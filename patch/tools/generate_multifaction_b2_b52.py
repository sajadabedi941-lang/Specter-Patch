#!/usr/bin/env python3
"""Generate multi-faction AAB B-2/B-52 access with country cost tiers."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

USA_B2_COST, USA_B2_TIME = 14000, 95.0
USA_B52_COST, USA_B52_TIME = 13000, 90.0
MAJOR_COST_MULT, MAJOR_TIME_MULT = 2.0, 1.35
OTHER_COST_MULT, OTHER_TIME_MULT = 3.5, 1.70

MAJOR = {"Russia", "China", "Britain", "France", "Germany", "Nato"}

# (object_prefix, Side, CommandSet prefix)
FACTIONS = [
    ("Russia", "Russia", "Russia"),
    ("China", "China", "China"),
    ("Britain", "Britain", "Britain"),
    ("France", "France", "France"),
    ("Germany", "Germany", "Germany"),
    ("Nato", "Nato", "Nato"),
    ("Japan", "Japan", "Japan"),
    ("Turkey", "Turkey", "Turkey"),
    ("Saudi", "SaudiArabia", "SaudiArabia"),
    ("India", "India", "India"),
    ("UAE", "UAE", "UAE"),
    ("Pakistan", "Pakistan", "Pakistan"),
    ("Ukraine", "Ukraine", "Ukraine"),
    ("Iran", "Iran", "Iran"),
    ("Iraq", "Iraq", "Iraq"),
    ("NK", "NorthKorea", "NorthKorea"),
    ("Egypt", "Egypt", "Egypt"),
    ("Syria", "Syria", "Syria"),
    ("Libya", "Libya", "Libya"),
    ("Vietnam", "Vietnam", "Vietnam"),
    ("SouthAfrica", "SouthAfrica", "SouthAfrica"),
    ("Italy", "Italy", "Italy"),
    ("Sweden", "Sweden", "Sweden"),
    ("SouthKorea", "SouthKorea", "SouthKorea"),
    ("Taiwan", "Taiwan", "Taiwan"),
    ("UN", "UN", "UN"),
    ("GLA", "GLA", "GLA"),
]

B2_DRAW = """
  SelectPortrait         = us_b1r
  ButtonImage            = us_b1r
  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model               = US_B1R
      WeaponLaunchBone = PRIMARY Weapon01
    End
    ConditionState        = JETEXHAUST
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End
    ConditionState        = JETEXHAUST JETAFTERBURNER
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
      ShowSubObject       = BurnerFX03 BurnerFX04
      ParticleSysBone     = Engine01 JetLenzflare
      ParticleSysBone     = Engine02 JetLenzflare
      ParticleSysBone     = Engine03 JetLenzflare
      ParticleSysBone     = Engine04 JetLenzflare
    End
    ConditionState        = REALLYDAMAGED
      Model               = US_B1R
      ParticleSysBone     = Smoke01 JetSmoke
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
    End
    ConditionState        = REALLYDAMAGED JETEXHAUST
      Model               = US_B1R
      ParticleSysBone     = Smoke01 JetSmoke
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End
    ConditionState        = REALLYDAMAGED JETEXHAUST JETAFTERBURNER
      Model               = US_B1R
      ParticleSysBone     = Smoke01 JetSmoke
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
      ShowSubObject       = BurnerFX03 BurnerFX04
      ParticleSysBone     = Engine01 JetLenzflare
      ParticleSysBone     = Engine02 JetLenzflare
      ParticleSysBone     = Engine03 JetLenzflare
      ParticleSysBone     = Engine04 JetLenzflare
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End
    ConditionState        = RUBBLE
      Model               = US_B1R
      HideSubObject       = None
      ShowSubObject       = None
    End
    ConditionState        = RUBBLE JETEXHAUST JETAFTERBURNER
      Model               = US_B1R
      HideSubObject       = None
      ShowSubObject       = None
      ParticleSysBone     = Engine01 JetLenzflare
      ParticleSysBone     = Engine02 JetLenzflare
      ParticleSysBone     = Engine03 JetLenzflare
      ParticleSysBone     = Engine04 JetLenzflare
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End
    OkToChangeModelColor = Yes
  End
