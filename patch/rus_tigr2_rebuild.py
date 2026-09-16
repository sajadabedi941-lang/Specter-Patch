#!/usr/bin/env python3
"""Rebuild upgrade_rus_tigr2 from zero on the capture DATA baseline.

Removes the failed implementations:
  1) Stub: PLAYER_UPGRADE on unused _T CommandSets, no object.
  2) Trace fix: Object cloned into BTR82A.ini with INVALID
     `Prerequisites / Upgrade = Upgrade_Rus_Tigr2` (that key is never used
     in this DATA set; SAGE Prerequisites only parse Object/Science).
     Construct was also placed on the live CS, so a PRELOAD parse failure
     crashes when the upgrade menu opens.

New chain (working Russia patterns only):
  Upgrade_SU39-style PLAYER_UPGRADE on RussiaIndsturialComplexCommandSet
  CommandSetUpgrade on RussiaIndustrialComplex (same module as _T Tier2)
    -> RussiaIndsturialComplexCommandSet_Tigr2 (adds UNIT_BUILD)
  Object RussiaVehicleTigr2 = byte-identical BTR82A clone except Object name
    in its own INI. No extra modules, no Prerequisites Upgrade, no cameo.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER_WARFACTORY_CAPTURE_UPDATE/_SPEC_DATA_ONE.big")
EXPECTED_DATA_SHA = "cc0595379e7f255f98170bd4502ed0479b634162739bd206748c86459176552b"
OUT_DIR = Path("/workspace/patch/Release/SPECTER1_RUS_TIGR2_REBUILD")
REPORT = Path("/workspace/patch/TIGR2_FULL_DEBUG_REPORT.txt")

P_UPG = r"Data\INI\Upgrade.ini"
P_BTN = r"Data\INI\CommandButton.ini"
P_CS = r"Data\INI\CommandSet.ini"
P_IC = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\WeaponIndustryPlant.ini"
P_BTR = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\APC\BTR82A.ini"
P_TIGR = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\APC\Tigr2.ini"
P_IMG = r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI"

CS_LIVE = "RussiaIndsturialComplexCommandSet"
CS_AFTER = "RussiaIndsturialComplexCommandSet_Tigr2"

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

BUTTON_BUILD = """CommandButton Command_ConstructRussiaVehicleTigr2
  Command       = UNIT_BUILD
  Object        = RussiaVehicleTigr2
  TextLabel     = CONTROLBAR:ConstructRussiaVehicleBTR82A
  ButtonImage   = rus_btr82
  ButtonBorderType        = BUILD ; Identifier for the User as to what kind of button this is
  DescriptLabel           = CONTROLBAR:ToolTipRussiaVehicleBTR82A
End
"""

CS_UPGRADE_MODULE = """  Behavior = CommandSetUpgrade ModuleTag_Tigr2CS
    TriggeredBy = Upgrade_Rus_Tigr2
    CommandSet  = RussiaIndsturialComplexCommandSet_Tigr2
  End
