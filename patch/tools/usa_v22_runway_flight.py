#!/usr/bin/env python3
"""Convert AmericaJetV22Visual to E-737 runway/fixed-wing flight.

Keep full AVOsprey visual Draw hierarchy unchanged.
Replace helicopter-style movement with AmericaJetE737Visual flight system.
DATA-only.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
STAGE = MASTER / "_stage_usa_v22_runway_flight"
VERIFY = MASTER / "_extract_usa_v22_runway_flight_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_V22_RUNWAY_FLIGHT.zip"
OUT_HASH = ROOT / "Release/DATA_USA_V22_RUNWAY_FLIGHT_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_V22_RUNWAY_FLIGHT_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_V22_RUNWAY_FLIGHT_REPORT.txt"
SRC_DIR = ROOT / "Data/INI/Object/Specter/United States Of America"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"

V22_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini"
)
E737_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini"
)
E2_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE2Visual.ini"
)
E3_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE3Visual.ini"
)
C17_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Visual.ini"
)
AC130_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
)
HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"
CSF_KEY = "Data\\English\\generals.csf"

FREEZE_KEYS = [
    CSF_KEY,
    CS_KEY,
    CB_KEY,
    E737_KEY,
    E2_KEY,
    E3_KEY,
    C17_KEY,
    AC130_KEY,
    HEAVY_KEY,
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\Airforce\\B1R.ini",
]

E737_JETAI = """  Behavior = JetAIUpdate ModuleTag_09
    KeepsParkingSpaceWhenAirborne = Yes
    MinHeight = 1
    NeedsRunway = Yes
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 10000
    TakeoffPause = 1000
    TakeoffDistForMaxLift = 0%
    AutoAcquireEnemiesWhenIdle = No
    ParkingOffset = 5
  End"""

# Jet death for runway aircraft (replaces FXListDie heli death-only)
E737_JET_DEATH = """  Behavior = JetSlowDeathBehavior ModuleTag_05
    FXOnGroundDeath = FX_JetOnGroundDeath
    OCLOnGroundDeath = OCL_RaptorDeathFinalBlowUp
    DestructionDelay = 99999999
    RollRate = 0.2
    RollRateDelta = 100%
    PitchRate = 0.0
    FallHowFast = 110.0%
    FXInitialDeath = FX_RaptorDeathInitial
    OCLInitialDeath = OCL_RaptorDeathInitial
    DelaySecondaryFromInitialDeath = 500
    FXSecondary = FX_JetDeathSecondary
    OCLSecondary = OCL_RaptorDeathSecondary
    FXHitGround = FX_JetDeathHitGround
    OCLHitGround = OCL_RaptorDeathHitGround
    DelayFinalBlowUpFromHitGround = 200
    FXFinalBlowUp = FX_JetDeathFinalBlowUp
    OCLFinalBlowUp = OCL_RaptorDeathFinalBlowUp
  End"""


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        out[name.replace("/", "\\")] = data[off : off + size]
    return out


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16 + sum(8 + len(n.encode("latin1")) + 1 for n, _ in items)
    offset = header_size
    index, blobs = [], []
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">III", offset, len(items), header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for b in blobs:
        out += b
    return bytes(out)


def write_tree(file_map: dict[str, bytes], root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for name, content in file_map.items():
        path = root / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def read_tree(root: Path) -> dict[str, bytes]:
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root)).replace("/", "\\")] = p.read_bytes()
    return out


def grab(text: str, pat: str) -> str | None:
    m = re.search(pat, text)
    return m.group(1) if m else None


def extract_draw_section(text: str) -> str:
    """Return all consecutive Draw blocks from first Draw to before DisplayName."""
    m = re.search(
        r"(?ms)(^\s*Draw\s*=\s*W3DModelDraw.*?)(?=^\s*DisplayName\s*=)",
        text,
    )
    if not m:
        raise SystemExit("V22 Draw section not found")
    return m.group(1)


def patch_v22(text: str) -> tuple[str, dict]:
    before = {
        "AIUpdate": grab(text, r"(?m)^\s*Behavior\s*=\s*(\S*AIUpdate\S*)"),
        "NeedsRunway": grab(text, r"(?m)^\s*NeedsRunway\s*=\s*(\S+)"),
        "MinHeight": grab(text, r"(?m)^\s*MinHeight\s*=\s*(\S+)"),
        "Locomotor": grab(text, r"(?m)^\s*Locomotor\s*=\s*SET_NORMAL\s+(\S+)"),
        "Taxi": grab(text, r"(?m)^\s*Locomotor\s*=\s*SET_TAXIING\s+(\S+)"),
        "KindOf": grab(text, r"(?m)^\s*KindOf\s*=\s*(.+)"),
        "CommandSet": grab(text, r"(?m)^\s*CommandSet\s*=\s*(\S+)"),
        "Scale": grab(text, r"(?m)^\s*Scale\s*=\s*(\S+)"),
        "GeometryMajorRadius": grab(
            text, r"(?m)^\s*GeometryMajorRadius\s*=\s*(\S+)"
        ),
        "GeometryMinorRadius": grab(
            text, r"(?m)^\s*GeometryMinorRadius\s*=\s*(\S+)"
        ),
        "GeometryHeight": grab(text, r"(?m)^\s*GeometryHeight\s*=\s*(\S+)"),
    }

    draw = extract_draw_section(text)
    # Preserve SelectPortrait/ButtonImage header before Draw
    header_m = re.search(
        r"(?ms)^(Object AmericaJetV22Visual\s*\n.*?)^(\s*Draw\s*=)",
        text,
    )
    if not header_m:
        raise SystemExit("V22 header not found")
    header = header_m.group(1)

    # Comment update
    header = re.sub(
        r"(?m)^; Movement skeleton:.*$",
        "; Movement skeleton: AmericaJetE737Visual runway/fixed-wing flight "
        "(no helicopter VTOL)",
        header,
    )
    header = re.sub(
        r"(?m)^; Method: Specter-safe VTOL structure",
        "; Method: Specter-safe RUNWAY aircraft structure",
        header,
    )

    models_before = re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)

    body = f"""{header}{draw}  DisplayName = OBJECT:AmericaJetV22Visual
  EditorSorting = VEHICLE
  Side = America
  TransportSlotCount = 0
  VisionRange = 300.0
  ShroudClearingRange = 300
  Prerequisites
  End
  Buildable = Ignore_Prerequisites

  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End

  BuildCost = 5000
  BuildTime = 40
  ExperienceValue = 50 50 100 150
  IsTrainable = No
  CommandSet = GenericTacticalBomberCommandSet

  VoiceSelect = ComancheVoiceSelect
  VoiceMove = ComancheVoiceMove
  VoiceGuard = ComancheVoiceMove
  SoundAmbient = ComancheAmbientLoop
  SoundAmbientRubble = NoSound
  UnitSpecificSounds
    VoiceCreate = ComancheVoiceCreate
    SoundEject = PilotSoundEject
    VoiceEject = PilotVoiceEject
    VoiceGarrison = ComancheVoiceMove
  End

  RadarPriority = UNIT
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT

  Body = ActiveBody ModuleTag_02
    MaxHealth = 400.0
    InitialHealth = 400.0
  End