"""

B52_DRAW = """
  SelectPortrait = us_b52h
  ButtonImage = us_b52h
  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model = US_B52H
      WeaponLaunchBone = PRIMARY WeaponA01
      ParticleSysBone = Engine02 HighAltitudeJetContrail
      ParticleSysBone = Engine03 HighAltitudeJetContrail
      ParticleSysBone = Engine04 HighAltitudeJetContrail
      ParticleSysBone = Engine05 HighAltitudeJetContrail
      ParticleSysBone = Engine06 HighAltitudeJetContrail
      ParticleSysBone = Engine07 HighAltitudeJetContrail
      ParticleSysBone = Engine08 HighAltitudeJetContrail
    End
    ConditionState = JETEXHAUST
      ParticleSysBone = Wingtip01 JetContrail
      ParticleSysBone = Wingtip02 JetContrail
    End
    ConditionState = DAMAGED
      Model = US_B52H
      ParticleSysBone = Smoke01 JetFireLarge
      ParticleSysBone = Smoke02 JetFireLarge
      ParticleSysBone = Engine02 HighAltitudeJetContrail
      ParticleSysBone = Engine03 JetBlackTrailThin
      ParticleSysBone = Engine04 HighAltitudeJetContrail
      ParticleSysBone = Engine05 HighAltitudeJetContrail
      ParticleSysBone = Engine06 HighAltitudeJetContrail
      ParticleSysBone = Engine07 HighAltitudeJetContrail
      ParticleSysBone = Engine08 HighAltitudeJetContrail
      ParticleSysBone = Smoke01 JetSmokeLarge
      ParticleSysBone = Smoke02 JetSmokeLarge
    End
    ConditionState = REALLYDAMAGED
      Model = US_B52H
      ParticleSysBone = Smoke01 JetFireLarge
      ParticleSysBone = Smoke02 JetFireLarge
      ParticleSysBone = Engine02 JetBlackTrailThin
      ParticleSysBone = Engine03 JetBlackTrailThin
      ParticleSysBone = Engine04 JetBlackTrailThin
      ParticleSysBone = Engine05 HighAltitudeJetContrail
      ParticleSysBone = Engine06 HighAltitudeJetContrail
      ParticleSysBone = Engine07 HighAltitudeJetContrail
      ParticleSysBone = Engine08 HighAltitudeJetContrail
      ParticleSysBone = Smoke01 JetSmokeLarge
      ParticleSysBone = Smoke02 JetSmokeLarge
    End
    ConditionState = RUBBLE
      Model = US_B52H
      ParticleSysBone = Smoke01 JetFireLarge
      ParticleSysBone = Smoke02 JetSmokeLarge
    End
    OkToChangeModelColor = Yes
  End
"""


def tier_of(prefix: str) -> str:
    return "major" if prefix in MAJOR else "other"


def costs(prefix: str, kind: str) -> tuple[int, float]:
    if kind == "B2":
        base_c, base_t = USA_B2_COST, USA_B2_TIME
    else:
        base_c, base_t = USA_B52_COST, USA_B52_TIME
    if tier_of(prefix) == "major":
        return int(round(base_c * MAJOR_COST_MULT)), round(base_t * MAJOR_TIME_MULT, 1)
    return int(round(base_c * OTHER_COST_MULT)), round(base_t * OTHER_TIME_MULT, 1)


def make_object(prefix: str, side: str, kind: str, cost: int, time: float) -> str:
    obj = f"Patch_{prefix}_{kind}"
    draw = B2_DRAW if kind == "B2" else B52_DRAW
    label = "B-2 Spirit" if kind == "B2" else "B-52H"
    vision = 480 if kind == "B2" else 450
    hp = 850.0 if kind == "B2" else 950.0
    tier = tier_of(prefix)
    return f"""
; Multi-faction AAB strategic bomber - {label} for {side}
; Tier={tier} cost scaling from USA base; Max 1 strategic bomber (shared link key)
Object {obj}
; PatchBaseCost = {cost}
; PatchBaseTime = {time}
Scale = 0.72
{draw}
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  TransportSlotCount = 0
  VisionRange = {vision}
  ShroudClearingRange = 220
  BuildCost           = {cost}
  BuildTime           = {time}
  MaxSimultaneousOfType = 1
  MaxSimultaneousLinkKey = Patch_StrategicBomber
  WeaponSet
    Conditions = None
    Weapon = PRIMARY GBU38_JDAM_F16C
  End
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  ExperienceValue = 80 80 120 160
  IsTrainable = Yes
  CommandSet = GenericTacticalBomberCommandSet
  SoundAmbient = B52AmbientLoop
  SoundAmbientRubble = NoSound
  RadarPriority = UNIT
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT CAN_ATTACK
  Body = ActiveBody ModuleTag_02
    MaxHealth = {hp}
    InitialHealth = {hp}
  End
  Behavior = PhysicsBehavior ModuleTag_03
    Mass = 500.0
  End
  Behavior = JetAIUpdate ModuleTag_04
    OutOfAmmoDamagePerSecond = 8%
    TakeoffDistForMaxLift = 0%
    TakeoffPause = 500
    MinHeight = 5
    ParkingOffset = 5
    ReturnToBaseIdleTime = 12000
  End
  Locomotor = SET_NORMAL B52HLocomotor
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor
  Behavior = JetSlowDeathBehavior ModuleTag_05
    DestructionDelay = 99999999
    RollRate = 0.2
    RollRateDelta = 100%
    PitchRate = 0.0
    FallHowFast = 110.0%
    FXInitialDeath = FX_JetBigDeathInitial
    OCLInitialDeath = OCL_AmericaJetSlowDeathInitial
  End
  Behavior = ProductionUpdate ModuleTag_06
  End
  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 36.0
  GeometryMinorRadius = 12.0
  GeometryHeight = 18.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""