"""

TIGR_RX = re.compile(
    r"upgrade_rus_tigr2|Upgrade_Rus_Tigr2|rus_tigr2|RussiaVehicleTigr2|"
    r"Command_Upgrade_Rus_Tigr2|Command_ConstructRussiaVehicleTigr2|"
    r"RussiaIndsturialComplexCommandSet_Tigr2",
    re.I,
)


def insert_after_block(text: str, kind: str, name: str, new_block: str) -> str:
    nl = jf.file_nl(text)
    block = jf.to_nl(new_block.strip() + "\n", nl)
    m = re.search(rf"(?im)^{kind}\s+{re.escape(name)}\s*$", text)
    if not m:
        raise SystemExit(f"missing {kind} {name}")
    m2 = re.search(rf"(?im)^{kind}\s+\S+", text[m.end() :])
    end = m.end() + m2.start() if m2 else len(text)
    return text[:end] + block + nl + text[end:]


def extract_named(text: str, kind: str, name: str) -> str:
    m = re.search(rf"(?im)^{kind}\s+{re.escape(name)}\s*$", text)
    if not m:
        raise SystemExit(f"missing {kind} {name}")
    m2 = re.search(rf"(?im)^{kind}\s+\S+", text[m.end() :])
    return text[m.start() : m.end() + m2.start() if m2 else len(text)]


def insert_cs_button(text: str, cs_name: str, slot: int, button: str) -> str:
    m = re.search(rf"(?im)^CommandSet\s+{re.escape(cs_name)}\s*$", text)
    if not m:
        raise SystemExit(f"missing CommandSet {cs_name}")
    m2 = re.search(r"(?im)^CommandSet\s+\S+", text[m.end() :])
    end = m.end() + m2.start() if m2 else len(text)
    block = text[m.start() : end]
    if button in block:
        return text
    used = {int(x) for x in re.findall(r"(?im)^\s*(\d+)\s*=", block)}
    if slot in used:
        for s in range(1, 16):
            if s not in used:
                slot = s
                break
        else:
            raise SystemExit(f"{cs_name}: no free slot")
    nl = "\r\n" if "\r\n" in block else "\n"
    insert = f"  {slot} = {button}{nl}"
    lines = block.splitlines(True)
    out = []
    done = False
    for line in lines:
        if (not done) and re.search(r"(?im)^\s*End\s*$", line):
            out.append(insert)
            done = True
        out.append(line)
    return text[: m.start()] + "".join(out) + text[end:]


def strip_tigr_lines(text: str) -> str:
    """Drop any CommandSet slot lines that still point at Tigr2."""
    lines = text.splitlines(True)
    keep = []
    for line in lines:
        if re.search(r"(?i)Command_Upgrade_Rus_Tigr2|Command_ConstructRussiaVehicleTigr2", line):
            continue
        keep.append(line)
    return "".join(keep)


def strip_named_block(text: str, kind: str, name: str) -> str:
    m = re.search(rf"(?im)^{kind}\s+{re.escape(name)}\s*$", text)
    if not m:
        return text
    m2 = re.search(rf"(?im)^{kind}\s+\S+", text[m.end() :])
    end = m.end() + m2.start() if m2 else len(text)
    return text[: m.start()] + text[end:]


def make_tigr2_object(btr_text: str) -> str:
    block = jf.extract_object_block(btr_text, "RussiaVehicleBTR82A")
    block = block.replace("Object RussiaVehicleBTR82A", "Object RussiaVehicleTigr2", 1)
    if re.search(r"(?im)^\s*Upgrade\s*=", block):
        raise SystemExit("clone still has Upgrade =")
    if "WeaponSetUpgrade" in block or "LocomotorSetUpgrade" in block or "MaxHealthUpgrade" in block:
        raise SystemExit("clone inherited upgrade modules")
    return block


def insert_building_module(ic_text: str) -> str:
    if "ModuleTag_Tigr2CS" in ic_text:
        return ic_text
    nl = jf.file_nl(ic_text)
    block = jf.to_nl(CS_UPGRADE_MODULE.rstrip() + "\n", nl)
    m = re.search(r"(?im)^  Geometry\s*=", ic_text)
    if not m:
        raise SystemExit("IC Geometry missing")
    return ic_text[: m.start()] + block + nl + ic_text[m.start() :]


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

    # STEP 1: confirm capture baseline has ZERO tigr2, then never copy broken blocks.
    leftover = []
    for n, b in entries:
        if TIGR_RX.search(n) or TIGR_RX.search(bytes(b).decode("latin1", "replace")):
            leftover.append(n)
    if leftover:
        raise SystemExit(f"capture baseline already has tigr2: {leftover}")

    upg = jf.text_of(entries, P_UPG)
    btn = jf.text_of(entries, P_BTN)
    cs = jf.text_of(entries, P_CS)
    ic = jf.text_of(entries, P_IC)
    btr = jf.text_of(entries, P_BTR)
    img = jf.text_of(entries, P_IMG)

    upg = insert_after_block(upg, "Upgrade", "Upgrade_SU39", UPGRADE_BLOCK)
    btn = insert_after_block(btn, "CommandButton", "Command_Upgrade_SU39", BUTTON_UPG)
    btn = insert_after_block(btn, "CommandButton", "Command_ConstructRussiaVehicleBTR82A", BUTTON_BUILD)

    cs = insert_cs_button(cs, CS_LIVE, 5, "Command_Upgrade_Rus_Tigr2")
    live = extract_named(cs, "CommandSet", CS_LIVE)
    after = live.replace(f"CommandSet {CS_LIVE}", f"CommandSet {CS_AFTER}", 1)
    # inject construct into the AFTER set only
    tmp = "\n" + after if not after.startswith("CommandSet") else after
    # reuse insert_cs_button by wrapping
    wrapped = tmp if tmp.endswith("\n") else tmp + "\n"
    wrapped = insert_cs_button("CommandSet __WRAP__\nEnd\n" + wrapped, CS_AFTER, 6, "Command_ConstructRussiaVehicleTigr2")
    after = extract_named(wrapped, "CommandSet", CS_AFTER)
    cs = insert_after_block(cs, "CommandSet", CS_LIVE, after)

    ic = insert_building_module(ic)
    tigr = make_tigr2_object(btr)
    nl = jf.file_nl(btr)
    tigr = jf.to_nl(tigr, nl)

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
    pups = jf.text_of(packed, P_UPG)
    pbtn = jf.parse_buttons(jf.text_of(packed, P_BTN))
    pcs = jf.parse_commandsets(jf.text_of(packed, P_CS))
    pic = jf.text_of(packed, P_IC)
    ptigr = jf.text_of(packed, P_TIGR)
    pimg = jf.text_of(packed, P_IMG)
    pbtr = jf.text_of(packed, P_BTR)

    tigr_block = jf.extract_object_block(ptigr, "RussiaVehicleTigr2")
    btr_block = jf.extract_object_block(pbtr, "RussiaVehicleBTR82A")
    tigr_wo_name = re.sub(r"(?im)^Object\s+\S+", "Object __NAME__", tigr_block, count=1)
    btr_wo_name = re.sub(r"(?im)^Object\s+\S+", "Object __NAME__", btr_block, count=1)
    clone_exact = tigr_wo_name == btr_wo_name

    def cs_buttons(name: str) -> list[str]:
        return re.findall(r"(?im)^\s*\d+\s*=\s*(\S+)", pcs.get(name, ""))

    live_btns = cs_buttons(CS_LIVE)
    after_btns = cs_buttons(CS_AFTER)

    no_prereq_upg = not re.search(r"(?im)^\s*Upgrade\s*=", tigr_block)
    no_vehicle_modules = not re.search(
        r"(?im)Behavior\s*=\s*(WeaponSetUpgrade|LocomotorSetUpgrade|MaxHealthUpgrade|CommandSetUpgrade|ObjectCreationUpgrade)",
        tigr_block,
    )
    no_cameo = "Upgrade_Rus_Tigr2" not in tigr_block
    building_csu = bool(re.search(r"(?im)TriggeredBy\s*=\s*Upgrade_Rus_Tigr2", pic)) and CS_AFTER in pic
    no_img = not re.search(r"(?im)^MappedImage\s+upgrade_rus_tigr2\s*$", pimg)
    no_t_cs = all(
        "Tigr2" not in pcs.get(n, "")
        for n in (
            "RussiaWeaponIndustryPlantCommandSet_T",
            "RussiaWeaponIndustryPlantCommandSet_T1",
            "RussiaWeaponIndustryPlantCommandSet_T2",
            "RussiaWarFactoryCommandSet",
            "RussiaCommandCenterCommandSet",
        )
    )
    live_ok = "Command_Upgrade_Rus_Tigr2" in live_btns and "Command_ConstructRussiaVehicleTigr2" not in live_btns
    after_ok = (
        "Command_Upgrade_Rus_Tigr2" in after_btns
        and "Command_ConstructRussiaVehicleTigr2" in after_btns
        and "Command_Upgrade_SU39" in after_btns
        and "Command_Sell" in after_btns
    )
    upg_ok = bool(re.search(r"(?im)^Upgrade\s+Upgrade_Rus_Tigr2\s*$", pups))
    btn_upg_ok = "PLAYER_UPGRADE" in pbtn.get("Command_Upgrade_Rus_Tigr2", "") and "rus_btr82" in pbtn["Command_Upgrade_Rus_Tigr2"]
    btn_build_ok = "UNIT_BUILD" in pbtn.get("Command_ConstructRussiaVehicleTigr2", "") and "RussiaVehicleTigr2" in pbtn["Command_ConstructRussiaVehicleTigr2"]
    side_ok = bool(re.search(r"(?im)^\s*Side\s*=\s*Russia\s*$", tigr_block))
    refs_ok = all(
        [
            def_exists(packed, "Weapon", "30mm_2A72_dualfeed"),
            def_exists(packed, "Weapon", "7_62mm_PKT_Coaxial"),
            def_exists(packed, "Armor", "BTR90Armor"),
            def_exists(packed, "Locomotor", "TCD_510diesel"),
            def_exists(packed, "Object", "RussiaMechanizedInfantry"),
            def_exists(packed, "CommandSet", "GenericIFVcommandset"),
            def_exists(packed, "FXList", "FX_CrusaderCatchFire"),
            def_exists(packed, "ObjectCreationList", "OCL_BTR90DeathEffect"),
            def_exists(packed, "MappedImage", "rus_btr82"),
        ]
    )
    art_path = Path("/workspace/patch/Release/SPECTER1_BUILDING_FLAGS_01/_SPEC_ART_ONE.big")
    art_names = {jf.norm(n).lower() for n, _ in jf.read_big_list(art_path)}
    art_ok = r"art\w3d\rus_btr90.w3d" in art_names and r"art\w3d\rus_btr90d.w3d" in art_names

    # BTR82A.ini must be unchanged vs source
    src_entries = jf.read_big_list(SRC_DATA)
    btr_unchanged = bytes(jf.raw_of(packed, P_BTR)) == bytes(jf.raw_of(src_entries, P_BTR))
    img_unchanged = bytes(jf.raw_of(packed, P_IMG)) == bytes(jf.raw_of(src_entries, P_IMG))

    base = {jf.norm(n).lower(): bytes(b) for n, b in src_entries}
    packed_map = {jf.norm(n).lower(): (n, bytes(b)) for n, b in packed}
    changed = [
        packed_map[k][0]
        for k, old in base.items()
        if k in packed_map and packed_map[k][1] != old
    ]
    added = [n for n, b in packed if jf.norm(n).lower() not in base]
    allowed_mod = {jf.norm(x).lower() for x in (P_UPG, P_BTN, P_CS, P_IC)}
    allowed_add = {jf.norm(P_TIGR).lower()}
    if {jf.norm(c).lower() for c in changed} != allowed_mod:
        raise SystemExit(f"unexpected DATA mods: {changed}")
    if {jf.norm(a).lower() for a in added} != allowed_add:
        raise SystemExit(f"unexpected DATA adds: {added}")

    bcs = jf.parse_commandsets(jf.text_of(src_entries, P_CS))
    if pcs.get("RussiaWarFactoryCommandSet") != bcs.get("RussiaWarFactoryCommandSet"):
        raise SystemExit("Russia WF CommandSet changed")

    checks = {
        "Upgrade definition": upg_ok,
        "CommandButton upgrade SU39-style": btn_upg_ok,
        "CommandButton construct": btn_build_ok,
        "Live CS has upgrade, no construct": live_ok,
        "Post-upgrade CS has construct": after_ok,
        "CommandSetUpgrade on RussiaIndustrialComplex": building_csu,
        "Object clone exact except name": clone_exact,
        "No Prerequisites Upgrade": no_prereq_upg,
        "No vehicle upgrade modules": no_vehicle_modules,
        "No UpgradeCameo on Tigr2": no_cameo,
        "No MappedImage upgrade_rus_tigr2": no_img,
        "No Tigr2 on _T/WF/CC": no_t_cs,
        "BTR82A.ini unchanged": btr_unchanged,
        "MappedImages unchanged": img_unchanged,
        "Side=Russia": side_ok,
        "Weapon/Armor/Locomotor/FX/OCL/payload": refs_ok,
        "ART RUS_BTR90": art_ok,
    }
    working = all(checks.values())
    check_lines = "\n".join(f"  {k} = {'PASS' if v else 'FAIL'}" for k, v in checks.items())

    report = f"""TIGR2_FULL_DEBUG_REPORT

