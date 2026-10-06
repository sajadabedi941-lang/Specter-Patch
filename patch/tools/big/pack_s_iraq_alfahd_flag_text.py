#!/usr/bin/env python3
"""Paint Iraqi flag + AL-FAHD500 stencil on the actual Al-Fahd500 missile meshes.

Live baseline: FIRE_FLAG / 9p117-freeze ART+DATA.
Does not rebuild weapons, factory, 9P117, or unrelated ART.

Root causes of the missing flag:
  1. Flying projectile texture Irq_AlFahd500P.tga was 24-bit / desc 0x00.
     Every working Al-Fahd W3D texture is 32-bit TGA desc 0x08.
  2. Launcher-mounted MISSILE01 still used Irq_AlFahd500M.tga with the original
     GENERIC-MISSILES atlas UVs (tiny islands, no flag texels).
  3. Stencil text was never drawn.

Fix is ART-only. DATA is copied unchanged from the freeze baseline.
"""
from __future__ import annotations

import hashlib
import io
import shutil
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD_FIRE_FLAG/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD_FIRE_FLAG/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD_FLAG_TEXT"

BASE_DATA_SHA = "aed109b44177bcf6c03cff56b42106f985115404f0ace80811ae262e999b9cc0"
BASE_ART_SHA = "0fa219d868ad1e6f6ddc8d0c955910cdd627b353869cae1459e3b969ece91a65"
BASE_DATA_SIZE = 366368616
BASE_ART_SIZE = 1263069228

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
STAMP = "AL-FAHD500"
SHEET = 1024
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/macos/Inter-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
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


def walk_rebuild_missile01(blob: bytes, mesh_name: str | None = None) -> bytes:
    """Remap launcher MISSILE01 UVs onto the dedicated sheet and retarget its texture."""
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
            payload = walk_rebuild_missile01(payload, current_mesh)
        elif cid == TEX_CHUNK and current_mesh == "MISSILE01":
            payload = b"Irq_AlFahd500P.tga\x00"
        elif cid == TEXCOORD_CHUNK and current_mesh == "MISSILE01":
            payload = remap_launcher_uv_payload(payload)
        new_raw = len(payload) | (0x80000000 if cont else 0)
        out += struct.pack("<II", cid, new_raw)
        out += payload
        pos = ce
    if pos < end:
        out += blob[pos:]
    return bytes(out)


def remap_launcher_uv_payload(payload: bytes) -> bytes:
    n = len(payload) // 8
    out = bytearray()
    for i in range(n):
        u, v = struct.unpack_from("<ff", payload, i * 8)
        out += struct.pack("<ff", *remap_launcher_uv(u, v))
    return bytes(out)


def remap_launcher_uv(u: float, v: float) -> tuple[float, float]:
    """Map original GENERIC-MISSILES atlas islands on the TEL missile onto the dedicated sheet.

    Island A (engine/body): u 0.4704-0.5313, v 0.2343-0.2709
    Island B (main body):   u 0.5462-0.5897, v 0.8115-0.8551
    Island C (warhead):     u 0.6695-0.7336, v 0.8208-0.8627
    """
    if 0.46 <= u <= 0.54 and 0.22 <= v <= 0.29:
        u2 = clamp01((u - 0.4704) / (0.5313 - 0.4704))
        v2 = clamp01((v - 0.2343) / (0.2709 - 0.2343))
        return 0.04 + u2 * 0.92, 0.12 + v2 * 0.70
    if 0.54 <= u <= 0.60 and 0.80 <= v <= 0.87:
        u2 = clamp01((u - 0.5462) / (0.5897 - 0.5462))
        v2 = clamp01((v - 0.8115) / (0.8551 - 0.8115))
        return 0.04 + u2 * 0.92, 0.12 + v2 * 0.70
    if 0.66 <= u <= 0.76 and 0.80 <= v <= 0.88:
        u2 = clamp01((u - 0.6695) / (0.7336 - 0.6695))
        v2 = clamp01((v - 0.8208) / (0.8627 - 0.8208))
        return 0.04 + u2 * 0.92, 0.12 + v2 * 0.70
    return 0.50, 0.94


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


