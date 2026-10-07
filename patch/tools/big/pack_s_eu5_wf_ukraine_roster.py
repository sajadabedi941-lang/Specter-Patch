#!/usr/bin/env python3
"""Give Germany/France/Britain/Italy/Turkey Ukraine's War Factory roster.

Starts from packed PR #587 DATA (Sweden WF USA T3 on PR #584):
  SHA256 9b139e75ebb02c442541a4c5e97e89d5396e68ffb41f323da629a22e5689d036

Does NOT rebuild ART (PR #574). Does NOT modify Ukraine, USA, Sweden,
or any other country's War Factory objects.

Forensic (engine-loaded last-wins):
  UkraineWarFactory -> UkraineWarfactoryCommandSet (1 def, no CommandSetUpgrade)
  Germany/France/Britain/Italy/Turkey each have their own *WarfactoryCommandSet
  (1 def each, no CommandSetUpgrade). Country-specific vehicle buttons.

Fix: replace those five CommandSet definitions in CommandSet.ini with the
exact Ukraine slot list (same CommandButton names/order). Building objects,
flags, models, stats stay country-specific. Ukraine CommandSet unchanged.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_SWEDEN_WF_USA_ROSTER/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_DATA_BCDHIJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_EU5_WF_UKRAINE_ROSTER"

BASE_DATA_SHA = "9b139e75ebb02c442541a4c5e97e89d5396e68ffb41f323da629a22e5689d036"
BASE_DATA_SIZE = 366461188
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
UA_WF_KEY = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\Warfactory.ini"
NATO_WF_KEY = r"Data\INI\Object\Specter\NATO\Buildings\Warfactory.ini"

DONOR_SET = "UkraineWarfactoryCommandSet"
TARGET_SETS = [
    "GermanyWarfactoryCommandSet",
    "FranceWarfactoryCommandSet",
    "BritainWarfactoryCommandSet",
    "ItalyWarfactoryCommandSet",
    "TurkeyWarfactoryCommandSet",
]
TARGET_OBJECTS = {
    "Germany": (r"Data\INI\Object\Specter\German Armed Forces\Buildings\Warfactory.ini", "GermanyWarFactory", "GermanyWarfactoryCommandSet", "DE__DEFlag_HsWF"),
    "France": (r"Data\INI\Object\Specter\French Armed Forces\Buildings\Warfactory.ini", "FranceWarFactory", "FranceWarfactoryCommandSet", "FR__FRFlag_HsWF"),
    "Britain": (r"Data\INI\Object\Specter\British Armed Forces\Buildings\Warfactory.ini", "BritainWarFactory", "BritainWarfactoryCommandSet", "UK__UKFlag_HsWF"),
    "Italy": (r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\Warfactory.ini", "ItalyWarFactory", "ItalyWarfactoryCommandSet", "IT__ITFlag_HsWF"),
    "Turkey": (r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\Warfactory.ini", "TurkeyWarFactory", "TurkeyWarfactoryCommandSet", "TR__TRFlag_HsWF"),
}

UKRAINE_ROSTER = {
    1: "Command_ConstructUkraineTankLeopard2A7Plus",
    2: "Command_ConstructUkraineTankPuma",
    3: "Command_ConstructUkraineVehicleCortaleMK3",
    4: "Command_ConstructUkraineVehicleVBCI",
    5: "Command_ConstructUkraineVehicleM142",
    6: "Command_ConstructUkraineVehicleCaesar",
    7: "Command_ConstructUkraineVehicleCentauroB2",
    8: "Command_ConstructUkraineVehicleIRIST",
    9: "Command_ConstructUkraineVehicleTRML4D",
    10: "Command_ConstructUkraineVehicleM142ATACMS",
    14: "Command_Sell",
}


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


def defs(text: str, kind: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for m in re.finditer(rf"^{kind} (\S+)", text, re.M):
        out[m.group(1)] = out.get(m.group(1), 0) + 1
    return out


def retarget_commandsets(cs: str) -> str:
    donor = command_block(cs, "CommandSet", DONOR_SET)
    if not donor:
        raise SystemExit("missing Ukraine donor CommandSet")
    donor_slots = slot_map(donor)
    if donor_slots != UKRAINE_ROSTER:
        raise SystemExit(f"Ukraine roster unexpected {donor_slots}")
    for set_name in TARGET_SETS:
        old = command_block(cs, "CommandSet", set_name)
        if not old:
            raise SystemExit(f"missing {set_name}")
        new = re.sub(rf"^CommandSet {re.escape(DONOR_SET)}", f"CommandSet {set_name}", donor, count=1)
        if slot_map(new) != UKRAINE_ROSTER:
            raise SystemExit(f"{set_name} copy failed {slot_map(new)}")
        idx = cs.rfind(old)
        if idx < 0:
            raise SystemExit(f"rfind failed {set_name}")
        cs = cs[:idx] + new + cs[idx + len(old) :]
    return cs


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    changed = sorted(k for k in set(src) | set(data) if src.get(k) != data.get(k))
    if changed != [CS_KEY]:
        fails.append(f"unexpected changed files: {changed}")
    if set(data) != set(src):
        fails.append("packed file set changed")

    if data[CB_KEY] != src[CB_KEY]:
        fails.append("CommandButton.ini mutated")
    if data[UA_WF_KEY] != src[UA_WF_KEY]:
        fails.append("Ukraine War Factory object mutated")
    if data[US_WF_KEY] != src[US_WF_KEY] or data[US_WF_AI_KEY] != src[US_WF_AI_KEY]:
        fails.append("USA War Factory mutated")
    if data[SE_WF_KEY] != src[SE_WF_KEY]:
        fails.append("Sweden War Factory mutated")
    if data[NATO_WF_KEY] != src[NATO_WF_KEY]:
        fails.append("NATO War Factory mutated")

    cs = data[CS_KEY].decode("latin1")
    src_cs = src[CS_KEY].decode("latin1")
    ukr = slot_map(command_block(cs, "CommandSet", DONOR_SET))
    src_ukr = slot_map(command_block(src_cs, "CommandSet", DONOR_SET))
    if command_block(cs, "CommandSet", DONOR_SET) != command_block(src_cs, "CommandSet", DONOR_SET):
        fails.append("Ukraine CommandSet mutated")
    if ukr != UKRAINE_ROSTER or src_ukr != UKRAINE_ROSTER:
        fails.append("Ukraine roster mismatch")

    cs_defs = defs(cs, "CommandSet")
    src_defs = defs(src_cs, "CommandSet")
    dups = {n: c for n, c in cs_defs.items() if c > 1}
    if dups:
        fails.append(f"CommandSet last-wins dups {list(dups)[:8]}")
    for name in TARGET_SETS + [DONOR_SET, "NatoWarfactoryCommandSet", "AmericaWarFactoryCommandSet_T", "AmericaWarFactoryCommandSet_T3"]:
        if cs_defs.get(name, 0) != 1:
            fails.append(f"{name} def count {cs_defs.get(name)}")
        if src_defs.get(name, 0) != 1:
            fails.append(f"baseline {name} def count {src_defs.get(name)}")

    old_country_btns = []
    for set_name in TARGET_SETS:
        sl = slot_map(command_block(cs, "CommandSet", set_name))
        if sl != ukr:
            fails.append(f"{set_name} != Ukraine {sl}")
        src_sl = slot_map(command_block(src_cs, "CommandSet", set_name))
        old_country_btns.extend(v for v in src_sl.values() if v != "Command_Sell")
        leftover = [v for v in sl.values() if v != "Command_Sell" and not v.startswith("Command_ConstructUkraine")]
        if leftover:
            fails.append(f"{set_name} leftover {leftover}")
        if len(sl) != len(set(sl.values())):
            fails.append(f"{set_name} duplicate buttons")

    if command_block(cs, "CommandSet", "NatoWarfactoryCommandSet") != command_block(
        src_cs, "CommandSet", "NatoWarfactoryCommandSet"
    ):
        fails.append("NatoWarfactoryCommandSet mutated")
    if command_block(cs, "CommandSet", "AmericaWarFactoryCommandSet_T3") != command_block(
        src_cs, "CommandSet", "AmericaWarFactoryCommandSet_T3"
    ):
        fails.append("USA T3 CommandSet mutated")
    if command_block(cs, "CommandSet", "SwedenWarfactoryCommandSet") != command_block(
        src_cs, "CommandSet", "SwedenWarfactoryCommandSet"
    ):
        fails.append("unused SwedenWarfactoryCommandSet mutated")

    for country, (key, obj, set_name, flag) in TARGET_OBJECTS.items():
        if data[key] != src[key]:
            fails.append(f"{country} WF object mutated")
        obj_block = first_object(data[key].decode("latin1"), obj)
        if field(obj_block, "CommandSet") != set_name:
            fails.append(f"{country} object CommandSet field changed")
        if field(obj_block, "Side") != country:
            fails.append(f"{country} Side lost")
        if flag not in obj_block:
            fails.append(f"{country} flag lost")
        if "UA__UAFlag_HsWF" in obj_block:
            fails.append(f"{country} gained Ukraine flag")

    ua_obj = first_object(data[UA_WF_KEY].decode("latin1"), "UkraineWarFactory")
    if field(ua_obj, "CommandSet") != DONOR_SET or "UA__UAFlag_HsWF" not in ua_obj:
        fails.append("Ukraine object identity")
    se_obj = first_object(data[SE_WF_KEY].decode("latin1"), "SwedenWarFactory")
    if field(se_obj, "CommandSet") != "AmericaWarFactoryCommandSet_T3":
        fails.append("Sweden roster retarget lost")
    us_obj = first_object(data[US_WF_KEY].decode("latin1"), "AmericaWarFactory_T")
    if field(us_obj, "CommandSet") != "AmericaWarFactoryCommandSet_T":
        fails.append("USA player WF CommandSet changed")

    # other WF object files
    for k, blob in data.items():
        if "warfactory" not in k.lower():
            continue
        if blob != src.get(k):
            fails.append(f"WF object file mutated {k}")

    cb = data[CB_KEY].decode("latin1")
    for btn in UKRAINE_ROSTER.values():
        if btn == "Command_Sell":
            continue
        if not command_block(cb, "CommandButton", btn):
            fails.append(f"missing Ukraine button {btn}")

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
    return fails


def dump_extract(extracted: dict[str, bytes]) -> None:
    stage = OUT / "LAST_WINS_EXTRACT/DATA"
    keys = [CS_KEY, UA_WF_KEY, US_WF_KEY, SE_WF_KEY, R11_KEY]
    for country, (key, *_rest) in TARGET_OBJECTS.items():
        keys.append(key)
    for rel in keys:
        p = stage / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing baseline DATA BIG at {SRC_DATA}")
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("PR #587 DATA baseline mismatch")
    if SRC_ART.is_file():
        if SRC_ART.stat().st_size != BASE_ART_SIZE or sha256_path(SRC_ART) != BASE_ART_SHA:
            raise SystemExit("PR #574 ART baseline mismatch")

    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)
    data[CS_KEY] = retarget_commandsets(data[CS_KEY].decode("latin1")).encode("latin1")

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

    obj_count = 0
    cs = extracted[CS_KEY].decode("latin1")
    for blob in extracted.values():
        if not blob:
            continue
        obj_count += len(re.findall(rb"^Object ", blob, re.M))

    data_sha = sha256_path(out_data)
    report = [
        "# SPECTER EU5 War Factory: Ukraine production roster",
        "",
        "Baseline DATA: PR #587 Sweden WF USA roster on PR #584 (CC + PR #583 missiles).",
        "Baseline ART: PR #574 ART BIG (unchanged, not rebuilt).",
        "",
        f"DONOR object     = UkraineWarFactory",
        f"DONOR CommandSet = {DONOR_SET}",
        "DONOR roster:",
        *[f"  {k} = {v}" for k, v in sorted(UKRAINE_ROSTER.items())],
        "",
        "Targets: Germany, France, Britain, Italy, Turkey",
        "Each country's *WarfactoryCommandSet now matches Ukraine exactly.",
        "Building objects/flags/models/stats unchanged. Ukraine/USA/Sweden unchanged.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- Object defs: {obj_count}",
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
        "- five target CommandSets == UkraineWarfactoryCommandSet slots",
        "- Ukraine CommandSet and War Factory object unchanged",
        "- USA and Sweden War Factories unchanged",
        "- building flags/models/CommandSet field names unchanged",
        "- CommandButton.ini unchanged (reuse Ukraine buttons)",
        "- CommandSet.ini last-wins dups: 0 for target sets",
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
        f"OBJECT_DEFS={obj_count}\n"
        "ART_FILE=PR574 _SPEC_ART_ONE.big (not rebuilt)\n"
        f"ART_SIZE={BASE_ART_SIZE}\n"
        f"ART_SHA256={BASE_ART_SHA}\n"
        "DONOR_OBJECT=UkraineWarFactory\n"
        f"DONOR_COMMANDSET={DONOR_SET}\n"
        "TARGETS=Germany,France,Britain,Italy,Turkey\n"
        "CHANGED_FILES=Data\\INI\\CommandSet.ini\n"
        "BASELINE_DATA=PR #587 on PR #584\n"
        "BASELINE_ART=PR #574\n"
        "UKRAINE=UNCHANGED\n"
        "USA_WARFACTORY=UNCHANGED\n"
        "SWEDEN_WARFACTORY=UNCHANGED\n"
        "CC_CONSTRUCT=UNCHANGED\n"
        "MISSILES=UNCHANGED\n"
        "MOTHER_GAMEPLAY=UNCHANGED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Germany/France/Britain/Italy/Turkey War Factory = Ukraine roster\n"
        "\n"
        "Those five countries' War Factory buildings remain their own\n"
        "(object, flag, model, health). Production bars now use the same\n"
        "CommandButtons/order as UkraineWarfactoryCommandSet.\n"
        "Ukraine, USA, and Sweden War Factories are unchanged.\n"
        "\n"
        "Place this complete replacement DATA BIG in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "\n"
        "Keep the existing PR #574 ART BIG (do not replace ART unless\n"
        "this release also includes it unchanged):\n"
        "  _SPEC_ART_ONE.big\n"
        f"  SHA256={BASE_ART_SHA}\n"
        "\n"
        "Static validation completed; runtime game test not performed.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_EU5_WF_UKRAINE_ROSTER.zip"
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
