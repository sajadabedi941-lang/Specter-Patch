#!/usr/bin/env python3
"""Fix Al-Haitham spawn CTD and missing Haitham/Najm visuals.

Baseline: PR #607 HAITHAM_NAJM DATA+ART.

Root cause: PR #607 uniquified W3D hierarchy/HLod/animation names
(IRQ_ABBAS_L -> IRQ_ALHTM_L, IRQ_SARAB7 -> IRQ_ALNAJT) and pointed
the objects at those copies. SAGE looks up Animation = File.Anim
against the internal names. The rewritten W3Ds do not match a proven
HLod/animation chain, so the TELs draw nothing. The Alabaas ICBM
draw/animation stack is also the spawn-CTD source when those internals
are invalid.

Fix:
  - Restore Iraq_AlHaitham Draw/Model/Animation to the working
    Iraq_Alhussaien Irq_Abbas_* chain.
  - Restore Iraq_AlNajm Draw/Model/Animation to the working
    Iraq_Sarab7 Irq_Sarab7 chain.
  - Rebuild projectile W3Ds as bit-identical parent copies with
    texture-only same-length retarget (black / red + Iraqi flag).
    Keep parent HLod names. Do not uniquify bones.

Gameplay (range/damage/accuracy/stealth/cost/time/roster) is unchanged.
"""
from __future__ import annotations

import hashlib
import io
import re
import struct
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_HAITHAM_NAJM/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_HAITHAM_NAJM/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_HAITHAM_VISUAL"

SHA_DATA_607 = "67cdb31bc458c46cb56acba9073714e020418cbae6a391ac46f2928fc998797d"
SIZE_DATA_607 = 366674916
SHA_ART_607 = "7fb8b996ec45222142e41a68b1a2eb825a6ae0bf19ebe2c351fd6ccb18507937"
SIZE_ART_607 = 1305667638

HAITHAM_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHaitham.ini"
NAJM_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNajm.ini"
ABBAS_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini"
SARAB_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AlNida.ini"
HCHAIN_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlHaitham_Chain.ini"
NPROJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlNajm_Projectile.ini"
WEP_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlHaithamNajm.ini"
UPG_KEY = r"Data\INI\Upgrade_MissileHalfPriceRearm.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"

