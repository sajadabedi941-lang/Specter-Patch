#!/usr/bin/env python3
"""Point Sweden's War Factory production at the USA player T3 roster.

Starts from packed PR #584 _SPEC_DATA_ONE.big
  SHA256 3802cafba1af5609e0725d32cdc5f4d0e9e8a183746d9c85070854ea06c1e3af

Does NOT import PR #585+. Does NOT rebuild ART (PR #574).
Does NOT modify USA War Factory, missiles, MOTHER, Command Center,
or any other country's War Factory.

Forensic (engine-loaded last-wins on PR #584):
  Sweden object SwedenWarFactory
    Data\\INI\\Object\\Specter\\Swedish Armed Forces\\Buildings\\Warfactory.ini
    CommandSet = SwedenWarfactoryCommandSet  (13 Sweden-only vehicles + Sell)
    Flag = SE__SEFlag_HsWF, Side = Sweden, model US_WarFactory
    No CommandSetUpgrade. Sweden cannot research Upgrade_US_Tier*.

  USA player object AmericaWarFactory_T
    Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\Warfactory.ini
    CommandSet = AmericaWarFactoryCommandSet_T
    CommandSetUpgrade T1/T2/T3 via Upgrade_US_Tier1/2/3 (Strategy Center)
    Full unlocked player roster = AmericaWarFactoryCommandSet_T3

Fix: retarget SwedenWarFactory CommandSet to AmericaWarFactoryCommandSet_T3
so Sweden produces the same units as the fully unlocked USA player WF,
reusing USA CommandSets/CommandButtons. Building object/flag/stats stay Swedish.
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
OUT = ROOT / "patch/Release/SPECTER_SWEDEN_WF_USA_ROSTER"

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
SE_WF_KEY = r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\Warfactory.ini"
US_WF_KEY = r"Data\INI\Object\Specter\United States Of America\Buildings\Warfactory.ini"
US_WF_AI_KEY = r"Data\INI\Object\Specter\United States Of America\Buildings\Warfactory_AI.ini"
SE_CC_KEY = r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\CommandCenter.ini"

OLD_SET = "SwedenWarfactoryCommandSet"
NEW_SET = "AmericaWarFactoryCommandSet_T3"
USA_PLAYER_SET = "AmericaWarFactoryCommandSet_T"

SWEDEN_REMOVED = [
    "Command_ConstructSwedenTankStrv122",
    "Command_ConstructSwedenTankStrv121",
    "Command_ConstructSwedenVehicleCV90R",
    "Command_ConstructSwedenVehicleCV90",
    "Command_ConstructSwedenVehiclePatgb203",
    "Command_ConstructSwedenVehicleLvkv90",
    "Command_ConstructSwedenVehicleGiraffe",
    "Command_ConstructSwedenVehiclePULS",
    "Command_ConstructSwedenVehicleRBS15",
    "Command_ConstructSwedenVehicleArcher",
    "Command_ConstructSwedenVehicleCV90AT",
    "Command_ConstructSwedenVehicleBgbv120",
    "Command_ConstructSwedenTankStrv122B",
]

CONTROL_WF_OBJECTS = [
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_WarFactory.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_WarFactory.ini",
    r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_WarFactory.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_WarFactory.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_WarFactory.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\French Armed Forces\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\Warfactory.ini",
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
    return m.group(0)


def patch_sweden_wf(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    needle = "CommandSet       = SwedenWarfactoryCommandSet"
    repl = "CommandSet       = AmericaWarFactoryCommandSet_T3"
    n = text.count(needle)
    if n != 1:
        raise SystemExit(f"Sweden CommandSet line count {n}")
    if "SE__SEFlag_HsWF" not in text:
        raise SystemExit("Sweden flag missing before patch")
    if "Side             = Sweden" not in text:
        raise SystemExit("Sweden Side missing before patch")
    text = text.replace(needle, repl, 1)
    if OLD_SET in text:
        raise SystemExit("SwedenWarfactoryCommandSet residue on object")
    if "CommandSet       = AmericaWarFactoryCommandSet_T3" not in text:
        raise SystemExit("new CommandSet not applied")
    return text.encode("latin1")


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    changed = sorted(k for k in set(src) | set(data) if src.get(k) != data.get(k))
    if changed != [SE_WF_KEY]:
        fails.append(f"unexpected changed files: {changed}")
    if set(data) != set(src):
        fails.append("packed file set changed")

    if data[US_WF_KEY] != src[US_WF_KEY]:
        fails.append("USA War Factory mutated")
    if data[US_WF_AI_KEY] != src[US_WF_AI_KEY]:
        fails.append("USA AI War Factory mutated")
    if data[CS_KEY] != src[CS_KEY]:
        fails.append("CommandSet.ini mutated")
    if data[CB_KEY] != src[CB_KEY]:
        fails.append("CommandButton.ini mutated")
    if data[SE_CC_KEY] != src[SE_CC_KEY]:
        fails.append("Sweden Command Center mutated")

    se = data[SE_WF_KEY].decode("latin1")
    src_se = src[SE_WF_KEY].decode("latin1")
    se_obj = first_object(se, "SwedenWarFactory")
    src_obj = first_object(src_se, "SwedenWarFactory")
    if field(se_obj, "CommandSet") != NEW_SET:
        fails.append(f"Sweden CommandSet {field(se_obj, 'CommandSet')}")
    if field(src_obj, "CommandSet") != OLD_SET:
        fails.append("baseline Sweden CommandSet unexpected")
    if field(se_obj, "Side") != "Sweden":
        fails.append("Sweden Side lost")
    if "SE__SEFlag_HsWF" not in se_obj:
        fails.append("Sweden flag lost")
    if "US__USFlag_HsWF" in se_obj:
        fails.append("USA flag leaked onto Sweden WF")
    if field(se_obj, "BuildCost") != field(src_obj, "BuildCost"):
        fails.append("Sweden BuildCost changed")
    if "MaxHealth       = 2000.0" not in se_obj:
        fails.append("Sweden health changed")
    if "Object = SwedenSupplyCenter" not in se_obj:
        fails.append("Sweden WF prereq changed")
    if "Model           = US_WarFactory" not in se_obj:
        fails.append("Sweden factory model lost")
    # identity besides CommandSet line
    if src_se.replace(
        "CommandSet       = SwedenWarfactoryCommandSet",
        "CommandSet       = AmericaWarFactoryCommandSet_T3",
        1,
    ) != se:
        fails.append("Sweden WF file changed beyond CommandSet retarget")

    cs = data[CS_KEY].decode("latin1")
    usa_t3 = slot_map(command_block(cs, "CommandSet", NEW_SET))
    se_slots_via_ref = usa_t3  # object now uses that set
    usa_player_default = slot_map(command_block(cs, "CommandSet", USA_PLAYER_SET))
    if not usa_t3:
        fails.append("AmericaWarFactoryCommandSet_T3 missing")
    # roster identity: Sweden production == USA T3 (full unlocked player roster)
    if se_slots_via_ref != usa_t3:
        fails.append("Sweden roster != USA T3")
    expected = {
        1: "Command_ConstructAmericaTankCrusader",
        2: "Command_ConstructAmericaVehicleM1128",
        3: "Command_ConstructAmericaVehicleM1296",
        4: "Command_ConstructAmericaVehicleSentryDrone",
        5: "Command_ConstructAmericaVehicleTomahawk",
        6: "Command_ConstructAmericaTankM109A7",
        7: "Command_ConstructAmericaVehicleAvenger",
        8: "Command_ConstructAmericaVehicleMicrowave",
        9: "Command_ConstructAmericaVehicleAN_TPY2",
        10: "Command_ConstructAmericaVehicleTHAAD",
        11: "Command_ConstructAmericaVehicleM142",
        12: "Command_ConstructAmericaVehicleM1075I",
        13: "Command_ConstructAmericaVehicleM1075T",
        14: "Command_Sell",
        15: "Command_ConstructAmericaVehicleM1075I_AI",
    }
    if usa_t3 != expected:
        fails.append(f"USA T3 roster drifted {usa_t3}")
    old_se = slot_map(command_block(cs, "CommandSet", OLD_SET))
    for btn in SWEDEN_REMOVED:
        if btn not in old_se.values():
            fails.append(f"baseline missing removed button {btn}")
        if btn in usa_t3.values():
            fails.append(f"Sweden unit leaked into USA T3 {btn}")
    if usa_player_default.get(1) != "Command_ConstructAmericaTankCrusader":
        fails.append("USA default T CommandSet drifted")

    us_obj = first_object(data[US_WF_KEY].decode("latin1"), "AmericaWarFactory_T")
    if field(us_obj, "CommandSet") != USA_PLAYER_SET:
        fails.append("USA player WF CommandSet changed")
    if "US__USFlag_HsWF" not in us_obj:
        fails.append("USA flag missing")

    for key in CONTROL_WF_OBJECTS:
        if data.get(key) != src.get(key):
            fails.append(f"unrelated WF mutated {key}")

    # last-wins: CS/CB unchanged so dups identical to PR #584
    cs_src = src[CS_KEY].decode("latin1")
    if command_block(cs, "CommandSet", NEW_SET) != command_block(cs_src, "CommandSet", NEW_SET):
        fails.append("USA T3 CommandSet mutated")
    if command_block(cs, "CommandSet", "SwedenDozerCommandSet") != command_block(
        cs_src, "CommandSet", "SwedenDozerCommandSet"
    ):
        fails.append("Sweden Dozer CommandSet mutated")
    dozer = slot_map(command_block(cs, "CommandSet", "SwedenDozerCommandSet"))
    if dozer.get(11) != "Command_ConstructSwedenWarFactory":
        fails.append("Sweden Dozer no longer constructs SwedenWarFactory")

    # PR #584 CC
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
    loc = data[LOCO_KEY].decode("latin1")
    if not command_block(loc, "Locomotor", "R11SRBMLocomotor"):
        fails.append("R11SRBMLocomotor missing")
    if re.search(r"^Locomotor Iraq_Al(HusseinII|SamoudII|Abbas|Basrah|Nasir|Mansour)_Locomotor", loc, re.M):
        fails.append("later dedicated missile locos leaked")
    for obj in (
        "Iraq_AlHusseinII",
        "Iraq_AlSamoudII",
        "Iraq_AlAbbas",
        "Iraq_AlBasrah",
        "Iraq_AlNasir",
        "Iraq_AlMansour",
    ):
        key = rf"Data\INI\Object\Specter\Iraq Army\Wheeled\{obj}.ini"
        if data.get(key) != src.get(key):
            fails.append(f"{obj} mutated vs PR #584")
        if "CommandSet    = Scud_B_CommandSet" not in data.get(key, b"").decode("latin1"):
            fails.append(f"{obj} lost Scud_B_CommandSet")
    fac = command_block(cs, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet")
    src_fac = command_block(src[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet")
    if fac != src_fac:
        fails.append("Iraq missile factory CommandSet mutated")
    return fails


def dump_extract(extracted: dict[str, bytes]) -> None:
    stage = OUT / "LAST_WINS_EXTRACT/DATA"
    keys = [SE_WF_KEY, US_WF_KEY, CS_KEY, R11_KEY, FACTORY_KEY, UNIT_A_KEY]
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
    data[SE_WF_KEY] = patch_sweden_wf(data[SE_WF_KEY])

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
        "# SPECTER Sweden War Factory: use USA production roster",
        "",
        "Baseline DATA: PR #584 (CC start=construct + PR #583 missiles).",
        "Baseline ART: PR #574 ART BIG (unchanged, not rebuilt).",
        "PR #585+ NOT imported.",
        "",
        "SWEDEN War Factory Object = SwedenWarFactory",
        "USA War Factory Object    = AmericaWarFactory_T (player)",
        f"OLD Sweden CommandSet     = {OLD_SET}",
        f"NEW Sweden CommandSet     = {NEW_SET} (full unlocked USA player roster)",
        "Sweden building/flag/model/stats unchanged. USA WF unchanged.",
        "",
        "Removed from Sweden WF:",
        *[f"  - {b}" for b in SWEDEN_REMOVED],
        "USA T3 units now used (existing CommandButtons):",
        "  Crusader, M1128, M1296, SentryDrone, Tomahawk, M109A7, Avenger,",
        "  Microwave, AN_TPY2, THAAD, M142, M1075I, M1075T, Sell, M1075I_AI",
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
        "- Sweden WF production CommandSet == AmericaWarFactoryCommandSet_T3",
        "- Sweden object still SwedenWarFactory, Side=Sweden, flag SE__SEFlag_HsWF",
        "- USA Warfactory.ini / CommandSet.ini / CommandButton.ini unchanged",
        "- other countries' War Factories unchanged",
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
        "SWEDEN_OBJECT=SwedenWarFactory\n"
        "USA_OBJECT=AmericaWarFactory_T\n"
        f"OLD_COMMANDSET={OLD_SET}\n"
        f"NEW_COMMANDSET={NEW_SET}\n"
        "CHANGED_FILES=Data\\INI\\Object\\Specter\\Swedish Armed Forces\\Buildings\\Warfactory.ini\n"
        "BASELINE_DATA=PR #584\n"
        "BASELINE_ART=PR #574\n"
        "PR585PLUS=NOT IMPORTED\n"
        "CC_CONSTRUCT=UNCHANGED\n"
        "MISSILES=UNCHANGED\n"
        "MOTHER_GAMEPLAY=UNCHANGED\n"
        "USA_WARFACTORY=UNCHANGED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Sweden War Factory: USA production roster\n"
        "\n"
        "Sweden's War Factory building remains Swedish (object, flag,\n"
        "model, health, supply-center prereq). Its production bar now\n"
        "uses AmericaWarFactoryCommandSet_T3 (full USA player roster).\n"
        "USA War Factory is unchanged.\n"
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
    zip_path = ROOT / "patch/Release/SPECTER_SWEDEN_WF_USA_ROSTER.zip"
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
