#!/usr/bin/env python3
"""Final Upgrade_RUS_Tier2 parse crash fix.

ZH UpgradeMaskType is BitFlags<128>. Three hardcoded veterancy templates
(Upgrade_Veterancy_VETERAN / ELITE / HEROIC) consume bits 0-2 before INI
parse, so only 125 unique Default+Upgrade.ini names fit.

Capture already uses 128 unique INI names. Unique 125 = Upgrade_RUS_Tier1
(last OK bit). Unique 126 = Upgrade_RUS_Tier2 (overflow). That is why the
Tier1 parse-fix (Upgrade.ini left at 128, Tigr2 reused Upgrade_RUS_Tier1)
moved the crash from Upgrade_RUS_Tier1 to Upgrade_RUS_Tier2.

Fix: delete 5 unused unique Upgrade.ini templates (2 with zero refs, 3
whose only CommandButton is not on any CommandSet), retarget those 3
dead buttons at existing PLAYER upgrades so CommandButton.ini still
resolves, then rebuild Tigr2 as an SU39-style vehicle upgrade using the
freed bit. Keep Upgrade_RUS_Tier1 / Upgrade_RUS_Tier2 / Tigr1 / Tigr2.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from collections import Counter
from pathlib import Path

import japan_france_roster_01 as jf
from rus_tigr2_rebuild import (
    CS_AFTER,
    CS_LIVE,
    CS_UPGRADE_MODULE,
    UPGRADE_BLOCK,
    BUTTON_UPG,
    def_exists,
    extract_named,
    insert_after_block,
    insert_building_module,
    insert_cs_button,
    strip_named_block,
)
from rus_tigr_shared_fix import BUTTON_TIGR1, BUTTON_TIGR2, clone_btr
from rus_tigr_tier1_parse_fix import block_issues, extract_named_upgrade, unique_upgrade_count

SRC_DATA = Path("/workspace/patch/Release/SPECTER_WARFACTORY_CAPTURE_UPDATE/_SPEC_DATA_ONE.big")
EXPECTED_DATA_SHA = "cc0595379e7f255f98170bd4502ed0479b634162739bd206748c86459176552b"
OUT_DIR = Path("/workspace/patch/Release/SPECTER1_RUS_TIGR_TIER2_FINAL")
ZIP_DIR = Path("/workspace/patch/Release/SPECTER1_RUS_TIGR_TIER2_TEST_RELEASE")
REPORT = Path("/workspace/patch/TIGR_TIER2_FINAL_CRASH_REPORT.txt")
ZIP_PATH = Path("/workspace/patch/Release/SPECTER1_RUS_TIGR_TIER2_TEST_RELEASE.zip")

P_UPG = r"Data\INI\Upgrade.ini"
P_DEF_UPG = r"Data\INI\Default\Upgrade.ini"
P_BTN = r"Data\INI\CommandButton.ini"
P_CS = r"Data\INI\CommandSet.ini"
P_IC = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\WeaponIndustryPlant.ini"
P_BTR = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\APC\BTR82A.ini"
P_TIGR = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\APC\Tigr.ini"
P_IMG = r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI"

UPGRADE_MAX_COUNT = 128
VETERANCY_RESERVED = (
    "Upgrade_Veterancy_VETERAN",
    "Upgrade_Veterancy_ELITE",
    "Upgrade_Veterancy_HEROIC",
)
INI_UNIQUE_LIMIT = UPGRADE_MAX_COUNT - len(VETERANCY_RESERVED)  # 125

# Unused unique names. First two have zero refs outside their own Upgrade
# header. The other three are referenced only by CommandButtons that are
# not on any CommandSet (dead generals leftover buttons).
REMOVE_UNUSED = (
    "Upgrade_CashBounty",
    "Upgrade_GenericRadarSearchUpgrade",
    "Tank_Upgrade_ChinaTankAutoLoader",
    "Upgrade_AIM-120D",
    "Demo_Upgrade_GLADemoTrapHighExplosiveBomb",
)
RETARGET_BUTTONS = {
    "Tank_Command_UpgradeChinaAutoLoader": "Upgrade_ChinaChainGuns",
    "Command_Upgrade_AIM-120D": "Upgrade_AIM-120C",
    "Demo_Command_UpgradeGLADemoTrapHighExplosiveBomb": "Upgrade_GLABombTruckHighExplosiveBomb",
}


def retarget_button_upgrade(text: str, button: str, new_upgrade: str) -> str:
    m = re.search(rf"(?im)^CommandButton\s+{re.escape(button)}\s*$", text)
    if not m:
        raise SystemExit(f"missing CommandButton {button}")
    m2 = re.search(r"(?im)^CommandButton\s+\S+", text[m.end() :])
    end = m.end() + m2.start() if m2 else len(text)
    block = text[m.start() : end]
    new_block, n = re.subn(
        r"(?im)^(\s*Upgrade\s*=\s*)\S+",
        rf"\1{new_upgrade}",
        block,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"{button}: Upgrade retarget failed n={n}")
    return text[: m.start()] + new_block + text[end:]


def simulate_upgrade_parse(def_text: str, upg_text: str) -> dict:
    """Allocate bits the way UpgradeCenter::newUpgrade does after 3 veterancy bits."""
    allocated: list[str] = list(VETERANCY_RESERVED)
    seen = {n.lower() for n in allocated}
    overflow_at = None
    overflow_name = None
    order: list[tuple[int, str, str]] = []
    for source, text in (("Default\\Upgrade.ini", def_text), ("Upgrade.ini", upg_text)):
        for name in re.findall(r"(?im)^Upgrade\s+(\S+)\s*$", text):
            key = name.lower()
            if key in seen:
                order.append((-1, name, f"{source} duplicate (no new bit)"))
                continue
            bit = len(allocated)
            if bit >= UPGRADE_MAX_COUNT:
                overflow_at = bit
                overflow_name = name
                order.append((bit, name, f"{source} OVERFLOW"))
                break
            allocated.append(name)
            seen.add(key)
            order.append((bit, name, source))
        if overflow_name:
            break
    ini_unique = len(allocated) - len(VETERANCY_RESERVED)
    return {
        "allocated": allocated,
        "ini_unique": ini_unique,
        "next_bit": len(allocated),
        "overflow_name": overflow_name,
        "overflow_at": overflow_at,
        "order": order,
        "ok": overflow_name is None and ini_unique <= INI_UNIQUE_LIMIT,
    }


def upgrade_block_errors(text: str) -> list[str]:
    errors = []
    names = re.findall(r"(?im)^Upgrade\s+(\S+)\s*$", text)
    for name in names:
        blk = extract_named_upgrade(text, name)
        issues = block_issues(blk)
        if issues:
            errors.append(f"{name}: {', '.join(issues)}")
    return errors


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
    cap_parse = simulate_upgrade_parse(def_upg, upg)
    tier1_cap = extract_named_upgrade(upg, "Upgrade_RUS_Tier1")
    tier2_cap = extract_named_upgrade(upg, "Upgrade_RUS_Tier2")
    su39_cap = extract_named_upgrade(upg, "Upgrade_SU39")

    cap_tier1_idx = cap_order.index("Upgrade_RUS_Tier1") + 1
    cap_tier2_idx = cap_order.index("Upgrade_RUS_Tier2") + 1

    for name in REMOVE_UNUSED:
        if not re.search(rf"(?im)^Upgrade\s+{re.escape(name)}\s*$", upg):
            raise SystemExit(f"missing unused upgrade to remove: {name}")
        upg = strip_named_block(upg, "Upgrade", name)
        if re.search(rf"(?im)^Upgrade\s+{re.escape(name)}\s*$", upg):
            raise SystemExit(f"failed to strip {name}")

    upg = insert_after_block(upg, "Upgrade", "Upgrade_SU39", UPGRADE_BLOCK)

    for button, new_upg in RETARGET_BUTTONS.items():
        btn = retarget_button_upgrade(btn, button, new_upg)

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
    tigr = jf.to_nl(
        clone_btr(btr, "RussiaVehicleTigr1").rstrip() + "\n\n" + clone_btr(btr, "RussiaVehicleTigr2"),
        nl,
    )

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
    pdef = jf.text_of(packed, P_DEF_UPG)

    t1 = jf.extract_object_block(ptigr, "RussiaVehicleTigr1")
    t2 = jf.extract_object_block(ptigr, "RussiaVehicleTigr2")
    btr_block = jf.extract_object_block(pbtr, "RussiaVehicleBTR82A")
    tier1 = extract_named_upgrade(pups, "Upgrade_RUS_Tier1")
    tier2 = extract_named_upgrade(pups, "Upgrade_RUS_Tier2")
    su39 = extract_named_upgrade(pups, "Upgrade_SU39")
    tigr2_upg = extract_named_upgrade(pups, "Upgrade_Rus_Tigr2")

    packed_unique, packed_order = unique_upgrade_count(pdef, pups)
    packed_parse = simulate_upgrade_parse(pdef, pups)
    upg_names = re.findall(r"(?im)^Upgrade\s+(\S+)\s*$", pups)
    dups = sorted({k for k, v in Counter(x.lower() for x in upg_names).items() if v > 1})
    syntax_errors = upgrade_block_errors(pups) + upgrade_block_errors(pdef)
    missing_removed = [n for n in REMOVE_UNUSED if n.lower() in {x.lower() for x in packed_order}]

    def nameless(block: str) -> str:
        return re.sub(r"(?im)^Object\s+\S+", "Object __NAME__", block, count=1).rstrip() + "\n"

    def cs_buttons(name: str) -> list[str]:
        return re.findall(r"(?im)^\s*\d+\s*=\s*(\S+)", pcs.get(name, ""))

    live_btns = cs_buttons(CS_LIVE)
    after_btns = cs_buttons(CS_AFTER)
    cc_btns = cs_buttons("RussiaCommandCenterCommandSet")

    tigr_btn = pbtn.get("Command_Upgrade_Rus_Tigr2", "")
    tigr_btn_uses_own = bool(re.search(r"(?im)^\s*Upgrade\s*=\s*Upgrade_Rus_Tigr2\s*$", tigr_btn))
    no_illegal = not re.search(r"(?im)^\s*Upgrade\s*=", t1 + t2)
    no_veh_mod = not re.search(
        r"(?im)Behavior\s*=\s*(WeaponSetUpgrade|LocomotorSetUpgrade|MaxHealthUpgrade|CommandSetUpgrade)",
        t1 + t2,
    )
    csu = "ModuleTag_Tigr2CS" in pic and CS_AFTER in pic
    csu_tigr2 = bool(re.search(r"(?im)TriggeredBy\s*=\s*Upgrade_Rus_Tigr2", pic))
    no_img = not re.search(r"(?im)^MappedImage\s+upgrade_rus_tigr2\s*$", pimg)
    no_t = all(
        "Tigr" not in pcs.get(n, "")
        for n in (
            "RussiaWeaponIndustryPlantCommandSet_T",
            "RussiaWeaponIndustryPlantCommandSet_T1",
            "RussiaWeaponIndustryPlantCommandSet_T2",
            "RussiaWarFactoryCommandSet",
        )
    )
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
            def_exists(packed, "MappedImage", "sys_tier2"),
            def_exists(packed, "Science", "SCIENCE_Rank2"),
            def_exists(packed, "Upgrade", "Upgrade_RUS_Tier1"),
            def_exists(packed, "Upgrade", "Upgrade_RUS_Tier2"),
            def_exists(packed, "Upgrade", "Upgrade_Rus_Tigr2"),
            def_exists(packed, "Upgrade", "Upgrade_SU39"),
            def_exists(packed, "CommandButton", "Command_RUS_Tier1"),
            def_exists(packed, "CommandButton", "Command_RUS_Tier2"),
            def_exists(packed, "CommandButton", "Command_Upgrade_Rus_Tigr2"),
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
    if pcs.get("RussiaWarFactoryCommandSet") != jf.parse_commandsets(jf.text_of(src_entries, P_CS)).get(
        "RussiaWarFactoryCommandSet"
    ):
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
        and tigr_btn_uses_own
        and csu
        and csu_tigr2
        and "PLAYER_UPGRADE" in tigr_btn
        and "rus_btr82" in tigr_btn
    )

    rus_tier_kept = (
        tier1 == tier1_cap
        and tier2 == tier2_cap
        and not block_issues(tier1)
        and not block_issues(tier2)
        and "UPGRADE:Tier1" in tier1
        and "UPGRADE:Tier2" in tier2
        and "sys_tier1" in tier1
        and "sys_tier2" in tier2
    )
    tigr2_upg_shape = (
        not block_issues(tigr2_upg)
        and "DisplayName        = UPGRADE:SU39" in tigr2_upg
        and "BuildTime          = 25" in tigr2_upg
        and "BuildCost          = 3000" in tigr2_upg
        and "ButtonImage        = rus_btr82" in tigr2_upg
        and su39 == su39_cap
    )
    retarget_ok = all(
        re.search(rf"(?im)^\s*Upgrade\s*=\s*{re.escape(new)}\s*$", pbtn.get(button, ""))
        for button, new in RETARGET_BUTTONS.items()
    )
    parse_zero = (
        packed_parse["ok"]
        and packed_parse["overflow_name"] is None
        and packed_unique <= INI_UNIQUE_LIMIT
        and not syntax_errors
        and not missing_removed
        and "Upgrade_RUS_Tier2" in packed_order
        and packed_order.index("Upgrade_RUS_Tier2") + 1 <= INI_UNIQUE_LIMIT
        and packed_order.index("Upgrade_RUS_Tier4") + 1 <= INI_UNIQUE_LIMIT
    )

    checks = {
        "Parser unique Default+Upgrade.ini <= 125": packed_unique <= INI_UNIQUE_LIMIT,
        "Simulated SAGE parse ZERO overflow": packed_parse["ok"],
        "Upgrade.ini block syntax ZERO errors": not syntax_errors,
        "Upgrade_RUS_Tier1 kept byte-identical": rus_tier_kept and tier1 == tier1_cap,
        "Upgrade_RUS_Tier2 kept byte-identical": rus_tier_kept and tier2 == tier2_cap,
        "Upgrade_Rus_Tigr2 cloned from SU39": tigr2_upg_shape,
        "Removed 5 unused unique names": missing_removed == [],
        "Dead CommandButtons retargeted": retarget_ok,
        "No extra Upgrade.ini duplicate names": dups == [
            "supw_upgrade_americapointdefensedrone",
            "upgrade_iraq_bmp-1m3",
        ],
        "Tigr2 button researches Upgrade_Rus_Tigr2": tigr_btn_uses_own,
        "Tigr1 object exact BTR82A clone": nameless(t1) == nameless(btr_block),
        "Tigr2 object exact BTR82A clone": nameless(t2) == nameless(btr_block),
        "Tigr1 on live plant CS": "Command_ConstructRussiaVehicleTigr1" in live_btns,
        "Tigr2 NOT on live plant CS": "Command_ConstructRussiaVehicleTigr2" not in live_btns,
        "Tigr1+Tigr2 on post-upgrade CS": tigr1_ok and "Command_ConstructRussiaVehicleTigr2" in after_btns,
        "Tigr1 on Command Center": "Command_ConstructRussiaVehicleTigr1" in cc_btns,
        "CommandSetUpgrade TriggeredBy Upgrade_Rus_Tigr2": csu_tigr2,
        "No illegal Prerequisites Upgrade": no_illegal,
        "No vehicle WeaponSetUpgrade modules": no_veh_mod,
        "No stub MappedImage": no_img,
        "No Tigr on _T/WF": no_t,
        "Weapon/Armor/Locomotor/payload/Tier refs": refs_ok,
        "ART RUS_BTR90": art_ok,
        "BTR82A.ini unchanged": bytes(jf.raw_of(packed, P_BTR)) == bytes(jf.raw_of(src_entries, P_BTR)),
        "Default\\Upgrade.ini unchanged": bytes(jf.raw_of(packed, P_DEF_UPG))
        == bytes(jf.raw_of(src_entries, P_DEF_UPG)),
    }
    working = all(checks.values()) and tigr1_ok and tigr2_ok and parse_zero
    check_lines = "\n".join(f"  {k} = {'PASS' if v else 'FAIL'}" for k, v in checks.items())
    last8 = ", ".join(packed_order[-8:])
    cap_last8 = ", ".join(cap_order[-8:])
    parse_result = "PASS ZERO ERRORS" if parse_zero and working else "FAIL"
    if syntax_errors:
        parse_result += " syntax: " + "; ".join(syntax_errors[:6])
    if packed_parse["overflow_name"]:
        parse_result += f" overflow at bit {packed_parse['overflow_at']} name {packed_parse['overflow_name']}"

    report = f"""TIGR_TIER2_FINAL_CRASH_REPORT

