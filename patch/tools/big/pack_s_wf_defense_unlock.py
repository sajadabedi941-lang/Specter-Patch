#!/usr/bin/env python3
"""Unlock two War Factory defenses for 5 SPECTER countries on PR #584.

Starts from packed PR #584 _SPEC_DATA_ONE.big
  SHA256 3802cafba1af5609e0725d32cdc5f4d0e9e8a183746d9c85070854ea06c1e3af

Does NOT import PR #585+. Does NOT rebuild ART (PR #574).
Does NOT modify USA/Iraq/Russia/China War Factories, missiles, MOTHER,
or Command Center construction.

Forensic (engine-loaded last-wins on PR #584):
  India/Pakistan/SouthKorea/Japan/Vietnam WarFactory CommandSets all
  produce the America roster. Two entries are locked by Object
  Prerequisites inherited from the shared USA objects:

    slot 10 Command_ConstructAmericaVehicleTHAAD
      Object US_THAAD
      Prerequisites Object = AmericaStrategyCenter AmericaStrategyCenter_T

    slot 12 Command_ConstructAmericaVehicleM1075I
      Object US_M1075I_Trident
      Prerequisites Object = AmericaStrategyCenter_T
                   Science = SCIENCE_M1075I

Those countries never get AmericaStrategyCenter / SCIENCE_M1075I, so the
two buttons stay greyed. CommandButtons themselves have no NEED_UPGRADE.

Fix: country-specific CommandButtons + unlocked clone objects (same
stats/model/weapons, Prerequisites stripped). Only the five countries'
WarFactory CommandSets are retargeted. Shared USA objects and USA
CommandSets are unchanged. SCIENCE_M1075I / Strategy Center remain for USA.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_CC_MATCH_START_BUILD/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_DATA_BCDHIJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_WF_DEFENSE_UNLOCK"

BASE_DATA_SHA = "3802cafba1af5609e0725d32cdc5f4d0e9e8a183746d9c85070854ea06c1e3af"
BASE_DATA_SIZE = 366461184
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
THAAD_KEY = r"Data\INI\Object\Specter\United States Of America\AirDefense\US_M1120.ini"
M1075_KEY = r"Data\INI\Object\Specter\United States Of America\Wheeled\US_MGM134.ini"
UNLOCK_KEY = r"Data\INI\Object\Specter\WFUnlock\Specter_WFDefenseUnlock.ini"

BTN_THAAD_OLD = "Command_ConstructAmericaVehicleTHAAD"
BTN_M1075_OLD = "Command_ConstructAmericaVehicleM1075I"
BTN_THAAD_NEW = "Command_ConstructSpecterWF_THAAD"
BTN_M1075_NEW = "Command_ConstructSpecterWF_M1075I"
OBJ_THAAD_OLD = "US_THAAD"
OBJ_M1075_OLD = "US_M1075I_Trident"
OBJ_THAAD_NEW = "Specter_WF_THAAD"
OBJ_M1075_NEW = "Specter_WF_M1075I"

COUNTRY_SETS = [
    "India_WarFactoryCommandSet",
    "India_WarFactoryCommandSet1",
    "India_WarFactoryCommandSet2",
    "India_WarFactoryCommandSet3",
    "Pakistan_WarFactoryCommandSet",
    "SouthKorea_WarFactoryCommandSet",
    "Japan_WarFactoryCommandSet",
    "Vietnam_WarFactoryCommandSet",
]
USA_SETS = [
    "AmericaWarFactoryCommandSet",
    "AmericaWarFactoryCommandSet_T",
    "AmericaWarFactoryCommandSet_T1",
    "AmericaWarFactoryCommandSet_T2",
    "AmericaWarFactoryCommandSet_T3",
]
CONTROL_SETS = [
    "Iraq_WarFactoryCommandSet",
    "SaudiArabia_WarFactoryCommandSet",
    "UAE_WarFactoryCommandSet",
    "Libya_WarFactoryCommandSet",
    "Syria_WarFactoryCommandSet",
    "SouthAfrica_WarFactoryCommandSet",
    "RussiaWarFactoryCommandSet",
    "ChinaWarFactoryCommandSet",
]

THAAD_BTN = (
    "CommandButton Command_ConstructSpecterWF_THAAD\r\n"
    "  Command       = UNIT_BUILD\r\n"
    "  Object        = Specter_WF_THAAD\r\n"
    "  TextLabel     = CONTROLBAR:ConstructAmericathaad\r\n"
    "  ButtonImage   = us_thaad\r\n"
    "  ButtonBorderType        = BUILD\r\n"
    "  DescriptLabel           = CONTROLBAR:ToolTipUSABuildthaad\r\n"
    "End"
)
M1075_BTN = (
    "CommandButton Command_ConstructSpecterWF_M1075I\r\n"
    "  Command       = UNIT_BUILD\r\n"
    "  Object        = Specter_WF_M1075I\r\n"
    "  TextLabel     = CONTROLBAR:ConstructAmericaVehicleM1075I\r\n"
    "  ButtonImage   = us_m1075i\r\n"
    "  ButtonBorderType        = BUILD\r\n"
    "  DescriptLabel           = CONTROLBAR:ToolTipUSABuildM1075I\r\n"
    "End"
)


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


def first_object_block(text: str, name: str) -> str:
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
    if "AmericaStrategyCenter" in new.split("Object ", 1)[-1][:800]:
        # Strategy Center may still appear in comments/modules; only fail if still a prereq
        pass
    if re.search(r"^\s*Science\s*=\s*SCIENCE_M1075I", new, re.M):
        raise SystemExit("SCIENCE_M1075I prereq remains")
    return new


def clone_object(src_text: str, old_name: str, new_name: str) -> str:
    block = first_object_block(src_text, old_name)
    block = strip_prerequisites(block)
    block = block.replace(f"Object {old_name}", f"Object {new_name}", 1)
    header = (
        "; SPECTER country War Factory unlocked clone of "
        f"{old_name}.\r\n"
        "; Same stats/model/weapons. Prerequisites stripped so India/\r\n"
        "; Pakistan/SouthKorea/Japan/Vietnam can build it from the War\r\n"
        "; Factory without AmericaStrategyCenter / SCIENCE_M1075I.\r\n"
        "; Shared USA object is unchanged.\r\n"
        "\r\n"
    )
    return header + block


def patch_commandset(cs: str) -> str:
    for set_name in COUNTRY_SETS:
        old = command_block(cs, "CommandSet", set_name)
        if not old:
            raise SystemExit(f"missing {set_name}")
        new = old.replace(BTN_THAAD_OLD, BTN_THAAD_NEW).replace(BTN_M1075_OLD, BTN_M1075_NEW)
        if new == old:
            raise SystemExit(f"{set_name}: no locked buttons to replace")
        if BTN_THAAD_OLD in new or BTN_M1075_OLD in new:
            raise SystemExit(f"{set_name}: locked button residue")
        slots = slot_map(new)
        if slots.get(10) != BTN_THAAD_NEW or slots.get(12) != BTN_M1075_NEW:
            raise SystemExit(f"{set_name} slots {slots}")
        idx = cs.rfind(old)
        cs = cs[:idx] + new + cs[idx + len(old) :]
    return cs


def add_buttons(cb: str) -> str:
    if command_block(cb, "CommandButton", BTN_THAAD_NEW):
        raise SystemExit("THAAD unlock button already present")
    thaad = command_block(cb, "CommandButton", BTN_THAAD_OLD)
    m1075 = command_block(cb, "CommandButton", BTN_M1075_OLD)
    if not thaad or not m1075:
        raise SystemExit("missing baseline America construct buttons")
    idx = cb.rfind(m1075)
    insert_at = idx + len(m1075)
    return cb[:insert_at] + "\r\n\r\n" + THAAD_BTN + "\r\n\r\n" + M1075_BTN + cb[insert_at:]


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    changed = sorted(k for k in set(src) | set(data) if src.get(k) != data.get(k))
    allowed = {CS_KEY, CB_KEY, UNLOCK_KEY}
    unexpected = [k for k in changed if k not in allowed]
    if unexpected:
        fails.append(f"unexpected mutated files: {unexpected[:8]}")
    if UNLOCK_KEY not in data:
        fails.append("unlock object file missing from BIG")
    if set(data) - set(src) != {UNLOCK_KEY}:
        extra = set(data) - set(src)
        if extra != {UNLOCK_KEY}:
            fails.append(f"packed file set extra {extra}")
    if set(src) - set(data):
        fails.append("packed files deleted")

    if data[THAAD_KEY] != src[THAAD_KEY]:
        fails.append("shared US_THAAD file mutated")
    if data[M1075_KEY] != src[M1075_KEY]:
        fails.append("shared US_M1075I file mutated")

    cs = data[CS_KEY].decode("latin1")
    src_cs = src[CS_KEY].decode("latin1")
    cb = data[CB_KEY].decode("latin1")
    unlock = data[UNLOCK_KEY].decode("latin1")

    thaad_obj = command_block(unlock, "Object", OBJ_THAAD_NEW) or first_object_block(unlock, OBJ_THAAD_NEW)
    m1075_obj = command_block(unlock, "Object", OBJ_M1075_NEW) or first_object_block(unlock, OBJ_M1075_NEW)
    if re.search(r"^\s*Prerequisites\b", thaad_obj, re.M):
        fails.append("Specter_WF_THAAD still has Prerequisites")
    if re.search(r"^\s*Prerequisites\b", m1075_obj, re.M):
        fails.append("Specter_WF_M1075I still has Prerequisites")
    if re.search(r"^\s*Science\s*=", m1075_obj, re.M):
        fails.append("Specter_WF_M1075I still has Science prereq")
    if field(thaad_obj, "BuildCost") != "3000" or "Model                   = US_M1120" not in thaad_obj:
        fails.append("THAAD clone stats/model")
    if field(m1075_obj, "BuildCost") != "3400" or "Model             = US_MGM134" not in m1075_obj:
        fails.append("M1075I clone stats/model")

    thaad_btn = command_block(cb, "CommandButton", BTN_THAAD_NEW)
    m1075_btn = command_block(cb, "CommandButton", BTN_M1075_NEW)
    if field(thaad_btn, "Object") != OBJ_THAAD_NEW or field(thaad_btn, "Command") != "UNIT_BUILD":
        fails.append("THAAD unlock button")
    if field(m1075_btn, "Object") != OBJ_M1075_NEW or field(m1075_btn, "Command") != "UNIT_BUILD":
        fails.append("M1075I unlock button")
    if "NEED_UPGRADE" in (thaad_btn or "") or "NEED_UPGRADE" in (m1075_btn or ""):
        fails.append("unlock buttons gained NEED_UPGRADE")

    old_thaad = command_block(cb, "CommandButton", BTN_THAAD_OLD)
    old_m1075 = command_block(cb, "CommandButton", BTN_M1075_OLD)
    src_thaad = command_block(src[CB_KEY].decode("latin1"), "CommandButton", BTN_THAAD_OLD)
    src_m1075 = command_block(src[CB_KEY].decode("latin1"), "CommandButton", BTN_M1075_OLD)
    if old_thaad != src_thaad or old_m1075 != src_m1075:
        fails.append("original America construct buttons mutated")

    for set_name in COUNTRY_SETS:
        sl = slot_map(command_block(cs, "CommandSet", set_name))
        src_sl = slot_map(command_block(src_cs, "CommandSet", set_name))
        if sl.get(10) != BTN_THAAD_NEW or sl.get(12) != BTN_M1075_NEW:
            fails.append(f"{set_name} slots 10/12 {sl.get(10)} {sl.get(12)}")
        for k, v in src_sl.items():
            if k in (10, 12):
                continue
            if sl.get(k) != v:
                fails.append(f"{set_name} unrelated slot {k} changed")

    for set_name in USA_SETS + CONTROL_SETS:
        a = command_block(cs, "CommandSet", set_name)
        b = command_block(src_cs, "CommandSet", set_name)
        if a != b:
            fails.append(f"{set_name} mutated")

    dozer = command_block(cs, "CommandSet", "IndiaDozerCommandSet")
    if slot_map(dozer).get(2) != "Command_ConstructIndia_CommandCenter":
        fails.append("PR #584 India Dozer Command Center construct lost")
    for country in ("Pakistan", "SaudiArabia", "UAE", "Libya", "Syria", "SouthAfrica"):
        d = command_block(cs, "CommandSet", f"{country}DozerCommandSet")
        if slot_map(d).get(2) != f"Command_Construct{country}_CommandCenter":
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
    loc = data[LOCO_KEY].decode("latin1")
    if not command_block(loc, "Locomotor", "R11SRBMLocomotor"):
        fails.append("R11SRBMLocomotor missing")
    if re.search(r"^Locomotor Iraq_Al(HusseinII|SamoudII|Abbas|Basrah|Nasir|Mansour)_Locomotor", loc, re.M):
        fails.append("later dedicated missile locos leaked")
    for k in data:
        lk = k.replace("/", "\\").lower()
        if "iraq-al" in lk and "specter" in lk:
            fails.append(f"hyphenated Specter alias leaked {k}")
    for obj in ("Iraq_AlHusseinII", "Iraq_AlSamoudII", "Iraq_AlAbbas", "Iraq_AlBasrah", "Iraq_AlNasir", "Iraq_AlMansour"):
        key = rf"Data\INI\Object\Specter\Iraq Army\Wheeled\{obj}.ini"
        if data.get(key) != src.get(key):
            fails.append(f"{obj} mutated vs PR #584")
        if "CommandSet    = Scud_B_CommandSet" not in data.get(key, b"").decode("latin1"):
            fails.append(f"{obj} lost Scud_B_CommandSet")
    fac = command_block(cs, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet")
    src_fac = command_block(src_cs, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet")
    if fac != src_fac:
        fails.append("Iraq missile factory CommandSet mutated")
    return fails


def dump_extract(extracted: dict[str, bytes]) -> None:
    stage = OUT / "LAST_WINS_EXTRACT/DATA"
    keys = [CS_KEY, CB_KEY, UNLOCK_KEY, THAAD_KEY, M1075_KEY, R11_KEY, FACTORY_KEY, UNIT_A_KEY, PT_KEY]
    for rel in keys:
        p = stage / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing PR #584 DATA BIG at {SRC_DATA}")
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("PR #584 DATA baseline mismatch")
    if SRC_ART.is_file():
        if SRC_ART.stat().st_size != BASE_ART_SIZE or sha256_path(SRC_ART) != BASE_ART_SHA:
            raise SystemExit("PR #574 ART baseline mismatch")

    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)
    thaad_src = data[THAAD_KEY].decode("latin1")
    m1075_src = data[M1075_KEY].decode("latin1")
    unlock = clone_object(thaad_src, OBJ_THAAD_OLD, OBJ_THAAD_NEW)
    unlock += "\r\n"
    unlock += clone_object(m1075_src, OBJ_M1075_OLD, OBJ_M1075_NEW)
    data[UNLOCK_KEY] = unlock.encode("latin1")
    data[CS_KEY] = patch_commandset(data[CS_KEY].decode("latin1")).encode("latin1")
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
        "# SPECTER War Factory: unlock two defenses for 5 countries",
        "",
        "Baseline DATA: PR #584 (CC start=construct + PR #583 missiles).",
        "Baseline ART: PR #574 ART BIG (unchanged, not rebuilt).",
        "PR #585+ NOT imported.",
        "",
        "INDIA / PAKISTAN / SOUTH KOREA / JAPAN / VIETNAM",
        f"  Defense #1 Object = {OBJ_THAAD_OLD} (unlocked clone {OBJ_THAAD_NEW})",
        "  Old lock = Prerequisites Object AmericaStrategyCenter / AmericaStrategyCenter_T",
        f"  Defense #2 Object = {OBJ_M1075_OLD} (unlocked clone {OBJ_M1075_NEW})",
        "  Old lock = Prerequisites Object AmericaStrategyCenter_T + Science SCIENCE_M1075I",
        "  CommandSet = <Country>_WarFactoryCommandSet slots 10 and 12",
        "  Lock was inherited from shared USA objects, not country-specific NEED_UPGRADE.",
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
        "- five countries: WF slots 10/12 now UNIT_BUILD unlocked clones (no Strategy Center / SCIENCE_M1075I)",
        "- clone stats/model/cost match the original USA objects",
        "- shared US_THAAD / US_M1075I_Trident files unchanged (USA WF still locked as before)",
        "- SCIENCE_M1075I definition unchanged",
        "- other countries' WarFactory CommandSets unchanged",
        "- PR #584 Command Center construct slots intact",
        "- PR #583 missile data / MOTHER / 9P117 intact",
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
        "ART_FILE=PR574 _SPEC_ART_ONE.big (not rebuilt)\n"
        f"ART_SIZE={BASE_ART_SIZE}\n"
        f"ART_SHA256={BASE_ART_SHA}\n"
        f"DEFENSE_1={OBJ_THAAD_OLD}->{OBJ_THAAD_NEW}\n"
        f"DEFENSE_2={OBJ_M1075_OLD}->{OBJ_M1075_NEW}\n"
        "COUNTRIES=India,Pakistan,SouthKorea,Japan,Vietnam\n"
        "CHANGED_FILES=Data\\INI\\CommandSet.ini, Data\\INI\\CommandButton.ini, Data\\INI\\Object\\Specter\\WFUnlock\\Specter_WFDefenseUnlock.ini\n"
        "BASELINE_DATA=PR #584\n"
        "BASELINE_ART=PR #574\n"
        "PR585PLUS=NOT IMPORTED\n"
        "CC_CONSTRUCT=UNCHANGED\n"
        "MISSILES=UNCHANGED\n"
        "MOTHER_GAMEPLAY=UNCHANGED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER War Factory: unlock two defenses\n"
        "Countries: India, Pakistan, South Korea, Japan, Vietnam\n"
        "\n"
        "War Factory slot 10 (THAAD) and slot 12 (M1075I/Trident) are now\n"
        "buildable without AmericaStrategyCenter / SCIENCE_M1075I.\n"
        "USA objects and USA War Factory remain locked as before.\n"
        "\n"
        "Place this complete replacement DATA BIG in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "\n"
        "Keep the existing PR #574 ART BIG (do not replace ART):\n"
        "  _SPEC_ART_ONE.big\n"
        f"  SHA256={BASE_ART_SHA}\n"
        "\n"
        "PR #584 Command Center start=construct fix remains.\n"
        "PR #583 missile spawn-fix remains. ART not rebuilt.\n"
        "\n"
        "Static validation completed; runtime game test not performed.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_WF_DEFENSE_UNLOCK.zip"
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
