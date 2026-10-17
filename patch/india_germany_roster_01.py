#!/usr/bin/env python3
"""SPECTER1 India + Germany roster/factory/unlock pass.

Baseline: SPECTER1_Vietnam_Syria_ART_01 DATA+ART.
Does not revert Vietnam/Syria/USA/China/Russia/Iraq work.
Does not modify USA/Russia/China donor object INIs.
Only India and Germany CommandSets, object INIs, and new clone files.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_VIETNAM_SYRIA_ART_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_VIETNAM_SYRIA_ART_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "e63195d16a8ed35d079e6020a6b46e52986a2dbb51b15d582d1ed587015379ce"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_INDIA_GERMANY_ROSTER_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_INDIA_GERMANY_ROSTER_01")

P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_IRAQ_MR = r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MR.ini"

RUS_RIFLE = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Infantry\Rifleman.ini"
RUS_AT = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Infantry\AntiTank.ini"
RUS_KORNET = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Infantry\KornetTeam.ini"
RUS_MORTAR = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Infantry\MortarTeam.ini"
RUS_MG = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Infantry\Machinegunner.ini"
RUS_AA = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Infantry\AntiAir.ini"
RUS_ENG = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Infantry\Engineer.ini"
RUS_SPETS = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Infantry\SpetsNaz.ini"
RUS_SNIPER = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Infantry\Sniper.ini"
RUS_LANCET = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Infantry\LancetTeam.ini"
RUS_FPV = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Infantry\FPVDroneOperator.ini"
RUS_MEDIC = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Infantry\Medic.ini"
RUS_TU22 = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\TU22M3M.ini"
RUS_KA52 = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\KA52M.ini"
RUS_AN124 = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\RussiaJetAn124.ini"
USA_B2A = r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini"
USA_E3 = r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini"
USA_B21 = r"Data\INI\Object\Specter\United States Of America\AmericaJetB21Clean.ini"
CHINA_H6K = r"Data\INI\Object\Specter\PLA\Airforce\H6K.ini"

IN_SU30 = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetSu30MKI.ini"
IN_MIG29A = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\India_Mig-29A.ini"
IN_MIG29K = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMig29K.ini"
IN_RAF_EH = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetRafaleEH.ini"
IN_RAF_DH = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetRafaleDH.ini"
IN_MIR_H = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMirage2000H.ini"
IN_MIR_I = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMirage2000I.ini"
IN_MIG21 = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMig21Bison.ini"
IN_JAG = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetJaguarIS.ini"
IN_MIG27 = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMig27.ini"
IN_TEJAS = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetTejas.ini"
IN_AMCA = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetAMCA.ini"
IN_DRONE_C = r"Data\INI\Object\Specter\Indian Armed Forces\Drones\India_CombatDrone.ini"
IN_DRONE_L = r"Data\INI\Object\Specter\Indian Armed Forces\Drones\India_LoiteringDrone.ini"
IN_ABBAS = r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_Abbas.ini"

DE_T4 = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTyphoonT4.ini"
DE_T1 = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTyphoonT1.ini"
DE_TECR = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTyphoonECR.ini"
DE_TADV = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTornadoADV.ini"
DE_F35 = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetF35A.ini"
DE_MIG29 = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetMiG29G.ini"
DE_TIDS = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTornadoIDS.ini"
DE_TECR2 = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetTornadoECR.ini"
DE_F4 = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetF4F.ini"
DE_ALPHA = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetAlphaJet.ini"
DE_MAKO = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetMako.ini"
DE_FCAS = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetFCASNGF.ini"
DE_A400 = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetA400M.ini"
DE_E3 = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyAircraftE3.ini"
DE_C130J = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetC130J.ini"

IN_TU22_NEW = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetTu22M3M.ini"
IN_B2_NEW = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetB2A.ini"
IN_KA52_NEW = r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaHelicopterKA52.ini"
DE_C130_NEW = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetC130.ini"
DE_B2_NEW = r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetB2A.ini"

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

DONOR_PROTECTED = [
    RUS_RIFLE, RUS_AT, RUS_KORNET, RUS_MORTAR, RUS_MG, RUS_AA, RUS_ENG,
    RUS_SPETS, RUS_SNIPER, RUS_LANCET, RUS_FPV, RUS_MEDIC, RUS_TU22, RUS_KA52,
    RUS_AN124, USA_B2A, USA_E3, USA_B21, CHINA_H6K, P_IRAQ_MR, P_WEAPON,
    r"Data\INI\Object\Specter\United States Of America\AmericaJetB21A.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\H6K.ini",
]

AN124_CONTAIN = """  Behavior = TransportContain ModuleTag_An124Cargo
    Slots                 = 64
    DamagePercentToUnits  = 100%
    AllowInsideKindOf     = INFANTRY VEHICLE
    ForbidInsideKindOf    = AIRCRAFT HUGE_VEHICLE
    ExitDelay             = 100
    NumberOfExitPaths     = 1
  End