def mesh_textures(blob: bytes) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
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
            elif cid == TEX_CHUNK:
                out.setdefault(mesh, set()).add(zstr(data[cs:ce]))
            p = ce

    rec(blob, 0, len(blob))
    return out


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
    """32-bit bottom-origin TGA, identical header profile to Irq_AlFahd500.tga / Irq_AlFahd500M.tga."""
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
        "descriptor": f"0x{blob[17]:02x}",
        "origin": "top" if blob[17] & 0x20 else "bottom",
        "size": len(blob),
    }


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise SystemExit("no bold latin font for AL-FAHD500 stencil")


def draw_stencil(im: Image.Image, text: str, cy: int, font: ImageFont.FreeTypeFont) -> None:
    draw = ImageDraw.Draw(im)
    gap = max(6, font.size // 10)
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + gap * (len(text) - 1)
    x = (im.size[0] - total) / 2
    bbox = font.getbbox("Hg")
    glyph_h = bbox[3] - bbox[1]
    y = cy - glyph_h // 2 - bbox[1]
    plate = [
        int(x - 18),
        int(y - 10),
        int(x + total + 18),
        int(y + glyph_h + 14),
    ]
    draw.rectangle(plate, fill=(214, 178, 16), outline=(18, 16, 10), width=4)
    fill = (18, 16, 12)
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill, stroke_width=2, stroke_fill=(10, 8, 6))
        x += w + gap


def paste_flag(im: Image.Image, flag: Image.Image, xy: tuple[int, int], size: tuple[int, int]) -> None:
    fw, fh = size
    flag_im = flag.convert("RGBA").resize((fw, fh), Image.Resampling.NEAREST)
    bordered = Image.new("RGBA", (fw + 10, fh + 10), (12, 10, 8, 255))
    bordered.paste(flag_im, (5, 5), flag_im)
    im.paste(bordered, xy, bordered)


def make_missile_skin(flag: Image.Image) -> Image.Image:
    """Yellow missile unwrap with two Iraqi flags and two AL-FAHD500 stencils.

    Body UVs occupy u 0.04-0.96, v 0.12-0.82. Duplicate markings along V so the
    cylinder shows the flag from either side and survives TGA V interpretation.
    """
    w = h = SHEET
    im = Image.new("RGBA", (w, h), (232, 196, 24, 255))
    px = im.load()
    for y in range(h):
        shade = 1.0 - 0.16 * abs((y / h) - 0.47)
        for x in range(w):
            if y >= int(0.90 * h):
                px[x, y] = (236, 200, 28, 255)
                continue
            r = min(255, int(232 * shade))
            g = min(255, int(196 * shade))
            b = min(40, int(24 * shade))
            px[x, y] = (r, g, b, 255)
    # Flag A: upper body (v ~ 0.13-0.38)
    paste_flag(im, flag, (42, 90), (930, 260))
    font = load_font(72)
    # Text A between the two flags (v ~ 0.42-0.50)
    draw_stencil(im, STAMP, 430, font)
    # Flag B: opposite side / lower body (v ~ 0.52-0.77)
    paste_flag(im, flag, (42, 500), (930, 260))
    # Text B near the high-V edge still sampled by body unwrap
    draw_stencil(im, STAMP, 830, font)
    return im


