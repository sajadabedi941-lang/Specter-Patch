"""Read SAGE BIGF archives without loading every payload into RAM.

write_big is for tests and nested-BIG fixtures only. Never used on SPECTER game BIGs.
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


def copy_big_with_adds(
    src: Path,
    dest: Path,
    adds: dict[str, bytes],
    protected_nkeys: set[str] | None = None,
) -> dict:
    """Copy a BIG and append unique-path files. Never overwrites an existing path."""
    protected = {n.replace("/", "\\").lower() for n in (protected_nkeys or set())}
    entries = _read_index(src)
    existing = {nkey(n): n for n, _, _ in entries}
    collisions = []
    protected_hits = []
    for name in adds:
        k = nkey(name)
        if k in protected:
            protected_hits.append(name)
        if k in existing:
            collisions.append(f"{name} -> {existing[k]}")
    if protected_hits:
        raise ValueError("refusing to overwrite protected BIG paths: " + ", ".join(protected_hits))
    if collisions:
        raise ValueError("unique-path add collides with existing BIG member: " + "; ".join(collisions))

    add_items = sorted(adds.items(), key=lambda kv: kv[0].replace("/", "\\").lower())
    header_size = 16
    for name, _, _ in entries:
        header_size += 8 + len(name.encode("latin1")) + 1
    for name, _blob in add_items:
        header_size += 8 + len(name.encode("latin1")) + 1

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    with src.open("rb") as inf, tmp.open("wb") as out:
        out.write(b"\x00" * header_size)
        new_index: list[tuple[str, int, int]] = []
        for name, off, size in entries:
            inf.seek(off)
            payload_off = out.tell()
            left = size
            while left:
                chunk = inf.read(min(1 << 20, left))
                if not chunk:
                    break
                out.write(chunk)
                left -= len(chunk)
            new_index.append((name, payload_off, size))
        for name, blob in add_items:
            payload_off = out.tell()
            out.write(blob)
            new_index.append((name, payload_off, len(blob)))
        total = out.tell()
        out.seek(0)
        out.write(b"BIGF" + struct.pack(">III", total, len(new_index), header_size))
        for name, off, size in new_index:
            out.write(struct.pack(">II", off, size))
            out.write(name.encode("latin1") + b"\x00")
    tmp.replace(dest)
    return {
        "source": str(src),
        "dest": str(dest),
        "original_entries": len(entries),
        "added": len(add_items),
        "total_entries": len(entries) + len(add_items),
        "bytes": dest.stat().st_size,
        "added_names": [n for n, _ in add_items],
    }


def rewrite_big_members(src: Path, dest: Path, replacements: dict[str, bytes]) -> dict:
    """Copy a BIG and replace existing member payloads. Does not add or delete names.

    `src` is never opened for write. Replacements must match existing paths.
    """
    entries = _read_index(src)
    existing = {nkey(n): (n, off, size) for n, off, size in entries}
    missing = [name for name in replacements if nkey(name) not in existing]
    if missing:
        raise ValueError("rewrite_big_members: names not in BIG: " + ", ".join(missing))
    repl = {nkey(name): blob for name, blob in replacements.items()}

    header_size = 16
    for name, _, _ in entries:
        header_size += 8 + len(name.encode("latin1")) + 1

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    with src.open("rb") as inf, tmp.open("wb") as out:
        out.write(b"\x00" * header_size)
        new_index: list[tuple[str, int, int]] = []
        for name, off, size in entries:
            k = nkey(name)
            payload_off = out.tell()
            if k in repl:
                blob = repl[k]
                out.write(blob)
                new_index.append((name, payload_off, len(blob)))
            else:
                inf.seek(off)
                left = size
                while left:
                    chunk = inf.read(min(1 << 20, left))
                    if not chunk:
                        break
                    out.write(chunk)
                    left -= len(chunk)
                new_index.append((name, payload_off, size))
        total = out.tell()
        out.seek(0)
        out.write(b"BIGF" + struct.pack(">III", total, len(new_index), header_size))
        for name, off, size in new_index:
            out.write(struct.pack(">II", off, size))
            out.write(name.encode("latin1") + b"\x00")
    tmp.replace(dest)
    return {
        "source": str(src),
        "dest": str(dest),
        "replaced": sorted(replacements),
        "total_entries": len(entries),
        "bytes": dest.stat().st_size,
    }


def write_big(path: Path, files: dict[str, bytes]) -> None:
    """Minimal BIGF writer for tests. Not used on SPECTER game BIGs."""
    items = list(files.items())
    index = b""
    payload = b""
    index_size = sum(8 + len(name.encode("latin1")) + 1 for name, _ in items)
    off = 16 + index_size
    for name, blob in items:
        index += struct.pack(">II", off, len(blob))
        index += name.encode("latin1") + b"\x00"
        payload += blob
        off += len(blob)
    total = 16 + len(index) + len(payload)
    path.write_bytes(b"BIGF" + struct.pack(">III", total, len(items), 16 + len(index)) + index + payload)


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
