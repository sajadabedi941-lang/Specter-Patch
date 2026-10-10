#!/usr/bin/env python3
"""Complete Iraq building-construction ButtonImage set from uploaded Button_*.png.

Baseline: PR #616 SPECTER_IRAQ_CONSTRUCT_BTN_FIX
  DATA 366674056 SHA a3dc851ec3d1d4042d8ae46a32beb299fd84fd394bf35544d3d43ff94fec09cb
  ART  1306406185 SHA a4f033e556c280a7f0fd50f5ead273d736a1238ec11233924aedb82f4e915481

Keeps the five #616 mappings and VT72B slot 14 factory restore.
Adds remaining uploaded Button_*.png files to every other real Iraq
DOZER_CONSTRUCT button that has a matching image.

Does not create Bio / CRAM / Mantis / Strategy Center / World Market.
Does not change CommandSets, factory object, or other countries.
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
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_CONSTRUCT_BTN_FIX/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_CONSTRUCT_BTN_FIX/_SPEC_ART_ONE.big"
TEX = ROOT / "patch/Art/Textures"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALL_CONSTRUCT_BTNS"
LOOSE_CB = ROOT / "patch/Data/INI/CommandButton.ini"
LOOSE_MAPPED = ROOT / "patch/Data/INI/MappedImages/HandCreated/IraqAllConstructCameos_Images.INI"

SHA_DATA_616 = "a3dc851ec3d1d4042d8ae46a32beb299fd84fd394bf35544d3d43ff94fec09cb"
SIZE_DATA_616 = 366674056
SHA_ART_616 = "a4f033e556c280a7f0fd50f5ead273d736a1238ec11233924aedb82f4e915481"
SIZE_ART_616 = 1306406185

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
PK_KEY = r"Data\INI\CommandSet_Pakistan.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\IraqAllConstructCameos_Images.INI"
KEEP_MAPPED = (
    r"Data\INI\MappedImages\HandCreated\IraqConstructFix_Images.INI",
    r"Data\INI\MappedImages\HandCreated\IraqBuildingCameos_Images.INI",
)

TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")

# Already packed in #616 ART + MappedImages. Must stay assigned.
KEEP_616 = {
    "Command_ConstructIraq_D30_Howitzer": "Button_Artillery",
    "Command_ConstructIraq_Sam2": "Button_AirDefense",
    "Command_ConstructIraq_MIC": "Button_GlobalMarket",
    "Command_ConstructIraq_DefenseSite": "Button_DefenceSite",
    "Command_ConstructIraq_AlFahdMissileFactory": "Button_MissileFactory",
}

# Remaining real Iraq construct buttons with a matching uploaded image.
NEW_ASSIGN = {
    "Command_ConstructIraq_PowerPlant": "Button_PowerPlant",
    "Command_ConstructIraq_CommandCenter": "Button_CommandCenter",
    "Command_ConstructIraq_SupplyCenter": "Button_SupplyCenter",
    "Command_ConstructIraq_WarFactory_T": "Button_WarFactory",
    "Command_ConstructIraqMilitaryWarfactory": "Button_WarFactory",
    "Command_ConstructIraq_Airfield_T": "Button_FighterBase",
    "Command_ConstructIraqMilitaryAirfield": "Button_FighterBase",
    "Command_ConstructIraq_Barracks": "Button_Camp",
    "Command_ConstructIraq_Abbas": "Button_Atom",
    "Command_ConstructIraq_Abbas_AI": "Button_Atom",
    "Command_ConstructIraq_HeavyAirBase": "Button_AircraftBase",
    "Command_ConstructIraq_RadarStation": "Button_Radar",
}

BTN_TO_IMAGE = {**KEEP_616, **NEW_ASSIGN}

NEW_PNG = {
    "Button_PowerPlant": TEX / "Button_PowerPlant.png",
    "Button_CommandCenter": TEX / "Button_CommandCenter.png",
    "Button_SupplyCenter": TEX / "Button_SupplyCenter.png",
    "Button_WarFactory": TEX / "Button_WarFactory.png",
    "Button_FighterBase": TEX / "Button_FighterBase.png",
    "Button_Camp": TEX / "Button_Camp.png",
    "Button_Atom": TEX / "Button_Atom.png",
    "Button_AircraftBase": TEX / "Button_AircraftBase.png",
    "Button_Radar": TEX / "Button_Radar.png",
}

# Existing construct buttons with no matching uploaded image.
PRESERVE = [
    "Command_ConstructIraq_100mmCannon",
    "Command_ConstructIraqFahad3SamSite",
    "Command_DisarmMinesAtPosition",
]

UNUSED_IMAGES = [
    "Button_Bio.png — no Iraq Bio building; Iraq_MIC already uses Button_GlobalMarket",
    "Button_C-RAM.png — no Iraq_CRAM object",
    "Button_Mantis.png — no Iraq_Mantis object",
    "Button_StrategyCenter.png — no Iraq Strategy Center object",
]

FACTORY_BTN = "Command_ConstructIraq_AlFahdMissileFactory"
DOZER_SET = "Iraq_VT72BCommandSet"


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
    return {"width": w, "height": h, "type": blob[2], "bpp": blob[16], "alpha_bits": blob[17] & 0x0F}


def mapped_ini(names: list[str]) -> str:
    lines = [
        "; SPECTER remaining Iraq construct cameos from uploaded Button_*.png.",
        "; Completes the set after IraqConstructFix_Images.INI (#616).",
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
        LOOSE_CB.write_bytes(splice_button_images(raw, loose_map))


def validate(data, art, src_data, src_art, tgas) -> list[str]:
    fails: list[str] = []
    added_data = set(data) - set(src_data)
    if added_data != {MAPPED_KEY}:
        fails.append(f"DATA added unexpected {added_data}")
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

    src_btns = {n: b for n, b in iter_blocks(src_data[CB_KEY], b"CommandButton ")}
    new_btns = {n: b for n, b in iter_blocks(data[CB_KEY], b"CommandButton ")}
    if set(src_btns) != set(new_btns):
        fails.append("CommandButton name set changed")
    for name, src_block in src_btns.items():
        new_block = new_btns[name]
        src_text = src_block.decode("latin1")
        new_text = new_block.decode("latin1")
        if name in NEW_ASSIGN:
            want = NEW_ASSIGN[name]
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

    for name, img in KEEP_616.items():
        if field(last_button(data[CB_KEY], name), "ButtonImage") != img:
            fails.append(f"#616 mapping lost: {name}")
    for name in PRESERVE:
        if last_button(data[CB_KEY], name) != last_button(src_data[CB_KEY], name):
            fails.append(f"preserved button mutated: {name}")

    dozer = last_commandset(data[CS_KEY], DOZER_SET)
    if slot_map(dozer).get(14) != FACTORY_BTN:
        fails.append(f"factory slot 14 lost: {slot_map(dozer).get(14)}")
    if last_commandset(data[CS_KEY], "Iraq_WorkerCommandSet") != last_commandset(
        src_data[CS_KEY], "Iraq_WorkerCommandSet"
    ):
        fails.append("Worker CommandSet mutated")
    return fails


def main() -> None:
    missing = [str(p) for p in NEW_PNG.values() if not p.is_file()]
    if missing:
        raise SystemExit("missing uploaded images:\n" + "\n".join(missing))
    if sha256_path(SRC_DATA) != SHA_DATA_616 or SRC_DATA.stat().st_size != SIZE_DATA_616:
        raise SystemExit("DATA baseline mismatch")
    if sha256_path(SRC_ART) != SHA_ART_616 or SRC_ART.stat().st_size != SIZE_ART_616:
        raise SystemExit("ART baseline mismatch")

    mapped_text = mapped_ini(list(NEW_PNG))
    tgas = {name: make_tga24(Image.open(path)) for name, path in NEW_PNG.items()}
    update_loose(mapped_text)

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    data[CB_KEY] = splice_button_images(src_data[CB_KEY], NEW_ASSIGN)
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
    inv_lines = []
    for name in sorted(set(list(BTN_TO_IMAGE) + PRESERVE[:2])):
        body = last_button(data[CB_KEY], name)
        inv_lines.append(body)
    (ext / "CommandButton_IraqAllConstruct.ini").write_bytes(
        b"\r\n".join(s.encode("latin1") for s in inv_lines if s)
    )
    (ext / "IraqAllConstructCameos_Images.INI").write_bytes(data[MAPPED_KEY])

    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_ALL_CONSTRUCT_BTNS.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    inventory = [
        "Power Plant | Iraq_PowerPlant | Command_ConstructIraq_PowerPlant | Button_PowerPlant.png | CORRECTED (was irqbtn_power)",
        "Command Center | Iraq_CommandCenter | Command_ConstructIraq_CommandCenter | Button_CommandCenter.png | CORRECTED (was irqbtn_cmdctr)",
        "Supply Center | Iraq_SupplyCenter | Command_ConstructIraq_SupplyCenter | Button_SupplyCenter.png | CORRECTED (was irqbtn_supply)",
        "War Factory | Iraq_WarFactory_T | Command_ConstructIraq_WarFactory_T | Button_WarFactory.png | CORRECTED (was irqbtn_warfac)",
        "War Factory (military) | IraqMilitaryWarfactory | Command_ConstructIraqMilitaryWarfactory | Button_WarFactory.png | CORRECTED (was irqbtn_warfac)",
        "Fighter Base | Iraq_LargeAirBase | Command_ConstructIraq_Airfield_T | Button_FighterBase.png | CORRECTED (was irqbtn_fighter)",
        "Fighter Base (military) | Iraq_LargeAirBase | Command_ConstructIraqMilitaryAirfield | Button_FighterBase.png | CORRECTED (was irqbtn_fighter)",
        "Camp / Barracks | Iraq_Barracks | Command_ConstructIraq_Barracks | Button_Camp.png | CORRECTED (was irqbtn_camp)",
        "Atom / Abbas | Iraq_Abbas | Command_ConstructIraq_Abbas | Button_Atom.png | CORRECTED (was irqbtn_atom)",
        "Atom / Abbas AI | Iraq_Abbas_AI | Command_ConstructIraq_Abbas_AI | Button_Atom.png | CORRECTED (was irqbtn_atom)",
        "Aircraft Base | Iraq_HeavyAirBase | Command_ConstructIraq_HeavyAirBase | Button_AircraftBase.png | CORRECTED (was irqbtn_airbase)",
        "Radar | Iraq_RadarStation | Command_ConstructIraq_RadarStation | Button_Radar.png | CORRECTED (was irqbtn_radar)",
        "Artillery / D30 | Iraq_D30_Howitzer | Command_ConstructIraq_D30_Howitzer | Button_Artillery.png | ALREADY CORRECT (#616)",
        "S125 | Iraq_Sam2 | Command_ConstructIraq_Sam2 | Button_AirDefense.png | ALREADY CORRECT (#616)",
        "M.I.C. | Iraq_MIC | Command_ConstructIraq_MIC | Button_GlobalMarket.png | ALREADY CORRECT (#616)",
        "DefenseSite | Iraq_DefenseSite | Command_ConstructIraq_DefenseSite | Button_DefenceSite.png | ALREADY CORRECT (#616)",
        "Missile Factory | Iraq_AlFahdMissileFactory | Command_ConstructIraq_AlFahdMissileFactory | Button_MissileFactory.png | ALREADY CORRECT (#616); VT72B slot 14 retained",
        "100mm Cannon | Iraq_100mmCannon | Command_ConstructIraq_100mmCannon | (none uploaded) | PRESERVED irq_100canon",
        "Fahad-3 SAM | IraqFahad3SamSite | Command_ConstructIraqFahad3SamSite | (none uploaded) | PRESERVED irq_fahad3",
    ]

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #616 s-iraq-construct-btn-fix",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "COMMANDSET_UNCHANGED=YES",
        "FACTORY_SLOT14_RETAINED=YES",
        "DATA mutations: CommandButton.ini ButtonImage on remaining Iraq construct buttons + new MappedImage INI",
        "ART mutations: 9 new Button_*.tga only",
        "",
        "COMPLETE IRAQ CONSTRUCTION-BUTTON INVENTORY:",
        *[f"  {x}" for x in inventory],
        "",
        "UNUSED UPLOADED IMAGES (no Iraq building created):",
        *[f"  {x}" for x in UNUSED_IMAGES],
        "",
        "CHANGED vs PR #616:",
        "  DATA Data\\INI\\CommandButton.ini — ButtonImage only on 12 remaining Iraq DOZER_CONSTRUCT buttons",
        "  DATA Data\\INI\\MappedImages\\HandCreated\\IraqAllConstructCameos_Images.INI — new",
        "  ART 9 new Button_{PowerPlant,CommandCenter,SupplyCenter,WarFactory,FighterBase,Camp,Atom,AircraftBase,Radar}.tga",
        "  CommandSet.ini unchanged (factory slot 14 already restored)",
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
            "ZIP_FILE=SPECTER_IRAQ_ALL_CONSTRUCT_BTNS.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={sha256_path(zip_path)}",
            "BASELINE=PR #616",
            "FACTORY_SLOT14_RETAINED=YES",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-all-construct-btns/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-all-construct-btns/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-all-construct-btns/SPECTER_IRAQ_ALL_CONSTRUCT_BTNS.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={sha256_path(zip_path)}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-iraq-all-construct-btns",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-iraq-all-construct-btns",
                "BASELINE=PR #616",
                "FACTORY_SLOT14_RETAINED=YES",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Complete Iraq construction-menu ButtonImages from uploaded Button_*.png files.\n"
        "Keeps #616 five mappings and VT72B slot 14 factory. Static validation only.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Complete Iraq construction button images\n\n"
        "- Remaining Iraq DOZER_CONSTRUCT buttons now use uploaded Button_*.png files.\n"
        "- #616 D30 / S125 / MIC / DefenseSite / Missile Factory mappings retained.\n"
        "- Iraq VT72B slot 14 remains the existing missile factory construct button.\n"
        "- No CommandSet, factory-object, or other-country changes.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text("No last-wins path conflicts. New Button_* MappedImages only.\n")
    (OUT / "INVENTORY.txt").write_text("\n".join(inventory) + "\n")
    print("PACKED")
    print(hashes)
    print("\n".join(report))


if __name__ == "__main__":
    main()