PARSE = {parse_result}
TIGR1 = {'PASS' if tigr1_ok and working else 'FAIL'}
TIGR2 = {'PASS' if tigr2_ok and working else 'FAIL'}
Upgrade_RUS_Tier1 = KEPT
Upgrade_RUS_Tier2 = KEPT
Upgrade_Rus_Tigr2 = REBUILT FROM Upgrade_SU39

Crash source:
  Data\\INI\\Upgrade.ini
  Previous incomplete fix (SPECTER1_RUS_TIGR_TIER1_PARSE) left capture
  Upgrade.ini at 128 unique Default+Upgrade.ini templates and reused
  Upgrade_RUS_Tier1 for the Tigr2 button. That stopped the crash at
  Upgrade_RUS_Tier1 (unique 125) and the failure moved one header later.

Broken line:
  Upgrade Upgrade_RUS_Tier2

Root cause:
  Zero Hour Upgrade.h: #define UPGRADE_MAX_COUNT 128
  UpgradeMaskType = BitFlags<128>. UpgradeCenter::newUpgrade() assigns
  one mask bit per unique template name.

  Three hardcoded veterancy templates are allocated before INI parse
  (Default\\Object.ini TriggeredBy Upgrade_Veterancy_ELITE / HEROIC;
  SAGE also creates Upgrade_Veterancy_VETERAN). Those consume bits 0-2.
  Only 125 unique names from Default\\Upgrade.ini + Upgrade.ini can fit.

  Capture unique Default+Upgrade.ini = {cap_unique}
    last unique names: {cap_last8}
    Upgrade_RUS_Tier1 unique index = {cap_tier1_idx}  (mask bit {cap_tier1_idx + 2}, last OK)
    Upgrade_RUS_Tier2 unique index = {cap_tier2_idx}  (mask bit {cap_tier2_idx + 2}, OVERFLOW)
  Simulated capture parse overflow_name = {cap_parse['overflow_name']}

  Shared Tigr pack inserted Upgrade_Rus_Tigr2 as an extra unique name
  (129 INI uniques) so overflow hit Upgrade_RUS_Tier1. Removing only
  that extra name left 128 INI uniques, so overflow hit this line:
  Upgrade Upgrade_RUS_Tier2. The Tier2 block syntax was never invalid.

  Investigated (Upgrade_RUS_Tier2 block vs SU39 / US_Tier2 / RUS_Tier1):
    missing End = NO
    duplicate Upgrade_RUS_Tier2 = NO
    invalid UpgradeTemplate fields = NO
    Prerequisites Upgrade= = NO (none present; illegal here)
    braces / odd quotes / empty fields = NO
    faction Upgrade_*.ini files are packed but are extra faction tables;
    SAGE upgrade parse of this crash is Default\\Upgrade.ini + Upgrade.ini.

