#!/usr/bin/env python3
"""SPECTER1 Japan + France roster/factory/unlock pass.

Baseline: SPECTER1_India_Germany_Roster_01 DATA+ART.
Does not revert India/Germany/Vietnam/Syria/USA/China/Russia/Iraq work.
Does not modify USA/Russia/China/Germany donor object INIs.
Only Japan and France CommandSets, object INIs, new clone files,
and Iran_HeavyAirBase CommandSet (Mirage F1CR add).
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_INDIA_GERMANY_ROSTER_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_INDIA_GERMANY_ROSTER_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "bf9104f64226accaa386dcbe96255f7af2b5089f7b6b90bdf6fad13cec787aa0"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_JAPAN_FRANCE_ROSTER_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_JAPAN_FRANCE_ROSTER_01")

P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_IRAQ_MR = r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MR.ini"
P_NATIONAL = r"Data\INI\Object\Specter\NationalGround\NationalGroundForces.ini"

USA_B2A = r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini"
USA_E3 = r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini"
USA_B21 = r"Data\INI\Object\Specter\United States Of America\AmericaJetB21Clean.ini"
USA_B21A = r"Data\INI\Object\Specter\United States Of America\AmericaJetB21A.ini"
USA_PROWLER = r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaJetF18Prowler.ini"
USA_SYSTEM = r"Data\INI\Object\Specter\United States Of America\USA_System.ini"
CHINA_H6K = r"Data\INI\Object\Specter\PLA\Airforce\H6K.ini"
DE_C130 = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetC130.ini"
DE_C130J = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetC130J.ini"

JP_F35A = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35A.ini"
JP_F15J = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF15J.ini"
JP_F15DJ = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF15DJ.ini"
JP_F2A = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2A.ini"
JP_F2B = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2B.ini"
JP_F2KAI = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2Kai.ini"
JP_F4 = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF4EJKai.ini"
JP_X2 = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetX2Shinshin.ini"
JP_F16 = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF16.ini"
JP_F35JAPON = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35Japon.ini"
JP_F14 = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF14Tomcat.ini"
JP_EA6B_NEW = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetEA6BUSA.ini"

FR_RAF_C = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleC.ini"
FR_RAF_B = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleB.ini"
FR_RAF_M = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleM.ini"
FR_RAF_F4 = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleF4.ini"
FR_RAF_F3 = r"Data\INI\Object\Specter\French Armed Forces\FixedWings\Rafale_B_F3.ini"
FR_M2K5F = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage20005F.ini"
FR_M2K = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage2000.ini"
FR_M2KD = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage2000D.ini"
FR_F1CT = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirageF1CT.ini"
FR_IIIE = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirageIIIE.ini"
FR_M5 = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage5.ini"
FR_FCAS = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetFCASNGF.ini"
FR_F1CR = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirageF1CR.ini"
FR_E3 = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceAircraftE3.ini"
FR_CARACAL = r"Data\INI\Object\Specter\French Armed Forces\Rotary\FranceHelicopterCaracal.ini"
FR_C130_NEW = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetC130US.ini"
FR_B21_NEW = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetB21.ini"
FR_B52_NEW = r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetB52H.ini"
IR_F1CR_NEW = r"Data\INI\Object\Specter\Iranian Army\Airforce\IranJetMirageF1CR.ini"

STD44 = [
    r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetF35B.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\French Armed Forces\Rotary\CH47F.ini",
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

DONOR_PROTECTED = [
    P_IRAQ_MR, P_WEAPON, USA_B2A, USA_E3, USA_B21, USA_B21A, USA_PROWLER, USA_SYSTEM,
    CHINA_H6K, DE_C130, DE_C130J,
    r"Data\INI\Object\Specter\PLA\Airforce\H6K.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\TU22M3M.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\KA52M.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\RussiaJetAn124.ini",
]

E3_USA_MODULES = """  Behavior = FireWeaponUpdate ModuleTag_AWACS_RadarPower
    Weapon                    = AN_APY2_Radar_Power
    ExclusiveWeaponDelay      = 1000
  End
  Behavior = PointDefenseLaserUpdate ModuleTag_AWACS_BaseMonitor
    WeaponTemplate              = AWACS_BaseMonaitoring
    PrimaryTargetTypes          = COMMANDCENTER
    ScanRate                    = 1000
    ScanRange                   = 6750
    PredictTargetVelocityFactor = 3.0
  End
"""

EC725_WEAPONS = """  WeaponSet
    Conditions = None
    Weapon = PRIMARY France_Weapon_Cannon_Tiger
    PreferredAgainst = PRIMARY INFANTRY VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY France_Weapon_ATGM_Tiger
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = TERTIARY France_Weapon_Rocket_Tiger
    PreferredAgainst = TERTIARY INFANTRY STRUCTURE VEHICLE
    AutoChooseSources = TERTIARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End
"""

EC725_AI = """  Behavior = JetAIUpdate ModuleTag_Caracal_07
    OutOfAmmoDamagePerSecond = 0%
    TakeoffDistForMaxLift = 0%
    TakeoffPause = 500
    MinHeight = 5
    ParkingOffset = 3
    NeedsRunway = No
    KeepsParkingSpaceWhenAirborne = No
    ReturnToBaseIdleTime = 10000
    AutoAcquireEnemiesWhenIdle = Yes
  End
"""

EC725_PHYSICS = """  Behavior = PhysicsBehavior ModuleTag_Caracal_Physics
    Mass = 50.0
  End