def region_colors(im: Image.Image, box: tuple[int, int, int, int]) -> dict[str, int]:
    crop = im.convert("RGB").crop(box)
    px = crop.load()
    w, h = crop.size
    counts = {"red": 0, "white": 0, "black": 0, "yellow": 0, "dark": 0, "green": 0, "other": 0}
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if r > 160 and g < 90 and b < 90:
                counts["red"] += 1
            elif r < 55 and g < 55 and b < 55:
                counts["black"] += 1
            elif r > 190 and g > 190 and b > 190:
                counts["white"] += 1
            elif r > 170 and g > 130 and b < 90:
                counts["yellow"] += 1
            elif g > r + 20 and g > b + 20 and g > 70:
                counts["green"] += 1
            elif r < 80 and g < 80 and b < 70:
                counts["dark"] += 1
            else:
                counts["other"] += 1
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
    names = [n.replace("/", "\\") for n, _, _ in files]
    last = {}
    for n, _, _ in files:
        last[n.replace("/", "\\").lower()] = n
    for want in [PROJ_W3D_KEY, PROJ_TEX_KEY, LAUNCHER_W3D_KEY]:
        if last.get(want.lower()) != want:
            issues.append(f"last-wins missing {want}")
    return issues


def validate(
    data: dict[str, bytes],
    art: dict[str, bytes],
    src_data: dict[str, bytes],
    src_art: dict[str, bytes],
    sheet: Image.Image,
) -> list[str]:
    fails: list[str] = []

    changed_d = sorted(k for k in set(data) | set(src_data) if data.get(k) != src_data.get(k))
    if changed_d:
        fails.append(f"DATA changed unexpectedly {changed_d[:8]}")

    if data[r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"] != src_data[
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
    ]:
        fails.append("launcher INI mutated")
    proj = data[r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini"].decode("latin1")
    if "Model = Irq_AlFahd500M" not in proj:
        fails.append("projectile model retargeted")
    unit = data[r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"].decode("latin1")
    if "Model                           = Irq_AlFahd500" not in unit:
        fails.append("launcher model retargeted")
    if data[r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"] != src_data[
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
    ]:
        fails.append("9P117 INI mutated")

    for key in [GENERIC_KEY, FLAG_KEY, FACTORY_TGA_KEY, LAUNCHER_TEX_KEY]:
        if art[key] != src_art[key]:
            fails.append(f"frozen texture mutated {key}")
    for donor in ["Irq_9P117", "Irq_9P117D", "Irq_9P117R", "Irq_R11_M"]:
        k = f"Art\\W3D\\{donor}.W3D"
        if art[k] != src_art[k]:
            fails.append(f"donor W3D mutated {donor}")
    for tex in ["Irq_9P117.dds", "Irq_9P117D.dds", "Irq_9P117R.dds"]:
        k = f"Art\\Textures\\{tex}"
        if art[k] != src_art[k]:
            fails.append(f"donor texture mutated {tex}")

    if b"IRQ_9P117" in art[LAUNCHER_W3D_KEY] or b"IRQ_R11_M" in art[PROJ_W3D_KEY]:
        fails.append("Al-Fahd W3D regained 9P117 identity")
    if b"IRQ_AF500" not in art[LAUNCHER_W3D_KEY] or b"IRQ_ALF_M" not in art[PROJ_W3D_KEY]:
        fails.append("Al-Fahd dedicated identity missing")
    if b"IRQ_9P117" not in art[r"Art\W3D\Irq_9P117.W3D"]:
        fails.append("original 9P117 identity lost")
    if b"Irq_AlFahd500P.tga" in art[r"Art\W3D\Irq_R11_M.W3D"]:
        fails.append("original R11 references Al-Fahd projectile texture")

    if hlod_name(art[PROJ_W3D_KEY]) != "Irq_AlFahd500M":
        fails.append("projectile HLod renamed")
    if texture_names(art[PROJ_W3D_KEY]) != {"Irq_AlFahd500P.tga"}:
        fails.append(f"projectile textures {texture_names(art[PROJ_W3D_KEY])}")

    mt = mesh_textures(art[LAUNCHER_W3D_KEY])
    if mt.get("MISSILE01") != {"Irq_AlFahd500P.tga"}:
        fails.append(f"launcher MISSILE01 textures {mt.get('MISSILE01')}")
    truck_tex = set()
    for mesh, texes in mt.items():
        if mesh != "MISSILE01":
            truck_tex |= texes
    if "Irq_AlFahd500P.tga" in truck_tex:
        fails.append("truck meshes accidentally retargeted to projectile sheet")
    if not any("Irq_AlFahd500.tga" in t or "Irq_AlFahd500" in next(iter(t)) for t in truck_tex if t):
        # truck should still use the TEL body texture
        if "Irq_AlFahd500.tga" not in truck_tex:
            fails.append(f"launcher body textures unexpected {truck_tex}")

    mtd = mesh_textures(art[LAUNCHERD_W3D_KEY])
    if mtd.get("MISSILE01") != {"Irq_AlFahd500P.tga"}:
        fails.append(f"destroyed MISSILE01 textures {mtd.get('MISSILE01')}")

    info = tga_info(art[PROJ_TEX_KEY])
    if info["type"] != 2 or info["bpp"] != 32 or info["alpha_bits"] != 8:
        fails.append(f"projectile TGA profile {info}")
    if info["width"] != SHEET or info["height"] != SHEET:
        fails.append(f"projectile TGA size {info['width']}x{info['height']}")
    if info["origin"] != "bottom":
        fails.append("projectile TGA not bottom-origin")

    # UV coverage on the dedicated sheet
    for label, w3d in [
        ("projectile", art[PROJ_W3D_KEY]),
        ("launcher", art[LAUNCHER_W3D_KEY]),
    ]:
        uvs = collect_uvs(w3d)
        if label == "launcher":
            uvs = [(m, u, v) for m, u, v in uvs if m == "MISSILE01"]
        body = [(u, v) for _m, u, v in uvs if v < 0.88]
        if len(body) < 20:
            fails.append(f"{label} too few body UVs {len(body)}")
            continue
        us = [u for u, _v in body]
        vs = [v for _u, v in body]
        if min(us) > 0.08 or max(us) < 0.90 or min(vs) > 0.18 or max(vs) < 0.70:
            fails.append(
                f"{label} body UV bbox misses flag sheet "
                f"{min(us):.3f}..{max(us):.3f} {min(vs):.3f}..{max(vs):.3f}"
            )

    decoded = Image.open(io.BytesIO(art[PROJ_TEX_KEY])).convert("RGBA")
    if decoded.size != (SHEET, SHEET):
        fails.append(f"decoded sheet size {decoded.size}")
    flag_a = region_colors(decoded, (50, 95, 970, 350))
    flag_b = region_colors(decoded, (50, 505, 970, 760))
    text_a = region_colors(decoded, (80, 390, 944, 470))
    text_b = region_colors(decoded, (80, 790, 944, 870))
    for name, counts in [("flagA", flag_a), ("flagB", flag_b)]:
        if counts["red"] < 200 or counts["white"] < 80 or counts["black"] < 200:
            fails.append(f"{name} missing Iraqi flag bands {counts}")
    for name, counts in [("textA", text_a), ("textB", text_b)]:
        if counts["dark"] + counts["black"] < 80:
            fails.append(f"{name} missing AL-FAHD500 stencil ink {counts}")

    # Sample interpolated body UVs (not just vertex edge texels).
    rgb = decoded.convert("RGB")
    hits = {"red": 0, "white": 0, "black": 0, "dark": 0}
    for v in (0.15, 0.22, 0.30, 0.45, 0.55, 0.62, 0.72):
        for u in (0.15, 0.35, 0.50, 0.65, 0.85):
            r, g, b = rgb.getpixel((int(u * (SHEET - 1)), int(v * (SHEET - 1))))
            if r > 160 and g < 90 and b < 90:
                hits["red"] += 1
            elif r > 190 and g > 190 and b > 190:
                hits["white"] += 1
            elif r < 55 and g < 55 and b < 55:
                hits["black"] += 1
            elif r < 80 and g < 80 and b < 70:
                hits["dark"] += 1
    if hits["red"] < 2 or hits["black"] < 2 or (hits["white"] + hits["dark"]) < 2:
        fails.append(f"interpolated body UVs miss flag/text {hits}")

    changed_a = sorted(k for k in set(art) | set(src_art) if art.get(k) != src_art.get(k))
    allowed_a = {PROJ_TEX_KEY, LAUNCHER_W3D_KEY, LAUNCHERD_W3D_KEY}
    unexpected_a = [k for k in changed_a if k not in allowed_a]
    if unexpected_a:
        fails.append(f"unexpected ART changes {unexpected_a[:8]}")
    for need in [PROJ_TEX_KEY, LAUNCHER_W3D_KEY, LAUNCHERD_W3D_KEY]:
        if need not in changed_a:
            fails.append(f"expected ART change missing {need}")
    if PROJ_W3D_KEY in changed_a:
        fails.append("projectile W3D mutated; UVs were already remapped")
    return fails


def overlay_uvs(sheet: Image.Image, art: dict[str, bytes]) -> Image.Image:
    vis = sheet.convert("RGBA")
    dr = ImageDraw.Draw(vis)
    for mesh, u, v in collect_uvs(art[PROJ_W3D_KEY]):
        x, y = u * (SHEET - 1), v * (SHEET - 1)
        col = (255, 0, 0, 255) if mesh == "BOOSTER" else (0, 255, 0, 255)
        dr.ellipse([x - 4, y - 4, x + 4, y + 4], outline=col, width=2)
    for mesh, u, v in collect_uvs(art[LAUNCHER_W3D_KEY]):
        if mesh != "MISSILE01":
            continue
        x, y = u * (SHEET - 1), v * (SHEET - 1)
        dr.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(0, 80, 255, 255), width=2)
    return vis


def main() -> int:
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("live DATA baseline mismatch")
    if SRC_ART.stat().st_size != BASE_ART_SIZE or sha256_path(SRC_ART) != BASE_ART_SHA:
        raise SystemExit("live ART baseline mismatch")

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    flag = Image.open(io.BytesIO(src_art[FLAG_KEY]))
    sheet = make_missile_skin(flag)
    tga = make_tga32(sheet)
    art[PROJ_TEX_KEY] = tga
    art[LAUNCHER_W3D_KEY] = walk_rebuild_missile01(src_art[LAUNCHER_W3D_KEY])
    art[LAUNCHERD_W3D_KEY] = walk_rebuild_missile01(src_art[LAUNCHERD_W3D_KEY])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    preview = overlay_uvs(sheet, art)
    preview.save(OUT / "alfahd_flag_text_preview.png")
    (OUT / "Irq_AlFahd500P.tga").write_bytes(tga)
    sheet.convert("RGB").save(OUT / "Irq_AlFahd500P_skin.png")

    packed_art = build_big(art)
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_art.write_bytes(packed_art)

    extracted_a = parse_big(packed_art)
    fails = validate(data, extracted_a, src_data, src_art, sheet)
    fails.extend(f"ART {x}" for x in big_structure_ok(packed_art))

    art_sha = sha256_path(out_art)
    tinfo = tga_info(extracted_a[PROJ_TEX_KEY])
    report = [
        "# Iraq_AlFahd500 missile flag + AL-FAHD500 stencil",
        "",
        "Live baseline: SPECTER_IRAQ_ALFAHD_FIRE_FLAG (s-iraq-alfahd-9p117-freeze).",
        "DATA unchanged. ART-only complete replacement of _SPEC_ART_ONE.big.",
        "",
        "## Audit chain",
        "Object Iraq_AlFahd500 -> Model Irq_AlFahd500 / Irq_AlFahd500D",
        "  MISSILE01 material now -> Irq_AlFahd500P.tga (was Irq_AlFahd500M.tga atlas)",
        "Object Projectile_Iraq_AlFahd500 -> Model Irq_AlFahd500M",
        "  BOOSTER + MISSILE01 -> Irq_AlFahd500P.tga",
        "Texture source flag: Art\\Textures\\IraqiFlag.dds (unchanged asset, composited onto skin)",
        "",
        "## Root cause",
        "1. Flying skin was 24-bit TGA desc 0x00; working Al-Fahd W3D textures are 32-bit desc 0x08.",
        "2. TEL-mounted missile kept GENERIC-MISSILES atlas UVs on Irq_AlFahd500M.tga; flag texels were unused.",
        "3. AL-FAHD500 stencil was never present on the sampled skin.",
        "",
        f"- ART size: {out_art.stat().st_size}",
        f"- ART SHA256: {art_sha}",
        f"- ART files: {len(extracted_a)}",
        f"- projectile TGA: type={tinfo['type']} bpp={tinfo['bpp']} alpha={tinfo['alpha_bits']} desc={tinfo['descriptor']} {tinfo['width']}x{tinfo['height']}",
        f"- DATA SHA256 (unchanged): {BASE_DATA_SHA}",
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
        "- DATA byte-identical to s-iraq-alfahd-9p117-freeze",
        "- Projectile Irq_AlFahd500M.W3D still references Irq_AlFahd500P.tga",
        "- Launcher / destroyed MISSILE01 now reference Irq_AlFahd500P.tga",
        "- Irq_AlFahd500P.tga is 32-bit bottom-origin, same profile as working Al-Fahd W3D textures",
        "- Sheet contains two Iraqi flags from IraqiFlag.dds and two AL-FAHD500 stencils",
        "- Body UVs of flying + mounted missile overlap those markings",
        "- GENERIC-MISSILES.dds / IraqiFlag.dds / 9P117 W3D+DDS / missile_factory.tga unchanged",
        "- Al-Fahd identities remain IRQ_AF500 / IRQ_AF500D / IRQ_ALF_M",
        "",
        "RUNTIME_TEST=NOT RUN",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=NO\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={BASE_DATA_SIZE}\n"
        f"DATA_SHA256={BASE_DATA_SHA}\n"
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={out_art.stat().st_size}\n"
        f"ART_SHA256={art_sha}\n"
        f"ART_FILES={len(extracted_a)}\n"
        "OBJECT=Iraq_AlFahd500\n"
        "PROJECTILE_OBJECT=Projectile_Iraq_AlFahd500\n"
        "LAUNCHER_MODEL=Irq_AlFahd500 / Irq_AlFahd500D\n"
        "PROJECTILE_MODEL=Irq_AlFahd500M\n"
        "MISSILE_TEXTURE=Art\\Textures\\Irq_AlFahd500P.tga\n"
        "FLAG_SOURCE=Art\\Textures\\IraqiFlag.dds\n"
        "FLAG_LOCATION=two decals on dedicated sheet at v~0.13-0.38 and v~0.52-0.77\n"
        "STENCIL_TEXT=AL-FAHD500 (two military stencil plates at v~0.42 and v~0.81)\n"
        "TGA_PROFILE=32-bit type2 desc 0x08 bottom-origin 1024x1024\n"
        "ALFAHD_HIER=IRQ_AF500 / IRQ_AF500D / IRQ_ALF_M\n"
        "9P117_HIER=IRQ_9P117 / IRQ_9P117D / IRQ_R11_M (frozen original files)\n"
        "BASELINE_ART=s-iraq-alfahd-9p117-freeze / 0fa219d868ad1e6f6ddc8d0c955910cdd627b353869cae1459e3b969ece91a65\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq Al-Fahd 500 missile Iraqi flag + AL-FAHD500 stencil\n"
        "ART-only complete replacement. Place in the game folder:\n"
        "  _SPEC_ART_ONE.big\n"
        "Keep the current freeze DATA file (_SPEC_DATA_ONE.big from s-iraq-alfahd-9p117-freeze).\n"
        "The flying projectile and the missile mounted on the TEL now share Irq_AlFahd500P.tga\n"
        "with the Iraqi flag (from IraqiFlag.dds) and stencil text AL-FAHD500.\n"
        "Do not use a partial TGA/W3D patch.\n",
        encoding="utf-8",
    )
    print("\n".join(report))
    print("PACK OK", art_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
