#!/usr/bin/env python3
"""DATA-only factory integration pack.

Starts from the current 8-missile live DATA BIG.
Replaces only Data\\INI\\CommandSet_Iraq_MissileFactory.ini.
Does not touch ART, Objects, Weapons, Projectiles, or CommandButton.ini.
"""
from __future__ import annotations

import hashlib
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_STRATEGIC_MISSILES/_SPEC_DATA_ONE.big"
PATCH_SET = ROOT / "patch/Data/INI/CommandSet_Iraq_MissileFactory.ini"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_INTEGRATION"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes):
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index = []
    blobs = []
    offset = header_size
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
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def to_crlf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing current 8-missile DATA {SRC_DATA}")
    if not PATCH_SET.is_file():
        raise SystemExit(f"missing {PATCH_SET}")
    OUT.mkdir(parents=True, exist_ok=True)

    src_bytes = SRC_DATA.read_bytes()
    data_map = parse_big(src_bytes)

    # preserve missile/object INIs and core CommandButton.ini
    frozen = [
        "Data\\INI\\CommandButton.ini",
        "Data\\INI\\Object\\Specter\\Iraq Army\\Wheeled\\Iraq_StrategicMissiles_New.ini",
        "Data\\INI\\Weapon_Iraq_StrategicMissiles.ini",
        "Data\\INI\\Object\\Specter\\Iraq Army\\Wheeled\\9P117.ini",
        "Data\\INI\\Object\\Specter\\Iraq Army\\Wheeled\\AlNida.ini",
        "Data\\INI\\Object\\Specter\\Iraq Army\\Buildings\\Iraq_MissileFactory.ini",
    ]
    before = {k: data_map[k] for k in frozen}

    extra = to_crlf(PATCH_SET.read_bytes())
    if b"CommandSet Iraq_VT72BCommandSet" in extra:
        raise SystemExit("extra CommandSet must not redefine Iraq_VT72BCommandSet")
    if extra.count(b"CommandSet Iraq_MissileFactoryCommandSet") != 1:
        raise SystemExit("Iraq_MissileFactoryCommandSet count != 1")
    data_map["Data\\INI\\CommandSet_Iraq_MissileFactory.ini"] = extra

    for k, v in before.items():
        if data_map[k] != v:
            raise SystemExit(f"refusing mutation of {k}")

    data_path = OUT / "_SPEC_DATA_ONE.big"
    data_path.write_bytes(build_big(data_map))
    zip_path = OUT / "SPECTER_IRAQ_FACTORY_INTEGRATION.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        zf.write(data_path, arcname="_SPEC_DATA_ONE.big")
    dhash, zhash = sha256(data_path), sha256(zip_path)
    (OUT / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  {data_path.stat().st_size}  SHA256={dhash}\n"
        f"SPECTER_IRAQ_FACTORY_INTEGRATION.zip  {zip_path.stat().st_size}  SHA256={zhash}\n",
        encoding="ascii",
    )
    print("DATA", data_path.stat().st_size, dhash)
    print("ZIP", zip_path.stat().st_size, zhash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
