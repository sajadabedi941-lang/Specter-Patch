#!/usr/bin/env python3
"""Build and statically validate the SPECTER camera-zoom override archive.

Zero Hour mounts every *.big beside generals.exe, but duplicate internal paths
keep the first archive that registered them (loadBigFilesFromDirectory is
called with overwrite = false). Replacing Data\\INI\\GameData.ini inside a
later archive, including one named z_*, does not change the parsed file.

TheWritableGlobalData then loads Data\\INI\\GameData.ini and, after that file,
every *.ini in Data\\INI\\GameData\\ with INI_LOAD_OVERWRITE. A new file in
that directory is the value the running game actually applies.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
import sys
from pathlib import Path


OVERRIDE_PATH = "Data\\INI\\GameData\\ZZZZZZZZ_SPECTER_CameraZoom.ini"
GAMEDATA_PATH = "Data\\INI\\GameData.ini"
EXPECTED_MAX = 620.0
RETAIL_MAX = 310.0


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _content in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    out = bytearray(b"BIGF")
    # size is filled after the payload length is known
    out += struct.pack(">III", 0, len(items), header_size)
    offset = header_size
    blobs: list[bytes] = []
    for name, content in items:
        content = bytes(content)
        out += struct.pack(">II", offset, len(content))
        out += name.encode("latin1") + b"\x00"
        blobs.append(content)
        offset += len(content)
    for blob in blobs:
        out += blob
    struct.pack_into(">I", out, 4, len(out))
    return bytes(out)


def read_big(path: Path) -> list[tuple[str, int, int, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not a BIGF archive: {path}")
    # Retail stores the archive size little-endian and the count/header big-endian.
    # FinalBIG and this packer store all three big-endian. The game byte-swaps the
    # count and entry fields and does not require the size field to match.
    count, header = struct.unpack(">II", data[8:16])
    off = 16
    entries: list[tuple[str, int, int, bytes]] = []
    for _ in range(count):
        entry_off, entry_size = struct.unpack(">II", data[off : off + 8])
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        if entry_size and (entry_off + entry_size > len(data)):
            raise SystemExit(f"entry out of range in {path}: {name}")
        entries.append((name, entry_off, entry_size, data[entry_off : entry_off + entry_size] if entry_size else b""))
    if off > header:
        raise SystemExit(f"header size {header} does not cover the name table in {path}")
    return entries


def camera_values(blob: bytes) -> list[tuple[str, str]]:
    """Return (key, value) assignments inside GameData blocks. Comments are dropped."""
    text = blob.replace(b"\r\n", b"\n").replace(b"\r", b"\n").decode("latin1")
    values: list[tuple[str, str]] = []
    in_block = False
    for raw in text.split("\n"):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if not in_block:
            if line == "GameData":
                in_block = True
            continue
        if line == "End":
            in_block = False
            continue
        if "=" not in line:
            raise SystemExit(f"unparsed GameData line: {line!r}")
        key, value = (part.strip() for part in line.split("=", 1))
        values.append((key, value))
    return values


def max_camera_height(blob: bytes) -> float | None:
    found = None
    for key, value in camera_values(blob):
        if key == "MaxCameraHeight":
            found = float(value)
    return found


def stricmp_key(name: str) -> str:
    """Sort key for AsciiString::compareNoCase, which is _stricmp.

    Letters are uppercased. '_' (0x5F) stays above 'Z', so INIZH.big is
    ordered before _SPEC_DATA_ONE.big and before z_SPECTER_CameraZoom.big.
    """
    return "".join(ch.upper() if "a" <= ch <= "z" else ch for ch in name)


def simulate(archives: list[tuple[str, list[tuple[str, bytes]]]]) -> dict[str, tuple[str, bytes]]:
    """First archive in case-insensitive name order keeps each internal path."""
    owned: dict[str, tuple[str, bytes]] = {}
    for archive_name, entries in sorted(archives, key=lambda item: stricmp_key(item[0])):
        for internal, blob in entries:
            key = internal.replace("/", "\\").casefold()
            owned.setdefault(key, (archive_name, blob))
    return owned


def directory_inis(owned: dict[str, tuple[str, bytes]], directory: str) -> list[tuple[str, str, bytes]]:
    prefix = directory.replace("/", "\\").casefold().rstrip("\\") + "\\"
    found = []
    for key, (archive_name, blob) in owned.items():
        if key.startswith(prefix) and key.endswith(".ini") and "\\" not in key[len(prefix) :]:
            found.append((key, archive_name, blob))
    found.sort(key=lambda item: stricmp_key(item[0]))
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--game-big", type=Path, action="append", default=[])
    args = parser.parse_args()

    source = args.source.read_bytes()
    if b"\t" in source:
        raise SystemExit("override INI contains a tab; Zero Hour rejects tabs")
    assignments = camera_values(source)
    if assignments != [("MaxCameraHeight", "620.0")]:
        raise SystemExit(f"override must set only MaxCameraHeight = 620.0, got {assignments}")

    archive = build_big({OVERRIDE_PATH: source})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(archive)

    packed = read_big(args.out)
    if len(packed) != 1 or packed[0][0] != OVERRIDE_PATH:
        raise SystemExit(f"packed archive entries are { [item[0] for item in packed] }")
    if packed[0][3] != source:
        raise SystemExit("packed override bytes do not match the source INI")

    archives: list[tuple[str, list[tuple[str, bytes]]]] = []
    for game_big in args.game_big:
        entries = [(name, blob) for name, _off, _size, blob in read_big(game_big)]
        archives.append((game_big.name, entries))
    archives.append((args.out.name, [(packed[0][0], packed[0][3])]))

    # The previous package replaced Data\INI\GameData.ini inside a z_ archive.
    # That archive sorts last and is mounted with overwrite disabled, so its
    # copy of an existing path is never opened.
    archives.append(
        (
            "z_SPECTER_CameraZoom_replaced_gamedata.big",
            [(GAMEDATA_PATH, b"GameData\r\n  MaxCameraHeight = 999.0\r\nEnd\r\n")],
        )
    )

    print("mount_order=" + ",".join(name for name, _entries in sorted(archives, key=lambda item: stricmp_key(item[0]))))
    for archive_name, entries in sorted(archives, key=lambda item: stricmp_key(item[0])):
        for internal, blob in entries:
            if internal.replace("/", "\\").casefold() == GAMEDATA_PATH.casefold():
                print(f"contains_GameData.ini={archive_name} MaxCameraHeight={max_camera_height(blob)}")

    owned = simulate(archives)
    winner_name, winner_blob = owned[GAMEDATA_PATH.casefold()]
    winner_max = max_camera_height(winner_blob)
    if winner_name == args.out.name:
        raise SystemExit("override archive unexpectedly owns Data\\INI\\GameData.ini")
    if winner_max != RETAIL_MAX:
        raise SystemExit(
            f"live GameData.ini is {winner_name} MaxCameraHeight={winner_max}, expected {RETAIL_MAX}"
        )

    extra = directory_inis(owned, "Data\\INI\\GameData")
    if [item[0] for item in extra] != [OVERRIDE_PATH.casefold()]:
        raise SystemExit(f"unexpected Data\\INI\\GameData directory files: {extra}")
    if extra[0][1] != args.out.name:
        raise SystemExit(f"override directory file is owned by {extra[0][1]}")

    # Parse order: the winning GameData.ini, then directory INIs in sorted order.
    effective = winner_max
    for _key, _archive_name, blob in extra:
        override = max_camera_height(blob)
        if override is not None:
            effective = override
    if effective != EXPECTED_MAX:
        raise SystemExit(f"effective MaxCameraHeight is {effective}, expected {EXPECTED_MAX}")

    digest = hashlib.sha256(archive).hexdigest()
    print(f"archive={args.out}")
    print(f"sha256={digest}")
    print(f"bytes={len(archive)}")
    print(f"internal={OVERRIDE_PATH}")
    print(f"first_wins_gamedata={winner_name} MaxCameraHeight={winner_max}")
    print(f"directory_override={extra[0][1]}::{OVERRIDE_PATH}")
    print(f"effective_MaxCameraHeight={effective}")
    print("static_load_simulation=PASS")
    print("runtime_game_test=NOT_RUN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
