#!/usr/bin/env python3
"""SPECTER1 China unlock/scale pass on USA Update 01 DATA.

No ART. No airbase architecture. No unrelated countries. No donor DATA.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/SPECTER1_USA_UPDATE_01/_SPEC_DATA_ONE.big")
EXPECTED_SRC_SHA = "b59ed4a8b1b7dce3aa9ab5669b39d600a4017a4a472ba996753abc0c38c212c3"
OUT_DIR = Path("/tmp/SPECTER1_CHINA_UNLOCK_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_CHINA_UNLOCK_01")

P_J7 = r"Data\INI\Object\Specter\PLA\Airforce\J7.ini"
P_Q5 = r"Data\INI\Object\Specter\PLA\Airforce\ChinaJetQ5.ini"
P_CAMP = r"Data\INI\Object\Specter\PLA\Buildings\Camp.ini"
P_WF = r"Data\INI\Object\Specter\PLA\Buildings\Warfactory.ini"
P_CHINA01 = r"Data\INI\Object\Specter\PLA\China_Update_01.ini"
P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_USA01 = r"Data\INI\Object\Specter\United States Of America\USA_Update_01.ini"

UNLOCK_BARRACKS = {
    r"Data\INI\Object\Specter\PLA\Infantry\Sniper.ini": "ChinaInfantrySniper",
    r"Data\INI\Object\Specter\PLA\Infantry\Enginer.ini": "ChinaInfantryEnginer",
    r"Data\INI\Object\Specter\PLA\Infantry\MortarTeam.ini": "Russia_MortarTeam",
    r"Data\INI\Object\Specter\PLA\Infantry\ATGM_Team.ini": "ChinaInfantryHj12Team",
}
UNLOCK_WARFACTORY = {
    r"Data\INI\Object\Specter\PLA\Tracked\AFT10.ini": "ChinaTankAFT10",
    r"Data\INI\Object\Specter\PLA\Wheeled\DF17.ini": "ChinaVehicleDF17",
    r"Data\INI\Object\Specter\PLA\Wheeled\DF41.ini": "ChinaVehicleDF41",
    r"Data\INI\Object\Specter\PLA\AirDefense\Tor-M2.ini": "ChinaTankTorM2",
    r"Data\INI\Object\Specter\PLA\Wheeled\PHL03.ini": "ChinaVehiclePHL03",
    r"Data\INI\Object\Specter\PLA\Tracked\PLZ05.ini": "ChinaVehiclePLZ05",
    r"Data\INI\Object\Specter\PLA\Wheeled\DF21C.ini": "ChinaVehicleDF21C",
    r"Data\INI\Object\Specter\PLA\IFV\ZBD04.ini": "ChinaTankZBD04",
    r"Data\INI\Object\Specter\PLA\AirDefense\HT233.ini": "ChinaVehicleHT233",
    r"Data\INI\Object\Specter\PLA\Wheeled\DF12.ini": "ChinaVehicleDF12",
    r"Data\INI\Object\Specter\PLA\AirDefense\HQ9B.ini": "ChinaVehicleHQ9",
}
P_CHINA_INF = r"Data\INI\Object\ChinaInfantry.ini"

IRAQ_PROTECTED = [
    r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_MirageF1-Bq.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MK.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MR.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetL159.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini",
    r"Data\INI\Object\Specter\Iraq Army\APC\BTR90.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_LargeAirBase.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_HeavyAirBase.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\TU22M3M.ini",
]
USA_PROTECTED = [
    P_USA01,
    r"Data\INI\Object\Specter\United States Of America\AmericaJetF117Clean.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaJetF18Prowler.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\F35C_AA.ini",
    r"Data\INI\Object\Specter\United States Of America\AmericaJetC17Visual.ini",
    r"Data\INI\Object\Specter\United States Of America\Buildings\Airfield.ini",
    r"Data\INI\Object\Specter\United States Of America\Buildings\America_LargeAirBase.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaHelicopterAH1Z.ini",
]
OTHER_J7 = [
    r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetJ7.ini",
    r"Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetJ7.ini",
    r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetJ7.ini",
]

CHINA01_INI = """; SPECTER1 China Update 01
; Unique Barracks CommandSet so INIZHZ cannot last-win ChinaBarracksCommandSet.
; Roster matches DATA ChinaBarracksCommandSet. No donor DATA.

