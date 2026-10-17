#!/usr/bin/env python3
"""Pack the 8-missile Iraqi strategic family into live s SPEC BIGs.

Authority: /tmp/s-bigs/_SPEC_DATA_ONE.big and _SPEC_ART_ONE.big only.
Does not modify Iraq_R11ScudB, Iraq_Sarab7, or shared atlases in-place.
Clones W3Ds and writes private TGA textures. Includes Missile Factory
production bar for the new units.

Not an in-game runtime test.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path("/workspace")
S_DATA = Path("/tmp/s-bigs/_SPEC_DATA_ONE.big")
S_ART = Path("/tmp/s-bigs/_SPEC_ART_ONE.big")
OUT = ROOT / "patch/Release/SPECTER_IRAQ_STRATEGIC_MISSILES"
PATCH_DATA = ROOT / "patch/Data"
DONOR_W3D = Path("/tmp/iqmiss-donor")
DONOR_TEX = Path("/tmp/iqmiss-donor/textures")

FLAG_RED = (206, 17, 38, 255)
FLAG_WHITE = (255, 255, 255, 255)
FLAG_BLACK = (0, 0, 0, 255)
FLAG_GREEN = (0, 122, 61, 255)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes):
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


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


def to_crlf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


class Chunk:
    def __init__(self, cid: int, container: bool, children=None, payload=b""):
        self.cid = cid
        self.container = container
        self.children = children or []
        self.payload = payload


def parse_w3d_tree(blob: bytes, start: int = 0, end: int | None = None) -> list[Chunk]:
    if end is None:
        end = len(blob)
    chunks = []
    pos = start
    while pos + 8 <= end:
        cid, raw = struct.unpack_from("<II", blob, pos)
        sz = raw & 0x7FFFFFFF
        cont = bool(raw & 0x80000000)
        cs, ce = pos + 8, pos + 8 + sz
        if ce > end:
            break
        if cont:
            chunks.append(Chunk(cid, True, parse_w3d_tree(blob, cs, ce)))
        else:
            chunks.append(Chunk(cid, False, payload=blob[cs:ce]))
        pos = ce
    return chunks


def serialize_w3d(chunks: list[Chunk]) -> bytes:
    out = bytearray()
    for c in chunks:
        if c.container:
            body = serialize_w3d(c.children)
            out += struct.pack("<II", c.cid, len(body) | 0x80000000)
            out += body
        else:
            out += struct.pack("<II", c.cid, len(c.payload))
            out += c.payload
    return bytes(out)


def retarget_w3d(blob: bytes, mapping: dict[str, str]) -> bytes:
    tree = parse_w3d_tree(blob)

    def walk(chunks):
        for c in chunks:
            if c.container:
                walk(c.children)
            else:
                raw = c.payload
                for old, new in mapping.items():
                    ob = old.encode("latin1") + b"\x00"
                    nb = new.encode("latin1") + b"\x00"
                    if ob in raw:
                        raw = raw.replace(ob, nb)
                c.payload = raw

    walk(tree)
    return serialize_w3d(tree)


def _dxt1_block(b: bytes):
    c0, c1 = struct.unpack_from("<HH", b, 0)
    bits = struct.unpack_from("<I", b, 4)[0]

    def rgb565(c):
        r = ((c >> 11) & 31) * 255 // 31
        g = ((c >> 5) & 63) * 255 // 63
        bl = (c & 31) * 255 // 31
        return (r, g, bl, 255)

    cols = [rgb565(c0), rgb565(c1)]
    if c0 > c1:
        cols.append(tuple((2 * cols[0][i] + cols[1][i]) // 3 for i in range(4)))
        cols.append(tuple((cols[0][i] + 2 * cols[1][i]) // 3 for i in range(4)))
    else:
        cols.append(tuple((cols[0][i] + cols[1][i]) // 2 for i in range(4)))
        cols.append((0, 0, 0, 0))
    return [cols[(bits >> (2 * i)) & 3] for i in range(16)]


def decode_dds(blob: bytes) -> Image.Image:
    if blob[:4] != b"DDS ":
        raise ValueError("not DDS")
    h, w = struct.unpack_from("<II", blob, 12)
    fourcc = struct.unpack_from("<4s", blob, 84)[0]
    data = blob[128:]
    img = Image.new("RGBA", (w, h))
    px = img.load()
    bw, bh = w // 4, h // 4
    i = 0
    dxt1 = fourcc == b"DXT1"
    for by in range(bh):
        for bx in range(bw):
            if not dxt1:
                i += 8
            block = _dxt1_block(data[i : i + 8])
            i += 8
            for k, c in enumerate(block):
                x, y = bx * 4 + (k % 4), by * 4 + (k // 4)
                if x < w and y < h:
                    px[x, y] = c
    return img


def write_tga(img: Image.Image) -> bytes:
    img = img.convert("RGBA")
    w, h = img.size
    pixels = img.tobytes()
    header = bytearray(18)
    header[2] = 2
    header[12] = w & 255
    header[13] = (w >> 8) & 255
    header[14] = h & 255
    header[15] = (h >> 8) & 255
    header[16] = 32
    header[17] = 0x20
    bgra = bytearray(w * h * 4)
    for i in range(0, len(pixels), 4):
        bgra[i] = pixels[i + 2]
        bgra[i + 1] = pixels[i + 1]
        bgra[i + 2] = pixels[i]
        bgra[i + 3] = pixels[i + 3]
    return bytes(header) + bytes(bgra)


def find_art(art_map: dict[str, bytes], *candidates: str) -> bytes:
    lower = {k.replace("/", "\\").lower(): v for k, v in art_map.items()}
    for c in candidates:
        cl = c.replace("/", "\\").lower()
        if cl in lower:
            return lower[cl]
        stem = Path(cl.replace("\\", "/")).name
        for k, v in lower.items():
            if Path(k.replace("\\", "/")).name == stem:
                return v
    raise KeyError(f"missing ART {candidates}")


def load_tex_image(art_map, *cands) -> Image.Image:
    blob = find_art(art_map, *cands)
    if blob[:4] == b"DDS ":
        return decode_dds(blob)
    if len(blob) > 18 and blob[2] in (2, 10):
        w = blob[12] | (blob[13] << 8)
        h = blob[14] | (blob[15] << 8)
        bpp = blob[16]
        origin = blob[17]
        raw = blob[18 + blob[0] :]
        if bpp == 32:
            img = Image.frombytes("RGBA", (w, h), raw[: w * h * 4])
            r, g, b, a = img.split()
            img = Image.merge("RGBA", (b, g, r, a))
            if not (origin & 0x20):
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
            return img
        if bpp == 24:
            img = Image.frombytes("RGB", (w, h), raw[: w * h * 3])
            r, g, b = img.split()
            img = Image.merge("RGB", (b, g, r)).convert("RGBA")
            if not (origin & 0x20):
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
            return img
    raise ValueError(f"unreadable texture {cands}")


def paint_flag(img: Image.Image, box) -> None:
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, x1 = max(0, min(x0, x1)), min(img.size[0], max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(img.size[1], max(y0, y1))
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    if w < 6 or h < 4:
        return
    flag = Image.new("RGBA", (w, h), FLAG_WHITE)
    bh = max(1, h // 3)
    d = ImageDraw.Draw(flag)
    d.rectangle([0, 0, w, bh], fill=FLAG_RED)
    d.rectangle([0, bh, w, bh * 2], fill=FLAG_WHITE)
    d.rectangle([0, bh * 2, w, h], fill=FLAG_BLACK)
    cy = bh + max(1, bh // 2)
    rad = max(1, min(3, w // 12))
    for ox in (w // 4, w // 2, 3 * w // 4):
        d.ellipse([ox - rad, cy - rad, ox + rad, cy + rad], fill=FLAG_GREEN)
    img.paste(flag, (x0, y0), flag)


def paint_text(img: Image.Image, xy, text, fill=(255, 255, 220, 255)) -> None:
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    d.text(xy, text, fill=fill, font=font)


def paint_band(img: Image.Image, box, color) -> None:
    d = ImageDraw.Draw(img)
    d.rectangle(box, fill=color)


def uv_px(img, u0, v0, u1, v1):
    w, h = img.size
    return (int(u0 * w), int(v0 * h), int(u1 * w), int(v1 * h))


def recolor_fill(img: Image.Image, rgb, strength=0.50) -> Image.Image:
    base = img.convert("RGBA")
    r, g, b = rgb
    px = base.load()
    w, h = base.size
    out = Image.new("RGBA", base.size)
    opx = out.load()
    for y in range(h):
        for x in range(w):
            pr, pg, pb, pa = px[x, y]
            lum = (pr + pg + pb) / 3.0
            if lum < 50 or pa < 8:
                opx[x, y] = (pr, pg, pb, pa)
            else:
                nr = int(pr * (1 - strength) + r * strength * (lum / 255.0))
                ng = int(pg * (1 - strength) + g * strength * (lum / 255.0))
                nb = int(pb * (1 - strength) + b * strength * (lum / 255.0))
                opx[x, y] = (min(255, nr), min(255, ng), min(255, nb), pa)
    return out


def paint_variant(src: Image.Image, spec: dict) -> Image.Image:
    img = recolor_fill(src, spec["body_rgb"], spec.get("strength", 0.50))
    for box in spec.get("flags", []):
        paint_flag(img, box)
    for box, color in spec.get("bands", []):
        paint_band(img, box, color)
    for xy, text in spec.get("texts", []):
        paint_text(img, xy, text)
    return img


# ---------------------------------------------------------------------------
# Family table. Donors are live-s W3Ds. Animation names stay ORIGINAL.
# ---------------------------------------------------------------------------
FAMILY = [
    dict(
        key="AlHussein",
        obj="Iraq_AlHussein_New",
        label="AL-HUSSEIN",
        portrait="irq_9p117",
        draw="deploy",
        tel_models=("Irq_9P117", "Irq_9P117D", "Irq_9P117R"),
        msl_model="Irq_R11_M",
        anim="Irq_9P117.Irq_9P117",
        animd="Irq_9P117D.Irq_9P117D",
        launch="MISSILE",
        scale=1.30,
        pscale=1.28,
        geom=(46.0, 14.0, 25.0),
        shadow=55,
        health=550,
        cost=6000,
        time=45.0,
        dmg=2500,
        rad=110,
        rng=1600,
        mind=700,
        reload=110000,
        loc="Generic8x8Locomotor",
        ploc="R11SRBMLocomotor",
        body_rgb=(48, 72, 36),
        msl_rgb=(36, 56, 28),
        tel_tex="Art\\Textures\\Irq_9P117.dds",
        msl_tex="Art\\Textures\\GENERIC-MISSILES.dds",
        tel_map={
            "Irq_9P117.tga": "tex_tel",
            "GENERIC-MISSILES.dds": "tex_ontruck",
        },
        teld_map={"Irq_9P117D.tga": "tex_teld", "GENERIC-MISSILES.dds": "tex_ontruck"},
        telr_map={"Irq_9P117R.tga": "tex_telr"},
        msl_map={"GENERIC-MISSILES.dds": "tex_msl"},
        flags_tel_uv=[(0.68, 0.02, 0.86, 0.10), (0.04, 0.40, 0.18, 0.50)],
        flags_msl_uv=[(0.22, 0.46, 0.40, 0.56)],
        bands_tel_uv=[((0.02, 0.84, 0.98, 0.88), (230, 200, 40, 220))],
        bands_msl_uv=[((0.16, 0.26, 0.50, 0.30), (20, 20, 20, 255))],
        texts_tel_uv=[((0.70, 0.11), "AL-HUSSEIN")],
        texts_msl_uv=[((0.22, 0.58), "AL-HUSSEIN")],
        wreck_note="cloned Irq_9P117D / Irq_9P117R",
    ),
    dict(
        key="AlHijarah",
        obj="Iraq_AlHijarah_New",
        label="AL-HIJARAH",
        portrait="irq_9p117",
        draw="deploy",
        tel_models=("Irq_9P117", "Irq_9P117D", "Irq_9P117R"),
        msl_model="Irq_R11_M",
        anim="Irq_9P117.Irq_9P117",
        animd="Irq_9P117D.Irq_9P117D",
        launch="MISSILE",
        scale=1.25,
        pscale=1.22,
        geom=(44.0, 14.0, 24.0),
        shadow=52,
        health=550,
        cost=6500,
        time=48.0,
        dmg=2200,
        rad=90,
        rng=1720,
        mind=750,
        reload=95000,
        loc="Generic8x8Locomotor",
        ploc="R11SRBMLocomotor",
        body_rgb=(42, 48, 40),
        msl_rgb=(28, 32, 28),
        tel_tex="Art\\Textures\\Irq_9P117.dds",
        msl_tex="Art\\Textures\\GENERIC-MISSILES.dds",
        tel_map={"Irq_9P117.tga": "tex_tel", "GENERIC-MISSILES.dds": "tex_ontruck"},
        teld_map={"Irq_9P117D.tga": "tex_teld", "GENERIC-MISSILES.dds": "tex_ontruck"},
        telr_map={"Irq_9P117R.tga": "tex_telr"},
        msl_map={"GENERIC-MISSILES.dds": "tex_msl"},
        flags_tel_uv=[(0.68, 0.02, 0.86, 0.10)],
        flags_msl_uv=[(0.22, 0.46, 0.40, 0.56)],
        bands_tel_uv=[((0.02, 0.84, 0.98, 0.87), (230, 160, 20, 230))],
        bands_msl_uv=[((0.16, 0.22, 0.50, 0.27), (230, 140, 20, 255))],
        texts_tel_uv=[((0.70, 0.11), "AL-HIJARAH")],
        texts_msl_uv=[((0.22, 0.58), "AL-HIJARAH")],
        wreck_note="cloned Irq_9P117D / Irq_9P117R",
    ),
    dict(
        key="AlAbbas",
        obj="Iraq_AlAbbas_New",
        label="AL-ABBAS",
        portrait="irq_alabbas",
        draw="deploy",
        tel_models=("Irq_Abbas_L", "Irq_Abbas_L_D", "Irq_Abbas_L_R"),
        msl_model="Irq_AbbasM",
        anim="Irq_Abbas_L.Irq_Abbas_L",
        animd="Irq_Abbas_L_D.Irq_Abbas_L_D",
        launch="MISSILE",
        scale=1.40,
        pscale=1.38,
        geom=(52.0, 16.0, 28.0),
        shadow=60,
        health=600,
        cost=7000,
        time=52.0,
        dmg=1800,
        rad=85,
        rng=2200,
        mind=800,
        reload=100000,
        loc="Generic8x8Locomotor",
        ploc="R11SRBMLocomotor",
        body_rgb=(168, 148, 96),
        msl_rgb=(150, 132, 80),
        tel_tex="Art\\Textures\\Irq_AbbasLauncher.dds",
        msl_tex="Art\\Textures\\Irq_AbbasMissile.dds",
        tel_map={"Irq_AbbasLauncher.tga": "tex_tel", "Irq_AbbasMissile.dds": "tex_ontruck"},
        teld_map={"Irq_AbbasLauncherD.tga": "tex_teld", "Irq_AbbasMissile.dds": "tex_ontruck"},
        telr_map={"Irq_AbbasLauncher_R.tga": "tex_telr", "Irq_Scud.tga": "tex_ontruck"},
        msl_map={"Irq_AbbasMissile.tga": "tex_msl"},
        flags_tel_uv=[(0.52, 0.02, 0.72, 0.10), (0.04, 0.40, 0.18, 0.50)],
        flags_msl_uv=[(0.84, 0.40, 0.97, 0.55)],
        bands_tel_uv=[((0.02, 0.84, 0.98, 0.87), (30, 70, 30, 220))],
        bands_msl_uv=[((0.81, 0.12, 0.99, 0.18), (30, 70, 30, 255))],
        texts_tel_uv=[((0.54, 0.11), "AL-ABBAS")],
        texts_msl_uv=[((0.84, 0.57), "AL-ABBAS")],
        wreck_note="cloned Irq_Abbas_L_D / Irq_Abbas_L_R",
    ),
    dict(
        key="Badr2000",
        obj="Iraq_Badr2000_New",
        label="BADR-2000",
        portrait="rus_iskanderr",
        draw="deploy",
        tel_models=("RUS_9K720K", "RUS_9K720KD", "RUS_9K720KD"),
        msl_model="Hwasong7",
        anim="RUS_9K720K.RUS_9K720K",
        animd="RUS_9K720KD.RUS_9K720KD",
        launch="Missile",
        scale=1.42,
        pscale=1.40,
        geom=(58.0, 16.0, 27.0),
        shadow=62,
        health=700,
        cost=8500,
        time=60.0,
        dmg=2800,
        rad=120,
        rng=2100,
        mind=800,
        reload=130000,
        loc="Generic8x8Locomotor",
        ploc="R11SRBMLocomotor",
        body_rgb=(24, 36, 24),
        msl_rgb=(20, 20, 22),
        tel_tex="Art\\Textures\\RUS_9K720K.dds",
        msl_tex="Art\\Textures\\AAM-GENTEX.dds",
        tel_map={
            "RUS_9K720K.tga": "tex_tel",
            "RUS_9K720.dds": "tex_tel",
            "AAM-GENTEX.dds": "tex_ontruck",
        },
        teld_map={
            "RUS_9K720KD.tga": "tex_teld",
            "RUS_9K720D.dds": "tex_teld",
            "AAM-GENTEX.dds": "tex_ontruck",
        },
        telr_map={"RUS_9K720KD.tga": "tex_telr", "RUS_9K720D.dds": "tex_telr"},
        msl_map={"AAM-GENTEX.dds": "tex_msl"},
        flags_tel_uv=[(0.54, 0.02, 0.74, 0.10)],
        flags_msl_uv=[(0.60, 0.28, 0.78, 0.40)],
        bands_tel_uv=[
            ((0.04, 0.38, 0.96, 0.41), (180, 30, 30, 220)),
            ((0.04, 0.41, 0.96, 0.43), (220, 180, 30, 220)),
        ],
        bands_msl_uv=[((0.56, 0.14, 0.84, 0.20), (180, 30, 30, 255))],
        texts_tel_uv=[((0.56, 0.11), "BADR-2000")],
        texts_msl_uv=[((0.60, 0.42), "BADR-2000")],
        wreck_note="no dedicated R W3D; damaged/wreck use cloned RUS_9K720KD",
    ),
    dict(
        key="AlSamoud",
        obj="Iraq_AlSamoud_New",
        label="AL-SAMOUD",
        portrait="irq_sarab7",
        draw="sarab",
        tel_models=("Irq_Sarab7", "Irq_Sarab7", "Irq_Sarab7R"),
        msl_model="Irq_R11_M",
        anim="Irq_Sarab7.Irq_Sarab7",
        animd="Irq_Sarab7.Irq_Sarab7",
        launch="MISSILE",
        scale=0.80,
        pscale=0.82,
        geom=(12.0, 8.0, 8.0),
        shadow=36,
        health=400,
        cost=3000,
        time=28.0,
        dmg=800,
        rad=40,
        rng=480,
        mind=180,
        reload=45000,
        loc="Generic8x8Locomotor",
        ploc="R11SRBMLocomotor",
        body_rgb=(90, 110, 55),
        msl_rgb=(200, 200, 190),
        tel_tex="Art\\Textures\\Irq_Sarab7.dds",
        msl_tex="Art\\Textures\\GENERIC-MISSILES.dds",
        tel_map={"Irq_Sarab7.dds": "tex_tel", "AAM-GENTEX.dds": "tex_ontruck"},
        teld_map={"Irq_Sarab7.dds": "tex_teld", "AAM-GENTEX.dds": "tex_ontruck"},
        telr_map={"Irq_Sarab7R.tga": "tex_telr"},
        msl_map={"GENERIC-MISSILES.dds": "tex_msl"},
        flags_tel_uv=[(0.76, 0.06, 0.94, 0.16)],
        flags_msl_uv=[(0.22, 0.46, 0.40, 0.56)],
        bands_tel_uv=[((0.56, 0.36, 0.72, 0.48), (210, 190, 80, 200))],
        bands_msl_uv=[
            ((0.16, 0.22, 0.50, 0.27), (220, 190, 40, 255)),
            ((0.16, 0.70, 0.50, 0.76), (230, 230, 220, 255)),
        ],
        texts_tel_uv=[((0.76, 0.17), "AL-SAMOUD")],
        texts_msl_uv=[((0.22, 0.58), "AL-SAMOUD")],
        wreck_note="cloned Irq_Sarab7R; damaged uses painted Irq_Sarab7 (donor has no D W3D)",
    ),
    dict(
        key="Ababil100",
        obj="Iraq_Ababil100_New",
        label="ABABIL-100",
        portrait="irq_lamiaa",
        draw="lamia",
        tel_models=("Irq_Lamiaa", "Irq_Lamiaa", "Irq_Lamiaa"),
        msl_model="Irq_Alraad2M",
        anim="Irq_Lamiaa.Irq_Lamiaa",
        animd="Irq_Lamiaa.Irq_Lamiaa",
        launch="Missile",
        scale=0.75,
        pscale=0.76,
        geom=(11.0, 7.0, 7.0),
        shadow=32,
        health=350,
        cost=2500,
        time=24.0,
        dmg=500,
        rad=32,
        rng=420,
        mind=120,
        reload=32000,
        loc="Zil-375V8",
        ploc="PGMRaad2RocketLocomotor",
        body_rgb=(176, 150, 88),
        msl_rgb=(210, 205, 190),
        tel_tex="Art\\Textures\\Irq_Lamiaa.dds",
        msl_tex="Art\\Textures\\AAM-GENTEX.dds",
        tel_map={"Irq_Lamiaa.dds": "tex_tel", "Irq_Quds5.dds": "tex_ontruck"},
        teld_map={"Irq_Lamiaa.dds": "tex_teld", "Irq_Quds5.dds": "tex_ontruck"},
        telr_map={"Irq_Lamiaa.dds": "tex_telr", "Irq_Quds5.dds": "tex_ontruck"},
        msl_map={"AAM-GENTEX.dds": "tex_msl"},
        flags_tel_uv=[(0.76, 0.05, 0.94, 0.15)],
        flags_msl_uv=[(0.08, 0.40, 0.28, 0.52)],
        bands_tel_uv=[((0.46, 0.32, 0.66, 0.46), (70, 90, 40, 200))],
        bands_msl_uv=[((0.04, 0.22, 0.40, 0.28), (255, 255, 255, 255))],
        texts_tel_uv=[((0.76, 0.16), "ABABIL-100")],
        texts_msl_uv=[((0.08, 0.54), "ABABIL-100")],
        wreck_note="Irq_Lamiaa has no D/R W3D; damaged/wreck reuse painted clones of Irq_Lamiaa",
    ),
    dict(
        key="Tammuz1",
        obj="Iraq_Tammuz1_New",
        label="TAMMUZ-1",
        portrait="irq_mslbrg",
        draw="deploy",
        tel_models=("Iraq_Alhusain_L", "Iraq_Alhusain_L", "Iraq_Alhusain_L"),
        msl_model="Iraq_Alhusain_M",
        anim="Iraq_Alhusain_L.Iraq_Alhusain_L",
        animd="Iraq_Alhusain_L.Iraq_Alhusain_L",
        launch="MISSILE",
        scale=1.60,
        pscale=1.55,
        geom=(64.0, 18.0, 30.0),
        shadow=68,
        health=900,
        cost=12000,
        time=75.0,
        dmg=4000,
        rad=150,
        rng=2900,
        mind=900,
        reload=160000,
        loc="Generic8x8Locomotor_H",
        ploc="R11SRBMLocomotor",
        body_rgb=(16, 22, 16),
        msl_rgb=(220, 210, 180),
        tel_tex="Art\\Textures\\Irq_Alhussien.dds",
        msl_tex="Art\\Textures\\irq_projectiles_c.dds",
        tel_map={"Irq_Alhussien.tga": "tex_tel"},
        teld_map={"Irq_Alhussien.tga": "tex_teld"},
        telr_map={"Irq_Alhussien.tga": "tex_telr"},
        msl_map={"irq_projectiles_c.tga": "tex_msl"},
        flags_tel_uv=[(0.52, 0.02, 0.72, 0.10)],
        flags_msl_uv=[(0.40, 0.42, 0.62, 0.56)],
        bands_tel_uv=[((0.04, 0.56, 0.96, 0.64), (220, 210, 180, 180))],
        bands_msl_uv=[((0.08, 0.18, 0.92, 0.40), (20, 20, 20, 255))],
        texts_tel_uv=[((0.54, 0.11), "TAMMUZ-1")],
        texts_msl_uv=[((0.42, 0.58), "TAMMUZ-1")],
        wreck_note="Iraq_Alhusain_L has no D/R W3D in live ART; damaged/wreck reuse darkened clones",
    ),
    dict(
        key="AlAbid",
        obj="Iraq_AlAbid_New",
        label="AL-ABID",
        portrait="rus_rs24",
        draw="deploy",
        tel_models=("RUS_RS24", "RUS_RS24_D", "RUS_RS24_R"),
        msl_model="RUS_RS24M",
        anim="RUS_RS24.RUS_RS24",
        animd="RUS_RS24_D.RUS_RS24_D",
        launch="MISSILE",
        scale=1.70,
        pscale=1.68,
        geom=(70.0, 19.0, 32.0),
        shadow=72,
        health=1100,
        cost=15000,
        time=90.0,
        dmg=5500,
        rad=180,
        rng=3900,
        mind=1000,
        reload=190000,
        loc="Generic8x8Locomotor_H",
        ploc="R11SRBMLocomotor",
        body_rgb=(12, 14, 18),
        msl_rgb=(18, 18, 20),
        tel_tex="Art\\Textures\\RUS_RS24.dds",
        msl_tex="Art\\Textures\\irq_projectiles_c.dds",
        tel_map={"RUS_RS24.tga": "tex_tel"},
        teld_map={"RUS_RS24D.tga": "tex_teld"},
        telr_map={"RUS_RS24_R.tga": "tex_telr"},
        msl_map={"irq_projectiles_c.tga": "tex_msl"},
        flags_tel_uv=[(0.52, 0.02, 0.72, 0.10)],
        flags_msl_uv=[(0.40, 0.42, 0.62, 0.56)],
        bands_tel_uv=[((0.04, 0.38, 0.96, 0.41), (240, 240, 240, 200))],
        bands_msl_uv=[
            ((0.08, 0.08, 0.92, 0.16), (240, 240, 240, 255)),
            ((0.08, 0.70, 0.92, 0.78), (240, 240, 240, 255)),
        ],
        texts_tel_uv=[((0.56, 0.11), "AL-ABID")],
        texts_msl_uv=[((0.44, 0.58), "AL-ABID")],
        wreck_note="cloned RUS_RS24_D / RUS_RS24_R",
    ),
]


def asset_names(spec):
    k = spec["key"]
    return {
        "tel": f"IQ_{k}TEL",
        "teld": f"IQ_{k}TELD",
        "telr": f"IQ_{k}TELR",
        "msl": f"IQ_{k}MSL",
        "tex_tel": f"IQ_{k}TEL.tga",
        "tex_teld": f"IQ_{k}TELD.tga",
        "tex_telr": f"IQ_{k}TELR.tga",
        "tex_msl": f"IQ_{k}MSL.tga",
        "tex_ontruck": f"IQ_{k}OTK.tga",
        "weapon": f"Weapon_Iraq_{k}_New",
        "proj": f"Projectile_Iraq_{k}_New",
        "hulk": f"{spec['obj']}_Hulk",
        "ocl": f"OCL_{spec['obj']}_Death",
        "btn": f"Command_ConstructIraq_{k}_New",
        "cmdset": "Iraq_StrategicMissileNewCommandSet",
    }


def _uv_flags(img, uvs):
    return [uv_px(img, *box) for box in uvs]


def _uv_bands(img, items):
    out = []
    for box, color in items:
        out.append((uv_px(img, *box), color))
    return out


def _uv_texts(img, items):
    w, h = img.size
    return [((int(u * w), int(v * h)), text) for (u, v), text in items]


def deploy_draw(spec, names) -> str:
    m, md = names["tel"], names["teld"]
    anim, animd = spec["anim"], spec["animd"]
    launch = spec["launch"]
    return f"""  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = Yes
    ProjectileBoneFeedbackEnabledSlots = PRIMARY
    DefaultConditionState
      Model                           = {m}
      WeaponLaunchBone                = PRIMARY {launch}
      WeaponFireFXBone                = PRIMARY {launch}
      Turret                          = Turrettt
      Flags                           = START_FRAME_FIRST
    End
    ConditionState                    = REALLYDAMAGED
      Model                           = {md}
      WeaponLaunchBone                = PRIMARY {launch}
      WeaponFireFXBone                = PRIMARY {launch}
      Turret                          = Turrettt
      Flags                           = START_FRAME_FIRST
    End
    ConditionState                    = RUBBLE
      Model                           = {md}
      WeaponLaunchBone                = PRIMARY {launch}
      WeaponFireFXBone                = PRIMARY {launch}
      Flags                           = START_FRAME_FIRST
    End
    ConditionState    = MOVING
      Animation       = {anim}
      AnimationMode   = ONCE_BACKWARDS
      Flags           = START_FRAME_FIRST
    End
    AliasConditionState = MOVING BETWEEN_FIRING_SHOTS_A
    AliasConditionState = BETWEEN_FIRING_SHOTS_A
    ConditionState    = REALLYDAMAGED MOVING
      Model           = {md}
      Animation       = {animd}
      AnimationMode   = ONCE_BACKWARDS
      Flags           = START_FRAME_FIRST
    End
    ConditionState    = UNPACKING
      Animation       = {anim}
      AnimationMode   = ONCE
    End
    AliasConditionState = UNPACKING BETWEEN_FIRING_SHOTS_A
    ConditionState    = REALLYDAMAGED UNPACKING
      Model           = {md}
      Animation       = {animd}
      AnimationMode   = ONCE
    End
    ConditionState    = PACKING
      Animation       = {anim}
      AnimationMode   = ONCE_BACKWARDS
      Flags           = START_FRAME_LAST
    End
    AliasConditionState = PACKING BETWEEN_FIRING_SHOTS_A
    ConditionState    = REALLYDAMAGED PACKING
      Model           = {md}
      Animation       = {animd}
      AnimationMode   = MANUAL
    End
    ConditionState  = DEPLOYED
      Animation       = {anim}
      AnimationMode   = ONCE
      Flags           = START_FRAME_LAST
    End
    AliasConditionState = DEPLOYED FIRING_A
    AliasConditionState = DEPLOYED BETWEEN_FIRING_SHOTS_A
    AliasConditionState = DEPLOYED RELOADING_A
    ConditionState  = DEPLOYED REALLYDAMAGED
      Model           = {md}
      Animation       = {animd}
      AnimationMode   = ONCE
      Flags           = START_FRAME_LAST
    End
    TrackMarks = EXTireTrack.tga
    Dust = ScudLauncherDust
    DirtSpray = RocketBuggyDirtSpray
    LeftFrontTireBone = Tire01
    RightFrontTireBone = Tire05
    LeftRearTireBone = Tire04
    RightRearTireBone = Tire08
    MidLeftFrontTireBone = Tire02
    MidRightFrontTireBone = Tire06
    MidLeftRearTireBone = Tire03
    MidRightRearTireBone = Tire07
    TireRotationMultiplier = 0.2
  End