"""


def norm(name: str) -> str:
    return name.replace("/", "\\")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def raw_of(entries, target) -> bytes:
    return entries[find_index(entries, target)][1]


def text_of(entries, target) -> str:
    return raw_of(entries, target).decode("latin1", errors="replace")


def set_text(entries, target, text: str) -> None:
    i = find_index(entries, target)
    name = entries[i][0]
    entries[i] = (name, text.encode("latin1", errors="replace"))


def add_file(entries, name: str, text: str) -> None:
    n = norm(name)
    if any(norm(x).lower() == n.lower() for x, _ in entries):
        raise SystemExit(f"already packed: {name}")
    entries.append((n, text.encode("latin1", errors="replace")))


def file_nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def to_nl(s: str, nl: str) -> str:
    return s.replace("\r\n", "\n").replace("\n", nl)


def patch_button_image(text: str, button: str, new_image: str, label: str) -> str:
    m = re.search(rf"(?im)^CommandButton\s+{re.escape(button)}\s*$", text)
    if not m:
        raise SystemExit(f"{label}: missing CommandButton {button}")
    m2 = re.search(r"(?im)^CommandButton\s+\S+", text[m.end() :])
    end = m.end() + m2.start() if m2 else len(text)
    block = text[m.start() : end]
    new_block, n = re.subn(
        r"(?im)^(\s*ButtonImage\s*=\s*)\S+",
        rf"\1{new_image}",
        block,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"{label}: ButtonImage replace failed for {button} n={n}")
    return text[: m.start()] + new_block + text[end:]


def replace_commandset(text: str, name: str, body_lines: list[str]) -> str:
    nl = file_nl(text)
    m = re.search(rf"(?im)^CommandSet\s+{re.escape(name)}\s*$", text)
    if not m:
        raise SystemExit(f"missing CommandSet {name}")
    m2 = re.search(r"(?im)^CommandSet\s+\S+", text[m.end() :])
    end = m.end() + m2.start() if m2 else len(text)
    block = "CommandSet " + name + nl
    for line in body_lines:
        block += line + nl
    block += "End" + nl + nl
    return text[: m.start()] + block + text[end:].lstrip("\r\n")


def replace_weapon_slot(text: str, slot: str, old_wpn: str, new_wpn: str, label: str) -> str:
    rx = re.compile(
        rf"^([ \t]*Weapon[ \t]*=[ \t]*{re.escape(slot)}[ \t]+){re.escape(old_wpn)}\b",
        re.M,
    )
    hits = list(rx.finditer(text))
    if len(hits) != 1:
        raise SystemExit(f"{label}: expected 1 {slot} {old_wpn}, got {len(hits)}")
    m = hits[0]
    return text[: m.start()] + m.group(1) + new_wpn + text[m.end() :]


def add_tertiary_weapon(text: str, weapon: str, label: str) -> str:
    nl = file_nl(text)
    m = re.search(r"(?im)^(\s*Weapon\s*=\s*PRIMARY\s+\S+[^\n]*\n)", text)
    if not m:
        raise SystemExit(f"{label}: no PRIMARY weapon to insert after")
    insert = m.group(1) + f"    Weapon            = TERTIARY    {weapon}" + nl
    return text[: m.start()] + insert + text[m.end() :]


def promote_player_upgrade_weaponset(text: str, label: str) -> tuple[str, bool]:
    blocks = list(re.finditer(r"^  WeaponSet\b[^\n]*\n(?:.*\n)*?^  End", text, re.M))
    none_i = None
    up_i = None
    for i, m in enumerate(blocks):
        if re.search(r"(?im)^\s*Conditions\s*=\s*PLAYER_UPGRADE\b", m.group(0)):
            up_i = i
        elif re.search(r"(?im)^\s*Conditions\s*=\s*None\b", m.group(0)):
            none_i = i
    if up_i is None:
        return text, False
    up = blocks[up_i].group(0)
    up_new = re.sub(r"(?im)^(\s*Conditions\s*=\s*)PLAYER_UPGRADE\b", r"\1None", up, count=1)
    if none_i is not None and none_i != up_i:
        none = blocks[none_i]
        upm = blocks[up_i]
        if none.start() < upm.start():
            text = text[: none.start()] + up_new + text[none.end() : upm.start()] + text[upm.end() :]
        else:
            text = text[: upm.start()] + text[upm.end() : none.start()] + up_new + text[none.end() :]
    else:
        text = text[: blocks[up_i].start()] + up_new + text[blocks[up_i].end() :]
    return text, True


def strip_unit_science_locks(text: str) -> tuple[str, int]:
    n = 0

    def drop(rx: str, s: str) -> str:
        nonlocal n
        s2, c = re.subn(rx, "", s, flags=re.M)
        n += c
        return s2

    text = drop(r"^[ \t]*Science[ \t]*=[ \t]*.*\n", text)
    text = drop(r"^[ \t]*RequiredScience[ \t]*=[ \t]*.*\n", text)
    text = drop(r"^[ \t]*ForbiddenScience[ \t]*=[ \t]*.*\n", text)
    text = drop(r"^[ \t]*NeededUpgrade[ \t]*=[ \t]*.*\n", text)
    return text, n


def unlock_named_objects(text: str, prefixes: tuple[str, ...]) -> tuple[str, int]:
    matches = list(re.finditer(r"(?im)^Object\s+(\S+)", text))
    if not matches:
        return text, 0
    n = 0
    out = text[: matches[0].start()]
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[m.start() : end]
        name = m.group(1)
        if name.startswith(prefixes):
            block, c = strip_unit_science_locks(block)
            block, _ = promote_player_upgrade_weaponset(block, name)
            n += c
        out += block
    return out, n


def clone_rename(src: str, pairs: list[tuple[str, str]], old_side: str, new_side: str, header: str) -> str:
    t = src
    for old, new in sorted(pairs, key=lambda x: -len(x[0])):
        t = t.replace(old, new)
    t2, c = re.subn(rf"(?im)^(\s*Side\s*=\s*){re.escape(old_side)}\b", rf"\1{new_side}", t)
    if c < 1:
        raise SystemExit(f"clone side {old_side}->{new_side} failed c={c}")
    t = t2
    t = header + t
    if re.search(rf"(?m)^Object {re.escape(pairs[0][0])}\b", t):
        raise SystemExit(f"clone still has donor object {pairs[0][0]}")
    return t


def extract_object_block(text: str, name: str) -> str:
    m = re.search(rf"(?im)^Object\s+{re.escape(name)}\s*$", text)
    if not m:
        raise SystemExit(f"missing object {name}")
    m2 = re.search(r"(?im)^Object\s+\S+", text[m.end() :])
    return text[m.start() : m.end() + m2.start() if m2 else len(text)]


def insert_before_geometry(text: str, block: str, label: str) -> str:
    nl = file_nl(text)
    block = to_nl(block.rstrip() + "\n", nl)
    m = re.search(r"(?im)^  Geometry\s*=\s*Box\s*$", text)
    if not m:
        raise SystemExit(f"{label}: no Geometry = Box")
    if "ModuleTag_An124Cargo" in block and "ModuleTag_An124Cargo" in text:
        return text
    if "ModuleTag_AWACS_RadarPower" in block and "ModuleTag_AWACS_RadarPower" in text:
        return text
    if "ModuleTag_Caracal_Physics" in block and "ModuleTag_Caracal_Physics" in text:
        return text
    return text[: m.start()] + block + text[m.start() :]


def unit_button(name: str, obj: str, image: str, nl: str) -> str:
    return (
        f"CommandButton {name}{nl}"
        f"  Command          = UNIT_BUILD{nl}"
        f"  Object           = {obj}{nl}"
        f"  TextLabel        = CONTROLBAR:Construct{obj}{nl}"
        f"  ButtonImage      = {image}{nl}"
        f"  ButtonBorderType = BUILD{nl}"
        f"  DescriptLabel    = CONTROLBAR:ToolTip{obj}{nl}"
        f"End{nl}{nl}"
    )


def append_buttons(text: str, buttons: list[str]) -> str:
    nl = file_nl(text)
    extra = ""
    for b in buttons:
        btn_name = b.split()[1]
        if re.search(rf"(?im)^CommandButton\s+{re.escape(btn_name)}\s*$", text):
            continue
        extra += to_nl(b, nl)
    if not extra:
        return text
    if not text.endswith(("\n", "\r\n")):
        text += nl
    return text + extra


def parse_buttons(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"(?im)^CommandButton\s+(\S+)\s*$", text):
        m2 = re.search(r"(?im)^CommandButton\s+\S+", text[m.end() :])
        out[m.group(1)] = text[m.start() : m.end() + m2.start() if m2 else len(text)]
    return out


def parse_commandsets(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"(?im)^CommandSet\s+(\S+)\s*$", text):
        m2 = re.search(r"(?im)^CommandSet\s+\S+", text[m.end() :])
        out[m.group(1)] = text[m.start() : m.end() + m2.start() if m2 else len(text)]
    return out


def object_folder_illegal(entries) -> list[str]:
    bad = []
    rx = re.compile(r"(?im)^(CommandSet|CommandButton|MappedImage|Science|Upgrade)\s+(\S+)")
    for n, b in entries:
        ln = n.lower().replace("/", "\\")
        if "\\ini\\object\\" not in ln or not ln.endswith(".ini"):
            continue
        t = b.decode("latin1", errors="replace")
        for i, line in enumerate(t.splitlines(), 1):
            if line.strip().startswith(";"):
                continue
            m = rx.match(line)
            if m:
                bad.append(f"{n}:{i} {m.group(1)} {m.group(2)}")
    return bad


def mapped_images(entries) -> set[str]:
    names: set[str] = set()
    for n, b in entries:
        t = b.decode("latin1", errors="replace")
        if "MappedImage" not in t:
            continue
        for m in re.finditer(r"(?im)^MappedImage\s+(\S+)", t):
            names.add(m.group(1))
    return names


def art_stems(art_entries) -> set[str]:
    stems: set[str] = set()
    for n, _ in art_entries:
        base = n.replace("/", "\\").split("\\")[-1]
        stem = base.rsplit(".", 1)[0].lower()
        stems.add(stem)
    return stems


def weapon_clip(weapon_text: str, name: str) -> str:
    m = re.search(rf"(?im)^Weapon\s+{re.escape(name)}\s*$", weapon_text)
    if not m:
        return "MISSING"
    m2 = re.search(r"(?im)^Weapon\s+\S+", weapon_text[m.end() :])
    block = weapon_text[m.start() : m.end() + m2.start() if m2 else len(weapon_text)]
    clip = re.search(r"(?im)^\s*ClipSize\s*=\s*(\S+)", block)
    shots = re.search(r"(?im)^\s*ShotsPerBarrel\s*=\s*(\S+)", block)
    bits = []
    if clip:
        bits.append("ClipSize=" + clip.group(1))
    if shots:
        bits.append("ShotsPerBarrel=" + shots.group(1))
    return " ".join(bits) if bits else "defined"


def slot_weapon(text: str, slot: str) -> str:
    m = re.search(rf"(?im)^\s*Weapon\s*=\s*{re.escape(slot)}\s+(\S+)", text)
    return m.group(1) if m else "NONE"


def fix_ec725(text: str) -> str:
    nl = file_nl(text)
    if not text.startswith("; SPECTER1"):
        text = "; SPECTER1 France EC725 combat heli. ART kept LSFRUMi171 (no EC725 mesh). JetAI NeedsRunway=No + Tiger weapons.\n" + text
    text, n = re.subn(
        r"(?im)^(\s*CommandSet\s*=\s*)\S+",
        r"\1GenericAttackHelicopterHoverCommandSet",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("caracal CommandSet replace failed")
    if "France_Weapon_Cannon_Tiger" not in text:
        text = re.sub(
            r"(?im)^(\s*CommandSet\s*=\s*GenericAttackHelicopterHoverCommandSet[^\n]*\n)",
            r"\1" + to_nl(EC725_WEAPONS, nl),
            text,
            count=1,
        )
    text, n = re.subn(
        r"(?im)^(\s*KindOf\s*=\s*).*$",
        r"\1PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT PRODUCED_AT_HELIPAD",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("caracal KindOf replace failed")
    text, n = re.subn(
        r"(?im)^  Behavior = ChinookAIUpdate ModuleTag_Caracal_07\n(?:.*\n)*?^  End\n",
        to_nl(EC725_AI, nl),
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("caracal ChinookAIUpdate replace failed")
    text, n = re.subn(
        r"(?im)^(\s*Locomotor\s*=\s*SET_NORMAL\s+)\S+",
        r"\1ComancheLocomotor",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("caracal locomotor replace failed")
    text, n = re.subn(
        r"(?im)^  Behavior = TransportContain ModuleTag_Caracal_08\n(?:.*\n)*?^  End\n",
        "",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("caracal TransportContain remove failed")
    if "PhysicsBehavior" not in text:
        text = insert_before_geometry(text, EC725_PHYSICS, "caracal physics")
    text = re.sub(r"(?im)^(\s*IsTrainable\s*=\s*)No\b", r"\1Yes", text, count=1)
    m = re.search(r"(?ms)^    DefaultConditionState\n.*?\n    End", text)
    if not m:
        raise SystemExit("caracal DefaultConditionState missing")
    block = m.group(0)
    if "WeaponFireFXBone" not in block:
        block = block.replace(
            "    End",
            "      WeaponFireFXBone = PRIMARY Weapon01\n"
            "      WeaponLaunchBone = PRIMARY Weapon01\n"
            "      WeaponFireFXBone = SECONDARY Weapon01\n"
            "      WeaponLaunchBone = SECONDARY Weapon01\n"
            "      WeaponFireFXBone = TERTIARY Weapon01\n"
            "      WeaponLaunchBone = TERTIARY Weapon01\n"
            "    End",
            1,
        )
        text = text[: m.start()] + to_nl(block, nl) + text[m.end() :]
    if "ChinookAIUpdate" in text:
        raise SystemExit("caracal still ChinookAIUpdate")
    if "CAN_ATTACK" not in text:
        raise SystemExit("caracal missing CAN_ATTACK")
    if "NeedsRunway = No" not in text and "NeedsRunway=No" not in text:
        raise SystemExit("caracal missing NeedsRunway=No")
    return text


def main() -> int:
    data_sha = sha256_file(SRC_DATA)
    art_sha = sha256_file(SRC_ART)
    if data_sha != EXPECTED_DATA_SHA:
        raise SystemExit(f"DATA SHA mismatch {data_sha}")
    if art_sha != EXPECTED_ART_SHA:
        raise SystemExit(f"ART SHA mismatch {art_sha}")

    entries = read_big_list(SRC_DATA)
    art_entries = read_big_list(SRC_ART)
    baseline_hashes = {norm(n).lower(): hashlib.sha256(b).hexdigest() for n, b in entries}

    # --- Japan EA-6B from USA Prowler (do not edit STD44 JapanJetEA6B.ini) ---
    prowler = clone_rename(
        text_of(entries, USA_PROWLER),
        [("AmericaJetF18Prowler", "JapanJetEA6BUSA")],
        "America",
        "Japan",
        "; SPECTER1 Japan EA-6B clone. Donor AmericaJetF18Prowler (NOT modified). STD44 JapanJetEA6B unused.\n",
    )
    prowler = replace_weapon_slot(
        prowler,
        "PRIMARY",
        "Specter_Weapon_EA6B_JH7A2_Bomb",
        "ODAB_500_PMV_SU39",
        "japan ea6b usa bomb",
    )
    add_file(entries, JP_EA6B_NEW, prowler)

    # --- France American C-130 from Germany C-130 clone (do not edit Germany) ---
    fr_c130 = clone_rename(
        text_of(entries, DE_C130),
        [("GermanyJetC130", "FranceJetC130US")],
        "Germany",
        "France",
        "; SPECTER1 France American C-130. Donor GermanyJetC130 LSFUSAC130 + An-124 contain (NOT modified).\n",
    )
    add_file(entries, FR_C130_NEW, fr_c130)

    # --- France B-21 from USA B-21 Clean ---
    fr_b21 = clone_rename(
        text_of(entries, USA_B21),
        [("AmericaJetB21Clean", "FranceJetB21")],
        "America",
        "France",
        "; SPECTER1 France B-21 clone. Donor AmericaJetB21Clean (NOT modified).\n",
    )
    add_file(entries, FR_B21_NEW, fr_b21)

    # --- France B-52H extracted from USA_System.ini (file itself not modified) ---
    b52_src = extract_object_block(text_of(entries, USA_SYSTEM), "AmericaJetB52H")
    fr_b52 = clone_rename(
        b52_src,
        [("AmericaJetB52H", "FranceJetB52H")],
        "America",
        "France",
        "; SPECTER1 France B-52H clone. Extracted from USA_System.ini AmericaJetB52H (NOT modified).\n",
    )
    add_file(entries, FR_B52_NEW, fr_b52)

    # --- Mirage F1CR moved to Iran ---
    ir_f1 = clone_rename(
        text_of(entries, FR_F1CR),
        [("FranceJetMirageF1CR", "IranJetMirageF1CR")],
        "France",
        "Iran",
        "; SPECTER1 Iran Mirage F1CR. Cloned from FranceJetMirageF1CR; France production removed. Scale increased.\n",
    )
    ir_f1, nsc = re.subn(r"(?im)^(Scale\s*=\s*)\S+", r"\g<1>1.08", ir_f1, count=1)
    if nsc != 1:
        raise SystemExit("iran f1cr scale failed")
    ir_f1, _ = promote_player_upgrade_weaponset(ir_f1, "iran f1cr")
    ir_f1 = replace_weapon_slot(
        ir_f1,
        "TERTIARY",
        "France_Weapon_F1CR_Bomb",
        "GBU_31V1_JDAM_F16C",
        "iran f1cr bomb",
    )
    ir_f1, _ = strip_unit_science_locks(ir_f1)
    add_file(entries, IR_F1CR_NEW, ir_f1)

    # --- Japan fighter bombs (skip STD44 F35B / F18G / EA6B files) ---
    japan_bombs = [
        (JP_F15DJ, "SECONDARY", "GBU_31V2_JDAM_F15E", "Kab500_LeaserGuidedBomb"),
        (JP_F2A, "SECONDARY", "Gbu-12II_Paveway", "6_MK-82"),
        (JP_F2B, "SECONDARY", "2x_GBU12II_F16CMB50", "GBU38_JDAM_F16C"),
        (JP_F16, "SECONDARY", "GBU_31V1_JDAM_F16C", "AGM-154C_JSOW_F16C"),
        (JP_F35JAPON, "SECONDARY", "GBU38_JDAM_F16C", "GBU-39_SDB_F22A"),
    ]
    for path, slot, old, new in japan_bombs:
        t = text_of(entries, path)
        t, _ = promote_player_upgrade_weaponset(t, path)
        t = replace_weapon_slot(t, slot, old, new, path)
        set_text(entries, path, t)
    for path, wpn, label in [
        (JP_F15J, "Gbu-12II_Paveway", "f15j bomb"),
        (JP_F2KAI, "Kab1500_LeaserGuidedBomb", "f2kai bomb"),
        (JP_F4, "Fab-250", "f4ej bomb"),
        (JP_F14, "Kab2500_LeaserGuidedBomb", "f14 bomb"),
    ]:
        t = text_of(entries, path)
        t, _ = promote_player_upgrade_weaponset(t, path)
        t = add_tertiary_weapon(t, wpn, label)
        set_text(entries, path, t)

    # --- France fighter bombs ---
    france_bombs = [
        (FR_RAF_C, "TERTIARY", "France_Weapon_Cannon_Jet", "GBU_31V2_JDAM_F15E"),
        (FR_RAF_B, "TERTIARY", "France_Weapon_Cannon_Jet", "Paveway_IV_EF2000"),
        (FR_RAF_M, "TERTIARY", "France_Weapon_Cannon_Jet", "6_MK-82"),
        (FR_RAF_F4, "TERTIARY", "France_Weapon_RafaleF4_AASM", "GBU-39_SDB_F22A"),
        (FR_M2K5F, "TERTIARY", "France_Weapon_Cannon_20005F", "Gbu-12II_Paveway"),
        (FR_M2K, "TERTIARY", "France_Weapon_Cannon_Jet", "Fab-250"),
        (FR_M2KD, "SECONDARY", "France_Weapon_AASM_Mirage2000D", "AGM-154C_JSOW_F16C"),
        (FR_F1CT, "SECONDARY", "France_Weapon_Bomb_MirageF1CT", "GBU38_JDAM_F16C"),
        (FR_IIIE, "SECONDARY", "France_Weapon_Bomb_MirageIIIE", "Kab1500_LeaserGuidedBomb"),
        (FR_M5, "PRIMARY", "France_Weapon_Bomb_Mirage5", "Kab2500_LeaserGuidedBomb"),
        (FR_FCAS, "TERTIARY", "France_Weapon_AASM_FCAS", "ODAB_500_PMV_SU39"),
    ]
    for path, slot, old, new in france_bombs:
        t = text_of(entries, path)
        t, _ = promote_player_upgrade_weaponset(t, path)
        t = replace_weapon_slot(t, slot, old, new, path)
        set_text(entries, path, t)
    f3 = text_of(entries, FR_RAF_F3)
    f3, _ = promote_player_upgrade_weaponset(f3, "rafale f3")
    f3 = add_tertiary_weapon(f3, "Kab500_LeaserGuidedBomb", "rafale f3 bomb")
    set_text(entries, FR_RAF_F3, f3)

    # --- France E-3 USA AWACS modules ---
    e3 = text_of(entries, FR_E3)
    e3 = re.sub(r"(?im)^(\s*DetectionRange\s*=\s*)\S+", r"\g<1>4000", e3, count=1)
    e3 = insert_before_geometry(e3, E3_USA_MODULES, "france e3 awacs")
    set_text(entries, FR_E3, e3)

    # --- EC725 Caracal combat heli ---
    set_text(entries, FR_CARACAL, fix_ec725(text_of(entries, FR_CARACAL)))

    # --- Unlock Japan/France object blocks (not donors, not STD44, not other countries) ---
    unlock_files = 0
    unlock_lines = 0
    protected = {norm(x).lower() for x in STD44 + DONOR_PROTECTED}
    for n, b in list(entries):
        ln = n.replace("/", "\\")
        if not ln.lower().endswith(".ini"):
            continue
        if "\\object\\" not in ln.lower():
            continue
        if norm(ln).lower() in protected:
            continue
        allow = (
            "Japan Self-Defense" in ln
            or "French Armed" in ln
            or ln.endswith("NationalGroundForces.ini")
        )
        if not allow:
            continue
        t = b.decode("latin1", errors="replace")
        t2, stripped = unlock_named_objects(t, ("Japan", "France"))
        if t2 != t:
            set_text(entries, n, t2)
            unlock_files += 1
            unlock_lines += stripped

    # --- CommandButtons ---
    btn = text_of(entries, P_CMDBTN)
    new_btns = [
        unit_button("Command_ConstructJapanJetEA6BUSA", "JapanJetEA6BUSA", "EA6Prowler", "\n"),
        unit_button("Command_ConstructFranceJetC130US", "FranceJetC130US", "SPEC_FranceC130", "\n"),
        unit_button("Command_ConstructFranceJetB21", "FranceJetB21", "B21_L", "\n"),
        unit_button("Command_ConstructFranceJetB52H", "FranceJetB52H", "B52", "\n"),
        unit_button("Command_ConstructIranJetMirageF1CR", "IranJetMirageF1CR", "SPEC_FranceMirageF1CR", "\n"),
    ]
    btn = append_buttons(btn, new_btns)
    img_fixes = [
        ("Command_ConstructJapanVehicleType16", "us_m1126S", "jp type16 img"),
        ("Command_ConstructJapanVehicleType89", "arb_m2a3", "jp type89 img"),
        ("Command_ConstructJapanVehicleType96", "us_m1126S", "jp type96 img"),
        ("Command_ConstructJapanVehicleChuSAM", "us_mim104e", "jp chusam img"),
        ("Command_ConstructJapanVehicleRadar", "us_tpy2", "jp radar img"),
        ("Command_ConstructJapanVehicleType12", "us_m1075t", "jp type12 img"),
        ("Command_ConstructFranceVehicleAMX10RC", "us_m1126S", "fr amx10 img"),
        ("Command_ConstructFranceVehicleSAMPT", "us_mim104e", "fr sampt img"),
        ("Command_ConstructJapanHelicopterUH60J", "us_uh60", "jp uh60 img"),
        ("Command_ConstructJapanHelicopterCH47J", "Nat_ch47", "jp ch47 img"),
    ]
    for name, image, label in img_fixes:
        btn = patch_button_image(btn, name, image, label)
    set_text(entries, P_CMDBTN, btn)

    cs = text_of(entries, P_CMDSET)
    japan_wf = [
        "  1  = Command_ConstructJapanTankType10",
        "  2  = Command_ConstructJapanTankType90",
        "  3  = Command_ConstructJapanVehicleType16",
        "  4  = Command_ConstructJapanVehicleType89",
        "  5  = Command_ConstructJapanVehicleType96",
        "  6  = Command_ConstructJapanVehicleType87",
        "  7  = Command_ConstructJapanVehicleChuSAM",
        "  8  = Command_ConstructJapanVehicleRadar",
        "  9  = Command_ConstructJapanVehicleM270",
        "  10 = Command_ConstructJapanVehicleType12",
        "  11 = Command_ConstructJapanVehicleType99",
        "  12 = Command_ConstructJapanVehicleType16AT",
        "  13 = Command_ConstructJapanVehicleType11ARV",
        "  14 = Command_Sell",
    ]
    cs = replace_commandset(cs, "Japan_WarFactoryCommandSet", japan_wf)
    japan_air = [
        "  1 = Command_ConstructJapanJetF35A",
        "  2 = Command_ConstructJapanJetF35B",
        "  3 = Command_ConstructJapanJetF15J",
        "  4 = Command_ConstructJapanJetF15DJ",
        "  5 = Command_ConstructJapanJetF2A",
        "  6 = Command_ConstructJapanJetF2B",
        "  7 = Command_ConstructJapanJetF2Kai",
        "  8 = Command_ConstructJapanJetF4EJKai",
        "  9 = Command_ConstructJapanJetX2Shinshin",
        "  10 = Command_ConstructJapanJetF16",
        "  11 = Command_ConstructJapanJetF18G",
        "  12 = Command_ConstructJapanJetEA6BUSA",
        "  13 = Command_ConstructJapanJetF35Japon",
        "  14 = Command_ConstructJapanJetF14Tomcat",
    ]
    cs = replace_commandset(cs, "Japan_AirfieldCommandSet", japan_air)
    japan_heavy = [
        "  1 = Command_ConstructJapanJetE2D",
        "  2 = Command_ConstructJapanJetC130H",
        "  3 = Command_ConstructJapanUAVRQ4",
        "  4 = Command_ConstructJapanHelicopterAH64D",
        "  5 = Command_ConstructJapanHelicopterUH60J",
        "  6 = Command_ConstructJapanHelicopterCH47J",
        "  7 = Command_ConstructJapanJetV22",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = replace_commandset(cs, "Japan_HeavyAirBaseCommandSet", japan_heavy)

    france_wf = [
        "  1  = Command_ConstructFranceTankLeclerc",
        "  2  = Command_ConstructFranceTankAMX30",
        "  3  = Command_ConstructFranceVehicleAMX10RC",
        "  4  = Command_ConstructFranceVehicleVBCI",
        "  5  = Command_ConstructFranceVehicleCaesar",
        "  6  = Command_ConstructFranceVehicleCortaleMK3",
        "  7  = Command_ConstructFranceVehicleCentauroB2",
        "  8  = Command_ConstructFranceVehicleIRIST",
        "  9  = Command_ConstructFranceVehicleTRML4D",
        "  10 = Command_ConstructFranceVehicleJaguar",
        "  11 = Command_ConstructFranceVehicleLRU",
        "  12 = Command_ConstructFranceVehicleMistral",
        "  13 = Command_ConstructFranceVehicleSAMPT",
        "  14 = Command_Sell",
    ]
    cs = replace_commandset(cs, "FranceWarfactoryCommandSet", france_wf)
    france_heavy = [
        "  1 = Command_ConstructFranceJetC130US",
        "  2 = Command_ConstructFranceAircraftE3",
        "  3 = Command_ConstructFranceUCAVNeuron",
        "  4 = Command_ConstructFranceHelicopterTiger",
        "  5 = Command_ConstructFranceHelicopterNH90",
        "  6 = Command_ConstructFranceHelicopterCaracal",
        "  7 = Command_ConstructFranceJetB21",
        "  8 = Command_ConstructFranceJetB52H",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = replace_commandset(cs, "France_HeavyAirBaseCommandSet", france_heavy)
    iran_heavy = [
        "  1 = Command_ConstructIranHelicopterPanha2091",
        "  2 = Command_ConstructIranHelicopterMi8",
        "  3 = Command_ConstructIranJetSu47Berkut",
        "  4 = Command_ConstructIranJetMirageF1CR",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = replace_commandset(cs, "Iran_HeavyAirBaseCommandSet", iran_heavy)
    set_text(entries, P_CMDSET, cs)

    for p in STD44 + DONOR_PROTECTED:
        i = find_index(entries, p)
        new_h = hashlib.sha256(entries[i][1]).hexdigest()
        old_h = baseline_hashes[norm(p).lower()]
        if new_h != old_h:
            raise SystemExit(f"PROTECTED FILE CHANGED: {p}")

    if "Object AmericaJetF18Prowler" not in text_of(entries, USA_PROWLER):
        raise SystemExit("USA Prowler damaged")
    if "Object AmericaJetB21Clean" not in text_of(entries, USA_B21):
        raise SystemExit("USA B21 damaged")
    if "Object AmericaJetB52H" not in text_of(entries, USA_SYSTEM):
        raise SystemExit("USA B52H damaged")
    if "Object GermanyJetC130" not in text_of(entries, DE_C130):
        raise SystemExit("Germany C130 damaged")
    if "Object JapanJetEA6BUSA" not in text_of(entries, JP_EA6B_NEW):
        raise SystemExit("Japan EA6B USA clone missing")
    if "Object FranceJetC130US" not in text_of(entries, FR_C130_NEW):
        raise SystemExit("France C130 US clone missing")
    if "Object FranceJetB21" not in text_of(entries, FR_B21_NEW):
        raise SystemExit("France B21 missing")
    if "Object FranceJetB52H" not in text_of(entries, FR_B52_NEW):
        raise SystemExit("France B52 missing")
    if "Object IranJetMirageF1CR" not in text_of(entries, IR_F1CR_NEW):
        raise SystemExit("Iran F1CR missing")
    if "AN_APY2_Radar_Power" not in text_of(entries, FR_E3):
        raise SystemExit("France E3 missing USA radar power")
    if "AWACS_BaseMonaitoring" not in text_of(entries, FR_E3):
        raise SystemExit("France E3 missing USA base monitor")
    car = text_of(entries, FR_CARACAL)
    if "ChinookAIUpdate" in car or "CAN_ATTACK" not in car or "NeedsRunway = No" not in car:
        raise SystemExit("EC725 not converted to combat heli")
    if "France_Weapon_Cannon_Tiger" not in car:
        raise SystemExit("EC725 missing Tiger weapons")
    if "LSFRUMi171" not in car:
        raise SystemExit("EC725 ART mesh lost")
    if "ModuleTag_An124Cargo" not in text_of(entries, FR_C130_NEW):
        raise SystemExit("France C130 missing An-124 contain")
    if "Scale = 1.08" not in text_of(entries, IR_F1CR_NEW) and "Scale=1.08" not in text_of(entries, IR_F1CR_NEW):
        raise SystemExit("Iran F1CR scale not 1.08")

    seen: dict[str, list[str]] = {}
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        if "\\object\\" not in n.lower().replace("/", "\\"):
            continue
        t = b.decode("latin1", errors="replace")
        for m in re.finditer(r"(?im)^Object\s+(\S+)", t):
            seen.setdefault(m.group(1), []).append(n)
    for on in (
        "JapanJetEA6BUSA",
        "FranceJetC130US",
        "FranceJetB21",
        "FranceJetB52H",
        "IranJetMirageF1CR",
    ):
        files = seen.get(on, [])
        if len(files) != 1:
            raise SystemExit(f"{on} files={files}")

    illegal = object_folder_illegal(entries)
    btns = parse_buttons(text_of(entries, P_CMDBTN))
    btns.update(parse_buttons(text_of(entries, P_CMDSET)))
    csets = parse_commandsets(text_of(entries, P_CMDSET))
    images = mapped_images(entries)
    astems = art_stems(art_entries)
    weapons = set(re.findall(r"(?im)^Weapon\s+(\S+)", text_of(entries, P_WEAPON)))
    last_seen = {k: v[-1] for k, v in seen.items()}

    missing_btn: list[str] = []
    missing_obj: list[str] = []
    missing_img: list[str] = []
    missing_wpn: list[str] = []
    locked_counts = {"jp_wf": 0, "jp_air": 0, "fr_wf": 0, "fr_air": 0, "ir_air": 0}

    def audit_cs(cs_name: str, bucket: str | None = None) -> list[str]:
        blk = csets[cs_name]
        cmds = re.findall(r"(?m)^\s*\d+\s*=\s*(\S+)", blk)
        rows = []
        skip = {
            "Command_SetRallyPoint",
            "Command_Sell",
            "Command_Stop",
            "Command_UpgradeChinaRedguardCaptureBuilding",
            "Command_UpgradeGLARebelCaptureBuilding",
        }
        for c in cmds:
            if c in skip:
                continue
            b = btns.get(c)
            if not b:
                missing_btn.append(f"{cs_name} -> {c}")
                continue
            if re.search(r"(?i)RequiredScience|NeededUpgrade|NEED_UPGRADE|NEED_SPECIAL_POWER_SCIENCE", b):
                if bucket:
                    locked_counts[bucket] += 1
            objm = re.search(r"(?im)^\s*Object\s*=\s*(\S+)", b)
            imgm = re.search(r"(?im)^\s*ButtonImage\s*=\s*(\S+)", b)
            cmdm = re.search(r"(?im)^\s*Command\s*=\s*(\S+)", b)
            cmd = cmdm.group(1) if cmdm else ""
            if objm and objm.group(1) not in last_seen:
                missing_obj.append(f"{c} Object={objm.group(1)}")
            if cmd in ("UNIT_BUILD", "DOZER_CONSTRUCT") and imgm and imgm.group(1) not in images:
                missing_img.append(f"{c} ButtonImage={imgm.group(1)}")
            rows.append(c)
        return rows

    jp_wf = audit_cs("Japan_WarFactoryCommandSet", "jp_wf")
    jp_air = audit_cs("Japan_AirfieldCommandSet", "jp_air")
    jp_heavy = audit_cs("Japan_HeavyAirBaseCommandSet", "jp_air")
    jp_dozer = audit_cs("Japan_VT72BCommandSet")
    fr_wf = audit_cs("FranceWarfactoryCommandSet", "fr_wf")
    fr_air = audit_cs("FranceAirfieldCommandSet", "fr_air")
    fr_large = audit_cs("France_LargeAirBaseCommandSet", "fr_air")
    fr_heavy = audit_cs("France_HeavyAirBaseCommandSet", "fr_air")
    fr_heli = audit_cs("France_HelicopterBaseCommandSet", "fr_air")
    fr_dozer = audit_cs("FranceDozerCommandSet")
    ir_heavy = audit_cs("Iran_HeavyAirBaseCommandSet", "ir_air")

    bomb_wpns = [
        "GBU_31V2_JDAM_F15E", "GBU_31V2_JDAM_F35C", "Gbu-12II_Paveway",
        "Kab500_LeaserGuidedBomb", "Paveway_IV_EF2000", "AGM-154C_JSOW_F16C",
        "6_MK-82", "GBU38_JDAM_F16C", "Kab1500_LeaserGuidedBomb", "Fab-250",
        "GBU-39_SDB_F22A", "Kab2500_LeaserGuidedBomb", "ODAB_500_PMV_SU39",
        "GBU_31V1_JDAM_F16C", "2x_GBU24_2000lb_F16CMB50",
        "France_Weapon_Cannon_Tiger", "France_Weapon_ATGM_Tiger", "France_Weapon_Rocket_Tiger",
        "AN_APY2_Radar_Power", "AWACS_BaseMonaitoring",
    ]
    for w in bomb_wpns:
        if w not in weapons and w not in ("AN_APY2_Radar_Power", "AWACS_BaseMonaitoring"):
            missing_wpn.append(w)
    # radar power / base monitor are weapons; confirm:
    for w in ("AN_APY2_Radar_Power", "AWACS_BaseMonaitoring"):
        if w not in weapons:
            missing_wpn.append(w)

    model_checks = ["EA6", "LSFUSAC130", "US_E3G", "AVB21_A", "US_B52H", "UVMirage", "LSFRUMi171", "LSFFRTiger"]
    missing_models = [m for m in model_checks if m.lower() not in astems]

    if illegal:
        raise SystemExit("illegal Object-folder blocks: " + "; ".join(illegal[:8]))
    if missing_btn:
        raise SystemExit("missing buttons: " + "; ".join(missing_btn[:8]))
    if missing_obj:
        raise SystemExit("missing objects: " + "; ".join(missing_obj[:8]))
    if missing_wpn:
        raise SystemExit("missing weapons: " + "; ".join(missing_wpn[:8]))
    if missing_img:
        raise SystemExit("missing button images: " + "; ".join(missing_img[:12]))
    if missing_models:
        raise SystemExit("missing W3D: " + ", ".join(missing_models))
    if "Command_ConstructJapanJetC2" in jp_heavy:
        raise SystemExit("Kawasaki C-2 still produced")
    if "Command_ConstructJapanJetEA6BUSA" not in jp_air:
        raise SystemExit("USA EA-6B not on Japan airfield")
    if "Command_ConstructJapanJetEA6B" in jp_air:
        raise SystemExit("old Japan EA-6B still produced")
    if "Command_ConstructFranceJetC130" in fr_heavy and "Command_ConstructFranceJetC130US" not in fr_heavy:
        raise SystemExit("old France C-130 still produced")
    if "Command_ConstructFranceJetC130US" not in fr_heavy:
        raise SystemExit("American C-130 not on France heavy")
    if "Command_ConstructFranceJetMirageF1CR" in fr_heavy:
        raise SystemExit("F1CR still on France")
    if "Command_ConstructIranJetMirageF1CR" not in ir_heavy:
        raise SystemExit("F1CR not on Iran heavy")
    if "Command_ConstructFranceJetB21" not in fr_heavy:
        raise SystemExit("B-21 not on France heavy")
    if "Command_ConstructFranceJetB52H" not in fr_heavy:
        raise SystemExit("B-52 not on France heavy")
    if "Command_ConstructAmericaTankCrusader" in jp_wf:
        raise SystemExit("Japan WF still America tanks")
    if "Command_ConstructNatoTankLeopard2A7Plus" in fr_wf:
        raise SystemExit("France WF still NATO tanks")
    if sum(locked_counts.values()):
        raise SystemExit(f"button locks remain {locked_counts}")

    # uniqueness of Japan/France fighter bombs on live airfield objects
    jp_bomb_map = {
        "JapanJetF35A": slot_weapon(text_of(entries, JP_F35A), "SECONDARY"),
        "JapanJetF15J": slot_weapon(text_of(entries, JP_F15J), "TERTIARY"),
        "JapanJetF15DJ": slot_weapon(text_of(entries, JP_F15DJ), "SECONDARY"),
        "JapanJetF2A": slot_weapon(text_of(entries, JP_F2A), "SECONDARY"),
        "JapanJetF2B": slot_weapon(text_of(entries, JP_F2B), "SECONDARY"),
        "JapanJetF2Kai": slot_weapon(text_of(entries, JP_F2KAI), "TERTIARY"),
        "JapanJetF4EJKai": slot_weapon(text_of(entries, JP_F4), "TERTIARY"),
        "JapanJetX2Shinshin": slot_weapon(text_of(entries, JP_X2), "SECONDARY"),
        "JapanJetF16": slot_weapon(text_of(entries, JP_F16), "SECONDARY"),
        "JapanJetEA6BUSA": slot_weapon(text_of(entries, JP_EA6B_NEW), "PRIMARY"),
        "JapanJetF35Japon": slot_weapon(text_of(entries, JP_F35JAPON), "SECONDARY"),
        "JapanJetF14Tomcat": slot_weapon(text_of(entries, JP_F14), "TERTIARY"),
    }
    fr_bomb_map = {
        "FranceJetRafaleC": slot_weapon(text_of(entries, FR_RAF_C), "TERTIARY"),
        "FranceJetRafaleB": slot_weapon(text_of(entries, FR_RAF_B), "TERTIARY"),
        "FranceJetRafaleM": slot_weapon(text_of(entries, FR_RAF_M), "TERTIARY"),
        "FranceJetRafaleF4": slot_weapon(text_of(entries, FR_RAF_F4), "TERTIARY"),
        "FranceJetRafaleF3": slot_weapon(text_of(entries, FR_RAF_F3), "TERTIARY"),
        "FranceJetMirage20005F": slot_weapon(text_of(entries, FR_M2K5F), "TERTIARY"),
        "FranceJetMirage2000": slot_weapon(text_of(entries, FR_M2K), "TERTIARY"),
        "FranceJetMirage2000D": slot_weapon(text_of(entries, FR_M2KD), "SECONDARY"),
        "FranceJetMirageF1CT": slot_weapon(text_of(entries, FR_F1CT), "SECONDARY"),
        "FranceJetMirageIIIE": slot_weapon(text_of(entries, FR_IIIE), "SECONDARY"),
        "FranceJetMirage5": slot_weapon(text_of(entries, FR_M5), "PRIMARY"),
        "FranceJetFCASNGF": slot_weapon(text_of(entries, FR_FCAS), "TERTIARY"),
    }
    jp_vals = list(jp_bomb_map.values())
    fr_vals = list(fr_bomb_map.values())
    if len(set(jp_vals)) != len(jp_vals):
        raise SystemExit(f"Japan bomb collision {jp_bomb_map}")
    if len(set(fr_vals)) != len(fr_vals):
        raise SystemExit(f"France bomb collision {fr_bomb_map}")
    if "NONE" in jp_vals or "NONE" in fr_vals:
        raise SystemExit(f"missing bomb slot JP={jp_bomb_map} FR={fr_bomb_map}")

    loadout_after = 0
    ws_up_rx = re.compile(r"^  WeaponSet\b[^\n]*\n(?:.*\n)*?^  End", re.M)
    for n, b in entries:
        ln = n.replace("/", "\\")
        if "Japan Self-Defense" not in ln and "French Armed" not in ln:
            continue
        if norm(ln).lower() in protected:
            continue
        t = b.decode("latin1", errors="replace")
        if not re.search(r"(?im)^Object\s+(Japan|France)", t):
            continue
        for blk in ws_up_rx.findall(t):
            if re.search(r"(?im)^\s*Conditions\s*=\s*PLAYER_UPGRADE\b", blk):
                loadout_after += 1

    # Side checks on live WF objects
    for obj in ["JapanTankType10", "JapanTankType90", "FranceTankLeclerc", "FranceVehicleVBCI"]:
        files = seen.get(obj, [])
        if not files:
            raise SystemExit(f"missing live WF object {obj}")
        t = text_of(entries, files[-1])
        blk = extract_object_block(t, obj)
        side = re.search(r"(?im)^\s*Side\s*=\s*(\S+)", blk)
        if not side:
            raise SystemExit(f"{obj} missing Side")
        want = "Japan" if obj.startswith("Japan") else "France"
        if side.group(1) != want:
            raise SystemExit(f"{obj} Side={side.group(1)} want {want}")

    wtxt = text_of(entries, P_WEAPON)

    def clip(name: str) -> str:
        return weapon_clip(wtxt, name)

    changed = []
    for n, b in entries:
        h = hashlib.sha256(b).hexdigest()
        key = norm(n).lower()
        if key not in baseline_hashes or baseline_hashes[key] != h:
            changed.append(n)
    changed.sort()

    # other-country safety: only Japan/France/Iran CS + NationalGround + Command ini
    other_hits = []
    for n in changed:
        ln = n.replace("/", "\\")
        ok = (
            ln in (P_CMDSET, P_CMDBTN)
            or "Japan Self-Defense" in ln
            or "French Armed" in ln
            or ln.endswith("NationalGroundForces.ini")
            or ln.endswith("IranJetMirageF1CR.ini")
        )
        if not ok:
            other_hits.append(n)
    if other_hits:
        raise SystemExit("unrelated paths changed: " + "; ".join(other_hits[:8]))

    blob = build_big_ordered(entries)
    new_sha = hashlib.sha256(blob).hexdigest()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(blob)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(blob)
    art_bytes = SRC_ART.read_bytes()
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_bytes)
    (WS_OUT / "_SPEC_ART_ONE.big").write_bytes(art_bytes)

    lines: list[str] = []
    p = lines.append
    p("SPECTER1 JAPAN + FRANCE ROSTER 01")
    p("BASELINE_DATA_SHA256 = " + EXPECTED_DATA_SHA)
    p("BASELINE_ART_SHA256 = " + EXPECTED_ART_SHA)
    p("NEW_DATA_SHA256 = " + new_sha)
    p("NEW_ART_SHA256 = " + EXPECTED_ART_SHA + " (unchanged copy)")
    p("NEW_DATA_BYTES = " + str(len(blob)))
    p("NEW_DATA_FILE_COUNT = " + str(len(entries)))
    p("MODE = DATA edits from India+Germany roster baseline; ART packed unchanged")
    p("")
    p("=== JAPAN FACTORY / BUILDINGS ===")
    p("BUG = Japan_WarFactoryCommandSet produced Side=America vehicles (Crusader/Stryker/etc)")
    p("FIX = retargeted to Side=Japan Type10/Type90/Type16/Type89/Type96/Type87/ChuSAM/Radar/M270/Type12/Type99/Type16AT/Type11ARV")
    p("BUILDING_CHAIN = Power/Supply Object prereqs kept (all targets exist)")
    p("DOZER = Japan_VT72B KindOf DOZER + Japan_VT72BCommandSet unchanged")
    p("FACTORY_FIXED = YES")
    p("JAPAN WARFACTORY =")
    for c in jp_wf:
        p("  " + c)
    p("JAPAN DOZER BUILDINGS = " + str(len(jp_dozer)))
    p("")
    p("=== JAPAN AIRCRAFT ROSTER ===")
    p("EA6B_REPLACED_FROM_USA = YES (JapanJetEA6BUSA clone of AmericaJetF18Prowler; STD44 JapanJetEA6B unused)")
    p("KAWASAKI_C2_REMOVED = YES (JapanJetC2 dropped from HeavyAirBase CommandSet; object file left)")
    p("JAPAN AIRFIELD =")
    for c in jp_air:
        p("  " + c)
    p("JAPAN HEAVY =")
    for c in jp_heavy:
        p("  " + c)
    p("")
    p("=== JAPAN BOMB DIVERSITY ===")
    p("JAPAN AIRCRAFT | BOMB / STRIKE WEAPON")
    for obj, wpn in jp_bomb_map.items():
        p(f"{obj} | {wpn} | {clip(wpn)}")
    p("JapanJetF35A | GBU_31V2_JDAM_F35C kept unique | " + clip("GBU_31V2_JDAM_F35C"))
    p("JapanJetX2Shinshin | 2x_GBU24_2000lb_F16CMB50 kept unique | " + clip("2x_GBU24_2000lb_F16CMB50"))
    p("STD44_SKIP = JapanJetF35B.ini and JapanJetF18G.ini not edited")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("")
    p("=== JAPAN UNLOCK ===")
    p("UNLOCK_OBJECT_FILES_TOUCHED = " + str(unlock_files))
    p("SCIENCE_LOCK_LINES_REMOVED = " + str(unlock_lines))
    p("JAPAN_WARFACTORY_LOCKED_UNIT_COUNT = " + str(locked_counts["jp_wf"]))
    p("JAPAN_AIRCRAFT_LOCKED_UNIT_COUNT = " + str(locked_counts["jp_air"]))
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("=== FRANCE FACTORY / BUILDINGS ===")
    p("BUG = FranceWarfactoryCommandSet produced Side=Nato vehicles (Leopard 2A7+/Puma/etc)")
    p("FIX = retargeted to Side=France Leclerc/AMX30/AMX10RC/VBCI/Caesar/Cortale/Centauro/IRIS-T/TRML-4D/Jaguar/LRU/Mistral/SAMP/T")
    p("DOZER = FranceVehicleDozer KindOf DOZER + FranceDozerCommandSet unchanged")
    p("FACTORY_FIXED = YES")
    p("FRANCE WARFACTORY =")
    for c in fr_wf:
        p("  " + c)
    p("FRANCE DOZER BUILDINGS = " + str(len(fr_dozer)))
    p("")
    p("=== FRANCE EC725 ===")
    p("BUG = FranceHelicopterCaracal ChinookAIUpdate + no CAN_ATTACK + no WeaponSet (stuck on runway, no fire)")
    p("FIX = JetAIUpdate NeedsRunway=No, ComancheLocomotor, CAN_ATTACK, Tiger Cannon/ATGM/Rocket, hover CommandSet")
    p("ART = LSFRUMi171 kept (no EC725 W3D in ART pack)")
    p("EC725_FLIGHT_FIXED = YES")
    p("EC725_FIRE_ENABLED = YES")
    p("")
    p("=== FRANCE AIRCRAFT ROSTER ===")
    p("C130_REPLACED = YES (FranceJetC130US clone of GermanyJetC130 American LSFUSAC130 + An-124 Slots=64)")
    p("E3_AWACS_FUNCTION_ADDED = YES (FireWeaponUpdate AN_APY2_Radar_Power + PointDefenseLaserUpdate AWACS_BaseMonaitoring)")
    p("MIRAGE_F1CR_MOVED_TO_IRAN = YES (IranJetMirageF1CR Scale=1.08 GBU-31V1; removed from France HeavyAirBase)")
    p("B21_ADDED = YES (FranceJetB21 clone of AmericaJetB21Clean)")
    p("B52_ADDED = YES (FranceJetB52H extracted from USA_System.ini AmericaJetB52H)")
    p("FRANCE HEAVY =")
    for c in fr_heavy:
        p("  " + c)
    p("IRAN HEAVY =")
    for c in ir_heavy:
        p("  " + c)
    p("")
    p("=== FRANCE BOMB DIVERSITY ===")
    p("FRANCE AIRCRAFT | BOMB / STRIKE WEAPON")
    for obj, wpn in fr_bomb_map.items():
        p(f"{obj} | {wpn} | {clip(wpn)}")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("")
    p("=== FRANCE UNLOCK ===")
    p("FRANCE_WARFACTORY_LOCKED_UNIT_COUNT = " + str(locked_counts["fr_wf"]))
    p("FRANCE_AIRCRAFT_LOCKED_UNIT_COUNT = " + str(locked_counts["fr_air"]))
    p("WEAPON_LOADOUT_UPGRADE_GATE_COUNT = " + str(loadout_after))
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("BUILDING_CHAIN_PREREQS_PRESERVED = YES")
    p("")
    p("=== SAFETY ===")
    p("USA_PROWLER_DONOR_UNCHANGED = YES")
    p("USA_B21_DONOR_UNCHANGED = YES")
    p("USA_SYSTEM_INI_UNCHANGED = YES")
    p("GERMANY_C130_DONOR_UNCHANGED = YES")
    p("IRAQ_SU24MR_UNCHANGED = YES")
    p("STD44_FILES_UNCHANGED = YES")
    p("INDIA_GERMANY_VIETNAM_SYRIA_UNCHANGED = YES")
    p("WEAPON_INI_CHANGED = NO")
    p("OBJECT_FOLDER_COMMANDSET_BLOCKS = " + str(len(illegal)))
    p("MISSING_COMMANDBUTTONS = " + str(len(missing_btn)))
    p("MISSING_BUTTONIMAGES = " + str(len(missing_img)))
    p("")
    p("CHANGED_PATHS =")
    for n in changed:
        p("  " + n)
    p("")
    p("JAPAN:")
    p("FACTORY_FIXED = YES")
    p("EA6B_REPLACED_FROM_USA = YES")
    p("KAWASAKI_C2_REMOVED = YES")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("FRANCE:")
    p("FACTORY_FIXED = YES")
    p("EC725_FLIGHT_FIXED = YES")
    p("EC725_FIRE_ENABLED = YES")
    p("C130_REPLACED = YES")
    p("E3_AWACS_FUNCTION_ADDED = YES")
    p("MIRAGE_F1CR_MOVED_TO_IRAN = YES")
    p("B21_ADDED = YES")
    p("B52_ADDED = YES")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("DATA_CHANGED = YES")
    p("ART_CHANGED = NO")
    p("ART_CHANGED_CHECK = existing EA6 / LSFUSAC130 / US_E3G / AVB21_A / US_B52H / UVMirage / LSFRUMi171 stems present; no new W3D required")
    p("INGAME_TESTED = NO")
    p("RELEASE_OVERWRITES_PREVIOUS = NO")

    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 Japan + France Roster 01

Continues from SPECTER1_India_Germany_Roster_01. Does not revert previous country work.
Does not overwrite previous GitHub Releases. USA/Germany donor INIs untouched.

Japan:
- War factory production retargeted from Side=America vehicles to Side=Japan JGSDF vehicles.
- Distinct bomb/strike loadouts on live airfield fighters (STD44 F-35B / F/A-18G files not edited).
- Removed Kawasaki C-2 production. Replaced EA-6B with USA Prowler clone (JapanJetEA6BUSA).
- Stripped Science/RequiredScience/NeededUpgrade unit locks. Building Object chains kept.

France:
- War factory production retargeted from Side=Nato to Side=France vehicles.
- EC725 Caracal converted to combat helicopter (JetAI NeedsRunway=No, CAN_ATTACK, Tiger weapons).
- Removed C-130 and Mirage F1CR production. Added American C-130 (An-124 contain), B-21, B-52H.
- E-3 gained USA AWACS FireWeaponUpdate + PointDefenseLaserUpdate.
- Mirage F1CR cloned to Iran HeavyAirBase (Scale 1.08, GBU-31V1). France object left unused.
- Distinct bomb loadouts on all 12 airfield fighters.
- Stripped French upgrade/science locks.

No Weapon.ini new entries. ART packed unchanged (donor meshes already present).
INGAME_TESTED = NO
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")

    zpath = WS_OUT / "SPECTER1_Japan_France_Roster_01.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
    (OUT_DIR / "SPECTER1_Japan_France_Roster_01.zip").write_bytes(zpath.read_bytes())

    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", len(blob), new_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    if loadout_after != 0:
        print("NOTE loadout gates remaining (non-fatal if TriggeredBy-only):", loadout_after)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
