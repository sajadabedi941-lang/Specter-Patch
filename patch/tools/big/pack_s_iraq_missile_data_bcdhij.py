#!/usr/bin/env python3
"""Activate Iraq factory missiles B/C/D/H/I/J in DATA, keep dedicated ART skins.

Live DATA baseline: SPECTER_IRAQ_ALFAHD500_STATS
Live ART baseline:  SPECTER_IRAQ_MISSILE_SKINS_BCDHIJ (identity rebuild)

Does not modify MOTHER / Iraq_R11ScudB / 9P117 gameplay or ART.
Does not modify Iraq_AlFahd500 gameplay, launcher ART, or launch animation.
Only Al-Fahd UI change: Persian tooltip -> English.
Does not wire E/F/G/K/L.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD500_STATS/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_SKINS_BCDHIJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_DATA_BCDHIJ"
SRC_DIR = ROOT / "patch/Data/INI"

BASE_DATA_SHA = "a8b7af7354d2887ac43b9a0a498771828689d19f747da71ff5dd0895afc07256"
BASE_DATA_SIZE = 366379397
BASE_ART_SHA = "e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4"
BASE_ART_SIZE = 1292294758

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CSF_KEY = r"Data\English\generals.csf"
UNIT_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
PROJ_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
WEP_A_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlFahd500.ini"
WEP_NEW_KEY = r"Data\INI\Weapon\Weapon_Iraq_FactoryMissiles.ini"
UPG_KEY = r"Data\INI\Upgrade_IraqFactoryMissiles.ini"

OLD_SET = (
    "CommandSet Iraq_AlFahdMissileFactoryCommandSet\r\n"
    "  1  = CB_MISSILE_A\r\n"
    "  ; 2-12 reserved for CB_MISSILE_B .. CB_MISSILE_L once each has a real Object.\r\n"
    "  ; UNIT_BUILD with a null Object is unsafe to show on the factory bar.\r\n"
    "  13 = Command_SetRallyPoint\r\n"
    "  14 = Command_Sell\r\n"
    "End"
)
NEW_SET = (
    "CommandSet Iraq_AlFahdMissileFactoryCommandSet\r\n"
    "  1  = CB_MISSILE_A\r\n"
    "  2  = CB_MISSILE_B\r\n"
    "  3  = CB_MISSILE_C\r\n"
    "  4  = CB_MISSILE_D\r\n"
    "  ; 5-7 reserved (E/F/G skins not specified)\r\n"
    "  8  = CB_MISSILE_H\r\n"
    "  9  = CB_MISSILE_I\r\n"
    "  10 = CB_MISSILE_J\r\n"
    "  ; 11-12 reserved (K/L not activated)\r\n"
    "  13 = Command_SetRallyPoint\r\n"
    "  14 = Command_Sell\r\n"
    "End"
)

# MOTHER scale: 1000 km -> AttackRange 1720; 400 kg -> 2000 + death 2200;
# accuracy 10/100 -> ScatterRadius 175; stealth 5/100 -> HP 400, on radar.
MOTHER_RANGE = 1720.0
MOTHER_KG = 400
MOTHER_DMG = 2000.0
MOTHER_DEATH = 2200
MOTHER_ACC = 10
MOTHER_SCATTER = 175
MOTHER_STEALTH = 5
MOTHER_HP = 400.0

ALFAHD_TOOLTIP = (
    "Al-Fahd500\n"
    "Range: 1000 km\n"
    "Warhead: 1600 kg\n"
    "Point Accuracy: 10/100\n"
    "Radar Stealth: 20/100\n"
    "Rebuild Time: 30 sec\n"
    "Price: $2200"
)

MISSILES = [
    {
        "slot": "B",
        "object": "Iraq_AlHusseinII",
        "name": "Al-Hussein II",
        "model": "Irq_AlHussein2M",
        "tex": "Irq_AlHussein2P.tga",
        "hier": b"IRQ_AH2_M",
        "cameo": "specter_missile_b",
        "km": 1200,
        "kg": 800,
        "acc": 20,
        "stealth": 10,
        "rebuild": 25,
        "price": 1800,
    },
    {
        "slot": "C",
        "object": "Iraq_AlSamoudII",
        "name": "Al-Samoud II",
        "model": "Irq_AlSamoud2M",
        "tex": "Irq_AlSamoud2P.tga",
        "hier": b"IRQ_AS2_M",
        "cameo": "specter_missile_c",
        "km": 1400,
        "kg": 600,
        "acc": 40,
        "stealth": 30,
        "rebuild": 22,
        "price": 1700,
    },
    {
        "slot": "D",
        "object": "Iraq_AlAbbas",
        "name": "Al-Abbas",
        "model": "Irq_AlAbbas2M",
        "tex": "Irq_AlAbbas2P.tga",
        "hier": b"IRQ_AAB_M",
        "cameo": "specter_missile_d",
        "km": 1600,
        "kg": 1200,
        "acc": 25,
        "stealth": 15,
        "rebuild": 35,
        "price": 2600,
    },
    {
        "slot": "H",
        "object": "Iraq_AlBasrah",
        "name": "Al-Basrah",
        "model": "Irq_AlBasrahM",
        "tex": "Irq_AlBasrahP.tga",
        "hier": b"IRQ_ABS_M",
        "cameo": "specter_missile_h",
        "km": 2300,
        "kg": 2400,
        "acc": 20,
        "stealth": 60,
        "rebuild": 60,
        "price": 5000,
    },
    {
        "slot": "I",
        "object": "Iraq_AlNasir",
        "name": "Al-Nasir",
        "model": "Irq_AlNasirM",
        "tex": "Irq_AlNasirP.tga",
        "hier": b"IRQ_ANS_M",
        "cameo": "specter_missile_i",
        "km": 2400,
        "kg": 3200,
        "acc": 35,
        "stealth": 70,
        "rebuild": 75,
        "price": 6500,
    },
    {
        "slot": "J",
        "object": "Iraq_AlMansour",
        "name": "Al-Mansour",
        "model": "Irq_AlMansourM",
        "tex": "Irq_AlMansourP.tga",
        "hier": b"IRQ_AMN_M",
        "cameo": "specter_missile_j",
        "km": 2500,
        "kg": 4000,
        "acc": 50,
        "stealth": 85,
        "rebuild": 90,
        "price": 8000,
    },
]


def derived(m: dict) -> dict:
    d = dict(m)
    d["range"] = MOTHER_RANGE * (m["km"] / 1000.0)
    d["damage"] = MOTHER_DMG * (m["kg"] / MOTHER_KG)
    d["death"] = int(MOTHER_DEATH * (m["kg"] / MOTHER_KG))
    d["scatter"] = MOTHER_SCATTER * (MOTHER_ACC / m["acc"])
    d["inf_scatter"] = d["scatter"] * (280.0 / 175.0)
    d["hp"] = MOTHER_HP * (m["stealth"] / MOTHER_STEALTH)
    d["rebuild_cost"] = m["price"] // 2
    d["weapon"] = f"Weapon_{m['object']}"
    d["warhead"] = f"Weapon_{m['object']}_Warhead"
    d["projectile"] = f"Projectile_{m['object']}"
    d["upgrade"] = f"Upgrade_{m['object']}_Rebuild"
    d["rebuild_btn"] = f"CB_{m['object']}_Rebuild"
    d["commandset"] = f"{m['object']}_TELCommandSet"
    d["unit_key"] = rf"Data\INI\Object\Specter\Iraq Army\Wheeled\{m['object']}.ini"
    d["proj_key"] = rf"Data\INI\Object\Specter\Iraq Army\{m['object']}_Projectile.ini"
    if m["stealth"] >= 60:
        d["radar"] = "NOT_ON_RADAR"
    elif m["stealth"] >= 20:
        d["radar"] = "LOCAL_UNIT_ONLY"
    else:
        d["radar"] = None
    d["tooltip"] = (
        f"{m['name']}\n"
        f"Range: {m['km']} km\n"
        f"Warhead: {m['kg']} kg\n"
        f"Point Accuracy: {m['acc']}/100\n"
        f"Radar Stealth: {m['stealth']}/100\n"
        f"Rebuild Time: {m['rebuild']} sec\n"
        f"Price: ${m['price']}"
    )
    return d


DERIVED = [derived(m) for m in MISSILES]


def fmt_num(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".")


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes) -> dict[str, bytes]:
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


def parse_index(data: bytes):
    archive_size = struct.unpack(">I", data[4:8])[0]
    count = struct.unpack(">I", data[8:12])[0]
    header_size = struct.unpack(">I", data[12:16])[0]
    pos = 16
    files = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files.append((name, off, size))
    return archive_size, count, header_size, pos, files


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")


def command_block(text: str, kind: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text)
    return m.group(0) if m else None


def slot_map(block: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    expected = header
    for name, off, size in sorted(files, key=lambda x: x[1]):
        if off != expected:
            issues.append(f"overlap/gap {name}")
            break
        expected = off + size
    if expected != len(blob):
        issues.append("trailing gap/overflow")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def csf_parse(csf: bytes):
    if csf[:4] != b" FSC":
        raise SystemExit(f"unexpected CSF magic {csf[:4]!r}")
    magic, ver, nlab, nstr, unused, lang = struct.unpack_from("<4sIIIII", csf, 0)
    labels = []
    pos = 24
    while pos < len(csf):
        if csf[pos : pos + 4] != b" LBL":
            break
        pos += 4
        cnt, nlen = struct.unpack_from("<II", csf, pos)
        pos += 8
        name = csf[pos : pos + nlen].decode("latin1")
        pos += nlen
        strs = []
        for _ in range(cnt):
            smag = csf[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4
            raw = csf[pos : pos + slen * 2]
            pos += slen * 2
            val = bytes(x ^ 0xFF for x in raw).decode("utf-16le")
            extra = None
            if smag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4
                extra = csf[pos : pos + elen]
                pos += elen
            strs.append((smag, val, extra))
        labels.append((name, strs))
    return magic, ver, unused, lang, labels


def csf_build(magic, ver, unused, lang, labels) -> bytes:
    body = bytearray()
    nstr = 0
    for name, strs in labels:
        body += b" LBL"
        body += struct.pack("<II", len(strs), len(name))
        body += name.encode("latin1")
        for smag, val, extra in strs:
            encoded = val.encode("utf-16le")
            xored = bytes(x ^ 0xFF for x in encoded)
            tag = smag if smag in (b" RTS", b"WRTS") else b" RTS"
            body += tag
            body += struct.pack("<I", len(val))
            body += xored
            nstr += 1
            if tag == b"WRTS" and extra is not None:
                body += struct.pack("<I", len(extra))
                body += extra
    header = bytearray()
    header += magic
    header += struct.pack("<IIIII", ver, len(labels), nstr, unused, lang)
    return bytes(header + body)


def csf_upsert(csf: bytes, mapping: dict[str, str]) -> bytes:
    magic, ver, unused, lang, labels = csf_parse(csf)
    by_name = {n: i for i, (n, _) in enumerate(labels)}
    for key, value in mapping.items():
        if key in by_name:
            i = by_name[key]
            name, strs = labels[i]
            if strs:
                smag, _old, extra = strs[0]
                strs[0] = (smag, value, extra)
            else:
                strs.append((b" RTS", value, None))
            labels[i] = (name, strs)
        else:
            labels.append((key, [(b" RTS", value, None)]))
    return csf_build(magic, ver, unused, lang, labels)


def csf_get(csf: bytes, key: str) -> str | None:
    _m, _v, _u, _l, labels = csf_parse(csf)
    for name, strs in labels:
        if name == key and strs:
            return strs[0][1]
    return None


def last_weapon_block(data: dict[str, bytes], name: str) -> tuple[str, str] | None:
    blocks: list[tuple[str, str]] = []
    wep = data[WEAPON_KEY].decode("latin1")
    b = command_block(wep, "Weapon", name)
    if b:
        blocks.append((WEAPON_KEY, b))
    weapon_dir = []
    for k in data:
        lk = k.replace("/", "\\").lower()
        if lk.startswith(r"data\ini\weapon" + "\\") and lk.endswith(".ini"):
            weapon_dir.append(k)
    for k in sorted(weapon_dir, key=lambda x: x.lower()):
        t = data[k].decode("utf-8")
        b = command_block(t, "Weapon", name)
        if b:
            blocks.append((k, b))
    return blocks[-1] if blocks else None


def english_ok(text: str) -> bool:
    for ch in text:
        if ord(ch) > 127 and ch not in "–—−":
            return False
    return True


def make_unit(m: dict) -> str:
    return f"""; Iraq factory missile {m['slot']} — {m['name']}
