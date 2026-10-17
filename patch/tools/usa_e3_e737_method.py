#!/usr/bin/env python3
"""USA E-3 AWACS via exact working E-737 integration method.

Specter-safe Object structure (clone AmericaJetE737Visual) + donor ART only.
No donor gameplay DATA. No E-737 / E-2 / other aircraft changes.

Root cause addressed:
  Prior E-3 UNIT_BUILD button reused CONTROLBAR:AmericaAWACS, which is also the
  SCIENCE-gated SPECIAL_POWER Command_AmericaAWACS TextLabel. Switch to unique
  E-737-style labels so HeavyAirBase Slot 5 can show.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
STAGE = MASTER / "_stage_usa_e3_e737_method"
VERIFY = MASTER / "_extract_usa_e3_e737_method_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_E3_E737_METHOD.zip"
OUT_HASH = ROOT / "Release/DATA_USA_E3_E737_METHOD_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_E3_E737_METHOD_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_E3_E737_METHOD_REPORT.txt"
SRC_DIR = ROOT / "Data/INI/Object/Specter/United States Of America"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"

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
V22_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini"
)
HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"
CSF_KEY = "Data\\English\\generals.csf"
MI_KEY = "Data\\INI\\MappedImages\\HandCreated\\HandCreatedMappedImages.INI"

FREEZE_KEYS = [
    CSF_KEY,
    E737_KEY,
    E2_KEY,
    C17_KEY,
    AC130_KEY,
    V22_KEY,
    HEAVY_KEY,
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\Airforce\\B1R.ini",
]

# Exact E-737 structure; donor E-3 visual only. No Scale (native donor size).
E3_OBJECT = """;==============================================================================
; AmericaJetE3Visual - USA E-3 AWACS (VISUAL / BASE ONLY)
; Method: EXACT AmericaJetE737Visual Specter-safe structure + donor ART only
; Donor DATA = NOT USED. Weapons = NONE. AWACS functionality = NOT YET
; Primary W3D = E3
;==============================================================================

Object AmericaJetE3Visual

  SelectPortrait         = E3USA
  ButtonImage            = E3USA

  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    ParticlesAttachedToAnimatedBones = Yes

    DefaultConditionState
      Model = E3
      ParticleSysBone = Engine01 JetBlackTrailThin
      ParticleSysBone = WingTip01 JetContrailThin
      ParticleSysBone = WingTip02 JetContrailThin
    End

    ConditionState = JETEXHAUST
      Model = E3
      ParticleSysBone = Engine01 JetBlackTrailThin
      ParticleSysBone = WingTip01 JetContrailThin
      ParticleSysBone = WingTip02 JetContrailThin
    End

    ConditionState = REALLYDAMAGED
      Model = E3
      ParticleSysBone = Smoke01 JetSmoke
      ParticleSysBone = Smoke02 JetSmoke
    End

    ConditionState = REALLYDAMAGED JETEXHAUST
      Model = E3
      ParticleSysBone = Smoke01 JetSmoke
      ParticleSysBone = Smoke02 JetSmoke
      ParticleSysBone = Engine01 JetBlackTrailThin
    End

    ConditionState = RUBBLE
      Model = E3
    End
  End

  DisplayName = OBJECT:AmericaJetE3Visual
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

  BuildCost = 5500
  BuildTime = 45
  ExperienceValue = 50 50 100 150
  IsTrainable = No
  CommandSet = GenericTacticalBomberCommandSet

  VoiceSelect = RaptorVoiceSelect
  VoiceMove = RaptorVoiceMove
  VoiceGuard = RaptorVoiceAirPatrol
  SoundAmbient = AdvancedFightEngineLoop
  SoundAmbientRubble = NoSound
  UnitSpecificSounds
    VoiceCreate = RaptorVoiceCreate
    SoundEject = PilotSoundEject
    VoiceEject = PilotVoiceEject
    Afterburner = RaptorAfterburner
    VoiceLowFuel = RaptorVoiceLowFuel
    VoiceGarrison = RaptorVoiceMove
  End

  RadarPriority = UNIT
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT

  Body = ActiveBody ModuleTag_02
    MaxHealth = 350.0
    InitialHealth = 350.0
  End

  Behavior = JetSlowDeathBehavior ModuleTag_05
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
  End

  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 500.0
  End

  Behavior = TransitionDamageFX ModuleTag_08
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuous01
    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_MIGDamageTransition
  End

  Behavior = JetAIUpdate ModuleTag_09
    KeepsParkingSpaceWhenAirborne = Yes
    MinHeight = 1
    NeedsRunway = Yes
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 10000
    TakeoffPause = 1000
    TakeoffDistForMaxLift = 0%
    AutoAcquireEnemiesWhenIdle = No
    ParkingOffset = 5
  End
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

