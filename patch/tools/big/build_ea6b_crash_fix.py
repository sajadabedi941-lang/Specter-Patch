#!/usr/bin/env python3
"""Fix USA EA-6B Prowler spawn CTD. Touch only AmericaJetF18Prowler + one new weapon.

Source: latest Saetbyol-fixed packed BIGs.
ART is copied unchanged (EA6.W3D / EA6.tga / USAEA6Prowler already packed).

Root cause:
  AmericaJetF18Prowler used GenericMultiRoleFighter_AG_CommandSet, which
  binds Command_RadioWaveDisabler (SuperweaponRadioWaveDisabler) and
  Command_GMRF_AAM (SpecialAbility_AAMode). Working USA jets on that bar
  (F-35C) implement OCLSpecialPower SuperweaponRadioWaveDisabler.
  The Prowler does not. Command-bar init at produce/spawn null-derefs.

  Second spawn/init hazard: CountermeasuresBehavior FlareBoneBaseName=Flare
  but EA6.W3D has no Flare pivot (EMP_V/EMP_B/ENGINE/WINGTIP/BOMB exist).

Fix:
  - CommandSet = GenericTacticalBomberCommandSet (working A-10C bomber bar)
  - Dedicated Specter_Weapon_EA6B_JH7A2_Bomb ClipSize=6, Fab-250 JH-7A2 chain
  - FlareBoneBaseName = EMP_V
  - NeedsRunway + KeepsParkingSpaceWhenAirborne
  - Keep EA6.W3D / EA6.tga / EA6Prowler cameo
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/saetbyol_crash_fix/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/saetbyol_crash_fix/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/ea6b_crash_fix")

PROWLER_PATH = r"data\ini\object\specter\united states of america\airforce\americajetf18prowler.ini"
WEAPON_PATH = r"data\ini\weapon.ini"

PROWLER_INI = """Object AmericaJetF18Prowler
Scale = 0.9

  SelectPortrait         = EA6Prowler
  ButtonImage            = EA6Prowler

  UpgradeCameo1 = Upgrade_AmericaCountermeasures
  UpgradeCameo2 = Upgrade_MTS

  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes

    DefaultConditionState
      Model               = EA6
      WeaponLaunchBone    = PRIMARY BOMB01
      WeaponLaunchBone    = SECONDARY BOMB02
    End

    ConditionState        = JETEXHAUST
      Model               = EA6
      ParticleSysBone     = ENGINE01 JetLenzflare
      ParticleSysBone     = ENGINE02 JetLenzflare
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
      WeaponLaunchBone    = PRIMARY BOMB01
      WeaponLaunchBone    = SECONDARY BOMB02
    End

    ConditionState        = JETEXHAUST JETAFTERBURNER
      Model               = EA6
      ParticleSysBone     = ENGINE01 JetLenzflare
      ParticleSysBone     = ENGINE02 JetLenzflare
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
      WeaponLaunchBone    = PRIMARY BOMB01
      WeaponLaunchBone    = SECONDARY BOMB02
    End

    ConditionState        = REALLYDAMAGED
      Model               = EA6
      WeaponLaunchBone    = PRIMARY BOMB01
      WeaponLaunchBone    = SECONDARY BOMB02
    End

    ConditionState        = REALLYDAMAGED JETEXHAUST
      Model               = EA6
      ParticleSysBone     = ENGINE01 JetSmoke
      ParticleSysBone     = ENGINE02 JetSmoke
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
      WeaponLaunchBone    = PRIMARY BOMB01
      WeaponLaunchBone    = SECONDARY BOMB02
    End

    ConditionState        = REALLYDAMAGED JETEXHAUST JETAFTERBURNER
      Model               = EA6
      ParticleSysBone     = ENGINE01 JetSmoke
      ParticleSysBone     = ENGINE02 JetSmoke
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
      WeaponLaunchBone    = PRIMARY BOMB01
      WeaponLaunchBone    = SECONDARY BOMB02
    End

    ConditionState        = RUBBLE
      Model               = EA6
    End

    ConditionState        = RUBBLE JETEXHAUST JETAFTERBURNER
      Model               = EA6
    End
  End

  DisplayName           = OBJECT:AmericaJetF18Prowler
  EditorSorting         = VEHICLE
  Side                  = America
  TransportSlotCount    = 0
  VisionRange           = 620.0
  ShroudClearingRange   = 400.0
  Prerequisites
  End
  WeaponSet
    Conditions = None
    Weapon = PRIMARY Specter_Weapon_EA6B_JH7A2_Bomb
    PreferredAgainst = PRIMARY STRUCTURE VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End

  ArmorSet
    Conditions          = None
    Armor               = AirplaneArmor_P
    DamageFX            = None
  End
  ArmorSet
    Conditions          = PLAYER_UPGRADE
    Armor               = CountermeasuresAirplaneArmor_P
    DamageFX            = None
  End

  BuildCost             = 2200
  BuildTime             = 18.0
  ExperienceValue       = 80 80 160 240
  ExperienceRequired    = 0 150 250 500
  IsTrainable           = Yes
  CrusherLevel          = 1
  CrushableLevel        = 2
  CommandSet            = GenericTacticalBomberCommandSet

  VoiceSelect           = RaptorVoiceSelect
  VoiceMove             = RaptorVoiceMove
  VoiceAttack           = RaptorVoiceAttack
  VoiceAttackAir        = RaptorVoiceAttackAir
  VoiceGuard            = RaptorVoiceAirPatrol
  SoundAmbient          = RaptorAmbientLoop
  SoundAmbientRubble    = NoSound
  UnitSpecificSounds
    VoiceCreate         = RaptorVoiceCreate
    SoundEject          = PilotSoundEject
    VoiceEject          = PilotVoiceEject
    Afterburner         = RaptorAfterburner
    VoiceLowFuel        = RaptorVoiceLowFuel
    VoiceGarrison       = RaptorVoiceMove
  End

  RadarPriority         = UNIT
  KindOf                = PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT
  Body                  = ActiveBody ModuleTag_02
    MaxHealth           = 560.0
    InitialHealth       = 560.0
  End

  Behavior              = JetSlowDeathBehavior ModuleTag_03
    FXOnGroundDeath                 = FX_JetOnGroundDeath
    OCLOnGroundDeath                = OCL_RaptorDeathFinalBlowUp
    DestructionDelay                = 99999999
    RollRate                        = 0.2
    RollRateDelta                   = 100%
    PitchRate                       = 0.0
    FallHowFast                     = 110.0%
    FXInitialDeath                  = FX_RaptorDeathInitial
    OCLInitialDeath                 = OCL_RaptorDeathInitial
    DelaySecondaryFromInitialDeath  = 500
    FXSecondary                     = FX_JetDeathSecondary
    OCLSecondary                    = OCL_RaptorDeathSecondary
    FXHitGround                     = FX_JetDeathHitGround
    OCLHitGround                    = OCL_RaptorDeathHitGround
    DelayFinalBlowUpFromHitGround   = 200
    FXFinalBlowUp                   = FX_JetDeathFinalBlowUp
    OCLFinalBlowUp                  = OCL_RaptorDeathFinalBlowUp
  End
  Behavior              = EjectPilotDie ModuleTag_04
    GroundCreationList  = OCL_EjectPilotOnGround
    AirCreationList     = OCL_EjectPilotViaParachute
    ExemptStatus        = HIJACKED
    VeterancyLevels     = ALL -REGULAR
  End
  Behavior              = PhysicsBehavior ModuleTag_05
    Mass                = 500.0
  End
  Behavior              = JetAIUpdate ModuleTag_06
    OutOfAmmoDamagePerSecond = 10%
    TakeoffDistForMaxLift    = 0%
    TakeoffPause             = 500
    MinHeight                = 6
    ParkingOffset            = 3
    ReturnToBaseIdleTime     = 10000
    NeedsRunway              = Yes
    KeepsParkingSpaceWhenAirborne = Yes
  End
  Locomotor             = SET_NORMAL General_Electric_F414
  Locomotor             = SET_TAXIING BasicJetTaxiLocomotor

  Behavior              = ExperienceScalarUpgrade ModuleTag_08
    TriggeredBy         = Upgrade_AmericaAdvancedTraining
    AddXPScalar         = 1.0
  End
  Behavior              = ArmorUpgrade ModuleTag_Armor01
    TriggeredBy         = Upgrade_AmericaCountermeasures
  End
  Behavior              = CountermeasuresBehavior ModuleTag_10
    TriggeredBy         = Upgrade_AmericaCountermeasures
    FlareTemplateName   = CountermeasureFlare
    FlareBoneBaseName   = EMP_V
    VolleySize          = 2
    VolleyArcAngle      = 90.0
    VolleyVelocityFactor = 4.0
    DelayBetweenVolleys = 180
    NumberOfVolleys     = 3
    ReloadTime          = 1600
    EvasionRate         = 50%
    ReactionLaunchLatency = 0
    MissileDecoyDelay   = 50
  End
  Behavior              = FlammableUpdate ModuleTag_21
    AflameDuration      = 5000
    AflameDamageAmount  = 3
    AflameDamageDelay   = 500
  End
  Behavior              = CreateObjectDie ModuleTag_Deletion
    DeathTypes          = NONE +EXTRA_6
    CreationList        = None
  End
  Behavior              = TransitionDamageFX ModuleTag_22
    ReallyDamagedParticleSystem1 = Bone:ENGINE01 RandomBone:No Psys:SmokeSmallContinuous01
    ReallyDamagedFXList1         = Loc: X:0 Y:0 Z:0 FXList:FX_MIGDamageTransition
  End

  Geometry              = Box
  GeometryIsSmall       = Yes
  GeometryMajorRadius   = 14.0
  GeometryMinorRadius   = 7.0
  GeometryHeight        = 5.0
  Shadow                = SHADOW_VOLUME
  ShadowSizeX           = 89
