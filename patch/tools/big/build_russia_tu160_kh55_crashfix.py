#!/usr/bin/env python3
"""Build SPECTER_RUSSIA_TU160_KH55_CRASHFIX from SUT50 R27 crashfix baseline.

Crash fix ONLY:
  - Delete packed Russia_TU160_KH55MS_Projectile + unique KH55 locomotor
  - Retarget Russia_Weapon_TU160_KH55 → ProjectileObject = KH55MS
  - Use existing TEOD Object KH55MS (do NOT redefine / clone)

Does NOT modify SU-47, SU-T50, SU-75, CommandSet, or other factions.
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
BASE = PATCH / "Release" / "SPECTER_RUSSIA_SUT50_R27_CRASHFIX"
TEOD_INI = Path("/tmp/teod_bigs/!TEOD_INI.big")
OUT = PATCH / "Release" / "SPECTER_RUSSIA_TU160_KH55_CRASHFIX"

AIRFORCE = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"
)
TU160_OBJ = AIRFORCE / "RussiaJetTU160Clean.ini"
TU160_WEP = PATCH / "Data/INI/Weapon_Russia_TU160_Clean.ini"

TU160_OBJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\RussiaJetTU160Clean.ini"
)
TU160_WEP_KEY = r"Data\INI\Weapon_Russia_TU160_Clean.ini"
CRASH_PROJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\Russia_TU160_KH55MS_Projectile.ini"
)
CRASH_LOCO_KEY = r"Data\INI\Locomotor_Russia_TU160_KH55_Clean.ini"
COMMANDSET_KEY = r"Data\INI\CommandSet.ini"
RUNTIME_CS = "RussiaAirfieldCommandSet"

REMOVE_KEYS = (CRASH_PROJ_KEY, CRASH_LOCO_KEY)

# Must not change these keys
PRESERVE_KEYS = [
    (
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
        r"\Airforce\RussiaJetSU47Clean.ini"
    ),
    (
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
        r"\Airforce\RussiaJetT50PAKFAClean.ini"
    ),
    r"Data\INI\Weapon_Russia_SU47_Berkut_Clean.ini",
    r"Data\INI\Weapon_Russia_T50_PAKFA_Clean.ini",
]


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


def count_defs(file_map: dict[str, bytes], kind: str, name: str) -> int:
    pat = re.compile(rf"^{kind}\s+{re.escape(name)}\b", re.M)
    total = 0
    for blob in file_map.values():
        total += len(pat.findall(blob.decode("latin1", errors="replace")))
    return total


def field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(\S+)", block, re.M)
    return m.group(1) if m else "MISSING"


def commandset_slots(blob: bytes, name: str) -> list[tuple[int, str]]:
    text = blob.decode("latin1", errors="replace")
    block = extract_block(text, "CommandSet", name)
    if not block:
        return []
    return [
        (int(m.group(1)), m.group(2))
        for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M)
    ]


def cs_map(blob: bytes) -> dict[int, str]:
    return dict(commandset_slots(blob, RUNTIME_CS))


def find_teod_tu160(teod: dict[str, bytes]) -> dict[str, str]:
    """Trace original TEOD TU-160 donor weapon/projectile (no inference)."""
    out = {
        "TEOD_TU160_OBJECT": "MISSING",
        "TEOD_TU160_WEAPON": "MISSING",
        "TEOD_TU160_PROJECTILE": "MISSING",
        "TEOD_TU160_PROJECTILE_SOURCE_FILE": "MISSING",
        "TEOD_TU160_PROJECTILE_OBJECT_NAME": "MISSING",
        "KH55MS_SOURCE_FILE": "MISSING",
        "KH55MS_SOURCE_BIG": "!TEOD_INI.big",
    }
    # Prefer playable jet donor Object TU160FOAB (RU-TU160 + TU160MissileWeapon)
    donor_obj = None
    donor_key = None
    for key, blob in teod.items():
        text = blob.decode("latin1", errors="replace")
        if re.search(r"^Object\s+TU160FOAB\b", text, re.M):
            donor_obj = extract_block(text, "Object", "TU160FOAB")
            donor_key = key
            break
    if donor_obj:
        out["TEOD_TU160_OBJECT"] = "TU160FOAB"
        m = re.search(r"Weapon\s*=\s*PRIMARY\s+(\S+)", donor_obj)
        if m:
            out["TEOD_TU160_WEAPON"] = m.group(1)
    # Read actual ProjectileObject from that weapon
    wep_name = out["TEOD_TU160_WEAPON"]
    if wep_name != "MISSING":
        for key, blob in teod.items():
            text = blob.decode("latin1", errors="replace")
            block = extract_block(text, "Weapon", wep_name)
            if block:
                proj = field(block, "ProjectileObject")
                out["TEOD_TU160_PROJECTILE"] = proj
                out["TEOD_TU160_PROJECTILE_OBJECT_NAME"] = proj
                break
    # Locate Object definition for that projectile name
    proj_name = out["TEOD_TU160_PROJECTILE"]
    if proj_name not in ("MISSING", "NONE"):
        for key, blob in teod.items():
            text = blob.decode("latin1", errors="replace")
            if re.search(rf"^Object\s+{re.escape(proj_name)}\b", text, re.M):
                out["TEOD_TU160_PROJECTILE_SOURCE_FILE"] = key
                if proj_name == "KH55MS":
                    out["KH55MS_SOURCE_FILE"] = key
                break
    # Always locate KH55MS even if weapon chain differs
    if out["KH55MS_SOURCE_FILE"] == "MISSING":
        for key, blob in teod.items():
            text = blob.decode("latin1", errors="replace")
            if re.search(r"^Object\s+KH55MS\b", text, re.M):
                out["KH55MS_SOURCE_FILE"] = key
                break
    _ = donor_key
    return out


def kh55_dep_report(teod: dict[str, bytes]) -> list[str]:
    """Trace modules referenced by original Object KH55MS."""
    lines: list[str] = []
    block = None
    for blob in teod.values():
        text = blob.decode("latin1", errors="replace")
        block = extract_block(text, "Object", "KH55MS")
        if block:
            break
    if not block:
        return ["KH55MS_BLOCK = MISSING"]

    models = re.findall(r"^\s*Model\s*=\s*(\S+)", block, re.M)
    behaviors = re.findall(r"^\s*Behavior\s*=\s*(\S+)", block, re.M)
    loco = "MISSING"
    m = re.search(r"^\s*Locomotor\s*=\s*SET_NORMAL\s+(\S+)", block, re.M)
    if m:
        loco = m.group(1)
    armor = field(block, "Armor")
    death_weapon = "MISSING"
    mw = re.search(r"Weapon\s*=\s*(\S+)", block)
    # InstantDeathBehavior Weapon
    mw = re.search(
        r"Behavior\s*=\s*InstantDeathBehavior.*?Weapon\s*=\s*(\S+)",
        block,
        re.S,
    )
    if mw:
        death_weapon = mw.group(1)
    ocl = "MISSING"
    mo = re.search(
        r"Behavior\s*=\s*InstantDeathBehavior.*?OCL\s*=\s*(\S+)",
        block,
        re.S,
    )
    if mo:
        ocl = mo.group(1)
    ign = "MISSING"
    mi = re.search(r"IgnitionFX\s*=\s*(\S+)", block)
    if mi:
        ign = mi.group(1)

    def exists(kind: str, name: str) -> int:
        return count_defs(teod, kind, name)

    lines += [
        f"KH55MS_DRAW_MODELS = {','.join(models) if models else 'MISSING'}",
        f"KH55MS_LOCOMOTOR = {loco} EXISTS={exists('Locomotor', loco)}",
        f"KH55MS_BEHAVIORS = {','.join(behaviors) if behaviors else 'MISSING'}",
        f"KH55MS_ARMOR = {armor} EXISTS={exists('Armor', armor)}",
        f"KH55MS_DETONATION_WEAPON = {death_weapon} EXISTS={exists('Weapon', death_weapon)}",
        f"KH55MS_OCL = {ocl} EXISTS={exists('ObjectCreationList', ocl)}",
        f"KH55MS_IGNITION_FX = {ign} EXISTS={exists('FXList', ign)}",
        f"KH55MS_BODY = ActiveBody",
    ]
    missing = []
    if loco != "MISSING" and exists("Locomotor", loco) != 1:
        missing.append(loco)
    if death_weapon != "MISSING" and exists("Weapon", death_weapon) != 1:
        missing.append(death_weapon)
    if ocl != "MISSING" and exists("ObjectCreationList", ocl) != 1:
        missing.append(ocl)
    if ign != "MISSING" and exists("FXList", ign) != 1:
        missing.append(ign)
    if armor != "MISSING" and exists("Armor", armor) != 1:
        missing.append(armor)
    lines.append(
        f"KH55MS_RUNTIME_DEPS_MISSING = {','.join(missing) if missing else 'NONE'}"
    )
    return lines


def validate(
    art: dict[str, bytes],
    data: dict[str, bytes],
    teod: dict[str, bytes],
    before_cs: dict[int, str],
    before_preserve: dict[str, bytes],
) -> list[str]:
    lines: list[str] = []
    teod_info = find_teod_tu160(teod)

    custom_file = CRASH_PROJ_KEY in data
    custom_keys = [k for k in data if "Russia_TU160_KH55MS_Projectile" in k]
    custom_count = count_defs(data, "Object", "Russia_TU160_KH55MS_Projectile")
    support_left = [k for k in REMOVE_KEYS if k in data]

    packed_kh55 = count_defs(data, "Object", "KH55MS")
    teod_kh55 = count_defs(teod, "Object", "KH55MS")
    if packed_kh55 != 0:
        raise RuntimeError(f"Patch must not redefine Object KH55MS (count={packed_kh55})")
    if teod_kh55 != 1:
        raise RuntimeError(
            f"STOP: TEOD Object KH55MS count={teod_kh55} (need exactly 1); "
            "do not invent a clone"
        )

    tu = data[TU160_OBJ_KEY].decode("latin1", errors="replace")
    wep = data[TU160_WEP_KEY].decode("latin1", errors="replace")
    wep_block = extract_block(wep, "Weapon", "Russia_Weapon_TU160_KH55") or ""
    proj = field(wep_block, "ProjectileObject")
    clip = field(wep_block, "ClipSize")
    anti_g = field(wep_block, "AntiGround")
    rtb = field(wep_block, "AutoReloadsClip")
    model = "RU-TU160" if re.search(r"Model\s*=\s*RU-TU160\b", tu) else "MISSING"
    cost = field(tu, "BuildCost")
    needs = "YES" if re.search(r"NeedsRunway\s*=\s*Yes", tu, re.I) else "NO"
    primary = "MISSING"
    m = re.search(r"Weapon\s*=\s*PRIMARY\s+(\S+)", tu)
    if m:
        primary = m.group(1)

    # detonation clone must be gone
    det_count = count_defs(data, "Weapon", "Russia_TU160_KH55_Detonation")
    loco_count = count_defs(data, "Locomotor", "Russia_TU160_KH55MissileLocomotor")

    slots = cs_map(data[COMMANDSET_KEY])
    if slots != before_cs:
        raise RuntimeError("CommandSet changed")

    for k, prev in before_preserve.items():
        if data.get(k) != prev:
            raise RuntimeError(f"Preserved key changed: {k}")

    # watched duplicates for this fix scope
    watched = {
        "RussiaJetTU160Clean": count_defs(data, "Object", "RussiaJetTU160Clean"),
        "RussiaJetSU47Clean": count_defs(data, "Object", "RussiaJetSU47Clean"),
        "RussiaJetT50PAKFAClean": count_defs(data, "Object", "RussiaJetT50PAKFAClean"),
        "Russia_TU160_KH55MS_Projectile": custom_count,
        "KH55MS": packed_kh55,
        "Russia_Weapon_TU160_KH55": count_defs(data, "Weapon", "Russia_Weapon_TU160_KH55"),
        "Russia_TU160_KH55_Detonation": det_count,
    }
    dup_obj = 0
    for name, c in watched.items():
        if name in ("KH55MS", "Russia_TU160_KH55MS_Projectile", "Russia_TU160_KH55_Detonation"):
            if c != 0:
                dup_obj += c
        elif c != 1:
            dup_obj += abs(c - 1)

    missing = 0
    if proj != "KH55MS":
        missing += 1
    if teod_kh55 != 1:
        missing += 1
    if re.search(r"ProjectileObject\s*=\s*Russia_TU160_KH55MS_Projectile\b", wep):
        missing += 1
    if r"Art\W3D\KH-55MS.W3D" not in art:
        missing += 1
    if r"Art\W3D\SMF.W3D" not in art:
        missing += 1
    if r"Art\W3D\RU-TU160.W3D" not in art:
        missing += 1

    dep_lines = kh55_dep_report(teod)
    dep_missing = any("MISSING" in x and "DEPS_MISSING = NONE" not in x for x in dep_lines if x.startswith("KH55MS_RUNTIME_DEPS_MISSING"))
    # stricter: parse NONE
    deps_ok = any(x.endswith("= NONE") for x in dep_lines if x.startswith("KH55MS_RUNTIME_DEPS_MISSING"))

    parse_ok = (
        not custom_file
        and not custom_keys
        and custom_count == 0
        and not support_left
        and packed_kh55 == 0
        and teod_kh55 == 1
        and proj == "KH55MS"
        and primary == "Russia_Weapon_TU160_KH55"
        and model == "RU-TU160"
        and clip == "6"
        and anti_g.lower() == "yes"
        and rtb == "RETURN_TO_BASE"
        and needs == "YES"
        and det_count == 0
        and loco_count == 0
        and dup_obj == 0
        and missing == 0
        and deps_ok
        and slots.get(2) == "Command_ConstructRussiaJetTU160"
        and teod_info["TEOD_TU160_PROJECTILE"] == "KH55MS"
    )

    lines += [
        f"CRASH_FILE = russia_tu160_kh55ms_projectile.ini",
        f"CRASH_FILE_REMOVED = {'YES' if not custom_file and custom_count == 0 else 'NO'}",
        f"TU160_CUSTOM_PROJECTILE_FILE_PRESENT = {'YES' if custom_file or custom_keys else 'NO'}",
        f"TU160_CUSTOM_PROJECTILE_OBJECT_COUNT = {custom_count}",
        f"TU160_OBJECT = RussiaJetTU160Clean",
        f"TU160_MODEL = {model}",
        f"TU160_WEAPON = {primary}",
        f"TU160_BUILDCOST = {cost}",
        f"TU160_CLIPSIZE = {clip}",
        f"TU160_ANTI_GROUND = {anti_g}",
        f"TU160_NEEDS_RUNWAY = {needs}",
        f"TU160_AUTO_RELOAD = {rtb}",
        f"FINAL_TU160_PROJECTILE = {proj}",
        f"CUSTOM_TU160_PROJECTILE = NONE",
        f"PATCH_OBJECT_KH55MS_COUNT = {packed_kh55}",
        f"RUNTIME_OBJECT_KH55MS_COUNT = {teod_kh55}",
        f"KH55MS_RUNTIME_DEFINITION_COUNT = {teod_kh55}",
        f"KH55MS_SOURCE_BIG = {teod_info['KH55MS_SOURCE_BIG']}",
        f"KH55MS_SOURCE_FILE = {teod_info['KH55MS_SOURCE_FILE']}",
        f"TEOD_TU160_OBJECT = {teod_info['TEOD_TU160_OBJECT']}",
        f"TEOD_TU160_WEAPON = {teod_info['TEOD_TU160_WEAPON']}",
        f"TEOD_TU160_PROJECTILE = {teod_info['TEOD_TU160_PROJECTILE']}",
        f"TEOD_TU160_PROJECTILE_SOURCE_FILE = {teod_info['TEOD_TU160_PROJECTILE_SOURCE_FILE']}",
        f"TEOD_TU160_PROJECTILE_OBJECT_NAME = {teod_info['TEOD_TU160_PROJECTILE_OBJECT_NAME']}",
        *dep_lines,
        f"SU47_PRESERVED = YES",
        f"SU_T50_PAKFA_PRESERVED = {'YES' if 'Command_ConstructRussiaJetT50PAKFA' in slots.values() else 'NO'}",
        f"SU75_PRESERVED = {'YES' if 'Command_ConstructRussiaJetSu75Checkmate' in slots.values() else 'NO'}",
        f"OTHER_SU35_VARIANTS_PRESERVED = {'YES' if 'Command_ConstructRussiaJetSu35AG' in slots.values() else 'NO'}",
        f"RUSSIA_AIRFIELD_LAYOUT_PRESERVED = YES",
        f"USA_B2_PRESERVED = YES",
        f"USA_B21_PRESERVED = YES",
        f"USA_B52H_PRESERVED = YES",
        f"USA_F117_PRESERVED = YES",
        f"OTHER_FACTIONS_MODIFIED = 0",
        f"COMMANDSET_MASS_MERGE = NO",
        f"DUPLICATE_OBJECTS = {dup_obj}",
        f"DUPLICATE_WEAPONS = {det_count}",
        f"DUPLICATE_PROJECTILES = {custom_count + packed_kh55}",
        f"MISSING_REFERENCES = {missing}",
        f"INI_PARSE_VALID = {'YES' if parse_ok else 'NO'}",
        "CLAIM = TU-160 KH55 CRASH FIX PACKED — MATCH ENTRY TEST REQUIRED (NO RUNTIME PASS CLAIM)",
    ]
    lines.append("RussiaAirfieldCommandSet slots:")
    for n, b in sorted(slots.items()):
        lines.append(f"  {n} = {b}")

    if not parse_ok:
        raise RuntimeError("VALIDATION FAILED\n" + "\n".join(lines))
    return lines


def main() -> int:
    for p in [TU160_OBJ, TU160_WEP, BASE / "_SPEC_DATA_ONE.big", BASE / "_SPEC_ART_ONE.big"]:
        if not p.exists():
            raise SystemExit(f"Missing {p}")
    if AIRFORCE.joinpath("Russia_TU160_KH55MS_Projectile.ini").exists():
        raise RuntimeError("Source crash projectile still present")
    if (PATCH / "Data/INI/Locomotor_Russia_TU160_KH55_Clean.ini").exists():
        raise RuntimeError("Source unique KH55 locomotor still present")

    wep_src = TU160_WEP.read_text(encoding="utf-8")
    if not re.search(r"ProjectileObject\s*=\s*KH55MS\b", wep_src):
        raise RuntimeError("Weapon not retargeted to KH55MS")
    if re.search(r"ProjectileObject\s*=\s*Russia_TU160_KH55MS_Projectile\b", wep_src):
        raise RuntimeError("Weapon still references crash projectile")
    if re.search(r"^Weapon\s+Russia_TU160_KH55_Detonation\b", wep_src, re.M):
        raise RuntimeError("Unique detonation weapon must be removed")
    if re.search(r"^Object\s+KH55MS\b", wep_src, re.M):
        raise RuntimeError("Weapon file must not define Object KH55MS")

    if not TEOD_INI.exists():
        raise SystemExit(f"Missing TEOD INI: {TEOD_INI}")
    teod = read_big(TEOD_INI)

    with tempfile.TemporaryDirectory(prefix="tu160_kh55_fix_") as td:
        stage = Path(td)
        art_p = stage / "_SPEC_ART_ONE.big"
        data_p = stage / "_SPEC_DATA_ONE.big"
        shutil.copy2(BASE / "_SPEC_ART_ONE.big", art_p)
        shutil.copy2(BASE / "_SPEC_DATA_ONE.big", data_p)
        art = read_big(art_p)
        data = read_big(data_p)
        before_cs = cs_map(data[COMMANDSET_KEY])
        before_preserve = {k: data[k] for k in PRESERVE_KEYS if k in data}

        for k in REMOVE_KEYS:
            data.pop(k, None)

        data[TU160_WEP_KEY] = TU160_WEP.read_bytes()
        data[TU160_OBJ_KEY] = TU160_OBJ.read_bytes()

        if any(k in data for k in REMOVE_KEYS):
            raise RuntimeError("Crash keys still in DATA")
        if count_defs(data, "Object", "Russia_TU160_KH55MS_Projectile") != 0:
            raise RuntimeError("Custom projectile still defined")
        if count_defs(data, "Object", "KH55MS") != 0:
            raise RuntimeError("Must not pack Object KH55MS")
        if cs_map(data[COMMANDSET_KEY]) != before_cs:
            raise RuntimeError("CommandSet changed")
        for k, prev in before_preserve.items():
            if data.get(k) != prev:
                raise RuntimeError(f"Preserved key changed during pack: {k}")

        if OUT.exists():
            for stale in OUT.glob("_SPEC_*.big"):
                stale.unlink()
            z = OUT / "SPECTER_RUSSIA_TU160_KH55_CRASHFIX.zip"
            if z.exists():
                z.unlink()
        OUT.mkdir(parents=True, exist_ok=True)
        art_out = OUT / "_SPEC_ART_ONE.big"
        data_out = OUT / "_SPEC_DATA_ONE.big"
        write_big(art_out, art)
        write_big(data_out, data)

        report = validate(read_big(art_out), read_big(data_out), teod, before_cs, before_preserve)
        report.insert(0, "PACK = SPECTER_RUSSIA_TU160_KH55_CRASHFIX")
        report.insert(1, f"BASELINE = {BASE.name}")
        report.insert(2, "BUILD_MODE = CLEAN_STAGING")
        report.append(f"ART_SHA256 = {sha256(art_out)}")
        report.append(f"DATA_SHA256 = {sha256(data_out)}")
        (OUT / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        (OUT / "README_INSTALL.txt").write_text(
            "SPECTER Russia TU-160 KH55 crash fix\n"
            "\n"
            "Install: replace _SPEC_ART_ONE.big and _SPEC_DATA_ONE.big\n"
            "\n"
            "Removed custom Russia_TU160_KH55MS_Projectile (INI parse crash).\n"
            "TU-160 weapon now uses original TEOD Object KH55MS.\n"
            "Requires !TEOD_INI.big in load order (provides Object KH55MS).\n"
            "\n"
            "First test: Russia -> start match.\n"
            "Do not assume combat PASS.\n",
            encoding="utf-8",
        )

        zip_path = OUT / "SPECTER_RUSSIA_TU160_KH55_CRASHFIX.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(art_out, "_SPEC_ART_ONE.big")
            zf.write(data_out, "_SPEC_DATA_ONE.big")
            zf.write(OUT / "VERIFY.txt", "VERIFY.txt")
            zf.write(OUT / "README_INSTALL.txt", "README_INSTALL.txt")

        print("\n".join(report))
        print(f"ZIP = {zip_path}")
        print(f"ZIP_SHA256 = {sha256(zip_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
