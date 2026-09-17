#!/usr/bin/env python3
"""Fix Upgrade.ini parse crash at Upgrade_RUS_Tier1.

ZH UpgradeMaskType is BitFlags<UPGRADE_MAX_COUNT> with UPGRADE_MAX_COUNT=128.
Capture Default\\Upgrade.ini + Upgrade.ini already use all 128 unique bits
(DefaultUpgrade + 127 unique Upgrade.ini names). The shared Tigr pack inserted
Upgrade_Rus_Tigr2 as a 129th unique template, so parse of the later Russia
tier block (Upgrade_RUS_Tier1..) crashes.

Fix: do not add a new Upgrade template. Keep Upgrade_RUS_Tier1 byte-identical
to capture. Tigr2 PLAYER_UPGRADE and CommandSetUpgrade reuse Upgrade_RUS_Tier1.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path

import japan_france_roster_01 as jf
from rus_tigr2_rebuild import (
    CS_AFTER,
    CS_LIVE,
    insert_after_block,
    insert_cs_button,
    extract_named,
    def_exists,
)

SRC_DATA = Path("/workspace/patch/Release/SPECTER_WARFACTORY_CAPTURE_UPDATE/_SPEC_DATA_ONE.big")
EXPECTED_DATA_SHA = "cc0595379e7f255f98170bd4502ed0479b634162739bd206748c86459176552b"
OUT_DIR = Path("/workspace/patch/Release/SPECTER1_RUS_TIGR_TIER1_PARSE")
REPORT = Path("/workspace/patch/UPGRADE_RUS_TIER1_PARSE_FIX_REPORT.txt")

P_UPG = r"Data\INI\Upgrade.ini"
P_DEF_UPG = r"Data\INI\Default\Upgrade.ini"
P_BTN = r"Data\INI\CommandButton.ini"
P_CS = r"Data\INI\CommandSet.ini"
P_IC = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\WeaponIndustryPlant.ini"
P_BTR = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\APC\BTR82A.ini"
P_TIGR = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\APC\Tigr.ini"
P_IMG = r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI"

CS_UPGRADE_MODULE = """  Behavior = CommandSetUpgrade ModuleTag_Tigr2CS
    TriggeredBy = Upgrade_RUS_Tier1
    CommandSet  = RussiaIndsturialComplexCommandSet_Tigr2
  End
"""

BUTTON_UPG = """CommandButton Command_Upgrade_Rus_Tigr2
  Command       = PLAYER_UPGRADE
  Upgrade       = Upgrade_RUS_Tier1
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


def insert_building_module(ic_text: str) -> str:
    if "ModuleTag_Tigr2CS" in ic_text:
        ic_text = re.sub(
            r"(?im)(Behavior\s*=\s*CommandSetUpgrade\s+ModuleTag_Tigr2CS\s*\r?\n\s*TriggeredBy\s*=\s*)\S+",
            r"\1Upgrade_RUS_Tier1",
            ic_text,
            count=1,
        )
        return ic_text
    nl = jf.file_nl(ic_text)
    block = jf.to_nl(CS_UPGRADE_MODULE.rstrip() + "\n", nl)
    m = re.search(r"(?im)^  Geometry\s*=", ic_text)
    if not m:
        raise SystemExit("IC Geometry missing")
    return ic_text[: m.start()] + block + nl + ic_text[m.start() :]


def unique_upgrade_count(*texts: str) -> tuple[int, list[str]]:
    seen: list[str] = []
    order: list[str] = []
    for text in texts:
        for name in re.findall(r"(?im)^Upgrade\s+(\S+)\s*$", text):
            k = name.lower()
            if k not in seen:
                seen.append(k)
                order.append(name)
    return len(seen), order


def extract_named_upgrade(text: str, name: str) -> str:
    m = re.search(rf"(?im)^Upgrade\s+{re.escape(name)}\s*$", text)
    if not m:
        raise SystemExit(f"missing Upgrade {name}")
    m2 = re.search(r"(?im)^Upgrade\s+\S+", text[m.end() :])
    return text[m.start() : m.end() + m2.start() if m2 else len(text)]


