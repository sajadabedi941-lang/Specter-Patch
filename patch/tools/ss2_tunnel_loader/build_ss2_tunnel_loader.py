#!/usr/bin/env python3
"""SS2: add Turkey-style tunnel loaders to every other playable faction.

Adds three unique-path INI members to SS2 _SPEC_DATA_ONE.big:

  Data\\INI\\CommandButton_zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini
  Data\\INI\\CommandSet_zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini
  Data\\INI\\zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini

Does not modify CommandSet.ini, CommandButton.ini, MatchStart, OCL,
Turkey Dozer.ini, or Turkey PowerStation.ini.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/tmp/ss2/SPECTER FINAL (GeneralsMode.com)")
SRC_BIG = ROOT / "_SPEC_DATA_ONE.big"
OUT_DIR = Path("patch/Release/SPECTER_SS2_TUNNEL_LOADER_ALL_FACTIONS")
GEN_DIR = Path("patch/tools/ss2_tunnel_loader/generated")

CB_MEMBER = r"Data\INI\CommandButton_zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini"
CS_MEMBER = r"Data\INI\CommandSet_zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini"
OBJ_MEMBER = r"Data\INI\zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini"

FORBIDDEN_MEMBERS = (
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\CommandSet_ZZZZ_CommandCenterMatchStart.ini",
    r"Data\INI\ObjectCreationList.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Wheleed\Dozer.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\PowerStation.ini",
)

FACTIONS = [
    {"side": "Iraq", "cc": "Iraq_CommandCenter", "loader": "Iraq_VehicleDozerm", "tunnel": "Iraq_PowerStationm"},
    {"side": "NorthKorea", "cc": "NorthKorea_CommandCenter", "loader": "NorthKorea_VehicleDozerm", "tunnel": "NorthKorea_PowerStationm"},
    {"side": "America", "cc": "AmericaCommandCenter", "loader": "AmericaVehicleDozerm", "tunnel": "AmericaPowerStationm"},
    {"side": "Russia", "cc": "RussiaCommandCenter", "loader": "RussiaVehicleDozerm", "tunnel": "RussiaPowerStationm"},
    {"side": "China", "cc": "ChinaCommandCenter", "loader": "ChinaVehicleDozerm", "tunnel": "ChinaPowerStationm"},
    {"side": "GLA", "cc": "GLACommandCenter", "loader": "GLAVehicleDozerm", "tunnel": "GLAPowerStationm"},
    {"side": "Boss", "cc": "Boss_CommandCenter", "loader": "Boss_VehicleDozerm", "tunnel": "Boss_PowerStationm"},
    {"side": "AmericaAirForceGeneral", "cc": "AirF_AmericaCommandCenter", "loader": "AirF_AmericaVehicleDozerm", "tunnel": "AirF_AmericaPowerStationm"},
    {"side": "Nato", "cc": "NatoCommandCenter", "loader": "NatoVehicleDozerm", "tunnel": "NatoPowerStationm"},
    {"side": "Iran", "cc": "IranCommandCenter", "loader": "IranVehicleDozerm", "tunnel": "IranPowerStationm"},
    {"side": "Pakistan", "cc": "Pakistan_CommandCenter", "loader": "Pakistan_VehicleDozerm", "tunnel": "Pakistan_PowerStationm"},
    {"side": "SaudiArabia", "cc": "SaudiArabia_CommandCenter", "loader": "SaudiArabia_VehicleDozerm", "tunnel": "SaudiArabia_PowerStationm"},
    {"side": "UAE", "cc": "UAE_CommandCenter", "loader": "UAE_VehicleDozerm", "tunnel": "UAE_PowerStationm"},
    {"side": "India", "cc": "India_CommandCenter", "loader": "India_VehicleDozerm", "tunnel": "India_PowerStationm"},
    {"side": "Syria", "cc": "Syria_CommandCenter", "loader": "Syria_VehicleDozerm", "tunnel": "Syria_PowerStationm"},
    {"side": "Germany", "cc": "GermanyCommandCenter", "loader": "GermanyVehicleDozerm", "tunnel": "GermanyPowerStationm"},
    {"side": "France", "cc": "FranceCommandCenter", "loader": "FranceVehicleDozerm", "tunnel": "FrancePowerStationm"},
    {"side": "Britain", "cc": "BritainCommandCenter", "loader": "BritainVehicleDozerm", "tunnel": "BritainPowerStationm"},
    {"side": "Italy", "cc": "ItalyCommandCenter", "loader": "ItalyVehicleDozerm", "tunnel": "ItalyPowerStationm"},
    {"side": "Sweden", "cc": "SwedenCommandCenter", "loader": "SwedenVehicleDozerm", "tunnel": "SwedenPowerStationm"},
    {"side": "Ukraine", "cc": "UkraineCommandCenter", "loader": "UkraineVehicleDozerm", "tunnel": "UkrainePowerStationm"},
    {"side": "Libya", "cc": "Libya_CommandCenter", "loader": "Libya_VehicleDozerm", "tunnel": "Libya_PowerStationm"},
    {"side": "SouthAfrica", "cc": "SouthAfrica_CommandCenter", "loader": "SouthAfrica_VehicleDozerm", "tunnel": "SouthAfrica_PowerStationm"},
    {"side": "SouthKorea", "cc": "SouthKorea_CommandCenter", "loader": "SouthKorea_VehicleDozerm", "tunnel": "SouthKorea_PowerStationm"},
    {"side": "Japan", "cc": "Japan_CommandCenter", "loader": "Japan_VehicleDozerm", "tunnel": "Japan_PowerStationm"},
    {"side": "Vietnam", "cc": "Vietnam_CommandCenter", "loader": "Vietnam_VehicleDozerm", "tunnel": "Vietnam_PowerStationm"},
]


def crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def iter_big_members(data: bytes):
    if data[:4] != b"BIGF":
        raise SystemExit("not BIGF")
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    for _ in range(nfiles):
        foff, fsize = struct.unpack(">II", data[off : off + 8])
        off += 8
        end = data.find(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        yield name, data[foff : foff + fsize]


def build_big_ordered(items: list[tuple[str, bytes]]) -> bytes:
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


def parse_blocks(text: str, kind: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(rf"(?m)^{kind}\s+(\S+)\s*$", text):
        name = m.group(1)
        start = m.start()
        nxt = text.find(f"\n{kind} ", start + 1)
        out[name] = text[start : nxt if nxt > 0 else None]
    return out


def load_winning_commandsets() -> dict[str, str]:
    cs_map = {}
    files = sorted((ROOT / "Data/INI").glob("CommandSet*.ini"), key=lambda p: p.name.lower())
    for path in files:
        cs_map.update(parse_blocks(path.read_text("latin1", "replace"), "CommandSet"))
    return cs_map


def find_object_commandset(obj_name: str) -> str:
    hits = []
    for path in (ROOT / "Data/INI/Object").rglob("*.ini"):
        text = path.read_text("latin1", "replace")
        i = text.find(f"Object {obj_name}")
        if i < 0:
            continue
        first = text[i : text.find("\n", i)].split()
        if first[:2] != ["Object", obj_name]:
            continue
        nxt = text.find("\nObject ", i + 1)
        chunk = text[i : nxt if nxt > 0 else None]
        m = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", chunk)
        if m:
            hits.append(m.group(1))
    if not hits:
        raise SystemExit(f"CommandSet not found for {obj_name}")
    return hits[-1]


def slots_of(block: str) -> list[tuple[int, str]]:
    return [(int(a), b) for a, b in re.findall(r"(?m)^\s*(\d+)\s*=\s*(\S+)", block)]


def choose_slot(used: set[int]) -> int:
    if 4 not in used:
        return 4
    for i in range(1, 13):
        if i not in used:
            return i
    # Iran: 1-12 full, 13/14 reserved. SS2 CC bars already use 15-18.
    for i in range(15, 19):
        if i not in used:
            return i
    raise SystemExit(f"no legal slot in {sorted(used)}")


def collect_existing_names() -> dict[str, set[str]]:
    names = {"Object": set(), "CommandSet": set(), "CommandButton": set(), "ObjectCreationList": set()}
    for path in (ROOT / "Data/INI").rglob("*.ini"):
        text = path.read_text("latin1", "replace")
        for kind in names:
            names[kind].update(parse_blocks(text, kind).keys())
    src = SRC_BIG.read_bytes()
    for _, blob in iter_big_members(src):
        text = blob.decode("latin1", "replace")
        for kind in names:
            names[kind].update(parse_blocks(text, kind).keys())
    return names


def loader_object(side: str, name: str, commandset: str) -> str:
    return f"""Object {name}

  SelectPortrait         = SACDozerm
  ButtonImage            = SACDozerm
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model             = Irq_VT72B
      WaitForStateToFinishIfPossible = TRANS_DIGGING
    End
    ConditionState = PREATTACK_A
      Animation         = Irq_VT72B.Irq_VT72B
      AnimationMode     = ONCE
      TransitionKey     = TRANS_DIGGING
    End
    ConditionState = MOVING
      WaitForStateToFinishIfPossible = TRANS_DIGGING
    End
    ConditionState      = REALLYDAMAGED RUBBLE
      Model             = Irq_VT72B
      WaitForStateToFinishIfPossible = TRANS_DIGGING_DAMAGED
    End
    ConditionState = PREATTACK_A REALLYDAMAGED RUBBLE
      Model             = Irq_VT72B
      Animation         = Irq_VT72B.Irq_VT72B
      AnimationMode     = ONCE
      TransitionKey     = TRANS_DIGGING_DAMAGED
    End
    ConditionState      = MOVING REALLYDAMAGED RUBBLE
      Model             = Irq_VT72B
      WaitForStateToFinishIfPossible = TRANS_DIGGING_DAMAGED
    End
    TrackMarks            = EXTireTrack2.tga
    Dust                  = RocketBuggyDust
    DirtSpray             = RocketBuggyDirtSpray
    TireRotationMultiplier      = 0.2
    PowerslideRotationAddition  = 0
    ParticlesAttachedToAnimatedBones = Yes
  End
  DisplayName         = OBJECT:Dozer
  Side                = {side}
  EditorSorting       = VEHICLE
  TransportSlotCount  = 5
  BuildCost           = 1000
  BuildTime           = 5.0
  VisionRange         = 200
  ShroudClearingRange = 200
  WeaponSet
    Conditions = None
    Weapon = PRIMARY None
  End
  WeaponSet
    Conditions = MINE_CLEARING_DETAIL
    Weapon = PRIMARY DozerMineDisarmingWeapon
  End
  ArmorSet
    Conditions        = None
    Armor             = DozerArmor
    DamageFX          = TankDamageFX
  End
  CrusherLevel           = 2
  CrushableLevel         = 2
  CommandSet          = {commandset}
  VoiceSelect         = DozerUSAVoiceSelect
  VoiceMove           = DozerUSAVoiceMove
  VoiceGuard          = DozerUSAVoiceMove
  VoiceTaskComplete   = DozerUSAVoiceBuildComplete
  SoundMoveStart      = DozerUSAMoveStart
  SoundMoveStartDamaged = DozerUSAMoveStart
  UnitSpecificSounds
    VoiceCreate           = DozerUSAVoiceCreate
    VoiceNoBuild          = DozerUSAVoiceBuildNot
    VoiceCrush            = DozerUSAVoiceCrush
    VoiceRepair           = DozerUSAVoiceRepair
    VoiceDisarm           = DozerUSAVoiceClearMine
    TruckLandingSound     = NoSound
    TruckPowerslideSound  = NoSound
    VoiceEnter            = DozerUSAVoiceMove
    VoiceBuildResponse    = DozerUSAVoiceBuild
  End
  RadarPriority       = UNIT
  KindOf              = PRELOAD VEHICLE SCORE SELECTABLE DOZER
  Body                = ActiveBody ModuleTag_02
    MaxHealth         = 250.0
    InitialHealth     = 250.0
    SubdualDamageCap = 500
    SubdualDamageHealRate = 500
    SubdualDamageHealAmount = 50
  End
  Behavior = DozerAIUpdate ModuleTag_03
    RepairHealthPercentPerSecond = 2%
    BoredTime                    = 5000
    BoredRange                   = 150
    AutoAcquireEnemiesWhenIdle   = Yes
  End
  Locomotor = SET_NORMAL AmericaVehicleDozerLocomotor
  Behavior            = PhysicsBehavior ModuleTag_04
    Mass              = 75.0
  End
  Behavior = StealthDetectorUpdate ModuleTag_05
    DetectionRate         = 500
    CanDetectWhileGarrisoned  = No
    CanDetectWhileContained   = No
    ExtraRequiredKindOf   = MINE
  End
  Behavior                 = TransitionDamageFX ModuleTag_06
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuous01
    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_BattleMasterDamageTransition
  End
  Behavior = SlowDeathBehavior ModuleTag_07
    DeathTypes = ALL -CRUSHED -SPLATTED
    ProbabilityModifier = 100
    DestructionDelay = 1500
    DestructionDelayVariance = 600
    FX  = INITIAL  FX_CrusaderCatchFire
    OCL = FINAL    OCL_AmericaDozerExplode
    FX  = FINAL    FX_BattleMasterExplosionOneFinal
  End
  Behavior = CreateCrateDie ModuleTag_CratesChange
    CrateData = SalvageCrateData
  End
  Behavior = FlammableUpdate ModuleTag_21
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
  End
  Behavior               = FXListDie ModuleTag_23
    DeathTypes = NONE +CRUSHED +SPLATTED
    DeathFX         = FX_CarCrush
  End
  Behavior = DestroyDie ModuleTag_24
    DeathTypes = NONE +CRUSHED +SPLATTED
  End
  Geometry            = BOX
  GeometryMajorRadius = 15.0
  GeometryMinorRadius = 10.0
  GeometryHeight      = 15.0
  GeometryIsSmall     = Yes
  Shadow              = SHADOW_VOLUME
  ShadowSizeX = 45
