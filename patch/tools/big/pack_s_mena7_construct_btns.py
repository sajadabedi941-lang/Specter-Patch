#!/usr/bin/env python3
"""MENA7 construction-button images from uploaded Button_*.png.

Baseline: PR #618 / #619 SPECTER_EU8_CONSTRUCT_BTNS == SPECTER_ASIA4_CONSTRUCT_BTNS
  DATA 366676852 SHA bae544986974b2c4b96e9071024091f96833b686796dd6bdf0d233003a4603ee
  ART  1306947794 SHA 2a89dd356f1b3938fc9f34b6f63572e758c5f96f2486dfe578daab737b2cc8a7

Countries: Libya, South Africa, UAE, Saudi Arabia, Syria, India, Pakistan.
Mandatory mappings (actual existing construct buttons only):
  M777 / FireBase          -> Button_Artillery
  S-125 / Sam2             -> Button_AirDefense
  Strategy Center          -> DOES NOT EXIST (MIC uses Button_GlobalMarket)
  LGM30G / country Lgm30   -> Button_Atom

Pakistan last-wins: Data\\INI\\CommandButton_Pakistan.ini overrides 11
construct buttons after CommandButton.ini. Both files are spliced.
CommandSets unchanged. Missile factory image retained.
Static validation only.
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
SRC_DATA = ROOT / "patch/Release/SPECTER_ASIA4_CONSTRUCT_BTNS/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_ASIA4_CONSTRUCT_BTNS/_SPEC_ART_ONE.big"
TEX = ROOT / "patch/Art/Textures"
OUT = ROOT / "patch/Release/SPECTER_MENA7_CONSTRUCT_BTNS"
LOOSE_CB = ROOT / "patch/Data/INI/CommandButton.ini"
LOOSE_MAPPED = ROOT / "patch/Data/INI/MappedImages/HandCreated/MENA7ConstructCameos_Images.INI"

SHA_DATA_619 = "bae544986974b2c4b96e9071024091f96833b686796dd6bdf0d233003a4603ee"
SIZE_DATA_619 = 366676852
SHA_ART_619 = "2a89dd356f1b3938fc9f34b6f63572e758c5f96f2486dfe578daab737b2cc8a7"
SIZE_ART_619 = 1306947794

CB_KEY = r"Data\INI\CommandButton.ini"
PK_CB_KEY = r"Data\INI\CommandButton_Pakistan.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
PK_CS_KEY = r"Data\INI\CommandSet_Pakistan.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\MENA7ConstructCameos_Images.INI"
KEEP_MAPPED = (
    r"Data\INI\MappedImages\HandCreated\IraqConstructFix_Images.INI",
    r"Data\INI\MappedImages\HandCreated\IraqBuildingCameos_Images.INI",
    r"Data\INI\MappedImages\HandCreated\IraqAllConstructCameos_Images.INI",
    r"Data\INI\MappedImages\HandCreated\EU8ConstructCameos_Images.INI",
)

TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")
END_MARKERS = (b"End\r\n", b"End\n", b"End", b"END\r\n", b"END\n", b"END")

COUNTRIES = [
    "Libya",
    "SouthAfrica",
    "UAE",
    "SaudiArabia",
    "Syria",
    "India",
    "Pakistan",
]

COUNTRY_LABEL = {
    "Libya": "Libya",
    "SouthAfrica": "South Africa",
    "UAE": "United Arab Emirates",
    "SaudiArabia": "Saudi Arabia",
    "Syria": "Syria",
    "India": "India",
    "Pakistan": "Pakistan",
}

# Country-specific DOZER_CONSTRUCT suffix -> uploaded Button_* MappedImage.
COUNTRY_SUFFIX = {
    "PowerPlant": "Button_PowerPlant",
    "CommandCenter": "Button_CommandCenter",
    "MilitaryHQ": "Button_CommandCenter",
    "SupplyCenter": "Button_SupplyCenter",
    "WarFactory_T": "Button_WarFactory",
    "HeavyAirBase": "Button_AircraftBase",
    "RadarStation": "Button_Radar",
    "Barracks": "Button_Camp",
    "Airfield_T": "Button_FighterBase",
    "Sam2": "Button_AirDefense",
    "FireBase": "Button_Artillery",
    "Lgm30": "Button_Atom",
    "MIC": "Button_GlobalMarket",
    "CRAM": "Button_C-RAM",
    "Abbas": "Button_Atom",
}

NEW_ASSIGN: dict[str, str] = {}
for country in COUNTRIES:
    for suffix, img in COUNTRY_SUFFIX.items():
        NEW_ASSIGN[f"Command_Construct{country}_{suffix}"] = img

# Pakistan Worker slot 2 last-wins as UNIT_BUILD, not a construction button.
NEW_ASSIGN.pop("Command_ConstructPakistan_MilitaryHQ")

KEEP_ALREADY = {
    "Command_ConstructIraq_AlFahdMissileFactory": "Button_MissileFactory",
}

PRESERVE_PRIOR = {
    "Command_ConstructIraq_Abbas": "Button_Bio",
    "Command_ConstructIraq_Abbas_AI": "Button_Bio",
    "Command_ConstructAmericaLgm30": "Button_Atom",
}

NEW_PNG = {
    "Button_C-RAM": TEX / "Button_C-RAM.png",
}

FACTORY_BTN = "Command_ConstructIraq_AlFahdMissileFactory"
IRAQ_DOZER = "Iraq_VT72BCommandSet"

BUILDER_SETS = []
for country in COUNTRIES:
    BUILDER_SETS.append(f"{country}DozerCommandSet")
    BUILDER_SETS.append(f"{country}_VT72BCommandSet")
    BUILDER_SETS.append(f"{country}_WorkerCommandSet")


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
                if lines[i] in END_MARKERS:
                    yield name, b"".join(lines[start : i + 1])
                    i += 1
                    break
                i += 1
            else:
                break
        else:
            i += 1


def last_button_in(blob: bytes, name: str) -> str:
    last = ""
    for n, block in iter_blocks(blob, b"CommandButton "):
        if n == name:
            last = block.decode("latin1")
    return last


def last_button(data: dict[str, bytes], name: str) -> str:
    last = last_button_in(data[CB_KEY], name)
    pk = last_button_in(data.get(PK_CB_KEY, b""), name)
    return pk or last


def last_commandset(data: dict[str, bytes], name: str) -> str:
    last = ""
    for key in (CS_KEY, PK_CS_KEY):
        blob = data.get(key, b"")
        for n, block in iter_blocks(blob, b"CommandSet "):
            if n == name:
                last = block.decode("latin1")
    return last


def field(body: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(\S+)", body, re.M)
    return m.group(1) if m else ""


def slot_map(block: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


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
    rgb = tight_card(im).convert("RGB")
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
    w, h = struct.unpack_from("<HH", blob, 12)
    return {"width": w, "height": h, "type": blob[2], "bpp": blob[16], "alpha_bits": blob[17] & 0x0F}


def mapped_ini(names: list[str]) -> str:
    lines = [
        "; SPECTER MENA7 construct cameos: Button_C-RAM.",
        "; Other Button_* MappedImages already last-win from #616/#617/#618.",
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
                if lines[i] in END_MARKERS:
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


def names_in(blob: bytes) -> set[str]:
    return {n for n, _ in iter_blocks(blob, b"CommandButton ")}


def update_loose(mapped_text: str) -> None:
    LOOSE_MAPPED.parent.mkdir(parents=True, exist_ok=True)
    LOOSE_MAPPED.write_text(mapped_text.replace("\r\n", "\n") + "\n", encoding="latin1")
    if LOOSE_CB.is_file():
        raw = LOOSE_CB.read_bytes()
        loose_map = {
            name: img
            for name, img in NEW_ASSIGN.items()
            if f"CommandButton {name}".encode("ascii") in raw
        }
        if loose_map:
            LOOSE_CB.write_bytes(splice_button_images(raw, loose_map))


def validate(data, art, src_data, src_art, tgas) -> list[str]:
    fails: list[str] = []
    added_data = set(data) - set(src_data)
    if added_data != {MAPPED_KEY}:
        fails.append(f"DATA added unexpected {added_data}")
    if set(src_data) - set(data):
        fails.append("DATA removed files")
    mutated = sorted(k for k in src_data if src_data[k] != data.get(k))
    if mutated != [CB_KEY, PK_CB_KEY]:
        fails.append(f"unexpected DATA mutations: {mutated}")
    if data[CS_KEY] != src_data[CS_KEY]:
        fails.append("CommandSet.ini mutated")
    if data[PK_CS_KEY] != src_data[PK_CS_KEY]:
        fails.append("CommandSet_Pakistan.ini mutated")
    if data[FACTORY_KEY] != src_data[FACTORY_KEY]:
        fails.append("factory object mutated")
    for key in KEEP_MAPPED:
        if data.get(key) != src_data.get(key):
            fails.append(f"{key} mutated")

    added_art = set(art) - set(src_art)
    expected_art = {rf"Art\Textures\{n}.tga" for n in NEW_PNG}
    if added_art != expected_art:
        fails.append(f"ART added unexpected {added_art ^ expected_art}")
    if set(src_art) - set(art):
        fails.append("ART removed files")
    mutated_art = [k for k in src_art if src_art[k] != art.get(k)]
    if mutated_art:
        fails.append(f"existing ART mutated: {mutated_art[:8]}")

    mapped = data[MAPPED_KEY].decode("latin1")
    for name in NEW_PNG:
        if f"MappedImage {name}" not in mapped:
            fails.append(f"missing MappedImage {name}")
        key = rf"Art\Textures\{name}.tga"
        info = tga_info(art[key])
        if info["type"] != 2 or info["bpp"] != 24 or info["width"] != 128:
            fails.append(f"bad TGA {name}: {info}")
        if art[key] != tgas[name]:
            fails.append(f"ART TGA mismatch {name}")

    for key in (CB_KEY, PK_CB_KEY):
        src_btns = {n: b for n, b in iter_blocks(src_data[key], b"CommandButton ")}
        new_btns = {n: b for n, b in iter_blocks(data[key], b"CommandButton ")}
        if set(src_btns) != set(new_btns):
            fails.append(f"{key} CommandButton name set changed")

        def strip_img(s: str) -> str:
            return re.sub(r"(ButtonImage\s*=\s*)\S+", r"\1X", s)

        present = names_in(src_data[key])
        for name, src_block in src_btns.items():
            new_block = new_btns[name]
            src_text = src_block.decode("latin1")
            new_text = new_block.decode("latin1")
            if name in NEW_ASSIGN and name in present:
                want = NEW_ASSIGN[name]
                if field(new_text, "ButtonImage") != want:
                    fails.append(f"{key} {name} ButtonImage={field(new_text, 'ButtonImage')} want {want}")
                if field(new_text, "Command") != field(src_text, "Command"):
                    fails.append(f"{key} {name} Command changed")
                if field(src_text, "Object") != field(new_text, "Object"):
                    fails.append(f"{key} {name} Object changed")
                if strip_img(src_text) != strip_img(new_text):
                    fails.append(f"{key} {name} changed beyond ButtonImage")
            else:
                if src_block != new_block:
                    fails.append(f"non-target button mutated in {key}: {name}")

    for name, img in KEEP_ALREADY.items():
        if field(last_button(data, name), "ButtonImage") != img:
            fails.append(f"kept mapping lost: {name}")
    for name, img in PRESERVE_PRIOR.items():
        if field(last_button(data, name), "ButtonImage") != img:
            fails.append(f"prior mapping lost: {name} want {img}")
    pk_mhq = last_button(data, "Command_ConstructPakistan_MilitaryHQ")
    if field(pk_mhq, "Command") != "UNIT_BUILD":
        fails.append("Pakistan MilitaryHQ last-wins Command changed")
    if field(pk_mhq, "ButtonImage") != "us_commandcenter":
        fails.append("Pakistan MilitaryHQ unit-production ButtonImage changed")

    for country in COUNTRIES:
        for suffix, img in (
            ("FireBase", "Button_Artillery"),
            ("Sam2", "Button_AirDefense"),
            ("MIC", "Button_GlobalMarket"),
            ("Lgm30", "Button_Atom"),
        ):
            name = f"Command_Construct{country}_{suffix}"
            if field(last_button(data, name), "ButtonImage") != img:
                fails.append(f"special mapping failed: {name}")

    iraq = last_commandset(data, IRAQ_DOZER)
    if slot_map(iraq).get(14) != FACTORY_BTN:
        fails.append(f"factory slot 14 lost: {slot_map(iraq).get(14)}")
    for name in BUILDER_SETS + [IRAQ_DOZER, "Iraq_WorkerCommandSet"]:
        if last_commandset(data, name) != last_commandset(src_data, name):
            fails.append(f"CommandSet mutated: {name}")

    # Referenced Button_* textures must exist in packed ART.
    for name in NEW_ASSIGN:
        img = field(last_button(data, name), "ButtonImage")
        tex = rf"Art\Textures\{img}.tga"
        if tex not in art:
            fails.append(f"missing packed texture for {name}: {tex}")
    return fails


def inventory_lines(data: dict[str, bytes], art: dict[str, bytes]) -> list[str]:
    lines = []
    for country in COUNTRIES:
        label = COUNTRY_LABEL[country]
        lines.append(f"# {label}")
        for cs_name in (
            f"{country}DozerCommandSet",
            f"{country}_VT72BCommandSet",
            f"{country}_WorkerCommandSet",
        ):
            body = last_commandset(data, cs_name)
            lines.append(f"## {cs_name}")
            if not body:
                lines.append("  MISSING CommandSet")
                continue
            for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", body, re.M):
                slot, btn = m.group(1), m.group(2)
                block = last_button(data, btn)
                cmd = field(block, "Command")
                obj = field(block, "Object")
                img = field(block, "ButtonImage")
                tex = rf"Art\Textures\{img}.tga"
                tex_ok = tex in art if img.startswith("Button_") else "n/a"
                if cmd != "DOZER_CONSTRUCT":
                    status = "NON-CONSTRUCT preserved"
                elif btn in NEW_ASSIGN:
                    status = "CORRECTED"
                elif btn in KEEP_ALREADY:
                    status = "ALREADY CORRECT"
                else:
                    status = "PRESERVED (no matching uploaded image)"
                lines.append(
                    f"  slot {slot:>2} | {btn} | {obj or '-'} | {cmd} | {img} | {tex} exists={tex_ok} | {status}"
                )
            lines.append("")
        lines.append("### Mandatory mappings")
        for suffix, want, label_s in (
            ("FireBase", "Button_Artillery", "M777"),
            ("Sam2", "Button_AirDefense", "S-125"),
            ("MIC", "Button_GlobalMarket", "Strategy Center (absent; MIC mapped)"),
            ("Lgm30", "Button_Atom", "LGM30G"),
        ):
            name = f"Command_Construct{country}_{suffix}"
            block = last_button(data, name)
            img = field(block, "ButtonImage")
            obj = field(block, "Object")
            tex = rf"Art\Textures\{img}.tga"
            lines.append(
                f"  {label_s} | {name} | {obj} | {img} | {tex} exists={tex in art} | "
                f"{'OK' if img == want else 'MISSING/MISMATCH'}"
            )
        lines.append("  Strategy Center construct button: DOES NOT EXIST")
        lines.append("")
    lines.append("## Preserved prior work")
    for name, img in {**KEEP_ALREADY, **PRESERVE_PRIOR}.items():
        block = last_button(data, name)
        lines.append(
            f"  {name} | {field(block, 'Object')} | {field(block, 'ButtonImage')} | "
            f"{'RETAINED' if field(block, 'ButtonImage') == img else 'LOST'}"
        )
    lines.append(
        f"  Iraq_VT72BCommandSet slot 14 | {FACTORY_BTN} | Button_MissileFactory | RETAINED"
    )
    return lines


def main() -> None:
    missing = [str(p) for p in NEW_PNG.values() if not p.is_file()]
    if missing:
        raise SystemExit("missing uploaded images:\n" + "\n".join(missing))
    if sha256_path(SRC_DATA) != SHA_DATA_619 or SRC_DATA.stat().st_size != SIZE_DATA_619:
        raise SystemExit("DATA baseline mismatch")
    if sha256_path(SRC_ART) != SHA_ART_619 or SRC_ART.stat().st_size != SIZE_ART_619:
        raise SystemExit("ART baseline mismatch")

    mapped_text = mapped_ini(list(NEW_PNG))
    tgas = {name: make_tga24(Image.open(path)) for name, path in NEW_PNG.items()}
    update_loose(mapped_text)

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    pk_present = names_in(src_data[PK_CB_KEY])
    pk_map = {n: img for n, img in NEW_ASSIGN.items() if n in pk_present}
    data[CB_KEY] = splice_button_images(src_data[CB_KEY], NEW_ASSIGN)
    data[PK_CB_KEY] = splice_button_images(src_data[PK_CB_KEY], pk_map)
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

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    inv = inventory_lines(data, art)
    (ext / "MENA7_BuilderCommandSets.ini").write_text(
        "\n".join(last_commandset(data, n) for n in BUILDER_SETS) + "\n"
    )
    btn_extract = [last_button(data, name) for name in sorted(NEW_ASSIGN)]
    btn_extract += [last_button(data, name) for name in KEEP_ALREADY]
    (ext / "CommandButton_MENA7Construct.ini").write_text("\n".join(btn_extract) + "\n")
    (ext / "MENA7ConstructCameos_Images.INI").write_bytes(data[MAPPED_KEY])
    (ext / "CommandButton_Pakistan_spliced.ini").write_bytes(data[PK_CB_KEY])

    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_MENA7_CONSTRUCT_BTNS.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #618 / #619 s-eu8-construct-btns / s-asia4-construct-btns",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "COMMANDSET_UNCHANGED=YES",
        "FACTORY_SLOT14_RETAINED=YES",
        "IRAQ_ABBAS_BUTTON=Button_Bio (unchanged)",
        "AMERICA_LGM30_BUTTON=Button_Atom (unchanged)",
        "PAKISTAN_LAST_WINS_SPLICED=YES",
        "DATA mutations: CommandButton.ini + CommandButton_Pakistan.ini ButtonImage only; new MappedImage INI",
        "ART mutations: Button_C-RAM.tga only",
        "",
        "DOES NOT EXIST:",
        "  Strategy Center construct button / object for Libya, South Africa, UAE, Saudi Arabia, Syria, India, Pakistan",
        "  MIC (DisplayName OBJECT:MIC) is the existing us_stratcenter-image building and uses Button_GlobalMarket",
        "",
        "UNUSED UPLOADED IMAGES:",
        "  Button_StrategyCenter.png — Strategy Center does not exist; MIC/Strategy visual uses Button_GlobalMarket",
        "  Button_Bio.png — Iraq Abbas only; these seven countries use Button_Atom for Abbas nuclear facility",
        "  Button_Mantis.png / Button_DefenceSite.png — no matching building on these seven countries",
        "",
        "CHANGED vs PR #618/#619:",
        "  DATA Data\\INI\\CommandButton.ini — ButtonImage only on seven-country construct buttons",
        "  DATA Data\\INI\\CommandButton_Pakistan.ini — ButtonImage only on Pakistan last-wins construct buttons",
        "  DATA Data\\INI\\MappedImages\\HandCreated\\MENA7ConstructCameos_Images.INI — new",
        "  ART Button_C-RAM.tga",
        "  CommandSet.ini and CommandSet_Pakistan.ini unchanged",
        "",
        "COMPLETE CONSTRUCTION-BUTTON INVENTORY:",
        *inv,
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n")
    hashes = "\n".join(
        [
            "DATA_CHANGED=YES",
            "ART_CHANGED=YES",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_SIZE={art_path.stat().st_size}",
            f"ART_SHA256={art_sha}",
            "ZIP_FILE=SPECTER_MENA7_CONSTRUCT_BTNS.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #618 / #619",
            "FACTORY_SLOT14_RETAINED=YES",
            "PAKISTAN_LAST_WINS_SPLICED=YES",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-mena7-construct-btns/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-mena7-construct-btns/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-mena7-construct-btns/SPECTER_MENA7_CONSTRUCT_BTNS.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-mena7-construct-btns",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-mena7-construct-btns",
                "BASELINE=PR #618 / #619",
                "FACTORY_SLOT14_RETAINED=YES",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Libya, South Africa, UAE, Saudi Arabia, Syria, India, and Pakistan\n"
        "construction-menu ButtonImages from uploaded Button_*.png files.\n"
        "CommandSets unchanged. Pakistan last-wins CommandButton file spliced.\n"
        "Static validation only.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# MENA7 construction button images\n\n"
        "- Libya, South Africa, UAE, Saudi Arabia, Syria, India, and Pakistan construction buttons now use uploaded Button_*.png files.\n"
        "- M777 → Button_Artillery; S-125 → Button_AirDefense; LGM30G → Button_Atom.\n"
        "- Strategy Center does not exist for these countries. MIC uses Button_GlobalMarket.\n"
        "- Pakistan last-wins CommandButton_Pakistan.ini is spliced so Pakistan images actually apply.\n"
        "- CommandSets, missile factory gameplay, and prior Iraq/EU8/Asia4 button work are unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "No last-wins path conflicts. New Button_C-RAM MappedImage only.\n"
        "Pakistan construct buttons last-win from CommandButton_Pakistan.ini; both files spliced.\n"
        "Country-specific CommandButtons only. Command_ConstructAmericaLgm30 and Iraq Abbas untouched.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n")
    print("PACKED")
    print(hashes)
    print("\n".join(report[:45]))
    print(f"assigned {len(NEW_ASSIGN)} CommandButtons; pakistan overrides {len(pk_map)}")


if __name__ == "__main__":
    main()
