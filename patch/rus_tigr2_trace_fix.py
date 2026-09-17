#!/usr/bin/env python3
"""TIGR2 crash trace fix 02.

Previous stub only added Upgrade/CommandButton/MappedImage with NO target
object and NO modules. Purchase could complete; spawn Tigr2 was impossible
and any attempt to build a missing object crashes SAGE.

Real chain (compare Upgrade_SU39 / RussiaVehicleBTR82A):
  Upgrade_Rus_Tigr2
    -> Command_Upgrade_Rus_Tigr2 (PLAYER_UPGRADE) on Industrial Complex
    -> Object RussiaVehicleTigr2 (BTR82A clone, existing W3D/weapons/armor)
    -> UNIT_BUILD Command_ConstructRussiaVehicleTigr2
    -> NO WeaponSetUpgrade / LocomotorSetUpgrade / MaxHealthUpgrade
       (those are the modules that crash when they point at missing weapons)

Isolation: Tigr2 has zero upgrade-triggered modules. Only a player flag +
Prerequisites Upgrade gate, same weapons as working BTR82A.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER_WARFACTORY_CAPTURE_UPDATE/_SPEC_DATA_ONE.big")
EXPECTED_DATA_SHA = "cc0595379e7f255f98170bd4502ed0479b634162739bd206748c86459176552b"
OUT_DIR = Path("/workspace/patch/Release/SPECTER1_RUS_TIGR2_CRASHFIX")
REPORT = Path("/workspace/patch/TIGR2_CRASH_TRACE_REPORT.txt")

P_UPG = r"Data\INI\Upgrade.ini"
P_BTN = r"Data\INI\CommandButton.ini"
P_CS = r"Data\INI\CommandSet.ini"
P_IMG = r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI"
P_BTR = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\APC\BTR82A.ini"

UPGRADE_BLOCK = """Upgrade Upgrade_Rus_Tigr2
  DisplayName        = UPGRADE:SU39
  BuildTime          = 30
  BuildCost          = 1000
  ButtonImage        = rus_btr82
End
"""

BUTTON_UPG = """CommandButton Command_Upgrade_Rus_Tigr2
  Command       = PLAYER_UPGRADE
  Upgrade       = Upgrade_Rus_Tigr2
  TextLabel     = CONTROLBAR:Upgrade_SU39
  ButtonImage   = rus_btr82
  ButtonBorderType        = ACTION
  DescriptLabel           = CONTROLBAR:ToolTipUpgrade_SU39
End
"""

BUTTON_BUILD = """CommandButton Command_ConstructRussiaVehicleTigr2
  Command       = UNIT_BUILD
  Object        = RussiaVehicleTigr2
  TextLabel     = CONTROLBAR:ConstructRussiaVehicleBTR82A
  ButtonImage   = rus_btr82
  ButtonBorderType        = BUILD
  DescriptLabel           = CONTROLBAR:ToolTipRussiaVehicleBTR82A
End
"""

IMAGE_BLOCK = """MappedImage upgrade_rus_tigr2
  Texture = rus_Icons05.tga
  TextureWidth = 512
  TextureHeight = 512
  Coords = Left:255 Top:212 Right:376 Bottom:313
  Status = NONE
