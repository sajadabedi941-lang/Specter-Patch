#!/usr/bin/env python3
"""Launch-safe DATA pack: PR #385 CommandSet.ini frozen.

- CommandSet.ini is copied byte-identical from the #385 working pack.
- No replacement of CommandButton.ini, Weapon.ini, Russia_System.ini, or CSF.
- Su-47 / T-50 are ADD-ONLY isolated overlay Object INIs.
- Su-75 stays the existing packed #385 object (no second Object file).
- ZIP is written only after CommandSet.ini parser check passes.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

DATA_SRC = Path("/tmp/russia_su35s_ka52/_SPEC_DATA_ONE.big")
PATCH = Path("/workspace/patch")
OUT = Path("/tmp/russia_launch_safe")

CS_KEY = r"data\ini\commandset.ini"
LARGE_NAME = "Russia_LargeAirBaseCommandSet"
EXPECTED_LARGE = (
    "CommandSet Russia_LargeAirBaseCommandSet\n"
    "  1  = Command_ConstructRussiaJetSu75Checkmate\n"
    "  2  = Command_ConstructRussiaJetSu35S\n"
    "  3  = Command_ConstructRussiaJetSu30SM2\n"
    "  4  = Command_ConstructRussiaJetSU25T\n"
    "  5  = Command_ConstructRussiaJetSu35AG\n"
    "  6  = Command_ConstructRussiaJetMig31K\n"
    "  7  = Command_ConstructRussiaHelicopterMi28N\n"
    "  8  = Command_ConstructRussiaHelicopterKA52\n"
    "  9  = Command_ConstructRussiaJetSu57AA\n"
    "  10 = Command_ConstructRussiaJetSu47Recon\n"
    "  13 = Command_SetRallyPoint\n"
    "  14 = Command_Sell\n"
    "End"
)

NEW_OBJECTS = {
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su47Berkut.ini": (
        PATCH / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/Su47Berkut.ini"
    ),
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su57T50.ini": (
        PATCH / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/Su57T50.ini"
    ),
}

FROZEN = (
    CS_KEY,
    r"data\ini\commandbutton.ini",
    r"data\ini\weapon.ini",
    r"data\ini\upgrade.ini",
    r"data\english\generals.csf",
    r"data\ini\object\specter\armed forces of russian federation\russia_system.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su35s.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\ka52m.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su57.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su57_aa.ini",
    r"data\ini\object\specter\armed forces of russian federation\buildings\russia_largeairbase.ini",
)


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def write_big(entries: list[tuple[str, bytes]]) -> bytes:
    header = 16
    encoded = []
    for name, blob in entries:
        raw = name.replace("/", "\\").encode("latin1")
        encoded.append((raw, blob))
        header += 8 + len(raw) + 1
    offset = header
    out = bytearray()
    total = header + sum(len(b) for _, b in encoded)
    out += b"BIGF"
    out += struct.pack(">I", total)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header)
    for raw, blob in encoded:
        out += struct.pack(">II", offset, len(blob))
        out += raw + b"\x00"
        offset += len(blob)
    for _, blob in encoded:
        out += blob
    return bytes(out)


def upsert_new_only(entries: list[tuple[str, bytes]], name: str, content: bytes) -> None:
    key = name.replace("/", "\\").lower()
    for n, _ in entries:
        if n.replace("/", "\\").lower() == key:
            raise SystemExit(f"refusing to replace existing DATA file: {n}")
    entries.append((name.replace("/", "\\"), content))


def parse_commandset_block(text: str, name: str) -> dict:
    matches = list(re.finditer(rf"^CommandSet {re.escape(name)}\s*$", text, re.M))
    if len(matches) != 1:
        raise SystemExit(f"parser FAIL: {name} defined {len(matches)} time(s)")
    start = matches[0].start()
    rest = text[start:]
    m = re.match(
        rf"CommandSet {re.escape(name)}\n(?P<body>.*?)(?:\nEnd)(?=\n|$)",
        rest,
        re.S,
    )
    if not m:
        raise SystemExit(f"parser FAIL: {name} missing well-formed End")
    body = m.group("body")
    slots = {}
    for lineno, line in enumerate(body.splitlines(), 1):
        raw = line.split(";", 1)[0].rstrip()
        if not raw.strip():
            continue
        sm = re.match(r"^  (\d+)\s*=\s*(\S+)\s*$", raw)
        if not sm:
            raise SystemExit(f"parser FAIL: {name} bad line {lineno}: {raw!r}")
        slot = int(sm.group(1))
        if slot in slots:
            raise SystemExit(f"parser FAIL: {name} duplicate slot {slot}")
        if slot < 1 or slot > 14:
            raise SystemExit(f"parser FAIL: {name} slot {slot} out of range")
        slots[slot] = sm.group(2)
    block = rest[: m.end()]
    return {"block": block, "slots": slots}


def parser_check_commandset(raw: bytes, baseline: bytes) -> None:
    if raw != baseline:
        raise SystemExit("parser FAIL: CommandSet.ini is not byte-identical to PR #385")
    text = raw.decode("latin1")
    if raw[:2] == b"\xff\xfe" or raw[:3] == b"\xef\xbb\xbf":
        raise SystemExit("parser FAIL: CommandSet.ini has a BOM")
    if b"\r\n" in raw:
        raise SystemExit("parser FAIL: CommandSet.ini has CRLF (385 baseline is LF)")
    parsed = parse_commandset_block(text, LARGE_NAME)
    if parsed["block"] != EXPECTED_LARGE:
        raise SystemExit("parser FAIL: Russia_LargeAirBaseCommandSet body != #385")
    # injected fighter buttons must not be in the frozen menu
    for banned in (
        "Command_ConstructRussiaJetSu47Berkut",
        "Command_ConstructRussiaJetSu57T50",
    ):
        if banned in parsed["block"]:
            raise SystemExit(f"parser FAIL: injected button still in Large menu: {banned}")
    expected_slots = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14}
    if set(parsed["slots"]) != expected_slots:
        raise SystemExit(f"parser FAIL: Large slots {sorted(parsed['slots'])} != {sorted(expected_slots)}")
    # no second definition anywhere later in this file
    if text.count("CommandSet Russia_LargeAirBaseCommandSet") != 1:
        raise SystemExit("parser FAIL: duplicated Russia_LargeAirBaseCommandSet in CommandSet.ini")
    print("PARSER CHECK PASS: CommandSet.ini == PR #385, Large Air Base block valid")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    src_entries = read_big(DATA_SRC)
    src_map = {n.replace("/", "\\").lower(): b for n, b in src_entries}
    baseline_cs = src_map[CS_KEY]

    # Parser check on the source CommandSet BEFORE any pack/zip work.
    parser_check_commandset(baseline_cs, baseline_cs)

    data_entries = list(src_entries)
    added = {}
    for name, path in NEW_OBJECTS.items():
        upsert_new_only(data_entries, name, path.read_bytes())
        added[name] = "added"

    # Re-check the packed CommandSet after adds (must still be the #385 bytes).
    packed_cs = None
    for n, b in data_entries:
        if n.replace("/", "\\").lower() == CS_KEY:
            packed_cs = b
            break
    parser_check_commandset(packed_cs, baseline_cs)

    new_map = {n.replace("/", "\\").lower(): b for n, b in data_entries}
    for key in FROZEN:
        if src_map[key] != new_map[key]:
            raise SystemExit(f"existing file replaced: {key}")
    extra = sorted(set(new_map) - set(src_map))
    expected_extra = {k.replace("/", "\\").lower() for k in NEW_OBJECTS}
    if set(extra) != expected_extra:
        raise SystemExit(f"unexpected added files: {extra}")
    if any("su75checkmate.ini" in k for k in new_map):
        raise SystemExit("refusing duplicate Su-75 overlay object")
    # extra CommandSet files must not redefine Large
    for n, b in data_entries:
        key = n.replace("/", "\\").lower()
        if key == CS_KEY:
            continue
        if b"CommandSet Russia_LargeAirBaseCommandSet" in b:
            raise SystemExit(f"partial Large Air Base override present: {n}")

    data_bytes = write_big(data_entries)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(data_bytes)

    # Final parser check on the written BIG, then ZIP.
    written = {n.replace("/", "\\").lower(): b for n, b in read_big(out_data)}
    parser_check_commandset(written[CS_KEY], baseline_cs)

    zpath = OUT / "RUSSIA_LAUNCH_SAFE_DATA.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
    report = OUT / "PACK_REPORT.txt"
    report.write_text(
        f"DATA SHA256={hashlib.sha256(data_bytes).hexdigest()} SIZE={len(data_bytes)}\n"
        f"ZIP  SHA256={hashlib.sha256(zpath.read_bytes()).hexdigest()} SIZE={zpath.stat().st_size}\n"
        f"CommandSet.ini SHA256={hashlib.sha256(baseline_cs).hexdigest()} (PR #385 exact)\n"
        f"added={added}\n"
        f"PARSER CHECK PASS\n",
        encoding="utf-8",
    )
    print(report.read_text())
    print("ZIP", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
