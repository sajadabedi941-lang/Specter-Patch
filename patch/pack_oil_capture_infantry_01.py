#!/usr/bin/env python3
"""Pack-only: oil-capture overlays onto the validated Next-14 DATA BIG.

Replaces the seven audited NATO G36 object paths and appends the Class 2
CommandSet last-win file. Does not rewrite source INIs. Does not replace
Weapon.ini / CommandSet.ini / CommandButton.ini from workspace copies.
Does not touch Japan / South Korea / Vietnam infantry.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/FIGHTER_ROSTER_NEXT14/_SPEC_DATA_ONE.big")
EXPECTED_SRC_SHA = "0528e90d4627e7949c683847b00df97626bdc8e36d4f8cd022dae5738856d71a"
ROOT = Path("/workspace/patch")
INI = ROOT / "Data" / "INI"
RELEASE = ROOT / "Release" / "OIL_CAPTURE_INFANTRY"

REPLACE = [
    r"Data\INI\Object\Specter\Swedish Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\French Armed Forces\Infantry\Rifleman_G36.ini",
]

APPEND = [
    (
        r"Data\INI\CommandSet_ZZZZ_OilCapture_Class2.ini",
        INI / "CommandSet_ZZZZ_OilCapture_Class2.ini",
    ),
]

FROZEN = [
    r"Data\INI\Weapon.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\Upgrade.ini",
    r"Data\INI\SpecialPower.ini",
    r"Data\INI\Object\CivilianBuilding.ini",
    r"Data\INI\Object\Specter\United States Of America\Infantry\Rifleman_M4.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Infantry\Japan_Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Infantry\SouthKorea_Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Vietnam People's Army\Infantry\Rifleman.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Infantry\Rifleman.ini",
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Infantry\Rifleman.ini",
    r"Data\INI\Object\Specter\Libyan Armed Forces\Infantry\Rifleman.ini",
    r"Data\INI\Object\Specter\South African National Defence Force\Infantry\Rifleman.ini",
    r"Data\INI\CommandButton_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\CommandButton_ZZZZ_FighterRoster_SAUAESYINPK.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_SAUAESYINPK.ini",
    r"Data\INI\CommandSet_ZZZZ_JapanSKVietnam_Capture.ini",
    r"Data\INI\CommandButton_ZZZZ_JapanSKVietnam_Capture.ini",
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
    return read_big_from_bytes(data)


def read_big_from_bytes(data: bytes):
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
    encoded = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
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


def ws_path(packed: str) -> Path:
    rel = packed.replace("\\", "/")
    if rel.lower().startswith("data/ini/"):
        return INI / rel[len("Data/INI/") :]
    raise SystemExit(f"unexpected packed path {packed}")


def main() -> int:
    if sha256_file(SRC_DATA) != EXPECTED_SRC_SHA:
        raise SystemExit("validated Next-14 DATA SHA mismatch")

    entries = read_big(SRC_DATA)
    orig = list(entries)
    orig_map = {norm(n).lower(): (n, b) for n, b in orig}

    replaced = []
    for packed in REPLACE:
        src = ws_path(packed)
        if not src.is_file():
            raise SystemExit(f"missing overlay {src}")
        blob = src.read_bytes()
        idx = find_index(entries, packed)
        old_name, old_blob = entries[idx]
        if blob == old_blob:
            raise SystemExit(f"overlay identical to baseline: {packed}")
        entries[idx] = (old_name, blob)
        replaced.append(packed)

    for packed, src in APPEND:
        if any(norm(n).lower() == packed.lower() for n, _ in entries):
            raise SystemExit(f"already packed: {packed}")
        if not src.is_file():
            raise SystemExit(f"missing append {src}")
        entries.append((packed, src.read_bytes()))

    for p in FROZEN:
        idx = find_index(entries, p)
        if entries[idx][1] != orig_map[norm(p).lower()][1]:
            raise SystemExit(f"frozen path changed: {p}")

    orig_names = [n for n, _ in orig]
    new_names = [n for n, _ in entries]
    if new_names[: len(orig_names)] != orig_names:
        raise SystemExit("packed path order prefix changed")
    added = new_names[len(orig_names) :]
    if [norm(x) for x in added] != [a[0] for a in APPEND]:
        raise SystemExit(f"unexpected added paths: {added}")

    replace_set = {norm(p).lower() for p in REPLACE}
    for n, b in entries[: len(orig)]:
        if norm(n).lower() in replace_set:
            continue
        if b != orig_map[norm(n).lower()][1]:
            raise SystemExit(f"unintended rewrite: {n}")

    data_blob = build_big_ordered(entries)
    rebuilt = read_big_from_bytes(data_blob)
    if [n for n, _ in rebuilt] != new_names:
        raise SystemExit("rebuild order drifted")

    RELEASE.mkdir(parents=True, exist_ok=True)
    out = RELEASE / "_SPEC_DATA_ONE.big"
    out.write_bytes(data_blob)
    sha = sha256_file(out)
    (RELEASE / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {sha}\n"
        f"SOURCE_DATA_SHA {EXPECTED_SRC_SHA}\n"
        f"ART unchanged (not packed)\n"
        f"FILE_COUNT {len(entries)}\n"
        f"BYTES {out.stat().st_size}\n",
        encoding="utf-8",
    )
    (RELEASE / "PACKED_FILES.txt").write_text(
        "REPLACED\n"
        + "\n".join(f"  {p}" for p in replaced)
        + "\nAPPENDED\n"
        + "\n".join(f"  {p}" for p, _ in APPEND)
        + "\nPRESERVED_NEXT14 = YES\n"
        + "PRESERVED_SA_UAE_SY_IN_PK = YES\n"
        + "ART_CHANGED = NO\n",
        encoding="utf-8",
    )
    print("PACKED", out, out.stat().st_size, sha, "files", len(entries))
    print("REPLACED", len(replaced), "APPENDED", len(APPEND))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