UPGRADE_RUS_TIGR2 = {'WORKING' if working else 'NOT_WORKING'}

Original crash cause:
  Two failed patches stacked on a missing unit.

  Patch 1 (stub) added Upgrade/CommandButton/MappedImage upgrade_rus_tigr2
  cloned from Upgrade_RUS_Tier2 and hung the button on
  RussiaWeaponIndustryPlantCommandSet_T/T1/T2. Those CommandSets belong to
  Object RussiaIndustrialComplex_T (Side=China). Live Russia builds
  RussiaIndustrialComplex -> RussiaIndsturialComplexCommandSet. No target
  object existed.

  Patch 2 (trace) cloned BTR82A as RussiaVehicleTigr2 and gated it with:

      Prerequisites
        Object = RussiaCommandCenter
        Upgrade = Upgrade_Rus_Tigr2
      End

  `Upgrade =` is not a valid Prerequisites field in this DATA set
  (zero uses; only Object and Science appear). RussiaVehicleTigr2 is
  KindOf PRELOAD, so SAGE parses it at load. The live upgrade menu also
  had UNIT_BUILD Tigr2 on slot 6, so a template parse failure crashes
  when the Weapon Industry Plant is selected.

  WeaponSetUpgrade / MaxHealthUpgrade / LocomotorSetUpgrade were NOT used
  on Tigr2. Those SU39 modules would also crash if pointed at missing
  Tigr weapons (9A1472_Vikhr1_SU39 / RUS_SU39). They stay omitted.