; TEL clone of Iraq_AlFahd500 (launcher W3D/animation unchanged).
; Flying missile Model = {m['model']} on {m['projectile']}.
; Donor Iraq_AlFahd500 / Iraq_R11ScudB are not modified.

Object {m['object']}
Scale = 0.9
  SelectPortrait         = {m['cameo']}
  ButtonImage            = {m['cameo']}
  UpgradeCameo1 = Upgrade_ChinaNeutronShells
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = Yes
    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY TERTIARY
    DefaultConditionState
      Model                           = Irq_AlFahd500
      WeaponLaunchBone                = PRIMARY MISSILE
      WeaponFireFXBone                = PRIMARY MISSILE
      WeaponLaunchBone                = SECONDARY MISSILE
      WeaponFireFXBone                = SECONDARY MISSILE
      WeaponLaunchBone                = TERTIARY MISSILE
      WeaponFireFXBone                = TERTIARY MISSILE
      Turret                          = Turrettt
      Flags                           = START_FRAME_FIRST
    End
    ConditionState                    = REALLYDAMAGED
      Model                           = Irq_AlFahd500D
      WeaponLaunchBone                = PRIMARY MISSILE
      WeaponFireFXBone                = PRIMARY WEAPONA01
      WeaponLaunchBone                = SECONDARY MISSILE
      WeaponFireFXBone                = SECONDARY WEAPONA01
      WeaponLaunchBone                = TERTIARY MISSILE
      WeaponFireFXBone                = TERTIARY WEAPONA01
      Turret                          = Turrettt
      Flags                           = START_FRAME_FIRST
    End
    ConditionState                    = RUBBLE
      Model                           = Irq_AlFahd500D
      WeaponLaunchBone                = PRIMARY MISSILE
      WeaponFireFXBone                = PRIMARY WEAPONA01
      WeaponLaunchBone                = SECONDARY MISSILE
      WeaponFireFXBone                = SECONDARY WEAPONA01
      WeaponLaunchBone                = TERTIARY MISSILE
      WeaponFireFXBone                = TERTIARY WEAPONA01
      Turret                          = Turrettt
      Flags                           = START_FRAME_FIRST
    End
    ConditionState    = MOVING
      Animation       = IRQ_AF500.IRQ_AF500
      AnimationMode   = ONCE_BACKWARDS
      Flags           = START_FRAME_FIRST
    End
    AliasConditionState = MOVING BETWEEN_FIRING_SHOTS_A
    AliasConditionState = BETWEEN_FIRING_SHOTS_A
    ConditionState    = REALLYDAMAGED MOVING
      Model           = Irq_AlFahd500D
      Animation       = IRQ_AF500D.IRQ_AF500D
      AnimationMode   = ONCE_BACKWARDS
      Flags           = START_FRAME_FIRST
    End
    AliasConditionState = REALLYDAMAGED MOVING BETWEEN_FIRING_SHOTS_A
    ConditionState    = UNPACKING
      Animation       = IRQ_AF500.IRQ_AF500
      AnimationMode   = ONCE
    End
    AliasConditionState = UNPACKING BETWEEN_FIRING_SHOTS_A
    ConditionState    = REALLYDAMAGED UNPACKING
      Model           = Irq_AlFahd500D
      Animation       = IRQ_AF500D.IRQ_AF500D
      AnimationMode   = ONCE
    End
    AliasConditionState = REALLYDAMAGED UNPACKING BETWEEN_FIRING_SHOTS_A
    ConditionState    = PACKING
      Animation       = IRQ_AF500.IRQ_AF500
      AnimationMode   = ONCE_BACKWARDS
      Flags           = START_FRAME_LAST
    End
    AliasConditionState = PACKING BETWEEN_FIRING_SHOTS_A
    ConditionState    = REALLYDAMAGED PACKING
      Model           = Irq_AlFahd500D
      Animation       = IRQ_AF500D.IRQ_AF500D
      AnimationMode   = MANUAL
    End
    AliasConditionState = REALLYDAMAGED PACKING BETWEEN_FIRING_SHOTS_A
    ConditionState  = DEPLOYED
      Animation       = IRQ_AF500.IRQ_AF500
      AnimationMode   = ONCE
      Flags           = START_FRAME_LAST
      TransitionKey   = TRANS_FIRING_A
    End
    AliasConditionState = DEPLOYED FIRING_A
    AliasConditionState = DEPLOYED BETWEEN_FIRING_SHOTS_A
    AliasConditionState = DEPLOYED RELOADING_A
    AliasConditionState = DEPLOYED MOVING
    ConditionState  = DEPLOYED REALLYDAMAGED
      Model           = Irq_AlFahd500D
      Animation       = IRQ_AF500D.IRQ_AF500D
      AnimationMode   = ONCE
      Flags           = START_FRAME_LAST
      TransitionKey   = TRANS_FIRING_A
      HideSubObject   = TURRETFRONT TURRETBACK
      ShowSubObject   = TURRET01
    End
    AliasConditionState = DEPLOYED REALLYDAMAGED FIRING_A
    AliasConditionState = DEPLOYED REALLYDAMAGED BETWEEN_FIRING_SHOTS_A
    AliasConditionState = DEPLOYED REALLYDAMAGED RELOADING_A
    AliasConditionState = DEPLOYED REALLYDAMAGED MOVING
    TrackMarks = EXTireTrack.tga
    Dust = ScudLauncherDust
    DirtSpray = RocketBuggyDirtSpray
    PowerslideSpray = RocketBuggyDirtPowerSlide
    LeftFrontTireBone = Tire01
    RightFrontTireBone = Tire05
    LeftRearTireBone = Tire04
    RightRearTireBone = Tire08
    MidLeftFrontTireBone = Tire02
    MidRightFrontTireBone = Tire06
    MidLeftRearTireBone = Tire03
    MidRightRearTireBone = Tire07
    TireRotationMultiplier = 0.2
  End
  DisplayName      = OBJECT:{m['object']}
  Side = Iraq
  EditorSorting   = VEHICLE
  TransportSlotCount = 10
  WeaponSet
    Conditions = None
    Weapon = PRIMARY   {m['weapon']}
  End
  ArmorSet
    Conditions      = None
    Armor           = TruckArmor
    DamageFX        = TankDamageFX
  End
  BuildCost       = {m['price']}
  BuildTime       = {m['rebuild']}.0
  VisionRange     = 650
  ShroudClearingRange = 150
  ExperienceValue = 50 100 200 400
  ExperienceRequired = 0 400 600 1000
  IsTrainable = Yes
  CrusherLevel           = 2
  CrushableLevel         = 2
  CommandSet    = {m['commandset']}
  VoiceSelect = ScudLauncherVoiceSelect
  VoiceMove = ScudLauncherVoiceMove
  VoiceGuard = ScudLauncherVoiceMove
  VoiceAttack = ScudLauncherVoiceAttack
  SoundMoveStart = ScudLauncherMoveStart
  SoundMoveStartDamaged = ScudLauncherMoveStart
  UnitSpecificSounds
    VoiceCreate       = ScudLauncherVoiceCreate
    TurretMoveStart = NoSound
    TurretMoveLoop = TurretMoveLoop
    TruckLandingSound = NoSound
    TruckPowerslideSound = NoSound
    VoiceCrush = ScudLauncherVoiceCrush
    VoiceEnter = ScudLauncherVoiceMove
    VoicePrimaryWeaponMode = ScudLauncherVoiceModeHiEx
    VoiceSecondaryWeaponMode = ScudLauncherVoiceModeHiEx
    VoiceTertiaryWeaponMode = ScudLauncherVoiceModeAnthrax
    Deploy              = ScudLauncherVoiceAttack
    Undeploy            = ScudLauncherVoiceCrush
  End
  RadarPriority = UNIT
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
  Body = ActiveBody ModuleTag_02
    MaxHealth       = 500.0
    InitialHealth   = 500.0
    SubdualDamageCap = 480
    SubdualDamageHealRate = 500
    SubdualDamageHealAmount = 50
  End
  Behavior = DeployStyleAIUpdate ModuleTag_04
    AutoAcquireEnemiesWhenIdle = No
    PackTime = 6555
    UnpackTime = 6555
    TurretsFunctionOnlyWhenDeployed = Yes
    TurretsMustCenterBeforePacking = Yes
    ManualDeployAnimations = Yes
  End
  Locomotor = SET_NORMAL Generic8x8Locomotor
  Behavior = PhysicsBehavior ModuleTag_05
    Mass = 400.0
  End
  Behavior = WeaponSetUpgrade ModuleTag_09h56u56j
  End
  ; After firing (ClipSize 1, AutoReloadsClip No) the missile is spent.
  ; OBJECT_UPGRADE charges RebuildCost = Price * 0.50 and takes Rebuild Time,
  ; then ReplaceObjectUpgrade recreates a fresh loaded TEL. SPECTER native.
  Behavior = ReplaceObjectUpgrade ModuleTag_Rebuild
    TriggeredBy   = {m['upgrade']}
    ReplaceObject = {m['object']}
  End
  Behavior = TransitionDamageFX ModuleTag_MB708
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuous01
    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_ScudLauncherDamageTransition
  End
  Behavior = SlowDeathBehavior ModuleTag_L8F09
    DeathTypes = ALL -CRUSHED -SPLATTED
    ProbabilityModifier = 50
    DestructionDelay = 100
    DestructionDelayVariance = 300
    FX  = INITIAL  FX_CrusaderCatchFire
    OCL = FINAL    OCL_9P117DeathEffect
    FX  = FINAL    FX_HE_ALBM_Explosion
  End
  Behavior = FXListDie ModuleTag_10F66
    DeathTypes = NONE +CRUSHED +SPLATTED
    DeathFX = FX_CarCrush
  End
  Behavior = CreateObjectDie ModuleTag_11J6
    DeathTypes = NONE +CRUSHED +SPLATTED
    CreationList = OCL_CrusaderTank_CrushEffect
  End
  Behavior = FlammableUpdate ModuleTag_21VHN
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
  End
  Behavior = DestroyDie ModuleTag_22MYUJ76
    DeathTypes = NONE +CRUSHED +SPLATTED
  End
  Behavior = ProductionUpdate ModuleTag_12
    MaxQueueEntries = 1
  End
  Geometry = BOX
  GeometryMajorRadius = 32.0
  GeometryMinorRadius = 10.0
  GeometryHeight = 17.0
  GeometryIsSmall = No
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 45
End
"""


def make_projectile(m: dict) -> str:
    radar = ""
    if m["radar"]:
        radar = f"  RadarPriority = {m['radar']}\n"
    return f"""; Flying missile for {m['name']}. Dedicated W3D {m['model']}.
