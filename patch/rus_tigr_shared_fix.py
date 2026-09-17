#!/usr/bin/env python3
"""Fix Tigr1 crash after the Tigr2 rebuild.

Tigr1 never existed in DATA. Tigr2 was added as a BTR82A clone unlocked
by CommandSetUpgrade on the shared Russia Industrial Complex. The player
path "build Tigr1" then hits a missing Object/CommandButton, or the shared
plant bar has Tigr2-only unlock with no base Tigr unit.

Working pair: RussiaTankBMP3 + RussiaTankBMP3MV in one INI, shared
GenericIFVcommandset, no illegal Prerequisites Upgrade=.

This pack starts from capture DATA and creates both Tigr1 (always
buildable) and Tigr2 (unlocked by Upgrade_Rus_Tigr2).
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import japan_france_roster_01 as jf
from rus_tigr2_rebuild import (
    CS_AFTER,
    CS_LIVE,
    CS_UPGRADE_MODULE,
    insert_after_block,
    insert_building_module,
    insert_cs_button,
    extract_named,
)

SRC_DATA = Path("/workspace/patch/Release/SPECTER_WARFACTORY_CAPTURE_UPDATE/_SPEC_DATA_ONE.big")
EXPECTED_DATA_SHA = "cc0595379e7f255f98170bd4502ed0479b634162739bd206748c86459176552b"
OUT_DIR = Path("/workspace/patch/Release/SPECTER1_RUS_TIGR_SHARED")
REPORT = Path("/workspace/patch/TIGR_SHARED_CRASH_REPORT.txt")

P_UPG = r"Data\INI\Upgrade.ini"
P_BTN = r"Data\INI\CommandButton.ini"
P_CS = r"Data\INI\CommandSet.ini"
P_IC = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\WeaponIndustryPlant.ini"
P_BTR = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\APC\BTR82A.ini"
P_TIGR = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\APC\Tigr.ini"
P_IMG = r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI"

UPGRADE_BLOCK = """Upgrade Upgrade_Rus_Tigr2
  DisplayName        = UPGRADE:SU39
  BuildTime          = 25
  BuildCost          = 3000
  ButtonImage        = rus_btr82
End
"""

BUTTON_UPG = """CommandButton Command_Upgrade_Rus_Tigr2
  Command       = PLAYER_UPGRADE
  Upgrade       = Upgrade_Rus_Tigr2
  ;Options       = OK_FOR_MULTI_SELECT
  TextLabel     = CONTROLBAR:Upgrade_SU39
  ButtonImage   = rus_btr82
  ButtonBorderType        = ACTION ; Identifier for the User as to what kind of button this is
  DescriptLabel           = CONTROLBAR:ToolTipUpgrade_SU39
End
"""

BUTTON_TIGR1 = """CommandButton Command_ConstructRussiaVehicleTigr1
  Command       = UNIT_BUILD
  Object        = RussiaVehicleTigr1
  TextLabel     = CONTROLBAR:ConstructRussiaVehicleBTR82A
  ButtonImage   = rus_btr82
  ButtonBorderType        = BUILD ; Identifier for the User as to what kind of button this is
  DescriptLabel           = CONTROLBAR:ToolTipRussiaVehicleBTR82A
End
"""

BUTTON_TIGR2 = """CommandButton Command_ConstructRussiaVehicleTigr2
  Command       = UNIT_BUILD
  Object        = RussiaVehicleTigr2
  TextLabel     = CONTROLBAR:ConstructRussiaVehicleBTR82A
  ButtonImage   = rus_btr82
  ButtonBorderType        = BUILD ; Identifier for the User as to what kind of button this is
  DescriptLabel           = CONTROLBAR:ToolTipRussiaVehicleBTR82A
