#!/usr/bin/env python3
"""Japan aircraft final completion: slots, unique loadouts, F-35A/B split.

Source: latest packed japan_f35_ew BIGs.
Does not touch CommandCenter, VT72B, PlayerTemplate, Science, or airfield buildings.
No new meshes. ART is copied through unless a packed stem is missing.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/japan_f35_ew/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/japan_f35_ew/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/japan_aircraft_final")

LOCKED_PATHS = (
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\Science.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Tracked\Japan_VT72B.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Tracked\VT72B.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_CommandCenter.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_CommandCenter.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_Airfield.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_LargeAirBase.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_HeavyAirBase.ini",
)

LOCKED_COMMANDSETS = (
    "Japan_VT72BCommandSet",
    "SouthKorea_VT72BCommandSet",
    "Vietnam_VT72BCommandSet",
    "Japan_CommandCenterCommandSet",
    "SouthKorea_CommandCenterCommandSet",
    "Vietnam_CommandCenterCommandSet",
    "SouthKorea_AirfieldCommandSet",
    "SouthKorea_HeavyAirBaseCommandSet",
    "Vietnam_AirfieldCommandSet",
    "Vietnam_HeavyAirBaseCommandSet",
)

FIGHTER_BAR = """CommandSet Japan_AirfieldCommandSet
  1 = Command_ConstructJapanJetF35A
  2 = Command_ConstructJapanJetF35B
  3 = Command_ConstructJapanJetF15J
  4 = Command_ConstructJapanJetF15DJ
  5 = Command_ConstructJapanJetF2A
  6 = Command_ConstructJapanJetF2B
  7 = Command_ConstructJapanJetF2Kai
  8 = Command_ConstructJapanJetF4EJKai
  9 = Command_ConstructJapanJetX2Shinshin
  10 = Command_ConstructJapanJetF16
  11 = Command_ConstructJapanJetF18G
  12 = Command_ConstructJapanJetEA6B
  13 = Command_ConstructJapanJetF35Japon
  14 = Command_ConstructJapanJetF14Tomcat
