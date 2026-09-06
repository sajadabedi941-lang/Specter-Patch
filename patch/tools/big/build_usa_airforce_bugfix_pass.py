#!/usr/bin/env python3
"""Surgical USA Air Force final bug-fix pass into packed _SPEC_DATA_ONE.big.

Base: last released USA aircraft DATA (2782 files).
Preserves entry order. Does not rebuild ART. Does not pack overlay CommandSet
as a whole file — C-17 slot edits are applied inside the live packed INI.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/usa_aircraft_final_adj/_SPEC_DATA_ONE.big")
OUT_DIR = Path("/tmp/usa_bugfix_pass")
PATCH = Path("/workspace/patch/Data/INI")

OBJECT_REPLACEMENTS = {
    r"Data\INI\Object\Specter\United States Of America\Drones\AmericaUAVGlobalHawk.ini":
        PATCH / "Object/Specter/United States Of America/Drones/AmericaUAVGlobalHawk.ini",
    r"Data\INI\Object\Specter\United States Of America\AmericaJetV22Visual.ini":
        PATCH / "Object/Specter/United States Of America/AmericaJetV22Visual.ini",
    r"Data\INI\Object\Specter\United States Of America\AmericaJetB21A.ini":
        PATCH / "Object/Specter/United States Of America/AmericaJetB21A.ini",
    r"Data\INI\Object\Specter\United States Of America\AmericaJetC17Visual.ini":
        PATCH / "Object/Specter/United States Of America/AmericaJetC17Visual.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\F35C_AA.ini":
        PATCH / "Object/Specter/United States Of America/Airforce/F35C_AA.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\EA18G.ini":
        PATCH / "Object/Specter/United States Of America/Airforce/EA18G.ini",
    r"Data\INI\Object\Specter\United States Of America\USA_AirForce_WeaponObjects.ini":
        PATCH / "Object/Specter/United States Of America/USA_AirForce_WeaponObjects.ini",
}

B52_WEAPON = """Weapon AmericaB52FifteenBombLineWeapon
  ; Targeted carpet: dummy projectile dies on the clicked point, then
  ; 12x Mk82_B52H spawn in a line centered on that point.
  PrimaryDamage = 1.0
  PrimaryDamageRadius = 1.0
  AttackRange = 800.0
  MinimumAttackRange = 0
  AcceptableAimDelta = 45
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 999999.0
  ProjectileObject = AmericaB52TargetCarpetAnchor
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

V22_WEAPON = """
Weapon AmericaV22_GuidedStandoff
  ; 8 guided stand-off missiles. Clip of 8 with 180ms spacing:
  ; first 4 then remaining 4 on the same attack run. Not carpet bombs.
  PrimaryDamage               = 900.0
  PrimaryDamageRadius         = 45.0
  SecondaryDamage             = 180.0
  SecondaryDamageRadius       = 70.0
  AttackRange                 = 1500
  MinimumAttackRange          = 400.0
  AcceptableAimDelta          = 35
  DamageType                  = ARMOR_PIERCING
  DeathType                   = EXPLODED
  WeaponSpeed                 = 130
  ProjectileObject            = AGM158B2_CruiseMissileObject
  FireSound                   = 30mm_fire2
  ProjectileDetonationFX      = FX_HeavyWarheadCruiseMissileExplosion
  RadiusDamageAffects         = ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots           = 180
  ClipSize                    = 8
  ClipReloadTime              = 45000
  AutoReloadsClip             = RETURN_TO_BASE
  ProjectileCollidesWith      = ENEMIES STRUCTURES WALLS SHRUBBERY
  AntiAirborneVehicle         = No
  AntiGround                  = Yes
  AntiAirborneInfantry        = No
  ShowsAmmoPips               = Yes
  LeechRangeWeapon            = Yes
  ShockWaveAmount             = 80.0
  ShockWaveRadius             = 60.0
  ShockWaveTaperOff           = 0.33
End
"""

B21A_WEAPON = """
Weapon AmericaB21A_HeavyStandoff
  ; One heavy guided stand-off bomb. Not the B-52 carpet weapon.
  PrimaryDamage           = 2200.0
  PrimaryDamageRadius     = 70.0
  SecondaryDamage         = 400.0
  SecondaryDamageRadius   = 110.0
  AttackRange             = 2300
  MinimumAttackRange      = 500
  AcceptableAimDelta      = 50
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 9999999999
  ProjectileObject        = GBU72_GuidedBombObject
  FireFX                  = FX_AuroraBombLaunch
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 0
  ClipSize                = 1
  ClipReloadTime          = 25000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
  AntiGround              = Yes
  AntiAirborneVehicle     = No
  AntiAirborneInfantry    = No
  LeechRangeWeapon        = Yes
  ShockWaveAmount         = 160.0
  ShockWaveRadius         = 80.0
  ShockWaveTaperOff       = 0.33
End
"""

