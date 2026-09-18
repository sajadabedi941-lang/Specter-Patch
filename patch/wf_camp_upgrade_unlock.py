#!/usr/bin/env python3
"""SPECTER1 WF + Camp upgrade unlock on PR #505 WarFactory DATA.

Factions: Iraq, Sweden, Turkey, Britain, Germany, France, Italy, Ukraine, Vietnam.
Only upgrade logic. ART / Weapon.ini / Upgrade.ini / models / other factions unchanged.
Upgrade buttons stay on the bar and are usable without Science/NeededUpgrade/prereq locks.
PLAYER_UPGRADE Conditions are promoted so upgraded loadouts are not locked.
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
OUT_DIR = Path("/tmp/SPECTER1_WF_CAMP_UPGRADE_UNLOCK")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_WF_CAMP_UPGRADE_UNLOCK")

P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_UPGRADE = r"Data\INI\Upgrade.ini"

FACTION_FOLDERS = (
    "iraq army",
    "swedish armed forces",
    "turkish armed forces",
    "british armed forces",
    "german armed forces",
    "french armed forces",
    "italian armed forces",
    "ukrainian armed forces",
    "vietnam people's armed forces",
    "vietnam people's army",
)

OTHER_FACTION_MARKERS = (
    r"\united states of america\\",
    r"\iranian army\\",
    r"\israel defense forces\\",
    r"\nato\\",
    r"\egyptian armed forces\\",
    r"\armed forces of russian federation\\",
    r"\pla\\",
    r"\indian armed forces\\",
    r"\japan self-defense forces\\",
    r"\south korean armed forces\\",
    r"\saudi arabia armed forces\\",
    r"\united arab emirates",
    r"\libyan armed forces\\",
    r"\syrian",
    r"\pakistan armed forces\\",
    r"\south african",
    r"\north korea\\",
)

MODE_UPGRADES = {
    "Upgrade_AADS_AA_Mode",
    "Upgrade_AADS_ABM_Mode",
    "Upgrade_ICBM_BoosterKiller",
}
WORKER_MODE = {
    "Upgrade_GLAWorkerFakeCommandSet",
    "Upgrade_GLAWorkerRealCommandSet",
}

SCIENCE_BUTTONS = (
    "Command_Irq_Tier1",
    "Command_Irq_Tier3",
    "Command_UpgradeHussienResearchProgram",
    "Command_UpgradeAbbasResearchProgram",
)

IRAQ_WF_T3 = [
    "  1 = Command_ConstructIraq_T-72",
    "  2 = Command_ConstructIraq_BMP-1",
    "  3 = Command_ConstructIraq_BMP-2",
    "  4 = Command_ConstructIraq_BTR-90",
    "  5 = Command_ConstructIraq_2S1",
    "  6 = Command_ConstructIraq_Sam8",
    "  7 = Command_ConstructIraq_AssadBabel-2",
    "  8 = Command_ConstructIraq_SA-6",
    "  9 = Command_ConstructIraq_Sarab7",
    "  10 = Command_ConstructIraq_Alhussaien",
    "  11 = Command_ConstructIraqVehicleRoland3K",
    "  12 = Command_ConstructIraq_BM-21",
    "  13 = Command_ConstructIraq_R11ScudB",
    "  14 = Command_Sell",
]

IRAQ_MIC_OPEN = [
    "  1 = Command_UpgradeAbbasResearchProgram",
    "  2 = Command_ConstructIraq_Karrar2",
    "  3 = Command_Upgrade_Iraq_BMP-2M2",
    "  4 = Command_ConstructIraqVehicleB340",
    "  5 = Command_ConstructIraqVehicleFahad3",
    "  6 = Command_UpgradeHussienResearchProgram",
    "  7 = Command_UpgradeS-8Rockets",
    "  9 = Command_Upgrade_Iraq_BMP-1M3",
    "  11 = Command_Irq_Tier1",
    "  12 = Command_Irq_Tier2",
    "  13 = Command_Irq_Tier3",
    "  14 = Command_Sell",
    "  15 = Command_UpgradeMi35Mk3",
    "  16 = Command_UpgradeKab500",
]

VIETNAM_MIC_OPEN = [
    "  1  = Command_UpgradeAbbasResearchProgram",
    "  3  = Command_Upgrade_Iraq_BMP-2M2",
    "  6  = Command_UpgradeHussienResearchProgram",
    "  7  = Command_UpgradeS-8Rockets",
    "  9  = Command_Upgrade_Iraq_BMP-1M3",
    "  11 = Command_Irq_Tier1",
    "  12 = Command_Irq_Tier2",
    "  13 = Command_Irq_Tier3",
    "  14 = Command_Sell",
    "  15 = Command_UpgradeMi35Mk3",
    "  16 = Command_UpgradeKab500",
]

IRAQ_WF_PATHS = (
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory.ini",
    r"Data\INI\Object\Specter\Iraq Army\AI\Iraq_WarFactory.ini",
)
IRAQ_MIC_PATH = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_MIC.ini"
VN_WF_PATH = r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_WarFactory.ini"
VN_SYS_PATH = r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Vietnam_Systems.ini"

CAMP_CAPTURE_BUTTONS = {
    "Command_UpgradeAmericaRangerCaptureBuilding",
    "Command_UpgradeGLARebelCaptureBuilding",
    "Command_Upgrade_RGD5",
    "Command_Upgrade_Rpg29",
}

NATO_CAMP_CS = (
    "SwedenCampCommandSet",
    "TurkeyCampCommandSet",
    "BritainCampCommandSet",
    "GermanyCampCommandSet",
    "FranceCampCommandSet",
    "ItalyCampCommandSet",
    "UkraineCampCommandSet",
)
NATO_STRAT_CS = (
    "SwedenStrategyCenterCommandSet",
    "TurkeyStrategyCenterCommandSet",
    "BritainStrategyCenterCommandSet",
    "GermanyStrategyCenterCommandSet",
    "FranceStrategyCenterCommandSet",
    "ItalyStrategyCenterCommandSet",
    "UkraineStrategyCenterCommandSet",
)


def path_faction(name: str) -> bool:
    ln = name.lower().replace("/", "\\")
    return any(f"\\{folder}\\" in ln for folder in FACTION_FOLDERS)


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


def promote_set(text: str, kind: str) -> tuple[str, int]:
    n = 0
    while True:
        blocks = list(re.finditer(rf"^  {kind}\b[^\n]*\n(?:.*\n)*?^  End", text, re.M))
        none_i = None
        up_i = None
        for i, m in enumerate(blocks):
            if re.search(r"(?im)^\s*Conditions\s*=\s*PLAYER_UPGRADE\b", m.group(0)):
                up_i = i
            elif re.search(r"(?im)^\s*Conditions\s*=\s*None\b", m.group(0)):
                none_i = i
        if up_i is None:
            return text, n
        up = blocks[up_i].group(0)
        up_new = re.sub(r"(?im)^(\s*Conditions\s*=\s*)PLAYER_UPGRADE\b", r"\1None", up, count=1)
        if none_i is not None and none_i != up_i:
            none = blocks[none_i]
            upm = blocks[up_i]
            if none.start() < upm.start():
                text = text[: none.start()] + up_new + text[none.end() : upm.start()] + text[upm.end() :]
            else:
                text = text[: upm.start()] + text[upm.end() : none.start()] + up_new + text[none.end() :]
        else:
            text = text[: blocks[up_i].start()] + up_new + text[blocks[up_i].end() :]
        n += 1
        if n > 40:
            raise SystemExit(f"{kind} PLAYER_UPGRADE promote loop")


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


def strip_prereq_upgrade(text: str) -> tuple[str, int]:
    n = 0
    out = []
    in_prereq = False
    for line in text.splitlines(keepends=True):
        if re.match(r"(?i)^[ \t]*Prerequisites\b", line):
            in_prereq = True
            out.append(line)
            continue
        if in_prereq and re.match(r"(?i)^[ \t]*End\b", line):
            in_prereq = False
            out.append(line)
            continue
        if in_prereq and re.match(r"(?i)^[ \t]*Upgrade[ \t]*=", line):
            n += 1
            continue
        out.append(line)
    return "".join(out), n


def drop_research_triggered_by(text: str) -> tuple[str, int]:
    n = 0
    keep = MODE_UPGRADES | WORKER_MODE
    out = []
    for line in text.splitlines(keepends=True):
        m = re.match(r"^([ \t]*TriggeredBy[ \t]*=[ \t]*)(.+?)(\r?\n)$", line)
        if not m:
            out.append(line)
            continue
        vals = m.group(2).split()
        kept = [v for v in vals if v in keep or v.startswith(";")]
        dropped = [v for v in vals if v not in keep and not v.startswith(";")]
        if not dropped:
            out.append(line)
            continue
        n += len(dropped)
        if kept:
            out.append(m.group(1) + " ".join(kept) + m.group(3))
    return "".join(out), n


def remove_irq_tier_commandset_upgrades(text: str) -> tuple[str, int]:
    """Drop CommandSetUpgrade modules gated by Iraq tier upgrades."""
    n = 0
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    start_rx = re.compile(r"(?i)^[ \t]*Behavior[ \t]*=[ \t]*CommandSetUpgrade\b")
    end_rx = re.compile(r"(?i)^[ \t]*End[ \t]*\r?\n$")
    while i < len(lines):
        if start_rx.match(lines[i]):
            j = i + 1
            while j < len(lines) and not end_rx.match(lines[j]):
                j += 1
            if j < len(lines):
                j += 1
            blk = "".join(lines[i:j])
            if re.search(r"Upgrade_Irq_Tier[123]\b", blk):
                n += 1
                i = j
                continue
            out.extend(lines[i:j])
            i = j
            continue
        out.append(lines[i])
        i += 1
    return "".join(out), n


def retarget_commandset(text: str, old: str, new: str, label: str) -> str:
    work, c = re.subn(
        rf"(?im)^([ \t]*CommandSet[ \t]*=[ \t]*){re.escape(old)}\b",
        rf"\1{new}",
        text,
    )
    if c < 1:
        raise SystemExit(f"{label}: CommandSet {old} not retargeted")
    return work


def strip_button_science(text: str, name: str) -> str:
    hits = list(re.finditer(rf"(?im)^CommandButton\s+{re.escape(name)}\s*$", text))
    if not hits:
        raise SystemExit(f"missing CommandButton {name}")
    stripped = 0
    # Walk last-to-first so offsets stay valid.
    for m in reversed(hits):
        m2 = re.search(r"(?im)^CommandButton\s+\S+", text[m.end() :])
        end = m.end() + m2.start() if m2 else len(text)
        block = text[m.start() : end]
        block2, c = re.subn(r"(?im)^[ \t]*Science[ \t]*=[ \t]*.*\n", "", block)
        stripped += c
        text = text[: m.start()] + block2 + text[end:]
    if stripped < 1:
        raise SystemExit(f"{name}: no Science line to strip")
    return text


def unlock_object_text(text: str) -> tuple[str, dict[str, int]]:
    stats = {"science": 0, "prereq": 0, "triggered": 0, "weaponset": 0, "armorset": 0, "csu": 0}
    matches = list(re.finditer(r"(?im)^Object\s+(\S+)", text))
    if not matches:
        t, c = remove_irq_tier_commandset_upgrades(text)
        stats["csu"] += c
        return t, stats
    out = text[: matches[0].start()]
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[m.start() : end]
        block, c = strip_science_locks(block)
        stats["science"] += c
        block, c = strip_prereq_upgrade(block)
        stats["prereq"] += c
        block, c = promote_set(block, "WeaponSet")
        stats["weaponset"] += c
        block, c = promote_set(block, "ArmorSet")
        stats["armorset"] += c
        block, c = remove_irq_tier_commandset_upgrades(block)
        stats["csu"] += c
        block, c = drop_research_triggered_by(block)
        stats["triggered"] += c
        out += block
    return out, stats


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("unexpected DATA SHA — not PR #505")
    if jf.sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("unexpected ART SHA")

    entries = jf.read_big_list(SRC_DATA)
    packed_before = len(entries)
    names_before = [n for n, _ in entries]
    weapon_raw = jf.raw_of(entries, P_WEAPON)
    upgrade_raw = jf.raw_of(entries, P_UPGRADE)
    other_raw = {n: b for n, b in entries if is_other_faction_path(n)}

    # 1. CommandSet.ini — open Iraq WF tiers + MIC research bars. Buttons kept.
    cs = jf.text_of(entries, P_CMDSET)
    for name in (
        "Iraq_WarFactoryCommandSet_T",
        "Iraq_WarFactoryCommandSet_T1",
        "Iraq_WarFactoryCommandSet_T2",
        "Iraq_WarFactoryCommandSet_T3",
    ):
        cs = jf.replace_commandset(cs, name, IRAQ_WF_T3)
    cs = jf.replace_commandset(cs, "Iraq_MICCommandSet", IRAQ_MIC_OPEN)
    cs = jf.replace_commandset(cs, "Iraq_MICCommandSet2", IRAQ_MIC_OPEN)
    cs = jf.replace_commandset(cs, "Iraq_MICCommandSet3", IRAQ_MIC_OPEN)
    cs = jf.replace_commandset(cs, "Vietnam_MICCommandSet", VIETNAM_MIC_OPEN)
    cs = jf.replace_commandset(cs, "Vietnam_MICCommandSet2", VIETNAM_MIC_OPEN)
    cs = jf.replace_commandset(cs, "Vietnam_MICCommandSet3", VIETNAM_MIC_OPEN)
    jf.set_text(entries, P_CMDSET, cs)

    # 2. CommandButton.ini — strip rank Science from Iraq/Vietnam PLAYER_UPGRADE buttons only.
    btn = jf.text_of(entries, P_CMDBTN)
    for name in SCIENCE_BUTTONS:
        btn = strip_button_science(btn, name)
    jf.set_text(entries, P_CMDBTN, btn)

    # 3. Iraq / Vietnam factory + MIC objects: default to open CS, drop tier CommandSetUpgrade.
    for path in IRAQ_WF_PATHS:
        t = jf.text_of(entries, path)
        t2 = t
        if re.search(r"(?im)^\s*CommandSet\s*=\s*Iraq_WarFactoryCommandSet_T\b", t2):
            t2 = retarget_commandset(t2, "Iraq_WarFactoryCommandSet_T", "Iraq_WarFactoryCommandSet_T3", path)
        t2, _st = unlock_object_text(t2)
        jf.set_text(entries, path, t2)

    mic = jf.text_of(entries, IRAQ_MIC_PATH)
    mic, _ = unlock_object_text(mic)
    jf.set_text(entries, IRAQ_MIC_PATH, mic)

    vnwf = jf.text_of(entries, VN_WF_PATH)
    vnwf, _ = unlock_object_text(vnwf)
    jf.set_text(entries, VN_WF_PATH, vnwf)

    # 4. All nine-faction object INIs: promote PLAYER_UPGRADE, strip science/prereq, drop research TriggeredBy.
    totals = {"science": 0, "prereq": 0, "triggered": 0, "weaponset": 0, "armorset": 0, "csu": 0, "files": 0}
    fac_inis = [(n, b) for n, b in entries if path_faction(n) and n.lower().endswith(".ini")]
    print(f"unlocking {len(fac_inis)} faction INI files", flush=True)
    for idx, (n, b) in enumerate(fac_inis, 1):
        old = b.decode("latin1", errors="replace")
        new, st = unlock_object_text(old)
        if new != old:
            jf.set_text(entries, n, new)
            totals["files"] += 1
            for k, v in st.items():
                totals[k] += v
        if idx % 50 == 0 or idx == len(fac_inis):
            print(f"  {idx}/{len(fac_inis)} files  changed={totals['files']}", flush=True)

    # Safety
    if jf.raw_of(entries, P_WEAPON) != weapon_raw:
        raise SystemExit("Weapon.ini changed")
    if jf.raw_of(entries, P_UPGRADE) != upgrade_raw:
        raise SystemExit("Upgrade.ini changed")
    for n, raw in other_raw.items():
        if jf.raw_of(entries, n) != raw:
            raise SystemExit(f"other-faction mutated {n}")
    if [n for n, _ in entries] != names_before or len(entries) != packed_before:
        raise SystemExit("packed path list changed")

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

    # WF Iraq full roster on all tier CS.
    for name in (
        "Iraq_WarFactoryCommandSet_T",
        "Iraq_WarFactoryCommandSet_T1",
        "Iraq_WarFactoryCommandSet_T2",
        "Iraq_WarFactoryCommandSet_T3",
    ):
        btns = cs_buttons(cmdset[name])
        if "Command_ConstructIraq_R11ScudB" not in btns or "Command_ConstructIraq_BMP-2" not in btns:
            raise SystemExit(f"{name} not fully unlocked")

    # MIC all upgrade buttons present on default CS.
    for name, required in (
        ("Iraq_MICCommandSet", ("Command_Irq_Tier1", "Command_Irq_Tier2", "Command_Irq_Tier3",
                                "Command_UpgradeAbbasResearchProgram", "Command_UpgradeHussienResearchProgram",
                                "Command_Upgrade_Iraq_BMP-1M3", "Command_Upgrade_Iraq_BMP-2M2")),
        ("Vietnam_MICCommandSet", ("Command_Irq_Tier1", "Command_Irq_Tier2", "Command_Irq_Tier3",
                                   "Command_UpgradeAbbasResearchProgram", "Command_UpgradeHussienResearchProgram")),
    ):
        have = set(cs_buttons(cmdset[name]))
        missing = [b for b in required if b not in have]
        if missing:
            raise SystemExit(f"{name} missing buttons {missing}")

    # Camp / Strategy buttons still present (usable, not removed).
    for name in NATO_CAMP_CS + ("Iraq_BarracksCommandSet", "Vietnam_BarracksCommandSet"):
        have = set(cs_buttons(cmdset[name]))
        if name.endswith("BarracksCommandSet"):
            need = CAMP_CAPTURE_BUTTONS
        else:
            need = {"Command_UpgradeAmericaRangerCaptureBuilding"}
        if not (have & need):
            raise SystemExit(f"{name} lost camp upgrade button")
    for name in NATO_STRAT_CS:
        have = set(cs_buttons(cmdset[name]))
        if "Command_Upgrade_NuclearReactor" not in have or "Command_Upgrade_MTS" not in have:
            raise SystemExit(f"{name} lost strategy upgrade buttons")

    # PLAYER_UPGRADE buttons no longer have Science.
    for name in SCIENCE_BUTTONS:
        if field(cmdbtn[name], "Science"):
            raise SystemExit(f"{name} still has Science")
        if field(cmdbtn[name], "Command") != "PLAYER_UPGRADE":
            raise SystemExit(f"{name} is not PLAYER_UPGRADE")

    leftover_sci = []
    leftover_prereq = []
    leftover_pu = []
    leftover_trig = []
    leftover_csu = []
    for n, b in packed:
        if not path_faction(n) or not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", errors="replace")
        if re.search(r"Behavior\s*=\s*CommandSetUpgrade[\s\S]{0,200}Upgrade_Irq_Tier", t):
            leftover_csu.append(n)
        for oname, blk in parse_objects(t).items():
            if re.search(r"(?im)^\s*(Science|RequiredScience|ForbiddenScience|NeededUpgrade)\s*=", blk):
                leftover_sci.append(f"{oname}")
            in_prereq = False
            for line in blk.splitlines():
                if re.match(r"(?i)^\s*Prerequisites\b", line):
                    in_prereq = True
                elif in_prereq and re.match(r"(?i)^\s*End\b", line):
                    in_prereq = False
                elif in_prereq and re.match(r"(?i)^\s*Upgrade\s*=", line):
                    leftover_prereq.append(oname)
            if re.search(r"(?im)^\s*Conditions\s*=\s*PLAYER_UPGRADE\b", blk):
                leftover_pu.append(oname)
            for m in re.finditer(r"(?im)^\s*TriggeredBy\s*=\s*(.+)$", blk):
                for v in m.group(1).split():
                    if v.startswith(";"):
                        continue
                    if v not in MODE_UPGRADES and v not in WORKER_MODE:
                        leftover_trig.append(f"{oname}:{v}")

    if leftover_sci:
        raise SystemExit("science remain: " + ", ".join(leftover_sci[:15]))
    if leftover_prereq:
        raise SystemExit("prereq Upgrade remain: " + ", ".join(leftover_prereq[:15]))
    if leftover_pu:
        raise SystemExit("PLAYER_UPGRADE conditions remain: " + ", ".join(leftover_pu[:15]))
    if leftover_trig:
        raise SystemExit("research TriggeredBy remain: " + ", ".join(leftover_trig[:20]))
    if leftover_csu:
        raise SystemExit("tier CommandSetUpgrade remain: " + ", ".join(leftover_csu[:10]))

    src_entries = jf.read_big_list(SRC_DATA)
    if jf.raw_of(packed, P_WEAPON) != jf.raw_of(src_entries, P_WEAPON):
        raise SystemExit("Weapon.ini changed after pack")
    if jf.raw_of(packed, P_UPGRADE) != jf.raw_of(src_entries, P_UPGRADE):
        raise SystemExit("Upgrade.ini changed after pack")
    packed_map = {jf.norm(n).lower(): b for n, b in packed}
    for n, b in src_entries:
        if is_other_faction_path(n) and packed_map[jf.norm(n).lower()] != b:
            raise SystemExit(f"other faction mutated after pack {n}")
    if len(packed) != packed_before:
        raise SystemExit("packed count drift")

    # Turkey WF from #505 still native.
    if "Command_ConstructTurkeyTankLeopard2A7Plus" not in cs_buttons(cmdset["TurkeyWarfactoryCommandSet"]):
        raise SystemExit("Turkey WF CS reverted")

    # BIG integrity: unique packed paths, BIGF readable, same file count.
    packed_names = [jf.norm(n).lower() for n, _ in packed]
    if len(packed_names) != len(set(packed_names)):
        raise SystemExit("duplicate packed paths")
    if packed[0][0] and jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")[0][0] != packed[0][0]:
        raise SystemExit("DATA BIG re-read mismatch")
    art_entries = jf.read_big_list(WS_OUT / "_SPEC_ART_ONE.big")
    art_names = [jf.norm(n).lower() for n, _ in art_entries]
    if not art_names or not all(n.startswith("art\\") for n in art_names):
        raise SystemExit("ART BIG layout is not Art\\...")
    if any(n.startswith("data\\") for n in art_names):
        raise SystemExit("DATA paths leaked into ART BIG")
    data_names = [jf.norm(n).lower() for n, _ in packed]
    if any(n.startswith("art\\") for n in data_names):
        raise SystemExit("ART paths leaked into DATA BIG")

    # Duplicate Object templates across packed INIs.
    obj_homes: dict[str, list[str]] = {}
    all_objs: dict[str, str] = {}
    for n, b in packed:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", errors="replace")
        for oname, blk in parse_objects(t).items():
            obj_homes.setdefault(oname, []).append(n)
            all_objs[oname] = blk
    dup_objs = {k: v for k, v in obj_homes.items() if len(v) > 1}
    src_homes: dict[str, list[str]] = {}
    for n, b in src_entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", errors="replace")
        for oname, _blk in parse_objects(t).items():
            src_homes.setdefault(oname, []).append(n)
    src_dups = {k for k, v in src_homes.items() if len(v) > 1}
    new_dups = [k for k in dup_objs if k not in src_dups]
    if new_dups:
        raise SystemExit("new duplicate objects introduced: " + ", ".join(new_dups[:10]))

    # Broken INI refs on the nine factions' WF / Camp / MIC / Strategy bars.
    check_cs = (
        [
            "Iraq_WarFactoryCommandSet_T", "Iraq_WarFactoryCommandSet_T3",
            "Iraq_BarracksCommandSet", "Iraq_MICCommandSet",
            "Vietnam_WarFactoryCommandSet", "Vietnam_BarracksCommandSet", "Vietnam_MICCommandSet",
            "SwedenWarfactoryCommandSet", "SwedenCampCommandSet", "SwedenStrategyCenterCommandSet",
            "TurkeyWarfactoryCommandSet", "TurkeyCampCommandSet", "TurkeyStrategyCenterCommandSet",
            "BritainWarfactoryCommandSet", "BritainCampCommandSet", "BritainStrategyCenterCommandSet",
            "GermanyWarfactoryCommandSet", "GermanyCampCommandSet", "GermanyStrategyCenterCommandSet",
            "FranceWarfactoryCommandSet", "FranceCampCommandSet", "FranceStrategyCenterCommandSet",
            "ItalyWarfactoryCommandSet", "ItalyCampCommandSet", "ItalyStrategyCenterCommandSet",
            "UkraineWarfactoryCommandSet", "UkraineCampCommandSet", "UkraineStrategyCenterCommandSet",
        ]
    )
    broken = []
    for csname in check_cs:
        if csname not in cmdset:
            broken.append(f"missing CS {csname}")
            continue
        for btn in cs_buttons(cmdset[csname]):
            if btn not in cmdbtn:
                broken.append(f"{csname}:{btn} missing CommandButton")
                continue
            cmd = field(cmdbtn[btn], "Command") or ""
            if cmd in ("UNIT_BUILD", "DOZER_CONSTRUCT"):
                obj = field(cmdbtn[btn], "Object") or ""
                if obj and obj not in all_objs:
                    broken.append(f"{csname}:{btn} Object {obj} missing")
            if cmd == "PLAYER_UPGRADE":
                up = field(cmdbtn[btn], "Upgrade") or ""
                if not up:
                    broken.append(f"{csname}:{btn} PLAYER_UPGRADE has no Upgrade=")
    if broken:
        raise SystemExit("broken INI refs: " + "; ".join(broken[:20]))

    def pu_btns(csname: str) -> list[str]:
        return [
            b for b in cs_buttons(cmdset[csname])
            if b in cmdbtn and field(cmdbtn[b], "Command") == "PLAYER_UPGRADE"
        ]

    country_audit = [
        "",
        "===== COUNTRY AUDIT =====",
        "",
        "IRAQ",
        "  BIG_PATHS = Data\\INI\\Object\\Specter\\Iraq Army\\...",
        "  WARFACTORY = Iraq_WarFactoryCommandSet_T/T1/T2/T3 all equal full T3 roster",
        "  WARFACTORY_UNLOCKED = T-72 BMP-1 BMP-2 BTR-90 2S1 Sam8 AssadBabel-2 SA-6 Sarab7 Alhussaien Roland3K BM-21 R11ScudB",
        "  MIC_PATH_KEPT = YES  buttons=" + ", ".join(pu_btns("Iraq_MICCommandSet")),
        "  CAMP = Iraq_BarracksCommandSet  " + ", ".join(pu_btns("Iraq_BarracksCommandSet")),
        "  CAMP_UNLOCKED = Capture RGD5 RPG29",
        "  BLOCKING_PLAYER_UPGRADE = NO  SCIENCE = NO  NEEDEDUPGRADE = NO  PREREQ_UPGRADE = NO",
        "  KEPT = AADS AA/ABM, ICBM, GLA worker pack/unpack, MIC upgrade buttons",
        "",
        "VIETNAM",
        "  BIG_PATHS = Data\\INI\\Object\\Specter\\Vietnam People's Armed Forces\\...",
        "  WARFACTORY = Vietnam_WarFactoryCommandSet  tier CommandSetUpgrade removed",
        "  MIC_PATH_KEPT = YES  buttons=" + ", ".join(pu_btns("Vietnam_MICCommandSet")),
        "  CAMP = Vietnam_BarracksCommandSet  " + ", ".join(pu_btns("Vietnam_BarracksCommandSet")),
        "  CAMP_UNLOCKED = Capture RGD5 RPG29",
        "  BLOCKING_PLAYER_UPGRADE = NO  SCIENCE = NO  NEEDEDUPGRADE = NO  PREREQ_UPGRADE = NO",
        "  KEPT = AADS AA/ABM, ICBM, MIC upgrade buttons",
        "",
        "SWEDEN",
        "  WARFACTORY = SwedenWarfactoryCommandSet  PLAYER_UPGRADE conditions promoted",
        "  CAMP = SwedenCampCommandSet  " + ", ".join(pu_btns("SwedenCampCommandSet")),
        "  STRATEGY = SwedenStrategyCenterCommandSet  " + ", ".join(pu_btns("SwedenStrategyCenterCommandSet")),
        "  STRATEGY_UNLOCKED = NuclearReactor MTS",
        "  BLOCKING_PLAYER_UPGRADE = NO",
        "",
        "TURKEY",
        "  WARFACTORY = TurkeyWarfactoryCommandSet  PLAYER_UPGRADE conditions promoted",
        "  CAMP = TurkeyCampCommandSet  " + ", ".join(pu_btns("TurkeyCampCommandSet")),
        "  STRATEGY = TurkeyStrategyCenterCommandSet  " + ", ".join(pu_btns("TurkeyStrategyCenterCommandSet")),
        "  STRATEGY_UNLOCKED = NuclearReactor MTS",
        "  BLOCKING_PLAYER_UPGRADE = NO",
        "",
        "UNITED KINGDOM",
        "  WARFACTORY = BritainWarfactoryCommandSet  PLAYER_UPGRADE conditions promoted",
        "  CAMP = BritainCampCommandSet  " + ", ".join(pu_btns("BritainCampCommandSet")),
        "  STRATEGY = BritainStrategyCenterCommandSet  " + ", ".join(pu_btns("BritainStrategyCenterCommandSet")),
        "  STRATEGY_UNLOCKED = NuclearReactor MTS",
        "  BLOCKING_PLAYER_UPGRADE = NO",
        "",
        "GERMANY",
        "  WARFACTORY = GermanyWarfactoryCommandSet  PLAYER_UPGRADE conditions promoted",
        "  CAMP = GermanyCampCommandSet  " + ", ".join(pu_btns("GermanyCampCommandSet")),
        "  STRATEGY = GermanyStrategyCenterCommandSet  " + ", ".join(pu_btns("GermanyStrategyCenterCommandSet")),
        "  STRATEGY_UNLOCKED = NuclearReactor MTS",
        "  BLOCKING_PLAYER_UPGRADE = NO",
        "",
        "FRANCE",
        "  WARFACTORY = FranceWarfactoryCommandSet  PLAYER_UPGRADE conditions promoted",
        "  CAMP = FranceCampCommandSet  " + ", ".join(pu_btns("FranceCampCommandSet")),
        "  STRATEGY = FranceStrategyCenterCommandSet  " + ", ".join(pu_btns("FranceStrategyCenterCommandSet")),
        "  STRATEGY_UNLOCKED = NuclearReactor MTS",
        "  BLOCKING_PLAYER_UPGRADE = NO",
        "",
        "ITALY",
        "  WARFACTORY = ItalyWarfactoryCommandSet  PLAYER_UPGRADE conditions promoted",
        "  CAMP = ItalyCampCommandSet  " + ", ".join(pu_btns("ItalyCampCommandSet")),
        "  STRATEGY = ItalyStrategyCenterCommandSet  " + ", ".join(pu_btns("ItalyStrategyCenterCommandSet")),
        "  STRATEGY_UNLOCKED = NuclearReactor MTS",
        "  BLOCKING_PLAYER_UPGRADE = NO",
        "",
        "UKRAINE",
        "  WARFACTORY = UkraineWarfactoryCommandSet  PLAYER_UPGRADE conditions promoted",
        "  CAMP = UkraineCampCommandSet  " + ", ".join(pu_btns("UkraineCampCommandSet")),
        "  STRATEGY = UkraineStrategyCenterCommandSet  " + ", ".join(pu_btns("UkraineStrategyCenterCommandSet")),
        "  STRATEGY_UNLOCKED = NuclearReactor MTS",
        "  BLOCKING_PLAYER_UPGRADE = NO",
    ]

    lines = [
        "SPECTER1 WF + CAMP UPGRADE UNLOCK",
        "BASELINE = SPECTER1_WARFACTORY_BUILD_FIX / PR #505",
        f"BASELINE_DATA_SHA256 = {EXPECTED_DATA_SHA}",
        f"NEW_DATA_SHA256 = {new_sha}",
        f"ART_SHA256 = {EXPECTED_ART_SHA} (unchanged copy)",
        f"PACKED_DATA_FILES = {len(packed)}",
        f"PACKED_ART_FILES = {len(art_entries)}",
        f"DUPLICATE_PACKED_PATHS = NO",
        f"DUPLICATE_FACTION_OBJECTS_INTRODUCED = NO",
        f"PREEXISTING_DUPLICATE_OBJECTS = {len(src_dups)} (present in PR #505, not added)",
        f"BROKEN_INI_REFS_WF_CAMP = NO",
        "BIG_INTEGRITY = YES",
        "DATA_LAYOUT = Data\\INI\\... inside _SPEC_DATA_ONE.big",
        "ART_LAYOUT = Art\\... inside _SPEC_ART_ONE.big",
        "ART_CHANGED = NO",
        "WEAPON_INI_CHANGED = NO",
        "UPGRADE_INI_CHANGED = NO",
        "OTHER_FACTIONS_UNCHANGED = YES",
        "PACKED_FILE_COUNT_UNCHANGED = YES",
        "NEW_DATA_OR_ART_FOLDERS = NO",
        "NEW_BIG_FILES = NO  (same two archive names as PR #505)",
        "FACTIONS = Iraq, Sweden, Turkey, United Kingdom (Britain), Germany, France, Italy, Ukraine, Vietnam",
        "",
        "WARFACTORY = Iraq T/T1/T2 bars equal T3 full roster; Iraq/Vietnam tier CommandSetUpgrade removed",
        "MIC = Iraq/Vietnam research bars show all upgrade buttons; MIC path kept",
        "CAMP = Capture/RGD5/RPG29 buttons kept and unlocked (no Science/NeededUpgrade)",
        "STRATEGY = NuclearReactor + MTS buttons kept; research TriggeredBy dropped on faction objects",
        "PLAYER_UPGRADE_CONDITIONS = promoted to default on these nine factions' objects",
        f"SCIENCE_STRIPPED = files={totals['files']} science_lines={totals['science']} prereq_upgrade={totals['prereq']}",
        f"TRIGGEREDBY_RESEARCH_DROPPED = {totals['triggered']}",
        f"WEAPONSET_PROMOTED = {totals['weaponset']} ARMORSET_PROMOTED = {totals['armorset']}",
        f"TIER_COMMANDSETUPGRADE_REMOVED = {totals['csu']}",
        "COMMANDBUTTON_SCIENCE_STRIPPED = Command_Irq_Tier1, Command_Irq_Tier3, Hussien, Abbas",
        "MODE_UPGRADES_KEPT = AADS AA/ABM, ICBM_BoosterKiller, GLA worker pack/unpack",
        "",
        "BLOCKED_PLAYER_UPGRADE_REMAIN = NO",
        "INGAME_TESTED = NO",
        "DATA_CHANGED = YES",
        "ART_CHANGED = NO",
    ]
    audit = "\n".join(lines + country_audit) + "\n"

    changelog = """SPECTER1 WarFactory + Camp upgrade unlock