"""


def sarab_draw(spec, names) -> str:
    m, md = names["tel"], names["teld"]
    anim = spec["anim"]
    launch = spec["launch"]
    return f"""  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = Yes
    ProjectileBoneFeedbackEnabledSlots = PRIMARY
    DefaultConditionState
      Model                           = {m}
      WeaponLaunchBone                = PRIMARY {launch}
      WeaponFireFXBone                = PRIMARY WeaponFX
      Turret                          = Turrettt
      Flags                           = START_FRAME_FIRST
    End
    ConditionState                    = RUBBLE
      Model                           = {md}
      WeaponLaunchBone                = PRIMARY {launch}
      WeaponFireFXBone                = PRIMARY WeaponFX
      Flags                           = START_FRAME_FIRST
    End
    ConditionState    = MOVING
      Animation       = {anim}
      AnimationMode   = ONCE_BACKWARDS
      Flags           = START_FRAME_FIRST
    End
    AliasConditionState = MOVING BETWEEN_FIRING_SHOTS_A
    ConditionState    = UNPACKING
      Animation       = {anim}
      AnimationMode   = ONCE
    End
    ConditionState    = PACKING
      Animation       = {anim}
      AnimationMode   = ONCE_BACKWARDS
      Flags           = START_FRAME_LAST
    End
    ConditionState  = DEPLOYED
      Animation       = {anim}
      AnimationMode   = ONCE
      Flags           = START_FRAME_LAST
    End
    AliasConditionState = DEPLOYED FIRING_A
    AliasConditionState = DEPLOYED BETWEEN_FIRING_SHOTS_A
    TrackMarks = EXTireTrack.tga
    Dust = ScudLauncherDust
    LeftFrontTireBone = Tire01
    RightFrontTireBone = Tire05
    LeftRearTireBone = Tire04
    RightRearTireBone = Tire08
    TireRotationMultiplier = 0.2
  End
