#!/usr/bin/env python3
"""Fix Iraq_AlFahd500 fire (Weapon.ini load) and flying-missile Iraqi flag.

Live baselines:
  DATA  SPECTER_MISSILE_FACTORY_BUTTON
        SHA256 fcc5cc49fc50e22bf89c5af40b7a1a1cde9035f83c212c90b6fbee2b8bd40288
  ART   SPECTER_MISSILE_FACTORY_TGA24
        SHA256 77ea62f6e28ad356e7c6ac6f46f6c69b2b9736999a46d89988ee333db3610e33

Does not touch Missile Factory, missile_factory.tga, original 9P117/R11 assets,
or GENERIC-MISSILES.dds. Al-Fahd W3D internals are renamed so they cannot
overwrite IRQ_9P117 / IRQ_R11_M at runtime.
"""
from __future__ import annotations

import hashlib
import io
import re
import shutil
import struct
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_MISSILE_FACTORY_BUTTON/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_MISSILE_FACTORY_TGA24/_SPEC_ART_ONE.big"
WEAPON_SRC = ROOT / "patch/Data/INI/Weapon_Iraq_AlFahd500.ini"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD_FIRE_FLAG"

BASE_DATA_SHA = "fcc5cc49fc50e22bf89c5af40b7a1a1cde9035f83c212c90b6fbee2b8bd40288"
BASE_ART_SHA = "77ea62f6e28ad356e7c6ac6f46f6c69b2b9736999a46d89988ee333db3610e33"
BASE_DATA_SIZE = 366368481
BASE_ART_SIZE = 1262282712

OLD_WEAPON_KEY = r"Data\INI\Weapon_Iraq_AlFahd500.ini"
WEAPON_INI_KEY = r"Data\INI\Weapon.ini"
UNIT_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
UNIT_SRC = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlFahd500.ini"
LAUNCHER_W3D_KEY = r"Art\W3D\Irq_AlFahd500.W3D"
LAUNCHERD_W3D_KEY = r"Art\W3D\Irq_AlFahd500D.W3D"
PROJ_W3D_KEY = r"Art\W3D\Irq_AlFahd500M.W3D"
PROJ_TEX_KEY = r"Art\Textures\Irq_AlFahd500P.tga"
LAUNCHER_TEX_KEY = r"Art\Textures\Irq_AlFahd500M.tga"
FLAG_KEY = r"Art\Textures\IraqiFlag.dds"
GENERIC_KEY = r"Art\Textures\GENERIC-MISSILES.dds"
FACTORY_TGA_KEY = r"Art\Textures\missile_factory.tga"

TEX_CHUNK = 0x00000032
MESH_HEADER = 0x0000001F
TEXCOORD_CHUNK = 0x0000004A
HLOD_HEADER = 0x00000701
TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")