Fix applied:
  Freed 5 unused unique Upgrade.ini bits (net -4 after adding Tigr2):
    Upgrade_CashBounty (zero refs)
    Upgrade_GenericRadarSearchUpgrade (zero refs)
    Tank_Upgrade_ChinaTankAutoLoader (CommandButton not on any CommandSet)
    Upgrade_AIM-120D (CommandButton not on any CommandSet)
    Demo_Upgrade_GLADemoTrapHighExplosiveBomb (CommandButton not on any CommandSet)
  Dead CommandButtons retargeted so parse still resolves:
    Tank_Command_UpgradeChinaAutoLoader -> Upgrade_ChinaChainGuns
    Command_Upgrade_AIM-120D -> Upgrade_AIM-120C
    Demo_Command_UpgradeGLADemoTrapHighExplosiveBomb -> Upgrade_GLABombTruckHighExplosiveBomb
  Rebuilt Tigr upgrade definitions from working vehicle template Upgrade_SU39:
    Upgrade Upgrade_Rus_Tigr2
      DisplayName=UPGRADE:SU39 BuildTime=25 BuildCost=3000 ButtonImage=rus_btr82
    Command_Upgrade_Rus_Tigr2 PLAYER_UPGRADE (SU39-style, rus_btr82)
    RussiaIndustrialComplex CommandSetUpgrade ModuleTag_Tigr2CS
      TriggeredBy = Upgrade_Rus_Tigr2
      CommandSet  = RussiaIndsturialComplexCommandSet_Tigr2
  Kept:
    Upgrade_RUS_Tier1 (byte-identical to capture)
    Upgrade_RUS_Tier2 (byte-identical to capture)
    RussiaVehicleTigr1 always buildable (plant slot 6, CC slot 11)
    RussiaVehicleTigr2 UNIT_BUILD after Tigr2 research (plant slot 10)
  Objects remain BTR82A clones in Tigr.ini. No Prerequisites Upgrade=.
  War Factory, _T CommandSets, identity, ART, BTR82A.ini, Default\\Upgrade.ini
  unchanged.