"""


def lamia_draw(spec, names) -> str:
    m, md = names["tel"], names["teld"]
    launch = spec["launch"]
    return f"""  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = Yes
    ProjectileBoneFeedbackEnabledSlots = PRIMARY
    ExtraPublicBone    = Missile
    DefaultConditionState
      Model              = {m}
      WeaponLaunchBone   = PRIMARY   {launch}
      WeaponFireFXBone   = PRIMARY   WeaponFX
      Turret             = TurretF
    End
    ConditionState       = REALLYDAMAGED
      Model              = {md}
      WeaponLaunchBone   = PRIMARY   {launch}
      WeaponFireFXBone   = PRIMARY   WeaponFX
      Turret             = TurretF
    End
    ConditionState       = RUBBLE
      Model              = {md}
      WeaponLaunchBone   = PRIMARY   {launch}
      WeaponFireFXBone   = PRIMARY   WeaponFX
    End
    TrackMarks              = EXTireTrack.tga
    LeftFrontTireBone           = Tire01
    RightFrontTireBone          = Tire02
    MidLeftRearTireBone         = Tire03
    MidRightRearTireBone        = Tire04
    LeftRearTireBone            = Tire05
    RightRearTireBone           = Tire06
    TireRotationMultiplier      = 0.2
    Dust                    = RocketBuggyDust
    DirtSpray               = RocketBuggyDirtSpray
  End