End
"""


def clone_btr(btr_text: str, new_name: str) -> str:
    block = jf.extract_object_block(btr_text, "RussiaVehicleBTR82A")
    block = block.replace("Object RussiaVehicleBTR82A", f"Object {new_name}", 1)
    if re.search(r"(?im)^\s*Upgrade\s*=", block):
        raise SystemExit(f"{new_name}: illegal Upgrade =")
    if "WeaponSetUpgrade" in block or "LocomotorSetUpgrade" in block or "MaxHealthUpgrade" in block:
        raise SystemExit(f"{new_name}: inherited crashy upgrade modules")
    return block


def def_exists(packed, kind: str, name: str) -> bool:
    rx = re.compile(rf"(?im)^{kind}\s+{re.escape(name)}\s*$")
    for n, b in packed:
        if n.lower().endswith(".ini") and rx.search(bytes(b).decode("latin1", "replace")):
            return True
    return False


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("unexpected source DATA SHA")
    entries = jf.read_big_list(SRC_DATA)

    leftover = []
    rx = re.compile(r"tigr1|tigr2|rus_tigr|upgrade_rus_tigr|RussiaVehicleTigr", re.I)
    for n, b in entries:
        if rx.search(n) or rx.search(bytes(b).decode("latin1", "replace")):
            leftover.append(n)
    leftover = [n for n in leftover if not n.lower().endswith(".bik")]
    if leftover:
        raise SystemExit(f"capture baseline already has tigr: {leftover}")

    upg = jf.text_of(entries, P_UPG)
    btn = jf.text_of(entries, P_BTN)
    cs = jf.text_of(entries, P_CS)
    ic = jf.text_of(entries, P_IC)
    btr = jf.text_of(entries, P_BTR)
    img = jf.text_of(entries, P_IMG)

    upg = insert_after_block(upg, "Upgrade", "Upgrade_SU39", UPGRADE_BLOCK)
    btn = insert_after_block(btn, "CommandButton", "Command_Upgrade_SU39", BUTTON_UPG)
    btn = insert_after_block(btn, "CommandButton", "Command_ConstructRussiaVehicleBTR82A", BUTTON_TIGR1)
    btn = insert_after_block(btn, "CommandButton", "Command_ConstructRussiaVehicleTigr1", BUTTON_TIGR2)

    cs = insert_cs_button(cs, CS_LIVE, 5, "Command_Upgrade_Rus_Tigr2")
    cs = insert_cs_button(cs, CS_LIVE, 6, "Command_ConstructRussiaVehicleTigr1")
    live = extract_named(cs, "CommandSet", CS_LIVE)
    after = live.replace(f"CommandSet {CS_LIVE}", f"CommandSet {CS_AFTER}", 1)
    wrapped = "CommandSet __WRAP__\nEnd\n" + after
    wrapped = insert_cs_button(wrapped, CS_AFTER, 10, "Command_ConstructRussiaVehicleTigr2")
    after = extract_named(wrapped, "CommandSet", CS_AFTER)
    cs = insert_after_block(cs, "CommandSet", CS_LIVE, after)
    cs = insert_cs_button(cs, "RussiaCommandCenterCommandSet", 11, "Command_ConstructRussiaVehicleTigr1")

    ic = insert_building_module(ic)
    nl = jf.file_nl(btr)
    tigr = jf.to_nl(clone_btr(btr, "RussiaVehicleTigr1").rstrip() + "\n\n" + clone_btr(btr, "RussiaVehicleTigr2"), nl)

    jf.set_text(entries, P_UPG, upg)
    jf.set_text(entries, P_BTN, btn)
    jf.set_text(entries, P_CS, cs)
    jf.set_text(entries, P_IC, ic)
    jf.add_file(entries, P_TIGR, tigr)

    blob = jf.build_big_ordered(entries)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(blob)
    new_sha = hashlib.sha256(blob).hexdigest()

    packed = jf.read_big_list(OUT_DIR / "_SPEC_DATA_ONE.big")
    pbtn = jf.parse_buttons(jf.text_of(packed, P_BTN))
    pcs = jf.parse_commandsets(jf.text_of(packed, P_CS))
    pic = jf.text_of(packed, P_IC)
    ptigr = jf.text_of(packed, P_TIGR)
    pimg = jf.text_of(packed, P_IMG)
    pbtr = jf.text_of(packed, P_BTR)
    pups = jf.text_of(packed, P_UPG)

    t1 = jf.extract_object_block(ptigr, "RussiaVehicleTigr1")
    t2 = jf.extract_object_block(ptigr, "RussiaVehicleTigr2")
    btr_block = jf.extract_object_block(pbtr, "RussiaVehicleBTR82A")

    def nameless(block: str) -> str:
        return re.sub(r"(?im)^Object\s+\S+", "Object __NAME__", block, count=1).rstrip() + "\n"

    def cs_buttons(name: str) -> list[str]:
        return re.findall(r"(?im)^\s*\d+\s*=\s*(\S+)", pcs.get(name, ""))

    live_btns = cs_buttons(CS_LIVE)
    after_btns = cs_buttons(CS_AFTER)
    cc_btns = cs_buttons("RussiaCommandCenterCommandSet")

    no_illegal = not re.search(r"(?im)^\s*Upgrade\s*=", t1 + t2)
    no_veh_mod = not re.search(
        r"(?im)Behavior\s*=\s*(WeaponSetUpgrade|LocomotorSetUpgrade|MaxHealthUpgrade|CommandSetUpgrade)",
        t1 + t2,
    )
    csu = "ModuleTag_Tigr2CS" in pic and CS_AFTER in pic
    no_img = not re.search(r"(?im)^MappedImage\s+upgrade_rus_tigr2\s*$", pimg)
    no_t = all("Tigr" not in pcs.get(n, "") for n in (
        "RussiaWeaponIndustryPlantCommandSet_T",
        "RussiaWeaponIndustryPlantCommandSet_T1",
        "RussiaWeaponIndustryPlantCommandSet_T2",
        "RussiaWarFactoryCommandSet",
    ))
    refs_ok = all(
        [
            def_exists(packed, "Weapon", "30mm_2A72_dualfeed"),
            def_exists(packed, "Weapon", "7_62mm_PKT_Coaxial"),
            def_exists(packed, "Armor", "BTR90Armor"),
            def_exists(packed, "Locomotor", "TCD_510diesel"),
            def_exists(packed, "Object", "RussiaMechanizedInfantry"),
            def_exists(packed, "CommandSet", "GenericIFVcommandset"),
            def_exists(packed, "MappedImage", "rus_btr82"),
        ]
    )
    art_path = Path("/workspace/patch/Release/SPECTER1_BUILDING_FLAGS_01/_SPEC_ART_ONE.big")
    art_names = {jf.norm(n).lower() for n, _ in jf.read_big_list(art_path)}
    art_ok = r"art\w3d\rus_btr90.w3d" in art_names

    src_entries = jf.read_big_list(SRC_DATA)
    base = {jf.norm(n).lower(): bytes(b) for n, b in src_entries}
    packed_map = {jf.norm(n).lower(): (n, bytes(b)) for n, b in packed}
    changed = [packed_map[k][0] for k, old in base.items() if k in packed_map and packed_map[k][1] != old]
    added = [n for n, b in packed if jf.norm(n).lower() not in base]
    allowed_mod = {jf.norm(x).lower() for x in (P_UPG, P_BTN, P_CS, P_IC)}
    allowed_add = {jf.norm(P_TIGR).lower()}
    if {jf.norm(c).lower() for c in changed} != allowed_mod:
        raise SystemExit(f"unexpected DATA mods: {changed}")
    if {jf.norm(a).lower() for a in added} != allowed_add:
        raise SystemExit(f"unexpected DATA adds: {added}")
    if pcs.get("RussiaWarFactoryCommandSet") != jf.parse_commandsets(jf.text_of(src_entries, P_CS)).get("RussiaWarFactoryCommandSet"):
        raise SystemExit("WF changed")

    tigr1_ok = (
        "Command_ConstructRussiaVehicleTigr1" in live_btns
        and "Command_ConstructRussiaVehicleTigr1" in after_btns
        and "Command_ConstructRussiaVehicleTigr1" in cc_btns
        and "UNIT_BUILD" in pbtn.get("Command_ConstructRussiaVehicleTigr1", "")
        and "RussiaVehicleTigr1" in pbtn["Command_ConstructRussiaVehicleTigr1"]
        and nameless(t1) == nameless(btr_block)
        and re.search(r"(?im)^\s*Side\s*=\s*Russia\s*$", t1)
    )
    tigr2_ok = (
        "Command_Upgrade_Rus_Tigr2" in live_btns
        and "Command_ConstructRussiaVehicleTigr2" not in live_btns
        and "Command_ConstructRussiaVehicleTigr2" in after_btns
        and "UNIT_BUILD" in pbtn.get("Command_ConstructRussiaVehicleTigr2", "")
        and nameless(t2) == nameless(btr_block)
        and bool(re.search(r"(?im)^Upgrade\s+Upgrade_Rus_Tigr2\s*$", pups))
        and csu
    )
    checks = {
        "Tigr1 object exact BTR82A clone": nameless(t1) == nameless(btr_block),
        "Tigr2 object exact BTR82A clone": nameless(t2) == nameless(btr_block),
        "Tigr1 on live plant CS": "Command_ConstructRussiaVehicleTigr1" in live_btns,
        "Tigr2 NOT on live plant CS": "Command_ConstructRussiaVehicleTigr2" not in live_btns,
        "Tigr1+Tigr2 on post-upgrade CS": tigr1_ok and "Command_ConstructRussiaVehicleTigr2" in after_btns,
        "Tigr1 on Command Center": "Command_ConstructRussiaVehicleTigr1" in cc_btns,
        "Shared Upgrade_Rus_Tigr2 SU39-style": "PLAYER_UPGRADE" in pbtn.get("Command_Upgrade_Rus_Tigr2", ""),
        "CommandSetUpgrade on plant": csu,
        "No illegal Prerequisites Upgrade": no_illegal,
        "No vehicle WeaponSetUpgrade modules": no_veh_mod,
        "No stub MappedImage": no_img,
        "No Tigr on _T/WF": no_t,
        "Weapon/Armor/Locomotor/payload": refs_ok,
        "ART RUS_BTR90": art_ok,
        "BTR82A.ini unchanged": bytes(jf.raw_of(packed, P_BTR)) == bytes(jf.raw_of(src_entries, P_BTR)),
    }
    working = all(checks.values()) and tigr1_ok and tigr2_ok
    check_lines = "\n".join(f"  {k} = {'PASS' if v else 'FAIL'}" for k, v in checks.items())

    report = f"""TIGR_SHARED_CRASH_REPORT

