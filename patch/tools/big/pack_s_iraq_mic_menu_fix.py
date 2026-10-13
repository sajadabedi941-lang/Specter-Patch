#!/usr/bin/env python3
"""Fix Iraq M.I.C. in-game menu by writing the 14 copies into live catalogs.

PR #664 put the roster only in CommandSet_ZZZZ_* / CommandButton_ZZZZ_*.
Packed CommandSet.ini still has the old Iraqi MIC production/upgrade menu
(Karrar-2, B340, Fahad-3, Abbas/Hussien/S-8/BMP/Tier upgrades). That live
catalog is what the game shows.

Baseline: SPECTER_IRAQ_MIC_RADAR_AD (PR #664) packed DATA + ART.
ART is copied byte-identical.

Established SPECTER pattern (SK/China/Russia missile packers):
  Live catalogs: CommandSet.ini, CommandButton.ini. No ZZZZ-only menus.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_iraq_mic_radar_ad as rad  # noqa: E402
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MIC_RADAR_AD/_SPEC_DATA_ONE.big"
SRC_ART1 = ROOT / "patch/Release/SPECTER_IRAQ_MIC_RADAR_AD/_SPEC_ART_ONE.big"
SRC_ART2 = ROOT / "patch/Release/SPECTER_IRAQ_MIC_RADAR_AD/_SPEC_ART_TWO.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MIC_MENU_FIX"
INSTALLER = ROOT / "patch/tools/installer"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "50867f319262f646d32583ffcf98d2c8fb51e1156fa2035ed2a3ea061bb9ff41"
SIZE_DATA_SRC = 370866479
SHA_ART1_SRC = rad.SHA_ART1_SRC
SIZE_ART1_SRC = rad.SIZE_ART1_SRC
SHA_ART2_SRC = rad.SHA_ART2_SRC
SIZE_ART2_SRC = rad.SIZE_ART2_SRC
SAGE_SAFE = 2147483648

CS_INI = r"Data\INI\CommandSet.ini"
CB_INI = r"Data\INI\CommandButton.ini"
CS_ZZZZ = rad.CS_KEY
CB_ZZZZ = rad.CB_KEY
OBJ_KEY = rad.OBJ_KEY
TOWF_KEY = rad.TOWF_KEY
EMPTY_CS_KEY = rad.EMPTY_CS_KEY
KARRAR_KEY = rad.KARRAR_KEY
MIC_OBJ_KEY = rad.MIC_OBJ_KEY
WF_OBJ_KEY = rad.WF_OBJ_KEY
AA_WF_KEY = rad.AA_WF_KEY

MIC_CS_NAMES = rad.MIC_CS_NAMES
WF_CS_NAME = rad.WF_CS_NAME
IRAQ_DOZER_CS = rad.IRAQ_DOZER_CS
MIC_CONSTRUCT = rad.MIC_CONSTRUCT
SELL = rad.SELL
COPIES = rad.COPIES
OLD_IRAQI = (
    "Command_UpgradeAbbasResearchProgram",
    "Command_ConstructIraq_Karrar2",
    "Command_Upgrade_Iraq_BMP-2M2",
    "Command_ConstructIraqVehicleB340",
    "Command_ConstructIraqVehicleFahad3",
    "Command_UpgradeHussienResearchProgram",
    "Command_UpgradeS-8Rockets",
    "Command_Upgrade_Iraq_BMP-1M3",
    "Command_Irq_Tier1",
    "Command_Irq_Tier2",
    "Command_Irq_Tier3",
    "Command_UpgradeMi35Mk3",
    "Command_UpgradeKab500",
    "Command_Upgrade_Iraq_BMP-2M2",
)

FROZEN_SOURCE = [
    r"Data\INI\Object\Specter\Israel Defense Forces\Airdefense\Arrow.ini",
    r"Data\INI\Object\Specter\Israel Defense Forces\Airdefense\AN_TPY2.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\92N6R.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\S400.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\Pantsir.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Wheeled\Krasukha-4.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\96L6TSP.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\S500.ini",
    r"Data\INI\Object\Specter\PLA\AirDefense\HQ9B.ini",
    r"Data\INI\Object\Specter\PLA\AirDefense\HT233.ini",
    r"Data\INI\Object\Specter\NATO\Airdefense\TRML4D.ini",
    r"Data\INI\Object\Specter\NATO\Airdefense\IRIST_SLX.ini",
    r"Data\INI\Object\Specter\United States Of America\AirDefense\US_AN_TPY2.ini",
    r"Data\INI\Object\Specter\United States Of America\AirDefense\US_M1120.ini",
    MIC_OBJ_KEY,
    WF_OBJ_KEY,
    AA_WF_KEY,
    KARRAR_KEY,
    OBJ_KEY,
]


def last_from(order, files, kind, name):
    return sk.last_block_from_files(order, files, kind, name)


def field(block: str, key: str) -> str:
    return sk.field(block, key)


def sha256_path(path: Path) -> str:
    return rad.sha256_path(path)


def slot_map(block: str) -> dict[str, str]:
    return rad.slot_map(block)


def mic_commandset(name: str) -> str:
    lines = [f"CommandSet {name}"]
    for item in COPIES:
        lines.append(f"  {item['slot']} = {item['cmd']}")
    lines.append(f"  15 = {SELL}")
    lines.append("End")
    return "\n".join(lines)


def wf_t3_commandset() -> str:
    return "\n".join(
        [
            f"CommandSet {WF_CS_NAME}",
            "  1 = Command_ConstructIraq_T-72",
            "  2 = Command_ConstructIraq_BMP-1",
            "  3 = Command_ConstructIraq_BMP-2",
            "  4 = Command_ConstructIraq_BTR-90",
            "  5 = Command_ConstructIraq_2S1",
            "  6 = Command_ConstructIraq_Sam8",
            "  7 = Command_ConstructIraq_AssadBabel-2",
            "  8 = Command_ConstructIraq_SA-6",
            "  9 = Command_ConstructIraqVehicleB340",
            "  10 = Command_ConstructIraq_Karrar2",
            "  11 = Command_ConstructIraqVehicleRoland3K",
            "  12 = Command_ConstructIraqVehicleFahad3",
            "  14 = Command_Sell",
            "End",
        ]
    )


def expected_mic_slots() -> dict[str, str]:
    slots = {item["slot"]: item["cmd"] for item in COPIES}
    slots["15"] = SELL
    return slots


def catalog_block(text: str, kind: str, name: str) -> str:
    return sk.last_block(text, kind, name)


def ensure_buttons(cb_text: str) -> str:
    missing = []
    for item in COPIES:
        blk = catalog_block(cb_text, "CommandButton", item["cmd"])
        if not blk:
            missing.append(rad.make_button(item).rstrip() + "\n")
            continue
        if field(blk, "Object") != item["copy"] or field(blk, "Command") != "UNIT_BUILD":
            cb_text = sk.replace_last(cb_text, "CommandButton", item["cmd"], rad.make_button(item).rstrip())
    if missing:
        if not cb_text.endswith("\n"):
            cb_text += "\n"
        cb_text += "\n" + "\n".join(missing)
    return cb_text


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_IRAQ_MIC_RADAR_AD")
    if sha256_path(SRC_ART1) != SHA_ART1_SRC or SRC_ART1.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE baseline mismatch")
    if sha256_path(SRC_ART2) != SHA_ART2_SRC or SRC_ART2.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO baseline mismatch")

    files, order = sk.parse_big_ordered(SRC_DATA.read_bytes())
    original = dict(files)

    cs_text = files[CS_INI].decode("latin1")
    live_before = catalog_block(cs_text, "CommandSet", "Iraq_MICCommandSet")
    if "Command_ConstructIraq_Karrar2" not in live_before:
        raise SystemExit("packed CommandSet.ini no longer has the old MIC menu to replace")
    if "Command_ConstructIraq_MIC_Arrow" in live_before:
        raise SystemExit("CommandSet.ini already has the 14-copy menu")

    for name in MIC_CS_NAMES:
        cs_text = sk.replace_last(cs_text, "CommandSet", name, mic_commandset(name))
    cs_text = sk.replace_last(cs_text, "CommandSet", WF_CS_NAME, wf_t3_commandset())
    files[CS_INI] = sk.to_crlf(cs_text.replace("\r\n", "\n"))

    cb_text = files[CB_INI].decode("latin1")
    files[CB_INI] = sk.to_crlf(ensure_buttons(cb_text.replace("\r\n", "\n")))

    files[CS_ZZZZ] = sk.to_crlf("\n".join(mic_commandset(n) + "\n" for n in MIC_CS_NAMES) + "\n")
    files[CB_ZZZZ] = sk.to_crlf("\n".join(rad.make_button(item) for item in COPIES) + "\n")

    for key in FROZEN_SOURCE:
        if files.get(key) != original.get(key):
            raise SystemExit(f"frozen mutated: {key}")
    for item in COPIES:
        if original.get(item["src_file"] if "src_file" in item else ""):
            pass

    data_big = sk.build_big(files)
    packed, packed_order = sk.parse_big_ordered(data_big)
    fails = []
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))

    live_cs = packed[CS_INI].decode("latin1")
    live_cb = packed[CB_INI].decode("latin1")
    expect = expected_mic_slots()

    for name in MIC_CS_NAMES:
        catalog = slot_map(catalog_block(live_cs, "CommandSet", name))
        src, packed_blk = last_from(packed_order, packed, "CommandSet", name)
        packed_slots = slot_map(packed_blk)
        if catalog != expect:
            fails.append(f"LIVE {name} {catalog}")
        if packed_slots != expect:
            fails.append(f"PACKED {name} {packed_slots} from {src}")
        if catalog.get("14") != "Command_ConstructIraq_MIC_THAAD":
            fails.append(f"{name} slot 14 is not THAAD")
        if catalog.get("15") != SELL:
            fails.append(f"{name} slot 15 is not Sell")
        for old in OLD_IRAQI:
            if old in catalog_block(live_cs, "CommandSet", name):
                fails.append(f"LIVE {name} still has {old}")
            if old in (packed_blk or ""):
                fails.append(f"PACKED {name} still has {old}")

    live_t3 = slot_map(catalog_block(live_cs, "CommandSet", WF_CS_NAME))
    src_t3, packed_t3 = last_from(packed_order, packed, "CommandSet", WF_CS_NAME)
    packed_t3_slots = slot_map(packed_t3)
    if live_t3.get("9") != "Command_ConstructIraqVehicleB340":
        fails.append(f"LIVE T3 missing B340 {live_t3}")
    if live_t3.get("10") != "Command_ConstructIraq_Karrar2":
        fails.append("LIVE T3 missing Karrar2")
    if live_t3.get("12") != "Command_ConstructIraqVehicleFahad3":
        fails.append("LIVE T3 missing Fahad3")
    if packed_t3_slots.get("9") != "Command_ConstructIraqVehicleB340":
        fails.append(f"PACKED T3 last-wins {src_t3} missing B340")

    src_dozer, dozer = last_from(packed_order, packed, "CommandSet", IRAQ_DOZER_CS)
    dozer_slots = slot_map(dozer)
    if dozer_slots.get("6") != MIC_CONSTRUCT:
        fails.append(f"dozer slot 6 {dozer_slots.get('6')}")
    _, construct = last_from(packed_order, packed, "CommandButton", MIC_CONSTRUCT)
    if field(construct, "Object") != "Iraq_MIC":
        fails.append(f"dozer construct object {field(construct, 'Object')}")
    src_mic, mic = last_from(packed_order, packed, "Object", "Iraq_MIC")
    if field(mic, "CommandSet") != "Iraq_MICCommandSet":
        fails.append(f"Iraq_MIC CommandSet {field(mic, 'CommandSet')}")
    if src_mic != MIC_OBJ_KEY:
        fails.append(f"Iraq_MIC last-wins {src_mic}")
    if rad.prereq_has_objects(mic):
        fails.append("Iraq_MIC regained prerequisites")
    if "CommandSetUpgrade" in mic:
        fails.append("Iraq_MIC gained CommandSetUpgrade")

    src_wf, wf = last_from(packed_order, packed, "Object", "Iraq_WarFactory_T")
    if field(wf, "CommandSet") != WF_CS_NAME:
        fails.append("Iraq_WarFactory_T CommandSet changed")
    src_karrar, karrar = last_from(packed_order, packed, "Object", "Iraq_Karrar2")
    if rad.prereq_has_objects(karrar):
        fails.append("Iraq_Karrar2 regained prerequisites")

    table = ["slot|live_cs_cmd|live_button|target|cost|button_image|mapped|old_iraqi_absent"]
    for item in COPIES:
        live_cmd = catalog.get(item["slot"]) if False else slot_map(
            catalog_block(live_cs, "CommandSet", "Iraq_MICCommandSet")
        ).get(item["slot"])
        live_btn = catalog_block(live_cb, "CommandButton", item["cmd"])
        packed_btn_src, packed_btn = last_from(packed_order, packed, "CommandButton", item["cmd"])
        src_obj, obj = last_from(packed_order, packed, "Object", item["copy"])
        img_src, img = last_from(packed_order, packed, "MappedImage", item["button"])
        old_absent = live_cmd == item["cmd"] and all(
            old not in (catalog_block(live_cs, "CommandSet", "Iraq_MICCommandSet") or "")
            for old in OLD_IRAQI
        )
        if live_cmd != item["cmd"]:
            fails.append(f"LIVE slot {item['slot']} {live_cmd}")
        if not live_btn:
            fails.append(f"LIVE CommandButton.ini missing {item['cmd']}")
        if field(live_btn, "Object") != item["copy"]:
            fails.append(f"LIVE {item['cmd']} -> {field(live_btn, 'Object')}")
        if field(live_btn, "Command") != "UNIT_BUILD":
            fails.append(f"LIVE {item['cmd']} not UNIT_BUILD")
        if field(live_btn, "ButtonImage") != item["button"]:
            fails.append(f"LIVE {item['cmd']} art {field(live_btn, 'ButtonImage')}")
        if field(packed_btn, "Object") != item["copy"]:
            fails.append(f"PACKED {item['cmd']} -> {field(packed_btn, 'Object')}")
        if field(obj, "BuildCost") != item["cost"]:
            fails.append(f"{item['copy']} cost {field(obj, 'BuildCost')}")
        if field(obj, "Side") != "Iraq":
            fails.append(f"{item['copy']} Side {field(obj, 'Side')}")
        if not img:
            fails.append(f"MappedImage missing {item['button']}")
        osrc, oblk = last_from(packed_order, packed, "Object", item["source"])
        orig_src, orig_blk = last_from(order, original, "Object", item["source"])
        if osrc != orig_src or oblk != orig_blk:
            fails.append(f"source mutated {item['source']}")
        csrc, cblk = last_from(packed_order, packed, "CommandButton", item["src_cmd"])
        orig_c, orig_cblk = last_from(order, original, "CommandButton", item["src_cmd"])
        if field(cblk, "Object") != item["source"]:
            fails.append(f"{item['src_cmd']} retargeted")
        cssrc, csblk = last_from(packed_order, packed, "CommandSet", item["src_cs"])
        orig_cs, orig_csblk = last_from(order, original, "CommandSet", item["src_cs"])
        if item["src_cmd"] not in (csblk or ""):
            fails.append(f"{item['src_cs']} lost {item['src_cmd']}")
        table.append(
            f"{item['slot']}|{live_cmd}|{item['cmd']}|{item['copy']}|{item['cost']}|"
            f"{item['button']}|{field(img, 'Texture') or 'MISSING'}|"
            f"{'YES' if old_absent else 'NO'}"
        )

    live_dozer = catalog_block(live_cs, "CommandSet", IRAQ_DOZER_CS)
    orig_dozer = catalog_block(original[CS_INI].decode("latin1"), "CommandSet", IRAQ_DOZER_CS)
    if slot_map(live_dozer) != slot_map(orig_dozer):
        fails.append("Iraq dozer CommandSet.ini mutated beyond MIC work")

    aa_src, aa = last_from(packed_order, packed, "Object", "ArabicArmy_WarFactory")
    if rad.prereq_block(aa) and "Iraq_" in rad.prereq_block(aa):
        fails.append("Arabic Alliance War Factory gained Iraq prereq")

    allowed = {CS_INI, CB_INI, CS_ZZZZ, CB_ZZZZ}
    for key in original:
        if key in allowed:
            continue
        if packed.get(key) != original[key]:
            fails.append(f"unrelated mutated {key}")

    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art1_path = OUT / "_SPEC_ART_ONE.big"
    art2_path = OUT / "_SPEC_ART_TWO.big"
    data_path.write_bytes(data_big)
    shutil.copy2(SRC_ART1, art1_path)
    shutil.copy2(SRC_ART2, art2_path)

    # Do not overwrite the repo CommandSet.ini / CommandButton.ini catalogs
    # with the full packed BIG copies. Those live catalogs are larger last-wins
    # snapshots; only the packed BIG is the install artifact.
    (LOOSE / "CommandSet_ZZZZ_IraqMicToWfRadarAd.ini").write_bytes(files[CS_ZZZZ])
    (LOOSE / "CommandButton_ZZZZ_IraqMicRadarAd.ini").write_bytes(files[CB_ZZZZ])

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "CommandSet.ini.Iraq_MICCommandSet.ini").write_text(
        catalog_block(live_cs, "CommandSet", "Iraq_MICCommandSet") + "\n", encoding="utf-8"
    )
    (ext / "CommandSet.ini.Iraq_WarFactoryCommandSet_T3.ini").write_text(
        catalog_block(live_cs, "CommandSet", WF_CS_NAME) + "\n", encoding="utf-8"
    )
    (ext / "SLOT_TABLE.txt").write_text("\n".join(table) + "\n", encoding="utf-8")
    (ext / "ROOT_CAUSE.txt").write_text(
        "PR #664 last-wins overlay was CommandSet_ZZZZ_IraqMicToWfRadarAd.ini. "
        "Packed CommandSet.ini still defined Iraq_MICCommandSet as the old Iraqi "
        "upgrade/production menu (Karrar-2, B340, Fahad-3, Abbas/Hussien/S-8/"
        "BMP/Tier). SPECTER live catalogs are CommandSet.ini and CommandButton.ini. "
        "The in-game MIC menu matched CommandSet.ini, not the ZZZZ sidecar.\n",
        encoding="utf-8",
    )

    (OUT / "INSTALL.txt").write_text(
        "\n".join(
            [
                "SPECTER IRAQ M.I.C. MENU FIX — INSTALL",
                "",
                "Keep the split ART arrangement. Do not recombine ART.",
                "Place all three uncompressed BIGs next to generals.exe:",
                "  _SPEC_DATA_ONE.big",
                "  _SPEC_ART_ONE.big",
                "  _SPEC_ART_TWO.big",
                "",
                "Zero Hour auto-loads every *.big in that folder.",
                "Each .big must start with BIGF. Do not install gzip as .big.",
                "Replace any older SPECTER_IRAQ_MIC_RADAR_AD DATA file.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "Live catalog CommandSet.ini now owns Iraq_MICCommandSet slots 1-14 "
        "(dedicated radar/AD copies) and slot 15 Sell. War Factory T3 live "
        "catalog keeps B340, Karrar-2, Fahad-3. RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    zip_path = OUT / "SPECTER_IRAQ_MIC_MENU_FIX.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "_SPEC_ART_TWO.big",
            "INSTALL.txt",
            "README.txt",
            "Launch_Specter.bat",
            "Install_SpecterPatch.bat",
        ):
            zf.write(OUT / name, name)

    if sha256_path(art1_path) != SHA_ART1_SRC or art1_path.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE copy is not byte-identical")
    if sha256_path(art2_path) != SHA_ART2_SRC or art2_path.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO copy is not byte-identical")
    if art1_path.stat().st_size >= SAGE_SAFE or art2_path.stat().st_size >= SAGE_SAFE:
        raise SystemExit("ART archive exceeds SAGE 2GiB signed offset limit")

    data_sha = sha256_path(data_path)
    art1_sha = sha256_path(art1_path)
    art2_sha = sha256_path(art2_path)
    zip_sha = sha256_path(zip_path)
    tag = "s-iraq-mic-menu-fix"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/" + tag
    )
    report = "\n".join(
        [
            "STATIC VALIDATION: PASS",
            "RUNTIME_TEST=NOT RUN",
            "BASELINE: PR #664 SPECTER_IRAQ_MIC_RADAR_AD",
            "ROOT_CAUSE=LIVE_CATALOG_CommandSet.ini_STILL_HAD_OLD_IRAQI_MIC_MENU",
            "LIVE_CATALOG_PATCHED=CommandSet.ini+CommandButton.ini",
            "ART_ONE_UNCHANGED=YES",
            "ART_TWO_UNCHANGED=YES",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_ONE_SIZE={art1_path.stat().st_size}",
            f"ART_ONE_SHA256={art1_sha}",
            f"ART_TWO_SIZE={art2_path.stat().st_size}",
            f"ART_TWO_SHA256={art2_sha}",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            f"CHANGED_PACKED_FILES={CS_INI};{CB_INI};{CS_ZZZZ};{CB_ZZZZ}",
            "MIC_LIVE_SLOTS=1-14_COPIES_SELL_15",
            "WF_T3_LIVE_TRANSFER=YES",
            "KARRAR2_MIC_PREREQ=REMOVED",
            "MIC_START_GAME_PRESERVED=YES",
            "SOURCE_MENUS_PRESERVED=YES",
            "ART_CHANGED=NO",
            "RUNTIME_TEST=NOT RUN",
            "",
            *table,
            "",
        ]
    )
    (OUT / "VALIDATE_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "\n".join(
            [
                "DATA_CHANGED=YES",
                "ART_CHANGED=NO",
                f"DATA_SIZE={data_path.stat().st_size}",
                f"DATA_SHA256={data_sha}",
                f"ART_ONE_SIZE={art1_path.stat().st_size}",
                f"ART_ONE_SHA256={art1_sha}",
                f"ART_TWO_SIZE={art2_path.stat().st_size}",
                f"ART_TWO_SHA256={art2_sha}",
                "ZIP_FILE=SPECTER_IRAQ_MIC_MENU_FIX.zip",
                f"ZIP_SIZE={zip_path.stat().st_size}",
                f"ZIP_SHA256={zip_sha}",
                "BASELINE=PR #664",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA:",
                f"  {rel_base}/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART textures (unchanged):",
                f"  {rel_base}/_SPEC_ART_ONE.big",
                f"  SIZE={art1_path.stat().st_size}",
                f"  SHA256={art1_sha}",
                "",
                "ART models (unchanged):",
                f"  {rel_base}/_SPEC_ART_TWO.big",
                f"  SIZE={art2_path.stat().st_size}",
                f"  SHA256={art2_sha}",
                "",
                "ZIP:",
                f"  {rel_base}/SPECTER_IRAQ_MIC_MENU_FIX.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                f"TAG={tag}",
                f"RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/{tag}",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "\n".join(
            [
                "# Iraq M.I.C. live-catalog menu fix",
                "",
                "PR #664 wrote the 14 radar/AD copies only into ZZZZ sidecar INIs.",
                "The live `CommandSet.ini` catalog still showed the old Iraqi MIC",
                "menu. This release writes slots 1-14 + Sell 15 into CommandSet.ini",
                "and the UNIT_BUILD buttons into CommandButton.ini.",
                "",
                "War Factory T3 live catalog now also carries B340 / Karrar-2 /",
                "Fahad-3 so they are not lost when removed from the MIC catalog.",
                "",
                "ART_ONE and ART_TWO are byte-identical to PR #664.",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("PACKED", data_path.stat().st_size, data_sha)
    print("ART_ONE", art1_path.stat().st_size, art1_sha)
    print("ART_TWO", art2_path.stat().st_size, art2_sha)
    print("ZIP", zip_path.stat().st_size, zip_sha)
    print("LIVE MIC")
    print(catalog_block(live_cs, "CommandSet", "Iraq_MICCommandSet"))
    print("LIVE T3")
    print(catalog_block(live_cs, "CommandSet", WF_CS_NAME))
    print("\n".join(table))
    print("STATIC VALIDATION: PASS")
    print("RUNTIME_TEST=NOT RUN")


if __name__ == "__main__":
    main()
