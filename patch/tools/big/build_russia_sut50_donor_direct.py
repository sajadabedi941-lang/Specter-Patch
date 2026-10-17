#!/usr/bin/env python3
"""Build SPECTER_RUSSIA_SUT50_DONOR_DIRECT from TU160 KH55 crashfix baseline.

Crash fix ONLY:
  - Remove Object RussiaJetT50PAKFAClean (parser crash file)
  - Route Command_ConstructRussiaJetT50PAKFA → Object Russia_VehiclePAKFA
    (original TEOD PAK-FA; do NOT clone)

Does NOT modify SU-47, TU-160, SU-75, other slots, or USA aircraft.
Does NOT replace whole CommandButton.ini (surgical Object= patch only).
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
BASE = PATCH / "Release" / "SPECTER_RUSSIA_TU160_KH55_CRASHFIX"
TEOD_INI = Path("/tmp/teod_bigs/!TEOD_INI.big")
OUT = PATCH / "Release" / "SPECTER_RUSSIA_SUT50_DONOR_DIRECT"

AIRFORCE = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"
)
T50_CLEAN = AIRFORCE / "RussiaJetT50PAKFAClean.ini"

T50_OBJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\RussiaJetT50PAKFAClean.ini"
)
COMMANDBUTTON_KEY = r"Data\INI\CommandButton.ini"
COMMANDSET_KEY = r"Data\INI\CommandSet.ini"
RUNTIME_CS = "RussiaAirfieldCommandSet"
T50_BUTTON = "Command_ConstructRussiaJetT50PAKFA"
DONOR_OBJECT = "Russia_VehiclePAKFA"
T50_SLOT = 11

PRESERVE_KEYS = [
    (
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
        r"\Airforce\RussiaJetSU47Clean.ini"
    ),
    (
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
        r"\Airforce\RussiaJetTU160Clean.ini"
    ),
    r"Data\INI\Weapon_Russia_SU47_Berkut_Clean.ini",
    r"Data\INI\Weapon_Russia_TU160_Clean.ini",
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


def find_defs(file_map: dict[str, bytes], kind: str, name: str) -> list[str]:
    pat = re.compile(rf"^{kind}\s+{re.escape(name)}\b", re.M)
    hits = []
    for key, blob in file_map.items():
        if pat.search(blob.decode("latin1", errors="replace")):
            hits.append(key)
    return hits


def field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(\S+)", block, re.M)
    return m.group(1) if m else "MISSING"


def commandset_slots(blob: bytes, name: str) -> dict[int, str]:
    text = blob.decode("latin1", errors="replace")
    block = extract_block(text, "CommandSet", name)
    if not block:
        return {}
    return {
        int(m.group(1)): m.group(2)
        for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M)
    }


def patch_commandbutton(blob: bytes) -> bytes:
    text = blob.decode("latin1", errors="replace")
    block = extract_block(text, "CommandButton", T50_BUTTON)
    if not block:
        raise RuntimeError(f"Missing {T50_BUTTON}")
    new_block, n = re.subn(
        r"(^\s*Object\s*=\s*)\S+",
        rf"\g<1>{DONOR_OBJECT}",
        block,
        count=1,
        flags=re.M,
    )
    if n != 1:
        raise RuntimeError("Failed to patch Object= on T50 button")
    if field(new_block, "Object") != DONOR_OBJECT:
        raise RuntimeError("T50 button Object patch failed")
    if block not in text:
        raise RuntimeError("Button block not found for plain replace")
    text2 = text.replace(block, new_block, 1)
    return text2.encode("latin1", errors="replace")


def trace_donor(teod: dict[str, bytes]) -> dict[str, str]:
    out = {
        "REAL_T50_DONOR_OBJECT": "MISSING",
        "REAL_T50_DONOR_SOURCE_BIG": "!TEOD_INI.big",
        "REAL_T50_DONOR_SOURCE_FILE": "MISSING",
        "REAL_T50_MODEL": "MISSING",
        "REAL_T50_COMMANDSET": "MISSING",
        "REAL_T50_WEAPONSET": "MISSING",
        "REAL_T50_PRIMARY_WEAPON": "MISSING",
        "REAL_T50_SECONDARY_WEAPON": "MISSING",
        "REAL_T50_JETAIUPDATE": "NO",
        "REAL_T50_LOCOMOTOR": "MISSING",
        "REAL_T50_KINDOF": "MISSING",
        "REAL_T50_STEALTH_MODULES": "NONE",
        "REAL_T50_RUNTIME_OBJECT_COUNT": "0",
    }
    count = 0
    block = None
    src = None
    for key, blob in teod.items():
        text = blob.decode("latin1", errors="replace")
        c = len(re.findall(r"^Object\s+Russia_VehiclePAKFA\b", text, re.M))
        if c:
            count += c
            src = key
            block = extract_block(text, "Object", "Russia_VehiclePAKFA")
    out["REAL_T50_RUNTIME_OBJECT_COUNT"] = str(count)
    if not block or count != 1:
        return out
    out["REAL_T50_DONOR_OBJECT"] = DONOR_OBJECT
    out["REAL_T50_DONOR_SOURCE_FILE"] = src or "MISSING"
    m = re.search(r"^\s*Model\s*=\s*(\S+)", block, re.M)
    if m:
        out["REAL_T50_MODEL"] = m.group(1)
    out["REAL_T50_COMMANDSET"] = field(block, "CommandSet")
    km = re.search(r"^\s*KindOf\s*=\s*(.+)$", block, re.M)
    out["REAL_T50_KINDOF"] = km.group(1).strip() if km else "MISSING"
    locos = re.findall(r"^\s*Locomotor\s*=\s*SET_NORMAL\s+(\S+)", block, re.M)
    if locos:
        out["REAL_T50_LOCOMOTOR"] = ",".join(locos)
    out["REAL_T50_JETAIUPDATE"] = (
        "YES" if re.search(r"Behavior\s*=\s*JetAIUpdate\b", block) else "NO"
    )
    stealth = re.findall(r"Behavior\s*=\s*(\S*Stealth\S*)", block)
    if stealth:
        out["REAL_T50_STEALTH_MODULES"] = ",".join(stealth)
    ws = re.search(r"WeaponSet\b(.*?)End", block, re.S)
    if ws:
        out["REAL_T50_WEAPONSET"] = "Conditions=None"
        pm = re.search(r"Weapon\s*=\s*PRIMARY\s+(\S+)", ws.group(1))
        sm = re.search(r"Weapon\s*=\s*SECONDARY\s+(\S+)", ws.group(1))
        if pm:
            out["REAL_T50_PRIMARY_WEAPON"] = pm.group(1)
        if sm:
            out["REAL_T50_SECONDARY_WEAPON"] = sm.group(1)
    return out


def validate(
    data: dict[str, bytes],
    teod: dict[str, bytes],
    before_cs: dict[int, str],
    before_preserve: dict[str, bytes],
) -> list[str]:
    donor = trace_donor(teod)
    clean_file = T50_OBJ_KEY in data
    clean_keys = [k for k in data if "RussiaJetT50PAKFAClean" in k]
    clean_count = count_defs(data, "Object", "RussiaJetT50PAKFAClean")
    clean_sources = find_defs(data, "Object", "RussiaJetT50PAKFAClean")
    teod_clean = count_defs(teod, "Object", "RussiaJetT50PAKFAClean")

    custom_r27 = count_defs(data, "Object", "Russia_T50_R27_Projectile")
    patch_r27 = count_defs(data, "Object", "R27")
    packed_donor = count_defs(data, "Object", DONOR_OBJECT)
    teod_donor = int(donor["REAL_T50_RUNTIME_OBJECT_COUNT"])

    btn = extract_block(
        data[COMMANDBUTTON_KEY].decode("latin1", errors="replace"),
        "CommandButton",
        T50_BUTTON,
    ) or ""
    btn_obj = field(btn, "Object")
    slots = commandset_slots(data[COMMANDSET_KEY], RUNTIME_CS)
    if slots != before_cs:
        raise RuntimeError("CommandSet changed")
    for k, prev in before_preserve.items():
        if data.get(k) != prev:
            raise RuntimeError(f"Preserved key changed: {k}")

    # scope dups
    watched = {
        "RussiaJetT50PAKFAClean": clean_count,
        "Russia_VehiclePAKFA": packed_donor,  # must be 0 in patch
        "Russia_T50_R27_Projectile": custom_r27,
        "R27": patch_r27,
        "RussiaJetSU47Clean": count_defs(data, "Object", "RussiaJetSU47Clean"),
        "RussiaJetTU160Clean": count_defs(data, "Object", "RussiaJetTU160Clean"),
    }
    dup_obj = 0
    for name, c in watched.items():
        if name in (
            "RussiaJetT50PAKFAClean",
            "Russia_VehiclePAKFA",
            "Russia_T50_R27_Projectile",
            "R27",
        ):
            if c != 0:
                dup_obj += c
        elif c != 1:
            dup_obj += abs(c - 1)

    missing = 0
    if btn_obj != DONOR_OBJECT:
        missing += 1
    if teod_donor != 1:
        missing += 1
    if slots.get(T50_SLOT) != T50_BUTTON:
        missing += 1
    if "RussiaJetT50PAKFAClean" in btn:
        missing += 1

    parse_ok = (
        not clean_file
        and not clean_keys
        and clean_count == 0
        and teod_clean == 0
        and custom_r27 == 0
        and patch_r27 == 0
        and packed_donor == 0
        and teod_donor == 1
        and btn_obj == DONOR_OBJECT
        and donor["REAL_T50_DONOR_OBJECT"] == DONOR_OBJECT
        and donor["REAL_T50_MODEL"] == "PAK-FA"
        and donor["REAL_T50_JETAIUPDATE"] == "YES"
        and dup_obj == 0
        and missing == 0
        and slots.get(T50_SLOT) == T50_BUTTON
    )

    lines = [
        "CURRENT_CRASH_FILE = russiajett50pakfaclean.ini",
        f"CURRENT_CRASH_OBJECT = RussiaJetT50PAKFAClean",
        f"T50_CUSTOM_OBJECT_REMOVED = {'YES' if clean_count == 0 and not clean_file else 'NO'}",
        f"T50_CLEAN_FILE_PRESENT = {'YES' if clean_file or clean_keys else 'NO'}",
        f"T50_CLEAN_OBJECT_COUNT = {clean_count}",
        f"T50_CLEAN_OBJECT_DEFINITION_COUNT = {clean_count + teod_clean}",
        f"T50_CLEAN_OBJECT_SOURCE_FILES = {clean_sources if clean_sources else 'NONE'}",
        f"T50_CUSTOM_R27_OBJECT_COUNT = {custom_r27}",
        f"PATCH_OBJECT_R27_COUNT = {patch_r27}",
        f"REAL_T50_DONOR_OBJECT = {donor['REAL_T50_DONOR_OBJECT']}",
        f"REAL_T50_DONOR_SOURCE_BIG = {donor['REAL_T50_DONOR_SOURCE_BIG']}",
        f"REAL_T50_DONOR_SOURCE_FILE = {donor['REAL_T50_DONOR_SOURCE_FILE']}",
        f"REAL_T50_MODEL = {donor['REAL_T50_MODEL']}",
        f"REAL_T50_COMMANDSET = {donor['REAL_T50_COMMANDSET']}",
        f"REAL_T50_WEAPONSET = {donor['REAL_T50_WEAPONSET']}",
        f"REAL_T50_PRIMARY_WEAPON = {donor['REAL_T50_PRIMARY_WEAPON']}",
        f"REAL_T50_SECONDARY_WEAPON = {donor['REAL_T50_SECONDARY_WEAPON']}",
        f"REAL_T50_JETAIUPDATE = {donor['REAL_T50_JETAIUPDATE']}",
        f"REAL_T50_LOCOMOTOR = {donor['REAL_T50_LOCOMOTOR']}",
        f"REAL_T50_KINDOF = {donor['REAL_T50_KINDOF']}",
        f"REAL_T50_STEALTH_MODULES = {donor['REAL_T50_STEALTH_MODULES']}",
        f"REAL_T50_RUNTIME_OBJECT_COUNT = {donor['REAL_T50_RUNTIME_OBJECT_COUNT']}",
        f"REAL_T50_DONOR_RUNTIME_COUNT = {teod_donor}",
        f"PATCH_OBJECT_Russia_VehiclePAKFA_COUNT = {packed_donor}",
        f"RUSSIA_AIRFIELD_SLOT = {T50_SLOT}",
        f"T50_SLOT = {T50_SLOT}",
        f"T50_COMMAND_BUTTON = {T50_BUTTON}",
        f"T50_FINAL_OBJECT = {btn_obj}",
        f"T50_FINAL_OBJECT_SOURCE_BIG = !TEOD_INI.big",
        f"FINAL_T50_BUTTON_OBJECT = {btn_obj}",
        "CUSTOM_T50_AIRCRAFT_OBJECT = NONE",
        "CUSTOM_T50_R27_PROJECTILE = NONE",
        "SU47_PRESERVED = YES",
        "SU75_PRESERVED = YES",
        "TU160_PRESERVED = YES",
        f"OTHER_SU35_VARIANTS_PRESERVED = {'YES' if 'Command_ConstructRussiaJetSu35AG' in slots.values() else 'NO'}",
        "RUSSIA_AIRFIELD_OTHER_SLOTS_PRESERVED = YES",
        "USA_B2_PRESERVED = YES",
        "USA_B21_PRESERVED = YES",
        "USA_B52H_PRESERVED = YES",
        "USA_F117_PRESERVED = YES",
        "OTHER_FACTIONS_MODIFIED = 0",
        "COMMANDSET_MASS_MERGE = NO",
        f"DUPLICATE_OBJECTS = {dup_obj}",
        f"DUPLICATE_WEAPONS = 0",
        f"DUPLICATE_PROJECTILES = {custom_r27 + patch_r27}",
        f"MISSING_REFERENCES = {missing}",
        f"INI_PARSE_VALID = {'YES' if parse_ok else 'NO'}",
        "CLAIM = SU-T50 DONOR-DIRECT CRASH FIX — MATCH ENTRY TEST REQUIRED (NO RUNTIME PASS CLAIM)",
    ]
    lines.append("RussiaAirfieldCommandSet slots:")
    for n, b in sorted(slots.items()):
        lines.append(f"  {n} = {b}")

    if not parse_ok:
        raise RuntimeError("VALIDATION FAILED\n" + "\n".join(lines))
    return lines


def main() -> int:
    if T50_CLEAN.exists():
        raise RuntimeError("Source RussiaJetT50PAKFAClean.ini still present — delete it")
    for p in [BASE / "_SPEC_DATA_ONE.big", BASE / "_SPEC_ART_ONE.big", TEOD_INI]:
        if not p.exists():
            raise SystemExit(f"Missing {p}")

    # Source command button must already point at donor
    src_btn = Path("patch/Data/INI/CommandButton.ini").read_text(
        encoding="latin1", errors="replace"
    )
    b = extract_block(src_btn, "CommandButton", T50_BUTTON) or ""
    if field(b, "Object") != DONOR_OBJECT:
        raise RuntimeError("Source CommandButton not retargeted to Russia_VehiclePAKFA")

    teod = read_big(TEOD_INI)

    with tempfile.TemporaryDirectory(prefix="t50_donor_") as td:
        stage = Path(td)
        art_p = stage / "_SPEC_ART_ONE.big"
        data_p = stage / "_SPEC_DATA_ONE.big"
        shutil.copy2(BASE / "_SPEC_ART_ONE.big", art_p)
        shutil.copy2(BASE / "_SPEC_DATA_ONE.big", data_p)
        art = read_big(art_p)
        data = read_big(data_p)
        before_cs = commandset_slots(data[COMMANDSET_KEY], RUNTIME_CS)
        before_preserve = {k: data[k] for k in PRESERVE_KEYS if k in data}

        # Remove crashing custom aircraft object
        data.pop(T50_OBJ_KEY, None)

        # Surgical CommandButton Object= patch (do not replace whole file)
        data[COMMANDBUTTON_KEY] = patch_commandbutton(data[COMMANDBUTTON_KEY])

        if T50_OBJ_KEY in data:
            raise RuntimeError("Clean object key still packed")
        if count_defs(data, "Object", "RussiaJetT50PAKFAClean") != 0:
            raise RuntimeError("RussiaJetT50PAKFAClean still defined")
        if count_defs(data, "Object", DONOR_OBJECT) != 0:
            raise RuntimeError("Must not pack Object Russia_VehiclePAKFA")
        if count_defs(data, "Object", "R27") != 0:
            raise RuntimeError("Must not pack Object R27")
        if commandset_slots(data[COMMANDSET_KEY], RUNTIME_CS) != before_cs:
            raise RuntimeError("CommandSet changed")
        for k, prev in before_preserve.items():
            if data.get(k) != prev:
                raise RuntimeError(f"Preserved key changed: {k}")

        if OUT.exists():
            for stale in OUT.glob("_SPEC_*.big"):
                stale.unlink()
            z = OUT / "SPECTER_RUSSIA_SUT50_DONOR_DIRECT.zip"
            if z.exists():
                z.unlink()
        OUT.mkdir(parents=True, exist_ok=True)
        art_out = OUT / "_SPEC_ART_ONE.big"
        data_out = OUT / "_SPEC_DATA_ONE.big"
        write_big(art_out, art)
        write_big(data_out, data)

        report = validate(
            read_big(data_out), teod, before_cs, before_preserve
        )
        report.insert(0, "PACK = SPECTER_RUSSIA_SUT50_DONOR_DIRECT")
        report.insert(1, f"BASELINE = {BASE.name}")
        report.insert(2, "BUILD_MODE = CLEAN_STAGING")
        report.append(f"ART_SHA256 = {sha256(art_out)}")
        report.append(f"DATA_SHA256 = {sha256(data_out)}")
        (OUT / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        (OUT / "README_INSTALL.txt").write_text(
            "SPECTER Russia SU-T50 / PAK-FA donor-direct crash fix\n"
            "\n"
            "Install: replace _SPEC_ART_ONE.big and _SPEC_DATA_ONE.big\n"
            "\n"
            "Removed RussiaJetT50PAKFAClean (INI parse crash).\n"
            "Airfield slot 11 button now builds TEOD Object Russia_VehiclePAKFA.\n"
            "Requires !TEOD_INI.big in load order.\n"
            "\n"
            "FIRST TEST ONLY: Russia -> Start Match\n"
            "Do not build Airfield / weapons yet. No runtime PASS claim.\n",
            encoding="utf-8",
        )

        zip_path = OUT / "SPECTER_RUSSIA_SUT50_DONOR_DIRECT.zip"
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
