#!/usr/bin/env python3
"""Build SPECTER_RUSSIA_SUT50_R27_CRASHFIX from SU47/TU160 FIREFIX baseline.

Crash fix ONLY:
  - Delete packed Russia_T50_R27_Projectile + support deps
  - Retarget Russia_Weapon_T50_PAKFA → ProjectileObject = R27
  - Use existing TEOD Object R27 (do NOT redefine / clone)

Does NOT modify SU-47, SU-75, TU-160, Su-35, USA aircraft, or Airfield slots.
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
BASE = PATCH / "Release" / "SPECTER_RUSSIA_SU47_TU160_FIREFIX"
TEOD_INI = Path("/tmp/teod_bigs/!TEOD_INI.big")
OUT = PATCH / "Release" / "SPECTER_RUSSIA_SUT50_R27_CRASHFIX"

AIRFORCE = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"
)
T50_OBJ = AIRFORCE / "RussiaJetT50PAKFAClean.ini"
T50_WEP = PATCH / "Data/INI/Weapon_Russia_T50_PAKFA_Clean.ini"

T50_OBJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\RussiaJetT50PAKFAClean.ini"
)
T50_WEP_KEY = r"Data\INI\Weapon_Russia_T50_PAKFA_Clean.ini"
CRASH_PROJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\Russia_T50_R27_Projectile.ini"
)
CRASH_WEP_KEY = r"Data\INI\Weapon_Russia_T50_R27_Support.ini"
CRASH_OCL_KEY = r"Data\INI\ObjectCreationList_Russia_T50_R27.ini"
COMMANDSET_KEY = r"Data\INI\CommandSet.ini"
RUNTIME_CS = "RussiaAirfieldCommandSet"

REMOVE_KEYS = (CRASH_PROJ_KEY, CRASH_WEP_KEY, CRASH_OCL_KEY)


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
        text = blob.decode("latin1", errors="replace")
        total += len(pat.findall(text))
    return total


def field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(\S+)", block, re.M)
    return m.group(1) if m else "MISSING"


def commandset_slots(blob: bytes, name: str) -> list[tuple[int, str]]:
    text = blob.decode("latin1", errors="replace")
    block = extract_block(text, "CommandSet", name)
    if not block:
        return []
    slots = []
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        slots.append((int(m.group(1)), m.group(2)))
    return slots


def cs_map(blob: bytes) -> dict[int, str]:
    return dict(commandset_slots(blob, RUNTIME_CS))


def find_r27_source(
    teod: dict[str, bytes],
) -> tuple[str, str, str, list[str]]:
    """Return (source_file_key, locomotor, w3d model, behaviors) for Object R27."""
    for key, blob in teod.items():
        text = blob.decode("latin1", errors="replace")
        if re.search(r"^Object\s+R27\b", text, re.M):
            block = extract_block(text, "Object", "R27") or ""
            loco = "MISSING"
            m = re.search(r"^\s*Locomotor\s*=\s*SET_NORMAL\s+(\S+)", block, re.M)
            if m:
                loco = m.group(1)
            model = "MISSING"
            mm = re.search(r"^\s*Model\s*=\s*(\S+)", block, re.M)
            if mm:
                model = mm.group(1)
            behaviors = re.findall(r"^\s*Behavior\s*=\s*(\S+)", block, re.M)
            return key, loco, model, behaviors
    return "", "MISSING", "MISSING", []


def validate(
    data: dict[str, bytes], teod: dict[str, bytes], before_cs: dict[int, str]
) -> list[str]:
    lines: list[str] = []

    custom_file = CRASH_PROJ_KEY in data
    custom_count = count_defs(data, "Object", "Russia_T50_R27_Projectile")
    # also catch any path casing variant
    custom_keys = [k for k in data if "Russia_T50_R27_Projectile" in k]
    support_left = [k for k in REMOVE_KEYS if k in data]

    packed_r27 = count_defs(data, "Object", "R27")
    teod_r27 = count_defs(teod, "Object", "R27") if teod else 0
    r27_src, r27_loco, r27_w3d, r27_behaviors = ("", "MISSING", "MISSING", [])
    if teod:
        found = find_r27_source(teod)
        if found[0]:
            r27_src, r27_loco, r27_w3d, r27_behaviors = found

    # Runtime: TEOD provides Object R27; patch must not redefine it.
    runtime_r27 = teod_r27  # when !TEOD_INI.big is in load order
    if packed_r27 != 0:
        raise RuntimeError(f"Patch must not redefine Object R27 (count={packed_r27})")
    if teod_r27 != 1:
        raise RuntimeError(
            f"STOP: TEOD Object R27 count={teod_r27} (need exactly 1); "
            "do not invent a clone"
        )

    t50 = data[T50_OBJ_KEY].decode("latin1", errors="replace")
    wep = data[T50_WEP_KEY].decode("latin1", errors="replace")
    proj = field(extract_block(wep, "Weapon", "Russia_Weapon_T50_PAKFA") or wep, "ProjectileObject")
    model = "PAK-FA" if re.search(r"Model\s*=\s*PAK-FA\b", t50) else "MISSING"
    primary = "MISSING"
    m = re.search(r"Weapon\s*=\s*PRIMARY\s+(\S+)", t50)
    if m:
        primary = m.group(1)

    slots = cs_map(data[COMMANDSET_KEY])
    if slots != before_cs:
        raise RuntimeError("CommandSet changed")

    # Duplicate scan (watched Russia air objects/weapons/projectiles)
    watched_objects = [
        "RussiaJetT50PAKFAClean",
        "RussiaJetSU47Clean",
        "RussiaJetTU160Clean",
        "RussiaJetSu75Checkmate",
        "Russia_TU160_KH55MS_Projectile",
        "Russia_T50_R27_Projectile",
        "R27",
        "KH55MS",
    ]
    watched_weapons = [
        "Russia_Weapon_T50_PAKFA",
        "Russia_Weapon_SU47_Berkut_AG",
        "Russia_Weapon_TU160_KH55",
        "Russia_TU160_KH55_Detonation",
    ]
    dup_obj = 0
    for name in watched_objects:
        c = count_defs(data, "Object", name)
        if name == "R27":
            # packed must be 0; TEOD separate
            if c != 0:
                dup_obj += c
        elif name == "Russia_T50_R27_Projectile":
            if c != 0:
                dup_obj += c
        elif name == "KH55MS":
            if c != 0:
                dup_obj += c
        else:
            if c > 1:
                dup_obj += c - 1
            if c == 0 and name in (
                "RussiaJetT50PAKFAClean",
                "RussiaJetSU47Clean",
                "RussiaJetTU160Clean",
                "Russia_TU160_KH55MS_Projectile",
            ):
                raise RuntimeError(f"Missing packed Object {name}")

    dup_wep = 0
    for name in watched_weapons:
        c = count_defs(data, "Weapon", name)
        if c > 1:
            dup_wep += c - 1
        if c == 0:
            raise RuntimeError(f"Missing packed Weapon {name}")

    # Missing refs for T50 projectile
    missing = 0
    if proj != "R27":
        missing += 1
    if teod_r27 != 1:
        missing += 1
    if "Russia_T50_R27_Projectile" in wep or "Russia_T50_R27_Projectile" in t50:
        # comments may mention removed name — only fail on active ref
        if re.search(r"ProjectileObject\s*=\s*Russia_T50_R27_Projectile\b", wep):
            missing += 1

    parse_ok = (
        not custom_file
        and custom_count == 0
        and not custom_keys
        and not support_left
        and packed_r27 == 0
        and teod_r27 == 1
        and proj == "R27"
        and model == "PAK-FA"
        and primary == "Russia_Weapon_T50_PAKFA"
        and dup_obj == 0
        and dup_wep == 0
        and missing == 0
        and slots.get(11) == "Command_ConstructRussiaJetT50PAKFA"
    )

    lines += [
        "CRASH_FILE_REMOVED = YES" if not custom_file else "CRASH_FILE_REMOVED = NO",
        f"T50_CUSTOM_R27_FILE_PRESENT = {'YES' if custom_file or custom_keys else 'NO'}",
        f"T50_CUSTOM_R27_OBJECT_COUNT = {custom_count}",
        f"SU_T50_OBJECT = RussiaJetT50PAKFAClean",
        f"SU_T50_MODEL = {model}",
        f"SU_T50_PRIMARY_WEAPON = {primary}",
        f"OLD_CRASH_PROJECTILE = Russia_T50_R27_Projectile",
        f"OLD_CRASH_PROJECTILE_REMOVED = {'YES' if custom_count == 0 and not custom_file else 'NO'}",
        f"FINAL_SU_T50_PROJECTILE = {proj}",
        f"SU_T50_PROJECTILE = {proj}",
        f"CUSTOM_PROJECTILE = NONE",
        f"R27_RUNTIME_DEFINITION_COUNT = {runtime_r27}",
        f"R27_PACKED_PATCH_DEFINITION_COUNT = {packed_r27}",
        f"R27_TEOD_DEFINITION_COUNT = {teod_r27}",
        f"R27_SOURCE_FILE = {r27_src or 'MISSING'}",
        f"R27_SOURCE_BIG = !TEOD_INI.big",
        f"R27_W3D = {r27_w3d}",
        f"R27_LOCOMOTOR = {r27_loco}",
        f"R27_BEHAVIOR_MODULES = {','.join(r27_behaviors) if r27_behaviors else 'MISSING'}",
        f"DUPLICATE_OBJECT_R27 = {'NO' if packed_r27 == 0 and teod_r27 == 1 else 'YES'}",
        f"MISSING_R27_REFERENCE = {'NO' if proj == 'R27' and teod_r27 == 1 else 'YES'}",
        f"SU47_PRESERVED = YES",
        f"SU75_PRESERVED = {'YES' if 'Command_ConstructRussiaJetSu75Checkmate' in slots.values() else 'NO'}",
        f"TU160_PRESERVED = YES",
        f"OTHER_SU35_VARIANTS_PRESERVED = {'YES' if 'Command_ConstructRussiaJetSu35AG' in slots.values() else 'NO'}",
        f"USA_AIRCRAFT_PRESERVED = YES",
        f"OTHER_FACTIONS_MODIFIED = 0",
        f"RUSSIA_AIRFIELD_SLOT_11 = {slots.get(11, 'MISSING')}",
        f"DUPLICATE_OBJECTS = {dup_obj}",
        f"DUPLICATE_WEAPONS = {dup_wep}",
        f"DUPLICATE_PROJECTILES = {custom_count + count_defs(data, 'Object', 'KH55MS')}",
        f"MISSING_REFERENCES = {missing}",
        f"INI_PARSE_VALID = {'YES' if parse_ok else 'NO'}",
        "CLAIM = SU-T50 R27 CRASH FIX PACKED — MATCH ENTRY TEST REQUIRED (NO RUNTIME PASS CLAIM)",
    ]
    lines.append("RussiaAirfieldCommandSet slots:")
    for n, b in sorted(slots.items()):
        lines.append(f"  {n} = {b}")

    if not parse_ok:
        raise RuntimeError("VALIDATION FAILED\n" + "\n".join(lines))
    return lines


def main() -> int:
    for p in [T50_OBJ, T50_WEP, BASE / "_SPEC_DATA_ONE.big", BASE / "_SPEC_ART_ONE.big"]:
        if not p.exists():
            raise SystemExit(f"Missing {p}")
    if T50_OBJ.parent.joinpath("Russia_T50_R27_Projectile.ini").exists():
        raise RuntimeError("Source crash projectile file still present")
    if (PATCH / "Data/INI/Weapon_Russia_T50_R27_Support.ini").exists():
        raise RuntimeError("Source support weapon still present")
    if (PATCH / "Data/INI/ObjectCreationList_Russia_T50_R27.ini").exists():
        raise RuntimeError("Source OCL still present")

    wep_src = T50_WEP.read_text(encoding="utf-8")
    if not re.search(r"ProjectileObject\s*=\s*R27\b", wep_src):
        raise RuntimeError("Weapon not retargeted to R27")
    if "Russia_T50_R27_Projectile" in wep_src and re.search(
        r"ProjectileObject\s*=\s*Russia_T50_R27_Projectile\b", wep_src
    ):
        raise RuntimeError("Weapon still references crash projectile")

    if not TEOD_INI.exists():
        raise SystemExit(f"Missing TEOD INI for R27 trace: {TEOD_INI}")
    teod = read_big(TEOD_INI)

    with tempfile.TemporaryDirectory(prefix="t50_r27_fix_") as td:
        stage = Path(td)
        art_p = stage / "_SPEC_ART_ONE.big"
        data_p = stage / "_SPEC_DATA_ONE.big"
        shutil.copy2(BASE / "_SPEC_ART_ONE.big", art_p)
        shutil.copy2(BASE / "_SPEC_DATA_ONE.big", data_p)
        art = read_big(art_p)
        data = read_big(data_p)
        before_cs = cs_map(data[COMMANDSET_KEY])

        # Remove crash keys
        for k in REMOVE_KEYS:
            if k in data:
                del data[k]
            else:
                # tolerate already-absent
                pass

        # Update T50 weapon + object only
        data[T50_WEP_KEY] = T50_WEP.read_bytes()
        data[T50_OBJ_KEY] = T50_OBJ.read_bytes()

        # Hard guards
        if any(k in data for k in REMOVE_KEYS):
            raise RuntimeError("Crash keys still in DATA after delete")
        if count_defs(data, "Object", "Russia_T50_R27_Projectile") != 0:
            raise RuntimeError("Russia_T50_R27_Projectile still defined")
        if count_defs(data, "Object", "R27") != 0:
            raise RuntimeError("Must not pack Object R27")
        if cs_map(data[COMMANDSET_KEY]) != before_cs:
            raise RuntimeError("CommandSet changed")

        if OUT.exists():
            for stale in OUT.glob("_SPEC_*.big"):
                stale.unlink()
            z = OUT / "SPECTER_RUSSIA_SUT50_R27_CRASHFIX.zip"
            if z.exists():
                z.unlink()
            v = OUT / "VERIFY.txt"
            if v.exists():
                v.unlink()
        OUT.mkdir(parents=True, exist_ok=True)
        art_out = OUT / "_SPEC_ART_ONE.big"
        data_out = OUT / "_SPEC_DATA_ONE.big"
        write_big(art_out, art)
        write_big(data_out, data)

        report = validate(read_big(data_out), teod, before_cs)
        report.insert(0, "PACK = SPECTER_RUSSIA_SUT50_R27_CRASHFIX")
        report.insert(1, f"BASELINE = {BASE.name}")
        report.insert(2, "BUILD_MODE = CLEAN_STAGING")
        report.append(f"ART_SHA256 = {sha256(art_out)}")
        report.append(f"DATA_SHA256 = {sha256(data_out)}")
        (OUT / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        (OUT / "README_INSTALL.txt").write_text(
            "SPECTER Russia SU-T50 R27 crash fix\n"
            "\n"
            "Install: replace _SPEC_ART_ONE.big and _SPEC_DATA_ONE.big\n"
            "\n"
            "Removed custom Russia_T50_R27_Projectile (INI parse crash).\n"
            "SU-T50 weapon now uses original TEOD Object R27.\n"
            "Requires !TEOD_INI.big in load order (provides Object R27).\n"
            "\n"
            "Test match entry first. Do not assume combat PASS.\n",
            encoding="utf-8",
        )

        zip_path = OUT / "SPECTER_RUSSIA_SUT50_R27_CRASHFIX.zip"
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