"""


def tel_ini(spec, names) -> str:
    draws = {"deploy": deploy_draw, "sarab": sarab_draw, "lamia": lamia_draw}
    draw = draws[spec["draw"]](spec, names)
    ai = ""
    if spec["draw"] == "lamia":
        ai = """  Behavior = AIUpdateInterface ModuleTag_03FA3
    Turret
      TurretTurnRate = 80
      TurretPitchRate = 30
      FirePitch = 45
      AllowsPitch = Yes
      ControlledWeaponSlots = PRIMARY
    End
    AutoAcquireEnemiesWhenIdle = No
  End
"""
    else:
        ai = """  Behavior = DeployStyleAIUpdate ModuleTag_04
    AutoAcquireEnemiesWhenIdle = No
    PackTime = 6555
    UnpackTime = 6555
    TurretsFunctionOnlyWhenDeployed = Yes
    TurretsMustCenterBeforePacking = Yes
    ManualDeployAnimations = Yes
  End
"""
    return f"""
; SPECTER cloned Iraqi strategic TEL - {spec['label']}
; Geometry donor only. Does not replace Iraq_R11ScudB / Iraq_Sarab7.
Object {spec['obj']}
Scale = {spec['scale']:.2f}
  SelectPortrait         = {spec['portrait']}
  ButtonImage            = {spec['portrait']}
{draw}  DisplayName      = OBJECT:{spec['obj']}
  Side = Iraq
  EditorSorting   = VEHICLE
  TransportSlotCount = 10
  WeaponSet
    Conditions = None
    Weapon = PRIMARY   {names['weapon']}
  End
  ArmorSet
    Conditions      = None
    Armor           = TruckArmor
    DamageFX        = TankDamageFX
  End
  BuildCost       = {spec['cost']}
  BuildTime       = {spec['time']:.1f}
  VisionRange     = 200
  ShroudClearingRange = 150
  ExperienceValue = 50 100 200 400
  ExperienceRequired = 0 400 600 1000
  IsTrainable = Yes
  CrusherLevel           = 2
  CrushableLevel         = 2
  CommandSet    = {names['cmdset']}
  VoiceSelect = ScudLauncherVoiceSelect
  VoiceMove = ScudLauncherVoiceMove
  VoiceGuard = ScudLauncherVoiceMove
  VoiceAttack = ScudLauncherVoiceAttack
  SoundMoveStart = ScudLauncherMoveStart
  RadarPriority = UNIT
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
  Body = ActiveBody ModuleTag_02
    MaxHealth       = {spec['health']:.1f}
    InitialHealth   = {spec['health']:.1f}
    SubdualDamageCap = 480
    SubdualDamageHealRate = 500
    SubdualDamageHealAmount = 50
  End
{ai}  Locomotor = SET_NORMAL {spec['loc']}
  Behavior = PhysicsBehavior ModuleTag_05
    Mass = 400.0
  End
  Behavior = SlowDeathBehavior ModuleTag_L8F09
    DeathTypes = ALL -CRUSHED -SPLATTED
    ProbabilityModifier = 50
    DestructionDelay = 100
    FX  = INITIAL  FX_CrusaderCatchFire
    OCL = FINAL    {names['ocl']}
    FX  = FINAL    FX_HE_ALBM_Explosion
  End
  Behavior = FlammableUpdate ModuleTag_21VHN
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
  End
  Behavior = ProductionUpdate ModuleTag_12
    MaxQueueEntries = 1
  End
  Geometry = BOX
  GeometryMajorRadius = {spec['geom'][0]:.1f}
  GeometryMinorRadius = {spec['geom'][1]:.1f}
  GeometryHeight = {spec['geom'][2]:.1f}
  GeometryIsSmall = No
  Shadow = SHADOW_VOLUME
  ShadowSizeX = {spec['shadow']}