End
"""


def insert_after_block(text: str, kind: str, name: str, new_block: str) -> str:
    nl = jf.file_nl(text)
    block = jf.to_nl(new_block.strip() + "\n", nl)
    m = re.search(rf"(?im)^{kind}\s+{re.escape(name)}\s*$", text)
    if not m:
        raise SystemExit(f"missing {kind} {name}")
    m2 = re.search(rf"(?im)^{kind}\s+\S+", text[m.end() :])
    end = m.end() + m2.start() if m2 else len(text)
    return text[:end] + block + nl + text[end:]


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


def make_tigr2_object(btr_text: str) -> str:
    m = re.search(r"(?im)^Object\s+RussiaVehicleBTR82A\s*$", btr_text)
    if not m:
        raise SystemExit("BTR82A object missing")
    m2 = re.search(r"(?im)^Object\s+\S+", btr_text[m.end() :])
    block = btr_text[m.start() : m.end() + m2.start() if m2 else len(btr_text)]
    block = block.replace("Object RussiaVehicleBTR82A", "Object RussiaVehicleTigr2", 1)
    # cameo
    block = block.replace(
        "  ;UpgradeCameo3 = NONE",
        "  UpgradeCameo1           = Upgrade_Rus_Tigr2\n  ;UpgradeCameo3 = NONE",
        1,
    )
    # gate spawn behind the upgrade; keep Command Center prereq
    if "Upgrade = Upgrade_Rus_Tigr2" not in block:
        block = re.sub(
            r"(?im)^(\s*Prerequisites\s*\n\s*Object\s*=\s*RussiaCommandCenter\s*\n)",
            r"\1    Upgrade = Upgrade_Rus_Tigr2\n",
            block,
            count=1,
        )
    return block.rstrip() + "\n"


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("unexpected source DATA SHA")
    entries = jf.read_big_list(SRC_DATA)

    upg = jf.text_of(entries, P_UPG)
    btn = jf.text_of(entries, P_BTN)
    cs = jf.text_of(entries, P_CS)
    img = jf.text_of(entries, P_IMG)
    btr = jf.text_of(entries, P_BTR)

    if not re.search(r"(?im)^Upgrade\s+Upgrade_Rus_Tigr2\s*$", upg):
        upg = insert_after_block(upg, "Upgrade", "Upgrade_SU39", UPGRADE_BLOCK)
    if not re.search(r"(?im)^CommandButton\s+Command_Upgrade_Rus_Tigr2\s*$", btn):
        btn = insert_after_block(btn, "CommandButton", "Command_Upgrade_SU39", BUTTON_UPG)
    if not re.search(r"(?im)^CommandButton\s+Command_ConstructRussiaVehicleTigr2\s*$", btn):
        btn = insert_after_block(btn, "CommandButton", "Command_ConstructRussiaVehicleBTR82A", BUTTON_BUILD)
    if not re.search(r"(?im)^MappedImage\s+upgrade_rus_tigr2\s*$", img):
        img = insert_after_block(img, "MappedImage", "rus_btr82", IMAGE_BLOCK)

    cs = insert_cs_button(cs, "RussiaIndsturialComplexCommandSet", 5, "Command_Upgrade_Rus_Tigr2")
    cs = insert_cs_button(cs, "RussiaIndsturialComplexCommandSet", 6, "Command_ConstructRussiaVehicleTigr2")
    cs = insert_cs_button(cs, "RussiaWeaponIndustryPlantCommandSet_T", 7, "Command_Upgrade_Rus_Tigr2")
    cs = insert_cs_button(cs, "RussiaWeaponIndustryPlantCommandSet_T1", 7, "Command_Upgrade_Rus_Tigr2")
    cs = insert_cs_button(cs, "RussiaWeaponIndustryPlantCommandSet_T2", 15, "Command_Upgrade_Rus_Tigr2")
    cs = insert_cs_button(cs, "RussiaCommandCenterCommandSet", 11, "Command_ConstructRussiaVehicleTigr2")

    if not re.search(r"(?im)^Object\s+RussiaVehicleTigr2\s*$", btr):
        nl = jf.file_nl(btr)
        tigr = jf.to_nl(make_tigr2_object(btr), nl)
        if not btr.endswith(nl):
            btr += nl
        btr += nl + tigr

    jf.set_text(entries, P_UPG, upg)
    jf.set_text(entries, P_BTN, btn)
    jf.set_text(entries, P_CS, cs)
    jf.set_text(entries, P_IMG, img)
    jf.set_text(entries, P_BTR, btr)

    blob = jf.build_big_ordered(entries)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(blob)
    new_sha = hashlib.sha256(blob).hexdigest()

    packed = jf.read_big_list(OUT_DIR / "_SPEC_DATA_ONE.big")
    pups = jf.text_of(packed, P_UPG)
    pbtn = jf.parse_buttons(jf.text_of(packed, P_BTN))
    pcs = jf.parse_commandsets(jf.text_of(packed, P_CS))
    pbtr = jf.text_of(packed, P_BTR)
    pimg = jf.text_of(packed, P_IMG)

    def cs_buttons(name: str) -> list[str]:
        return re.findall(r"(?im)^\s*\d+\s*=\s*(\S+)", pcs.get(name, ""))

    # objects
    objs = set()
    for n, b in packed:
        t = bytes(b).decode("latin1", "replace")
        if n.lower().endswith(".ini"):
            objs.update(re.findall(r"(?im)^Object\s+(\S+)\s*$", t))

    tigr_obj = "RussiaVehicleTigr2" in objs
    m = re.search(r"(?im)^Object\s+RussiaVehicleTigr2\s*$", pbtr)
    m2 = re.search(r"(?im)^Object\s+\S+", pbtr[m.end() :]) if m else None
    tigr_block = pbtr[m.start() : m.end() + m2.start() if m2 else len(pbtr)] if m else ""
    has_ws_up = bool(re.search(r"(?im)Behavior\s*=\s*WeaponSetUpgrade", tigr_block))
    has_weapons = "30mm_2A72_dualfeed" in tigr_block and "7_62mm_PKT_Coaxial" in tigr_block
    has_armor = "BTR90Armor" in tigr_block
    has_prereq = bool(re.search(r"(?im)^\s*Upgrade\s*=\s*Upgrade_Rus_Tigr2\s*$", tigr_block))
    no_bad_modules = (
        (not has_ws_up)
        and "LocomotorSetUpgrade" not in tigr_block
        and "MaxHealthUpgrade" not in tigr_block
        and "ObjectCreationUpgrade" not in tigr_block
        and "CommandSetUpgrade" not in tigr_block
    )
    # Isolation: no object in DATA may TriggeredBy Upgrade_Rus_Tigr2
    triggered = []
    for n, b in packed:
        t = bytes(b).decode("latin1", "replace")
        if n.lower().endswith(".ini") and re.search(
            r"(?im)^\s*TriggeredBy\s*=\s*Upgrade_Rus_Tigr2\b", t
        ):
            triggered.append(n)
    no_triggered = not triggered
    dup_upg = len(re.findall(r"(?im)^Upgrade\s+Upgrade_Rus_Tigr2\s*$", pups)) == 1
    dup_btn = len(re.findall(r"(?im)^CommandButton\s+Command_Upgrade_Rus_Tigr2\s*$", jf.text_of(packed, P_BTN))) == 1
    obj_hits = 0
    for n, b in packed:
        if n.lower().endswith(".ini"):
            obj_hits += len(re.findall(r"(?im)^Object\s+RussiaVehicleTigr2\s*$", bytes(b).decode("latin1", "replace")))
    dup_obj = obj_hits == 1
    side_ok = bool(re.search(r"(?im)^\s*Side\s*=\s*Russia\s*$", tigr_block))

    def def_exists(kind: str, name: str) -> bool:
        rx = re.compile(rf"(?im)^{kind}\s+{re.escape(name)}\s*$")
        for n, b in packed:
            if n.lower().endswith(".ini") and rx.search(bytes(b).decode("latin1", "replace")):
                return True
        return False

    weapons_ok = def_exists("Weapon", "30mm_2A72_dualfeed") and def_exists("Weapon", "7_62mm_PKT_Coaxial")
    armor_ok = def_exists("Armor", "BTR90Armor")
    loco_ok = def_exists("Locomotor", "TCD_510diesel")
    payload_ok = def_exists("Object", "RussiaMechanizedInfantry")
    cs_ifv_ok = def_exists("CommandSet", "GenericIFVcommandset")
    fx_ok = def_exists("FXList", "FX_CrusaderCatchFire") and def_exists("FXList", "FX_UnguidedRocketExplosion")
    ocl_ok = def_exists("ObjectCreationList", "OCL_BTR90DeathEffect")
    refs_ok = weapons_ok and armor_ok and loco_ok and payload_ok and cs_ifv_ok and fx_ok and ocl_ok and side_ok

    art_path = Path("/workspace/patch/Release/SPECTER1_BUILDING_FLAGS_01/_SPEC_ART_ONE.big")
    art_ok = False
    if art_path.exists():
        art_names = {jf.norm(n).lower() for n, _ in jf.read_big_list(art_path)}
        art_ok = (
            r"art\w3d\rus_btr90.w3d" in art_names
            and r"art\w3d\rus_btr90d.w3d" in art_names
            and r"art\textures\rus_icons05.dds" in art_names
        )

    construct = pbtn.get("Command_ConstructRussiaVehicleTigr2", "")
    construct_ok = "RussiaVehicleTigr2" in construct and "UNIT_BUILD" in construct
    upg_btn = pbtn.get("Command_Upgrade_Rus_Tigr2", "")
    upg_btn_ok = "PLAYER_UPGRADE" in upg_btn and "Upgrade_Rus_Tigr2" in upg_btn
    upg_def = bool(re.search(r"(?im)^Upgrade\s+Upgrade_Rus_Tigr2\s*$", pups))
    img_ok = bool(re.search(r"(?im)^MappedImage\s+upgrade_rus_tigr2\s*$", pimg))
    cs_ok = (
        "Command_Upgrade_Rus_Tigr2" in cs_buttons("RussiaIndsturialComplexCommandSet")
        and "Command_ConstructRussiaVehicleTigr2" in cs_buttons("RussiaIndsturialComplexCommandSet")
        and "Command_ConstructRussiaVehicleTigr2" in cs_buttons("RussiaCommandCenterCommandSet")
    )

    base = {jf.norm(n).lower(): bytes(b) for n, b in jf.read_big_list(SRC_DATA)}
    changed = [n for n, b in packed if base.get(jf.norm(n).lower()) != bytes(b)]
    allowed = {jf.norm(x).lower() for x in (P_UPG, P_BTN, P_CS, P_IMG, P_BTR)}
    if {jf.norm(c).lower() for c in changed} != allowed:
        raise SystemExit(f"unexpected DATA changes: {changed}")

    # WF untouched
    bcs = jf.parse_commandsets(jf.text_of(jf.read_big_list(SRC_DATA), P_CS))
    if pcs.get("RussiaWarFactoryCommandSet") != bcs.get("RussiaWarFactoryCommandSet"):
        raise SystemExit("Russia WF CommandSet changed")

    chain_ok = all(
        [
            upg_def,
            upg_btn_ok,
            cs_ok,
            tigr_obj,
            construct_ok,
            has_weapons,
            has_armor,
            has_prereq,
            no_bad_modules,
            no_triggered,
            dup_upg,
            dup_btn,
            dup_obj,
            img_ok,
            refs_ok,
            art_ok,
        ]
    )
    crash = "FIXED" if chain_ok else "NOT_FIXED"
    checks = {
        "Upgrade definition": upg_def,
        "CommandButton upgrade": upg_btn_ok,
        "CommandButton construct": construct_ok,
        "CommandSet live path": cs_ok,
        "Object RussiaVehicleTigr2": tigr_obj,
        "Weapons on object": has_weapons,
        "Armor on object": has_armor,
        "Prerequisites Upgrade gate": has_prereq,
        "No SU39-style upgrade modules": no_bad_modules,
        "No TriggeredBy Upgrade_Rus_Tigr2": no_triggered,
        "Single Upgrade name": dup_upg,
        "Single CommandButton name": dup_btn,
        "Single Object name": dup_obj,
        "MappedImage": img_ok,
        "Weapon/Armor/Locomotor/FX/OCL/payload/CS defs": refs_ok,
        "ART RUS_BTR90 + rus_Icons05": art_ok,
        "Side=Russia": side_ok,
    }
    check_lines = "\n".join(
        f"  {k} = {'PASS' if v else 'FAIL'}" for k, v in checks.items()
    )

    report = f"""TIGR2_CRASH_TRACE_REPORT

