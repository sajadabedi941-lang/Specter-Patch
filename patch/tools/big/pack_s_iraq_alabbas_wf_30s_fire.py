#!/usr/bin/env python3
"""Iraq Al-Abbas: 30s production BuildTime + immediate fire activation.

Starts from packed PR #589 _SPEC_DATA_ONE.big
  SHA256 92b4ea699116f4fa12e81c923019370f84d25f58404d0438debe997a08912c27

Does NOT rebuild ART (PR #574). Does NOT start the aircraft-roster task.
Does NOT add Al-Abbas to Iraq War Factory (packed last-wins production is
the missile factory, not Iraq_WarFactoryCommandSet_*).

Forensic (packed PR #589 last-wins):
  CommandButton CB_MISSILE_D
    Command = UNIT_BUILD
    Object  = Iraq_AlAbbas
  CommandSet Iraq_AlFahdMissileFactoryCommandSet slot 4 = CB_MISSILE_D
  Object Iraq_AlAbbas
    BuildTime   = 35.0   -> 30.0
    CommandSet  = Scud_B_CommandSet
    WeaponSet   PRIMARY Weapon_Iraq_AlAbbas  (Conditions = None)
    Prerequisites NONE
  Weapon Weapon_Iraq_AlAbbas
    AutoReloadsClip = No   -> removed (default Yes, same as known-good Missile A)
    ClipReloadTime / damage / range / projectile unchanged

Iraq War Factory CommandSets do not produce Al-Abbas. Unused
Iraq_AlAbbasCommandSet (SPECIAL_POWER + NEED_SPECIAL_POWER_SCIENCE) is
attached to building Iraq_Abbas, not to this missile object. Left unchanged.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_EU5_WF_UNLOCK_START/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_DATA_BCDHIJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_WF_30S_FIRE"

BASE_DATA_SHA = "92b4ea699116f4fa12e81c923019370f84d25f58404d0438debe997a08912c27"
BASE_DATA_SIZE = 366514449
BASE_ART_SHA = "e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4"
BASE_ART_SIZE = 1292294758

CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
PT_KEY = r"Data\INI\PlayerTemplate.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
UPGRADE_KEY = r"Data\INI\Upgrade.ini"
LOCO_KEY = r"Data\INI\Locomotor.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
UNIT_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
UNIT_D_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini"
PROJ_D_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlAbbas_Projectile.ini"
UNLOCK_KEY = r"Data\INI\Object\Specter\EU5Unlock\Specter_EU5WFUnlock.ini"
IRAQ_WF_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory.ini"

SIBLINGS = [
    ("Iraq_AlFahd500", r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini", "30.0"),
    ("Iraq_AlHusseinII", r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHusseinII.ini", "25.0"),
    ("Iraq_AlSamoudII", r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlSamoudII.ini", "22.0"),
    ("Iraq_AlBasrah", r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlBasrah.ini", "60.0"),
    ("Iraq_AlNasir", r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNasir.ini", "75.0"),
    ("Iraq_AlMansour", r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlMansour.ini", "90.0"),
]

FACTORY_SLOTS = {
    1: "CB_MISSILE_A",
    2: "CB_MISSILE_B",
    3: "CB_MISSILE_C",
    4: "CB_MISSILE_D",
    8: "CB_MISSILE_H",
    9: "CB_MISSILE_I",
    10: "CB_MISSILE_J",
    13: "Command_SetRallyPoint",
    14: "Command_Sell",
}

IRAQ_WF_SLOTS = {
    1: "Command_ConstructIraq_T-72",
    2: "Command_ConstructIraq_BMP-1",
    3: "Command_ConstructIraq_BMP-2",
    4: "Command_ConstructIraq_BTR-90",
    5: "Command_ConstructIraq_2S1",
    6: "Command_ConstructIraq_Sam8",
    7: "Command_ConstructIraq_AssadBabel-2",
    8: "Command_ConstructIraq_SA-6",
    9: "Command_ConstructIraq_Sarab7",
    10: "Command_ConstructIraq_Alhussaien",
    11: "Command_ConstructIraqVehicleRoland3K",
    12: "Command_ConstructIraq_BM-21",
    13: "Command_ConstructIraq_R11ScudB",
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


def first_weapon(text: str, name: str) -> str:
    block = command_block(text, "Weapon", name)
    if not block:
        raise SystemExit(f"missing Weapon {name}")
    return block


def patch_build_time(unit_text: str) -> str:
    obj = first_object(unit_text, "Iraq_AlAbbas")
    if field(obj, "BuildTime") != "35.0":
        raise SystemExit(f"unexpected baseline BuildTime {field(obj, 'BuildTime')}")
    new_obj, n = re.subn(
        r"^(\s*BuildTime\s*=\s*)35\.0\s*$",
        r"\g<1>30.0",
        obj,
        count=1,
        flags=re.M,
    )
    if n != 1:
        raise SystemExit("BuildTime replace failed")
    if field(new_obj, "BuildTime") != "30.0":
        raise SystemExit("BuildTime not 30.0 after patch")
    idx = unit_text.find(obj)
    if idx < 0:
        raise SystemExit("Iraq_AlAbbas object not found for splice")
    return unit_text[:idx] + new_obj + unit_text[idx + len(obj) :]


def patch_weapon_autoreload(weapon_text: str) -> str:
    block = first_weapon(weapon_text, "Weapon_Iraq_AlAbbas")
    if "AutoReloadsClip             = No" not in block:
        raise SystemExit("baseline AutoReloadsClip = No missing")
    new_block, n = re.subn(
        r"^\s*AutoReloadsClip\s*=\s*No\s*\r?\n",
        "",
        block,
        count=1,
        flags=re.M,
    )
    if n != 1:
        raise SystemExit("AutoReloadsClip remove failed")
    if re.search(r"AutoReloadsClip", new_block):
        raise SystemExit("AutoReloadsClip residue in Weapon_Iraq_AlAbbas")
    if field(new_block, "PrimaryDamage") != "6000.0":
        raise SystemExit("Al-Abbas damage changed")
    if field(new_block, "AttackRange") != "2752.0":
        raise SystemExit("Al-Abbas range changed")
    if field(new_block, "ProjectileObject") != "Projectile_Iraq_AlAbbas":
        raise SystemExit("Al-Abbas projectile changed")
    if field(new_block, "ClipReloadTime") != "35000":
        raise SystemExit("Al-Abbas ClipReloadTime changed")
    idx = weapon_text.rfind(block)
    if idx < 0:
        raise SystemExit("Weapon_Iraq_AlAbbas not found for splice")
    return weapon_text[:idx] + new_block + weapon_text[idx + len(block) :]


def object_defs(files: dict[str, bytes], name: str) -> list[str]:
    hits = []
    for k, blob in files.items():
        if not k.lower().endswith(".ini"):
            continue
        t = blob.decode("latin1", errors="ignore")
        if re.search(rf"^Object {re.escape(name)}\b", t, re.M):
            hits.append(k)
    return hits


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    changed = sorted(k for k in set(src) | set(data) if src.get(k) != data.get(k))
    allowed = {UNIT_D_KEY, WEAPON_KEY}
    unexpected = [k for k in changed if k not in allowed]
    if unexpected:
        fails.append(f"unexpected mutated files: {unexpected[:8]}")
    if set(data) != set(src):
        fails.append("packed file set changed")

    unit = first_object(data[UNIT_D_KEY].decode("latin1"), "Iraq_AlAbbas")
    src_unit = first_object(src[UNIT_D_KEY].decode("latin1"), "Iraq_AlAbbas")
    if field(unit, "BuildTime") != "30.0":
        fails.append(f"BuildTime {field(unit, 'BuildTime')}")
    if field(src_unit, "BuildTime") != "35.0":
        fails.append("baseline BuildTime not 35.0")
    if field(unit, "CommandSet") != "Scud_B_CommandSet":
        fails.append("CommandSet changed")
    if field(unit, "BuildCost") != field(src_unit, "BuildCost"):
        fails.append("BuildCost changed")
    if "Weapon = PRIMARY   Weapon_Iraq_AlAbbas" not in unit:
        fails.append("PRIMARY weapon lost")
    if re.search(r"^\s*Prerequisites\b", unit, re.M):
        fails.append("Iraq_AlAbbas gained Prerequisites")
    if re.search(r"^\s*Science\s*=", unit, re.M):
        fails.append("Iraq_AlAbbas gained Science")
    pack = re.search(r"PackTime\s*=\s*(\S+)", unit)
    unpack = re.search(r"UnpackTime\s*=\s*(\S+)", unit)
    if not pack or pack.group(1) != "6555":
        fails.append("PackTime changed")
    if not unpack or unpack.group(1) != "6555":
        fails.append("UnpackTime changed")

    weap = data[WEAPON_KEY].decode("latin1")
    src_weap = src[WEAPON_KEY].decode("latin1")
    w = first_weapon(weap, "Weapon_Iraq_AlAbbas")
    sw = first_weapon(src_weap, "Weapon_Iraq_AlAbbas")
    if re.search(r"AutoReloadsClip", w):
        fails.append("AutoReloadsClip still present")
    if "AutoReloadsClip             = No" not in sw:
        fails.append("baseline AutoReloadsClip missing")
    if field(w, "PrimaryDamage") != "6000.0" or field(w, "AttackRange") != "2752.0":
        fails.append("Al-Abbas weapon combat values changed")
    if field(w, "ProjectileObject") != "Projectile_Iraq_AlAbbas":
        fails.append("projectile retargeted")
    if field(w, "ClipReloadTime") != "35000":
        fails.append("ClipReloadTime changed")
    if field(w, "ClipSize") != "1":
        fails.append("ClipSize changed")
    if weap.count("Weapon Weapon_Iraq_AlAbbas\r") + weap.count("Weapon Weapon_Iraq_AlAbbas\n") < 1:
        fails.append("Weapon_Iraq_AlAbbas missing")
    if len(re.findall(r"^Weapon Weapon_Iraq_AlAbbas\b", weap, re.M)) != 1:
        fails.append("Weapon_Iraq_AlAbbas last-wins dups")
    if first_weapon(weap, "Weapon_Iraq_AlFahd500") != first_weapon(src_weap, "Weapon_Iraq_AlFahd500"):
        fails.append("Missile A weapon mutated")
    for other in (
        "Weapon_Iraq_AlHusseinII",
        "Weapon_Iraq_AlSamoudII",
        "Weapon_Iraq_AlBasrah",
        "Weapon_Iraq_AlNasir",
        "Weapon_Iraq_AlMansour",
    ):
        if first_weapon(weap, other) != first_weapon(src_weap, other):
            fails.append(f"{other} mutated")

    cs = data[CS_KEY].decode("latin1")
    src_cs = src[CS_KEY].decode("latin1")
    if cs != src_cs:
        fails.append("CommandSet.ini mutated")
    cb = data[CB_KEY].decode("latin1")
    src_cb = src[CB_KEY].decode("latin1")
    if cb != src_cb:
        fails.append("CommandButton.ini mutated")

    factory = slot_map(command_block(cs, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet"))
    if factory != FACTORY_SLOTS:
        fails.append(f"missile factory slots {factory}")
    btn = command_block(cb, "CommandButton", "CB_MISSILE_D")
    if field(btn, "Command") != "UNIT_BUILD" or field(btn, "Object") != "Iraq_AlAbbas":
        fails.append("CB_MISSILE_D retargeted")
    if "NEED_UPGRADE" in (btn or "") or re.search(r"^\s*(Science|Upgrade)\s*=", btn or "", re.M):
        fails.append("CB_MISSILE_D gained lock")
    fire = command_block(cb, "CommandButton", "Command_FireMainWeapon")
    if field(fire, "Command") != "FIRE_WEAPON" or field(fire, "WeaponSlot") != "PRIMARY":
        fails.append("Command_FireMainWeapon broken")
    if "NEED_UPGRADE" in (fire or "") or "NEED_SPECIAL_POWER_SCIENCE" in (fire or ""):
        fails.append("Command_FireMainWeapon locked")

    for set_name in (
        "Iraq_WarFactoryCommandSet_T3",
        "Iraq_WarFactoryCommandSet_T2",
        "Iraq_WarFactoryCommandSet_T1",
        "Iraq_WarFactoryCommandSet_T",
    ):
        sl = slot_map(command_block(cs, "CommandSet", set_name))
        if sl != IRAQ_WF_SLOTS:
            fails.append(f"{set_name} changed")
        if "CB_MISSILE_D" in sl.values() or "Iraq_AlAbbas" in sl.values():
            fails.append(f"{set_name} unexpectedly produces Al-Abbas")

    for name, key, bt in SIBLINGS:
        if data[key] != src[key]:
            fails.append(f"sibling object mutated {name}")
        obj = first_object(data[key].decode("latin1"), name)
        if field(obj, "BuildTime") != bt:
            fails.append(f"{name} BuildTime {field(obj, 'BuildTime')}")

    if data[UNIT_A_KEY] != src[UNIT_A_KEY]:
        fails.append("Missile A object mutated")
    if data[FACTORY_KEY] != src[FACTORY_KEY]:
        fails.append("missile factory mutated")
    if data[R11_KEY] != src[R11_KEY]:
        fails.append("9P117.ini mutated")
    if data[LOCO_KEY] != src[LOCO_KEY]:
        fails.append("Locomotor.ini mutated")
    if data[UPGRADE_KEY] != src[UPGRADE_KEY]:
        fails.append("Upgrade.ini mutated")
    if data[PT_KEY] != src[PT_KEY]:
        fails.append("PlayerTemplate.ini mutated")
    if data[PROJ_D_KEY] != src[PROJ_D_KEY]:
        fails.append("Al-Abbas projectile mutated")
    if data[UNLOCK_KEY] != src[UNLOCK_KEY]:
        fails.append("PR #589 EU5 unlock mutated")
    if data[IRAQ_WF_KEY] != src[IRAQ_WF_KEY]:
        fails.append("Iraq War Factory object mutated")
    if UNLOCK_KEY not in data:
        fails.append("PR #589 unlock file missing")
    defs = object_defs(data, "Iraq_AlAbbas")
    if defs != [UNIT_D_KEY]:
        fails.append(f"Iraq_AlAbbas object defs {defs}")
    return fails


def dump_extract(extracted: dict[str, bytes]) -> None:
    stage = OUT / "LAST_WINS_EXTRACT/DATA"
    keys = [
        UNIT_D_KEY,
        WEAPON_KEY,
        CS_KEY,
        CB_KEY,
        FACTORY_KEY,
        UNIT_A_KEY,
        UNLOCK_KEY,
        IRAQ_WF_KEY,
        PROJ_D_KEY,
    ]
    for name, key, _bt in SIBLINGS:
        keys.append(key)
    for rel in keys:
        p = stage / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])


def independent_extract_audit(packed: bytes) -> list[str]:
    """Re-parse the written BIG into a clean directory and repeat the audit."""
    fails: list[str] = []
    clean = OUT / "CLEAN_EXTRACT"
    if clean.exists():
        shutil.rmtree(clean)
    extracted = parse_big(packed)
    for name, blob in extracted.items():
        p = clean / name.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
    unit_path = clean / "Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlAbbas.ini"
    weap_path = clean / "Data/INI/Weapon.ini"
    cs_path = clean / "Data/INI/CommandSet.ini"
    cb_path = clean / "Data/INI/CommandButton.ini"
    unit = first_object(unit_path.read_text(encoding="latin1"), "Iraq_AlAbbas")
    weap = weap_path.read_text(encoding="latin1")
    cs = cs_path.read_text(encoding="latin1")
    cb = cb_path.read_text(encoding="latin1")
    if field(unit, "BuildTime") != "30.0":
        fails.append(f"clean extract BuildTime {field(unit, 'BuildTime')}")
    if field(unit, "CommandSet") != "Scud_B_CommandSet":
        fails.append("clean extract CommandSet")
    if "Weapon = PRIMARY   Weapon_Iraq_AlAbbas" not in unit:
        fails.append("clean extract PRIMARY")
    w = first_weapon(weap, "Weapon_Iraq_AlAbbas")
    if re.search(r"AutoReloadsClip", w):
        fails.append("clean extract AutoReloadsClip still present")
    if field(w, "PrimaryDamage") != "6000.0" or field(w, "ProjectileObject") != "Projectile_Iraq_AlAbbas":
        fails.append("clean extract weapon values")
    factory = slot_map(command_block(cs, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet"))
    if factory.get(4) != "CB_MISSILE_D":
        fails.append("clean extract factory slot 4")
    btn = command_block(cb, "CommandButton", "CB_MISSILE_D")
    if field(btn, "Object") != "Iraq_AlAbbas":
        fails.append("clean extract CB_MISSILE_D")
    wf = slot_map(command_block(cs, "CommandSet", "Iraq_WarFactoryCommandSet_T3"))
    if wf != IRAQ_WF_SLOTS:
        fails.append("clean extract Iraq WF")
    if not (clean / "Data/INI/Object/Specter/EU5Unlock/Specter_EU5WFUnlock.ini").is_file():
        fails.append("clean extract missing PR #589 unlock")
    file_count = sum(1 for p in clean.rglob("*") if p.is_file())
    if file_count != len(extracted):
        fails.append(f"clean extract file count {file_count} != {len(extracted)}")
    return fails


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing PR #589 DATA BIG at {SRC_DATA}")
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("PR #589 DATA baseline mismatch")
    if SRC_ART.is_file():
        if SRC_ART.stat().st_size != BASE_ART_SIZE or sha256_path(SRC_ART) != BASE_ART_SHA:
            raise SystemExit("ART baseline mismatch")

    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)
    data[UNIT_D_KEY] = patch_build_time(data[UNIT_D_KEY].decode("latin1")).encode("latin1")
    data[WEAPON_KEY] = patch_weapon_autoreload(data[WEAPON_KEY].decode("latin1")).encode("latin1")

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
    fails.extend(f"CLEAN {x}" for x in independent_extract_audit(out_data.read_bytes()))

    data_sha = sha256_path(out_data)
    changed = sorted(k for k in extracted if src.get(k) != extracted.get(k))
    report = [
        "# SPECTER Iraq Al-Abbas: 30s BuildTime + immediate fire",
        "",
        "Baseline DATA: PR #589 (EU5 WF unlock on PR #588/#587/#584).",
        "Baseline ART: PR #574 ART BIG (unchanged, not rebuilt).",
        "",
        "Production last-wins: CB_MISSILE_D UNIT_BUILD Object=Iraq_AlAbbas",
        "on Iraq_AlFahdMissileFactoryCommandSet slot 4. Iraq War Factory",
        "CommandSets do not produce Al-Abbas and were left unchanged.",
        "",
        "BuildTime: 35.0 -> 30.0 on Object Iraq_AlAbbas only.",
        "Fire lock: Weapon_Iraq_AlAbbas AutoReloadsClip = No (clip never",
        "reloads / can stay empty). Removed so the weapon uses the default",
        "Yes path, same as known-good Missile A. Damage, range, projectile,",
        "ClipReloadTime 35000, and Deploy Pack/Unpack 6555 left unchanged.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART SHA256 (unchanged): {BASE_ART_SHA}",
        f"- ART size (unchanged): {BASE_ART_SIZE}",
        f"- Changed packed files: {', '.join(changed)}",
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
        "## VALIDATION PASS (static / packed last-wins + independent re-extract)",
        "- Iraq_AlAbbas BuildTime is exactly 30.0",
        "- CB_MISSILE_D still UNIT_BUILD Object=Iraq_AlAbbas, no NEED_UPGRADE/Science",
        "- Weapon_Iraq_AlAbbas AutoReloadsClip removed; damage/range/projectile unchanged",
        "- CommandSet remains Scud_B_CommandSet -> Command_FireMainWeapon PRIMARY",
        "- Sibling missile BuildTimes unchanged (A 30 / B 25 / C 22 / H 60 / I 75 / J 90)",
        "- Iraq War Factory CommandSets unchanged; Al-Abbas not added to WF",
        "- PR #589 EU5 unlock file unchanged",
        "- Missile A object + weapon unchanged; 9P117 / factory / loco / upgrade / PT unchanged",
        "- Independent clean extract repeated the same audit",
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
        "OBJECT=Iraq_AlAbbas\n"
        "PRODUCTION_BUTTON=CB_MISSILE_D\n"
        "PRODUCTION_COMMANDSET=Iraq_AlFahdMissileFactoryCommandSet\n"
        "PRODUCTION_SLOT=4\n"
        "BUILD_TIME_BEFORE=35.0\n"
        "BUILD_TIME_AFTER=30.0\n"
        "FIRE_LOCK=Weapon_Iraq_AlAbbas AutoReloadsClip=No\n"
        "FIRE_FIX=removed AutoReloadsClip (default Yes, same as Missile A)\n"
        "WEAPONSET=PRIMARY Weapon_Iraq_AlAbbas Conditions=None\n"
        "UNIT_COMMANDSET=Scud_B_CommandSet\n"
        "FIRE_BUTTON=Command_FireMainWeapon\n"
        f"CHANGED_FILES={', '.join(changed)}\n"
        "BASELINE_DATA=PR #589\n"
        "BASELINE_ART=PR #574\n"
        "IRAQ_WAR_FACTORY=UNCHANGED\n"
        "MISSILE_A=UNCHANGED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "LAST_WINS.txt").write_text(
        "OBJECT=Iraq_AlAbbas defs=1 "
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini" "\n"
        "WEAPON=Weapon_Iraq_AlAbbas defs=1 Data\\INI\\Weapon.ini\n"
        "BUTTON=CB_MISSILE_D defs=1 Data\\INI\\CommandButton.ini\n"
        "FACTORY_SET=Iraq_AlFahdMissileFactoryCommandSet slot 4 CB_MISSILE_D\n"
        "IRAQ_WF=Iraq_WarFactoryCommandSet_T3 does not list Al-Abbas\n"
        "UNIT_COMMANDSET=Scud_B_CommandSet -> Command_FireMainWeapon PRIMARY\n"
        "UNUSED_SET=Iraq_AlAbbasCommandSet is on building Iraq_Abbas only\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Iraq Al-Abbas 30s production + immediate fire\n"
        "\n"
        "Object Iraq_AlAbbas (missile factory slot 4 / CB_MISSILE_D)\n"
        "now has BuildTime 30.0. AutoReloadsClip = No was removed from\n"
        "Weapon_Iraq_AlAbbas so the missile can load and fire after\n"
        "production without an extra clip-activation wait.\n"
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
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_WF_30S_FIRE.zip"
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
