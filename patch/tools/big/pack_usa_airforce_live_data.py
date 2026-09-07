#!/usr/bin/env python3
"""Pack DATA-only BIG for the live USA CommandSet fix.

Starts from the previous USA expansion DATA big. Updates building
CommandSet pointers back to the real INIZH names. Removes unused
unique USA CommandSet/CommandButton files so they cannot redefine
names already in the winning INIZH/INIZHZ/loose files.
"""

from __future__ import annotations

import hashlib
import struct
import zipfile
from pathlib import Path

STOCK_SKIP = {
    "data\\ini\\weapon.ini",
    "data\\ini\\commandbutton.ini",
    "data\\ini\\commandset.ini",
    "data\\ini\\armor.ini",
    "data\\ini\\locomotor.ini",
}

USA_OVERLAYS = [
    "Data/INI/Upgrade_USA_AirForce.ini",
    "Data/INI/Weapon_USA_AirForce.ini",
    "Data/INI/Object/Specter/United States Of America/Airforce/AmericaJetAuterF22.ini",
    "Data/INI/Object/Specter/United States Of America/Airforce/F35C.ini",
    "Data/INI/Object/Specter/United States Of America/Airforce/F35C_AA.ini",
    "Data/INI/Object/Specter/United States Of America/Buildings/Airfield.ini",
    "Data/INI/Object/Specter/United States Of America/Buildings/CommandCenter.ini",
    "Data/INI/Object/Specter/United States Of America/Buildings/America_LargeAirBase.ini",
    "Data/INI/Object/Specter/United States Of America/AmericaJetV22Visual.ini",
    "Data/INI/Object/Specter/United States Of America/AmericaJetB21Clean.ini",
]

REMOVE = {
    "data\\ini\\commandset_usa_airforce.ini",
    "data\\ini\\commandbutton_usa_airforce.ini",
}


def norm_key(name: str) -> str:
    return name.replace("/", "\\").lower()


def read_big(path: Path):
    data = path.read_bytes()
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    offset = header_size
    index = []
    blobs = []
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def main() -> int:
    src = Path("/tmp/usa_airforce_expansion/_SPEC_DATA_ONE.big")
    patch = Path("/workspace/patch")
    out_dir = Path("/tmp/usa_airforce_live")
    out_dir.mkdir(parents=True, exist_ok=True)

    entries, raw = read_big(src)
    data_map: dict[str, tuple[str, bytes]] = {}
    order: list[str] = []
    for name, off, size in entries:
        key = norm_key(name)
        if key in REMOVE:
            print(f"REMOVE {name}")
            continue
        if key not in data_map:
            order.append(key)
        data_map[key] = (name.replace("/", "\\"), raw[off : off + size])

    for rel in USA_OVERLAYS:
        path = patch / rel
        if not path.is_file():
            raise SystemExit(f"missing overlay {path}")
        big_path = rel.replace("/", "\\")
        key = norm_key(big_path)
        if key in STOCK_SKIP:
            raise SystemExit(f"refused to pack stock core {big_path}")
        content = path.read_bytes()
        if key in data_map:
            old_name, old = data_map[key]
            if old != content:
                data_map[key] = (old_name, content)
                print(f"UPDATE {big_path}")
        else:
            data_map[key] = (big_path, content)
            order.append(key)
            print(f"ADD    {big_path}")

    final: dict[str, bytes] = {}
    seen = set()
    for key in order:
        if key not in data_map:
            continue
        name, content = data_map[key]
        final[name] = content
        seen.add(key)
    for key, (name, content) in sorted(data_map.items()):
        if key not in seen:
            final[name] = content

    out_big = out_dir / "_SPEC_DATA_ONE.big"
    blob = build_big(final)
    out_big.write_bytes(blob)
    print(f"DATA files={len(final)} size={len(blob)} sha256={hashlib.sha256(blob).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
