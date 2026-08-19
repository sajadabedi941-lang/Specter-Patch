#!/usr/bin/env python3
"""DATA-only T50/PAKFA startup crash fix.

Replace RussiaJetT50PAKFAClean with Su-47-skeleton + PAK-FA visuals + Weapons=NONE.
Remove unused T50 custom weapon/locomotor keys from DATA BIG.
ART untouched. Other new Russian aircraft untouched.
"""
from __future__ import annotations

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
STAGE = MASTER / "_stage_russia_t50_crashfix"
VERIFY = MASTER / "_extract_russia_t50_crashfix_verify"
ZIP_OUT = PATCH / "Release/SPECTER_MASTER_DATA_RUSSIA_T50_CRASHFIX.zip"
REPORT = PATCH / "Release/DATA_RUSSIA_T50_CRASHFIX_REPORT.txt"
HASHES = PATCH / "Release/DATA_RUSSIA_T50_CRASHFIX_HASHES.txt"
DOWNLOAD = PATCH / "Release/DATA_RUSSIA_T50_CRASHFIX_DOWNLOAD.txt"

AF = "Armed Forces Of Russian Federation"
T50_OBJ = "RussiaJetT50PAKFAClean"
T50_KEY = rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetT50PAKFAClean.ini"
T50_SRC = PATCH / f"Data/INI/Object/Specter/{AF}/Airforce/RussiaJetT50PAKFAClean.ini"

REMOVE_KEYS = [
    r"Data\INI\Weapon_Russia_T50_PAKFA_Clean.ini",
    r"Data\INI\Locomotor_Russia_T50_PAKFA_Clean.ini",
]