# Unique labels (E-737 style). Do NOT reuse CONTROLBAR:AmericaAWACS
# (that string is owned by SCIENCE-gated SPECIAL_POWER Command_AmericaAWACS).
E3_BUTTON = """CommandButton Command_ConstructAmericaJetE3Visual
  Command       = UNIT_BUILD
  Object        = AmericaJetE3Visual
  TextLabel     = CONTROLBAR:AmericaJetE3Visual
  ButtonImage   = E3USA
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipAmericaJetE3Visual
End
"""


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


def count_obj(dmap: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(name)}\s*$")
    return sum(
        len(pat.findall(v.decode("latin1")))
        for k, v in dmap.items()
        if k.lower().endswith(".ini")
    )


def count_btn(dmap: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^CommandButton\s+{re.escape(name)}\s*$")
    return sum(
        len(pat.findall(v.decode("latin1")))
        for k, v in dmap.items()
        if k.lower().endswith(".ini")
    )


def upsert_button(cb: str) -> str:
    block = E3_BUTTON.rstrip()
    if re.search(r"(?m)^CommandButton\s+Command_ConstructAmericaJetE3Visual\s*$", cb):
        cb2, n = re.subn(
            r"CommandButton\s+Command_ConstructAmericaJetE3Visual\s*\n.*?^End\s*$",
            block,
            cb,
            count=1,
            flags=re.M | re.S,
        )
        assert n == 1, "failed to replace E3 button"
        return cb2
    # Insert immediately after E-737 button (same neighborhood as working visual jets)
    m = re.search(
        r"CommandButton\s+Command_ConstructAmericaJetE737Visual\s*\n.*?^End\s*$",
        cb,
        flags=re.M | re.S,
    )
    assert m, "E-737 button missing; refuse to insert E-3"
    return cb[: m.end()] + "\n\n" + block + "\n" + cb[m.end() :]


def patch_commandset(cs: str) -> str:
    def repl(m: re.Match[str]) -> str:
        body = m.group(0)
        body2, n = re.subn(
            r"(?m)^(\s*5\s*=\s*).*$",
            r"\1Command_ConstructAmericaJetE3Visual",
            body,
            count=1,
        )
        assert n == 1, "HeavyAirBase slot 5 missing"
        # freeze required slots
        required = {
            1: "Command_ConstructAmericaJetB2Spirit",
            2: "Command_ConstructAmericaJetB21",
            3: "Command_ConstructAmericaJetB52H",
            4: "Command_ConstructAmericaJetB1R",
            5: "Command_ConstructAmericaJetE3Visual",
            6: "Command_Upgrade_NuclearTipWarhead2",
            7: "Command_ConstructAmericaJetAC130",
            8: "Command_ConstructAmericaJetC17Visual",
            9: "Command_ConstructAmericaJetE737Visual",
            10: "Command_ConstructAmericaJetE2Visual",
            11: "Command_ConstructAmericaJetV22Visual",
            13: "Command_SetRallyPoint",
            14: "Command_Sell",
        }
        for slot, cmd in required.items():
            assert re.search(
                rf"(?m)^\s*{slot}\s*=\s*{re.escape(cmd)}\s*$", body2
            ), f"slot {slot} != {cmd}"
        return body2

    cs2, n = re.subn(
        r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?^End\s*$",
        repl,
        cs,
        count=1,
    )
    assert n == 1, "America_HeavyAirBaseCommandSet missing"
    return cs2


def structure_ok(blob: bytes, obj: str, w3d: str) -> None:
    assert all(c < 128 for c in blob), f"{obj} non-ASCII"
    assert b"\x00" not in blob
    assert not blob.startswith(b"\xef\xbb\xbf")
    text = blob.decode("ascii")
    assert len(re.findall(r"(?m)^Object\s+\S+", text)) == 1
    assert re.search(rf"(?m)^Object\s+{re.escape(obj)}\s*$", text)
    assert f"Model = {w3d}" in text
    assert "ParticlesAttachedToAnimatedBones = Yes" in text
    assert not re.search(r"(?m)^\s*WeaponSet\b", text)
    assert "SpectreGunship" not in text
    assert "Scale =" not in text  # native donor size
    stack: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(";"):
            continue
        if s.startswith("Object "):
            stack = ["Object"]
        elif re.match(
            r"^(Draw|Behavior|ArmorSet|WeaponSet|Body|UnitSpecificSounds|"
            r"Prerequisites|DefaultConditionState|ConditionState|TransitionState)\b",
            s,
        ):
            stack.append(s.split()[0])
        elif s == "End":
            assert stack, f"{obj} extra End"
            stack.pop()
    assert stack == [], f"{obj} unclosed {stack}"


def assert_freeze(before: dict[str, bytes], after: dict[str, bytes]) -> None:
    for k in FREEZE_KEYS:
        assert before[k] == after[k], f"freeze violated: {k}"
    # E-737 scale must remain 0.8
    e737 = after[E737_KEY].decode("latin1")
    assert re.search(r"(?m)^\s*Scale\s*=\s*0\.8\s*$", e737)
    e2 = after[E2_KEY].decode("latin1")
    assert re.search(r"(?m)^\s*Scale\s*=\s*1\.5\s*$", e2)
    heavy = after[HEAVY_KEY].decode("latin1")
    assert re.search(r"(?m)^\s*NumRows\s*=\s*3\s*$", heavy)
    assert re.search(r"(?m)^\s*NumCols\s*=\s*2\s*$", heavy)
    assert sha256(after[CSF_KEY]) == GOOD_CSF


def art_has_e3(art: dict[str, bytes]) -> dict[str, bool]:
    return {
        "E3.W3D": "Art\\W3D\\E3.W3D" in art,
        "avE3.tga": "Art\\Textures\\avE3.tga" in art,
        "avE3ACC.tga": "Art\\Textures\\avE3ACC.tga" in art,
        "E3USA.tga": "Art\\Textures\\E3USA.tga" in art,
        "E3USATB.tga": "Art\\Textures\\E3USATB.tga" in art,
        "chj10_r.W3D": "Art\\W3D\\chj10_r.W3D" in art,
    }


def upload(path: Path) -> str:
    for cmd in (
        ["curl", "-sF", f"file=@{path}", "https://litterbox.catbox.moe/resources/internals/api.php",
         "-F", "time=72h", "-F", "reqtype=fileupload"],
        ["curl", "-sF", f"reqtype=fileupload", "-F", f"fileToUpload=@{path}",
         "https://litterbox.catbox.moe/resources/internals/api.php", "-F", "time=72h"],
    ):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            out = (r.stdout or "").strip()
            if out.startswith("http"):
                return out
        except Exception:
            pass
    # fallback gofile
    try:
        r = subprocess.run(
            ["curl", "-sF", f"file=@{path}", "https://store1.gofile.io/uploadFile"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        m = re.search(r'"downloadPage"\s*:\s*"([^"]+)"', r.stdout or "")
        if m:
            return m.group(1)
    except Exception:
        pass
    return "(upload failed)"


def main() -> None:
    before = read_big(DATA_BIG)
    art = read_big(ART_BIG)
    art_status = art_has_e3(art)
    assert all(art_status.values()), f"missing ART: {art_status}"
    assert "MappedImage E3USA" in before[MI_KEY].decode("latin1")

    freeze_snap = {k: before[k] for k in FREEZE_KEYS}

    e3_blob = E3_OBJECT.encode("ascii")
    structure_ok(e3_blob, "AmericaJetE3Visual", "E3")

    cb = before[CB_KEY].decode("latin1")
    cs = before[CS_KEY].decode("latin1")
    cb2 = upsert_button(cb)
    cs2 = patch_commandset(cs)

    # Ensure button does not reuse AmericaAWACS special-power string
    btn_m = re.search(
        r"CommandButton\s+Command_ConstructAmericaJetE3Visual\s*\n.*?^End\s*$",
        cb2,
        flags=re.M | re.S,
    )
    assert btn_m
    btn_block = btn_m.group(0)
    assert "Object        = AmericaJetE3Visual" in btn_block
    assert "ButtonImage   = E3USA" in btn_block
    assert "CONTROLBAR:AmericaJetE3Visual" in btn_block
    assert "CONTROLBAR:AmericaAWACS" not in btn_block
    assert "UNIT_BUILD" in btn_block

    after = dict(before)
    after[E3_KEY] = e3_blob
    after[CB_KEY] = cb2.replace("\r\n", "\n").encode("latin1")
    after[CS_KEY] = cs2.replace("\r\n", "\n").encode("latin1")

    # restore freeze from snap (paranoia)
    for k, v in freeze_snap.items():
        after[k] = v

    assert_freeze(before, after)
    assert count_obj(after, "AmericaJetE3Visual") == 1
    assert count_obj(after, "AmericaJetE3AWACS") == 0
    assert count_obj(after, "USAE3") == 0
    assert count_btn(after, "Command_ConstructAmericaJetE3Visual") == 1
    assert count_btn(after, "Command_ConstructAmericaJetE3AWACS") == 0

    # stage + rebuild
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    write_tree(after, STAGE / "in")
    new_big = build_big(after)
    DATA_BIG.write_bytes(new_big)

    # verify by re-extract
    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    verify_map = read_big(DATA_BIG)
    write_tree(verify_map, VERIFY / "out")
    assert_freeze(before, verify_map)
    assert count_obj(verify_map, "AmericaJetE3Visual") == 1
    assert count_obj(verify_map, "AmericaJetE3AWACS") == 0
    assert count_obj(verify_map, "USAE3") == 0
    assert count_btn(verify_map, "Command_ConstructAmericaJetE3Visual") == 1
    vcb = verify_map[CB_KEY].decode("latin1")
    vcs = verify_map[CS_KEY].decode("latin1")
    assert "Command_ConstructAmericaJetE3Visual" in vcb
    assert re.search(
        r"(?m)^\s*5\s*=\s*Command_ConstructAmericaJetE3Visual\s*$",
        re.search(
            r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?^End\s*$",
            vcs,
        ).group(0),
    )
    structure_ok(verify_map[E3_KEY], "AmericaJetE3Visual", "E3")
    # button target resolves
    assert "Object AmericaJetE3Visual" in verify_map[E3_KEY].decode("latin1")
    assert "ButtonImage   = E3USA" in vcb
    assert "MappedImage E3USA" in verify_map[MI_KEY].decode("latin1")

    # sync loose source Object
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    (SRC_DIR / "AmericaJetE3Visual.ini").write_bytes(e3_blob)

    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)

    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    url = upload(OUT_ZIP)
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={data_sha}\n"
        f"_SPEC_ART_ONE.big sha256={art_sha} (unchanged)\n"
        f"zip={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    OUT_URL.write_text(url + "\n", encoding="utf-8")

    report = f"""USA E-3 E737-STYLE INTEGRATION = PASS

Reference method:
E-737 method followed = YES

Root cause fixed:
Prior TextLabel CONTROLBAR:AmericaAWACS collided with SCIENCE-gated
SPECIAL_POWER Command_AmericaAWACS. Replaced with unique E-737-style labels.

E-3:
Object = AmericaJetE3Visual
Real donor primary W3D = E3
Real donor textures = avE3.tga, avE3ACC.tga, housecolor (ART)
Real donor animation dependencies = (in-mesh E3.RADAR / chassis; gear W3D chj10_r present in ART, not bound in Specter-safe Draw — matches E-737 method)
Button = Command_ConstructAmericaJetE3Visual
ButtonImage = E3USA
Exact donor E-3 icon = YES
HeavyAirBase Slot = 5

Build chain:
HeavyAirBase -> CommandSet -> Button -> Object = YES

Donor DATA used = NO
Specter-safe DATA used = YES

Old AmericaJetE3AWACS active = 0
USAE3 gameplay Object active = 0
AmericaJetE3Visual active = 1

Weapons = NONE
AWACS functionality = NOT YET

E-737 changed = NO
E-2 changed = NO
C-17 changed = NO
V-22 changed = NO
AC-130 changed = NO
Bombers changed = NO
HeavyAirBase parking changed = NO
Other factions changed = NO

ART CHANGED = NO
ART present = {art_status}

FINAL PACKED-BIG VERIFICATION:
Command_ConstructAmericaJetE3Visual exists = 1
Object AmericaJetE3Visual exists = 1
America_HeavyAirBaseCommandSet Slot 5 references E-3 button = YES
Button Object target resolves = YES
E-3 donor W3D exists in ART = YES
E-3 donor ButtonImage exists in ART = YES

DATA sha256 = {data_sha}
ZIP = {OUT_ZIP.name}
URL = {url}
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
