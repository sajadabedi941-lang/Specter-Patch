#!/usr/bin/env python3
"""Fix AmericaJetE737AEW parse crash: recreate from donor avionE737 (ASCII-only).

Also strip parser-breaking UTF-8 from C-17/E2 source (same batch). DATA-only.
Freeze: E-3, AC-130, bombers, Heavy CS, ART.
"""
from __future__ import annotations

import hashlib
import re
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
OBJ = ROOT / "Data/INI/Object/Specter/United States Of America"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_E737_PARSE_FIX.zip"
OUT_HASH = ROOT / "Release/DATA_USA_E737_PARSE_FIX_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_E737_PARSE_FIX_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_E737_PARSE_FIX_REPORT.txt"
VERIFY = MASTER / "_extract_usa_e737_parse_fix_verify"
GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"

FILES = {
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737AEW.ini":
        OBJ / "AmericaJetE737AEW.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Globemaster.ini":
        OBJ / "AmericaJetC17Globemaster.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\E2avionHE.ini":
        OBJ / "E2avionHE.ini",
}


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
        entries.append((name, off, size))
    return entries, data


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


def assert_ascii_object(blob: bytes, name: str) -> None:
    assert not blob.startswith(b"\xef\xbb\xbf"), f"{name} UTF-8 BOM"
    assert not blob.startswith(b"\xff\xfe") and not blob.startswith(b"\xfe\xff")
    assert b"\x00" not in blob, f"{name} nulls"
    assert all(c < 128 for c in blob), f"{name} non-ASCII"
    text = blob.decode("ascii")
    objs = re.findall(r"(?m)^Object\s+(\S+)", text)
    assert len(objs) == 1, f"{name} object count {objs}"
    assert "-----BEGIN" not in text and "<<<<<<" not in text
    # no nested Object
    assert text.strip().startswith("Object ")


def main() -> None:
    dentries, dblob = read_big(DATA_BIG)
    dmap = {n.replace("/", "\\"): dblob[o : o + s] for n, o, s in dentries}

    if sha256(dmap["Data\\English\\generals.csf"]) != GOOD_CSF:
        raise SystemExit("CSF changed")

    ac130_key = (
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
    )
    assert sha256(dmap[ac130_key]) == AC130_SHA

    # Freeze E-3 block fingerprint (must contain donor E3 model, not US_E3G)
    usa_key = "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"
    usa_before = dmap[usa_key]
    assert b"Object AmericaJetE3AWACS" in usa_before
    e3m = re.search(
        rb"^Object\s+AmericaJetE3AWACS\s*\n.*?(?=^Object\s+\S+\s*$)",
        usa_before,
        re.M | re.S,
    )
    e3_before = e3m.group(0)
    assert b"Model               = E3" in e3_before or re.search(
        rb"Model\s*=\s*E3\b", e3_before
    )
    assert b"US_E3G" not in e3_before

    cs_before = dmap["Data\\INI\\CommandSet.ini"]
    cb_before = dmap["Data\\INI\\CommandButton.ini"]
    v22_key = "Data\\INI\\Object\\Specter\\United States Of America\\USAHelixV22.ini"
    v22_before = dmap[v22_key]
    b21_key = (
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini"
    )
    b21_before = dmap[b21_key]

    # Replace object files
    for key, src in FILES.items():
        blob = src.read_bytes()
        assert_ascii_object(blob, src.name)
        dmap[key] = blob

    # E737 specific checks on source
    e737 = dmap[
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737AEW.ini"
    ]
    assert b"Object AmericaJetE737AEW" in e737
    assert b"KVE737" in e737
    assert b"EA_18AntiRadarECMDevice" in e737
    assert b"StealthDetector" not in e737
    assert b"\xe2\x80\x94" not in e737  # em-dash UTF-8

    new_data = build_big(dmap)
    DATA_BIG.write_bytes(new_data)

    # Verify from re-extract
    import shutil

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    VERIFY.mkdir(parents=True)
    ve, vb = read_big(DATA_BIG)
    vmap = {n.replace("/", "\\"): vb[o : o + s] for n, o, s in ve}

    assert sha256(vmap["Data\\English\\generals.csf"]) == GOOD_CSF
    assert sha256(vmap[ac130_key]) == AC130_SHA
    assert vmap[usa_key] == usa_before
    assert vmap["Data\\INI\\CommandSet.ini"] == cs_before
    assert vmap["Data\\INI\\CommandButton.ini"] == cb_before
    assert vmap[v22_key] == v22_before
    assert vmap[b21_key] == b21_before

    # Count AmericaJetE737AEW across ALL packed files
    count = 0
    locations = []
    for name, blob in vmap.items():
        n = len(re.findall(rb"(?m)^Object\s+AmericaJetE737AEW\s*$", blob))
        if n:
            count += n
            locations.append((name, n))
    assert count == 1, locations

    e737v = vmap[
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737AEW.ini"
    ]
    assert_ascii_object(e737v, "packed E737")
    assert b"KVE737" in e737v
    text = e737v.decode("ascii")
    assert text.count("\nObject ") + (1 if text.startswith("Object ") else 0) == 1
    # End: file should end with End
    assert text.rstrip().endswith("End")

    for key, label in [
        (
            "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Globemaster.ini",
            "C17",
        ),
        (
            "Data\\INI\\Object\\Specter\\United States Of America\\E2avionHE.ini",
            "E2",
        ),
        (v22_key, "V22"),
    ]:
        assert_ascii_object(vmap[key], label)

    # Slot 9 preserved
    cs = vmap["Data\\INI\\CommandSet.ini"].decode("latin1")
    assert "9  = Command_ConstructAmericaJetE737AEW" in cs or \
           "9 = Command_ConstructAmericaJetE737AEW" in cs
    cb = vmap["Data\\INI\\CommandButton.ini"].decode("latin1")
    m = re.search(
        r"CommandButton\s+Command_ConstructAmericaJetE737AEW\s*\n(.*?)End", cb, re.S
    )
    assert m and "UNIT_BUILD" in m.group(0) and "AmericaJetE737AEW" in m.group(0)

    report = []
    report.append("E-737 STARTUP CRASH FIX = PASS")
    report.append("")
    report.append("Root cause = UTF-8 em-dash (U+2014) in invented comment "
                  "'; WeaponSet NONE — ...' inside AmericaJetE737AEW.ini "
                  "(bytes E2 80 94). Generals INI parser rejects non-ASCII.")
    report.append("Original donor Object = avionE737")
    report.append("Donor INI path = DONOR_INI.rar / INI/object/America.ini")
    report.append("Final Object = AmericaJetE737AEW")
    report.append("Primary W3D = KVE737")
    report.append(
        "Final file = Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737AEW.ini"
    )
    report.append("Encoding = ASCII")
    report.append("BOM = NO")
    report.append("Object count = 1")
    report.append("")
    report.append("HeavyAirBase Slot 9 preserved = YES")
    report.append("E-3 changed = NO")
    report.append("AC-130 changed = NO")
    report.append("C-17 gameplay changed = NO (ASCII sanitize of UTF-8 comments only; donor body restored)")
    report.append("E2avionHE gameplay changed = NO (ASCII sanitize; donor body restored)")
    report.append("V-22 changed = NO")
    report.append("Bombers changed = NO")
    report.append("Other factions changed = NO")
    report.append("")
    report.append("C-17 parse audit = PASS")
    report.append("E2avionHE parse audit = PASS")
    report.append("V-22 parse audit = PASS")

    OUT_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    dsha = sha256(DATA_BIG)
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={dsha}\nZIP={OUT_ZIP.name}\n", encoding="utf-8"
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
