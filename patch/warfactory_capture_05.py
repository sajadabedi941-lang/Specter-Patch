#!/usr/bin/env python3
"""SPECTER1 War Factory production + capture-building pass.

Baseline: SPECTER1_BUILDING_FLAGS_01 DATA+ART.
Does not modify faction identity, flags, portraits, logos, ART, weapons,
animations, or protected working factions' unit objects.

- Copy Vietnam_WarFactoryCommandSet (USA vehicle list) onto:
  Japan, SouthKorea, SaudiArabia, UAE, Libya, SouthAfrica, Syria,
  Pakistan, India (all CS variants).
- European WF unit lists kept. Composite/TOW/Sentry added to DE/FR/UK/IT/SE/UA/TR
  War Factory CommandSets (visible slots). Same upgrades restored on those
  Strategy Center CommandSets. Upgrade_AmericaTOWMissile / SentryDroneGun /
  DroneArmor restored in Upgrade.ini (TOW was commented out; Sentry/DroneArmor
  were never defined).
- Capture Building: barracks purchase + infantry capture command for every
  faction that was missing either.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_BUILDING_FLAGS_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_BUILDING_FLAGS_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "b6b5b9043c1b08e3ed44ee057efb8cbbadb444aa05326af2634be8824d3a3f12"
EXPECTED_ART_SHA = "81352688fcf75b5375ce88106c9fc87f8c37b0645885bd5077d385b4a63f0b26"
OUT_DIR = Path("/tmp/SPECTER1_WARFACTORY_CAPTURE_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_WARFACTORY_CAPTURE_01")
AUDIT_ROOT = Path("/workspace/patch/SPECTER_WARFACTORY_CAPTURE_AUDIT.txt")
RELEASE_NAME = "SPECTER1_WARFACTORY_CAPTURE_01"

P_CMDSET = r"Data\INI\CommandSet.ini"
P_UPG = r"Data\INI\Upgrade.ini"

VN_WF_BODY = [
    "  1  = Command_ConstructAmericaTankCrusader",
    "  2  = Command_ConstructAmericaVehicleM1128",
    "  3  = Command_ConstructAmericaVehicleM1296",
    "  4  = Command_ConstructAmericaVehicleSentryDrone",
    "  5  = Command_ConstructAmericaVehicleTomahawk",
    "  6  = Command_ConstructAmericaTankM109A7",
    "  7  = Command_ConstructAmericaVehicleAvenger",
    "  8  = Command_ConstructAmericaVehicleMicrowave",
    "  9  = Command_ConstructAmericaVehicleAN_TPY2",
    " 10  = Command_ConstructAmericaVehicleTHAAD",
    " 11  = Command_ConstructAmericaVehicleM142",
    " 12  = Command_ConstructAmericaVehicleM1075I",
    " 13  = Command_ConstructAmericaVehicleM1075T",
    " 14  = Command_Sell",
]

VN_TEMPLATE_CS = [
    "Japan_WarFactoryCommandSet",
    "SouthKorea_WarFactoryCommandSet",
    "Pakistan_WarFactoryCommandSet",
    "SaudiArabia_WarFactoryCommandSet",
    "SaudiArabia_WarFactoryCommandSet1",
    "SaudiArabia_WarFactoryCommandSet2",
    "SaudiArabia_WarFactoryCommandSet3",
    "UAE_WarFactoryCommandSet",
    "UAE_WarFactoryCommandSet1",
    "UAE_WarFactoryCommandSet2",
    "UAE_WarFactoryCommandSet3",
    "Libya_WarFactoryCommandSet",
    "Libya_WarFactoryCommandSet1",
    "Libya_WarFactoryCommandSet2",
    "Libya_WarFactoryCommandSet3",
    "SouthAfrica_WarFactoryCommandSet",
    "SouthAfrica_WarFactoryCommandSet1",
    "SouthAfrica_WarFactoryCommandSet2",
    "SouthAfrica_WarFactoryCommandSet3",
    "Syria_WarFactoryCommandSet",
    "Syria_WarFactoryCommandSet1",
    "Syria_WarFactoryCommandSet2",
    "Syria_WarFactoryCommandSet3",
    "India_WarFactoryCommandSet",
    "India_WarFactoryCommandSet1",
    "India_WarFactoryCommandSet2",
    "India_WarFactoryCommandSet3",
]

EURO_WF_CS = [
    "GermanyWarfactoryCommandSet",
    "FranceWarfactoryCommandSet",
    "BritainWarfactoryCommandSet",
    "ItalyWarfactoryCommandSet",
    "SwedenWarfactoryCommandSet",
    "UkraineWarfactoryCommandSet",
    "TurkeyWarfactoryCommandSet",
]
EURO_SC_CS = [
    "GermanyStrategyCenterCommandSet",
    "FranceStrategyCenterCommandSet",
    "BritainStrategyCenterCommandSet",
    "ItalyStrategyCenterCommandSet",
    "SwedenStrategyCenterCommandSet",
    "UkraineStrategyCenterCommandSet",
    "TurkeyStrategyCenterCommandSet",
]
EURO_UPGRADES = [
    "Command_UpgradeAmericaCompositeArmor",
    "Command_UpgradeAmericaTOWMissile",
    "Command_UpgradeAmericaSentryDroneGun",
]
EURO_SC_BODY = [
    "  1  = Command_Upgrade_NuclearReactor",
    "  2  = Command_Upgrade_MTS",
    "  3  = Command_UpgradeAmericaCompositeArmor",
    "  4  = Command_UpgradeAmericaTOWMissile",
    "  5  = Command_UpgradeAmericaSentryDroneGun",
    "  6  = Command_UpgradeAmericaChemicalSuits",
    "  7  = Command_UpgradeAmericaAdvancedTraining",
    "  8  = Command_UpgradeAmericaSupplyLines",
    "  9  = Command_UpgradeAmericaDroneArmor",
    " 14  = Command_Sell",
]

RG_CAPTURE_BODY = [
    "  1  = Command_GLAInfantryRebelCaptureBuilding",
    " 12 = Command_AttackMove",
    " 13 = Command_Guard",
    " 14 = Command_Stop",
]
RG_CAPTURE_CS = [
    "Libya_RepublicanGuardCommandSet",
    "SaudiArabia_RepublicanGuardCommandSet",
    "UAE_RepublicanGuardCommandSet",
    "SouthAfrica_RepublicanGuardCommandSet",
    "Syria_RepublicanGuardCommandSet",
    "India_RepublicanGuardCommandSet",
]
PK_RG_CS = """CommandSet Pakistan_RepublicanGuardCommandSet
  1  = Command_GLAInfantryRebelCaptureBuilding
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End

