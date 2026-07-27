#!/usr/bin/env python3
"""Minimal Egypt_MilitaryHQ-only test package (no other countries)."""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_EGYPT_MILITARYHQ_TEST"
EG_PATH = (
    r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_MilitaryHQ.ini"
)
FIXED_SRC = (
    ROOT
    / "Data"
    / "INI"
    / "Object"
    / "Specter"
    / "Egyptian Armed Forces"
    / "Buildings"
    / "Egypt_MilitaryHQ.ini"
)
PREV_PKG = ROOT / "Release" / "SPECTER_EGYPT_MILITARYHQ_FIX" / "_SPEC_DATA_ONE.big"
BROKEN_SHA = "5ee7d870b9bdd0b20b8f38ec7e2071226fde174b4ed48ed6118fcf49c08d2b7b"


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
    blobs, index, cursor = [], [], header_size
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


def main() -> int:
    if not VENDOR.is_file() or not FIXED_SRC.is_file():
        raise SystemExit("missing vendor or fixed Egypt_MilitaryHQ.ini")

    entries = parse_big(VENDOR)
    by = {knorm(n): (n, b) for n, b in entries}
    broken = by[knorm(EG_PATH)][1]
    if sha256_bytes(broken) != BROKEN_SHA:
        print("WARN: vendor Egypt_MilitaryHQ sha changed:", sha256_bytes(broken))

    fixed_bytes = FIXED_SRC.read_bytes()
    if PREV_PKG.is_file():
        for n, b in parse_big(PREV_PKG):
            if knorm(n) == knorm(EG_PATH):
                fixed_bytes = b
                break

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "Egypt_MilitaryHQ.ini").write_bytes(fixed_bytes)
    loose = (
        OUT
        / "Data"
        / "INI"
        / "Object"
        / "Specter"
        / "Egyptian Armed Forces"
        / "Buildings"
        / "Egypt_MilitaryHQ.ini"
    )
    loose.parent.mkdir(parents=True, exist_ok=True)
    loose.write_bytes(fixed_bytes)
    FIXED_SRC.write_bytes(fixed_bytes)
    write_big(OUT / "_SPECTER_EGYPT_MILITARYHQ_TEST.big", [(EG_PATH, fixed_bytes)])

    fixed = fixed_bytes.decode("utf-8", "replace")
    code_only = "\n".join(line.split(";", 1)[0] for line in fixed.splitlines())
    assert re.search(r"(?m)^Object\s+Egypt_MilitaryHQ\b", fixed)
    assert re.search(r"(?m)^\s*Side\s*=\s*Egypt\b", fixed)
    assert "Egypt_MilitaryHQCommandSet" in fixed
    assert "US_Command" in fixed and "us_commandcenter" in fixed
    assert "US_E3G_AWACS" in fixed
    assert not re.search(r"(?i)\b(?:iraq\w*|irq_\w*|adnan\w*)\b", code_only)
    assert all(ord(c) < 128 for c in fixed)

    report = (
        "SPECTER EGYPT MILITARYHQ TEST — VERIFY REPORT\n"
        "============================================================\n"
        "VERDICT: PASS\n"
        "Scope: Egypt_MilitaryHQ.ini ONLY\n"
        f"Broken vendor SHA256: {sha256_bytes(broken)}\n"
        f"Fixed SHA256:         {sha256_bytes(fixed_bytes)}\n"
        "Other countries: untouched\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT / "README_INSTALL.txt").write_text(
        "MINIMAL Egypt_MilitaryHQ fix only.\n"
        "Copy _SPECTER_EGYPT_MILITARYHQ_TEST.big into Data\\.\n"
        "Keep _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big.\n",
        encoding="utf-8",
    )
    zpath = OUT / "_SPECTER_EGYPT_MILITARYHQ_TEST.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in (
            "_SPECTER_EGYPT_MILITARYHQ_TEST.big",
            "CRASH_FORENSIC_REPORT.txt",
            "VERIFY_REPORT.txt",
            "README_INSTALL.txt",
        ):
            p = OUT / name
            if p.is_file():
                zf.write(p, name)
        zf.write(
            loose,
            "Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_MilitaryHQ.ini",
        )
    print(report)
    print("ZIP", zpath, sha256_file(zpath))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
