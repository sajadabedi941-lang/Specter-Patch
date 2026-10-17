#!/usr/bin/env python3
"""Emergency T-50 crash isolation: remove T-50 completely from active DATA.

NO T-50 Object rebuild. DATA only. ART untouched.
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
STAGE = MASTER / "_stage_russia_t50_isolation"
VERIFY = MASTER / "_extract_russia_t50_isolation_verify"
ZIP_OUT = PATCH / "Release/SPECTER_MASTER_DATA_RUSSIA_T50_ISOLATION.zip"
REPORT = PATCH / "Release/DATA_RUSSIA_T50_ISOLATION_REPORT.txt"
HASHES = PATCH / "Release/DATA_RUSSIA_T50_ISOLATION_HASHES.txt"
DOWNLOAD = PATCH / "Release/DATA_RUSSIA_T50_ISOLATION_DOWNLOAD.txt"

AF = "Armed Forces Of Russian Federation"
T50_OBJ = "RussiaJetT50PAKFAClean"
T50_BTN = "Command_ConstructRussiaJetT50PAKFA"
T50_KEY = rf"Data\INI\Object\Specter\{AF}\Airforce\RussiaJetT50PAKFAClean.ini"

# Optional non-Object T50 support files — remove so runtime has no T50 gameplay chain
EXTRA_REMOVE = [
    r"Data\English\SPECTER_T50_PAKFA_Strings.txt",
    # Keep MappedImages? Icon art DATA block is not an Object; leave it (harmless, no Object).
]

RETAIN = [
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


def count_t50_objects(store: dict[str, bytes]) -> list[tuple[str, str]]:
    hits = []
    pat = re.compile(r"(?m)^Object\s+(\S+)\s*$")
    for k, v in store.items():
        if not k.lower().endswith(".ini"):
            continue
        text = v.decode("latin1", errors="replace")
        for m in pat.finditer(text):
            name = m.group(1)
            nl = name.lower()
            if any(x in nl for x in ["t50", "pakfa", "sut50"]):
                hits.append((k, name))
    return hits


def strip_commandset_t50(cs: str) -> str:
    m = re.search(r"(?ms)^CommandSet\s+Russia_LargeAirBaseCommandSet\s*.*?^End", cs)
    assert m, "Russia_LargeAirBaseCommandSet missing"
    block = m.group(0)
    # Remove ONLY the T50 slot line; leave gap (no replacement aircraft)
    new_block = re.sub(
        rf"(?m)^\s*11\s*=\s*{re.escape(T50_BTN)}\s*\n",
        "",
        block,
    )
    assert T50_BTN not in new_block
    assert "Command_ConstructRussiaJetSu47Recon" in new_block
    assert "Command_ConstructRussiaJetSu75Checkmate" in new_block
    assert "Command_Sell" in new_block
    return cs[: m.start()] + new_block + cs[m.end() :]


def strip_commandbutton_t50(cb: str) -> str:
    m = re.search(rf"(?ms)^CommandButton\s+{re.escape(T50_BTN)}\s*.*?^End\s*", cb)
    if not m:
        return cb
    return cb[: m.start()] + cb[m.end() :]


def main() -> int:
    assert DATA_BIG.exists(), DATA_BIG
    # Discard previous BIG path by rebuilding from a fresh in-memory map into NEW staging,
    # then overwrite DATA_BIG with a newly built archive (not in-place patch of entries).
    old = read_big(DATA_BIG)
    before_retain = {n: count_obj(old, n) for n in RETAIN}
    before_t50 = count_t50_objects(old)

    data = dict(old)

    removed_keys = []
    # Remove crash file (any case)
    for k in list(data):
        if k.lower().endswith("russiajett50pakfaclean.ini"):
            del data[k]
            removed_keys.append(k)
    assert T50_KEY not in data
    assert not any(k.lower().endswith("russiajett50pakfaclean.ini") for k in data)

    for key in EXTRA_REMOVE:
        for k in list(data):
            if k.lower() == key.lower():
                del data[k]
                removed_keys.append(k)

    # CommandSet / CommandButton
    cs_key = r"Data\INI\CommandSet.ini"
    cb_key = r"Data\INI\CommandButton.ini"
    cs = data[cs_key].decode("latin1", errors="replace")
    cb = data[cb_key].decode("latin1", errors="replace")
    cs2 = strip_commandset_t50(cs)
    cb2 = strip_commandbutton_t50(cb)
    assert T50_BTN not in cs2
    assert T50_OBJ not in cs2
    # button definition removed
    assert not re.search(rf"(?m)^CommandButton\s+{re.escape(T50_BTN)}\s*$", cb2)
    assert T50_OBJ not in cb2
    data[cs_key] = cs2.encode("latin1", errors="replace")
    data[cb_key] = cb2.encode("latin1", errors="replace")

    # Also sync patch source files that exist for Object
    src_obj = PATCH / f"Data/INI/Object/Specter/{AF}/Airforce/RussiaJetT50PAKFAClean.ini"
    if src_obj.exists():
        src_obj.unlink()

    # Staging audits BEFORE pack
    assert count_obj(data, T50_OBJ) == 0
    assert count_t50_objects(data) == []
    assert not any("russiajett50pakfaclean.ini" in k.lower() for k in data)
    assert T50_BTN not in data[cs_key].decode("latin1", errors="replace")
    for n in RETAIN:
        assert count_obj(data, n) == before_retain[n] == 1, n

    # Parking unchanged
    for bkey, rows, cols in [
        (rf"Data\INI\Object\Specter\{AF}\Buildings\Russia_LargeAirBase.ini", 4, 4),
        (rf"Data\INI\Object\Specter\{AF}\Buildings\Russia_HeavyAirBase.ini", 3, 2),
    ]:
        t = data[bkey].decode("latin1", errors="replace")
        assert re.search(rf"NumRows\s*=\s*{rows}", t)
        assert re.search(rf"NumCols\s*=\s*{cols}", t)

    # Clean staging + NEW big
    if STAGE.exists():
        shutil.rmtree(STAGE)
    write_tree(data, STAGE / "DATA_TREE")
    stage_hit = list((STAGE / "DATA_TREE").rglob("*t50*")) + list((STAGE / "DATA_TREE").rglob("*T50*"))
    stage_hit += list((STAGE / "DATA_TREE").rglob("*pakfa*")) + list((STAGE / "DATA_TREE").rglob("*PAKFA*"))
    # MappedImages TEOD_T50 may remain — filter Object path only for hard fail
    obj_hits = [p for p in stage_hit if "Object" in str(p) and p.suffix.lower() == ".ini"]
    assert obj_hits == [], obj_hits
    assert not (STAGE / "DATA_TREE/Data/INI/Object/Specter" / AF / "Airforce/RussiaJetT50PAKFAClean.ini").exists()

    # Discard old BIG bytes: write brand-new archive
    if DATA_BIG.exists():
        DATA_BIG.unlink()
    DATA_BIG.write_bytes(build_big(data))

    # Re-extract FINAL BIG
    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    vdata = read_big(DATA_BIG)
    write_tree(vdata, VERIFY)

    # FINAL extracted audits
    assert not any(k.lower().endswith("russiajett50pakfaclean.ini") for k in vdata)
    assert count_obj(vdata, T50_OBJ) == 0
    t50_objs = count_t50_objects(vdata)
    assert t50_objs == [], t50_objs

    vcs = vdata[cs_key].decode("latin1", errors="replace")
    vcb = vdata[cb_key].decode("latin1", errors="replace")
    assert T50_BTN not in vcs
    assert T50_OBJ not in vcs
    assert T50_OBJ not in vcb
    assert not re.search(rf"(?m)^CommandButton\s+{re.escape(T50_BTN)}\s*$", vcb)

    # No CommandSet reference to missing T50 anywhere
    assert T50_BTN not in vcs
    for n in RETAIN:
        assert count_obj(vdata, n) == 1, n

    # Fighter CS still valid
    m = re.search(r"(?ms)^CommandSet\s+Russia_LargeAirBaseCommandSet\s*.*?^End", vcs)
    assert m
    assert "11 =" not in m.group(0) and "11=" not in m.group(0).replace(" ", "")
    # more precise: no slot 11
    assert not re.search(r"(?m)^\s*11\s*=", m.group(0))

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    dhash = sha256(DATA_BIG)
    zhash = sha256(ZIP_OUT)
    HASHES.write_text(f"_SPEC_DATA_ONE.big sha256={dhash}\nZIP sha256={zhash}\n")

    # List remaining PAKFA non-object keys (UI mapped images only expected)
    leftover = [k for k in sorted(vdata) if any(x in k.lower() for x in ["t50", "pakfa", "sut50"])]

    report = f"""T50 CRASH ISOLATION BUILD = PASS