def add_to_commandset(path: Path, cs_name: str, prefix: str) -> bool:
    text = path.read_text("latin-1")
    pat = re.compile(rf"(^CommandSet {re.escape(cs_name)}\n)([\s\S]*?)(^End\s*$)", re.M)
    m = pat.search(text)
    if not m:
        print("MISSING CS", cs_name, "in", path)
        return False
    header, body, end = m.group(1), m.group(2), m.group(3)
    body = re.sub(rf"^\s*\d+\s*=\s*Command_ConstructPatch_{prefix}_B2\s*\n", "", body, flags=re.M)
    body = re.sub(rf"^\s*\d+\s*=\s*Command_ConstructPatch_{prefix}_B52\s*\n", "", body, flags=re.M)
    body = re.sub(r"^\s*; Multi-faction strategic bombers \(B-2 / B-52\)\s*\n", "", body, flags=re.M)
    used = {int(x) for x in re.findall(r"^\s*(\d+)\s*=", body, re.M)}
    free: list[int] = []
    for i in range(15, 40):
        if i not in used:
            free.append(i)
        if len(free) >= 2:
            break
    if len(free) < 2:
        print("NO SLOTS", cs_name, used)
        return False
    s1, s2 = free[0], free[1]
    insert = (
        "\n  ; Multi-faction strategic bombers (B-2 / B-52)\n"
        f"  {s1} = Command_ConstructPatch_{prefix}_B2\n"
        f"  {s2} = Command_ConstructPatch_{prefix}_B52\n"
    )
    new_body = body.rstrip() + insert + "\n"
    text = text[: m.start()] + header + new_body + end + text[m.end() :]
    path.write_text(text, encoding="latin-1")
    print(f"Wired {cs_name} slots {s1}/{s2}")
    return True


def patch_america(text: str, obj: str, cost: int, time: float) -> str:
    s = text.find(f"Object {obj}")
    if s < 0:
        raise SystemExit("missing " + obj)
    n = text.find("\nObject ", s + 10)
    block = text[s:n]
    block2 = re.sub(r"^(\s*BuildCost\s*=\s*)\S+", rf"\g<1>{cost}", block, count=1, flags=re.M)
    block2 = re.sub(r"^(\s*BuildTime\s*=\s*)\S+", rf"\g<1>{time}", block2, count=1, flags=re.M)
    if re.search(r"^\s*MaxSimultaneousOfType\s*=", block2, re.M):
        block2 = re.sub(r"^(\s*MaxSimultaneousOfType\s*=\s*)\S+", r"\g<1>1", block2, count=1, flags=re.M)
    else:
        block2 = re.sub(
            r"(BuildTime\s*=\s*\S+\n)",
            r"\1  MaxSimultaneousOfType = 1\n",
            block2,
            count=1,
        )
    if re.search(r"^\s*MaxSimultaneousLinkKey\s*=", block2, re.M):
        block2 = re.sub(
            r"^(\s*MaxSimultaneousLinkKey\s*=\s*)\S+",
            r"\g<1>Patch_StrategicBomber",
            block2,
            count=1,
            flags=re.M,
        )
    else:
        block2 = re.sub(
            r"(MaxSimultaneousOfType\s*=\s*\S+\n)",
            r"\1  MaxSimultaneousLinkKey = Patch_StrategicBomber\n",
            block2,
            count=1,
        )
    return text[:s] + block2 + text[n:]


