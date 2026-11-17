#!/usr/bin/env python3
"""Replace packed Object USAPAC3.ini only. ART TWO / CommandSet / other objects untouched."""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
PATCH_OBJ = ROOT / "patch/Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3.ini"
DATA_PATH = ROOT / "docs/specter-usapac3/merged/_SPEC_DATA_ONE.big"
KEY = "data\\ini\\object\\specter\\patchsystems\\airdefense\\usapac3.ini"


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        fail(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos = end + 1
        entries.append((name, off, size))
    return data, entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin-1")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
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
        out += name.encode("latin-1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def main() -> int:
    if not PATCH_OBJ.is_file():
        fail("missing overlay USAPAC3.ini")
    if not DATA_PATH.is_file():
        fail("missing merged DATA")
    new = PATCH_OBJ.read_bytes()
    txt = new.decode("latin-1")
    if "AttachToBoneInAnotherModule" in txt or "UsaPac3Car_w" in txt:
        fail("overlay still has attach or UsaPac3Car_w")
    if "PRISTINE_BONE_POS_IN_FINAL_FRAME" in txt or "WeaponLaunchBone" in txt:
        fail("overlay still has pristine/launch-bone Draw")
    if "Animation         = UsaPac3F" in txt or "Animation         = UsaPac3F_d" in txt:
        fail("overlay still names empty UsaPac3F animation")
    if "BuildCost           = 3876" not in txt or "BuildTime           = 18.6" not in txt:
        fail("cost/time changed")
    if txt.count("Object USAPAC3\n") + txt.count("Object USAPAC3\r\n") != 1:
        if "Object USAPAC3" not in txt.split("DisplayName")[0]:
            fail("object header")
    raw, entries = read_big(DATA_PATH)
    amap = {}
    found = None
    for name, off, size in entries:
        key = name.replace("/", "\\").lower()
        blob = raw[off : off + size]
        if key == KEY:
            found = name
            blob = new
        if key in amap:
            fail(f"duplicate path {name}")
        amap[name] = blob
    if found is None:
        fail("packed USAPAC3.ini not found")
    out = build_big(amap)
    DATA_PATH.write_bytes(out)
    print(f"replaced {found} bytes {len(new)}")
    print(f"DATA entries={len(amap)} bytes={len(out)} sha256={hashlib.sha256(out).hexdigest()}")
    print(f"file sha256={sha_file(DATA_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
