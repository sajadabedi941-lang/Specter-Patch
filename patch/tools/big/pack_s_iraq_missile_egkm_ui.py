#!/usr/bin/env python3
"""Iraq factory E/G/K/M cameo+cards and missile J dark teal/oil-blue skin.

Baseline: PR #605 roster DATA + PR #599/#605 ART.

Queue/timer root cause (ZH): the factory countdown uses Object
SelectPortrait/ButtonImage, not CommandButton. A/B/C/D already use
specter_missile_*. E/G/K/M still used irq_sarab7 / irq_9p117 /
irq_alabbas / irq_bm21.

This pack:
  - retargets E/G/K/M object portraits to specter_missile_{e,g,k,m}
  - gives missile M the same slot-cameo ButtonImage as A-L
  - writes E/G/K tooltip cards in the A/B/C/D layout
  - replaces only Art\\Textures\\Irq_AlMansourP.tga (J-only) with dark teal
  - does not change roster, weapons, costs, build times, or cooldown
"""
from __future__ import annotations

import hashlib
import io
import re
import shutil
import struct
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_ROSTER/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_ROSTER/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_EGKM_UI"

SHA_DATA_605 = "1f226a9de7f1d9fb121e07f6083def0d553bac6bc2f3be223dbea30b432c5d16"
SIZE_DATA_605 = 366614827
SHA_ART_605 = "9c1dc445c17b024f8a4c1c55e699371a94d4991d1dff1eb377f3976a6c54545e"
SIZE_ART_605 = 1295713019

CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
CSF_KEY = r"Data\English\generals.csf"
MAP_KEY = r"Data\INI\MappedImages\HandCreated\Specter_MissileSlot_Images.INI"
E_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AlNida.ini"
G_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
K_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini"
M_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_BM-21.ini"
J_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlMansour.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"

CAMEO_M = r"Art\Textures\specter_missile_m.tga"
J_TEX = r"Art\Textures\Irq_AlMansourP.tga"
FLAG_KEY = r"Art\Textures\IraqiFlag.dds"
J_W3D_M = r"Art\W3D\Irq_AlMansourM.W3D"
J_W3D_T = r"Art\W3D\Irq_AlMansourT.W3D"
J_W3D_TD = r"Art\W3D\Irq_AlMansourTD.W3D"

TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")
TEAL_BODY = (8, 68, 78)
OIL_NOSE = (6, 38, 56)

PORTRAITS = {
    "Iraq_Sarab7": (E_KEY, "irq_sarab7", "specter_missile_e"),
    "Iraq_R11ScudB": (G_KEY, "irq_9p117", "specter_missile_g"),
    "Iraq_Alhussaien": (K_KEY, "irq_alabbas", "specter_missile_k"),
    "Iraq_BM-21": (M_KEY, "irq_bm21", "specter_missile_m"),
}