UPGRADE_RUS_TIGR2_CRASH = {crash}

Crash source:
  The previous stub only registered Upgrade_Rus_Tigr2 + Command_Upgrade_Rus_Tigr2
  + MappedImage upgrade_rus_tigr2. It never created Object RussiaVehicleTigr2,
  never added a UNIT_BUILD button, and never put the upgrade on the CommandSet
  Russia actually uses.

  Execution path (Russia start):
    PlayerTemplate FactionRussia StartingBuilding = RussiaCommandCenter
    RussiaDozerCommandSet -> Command_ConstructRussiaIndustrialComplex
    Object RussiaIndustrialComplex
      Side = Russia
      CommandSet = RussiaIndsturialComplexCommandSet   << live upgrade menu
    Stub buttons lived only on RussiaWeaponIndustryPlantCommandSet_T/T1/T2
      which belong to Object RussiaIndustrialComplex_T (Side = China).
    Russia dozer does not build _T. Purchase on the live plant was impossible
    or, if a leftover CommandSet referenced a missing object/module, SAGE
    crashed.

  Working Russia vehicle upgrade (Upgrade_SU39) chain:
    Upgrade Upgrade_SU39
    Command_Upgrade_SU39 PLAYER_UPGRADE on RussiaIndsturialComplexCommandSet slot 1
    Object RussiaJetSU25T modules:
      MaxHealthUpgrade    TriggeredBy = Upgrade_SU39
      WeaponSetUpgrade    TriggeredBy = Upgrade_SU39
      LocomotorSetUpgrade TriggeredBy = Upgrade_SU39
      Draw PLAYER_UPGRADE Model = RUS_SU39
      PLAYER_UPGRADE weapons: 9A1472_Vikhr1_SU39 / KH-29T_Missile_SU39 / ODAB_500_PMV_SU39
    Those modules are SAFE only because the SU39 weapons and RUS_SU39 W3D exist.

  Isolation:
    Disabled (never added) WeaponSetUpgrade / MaxHealthUpgrade /
    LocomotorSetUpgrade / ObjectCreationUpgrade / CommandSetUpgrade on Tigr2.
    No INI contains TriggeredBy = Upgrade_Rus_Tigr2.
    Tigr2 is a BTR82A clone gated by Prerequisites Upgrade = Upgrade_Rus_Tigr2.
    Spawn uses the same weapons/armor/locomotor/W3D as working BTR82A.

