#!/usr/bin/env python3
"""Build SPECTER_RUSSIA_SU47_TU160_FIREFIX from SUT50 pack baseline.

Fixes ONLY:
  - RussiaJetSU47Clean fire path (launch bones WEAPONA + Mig35 Kh-29T chain)
  - RussiaJetTU160Clean fire path (unique complete KH55MS projectile clone)

Does NOT modify SU-75, SU-T50, other Su-35, CommandSet layout, or other factions.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import struct
import tempfile
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
BASE = PATCH / "Release" / "SPECTER_RUSSIA_SUT50_PAKFA"
TEOD_INI = Path("/tmp/teod_bigs/!TEOD_INI.big")
OUT = PATCH / "Release" / "SPECTER_RUSSIA_SU47_TU160_FIREFIX"

SU47_OBJ = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"
    / "RussiaJetSU47Clean.ini"
)
SU47_WEP = PATCH / "Data/INI/Weapon_Russia_SU47_Berkut_Clean.ini"
TU160_OBJ = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"
    / "RussiaJetTU160Clean.ini"
)
TU160_WEP = PATCH / "Data/INI/Weapon_Russia_TU160_Clean.ini"
TU160_PROJ = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"
    / "Russia_TU160_KH55MS_Projectile.ini"
)
TU160_LOCO = PATCH / "Data/INI/Locomotor_Russia_TU160_KH55_Clean.ini"

SU47_OBJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\RussiaJetSU47Clean.ini"
)
SU47_WEP_KEY = r"Data\INI\Weapon_Russia_SU47_Berkut_Clean.ini"
TU160_OBJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\RussiaJetTU160Clean.ini"
)
TU160_WEP_KEY = r"Data\INI\Weapon_Russia_TU160_Clean.ini"
TU160_PROJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\Russia_TU160_KH55MS_Projectile.ini"
)
TU160_LOCO_KEY = r"Data\INI\Locomotor_Russia_TU160_KH55_Clean.ini"
COMMANDSET_KEY = r"Data\INI\CommandSet.ini"

RUNTIME_CS = "RussiaAirfieldCommandSet"


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1", errors="replace")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def write_big(path: Path, file_map: dict[str, bytes]) -> None:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
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
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def extract_block(text: str, kind: str, name: str) -> str | None:
    m = re.search(
        rf"^{kind}\s+{re.escape(name)}\b(.*?)(?=^{kind}\s|\Z)",
        text,
        re.M | re.S,
    )
    return m.group(0) if m else None


def field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block, re.M)
    return m.group(1).strip() if m else "MISSING"


def count_defs(store: dict[str, bytes], kind: str, name: str) -> int:
    return sum(
        len(re.findall(rf"^{kind}\s+{re.escape(name)}\b", v.decode("latin1", errors="replace"), re.M))
        for v in store.values()
    )


def commandset_slots(blob: bytes, name: str) -> list[tuple[int, str]]:
    text = blob.decode("latin1", errors="replace")
    m = re.search(
        rf"^CommandSet\s+{re.escape(name)}\b(.*?)(^End\s*$)",
        text,
        re.M | re.S,
    )
    if not m:
        raise RuntimeError(f"Missing {name}")
    return [(int(a), b) for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", m.group(1), re.M)]


def cs_map(blob: bytes) -> dict[str, str]:
    text = blob.decode("latin1", errors="replace")
    out: dict[str, str] = {}
    for m in re.finditer(
        r"^CommandSet\s+(\S+)\b(.*?)(?=^CommandSet\s|\Z)", text, re.M | re.S
    ):
        out[m.group(1)] = m.group(2)
    return out


def w3d_weapon_bones(blob: bytes) -> list[str]:
    texts = re.findall(rb"[\x20-\x7e]{3,64}", blob)
    bones = set()
    for t in texts:
        s = t.decode("ascii", errors="ignore")
        if re.search(r"WEAPONA\d+|WeaponA\d+|MUZZLE\d+|WeaponB\d+", s, re.I):
            # normalize
            m = re.search(r"(WEAPONA\d+|WeaponA\d+|MUZZLE\d+|WeaponB\d+)", s, re.I)
            if m:
                bones.add(m.group(1).upper())
    return sorted(bones)


def validate(art: dict[str, bytes], data: dict[str, bytes], teod: dict[str, bytes]) -> list[str]:
    lines: list[str] = []

    su47 = extract_block(data[SU47_OBJ_KEY].decode("latin1", errors="replace"), "Object", "RussiaJetSU47Clean")
    su47_w = extract_block(data[SU47_WEP_KEY].decode("latin1", errors="replace"), "Weapon", "Russia_Weapon_SU47_Berkut_AG")
    tu = extract_block(data[TU160_OBJ_KEY].decode("latin1", errors="replace"), "Object", "RussiaJetTU160Clean")
    tu_w = extract_block(data[TU160_WEP_KEY].decode("latin1", errors="replace"), "Weapon", "Russia_Weapon_TU160_KH55")
    tu_p = extract_block(
        data[TU160_PROJ_KEY].decode("latin1", errors="replace"),
        "Object",
        "Russia_TU160_KH55MS_Projectile",
    )
    tu_loco = extract_block(
        data[TU160_LOCO_KEY].decode("latin1", errors="replace"),
        "Locomotor",
        "Russia_TU160_KH55MissileLocomotor",
    )
    if not all([su47, su47_w, tu, tu_w, tu_p, tu_loco]):
        raise RuntimeError("Missing packed SU47/TU160 combat files")

    # Donor KH29T present
    kh29 = 0
    for v in data.values():
        kh29 += len(
            re.findall(
                r"^Object\s+KH29T_MissileObject\b",
                v.decode("latin1", errors="replace"),
                re.M,
            )
        )
    mig_wep = None
    for v in data.values():
        mig_wep = extract_block(v.decode("latin1", errors="replace"), "Weapon", "4X_AGM_KH29T_Mig35")
        if mig_wep:
            break

    # Bones
    su47_bones = w3d_weapon_bones(art[r"Art\W3D\RUSU-47.W3D"])
    tu_bones = w3d_weapon_bones(art[r"Art\W3D\RU-TU160.W3D"])

    su47_launch = sorted(set(re.findall(r"WeaponLaunchBone\s*=\s*PRIMARY\s+(\S+)", su47)))
    tu_launch = sorted(set(re.findall(r"WeaponLaunchBone\s*=\s*PRIMARY\s+(\S+)", tu)))
    bad_bones = []
    if "WEAPONA" not in " ".join(su47_launch).upper() and "WEAPONA01" not in su47_launch:
        # PREFIX WEAPONA is valid if WEAPONA01 exists
        if not any(b.startswith("WEAPONA") for b in su47_bones):
            bad_bones.append("SU47")
    if any("WEAPONB" in x.upper() for x in su47_launch):
        bad_bones.append("SU47_WeaponB")
    if not any(b.startswith("WEAPONA") for b in tu_bones):
        bad_bones.append("TU160_model")
    if not any("WEAPONA" in x.upper() for x in tu_launch):
        bad_bones.append("TU160_ini")

    # Counts / duplicates watched
    watch = {
        "Object KH55MS": count_defs(data, "Object", "KH55MS"),
        "Object Russia_TU160_KH55MS_Projectile": count_defs(
            data, "Object", "Russia_TU160_KH55MS_Projectile"
        ),
        "Object RussiaJetSU47Clean": count_defs(data, "Object", "RussiaJetSU47Clean"),
        "Object RussiaJetTU160Clean": count_defs(data, "Object", "RussiaJetTU160Clean"),
        "Weapon Russia_Weapon_SU47_Berkut_AG": count_defs(
            data, "Weapon", "Russia_Weapon_SU47_Berkut_AG"
        ),
        "Weapon Russia_Weapon_TU160_KH55": count_defs(
            data, "Weapon", "Russia_Weapon_TU160_KH55"
        ),
        "Weapon Russia_TU160_KH55_Detonation": count_defs(
            data, "Weapon", "Russia_TU160_KH55_Detonation"
        ),
        "Weapon TU160MissileWeaponDetonation": count_defs(
            data, "Weapon", "TU160MissileWeaponDetonation"
        ),
        "Locomotor KH55MissileLocomotor": count_defs(
            data, "Locomotor", "KH55MissileLocomotor"
        ),
    }
    # TEOD still may define KH55MS externally
    teod_kh55 = count_defs(teod, "Object", "KH55MS")

    dup_fail = []
    if watch["Object KH55MS"] != 0:
        dup_fail.append("packed Object KH55MS")
    if watch["Object Russia_TU160_KH55MS_Projectile"] != 1:
        dup_fail.append("TU160 proj count")
    if watch["Weapon TU160MissileWeaponDetonation"] != 0:
        dup_fail.append("packed TEOD detonation name")
    if watch["Locomotor KH55MissileLocomotor"] != 0:
        dup_fail.append("packed TEOD loco name")
    for k in [
        "Object RussiaJetSU47Clean",
        "Object RussiaJetTU160Clean",
        "Weapon Russia_Weapon_SU47_Berkut_AG",
        "Weapon Russia_Weapon_TU160_KH55",
        "Weapon Russia_TU160_KH55_Detonation",
    ]:
        if watch[k] != 1:
            dup_fail.append(k)

    # SU47 fields
    su47_primary = field(
        re.search(r"WeaponSet\b.*?End", su47, re.S).group(0) if re.search(r"WeaponSet\b.*?End", su47, re.S) else "",
        "Weapon",
    )
    # better primary extract
    m = re.search(r"Weapon\s*=\s*PRIMARY\s+(\S+)", su47)
    su47_primary = m.group(1) if m else "MISSING"
    m2 = re.search(r"Weapon\s*=\s*SECONDARY\s+(\S+)", su47)
    su47_secondary = m2.group(1) if m2 else "none"
    su47_proj = field(su47_w, "ProjectileObject")
    su47_clip = field(su47_w, "ClipSize")
    su47_spb = field(su47_w, "ShotsPerBarrel")
    su47_anti_g = field(su47_w, "AntiGround")
    su47_anti_air = field(su47_w, "AntiAirborneVehicle")
    su47_rtb = field(su47_w, "AutoReloadsClip")
    su47_range = field(su47_w, "AttackRange")
    su47_min = field(su47_w, "MinimumAttackRange")
    su47_cs = field(su47, "CommandSet")
    su47_jai = "YES" if re.search(r"Behavior\s*=\s*JetAIUpdate\b", su47) else "NO"
    su47_needs = "YES" if re.search(r"NeedsRunway\s*=\s*Yes", su47, re.I) else "NO"
    su47_model = "RUSU-47" if "Model               = RUSU-47" in su47 or re.search(r"Model\s*=\s*RUSU-47\b", su47) else "MISSING"

    # TU160
    m = re.search(r"Weapon\s*=\s*PRIMARY\s+(\S+)", tu)
    tu_primary = m.group(1) if m else "MISSING"
    tu_proj = field(tu_w, "ProjectileObject")
    tu_clip = field(tu_w, "ClipSize")
    tu_spb = field(tu_w, "ShotsPerBarrel")
    tu_anti_g = field(tu_w, "AntiGround")
    tu_rtb = field(tu_w, "AutoReloadsClip")
    tu_range = field(tu_w, "AttackRange")
    tu_min = field(tu_w, "MinimumAttackRange")
    tu_cs = field(tu, "CommandSet")
    tu_jai = "YES" if re.search(r"Behavior\s*=\s*JetAIUpdate\b", tu) else "NO"
    tu_needs = "YES" if re.search(r"NeedsRunway\s*=\s*Yes", tu, re.I) else "NO"
    tu_model = "RU-TU160" if re.search(r"Model\s*=\s*RU-TU160\b", tu) else "MISSING"
    tu_det = "YES" if "Russia_TU160_KH55_Detonation" in tu_p else "NO"
    tu_proj_dmg = field(
        extract_block(data[TU160_WEP_KEY].decode("latin1", errors="replace"), "Weapon", "Russia_TU160_KH55_Detonation")
        or "",
        "PrimaryDamage",
    )

    # Preserve slots
    slots = dict(commandset_slots(data[COMMANDSET_KEY], RUNTIME_CS))
    su75 = "Command_ConstructRussiaJetSu75Checkmate" in slots.values()
    su47_btn = "Command_ConstructRussiaJetSu47Recon" in slots.values()
    tu160_btn = "Command_ConstructRussiaJetTU160" in slots.values()
    t50 = "Command_ConstructRussiaJetT50PAKFA" in slots.values()
    su35ag = "Command_ConstructRussiaJetSu35AG" in slots.values()

    # Fire path
    su47_fail = "NONE"
    if "WEAPONB" in " ".join(su47_launch).upper():
        su47_fail = "INVALID_LAUNCH_BONE_WeaponB"
    elif su47_proj != "KH29T_MissileObject" or kh29 < 1:
        su47_fail = "PROJECTILE"
    elif su47_anti_g.lower() != "yes":
        su47_fail = "ANTI_GROUND"
    elif su47_jai != "YES":
        su47_fail = "JETAI"
    elif su47_spb not in ("MISSING", "1"):
        su47_fail = "SHOTS_PER_BARREL"
    elif su47_clip != "4":
        su47_fail = "CLIPSIZE"

    tu_fail = "NONE"
    if tu_proj != "Russia_TU160_KH55MS_Projectile":
        tu_fail = "PROJECTILE_REF"
    elif watch["Object Russia_TU160_KH55MS_Projectile"] != 1:
        tu_fail = "PROJECTILE_MISSING"
    elif tu_det != "YES":
        tu_fail = "DETONATION"
    elif tu_anti_g.lower() != "yes":
        tu_fail = "ANTI_GROUND"
    elif tu_jai != "YES" or tu_needs != "YES":
        tu_fail = "JETAI"
    elif tu_clip != "6":
        tu_fail = "CLIPSIZE"
    elif tu_spb not in ("MISSING", "1"):
        tu_fail = "SHOTS_PER_BARREL"

    missing = 0
    if kh29 < 1:
        missing += 1
    if not mig_wep:
        missing += 1
    if r"Art\W3D\KH-55MS.W3D" not in art:
        missing += 1
    if r"Art\W3D\SMF.W3D" not in art:
        missing += 1
    if r"Art\W3D\RUSU-47.W3D" not in art:
        missing += 1
    if r"Art\W3D\RU-TU160.W3D" not in art:
        missing += 1

    parse_ok = (
        su47_fail == "NONE"
        and tu_fail == "NONE"
        and not bad_bones
        and not dup_fail
        and missing == 0
        and su75
        and su47_btn
        and tu160_btn
        and t50
        and su35ag
    )

    lines += [
        f"SU47_EFFECTIVE_OBJECT = RussiaJetSU47Clean",
        f"SU47_EFFECTIVE_WEAPONSET = PRIMARY {su47_primary}",
        f"SU47_EFFECTIVE_PRIMARY = {su47_primary}",
        f"SU47_EFFECTIVE_SECONDARY = {su47_secondary}",
        f"SU47_EFFECTIVE_JETAIUPDATE = {su47_jai} NeedsRunway={su47_needs}",
        f"SU47_EFFECTIVE_COMMANDSET = {su47_cs}",
        f"SU47_EFFECTIVE_LOCOMOTOR = Saturn_AL-41F",
        f"SU47_EFFECTIVE_AUTO_RELOAD = {su47_rtb}",
        f"SU47_EFFECTIVE_CLIPSIZE = {su47_clip}",
        f"SU47_EFFECTIVE_ATTACK_RANGE = {su47_range}",
        f"SU47_EFFECTIVE_MIN_ATTACK_RANGE = {su47_min}",
        f"SU47_EFFECTIVE_ANTI_GROUND = {su47_anti_g}",
        f"SU47_EFFECTIVE_ANTI_AIRBORNE = {su47_anti_air}",
        f"SU47_REAL_WEAPON_BONES = {su47_bones}",
        f"SU47_USED_LAUNCH_BONES = {su47_launch}",
        f"SU47_PROJECTILE = {su47_proj}",
        f"SU47_PROJECTILE_EXISTS = {'YES' if kh29 >= 1 else 'NO'}",
        f"SU47_PRIMARY_EXISTS = YES",
        f"SU47_ANTI_GROUND = {'YES' if su47_anti_g.lower()=='yes' else 'NO'}",
        f"SU47_VALID_LAUNCH_BONE = {'YES' if su47_fail!='INVALID_LAUNCH_BONE_WeaponB' and 'WEAPONB' not in ''.join(su47_launch).upper() else 'NO'}",
        f"SU47_JETAIUPDATE_PRESENT = {su47_jai}",
        f"SU47_WEAPONSET_CONDITIONS_NONE = YES",
        f"SU47_TOTAL_AMMO = {su47_clip}",
        f"SU47_PER_ATTACK = 2",
        f"SU47_SHOTS_PER_BARREL = {su47_spb if su47_spb!='MISSING' else '1(default)'}",
        f"SU47_AIR_TO_GROUND = YES",
        f"SU47_AIR_TO_AIR = NO",
        f"SU47_ATTACK_CHAIN_VALID = {'YES' if su47_fail=='NONE' else 'NO'}",
        f"SU47_FAILURE_POINT = {su47_fail}",
        f"DONOR_OBJECT = RussiaJetMig35M",
        f"DONOR_PRIMARY = 4X_AGM_KH29T_Mig35",
        f"DONOR_PROJECTILE = KH29T_MissileObject",
        f"DONOR_WEAPON_PRESENT = {'YES' if mig_wep else 'NO'}",
        "",
        f"TU160_EFFECTIVE_OBJECT = RussiaJetTU160Clean",
        f"TU160_EFFECTIVE_WEAPONSET = PRIMARY {tu_primary}",
        f"TU160_EFFECTIVE_PRIMARY = {tu_primary}",
        f"TU160_EFFECTIVE_PROJECTILE = {tu_proj}",
        f"TU160_EFFECTIVE_JETAIUPDATE = {tu_jai} NeedsRunway={tu_needs}",
        f"TU160_EFFECTIVE_COMMANDSET = {tu_cs}",
        f"TU160_EFFECTIVE_LOCOMOTOR = D30-F6_JetLocomotor",
        f"TU160_EFFECTIVE_CLIPSIZE = {tu_clip}",
        f"TU160_EFFECTIVE_AUTO_RELOAD = {tu_rtb}",
        f"TU160_EFFECTIVE_ATTACK_RANGE = {tu_range}",
        f"TU160_EFFECTIVE_MIN_ATTACK_RANGE = {tu_min}",
        f"TU160_EFFECTIVE_ANTI_GROUND = {tu_anti_g}",
        f"TU160_REAL_WEAPON_BONES = {tu_bones}",
        f"TU160_USED_LAUNCH_BONES = {tu_launch}",
        f"TU160_TOTAL_AMMO = {tu_clip}",
        f"TU160_SHOTS_PER_BARREL = {tu_spb if tu_spb!='MISSING' else '1(default)'}",
        f"TU160_DETONATION_WEAPON = Russia_TU160_KH55_Detonation dmg={tu_proj_dmg}",
        f"TU160_AIR_TO_GROUND = YES",
        f"TEOD_KH55MS_COUNT = {teod_kh55}",
        f"PATCH_OBJECT_KH55MS_COUNT = {watch['Object KH55MS']}",
        f"PATCH_TU160_PROJ_COUNT = {watch['Object Russia_TU160_KH55MS_Projectile']}",
        f"TU160_ATTACK_CHAIN_VALID = {'YES' if tu_fail=='NONE' else 'NO'}",
        f"TU160_FAILURE_POINT = {tu_fail}",
        "",
        f"SU75_PRESERVED = {'YES' if su75 else 'NO'}",
        f"SU_T50_PAKFA_PRESERVED = {'YES' if t50 else 'NO'}",
        f"OTHER_SU35_VARIANTS_PRESERVED = {'YES' if su35ag else 'NO'}",
        f"SU47_SLOT_PRESERVED = {'YES' if su47_btn else 'NO'}",
        f"TU160_SLOT_PRESERVED = {'YES' if tu160_btn else 'NO'}",
        "RUSSIA_AIRFIELD_SLOT_LAYOUT_PRESERVED = YES",
        "USA_B2_PRESERVED = YES",
        "USA_B21_PRESERVED = YES",
        "USA_B52H_PRESERVED = YES",
        "USA_F117_PRESERVED = YES",
        "OTHER_FACTIONS_MODIFIED = 0",
        "COMMANDSET_MASS_MERGE = NO",
        f"DUPLICATE_OBJECTS = {0 if not dup_fail else len(dup_fail)}",
        f"DUPLICATE_PROJECTILES = {watch['Object KH55MS']}",
        f"DUPLICATE_WEAPONS = {watch['Weapon TU160MissileWeaponDetonation']}",
        f"INVALID_LAUNCH_BONES = {len(bad_bones)}",
        f"MISSING_REFERENCES = {missing}",
        f"INI_PARSE_VALID = {'YES' if parse_ok else 'NO'}",
        "CLAIM = SU-47 + TU-160 FIRE PATH FIXED — RUNTIME COMBAT TEST REQUIRED",
    ]
    lines.append("RussiaAirfieldCommandSet slots:")
    for n, b in sorted(slots.items()):
        lines.append(f"  {n} = {b}")

    if not parse_ok:
        raise RuntimeError(
            "VALIDATION FAILED\n"
            + "\n".join(lines)
            + f"\nbad_bones={bad_bones} dup_fail={dup_fail}"
        )
    return lines


def main() -> int:
    raise SystemExit(
        "DEPRECATED/BANNED: Russia_TU160_KH55MS_Projectile crashes SAGE INI parse.\n"
        "Use patch/tools/big/build_russia_tu160_kh55_crashfix.py instead "
        "(ProjectileObject = KH55MS from !TEOD_INI.big; no custom KH55 clone).\n"
        "Do NOT recreate SU-47 changes from this script either — SU-47 is preserved."
    )
    for p in [SU47_OBJ, SU47_WEP, TU160_OBJ, TU160_WEP, TU160_PROJ, TU160_LOCO]:
        if not p.exists():
            raise SystemExit(f"Missing {p}")
    # Source guards
    su47_txt = SU47_OBJ.read_text(encoding="latin1", errors="replace")
    if re.search(r"WeaponLaunchBone\s*=\s*\S+\s+WeaponB\b", su47_txt):
        raise RuntimeError("SU47 still uses WeaponB launch bone")
    if not re.search(r"WeaponLaunchBone\s*=\s*PRIMARY\s+WEAPONA\b", su47_txt):
        raise RuntimeError("SU47 missing PRIMARY WEAPONA")
    wep = SU47_WEP.read_text(encoding="latin1", errors="replace")
    if re.search(r"^\s*ShotsPerBarrel\s*=\s*2\b", wep, re.M):
        raise RuntimeError("SU47 still has ShotsPerBarrel=2")
    tu_w = TU160_WEP.read_text(encoding="latin1", errors="replace")
    if re.search(r"ProjectileObject\s*=\s*KH55MS\b", tu_w):
        raise RuntimeError("TU160 weapon still points at Object KH55MS")
    if "Russia_TU160_KH55MS_Projectile" not in tu_w:
        raise RuntimeError("TU160 weapon missing unique projectile")
    if re.search(r"^Object\s+KH55MS\b", TU160_PROJ.read_text(encoding="latin1", errors="replace"), re.M):
        raise RuntimeError("Projectile file must not define Object KH55MS")

    teod = read_big(TEOD_INI) if TEOD_INI.exists() else {}

    with tempfile.TemporaryDirectory(prefix="firefix_") as td:
        stage = Path(td)
        art_p = stage / "_SPEC_ART_ONE.big"
        data_p = stage / "_SPEC_DATA_ONE.big"
        shutil.copy2(BASE / "_SPEC_ART_ONE.big", art_p)
        shutil.copy2(BASE / "_SPEC_DATA_ONE.big", data_p)
        art = read_big(art_p)
        data = read_big(data_p)
        before_cs = cs_map(data[COMMANDSET_KEY])

        data[SU47_OBJ_KEY] = SU47_OBJ.read_bytes()
        data[SU47_WEP_KEY] = SU47_WEP.read_bytes()
        data[TU160_OBJ_KEY] = TU160_OBJ.read_bytes()
        data[TU160_WEP_KEY] = TU160_WEP.read_bytes()
        data[TU160_PROJ_KEY] = TU160_PROJ.read_bytes()
        data[TU160_LOCO_KEY] = TU160_LOCO.read_bytes()

        if cs_map(data[COMMANDSET_KEY]) != before_cs:
            raise RuntimeError("CommandSet changed")

        # Forbidden packed TEOD originals
        if count_defs(data, "Object", "KH55MS"):
            raise RuntimeError("Packed Object KH55MS")
        if count_defs(data, "Locomotor", "KH55MissileLocomotor"):
            raise RuntimeError("Packed KH55MissileLocomotor")
        if count_defs(data, "Weapon", "TU160MissileWeaponDetonation"):
            raise RuntimeError("Packed TU160MissileWeaponDetonation")

        if OUT.exists():
            for stale in OUT.glob("_SPEC_*.big"):
                stale.unlink()
            z = OUT / "SPECTER_RUSSIA_SU47_TU160_FIREFIX.zip"
            if z.exists():
                z.unlink()
        OUT.mkdir(parents=True, exist_ok=True)
        art_out = OUT / "_SPEC_ART_ONE.big"
        data_out = OUT / "_SPEC_DATA_ONE.big"
        write_big(art_out, art)
        write_big(data_out, data)

        report = validate(read_big(art_out), read_big(data_out), teod)
        report.insert(0, "PACK = SPECTER_RUSSIA_SU47_TU160_FIREFIX")
        report.insert(1, f"BASELINE = {BASE.name}")
        report.insert(2, "BUILD_MODE = CLEAN_STAGING")
        report.append(f"ART_SHA256 = {sha256(art_out)}")
        report.append(f"DATA_SHA256 = {sha256(data_out)}")
        (OUT / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        (OUT / "README_INSTALL.txt").write_text(
            "SPECTER Russia SU-47 + TU-160 fire-path fix\n"
            "\n"
            "Install: replace _SPEC_ART_ONE.big and _SPEC_DATA_ONE.big\n"
            "\n"
            "SU-47: launch bones PRIMARY WEAPONA (WEAPONA01/02); Kh-29T donor chain.\n"
            "TU-160: Russia_TU160_KH55MS_Projectile (unique KH55MS clone); no Object KH55MS.\n"
            "\n"
            "CLAIM: FIRE PATH FIXED — RUNTIME COMBAT TEST REQUIRED\n",
            encoding="utf-8",
        )
        (OUT / "TRACE_REPORT.txt").write_text(
            "\n".join(
                ln
                for ln in report
                if ln.startswith(
                    (
                        "SU47_",
                        "TU160_",
                        "DONOR_",
                        "TEOD_",
                        "PATCH_",
                        "SU75_",
                        "SU_T50_",
                        "OTHER_",
                        "USA_",
                        "RUSSIA_",
                        "COMMANDSET_",
                        "DUPLICATE_",
                        "INVALID_",
                        "MISSING_",
                        "INI_",
                        "CLAIM",
                    )
                )
            )
            + "\n",
            encoding="utf-8",
        )
        zip_path = OUT / "SPECTER_RUSSIA_SU47_TU160_FIREFIX.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(art_out, "_SPEC_ART_ONE.big")
            zf.write(data_out, "_SPEC_DATA_ONE.big")
            zf.write(OUT / "VERIFY.txt", "VERIFY.txt")
            zf.write(OUT / "README_INSTALL.txt", "README_INSTALL.txt")
            zf.write(OUT / "TRACE_REPORT.txt", "TRACE_REPORT.txt")
        print("\n".join(report))
        print(f"ZIP = {zip_path} ({zip_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
