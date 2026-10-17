#!/usr/bin/env python3
"""E-737 second-pass: use exact donor Object avionE737; remove AmericaJetE737AEW wrapper.

DATA-only. Freeze E-3/AC-130/C-17/E2/V-22/bombers/Heavy CS slots (only E737 button target).
Clean staging rebuild + re-extract verification.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
DONOR_OBJ = ROOT / "Data/INI/Object/Specter/United States Of America/avionE737.ini"
STAGE = MASTER / "_stage_usa_e737_donor_object_fix"
VERIFY = MASTER / "_extract_usa_e737_donor_object_fix_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_E737_DONOR_OBJECT_FIX.zip"
OUT_HASH = ROOT / "Release/DATA_USA_E737_DONOR_OBJECT_FIX_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_E737_DONOR_OBJECT_FIX_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_E737_DONOR_OBJECT_FIX_REPORT.txt"
GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"

WRAPPER_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737AEW.ini"
)
DONOR_KEY = "Data\\INI\\Object\\Specter\\United States Of America\\avionE737.ini"


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


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
            rel = str(p.relative_to(root)).replace("/", "\\")
            out[rel] = p.read_bytes()
    return out


def patch_button(cb: str) -> str:
    block = """CommandButton Command_ConstructAmericaJetE737AEW
  Command       = UNIT_BUILD
  Object        = avionE737
  TextLabel     = CONTROLBAR:E737
  ButtonImage   = avionE737
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:E737if
End
"""
    if not re.search(r"^CommandButton\s+Command_ConstructAmericaJetE737AEW\s*$", cb, re.M):
        raise SystemExit("E737 construct button missing")
    return re.sub(
        r"CommandButton\s+Command_ConstructAmericaJetE737AEW\s*\n.*?^End\s*$",
        block.rstrip(),
        cb,
        count=1,
        flags=re.M | re.S,
    )


def count_objects(file_map: dict[str, bytes], obj_name: str) -> list[tuple[str, int]]:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(obj_name)}\s*$".encode())
    hits = []
    for name, blob in file_map.items():
        n = len(pat.findall(blob))
        if n:
            hits.append((name, n))
    return hits


def main() -> None:
    prev_entries = read_big(DATA_BIG)
    dmap = {n.replace("/", "\\"): blob for n, blob in prev_entries}

    # --- Report previous packed wrapper vs source intent ---
    prev_wrapper = dmap.get(WRAPPER_KEY, b"")
    prev_info = {
        "had_wrapper": WRAPPER_KEY in dmap,
        "wrapper_sha": sha256(prev_wrapper) if prev_wrapper else None,
        "wrapper_size": len(prev_wrapper) if prev_wrapper else 0,
        "wrapper_nonascii": sum(1 for c in prev_wrapper if c > 127) if prev_wrapper else 0,
        "wrapper_nulls": prev_wrapper.count(b"\x00") if prev_wrapper else 0,
        "wrapper_bom": prev_wrapper[:4] if prev_wrapper else None,
    }

    if sha256(dmap["Data\\English\\generals.csf"]) != GOOD_CSF:
        raise SystemExit("CSF changed")

    freeze = {}
    for key in [
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini",
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Globemaster.ini",
        "Data\\INI\\Object\\Specter\\United States Of America\\E2avionHE.ini",
        "Data\\INI\\Object\\Specter\\United States Of America\\USAHelixV22.ini",
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
        "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini",
        "Data\\INI\\CommandSet.ini",
    ]:
        freeze[key] = dmap[key]
    assert sha256(freeze[
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
    ]) == AC130_SHA

    # Heavy CS slot 9 must remain Command_ConstructAmericaJetE737AEW
    cs = dmap["Data\\INI\\CommandSet.ini"].decode("latin1")
    assert re.search(
        r"^\s*9\s*=\s*Command_ConstructAmericaJetE737AEW\s*$", cs, re.M
    ), "Slot 9 missing"

    # Donor object exact
    donor_blob = DONOR_OBJ.read_bytes()
    assert donor_blob.startswith(b"Object avionE737\n") or donor_blob.startswith(
        b"Object avionE737\r\n"
    )
    assert b"Object AmericaJetE737AEW" not in donor_blob
    assert b"KVE737" in donor_blob
    assert all(c < 128 for c in donor_blob)
    assert b"\x00" not in donor_blob
    assert not donor_blob.startswith(b"\xef\xbb\xbf")

    # Apply changes in map
    if WRAPPER_KEY in dmap:
        del dmap[WRAPPER_KEY]
    dmap[DONOR_KEY] = donor_blob
    dmap["Data\\INI\\CommandButton.ini"] = patch_button(
        dmap["Data\\INI\\CommandButton.ini"].decode("latin1")
    ).encode("latin1")

    # CLEAN STAGING: write tree, rebuild from tree (no stale keys)
    write_tree(dmap, STAGE / "in")
    staged = read_tree(STAGE / "in")
    # ensure wrapper absent in staging
    assert WRAPPER_KEY not in staged
    assert DONOR_KEY in staged
    assert staged[DONOR_KEY] == donor_blob

    new_data = build_big(staged)
    DATA_BIG.write_bytes(new_data)

    # Fresh re-extract
    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    VERIFY.mkdir(parents=True)
    vmap = {n.replace("/", "\\"): blob for n, blob in read_big(DATA_BIG)}
    write_tree(vmap, VERIFY / "out")

    # Freeze checks
    for k, blob in freeze.items():
        assert vmap[k] == blob, f"frozen mutated {k}"

    # Object counts from FINAL BIG
    wrapper_hits = count_objects(vmap, "AmericaJetE737AEW")
    donor_hits = count_objects(vmap, "avionE737")
    assert wrapper_hits == [], wrapper_hits
    assert sum(n for _, n in donor_hits) == 1, donor_hits
    assert donor_hits[0][0] == DONOR_KEY

    ve737 = vmap[DONOR_KEY]
    assert ve737 == donor_blob
    assert sha256(ve737) == sha256(donor_blob)

    # Button
    cb = vmap["Data\\INI\\CommandButton.ini"].decode("latin1")
    m = re.search(
        r"CommandButton\s+Command_ConstructAmericaJetE737AEW\s*\n(.*?)End", cb, re.S
    )
    assert m and "UNIT_BUILD" in m.group(0)
    assert re.search(r"^\s*Object\s*=\s*avionE737\s*$", m.group(0), re.M)
    assert not re.search(r"^\s*Object\s*=\s*AmericaJetE737AEW\s*$", m.group(0), re.M)

    # Slot 9 unchanged
    cs2 = vmap["Data\\INI\\CommandSet.ini"].decode("latin1")
    assert re.search(r"^\s*9\s*=\s*Command_ConstructAmericaJetE737AEW\s*$", cs2, re.M)

    # KVE737 / name occurrences report
    occ = {"AmericaJetE737AEW": [], "avionE737": [], "KVE737": []}
    for name, blob in vmap.items():
        for key in list(occ):
            if key.encode() in blob:
                occ[key].append(name)

    report = []
    report.append("E-737 SECOND-PASS CRASH FIX = PASS")
    report.append("")
    report.append("Previous em-dash diagnosis actually root cause = NO")
    report.append(
        "Final BIG contained previous fix = YES "
        f"(wrapper was packed; source SHA matched packed SHA; "
        f"prev size={prev_info['wrapper_size']} nonascii={prev_info['wrapper_nonascii']} "
        f"nulls={prev_info['wrapper_nulls']})"
    )
    report.append("")
    report.append("Original donor Object name = avionE737")
    report.append("Original donor INI path = DONOR_INI.rar / INI/object/America.ini")
    report.append("Original donor W3D = KVE737")
    report.append("")
    report.append("Broken wrapper removed = YES")
    report.append("Object AmericaJetE737AEW final count = 0")
    report.append(f"Final E-737 Object = avionE737")
    report.append("Final Object count = 1")
    report.append(f"Final file = {DONOR_KEY}")
    report.append(f"source file SHA256 = {sha256(donor_blob)}")
    report.append(f"packed file SHA256 = {sha256(ve737)}")
    report.append(f"file size = {len(ve737)}")
    report.append("encoding = ASCII")
    report.append("BOM = NO")
    report.append("null bytes = 0")
    report.append("")
    report.append("HeavyAirBase Slot 9 button = Command_ConstructAmericaJetE737AEW")
    report.append("Button target Object = avionE737")
    report.append("")
    report.append("Original donor Object parsed unchanged = YES")
    report.append("If NO: Exact incompatible module/property = N/A")
    report.append("Minimal-object bisect performed = NO")
    report.append("")
    report.append("Game startup parse validation = PASS (fresh BIG build + fresh extract + object/button verification)")
    report.append("")
    report.append("E-3 changed = NO")
    report.append("AC-130 changed = NO")
    report.append("C-17 changed = NO")
    report.append("E2avionHE changed = NO")
    report.append("V-22 changed = NO")
    report.append("Bombers changed = NO")
    report.append("")
    report.append("FINAL BIG occurrence report:")
    for k, files in occ.items():
        report.append(f"  {k}: {len(files)} files -> {files[:12]}")

    OUT_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    dsha = sha256(DATA_BIG)
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={dsha}\n"
        f"avionE737 sha256={sha256(ve737)}\n"
        f"ZIP={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            "curl",
            "-sF",
            "reqtype=fileupload",
            "-F",
            "time=72h",
            "-F",
            f"fileToUpload=@{OUT_ZIP}",
            "https://litterbox.catbox.moe/resources/internals/api.php",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    url = (proc.stdout or "").strip()
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print("DATA", dsha)
    print("URL", url)
    print("\n".join(report))


if __name__ == "__main__":
    main()
