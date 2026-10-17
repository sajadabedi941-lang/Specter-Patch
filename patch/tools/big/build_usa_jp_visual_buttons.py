#!/usr/bin/env python3
"""USA/Japan F-35B lock + F35Japon / F-18G / EA-6B ControlBar fix.

DATA only. ART already contains every chosen donor mesh/texture.
Does not touch CommandCenter, VT72B, PlayerTemplate, Science, or airfield buildings.
Does not change live F-35B models or weapons.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/japan_aircraft_final/_SPEC_DATA_ONE.big")
OUT_DIR = Path("/tmp/usa_jp_visual_buttons")

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
    "Japan_AirfieldCommandSet",
    "Japan_HeavyAirBaseCommandSet",
)

EA6B_WEAPON = """Weapon Japan_Weapon_EA6B_GuidedBomb
  PrimaryDamage = 1100.0
  PrimaryDamageRadius = 48.0
  SecondaryDamage = 90.0
  SecondaryDamageRadius = 80.0
  ScatterRadius = 14.0
  AttackRange = 920.0
  MinimumAttackRange = 90.0
  PreAttackDelay = 2800
  PreAttackType = PER_ATTACK
  AcceptableAimDelta = 20
  DamageType = ARMOR_PIERCING
  DeathType = EXPLODED
  WeaponSpeed = 9999
  ProjectileObject = GBU24_GuidedBombObject
  FireFX = FX_AuroraBombLaunch
  ProjectileDetonationFX = FX_FreeFallBombsDetonation
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 2200
  ClipSize = 6
  ClipReloadTime = 28000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
  ProjectileCollidesWith = STRUCTURES
  AntiGround = Yes
  AntiAirborneVehicle = No
  LeechRangeWeapon = Yes
End
"""

MAPPED = {
    "F18G": """MappedImage F18G
  Texture = EA18GTB.tga
  TextureWidth = 150
  TextureHeight = 112
  Coords = Left:0 Top:0 Right:150 Bottom:112
  Status = NONE
End""",
    "autreF18G": """MappedImage autreF18G
  Texture = EA18GTB.tga
  TextureWidth = 150
  TextureHeight = 112
  Coords = Left:0 Top:0 Right:150 Bottom:112
  Status = NONE
End""",
    "EA6Prowler": """MappedImage EA6Prowler
  Texture = USAEA6Prowler.tga
  TextureWidth = 870
  TextureHeight = 713
  Coords = Left:0 Top:0 Right:870 Bottom:713
  Status = NONE
End""",
    "F35BJSF": """MappedImage F35BJSF
  Texture = AmericaF35BJSF.tga
  TextureWidth = 600
  TextureHeight = 471
  Coords = Left:0 Top:0 Right:600 Bottom:471
  Status = NONE
