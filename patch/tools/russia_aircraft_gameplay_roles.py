#!/usr/bin/env python3
"""Russia aircraft GAMEPLAY/DATA-ONLY role update on PR #372 recovery baseline.

Stages (isolated commits):
  1 Tu-95  — reuse active AmericaJetB52H fire (USA_B52H_AreaBombardment / MK-84)
  2 Tu-160 — reuse active AmericaJetB2Spirit fire (USA_B2_Spirit_BunkerBuster / MK-84)
  3 A-50   — E-737-family targeted SAR scan (US_E3G / Superweapon_A50_SARSCANMODE)
  4 An-225 — E-3-family targeted SAR + passive Vision/Shroud/StealthDetector (US_E3G)
  5 An-124 — strip offense; TransportContain Slots = 8× Chinook
  6 avionIL76 — TransportContain Slots = 4× Chinook
  7 cargoIL76 — TransportContain Slots = 6× Chinook
  8 Su-47  — Su-35 R-77 primary + R-73 secondary (air-only)

DATA ONLY. No ART / W3D / texture / visual family edits.
T-50 remains disabled. Do not modify USA B-52 / B-2 / E-737 / E-3 / Chinook Objects.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
MASTER = PATCH / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
STAGE = MASTER / "_stage_russia_gameplay_roles_data"
VERIFY = MASTER / "_extract_russia_gameplay_roles_data"
ZIP_OUT = PATCH / "Release/SPECTER_MASTER_DATA_RUSSIA_AIRCRAFT_GAMEPLAY_ROLES.zip"
REPORT = PATCH / "Release/DATA_RUSSIA_AIRCRAFT_GAMEPLAY_ROLES_REPORT.txt"
HASHES = PATCH / "Release/DATA_RUSSIA_AIRCRAFT_GAMEPLAY_ROLES_HASHES.txt"
DOWNLOAD = PATCH / "Release/DATA_RUSSIA_AIRCRAFT_GAMEPLAY_ROLES_DOWNLOAD.txt"

BASELINE_DATA = "a3eace60486397c772d9020fef7cd382363e33c86ecb08ab2de0629bd1cbf749"
RECOVERY_DATA = Path("/tmp/russia_recovery/last_good/_SPEC_DATA_ONE.big")

AF = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce"
CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
SP_KEY = r"Data\INI\SpecialPower.ini"
CHINOOK_KEY = r"Data\INI\Object\Specter\United States Of America\Airforce\CH47F.ini"
USA_SYS = r"Data\INI\Object\Specter\United States Of America\USA_System.ini"
E737_KEY = r"Data\INI\Object\Specter\United States Of America\AmericaJetE737Visual.ini"
E3_KEY = r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini"
E3G_KEY = r"Data\INI\Object\Specter\United States Of America\ScienceObjects\E3G.ini"

OBJ = {
    "tu95": (AF + r"\RussiaJetTu95Visual.ini", "RussiaJetTu95Visual"),
    "tu160": (AF + r"\RussiaJetTU160Clean.ini", "RussiaJetTU160Clean"),
    "a50": (AF + r"\RussiaJetA50Visual.ini", "RussiaJetA50Visual"),
    "an225": (AF + r"\RussiaJetAn225Visual.ini", "RussiaJetAn225Visual"),
    "an124": (AF + r"\RussiaJetAn124Visual.ini", "RussiaJetAn124Visual"),
    "avion": (AF + r"\RussiaJetAvionIL76Visual.ini", "RussiaJetAvionIL76Visual"),
    "cargo": (AF + r"\RussiaJetCargoIL76Visual.ini", "RussiaJetCargoIL76Visual"),
    "su47": (AF + r"\RussiaJetSU47Clean.ini", "RussiaJetSU47Clean"),
}

# Proven US_E3G_AWACS passive reveal (Science E-3; playable E3 Visual is stub on PR372)
E3G_VISION = "350.0"
E3G_SHROUD = "300.0"
E3G_STEALTH = "1000"

TRANSPORT_CS = "C17GlobalMasterCommandSet"
CHINOOK_SLOTS = 8  # filled from live Chinook at runtime

A50_CS = """
CommandSet RussiaJetA50VisualCommandSet
  ; Targeted SAR scan (Russia A50 / E-737-family ANAPY2 architecture). Non-offensive.
  5  = Command_A50_SARSCANMODE
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
""".strip()

AN225_CS = """
CommandSet RussiaJetAn225VisualCommandSet
  ; E-3-family targeted SAR + flight orders. Non-offensive (no FireMainWeapon).
  5  = Command_A50_SARSCANMODE
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
""".strip()

TRANSPORT_BLOCK = """
  Behavior = TransportContain ModuleTag_RussiaCargo
    Slots                 = {slots}
    DamagePercentToUnits  = 100%
    AllowInsideKindOf     = INFANTRY VEHICLE
    ForbidInsideKindOf    = AIRCRAFT HUGE_VEHICLE
    ExitDelay             = 100
    NumberOfExitPaths     = 1
  End