HAITHAM_REPLACES = [
    ("Irq_AlHthm_L_AD", "Irq_Abbas_L_AD"),
    ("Irq_AlHthm_L_A", "Irq_Abbas_L_A"),
    ("Irq_AlHthm_L_D", "Irq_Abbas_L_D"),
    ("Irq_AlHthm_L_R", "Irq_Abbas_L_R"),
    ("Irq_AlHthm_L", "Irq_Abbas_L"),
]


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes) -> dict[str, bytes]:
    if data[:4] != b"BIGF":
        raise SystemExit("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


def parse_index(data: bytes):
    archive_size = struct.unpack(">I", data[4:8])[0]
    count = struct.unpack(">I", data[8:12])[0]
    header_size = struct.unpack(">I", data[12:16])[0]
    pos = 16
    files = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files.append((name, off, size))
    return archive_size, count, header_size, pos, files


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def decode(blob: bytes) -> str:
    return blob.decode("latin1").replace("\r\n", "\n")


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def object_body(text: str, name: str) -> str | None:
    found = [(m.group(1), m.start()) for m in re.finditer(r"^Object\s+(\S+)\s*$", text, re.M)]
    for i, (n, start) in enumerate(found):
        if n == name:
            end = found[i + 1][1] if i + 1 < len(found) else len(text)
            return text[start:end]
    return None


def field(body: str | None, key: str) -> str:
    if not body:
        return ""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", body, re.M)
    return m.group(1).strip() if m else ""


def last_block(kind: str, name: str, text: str):
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\n.*?^End", text))
    return matches[-1] if matches else None


def models(body: str) -> list[str]:
    return re.findall(r"^\s*Model\s+=\s+(\S+)", body, re.M)


def anims(body: str) -> list[str]:
    return re.findall(r"^\s*Animation\s+=\s+(\S+)", body, re.M)


def restore_haitham_tel(body: str) -> str:
    for old, new in HAITHAM_REPLACES:
        body = body.replace(old, new)
    if "Irq_AlHthm" in body:
        raise SystemExit("Haitham TEL still has Irq_AlHthm models")
    return body


def restore_najm_tel(body: str) -> str:
    # Only visual model/animation tokens. Do not touch Iraq_AlNajm or Irq_AlNajmM.
    body = body.replace("Irq_AlNajm.Irq_AlNajm", "Irq_Sarab7.Irq_Sarab7")
    body = re.sub(r"(^\s*Model\s+=\s+)Irq_AlNajm\s*$", r"\1Irq_Sarab7", body, flags=re.M)
    if re.search(r"^\s*Model\s+=\s+Irq_AlNajm\s*$", body, re.M):
        raise SystemExit("Najm TEL still uses Irq_AlNajm model")
    if "Iraq_AlNajm" not in body:
        raise SystemExit("Najm object id lost")
    return body


def texture_only_copy(src: bytes, old: bytes, new: bytes) -> bytes:
    if len(old) != len(new):
        raise SystemExit(f"texture length {old!r} -> {new!r}")
    if old not in src:
        raise SystemExit(f"parent W3D missing {old!r}")
    out = src.replace(old, new)
    if old in out:
        raise SystemExit(f"parent texture {old!r} still present")
    return out


def write_source(haitham: str, najm: str) -> None:
    src_h = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlHaitham.ini"
    src_n = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlNajm.ini"
    src_h.write_bytes(to_crlf(haitham))
    src_n.write_bytes(to_crlf(najm))


def validate(data: dict[str, bytes], art: dict[str, bytes], src_data: dict[str, bytes], src_art: dict[str, bytes]) -> list[str]:
    fails = []
    h = object_body(decode(data[HAITHAM_KEY]), "Iraq_AlHaitham")
    n = object_body(decode(data[NAJM_KEY]), "Iraq_AlNajm")
    p = object_body(decode(data[ABBAS_KEY]), "Iraq_Alhussaien")
    s = object_body(decode(data[SARAB_KEY]), "Iraq_Sarab7")
    if not all([h, n, p, s]):
        fails.append("object missing")
        return fails

    # Visual chain must match proven parents.
    h_models = [m for m in models(h) if m.startswith("Irq_")]
    p_models = [m for m in models(p) if m.startswith("Irq_")]
    if h_models != p_models:
        fails.append(f"Haitham models {h_models[:6]} != parent {p_models[:6]}")
    if anims(h) != anims(p):
        fails.append("Haitham animations != Alabaas parent")
    if "Irq_AlHthm" in h:
        fails.append("Haitham still references broken Irq_AlHthm W3D")

    n_models = [m for m in models(n) if m.startswith("Irq_")]
    s_models = [m for m in models(s) if m.startswith("Irq_")]
    if n_models != s_models:
        fails.append(f"Najm models {n_models} != parent {s_models}")
    if anims(n) != anims(s):
        fails.append("Najm animations != Sarab7 parent")

    # Gameplay frozen vs #607.
    if field(h, "BuildCost") != "30000" or field(h, "BuildTime") != "300":
        fails.append("Haitham cost/time changed")
    if field(n, "BuildCost") != "2500" or not field(n, "BuildTime").startswith("50"):
        fails.append("Najm cost/time changed")
    if field(p, "BuildCost") != "20000" or not field(p, "BuildTime").startswith("30"):
        fails.append("Alabaas production changed")
    if data[ABBAS_KEY] != src_data[ABBAS_KEY]:
        fails.append("AbbasLauncher.ini mutated")
    if data[SARAB_KEY] != src_data[SARAB_KEY]:
        fails.append("AlNida.ini mutated")
    if data[R11_KEY] != src_data[R11_KEY]:
        fails.append("9P117 mutated")
    if data[WEP_KEY] != src_data[WEP_KEY]:
        fails.append("weapon file mutated")
    if data[UPG_KEY] != src_data[UPG_KEY]:
        fails.append("upgrade file mutated")
    if data[CS_KEY] != src_data[CS_KEY]:
        fails.append("CommandSet mutated")
    if data[CB_KEY] != src_data[CB_KEY]:
        fails.append("CommandButton mutated")

    wep = decode(data[WEP_KEY])
    if field(last_block("Weapon", "Weapon_Iraq_AlHaitham_Hussiean", wep).group(0), "AttackRange") != "4300":
        fails.append("Haitham range")
    if field(last_block("Weapon", "Weapon_Iraq_AlNajm", wep).group(0), "AttackRange") != "1376":
        fails.append("Najm range")
    if field(last_block("Weapon", "Weapon_Iraq_AlHaitham_HussieanWH", wep).group(0), "PrimaryDamage") not in {"75000", "75000.0"}:
        fails.append("Haitham warhead")
    if field(last_block("Weapon", "Weapon_Iraq_AlNajm", wep).group(0), "PrimaryDamage") != "2000":
        fails.append("Najm damage")

    chain = decode(data[HCHAIN_KEY])
    nproj = decode(data[NPROJ_KEY])
    fly = object_body(chain, "Projectile_Iraq_AlHaitham_Hussiean")
    nfly = object_body(nproj, "Projectile_Iraq_AlNajm")
    if not fly or "Irq_AlHaithamM" not in fly:
        fails.append("Haitham projectile model")
    if not nfly or "Irq_AlNajmM" not in nfly:
        fails.append("Najm projectile model")
    if field(fly, "MaxHealth") != "6800.0":
        fails.append("Haitham stealth HP")
    if field(nfly, "MaxHealth") != "2000.0":
        fails.append("Najm stealth HP")

    # Parent TEL W3Ds must still be the live originals.
    for key in [
        r"Art\W3D\Irq_Abbas_L.W3D",
        r"Art\W3D\Irq_Abbas_L_A.W3D",
        r"Art\W3D\Irq_Abbas_L_D.W3D",
        r"Art\W3D\Irq_AbbasM.W3D",
        r"Art\W3D\Irq_Sarab7.W3D",
        r"Art\W3D\Irq_Raad2M.W3D",
    ]:
        if art.get(key) != src_art.get(key):
            fails.append(f"parent ART mutated {key}")

    hm = art.get(r"Art\W3D\Irq_AlHaithamM.W3D")
    nm = art.get(r"Art\W3D\Irq_AlNajmM.W3D")
    if not hm or b"IRQ_ABBASM" not in hm or b"IRQ_ALHTHM" in hm:
        fails.append("Haitham projectile W3D lost parent HLod")
    if not hm or b"AlHaithamMissile.tga" not in hm or b"Irq_AbbasMissile.tga" in hm:
        fails.append("Haitham projectile texture")
    if not nm or b"IRQ_RAAD2M" not in nm or b"IRQ_ALNAJM" in nm:
        fails.append("Najm projectile W3D lost parent HLod")
    if not nm or b"AlNajmSkin.tga" not in nm or b"AAM-GENTEX.dds" in nm:
        fails.append("Najm projectile texture")
    if r"Art\Textures\AlHaithamMissile.tga" not in art or r"Art\Textures\AlNajmSkin.tga" not in art:
        fails.append("dedicated textures missing")

    # Unused broken TEL copies may remain; they must not be referenced.
    packed_ini = decode(data[HAITHAM_KEY]) + decode(data[NAJM_KEY]) + decode(data[HCHAIN_KEY]) + decode(data[NPROJ_KEY])
    if "Irq_AlHthm" in packed_ini:
        fails.append("broken TEL name still referenced")
    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != SIZE_DATA_607 or sha256_path(SRC_DATA) != SHA_DATA_607:
        raise SystemExit("DATA baseline is not PR #607")
    if SRC_ART.stat().st_size != SIZE_ART_607 or sha256_path(SRC_ART) != SHA_ART_607:
        raise SystemExit("ART baseline is not PR #607")
    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    h_txt = decode(data[HAITHAM_KEY])
    n_txt = decode(data[NAJM_KEY])
    h_obj = object_body(h_txt, "Iraq_AlHaitham")
    n_obj = object_body(n_txt, "Iraq_AlNajm")
    if not h_obj or not n_obj:
        raise SystemExit("clone objects missing")
    h_new = restore_haitham_tel(h_obj)
    n_new = restore_najm_tel(n_obj)
    h_txt = h_txt.replace(h_obj, h_new, 1)
    n_txt = n_txt.replace(n_obj, n_new, 1)
    data[HAITHAM_KEY] = to_crlf(h_txt)
    data[NAJM_KEY] = to_crlf(n_txt)

    # Safe projectile skins: parent internals + dedicated color only.
    art[r"Art\W3D\Irq_AlHaithamM.W3D"] = texture_only_copy(
        art[r"Art\W3D\Irq_AbbasM.W3D"],
        b"Irq_AbbasMissile.tga",
        b"AlHaithamMissile.tga",
    )
    art[r"Art\W3D\Irq_AlNajmM.W3D"] = texture_only_copy(
        art[r"Art\W3D\Irq_Raad2M.W3D"],
        b"AAM-GENTEX.dds",
        b"AlNajmSkin.tga",
    )

    write_source(h_new, n_new)

    fails = validate(data, art, src_data, src_art)
    out_data = build_big(data)
    out_art = build_big(art)
    fails.extend([f"DATA {x}" for x in big_structure_ok(out_data)])
    fails.extend([f"ART {x}" for x in big_structure_ok(out_art)])
    packed = parse_big(out_data)
    packed_art = parse_big(out_art)
    fails.extend(validate(packed, packed_art, src_data, src_art))
    if fails:
        raise SystemExit("VALIDATION FAIL\n" + "\n".join(fails))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_SPEC_DATA_ONE.big").write_bytes(out_data)
    (OUT / "_SPEC_ART_ONE.big").write_bytes(out_art)
    data_sha = sha256_path(OUT / "_SPEC_DATA_ONE.big")
    art_sha = sha256_path(OUT / "_SPEC_ART_ONE.big")

    report = [
        "SPECTER Al-Haitham / Al-Najm visual + spawn-CTD fix",
        f"DATA {len(out_data)} {data_sha}",
        f"ART  {len(out_art)} {art_sha}",
        "",
        "BROKEN REFERENCE:",
        "  Iraq_AlHaitham Model/Animation Irq_AlHthm_L* -> rewritten W3D HLod IRQ_ALHTM_L",
        "  Iraq_AlNajm    Model/Animation Irq_AlNajm    -> rewritten W3D HLod IRQ_ALNAJT",
        "  Parent working HLods are IRQ_ABBAS_L / IRQ_SARAB7 with Animation File.File.",
        "  Naive W3D uniquify also left truncated texture fragments (ithamMissile.tga).",
        "",
        "WHY INVISIBLE: INI asked for Irq_AlHthm_L.Irq_AlHthm_L / Irq_AlNajm.Irq_AlNajm",
        "  but the cloned W3Ds no longer contained a proven HLod/animation pair.",
        "WHY HAITHAM CTD: Alabaas ICBM Draw+animation+ParticlesAttachedToAnimatedBones",
        "  on an invalid rewritten W3D. Sarab7 has a simpler draw stack so Najm only vanished.",
        "",
        "FIX: restore parent Irq_Abbas_* / Irq_Sarab7 visual chains on the TELs.",
        "  Projectile W3Ds rebuilt as parent copies + texture-only black/red skins.",
        "  Gameplay values unchanged.",
        "",
        "STATIC_VALIDATION=PASS",
        "RUNTIME_TEST=NOT RUN (visual/CTD claim requires in-game retest)",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=YES\n"
        f"DATA_SIZE={len(out_data)}\n"
        f"DATA_SHA256={data_sha}\n"
        f"ART_SIZE={len(out_art)}\n"
        f"ART_SHA256={art_sha}\n"
        "BASELINE=PR #607\n"
        "FIX=parent visual chains + texture-only projectile skins\n"
        "GAMEPLAY=UNCHANGED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Al-Haitham / Al-Najm visual + spawn-CTD fix\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder.\n"
        "TELs now use the proven Alabaas / Sarab7 W3D chains.\n"
        "In-flight skins stay dedicated black / red with Iraqi markings.\n"
        "Gameplay stats from PR #607 are unchanged.\n",
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Al-Haitham / Al-Najm visual and spawn-CTD fix\n"
        "\n"
        "- Restore Al-Haitham TEL art to working `Irq_Abbas_*` parent models.\n"
        "- Restore Al-Najm TEL art to working `Irq_Sarab7` parent models.\n"
        "- Rebuild projectile W3Ds as texture-only black/red copies.\n"
        "- PR #607 gameplay values unchanged.\n",
        encoding="utf-8",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "DATA/ART/ZIP links are filled after the GitHub Release is published.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_HAITHAM_VISUAL.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
        zf.write(OUT / "RELEASE_NOTES.md", "RELEASE_NOTES.md")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size} sha={sha256_path(zip_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