End
"""


def hulk_ini(spec, names) -> str:
    return f"""
Object {names['hulk']}
Scale = {spec['scale']:.2f}
  Draw = W3DModelDraw ModuleTag_01
    ConditionState = NONE
      Model = {names['telr']}
    End
  End
  EditorSorting   = DEBRIS
  KindOf =  NO_COLLIDE HULK
  Behavior = PhysicsBehavior ModuleTag_03
    Mass = 100.0
    AllowBouncing = Yes
    KillWhenRestingOnGround = Yes
  End
  Behavior = LifetimeUpdate ModuleTag_04
    MinLifetime = 9500
    MaxLifetime = 9600
  End
  Behavior = SlowDeathBehavior ModuleTag_05
    SinkDelay         = 9500
    SinkRate          = 2
    DestructionDelay  = 11000
  End
End
"""


def proj_ini(spec, names) -> str:
    return f"""
Object {names['proj']}
Scale = {spec['pscale']:.2f}
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    ConditionState
      Model = {names['msl']}
      ParticleSysBone = ENGINE01 LRBM_Trail
    End
  End
  DisplayName      = OBJECT:{spec['obj']}
  EditorSorting   = SYSTEM
  VisionRange = 80.0
  ArmorSet
    Conditions      = None
    Armor           = SRBMArmor
    DamageFX        = None
  End
  SoundAmbient  = GenericMissileAmbientLoop
  KindOf = PROJECTILE BALLISTIC_MISSILE
  Body = ActiveBody ModuleTag_02
    MaxHealth       = 300.0
    InitialHealth   = 300.0
  End
  Behavior = InstantDeathBehavior DeathModuleTag_01
    DeathTypes = NONE +DETONATED
  End
  Behavior = InstantDeathBehavior DeathModuleTag_02
    DeathTypes = NONE +LASERED
    FX         = FX_GenericMissileDisintegrate
    OCL        = OCL_GenericMissileDisintegrate
  End
  Behavior = InstantDeathBehavior DeathModuleTag_03
    DeathTypes = ALL -LASERED -DETONATED
    FX         = FX_GenericMissileDeath
  End
  Behavior = PhysicsBehavior ModuleTag_04
    Mass = 15
  End
  Locomotor = SET_NORMAL {spec['ploc']}
  Geometry            = Cylinder
  GeometryMajorRadius = 4.0
  GeometryHeight      = 4.0
  GeometryIsSmall     = Yes
  Shadow = SHADOW_DECAL
