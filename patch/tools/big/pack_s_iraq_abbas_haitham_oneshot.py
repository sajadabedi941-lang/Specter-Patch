#!/usr/bin/env python3
"""Remove paid rearm from Iraq Al-Abbas and Al-Haitham; one-shot factory units.

Baseline: PR #610 / s-iraq-kl-najm-restore DATA+ART.

Al-Abbas (Iraq_Alhussaien):
  Paid path is Upgrade_Rearm_Iraq_Alhussaien + UnarmedRearmSet button +
  ObjectCreationUpgrade + OCL_Rearm + RearmStrip.
  Existing FireOCL OCL_HussienMissileDisarm already consumes the payload
  after the first shot. Remove only the restore/money path.
  BuildTime 30 -> 300 (5 min). BuildCost 20000 unchanged.
  Do not edit shared HussieanMissileWeapon / AlAbidMissileWeapon.

Al-Haitham (Iraq_AlHaitham):
  Paid rearm IDs already gone in #610. Launch weapons still ClipReloadTime
  4000 (free recharge). Set AutoReloadsClip = No so each warhead fires once.
  BuildTime already 300. No riders, no FireOCL, no new recharge system.

ART is copied byte-identical from #610. No W3D/texture/model edits.
Sarab7, 9P117, Al-Najm, other missiles, other countries are not edited.
"""
from __future__ import annotations

import hashlib
import io
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_KL_NAJM_RESTORE/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_KL_NAJM_RESTORE/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ABBAS_HAITHAM_ONESHOT"

SHA_DATA_610 = "9f8311b469fe1fc3a807dccf302c27cb525b4da3cfb3608fcb80556399e7d5ee"
SIZE_DATA_610 = 366671017
SHA_ART_610 = "2bc140fd19ad138ed6fd34e61d8cea32976af287e2183d5725ca060112236309"
SIZE_ART_610 = 1305667638

ABBAS_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini"
HAITHAM_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHaitham.ini"
NAJM_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNajm.ini"
SARAB_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AlNida.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
HCHAIN_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlHaitham_Chain.ini"
NPROJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlNajm_Projectile.ini"
WEP_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlHaithamNajm.ini"
UPG_KEY = r"Data\INI\Upgrade_MissileHalfPriceRearm.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
OCL_KEY = r"Data\INI\ObjectCreationList.ini"
REARM_KEY = r"Data\INI\Object\Specter\Iraq Army\MissileHalfPriceRearm.ini"
WEAPON_INI = r"Data\INI\Weapon.ini"


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
    blobs = []
    offset = header_size
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", 0)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    index = []
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out[4:8] = struct.pack(">I", offset)
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


def remove_block(text: str, kind: str, name: str) -> str:
    m = last_block(kind, name, text)
    if not m:
        return text
    start = m.start()
    end = m.end()
    if end < len(text) and text[end] == "\n":
        end += 1
    return text[:start] + text[end:]


def replace_last_block(kind: str, name: str, text: str, new: str) -> str:
    m = last_block(kind, name, text)
    if not m:
        raise SystemExit(f"missing {kind} {name}")
    return text[: m.start()] + new.rstrip() + "\n" + text[m.end() :]


def strip_cs_line(block: str, needle: str) -> str:
    lines = [ln for ln in block.splitlines() if needle not in ln]
    return "\n".join(lines) + ("\n" if block.endswith("\n") else "")


def fix_abbas(body: str) -> str:
    body = re.sub(
        r"  Behavior = ObjectCreationUpgrade ModuleTag_Rearm\n.*?  End\n",
        "",
        body,
        count=1,
        flags=re.S,
    )
    if "ObjectCreationUpgrade" in body or "Upgrade_Rearm_Iraq_Alhussaien" in body or "OCL_Rearm_Iraq_Alhussaien" in body:
        raise SystemExit("Alabaas still has paid rearm modules")
    if "RiderChangeContain" not in body or "InitialPayload" not in body:
        raise SystemExit("Alabaas lost spawn-safe rider/payload")
    body = re.sub(r"^(\s*BuildTime\s+=\s+)30(?:\.0)?\s*$", r"\g<1>300.0", body, count=1, flags=re.M)
    if field(body, "BuildCost") != "20000":
        raise SystemExit("Alabaas BuildCost changed")
    if not field(body, "BuildTime").startswith("300"):
        raise SystemExit(f"Alabaas BuildTime {field(body, 'BuildTime')}")
    return body


