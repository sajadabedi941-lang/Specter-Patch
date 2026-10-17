#!/usr/bin/env python3
"""Dedicated visual skins for Iraq factory missiles B, C, D, H, I, J.

ART-only. Live ART baseline: SPECTER_IRAQ_MISSILE_QUEUE_SLOTS.
Does not modify DATA, 9P117, Al-Fahd500, universal slot cameos A-L,
GENERIC-MISSILES, or shared Hussien/Abbas textures.

Each missile is a clone of Irq_R11_M.W3D (BOOSTER = middle body,
MISSILE01 = nose) with a unique hierarchy and a dedicated 1024 32-bit TGA.
"""
from __future__ import annotations

import hashlib
import io
import shutil
import struct
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/workspace")
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_QUEUE_SLOTS/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_SKINS_BCDHIJ"
PREVIEW = ROOT / "patch/Art/Textures/Missiles"

BASE_ART_SHA = "5fdc19145769b81bce2cddaeeb91701d6c9ce0f4e288e0d55baa03cbfdb33ea9"
BASE_ART_SIZE = 1267067968

R11_W3D = r"Art\W3D\Irq_R11_M.W3D"
ALFAHD_W3D = r"Art\W3D\Irq_AlFahd500M.W3D"
ALFAHD_TEX = r"Art\Textures\Irq_AlFahd500P.tga"
GENERIC = r"Art\Textures\GENERIC-MISSILES.dds"
FLAG_KEY = r"Art\Textures\IraqiFlag.dds"
FACTORY_TGA = r"Art\Textures\missile_factory.tga"

TEX_CHUNK = 0x00000032
MESH_HEADER = 0x0000001F
TEXCOORD_CHUNK = 0x0000004A
HLOD_HEADER = 0x00000701
TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")
SHEET = 1024

# Military body / nose colours (RGB).
WHITE = (228, 224, 216)
BLACK = (22, 24, 26)
RED = (168, 32, 28)
ORANGE = (210, 108, 22)
YELLOW = (214, 178, 28)

MISSILES = [
    {
        "slot": "B",
        "name": "AL-HUSSEIN II",
        "w3d": r"Art\W3D\Irq_AlHussein2M.W3D",
        "tex": r"Art\Textures\Irq_AlHussein2P.tga",
        "hier": b"IRQ_AH2_M",
        "hlod": "Irq_AlHussein2M",
        "body": WHITE,
        "nose": RED,
        "expect_body": "white",
        "expect_nose": "red",
    },
    {
        "slot": "C",
        "name": "AL-SAMOUD II",
        "w3d": r"Art\W3D\Irq_AlSamoud2M.W3D",
        "tex": r"Art\Textures\Irq_AlSamoud2P.tga",
        "hier": b"IRQ_AS2_M",
        "hlod": "Irq_AlSamoud2M",
        "body": BLACK,
        "nose": RED,
        "expect_body": "black",
        "expect_nose": "red",
    },
    {
        "slot": "D",
        "name": "AL-ABBAS",
        "w3d": r"Art\W3D\Irq_AlAbbas2M.W3D",
        "tex": r"Art\Textures\Irq_AlAbbas2P.tga",
        "hier": b"IRQ_AAB_M",
        "hlod": "Irq_AlAbbas2M",
        "body": RED,
        "nose": WHITE,
        "expect_body": "red",
        "expect_nose": "white",
    },
    {
        "slot": "H",
        "name": "AL-BASRAH",
        "w3d": r"Art\W3D\Irq_AlBasrahM.W3D",
        "tex": r"Art\Textures\Irq_AlBasrahP.tga",
        "hier": b"IRQ_ABS_M",
        "hlod": "Irq_AlBasrahM",
        "body": WHITE,
        "nose": BLACK,
        "expect_body": "white",
        "expect_nose": "black",
    },
    {
        "slot": "I",
        "name": "AL-NASIR",
        "w3d": r"Art\W3D\Irq_AlNasirM.W3D",
        "tex": r"Art\Textures\Irq_AlNasirP.tga",
        "hier": b"IRQ_ANS_M",
        "hlod": "Irq_AlNasirM",
        "body": ORANGE,
        "nose": RED,
        "expect_body": "orange",
        "expect_nose": "red",
    },
    {
        "slot": "J",
        "name": "AL-MANSOUR",
        "w3d": r"Art\W3D\Irq_AlMansourM.W3D",
        "tex": r"Art\Textures\Irq_AlMansourP.tga",
        "hier": b"IRQ_AMN_M",
        "hlod": "Irq_AlMansourM",
        "body": YELLOW,
        "nose": RED,
        "expect_body": "yellow",
        "expect_nose": "red",
    },
]