End
"""


def tunnel_object(side: str, name: str) -> str:
    src = (ROOT / "Data/INI/Object/Specter/Turkish Armed Forces/Buildings/PowerStation.ini").read_text(
        "latin1", "replace"
    )
    i = src.find("Object TurkeyPowerStationm")
    if i < 0:
        raise SystemExit("TurkeyPowerStationm missing")
    nxt = src.find("\nObject ", i + 1)
    body = src[i : nxt if nxt > 0 else None]
    body = body.replace("Object TurkeyPowerStationm", f"Object {name}", 1)
    body = re.sub(r"(?m)^(\s*Side\s*=\s*)Turkey\s*$", rf"\1{side}", body, count=1)
    body = re.sub(
        r"(?m)^(\s*CommandSet\s*=\s*)AmericaPowerPlantmCommandSet\s*$",
        r"\1SpecterSS2TunnelNetworkCommandSet",
        body,
        count=1,
    )
    if f"Side             = {side}" not in body and f"Side                = {side}" not in body:
        if not re.search(rf"(?m)^\s*Side\s*=\s*{re.escape(side)}\s*$", body):
            raise SystemExit(f"failed to retarget Side on {name}")
    if "TurkeyPowerStationm" in body or "Side             = Turkey" in body:
        raise SystemExit(f"Turkey leftovers in {name}")
    if "TunnelContain" not in body:
        raise SystemExit(f"TunnelContain missing from {name}")
    return body.strip() + "\n"


def emit_commandset(name: str, slot_lines: list[str]) -> str:
    lines = [f"CommandSet {name}"]
    lines.extend(slot_lines)
    lines.append("End")
    lines.append("")
    return "\n".join(lines)


def original_slot_lines(block: str) -> list[str]:
    lines = []
    for raw in block.splitlines():
        if re.match(r"^\s*\d+\s*=\s*\S+", raw):
            lines.append(raw.rstrip())
    return lines


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    existing = collect_existing_names()
    cs_map = load_winning_commandsets()
    plan = []
    new_names = {"Object": set(), "CommandSet": set(), "CommandButton": set()}

    cb_parts = [
        "; SPECTER SS2 tunnel-loader CommandButtons. Unique names only.",
        "; Loads before every CommandSet* file (CommandButton < CommandSet).",
        "",
    ]
    cs_parts = [
        "; SPECTER SS2 tunnel-loader CommandSets. Unique names only.",
        "; Sorts after CommandSet_ZZZZ_ZZZZZSupplyCentreBuyButtons.ini.",
        "",
        "CommandSet SpecterSS2TunnelNetworkCommandSet",
        "  1  = Command_StructureExit",
        "  2  = Command_StructureExit",
        "  3  = Command_StructureExit",
        "  4  = Command_StructureExit",
        "  5  = Command_StructureExit",
        "  6  = Command_StructureExit",
        "  7  = Command_StructureExit",
        "  8  = Command_StructureExit",
        "  9  = Command_StructureExit",
        "  10 = Command_StructureExit",
        "  11 = Command_Evacuate",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
        "End",
        "",
    ]
    new_names["CommandSet"].add("SpecterSS2TunnelNetworkCommandSet")
    obj_parts = [
        "; SPECTER SS2 tunnel-loader objects and Command Center CommandSet overlays.",
        "; Unique Object names. CC overlays merge CommandSet onto existing templates.",
        "; This filename sorts after Data\\INI\\Object\\ and after ZZZZZZZZ_* overlays.",
        "",
    ]

    reserved_buttons = {
        "Command_StructureExit",
        "Command_Evacuate",
        "Command_SetRallyPoint",
        "Command_Sell",
        "Command_TunnelEvacuate",
    }

    for fac in FACTIONS:
        orig_cs = find_object_commandset(fac["cc"])
        block = cs_map.get(orig_cs)
        if not block:
            raise SystemExit(f"winning CommandSet missing: {orig_cs}")
        sl = slots_of(block)
        used = {n for n, _ in sl}
        slot1 = next((b for n, b in sl if n == 1), None)
        if not slot1:
            raise SystemExit(f"{fac['side']} CommandSet {orig_cs} has no slot 1")
        slot = choose_slot(used)
        loader_btn = f"Command_Construct{fac['loader']}"
        tunnel_btn = f"Command_Construct{fac['tunnel']}"
        loader_cs = f"{fac['loader']}CommandSet"
        cc_cs = f"{orig_cs}_SpecterSS2TunnelLoader"
        for kind, name in (
            ("Object", fac["loader"]),
            ("Object", fac["tunnel"]),
            ("CommandButton", loader_btn),
            ("CommandButton", tunnel_btn),
            ("CommandSet", loader_cs),
            ("CommandSet", cc_cs),
        ):
            if name in existing[kind] or name in new_names[kind]:
                raise SystemExit(f"name collision {kind} {name}")
            new_names[kind].add(name)
        if "THAAD" in loader_cs or "NASAMS" in loader_cs:
            raise SystemExit("refused to copy Turkey extra buildings")

        cb_parts.append(f"CommandButton {loader_btn}")
        cb_parts.append("  Command       = UNIT_BUILD")
        cb_parts.append(f"  Object        = {fac['loader']}")
        cb_parts.append("  TextLabel     = CONTROLBAR:ConstructNatoVehicleDozerm")
        cb_parts.append("  ButtonImage   = SACDozerm")
        cb_parts.append("  ButtonBorderType        = BUILD")
        cb_parts.append("  DescriptLabel           = CONTROLBAR:ToolTipNatoVehicleDozer")
        cb_parts.append("End")
        cb_parts.append("")
        cb_parts.append(f"CommandButton {tunnel_btn}")
        cb_parts.append("  Command       = DOZER_CONSTRUCT")
        cb_parts.append(f"  Object        = {fac['tunnel']}")
        cb_parts.append("  TextLabel     = CONTROLBAR:ConstructTurkeyPowerStationm")
        cb_parts.append("  ButtonImage   = us_powerplantm")
        cb_parts.append("  ButtonBorderType        = BUILD")
        cb_parts.append("  DescriptLabel           = CONTROLBAR:ToolTipTurkeyPowerStationm")
        cb_parts.append("End")
        cb_parts.append("")

        cs_parts.append(emit_commandset(loader_cs, [f"  1   = {tunnel_btn}"]))
        copied = original_slot_lines(block)
        copied.append(f"  {slot} = {loader_btn}")
        copied_nums = [int(re.match(r"\s*(\d+)", line).group(1)) for line in copied]
        if copied_nums.count(slot) != 1:
            raise SystemExit(f"{fac['side']} slot {slot} not unique after insert")
        if 1 not in copied_nums:
            raise SystemExit(f"{fac['side']} lost slot 1")
        # Existing buttons except the newly added loader button must remain.
        orig_pairs = [(n, b) for n, b in sl]
        for n, b in orig_pairs:
            if (n, b) not in [(int(re.match(r"\s*(\d+)", line).group(1)), line.split("=")[1].strip()) for line in copied[:-1]]:
                # allow last-wins of duplicate slot numbers inside original
                pass
        orig_buttons = [b for _, b in sl]
        new_buttons = [line.split("=", 1)[1].strip() for line in copied]
        for b in orig_buttons:
            if b not in new_buttons:
                raise SystemExit(f"{fac['side']} dropped button {b}")
        if new_buttons.count(loader_btn) != 1:
            raise SystemExit(f"{fac['side']} loader button missing")
        cs_parts.append(emit_commandset(cc_cs, copied))

        obj_parts.append(loader_object(fac["side"], fac["loader"], loader_cs))
        obj_parts.append(tunnel_object(fac["side"], fac["tunnel"]))
        obj_parts.append(f"Object {fac['cc']}")
        obj_parts.append(f"  CommandSet = {cc_cs}")
        obj_parts.append("End")
        obj_parts.append("")

        plan.append(
            {
                "side": fac["side"],
                "cc": fac["cc"],
                "orig_cs": orig_cs,
                "new_cs": cc_cs,
                "slot": slot,
                "slot1": slot1,
                "loader": fac["loader"],
                "tunnel": fac["tunnel"],
                "loader_btn": loader_btn,
                "tunnel_btn": tunnel_btn,
                "loader_cs": loader_cs,
                "orig_slots": sl,
            }
        )

    forbidden_res = (
        r"(?m)^Object\s+Turkey(VehicleDozer|VehicleDozerm|PowerStationm)\s*$",
        r"(?m)^CommandSet\s+TurkeyDozermCommandSet\s*$",
        r"(?m)^CommandButton\s+Command_ConstructTurkey(VehicleDozer|VehicleDozerm|PowerStationm)\s*$",
        r"Command_ConstructAmericaVehicleTHAAD_AI",
        r"Command_ConstructTurkeyNASAMSIII",
        r"Command_ConstructTurkeySkySabre",
        r"Command_ConstructTurkeySkyranger30",
    )
    cb_text = "\n".join(cb_parts).rstrip() + "\n"
    cs_text = "\n".join(cs_parts).rstrip() + "\n"
    obj_text = "\n".join(obj_parts).rstrip() + "\n"
    for label, text in (("CB", cb_text), ("CS", cs_text), ("OBJ", obj_text)):
        for tok in forbidden_res:
            if re.search(tok, text):
                raise SystemExit(f"{label} contains forbidden token {tok}")

    (GEN_DIR / "CommandButton_zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini").write_bytes(crlf(cb_text))
    (GEN_DIR / "CommandSet_zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini").write_bytes(crlf(cs_text))
    (GEN_DIR / "zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini").write_bytes(crlf(obj_text))

    # Load-order guarantees (case-insensitive Windows/ZH).
    def k(s: str) -> str:
        return s.replace("\\", "/").lower()

    if not (k(CB_MEMBER) < k(r"Data\INI\CommandSet.ini") < k(CS_MEMBER)):
        raise SystemExit("CommandButton file would not parse before CommandSets")
    last_loose_cs = r"Data\INI\CommandSet_ZZZZ_ZZZZZSupplyCentreBuyButtons.ini"
    if not (k(CS_MEMBER) > k(last_loose_cs)):
        raise SystemExit("CommandSet file would not sort after MatchStart/ZZZZ sets")
    usa_cc = r"Data\INI\Object\Specter\United States Of America\Buildings\CommandCenter.ini"
    zzzz_obj = r"Data\INI\ZZZZZZZZ_America_StrategyCenter_Restore.ini"
    if not (k(OBJ_MEMBER) > k(usa_cc) and k(OBJ_MEMBER) > k(zzzz_obj)):
        raise SystemExit("Object overlay would not sort after live CC definitions")

    original = SRC_BIG.read_bytes()
    items = list(iter_big_members(original))
    orig_map = {name: blob for name, blob in items}
    for member in (CB_MEMBER, CS_MEMBER, OBJ_MEMBER):
        if any(n.replace("\\", "/").lower() == member.replace("\\", "/").lower() for n, _ in items):
            raise SystemExit(f"{member} already in DATA BIG")
    new_items = items + [
        (CB_MEMBER, crlf(cb_text)),
        (CS_MEMBER, crlf(cs_text)),
        (OBJ_MEMBER, crlf(obj_text)),
    ]
    packed = build_big_ordered(new_items)
    out_big = OUT_DIR / "_SPEC_DATA_ONE.big"
    out_big.write_bytes(packed)

    packed_map = {n: b for n, b in iter_big_members(packed)}
    for name in FORBIDDEN_MEMBERS:
        if name in orig_map:
            if packed_map.get(name) != orig_map[name]:
                raise SystemExit(f"forbidden member mutated: {name}")
    for member, blob in (
        (CB_MEMBER, crlf(cb_text)),
        (CS_MEMBER, crlf(cs_text)),
        (OBJ_MEMBER, crlf(obj_text)),
    ):
        if packed_map.get(member) != blob:
            raise SystemExit(f"packed member mismatch {member}")
    if len(packed_map) != len(orig_map) + 3:
        raise SystemExit("unexpected member count")

    # Reference check inside generated files.
    defined_buttons = set(parse_blocks(cb_text, "CommandButton")) | existing["CommandButton"] | reserved_buttons
    for name, block in parse_blocks(cs_text, "CommandSet").items():
        for _, btn in slots_of(block):
            if btn not in defined_buttons:
                raise SystemExit(f"CommandSet {name} refs missing button {btn}")
    for fac in plan:
        if f"Side                = {fac['side']}" not in obj_text and not re.search(
            rf"Object {fac['loader']}.*?Side\s*=\s*{fac['side']}", obj_text, re.S
        ):
            raise SystemExit(f"loader Side mismatch {fac['side']}")
        if f"Object {fac['tunnel']}" not in obj_text:
            raise SystemExit(f"tunnel object missing {fac['tunnel']}")
        if f"Object {fac['cc']}\r\n  CommandSet = {fac['new_cs']}" not in crlf(obj_text).decode("latin1") and (
            f"Object {fac['cc']}\n  CommandSet = {fac['new_cs']}" not in obj_text
        ):
            raise SystemExit(f"CC overlay missing {fac['cc']}")

    zip_path = OUT_DIR / "SPECTER_SS2_TUNNEL_LOADER_ALL_FACTIONS.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        names = zf.namelist()
        if names != ["_SPEC_DATA_ONE.big"]:
            raise SystemExit(f"ZIP contents {names}")

    report = []
    report.append("SS2 tunnel loader transfer")
    report.append(f"base BIG: {SRC_BIG}")
    report.append(f"out BIG:  {out_big}  {out_big.stat().st_size}")
    report.append(f"SHA-256 BIG: {sha256(out_big)}")
    report.append(f"SHA-256 ZIP: {sha256(zip_path)}")
    report.append(f"ZIP: {zip_path}  {zip_path.stat().st_size}")
    report.append("")
    report.append(f"{'Side':24s} {'CC':32s} {'slot':4s} {'slot1 kept':40s} loader / tunnel")
    for fac in plan:
        report.append(
            f"{fac['side']:24s} {fac['cc']:32s} {fac['slot']:<4d} {fac['slot1']:40s} {fac['loader']} / {fac['tunnel']}"
        )
    (OUT_DIR / "BUILD_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
