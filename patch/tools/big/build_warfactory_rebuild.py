#!/usr/bin/env python3
"""Clean destination War Factory bars and rebuild them from live reference templates.

Packs from the EA-6B crash-fix DATA baseline. Does not modify protected-country
files. ART is not rewritten. Destination Iraq_WarFactory.ini clones (JP/SK/VN)
are dropped so national War Factory objects last-win.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/ea6b_crash_fix/_SPEC_DATA_ONE.big")
OUT_DIR = Path("/tmp/warfactory_rebuild")
INI_PATH = Path("/workspace/patch/Data/INI/CommandSet_ZZZZ_WarFactoryRebuild.ini")
NEW_NAME = r"Data\INI\CommandSet_ZZZZ_WarFactoryRebuild.ini"

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
    r"data\ini\commandset.ini",
    r"data\ini\commandbutton.ini",
)

PROTECTED_CS = {
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
    "Israel_WarFactoryCommandSet1",
    "Israel_WarFactoryCommandSet2",
    "Israel_WarFactoryCommandSet3",
    "NorthKorea_WarFactoryCommandSet",
    "ChinaWarFactoryCommandSet",
}

# Live destination War Factory CommandSet names, plus aliases that must not
# restore destination-named production after this last-wins file.
DEST_CS = {
    "NATO": [
        "BritainWarfactoryCommandSet",
        "Britain_WarFactoryCommandSet",
        "GermanyWarfactoryCommandSet",
        "Germany_WarFactoryCommandSet",
        "FranceWarfactoryCommandSet",
        "France_WarFactoryCommandSet",
        "ItalyWarfactoryCommandSet",
        "Italy_WarFactoryCommandSet",
        "UkraineWarfactoryCommandSet",
        "Ukraine_WarFactoryCommandSet",
        "Ukraine_WarFactoryCommandSet1",
        "Ukraine_WarFactoryCommandSet2",
        "Ukraine_WarFactoryCommandSet3",
        "TurkeyWarfactoryCommandSet",
        "Turkey_WarFactoryCommandSet",
        "Turkey_WarFactoryCommandSet_T",
        "Turkey_WarFactoryCommandSet_T1",
        "Turkey_WarFactoryCommandSet_T2",
        "Turkey_WarFactoryCommandSet_T3",
        "SwedenWarfactoryCommandSet",
        "Sweden_WarFactoryCommandSet",
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
        "Vietnam_WarFactoryCommandSet1",
        "Vietnam_WarFactoryCommandSet2",
        "Vietnam_WarFactoryCommandSet3",
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

LIVE_DEST_CS = {
    "Britain": "BritainWarfactoryCommandSet",
    "Germany": "GermanyWarfactoryCommandSet",
    "France": "FranceWarfactoryCommandSet",
    "Italy": "ItalyWarfactoryCommandSet",
    "Ukraine": "UkraineWarfactoryCommandSet",
    "Turkey": "TurkeyWarfactoryCommandSet",
    "Sweden": "SwedenWarfactoryCommandSet",
    "Libya": "Libya_WarFactoryCommandSet",
    "SouthAfrica": "SouthAfrica_WarFactoryCommandSet",
    "UAE": "UAE_WarFactoryCommandSet",
    "SaudiArabia": "SaudiArabia_WarFactoryCommandSet",
    "Syria": "Syria_WarFactoryCommandSet",
    "Japan": "Japan_WarFactoryCommandSet",
    "Vietnam": "Vietnam_WarFactoryCommandSet",
    "SouthKorea": "SouthKorea_WarFactoryCommandSet",
    "India": "India_WarFactoryCommandSet",
    "Pakistan": "Pakistan_WarFactoryCommandSet",
}

REF_CS_NAME = {
    "NATO": "NatoWarfactoryCommandSet",
    "Iraq": "Iraq_WarFactoryCommandSet_T3",
    "Egypt": "EgyptWarFactoryCommandSet",
    "USA": "AmericaWarFactoryCommandSet",
    "Russia": "RussiaWarFactoryCommandSet",
}

COUNTRY_TO_REF = {
    "Britain": "NATO",
    "Germany": "NATO",
    "France": "NATO",
    "Italy": "NATO",
    "Ukraine": "NATO",
    "Turkey": "NATO",
    "Sweden": "NATO",
    "Libya": "Iraq",
    "SouthAfrica": "Iraq",
    "UAE": "Egypt",
    "SaudiArabia": "Egypt",
    "Syria": "Egypt",
    "Japan": "USA",
    "Vietnam": "USA",
    "SouthKorea": "USA",
    "India": "Russia",
    "Pakistan": "Russia",
}

USA_OMIT_BUTTONS = {"Command_ConstructAmericaVehicleM1075I_AI"}


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


def last_block(kind: str, name: str, entries):
    found = None
    src = None
    pat = re.compile(rf"(?im)^{kind}\s+{re.escape(name)}\b")
    for fname, blob in entries:
        text = blob.decode("latin1", errors="ignore")
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
                elif re.match(
                    r"(?i)^\s*(Draw|Behavior|Body|WeaponSet|ArmorSet|Prerequisites|DefaultConditionState|ConditionState|UnitSpecificSounds)\b",
                    raw,
                ):
                    depth += 1
            found = "".join(buf)
            src = fname
    return src, found


def cs_slots(blk: str):
    out = []
    for line in blk.splitlines():
        raw = line.split(";", 1)[0]
        m = re.match(r"\s*(\d+)\s*=\s*(\S+)", raw)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def format_cs(name: str, slots: list[tuple[str, str]]) -> str:
    lines = [f"CommandSet {name}"]
    for slot, btn in slots:
        if len(slot) == 1:
            lines.append(f"  {slot}  = {btn}")
        else:
            lines.append(f" {slot}  = {btn}")
    lines.append("End")
    return "\r\n".join(lines) + "\r\n"


def reference_slots(entries, ref_key: str) -> list[tuple[str, str]]:
    cs_name = REF_CS_NAME[ref_key]
    src, blk = last_block("CommandSet", cs_name, entries)
    if not blk:
        raise SystemExit(f"missing reference CommandSet {cs_name}")
    slots = cs_slots(blk)
    if ref_key == "USA":
        slots = [(s, b) for s, b in slots if b not in USA_OMIT_BUTTONS]
    if src != r"Data\INI\CommandSet.ini" and ref_key != "Iraq":
        # Iraq T3 also lives in CommandSet.ini; keep the check informative.
        pass
    return slots


def generate_ini(entries) -> str:
    parts = [
        "; SPECTER -- destination War Factory FULL CLEAN AND REBUILD",
        "; Last-wins. Protected countries are NOT defined here.",
        "; Each destination CommandSet is an exact copy of the assigned",
        "; reference War Factory bar (same CommandButtons and objects).",
        "; Destination-named tank/vehicle production entries are removed.",
        "",
    ]
    headers = {
        "NATO": "NATO NatoWarfactoryCommandSet",
        "Iraq": "Iraq Iraq_WarFactoryCommandSet_T3",
        "Egypt": "Egypt EgyptWarFactoryCommandSet",
        "USA": "USA AmericaWarFactoryCommandSet minus AI-only M1075I",
        "Russia": "Russia RussiaWarFactoryCommandSet",
    }
    for ref_key, names in DEST_CS.items():
        slots = reference_slots(entries, ref_key)
        parts.append(";============================================================================")
        parts.append(f"; {headers[ref_key]}")
        parts.append(";============================================================================")
        parts.append("")
        for name in names:
            if name in PROTECTED_CS:
                raise SystemExit(f"refusing to write protected CommandSet {name}")
            parts.append(format_cs(name, slots).replace("\r\n", "\n").rstrip("\n"))
            parts.append("")
    text = "\n".join(parts)
    if not text.endswith("\n"):
        text += "\n"
    return text.replace("\n", "\r\n")


def main() -> int:
    src = parse_big(SRC_DATA)
    text = generate_ini(src)
    INI_PATH.parent.mkdir(parents=True, exist_ok=True)
    INI_PATH.write_bytes(text.encode("latin1"))
    print("wrote", INI_PATH, len(text))

    blob = text.encode("latin1")
    out = []
    dropped = []
    for n, b in src:
        key = n.replace("/", "\\").lower()
        if key in DROP:
            dropped.append(n)
            continue
        out.append((n, b))
    out.append((NEW_NAME, blob))
    print("dropped", dropped)
    print("added", NEW_NAME, len(blob))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(out)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    dsha = hashlib.sha256(data_big).hexdigest()
    print("DATA", dsha, len(data_big))
    (OUT_DIR / "SHA256.txt").write_text(f"DATA {dsha}\n")

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
            print("FAIL protected/locked path changed", d)
            return 1

    for name in LIVE_DEST_CS.values():
        src_file, last = last_block("CommandSet", name, packed)
        if src_file != NEW_NAME:
            print("FAIL last-wins", name, "from", src_file)
            return 1
        if "Command_Sell" not in last:
            print("FAIL", name, "no Sell")
            return 1
    print("LAST_WINS_OK", len(LIVE_DEST_CS), "live dest CommandSets")

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

    for cs in PROTECTED_CS:
        old_src, old = last_block("CommandSet", cs, src)
        new_src, new = last_block("CommandSet", cs, packed)
        if old != new or new_src != old_src:
            print("FAIL protected CommandSet changed", cs, old_src, "->", new_src)
            return 1
    print("PROTECTED_CS_UNCHANGED", len(PROTECTED_CS))
    print("PACK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