End
"""


def weapon_ini(spec, names) -> str:
    return f"""
Weapon {names['weapon']}
  PrimaryDamage               = {spec['dmg']:.1f}
  PrimaryDamageRadius         = {spec['rad']:.1f}
  SecondaryDamage             = {spec['dmg'] * 0.08:.1f}
  SecondaryDamageRadius       = {spec['rad'] * 0.35:.1f}
  ScatterRadius               = 80
  AttackRange                 = {spec['rng']:.1f}
  MinimumAttackRange          = {spec['mind']:.1f}
  PreAttackDelay              = 500
  PreAttackType               = PER_SHOT
  DamageType                  = ARMOR_PIERCING
  DeathType                   = EXPLODED
  FireFX                      = FX_IskanderFiringEffects
  ProjectileObject            = {names['proj']}
  ProjectileDetonationFX      = FX_SmallSRBM_Explosion
  RadiusDamageAffects         = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  FireSound                   = Iskander_Firing
  WeaponSpeed                 = 280
  AcceptableAimDelta          = 360
  DelayBetweenShots           = 3000
  ClipSize                    = 1
  ClipReloadTime              = {spec['reload']}
  ShockWaveAmount             = 80.0
  ShockWaveRadius             = {spec['rad']:.1f}
  ShockWaveTaperOff           = 0.33
End
"""


def ocl_ini(spec, names) -> str:
    return f"""
ObjectCreationList {names['ocl']}
  CreateObject
    ObjectNames = {names['hulk']}
    Count = 1
  End
