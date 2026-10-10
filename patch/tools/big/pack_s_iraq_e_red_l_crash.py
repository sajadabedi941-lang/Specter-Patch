#!/usr/bin/env python3
"""Fix Al-Najm red (still parent-colored) and Al-Haitham produce CTD after PR #608.

Baseline: PR #608 / s-iraq-haitham-visual.

Issue 1 — Najm still not red:
  #608 pointed Iraq_AlNajm Model/Animation at Irq_Sarab7. The parked
  MISSILE01/02 meshes use AAM-GENTEX.dds on that parent W3D. The dedicated
  Irq_AlNajm.W3D (AlNajmSkin.tga) was left unreferenced. AlNajmSkin itself
  was a 1024 make_skin sheet with a black center, so even Irq_AlNajmM UVs
  sampled from AAM-GENTEX islands would not read as red.

  Fix: rebuild Irq_AlNajm.W3D as a bit-identical Irq_Sarab7 copy with only
  AAM-GENTEX.dds -> AlNajmSkin.tga. Keep HLod IRQ_SARAB7. INI Model =
  Irq_AlNajm, Animation = Irq_AlNajm.Irq_Sarab7. Replace AlNajmSkin with a
  solid red TGA so every UV sample is red. Flying Irq_AlNajmM keeps parent
  HLod IRQ_RAAD2M. Sarab7 ART/DATA is not modified.

Issue 2 — Haitham still CTDs on produce:
  #608 restored parent TEL W3Ds; crash persisted, so the W3D uniquify
  theory was incomplete. Packed last-wins IDs all resolve. Remaining
  Haitham-only create-time modules vs working Iraq_Alhussaien:
    RiderChangeContain + InitialPayload GenericFakeRider2
    ObjectCreationUpgrade -> OCL_Rearm contain riders
    Weapon bind -> unique Irq_AlHaithamM + ParticlesAttachedToAnimatedBones
    FireOCL OCL_HussienMissileDisarm (contain Rider1; fire-time)

  Same rider pattern crashed when applied to other NEW factory objects
  (#603). Isolate it. Always-armed WeaponSet. Parent flying model
  Irq_AbbasM. Remove FireOCL contain. Keep $20000 upgrade + button.
  Do not modify Alabaas / Sarab7 / 9P117. Gameplay numbers stay #607.
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
OUT = ROOT / "patch/Release/SPECTER_IRAQ_E_RED_L_CRASH"

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
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"

TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")
RED = (168, 32, 28)


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


def texture_only_copy(src: bytes, old: bytes, new: bytes) -> bytes:
    if len(old) != len(new):
        raise SystemExit(f"texture length {old!r} -> {new!r}")
    if old not in src:
        raise SystemExit(f"parent W3D missing {old!r}")
    out = src.replace(old, new)
    if old in out:
        raise SystemExit(f"parent texture {old!r} still present")
    return out


def solid_red_tga(size: int = 512) -> bytes:
    im = Image.new("RGBA", (size, size), RED + (255,))
    buf = io.BytesIO()
    im.save(buf, format="TGA")
    return buf.getvalue()


def replace_last_block(text: str, kind: str, name: str, new_body: str) -> str:
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\n.*?^End", text))
    if not matches:
        raise SystemExit(f"missing {kind} {name}")
    m = matches[-1]
    return text[: m.start()] + new_body.rstrip() + "\n" + text[m.end() :]


def fix_najm_tel(body: str) -> str:
    body = body.replace("Irq_Sarab7.Irq_Sarab7", "Irq_AlNajm.Irq_Sarab7")
    body = re.sub(r"(^\s*Model\s+=\s+)Irq_Sarab7\s*$", r"\1Irq_AlNajm", body, flags=re.M)
    if re.search(r"^\s*Model\s+=\s+Irq_Sarab7\s*$", body, re.M):
        raise SystemExit("Najm still uses Irq_Sarab7 model")
    if "Irq_AlNajm.Irq_Sarab7" not in body:
        raise SystemExit("Najm animation not Irq_AlNajm.Irq_Sarab7")
    if "Iraq_AlNajm" not in body:
        raise SystemExit("Najm object id lost")
    return body


def fix_haitham_object(body: str) -> str:
    # Always-armed weapon set (no rider conditions).
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

    # Remove create-time rider contain + upgrade OCL that injects riders.
    body = re.sub(
        r"  Behavior = RiderChangeContain ModuleTag_WarheadRider\n.*?  End\n",
        "",
        body,
        count=1,
        flags=re.S,
    )
    body = re.sub(
        r"  Behavior = ObjectCreationUpgrade ModuleTag_Rearm\n.*?  End\n",
        "",
        body,
        count=1,
        flags=re.S,
    )
    if "RiderChangeContain" in body or "InitialPayload" in body:
        raise SystemExit("Haitham still has rider contain")
    if "ObjectCreationUpgrade" in body:
        raise SystemExit("Haitham still has rearm OCL upgrade")

    body = body.replace(
        "KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE HUGE_VEHICLE SCORE SALVAGER GARRISONABLE_UNTIL_DESTROYED",
        "KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE HUGE_VEHICLE SCORE SALVAGER",
    )
    # Always show the mounted missile (was hidden until RIDER2).
    body = body.replace("HideSubObject     = MISSILE01", "ShowSubObject     = MISSILE01")
    if "HideSubObject     = MISSILE01" in body:
        raise SystemExit("Haitham still hides MISSILE01")
    if field(body, "BuildCost") != "30000" or field(body, "BuildTime") != "300":
        raise SystemExit("Haitham cost/time changed during crash isolation")
    return body


def fix_haitham_chain(text: str) -> str:
    text = text.replace("Model = Irq_AlHaithamM", "Model = Irq_AbbasM")
    if "Irq_AlHaithamM" in text:
        raise SystemExit("Haitham chain still uses Irq_AlHaithamM")
    return text


def fix_haitham_weapons(text: str) -> str:
    # FireOCL injects GenericFakeRider1 into the firer. Unsafe without contain.
    text = re.sub(r"^  FireOCL\s+=\s+OCL_HussienMissileDisarm\r?\n", "", text, flags=re.M)
    if "OCL_HussienMissileDisarm" in text:
        raise SystemExit("Haitham weapons still FireOCL disarm")
    return text


def fix_commandset(text: str) -> str:
    m = last_block("CommandSet", "Iraq_AlHaithamArmedCommandSet", text)
    if not m:
        raise SystemExit("armed command set missing")
    block = m.group(0)
    if "Command_Rearm_Iraq_AlHaitham" not in block:
        block = block.replace(
            "  5 = Command_AlHaithamAlAbidStrike\n",
            "  5 = Command_AlHaithamAlAbidStrike\n  8 = Command_Rearm_Iraq_AlHaitham\n",
        )
    if "Command_Rearm_Iraq_AlHaitham" not in block:
        raise SystemExit("failed to add rearm button to armed set")
    return text[: m.start()] + block + text[m.end() :]


def fix_ocl(text: str) -> str:
    m = last_block("ObjectCreationList", "OCL_Rearm_Iraq_AlHaitham", text)
    if not m:
        raise SystemExit("OCL_Rearm_Iraq_AlHaitham missing")
    new = (
        "ObjectCreationList OCL_Rearm_Iraq_AlHaitham\n"
        "  CreateObject\n"
        "    ObjectNames       = RearmStrip_Iraq_AlHaitham\n"
        "    Count             = 1\n"
        "    Disposition       = LIKE_EXISTING\n"
        "  End\n"
        "End"
    )
    return text[: m.start()] + new + text[m.end() :]


def write_sources(data: dict[str, bytes]) -> None:
    mapping = {
        HAITHAM_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlHaitham.ini",
        NAJM_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlNajm.ini",
        HCHAIN_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Iraq_AlHaitham_Chain.ini",
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
    if data[UPG_KEY] != src_data[UPG_KEY]:
        fails.append("upgrade file mutated")
    if data[CB_KEY] != src_data[CB_KEY]:
        fails.append("CommandButton mutated")

    cb = decode(data[CB_KEY])
    if "Object        = Iraq_AlNajm" not in last_block("CommandButton", "CB_MISSILE_F", cb).group(0):
        fails.append("slot F is not Najm")
    if "Object        = Iraq_Sarab7" not in last_block("CommandButton", "CB_MISSILE_E", cb).group(0):
        fails.append("slot E Sarab7 lost")
    if "Object        = Iraq_AlHaitham" not in last_block("CommandButton", "CB_MISSILE_L", cb).group(0):
        fails.append("slot L is not Haitham")

    wep = decode(data[WEP_KEY])
    if field(last_block("Weapon", "Weapon_Iraq_AlHaitham_Hussiean", wep).group(0), "AttackRange") != "4300":
        fails.append("Haitham range")
    if field(last_block("Weapon", "Weapon_Iraq_AlNajm", wep).group(0), "AttackRange") != "1376":
        fails.append("Najm range")
    if field(last_block("Weapon", "Weapon_Iraq_AlHaitham_HussieanWH", wep).group(0), "PrimaryDamage") not in {"75000", "75000.0"}:
        fails.append("Haitham warhead")
    if field(last_block("Weapon", "Weapon_Iraq_AlNajm", wep).group(0), "PrimaryDamage") != "2000":
        fails.append("Najm damage")
    if "OCL_HussienMissileDisarm" in wep:
        fails.append("Haitham FireOCL still present")

    if "RiderChangeContain" in h or "InitialPayload" in h:
        fails.append("Haitham still has riders")
    if re.search(r"Conditions = WEAPON_RIDER", h):
        fails.append("Haitham still rider-gated")
    if "Irq_Abbas_L" not in h:
        fails.append("Haitham lost parent TEL model")

    n_models = [m for m in models(n) if m.startswith("Irq_")]
    if any(m != "Irq_AlNajm" for m in n_models):
        fails.append(f"Najm models {n_models}")
    if any(a != "Irq_AlNajm.Irq_Sarab7" for a in anims(n)):
        fails.append(f"Najm anims {anims(n)}")

    chain = decode(data[HCHAIN_KEY])
    nproj = decode(data[NPROJ_KEY])
    fly = object_body(chain, "Projectile_Iraq_AlHaitham_Hussiean")
    nfly = object_body(nproj, "Projectile_Iraq_AlNajm")
    if not fly or "Irq_AbbasM" not in fly:
        fails.append("Haitham projectile not parent Irq_AbbasM")
    if not nfly or "Irq_AlNajmM" not in nfly:
        fails.append("Najm projectile model")
    if field(fly, "MaxHealth") != "6800.0":
        fails.append("Haitham stealth HP")
    if field(nfly, "MaxHealth") != "2000.0":
        fails.append("Najm stealth HP")

    cs = decode(data[CS_KEY])
    armed = last_block("CommandSet", "Iraq_AlHaithamArmedCommandSet", cs)
    if not armed or "Command_Rearm_Iraq_AlHaitham" not in armed.group(0):
        fails.append("armed set missing $20000 rearm button")
    upg = last_block("Upgrade", "Upgrade_Rearm_Iraq_AlHaitham", decode(data[UPG_KEY]))
    if not upg or field(upg.group(0), "BuildCost") != "20000":
        fails.append("Haitham rearm price")
    abup = last_block("Upgrade", "Upgrade_Rearm_Iraq_Alhussaien", decode(data[UPG_KEY]))
    if not abup or field(abup.group(0), "BuildCost") != "15000":
        fails.append("Alabaas rearm price")

    ocl = last_block("ObjectCreationList", "OCL_Rearm_Iraq_AlHaitham", decode(data[OCL_KEY]))
    if not ocl:
        fails.append("OCL_Rearm missing")
    elif "GenericFakeRider" in ocl.group(0) or "ContainInsideSourceObject" in ocl.group(0):
        fails.append("OCL_Rearm still injects riders")

    for key in [
        r"Art\W3D\Irq_Abbas_L.W3D",
        r"Art\W3D\Irq_AbbasM.W3D",
        r"Art\W3D\Irq_Sarab7.W3D",
        r"Art\W3D\Irq_Raad2M.W3D",
    ]:
        if art.get(key) != src_art.get(key):
            fails.append(f"parent ART mutated {key}")

    tel = art.get(r"Art\W3D\Irq_AlNajm.W3D")
    flyw = art.get(r"Art\W3D\Irq_AlNajmM.W3D")
    if not tel or b"IRQ_SARAB7" not in tel or b"IRQ_ALNAJT" in tel:
        fails.append("Najm TEL W3D lost parent HLod")
    if not tel or b"AlNajmSkin.tga" not in tel or b"AAM-GENTEX.dds" in tel:
        fails.append("Najm TEL W3D not bound to AlNajmSkin.tga")
    if not flyw or b"IRQ_RAAD2M" not in flyw or b"IRQ_ALNAJM" in flyw:
        fails.append("Najm projectile W3D lost parent HLod")
    if not flyw or b"AlNajmSkin.tga" not in flyw or b"AAM-GENTEX.dds" in flyw:
        fails.append("Najm projectile W3D not bound to AlNajmSkin.tga")
    tex = art.get(r"Art\Textures\AlNajmSkin.tga")
    if not tex:
        fails.append("AlNajmSkin.tga missing")
    else:
        im = Image.open(io.BytesIO(tex)).convert("RGB")
        cx, cy = im.size[0] // 2, im.size[1] // 2
        center = im.getpixel((cx, cy))
        if center[0] < 120 or center[1] > 80:
            fails.append(f"AlNajmSkin center not red {center}")
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
    n_txt = n_txt.replace(n_obj, fix_najm_tel(n_obj), 1)
    data[NAJM_KEY] = to_crlf(n_txt)

    h_txt = decode(data[HAITHAM_KEY])
    h_obj = object_body(h_txt, "Iraq_AlHaitham")
    h_txt = h_txt.replace(h_obj, fix_haitham_object(h_obj), 1)
    data[HAITHAM_KEY] = to_crlf(h_txt)

    data[HCHAIN_KEY] = to_crlf(fix_haitham_chain(decode(data[HCHAIN_KEY])))
    data[WEP_KEY] = to_crlf(fix_haitham_weapons(decode(data[WEP_KEY])))
    data[CS_KEY] = to_crlf(fix_commandset(decode(data[CS_KEY])))
    data[OCL_KEY] = to_crlf(fix_ocl(decode(data[OCL_KEY])))

    red = solid_red_tga(512)
    art[r"Art\Textures\AlNajmSkin.tga"] = red
    art[r"Art\W3D\Irq_AlNajm.W3D"] = texture_only_copy(
        art[r"Art\W3D\Irq_Sarab7.W3D"],
        b"AAM-GENTEX.dds",
        b"AlNajmSkin.tga",
    )
    art[r"Art\W3D\Irq_AlNajmM.W3D"] = texture_only_copy(
        art[r"Art\W3D\Irq_Raad2M.W3D"],
        b"AAM-GENTEX.dds",
        b"AlNajmSkin.tga",
    )

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

    # last-wins extracts
    ext = OUT / "LAST_WINS_EXTRACT/DATA"
    ext.mkdir(parents=True, exist_ok=True)
    for key in [HAITHAM_KEY, NAJM_KEY, HCHAIN_KEY, NPROJ_KEY, WEP_KEY]:
        (ext / Path(key.replace("\\", "/")).name).write_bytes(packed[key])

    report = [
        "SPECTER Al-Najm red + Al-Haitham produce-CTD isolation",
        f"DATA {len(out_data)} {data_sha}",
        f"ART  {len(out_art)} {art_sha}",
        "",
        "NAJM OLD COLOR ROOT CAUSE:",
        "  Effective parked Model/Animation was Irq_Sarab7 / Irq_Sarab7.Irq_Sarab7.",
        "  MISSILE01/02 on that W3D use AAM-GENTEX.dds (shared with Sarab7).",
        "  Dedicated Irq_AlNajm.W3D was unreferenced after PR #608.",
        "  AlNajmSkin.tga was a 1024 make_skin with a black center; Raad2 UVs",
        "  do not paint from that sheet the way AAM-GENTEX islands do.",
        "",
        "NAJM FIX:",
        "  Irq_AlNajm.W3D = Irq_Sarab7 copy, texture-only, HLod IRQ_SARAB7.",
        "  Animation = Irq_AlNajm.Irq_Sarab7 (file new, internal anim parent).",
        "  AlNajmSkin.tga = solid red 512 so every UV sample is red.",
        "  Flying Irq_AlNajmM keeps IRQ_RAAD2M + AlNajmSkin.tga.",
        "  Slot E remains Iraq_Sarab7. Al-Najm is slot F. Sarab7 not modified.",
        "",
        "HAITHAM CTD — STATIC FINDING (runtime unconfirmed):",
        "  #608 parent TEL restore did not stop the produce crash.",
        "  All packed object/weapon/OCL/command/art IDs resolve.",
        "  Remaining Haitham-only create-time modules vs working Alabaas:",
        "    RiderChangeContain + InitialPayload GenericFakeRider2",
        "    ObjectCreationUpgrade OCL_Rearm contain riders",
        "    unique Irq_AlHaithamM + ParticlesAttachedToAnimatedBones",
        "    FireOCL OCL_HussienMissileDisarm (contain Rider1)",
        "  Isolated those. Always-armed WeaponSet. Flying model Irq_AbbasM.",
        "  $20000 Upgrade_Rearm_Iraq_AlHaitham kept on the armed command set.",
        "  Rider restore itself was removed so it cannot keep crashing spawn.",
        "",
        "STATIC_VALIDATION=PASS",
        "RUNTIME_TEST=NOT RUN (produce/color claim requires in-game retest)",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=YES\n"
        f"DATA_SIZE={len(out_data)}\n"
        f"DATA_SHA256={data_sha}\n"
        f"ART_SIZE={len(out_art)}\n"
        f"ART_SHA256={art_sha}\n"
        "BASELINE=PR #608\n"
        "GAMEPLAY_NUMBERS=UNCHANGED\n"
        "NAJM_SLOT=F\n"
        "HAITHAM_SLOT=L\n"
        "SARAB7_SLOT=E\n"
        "HAITHAM_RIDERS=REMOVED\n"
        "HAITHAM_REARM_PRICE=20000\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Al-Najm red + Al-Haitham produce-CTD isolation\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder.\n"
        "Al-Najm is factory slot F (not E; E is still Sarab7).\n"
        "Al-Haitham is factory slot L.\n"
        "Gameplay numbers from PR #607 are unchanged.\n"
        "In-game produce/color still needs a user retest.\n",
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Al-Najm red + Al-Haitham produce-CTD isolation\n"
        "\n"
        "- Bind Al-Najm TEL/projectile to a parent-HLod W3D whose missile meshes use solid-red `AlNajmSkin.tga`.\n"
        "- Do not modify Sarab7. Slot E stays `Iraq_Sarab7`; Al-Najm stays slot F.\n"
        "- Isolate Al-Haitham create-time riders/FireOCL contain. Always-armed weapons. Parent `Irq_AbbasM` flight model.\n"
        "- Keep the $20,000 rearm upgrade price. Rider restore was removed because it is the remaining spawn-CTD suspect.\n"
        "- PR #607 gameplay numbers unchanged.\n",
        encoding="utf-8",
    )
    (OUT / "CONFLICTS.txt").write_text(
        "Slot E is still Iraq_Sarab7. Producing E will not be red; that is Sarab7, not Al-Najm.\n"
        "Al-Najm is slot F. Parked truck body still uses Irq_Sarab7.dds; only MISSILE01/02 are red.\n"
        "Haitham flying model is the working parent Irq_AbbasM (not a dedicated black W3D).\n"
        "Haitham rider-based rebuild restore was removed. The $20000 upgrade button remains.\n"
        "Without riders, FireOCL disarm was also removed so fire cannot inject Rider1 into a non-contain unit.\n"
        "Alabaas, Sarab7, and 9P117 are not modified.\n"
        "STATIC ONLY. Produce/color not claimed fixed in-game.\n",
        encoding="utf-8",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "DATA/ART/ZIP links are filled after the GitHub Release is published.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_E_RED_L_CRASH.zip"
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
