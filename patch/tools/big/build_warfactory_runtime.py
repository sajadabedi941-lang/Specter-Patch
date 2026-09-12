#!/usr/bin/env python3
"""Replace destination War Factory CommandSets in the LIVE packed files.

Edits only the winning CommandSet.ini / CommandSet_Pakistan.ini blobs from
the EA-6B DATA baseline. Protected CommandSet blocks are left byte-identical.
Does not append a ZZZZ override file.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/ea6b_crash_fix/_SPEC_DATA_ONE.big")
OUT_DIR = Path("/tmp/warfactory_runtime")
EXTRACT_DIR = Path("/tmp/warfactory_runtime/extracted")

CS_INI = r"Data\INI\CommandSet.ini"
PK_INI = r"Data\INI\CommandSet_Pakistan.ini"

DROP = {
    r"data\ini\object\specter\japan self-defense forces\buildings\iraq_warfactory.ini",
    r"data\ini\object\specter\south korean armed forces\buildings\iraq_warfactory.ini",
    r"data\ini\object\specter\vietnam people's armed forces\buildings\iraq_warfactory.ini",
}

REF_CS = {
    "NATO": "NatoWarfactoryCommandSet",
    "Iraq": "Iraq_WarFactoryCommandSet_T3",
    "Egypt": "EgyptWarFactoryCommandSet",
    "USA": "AmericaWarFactoryCommandSet_T3",
    "Russia": "RussiaWarFactoryCommandSet",
}

USA_OMIT = {"Command_ConstructAmericaVehicleM1075I_AI"}

# Live dest CommandSet names (from PlayerTemplate -> dozer/VT72B -> WF Object)
# plus numbered aliases that live in the same winning files.
DEST_CS = {
    "NATO": [
        "BritainWarfactoryCommandSet",
        "GermanyWarfactoryCommandSet",
        "FranceWarfactoryCommandSet",
        "ItalyWarfactoryCommandSet",
        "UkraineWarfactoryCommandSet",
        "TurkeyWarfactoryCommandSet",
        "SwedenWarfactoryCommandSet",
    ],
    "Iraq": [
        "Libya_WarFactoryCommandSet",
        "Libya_WarFactoryCommandSet1",
        "Libya_WarFactoryCommandSet2",
        "Libya_WarFactoryCommandSet3",
        "SouthAfrica_WarFactoryCommandSet",
        "SouthAfrica_WarFactoryCommandSet1",
        "SouthAfrica_WarFactoryCommandSet2",
        "SouthAfrica_WarFactoryCommandSet3",
    ],
    "Egypt": [
        "UAE_WarFactoryCommandSet",
        "UAE_WarFactoryCommandSet1",
        "UAE_WarFactoryCommandSet2",
        "UAE_WarFactoryCommandSet3",
        "SaudiArabia_WarFactoryCommandSet",
        "SaudiArabia_WarFactoryCommandSet1",
        "SaudiArabia_WarFactoryCommandSet2",
        "SaudiArabia_WarFactoryCommandSet3",
        "Syria_WarFactoryCommandSet",
        "Syria_WarFactoryCommandSet1",
        "Syria_WarFactoryCommandSet2",
        "Syria_WarFactoryCommandSet3",
    ],
    "USA": [
        "Japan_WarFactoryCommandSet",
        "Vietnam_WarFactoryCommandSet",
        "SouthKorea_WarFactoryCommandSet",
    ],
    "Russia": [
        "India_WarFactoryCommandSet",
        "India_WarFactoryCommandSet1",
        "India_WarFactoryCommandSet2",
        "India_WarFactoryCommandSet3",
        "Pakistan_WarFactoryCommandSet",
        "Pakistan_WarFactoryCommandSet1",
        "Pakistan_WarFactoryCommandSet2",
        "Pakistan_WarFactoryCommandSet3",
    ],
}

PROTECTED_CS = [
    "NatoWarfactoryCommandSet",
    "AmericaWarFactoryCommandSet",
    "AmericaWarFactoryCommandSet_T",
    "AmericaWarFactoryCommandSet_T1",
    "AmericaWarFactoryCommandSet_T2",
    "AmericaWarFactoryCommandSet_T3",
    "RussiaWarFactoryCommandSet",
    "EgyptWarFactoryCommandSet",
    "Egypt_WarFactoryCommandSet",
    "Egypt_WarFactoryCommandSet1",
    "Egypt_WarFactoryCommandSet2",
    "Egypt_WarFactoryCommandSet3",
    "Iraq_WarFactoryCommandSet",
    "Iraq_WarFactoryCommandSet_T",
    "Iraq_WarFactoryCommandSet_T1",
    "Iraq_WarFactoryCommandSet_T2",
    "Iraq_WarFactoryCommandSet_T3",
    "IranWarfactoryCommandSet",
    "Israel_WarFactoryCommandSet",
    "NorthKorea_WarFactoryCommandSet",
    "ChinaWarFactoryCommandSet",
]

PROTECTED_PATHS = (
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
    r"data\ini\commandbutton.ini",
)


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


def cs_slots(blk: str):
    out = []
    for line in blk.splitlines():
        raw = line.split(";", 1)[0]
        m = re.match(r"\s*(\d+)\s*=\s*(\S+)", raw)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def extract_cs_block(text: str, name: str):
    pat = re.compile(rf"(?im)^CommandSet\s+{re.escape(name)}\b")
    found = None
    for m in pat.finditer(text):
        start = m.start()
        depth = 0
        buf = []
        for i, line in enumerate(text[start:].splitlines(True)):
            buf.append(line)
            raw = line.split(";", 1)[0]
            if i == 0:
                depth = 1
                continue
            if re.match(r"(?i)^\s*End\b", raw):
                depth -= 1
                if depth <= 0:
                    break
        found = "".join(buf)
    return found


def format_cs(name: str, slots: list[tuple[str, str]], nl: str) -> str:
    lines = [f"CommandSet {name}"]
    for slot, btn in slots:
        if len(slot) == 1:
            lines.append(f"  {slot}  = {btn}")
        else:
            lines.append(f" {slot}  = {btn}")
    lines.append("End")
    return nl.join(lines) + nl


def replace_cs(text: str, name: str, slots: list[tuple[str, str]]) -> tuple[str, int]:
    nl = "\r\n" if "\r\n" in text else "\n"
    pat = re.compile(rf"(?im)^CommandSet\s+{re.escape(name)}\b")
    matches = list(pat.finditer(text))
    if not matches:
        return text, 0
    new_blk = format_cs(name, slots, nl)
    # replace last occurrence first so offsets stay valid
    out = text
    count = 0
    for m in reversed(matches):
        start = m.start()
        depth = 0
        end = None
        pos = start
        for i, line in enumerate(out[start:].splitlines(True)):
            raw = line.split(";", 1)[0]
            if i == 0:
                depth = 1
                pos += len(line)
                continue
            pos += len(line)
            if re.match(r"(?i)^\s*End\b", raw):
                depth -= 1
                if depth <= 0:
                    end = pos
                    break
        if end is None:
            raise SystemExit(f"unclosed CommandSet {name}")
        out = out[:start] + new_blk + out[end:]
        count += 1
    return out, count


def reference_slots(cs_text: str, ref_key: str):
    name = REF_CS[ref_key]
    blk = extract_cs_block(cs_text, name)
    if not blk:
        raise SystemExit(f"missing reference CommandSet {name}")
    slots = cs_slots(blk)
    if ref_key == "USA":
        slots = [(s, b) for s, b in slots if b not in USA_OMIT]
    return slots


def main() -> int:
    src = parse_big(SRC_DATA)
    by_name = {n.replace("/", "\\"): (i, n, b) for i, (n, b) in enumerate(src)}
    cs_key = CS_INI
    pk_key = PK_INI
    if cs_key not in by_name:
        raise SystemExit("CommandSet.ini missing from packed DATA")
    if pk_key not in by_name:
        raise SystemExit("CommandSet_Pakistan.ini missing from packed DATA")

    _, cs_name, cs_blob = by_name[cs_key]
    _, pk_name, pk_blob = by_name[pk_key]
    cs_text = cs_blob.decode("latin1")
    pk_text = pk_blob.decode("latin1")

    protected_before = {n: extract_cs_block(cs_text, n) for n in PROTECTED_CS}

    replaced = []
    for ref_key, names in DEST_CS.items():
        slots = reference_slots(cs_text, ref_key)
        for name in names:
            if name in PROTECTED_CS:
                raise SystemExit(f"refusing to edit protected {name}")
            cs_text, n1 = replace_cs(cs_text, name, slots)
            pk_text, n2 = replace_cs(pk_text, name, slots)
            if n1 + n2 == 0:
                print("WARN no block", name)
            else:
                replaced.append((name, ref_key, n1, n2, slots))
                print(f"replaced {name} ref={ref_key} CommandSet.ini={n1} Pakistan.ini={n2}")

    for n in PROTECTED_CS:
        after = extract_cs_block(cs_text, n)
        if after != protected_before[n]:
            print("FAIL protected CommandSet mutated", n)
            return 1
    print("PROTECTED_CS_BLOCKS_UNCHANGED", len(PROTECTED_CS))

    new_cs = cs_text.encode("latin1")
    new_pk = pk_text.encode("latin1")
    print("CommandSet.ini", len(cs_blob), "->", len(new_cs))
    print("CommandSet_Pakistan.ini", len(pk_blob), "->", len(new_pk))

    out = []
    dropped = []
    for n, b in src:
        key = n.replace("/", "\\")
        low = key.lower()
        if low in DROP:
            dropped.append(n)
            continue
        if key == cs_key:
            out.append((n, new_cs))
        elif key == pk_key:
            out.append((n, new_pk))
        else:
            out.append((n, b))
    print("dropped", dropped)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(out)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    dsha = hashlib.sha256(data_big).hexdigest()
    print("DATA", dsha, len(data_big))
    (OUT_DIR / "SHA256.txt").write_text(f"DATA {dsha}\n")

    # Re-extract the two edited files and dest CS blocks for inspection
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    packed = parse_big(OUT_DIR / "_SPEC_DATA_ONE.big")
    for n, b in packed:
        key = n.replace("/", "\\")
        if key in (cs_key, pk_key):
            safe = n.replace("\\", "_")
            (EXTRACT_DIR / safe).write_bytes(b)
    excerpt = []
    packed_cs = None
    packed_pk = None
    for n, b in packed:
        key = n.replace("/", "\\")
        if key == cs_key:
            packed_cs = b.decode("latin1")
        if key == pk_key:
            packed_pk = b.decode("latin1")
    for ref_key, names in DEST_CS.items():
        for name in names:
            blk = extract_cs_block(packed_cs or "", name)
            srcfile = CS_INI
            if name.startswith("Pakistan") and packed_pk:
                pkblk = extract_cs_block(packed_pk, name)
                if pkblk:
                    blk = pkblk
                    srcfile = PK_INI
            excerpt.append(f"; winner {srcfile}")
            excerpt.append(blk.rstrip() if blk else f"; MISSING {name}")
            excerpt.append("")
    (EXTRACT_DIR / "LIVE_DEST_WARFACTORY_COMMANDSETS.ini").write_text(
        "\n".join(excerpt), encoding="latin1"
    )

    # Diff list
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
        if any(tok in low for tok in PROTECTED_PATHS):
            print("FAIL protected path changed", d)
            return 1
        if "commandset.ini" in low and "pakistan" not in low:
            continue
        if "commandset_pakistan.ini" in low:
            continue
        if d.startswith("DEL "):
            continue
        print("FAIL unexpected diff", d)
        return 1

    print("PACK_OK replacements", len(replaced))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
