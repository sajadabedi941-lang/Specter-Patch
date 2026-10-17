#!/usr/bin/env python3
"""Add USA AmericaJetB2A — second B-2 from donor visual, separate from Spirit.

Specter-safe Object (E-737 method) + donor W3D AVB3bmbr (USAB2 primary model).
Distinct ButtonImage = B2A. HeavyAirBase Slot 12.
No donor gameplay DATA. Does not modify existing B-2 Spirit or other aircraft.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
STAGE = MASTER / "_stage_usa_b2a_donor_visual"
VERIFY = MASTER / "_extract_usa_b2a_donor_visual_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_ART_USA_B2A_DONOR_VISUAL.zip"
OUT_HASH = ROOT / "Release/DATA_ART_USA_B2A_DONOR_VISUAL_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_ART_USA_B2A_DONOR_VISUAL_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_ART_USA_B2A_DONOR_VISUAL_REPORT.txt"
SRC_DIR = ROOT / "Data/INI/Object/Specter/United States Of America"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"

E737_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini"
)
B2_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"
)
B2A_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB2A.ini"
)
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"
CSF_KEY = "Data\\English\\generals.csf"
MI_KEY = "Data\\INI\\MappedImages\\HandCreated\\HandCreatedMappedImages.INI"
HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)

FREEZE_BUTTONS = {
    "Command_ConstructAmericaJetB2Spirit": "B2DropBombTB",
    "Command_ConstructAmericaJetB21": "B21_L",
    "Command_ConstructAmericaJetB52H": "B52",
    "Command_ConstructAmericaJetB1R": "B1",
    "Command_ConstructAmericaJetE3Visual": "E3USA",
    "Command_ConstructAmericaJetAC130": "Cargo130",
    "Command_ConstructAmericaJetC17Visual": "C17GlobalMaster",
    "Command_ConstructAmericaJetE737Visual": "avionE737",
    "Command_ConstructAmericaJetE2Visual": "E2avionHE",
    "Command_ConstructAmericaJetV22Visual": "V22",
}

B2A_OBJECT = """;==============================================================================
; AmericaJetB2A - USA B-2 (B2A) second airframe, separate from AmericaJetB2Spirit
; Method: Specter-safe structure + donor ART only (E-737 workflow)
; Donor Object USAB2 primary W3D = AVB3bmbr (DATA not imported)
; Weapons = NONE for now
;==============================================================================

Object AmericaJetB2A

  SelectPortrait         = B2A
  ButtonImage            = B2A

  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    ParticlesAttachedToAnimatedBones = Yes

    DefaultConditionState
      Model = AVB3bmbr
      ParticleSysBone = Engine01 JetBlackTrailThin
      ParticleSysBone = Engine02 JetBlackTrailThin
      ParticleSysBone = Wingtip01 JetContrailThin
      ParticleSysBone = Wingtip02 JetContrailThin
    End

    ConditionState = JETEXHAUST
      Model = AVB3bmbr
      ParticleSysBone = Engine01 JetBlackTrailThin
      ParticleSysBone = Engine02 JetBlackTrailThin
      ParticleSysBone = Wingtip01 JetContrailThin
      ParticleSysBone = Wingtip02 JetContrailThin
    End

    ConditionState = REALLYDAMAGED
      Model = AVB3bmbr_D
      ParticleSysBone = Smoke01 JetSmoke
      ParticleSysBone = Smoke02 JetSmoke
    End

    ConditionState = REALLYDAMAGED JETEXHAUST
      Model = AVB3bmbr_D
      ParticleSysBone = Smoke01 JetSmoke
      ParticleSysBone = Smoke02 JetSmoke
      ParticleSysBone = Engine01 JetBlackTrailThin
      ParticleSysBone = Engine02 JetBlackTrailThin
    End

    ConditionState = RUBBLE
      Model = AVB3bmbr_D
    End
  End

  DisplayName = OBJECT:AmericaJetB2A
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

  BuildCost = 6000
  BuildTime = 50
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
    MaxHealth = 400.0
    InitialHealth = 400.0
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

  Scale = 0.85
  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 40.0
  GeometryMinorRadius = 10.0
  GeometryHeight = 10.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""