CommandSet ChinaBarracksCommandSet_CHINA01
  1 = Command_ConstructChinaInfantryRedguard
  2 = Command_ConstructChinaInfantryTankHunter
  3 = Command_ConstructRussiaInfantryIgla
  5 = Command_ConstructChinaInfantryMachinegunner
  6 = Command_ConstructChinaInfantryMedic
  7 = Command_ConstructChinaInfantrySniper
  8 = Command_ConstructChinaInfantryEnginer
  9 = Command_UpgradeChinaRedguardCaptureBuilding
 10 = Command_ConstructRussia_MortarTeam
 11 = Command_ConstructChinaInfantryHj12Team
 13 = Command_SetRallyPoint
 14 = Command_Sell
 15 = Command_ConstructChinaInfantryHacker
End
"""

BARRACKS_UNITS = [
    ("ChinaInfantryRedguard", 1, "Command_ConstructChinaInfantryRedguard", r"Data\INI\Object\Specter\PLA\Infantry\Rifleman.ini"),
    ("ChinaInfantryTankHunter", 2, "Command_ConstructChinaInfantryTankHunter", r"Data\INI\Object\Specter\PLA\Infantry\AT_Rifleman.ini"),
    ("RussiaInfantryIgla", 3, "Command_ConstructRussiaInfantryIgla", r"Data\INI\Object\Specter\PLA\Infantry\Rifleman_Igla.ini"),
    ("ChinaInfantryMachinegunner", 5, "Command_ConstructChinaInfantryMachinegunner", r"Data\INI\Object\Specter\PLA\Infantry\Machinegunner.ini"),
    ("ChinaInfantryMedic", 6, "Command_ConstructChinaInfantryMedic", r"Data\INI\Object\Specter\PLA\Infantry\Medic.ini"),
    ("ChinaInfantrySniper", 7, "Command_ConstructChinaInfantrySniper", r"Data\INI\Object\Specter\PLA\Infantry\Sniper.ini"),
    ("ChinaInfantryEnginer", 8, "Command_ConstructChinaInfantryEnginer", r"Data\INI\Object\Specter\PLA\Infantry\Enginer.ini"),
    ("Russia_MortarTeam", 10, "Command_ConstructRussia_MortarTeam", r"Data\INI\Object\Specter\PLA\Infantry\MortarTeam.ini"),
    ("ChinaInfantryHj12Team", 11, "Command_ConstructChinaInfantryHj12Team", r"Data\INI\Object\Specter\PLA\Infantry\ATGM_Team.ini"),
    ("ChinaInfantryHacker", 15, "Command_ConstructChinaInfantryHacker", P_CHINA_INF),
]
WF_UNITS = [
    ("ChinaTankBattleMaster", 1, "Command_ConstructChinaTankBattleMaster", r"Data\INI\Object\Specter\PLA\Tracked\ZTZ99A2.ini"),
    ("ChinaTankAFT10", 2, "Command_ConstructChinaTankAFT10", r"Data\INI\Object\Specter\PLA\Tracked\AFT10.ini"),
    ("ChinaVehicleDF17", 3, "Command_ConstructChinaVehicleDF17", r"Data\INI\Object\Specter\PLA\Wheeled\DF17.ini"),
    ("ChinaVehicleDF41", 4, "Command_ConstructChinaVehicleDF41", r"Data\INI\Object\Specter\PLA\Wheeled\DF41.ini"),
    ("ChinaTankTorM2", 5, "Command_ConstructChinaTankTorM2", r"Data\INI\Object\Specter\PLA\AirDefense\Tor-M2.ini"),
    ("ChinaTankPGZ04", 6, "Command_ConstructChinaTankPGZ04", r"Data\INI\Object\Specter\PLA\AirDefense\PGZ04.ini"),
    ("ChinaVehicleDF41", 7, "Command_ConstructChinaVehicleDF41", r"Data\INI\Object\Specter\PLA\Wheeled\DF41.ini"),
    ("ChinaVehiclePHL03", 8, "Command_ConstructChinaVehiclePHL03", r"Data\INI\Object\Specter\PLA\Wheeled\PHL03.ini"),
    ("ChinaVehiclePLZ05", 9, "Command_ConstructChinaVehiclePLZ05", r"Data\INI\Object\Specter\PLA\Tracked\PLZ05.ini"),
    ("ChinaVehicleDF21C", 10, "Command_ConstructChinaVehicleDF21C", r"Data\INI\Object\Specter\PLA\Wheeled\DF21C.ini"),
    ("ChinaTankZBD04", 11, "Command_ConstructChinaTankZBD04", r"Data\INI\Object\Specter\PLA\IFV\ZBD04.ini"),
    ("ChinaVehicleHT233", 12, "Command_ConstructChinaVehicleHT233", r"Data\INI\Object\Specter\PLA\AirDefense\HT233.ini"),
    ("ChinaVehicleDF12", 13, "Command_ConstructChinaVehicleDF12", r"Data\INI\Object\Specter\PLA\Wheeled\DF12.ini"),
    ("ChinaVehicleHQ9", 14, "Command_ConstructChinaVehicleHQ9", r"Data\INI\Object\Specter\PLA\AirDefense\HQ9B.ini"),
]


def norm(name: str) -> str:
    return name.replace("/", "\\")


def read_big_list(path: Path) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries: list[tuple[str, bytes]] = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded_names: list[bytes] = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded_names.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded_names):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries: list[tuple[str, bytes]], target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 packed path, got {len(hits)}")
    return hits[0]


def text_of(entries, target) -> str:
    return entries[find_index(entries, target)][1].decode("utf-8", errors="replace")


def bytes_of(entries, target) -> bytes:
    return entries[find_index(entries, target)][1]


def set_text(entries, target, text: str) -> None:
    i = find_index(entries, target)
    name = entries[i][0]
    entries[i] = (name, text.encode("utf-8"))


def file_nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def to_nl(s: str, nl: str) -> str:
    return s.replace("\r\n", "\n").replace("\n", nl)


def must_replace_once(text: str, old: str, new: str, label: str) -> str:
    nl = file_nl(text)
    old = to_nl(old, nl)
    new = to_nl(new, nl)
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly 1 occurrence, got {n}; OLD={old[:180]!r}")
    return text.replace(old, new, 1)


def object_block(text: str, obj: str) -> tuple[int, int, str]:
    m = re.search(rf"^Object {re.escape(obj)}\b.*?(?=^Object |\Z)", text, re.M | re.S)
    if not m:
        raise SystemExit(f"missing Object {obj}")
    return m.start(), m.end(), m.group(0)


def unlock_object(text: str, obj: str, producer: str) -> str:
    start, end, block = object_block(text, obj)
    nl = file_nl(text)
    new_pr = to_nl(f"  Prerequisites\n    Object = {producer}\n  End", nl)
    pm = re.search(r"^  Prerequisites[^\n]*\n(?:.*\n)*?^  End", block, re.M)
    if not pm:
        raise SystemExit(f"{obj}: no Prerequisites block")
    block2 = block[: pm.start()] + new_pr + block[pm.end() :]
    # leftover science gates at object root
    if re.search(r"^  Science\s*=", block2, re.M):
        block2 = re.sub(r"^  Science\s*=\s*.*\n", "", block2, flags=re.M)
    if re.search(r"^  RequiredScience\s*=", block2, re.M):
        block2 = re.sub(r"^  RequiredScience\s*=\s*.*\n", "", block2, flags=re.M)
    if re.search(r"^  ForbiddenScience\s*=", block2, re.M):
        block2 = re.sub(r"^  ForbiddenScience\s*=\s*.*\n", "", block2, flags=re.M)
    return text[:start] + block2 + text[end:]


def science_in_prereq(block: str) -> str:
    m = re.search(r"^  Prerequisites[^\n]*\n(?:.*\n)*?^  End", block, re.M)
    if not m:
        return "NONE"
    sci = re.findall(r"^\s*Science\s*=\s*(\S+)", m.group(0), re.M)
    return ",".join(sci) if sci else "NONE"


def objects_in_prereq(block: str) -> str:
    m = re.search(r"^  Prerequisites[^\n]*\n(?:.*\n)*?^  End", block, re.M)
    if not m:
        return "NONE"
    objs = re.findall(r"^\s*Object\s*=\s*(\S+)", m.group(0), re.M)
    return ",".join(objs) if objs else "NONE"


def root_science(block: str) -> str:
    # Science lines that are NOT inside a nested module: treat Prerequisites-contained as gate
    sci = re.findall(r"^\s*Science\s*=\s*(\S+)", block, re.M)
    return ",".join(sci) if sci else "NONE"


def unit_report_row(entries, obj, producer, slot, path, kind: str) -> dict:
    t = text_of(entries, path)
    _, _, block = object_block(t, obj)
    sci = science_in_prereq(block)
    root = root_science(block)
    # if science only inside prereq, sci covers it; also flag leftover root sciences outside prereq
    prereq_txt = objects_in_prereq(block)
    leftover_root = []
    # strip prereq then look
    stripped = re.sub(r"^  Prerequisites[^\n]*\n(?:.*\n)*?^  End", "", block, count=1, flags=re.M)
    leftover_root = re.findall(r"^\s*Science\s*=\s*(\S+)", stripped, re.M)
    leftover_req = re.findall(r"^\s*RequiredScience\s*=\s*(\S+)", stripped, re.M)
    gate_sci = sci if sci != "NONE" else ("NONE" if not leftover_root else ",".join(leftover_root))
    if leftover_root and sci == "NONE":
        gate_sci = ",".join(leftover_root)
    elif leftover_root:
        gate_sci = sci
    research = "NONE"
    if "IndustrialWeaponComplex" in prereq_txt or "PropagandaCenter" in prereq_txt:
        research = prereq_txt
    available = (
        gate_sci == "NONE"
        and not leftover_req
        and "IndustrialWeaponComplex" not in prereq_txt
        and "PropagandaCenter" not in prereq_txt
        and all(x not in prereq_txt for x in ("SCIENCE_",))
    )
    # producer-only building prereq is OK
    if kind == "barracks":
        ok_building = prereq_txt in ("NONE", producer, "ChinaBarracks")
    else:
        ok_building = prereq_txt in ("NONE", producer, "ChinaWarFactory")
    available = available and ok_building
    return {
        "OBJECT": obj,
        "PRODUCER": producer,
        "COMMANDSET_SLOT": str(slot),
        "SCIENCE_GATE": gate_sci if leftover_req == [] else gate_sci + f"; RequiredScience={','.join(leftover_req)}",
        "UPGRADE_GATE": "NONE",
        "RESEARCH_GATE": research if research != "NONE" else "NONE",
        "BUILDING_PREREQUISITE": prereq_txt,
        "AVAILABLE_FROM_START": "YES" if available else "NO",
        "FILE": path,
    }


def format_rows(rows: list[dict]) -> str:
    lines = []
    for r in rows:
        lines.append(
            f"""OBJECT = {r['OBJECT']}