TIGR1 = {'PASS' if tigr1_ok and working else 'FAIL'}
TIGR2 = {'PASS' if tigr2_ok and working else 'FAIL'}

Crash source:
  After the Tigr2-only rebuild, the crash moved to Tigr1 because Tigr1
  never existed. Packed DATA had RussiaVehicleTigr2 (BTR82A clone) and
  Upgrade_Rus_Tigr2, but ZERO RussiaVehicleTigr1 / rus_tigr1 /
  Command_ConstructRussiaVehicleTigr1. The two units are one Tigr family
  on the shared Russia Industrial Complex. Building Tigr1 resolved a
  missing object. Tigr2 sitting alone on a CommandSetUpgrade of that
  shared plant left the base Tigr slot empty.

  Same illegal field as the Tigr2 crash (Prerequisites Upgrade=) was NOT
  present on Tigr1 because Tigr1 had no object at all.

Broken reference:
  Missing Object RussiaVehicleTigr1
  Missing CommandButton Command_ConstructRussiaVehicleTigr1
  Live RussiaIndsturialComplexCommandSet had no Tigr1 UNIT_BUILD
  Shared plant CommandSetUpgrade only revealed Tigr2

Affected units:
  RussiaVehicleTigr1 (missing)
  RussiaVehicleTigr2 (present, BTR82A clone, no extra modules)
  RussiaIndustrialComplex (shared CommandSetUpgrade)

