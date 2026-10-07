#!/usr/bin/env python3
"""Remove India's two Radar drones on the PR #584 DATA baseline.

Starts from packed PR #584 _SPEC_DATA_ONE.big
  SHA256 3802cafba1af5609e0725d32cdc5f4d0e9e8a183746d9c85070854ea06c1e3af

Does NOT import PR #585+. Does NOT rebuild ART (PR #574).
Does NOT modify Command Center construction, missiles, MOTHER/9P117,
or any other country's radar/drone CommandSets.

Forensic (engine-loaded last-wins on PR #584):
  Object India_RadarStation
    CommandSet = India_RadarCommandSet
  CommandSet India_RadarCommandSet
    1 = Command_ConstructIndia_CombatDrone   -> Object India_CombatDrone
    2 = Command_ConstructIndia_LoiteringDrone -> Object India_LoiteringDrone
    13 = Command_SetRallyPoint
    14 = Command_Sell

Those two UNIT_BUILD buttons are the only Radar association. The Radar
object itself does not SpawnBehavior the drones. India_HeavyAirBaseCommandSet
also produces the same two objects; those airbase slots are left intact.
The Object definitions are India-specific but still used by Heavy Air Base,
so they are not deleted.

Fix: strip slots 1 and 2 from engine-loaded India_RadarCommandSet only.
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
OUT = ROOT / "patch/Release/SPECTER_INDIA_RADAR_DRONES"

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
RADAR_KEY = r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_RadarStation.ini"
CC_KEY = r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_CommandCenter.ini"
COMBAT_KEY = r"Data\INI\Object\Specter\Indian Armed Forces\Drones\India_CombatDrone.ini"
LOITER_KEY = r"Data\INI\Object\Specter\Indian Armed Forces\Drones\India_LoiteringDrone.ini"
HEAVY_KEY = r"Data\INI\Object\Specter\Indian Armed Forces\Drones\India_HeavyUAV.ini"

DRONE_A = "India_CombatDrone"
DRONE_B = "India_LoiteringDrone"
BTN_A = "Command_ConstructIndia_CombatDrone"
BTN_B = "Command_ConstructIndia_LoiteringDrone"
SET_NAME = "India_RadarCommandSet"

OLD_SET = (
    "CommandSet India_RadarCommandSet\r\n"
    "  1 = Command_ConstructIndia_CombatDrone\r\n"
    "  2 = Command_ConstructIndia_LoiteringDrone\r\n"
    "  13 = Command_SetRallyPoint\r\n"
    "  14 = Command_Sell\r\n"
    "End"
)
NEW_SET = (
    "CommandSet India_RadarCommandSet\r\n"
    "  13 = Command_SetRallyPoint\r\n"
    "  14 = Command_Sell\r\n"
    "End"
)

CONTROL_RADAR_SETS = [
    "Pakistan_RadarCommandSet",
    "SaudiArabia_RadarCommandSet",
    "UAE_RadarCommandSet",
    "Libya_RadarCommandSet",
    "Syria_RadarCommandSet",
    "SouthAfrica_RadarCommandSet",
    "Iraq_RadarStationCommandSet",
    "AmericaRadarStationCommandSet",
    "RussiaRadarStationCommandSet",
    "ChinaRadarStationCommandSet",
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


def patch_commandset(cs: str) -> str:
    blk = command_block(cs, "CommandSet", SET_NAME)
    if blk != OLD_SET:
        raise SystemExit(f"{SET_NAME} baseline mismatch:\n{blk!r}")
    idx = cs.rfind(blk)
    if idx < 0:
        raise SystemExit("India_RadarCommandSet splice failed")
    return cs[:idx] + NEW_SET + cs[idx + len(blk) :]


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    changed = sorted(k for k in set(src) | set(data) if src.get(k) != data.get(k))
    if changed != [CS_KEY]:
        fails.append(f"changed files {changed} (expected only CommandSet.ini)")
    if set(data) != set(src):
        fails.append("packed file set changed")

    cs = data[CS_KEY].decode("latin1")
    src_cs = src[CS_KEY].decode("latin1")
    radar = data[RADAR_KEY].decode("latin1")
    src_radar = src[RADAR_KEY].decode("latin1")

    if radar != src_radar:
        fails.append("India_RadarStation.ini mutated")
    if "Object India_RadarStation" not in radar:
        fails.append("India_RadarStation object missing")
    if "CommandSet          = India_RadarCommandSet" not in radar:
        fails.append("India_RadarStation lost CommandSet link")
    if "Behavior = GrantUpgradeCreate ModuleTag_0xd99" not in radar:
        fails.append("India radar GrantUpgradeCreate missing")
    if "UpgradeToGrant    = Upgrade_AmericaRadar" not in radar:
        fails.append("India radar Upgrade_AmericaRadar missing")
    if "Behavior        = RadarUpgrade ModuleTag_0d995" not in radar:
        fails.append("India RadarUpgrade missing")
    if "RadarPriority       = STRUCTURE" not in radar:
        fails.append("India RadarPriority missing")
    if "SpecialPowerSpySatellite" not in radar:
        fails.append("India SpySatellite scan missing")

    new_set = command_block(cs, "CommandSet", SET_NAME)
    if new_set != NEW_SET:
        fails.append(f"India_RadarCommandSet last-wins {new_set!r}")
    slots = slot_map(new_set)
    if BTN_A in (new_set or "") or BTN_B in (new_set or ""):
        fails.append("Radar CommandSet still has drone buttons")
    if slots.get(13) != "Command_SetRallyPoint" or slots.get(14) != "Command_Sell":
        fails.append(f"Radar CommandSet slots {slots}")
    if 1 in slots or 2 in slots:
        fails.append(f"Radar CommandSet still has production slots {slots}")
    defs = len(re.findall(rf"^CommandSet {re.escape(SET_NAME)}\b", cs, re.M))
    if defs != 1:
        fails.append(f"India_RadarCommandSet definition count {defs}")

    air = command_block(cs, "CommandSet", "India_HeavyAirBaseCommandSet")
    src_air = command_block(src_cs, "CommandSet", "India_HeavyAirBaseCommandSet")
    if air != src_air:
        fails.append("India_HeavyAirBaseCommandSet mutated")
    air_slots = slot_map(air)
    if air_slots.get(3) != BTN_A or air_slots.get(4) != BTN_B:
        fails.append("Heavy Air Base lost drone production")

    for set_name in CONTROL_RADAR_SETS:
        a = command_block(cs, "CommandSet", set_name)
        b = command_block(src_cs, "CommandSet", set_name)
        if a != b:
            fails.append(f"{set_name} mutated")

    names = set(re.findall(r"^CommandSet\s+(\S+)", cs, re.M)) | set(
        re.findall(r"^CommandSet\s+(\S+)", src_cs, re.M)
    )
    mutated_sets = []
    for set_name in sorted(names):
        if command_block(cs, "CommandSet", set_name) != command_block(src_cs, "CommandSet", set_name):
            mutated_sets.append(set_name)
    if mutated_sets != [SET_NAME]:
        fails.append(f"CommandSet mutations {mutated_sets}")

    dozer = command_block(cs, "CommandSet", "IndiaDozerCommandSet")
    worker = command_block(cs, "CommandSet", "India_WorkerCommandSet")
    if slot_map(dozer).get(2) != "Command_ConstructIndia_CommandCenter":
        fails.append("PR #584 India Dozer Command Center construct lost")
    if slot_map(worker).get(2) != "Command_ConstructIndia_CommandCenter":
        fails.append("PR #584 India Worker Command Center construct lost")
    for country in ("Pakistan", "SaudiArabia", "UAE", "Libya", "Syria", "SouthAfrica"):
        d = command_block(cs, "CommandSet", f"{country}DozerCommandSet")
        if slot_map(d).get(2) != f"Command_Construct{country}_CommandCenter":
            fails.append(f"PR #584 {country} Dozer construct lost")

    pt = data[PT_KEY]
    if pt != src[PT_KEY]:
        fails.append("PlayerTemplate.ini mutated")
    if b"StartingBuilding  = India_CommandCenter" not in pt:
        fails.append("India StartingBuilding lost")

    if data[CB_KEY] != src[CB_KEY]:
        fails.append("CommandButton.ini mutated")
    if data[CC_KEY] != src[CC_KEY]:
        fails.append("India_CommandCenter.ini mutated")
    if data[COMBAT_KEY] != src[COMBAT_KEY]:
        fails.append("India_CombatDrone.ini mutated (object should remain)")
    if data[LOITER_KEY] != src[LOITER_KEY]:
        fails.append("India_LoiteringDrone.ini mutated (object should remain)")
    if data[HEAVY_KEY] != src[HEAVY_KEY]:
        fails.append("India_HeavyUAV.ini mutated")

    cb = data[CB_KEY].decode("latin1")
    if field(command_block(cb, "CommandButton", BTN_A), "Object") != DRONE_A:
        fails.append("CombatDrone construct button Object")
    if field(command_block(cb, "CommandButton", BTN_B), "Object") != DRONE_B:
        fails.append("LoiteringDrone construct button Object")
    if field(command_block(cb, "CommandButton", "Command_ConstructIndia_RadarStation"), "Object") != "India_RadarStation":
        fails.append("Radar construct button lost")

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
    if b"ReplaceObjectUpgrade ModuleTag_Rebuild" in b"".join(v for k, v in data.items() if k.lower().endswith(".ini")):
        fails.append("ReplaceObjectUpgrade leaked back")
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
        unit = data.get(key, b"").decode("latin1")
        if "CommandSet    = Scud_B_CommandSet" not in unit:
            fails.append(f"{obj} lost Scud_B_CommandSet")

    fac = command_block(cs, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet")
    src_fac = command_block(src_cs, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet")
    if fac != src_fac:
        fails.append("Iraq missile factory CommandSet mutated")

    zzzz = r"Data\INI\CommandSet_ZZZZ_CommandCenterMatchStart.ini"
    if data.get(zzzz) != src.get(zzzz):
        fails.append("ZZZZ CommandCenterMatchStart mutated")
    for k, v in data.items():
        if "zzzz" in k.lower() and data.get(k) != src.get(k):
            fails.append(f"ZZZZ overlay mutated {k}")

    return fails


def dump_extract(extracted: dict[str, bytes]) -> None:
    stage = OUT / "LAST_WINS_EXTRACT/DATA"
    keys = [CS_KEY, CB_KEY, PT_KEY, RADAR_KEY, CC_KEY, COMBAT_KEY, LOITER_KEY, HEAVY_KEY, R11_KEY, FACTORY_KEY, UNIT_A_KEY]
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
    cs = data[CS_KEY].decode("latin1")
    data[CS_KEY] = patch_commandset(cs).encode("latin1")

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
        "# SPECTER India Radar: remove two drones",
        "",
        "Baseline DATA: PR #584 (Command Center start=construct + PR #583 missiles).",
        "Baseline ART: PR #574 ART BIG (unchanged, not rebuilt).",
        "PR #585+ NOT imported.",
        "",
        f"DRONE_1={DRONE_A}",
        f"DRONE_2={DRONE_B}",
        "SOURCE=India_RadarStation CommandSet India_RadarCommandSet slots 1 and 2",
        "MECHANISM=UNIT_BUILD CommandButtons (not SpawnBehavior / SpecialPower)",
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
        "- India_RadarStation object unchanged (detection, RadarUpgrade, SpySatellite scan)",
        "- India_RadarCommandSet no longer produces India_CombatDrone or India_LoiteringDrone",
        "- Rally + Sell remain on the Radar",
        "- India_HeavyAirBaseCommandSet still produces both drones (not Radar)",
        "- drone Object INIs not deleted (still referenced by Heavy Air Base)",
        "- other countries' Radar CommandSets unchanged",
        "- PR #584 Command Center start/build construct slots intact",
        "- PR #583 missile data / Weapon.ini / factory CommandSet / MOTHER intact",
        "- only packed file changed: Data\\INI\\CommandSet.ini",
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
        f"DRONE_1={DRONE_A}\n"
        f"DRONE_2={DRONE_B}\n"
        "CHANGED_FILES=Data\\INI\\CommandSet.ini\n"
        "CHANGED_DEF=CommandSet India_RadarCommandSet\n"
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
        "SPECTER India Radar: remove two drones\n"
        "\n"
        f"Removed from India_RadarCommandSet:\n"
        f"  {DRONE_A}\n"
        f"  {DRONE_B}\n"
        "\n"
        "Place this complete replacement DATA BIG in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "\n"
        "Keep the existing PR #574 ART BIG (do not replace ART):\n"
        "  _SPEC_ART_ONE.big\n"
        f"  SHA256={BASE_ART_SHA}\n"
        "\n"
        "India's Radar building, radar detection, and SpySatellite scan remain.\n"
        "PR #584 Command Center start=construct fix remains.\n"
        "PR #583 missile spawn-fix remains. ART not rebuilt.\n"
        "\n"
        "Static validation completed; runtime game test not performed.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_INDIA_RADAR_DRONES.zip"
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