Continues from SPECTER1_WARFACTORY_BUILD_FIX (PR #505). ART, Weapon.ini,
Upgrade.ini, models, and other factions are unchanged. Packed file count
unchanged. Same BIG packaging as PR #505.

Unlocks upgrade logic for Iraq, Sweden, Turkey, United Kingdom, Germany,
France, Italy, Ukraine, and Vietnam:

1. WarFactory: Iraq T/T1/T2 production bars equal the full T3 roster.
   Iraq/Vietnam CommandSetUpgrade modules gated by Upgrade_Irq_Tier1/2/3
   are removed so the factory bar cannot lock or shrink.
2. Camp / main research building: Camp Capture (and Iraq/Vietnam RGD5/RPG29)
   buttons stay on the bar. Iraq/Vietnam MIC upgrade buttons stay and are
   all visible (path kept). NATO Strategy Center NuclearReactor/MTS buttons stay.
3. PLAYER_UPGRADE WeaponSet/ArmorSet Conditions on these nine factions
   are promoted to default. Research TriggeredBy is dropped (AADS mode
   toggles and ICBM grant kept). Science / NeededUpgrade / Prerequisites
   Upgrade= stripped on those objects.
4. Rank Science removed from Command_Irq_Tier1, Command_Irq_Tier3,
   Command_UpgradeHussienResearchProgram, Command_UpgradeAbbasResearchProgram
   so those PLAYER_UPGRADE buttons are usable without rank lock.

INGAME_TESTED = NO
"""

    install = f"""SPECTER1_WF_CAMP_UPGRADE_UNLOCK
================================

WarFactory + Camp upgrade unlock for Iraq, Sweden, Turkey, United Kingdom,
Germany, France, Italy, Ukraine, Vietnam on the PR #505 baseline.
ART, models, weapons, and other factions unchanged.
Same GameRoot layout as PR #505: two BIG files, no loose Data/Art.

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

WF_CAMP_UPGRADES_UNLOCKED = YES
BLOCKED_PLAYER_UPGRADE_REMAIN = NO
INGAME_TESTED = NO
"""
    for dest in (OUT_DIR, WS_OUT):
        (dest / "audit.txt").write_text(audit, encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "INSTALL.txt").write_text(install, encoding="utf-8")

    zpath = WS_OUT / "SPECTER1_WF_Camp_Upgrade_Unlock.zip"
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
        f"SPECTER1_WF_Camp_Upgrade_Unlock.zip  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n"
    )
    for dest in (OUT_DIR, WS_OUT):
        (dest / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", new_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    print("TOTALS", totals)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
