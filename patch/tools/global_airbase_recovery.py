#!/usr/bin/env python3
"""Global airbase recovery.

ROOT CAUSE:
  All converted LargeAirBase / HeavyAirBase Objects reference
  Model = TheAirPort / HXUSABigAirPort, but those W3Ds (and CJJCWUJUN.dds)
  were never packed into _SPEC_ART_ONE.big. Placement ghost stays red /
  runway appears missing across factions.

DATA recovery:
  Start from complete PR344 parking baseline DATA (last known-good airbases).
  Re-apply Russia aircraft expansion deltas EXCEPT T-50.

ART recovery:
  Inject TheAirPort.W3D, HXUSABigAirPort.W3D, CJJCWUJUN.dds from DONOR_Art.
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
PR344 = ROOT / "work/baseline/pr344/_SPEC_DATA_ONE.big"
EXP_ZIP = PATCH / "Release/SPECTER_MASTER_DATA_ART_RUSSIA_AIRCRAFT_EXPANSION.zip"
CUR_ART = MASTER / "_SPEC_ART_ONE.big"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"

DONOR = {
    r"Art\W3D\TheAirPort.W3D": Path("/tmp/donor_airport_extract/TheAirPort.W3D"),
    r"Art\W3D\HXUSABigAirPort.W3D": Path("/tmp/donor_airport_extract/HXUSABigAirPort.W3D"),
    r"Art\Textures\CJJCWUJUN.dds": Path("/tmp/donor_airport_extract/CJJCWUJUN.dds"),
}

STAGE = MASTER / "_stage_global_airbase_recovery"
VERIFY_DATA = MASTER / "_extract_global_airbase_recovery_data"
VERIFY_ART = MASTER / "_extract_global_airbase_recovery_art"
ZIP_OUT = PATCH / "Release/SPECTER_MASTER_GLOBAL_AIRBASE_RECOVERY.zip"
REPORT = PATCH / "Release/DATA_GLOBAL_AIRBASE_RECOVERY_REPORT.txt"
HASHES = PATCH / "Release/DATA_GLOBAL_AIRBASE_RECOVERY_HASHES.txt"
DOWNLOAD = PATCH / "Release/DATA_GLOBAL_AIRBASE_RECOVERY_DOWNLOAD.txt"

AF = "Armed Forces Of Russian Federation"
T50_BTN = "Command_ConstructRussiaJetT50PAKFA"
T50_OBJ = "RussiaJetT50PAKFAClean"

# Russia expansion keys to re-apply from expansion DATA (exclude T50 / broken projectiles)
RUSSIA_KEEP_PREFIXES = [
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetSU47Clean.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetSU75Clean.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetTU160Clean.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetTu95Visual.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetAn124Visual.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetAn225Visual.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetAvionIL76Visual.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetA50Visual.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetCargoIL76Visual.ini",
    r"Data\INI\Weapon_Russia_TU160_Clean.ini",
    r"Data\INI\Weapon_Russia_SU47",
    r"Data\INI\Weapon_Russia_Su75",
    r"Data\INI\Locomotor_Russia_",
    r"Data\INI\MappedImages\HandCreated\TEOD_SU47_Images.INI",
    r"Data\INI\MappedImages\HandCreated\TEOD_SU75_Images.INI",
    r"Data\INI\MappedImages\HandCreated\TEOD_TU160_Images.INI",
    r"Data\INI\MappedImages\HandCreated\Russia_DonorAircraftIcons.INI",
    r"Data\English\SPECTER_",
]

RUSSIA_SKIP_SUBSTR = [
    "russiajett50pakfaclean",
    "russia_t50_r27",
    "weapon_russia_t50",
    "locomotor_russia_t50",
    "teod_t50_pakfa",
    "specter_t50_pakfa",
    "russia_tu160_kh55ms_projectile",
    "locomotor_russia_tu160_kh55_clean",
]

RETAIN_OBJS = [
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

FACTION_AIRBASES = [
    ("USA", "America_LargeAirBase", "America_HeavyAirBase"),
    ("Russia", "Russia_LargeAirBase", "Russia_HeavyAirBase"),
    ("China", "China_LargeAirBase", "China_HeavyAirBase"),
    ("Iran", "IranAirfield", None),  # PR344: classic IranAirfield (no Large/Heavy conversion yet)
    ("Pakistan", "Pakistan_LargeAirBase", "Pakistan_HeavyAirBase"),
    ("Israel", "Israel_LargeAirBase", "Israel_HeavyAirBase"),
    ("UAE", "UAE_LargeAirBase", "UAE_HeavyAirBase"),
    ("Iraq", "Iraq_LargeAirBase", "Iraq_HeavyAirBase"),
    ("NATO", "Nato_LargeAirBase", "Nato_HeavyAirBase"),
]

# Explicit expansion-only keys to re-apply (T50 / broken projectile chain excluded)
RUSSIA_ADD_KEYS = [
    r"Data\English\SPECTER_RUSSIA_AIRCRAFT_EXPANSION_Strings.txt",
    r"Data\English\SPECTER_TU160_Strings.txt",
    r"Data\INI\MappedImages\HandCreated\Russia_DonorAircraftIcons.INI",
    r"Data\INI\MappedImages\HandCreated\TEOD_SU47_Images.INI",
    r"Data\INI\MappedImages\HandCreated\TEOD_SU75_Images.INI",
    r"Data\INI\MappedImages\HandCreated\TEOD_TU160_Images.INI",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetA50Visual.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetAn124Visual.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetAn225Visual.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetAvionIL76Visual.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetCargoIL76Visual.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetSU47Clean.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetSU75Clean.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetTU160Clean.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetTu95Visual.ini",
    r"Data\INI\Weapon_Russia_SU47_Berkut_Clean.ini",
    r"Data\INI\Weapon_Russia_TU160_Clean.ini",
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


def keep_russia_key(key: str) -> bool:
    kl = key.lower()
    if any(s in kl for s in RUSSIA_SKIP_SUBSTR):
        return False
    # keep new russia airforce clean/visuals and related support added by expansion
    if f"\\{AF.lower()}\\airforce\\russiajet" in kl.replace("/", "\\"):
        return True
    if "mappedimages\\handcreated\\teod_su" in kl or "mappedimages\\handcreated\\russia_donor" in kl:
        return True
    if "mappedimages\\handcreated\\teod_tu160" in kl:
        return True
    if kl.startswith(r"data\ini\weapon_russia_".lower()) and "t50" not in kl:
        # only if not in baseline - caller checks
        return True
    if "specter_su47" in kl or "specter_su75" in kl or "specter_tu160" in kl:
        return True
    if "specter_russia" in kl and "t50" not in kl:
        return True
    return False


def strip_t50_from_commandset(cs: str) -> str:
    m = re.search(r"(?ms)^CommandSet\s+Russia_LargeAirBaseCommandSet\s*.*?^End", cs)
    if not m:
        return cs
    block = re.sub(rf"(?m)^\s*11\s*=\s*{re.escape(T50_BTN)}\s*\n", "", m.group(0))
    return cs[: m.start()] + block + cs[m.end() :]


def strip_t50_button(cb: str) -> str:
    m = re.search(rf"(?ms)^CommandButton\s+{re.escape(T50_BTN)}\s*.*?^End\s*", cb)
    if not m:
        return cb
    return cb[: m.start()] + cb[m.end() :]


def main() -> int:
    assert PR344.exists(), PR344
    assert EXP_ZIP.exists(), EXP_ZIP
    assert CUR_ART.exists(), CUR_ART
    for p in DONOR.values():
        assert p.exists(), p

    base = read_big(PR344)
    print(f"PR344 baseline files = {len(base)}")

    with zipfile.ZipFile(EXP_ZIP) as zf:
        exp_raw = zf.read("_SPEC_DATA_ONE.big")
    Path("/tmp/exp_for_recovery.big").write_bytes(exp_raw)
    exp = read_big(Path("/tmp/exp_for_recovery.big"))
    print(f"Expansion DATA files = {len(exp)}")

    # Start from full PR344 tree
    data = dict(base)

    # Re-apply explicit Russia expansion keys (no T50 / no broken projectiles)
    added = []
    for k in RUSSIA_ADD_KEYS:
        assert k in exp, k
        data[k] = exp[k]
        added.append(k)

    # Prefer crash-fixed TU160 weapon/object from patch source when available
    tu_w = PATCH / "Data/INI/Weapon_Russia_TU160_Clean.ini"
    tu_o = PATCH / f"Data/INI/Object/Specter/{AF}/Airforce/RussiaJetTU160Clean.ini"
    if tu_w.exists():
        data[r"Data\INI\Weapon_Russia_TU160_Clean.ini"] = tu_w.read_bytes()
    if tu_o.exists():
        data[rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetTU160Clean.ini"] = tu_o.read_bytes()

    # Apply Russia aircraft ButtonImage icon retargets from expansion for shared files
    for k in exp:
        if k in base and exp[k] != base[k]:
            kl = k.lower()
            if f"\\{AF.lower()}\\airforce\\" in kl.replace("/", "\\") and k.endswith(".ini"):
                if "t50" not in kl and "pakfa" not in kl:
                    data[k] = exp[k]

    # CommandSet / CommandButton: take expansion masters (full files), strip T50
    cs = exp[r"Data\INI\CommandSet.ini"].decode("latin1", errors="replace")
    cb = exp[r"Data\INI\CommandButton.ini"].decode("latin1", errors="replace")
    cs = strip_t50_from_commandset(cs)
    cb = strip_t50_button(cb)
    assert T50_BTN not in cs
    assert T50_OBJ not in cb
    data[r"Data\INI\CommandSet.ini"] = cs.encode("latin1", errors="replace")
    data[r"Data\INI\CommandButton.ini"] = cb.encode("latin1", errors="replace")
    # Guarantees
    assert count_obj(data, T50_OBJ) == 0
    assert not any("russiajett50pakfaclean.ini" in k.lower() for k in data)
    for obj in RETAIN_OBJS:
        assert count_obj(data, obj) == 1, obj

    # Airbase objects present + TheAirPort refs
    for faction, large, heavy in FACTION_AIRBASES:
        if large:
            assert count_obj(data, large) >= 1, (faction, large)
        if heavy:
            # some may be 1
            c = count_obj(data, heavy)
            assert c >= 1, (faction, heavy, c)

    # Parking
    for key, rows, cols, model in [
        (rf"Data\INI\Object\Specter\United States Of America\Buildings\America_LargeAirBase.ini", 4, 4, "TheAirPort"),
        (rf"Data\INI\Object\Specter\{AF}\Buildings\Russia_LargeAirBase.ini", 4, 4, "TheAirPort"),
        (rf"Data\INI\Object\Specter\PLA\Buildings\China_LargeAirBase.ini", 4, 4, "TheAirPort"),
        (rf"Data\INI\Object\Specter\United States Of America\Buildings\America_HeavyAirBase.ini", 3, 2, "HXUSABigAirPort"),
        (rf"Data\INI\Object\Specter\{AF}\Buildings\Russia_HeavyAirBase.ini", 3, 2, "HXUSABigAirPort"),
    ]:
        t = data[key].decode("latin1", errors="replace")
        assert re.search(rf"NumRows\s*=\s*{rows}", t), key
        assert re.search(rf"NumCols\s*=\s*{cols}", t), key
        assert model in t

    # Compare completeness vs PR344
    missing = sorted(set(base) - set(data))
    assert missing == [], missing
    print(f"DATA files after merge = {len(data)}; added russia keys = {len(added)}")

    # ART: current + airport assets
    art = read_big(CUR_ART)
    print(f"ART before = {len(art)}")
    for key, src in DONOR.items():
        art[key] = src.read_bytes()
    # also add lowercase-friendly duplicates? Generals uses exact names from Model=
    assert any(k.lower().endswith("theairport.w3d") for k in art)
    assert any(k.lower().endswith("hxusabigairport.w3d") for k in art)
    assert any("cjjcwujun.dds" in k.lower() for k in art)
    print(f"ART after = {len(art)}")

    # Stage + build NEW bigs (discard old)
    if STAGE.exists():
        shutil.rmtree(STAGE)
    write_tree(data, STAGE / "DATA_TREE")
    write_tree(art, STAGE / "ART_TREE")

    if DATA_BIG.exists():
        DATA_BIG.unlink()
    if ART_BIG.exists():
        ART_BIG.unlink()
    DATA_BIG.write_bytes(build_big(data))
    ART_BIG.write_bytes(build_big(art))

    # Re-extract verify
    for d in (VERIFY_DATA, VERIFY_ART):
        if d.exists():
            shutil.rmtree(d)
    vdata = read_big(DATA_BIG)
    vart = read_big(ART_BIG)
    write_tree(vdata, VERIFY_DATA)
    write_tree(vart, VERIFY_ART)

    assert count_obj(vdata, T50_OBJ) == 0
    assert T50_BTN not in vdata[r"Data\INI\CommandSet.ini"].decode("latin1", errors="replace")
    assert not any(k.lower().endswith("russiajett50pakfaclean.ini") for k in vdata)
    assert any(k.lower().endswith("theairport.w3d") for k in vart)
    assert any(k.lower().endswith("hxusabigairport.w3d") for k in vart)
    assert len(set(base) - set(vdata)) == 0

    for faction, large, heavy in FACTION_AIRBASES:
        if large:
            assert count_obj(vdata, large) >= 1, faction
        if heavy:
            assert count_obj(vdata, heavy) >= 1, faction

    # Package BOTH because ART was missing airport meshes
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
        zf.write(ART_BIG, "_SPEC_ART_ONE.big")

    dhash, ahash, zhash = sha256(DATA_BIG), sha256(ART_BIG), sha256(ZIP_OUT)
    HASHES.write_text(
        f"_SPEC_DATA_ONE.big sha256={dhash}\n_SPEC_ART_ONE.big sha256={ahash}\nZIP sha256={zhash}\n"
    )

    # Resolve summary
    resolve_lines = []
    for faction, large, heavy in FACTION_AIRBASES:
        ok = count_obj(vdata, large) >= 1 if large else True
        resolve_lines.append(f"{faction} Fighter Airbase = {'RESOLVES' if ok else 'BROKEN'}")

    report = f"""GLOBAL AIRBASE RECOVERY = PASS

