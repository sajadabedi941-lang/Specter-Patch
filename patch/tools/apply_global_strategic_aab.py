#!/usr/bin/env python3
"""Global Advanced Air Base strategic aircraft system.

- Override airfield CommandSets to remove GenStar strategic bomber builds
- Fix Russia/China heavy aircraft identity (correct W3D)
- Add America B-1 + Russia Tu-95
- Scale heavies 0.65-0.75, strengthen AWACS, country cost tiers
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AAB = ROOT / "Data/INI/Object/Specter/PatchSystems/AdvancedAirBase/Aircraft_AAB_Global.ini"
CS_AAB = ROOT / "Data/INI/CommandSet_AdvancedAirBase.ini"
CS_OVERRIDE = ROOT / "Data/INI/CommandSet_StrategicBombers_AABOnly.ini"
BTN = ROOT / "Data/INI/CommandButton_AdvancedAirBase_Aircraft.ini"
STR = ROOT / "Data/English/AdvancedAirBase_Strings.txt"
STOCK_CS = Path("/tmp/stock_commandset_airfields.txt")

HEAVY_SCALE = 0.72
AWACS_SCALE = 0.70
SUPPORT_SCALE = 0.68

# AWACS strength targets
AWACS_VISION = 950
AWACS_SHROUD = 850
AWACS_HP = 1850
AWACS_COST_USA = 8500
AWACS_TIME = 75.0

BOMBER_STRIP = re.compile(
    r"B2Spirit|JetB52H|JetB1R|Tu22M3M|Tu-22M3M|Tu160|BomberH6|JetB52\b|AmericaJetB2|AmericaJetB52|AmericaJetB1",
    re.I,
)


def extract_cs(text: str, name: str) -> str | None:
    m = re.search(rf"^CommandSet {re.escape(name)}\n([\s\S]*?)^End\s*$", text, re.M)
    return m.group(0) if m else None


def strip_strategic_bombers(cs_block: str) -> str:
    lines = []
    for line in cs_block.splitlines():
        raw = line.split(";", 1)[0]
        if BOMBER_STRIP.search(raw):
            # comment out rather than delete (keeps slot docs)
            if line.lstrip().startswith(";"):
                lines.append(line)
            else:
                lines.append("; AAB-only strategic bomber removed: " + line.lstrip())
            continue
        lines.append(line)
    return "\n".join(lines)


def write_airfield_overrides() -> None:
    stock = STOCK_CS.read_text("latin-1")
    names = [
        "AmericaAirfieldCommandSet",
        "AmericaAirfieldCommandSet_T",
        "AmericaAirfieldCommandSet_T1",
        "AmericaAirfieldCommandSet_T2",
        "AmericaAirfieldCommandSet_T3",
        "RussiaAirfieldCommandSet",
        "ChinaAirfieldCommandSet",
    ]
    out = [
        "; SPECTER PATCH - Strategic bombers are Advanced Air Base only",
        "; Redefines stock airfield CommandSets without GenStar strategic bomber builds",
        "; (CommandSet.ini is stock-skipped in BIG merge; this override file is merged.)",
        "",
    ]
    for name in names:
        block = extract_cs(stock, name)
        if not block:
            print("WARN missing stock CS", name)
            continue
        out.append(strip_strategic_bombers(block))
        out.append("")
        print("Override", name)
    CS_OVERRIDE.write_text("\n".join(out) + "\n", encoding="ascii")


def jet_draw(model: str, bone: str = "WeaponA01", engines: int = 2) -> str:
    eng = "\n".join(f"      ParticleSysBone     = Engine{i:02d} JetLenzflare" for i in range(1, engines + 1))
    return f"""  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model               = {model}
      WeaponLaunchBone = PRIMARY {bone}
    End
    ConditionState        = JETEXHAUST
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End
    ConditionState        = JETEXHAUST JETAFTERBURNER
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
{eng}
    End
    ConditionState        = REALLYDAMAGED
      Model               = {model}
      ParticleSysBone     = Smoke01 JetSmoke
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
    End
    ConditionState        = REALLYDAMAGED JETEXHAUST
      Model               = {model}
      ParticleSysBone     = Smoke01 JetSmoke
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End
    ConditionState        = RUBBLE
      Model               = {model}
      HideSubObject       = None
      ShowSubObject       = None
    End
    OkToChangeModelColor = Yes
  End