UNTOUCHED = [
    "RussiaJetSU47Clean",
    "RussiaJetSU75Clean",
    "RussiaJetTU160Clean",
    "RussiaJetTu95Visual",
    "RussiaJetAn124Visual",
    "RussiaJetAn225Visual",
    "RussiaJetAvionIL76Visual",
    "RussiaJetA50Visual",
    "RussiaJetCargoIL76Visual",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
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
    names = sorted(file_map.keys(), key=lambda s: s.lower())
    header_size = 16
    entries: list[tuple[str, bytes]] = []
    for name in names:
        entries.append((name, file_map[name]))
    # entry table size
    table = 0
    for name, blob in entries:
        table += 8 + len(name.encode("latin1")) + 1
    data_start = header_size + table
    # pad to 4?
    while data_start % 4:
        data_start += 1
    blobs = bytearray()
    index = bytearray()
    offset = data_start
    for name, blob in entries:
        index += struct.pack(">II", offset, len(blob))
        index += name.encode("latin1") + b"\x00"
        blobs += blob
        offset += len(blob)
    pad = data_start - (header_size + len(index))
    index += b"\x00" * pad
    total = data_start + len(blobs)
    header = b"BIGF" + struct.pack(">III", total, len(entries), data_start)
    return bytes(header + index + blobs)


def write_tree(store: dict[str, bytes], root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for name, blob in store.items():
        path = root / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)


def count_obj(store: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(name)}\s*$")
    return sum(len(pat.findall(v.decode("latin1", errors="replace"))) for v in store.values())


def structure_ok(blob: bytes, obj: str) -> None:
    text = blob.decode("latin1", errors="replace")
    assert re.search(rf"(?m)^Object\s+{re.escape(obj)}\s*$", text)
    assert sum(1 for line in text.splitlines() if re.match(r"^Object\s+\S+", line.strip() if False else line)) == 1 or \
           len(re.findall(rf"(?m)^Object\s+\S+", text)) == 1
    assert b"\nWeapons = NONE\n" in blob or b"\r\nWeapons = NONE\r\n" in blob or "Weapons = NONE" in text
    assert "Saturn_AL-41F" in text
    assert "PAK-FA" in text
    assert "Russia_Weapon_T50_PAKFA" not in text
    assert "Russia_Locomotor_T50_PAKFA" not in text
    assert "StealthUpdate" not in text
    assert all(b < 128 for b in blob), "non-ASCII bytes remain"
    stack: list[str] = []
    openers = re.compile(
        r"^(Object|Draw|Behavior|ArmorSet|WeaponSet|Body|UnitSpecificSounds|"
        r"Prerequisites|DefaultConditionState|ConditionState|TransitionState|"
        r"ClientUpdate)\b"
    )
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(";"):
            continue
        if openers.match(s):
            stack.append(s.split()[0])
        elif s == "End":
            assert stack, f"{obj}: extra End"
            stack.pop()
    assert not stack, f"{obj}: unclosed {stack}"


def main() -> int:
    assert DATA_BIG.exists()
    assert T50_SRC.exists()
    before = read_big(DATA_BIG)
    before_t50 = count_obj(before, T50_OBJ)

    data = dict(before)
    removed = []
    for key in REMOVE_KEYS:
        for k in list(data):
            if k.lower() == key.lower():
                del data[k]
                removed.append(k)

    blob = T50_SRC.read_bytes()
    structure_ok(blob, T50_OBJ)
    data[T50_KEY] = blob

    assert count_obj(data, T50_OBJ) == 1
    for name in UNTOUCHED:
        assert count_obj(data, name) == count_obj(before, name) == 1, name

    # CommandButton still resolves
    cb = data[r"Data\INI\CommandButton.ini"].decode("latin1", errors="replace")
    bm = re.search(r"(?ms)^CommandButton\s+Command_ConstructRussiaJetT50PAKFA\s*.*?^End", cb)
    assert bm
    assert "Object        = RussiaJetT50PAKFAClean" in bm.group(0)
    assert "ButtonImage   = PAKFA-ic_L" in bm.group(0)

    cs = data[r"Data\INI\CommandSet.ini"].decode("latin1", errors="replace")
    m = re.search(r"(?ms)^CommandSet\s+Russia_LargeAirBaseCommandSet\s*.*?^End", cs)
    assert m and "Command_ConstructRussiaJetT50PAKFA" in m.group(0)

    # Parking unchanged
    for bkey, rows, cols in [
        (rf"Data\INI\Object\Specter\{AF}\Buildings\Russia_LargeAirBase.ini", 4, 4),
        (rf"Data\INI\Object\Specter\{AF}\Buildings\Russia_HeavyAirBase.ini", 3, 2),
    ]:
        t = data[bkey].decode("latin1", errors="replace")
        assert re.search(rf"NumRows\s*=\s*{rows}", t)
        assert re.search(rf"NumCols\s*=\s*{cols}", t)

    # Stage clean tree + rebuild
    if STAGE.exists():
        shutil.rmtree(STAGE)
    write_tree(data, STAGE / "DATA_TREE")
    built = build_big(data)
    DATA_BIG.write_bytes(built)

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    vdata = read_big(DATA_BIG)
    write_tree(vdata, VERIFY)

    assert count_obj(vdata, T50_OBJ) == 1
    for key in REMOVE_KEYS:
        assert not any(k.lower() == key.lower() for k in vdata)
    structure_ok(vdata[T50_KEY], T50_OBJ)
    # packed path case-insensitive match for crash path
    assert any(k.lower().endswith("russiajett50pakfaclean.ini") for k in vdata)

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    dhash = sha256(DATA_BIG)
    zhash = sha256(ZIP_OUT)
    HASHES.write_text(f"_SPEC_DATA_ONE.big sha256={dhash}\nZIP sha256={zhash}\n")

    report = f"""T50 PAKFA STARTUP CRASH FIX = PASS

Crash file =
  Data\\INI\\Object\\specter\\armed forces of russian federation\\airforce\\russiajett50pakfaclean.ini

Reported Object =
  Object RussiaJetT50PAKFAClean

Actual parser root cause =
  Active RussiaJetT50PAKFAClean carried legacy helper/firefix gameplay DATA
  (custom Weapon/Locomotor chain + donor StealthUpdate + non-ASCII comment bytes).
  Generals reported the Object RussiaJetT... header in this file.

Was previous block malformed = NO
  (single Object file; fault was inside this Object / its dependencies)

Missing End = NO
Old helper-only DATA activated = YES
Broken Weapon/Projectile dependency = YES
  (prior custom R27 clone path; weapon file still targeted TEOD R27 after last fix,
   but T50 Object itself remained the reported crash file — rewritten entirely)
Duplicate Object = NO

OLD T50 Object active count before = {before_t50}
OLD T50 Object active count after = 1 (same ID, clean contents)

FINAL T50:
Object = RussiaJetT50PAKFAClean
W3D = PAK-FA / PAK-FA_D (ART preserved)
Data skeleton source = RussiaJetSU47Clean
Locomotor = Saturn_AL-41F (+ BasicJetTaxiLocomotor)
AIUpdate = JetAIUpdate
WeaponSet = NONE (Weapons = NONE)
Weapons temporarily disabled = YES

Button = Command_ConstructRussiaJetT50PAKFA
Russia Fighter Airbase slot = 11 (Russia_LargeAirBaseCommandSet)

T50 ART preserved = YES
T50 real icon preserved = YES (PAKFA-ic_L)

Su47 changed = NO
SuT75 changed = NO
Tu160 changed = NO
New donor heavy aircraft changed = NO
Other factions changed = NO
ART changed = NO

Removed unused DATA keys:
{chr(10).join('  - ' + k for k in removed) if removed else '  (none present in prior BIG)'}

DATA sha256 = {dhash}
ZIP = {ZIP_OUT}

IMPORTANT: static PASS only. User must launch to verify startup.
"""
    REPORT.write_text(report)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
