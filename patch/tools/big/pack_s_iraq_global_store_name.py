#!/usr/bin/env python3
"""Rename Iraq Global Store display text and lock BuildCost at 7000.

Baseline packed archives: SPECTER_RADAR_UAV_MIC_ART (PR #667).
ART_ONE / ART_TWO are copied byte-identical.

Iraq_MIC is the existing Global Store / Global Market (Button_GlobalMarket,
dozer slot 6, 14 radar/AD copies + Sell). Do not duplicate the building.

OBJECT:MIC is shared by other countries' MIC buildings, so Iraq_MIC gets a
dedicated DisplayName. ConstructIraq_MIC / ToolTipIraq_MIC are Iraq-only CSF
keys already referenced by Command_ConstructIraq_MIC.
"""
from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_iraq_mic_radar_ad as rad  # noqa: E402
import pack_s_radar_uav_slots as uav  # noqa: E402
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_RADAR_UAV_MIC_ART/_SPEC_DATA_ONE.big"
SRC_ART1 = ROOT / "patch/Release/SPECTER_RADAR_UAV_MIC_ART/_SPEC_ART_ONE.big"
SRC_ART2 = ROOT / "patch/Release/SPECTER_RADAR_UAV_MIC_ART/_SPEC_ART_TWO.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_GLOBAL_STORE_NAME"
INSTALLER = ROOT / "patch/tools/installer"
LOOSE_MIC = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Buildings/Iraq_MIC.ini"

SHA_DATA_SRC = "16fe4be2b4fc8c693b59c3340b996535a26c1c2abc50be62f205ef62145284aa"
SIZE_DATA_SRC = 370921471
SHA_ART1_SRC = "9dc4524ccb44881fcd0149957d2fcce1d378db1483e6c458df67e07c86a86aa8"
SIZE_ART1_SRC = 2144972013
SHA_ART2_SRC = "c2985f5a7bd53ab1a465c30bb85357db05aaa2724d12fabc92492fe12486bf10"
SIZE_ART2_SRC = 307254782
SAGE_SAFE = 2147483648

MIC_OBJ_KEY = rad.MIC_OBJ_KEY
CSF_KEY = sk.CSF_KEY
CB_INI = r"Data\INI\CommandButton.ini"
CS_INI = r"Data\INI\CommandSet.ini"
CS_ZZZZ_UAV = r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini"
CS_MIC_ZZZZ = rad.CS_KEY
CB_MIC_ZZZZ = rad.CB_KEY

DISPLAY_KEY = "OBJECT:IraqGlobalStore"
NAME = "Global Store"
DESC_TITLE = "Global Aerospace Market"
DESC_BODY = (
    "An international marketplace for aviation systems, reconnaissance drones, "
    "radar technology, and air-defense equipment."
)
TIP = f"{DESC_TITLE}\n\n{DESC_BODY}"
COST = "7000"

CSF_MAP = {
    DISPLAY_KEY: NAME,
    "CONTROLBAR:ConstructIraq_MIC": NAME,
    "CONTROLBAR:ToolTipIraq_MIC": TIP,
}

SHARED_MIC_OBJECTS = (
    "Egypt_MIC",
    "India_MIC",
    "Libya_MIC",
    "Pakistan_MIC",
    "SaudiArabia_MIC",
    "SouthAfrica_MIC",
    "Syria_MIC",
    "UAE_MIC",
)

OBJECT_MIC_CSF = "MIC\nIraqi Military Industary Corporation"


def set_field(text: str, key: str, value: str) -> str:
    new, n = re.subn(
        rf"(?m)^(\s*{re.escape(key)}\s*=\s*)\S+",
        rf"\g<1>{value}",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"failed to set {key}")
    return new


def patch_mic(text: str) -> str:
    body = text.replace("\r\n", "\n")
    if re.search(r"(?m)^\s*DisplayName\s*=\s*OBJECT:MIC\s*$", body) is None:
        raise SystemExit("Iraq_MIC DisplayName is not OBJECT:MIC")
    body = set_field(body, "DisplayName", DISPLAY_KEY)
    cost_m = re.search(r"(?m)^\s*BuildCost\s*=\s*(\S+)", body)
    if not cost_m:
        raise SystemExit("Iraq_MIC missing BuildCost")
    if cost_m.group(1) != COST:
        body = set_field(body, "BuildCost", COST)
    return body


def catalog_block(text: str, kind: str, name: str) -> str:
    return sk.last_block(text, kind, name)


def last_from(order, files, kind, name):
    return sk.last_block_from_files(order, files, kind, name)


def field(block: str, key: str) -> str:
    return sk.field(block, key)