CAMEOS = [rf"Art\Textures\specter_missile_{ch}.tga" for ch in "abcdefghijkl"]
DONOR_W3D = [
    r"Art\W3D\Irq_9P117.W3D",
    r"Art\W3D\Irq_9P117D.W3D",
    r"Art\W3D\Irq_R11_M.W3D",
    r"Art\W3D\Irq_AlFahd500.W3D",
    r"Art\W3D\Irq_AlFahd500D.W3D",
    r"Art\W3D\Irq_AlFahd500M.W3D",
    r"Art\W3D\Irq_HussienM.W3D",
    r"Art\W3D\Irq_AbbasM.W3D",
]
DONOR_TEX = [
    r"Art\Textures\Irq_9P117.dds",
    r"Art\Textures\Irq_AlFahd500P.tga",
    r"Art\Textures\Irq_AlFahd500M.tga",
    r"Art\Textures\Irq_Alhussein.dds",
    r"Art\Textures\Irq_AbbasMissile.dds",
    GENERIC,
    FLAG_KEY,
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


def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def uniquify(blob: bytes, old: bytes, new: bytes) -> bytes:
    if len(old) != len(new):
        raise ValueError(f"identity length {old!r} -> {new!r}")
    return blob.replace(old, new)


def set_hlod_name(blob: bytes, name: str) -> bytes:
    padded = name.encode("latin1")[:15] + b"\x00"
    padded = padded + b"\x00" * (16 - len(padded))

    def rec(data: bytes) -> bytes:
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
                payload = rec(payload)
            elif cid == HLOD_HEADER and len(payload) >= 24:
                payload = bytearray(payload)
                payload[8:24] = padded
                payload = bytes(payload)
            new_raw = len(payload) | (0x80000000 if cont else 0)
            out += struct.pack("<II", cid, new_raw)
            out += payload
            pos = ce
        if pos < end:
            out += data[pos:]
        return bytes(out)

    return rec(blob)


def remap_uv(u: float, v: float, mesh: str) -> tuple[float, float]:
    """Split R11 GENERIC-MISSILES islands onto a dedicated unwrap.

    BOOSTER main cylinder (length along U, circumference along V) -> middle body.
    MISSILE01 warhead -> nose band at low V.
    Rear/fin leftovers -> high-V body strip with no decals.
    """
    if mesh == "MISSILE01":
        if 0.64 <= u <= 0.76 and 0.80 <= v <= 0.88:
            u2 = clamp01((u - 0.6708) / (0.7317 - 0.6708))
            v2 = clamp01((v - 0.8189) / (0.8634 - 0.8189))
            return 0.04 + u2 * 0.92, 0.015 + v2 * 0.11
        return 0.50, 0.07
    if 0.46 <= u <= 0.54 and 0.18 <= v <= 0.32:
        u2 = clamp01((u - 0.4694) / (0.5305 - 0.4694))
        v2 = clamp01((v - 0.2211) / (0.2843 - 0.2211))
        return 0.04 + u2 * 0.92, 0.20 + v2 * 0.60
    return 0.14, 0.94


def walk_rebuild(blob: bytes, tex_name: str, mesh_name: str | None = None) -> bytes:
    out = bytearray()
    pos = 0
    end = len(blob)
    current = mesh_name
    tex_payload = tex_name.encode("latin1") + b"\x00"
    while pos + 8 <= end:
        cid, raw = struct.unpack_from("<II", blob, pos)
        sz = raw & 0x7FFFFFFF
        cont = bool(raw & 0x80000000)
        cs, ce = pos + 8, pos + 8 + sz
        if ce > end:
            break
        payload = blob[cs:ce]
        if cid == MESH_HEADER and len(payload) >= 24:
            current = zstr(payload[8:24])
        if cont:
            payload = walk_rebuild(payload, tex_name, current)
        elif cid == TEX_CHUNK:
            payload = tex_payload
        elif cid == TEXCOORD_CHUNK:
            n = len(payload) // 8
            rebuilt = bytearray()
            for i in range(n):
                u, v = struct.unpack_from("<ff", payload, i * 8)
                rebuilt += struct.pack("<ff", *remap_uv(u, v, current or ""))
            payload = bytes(rebuilt)
        new_raw = len(payload) | (0x80000000 if cont else 0)
        out += struct.pack("<II", cid, new_raw)
        out += payload
        pos = ce
    if pos < end:
        out += blob[pos:]
    return bytes(out)


def texture_names(blob: bytes) -> set[str]:
    found: set[str] = set()

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

    rec(blob, 0, len(blob))
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


def tga_info(blob: bytes) -> dict:
    return {
        "width": struct.unpack_from("<H", blob, 12)[0],
        "height": struct.unpack_from("<H", blob, 14)[0],
        "type": blob[2],
        "bpp": blob[16],
        "alpha_bits": blob[17] & 0x0F,
        "origin": "top" if blob[17] & 0x20 else "bottom",
    }


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


def draw_stencil(im: Image.Image, text: str, center: tuple[int, int], light_body: bool) -> None:
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
    if light_body:
        fill_plate = (28, 26, 22, 230)
        ink = (236, 228, 210)
        outline = (12, 10, 8)
    else:
        fill_plate = (214, 178, 16, 230)
        ink = (18, 16, 12)
        outline = (12, 10, 8)
    draw.rounded_rectangle(plate, radius=6, fill=fill_plate, outline=outline, width=3)
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=ink, stroke_width=1, stroke_fill=(8, 8, 8))
        x += w + gap