End
"""

EA6B_WEAPON = """Weapon Specter_Weapon_EA6B_JH7A2_Bomb
  PrimaryDamage           = 850
  PrimaryDamageRadius     = 48.0
  SecondaryDamage         = 100.0
  SecondaryDamageRadius   = 50.0
  ScatterRadius           = 80.0
  AttackRange             = 550.0
  AcceptableAimDelta      = 45
  DamageType              = EXPLOSION
  DeathType               = BURNED
  WeaponSpeed             = 9999
  ProjectileObject        = Fab-250
  FireFX                  = FX_AuroraBombLaunch
  ProjectileDetonationFX  = FX_ThermobaricWarheadExplosion
  ProjectileDetonationOCL = OCL_ThermobaricFire
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 1
  ClipSize                = 6
  ClipReloadTime          = 13000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
  AntiGround              = Yes
  AntiAirborneVehicle     = No
End
"""

BLOCK_OPEN = re.compile(
    r"(?i)^\s*(Object(?:Reskin)?\s+\S+|Draw\s*=|DefaultConditionState\b|"
    r"ConditionState\s*=|Behavior\s*=|Body\s*=|ArmorSet\b|WeaponSet\b|"
    r"UnitSpecificSounds\b|Prerequisites\b|Weapon\s+(?![=])\S+)"
)

LOCKED_OBJECTS = {
    "AmericaJetF35A",
    "AmericaJetF35B",
    "AmericaJetF35C",
    "AmericaJetF35C_AA",
    "AmericaJetF35BJSF",
    "AmericaJetEA18",
    "AmericaJetAuterF22",
    "AmericaJetRaptor",
    "AmericaJetB52H",
    "AmericaJetC17Visual",
    "NorthKoreaUAVSaetbyol",
}


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


def encode_ini(text: str) -> bytes:
    return text.replace("\n", "\r\n").encode("latin1")


def validate_ini(text: str) -> list[str]:
    errors = []
    depth = 0
    stack = []
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.split(";", 1)[0].rstrip()
        if not line.strip():
            continue
        if re.match(r"(?i)^\s*End\b", line):
            if depth <= 0:
                errors.append(f"line {i}: extra End")
            else:
                depth -= 1
                stack.pop()
            continue
        if BLOCK_OPEN.match(line):
            depth += 1
            stack.append((i, line.strip()[:60]))
            continue
        if "=" not in line and not re.match(r"(?i)^\s*(Object|Weapon|End)\b", line):
            errors.append(f"line {i}: not a key=value or block: {line.strip()[:80]}")
    if depth != 0:
        errors.append(f"unclosed blocks depth={depth} last={stack[-1:]}")
    return errors


def upsert_weapon(weapon_text: str) -> str:
    if re.search(r"(?im)^Weapon\s+Specter_Weapon_EA6B_JH7A2_Bomb\b", weapon_text):
        weapon_text = re.sub(
            r"(?ims)^Weapon\s+Specter_Weapon_EA6B_JH7A2_Bomb\b.*?^End\s*$",
            EA6B_WEAPON.strip(),
            weapon_text,
            count=1,
        )
        return weapon_text
    nl = "\r\n" if "\r\n" in weapon_text else "\n"
    return weapon_text.rstrip() + nl + nl + EA6B_WEAPON.replace("\n", nl)


def last_block(kind: str, name: str, texts: list[str]) -> str | None:
    found = None
    pat = re.compile(rf"(?im)^{kind}\s+{re.escape(name)}\b")
    for text in texts:
        for m in pat.finditer(text):
            start = m.start()
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
            found = "".join(buf)
    return found


def w3d_pivots_and_textures(blob: bytes):
    pivots = []
    textures = []

    def walk(data: bytes):
        off = 0
        while off + 8 <= len(data):
            ctype, csize = struct.unpack_from("<II", data, off)
            payload = csize & 0x7FFFFFFF
            body = data[off + 8 : off + 8 + payload]
            if ctype == 0x00000102:  # PIVOTS
                for i in range(0, len(body), 60):
                    rec = body[i : i + 60]
                    if len(rec) < 16:
                        break
                    pivots.append(rec[:16].split(b"\x00", 1)[0].decode("latin1", errors="replace"))
            elif ctype == 0x00000032:  # TEXTURE_NAME
                name = body.split(b"\x00", 1)[0].decode("latin1", errors="replace")
                if name:
                    textures.append(name)
            if ctype in (0x00000100, 0x00000000, 0x00000030, 0x00000031) or (csize & 0x80000000):
                walk(body)
            off = off + 8 + payload

    walk(blob)
    return pivots, textures


def main() -> int:
    obj_err = validate_ini(PROWLER_INI)
    wpn_err = validate_ini(EA6B_WEAPON)
    print("=== INI PARSER ===")
    if obj_err or wpn_err:
        for e in obj_err:
            print(" FAIL object", e)
        for e in wpn_err:
            print(" FAIL weapon", e)
        return 1
    print("INI_PARSE_OK")

    required = [
        "Object AmericaJetF18Prowler",
        "Model               = EA6",
        "Specter_Weapon_EA6B_JH7A2_Bomb",
        "GenericTacticalBomberCommandSet",
        "FlareBoneBaseName   = EMP_V",
        "NeedsRunway              = Yes",
        "KeepsParkingSpaceWhenAirborne = Yes",
        "SelectPortrait         = EA6Prowler",
    ]
    forbidden = [
        "GenericMultiRoleFighter_AG_CommandSet",
        "Command_RadioWaveDisabler",
        "SuperweaponRadioWaveDisabler",
        "SpecialAbility_AAMode",
        "FlareBoneBaseName   = Flare",
        "AmF18A",
        "F18SEA",
        "AVF-35",
    ]
    for tok in required:
        if tok not in PROWLER_INI:
            print("FAIL missing", tok)
            return 1
    for tok in forbidden:
        if tok in PROWLER_INI:
            print("FAIL forbidden", tok)
            return 1
    if "ClipSize                = 6" not in EA6B_WEAPON:
        print("FAIL ClipSize")
        return 1

    data_entries = parse_big(SRC_DATA)
    art_entries = parse_big(SRC_ART)
    out_data = []
    changed = []
    found_obj = found_wpn = False
    for n, b in data_entries:
        key = n.replace("/", "\\").lower()
        if key == PROWLER_PATH:
            nb = encode_ini(PROWLER_INI)
            out_data.append((n, nb))
            changed.append((n, len(b), len(nb)))
            found_obj = True
        elif key == WEAPON_PATH:
            text = b.decode("latin1")
            new = upsert_weapon(text)
            nb = new.encode("latin1")
            out_data.append((n, nb))
            changed.append((n, len(b), len(nb)))
            found_wpn = True
        else:
            out_data.append((n, b))
    if not found_obj or not found_wpn:
        print("TARGET MISSING", found_obj, found_wpn)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(out_data)
    art_big = SRC_ART.read_bytes()  # byte-identical ART
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_big)
    dsha = hashlib.sha256(data_big).hexdigest()
    asha = hashlib.sha256(art_big).hexdigest()
    print("changed:")
    for n, old, new in changed:
        print(f"  {n} {old} -> {new}")
    print("DATA", dsha, len(data_big))
    print("ART ", asha, len(art_big), "(unchanged bytes)")

    # Re-extract and audit
    packed = parse_big(OUT_DIR / "_SPEC_DATA_ONE.big")
    packed_art = parse_big(OUT_DIR / "_SPEC_ART_ONE.big")
    if [n for n, _ in packed] != [n for n, _ in data_entries]:
        print("FAIL entry order changed")
        return 1
    src_map = {n.replace("/", "\\").lower(): b for n, b in data_entries}
    new_map = {n.replace("/", "\\").lower(): (n, b) for n, b in packed}
    diffs = []
    for k, (n, b) in new_map.items():
        if src_map.get(k) != b:
            diffs.append(n)
    print("DATA diffs:", diffs)
    allowed = {
        r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaJetF18Prowler.ini",
        r"Data\INI\Weapon.ini",
    }
    unexpected = [n for n in diffs if n not in allowed]
    if unexpected:
        print("FAIL unexpected diffs", unexpected)
        return 1

    texts = [b.decode("latin1", errors="ignore") for _, b in packed]
    prowler = None
    for n, b in packed:
        if n.replace("/", "\\").lower() == PROWLER_PATH:
            prowler = b.decode("latin1").replace("\r\n", "\n")
            (OUT_DIR / "AmericaJetF18Prowler.ini").write_text(prowler)
    if "Object AmericaJetF18Prowler" not in prowler:
        print("FAIL packed object")
        return 1
    if prowler.count("Object AmericaJetF18Prowler") != 1:
        print("FAIL duplicate object in file")
        return 1
    if last_block("Object", "AmericaJetF18Prowler", texts).count("Object AmericaJetF18Prowler") < 1:
        print("FAIL last-wins object missing")
        return 1
    # only one definition across DATA
    hits = []
    for n, b in packed:
        t = b.decode("latin1", errors="ignore")
        if re.search(r"(?im)^Object(?:Reskin)?\s+AmericaJetF18Prowler\b", t):
            hits.append(n)
    print("AmericaJetF18Prowler defs:", hits)
    if hits != [r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaJetF18Prowler.ini"]:
        print("FAIL unexpected object locations")
        return 1

    wblk = last_block("Weapon", "Specter_Weapon_EA6B_JH7A2_Bomb", texts)
    if not wblk or "ClipSize                = 6" not in wblk or "ProjectileObject        = Fab-250" not in wblk:
        print("FAIL weapon block", wblk)
        return 1
    if last_block("Object", "Fab-250", texts) is None:
        print("FAIL Fab-250 missing")
        return 1
    for kind, name in [
        ("ObjectCreationList", "OCL_ThermobaricFire"),
        ("FXList", "FX_AuroraBombLaunch"),
        ("FXList", "FX_ThermobaricWarheadExplosion"),
        ("Armor", "AirplaneArmor_P"),
        ("Locomotor", "General_Electric_F414"),
        ("Locomotor", "BasicJetTaxiLocomotor"),
        ("CommandSet", "GenericTacticalBomberCommandSet"),
        ("CommandButton", "Command_ConstructAmericaJetF18Prowler"),
        ("Object", "CountermeasureFlare"),
    ]:
        if last_block(kind, name, texts) is None:
            print("FAIL missing", kind, name)
            return 1

    cb = next(b.decode("latin1") for n, b in packed if n.replace("/", "\\").lower().endswith("commandbutton.ini") and "default" not in n.lower())
    m = re.search(
        r"(?ims)^CommandButton\s+Command_ConstructAmericaJetF18Prowler\b.*?^End\s*$",
        cb,
    )
    if not m or "Object        = AmericaJetF18Prowler" not in m.group(0):
        print("FAIL construct button", m.group(0) if m else None)
        return 1
    if "ButtonImage   = EA6Prowler" not in m.group(0):
        print("FAIL button image")
        return 1

    # locked objects unchanged
    for n, b in packed:
        t = b.decode("latin1", errors="ignore")
        for obj in LOCKED_OBJECTS:
            if re.search(rf"(?im)^Object(?:Reskin)?\s+{obj}\b", t):
                old = src_map[n.replace("/", "\\").lower()]
                if old != b:
                    print("FAIL locked object file changed", obj, n)
                    return 1

    art_base = {}
    art_blob = {}
    for n, b in packed_art:
        art_base.setdefault(Path(n.replace("\\", "/")).name.lower(), n)
        art_blob[n.replace("/", "\\").lower()] = b
    ea6 = art_blob.get(r"art\w3d\ea6.w3d")
    if not ea6:
        print("FAIL EA6.W3D missing")
        return 1
    pivots, textures = w3d_pivots_and_textures(ea6)
    print("EA6 pivots", pivots)
    print("EA6 textures", sorted(set(textures)))
    for tex in set(textures):
        base = Path(tex.replace("\\", "/")).name.lower()
        if base not in art_base:
            print("FAIL missing W3D texture", tex)
            return 1
    for req in ("ea6.w3d", "ea6.tga", "usaea6prowler.tga", "usaea6prowlertb.tga"):
        if req not in art_base:
            print("FAIL missing ART", req)
            return 1
    if "Flare" in pivots:
        print("NOTE Flare pivot exists")
    if "EMP_V" not in pivots:
        print("FAIL EMP_V missing on EA6")
        return 1

    (OUT_DIR / "SHA256.txt").write_text(f"DATA {dsha}\nART  {asha}\n")
    (OUT_DIR / "INI_PARSE.txt").write_text("INI_PARSE_OK\nDEPENDENCY_WALK_OK\n")
    print("DEPENDENCY_WALK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
