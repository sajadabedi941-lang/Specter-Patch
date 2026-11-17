#!/usr/bin/env python3
"""Strip empty ANIMATION chunks from UsaPac3F / UsaPac3F_d.

Live deployed TELs (US_M1120_A, Irq_Fahad3_A) have no ANIMATION chunk.
UsaPac3F has a 101-frame header and zero channels. Naming that clip in
Draw preloads it at object create. After this strip the files match the
live deployed-TEL layout: hierarchy + meshes + HLOD, no anim blob.

Reversible: originals are copied to docs/specter-usapac3/backup/w3d_empty_anim/.
"""
from __future__ import annotations

import hashlib
import shutil
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
ART_DIR = ROOT / "patch/Art/W3D"
BAK = ROOT / "docs/specter-usapac3/backup/w3d_empty_anim"
ART2 = ROOT / "docs/specter-usapac3/merged/_SPEC_ART_TWO.big"
CON = 0x80000000
TARGETS = ["UsaPac3F.W3D", "UsaPac3F_d.W3D"]


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def strip_animation(blob: bytes) -> bytes:
    out = bytearray()
    pos = 0
    removed = 0
    while pos + 8 <= len(blob):
        cid, raw = struct.unpack_from("<II", blob, pos)
        size = raw & 0x7FFFFFFF
        pe = pos + 8 + size
        if pe > len(blob):
            fail(f"truncated chunk {hex(cid)} at {pos}")
        if cid == 0x200:  # W3D_CHUNK_ANIMATION (container)
            removed += 1
            pos = pe
            continue
        out += blob[pos:pe]
        pos = pe
    if pos != len(blob):
        fail(f"trailing bytes {len(blob) - pos}")
    if removed == 0:
        return blob  # already stripped
    if removed != 1:
        fail(f"expected one ANIMATION container, removed {removed}")
    return bytes(out)


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        fail(f"not BIGF {path}")
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
    BAK.mkdir(parents=True, exist_ok=True)
    stripped: dict[str, bytes] = {}
    for fname in TARGETS:
        src = ART_DIR / fname
        if not src.is_file():
            fail(f"missing {src}")
        raw = src.read_bytes()
        bak = BAK / fname
        if not bak.is_file():
            shutil.copy2(src, bak)
            print(f"backup {fname} sha={sha_bytes(raw)} bytes={len(raw)}")
        else:
            print(f"backup exists {fname} sha={sha_bytes(bak.read_bytes())}")
        new = strip_animation(raw)
        if new != raw:
            src.write_bytes(new)
            print(f"stripped {fname} {len(raw)} -> {len(new)} sha={sha_bytes(new)}")
        else:
            print(f"already stripped {fname} bytes={len(new)} sha={sha_bytes(new)}")
        stripped[fname] = new

    raw, entries = read_big(ART2)
    amap = {}
    replaced = []
    for name, off, size in entries:
        key = name.replace("/", "\\").lower()
        blob = raw[off : off + size]
        base = name.replace("/", "\\").rsplit("\\", 1)[-1]
        if base in stripped:
            blob = stripped[base]
            replaced.append(name)
        if key in amap:
            fail(f"duplicate {name}")
        amap[name] = blob
    replaced_bases = sorted(n.replace("/", "\\").rsplit("\\", 1)[-1] for n in replaced)
    if replaced_bases != sorted(TARGETS):
        fail(f"ART TWO replace set {replaced}")
    out = build_big(amap)
    ART2.write_bytes(out)
    print(f"ART TWO entries={len(amap)} bytes={len(out)} sha256={sha_bytes(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