def fix_haitham_weapons(text: str) -> str:
    for name in ("Weapon_Iraq_AlHaitham_AlAbid", "Weapon_Iraq_AlHaitham_Hussiean"):
        m = last_block("Weapon", name, text)
        if not m:
            raise SystemExit(f"missing {name}")
        block = m.group(0)
        if "AutoReloadsClip" in block:
            block = re.sub(r"^(\s*AutoReloadsClip\s+=\s+).+$", r"\1No", block, flags=re.M)
        else:
            block = re.sub(r"^(\s*ClipSize\s+=\s+1\s*)$", r"\1\n  AutoReloadsClip         = No", block, count=1, flags=re.M)
        text = text[: m.start()] + block + text[m.end() :]
    if "OCL_HussienMissileDisarm" in text:
        raise SystemExit("do not put FireOCL on unique Haitham weapons")
    return text


def strip_abbas_rearm(data: dict[str, bytes]) -> None:
    cs = decode(data[CS_KEY])
    for name in ("Iraq_Alhussaien_UnarmedRearmSet", "Iraq_AlhussaienCommandSet", "Iraq_AlhussaienArmedCommandSet"):
        m = last_block("CommandSet", name, cs)
        if not m:
            if name == "Iraq_Alhussaien_UnarmedRearmSet":
                raise SystemExit("missing UnarmedRearmSet")
            continue
        cleaned = strip_cs_line(m.group(0), "Command_Rearm_Iraq_Alhussaien")
        cleaned = strip_cs_line(cleaned, "Command_BuyAlhussaienMissile")
        cs = cs[: m.start()] + cleaned + cs[m.end() :]
    if "Command_Rearm_Iraq_Alhussaien" in cs:
        raise SystemExit("CommandSet still has Alabaas rearm")
    data[CS_KEY] = to_crlf(cs)

    cb = decode(data[CB_KEY])
    cb = remove_block(cb, "CommandButton", "Command_Rearm_Iraq_Alhussaien")
    if "Command_Rearm_Iraq_Alhussaien" in cb:
        raise SystemExit("CommandButton still has Alabaas rearm")
    data[CB_KEY] = to_crlf(cb)

    upg = decode(data[UPG_KEY])
    upg = remove_block(upg, "Upgrade", "Upgrade_Rearm_Iraq_Alhussaien")
    if "Upgrade_Rearm_Iraq_Alhussaien" in upg:
        raise SystemExit("upgrade file still has Alabaas rearm")
    if "Upgrade_Rearm_Iraq_AlHaitham" in upg:
        raise SystemExit("Haitham rearm upgrade reappeared")
    data[UPG_KEY] = to_crlf(upg)

    ocl = decode(data[OCL_KEY])
    ocl = remove_block(ocl, "ObjectCreationList", "OCL_Rearm_Iraq_Alhussaien")
    if "OCL_Rearm_Iraq_Alhussaien" in ocl:
        raise SystemExit("OCL still has Alabaas rearm")
    data[OCL_KEY] = to_crlf(ocl)

    rearm = decode(data[REARM_KEY])
    rearm = remove_block(rearm, "Object", "RearmStrip_Iraq_Alhussaien")
    if "RearmStrip_Iraq_Alhussaien" in rearm:
        raise SystemExit("Alabaas rearm strip still present")
    data[REARM_KEY] = to_crlf(rearm)


def write_sources(data: dict[str, bytes]) -> None:
    mapping = {
        WEP_KEY: ROOT / "patch/Data/INI/Weapon/Weapon_Iraq_AlHaithamNajm.ini",
        UPG_KEY: ROOT / "patch/Data/INI/Upgrade_MissileHalfPriceRearm.ini",
        REARM_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/MissileHalfPriceRearm.ini",
        HAITHAM_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlHaitham.ini",
    }
    for key, path in mapping.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data[key])


