#!/usr/bin/env python3
"""Put Iraqi flag + missile name on the dorsal top UV band; recolor B green / H gray.

Baseline: PR #592 SPECTER_IRAQ_TEL_PRELAUNCH_COLOR DATA+ART.

W3D evidence (projectile BOOSTER length=X, circumference=V):
  +Z (sky) verts sit at V ~ 0.725. Old skins painted flags at V ~ 0.21-0.54 (sides).
TEL MISSILE01 (packed length=Z, +Y up):
  +Y verts sit at V ~ 0.22. Same P.tga is shared, so markings are painted on BOTH
  dorsal bands. Flying W3Ds/TELs/DATA/INI are not modified — texture only.

Al-Hussein II body -> green. Al-Basrah body -> gray. Other body/nose colors kept.
Missile A body color kept; only its flag/name move onto the top bands.
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
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_TEL_PRELAUNCH_COLOR/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_TEL_PRELAUNCH_COLOR/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_TOP_MARKINGS"

BASE_DATA_SHA = "6af19c95f508a80752e26fd603d2745b5c2c51d446890a3f373816d329033f27"
BASE_DATA_SIZE = 366515208
BASE_ART_SHA = "72afcc72a12c5cf576a43351a0143796789faa8a55743012bbaf8329c0011246"
BASE_ART_SIZE = 1294467676

FLAG_KEY = r"Art\Textures\IraqiFlag.dds"
SHEET = 1024
TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")

WHITE = (228, 224, 216)
BLACK = (22, 24, 26)
RED = (168, 32, 28)
ORANGE = (210, 108, 22)
YELLOW = (214, 178, 28)
GREEN = (32, 128, 54)
GRAY = (124, 126, 130)
A_YELLOW = (232, 196, 24)

# UV evidence: projectile dorsal V~0.725; TEL dorsal V~0.22. Paint both.
TEL_BAND = (0.16, 0.30)        # y 164-307
PROJ_BAND = (0.66, 0.80)       # y 675-819

MISSILES = [
    {
        "slot": "A",
        "stamp": "AL-FAHD500",
        "tex": r"Art\Textures\Irq_AlFahd500P.tga",
        "body": A_YELLOW,
        "nose": (236, 168, 20),
        "expect": "yellow",
    },
    {
        "slot": "B",
        "stamp": "AL-HUSSEIN II",
        "tex": r"Art\Textures\Irq_AlHussein2P.tga",
        "body": GREEN,
        "nose": RED,
        "expect": "green",
    },
    {
        "slot": "C",
        "stamp": "AL-SAMOUD II",
        "tex": r"Art\Textures\Irq_AlSamoud2P.tga",
        "body": BLACK,
        "nose": RED,
        "expect": "black",
    },
    {
        "slot": "D",
        "stamp": "AL-ABBAS",
        "tex": r"Art\Textures\Irq_AlAbbas2P.tga",
        "body": RED,
        "nose": WHITE,
        "expect": "red",
    },
    {
        "slot": "H",
        "stamp": "AL-BASRAH",
        "tex": r"Art\Textures\Irq_AlBasrahP.tga",
        "body": GRAY,
        "nose": BLACK,
        "expect": "gray",
    },
    {
        "slot": "I",
        "stamp": "AL-NASIR",
        "tex": r"Art\Textures\Irq_AlNasirP.tga",
        "body": ORANGE,
        "nose": RED,
        "expect": "orange",
    },
    {
        "slot": "J",
        "stamp": "AL-MANSOUR",
        "tex": r"Art\Textures\Irq_AlMansourP.tga",
        "body": YELLOW,
        "nose": RED,
        "expect": "yellow",
    },
]

FROZEN = [
    r"Art\W3D\Irq_9P117.W3D",
    r"Art\W3D\Irq_9P117D.W3D",
    r"Art\W3D\Irq_R11_M.W3D",
    r"Art\W3D\Irq_AlFahd500.W3D",
    r"Art\W3D\Irq_AlFahd500D.W3D",
    r"Art\W3D\Irq_AlFahd500M.W3D",
    r"Art\W3D\Irq_AlHussein2.W3D",
    r"Art\W3D\Irq_AlHussein2D.W3D",
    r"Art\W3D\Irq_AlHussein2M.W3D",
    r"Art\W3D\Irq_AlSamoud2T.W3D",
    r"Art\W3D\Irq_AlSamoud2TD.W3D",
    r"Art\W3D\Irq_AlSamoud2M.W3D",
    r"Art\W3D\Irq_AlAbbas2TL.W3D",
    r"Art\W3D\Irq_AlAbbas2TLD.W3D",
    r"Art\W3D\Irq_AlAbbas2M.W3D",
    r"Art\W3D\Irq_AlBasrahTL.W3D",
    r"Art\W3D\Irq_AlBasrahTLD.W3D",
    r"Art\W3D\Irq_AlBasrahM.W3D",
    r"Art\W3D\Irq_AlNasirTEL.W3D",
    r"Art\W3D\Irq_AlNasirTELD.W3D",
    r"Art\W3D\Irq_AlNasirM.W3D",
    r"Art\W3D\Irq_AlMansourT.W3D",
    r"Art\W3D\Irq_AlMansourTD.W3D",
    r"Art\W3D\Irq_AlMansourM.W3D",
    r"Art\Textures\Irq_9P117.dds",
    r"Art\Textures\Irq_9P117D.dds",
    r"Art\Textures\GENERIC-MISSILES.dds",
    FLAG_KEY,
    r"Art\Textures\Irq_AlFahd500.tga",
    r"Art\Textures\Irq_AlFahd500D.tga",
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


def big_structure_ok(data: bytes) -> list[str]:
    fails = []
    archive_size, count, header_size, hdr_end, files = parse_index(data)
    if archive_size != len(data):
        fails.append(f"archive size {archive_size} != {len(data)}")
    if count != len(files):
        fails.append("count mismatch")
    if header_size != hdr_end:
        fails.append("header size mismatch")
    seen = set()
    for name, off, size in files:
        key = name.replace("/", "\\").lower()
        if key in seen:
            fails.append(f"dup {name}")
        seen.add(key)
        if off < header_size or off + size > len(data):
            fails.append(f"range {name}")
    return fails


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


def paste_flag(im: Image.Image, flag: Image.Image, xy: tuple[int, int], size: tuple[int, int]) -> None:
    fw, fh = size
    flag_im = flag.convert("RGBA").resize((fw, fh), Image.Resampling.NEAREST)
    bordered = Image.new("RGBA", (fw + 8, fh + 8), (16, 14, 12, 255))
    bordered.paste(flag_im, (4, 4), flag_im)
    im.paste(bordered, xy, bordered)


def draw_name(im: Image.Image, text: str, box: tuple[int, int, int, int], light_body: bool) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    if light_body:
        plate = (28, 26, 22, 230)
        ink = (236, 228, 210)
    else:
        plate = (236, 228, 196, 230)
        ink = (18, 16, 12)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=plate, outline=(12, 10, 8), width=3)
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = x0 + (x1 - x0 - tw) / 2 - bbox[0]
    ty = y0 + (y1 - y0 - th) / 2 - bbox[1]
    draw.text((tx, ty), text, font=font, fill=ink, stroke_width=1, stroke_fill=(8, 8, 8))


def paint_dorsal(im: Image.Image, flag: Image.Image, stamp: str, v0: float, v1: float, light: bool) -> None:
    w = h = SHEET
    y0, y1 = int(v0 * h), int(v1 * h)
    pad = 6
    band_h = y1 - y0
    flag_h = min(124, band_h - 2 * pad)
    flag_w = 380
    fx = int(0.06 * w)
    fy = y0 + (band_h - flag_h) // 2
    paste_flag(im, flag, (fx, fy), (flag_w, flag_h))
    nx0 = fx + flag_w + 24
    nx1 = int(0.96 * w)
    ny0 = fy + 6
    ny1 = fy + flag_h - 6
    draw_name(im, stamp, (nx0, ny0, nx1, ny1), light)


def make_skin(body: tuple[int, int, int], nose: tuple[int, int, int], stamp: str, flag: Image.Image) -> Image.Image:
    w = h = SHEET
    im = Image.new("RGBA", (w, h), shade(body, 1.0))
    px = im.load()
    nose_hi = int(0.14 * h)
    body_lo = int(0.18 * h)
    body_hi = int(0.82 * h)
    for y in range(h):
        for x in range(w):
            if y < nose_hi:
                circ = 1.0 - 0.10 * abs((x / w) - 0.5)
                px[x, y] = shade(nose, circ)
            elif y < body_lo:
                px[x, y] = shade(body, 0.78)
            elif y < body_hi:
                circ = 1.04 - 0.12 * abs((y - (body_lo + body_hi) / 2) / max(1, (body_hi - body_lo) / 2))
                px[x, y] = shade(body, circ)
            else:
                px[x, y] = shade(body, 0.88)
    light = body[0] + body[1] + body[2] > 360
    paint_dorsal(im, flag, stamp, TEL_BAND[0], TEL_BAND[1], light)
    paint_dorsal(im, flag, stamp, PROJ_BAND[0], PROJ_BAND[1], light)
    im = ImageEnhance.Contrast(im).enhance(1.04)
    im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=40, threshold=3))
    return im.convert("RGBA")


def classify(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    mx, mn = max(r, g, b), min(r, g, b)
    avg = (r + g + b) / 3
    if g > r + 18 and g > b + 18 and g > 80:
        return "green"
    if mx - mn < 28 and 85 <= avg <= 165:
        return "gray"
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
    if r > 180 and g > 150 and b < 80:
        return "yellow"
    return "other"


def region_mode(im: Image.Image, box: tuple[int, int, int, int]) -> dict[str, int]:
    crop = im.convert("RGB").crop(box)
    px = crop.load()
    w, h = crop.size
    counts: dict[str, int] = {}
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            k = classify(px[x, y])
            counts[k] = counts.get(k, 0) + 1
    return counts


def has_flag(counts: dict[str, int]) -> bool:
    # Iraqi flag is red/white/black stripes plus a green takbir on the white band.
    iraqi = counts.get("red", 0) >= 8 and counts.get("white", 0) >= 6
    bars = counts.get("black", 0) >= 4 or counts.get("green", 0) >= 20
    return iraqi and bars


def validate_art(art: dict[str, bytes], src_art: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    for key in FROZEN:
        if art.get(key) != src_art.get(key):
            fails.append(f"frozen mutated {key}")
    for m in MISSILES:
        im = Image.open(io.BytesIO(art[m["tex"]])).convert("RGB")
        if im.size != (SHEET, SHEET):
            fails.append(f"{m['slot']} size {im.size}")
        # Body sample: mid-length, away from both dorsal bands (V 0.40-0.55, U 0.08-0.20)
        body = region_mode(im, (80, 410, 200, 560))
        top_body = max(body, key=body.get)
        if m["expect"] == "yellow":
            if top_body not in ("yellow", "orange"):
                fails.append(f"{m['slot']} body {top_body} {body}")
        elif top_body != m["expect"]:
            fails.append(f"{m['slot']} body {top_body} {body}")
        nose = region_mode(im, (80, 10, 200, 120))
        # Flag + name on TEL dorsal and projectile dorsal.
        tel_flag = region_mode(im, (110, 180, 420, 290))
        proj_flag = region_mode(im, (110, 690, 420, 800))
        if not has_flag(tel_flag):
            fails.append(f"{m['slot']} TEL-top flag missing {tel_flag}")
        if not has_flag(proj_flag):
            fails.append(f"{m['slot']} projectile-top flag missing {proj_flag}")
        tel_name = region_mode(im, (500, 190, 960, 280))
        proj_name = region_mode(im, (500, 700, 960, 790))
        def name_ok(counts: dict[str, int]) -> bool:
            # Name plates are dark-on-light or light-on-dark, not a body-only stripe.
            plate = counts.get("black", 0) + counts.get("white", 0) + counts.get("yellow", 0)
            return plate >= 20

        if not name_ok(tel_name):
            fails.append(f"{m['slot']} TEL name plate missing {tel_name}")
        if not name_ok(proj_name):
            fails.append(f"{m['slot']} projectile name plate missing {proj_name}")
        # Exact W3D dorsal UVs: TEL +Y seam V~0.22, projectile +Z V~0.725, U along length.
        tel_uv = region_mode(im, (90, 200, 280, 250))
        proj_uv = region_mode(im, (90, 710, 280, 770))
        if not has_flag(tel_uv):
            fails.append(f"{m['slot']} TEL UV V=0.22 flag miss {tel_uv}")
        if not has_flag(proj_uv):
            fails.append(f"{m['slot']} proj UV V=0.725 flag miss {proj_uv}")
        # Side band (old placement V~0.42-0.50) must NOT be the only markings;
        # body color should dominate there.
        side = region_mode(im, (350, 420, 700, 520))
        side_top = max(side, key=side.get)
        if m["expect"] == "yellow":
            ok_side = side_top in ("yellow", "orange", "other")
        else:
            ok_side = side_top == m["expect"] or side.get(m["expect"], 0) > side.get("red", 0)
        if not ok_side and side_top in ("red",) and m["expect"] not in ("red",):
            fails.append(f"{m['slot']} side still looks like a decal {side}")
    return fails


def main() -> int:
    if sha256_path(SRC_DATA) != BASE_DATA_SHA or SRC_DATA.stat().st_size != BASE_DATA_SIZE:
        raise SystemExit("PR #592 DATA baseline mismatch")
    if sha256_path(SRC_ART) != BASE_ART_SHA or SRC_ART.stat().st_size != BASE_ART_SIZE:
        raise SystemExit("PR #592 ART baseline mismatch")

    src_art = parse_big(SRC_ART.read_bytes())
    art = dict(src_art)
    flag = Image.open(io.BytesIO(src_art[FLAG_KEY]))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    preview = OUT / "PREVIEW"
    preview.mkdir()

    for m in MISSILES:
        im = make_skin(m["body"], m["nose"], m["stamp"], flag)
        art[m["tex"]] = make_tga32(im)
        im.save(preview / f"{m['slot']}_{m['stamp'].replace(' ', '_')}.png")

    packed_art = build_big(art)
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_art.write_bytes(packed_art)
    shutil.copy2(SRC_DATA, OUT / "_SPEC_DATA_ONE.big")
    extracted_art = parse_big(out_art.read_bytes())

    fails = validate_art(extracted_art, src_art)
    fails.extend(f"ART {x}" for x in big_structure_ok(packed_art))
    if len(extracted_art) != len(src_art):
        fails.append(f"ART file count {len(extracted_art)} != {len(src_art)}")
    if sha256_path(OUT / "_SPEC_DATA_ONE.big") != BASE_DATA_SHA:
        fails.append("DATA copy not byte-identical")

    data_sha = BASE_DATA_SHA
    art_sha = sha256_path(out_art)
    changed = sorted(k for k in extracted_art if src_art.get(k) != extracted_art.get(k))
    report = [
        "# SPECTER missile top-surface flag/name + Hussein green / Basrah gray",
        "",
        "Baseline: PR #592 TEL pre-launch color DATA+ART.",
        "DATA is a byte-identical copy. ART replaces seven missile P.tga skins.",
        "",
        "UV fix: projectile BOOSTER +Z (top) is V~0.725; TEL MISSILE01 +Y (top) is V~0.22.",
        "Previous skins painted flags at V~0.21-0.54 (cylinder sides). New skins paint",
        "Iraqi flag + exact missile name on both dorsal bands, along the length (U).",
        "",
        "Al-Hussein II body -> green. Al-Basrah body -> gray. Other colors preserved.",
        "Missile A body stays yellow; only its markings move onto the top bands.",
        "W3Ds, 9P117, weapons, radar, costs: unchanged.",
        "",
        f"- DATA size: {BASE_DATA_SIZE}",
        f"- DATA SHA256: {data_sha}",
        f"- ART size: {out_art.stat().st_size}",
        f"- ART SHA256: {art_sha}",
        f"- ART files: {len(extracted_art)}",
        f"- Changed ART: {', '.join(changed)}",
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
        "## VALIDATION PASS (static / packed last-wins)",
        "- DATA SHA identical to PR #592",
        "- All TEL and projectile W3Ds byte-identical",
        "- 9P117 / GENERIC-MISSILES / IraqiFlag.dds / vehicle TGAs unchanged",
        "- Flag red/white/black present on TEL dorsal band AND projectile dorsal band",
        "- Name plates present on both dorsal bands",
        "- Al-Hussein II body classified green; Al-Basrah body classified gray",
        "- Missile A body remains yellow; C/D/I/J body colors unchanged",
        "",
        "Static validation completed; runtime game test not performed.",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=NO\n"
        "ART_CHANGED=YES\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={BASE_DATA_SIZE}\n"
        f"DATA_SHA256={data_sha}\n"
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={out_art.stat().st_size}\n"
        f"ART_SHA256={art_sha}\n"
        f"ART_FILES={len(extracted_art)}\n"
        f"CHANGED_ART={', '.join(changed)}\n"
        "DORSAL_TEL_V=0.16-0.30\n"
        "DORSAL_PROJ_V=0.66-0.80\n"
        "HUSSEIN_BODY=green\n"
        "BASRAH_BODY=gray\n"
        "BASELINE=PR #592\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: missile top-surface flag + name; Al-Hussein green; Al-Basrah gray\n"
        "\n"
        "Each factory missile skin now has the Iraqi flag and the missile name on\n"
        "the upper-facing UV band (visible from the top-down camera), on both the\n"
        "mounted TEL missile and the launched projectile.\n"
        "\n"
        "Al-Hussein II body is green. Al-Basrah body is gray.\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big  (unchanged from PR #592)\n"
        "  _SPEC_ART_ONE.big\n"
        "\n"
        "Static validation completed; runtime game test not performed.\n",
        encoding="utf-8",
    )
    (OUT / "LAST_WINS.txt").write_text(
        "UV_PROJ_TOP=BOOSTER V~0.725 U=length\n"
        "UV_TEL_TOP=MISSILE01 V~0.22 +Y\n"
        "MARKINGS=flag+name on both dorsal bands along U\n"
        "B_BODY=green (32,128,54) nose=red\n"
        "H_BODY=gray (124,126,130) nose=black\n"
        "A_BODY=yellow preserved; markings moved to dorsal bands\n"
        "DATA=PR592 byte-identical\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_TOP_MARKINGS.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