def main() -> int:
    out_ini = ROOT / "Data/INI/Object/Specter/PatchSystems/AdvancedAirBase/Aircraft_AAB_StrategicBombers.ini"
    chunks = [
        "; SPECTER PATCH - Multi-faction B-2 / B-52 Advanced Air Base access\n"
        "; USA objects remain Patch_America_B2 / Patch_America_B52 in Aircraft_AAB_Global.ini\n"
        "; Cost tiers: USA=base, Major(Russia/China/Britain/France/Germany/Nato)=x2, Others=x3.5\n"
        "; Limit: MaxSimultaneousOfType=1 with MaxSimultaneousLinkKey=Patch_StrategicBomber\n"
        "; Scale=0.72; Weapon=GBU38_JDAM_F16C\n"
    ]
    buttons: list[str] = []
    strings: list[str] = []
    for prefix, side, _cs in FACTIONS:
        for kind in ("B2", "B52"):
            c, t = costs(prefix, kind)
            chunks.append(make_object(prefix, side, kind, c, t))
            obj = f"Patch_{prefix}_{kind}"
            cmd = f"Command_Construct{obj}"
            img = "us_b1r" if kind == "B2" else "us_b52h"
            label = "B-2" if kind == "B2" else "B-52"
            buttons.append(
                f"CommandButton {cmd}\n"
                f"  Command       = UNIT_BUILD\n"
                f"  Object        = {obj}\n"
                f"  TextLabel     = CONTROLBAR:Construct{obj}\n"
                f"  ButtonImage   = {img}\n"
                f"  ButtonBorderType = BUILD\n"
                f"  DescriptLabel = CONTROLBAR:ToolTipConstruct{obj}\n"
                f"End\n"
            )
            strings.append(f"OBJECT:{obj} = {label}")
            strings.append(f"CONTROLBAR:Construct{obj} = {label}")
            strings.append(
                f"CONTROLBAR:ToolTipConstruct{obj} = Produce {label} from Advanced Air Base ({side}). "
                f"Expensive imported strategic bomber. Max 1."
            )

    out_ini.write_text("\n".join(chunks) + "\n", encoding="ascii")
    print("Wrote", out_ini, "objects", len(FACTIONS) * 2)

    btn_path = ROOT / "Data/INI/CommandButton_AdvancedAirBase_Aircraft.ini"
    btn_text = btn_path.read_text("latin-1")
    marker = "; ---- Multi-faction B-2 / B-52 AAB access ----"
    if marker in btn_text:
        btn_text = btn_text.split(marker)[0].rstrip() + "\n"
    btn_path.write_text(btn_text.rstrip() + "\n\n" + marker + "\n" + "\n".join(buttons), encoding="latin-1")
    print("Buttons appended", len(buttons))

    str_path = ROOT / "Data/English/AdvancedAirBase_Strings.txt"
    str_text = str_path.read_text("latin-1")
    smarker = "; ---- Multi-faction B-2 / B-52 ----"
    if smarker in str_text:
        str_text = str_text.split(smarker)[0].rstrip() + "\n"
    str_text = str_text.replace(
        "CONTROLBAR:ToolTipConstructPatch_America_B2 = Produce B-2 from Advanced Air Base (America).",
        "CONTROLBAR:ToolTipConstructPatch_America_B2 = Produce B-2 from Advanced Air Base (America). Max 1 strategic bomber.",
    ).replace(
        "CONTROLBAR:ToolTipConstructPatch_America_B52 = Produce B-52 from Advanced Air Base (America).",
        "CONTROLBAR:ToolTipConstructPatch_America_B52 = Produce B-52 from Advanced Air Base (America). Max 1 strategic bomber.",
    )
    str_path.write_text(str_text.rstrip() + "\n\n" + smarker + "\n" + "\n".join(strings) + "\n", encoding="latin-1")
    print("Strings updated")

    cs_aab = ROOT / "Data/INI/CommandSet_AdvancedAirBase.ini"
    cs_tur = ROOT / "Data/INI/CommandSet_Turkey.ini"
    for prefix, _side, cs_prefix in FACTIONS:
        path = cs_tur if cs_prefix == "Turkey" else cs_aab
        add_to_commandset(path, f"{cs_prefix}_AdvancedAirBaseCommandSet", prefix)

    aab = ROOT / "Data/INI/Object/Specter/PatchSystems/AdvancedAirBase/Aircraft_AAB_Global.ini"
    text = aab.read_text("latin-1")
    text = patch_america(text, "Patch_America_B2", USA_B2_COST, USA_B2_TIME)
    text = patch_america(text, "Patch_America_B52", USA_B52_COST, USA_B52_TIME)
    text = text.replace(
        "Keeps Patch_America_B2 id, AAB USA-only access, GBU38 weapon, Scale 0.72 runway budget",
        "Patch_America_B2 USA base-price strategic bomber; GBU38; Scale 0.72; Max 1 via Patch_StrategicBomber",
    )
    aab.write_text(text, encoding="latin-1")
    print("Updated America B2/B52 costs/limits")

    cs = cs_aab.read_text("latin-1")
    assert "Command_ConstructPatch_America_B2" in cs
    assert "Command_ConstructPatch_America_B52" in cs
    print("America access preserved")
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
