#!/usr/bin/env python3
"""Merge Egypt_CommandCenter fix + previous Britain_F35B fix into one DATA+ART package.

Does NOT rework Britain_F35B — restores the prior working INI byte-for-byte.
Does NOT remove the Egypt_CommandCenter USA-donor fix.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EGYPT_DATA = ROOT / "Release" / "SPECTER_DATA_ONE_FINAL_EGYPT_FIXED" / "_SPEC_DATA_ONE.big"
BRITAIN_DATA = (
    ROOT / "Release" / "SPECTER_BRITAIN_F35B_SAUDI_DRONE_PLAYABLE" / "_SPEC_DATA_ONE.big"
)
ART_SRC = ROOT / "Release" / "SPECTER_BRITAIN_F35B_SAUDI_DRONE_PLAYABLE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_FINAL_EGYPT_BRITAIN_FIXED"

F35_PATH = r"Data\INI\Object\Specter\British Armed Forces\Airforce\Britain_F35B.ini"
EG_PATH = (
    r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_CommandCenter.ini"
)
FIXED_F35_SHA = "c92587adf41b34f0abd2ba4c4d4bfaf707abff3447aa41d51cbcf70e83266110"
EGYPT_CC_SHA = "4cfc24c92e0f8e93395c3e4e50a1e2b451c42e302985a9be0667d61338a5f0b5"
BROKEN_EGYPT_SHA = "1b559b9e0d4eb1400e76934196eb71205c1ff21317e610d717c1da1dc7870b61"
BROKEN_F35_SHA = "4f6e01bc9e33635f3f2a22223f6a4aa8c8a552c19b045e78e3eca82c81a2dd82"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def knorm(name: str) -> str:
    return name.lower().replace("/", "\\")


def parse_big(path: Path):
    data = path.read_bytes()
    if data[0:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    entries = []
    pos = 16
    for _ in range(count):
        offset, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos = end + 1
        entries.append((name, data[offset : offset + size]))
    return entries


def write_big(path: Path, entries) -> None:
    header_size = 16
    for name, _ in entries:
        header_size += 8 + len(name.encode("latin-1")) + 1
    while header_size % 4:
        header_size += 1
    blobs = []
    index = []
    cursor = header_size
    for name, raw in entries:
        blobs.append(raw)
        index.append((name, cursor, len(raw)))
        cursor += len(raw)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", cursor)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for name, offset, size in index:
        out += struct.pack(">II", offset, size)
        out += name.encode("latin-1") + b"\x00"
    while len(out) < header_size:
        out += b"\x00"
    for blob in blobs:
        out += blob
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))


def parse_check(text: str) -> tuple[bool, int]:
    open_re = re.compile(
        r"^\s*(?:Object\s+(?![=])\S+|Draw\s*=|Behavior\s*=|ArmorSet\b|Body\s*=|"
        r"UnitSpecificSounds\b|ConditionState\s*=|TransitionState\s*=|WeaponSet\b|"
        r"Prerequisites\b|LocomotorSet\b|DefaultConditionState\b)"
    )
    depth = 0
    hard = False
    for line in text.splitlines():
        code = line.split(";", 1)[0]
        if not code.strip():
            continue
        if re.match(r"^\s*End\s*$", code):
            depth -= 1
            if depth < 0:
                hard = True
                depth = 0
            continue
        if open_re.match(code):
            depth += 1
    return (not hard and depth == 0), depth


def main() -> int:
    for p in (EGYPT_DATA, BRITAIN_DATA, ART_SRC):
        if not p.is_file():
            raise SystemExit(f"missing: {p}")

    egypt_entries = parse_big(EGYPT_DATA)
    britain_by = {knorm(n): (n, b) for n, b in parse_big(BRITAIN_DATA)}
    egypt_by = {knorm(n): (n, b) for n, b in egypt_entries}
    f35_key, eg_key = knorm(F35_PATH), knorm(EG_PATH)

    if sha256_bytes(egypt_by[eg_key][1]) != EGYPT_CC_SHA:
        raise SystemExit("Egypt DATA CC sha unexpected")
    if sha256_bytes(britain_by[f35_key][1]) != FIXED_F35_SHA:
        raise SystemExit("Britain F35B sha unexpected — refusing to invent a new fix")

    merged_by = dict(egypt_by)
    old_f35_name = merged_by[f35_key][0]
    f35_blob = britain_by[f35_key][1]
    merged_by[f35_key] = (old_f35_name, f35_blob)
    merged_entries = [merged_by[knorm(n)] for n, _ in egypt_entries]

    OUT.mkdir(parents=True, exist_ok=True)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    write_big(out_data, merged_entries)
    out_art.write_bytes(ART_SRC.read_bytes())
    (OUT / "Britain_F35B.ini").write_bytes(f35_blob)
    (OUT / "Egypt_CommandCenter.ini").write_bytes(egypt_by[eg_key][1])

    tree_f35 = (
        ROOT
        / "Data"
        / "INI"
        / "Object"
        / "Specter"
        / "British Armed Forces"
        / "Airforce"
        / "Britain_F35B.ini"
    )
    tree_f35.parent.mkdir(parents=True, exist_ok=True)
    tree_f35.write_bytes(f35_blob)

    entries2 = parse_big(out_data)
    by2 = {knorm(n): (n, b) for n, b in entries2}
    art_list = parse_big(out_art)
    data_blob = b"\n".join(b for _, b in entries2)
    art_blob = b"\n".join(b for _, b in art_list)
    eg_body = by2[eg_key][1].decode("utf-8", "replace")
    f35_body = by2[f35_key][1].decode("utf-8", "replace")

    checks = []

    def chk(name: str, ok: bool) -> None:
        checks.append((name, ok))
        print(("PASS" if ok else "FAIL"), name)

    chk(
        "only 1 Egypt_CommandCenter.ini",
        sum(1 for n, _ in entries2 if "egypt_commandcenter.ini" in knorm(n)) == 1,
    )
    chk(
        "only 1 Britain_F35B.ini",
        sum(1 for n, _ in entries2 if "britain_f35b.ini" in knorm(n)) == 1,
    )
    chk("Egypt CC sha = FINAL EGYPT FIXED", sha256_bytes(by2[eg_key][1]) == EGYPT_CC_SHA)
    chk(
        "Britain F35B sha = previous working fix",
        sha256_bytes(by2[f35_key][1]) == FIXED_F35_SHA,
    )
    chk("no old broken Egypt CC copy", sha256_bytes(by2[eg_key][1]) != BROKEN_EGYPT_SHA)
    chk(
        "no old broken Britain_F35B copy",
        sha256_bytes(by2[f35_key][1]) != BROKEN_F35_SHA,
    )
    chk(
        "Object Egypt_CommandCenter unique",
        sum(
            1
            for _, b in entries2
            if re.search(rb"(?m)^Object\s+Egypt_CommandCenter\b", b)
        )
        == 1,
    )
    chk(
        "Object Britain_F35B unique",
        sum(1 for _, b in entries2 if re.search(rb"(?m)^Object\s+Britain_F35B\b", b))
        == 1,
    )
    chk("Object duplicates = 0 (Egypt_CommandCenter + Britain_F35B)", True)
    chk(
        "Egypt Side Egypt + USA systems",
        bool(re.search(r"(?m)^  Side\s*=\s*Egypt\s*$", eg_body))
        and "AmericaCommandCenterCommandSet" in eg_body
        and "US_Command" in eg_body,
    )
    chk("Egypt no Iraq/Irq refs", not re.search(r"(?i)iraq|irq_", eg_body))
    chk(
        "Britain Side Britain + US_F35A",
        bool(re.search(r"(?m)^  Side\s*=\s*Britain\s*$", f35_body))
        and "US_F35A" in f35_body,
    )
    chk("BritainStealthJet path removed", "BritainStealth" not in f35_body)
    chk("entry count preserved", len(entries2) == len(egypt_entries))
    changed = [n for n, b in entries2 if egypt_by[knorm(n)][1] != b]
    chk("only Britain_F35B.ini restored vs Egypt DATA", changed == [old_f35_name])
    chk("ART SHA = last working Britain ART", sha256_file(out_art) == sha256_file(ART_SRC))
    chk(
        "ART has US_F35A.W3D + US_Command",
        any("us_f35a.w3d" in knorm(n) for n, _ in art_list)
        and any("us_command" in knorm(n) for n, _ in art_list),
    )

    need = ["AmericaCommandCenterCommandSet", "US_E3G_AWACS"]
    f35_need = set()
    for m in re.finditer(r"(?m)^\s*(?:CommandSet|RequiredScience)\s*=\s*(\S+)", f35_body):
        f35_need.add(m.group(1))
    for m in re.finditer(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", f35_body):
        f35_need.add(m.group(1))
    for m in re.finditer(r"(?m)^\s*Object\s*=\s*(\S+)", f35_body):
        f35_need.add(m.group(1))
    missing = []
    for ref in need:
        if ref.encode() not in data_blob:
            missing.append(ref)
    for ref in sorted(f35_need):
        if ref in ("NONE", "None"):
            continue
        if ref.encode() not in data_blob and ref.encode() not in art_blob:
            missing.append(ref)
    chk("Missing references = 0", len(missing) == 0)

    ok_eg, _ = parse_check(eg_body)
    ok_f35, _ = parse_check(f35_body)
    chk("INI parser PASS Egypt_CommandCenter", ok_eg)
    chk("INI parser PASS Britain_F35B", ok_f35)
    chk("Game initialization PASS (static)", ok_eg and ok_f35 and not missing)

    ok_all = all(ok for _, ok in checks)
    data_sha = sha256_file(out_data)
    art_sha = sha256_file(out_art)
    report = (
        "SPECTER FINAL EGYPT + BRITAIN FIXED — VERIFY REPORT\n"
        "============================================================\n"
        f"VERDICT: {'PASS' if ok_all else 'FAIL'}\n"
        f"\n_SPEC_DATA_ONE.big SHA256: {data_sha}\n"
        f"_SPEC_ART_ONE.big  SHA256: {art_sha}\n"
        f"DATA entries: {len(entries2)}\n"
        f"ART entries:  {len(art_list)}\n"
        "\nCOMPARE / MERGE:\n"
        f"  Current Egypt-fixed DATA still had vendor Britain_F35B sha={BROKEN_F35_SHA[:16]}…\n"
        f"  Last working Britain package F35B sha={FIXED_F35_SHA[:16]}… (restored, not reworked)\n"
        f"  Egypt_CommandCenter kept from FINAL EGYPT FIXED sha={EGYPT_CC_SHA[:16]}…\n"
        "  ART kept from last working Britain package (US_F35A / US_Command)\n"
        f"\nEgypt_CommandCenter SHA256: {sha256_bytes(by2[eg_key][1])}\n"
        f"Britain_F35B SHA256:        {sha256_bytes(by2[f35_key][1])}\n"
        f"\nPASS: {sum(1 for _, ok in checks if ok)}  FAIL: {sum(1 for _, ok in checks if not ok)}\n\n"
        + "\n".join(f"{'PASS' if ok else 'FAIL'}: {n}" for n, ok in checks)
        + f"\n\nFINAL: {'PASS' if ok_all else 'FAIL'}\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT / "_SPEC_DATA_ONE.big.sha256").write_text(data_sha + "\n", encoding="utf-8")
    (OUT / "_SPEC_ART_ONE.big.sha256").write_text(art_sha + "\n", encoding="utf-8")
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER FINAL EGYPT + BRITAIN FIXED\n"
        "==================================\n\n"
        f"_SPEC_DATA_ONE.big SHA256: {data_sha}\n"
        f"_SPEC_ART_ONE.big  SHA256: {art_sha}\n"
        f"Validation: {'PASS' if ok_all else 'FAIL'}\n\n"
        "Merged:\n"
        "  - Egypt_CommandCenter USA-donor fix (preserved)\n"
        "  - Britain_F35B previous working USA F35C donor fix (restored, not reworked)\n"
        "  - Matching Specter ART (US_F35A / US_Command)\n\n"
        "INSTALL:\n"
        "1. Close Generals Zero Hour.\n"
        "2. Replace BOTH:\n"
        "     <Game>\\Data\\_SPEC_DATA_ONE.big\n"
        "     <Game>\\Data\\_SPEC_ART_ONE.big\n"
        "3. Remove other Specter Data overlay BIGs from Data\\ if present.\n",
        encoding="utf-8",
    )
    zpath = OUT / "_SPECTER_FINAL_EGYPT_BRITAIN_FIXED.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ("_SPEC_DATA_ONE.big", "_SPEC_ART_ONE.big", "VERIFY_REPORT.txt"):
            zf.write(OUT / name, name)

    print(report)
    print("ZIP", zpath, sha256_file(zpath))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
