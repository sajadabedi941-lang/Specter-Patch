"""Read SAGE BIGF archives without loading every payload into RAM.

Write is intentionally omitted in stage 1.
"""
from __future__ import annotations

import struct
from pathlib import Path
from typing import Callable, Iterator


def _read_index(path: Path) -> list[tuple[str, int, int]]:
    with path.open("rb") as f:
        magic = f.read(4)
        if magic not in (b"BIGF", b"BIG4"):
            raise ValueError(f"not BIGF: {path}")
        f.read(4)  # archive size
        count = struct.unpack(">I", f.read(4))[0]
        f.read(4)  # index / header size
        entries: list[tuple[str, int, int]] = []
        for _ in range(count):
            off, size = struct.unpack(">II", f.read(8))
            name_b = b""
            while True:
                ch = f.read(1)
                if not ch or ch == b"\x00":
                    break
                name_b += ch
            name = name_b.decode("latin1")
            entries.append((name, off, size))
        return entries


def iter_big(
    path: Path,
    payload_if: Callable[[str], bool] | None = None,
) -> Iterator[tuple[str, bytes | None]]:
    """Yield (name, payload or None). If payload_if is set, only those names are read."""
    entries = _read_index(path)
    with path.open("rb") as f:
        for name, off, size in entries:
            if payload_if is None or payload_if(name):
                f.seek(off)
                yield name, f.read(size)
            else:
                yield name, None


def read_big(path: Path, suffixes: tuple[str, ...] | None = (".ini",)) -> dict[str, bytes]:
    want = None
    if suffixes:
        suf = tuple(s.lower() for s in suffixes)

        def want(name: str, _suf=suf) -> bool:
            return nkey(name).endswith(_suf)

    out: dict[str, bytes] = {}
    for name, blob in iter_big(path, want):
        if blob is not None:
            out[name] = blob
    return out


def list_names(path: Path) -> list[str]:
    return [name for name, _, _ in _read_index(path)]


def nkey(name: str) -> str:
    return name.replace("/", "\\").lower()


def basename(name: str) -> str:
    return name.replace("\\", "/").rsplit("/", 1)[-1]


def stem_lower(name: str) -> str:
    base = basename(name)
    if "." in base:
        return base.rsplit(".", 1)[0].lower()
    return base.lower()