def make_skin(body: tuple[int, int, int], nose: tuple[int, int, int], stamp: str, flag: Image.Image) -> Image.Image:
    """1024 unwrap: low-V nose, mid-V body with small flag+name on the middle U third."""
    w = h = SHEET
    im = Image.new("RGBA", (w, h), shade(body, 1.0))
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
                px[x, y] = shade(nose, circ)
            elif y < body_lo:
                px[x, y] = shade(body, 0.78)
            elif y < body_hi:
                circ = 1.04 - 0.18 * abs((y - (body_lo + body_hi) / 2) / max(1, (body_hi - body_lo) / 2))
                px[x, y] = shade(body, circ)
            elif y < rear_lo:
                px[x, y] = shade(body, 0.80)
            else:
                px[x, y] = shade(body, 0.88)
    draw = ImageDraw.Draw(im)
    # Section seams on the body unwrap (rear | middle | forward) without covering decals.
    for x in (int(0.30 * w), int(0.70 * w)):
        draw.line([(x, body_lo + 4), (x, body_hi - 4)], fill=(12, 12, 12, 80), width=2)
    light = body[0] + body[1] + body[2] > 360
    # Two small flags around the cylinder, both in the middle-length third.
    paste_small_flag(im, flag, (mid_u0 + 18, body_lo + 36), (168, 96))
    paste_small_flag(im, flag, (mid_u0 + 18, body_lo + 250), (168, 96))
    draw_stencil(im, stamp, ((mid_u0 + mid_u1) // 2, body_lo + 160), light)
    draw_stencil(im, stamp, ((mid_u0 + mid_u1) // 2, body_lo + 372), light)
    im = ImageEnhance.Contrast(im).enhance(1.04)
    im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=40, threshold=3))
    return im.convert("RGBA")


def classify(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    if r > 140 and g < 90 and b < 90:
        return "red"
    if r < 55 and g < 55 and b < 55:
        return "black"
    if r > 190 and g > 185 and b > 175:
        return "white"
    if r > 170 and 70 < g < 160 and b < 70:
        return "orange"
    if r > 160 and g > 130 and b < 80:
        return "yellow"
    if r > 160 and g > 90 and b < 80 and g > b + 40:
        return "orange"
    return "other"


def region_mode(im: Image.Image, box: tuple[int, int, int, int]) -> dict[str, int]:
    crop = im.convert("RGB").crop(box)
    px = crop.load()
    w, h = crop.size
    counts = {"red": 0, "white": 0, "black": 0, "yellow": 0, "orange": 0, "other": 0}
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            counts[classify(px[x, y])] += 1
    return counts


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


def validate(art: dict[str, bytes], src_art: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    for key in DONOR_W3D + DONOR_TEX + CAMEOS:
        if key in src_art and art.get(key) != src_art[key]:
            fails.append(f"protected asset mutated {key}")
    if b"IRQ_R11_M" not in art[R11_W3D]:
        fails.append("original R11 identity lost")
    if b"IRQ_ALF_M" not in art[ALFAHD_W3D]:
        fails.append("Al-Fahd projectile identity lost")
    if texture_names(art[ALFAHD_W3D]) != {"Irq_AlFahd500P.tga"}:
        fails.append("Al-Fahd projectile texture retargeted")

    for spec in MISSILES:
        w3d = art.get(spec["w3d"])
        tex = art.get(spec["tex"])
        if not w3d or not tex:
            fails.append(f"missing {spec['name']} assets")
            continue
        if spec["hier"] not in w3d:
            fails.append(f"{spec['name']} hierarchy {spec['hier']!r} missing")
        if b"IRQ_R11_M" in w3d or b"IRQ_ALF_M" in w3d or b"IRQ_9P117" in w3d:
            fails.append(f"{spec['name']} still shares 9P117/Al-Fahd identity")
        if hlod_name(w3d) != spec["hlod"]:
            fails.append(f"{spec['name']} HLod {hlod_name(w3d)!r}")
        tex_file = spec["tex"].rsplit("\\", 1)[-1]
        if texture_names(w3d) != {tex_file}:
            fails.append(f"{spec['name']} textures {texture_names(w3d)}")
        info = tga_info(tex)
        if info["type"] != 2 or info["bpp"] != 32 or info["alpha_bits"] != 8:
            fails.append(f"{spec['name']} TGA profile {info}")
        if info["width"] != SHEET or info["height"] != SHEET or info["origin"] != "bottom":
            fails.append(f"{spec['name']} TGA layout {info}")
        decoded = Image.open(io.BytesIO(tex)).convert("RGB")
        # Nose band (low V), body (mid V, not the flag island), flag, stencil.
        nose = region_mode(decoded, (40, 20, 980, 120))
        body = region_mode(decoded, (40, 200, 280, 780))
        flag = region_mode(decoded, (340, 230, 530, 350))
        text = region_mode(decoded, (360, 330, 760, 410))
        if nose.get(spec["expect_nose"], 0) < 80:
            fails.append(f"{spec['name']} nose not {spec['expect_nose']} {nose}")
        if body.get(spec["expect_body"], 0) < 80:
            fails.append(f"{spec['name']} body not {spec['expect_body']} {body}")
        if flag["red"] < 40 or flag["white"] < 15 or flag["black"] < 30:
            fails.append(f"{spec['name']} missing Iraqi flag {flag}")
        if text["black"] + text["yellow"] + text["white"] + text["other"] < 30:
            fails.append(f"{spec['name']} missing stencil {text}")
        uvs = collect_uvs(w3d)
        body_uv = [(u, v) for m, u, v in uvs if m == "BOOSTER" and 0.18 < v < 0.82]
        nose_uv = [(u, v) for m, u, v in uvs if m == "MISSILE01" and v < 0.16]
        if len(body_uv) < 8:
            fails.append(f"{spec['name']} too few middle-body UVs")
        if len(nose_uv) < 4:
            fails.append(f"{spec['name']} too few nose UVs")
        if body_uv:
            us = [u for u, _v in body_uv]
            if min(us) > 0.35 or max(us) < 0.65:
                fails.append(f"{spec['name']} body UVs miss middle U {min(us):.2f}..{max(us):.2f}")

    changed = sorted(k for k in set(art) | set(src_art) if art.get(k) != src_art.get(k))
    allowed = {spec["w3d"] for spec in MISSILES} | {spec["tex"] for spec in MISSILES}
    unexpected = [k for k in changed if k not in allowed]
    if unexpected:
        fails.append(f"unexpected ART changes {unexpected[:8]}")
    return fails


def main() -> int:
    if SRC_ART.stat().st_size != BASE_ART_SIZE or sha256_path(SRC_ART) != BASE_ART_SHA:
        raise SystemExit("live ART baseline mismatch")
    src_art = parse_big(SRC_ART.read_bytes())
    art = dict(src_art)
    flag = Image.open(io.BytesIO(src_art[FLAG_KEY])).convert("RGBA")
    donor = src_art[R11_W3D]

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(parents=True, exist_ok=True)

    for spec in MISSILES:
        sheet = make_skin(spec["body"], spec["nose"], spec["name"], flag)
        tga = make_tga32(sheet)
        tex_file = spec["tex"].rsplit("\\", 1)[-1]
        w3d = walk_rebuild(donor, tex_file)
        w3d = uniquify(w3d, b"IRQ_R11_M", spec["hier"])
        w3d = set_hlod_name(w3d, spec["hlod"])
        art[spec["tex"]] = tga
        art[spec["w3d"]] = w3d
        png_name = f"irq_{spec['slot'].lower()}_{spec['hlod']}.png"
        sheet.convert("RGB").save(OUT / png_name)
        sheet.convert("RGB").save(PREVIEW / png_name)
        (OUT / spec["tex"].rsplit("\\", 1)[-1]).write_bytes(tga)

    packed = build_big(art)
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_art.write_bytes(packed)
    extracted = parse_big(packed)

    stage = OUT / "LAST_WINS_EXTRACT"
    (stage / "ART").mkdir(parents=True)
    lines = ["# Last-wins missile skin audit", ""]
    for spec in MISSILES:
        w3d = extracted[spec["w3d"]]
        texp = stage / "ART" / spec["tex"].replace("\\", "/")
        w3p = stage / "ART" / spec["w3d"].replace("\\", "/")
        texp.parent.mkdir(parents=True, exist_ok=True)
        w3p.parent.mkdir(parents=True, exist_ok=True)
        texp.write_bytes(extracted[spec["tex"]])
        w3p.write_bytes(w3d)
        lines.append(
            f"Slot {spec['slot']} {spec['name']}: {spec['hlod']} -> {spec['tex'].rsplit(chr(92),1)[-1]} "
            f"hier={spec['hier'].decode()} textures={sorted(texture_names(w3d))} "
            f"HLod={hlod_name(w3d)}"
        )
    (stage / "AUDIT.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    fails = validate(extracted, src_art)
    fails.extend(f"ART {x}" for x in big_structure_ok(packed))
    art_sha = sha256_path(out_art)
    report = [
        "# Iraq missile skins B/C/D/H/I/J",
        "",
        "ART-only. 9P117, Al-Fahd500, slot cameos A-L, GENERIC-MISSILES unchanged.",
        "Each skin is a dedicated Irq_R11_M clone: BOOSTER=middle body, MISSILE01=nose.",
        "",
        f"- ART size: {out_art.stat().st_size}",
        f"- ART SHA256: {art_sha}",
        f"- ART files: {len(extracted)} (was {len(src_art)})",
        "- DATA changed: NO",
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
        "- B Al-Hussein II: white body / red nose + AL-HUSSEIN II",
        "- C Al-Samoud II: black body / red nose + AL-SAMOUD II",
        "- D Al-Abbas: red body / white nose + AL-ABBAS",
        "- H Al-Basrah: white body / black nose + AL-BASRAH",
        "- I Al-Nasir: orange body / red nose + AL-NASIR",
        "- J Al-Mansour: yellow body / red nose + AL-MANSOUR",
        "- Small Iraqi flag + English stencil on middle BOOSTER UVs",
        "- Nose uses MISSILE01 UVs on a separate color band",
        "- 9P117 / Al-Fahd500 / specter_missile_a-l / GENERIC-MISSILES byte-identical",
        "",
        "RUNTIME_TEST=NOT RUN",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=NO\n"
        "ART_CHANGED=YES\n"
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={out_art.stat().st_size}\n"
        f"ART_SHA256={art_sha}\n"
        f"ART_FILES={len(extracted)}\n"
        "MISSILES=B,C,D,H,I,J\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq missile skins B/C/D/H/I/J\n"
        "Place this complete replacement ART BIG in the game folder:\n"
        "  _SPEC_ART_ONE.big\n"
        "Keep the current DATA BIG; DATA did not change.\n"
        "9P117 and Al-Fahd500 skins are unchanged.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_SKINS_BCDHIJ.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