"""


def replace_draw(block: str, model: str, bone: str, engines: int) -> str:
    draw = jet_draw(model, bone, engines)
    block2, n = re.subn(
        r"^\s*Draw\s*=\s*W3DModelDraw[\s\S]*?^\s*OkToChangeModelColor\s*=\s*Yes\s*\n\s*End",
        draw.rstrip(),
        block,
        count=1,
        flags=re.M,
    )
    if n != 1:
        block2, n = re.subn(
            r"^\s*Draw\s*=\s*W3DModelDraw ModuleTag_01\n[\s\S]*?^\s*End\n(?=\s*DisplayName|\s*;|\s*EditorSorting)",
            draw,
            block,
            count=1,
            flags=re.M,
        )
    if n != 1:
        raise RuntimeError(f"Draw replace failed n={n}")
    return block2


def set_field(block: str, key: str, value: str) -> str:
    if re.search(rf"^\s*{re.escape(key)}\s*=", block, re.M):
        return re.sub(rf"(^\s*{re.escape(key)}\s*=\s*)\S+", rf"\g<1>{value}", block, count=1, flags=re.M)
    # insert after Scale if present
    if re.search(r"^Scale\s*=", block, re.M):
        return re.sub(r"(^Scale\s*=\s*\S+\n)", rf"\1  {key} = {value}\n", block, count=1, flags=re.M)
    return block


def patch_object_block(text: str, obj: str, **fields) -> str:
    s = text.find(f"Object {obj}")
    if s < 0:
        print("MISSING", obj)
        return text
    n = text.find("\nObject ", s + 10)
    if n < 0:
        n = len(text)
    block = text[s:n]
    if "model" in fields:
        block = replace_draw(block, fields["model"], fields.get("bone", "WeaponA01"), fields.get("engines", 2))
    for k in ("SelectPortrait", "ButtonImage", "CommandSet", "Scale", "BuildCost", "BuildTime", "VisionRange", "ShroudClearingRange"):
        fk = k
        if k == "SelectPortrait" and "portrait" in fields:
            block = set_field(block, "SelectPortrait", fields["portrait"])
            block = set_field(block, "ButtonImage", fields["portrait"])
        elif k in fields:
            block = set_field(block, k, str(fields[k]))
    if "MaxHealth" in fields:
        block = re.sub(
            r"(Body\s*=\s*ActiveBody[\s\S]*?MaxHealth\s*=\s*)\S+",
            rf"\g<1>{fields['MaxHealth']}",
            block,
            count=1,
        )
        block = re.sub(
            r"(Body\s*=\s*ActiveBody[\s\S]*?InitialHealth\s*=\s*)\S+",
            rf"\g<1>{fields['MaxHealth']}",
            block,
            count=1,
        )
    if "MaxSimultaneousOfType" in fields:
        block = set_field(block, "MaxSimultaneousOfType", str(fields["MaxSimultaneousOfType"]))
    if "MaxSimultaneousLinkKey" in fields:
        block = set_field(block, "MaxSimultaneousLinkKey", fields["MaxSimultaneousLinkKey"])
    if "SPECTER GLOBAL STRATEGIC" not in block:
        block = block.replace(f"Object {obj}\n", f"Object {obj}\n; SPECTER GLOBAL STRATEGIC AAB\n", 1)
    return text[:s] + block + text[n:]


def make_strategic_object(
    obj: str,
    side: str,
    model: str,
    portrait: str,
    cost: int,
    time: float,
    scale: float,
    weapon: str,
    cmd: str,
    hp: float,
    vision: float,
    bone: str = "WeaponA01",
    engines: int = 2,
    link: str = "Patch_StrategicBomber",
) -> str:
    return f"""
; Global strategic AAB unit
Object {obj}
; SPECTER GLOBAL STRATEGIC AAB
; PatchBaseCost = {cost}
; PatchBaseTime = {time}
Scale = {scale}
  SelectPortrait = {portrait}
  ButtonImage = {portrait}
{jet_draw(model, bone, engines)}
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  TransportSlotCount = 0
  VisionRange = {vision}
  ShroudClearingRange = 220
  BuildCost           = {cost}
  BuildTime           = {time}
  MaxSimultaneousOfType = 1
  MaxSimultaneousLinkKey = {link}
  WeaponSet
    Conditions = None
    Weapon = PRIMARY {weapon}
  End
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  ExperienceValue = 80 80 120 160
  IsTrainable = Yes
  CommandSet = {cmd}
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