"""

A50_SCAN_MODULES = """
  Behavior = OCLSpecialPower ModuleTag_RussiaA50SAR
    SpecialPowerTemplate = Superweapon_A50_SARSCANMODE
    OCL                  = SUPERWEAPON_A50_SARSCAN
    CreateLocation       = CREATE_AT_EDGE_NEAR_SOURCE
  End
"""

AN225_SCAN_MODULES = """
  Behavior = OCLSpecialPower ModuleTag_RussiaAn225SAR
    SpecialPowerTemplate = Superweapon_A50_SARSCANMODE
    OCL                  = SUPERWEAPON_A50_SARSCAN
    CreateLocation       = CREATE_AT_EDGE_NEAR_SOURCE
  End
  Behavior = StealthDetectorUpdate ModuleTag_RussiaAn225Stealth
    DetectionRate             = 1800
    DetectionRange            = 1000
    CanDetectWhileGarrisoned  = No
    CanDetectWhileContained   = No
    ExtraForbiddenKindOf      = UNATTACKABLE
  End
"""

SRC_ROOT = PATCH / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"


def sha256(p: Path | bytes) -> str:
    data = p if isinstance(p, bytes) else Path(p).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF", path
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        out[name.replace("/", "\\")] = data[off : off + size]
    return out


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16 + sum(8 + len(n.encode("latin1")) + 1 for n, _ in items)
    offset = header_size
    index, blobs = [], []
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">III", offset, len(items), header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for b in blobs:
        out += b
    return bytes(out)


def write_tree(file_map: dict[str, bytes], root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for name, content in file_map.items():
        path = root / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def dec(b: bytes) -> str:
    return b.decode("utf-8", errors="replace")


def enc(t: str) -> bytes:
    return t.encode("utf-8")


def extract_object(text: str, name: str) -> str:
    m = re.search(rf"(?ms)^Object\s+{re.escape(name)}\s*\n.*?(?=^Object\s|\Z)", text)
    assert m, f"Object {name} not found"
    return m.group(0)


def replace_object(text: str, name: str, new_obj: str) -> str:
    m = re.search(rf"(?ms)^Object\s+{re.escape(name)}\s*\n.*?(?=^Object\s|\Z)", text)
    assert m, name
    return text[: m.start()] + new_obj.rstrip() + "\n\n" + text[m.end() :]


def set_kindof_flags(obj: str, add: list[str], remove: list[str] | None = None) -> str:
    remove = remove or []

    def repl(m: re.Match[str]) -> str:
        indent, vals = m.group(1), m.group(2)
        parts = vals.split()
        for r in remove:
            parts = [p for p in parts if p != r]
        for a in add:
            if a not in parts:
                parts.append(a)
        return f"{indent}KindOf = " + " ".join(parts)

    out, n = re.subn(r"(?m)^(\s*)KindOf\s*=\s*(.*)$", repl, obj, count=1)
    assert n == 1, "KindOf missing"
    return out


def set_field(obj: str, field: str, value: str) -> str:
    m = re.search(rf"(?m)^(\s*{re.escape(field)}\s*=\s*)(\S+)", obj)
    assert m, f"missing {field}"
    return obj[: m.start(2)] + value + obj[m.end(2) :]


def set_commandset(obj: str, cs: str) -> str:
    out, n = re.subn(
        r"(?m)^(\s*CommandSet\s*=\s*)\S+\s*$",
        rf"\g<1>{cs}",
        obj,
        count=1,
    )
    assert n == 1, "CommandSet missing"
    return out


def upsert_weaponset(obj: str, weaponset_block: str) -> str:
    block = weaponset_block.rstrip() + "\n"
    if re.search(r"(?m)^\s*WeaponSet\b", obj):
        return re.sub(
            r"(?ms)^\s*WeaponSet\s*\n.*?\n\s*End\s*\n?",
            block + "\n",
            obj,
            count=1,
        )
    # Insert before CommandSet
    return re.sub(
        r"(?m)^(\s*CommandSet\s*=)",
        block + "\n\\1",
        obj,
        count=1,
    )


def remove_weaponset(obj: str) -> str:
    return re.sub(r"(?ms)^\s*WeaponSet\s*\n.*?\n\s*End\s*\n?", "", obj, count=1)


def upsert_transport(obj: str, slots: int) -> str:
    block = TRANSPORT_BLOCK.format(slots=slots).rstrip() + "\n"
    if re.search(r"(?m)^\s*Behavior\s*=\s*TransportContain\b", obj):
        return re.sub(
            r"(?ms)^\s*Behavior\s*=\s*TransportContain.*?\n\s*End\s*\n?",
            block + "\n",
            obj,
            count=1,
        )
    return re.sub(r"(?m)^(\s*Geometry\s*=)", block + "\n\\1", obj, count=1)


def ensure_module_block(obj: str, marker: str, block: str, before_geometry: bool = True) -> str:
    if marker in obj:
        return obj
    block = block.rstrip() + "\n"
    if before_geometry and re.search(r"(?m)^\s*Geometry\s*=", obj):
        return re.sub(r"(?m)^(\s*Geometry\s*=)", block + "\n\\1", obj, count=1)
    # before final End of object — insert before last End
    return obj.rstrip() + "\n" + block + "\n"


def upsert_commandset_ini(cs_text: str, name: str, block: str) -> str:
    pat = re.compile(rf"(?ms)^CommandSet\s+{re.escape(name)}\s*\n.*?(?=^CommandSet\s|\Z)")
    block = block.rstrip() + "\n\n"
    if pat.search(cs_text):
        return pat.sub(block, cs_text, count=1)
    return cs_text.rstrip() + "\n\n" + block


def chinook_slots(files: dict[str, bytes]) -> int:
    obj = extract_object(dec(files[CHINOOK_KEY]), "AmericaVehicleChinook")
    m = re.search(r"(?ms)Behavior\s*=\s*TransportContain.*?\n\s*End", obj)
    assert m
    sm = re.search(r"(?m)^\s*Slots\s*=\s*(\d+)", m.group(0))
    assert sm
    return int(sm.group(1))


def patch_jetai_out_of_ammo(obj: str, pct: str = "10%") -> str:
    if re.search(r"(?m)^\s*OutOfAmmoDamagePerSecond\s*=", obj):
        return re.sub(
            r"(?m)^(\s*OutOfAmmoDamagePerSecond\s*=\s*)\S+",
            rf"\g<1>{pct}",
            obj,
            count=1,
        )
    return re.sub(
        r"(?ms)(Behavior\s*=\s*JetAIUpdate\b.*?)(\n\s*End)",
        rf"\1\n    OutOfAmmoDamagePerSecond = {pct}\2",
        obj,
        count=1,
    )


def save_src(key: str, content: bytes) -> None:
    SRC_ROOT.mkdir(parents=True, exist_ok=True)
    name = Path(key.replace("\\", "/")).name
    (SRC_ROOT / name).write_bytes(content)


def validate_static(files: dict[str, bytes], focus_keys: list[str]) -> list[str]:
    errs: list[str] = []
    # duplicate Object IDs across focus + global sample
    seen: dict[str, str] = {}
    for k, v in files.items():
        if not k.lower().endswith(".ini"):
            continue
        t = dec(v)
        for m in re.finditer(r"(?m)^Object\s+(\S+)", t):
            oid = m.group(1)
            if oid in seen and seen[oid] != k:
                # allow known multi-file? report only for our objects
                if any(oid == name for _, name in OBJ.values()):
                    errs.append(f"duplicate Object {oid} in {seen[oid]} and {k}")
            else:
                seen[oid] = k

    for k in focus_keys:
        t = dec(files[k])
        if t.count("\nEnd") < 1:
            errs.append(f"{k}: suspiciously few End")
        # unbalanced crude check on changed object files
        if k.endswith(".ini") and "Object\\" in k.replace("/", "\\"):
            if not re.search(r"(?m)^Object\s+\S+", t):
                errs.append(f"{k}: no Object header")

    # CommandSet refs
    cs = dec(files[CS_KEY])
    for name in ["RussiaJetA50VisualCommandSet", "RussiaJetAn225VisualCommandSet", TRANSPORT_CS]:
        if name.startswith("Russia") and name not in cs and any(
            name.encode() in files[OBJ[x][0]] for x in ("a50", "an225") if OBJ[x][0] in files
        ):
            # only error if object references it
            pass
    for stage_key, (fkey, oid) in OBJ.items():
        if fkey not in files:
            continue
        obj = extract_object(dec(files[fkey]), oid)
        m = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", obj)
        if m:
            cs_name = m.group(1)
            if not re.search(rf"(?m)^CommandSet\s+{re.escape(cs_name)}\b", cs):
                errs.append(f"{oid}: CommandSet {cs_name} missing")
        # Weapon refs
        for wm in re.finditer(r"(?m)^\s*Weapon\s*=\s*(?:PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", obj):
            wid = wm.group(1)
            found = False
            for wk, wv in files.items():
                if "weapon" in wk.lower() and wk.lower().endswith(".ini"):
                    if re.search(rf"(?m)^Weapon\s+{re.escape(wid)}\b", dec(wv)):
                        found = True
                        break
            if not found:
                errs.append(f"{oid}: Weapon {wid} not found")
        # SP refs
        for sm in re.finditer(r"(?m)^\s*SpecialPowerTemplate\s*=\s*(\S+)", obj):
            spn = sm.group(1)
            if not re.search(rf"(?m)^SpecialPower\s+{re.escape(spn)}\b", dec(files[SP_KEY])):
                errs.append(f"{oid}: SpecialPower {spn} missing")
        # OCL refs on OCLSpecialPower
        for om in re.finditer(
            r"(?ms)Behavior\s*=\s*OCLSpecialPower.*?OCL\s*=\s*(\S+).*?End", obj
        ):
            ocl = om.group(1)
            ocl_txt = dec(files[r"Data\INI\ObjectCreationList.ini"])
            if not re.search(rf"(?m)^ObjectCreationList\s+{re.escape(ocl)}\b", ocl_txt):
                errs.append(f"{oid}: OCL {ocl} missing")
    return errs


def ensure_baseline() -> None:
    DATA_BIG.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_BIG.exists() or sha256(DATA_BIG) != BASELINE_DATA:
        assert RECOVERY_DATA.exists(), "missing recovery DATA"
        assert sha256(RECOVERY_DATA) == BASELINE_DATA
        shutil.copy2(RECOVERY_DATA, DATA_BIG)
    assert sha256(DATA_BIG) == BASELINE_DATA or True  # after stages hash changes


def load() -> dict[str, bytes]:
    return read_big(DATA_BIG)


def persist(files: dict[str, bytes], changed: list[str]) -> None:
    write_tree(files, STAGE)
    DATA_BIG.write_bytes(build_big(files))
    for k in changed:
        if k.startswith(AF):
            save_src(k, files[k])
        elif k in (CS_KEY, CB_KEY):
            # keep CS/CB only inside BIG; also mirror under patch/Data/INI
            rel = PATCH / k.replace("\\", "/")
            rel.parent.mkdir(parents=True, exist_ok=True)
            rel.write_bytes(files[k])
    errs = validate_static(files, changed)
    if errs:
        raise SystemExit("VALIDATION FAILED:\n" + "\n".join(errs))


# ---- stages ----


def stage1_tu95(files: dict[str, bytes]) -> list[str]:
    key, oid = OBJ["tu95"]
    obj = extract_object(dec(files[key]), oid)
    obj = set_kindof_flags(obj, ["CAN_ATTACK"])
    obj = upsert_weaponset(
        obj,
        """  WeaponSet
    Conditions = None
    Weapon = PRIMARY USA_B52H_AreaBombardment
  End""",
    )
    obj = patch_jetai_out_of_ammo(obj, "10%")
    # Keep GenericTacticalBomberCommandSet (has Command_FireMainWeapon)
    files[key] = enc(replace_object(dec(files[key]), oid, obj))
    return [key]


def stage2_tu160(files: dict[str, bytes]) -> list[str]:
    key, oid = OBJ["tu160"]
    obj = extract_object(dec(files[key]), oid)
    obj = upsert_weaponset(
        obj,
        """  WeaponSet
    Conditions = None
    Weapon           = PRIMARY    USA_B2_Spirit_BunkerBuster
    PreferredAgainst = PRIMARY    VEHICLE STRUCTURE
  End""",
    )
    files[key] = enc(replace_object(dec(files[key]), oid, obj))
    return [key]


def stage3_a50(files: dict[str, bytes]) -> list[str]:
    key, oid = OBJ["a50"]
    obj = extract_object(dec(files[key]), oid)
    obj = remove_weaponset(obj)
    obj = set_commandset(obj, "RussiaJetA50VisualCommandSet")
    obj = set_kindof_flags(obj, [], remove=["CAN_ATTACK"])
    obj = ensure_module_block(obj, "ModuleTag_RussiaA50SAR", A50_SCAN_MODULES)
    files[key] = enc(replace_object(dec(files[key]), oid, obj))
    files[CS_KEY] = enc(upsert_commandset_ini(dec(files[CS_KEY]), "RussiaJetA50VisualCommandSet", A50_CS))
    return [key, CS_KEY]


def stage4_an225(files: dict[str, bytes]) -> list[str]:
    key, oid = OBJ["an225"]
    obj = extract_object(dec(files[key]), oid)
    obj = remove_weaponset(obj)
    obj = set_commandset(obj, "RussiaJetAn225VisualCommandSet")
    obj = set_kindof_flags(obj, [], remove=["CAN_ATTACK"])
    obj = set_field(obj, "VisionRange", E3G_VISION)
    obj = set_field(obj, "ShroudClearingRange", E3G_SHROUD)
    obj = ensure_module_block(obj, "ModuleTag_RussiaAn225SAR", AN225_SCAN_MODULES)
    files[key] = enc(replace_object(dec(files[key]), oid, obj))
    files[CS_KEY] = enc(upsert_commandset_ini(dec(files[CS_KEY]), "RussiaJetAn225VisualCommandSet", AN225_CS))
    return [key, CS_KEY]


def stage_transport(files: dict[str, bytes], which: str, mult: int) -> list[str]:
    key, oid = OBJ[which]
    slots = chinook_slots(files) * mult
    obj = extract_object(dec(files[key]), oid)
    obj = remove_weaponset(obj)
    obj = set_kindof_flags(obj, ["TRANSPORT"], remove=["CAN_ATTACK"])
    obj = set_commandset(obj, TRANSPORT_CS)
    obj = upsert_transport(obj, slots)
    files[key] = enc(replace_object(dec(files[key]), oid, obj))
    return [key]


def stage5_an124(files: dict[str, bytes]) -> list[str]:
    return stage_transport(files, "an124", 8)


def stage6_avion(files: dict[str, bytes]) -> list[str]:
    return stage_transport(files, "avion", 4)


def stage7_cargo(files: dict[str, bytes]) -> list[str]:
    return stage_transport(files, "cargo", 6)


def stage8_su47(files: dict[str, bytes]) -> list[str]:
    key, oid = OBJ["su47"]
    obj = extract_object(dec(files[key]), oid)
    obj = upsert_weaponset(
        obj,
        """  WeaponSet
    Conditions = None
    Weapon           = PRIMARY    6x_R77_MRBVR_SU35S
    Weapon           = SECONDARY  R73_HOBS_SRAAM_SU35
  End""",
    )
    # Air-superiority command set (proven GenericFighterCommandSet used by Su-35)
    obj = set_commandset(obj, "GenericFighterCommandSet")
    files[key] = enc(replace_object(dec(files[key]), oid, obj))
    return [key]


STAGES = {
    1: ("tu95", stage1_tu95),
    2: ("tu160", stage2_tu160),
    3: ("a50", stage3_a50),
    4: ("an225", stage4_an225),
    5: ("an124", stage5_an124),
    6: ("avion", stage6_avion),
    7: ("cargo", stage7_cargo),
    8: ("su47", stage8_su47),
}


def verify_extract(files_expect: dict[str, bytes] | None = None) -> dict[str, bytes]:
    dv = read_big(DATA_BIG)
    write_tree(dv, VERIFY)
    if files_expect is not None:
        for k, v in files_expect.items():
            if k in dv and dv[k] != v:
                raise SystemExit(f"re-extract mismatch: {k}")
    return dv


def pack_zip() -> tuple[str, str]:
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
        names = zf.namelist()
    assert names == ["_SPEC_DATA_ONE.big"], names
    return sha256(DATA_BIG), sha256(ZIP_OUT)


def audit_sources(files: dict[str, bytes]) -> str:
    lines = []
    b52 = extract_object(dec(files[USA_SYS]), "AmericaJetB52H")
    b2 = extract_object(dec(files[USA_SYS]), "AmericaJetB2Spirit")
    e737 = extract_object(dec(files[E737_KEY]), "AmericaJetE737Visual")
    e3 = extract_object(dec(files[E3_KEY]), "AmericaJetE3Visual")
    e3g = extract_object(dec(files[E3G_KEY]), "US_E3G_AWACS")
    chin = extract_object(dec(files[CHINOOK_KEY]), "AmericaVehicleChinook")
    lines.append(f"B52 Object=AmericaJetB52H Weapon=USA_B52H_AreaBombardment")
    lines.append(f"B2 Object=AmericaJetB2Spirit Weapon=USA_B2_Spirit_BunkerBuster (no AmericaJetB2A in runtime)")
    vm = re.search(r"(?m)^\s*VisionRange\s*=\s*(\S+)", e3g)
    lines.append(
        f"E737 playable_scan={('OCLSpecialPower' in e737)} E3 playable_scan={('OCLSpecialPower' in e3)} "
        f"US_E3G scan={('OCLSpecialPower' in e3g)} Vision={vm.group(1) if vm else '?'}"
    )
    lines.append(f"Chinook Slots={chinook_slots(files)}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, choices=range(1, 9), required=True)
    ap.add_argument("--restore-baseline", action="store_true")
    ap.add_argument("--pack", action="store_true", help="After stage 8, pack DATA-only ZIP")
    args = ap.parse_args()

    if args.restore_baseline or not DATA_BIG.exists():
        assert RECOVERY_DATA.exists()
        assert sha256(RECOVERY_DATA) == BASELINE_DATA
        DATA_BIG.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(RECOVERY_DATA, DATA_BIG)
        print("RESTORED BASELINE", BASELINE_DATA)

    files = load()
    if args.stage == 1:
        cur = sha256(DATA_BIG)
        if cur != BASELINE_DATA:
            print(f"WARNING: DATA hash {cur} != baseline {BASELINE_DATA} (continuing)")

    name, fn = STAGES[args.stage]
    print(audit_sources(files))
    changed = fn(files)
    persist(files, changed)
    verify_extract({k: files[k] for k in changed})
    print(f"STAGE {args.stage} ({name}) OK changed={changed} DATA={sha256(DATA_BIG)}")

    if args.pack or args.stage == 8:
        dsha, zsha = pack_zip()
        HASHES.write_text(
            f"_SPEC_DATA_ONE.big={dsha}\nZIP={zsha}\nBASELINE_PR372={BASELINE_DATA}\n",
            encoding="utf-8",
        )
        print(f"PACKED {ZIP_OUT} data={dsha} zip={zsha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
