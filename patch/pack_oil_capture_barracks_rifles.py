#!/usr/bin/env python3
"""Pack-only: append barracks/rifle oil-capture CommandSet overlay onto the
validated OIL_CAPTURE_INFANTRY DATA BIG.

Does not rewrite source INIs. Does not replace Weapon.ini / CommandSet.ini /
CommandButton.ini from workspace copies. Appends one last-win overlay and
preserves original BIG path order.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/oil_audit/_SPEC_DATA_ONE.big")
EXPECTED_SRC_SHA = "b754d43373e92816d23fd0cd13e365fcb4619699c93f64ff2cd7c7e037028cb4"
EXPECTED_SRC_SIZE = 366162692
ROOT = Path("/workspace/patch")
INI = ROOT / "Data" / "INI"
RELEASE = ROOT / "Release" / "OIL_CAPTURE_BARRACKS_RIFLES"

APPEND = [
    (
        r"Data\INI\CommandSet_ZZZZ_OilCapture_BarracksAndRifles.ini",
        INI / "CommandSet_ZZZZ_OilCapture_BarracksAndRifles.ini",
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
    r"Data\INI\Object\Specter\Iraq Army\Infantry\Rifleman.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Infantry\Japan_Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Infantry\SouthKorea_Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Vietnam People's Army\Infantry\Rifleman.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_Class2.ini",
    r"Data\INI\CommandButton_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\CommandButton_ZZZZ_FighterRoster_SAUAESYINPK.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_SAUAESYINPK.ini",
    r"Data\INI\CommandSet_ZZZZ_JapanSKVietnam_Capture.ini",
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


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing base BIG {SRC_DATA}")
    if SRC_DATA.stat().st_size != EXPECTED_SRC_SIZE:
        raise SystemExit(f"base size mismatch: {SRC_DATA.stat().st_size}")
    if sha256_file(SRC_DATA) != EXPECTED_SRC_SHA:
        raise SystemExit("validated OIL_CAPTURE_INFANTRY DATA SHA mismatch")

    entries = read_big(SRC_DATA)
    orig = list(entries)
    orig_map = {norm(n).lower(): (n, b) for n, b in orig}

    for packed, src in APPEND:
        if any(norm(n).lower() == packed.lower() for n, _ in entries):
            raise SystemExit(f"already packed: {packed}")
        if not src.is_file():
            raise SystemExit(f"missing append {src}")
        blob = src.read_bytes()
        if b"\n" in blob and b"\r\n" not in blob.replace(b"\r\n", b""):
            # allow mixed only if CRLF present; require CRLF lines
            pass
        if blob.count(b"\n") != blob.count(b"\r\n"):
            raise SystemExit(f"overlay is not CRLF: {src}")
        entries.append((packed, blob))

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

    for n, b in entries[: len(orig)]:
        if b != orig_map[norm(n).lower()][1]:
            raise SystemExit(f"unintended rewrite: {n}")

    data_blob = build_big_ordered(entries)
    rebuilt = read_big_from_bytes(data_blob)
    if [n for n, _ in rebuilt] != new_names:
        raise SystemExit("rebuild order drifted")
    for (n1, b1), (n2, b2) in zip(entries, rebuilt):
        if n1 != n2 or b1 != b2:
            raise SystemExit(f"rebuild content drifted: {n1}")

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
        "  NONE\n"
        "APPENDED\n"
        + "\n".join(f"  {p}" for p, _ in APPEND)
        + "\nPRESERVED_CLASS2 = YES\n"
        + "PRESERVED_NEXT14 = YES\n"
        + "PRESERVED_SA_UAE_SY_IN_PK = YES\n"
        + "ART_CHANGED = NO\n",
        encoding="utf-8",
    )
    print("PACKED", out, out.stat().st_size, sha, "files", len(entries))
    print("REPLACED 0 APPENDED", len(APPEND))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