def strengthen_all_awacs(text: str) -> str:
    for m in re.finditer(r"^Object (Patch_\S+)\s*$", text, re.M):
        name = m.group(1)
        # AWACS naming patterns
        if not re.search(r"(E3|A50|AWACS|E767|E2C|KJ2000|AN71)$", name) and "AWACS" not in name and not name.endswith("_E3") and not name.endswith("_E3D") and not name.endswith("_E7"):
            if name not in ("Patch_America_E3", "Patch_Russia_A50", "Patch_China_KJ2000", "Patch_Britain_E3D", "Patch_Japan_E767", "Patch_Saudi_E3", "Patch_Turkey_E7", "Patch_Ukraine_A50U"):
                continue
        s = m.start()
        n = text.find("\nObject ", s + 10)
        if n < 0:
            n = len(text)
        block = text[s:n]
        # must look like AWACS (Patch_AWACS command or high vision already)
        if "AWACS" not in block and "Patch_AWACS" not in block and "E3G" not in block and "A50" not in block:
            # still apply if name matched
            pass
        side_m = re.search(r"Side\s*=\s*(\S+)", block)
        side = side_m.group(1) if side_m else "America"
        # cost tier
        if side == "America":
            cost = AWACS_COST_USA
        elif side in ("Russia", "China", "Britain", "France", "Germany", "Nato"):
            cost = int(AWACS_COST_USA * 1.35)
        else:
            cost = int(AWACS_COST_USA * 2.2)
        block = set_field(block, "Scale", str(AWACS_SCALE))
        block = set_field(block, "VisionRange", str(AWACS_VISION))
        block = set_field(block, "ShroudClearingRange", str(AWACS_SHROUD))
        block = set_field(block, "BuildCost", str(cost))
        block = set_field(block, "BuildTime", str(AWACS_TIME))
        block = re.sub(
            r"(Body\s*=\s*ActiveBody[\s\S]*?MaxHealth\s*=\s*)\S+",
            rf"\g<1>{AWACS_HP}.0",
            block,
            count=1,
        )
        block = re.sub(
            r"(Body\s*=\s*ActiveBody[\s\S]*?InitialHealth\s*=\s*)\S+",
            rf"\g<1>{AWACS_HP}.0",
            block,
            count=1,
        )
        if "SPECTER AWACS BUFF" not in block:
            block = block.replace(f"Object {name}\n", f"Object {name}\n; SPECTER AWACS BUFF - longer radar, tougher, expensive\n", 1)
        text = text[:s] + block + text[n:]
        print("AWACS buff", name, "cost", cost)
    return text


def scale_heavies(text: str) -> str:
    """Scale bombers/tankers/transports into 0.65-0.75 runway band."""
    heavy_re = re.compile(
        r"Patch_\w+_(B2|B52|B21|B1|B3|Tu160|Tu95|Tu22M3|H6|HeavyBomber|MediumBomber|"
        r"KC135|KC135R|KC767|C17|Il78|Il76|HY6|Y20|Tanker|Transport|Voyager)$"
    )
    for m in re.finditer(r"^Object (Patch_\S+)\s*$", text, re.M):
        name = m.group(1)
        if not heavy_re.search(name) and not re.search(
            r"_(B2|B52|Tu160|Tu95|Tu22|H6|Tanker|Transport|KC|C17|Il7|HY6|Y20|Voyager)$", name
        ):
            continue
        if "AWACS" in name or name.endswith("_E3") or name.endswith("_A50") or "KJ2000" in name:
            continue
        s = m.start()
        n = text.find("\nObject ", s + 10)
        if n < 0:
            n = len(text)
        block = text[s:n]
        # choose scale
        if re.search(r"Tanker|Transport|KC|C17|Il7|HY6|Y20|Voyager", name):
            sc = SUPPORT_SCALE
        else:
            sc = HEAVY_SCALE
        old = re.search(r"^Scale\s*=\s*(\S+)", block, re.M)
        if old and abs(float(old.group(1)) - sc) < 0.001:
            continue
        block = set_field(block, "Scale", str(sc))
        text = text[:s] + block + text[n:]
        print("Scale", name, "->", sc)
    return text