Crash file from ReleaseCrashInfo =
Data\\INI\\Object\\specter\\armed forces of russian federation\\airforce\\russiajett50pakfaclean.ini

SOURCE STAGING:
Crash file removed = YES
T50 Object count = 0
T50 CommandSet references = 0

FINAL EXTRACTED _SPEC_DATA_ONE.big:
russiajett50pakfaclean.ini present = NO

RussiaJetT50 definitions = 0
SuT50 definitions = 0
PAKFA gameplay Objects = 0

Russia Fighter Airbase T50 button removed = YES
(slot 11 emptied; no replacement aircraft)

Su-47 retained = YES
SuT75 retained = YES
Tu-160 retained = YES

Tu-95 retained = YES
An-124 retained = YES
An-225 retained = YES
avionIL76 retained = YES
A-50 retained = YES
cargoIL76 retained = YES

Other factions changed = NO
ART changed = NO

Removed keys:
{chr(10).join('  - ' + k for k in removed_keys)}

Before T50 Object hits: {before_t50}
After T50 Object hits: {t50_objs}

Non-Object leftover path keys (UI MappedImages only expected):
{chr(10).join('  - ' + k for k in leftover) if leftover else '  (none)'}

DATA sha256 = {dhash}
ZIP = {ZIP_OUT}

IMPORTANT: Do NOT claim game launch. User tests this recovery build.
"""
    REPORT.write_text(report)
    DOWNLOAD.write_text(
        "ZIP (DATA only):\n(pending upload)\n\n"
        f"_SPEC_DATA_ONE.big sha256={dhash}\nZIP sha256={zhash}\n"
        "ART unchanged — do not replace _SPEC_ART_ONE.big\n"
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
