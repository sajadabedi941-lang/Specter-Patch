#!/usr/bin/env python3
"""Pack-only: copy USA RadarUpgrade TriggeredBy onto 7 country GM406 radars.

Replaces seven packed GM406.ini files extracted from the validated oil-capture
soldier DATA BIG. Does not rewrite USA radar, Weapon.ini, CommandButton.ini,
CommandSet.ini, or oil-capture overlays.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/OIL_CAPTURE_SOLDIER_COMMAND/_SPEC_DATA_ONE.big")
EXPECTED_SRC_SHA = "817438bd67088b42db28cf65072c385f7569bf6183a14cd6b40982cfbf6b8be6"
EXPECTED_SRC_SIZE = 366168990
ROOT = Path("/workspace/patch")
PAYLOAD = ROOT / "Release" / "NATO_RADAR_USA_REF" / "payload"
RELEASE = ROOT / "Release" / "NATO_RADAR_USA_REF"

REPLACE = [
    r"Data\INI\Object\Specter\German Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\French Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\GM406.ini",
]

FROZEN = [
    r"Data\INI\Weapon.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\Upgrade.ini",
    r"Data\INI\SpecialPower.ini",
    r"Data\INI\Object\CivilianBuilding.ini",
    r"Data\INI\Object\Specter\United States Of America\Buildings\AN_FPS117.ini",
    r"Data\INI\Object\Specter\United States Of America\Infantry\Rifleman_M4.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_SoldierCommand.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_BarracksAndRifles.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_Class2.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_SAUAESYINPK.ini",
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


def payload_path(packed: str) -> Path:
    return PAYLOAD / packed.replace("\\", "/")


def main() -> int:
    if sha256_file(SRC_DATA) != EXPECTED_SRC_SHA:
        raise SystemExit("validated soldier-command DATA SHA mismatch")
    if SRC_DATA.stat().st_size != EXPECTED_SRC_SIZE:
        raise SystemExit("validated soldier-command DATA size mismatch")

    entries = read_big(SRC_DATA)
    orig = list(entries)
    orig_map = {norm(n).lower(): (n, b) for n, b in orig}

    replaced = []
    for packed in REPLACE:
        src = payload_path(packed)
        if not src.is_file():
            raise SystemExit(f"missing payload {src}")
        blob = src.read_bytes()
        idx = find_index(entries, packed)
        old_name, old_blob = entries[idx]
        if blob == old_blob:
            raise SystemExit(f"payload identical to baseline: {packed}")
        if b"TriggeredBy   = Upgrade_AmericaRadar" not in blob:
            raise SystemExit(f"payload missing RadarUpgrade TriggeredBy: {packed}")
        entries[idx] = (old_name, blob)
        replaced.append(packed)

    for p in FROZEN:
        idx = find_index(entries, p)
        if entries[idx][1] != orig_map[norm(p).lower()][1]:
            raise SystemExit(f"frozen path changed: {p}")

    orig_names = [n for n, _ in orig]
    new_names = [n for n, _ in entries]
    if new_names != orig_names:
        raise SystemExit("packed path set/order changed")

    replace_set = {norm(p).lower() for p in REPLACE}
    for n, b in entries:
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
        + "\nAPPENDED\n  NONE\n"
        + "USA_RADAR_CHANGED = NO\n"
        + "ART_CHANGED = NO\n",
        encoding="utf-8",
    )
    print("PACKED", out, out.stat().st_size, sha, "files", len(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