End
"""

EA6B_COMMANDSET = """CommandSet JapanEA6BBomberCommandSet
  1 = Command_FireMainWeapon
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
"""

# Unique AG per aircraft. F-35B / F-15J are AIM-120 + AIM-9X only.
WEAPONSETS = {
    "JapanJetF35B": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaF35C_AA_AIM120
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY AIM9X_HOBS_SRAAM_F35C
    PreferredAgainst = SECONDARY AIRCRAFT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF15J": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaF35C_AA_AIM120
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY AIM9X_HOBS_SRAAM_F22A
    PreferredAgainst = SECONDARY AIRCRAFT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF35A": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaF35C_AA_AIM120
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY GBU_31V2_JDAM_F35C
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF15DJ": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaF35C_AA_AIM120
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY GBU_31V2_JDAM_F15E
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF2A": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY Japan_Weapon_ASM2_F2A
    PreferredAgainst = PRIMARY VEHICLE STRUCTURE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY Gbu-12II_Paveway
    PreferredAgainst = SECONDARY STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF2B": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaF35C_AA_AIM120
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY 2x_GBU12II_F16CMB50
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF2Kai": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM9X_HOBS_SRAAM_F22A
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY Japan_Weapon_ASM2_F2A
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF4EJKai": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY Japan_Weapon_Sparrow_F4EJ
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY 1x_AGM65F_FA18F
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetX2Shinshin": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM120D_BVR_MRAAM_F22A
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY 2x_GBU24_2000lb_F16CMB50
    PreferredAgainst = SECONDARY STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF16": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM-9X_F16C
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY GBU_31V1_JDAM_F16C
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF18G": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY ALQ_99_RadarJamming
    PreferredAgainst = PRIMARY VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY AGM88G_AARGM-ER
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = TERTIARY AIM9X_HOBS_SRAAM_F22A
    PreferredAgainst = TERTIARY AIRCRAFT
    AutoChooseSources = TERTIARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF35Japon": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM120D_BVR_MRAAM_F35C
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY GBU38_JDAM_F16C
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetEA6B": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY GermanyJetTornadoIDS_WpnBombHvy
    PreferredAgainst = PRIMARY STRUCTURE VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF14Tomcat": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM54A_BVR_AALRM
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY AIM9M_Sidewinder_HSSRAAM
    PreferredAgainst = SECONDARY AIRCRAFT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
}

UH60_WEAPONS = """  WeaponSet
    Conditions = None
    Weapon = PRIMARY 30mm_M230E1_ChainGun
    PreferredAgainst = PRIMARY INFANTRY VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY 70mm_Hydra_AH64E
    PreferredAgainst = SECONDARY STRUCTURE INFANTRY
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = TERTIARY GenericHeliRWR
    PreferredAgainst = TERTIARY AIRCRAFT
    AutoChooseSources = TERTIARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End"""

F35A_OBJECTS = (
    "GermanyJetF35A",
    "ItalyJetF35A",
    "JapanJetF35A",
    "SouthKoreaJetF35A",
    "TurkeyJetF35A",
)

F35B_OBJECTS = (
    "BritainJetF35B",
    "ItalyJetF35B",
    "NatoJetF35B",
    "JapanJetF35B",
    "SouthKoreaJetF35B",
    "AmericaJetF35BJSF",
)


def parse_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
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


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def to_nl(block: str, newline: str) -> str:
    return block.replace("\r\n", "\n").replace("\n", newline).strip("\n") + newline


def named(text: str, kind: str, name: str):
    m = re.search(rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^End\s*$", text)
    return m.group(0) if m else None


def replace_named_block(text: str, kind: str, name: str, replacement: str) -> str:
    pat = rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^End\s*$"
    m = re.search(pat, text)
    if not m:
        raise SystemExit(f"{kind} {name} not found")
    return text[: m.start()] + to_nl(replacement, nl(text)).rstrip() + text[m.end() :]


def replace_weaponset(text: str, block: str) -> str:
    pat = r"(?ms)^[ \t]*WeaponSet\s*\r?\n.*?^[ \t]*End\s*$"
    m = re.search(pat, text)
    if not m:
        raise SystemExit("WeaponSet not found")
    return text[: m.start()] + to_nl(block, nl(text)).rstrip() + text[m.end() :]


def last_object_span(text: str, obj: str):
    hits = list(re.finditer(rf"(?ms)^Object\s+{re.escape(obj)}\s*\r?\n.*?(?=^Object\s|\Z)", text))
    return hits[-1] if hits else None


def patch_object(text: str, obj: str, fn) -> str:
    m = last_object_span(text, obj)
    if not m:
        raise SystemExit(f"Object {obj} not found")
    return text[: m.start()] + fn(m.group(0)) + text[m.end() :]


def set_all_models(text: str, model: str, bone: str) -> str:
    text = re.sub(r"(?m)^(\s*Model\s*=\s*)\S+", rf"\1{model}", text)
    text = re.sub(r"(?m)^(\s*WeaponLaunchBone\s*=\s*\S+\s+)\S+", rf"\1{bone}", text)
    return text


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing source BIGs", file=sys.stderr)
        return 1

    data_entries = parse_big(SRC_DATA)
    art_entries = parse_big(SRC_ART)
    index = {norm(n): i for i, (n, _) in enumerate(data_entries)}
    original_data_names = [n for n, _ in data_entries]
    original_art_names = [n for n, _ in art_entries]
    src_blobs = {norm(n): b for n, b in data_entries}
    src_cs = src_blobs[norm(r"Data\INI\CommandSet.ini")].decode("latin1")
    locked_cs_before = {name: named(src_cs, "CommandSet", name) for name in LOCKED_COMMANDSETS}

    stems = set()
    for n, _ in art_entries:
        base = n.replace("/", "\\").split("\\")[-1]
        if base.lower().endswith(".w3d"):
            stems.add(base[:-4])
    for req in ("AVF-35", "US_F35A", "US_EA18G", "EA6", "JP_X2Shinshin", "LSFIRF14A", "LSFISF15E", "LSFISF15Ed"):
        if req not in stems:
            raise SystemExit(f"required donor stem missing from ART: {req}")

    obj_files = {}
    for n, b in data_entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        for obj in re.findall(r"(?m)^Object\s+(\S+)", t):
            obj_files.setdefault(obj, n)

    def mut(path: str, fn):
        key = norm(path)
        if key in {norm(p) for p in LOCKED_PATHS}:
            raise SystemExit(f"refusing locked path {path}")
        i = index[key]
        name, blob = data_entries[i]
        old = blob.decode("latin1")
        new = fn(old)
        if new == old:
            print("unchanged", path)
            return
        data_entries[i] = (name, new.encode("latin1"))
        print("patched", path, "delta", len(new) - len(blob))

    # F-35A -> dedicated US_F35A donor; F-35B stays AVF-35 JSF
    for obj in F35A_OBJECTS:
        path = obj_files[obj]
        mut(path, lambda t, o=obj: patch_object(t, o, lambda blk: set_all_models(blk, "US_F35A", "WEAPONA01")))
    for obj in F35B_OBJECTS:
        path = obj_files[obj]
        def keep_b(text, o=obj):
            def inner(blk):
                models = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", blk))
                if models - {"AVF-35", "AVF-35_D", "AVF-35_E"}:
                    blk = set_all_models(blk, "AVF-35", "WEAPONA01")
                    blk = re.sub(r"(?m)^(\s*Model\s*=\s*)AVF-35\s*$", r"\1AVF-35", blk)
                if "AmericaF35C_AA_AIM120" not in blk or "AIM9X" not in blk:
                    blk = replace_weaponset(blk, WEAPONSETS["JapanJetF35B"])
                return blk
            return patch_object(text, o, inner)
        mut(path, keep_b)

    # F-15DJ damaged stem case (packed ART is LSFISF15Ed)
    mut(
        obj_files["JapanJetF15DJ"],
        lambda t: patch_object(
            t,
            "JapanJetF15DJ",
            lambda blk: re.sub(r"(?m)^(\s*Model\s*=\s*)LSFISF15ED\s*$", r"\1LSFISF15Ed", blk),
        ),
    )

    for obj, wset in WEAPONSETS.items():
        path = obj_files[obj]
        mut(path, lambda t, o=obj, w=wset: patch_object(t, o, lambda blk: replace_weaponset(blk, w)))

    def patch_ea6b(blk: str) -> str:
        blk = re.sub(r"(?m)^(\s*CommandSet\s*=\s*)\S+", r"\1JapanEA6BBomberCommandSet", blk, count=1)
        return blk

    mut(obj_files["JapanJetEA6B"], lambda t: patch_object(t, "JapanJetEA6B", patch_ea6b))

    def patch_f18g_bones(blk: str) -> str:
        if re.search(r"(?m)^\s*WeaponLaunchBone\s*=\s*TERTIARY\b", blk):
            return blk
        return re.sub(
            r"(?m)^(\s*WeaponLaunchBone\s*=\s*SECONDARY\s+\S+)\s*$",
            r"\1\n      WeaponLaunchBone = TERTIARY WEAPONA01",
            blk,
            count=1,
        )

    mut(obj_files["JapanJetF18G"], lambda t: patch_object(t, "JapanJetF18G", patch_f18g_bones))

    mut(
        obj_files["JapanHelicopterUH60J"],
        lambda t: patch_object(t, "JapanHelicopterUH60J", lambda blk: replace_weaponset(blk, UH60_WEAPONS)),
    )

    def patch_cs(text: str) -> str:
        text = replace_named_block(text, "CommandSet", "Japan_AirfieldCommandSet", FIGHTER_BAR)
        if not named(text, "CommandSet", "JapanEA6BBomberCommandSet"):
            text = text.rstrip("\r\n") + nl(text) + nl(text) + to_nl(EA6B_COMMANDSET, nl(text))
        after = {name: named(text, "CommandSet", name) for name in LOCKED_COMMANDSETS}
        for name, before in locked_cs_before.items():
            if after[name] != before:
                raise SystemExit(f"locked CommandSet mutated: {name}")
        bar = named(text, "CommandSet", "Japan_AirfieldCommandSet")
        if "Command_Sell" in bar or "Command_SetRallyPoint" in bar:
            raise SystemExit("rally/sell still on fighter bar")
        if "Command_ConstructJapanJetF14Tomcat" not in bar.split("14 =")[-1]:
            raise SystemExit("slot 14 is not Tomcat")
        if "E767" in bar:
            raise SystemExit("E-767 still listed")
        return text

    mut(r"Data\INI\CommandSet.ini", patch_cs)

    allowed = {norm(r"Data\INI\CommandSet.ini")}
    for obj in (*F35A_OBJECTS, *F35B_OBJECTS, *WEAPONSETS, "JapanHelicopterUH60J", "JapanJetF15DJ"):
        allowed.add(norm(obj_files[obj]))

    src_index = {norm(n): b for n, b in zip(original_data_names, (b for _, b in parse_big(SRC_DATA)))}
    for n, blob in data_entries:
        key = norm(n)
        if key in {norm(p) for p in LOCKED_PATHS} and key in src_index and blob != src_index[key]:
            raise SystemExit(f"locked file changed {n}")
        if any(s in key for s in ("commandcenter", "vt72b", "playertemplate")) and key in src_index and blob != src_index[key]:
            raise SystemExit(f"faction-chain file changed {n}")
        if key in src_index and blob != src_index[key] and key not in allowed:
            raise SystemExit(f"unexpected DATA mutation {n}")

    if [n for n, _ in data_entries] != original_data_names:
        raise SystemExit("DATA entry order changed")
    if [n for n, _ in art_entries] != original_art_names:
        raise SystemExit("ART entry order changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packed_data = build_big_ordered(data_entries)
    packed_art = build_big_ordered(art_entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(packed_data)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(packed_art)
    print("wrote DATA", len(packed_data), hashlib.sha256(packed_data).hexdigest())
    print("wrote ART", len(packed_art), hashlib.sha256(packed_art).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
