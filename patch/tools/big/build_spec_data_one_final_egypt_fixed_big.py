#!/usr/bin/env python3
"""Rebuild vendor _SPEC_DATA_ONE.big with USA-donor Egypt_CommandCenter only.

Opens the actual vendor BIG, replaces ONLY:
  Data\\INI\\Object\\Specter\\Egyptian Armed Forces\\Buildings\\Egypt_CommandCenter.ini
with an exact clone of USA AmericaCommandCenter (Object/Side kept as Egypt).
No overlay. No new Object. No rename.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_DATA_ONE.big"
OUT_DIR = ROOT / "Release" / "SPECTER_DATA_ONE_FINAL_EGYPT_FIXED"
EGYPT_PATH = r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_CommandCenter.ini"
USA_PATH = r"Data\INI\Object\Specter\United States Of America\Buildings\CommandCenter.ini"
BROKEN_VENDOR_CC_SHA = "1b559b9e0d4eb1400e76934196eb71205c1ff21317e610d717c1da1dc7870b61"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_big(path: Path):
    data = path.read_bytes()
    if data[0:4] != b"BIGF":
        raise SystemExit(f"not a BIGF archive: {path}")
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


def clone_usa_to_egypt(usa_text: str) -> str:
    text = usa_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    i = 0
    while i < len(lines) and (lines[i].strip() == "" or lines[i].lstrip().startswith(";")):
        i += 1
    text = "\n".join(lines[i:])
    if not text.startswith("Object AmericaCommandCenter"):
        raise SystemExit("unexpected USA CommandCenter start")

    text = text.replace("Object AmericaCommandCenter", "Object Egypt_CommandCenter", 1)
    text = re.sub(r"(?m)^(  Side\s*=\s*)America\s*$", r"\1Egypt", text, count=1)
    text = re.sub(
        r"(?m)^(  DisplayName\s*=\s*)OBJECT:CommandCenter\s*$",
        r"\1OBJECT:Egypt_CommandCenter",
        text,
        count=1,
    )
    header = (
        "; SPECTER DATA ONE FINAL EGYPT FIXED\n"
        "; Egypt_CommandCenter rebuilt as exact USA AmericaCommandCenter clone\n"
        "; Keep: Object Egypt_CommandCenter / Side Egypt / Faction Egypt\n"
        "; Donor systems: AmericaCommandCenter model, CommandSet, buttons, behaviors\n"
        "; No overlay. No new Object. No rename.\n"
        "\n"
    )
    text = header + text

    if "Object Egypt_CommandCenter" not in text:
        raise SystemExit("Object Egypt_CommandCenter missing")
    if not re.search(r"(?m)^  Side\s*=\s*Egypt\s*$", text):
        raise SystemExit("Side Egypt missing")
    if re.search(r"(?i)iraq|irq_", text):
        raise SystemExit("Iraq/Irq references remain in cloned Egypt CC")
    if "AmericaCommandCenterCommandSet" not in text:
        raise SystemExit("America CommandSet missing")
    if "US_Command" not in text or "us_commandcenter" not in text:
        raise SystemExit("USA model/icons missing")
    return text.replace("\n", "\r\n")


def main() -> int:
    if not VENDOR.is_file():
        raise SystemExit(f"missing vendor BIG: {VENDOR}")

    entries = parse_big(VENDOR)
    by = {n.lower().replace("/", "\\"): (n, b) for n, b in entries}
    usa_key = USA_PATH.lower()
    egypt_key = EGYPT_PATH.lower()
    if usa_key not in by:
        raise SystemExit("USA CommandCenter.ini missing from vendor BIG")
    if egypt_key not in by:
        raise SystemExit("Egypt_CommandCenter.ini missing from vendor BIG")

    usa_text = by[usa_key][1].decode("utf-8", "replace")
    egypt = clone_usa_to_egypt(usa_text)
    egypt_bytes = egypt.encode("utf-8")

    old_name, old_body = by[egypt_key]
    old_sha = sha256_bytes(old_body)
    by[egypt_key] = (old_name, egypt_bytes)
    new_entries = [by[n.lower().replace("/", "\\")] for n, _ in entries]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_big = OUT_DIR / "_SPEC_DATA_ONE.big"
    write_big(out_big, new_entries)
    (OUT_DIR / "Egypt_CommandCenter.ini").write_bytes(egypt_bytes)

    tree = (
        ROOT
        / "Data"
        / "INI"
        / "Object"
        / "Specter"
        / "Egyptian Armed Forces"
        / "Buildings"
        / "Egypt_CommandCenter.ini"
    )
    tree.parent.mkdir(parents=True, exist_ok=True)
    tree.write_bytes(egypt_bytes)

    entries2 = parse_big(out_big)
    eg = [e for e in entries2 if e[0].lower().replace("/", "\\") == egypt_key]
    body = eg[0][1].decode("utf-8", "replace")
    checks = []

    def chk(name: str, ok: bool) -> None:
        checks.append((name, ok))
        print(("PASS" if ok else "FAIL"), name)

    chk("only 1 Egypt_CommandCenter.ini", len(eg) == 1)
    chk("no Iraq/Irq substrings in Egypt file", not re.search(r"(?i)iraq|irq_", body))
    chk("no Irq_Command", "Irq_Command" not in body)
    chk(
        "Object Egypt_CommandCenter once",
        len(re.findall(r"(?m)^Object\s+Egypt_CommandCenter\b", body)) == 1,
    )
    chk("Side Egypt", bool(re.search(r"(?m)^  Side\s*=\s*Egypt\s*$", body)))
    chk("America CommandSet", "AmericaCommandCenterCommandSet" in body)
    chk("USA model/icons", "US_Command" in body and "us_commandcenter" in body)
    usa_still = sum(
        1 for _, b in entries2 if re.search(rb"(?m)^Object\s+AmericaCommandCenter\b", b)
    )
    chk("AmericaCommandCenter preserved", usa_still == 1)
    chk("entry count preserved", len(entries2) == len(entries))
    old_by = {n.lower().replace("/", "\\"): b for n, b in entries}
    changed = [
        n
        for n, b in entries2
        if old_by[n.lower().replace("/", "\\")] != b
    ]
    chk("only Egypt_CommandCenter.ini content changed", changed == [old_name])
    obj_hits = sum(
        1 for _, b in entries2 if re.search(rb"(?m)^Object\s+Egypt_CommandCenter\b", b)
    )
    chk("no duplicate Egypt_CommandCenter objects", obj_hits == 1)
    broken = [
        "Irq_Command",
        "Iraq_Adnan1",
        "SUPERWEAPON_Iraqi",
        "Iraq_CommandSet",
        "irq_comndcntr",
    ]
    chk("broken vendor tokens absent", not any(t in body for t in broken))
    blob = b"\n".join(b for _, b in entries2)
    chk("AmericaCommandCenterCommandSet exists in DATA", b"AmericaCommandCenterCommandSet" in blob)
    chk("US_E3G_AWACS exists in DATA", b"US_E3G_AWACS" in blob)

    sha = sha256_file(out_big)
    egypt_sha = sha256_bytes(egypt_bytes)
    vendor_sha = sha256_file(VENDOR)
    ok_all = all(ok for _, ok in checks)
    report = (
        "SPECTER DATA ONE FINAL EGYPT FIXED — VERIFY REPORT\n"
        "============================================================\n"
        f"VERDICT: {'PASS' if ok_all else 'FAIL'}\n"
        "BIG: _SPEC_DATA_ONE.big\n"
        f"SHA256: {sha}\n"
        "Source vendor: patch/Release/SPECTER_BIG_MERGE/_SPEC_DATA_ONE.big\n"
        f"Vendor SHA256: {vendor_sha}\n"
        f"Old Egypt_CommandCenter SHA256: {old_sha}\n"
        f"New Egypt_CommandCenter SHA256: {egypt_sha}\n"
        f"Broken vendor CC SHA256: {BROKEN_VENDOR_CC_SHA}\n"
        f"Entries: {len(entries2)}\n"
        f"Size: {out_big.stat().st_size} bytes\n"
        "\n"
        "Method: open vendor _SPEC_DATA_ONE.big → replace ONLY\n"
        "Data\\INI\\Object\\Specter\\Egyptian Armed Forces\\Buildings\\Egypt_CommandCenter.ini\n"
        "with exact USA AmericaCommandCenter clone (Object/Side/Faction Egypt kept).\n"
        "No overlay. No new Object. No rename.\n"
        "\n"
        f"PASS: {sum(1 for _, ok in checks if ok)}  FAIL: {sum(1 for _, ok in checks if not ok)}\n"
        "\n"
        + "\n".join(f"{'PASS' if ok else 'FAIL'}: {name}" for name, ok in checks)
        + f"\n\nFINAL: {'PASS' if ok_all else 'FAIL'}\n"
    )
    (OUT_DIR / "VERIFY_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(sha + "\n", encoding="utf-8")
    readme = (
        "SPECTER DATA ONE FINAL EGYPT FIXED\n"
        "=================================\n"
        "\n"
        "File: _SPEC_DATA_ONE.big\n"
        f"SHA256: {sha}\n"
        f"Egypt_CommandCenter SHA256: {egypt_sha}\n"
        f"Validation: {'PASS' if ok_all else 'FAIL'}\n"
        "\n"
        "What changed:\n"
        "  ONLY Data\\INI\\Object\\Specter\\Egyptian Armed Forces\\Buildings\\Egypt_CommandCenter.ini\n"
        "  Rebuilt by copying USA AmericaCommandCenter.ini\n"
        "  Object Egypt_CommandCenter / Side=Egypt / Faction=Egypt\n"
        "  USA model / AmericaCommandCenterCommandSet / America buttons / America behaviors\n"
        "  All Irq_Command / SUPERWEAPON_Iraqi* / Iraq_Adnan1 / Iraq_CommandSet removed\n"
        "  No overlay. No new Object. No rename.\n"
        "\n"
        "INSTALLATION:\n"
        "1. Close Generals Zero Hour.\n"
        "2. Replace ONLY:  <Game>\\Data\\_SPEC_DATA_ONE.big\n"
        "3. Keep:          <Game>\\Data\\_SPEC_ART_ONE.big\n"
        "4. Remove any other Specter Data overlay BIGs from Data\\ if present.\n"
        "5. Launch and confirm Egypt Command Center loads without init crash.\n"
        "\n"
        "Do NOT replace _SPEC_ART_ONE.big.\n"
    )
    (OUT_DIR / "README_INSTALL.txt").write_text(readme, encoding="utf-8")

    zpath = OUT_DIR / "_SPECTER_DATA_ONE_FINAL_EGYPT_FIXED.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ("_SPEC_DATA_ONE.big", "VERIFY_REPORT.txt", "README_INSTALL.txt"):
            zf.write(OUT_DIR / name, name)

    print("OK", out_big, sha)
    print("EGYPT", egypt_sha)
    print("ZIP", zpath, sha256_file(zpath))
    print(report)
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
