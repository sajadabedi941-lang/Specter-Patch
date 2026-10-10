#!/usr/bin/env python3
"""EU8 + Iraq Abbas construction-button images from uploaded Button_*.png.

Baseline: PR #617 SPECTER_IRAQ_ALL_CONSTRUCT_BTNS
  DATA 366675916 SHA 5db24a2aeed226e2fb19416c390d6907c5d68a566b99d7220d410ff8bf16f044
  ART  1306849327 SHA b61729185bff96f9e54130dd4d475da8fcca2d9fafd185f9be7af1d053168d4c

Countries: Germany, France, Britain, Italy, Turkey, Sweden, Ukraine, NATO.
Iraq Abbas construct buttons switch from Button_Atom to Button_Bio.
CommandSets unchanged. Missile factory slot 14 retained.
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
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ALL_CONSTRUCT_BTNS/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_ALL_CONSTRUCT_BTNS/_SPEC_ART_ONE.big"
TEX = ROOT / "patch/Art/Textures"
OUT = ROOT / "patch/Release/SPECTER_EU8_CONSTRUCT_BTNS"
LOOSE_CB = ROOT / "patch/Data/INI/CommandButton.ini"
LOOSE_MAPPED = ROOT / "patch/Data/INI/MappedImages/HandCreated/EU8ConstructCameos_Images.INI"

SHA_DATA_617 = "5db24a2aeed226e2fb19416c390d6907c5d68a566b99d7220d410ff8bf16f044"
SIZE_DATA_617 = 366675916
SHA_ART_617 = "b61729185bff96f9e54130dd4d475da8fcca2d9fafd185f9be7af1d053168d4c"
SIZE_ART_617 = 1306849327

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
PK_KEY = r"Data\INI\CommandSet_Pakistan.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\EU8ConstructCameos_Images.INI"
KEEP_MAPPED = (
    r"Data\INI\MappedImages\HandCreated\IraqConstructFix_Images.INI",
    r"Data\INI\MappedImages\HandCreated\IraqBuildingCameos_Images.INI",
    r"Data\INI\MappedImages\HandCreated\IraqAllConstructCameos_Images.INI",
)

TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")

COUNTRIES = [
    "Germany",
    "France",
    "Britain",
    "Italy",
    "Turkey",
    "Sweden",
    "Ukraine",
    "Nato",
]

# Country-specific DOZER_CONSTRUCT suffix -> uploaded Button_* MappedImage.
COUNTRY_SUFFIX = {
    "PowerStation": "Button_PowerPlant",
    "CommandCenter": "Button_CommandCenter",
    "SupplyCenter": "Button_SupplyCenter",
    "WarFactory": "Button_WarFactory",
    "Airfield": "Button_FighterBase",
    "_HeavyAirBase": "Button_AircraftBase",
    "BootCamp": "Button_Camp",
    "RadarGM406": "Button_Radar",
    "IRISTSamSite": "Button_AirDefense",
    "M777": "Button_Artillery",
    "Mantis": "Button_Mantis",
    "StrategyCenter": "Button_GlobalMarket",
}

NEW_ASSIGN: dict[str, str] = {}
for country in COUNTRIES:
    for suffix, img in COUNTRY_SUFFIX.items():
        NEW_ASSIGN[f"Command_Construct{country}{suffix}"] = img

# Shared LGM30 construct button used by all eight countries (also America).
NEW_ASSIGN["Command_ConstructAmericaLgm30"] = "Button_Atom"

# Iraq Abbas correction from PR #617 Atom -> Bio.
NEW_ASSIGN["Command_ConstructIraq_Abbas"] = "Button_Bio"
NEW_ASSIGN["Command_ConstructIraq_Abbas_AI"] = "Button_Bio"

KEEP_ALREADY = {
    "Command_ConstructIraq_AlFahdMissileFactory": "Button_MissileFactory",
}

PRESERVE_NO_IMAGE = [
    "NASAMSIII",
    "SkySabre",
    "Skyranger30",
]

NEW_PNG = {
    "Button_Bio": TEX / "Button_Bio.png",
    "Button_Mantis": TEX / "Button_Mantis.png",
}

FACTORY_BTN = "Command_ConstructIraq_AlFahdMissileFactory"
DOZER_SET = "Iraq_VT72BCommandSet"
EU_DOZERS = [f"{c}DozerCommandSet" for c in COUNTRIES]


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
        "; SPECTER EU8 construct cameos: Button_Bio and Button_Mantis.",
        "; Other Button_* MappedImages already last-win from #616/#617.",
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

    def strip_img(s: str) -> str:
        return re.sub(r"(ButtonImage\s*=\s*)\S+", r"\1X", s)

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
            if strip_img(src_text) != strip_img(new_text):
                fails.append(f"{name} changed beyond ButtonImage")
        else:
            if src_block != new_block:
                fails.append(f"non-target button mutated: {name}")

    for name, img in KEEP_ALREADY.items():
        if field(last_button(data[CB_KEY], name), "ButtonImage") != img:
            fails.append(f"kept mapping lost: {name}")

    if field(last_button(data[CB_KEY], "Command_ConstructIraq_Abbas"), "ButtonImage") != "Button_Bio":
        fails.append("Iraq Abbas is not Button_Bio")
    if field(last_button(data[CB_KEY], "Command_ConstructIraq_Abbas_AI"), "ButtonImage") != "Button_Bio":
        fails.append("Iraq Abbas_AI is not Button_Bio")
    if field(last_button(data[CB_KEY], "Command_ConstructAmericaLgm30"), "ButtonImage") != "Button_Atom":
        fails.append("LGM30 is not Button_Atom")

    for country in COUNTRIES:
        for suffix, img in (
            ("IRISTSamSite", "Button_AirDefense"),
            ("M777", "Button_Artillery"),
            ("StrategyCenter", "Button_GlobalMarket"),
        ):
            name = f"Command_Construct{country}{suffix}"
            if field(last_button(data[CB_KEY], name), "ButtonImage") != img:
                fails.append(f"special mapping failed: {name}")

    dozer = last_commandset(data[CS_KEY], DOZER_SET)
    if slot_map(dozer).get(14) != FACTORY_BTN:
        fails.append(f"factory slot 14 lost: {slot_map(dozer).get(14)}")
    for name in EU_DOZERS + [DOZER_SET, "Iraq_WorkerCommandSet"]:
        if last_commandset(data[CS_KEY], name) != last_commandset(src_data[CS_KEY], name):
            fails.append(f"CommandSet mutated: {name}")
    return fails


def inventory_lines(data: dict[str, bytes]) -> list[str]:
    lines = []
    for country in COUNTRIES:
        cs_name = f"{country}DozerCommandSet"
        body = last_commandset(data[CS_KEY], cs_name)
        lines.append(f"## {country}  CommandSet={cs_name}")
        for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", body, re.M):
            slot, btn = m.group(1), m.group(2)
            block = last_button(data[CB_KEY], btn)
            cmd = field(block, "Command")
            obj = field(block, "Object")
            img = field(block, "ButtonImage")
            tex = f"Art\\Textures\\{img}.tga" if img.startswith("Button_") else "(pre-existing)"
            status = "UNIT_BUILD skipped" if cmd != "DOZER_CONSTRUCT" else (
                "CORRECTED" if btn in NEW_ASSIGN else (
                    "ALREADY CORRECT" if btn in KEEP_ALREADY else "PRESERVED (no matching uploaded image)"
                )
            )
            lines.append(
                f"  slot {slot:>2} | {btn} | {obj or '-'} | {cmd} | {img} | {tex} | {status}"
            )
        lines.append("")
    lines.append("## Iraq Abbas correction")
    for name in ("Command_ConstructIraq_Abbas", "Command_ConstructIraq_Abbas_AI"):
        block = last_button(data[CB_KEY], name)
        lines.append(
            f"  {name} | {field(block, 'Object')} | {field(block, 'ButtonImage')} | "
            f"Art\\Textures\\{field(block, 'ButtonImage')}.tga | CORRECTED (was Button_Atom)"
        )
    lines.append(
        f"  Iraq_VT72BCommandSet slot 14 | {FACTORY_BTN} | Button_MissileFactory | RETAINED"
    )
    return lines


def main() -> None:
    missing = [str(p) for p in NEW_PNG.values() if not p.is_file()]
    if missing:
        raise SystemExit("missing uploaded images:\n" + "\n".join(missing))
    if sha256_path(SRC_DATA) != SHA_DATA_617 or SRC_DATA.stat().st_size != SIZE_DATA_617:
        raise SystemExit("DATA baseline mismatch")
    if sha256_path(SRC_ART) != SHA_ART_617 or SRC_ART.stat().st_size != SIZE_ART_617:
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
    inv = inventory_lines(data)
    (ext / "EU8_DozerCommandSets.ini").write_text(
        "\n".join(last_commandset(data[CS_KEY], n) for n in EU_DOZERS) + "\n"
    )
    (ext / "Iraq_VT72BCommandSet.ini").write_text(last_commandset(data[CS_KEY], DOZER_SET))
    btn_extract = []
    for name in sorted(NEW_ASSIGN) + list(KEEP_ALREADY):
        btn_extract.append(last_button(data[CB_KEY], name))
    (ext / "CommandButton_EU8Construct.ini").write_text("\n".join(btn_extract) + "\n")
    (ext / "EU8ConstructCameos_Images.INI").write_bytes(data[MAPPED_KEY])

    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_EU8_CONSTRUCT_BTNS.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #617 s-iraq-all-construct-btns",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "COMMANDSET_UNCHANGED=YES",
        "FACTORY_SLOT14_RETAINED=YES",
        "IRAQ_ABBAS_BUTTON=Button_Bio",
        "LGM30_BUTTON=Button_Atom (shared Command_ConstructAmericaLgm30; America dozer uses same button)",
        "DATA mutations: CommandButton.ini ButtonImage on EU8 construct buttons + Iraq Abbas + LGM30; new MappedImage INI",
        "ART mutations: Button_Bio.tga and Button_Mantis.tga only",
        "",
        "UNUSED UPLOADED IMAGES:",
        "  Button_C-RAM.png — no C-RAM / CRAM DOZER_CONSTRUCT object for the eight countries",
        "  Button_StrategyCenter.png — Strategy Center explicitly uses Button_GlobalMarket",
        "",
        "PRESERVED (no matching uploaded image):",
        "  NASAMS III, Sky Sabre, Skyranger 30 construct buttons keep Nat_irist / Nat_mantis",
        "  THAAD AI slot is UNIT_BUILD and was not changed",
        "",
        "CHANGED vs PR #617:",
        "  DATA Data\\INI\\CommandButton.ini — ButtonImage only on EU8 construct + Iraq Abbas + shared LGM30",
        "  DATA Data\\INI\\MappedImages\\HandCreated\\EU8ConstructCameos_Images.INI — new",
        "  ART Button_Bio.tga and Button_Mantis.tga",
        "  CommandSet.ini unchanged",
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
            "ZIP_FILE=SPECTER_EU8_CONSTRUCT_BTNS.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #617",
            "FACTORY_SLOT14_RETAINED=YES",
            "IRAQ_ABBAS_BUTTON=Button_Bio",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-eu8-construct-btns/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-eu8-construct-btns/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-eu8-construct-btns/SPECTER_EU8_CONSTRUCT_BTNS.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-eu8-construct-btns",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-eu8-construct-btns",
                "BASELINE=PR #617",
                "FACTORY_SLOT14_RETAINED=YES",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "EU8 construction-menu ButtonImages from uploaded Button_*.png files.\n"
        "Iraq Abbas construct buttons use Button_Bio. CommandSets unchanged.\n"
        "Static validation only.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# EU8 construction button images + Iraq Abbas Bio correction\n\n"
        "- Germany, France, Britain, Italy, Turkey, Sweden, Ukraine, and NATO construction buttons now use uploaded Button_*.png files.\n"
        "- IRIS-T SLX → Button_AirDefense; M777 → Button_Artillery; LGM30G → Button_Atom; Strategy Center → Button_GlobalMarket.\n"
        "- Iraq Abbas construction buttons use Button_Bio instead of Button_Atom.\n"
        "- Iraq VT72B slot 14 remains the missile factory construct button.\n"
        "- CommandSets and factory gameplay unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "No last-wins path conflicts. New Button_Bio / Button_Mantis MappedImages only.\n"
        "Command_ConstructAmericaLgm30 is shared with AmericaDozerCommandSet; ButtonImage change is last-wins for that shared button.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n")
    print("PACKED")
    print(hashes)
    print("\n".join(report[:40]))
    print(f"assigned {len(NEW_ASSIGN)} CommandButtons")


if __name__ == "__main__":
    main()
