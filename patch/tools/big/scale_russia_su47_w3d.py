#!/usr/bin/env python3
"""Scale only RussiaJetSu47Berkut ART (RUSU-47*.W3D) to Su-35/Su-57 visual size.

Does not touch object INI, weapons, cost, or other models.
Uses MESH_HEADER3 + VERTICES + hierarchy pivot translations only.
"""
from __future__ import annotations

import struct
from pathlib import Path

W3D_VERTICES = 0x00000002
W3D_MESH_HEADER3 = 0x0000001F
W3D_PIVOTS = 0x00000102

# Measured from packed RUS_SU57.W3D / current RUSU-47.W3D vertex AABBs.
SU47_SRC_MAX = 36.85
SU57_MAX = 61.62
SCALE = SU57_MAX / SU47_SRC_MAX  # ~1.672

ART_W3D = Path("/workspace/patch/Art/W3D")
FILES = (
    ART_W3D / "RUSU-47.W3D",
    ART_W3D / "RUSU-47_D.W3D",
    ART_W3D / "RUSU-47_E.W3D",
)


def walk(data: bytes, start: int, end: int, out: list | None = None) -> list:
    if out is None:
        out = []
    pos = start
    while pos + 8 <= end:
        typ, size_raw = struct.unpack_from("<II", data, pos)
        size = size_raw & 0x7FFFFFFF
        has_sub = bool(size_raw & 0x80000000)
        payload = pos + 8
        payload_end = payload + size
        if payload_end > len(data):
            break
        out.append((pos, typ, size, has_sub))
        if has_sub:
            walk(data, payload, payload_end, out)
        pos = payload_end
    return out


def vertex_extents(data: bytes) -> tuple[float, float, float]:
    xs, ys, zs = [], [], []
    for pos, typ, size, _ in walk(data, 0, len(data)):
        if typ != W3D_VERTICES:
            continue
        for i in range(size // 12):
            x, y, z = struct.unpack_from("<fff", data, pos + 8 + i * 12)
            if max(abs(x), abs(y), abs(z)) < 1e5:
                xs.append(x)
                ys.append(y)
                zs.append(z)
    if not xs:
        raise SystemExit("no vertices")
    return max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)


def scale_file(path: Path, factor: float) -> None:
    data = bytearray(path.read_bytes())
    for pos, typ, size, _ in walk(bytes(data), 0, len(data)):
        if typ == W3D_VERTICES:
            for i in range(size // 12):
                off = pos + 8 + i * 12
                x, y, z = struct.unpack_from("<fff", data, off)
                struct.pack_into("<fff", data, off, x * factor, y * factor, z * factor)
        elif typ == W3D_MESH_HEADER3 and size >= 116:
            off = pos + 8 + 76
            vals = list(struct.unpack_from("<10f", data, off))
            struct.pack_into("<10f", data, off, *[v * factor for v in vals])
        elif typ == W3D_PIVOTS:
            for i in range(size // 60):
                off = pos + 8 + i * 60 + 20
                x, y, z = struct.unpack_from("<fff", data, off)
                struct.pack_into("<fff", data, off, x * factor, y * factor, z * factor)
    path.write_bytes(data)


def main() -> int:
    for path in FILES:
        if not path.exists():
            raise SystemExit(f"missing {path}")
        ext = vertex_extents(path.read_bytes())
        current_max = max(ext)
        print(f"{path.name} before AABB {ext[0]:.2f} x {ext[1]:.2f} x {ext[2]:.2f} max={current_max:.2f}")
        if abs(current_max - SU57_MAX) < 2.0:
            print(f"  already Su-57-class, skip")
            continue
        if abs(current_max - SU47_SRC_MAX) > 2.0:
            raise SystemExit(f"{path.name} unexpected size {current_max:.2f}")
        scale_file(path, SCALE)
        ext2 = vertex_extents(path.read_bytes())
        print(f"  after  AABB {ext2[0]:.2f} x {ext2[1]:.2f} x {ext2[2]:.2f} max={max(ext2):.2f} scale={SCALE:.4f}")
        if abs(max(ext2) - SU57_MAX) > 2.5:
            raise SystemExit(f"{path.name} scale did not reach Su-57 class")
    print(f"SU47 W3D SCALE PASS factor={SCALE:.4f} target_max={SU57_MAX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