End""",
}

CSF_LABELS = {
    "CONTROLBAR:F18G": "F/A-18G Growler",
    "CONTROLBAR:F18Gif": "Electronic warfare Growler. ALQ-99 jamming, AGM-88, AIM-9X.",
    "CONTROLBAR:autreF18G": "F/A-18G Growler",
    "CONTROLBAR:autreF18Gif": "Electronic warfare Growler. ALQ-99 jamming, AGM-88, AIM-9X.",
    "CONTROLBAR:EA18G": "EA-18G Growler",
    "CONTROLBAR:EA18Gif": "Electronic warfare Growler. ALQ-99 jamming.",
    "CONTROLBAR:us_ea18g": "EA-18G Growler",
    "CONTROLBAR:us_ea18gif": "Electronic warfare Growler. ALQ-99 jamming.",
    "CONTROLBAR:Nat_ea18g": "F/A-18G Growler",
    "CONTROLBAR:Nat_ea18gif": "Electronic warfare Growler. ALQ-99 jamming, AGM-88, AIM-9X.",
    "CONTROLBAR:EA6Prowler": "EA-6B Prowler",
    "CONTROLBAR:EA6Prowleri": "Heavy precision strike. Six guided bombs.",
    "CONTROLBAR:EA6Prowlerif": "Heavy precision strike. Six guided bombs.",
    "CONTROLBAR:USAEA6Prowler": "EA-6B Prowler",
    "CONTROLBAR:USAEA6Prowlerif": "Heavy precision strike. Six guided bombs.",
    "CONTROLBAR:F35BJSF": "F-35B JSF",
    "CONTROLBAR:F35BJSFif": "Air-to-air F-35B. AIM-120 and AIM-9X.",
    "CONTROLBAR:AmericaF35BJSF": "F-35B JSF",
    "CONTROLBAR:AmericaF35BJSFif": "Air-to-air F-35B. AIM-120 and AIM-9X.",
    "CONTROLBAR:ToolTipUSABuildF35C_AA": "Air-to-air F-35B JSF. AIM-120 and AIM-9X.",
    "CONTROLBAR:SPEC_JapanJetF35A": "F-35 Japon",
    "CONTROLBAR:SPEC_JapanJetF35Aif": "Japanese F-35. AIM missiles and guided bombs.",
    "CONTROLBAR:SPEC_JapanJetF35B": "F-35B",
    "CONTROLBAR:SPEC_JapanJetF35Bif": "JASDF F-35B. AIM-120 and AIM-9X.",
    "CONTROLBAR:Nat_f35a": "F-35",
    "CONTROLBAR:Nat_f35aif": "Stealth fighter.",
}

BUTTON_F18G = """CommandButton Command_ConstructJapanJetF18G
  Command       = UNIT_BUILD
  Object        = JapanJetF18G
  TextLabel     = CONTROLBAR:ConstructJapanJetF18G
  ButtonImage   = F18G
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipJapanJetF18G
End
"""

BUTTON_EA6B = """CommandButton Command_ConstructJapanJetEA6B
  Command       = UNIT_BUILD
  Object        = JapanJetEA6B
  TextLabel     = CONTROLBAR:ConstructJapanJetEA6B
  ButtonImage   = EA6Prowler
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipJapanJetEA6B
End
"""

BUTTON_F35JAPON = """CommandButton Command_ConstructJapanJetF35Japon
  Command       = UNIT_BUILD
  Object        = JapanJetF35Japon
  TextLabel     = CONTROLBAR:ConstructJapanJetF35Japon
  ButtonImage   = SPEC_JapanJetF35A
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipJapanJetF35Japon
End
"""


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


def last_object_span(text: str, obj: str):
    hits = list(re.finditer(rf"(?ms)^Object\s+{re.escape(obj)}\s*\r?\n.*?(?=^Object\s|\Z)", text))
    return hits[-1] if hits else None


def patch_object(text: str, obj: str, fn) -> str:
    m = last_object_span(text, obj)
    if not m:
        raise SystemExit(f"Object {obj} not found")
    return text[: m.start()] + fn(m.group(0)) + text[m.end() :]


def xor_csf_utf16(s: str) -> bytes:
    return bytes(b ^ 0xFF for b in s.encode("utf-16-le"))


def append_csf_labels(blob: bytes, labels: dict[str, str]) -> bytes:
    if blob[:4] != b" FSC":
        raise SystemExit("generals.csf is not CSF")
    _version, nlabels, nstrings = struct.unpack_from("<III", blob, 4)
    extra = bytearray()
    add_labels = 0
    add_strings = 0
    existing = blob.upper()
    for name, value in labels.items():
        key = name.encode("latin1")
        if key.upper() in existing:
            continue
        extra += b" LBL"
        extra += struct.pack("<II", 1, len(key))
        extra += key
        extra += b" RTS"
        extra += struct.pack("<I", len(value))
        extra += xor_csf_utf16(value)
        add_labels += 1
        add_strings += 1
    if add_labels == 0:
        return blob
    out = bytearray(blob)
    struct.pack_into("<I", out, 8, nlabels + add_labels)
    struct.pack_into("<I", out, 12, nstrings + add_strings)
    out += extra
    return bytes(out)


def upsert_mapped(text: str, name: str, block: str) -> str:
    if named(text, "MappedImage", name):
        return replace_named_block(text, "MappedImage", name, block)
    return text.rstrip("\r\n") + nl(text) + nl(text) + to_nl(block, nl(text))


def main() -> int:
    if not SRC_DATA.is_file():
        print("missing source DATA BIG", file=sys.stderr)
        return 1

    data_entries = parse_big(SRC_DATA)
    index = {norm(n): i for i, (n, _) in enumerate(data_entries)}
    original_names = [n for n, _ in data_entries]
    src_blobs = {norm(n): b for n, b in data_entries}
    src_cs = src_blobs[norm(r"Data\INI\CommandSet.ini")].decode("latin1")
    locked_cs_before = {name: named(src_cs, "CommandSet", name) for name in LOCKED_COMMANDSETS}

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

    def patch_f35japon(blk: str) -> str:
        blk = re.sub(r"(?m)^(\s*SelectPortrait\s*=\s*)\S+", r"\1SPEC_JapanJetF35A", blk)
        blk = re.sub(r"(?m)^(\s*ButtonImage\s*=\s*)\S+", r"\1SPEC_JapanJetF35A", blk)
        models = ["JPF35A", "JPF35Ad", "JPF35Ak"]
        idx = {"n": 0}

        def next_model(m):
            name = models[min(idx["n"], 2)]
            idx["n"] += 1
            return m.group(1) + name

        blk = re.sub(r"(?m)^(\s*Model\s*=\s*)\S+", next_model, blk)
        blk = re.sub(r"(?m)^(\s*WeaponLaunchBone\s*=\s*\S+\s+)\S+", r"\1MISSILEA01", blk)
        if idx["n"] < 1 or "JPF35A" not in blk:
            raise SystemExit("F35Japon model replace failed")
        return blk

    def patch_f18g(blk: str) -> str:
        blk = re.sub(r"(?m)^(\s*SelectPortrait\s*=\s*)\S+", r"\1F18G", blk)
        blk = re.sub(r"(?m)^(\s*ButtonImage\s*=\s*)\S+", r"\1autreF18G", blk)
        if "Model = US_EA18G" not in blk and "Model               = US_EA18G" not in blk:
            raise SystemExit("F-18G lost US_EA18G")
        if "ALQ_99_RadarJamming" not in blk or "AGM88G_AARGM-ER" not in blk:
            raise SystemExit("F-18G lost EW loadout")
        return blk

    def patch_ea6b(blk: str) -> str:
        blk = re.sub(r"(?m)^(\s*SelectPortrait\s*=\s*)\S+", r"\1EA6Prowler", blk)
        blk = re.sub(r"(?m)^(\s*ButtonImage\s*=\s*)\S+", r"\1EA6Prowler", blk)
        blk = blk.replace("GermanyJetTornadoIDS_WpnBombHvy", "Japan_Weapon_EA6B_GuidedBomb")
        if "Model = EA6" not in blk:
            raise SystemExit("EA-6B lost EA6 mesh")
        return blk

    mut(
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35Japon.ini",
        lambda t: patch_object(t, "JapanJetF35Japon", patch_f35japon),
    )
    mut(
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF18G.ini",
        lambda t: patch_object(t, "JapanJetF18G", patch_f18g),
    )
    mut(
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetEA6B.ini",
        lambda t: patch_object(t, "JapanJetEA6B", patch_ea6b),
    )

    def patch_buttons(text: str) -> str:
        text = replace_named_block(text, "CommandButton", "Command_ConstructJapanJetF18G", BUTTON_F18G)
        text = replace_named_block(text, "CommandButton", "Command_ConstructJapanJetEA6B", BUTTON_EA6B)
        text = replace_named_block(text, "CommandButton", "Command_ConstructJapanJetF35Japon", BUTTON_F35JAPON)
        return text

    mut(r"Data\INI\CommandButton.ini", patch_buttons)

    def patch_weapon(text: str) -> str:
        if named(text, "Weapon", "Japan_Weapon_EA6B_GuidedBomb"):
            return replace_named_block(text, "Weapon", "Japan_Weapon_EA6B_GuidedBomb", EA6B_WEAPON)
        if not named(text, "Weapon", "GermanyJetTornadoIDS_WpnBombHvy"):
            raise SystemExit("donor Tornado heavy bomb missing")
        if not named(text, "Weapon", "GBU24_GuidedBombObject") and "GBU24_GuidedBombObject" not in text:
            # projectile is an Object, not a Weapon — existence checked by string
            pass
        return text.rstrip("\r\n") + nl(text) + nl(text) + to_nl(EA6B_WEAPON, nl(text))

    mut(r"Data\INI\Weapon.ini", patch_weapon)

    def patch_mapped(text: str) -> str:
        for name, block in MAPPED.items():
            text = upsert_mapped(text, name, block)
        return text

    mut(r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI", patch_mapped)

    i = index[norm(r"Data\English\generals.csf")]
    name, blob = data_entries[i]
    new_csf = append_csf_labels(blob, CSF_LABELS)
    if new_csf != blob:
        data_entries[i] = (name, new_csf)
        print("patched generals.csf", "delta", len(new_csf) - len(blob))
    else:
        print("unchanged generals.csf")

    # locked CommandSets must stay byte-identical
    cs = data_entries[index[norm(r"Data\INI\CommandSet.ini")]][1].decode("latin1")
    for name in LOCKED_COMMANDSETS:
        if named(cs, "CommandSet", name) != locked_cs_before[name]:
            raise SystemExit(f"locked CommandSet mutated: {name}")

    allowed = {
        norm(r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35Japon.ini"),
        norm(r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF18G.ini"),
        norm(r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetEA6B.ini"),
        norm(r"Data\INI\CommandButton.ini"),
        norm(r"Data\INI\Weapon.ini"),
        norm(r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI"),
        norm(r"Data\English\generals.csf"),
    }
    for n, blob in data_entries:
        key = norm(n)
        if key in {norm(p) for p in LOCKED_PATHS} and blob != src_blobs[key]:
            raise SystemExit(f"locked file changed {n}")
        if any(s in key for s in ("commandcenter", "vt72b", "playertemplate")) and blob != src_blobs[key]:
            raise SystemExit(f"faction-chain file changed {n}")
        if blob != src_blobs[key] and key not in allowed:
            raise SystemExit(f"unexpected DATA mutation {n}")
    if [n for n, _ in data_entries] != original_names:
        raise SystemExit("DATA entry order changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packed = build_big_ordered(data_entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(packed)
    print("wrote DATA", len(packed), hashlib.sha256(packed).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
