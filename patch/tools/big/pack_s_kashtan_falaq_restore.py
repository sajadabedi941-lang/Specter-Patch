#!/usr/bin/env python3
"""Restore dedicated Kashtan / Falaq construction-button artwork.

Baseline: PR #623 SPECTER_KASHTAN_FALAQ_BTNS
  DATA 366682583 SHA 89f2b05fde9e9548170d4232a88744c96f97f5d1440802ce9d23e67d81831d04
  ART  1306997028 SHA d487dd508857a496502bfee0fd5919210346db0d83b80832289035002a0dbdc3

Source artwork (origin/main commit 306191dc, user upload):
  patch/Art/Textures/Button_kashtan.png  1254x1254 RGB
  patch/Art/Textures/Button_falaq.png    1254x1254 RGB

Converted with the established SPECTER construct-cameo pipeline:
  tight-crop, LANCZOS 128x128, TGA 24-bit type-2.
MappedImage names match PNG basenames.

Live buttons:
  Russia slot 5  Command_ConstructRussiaKashtan       -> Button_kashtan
  China  slot 9  Command_ConstructChinaGattlingCannon -> Button_kashtan
  Iran   slot 12 Command_ConstructIranFalaqTrench     -> Button_falaq

CommandSets unchanged. Vanilla Tank_/Nuke_/Infa_/Boss_ untouched.
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
SRC_DATA = ROOT / "patch/Release/SPECTER_KASHTAN_FALAQ_BTNS/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_KASHTAN_FALAQ_BTNS/_SPEC_ART_ONE.big"
TEX = ROOT / "patch/Art/Textures"
OUT = ROOT / "patch/Release/SPECTER_KASHTAN_FALAQ_RESTORE"
LOOSE_CB = ROOT / "patch/Data/INI/CommandButton.ini"
LOOSE_MAPPED = ROOT / "patch/Data/INI/MappedImages/HandCreated/KashtanFalaqCameos_Images.INI"

SHA_DATA_623 = "89f2b05fde9e9548170d4232a88744c96f97f5d1440802ce9d23e67d81831d04"
SIZE_DATA_623 = 366682583
SHA_ART_623 = "d487dd508857a496502bfee0fd5919210346db0d83b80832289035002a0dbdc3"
SIZE_ART_623 = 1306997028

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
PK_KEY = r"Data\INI\CommandSet_Pakistan.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
BUILDING_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactoryBuilding.ini"
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\KashtanFalaqCameos_Images.INI"
FACTORY_CS = "Iraq_AlFahdMissileFactoryCommandSet"
BUILDING_CS = "Iraq_AlFahdMissileFactoryBuildingCommandSet"
FACTORY_BTN = "Command_ConstructIraq_AlFahdMissileFactory"
BUILDING_BTN = "Command_ConstructIraq_AlFahdMissileFactoryBuilding"

TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")
END_MARKERS = (b"End\r\n", b"End\n", b"End", b"END\r\n", b"END\n", b"END")

NEW_ASSIGN = {
    "Command_ConstructRussiaKashtan": "Button_kashtan",
    "Command_ConstructChinaGattlingCannon": "Button_kashtan",
    "Command_ConstructIranFalaqTrench": "Button_falaq",
}

BEFORE = {
    "Command_ConstructRussiaKashtan": "Button_C-RAM",
    "Command_ConstructChinaGattlingCannon": "Button_C-RAM",
    "Command_ConstructIranFalaqTrench": "Button_DefenceSite",
}

NEW_PNG = {
    "Button_kashtan": TEX / "Button_kashtan.png",
    "Button_falaq": TEX / "Button_falaq.png",
}

KEEP = {
    "Command_ConstructAmericaLgm30": "Button_Atom",
    "Command_ConstructIraq_Abbas": "Button_Bio",
    BUILDING_BTN: "Button_MissileFactory",
    FACTORY_BTN: "Button_MissileFactory",
}

TRACE = [
    ("Russia", "RussiaDozerCommandSet", 5, "Command_ConstructRussiaKashtan", "RussiaKashtan"),
    ("China", "PLADozerCommandSet", 9, "Command_ConstructChinaGattlingCannon", "ChinaGattlingCannon"),
    ("Iran", "IranDozerCommandSet", 12, "Command_ConstructIranFalaqTrench", "IranFalaqTrench"),
]

VANILLA_UNTOUCHED = (
    "Tank_Command_ConstructChinaGattlingCannon",
    "Nuke_Command_ConstructChinaGattlingCannon",
    "Infa_Command_ConstructChinaGattlingCannon",
    "Boss_Command_ConstructChinaGattlingCannon",
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


def parse_big_ordered(data: bytes):
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files = {}
    order = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        key = name.replace("/", "\\")
        files[key] = data[off : off + size]
        order.append(key)
    return files, order


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


def last_button(blob: bytes, name: str) -> str:
    last = ""
    for n, block in iter_blocks(blob, b"CommandButton "):
        if n == name:
            last = block.decode("latin1")
    return last


def last_commandset(blob: bytes, name: str) -> str:
    last = ""
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
        "; SPECTER dedicated Kashtan / Falaq construct cameos.",
        "; Source: patch/Art/Textures/Button_kashtan.png and Button_falaq.png (origin/main 306191dc).",
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


def last_wins_source(files: dict[str, bytes], order: list[str], name: str) -> str:
    src = ""
    for key in order:
        if not key.lower().endswith(".ini"):
            continue
        blob = files[key]
        if b"CommandButton " not in blob:
            continue
        for n, _ in iter_blocks(blob, b"CommandButton "):
            if n == name:
                src = key
    return src


def last_mapped(files: dict[str, bytes], order: list[str], name: str) -> str:
    src = ""
    needle = f"MappedImage {name}".encode("latin1")
    for key in order:
        if not key.lower().endswith(".ini"):
            continue
        if needle in files[key]:
            src = key
    return src


def update_loose() -> None:
    if LOOSE_CB.is_file():
        raw = LOOSE_CB.read_bytes()
        loose_map = {
            name: img
            for name, img in NEW_ASSIGN.items()
            if f"CommandButton {name}".encode("ascii") in raw
        }
        if loose_map:
            LOOSE_CB.write_bytes(splice_button_images(raw, loose_map))
    LOOSE_MAPPED.parent.mkdir(parents=True, exist_ok=True)
    LOOSE_MAPPED.write_text(mapped_ini(list(NEW_PNG)), encoding="latin1")


def validate(data, art, src_data, src_art, order, tgas) -> list[str]:
    fails: list[str] = []
    added_data = set(data) - set(src_data)
    if added_data != {MAPPED_KEY}:
        fails.append(f"DATA added unexpected {added_data ^ {MAPPED_KEY}}")
    if set(src_data) - set(data):
        fails.append("DATA removed files")
    mutated = sorted(k for k in src_data if src_data[k] != data.get(k))
    if mutated != [CB_KEY]:
        fails.append(f"unexpected DATA mutations: {mutated}")
    if data[CS_KEY] != src_data[CS_KEY]:
        fails.append("CommandSet.ini mutated")
    if data[PK_KEY] != src_data[PK_KEY]:
        fails.append("CommandSet_Pakistan.ini mutated")
    if data[FACTORY_KEY] != src_data[FACTORY_KEY]:
        fails.append("Iraq factory object mutated")
    if data[BUILDING_KEY] != src_data[BUILDING_KEY]:
        fails.append("building-only factory object mutated")

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
        if last_mapped(data, order, name) != MAPPED_KEY:
            fails.append(f"{name} MappedImage last-wins from {last_mapped(data, order, name)}")
        key = rf"Art\Textures\{name}.tga"
        info = tga_info(art[key])
        if info["type"] != 2 or info["bpp"] != 24 or info["width"] != 128 or info["height"] != 128:
            fails.append(f"bad TGA {name}: {info}")
        if art[key] != tgas[name]:
            fails.append(f"ART TGA mismatch {name}")

    src_btns = {n: b for n, b in iter_blocks(src_data[CB_KEY], b"CommandButton ")}
    new_btns = {n: b for n, b in iter_blocks(data[CB_KEY], b"CommandButton ")}
    if set(src_btns) != set(new_btns):
        fails.append("CommandButton name set changed")

    def strip_img(s: str) -> str:
        return re.sub(r"(ButtonImage\s*=\s*)\S+", r"\1X", s)

    for name, src_block in src_btns.items():
        new_block = new_btns[name]
        src_text = src_block.decode("latin1")
        new_text = new_block.decode("latin1")
        if name in NEW_ASSIGN:
            want = NEW_ASSIGN[name]
            if field(src_text, "ButtonImage") != BEFORE[name]:
                fails.append(f"{name} baseline image {field(src_text, 'ButtonImage')} != {BEFORE[name]}")
            if field(new_text, "ButtonImage") != want:
                fails.append(f"{name} ButtonImage={field(new_text, 'ButtonImage')} want {want}")
            if field(new_text, "Command") != field(src_text, "Command"):
                fails.append(f"{name} Command changed")
            if field(src_text, "Object") != field(new_text, "Object"):
                fails.append(f"{name} Object changed")
            if strip_img(src_text) != strip_img(new_text):
                fails.append(f"{name} changed beyond ButtonImage")
        else:
            if src_block != new_block:
                fails.append(f"non-target button mutated: {name}")

    for vanilla in VANILLA_UNTOUCHED:
        if last_button(data[CB_KEY], vanilla) != last_button(src_data[CB_KEY], vanilla):
            fails.append(f"vanilla button mutated: {vanilla}")

    for country, cs_name, slot, btn, obj in TRACE:
        cs = last_commandset(data[CS_KEY], cs_name)
        if slot_map(cs).get(slot) != btn:
            fails.append(f"{country} {cs_name} slot {slot} is {slot_map(cs).get(slot)}")
        block = last_button(data[CB_KEY], btn)
        if field(block, "Object") != obj:
            fails.append(f"{btn} object {field(block, 'Object')} != {obj}")
        if field(block, "Command") != "DOZER_CONSTRUCT":
            fails.append(f"{btn} is not DOZER_CONSTRUCT")
        src = last_wins_source(data, order, btn)
        if src != CB_KEY:
            fails.append(f"{btn} last-wins from {src}")

    for name, img in KEEP.items():
        if field(last_button(data[CB_KEY], name), "ButtonImage") != img:
            fails.append(f"kept mapping lost: {name}")

    rus = last_commandset(data[CS_KEY], "RussiaDozerCommandSet")
    pla = last_commandset(data[CS_KEY], "PLADozerCommandSet")
    if slot_map(rus).get(14) != BUILDING_BTN:
        fails.append(f"Russia factory slot lost: {slot_map(rus).get(14)}")
    if slot_map(pla).get(14) != BUILDING_BTN:
        fails.append(f"China PLA factory slot lost: {slot_map(pla).get(14)}")
    bld_cs = last_commandset(data[CS_KEY], BUILDING_CS)
    if "CB_MISSILE_" in bld_cs:
        fails.append("building-only factory gained Iraq roster")
    if slot_map(bld_cs) != {14: "Command_Sell"}:
        fails.append(f"building CommandSet drifted: {slot_map(bld_cs)}")
    iraq_cs = last_commandset(data[CS_KEY], FACTORY_CS)
    if iraq_cs != last_commandset(src_data[CS_KEY], FACTORY_CS):
        fails.append("Iraq factory roster CommandSet mutated")
    if "CB_MISSILE_A" not in iraq_cs:
        fails.append("Iraq roster missing")
    if slot_map(last_commandset(data[CS_KEY], "Iraq_VT72BCommandSet")).get(14) != FACTORY_BTN:
        fails.append("Iraq VT72B factory button lost")

    for name in (
        "IranDozerCommandSet",
        "AmericaDozerCommandSet",
        "AirF_AmericaDozerCommandSet",
        "RussiaDozerCommandSet",
        "PLADozerCommandSet",
    ):
        if last_commandset(data[CS_KEY], name) != last_commandset(src_data[CS_KEY], name):
            fails.append(f"CommandSet mutated: {name}")
    return fails


def report_lines(data: dict[str, bytes], art: dict[str, bytes]) -> list[str]:
    lines = [
        "# Source artwork",
        "  Kashtan: patch/Art/Textures/Button_kashtan.png  (origin/main 306191dc, 1254x1254 RGB)",
        "  Falaq:   patch/Art/Textures/Button_falaq.png    (origin/main 306191dc, 1254x1254 RGB)",
        "  Packed:  Art\\Textures\\Button_kashtan.tga and Art\\Textures\\Button_falaq.tga (128x128 24-bit)",
        "",
        "# Before / after",
    ]
    for country, cs_name, slot, btn, obj in TRACE:
        block = last_button(data[CB_KEY], btn)
        img = field(block, "ButtonImage")
        tex = rf"Art\Textures\{img}.tga"
        lines.append(
            f"  {country} | {cs_name} slot {slot} | {btn} | {obj} | "
            f"{BEFORE[btn]} -> {img} | {tex} exists={tex in art}"
        )
    return lines


def main() -> None:
    missing = [str(p) for p in NEW_PNG.values() if not p.is_file()]
    if missing:
        raise SystemExit("missing PNG " + ", ".join(missing))
    if sha256_path(SRC_DATA) != SHA_DATA_623 or SRC_DATA.stat().st_size != SIZE_DATA_623:
        raise SystemExit("DATA baseline mismatch")
    if sha256_path(SRC_ART) != SHA_ART_623 or SRC_ART.stat().st_size != SIZE_ART_623:
        raise SystemExit("ART baseline mismatch")

    update_loose()
    src_bytes = SRC_DATA.read_bytes()
    src_data, _ = parse_big_ordered(src_bytes)
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    tgas = {name: make_tga24(Image.open(path)) for name, path in NEW_PNG.items()}
    mapped_text = mapped_ini(list(NEW_PNG))
    data[CB_KEY] = splice_button_images(src_data[CB_KEY], NEW_ASSIGN)
    data[MAPPED_KEY] = mapped_text.encode("latin1")
    for name, blob in tgas.items():
        art[rf"Art\Textures\{name}.tga"] = blob

    data_big = build_big(data)
    art_big = build_big(art)
    packed_data, order = parse_big_ordered(data_big)
    packed_art = parse_big(art_big)
    fails = validate(packed_data, packed_art, src_data, src_art, order, tgas)
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
    inv = report_lines(packed_data, packed_art)
    (ext / "BEFORE_AFTER.txt").write_text("\n".join(inv) + "\n")
    (ext / "KashtanFalaqCameos_Images.INI").write_text(mapped_text)
    chunks = []
    for _, cs_name, _, btn, _ in TRACE:
        chunks.append(last_commandset(packed_data[CS_KEY], cs_name))
        chunks.append(last_button(packed_data[CB_KEY], btn))
    (ext / "KashtanFalaq.ini").write_text("\n\n".join(chunks) + "\n")

    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_KASHTAN_FALAQ_RESTORE.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #623 s-kashtan-falaq-btns",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "ART_ADDED=Button_kashtan.tga,Button_falaq.tga",
        "EXISTING_ART_UNCHANGED=YES",
        "COMMANDSET_UNCHANGED=YES",
        "IRAQ_FACTORY_ROSTER_UNCHANGED=YES",
        "RUSSIA_CHINA_FACTORY_BUILDING_ONLY=YES",
        "",
        "SOURCE:",
        "  origin/main 306191dc patch/Art/Textures/Button_kashtan.png",
        "  origin/main 306191dc patch/Art/Textures/Button_falaq.png",
        "  Converted with established tight-crop + LANCZOS 128x128 24-bit TGA pipeline.",
        "  Images were not redrawn or approximated.",
        "",
        *inv,
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n")
    hashes = "\n".join(
        [
            "DATA_CHANGED=YES",
            "ART_CHANGED=YES_ADDED_ONLY",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_SIZE={art_path.stat().st_size}",
            f"ART_SHA256={art_sha}",
            "ZIP_FILE=SPECTER_KASHTAN_FALAQ_RESTORE.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #623",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-kashtan-falaq-restore/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-kashtan-falaq-restore/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-kashtan-falaq-restore/SPECTER_KASHTAN_FALAQ_RESTORE.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-kashtan-falaq-restore",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-kashtan-falaq-restore",
                "BASELINE=PR #623",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Restore dedicated Kashtan and Falaq construction-button artwork from\n"
        "patch/Art/Textures/Button_kashtan.png and Button_falaq.png.\n"
        "CommandSets unchanged. Existing ART textures unchanged.\n"
        "Static validation only.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Restore dedicated Kashtan and Falaq construction buttons\n\n"
        "- Source: origin/main 306191dc `Button_kashtan.png` and `Button_falaq.png`.\n"
        "- Russia Kashtan and China LD2000/Kashtan use Button_kashtan.\n"
        "- Iran Falaq trench uses Button_falaq.\n"
        "- Packed as 128x128 24-bit TGA via the established construct-cameo pipeline.\n"
        "- CommandSets and factory isolation unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "New MappedImages Button_kashtan / Button_falaq. Existing Button_* and rus_kashtan / irn_falaq portraits untouched.\n"
        "Vanilla Tank_/Nuke_/Infa_/Boss_ China gattling buttons untouched.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n")
    print("PACKED")
    print(hashes)
    print("\n".join(report))


if __name__ == "__main__":
    main()