def slot_map(block: str) -> dict[str, str]:
    return rad.slot_map(block)


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_RADAR_UAV_MIC_ART")
    if sk.sha256_path(SRC_ART1) != SHA_ART1_SRC or SRC_ART1.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE baseline mismatch")
    if sk.sha256_path(SRC_ART2) != SHA_ART2_SRC or SRC_ART2.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO baseline mismatch")

    files, order = sk.parse_big_ordered(SRC_DATA.read_bytes())
    original = dict(files)

    files[MIC_OBJ_KEY] = sk.to_crlf(patch_mic(files[MIC_OBJ_KEY].decode("latin1")))
    files[CSF_KEY] = sk.csf_upsert(files[CSF_KEY], CSF_MAP)

    data_big = sk.build_big(files)
    packed, packed_order = sk.parse_big_ordered(data_big)
    fails = [f"DATA {x}" for x in sk.big_structure_ok(data_big)]

    src, mic = last_from(packed_order, packed, "Object", "Iraq_MIC")
    orig_src, orig_mic = last_from(order, original, "Object", "Iraq_MIC")
    if src != MIC_OBJ_KEY:
        fails.append(f"Iraq_MIC last-wins {src}")
    if field(mic, "DisplayName") != DISPLAY_KEY:
        fails.append(f"DisplayName {field(mic, 'DisplayName')}")
    if field(mic, "BuildCost") != COST:
        fails.append(f"BuildCost {field(mic, 'BuildCost')}")
    if field(mic, "CommandSet") != "Iraq_MICCommandSet":
        fails.append("Iraq_MIC CommandSet changed")
    if field(mic, "Side") != "Iraq":
        fails.append("Iraq_MIC Side changed")
    if "ModuleTag_Flag_Hs" not in mic or "IQ__IQFlag_HsGM" not in mic:
        fails.append("futuristic Flag_Hs lost")
    if field(mic, "SelectPortrait") != "irq_mic" or field(mic, "ButtonImage") != "irq_mic":
        fails.append("Iraq_MIC portraits changed")
    orig_time = field(orig_mic, "BuildTime")
    if field(mic, "BuildTime") != orig_time:
        fails.append("BuildTime changed")
    orig_kind = field(orig_mic, "KindOf")
    if field(mic, "KindOf") != orig_kind:
        fails.append("KindOf changed")
    stripped = re.sub(
        r"(DisplayName\s*=\s*)\S+",
        r"\1OBJECT:MIC",
        mic.replace("\r\n", "\n"),
        count=1,
    )
    if stripped.strip() != orig_mic.replace("\r\n", "\n").strip():
        fails.append("Iraq_MIC changed beyond DisplayName")

    csf = packed[CSF_KEY]
    if sk.csf_get(csf, DISPLAY_KEY) != NAME:
        fails.append(f"CSF {DISPLAY_KEY}={sk.csf_get(csf, DISPLAY_KEY)!r}")
    if sk.csf_get(csf, "CONTROLBAR:ConstructIraq_MIC") != NAME:
        fails.append("construct label is not Global Store")
    if sk.csf_get(csf, "CONTROLBAR:ToolTipIraq_MIC") != TIP:
        fails.append(f"tooltip {sk.csf_get(csf, 'CONTROLBAR:ToolTipIraq_MIC')!r}")
    if DESC_TITLE not in (sk.csf_get(csf, "CONTROLBAR:ToolTipIraq_MIC") or ""):
        fails.append("tooltip missing Global Aerospace Market title")
    if DESC_BODY not in (sk.csf_get(csf, "CONTROLBAR:ToolTipIraq_MIC") or ""):
        fails.append("tooltip missing marketplace body")
    if sk.csf_get(csf, "OBJECT:MIC") != OBJECT_MIC_CSF:
        fails.append("shared OBJECT:MIC mutated")
    if sk.csf_get(original[CSF_KEY], "OBJECT:MIC") != sk.csf_get(csf, "OBJECT:MIC"):
        fails.append("OBJECT:MIC CSF changed")

    src_btn, btn = last_from(packed_order, packed, "CommandButton", "Command_ConstructIraq_MIC")
    orig_btn_src, orig_btn = last_from(order, original, "CommandButton", "Command_ConstructIraq_MIC")
    if btn != orig_btn:
        fails.append("Command_ConstructIraq_MIC INI mutated")
    if field(btn, "Command") != "DOZER_CONSTRUCT":
        fails.append("construct command changed")
    if field(btn, "Object") != "Iraq_MIC":
        fails.append("construct object changed")
    if field(btn, "ButtonImage") != "Button_GlobalMarket":
        fails.append("construct ButtonImage changed")
    if field(btn, "TextLabel") != "CONTROLBAR:ConstructIraq_MIC":
        fails.append("construct TextLabel changed")
    if field(btn, "DescriptLabel") != "CONTROLBAR:ToolTipIraq_MIC":
        fails.append("construct DescriptLabel changed")

    live_cs = packed[CS_INI].decode("latin1")
    expect_mic = {item["slot"]: item["cmd"] for item in rad.COPIES}
    expect_mic["15"] = rad.SELL
    for name in rad.MIC_CS_NAMES:
        live_mic = slot_map(catalog_block(live_cs, "CommandSet", name))
        packed_mic = slot_map(last_from(packed_order, packed, "CommandSet", name)[1])
        orig_mic = slot_map(last_from(order, original, "CommandSet", name)[1])
        if live_mic != expect_mic or packed_mic != expect_mic or orig_mic != packed_mic:
            fails.append(f"MIC menu mutated {name}")

    orig_t3 = slot_map(last_from(order, original, "CommandSet", rad.WF_CS_NAME)[1])
    packed_t3 = slot_map(last_from(packed_order, packed, "CommandSet", rad.WF_CS_NAME)[1])
    if orig_t3 != packed_t3:
        fails.append("WF T3 mutated")
    if packed_t3.get("9") != "Command_ConstructIraqVehicleB340":
        fails.append("WF T3 lost B340")

    dozer = slot_map(catalog_block(live_cs, "CommandSet", "Iraq_VT72BCommandSet"))
    worker = slot_map(catalog_block(live_cs, "CommandSet", "Iraq_WorkerCommandSet"))
    orig_dozer = slot_map(catalog_block(original[CS_INI].decode("latin1"), "CommandSet", "Iraq_VT72BCommandSet"))
    orig_worker = slot_map(catalog_block(original[CS_INI].decode("latin1"), "CommandSet", "Iraq_WorkerCommandSet"))
    if dozer != orig_dozer or worker != orig_worker:
        fails.append("Iraq construct menus mutated")
    if dozer.get("6") != "Command_ConstructIraq_MIC":
        fails.append("VT72B lost Global Store construct")

    for country in uav.COUNTRIES:
        orig_slots = slot_map(last_from(order, original, "CommandSet", country["cs"])[1])
        packed_slots = slot_map(last_from(packed_order, packed, "CommandSet", country["cs"])[1])
        if orig_slots != packed_slots:
            fails.append(f"UAV CS mutated {country['cs']}")
        for item in uav.COPIES:
            if packed_slots.get(item["slot"]) != item["cmd"]:
                fails.append(f"{country['display']} lost UAV slot {item['slot']}")
            src_btn, uav_btn = last_from(packed_order, packed, "CommandButton", item["cmd"])
            orig_uav_src, orig_uav = last_from(order, original, "CommandButton", item["cmd"])
            if uav_btn != orig_uav:
                fails.append(f"UAV button mutated {item['cmd']}")

    for name in SHARED_MIC_OBJECTS:
        orig_o = last_from(order, original, "Object", name)[1]
        new_o = last_from(packed_order, packed, "Object", name)[1]
        if orig_o != new_o:
            fails.append(f"other MIC mutated {name}")
        if field(new_o, "DisplayName") != "OBJECT:MIC":
            fails.append(f"{name} DisplayName retargeted")

    for item in rad.COPIES:
        orig_b = last_from(order, original, "CommandButton", item["cmd"])[1]
        new_b = last_from(packed_order, packed, "CommandButton", item["cmd"])[1]
        if orig_b != new_b:
            fails.append(f"MIC product button mutated {item['cmd']}")

    allowed = {MIC_OBJ_KEY, CSF_KEY}
    for key in original:
        if key in allowed:
            continue
        if packed.get(key) != original[key]:
            fails.append(f"unrelated DATA mutated {key}")
    if set(packed) != set(original):
        fails.append(f"DATA key set changed {set(packed) ^ set(original)}")

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

    LOOSE_MIC.parent.mkdir(parents=True, exist_ok=True)
    LOOSE_MIC.write_bytes(files[MIC_OBJ_KEY])

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "Iraq_MIC.ini").write_bytes(files[MIC_OBJ_KEY])
    (ext / "NAME_COST_DESC.txt").write_text(
        "\n".join(
            [
                f"OBJECT=Iraq_MIC",
                f"DISPLAY_NAME_KEY={DISPLAY_KEY}",
                f"DISPLAY_NAME={NAME}",
                f"BUILD_COST={COST}",
                f"CONSTRUCT_BUTTON=Command_ConstructIraq_MIC",
                f"CONSTRUCT_LABEL=CONTROLBAR:ConstructIraq_MIC -> {NAME}",
                f"DESCRIPT_LABEL=CONTROLBAR:ToolTipIraq_MIC",
                f"DESCRIPTION_TITLE={DESC_TITLE}",
                f"DESCRIPTION_BODY={DESC_BODY}",
                "SHARED_OBJECT_MIC_UNCHANGED=YES",
                "ART_UNCHANGED=YES",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (OUT / "INSTALL.txt").write_text(
        "\n".join(
            [
                "SPECTER IRAQ GLOBAL STORE NAME — INSTALL",
                "",
                "Keep the split ART arrangement. Do not recombine ART.",
                "Place all three uncompressed BIGs next to generals.exe:",
                "  _SPEC_DATA_ONE.big",
                "  _SPEC_ART_ONE.big",
                "  _SPEC_ART_TWO.big",
                "",
                "Zero Hour auto-loads every *.big in that folder.",
                "Each .big must start with BIGF. Do not install gzip as .big.",
                "Replace SPECTER_RADAR_UAV_MIC_ART DATA. ART is unchanged from PR #667.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "Iraq Global Store (Iraq_MIC) in-game name is Global Store, BuildCost "
        "is 7000, and the construct tooltip is Global Aerospace Market plus the "
        "marketplace description. ART unchanged from PR #667. RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    zip_path = OUT / "SPECTER_IRAQ_GLOBAL_STORE_NAME.zip"
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

    if sk.sha256_path(art1_path) != SHA_ART1_SRC or art1_path.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE copy is not byte-identical")
    if sk.sha256_path(art2_path) != SHA_ART2_SRC or art2_path.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO copy is not byte-identical")
    if art1_path.stat().st_size >= SAGE_SAFE or art2_path.stat().st_size >= SAGE_SAFE:
        raise SystemExit("ART archive exceeds SAGE 2GiB signed offset limit")

    data_sha = sk.sha256_path(data_path)
    art1_sha = sk.sha256_path(art1_path)
    art2_sha = sk.sha256_path(art2_path)
    zip_sha = sk.sha256_path(zip_path)
    tag = "s-iraq-global-store-name"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/" + tag
    )
    prev_art = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/"
        "s-radar-uav-mic-art"
    )
    report = "\n".join(
        [
            "STATIC VALIDATION: PASS",
            "RUNTIME_TEST=NOT RUN",
            "BASELINE: PR #667 SPECTER_RADAR_UAV_MIC_ART",
            "OBJECT=Iraq_MIC (existing Global Store / Global Market; not duplicated)",
            f"DISPLAY_NAME={NAME} via {DISPLAY_KEY}",
            f"BUILD_COST={COST}",
            f"DESCRIPTION_TITLE={DESC_TITLE}",
            f"DESCRIPTION_BODY={DESC_BODY}",
            "CONSTRUCT_BUTTON=Command_ConstructIraq_MIC (INI unchanged)",
            "ART_UNCHANGED=YES",
            "OBJECT_MIC_SHARED_UNCHANGED=YES",
            "MIC_SLOTS_1_14_SELL_15=YES",
            "UAV_SLOTS_9_12_UNCHANGED=YES",
            "WF_T3_UNCHANGED=YES",
            "FLAG_HSGM_UNCHANGED=YES",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_ONE_SIZE={art1_path.stat().st_size}",
            f"ART_ONE_SHA256={art1_sha}",
            f"ART_TWO_SIZE={art2_path.stat().st_size}",
            f"ART_TWO_SHA256={art2_sha}",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "RUNTIME_TEST=NOT RUN",
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
                "ZIP_FILE=SPECTER_IRAQ_GLOBAL_STORE_NAME.zip",
                f"ZIP_SIZE={zip_path.stat().st_size}",
                f"ZIP_SHA256={zip_sha}",
                "BASELINE=PR #667",
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
                "ART textures (unchanged from PR #667 / tag s-radar-uav-mic-art):",
                f"  {prev_art}/_SPEC_ART_ONE.big",
                f"  SIZE={art1_path.stat().st_size}",
                f"  SHA256={art1_sha}",
                "",
                "ART models (unchanged from PR #667 / tag s-radar-uav-mic-art):",
                f"  {prev_art}/_SPEC_ART_TWO.big",
                f"  SIZE={art2_path.stat().st_size}",
                f"  SHA256={art2_sha}",
                "",
                "ZIP:",
                f"  {rel_base}/SPECTER_IRAQ_GLOBAL_STORE_NAME.zip",
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
                "# Iraq Global Store name, cost, and description",
                "",
                "The existing Iraq Global Store building (`Iraq_MIC`) now displays",
                "as **Global Store**, costs **$7,000** (`BuildCost = 7000`), and uses",
                "the Global Aerospace Market construct tooltip describing an",
                "international marketplace for aviation, reconnaissance drones,",
                "radar, and air-defense equipment.",
                "",
                "The building is not duplicated. Production menu, futuristic flag,",
                "and PR #666 / #667 UAV and button art are unchanged.",
                "ART is byte-identical to PR #667.",
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
    print("STATIC VALIDATION: PASS")
    print("RUNTIME_TEST=NOT RUN")


if __name__ == "__main__":
    main()
