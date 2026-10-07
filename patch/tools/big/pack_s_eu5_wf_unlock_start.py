#!/usr/bin/env python3
"""Unlock Ukraine WF vehicles at game start for 5 EU countries on PR #588.

Starts from packed PR #588 _SPEC_DATA_ONE.big
  SHA256 81efb3aa9067bed72c37546f16c6ef719d0b7f1170eceb4ccb4fa4d043f46872

Does NOT rebuild ART (PR #574 / PR #588 ART). Does NOT modify Ukraine,
USA, Sweden, or the 10-vehicle order.

Forensic: CommandButtons have no NEED_UPGRADE. Slots 1-3 have no Object
Prerequisites. Slots 4-10 require Object Prerequisites
  Object = UkraineStrategyCenter
on the shared Ukraine vehicle objects. Stripping those objects would
unlock Ukraine too.

Fix: unlocked clone objects (Prerequisites stripped) + new UNIT_BUILD
buttons; retarget only Germany/France/Britain/Italy/Turkey CommandSets
slots 4-10. Ukraine CommandSet and Ukraine object files unchanged.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_EU5_WF_UKRAINE_ROSTER/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_DATA_BCDHIJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_EU5_WF_UNLOCK_START"

BASE_DATA_SHA = "81efb3aa9067bed72c37546f16c6ef719d0b7f1170eceb4ccb4fa4d043f46872"
BASE_DATA_SIZE = 366460881
BASE_ART_SHA = "e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4"
BASE_ART_SIZE = 1292294758

CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
PT_KEY = r"Data\INI\PlayerTemplate.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
UNIT_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
LOCO_KEY = r"Data\INI\Locomotor.ini"
UPGRADE_KEY = r"Data\INI\Upgrade.ini"
SE_WF_KEY = r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\Warfactory.ini"
US_WF_KEY = r"Data\INI\Object\Specter\United States Of America\Buildings\Warfactory.ini"
UA_WF_KEY = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\Warfactory.ini"
UNLOCK_KEY = r"Data\INI\Object\Specter\EU5Unlock\Specter_EU5WFUnlock.ini"

DONOR_SET = "UkraineWarfactoryCommandSet"
TARGET_SETS = [
    "GermanyWarfactoryCommandSet",
    "FranceWarfactoryCommandSet",
    "BritainWarfactoryCommandSet",
    "ItalyWarfactoryCommandSet",
    "TurkeyWarfactoryCommandSet",
]

FREE_SLOTS = {
    1: "Command_ConstructUkraineTankLeopard2A7Plus",
    2: "Command_ConstructUkraineTankPuma",
    3: "Command_ConstructUkraineVehicleCortaleMK3",
}

LOCKS = [
    {
        "slot": 4,
        "old_btn": "Command_ConstructUkraineVehicleVBCI",
        "old_obj": "UkraineVehicleVBCI",
        "src_key": r"Data\INI\Object\Specter\Ukrainian Armed Forces\Wheleed\VBCI.ini",
        "new_btn": "Command_ConstructSpecterEU5_VBCI",
        "new_obj": "Specter_EU5_VBCI",
    },
    {
        "slot": 5,
        "old_btn": "Command_ConstructUkraineVehicleM142",
        "old_obj": "UkraineVehicleM142",
        "src_key": r"Data\INI\Object\Specter\Ukrainian Armed Forces\Wheleed\M142.ini",
        "new_btn": "Command_ConstructSpecterEU5_M142",
        "new_obj": "Specter_EU5_M142",
    },
    {
        "slot": 6,
        "old_btn": "Command_ConstructUkraineVehicleCaesar",
        "old_obj": "UkraineVehicleCaesar",
        "src_key": r"Data\INI\Object\Specter\Ukrainian Armed Forces\Wheleed\Caesar.ini",
        "new_btn": "Command_ConstructSpecterEU5_Caesar",
        "new_obj": "Specter_EU5_Caesar",
    },
    {
        "slot": 7,
        "old_btn": "Command_ConstructUkraineVehicleCentauroB2",
        "old_obj": "UkraineVehicleCentauroB2",
        "src_key": r"Data\INI\Object\Specter\Ukrainian Armed Forces\Wheleed\Centauro B2.ini",
        "new_btn": "Command_ConstructSpecterEU5_CentauroB2",
        "new_obj": "Specter_EU5_CentauroB2",
    },
    {
        "slot": 8,
        "old_btn": "Command_ConstructUkraineVehicleIRIST",
        "old_obj": "UkraineVehicleIRIST",
        "src_key": r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airdefense\IRIST_SLX.ini",
        "new_btn": "Command_ConstructSpecterEU5_IRIST",
        "new_obj": "Specter_EU5_IRIST",
    },
    {
        "slot": 9,
        "old_btn": "Command_ConstructUkraineVehicleTRML4D",
        "old_obj": "UkraineVehicleTRML4D",
        "src_key": r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airdefense\TRML4D.ini",
        "new_btn": "Command_ConstructSpecterEU5_TRML4D",
        "new_obj": "Specter_EU5_TRML4D",
    },
    {
        "slot": 10,
        "old_btn": "Command_ConstructUkraineVehicleM142ATACMS",
        "old_obj": "UkraineVehicleM142ATACMS",
        "src_key": r"Data\INI\Object\Specter\Ukrainian Armed Forces\Wheleed\M142_ATACMS.ini",
        "new_btn": "Command_ConstructSpecterEU5_M142ATACMS",
        "new_obj": "Specter_EU5_M142ATACMS",
    },
]


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes) -> dict[str, bytes]:
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


def parse_index(data: bytes):
    archive_size = struct.unpack(">I", data[4:8])[0]
    count = struct.unpack(">I", data[8:12])[0]
    header_size = struct.unpack(">I", data[12:16])[0]
    pos = 16
    files = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files.append((name, off, size))
    return archive_size, count, header_size, pos, files


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    expected = header
    for name, off, size in sorted(files, key=lambda x: x[1]):
        if off != expected:
            issues.append(f"overlap/gap {name}")
            break
        expected = off + size
    if expected != len(blob):
        issues.append("trailing gap/overflow")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def command_block(text: str, kind: str, name: str) -> str | None:
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text))
    return matches[-1].group(0) if matches else None


def slot_map(block: str | None) -> dict[int, str]:
    out: dict[int, str] = {}
    if not block:
        return out
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def field(block: str | None, key: str) -> str:
    if not block:
        return ""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block, re.M)
    return m.group(1).strip() if m else ""


def first_object(text: str, name: str) -> str:
    m = re.search(rf"(?ms)^Object {re.escape(name)}\r?\n.*?(?=^Object |\Z)", text)
    if not m:
        raise SystemExit(f"missing Object {name}")
    return m.group(0).rstrip() + "\r\n"


def strip_prerequisites(block: str) -> str:
    new, n = re.subn(
        r"(?ms)^[ \t]*Prerequisites\s*\r?\n.*?^[ \t]*End\r?\n",
        "",
        block,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"Prerequisites strip failed ({n})")
    if re.search(r"^\s*Prerequisites\b", new, re.M):
        raise SystemExit("Prerequisites residue remains")
    if re.search(r"^\s*Object\s*=\s*UkraineStrategyCenter", new, re.M):
        raise SystemExit("UkraineStrategyCenter prereq remains")
    if re.search(r"^\s*Science\s*=", new, re.M):
        raise SystemExit("Science prereq remains")
    return new


def clone_object(src_text: str, old_name: str, new_name: str) -> str:
    block = first_object(src_text, old_name)
    block = strip_prerequisites(block)
    block = block.replace(f"Object {old_name}", f"Object {new_name}", 1)
    header = (
        "; SPECTER EU5 unlocked clone of "
        f"{old_name}.\r\n"
        "; Prerequisites stripped so Germany/France/Britain/Italy/Turkey\r\n"
        "; can build it from the War Factory without UkraineStrategyCenter.\r\n"
        "; Shared Ukraine object is unchanged.\r\n"
        "\r\n"
    )
    return header + block


def patch_commandsets(cs: str) -> str:
    for set_name in TARGET_SETS:
        old = command_block(cs, "CommandSet", set_name)
        if not old:
            raise SystemExit(f"missing {set_name}")
        new = old
        for lock in sorted(LOCKS, key=lambda x: len(x["old_btn"]), reverse=True):
            if lock["old_btn"] not in new:
                raise SystemExit(f"{set_name} missing {lock['old_btn']}")
            new = new.replace(lock["old_btn"], lock["new_btn"])
        sl = slot_map(new)
        for slot, btn in FREE_SLOTS.items():
            if sl.get(slot) != btn:
                raise SystemExit(f"{set_name} free slot {slot} {sl.get(slot)}")
        for lock in LOCKS:
            if sl.get(lock["slot"]) != lock["new_btn"]:
                raise SystemExit(f"{set_name} slot {lock['slot']} {sl.get(lock['slot'])}")
        if sl.get(14) != "Command_Sell":
            raise SystemExit(f"{set_name} sell {sl.get(14)}")
        idx = cs.rfind(old)
        cs = cs[:idx] + new + cs[idx + len(old) :]
    return cs


def add_buttons(cb: str) -> str:
    last_old = command_block(cb, "CommandButton", LOCKS[-1]["old_btn"])
    if not last_old:
        raise SystemExit("missing Ukraine ATACMS button")
    chunks = []
    for lock in LOCKS:
        old = command_block(cb, "CommandButton", lock["old_btn"])
        if not old:
            raise SystemExit(f"missing {lock['old_btn']}")
        if command_block(cb, "CommandButton", lock["new_btn"]):
            raise SystemExit(f"{lock['new_btn']} already present")
        new = old.replace(f"CommandButton {lock['old_btn']}", f"CommandButton {lock['new_btn']}", 1)
        new, n = re.subn(
            rf"^(\s*Object\s*=\s*){re.escape(lock['old_obj'])}\s*$",
            rf"\1{lock['new_obj']}",
            new,
            count=1,
            flags=re.M,
        )
        if n != 1:
            raise SystemExit(f"Object retarget failed {lock['old_btn']}")
        if "NEED_UPGRADE" in new or re.search(r"^\s*(Science|Upgrade)\s*=", new, re.M):
            raise SystemExit(f"unlock button gained lock {lock['new_btn']}")
        chunks.append(new)
    idx = cb.rfind(last_old)
    insert_at = idx + len(last_old)
    return cb[:insert_at] + "\r\n\r\n" + "\r\n\r\n".join(chunks) + cb[insert_at:]


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    changed = sorted(k for k in set(src) | set(data) if src.get(k) != data.get(k))
    allowed = {CS_KEY, CB_KEY, UNLOCK_KEY}
    unexpected = [k for k in changed if k not in allowed]
    if unexpected:
        fails.append(f"unexpected mutated files: {unexpected[:8]}")
    if UNLOCK_KEY not in data:
        fails.append("unlock object file missing")
    if set(data) - set(src) != {UNLOCK_KEY}:
        extra = set(data) - set(src)
        if extra != {UNLOCK_KEY}:
            fails.append(f"packed file set extra {extra}")
    if set(src) - set(data):
        fails.append("packed files deleted")

    for lock in LOCKS:
        if data[lock["src_key"]] != src[lock["src_key"]]:
            fails.append(f"shared Ukraine object mutated {lock['old_obj']}")
        orig = first_object(data[lock["src_key"]].decode("latin1"), lock["old_obj"])
        if "Object = UkraineStrategyCenter" not in orig:
            fails.append(f"{lock['old_obj']} lost Strategy Center prereq")

    if data[UA_WF_KEY] != src[UA_WF_KEY]:
        fails.append("Ukraine WF object mutated")
    if data[US_WF_KEY] != src[US_WF_KEY]:
        fails.append("USA WF mutated")
    if data[SE_WF_KEY] != src[SE_WF_KEY]:
        fails.append("Sweden WF mutated")

    cs = data[CS_KEY].decode("latin1")
    src_cs = src[CS_KEY].decode("latin1")
    cb = data[CB_KEY].decode("latin1")
    unlock = data[UNLOCK_KEY].decode("latin1")

    if command_block(cs, "CommandSet", DONOR_SET) != command_block(src_cs, "CommandSet", DONOR_SET):
        fails.append("Ukraine CommandSet mutated")
    ukr = slot_map(command_block(cs, "CommandSet", DONOR_SET))
    if ukr.get(14) != "Command_Sell":
        fails.append("Ukraine sell")
    for lock in LOCKS:
        if ukr.get(lock["slot"]) != lock["old_btn"]:
            fails.append(f"Ukraine slot {lock['slot']} retargeted")

    for set_name in TARGET_SETS:
        sl = slot_map(command_block(cs, "CommandSet", set_name))
        src_sl = slot_map(command_block(src_cs, "CommandSet", set_name))
        if sl.get(14) != "Command_Sell" or src_sl.get(14) != "Command_Sell":
            fails.append(f"{set_name} sell")
        for slot, btn in FREE_SLOTS.items():
            if sl.get(slot) != btn:
                fails.append(f"{set_name} slot {slot} changed")
        for lock in LOCKS:
            if sl.get(lock["slot"]) != lock["new_btn"]:
                fails.append(f"{set_name} slot {lock['slot']} {sl.get(lock['slot'])}")
            if src_sl.get(lock["slot"]) != lock["old_btn"]:
                fails.append(f"baseline {set_name} slot {lock['slot']}")
        if sorted(k for k in set(sl) | set(src_sl) if sl.get(k) != src_sl.get(k)) != [4, 5, 6, 7, 8, 9, 10]:
            fails.append(f"{set_name} unexpected slot edits")

    for lock in LOCKS:
        clone = first_object(unlock, lock["new_obj"])
        if re.search(r"^\s*Prerequisites\b", clone, re.M):
            fails.append(f"{lock['new_obj']} still has Prerequisites")
        if re.search(r"^\s*Science\s*=", clone, re.M):
            fails.append(f"{lock['new_obj']} Science prereq")
        orig = first_object(data[lock["src_key"]].decode("latin1"), lock["old_obj"])
        if field(clone, "BuildCost") != field(orig, "BuildCost"):
            fails.append(f"{lock['new_obj']} BuildCost")
        btn = command_block(cb, "CommandButton", lock["new_btn"])
        if field(btn, "Command") != "UNIT_BUILD" or field(btn, "Object") != lock["new_obj"]:
            fails.append(f"{lock['new_btn']} button")
        if "NEED_UPGRADE" in (btn or "") or re.search(r"^\s*(Science|Upgrade)\s*=", btn or "", re.M):
            fails.append(f"{lock['new_btn']} lock fields")
        old_btn = command_block(cb, "CommandButton", lock["old_btn"])
        src_btn = command_block(src[CB_KEY].decode("latin1"), "CommandButton", lock["old_btn"])
        if old_btn != src_btn:
            fails.append(f"original {lock['old_btn']} mutated")

    se = first_object(data[SE_WF_KEY].decode("latin1"), "SwedenWarFactory")
    if field(se, "CommandSet") != "AmericaWarFactoryCommandSet_T3":
        fails.append("Sweden roster lost")
    us = first_object(data[US_WF_KEY].decode("latin1"), "AmericaWarFactory_T")
    if field(us, "CommandSet") != "AmericaWarFactoryCommandSet_T":
        fails.append("USA WF CommandSet lost")
    ua = first_object(data[UA_WF_KEY].decode("latin1"), "UkraineWarFactory")
    if field(ua, "CommandSet") != DONOR_SET:
        fails.append("Ukraine WF CommandSet lost")

    for country, btn in (
        ("India", "Command_ConstructIndia_CommandCenter"),
        ("Pakistan", "Command_ConstructPakistan_CommandCenter"),
        ("SaudiArabia", "Command_ConstructSaudiArabia_CommandCenter"),
        ("UAE", "Command_ConstructUAE_CommandCenter"),
        ("Libya", "Command_ConstructLibya_CommandCenter"),
        ("Syria", "Command_ConstructSyria_CommandCenter"),
        ("SouthAfrica", "Command_ConstructSouthAfrica_CommandCenter"),
    ):
        d = command_block(cs, "CommandSet", f"{country}DozerCommandSet")
        if slot_map(d).get(2) != btn:
            fails.append(f"PR #584 {country} Dozer construct lost")

    if data[R11_KEY] != src[R11_KEY]:
        fails.append("9P117.ini mutated")
    if b"BuildCost       = 1200" not in data[R11_KEY] or b"SRBM_ALHIJARAH_HE" not in data[R11_KEY]:
        fails.append("MOTHER cost/weapon changed")
    if data[FACTORY_KEY] != src[FACTORY_KEY]:
        fails.append("missile factory mutated")
    if data[UNIT_A_KEY] != src[UNIT_A_KEY]:
        fails.append("Al-Fahd500 mutated")
    if data[WEAPON_KEY] != src[WEAPON_KEY]:
        fails.append("Weapon.ini mutated")
    if data[LOCO_KEY] != src[LOCO_KEY]:
        fails.append("Locomotor.ini mutated")
    if data[UPGRADE_KEY] != src[UPGRADE_KEY]:
        fails.append("Upgrade.ini mutated")
    if data[PT_KEY] != src[PT_KEY]:
        fails.append("PlayerTemplate.ini mutated")
    return fails


def dump_extract(extracted: dict[str, bytes]) -> None:
    stage = OUT / "LAST_WINS_EXTRACT/DATA"
    keys = [CS_KEY, CB_KEY, UNLOCK_KEY, UA_WF_KEY, US_WF_KEY, SE_WF_KEY]
    for lock in LOCKS:
        keys.append(lock["src_key"])
    for rel in keys:
        p = stage / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing PR #588 DATA BIG at {SRC_DATA}")
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("PR #588 DATA baseline mismatch")
    if SRC_ART.is_file():
        if SRC_ART.stat().st_size != BASE_ART_SIZE or sha256_path(SRC_ART) != BASE_ART_SHA:
            raise SystemExit("ART baseline mismatch")

    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)
    parts = []
    for lock in LOCKS:
        parts.append(clone_object(data[lock["src_key"]].decode("latin1"), lock["old_obj"], lock["new_obj"]))
    data[UNLOCK_KEY] = ("\r\n".join(parts)).encode("latin1")
    data[CS_KEY] = patch_commandsets(data[CS_KEY].decode("latin1")).encode("latin1")
    data[CB_KEY] = add_buttons(data[CB_KEY].decode("latin1")).encode("latin1")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    packed_data = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed_data)
    extracted = parse_big(out_data.read_bytes())
    dump_extract(extracted)

    fails = validate(extracted, src)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed_data))

    data_sha = sha256_path(out_data)
    report = [
        "# SPECTER EU5 War Factory: unlock Ukraine vehicles at game start",
        "",
        "Baseline DATA: PR #588 (EU5 = Ukraine roster on PR #587/#584).",
        "Baseline ART: PR #574 / PR #588 ART BIG (unchanged, not rebuilt).",
        "",
        "Lock: Object Prerequisites Object = UkraineStrategyCenter on slots 4-10.",
        "CommandButtons have no NEED_UPGRADE. Slots 1-3 already unrestricted.",
        "Clones + new UNIT_BUILD buttons for Germany/France/Britain/Italy/Turkey only.",
        "Ukraine CommandSet and Ukraine vehicle objects unchanged.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART SHA256 (unchanged): {BASE_ART_SHA}",
        f"- ART size (unchanged): {BASE_ART_SIZE}",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        report.append("RUNTIME_TEST=NOT RUN")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static / packed last-wins)",
        "- slots 1-3 original Ukraine buttons (no Object Prerequisites)",
        "- slots 4-10 unlocked clones (no UkraineStrategyCenter / Science / NEED_UPGRADE)",
        "- Command_Sell remains INI slot 14 (11th command; PR #588 layout)",
        "- button order otherwise unchanged",
        "- Ukraine CommandSet and shared Ukraine objects unchanged",
        "- USA and Sweden War Factories unchanged",
        "- ART not rebuilt",
        "",
        "Static validation completed; runtime game test not performed.",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=NO\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted)}\n"
        "ART_FILE=PR574/PR588 _SPEC_ART_ONE.big (not rebuilt)\n"
        f"ART_SIZE={BASE_ART_SIZE}\n"
        f"ART_SHA256={BASE_ART_SHA}\n"
        "TARGETS=Germany,France,Britain,Italy,Turkey\n"
        "UNLOCKED_SLOTS=4-10 (UkraineStrategyCenter clones)\n"
        "FREE_SLOTS=1-3 (already unrestricted)\n"
        "SELL_SLOT=14\n"
        "CHANGED_FILES=Data\\INI\\CommandSet.ini, Data\\INI\\CommandButton.ini, Data\\INI\\Object\\Specter\\EU5Unlock\\Specter_EU5WFUnlock.ini\n"
        "BASELINE_DATA=PR #588\n"
        "BASELINE_ART=PR #574\n"
        "UKRAINE=UNCHANGED\n"
        "USA_WARFACTORY=UNCHANGED\n"
        "SWEDEN_WARFACTORY=UNCHANGED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: unlock Ukraine WF vehicles at start for 5 EU countries\n"
        "\n"
        "Germany, France, Britain, Italy, and Turkey keep the PR #588\n"
        "Ukraine 10-vehicle roster. Slots 4-10 are now immediately\n"
        "buildable (no UkraineStrategyCenter). Ukraine itself is unchanged.\n"
        "\n"
        "Place this complete replacement DATA BIG in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "\n"
        "Keep the existing PR #574/_SPEC_ART_ONE.big (not rebuilt):\n"
        f"  SHA256={BASE_ART_SHA}\n"
        "\n"
        "Static validation completed; runtime game test not performed.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_EU5_WF_UNLOCK_START.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