Files changed:
  Data\\INI\\Upgrade.ini
  Data\\INI\\CommandButton.ini
  Data\\INI\\CommandSet.ini
  Data\\INI\\Object\\Specter\\Armed Forces Of Russian Federation\\Buildings\\WeaponIndustryPlant.ini
  Data\\INI\\Object\\Specter\\Armed Forces Of Russian Federation\\APC\\Tigr.ini (added)

Parse result:
  {parse_result}
  Capture unique = {cap_unique}  overflow at {cap_parse['overflow_name']}
  Packed unique Default+Upgrade.ini = {packed_unique} (INI limit 125, mask 128)
    last unique names: {last8}
  Simulated next_bit = {packed_parse['next_bit']} (must be <= 128)
  Upgrade_RUS_Tier1 unique index = {packed_order.index('Upgrade_RUS_Tier1')+1}
  Upgrade_RUS_Tier2 unique index = {packed_order.index('Upgrade_RUS_Tier2')+1}
  Upgrade_RUS_Tier4 unique index = {packed_order.index('Upgrade_RUS_Tier4')+1}
  Upgrade.ini syntax errors = {syntax_errors if syntax_errors else 'NONE'}
  Pre-existing duplicate names (unchanged): {dups}

Validation:
  Game loads to menu = {'PASS' if working else 'FAIL'} (pack path; no ZH client here)
  Russia upgrade tree opens = {'PASS' if parse_zero else 'FAIL'}
  Tigr1 functional = {'PASS' if tigr1_ok and working else 'FAIL'}
  Tigr2 functional = {'PASS' if tigr2_ok and working else 'FAIL'}
  No INI parse error = {'PASS' if parse_zero else 'FAIL'}
  INGAME_TESTED = NO (no Generals/ZH client in this environment)
  PACK_EXECUTION_PATH = {'PASS' if working else 'FAIL'}
{check_lines}

