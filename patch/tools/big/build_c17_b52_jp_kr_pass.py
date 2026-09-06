#!/usr/bin/env python3
"""C-17 parachute drop, B-52H heavy-bomb replace, JP/SK aircraft unbuildable.

Source of truth: latest packed DATA (F22A_AG parse fix). Surgical inject only.
Does not overwrite stock Weapon/CommandSet/CommandButton as whole files.
Does not touch Tu-95 / H-20 carpet objects that still use the old B-52 line weapon.
Does not edit other USA aircraft.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/usa_f22a_ag_parse_fix/_SPEC_DATA_ONE.big")
OUT_DIR = Path("/tmp/c17_b52_jp_kr_pass")
PATCH = Path("/workspace/patch/Data/INI")

OBJECT_REPLACEMENTS = {
    r"Data\INI\Object\Specter\United States Of America\AmericaJetC17Visual.ini":
        PATCH / "Object/Specter/United States Of America/AmericaJetC17Visual.ini",
    r"Data\INI\Object\Specter\United States Of America\USA_AirForce_WeaponObjects.ini":
        PATCH / "Object/Specter/United States Of America/USA_AirForce_WeaponObjects.ini",
}

C17_COMMANDSET = """
CommandSet AmericaC17StarlifterCommandSet
  1 = Command_AmericaC17ParaDrop
  13 = Command_Guard
  14 = Command_Stop
End
"""

C17_OCL = """
ObjectCreationList OCL_AmericaC17TargetParaDrop
  DeliverPayload
    Transport = AmericaJetC17ParaDropTransport
    StartAtPreferredHeight = Yes
    StartAtMaxSpeed = No
    MaxAttempts = 4
    DropOffset = X:0 Y:0 Z:-10
    DropDelay = 400
    ParachuteDirectly = Yes
    PutInContainer = GenericVehicleParachute
    Payload = AmericaTankCrusader 1
    Payload = AmericaTankM1A2_GC 1
    DeliveryDistance = 0
    PreOpenDistance = 300
    DeliveryDecalRadius = 150
    DeliveryDecal
      Texture           = SCCParadrop_USA
      Style             = SHADOW_ALPHA_DECAL
      OpacityMin        = 25%
      OpacityMax        = 50%
      OpacityThrobTime  = 500
      Color             = R:227 G:229 B:22 A:255
      OnlyVisibleToOwningPlayer = Yes
    End
  End
End
"""

B52_OCL = """
ObjectCreationList OCL_AmericaB52H_HeavyBombDrop
  CreateObject
    Offset = X:0 Y:0 Z:-20
    ObjectNames = AmericaB52H_HeavyBomb
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 12
  End
End
"""

B52_WEAPON = """
Weapon AmericaB52H_HeavyBombDrop
  PrimaryDamage = 1.0
  PrimaryDamageRadius = 1.0
  AttackRange = 350.0
  MinimumAttackRange = 0
  AcceptableAimDelta = 45
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 999999.0
  ProjectileObject = NONE
  FireOCL = OCL_AmericaB52H_HeavyBombDrop
  FireFX = FX_AuroraBombLaunch
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 0
  ClipSize = 1
  ClipReloadTime = 600000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
  AntiGround = Yes
  AntiAirborneVehicle = No
  AntiAirborneInfantry = No
  LeechRangeWeapon = Yes
End
"""

B52_DETONATION = """
Weapon AmericaB52H_HeavyBombDetonation
  PrimaryDamage = 900.0
  PrimaryDamageRadius = 140.0
  SecondaryDamage = 400.0
  SecondaryDamageRadius = 200.0
  AttackRange = 100.0
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 99999.0
  ProjectileObject = NONE
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 0
  ClipSize = 1
  ClipReloadTime = 0
  AutoReloadsClip = No
  ProjectileCollidesWith = STRUCTURES
  ShockWaveAmount = 180.0
  ShockWaveRadius = 120.0
  ShockWaveTaperOff = 0.33
End
"""

JAPAN_AIRFIELD = """
CommandSet Japan_AirfieldCommandSet
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

JAPAN_HEAVY = """
CommandSet Japan_HeavyAirBaseCommandSet
  1 = Command_UpgradeJapan_AircraftWeapons
  2 = Command_UpgradeJapan_AircraftCountermeasures
  3 = Command_UpgradeJapan_F35Integration
  4 = Command_UpgradeJapan_PrecisionStrike
  5 = Command_UpgradeJapan_DoctrineAirSuperiority
  6 = Command_UpgradeJapan_DoctrinePrecisionStrike
  7 = Command_UpgradeJapan_TechPrecisionDefense
  8 = Command_UpgradeJapan_TechRadarNetwork
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

SK_AIRFIELD = """
CommandSet SouthKorea_AirfieldCommandSet
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

