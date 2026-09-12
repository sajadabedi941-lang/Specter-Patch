#!/usr/bin/env python3
"""SPECTER WarFactory + Air Force complete rebuild on the live packed DATA chain.

Starts from the unlocked dest War Factory BIG.
- Replaces Japan/Vietnam/SouthKorea WarFactory objects with USA-template buildings.
- Last-wins dest air objects / new dest-only clones (never protected object names).
- Rewrites live dest (and Iran-air) CommandSets inside CommandSet.ini / CommandSet_Pakistan.ini.
- Does not write CommandSet_ZZZZ or fake CommandSet names.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/warfactory_unlock/_SPEC_DATA_ONE.big")
OUT_DIR = Path("/tmp/wf_airforce_complete")
REPO_OBJ = Path("/workspace/patch/Data/INI/Object/Specter/DestinationAirForceComplete/AirForceComplete_Objects.ini")
REPO_BTN = Path("/workspace/patch/Data/INI/CommandButton_AirForceComplete.ini")
REPO_JP = Path("/workspace/patch/Data/INI/Object/Specter/DestinationWarFactoryFix/Japan_WarFactory.ini")
REPO_VN = Path("/workspace/patch/Data/INI/Object/Specter/DestinationWarFactoryFix/Vietnam_WarFactory.ini")
REPO_SK = Path("/workspace/patch/Data/INI/Object/Specter/DestinationWarFactoryFix/SouthKorea_WarFactory.ini")

CS_INI = r"Data\INI\CommandSet.ini"
PK_INI = r"Data\INI\CommandSet_Pakistan.ini"
OBJ_NAME = r"Data\INI\Object\Specter\DestinationAirForceComplete\AirForceComplete_Objects.ini"
BTN_NAME = r"Data\INI\CommandButton_AirForceComplete.ini"

PROTECTED_CS = [
    "NatoWarfactoryCommandSet",
    "AmericaWarFactoryCommandSet",
    "AmericaWarFactoryCommandSet_T3",
    "RussiaWarFactoryCommandSet",
    "EgyptWarFactoryCommandSet",
    "Egypt_WarFactoryCommandSet",
    "Iraq_WarFactoryCommandSet_T3",
    "IranWarfactoryCommandSet",
    "Israel_WarFactoryCommandSet",
    "NorthKorea_WarFactoryCommandSet",
    "ChinaWarFactoryCommandSet",
    "AmericaAirfieldCommandSet",
    "AmericaAirfieldCommandSet_T3",
    "Iraq_AirfieldCommandSet",
    "NatoAirfieldCommandSet",
    "Egypt_AirfieldCommandSet",
    "EgyptAirfieldCommandSet",
]

# Iran air CommandSets are an explicit Part 4 exception.
IRAN_AIR_CS = ("IranAirfieldCommandSet", "IranExpandedAirfieldCommandSet")

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
    r"data\ini\weapon.ini",
)

WF_REPLACE = {
    r"data\ini\object\specter\japan self-defense forces\buildings\japan_warfactory.ini": "Japan",
    r"data\ini\object\specter\vietnam people's armed forces\buildings\vietnam_warfactory.ini": "Vietnam",
    r"data\ini\object\specter\south korean armed forces\buildings\southkorea_warfactory.ini": "SouthKorea",
}

BOMB = "4x_GBU54B_500lb_LGB_EF2000"
BOMB2 = "Pakistan_Weapon_Bomb_F16AMLU"
CAS_ATGM = "6x_GRATGM_Brimstone3_EF2000"

PAK_F16_WS = """WeaponSet
    Conditions = None
    Weapon              = PRIMARY    Pakistan_Weapon_AIM120_F16AMLU
    PreferredAgainst    = PRIMARY    AIRCRAFT
    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon              = SECONDARY  Pakistan_Weapon_AIM9_F16AMLU
    PreferredAgainst    = SECONDARY  AIRCRAFT
    AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon              = TERTIARY   Pakistan_Weapon_Bomb_F16AMLU
    PreferredAgainst    = TERTIARY   VEHICLE STRUCTURE
    AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI
  End"""

CAS_WS = f"""WeaponSet
    Conditions = None
    Weapon              = PRIMARY    {CAS_ATGM}
    PreferredAgainst    = PRIMARY    VEHICLE STRUCTURE
    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon              = SECONDARY  {BOMB}
    PreferredAgainst    = SECONDARY  VEHICLE STRUCTURE
    AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon              = TERTIARY   {BOMB2}
    PreferredAgainst    = TERTIARY   VEHICLE STRUCTURE
    AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI
  End"""

E737_SCAN = """
  Behavior = StealthDetectorUpdate ModuleTag_AWACS_StealthDetect
    DetectionRate   = 1800
    DetectionRange = 2700
    CanDetectWhileGarrisoned  = No
    CanDetectWhileContained   = No
    ExtraForbiddenKindOf = UNATTACKABLE
  End
  Behavior = OCLSpecialPower ModuleTag_E737_SAR
    SpecialPowerTemplate = AmericaE737TargetedSARScan
    OCL                  = OCL_AmericaE737TargetedSARScan
    CreateLocation       = CREATE_AT_LOCATION
  End
  Behavior = FireWeaponUpdate ModuleTag_AWACS_RadarPower
    Weapon                    = AN_APY2_Radar_Power
    ExclusiveWeaponDelay      = 1000
  End
