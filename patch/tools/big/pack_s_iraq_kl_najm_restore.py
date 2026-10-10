#!/usr/bin/env python3
"""Restore Sarab7, make Najm a visible parent-identical clone, isolate K/L, strip paid rearm.

Baseline: PR #608 DATA+ART (before the failed #609 HLod-collision attempt).

In-game #609 failures and packed last-wins causes:

1. Sarab7 recolored
   Irq_AlNajm.W3D kept parent HLod IRQ_SARAB7 but swapped AAM-GENTEX -> AlNajmSkin.
   SAGE registers HLods by internal name, so the clone overrode Irq_Sarab7.W3D.
   Parent W3D and AAM-GENTEX.dds were never byte-mutated.

2. Najm invisible / not firing
   Model = Irq_AlNajm + Animation = Irq_AlNajm.Irq_Sarab7 is not a proven pair.
   Failed unpack/deploy leaves the unit with no model and no PRIMARY fire.

3. Slots K and L both CTD
   K = Iraq_Alhussaien (Alabaas). L = Iraq_AlHaitham.
   Alabaas INI/CommandSet/OCL were not text-changed.
   Irq_AlHaithamM.W3D still carries parent HLod IRQ_ABBASM + AlHaithamMissile.tga.
   Same collision class as Sarab7: both ICBM objects share IRQ_ABBASM.

Fix:
  - Neutralize unique W3Ds to bit-identical parent copies (same HLod AND textures).
  - Najm TEL/projectile use proven Irq_Sarab7 / Irq_Raad2M names and anims.
  - Red deferred: unique same-HLod recolor contaminated parents; unique HLod broke draw.
  - Haitham: no paid rearm IDs; no rider/FireOCL contain; parent Irq_Abbas* visuals.
  - Do not rewrite Alabaas / Sarab7 / 9P117 objects.
  - #607 gameplay numbers kept. Alabaas rearm stays $15000.
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
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_HAITHAM_VISUAL/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_HAITHAM_VISUAL/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_KL_NAJM_RESTORE"

SHA_DATA_608 = "66109b457ed8e3fcdb7ec3430cbc97498f485095f3b509f077fcb021266eeac5"
SIZE_DATA_608 = 366674844
SHA_ART_608 = "fd17c94bcfc6f89bf2d6d567064b965cad1ecb6f1ba73cadbb90dae94523d7d6"
SIZE_ART_608 = 1305667638

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
OCL_KEY = r"Data\INI\ObjectCreationList.ini"
REARM_KEY = r"Data\INI\Object\Specter\Iraq Army\MissileHalfPriceRearm.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"


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


def remove_block(text: str, kind: str, name: str) -> str:
    m = last_block(kind, name, text)
    if not m:
        return text
    start = m.start()
    end = m.end()
    if end < len(text) and text[end] == "\n":
        end += 1
    return text[:start] + text[end:]


def fix_najm_tel(body: str) -> str:
    # Proven parent pair only.
    body = body.replace("Irq_AlNajm.Irq_AlNajm", "Irq_Sarab7.Irq_Sarab7")
    body = body.replace("Irq_AlNajm.Irq_Sarab7", "Irq_Sarab7.Irq_Sarab7")
    body = re.sub(r"(^\s*Model\s+=\s+)Irq_AlNajm\s*$", r"\1Irq_Sarab7", body, flags=re.M)
    if re.search(r"Irq_AlNajm", body):
        raise SystemExit("Najm TEL still references Irq_AlNajm")
    if anims(body) and any(a != "Irq_Sarab7.Irq_Sarab7" for a in anims(body)):
        raise SystemExit(f"Najm anims {anims(body)}")
    return body


def fix_najm_proj(text: str) -> str:
    text = text.replace("Model = Irq_AlNajmM", "Model = Irq_Raad2M")
    if "Irq_AlNajmM" in text:
        raise SystemExit("Najm projectile still unique W3D")
    return text


def fix_haitham_object(body: str) -> str:
    body = re.sub(
        r"  WeaponSet\n    Conditions = WEAPON_RIDER1\n.*?  End\n\s*  WeaponSet\n    Conditions = WEAPON_RIDER2\n.*?  End\n",
        "  WeaponSet\n"
        "    Conditions = None\n"
        "    Weapon            = PRIMARY    Weapon_Iraq_AlHaitham_AlAbid\n"
        "    AutoChooseSources = PRIMARY    NONE\n"
        "    Weapon            = SECONDARY  Weapon_Iraq_AlHaitham_Hussiean\n"
        "    AutoChooseSources = SECONDARY  NONE\n"
        "    Weapon            = TERTIARY   RandomDummyDeployWeapon\n"
        "    AutoChooseSources = TERTIARY   NONE\n"
        "  End\n",
        body,
        count=1,
        flags=re.S,
    )
    if re.search(r"Conditions = WEAPON_RIDER", body):
        raise SystemExit("Haitham still has rider weapon sets")
    body = re.sub(r"  Behavior = RiderChangeContain ModuleTag_WarheadRider\n.*?  End\n", "", body, count=1, flags=re.S)
    body = re.sub(r"  Behavior = ObjectCreationUpgrade ModuleTag_Rearm\n.*?  End\n", "", body, count=1, flags=re.S)
    if "RiderChangeContain" in body or "InitialPayload" in body or "ObjectCreationUpgrade" in body:
        raise SystemExit("Haitham still has rider/rearm contain")
    body = body.replace(
        "KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE HUGE_VEHICLE SCORE SALVAGER GARRISONABLE_UNTIL_DESTROYED",
        "KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE HUGE_VEHICLE SCORE SALVAGER",
    )
    body = body.replace("HideSubObject     = MISSILE01", "ShowSubObject     = MISSILE01")
    if "Upgrade_Rearm_Iraq_AlHaitham" in body or "OCL_Rearm_Iraq_AlHaitham" in body:
        raise SystemExit("Haitham object still refs paid rearm")
    if field(body, "BuildCost") != "30000" or field(body, "BuildTime") != "300":
        raise SystemExit("Haitham cost/time changed")
    return body


def fix_haitham_chain(text: str) -> str:
    text = text.replace("Model = Irq_AlHaithamM", "Model = Irq_AbbasM")
    if "Irq_AlHaithamM" in text:
        raise SystemExit("Haitham chain still uses Irq_AlHaithamM")
    return text


def fix_haitham_weapons(text: str) -> str:
    text = re.sub(r"^  FireOCL\s+=\s+OCL_HussienMissileDisarm\r?\n", "", text, flags=re.M)
    if "OCL_HussienMissileDisarm" in text:
        raise SystemExit("Haitham weapons still FireOCL disarm")
    return text


def strip_haitham_rearm(data: dict[str, bytes]) -> None:
    cs = decode(data[CS_KEY])
    cs = remove_block(cs, "CommandSet", "Iraq_AlHaitham_UnarmedRearmSet")
    cs = remove_block(cs, "CommandSet", "Iraq_AlHaithamCommandSet")
    armed = last_block("CommandSet", "Iraq_AlHaithamArmedCommandSet", cs)
    if armed and "Command_Rearm_Iraq_AlHaitham" in armed.group(0):
        cleaned = "\n".join(
            ln for ln in armed.group(0).splitlines() if "Command_Rearm_Iraq_AlHaitham" not in ln
        )
        cs = cs[: armed.start()] + cleaned + "\n" + cs[armed.end() :]
    if "Command_Rearm_Iraq_AlHaitham" in cs:
        raise SystemExit("CommandSet still has Haitham rearm")
    data[CS_KEY] = to_crlf(cs)

    cb = decode(data[CB_KEY])
    cb = remove_block(cb, "CommandButton", "Command_Rearm_Iraq_AlHaitham")
    if "Command_Rearm_Iraq_AlHaitham" in cb:
        raise SystemExit("CommandButton still has Haitham rearm")
    data[CB_KEY] = to_crlf(cb)

    upg = decode(data[UPG_KEY])
    upg = remove_block(upg, "Upgrade", "Upgrade_Rearm_Iraq_AlHaitham")
    if "Upgrade_Rearm_Iraq_AlHaitham" in upg:
        raise SystemExit("upgrade file still has Haitham rearm")
    data[UPG_KEY] = to_crlf(upg)

    ocl = decode(data[OCL_KEY])
    ocl = remove_block(ocl, "ObjectCreationList", "OCL_Rearm_Iraq_AlHaitham")
    if "OCL_Rearm_Iraq_AlHaitham" in ocl:
        raise SystemExit("OCL still has Haitham rearm")
    data[OCL_KEY] = to_crlf(ocl)

    rearm = decode(data[REARM_KEY])
    rearm = remove_block(rearm, "Object", "RearmStrip_Iraq_AlHaitham")
    if "RearmStrip_Iraq_AlHaitham" in rearm:
        raise SystemExit("rearm strip still present")
    data[REARM_KEY] = to_crlf(rearm)


def write_sources(data: dict[str, bytes]) -> None:
    mapping = {
        HAITHAM_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlHaitham.ini",
        NAJM_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlNajm.ini",
        HCHAIN_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Iraq_AlHaitham_Chain.ini",
        NPROJ_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Iraq_AlNajm_Projectile.ini",
        WEP_KEY: ROOT / "patch/Data/INI/Weapon/Weapon_Iraq_AlHaithamNajm.ini",
    }
    for key, path in mapping.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data[key])


def validate(data: dict[str, bytes], art: dict[str, bytes], src_data: dict[str, bytes], src_art: dict[str, bytes]) -> list[str]:
    fails = []
    h = object_body(decode(data[HAITHAM_KEY]), "Iraq_AlHaitham")
    n = object_body(decode(data[NAJM_KEY]), "Iraq_AlNajm")
    p = object_body(decode(data[ABBAS_KEY]), "Iraq_Alhussaien")
    s = object_body(decode(data[SARAB_KEY]), "Iraq_Sarab7")
    if not all([h, n, p, s]):
        return ["object missing"]

    if data[ABBAS_KEY] != src_data[ABBAS_KEY]:
        fails.append("AbbasLauncher.ini mutated")
    if data[SARAB_KEY] != src_data[SARAB_KEY]:
        fails.append("AlNida.ini mutated")
    if data[R11_KEY] != src_data[R11_KEY]:
        fails.append("9P117 mutated")

    if field(h, "BuildCost") != "30000" or field(h, "BuildTime") != "300":
        fails.append("Haitham cost/time")
    if field(n, "BuildCost") != "2500" or not field(n, "BuildTime").startswith("50"):
        fails.append("Najm cost/time")
    if field(p, "BuildCost") != "20000" or not field(p, "BuildTime").startswith("30"):
        fails.append("Alabaas production")

    n_models = [m for m in models(n) if m.startswith("Irq_")]
    s_models = [m for m in models(s) if m.startswith("Irq_")]
    if n_models != s_models:
        fails.append(f"Najm models {n_models} != Sarab7 {s_models}")
    if anims(n) != anims(s):
        fails.append("Najm animations != Sarab7")
    if "Irq_AlNajm" in n or "Irq_AlNajm" in decode(data[NPROJ_KEY]):
        fails.append("Najm still refs unique TEL/proj W3D name")

    wep = decode(data[WEP_KEY])
    if field(last_block("Weapon", "Weapon_Iraq_AlHaitham_Hussiean", wep).group(0), "AttackRange") != "4300":
        fails.append("Haitham range")
    if field(last_block("Weapon", "Weapon_Iraq_AlNajm", wep).group(0), "AttackRange") != "1376":
        fails.append("Najm range")
    if field(last_block("Weapon", "Weapon_Iraq_AlHaitham_HussieanWH", wep).group(0), "PrimaryDamage") not in {"75000", "75000.0"}:
        fails.append("Haitham warhead")
    if field(last_block("Weapon", "Weapon_Iraq_AlNajm", wep).group(0), "PrimaryDamage") != "2000":
        fails.append("Najm damage")
    if "ClipSize                    = 2" not in last_block("Weapon", "Weapon_Iraq_AlNajm", wep).group(0):
        fails.append("Najm ClipSize")
    if "OCL_HussienMissileDisarm" in wep:
        fails.append("Haitham FireOCL still present")

    if "RiderChangeContain" in h or "InitialPayload" in h:
        fails.append("Haitham still has riders")
    if re.search(r"Conditions = WEAPON_RIDER", h):
        fails.append("Haitham still rider-gated")
    if "Irq_Abbas_L" not in h:
        fails.append("Haitham lost parent TEL")

    chain = decode(data[HCHAIN_KEY])
    nproj = decode(data[NPROJ_KEY])
    fly = object_body(chain, "Projectile_Iraq_AlHaitham_Hussiean")
    nfly = object_body(nproj, "Projectile_Iraq_AlNajm")
    if not fly or "Irq_AbbasM" not in fly:
        fails.append("Haitham projectile not Irq_AbbasM")
    if not nfly or "Irq_Raad2M" not in nfly:
        fails.append("Najm projectile not parent Irq_Raad2M")
    if field(fly, "MaxHealth") != "6800.0":
        fails.append("Haitham stealth HP")
    if field(nfly, "MaxHealth") != "2000.0":
        fails.append("Najm stealth HP")

    cb = decode(data[CB_KEY])
    if "Object        = Iraq_Alhussaien" not in last_block("CommandButton", "CB_MISSILE_K", cb).group(0):
        fails.append("slot K not Alabaas")
    if "Object        = Iraq_AlHaitham" not in last_block("CommandButton", "CB_MISSILE_L", cb).group(0):
        fails.append("slot L not Haitham")
    if "Object        = Iraq_AlNajm" not in last_block("CommandButton", "CB_MISSILE_F", cb).group(0):
        fails.append("slot F not Najm")
    if "Object        = Iraq_Sarab7" not in last_block("CommandButton", "CB_MISSILE_E", cb).group(0):
        fails.append("slot E not Sarab7")
    if last_block("CommandButton", "Command_Rearm_Iraq_AlHaitham", cb):
        fails.append("Haitham rearm button remains")
    if last_block("Upgrade", "Upgrade_Rearm_Iraq_AlHaitham", decode(data[UPG_KEY])):
        fails.append("Haitham rearm upgrade remains")
    abup = last_block("Upgrade", "Upgrade_Rearm_Iraq_Alhussaien", decode(data[UPG_KEY]))
    if not abup or field(abup.group(0), "BuildCost") != "15000":
        fails.append("Alabaas rearm price")
    if last_block("ObjectCreationList", "OCL_Rearm_Iraq_AlHaitham", decode(data[OCL_KEY])):
        fails.append("Haitham rearm OCL remains")
    if last_block("Object", "RearmStrip_Iraq_AlHaitham", decode(data[REARM_KEY])):
        fails.append("Haitham rearm strip remains")
    if "Command_Rearm_Iraq_AlHaitham" in decode(data[CS_KEY]):
        fails.append("Haitham rearm still in a CommandSet")

    # Parent ART must be the live #608 originals.
    for key in [
        r"Art\W3D\Irq_Sarab7.W3D",
        r"Art\W3D\Irq_Raad2M.W3D",
        r"Art\W3D\Irq_Abbas_L.W3D",
        r"Art\W3D\Irq_AbbasM.W3D",
        r"Art\Textures\AAM-GENTEX.dds",
        r"Art\Textures\Irq_Sarab7.dds",
    ]:
        if art.get(key) != src_art.get(key):
            fails.append(f"parent ART mutated {key}")

    # Unique files must be bit-identical to parents so a same-HLod load cannot recolor/crash.
    if art.get(r"Art\W3D\Irq_AlNajm.W3D") != art.get(r"Art\W3D\Irq_Sarab7.W3D"):
        fails.append("Irq_AlNajm.W3D is not an identical Sarab7 copy")
    if art.get(r"Art\W3D\Irq_AlNajmM.W3D") != art.get(r"Art\W3D\Irq_Raad2M.W3D"):
        fails.append("Irq_AlNajmM.W3D is not an identical Raad2 copy")
    if art.get(r"Art\W3D\Irq_AlHaithamM.W3D") != art.get(r"Art\W3D\Irq_AbbasM.W3D"):
        fails.append("Irq_AlHaithamM.W3D is not an identical AbbasM copy")
    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != SIZE_DATA_608 or sha256_path(SRC_DATA) != SHA_DATA_608:
        raise SystemExit("DATA baseline is not PR #608")
    if SRC_ART.stat().st_size != SIZE_ART_608 or sha256_path(SRC_ART) != SHA_ART_608:
        raise SystemExit("ART baseline is not PR #608")
    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    n_txt = decode(data[NAJM_KEY])
    n_obj = object_body(n_txt, "Iraq_AlNajm")
    data[NAJM_KEY] = to_crlf(n_txt.replace(n_obj, fix_najm_tel(n_obj), 1))
    data[NPROJ_KEY] = to_crlf(fix_najm_proj(decode(data[NPROJ_KEY])))

    h_txt = decode(data[HAITHAM_KEY])
    h_obj = object_body(h_txt, "Iraq_AlHaitham")
    data[HAITHAM_KEY] = to_crlf(h_txt.replace(h_obj, fix_haitham_object(h_obj), 1))
    data[HCHAIN_KEY] = to_crlf(fix_haitham_chain(decode(data[HCHAIN_KEY])))
    data[WEP_KEY] = to_crlf(fix_haitham_weapons(decode(data[WEP_KEY])))
    strip_haitham_rearm(data)

    # Neutralize same-HLod clones. Do not leave a differently textured IRQ_SARAB7 / IRQ_ABBASM / IRQ_RAAD2M.
    art[r"Art\W3D\Irq_AlNajm.W3D"] = bytes(art[r"Art\W3D\Irq_Sarab7.W3D"])
    art[r"Art\W3D\Irq_AlNajmM.W3D"] = bytes(art[r"Art\W3D\Irq_Raad2M.W3D"])
    art[r"Art\W3D\Irq_AlHaithamM.W3D"] = bytes(art[r"Art\W3D\Irq_AbbasM.W3D"])

    write_sources(data)
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

    ext = OUT / "LAST_WINS_EXTRACT/DATA"
    ext.mkdir(parents=True, exist_ok=True)
    for key in [HAITHAM_KEY, NAJM_KEY, HCHAIN_KEY, NPROJ_KEY, WEP_KEY]:
        (ext / Path(key.replace("\\", "/")).name).write_bytes(packed[key])

    report = [
        "SPECTER restore Sarab7 / visible Najm / K+L isolation / no paid rearm",
        f"DATA {len(out_data)} {data_sha}",
        f"ART  {len(out_art)} {art_sha}",
        "",
        "SARAB7 COLOR CONTAMINATION:",
        "  Parent Irq_Sarab7.W3D and AAM-GENTEX.dds were never edited.",
        "  #609 Irq_AlNajm.W3D reused HLod IRQ_SARAB7 with AlNajmSkin.tga.",
        "  SAGE HLod lookup then drew Sarab7 with the Najm material.",
        "",
        "NAJM INVISIBLE / NO FIRE:",
        "  Animation = Irq_AlNajm.Irq_Sarab7 is not a working File.Anim pair.",
        "  Failed unpack/deploy = no model and no PRIMARY fire.",
        "  Restored proven Irq_Sarab7 / Irq_Sarab7.Irq_Sarab7 and Irq_Raad2M.",
        "  Dedicated red deferred: same-HLod recolor contaminates the parent;",
        "  uniquified HLod/anim previously hid the unit.",
        "",
        "SLOT K (Iraq_Alhussaien) vs L (Iraq_AlHaitham):",
        "  K object/INI/CommandSet/OCL were not text-changed in #609.",
        "  Shared suspect: Irq_AlHaithamM.W3D also reused parent HLod IRQ_ABBASM.",
        "  Neutralized unique ICBM/Sarab W3Ds to bit-identical parent copies.",
        "  L still has no riders/paid rearm (requested). That is NOT claimed as the K fix.",
        "",
        "PAID REARM:",
        "  Removed Upgrade/Button/OCL/CommandSet/Strip for Al-Haitham.",
        "  Al-Najm has none. Alabaas Upgrade_Rearm_Iraq_Alhussaien stays 15000.",
        "",
        "STATIC_VALIDATION=PASS",
        "RUNTIME_TEST=NOT RUN",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=YES\n"
        f"DATA_SIZE={len(out_data)}\n"
        f"DATA_SHA256={data_sha}\n"
        f"ART_SIZE={len(out_art)}\n"
        f"ART_SHA256={art_sha}\n"
        "BASELINE=PR #608 (not failed #609)\n"
        "NAJM_RED=DEFERRED_PARENT_IDENTICAL\n"
        "HAITHAM_REARM=REMOVED\n"
        "NAJM_REARM=NONE\n"
        "ALABAAS_REARM=15000\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: restore Sarab7, visible Najm, K/L isolation, no paid rearm\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder.\n"
        "Al-Najm is slot F and currently uses the proven Sarab7 visual chain\n"
        "(parent colors). Dedicated red was deferred to keep the unit visible.\n"
        "Al-Haitham is slot L with no paid rearm. Alabaas rebuild stays $15000.\n"
        "STATIC ONLY. In-game F/K/L/E retest is required.\n",
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Restore Sarab7 / visible Al-Najm / K+L isolation / remove paid rearm\n"
        "\n"
        "- Neutralize same-HLod unique W3Ds that recolored Sarab7 and likely crashed K/L.\n"
        "- Al-Najm uses the proven Sarab7 Model/Animation pair and parent projectile mesh.\n"
        "- Dedicated red is deferred so visibility and firing are not sacrificed.\n"
        "- Remove all Al-Haitham paid-rearm IDs. Alabaas rebuild stays $15,000.\n"
        "- PR #607 gameplay numbers unchanged.\n",
        encoding="utf-8",
    )
    (OUT / "CONFLICTS.txt").write_text(
        "Al-Najm parked/flying currently look like Sarab7. Dedicated red is deferred.\n"
        "Slot E is Sarab7; slot F is Al-Najm; slot K is Alabaas; slot L is Al-Haitham.\n"
        "Haitham has no paid rearm and no rider contain. After fire it uses normal clip behavior.\n"
        "K/L crash is isolated at the HLod-collision class; not proven in-game.\n"
        "STATIC ONLY.\n",
        encoding="utf-8",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "DATA/ART/ZIP links are filled after the GitHub Release is published.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_KL_NAJM_RESTORE.zip"
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