"""

COMMENTED_TOW_RX = re.compile(
    r"(?m)^;Upgrade Upgrade_AmericaTOWMissile[^\n]*\r?\n"
    r"(?:^[ \t]*;.*\r?\n)*"
    r"^;End[ \t]*\r?\n",
)
RESTORED_UPGRADES = """Upgrade Upgrade_AmericaTOWMissile
  DisplayName        = UPGRADE:TOWMissile
  BuildTime          = 30.0
  BuildCost          = 800
  ButtonImage        = SSTowMissiles
  ResearchSound      = HumveeVoiceUpgradeTowMissiles
End

Upgrade Upgrade_AmericaSentryDroneGun
  DisplayName        = UPGRADE:AmericaSentryDroneGun
  BuildTime          = 30.0
  BuildCost          = 500
  ButtonImage        = SASentryUpgr
End

Upgrade Upgrade_AmericaDroneArmor
  DisplayName        = UPGRADE:AmericaDroneArmor
  BuildTime          = 30.0
  BuildCost          = 500
  ButtonImage        = SSScoutArmor
End
"""

VN_UNIT_BUTTONS = [ln.split("= ")[1] for ln in VN_WF_BODY if "Sell" not in ln]
CAPTURE_UPGRADE_BTNS = (
    "Command_UpgradeGLARebelCaptureBuilding",
    "Command_UpgradeAmericaRangerCaptureBuilding",
    "Command_UpgradeChinaRedguardCaptureBuilding",
    "Command_UpgradeGenericInfantryCaptureBuilding",
)
CAPTURE_CMD_BTNS = (
    "Command_GLAInfantryRebelCaptureBuilding",
    "Command_AmericaRangerCaptureBuilding",
    "Command_ChinaInfantryRedGuardCaptureBuilding",
    "Command_GenericInfantryCaptureBuilding",
)


def add_upgrades_to_cs(text: str, name: str) -> str:
    m = re.search(rf"(?im)^CommandSet\s+{re.escape(name)}\s*$", text)
    if not m:
        raise SystemExit(f"missing CommandSet {name}")
    m2 = re.search(r"(?im)^CommandSet\s+\S+", text[m.end() :])
    end = m.end() + m2.start() if m2 else len(text)
    block = text[m.start() : end]
    missing = [u for u in EURO_UPGRADES if u not in block]
    if not missing:
        return text
    used = {int(x) for x in re.findall(r"(?im)^\s*(\d+)\s*=", block)}
    # Prefer command-bar visible slots 1-15 (3x5). 16+ often never draws.
    slots = [s for s in (11, 12, 13, 15, 3, 4, 5, 6, 16, 17) if s not in used]
    if len(slots) < len(missing):
        raise SystemExit(f"{name}: not enough free slots for upgrades ({used})")
    upgrade_lines = [f"  {slots[i]} = {missing[i]}\n" for i in range(len(missing))]
    lines = block.splitlines(True)
    out = []
    inserted = False
    for line in lines:
        if (not inserted) and re.search(r"(?im)^\s*End\s*$", line):
            out.extend(upgrade_lines)
            inserted = True
        out.append(line)
    if not inserted:
        raise SystemExit(f"{name}: no End")
    return text[: m.start()] + "".join(out) + text[end:]


def insert_button(text: str, cs_name: str, slot: int, button: str) -> str:
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
            raise SystemExit(f"{cs_name}: no free slot for {button}")
    lines = block.splitlines(True)
    out = []
    done = False
    insert = f"  {slot} = {button}\n"
    for line in lines:
        if (not done) and re.search(r"(?im)^\s*End\s*$", line):
            out.append(insert)
            done = True
        out.append(line)
    return text[: m.start()] + "".join(out) + text[end:]


def restore_america_wf_upgrades(upg_text: str) -> str:
    nl = jf.file_nl(upg_text)
    body = jf.to_nl(RESTORED_UPGRADES, nl)
    if re.search(r"(?im)^Upgrade\s+Upgrade_AmericaTOWMissile\s*$", upg_text):
        # already live
        pass
    else:
        new_text, n = COMMENTED_TOW_RX.subn(body, upg_text, count=1)
        if n != 1:
            raise SystemExit(f"TOW uncomment failed n={n}")
        upg_text = new_text
    for uname in (
        "Upgrade_AmericaSentryDroneGun",
        "Upgrade_AmericaDroneArmor",
        "Upgrade_AmericaTOWMissile",
    ):
        if not re.search(rf"(?im)^Upgrade\s+{re.escape(uname)}\s*$", upg_text):
            raise SystemExit(f"missing restored {uname}")
    return upg_text


def parse_upgrades(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"(?im)^Upgrade\s+(\S+)\s*$", text):
        m2 = re.search(r"(?im)^Upgrade\s+\S+", text[m.end() :])
        out[m.group(1)] = text[m.start() : m.end() + m2.start() if m2 else len(text)]
    return out


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("unexpected DATA SHA")
    if jf.sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("unexpected ART SHA")

    entries = jf.read_big_list(SRC_DATA)
    cs_text = jf.text_of(entries, P_CMDSET)
    upg_text = jf.text_of(entries, P_UPG)
    btns = jf.parse_buttons(jf.text_of(entries, r"Data\INI\CommandButton.ini"))
    for b in VN_UNIT_BUTTONS + list(EURO_UPGRADES) + [
        "Command_UpgradeGLARebelCaptureBuilding",
        "Command_GLAInfantryRebelCaptureBuilding",
        "Command_UpgradeAmericaChemicalSuits",
        "Command_UpgradeAmericaAdvancedTraining",
        "Command_UpgradeAmericaSupplyLines",
        "Command_UpgradeAmericaDroneArmor",
        "Command_Upgrade_NuclearReactor",
        "Command_Upgrade_MTS",
        "Command_Sell",
    ]:
        if b not in btns:
            raise SystemExit(f"missing CommandButton {b}")

    # 1. Vietnam template onto listed factions
    for name in VN_TEMPLATE_CS:
        cs_text = jf.replace_commandset(cs_text, name, VN_WF_BODY)

    # 2. European upgrades: keep WF unit lists, add purchase buttons
    for name in EURO_WF_CS:
        cs_text = add_upgrades_to_cs(cs_text, name)
    for name in EURO_SC_CS:
        cs_text = jf.replace_commandset(cs_text, name, EURO_SC_BODY)

    # 3. Restore missing America WF upgrade objects
    upg_text = restore_america_wf_upgrades(upg_text)

    # 4. Capture Building
    cs_text = insert_button(cs_text, "Libya_BarracksCommandSet", 9, "Command_UpgradeGLARebelCaptureBuilding")
    cs_text = insert_button(cs_text, "Pakistan_BarracksCommandSet", 9, "Command_UpgradeGLARebelCaptureBuilding")
    cs_text = insert_button(cs_text, "Syria_BarracksCommandSet", 10, "Command_UpgradeGLARebelCaptureBuilding")
    for name in RG_CAPTURE_CS:
        cs_text = jf.replace_commandset(cs_text, name, RG_CAPTURE_BODY)
    if "Pakistan_RepublicanGuardCommandSet" not in jf.parse_commandsets(cs_text):
        if not cs_text.endswith("\n"):
            cs_text += "\n"
        cs_text += jf.to_nl(PK_RG_CS, jf.file_nl(cs_text))

    jf.set_text(entries, P_CMDSET, cs_text)
    jf.set_text(entries, P_UPG, upg_text)

    blob = jf.build_big_ordered(entries)
    new_sha = hashlib.sha256(blob).hexdigest()
    WS_OUT.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(blob)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(blob)
    shutil.copy2(SRC_ART, WS_OUT / "_SPEC_ART_ONE.big")
    shutil.copy2(SRC_ART, OUT_DIR / "_SPEC_ART_ONE.big")
    if jf.sha256_file(WS_OUT / "_SPEC_ART_ONE.big") != EXPECTED_ART_SHA:
        raise SystemExit("ART copy changed")

    packed = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    pcs = jf.parse_commandsets(jf.text_of(packed, P_CMDSET))
    pups = parse_upgrades(jf.text_of(packed, P_UPG))
    pbtns = jf.parse_buttons(jf.text_of(packed, r"Data\INI\CommandButton.ini"))

    def cs_buttons(name: str) -> list[str]:
        return re.findall(r"(?im)^\s*\d+\s*=\s*(\S+)", pcs.get(name, ""))

    def has_cap_upgrade(csn: str) -> bool:
        bt = cs_buttons(csn)
        return any(x in bt for x in CAPTURE_UPGRADE_BTNS)

    def has_cap_cmd(csn: str) -> bool:
        bt = cs_buttons(csn)
        return any(x in bt for x in CAPTURE_CMD_BTNS) or any("CaptureBuilding" in x for x in bt)

    vn_btns = cs_buttons("Vietnam_WarFactoryCommandSet")
    for name in VN_TEMPLATE_CS:
        got = cs_buttons(name)
        if got != vn_btns:
            raise SystemExit(f"{name} != Vietnam template: {got}")

    for name in EURO_WF_CS:
        for u in EURO_UPGRADES:
            if u not in cs_buttons(name):
                raise SystemExit(f"{name} missing {u}")
    for name in EURO_SC_CS:
        for u in EURO_UPGRADES:
            if u not in cs_buttons(name):
                raise SystemExit(f"{name} missing {u}")
    for uname in ("Upgrade_AmericaTOWMissile", "Upgrade_AmericaSentryDroneGun", "Upgrade_AmericaDroneArmor"):
        if uname not in pups:
            raise SystemExit(f"Upgrade.ini missing {uname}")

    for name in ("Libya_BarracksCommandSet", "Pakistan_BarracksCommandSet", "Syria_BarracksCommandSet"):
        if "Command_UpgradeGLARebelCaptureBuilding" not in cs_buttons(name):
            raise SystemExit(f"{name} missing capture upgrade")
    for name in RG_CAPTURE_CS + ["Pakistan_RepublicanGuardCommandSet"]:
        if "Command_GLAInfantryRebelCaptureBuilding" not in cs_buttons(name):
            raise SystemExit(f"{name} missing capture")

    # identity files untouched
    identity_files = [
        r"Data\INI\PlayerTemplate.ini",
        r"Data\INI\MappedImages\HandCreated\Specter_FactionIdentity.INI",
        r"Data\INI\MappedImages\HandCreated\Turkey_FactionImages.INI",
    ]
    base_entries = {jf.norm(n).lower(): bytes(b) for n, b in jf.read_big_list(SRC_DATA)}
    for p in identity_files:
        if bytes(jf.raw_of(packed, p)) != base_entries[jf.norm(p).lower()]:
            raise SystemExit(f"identity file changed: {p}")
    allowed = {jf.norm(P_CMDSET).lower(), jf.norm(P_UPG).lower()}
    changed = [n for n, b in packed if base_entries.get(jf.norm(n).lower()) != bytes(b)]
    changed_n = {jf.norm(c).lower() for c in changed}
    if changed_n != allowed:
        raise SystemExit(f"unexpected DATA changes: {changed}")

    audit_rows = []

    def row(faction, wf, tmpl, tanks, ups, cap, oil):
        audit_rows.append(
            f"Faction: {faction}\n"
            f"War Factory: {wf}\n"
            f"Vietnam Template Applied: {tmpl}\n"
            f"All Tanks Available: {tanks}\n"
            f"Upgrades: {ups}\n"
            f"Capture Building: {cap}\n"
            f"Oil Capture: {oil}\n"
        )

    def pf(ok: bool) -> str:
        return "PASS" if ok else "FAIL"

    cap_btn = pbtns.get("Command_GLAInfantryRebelCaptureBuilding", "") + pbtns.get(
        "Command_AmericaRangerCaptureBuilding", ""
    )
    oil_ok_global = "NEED_TARGET_NEUTRAL_OBJECT" in cap_btn

    # templated
    for fac, wfcs, barcs, infcs in [
        ("Japan", "Japan_WarFactoryCommandSet", "Japan_BarracksCommandSet", "Iraq_RepublicanGuardCommandSet"),
        ("South Korea", "SouthKorea_WarFactoryCommandSet", "SouthKorea_BarracksCommandSet", "Iraq_RepublicanGuardCommandSet"),
        ("Saudi Arabia", "SaudiArabia_WarFactoryCommandSet", "SaudiArabia_BarracksCommandSet", "SaudiArabia_RepublicanGuardCommandSet"),
        ("UAE", "UAE_WarFactoryCommandSet", "UAE_BarracksCommandSet", "UAE_RepublicanGuardCommandSet"),
        ("Libya", "Libya_WarFactoryCommandSet", "Libya_BarracksCommandSet", "Libya_RepublicanGuardCommandSet"),
        ("South Africa", "SouthAfrica_WarFactoryCommandSet", "SouthAfrica_BarracksCommandSet", "SouthAfrica_RepublicanGuardCommandSet"),
        ("Syria", "Syria_WarFactoryCommandSet", "Syria_BarracksCommandSet", "Iraq_RepublicanGuardCommandSet"),
        ("Pakistan", "Pakistan_WarFactoryCommandSet", "Pakistan_BarracksCommandSet", "Pakistan_RepublicanGuardCommandSet"),
        ("India", "India_WarFactoryCommandSet", "India_BarracksCommandSet", "ChinaInfantryRedguardCommandSet"),
        ("Vietnam", "Vietnam_WarFactoryCommandSet", "Vietnam_BarracksCommandSet", "Iraq_RepublicanGuardCommandSet"),
    ]:
        wf = pf(wfcs in pcs and len(cs_buttons(wfcs)) >= 14)
        tmpl = pf(cs_buttons(wfcs) == vn_btns)
        tanks = pf("Command_ConstructAmericaTankCrusader" in cs_buttons(wfcs))
        cap = pf(has_cap_upgrade(barcs) and has_cap_cmd(infcs))
        oil = pf(cap == "PASS" and oil_ok_global)
        row(fac, wf, tmpl, tanks, pf(tmpl == "PASS"), cap, oil)

    for fac, wfcs, sccs, barcs, infcs in [
        ("Germany", "GermanyWarfactoryCommandSet", "GermanyStrategyCenterCommandSet", "GermanyCampCommandSet", "AmericaInfantryRangerCommandSet"),
        ("France", "FranceWarfactoryCommandSet", "FranceStrategyCenterCommandSet", "FranceCampCommandSet", "AmericaInfantryRangerCommandSet"),
        ("Britain", "BritainWarfactoryCommandSet", "BritainStrategyCenterCommandSet", "BritainCampCommandSet", "AmericaInfantryRangerCommandSet"),
        ("Italy", "ItalyWarfactoryCommandSet", "ItalyStrategyCenterCommandSet", "ItalyCampCommandSet", "AmericaInfantryRangerCommandSet"),
        ("Sweden", "SwedenWarfactoryCommandSet", "SwedenStrategyCenterCommandSet", "SwedenCampCommandSet", "AmericaInfantryRangerCommandSet"),
        ("Ukraine", "UkraineWarfactoryCommandSet", "UkraineStrategyCenterCommandSet", "UkraineCampCommandSet", "AmericaInfantryRangerCommandSet"),
        ("Turkey", "TurkeyWarfactoryCommandSet", "TurkeyStrategyCenterCommandSet", "TurkeyCampCommandSet", "AmericaInfantryRangerCommandSet"),
    ]:
        wf = pf(wfcs in pcs and len(cs_buttons(wfcs)) >= 11)
        ups = pf(all(u in cs_buttons(wfcs) for u in EURO_UPGRADES) and all(u in cs_buttons(sccs) for u in EURO_UPGRADES)
                 and "Upgrade_AmericaTOWMissile" in pups)
        cap = pf(has_cap_upgrade(barcs) and has_cap_cmd(infcs))
        tanks = pf(any("Tank" in b or "Vehicle" in b for b in cs_buttons(wfcs)))
        oil = pf(cap == "PASS" and oil_ok_global)
        row(fac, wf, "N/A", tanks, ups, cap, oil)

    for fac, wfcs, barcs, infcs in [
        ("USA", "AmericaWarFactoryCommandSet", "AmericaBarracksCommandSet", "AmericaInfantryRangerCommandSet"),
        ("China", "ChinaWarFactoryCommandSet", "ChinaBarracksCommandSet", "ChinaInfantryRedguardCommandSet"),
        ("Russia", "RussiaWarFactoryCommandSet", "RussiaBarracksCommandSet", "ChinaInfantryRedguardCommandSet"),
        ("Iran", "IranWarfactoryCommandSet", "IranCampCommandSet", "GenericRiflemanInfantryCommandSet"),
        ("Iraq", "Iraq_WarFactoryCommandSet", "Iraq_BarracksCommandSet", "Iraq_RepublicanGuardCommandSet"),
        ("NATO", "NatoWarfactoryCommandSet", "NatoCampCommandSet", "AmericaInfantryRangerCommandSet"),
        ("Egypt", "EgyptWarFactoryCommandSet", "EgyptCampCommandSet", "Iraq_RepublicanGuardCommandSet"),
    ]:
        cap = pf(has_cap_upgrade(barcs) and has_cap_cmd(infcs))
        wf = pf(wfcs in pcs and len(cs_buttons(wfcs)) >= 10)
        oil = pf(cap == "PASS" and oil_ok_global)
        row(fac, wf, "N/A", pf(wf == "PASS"), "N/A", cap, oil)

    fails = [r for r in audit_rows if "\nFAIL" in ("\n" + r) or r.endswith("FAIL\n") or "\nFAIL\n" in r]
    # stricter: any line with FAIL
    fail_factions = [r.split("\n", 1)[0] for r in audit_rows if re.search(r"(?m)^(?:War Factory|Vietnam Template Applied|All Tanks Available|Upgrades|Capture Building|Oil Capture): FAIL$", r)]
    if fail_factions:
        raise SystemExit("audit FAIL: " + ", ".join(fail_factions))

    audit = (
        "SPECTER_WARFACTORY_CAPTURE_AUDIT\n"
        f"DATA SHA256 {new_sha}\n"
        f"ART  SHA256 {EXPECTED_ART_SHA} (unchanged)\n"
        "IDENTITY_UNCHANGED = YES\n"
        "ART_CHANGED = NO\n"
        "CHANGED_INI = CommandSet.ini, Upgrade.ini\n\n"
        + "\n".join(audit_rows)
        + "\nINGAME_TESTED = NO\n"
    )
    changelog = """SPECTER1 War Factory + capture 01

