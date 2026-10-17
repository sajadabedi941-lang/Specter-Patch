#!/usr/bin/env python3
"""Universal SPECTER missile-slot A command button, Iraq-mapped to Iraq_AlFahd500.

Live baselines:
  DATA  SPECTER_IRAQ_ALFAHD_LAUNCH_ANIM
        SHA256 b3ce190a555edc336006abfc763e1d44d11889233c79b72f159054d69b64d8f3
  ART   SPECTER_IRAQ_ALFAHD_FLAG_TEXT
        SHA256 b242265f79404e0d07f2f1f52599becb0eb73e28a741e9b79f0ba67a6078bb34

ZH CommandButton.Object is per-button, not per-faction. One global CB_MISSILE_A
can only bind one Object. This first implementation binds Iraq_AlFahd500.
Later countries need additional CommandButton IDs that share ButtonImage
specter_missile_a (do not duplicate the artwork).

Does not modify Iraq_AlFahd500 object/W3D/weapon, 9P117, or other factions.
"""
from __future__ import annotations

import hashlib
import io
import re
import shutil
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD_LAUNCH_ANIM/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD_FLAG_TEXT/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_A_BUTTON"
PNG_SRC = ROOT / "patch/Art/Textures/UI/specter_missile_a.png"

BASE_DATA_SHA = "b3ce190a555edc336006abfc763e1d44d11889233c79b72f159054d69b64d8f3"
BASE_DATA_SIZE = 366368717
BASE_ART_SHA = "b242265f79404e0d07f2f1f52599becb0eb73e28a741e9b79f0ba67a6078bb34"
BASE_ART_SIZE = 1266477100

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CSF_KEY = r"Data\English\generals.csf"
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\Specter_MissileSlot_Images.INI"
TGA_KEY = r"Art\Textures\specter_missile_a.tga"
UNIT_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
PROJ_TEX = r"Art\Textures\Irq_AlFahd500P.tga"
FACTORY_TGA = r"Art\Textures\missile_factory.tga"
GENERIC = r"Art\Textures\GENERIC-MISSILES.dds"
TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")

OLD_SET = (
    "CommandSet Iraq_AlFahdMissileFactoryCommandSet\r\n"
    "  1  = Command_ConstructIraq_AlFahd500\r\n"
    "  13 = Command_SetRallyPoint\r\n"
    "  14 = Command_Sell\r\n"
    "End"
)
NEW_SET = (
    "CommandSet Iraq_AlFahdMissileFactoryCommandSet\r\n"
    "  1  = CB_MISSILE_A\r\n"
    "  13 = Command_SetRallyPoint\r\n"
    "  14 = Command_Sell\r\n"
    "End"
)

NEW_BUTTON = (
    "\r\n"
    "; SPECTER universal missile slot A. ButtonImage is shared.\r\n"
    "; ZH binds Object on the CommandButton, so this first ID maps Iraq_AlFahd500.\r\n"
    "; Other countries later: extra CommandButton IDs, same ButtonImage specter_missile_a.\r\n"
    "CommandButton CB_MISSILE_A\r\n"
    "  Command       = UNIT_BUILD\r\n"
    "  Object        = Iraq_AlFahd500\r\n"
    "  TextLabel     = CONTROLBAR:SpecterMissileA\r\n"
    "  ButtonImage   = specter_missile_a\r\n"
    "  ButtonBorderType = BUILD\r\n"
    "  DescriptLabel = CONTROLBAR:ToolTipSpecterMissileA\r\n"
    "End\r\n"
)

MAPPED_INI = (
    "; SPECTER universal missile-slot cameos. Not country-specific.\r\n"
    "; Slot A artwork is reused by every faction CommandButton that shares\r\n"
    "; ButtonImage = specter_missile_a.\r\n"
    "\r\n"
    "MappedImage specter_missile_a\r\n"
    "  Texture = specter_missile_a.tga\r\n"
    "  TextureWidth = 128\r\n"
    "  TextureHeight = 128\r\n"
    "  Coords = Left:0 Top:0 Right:128 Bottom:128\r\n"
    "  Status = NONE\r\n"
    "End\r\n"
)