ABCD = [
    ("Iraq_AlFahd500", r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"),
    ("Iraq_AlHusseinII", r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHusseinII.ini"),
    ("Iraq_AlSamoudII", r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlSamoudII.ini"),
    ("Iraq_AlAbbas", r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini"),
]

TIP_E = (
    "Sarab7\n"
    "Range: 400k\n"
    "Warhead: 200k × 2\n"
    "Point Accuracy: 60/100\n"
    "Radar Stealth: 10/100\n"
    "Rebuild Time: 20 seconds\n"
    "Price: $1,200"
)
TIP_G = (
    "9P117\n"
    "Range: 1000k\n"
    "Warhead: 400k\n"
    "Point Accuracy: 10/100\n"
    "Radar Stealth: 5/100\n"
    "Rebuild Time: 20 seconds\n"
    "Price: $1,200"
)
TIP_K = (
    "Alabaas\n"
    "Range: 1400k\n"
    "Warhead: 15000k\n"
    "Point Accuracy: 40/100\n"
    "Radar Stealth: 80/100\n"
    "Rebuild Time: 5 minutes\n"
    "Price: $20,000"
)

MAP_M = """
MappedImage specter_missile_m
  Texture = specter_missile_m.tga
  TextureWidth = 128
  TextureHeight = 128
  Coords = Left:0 Top:0 Right:128 Bottom:128
  Status = NONE
End
"""

CB_M_NEW = """CommandButton CB_MISSILE_M
  Command       = UNIT_BUILD
  Object        = Iraq_BM-21
  TextLabel     = CONTROLBAR:SpecterMissileM
  ButtonImage   = specter_missile_m
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipSpecterMissileM
End"""


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


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


def last_block(kind: str, name: str, text: str):
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\n.*?^End", text))
    return matches[-1] if matches else None


def replace_last_block(kind: str, name: str, text: str, new_block: str) -> str:
    m = last_block(kind, name, text)
    if not m:
        raise SystemExit(f"missing {kind} {name}")
    return text[: m.start()] + new_block.strip() + text[m.end() :]


def object_body(text: str, name: str) -> str | None:
    found = [(m.group(1), m.start()) for m in re.finditer(r"^Object\s+(\S+)\s*$", text, re.M)]
    for i, (n, start) in enumerate(found):
        if n == name:
            end = found[i + 1][1] if i + 1 < len(found) else len(text)
            return text[start:end]
    return None


def replace_object_portraits(text: str, name: str, old: str, new: str) -> str:
    found = [(m.group(1), m.start()) for m in re.finditer(r"^Object\s+(\S+)\s*$", text, re.M)]
    for i, (n, start) in enumerate(found):
        if n != name:
            continue
        end = found[i + 1][1] if i + 1 < len(found) else len(text)
        body = text[start:end]
        body2 = re.sub(
            rf"^(\s*SelectPortrait\s*=\s*){re.escape(old)}[ \t]*$",
            rf"\1{new}",
            body,
            count=1,
            flags=re.M,
        )
        body2 = re.sub(
            rf"^(\s*ButtonImage\s*=\s*){re.escape(old)}[ \t]*$",
            rf"\1{new}",
            body2,
            count=1,
            flags=re.M,
        )
        if body2 == body:
            raise SystemExit(f"{name} portraits {old} not found")
        return text[:start] + body2 + text[end:]
    raise SystemExit(f"object {name} missing")


def field(body: str | None, key: str) -> str:
    if not body:
        return ""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", body, re.M)
    return m.group(1).strip() if m else ""


def cmdset_slots(block: str) -> dict[int, str]:
    return {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)\s*$", block, re.M)}


def cb_field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block, re.M)
    return m.group(1).strip() if m else ""


def csf_parse(csf: bytes):
    if csf[:4] != b" FSC":
        raise SystemExit(f"unexpected CSF magic {csf[:4]!r}")
    magic, ver, nlab, nstr, unused, lang = struct.unpack_from("<4sIIIII", csf, 0)
    labels = []
    pos = 24
    while pos < len(csf):
        if csf[pos : pos + 4] != b" LBL":
            break
        pos += 4
        cnt, nlen = struct.unpack_from("<II", csf, pos)
        pos += 8
        name = csf[pos : pos + nlen].decode("latin1")
        pos += nlen
        strs = []
        for _ in range(cnt):
            smag = csf[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4
            raw = csf[pos : pos + slen * 2]
            pos += slen * 2
            val = bytes(x ^ 0xFF for x in raw).decode("utf-16le")
            extra = None
            if smag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4
                extra = csf[pos : pos + elen]
                pos += elen
            strs.append((smag, val, extra))
        labels.append((name, strs))
    return magic, ver, unused, lang, labels


def csf_build(magic, ver, unused, lang, labels) -> bytes:
    body = bytearray()
    nstr = 0
    for name, strs in labels:
        body += b" LBL"
        body += struct.pack("<II", len(strs), len(name))
        body += name.encode("latin1")
        for smag, val, extra in strs:
            encoded = val.encode("utf-16le")
            xored = bytes(x ^ 0xFF for x in encoded)
            tag = smag if smag in (b" RTS", b"WRTS") else b" RTS"
            body += tag
            body += struct.pack("<I", len(val))
            body += xored
            nstr += 1
            if tag == b"WRTS" and extra is not None:
                body += struct.pack("<I", len(extra))
                body += extra
    header = bytearray()
    header += magic
    header += struct.pack("<IIIII", ver, len(labels), nstr, unused, lang)
    return bytes(header + body)


def csf_upsert(csf: bytes, mapping: dict[str, str]) -> bytes:
    magic, ver, unused, lang, labels = csf_parse(csf)
    by_name = {n: i for i, (n, _) in enumerate(labels)}
    for key, value in mapping.items():
        if key in by_name:
            i = by_name[key]
            name, strs = labels[i]
            if strs:
                smag, _old, extra = strs[0]
                strs[0] = (smag, value, extra)
            else:
                strs.append((b" RTS", value, None))
            labels[i] = (name, strs)
        else:
            labels.append((key, [(b" RTS", value, None)]))
    return csf_build(magic, ver, unused, lang, labels)


def csf_get(csf: bytes, key: str) -> str | None:
    _m, _v, _u, _l, labels = csf_parse(csf)
    for name, strs in labels:
        if name == key and strs:
            return strs[0][1]
    return None


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_missile_slot_image(letter: str) -> Image.Image:
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


def make_tga32(im: Image.Image) -> bytes:
    rgba = im.convert("RGBA")
    w, h = rgba.size
    pixels = rgba.tobytes()
    rows = []
    stride = w * 4
    for y in range(h - 1, -1, -1):
        src = pixels[y * stride : (y + 1) * stride]
        bgra = bytearray()
        for i in range(0, len(src), 4):
            r, g, b, a = src[i : i + 4]
            bgra += bytes((b, g, r, a))
        rows.append(bytes(bgra))
    header = bytearray(18)
    header[2] = 2
    struct.pack_into("<HH", header, 12, w, h)
    header[16] = 32
    header[17] = 0x08
    return bytes(header) + b"".join(rows) + TRUEVISION


def shade(color: tuple[int, int, int], t: float) -> tuple[int, int, int, int]:
    t = max(0.72, min(1.08, t))
    return (
        min(255, int(color[0] * t)),
        min(255, int(color[1] * t)),
        min(255, int(color[2] * t)),
        255,
    )


def paste_small_flag(im: Image.Image, flag: Image.Image, xy: tuple[int, int], size: tuple[int, int]) -> None:
    fw, fh = size
    flag_im = flag.convert("RGBA").resize((fw, fh), Image.Resampling.NEAREST)
    bordered = Image.new("RGBA", (fw + 8, fh + 8), (16, 14, 12, 255))
    bordered.paste(flag_im, (4, 4), flag_im)
    im.paste(bordered, xy, bordered)


def draw_stencil(im: Image.Image, text: str, center: tuple[int, int]) -> None:
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
    gap = 4
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + gap * (len(text) - 1)
    bbox = font.getbbox("Hg")
    glyph_h = bbox[3] - bbox[1]
    x = center[0] - total / 2
    y = center[1] - glyph_h / 2 - bbox[1]
    plate = [int(x - 14), int(y - 7), int(x + total + 14), int(y + glyph_h + 10)]
    draw.rounded_rectangle(plate, radius=6, fill=(214, 178, 16, 230), outline=(12, 10, 8), width=3)
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=(18, 16, 12), stroke_width=1, stroke_fill=(8, 8, 8))
        x += w + gap


def make_j_skin(flag: Image.Image) -> Image.Image:
    w = h = 1024
    im = Image.new("RGBA", (w, h), shade(TEAL_BODY, 1.0))
    px = im.load()
    nose_hi = int(0.14 * h)
    body_lo = int(0.18 * h)
    body_hi = int(0.82 * h)
    rear_lo = int(0.88 * h)
    mid_u0, mid_u1 = int(0.32 * w), int(0.68 * w)
    for y in range(h):
        for x in range(w):
            if y < nose_hi:
                circ = 1.0 - 0.10 * abs((x / w) - 0.5)
                px[x, y] = shade(OIL_NOSE, circ)
            elif y < body_lo:
                px[x, y] = shade(TEAL_BODY, 0.78)
            elif y < body_hi:
                circ = 1.04 - 0.18 * abs((y - (body_lo + body_hi) / 2) / max(1, (body_hi - body_lo) / 2))
                px[x, y] = shade(TEAL_BODY, circ)
            elif y < rear_lo:
                px[x, y] = shade(TEAL_BODY, 0.80)
            else:
                px[x, y] = shade(TEAL_BODY, 0.88)
    draw = ImageDraw.Draw(im)
    for x in (int(0.30 * w), int(0.70 * w)):
        draw.line([(x, body_lo + 4), (x, body_hi - 4)], fill=(12, 12, 12, 80), width=2)
    paste_small_flag(im, flag, (mid_u0 + 18, body_lo + 36), (168, 96))
    paste_small_flag(im, flag, (mid_u0 + 18, body_lo + 250), (168, 96))
    draw_stencil(im, "AL-MANSOUR", ((mid_u0 + mid_u1) // 2, body_lo + 160))
    draw_stencil(im, "AL-MANSOUR", ((mid_u0 + mid_u1) // 2, body_lo + 372))
    im = ImageEnhance.Contrast(im).enhance(1.04)
    im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=40, threshold=3))
    return im.convert("RGBA")


def is_teal(rgb: tuple[int, int, int]) -> bool:
    r, g, b = rgb
    return g >= 28 and b >= 28 and g >= r + 15 and b >= r + 10 and r < 90


def weapon_field(data: dict[str, bytes], name: str, key: str) -> str:
    b = last_block("Weapon", name, decode(data[WEAPON_KEY]))
    return field(b.group(0) if b else None, key)


def validate(data: dict[str, bytes], src: dict[str, bytes], art: dict[str, bytes], src_art: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    cs = decode(data[CS_KEY])
    src_cs = decode(src[CS_KEY])
    if cs != src_cs:
        fails.append("CommandSet.ini mutated; roster must stay PR #605")
    cb = decode(data[CB_KEY])
    src_cb = decode(src[CB_KEY])
    for ch in "ABCDEFGHIJKL":
        a = last_block("CommandButton", f"CB_MISSILE_{ch}", cb)
        b = last_block("CommandButton", f"CB_MISSILE_{ch}", src_cb)
        if not a or not b:
            fails.append(f"CB_MISSILE_{ch} missing")
        elif ch != "M" and a.group(0) != b.group(0):
            fails.append(f"CB_MISSILE_{ch} mutated")
    mbtn = last_block("CommandButton", "CB_MISSILE_M", cb)
    if not mbtn:
        fails.append("CB_MISSILE_M missing")
    else:
        if cb_field(mbtn.group(0), "Object") != "Iraq_BM-21":
            fails.append("M object drifted")
        if cb_field(mbtn.group(0), "Command") != "UNIT_BUILD":
            fails.append("M command drifted")
        if cb_field(mbtn.group(0), "ButtonImage") != "specter_missile_m":
            fails.append("M ButtonImage not specter_missile_m")
        if cb_field(mbtn.group(0), "TextLabel") != "CONTROLBAR:SpecterMissileM":
            fails.append("M TextLabel drifted")

    for obj, path in ABCD:
        if decode(data[path]) != decode(src[path]):
            fails.append(f"{obj} mutated")
        body = object_body(decode(data[path]), obj)
        if not field(body, "ButtonImage").startswith("specter_missile_"):
            fails.append(f"{obj} lost slot cameo")

    for obj, (path, _old, new) in PORTRAITS.items():
        body = object_body(decode(data[path]), obj)
        src_body = object_body(decode(src[path]), obj)
        if field(body, "SelectPortrait") != new or field(body, "ButtonImage") != new:
            fails.append(f"{obj} portraits {field(body,'SelectPortrait')}/{field(body,'ButtonImage')}")
        if field(body, "BuildCost") != field(src_body, "BuildCost"):
            fails.append(f"{obj} BuildCost changed")
        if field(body, "BuildTime") != field(src_body, "BuildTime"):
            fails.append(f"{obj} BuildTime changed")
        src_rest = re.sub(r"^\s*(SelectPortrait|ButtonImage)\s*=.*$", "", src_body or "", flags=re.M)
        new_rest = re.sub(r"^\s*(SelectPortrait|ButtonImage)\s*=.*$", "", body or "", flags=re.M)
        if src_rest != new_rest:
            fails.append(f"{obj} non-portrait body mutated")

    mapped = decode(data[MAP_KEY])
    if "MappedImage specter_missile_m" not in mapped:
        fails.append("mapped image specter_missile_m missing")

    if csf_get(data[CSF_KEY], "CONTROLBAR:SpecterMissileM") != "Missile M":
        fails.append("M label not Missile M")
    if csf_get(data[CSF_KEY], "CONTROLBAR:ToolTipSpecterMissileE") != TIP_E:
        fails.append("E tooltip mismatch")
    if csf_get(data[CSF_KEY], "CONTROLBAR:ToolTipSpecterMissileG") != TIP_G:
        fails.append("G tooltip mismatch")
    if csf_get(data[CSF_KEY], "CONTROLBAR:ToolTipSpecterMissileK") != TIP_K:
        fails.append("K tooltip mismatch")
    if csf_get(data[CSF_KEY], "OBJECT:abbasicbmm") != csf_get(src[CSF_KEY], "OBJECT:abbasicbmm"):
        fails.append("ICBM display CSF mutated")
    for ch in "ABCDHIJ":
        if csf_get(data[CSF_KEY], f"CONTROLBAR:ToolTipSpecterMissile{ch}") != csf_get(
            src[CSF_KEY], f"CONTROLBAR:ToolTipSpecterMissile{ch}"
        ):
            fails.append(f"tooltip {ch} mutated")

    for wname in ["2x_MRPGM_Raad2", "SRBM_ALHIJARAH_HE", "AlAbidMissileWeapon", "Weapon_Iraq_AlMansour"]:
        a = last_block("Weapon", wname, decode(data[WEAPON_KEY]))
        b = last_block("Weapon", wname, decode(src[WEAPON_KEY]))
        if (a.group(0) if a else None) != (b.group(0) if b else None):
            fails.append(f"weapon {wname} mutated")

    allowed_data = {CB_KEY, CSF_KEY, MAP_KEY, E_KEY, G_KEY, K_KEY, M_KEY}
    for k in data:
        if k not in allowed_data and data[k] != src[k]:
            fails.append(f"unrelated DATA mutated: {k}")
            break

    if CAMEO_M not in art:
        fails.append("specter_missile_m.tga missing from ART")
    if art.get(J_W3D_M) != src_art.get(J_W3D_M):
        fails.append("Irq_AlMansourM.W3D mutated")
    if art.get(J_W3D_T) != src_art.get(J_W3D_T):
        fails.append("Irq_AlMansourT.W3D mutated")
    if art.get(J_W3D_TD) != src_art.get(J_W3D_TD):
        fails.append("Irq_AlMansourTD.W3D mutated")
    if art.get(J_TEX) == src_art.get(J_TEX):
        fails.append("Irq_AlMansourP.tga not recolored")
    else:
        im = Image.open(io.BytesIO(art[J_TEX])).convert("RGB")
        body = im.crop((40, 200, 280, 780))
        px = list(body.getdata())
        teal_n = sum(1 for p in px[::8] if is_teal(p))
        if teal_n < 200:
            fails.append(f"J body not teal/oil-blue samples={teal_n}")
    for ch in "abcdefghijkl":
        key = rf"Art\Textures\specter_missile_{ch}.tga"
        if art.get(key) != src_art.get(key):
            fails.append(f"cameo {ch} mutated")
            break
    added = sorted(set(art) - set(src_art))
    if added != [CAMEO_M]:
        fails.append(f"unexpected ART adds {added}")
    removed = sorted(set(src_art) - set(art))
    if removed:
        fails.append(f"ART removed {removed}")
    changed = [k for k in src_art if art.get(k) != src_art.get(k)]
    if set(changed) - {J_TEX}:
        fails.append(f"unexpected ART mutations {changed}")
    return fails


def main() -> int:
    if sha256_path(SRC_DATA) != SHA_DATA_605 or SRC_DATA.stat().st_size != SIZE_DATA_605:
        raise SystemExit("PR #605 DATA mismatch")
    if sha256_path(SRC_ART) != SHA_ART_605 or SRC_ART.stat().st_size != SIZE_ART_605:
        raise SystemExit("PR #605 ART mismatch")

    src = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src)
    art = dict(src_art)

    cb = decode(data[CB_KEY])
    cb = replace_last_block("CommandButton", "CB_MISSILE_M", cb, CB_M_NEW)
    data[CB_KEY] = to_crlf(cb)

    mapped = decode(data[MAP_KEY])
    if "MappedImage specter_missile_m" not in mapped:
        mapped = mapped.rstrip() + "\n" + MAP_M
    data[MAP_KEY] = to_crlf(mapped)

    for obj, (path, old, new) in PORTRAITS.items():
        data[path] = to_crlf(replace_object_portraits(decode(data[path]), obj, old, new))

    data[CSF_KEY] = csf_upsert(
        data[CSF_KEY],
        {
            "CONTROLBAR:ToolTipSpecterMissileE": TIP_E,
            "CONTROLBAR:ToolTipSpecterMissileG": TIP_G,
            "CONTROLBAR:ToolTipSpecterMissileK": TIP_K,
            "CONTROLBAR:SpecterMissileM": "Missile M",
            "OBJECT:Sarab7": "Sarab7",
            "OBJECT:9P117S": "9P117",
        },
    )

    cameo = make_missile_slot_image("M")
    art[CAMEO_M] = make_tga24(cameo)
    flag = Image.open(io.BytesIO(src_art[FLAG_KEY])).convert("RGBA")
    sheet = make_j_skin(flag)
    art[J_TEX] = make_tga32(sheet)

    fails = validate(data, src, art, src_art)
    packed_data = build_big(data)
    packed_art = build_big(art)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed_data))
    fails.extend(f"ART {x}" for x in big_structure_ok(packed_art))
    extracted_d = parse_big(packed_data)
    extracted_a = parse_big(packed_art)
    fails.extend(validate(extracted_d, src, extracted_a, src_art))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(packed_data)
    out_art.write_bytes(packed_art)
    cameo.save(OUT / "specter_missile_m.png")
    sheet.convert("RGB").save(OUT / "irq_j_almansour_teal.png")
    (ROOT / "patch/Art/Textures").mkdir(parents=True, exist_ok=True)
    (ROOT / "patch/Art/Textures/specter_missile_m.tga").write_bytes(art[CAMEO_M])
    (ROOT / "patch/Art/Textures/Irq_AlMansourP.tga").write_bytes(art[J_TEX])

    data_sha = sha256_path(out_data)
    art_sha = sha256_path(out_art)
    conflicts = [
        "E display Build 20s vs object BuildTime 22.0; AttackRange 1200 vs card 400k; ClipSize 2 matches two missiles; BuildCost 1200 matches $1,200",
        "G display Build 20s vs object BuildTime 17.0; AttackRange 1720 vs card 1000k; PrimaryDamage 2000 vs card 400k; BuildCost 1200 matches $1,200",
        "K display Build 5 minutes vs object BuildTime 30.0; AttackRange 2300 vs card 1400k; AlAbidMissileWeapon PrimaryDamage 1 (warhead is separate) vs card 15000k; BuildCost 20000 matches $20,000",
        "K ICBM CSF OBJECT:abbasicbmm left unchanged; factory card first line is Alabaas",
    ]
    report = [
        "# SPECTER Iraq E/G/K/M cameos + cards + missile J teal",
        "",
        "Baseline packed last-wins: PR #605 DATA + PR #599/#605 ART",
        "",
        "QUEUE/TIMER ROOT CAUSE: ZH build-queue icon is Object ButtonImage.",
        "A/B/C/D already use specter_missile_*. E/G/K/M used WF portraits.",
        "Command type was already UNIT_BUILD on the factory; not a command-type bug.",
        "",
        "Fixes:",
        "  E object Iraq_Sarab7     irq_sarab7  -> specter_missile_e",
        "  G object Iraq_R11ScudB   irq_9p117   -> specter_missile_g",
        "  K object Iraq_Alhussaien irq_alabbas -> specter_missile_k",
        "  M object Iraq_BM-21      irq_bm21    -> specter_missile_m",
        "  CB_MISSILE_M ButtonImage irq_bm21    -> specter_missile_m",
        "  ART add specter_missile_m.tga (same generator as A-L, letter M)",
        "  ART replace Irq_AlMansourP.tga only (J flying + pre-launch missile)",
        "",
        "DISPLAY/GAMEPLAY CONFLICTS (gameplay NOT changed):",
        *[f"  - {c}" for c in conflicts],
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- ART size: {out_art.stat().st_size}",
        f"- ART SHA256: {art_sha}",
        "",
    ]
    if fails:
        seen = []
        for f in fails:
            if f not in seen:
                seen.append(f)
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in seen)
        report.append("RUNTIME_TEST=NOT RUN")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static / packed last-wins)",
        "- Factory CommandSet unchanged vs PR #605",
        "- A/B/C/D buttons and objects unchanged",
        "- E/G/K/M CommandButtons remain UNIT_BUILD on the correct objects",
        "- E/G/K/M object portraits now match A/B/C/D slot cameos (queue/timer)",
        "- M button image is specter_missile_m; label Missile M",
        "- E/G/K tooltip cards use the A/B/C/D layout with requested text",
        "- ICBM object ID/weapon/cost/time and OBJECT:abbasicbmm unchanged",
        "- Weapons and BuildCost/BuildTime unchanged",
        "- ART: only specter_missile_m.tga added and Irq_AlMansourP.tga replaced",
        "- J W3Ds still reference Irq_AlMansourP.tga; shared 9P117 truck tex untouched",
        "",
        "Static validation completed; runtime game test not performed.",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=YES\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"ART_SIZE={out_art.stat().st_size}\n"
        f"ART_SHA256={art_sha}\n"
        "BASELINE=PR #605 DATA + PR #599 ART\n"
        "CAMEO_M=specter_missile_m\n"
        "J_TEX=Irq_AlMansourP.tga dark teal / oil blue\n"
        "COOLDOWN=NOT IMPLEMENTED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n"
        "J_COLOR_INGAME=NOT TESTED\n"
        "EGK_QUEUE_INGAME=NOT TESTED\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Iraq E/G/K/M factory cameos + cards, missile J teal\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder.\n"
        "Missile M uses the same slot-cameo design as A-D.\n"
        "E/G/K queue/timer portraits now use specter_missile_e/g/k.\n"
        "Al-Mansour flying/pre-launch texture is dark teal / oil blue.\n"
        "No cooldown in this pack. Static validation only.\n",
        encoding="utf-8",
    )
    (OUT / "CONFLICTS.txt").write_text("\n".join(conflicts) + "\n", encoding="utf-8")
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_EGKM_UI.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
        zf.write(OUT / "CONFLICTS.txt", "CONFLICTS.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