Broken file:
  Data\\INI\\Object\\Specter\\Armed Forces Of Russian Federation\\APC\\BTR82A.ini
  (RussiaVehicleTigr2 was absent)
  Data\\INI\\CommandSet.ini
  (RussiaIndsturialComplexCommandSet had no Tigr2 button; stub used _T CS)

Broken object:
  RussiaVehicleTigr2 (missing). No ART W3D named Tigr / GAZ-Tigr.
  Donor: RussiaVehicleBTR82A
    Model RUS_BTR90 / RUS_BTR90D
    Weapons 30mm_2A72_dualfeed + 7_62mm_PKT_Coaxial
    Armor BTR90Armor
    Locomotor TCD_510diesel
    CommandSet GenericIFVcommandset
    Side Russia

Fix applied:
  1. Upgrade Upgrade_Rus_Tigr2 cloned from Upgrade_SU39 (ButtonImage rus_btr82).
  2. Command_Upgrade_Rus_Tigr2 cloned from Command_Upgrade_SU39
     (PLAYER_UPGRADE, OK_FOR_MULTI_SELECT commented off, Border ACTION).
  3. Command_ConstructRussiaVehicleTigr2 UNIT_BUILD -> RussiaVehicleTigr2.
  4. Object RussiaVehicleTigr2 appended to BTR82A.ini as a BTR82A clone.
     Prerequisites Upgrade = Upgrade_Rus_Tigr2. UpgradeCameo1 set.
     ZERO upgrade-triggered modules (the crashy SU39-style ones).
  5. Live CommandSets:
     RussiaIndsturialComplexCommandSet slot 5 upgrade, slot 6 construct
     RussiaCommandCenterCommandSet slot 11 construct (next to BTR82A)
     _T/_T1/_T2 keep the upgrade button only (no construct on China-sided _T).
  6. MappedImage upgrade_rus_tigr2 aliases rus_btr82 texture coords.
  War Factory CommandSet unchanged. ART unchanged.

Test result:
  INGAME_TESTED = NO (no Generals/ZH client in this environment)
  PACK_EXECUTION_PATH = {'PASS' if chain_ok else 'FAIL'}
{check_lines}
  TriggeredBy leftovers = {triggered or 'none'}

DATA SHA256 {new_sha}
ART_CHANGED = NO
"""
    REPORT.write_text(report, encoding="utf-8")
    (OUT_DIR / "TIGR2_CRASH_TRACE_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {new_sha}\nART unchanged\n", encoding="utf-8"
    )
    print(report)
    if crash != "FIXED":
        failed = [k for k, v in checks.items() if not v]
        raise SystemExit(f"chain validation failed: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
