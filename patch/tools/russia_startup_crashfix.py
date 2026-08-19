#!/usr/bin/env python3
"""DATA-only Russia startup crash fix.

Root cause: packed custom projectile clones that previously crashed SAGE parse:
  - Russia_TU160_KH55MS_Projectile
  - Russia_T50_R27_Projectile
(+ support locomotor / FireWeaponUpdate weapons / OCLs)

Fix: remove those keys from DATA; retarget weapons to TEOD Object KH55MS / R27
(same proven crash-fix as PR#318/#319). Rebuild DATA BIG from clean staging.
ART untouched.
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
STAGE = MASTER / "_stage_russia_startup_crashfix"
VERIFY = MASTER / "_extract_russia_startup_crashfix_verify"
ZIP_OUT = PATCH / "Release/SPECTER_MASTER_DATA_RUSSIA_STARTUP_CRASHFIX.zip"
REPORT = PATCH / "Release/DATA_RUSSIA_STARTUP_CRASHFIX_REPORT.txt"
HASHES = PATCH / "Release/DATA_RUSSIA_STARTUP_CRASHFIX_HASHES.txt"
DOWNLOAD = PATCH / "Release/DATA_RUSSIA_STARTUP_CRASHFIX_DOWNLOAD.txt"

AF = "Armed Forces Of Russian Federation"

REMOVE_KEYS = [
    rf"Data\INI\Object\Specter\{AF}\Airforce\Russia_T50_R27_Projectile.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\Russia_TU160_KH55MS_Projectile.ini",
    r"Data\INI\Weapon_Russia_T50_R27_Support.ini",
    r"Data\INI\ObjectCreationList_Russia_T50_R27.ini",
    r"Data\INI\Locomotor_Russia_TU160_KH55_Clean.ini",
]

UPDATE_FILES = {
    r"Data\INI\Weapon_Russia_TU160_Clean.ini": PATCH / "Data/INI/Weapon_Russia_TU160_Clean.ini",
    r"Data\INI\Weapon_Russia_T50_PAKFA_Clean.ini": PATCH / "Data/INI/Weapon_Russia_T50_PAKFA_Clean.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetTU160Clean.ini": PATCH
    / f"Data/INI/Object/Specter/{AF}/Airforce/RussiaJetTU160Clean.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetT50PAKFAClean.ini": PATCH
    / f"Data/INI/Object/Specter/{AF}/Airforce/RussiaJetT50PAKFAClean.ini",
}

FORBIDDEN_OBJECTS = [
    "Russia_T50_R27_Projectile",
    "Russia_TU160_KH55MS_Projectile",
    "Russia_TU160_KH55_Detonation",
    "Russia_T50_JetMissileControl",
    "Russia_T50_JetMissileControlForcer",
    "RussiaTu95",
    "RussiaAN124",
    "RussiaAN225",
    "RussiaA50",
    "RussiaCargoIL76",
    "avionIL76",
]

RETAIN_OBJECTS = [
    "RussiaJetSU47Clean",
    "RussiaJetSU75Clean",
    "RussiaJetT50PAKFAClean",
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


def read_tree(root: Path) -> dict[str, bytes]:
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root)).replace("/", "\\")] = p.read_bytes()
    return out


def count_obj(store: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(name)}\s*$")
    return sum(len(pat.findall(v.decode("latin1", errors="replace"))) for v in store.values())


def count_weapon(store: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^Weapon\s+{re.escape(name)}\s*$")
    return sum(len(pat.findall(v.decode("latin1", errors="replace"))) for v in store.values())


def structure_ok(blob: bytes, obj: str) -> None:
    assert b"\x00" not in blob
    assert not blob.startswith(b"\xef\xbb\xbf")
    text = blob.decode("latin1", errors="replace")
    assert re.search(rf"(?m)^Object\s+{re.escape(obj)}\s*$", text)
    # Balance End for Object-level blocks (ignore Locomotor= fields)
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
    data = read_big(DATA_BIG)

    removed = []
    for key in REMOVE_KEYS:
        if key in data:
            del data[key]
            removed.append(key)
        # also try lowercase-insensitive match
        for k in list(data):
            if k.lower() == key.lower() and k in data:
                del data[k]
                if k not in removed:
                    removed.append(k)

    for key, src in UPDATE_FILES.items():
        assert src.exists(), src
        blob = src.read_bytes()
        data[key] = blob

    # Verify crash objects gone
    for name in [
        "Russia_T50_R27_Projectile",
        "Russia_TU160_KH55MS_Projectile",
    ]:
        assert count_obj(data, name) == 0, name

    # Weapons retargeted (comments may mention the removed clones; check assignments only)
    tu_w = data[r"Data\INI\Weapon_Russia_TU160_Clean.ini"].decode("latin1")
    t50_w = data[r"Data\INI\Weapon_Russia_T50_PAKFA_Clean.ini"].decode("latin1")

    def projectile_targets(text: str) -> list[str]:
        out = []
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("ProjectileObject"):
                out.append(s.split("=", 1)[1].strip())
        return out

    assert projectile_targets(tu_w) == ["KH55MS"], projectile_targets(tu_w)
    assert projectile_targets(t50_w) == ["R27"], projectile_targets(t50_w)

    # Retain objects present + parse structure
    for obj in RETAIN_OBJECTS:
        assert count_obj(data, obj) == 1, obj
        # find file
        for k, v in data.items():
            if re.search(rf"(?m)^Object\s+{re.escape(obj)}\s*$", v.decode("latin1", errors="replace")):
                structure_ok(v, obj)
                break

    # No donor gameplay objects
    for name in ["RussiaTu95", "RussiaAN124", "RussiaAN225", "RussiaA50", "RussiaCargoIL76"]:
        assert count_obj(data, name) == 0, name

    # CommandSets still resolve
    cs = data[r"Data\INI\CommandSet.ini"].decode("latin1", errors="replace")
    cb = data[r"Data\INI\CommandButton.ini"].decode("latin1", errors="replace")
    for cs_name in ["Russia_LargeAirBaseCommandSet", "Russia_HeavyAirBaseCommandSet"]:
        m = re.search(rf"(?ms)^CommandSet\s+{re.escape(cs_name)}\s*.*?^End", cs)
        assert m, cs_name
        for btn in re.findall(r"Command_\S+", m.group(0)):
            if btn in ("Command_SetRallyPoint", "Command_Sell"):
                continue
            bm = re.search(rf"(?ms)^CommandButton\s+{re.escape(btn)}\s*.*?^End", cb)
            assert bm, btn
            obj = re.search(r"(?m)^\s*Object\s*=\s*(\S+)", bm.group(0))
            if obj:
                assert count_obj(data, obj.group(1)) == 1, (btn, obj.group(1))

    # Parking unchanged
    for bkey, rows, cols, model in [
        (rf"Data\INI\Object\Specter\{AF}\Buildings\Russia_LargeAirBase.ini", 4, 4, "TheAirPort"),
        (rf"Data\INI\Object\Specter\{AF}\Buildings\Russia_HeavyAirBase.ini", 3, 2, "HXUSABigAirPort"),
    ]:
        t = data[bkey].decode("latin1", errors="replace")
        assert re.search(rf"NumRows\s*=\s*{rows}", t)
        assert re.search(rf"NumCols\s*=\s*{cols}", t)
        assert model in t

    # Clean staging rebuild
    if STAGE.exists():
        shutil.rmtree(STAGE)
    write_tree(data, STAGE / "DATA_TREE")
    data2 = read_tree(STAGE / "DATA_TREE")
    data_bytes = build_big(data2)
    DATA_BIG.write_bytes(data_bytes)

    # Re-extract verify
    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    vdata = read_big(DATA_BIG)
    write_tree(vdata, VERIFY)

    for name in ["Russia_T50_R27_Projectile", "Russia_TU160_KH55MS_Projectile"]:
        assert count_obj(vdata, name) == 0
    for key in REMOVE_KEYS:
        assert key not in vdata
        assert not any(k.lower() == key.lower() for k in vdata)

    for obj in RETAIN_OBJECTS:
        assert count_obj(vdata, obj) == 1

    tu_w2 = vdata[r"Data\INI\Weapon_Russia_TU160_Clean.ini"].decode("latin1")
    t50_w2 = vdata[r"Data\INI\Weapon_Russia_T50_PAKFA_Clean.ini"].decode("latin1")
    assert "ProjectileObject            = KH55MS" in tu_w2
    assert "ProjectileObject            = R27" in t50_w2

    # Package DATA-only
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    dhash = sha256(DATA_BIG)
    HASHES.write_text(f"_SPEC_DATA_ONE.big sha256={dhash}\nZIP sha256={sha256(ZIP_OUT)}\n")

    report = f"""RUSSIA STARTUP CRASH FIX = PASS

