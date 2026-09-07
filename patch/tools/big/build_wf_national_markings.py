#!/usr/bin/env python3
"""War Factory realism pass: keep military paint, swap only flag markings.

Does not recolor buildings or replace structural textures.
Does not touch CommandCenter, PlayerTemplate, Science, or airfields.

US donor flags live on a 512 atlas (US_BUILDINGS). Clones copy that atlas
and repaint only the F1/F2/F3 UV island. Iraq/NK donor flags are dedicated
128x64 textures, so those names are swapped in place.
"""

from __future__ import annotations

import hashlib
import io
import re
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

SRC_DATA = Path("/tmp/national_wmd/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/japan_aircraft_final/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/wf_national_markings")
PREVIEW = Path("/opt/cursor/artifacts/wf_national_markings_preview.png")

LOCKED_PATHS = {
    r"data\ini\playertemplate.ini",
    r"data\ini\science.ini",
    r"data\ini\specialpower.ini",
    r"data\ini\object\specter\japan self-defense forces\tracked\japan_vt72b.ini",
    r"data\ini\object\specter\japan self-defense forces\tracked\vt72b.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\japan_commandcenter.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\iraq_commandcenter.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\japan_airfield.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\japan_largeairbase.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\japan_heavyairbase.ini",
}

# F1/F2/F3 UV island on US_BUILDINGS.dds (V from bottom, 512x512)
US_FLAG_BOX = (54, 408, 188, 484)

# new W3D stem -> (donor stem, flag tex, kind, style)
# kind irq = replace IraqiFlag/DPRK_Flag; us = paint F1/F2/F3 atlas island
NEW_STEMS = {
    "JP_WarFactory": ("NKr_WarFactory", "JP_WF_Flag.tga", "irq", "japan"),
    "SK_WarFactory": ("NKr_WarFactory", "SK_WF_Flag.tga", "irq", "korea"),
    "IN_WarFactory": ("Irq_WarFactory", "IN_WF_Flag.tga", "irq", "india"),
    "SA_WarFactory": ("Irq_WarFactory", "SA_WF_Flag.tga", "irq", "saudi"),
    "AE_WarFactory": ("Irq_WarFactory", "AE_WF_Flag.tga", "irq", "uae"),
    "DE_WarFactory": ("US_WarFactory", "DE_WF_Mark00.tga", "us", "germany"),
    "FR_WarFactory": ("US_WarFactory", "FR_WF_Mark00.tga", "us", "france"),
    "TR_WarFactory": ("US_WarFactory", "TR_WF_Mark00.tga", "us", "turkey"),
    "UA_WarFactory": ("US_WarFactory", "UA_WF_Mark00.tga", "us", "ukraine"),
    "SE_WarFactory": ("US_WarFactory", "SE_WF_Mark00.tga", "us", "sweden"),
}

OBJECT_MODEL = {
    "Japan_WarFactory": ("JP_WarFactory", "JP_WarFactory.NKr_WarFactory", "HOUSECOLOR01 HOUSECOLOR02 HOUSECOLOR03"),
    "SouthKorea_WarFactory": ("SK_WarFactory", "SK_WarFactory.NKr_WarFactory", "HOUSECOLOR01 HOUSECOLOR02 HOUSECOLOR03"),
    "India_WarFactory_T": ("IN_WarFactory", "IN_WarFactory.Irq_WarFactory", "HOUSECOLOR01 HOUSECOLOR02 HOUSECOLOR03"),
    "SaudiArabia_WarFactory_T": ("SA_WarFactory", "SA_WarFactory.Irq_WarFactory", "HOUSECOLOR01 HOUSECOLOR02 HOUSECOLOR03"),
    "UAE_WarFactory_T": ("AE_WarFactory", "AE_WarFactory.Irq_WarFactory", "HOUSECOLOR01 HOUSECOLOR02 HOUSECOLOR03"),
    "GermanyWarFactory": ("DE_WarFactory", "DE_WarFactory.US_WarFactory", "HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06"),
    "FranceWarFactory": ("FR_WarFactory", "FR_WarFactory.US_WarFactory", "HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06"),
    "TurkeyWarFactory": ("TR_WarFactory", "TR_WarFactory.US_WarFactory", "HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06"),
    "UkraineWarFactory": ("UA_WarFactory", "UA_WarFactory.US_WarFactory", "HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06"),
    "SwedenWarFactory": ("SE_WarFactory", "SE_WarFactory.US_WarFactory", "HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06"),
    "AmericaWarFactory_T": (None, None, "HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06"),
    "AmericaWarFactory": (None, None, "HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06"),
}

