#!/usr/bin/env python3
"""FINAL packaging only. Frozen EU flag payload onto locked baseline.

Does not regenerate W3Ds or re-patch INI logic.
"""
from __future__ import annotations

import hashlib
import shutil
import struct
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/NK_POWERPLANT_FLAG/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/BUILDING_FLAG_SIZE_CC/_SPEC_ART_ONE.big")
EXPECTED_SRC_DATA = "c035a6c1dabe6dfd064cfa4462d55c7c06bc1691117a5a573e29fa05bc549cad"
EXPECTED_SRC_ART = "b40a8e686df17ffbb538be22ecb17c783a9b6913ab0d3af0d9ef3ed4ebdf7191"
FROZEN_PAYLOAD = Path("/workspace/patch/Release/EU_BUILDING_FLAGS/payload")
STAGING = Path("/tmp/eu_final_clean_staging")
RELEASE = Path("/workspace/patch/Release/EUROPEAN_BUILDING_FLAGS_FINAL")

DATA_FILES = [
    r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\CommandCenter.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\Camp.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\PowerStation.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\SupplyCenter.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\CommandCenter.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\Camp.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\PowerStation.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\SupplyCenter.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\CommandCenter.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\Camp.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\PowerStation.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\SupplyCenter.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Buildings\CommandCenter.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Buildings\Camp.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Buildings\PowerStation.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Buildings\SupplyCenter.ini",
    r"Data\INI\Object\Specter\French Armed Forces\Buildings\CommandCenter.ini",
    r"Data\INI\Object\Specter\French Armed Forces\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\French Armed Forces\Buildings\Camp.ini",
    r"Data\INI\Object\Specter\French Armed Forces\Buildings\PowerStation.ini",
    r"Data\INI\Object\Specter\French Armed Forces\Buildings\SupplyCenter.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Buildings\CommandCenter.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Buildings\Camp.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Buildings\PowerStation.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Buildings\SupplyCenter.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\CommandCenter.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\Camp.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\PowerStation.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\SupplyCenter.ini",
]

ART_FILES = [
    rf"Art\W3D\{p}__{p}Flag_Hs{k}.W3D"
    for p in ("TR", "IT", "SE", "UK", "FR", "DE", "UA")
    for k in ("CU", "WF", "CP", "PP", "SC")
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(name: str) -> str:
    return name.replace("/", "\\")


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries):
    header_size = 16
    encoded = [n.encode("latin1", errors="replace") for n, _ in entries]
    for nb in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    out = bytearray(b"BIGF")
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries, target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 path, got {len(hits)}")
    return hits[0]


def main() -> int:
    if sha256_file(SRC_DATA) != EXPECTED_SRC_DATA:
        raise SystemExit("baseline DATA SHA mismatch")
    if sha256_file(SRC_ART) != EXPECTED_SRC_ART:
        raise SystemExit("baseline ART SHA mismatch")

    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir(parents=True)

    for rel in DATA_FILES + ART_FILES:
        src = FROZEN_PAYLOAD / rel.replace("\\", "/")
        if not src.is_file():
            raise SystemExit(f"frozen payload missing: {src}")
        dest = STAGING / rel.replace("\\", "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
    staged = [p for p in STAGING.rglob("*") if p.is_file()]
    if len(staged) != 70:
        raise SystemExit(f"clean staging file count {len(staged)}")

    data = read_big(SRC_DATA)
    art = read_big(SRC_ART)
    orig_data_names = [n for n, _ in data]
    orig_art_names = [n for n, _ in art]
    orig_art_map = {norm(n).lower(): b for n, b in art}
    orig_data_map = {norm(n).lower(): b for n, b in data}

    for rel in DATA_FILES:
        blob = (STAGING / rel.replace("\\", "/")).read_bytes()
        idx = find_index(data, rel)
        data[idx] = (data[idx][0], blob)

    for rel in ART_FILES:
        key = norm(rel).lower()
        if any(norm(n).lower() == key for n, _ in art):
            raise SystemExit(f"ART collision: {rel}")
        blob = (STAGING / rel.replace("\\", "/")).read_bytes()
        if len(blob) != 20341:
            raise SystemExit(f"W3D size {rel} {len(blob)}")
        art.append((rel, blob))

    if [n for n, _ in data] != orig_data_names:
        raise SystemExit("DATA path order changed")
    change_set = {norm(p).lower() for p in DATA_FILES}
    for n, b in data:
        key = norm(n).lower()
        if key in change_set:
            continue
        if b != orig_data_map[key]:
            raise SystemExit(f"unrelated DATA change: {n}")
    if [n for n, _ in art][: len(orig_art_names)] != orig_art_names:
        raise SystemExit("existing ART order changed")
    for n, b in zip(orig_art_names, (b for _, b in art[: len(orig_art_names)])):
        if b != orig_art_map[norm(n).lower()]:
            raise SystemExit(f"existing ART modified: {n}")

    if RELEASE.exists():
        shutil.rmtree(RELEASE)
    RELEASE.mkdir(parents=True)
    data_out = RELEASE / "_SPEC_DATA_ONE.big"
    art_out = RELEASE / "_SPEC_ART_ONE.big"
    data_out.write_bytes(build_big_ordered(data))
    art_out.write_bytes(build_big_ordered(art))
    dsha = sha256_file(data_out)
    asha = sha256_file(art_out)
    print(f"DATA {data_out.stat().st_size} {dsha}")
    print(f"ART  {art_out.stat().st_size} {asha}")
    print(f"DATA_FILES {len(data)} ART_FILES {len(art)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
