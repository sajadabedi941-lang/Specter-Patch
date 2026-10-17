#!/usr/bin/env python3
"""Fix Iraq missile factory build-queue icon and prepare universal slots A-L.

Live baseline: SPECTER_IRAQ_MISSILE_A_BUTTON (order button already uses
specter_missile_a). The production queue still used Iraq_AlFahd500's
Object ButtonImage/SelectPortrait = irq_9p117. ZH displays the *Object*
ButtonImage in the factory build queue / countdown, not the CommandButton.

This pack:
  - retargets ONLY those two Iraq_AlFahd500 UI fields to specter_missile_a
  - defines CB_MISSILE_B..L with the same universal cameo system
  - does NOT wire B-L into the factory CommandSet (UNIT_BUILD needs a real Object)
  - does NOT change Al-Fahd W3D, flag skin, animation, weapon, 9P117, or irq_9p117
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
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_A_BUTTON/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_A_BUTTON/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_QUEUE_SLOTS"
PNG_DIR = ROOT / "patch/Art/Textures/UI"
MAPPED_SRC = ROOT / "patch/Data/INI/MappedImages/HandCreated/Specter_MissileSlot_Images.INI"
SLOTS_SRC = ROOT / "patch/Data/INI/CommandButton_SpecterMissileSlots.ini"
UNIT_SRC = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlFahd500.ini"

BASE_DATA_SHA = "5ee8034acadfaf38545db90486334e460890aa4c7b89ed1babdd615c658692bf"
BASE_DATA_SIZE = 366369779
BASE_ART_SHA = "1fa2de6da5eebe152750c223c9c33a93a67f92de951ce6eaff07a47cb9551da4"
BASE_ART_SIZE = 1266526339

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CSF_KEY = r"Data\English\generals.csf"
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\Specter_MissileSlot_Images.INI"
UNIT_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
PROJ_TEX = r"Art\Textures\Irq_AlFahd500P.tga"
FACTORY_TGA = r"Art\Textures\missile_factory.tga"
GENERIC = r"Art\Textures\GENERIC-MISSILES.dds"
IRQ_TGA = r"Art\Textures\irq_9p117.tga"
TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")

SLOTS = list("ABCDEFGHIJKL")
OLD_PORTRAIT = (
    "  SelectPortrait         = irq_9p117\r\n"
    "  ButtonImage            = irq_9p117\r\n"
)
NEW_PORTRAIT = (
    "  ; Queue/countdown/selected portrait follow Object ButtonImage, not CommandButton.\r\n"
    "  SelectPortrait         = specter_missile_a\r\n"
    "  ButtonImage            = specter_missile_a\r\n"
)

OLD_SET = (
    "CommandSet Iraq_AlFahdMissileFactoryCommandSet\r\n"
    "  1  = CB_MISSILE_A\r\n"
    "  13 = Command_SetRallyPoint\r\n"
    "  14 = Command_Sell\r\n"
    "End"
)
NEW_SET = (
    "CommandSet Iraq_AlFahdMissileFactoryCommandSet\r\n"
    "  1  = CB_MISSILE_A\r\n"
    "  ; 2-12 reserved for CB_MISSILE_B .. CB_MISSILE_L once each has a real Object.\r\n"
    "  ; UNIT_BUILD with a null Object is unsafe to show on the factory bar.\r\n"
    "  13 = Command_SetRallyPoint\r\n"
    "  14 = Command_Sell\r\n"
    "End"
)

CSF_LABELS = {}
for ch in SLOTS:
    CSF_LABELS[f"CONTROLBAR:SpecterMissile{ch}"] = f"Missile {ch}"
    CSF_LABELS[f"CONTROLBAR:ToolTipSpecterMissile{ch}"] = f"Strategic missile slot {ch}."


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


def make_missile_slot_image(letter: str) -> Image.Image:
    """128x128 universal slot cameo. Same silhouette; only the plate letter changes."""
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
    d.text((46, 220), letter, font=latin, fill=(232, 214, 150), anchor="mm", stroke_width=2, stroke_fill=(8, 8, 8))
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


def buttons_b_through_l() -> str:
    text = SLOTS_SRC.read_text(encoding="utf-8")
    parts = []
    for ch in SLOTS[1:]:
        block = command_block(text, "CommandButton", f"CB_MISSILE_{ch}")
        if not block:
            raise SystemExit(f"missing CB_MISSILE_{ch} in source")
        if re.search(r"^\s*Object\s*=", block, re.M):
            raise SystemExit(f"CB_MISSILE_{ch} must not bind an Object yet")
        parts.append(block.replace("\r\n", "\n").strip())
    return "\r\n\r\n" + "\r\n\r\n".join(parts) + "\r\n"


def unit_only_portrait_changed(new: bytes, old: bytes) -> list[str]:
    fails = []
    n = new.decode("latin1").replace("\r\n", "\n")
    o = old.decode("latin1").replace("\r\n", "\n")
    n_lines = n.splitlines()
    o_lines = o.splitlines()
    # allow inserting comment lines next to portraits
    def stripped(lines):
        keep = []
        for line in lines:
            if line.strip().startswith(";") and ("Queue" in line or "countdown" in line or "SelectPortrait" in line):
                continue
            keep.append(line)
        return keep

    ns, os_ = stripped(n_lines), stripped(o_lines)
    if len(ns) != len(os_):
        fails.append(f"Al-Fahd line count {len(ns)} vs {len(os_)}")
        return fails
    diffs = []
    for i, (a, b) in enumerate(zip(ns, os_), 1):
        if a != b:
            diffs.append((i, a, b))
    allowed = {
        ("  SelectPortrait         = specter_missile_a", "  SelectPortrait         = irq_9p117"),
        ("  ButtonImage            = specter_missile_a", "  ButtonImage            = irq_9p117"),
    }
    for i, a, b in diffs:
        if (a, b) not in allowed:
            fails.append(f"unexpected Al-Fahd line {i}: {b!r} -> {a!r}")
    if not any(a.startswith("  SelectPortrait") and "specter_missile_a" in a for a, _b in [(x[1], x[2]) for x in diffs]):
        if "SelectPortrait         = specter_missile_a" not in n:
            fails.append("SelectPortrait not retargeted")
    return fails


def validate(
    data: dict[str, bytes],
    art: dict[str, bytes],
    src_data: dict[str, bytes],
    src_art: dict[str, bytes],
) -> list[str]:
    fails: list[str] = []
    all_ini = b"".join(v for k, v in data.items() if k.lower().endswith(".ini"))

    for ch in SLOTS:
        n = all_ini.count(f"CommandButton CB_MISSILE_{ch}".encode("ascii"))
        if n != 1:
            fails.append(f"CB_MISSILE_{ch} def count {n}")
        n = all_ini.count(f"MappedImage specter_missile_{ch.lower()}".encode("ascii"))
        if n != 1:
            fails.append(f"MappedImage specter_missile_{ch.lower()} count {n}")

    btn_a = command_block(data[CB_KEY].decode("latin1"), "CommandButton", "CB_MISSILE_A") or ""
    if "Object        = Iraq_AlFahd500" not in btn_a:
        fails.append("CB_MISSILE_A Object not Iraq_AlFahd500")
    if "ButtonImage   = specter_missile_a" not in btn_a:
        fails.append("CB_MISSILE_A ButtonImage")
    if "Command       = UNIT_BUILD" not in btn_a:
        fails.append("CB_MISSILE_A command")

    for ch in SLOTS[1:]:
        btn = command_block(data[CB_KEY].decode("latin1"), "CommandButton", f"CB_MISSILE_{ch}") or ""
        if re.search(r"^\s*Object\s*=", btn, re.M):
            fails.append(f"CB_MISSILE_{ch} unexpectedly binds Object")
        if f"ButtonImage   = specter_missile_{ch.lower()}" not in btn:
            fails.append(f"CB_MISSILE_{ch} ButtonImage")
        if "Iraq_AlFahd500" in btn:
            fails.append(f"CB_MISSILE_{ch} points at Iraq_AlFahd500")

    fac = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet") or ""
    slots = slot_map(fac)
    if slots.get(1) != "CB_MISSILE_A":
        fails.append(f"factory slot 1 {slots.get(1)}")
    if slots.get(13) != "Command_SetRallyPoint":
        fails.append("rally slot lost")
    if slots.get(14) != "Command_Sell":
        fails.append("sell slot lost")
    for i in range(2, 13):
        if i in slots:
            fails.append(f"factory slot {i} wired to {slots[i]} without an Object")
    if any(n > 18 for n in slots):
        fails.append(f"CommandSet slot > 18: {sorted(slots)}")

    fails.extend(unit_only_portrait_changed(data[UNIT_KEY], src_data[UNIT_KEY]))
    unit = data[UNIT_KEY].decode("latin1")
    if "SelectPortrait         = specter_missile_a" not in unit:
        fails.append("queue SelectPortrait still not specter_missile_a")
    if "ButtonImage            = specter_missile_a" not in unit:
        fails.append("queue ButtonImage still not specter_missile_a")
    if "SelectPortrait         = irq_9p117" in unit or re.search(
        r"^\s*ButtonImage\s*=\s*irq_9p117", unit, re.M
    ):
        fails.append("Al-Fahd still references irq_9p117 for UI cameo")
    for token in ["IRQ_AF500.IRQ_AF500", "UnpackTime = 6555", "BuildCost       = 3000", "BuildTime       = 17.0"]:
        if token not in unit:
            fails.append(f"Al-Fahd lost {token}")

    if data[FACTORY_KEY] != src_data[FACTORY_KEY]:
        fails.append("factory object mutated")
    if data[WEAPON_KEY] != src_data[WEAPON_KEY]:
        fails.append("Weapon.ini mutated")
    if data[R11_KEY] != src_data[R11_KEY]:
        fails.append("9P117 mutated")
    r11 = data[R11_KEY].decode("latin1")
    if "SelectPortrait         = irq_9p117" not in r11 or "ButtonImage            = irq_9p117" not in r11:
        fails.append("9P117 cameo retargeted")

    zzzz_hits = [
        k
        for k, v in data.items()
        if "zzzz" in k.lower()
        and any(f"CB_MISSILE_{ch}".encode("ascii") in v for ch in SLOTS)
    ]
    if zzzz_hits:
        fails.append(f"ZZZZ override of missile slots {zzzz_hits[:4]}")

    csf = data[CSF_KEY]
    for ch in SLOTS:
        if f"CONTROLBAR:SpecterMissile{ch}".encode("ascii") not in csf:
            fails.append(f"CSF missing SpecterMissile{ch}")
    if b"CONTROLBAR:ConstructIraq_AlFahd500" not in csf:
        fails.append("original Al-Fahd CSF label lost")

    if art[r"Art\Textures\specter_missile_a.tga"] != src_art[r"Art\Textures\specter_missile_a.tga"]:
        fails.append("specter_missile_a.tga mutated (must keep existing slot-A art)")
    for ch in SLOTS:
        key = rf"Art\Textures\specter_missile_{ch.lower()}.tga"
        if key not in art:
            fails.append(f"missing {key}")
            continue
        info = tga_info(art[key])
        if info["type"] != 2 or info["bpp"] != 24 or info["alpha_bits"] != 0:
            fails.append(f"{key} profile {info}")
        if info["width"] != 128 or info["height"] != 128:
            fails.append(f"{key} size {info['width']}x{info['height']}")

    irq_mapped = [k for k, v in data.items() if b"MappedImage irq_9p117" in v]
    if not irq_mapped:
        fails.append("irq_9p117 MappedImage missing")
    if IRQ_TGA in art and IRQ_TGA in src_art and art[IRQ_TGA] != src_art[IRQ_TGA]:
        fails.append("irq_9p117.tga mutated")
    if art[PROJ_TEX] != src_art[PROJ_TEX]:
        fails.append("Al-Fahd missile skin mutated")
    if art[FACTORY_TGA] != src_art[FACTORY_TGA]:
        fails.append("missile_factory.tga mutated")
    if art[GENERIC] != src_art[GENERIC]:
        fails.append("GENERIC-MISSILES mutated")
    for donor in ["Irq_9P117", "Irq_9P117D", "Irq_AlFahd500", "Irq_AlFahd500M", "Irq_AlFahd500D"]:
        k = f"Art\\W3D\\{donor}.W3D"
        if k in src_art and art.get(k) != src_art[k]:
            fails.append(f"W3D mutated {donor}")

    r11_btn = command_block(data[CB_KEY].decode("latin1"), "CommandButton", "Command_ConstructIraq_R11ScudB") or ""
    if "irq_9p117" not in r11_btn:
        fails.append("R11 construct button image changed")

    vt = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_VT72BCommandSet") or ""
    if slot_map(vt).get(14) != "Command_ConstructIraq_AlFahdMissileFactory":
        fails.append("VT72B factory button lost")

    changed_d = sorted(k for k in set(data) | set(src_data) if data.get(k) != src_data.get(k))
    allowed_d = {CB_KEY, CS_KEY, CSF_KEY, MAPPED_KEY, UNIT_KEY}
    unexpected_d = [k for k in changed_d if k not in allowed_d]
    if unexpected_d:
        fails.append(f"unexpected DATA changes {unexpected_d[:8]}")
    changed_a = sorted(k for k in set(art) | set(src_art) if art.get(k) != src_art.get(k))
    allowed_a = {rf"Art\Textures\specter_missile_{ch.lower()}.tga" for ch in SLOTS[1:]}
    unexpected_a = [k for k in changed_a if k not in allowed_a]
    if unexpected_a:
        fails.append(f"unexpected ART changes {unexpected_a[:8]}")
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

    unit = data[UNIT_KEY].decode("latin1")
    if OLD_PORTRAIT not in unit:
        raise SystemExit("Al-Fahd portrait block not found")
    data[UNIT_KEY] = unit.replace(OLD_PORTRAIT, NEW_PORTRAIT, 1).encode("latin1")
    # keep workspace object file aligned
    ws = UNIT_SRC.read_text(encoding="latin1")
    if "SelectPortrait         = specter_missile_a" not in ws:
        raise SystemExit("workspace Iraq_AlFahd500.ini portraits not updated")

    data[MAPPED_KEY] = to_crlf(MAPPED_SRC.read_text(encoding="latin1"))

    cb = data[CB_KEY]
    if b"CommandButton CB_MISSILE_B" in cb:
        raise SystemExit("CB_MISSILE_B already present")
    data[CB_KEY] = cb + buttons_b_through_l().encode("latin1")

    cs = data[CS_KEY].decode("latin1")
    if OLD_SET not in cs:
        raise SystemExit("factory CommandSet block not found")
    data[CS_KEY] = cs.replace(OLD_SET, NEW_SET, 1).encode("latin1")
    data[CSF_KEY] = csf_append(data[CSF_KEY], CSF_LABELS)

    PNG_DIR.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    # Keep packed slot-A TGA byte-identical; generate B-L with the same design.
    (OUT / "specter_missile_a.tga").write_bytes(art[r"Art\Textures\specter_missile_a.tga"])
    for ch in SLOTS[1:]:
        sheet = make_missile_slot_image(ch)
        png_path = PNG_DIR / f"specter_missile_{ch.lower()}.png"
        sheet.save(png_path)
        tga = make_tga24(sheet)
        art[rf"Art\Textures\specter_missile_{ch.lower()}.tga"] = tga
        sheet.save(OUT / f"specter_missile_{ch.lower()}.png")
        (OUT / f"specter_missile_{ch.lower()}.tga").write_bytes(tga)

    packed_data = build_big(data)
    packed_art = build_big(art)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(packed_data)
    out_art.write_bytes(packed_art)

    extracted_d = parse_big(packed_data)
    extracted_a = parse_big(packed_art)
    stage = OUT / "LAST_WINS_EXTRACT"
    if stage.exists():
        shutil.rmtree(stage)
    (stage / "DATA").mkdir(parents=True)
    (stage / "ART").mkdir(parents=True)
    for rel in [CB_KEY, CS_KEY, UNIT_KEY, MAPPED_KEY, FACTORY_KEY, R11_KEY]:
        p = stage / "DATA" / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted_d[rel])
    for ch in SLOTS:
        rel = rf"Art\Textures\specter_missile_{ch.lower()}.tga"
        p = stage / "ART" / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted_a[rel])

    fails = validate(extracted_d, extracted_a, src_data, src_art)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed_data))
    fails.extend(f"ART {x}" for x in big_structure_ok(packed_art))

    # last-wins extract must match packed map
    ext_unit = (stage / "DATA" / UNIT_KEY.replace("\\", "/")).read_bytes()
    if b"ButtonImage            = specter_missile_a" not in ext_unit:
        fails.append("last-wins extract missing queue ButtonImage")
    if b"ButtonImage            = irq_9p117" in ext_unit:
        fails.append("last-wins extract still has irq_9p117 on Al-Fahd")

    data_sha = sha256_path(out_data)
    art_sha = sha256_path(out_art)
    info_a = tga_info(extracted_a[r"Art\Textures\specter_missile_a.tga"])
    report = [
        "# SPECTER missile factory queue icon + universal slots A-L",
        "",
        "QUEUE MECHANISM: Object Iraq_AlFahd500 ButtonImage / SelectPortrait",
        "OLD QUEUE ICON: irq_9p117 (9P117 Scud cameo inherited on Al-Fahd)",
        "NEW QUEUE ICON: specter_missile_a (same as CB_MISSILE_A order button)",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted_d)}",
        f"- ART size: {out_art.stat().st_size}",
        f"- ART SHA256: {art_sha}",
        f"- ART files: {len(extracted_a)}",
        f"- Slot A TGA: type={info_a['type']} bpp={info_a['bpp']} alpha={info_a['alpha_bits']} {info_a['width']}x{info_a['height']}",
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
        "- Order button CB_MISSILE_A ButtonImage = specter_missile_a",
        "- Queue/countdown Iraq_AlFahd500 ButtonImage = specter_missile_a",
        "- Queue/countdown Iraq_AlFahd500 SelectPortrait = specter_missile_a",
        "- CB_MISSILE_A Object = Iraq_AlFahd500",
        "- CB_MISSILE_B..L defined, no Object, not on factory CommandSet",
        "- Iraq_AlFahdMissileFactoryCommandSet 1=A, 13=Rally, 14=Sell",
        "- 9P117 / irq_9p117 / Al-Fahd W3D / flag / weapon unchanged",
        "- no ZZZZ override of missile slots",
        "",
        "RUNTIME_TEST=NOT RUN",
        "",
        "COMMANDSET LIMIT: slots 2-12 are free (max 18; 13-14 used). B-L are",
        "not wired because UNIT_BUILD requires a valid Object.",
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
        "QUEUE_MECHANISM=Object Iraq_AlFahd500 ButtonImage+SelectPortrait\n"
        "OLD_QUEUE_ICON=irq_9p117\n"
        "NEW_QUEUE_ICON=specter_missile_a\n"
        "COMMANDBUTTONS=CB_MISSILE_A..L\n"
        "BUTTONIMAGE_A=specter_missile_a\n"
        "COMMANDSET=Iraq_AlFahdMissileFactoryCommandSet\n"
        "MAPPING=موشک A -> Iraq_AlFahd500\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER missile factory queue icon + slots A-L\n"
        "Place BOTH complete replacement BIG files in the game folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "  _SPEC_ART_ONE.big\n"
        "Order button and build-queue/countdown both use specter_missile_a.\n"
        "Iraq slot A (CB_MISSILE_A) still builds Iraq_AlFahd500.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_QUEUE_SLOTS.zip"
    if zip_path.exists():
        zip_path.unlink()
    import zipfile

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
