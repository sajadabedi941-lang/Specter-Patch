#!/usr/bin/env python3
"""PR #385 baseline + isolated Russia Large Air Base additions.

Stock CommandButton.ini / Weapon.ini / Russia_System.ini / CSF / existing
aircraft stay untouched.

CommandSet.ini is the one live file that is surgically updated:
  Russia_LargeAirBaseCommandSet keeps slots 1-9 and 13-14 from #385.
  Slot 10 is Su-39 (replaces Su47 Recon). Slot 11 is Su-47 Berkut.
  Slot 12 is Dozor-600 (replaces empty T-50). Slot 15 stays isolated Su-75.
  No overlay CommandSet file. No second Russia_LargeAirBaseCommandSet.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from russia_air_buttons import (
    CSF_STRINGS,
    NEW_CONSTRUCT_BUTTONS,
    add_csf_strings,
    decode_csf_labels,
    parse_commandbutton_block,
    patch_commandbutton_ini,
    render_live_commandset_buttons,
)

DATA_SRC = Path("/tmp/russia_su35s_ka52/_SPEC_DATA_ONE.big")
ART_SRC = Path("/tmp/radar_pkg/_SPEC_ART_ONE.big")
PATCH = Path("/workspace/patch")
OUT = Path("/tmp/russia_four_fighters")

CS_KEY = r"data\ini\commandset.ini"
CB_KEY = r"data\ini\commandbutton.ini"
CSF_KEY = r"data\english\generals.csf"
LARGE_NAME = "Russia_LargeAirBaseCommandSet"

OLD_LARGE = (
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
NEW_LARGE = (
    "CommandSet Russia_LargeAirBaseCommandSet\n"
    "  1  = Command_ConstructRussiaJetSuT75\n"
    "  2  = Command_ConstructRussiaJetSu35S\n"
    "  3  = Command_ConstructRussiaJetSu30SM2\n"
    "  4  = Command_ConstructRussiaJetSU25T\n"
    "  5  = Command_ConstructRussiaJetSu35AG\n"
    "  6  = Command_ConstructRussiaJetMig31K\n"
    "  7  = Command_ConstructRussiaHelicopterMi28N\n"
    "  8  = Command_ConstructRussiaHelicopterKA52\n"
    "  9  = Command_ConstructRussiaJetSu57AA\n"
    "  10 = Command_ConstructRussiaJetSu39\n"
    "  11 = Command_ConstructRussiaJetSu47Berkut\n"
    "  12 = Command_ConstructRussiaJetDozor600\n"
    "  13 = Command_ConstructRussiaJetSu57Felon\n"
    "  14 = Command_ConstructRussiaJetSuT50PAKFA\n"
    "  15 = Command_ConstructRussiaJetSu35Flanker\n"
    "  16 = Command_ConstructRussiaJetSu24MR\n"
    "End"
)

# CommandButtons must live in CommandSet.ini before the Large set AND in
# CommandButton.ini so UNIT_BUILD can resolve the object. Extra
# CommandButton_*.ini files are not packed.
LIVE_BUTTONS = render_live_commandset_buttons()

EXPECTED_SLOTS = {
    1: "Command_ConstructRussiaJetSuT75",
    2: "Command_ConstructRussiaJetSu35S",
    3: "Command_ConstructRussiaJetSu30SM2",
    4: "Command_ConstructRussiaJetSU25T",
    5: "Command_ConstructRussiaJetSu35AG",
    6: "Command_ConstructRussiaJetMig31K",
    7: "Command_ConstructRussiaHelicopterMi28N",
    8: "Command_ConstructRussiaHelicopterKA52",
    9: "Command_ConstructRussiaJetSu57AA",
    10: "Command_ConstructRussiaJetSu39",
    11: "Command_ConstructRussiaJetSu47Berkut",
    12: "Command_ConstructRussiaJetDozor600",
    13: "Command_ConstructRussiaJetSu57Felon",
    14: "Command_ConstructRussiaJetSuT50PAKFA",
    15: "Command_ConstructRussiaJetSu35Flanker",
    16: "Command_ConstructRussiaJetSu24MR",
}

FROZEN_SLOTS = (2, 3, 4, 5, 6, 7, 8, 9)
REMOVED_MENU_BUTTONS = (
    "Command_ConstructRussiaJetSu47Recon",
    "Command_ConstructRussiaJetSu57T50",
    "Command_ConstructRussiaJetSu75Checkmate",
    "Command_ConstructRussiaJetSu75",
    "Command_SetRallyPoint",
    "Command_Sell",
)

AIRFORCE = PATCH / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"

NEW_DATA = {
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su47Berkut.ini": AIRFORCE
    / "Su47Berkut.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su57T50.ini": AIRFORCE
    / "Su57T50.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su75Checkmate.ini": AIRFORCE
    / "Su75Checkmate.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su39.ini": AIRFORCE / "Su39.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Dozor600.ini": AIRFORCE
    / "Dozor600.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su57Felon.ini": AIRFORCE
    / "Su57Felon.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\SuT75.ini": AIRFORCE / "SuT75.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\SuT50PAKFA.ini": AIRFORCE
    / "SuT50PAKFA.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su35Flanker.ini": AIRFORCE
    / "Su35Flanker.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su24MR.ini": AIRFORCE / "Su24MR.ini",
    r"Data\INI\MappedImages\HandCreated\Russia_Dozor600_Images.INI": PATCH
    / "Data/INI/MappedImages/HandCreated/Russia_Dozor600_Images.INI",
}

NEW_ART = {
    r"Art\W3D\RUSU-47.W3D": PATCH / "Art/W3D/RUSU-47.W3D",
    r"Art\W3D\RUSU-47_D.W3D": PATCH / "Art/W3D/RUSU-47_D.W3D",
    r"Art\W3D\RUSU-47_E.W3D": PATCH / "Art/W3D/RUSU-47_E.W3D",
    r"Art\Textures\RUSU-47mainskin.tga": PATCH / "Art/Textures/RUSU-47mainskin.tga",
    r"Art\Textures\RUSU-47mainskin_D.tga": PATCH / "Art/Textures/RUSU-47mainskin_D.tga",
    r"Art\Textures\RUSU-47mainskin_E.tga": PATCH / "Art/Textures/RUSU-47mainskin_E.tga",
    r"Art\Textures\RUSU47MAP.dds": PATCH / "Art/Textures/RUSU47MAP.dds",
    r"Art\W3D\LSFT50.W3D": PATCH / "Art/W3D/LSFT50.W3D",
    r"Art\W3D\LSFT50d.W3D": PATCH / "Art/W3D/LSFT50d.W3D",
    r"Art\W3D\LSFT50k.W3D": PATCH / "Art/W3D/LSFT50k.W3D",
    r"Art\Textures\LSFT50.dds": PATCH / "Art/Textures/LSFT50.dds",
    r"Art\Textures\LSFT50d.dds": PATCH / "Art/Textures/LSFT50d.dds",
    r"Art\Textures\LSFT50k.dds": PATCH / "Art/Textures/LSFT50k.dds",
    r"Art\W3D\RUSU75.W3D": PATCH / "Art/W3D/RUSU75.W3D",
    r"Art\W3D\RUSU75_D.W3D": PATCH / "Art/W3D/RUSU75_D.W3D",
    r"Art\W3D\RUSU75_E.W3D": PATCH / "Art/W3D/RUSU75_E.W3D",
    r"Art\W3D\RUSU75_E1.W3D": PATCH / "Art/W3D/RUSU75_E1.W3D",
    r"Art\W3D\RUSU75_E2.W3D": PATCH / "Art/W3D/RUSU75_E2.W3D",
    r"Art\Textures\SU-75.dds": PATCH / "Art/Textures/SU-75.dds",
    r"Art\Textures\SU-75_D.dds": PATCH / "Art/Textures/SU-75_D.dds",
    r"Art\Textures\SU-75_E.dds": PATCH / "Art/Textures/SU-75_E.dds",
    r"Art\W3D\AVReaper.W3D": PATCH / "Art/W3D/AVReaper.W3D",
    r"Art\W3D\AVReaper_D.W3D": PATCH / "Art/W3D/AVReaper_D.W3D",
    r"Art\W3D\AVReaper_D1.W3D": PATCH / "Art/W3D/AVReaper_D1.W3D",
    r"Art\W3D\AVReaper_P.W3D": PATCH / "Art/W3D/AVReaper_P.W3D",
    r"Art\Textures\AVReaper.dds": PATCH / "Art/Textures/AVReaper.dds",
    r"Art\Textures\AVReaper_D.dds": PATCH / "Art/Textures/AVReaper_D.dds",
    r"Art\Textures\AVReaper_D1.dds": PATCH / "Art/Textures/AVReaper_D1.dds",
    r"Art\Textures\Dozor600.tga": PATCH / "Art/Textures/Dozor600.tga",
    r"Art\Textures\Dozor600TB.tga": PATCH / "Art/Textures/Dozor600TB.tga",
    r"Art\W3D\LSFSU35.W3D": PATCH / "Art/W3D/LSFSU35.W3D",
    r"Art\W3D\LSFSU35d.W3D": PATCH / "Art/W3D/LSFSU35d.W3D",
    r"Art\W3D\LSFSU35k.W3D": PATCH / "Art/W3D/LSFSU35k.W3D",
    r"Art\Textures\RussiaSU35.dds": PATCH / "Art/Textures/RussiaSU35.dds",
    r"Art\Textures\RussiaSU35d.dds": PATCH / "Art/Textures/RussiaSU35d.dds",
    r"Art\Textures\RussiaSU35k.dds": PATCH / "Art/Textures/RussiaSU35k.dds",
    r"Art\W3D\SU24MP.W3D": PATCH / "Art/W3D/SU24MP.W3D",
    r"Art\W3D\SU24MPA.W3D": PATCH / "Art/W3D/SU24MPA.W3D",
    r"Art\Textures\SU24MP1.tga": PATCH / "Art/Textures/SU24MP1.tga",
}

FROZEN = (
    r"data\ini\weapon.ini",
    r"data\ini\upgrade.ini",
    r"data\ini\object\specter\armed forces of russian federation\russia_system.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su35s.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\ka52m.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su57.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su57_aa.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su25t_su39.ini",
    r"data\ini\object\specter\armed forces of russian federation\buildings\russia_largeairbase.ini",
)

REQUIRED_OBJECTS = {
    "RussiaJetSu47Berkut": "RUSU-47",
    "RussiaJetSu57T50": "LSFT50",
    "RussiaJetSu75": "RUSU75",
    "RussiaJetSu39": "RUS_SU39",
    "RussiaJetDozor600": "AVReaper",
    "RussiaJetSu57Felon": "RUS_SU57",
    "RussiaJetSuT75": "RUSU75",
    "RussiaJetSuT50PAKFA": "LSFT50",
    "RussiaJetSu35Flanker": "LSFSU35",
    "RussiaJetSu24MR": "SU24MP",
}

FORBIDDEN_REUSED_OBJECTS = (
    "RussiaJetSu75Checkmate",
    "RussiaJetSU25T",
    "RussiaJetSU25T_UCAS",
    "RussiaJetSu47Recon",
    "RussiaJetSu57",
    "RussiaJetSu57AA",
    "RussiaJetSu35S",
    "RussiaJetSu34",
    "RussiaHelicopterKA52",
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
            raise SystemExit(f"refusing to replace existing file: {n}")
    entries.append((name.replace("/", "\\"), content))


def replace_existing(entries: list[tuple[str, bytes]], name: str, content: bytes) -> None:
    key = name.replace("/", "\\").lower()
    for i, (n, _) in enumerate(entries):
        if n.replace("/", "\\").lower() == key:
            entries[i] = (n, content)
            return
    raise SystemExit(f"missing existing file to replace: {name}")


def parse_commandset_block(text: str, name: str, max_slot: int = 16) -> dict:
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
    slots = {}
    for lineno, line in enumerate(m.group("body").splitlines(), 1):
        raw = line.split(";", 1)[0].rstrip()
        if not raw.strip():
            continue
        sm = re.match(r"^  (\d+)\s*=\s*(\S+)\s*$", raw)
        if not sm:
            raise SystemExit(f"parser FAIL: {name} bad line {lineno}: {raw!r}")
        slot = int(sm.group(1))
        if slot in slots:
            raise SystemExit(f"parser FAIL: {name} duplicate slot {slot}")
        if slot < 1 or slot > max_slot:
            raise SystemExit(f"parser FAIL: {name} slot {slot} out of range")
        slots[slot] = sm.group(2)
    return {"block": rest[: m.end()], "slots": slots}


def check_ini_bytes(raw: bytes, label: str) -> str:
    if raw[:2] == b"\xff\xfe" or raw[:3] == b"\xef\xbb\xbf":
        raise SystemExit(f"parser FAIL: {label} has a BOM")
    if b"\r\n" in raw:
        raise SystemExit(f"parser FAIL: {label} has CRLF")
    text = raw.decode("latin1")
    if text.count("End") < 1:
        raise SystemExit(f"parser FAIL: {label} has no End")
    return text


def patch_commandset(raw: bytes) -> bytes:
    text = check_ini_bytes(raw, "source CommandSet.ini")
    if text.count("CommandSet Russia_LargeAirBaseCommandSet") != 1:
        raise SystemExit("parser FAIL: source CommandSet.ini Large set is not unique")
    if OLD_LARGE not in text:
        raise SystemExit("parser FAIL: #385 Russia_LargeAirBaseCommandSet block not found")
    if text.count(OLD_LARGE) != 1:
        raise SystemExit("parser FAIL: #385 Large block matched more than once")
    replacement = LIVE_BUTTONS + NEW_LARGE
    patched = text.replace(OLD_LARGE, replacement, 1)
    if patched.replace(replacement, OLD_LARGE, 1) != text:
        raise SystemExit("parser FAIL: CommandSet rewrite was not a pure insert")
    if patched.count("CommandSet Russia_LargeAirBaseCommandSet") != 1:
        raise SystemExit("parser FAIL: patched file has duplicate Large set")
    if "Command_ConstructRussiaJetSU24MP" in patched:
        patched = patched.replace("Command_ConstructRussiaJetSU24MP", "Command_ConstructRussiaJetSu24MR")
    out = patched.encode("latin1")
    if b"\r\n" in out:
        raise SystemExit("parser FAIL: patched CommandSet.ini gained CRLF")
    return out


def parser_check_commandset_balance(text: str) -> None:
    """Every CommandSet must have a matching End/END. No leftover open blocks."""
    stack = []
    for lineno, line in enumerate(text.splitlines(), 1):
        raw = line.split(";", 1)[0].rstrip()
        m = re.match(r"^CommandSet\s+(\S+)\s*$", raw)
        if m:
            stack.append((lineno, m.group(1)))
            continue
        if raw.strip() in ("End", "END"):
            if stack:
                stack.pop()
    if stack:
        preview = ", ".join(f"{n}@{ln}" for ln, n in stack[:8])
        raise SystemExit(f"parser FAIL: unclosed CommandSet blocks: {preview}")
    print("PARSER CHECK PASS: every CommandSet has matching End/END")


def parser_check_live_commandset(raw: bytes) -> None:
    text = check_ini_bytes(raw, "CommandSet.ini")
    if text.count("CommandSet Russia_LargeAirBaseCommandSet") != 1:
        raise SystemExit("parser FAIL: duplicated Russia_LargeAirBaseCommandSet in CommandSet.ini")
    parser_check_commandset_balance(text)
    parsed = parse_commandset_block(text, LARGE_NAME, max_slot=16)
    if parsed["block"] != NEW_LARGE:
        raise SystemExit("parser FAIL: live Russia_LargeAirBaseCommandSet body mismatch")
    if parsed["slots"] != EXPECTED_SLOTS:
        raise SystemExit(f"parser FAIL: live Large slots {parsed['slots']}")
    for slot in FROZEN_SLOTS:
        if parsed["slots"][slot] != EXPECTED_SLOTS[slot]:
            raise SystemExit(f"parser FAIL: existing slot {slot} changed")
    if parsed["slots"].get(10) == "Command_ConstructRussiaJetSu47Recon":
        raise SystemExit("parser FAIL: Su47 Recon is still in slot 10")
    if parsed["slots"].get(1) == "Command_ConstructRussiaJetSu75Checkmate":
        raise SystemExit("parser FAIL: packed Checkmate is still in slot 1")
    if parsed["slots"].get(13) == "Command_SetRallyPoint":
        raise SystemExit("parser FAIL: Rally is still in slot 13")
    if parsed["slots"].get(14) == "Command_Sell":
        raise SystemExit("parser FAIL: Sell is still in slot 14")
    btn_pos = {}
    for btn in NEW_CONSTRUCT_BUTTONS:
        m = re.search(rf"^CommandButton {re.escape(btn)}\s*$", text, re.M)
        if not m:
            raise SystemExit(f"parser FAIL: CommandSet.ini missing CommandButton {btn}")
        btn_pos[btn] = m.start()
    if re.search(r"^CommandButton Command_ConstructRussiaJetSu57T50\s*$", text, re.M):
        raise SystemExit("parser FAIL: T-50 CommandButton visibility still in CommandSet.ini")
    set_pos = text.find("CommandSet Russia_LargeAirBaseCommandSet")
    if any(pos > set_pos for pos in btn_pos.values()):
        raise SystemExit("parser FAIL: CommandButtons must appear before Russia_LargeAirBaseCommandSet")
    print("PARSER CHECK PASS: live CommandSet.ini has unique Large set + Felon/T75/T50/Flanker/Su24MR")


def assert_no_duplicate_large(entries: list[tuple[str, bytes]]) -> None:
    hits = []
    for n, b in entries:
        if b"CommandSet Russia_LargeAirBaseCommandSet" in b:
            hits.append(n)
        key = n.replace("/", "\\").lower()
        if "commandset_zzzz" in key or key.endswith(r"commandset_zzzz_russia_largeairbase.ini"):
            raise SystemExit(f"parser FAIL: overlay CommandSet file still packed: {n}")
    if hits != [next(n for n, _ in entries if n.replace("/", "\\").lower() == CS_KEY)]:
        raise SystemExit(f"parser FAIL: Russia_LargeAirBaseCommandSet files={hits}")
    print("PARSER CHECK PASS: no duplicate Russia_LargeAirBaseCommandSet, no overlay file")


def collect_objects(entries: list[tuple[str, bytes]]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        text = b.decode("latin1", "replace")
        for obj in re.findall(r"^Object (\S+)", text, re.M):
            found.setdefault(obj, []).append(n)
    return found


def collect_buttons(entries: list[tuple[str, bytes]]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        text = b.decode("latin1", "replace")
        for btn in re.findall(r"^CommandButton (\S+)", text, re.M):
            found.setdefault(btn, []).append(n)
    return found


def verify_construct_create_path(
    data_entries: list[tuple[str, bytes]],
    art_map: dict[str, bytes],
    slot: int,
    btn: str,
    obj: str,
    model: str,
) -> None:
    data = {n.replace("/", "\\").lower(): b for n, b in data_entries}
    cs = parse_commandset_block(data[CS_KEY].decode("latin1"), LARGE_NAME, max_slot=16)
    cmd = cs["slots"].get(slot)
    if cmd != btn:
        raise SystemExit(f"CREATE FAIL: slot {slot} is {cmd}, expected {btn}")
    cb_text = data[CB_KEY].decode("latin1")
    parsed = parse_commandbutton_block(cb_text, btn)
    if not parsed:
        raise SystemExit(f"CREATE FAIL: CommandButton.ini missing {btn}")
    if parsed.get("Command") != "UNIT_BUILD":
        raise SystemExit(f"CREATE FAIL: {btn} is not UNIT_BUILD")
    if parsed.get("Object") != obj:
        raise SystemExit(f"CREATE FAIL: {btn} Object {parsed.get('Object')} != {obj}")
    objects = collect_objects(data_entries)
    files = objects.get(obj, [])
    if len(files) != 1:
        raise SystemExit(f"CREATE FAIL: Object {obj} files={files}")
    obj_text = data[files[0].replace("/", "\\").lower()].decode("latin1")
    if "AIRCRAFT" not in obj_text or not re.search(r"BuildCost\s+=\s+\d+", obj_text):
        raise SystemExit(f"CREATE FAIL: {obj} is not a buildable aircraft")
    weapons = re.findall(r"^\s+Weapon\s+=\s+\S+\s+(\S+)\s*$", obj_text, re.M)
    weapon_ini = data[r"data\ini\weapon.ini"].decode("latin1")
    for wpn in weapons:
        if not re.search(rf"^Weapon {re.escape(wpn)}\s*$", weapon_ini, re.M):
            raise SystemExit(f"CREATE FAIL: packed Weapon.ini missing {wpn}")
    model_key = rf"art\w3d\{model}.w3d".lower()
    if model_key not in art_map:
        raise SystemExit(f"CREATE FAIL: {model}.W3D not packed in ART")
    csf_names = decode_csf_labels(data[CSF_KEY])
    label = parsed.get("TextLabel")
    if label not in csf_names:
        raise SystemExit(f"CREATE FAIL: CSF missing {label}")
    print(f"CREATE PATH PASS: slot {slot} {btn} -> {obj} model {model}")


def verify_new_object_file(path: Path, obj: str, model: str) -> None:
    raw = path.read_bytes()
    text = check_ini_bytes(raw, path.name)
    objs = re.findall(r"^Object (\S+)", text, re.M)
    if objs != [obj]:
        raise SystemExit(f"parser FAIL: {path.name} objects {objs} != [{obj}]")
    if not re.search(rf"Model\s+=\s+{re.escape(model)}\s*$", text, re.M):
        raise SystemExit(f"parser FAIL: {path.name} missing Model={model}")
    for banned in FORBIDDEN_REUSED_OBJECTS:
        if re.search(rf"^Object {re.escape(banned)}\s*$", text, re.M):
            raise SystemExit(f"parser FAIL: {path.name} redefines packed {banned}")
    print(f"PARSER CHECK PASS: {path.name} Object {obj} Model {model}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    overlay = PATCH / "Data/INI/CommandSet_ZZZZ_Russia_LargeAirBase.ini"
    if overlay.exists():
        raise SystemExit("refusing to pack: overlay CommandSet_ZZZZ_Russia_LargeAirBase.ini still exists")

    for obj, model, fname in (
        ("RussiaJetSu47Berkut", "RUSU-47", "Su47Berkut.ini"),
        ("RussiaJetSu57T50", "LSFT50", "Su57T50.ini"),
        ("RussiaJetSu75", "RUSU75", "Su75Checkmate.ini"),
        ("RussiaJetSu39", "RUS_SU39", "Su39.ini"),
        ("RussiaJetDozor600", "AVReaper", "Dozor600.ini"),
        ("RussiaJetSu57Felon", "RUS_SU57", "Su57Felon.ini"),
        ("RussiaJetSuT75", "RUSU75", "SuT75.ini"),
        ("RussiaJetSuT50PAKFA", "LSFT50", "SuT50PAKFA.ini"),
        ("RussiaJetSu35Flanker", "LSFSU35", "Su35Flanker.ini"),
        ("RussiaJetSu24MR", "SU24MP", "Su24MR.ini"),
    ):
        verify_new_object_file(AIRFORCE / fname, obj, model)

    src_entries = read_big(DATA_SRC)
    src_map = {n.replace("/", "\\").lower(): b for n, b in src_entries}
    baseline_cs = src_map[CS_KEY]
    baseline_text = check_ini_bytes(baseline_cs, "PR #385 CommandSet.ini")
    if parse_commandset_block(baseline_text, LARGE_NAME, max_slot=14)["block"] != OLD_LARGE:
        raise SystemExit("parser FAIL: source CommandSet.ini is not the #385 Large block")

    patched_cs = patch_commandset(baseline_cs)
    parser_check_live_commandset(patched_cs)

    patched_cb = patch_commandbutton_ini(src_map[CB_KEY])
    patched_csf = add_csf_strings(src_map[CSF_KEY])

    data_entries = list(src_entries)
    replace_existing(data_entries, r"Data\INI\CommandSet.ini", patched_cs)
    replace_existing(data_entries, r"Data\INI\CommandButton.ini", patched_cb)
    replace_existing(data_entries, r"Data\English\generals.csf", patched_csf)
    added = {
        r"Data\INI\CommandSet.ini": "Large Air Base slots + construct buttons",
        r"Data\INI\CommandButton.ini": "Russia aircraft construct buttons/icons",
        r"Data\English\generals.csf": "added missing construct/object labels",
    }
    for name, path in NEW_DATA.items():
        upsert_new_only(data_entries, name, path.read_bytes())
        added[name] = "added"

    new_map = {n.replace("/", "\\").lower(): b for n, b in data_entries}
    if new_map[CS_KEY] == src_map[CS_KEY]:
        raise SystemExit("parser FAIL: CommandSet.ini was not updated")
    for key in FROZEN:
        if src_map[key] != new_map[key]:
            raise SystemExit(f"existing file replaced: {key}")

    extra = sorted(set(new_map) - set(src_map))
    expected_extra = {k.replace("/", "\\").lower() for k in NEW_DATA}
    if set(extra) != expected_extra:
        raise SystemExit(f"unexpected added DATA files: {sorted(set(extra) ^ expected_extra)}")

    assert_no_duplicate_large(data_entries)
    parser_check_live_commandset(new_map[CS_KEY])

    objects = collect_objects(data_entries)
    for obj in REQUIRED_OBJECTS:
        files = objects.get(obj, [])
        if len(files) != 1:
            raise SystemExit(f"parser FAIL: Object {obj} files={files}")
        print(f"OBJECT UNIQUE PASS: {obj} -> {files[0]}")
    for banned in FORBIDDEN_REUSED_OBJECTS:
        if banned not in objects:
            raise SystemExit(f"parser FAIL: expected packed object missing: {banned}")

    buttons = collect_buttons(data_entries)
    cb_text = new_map[CB_KEY].decode("latin1")
    for btn, spec in NEW_CONSTRUCT_BUTTONS.items():
        files = [f.replace("/", "\\").lower() for f in buttons.get(btn, [])]
        if CS_KEY not in files:
            raise SystemExit(f"parser FAIL: CommandButton {btn} missing from CommandSet.ini ({files})")
        if CB_KEY not in files:
            raise SystemExit(f"parser FAIL: CommandButton {btn} missing from CommandButton.ini ({files})")
        parsed_cb = parse_commandbutton_block(cb_text, btn)
        if not parsed_cb or parsed_cb.get("Object") != spec["Object"]:
            raise SystemExit(f"parser FAIL: CommandButton.ini {btn} Object mismatch")
        if parsed_cb.get("Command") != "UNIT_BUILD":
            raise SystemExit(f"parser FAIL: {btn} is not UNIT_BUILD")
        print(f"BUTTON IN CommandButton.ini+CommandSet.ini PASS: {btn} -> {spec['Object']}")

    parsed_large = parse_commandset_block(new_map[CS_KEY].decode("latin1"), LARGE_NAME, max_slot=16)
    for removed in REMOVED_MENU_BUTTONS:
        if removed in parsed_large["slots"].values():
            raise SystemExit(f"parser FAIL: removed menu button still slotted: {removed}")

    mapped = new_map[r"data\ini\mappedimages\handcreated\russia_dozor600_images.ini".lower()].decode("latin1")
    if "MappedImage Dozor600" not in mapped:
        raise SystemExit("parser FAIL: Dozor600 MappedImage missing")

    data_bytes = write_big(data_entries)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(data_bytes)

    written_entries = read_big(out_data)
    written = {n.replace("/", "\\").lower(): b for n, b in written_entries}
    parser_check_live_commandset(written[CS_KEY])
    assert_no_duplicate_large(written_entries)
    if r"data\ini\commandset_zzzz_russia_largeairbase.ini" in written:
        raise SystemExit("parser FAIL: overlay CommandSet packed in final DATA BIG")

    art_entries = read_big(ART_SRC)
    art_added = {}
    for name, path in NEW_ART.items():
        if not path.exists():
            raise SystemExit(f"missing ART {path}")
        upsert_new_only(art_entries, name, path.read_bytes())
        art_added[name] = "added"
    art_bytes = write_big(art_entries)
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_art.write_bytes(art_bytes)
    packed_art = {n.replace("/", "\\").lower(): b for n, b in read_big(out_art)}
    for name, path in NEW_ART.items():
        key = name.replace("/", "\\").lower()
        if key not in packed_art:
            raise SystemExit(f"ART missing from packed BIG: {name}")
        if packed_art[key] != path.read_bytes():
            raise SystemExit(f"ART payload mismatch: {name}")
    print("ART PACK PASS:", ", ".join(sorted(art_added)))

    create_slots = {
        1: ("Command_ConstructRussiaJetSuT75", "RussiaJetSuT75", "RUSU75"),
        10: ("Command_ConstructRussiaJetSu39", "RussiaJetSu39", "RUS_SU39"),
        11: ("Command_ConstructRussiaJetSu47Berkut", "RussiaJetSu47Berkut", "RUSU-47"),
        12: ("Command_ConstructRussiaJetDozor600", "RussiaJetDozor600", "AVReaper"),
        13: ("Command_ConstructRussiaJetSu57Felon", "RussiaJetSu57Felon", "RUS_SU57"),
        14: ("Command_ConstructRussiaJetSuT50PAKFA", "RussiaJetSuT50PAKFA", "LSFT50"),
        15: ("Command_ConstructRussiaJetSu35Flanker", "RussiaJetSu35Flanker", "LSFSU35"),
        16: ("Command_ConstructRussiaJetSu24MR", "RussiaJetSu24MR", "SU24MP"),
    }
    for slot, (btn, obj, model) in create_slots.items():
        verify_construct_create_path(written_entries, packed_art, slot, btn, obj, model)
    if "Command_ConstructRussiaJetSU24MP" in written[CS_KEY].decode("latin1"):
        raise SystemExit("parser FAIL: old SU24MP construct command still in CommandSet.ini")
    for key in CSF_STRINGS:
        if key not in decode_csf_labels(written[CSF_KEY]):
            raise SystemExit(f"parser FAIL: packed CSF missing {key}")
    print("CSF LABEL PASS: all new construct/object strings present")

    zpath = OUT / "RUSSIA_AIRCRAFT_UPDATE.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")

    report = OUT / "PACK_REPORT.txt"
    report.write_text(
        f"DATA SHA256={hashlib.sha256(data_bytes).hexdigest()} SIZE={len(data_bytes)}\n"
        f"ART  SHA256={hashlib.sha256(art_bytes).hexdigest()} SIZE={len(art_bytes)}\n"
        f"ZIP  SHA256={hashlib.sha256(zpath.read_bytes()).hexdigest()} SIZE={zpath.stat().st_size}\n"
        f"CommandSet.ini SHA256={hashlib.sha256(written[CS_KEY]).hexdigest()}\n"
        f"added_data={added}\n"
        f"added_art={art_added}\n"
        f"objects={ {k: objects[k] for k in REQUIRED_OBJECTS} }\n"
        f"slots={EXPECTED_SLOTS}\n"
        f"PARSER CHECK PASS\n",
        encoding="utf-8",
    )
    print(report.read_text())
    print("ZIP", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