; Donor ALHIJARAH_MRBM_Object / Projectile_Iraq_AlFahd500 are not modified.

Object {m['projectile']}
Scale = 0.9
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    ParticlesAttachedToAnimatedBones = Yes
    ConditionState
      Model = {m['model']}
      ParticleSysBone = ENGINE01 LRBM_Trail
      ParticleSysBone = ENGINE01 LRBM_Flare2
      ParticleSysBone = ENGINE01 AGM_MissileLenzFlare
      ParticleSysBone = Engine01 SmallCruiseMissileFlare
    End
    ConditionState = POWER_PLANT_UPGRADED
      Model = {m['model']}
    End
  End
  DisplayName      = OBJECT:{m['object']}
  EditorSorting   = SYSTEM
  VisionRange = 100.0
  ShroudClearingRange = 50
{radar}  ArmorSet
    Conditions      = None
    Armor           = SRBMArmor
    DamageFX        = None
  End
  SoundAmbient  = GenericMissileAmbientLoop
  KindOf = PROJECTILE BALLISTIC_MISSILE
  Body = ActiveBody ModuleTag_02
    MaxHealth       = {fmt_num(m['hp'])}.0
    InitialHealth   = {fmt_num(m['hp'])}.0
    SubdualDamageCap = 800
    SubdualDamageHealRate = 100000
    SubdualDamageHealAmount = 50
  End
  Behavior = InstantDeathBehavior DeathModuleTag_01
    DeathTypes = NONE +DETONATED
  End
  Behavior = InstantDeathBehavior DeathModuleTag_02
    DeathTypes = NONE +LASERED
    FX         = FX_GenericMissileDisintegrate
    OCL        = OCL_GenericMissileDisintegrate
  End
  Behavior = InstantDeathBehavior DeathModuleTag_03
    DeathTypes = ALL -LASERED -DETONATED
    FX         = FX_GenericMissileDeath
  End
  Behavior = FireWeaponUpdate ModuleTag_Booster
      Weapon = SRBM_Boosters_Igniter2
      InitialDelay = 6800
  End
  Behavior = PowerPlantUpgrade ModuleTag_IBK
    TriggeredBy = Upgrade_ICBM_BoosterKiller
  End
  Behavior = PowerPlantUpdate ModuleTag_IBKT
    RodsExtendTime = 6500
  End
  Behavior = FireWeaponWhenDeadBehavior ModuleTag_WEC
    DeathWeapon   = {m['warhead']}
    StartsActive  = Yes
  End
  Behavior = PhysicsBehavior ModuleTag_04cwe
    Mass = 15
    ShockResistance       = 0.5
    AerodynamicFriction   = 0.5
    CenterOfMassOffset    = 2
    AllowBouncing = Yes
    AllowCollideForce = Yes
    PitchRollYawFactor  = 1.5
  End
  Behavior = MissileAIUpdate ModuleTag_07
    DetonateCallsKill = Yes
    TryToFollowTarget = No
    FuelLifetime = 0
    IgnitionDelay = 0
    InitialVelocity = 10
    DistanceToTravelBeforeTurning = 1000
    DistanceToTargetBeforeDiving = 800
  End
  Locomotor = SET_NORMAL R11SRBMLocomotor
  Geometry            = Cylinder
  GeometryMajorRadius = 4.0
  GeometryHeight      = 4.0
  GeometryIsSmall     = Yes
  Shadow = SHADOW_DECAL