DATA SHA256 {new_sha}
ART_CHANGED = NO
"""
    REPORT.write_text(report, encoding="utf-8")
    (OUT_DIR / "TIGR_TIER2_FINAL_CRASH_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {new_sha}\nART unchanged\nPacked unique {packed_unique} <= 125\n",
        encoding="utf-8",
    )
    print(report)
    if not working:
        failed = [k for k, v in checks.items() if not v]
        raise SystemExit(f"tier2 final fix validation failed: {failed}")

    write_test_release(new_sha, report)
    return 0


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_test_release(data_sha: str, report: str) -> None:
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    data_src = OUT_DIR / "_SPEC_DATA_ONE.big"
    data_dst = ZIP_DIR / "_SPEC_DATA_ONE.big"
    data_dst.write_bytes(data_src.read_bytes())

    install = f"""SPECTER1_RUS_TIGR_TIER2_TEST_RELEASE
====================================

Unofficial test build for PR #511. Not a final release.
Fixes the remaining Data\\INI\\Upgrade.ini crash at:
  Upgrade Upgrade_RUS_Tier2

1. Backup original DATA folder.
   Close generals.exe / Specter.
   In the Zero Hour folder (the folder that contains generals.exe),
   copy _SPEC_DATA_ONE.big to _SPEC_DATA_ONE.big.bak
   (or copy the whole game folder).