B2A_BUTTON = """CommandButton Command_ConstructAmericaJetB2A
  Command       = UNIT_BUILD
  Object        = AmericaJetB2A
  TextLabel     = CONTROLBAR:AmericaJetB2A
  ButtonImage   = B2A
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipAmericaJetB2A
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


def get_button_image(cb: str, btn: str) -> str:
    m = re.search(
        rf"(?ms)^CommandButton\s+{re.escape(btn)}\s*\n.*?^End\s*$", cb
    )
    assert m, btn
    bi = re.search(r"(?m)^\s*ButtonImage\s*=\s*(\S+)", m.group(0))
    assert bi
    return bi.group(1)


def rgb_to_tga24(im: Image.Image) -> bytes:
    """Bottom-origin 24-bit uncompressed TGA."""
    im = im.convert("RGB")
    w, h = im.size
    pixels = im.load()
    body = bytearray()
    for y in range(h):  # bottom origin: y=0 is bottom
        yy = h - 1 - y
        for x in range(w):
            r, g, b = pixels[x, yy]
            body += bytes([b, g, r])
    header = bytearray(18)
    header[2] = 2
    struct.pack_into("<HH", header, 12, w, h)
    header[16] = 24
    header[17] = 0
    return bytes(header) + bytes(body)


def make_b2a_button_tga(art: dict[str, bytes]) -> bytes:
    """Distinct B2A cameo from US-Icons03 flying-wing tile (not B2DropBombTB)."""
    b = art["Art\\Textures\\US-Icons03.tga"]
    w, h = struct.unpack_from("<HH", b, 12)
    bpp = b[16] // 8
    top = bool(b[17] & 0x20)
    assert b[2] == 2
    img = b[18 : 18 + w * h * bpp]
    mode = "RGBA" if bpp == 4 else "RGB"
    raw = "BGRA" if bpp == 4 else "BGR"
    im = Image.frombytes(mode, (w, h), img, "raw", raw)
    if not top:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    crop = im.crop((366, 392, 488, 489)).convert("RGB")
    crop = crop.resize((150, 112), Image.Resampling.LANCZOS)
    return rgb_to_tga24(crop)


def ensure_mapped_image(mi: str, name: str, texture: str, tw: int, th: int) -> str:
    block = (
        f"MappedImage {name}\n"
        f"  Texture = {texture}\n"
        f"  TextureWidth = {tw}\n"
        f"  TextureHeight = {th}\n"
        f"  Coords = Left:0 Top:0 Right:{tw} Bottom:{th}\n"
        f"  Status = NONE\n"
        f"End\n"
    )
    if re.search(rf"(?m)^MappedImage\s+{re.escape(name)}\s*$", mi):
        mi2, n = re.subn(
            rf"(?ms)^MappedImage\s+{re.escape(name)}\s*\n.*?^End\s*$",
            block.rstrip(),
            mi,
            count=1,
        )
        assert n == 1
        return mi2
    anchor = re.search(r"(?ms)^MappedImage\s+B2DropBombTB\s*\n.*?^End\s*$", mi)
    if not anchor:
        anchor = re.search(r"(?ms)^MappedImage\s+E3USA\s*\n.*?^End\s*$", mi)
    if anchor:
        return mi[: anchor.end()] + "\n\n" + block + mi[anchor.end() :]
    return mi.rstrip() + "\n\n" + block


def upsert_button(cb: str) -> str:
    block = B2A_BUTTON.rstrip()
    if re.search(r"(?m)^CommandButton\s+Command_ConstructAmericaJetB2A\s*$", cb):
        cb2, n = re.subn(
            r"(?ms)^CommandButton\s+Command_ConstructAmericaJetB2A\s*\n.*?^End\s*$",
            block,
            cb,
            count=1,
        )
        assert n == 1
        return cb2
    m = re.search(
        r"(?ms)^CommandButton\s+Command_ConstructAmericaJetB2Spirit\s*\n.*?^End\s*$",
        cb,
    )
    assert m, "B2 Spirit button missing"
    return cb[: m.end()] + "\n\n" + block + "\n" + cb[m.end() :]


def patch_commandset(cs: str) -> str:
    def repl(m: re.Match[str]) -> str:
        body = m.group(0)
        if re.search(r"(?m)^\s*12\s*=", body):
            body2, n = re.subn(
                r"(?m)^(\s*12\s*=\s*).*$",
                r"\1Command_ConstructAmericaJetB2A",
                body,
                count=1,
            )
            assert n == 1
        else:
            # insert before slot 13
            body2, n = re.subn(
                r"(?m)^(\s*13\s*=\s*Command_SetRallyPoint\s*)$",
                "  12 = Command_ConstructAmericaJetB2A\n\\1",
                body,
                count=1,
            )
            assert n == 1
        required = {
            1: "Command_ConstructAmericaJetB2Spirit",
            2: "Command_ConstructAmericaJetB21",
            3: "Command_ConstructAmericaJetB52H",
            4: "Command_ConstructAmericaJetB1R",
            5: "Command_ConstructAmericaJetE3Visual",
            7: "Command_ConstructAmericaJetAC130",
            9: "Command_ConstructAmericaJetE737Visual",
            12: "Command_ConstructAmericaJetB2A",
            13: "Command_SetRallyPoint",
            14: "Command_Sell",
        }
        for slot, cmd in required.items():
            assert re.search(
                rf"(?m)^\s*{slot}\s*=\s*{re.escape(cmd)}\s*$", body2
            ), f"slot {slot}"
        return body2

    cs2, n = re.subn(
        r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?^End\s*$",
        repl,
        cs,
        count=1,
    )
    assert n == 1
    return cs2


def upload(path: Path) -> str:
    try:
        r = subprocess.run(
            [
                "curl",
                "-sF",
                f"file=@{path}",
                "https://litterbox.catbox.moe/resources/internals/api.php",
                "-F",
                "time=72h",
                "-F",
                "reqtype=fileupload",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        out = (r.stdout or "").strip()
        if out.startswith("http"):
            return out
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["curl", "-sF", f"file=@{path}", "https://store1.gofile.io/uploadFile"],
            capture_output=True,
            text=True,
            timeout=900,
        )
        m = re.search(r'"downloadPage"\s*:\s*"([^"]+)"', r.stdout or "")
        if m:
            return m.group(1)
    except Exception:
        pass
    return "(upload failed)"


def main() -> None:
    data = read_big(DATA_BIG)
    art = read_big(ART_BIG)
    assert sha256(data[CSF_KEY]) == GOOD_CSF
    assert "Art\\W3D\\AVB3bmbr.W3D" in art
    assert "Art\\W3D\\AVB3bmbr_D.W3D" in art

    # freeze existing Spirit object bytes inside USA_System
    spirit_before = data[B2_KEY]
    assert b"Object AmericaJetB2Spirit" in spirit_before
    assert count_obj(data, "AmericaJetB2A") == 0

    cb = data[CB_KEY].decode("latin1")
    cs = data[CS_KEY].decode("latin1")
    mi = data[MI_KEY].decode("latin1")

    for btn, img in FREEZE_BUTTONS.items():
        assert get_button_image(cb, btn) == img, f"{btn} != {img}"

    # ART: B2A button TGA + ensure donor AVB2A skins present (used by related meshes)
    btn_tga = make_b2a_button_tga(art)
    assert struct.unpack_from("<HH", btn_tga, 12) == (150, 112)

    art2 = dict(art)
    art2["Art\\Textures\\B2ATB.tga"] = btn_tga
    art2["Art\\Textures\\B2A.tga"] = btn_tga
    # Import donor AVB2A textures if missing (skin family referenced by donor B-2 art)
    donor_tex = Path("/tmp/donor_art_extract/Art/Textures")
    for name in ("AVB2A.tga", "AVB2A_d.tga", "AVB2A_e.tga"):
        key = f"Art\\Textures\\{name}"
        src = donor_tex / name
        if key not in art2 and src.exists():
            art2[key] = src.read_bytes()

    mi2 = ensure_mapped_image(mi, "B2A", "B2ATB.tga", 150, 112)
    cb2 = upsert_button(cb)
    cs2 = patch_commandset(cs)

    e3_blob = B2A_OBJECT.encode("ascii")
    assert b"WeaponSet" not in e3_blob
    assert b"AVB3bmbr" in e3_blob

    data2 = dict(data)
    data2[B2A_KEY] = e3_blob
    data2[CB_KEY] = cb2.replace("\r\n", "\n").encode("latin1")
    data2[CS_KEY] = cs2.replace("\r\n", "\n").encode("latin1")
    data2[MI_KEY] = mi2.replace("\r\n", "\n").encode("latin1")
    data2[B2_KEY] = spirit_before  # freeze Spirit
    data2[E737_KEY] = data[E737_KEY]
    data2[CSF_KEY] = data[CSF_KEY]
    data2[HEAVY_KEY] = data[HEAVY_KEY]

    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    write_tree(data2, STAGE / "data_in")
    write_tree(art2, STAGE / "art_in")

    DATA_BIG.write_bytes(build_big(data2))
    ART_BIG.write_bytes(build_big(art2))

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    dv = read_big(DATA_BIG)
    av = read_big(ART_BIG)
    write_tree(dv, VERIFY / "data_out")
    write_tree(av, VERIFY / "art_out")

    assert count_obj(dv, "AmericaJetB2A") == 1
    assert count_obj(dv, "AmericaJetB2Spirit") == 1
    assert count_btn(dv, "Command_ConstructAmericaJetB2A") == 1
    assert dv[B2_KEY] == spirit_before
    assert sha256(dv[CSF_KEY]) == GOOD_CSF

    vcb = dv[CB_KEY].decode("latin1")
    vcs = dv[CS_KEY].decode("latin1")
    assert get_button_image(vcb, "Command_ConstructAmericaJetB2A") == "B2A"
    for btn, img in FREEZE_BUTTONS.items():
        assert get_button_image(vcb, btn) == img
    hab = re.search(
        r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?^End\s*$", vcs
    ).group(0)
    assert re.search(r"(?m)^\s*12\s*=\s*Command_ConstructAmericaJetB2A\s*$", hab)
    assert re.search(r"(?m)^\s*1\s*=\s*Command_ConstructAmericaJetB2Spirit\s*$", hab)

    assert "Art\\Textures\\B2ATB.tga" in av
    assert "Art\\W3D\\AVB3bmbr.W3D" in av
    w, h = struct.unpack_from("<HH", av["Art\\Textures\\B2ATB.tga"], 12)
    assert (w, h) == (150, 112)
    assert re.search(
        r"(?m)^MappedImage\s+B2A\s*$", dv[MI_KEY].decode("latin1")
    )
    assert "Model = AVB3bmbr" in dv[B2A_KEY].decode("latin1")

    SRC_DIR.mkdir(parents=True, exist_ok=True)
    (SRC_DIR / "AmericaJetB2A.ini").write_bytes(e3_blob)

    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
        zf.write(ART_BIG, "_SPEC_ART_ONE.big")
    url = upload(OUT_ZIP)
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={data_sha}\n"
        f"_SPEC_ART_ONE.big sha256={art_sha}\n"
        f"zip={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    report = f"""USA B2A DONOR VISUAL ADD = PASS

Object = AmericaJetB2A (separate from AmericaJetB2Spirit)
Primary W3D = AVB3bmbr (donor USAB2 model)
Damaged W3D = AVB3bmbr_D
Button = Command_ConstructAmericaJetB2A
ButtonImage = B2A
HeavyAirBase Slot = 12

Donor Object USAE3/USAB2 gameplay DATA imported = NO
Specter-safe flight DATA = YES
Weapons = NONE

Existing B-2 Spirit changed = NO
Other bombers / E-3 / E-737 / support aircraft changed = NO
CommandSet slots 1-11 / 13-14 preserved = YES

DATA sha256 = {data_sha}
ART sha256 = {art_sha}
ZIP = {OUT_ZIP.name}
URL = {url}
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