def ensure_america_b1(text: str) -> str:
    if "Object Patch_America_B1" in text:
        return text
    # insert after Patch_America_B52 block
    s = text.find("Object Patch_America_B52")
    n = text.find("\nObject ", s + 10)
    obj = make_strategic_object(
        "Patch_America_B1",
        "America",
        "US_B1R",
        "us_b1r",
        cost=12000,
        time=85.0,
        scale=HEAVY_SCALE,
        weapon="GBU38_JDAM_F16C",
        cmd="GenericTacticalBomberCommandSet",
        hp=900.0,
        vision=460,
        bone="Weapon01",
        engines=4,
    )
    return text[:n] + obj + text[n:]


def ensure_russia_tu95(text: str) -> str:
    if "Object Patch_Russia_Tu95" in text:
        return text
    s = text.find("Object Patch_Russia_Tu160")
    if s < 0:
        s = text.find("Object Patch_Russia_Tu22M3")
    n = text.find("\nObject ", s + 10)
    # No dedicated Tu-95 W3D in ART; use RUS_TU160M2 heavy bomber mesh with distinct balance
    obj = make_strategic_object(
        "Patch_Russia_Tu95",
        "Russia",
        "RUS_TU160M2",
        "rus_tu22m3m",
        cost=26000,
        time=110.0,
        scale=0.70,
        weapon="GBU38_JDAM_F16C",
        cmd="GenericTacticalBomberCommandSet",
        hp=980.0,
        vision=500,
        bone="WeaponA01",
        engines=4,
    )
    return text[:n] + "\n; Tu-95 uses RUS_TU160M2 mesh (no dedicated Bear W3D in ART)\n" + obj + text[n:]


def wire_commandsets() -> None:
    cs = CS_AAB.read_text("latin-1")

    def add_cmds(cs_name: str, cmds: list[str]) -> None:
        nonlocal cs
        m = re.search(rf"(^CommandSet {re.escape(cs_name)}\n)([\s\S]*?)(^End\s*$)", cs, re.M)
        if not m:
            print("CS missing", cs_name)
            return
        header, body, end = m.group(1), m.group(2), m.group(3)
        used = {int(x) for x in re.findall(r"^\s*(\d+)\s*=", body, re.M)}
        for cmd in cmds:
            if cmd in body:
                continue
            slot = next(i for i in range(15, 45) if i not in used)
            used.add(slot)
            body = body.rstrip() + f"\n  ; Global strategic AAB\n  {slot} = {cmd}\n"
            print("Wire", cs_name, slot, cmd)
        cs = cs[: m.start()] + header + body + end + cs[m.end() :]

    add_cmds("America_AdvancedAirBaseCommandSet", ["Command_ConstructPatch_America_B1"])
    add_cmds("AirF_America_AdvancedAirBaseCommandSet", ["Command_ConstructPatch_America_B1"])
    add_cmds("Russia_AdvancedAirBaseCommandSet", ["Command_ConstructPatch_Russia_Tu95"])
    CS_AAB.write_text(cs, encoding="latin-1")


def add_buttons_and_strings() -> None:
    extras = [
        ("Patch_America_B1", "us_b1r", "B-1B Lancer", "America"),
        ("Patch_Russia_Tu95", "rus_tu22m3m", "Tu-95", "Russia"),
    ]
    btn = BTN.read_text("latin-1")
    marker = "; ---- Global strategic AAB extras ----"
    if marker in btn:
        btn = btn.split(marker)[0].rstrip() + "\n"
    chunks = [marker]
    for obj, img, label, side in extras:
        cmd = f"Command_Construct{obj}"
        chunks.append(
            f"CommandButton {cmd}\n"
            f"  Command       = UNIT_BUILD\n"
            f"  Object        = {obj}\n"
            f"  TextLabel     = CONTROLBAR:Construct{obj}\n"
            f"  ButtonImage   = {img}\n"
            f"  ButtonBorderType = BUILD\n"
            f"  DescriptLabel = CONTROLBAR:ToolTipConstruct{obj}\n"
            f"End\n"
        )
    BTN.write_text(btn.rstrip() + "\n\n" + "\n".join(chunks), encoding="latin-1")

    st = STR.read_text("latin-1")
    sm = "; ---- Global strategic AAB extras ----"
    if sm in st:
        st = st.split(sm)[0].rstrip() + "\n"
    lines = [sm]
    for obj, img, label, side in extras:
        lines.append(f"OBJECT:{obj} = {label}")
        lines.append(f"CONTROLBAR:Construct{obj} = {label}")
        lines.append(f"CONTROLBAR:ToolTipConstruct{obj} = Produce {label} from Advanced Air Base ({side}).")
    STR.write_text(st.rstrip() + "\n\n" + "\n".join(lines) + "\n", encoding="latin-1")


