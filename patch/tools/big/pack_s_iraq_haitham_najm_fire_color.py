#!/usr/bin/env python3
"""Fix Al-Haitham/Al-Najm fire binds and give each a dedicated isolated color.

Baseline: PR #611 / s-iraq-abbas-haitham-oneshot DATA+ART.

Do not re-add paid rearm. Do not edit parent W3D/textures.

Fire:
  Haitham is always-armed (no riders) but launch bones lived only on rider
  states. Copy the Al-Abbas Bones + DEPLOYED launch-bone bind, and point the
  Haitham command set at the proven Al-Abbas FIRE_WEAPON buttons
  (slot-based PRIMARY/SECONDARY).
  Najm keeps Smerch_CommandSet / Command_FireMainWeapon / PRIMARY.

Dedicated ART (BCDHIJ method, not the failed #607/#609 paths):
  Copy parent W3D -> unique file.
  Same-length HLod/mesh prefix replace only (no bone/anim truncation).
  Rebuild texture chunks to a dedicated solid TGA. Never edit AAM-GENTEX,
  Irq_Sarab7.dds, Irq_AbbasMissile.*, or parent W3Ds.
  INI Model/Animation uses File.File on the unique filename.
  Parent Animation cross-file is NOT required because internals are
  uniquified to match the new file the same way Irq_Sarab7.Irq_Sarab7 maps
  onto IRQ_SARAB7.

#607 failed by also inventing File.File names that did not match internals
and by length-mismatched texture replaces (truncated names).
#609 failed by keeping parent HLod IRQ_SARAB7 with a different texture.
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
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ABBAS_HAITHAM_ONESHOT/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_ABBAS_HAITHAM_ONESHOT/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_HAITHAM_NAJM_FIRE_COLOR"

SHA_DATA_611 = "353dc3b0c25b81213edfa630d8c1d957ad0b3b70b5faac4d2fa06ccca02a4c6f"
SIZE_DATA_611 = 366668586
SHA_ART_611 = "2bc140fd19ad138ed6fd34e61d8cea32976af287e2183d5725ca060112236309"
SIZE_ART_611 = 1305667638

TEX_CHUNK = 0x00000032

HAITHAM_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHaitham.ini"
NAJM_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNajm.ini"
ABBAS_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini"
SARAB_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AlNida.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
HCHAIN_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlHaitham_Chain.ini"
NPROJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlNajm_Projectile.ini"
WEP_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlHaithamNajm.ini"
UPG_KEY = r"Data\INI\Upgrade_MissileHalfPriceRearm.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"

PARENT_ART = [
    r"Art\W3D\Irq_Sarab7.W3D",
    r"Art\W3D\Irq_Sarab7D.W3D",
    r"Art\W3D\Irq_Raad2M.W3D",
    r"Art\W3D\Irq_Abbas_L.W3D",
    r"Art\W3D\Irq_Abbas_L_D.W3D",
    r"Art\W3D\Irq_Abbas_L_A.W3D",
    r"Art\W3D\Irq_Abbas_L_AD.W3D",
    r"Art\W3D\Irq_AbbasM.W3D",
    r"Art\Textures\AAM-GENTEX.dds",
    r"Art\Textures\Irq_Sarab7.dds",
    r"Art\Textures\Irq_AbbasMissile.dds",
    r"Art\Textures\Irq_AbbasMissile.tga",
    r"Art\Textures\Irq_AbbasLauncher.tga",
]

LAUNCH_BONES = (
    "      WeaponLaunchBone  = PRIMARY MISSILE\n"
    "      WeaponFireFXBone  = PRIMARY Smoker\n"
    "      WeaponMuzzleFlash = PRIMARY Smoker\n"
    "      WeaponLaunchBone  = SECONDARY MISSILE\n"
    "      WeaponFireFXBone  = SECONDARY Smoker\n"
    "      WeaponMuzzleFlash = SECONDARY Smoker\n"
)


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
    offset = header_size
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", 0)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    blobs = []
    for name, content in items:
        content = bytes(content)
        out += struct.pack(">II", offset, len(content))
        out += name.encode("latin1") + b"\x00"
        blobs.append(content)
        offset += len(content)
    out[4:8] = struct.pack(">I", offset)
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


def uniquify(blob: bytes, old: bytes, new: bytes) -> bytes:
    if len(old) != len(new):
        raise SystemExit(f"identity length {old!r} -> {new!r}")
    return blob.replace(old, new)


def replace_textures(blob: bytes, mapping: dict[str, str]) -> bytes:
    lowmap = {k.lower(): v for k, v in mapping.items()}

    def rebuild(data: bytes) -> bytes:
        out = bytearray()
        pos = 0
        end = len(data)
        while pos + 8 <= end:
            cid, raw = struct.unpack_from("<II", data, pos)
            sz = raw & 0x7FFFFFFF
            cont = bool(raw & 0x80000000)
            cs, ce = pos + 8, pos + 8 + sz
            if ce > end:
                break
            payload = data[cs:ce]
            if cont:
                payload = rebuild(payload)
            elif cid == TEX_CHUNK:
                old = payload.split(b"\x00", 1)[0].decode("latin1", errors="replace")
                if old.lower() in lowmap:
                    payload = lowmap[old.lower()].encode("ascii") + b"\x00"
            new_raw = len(payload) | (0x80000000 if cont else 0)
            out += struct.pack("<II", cid, new_raw)
            out += payload
            pos = ce
        if pos < end:
            out += data[pos:]
        return bytes(out)

    return rebuild(blob)


def texture_names(blob: bytes) -> set[str]:
    found: set[str] = set()
    pos = 0
    end = len(blob)

    def walk(data: bytes, start: int, stop: int) -> None:
        p = start
        while p + 8 <= stop:
            cid, raw = struct.unpack_from("<II", data, p)
            sz = raw & 0x7FFFFFFF
            cont = bool(raw & 0x80000000)
            cs, ce = p + 8, p + 8 + sz
            if ce > stop:
                break
            if cont:
                walk(data, cs, ce)
            elif cid == TEX_CHUNK:
                found.add(data[cs:ce].split(b"\x00", 1)[0].decode("latin1", errors="replace"))
            p = ce

    walk(blob, 0, end)
    return found


def solid_tga32(size: int, rgb: tuple[int, int, int]) -> bytes:
    im = Image.new("RGBA", (size, size), (rgb[0], rgb[1], rgb[2], 255))
    buf = io.BytesIO()
    im.save(buf, format="TGA")
    return buf.getvalue()


def dedicated_w3d(src: bytes, old_id: bytes, new_id: bytes, texmap: dict[str, str]) -> bytes:
    return replace_textures(uniquify(src, old_id, new_id), texmap)


def inject_launch_bones(body: str) -> str:
    def add(block: str) -> str:
        if "WeaponLaunchBone" in block:
            return block
        # Insert after Flags / AnimationMode / Model lines, before particles or ShowSubObject.
        m = re.search(r"(^\s*(?:ShowSubObject|HideSubObject|ParticleSysBone|TransitionKey)\s+=)", block, re.M)
        if m:
            return block[: m.start()] + LAUNCH_BONES + block[m.start() :]
        return block[:-4] + LAUNCH_BONES + "    End"

    def patch_state(text: str, header: str) -> str:
        m = re.search(rf"(^\s*ConditionState\s+=\s+{header}\s*\n.*?^\s*End\s*$)", text, re.M | re.S)
        if not m:
            return text
        return text[: m.start()] + add(m.group(1)) + text[m.end() :]

    body = patch_state(body, r"DEPLOYED")
    body = patch_state(body, r"DEPLOYED REALLYDAMAGED")
    body = patch_state(body, r"RIDER2 DEPLOYED")
    body = patch_state(body, r"RIDER2 DEPLOYED REALLYDAMAGED")
    return body


def retarget_haitham_models(body: str) -> str:
    pairs = [
        ("Irq_Abbas_L_AD", "Irq_AlHthm_L_AD"),
        ("Irq_Abbas_L_A", "Irq_AlHthm_L_A"),
        ("Irq_Abbas_L_D", "Irq_AlHthm_L_D"),
        ("Irq_Abbas_L", "Irq_AlHthm_L"),
    ]
    for old, new in pairs:
        body = body.replace(old, new)
    if "Irq_Abbas_L" in body:
        raise SystemExit("Haitham TEL still references parent Irq_Abbas_L")
    return body


def retarget_najm_models(body: str) -> str:
    body = body.replace("Irq_Sarab7.Irq_Sarab7", "Irq_AlNajm.Irq_AlNajm")
    body = re.sub(r"(^\s*Model\s+=\s+)Irq_Sarab7\s*$", r"\1Irq_AlNajm", body, flags=re.M)
    if re.search(r"Irq_Sarab7", body):
        raise SystemExit("Najm TEL still references Irq_Sarab7")
    return body


def fix_haitham_cmdset(cs: str) -> str:
    m = last_block("CommandSet", "Iraq_AlHaithamArmedCommandSet", cs)
    if not m:
        raise SystemExit("missing Haitham armed command set")
    new = (
        "CommandSet Iraq_AlHaithamArmedCommandSet\n"
        "  1 = Command_IraqAlAbbasICBMFire\n"
        "  5 = Command_AlAbidMissileStrike\n"
        "  12 = Command_IraqDeployUnitWeapon\n"
        "  16 = Command_AttackMove\n"
        "  17 = Command_Guard\n"
        "  14 = Command_Stop\n"
        "End"
    )
    return cs[: m.start()] + new + cs[m.end() :]


def write_sources(data: dict[str, bytes]) -> None:
    mapping = {
        HAITHAM_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlHaitham.ini",
        NAJM_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlNajm.ini",
        HCHAIN_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Iraq_AlHaitham_Chain.ini",
        NPROJ_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Iraq_AlNajm_Projectile.ini",
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
        fails.append("Al-Abbas object mutated")
    if data[SARAB_KEY] != src_data[SARAB_KEY]:
        fails.append("Sarab7 object mutated")
    if data[R11_KEY] != src_data[R11_KEY]:
        fails.append("9P117 mutated")

    if field(h, "BuildCost") != "30000" or field(h, "BuildTime") != "300":
        fails.append("Haitham cost/time")
    if field(n, "BuildCost") != "2500" or not field(n, "BuildTime").startswith("50"):
        fails.append("Najm cost/time")
    if "RiderChangeContain" in h or "Upgrade_Rearm" in h:
        fails.append("Haitham rearm/rider returned")
    if "Upgrade_Rearm" in n:
        fails.append("Najm rearm")

    if "Irq_AlHthm_L" not in h or "Irq_Abbas_L" in h:
        fails.append("Haitham TEL not on dedicated models")
    if "Irq_AlNajm" not in n or "Irq_Sarab7" in n:
        fails.append("Najm TEL not on dedicated models")
    if "Irq_AlNajm.Irq_AlNajm" not in n:
        fails.append("Najm Animation pair")

    if "WeaponLaunchBone" not in h:
        fails.append("Haitham missing launch bones")
    deployed = re.search(r"ConditionState\s+=\s+DEPLOYED\s*\n.*?^\s*End", h, re.M | re.S)
    if not deployed or "WeaponLaunchBone" not in deployed.group(0):
        fails.append("Haitham DEPLOYED has no launch bones")

    wep = decode(data[WEP_KEY])
    if field(last_block("Weapon", "Weapon_Iraq_AlHaitham_Hussiean", wep).group(0), "AttackRange") != "4300":
        fails.append("Haitham range")
    najmw = last_block("Weapon", "Weapon_Iraq_AlNajm", wep).group(0)
    if field(najmw, "AttackRange") != "1376" or "ClipSize                    = 2" not in najmw:
        fails.append("Najm weapon")
    if "AutoReloadsClip         = No" not in last_block("Weapon", "Weapon_Iraq_AlHaitham_Hussiean", wep).group(0):
        fails.append("Haitham one-shot lost")

    chain = decode(data[HCHAIN_KEY])
    nproj = decode(data[NPROJ_KEY])
    if "Irq_AlHaithamM" not in object_body(chain, "Projectile_Iraq_AlHaitham_Hussiean"):
        fails.append("Haitham fly model")
    if "Irq_AlNajmM" not in object_body(nproj, "Projectile_Iraq_AlNajm"):
        fails.append("Najm fly model")

    cb = decode(data[CB_KEY])
    if last_block("CommandButton", "Command_IraqAlAbbasICBMFire", cb) is None:
        fails.append("Al-Abbas fire button missing")
    if last_block("CommandButton", "Command_AlAbidMissileStrike", cb) is None:
        fails.append("AlAbid fire button missing")
    if last_block("CommandButton", "Command_FireMainWeapon", cb) is None:
        fails.append("FireMainWeapon missing")
    if "Object        = Iraq_AlHaitham" not in last_block("CommandButton", "CB_MISSILE_L", cb).group(0):
        fails.append("slot L")
    if "Object        = Iraq_AlNajm" not in last_block("CommandButton", "CB_MISSILE_F", cb).group(0):
        fails.append("slot F")

    cs = decode(data[CS_KEY])
    harmed = last_block("CommandSet", "Iraq_AlHaithamArmedCommandSet", cs).group(0)
    if "Command_IraqAlAbbasICBMFire" not in harmed or "Command_AlAbidMissileStrike" not in harmed:
        fails.append("Haitham not on Al-Abbas fire buttons")
    if "Command_Rearm" in harmed:
        fails.append("Haitham rearm button")
    if field(n, "CommandSet").split()[0] != "Smerch_CommandSet":
        fails.append("Najm lost Smerch fire set")
    smerch = last_block("CommandSet", "Smerch_CommandSet", cs).group(0)
    if "Command_FireMainWeapon" not in smerch:
        fails.append("Smerch has no FireMainWeapon")

    upg = decode(data[UPG_KEY])
    if last_block("Upgrade", "Upgrade_Rearm_Iraq_Alhussaien", upg) or last_block("Upgrade", "Upgrade_Rearm_Iraq_AlHaitham", upg):
        fails.append("paid rearm upgrade present")

    for key in PARENT_ART:
        if key in src_art and art.get(key) != src_art.get(key):
            fails.append(f"parent ART mutated {key}")

    checks = [
        (r"Art\W3D\Irq_AlNajm.W3D", b"IRQ_ALNAJM", b"IRQ_SARAB7", "AlNajmSkin.tga", "AAM-GENTEX.dds"),
        (r"Art\W3D\Irq_AlNajmM.W3D", b"IRQ_ALNAJ2", b"IRQ_RAAD2M", "AlNajmSkin.tga", "AAM-GENTEX.dds"),
        (r"Art\W3D\Irq_AlHaithamM.W3D", b"IRQ_ALHTAM", b"IRQ_ABBASM", "AlHaithamMissile.tga", "Irq_AbbasMissile.tga"),
        (r"Art\W3D\Irq_AlHthm_L.W3D", b"IRQ_ALHTM_L", b"IRQ_ABBAS_L", "AlHaithamMissile.tga", "Irq_AbbasMissile.dds"),
    ]
    for key, uniq, parent, need_tex, ban_tex in checks:
        blob = art.get(key)
        if not blob:
            fails.append(f"missing {key}")
            continue
        if uniq not in blob:
            fails.append(f"{key} missing unique HLod {uniq!r}")
        if parent in blob:
            fails.append(f"{key} still has parent HLod {parent!r}")
        names = texture_names(blob)
        if need_tex not in names:
            fails.append(f"{key} missing {need_tex} {names}")
        if ban_tex in names:
            fails.append(f"{key} still uses {ban_tex}")
    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != SIZE_DATA_611 or sha256_path(SRC_DATA) != SHA_DATA_611:
        raise SystemExit("DATA baseline is not PR #611")
    if SRC_ART.stat().st_size != SIZE_ART_611 or sha256_path(SRC_ART) != SHA_ART_611:
        raise SystemExit("ART baseline is not PR #611")
    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    red = solid_tga32(1024, (200, 8, 8))
    black = solid_tga32(1024, (12, 12, 12))
    art[r"Art\Textures\AlNajmSkin.tga"] = red
    art[r"Art\Textures\AlHaithamMissile.tga"] = black

    najm_tex = {"AAM-GENTEX.dds": "AlNajmSkin.tga"}
    hait_tex = {
        "Irq_AbbasMissile.dds": "AlHaithamMissile.tga",
        "Irq_AbbasMissile.tga": "AlHaithamMissile.tga",
    }
    art[r"Art\W3D\Irq_AlNajm.W3D"] = dedicated_w3d(art[r"Art\W3D\Irq_Sarab7.W3D"], b"IRQ_SARAB7", b"IRQ_ALNAJM", najm_tex)
    art[r"Art\W3D\Irq_AlNajmD.W3D"] = dedicated_w3d(art[r"Art\W3D\Irq_Sarab7D.W3D"], b"IRQ_SARAB7D", b"IRQ_ALNAJMD", najm_tex)
    art[r"Art\W3D\Irq_AlNajmM.W3D"] = dedicated_w3d(art[r"Art\W3D\Irq_Raad2M.W3D"], b"IRQ_RAAD2M", b"IRQ_ALNAJ2", najm_tex)
    art[r"Art\W3D\Irq_AlHthm_L.W3D"] = dedicated_w3d(art[r"Art\W3D\Irq_Abbas_L.W3D"], b"IRQ_ABBAS_L", b"IRQ_ALHTM_L", hait_tex)
    art[r"Art\W3D\Irq_AlHthm_L_D.W3D"] = dedicated_w3d(art[r"Art\W3D\Irq_Abbas_L_D.W3D"], b"IRQ_ABBAS_L_D", b"IRQ_ALHTM_L_D", hait_tex)
    art[r"Art\W3D\Irq_AlHthm_L_A.W3D"] = dedicated_w3d(art[r"Art\W3D\Irq_Abbas_L_A.W3D"], b"IRQ_ABBAS_L_A", b"IRQ_ALHTM_L_A", hait_tex)
    art[r"Art\W3D\Irq_AlHthm_L_AD.W3D"] = dedicated_w3d(art[r"Art\W3D\Irq_Abbas_L_AD.W3D"], b"IRQ_ABBAS_L_AD", b"IRQ_ALHTM_L_AD", hait_tex)
    art[r"Art\W3D\Irq_AlHaithamM.W3D"] = dedicated_w3d(art[r"Art\W3D\Irq_AbbasM.W3D"], b"IRQ_ABBASM", b"IRQ_ALHTAM", hait_tex)

    n_txt = decode(data[NAJM_KEY])
    n_obj = object_body(n_txt, "Iraq_AlNajm")
    data[NAJM_KEY] = to_crlf(n_txt.replace(n_obj, retarget_najm_models(n_obj), 1))

    h_txt = decode(data[HAITHAM_KEY])
    h_obj = object_body(h_txt, "Iraq_AlHaitham")
    data[HAITHAM_KEY] = to_crlf(h_txt.replace(h_obj, inject_launch_bones(retarget_haitham_models(h_obj)), 1))

    chain = decode(data[HCHAIN_KEY]).replace("Model = Irq_AbbasM", "Model = Irq_AlHaithamM")
    if "Irq_AbbasM" in chain:
        raise SystemExit("Haitham chain still parent fly mesh")
    data[HCHAIN_KEY] = to_crlf(chain)

    nproj = decode(data[NPROJ_KEY]).replace("Model = Irq_Raad2M", "Model = Irq_AlNajmM")
    if "Irq_Raad2M" in nproj:
        raise SystemExit("Najm projectile still parent fly mesh")
    data[NPROJ_KEY] = to_crlf(nproj)

    data[CS_KEY] = to_crlf(fix_haitham_cmdset(decode(data[CS_KEY])))
    write_sources(data)

    fails = validate(data, art, src_data, src_art)
    out_data = build_big(data)
    out_art = build_big(art)
    fails.extend([f"DATA {x}" for x in big_structure_ok(out_data)])
    fails.extend([f"ART {x}" for x in big_structure_ok(out_art)])
    fails.extend(validate(parse_big(out_data), parse_big(out_art), src_data, src_art))
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
        (ext / Path(key.replace("\\", "/")).name).write_bytes(parse_big(out_data)[key])
    cs = decode(parse_big(out_data)[CS_KEY])
    (ext / "Iraq_AlHaithamArmedCommandSet.ini").write_text(
        last_block("CommandSet", "Iraq_AlHaithamArmedCommandSet", cs).group(0) + "\n", encoding="latin1"
    )

    report = [
        "SPECTER Haitham/Najm fire bind + isolated dedicated colors",
        f"DATA {len(out_data)} {data_sha}",
        f"ART  {len(out_art)} {art_sha}",
        "",
        "FIRE:",
        "  Haitham CommandSet uses proven Al-Abbas FIRE_WEAPON buttons.",
        "  Haitham DEPLOYED states now have WeaponLaunchBone PRIMARY/SECONDARY.",
        "  Najm keeps Smerch_CommandSet -> Command_FireMainWeapon PRIMARY.",
        "  No riders, no paid rearm.",
        "",
        "DEDICATED ART:",
        "  Unique HLod prefixes, unique solid black/red TGAs.",
        "  Parent Sarab7/Al-Abbas W3D and textures byte-identical to #611.",
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
        "BASELINE=PR #611\n"
        "HAITHAM_COLOR=DEDICATED_BLACK\n"
        "NAJM_COLOR=DEDICATED_RED\n"
        "PAID_REARM=NONE\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Al-Haitham fire + black missile, Al-Najm fire + red missile.\n"
        "Place both complete replacement BIGs in the SPECTER folder.\n"
        "Parent Sarab7 and Al-Abbas art is unchanged.\n"
        "STATIC ONLY.\n",
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Al-Haitham / Al-Najm fire and isolated colors\n"
        "\n"
        "- Haitham uses the Al-Abbas fire buttons and DEPLOYED launch bones.\n"
        "- Najm keeps the Sarab7 Smerch PRIMARY fire bind.\n"
        "- Dedicated unique-HLod W3D copies: Haitham black, Najm red.\n"
        "- Parent textures/W3Ds are not edited. No paid rearm.\n",
        encoding="utf-8",
    )
    (OUT / "CONFLICTS.txt").write_text(
        "Dedicated colors use unique HLod copies. Parked TEL trucks still use the parent launcher sheet.\n"
        "Only the missile meshes sample the dedicated black/red TGA.\n"
        "STATIC ONLY.\n",
        encoding="utf-8",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "DATA/ART/ZIP links are filled after the GitHub Release is published.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_HAITHAM_NAJM_FIRE_COLOR.zip"
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