{E737_JET_DEATH}

  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 500.0
  End

  Behavior = TransitionDamageFX ModuleTag_08
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuous01
    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_MIGDamageTransition
  End

{E737_JETAI}
  Locomotor = SET_NORMAL F100_PW_229
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor

  Behavior = FlammableUpdate ModuleTag_21
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
  End

  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 40.0
  GeometryMinorRadius = 10.0
  GeometryHeight = 10.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""
    # Ensure no Scale line introduced
    assert not re.search(r"(?m)^\s*Scale\s*=", body)
    models_after = re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", body)
    assert models_before == models_after
    assert "AVOsprey" in models_after
    assert "AVOsprey_A1" in models_after
    assert "AVOsprey_A4" in models_after
    assert "HelicopterAIUpdate" not in body
    assert "BasicHelicopterTaxiLocomotor" not in body
    assert "T700_GE_701D_B2" not in body
    assert "PRODUCED_AT_HELIPAD" not in body
    assert "NeedsRunway = Yes" in body
    assert "WeaponSet" not in body
    assert "TransportContain" not in body

    after = {
        "AIUpdate": "JetAIUpdate",
        "NeedsRunway": "Yes",
        "MinHeight": "1",
        "Locomotor": "F100_PW_229",
        "Taxi": "BasicJetTaxiLocomotor",
        "KindOf": "PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT",
        "CommandSet": "GenericTacticalBomberCommandSet",
        "Scale": before["Scale"],
        "GeometryMajorRadius": "40.0",
        "GeometryMinorRadius": "10.0",
        "GeometryHeight": "10.0",
    }
    return body, {"before": before, "after": after, "models": models_after}