def main() -> int:
    write_airfield_overrides()

    text = AAB.read_text("latin-1")

    # USA strategic pricing / identity
    text = patch_object_block(
        text,
        "Patch_America_B2",
        Scale=HEAVY_SCALE,
        BuildCost=14000,
        BuildTime=95.0,
        MaxSimultaneousOfType=1,
        MaxSimultaneousLinkKey="Patch_StrategicBomber",
    )
    text = patch_object_block(
        text,
        "Patch_America_B52",
        Scale=HEAVY_SCALE,
        BuildCost=13000,
        BuildTime=90.0,
        MaxSimultaneousOfType=1,
        MaxSimultaneousLinkKey="Patch_StrategicBomber",
    )
    text = patch_object_block(
        text,
        "Patch_America_KC135",
        Scale=SUPPORT_SCALE,
        BuildCost=5500,
        BuildTime=55.0,
    )
    text = patch_object_block(
        text,
        "Patch_America_C17",
        Scale=SUPPORT_SCALE,
        BuildCost=6000,
        BuildTime=60.0,
    )

    # Russia identity + expensive Tu160
    text = patch_object_block(
        text,
        "Patch_Russia_Tu160",
        model="RUS_TU160M2",
        portrait="rus_tu22m3m",
        bone="WeaponA01",
        engines=4,
        Scale=0.70,
        BuildCost=28000,
        BuildTime=120.0,
        MaxSimultaneousOfType=1,
        MaxSimultaneousLinkKey="Patch_StrategicBomber",
    )
    text = patch_object_block(
        text,
        "Patch_Russia_Tu22M3",
        model="RUS_TU22M3M",
        portrait="rus_tu22m3m",
        bone="WeaponA01",
        engines=2,
        Scale=0.70,
        BuildCost=18000,
        BuildTime=100.0,
        MaxSimultaneousOfType=1,
        MaxSimultaneousLinkKey="Patch_StrategicBomber",
    )
    text = patch_object_block(
        text,
        "Patch_Russia_A50",
        model="RUS_A50",
        portrait="rus_a50",
        bone="WeaponA01",
        engines=4,
        CommandSet="A50_CommandSet",
    )
    text = patch_object_block(
        text,
        "Patch_Russia_Il76",
        model="RUS_IL76MD90A",
        portrait="irq_il76",
        bone="WeaponA01",
        engines=4,
        Scale=SUPPORT_SCALE,
        BuildCost=7000,
        BuildTime=65.0,
    )
    text = patch_object_block(
        text,
        "Patch_Russia_Il78",
        Scale=SUPPORT_SCALE,
        BuildCost=6500,
        BuildTime=60.0,
    )

    # China H-6 cheaper than B-2
    text = patch_object_block(
        text,
        "Patch_China_H6",
        model="CHI_H6M",
        portrait="us_b1r",
        bone="WeaponA01",
        engines=2,
        Scale=0.70,
        BuildCost=9000,
        BuildTime=80.0,
        MaxSimultaneousOfType=1,
        MaxSimultaneousLinkKey="Patch_StrategicBomber",
    )
    text = patch_object_block(
        text,
        "Patch_China_HY6",
        Scale=SUPPORT_SCALE,
        BuildCost=5000,
        BuildTime=55.0,
    )
    text = patch_object_block(
        text,
        "Patch_China_Y20",
        Scale=SUPPORT_SCALE,
        BuildCost=5500,
        BuildTime=58.0,
    )

    text = ensure_america_b1(text)
    text = ensure_russia_tu95(text)
    text = strengthen_all_awacs(text)
    text = scale_heavies(text)

    AAB.write_text(text, encoding="latin-1")
    wire_commandsets()
    add_buttons_and_strings()
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