Fix applied:
  Rebuilt both from capture DATA using the working BMP3 + BMP3MV pair:
  - Object RussiaVehicleTigr1 and RussiaVehicleTigr2 in Tigr.ini
    (name-only BTR82A clones, Side=Russia, GenericIFVcommandset,
    weapons 30mm_2A72_dualfeed / 7_62mm_PKT_Coaxial, Armor BTR90Armor,
    Locomotor TCD_510diesel, Model RUS_BTR90)
  - No Prerequisites Upgrade=, no WeaponSetUpgrade/MaxHealthUpgrade/
    LocomotorSetUpgrade on either vehicle
  - Command_ConstructRussiaVehicleTigr1 on live plant slot 6 and
    Command Center slot 11 (always buildable)
  - Upgrade_Rus_Tigr2 (SU39-style PLAYER_UPGRADE) on live plant slot 5
  - CommandSetUpgrade ModuleTag_Tigr2CS -> CommandSet with Tigr1 kept
    and Tigr2 UNIT_BUILD added
  War Factory, _T CommandSets, identity, ART, BTR82A.ini unchanged.

Test result:
  INGAME_TESTED = NO (no Generals/ZH client in this environment)
  PACK_EXECUTION_PATH = {'PASS' if working else 'FAIL'}
{check_lines}

DATA SHA256 {new_sha}
ART_CHANGED = NO
NO_GITHUB_RELEASE = YES
"""
    REPORT.write_text(report, encoding="utf-8")
    (OUT_DIR / "TIGR_SHARED_CRASH_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {new_sha}\nART unchanged\n", encoding="utf-8"
    )
    print(report)
    if not working:
        failed = [k for k, v in checks.items() if not v]
        raise SystemExit(f"shared tigr validation failed: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