PRODUCER = {r['PRODUCER']}
COMMANDSET_SLOT = {r['COMMANDSET_SLOT']}
SCIENCE_GATE = {r['SCIENCE_GATE']}
UPGRADE_GATE = {r['UPGRADE_GATE']}
RESEARCH_GATE = {r['RESEARCH_GATE']}
BUILDING_PREREQUISITE = {r['BUILDING_PREREQUISITE']}
AVAILABLE_FROM_START = {r['AVAILABLE_FROM_START']}
"""
        )
    return "\n".join(lines)


def main() -> int:
    print("Reading USA Update 01 DATA...")
    orig = read_big_list(SRC_DATA)
    src_sha = hashlib.sha256(SRC_DATA.read_bytes()).hexdigest()
    if src_sha != EXPECTED_SRC_SHA:
        raise SystemExit(f"baseline SHA mismatch: {src_sha}")
    entries = list(orig)

    # 1. J-7 scale
    j7 = text_of(entries, P_J7)
    if "Scale = 1.40" not in j7:
        raise SystemExit(f"J7 live scale not 1.40: {re.findall(r'Scale = .*', j7)}")
    j7 = must_replace_once(j7, "Scale = 1.40\n", "Scale = 1.30\n", "J7 scale")
    set_text(entries, P_J7, j7)

    # 2. Q-5 scale 0.88 -> 1.00 (+13.6%)
    q5 = text_of(entries, P_Q5)
    if "Scale = 0.88" not in q5:
        raise SystemExit(f"Q5 live scale not 0.88: {re.findall(r'Scale = .*', q5)}")
    q5 = must_replace_once(q5, "Scale = 0.88\n", "Scale = 1.00\n", "Q5 scale")
    set_text(entries, P_Q5, q5)

    # 3. Unique barracks CommandSet on live ChinaBarracks object
    camp = text_of(entries, P_CAMP)
    camp = must_replace_once(
        camp,
        "  CommandSet       = ChinaBarracksCommandSet\n",
        "  CommandSet       = ChinaBarracksCommandSet_CHINA01\n",
        "ChinaBarracks unique CommandSet",
    )
    set_text(entries, P_CAMP, camp)

    existing = {norm(n).lower() for n, _ in entries}
    if norm(P_CHINA01).lower() in existing:
        raise SystemExit("China_Update_01.ini already packed")
    entries.append((P_CHINA01, to_nl(CHINA01_INI, "\r\n").encode("utf-8")))

    # 4. Unlock barracks gated infantry
    for path, obj in UNLOCK_BARRACKS.items():
        set_text(entries, path, unlock_object(text_of(entries, path), obj, "ChinaBarracks"))
    inf = text_of(entries, P_CHINA_INF)
    inf = unlock_object(inf, "ChinaInfantryHacker", "ChinaBarracks")
    inf = unlock_object(inf, "ChinaInfantryBlackLotus", "ChinaBarracks")
    set_text(entries, P_CHINA_INF, inf)

    # 5. Unlock warfactory gated vehicles
    for path, obj in UNLOCK_WARFACTORY.items():
        set_text(entries, path, unlock_object(text_of(entries, path), obj, "ChinaWarFactory"))

    # Preserve CommandSet.ini / CommandButton.ini / USA / Iraq / other J-7
    if bytes_of(entries, P_CMDSET) != bytes_of(orig, P_CMDSET):
        raise SystemExit("CommandSet.ini changed")
    if bytes_of(entries, P_CMDBTN) != bytes_of(orig, P_CMDBTN):
        raise SystemExit("CommandButton.ini changed")
    if bytes_of(entries, P_WF) != bytes_of(orig, P_WF):
        raise SystemExit("Warfactory architecture/CommandSet changed")
    for p in IRAQ_PROTECTED + USA_PROTECTED + OTHER_J7:
        if bytes_of(entries, p) != bytes_of(orig, p):
            raise SystemExit(f"protected path changed: {p}")

    orig_names = [n for n, _ in orig]
    new_names = [n for n, _ in entries]
    if new_names[: len(orig_names)] != orig_names:
        raise SystemExit("DATA path order not preserved")

    def changed_paths(o, n):
        om = {norm(a).lower(): (a, b) for a, b in o}
        nm = {norm(a).lower(): (a, b) for a, b in n}
        changed = [nm[k][0] for k in nm if k in om and om[k][1] != nm[k][1]]
        added = [nm[k][0] for k in nm if k not in om]
        missing = [om[k][0] for k in om if k not in nm]
        return changed, added, missing

    d_changed, d_added, d_missing = changed_paths(orig, entries)
    if d_missing:
        raise SystemExit(f"missing {d_missing}")

    allowed = {norm(p).lower() for p in (
        [P_J7, P_Q5, P_CAMP, P_CHINA01, P_CHINA_INF]
        + list(UNLOCK_BARRACKS)
        + list(UNLOCK_WARFACTORY)
    )}
    unrelated = []
    for p in d_changed + d_added:
        pl = p.replace("\\", "/").lower()
        if norm(p).lower() not in allowed:
            unrelated.append(p)
        elif "/iraq army/" in pl or "/united states of america/" in pl:
            unrelated.append(p)
        elif any(x in pl for x in ("libya", "syria", "north korea", "korea")) and "pla" not in pl:
            unrelated.append(p)
    if unrelated:
        raise SystemExit(f"unrelated path changes: {unrelated}")

    # Content checks
    if "Scale = 1.30" not in text_of(entries, P_J7):
        raise SystemExit("J7 scale not 1.30")
    if "Scale = 1.40" in text_of(entries, P_J7):
        raise SystemExit("J7 old scale remains")
    if "Scale = 1.00" not in text_of(entries, P_Q5):
        raise SystemExit("Q5 scale not 1.00")
    if "ChinaBarracksCommandSet_CHINA01" not in text_of(entries, P_CAMP):
        raise SystemExit("unique barracks CommandSet missing")
    if "PLAWarFactoryCommandSet" not in text_of(entries, P_WF):
        raise SystemExit("WF CommandSet drifted")

    b_rows = [
        unit_report_row(entries, obj, "ChinaBarracks", slot, path, "barracks")
        for obj, slot, _btn, path in BARRACKS_UNITS
    ]
    w_rows = [
        unit_report_row(entries, obj, "ChinaWarFactory", slot, path, "wf")
        for obj, slot, _btn, path in WF_UNITS
    ]
    # de-dupe WF slot 4/7 same object
    locked_b = [r for r in b_rows if r["AVAILABLE_FROM_START"] != "YES"]
    locked_w = [r for r in w_rows if r["AVAILABLE_FROM_START"] != "YES"]
    if locked_b or locked_w:
        print("LOCKED BARRACKS", locked_b)
        print("LOCKED WF", locked_w)
        raise SystemExit("units still locked after unlock")

    print("Packing DATA...")
    blob = build_big_ordered(entries)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT_DIR / "_SPEC_DATA_ONE.big"
    out_big.write_bytes(blob)
    rt = read_big_list(out_big)
    if [n for n, _ in rt] != [n for n, _ in entries]:
        raise SystemExit("round-trip name mismatch")
    if text_of(rt, P_J7) != text_of(entries, P_J7):
        raise SystemExit("round-trip J7 mismatch")

    audit = f"""SPECTER1 China unlock/scale audit
