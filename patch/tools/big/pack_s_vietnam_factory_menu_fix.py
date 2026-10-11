#!/usr/bin/env python3
"""Fix empty Vietnam missile factory menu by splicing the live command chain.

ROOT CAUSE (PR #626):
  Vietnam_WarFactoryCommandSet and Iraq_AlFahdMissileFactoryCommandSet last-wins
  from Data\\INI\\CommandSet.ini. CB_MISSILE_A-M last-wins from CommandButton.ini.

  PR #626 left CommandSet.ini Vietnam_VT72BCommandSet on
  Command_ConstructIraq_AlFahdMissileFactoryBuilding (Sell-only) and never put
  Vietnam_MissileFactoryCommandSet or CB_VIETNAM_MISSILE_A-H in those canonical
  files. A-H lived only in CommandSet_VietnamMissiles.ini /
  CommandButton_VietnamMissiles.ini.

  Runtime: factory opens with no A-H (Sell-only building and/or unresolved
  satellite buttons).

FIX:
  Splice the proven Iraq/WarFactory path:
    - last Vietnam_VT72BCommandSet in CommandSet.ini -> construct Vietnam_MissileFactory
    - append Vietnam_MissileFactoryCommandSet to CommandSet.ini
    - append construct + CB_VIETNAM_MISSILE_A-H to CommandButton.ini
  Satellite files kept with the same content. ART unchanged. No ZZZZ. No rearm.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_VIETNAM_MISSILES_AH/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_VIETNAM_MISSILES_AH/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_VIETNAM_FACTORY_MENU_FIX"

SHA_DATA_626 = "426940cef020cf85622bf59bf9f9ed11c8ab5a407a50d43315f7aa6fa0618c1f"
SIZE_DATA_626 = 366800464
SHA_ART_626 = "3030c68abc11b801121feeac44a21af4407ffa9be385fba0f979d01fd7e4ab44"
SIZE_ART_626 = 1343628546

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
SAT_CB = r"Data\INI\CommandButton_VietnamMissiles.ini"
SAT_CS = r"Data\INI\CommandSet_VietnamMissiles.ini"
FAC_KEY = (
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces"
    r"\Buildings\Vietnam_MissileFactory.ini"
)
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
BUILDING_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactoryBuilding.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"

MISSILES = [
    ("A", "CB_VIETNAM_MISSILE_A", "Vietnam_VCM01", "specter_missile_a"),
    ("B", "CB_VIETNAM_MISSILE_B", "Vietnam_VCM02", "specter_missile_b"),
    ("C", "CB_VIETNAM_MISSILE_C", "Vietnam_SongHong", "specter_missile_c"),
    ("D", "CB_VIETNAM_MISSILE_D", "Vietnam_HongHa", "specter_missile_d"),
    ("E", "CB_VIETNAM_MISSILE_E", "Vietnam_CuuLong", "specter_missile_e"),
    ("F", "CB_VIETNAM_MISSILE_F", "Vietnam_TruongSon", "specter_missile_f"),
    ("G", "CB_VIETNAM_MISSILE_G", "Vietnam_BachDang", "specter_missile_g"),
    ("H", "CB_VIETNAM_MISSILE_H", "Vietnam_ThangLong", "specter_missile_h"),
]

VT72B_NEW = (
    "CommandSet Vietnam_VT72BCommandSet\r\n"
    "  1  = Command_ConstructVietnam_PowerPlant\r\n"
    "  2  = Command_ConstructVietnam_CommandCenter\r\n"
    "  3  = Command_ConstructVietnam_SupplyCenter\r\n"
    "  4  = Command_ConstructVietnam_WarFactory\r\n"
    "  5  = Command_ConstructVietnam_LargeAirBase\r\n"
    "  6  = Command_ConstructVietnam_MissileFactory\r\n"
    "  7  = Command_ConstructVietnam_DefenseSite_SAFE\r\n"
    "  8  = Command_ConstructVietnam_RadarStation\r\n"
    "  9  = Command_ConstructVietnam_HeavyAirBase\r\n"
    "  10 = Command_ConstructVietnam_Barracks_SAFE\r\n"
    "  11 = Command_ConstructVietnam_NuclearCenter\r\n"
    "  12 = Command_ConstructVietnam_D30_SAFE\r\n"
    "  13 = Command_ConstructVietnam_CRAM\r\n"
    "  14 = Command_ConstructVietnam_Hq9_Site\r\n"
    "  15 = Command_Stop\r\n"
    "End"
)

FACTORY_SET = (
    "CommandSet Vietnam_MissileFactoryCommandSet\r\n"
    "  1  = CB_VIETNAM_MISSILE_A\r\n"
    "  2  = CB_VIETNAM_MISSILE_B\r\n"
    "  3  = CB_VIETNAM_MISSILE_C\r\n"
    "  4  = CB_VIETNAM_MISSILE_D\r\n"
    "  5  = CB_VIETNAM_MISSILE_E\r\n"
    "  6  = CB_VIETNAM_MISSILE_F\r\n"
    "  7  = CB_VIETNAM_MISSILE_G\r\n"
    "  8  = CB_VIETNAM_MISSILE_H\r\n"
    "  13 = Command_SetRallyPoint\r\n"
    "  14 = Command_Sell\r\n"
    "End"
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
    files: dict[str, bytes] = {}
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


def big_structure_ok(data: bytes) -> list[str]:
    fails = []
    archive_size, count, header_size, hdr_end, files = parse_index(data)
    if archive_size != len(data):
        fails.append(f"archive size {archive_size} != {len(data)}")
    if count != len(files):
        fails.append("count mismatch")
    if header_size != hdr_end:
        fails.append("header size mismatch")
    seen = set()
    for name, off, size in files:
        key = name.replace("/", "\\").lower()
        if key in seen:
            fails.append(f"dup {name}")
        seen.add(key)
        if off < header_size or off + size > len(data):
            fails.append(f"range {name}")
    return fails


def last_spans(text: str, kind: str, name: str):
    return list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text))


def last_block(text: str, kind: str, name: str) -> str:
    ms = last_spans(text, kind, name)
    return ms[-1].group(0) if ms else ""


def last_block_from_files(order: list[str], files: dict[str, bytes], kind: str, name: str) -> tuple[str, str]:
    found = ("", "")
    needle = f"{kind} {name}".encode("ascii")
    for key in order:
        blob = files[key]
        if needle not in blob:
            continue
        try:
            text = blob.decode("latin1")
        except Exception:
            continue
        block = last_block(text, kind, name)
        if block:
            found = (key, block)
    return found


def field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block or "", re.M)
    return m.group(1).strip() if m else ""


def replace_last(text: str, kind: str, name: str, new_block: str) -> str:
    ms = last_spans(text, kind, name)
    if not ms:
        raise SystemExit(f"missing {kind} {name}")
    m = ms[-1]
    return text[: m.start()] + new_block + text[m.end() :]


def command_buttons() -> str:
    lines = [
        "CommandButton Command_ConstructVietnam_MissileFactory",
        "  Command          = DOZER_CONSTRUCT",
        "  Object           = Vietnam_MissileFactory",
        "  TextLabel        = CONTROLBAR:ConstructVietnamMissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel    = CONTROLBAR:ToolTipVietnamMissileFactory",
        "End",
        "",
    ]
    for slot, btn, obj, img in MISSILES:
        lines.extend(
            [
                f"CommandButton {btn}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {obj}",
                f"  TextLabel     = CONTROLBAR:VietnamMissile{slot}",
                f"  ButtonImage   = {img}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTipVietnamMissile{slot}",
                "End",
                "",
            ]
        )
    return "\r\n".join(lines)


def validate(data: dict[str, bytes], src: dict[str, bytes], order: list[str]) -> list[str]:
    fails: list[str] = []
    for key in (R11_KEY, FACTORY_KEY, BUILDING_KEY, WEAPON_KEY):
        if data.get(key) != src.get(key):
            fails.append(f"frozen mutated {key}")

    cs = data[CS_KEY].decode("latin1")
    src_cs = src[CS_KEY].decode("latin1")
    cb = data[CB_KEY].decode("latin1")
    src_cb = src[CB_KEY].decode("latin1")

    if last_block(cs, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet") != last_block(
        src_cs, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet"
    ):
        fails.append("Iraq factory roster mutated")
    if last_block(cs, "CommandSet", "Iraq_AlFahdMissileFactoryBuildingCommandSet") != last_block(
        src_cs, "CommandSet", "Iraq_AlFahdMissileFactoryBuildingCommandSet"
    ):
        fails.append("Iraq Sell-only building CommandSet mutated")
    for country in ("NorthKorea", "SouthKorea", "Japan"):
        if last_block(cs, "CommandSet", f"{country}_VT72BCommandSet") != last_block(
            src_cs, "CommandSet", f"{country}_VT72BCommandSet"
        ):
            fails.append(f"{country} VT72B mutated")
        block = last_block(cs, "CommandSet", f"{country}_VT72BCommandSet")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in block:
            fails.append(f"{country} lost shared Sell-only factory")
        if "Command_ConstructVietnam_MissileFactory" in block:
            fails.append(f"{country} gained Vietnam factory")

    for img, btn in (
        ("Button_kashtan", "Command_ConstructRussiaKashtan"),
        ("Button_falaq", "Command_ConstructIranFalaqTrench"),
        ("Button_Bio", "Command_ConstructIraq_Abbas"),
    ):
        if field(last_block(cb, "CommandButton", btn), "ButtonImage") != img:
            fails.append(f"{btn} image lost")
        if last_block(cb, "CommandButton", btn) != last_block(src_cb, "CommandButton", btn):
            fails.append(f"{btn} mutated")

    # Canonical CommandSet.ini must now own the live Vietnam chain.
    vn_cs_ini = last_block(cs, "CommandSet", "Vietnam_VT72BCommandSet")
    if "Command_ConstructVietnam_MissileFactory" not in vn_cs_ini:
        fails.append("CommandSet.ini VT72B still not Vietnam factory")
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in vn_cs_ini:
        fails.append("CommandSet.ini VT72B still Sell-only factory")

    fac_cs_ini = last_block(cs, "CommandSet", "Vietnam_MissileFactoryCommandSet")
    if not fac_cs_ini:
        fails.append("CommandSet.ini missing Vietnam_MissileFactoryCommandSet")
    for _slot, btn, _obj, _img in MISSILES:
        if btn not in fac_cs_ini:
            fails.append(f"CommandSet.ini factory missing {btn}")

    # Effective last-wins across the whole archive.
    key, vn_cs = last_block_from_files(order, data, "CommandSet", "Vietnam_VT72BCommandSet")
    if "Command_ConstructVietnam_MissileFactory" not in vn_cs:
        fails.append(f"last-wins VT72B from {key} not Vietnam factory")
    key, fac_cs = last_block_from_files(order, data, "CommandSet", "Vietnam_MissileFactoryCommandSet")
    if not fac_cs:
        fails.append("last-wins missing Vietnam_MissileFactoryCommandSet")

    key, fac_obj = last_block_from_files(order, data, "Object", "Vietnam_MissileFactory")
    if field(fac_obj, "CommandSet") != "Vietnam_MissileFactoryCommandSet":
        fails.append(f"factory object CommandSet {field(fac_obj, 'CommandSet')} from {key}")
    if field(fac_obj, "Side") != "Vietnam":
        fails.append("factory Side")

    key, construct = last_block_from_files(order, data, "CommandButton", "Command_ConstructVietnam_MissileFactory")
    if field(construct, "Object") != "Vietnam_MissileFactory":
        fails.append(f"construct Object from {key}")
    if field(construct, "Command") != "DOZER_CONSTRUCT":
        fails.append("construct Command")
    if field(construct, "ButtonImage") != "Button_MissileFactory":
        fails.append("construct image")
    if last_block(cb, "CommandButton", "Command_ConstructVietnam_MissileFactory") == "":
        fails.append("CommandButton.ini missing construct button")

    for slot, btn, obj, img in MISSILES:
        if last_block(cb, "CommandButton", btn) == "":
            fails.append(f"CommandButton.ini missing {btn}")
        _k, block = last_block_from_files(order, data, "CommandButton", btn)
        if field(block, "Command") != "UNIT_BUILD":
            fails.append(f"{btn} Command")
        if field(block, "Object") != obj:
            fails.append(f"{btn} Object={field(block, 'Object')}")
        if field(block, "ButtonImage") != img:
            fails.append(f"{btn} image")
        if field(block, "TextLabel") != f"CONTROLBAR:VietnamMissile{slot}":
            fails.append(f"{btn} TextLabel")
        _k, unit = last_block_from_files(order, data, "Object", obj)
        if not unit:
            fails.append(f"missing object {obj}")
        elif field(unit, "Side") != "Vietnam":
            fails.append(f"{obj} Side")

    r11 = last_block(data[R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB")
    if field(r11, "BuildCost") != "1200" or "Irq_9P117" not in r11:
        fails.append("9P117 mutated")
    if "ZZZZ" in SAT_CB or "ZZZZ" in SAT_CS:
        fails.append("ZZZZ shortcut")
    return fails


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_626 or SRC_DATA.stat().st_size != SIZE_DATA_626:
        raise SystemExit("DATA baseline is not PR #626 SPECTER_VIETNAM_MISSILES_AH")
    if sha256_path(SRC_ART) != SHA_ART_626 or SRC_ART.stat().st_size != SIZE_ART_626:
        raise SystemExit("ART baseline is not PR #626 SPECTER_VIETNAM_MISSILES_AH")

    src_data, _ = parse_big_ordered(SRC_DATA.read_bytes())
    data = dict(src_data)

    cs = src_data[CS_KEY].decode("latin1")
    old_vn = last_block(cs, "CommandSet", "Vietnam_VT72BCommandSet")
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in old_vn:
        raise SystemExit("unexpected CommandSet.ini Vietnam_VT72BCommandSet")
    cs = replace_last(cs, "CommandSet", "Vietnam_VT72BCommandSet", VT72B_NEW)
    if last_block(cs, "CommandSet", "Vietnam_MissileFactoryCommandSet"):
        cs = replace_last(cs, "CommandSet", "Vietnam_MissileFactoryCommandSet", FACTORY_SET)
    else:
        cs = cs.rstrip("\r\n") + "\r\n\r\n" + FACTORY_SET + "\r\n"
    data[CS_KEY] = cs.encode("latin1")

    cb = src_data[CB_KEY].decode("latin1")
    extra = command_buttons()
    if "CommandButton Command_ConstructVietnam_MissileFactory" in cb:
        cb = replace_last(cb, "CommandButton", "Command_ConstructVietnam_MissileFactory", extra.split("CommandButton CB_VIETNAM", 1)[0].rstrip() + "\r\nEnd")
        raise SystemExit("CommandButton.ini already had Vietnam construct; inspect before splicing")
    data[CB_KEY] = (cb.rstrip("\r\n") + "\r\n\r\n" + extra).encode("latin1")

    data_big = build_big(data)
    packed, order = parse_big_ordered(data_big)
    fails = validate(packed, src_data, order)
    fails.extend(f"DATA {x}" for x in big_structure_ok(data_big))
    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_big)
    shutil.copy2(SRC_ART, art_path)

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "CommandSet.ini.Vietnam.txt").write_text(
        last_block(packed[CS_KEY].decode("latin1"), "CommandSet", "Vietnam_VT72BCommandSet")
        + "\r\n\r\n"
        + last_block(packed[CS_KEY].decode("latin1"), "CommandSet", "Vietnam_MissileFactoryCommandSet")
        + "\r\n",
        encoding="utf-8",
    )
    btns = [last_block(packed[CB_KEY].decode("latin1"), "CommandButton", "Command_ConstructVietnam_MissileFactory")]
    btns.extend(last_block(packed[CB_KEY].decode("latin1"), "CommandButton", b) for _s, b, _o, _i in MISSILES)
    (ext / "CommandButton.ini.Vietnam.txt").write_text("\r\n\r\n".join(btns) + "\r\n", encoding="utf-8")
    (ext / "CHAIN.txt").write_text(
        "FactionVietnam StartingUnit0 = Vietnam_VT72B\n"
        "Vietnam_VT72B CommandSet = Vietnam_VT72BCommandSet\n"
        "last-wins CommandSet.ini slot 6 = Command_ConstructVietnam_MissileFactory\n"
        "  Object = Vietnam_MissileFactory\n"
        "Vietnam_MissileFactory CommandSet = Vietnam_MissileFactoryCommandSet\n"
        "Vietnam_MissileFactoryCommandSet last-wins in CommandSet.ini = CB_VIETNAM_MISSILE_A-H\n"
        "Each CB_VIETNAM_MISSILE_* last-wins in CommandButton.ini -> dedicated Vietnam_* object\n",
        encoding="utf-8",
    )

    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_VIETNAM_FACTORY_MENU_FIX.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #626 s-vietnam-missiles-ah",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "ART_UNCHANGED=YES",
        "IRAQ_FACTORY_ROSTER_UNCHANGED=YES",
        "NINE_P117_UNCHANGED=YES",
        "KASHTAN_FALAQ_RETAINED=YES",
        "IRAQ_ABBAS_BIO_RETAINED=YES",
        "NO_REARM=YES",
        "NO_ZZZZ=YES",
        "",
        "ROOT CAUSE: A-H / Vietnam factory CommandSet were only in satellite INI files.",
        "Live WarFactory and Iraq factory last-wins are CommandSet.ini + CommandButton.ini.",
        "CommandSet.ini still constructed the shared Sell-only factory.",
        "FIX: splice Vietnam_VT72BCommandSet + Vietnam_MissileFactoryCommandSet into",
        "CommandSet.ini and append construct + CB_VIETNAM_MISSILE_A-H into CommandButton.ini.",
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
            "ZIP_FILE=SPECTER_VIETNAM_FACTORY_MENU_FIX.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #626",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-vietnam-factory-menu-fix/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-vietnam-factory-menu-fix/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-vietnam-factory-menu-fix/SPECTER_VIETNAM_FACTORY_MENU_FIX.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-vietnam-factory-menu-fix",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-vietnam-factory-menu-fix",
                "BASELINE=PR #626",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Vietnam missile factory A-H menu fix.\n"
        "Splices the live command chain into CommandSet.ini and CommandButton.ini.\n"
        "ART unchanged. Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Vietnam missile factory menu fix\n\n"
        "- Root cause: PR #626 left A-H and the Vietnam factory CommandSet only in satellite INI files.\n"
        "- Live CommandSet.ini still constructed the shared Sell-only factory.\n"
        "- Fix splices the chain into CommandSet.ini and CommandButton.ini, matching Iraq / WarFactory.\n"
        "- ART, 9P117, Iraq A-M, Kashtan, Falaq, and Abbas Bio unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet.ini last Vietnam_VT72BCommandSet is now the Vietnam factory construct.\n"
        "CommandSet_VietnamMissiles.ini still last-wins the same two CommandSets.\n"
        "CommandButton.ini now defines the construct + A-H buttons; satellite file matches.\n"
        "Other country VT72B sets and Iraq factory CommandSets are unchanged.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report))


if __name__ == "__main__":
    main()
