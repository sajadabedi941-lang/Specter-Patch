#!/usr/bin/env python3
"""PR #385 baseline + isolated Russia airbase menu wiring.

Stock CommandButton.ini / Weapon.ini / Russia_System.ini / CSF / existing
aircraft objects stay untouched. Menu slot wiring only.

CommandSet.ini is the one live file that is surgically updated.
No overlay CommandSet file. Each live set stays unique (not duplicated).

Fighter Air Base (Russia_LargeAirBase -> Russia_LargeAirBaseCommandSet):
  Slots 1-12 keep the current working fighter-runway aircraft.
  Slot 13 is Su-57 Felon. Slot 14 is Su-T50 PAK FA.
  Su-35 Flanker / Su-33 / Su-27 are not on this menu.

Large/Heavy Air Base (Russia_HeavyAirBase -> Russia_HeavyAirBaseCommandSet):
  Slot 3 (empty) is Su-35 Flanker.
  Slot 13 (Rally) is Su-33. Slot 14 (Sell) is Su-27.
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
HEAVY_NAME = "Russia_HeavyAirBaseCommandSet"

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
    "  16 = Command_ConstructRussiaJetSu24MR\n"
    "End"
)

# Source Heavy block after the global SU24MP -> Su24MR rewrite.
OLD_HEAVY = (
    "CommandSet Russia_HeavyAirBaseCommandSet\n"
    "  1  = Command_ConstructRussiaJetSu34\n"
    "  2  = Command_ConstructRussiaJetSU24M2\n"
    "  4  = Command_ConstructRussiaJetSu24MR\n"
    "  5  = Command_ConstructRussiaJetTu22M3M\n"
    "  6 = Command_ConstructRussiaJetTu95\n"
    "  7 = Command_ConstructRussiaJetTU160\n"
    "  8 = Command_ConstructRussiaJetAn225\n"
    "  9 = Command_ConstructRussiaJetA50\n"
    "  10 = Command_ConstructRussiaJetAn124\n"
    "  11 = Command_ConstructRussiaJetAvionIL76\n"
    "  12 = Command_ConstructRussiaJetCargoIL76\n"
    "  13 = Command_SetRallyPoint\n"
    "  14 = Command_Sell\n"
    "End"
)
NEW_HEAVY = (
    "CommandSet Russia_HeavyAirBaseCommandSet\n"
    "  1  = Command_ConstructRussiaJetSu34\n"
    "  2  = Command_ConstructRussiaJetSU24M2\n"
    "  3  = Command_ConstructRussiaJetSu35Flanker\n"
    "  4  = Command_ConstructRussiaJetSu24MR\n"
    "  5  = Command_ConstructRussiaJetTu22M3M\n"
    "  6 = Command_ConstructRussiaJetTu95\n"
    "  7 = Command_ConstructRussiaJetTU160\n"
    "  8 = Command_ConstructRussiaJetAn225\n"
    "  9 = Command_ConstructRussiaJetA50\n"
    "  10 = Command_ConstructRussiaJetAn124\n"
    "  11 = Command_ConstructRussiaJetAvionIL76\n"
    "  12 = Command_ConstructRussiaJetCargoIL76\n"
    "  13 = Command_ConstructRussiaJetSu33\n"
    "  14 = Command_ConstructRussiaJetSu27Flanker\n"
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
    16: "Command_ConstructRussiaJetSu24MR",
}

EXPECTED_HEAVY_SLOTS = {
    1: "Command_ConstructRussiaJetSu34",
    2: "Command_ConstructRussiaJetSU24M2",
    3: "Command_ConstructRussiaJetSu35Flanker",
    4: "Command_ConstructRussiaJetSu24MR",
    5: "Command_ConstructRussiaJetTu22M3M",
    6: "Command_ConstructRussiaJetTu95",
    7: "Command_ConstructRussiaJetTU160",
    8: "Command_ConstructRussiaJetAn225",
    9: "Command_ConstructRussiaJetA50",
    10: "Command_ConstructRussiaJetAn124",
    11: "Command_ConstructRussiaJetAvionIL76",
    12: "Command_ConstructRussiaJetCargoIL76",
    13: "Command_ConstructRussiaJetSu33",
    14: "Command_ConstructRussiaJetSu27Flanker",
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
FIGHTER_FORBIDDEN_BUTTONS = (
    "Command_ConstructRussiaJetSu33",
    "Command_ConstructRussiaJetSu27Flanker",
    "Command_ConstructRussiaJetSu35Flanker",
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
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su33.ini": AIRFORCE / "Su33.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su27Flanker.ini": AIRFORCE
    / "Su27Flanker.ini",
    r"Data\INI\MappedImages\HandCreated\Russia_Dozor600_Images.INI": PATCH
    / "Data/INI/MappedImages/HandCreated/Russia_Dozor600_Images.INI",
    r"Data\INI\MappedImages\HandCreated\Russia_Su33_Su27_Images.INI": PATCH
    / "Data/INI/MappedImages/HandCreated/Russia_Su33_Su27_Images.INI",
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
    r"Art\W3D\AGMZRT501.W3D": PATCH / "Art/W3D/AGMZRT501.W3D",
    r"Art\W3D\qsnt50.W3D": PATCH / "Art/W3D/qsnt50.W3D",
    r"Art\Textures\AGMZT50NEW.tga": PATCH / "Art/Textures/AGMZT50NEW.tga",
    r"Art\Textures\t50t.tga": PATCH / "Art/Textures/t50t.tga",
    r"Art\Textures\mig29_minipit.tga": PATCH / "Art/Textures/mig29_minipit.tga",
    r"Art\Textures\ZHCA_AIRapPilot.tga": PATCH / "Art/Textures/ZHCA_AIRapPilot.tga",
    r"Art\Textures\f35.tga": PATCH / "Art/Textures/f35.tga",
    r"Art\Textures\f35.dds": PATCH / "Art/Textures/f35.dds",
    r"Art\W3D\RUSU33.W3D": PATCH / "Art/W3D/RUSU33.W3D",
    r"Art\W3D\RUSU33d.W3D": PATCH / "Art/W3D/RUSU33d.W3D",
    r"Art\Textures\RUSU33.dds": PATCH / "Art/Textures/RUSU33.dds",
    r"Art\Textures\RUSU33.tga": PATCH / "Art/Textures/RUSU33.tga",
    r"Art\Textures\RUSU33d.dds": PATCH / "Art/Textures/RUSU33d.dds",
    r"Art\Textures\RUSU33d.tga": PATCH / "Art/Textures/RUSU33d.tga",
    r"Art\Textures\SU33TB.tga": PATCH / "Art/Textures/SU33TB.tga",
    r"Art\W3D\LSFRUSU27SK.W3D": PATCH / "Art/W3D/LSFRUSU27SK.W3D",
    r"Art\W3D\LSFRUSU27SKd.W3D": PATCH / "Art/W3D/LSFRUSU27SKd.W3D",
    r"Art\W3D\LSFRUSU27SKk.W3D": PATCH / "Art/W3D/LSFRUSU27SKk.W3D",
    r"Art\Textures\RUSU27SK.dds": PATCH / "Art/Textures/RUSU27SK.dds",
    r"Art\Textures\RUSU27SKd.dds": PATCH / "Art/Textures/RUSU27SKd.dds",
    r"Art\Textures\RUSU327SKk.dds": PATCH / "Art/Textures/RUSU327SKk.dds",
    r"Art\Textures\LSFCNMissle.dds": PATCH / "Art/Textures/LSFCNMissle.dds",
    r"Art\Textures\VietnamSU30.dds": PATCH / "Art/Textures/VietnamSU30.dds",
    r"Art\Textures\SU27SKTB.tga": PATCH / "Art/Textures/SU27SKTB.tga",
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
    "RussiaJetSu57Felon": "qsnt50",
    "RussiaJetSuT75": "RUSU75",
    "RussiaJetSuT50PAKFA": "AGMZRT501",
    "RussiaJetSu35Flanker": "LSFSU35",
    "RussiaJetSu24MR": "SU24MP",
    "RussiaJetSu33": "RUSU33",
    "RussiaJetSu27Flanker": "LSFRUSU27SK",
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


def parse_commandset_block(text: str, name: str, max_slot: int = 18) -> dict:
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
    if patched.count("CommandSet Russia_HeavyAirBaseCommandSet") != 1:
        raise SystemExit("parser FAIL: patched file Heavy set is not unique")
    if OLD_HEAVY not in patched:
        raise SystemExit("parser FAIL: rewritten Russia_HeavyAirBaseCommandSet block not found")
    if patched.count(OLD_HEAVY) != 1:
        raise SystemExit("parser FAIL: Heavy block matched more than once")
    patched = patched.replace(OLD_HEAVY, NEW_HEAVY, 1)
    if patched.count("CommandSet Russia_HeavyAirBaseCommandSet") != 1:
        raise SystemExit("parser FAIL: Heavy replace created a duplicate set")
    if patched.count("CommandSet Russia_LargeAirBaseCommandSet") != 1:
        raise SystemExit("parser FAIL: Heavy replace disturbed unique Large set")
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
    if text.count("CommandSet Russia_HeavyAirBaseCommandSet") != 1:
        raise SystemExit("parser FAIL: duplicated Russia_HeavyAirBaseCommandSet in CommandSet.ini")
    parser_check_commandset_balance(text)
    parsed = parse_commandset_block(text, LARGE_NAME, max_slot=18)
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
    if parsed["slots"].get(13) != "Command_ConstructRussiaJetSu57Felon":
        raise SystemExit("parser FAIL: fighter slot 13 is not Su-57 Felon")
    if parsed["slots"].get(14) != "Command_ConstructRussiaJetSuT50PAKFA":
        raise SystemExit("parser FAIL: fighter slot 14 is not Su-T50 PAK FA")
    for banned in FIGHTER_FORBIDDEN_BUTTONS:
        if banned in parsed["slots"].values():
            raise SystemExit(f"parser FAIL: {banned} is on Fighter Air Base")
    if parsed["slots"].get(13) == "Command_SetRallyPoint":
        raise SystemExit("parser FAIL: Rally is still in Large slot 13")
    if parsed["slots"].get(14) == "Command_Sell":
        raise SystemExit("parser FAIL: Sell is still in Large slot 14")
    heavy = parse_commandset_block(text, HEAVY_NAME, max_slot=14)
    if heavy["block"] != NEW_HEAVY:
        raise SystemExit("parser FAIL: live Russia_HeavyAirBaseCommandSet body mismatch")
    if heavy["slots"] != EXPECTED_HEAVY_SLOTS:
        raise SystemExit(f"parser FAIL: live Heavy slots {heavy['slots']}")
    if heavy["slots"].get(3) != "Command_ConstructRussiaJetSu35Flanker":
        raise SystemExit("parser FAIL: Heavy empty slot 3 is not Su-35 Flanker")
    if heavy["slots"].get(13) != "Command_ConstructRussiaJetSu33":
        raise SystemExit("parser FAIL: Heavy Rally slot 13 is not Su-33")
    if heavy["slots"].get(14) != "Command_ConstructRussiaJetSu27Flanker":
        raise SystemExit("parser FAIL: Heavy Sell slot 14 is not Su-27")
    if "Command_SetRallyPoint" in heavy["slots"].values():
        raise SystemExit("parser FAIL: Rally is still on Russia_HeavyAirBaseCommandSet")
    if "Command_Sell" in heavy["slots"].values():
        raise SystemExit("parser FAIL: Sell is still on Russia_HeavyAirBaseCommandSet")
    if "Command_ConstructRussiaJetSu57Felon" in heavy["slots"].values():
        raise SystemExit("parser FAIL: Su-57 Felon leaked onto Large/Heavy Air Base")
    if "Command_ConstructRussiaJetSuT50PAKFA" in heavy["slots"].values():
        raise SystemExit("parser FAIL: Su-T50 PAK FA leaked onto Large/Heavy Air Base")
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
    print("PARSER CHECK PASS: fighter Felon/T50 restored; Su-35/Su-33/Su-27 only on Heavy")


def assert_no_duplicate_commandsets(entries: list[tuple[str, bytes]]) -> None:
    large_hits = []
    heavy_hits = []
    for n, b in entries:
        if b"CommandSet Russia_LargeAirBaseCommandSet" in b:
            large_hits.append(n)
        if b"CommandSet Russia_HeavyAirBaseCommandSet" in b:
            heavy_hits.append(n)
        key = n.replace("/", "\\").lower()
        if "commandset_zzzz" in key or key.endswith(r"commandset_zzzz_russia_largeairbase.ini"):
            raise SystemExit(f"parser FAIL: overlay CommandSet file still packed: {n}")
    cs_name = next(n for n, _ in entries if n.replace("/", "\\").lower() == CS_KEY)
    if large_hits != [cs_name]:
        raise SystemExit(f"parser FAIL: Russia_LargeAirBaseCommandSet files={large_hits}")
    if heavy_hits != [cs_name]:
        raise SystemExit(f"parser FAIL: Russia_HeavyAirBaseCommandSet files={heavy_hits}")
    print("PARSER CHECK PASS: no duplicate Large/Heavy CommandSet, no overlay file")


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
    set_name: str = LARGE_NAME,
    max_slot: int = 18,
) -> None:
    data = {n.replace("/", "\\").lower(): b for n, b in data_entries}
    cs = parse_commandset_block(data[CS_KEY].decode("latin1"), set_name, max_slot=max_slot)
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
    weapons = re.findall(
        r"^\s+Weapon\s+=\s+(?:PRIMARY|SECONDARY|TERTIARY)\s+(\S+)\s*$",
        obj_text,
        re.M,
    )
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
    print(f"CREATE PATH PASS: {set_name} slot {slot} {btn} -> {obj} model {model}")


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
        ("RussiaJetSu57Felon", "qsnt50", "Su57Felon.ini"),
        ("RussiaJetSuT75", "RUSU75", "SuT75.ini"),
        ("RussiaJetSuT50PAKFA", "AGMZRT501", "SuT50PAKFA.ini"),
        ("RussiaJetSu35Flanker", "LSFSU35", "Su35Flanker.ini"),
        ("RussiaJetSu24MR", "SU24MP", "Su24MR.ini"),
        ("RussiaJetSu33", "RUSU33", "Su33.ini"),
        ("RussiaJetSu27Flanker", "LSFRUSU27SK", "Su27Flanker.ini"),
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

    assert_no_duplicate_commandsets(data_entries)
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

    parsed_large = parse_commandset_block(new_map[CS_KEY].decode("latin1"), LARGE_NAME, max_slot=18)
    for removed in REMOVED_MENU_BUTTONS + FIGHTER_FORBIDDEN_BUTTONS:
        if removed in parsed_large["slots"].values():
            raise SystemExit(f"parser FAIL: removed menu button still slotted on fighter: {removed}")
    parsed_heavy = parse_commandset_block(new_map[CS_KEY].decode("latin1"), HEAVY_NAME, max_slot=14)
    for removed in ("Command_SetRallyPoint", "Command_Sell"):
        if removed in parsed_heavy["slots"].values():
            raise SystemExit(f"parser FAIL: {removed} still slotted on Heavy")
    for banned in FIGHTER_FORBIDDEN_BUTTONS:
        if banned not in parsed_heavy["slots"].values():
            raise SystemExit(f"parser FAIL: {banned} missing from Large/Heavy Air Base")

    mapped = new_map[r"data\ini\mappedimages\handcreated\russia_dozor600_images.ini".lower()].decode("latin1")
    if "MappedImage Dozor600" not in mapped:
        raise SystemExit("parser FAIL: Dozor600 MappedImage missing")
    flanker_map = new_map[r"data\ini\mappedimages\handcreated\russia_su33_su27_images.ini".lower()].decode("latin1")
    if "MappedImage SU33TB" not in flanker_map or "MappedImage SU27SKTB" not in flanker_map:
        raise SystemExit("parser FAIL: Su-33/Su-27 MappedImages missing")

    data_bytes = write_big(data_entries)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(data_bytes)

    written_entries = read_big(out_data)
    written = {n.replace("/", "\\").lower(): b for n, b in written_entries}
    parser_check_live_commandset(written[CS_KEY])
    assert_no_duplicate_commandsets(written_entries)
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
        13: ("Command_ConstructRussiaJetSu57Felon", "RussiaJetSu57Felon", "qsnt50"),
        14: ("Command_ConstructRussiaJetSuT50PAKFA", "RussiaJetSuT50PAKFA", "AGMZRT501"),
        16: ("Command_ConstructRussiaJetSu24MR", "RussiaJetSu24MR", "SU24MP"),
    }
    for slot, (btn, obj, model) in create_slots.items():
        verify_construct_create_path(written_entries, packed_art, slot, btn, obj, model)
    for slot, btn, obj, model in (
        (3, "Command_ConstructRussiaJetSu35Flanker", "RussiaJetSu35Flanker", "LSFSU35"),
        (13, "Command_ConstructRussiaJetSu33", "RussiaJetSu33", "RUSU33"),
        (14, "Command_ConstructRussiaJetSu27Flanker", "RussiaJetSu27Flanker", "LSFRUSU27SK"),
    ):
        verify_construct_create_path(
            written_entries,
            packed_art,
            slot,
            btn,
            obj,
            model,
            set_name=HEAVY_NAME,
            max_slot=14,
        )
    fighter_slots = parse_commandset_block(written[CS_KEY].decode("latin1"), LARGE_NAME, max_slot=18)["slots"]
    heavy_slots = parse_commandset_block(written[CS_KEY].decode("latin1"), HEAVY_NAME, max_slot=14)["slots"]
    if fighter_slots.get(13) != "Command_ConstructRussiaJetSu57Felon":
        raise SystemExit("MENU FAIL: fighter menu slot 13 is not Su-57 Felon")
    if fighter_slots.get(14) != "Command_ConstructRussiaJetSuT50PAKFA":
        raise SystemExit("MENU FAIL: fighter menu slot 14 is not Su-T50 PAK FA")
    if set(FIGHTER_FORBIDDEN_BUTTONS) & set(fighter_slots.values()):
        raise SystemExit("MENU FAIL: Su-35/Su-33/Su-27 still on Fighter Air Base")
    if set(FIGHTER_FORBIDDEN_BUTTONS) - set(heavy_slots.values()):
        raise SystemExit("MENU FAIL: Su-35/Su-33/Su-27 missing from Large/Heavy Air Base")
    if "Command_ConstructRussiaJetSu57Felon" in heavy_slots.values():
        raise SystemExit("MENU FAIL: Su-57 Felon leaked onto Large/Heavy Air Base")
    if "Command_ConstructRussiaJetSuT50PAKFA" in heavy_slots.values():
        raise SystemExit("MENU FAIL: Su-T50 PAK FA leaked onto Large/Heavy Air Base")
    print("FIGHTER MENU PASS: unique Russia_LargeAirBaseCommandSet has Felon/T50, not Su-35/Su-33/Su-27")
    print("HEAVY MENU PASS: unique Russia_HeavyAirBaseCommandSet has Su-35/Su-33/Su-27 only")
    t75_text = (AIRFORCE / "SuT75.ini").read_text(encoding="latin1")
    if re.search(r"^\s+Weapon\s+=\s+\S*(R77|R73)", t75_text, re.M):
        raise SystemExit("parser FAIL: SuT75 still has air-to-air missiles")
    t75_bombs = re.findall(
        r"^\s+Weapon\s+=\s+(?:PRIMARY|SECONDARY|TERTIARY)\s+(\S+)\s*$",
        t75_text,
        re.M,
    )
    if t75_bombs != ["3x_1000LB_LT3_PGM_J10C", "3x_1000LB_LT3_PGM_J10C"]:
        raise SystemExit(f"parser FAIL: SuT75 bombs {t75_bombs}")
    print("T75 STRIKE LOADOUT PASS: 6 J-10 guided bombs, no R-77/R-73")
    felon_text = (AIRFORCE / "Su57Felon.ini").read_text(encoding="latin1")
    t50_text = (AIRFORCE / "SuT50PAKFA.ini").read_text(encoding="latin1")
    if "6x_R77_MRBVR_SU35S" not in felon_text or "6x_MRAAM_K77M_SU57" not in felon_text:
        raise SystemExit("parser FAIL: Felon weapons changed")
    if "6x_R77_MRBVR_SU35S" not in t50_text or "Kab500_LeaserGuidedBomb" not in t50_text:
        raise SystemExit("parser FAIL: T50 weapons changed")
    if not re.search(r"Model\s+=\s+qsnt50\s*$", felon_text, re.M):
        raise SystemExit("parser FAIL: Felon is not using qsnt50")
    if not re.search(r"Model\s+=\s+AGMZRT501\s*$", t50_text, re.M):
        raise SystemExit("parser FAIL: T50 is not using AGMZRT501")
    if re.search(r"Model\s+=\s+LSFT50", t50_text, re.M):
        raise SystemExit("parser FAIL: T50 still references F-22 LSFT50 mesh")
    print("FELON/T50 ART SWAP PASS: qsnt50 / AGMZRT501, weapons unchanged")
    if "Command_ConstructRussiaJetSU24MP" in written[CS_KEY].decode("latin1"):
        raise SystemExit("parser FAIL: old SU24MP construct command still in CommandSet.ini")
    for key in CSF_STRINGS:
        if key not in decode_csf_labels(written[CSF_KEY]):
            raise SystemExit(f"parser FAIL: packed CSF missing {key}")
    print("CSF LABEL PASS: all new construct/object strings present")

    zpath = OUT / "RUSSIA_AIRBASE_SEPARATION.zip"
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
        f"large_slots={EXPECTED_SLOTS}\n"
        f"heavy_slots={EXPECTED_HEAVY_SLOTS}\n"
        f"{NEW_LARGE}\n"
        f"{NEW_HEAVY}\n"
        f"PARSER CHECK PASS\n",
        encoding="utf-8",
    )
    print(report.read_text())
    print("ZIP", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