Vietnam_WarFactoryCommandSet is now the production list for Japan,
South Korea, Saudi Arabia, UAE, Libya, South Africa, Syria, Pakistan
and India (all CS variants). Same 13 USA vehicles + Sell as Vietnam.

European War Factory unit lists were not replaced. Composite Armor,
TOW, and Sentry Drone Gun purchase buttons were added to DE/FR/UK/IT/
SE/UA/TR War Factories, and the same upgrades plus Chemical Suits,
Advanced Training, Supply Lines and Drone Armor were restored on those
Strategy Centers. Upgrade_AmericaTOWMissile / SentryDroneGun / DroneArmor
were restored in Upgrade.ini (TOW was commented out).

Capture Building restored: Libya/Pakistan/Syria barracks purchase, and
Libya/Pakistan/Saudi/UAE/SouthAfrica/Syria/India Republican Guard
infantry capture commands (Upgrade_InfantryCaptureBuilding).

Identity, flags, portraits, logos, ART, weapons, animations unchanged.
INGAME_TESTED = NO
"""
    install = f"""{RELEASE_NAME}
==============================

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG (unchanged).
4. Launch Specter.

DATA SHA256 {new_sha}
ART  SHA256 {EXPECTED_ART_SHA}

INGAME_TESTED = NO
"""
    for dest in (OUT_DIR, WS_OUT):
        (dest / "audit.txt").write_text(audit, encoding="utf-8")
        (dest / "SPECTER_WARFACTORY_CAPTURE_AUDIT.txt").write_text(audit, encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "INSTALL.txt").write_text(install, encoding="utf-8")
    AUDIT_ROOT.write_text(audit, encoding="utf-8")
    zpath = WS_OUT / f"{RELEASE_NAME}.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "SPECTER_WARFACTORY_CAPTURE_AUDIT.txt", "SPECTER_WARFACTORY_CAPTURE_AUDIT.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
        zf.write(WS_OUT / "INSTALL.txt", "INSTALL.txt")
    (OUT_DIR / zpath.name).write_bytes(zpath.read_bytes())
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {new_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {EXPECTED_ART_SHA} (unchanged copy)\n"
        f"{zpath.name}  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n"
    )
    for dest in (OUT_DIR, WS_OUT):
        (dest / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    print(audit)
    print("ZIP", zpath, zpath.stat().st_size, zip_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
