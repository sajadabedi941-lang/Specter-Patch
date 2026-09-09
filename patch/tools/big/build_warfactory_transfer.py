#!/usr/bin/env python3
"""Pack destination-only War Factory CommandSet transfer.

Does not modify reference-country DATA. ART is copied unchanged.
Removes dest Iraq_WarFactory.ini last-wins clones (JP/SK/VN).
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/ea6b_crash_fix/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/ea6b_crash_fix/_SPEC_ART_ONE.big")
TRANSFER = Path("/workspace/patch/Data/INI/CommandSet_ZZZZ_WarFactoryTransfer.ini")
OUT_DIR = Path("/tmp/warfactory_transfer")

NEW_NAME = r"Data\INI\CommandSet_ZZZZ_WarFactoryTransfer.ini"

DROP = {
    r"data\ini\object\specter\japan self-defense forces\buildings\iraq_warfactory.ini",
    r"data\ini\object\specter\south korean armed forces\buildings\iraq_warfactory.ini",
    r"data\ini\object\specter\vietnam people's armed forces\buildings\iraq_warfactory.ini",
}

REF_PATH_TOKENS = (
    r"\united states of america\\",
    r"\armed forces of russian federation\\",
    r"\pla\\",
    r"\iranian army\\",
    r"\israel defense forces\\",
    r"\nato\\",
    r"\egyptian armed forces\\",
    r"\iraq army\\",
    r"\north korea\\",
    r"data\ini\playertemplate.ini",
    r"data\ini\science.ini",
)

LIVE_CS = [
    "BritainWarfactoryCommandSet",
    "GermanyWarfactoryCommandSet",
    "FranceWarfactoryCommandSet",
    "ItalyWarfactoryCommandSet",
    "UkraineWarfactoryCommandSet",
    "TurkeyWarfactoryCommandSet",
    "SwedenWarfactoryCommandSet",
    "Libya_WarFactoryCommandSet",
    "SouthAfrica_WarFactoryCommandSet",
    "UAE_WarFactoryCommandSet",
    "SaudiArabia_WarFactoryCommandSet",
    "Syria_WarFactoryCommandSet",
    "Japan_WarFactoryCommandSet",
    "Vietnam_WarFactoryCommandSet",
    "SouthKorea_WarFactoryCommandSet",
    "India_WarFactoryCommandSet",
    "Pakistan_WarFactoryCommandSet",
]


def parse_big(path: Path):
    data = path.read_bytes()
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for _ in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((name, data[eoff : eoff + esz]))
    return entries


def build_big_ordered(entries):
    header_size = 16
    encoded = [(n.encode("latin1"), b) for n, b in entries]
    for nb, _blob in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for nb, blob in encoded:
        index.append((nb, offset, len(blob)))
        blobs.append(blob)
        offset += len(blob)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def last_cs(entries, name):
    found = None
    src = None
    for n, b in entries:
        t = b.decode("latin1", errors="ignore")
        m = re.search(rf"(?ims)^CommandSet\s+{re.escape(name)}\b.*?^End\s*$", t)
        if m:
            found = m.group(0)
            src = n
    return src, found


def main() -> int:
    blob = TRANSFER.read_bytes()
    if b"\n" in blob and b"\r\n" not in blob:
        blob = blob.replace(b"\n", b"\r\n")
    src = parse_big(SRC_DATA)
    out = []
    dropped = []
    for n, b in src:
        key = n.replace("/", "\\").lower()
        if key in DROP:
            dropped.append(n)
            continue
        out.append((n, b))
    # last-wins new commandset file
    out.append((NEW_NAME, blob))
    print("dropped", dropped)
    print("added", NEW_NAME, len(blob))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(out)
    art_big = SRC_ART.read_bytes()
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_big)
    dsha = hashlib.sha256(data_big).hexdigest()
    asha = hashlib.sha256(art_big).hexdigest()
    print("DATA", dsha, len(data_big))
    print("ART ", asha, len(art_big), "(unchanged bytes)")
    (OUT_DIR / "SHA256.txt").write_text(f"DATA {dsha}\nART  {asha}\n")

    packed = parse_big(OUT_DIR / "_SPEC_DATA_ONE.big")
    src_map = {n.replace("/", "\\").lower(): b for n, b in src}
    new_map = {n.replace("/", "\\").lower(): (n, b) for n, b in packed}
    diffs = []
    for k, (n, b) in new_map.items():
        if src_map.get(k) != b:
            diffs.append(n)
    for n, _ in src:
        if n.replace("/", "\\").lower() not in new_map:
            diffs.append("DEL " + n)
    print("DATA diffs:")
    for d in diffs:
        print(" ", d)
        low = d.lower()
        if any(tok in low for tok in REF_PATH_TOKENS) and "commandset_zzzz" not in low:
            print("FAIL reference/locked path changed", d)
            return 1

    transfer_text = blob.decode("latin1")
    for name in LIVE_CS:
        src_file, last = last_cs(packed, name)
        if src_file != NEW_NAME:
            print("FAIL last-wins", name, "from", src_file)
            return 1
        if f"CommandSet {name}" not in transfer_text:
            print("FAIL", name, "not in transfer")
            return 1
        if "Command_Sell" not in last:
            print("FAIL", name, "no Sell")
            return 1
    print("LAST_WINS_OK", len(LIVE_CS), "dest CommandSets")

    # Japan/SK/VN object last-wins should be the national WF file, not Iraq clone
    for obj, needle in [
        ("Japan_WarFactory", "japan_warfactory.ini"),
        ("SouthKorea_WarFactory", "southkorea_warfactory.ini"),
        ("Vietnam_WarFactory", "vietnam_warfactory.ini"),
    ]:
        last = None
        for n, b in packed:
            if re.search(rf"(?im)^Object(?:Reskin)?\s+{re.escape(obj)}\b", b.decode("latin1", errors="ignore")):
                last = n
        if not last or needle not in last.replace("\\", "/").lower():
            print("FAIL last-wins object", obj, last)
            return 1
        print("object last-wins", obj, last)
    print("PACK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