C17_WEAPON = """
Weapon AmericaC17ParaDropWeapon
  ; Marker to the clicked point; OCL starts Star General vehicle paradrop.
  PrimaryDamage = 1.0
  PrimaryDamageRadius = 1.0
  AttackRange = 800.0
  MinimumAttackRange = 80.0
  AcceptableAimDelta = 45
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 999999.0
  ProjectileObject = AmericaC17DropMarker
  FireFX = FX_AuroraBombLaunch
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots = 0
  ClipSize = 1
  ClipReloadTime = 15000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
  AntiGround = Yes
  AntiAirborneVehicle = No
  AntiAirborneInfantry = No
  LeechRangeWeapon = Yes
End
"""

B52_OCL = """
ObjectCreationList OCL_AmericaB52TargetCarpetLine
  CreateObject
    Offset = X:0 Y:-110 Z:90
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:-90 Z:90
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:-70 Z:90
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:-50 Z:90
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:-30 Z:90
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:-10 Z:90
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:10 Z:90
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:30 Z:90
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:50 Z:90
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:70 Z:90
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:90 Z:90
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
  CreateObject
    Offset = X:0 Y:110 Z:90
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
End
"""

C17_OCL = """
ObjectCreationList OCL_AmericaC17TargetParaDrop
  DeliverPayload
    Transport = AmericaJetCargoPlane
    StartAtPreferredHeight = Yes
    StartAtMaxSpeed = Yes
    MaxAttempts = 4
    DropOffset = X:0 Y:0 Z:-10
    DropDelay = 300
    ParachuteDirectly = Yes
    PutInContainer = GenericVehicleParachute
    Payload = AmericaTankCrusader 1
    Payload = AmericaTankM1A2_GC 1
    DeliveryDistance = 150
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

C17_COMMANDSET = """CommandSet C17GlobalMasterCommandSet
  1 = Command_FireMainWeapon
  2 = Command_TransportExit
  3 = Command_TransportExit
  4 = Command_TransportExit
  5 = Command_TransportExit
  6 = Command_TransportExit
  7 = Command_TransportExit
  8 = Command_TransportExit
  9 = Command_TransportExit
  10 = Command_TransportExit
  11 = Command_ChinookUnload
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
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
    return block.replace("\r\n", "\n").replace("\n", newline)


def replace_weapon_block(text: str, weapon_name: str, replacement: str) -> str:
    m = re.search(
        rf"^Weapon {re.escape(weapon_name)}\s*.*?^End\s*",
        text,
        re.S | re.M,
    )
    if not m:
        raise SystemExit(f"{weapon_name} not found")
    return text[: m.start()] + to_nl(replacement, nl(text)) + text[m.end() :]


def append_if_missing(text: str, needle: str, block: str) -> str:
    if needle in text:
        return text
    newline = nl(text)
    return text.rstrip("\r\n") + newline + to_nl(block, newline) + newline


def patch_weapon(text: str) -> str:
    text = replace_weapon_block(text, "AmericaB52FifteenBombLineWeapon", B52_WEAPON)
    text = append_if_missing(text, "Weapon AmericaV22_GuidedStandoff", V22_WEAPON)
    text = append_if_missing(text, "Weapon AmericaB21A_HeavyStandoff", B21A_WEAPON)
    text = append_if_missing(text, "Weapon AmericaC17ParaDropWeapon", C17_WEAPON)
    return text


def patch_ocl(text: str) -> str:
    text = append_if_missing(text, "OCL_AmericaB52TargetCarpetLine", B52_OCL)
    text = append_if_missing(text, "OCL_AmericaC17TargetParaDrop", C17_OCL)
    return text


def patch_commandset(text: str) -> str:
    m = re.search(
        r"CommandSet C17GlobalMasterCommandSet\s*.*?^End",
        text,
        re.S | re.M,
    )
    if not m:
        raise SystemExit("C17GlobalMasterCommandSet not found")
    return text[: m.start()] + to_nl(C17_COMMANDSET, nl(text)).rstrip() + text[m.end() :]


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