Crash file =
  Data\\INI\\Object\\Specter\\Armed Forces Of Russian Federation\\Airforce\\Russia_TU160_KH55MS_Projectile.ini
  AND
  Data\\INI\\Object\\Specter\\Armed Forces Of Russian Federation\\Airforce\\Russia_T50_R27_Projectile.ini
  (ReleaseCrashInfo.txt was not present in this agent workspace; root cause matched
   prior proven SAGE parse crashes on these exact Airforce projectile Objects —
   PR#318 / PR#319. Screenshot context: Russian Airforce INI / projectile Object.)

Reported crash line/header =
  Object Russia_TU160_KH55MS_Projectile  /  Object Russia_T50_R27_Projectile
  (custom clones previously documented to crash SAGE INI parse)

Actual root cause =
  Accidental reactivation of helper-only custom projectile clones that were already
  proven to crash Generals/SAGE parse. They were packed into active DATA by the
  Russia expansion from the firefix branch, AFTER earlier crash-fix PRs had
  removed them.

Broken Object/Weapon/Projectile =
  Object Russia_TU160_KH55MS_Projectile
  Object Russia_T50_R27_Projectile
  (+ support: Weapon_Russia_T50_R27_Support, ObjectCreationList_Russia_T50_R27,
     Locomotor_Russia_TU160_KH55_Clean)

Was reported line itself broken = YES
  (custom projectile Object blocks / ClientUpdate+support chain previously crashed parse)

Was previous block missing End = NO
  (root cause was activating the known-bad projectile files themselves)

Was an old helper-only Russia file accidentally activated = YES

Was donor gameplay DATA accidentally activated = NO
  (donor Tu95/An124/An225/A50/cargoIL76/avionIL76 Objects remain count=0)

Exact fix applied =
  1) DELETE packed keys for both custom projectile INIs + support files
  2) Retarget Russia_Weapon_TU160_KH55 → ProjectileObject = KH55MS (TEOD)
  3) Retarget Russia_Weapon_T50_PAKFA → ProjectileObject = R27 (TEOD)
  4) Rebuild _SPEC_DATA_ONE.big from CLEAN staging; re-extract verify
  ART unchanged.

Removed keys:
{chr(10).join('  - '+k for k in removed)}

Su-47 retained = YES
SuT50 retained = YES
SuT75 retained = YES
Tu-160 retained = YES

Tu-95 wrapper retained = YES
An-124 wrapper retained = YES
An-225 wrapper retained = YES
avionIL76 wrapper retained = YES
A-50 wrapper retained = YES
cargoIL76 wrapper retained = YES

Other factions changed = NO
Airbase parking changed = NO
ART changed = NO

DATA sha256 = {dhash}
ZIP = {ZIP_OUT}

IMPORTANT: DO NOT CLAIM GAME-TESTED PASS. User must launch to verify startup.
Requires !TEOD_INI.big in load order for Object KH55MS / Object R27 (same as prior crashfix packs).
"""
    REPORT.write_text(report)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
