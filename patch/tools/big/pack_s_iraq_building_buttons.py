#!/usr/bin/env python3
"""Iraq-only construction-menu ButtonImage integration.

Baseline: PR #614 SPECTER_MISSILE_FACTORY_PREREQ
  DATA 366670870 SHA f00a086300d8e6c552bb6e2c29dd63d875a326f44457fc051dbf9635f5ff2ea3
  ART  1305667638 SHA fa46c291d9cec1b106977e7a5ec3ded54e9bc0c9e2c94ab4d4852b90d4e96359

Source images (already uploaded to GitHub, not redrawn):
  ChatGPT Image Oct 10, 2026, 07_01_48 PM.png  (12 labeled cameos)
  ChatGPT Image Oct 10, 2026, 07_02_03 PM.png  (Aircraft / Fighter)

Only Iraq DOZER_CONSTRUCT CommandButton ButtonImage values change.
Object SelectPortrait / ButtonImage, CommandSets, prerequisites, and
non-Iraq buttons stay byte-identical. Static validation only.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_MISSILE_FACTORY_PREREQ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_MISSILE_FACTORY_PREREQ/_SPEC_ART_ONE.big"
SHEET_12 = ROOT / "ChatGPT Image Oct 10, 2026, 07_01_48 PM.png"
SHEET_2 = ROOT / "ChatGPT Image Oct 10, 2026, 07_02_03 PM.png"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_BUILDING_BUTTONS"
UI_DIR = ROOT / "patch/Art/Textures/UI/iraq_buildings"
LOOSE_CB = ROOT / "patch/Data/INI/CommandButton.ini"
LOOSE_MAPPED = ROOT / "patch/Data/INI/MappedImages/HandCreated/IraqBuildingCameos_Images.INI"

SHA_DATA_614 = "f00a086300d8e6c552bb6e2c29dd63d875a326f44457fc051dbf9635f5ff2ea3"
SIZE_DATA_614 = 366670870
SHA_ART_614 = "fa46c291d9cec1b106977e7a5ec3ded54e9bc0c9e2c94ab4d4852b90d4e96359"
SIZE_ART_614 = 1305667638

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
PK_KEY = r"Data\INI\CommandSet_Pakistan.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\IraqBuildingCameos_Images.INI"

TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")

# Contact-sheet layout from the two uploaded PNGs.
SHEET12_NAMES = [
    "commandcenter",
    "camp",
    "powerplant",
    "supplycenter",
    "warfactory",
    "radar",
    "atom",
    "bio",
    "missilefactory",
    "cram",
    "mim80",
    "mantis",
]
SHEET2_NAMES = ["aircraftbase", "fighterbase"]

# Unique MappedImage names. Do not reuse irq_* portraits.
TILE_TO_MAPPED = {
    "commandcenter": "irqbtn_cmdctr",
    "camp": "irqbtn_camp",
    "powerplant": "irqbtn_power",
    "supplycenter": "irqbtn_supply",
    "warfactory": "irqbtn_warfac",
    "radar": "irqbtn_radar",
    "atom": "irqbtn_atom",
    "missilefactory": "irqbtn_mslfac",
    "aircraftbase": "irqbtn_airbase",
    "fighterbase": "irqbtn_fighter",
}

# Packed last-wins Iraq DOZER_CONSTRUCT buttons that have a matching uploaded image
# AND a real Iraqi constructible building.
BTN_TO_TILE = {
    "Command_ConstructIraq_CommandCenter": "commandcenter",
    "Command_ConstructIraq_Barracks": "camp",  # model irq_camp
    "Command_ConstructIraq_PowerPlant": "powerplant",
    "Command_ConstructIraq_SupplyCenter": "supplycenter",
    "Command_ConstructIraq_WarFactory_T": "warfactory",
    "Command_ConstructIraqMilitaryWarfactory": "warfactory",
    "Command_ConstructIraq_RadarStation": "radar",
    "Command_ConstructIraq_Abbas": "atom",
    "Command_ConstructIraq_Abbas_AI": "atom",
    "Command_ConstructIraq_AlFahdMissileFactory": "missilefactory",
    "Command_ConstructIraq_HeavyAirBase": "aircraftbase",
    "Command_ConstructIraq_Airfield_T": "fighterbase",
    "Command_ConstructIraqMilitaryAirfield": "fighterbase",
}

IRAQ_CONSTRUCT_KEEP = [
    "Command_ConstructIraq_MIC",
    "Command_ConstructIraq_DefenseSite",
    "Command_ConstructIraq_Sam2",
    "Command_ConstructIraq_100mmCannon",
    "Command_ConstructIraq_D30_Howitzer",
    "Command_ConstructIraqFahad3SamSite",
]

FORBIDDEN_NON_IRAQ_PREFIXES = (
    "Command_ConstructUkraine",
    "Command_ConstructTurkey",
    "Command_ConstructItaly",
    "Command_ConstructSweden",
    "Command_ConstructBritain",
    "Command_ConstructFrance",
    "Command_ConstructGermany",
    "Command_ConstructNato",
    "Command_ConstructChina",
    "Command_ConstructAmerica",
    "Command_ConstructRussia",
    "Command_ConstructIndia",
    "Command_ConstructPakistan",
    "Command_ConstructSaudi",
    "Command_ConstructUAE",
    "Command_ConstructSyria",
    "Command_ConstructLibya",
    "Command_ConstructSouthAfrica",
    "Command_ConstructSouthKorea",
    "Command_ConstructNorthKorea",
    "Command_ConstructVietnam",
    "Command_ConstructJapan",
    "Command_ConstructEgypt",
    "Command_ConstructIran",
    "Command_ConstructIsrael",
    "Command_ConstructTaiwan",
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


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def parse_big(data: bytes) -> dict[str, bytes]:
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


def iter_blocks(text: bytes, header_prefix: bytes):
    lines = text.splitlines(True)
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith(header_prefix):
            name = ln.split(None, 1)[-1].strip().decode("latin1", "replace")
            start = i
            i += 1
            while i < len(lines):
                if lines[i] in (b"End\r\n", b"End\n", b"End"):
                    yield name, b"".join(lines[start : i + 1]), start, i
                    i += 1
                    break
                i += 1
            else:
                break
        else:
            i += 1


def last_button(blob: bytes, name: str) -> str:
    last = ""
    for n, block, _, _ in iter_blocks(blob, b"CommandButton "):
        if n == name:
            last = block.decode("latin1")
    return last


def field(body: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(\S+)", body, re.M)
    return m.group(1) if m else ""


def crop_grid(im: Image.Image, rows: int, cols: int) -> list[Image.Image]:
    arr = np.array(im.convert("RGB"))
    lum = arr.mean(axis=2)
    ys, xs = np.where(lum > 28)
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    cw = (x1 - x0 + 1) / cols
    ch = (y1 - y0 + 1) / rows
    tiles = []
    for r in range(rows):
        for c in range(cols):
            gx0 = x0 + c * cw + cw * 0.02
            gy0 = y0 + r * ch + ch * 0.02
            gx1 = x0 + (c + 1) * cw - cw * 0.02
            gy1 = y0 + (r + 1) * ch - ch * 0.02
            tile = im.crop((int(gx0), int(gy0), int(gx1), int(gy1)))
            tiles.append(tight_card(tile))
    return tiles


def tight_card(im: Image.Image) -> Image.Image:
    arr = np.array(im.convert("RGB"))
    lum = arr.mean(axis=2)
    ys, xs = np.where(lum > 22)
    if len(xs) == 0:
        return im
    pad = 2
    x0 = max(int(xs.min()) - pad, 0)
    y0 = max(int(ys.min()) - pad, 0)
    x1 = min(int(xs.max()) + pad + 1, im.size[0])
    y1 = min(int(ys.max()) + pad + 1, im.size[1])
    return im.crop((x0, y0, x1, y1))


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
    imgtype = blob[2]
    w, h = struct.unpack_from("<HH", blob, 12)
    bpp, desc = blob[16], blob[17]
    return {
        "width": w,
        "height": h,
        "type": imgtype,
        "bpp": bpp,
        "alpha_bits": desc & 0x0F,
        "descriptor": f"0x{desc:02x}",
        "origin": "top" if desc & 0x20 else "bottom",
    }


def mapped_ini(names: list[str]) -> str:
    lines = [
        "; SPECTER Iraq construction-menu cameos.",
        "; Sliced from uploaded GitHub contact sheets. Iraq construct buttons only.",
        "; Do not reuse these MappedImages as SelectPortrait or unit-production icons.",
        "",
    ]
    for name in names:
        lines += [
            f"MappedImage {name}",
            f"  Texture = {name}.tga",
            "  TextureWidth = 128",
            "  TextureHeight = 128",
            "  Coords = Left:0 Top:0 Right:128 Bottom:128",
            "  Status = NONE",
            "End",
            "",
        ]
    return "\r\n".join(lines)


def splice_button_images(blob: bytes, mapping: dict[str, str]) -> bytes:
    lines = blob.splitlines(True)
    i = 0
    out = []
    while i < len(lines):
        ln = lines[i]
        if ln.startswith(b"CommandButton "):
            name = ln.split(None, 1)[-1].strip().decode("latin1", "replace")
            block = [ln]
            i += 1
            while i < len(lines):
                block.append(lines[i])
                if lines[i] in (b"End\r\n", b"End\n", b"End"):
                    i += 1
                    break
                i += 1
            if name in mapping:
                new_img = mapping[name].encode("latin1")
                replaced = False
                for j, bl in enumerate(block):
                    if re.match(rb"^\s*ButtonImage\s*=", bl):
                        block[j] = re.sub(
                            rb"(ButtonImage\s*=\s*)\S+",
                            rb"\1" + new_img,
                            bl,
                            count=1,
                        )
                        replaced = True
                if not replaced:
                    raise SystemExit(f"no ButtonImage in {name}")
            out.extend(block)
        else:
            out.append(ln)
            i += 1
    return b"".join(out)


def extract_tiles() -> dict[str, Image.Image]:
    if not SHEET_12.is_file() or not SHEET_2.is_file():
        raise SystemExit("uploaded ChatGPT contact sheets missing")
    sheet12 = Image.open(SHEET_12).convert("RGB")
    sheet2 = Image.open(SHEET_2).convert("RGB")
    tiles12 = crop_grid(sheet12, 3, 4)
    tiles2 = crop_grid(sheet2, 1, 2)
    out = {}
    for name, im in zip(SHEET12_NAMES, tiles12):
        out[name] = im
    for name, im in zip(SHEET2_NAMES, tiles2):
        out[name] = im
    return out


def write_loose_sources(tiles: dict[str, Image.Image], mapped_text: str) -> None:
    UI_DIR.mkdir(parents=True, exist_ok=True)
    for name, im in tiles.items():
        im.save(UI_DIR / f"{name}.png")
    LOOSE_MAPPED.parent.mkdir(parents=True, exist_ok=True)
    LOOSE_MAPPED.write_text(mapped_text.replace("\r\n", "\n") + "\n", encoding="latin1")
    if LOOSE_CB.is_file():
        raw = LOOSE_CB.read_bytes()
        # Only buttons that already exist in the loose file.
        loose_map = {
            name: TILE_TO_MAPPED[tile]
            for name, tile in BTN_TO_TILE.items()
            if f"CommandButton {name}".encode("ascii") in raw
        }
        LOOSE_CB.write_bytes(splice_button_images(raw, loose_map))


def validate(
    data: dict[str, bytes],
    art: dict[str, bytes],
    src_data: dict[str, bytes],
    src_art: dict[str, bytes],
    tgas: dict[str, bytes],
) -> list[str]:
    fails: list[str] = []
    added_data = set(data) - set(src_data)
    removed_data = set(src_data) - set(data)
    if added_data != {MAPPED_KEY}:
        fails.append(f"DATA added unexpected {added_data}")
    if removed_data:
        fails.append(f"DATA removed {removed_data}")
    mutated_data = sorted(k for k in src_data if src_data[k] != data.get(k))
    if mutated_data != [CB_KEY]:
        fails.append(f"unexpected DATA mutations: {mutated_data}")
    if data[CS_KEY] != src_data[CS_KEY]:
        fails.append("CommandSet.ini mutated")
    if data[PK_KEY] != src_data[PK_KEY]:
        fails.append("CommandSet_Pakistan.ini mutated")
    if data[FACTORY_KEY] != src_data[FACTORY_KEY]:
        fails.append("missile factory object mutated")

    added_art = set(art) - set(src_art)
    removed_art = set(src_art) - set(art)
    expected_art = {rf"Art\Textures\{name}.tga" for name in TILE_TO_MAPPED.values()}
    if added_art != expected_art:
        fails.append(f"ART added unexpected {added_art ^ expected_art}")
    if removed_art:
        fails.append(f"ART removed {removed_art}")
    mutated_art = [k for k in src_art if src_art[k] != art.get(k)]
    if mutated_art:
        fails.append(f"existing ART mutated: {mutated_art[:8]}")

    mapped = data[MAPPED_KEY].decode("latin1")
    for name in TILE_TO_MAPPED.values():
        if f"MappedImage {name}" not in mapped:
            fails.append(f"missing MappedImage {name}")
        if f"Texture = {name}.tga" not in mapped:
            fails.append(f"missing texture ref {name}")
        key = rf"Art\Textures\{name}.tga"
        if key not in art:
            fails.append(f"missing ART {key}")
        else:
            info = tga_info(art[key])
            if info["type"] != 2 or info["bpp"] != 24 or info["alpha_bits"] != 0:
                fails.append(f"bad TGA {name}: {info}")
            if info["width"] != 128 or info["height"] != 128:
                fails.append(f"TGA size {name}: {info['width']}x{info['height']}")
            if art[key] != tgas[name]:
                fails.append(f"ART TGA mismatch {name}")

    src_cb = src_data[CB_KEY]
    new_cb = data[CB_KEY]
    src_btns = {n: b for n, b, _, _ in iter_blocks(src_cb, b"CommandButton ")}
    new_btns = {}
    for n, b, _, _ in iter_blocks(new_cb, b"CommandButton "):
        new_btns[n] = b
    if set(src_btns) != set(new_btns):
        fails.append("CommandButton name set changed")

    for name, src_block in src_btns.items():
        new_block = new_btns[name]
        src_text = src_block.decode("latin1")
        new_text = new_block.decode("latin1")
        if name in BTN_TO_TILE:
            want = TILE_TO_MAPPED[BTN_TO_TILE[name]]
            if field(new_text, "ButtonImage") != want:
                fails.append(f"{name} ButtonImage={field(new_text, 'ButtonImage')} want {want}")
            if field(new_text, "Command") != "DOZER_CONSTRUCT":
                fails.append(f"{name} Command changed")
            if field(src_text, "Object") != field(new_text, "Object"):
                fails.append(f"{name} Object changed")
            if field(src_text, "TextLabel") != field(new_text, "TextLabel"):
                fails.append(f"{name} TextLabel changed")
            def strip_img(s: str) -> str:
                return re.sub(r"(ButtonImage\s*=\s*)\S+", r"\1X", s)
            if strip_img(src_text) != strip_img(new_text):
                fails.append(f"{name} changed beyond ButtonImage")
        else:
            if src_block != new_block:
                fails.append(f"non-target button mutated: {name}")
            if name.startswith(FORBIDDEN_NON_IRAQ_PREFIXES):
                if src_block != new_block:
                    fails.append(f"non-Iraq button mutated: {name}")

    for name in IRAQ_CONSTRUCT_KEEP:
        if last_button(new_cb, name) != last_button(src_cb, name):
            fails.append(f"kept Iraq construct button mutated: {name}")

    # Object portraits must still use original images.
    for obj_key, old_img in [
        (FACTORY_KEY, "irq_warfctry"),
    ]:
        body = data[obj_key].decode("latin1")
        if f"ButtonImage            = {old_img}" not in body and "ButtonImage" in body:
            if field(body, "ButtonImage") in TILE_TO_MAPPED.values():
                fails.append("factory object portrait retargeted")

    # Confirm Iraq construction CommandSets still reference the same buttons.
    cs = data[CS_KEY].decode("latin1")
    src_cs = src_data[CS_KEY].decode("latin1")
    for set_name in ("Iraq_VT72BCommandSet", "Iraq_WorkerCommandSet"):
        a = re.search(rf"(?ms)^CommandSet {set_name}\r?\n.*?^End", cs)
        b = re.search(rf"(?ms)^CommandSet {set_name}\r?\n.*?^End", src_cs)
        if not a or not b or a.group(0) != b.group(0):
            fails.append(f"{set_name} mutated")

    return fails


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_614 or SRC_DATA.stat().st_size != SIZE_DATA_614:
        raise SystemExit("DATA baseline mismatch")
    if sha256_path(SRC_ART) != SHA_ART_614 or SRC_ART.stat().st_size != SIZE_ART_614:
        raise SystemExit("ART baseline mismatch")

    tiles = extract_tiles()
    mapped_names = [TILE_TO_MAPPED[t] for t in TILE_TO_MAPPED]
    mapped_text = mapped_ini(mapped_names)
    write_loose_sources(tiles, mapped_text)

    tgas = {TILE_TO_MAPPED[name]: make_tga24(tiles[name]) for name in TILE_TO_MAPPED}
    btn_map = {btn: TILE_TO_MAPPED[tile] for btn, tile in BTN_TO_TILE.items()}

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    data[CB_KEY] = splice_button_images(src_data[CB_KEY], btn_map)
    data[MAPPED_KEY] = mapped_text.encode("latin1")
    for name, blob in tgas.items():
        art[rf"Art\Textures\{name}.tga"] = blob

    fails = validate(data, art, src_data, src_art, tgas)
    data_big = build_big(data)
    art_big = build_big(art)
    fails.extend(f"DATA {x}" for x in big_structure_ok(data_big))
    fails.extend(f"ART {x}" for x in big_structure_ok(art_big))
    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_big)
    art_path.write_bytes(art_big)

    ext = OUT / "LAST_WINS_EXTRACT"
    (ext / "DATA").mkdir(parents=True)
    (ext / "ART").mkdir(parents=True)
    (ext / "DATA" / "CommandButton_IraqConstruct.ini").write_bytes(
        b"\r\n".join(
            last_button(data[CB_KEY], name).encode("latin1")
            for name in BTN_TO_TILE
        )
    )
    (ext / "DATA" / "IraqBuildingCameos_Images.INI").write_bytes(data[MAPPED_KEY])
    for name in TILE_TO_MAPPED.values():
        (ext / "ART" / f"{name}.tga").write_bytes(art[rf"Art\Textures\{name}.tga"])

    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_BUILDING_BUTTONS.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    integrated = [
        "Aircraft Base -> Command_ConstructIraq_HeavyAirBase -> Iraq_HeavyAirBase (irqbtn_airbase)",
        "Fighter Base -> Command_ConstructIraq_Airfield_T / MilitaryAirfield -> Iraq_LargeAirBase (irqbtn_fighter)",
        "Command Center -> Command_ConstructIraq_CommandCenter -> Iraq_CommandCenter (irqbtn_cmdctr)",
        "Camp -> Command_ConstructIraq_Barracks -> Iraq_Barracks model irq_camp (irqbtn_camp)",
        "Power Plant -> Command_ConstructIraq_PowerPlant -> Iraq_PowerPlant (irqbtn_power)",
        "Supply Center -> Command_ConstructIraq_SupplyCenter -> Iraq_SupplyCenter (irqbtn_supply)",
        "War Factory -> Command_ConstructIraq_WarFactory_T / MilitaryWarfactory (irqbtn_warfac)",
        "Radar -> Command_ConstructIraq_RadarStation -> Iraq_RadarStation (irqbtn_radar)",
        "Atom -> Command_ConstructIraq_Abbas / Abbas_AI -> Iraq_Abbas (irqbtn_atom)",
        "Missile Factory -> Command_ConstructIraq_AlFahdMissileFactory (irqbtn_mslfac); not on Iraq dozer menu after #613",
    ]
    unused_images = [
        "bio.png from ChatGPT Image Oct 10, 2026, 07_01_48 PM.png — Iraq has no Bio building; Iraq_MIC is Military Industry Corporation, not assigned",
        "cram.png — no Iraq_CRAM object; not created",
        "mantis.png — no Iraq_Mantis object; not created",
        "mim80.png — no Iraq MIM-80 object; not created",
    ]
    missing_images = [
        "Air Defense — Iraq_DefenseSite / Iraq_Sam2 / Iraq_100mmCannon / IraqFahad3SamSite exist; no uploaded Air Defense card (no AirDefense.png / irq_Defsite replacement uploaded)",
        "Artillery — Iraq_D30_Howitzer exists; no uploaded Artillery card (no Artillery.png / irq_d30 replacement uploaded)",
        "Strategy Center — no Iraq Strategy Center object and no uploaded image",
        "World Market — no Iraq World Market object and no uploaded image",
    ]

    report = []
    report.append("STATIC VALIDATION: PASS")
    report.append("RUNTIME TEST: NOT RUN")
    report.append("BASELINE: PR #614 s-missile-factory-prereq")
    report.append(f"DATA_SIZE={data_path.stat().st_size}")
    report.append(f"DATA_SHA256={data_sha}")
    report.append(f"ART_SIZE={art_path.stat().st_size}")
    report.append(f"ART_SHA256={art_sha}")
    report.append("DATA mutations: CommandButton.ini ButtonImage only + new MappedImage INI")
    report.append("ART mutations: 10 new irqbtn_*.tga only")
    report.append("CommandSets unchanged")
    report.append("Iraq_AlFahdMissileFactory object unchanged")
    report.append("Non-Iraq CommandButtons unchanged")
    report.append("")
    report.append("INTEGRATED:")
    report.extend(f"  {x}" for x in integrated)
    report.append("UNUSED UPLOADED IMAGES:")
    report.extend(f"  {x}" for x in unused_images)
    report.append("MISSING IMAGES / NO IRAQ BUILDING:")
    report.extend(f"  {x}" for x in missing_images)
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n")

    hashes = "\n".join(
        [
            "DATA_CHANGED=YES",
            "ART_CHANGED=YES",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_SIZE={art_path.stat().st_size}",
            f"ART_SHA256={art_sha}",
            f"ZIP_FILE=SPECTER_IRAQ_BUILDING_BUTTONS.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #614",
            "SCOPE=Iraq construction ButtonImage only",
            "STATIC_VALIDATION=PASS",
            "RUNTIME_TEST=NOT RUN",
            "",
        ]
    )
    (OUT / "HASHES.txt").write_text(hashes)
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-building-buttons/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-building-buttons/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-building-buttons/SPECTER_IRAQ_BUILDING_BUTTONS.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-iraq-building-buttons",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-iraq-building-buttons",
                "BASELINE=PR #614",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Iraq construction-menu ButtonImage integration from uploaded GitHub contact sheets.\n"
        "Complete replacement DATA + ART BIGs. Static validation only.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Iraq building construction button images\n\n"
        "- Source: uploaded GitHub contact sheets, sliced (not redrawn).\n"
        "- Iraq DOZER_CONSTRUCT ButtonImage only.\n"
        "- No CommandSet, prerequisite, model, or other-country changes.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text("No last-wins path conflicts. New irqbtn_* names only.\n")
    print("PACKED")
    print(hashes)
    print("\n".join(report))


if __name__ == "__main__":
    main()