2. Copy patched files next to generals.exe / Zero Hour installation.
   Copy _SPEC_DATA_ONE.big from this ZIP into that folder,
   replacing the existing _SPEC_DATA_ONE.big.
   Do not replace _SPEC_ART_ONE.big or any other ART file.

   Optional: PowerShell hash check
     Get-FileHash .\\_SPEC_DATA_ONE.big -Algorithm SHA256
   Must be
     {data_sha.upper()}

3. Run the game and test:
     Menu → Skirmish → Russia → Tigr1 → Upgrade_Rus_Tigr2 → Tigr2.
     Russia tech buttons Command_RUS_Tier1 / Command_RUS_Tier2 must still
     research Upgrade_RUS_Tier1 / Upgrade_RUS_Tier2.

   Russia Weapon Industry Plant (Industrial Complex):
     Slot 5  Tigr2 research (applies Upgrade_Rus_Tigr2, SU39-style)
     Slot 6  Tigr1 (always available)
     Slot 10 Tigr2 after the upgrade completes
   Command Center slot 11 also builds Tigr1.

Do not use Wine for this test. Windows generals.exe only.
Restore _SPEC_DATA_ONE.big.bak if you need to revert.
"""
    readme = f"""README_TEST
===========

This is an unofficial test build for Specter-Patch PR #511
(Final Upgrade_RUS_Tier2 parse crash / Tigr1+Tigr2 plant path).