OLD_RESIDUE = [
    b"Iraq_AlHussein_New",
    b"Iraq_AlHijarah_New",
    b"Iraq_AlAbbas_New",
    b"Iraq_Badr2000_New",
    b"Iraq_AlSamoud_New",
    b"Iraq_Ababil100_New",
    b"Iraq_Tammuz1_New",
    b"Iraq_AlAbid_New",
    b"Object Iraq_MissileFactory",
    b"Iraq_MissileFactoryCommandSet",
    b"Command_ConstructIraq_MissileFactory",
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
        raise ValueError("not BIGF")
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


def zstr(buf: bytes) -> str:
    return buf.split(b"\x00", 1)[0].decode("latin1", errors="replace")


def to_crlf(data: bytes) -> bytes:
    text = data.decode("latin1").replace("\r\n", "\n").replace("\n", "\r\n")
    return text.encode("latin1")


def uniquify_w3d_identity(blob: bytes, replacements: list[tuple[bytes, bytes]]) -> bytes:
    """Same-length ASCII rename of W3D hierarchy/container/anim identities.

    ZH registers W3D assets globally by these 16-char names. Al-Fahd clones that
    still said IRQ_9P117 / IRQ_R11_M overwrote the original 9P117/R11 visuals
    at runtime even though the original files were byte-identical.
    """
    out = blob
    for old, new in replacements:
        if len(old) != len(new):
            raise ValueError(f"identity length mismatch {old!r} -> {new!r}")
        out = out.replace(old, new)
    return out


def walk_rebuild(blob: bytes, mesh_name: str | None = None) -> bytes:
    """Rebuild W3D, remapping projectile UVs and texture name."""
    out = bytearray()
    pos = 0
    end = len(blob)
    current_mesh = mesh_name
    while pos + 8 <= end:
        cid, raw = struct.unpack_from("<II", blob, pos)
        sz = raw & 0x7FFFFFFF
        cont = bool(raw & 0x80000000)
        cs, ce = pos + 8, pos + 8 + sz
        if ce > end:
            break
        payload = blob[cs:ce]
        if cid == MESH_HEADER and len(payload) >= 24:
            current_mesh = zstr(payload[8:24])
        if cont:
            payload = walk_rebuild(payload, current_mesh)
        elif cid == TEX_CHUNK:
            payload = b"Irq_AlFahd500P.tga\x00"
        elif cid == TEXCOORD_CHUNK:
            payload = remap_uv_payload(payload, current_mesh or "")
        new_raw = len(payload) | (0x80000000 if cont else 0)
        out += struct.pack("<II", cid, new_raw)
        out += payload
        pos = ce
    if pos < end:
        out += blob[pos:]
    return bytes(out)


def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def remap_uv_payload(payload: bytes, mesh_name: str) -> bytes:
    n = len(payload) // 8
    out = bytearray()
    for i in range(n):
        u, v = struct.unpack_from("<ff", payload, i * 8)
        u2, v2 = remap_uv(u, v, mesh_name)
        out += struct.pack("<ff", u2, v2)
    return bytes(out)


def remap_uv(u: float, v: float, mesh_name: str) -> tuple[float, float]:
    """Map original atlas islands onto the dedicated yellow+flag sheet.

    Body cylinder unwrap occupies u=0.04..0.96, v=0.12..0.82 of Irq_AlFahd500P.tga.
    Fins/caps sample a solid yellow strip at v=0.90..0.98.
    """
    # BOOSTER main body (length along U, circumference along V)
    if 0.40 <= u <= 0.60 and 0.18 <= v <= 0.32:
        u2 = clamp01((u - 0.4694) / (0.5305 - 0.4694))
        v2 = clamp01((v - 0.2211) / (0.2843 - 0.2211))
        return 0.04 + u2 * 0.92, 0.12 + v2 * 0.70
    # MISSILE01 / warhead cylinder
    if 0.64 <= u <= 0.76 and 0.80 <= v <= 0.88:
        u2 = clamp01((u - 0.6708) / (0.7317 - 0.6708))
        v2 = clamp01((v - 0.8189) / (0.8634 - 0.8189))
        return 0.04 + u2 * 0.92, 0.12 + v2 * 0.70
    # remaining islands (fins, caps, engine) -> solid yellow
    return 0.50, 0.94


def texture_names(blob: bytes) -> set[str]:
    found: set[str] = set()
    pos = 0
    end = len(blob)

    def rec(data: bytes, start: int, stop: int) -> None:
        p = start
        while p + 8 <= stop:
            cid, raw = struct.unpack_from("<II", data, p)
            sz = raw & 0x7FFFFFFF
            cont = bool(raw & 0x80000000)
            cs, ce = p + 8, p + 8 + sz
            if ce > stop:
                break
            if cont:
                rec(data, cs, ce)
            elif cid == TEX_CHUNK:
                found.add(zstr(data[cs:ce]))
            p = ce

    rec(blob, 0, end)
    return found


def hlod_name(blob: bytes) -> str | None:
    pos = 0
    end = len(blob)
    while pos + 8 <= end:
        cid, raw = struct.unpack_from("<II", blob, pos)
        sz = raw & 0x7FFFFFFF
        cont = bool(raw & 0x80000000)
        cs, ce = pos + 8, pos + 8 + sz
        if ce > end:
            break
        if cid == HLOD_HEADER and ce - cs >= 24:
            return zstr(blob[cs + 8 : cs + 24])
        if cont:
            name = hlod_name(blob[cs:ce])
            if name:
                return name
        pos = ce
    return None


def collect_uvs(blob: bytes) -> list[tuple[str, float, float]]:
    uvs: list[tuple[str, float, float]] = []
    mesh = ""

    def rec(data: bytes, start: int, stop: int) -> None:
        nonlocal mesh
        p = start
        while p + 8 <= stop:
            cid, raw = struct.unpack_from("<II", data, p)
            sz = raw & 0x7FFFFFFF
            cont = bool(raw & 0x80000000)
            cs, ce = p + 8, p + 8 + sz
            if ce > stop:
                break
            if cid == MESH_HEADER and ce - cs >= 24:
                mesh = zstr(data[cs + 8 : cs + 24])
            if cont:
                rec(data, cs, ce)
            elif cid == TEXCOORD_CHUNK:
                n = (ce - cs) // 8
                for i in range(n):
                    u, v = struct.unpack_from("<ff", data, cs + i * 8)
                    uvs.append((mesh, u, v))
            p = ce

    rec(blob, 0, len(blob))
    return uvs


def make_tga24(im: Image.Image) -> bytes:
    rgb = im.convert("RGB")
    w, h = rgb.size
    pixels = rgb.tobytes()
    rows = []
    stride = w * 3
    for y in range(h - 1, -1, -1):
        src = pixels[y * stride : (y + 1) * stride]
        bgr = bytearray()
        for i in range(0, len(src), 3):
            r, g, b = src[i], src[i + 1], src[i + 2]
            bgr += bytes((b, g, r))
        rows.append(bytes(bgr))
    header = bytearray(18)
    header[2] = 2
    struct.pack_into("<HH", header, 12, w, h)
    header[16] = 24
    header[17] = 0x00
    return bytes(header) + b"".join(rows) + TRUEVISION


def tga_info(blob: bytes) -> dict:
    return {
        "width": struct.unpack_from("<H", blob, 12)[0],
        "height": struct.unpack_from("<H", blob, 14)[0],
        "type": blob[2],
        "bpp": blob[16],
        "alpha_bits": blob[17] & 0x0F,
        "descriptor": f"0x{blob[17]:02x}",
        "origin": "top" if blob[17] & 0x20 else "bottom",
        "size": len(blob),
    }


def make_projectile_texture(flag: Image.Image) -> Image.Image:
    """Yellow missile sheet with a large Iraqi flag on the body unwrap."""
    w = h = 512
    im = Image.new("RGB", (w, h), (232, 196, 24))
    px = im.load()
    # Subtle gold shading so the cylinder does not read as a flat sticker.
    for y in range(h):
        shade = 1.0 - 0.18 * abs((y / h) - 0.47)
        for x in range(w):
            if y >= int(0.87 * h):
                px[x, y] = (236, 200, 28)
                continue
            r = min(255, int(232 * shade))
            g = min(255, int(196 * shade))
            b = min(40, int(24 * shade))
            px[x, y] = (r, g, b)
    fw, fh = 360, 180
    flag_im = flag.convert("RGBA").resize((fw, fh), Image.Resampling.NEAREST)
    bordered = Image.new("RGBA", (fw + 8, fh + 8), (10, 10, 10, 255))
    bordered.paste(flag_im, (4, 4), flag_im)
    # Centered on the body UV rectangle (u 0.04-0.96, v 0.12-0.82).
    cx = int(0.50 * w) - bordered.size[0] // 2
    cy = int(0.47 * h) - bordered.size[1] // 2
    im.paste(bordered.convert("RGB"), (max(0, cx), max(0, cy)))
    return im


def weapon_block() -> str:
    text = WEAPON_SRC.read_text(encoding="latin1")
    m = re.search(r"(?ms)^Weapon Weapon_Iraq_AlFahd500\r?\n.*?^End\s*", text)
    if not m:
        raise SystemExit("weapon source missing block")
    block = m.group(0).replace("\r\n", "\n").replace("\n", "\r\n").strip()
    if "PrimaryDamage               = 4000.0" not in block:
        raise SystemExit("weapon source damage not 4000")
    if "AttackRange                 = 1720.0" not in block:
        raise SystemExit("weapon source range mismatch")
    if "MinimumAttackRange          = 800.0" not in block:
        raise SystemExit("weapon source min range mismatch")
    return block


def append_weapon(weapon_ini: bytes, block: str) -> bytes:
    text = weapon_ini.decode("latin1")
    if "Weapon Weapon_Iraq_AlFahd500" in text:
        raise SystemExit("Weapon_Iraq_AlFahd500 already in Weapon.ini")
    if not text.endswith("\r\n"):
        text += "\r\n"
    text += "\r\n; ===== Iraq AL-Fahd 500 (relocated from unloaded Weapon_Iraq_AlFahd500.ini) =====\r\n"
    text += block
    if not text.endswith("\r\n"):
        text += "\r\n"
    return text.encode("latin1")


def commandset_block(text: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^CommandSet {re.escape(name)}\r?\n.*?^End", text)
    return m.group(0) if m else None


def slot_map(block: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def validate(
    data: dict[str, bytes],
    art: dict[str, bytes],
    src_data: dict[str, bytes],
    src_art: dict[str, bytes],
) -> list[str]:
    fails: list[str] = []
    all_ini = b"".join(v for k, v in data.items() if k.lower().endswith(".ini"))

    if all_ini.count(b"Weapon Weapon_Iraq_AlFahd500") != 1:
        fails.append(f"weapon def count {all_ini.count(b'Weapon Weapon_Iraq_AlFahd500')}")
    if OLD_WEAPON_KEY in data:
        fails.append("unloaded standalone weapon file still packed")
    if b"Weapon Weapon_Iraq_AlFahd500" not in data[WEAPON_INI_KEY]:
        fails.append("weapon missing from Weapon.ini")
    if b"Weapon Weapon_Iraq_AlFahd500" in src_data[WEAPON_INI_KEY]:
        fails.append("baseline Weapon.ini already had AlFahd")

    wep = re.search(
        r"(?ms)^Weapon Weapon_Iraq_AlFahd500\r?\n.*?^End",
        data[WEAPON_INI_KEY].decode("latin1"),
    )
    if not wep:
        fails.append("cannot extract packed weapon")
    else:
        body = wep.group(0)
        for need in [
            "PrimaryDamage               = 4000.0",
            "AttackRange                 = 1720.0",
            "MinimumAttackRange          = 800.0",
            "ProjectileObject            = Projectile_Iraq_AlFahd500",
            "ClipReloadTime              = 95000",
            "AntiGround                  = Yes",
        ]:
            if need not in body:
                fails.append(f"weapon missing {need}")

    unit = data[r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"].decode("latin1")
    if "Weapon = PRIMARY   Weapon_Iraq_AlFahd500" not in unit:
        fails.append("unit weapon link")
    if "BuildCost       = 3000" not in unit or "BuildTime       = 17.0" not in unit:
        fails.append("unit cost/time")
    if "CommandSet    = Scud_B_CommandSet" not in unit:
        fails.append("unit commandset")
    if "KindOf = PRELOAD SELECTABLE CAN_ATTACK" not in unit:
        fails.append("unit KindOf")
    if "Animation       = Irq_9P117.Irq_9P117" in unit or "Animation       = Irq_9P117D.Irq_9P117D" in unit:
        fails.append("AlFahd still plays original 9P117 animations")
    if "Irq_AlFahd500.IRQ_AF500" not in unit or "Irq_AlFahd500D.IRQ_AF500D" not in unit:
        fails.append("AlFahd dedicated animations missing")

    proj = data[r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini"].decode("latin1")
    if "Model = Irq_AlFahd500M" not in proj:
        fails.append("projectile model")
    if "MissileAIUpdate" not in proj:
        fails.append("projectile AI")

    cs = data[r"Data\INI\CommandSet.ini"].decode("latin1")
    if cs != src_data[r"Data\INI\CommandSet.ini"].decode("latin1"):
        fails.append("CommandSet.ini mutated")
    scud = commandset_block(cs, "Scud_B_CommandSet") or ""
    slots = slot_map(scud)
    if slots.get(1) != "Command_FireMainWeapon":
        fails.append("FireMainWeapon not slot 1")
    if any(s > 18 for s in slots):
        fails.append("Scud_B slot > 18")
    vt = commandset_block(cs, "Iraq_VT72BCommandSet") or ""
    vt_slots = slot_map(vt)
    if any(s > 18 for s in vt_slots):
        fails.append("VT72B slot > 18")
    if vt_slots.get(14) != "Command_ConstructIraq_AlFahdMissileFactory":
        fails.append("factory button lost")

    cb = data[r"Data\INI\CommandButton.ini"].decode("latin1")
    if cb != src_data[r"Data\INI\CommandButton.ini"].decode("latin1"):
        fails.append("CommandButton.ini mutated")
    if "ButtonImage      = missile_factory" not in cb:
        fails.append("factory ButtonImage lost")

    if data[r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"] != src_data[
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
    ]:
        fails.append("R11/9P117 mutated")
    fac = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
    if data[fac] != src_data[fac]:
        fails.append("Missile Factory object mutated")

    for needle in OLD_RESIDUE:
        if needle in all_ini:
            fails.append(f"old 8-missile residue {needle!r}")

    # ART
    if GENERIC_KEY not in art or art[GENERIC_KEY] != src_art[GENERIC_KEY]:
        fails.append("GENERIC-MISSILES.dds mutated")
    if FLAG_KEY not in art or art[FLAG_KEY] != src_art[FLAG_KEY]:
        fails.append("IraqiFlag.dds mutated")
    if art[FACTORY_TGA_KEY] != src_art[FACTORY_TGA_KEY]:
        fails.append("missile_factory.tga mutated")
    if art[LAUNCHER_TEX_KEY] != src_art[LAUNCHER_TEX_KEY]:
        fails.append("launcher missile atlas mutated")
    for donor in ["Irq_9P117", "Irq_9P117D", "Irq_9P117R", "Irq_R11_M"]:
        k = f"Art\\W3D\\{donor}.W3D"
        if art[k] != src_art[k]:
            fails.append(f"donor W3D mutated {donor}")
    for tex in ["Irq_9P117.dds", "Irq_9P117D.dds", "Irq_9P117R.dds"]:
        k = f"Art\\Textures\\{tex}"
        if art[k] != src_art[k]:
            fails.append(f"donor texture mutated {tex}")

    for key, forbidden in [
        (LAUNCHER_W3D_KEY, b"IRQ_9P117"),
        (LAUNCHERD_W3D_KEY, b"IRQ_9P117"),
        (PROJ_W3D_KEY, b"IRQ_R11_M"),
        (PROJ_W3D_KEY, b"IRQ_9P117"),
    ]:
        if forbidden in art[key]:
            fails.append(f"{key} still contains {forbidden.decode()}")
    for key, required in [
        (LAUNCHER_W3D_KEY, b"IRQ_AF500"),
        (LAUNCHERD_W3D_KEY, b"IRQ_AF500D"),
        (PROJ_W3D_KEY, b"IRQ_ALF_M"),
    ]:
        if required not in art[key]:
            fails.append(f"{key} missing dedicated identity {required.decode()}")
    # Original 9P117 still owns its identities.
    if b"IRQ_9P117" not in art[r"Art\W3D\Irq_9P117.W3D"]:
        fails.append("original 9P117 lost IRQ_9P117 identity")
    if b"IRQ_AF500" in art[r"Art\W3D\Irq_9P117.W3D"] or b"Irq_AlFahd500" in art[r"Art\W3D\Irq_9P117.W3D"]:
        fails.append("original 9P117 W3D picked up Al-Fahd identity")
    if b"IRQ_R11_M" not in art[r"Art\W3D\Irq_R11_M.W3D"]:
        fails.append("original Irq_R11_M lost identity")
    if b"Irq_AlFahd500P.tga" in art[r"Art\W3D\Irq_R11_M.W3D"] or b"Irq_AlFahd500M.tga" in art[r"Art\W3D\Irq_R11_M.W3D"]:
        fails.append("original R11 missile references Al-Fahd texture")
    r11 = data[r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"].decode("latin1")
    if "Model                           = Irq_9P117" not in r11:
        fails.append("R11 model retargeted")
    if "Irq_AlFahd500" in r11 or "IRQ_AF500" in r11 or "Irq_AlFahd500P" in r11:
        fails.append("R11 INI references Al-Fahd visuals")

    w3d = art[PROJ_W3D_KEY]
    if hlod_name(w3d) != "Irq_AlFahd500M":
        fails.append(f"projectile HLod {hlod_name(w3d)!r}")
    texes = texture_names(w3d)
    if texes != {"Irq_AlFahd500P.tga"}:
        fails.append(f"projectile textures {texes}")
    if PROJ_TEX_KEY not in art:
        fails.append("missing Irq_AlFahd500P.tga")
    else:
        info = tga_info(art[PROJ_TEX_KEY])
        if info["type"] != 2 or info["bpp"] != 24 or info["alpha_bits"] != 0:
            fails.append(f"projectile TGA {info}")
        if info["width"] != 512 or info["height"] != 512:
            fails.append(f"projectile TGA size {info['width']}x{info['height']}")

    uvs = collect_uvs(w3d)
    body = [(u, v) for _name, u, v in uvs if v < 0.88]
    if len(body) < 20:
        fails.append(f"too few body UVs after remap {len(body)}")
    # Cylinder verts sit at the unwrap edges; triangles interpolate across the flag.
    us = [u for u, _v in body]
    vs = [v for _u, v in body]
    if min(us) > 0.08 or max(us) < 0.90 or min(vs) > 0.18 or max(vs) < 0.70:
        fails.append(f"body UV bbox misses flag sheet {min(us):.3f}..{max(us):.3f} {min(vs):.3f}..{max(vs):.3f}")

    changed_d = sorted(k for k in set(data) | set(src_data) if data.get(k) != src_data.get(k))
    allowed_d = {WEAPON_INI_KEY, OLD_WEAPON_KEY, UNIT_KEY}
    unexpected_d = [k for k in changed_d if k not in allowed_d]
    if unexpected_d:
        fails.append(f"unexpected DATA changes {unexpected_d[:8]}")

    changed_a = sorted(k for k in set(art) | set(src_art) if art.get(k) != src_art.get(k))
    allowed_a = {PROJ_W3D_KEY, PROJ_TEX_KEY, LAUNCHER_W3D_KEY, LAUNCHERD_W3D_KEY}
    unexpected_a = [k for k in changed_a if k not in allowed_a]
    if unexpected_a:
        fails.append(f"unexpected ART changes {unexpected_a[:8]}")
    return fails


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    expected = header
    for name, off, size in sorted(files, key=lambda x: x[1]):
        if off != expected:
            issues.append(f"overlap/gap {name}")
            break
        expected = off + size
    if expected != len(blob):
        issues.append("trailing gap/overflow")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def main() -> int:
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("live DATA baseline mismatch")
    if SRC_ART.stat().st_size != BASE_ART_SIZE or sha256_path(SRC_ART) != BASE_ART_SHA:
        raise SystemExit("live ART baseline mismatch")

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    block = weapon_block()
    data[WEAPON_INI_KEY] = append_weapon(data[WEAPON_INI_KEY], block)
    data.pop(OLD_WEAPON_KEY, None)
    data[UNIT_KEY] = to_crlf(UNIT_SRC.read_bytes())

    flag = Image.open(io.BytesIO(src_art[FLAG_KEY]))
    sheet = make_projectile_texture(flag)
    tga = make_tga24(sheet)
    art[PROJ_TEX_KEY] = tga
    art[PROJ_W3D_KEY] = uniquify_w3d_identity(
        walk_rebuild(src_art[PROJ_W3D_KEY]),
        [(b"IRQ_R11_M", b"IRQ_ALF_M")],
    )
    art[LAUNCHER_W3D_KEY] = uniquify_w3d_identity(
        src_art[LAUNCHER_W3D_KEY],
        [(b"IRQ_9P117D", b"IRQ_AF500D"), (b"IRQ_9P117", b"IRQ_AF500")],
    )
    art[LAUNCHERD_W3D_KEY] = uniquify_w3d_identity(
        src_art[LAUNCHERD_W3D_KEY],
        [(b"IRQ_9P117D", b"IRQ_AF500D"), (b"IRQ_9P117", b"IRQ_AF500")],
    )

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    preview = OUT / "alfahd_projectile_flag_preview.png"
    vis = sheet.convert("RGBA")
    dr = ImageDraw.Draw(vis)
    for mesh, u, v in collect_uvs(art[PROJ_W3D_KEY]):
        x, y = u * 512, v * 512
        col = (255, 0, 0, 255) if mesh == "BOOSTER" else (0, 255, 0, 255)
        dr.ellipse([x - 3, y - 3, x + 3, y + 3], outline=col, width=2)
    vis.save(preview)
    (OUT / "Irq_AlFahd500P.tga").write_bytes(tga)

    packed_data = build_big(data)
    packed_art = build_big(art)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(packed_data)
    out_art.write_bytes(packed_art)

    extracted_d = parse_big(packed_data)
    extracted_a = parse_big(packed_art)
    fails = validate(extracted_d, extracted_a, src_data, src_art)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed_data))
    fails.extend(f"ART {x}" for x in big_structure_ok(packed_art))

    data_sha = sha256_path(out_data)
    art_sha = sha256_path(out_art)
    tinfo = tga_info(extracted_a[PROJ_TEX_KEY])
    report = [
        "# Iraq_AlFahd500 fire + flying-missile flag",
        "",
        "Live s baselines: missile-factory-button DATA + missile-factory-tga24 ART.",
        "Missile Factory / missile_factory.tga / R11ScudB / GENERIC-MISSILES.dds untouched.",
        "",
        "## Root cause (fire)",
        "TheWeaponStore loads Data\\INI\\Weapon.ini and Data\\INI\\Weapon\\*.ini.",
        "Weapon_Iraq_AlFahd500 lived at Data\\INI\\Weapon_Iraq_AlFahd500.ini and was never parsed.",
        "PRIMARY was empty, so Command_FireMainWeapon (FIRE_WEAPON) stayed inactive.",
        "Fix: define Weapon_Iraq_AlFahd500 at the end of Weapon.ini; drop the unloaded file.",
        "",
        "## Root cause (flag)",
        "The flag was pasted onto unused atlas space; Irq_AlFahd500M body UVs missed it.",
        "Fix: dedicated Irq_AlFahd500P.tga (yellow + large IraqiFlag.dds) and remap projectile UVs.",
        "Launcher still uses Irq_AlFahd500M.tga. Flying model Irq_AlFahd500M.W3D uses Irq_AlFahd500P.tga.",
        "",
        "## Root cause (9P117 visual contamination)",
        "Original Irq_9P117.W3D / Irq_R11_M.W3D / textures were NOT byte-modified.",
        "Al-Fahd clones still registered globally as IRQ_9P117 / IRQ_R11_M, so ZH last-wins",
        "overwrote the original 9P117/R11 visuals at runtime with the black/yellow copies.",
        "Fix: rename Al-Fahd internals to IRQ_AF500 / IRQ_AF500D / IRQ_ALF_M and point",
        "Al-Fahd INI animations at Irq_AlFahd500.IRQ_AF500. Original 9P117 files left intact.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted_d)}",
        f"- ART size: {out_art.stat().st_size}",
        f"- ART SHA256: {art_sha}",
        f"- ART files: {len(extracted_a)}",
        f"- projectile TGA: type={tinfo['type']} bpp={tinfo['bpp']} alpha={tinfo['alpha_bits']} desc={tinfo['descriptor']} {tinfo['width']}x{tinfo['height']}",
        "",
        f"- DATA files vs live: {len(extracted_d)} (was {len(src_data)})",
        f"- ART files vs live: {len(extracted_a)} (was {len(src_art)})",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        report.append("")
        report.append("RUNTIME_TEST=NOT RUN")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static / packed last-wins)",
        "- Weapon_Iraq_AlFahd500 defined once, inside Weapon.ini",
        "- unloaded Data\\INI\\Weapon_Iraq_AlFahd500.ini removed",
        "- Iraq_AlFahd500 PRIMARY -> Weapon_Iraq_AlFahd500 -> Projectile_Iraq_AlFahd500 -> Irq_AlFahd500M -> Irq_AlFahd500P.tga",
        "- body UVs overlap the Iraqi flag region of the dedicated sheet",
        "- CommandSet unchanged; no slot > 18; factory intact",
        "- GENERIC-MISSILES.dds / IraqiFlag.dds / original 9P117 W3D+DDS / missile_factory.tga unchanged",
        "- Al-Fahd W3Ds use IRQ_AF500 / IRQ_AF500D / IRQ_ALF_M (no IRQ_9P117 / IRQ_R11_M)",
        "- Al-Fahd INI animations no longer reference Irq_9P117.W3D",
        "- old 8-missile project not restored",
        "",
        "RUNTIME_TEST=NOT RUN",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted_d)}\n"
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={out_art.stat().st_size}\n"
        f"ART_SHA256={art_sha}\n"
        f"ART_FILES={len(extracted_a)}\n"
        "WEAPON=Weapon_Iraq_AlFahd500 in Data\\INI\\Weapon.ini\n"
        "PROJECTILE_MODEL=Irq_AlFahd500M\n"
        "PROJECTILE_TEXTURE=Art\\Textures\\Irq_AlFahd500P.tga\n"
        "FLAG_SOURCE=Art\\Textures\\IraqiFlag.dds\n"
        "ALFAHD_HIER=IRQ_AF500 / IRQ_AF500D / IRQ_ALF_M\n"
        "9P117_HIER=IRQ_9P117 / IRQ_9P117D / IRQ_R11_M (frozen original files)\n"
        "BASELINE_DATA=s-missile-factory-button / fcc5cc49fc50e22bf89c5af40b7a1a1cde9035f83c212c90b6fbee2b8bd40288\n"
        "BASELINE_ART=s-missile-factory-tga24 / 77ea62f6e28ad356e7c6ac6f46f6c69b2b9736999a46d89988ee333db3610e33\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq Al-Fahd 500 fire + flying-missile flag + 9P117 visual freeze\n"
        "Place BOTH complete replacement BIG files in the game folder.\n"
        "  _SPEC_DATA_ONE.big  (weapon loaded from Weapon.ini; dedicated Al-Fahd anims)\n"
        "  _SPEC_ART_ONE.big   (dedicated Al-Fahd W3D identities + yellow flag projectile)\n"
        "Original Iraq_R11ScudB / 9P117 visuals are unchanged.\n"
        "Do not use a partial INI/W3D patch.\n",
        encoding="utf-8",
    )
    print("\n".join(report))
    print("PACK OK", data_sha, art_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
