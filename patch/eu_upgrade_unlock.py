#!/usr/bin/env python3
"""SPECTER1 EU faction upgrade unlock on PR #505 WarFactory DATA.

Baseline: SPECTER1_WARFACTORY_BUILD_FIX DATA+ART (PR #505).
Does not modify ART, Weapon.ini, Upgrade.ini, CommandButton.ini, or other factions.
Does not change unit models, weapons, vehicle stats, or building Draw.

Turkey / Ukraine / Italy / Britain / Germany / France only:
- Remove PLAYER_UPGRADE research buttons from those factions' CommandSets
- Auto-grant player upgrades from each faction CommandCenter
- Auto-grant OBJECT control-rod upgrade on each faction PowerStation
- Give PowerStations a unique Sell-only CommandSet (they used America's)
- Strip leftover Science/NeededUpgrade production locks on those objects
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_WARFACTORY_BUILD_FIX/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_WARFACTORY_BUILD_FIX/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "1a4bbd0ff08c3f4c18ea70eb4b4af4d501ef69cdaf7bd77dafef10b1ff31561a"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_EU_UPGRADE_UNLOCK")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_EU_UPGRADE_UNLOCK")

P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_UPGRADE = r"Data\INI\Upgrade.ini"

FACTIONS = (
    ("Turkey", "Turkish Armed Forces", "Turkey"),
    ("Ukraine", "Ukrainian Armed Forces", "Ukraine"),
    ("Italy", "Italian Armed Forces", "Italy"),
    ("Britain", "British Armed Forces", "Britain"),
    ("Germany", "German Armed Forces", "Germany"),
    ("France", "French Armed Forces", "France"),
)

FACTION_FOLDERS = {prefix: folder for prefix, folder, _ in FACTIONS}
FACTION_PREFIXES = tuple(p for p, _, _ in FACTIONS)

RESEARCH_BUTTONS = {
    "Command_UpgradeAmericaCountermeasures",
    "Command_UpgradeAmericaRangerCaptureBuilding",
    "Command_Upgrade_NuclearReactor",
    "Command_Upgrade_MTS",
    "Command_UpgradeAmericaAdvancedControlRods",
    "Command_UpgradeAmericaAdvancedTraining",
    "Command_UpgradeAmericaChemicalSuits",
    "Command_UpgradeAmericaRangerFlashBangGrenade",
}

PLAYER_GRANTS = (
    ("ModuleTag_EUUnlockCM", "Upgrade_AmericaCountermeasures"),
    ("ModuleTag_EUUnlockCapture", "Upgrade_InfantryCaptureBuilding"),
    ("ModuleTag_EUUnlockTraining", "Upgrade_AmericaAdvancedTraining"),
    ("ModuleTag_EUUnlockChem", "Upgrade_AmericaChemicalSuits"),
    ("ModuleTag_EUUnlockFlash", "Upgrade_AmericaRangerFlashBangGrenade"),
    ("ModuleTag_EUUnlockNuke", "Upgrade_NuclearReactor"),
    ("ModuleTag_EUUnlockMTS", "Upgrade_MTS"),
    ("ModuleTag_EUUnlockChaff", "Upgrade_ChaffUpgrade"),
)

MODE_UPGRADES = {
    "Upgrade_AADS_AA_Mode",
    "Upgrade_AADS_ABM_Mode",
    "Upgrade_ICBM_BoosterKiller",
}

OTHER_FACTION_MARKERS = (
    r"\united states of america\\",
    r"\iranian army\\",
    r"\israel defense forces\\",
    r"\nato\\",
    r"\iraq army\\",
    r"\vietnam people's",
    r"\egyptian armed forces\\",
    r"\armed forces of russian federation\\",
    r"\pla\\",
    r"\indian armed forces\\",
    r"\japan self-defense forces\\",
    r"\south korean armed forces\\",
    r"\saudi arabia armed forces\\",
    r"\swedish armed forces\\",
    r"\united arab emirates",
    r"\libyan armed forces\\",
    r"\syrian",
    r"\pakistan armed forces\\",
    r"\south african",
    r"\north korea\\",
)

CC_PATHS = {
    prefix: rf"Data\INI\Object\Specter\{folder}\Buildings\CommandCenter.ini"
    for prefix, folder, _ in FACTIONS
}
PS_PATHS = {
    prefix: rf"Data\INI\Object\Specter\{folder}\Buildings\PowerStation.ini"
    for prefix, folder, _ in FACTIONS
}

PROTECTED_GLOBAL = (P_CMDBTN, P_WEAPON, P_UPGRADE)


def path_faction(name: str) -> str | None:
    ln = name.lower().replace("/", "\\")
    for prefix, folder, _ in FACTIONS:
        if f"\\{folder.lower()}\\" in ln:
            return prefix
    return None


def is_other_faction_path(name: str) -> bool:
    ln = name.lower().replace("/", "\\")
    return any(m in ln for m in OTHER_FACTION_MARKERS)


def parse_objects(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"(?im)^Object\s+(\S+)\s*$", text):
        m2 = re.search(r"(?im)^Object\s+\S+", text[m.end() :])
        out[m.group(1)] = text[m.start() : m.end() + m2.start() if m2 else len(text)]
    return out


def field(block: str, key: str) -> str | None:
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block)
    return m.group(1).strip() if m else None


def cs_buttons(block: str) -> list[str]:
    return re.findall(r"(?im)^\s*\d+\s*=\s*(\S+)", block)


def faction_commandset(name: str) -> str | None:
    for prefix in FACTION_PREFIXES:
        if name.startswith(prefix) or name.startswith(f"SpecialPowerShortcut{prefix}"):
            return prefix
    return None


def insert_grants_after_icbm(text: str, label: str) -> str:
    nl = jf.file_nl(text)
    work = text.replace("\r\n", "\n")
    m = re.search(
        r"(?m)^(  Behavior = GrantUpgradeCreate ModuleTag_ICBMBK\s*$"
        r"\n    UpgradeToGrant = Upgrade_ICBM_BoosterKiller\s*$"
        r"\n  End\s*$)",
        work,
    )
    if not m:
        raise SystemExit(f"{label}: missing GrantUpgradeCreate ModuleTag_ICBMBK")
    for tag, _up in PLAYER_GRANTS:
        if tag in work:
            raise SystemExit(f"{label}: {tag} already present")
    extra_n = "\n".join(
        [
            f"  Behavior = GrantUpgradeCreate {tag}\n    UpgradeToGrant = {up}\n  End"
            for tag, up in PLAYER_GRANTS
        ]
    )
    inserted = work[: m.end()] + "\n" + extra_n + work[m.end() :]
    return jf.to_nl(inserted, nl)


def add_powerstation_control_rods(text: str, label: str) -> str:
    nl = jf.file_nl(text)
    work = text.replace("\r\n", "\n")
    if "ModuleTag_EUUnlockControlRods" in work:
        raise SystemExit(f"{label}: control-rod grant already present")
    if not re.search(r"(?m)^\s*TriggeredBy\s*=\s*Upgrade_AmericaAdvancedControlRods\b", work):
        raise SystemExit(f"{label}: missing ControlRods PowerPlantUpgrade")
    grant = (
        "  Behavior = GrantUpgradeCreate ModuleTag_EUUnlockControlRods\n"
        "    UpgradeToGrant = Upgrade_AmericaAdvancedControlRods\n"
        "    ExemptStatus = UNDER_CONSTRUCTION\n"
        "  End\n"
    )
    rx = re.compile(r"(?m)^  Behavior = PowerPlantUpgrade ModuleTag_07\s*$")
    m = rx.search(work)
    if not m:
        raise SystemExit(f"{label}: missing PowerPlantUpgrade ModuleTag_07")
    work = work[: m.start()] + grant + work[m.start() :]
    work, n = re.subn(
        r"(?m)^(\s*CommandSet\s*=\s*)AmericaPowerPlantCommandSet\b",
        rf"\1{label}PowerStationCommandSet",
        work,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"{label}: PowerStation CommandSet retarget failed n={n}")
    return jf.to_nl(work, nl)


def strip_science_locks(text: str) -> tuple[str, int]:
    n = 0

    def drop(rx: str, s: str) -> str:
        nonlocal n
        s2, c = re.subn(rx, "", s, flags=re.M)
        n += c
        return s2

    text = drop(r"^[ \t]*Science[ \t]*=[ \t]*.*\n", text)
    text = drop(r"^[ \t]*RequiredScience[ \t]*=[ \t]*.*\n", text)
    text = drop(r"^[ \t]*ForbiddenScience[ \t]*=[ \t]*.*\n", text)
    text = drop(r"^[ \t]*NeededUpgrade[ \t]*=[ \t]*.*\n", text)
    return text, n


def strip_object_science(text: str) -> tuple[str, int]:
    matches = list(re.finditer(r"(?im)^Object\s+(\S+)", text))
    if not matches:
        return text, 0
    n = 0
    out = text[: matches[0].start()]
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[m.start() : end]
        block, c = strip_science_locks(block)
        n += c
        out += block
    return out, n


def strip_cs_upgrade_buttons(text: str) -> tuple[str, dict[str, int]]:
    nl = jf.file_nl(text)
    work = text.replace("\r\n", "\n")
    css = jf.parse_commandsets(work)
    removed: dict[str, int] = {}
    for name, block in css.items():
        fac = faction_commandset(name)
        if fac is None:
            continue
        if name.startswith("SpecialPowerShortcut"):
            continue
        lines = block.replace("\r\n", "\n").splitlines()
        new_lines = []
        n_drop = 0
        has_rally = False
        is_airfield = "AirfieldCommandSet" in name and "Large" not in name and "Heavy" not in name
        for ln in lines:
            m = re.match(r"^(\s*)(\d+)\s*=\s*(\S+)\s*$", ln)
            if m:
                btn = m.group(3)
                if btn == "Command_SetRallyPoint":
                    has_rally = True
                if btn in RESEARCH_BUTTONS:
                    n_drop += 1
                    continue
            new_lines.append(ln)
        if is_airfield and not has_rally:
            # Insert SetRallyPoint before Sell if present, else before End.
            inserted = False
            out2 = []
            for ln in new_lines:
                if (not inserted) and re.match(r"^\s*\d+\s*=\s*Command_Sell\b", ln):
                    out2.append("  13 = Command_SetRallyPoint")
                    inserted = True
                out2.append(ln)
            if not inserted:
                out3 = []
                for ln in out2:
                    if (not inserted) and re.match(r"(?i)^\s*End\b", ln):
                        out3.append("  13 = Command_SetRallyPoint")
                        inserted = True
                    out3.append(ln)
                out2 = out3
            new_lines = out2
        if n_drop or (is_airfield and not has_rally):
            body = "\n".join(new_lines).strip() + "\n"
            # replace_commandset wants body lines without header? It rebuilds from name + body_lines.
            # Use direct splice via replace_commandset with remaining slot lines + End stripped.
            slot_lines = [ln for ln in new_lines if re.match(r"^\s*\d+\s*=\s*\S+", ln)]
            work = jf.replace_commandset(work if "\r\n" not in work else work, name, slot_lines)
            # replace_commandset uses file_nl of current text; work is \n so End uses \n.
            removed[name] = n_drop
    return jf.to_nl(work, nl), removed


def add_power_commandsets(text: str) -> str:
    nl = jf.file_nl(text)
    work = text.replace("\r\n", "\n")
    extra = []
    for prefix, _, _ in FACTIONS:
        name = f"{prefix}PowerStationCommandSet"
        if re.search(rf"(?m)^CommandSet\s+{re.escape(name)}\s*$", work):
            raise SystemExit(f"CommandSet {name} already exists")
        extra.append(f"CommandSet {name}\n  14 = Command_Sell\nEnd\n")
    work = work.rstrip() + "\n\n" + "\n".join(extra) + "\n"
    return jf.to_nl(work, nl)


def triggered_values(block: str) -> list[str]:
    vals: list[str] = []
    for m in re.finditer(r"(?im)^\s*TriggeredBy\s*=\s*(.+?)\s*$", block):
        vals.extend(m.group(1).split())
    return vals


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("unexpected DATA SHA — not PR #505 WarFactory BIG")
    if jf.sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("unexpected ART SHA")

    entries = jf.read_big_list(SRC_DATA)
    packed_before = len(entries)
    names_before = [n for n, _ in entries]

    protected_raw = {p: jf.raw_of(entries, p) for p in PROTECTED_GLOBAL}
    other_raw = {
        n: b for n, b in entries if is_other_faction_path(n)
    }

    # 1. CommandSets: strip research buttons, add PowerStation CS.
    cs = jf.text_of(entries, P_CMDSET)
    cs, removed_cs = strip_cs_upgrade_buttons(cs)
    cs = add_power_commandsets(cs)
    jf.set_text(entries, P_CMDSET, cs)

    # 2. CommandCenter auto-grants.
    cc_changed = []
    for prefix, path in CC_PATHS.items():
        old = jf.text_of(entries, path)
        new = insert_grants_after_icbm(old, prefix)
        if new == old:
            raise SystemExit(f"{prefix} CC unchanged")
        jf.set_text(entries, path, new)
        cc_changed.append(path)

    # 3. PowerStation unique CS + OBJECT control-rod grant.
    ps_changed = []
    for prefix, path in PS_PATHS.items():
        old = jf.text_of(entries, path)
        new = add_powerstation_control_rods(old, prefix)
        if new == old:
            raise SystemExit(f"{prefix} PowerStation unchanged")
        jf.set_text(entries, path, new)
        ps_changed.append(path)

    # 4. Strip Science/NeededUpgrade locks in the six faction object INIs.
    science_files = 0
    science_lines = 0
    for n, b in list(entries):
        fac = path_faction(n)
        if not fac or not n.lower().endswith(".ini"):
            continue
        old = b.decode("latin1", errors="replace")
        new, c = strip_object_science(old)
        if c:
            jf.set_text(entries, n, new)
            science_files += 1
            science_lines += c

    # Safety: globals byte-identical.
    for p, raw in protected_raw.items():
        if jf.raw_of(entries, p) != raw:
            raise SystemExit(f"protected global mutated {p}")
    for n, raw in other_raw.items():
        i = jf.find_index(entries, n)
        if entries[i][1] != raw:
            raise SystemExit(f"other-faction file mutated {n}")

    if [n for n, _ in entries] != names_before:
        raise SystemExit("packed path list changed — refusing new Data/Art files")
    if len(entries) != packed_before:
        raise SystemExit("packed file count changed")

    blob = jf.build_big_ordered(entries)
    new_sha = hashlib.sha256(blob).hexdigest()
    if new_sha == EXPECTED_DATA_SHA:
        raise SystemExit("DATA SHA unchanged")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(blob)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(blob)
    shutil.copy2(SRC_ART, OUT_DIR / "_SPEC_ART_ONE.big")
    shutil.copy2(SRC_ART, WS_OUT / "_SPEC_ART_ONE.big")
    if jf.sha256_file(WS_OUT / "_SPEC_ART_ONE.big") != EXPECTED_ART_SHA:
        raise SystemExit("ART copy changed")

    packed = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    cmdset = jf.parse_commandsets(jf.text_of(packed, P_CMDSET))
    cmdbtn = jf.parse_buttons(jf.text_of(packed, P_CMDBTN))

    # Validate: no PLAYER_UPGRADE research buttons remain on the six factions.
    leftover_btn = []
    for name, block in cmdset.items():
        fac = faction_commandset(name)
        if fac is None or name.startswith("SpecialPowerShortcut"):
            continue
        for btn in cs_buttons(block):
            if btn in RESEARCH_BUTTONS:
                leftover_btn.append(f"{name}:{btn}")
            if btn in cmdbtn and field(cmdbtn[btn], "Command") == "PLAYER_UPGRADE":
                leftover_btn.append(f"{name}:{btn}=PLAYER_UPGRADE")
    if leftover_btn:
        raise SystemExit("blocked upgrade buttons remain: " + "; ".join(leftover_btn))

    # Airfields have SetRallyPoint after Countermeasures removal.
    for prefix in ("Turkey", "Ukraine"):
        csname = f"{prefix}AirfieldCommandSet"
        btns = cs_buttons(cmdset[csname])
        if "Command_SetRallyPoint" not in btns:
            raise SystemExit(f"{csname} missing SetRallyPoint")
        if "Command_UpgradeAmericaCountermeasures" in btns:
            raise SystemExit(f"{csname} still has Countermeasures")

    # PowerStation CS unique + Sell only, and America CS untouched.
    if "AmericaPowerPlantCommandSet" not in cmdset:
        raise SystemExit("America power CS missing")
    if "Command_UpgradeAmericaAdvancedControlRods" not in cs_buttons(cmdset["AmericaPowerPlantCommandSet"]):
        raise SystemExit("America control-rod button lost")
    for prefix in FACTION_PREFIXES:
        csname = f"{prefix}PowerStationCommandSet"
        if csname not in cmdset:
            raise SystemExit(f"missing {csname}")
        btns = cs_buttons(cmdset[csname])
        if btns != ["Command_Sell"]:
            raise SystemExit(f"{csname} expected Sell-only, got {btns}")
        pstxt = jf.text_of(packed, PS_PATHS[prefix])
        if f"CommandSet       = {csname}" not in pstxt and not re.search(
            rf"(?im)^\s*CommandSet\s*=\s*{re.escape(csname)}\b", pstxt
        ):
            raise SystemExit(f"{prefix} PowerStation not using {csname}")
        if "AmericaPowerPlantCommandSet" in pstxt:
            raise SystemExit(f"{prefix} PowerStation still uses America CS")
        if "ModuleTag_EUUnlockControlRods" not in pstxt:
            raise SystemExit(f"{prefix} PowerStation missing control-rod grant")

    # CC grants all player upgrades.
    for prefix, path in CC_PATHS.items():
        txt = jf.text_of(packed, path)
        for tag, up in PLAYER_GRANTS:
            if tag not in txt or up not in txt:
                raise SystemExit(f"{prefix} CC missing grant {up}")
        if "ModuleTag_ICBMBK" not in txt:
            raise SystemExit(f"{prefix} CC lost ICBM grant")

    # No Science/NeededUpgrade left on the six factions' objects.
    leftover_sci = []
    leftover_prereq_up = []
    remaining_triggered: dict[str, set[str]] = {p: set() for p in FACTION_PREFIXES}
    for n, b in packed:
        fac = path_faction(n)
        if not fac or not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", errors="replace")
        for oname, blk in parse_objects(t).items():
            if re.search(r"(?im)^\s*(Science|RequiredScience|ForbiddenScience|NeededUpgrade)\s*=", blk):
                leftover_sci.append(f"{fac}:{oname}")
            in_prereq = False
            for line in blk.splitlines():
                if re.match(r"(?i)^\s*Prerequisites\b", line):
                    in_prereq = True
                elif in_prereq and re.match(r"(?i)^\s*End\b", line):
                    in_prereq = False
                elif in_prereq and re.match(r"(?i)^\s*Upgrade\s*=", line):
                    leftover_prereq_up.append(f"{fac}:{oname}:{line.strip()}")
            for v in triggered_values(blk):
                remaining_triggered[fac].add(v)
    if leftover_sci:
        raise SystemExit("science locks remain: " + ", ".join(leftover_sci[:20]))
    if leftover_prereq_up:
        raise SystemExit("prereq Upgrade= remain: " + ", ".join(leftover_prereq_up[:20]))

    expected_triggered = MODE_UPGRADES | {
        "Upgrade_AmericaCountermeasures",
        "Upgrade_InfantryCaptureBuilding",
        "Upgrade_AmericaAdvancedTraining",
        "Upgrade_AmericaChemicalSuits",
        "Upgrade_AmericaRangerFlashBangGrenade",
        "Upgrade_NuclearReactor",
        "Upgrade_MTS",
        "Upgrade_ChaffUpgrade",
        "Upgrade_AmericaRadar",
        "Upgrade_AmericaAdvancedControlRods",
    }
    unexpected = []
    for fac, vals in remaining_triggered.items():
        extra = vals - expected_triggered
        missing_mode = MODE_UPGRADES - vals
        if extra:
            unexpected.append(f"{fac} extra TriggeredBy {sorted(extra)}")
        if missing_mode:
            unexpected.append(f"{fac} lost mode TriggeredBy {sorted(missing_mode)}")
    if unexpected:
        raise SystemExit("TriggeredBy unexpected: " + " | ".join(unexpected))

    # Other-faction objects still byte-identical vs source BIG.
    src_entries = jf.read_big_list(SRC_DATA)
    src_map = {jf.norm(n).lower(): b for n, b in src_entries}
    packed_map = {jf.norm(n).lower(): b for n, b in packed}
    for n, b in src_entries:
        if is_other_faction_path(n):
            if packed_map[jf.norm(n).lower()] != b:
                raise SystemExit(f"other faction mutated after pack {n}")
    if jf.raw_of(packed, P_WEAPON) != jf.raw_of(src_entries, P_WEAPON):
        raise SystemExit("Weapon.ini changed")
    if jf.raw_of(packed, P_UPGRADE) != jf.raw_of(src_entries, P_UPGRADE):
        raise SystemExit("Upgrade.ini changed")
    if jf.raw_of(packed, P_CMDBTN) != jf.raw_of(src_entries, P_CMDBTN):
        raise SystemExit("CommandButton.ini changed")

    # Turkey WF CS from PR #505 still native.
    tur_wf = cs_buttons(cmdset["TurkeyWarfactoryCommandSet"])
    if "Command_ConstructTurkeyTankLeopard2A7Plus" not in tur_wf:
        raise SystemExit("Turkey WF CS reverted")

    # Packed path count / ART file count.
    if len(packed) != packed_before:
        raise SystemExit("packed count drift")

    grant_list = ", ".join(up for _, up in PLAYER_GRANTS)
    removed_txt = ", ".join(f"{k}(-{v})" for k, v in sorted(removed_cs.items())) or "(none)"

    lines = [
        "SPECTER1 EU UPGRADE UNLOCK",
        f"BASELINE = SPECTER1_WARFACTORY_BUILD_FIX / PR #505",
        f"BASELINE_DATA_SHA256 = {EXPECTED_DATA_SHA}",
        f"NEW_DATA_SHA256 = {new_sha}",
        f"ART_SHA256 = {EXPECTED_ART_SHA} (unchanged copy)",
        "ART_CHANGED = NO",
        "WEAPON_INI_CHANGED = NO",
        "UPGRADE_INI_CHANGED = NO",
        "COMMANDBUTTON_INI_CHANGED = NO",
        "OTHER_FACTIONS_UNCHANGED = YES",
        "PACKED_FILE_COUNT_UNCHANGED = YES",
        "NEW_DATA_OR_ART_FOLDERS = NO",
        "FACTIONS = Turkey, Ukraine, Italy, United Kingdom (Britain), Germany, France",
        "",
        "RESEARCH_BUTTONS_REMOVED = " + removed_txt,
        "COMMANDCENTER_PLAYER_GRANTS = " + grant_list,
        "POWERSTATION = unique Sell-only CommandSet + GrantUpgradeCreate Upgrade_AmericaAdvancedControlRods",
        f"SCIENCE_LOCKS_STRIPPED = files={science_files} lines={science_lines}",
        "PREREQ_UPGRADE = none were present; none remain",
        "MODE_UPGRADES_KEPT = Upgrade_AADS_AA_Mode, Upgrade_AADS_ABM_Mode, Upgrade_ICBM_BoosterKiller",
        "UNIT_MODELS_CHANGED = NO",
        "BUILDING_DRAW_CHANGED = NO",
        "VEHICLE_STATS_CHANGED = NO",
        "",
        "BLOCKED_UPGRADES_REMAIN = NO",
        "INGAME_TESTED = NO",
        "DATA_CHANGED = YES",
        "ART_CHANGED = NO",
    ]
    audit = "\n".join(lines) + "\n"

    changelog = """SPECTER1 EU upgrade unlock