def validate(data: dict[str, bytes], src_data: dict[str, bytes]) -> list[str]:
    fails = []
    p = object_body(decode(data[ABBAS_KEY]), "Iraq_Alhussaien")
    h = object_body(decode(data[HAITHAM_KEY]), "Iraq_AlHaitham")
    n = object_body(decode(data[NAJM_KEY]), "Iraq_AlNajm")
    s = object_body(decode(data[SARAB_KEY]), "Iraq_Sarab7")
    if not all([p, h, n, s]):
        return ["object missing"]

    if data[SARAB_KEY] != src_data[SARAB_KEY]:
        fails.append("AlNida.ini / Sarab7 mutated")
    if data[R11_KEY] != src_data[R11_KEY]:
        fails.append("9P117 mutated")
    if data[NAJM_KEY] != src_data[NAJM_KEY]:
        fails.append("Al-Najm mutated")
    if data[NPROJ_KEY] != src_data[NPROJ_KEY]:
        fails.append("Najm projectile mutated")
    if data[HCHAIN_KEY] != src_data[HCHAIN_KEY]:
        fails.append("Haitham chain mutated")
    if data[HAITHAM_KEY] != src_data[HAITHAM_KEY]:
        fails.append("Haitham object mutated")

    if field(p, "BuildCost") != "20000":
        fails.append("Alabaas cost")
    if not field(p, "BuildTime").startswith("300"):
        fails.append("Alabaas build time")
    if field(h, "BuildCost") != "30000" or field(h, "BuildTime") != "300":
        fails.append("Haitham cost/time")
    if field(n, "BuildCost") != "2500":
        fails.append("Najm cost")

    if "ObjectCreationUpgrade" in p or "Upgrade_Rearm_Iraq_Alhussaien" in p:
        fails.append("Alabaas still has paid restore")
    if "RiderChangeContain" not in p or "InitialPayload" not in p:
        fails.append("Alabaas lost rider/payload")

    wep = decode(data[WEP_KEY])
    for name in ("Weapon_Iraq_AlHaitham_AlAbid", "Weapon_Iraq_AlHaitham_Hussiean"):
        blk = last_block("Weapon", name, wep).group(0)
        if field(blk, "AttackRange") != "4300":
            fails.append(f"{name} range")
        if "AutoReloadsClip         = No" not in blk and "AutoReloadsClip = No" not in blk:
            fails.append(f"{name} still auto-reloads")
        if field(blk, "ClipSize") != "1":
            fails.append(f"{name} clip")
    if field(last_block("Weapon", "Weapon_Iraq_AlHaitham_HussieanWH", wep).group(0), "PrimaryDamage") not in {"75000", "75000.0"}:
        fails.append("Haitham warhead")
    if field(last_block("Weapon", "Weapon_Iraq_AlNajm", wep).group(0), "AttackRange") != "1376":
        fails.append("Najm range")

    shared = decode(data[WEAPON_INI])
    if last_block("Weapon", "HussieanMissileWeapon", shared).group(0) != last_block(
        "Weapon", "HussieanMissileWeapon", decode(src_data[WEAPON_INI])
    ).group(0):
        fails.append("shared HussieanMissileWeapon mutated")
    if last_block("Weapon", "AlAbidMissileWeapon", shared).group(0) != last_block(
        "Weapon", "AlAbidMissileWeapon", decode(src_data[WEAPON_INI])
    ).group(0):
        fails.append("shared AlAbidMissileWeapon mutated")

    cb = decode(data[CB_KEY])
    if "Object        = Iraq_Alhussaien" not in last_block("CommandButton", "CB_MISSILE_K", cb).group(0):
        fails.append("slot K")
    if "Object        = Iraq_AlHaitham" not in last_block("CommandButton", "CB_MISSILE_L", cb).group(0):
        fails.append("slot L")
    if "Object        = Iraq_AlNajm" not in last_block("CommandButton", "CB_MISSILE_F", cb).group(0):
        fails.append("slot F")
    if "Object        = Iraq_Sarab7" not in last_block("CommandButton", "CB_MISSILE_E", cb).group(0):
        fails.append("slot E")
    if last_block("CommandButton", "Command_IraqAlAbbasICBMFire", cb) is None:
        fails.append("Alabaas fire button")
    if last_block("CommandButton", "Command_IraqAlHaithamICBMFire", cb) is None:
        fails.append("Haitham fire button")
    if last_block("CommandButton", "Command_Rearm_Iraq_Alhussaien", cb):
        fails.append("Alabaas rearm button remains")
    if last_block("CommandButton", "Command_Rearm_Iraq_AlHaitham", cb):
        fails.append("Haitham rearm button remains")

    upg = decode(data[UPG_KEY])
    if last_block("Upgrade", "Upgrade_Rearm_Iraq_Alhussaien", upg):
        fails.append("Upgrade_Rearm_Iraq_Alhussaien remains")
    if last_block("Upgrade", "Upgrade_Rearm_Iraq_AlHaitham", upg):
        fails.append("Upgrade_Rearm_Iraq_AlHaitham remains")

    if last_block("ObjectCreationList", "OCL_Rearm_Iraq_Alhussaien", decode(data[OCL_KEY])):
        fails.append("OCL_Rearm_Iraq_Alhussaien remains")
    if last_block("Object", "RearmStrip_Iraq_Alhussaien", decode(data[REARM_KEY])):
        fails.append("RearmStrip_Iraq_Alhussaien remains")

    cs = decode(data[CS_KEY])
    if "Command_Rearm_Iraq_Alhussaien" in cs or "Command_Rearm_Iraq_AlHaitham" in cs:
        fails.append("rearm still in a CommandSet")
    armed = last_block("CommandSet", "Iraq_AlhussaienArmedCommandSet", cs)
    if not armed or "Command_IraqAlAbbasICBMFire" not in armed.group(0):
        fails.append("Alabaas armed fire bind")
    harmed = last_block("CommandSet", "Iraq_AlHaithamArmedCommandSet", cs)
    if not harmed or "Command_IraqAlHaithamICBMFire" not in harmed.group(0):
        fails.append("Haitham armed fire bind")
    unarmed = last_block("CommandSet", "Iraq_Alhussaien_UnarmedRearmSet", cs)
    if not unarmed:
        fails.append("UnarmedRearmSet missing")
    elif "Command_Rearm" in unarmed.group(0) or "Command_BuyAlhussaien" in unarmed.group(0):
        fails.append("unarmed set still has paid restore")

    factory = last_block("CommandSet", "Iraq_AlFahdMissileFactoryCommandSet", cs)
    if not factory or "12 = CB_MISSILE_L" not in factory.group(0) or "11 = CB_MISSILE_K" not in factory.group(0):
        fails.append("factory slots")
    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != SIZE_DATA_610 or sha256_path(SRC_DATA) != SHA_DATA_610:
        raise SystemExit("DATA baseline is not PR #610")
    if SRC_ART.stat().st_size != SIZE_ART_610 or sha256_path(SRC_ART) != SHA_ART_610:
        raise SystemExit("ART baseline is not PR #610")
    src_data = parse_big(SRC_DATA.read_bytes())
    data = dict(src_data)

    a_txt = decode(data[ABBAS_KEY])
    a_obj = object_body(a_txt, "Iraq_Alhussaien")
    data[ABBAS_KEY] = to_crlf(a_txt.replace(a_obj, fix_abbas(a_obj), 1))
    data[WEP_KEY] = to_crlf(fix_haitham_weapons(decode(data[WEP_KEY])))
    strip_abbas_rearm(data)
    write_sources(data)

    fails = validate(data, src_data)
    out_data = build_big(data)
    fails.extend([f"DATA {x}" for x in big_structure_ok(out_data)])
    packed = parse_big(out_data)
    fails.extend(validate(packed, src_data))
    if fails:
        raise SystemExit("VALIDATION FAIL\n" + "\n".join(fails))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_SPEC_DATA_ONE.big").write_bytes(out_data)
    # ART is an unchanged #610 copy so visuals cannot drift.
    art_bytes = SRC_ART.read_bytes()
    (OUT / "_SPEC_ART_ONE.big").write_bytes(art_bytes)
    data_sha = sha256_path(OUT / "_SPEC_DATA_ONE.big")
    art_sha = sha256_path(OUT / "_SPEC_ART_ONE.big")
    if art_sha != SHA_ART_610:
        raise SystemExit("ART hash drifted from #610")

    ext = OUT / "LAST_WINS_EXTRACT/DATA"
    ext.mkdir(parents=True, exist_ok=True)
    (ext / "AbbasLauncher_Iraq_Alhussaien.ini").write_text(object_body(decode(packed[ABBAS_KEY]), "Iraq_Alhussaien"), encoding="latin1")
    for key in [HAITHAM_KEY, WEP_KEY, UPG_KEY]:
        (ext / Path(key.replace("\\", "/")).name).write_bytes(packed[key])
    cs = decode(packed[CS_KEY])
    for name in (
        "Iraq_AlhussaienArmedCommandSet",
        "Iraq_AlhussaienCommandSet",
        "Iraq_Alhussaien_UnarmedRearmSet",
        "Iraq_AlHaithamArmedCommandSet",
    ):
        m = last_block("CommandSet", name, cs)
        if m:
            (ext / f"{name}.ini").write_text(m.group(0) + "\n", encoding="latin1")

    report = [
        "SPECTER Al-Abbas / Al-Haitham one-shot (no paid rearm)",
        f"DATA {len(out_data)} {data_sha}",
        f"ART  {len(art_bytes)} {art_sha} (identical to PR #610)",
        "",
        "AL-ABBAS (Iraq_Alhussaien, slot K):",
        "  Removed Upgrade/Button/OCL/Strip/ObjectCreationUpgrade.",
        "  Existing FireOCL disarm remains; first shot consumes the payload.",
        "  Unarmed set no longer has a paid restore button.",
        "  BuildTime 300.0 (5 min). BuildCost 20000 unchanged.",
        "  Shared Hussiean/AlAbid weapons not edited.",
        "",
        "AL-HAITHAM (Iraq_AlHaitham, slot L):",
        "  Paid rearm IDs were already absent. Launch weapons now AutoReloadsClip = No.",
        "  BuildTime 300 / BuildCost 30000 unchanged. No riders, no FireOCL.",
        "",
        "UNCHANGED: Sarab7, 9P117, Al-Najm, factory roster, fire buttons, ART.",
        "",
        "STATIC_VALIDATION=PASS",
        "RUNTIME_TEST=NOT RUN",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=NO\n"
        f"DATA_SIZE={len(out_data)}\n"
        f"DATA_SHA256={data_sha}\n"
        f"ART_SIZE={len(art_bytes)}\n"
        f"ART_SHA256={art_sha}\n"
        "BASELINE=PR #610\n"
        "ALABAAS_REARM=REMOVED\n"
        "HAITHAM_REARM=NONE\n"
        "ALABAAS_BUILDTIME=300\n"
        "HAITHAM_BUILDTIME=300\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Al-Abbas and Al-Haitham are one-shot factory missiles.\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder.\n"
        "ART is unchanged from s-iraq-kl-najm-restore.\n"
        "Build either missile (5 minutes), fire once, then build a new one.\n"
        "No paid rearm. STATIC ONLY.\n",
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Al-Abbas / Al-Haitham one-shot (remove paid rearm)\n"
        "\n"
        "- Remove Upgrade_Rearm_Iraq_Alhussaien and every Al-Abbas paid restore ID.\n"
        "- Al-Haitham launch weapons no longer auto-reload.\n"
        "- Both use the 5-minute factory build timer. Production costs unchanged.\n"
        "- ART is the unchanged PR #610 file. No visual edits.\n",
        encoding="utf-8",
    )
    (OUT / "CONFLICTS.txt").write_text(
        "Al-Abbas empty TEL can remain after FireOCL consumes the payload.\n"
        "Al-Haitham has two warhead buttons; each clip is one-shot and does not reload.\n"
        "No paid button on either. STATIC ONLY.\n",
        encoding="utf-8",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "DATA/ART/ZIP links are filled after the GitHub Release is published.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_ABBAS_HAITHAM_ONESHOT.zip"
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