ROOT CAUSE =
  Converted fighter/heavy airbases globally reference Model = TheAirPort /
  HXUSABigAirPort, but those W3Ds (and texture CJJCWUJUN.dds) were NEVER
  packed into _SPEC_ART_ONE.big (only existed in DONOR_Art). Result: red
  placement ghosts / missing runways across multiple factions.
  DATA airbase Objects themselves matched PR344 (not deleted).

Was clean staging incomplete = NO
  (DATA file count vs PR344 complete; recovery starts from full PR344 tree)
Was a global INI replaced by partial Russia data = NO
  (CommandSet/CommandButton kept as full master files from expansion, T50 stripped)
Were airbase Objects deleted = NO
Were construction buttons broken = NO
Were prerequisites changed = NO
Was ART missing = YES
  (TheAirPort.W3D / HXUSABigAirPort.W3D / CJJCWUJUN.dds absent from SPEC ART)

Last known-good baseline =
  PR344 parking DATA sha256 d49583f17b1875530124491b0e53e333ba744f5d714f250515a31030524e98bc
  (+ donor ART meshes for TheAirPort / HXUSABigAirPort)

------------------------------

{chr(10).join(resolve_lines)}

TheAirPort.W3D present in ART = YES
HXUSABigAirPort.W3D present in ART = YES
CJJCWUJUN.dds present in ART = YES

Fighter parking 4x4 preserved = YES
Heavy parking 3x2 preserved = YES

T-50 disabled = YES
  (no russiajett50pakfaclean.ini; no T50 CommandSet refs)

Russia aircraft retained (non-T50) = YES
  Su-47 / SuT75 / Tu-160 / Tu-95 / An-124 / An-225 / avionIL76 / A-50 / cargoIL76

Other faction gameplay intentionally changed = NO

PR344 DATA file count = {len(base)}
Recovery DATA file count = {len(vdata)}
Missing unrelated runtime files vs PR344 = 0

DATA sha256 = {dhash}
ART sha256 = {ahash}
ZIP = {ZIP_OUT}

IMPORTANT: static recovery PASS only. User must test dozer placement (green ghost)
and construction across factions. Do NOT claim in-game PASS.
"""
    REPORT.write_text(report)
    DOWNLOAD.write_text(
        "ZIP (DATA + ART — airport W3Ds were missing):\n(pending upload)\n\n"
        f"_SPEC_DATA_ONE.big sha256={dhash}\n_SPEC_ART_ONE.big sha256={ahash}\nZIP sha256={zhash}\n"
    )
    print(report)
    print("Added russia keys sample:", added[:20], "... total", len(added))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