Continues from SPECTER1_WARFACTORY_BUILD_FIX (PR #505). Does not revert WarFactory
Draw/CommandSet work. Does not modify ART, Weapon.ini, Upgrade.ini, CommandButton.ini,
unit models, weapons, vehicle stats, or other factions.

Removes faction upgrade restrictions for Turkey, Ukraine, Italy, United Kingdom,
Germany, and France:

1. PLAYER_UPGRADE research buttons removed from those factions' CommandSets
   (Countermeasures, Capture Building, Nuclear Reactor, MTS). Turkey/Ukraine
   airfields gain SetRallyPoint in the freed slot, matching the other four.
2. Each faction CommandCenter auto-grants the player upgrades those modules
   were waiting on, so upgraded loadouts/armor/flares/capture/training/MTS
   apply without research cost or timer.
3. PowerStations no longer use AmericaPowerPlantCommandSet. Unique Sell-only
   CommandSets plus an OBJECT GrantUpgradeCreate so control rods are not a
   locked America-shared research button.
4. Leftover Science/NeededUpgrade production locks stripped on those six
   factions' objects (Turkey still had rank/science unit gates).

AADS AA/ABM mode toggles and the existing ICBM_BoosterKiller grant are kept
(they are not research trees). Upgrade templates stay in Upgrade.ini so other
factions are unchanged.

INGAME_TESTED = NO
"""

    install = f"""SPECTER1_EU_UPGRADE_UNLOCK
==========================

Upgrade-restriction removal for Turkey, Ukraine, Italy, United Kingdom,
Germany, and France on the SPECTER1_WARFACTORY_BUILD_FIX (PR #505) baseline.
ART, weapons, models, vehicle stats, buildings Draw, and other factions are
unchanged. Same GameRoot layout as PR #505: two BIG files, no loose Data/Art.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
   ART is an unchanged copy of the PR #505 ART pack.
4. Launch Specter.

Do not mix this DATA with older SPECTER1 roster ZIPs.
Do not extract a Data or Art folder. GameRoot is generals.exe plus the two BIGs.

Checksums:
  DATA SHA256 {new_sha}
  ART  SHA256 {EXPECTED_ART_SHA}

EU_UPGRADES_REMOVED = YES
BLOCKED_UPGRADES_REMAIN = NO
INGAME_TESTED = NO
"""
    for dest in (OUT_DIR, WS_OUT):
        (dest / "audit.txt").write_text(audit, encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "INSTALL.txt").write_text(install, encoding="utf-8")

    zpath = WS_OUT / "SPECTER1_EU_Upgrade_Unlock.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
        zf.write(WS_OUT / "INSTALL.txt", "INSTALL.txt")
    (OUT_DIR / zpath.name).write_bytes(zpath.read_bytes())
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {new_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {EXPECTED_ART_SHA} (unchanged copy)\n"
        f"SPECTER1_EU_Upgrade_Unlock.zip  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n"
    )
    for dest in (OUT_DIR, WS_OUT):
        (dest / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", new_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    print("REMOVED_CS", removed_cs)
    print("SCIENCE", science_files, science_lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
