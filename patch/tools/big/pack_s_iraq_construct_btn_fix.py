#!/usr/bin/env python3
"""Iraq-only: five construct ButtonImages + restore missile factory on VT72B slot 14.

Baseline: PR #615 SPECTER_IRAQ_BUILDING_BUTTONS
  DATA 366672869 SHA 708ef7a599dfcb1c073cf19e3201fbc0d3fbf3bd1c2c0398c0bae9dd2b853809
  ART  1306159984 SHA fee4ac85eb53d47e1a972b90b04b42996f14031bfcb9e0b9736916e12915c895

Source images (actual repo filenames on origin/main, not contact sheets):
  patch/Art/Textures/Button_Artillery.png
  patch/Art/Textures/Button_AirDefense.png
  patch/Art/Textures/Button_GlobalMarket.png
  patch/Art/Textures/Button_DefenceSite.png
  patch/Art/Textures/Button_MissileFactory.png

No Button_missilefactory.png exists; the uploaded file is Button_MissileFactory.png.
Static validation only. The game is not launched.
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
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_BUILDING_BUTTONS/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_BUILDING_BUTTONS/_SPEC_ART_ONE.big"
TEX = ROOT / "patch/Art/Textures"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_CONSTRUCT_BTN_FIX"
LOOSE_CB = ROOT / "patch/Data/INI/CommandButton.ini"
LOOSE_CS = ROOT / "patch/Data/INI/CommandSet.ini"
LOOSE_MAPPED = ROOT / "patch/Data/INI/MappedImages/HandCreated/IraqConstructFix_Images.INI"

SHA_DATA_615 = "708ef7a599dfcb1c073cf19e3201fbc0d3fbf3bd1c2c0398c0bae9dd2b853809"
SIZE_DATA_615 = 366672869
SHA_ART_615 = "fee4ac85eb53d47e1a972b90b04b42996f14031bfcb9e0b9736916e12915c895"
SIZE_ART_615 = 1306159984

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
PK_KEY = r"Data\INI\CommandSet_Pakistan.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\IraqConstructFix_Images.INI"
OLD_MAPPED = r"Data\INI\MappedImages\HandCreated\IraqBuildingCameos_Images.INI"

TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")

# Actual uploaded filenames. MappedImage / TGA use the same basename.
PNG_FILES = {
    "Button_Artillery": TEX / "Button_Artillery.png",
    "Button_AirDefense": TEX / "Button_AirDefense.png",
    "Button_GlobalMarket": TEX / "Button_GlobalMarket.png",
    "Button_DefenceSite": TEX / "Button_DefenceSite.png",
    "Button_MissileFactory": TEX / "Button_MissileFactory.png",
}

BTN_TO_IMAGE = {
    "Command_ConstructIraq_D30_Howitzer": "Button_Artillery",
    "Command_ConstructIraq_Sam2": "Button_AirDefense",
    "Command_ConstructIraq_MIC": "Button_GlobalMarket",
    "Command_ConstructIraq_DefenseSite": "Button_DefenceSite",
    "Command_ConstructIraq_AlFahdMissileFactory": "Button_MissileFactory",
}

FACTORY_BTN = "Command_ConstructIraq_AlFahdMissileFactory"
DOZER_SET = "Iraq_VT72BCommandSet"
FACTORY_SLOT = 14
OLD_SLOT_CMD = "Command_DisarmMinesAtPosition"

# Must remain byte-identical.
KEEP_BUTTONS = [
    "Command_ConstructIraq_CommandCenter",
    "Command_ConstructIraq_Barracks",
    "Command_ConstructIraq_PowerPlant",
    "Command_ConstructIraq_SupplyCenter",
    "Command_ConstructIraq_WarFactory_T",
    "Command_ConstructIraqMilitaryWarfactory",
    "Command_ConstructIraq_RadarStation",
    "Command_ConstructIraq_Abbas",
    "Command_ConstructIraq_Abbas_AI",
    "Command_ConstructIraq_HeavyAirBase",
    "Command_ConstructIraq_Airfield_T",
    "Command_ConstructIraqMilitaryAirfield",
    "Command_ConstructIraq_100mmCannon",
    "Command_ConstructIraqFahad3SamSite",
    "Command_DisarmMinesAtPosition",
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
    return {
        "width": w,
        "height": h,
        "type": blob[2],
        "bpp": blob[16],
        "alpha_bits": blob[17] & 0x0F,
    }


def mapped_ini(names: list[str]) -> str:
    lines = [
        "; SPECTER Iraq construct-button cameos from uploaded Button_*.png files.",
        "; Construction CommandButton ButtonImage only. Not SelectPortrait.",
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


def replace_dozer_slot(blob: bytes) -> bytes:
    text = blob.decode("latin1")
    matches = list(re.finditer(rf"(?ms)^CommandSet {re.escape(DOZER_SET)}\r?\n.*?^End", text))
    if not matches:
        raise SystemExit(f"{DOZER_SET} not found")
    block = matches[-1].group(0)
    new_block, n = re.subn(
        rf"(?m)^(\s*{FACTORY_SLOT}\s*=\s*){re.escape(OLD_SLOT_CMD)}\s*$",
        rf"\1{FACTORY_BTN}",
        block,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"{DOZER_SET} slot {FACTORY_SLOT} is not {OLD_SLOT_CMD}")
    if slot_map(new_block).get(FACTORY_SLOT) != FACTORY_BTN:
        raise SystemExit("slot replace failed")
    # Only that one command token may change.
    def norm(s: str) -> str:
        return re.sub(
            rf"(?m)^(\s*{FACTORY_SLOT}\s*=\s*)\S+",
            r"\1X",
            s,
        )
    if norm(block) != norm(new_block):
        raise SystemExit("CommandSet changed beyond slot 14")
    return text.replace(block, new_block, 1).encode("latin1")


def update_loose_sources(mapped_text: str) -> None:
    LOOSE_MAPPED.parent.mkdir(parents=True, exist_ok=True)
    LOOSE_MAPPED.write_text(mapped_text.replace("\r\n", "\n") + "\n", encoding="latin1")
    if LOOSE_CB.is_file():
        raw = LOOSE_CB.read_bytes()
        loose_map = {
            name: img
            for name, img in BTN_TO_IMAGE.items()
            if f"CommandButton {name}".encode("ascii") in raw
        }
        LOOSE_CB.write_bytes(splice_button_images(raw, loose_map))
    if LOOSE_CS.is_file():
        LOOSE_CS.write_bytes(replace_dozer_slot(LOOSE_CS.read_bytes()))


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
    if mutated_data != [CB_KEY, CS_KEY]:
        fails.append(f"unexpected DATA mutations: {mutated_data}")
    if data[PK_KEY] != src_data[PK_KEY]:
        fails.append("CommandSet_Pakistan.ini mutated")
    if data[FACTORY_KEY] != src_data[FACTORY_KEY]:
        fails.append("missile factory object mutated")
    if data.get(OLD_MAPPED) != src_data.get(OLD_MAPPED):
        fails.append("prior IraqBuildingCameos MappedImages mutated")

    added_art = set(art) - set(src_art)
    expected_art = {rf"Art\Textures\{name}.tga" for name in PNG_FILES}
    if added_art != expected_art:
        fails.append(f"ART added unexpected {added_art ^ expected_art}")
    if set(src_art) - set(art):
        fails.append("ART removed files")
    mutated_art = [k for k in src_art if src_art[k] != art.get(k)]
    if mutated_art:
        fails.append(f"existing ART mutated: {mutated_art[:8]}")

    mapped = data[MAPPED_KEY].decode("latin1")
    for name in PNG_FILES:
        if f"MappedImage {name}" not in mapped:
            fails.append(f"missing MappedImage {name}")
        key = rf"Art\Textures\{name}.tga"
        if key not in art:
            fails.append(f"missing ART {key}")
        else:
            info = tga_info(art[key])
            if info["type"] != 2 or info["bpp"] != 24 or info["alpha_bits"] != 0:
                fails.append(f"bad TGA {name}: {info}")
            if info["width"] != 128 or info["height"] != 128:
                fails.append(f"TGA size {name}")
            if art[key] != tgas[name]:
                fails.append(f"ART TGA mismatch {name}")

    src_cb = src_data[CB_KEY]
    new_cb = data[CB_KEY]
    src_btns = {n: b for n, b in iter_blocks(src_cb, b"CommandButton ")}
    new_btns = {n: b for n, b in iter_blocks(new_cb, b"CommandButton ")}
    if set(src_btns) != set(new_btns):
        fails.append("CommandButton name set changed")
    for name, src_block in src_btns.items():
        new_block = new_btns[name]
        src_text = src_block.decode("latin1")
        new_text = new_block.decode("latin1")
        if name in BTN_TO_IMAGE:
            want = BTN_TO_IMAGE[name]
            if field(new_text, "ButtonImage") != want:
                fails.append(f"{name} ButtonImage={field(new_text, 'ButtonImage')} want {want}")
            if field(new_text, "Command") != "DOZER_CONSTRUCT":
                fails.append(f"{name} Command changed")
            if field(src_text, "Object") != field(new_text, "Object"):
                fails.append(f"{name} Object changed")
            def strip_img(s: str) -> str:
                return re.sub(r"(ButtonImage\s*=\s*)\S+", r"\1X", s)
            if strip_img(src_text) != strip_img(new_text):
                fails.append(f"{name} changed beyond ButtonImage")
        else:
            if src_block != new_block:
                fails.append(f"non-target button mutated: {name}")

    for name in KEEP_BUTTONS:
        if last_button(new_cb, name) != last_button(src_cb, name):
            fails.append(f"kept button mutated: {name}")

    src_cs = src_data[CS_KEY]
    new_cs = data[CS_KEY]
    src_sets = {n: b for n, b in iter_blocks(src_cs, b"CommandSet ")}
    new_sets = {n: b for n, b in iter_blocks(new_cs, b"CommandSet ")}
    if set(src_sets) != set(new_sets):
        fails.append("CommandSet name set changed")
    for name, src_block in src_sets.items():
        if name == DOZER_SET:
            continue
        if src_block != new_sets[name]:
            fails.append(f"non-target CommandSet mutated: {name}")

    dozer = last_commandset(new_cs, DOZER_SET)
    src_dozer = last_commandset(src_cs, DOZER_SET)
    slots = slot_map(dozer)
    src_slots = slot_map(src_dozer)
    if slots.get(FACTORY_SLOT) != FACTORY_BTN:
        fails.append(f"dozer slot {FACTORY_SLOT}={slots.get(FACTORY_SLOT)}")
    if src_slots.get(FACTORY_SLOT) != OLD_SLOT_CMD:
        fails.append("baseline slot 14 was not Clear Mines")
    for slot, cmd in src_slots.items():
        if slot == FACTORY_SLOT:
            continue
        if slots.get(slot) != cmd:
            fails.append(f"dozer slot {slot} changed to {slots.get(slot)}")
    worker = last_commandset(new_cs, "Iraq_WorkerCommandSet")
    if worker != last_commandset(src_cs, "Iraq_WorkerCommandSet"):
        fails.append("Iraq_WorkerCommandSet mutated")
    if field(data[FACTORY_KEY].decode("latin1"), "BuildCost") != "1800":
        fails.append("factory cost changed")
    return fails


def main() -> None:
    missing = [str(p) for p in PNG_FILES.values() if not p.is_file()]
    if missing:
        raise SystemExit("missing uploaded images:\n" + "\n".join(missing))
    if (TEX / "Button_missilefactory.png").exists() and not (TEX / "Button_MissileFactory.png").exists():
        pass
    if sha256_path(SRC_DATA) != SHA_DATA_615 or SRC_DATA.stat().st_size != SIZE_DATA_615:
        raise SystemExit("DATA baseline mismatch")
    if sha256_path(SRC_ART) != SHA_ART_615 or SRC_ART.stat().st_size != SIZE_ART_615:
        raise SystemExit("ART baseline mismatch")

    mapped_text = mapped_ini(list(PNG_FILES))
    tgas = {name: make_tga24(Image.open(path)) for name, path in PNG_FILES.items()}
    update_loose_sources(mapped_text)

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    data[CB_KEY] = splice_button_images(src_data[CB_KEY], BTN_TO_IMAGE)
    data[CS_KEY] = replace_dozer_slot(src_data[CS_KEY])
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
    (ext / "Iraq_VT72BCommandSet.ini").write_text(last_commandset(data[CS_KEY], DOZER_SET))
    (ext / "CommandButton_IraqConstructFix.ini").write_bytes(
        b"\r\n".join(last_button(data[CB_KEY], name).encode("latin1") for name in BTN_TO_IMAGE)
    )
    (ext / "IraqConstructFix_Images.INI").write_bytes(data[MAPPED_KEY])

    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_CONSTRUCT_BTN_FIX.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    changed = [
        "DATA Data\\INI\\CommandButton.ini — ButtonImage only on 5 Iraq DOZER_CONSTRUCT buttons",
        "DATA Data\\INI\\CommandSet.ini — Iraq_VT72BCommandSet slot 14 only",
        "DATA Data\\INI\\MappedImages\\HandCreated\\IraqConstructFix_Images.INI — new",
        "ART Art\\Textures\\Button_Artillery.tga — new",
        "ART Art\\Textures\\Button_AirDefense.tga — new",
        "ART Art\\Textures\\Button_GlobalMarket.tga — new",
        "ART Art\\Textures\\Button_DefenceSite.tga — new",
        "ART Art\\Textures\\Button_MissileFactory.tga — new",
    ]
    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #615 s-iraq-building-buttons",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "MISSILE_FACTORY_RESTORED=YES Iraq_VT72BCommandSet slot 14 = Command_ConstructIraq_AlFahdMissileFactory",
        "WORKER_COMMANDSET_UNCHANGED=YES",
        "IMAGE_NOTE=Button_missilefactory.png does not exist; used actual file Button_MissileFactory.png",
        "",
        "CHANGED FILES:",
        *[f"  {x}" for x in changed],
        "",
        "MAPPINGS:",
        "  D30 Howitzer Command_ConstructIraq_D30_Howitzer -> Button_Artillery",
        "  S125 Command_ConstructIraq_Sam2 -> Button_AirDefense",
        "  MIC Command_ConstructIraq_MIC -> Button_GlobalMarket",
        "  DefenseSite Command_ConstructIraq_DefenseSite -> Button_DefenceSite",
        "  Missile Factory Command_ConstructIraq_AlFahdMissileFactory -> Button_MissileFactory",
        "  Clear Mines image NOT changed; slot 14 now builds the factory",
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
            "ZIP_FILE=SPECTER_IRAQ_CONSTRUCT_BTN_FIX.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #615",
            "MISSILE_FACTORY_RESTORED=YES",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-construct-btn-fix/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-construct-btn-fix/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-construct-btn-fix/SPECTER_IRAQ_CONSTRUCT_BTN_FIX.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-iraq-construct-btn-fix",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-iraq-construct-btn-fix",
                "BASELINE=PR #615",
                "MISSILE_FACTORY_RESTORED=YES",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Iraq construct-button image fix + restore missile factory on VT72B slot 14.\n"
        "Complete replacement DATA + ART. Static validation only.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Iraq construct button image fix\n\n"
        "- Five specified Iraq DOZER_CONSTRUCT ButtonImages from uploaded Button_*.png files.\n"
        "- Restore `Command_ConstructIraq_AlFahdMissileFactory` on Iraq VT72B slot 14 (was Clear Mines).\n"
        "- Factory object, Worker CommandSet, other countries, and other Iraq buttons unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "No last-wins path conflicts. New Button_* MappedImages only.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report))


if __name__ == "__main__":
    main()