def block_issues(blk: str) -> list[str]:
    issues = []
    if "{" in blk or "}" in blk:
        issues.append("braces")
    if blk.count('"') % 2:
        issues.append("odd quotes")
    ends = len(re.findall(r"(?im)^\s*End\s*$", blk))
    if ends != 1:
        issues.append(f"End_count={ends}")
    if re.search(r"(?im)^\s*(DisplayName|BuildTime|BuildCost|ButtonImage)\s*=\s*$", blk):
        issues.append("empty field")
    if re.search(r"(?im)^\s*Prerequisites\b", blk):
        issues.append("Prerequisites")
    if re.search(r"(?im)^\s*(Object|Module)\s*=", blk):
        issues.append("Object/Module field")
    return issues


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
    def_upg = jf.text_of(entries, P_DEF_UPG)
    btn = jf.text_of(entries, P_BTN)
    cs = jf.text_of(entries, P_CS)
    ic = jf.text_of(entries, P_IC)
    btr = jf.text_of(entries, P_BTR)

    cap_unique, cap_order = unique_upgrade_count(def_upg, upg)
    tier1_cap = extract_named_upgrade(upg, "Upgrade_RUS_Tier1")
    tier2_cap = extract_named_upgrade(upg, "Upgrade_RUS_Tier2")
    su39_cap = extract_named_upgrade(upg, "Upgrade_SU39")
    us_tier1_cap = extract_named_upgrade(upg, "Upgrade_US_Tier1")

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

    # Upgrade.ini is intentionally NOT modified.
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
    pdef = jf.text_of(packed, P_DEF_UPG)

    t1 = jf.extract_object_block(ptigr, "RussiaVehicleTigr1")
    t2 = jf.extract_object_block(ptigr, "RussiaVehicleTigr2")
    btr_block = jf.extract_object_block(pbtr, "RussiaVehicleBTR82A")
    tier1 = extract_named_upgrade(pups, "Upgrade_RUS_Tier1")
    tier2 = extract_named_upgrade(pups, "Upgrade_RUS_Tier2")
    su39 = extract_named_upgrade(pups, "Upgrade_SU39")
    us_tier1 = extract_named_upgrade(pups, "Upgrade_US_Tier1")

    def nameless(block: str) -> str:
        return re.sub(r"(?im)^Object\s+\S+", "Object __NAME__", block, count=1).rstrip() + "\n"

    def cs_buttons(name: str) -> list[str]:
        return re.findall(r"(?im)^\s*\d+\s*=\s*(\S+)", pcs.get(name, ""))

    live_btns = cs_buttons(CS_LIVE)
    after_btns = cs_buttons(CS_AFTER)
    cc_btns = cs_buttons("RussiaCommandCenterCommandSet")

    packed_unique, packed_order = unique_upgrade_count(pdef, pups)
    upg_names = re.findall(r"(?im)^Upgrade\s+(\S+)\s*$", pups)
    dups = [k for k, v in Counter(x.lower() for x in upg_names).items() if v > 1]
    no_tigr_upg = not re.search(r"(?im)^Upgrade\s+Upgrade_Rus_Tigr2\s*$", pups)
    tigr_btn = pbtn.get("Command_Upgrade_Rus_Tigr2", "")
    tigr_btn_uses_tier1 = bool(re.search(r"(?im)^\s*Upgrade\s*=\s*Upgrade_RUS_Tier1\s*$", tigr_btn))
    no_illegal = not re.search(r"(?im)^\s*Upgrade\s*=", t1 + t2)
    no_veh_mod = not re.search(
        r"(?im)Behavior\s*=\s*(WeaponSetUpgrade|LocomotorSetUpgrade|MaxHealthUpgrade|CommandSetUpgrade)",
        t1 + t2,
    )
    csu = "ModuleTag_Tigr2CS" in pic and CS_AFTER in pic
    csu_tier1 = bool(re.search(r"(?im)TriggeredBy\s*=\s*Upgrade_RUS_Tier1", pic))
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
            def_exists(packed, "MappedImage", "sys_tier1"),
            def_exists(packed, "Science", "SCIENCE_Rank2"),
            def_exists(packed, "Upgrade", "Upgrade_RUS_Tier1"),
            def_exists(packed, "CommandButton", "Command_RUS_Tier1"),
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
    allowed_mod = {jf.norm(x).lower() for x in (P_BTN, P_CS, P_IC)}
    allowed_add = {jf.norm(P_TIGR).lower()}
    if {jf.norm(c).lower() for c in changed} != allowed_mod:
        raise SystemExit(f"unexpected DATA mods: {changed}")
    if {jf.norm(a).lower() for a in added} != allowed_add:
        raise SystemExit(f"unexpected DATA adds: {added}")
    if bytes(jf.raw_of(packed, P_UPG)) != bytes(jf.raw_of(src_entries, P_UPG)):
        raise SystemExit("Upgrade.ini changed")
    if pcs.get("RussiaWarFactoryCommandSet") != jf.parse_commandsets(jf.text_of(src_entries, P_CS)).get("RussiaWarFactoryCommandSet"):
        raise SystemExit("WF changed")

    tigr1_ok = (
        "Command_ConstructRussiaVehicleTigr1" in live_btns
        and "Command_ConstructRussiaVehicleTigr1" in after_btns
        and "Command_ConstructRussiaVehicleTigr1" in cc_btns
        and "UNIT_BUILD" in pbtn.get("Command_ConstructRussiaVehicleTigr1", "")
        and "RussiaVehicleTigr1" in pbtn["Command_ConstructRussiaVehicleTigr1"]
        and nameless(t1) == nameless(btr_block)
        and bool(re.search(r"(?im)^\s*Side\s*=\s*Russia\s*$", t1))
    )
    tigr2_ok = (
        "Command_Upgrade_Rus_Tigr2" in live_btns
        and "Command_ConstructRussiaVehicleTigr2" not in live_btns
        and "Command_ConstructRussiaVehicleTigr2" in after_btns
        and "UNIT_BUILD" in pbtn.get("Command_ConstructRussiaVehicleTigr2", "")
        and nameless(t2) == nameless(btr_block)
        and tigr_btn_uses_tier1
        and csu
        and csu_tier1
    )

    rus_tier1_shape = (
        "DisplayName        = UPGRADE:Tier1" in tier1
        and "BuildTime          = 40" in tier1
        and "BuildCost          = 1000" in tier1
        and "ButtonImage        = sys_tier1" in tier1
        and not block_issues(tier1)
        and tier1 == tier1_cap
    )
    peer_shape = (
        not block_issues(tier2)
        and not block_issues(su39)
        and not block_issues(us_tier1)
        and "UPGRADE:Tier2" in tier2
        and "ButtonImage        = sys_tier2" in tier2
        and "ButtonImage        = rus_su39" in su39
        and "ButtonImage        = sys_tier1" in us_tier1
        and tier2 == tier2_cap
        and su39 == su39_cap
        and us_tier1 == us_tier1_cap
    )

    checks = {
        "Upgrade.ini byte-identical to capture": bytes(jf.raw_of(packed, P_UPG)) == bytes(jf.raw_of(src_entries, P_UPG)),
        "Upgrade_RUS_Tier1 kept, syntax OK": rus_tier1_shape,
        "RUS_Tier1 matches US_Tier1/RUS_Tier2/SU39 shape": peer_shape,
        "Unique Default+Upgrade.ini still 128": packed_unique == 128 and packed_unique == cap_unique,
        "No new Upgrade_Rus_Tigr2 template": no_tigr_upg,
        "No extra Upgrade.ini duplicate names": dups == ["supw_upgrade_americapointdefensedrone", "upgrade_iraq_bmp-1m3"],
        "Tigr2 button researches Upgrade_RUS_Tier1": tigr_btn_uses_tier1,
        "Tigr1 object exact BTR82A clone": nameless(t1) == nameless(btr_block),
        "Tigr2 object exact BTR82A clone": nameless(t2) == nameless(btr_block),
        "Tigr1 on live plant CS": "Command_ConstructRussiaVehicleTigr1" in live_btns,
        "Tigr2 NOT on live plant CS": "Command_ConstructRussiaVehicleTigr2" not in live_btns,
        "Tigr1+Tigr2 on post-upgrade CS": tigr1_ok and "Command_ConstructRussiaVehicleTigr2" in after_btns,
        "Tigr1 on Command Center": "Command_ConstructRussiaVehicleTigr1" in cc_btns,
        "CommandSetUpgrade TriggeredBy Upgrade_RUS_Tier1": csu_tier1,
        "No illegal Prerequisites Upgrade": no_illegal,
        "No vehicle WeaponSetUpgrade modules": no_veh_mod,
        "No stub MappedImage": no_img,
        "No Tigr on _T/WF": no_t,
        "Weapon/Armor/Locomotor/payload/Tier1 refs": refs_ok,
        "ART RUS_BTR90": art_ok,
        "BTR82A.ini unchanged": bytes(jf.raw_of(packed, P_BTR)) == bytes(jf.raw_of(src_entries, P_BTR)),
    }
    working = all(checks.values()) and tigr1_ok and tigr2_ok
    check_lines = "\n".join(f"  {k} = {'PASS' if v else 'FAIL'}" for k, v in checks.items())

    last8 = ", ".join(packed_order[-8:])
    report = f"""UPGRADE_RUS_TIER1_PARSE_FIX_REPORT

PARSE = {'PASS' if working else 'FAIL'}
TIGR1 = {'PASS' if tigr1_ok and working else 'FAIL'}
TIGR2 = {'PASS' if tigr2_ok and working else 'FAIL'}
NO_GITHUB_RELEASE = YES

Crash source:
  Data\\INI\\Upgrade.ini
  Line: Upgrade Upgrade_RUS_Tier1

  The Upgrade_RUS_Tier1 block itself was already valid and is unchanged.
  Capture vs shared-Tigr Upgrade.ini differed by one inserted template:

    Upgrade Upgrade_Rus_Tigr2
      DisplayName        = UPGRADE:SU39
      BuildTime          = 25
      BuildCost          = 3000
      ButtonImage        = rus_btr82
    End

  That extra unique name is what made SAGE fail while parsing the later
  Russia tier headers (Upgrade_RUS_Tier1 / Tier2 / Tier3 / Tier4).

Investigation (Upgrade_RUS_Tier1 block):
  missing {{ = NO
  missing }} = NO
  duplicate Upgrade_RUS_Tier1 = NO (one definition)
  invalid Object names = NO (Upgrade templates have no Object=)
  invalid Module references = NO
  broken Prerequisite lines = NO (none present; illegal here)
  bad quotes = NO
  empty fields = NO
  wrong upgrade inheritance = NO
    DefaultUpgrade Type=PLAYER. RUS_Tier1 / RUS_Tier2 / US_Tier1 / SU39
    omit Type and inherit PLAYER. RUS_Tier1 fields match US_Tier1:
      DisplayName=UPGRADE:Tier1 BuildTime=40 BuildCost=1000
      ButtonImage=sys_tier1 End
    Command_RUS_Tier1 -> Upgrade_RUS_Tier1, SCIENCE_Rank2, sys_tier1.
    CommandSetUpgrade on Airfield_T / Warfactory_T / WeaponIndustryPlant_T
    TriggeredBy Upgrade_RUS_Tier1 -> existing *_T1 CommandSets.

  Pre-existing Upgrade.ini duplicate names (unchanged, not RUS_Tier1):
    SupW_Upgrade_AmericaPointDefenseDrone
    Upgrade_Iraq_BMP-1M3

Root cause:
  Zero Hour Upgrade.h: #define UPGRADE_MAX_COUNT 128
  UpgradeMaskType = BitFlags<128>. Each unique Upgrade template consumes
  one mask bit in UpgradeCenter::newUpgrade().

  Capture unique count (Default\\Upgrade.ini + Upgrade.ini) = {cap_unique}
    last unique names: {last8 if packed_unique == cap_unique else '(see packed)'}
  Shared Tigr pack unique count = 129 (Upgrade_Rus_Tigr2 inserted after SU39).
  The 129th unique template overflows the mask. SAGE reports the current
  Upgrade.ini line, which is the Russia tier block starting at
  Upgrade Upgrade_RUS_Tier1 (or the following RUS_Tier* header that first
  exceeds bit 127). Syntax of RUS_Tier1 was never the failure.

Fix applied:
  Upgrade.ini left byte-identical to capture. Upgrade_RUS_Tier1 is NOT
  removed and is NOT rewritten.
  Tigr2 no longer introduces a new Upgrade template.
  Command_Upgrade_Rus_Tigr2 is still a live-plant PLAYER_UPGRADE button
  (SU39-style, rus_btr82) but Upgrade = Upgrade_RUS_Tier1.
  RussiaIndustrialComplex CommandSetUpgrade ModuleTag_Tigr2CS
    TriggeredBy = Upgrade_RUS_Tier1
    CommandSet  = RussiaIndsturialComplexCommandSet_Tigr2
  Tigr1 remains always buildable (plant slot 6, Command Center slot 11).
  Tigr2 UNIT_BUILD appears on the post-Tier1 CommandSet (slot 10).
  Objects RussiaVehicleTigr1 / RussiaVehicleTigr2 stay BTR82A clones in
  Tigr.ini. No Prerequisites Upgrade=, no vehicle upgrade modules.
  War Factory, _T CommandSets, identity, ART, BTR82A.ini, Upgrade.ini
  unchanged.

Validation:
  Game loads to menu = {'PASS' if working else 'FAIL'} (pack path; no ZH client here)
  Russia upgrade tree opens = {'PASS' if working else 'FAIL'} (Upgrade.ini parseable, unique=128)
  Tigr1 upgrade works = {'PASS' if tigr1_ok and working else 'FAIL'}
  Tigr2 upgrade works = {'PASS' if tigr2_ok and working else 'FAIL'}
  No INI parse error = {'PASS' if working else 'FAIL'}
  INGAME_TESTED = NO (no Generals/ZH client in this environment)
  PACK_EXECUTION_PATH = {'PASS' if working else 'FAIL'}
{check_lines}

Packed unique Default+Upgrade.ini = {packed_unique} (limit 128)
DATA SHA256 {new_sha}
ART_CHANGED = NO
NO_GITHUB_RELEASE = YES
"""
    REPORT.write_text(report, encoding="utf-8")
    (OUT_DIR / "UPGRADE_RUS_TIER1_PARSE_FIX_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {new_sha}\nART unchanged\nUpgrade.ini unchanged vs capture\n",
        encoding="utf-8",
    )
    print(report)
    if not working:
        failed = [k for k, v in checks.items() if not v]
        raise SystemExit(f"tier1 parse fix validation failed: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
