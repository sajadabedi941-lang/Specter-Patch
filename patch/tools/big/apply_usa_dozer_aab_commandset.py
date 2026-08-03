#!/usr/bin/env python3
"""Patch stock AmericaDozerCommandSet inside _SPEC_DATA_ONE.big.

This intentionally does not add a loose CommandSet.ini overlay and does not
create a second AmericaDozerCommandSet. It rewrites the existing BIG entry with
LF-only bytes so Specter's strict INI parser does not see mixed line endings.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path

COMMANDSET_KEY = r"Data\INI\CommandSet.ini"
TARGET_SET = "AmericaDozerCommandSet"
OLD_COMMAND = "Command_ConstructAmericaStrategyCenter"
OLD_T_COMMAND = "Command_ConstructAmericaStrategyCenter_T"
NEW_COMMAND = "Command_ConstructAmerica_AdvancedAirBase"


def norm_key(name: str) -> str:
    return name.replace("/", "\\").lower()


def read_big(path: Path) -> tuple[list[str], dict[str, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not a BIGF archive: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    order: list[str] = []
    entries: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        order.append(name)
        entries[name] = data[off : off + size]
    return order, entries


def build_big(order: list[str], entries: dict[str, bytes]) -> bytes:
    header_size = 16
    for name in order:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1

    offset = header_size
    index: list[tuple[str, int, int]] = []
    blobs: list[bytes] = []
    for name in order:
        content = bytes(entries[name])
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)

    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(order))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_entry_name(entries: dict[str, bytes], wanted: str) -> str:
    matches = [name for name in entries if norm_key(name) == norm_key(wanted)]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {wanted} entry, found {len(matches)}: {matches}")
    return matches[0]


def commandset_block(text: str, name: str) -> tuple[int, int, str]:
    opener = re.compile(rf"(?m)^CommandSet\s+{re.escape(name)}\s*$")
    matches = list(opener.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {name} definition, found {len(matches)}")
    start = matches[0].start()
    end_match = re.search(r"(?m)^End\s*$", text[matches[0].end() :])
    if not end_match:
        raise ValueError(f"{name} has no closing End")
    end = matches[0].end() + end_match.end()
    return start, end, text[start:end]


def validate_commandset_blocks(text: str) -> None:
    active: str | None = None
    seen = 0
    for line_no, line in enumerate(text.split("\n"), start=1):
        code = line.split(";", 1)[0].strip()
        if not code:
            continue
        open_match = re.match(r"^CommandSet\s+(\S+)\s*$", code)
        if open_match:
            if active is not None:
                raise ValueError(f"Nested CommandSet at line {line_no}: {open_match.group(1)} inside {active}")
            active = open_match.group(1)
            seen += 1
            continue
        if code.lower() == "end":
            if active is None:
                raise ValueError(f"Unexpected End at line {line_no}")
            active = None
    if active is not None:
        raise ValueError(f"Unclosed CommandSet: {active}")
    if seen == 0:
        raise ValueError("No CommandSet blocks found")


def patch_commandset(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    before_start, before_end, before_block = commandset_block(text, TARGET_SET)
    old_line = re.compile(
        rf"(?m)^(\s*\d+\s*=\s*)(?:{re.escape(OLD_T_COMMAND)}|{re.escape(OLD_COMMAND)})(\s*(?:;.*)?)$"
    )
    old_exact_line = re.compile(
        rf"(?m)^\s*\d+\s*=\s*(?:{re.escape(OLD_T_COMMAND)}|{re.escape(OLD_COMMAND)})(?:\s*(?:;.*)?)$"
    )
    if not old_line.search(before_block):
        raise ValueError(f"{OLD_COMMAND}/{OLD_T_COMMAND} not found inside {TARGET_SET}")
    if re.search(rf"(?m)^\s*\d+\s*=\s*{re.escape(NEW_COMMAND)}(?:\s|$)", before_block):
        raise ValueError(f"{NEW_COMMAND} already present inside {TARGET_SET}")

    after_block, replacements = old_line.subn(rf"\1{NEW_COMMAND}\2", before_block)
    if replacements != 2:
        raise ValueError(f"Expected two Strategy Center replacements in {TARGET_SET}, got {replacements}")
    if old_exact_line.search(after_block):
        raise ValueError(f"Strategy Center command still present inside patched {TARGET_SET}")
    patched = text[:before_start] + after_block + text[before_end:]

    # Re-check invariants on the final text.
    validate_commandset_blocks(patched)
    _, _, final_block = commandset_block(patched, TARGET_SET)
    if len(re.findall(rf"(?m)^\s*\d+\s*=\s*{re.escape(NEW_COMMAND)}(?:\s|$)", final_block)) != 2:
        raise ValueError(f"Expected two {NEW_COMMAND} entries in {TARGET_SET}")
    if old_exact_line.search(final_block):
        raise ValueError(f"Strategy Center command remained in {TARGET_SET}")
    if re.search(r"(?ms)^CommandSet\s+AmericaCommandCenterCommandSet\s*$.*AdvancedAirBase", patched):
        raise ValueError("America Command Center CommandSet was touched")

    out = patched.encode("latin1")
    if b"\r" in out:
        raise ValueError("Patched CommandSet.ini still contains CR bytes")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-big", type=Path, required=True)
    parser.add_argument("--out-big", type=Path, required=True)
    parser.add_argument("--export-commandset", type=Path)
    args = parser.parse_args()

    order, entries = read_big(args.data_big)
    key = find_entry_name(entries, COMMANDSET_KEY)
    old_raw = entries[key]
    new_raw = patch_commandset(old_raw)
    entries[key] = new_raw

    args.out_big.parent.mkdir(parents=True, exist_ok=True)
    out = build_big(order, entries)
    args.out_big.write_bytes(out)

    if args.export_commandset:
        args.export_commandset.parent.mkdir(parents=True, exist_ok=True)
        args.export_commandset.write_bytes(new_raw)

    print(f"Patched entry: {key}")
    print(f"AmericaDozerCommandSet definitions: 1")
    print(f"CommandSet.ini CR bytes: {new_raw.count(b'\r')}")
    print(f"CommandSet.ini LF bytes: {new_raw.count(b'\n')}")
    print(f"CommandSet.ini SHA256: {hashlib.sha256(new_raw).hexdigest()}")
    print(f"DATA BIG SHA256: {hashlib.sha256(out).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
