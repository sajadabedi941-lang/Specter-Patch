#!/usr/bin/env python3
"""Iran / America / Israel / Russia / China construction-button images.

Baseline: PR #621 SPECTER_FACTORY_ROSTER_ISOLATE
  DATA 366682208 SHA 7090bc97ac54de9e88c0ff9e9f27c7523f235155d154e0a5a8f53690bb554275
  ART  1306997028 SHA d487dd508857a496502bfee0fd5919210346db0d83b80832289035002a0dbdc3

Live dozers from packed last-wins:
  Iran   IranVehicleDozer        IranDozerCommandSet
  America AmericaVehicleDozer    AmericaDozerCommandSet
  Israel AirF_AmericaVehicleDozer AirF_AmericaDozerCommandSet
  Russia RussiaVehicleDozer      RussiaDozerCommandSet
  China  ChinaVehicleDozer       PLADozerCommandSet

CommandSets unchanged. ART unchanged. Factory isolation from #621 retained.
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
SRC_DATA = ROOT / "patch/Release/SPECTER_FACTORY_ROSTER_ISOLATE/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_FACTORY_ROSTER_ISOLATE/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAN_US_ISRAEL_RU_CN_BTNS"
LOOSE_CB = ROOT / "patch/Data/INI/CommandButton.ini"

SHA_DATA_621 = "7090bc97ac54de9e88c0ff9e9f27c7523f235155d154e0a5a8f53690bb554275"
SIZE_DATA_621 = 366682208
SHA_ART_621 = "d487dd508857a496502bfee0fd5919210346db0d83b80832289035002a0dbdc3"
SIZE_ART_621 = 1306997028

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
PK_KEY = r"Data\INI\CommandSet_Pakistan.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
BUILDING_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactoryBuilding.ini"
FACTORY_CS = "Iraq_AlFahdMissileFactoryCommandSet"
BUILDING_CS = "Iraq_AlFahdMissileFactoryBuildingCommandSet"
FACTORY_BTN = "Command_ConstructIraq_AlFahdMissileFactory"
BUILDING_BTN = "Command_ConstructIraq_AlFahdMissileFactoryBuilding"

END_MARKERS = (b"End\r\n", b"End\n", b"End", b"END\r\n", b"END\n", b"END")

NEW_ASSIGN = {
    # Iran
    "Command_ConstructIranPowerplant": "Button_PowerPlant",
    "Command_ConstructIranIndustrialComplex": "Button_GlobalMarket",
    "Command_ConstructIranSupplyCenter": "Button_SupplyCenter",
    "Command_ConstructIranCommandCenter": "Button_CommandCenter",
    "Command_ConstructIranBarracks": "Button_Camp",
    "Command_ConstructIranSejjilSilo": "Button_Atom",
    "Command_ConstructIranD30Post": "Button_Artillery",
    "Command_ConstructIranKhordad15SamSite": "Button_AirDefense",
    "Command_ConstructIranRadarStation": "Button_Radar",
    "Command_ConstructIranBavarSiteAI": "Button_AirDefense",
    "Command_ConstructIranWarFactory": "Button_WarFactory",
    "Command_ConstructIranAirfield": "Button_FighterBase",
    "Command_ConstructIran_HeavyAirBase": "Button_AircraftBase",
    # America — PatriotBattery object is C-RAM; MIM104F is the SAM
    "Command_ConstructAmericaPowerPlant": "Button_PowerPlant",
    "Command_ConstructAmericaStrategyCenter_T": "Button_GlobalMarket",
    "Command_ConstructAmericaStrategyCenter": "Button_GlobalMarket",
    "Command_ConstructAmericaBarracks": "Button_Camp",
    "Command_ConstructAmerica_HeavyAirBase": "Button_AircraftBase",
    "Command_ConstructAmericaSupplyCenter": "Button_SupplyCenter",
    "Command_ConstructAmericaRadarStation": "Button_Radar",
    "Command_ConstructAmericaPatriotBattery": "Button_C-RAM",
    "Command_ConstructAmericaCommandCenter": "Button_CommandCenter",
    "Command_ConstructAmericaFireBase": "Button_Artillery",
    "Command_ConstructAmerica_MIM104F": "Button_AirDefense",
    "Command_ConstructAmericaWarFactory_T": "Button_WarFactory",
    "Command_ConstructAmericaWarFactory": "Button_WarFactory",
    "Command_ConstructAmericaAirfield_T": "Button_FighterBase",
    "Command_ConstructAmericaAirfield": "Button_FighterBase",
    # Israel (AirF_ America* buttons; Side=Israel)
    "AirF_Command_ConstructAmericaPowerPlant": "Button_PowerPlant",
    "AirF_Command_ConstructAmericaStrategyCenter": "Button_GlobalMarket",
    "AirF_Command_ConstructAmericaBarracks": "Button_Camp",
    "Command_ConstructIsrael_HeavyAirBase": "Button_AircraftBase",
    "AirF_Command_ConstructAmericaSupplyCenter": "Button_SupplyCenter",
    "AirF_Command_ConstructAmericaPatriotBattery": "Button_AirDefense",
    "AirF_Command_ConstructAmericaCommandCenter": "Button_CommandCenter",
    "AirF_Command_ConstructAmericaFireBase": "Button_Artillery",
    "Command_ConstructIsraelBuildingC-RAM": "Button_C-RAM",
    "AirF_Command_ConstructAmericaWarFactory": "Button_WarFactory",
    "Command_ConstructIsraelBuildingRadarStation": "Button_Radar",
    "AirF_Command_ConstructAmericaAirfield": "Button_FighterBase",
    # Russia
    "Command_ConstructRussiaPowerPlant": "Button_PowerPlant",
    "Command_ConstructRussiaIndustrialComplex": "Button_GlobalMarket",
    "Command_ConstructRussiaBarracks": "Button_Camp",
    "Command_ConstructRussia91N6E": "Button_Radar",
    "Command_ConstructRussiaSupplyCenter": "Button_SupplyCenter",
    "Command_ConstructRussiaAirfield": "Button_FighterBase",
    "Command_ConstructRussiaRS28NuclearMissileSilo": "Button_Atom",
    "Command_ConstructRussiaWarFactory": "Button_WarFactory",
    "Command_ConstructRussiaCommandCenter": "Button_CommandCenter",
    "Command_ConstructRussia2A65Site": "Button_Artillery",
    "Command_ConstructRussiaS400Site_AI": "Button_AirDefense",
    "Command_ConstructRussia_HeavyAirBase": "Button_AircraftBase",
    # China live PLA dozer
    "Command_ConstructChinaPowerPlant": "Button_PowerPlant",
    "Command_ConstructChina_HeavyAirBase": "Button_AircraftBase",
    "Command_ConstructChinaBarracks": "Button_Camp",
    "Command_ConstructChinaAirfield": "Button_FighterBase",
    "Command_ConstructChinaSupplyCenter": "Button_SupplyCenter",
    "Command_ConstructChinaIndustrialWeaponComplex": "Button_GlobalMarket",
    "Command_ConstructChinaRadarYj26": "Button_Radar",
    "Command_ConstructChinaDF5NuclearMissileSilo": "Button_Atom",
    "Command_ConstructChinaWarFactory": "Button_WarFactory",
    "Command_ConstructChinaCommandCenter": "Button_CommandCenter",
    "Command_ConstructChina_Hq9_Site": "Button_AirDefense",
}

KEEP_ALREADY = {
    "Command_ConstructAmericaLgm30": "Button_Atom",
    BUILDING_BTN: "Button_MissileFactory",
    FACTORY_BTN: "Button_MissileFactory",
}

PRESERVE_NO_IMAGE = {
    "Command_ConstructIranFalaqTrench": "unique Falaq trench",
    "AirF_Command_ConstructAmericaParticleCannonUplink": "Jericho uplink",
    "Command_ConstructRussiaKashtan": "Kashtan CIWS",
    "Command_ConstructChinaBunker": "bunker",
    "Command_ConstructChinaGattlingCannon": "LD2000 CIWS",
}

COUNTRIES = [
    ("Iran", ["IranDozerCommandSet"]),
    ("America", ["AmericaDozerCommandSet"]),
    ("Israel", ["AirF_AmericaDozerCommandSet"]),
    ("Russia", ["RussiaDozerCommandSet"]),
    ("China", ["PLADozerCommandSet"]),
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


def update_loose() -> None:
    if not LOOSE_CB.is_file():
        return
    raw = LOOSE_CB.read_bytes()
    loose_map = {
        name: img
        for name, img in NEW_ASSIGN.items()
        if f"CommandButton {name}".encode("ascii") in raw
    }
    if loose_map:
        LOOSE_CB.write_bytes(splice_button_images(raw, loose_map))


def validate(data, art, src_data, src_art) -> list[str]:
    fails: list[str] = []
    if set(data) != set(src_data):
        fails.append(f"DATA file set changed {set(data) ^ set(src_data)}")
    if art != src_art:
        fails.append("ART mutated")
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
            if field(new_text, "Command") != field(src_text, "Command"):
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

    # Factory isolation
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
    src_iraq_cs = last_commandset(src_data[CS_KEY], FACTORY_CS)
    if iraq_cs != src_iraq_cs:
        fails.append("Iraq factory roster CommandSet mutated")
    if "CB_MISSILE_A" not in iraq_cs:
        fails.append("Iraq roster missing")
    if slot_map(last_commandset(data[CS_KEY], "Iraq_VT72BCommandSet")).get(14) != FACTORY_BTN:
        fails.append("Iraq VT72B factory button lost")

    if field(last_button(data[CB_KEY], "Command_ConstructAmericaLgm30"), "ButtonImage") != "Button_Atom":
        fails.append("America LGM30 is not Button_Atom")
    if field(last_button(data[CB_KEY], "Command_ConstructIraq_Abbas"), "ButtonImage") != "Button_Bio":
        fails.append("Iraq Abbas Bio lost")

    for name in NEW_ASSIGN:
        img = field(last_button(data[CB_KEY], name), "ButtonImage")
        tex = rf"Art\Textures\{img}.tga"
        if tex not in art:
            fails.append(f"missing packed texture {tex} for {name}")

    for name in (
        "IranDozerCommandSet",
        "AmericaDozerCommandSet",
        "AirF_AmericaDozerCommandSet",
        "RussiaDozerCommandSet",
        "PLADozerCommandSet",
        "ChinaDozerCommandSet",
    ):
        if last_commandset(data[CS_KEY], name) != last_commandset(src_data[CS_KEY], name):
            fails.append(f"CommandSet mutated: {name}")
    return fails


def inventory_lines(data: dict[str, bytes], art: dict[str, bytes]) -> list[str]:
    lines = []
    for country, sets in COUNTRIES:
        lines.append(f"# {country}")
        for cs_name in sets:
            body = last_commandset(data[CS_KEY], cs_name)
            lines.append(f"## {cs_name}")
            for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", body, re.M):
                slot, btn = m.group(1), m.group(2)
                block = last_button(data[CB_KEY], btn)
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
                elif btn in PRESERVE_NO_IMAGE:
                    status = f"PRESERVED ({PRESERVE_NO_IMAGE[btn]})"
                else:
                    status = "PRESERVED (no matching uploaded image)"
                lines.append(
                    f"  slot {slot:>2} | {btn} | {obj or '-'} | {cmd} | {img} | {tex} exists={tex_ok} | {status}"
                )
            lines.append("")
    lines.append("## Preserved factory isolation / prior work")
    for name, img in KEEP_ALREADY.items():
        block = last_button(data[CB_KEY], name)
        lines.append(
            f"  {name} | {field(block, 'Object')} | {field(block, 'ButtonImage')} | "
            f"{'RETAINED' if field(block, 'ButtonImage') == img else 'LOST'}"
        )
    return lines


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_621 or SRC_DATA.stat().st_size != SIZE_DATA_621:
        raise SystemExit("DATA baseline mismatch")
    if sha256_path(SRC_ART) != SHA_ART_621 or SRC_ART.stat().st_size != SIZE_ART_621:
        raise SystemExit("ART baseline mismatch")

    update_loose()
    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    data[CB_KEY] = splice_button_images(src_data[CB_KEY], NEW_ASSIGN)

    fails = validate(data, art, src_data, src_art)
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
    (ext / "INVENTORY.txt").write_text("\n".join(inv) + "\n")
    chunks = [last_commandset(data[CS_KEY], n) for _, sets in COUNTRIES for n in sets]
    (ext / "DozerCommandSets.ini").write_text("\n\n".join(chunks) + "\n")
    btns = [last_button(data[CB_KEY], n) for n in sorted(NEW_ASSIGN) + list(KEEP_ALREADY)]
    (ext / "CommandButton_IR5Construct.ini").write_text("\n".join(btns) + "\n")

    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_IRAN_US_ISRAEL_RU_CN_BTNS.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #621 s-factory-roster-isolate",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "ART_UNCHANGED=YES",
        "COMMANDSET_UNCHANGED=YES",
        "IRAQ_FACTORY_ROSTER_UNCHANGED=YES",
        "RUSSIA_CHINA_FACTORY_BUILDING_ONLY=YES",
        "AMERICA_LGM30=Button_Atom",
        "",
        "PRESERVED (no matching uploaded image):",
        "  Iran Falaq trench, Israel Jericho uplink, Russia Kashtan, China bunker, China LD2000",
        "  America THAAD slot is UNIT_BUILD and was not changed",
        "",
        "OBJECT-FOLLOWED MAPPINGS:",
        "  AmericaPatriotBattery object is C-RAM -> Button_C-RAM",
        "  America_MIM104F object is SAM -> Button_AirDefense",
        "  Israel PatriotBattery object is Iron Dome SAM -> Button_AirDefense",
        "  IsraelBuildingC-RAM object is C-RAM -> Button_C-RAM",
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
            "ZIP_FILE=SPECTER_IRAN_US_ISRAEL_RU_CN_BTNS.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #621",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iran-us-israel-ru-cn-btns/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iran-us-israel-ru-cn-btns/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iran-us-israel-ru-cn-btns/SPECTER_IRAN_US_ISRAEL_RU_CN_BTNS.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-iran-us-israel-ru-cn-btns",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-iran-us-israel-ru-cn-btns",
                "BASELINE=PR #621",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Iran, America, Israel, Russia, and China construction-menu ButtonImages\n"
        "from uploaded Button_*.png files. CommandSets and ART unchanged.\n"
        "Russia/China keep the building-only missile factory from PR #621.\n"
        "Static validation only.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Iran / America / Israel / Russia / China construction button images\n\n"
        "- Live dozer construction buttons now use uploaded Button_*.png files.\n"
        "- America LGM30G remains Button_Atom. America PatriotBattery maps to Button_C-RAM because that object is C-RAM.\n"
        "- Russia and China still construct the building-only missile factory from PR #621 (no Iraq A-M roster).\n"
        "- CommandSets, ART, and Iraq factory gameplay are unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "No new ART or MappedImages. Command_ConstructAmericaLgm30 already Button_Atom (EU8 shared).\n"
        "CommandSets unchanged. Factory isolation from PR #621 retained.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n")
    print("PACKED")
    print(hashes)
    print("\n".join(report[:40]))
    print(f"assigned {len(NEW_ASSIGN)} CommandButtons")


if __name__ == "__main__":
    main()