Broken file:
  Data\\INI\\Object\\Specter\\Armed Forces Of Russian Federation\\APC\\BTR82A.ini
  (Patch 2 appended a second Object with illegal Prerequisites Upgrade)
  Data\\INI\\CommandSet.ini
  (construct on live RussiaIndsturialComplexCommandSet; stub buttons on _T)

Broken reference:
  Prerequisites -> Upgrade = Upgrade_Rus_Tigr2
  Command_ConstructRussiaVehicleTigr2 on the pre-upgrade CommandSet
  MappedImage upgrade_rus_tigr2 / ButtonImage upgrade_rus_tigr2 (stub)
  Command_Upgrade_Rus_Tigr2 on China-sided _T CommandSets

New implementation (from capture DATA, no leftover Tigr2):
  1. Upgrade Upgrade_Rus_Tigr2 copied from working Upgrade_SU39
     (ButtonImage rus_btr82, existing MappedImage).
  2. Command_Upgrade_Rus_Tigr2 copied from working Command_Upgrade_SU39
     (PLAYER_UPGRADE, OK_FOR_MULTI_SELECT commented, Border ACTION).
  3. Live CommandSet RussiaIndsturialComplexCommandSet slot 5 = upgrade
     ONLY. Construct is NOT on the pre-upgrade bar.
  4. CommandSetUpgrade ModuleTag_Tigr2CS on Object RussiaIndustrialComplex
     TriggeredBy Upgrade_Rus_Tigr2 -> RussiaIndsturialComplexCommandSet_Tigr2
     (same module used by working RUS_Tier2 on the _T plant).
  5. Post-upgrade CommandSet adds Command_ConstructRussiaVehicleTigr2 slot 6
     and keeps every original plant button.
  6. Object RussiaVehicleTigr2 in new file Tigr2.ini: BTR82A clone, name
     only. No Prerequisites Upgrade, no UpgradeCameo, no extra modules.
     Weapons 30mm_2A72_dualfeed / 7_62mm_PKT_Coaxial, Armor BTR90Armor,
     Locomotor TCD_510diesel, Model RUS_BTR90, Side Russia.
  Isolated module: CommandSetUpgrade on the plant. Vehicle has zero
  upgrade-triggered modules.

Test result:
  INGAME_TESTED = NO (no Generals/ZH client in this environment)
  PACK_EXECUTION_PATH = {'PASS' if working else 'FAIL'}
{check_lines}

DATA SHA256 {new_sha}
ART_CHANGED = NO
NO_GITHUB_RELEASE = YES
"""
    REPORT.write_text(report, encoding="utf-8")
    (OUT_DIR / "TIGR2_FULL_DEBUG_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {new_sha}\nART unchanged\n", encoding="utf-8"
    )
    print(report)
    if not working:
        failed = [k for k, v in checks.items() if not v]
        raise SystemExit(f"rebuild validation failed: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