SK_HEAVY = """
CommandSet SouthKorea_HeavyAirBaseCommandSet
  1 = Command_UpgradeSouthKorea_AircraftWeapons
  2 = Command_UpgradeSouthKorea_AircraftCountermeasures
  3 = Command_UpgradeSouthKorea_F15KUpgrade
  4 = Command_UpgradeSouthKorea_KFDefense
  5 = Command_UpgradeSouthKorea_DoctrineAirSuperiority
  6 = Command_UpgradeSouthKorea_TechAirDominanceK
  13 = Command_SetRallyPoint
  14 = Command_Sell
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


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded = []
    for name, blob in entries:
        nb = name.encode("latin1")
        encoded.append((nb, blob))
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


def replace_named_block(text: str, kind: str, name: str, replacement: str) -> str:
    pat = rf"(?ms)^{kind}\s+{re.escape(name)}\s*\n.*?^End\s*$"
    m = re.search(pat, text)
    if not m:
        raise SystemExit(f"{kind} {name} not found")
    return text[: m.start()] + to_nl(replacement, nl(text)).rstrip() + text[m.end() :]


def append_if_missing(text: str, needle: str, block: str) -> str:
    if needle in text:
        return text
    newline = nl(text)
    return text.rstrip("\r\n") + newline + newline + to_nl(block, newline)


def patch_weapon(text: str) -> str:
    text = append_if_missing(text, "Weapon AmericaB52H_HeavyBombDetonation", B52_DETONATION)
    text = append_if_missing(text, "Weapon AmericaB52H_HeavyBombDrop", B52_WEAPON)
    return text


def patch_ocl(text: str) -> str:
    text = replace_named_block(
        text, "ObjectCreationList", "OCL_AmericaC17TargetParaDrop", C17_OCL
    )
    text = append_if_missing(text, "OCL_AmericaB52H_HeavyBombDrop", B52_OCL)
    return text


def patch_commandset(text: str) -> str:
    text = replace_named_block(
        text, "CommandSet", "AmericaC17StarlifterCommandSet", C17_COMMANDSET
    )
    text = replace_named_block(text, "CommandSet", "Japan_AirfieldCommandSet", JAPAN_AIRFIELD)
    text = replace_named_block(
        text, "CommandSet", "Japan_HeavyAirBaseCommandSet", JAPAN_HEAVY
    )
    text = replace_named_block(
        text, "CommandSet", "SouthKorea_AirfieldCommandSet", SK_AIRFIELD
    )
    text = replace_named_block(
        text, "CommandSet", "SouthKorea_HeavyAirBaseCommandSet", SK_HEAVY
    )
    return text


def patch_b52h_object(text: str) -> str:
    new, n = re.subn(
        r"(Object AmericaJetB52H\b[\s\S]*?WeaponSet\s*\r?\n\s*Conditions = None\r?\n\s*Weapon = PRIMARY )AmericaB52FifteenBombLineWeapon",
        r"\1AmericaB52H_HeavyBombDrop",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("AmericaJetB52H WeaponSet not retargeted")
    if "AmericaB52FifteenBombLineWeapon" in new[new.find("Object AmericaJetB52H") : new.find("Object AmericaJetB52H") + 2500]:
        raise SystemExit("AmericaJetB52H still references old carpet weapon")
    return new


def disable_airforce_objects(entries: list[tuple[str, bytes]]) -> int:
    """Buildable = No on Japan / South Korea aircraft INIs only."""
    air_dirs = (
        r"data\ini\object\specter\japan self-defense forces\airforce" + "\\",
        r"data\ini\object\specter\republic of korea armed forces\airforce" + "\\",
        r"data\ini\object\specter\south korean armed forces\airforce" + "\\",
    )
    changed = 0
    for i, (name, blob) in enumerate(entries):
        key = norm(name)
        if not key.endswith(".ini") or not any(key.startswith(d) for d in air_dirs):
            continue
        text = blob.decode("latin1")
        newline = nl(text)

        def add_buildable(m: re.Match[str]) -> str:
            header = m.group(0)
            # Object line plus following blank/scale lines until we can insert.
            return header + f"{newline}  Buildable = No"

        new = text
        if re.search(r"(?m)^\s*Buildable\s*=", new):
            new = re.sub(
                r"(?m)^(\s*Buildable\s*=\s*)\S+",
                r"\1No",
                new,
            )
        else:
            new, n = re.subn(
                r"(?m)^Object\s+\S+[ \t]*\r?\n",
                add_buildable,
                new,
            )
            if n < 1:
                raise SystemExit(f"no Object in {name}")
        if new != text:
            entries[i] = (name, new.encode("latin1"))
            changed += 1
            print("unbuildable", name)
    return changed


def main() -> int:
    if not SRC_DATA.is_file():
        print("missing source DATA BIG", SRC_DATA, file=sys.stderr)
        return 1
    entries = parse_big(SRC_DATA)
    index = {norm(n): i for i, (n, _) in enumerate(entries)}
    original_count = len(entries)
    original_names = [n for n, _ in entries]

    for big_name, src in OBJECT_REPLACEMENTS.items():
        key = norm(big_name)
        if key not in index:
            raise SystemExit(f"missing packed file {big_name}")
        if not src.is_file():
            raise SystemExit(f"missing overlay {src}")
        entries[index[key]] = (entries[index[key]][0], src.read_bytes())
        print("replaced", big_name, "bytes", len(entries[index[key]][1]))

    def mut(path: str, fn):
        key = norm(path)
        i = index[key]
        name, blob = entries[i]
        text = blob.decode("latin1")
        new = fn(text)
        if new == text:
            raise SystemExit(f"no change applied to {path}")
        entries[i] = (name, new.encode("latin1"))
        print("patched", path, "delta", len(new) - len(text))

    mut(r"Data\INI\Weapon.ini", patch_weapon)
    mut(r"Data\INI\ObjectCreationList.ini", patch_ocl)
    mut(r"Data\INI\CommandSet.ini", patch_commandset)
    mut(
        r"Data\INI\Object\Specter\United States Of America\USA_System.ini",
        patch_b52h_object,
    )
    n_air = disable_airforce_objects(entries)
    print("airforce objects unbuildable files", n_air)

    if len(entries) < original_count:
        raise SystemExit("entry count shrank")
    if [n for n, _ in entries][:original_count] != original_names:
        raise SystemExit("original entry order changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_big = OUT_DIR / "_SPEC_DATA_ONE.big"
    packed = build_big_ordered(entries)
    out_big.write_bytes(packed)
    sha = hashlib.sha256(packed).hexdigest()
    print("wrote", out_big, "size", len(packed), "files", len(entries), "sha", sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