CSF_LABELS = {
    "CONTROLBAR:SpecterMissileA": "Missile A",
    "CONTROLBAR:ToolTipSpecterMissileA": "Strategic missile slot A.",
}

OTHER_FACTION_MARKERS = [
    b"CommandSet USA_",
    b"CommandSet Russia_",
    b"CommandSet China_",
    b"CommandSet Iran_",
    b"CommandSet Turkey_",
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


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_missile_a_image() -> Image.Image:
    """128x128 universal slot-A cameo. Persian identity is painted on the bitmap
    because ZH's CSF UI font typically lacks Arabic glyphs."""
    s = 256
    im = Image.new("RGB", (s, s), (16, 18, 22))
    px = im.load()
    for y in range(s):
        col = lerp((22, 25, 30), (12, 14, 17), y / (s - 1))
        for x in range(s):
            cx, cy = (x - s / 2) / (s / 2), (y - s / 2) / (s / 2)
            v = min(1.0, (cx * cx + cy * cy) * 0.35)
            px[x, y] = lerp(col, (8, 9, 11), v)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, s - 1, s - 1], outline=(6, 7, 8), width=5)
    d.line([(6, 6), (s - 7, 6)], fill=(92, 98, 108), width=3)
    d.line([(6, 6), (6, s - 7)], fill=(92, 98, 108), width=3)
    d.line([(s - 7, 6), (s - 7, s - 7)], fill=(10, 11, 13), width=3)
    d.line([(6, s - 7), (s - 7, s - 7)], fill=(10, 11, 13), width=3)
    d.rectangle([10, 10, s - 11, s - 11], outline=(58, 64, 72), width=2)
    d.rectangle([13, 13, s - 14, s - 14], outline=(28, 32, 38), width=2)
    d.rectangle([18, 18, s - 19, s - 19], fill=(20, 24, 30), outline=(40, 46, 54))
    for i in range(4):
        d.line([(28, 40 + i * 36), (s - 29, 40 + i * 36)], fill=(32, 38, 46), width=1)
    d.line([(s // 2, 28), (s // 2, 170)], fill=(32, 38, 46), width=1)

    cx = s // 2
    body = [
        (cx - 16, 62),
        (cx - 13, 46),
        (cx, 28),
        (cx + 13, 46),
        (cx + 16, 62),
        (cx + 18, 150),
        (cx + 11, 168),
        (cx - 11, 168),
        (cx - 18, 150),
    ]
    d.polygon(body, fill=(168, 176, 186), outline=(210, 216, 224))
    d.polygon([(cx - 14, 50), (cx - 4, 38), (cx - 4, 160), (cx - 16, 148)], fill=(210, 218, 226))
    d.polygon([(cx + 6, 46), (cx + 16, 62), (cx + 18, 150), (cx + 9, 164)], fill=(90, 98, 108))
    d.polygon(
        [(cx - 13, 46), (cx, 28), (cx + 13, 46), (cx + 8, 56), (cx, 42), (cx - 8, 56)],
        fill=(200, 206, 214),
    )
    for y in (78, 102, 126):
        d.line([(cx - 15, y), (cx + 15, y)], fill=(70, 76, 84), width=1)
    d.rectangle([cx - 15, 66, cx + 15, 76], fill=(48, 52, 58), outline=(24, 26, 30))
    d.polygon([(cx - 18, 148), (cx - 32, 174), (cx - 16, 168)], fill=(120, 128, 138), outline=(40, 44, 50))
    d.polygon([(cx + 18, 148), (cx + 32, 174), (cx + 16, 168)], fill=(80, 86, 94), outline=(40, 44, 50))
    d.polygon([(cx - 7, 150), (cx, 174), (cx + 7, 150)], fill=(100, 108, 118))
    d.rectangle([cx - 9, 168, cx + 9, 180], fill=(36, 38, 42), outline=(12, 12, 14))
    d.rectangle([cx - 5, 180, cx + 5, 186], fill=(70, 50, 30))
    d.rectangle([22, 22, 27, 50], fill=(196, 154, 58))
    d.rectangle([s - 28, 22, s - 23, 50], fill=(196, 154, 58))

    d.rounded_rectangle([20, 196, s - 21, 244], radius=8, fill=(10, 12, 15), outline=(196, 154, 58), width=3)
    d.rounded_rectangle([24, 200, s - 25, 240], radius=5, fill=(16, 18, 22), outline=(60, 52, 32), width=1)
    latin = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    arab = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf", 32)
    d.text((46, 220), "A", font=latin, fill=(232, 214, 150), anchor="mm", stroke_width=2, stroke_fill=(8, 8, 8))
    d.line([(64, 208), (64, 232)], fill=(90, 74, 36), width=2)
    d.text((150, 218), "موشک", font=arab, fill=(236, 228, 200), anchor="mm", stroke_width=1, stroke_fill=(8, 8, 8))

    out = im.resize((128, 128), Image.Resampling.LANCZOS)
    out = ImageEnhance.Contrast(out).enhance(1.08)
    out = out.filter(ImageFilter.UnsharpMask(radius=1, percent=80, threshold=2))
    return out.convert("RGB")


def make_tga24(im: Image.Image) -> bytes:
    rgb = im.convert("RGB")
    if rgb.size != (128, 128):
        rgb = rgb.resize((128, 128), Image.Resampling.LANCZOS)
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
    }


def csf_append(csf: bytes, labels: dict[str, str]) -> bytes:
    if csf[:4] != b" FSC":
        raise SystemExit(f"unexpected CSF magic {csf[:4]!r}")
    _magic, ver, nlab, nstr, unused, lang = struct.unpack_from("<4sIIIII", csf, 0)
    existing = set()
    pos = 24
    while pos < len(csf):
        if csf[pos : pos + 4] != b" LBL":
            break
        pos += 4
        cnt, nlen = struct.unpack_from("<II", csf, pos)
        pos += 8
        name = csf[pos : pos + nlen].decode("latin1")
        pos += nlen
        existing.add(name)
        for _ in range(cnt):
            smag = csf[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4 + slen * 2
            if smag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4 + elen
    extra = bytearray()
    added = 0
    for key, value in labels.items():
        if key in existing:
            continue
        encoded = value.encode("utf-16le")
        xored = bytes(x ^ 0xFF for x in encoded)
        extra += b" LBL"
        extra += struct.pack("<II", 1, len(key))
        extra += key.encode("latin1")
        extra += b" RTS"
        extra += struct.pack("<I", len(value))
        extra += xored
        added += 1
    if not added:
        return csf
    out = bytearray(csf)
    struct.pack_into("<I", out, 8, nlab + added)
    struct.pack_into("<I", out, 12, nstr + added)
    out += extra
    return bytes(out)


def command_block(text: str, kind: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text)
    return m.group(0) if m else None


def slot_map(block: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


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


def validate(
    data: dict[str, bytes],
    art: dict[str, bytes],
    src_data: dict[str, bytes],
    src_art: dict[str, bytes],
) -> list[str]:
    fails: list[str] = []
    all_ini = b"".join(v for k, v in data.items() if k.lower().endswith(".ini"))

    if all_ini.count(b"CommandButton CB_MISSILE_A") != 1:
        fails.append(f"CB_MISSILE_A def count {all_ini.count(b'CommandButton CB_MISSILE_A')}")
    if all_ini.count(b"MappedImage specter_missile_a") != 1:
        fails.append("MappedImage specter_missile_a count")
    btn = command_block(data[CB_KEY].decode("latin1"), "CommandButton", "CB_MISSILE_A") or ""
    if "Object        = Iraq_AlFahd500" not in btn:
        fails.append("CB_MISSILE_A Object not Iraq_AlFahd500")
    if "ButtonImage   = specter_missile_a" not in btn:
        fails.append("CB_MISSILE_A ButtonImage")
    if "Command       = UNIT_BUILD" not in btn:
        fails.append("CB_MISSILE_A command")
    if "Al-Fahd" in btn or "AlFahd500" in btn.split("Object", 1)[0]:
        fails.append("Al-Fahd name leaked onto button identity fields")

    fac = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet") or ""
    slots = slot_map(fac)
    if slots.get(1) != "CB_MISSILE_A":
        fails.append(f"factory slot 1 {slots.get(1)}")
    if "Command_ConstructIraq_AlFahd500" in fac:
        fails.append("factory set still uses old Al-Fahd button")

    # leftover old button may remain defined, but factory must not show irq_9p117 for slot A
    old = command_block(data[CB_KEY].decode("latin1"), "CommandButton", "Command_ConstructIraq_AlFahd500") or ""
    if old and "ButtonImage   = irq_9p117" not in old:
        fails.append("unexpected mutation of leftover Al-Fahd construct button")

    if data[UNIT_KEY] != src_data[UNIT_KEY]:
        fails.append("Iraq_AlFahd500 object mutated")
    if data[FACTORY_KEY] != src_data[FACTORY_KEY]:
        fails.append("factory object mutated")
    if data[WEAPON_KEY] != src_data[WEAPON_KEY]:
        fails.append("Weapon.ini mutated")
    if data[R11_KEY] != src_data[R11_KEY]:
        fails.append("9P117 mutated")
    if data[FACTORY_KEY].decode("latin1").count("CommandSet       = Iraq_AlFahdMissileFactoryCommandSet") != 1:
        fails.append("factory commandset retargeted")

    zzzz_hits = [
        k
        for k, v in data.items()
        if "zzzz" in k.lower() and (b"CB_MISSILE_A" in v or b"Iraq_AlFahdMissileFactoryCommandSet" in v)
    ]
    if zzzz_hits:
        fails.append(f"ZZZZ override of missile A {zzzz_hits[:4]}")

    csf = data[CSF_KEY]
    if b"CONTROLBAR:SpecterMissileA" not in csf:
        fails.append("CSF missing SpecterMissileA")
    if b"AL-Fahd 500" not in bytes(x ^ 0xFF for x in b"AL-Fahd 500".decode().encode("utf-16le")):
        pass
    # original Al-Fahd CSF labels still present
    if b"CONTROLBAR:ConstructIraq_AlFahd500" not in csf:
        fails.append("original Al-Fahd CSF label lost")

    if TGA_KEY not in art:
        fails.append("missing specter_missile_a.tga")
    else:
        info = tga_info(art[TGA_KEY])
        if info["type"] != 2 or info["bpp"] != 24 or info["alpha_bits"] != 0:
            fails.append(f"cameo TGA profile {info}")
        if info["width"] != 128 or info["height"] != 128:
            fails.append(f"cameo size {info['width']}x{info['height']}")
        decoded = Image.open(io.BytesIO(art[TGA_KEY])).convert("RGB")
        # identity plate should have amber-ish pixels and dark well
        amber = dark = 0
        px = decoded.load()
        for y in range(96, 124):
            for x in range(10, 118):
                r, g, b = px[x, y]
                if r > 150 and g > 100 and b < 100:
                    amber += 1
                if r < 40 and g < 40 and b < 40:
                    dark += 1
        if amber < 20 or dark < 40:
            fails.append(f"cameo plate colors amber={amber} dark={dark}")

    if art[PROJ_TEX] != src_art[PROJ_TEX]:
        fails.append("Al-Fahd missile skin mutated")
    if art[FACTORY_TGA] != src_art[FACTORY_TGA]:
        fails.append("missile_factory.tga mutated")
    if art[GENERIC] != src_art[GENERIC]:
        fails.append("GENERIC-MISSILES mutated")
    for donor in ["Irq_9P117", "Irq_9P117D", "Irq_AlFahd500", "Irq_AlFahd500M"]:
        k = f"Art\\W3D\\{donor}.W3D"
        if art[k] != src_art[k]:
            fails.append(f"W3D mutated {donor}")

    r11_btn = command_block(data[CB_KEY].decode("latin1"), "CommandButton", "Command_ConstructIraq_R11ScudB") or ""
    if "ButtonImage   = irq_9p117" not in r11_btn and "ButtonImage      = irq_9p117" not in r11_btn:
        fails.append("R11 construct button image changed")

    vt = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_VT72BCommandSet") or ""
    if slot_map(vt).get(14) != "Command_ConstructIraq_AlFahdMissileFactory":
        fails.append("VT72B factory button lost")

    changed_d = sorted(k for k in set(data) | set(src_data) if data.get(k) != src_data.get(k))
    allowed_d = {CB_KEY, CS_KEY, CSF_KEY, MAPPED_KEY}
    unexpected_d = [k for k in changed_d if k not in allowed_d]
    if unexpected_d:
        fails.append(f"unexpected DATA changes {unexpected_d[:8]}")
    changed_a = sorted(k for k in set(art) | set(src_art) if art.get(k) != src_art.get(k))
    if changed_a != [TGA_KEY]:
        fails.append(f"unexpected ART changes {changed_a[:8]}")
    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("live DATA baseline mismatch")
    if SRC_ART.stat().st_size != BASE_ART_SIZE or sha256_path(SRC_ART) != BASE_ART_SHA:
        raise SystemExit("live ART baseline mismatch")

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    sheet = make_missile_a_image()
    PNG_SRC.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PNG_SRC)
    tga = make_tga24(sheet)
    art[TGA_KEY] = tga
    data[MAPPED_KEY] = to_crlf(MAPPED_INI)

    cb = data[CB_KEY]
    if b"CommandButton CB_MISSILE_A" in cb:
        raise SystemExit("CB_MISSILE_A already present")
    data[CB_KEY] = cb + NEW_BUTTON.encode("latin1")

    cs = data[CS_KEY].decode("latin1")
    if OLD_SET not in cs:
        raise SystemExit("factory CommandSet block not found")
    data[CS_KEY] = cs.replace(OLD_SET, NEW_SET, 1).encode("latin1")
    data[CSF_KEY] = csf_append(data[CSF_KEY], CSF_LABELS)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT / "specter_missile_a.png")
    (OUT / "specter_missile_a.tga").write_bytes(tga)

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
    info = tga_info(extracted_a[TGA_KEY])
    report = [
        "# SPECTER universal missile slot A (Iraq maps to Iraq_AlFahd500)",
        "",
        "ZH CommandButton.Object is per-button. CB_MISSILE_A binds Iraq_AlFahd500.",
        "Artwork specter_missile_a is universal (no country / no Al-Fahd name).",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted_d)}",
        f"- ART size: {out_art.stat().st_size}",
        f"- ART SHA256: {art_sha}",
        f"- ART files: {len(extracted_a)}",
        f"- TGA: type={info['type']} bpp={info['bpp']} alpha={info['alpha_bits']} {info['width']}x{info['height']}",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        report.append("RUNTIME_TEST=NOT RUN")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static)",
        "- CommandButton CB_MISSILE_A -> UNIT_BUILD Iraq_AlFahd500, ButtonImage specter_missile_a",
        "- Iraq_AlFahdMissileFactoryCommandSet slot 1 = CB_MISSILE_A",
        "- MappedImage specter_missile_a -> specter_missile_a.tga 128x128 24-bit",
        "- Iraq_AlFahd500 object / weapon / flag ART / 9P117 / factory object unchanged",
        "- no ZZZZ override of CB_MISSILE_A",
        "- R11 still uses irq_9p117",
        "",
        "RUNTIME_TEST=NOT RUN",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=YES\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted_d)}\n"
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={out_art.stat().st_size}\n"
        f"ART_SHA256={art_sha}\n"
        f"ART_FILES={len(extracted_a)}\n"
        "COMMANDBUTTON=CB_MISSILE_A\n"
        "BUTTONIMAGE=specter_missile_a\n"
        "TEXTURE=Art\\Textures\\specter_missile_a.tga\n"
        "COMMANDSET=Iraq_AlFahdMissileFactoryCommandSet slot 1\n"
        "MAPPING=موشک A -> Iraq_AlFahd500\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER universal missile slot A\n"
        "Place BOTH complete replacement BIG files in the game folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "  _SPEC_ART_ONE.big\n"
        "Iraq Missile Factory slot A (CB_MISSILE_A) builds Iraq_AlFahd500.\n"
        "Visible identity is موشک A. Do not use a partial INI/TGA patch.\n",
        encoding="utf-8",
    )
    print("\n".join(report))
    print("PACK OK", data_sha, art_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