End
"""


def button_block(spec, names) -> str:
    return (
        f"CommandButton {names['btn']}\r\n"
        f"  Command       = UNIT_BUILD\r\n"
        f"  Object        = {spec['obj']}\r\n"
        f"  TextLabel     = CONTROLBAR:Construct{spec['obj']}\r\n"
        f"  ButtonImage   = {spec['portrait']}\r\n"
        f"  ButtonBorderType = BUILD\r\n"
        f"  DescriptLabel = CONTROLBAR:ToolTip{spec['obj']}\r\n"
        f"End\r\n"
    )


def csf_append(csf: bytes, labels: dict[str, str]) -> bytes:
    if csf[:4] != b" FSC":
        raise SystemExit(f"unexpected CSF magic {csf[:4]!r}")
    magic, ver, nlab, nstr, unused, lang = struct.unpack_from("<4sIIIII", csf, 0)
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
    hdr = struct.pack("<4sIIIII", magic, ver, nlab + added, nstr + added, unused, lang)
    return hdr + csf[24:] + extra


def inject_core_buttons(text: str, blocks: str) -> str:
    if "Command_ConstructIraq_AlHussein_New" in text:
        raise SystemExit("strategic missile buttons already in CommandButton.ini")
    if "\r\n" not in text:
        raise SystemExit("s CommandButton.ini is not CRLF")
    if not text.endswith("\r\n"):
        text += "\r\n"
    return text + "\r\n" + blocks


def inject_core_mf_button(text: str) -> str:
    if "CommandButton Command_ConstructIraq_MissileFactory" in text:
        return text
    block = (
        "CommandButton Command_ConstructIraq_MissileFactory\r\n"
        "  Command          = DOZER_CONSTRUCT\r\n"
        "  Object           = Iraq_MissileFactory\r\n"
        "  TextLabel        = CONTROLBAR:ConstructIraqMissileFactory\r\n"
        "  ButtonImage      = irq_mslbrg\r\n"
        "  ButtonBorderType = BUILD\r\n"
        "  DescriptLabel    = CONTROLBAR:ToolTipIraqBuildMissileFactory\r\n"
        "End\r\n"
    )
    if not text.endswith("\r\n"):
        text += "\r\n"
    return text + "\r\n" + block


def patch_vt72b_slot14(text: str) -> str:
    old = (
        "  13 = Command_ConstructIraq_HeavyAirBase\r\n"
        "  14 = Command_DisarmMinesAtPosition\r\n"
        "  15 = Command_ConstructIraq_Abbas_AI"
    )
    new = (
        "  13 = Command_ConstructIraq_HeavyAirBase\r\n"
        "  14 = Command_ConstructIraq_MissileFactory\r\n"
        "  15 = Command_ConstructIraq_Abbas_AI"
    )
    if old not in text:
        if "14 = Command_ConstructIraq_MissileFactory" in text:
            return text
        raise SystemExit("Iraq_VT72BCommandSet slot 13-15 context not found")
    return text.replace(old, new, 1)


def resolve_map(names, mapping):
    out = {}
    for old, newkey in mapping.items():
        out[old] = names[newkey] if newkey in names else newkey
    return out


def build_private_art(art_map: dict[str, bytes]) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for spec in FAMILY:
        names = asset_names(spec)
        tel_img = load_tex_image(art_map, spec["tel_tex"])
        msl_img = load_tex_image(art_map, spec["msl_tex"])
        tel_painted = paint_variant(
            tel_img,
            {
                "body_rgb": spec["body_rgb"],
                "flags": _uv_flags(tel_img, spec["flags_tel_uv"]),
                "bands": _uv_bands(tel_img, spec["bands_tel_uv"]),
                "texts": _uv_texts(tel_img, spec["texts_tel_uv"]),
                "strength": 0.48,
            },
        )
        msl_painted = paint_variant(
            msl_img,
            {
                "body_rgb": spec["msl_rgb"],
                "flags": _uv_flags(msl_img, spec["flags_msl_uv"]),
                "bands": _uv_bands(msl_img, spec["bands_msl_uv"]),
                "texts": _uv_texts(msl_img, spec["texts_msl_uv"]),
                "strength": 0.42,
            },
        )
        tel_d = ImageEnhance.Contrast(tel_painted).enhance(0.75)
        tel_d = ImageEnhance.Brightness(tel_d).enhance(0.70)
        tel_r = ImageEnhance.Color(tel_d).enhance(0.35)
        tel_r = ImageEnhance.Brightness(tel_r).enhance(0.55)
        out[f"Art\\Textures\\{names['tex_tel']}"] = write_tga(tel_painted)
        out[f"Art\\Textures\\{names['tex_teld']}"] = write_tga(tel_d)
        out[f"Art\\Textures\\{names['tex_telr']}"] = write_tga(tel_r)
        out[f"Art\\Textures\\{names['tex_msl']}"] = write_tga(msl_painted)
        out[f"Art\\Textures\\{names['tex_ontruck']}"] = write_tga(msl_painted)

        src_tel, src_teld, src_telr = spec["tel_models"]
        clones = [
            (f"Art\\W3D\\{src_tel}.W3D", names["tel"], spec["tel_map"]),
            (f"Art\\W3D\\{src_teld}.W3D", names["teld"], spec["teld_map"]),
            (f"Art\\W3D\\{src_telr}.W3D", names["telr"], spec["telr_map"]),
        ]
        for src_path, dest_name, mapping in clones:
            src = find_art(art_map, src_path)
            cloned = retarget_w3d(src, resolve_map(names, mapping))
            out[f"Art\\W3D\\{dest_name}.W3D"] = cloned
        msl_src = find_art(art_map, f"Art\\W3D\\{spec['msl_model']}.W3D")
        out[f"Art\\W3D\\{names['msl']}.W3D"] = retarget_w3d(msl_src, resolve_map(names, spec["msl_map"]))
        print("ART", spec["key"], names["tel"], names["msl"], spec["wreck_note"])
    return out


def write_source_inis():
    tel_parts = ["; SPECTER Iraqi strategic missile family - new TEL objects only.\n"]
    hulk_parts = ["; SPECTER Iraqi strategic missile family hulks.\n"]
    proj_parts = ["; SPECTER Iraqi strategic missile family projectiles.\n"]
    weap_parts = ["; SPECTER Iraqi strategic missile family - new weapons only.\n"]
    ocl_parts = ["; SPECTER Iraqi strategic missile family death OCLs.\n"]
    for spec in FAMILY:
        names = asset_names(spec)
        tel_parts.append(tel_ini(spec, names))
        hulk_parts.append(hulk_ini(spec, names))
        proj_parts.append(proj_ini(spec, names))
        weap_parts.append(weapon_ini(spec, names))
        ocl_parts.append(ocl_ini(spec, names))
    files = {
        PATCH_DATA / "INI/Object/Specter/Iraq Army/Wheeled/Iraq_StrategicMissiles_New.ini": "\n".join(tel_parts),
        PATCH_DATA / "INI/Object/Specter/Iraq Army/Hulk/Iraq_StrategicMissile_Hulks.ini": "\n".join(hulk_parts),
        PATCH_DATA / "INI/Object/Specter/Iraq Army/Iraq_StrategicMissile_Projectiles.ini": "\n".join(proj_parts),
        PATCH_DATA / "INI/Weapon_Iraq_StrategicMissiles.ini": "\n".join(weap_parts),
        PATCH_DATA / "INI/ObjectCreationList_Iraq_StrategicMissiles.ini": "\n".join(ocl_parts),
    }
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.replace("\r\n", "\n"), encoding="ascii")
    return files


def write_manifest(dhash, ahash, zhash, data_path, art_path, zip_path):
    lines = [
        "# SPECTER Iraqi Strategic Missile Family — Manifest",
        "",
        "Authority: live s `_SPEC_DATA_ONE.big` / `_SPEC_ART_ONE.big` only.",
        "Static validation only. Not an in-game runtime test.",
        "",
        "## Donor and identity",
        "",
        "| Missile | Object | TEL donor W3D | Missile donor W3D | Private TEL tex | Private MSL tex | Scale | PScale | Cost | Time | Dmg | Rad | Range | Reload ms | Weapon | Projectile | Button |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for spec in FAMILY:
        n = asset_names(spec)
        lines.append(
            f"| {spec['label']} | {spec['obj']} | {spec['tel_models'][0]} | {spec['msl_model']} | "
            f"{n['tex_tel']} | {n['tex_msl']} | {spec['scale']:.2f} | {spec['pscale']:.2f} | "
            f"{spec['cost']} | {spec['time']:.0f} | {spec['dmg']} | {spec['rad']} | {spec['rng']} | "
            f"{spec['reload']} | {n['weapon']} | {n['proj']} | {n['btn']} |"
        )
    lines += [
        "",
        "## Shared command / production",
        "",
        "- CommandSet (TELs): `Iraq_StrategicMissileNewCommandSet`",
        "- CommandSet (factory): `Iraq_MissileFactoryCommandSet`",
        "- Factory object: `Iraq_MissileFactory`",
        "- Factory button (core CommandButton.ini): `Command_ConstructIraq_MissileFactory`",
        "- VT72B slot 14: Missile Factory (Worker Clear Mines unchanged)",
        "",
        "## Wreck / damage notes",
        "",
    ]
    for spec in FAMILY:
        lines.append(f"- **{spec['label']}**: {spec['wreck_note']}")
    lines += [
        "",
        "## Honest geometry limits",
        "",
        "- Al-Hussein / Al-Hijarah share cloned `Irq_9P117` + `Irq_R11_M` (Scale + private paint distinguish them).",
        "- Al-Samoud uses the same `Irq_R11_M` donor at 0.82 on a cloned `Irq_Sarab7` TEL.",
        "- Al-Abid (`RUS_RS24M`) and Tammuz-1 (`Iraq_Alhusain_M`) share the `irq_projectiles_c` mesh family; distinction is TEL, Scale, and stage-band paint.",
        "- Badr-2000 two-stage look uses `Hwasong7` (closest live two-stage missile W3D). No Iraqi Condor-II mesh exists in s.",
        "- Tammuz-1 / Al-Abid gameplay numbers are SPECTER balance, not historical combat statistics.",
        "",
        "## SHA256",
        "",
        f"- `_SPEC_DATA_ONE.big` {data_path.stat().st_size} SHA256={dhash}",
        f"- `_SPEC_ART_ONE.big` {art_path.stat().st_size} SHA256={ahash}",
        f"- `SPECTER_IRAQ_STRATEGIC_MISSILES.zip` {zip_path.stat().st_size} SHA256={zhash}",
        "",
    ]
    (OUT / "MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if not S_DATA.is_file() or not S_ART.is_file():
        raise SystemExit("live s BIGs missing under /tmp/s-bigs")
    OUT.mkdir(parents=True, exist_ok=True)
    write_source_inis()

    s_data_bytes = S_DATA.read_bytes()
    s_art_bytes = S_ART.read_bytes()
    data_map = parse_big(s_data_bytes)
    art_map = parse_big(s_art_bytes)
    s_art_orig = dict(art_map)

    irq_wf = None
    irq_wf_key = None
    for k, v in art_map.items():
        if k.replace("/", "\\").lower() == "art\\w3d\\irq_warfactory.w3d":
            irq_wf = v
            irq_wf_key = k
            break
    if irq_wf is None:
        raise SystemExit("Irq_WarFactory.W3D missing")

    extras = [
        "INI/Object/Specter/Iraq Army/Wheeled/Iraq_StrategicMissiles_New.ini",
        "INI/Object/Specter/Iraq Army/Hulk/Iraq_StrategicMissile_Hulks.ini",
        "INI/Object/Specter/Iraq Army/Iraq_StrategicMissile_Projectiles.ini",
        "INI/Weapon_Iraq_StrategicMissiles.ini",
        "INI/ObjectCreationList_Iraq_StrategicMissiles.ini",
        "INI/CommandSet_Iraq_MissileFactory.ini",
        "INI/Object/Specter/Iraq Army/Buildings/Iraq_MissileFactory.ini",
    ]
    for rel in extras:
        p = PATCH_DATA / rel
        if not p.is_file():
            raise SystemExit(f"missing {p}")
        data_map["Data\\" + rel.replace("/", "\\")] = to_crlf(p.read_bytes())

    extra_cs = data_map["Data\\INI\\CommandSet_Iraq_MissileFactory.ini"]
    if b"CommandSet Iraq_VT72BCommandSet" in extra_cs:
        raise SystemExit("extra CommandSet must not redefine Iraq_VT72BCommandSet")

    blocks = "".join(button_block(spec, asset_names(spec)) for spec in FAMILY)
    cb_key = "Data\\INI\\CommandButton.ini"
    cb = inject_core_mf_button(data_map[cb_key].decode("latin1"))
    cb = inject_core_buttons(cb, blocks)
    if cb.count("CommandButton Command_ConstructIraq_AlHussein_New") != 1:
        raise SystemExit("AlHussein button count != 1")
    data_map[cb_key] = cb.encode("latin1")

    cs_key = "Data\\INI\\CommandSet.ini"
    cs_text = patch_vt72b_slot14(data_map[cs_key].decode("latin1"))
    wk = re.search(r"CommandSet Iraq_WorkerCommandSet\r?\n.*?^End", cs_text, re.M | re.S)
    if not wk or "14 = Command_DisarmMinesAtPosition" not in wk.group(0):
        raise SystemExit("Worker Clear Mines lost")
    data_map[cs_key] = cs_text.encode("latin1")

    s_orig = parse_big(s_data_bytes)
    if data_map["Data\\INI\\Object\\Specter\\Iraq Army\\Wheeled\\9P117.ini"] != s_orig[
        "Data\\INI\\Object\\Specter\\Iraq Army\\Wheeled\\9P117.ini"
    ]:
        raise SystemExit("Iraq_R11ScudB INI mutated")
    if data_map["Data\\INI\\Object\\Specter\\Iraq Army\\Wheeled\\AlNida.ini"] != s_orig[
        "Data\\INI\\Object\\Specter\\Iraq Army\\Wheeled\\AlNida.ini"
    ]:
        raise SystemExit("Iraq_Sarab7 INI mutated")

    labels = {
        "CONTROLBAR:ConstructIraqMissileFactory": "Missile Factory",
        "CONTROLBAR:ToolTipIraqBuildMissileFactory": "Build Missile Factory. Produces the Iraqi strategic missile family.",
        "OBJECT:IraqMissileFactory": "Missile Factory",
    }
    for spec in FAMILY:
        labels[f"OBJECT:{spec['obj']}"] = spec["label"]
        labels[f"CONTROLBAR:Construct{spec['obj']}"] = spec["label"]
        labels[f"CONTROLBAR:ToolTip{spec['obj']}"] = f"Build {spec['label']} TEL."
    data_map["Data\\English\\generals.csf"] = csf_append(data_map["Data\\English\\generals.csf"], labels)

    private = build_private_art(art_map)
    for k, v in private.items():
        if k in art_map:
            raise SystemExit(f"refusing to overwrite existing ART {k}")
        art_map[k] = v

    mf_art = [
        ("Art\\W3D\\LSFIQMCheChang.W3D", DONOR_W3D / "LSFIQMCheChang.W3D"),
        ("Art\\W3D\\LSFIQMCheChangd.W3D", DONOR_W3D / "LSFIQMCheChangd.W3D"),
        ("Art\\W3D\\LSFIQMCheChange.W3D", DONOR_W3D / "LSFIQMCheChange.W3D"),
        ("Art\\W3D\\LSFMCheChangCB.W3D", DONOR_W3D / "LSFMCheChangCB.W3D"),
    ]
    for dest, src in mf_art:
        exists = any(k.replace("/", "\\").lower() == dest.lower() for k in art_map)
        if exists:
            continue
        if src.is_file():
            art_map[dest] = src.read_bytes()
    if DONOR_TEX.is_dir():
        for src in DONOR_TEX.iterdir():
            dest = f"Art\\Textures\\{src.name}"
            exists = any(k.replace("/", "\\").lower() == dest.lower() for k in art_map)
            if exists or not src.is_file():
                continue
            art_map[dest] = src.read_bytes()

    for atlas in ("GENERIC-MISSILES.dds", "AAM-GENTEX.dds", "KH-GENTEX.dds"):
        key = f"Art\\Textures\\{atlas}"
        if key in art_map and key in s_art_orig and art_map[key] != s_art_orig[key]:
            raise SystemExit(f"shared atlas mutated {atlas}")

    if hashlib.sha256(art_map[irq_wf_key]).hexdigest() != hashlib.sha256(irq_wf).hexdigest():
        raise SystemExit("Irq_WarFactory.W3D changed")

    data_big = build_big(data_map)
    art_big = build_big(art_map)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_big)
    art_path.write_bytes(art_big)
    zip_path = OUT / "SPECTER_IRAQ_STRATEGIC_MISSILES.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        zf.write(data_path, arcname="_SPEC_DATA_ONE.big")
        zf.write(art_path, arcname="_SPEC_ART_ONE.big")
    dhash, ahash, zhash = sha256(data_path), sha256(art_path), sha256(zip_path)
    (OUT / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  {data_path.stat().st_size}  SHA256={dhash}\n"
        f"_SPEC_ART_ONE.big  {art_path.stat().st_size}  SHA256={ahash}\n"
        f"SPECTER_IRAQ_STRATEGIC_MISSILES.zip  {zip_path.stat().st_size}  SHA256={zhash}\n",
        encoding="ascii",
    )
    write_manifest(dhash, ahash, zhash, data_path, art_path, zip_path)
    print("DATA", data_path.stat().st_size, dhash)
    print("ART", art_path.stat().st_size, ahash)
    print("ZIP", zip_path.stat().st_size, zhash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