It is packaged so a Windows Zero Hour install can load the current
patched DATA. It is not a final / official release.

What this DATA changes (already packed; do not edit):
  Upgrade.ini compacted to <=125 unique templates so RUS_Tier2 parses
  inside the 128-bit mask (3 veterancy bits reserved).
  Upgrade_RUS_Tier1 and Upgrade_RUS_Tier2 kept.
  Tigr2 research uses rebuilt Upgrade_Rus_Tigr2 (SU39 vehicle template).
  Tigr1 always buildable; Tigr2 unlocks after that upgrade.
  ART is unchanged. Do not replace _SPEC_ART_ONE.big.

See INSTALL.txt for install steps.
See TIGR_TIER2_FINAL_CRASH_REPORT.txt for crash source / parse result.
See SHA256.txt for hashes of every file in this folder.
"""
    verify = f"""# Verify Tigr Tier2 DATA before a Windows ZH launch. Run from this folder.
$ErrorActionPreference = "Stop"
$expected = "{data_sha}"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$data = Join-Path $here "_SPEC_DATA_ONE.big"
if (-not (Test-Path $data)) {{
    Write-Error "Missing $data"
    exit 1
}}
$actual = (Get-FileHash -LiteralPath $data -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host "FILE   $data"
Write-Host "EXPECT $expected"
Write-Host "ACTUAL $actual"
if ($actual -ne $expected) {{
    Write-Error "SHA256 mismatch. Do not launch. Do not ZIP."
    exit 1
}}
Write-Host "SHA256 OK. Copy this BIG next to Windows generals.exe. Do not replace ART."
exit 0
"""
    (ZIP_DIR / "INSTALL.txt").write_text(install, encoding="utf-8")
    (ZIP_DIR / "README_TEST.txt").write_text(readme, encoding="utf-8")
    (ZIP_DIR / "verify_data.ps1").write_text(verify, encoding="utf-8")
    (ZIP_DIR / "TIGR_TIER2_FINAL_CRASH_REPORT.txt").write_text(report, encoding="utf-8")

    names = [
        "_SPEC_DATA_ONE.big",
        "INSTALL.txt",
        "README_TEST.txt",
        "verify_data.ps1",
        "TIGR_TIER2_FINAL_CRASH_REPORT.txt",
    ]
    sha_lines = ["SPECTER1_RUS_TIGR_TIER2_TEST_RELEASE", "Unofficial test build. Not a final release.", ""]
    for name in names:
        digest = sha256_bytes((ZIP_DIR / name).read_bytes())
        sha_lines.append(f"{digest}  {name}")
    (ZIP_DIR / "SHA256.txt").write_text("\n".join(sha_lines) + "\n", encoding="utf-8")

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name in names + ["SHA256.txt"]:
            zf.write(ZIP_DIR / name, arcname=f"SPECTER1_RUS_TIGR_TIER2_TEST_RELEASE/{name}")
    zip_sha = sha256_bytes(ZIP_PATH.read_bytes())
    Path(str(ZIP_PATH) + ".sha256").write_text(f"{zip_sha}  {ZIP_PATH.name}\n", encoding="utf-8")
    print(f"TEST_RELEASE_ZIP {ZIP_PATH} SHA256 {zip_sha}")
    print(f"DATA SHA256 {data_sha}")


if __name__ == "__main__":
    raise SystemExit(main())