UNTOUCHED = (
    "BritainWarFactory",
    "ItalyWarFactory",
    "NatoWarFactory",
    "Vietnam_WarFactory",
    "NorthKorea_WarFactory",
)


def parse_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for _ in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((name, data[eoff : eoff + esz]))
    return entries


def build_big_ordered(entries):
    header_size = 16
    encoded = [(n.encode("latin1"), b) for n, b in entries]
    for nb, _blob in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for nb, blob in encoded:
        index.append((nb, offset, len(blob)))
        blobs.append(blob)
        offset += len(blob)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def last_object_span(text: str, obj: str):
    hits = list(re.finditer(rf"(?ms)^Object\s+{re.escape(obj)}\s*\r?\n.*?(?=^Object\s|\Z)", text))
    return hits[-1] if hits else None


def write_tga(img: Image.Image) -> bytes:
    img = img.convert("RGB")
    w, h = img.size
    pixels = img.load()
    buf = bytearray()
    buf += bytes([0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    buf += struct.pack("<HH", w, h)
    buf += bytes([24, 0])
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, h - 1 - y]
            buf += bytes([b, g, r])
    return bytes(buf)


def muted_flag(style: str, size=(128, 64)) -> Image.Image:
    w, h = size
    im = Image.new("RGB", (w, h), (90, 95, 85))
    d = ImageDraw.Draw(im)

    def sx(x):
        return int(x * w / 128)

    def sy(y):
        return int(y * h / 64)

    if style == "japan":
        im.paste((214, 214, 210), [0, 0, w, h])
        d.ellipse((sx(44), sy(12), sx(84), sy(52)), fill=(150, 36, 36))
    elif style == "korea":
        im.paste((214, 214, 210), [0, 0, w, h])
        d.ellipse((sx(48), sy(16), sx(80), sy(48)), fill=(150, 40, 40))
        d.pieslice((sx(48), sy(16), sx(80), sy(48)), 90, 270, fill=(32, 56, 92))
        d.rectangle((sx(8), sy(10), sx(22), sy(14)), fill=(40, 40, 40))
        d.rectangle((sx(106), sy(50), sx(120), sy(54)), fill=(40, 40, 40))
    elif style == "india":
        d.rectangle((0, 0, w, sy(21)), fill=(166, 92, 38))
        d.rectangle((0, sy(21), w, sy(43)), fill=(220, 216, 200))
        d.rectangle((0, sy(43), w, h), fill=(46, 92, 52))
        d.ellipse((sx(56), sy(24), sx(72), sy(40)), outline=(30, 48, 88), width=max(1, w // 64))
    elif style == "saudi":
        im.paste((36, 78, 42), [0, 0, w, h])
        d.rectangle((sx(18), sy(22), sx(110), sy(30)), fill=(214, 214, 200))
        d.rectangle((sx(28), sy(36), sx(100), sy(40)), fill=(214, 214, 200))
        d.polygon([(sx(100), sy(36)), (sx(112), sy(38)), (sx(100), sy(40))], fill=(214, 214, 200))
    elif style == "uae":
        d.rectangle((0, 0, sx(28), h), fill=(132, 36, 36))
        d.rectangle((sx(28), 0, w, sy(21)), fill=(46, 92, 52))
        d.rectangle((sx(28), sy(21), w, sy(43)), fill=(220, 216, 200))
        d.rectangle((sx(28), sy(43), w, h), fill=(36, 36, 36))
    elif style == "germany":
        d.rectangle((0, 0, w, sy(21)), fill=(28, 28, 28))
        d.rectangle((0, sy(21), w, sy(43)), fill=(120, 36, 36))
        d.rectangle((0, sy(43), w, h), fill=(168, 132, 48))
    elif style == "france":
        d.rectangle((0, 0, sx(42), h), fill=(36, 56, 96))
        d.rectangle((sx(42), 0, sx(86), h), fill=(220, 216, 200))
        d.rectangle((sx(86), 0, w, h), fill=(132, 40, 40))
    elif style == "turkey":
        im.paste((132, 32, 36), [0, 0, w, h])
        d.ellipse((sx(40), sy(16), sx(80), sy(48)), fill=(220, 216, 200))
        d.ellipse((sx(48), sy(20), sx(82), sy(44)), fill=(132, 32, 36))
        d.regular_polygon((sx(86), sy(32), max(3, sx(7))), 5, fill=(220, 216, 200))
    elif style == "ukraine":
        d.rectangle((0, 0, w, sy(32)), fill=(36, 72, 120))
        d.rectangle((0, sy(32), w, h), fill=(176, 148, 48))
    elif style == "sweden":
        im.paste((36, 72, 110), [0, 0, w, h])
        d.rectangle((sx(40), 0, sx(56), h), fill=(188, 160, 52))
        d.rectangle((0, sy(26), w, sy(38)), fill=(188, 160, 52))
    elif style == "usa":
        im.paste((36, 48, 84), [0, 0, sx(50), sy(34)])
        for i in range(13):
            y0 = sy(i * 64 / 13)
            y1 = sy((i + 1) * 64 / 13)
            d.rectangle((0, y0, w, y1), fill=(150, 40, 40) if i % 2 == 0 else (214, 214, 210))
        d.rectangle((0, 0, sx(50), sy(34)), fill=(36, 48, 84))
    else:
        im.paste((90, 95, 85), [0, 0, w, h])
    return im


def paint_us_atlas(atlas: Image.Image, style: str) -> Image.Image:
    out = atlas.convert("RGB").copy()
    x0, y0, x1, y1 = US_FLAG_BOX
    flag = muted_flag(style, (x1 - x0, y1 - y0))
    region = out.crop(US_FLAG_BOX)
    dirt = ImageEnhance.Contrast(region.convert("L")).enhance(0.55).convert("RGB")
    mixed = Image.blend(flag, dirt, 0.22)
    out.paste(mixed, (x0, y0))
    return out


def chunks(data, start, end):
    pos = start
    while pos + 8 <= end:
        ctype, csize = struct.unpack_from("<II", data, pos)
        has = csize & 0x80000000
        size = csize & 0x7FFFFFFF
        payload = pos + 8
        nxt = payload + size
        if nxt > end:
            break
        yield pos, ctype, has, payload, nxt
        pos = nxt


def walk(data, start, end):
    for pos, ctype, has, payload, nxt in chunks(data, start, end):
        yield pos, ctype, has, payload, nxt
        if has:
            yield from walk(data, payload, nxt)


def replace_bytes_at(buf: bytearray, off: int, old: bytes, new: bytes):
    if len(old) != len(new):
        raise SystemExit(f"texture name length {len(old)} != {len(new)}")
    if buf[off : off + len(old)] != old:
        raise SystemExit(f"texture mismatch at {off}: {buf[off:off+len(old)]!r}")
    buf[off : off + len(new)] = new


def clone_irq_w3d(src: bytes, new_flag: str) -> bytes:
    out = bytearray(src)
    for old in (b"IraqiFlag.tga", b"DPRK_Flag.tga"):
        off = 0
        repl = 0
        while True:
            i = out.find(old, off)
            if i < 0:
                break
            replace_bytes_at(out, i, old, new_flag.encode("ascii"))
            repl += 1
            off = i + len(old)
        if repl:
            print("  replaced", old.decode(), "x", repl, "->", new_flag)
    return bytes(out)


def clone_us_w3d(src: bytes, new_flag: str) -> bytes:
    out = bytearray(src)
    current = None
    replaced = []
    new = new_flag.encode("ascii")
    old = b"US_BUILDINGS.tga"
    for _pos, ctype, _has, pl, _nx in walk(src, 0, len(src)):
        if ctype == 0x1F:
            current = src[pl + 8 : pl + 24].split(b"\x00", 1)[0].decode("ascii", "replace")
        if ctype == 0x32 and current in ("F1", "F2", "F3"):
            replace_bytes_at(out, pl, old, new)
            replaced.append(current)
            print("  US mesh", current, "->", new_flag)
    if sorted(replaced) != ["F1", "F2", "F3"]:
        raise SystemExit(f"expected F1/F2/F3 once each, got {replaced}")
    return bytes(out)


def insert_hide_after_models(blk: str, hide: str) -> str:
    newline = nl(blk)
    out = []
    lines = blk.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        if re.match(r"^\s*Model\s+=", line):
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            already = j < len(lines) and re.match(r"^\s*HideSubObject\s+=", lines[j])
            if not already:
                indent = re.match(r"^(\s*)", line).group(1)
                out.append(f"{indent}HideSubObject    = {hide}{newline}")
        i += 1
    return "".join(out)


def patch_object_visual(blk: str, obj: str) -> str:
    model, anim, hide = OBJECT_MODEL[obj]
    blk = re.sub(r"(?m)^(\s*OkToChangeModelColor\s*=\s*)\S+", r"\g<1>No", blk)
    if model:
        blk = re.sub(r"(?m)^(\s*Model\s+=\s+)\S+", rf"\1{model}", blk)
        blk = re.sub(r"(?m)^(\s*Animation\s+=\s+)\S+", rf"\1{anim}", blk)
    return insert_hide_after_models(blk, hide)


def art_index_map(entries):
    return {norm(n): i for i, (n, _) in enumerate(entries)}


def find_art(entries, index, *cands):
    for c in cands:
        k = norm(c)
        if k in index:
            return entries[index[k]][1]
    raise SystemExit(f"missing ART {cands}")


def write_preview(flags: dict[str, Image.Image], atlases: dict[str, Image.Image]) -> None:
    labels = [
        ("japan", "Japan"),
        ("korea", "South Korea"),
        ("india", "India"),
        ("saudi", "Saudi Arabia"),
        ("uae", "UAE"),
        ("germany", "Germany"),
        ("france", "France"),
        ("turkey", "Turkey"),
        ("ukraine", "Ukraine"),
        ("sweden", "Sweden"),
    ]
    cell_w, cell_h = 160, 90
    cols = 5
    rows = 2
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h + 28), (40, 42, 38))
    d = ImageDraw.Draw(sheet)
    d.text((8, 6), "War Factory national markings (muted, flag-only)", fill=(210, 210, 200))
    for i, (style, label) in enumerate(labels):
        r, c = divmod(i, cols)
        x, y = c * cell_w + 8, 28 + r * cell_h + 4
        sheet.paste(flags[style].resize((128, 64), Image.Resampling.NEAREST), (x, y + 14))
        d.text((x, y), label, fill=(200, 200, 190))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW)
    print("preview", PREVIEW)


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing source BIG", file=sys.stderr)
        return 1

    data_entries = parse_big(SRC_DATA)
    art_entries = parse_big(SRC_ART)
    data_index = {norm(n): i for i, (n, _) in enumerate(data_entries)}
    art_index = art_index_map(art_entries)
    src_data_names = [n for n, _ in data_entries]
    src_art_names = [n for n, _ in art_entries]

    us_atlas = Image.open(
        io.BytesIO(find_art(art_entries, art_index, r"Art\Textures\US_BUILDINGS.dds", r"Art\Textures\US_BUILDINGS.tga"))
    ).convert("RGB")
    if us_atlas.size != (512, 512):
        raise SystemExit(f"US_BUILDINGS size {us_atlas.size}, expected 512x512")

    flag_images = {style: muted_flag(style) for _stem, (_d, _t, _k, style) in NEW_STEMS.items()}
    flag_images["usa"] = muted_flag("usa")

    tex_blobs = {}
    atlas_preview = {}
    for stem, (_donor, tex, kind, style) in NEW_STEMS.items():
        if kind == "irq":
            img = flag_images[style]
            if len(tex) != 13:
                raise SystemExit(f"{tex} must be 13 chars")
        else:
            img = paint_us_atlas(us_atlas, style)
            atlas_preview[style] = img.crop(US_FLAG_BOX)
            if len(tex) != 16:
                raise SystemExit(f"{tex} must be 16 chars")
        tex_blobs[tex] = write_tga(img)
        print("flag", tex, "style", style, "bytes", len(tex_blobs[tex]), "size", img.size)

    write_preview(flag_images, atlas_preview)

    donors = {}
    for stem, (donor, tex, kind, _style) in NEW_STEMS.items():
        dkey = norm(rf"Art\W3D\{donor}.W3D")
        if dkey not in art_index:
            raise SystemExit(f"missing donor {donor}")
        raw = art_entries[art_index[dkey]][1]
        if kind == "irq":
            cloned = clone_irq_w3d(raw, tex)
        else:
            cloned = clone_us_w3d(raw, tex)
        donors[stem] = cloned
        print("cloned", stem, "from", donor, "bytes", len(cloned))

    for tex, blob in tex_blobs.items():
        path = rf"Art\Textures\{tex}"
        if norm(path) in art_index:
            raise SystemExit(f"refusing to overwrite existing ART {path}")
        art_entries.append((path, blob))
        art_index[norm(path)] = len(art_entries) - 1
        print("added", path)
    for stem, blob in donors.items():
        path = rf"Art\W3D\{stem}.W3D"
        if norm(path) in art_index:
            raise SystemExit(f"refusing to overwrite existing ART {path}")
        art_entries.append((path, blob))
        art_index[norm(path)] = len(art_entries) - 1
        print("added", path)

    for i, (name, blob) in enumerate(data_entries):
        if "warfactory" not in name.lower() or not name.lower().endswith(".ini"):
            continue
        if norm(name) in LOCKED_PATHS:
            raise SystemExit(f"locked {name}")
        text = blob.decode("latin1")
        changed = False
        for obj in OBJECT_MODEL:
            m = last_object_span(text, obj)
            if not m:
                continue
            new_blk = patch_object_visual(m.group(0), obj)
            if new_blk != m.group(0):
                text = text[: m.start()] + new_blk + text[m.end() :]
                changed = True
        if changed:
            data_entries[i] = (name, text.encode("latin1"))
            print("patched", name)

    if [n for n, _ in data_entries][: len(src_data_names)] != src_data_names:
        raise SystemExit("DATA entry order prefix changed")
    if [n for n, _ in art_entries][: len(src_art_names)] != src_art_names:
        raise SystemExit("ART entry order prefix changed")
    if len(data_entries) != len(src_data_names):
        raise SystemExit("DATA file count changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(data_entries)
    art_big = build_big_ordered(art_entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_big)
    print("DATA_SHA256", hashlib.sha256(data_big).hexdigest())
    print("ART_SHA256", hashlib.sha256(art_big).hexdigest())
    print("DATA_BYTES", len(data_big), "FILES", len(data_entries))
    print("ART_BYTES", len(art_big), "FILES", len(art_entries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