"""


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


def parse_block(text, start):
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
            r"(?i)^\s*(Draw|Behavior|Body|WeaponSet|ArmorSet|Prerequisites|DefaultConditionState|ConditionState|UnitSpecificSounds|ClientUpdate)\b",
            raw,
        ):
            depth += 1
        elif re.match(r"(?i)^\s*Turret\s*$", raw):
            depth += 1
    return "".join(buf)


def extract_named(kind, name, text):
    found = None
    pat = re.compile(rf"(?im)^{kind}\s+{re.escape(name)}\b")
    for m in pat.finditer(text):
        found = parse_block(text, m.start())
    return found


def last_object(name, obj_idx):
    return obj_idx.get(name)


def index_entries(entries):
    obj_idx = {}
    btn_idx = {}
    opat = re.compile(r"(?im)^Object(?:Reskin)?\s+(\S+)")
    bpat = re.compile(r"(?im)^CommandButton\s+(\S+)")
    for fname, blob in entries:
        text = blob.decode("latin1", errors="ignore")
        for m in opat.finditer(text):
            obj_idx[m.group(1)] = parse_block(text, m.start())
        for m in bpat.finditer(text):
            btn_idx[m.group(1)] = parse_block(text, m.start())
    return obj_idx, btn_idx


def field(blk, key):
    if not blk:
        return None
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", blk)
    return m.group(1) if m else None


def set_field(blk, key, value):
    if re.search(rf"(?im)^\s*{re.escape(key)}\s*=", blk):
        return re.sub(rf"(?im)^(\s*{re.escape(key)}\s*=\s*)\S+", rf"\g<1>{value}", blk, count=1)
    # insert after Side if present else after object header
    m = re.search(r"(?im)^\s*Side\s*=\s*\S+.*\n", blk)
    line = f"  {key} = {value}\n"
    if m:
        return blk[: m.end()] + line + blk[m.end() :]
    return blk


def rename_object(blk, old, new):
    return re.sub(rf"(?im)^(Object(?:Reskin)?)\s+{re.escape(old)}\b", rf"\g<1> {new}", blk, count=1)


def strip_prereq(blk):
    if not re.search(r"(?im)^\s*Prerequisites\b", blk):
        return blk
    return re.sub(r"(?ims)^\s*Prerequisites\b.*?^\s*End\s*\r?\n", "  Prerequisites\r\n  End\r\n", blk, count=1)


def replace_weaponset(blk, new_ws):
    m = re.search(r"(?ims)^\s*WeaponSet\b.*?^\s*End\s*\r?\n", blk)
    if not m:
        # insert before first ArmorSet or after Side
        ins = new_ws.rstrip() + "\r\n"
        a = re.search(r"(?im)^\s*ArmorSet\b", blk)
        if a:
            return blk[: a.start()] + ins + blk[a.start() :]
        return blk
    return blk[: m.start()] + new_ws.rstrip() + "\r\n" + blk[m.end() :]


def replace_tertiary(blk, weapon):
    if re.search(r"(?im)^\s*Weapon\s*=\s*TERTIARY\s+\S+", blk):
        return re.sub(r"(?im)^(\s*Weapon\s*=\s*TERTIARY\s+)\S+", rf"\g<1>{weapon}", blk, count=1)
    m = re.search(r"(?ims)^\s*WeaponSet\b.*?^\s*End\s*\r?\n", blk)
    if not m:
        return replace_weaponset(blk, PAK_F16_WS.replace("Pakistan_Weapon_Bomb_F16AMLU", weapon))
    body = m.group(0)
    body = re.sub(
        r"(?im)^(\s*End\b)",
        f"    Weapon              = TERTIARY   {weapon}\r\n"
        f"    PreferredAgainst    = TERTIARY   VEHICLE STRUCTURE\r\n"
        f"    AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI\r\n  \\1",
        body,
        count=1,
    )
    return blk[: m.start()] + body + blk[m.end() :]


def replace_models(blk, mapping):
    def sub(m):
        name = m.group(2)
        return m.group(1) + mapping.get(name, name)

    return re.sub(r"(?im)^(\s*Model\s*=\s*)(\S+)", sub, blk)


def strip_modules(blk, kind):
    return re.sub(rf"(?ims)^\s*Behavior\s*=\s*{kind}\b.*?^\s*End\s*\r?\n", "", blk)


def make_usa_factory(template, country, obj_name, commandset, supply):
    blk = rename_object(template, "AmericaWarFactory_T", obj_name)
    blk = set_field(blk, "Side", country)
    blk = set_field(blk, "CommandSet", commandset)
    blk = set_field(blk, "BuildCost", "1500")
    blk = set_field(blk, "BuildTime", "16.0")
    blk = set_field(blk, "DisplayName", "OBJECT:WarFactory")
    blk = re.sub(
        r"(?ims)^\s*Prerequisites\b.*?^\s*End\s*\r?\n",
        f"  Prerequisites\r\n    Object = {supply}\r\n  End\r\n",
        blk,
        count=1,
    )
    blk = strip_modules(blk, "CommandSetUpgrade")
    blk = strip_modules(blk, "GrantUpgradeCreate")
    blk = strip_modules(blk, "ObjectCreationUpgrade")
    # Keep construction/production modules from USA template.
    return blk.rstrip() + "\r\n"


def make_button(name, obj, image="us_airfield"):
    return (
        f"CommandButton {name}\r\n"
        f"  Command       = UNIT_BUILD\r\n"
        f"  Object        = {obj}\r\n"
        f"  TextLabel     = CONTROLBAR:Construct{obj}\r\n"
        f"  ButtonImage   = {image}\r\n"
        f"  ButtonBorderType = BUILD\r\n"
        f"  DescriptLabel = CONTROLBAR:ToolTipConstruct{obj}\r\n"
        f"End\r\n"
    )


def clone(obj_idx, src, new_name, side, model_map=None, weaponset=None, extra=None):
    blk = obj_idx[src]
    old = field(blk, "None")  # unused
    # object header name from first line
    m = re.match(r"(?im)^Object(?:Reskin)?\s+(\S+)", blk)
    old_name = m.group(1)
    blk = rename_object(blk, old_name, new_name)
    blk = set_field(blk, "Side", side)
    blk = strip_prereq(blk)
    if model_map:
        blk = replace_models(blk, model_map)
    if weaponset:
        blk = replace_weaponset(blk, weaponset)
    if extra:
        blk = extra(blk)
    return blk.rstrip() + "\r\n"


def format_cs(name, slots, nl):
    lines = [f"CommandSet {name}"]
    # Keep stock Specter spacing. ZH crashed on 20-slot bars; cap at 18.
    kept = []
    for slot, btn in slots:
        if int(slot) > 18:
            continue
        kept.append((slot, btn))
        if len(str(slot)) == 1:
            lines.append(f"  {slot} = {btn}")
        else:
            lines.append(f"  {slot} = {btn}")
    lines.append("End")
    return nl.join(lines) + nl


def replace_cs(text, name, slots):
    nl = "\r\n" if "\r\n" in text else "\n"
    pat = re.compile(rf"(?im)^CommandSet\s+{re.escape(name)}\b")
    matches = list(pat.finditer(text))
    if not matches:
        return text, 0
    new_blk = format_cs(name, slots, nl)
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


def cs_slots(blk):
    out = []
    if not blk:
        return out
    for line in blk.splitlines():
        raw = line.split(";", 1)[0]
        m = re.match(r"\s*(\d+)\s*=\s*(\S+)", raw)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def upsert_slots(slots, extras):
    """Keep existing slots, overlay extras (slot->btn)."""
    cur = {s: b for s, b in slots}
    cur.update({str(s): b for s, b in extras})
    return sorted(cur.items(), key=lambda x: int(x[0]))


def patch_kindof_attack(blk):
    m = re.search(r"(?im)^(\s*KindOf\s*=\s*)(.+)$", blk)
    if not m:
        return blk
    kinds = m.group(2)
    if "CAN_ATTACK" not in kinds:
        kinds = kinds.rstrip() + " CAN_ATTACK"
    return blk[: m.start()] + m.group(1) + kinds + blk[m.end() :]


def add_e737_scan(blk):
    blk = re.sub(
        r"(?ims)^\s*Behavior\s*=\s*StealthDetectorUpdate\b.*?^\s*End\s*\r?\n",
        "",
        blk,
    )
    # insert before Geometry or End
    g = re.search(r"(?im)^\s*Geometry\b", blk)
    extra = E737_SCAN
    if g:
        return blk[: g.start()] + extra + blk[g.start() :]
    return blk[:-4] + extra + "End\r\n"


def main() -> int:
    src = parse_big(SRC_DATA)
    obj_idx, btn_idx = index_entries(src)
    cs_blob = pk_blob = None
    cs_name = pk_name = None
    for n, b in src:
        key = n.replace("/", "\\")
        if key == CS_INI:
            cs_blob = b
            cs_name = n
        elif key == PK_INI:
            pk_blob = b
            pk_name = n
    if not cs_blob or not pk_blob:
        raise SystemExit("missing CommandSet files")
    cs_text = cs_blob.decode("latin1")
    pk_text = pk_blob.decode("latin1")
    prot_before = {n: extract_named("CommandSet", n, cs_text) for n in PROTECTED_CS}

    usa = obj_idx["AmericaWarFactory_T"]
    jp_wf = make_usa_factory(usa, "Japan", "Japan_WarFactory", "Japan_WarFactoryCommandSet", "Japan_SupplyCenter")
    vn_wf = make_usa_factory(usa, "Vietnam", "Vietnam_WarFactory", "Vietnam_WarFactoryCommandSet", "Vietnam_SupplyCenter")
    sk_wf = make_usa_factory(usa, "SouthKorea", "SouthKorea_WarFactory", "SouthKorea_WarFactoryCommandSet", "SouthKorea_SupplyCenter")
    for p, blob in ((REPO_JP, jp_wf), (REPO_VN, vn_wf), (REPO_SK, sk_wf)):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(blob, encoding="latin1")

    parts = [
        "; Dest-only / dest last-win air + Japan-chain factory support objects.",
        "; Live object names are last-won here. Protected country objects are not redefined.",
        "",
    ]
    buttons = [
        "; Dest-only Air Force CommandButtons. New names only.",
        "",
    ]
    notes = []

    def add_obj(blk, note):
        text = blk.rstrip() + "\r\n"
        if not re.search(r"(?im)^End\s*$", text.splitlines()[-1]):
            text += "End\r\n"
        # ZH crashes if a last-win object is missing its Object End
        if not re.search(r"(?ims)^Object(?:Reskin)?\s+\S+.+\nEnd\s*$", text):
            print("WARN object may be unclosed", note)
        parts.append(text + "\r\n")
        notes.append(note)

    def add_btn(name, obj, image="us_airfield"):
        if name not in btn_idx:
            buttons.append(make_button(name, obj, image) + "\r\n")

    # --- dest last-wins: Saudi F5E visual ---
    f5 = obj_idx["SaudiJetF5E"]
    f5 = replace_models(
        f5,
        {
            "AVHawk": "LSFKoreaF5",
            "AVHawk_D": "LSFKoreaF5d",
            "AVHawk_D1": "LSFKoreaF5k",
        },
    )
    add_obj(f5, "SaudiJetF5E visual LSFKoreaF5")
    obj_idx["SaudiJetF5E"] = f5

    # Saudi AA-only fighters get bombs
    for name in ("SaudiJetF15C", "SaudiJetTyphoon", "SaudiJetTornadoADV", "SaudiJetLightning"):
        add_obj(replace_tertiary(obj_idx[name], BOMB), f"{name} tertiary bomb")

    # Saudi CAS clones for multiple loadouts
    for src_name in (
        "SaudiJetF15S",
        "SaudiJetF15C",
        "SaudiJetTyphoon",
        "SaudiJetTornadoADV",
        "SaudiJetF5E",
    ):
        new = src_name + "_CAS"
        add_obj(clone(obj_idx, src_name, new, "SaudiArabia", weaponset=CAS_WS), f"{new}")
        add_btn(f"Command_Construct{new}", new)

    # Saudi combat heli
    add_obj(clone(obj_idx, "NatoHelicopterAH64E", "SaudiAir_AH64E", "SaudiArabia"), "SaudiAir_AH64E")
    add_btn("Command_ConstructSaudiAir_AH64E", "SaudiAir_AH64E", "us_ah64e")

    # --- UAE F-16B1K52 no-fire + bombs ---
    uae_f16 = replace_weaponset(obj_idx["UAE_F16Blk52"], PAK_F16_WS)
    uae_f16 = patch_kindof_attack(uae_f16)
    add_obj(uae_f16, "UAE_F16Blk52 Pakistan weapons")
    for name in ("UAEJetMirage20009", "UAEJetF15SA"):
        add_obj(replace_tertiary(obj_idx[name], BOMB), f"{name} tertiary bomb")
    for src_name in ("UAE_F16Blk52", "UAEJetF16E", "UAEJetMirage20009", "UAEJetF15SA"):
        new = src_name.replace("-", "_") + "_CAS"
        add_obj(clone(obj_idx, src_name, new, "UAE", weaponset=CAS_WS), new)
        add_btn(f"Command_Construct{new}", new)
    add_obj(clone(obj_idx, "NatoHelicopterAH64E", "UAEAir_AH64E", "UAE"), "UAEAir_AH64E")
    add_btn("Command_ConstructUAEAir_AH64E", "UAEAir_AH64E", "us_ah64e")

    # --- India bombs + heli ---
    add_obj(replace_tertiary(obj_idx["IndiaJetSu30MKI"], BOMB), "IndiaJetSu30MKI bomb")
    add_obj(replace_tertiary(obj_idx["IndiaJetMirage2000H"], BOMB), "IndiaJetMirage2000H bomb")
    mig = replace_weaponset(obj_idx["India_Mig-29A"], PAK_F16_WS)
    add_obj(mig, "India_Mig-29A bombs")
    for src_name in ("IndiaJetSu30MKI", "India_Mig-29A", "IndiaJetMirage2000H"):
        new = src_name.replace("-", "_") + "_CAS"
        add_obj(clone(obj_idx, src_name, new, "India", weaponset=CAS_WS), new)
        add_btn(f"Command_Construct{new}", new)
    add_obj(clone(obj_idx, "NatoHelicopterAH64E", "IndiaAir_AH64E", "India"), "IndiaAir_AH64E")
    add_btn("Command_ConstructIndiaAir_AH64E", "IndiaAir_AH64E", "us_ah64e")

    # --- Pakistan bombs + extra heli / fighters ---
    add_obj(replace_weaponset(obj_idx["Pakistan_Mig-29A"], PAK_F16_WS), "Pakistan_Mig-29A bombs")
    add_obj(replace_tertiary(obj_idx["PakistanJetJ10CE"], BOMB), "PakistanJetJ10CE bomb")
    for src_name in ("Pakistan_F16Blk52", "PakistanJetJ10CE", "Pakistan_Mig-29A"):
        new = src_name.replace("-", "_") + "_CAS"
        add_obj(clone(obj_idx, src_name, new, "Pakistan", weaponset=CAS_WS), new)
        add_btn(f"Command_Construct{new}", new)
    add_obj(clone(obj_idx, "NatoHelicopterAH64E", "PakistanAir_AH64E", "Pakistan"), "PakistanAir_AH64E")
    add_btn("Command_ConstructPakistanAir_AH64E", "PakistanAir_AH64E", "us_ah64e")

    # extra Pakistan fighters already in DATA
    for src_name, btn in (
        ("PakistanJetJF17", "Command_ConstructPakistanJetJF17"),
        ("PakistanJetJF17Blk3", "Command_ConstructPakistanJetJF17Blk3"),
        ("PakistanJetF16AMLU", "Command_ConstructPakistanJetF16AMLU"),
        ("PakistanJetMirage5", "Command_ConstructPakistanJetMirage5"),
    ):
        if src_name in obj_idx:
            add_btn(btn, src_name)

    # --- South Korea helis / E737 / USA transport ---
    add_obj(clone(obj_idx, "NatoHelicopterUH60", "SouthKoreaJetUH60P", "SouthKorea"), "SK UH60P USA UH-60")
    add_obj(clone(obj_idx, "NatoHelicopterAH64E", "SouthKoreaJetAH64E", "SouthKorea"), "SK AH64E NATO weapons")
    add_obj(clone(obj_idx, "NatoHelicopterCH47F", "SouthKoreaJetCH47", "SouthKorea"), "SK CH47 NATO chinook")
    add_obj(
        clone(obj_idx, "NatoHelicopterAH64E", "SouthKoreaHelicopterLAH", "SouthKorea"),
        "SK LAH working AH64 donor",
    )
    add_obj(clone(obj_idx, "NatoHelicopterUH60", "SouthKoreaHelicopterKUH1", "SouthKorea"), "SK KUH-1 UH60 donor")
    e737 = add_e737_scan(obj_idx["SouthKoreaJetE737"])
    e737 = set_field(e737, "VisionRange", "810")
    e737 = set_field(e737, "ShroudClearingRange", "810")
    add_obj(e737, "SK E737 SAR/scan")
    add_obj(clone(obj_idx, "BritainJetC17", "SouthKoreaAir_USATransport", "SouthKorea"), "SK USA C-17 transport")
    add_btn("Command_ConstructSouthKoreaAir_USATransport", "SouthKoreaAir_USATransport", "yier76")

    # --- South Africa ---
    add_obj(strip_prereq(obj_idx["SouthAfrica_MirageF1_Bq"]), "SA Mirage F1 unlocked")
    oryx = clone(
        obj_idx,
        "Iraq_Mi-8T",
        "SouthAfricaHelicopterOryx",
        "SouthAfrica",
        model_map={"Irq_Mi8T": "Irq_Mi8T", "Irq_MI8T": "Irq_Mi8T"},
    )
    add_obj(oryx, "SA Oryx Mi-8 visual")
    imp = replace_models(
        obj_idx["SouthAfricaJetImpala"],
        {"UV_Turbo": "UVVampire", "UV_Turbo_D": "UVVampire_D"},
    )
    add_obj(imp, "SA Impala UVVampire")
    add_obj(clone(obj_idx, "NatoHelicopterAH64E", "SouthAfricaAir_AH64E", "SouthAfrica"), "SA combat heli")
    add_btn("Command_ConstructSouthAfricaAir_AH64E", "SouthAfricaAir_AH64E", "us_ah64e")

    # --- Vietnam Mi-17 combat + bombs ---
    def vn_mi17(blk):
        blk = set_field(blk, "CommandSet", "GenericAttackHelicopterHoverCommandSet")
        blk = patch_kindof_attack(blk)
        return replace_models(blk, {"RUS_MI8MTV5": "RUS_MI8MTV5"})

    add_obj(
        clone(obj_idx, "RussiaHelicopterMi8AMTSh", "VietnamJetMi17", "Vietnam", extra=vn_mi17),
        "VN Mi-17 combat",
    )
    add_obj(replace_tertiary(obj_idx["VietnamJetMig29S"], BOMB), "VN Mig29S bomb")
    add_obj(replace_tertiary(obj_idx["VietnamJetSu27"], BOMB), "VN Su27 bomb")
    for src_name in ("VietnamJetMig29S", "VietnamJetSu27", "VietnamJetSu30", "VietnamJetF5E"):
        new = src_name + "_CAS"
        add_obj(clone(obj_idx, src_name, new, "Vietnam", weaponset=CAS_WS), new)
        add_btn(f"Command_Construct{new}", new)
    add_obj(clone(obj_idx, "NatoHelicopterAH64E", "VietnamAir_AH64E", "Vietnam"), "VN extra heli")
    add_btn("Command_ConstructVietnamAir_AH64E", "VietnamAir_AH64E", "us_ah64e")

    # --- Iran air (Part 4 exception): new names only ---
    add_obj(clone(obj_idx, "Iraq_Tu-22M3", "IranAir_Tu22M3", "Iran"), "Iran Tu-22M3")
    add_obj(clone(obj_idx, "Iraq_Su-24MR", "IranAir_Su24MR", "Iran"), "Iran Su-24MR")
    add_obj(clone(obj_idx, "IraqJetIL76", "IranAir_IL76", "Iran"), "Iran IL-76 Iraq working")
    add_btn("Command_ConstructIranAir_Tu22M3", "IranAir_Tu22M3", "yier76")
    add_btn("Command_ConstructIranAir_Su24MR", "IranAir_Su24MR")
    add_btn("Command_ConstructIranAir_IL76", "IranAir_IL76", "yier76")

    obj_blob = ("\r\n".join(parts[:3]) + "\r\n\r\n" + "".join(parts[3:])).encode("latin1")
    btn_blob = ("\r\n".join(buttons[:2]) + "\r\n\r\n" + "".join(buttons[2:])).encode("latin1")
    REPO_OBJ.parent.mkdir(parents=True, exist_ok=True)
    REPO_OBJ.write_bytes(obj_blob)
    REPO_BTN.write_bytes(btn_blob)
    print("wrote", REPO_OBJ, len(obj_blob), "objects", len(notes))
    print("wrote", REPO_BTN, len(btn_blob))
    for n in notes:
        print(" OBJ", n)

    # --- live CommandSet rewrites ---
    def apply_air(text, name, extras, use_base=None):
        src_blk = extract_named("CommandSet", use_base or name, text)
        if not src_blk:
            print("WARN missing CS", name)
            return text
        slots = upsert_slots(cs_slots(src_blk), extras)
        new, n = replace_cs(text, name, slots)
        print("CS", name, n, "slots", len(slots))
        return new

    # ZH parse-crashes on 20-slot bars. Keep F-5E CAS (priority unit) inside 1-18.
    saudi_extra = [
        (15, "Command_ConstructSaudiArabia_Mi-8T"),
        (16, "Command_ConstructSaudiAir_AH64E"),
        (17, "Command_ConstructSaudiJetF5E_CAS"),
        (18, "Command_ConstructSaudiJetF15S_CAS"),
    ]
    uae_extra = [
        (15, "Command_ConstructUAE_Mi-8T"),
        (16, "Command_ConstructUAEAir_AH64E"),
        (17, "Command_ConstructUAE_F16Blk52_CAS"),
        (18, "Command_ConstructUAEJetF16E_CAS"),
        (19, "Command_ConstructUAEJetMirage20009_CAS"),
        (20, "Command_ConstructUAEJetF15SA_CAS"),
    ]
    india_extra = [
        (15, "Command_ConstructIndia_Mi-8T"),
        (16, "Command_ConstructIndiaAir_AH64E"),
        (17, "Command_ConstructIndiaJetSu30MKI_CAS"),
        (18, "Command_ConstructIndia_Mig_29A_CAS"),
        (19, "Command_ConstructIndiaJetMirage2000H_CAS"),
    ]
    sa_extra = [
        (15, "Command_ConstructSouthAfricaHelicopterOryx"),
        (16, "Command_ConstructSouthAfricaAir_AH64E"),
    ]
    iran_extra = [
        (15, "Command_ConstructIranAir_Tu22M3"),
        (16, "Command_ConstructIranAir_Su24MR"),
        (17, "Command_ConstructIranAir_IL76"),
    ]
    sk_extra = [
        (15, "Command_ConstructSouthKoreaJetUH60P"),
        (16, "Command_ConstructSouthKoreaJetAH64E"),
        (17, "Command_ConstructSouthKoreaJetCH47"),
        (18, "Command_ConstructSouthKoreaHelicopterLAH"),
        (19, "Command_ConstructSouthKoreaHelicopterKUH1"),
        (20, "Command_ConstructSouthKoreaJetE737"),
        (21, "Command_ConstructSouthKoreaAir_USATransport"),
    ]
    vn_full = [
        (1, "Command_ConstructVietnamJetMig29S"),
        (2, "Command_ConstructVietnamJetMig21"),
        (3, "Command_ConstructVietnamJetSu22"),
        (4, "Command_ConstructVietnamJetSu27"),
        (5, "Command_ConstructVietnamJetSu30"),
        (6, "Command_ConstructVietnamJetYak130"),
        (7, "Command_ConstructVietnamJetF5E"),
        (8, "Command_ConstructVietnamJetMig21bis"),
        (9, "Command_ConstructVietnamJetSu22M4"),
        (10, "Command_ConstructVietnamJetSu30MK2"),
        (11, "Command_ConstructVietnamJetSu27UB"),
        (12, "Command_ConstructVietnamJetL39"),
        (13, "Command_SetRallyPoint"),
        (14, "Command_Sell"),
        (15, "Command_ConstructVietnamJetMi17"),
        (16, "Command_ConstructVietnamAir_AH64E"),
        (17, "Command_ConstructVietnamJetMig29S_CAS"),
        (18, "Command_ConstructVietnamJetSu27_CAS"),
        (19, "Command_ConstructVietnamJetSu30_CAS"),
        (20, "Command_ConstructVietnamJetF5E_CAS"),
    ]
    pk_full = [
        (1, "Command_ConstructPakistan_Mig-29A"),
        (2, "Command_ConstructPakistan_MirageF1_Bq"),
        (3, "Command_ConstructPakistan_Su-25K"),
        (4, "Command_ConstructPakistan_Mi-8T"),
        (5, "Command_ConstructPakistan_IL-76"),
        (6, "Command_ConstructPakistanAir_AH64E"),
        (7, "Command_ConstructPakistan_F16Blk52"),
        (8, "Command_ConstructPakistan_F16Blk52_CAS"),
        (9, "Command_ConstructPakistanJetJ10CE"),
        (10, "Command_ConstructPakistanJetJ10CE_CAS"),
        (11, "Command_ConstructPakistanJetJF17"),
        (12, "Command_ConstructPakistanJetJF17Blk3"),
        (13, "Command_SetRallyPoint"),
        (14, "Command_Sell"),
        (15, "Command_ConstructPakistan_Mig_29A_CAS"),
        (16, "Command_ConstructPakistanJetF16AMLU"),
        (17, "Command_ConstructPakistanJetMirage5"),
    ]

    for name in (
        "SaudiArabia_AirfieldCommandSet",
        "SaudiArabia_AirfieldCommandSet1",
        "SaudiArabia_AirfieldCommandSet2",
        "SaudiArabia_AirfieldCommandSet3",
    ):
        cs_text = apply_air(cs_text, name, saudi_extra)
    for name in (
        "UAE_AirfieldCommandSet",
        "UAE_AirfieldCommandSet1",
        "UAE_AirfieldCommandSet2",
        "UAE_AirfieldCommandSet3",
    ):
        cs_text = apply_air(cs_text, name, uae_extra)
    for name in (
        "India_AirfieldCommandSet",
        "India_AirfieldCommandSet1",
        "India_AirfieldCommandSet2",
        "India_AirfieldCommandSet3",
    ):
        cs_text = apply_air(cs_text, name, india_extra)
    for name in (
        "SouthAfrica_AirfieldCommandSet",
        "SouthAfrica_AirfieldCommandSet1",
        "SouthAfrica_AirfieldCommandSet2",
        "SouthAfrica_AirfieldCommandSet3",
    ):
        cs_text = apply_air(cs_text, name, sa_extra)
    for name in IRAN_AIR_CS:
        cs_text = apply_air(cs_text, name, iran_extra)
    cs_text = apply_air(cs_text, "SouthKorea_AirfieldCommandSet", sk_extra)
    sk_heavy = [
        (1, "Command_ConstructSouthKoreaJetE737"),
        (2, "Command_ConstructSouthKoreaAir_USATransport"),
        (3, "Command_ConstructSouthKoreaJetUH60P"),
        (4, "Command_ConstructSouthKoreaJetAH64E"),
        (5, "Command_ConstructSouthKoreaJetCH47"),
        (6, "Command_ConstructSouthKoreaHelicopterLAH"),
        (7, "Command_ConstructSouthKoreaHelicopterKUH1"),
        (13, "Command_SetRallyPoint"),
        (14, "Command_Sell"),
    ]
    new, n = replace_cs(cs_text, "SouthKorea_HeavyAirBaseCommandSet", [(str(s), b) for s, b in sk_heavy])
    print("CS SouthKorea_HeavyAirBaseCommandSet", n, "full")
    cs_text = new
    # Vietnam: replace whole bar
    for name in ("Vietnam_AirfieldCommandSet",):
        new, n = replace_cs(cs_text, name, [(str(s), b) for s, b in vn_full])
        print("CS", name, n, "full")
        cs_text = new
    # Pakistan live file
    for name in (
        "Pakistan_AirfieldCommandSet",
        "Pakistan_AirfieldCommandSet1",
        "Pakistan_AirfieldCommandSet2",
        "Pakistan_AirfieldCommandSet3",
    ):
        new, n = replace_cs(pk_text, name, [(str(s), b) for s, b in pk_full])
        print("CS", name, "Pakistan.ini", n)
        pk_text = new

    for n in PROTECTED_CS:
        after = extract_named("CommandSet", n, cs_text)
        if after != prot_before[n]:
            print("FAIL protected CS mutated", n)
            return 1
    print("PROTECTED_CS_UNCHANGED")

    new_cs = cs_text.encode("latin1")
    new_pk = pk_text.encode("latin1")

    # CommandSet.ini is parsed before trailing BIG files. New buttons must
    # exist in CommandButton.ini (index before CommandSet.ini) or ZH crashes.
    CB_INI = r"Data\INI\CommandButton.ini"
    WF_BTN = r"Data\INI\CommandButton_WFUnlock.ini"
    wfunlock_btn = b""
    for n, b in src:
        if n.replace("/", "\\") == WF_BTN:
            wfunlock_btn = b
            break
    out = []
    for n, b in src:
        key = n.replace("/", "\\")
        low = key.lower()
        if key == CS_INI:
            out.append((n, new_cs))
        elif key == PK_INI:
            out.append((n, new_pk))
        elif key == CB_INI:
            extra = b""
            if wfunlock_btn:
                extra += b"\r\n\r\n" + wfunlock_btn.rstrip()
            extra += b"\r\n\r\n" + btn_blob
            merged = b.rstrip() + extra
            if not merged.startswith(b.rstrip()):
                print("FAIL CommandButton.ini prefix mutated")
                return 1
            print("appended dest unlock+air buttons to CommandButton.ini", len(extra))
            out.append((n, merged))
        elif low in WF_REPLACE:
            country = WF_REPLACE[low]
            blob = {"Japan": jp_wf, "Vietnam": vn_wf, "SouthKorea": sk_wf}[country]
            print("replaced WF object", n, "len", len(blob))
            out.append((n, blob.encode("latin1")))
        else:
            out.append((n, b))
    out.append((OBJ_NAME, obj_blob))
    out.append((BTN_NAME, btn_blob))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(out)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    dsha = hashlib.sha256(data_big).hexdigest()
    print("DATA", dsha, len(data_big))
    (OUT_DIR / "SHA256.txt").write_text(f"DATA {dsha}\n")

    packed = parse_big(OUT_DIR / "_SPEC_DATA_ONE.big")
    src_map = {n.replace("/", "\\").lower(): b for n, b in src}
    new_map = {n.replace("/", "\\").lower(): (n, b) for n, b in packed}
    print("DATA diffs:")
    for k, (n, b) in new_map.items():
        if src_map.get(k) != b:
            print(" ", n)
            low = n.lower()
            if any(tok in low for tok in PROTECTED_PATHS):
                # Shared INI files may gain dest-only tails. Object folders must not change.
                if not low.endswith((r"data\ini\commandset.ini", r"data\ini\commandbutton.ini")):
                    print("FAIL protected path changed", n)
                    return 1
    print("PACK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