def upload_zip(path: Path) -> str:
    proc = subprocess.run(
        [
            "curl",
            "-sF",
            "reqtype=fileupload",
            "-F",
            "time=72h",
            "-F",
            f"fileToUpload=@{path}",
            "https://litterbox.catbox.moe/resources/internals/api.php",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    url = (proc.stdout or "").strip()
    if url.startswith("http"):
        return url
    servers = json.loads(
        subprocess.run(
            ["curl", "-s", "https://api.gofile.io/servers"],
            capture_output=True,
            text=True,
            timeout=60,
        ).stdout
    )
    server = servers["data"]["servers"][0]["name"]
    up = subprocess.run(
        [
            "curl",
            "-s",
            "-F",
            f"file=@{path}",
            f"https://{server}.gofile.io/uploadFile",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    data = json.loads(up.stdout)
    return data["data"]["downloadPage"]


def main() -> None:
    dmap = read_big(DATA_BIG)
    assert sha256(dmap[CSF_KEY]) == GOOD_CSF
    freeze = {k: dmap[k] for k in FREEZE_KEYS if k in dmap}

    e737 = dmap[E737_KEY].decode("latin1")
    e2 = dmap[E2_KEY].decode("latin1")
    assert re.search(r"(?m)^\s*Scale\s*=\s*0\.8\s*$", e737)
    assert re.search(r"(?m)^\s*Scale\s*=\s*3\.932\s*$", e2)
    assert "Locomotor = SET_NORMAL F100_PW_229" in e737

    v22 = dmap[V22_KEY].decode("latin1")
    assert re.search(r"(?m)^Object\s+AmericaJetV22Visual\s*$", v22)
    assert "AVOsprey" in v22

    new_text, info = patch_v22(v22)
    dmap[V22_KEY] = new_text.encode("latin1")

    SRC_DIR.mkdir(parents=True, exist_ok=True)
    (SRC_DIR / "AmericaJetV22Visual.ini").write_bytes(dmap[V22_KEY])

    if STAGE.exists():
        shutil.rmtree(STAGE)
    write_tree(dmap, STAGE / "in")
    staged = read_tree(STAGE / "in")
    for k, blob in freeze.items():
        assert staged[k] == blob, f"freeze mutated: {k}"
    new_data = build_big(staged)
    DATA_BIG.write_bytes(new_data)

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    vmap = read_big(DATA_BIG)
    write_tree(vmap, VERIFY / "out")

    for k, blob in freeze.items():
        assert vmap[k] == blob, f"freeze broken: {k}"
    assert sha256(vmap[CSF_KEY]) == GOOD_CSF

    final = vmap[V22_KEY].decode("latin1")
    assert "HelicopterAIUpdate" not in final
    assert "BasicHelicopterTaxiLocomotor" not in final
    assert "T700_GE_701D_B2" not in final
    assert "PRODUCED_AT_HELIPAD" not in final
    assert "GenericAttackHelicopterHoverCommandSet" not in final
    assert "NeedsRunway = Yes" in final
    assert "Locomotor = SET_NORMAL F100_PW_229" in final
    assert "Locomotor = SET_TAXIING BasicJetTaxiLocomotor" in final
    assert "JetAIUpdate" in final
    assert "JetSlowDeathBehavior" in final
    assert not re.search(r"(?m)^\s*Scale\s*=", final)
    assert "WeaponSet" not in final
    assert "TransportContain" not in final
    models = re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", final)
    assert "AVOsprey" in models and "AVOsprey_A1" in models
    assert "AVOsprey_A4" in models and "AVOsprey_DA1" in models

    # Slot 11 preserved
    cs = vmap[CS_KEY].decode("latin1")
    m = re.search(
        r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)(?=^CommandSet\s+\S+\s*$|\Z)",
        cs,
    )
    assert re.search(
        r"(?m)^\s*11\s*=\s*Command_ConstructAmericaJetV22Visual\s*$",
        m.group(0),
    )

    # Scales preserved
    assert re.search(
        r"(?m)^\s*Scale\s*=\s*0\.8\s*$", vmap[E737_KEY].decode("latin1")
    )
    assert re.search(
        r"(?m)^\s*Scale\s*=\s*3\.932\s*$", vmap[E2_KEY].decode("latin1")
    )
    heavy = vmap[HEAVY_KEY].decode("latin1")
    assert re.search(r"(?m)^\s*NumRows\s*=\s*3\s*$", heavy)
    assert re.search(r"(?m)^\s*NumCols\s*=\s*2\s*$", heavy)

    b, a = info["before"], info["after"]
    report = []
    report.append("V22 RUNWAY FLIGHT CONVERSION = PASS (structural readiness)")
    report.append("")
    report.append("Object = AmericaJetV22Visual")
    report.append("Visual W3D family = AVOsprey*")
    report.append(
        f"Old AIUpdate = {b['AIUpdate']} "
        f"(NeedsRunway={b['NeedsRunway']}, MinHeight={b['MinHeight']})"
    )
    report.append(
        f"New AIUpdate = {a['AIUpdate']} "
        f"(NeedsRunway={a['NeedsRunway']}, MinHeight={a['MinHeight']}, "
        "KeepsParkingSpaceWhenAirborne=Yes, TakeoffPause=1000, "
        "TakeoffDistForMaxLift=0%, ParkingOffset=5 — E-737-identical)"
    )
    report.append(f"Old Locomotor = {b['Locomotor']} + {b['Taxi']}")
    report.append(f"New Locomotor = {a['Locomotor']} + {a['Taxi']}")
    report.append("Flight reference = AmericaJetE737Visual")
    report.append("Helicopter movement modules remaining = 0")
    report.append("Fixed-wing/runway movement adopted = YES")
    report.append(
        f"KindOf: removed PRODUCED_AT_HELIPAD; "
        f"CommandSet {b['CommandSet']} -> {a['CommandSet']}"
    )
    report.append(
        f"Geometry {b['GeometryMajorRadius']}/{b['GeometryMinorRadius']}/"
        f"{b['GeometryHeight']} -> {a['GeometryMajorRadius']}/"
        f"{a['GeometryMinorRadius']}/{a['GeometryHeight']} "
        "(E-737 runway-proven collision; visual unchanged)"
    )
    report.append("Visual model changed = NO")
    report.append("Scale changed = NO (no Scale line; unchanged)")
    report.append("Rotors preserved = YES (AVOsprey_A*/_DA*)")
    report.append("Nacelles preserved = YES (engine Draw ModuleTag_Engines01)")
    report.append("HeavyAirBase Slot 11 preserved = YES")
    report.append("")
    report.append("Expected behavior:")
    report.append("Park on airbase = READY")
    report.append("Runway takeoff = READY")
    report.append("Fixed-wing flight = READY")
    report.append("Runway landing = READY")
    report.append("Return to parking = READY")
    report.append("")
    report.append("Vertical takeoff = DISABLED")
    report.append("Vertical landing = DISABLED")
    report.append("")
    report.append("Weapons = NONE")
    report.append("Transport capability = NOT YET")
    report.append("")
    report.append("E-737 changed = NO")
    report.append("C-17 changed = NO")
    report.append("AC-130 changed = NO")
    report.append("E-2 changed = NO")
    report.append("E-3 changed = NO")
    report.append("HeavyAirBase changed = NO")
    report.append("Other factions changed = NO")
    report.append("ART changed = NO")
    report.append(f"DATA sha256 = {sha256(DATA_BIG)}")
    report.append(
        "NOTE = In-game takeoff/landing not launched here; structural readiness only."
    )

    text = "\n".join(report) + "\n"
    OUT_REPORT.write_text(text, encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text(text, encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    with zipfile.ZipFile(OUT_ZIP) as z:
        assert z.namelist() == ["_SPEC_DATA_ONE.big"]

    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={sha256(DATA_BIG)}\nZIP={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    url = upload_zip(OUT_ZIP)
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print(text)
    print("Download =", url)


if __name__ == "__main__":
    main()
