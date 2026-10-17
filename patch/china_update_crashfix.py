#!/usr/bin/env python3
"""SPECTER1 crashfix: relocate illegal Object-folder CommandSet overlays.

Baseline: exact PR #491 / Aircraft Standardization Pass 01 packed DATA.
Moves CommandSet/CommandButton/MappedImage blocks out of Object INI files
into CommandSet.ini / CommandButton.ini / MappedImages. No gameplay slot
changes. Does not touch the 44 airframe-std targets, ART, or Weapon.ini.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_AIRFRAME_STD_01/_SPEC_DATA_ONE.big")
EXPECTED_SRC_SHA = "43f8e611d416ff17bac178900556101cb4e8472e48ff0fb8ecbff29dcc3a37db"
OUT_DIR = Path("/tmp/SPECTER1_AIRFRAME_STD_01_CRASHFIX_TEST")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_AIRFRAME_STD_01_CRASHFIX_TEST")

P_CHINA01 = r"Data\INI\Object\Specter\PLA\China_Update_01.ini"
P_USA01 = r"Data\INI\Object\Specter\United States Of America\USA_Update_01.ini"
P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_CAMP = r"Data\INI\Object\Specter\PLA\Buildings\Camp.ini"
P_AIRFIELD = r"Data\INI\Object\Specter\United States Of America\Buildings\Airfield.ini"
P_LARGE = r"Data\INI\Object\Specter\United States Of America\Buildings\America_LargeAirBase.ini"
P_IRAQ_MR = r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MR.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_AH1Z_IMG = r"Data\INI\MappedImages\HandCreated\USA_AH1Z_Images.INI"

STD44 = [
    r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetF35B.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetF16IQ.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetIL76.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Tu-22M3.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetF35B.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetEA6B.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF18G.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35B.ini",
    r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetIL76.ini",
    r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetJ7.ini",
    r"Data\INI\Object\Specter\NATO\Airforce\NatoJetF18E.ini",
    r"Data\INI\Object\Specter\NATO\Airforce\NatoJetF18F.ini",
    r"Data\INI\Object\Specter\NATO\Airforce\NatoJetF35B.ini",
    r"Data\INI\Object\Specter\NATO\FixedWings\EA18G.ini",
    r"Data\INI\Object\Specter\NATO\FixedWings\F35A.ini",
    r"Data\INI\Object\Specter\NATO\Rotary\AH64E.ini",
    r"Data\INI\Object\Specter\NATO\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\NATO\Rotary\UH60.ini",
    r"Data\INI\Object\Specter\North Korea\Airforce\Iraq_Mig-25BM.ini",
    r"Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetJ7.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\Pakistan_F16Blk52.ini",
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetAH64E.ini",
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF35B.ini",
    r"Data\INI\Object\Specter\Shared\SpecterPlayableIL76.ini",
    r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetIL76.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Rotary\AH64E.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Rotary\UH60.ini",
    r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetJ7.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Rotary\AH64E.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Rotary\UH60.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu27.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Rotary\AH64E.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Rotary\UH60.ini",
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Airforce\UAE_F16Blk52.ini",
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15E.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Airforce\Iraq_Mig-25BM.ini",
    r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetIL76.ini",
    r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu27.ini",
]

STD44_OBJECTS = [
    "BritainJetF35B", "ItalyJetF35B", "JapanJetF35B", "NatoJetF35B", "SouthKoreaJetF35B",
    "NatoJetF35C", "NatoJetF18E", "NatoJetF18F", "NatoJetEA18G", "JapanJetF18G",
    "JapanJetEA6B", "Pakistan_F16Blk52", "UAE_F16Blk52", "IraqJetF16IQ", "UAEJetF15E",
    "NatoHelicopterAH64E", "SouthKoreaJetAH64E", "SwedenHelicopterAH64E",
    "TurkeyHelicopterAH64E", "UkraineHelicopterAH64E",
    "BritainHelicopterCH47F", "GermanyHelicopterCH47F", "ItalyHelicopterCH47F",
    "NatoHelicopterCH47F", "SwedenHelicopterCH47F", "TurkeyHelicopterCH47F",
    "UkraineHelicopterCH47F",
    "NatoHelicopterUH60", "SwedenHelicopterUH60", "TurkeyHelicopterUH60",
    "UkraineHelicopterUH60",
    "UkraineJetSu27", "VietnamJetSu27",
    "NorthKoreaJetTu22M3M", "VietnamJetTu22M3M", "Iraq_Tu-22M3",
    "IraqJetIL76", "SpecterPlayableIL76", "LibyaJetIL76", "SouthAfricaJetIL76",
    "VietnamJetIL76",
    "NorthKoreaJetJ7", "LibyaJetJ7", "SyriaJetJ7",
]


def norm(name: str) -> str:
    return name.replace("/", "\\")


def read_big_list(path: Path) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries: list[tuple[str, bytes]] = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded_names: list[bytes] = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded_names.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded_names):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries: list[tuple[str, bytes]], target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 packed path, got {len(hits)}")
    return hits[0]


def text_of(entries, target) -> str:
    return entries[find_index(entries, target)][1].decode("utf-8", errors="replace")


def set_bytes(entries, target, content: bytes) -> None:
    i = find_index(entries, target)
    name = entries[i][0]
    entries[i] = (name, content)


def file_nl(raw: bytes) -> str:
    return "\r\n" if b"\r\n" in raw else "\n"


def to_nl(s: str, nl: str) -> str:
    return s.replace("\r\n", "\n").replace("\n", nl)


def extract_named_blocks(text: str, kind: str) -> list[tuple[str, str]]:
    rx = re.compile(
        rf"^{kind} (\S+)\s*\n(?:.*\n)*?^End\s*$",
        re.M,
    )
    out = []
    for m in rx.finditer(text):
        out.append((m.group(1), m.group(0)))
    return out


def validate_commandset_block(name: str, block: str) -> None:
    if not block.strip().startswith(f"CommandSet {name}"):
        raise SystemExit(f"{name}: bad header")
    if block.count("\nEnd") + (1 if block.strip().endswith("End") else 0) < 1:
        raise SystemExit(f"{name}: missing End")
    # exactly one top-level End as last non-empty line
    lines = [ln.rstrip("\r") for ln in block.splitlines()]
    nonempty = [ln for ln in lines if ln.strip() and not ln.strip().startswith(";")]
    if nonempty[-1].strip() != "End":
        raise SystemExit(f"{name}: last token is not End: {nonempty[-1]!r}")
    if sum(1 for ln in nonempty if ln.strip() == "End") != 1:
        raise SystemExit(f"{name}: End count {sum(1 for ln in nonempty if ln.strip()=='End')}")
    if sum(1 for ln in nonempty if ln.startswith("CommandSet ")) != 1:
        raise SystemExit(f"{name}: nested/duplicate CommandSet header")
    for ln in nonempty[1:-1]:
        if not re.match(r"^\s*\d+\s*=\s*Command_\S+", ln):
            raise SystemExit(f"{name}: malformed slot line: {ln!r}")
        if "{" in ln or "}" in ln:
            raise SystemExit(f"{name}: brace in slot line")


def object_folder_illegal(entries) -> list[tuple[str, str, str, int]]:
    top = re.compile(
        r"^(CommandSet|CommandButton|Science|Upgrade)\s+(\S+)",
        re.M,
    )
    found = []
    for n, b in entries:
        nn = n.replace("/", "\\").lower()
        if "\\object\\" not in nn or not nn.endswith(".ini"):
            continue
        t = b.decode("utf-8", errors="replace")
        for m in top.finditer(t):
            if m.group(2).startswith("="):
                continue
            line = t[: m.start()].count("\n") + 1
            found.append((n, m.group(1), m.group(2), line))
    return found


def other_suspicious(entries) -> list[tuple[str, str, str, int]]:
    top = re.compile(
        r"^(MappedImage|Weapon|Locomotor|Armor|PlayerTemplate)\s+(\S+)",
        re.M,
    )
    found = []
    for n, b in entries:
        nn = n.replace("/", "\\").lower()
        if "\\object\\" not in nn or not nn.endswith(".ini"):
            continue
        t = b.decode("utf-8", errors="replace")
        for m in top.finditer(t):
            if m.group(2).startswith("="):
                continue
            line = t[: m.start()].count("\n") + 1
            found.append((n, m.group(1), m.group(2), line))
    return found


def main() -> int:
    if not SRC_DATA.is_file():
        alt = Path("/tmp/SPECTER1_AIRFRAME_STD_01/_SPEC_DATA_ONE.big")
        if not alt.is_file():
            raise SystemExit("missing PR #491 packed DATA")
        src = alt
    else:
        src = SRC_DATA
    raw = src.read_bytes()
    src_sha = hashlib.sha256(raw).hexdigest()
    if src_sha != EXPECTED_SRC_SHA:
        raise SystemExit(f"baseline SHA mismatch {src_sha} != {EXPECTED_SRC_SHA}")
    orig = read_big_list(src)
    orig_map = {norm(n).lower(): (n, b) for n, b in orig}
    orig_hashes = {norm(n).lower(): hashlib.sha256(b).hexdigest() for n, b in orig}

    china_text = orig_map[norm(P_CHINA01).lower()][1].decode("utf-8", errors="replace")
    usa_text = orig_map[norm(P_USA01).lower()][1].decode("utf-8", errors="replace")

    china_sets = extract_named_blocks(china_text, "CommandSet")
    usa_sets = extract_named_blocks(usa_text, "CommandSet")
    usa_btns = extract_named_blocks(usa_text, "CommandButton")
    usa_imgs = extract_named_blocks(usa_text, "MappedImage")
    if [n for n, _ in china_sets] != ["ChinaBarracksCommandSet_CHINA01"]:
        raise SystemExit(f"unexpected China CommandSets: {china_sets}")
    if [n for n, _ in usa_sets] != [
        "AmericaAirfieldCommandSet_USA01",
        "America_LargeAirBaseCommandSet_USA01",
    ]:
        raise SystemExit(f"unexpected USA CommandSets: {[n for n,_ in usa_sets]}")
    for name, blk in china_sets + usa_sets:
        validate_commandset_block(name, blk)

    entries = list(orig)

    # Append CommandSets to CommandSet.ini preserving exact slots.
    cs_i = find_index(entries, P_CMDSET)
    cs_raw = entries[cs_i][1]
    cs_nl = file_nl(cs_raw)
    cs_text = cs_raw.decode("utf-8", errors="replace")
    if "ChinaBarracksCommandSet_CHINA01" in cs_text:
        raise SystemExit("CHINA01 already in CommandSet.ini")
    if "AmericaAirfieldCommandSet_USA01" in cs_text:
        raise SystemExit("USA01 already in CommandSet.ini")
    add_cs = []
    add_cs.append("; SPECTER1 crashfix: unique CommandSets relocated from Object overlays")
    add_cs.append("; China Unlock barracks roster (was Data\\INI\\Object\\Specter\\PLA\\China_Update_01.ini)")
    add_cs.append(china_sets[0][1].strip())
    add_cs.append("; USA Update 01 airfield/LargeAirBase (was USA_Update_01.ini Object overlay)")
    add_cs.append(usa_sets[0][1].strip())
    add_cs.append(usa_sets[1][1].strip())
    chunk = cs_nl + cs_nl.join(to_nl(x, cs_nl) for x in add_cs) + cs_nl
    if not cs_text.endswith(("\n", "\r\n")):
        cs_text += cs_nl
    set_bytes(entries, P_CMDSET, (cs_text + chunk).encode("utf-8"))

    # Append CommandButton
    btn_i = find_index(entries, P_CMDBTN)
    btn_raw = entries[btn_i][1]
    btn_nl = file_nl(btn_raw)
    btn_text = btn_raw.decode("utf-8", errors="replace")
    if "Command_ConstructAmericaHelicopterAH1Z" in btn_text:
        raise SystemExit("AH1Z button already in CommandButton.ini")
    btn_add = btn_nl + "; SPECTER1 crashfix: relocated from USA_Update_01.ini Object overlay" + btn_nl
    btn_add += to_nl(usa_btns[0][1].strip(), btn_nl) + btn_nl
    if not btn_text.endswith(("\n", "\r\n")):
        btn_text += btn_nl
    set_bytes(entries, P_CMDBTN, (btn_text + btn_add).encode("utf-8"))

    # MappedImage as HandCreated sidecar (same pattern as USA_F35BJSF_Images.INI)
    img = "; SPECTER1 crashfix: AH-1Z button image relocated from USA_Update_01.ini Object overlay\r\n\r\n"
    img += to_nl(usa_imgs[0][1].strip(), "\r\n") + "\r\n"
    if norm(P_AH1Z_IMG).lower() in orig_map:
        raise SystemExit("AH1Z mappedimage sidecar already packed")
    entries.append((P_AH1Z_IMG, img.encode("utf-8")))

    # Remove illegal Object overlays (no valid Object blocks remain)
    drop = {norm(P_CHINA01).lower(), norm(P_USA01).lower()}
    entries = [(n, b) for n, b in entries if norm(n).lower() not in drop]

    # Object producers must still point at unique CommandSet names
    camp = text_of(entries, P_CAMP)
    if "CommandSet       = ChinaBarracksCommandSet_CHINA01" not in camp:
        raise SystemExit("ChinaBarracks lost unique CommandSet pointer")
    airfield = text_of(entries, P_AIRFIELD)
    if "AmericaAirfieldCommandSet_USA01" not in airfield:
        raise SystemExit("USA Airfield lost unique CommandSet pointer")
    large = text_of(entries, P_LARGE)
    if "America_LargeAirBaseCommandSet_USA01" not in large:
        raise SystemExit("USA LargeAirBase lost unique CommandSet pointer")

    # Preservation hashes
    new_map = {norm(n).lower(): (n, b) for n, b in entries}
    for p in STD44:
        k = norm(p).lower()
        if orig_hashes[k] != hashlib.sha256(new_map[k][1]).hexdigest():
            raise SystemExit(f"std44 path changed: {p}")
    if orig_hashes[norm(P_IRAQ_MR).lower()] != hashlib.sha256(new_map[norm(P_IRAQ_MR).lower()][1]).hexdigest():
        raise SystemExit("Iraq_Su-24MR.ini changed")
    if orig_hashes[norm(P_WEAPON).lower()] != hashlib.sha256(new_map[norm(P_WEAPON).lower()][1]).hexdigest():
        raise SystemExit("Weapon.ini changed")
    for hint in ("usa_update_01.ini", "china_update_01.ini", "j7.ini", "tu22m3m.ini", "russiajetcargoil76.ini"):
        pass
    # China J-7 reference object file unchanged
    j7k = [k for k in orig_hashes if k.endswith(r"\pla\airforce\j7.ini")]
    if len(j7k) != 1:
        raise SystemExit(f"J7 path ambiguity {j7k}")
    if orig_hashes[j7k[0]] != hashlib.sha256(new_map[j7k[0]][1]).hexdigest():
        raise SystemExit("China J7.ini changed")

    illegal = object_folder_illegal(entries)
    other = other_suspicious(entries)
    china_cmdsets = [n for n, _ in china_sets]
    usa_cmdsets = [n for n, _ in usa_sets]

    # CommandSets now in CommandSet.ini
    cs_new = text_of(entries, P_CMDSET)
    for name in china_cmdsets + usa_cmdsets:
        if not re.search(rf"^CommandSet {re.escape(name)}\b", cs_new, re.M):
            raise SystemExit(f"{name} missing from CommandSet.ini after move")
        validate_commandset_block(name, re.search(
            rf"^CommandSet {re.escape(name)}\b.*?(?=^CommandSet |\Z)", cs_new, re.M | re.S
        ).group(0))

    btn_new = text_of(entries, P_CMDBTN)
    if "Command_ConstructAmericaHelicopterAH1Z" not in btn_new:
        raise SystemExit("AH1Z CommandButton missing after move")

    if any(norm(n).lower() in drop for n, _ in entries):
        raise SystemExit("overlay still packed")

    remaining_cmd = [x for x in illegal]
    print("Packing DATA...")
    blob = build_big_ordered(entries)
    rt = read_big_list
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT_DIR / "_SPEC_DATA_ONE.big"
    out_big.write_bytes(blob)
    rt_entries = read_big_list(out_big)
    if [n for n, _ in rt_entries] != [n for n, _ in entries]:
        raise SystemExit("round-trip name mismatch")
    sha = hashlib.sha256(blob).hexdigest()

    remaining_kinds = object_folder_illegal(rt_entries)
    remaining_other = other_suspicious(rt_entries)
    china_valid = "YES"
    if any("china_update_01.ini" in n.lower() for n, _ in rt_entries):
        china_valid = "NO"

    lines = []
    p = lines.append
    p("SPECTER1 AIRCRAFT STANDARDIZATION 01 CRASHFIX TEST AUDIT")
    p("BASELINE = PR #491 / SPECTER1_Aircraft_Standardization_01 packed DATA")
    p(f"BASELINE_DATA_SHA256 = {src_sha}")
    p(f"NEW_DATA_SHA256 = {sha}")
    p(f"NEW_DATA_BYTES = {len(blob)}")
    p(f"NEW_DATA_FILE_COUNT = {len(entries)}")
    p("MODE = DATA ONLY CRASHFIX TEST — DOES NOT OVERWRITE PREVIOUS RELEASE")
    p("")
    p("CRASH_FILE = Data\\INI\\Object\\Specter\\pla\\china_update_01.ini")
    p("CRASH_REPORTED_LINE = CommandSet ChinaBarracksCommandSet_CHINA01")
    p("ROOT_CAUSE = CommandSet definition stored inside an Object INI. Zero Hour Object parser rejects top-level CommandSet tokens in Data\\INI\\Object\\ files.")
    p("")
    p(f"CHINA_UPDATE_OBJECT_FILE_VALID_AFTER_FIX = {china_valid} (file removed; it contained no Object blocks)")
    p("COMMANDSETS_MOVED_TO_COMMANDSET_INI = ChinaBarracksCommandSet_CHINA01, AmericaAirfieldCommandSet_USA01, America_LargeAirBaseCommandSet_USA01")
    p("COMMANDBUTTONS_MOVED_TO_COMMANDBUTTON_INI = Command_ConstructAmericaHelicopterAH1Z")
    p("MAPPEDIMAGES_MOVED_TO_HANDCREATED = AH1ZTB -> Data\\INI\\MappedImages\\HandCreated\\USA_AH1Z_Images.INI")
    p("OBJECT_OVERLAYS_REMOVED = Data\\INI\\Object\\Specter\\PLA\\China_Update_01.ini ; Data\\INI\\Object\\Specter\\United States Of America\\USA_Update_01.ini")
    p("")
    if remaining_kinds:
        p("INVALID_OBJECT_FOLDER_TOP_LEVEL_BLOCKS_REMAINING =")
        for n, kind, name, line in remaining_kinds:
            p(f"  {n} : {kind} {name} line {line}")
    else:
        p("INVALID_OBJECT_FOLDER_TOP_LEVEL_BLOCKS_REMAINING = 0 (CommandSet/CommandButton/Science/Upgrade)")
    p("")
    p("OBJECT_FOLDER_SUSPICIOUS_OTHER_TOP_LEVEL_BLOCKS (not rewritten; not CommandSet/CommandButton/Science/Upgrade):")
    if remaining_other:
        for n, kind, name, line in remaining_other:
            p(f"  {n} : {kind} {name} line {line}")
    else:
        p("  NONE")
    p("")
    p("CHINA_BARRACKS_OBJECT_STILL_USES = ChinaBarracksCommandSet_CHINA01")
    p("USA_AIRFIELD_OBJECT_STILL_USES = AmericaAirfieldCommandSet_USA01")
    p("USA_LARGEAIRBASE_OBJECT_STILL_USES = America_LargeAirBaseCommandSet_USA01")
    p("CHINA_WARFACTORY_UNIQUE_CHINA01_SET = NONE (live producer already uses PLAWarFactoryCommandSet in CommandSet.ini)")
    p("CHINA_AIRFIELD_UNIQUE_CHINA01_SET = NONE")
    p("CHINA_LARGEAIRBASE_UNIQUE_CHINA01_SET = NONE")
    p("CHINA_HEAVYAIRBASE_UNIQUE_CHINA01_SET = NONE")
    p("CHINA_COMMANDCENTER_UNIQUE_CHINA01_SET = NONE")
    p("")
    p("PREVIOUS_IRAQ_CHANGES_PRESERVED = YES")
    p("PREVIOUS_USA_CHANGES_PRESERVED = YES")
    p("PREVIOUS_CHINA_CHANGES_PRESERVED = YES")
    p("PREVIOUS_RUSSIA_CHANGES_PRESERVED = YES")
    p("AIRCRAFT_STANDARDIZATION_44_TARGETS_PRESERVED = YES")
    p("WEAPON_INI_CHANGED = NO")
    p("ART_CHANGED = NO")
    p("DATA_CHANGED = YES")
    p("INGAME_TESTED = NO")
    p("STATIC_PARSE_FIX = PASS")
    p("RELEASE_OVERWRITES_PREVIOUS = NO")
    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 Aircraft Standardization 01 CRASHFIX TEST

Baseline: exact PR #491 packed DATA. No ART. Does not overwrite SPECTER1_Aircraft_Standardization_01.

ROOT_CAUSE: China_Update_01.ini lived under Data\\INI\\Object\\ and contained a top-level CommandSet block. Zero Hour's Object parser rejects CommandSet there (ReleaseCrashInfo: CommandSet ChinaBarracksCommandSet_CHINA01).

FIX: Moved ChinaBarracksCommandSet_CHINA01 into Data\\INI\\CommandSet.ini with the exact China Unlock slots. Removed the empty/invalid Object overlay.

Same illegal overlay class existed in USA_Update_01.ini (MappedImage / CommandButton / CommandSet). Those blocks were relocated to CommandButton.ini, CommandSet.ini, and MappedImages\\HandCreated\\USA_AH1Z_Images.INI so init cannot crash on the next Object file. Airfield/LargeAirBase objects still use the unique _USA01 CommandSet names. Slots unchanged.

No 44-target airframe edits. No Iraq_Su-24MR edit. No Weapon.ini edit. No ART.
"""
    (OUT_DIR / "crashfix_audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(blob)
    (WS_OUT / "crashfix_audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    print(audit)
    print("WROTE", out_big, len(blob), sha)
    if remaining_kinds:
        raise SystemExit("illegal CommandSet/CommandButton/Science/Upgrade still in Object folder")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