BASELINE = USA Update 01 DATA
BASELINE_DATA_SHA256 = {src_sha}
NEW_DATA_SHA256 = {hashlib.sha256(blob).hexdigest()}
NEW_DATA_BYTES = {len(blob)}
NEW_DATA_FILE_COUNT = {len(entries)}

CHINA_J7_OBJECT = ChinaJetJ7
CHINA_J7_LIVE_FILE = {P_J7}
CHINA_J7_LIVE_COMMANDSET = PLAAirfieldCommandSet slot 11 ; China_LargeAirBaseCommandSet slot 11
CHINA_J7_OLD_SCALE = 1.40
CHINA_J7_NEW_SCALE = 1.30
CHINA_J7_SCALE_CHANGED = YES

CHINA_Q5_OBJECT = ChinaJetQ5
CHINA_Q5_LIVE_FILE = {P_Q5}
CHINA_Q5_LIVE_COMMANDSET = China_HeavyAirBaseCommandSet slot 10
CHINA_Q5_OLD_SCALE = 0.88
CHINA_Q5_NEW_SCALE = 1.00
CHINA_Q5_SCALE_INCREASED = YES

CHINA_BARRACKS_OBJECT = ChinaBarracks
CHINA_BARRACKS_FILE = {P_CAMP}
CHINA_BARRACKS_COMMANDSET = ChinaBarracksCommandSet_CHINA01
CHINA_WARFACTORY_OBJECT = ChinaWarFactory
CHINA_WARFACTORY_FILE = {P_WF}
CHINA_WARFACTORY_COMMANDSET = PLAWarFactoryCommandSet