End
"""


def make_weapons() -> str:
    chunks = [
        "; Iraq factory missiles B/C/D/H/I/J. Last-wins via Data\\INI\\Weapon\\.\n"
        "; Do not put these in Weapon.ini. MOTHER SRBM_ALHIJARAH_HE is not modified.\n"
        "; Range/damage/accuracy/stealth scale from MOTHER 1720/2000+2200/175/HP400.\n"
        "; AutoReloadsClip = No: after fire the clip is spent until paid OBJECT_UPGRADE rebuild.\n"
    ]
    for m in DERIVED:
        chunks.append(
            f"""
Weapon {m['weapon']}
  PrimaryDamage               = {fmt_num(m['damage'])}.0
  PrimaryDamageRadius         = 80.0
  SecondaryDamage             = 400.0
  SecondaryDamageRadius       = 10.0
  ScatterRadius               = {fmt_num(m['scatter'])}
  ScatterRadiusVsInfantry     = {fmt_num(m['inf_scatter'])}
  AttackRange                 = {fmt_num(m['range'])}.0
  MinimumAttackRange          = 800.0
  PreAttackDelay              = 500
  PreAttackType               = PER_SHOT
  DamageType                  = ARMOR_PIERCING
  DeathType                   = EXPLODED
  FireFX                      = FX_IskanderFiringEffects
  ProjectileObject            = {m['projectile']}
  ProjectileDetonationFX      = FX_SmallSRBM_Explosion
  RadiusDamageAffects         = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  FireSound                   = Iskander_Firing
  WeaponSpeed                 = 280
  AcceptableAimDelta          = 360
  DelayBetweenShots           = 3000
  ClipSize                    = 1
  AutoReloadsClip             = No
  ClipReloadTime              = {m['rebuild'] * 1000}
  ShockWaveAmount             = 680.0
  ShockWaveRadius             = 150.0
  ShockWaveTaperOff           = 0.33
  AntiGround                  = Yes