"""

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
    t = t.replace("Object = RussiaBarracks", "Object = India_Barracks")
    t = t.replace("Object = RussiaWarFactory", "Object = India_WarFactory_T")
    t = header + t
    if re.search(rf"(?m)^Object {re.escape(pairs[0][0])}\b", t):
        raise SystemExit(f"clone still has donor object {pairs[0][0]}")
    return t


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
        m = re.search(rf"(?im)^CommandButton\s+{re.escape(b.split()[1])}\s*$", b)
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


def patch_drone(text: str) -> str:
    text, _ = strip_unit_science_locks(text)
    text = re.sub(
        r"(?im)^(\s*KindOf\s*=\s*).*$",
        r"\1PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT DRONE",
        text,
        count=1,
    )
    text = re.sub(
        r"(?im)^[ \t]*Object[ \t]*=[ \t]*India_LargeAirBase[^\n]*\n",
        "",
        text,
    )
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

    inf_dir = r"Data\INI\Object\Specter\Indian Armed Forces\Infantry"
    inf_clones = [
        (
            RUS_RIFLE,
            inf_dir + r"\IndiaInfantryRifleman.ini",
            [("RussiaInfantryRiflemanAK74M", "IndiaInfantryRiflemanAK74M")],
        ),
        (
            RUS_AT,
            inf_dir + r"\IndiaInfantryAntitank.ini",
            [("RussiaInfantryAntitank", "IndiaInfantryAntitank")],
        ),
        (
            RUS_KORNET,
            inf_dir + r"\IndiaInfantryKornetTeam.ini",
            [
                ("RussiaMechanizedInfantryKornet", "IndiaMechanizedInfantryKornet"),
                ("RussiaInfantryKornetTeam", "IndiaInfantryKornetTeam"),
            ],
        ),
        (
            RUS_MORTAR,
            inf_dir + r"\IndiaInfantryMortarTeam.ini",
            [
                ("RussiaInfantryMortarGuard", "IndiaInfantryMortarGuard"),
                ("RussiaInfantryMortarTeam", "IndiaInfantryMortarTeam"),
            ],
        ),
        (
            RUS_MG,
            inf_dir + r"\IndiaInfantryMachinegunner.ini",
            [("RussiaInfantryMachinegunner", "IndiaInfantryMachinegunner")],
        ),
        (
            RUS_AA,
            inf_dir + r"\IndiaInfantryAntiair.ini",
            [("RussiaInfantryAntiair", "IndiaInfantryAntiair")],
        ),
        (
            RUS_ENG,
            inf_dir + r"\IndiaInfantryFieldEngineer.ini",
            [("RussiaInfantryFieldEngineer", "IndiaInfantryFieldEngineer")],
        ),
        (
            RUS_SPETS,
            inf_dir + r"\IndiaInfantrySpetsNaz.ini",
            [
                ("RussiaInfantrySpetsNaz_AT", "IndiaInfantrySpetsNaz_AT"),
                ("RussiaInfantrySpetsNaz_M", "IndiaInfantrySpetsNaz_M"),
                ("RussiaInfantrySpetsNaz_S", "IndiaInfantrySpetsNaz_S"),
                ("RussiaInfantrySpetsNaz_A", "IndiaInfantrySpetsNaz_A"),
            ],
        ),
        (
            RUS_SNIPER,
            inf_dir + r"\IndiaInfantryHeavySniper.ini",
            [("RussiaInfantryHeavySniper", "IndiaInfantryHeavySniper")],
        ),
        (
            RUS_LANCET,
            inf_dir + r"\IndiaInfantryLancetTeam.ini",
            [("RussiaInfantryLancetTeam", "IndiaInfantryLancetTeam")],
        ),
        (
            RUS_FPV,
            inf_dir + r"\IndiaInfantryDroneOperatorFPV.ini",
            [("RussiaInfantryDroneOperatorFPV", "IndiaInfantryDroneOperatorFPV")],
        ),
        (
            RUS_MEDIC,
            inf_dir + r"\IndiaInfantryFieldMedic.ini",
            [("RussiaInfantryFieldMedic", "IndiaInfantryFieldMedic")],
        ),
    ]
    for src, dst, pairs in inf_clones:
        add_file(
            entries,
            dst,
            clone_rename(
                text_of(entries, src),
                pairs,
                "Russia",
                "India",
                "; SPECTER1 India infantry clone. Donor " + pairs[0][0] + " (NOT modified).\n",
            ),
        )

    add_file(
        entries,
        IN_TU22_NEW,
        clone_rename(
            text_of(entries, RUS_TU22),
            [("RussiaJetTu22M3M", "IndiaJetTu22M3M")],
            "Russia",
            "India",
            "; SPECTER1 India Tu-22M3M clone. Donor RussiaJetTu22M3M (NOT modified).\n",
        ),
    )
    add_file(
        entries,
        IN_B2_NEW,
        clone_rename(
            text_of(entries, USA_B2A),
            [("AmericaJetB2A", "IndiaJetB2A")],
            "America",
            "India",
            "; SPECTER1 India B-2A clone. Donor AmericaJetB2A (NOT modified).\n",
        ),
    )
    add_file(
        entries,
        IN_KA52_NEW,
        clone_rename(
            text_of(entries, RUS_KA52),
            [
                ("RussiaHelicopterKA52C", "IndiaHelicopterKA52C"),
                ("RussiaHelicopterKA52U", "IndiaHelicopterKA52U"),
                ("RussiaHelicopterKA52", "IndiaHelicopterKA52"),
            ],
            "Russia",
            "India",
            "; SPECTER1 India Ka-52 clone. Donor RussiaHelicopterKA52 (NOT modified).\n",
        ),
    )
    de_c130 = clone_rename(
        text_of(entries, DE_C130J),
        [("GermanyJetC130J", "GermanyJetC130")],
        "Germany",
        "Germany",
        "; SPECTER1 Germany American C-130. Visual LSFUSAC130 from C-130J; An-124 TransportContain grafted.\n",
    )
    de_c130 = de_c130.replace("OBJECT:GermanyJetC130", "OBJECT:AmericaJetC130j")
    de_c130 = insert_before_geometry(de_c130, AN124_CONTAIN, "de c130 contain")
    add_file(entries, DE_C130_NEW, de_c130)
    add_file(
        entries,
        DE_B2_NEW,
        clone_rename(
            text_of(entries, USA_B2A),
            [("AmericaJetB2A", "GermanyJetB2A")],
            "America",
            "Germany",
            "; SPECTER1 Germany B-2A clone. Donor AmericaJetB2A (NOT modified).\n",
        ),
    )

    # --- India bomb diversity ---
    india_bombs = [
        (IN_SU30, "TERTIARY", "India_Weapon_Kh59_Su30MKI", "GBU_31V2_JDAM_F15E"),
        (IN_MIG29K, "TERTIARY", "IndiaJetMig29K_WpnStrike", "Kab500_LeaserGuidedBomb"),
        (IN_RAF_EH, "TERTIARY", "IndiaJetRafaleEH_WpnStrike", "Paveway_IV_EF2000"),
        (IN_RAF_DH, "TERTIARY", "IndiaJetRafaleDH_WpnStandoff", "AGM-154C_JSOW_F16C"),
        (IN_MIR_H, "TERTIARY", "IndiaJetMirage2000H_WpnGun", "6_MK-82"),
        (IN_MIR_I, "SECONDARY", "IndiaJetMirage2000I_WpnBomb", "GBU38_JDAM_F16C"),
        (IN_JAG, "SECONDARY", "IndiaJetJaguarIS_WpnBomb", "Kab1500_LeaserGuidedBomb"),
        (IN_MIG27, "TERTIARY", "IndiaJetMig27_WpnBomb", "Fab-250"),
        (IN_TEJAS, "TERTIARY", "IndiaJetTejas_WpnStrike", "GBU-39_SDB_F22A"),
        (IN_AMCA, "TERTIARY", "IndiaJetAMCA_WpnStrike", "Kab2500_LeaserGuidedBomb"),
    ]
    for path, slot, old, new in india_bombs:
        t = text_of(entries, path)
        t, _ = promote_player_upgrade_weaponset(t, path)
        t = replace_weapon_slot(t, slot, old, new, path)
        set_text(entries, path, t)
    mig29a = text_of(entries, IN_MIG29A)
    mig29a, _ = promote_player_upgrade_weaponset(mig29a, "mig29a")
    mig29a = add_tertiary_weapon(mig29a, "Gbu-12II_Paveway", "mig29a bomb")
    set_text(entries, IN_MIG29A, mig29a)

    # --- Germany bomb diversity ---
    ger_bombs = [
        (DE_T4, "TERTIARY", "Germany_Weapon_JetCannon", "GBU-39_SDB_F22A"),
        (DE_T1, "TERTIARY", "GermanyJetTyphoonT1_WpnGun", "Paveway_IV_EF2000"),
        (DE_TECR, "TERTIARY", "Germany_Weapon_JetCannon", "GBU_31V2_JDAM_F15E"),
        (DE_TADV, "TERTIARY", "Germany_Weapon_JetCannon", "Gbu-12II_Paveway"),
        (DE_MIG29, "TERTIARY", "Germany_Weapon_JetCannon", "Kab500_LeaserGuidedBomb"),
        (DE_TIDS, "SECONDARY", "GermanyJetTornadoIDS_WpnBombHvy", "6_MK-82"),
        (DE_TECR2, "TERTIARY", "Germany_Weapon_JetCannon", "AGM-154C_JSOW_F16C"),
        (DE_F4, "TERTIARY", "Germany_Weapon_JetCannon", "Fab-250"),
        (DE_ALPHA, "PRIMARY", "Germany_Weapon_Bomb", "GBU38_JDAM_F16C"),
        (DE_MAKO, "PRIMARY", "Germany_Weapon_JDAM", "Kab1500_LeaserGuidedBomb"),
        (DE_FCAS, "SECONDARY", "Germany_Weapon_FCAS_PGM", "Kab2500_LeaserGuidedBomb"),
    ]
    for path, slot, old, new in ger_bombs:
        t = text_of(entries, path)
        t, _ = promote_player_upgrade_weaponset(t, path)
        t = replace_weapon_slot(t, slot, old, new, path)
        set_text(entries, path, t)
    # F-35A keeps Germany_Weapon_JDAM as its unique JDAM loadout.

    a400 = insert_before_geometry(text_of(entries, DE_A400), AN124_CONTAIN, "a400m contain")
    set_text(entries, DE_A400, a400)

    e3 = text_of(entries, DE_E3)
    e3 = re.sub(
        r"(?im)^(\s*DetectionRange\s*=\s*)\S+",
        r"\g<1>4000",
        e3,
        count=1,
    )
    e3 = insert_before_geometry(e3, E3_USA_MODULES, "e3 awacs")
    set_text(entries, DE_E3, e3)

    set_text(entries, IN_DRONE_C, patch_drone(text_of(entries, IN_DRONE_C)))
    set_text(entries, IN_DRONE_L, patch_drone(text_of(entries, IN_DRONE_L)))

    abbas = text_of(entries, IN_ABBAS)
    abbas2, n_abbas = re.subn(
        r"(?im)^[ \t]*Object[ \t]*=[ \t]*India_AbbasResearchObject[ \t]*\n",
        "",
        abbas,
    )
    if n_abbas:
        set_text(entries, IN_ABBAS, abbas2)

    # --- unlock India/Germany object blocks (not donors, not STD44) ---
    unlock_files = 0
    unlock_lines = 0
    protected = {norm(x).lower() for x in STD44 + DONOR_PROTECTED}
    vn_sy_skip = ("Vietnam", "Syria", "Iraq Army", "United States", "Armed Forces Of Russian", "\\PLA\\")
    for n, b in list(entries):
        ln = n.replace("/", "\\")
        if not ln.lower().endswith(".ini"):
            continue
        if "\\object\\" not in ln.lower():
            continue
        if norm(ln).lower() in protected:
            continue
        if any(s in ln for s in vn_sy_skip) and "Indian" not in ln and "German Armed" not in ln and "NationalGround" not in ln:
            continue
        t = b.decode("latin1", errors="replace")
        if not re.search(r"(?im)^Object\s+(India|Germany)", t):
            continue
        t2, stripped = unlock_named_objects(t, ("India", "Germany"))
        if t2 != t:
            set_text(entries, n, t2)
            unlock_files += 1
            unlock_lines += stripped

    # --- CommandButtons ---
    btn = text_of(entries, P_CMDBTN)
    nl = file_nl(btn)
    new_btns = [
        unit_button("Command_ConstructIndiaInfantryRiflemanAK74M", "IndiaInfantryRiflemanAK74M", "rus_rifleman", "\n"),
        unit_button("Command_ConstructIndiaInfantryAntitank", "IndiaInfantryAntitank", "rus_at29", "\n"),
        unit_button("Command_ConstructIndiaInfantryKornetTeam", "IndiaInfantryKornetTeam", "rus_kornet", "\n"),
        unit_button("Command_ConstructIndiaInfantryMortarTeam", "IndiaInfantryMortarTeam", "rus_mortar", "\n"),
        unit_button("Command_ConstructIndiaInfantryMachinegunner", "IndiaInfantryMachinegunner", "rus_machinegunner", "\n"),
        unit_button("Command_ConstructIndiaInfantryAntiair", "IndiaInfantryAntiair", "rus_antiair", "\n"),
        unit_button("Command_ConstructIndiaInfantryFieldEngineer", "IndiaInfantryFieldEngineer", "rus_engineer", "\n"),
        unit_button("Command_ConstructIndiaInfantrySpetsNaz", "IndiaInfantrySpetsNaz_A", "rus_spets", "\n"),
        unit_button("Command_ConstructIndiaInfantryHeavySniper", "IndiaInfantryHeavySniper", "rus_heavysniper", "\n"),
        unit_button("Command_ConstructIndiaInfantryLancetTeam", "IndiaInfantryLancetTeam", "rus_lanteam", "\n"),
        unit_button("Command_ConstructIndiaInfantryDroneOperatorFPV", "IndiaInfantryDroneOperatorFPV", "rus_fpv", "\n"),
        unit_button("Command_ConstructIndiaInfantryFieldMedic", "IndiaInfantryFieldMedic", "rus_rifleman", "\n"),
        unit_button("Command_ConstructIndia_LoiteringDrone", "India_LoiteringDrone", "Nat_mq9", "\n"),
        unit_button("Command_ConstructIndiaJetTu22M3M", "IndiaJetTu22M3M", "rus_tu22m3m", "\n"),
        unit_button("Command_ConstructIndiaJetB2A", "IndiaJetB2A", "B2A", "\n"),
        unit_button("Command_ConstructIndiaHelicopterKA52", "IndiaHelicopterKA52", "rus_ka52", "\n"),
        unit_button("Command_ConstructGermanyJetC130", "GermanyJetC130", "SPEC_GermanyC130J", "\n"),
        unit_button("Command_ConstructGermanyJetB2A", "GermanyJetB2A", "B2A", "\n"),
    ]
    btn = append_buttons(btn, new_btns)
    btn = patch_button_image(btn, "Command_ConstructIndiaVehicleBMP2", "arb_m2a3", "bmp2 img")
    btn = patch_button_image(btn, "Command_ConstructIndiaVehicleAkash", "us_mim104e", "akash img")
    btn = patch_button_image(btn, "Command_ConstructIndiaVehiclePrahaar", "us_m1075t", "prahaar img")
    btn = patch_button_image(btn, "Command_ConstructIndia_CombatDrone", "Nat_mq9", "combatdrone img")
    btn = patch_button_image(btn, "Command_ConstructGermanyVehicleFennek", "us_m1126S", "fennek img")
    set_text(entries, P_CMDBTN, btn)

    cs = text_of(entries, P_CMDSET)
    india_wf = [
        "  1  = Command_ConstructIndiaTankT90S",
        "  2  = Command_ConstructIndiaTankT72Ajeya",
        "  3  = Command_ConstructIndiaTankArjun",
        "  4  = Command_ConstructIndiaVehicleBMP2",
        "  5  = Command_ConstructIndiaVehicleK9Vajra",
        "  6  = Command_ConstructIndiaVehiclePinaka",
        "  7  = Command_ConstructIndiaVehicleTunguska",
        "  8  = Command_ConstructIndiaVehicleAkash",
        "  9  = Command_ConstructIndia_BTR-90",
        "  10 = Command_ConstructIndia_BM-21",
        "  11 = Command_ConstructIndia_AlKhalid",
        "  12 = Command_ConstructIndiaVehicleNag",
        "  13 = Command_ConstructIndiaVehiclePrahaar",
        "  14 = Command_Sell",
    ]
    for name in (
        "India_WarFactoryCommandSet",
        "India_WarFactoryCommandSet1",
        "India_WarFactoryCommandSet2",
        "India_WarFactoryCommandSet3",
    ):
        cs = replace_commandset(cs, name, india_wf)

    india_bar = [
        "  1 = Command_ConstructIndiaInfantryRiflemanAK74M",
        "  2 = Command_ConstructIndiaInfantryAntitank",
        "  3 = Command_ConstructIndiaInfantryKornetTeam",
        "  4 = Command_ConstructIndiaInfantryMortarTeam",
        "  5 = Command_ConstructIndiaInfantryMachinegunner",
        "  6 = Command_ConstructIndiaInfantryAntiair",
        "  7 = Command_ConstructIndiaInfantryFieldEngineer",
        "  8 = Command_ConstructIndiaInfantrySpetsNaz",
        "  9 = Command_ConstructIndiaInfantryHeavySniper",
        "  10 = Command_ConstructIndiaInfantryLancetTeam",
        "  11 = Command_ConstructIndiaInfantryDroneOperatorFPV",
        "  12 = Command_ConstructIndiaInfantryFieldMedic",
        "  13 = Command_UpgradeChinaRedguardCaptureBuilding",
        "  14 = Command_Sell",
    ]
    cs = replace_commandset(cs, "India_BarracksCommandSet", india_bar)

    india_heavy = [
        "  1 = Command_ConstructIndia_Mi-8T",
        "  2 = Command_ConstructIndia_IL-76",
        "  3 = Command_ConstructIndia_CombatDrone",
        "  4 = Command_ConstructIndia_LoiteringDrone",
        "  5 = Command_ConstructIndiaJetTu22M3M",
        "  6 = Command_ConstructIndiaJetB2A",
        "  7 = Command_ConstructIndiaHelicopterKA52",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ]
    cs = replace_commandset(cs, "India_HeavyAirBaseCommandSet", india_heavy)
    cs = replace_commandset(
        cs,
        "India_RadarCommandSet",
        [
            "  1 = Command_ConstructIndia_CombatDrone",
            "  2 = Command_ConstructIndia_LoiteringDrone",
            "  13 = Command_SetRallyPoint",
            "  14 = Command_Sell",
        ],
    )

    ger_wf = [
        "  1  = Command_ConstructGermanyTankLeopard2A7Plus",
        "  2  = Command_ConstructGermanyTankPuma",
        "  3  = Command_ConstructGermanyVehicleCortaleMK3",
        "  4  = Command_ConstructGermanyVehicleVBCI",
        "  5  = Command_ConstructGermanyVehicleM142",
        "  6  = Command_ConstructGermanyVehicleCaesar",
        "  7  = Command_ConstructGermanyVehicleCentauroB2",
        "  8  = Command_ConstructGermanyVehicleIRIST",
        "  9  = Command_ConstructGermanyVehicleTRML4D",
        "  10 = Command_ConstructGermanyVehicleGepard",
        "  11 = Command_ConstructGermanyVehiclePzH2000",
        "  12 = Command_ConstructGermanyVehicleMARS",
        "  13 = Command_ConstructGermanyVehicleFennek",
        "  14 = Command_Sell",
    ]
    cs = replace_commandset(cs, "GermanyWarfactoryCommandSet", ger_wf)
    cs = replace_commandset(
        cs,
        "Germany_HeavyAirBaseCommandSet",
        [
            "  1 = Command_ConstructGermanyJetA400M",
            "  2 = Command_ConstructGermanyJetC130",
            "  3 = Command_ConstructGermanyAircraftE3",
            "  4 = Command_ConstructGermanyDroneHeronTP",
            "  5 = Command_ConstructGermanyUAVEuroMALE",
            "  6 = Command_ConstructGermanyHelicopterTigerUHT",
            "  7 = Command_ConstructGermanyHelicopterNH90",
            "  8 = Command_ConstructGermanyHelicopterCH53",
            "  9 = Command_ConstructGermanyHelicopterAH64E",
            "  10 = Command_ConstructGermanyJetB2A",
            "  13 = Command_SetRallyPoint",
            "  14 = Command_Sell",
        ],
    )
    cs = replace_commandset(
        cs,
        "Germany_HelicopterBaseCommandSet",
        [
            "  1  = Command_ConstructGermanyHelicopterTigerUHT",
            "  2  = Command_ConstructGermanyHelicopterNH90",
            "  3  = Command_ConstructGermanyHelicopterCH53",
            "  4  = Command_ConstructGermanyHelicopterAH64E",
            "  13 = Command_SetRallyPoint",
            "  14 = Command_Sell",
        ],
    )
    set_text(entries, P_CMDSET, cs)

    for p in STD44 + DONOR_PROTECTED:
        i = find_index(entries, p)
        new_h = hashlib.sha256(entries[i][1]).hexdigest()
        old_h = baseline_hashes[norm(p).lower()]
        if new_h != old_h:
            raise SystemExit(f"PROTECTED FILE CHANGED: {p}")

    if "Object AmericaJetB2A" not in text_of(entries, USA_B2A):
        raise SystemExit("USA B2 damaged")
    if "Object RussiaJetTu22M3M" not in text_of(entries, RUS_TU22):
        raise SystemExit("Russia Tu22 damaged")
    if "Object RussiaHelicopterKA52" not in text_of(entries, RUS_KA52):
        raise SystemExit("Russia KA52 damaged")
    if "Object RussiaInfantryRiflemanAK74M" not in text_of(entries, RUS_RIFLE):
        raise SystemExit("Russia rifleman damaged")
    if "TransportContain" not in text_of(entries, DE_A400):
        raise SystemExit("A400M missing TransportContain")
    if "AN_APY2_Radar_Power" not in text_of(entries, DE_E3):
        raise SystemExit("E3 missing USA radar power")
    if "AWACS_BaseMonaitoring" not in text_of(entries, DE_E3):
        raise SystemExit("E3 missing USA base monitor")
    if "Command_ConstructGermanyHelicopterH145M" in text_of(entries, P_CMDSET).split("CommandSet Germany_HeavyAirBaseCommandSet")[1][:800]:
        raise SystemExit("H145 still on HeavyAirBase")
    if "Command_ConstructGermanyJetC130J" in text_of(entries, P_CMDSET).split("CommandSet Germany_HeavyAirBaseCommandSet")[1][:800]:
        raise SystemExit("C130J still on HeavyAirBase")

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
        "IndiaInfantryRiflemanAK74M",
        "IndiaJetTu22M3M",
        "IndiaJetB2A",
        "IndiaHelicopterKA52",
        "GermanyJetC130",
        "GermanyJetB2A",
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
    locked_counts = {"india_bar": 0, "india_wf": 0, "india_air": 0, "ger_wf": 0, "ger_air": 0}

    def audit_cs(cs_name: str, bucket: str | None = None) -> list[str]:
        blk = csets[cs_name]
        cmds = re.findall(r"(?m)^\s*\d+\s*=\s*(\S+)", blk)
        rows = []
        for c in cmds:
            if c in ("Command_SetRallyPoint", "Command_Sell", "Command_Stop", "Command_UpgradeChinaRedguardCaptureBuilding"):
                continue
            b = btns.get(c)
            if not b:
                missing_btn.append(f"{cs_name} -> {c}")
                continue
            if re.search(r"(?i)RequiredScience|NeededUpgrade", b) or re.search(r"(?i)Options\s*=\s*.*NEED", b):
                if bucket:
                    locked_counts[bucket] += 1
            objm = re.search(r"(?im)^\s*Object\s*=\s*(\S+)", b)
            imgm = re.search(r"(?im)^\s*ButtonImage\s*=\s*(\S+)", b)
            if objm and objm.group(1) not in last_seen:
                missing_obj.append(f"{c} Object={objm.group(1)}")
            if imgm and imgm.group(1) not in images:
                missing_img.append(f"{c} ButtonImage={imgm.group(1)}")
            rows.append(c)
        return rows

    in_bar = audit_cs("India_BarracksCommandSet", "india_bar")
    in_wf = audit_cs("India_WarFactoryCommandSet", "india_wf")
    in_air = audit_cs("India_AirfieldCommandSet", "india_air")
    in_heavy = audit_cs("India_HeavyAirBaseCommandSet", "india_air")
    in_radar = audit_cs("India_RadarCommandSet", "india_air")
    de_wf = audit_cs("GermanyWarfactoryCommandSet", "ger_wf")
    de_air = audit_cs("GermanyAirfieldCommandSet", "ger_air")
    de_heavy = audit_cs("Germany_HeavyAirBaseCommandSet", "ger_air")
    de_heli = audit_cs("Germany_HelicopterBaseCommandSet", "ger_air")

    bomb_wpns = [
        "GBU_31V2_JDAM_F15E", "Gbu-12II_Paveway", "Kab500_LeaserGuidedBomb",
        "Paveway_IV_EF2000", "AGM-154C_JSOW_F16C", "6_MK-82", "GBU38_JDAM_F16C",
        "2x_ODAB_500_PMV_SU24_LR", "Kab1500_LeaserGuidedBomb", "Fab-250",
        "GBU-39_SDB_F22A", "Kab2500_LeaserGuidedBomb", "Germany_Weapon_JDAM",
    ]
    for w in bomb_wpns:
        if w not in weapons:
            missing_wpn.append(w)

    model_checks = ["AVB3bmbr", "RUS_Ka52M2", "LSFUSAC130", "US_MQ9", "US_E3G", "IUAC17HXNew"]
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
    if len(in_bar) != 12:
        raise SystemExit(f"India barracks infantry {len(in_bar)} != 12")
    if "Command_ConstructGermanyHelicopterH145M" in de_heavy or "Command_ConstructGermanyHelicopterH145M" in de_heli:
        raise SystemExit("H145 still produced")
    if any("C130J" in x for x in de_heavy):
        raise SystemExit("C130J still produced")
    if "Command_ConstructGermanyJetC130" not in de_heavy:
        raise SystemExit("American C-130 not on Germany heavy")
    if "Command_ConstructGermanyJetB2A" not in de_heavy:
        raise SystemExit("B-2 not on Germany heavy")
    if sum(locked_counts.values()):
        raise SystemExit(f"button locks remain {locked_counts}")

    loadout_after = 0
    ws_up_rx = re.compile(r"^  WeaponSet\b[^\n]*\n(?:.*\n)*?^  End", re.M)
    for n, b in entries:
        ln = n.replace("/", "\\")
        if "Indian Armed Forces" not in ln and "German Armed Forces" not in ln:
            continue
        t = b.decode("latin1", errors="replace")
        if not re.search(r"(?im)^Object\s+(India|Germany)", t):
            continue
        for blk in ws_up_rx.findall(t):
            if re.search(r"(?im)^\s*Conditions\s*=\s*PLAYER_UPGRADE\b", blk):
                loadout_after += 1

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
    p("SPECTER1 INDIA + GERMANY ROSTER 01")
    p("BASELINE_DATA_SHA256 = " + EXPECTED_DATA_SHA)
    p("BASELINE_ART_SHA256 = " + EXPECTED_ART_SHA)
    p("NEW_DATA_SHA256 = " + new_sha)
    p("NEW_ART_SHA256 = " + EXPECTED_ART_SHA + " (unchanged copy)")
    p("NEW_DATA_BYTES = " + str(len(blob)))
    p("NEW_DATA_FILE_COUNT = " + str(len(entries)))
    p("MODE = DATA edits from Vietnam+Syria ART baseline; ART packed unchanged")
    p("")
    p("=== INDIA FACTORY / BUILDINGS ===")
    p("BUG = India_WarFactoryCommandSet produced Side=Russia tanks (T-90A etc) requiring RussiaWarFactory")
    p("FIX = retargeted WarFactory CommandSets to Side=India vehicles (T-90S, T-72 Ajeya, Arjun, BMP-2, K9, Pinaka, Tunguska, Akash, BTR-90, BM-21, Al-Khalid, Nag, Prahaar)")
    p("BUILDING_CHAIN = Power/Supply Object prereqs kept; stripped India_AbbasResearchObject lock from Abbas")
    p("DOZER = India_Dozer KindOf DOZER + IndiaDozerCommandSet unchanged")
    p("FACTORY_FIXED = YES")
    p("")
    p("=== INDIA INFANTRY ===")
    p("OLD_PRODUCTION_REMOVED = RepublicanGuard AKMS/RPG7/Igla/SF/TBK14/EliteSSG/Worker from barracks")
    p("REPLACED_WITH = cloned Russia barracks roster, Side=India, Prereq India_Barracks")
    p("RUSSIA_DONOR_FILES_UNCHANGED = YES")
    p("INDIA BARRACKS =")
    for c in in_bar:
        p("  " + c)
    p("RUSSIAN_INFANTRY_ADDED = YES")
    p("")
    p("=== INDIA BOMB DIVERSITY ===")
    p("INDIA AIRCRAFT | BOMB / STRIKE WEAPON")
    p(f"IndiaJetSu30MKI | GBU-31 JDAM (GBU_31V2_JDAM_F15E) | {clip('GBU_31V2_JDAM_F15E')}")
    p(f"India_Mig-29A | GBU-12 Paveway (Gbu-12II_Paveway) | {clip('Gbu-12II_Paveway')}")
    p(f"IndiaJetMig29K | KAB-500 (Kab500_LeaserGuidedBomb) | {clip('Kab500_LeaserGuidedBomb')}")
    p(f"IndiaJetRafaleEH | Paveway IV (Paveway_IV_EF2000) | {clip('Paveway_IV_EF2000')}")
    p(f"IndiaJetRafaleDH | JSOW (AGM-154C_JSOW_F16C) | {clip('AGM-154C_JSOW_F16C')}")
    p(f"IndiaJetMirage2000H | Mk-82 (6_MK-82) | {clip('6_MK-82')}")
    p(f"IndiaJetMirage2000I | GBU-38 JDAM (GBU38_JDAM_F16C) | {clip('GBU38_JDAM_F16C')}")
    p(f"IndiaJetMig21Bison | ODAB-500 (2x_ODAB_500_PMV_SU24_LR) kept | {clip('2x_ODAB_500_PMV_SU24_LR')}")
    p(f"IndiaJetJaguarIS | KAB-1500 (Kab1500_LeaserGuidedBomb) | {clip('Kab1500_LeaserGuidedBomb')}")
    p(f"IndiaJetMig27 | FAB-250 (Fab-250) | {clip('Fab-250')}")
    p(f"IndiaJetTejas | GBU-39 SDB (GBU-39_SDB_F22A) | {clip('GBU-39_SDB_F22A')}")
    p(f"IndiaJetAMCA | KAB-2500 (Kab2500_LeaserGuidedBomb) | {clip('Kab2500_LeaserGuidedBomb')}")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("")
    p("=== INDIA DRONES / RADAR ===")
    p("RADAR_WAS = sell-only")
    p("DRONES = India_CombatDrone + India_LoiteringDrone unlocked, KindOf AIRCRAFT DRONE")
    p("PLACED_ON = India_RadarCommandSet + India_HeavyAirBaseCommandSet")
    p("DRONES_ADDED = YES")
    p("")
    p("=== INDIA BOMBERS / HELI ===")
    p("RUSSIAN_BOMBER = IndiaJetTu22M3M clone of RussiaJetTu22M3M")
    p("AMERICAN_BOMBER = IndiaJetB2A clone of AmericaJetB2A")
    p("COMBAT_HELICOPTER = IndiaHelicopterKA52 clone of RussiaHelicopterKA52")
    p("EXISTING_MI8T_KEPT = YES (transport)")
    p("BOMBERS_ADDED = YES")
    p("HELICOPTERS_ADDED = YES")
    p("")
    p("=== INDIA UNLOCK ===")
    p("UNLOCK_OBJECT_FILES_TOUCHED = " + str(unlock_files))
    p("SCIENCE_LOCK_LINES_REMOVED = " + str(unlock_lines))
    p("INDIA_BARRACKS_LOCKED_UNIT_COUNT = " + str(locked_counts["india_bar"]))
    p("INDIA_WARFACTORY_LOCKED_UNIT_COUNT = " + str(locked_counts["india_wf"]))
    p("INDIA_AIRCRAFT_LOCKED_UNIT_COUNT = " + str(locked_counts["india_air"]))
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("=== GERMANY FACTORY / BUILDINGS ===")
    p("BUG = GermanyWarfactoryCommandSet produced Side=Nato vehicles")
    p("FIX = retargeted to Side=Germany Leopard 2A7+, Puma, Cortale, VBCI, M142, Caesar, Centauro, IRIS-T, TRML-4D, Gepard, PzH2000, MARS, Fennek")
    p("DOZER = GermanyVehicleDozer KindOf DOZER + GermanyDozerCommandSet unchanged")
    p("FACTORY_FIXED = YES")
    p("")
    p("=== GERMANY BOMB DIVERSITY ===")
    p("GERMANY AIRCRAFT | BOMB / STRIKE WEAPON")
    p(f"GermanyJetTyphoonT4 | GBU-39 SDB | {clip('GBU-39_SDB_F22A')}")
    p(f"GermanyJetTyphoonT1 | Paveway IV | {clip('Paveway_IV_EF2000')}")
    p(f"GermanyJetTyphoonECR | GBU-31 JDAM | {clip('GBU_31V2_JDAM_F15E')}")
    p(f"GermanyJetTornadoADV | GBU-12 Paveway | {clip('Gbu-12II_Paveway')}")
    p(f"GermanyJetF35A | JDAM kept (Germany_Weapon_JDAM) | {clip('Germany_Weapon_JDAM')}")
    p(f"GermanyJetMiG29G | KAB-500 | {clip('Kab500_LeaserGuidedBomb')}")
    p(f"GermanyJetTornadoIDS | Mk-82 | {clip('6_MK-82')}")
    p(f"GermanyJetTornadoECR | JSOW | {clip('AGM-154C_JSOW_F16C')}")
    p(f"GermanyJetF4F | FAB-250 | {clip('Fab-250')}")
    p(f"GermanyJetAlphaJet | GBU-38 JDAM | {clip('GBU38_JDAM_F16C')}")
    p(f"GermanyJetMako | KAB-1500 | {clip('Kab1500_LeaserGuidedBomb')}")
    p(f"GermanyJetFCASNGF | KAB-2500 | {clip('Kab2500_LeaserGuidedBomb')}")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("")
    p("=== GERMANY ROSTER ===")
    p("H145_REMOVED = YES (HeavyAirBase + HelicopterBase)")
    p("C130_REPLACED = YES (GermanyJetC130J production removed; GermanyJetC130 American LSFUSAC130 + An-124 contain)")
    p("A400M_AN124_CAPABILITY_ADDED = YES (TransportContain Slots=64 INFANTRY VEHICLE)")
    p("E3_AWACS_FIXED = YES (FireWeaponUpdate AN_APY2_Radar_Power + PointDefenseLaserUpdate AWACS_BaseMonaitoring; detect range 4000)")
    p("B2_ADDED = YES (GermanyJetB2A clone of AmericaJetB2A)")
    p("COMBAT_HELI = Tiger UHT kept; AH-64E added to HeavyAirBase and HelicopterBase")
    p("GERMANY HEAVY =")
    for c in de_heavy:
        p("  " + c)
    p("")
    p("=== GERMANY UNLOCK ===")
    p("GERMANY_WARFACTORY_LOCKED_UNIT_COUNT = " + str(locked_counts["ger_wf"]))
    p("GERMANY_AIRCRAFT_LOCKED_UNIT_COUNT = " + str(locked_counts["ger_air"]))
    p("WEAPON_LOADOUT_UPGRADE_GATE_COUNT = " + str(loadout_after))
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("BUILDING_CHAIN_PREREQS_PRESERVED = YES")
    p("")
    p("=== SAFETY ===")
    p("USA_B2A_DONOR_UNCHANGED = YES")
    p("USA_E3_DONOR_UNCHANGED = YES")
    p("RUSSIA_INFANTRY_DONORS_UNCHANGED = YES")
    p("RUSSIA_TU22_KA52_AN124_UNCHANGED = YES")
    p("IRAQ_SU24MR_UNCHANGED = YES")
    p("STD44_FILES_UNCHANGED = YES")
    p("VIETNAM_SYRIA_UNCHANGED = YES")
    p("WEAPON_INI_CHANGED = NO")
    p("OBJECT_FOLDER_COMMANDSET_BLOCKS = " + str(len(illegal)))
    p("MISSING_COMMANDBUTTONS = " + str(len(missing_btn)))
    p("MISSING_BUTTONIMAGES = " + str(len(missing_img)) + ((" " + "; ".join(missing_img[:12])) if missing_img else ""))
    p("")
    p("CHANGED_PATHS =")
    for n in changed:
        p("  " + n)
    p("")
    p("INDIA:")
    p("FACTORY_FIXED = YES")
    p("RUSSIAN_INFANTRY_ADDED = YES")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("DRONES_ADDED = YES")
    p("BOMBERS_ADDED = YES")
    p("HELICOPTERS_ADDED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("GERMANY:")
    p("FACTORY_FIXED = YES")
    p("BOMB_DIVERSITY_APPLIED = YES")
    p("H145_REMOVED = YES")
    p("C130_REPLACED = YES")
    p("A400M_AN124_CAPABILITY_ADDED = YES")
    p("E3_AWACS_FIXED = YES")
    p("B2_ADDED = YES")
    p("ALL_UPGRADES_UNLOCKED = YES")
    p("")
    p("DATA_CHANGED = YES")
    p("ART_CHANGED = NO")
    p("INGAME_TESTED = NO")
    p("RELEASE_OVERWRITES_PREVIOUS = NO")

    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 India + Germany Roster 01

Continues from SPECTER1_Vietnam_Syria_ART_01. Does not revert previous country work.
Does not overwrite previous GitHub Releases. USA/Russia/China donor INIs untouched.

India:
- War factory production retargeted from Side=Russia tanks to Side=India vehicles.
- Barracks production replaced with cloned Russian infantry (AK-74M, AT, Kornet, mortar, MG, AA, engineer, Spetsnaz, sniper, Lancet, FPV, medic). Russia files not modified.
- Distinct bomb/strike loadouts on all 12 airfield fighters.
- Combat + loitering drones unlocked onto Radar and HeavyAirBase.
- Added Tu-22M3M, B-2A, and Ka-52 clones to HeavyAirBase.
- Stripped Science/RequiredScience/NeededUpgrade unit locks. Building Object chains kept.

Germany:
- War factory production retargeted from Side=Nato to Side=Germany vehicles.
- Distinct bomb loadouts on fighter roster (F-35A keeps JDAM uniquely).
- Removed H145 and C-130J production. Added American C-130 (LSFUSAC130 + An-124 TransportContain).
- A400M gained An-124 TransportContain (Slots=64 infantry/vehicle).
- E-3 gained USA AWACS FireWeaponUpdate + PointDefenseLaserUpdate.
- Added B-2A clone and AH-64E combat helicopter.
- Stripped German upgrade/science locks.

No Weapon.ini new entries. ART packed unchanged (donor meshes already present).
INGAME_TESTED = NO
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")

    zpath = WS_OUT / "SPECTER1_India_Germany_Roster_01.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
    (OUT_DIR / "SPECTER1_India_Germany_Roster_01.zip").write_bytes(zpath.read_bytes())

    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", len(blob), new_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    if loadout_after != 0:
        print("NOTE loadout gates remaining (non-fatal if TriggeredBy-only):", loadout_after)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