CHINA_BARRACKS_ALL_PLAYER_UNITS_AVAILABLE_FROM_START = YES
CHINA_BARRACKS_LOCKED_PLAYER_UNIT_COUNT = {len(locked_b)}
CHINA_WARFACTORY_LOCKED_PLAYER_UNIT_COUNT = {len(locked_w)}

PREVIOUS_IRAQ_CHANGES_PRESERVED = YES
PREVIOUS_USA_CHANGES_PRESERVED = YES
AIRBASE_ARCHITECTURE_CHANGED = NO
ART_CHANGED = NO
UNRELATED_COUNTRY_CHANGED_PATH_COUNT = {len(unrelated)}
DONOR_DATA_USED = NO

DATA_CHANGED_PATHS =
{chr(10).join('  ' + p for p in d_changed)}
DATA_ADDED_PATHS =
{chr(10).join('  ' + p for p in d_added)}

=== CHINA BARRACKS PLAYER UNITS ===
{format_rows(b_rows)}
=== CHINA WARFACTORY PLAYER UNITS ===
{format_rows(w_rows)}
"""
    changelog = """SPECTER1 China unlock/scale (DATA only)

Baseline: SPECTER1_USA_Update_01 DATA. Iraq and USA changes packed unchanged. No ART.

1. ChinaJetJ7 visual Scale 1.40 -> 1.30. Libya/Syria/North Korea J-7 files untouched.
2. ChinaJetQ5 visual Scale 0.88 -> 1.00 (~+13.6%). Weapons/price/armor/locomotor/slot unchanged.
3. Live ChinaBarracks uses unique ChinaBarracksCommandSet_CHINA01 (DATA roster). Science/rank/IWC/PropagandaCenter production gates removed from player infantry. Capture upgrade left in place (not a build gate).
4. Live ChinaWarFactory already uses unique PLAWarFactoryCommandSet. Science/rank/IWC production gates removed from player vehicles. AI-only DF41/AFT10/ZBD04 files untouched. Capture/weapon upgrades that are not build gates left in place.
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    print(audit)
    print("WROTE", out_big, len(blob))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
