#!/usr/bin/env python3
"""Fix North Korea / South Korea / Japan / Vietnam construction-button images.

WHY PREVIOUS ASIA4 FAILED:
  PR #619 (s-asia4-construct-btns) was audit-only. It looked for LGM30G / M777 /
  IRIS-T / Strategy Center, found none, and shipped archives byte-identical to
  PR #618. The live VT72B construction buttons were never remapped, so in-game
  menus still showed irq_* / us_* / pla_* portraits.

LIVE IN-GAME PATH (packed last-wins, PR #624 baseline):
  PlayerTemplate StartingUnit0 = {Country}_VT72B
  Object CommandSet            = {Country}_VT72BCommandSet
  CommandSet last-wins         = Data\\INI\\CommandSet.ini
  CommandButton last-wins      = Data\\INI\\CommandButton.ini
    except NK barracks         = Data\\INI\\CommandButton_ZZZZ_NKBarracksFlag.ini

Unused first CommandSet.ini definition of NorthKorea_VT72BCommandSet (MIC/Sam2)
is overwritten by the later packed definition and is not live.

CommandSets unchanged. ART unchanged. Factory isolation retained.
Static validation only.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_KASHTAN_FALAQ_RESTORE/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_KASHTAN_FALAQ_RESTORE/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_ASIA4_CONSTRUCT_BTNS_FIX"
LOOSE_CB = ROOT / "patch/Data/INI/CommandButton.ini"
LOOSE_NK = ROOT / "patch/Data/INI/CommandButton_ZZZZ_NKBarracksFlag.ini"

SHA_DATA_624 = "a3b1cc8efb2d84ee3f5d1dff8c4ded944802823733bf8a9e7ecb23d4d9a0b15b"
SIZE_DATA_624 = 366683148
SHA_ART_624 = "02376df9e1ba9dfe8069e368bf41ac71fa0de3a15bc7e7b72f98042a41248521"
SIZE_ART_624 = 1307095498

CB_KEY = r"Data\INI\CommandButton.ini"
NK_KEY = r"Data\INI\CommandButton_ZZZZ_NKBarracksFlag.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
PK_KEY = r"Data\INI\CommandSet_Pakistan.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
BUILDING_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactoryBuilding.ini"
FACTORY_CS = "Iraq_AlFahdMissileFactoryCommandSet"
BUILDING_CS = "Iraq_AlFahdMissileFactoryBuildingCommandSet"
FACTORY_BTN = "Command_ConstructIraq_AlFahdMissileFactory"
BUILDING_BTN = "Command_ConstructIraq_AlFahdMissileFactoryBuilding"

END_MARKERS = (b"End\r\n", b"End\n", b"End", b"END\r\n", b"END\n", b"END")

COUNTRIES = [
    ("NorthKorea", "NorthKorea_VT72BCommandSet"),
    ("SouthKorea", "SouthKorea_VT72BCommandSet"),
    ("Japan", "Japan_VT72BCommandSet"),
    ("Vietnam", "Vietnam_VT72BCommandSet"),
]

SUFFIX_IMAGE = {
    "PowerPlant": "Button_PowerPlant",
    "CommandCenter": "Button_CommandCenter",
    "SupplyCenter": "Button_SupplyCenter",
    "WarFactory": "Button_WarFactory",
    "LargeAirBase": "Button_FighterBase",
    "DefenseSite_SAFE": "Button_DefenceSite",
    "RadarStation": "Button_Radar",
    "HeavyAirBase": "Button_AircraftBase",
    "Barracks_SAFE": "Button_Camp",
    "NuclearCenter": "Button_Atom",
    "D30_SAFE": "Button_Artillery",
    "CRAM": "Button_C-RAM",
    "Hq9_Site": "Button_AirDefense",
}

NEW_ASSIGN: dict[str, str] = {}
for country, _ in COUNTRIES:
    for suffix, img in SUFFIX_IMAGE.items():
        NEW_ASSIGN[f"Command_Construct{country}_{suffix}"] = img

BEFORE = {
    "Command_ConstructNorthKorea_PowerPlant": "irq_powerplant",
    "Command_ConstructNorthKorea_CommandCenter": "irq_comndcntr",
    "Command_ConstructNorthKorea_SupplyCenter": "irq_money",
    "Command_ConstructNorthKorea_WarFactory": "irq_warfctry",
    "Command_ConstructNorthKorea_LargeAirBase": "irq_airfld",
    "Command_ConstructNorthKorea_DefenseSite_SAFE": "irq_defsite",
    "Command_ConstructNorthKorea_RadarStation": "irq_rdrstatn",
    "Command_ConstructNorthKorea_HeavyAirBase": "us_airfield",
    "Command_ConstructNorthKorea_Barracks_SAFE": "irq_barracks",
    "Command_ConstructNorthKorea_NuclearCenter": "irq_alhussien",
    "Command_ConstructNorthKorea_D30_SAFE": "irq_d30",
    "Command_ConstructNorthKorea_CRAM": "us_mim90d",
    "Command_ConstructNorthKorea_Hq9_Site": "pla_hq9b",
    "Command_ConstructSouthKorea_PowerPlant": "irq_powerplant",
    "Command_ConstructSouthKorea_CommandCenter": "irq_comndcntr",
    "Command_ConstructSouthKorea_SupplyCenter": "irq_money",
    "Command_ConstructSouthKorea_WarFactory": "irq_warfctry",
    "Command_ConstructSouthKorea_LargeAirBase": "irq_airfld",
    "Command_ConstructSouthKorea_DefenseSite_SAFE": "irq_defsite",
    "Command_ConstructSouthKorea_RadarStation": "irq_rdrstatn",
    "Command_ConstructSouthKorea_HeavyAirBase": "us_airfield",
    "Command_ConstructSouthKorea_Barracks_SAFE": "CampFlagSouthKorea",
    "Command_ConstructSouthKorea_NuclearCenter": "irq_alhussien",
    "Command_ConstructSouthKorea_D30_SAFE": "irq_d30",
    "Command_ConstructSouthKorea_CRAM": "us_mim90d",
    "Command_ConstructSouthKorea_Hq9_Site": "pla_hq9b",
    "Command_ConstructJapan_PowerPlant": "irq_powerplant",
    "Command_ConstructJapan_CommandCenter": "irq_comndcntr",
    "Command_ConstructJapan_SupplyCenter": "irq_money",
    "Command_ConstructJapan_WarFactory": "irq_warfctry",
    "Command_ConstructJapan_LargeAirBase": "irq_airfld",
    "Command_ConstructJapan_DefenseSite_SAFE": "irq_defsite",
    "Command_ConstructJapan_RadarStation": "irq_rdrstatn",
    "Command_ConstructJapan_HeavyAirBase": "us_airfield",
    "Command_ConstructJapan_Barracks_SAFE": "CampFlagJapan",
    "Command_ConstructJapan_NuclearCenter": "irq_alhussien",
    "Command_ConstructJapan_D30_SAFE": "irq_d30",
    "Command_ConstructJapan_CRAM": "us_mim90d",
    "Command_ConstructJapan_Hq9_Site": "pla_hq9b",
    "Command_ConstructVietnam_PowerPlant": "irq_powerplant",
    "Command_ConstructVietnam_CommandCenter": "irq_comndcntr",
    "Command_ConstructVietnam_SupplyCenter": "irq_money",
    "Command_ConstructVietnam_WarFactory": "irq_warfctry",
    "Command_ConstructVietnam_LargeAirBase": "irq_airfld",
    "Command_ConstructVietnam_DefenseSite_SAFE": "irq_defsite",
    "Command_ConstructVietnam_RadarStation": "irq_rdrstatn",
    "Command_ConstructVietnam_HeavyAirBase": "us_airfield",
    "Command_ConstructVietnam_Barracks_SAFE": "CampFlagVietnam",
    "Command_ConstructVietnam_NuclearCenter": "irq_alhussien",
    "Command_ConstructVietnam_D30_SAFE": "irq_d30",
    "Command_ConstructVietnam_CRAM": "us_mim90d",
    "Command_ConstructVietnam_Hq9_Site": "pla_hq9b",
}

KEEP = {
    BUILDING_BTN: "Button_MissileFactory",
    FACTORY_BTN: "Button_MissileFactory",
    "Command_ConstructAmericaLgm30": "Button_Atom",
    "Command_ConstructIraq_Abbas": "Button_Bio",
    "Command_ConstructIraq_Abbas_AI": "Button_Bio",
    "Command_ConstructRussiaKashtan": "Button_kashtan",
    "Command_ConstructChinaGattlingCannon": "Button_kashtan",
    "Command_ConstructIranFalaqTrench": "Button_falaq",
}


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
    LOOSE_NK.write_text(
        "CommandButton Command_ConstructNorthKorea_Barracks_SAFE\r\n"
        "  Command          = DOZER_CONSTRUCT\r\n"
        "  Object           = NorthKorea_Barracks\r\n"
        "  TextLabel        = CONTROLBAR:ConstructNorthKoreaBarracks\r\n"
        "  ButtonImage      = Button_Camp\r\n"
        "  ButtonBorderType = BUILD\r\n"
        "  DescriptLabel    = CONTROLBAR:ToolTipNorthKoreaBarracks\r\n"
        "End\r\n"
    )


def validate(data, art, src_data, src_art, order) -> list[str]:
    fails: list[str] = []
    if set(data) != set(src_data):
        fails.append(f"DATA file set changed {set(data) ^ set(src_data)}")
    if art != src_art:
        fails.append("ART mutated")
    mutated = sorted(k for k in src_data if src_data[k] != data.get(k))
    if mutated != sorted([CB_KEY, NK_KEY]):
        fails.append(f"unexpected DATA mutations: {mutated}")
    if data[CS_KEY] != src_data[CS_KEY]:
        fails.append("CommandSet.ini mutated")
    if data[PK_KEY] != src_data[PK_KEY]:
        fails.append("CommandSet_Pakistan.ini mutated")
    if data[FACTORY_KEY] != src_data[FACTORY_KEY]:
        fails.append("Iraq factory object mutated")
    if data[BUILDING_KEY] != src_data[BUILDING_KEY]:
        fails.append("building-only factory object mutated")

    def strip_img(s: str) -> str:
        return re.sub(r"(ButtonImage\s*=\s*)\S+", r"\1X", s)

    for key in (CB_KEY, NK_KEY):
        src_btns = {n: b for n, b in iter_blocks(src_data[key], b"CommandButton ")}
        new_btns = {n: b for n, b in iter_blocks(data[key], b"CommandButton ")}
        if set(src_btns) != set(new_btns):
            fails.append(f"{key} CommandButton name set changed")
        for name, src_block in src_btns.items():
            new_block = new_btns[name]
            src_text = src_block.decode("latin1")
            new_text = new_block.decode("latin1")
            if name in NEW_ASSIGN:
                want = NEW_ASSIGN[name]
                if field(src_text, "ButtonImage") != BEFORE[name]:
                    fails.append(
                        f"{key} {name} baseline {field(src_text, 'ButtonImage')} != {BEFORE[name]}"
                    )
                if field(new_text, "ButtonImage") != want:
                    fails.append(f"{key} {name} ButtonImage={field(new_text, 'ButtonImage')} want {want}")
                if field(new_text, "Command") != field(src_text, "Command"):
                    fails.append(f"{name} Command changed")
                if field(src_text, "Object") != field(new_text, "Object"):
                    fails.append(f"{name} Object changed")
                if strip_img(src_text) != strip_img(new_text):
                    fails.append(f"{name} changed beyond ButtonImage")
            elif src_block != new_block:
                fails.append(f"non-target button mutated in {key}: {name}")

    for country, cs_name in COUNTRIES:
        cs = last_commandset(data[CS_KEY], cs_name)
        if cs != last_commandset(src_data[CS_KEY], cs_name):
            fails.append(f"CommandSet mutated: {cs_name}")
        slots = slot_map(cs)
        if slots.get(6) != BUILDING_BTN:
            fails.append(f"{country} factory slot lost: {slots.get(6)}")
        for slot, btn in slots.items():
            block = last_button(data[CB_KEY] if btn != "Command_ConstructNorthKorea_Barracks_SAFE" else data[NK_KEY], btn)
            if btn == "Command_ConstructNorthKorea_Barracks_SAFE":
                # last-wins is NK_KEY; also confirm archive last-wins
                if last_wins_source(data, order, btn) != NK_KEY:
                    fails.append(f"NK barracks last-wins from {last_wins_source(data, order, btn)}")
            elif btn in NEW_ASSIGN:
                if last_wins_source(data, order, btn) != CB_KEY:
                    fails.append(f"{btn} last-wins from {last_wins_source(data, order, btn)}")
            if btn in NEW_ASSIGN:
                img = field(last_button_any(data, order, btn), "ButtonImage")
                if img != NEW_ASSIGN[btn]:
                    fails.append(f"{country} slot {slot} effective {img} != {NEW_ASSIGN[btn]}")
                tex = rf"Art\Textures\{img}.tga"
                if tex not in art:
                    fails.append(f"missing packed texture {tex}")

    for name, img in KEEP.items():
        if field(last_button_any(data, order, name), "ButtonImage") != img:
            fails.append(f"kept mapping lost: {name}")

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
    return fails


def last_button_any(files: dict[str, bytes], order: list[str], name: str) -> str:
    last = ""
    for key in order:
        if not key.lower().endswith(".ini"):
            continue
        blob = files[key]
        if b"CommandButton " not in blob:
            continue
        for n, block in iter_blocks(blob, b"CommandButton "):
            if n == name:
                last = block.decode("latin1")
    return last


def report_lines(data: dict[str, bytes], art: dict[str, bytes], order: list[str]) -> list[str]:
    lines = [
        "# Cause of previous Asia4 failure",
        "  PR #619 was audit-only (DATA/ART identical to #618). Live VT72B ButtonImages were never remapped.",
        "  Live builders are {Country}_VT72B, not unused first CommandSet.ini MIC/Sam2 definition.",
        "  North Korea barracks last-wins from CommandButton_ZZZZ_NKBarracksFlag.ini (must be spliced).",
        "",
        "# Before / after",
    ]
    for country, cs_name in COUNTRIES:
        lines.append(f"## {country}  CommandSet={cs_name}  builder={country}_VT72B")
        cs = last_commandset(data[CS_KEY], cs_name)
        for slot, btn in sorted(slot_map(cs).items()):
            block = last_button_any(data, order, btn)
            cmd = field(block, "Command")
            obj = field(block, "Object")
            img = field(block, "ButtonImage")
            tex = rf"Art\Textures\{img}.tga"
            src = last_wins_source(data, order, btn)
            if btn in NEW_ASSIGN:
                status = f"CORRECTED {BEFORE[btn]} -> {img}"
            elif btn in KEEP:
                status = "ALREADY CORRECT"
            elif cmd != "DOZER_CONSTRUCT":
                status = "NON-CONSTRUCT preserved"
            else:
                status = "PRESERVED"
            lines.append(
                f"  slot {slot:>2} | {btn} | {obj or '-'} | {cmd} | {img} | {tex} exists={tex in art if img.startswith('Button_') else 'n/a'} | last-wins={Path(src).name if src else '?'} | {status}"
            )
        lines.append("")
    return lines


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_624 or SRC_DATA.stat().st_size != SIZE_DATA_624:
        raise SystemExit("DATA baseline mismatch")
    if sha256_path(SRC_ART) != SHA_ART_624 or SRC_ART.stat().st_size != SIZE_ART_624:
        raise SystemExit("ART baseline mismatch")

    update_loose()
    src_bytes = SRC_DATA.read_bytes()
    src_data, _ = parse_big_ordered(src_bytes)
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    data[CB_KEY] = splice_button_images(src_data[CB_KEY], NEW_ASSIGN)
    data[NK_KEY] = splice_button_images(src_data[NK_KEY], {"Command_ConstructNorthKorea_Barracks_SAFE": "Button_Camp"})

    data_big = build_big(data)
    art_big = build_big(art)
    packed_data, order = parse_big_ordered(data_big)
    packed_art = parse_big(art_big)
    fails = validate(packed_data, packed_art, src_data, src_art, order)
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
    inv = report_lines(packed_data, packed_art, order)
    (ext / "BEFORE_AFTER.txt").write_text("\n".join(inv) + "\n")
    chunks = [last_commandset(packed_data[CS_KEY], cs) for _, cs in COUNTRIES]
    (ext / "VT72BCommandSets.ini").write_text("\n\n".join(chunks) + "\n")
    btns = [last_button_any(packed_data, order, n) for n in sorted(NEW_ASSIGN)]
    (ext / "CommandButton_Asia4Construct.ini").write_text("\n".join(btns) + "\n")

    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_ASIA4_CONSTRUCT_BTNS_FIX.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #624 s-kashtan-falaq-restore",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "ART_UNCHANGED=YES",
        "COMMANDSET_UNCHANGED=YES",
        "IRAQ_FACTORY_ROSTER_UNCHANGED=YES",
        "RUSSIA_CHINA_FACTORY_BUILDING_ONLY=YES",
        "KASHTAN_FALAQ_RETAINED=YES",
        "IRAQ_ABBAS_BIO_RETAINED=YES",
        "",
        "CAUSE: PR #619 audit-only; no live VT72B ButtonImages were changed.",
        "FIX: splice packed CommandButton.ini (52 live construct buttons) and",
        "     CommandButton_ZZZZ_NKBarracksFlag.ini (NK barracks last-wins).",
        "",
        *inv,
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n")
    hashes = "\n".join(
        [
            "DATA_CHANGED=YES",
            "ART_CHANGED=NO",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_SIZE={art_path.stat().st_size}",
            f"ART_SHA256={art_sha}",
            "ZIP_FILE=SPECTER_ASIA4_CONSTRUCT_BTNS_FIX.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #624",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-asia4-construct-btns-fix/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-asia4-construct-btns-fix/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-asia4-construct-btns-fix/SPECTER_ASIA4_CONSTRUCT_BTNS_FIX.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-asia4-construct-btns-fix",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-asia4-construct-btns-fix",
                "BASELINE=PR #624",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "North Korea, South Korea, Japan, and Vietnam construction-menu ButtonImages.\n"
        "Fixes the live VT72B last-wins definitions that PR #619 never changed.\n"
        "CommandSets and ART unchanged. Static validation only.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Asia-4 construction button images (actual last-wins fix)\n\n"
        "- Previous Asia4 release was audit-only and did not change in-game buttons.\n"
        "- Live builders are country VT72B CommandSets. NK barracks last-wins from a later ZZZZ file.\n"
        "- Shared Button_* images applied to the effective packed CommandButtons.\n"
        "- Factory isolation, Kashtan/Falaq, and Iraq Abbas Bio are unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "NK barracks last-wins from CommandButton_ZZZZ_NKBarracksFlag.ini; that file is spliced.\n"
        "Japan/SK/Vietnam Capture ZZZZ file contains UNIT_BUILD rifles only and was not changed.\n"
        "Unused MIC/Sam2 construct buttons are not on the live VT72B and were not remapped.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n")
    print("PACKED")
    print(hashes)
    print("\n".join(report[:45]))
    print(f"assigned {len(NEW_ASSIGN)} CommandButtons")


if __name__ == "__main__":
    main()
