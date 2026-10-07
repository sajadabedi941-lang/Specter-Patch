#!/usr/bin/env python3
"""Match starting vs constructed Command Center for 7 SPECTER countries.

Starts from the packed PR #583 DATA BIG (SHA 6d1ff28...).
Does NOT import PR #575+ content. Does NOT rebuild ART (PR #574).
Does NOT modify missiles, MOTHER/9P117, USA/Iraq/Russia/China/Japan/
Vietnam/South Korea Command Centers, or unrelated buildings.

Root cause (engine-loaded last-wins on PR #583):
  PlayerTemplate.ini StartingBuilding = <Country>_CommandCenter
  Dozer/Worker CommandSet.ini slot 2  = Command_Construct<Country>_MilitaryHQ

Those are different objects (health/scale/CommandSet/BuildTime). The
intended country-specific Command Center is the StartingBuilding object.
Iraq already constructs Iraq_CommandCenter from the Worker. This packer
points the 7 countries' Dozer/Worker construct slot at *_CommandCenter.

Pakistan is missing Command_ConstructPakistan_CommandCenter from the
engine-loaded CommandButton.ini (it exists only in an unloaded sidecar).
That button is added here, cloned from the sidecar / sibling-country
pattern. ART is unchanged: country flag W3Ds already exist on the
CommandCenter objects and in the PR #574 ART BIG.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_BCDHIJ_SPAWN_FIX/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_DATA_BCDHIJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_CC_MATCH_START_BUILD"

BASE_DATA_SHA = "6d1ff28fae8fdca41eef06b7ab3b5c4f57fec6898164cb27beef7460e6138514"
BASE_DATA_SIZE = 366460824
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

TARGETS = [
    "India",
    "Pakistan",
    "SaudiArabia",
    "UAE",
    "Libya",
    "Syria",
    "SouthAfrica",
]
DOZER_SETS = {name: f"{name}DozerCommandSet" for name in TARGETS}
WORKER_SETS = {
    "India": "India_WorkerCommandSet",
    "SaudiArabia": "SaudiArabia_WorkerCommandSet",
    "UAE": "UAE_WorkerCommandSet",
    "Libya": "Libya_WorkerCommandSet",
    "Syria": "Syria_WorkerCommandSet",
    "SouthAfrica": "SouthAfrica_WorkerCommandSet",
}
FLAG_MODEL = {
    "India": "IN__INFlag_HsCU",
    "Pakistan": "PK__PKFlag_HsCU",
    "SaudiArabia": "SA__SAFlag_HsCU",
    "UAE": "AE__AEFlag_HsCU",
    "Libya": "LY__LYFlag_HsCU",
    "Syria": "SY__SYFlag_HsCU",
    "SouthAfrica": "ZA__ZAFlag_HsCU",
}
UNRELATED_START = {
    "FactionAmerica": "AmericaCommandCenter",
    "FactionIraq": "Iraq_CommandCenter",
    "FactionRussia": "RussiaCommandCenter",
    "FactionChina": "ChinaCommandCenter",
    "FactionJapan": "Japan_CommandCenter",
    "FactionVietnam": "Vietnam_CommandCenter",
    "FactionSouthKorea": "SouthKorea_CommandCenter",
}
CONTROL_CONSTRUCT = {
    "Iraq_WorkerCommandSet": "Command_ConstructIraq_CommandCenter",
    "Egypt_WorkerCommandSet": "Command_ConstructEgypt_MilitaryHQ",
    "AmericaDozerCommandSet": "Command_ConstructAmericaCommandCenter",
}
MISSILE_UNITS = [
    "Iraq_AlFahd500",
    "Iraq_AlHusseinII",
    "Iraq_AlSamoudII",
    "Iraq_AlAbbas",
    "Iraq_AlBasrah",
    "Iraq_AlNasir",
    "Iraq_AlMansour",
]
PK_CC_BUTTON = (
    "CommandButton Command_ConstructPakistan_CommandCenter\r\n"
    "  Command       = DOZER_CONSTRUCT\r\n"
    "  Object        = Pakistan_CommandCenter\r\n"
    "  TextLabel     = CONTROLBAR:ConstructPakistan_CommandCenter\r\n"
    "  ButtonImage   = us_commandcenter\r\n"
    "  ButtonBorderType = BUILD\r\n"
    "  DescriptLabel = CONTROLBAR:ToolTipConstructPakistan_CommandCenter\r\n"
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


def slot_map(block: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def last_object(data: dict[str, bytes], obj: str) -> tuple[str | None, str | None]:
    last: tuple[str | None, str | None] = (None, None)
    pat = re.compile(rf"(?ms)^Object {re.escape(obj)}\r?\n.*?^End")
    for k, v in data.items():
        if not k.lower().endswith(".ini"):
            continue
        hits = list(pat.finditer(v.decode("latin1")))
        if hits:
            last = (k, hits[-1].group(0))
    return last


def field(block: str | None, key: str) -> str:
    if not block:
        return ""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block, re.M)
    return m.group(1).strip() if m else ""


def models(block: str | None) -> list[str]:
    if not block:
        return []
    return re.findall(r"^\s*Model\s*=\s*(\S+)", block, re.M)


def patch_construct_slot(cs: str, set_name: str, country: str) -> str:
    old = command_block(cs, "CommandSet", set_name)
    if not old:
        raise SystemExit(f"missing CommandSet {set_name}")
    src_btn = f"Command_Construct{country}_MilitaryHQ"
    dst_btn = f"Command_Construct{country}_CommandCenter"
    new, n = re.subn(
        rf"^(\s*2\s*=\s*){re.escape(src_btn)}\s*$",
        rf"\1{dst_btn}",
        old,
        count=1,
        flags=re.M,
    )
    if n != 1:
        raise SystemExit(f"{set_name}: slot 2 replace failed ({n}); have {slot_map(old)}")
    if src_btn in new:
        raise SystemExit(f"{set_name}: MilitaryHQ construct residue")
    if slot_map(new).get(2) != dst_btn:
        raise SystemExit(f"{set_name}: slot 2={slot_map(new).get(2)}")
    idx = cs.rfind(old)
    if idx < 0:
        raise SystemExit(f"{set_name}: block not found for splice")
    return cs[:idx] + new + cs[idx + len(old) :]


def add_pakistan_cc_button(cb: str) -> str:
    if command_block(cb, "CommandButton", "Command_ConstructPakistan_CommandCenter"):
        return cb
    hq = command_block(cb, "CommandButton", "Command_ConstructPakistan_MilitaryHQ")
    if not hq:
        raise SystemExit("Command_ConstructPakistan_MilitaryHQ missing; cannot anchor new button")
    idx = cb.rfind(hq)
    insert_at = idx + len(hq)
    nl = "\r\n" if hq.endswith("\r\n") or "\r\n" in hq else "\n"
    return cb[:insert_at] + nl + nl + PK_CC_BUTTON.replace("\r\n", nl) + cb[insert_at:]


def patch_commandset(cs: str) -> str:
    for country, set_name in DOZER_SETS.items():
        cs = patch_construct_slot(cs, set_name, country)
    for country, set_name in WORKER_SETS.items():
        cs = patch_construct_slot(cs, set_name, country)
    return cs


def object_key(country: str, kind: str) -> str:
    mapping = {
        ("India", "CommandCenter"): r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_CommandCenter.ini",
        ("India", "MilitaryHQ"): r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_MilitaryHQ.ini",
        ("Pakistan", "CommandCenter"): r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_CommandCenter.ini",
        ("Pakistan", "MilitaryHQ"): r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_MilitaryHQ.ini",
        ("SaudiArabia", "CommandCenter"): r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_CommandCenter.ini",
        ("SaudiArabia", "MilitaryHQ"): r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_MilitaryHQ.ini",
        ("UAE", "CommandCenter"): r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_CommandCenter.ini",
        ("UAE", "MilitaryHQ"): r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_MilitaryHQ.ini",
        ("Libya", "CommandCenter"): r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_CommandCenter.ini",
        ("Libya", "MilitaryHQ"): r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_MilitaryHQ.ini",
        ("Syria", "CommandCenter"): r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_CommandCenter.ini",
        ("Syria", "MilitaryHQ"): r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_MilitaryHQ.ini",
        ("SouthAfrica", "CommandCenter"): r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_CommandCenter.ini",
        ("SouthAfrica", "MilitaryHQ"): r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_MilitaryHQ.ini",
    }
    return mapping[(country, kind)]


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    changed = sorted(k for k in set(src) | set(data) if src.get(k) != data.get(k))
    allowed = {CS_KEY, CB_KEY}
    unexpected = [k for k in changed if k not in allowed]
    if unexpected:
        fails.append(f"unexpected mutated files: {unexpected[:8]}")
    if set(data) != set(src):
        fails.append("packed file set changed")

    pt = data[PT_KEY].decode("latin1")
    cs = data[CS_KEY].decode("latin1")
    cb = data[CB_KEY].decode("latin1")
    src_cs = src[CS_KEY].decode("latin1")
    src_cb = src[CB_KEY].decode("latin1")

    for name in TARGETS:
        start = command_block(pt, "PlayerTemplate", f"Faction{name}")
        if field(start, "StartingBuilding") != f"{name}_CommandCenter":
            fails.append(f"{name} StartingBuilding={field(start, 'StartingBuilding')}")
        dozer = command_block(cs, "CommandSet", DOZER_SETS[name])
        if slot_map(dozer or "").get(2) != f"Command_Construct{name}_CommandCenter":
            fails.append(f"{name} Dozer slot2={slot_map(dozer or '').get(2)}")
        if name in WORKER_SETS:
            worker = command_block(cs, "CommandSet", WORKER_SETS[name])
            if slot_map(worker or "").get(2) != f"Command_Construct{name}_CommandCenter":
                fails.append(f"{name} Worker slot2={slot_map(worker or '').get(2)}")
        btn = command_block(cb, "CommandButton", f"Command_Construct{name}_CommandCenter")
        if field(btn, "Object") != f"{name}_CommandCenter":
            fails.append(f"{name} construct button Object={field(btn, 'Object')}")
        if field(btn, "Command") != "DOZER_CONSTRUCT":
            fails.append(f"{name} construct Command={field(btn, 'Command')}")
        key, body = last_object(data, f"{name}_CommandCenter")
        if not body:
            fails.append(f"missing object {name}_CommandCenter")
            continue
        if field(body, "CommandSet") != f"{name}_CommandCenterCommandSet":
            fails.append(f"{name} CC CommandSet={field(body, 'CommandSet')}")
        if FLAG_MODEL[name] not in models(body):
            fails.append(f"{name} CC missing flag {FLAG_MODEL[name]}")
        if "US_Command" not in models(body):
            fails.append(f"{name} CC missing US_Command")
        defs = 0
        for k, v in data.items():
            if k.lower().endswith(".ini"):
                defs += len(re.findall(rf"^Object {re.escape(name)}_CommandCenter\s*$".encode("ascii"), v, re.M))
        if defs != 1:
            fails.append(f"{name}_CommandCenter definition count {defs}")
        if data.get(object_key(name, "CommandCenter")) != src.get(object_key(name, "CommandCenter")):
            fails.append(f"{name}_CommandCenter.ini mutated")
        if data.get(object_key(name, "MilitaryHQ")) != src.get(object_key(name, "MilitaryHQ")):
            fails.append(f"{name}_MilitaryHQ.ini mutated")

    if command_block(src_cs, "CommandSet", "Pakistan_WorkerCommandSet"):
        fails.append("baseline unexpectedly gained Pakistan_WorkerCommandSet")

    for faction, building in UNRELATED_START.items():
        blk = command_block(pt, "PlayerTemplate", faction)
        if field(blk, "StartingBuilding") != building:
            fails.append(f"{faction} StartingBuilding changed")
        src_blk = command_block(src[PT_KEY].decode("latin1"), "PlayerTemplate", faction)
        if blk != src_blk:
            fails.append(f"{faction} PlayerTemplate mutated")

    for set_name, btn in CONTROL_CONSTRUCT.items():
        blk = command_block(cs, "CommandSet", set_name)
        src_blk = command_block(src_cs, "CommandSet", set_name)
        if blk != src_blk:
            fails.append(f"{set_name} mutated")
        if btn not in (blk or ""):
            fails.append(f"{set_name} lost {btn}")

    for country in ("Japan", "Vietnam", "SouthKorea", "Iraq"):
        obj = f"{country}_CommandCenter"
        if last_object(data, obj)[1] != last_object(src, obj)[1]:
            fails.append(f"{obj} object mutated")

    egypt_dozer = command_block(cs, "CommandSet", "Egypt_WorkerCommandSet")
    if slot_map(egypt_dozer or "").get(2) != "Command_ConstructEgypt_MilitaryHQ":
        fails.append("Egypt Worker construct slot changed")

    r11 = data[R11_KEY]
    if r11 != src[R11_KEY]:
        fails.append("9P117.ini mutated")
    if b"BuildCost       = 1200" not in r11 or b"Weapon = PRIMARY   SRBM_ALHIJARAH_HE" not in r11:
        fails.append("MOTHER Iraq_R11ScudB cost/weapon changed")
    if data[FACTORY_KEY] != src[FACTORY_KEY]:
        fails.append("missile factory object mutated")
    if data[UNIT_A_KEY] != src[UNIT_A_KEY]:
        fails.append("Al-Fahd500 mutated")
    if data[WEAPON_KEY] != src[WEAPON_KEY]:
        fails.append("Weapon.ini mutated")
    if data[LOCO_KEY] != src[LOCO_KEY]:
        fails.append("Locomotor.ini mutated")
    if data[UPGRADE_KEY] != src[UPGRADE_KEY]:
        fails.append("Upgrade.ini mutated")
    if b"ReplaceObjectUpgrade ModuleTag_Rebuild" in b"".join(data.values()):
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
    for obj in MISSILE_UNITS:
        key = rf"Data\INI\Object\Specter\Iraq Army\Wheeled\{obj}.ini"
        if obj == "Iraq_AlFahd500":
            key = UNIT_A_KEY
        if data.get(key) != src.get(key):
            fails.append(f"{obj} mutated vs PR #583")
        if obj != "Iraq_AlFahd500":
            unit = data.get(key, b"").decode("latin1")
            if "CommandSet    = Scud_B_CommandSet" not in unit:
                fails.append(f"{obj} lost Scud_B_CommandSet")

    fac = command_block(cs, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet")
    src_fac = command_block(src_cs, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet")
    if fac != src_fac:
        fails.append("Iraq missile factory CommandSet mutated")

    zzzz_key = r"Data\INI\CommandSet_ZZZZ_CommandCenterMatchStart.ini"
    if data.get(zzzz_key) != src.get(zzzz_key):
        fails.append("ZZZZ CommandCenterMatchStart mutated")

    cs_changed_sets = []
    names = set(re.findall(r"^CommandSet\s+(\S+)", cs, re.M)) | set(re.findall(r"^CommandSet\s+(\S+)", src_cs, re.M))
    allowed_sets = set(DOZER_SETS.values()) | set(WORKER_SETS.values())
    for set_name in sorted(names):
        a = command_block(cs, "CommandSet", set_name)
        b = command_block(src_cs, "CommandSet", set_name)
        if a != b:
            cs_changed_sets.append(set_name)
            if set_name not in allowed_sets:
                fails.append(f"unrelated CommandSet mutated: {set_name}")
    expected_sets = set(allowed_sets)
    if set(cs_changed_sets) != expected_sets:
        fails.append(f"CommandSet changed {cs_changed_sets} expected {sorted(expected_sets)}")

    src_pk = command_block(src_cb, "CommandButton", "Command_ConstructPakistan_CommandCenter")
    new_pk = command_block(cb, "CommandButton", "Command_ConstructPakistan_CommandCenter")
    if src_pk:
        fails.append("baseline already had engine-loaded Pakistan CC button")
    if not new_pk or field(new_pk, "Object") != "Pakistan_CommandCenter":
        fails.append("Pakistan CC construct button not added")
    for name in TARGETS:
        if name == "Pakistan":
            continue
        a = command_block(cb, "CommandButton", f"Command_Construct{name}_CommandCenter")
        b = command_block(src_cb, "CommandButton", f"Command_Construct{name}_CommandCenter")
        if a != b:
            fails.append(f"{name} CC construct button mutated")
        a = command_block(cb, "CommandButton", f"Command_Construct{name}_MilitaryHQ")
        b = command_block(src_cb, "CommandButton", f"Command_Construct{name}_MilitaryHQ")
        if a != b:
            fails.append(f"{name} HQ construct button mutated")

    return fails


def dump_extract(extracted: dict[str, bytes]) -> None:
    stage = OUT / "LAST_WINS_EXTRACT/DATA"
    keys = [CS_KEY, CB_KEY, PT_KEY, R11_KEY, FACTORY_KEY, UNIT_A_KEY]
    for name in TARGETS:
        keys.append(object_key(name, "CommandCenter"))
    for rel in keys:
        p = stage / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing PR #583 DATA BIG at {SRC_DATA}")
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("PR #583 DATA baseline mismatch")
    if SRC_ART.is_file():
        if SRC_ART.stat().st_size != BASE_ART_SIZE or sha256_path(SRC_ART) != BASE_ART_SHA:
            raise SystemExit("PR #574 ART baseline mismatch")

    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)
    cs = data[CS_KEY].decode("latin1")
    cb = data[CB_KEY].decode("latin1")
    data[CS_KEY] = patch_commandset(cs).encode("latin1")
    data[CB_KEY] = add_pakistan_cc_button(cb).encode("latin1")

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
        "# SPECTER Command Center start=construct match (7 countries)",
        "",
        "Baseline DATA: PR #583 (s-iraq-bcdhij-spawn-fix).",
        "Baseline ART: PR #574 ART BIG (unchanged, not rebuilt).",
        "PR #575+ NOT imported.",
        "MOTHER / Iraq_R11ScudB / 9P117 — NOT MODIFIED",
        "Missile factory / B-J spawn-fix — NOT MODIFIED",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART SHA256 (unchanged): {BASE_ART_SHA}",
        f"- ART size (unchanged): {BASE_ART_SIZE}",
        "",
        "Forensic: engine-loaded StartingBuilding already used *_CommandCenter;",
        "Dozer/Worker slot 2 constructed *_MilitaryHQ (different object).",
        "Fix: point those construct slots at Command_Construct*_CommandCenter.",
        "Pakistan: add missing engine-loaded construct button.",
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
        "- 7 countries: StartingBuilding == constructed object == *_CommandCenter",
        "- same W3D (US_Command) and country flag W3D on that object",
        "- same CommandSet (*_CommandCenterCommandSet) for start and built",
        "- CommandButton construct Object = *_CommandCenter",
        "- Pakistan construct button added to engine-loaded CommandButton.ini",
        "- MilitaryHQ object INIs left in place but no longer selected by Dozer/Worker",
        "- USA / Iraq / Russia / China / Japan / Vietnam / South Korea CC unchanged",
        "- Egypt Worker still constructs Egypt_MilitaryHQ",
        "- PR #583 missile data / Weapon.ini / factory CommandSet unchanged",
        "- MOTHER / 9P117 unchanged",
        "- ZZZZ_CommandCenterMatchStart sidecar unchanged (not engine-loaded)",
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
        "COUNTRIES=India,Pakistan,SaudiArabia,UAE,Libya,Syria,SouthAfrica\n"
        "START_OBJECT=*_CommandCenter\n"
        "BUILT_OBJECT=*_CommandCenter\n"
        "CHANGED_FILES=Data\\INI\\CommandSet.ini, Data\\INI\\CommandButton.ini\n"
        "BASELINE_DATA=PR #583\n"
        "BASELINE_ART=PR #574\n"
        "PR575PLUS=NOT IMPORTED\n"
        "MISSILES=UNCHANGED\n"
        "MOTHER_GAMEPLAY=UNCHANGED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Command Center start=construct match\n"
        "Countries: India, Pakistan, Saudi Arabia, UAE, Libya, Syria, South Africa\n"
        "\n"
        "Place this complete replacement DATA BIG in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "\n"
        "Keep the existing PR #574 ART BIG (do not replace ART):\n"
        "  _SPEC_ART_ONE.big\n"
        f"  SHA256={BASE_ART_SHA}\n"
        "\n"
        "Fix:\n"
        "- Starting Command Center and later-constructed Command Center now use\n"
        "  the same country-specific *_CommandCenter object (model, flag,\n"
        "  CommandSet, health, armor, geometry).\n"
        "- Dozer/Worker construct slot 2 no longer builds *_MilitaryHQ.\n"
        "- Pakistan construct-CommandCenter button added to CommandButton.ini.\n"
        "- PR #583 missile spawn-fix data preserved. ART not rebuilt.\n"
        "\n"
        "Static validation completed; runtime game test not performed.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_CC_MATCH_START_BUILD.zip"
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