End

Weapon {m['warhead']}
  PrimaryDamage           = {m['death']}
  PrimaryDamageRadius     = 20.0
  AttackRange             = 1
  DamageType              = HACK
  DeathType               = EXPLODED
  WeaponSpeed             = 9999999999
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  ClipSize                = 1
  ProjectileCollidesWith  = STRUCTURES
End
"""
        )
    return "".join(chunks)


def make_upgrades() -> str:
    chunks = [
        "; Per-object rebuild after firing. Rebuild Cost = Price * 0.50.\n"
        "; Type = OBJECT so each TEL pays its own reactivation, not a player-wide flag.\n"
        "; Command_BuyAlhussaienMissile / OBJECT_UPGRADE is the SPECTER paid-rearm pattern.\n"
    ]
    for m in DERIVED:
        chunks.append(
            f"""
Upgrade {m['upgrade']}
  DisplayName      = UPGRADE:{m['object']}_Rebuild
  Type             = OBJECT
  BuildCost        = {m['rebuild_cost']}
  BuildTime        = {m['rebuild']}.0
  ButtonImage      = {m['cameo']}
End
"""
        )
    return "".join(chunks)


def make_commandsets() -> str:
    chunks = ["\r\n"]
    for m in DERIVED:
        chunks.append(
            f"CommandSet {m['commandset']}\r\n"
            "  1 = Command_FireMainWeapon\r\n"
            f"  2 = {m['rebuild_btn']}\r\n"
            "  6 = Command_ScudSwitchToHE\r\n"
            "  8 = Command_ScudSwitchToHE_NI\r\n"
            "  10 = Command_ScudSwitchToHE_CH\r\n"
            "  12 = Command_AttackMove\r\n"
            "  13 = Command_Guard\r\n"
            "  14 = Command_Stop\r\n"
            "End\r\n\r\n"
        )
    return "".join(chunks)


def make_rebuild_buttons() -> str:
    chunks = ["\r\n"]
    for m in DERIVED:
        chunks.append(
            f"CommandButton {m['rebuild_btn']}\r\n"
            "  Command                 = OBJECT_UPGRADE\r\n"
            "  UnitSpecificSound       = MoneyWithdraw\r\n"
            f"  Upgrade                 = {m['upgrade']}\r\n"
            "  TextLabel               = CONTROLBAR:IraqMissileRebuild\r\n"
            "  Options                 = OK_FOR_MULTI_SELECT NOT_QUEUEABLE\r\n"
            f"  ButtonImage             = {m['cameo']}\r\n"
            "  ButtonBorderType        = UPGRADE\r\n"
            "  DescriptLabel           = CONTROLBAR:ToolTipIraqMissileRebuild\r\n"
            "End\r\n\r\n"
        )
    return "".join(chunks)


def make_slots_ini() -> str:
    lines = [
        "; SPECTER universal missile slots A-L.",
        "; Visual identity is the slot, not a country missile name.",
        "; ZH binds Object on the CommandButton. A + B/C/D/H/I/J are assigned.",
        "; E/F/G/K/L omit Object until a real missile is connected.",
        "",
        "CommandButton CB_MISSILE_A",
        "  Command       = UNIT_BUILD",
        "  Object        = Iraq_AlFahd500",
        "  TextLabel     = CONTROLBAR:SpecterMissileA",
        "  ButtonImage   = specter_missile_a",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel = CONTROLBAR:ToolTipSpecterMissileA",
        "End",
        "",
    ]
    assigned = {m["slot"]: m["object"] for m in DERIVED}
    for ch in "BCDEFGHIJKL":
        lines.append(f"CommandButton CB_MISSILE_{ch}")
        lines.append("  Command       = UNIT_BUILD")
        if ch in assigned:
            lines.append(f"  Object        = {assigned[ch]}")
        lines.append(f"  TextLabel     = CONTROLBAR:SpecterMissile{ch}")
        lines.append(f"  ButtonImage   = specter_missile_{ch.lower()}")
        lines.append("  ButtonBorderType = BUILD")
        lines.append(f"  DescriptLabel = CONTROLBAR:ToolTipSpecterMissile{ch}")
        lines.append("End")
        lines.append("")
    return "\n".join(lines)


def patch_commandbuttons(cb: bytes) -> bytes:
    text = cb.decode("latin1")
    assigned = {m["slot"]: m["object"] for m in DERIVED}
    for ch, obj in assigned.items():
        pat = rf"(CommandButton CB_MISSILE_{ch}\r?\n  Command       = UNIT_BUILD\r?\n)(  Object        = [^\r\n]+\r?\n)?"
        repl = rf"\g<1>  Object        = {obj}\n"
        new, n = re.subn(pat, repl, text, count=1)
        if n != 1:
            raise SystemExit(f"failed to bind CB_MISSILE_{ch}")
        text = new
    if "CommandButton CB_Iraq_AlHusseinII_Rebuild" not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += make_rebuild_buttons().replace("\r\n", "\n")
    return text.replace("\n", "\r\n").replace("\r\r\n", "\r\n").encode("latin1")


def write_workspace_sources() -> None:
    wheeled = SRC_DIR / "Object/Specter/Iraq Army/Wheeled"
    proj_dir = SRC_DIR / "Object/Specter/Iraq Army"
    wep_dir = SRC_DIR / "Weapon"
    wheeled.mkdir(parents=True, exist_ok=True)
    proj_dir.mkdir(parents=True, exist_ok=True)
    wep_dir.mkdir(parents=True, exist_ok=True)
    for m in DERIVED:
        (wheeled / f"{m['object']}.ini").write_text(make_unit(m), encoding="utf-8")
        (proj_dir / f"{m['object']}_Projectile.ini").write_text(make_projectile(m), encoding="utf-8")
    (wep_dir / "Weapon_Iraq_FactoryMissiles.ini").write_text(make_weapons(), encoding="utf-8")
    (SRC_DIR / "Upgrade_IraqFactoryMissiles.ini").write_text(make_upgrades(), encoding="utf-8")
    (SRC_DIR / "CommandButton_SpecterMissileSlots.ini").write_text(make_slots_ini(), encoding="utf-8")


def csf_map() -> dict[str, str]:
    mapping = {
        "OBJECT:Iraq_AlFahd500": "Al-Fahd500",
        "CONTROLBAR:ToolTipSpecterMissileA": ALFAHD_TOOLTIP,
        "CONTROLBAR:IraqMissileRebuild": "Rebuild",
        "CONTROLBAR:ToolTipIraqMissileRebuild": (
            "Pay 50 percent of the missile price to rebuild after firing."
        ),
    }
    for m in DERIVED:
        mapping[f"OBJECT:{m['object']}"] = m["name"]
        mapping[f"CONTROLBAR:ToolTipSpecterMissile{m['slot']}"] = m["tooltip"]
        mapping[f"UPGRADE:{m['object']}_Rebuild"] = f"{m['name']} Rebuild"
    return mapping


def validate(data: dict[str, bytes], art: dict[str, bytes], src_data: dict[str, bytes], src_art: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    all_ini = b"".join(v for k, v in data.items() if k.lower().endswith(".ini"))

    if data[R11_KEY] != src_data[R11_KEY]:
        fails.append("9P117.ini mutated")
    if data[WEAPON_KEY] != src_data[WEAPON_KEY]:
        fails.append("Weapon.ini mutated")
    if data[FACTORY_KEY] != src_data[FACTORY_KEY]:
        fails.append("factory object mutated")
    if data[UNIT_A_KEY] != src_data[UNIT_A_KEY]:
        fails.append("Iraq_AlFahd500.ini mutated")
    if data[PROJ_A_KEY] != src_data[PROJ_A_KEY]:
        fails.append("Al-Fahd projectile mutated")
    if data[WEP_A_KEY] != src_data[WEP_A_KEY]:
        fails.append("Al-Fahd weapon last-wins mutated")

    r11 = data[R11_KEY].decode("latin1")
    if "BuildCost       = 1200" not in r11 or "Weapon = PRIMARY   SRBM_ALHIJARAH_HE" not in r11:
        fails.append("MOTHER Iraq_R11ScudB cost/weapon changed")
    if "SelectPortrait         = irq_9p117" not in r11:
        fails.append("9P117 cameo retargeted")

    mother = command_block(data[WEAPON_KEY].decode("latin1"), "Weapon", "SRBM_ALHIJARAH_HE") or ""
    if "PrimaryDamage               = 2000.0" not in mother:
        fails.append("MOTHER damage changed")
    if "AttackRange                 = 1720.0" not in mother:
        fails.append("MOTHER range changed")
    if "ScatterRadius               = 175" not in mother:
        fails.append("MOTHER scatter changed")

    unit_a = data[UNIT_A_KEY].decode("utf-8")
    if "BuildCost       = 2200" not in unit_a or "BuildTime       = 30.0" not in unit_a:
        fails.append("Al-Fahd price/time changed")
    if "Weapon = PRIMARY   Weapon_Iraq_AlFahd500" not in unit_a:
        fails.append("Al-Fahd weapon link")
    if "SelectPortrait         = specter_missile_a" not in unit_a:
        fails.append("Al-Fahd queue portrait")
    if "IRQ_AF500.IRQ_AF500" not in unit_a:
        fails.append("Al-Fahd launch animation lost")

    last_a = last_weapon_block(data, "Weapon_Iraq_AlFahd500")
    if not last_a or "PrimaryDamage               = 8000.0" not in last_a[1]:
        fails.append("Al-Fahd last-wins damage")
    if last_a and last_a[0].replace("/", "\\").lower() != WEP_A_KEY.lower():
        fails.append(f"Al-Fahd weapon last-wins file {last_a[0]}")

    btn_a = command_block(data[CB_KEY].decode("latin1"), "CommandButton", "CB_MISSILE_A") or ""
    if "Object        = Iraq_AlFahd500" not in btn_a:
        fails.append("CB_MISSILE_A mapping")

    fac = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet") or ""
    slots = slot_map(fac)
    expect = {1: "CB_MISSILE_A", 2: "CB_MISSILE_B", 3: "CB_MISSILE_C", 4: "CB_MISSILE_D",
              8: "CB_MISSILE_H", 9: "CB_MISSILE_I", 10: "CB_MISSILE_J",
              13: "Command_SetRallyPoint", 14: "Command_Sell"}
    for k, v in expect.items():
        if slots.get(k) != v:
            fails.append(f"factory slot {k}={slots.get(k)} expected {v}")
    for empty in (5, 6, 7, 11, 12, 15, 16, 17, 18):
        if empty in slots:
            fails.append(f"unused slot {empty} wired to {slots[empty]}")
    if max(slots) > 18:
        fails.append(f"CommandSet slot above 18: {max(slots)}")

    for ch in "EFGKL":
        btn = command_block(data[CB_KEY].decode("latin1"), "CommandButton", f"CB_MISSILE_{ch}") or ""
        if re.search(r"^\s*Object\s*=", btn, re.M):
            fails.append(f"CB_MISSILE_{ch} has Object (must stay unwired)")
        n = all_ini.count(f"CommandButton CB_MISSILE_{ch}".encode("ascii"))
        if n != 1:
            fails.append(f"CB_MISSILE_{ch} count {n}")

    for m in DERIVED:
        n_obj = len(re.findall(rf"^Object {re.escape(m['object'])}\s*$".encode("ascii"), all_ini, re.M))
        if n_obj != 1:
            fails.append(f"{m['object']} definition count {n_obj}")
        if m["unit_key"] not in data:
            fails.append(f"missing {m['unit_key']}")
            continue
        unit = data[m["unit_key"]].decode("utf-8")
        if f"SelectPortrait         = {m['cameo']}" not in unit:
            fails.append(f"{m['object']} SelectPortrait")
        if f"ButtonImage            = {m['cameo']}" not in unit:
            fails.append(f"{m['object']} ButtonImage")
        if f"BuildCost       = {m['price']}" not in unit:
            fails.append(f"{m['object']} price")
        if f"BuildTime       = {m['rebuild']}.0" not in unit:
            fails.append(f"{m['object']} build time")
        if f"Weapon = PRIMARY   {m['weapon']}" not in unit:
            fails.append(f"{m['object']} weapon")
        if f"ReplaceObject = {m['object']}" not in unit:
            fails.append(f"{m['object']} rebuild replace")
        if f"TriggeredBy   = {m['upgrade']}" not in unit:
            fails.append(f"{m['object']} rebuild upgrade")
        if "IRQ_AF500.IRQ_AF500" not in unit:
            fails.append(f"{m['object']} launch anim")
        if "Model                           = Irq_AlFahd500" not in unit:
            fails.append(f"{m['object']} launcher model")

        proj = data[m["proj_key"]].decode("utf-8")
        if proj.count(f"Model = {m['model']}") < 1:
            fails.append(f"{m['object']} projectile Model != {m['model']}")
        if f"MaxHealth       = {fmt_num(m['hp'])}.0" not in proj:
            fails.append(f"{m['object']} projectile HP")
        if m["radar"]:
            if f"RadarPriority = {m['radar']}" not in proj:
                fails.append(f"{m['object']} radar {m['radar']}")
        else:
            if "RadarPriority" in proj:
                fails.append(f"{m['object']} should omit RadarPriority like MOTHER")
        if f"DeathWeapon   = {m['warhead']}" not in proj:
            fails.append(f"{m['object']} death weapon")

        wep = last_weapon_block(data, m["weapon"])
        if not wep:
            fails.append(f"missing weapon {m['weapon']}")
        else:
            if wep[0].replace("/", "\\").lower() != WEP_NEW_KEY.lower():
                fails.append(f"{m['weapon']} last-wins {wep[0]}")
            if f"AttackRange                 = {fmt_num(m['range'])}.0" not in wep[1]:
                fails.append(f"{m['weapon']} range")
            if f"PrimaryDamage               = {fmt_num(m['damage'])}.0" not in wep[1]:
                fails.append(f"{m['weapon']} damage")
            if f"ScatterRadius               = {fmt_num(m['scatter'])}" not in wep[1]:
                fails.append(f"{m['weapon']} scatter")
            if "AutoReloadsClip             = No" not in wep[1]:
                fails.append(f"{m['weapon']} AutoReloadsClip")
            if f"ProjectileObject            = {m['projectile']}" not in wep[1]:
                fails.append(f"{m['weapon']} projectile")

        war = last_weapon_block(data, m["warhead"])
        if not war or f"PrimaryDamage           = {m['death']}" not in war[1]:
            fails.append(f"{m['warhead']} death damage")

        btn = command_block(data[CB_KEY].decode("latin1"), "CommandButton", f"CB_MISSILE_{m['slot']}") or ""
        if f"Object        = {m['object']}" not in btn:
            fails.append(f"CB_MISSILE_{m['slot']} Object")
        if f"ButtonImage   = {m['cameo']}" not in btn:
            fails.append(f"CB_MISSILE_{m['slot']} art")

        rbtn = command_block(data[CB_KEY].decode("latin1"), "CommandButton", m["rebuild_btn"]) or ""
        if f"Upgrade                 = {m['upgrade']}" not in rbtn:
            fails.append(f"{m['rebuild_btn']} upgrade")
        if "OBJECT_UPGRADE" not in rbtn:
            fails.append(f"{m['rebuild_btn']} command")

        cs_count = len(re.findall(rf"^CommandSet {re.escape(m['commandset'])}\s*$".encode("ascii"), all_ini, re.M))
        if cs_count != 1:
            fails.append(f"{m['commandset']} definition count {cs_count}")
        cs = command_block(data[CS_KEY].decode("latin1"), "CommandSet", m["commandset"]) or ""
        cs_slots = slot_map(cs)
        if cs_slots.get(1) != "Command_FireMainWeapon" or cs_slots.get(2) != m["rebuild_btn"]:
            fails.append(f"{m['commandset']} slots {cs_slots}")

        upg = command_block(data[UPG_KEY].decode("utf-8"), "Upgrade", m["upgrade"]) or ""
        if f"BuildCost        = {m['rebuild_cost']}" not in upg:
            fails.append(f"{m['upgrade']} cost")
        if "Type             = OBJECT" not in upg:
            fails.append(f"{m['upgrade']} Type OBJECT")
        if f"BuildTime        = {m['rebuild']}.0" not in upg:
            fails.append(f"{m['upgrade']} time")

        tip = csf_get(data[CSF_KEY], f"CONTROLBAR:ToolTipSpecterMissile{m['slot']}")
        if tip != m["tooltip"]:
            fails.append(f"tooltip {m['slot']} {tip!r}")
        if tip and (not english_ok(tip) or "Damage" in tip.splitlines()):
            fails.append(f"tooltip {m['slot']} not English-only / has Damage")
        disp = csf_get(data[CSF_KEY], f"OBJECT:{m['object']}")
        if disp != m["name"]:
            fails.append(f"DisplayName {m['object']} {disp!r}")

        w3d = rf"Art\W3D\{m['model']}.W3D"
        tex = rf"Art\Textures\{m['tex']}"
        if w3d not in art:
            fails.append(f"ART missing {w3d}")
        else:
            if m["hier"] not in art[w3d]:
                fails.append(f"{m['model']} hierarchy {m['hier']!r} missing")
            tex_stem = m["tex"].encode("ascii")
            if tex_stem not in art[w3d] and m["tex"].rsplit(".", 1)[0].encode("ascii") not in art[w3d]:
                fails.append(f"{m['model']} does not reference {m['tex']}")
        if tex not in art:
            fails.append(f"ART missing {tex}")

    tip_a = csf_get(data[CSF_KEY], "CONTROLBAR:ToolTipSpecterMissileA")
    if tip_a != ALFAHD_TOOLTIP:
        fails.append(f"Al-Fahd tooltip {tip_a!r}")
    if tip_a and (not english_ok(tip_a) or any(ord(c) > 127 for c in tip_a)):
        fails.append("Al-Fahd tooltip still non-English")
    if tip_a and "Damage" in tip_a.splitlines():
        fails.append("Al-Fahd tooltip has Damage line")

    zzzz = [
        k
        for k, v in data.items()
        if "zzzz" in k.lower()
        and any(m["object"].encode("ascii") in v for m in DERIVED)
    ]
    if zzzz:
        fails.append(f"ZZZZ override {zzzz[:4]}")

    # ART must be an identity rebuild of the skins package.
    if set(art) != set(src_art):
        fails.append("ART file set changed")
    mutated = [k for k in src_art if art.get(k) != src_art.get(k)]
    if mutated:
        fails.append(f"ART content mutated {mutated[:6]}")
    for donor in [
        r"Art\W3D\Irq_9P117.W3D",
        r"Art\W3D\Irq_R11_M.W3D",
        r"Art\W3D\Irq_AlFahd500.W3D",
        r"Art\W3D\Irq_AlFahd500M.W3D",
        r"Art\W3D\Irq_AlFahd500D.W3D",
        r"Art\Textures\GENERIC-MISSILES.dds",
        r"Art\Textures\Irq_AlFahd500P.tga",
    ]:
        if donor in src_art and art.get(donor) != src_art[donor]:
            fails.append(f"shared ART mutated {donor}")
    for ch in "abcdefghijkl":
        k = rf"Art\Textures\specter_missile_{ch}.tga"
        if art.get(k) != src_art.get(k):
            fails.append(f"slot cameo mutated {k}")

    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("live DATA baseline mismatch")
    if SRC_ART.stat().st_size != BASE_ART_SIZE or sha256_path(SRC_ART) != BASE_ART_SHA:
        raise SystemExit("live ART baseline mismatch")

    write_workspace_sources()
    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    cs = data[CS_KEY].decode("latin1")
    if OLD_SET not in cs:
        raise SystemExit("factory CommandSet block not found")
    data[CS_KEY] = (cs.replace(OLD_SET, NEW_SET, 1) + make_commandsets()).encode("latin1")
    data[CB_KEY] = patch_commandbuttons(data[CB_KEY])
    data[WEP_NEW_KEY] = to_crlf(make_weapons())
    data[UPG_KEY] = to_crlf(make_upgrades())
    for m in DERIVED:
        data[m["unit_key"]] = to_crlf(make_unit(m))
        data[m["proj_key"]] = to_crlf(make_projectile(m))
    data[CSF_KEY] = csf_upsert(data[CSF_KEY], csf_map())

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    packed_data = build_big(data)
    packed_art = build_big(art)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(packed_data)
    out_art.write_bytes(packed_art)

    extracted_d = parse_big(packed_data)
    extracted_a = parse_big(packed_art)
    stage = OUT / "LAST_WINS_EXTRACT"
    (stage / "DATA").mkdir(parents=True)
    (stage / "ART").mkdir(parents=True)
    dump_keys = [CB_KEY, CS_KEY, UNIT_A_KEY, WEP_NEW_KEY, UPG_KEY, R11_KEY, FACTORY_KEY]
    dump_keys += [m["unit_key"] for m in DERIVED]
    dump_keys += [m["proj_key"] for m in DERIVED]
    for rel in dump_keys:
        p = stage / "DATA" / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted_d[rel])
    for m in DERIVED:
        for rel in (rf"Art\W3D\{m['model']}.W3D", rf"Art\Textures\{m['tex']}"):
            p = stage / "ART" / rel.replace("\\", "/")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(extracted_a[rel])

    fails = validate(extracted_d, extracted_a, src_data, src_art)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed_data))
    fails.extend(f"ART {x}" for x in big_structure_ok(packed_art))

    data_sha = sha256_path(out_data)
    art_sha = sha256_path(out_art)
    report = [
        "# SPECTER Iraq missile DATA activation B/C/D/H/I/J + English Al-Fahd tooltip",
        "",
        "MOTHER / Iraq_R11ScudB / 9P117 — NOT MODIFIED",
        "Al-Fahd500 gameplay / ART / animation — NOT MODIFIED (English tooltip only)",
        "ART skins B/C/D/H/I/J rebuilt unchanged from SPECTER_IRAQ_MISSILE_SKINS_BCDHIJ",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted_d)}",
        f"- ART size: {out_art.stat().st_size}",
        f"- ART SHA256: {art_sha}",
        f"- ART files: {len(extracted_a)}",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        report.append("RUNTIME_TEST=NOT RUN")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static)",
        "- Objects: Iraq_AlHusseinII, Iraq_AlSamoudII, Iraq_AlAbbas, Iraq_AlBasrah, Iraq_AlNasir, Iraq_AlMansour",
        "- CB_MISSILE_B/C/D/H/I/J resolve to those Objects",
        "- Factory slots 1=A 2=B 3=C 4=D 8=H 9=I 10=J 13=Rally 14=Sell; E/F/G/K/L empty",
        "- Projectile Models: Irq_AlHussein2M / Irq_AlSamoud2M / Irq_AlAbbas2M / Irq_AlBasrahM / Irq_AlNasirM / Irq_AlMansourM",
        "- Queue ButtonImage/SelectPortrait = specter_missile_b/c/d/h/i/j",
        "- Al-Fahd tooltip English; no Persian; no Damage line",
        "- 50% OBJECT_UPGRADE rebuild cost + ReplaceObjectUpgrade + AutoReloadsClip No",
        "- MOTHER and Al-Fahd gameplay byte-identical vs DATA baseline",
        "- ART identity rebuild of dedicated skins package",
        "- no ZZZZ override",
        "",
        "RUNTIME_TEST=NOT RUN",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=NO (complete identity rebuild of skins package)\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted_d)}\n"
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={out_art.stat().st_size}\n"
        f"ART_SHA256={art_sha}\n"
        f"ART_FILES={len(extracted_a)}\n"
        "OBJECTS=Iraq_AlHusseinII,Iraq_AlSamoudII,Iraq_AlAbbas,Iraq_AlBasrah,Iraq_AlNasir,Iraq_AlMansour\n"
        "COMMANDBUTTONS=CB_MISSILE_B,C,D,H,I,J\n"
        "COMMANDSET=Iraq_AlFahdMissileFactoryCommandSet\n"
        "REBUILD=OBJECT_UPGRADE 50% Price + ReplaceObjectUpgrade + AutoReloadsClip=No\n"
        "ALFAHD_UI=English tooltip only\n"
        "MOTHER_GAMEPLAY=UNCHANGED\n"
        "ALFAHD_GAMEPLAY=UNCHANGED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq missile DATA activation (B/C/D/H/I/J) + English Al-Fahd tooltip\n"
        "Place BOTH complete replacement files in the game folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "  _SPEC_ART_ONE.big\n"
        "9P117 / MOTHER is unmodified. Al-Fahd500 gameplay is unmodified.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_DATA_BCDHIJ.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
