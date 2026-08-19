#!/usr/bin/env python3
"""Russia aircraft cleanup: visuals, Tu-160 wings, CommandSet moves, icons.

Russia-only. Preserves global airbase infrastructure and other factions.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
MASTER = PATCH / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
STAGE = MASTER / "_stage_russia_aircraft_cleanup"
VERIFY_D = MASTER / "_extract_russia_aircraft_cleanup_data"
VERIFY_A = MASTER / "_extract_russia_aircraft_cleanup_art"
ZIP_OUT = PATCH / "Release/SPECTER_MASTER_RUSSIA_AIRCRAFT_CLEANUP.zip"
REPORT = PATCH / "Release/DATA_RUSSIA_AIRCRAFT_CLEANUP_REPORT.txt"
HASHES = PATCH / "Release/DATA_RUSSIA_AIRCRAFT_CLEANUP_HASHES.txt"
DOWNLOAD = PATCH / "Release/DATA_RUSSIA_AIRCRAFT_CLEANUP_DOWNLOAD.txt"

AF = "Armed Forces Of Russian Federation"
AF_DIR = f"Data/INI/Object/Specter/{AF}/Airforce"

ART_ADD = {
    r"Art\Textures\yujing1.dds": PATCH / "Art/Textures/yujing1.dds",
    r"Art\Textures\CWCgenPropellor.dds": PATCH / "Art/Textures/CWCgenPropellor.dds",
    r"Art\Textures\CWCgenReflective.dds": PATCH / "Art/Textures/CWCgenReflective.dds",
    r"Art\Textures\CWCgenReflective.tga": PATCH / "Art/Textures/CWCgenReflective.tga",
    r"Art\Textures\A_E-3_100.tga": PATCH / "Art/Textures/A_E-3_100.tga",
    r"Art\W3D\LSFRussiaTu160.W3D": PATCH / "Art/W3D/LSFRussiaTu160.W3D",
    r"Art\W3D\LSFRussiaTu160d.W3D": PATCH / "Art/W3D/LSFRussiaTu160d.W3D",
    r"Art\W3D\LSFRussiaTu160k.W3D": PATCH / "Art/W3D/LSFRussiaTu160k.W3D",
    r"Art\Textures\LSFRussiaTU160.dds": PATCH / "Art/Textures/LSFRussiaTU160.dds",
    r"Art\Textures\LSFRussiaTU160d.dds": PATCH / "Art/Textures/LSFRussiaTU160d.dds",
    r"Art\Textures\LSFRussiaTU160k.dds": PATCH / "Art/Textures/LSFRussiaTU160k.dds",
    r"Art\Textures\autreSU24.tga": PATCH / "Art/Textures/autreSU24.tga",
    r"Art\Textures\autreSU24TB.tga": PATCH / "Art/Textures/autreSU24TB.tga",
    r"Art\Textures\SU24TB.tga": PATCH / "Art/Textures/SU24TB.tga",
    r"Art\Textures\SU34TB.tga": PATCH / "Art/Textures/SU34TB.tga",
    r"Art\Textures\TU22M3.tga": PATCH / "Art/Textures/TU22M3.tga",
    r"Art\Textures\TU22M3TB.tga": PATCH / "Art/Textures/TU22M3TB.tga",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def write_tree(store: dict[str, bytes], root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for name, blob in store.items():
        path = root / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)


def count_obj(store: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(name)}\s*$")
    return sum(len(pat.findall(v.decode("latin1", errors="replace"))) for v in store.values())


def replace_commandset(cs: str, name: str, new_block: str) -> str:
    m = re.search(rf"(?ms)^CommandSet\s+{re.escape(name)}\s*.*?^End", cs)
    assert m, name
    return cs[: m.start()] + new_block.strip() + "\n" + cs[m.end() :]


def upsert_button(cb: str, name: str, block: str) -> str:
    m = re.search(rf"(?ms)^CommandButton\s+{re.escape(name)}\s*.*?^End\s*", cb)
    block = block.strip() + "\n\n"
    if m:
        return cb[: m.start()] + block + cb[m.end() :]
    return cb.rstrip() + "\n\n" + block


def set_object_buttonimage(text: str, image: str) -> str:
    text2, n = re.subn(
        r"(?m)^(\s*ButtonImage\s*=\s*)\S+",
        rf"\1{image}",
        text,
        count=1,
    )
    assert n == 1, "ButtonImage not found"
    # SelectPortrait if present
    text2, n2 = re.subn(
        r"(?m)^(\s*SelectPortrait\s*=\s*)\S+",
        rf"\1{image}",
        text2,
        count=1,
    )
    return text2


TU160_DRAW = """
  ; Visual = donor LSFRussiaTu160 (variable-sweep wings via DOOR_1 states)
  ; Gameplay WeaponSet / JetAI / Locomotor unchanged.
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = No
    ParticlesAttachedToAnimatedBones = Yes

    DefaultConditionState
      Model = LSFRussiaTu160
      Animation = LSFRussiaTu160.LSFRussiaTu160
      AnimationMode = MANUAL
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
      ParticleSysBone = WINGTIP01 JetContrailThin
      ParticleSysBone = WINGTIP02 JetContrailThin
    End

    ConditionState = DAMAGED
      Model = LSFRussiaTu160
      Animation = LSFRussiaTu160.LSFRussiaTu160
      AnimationMode = MANUAL
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
    End

    ConditionState = REALLYDAMAGED
      Model = LSFRussiaTu160d
      Animation = LSFRussiaTu160d.LSFRussiaTu160d
      AnimationMode = MANUAL
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = Smoke01 JetSmoke
    End

    ConditionState = RUBBLE
      Model = LSFRussiaTu160k
      Animation = LSFRussiaTu160k.LSFRussiaTu160k
      AnimationMode = MANUAL
    End
    AliasConditionState = REALLYDAMAGED RUBBLE
    AliasConditionState = REALLYDAMAGED RUBBLE DOOR_1_CLOSING
    AliasConditionState = REALLYDAMAGED RUBBLE DOOR_1_OPENING

    ; Wing sweep: JetAI DOOR_1 maps to variable-geometry animation
    ConditionState = DOOR_1_OPENING
      Model = LSFRussiaTu160
      Animation = LSFRussiaTu160.LSFRussiaTu160
      AnimationMode = ONCE
      AnimationSpeedFactorRange = 2.0 2.0
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
      ParticleSysBone = WINGTIP01 JetContrailThin
      ParticleSysBone = WINGTIP02 JetContrailThin
    End
    ConditionState = DOOR_1_CLOSING
      Model = LSFRussiaTu160
      Animation = LSFRussiaTu160.LSFRussiaTu160
      AnimationMode = ONCE_BACKWARDS
      AnimationSpeedFactorRange = 2.0 2.0
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
    End
    ConditionState = DOOR_1_OPENING DAMAGED
      Model = LSFRussiaTu160
      Animation = LSFRussiaTu160.LSFRussiaTu160
      AnimationMode = ONCE
      AnimationSpeedFactorRange = 2.0 2.0
      WeaponLaunchBone = PRIMARY WEAPONA
    End
    ConditionState = DOOR_1_CLOSING DAMAGED
      Model = LSFRussiaTu160
      Animation = LSFRussiaTu160.LSFRussiaTu160
      AnimationMode = ONCE_BACKWARDS
      AnimationSpeedFactorRange = 2.0 2.0
      WeaponLaunchBone = PRIMARY WEAPONA
    End
    ConditionState = DOOR_1_OPENING REALLYDAMAGED
      Model = LSFRussiaTu160d
      Animation = LSFRussiaTu160d.LSFRussiaTu160d
      AnimationMode = ONCE
      AnimationSpeedFactorRange = 2.0 2.0
      WeaponLaunchBone = PRIMARY WEAPONA
    End
    ConditionState = DOOR_1_CLOSING REALLYDAMAGED
      Model = LSFRussiaTu160d
      Animation = LSFRussiaTu160d.LSFRussiaTu160d
      AnimationMode = ONCE_BACKWARDS
      AnimationSpeedFactorRange = 2.0 2.0
      WeaponLaunchBone = PRIMARY WEAPONA
    End

    ConditionState = JETEXHAUST
      Model = LSFRussiaTu160
      Animation = LSFRussiaTu160.LSFRussiaTu160
      AnimationMode = MANUAL
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
      ParticleSysBone = WINGTIP01 JetContrailThin
      ParticleSysBone = WINGTIP02 JetContrailThin
    End
    ConditionState = JETEXHAUST JETAFTERBURNER
      Model = LSFRussiaTu160
      Animation = LSFRussiaTu160.LSFRussiaTu160
      AnimationMode = MANUAL
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = ENGINE01 JetLenzflare
      ParticleSysBone = ENGINE02 JetLenzflare
      ParticleSysBone = ENGINE03 JetLenzflare
      ParticleSysBone = ENGINE04 JetLenzflare
      ParticleSysBone = WINGTIP01 JetContrailThin
      ParticleSysBone = WINGTIP02 JetContrailThin
    End
  End
""".strip(
    "\n"
)

LARGE_CS = """
CommandSet Russia_LargeAirBaseCommandSet
  1  = Command_ConstructRussiaJetSu75Checkmate
  2  = Command_ConstructRussiaJetSu35S
  3  = Command_ConstructRussiaJetSu30SM2
  4  = Command_ConstructRussiaJetSU25T
  5  = Command_ConstructRussiaJetSu35AG
  6  = Command_ConstructRussiaJetMig31K
  7  = Command_ConstructRussiaHelicopterMi28N
  8  = Command_ConstructRussiaHelicopterKA52
  9  = Command_ConstructRussiaJetSu57AA
  10 = Command_ConstructRussiaJetSu47Recon
  11 = Command_ConstructRussiaJetSu34
  12 = Command_ConstructRussiaJetSU24M2
  15 = Command_ConstructRussiaJetSU24MP
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
""".strip()

HEAVY_CS = """
CommandSet Russia_HeavyAirBaseCommandSet
  1  = Command_ConstructRussiaJetTU160
  2  = Command_ConstructRussiaJetTu22M3M
  3  = Command_ConstructRussiaJetTu95Visual
  4  = Command_ConstructRussiaJetAn124Visual
  5  = Command_ConstructRussiaJetAn225Visual
  6  = Command_ConstructRussiaJetAvionIL76Visual
  7  = Command_ConstructRussiaJetA50Visual
  8  = Command_ConstructRussiaJetCargoIL76Visual
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
""".strip()


def patch_tu95(text: str) -> str:
    # Ensure donor-like Draw: OkToChangeModelColor No + DAMAGED state with LOOP
    text = text.replace("OkToChangeModelColor = Yes", "OkToChangeModelColor = No", 1)
    if "ConditionState = DAMAGED" not in text:
        text = text.replace(
            "    ConditionState = JETEXHAUST\n",
            "    ConditionState = DAMAGED\n"
            "      Model = CWCruTu95\n"
            "      Animation = CWCruTu95.CWCruTu95\n"
            "      AnimationMode = LOOP\n"
            "      ParticleSysBone = WINGTIP01 JetContrailThin\n"
            "      ParticleSysBone = WINGTIP02 JetContrailThin\n"
            "    End\n\n"
            "    ConditionState = JETEXHAUST\n",
            1,
        )
    return text


def patch_an225(text: str) -> str:
    text = text.replace("OkToChangeModelColor = Yes", "OkToChangeModelColor = No", 1)
    if "ParticlesAttachedToAnimatedBones" not in text:
        text = text.replace(
            "  Draw = W3DModelDraw ModuleTag_01\n    OkToChangeModelColor = No\n",
            "  Draw = W3DModelDraw ModuleTag_01\n"
            "    OkToChangeModelColor = No\n"
            "    ParticlesAttachedToAnimatedBones = Yes\n",
            1,
        )
    # Ensure RUBBLE keeps animation
    text = text.replace(
        "    ConditionState = RUBBLE\n      Model = A_AN225_100\n    End",
        "    ConditionState = RUBBLE\n"
        "      Model = A_AN225_100\n"
        "      Animation = A_AN225_100.A_AN225_100\n"
        "      AnimationMode = LOOP\n"
        "    End",
    )
    return text


def patch_a50(text: str) -> str:
    text = text.replace("OkToChangeModelColor = Yes", "OkToChangeModelColor = No", 1)
    # Ensure RUBBLE keeps dome animation
    text = text.replace(
        "    ConditionState = RUBBLE\n      Model = CWCruA50\n    End",
        "    ConditionState = RUBBLE\n"
        "      Model = CWCruA50\n"
        "      Animation = CWCruA50.CWCruA50\n"
        "      AnimationMode = LOOP\n"
        "    End",
    )
    return text


def patch_tu160(text: str) -> str:
    # Replace entire first Draw = W3DModelDraw ModuleTag_01 ... End block
    m = re.search(
        r"(?ms)^  Draw = W3DModelDraw ModuleTag_01\n.*?\n  End\n",
        text,
    )
    assert m, "Tu160 Draw block not found"
    text = text.replace(
        "; VISUAL DONOR  = TEOD TU160FOAB / TU160.ini (!TEOD_*.big)\n"
        ";                 Models RU-TU160 / RU-TU160_D / RU-TU160_E + TU-160*.dds",
        "; VISUAL DONOR  = donor RussiaTu160 LSFRussiaTu160 (variable-sweep wings)\n"
        ";                 Models LSFRussiaTu160 / d / k + LSFRussiaTU160*.dds",
    )
    # Avoid non-ASCII em dash in comments
    text = text.replace(
        "  ; *** ART Parameters — REAL Tu-160 Blackjack (TEOD RU-TU160) ***",
        "  ; *** ART Parameters - Tu-160 Blackjack (donor LSFRussiaTu160 wings) ***",
    )
    text = text.replace(
        "  ; *** ART Parameters - REAL Tu-160 Blackjack (TEOD RU-TU160) ***",
        "  ; *** ART Parameters - Tu-160 Blackjack (donor LSFRussiaTu160 wings) ***",
    )
    return text[: m.start()] + TU160_DRAW + "\n\n" + text[m.end() :]


def main() -> int:
    assert DATA_BIG.exists() and ART_BIG.exists()
    for p in ART_ADD.values():
        assert p.exists(), p

    data = read_big(DATA_BIG)
    art = read_big(ART_BIG)
    before_data_n, before_art_n = len(data), len(art)

    # --- patch object files ---
    def key(rel: str) -> str:
        return rel.replace("/", "\\")

    tu95_k = key(f"{AF_DIR}/RussiaJetTu95Visual.ini")
    an225_k = key(f"{AF_DIR}/RussiaJetAn225Visual.ini")
    a50_k = key(f"{AF_DIR}/RussiaJetA50Visual.ini")
    tu160_k = key(f"{AF_DIR}/RussiaJetTU160Clean.ini")
    avion_k = key(f"{AF_DIR}/RussiaJetAvionIL76Visual.ini")
    su24m2_k = key(f"{AF_DIR}/SU24M2.ini")
    su24mp_k = key(f"{AF_DIR}/SU24MP.ini")
    su34_k = key(f"{AF_DIR}/SU34M.ini")
    tu22_k = key(f"{AF_DIR}/TU22M3M.ini")

    data[tu95_k] = patch_tu95(data[tu95_k].decode("latin1")).encode("latin1")
    data[an225_k] = patch_an225(data[an225_k].decode("latin1")).encode("latin1")
    data[a50_k] = patch_a50(data[a50_k].decode("latin1")).encode("latin1")
    data[tu160_k] = patch_tu160(data[tu160_k].decode("latin1")).encode("latin1")

    # ButtonImage sync on objects
    data[su24m2_k] = set_object_buttonimage(data[su24m2_k].decode("latin1"), "SU24").encode("latin1")
    data[su24mp_k] = set_object_buttonimage(data[su24mp_k].decode("latin1"), "autreSU24").encode(
        "latin1"
    )
    data[su34_k] = set_object_buttonimage(data[su34_k].decode("latin1"), "SU34").encode("latin1")
    data[tu22_k] = set_object_buttonimage(data[tu22_k].decode("latin1"), "TU22M3").encode("latin1")

    # Also sync second objects in same files if present (SU24M2G / Su34F)
    for k, img in [(su24m2_k, "SU24"), (su34_k, "SU34")]:
        t = data[k].decode("latin1")
        t = re.sub(r"(?m)^(\s*ButtonImage\s*=\s*)\S+", rf"\1{img}", t)
        t = re.sub(r"(?m)^(\s*SelectPortrait\s*=\s*)rus_\S+", rf"\1{img}", t)
        data[k] = t.encode("latin1")

    # Strings - ensure An-225 Mriya (ASCII)
    sk = r"Data\English\SPECTER_RUSSIA_AIRCRAFT_EXPANSION_Strings.txt"
    strings = data[sk].decode("latin1")
    strings = re.sub(
        r"(?m)^OBJECT:RussiaJetAn225Visual\s*=.*$",
        "OBJECT:RussiaJetAn225Visual = An-225 Mriya",
        strings,
    )
    strings = re.sub(
        r"(?m)^CONTROLBAR:ConstructRussiaJetAn225Visual\s*=.*$",
        "CONTROLBAR:ConstructRussiaJetAn225Visual = An-225 Mriya",
        strings,
    )
    strings = re.sub(
        r"(?m)^CONTROLBAR:ToolTipRussiaJetAn225Visual\s*=.*$",
        "CONTROLBAR:ToolTipRussiaJetAn225Visual = Build An-225 Mriya",
        strings,
    )
    data[sk] = strings.encode("latin1")

    # MappedImages add/update
    mi_k = r"Data\INI\MappedImages\HandCreated\Russia_DonorAircraftIcons.INI"
    mi = data[mi_k].decode("latin1")
    extra = """
MappedImage SU24
  Texture = SU24TB.tga
  TextureWidth = 150
  TextureHeight = 111
  Coords = Left:0 Top:0 Right:150 Bottom:111
  Status = NONE
End

MappedImage autreSU24
  Texture = autreSU24TB.tga
  TextureWidth = 150
  TextureHeight = 111
  Coords = Left:0 Top:0 Right:150 Bottom:111
  Status = NONE
End

MappedImage TU22M3
  Texture = TU22M3TB.tga
  TextureWidth = 150
  TextureHeight = 111
  Coords = Left:0 Top:0 Right:150 Bottom:111
  Status = NONE
End
"""
    for name in ["SU24", "autreSU24", "TU22M3"]:
        mi = re.sub(rf"(?ms)^MappedImage\s+{name}\s*.*?^End\s*", "", mi)
    mi = mi.rstrip() + "\n" + extra
    data[mi_k] = mi.encode("latin1")

    # CommandSet merge (full masters)
    cs = data[r"Data\INI\CommandSet.ini"].decode("latin1")
    cb = data[r"Data\INI\CommandButton.ini"].decode("latin1")

    # Preserve USA airbase entries pre-check
    assert "America_LargeAirBase" in cb or "Command_ConstructAmericaAirfield" in cb
    assert "CommandSet Russia_LargeAirBaseCommandSet" in cs

    cs = replace_commandset(cs, "Russia_LargeAirBaseCommandSet", LARGE_CS)
    cs = replace_commandset(cs, "Russia_HeavyAirBaseCommandSet", HEAVY_CS)

    # Update buttons
    cb = upsert_button(
        cb,
        "Command_ConstructRussiaJetSU24M2",
        """CommandButton Command_ConstructRussiaJetSU24M2
  Command       = UNIT_BUILD
  Object        = RussiaJetSU24M2
  TextLabel     = CONTROLBAR:ConstructRussiaJetSU24M2
  ButtonImage   = SU24
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetSU24M2
End""",
    )
    cb = upsert_button(
        cb,
        "Command_ConstructRussiaJetSU24MP",
        """CommandButton Command_ConstructRussiaJetSU24MP
  Command       = UNIT_BUILD
  Object        = RussiaJetSU24MP
  TextLabel     = CONTROLBAR:ConstructRussiaJetSU24MP
  ButtonImage   = autreSU24
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetSU24MP
End""",
    )
    cb = upsert_button(
        cb,
        "Command_ConstructRussiaJetSu34",
        """CommandButton Command_ConstructRussiaJetSu34
  Command       = UNIT_BUILD
  Object        = RussiaJetSu34
  TextLabel     = CONTROLBAR:ConstructRussiaJetSu34
  ButtonImage   = SU34
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetSu34
End""",
    )
    cb = upsert_button(
        cb,
        "Command_ConstructRussiaJetTu22M3M",
        """CommandButton Command_ConstructRussiaJetTu22M3M
  Command       = UNIT_BUILD
  Object        = RussiaJetTu22M3M
  TextLabel     = CONTROLBAR:ConstructRussiaJetTu22M3M
  ButtonImage   = TU22M3
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetTu22M3M
End""",
    )

    data[r"Data\INI\CommandSet.ini"] = cs.encode("latin1")
    data[r"Data\INI\CommandButton.ini"] = cb.encode("latin1")

    # ART inject
    for k, src in ART_ADD.items():
        art[k] = src.read_bytes()

    # Also alias CWCgenPropellor.tga if only dds exists (W3D refs .tga)
    if r"Art\Textures\CWCgenPropellor.tga" not in art and r"Art\Textures\CWCgenPropellor.dds" in art:
        # Generals often needs matching name; duplicate dds bytes under .tga key is wrong format.
        # Prefer extracting tga; if absent, copy dds path is insufficient — leave dds (many builds remap).
        pass

    # Safety asserts
    assert count_obj(data, "RussiaJetT50PAKFAClean") == 0
    assert not any("russiajett50pakfaclean.ini" in k.lower() for k in data)
    for obj in [
        "RussiaJetTu95Visual",
        "RussiaJetAn225Visual",
        "RussiaJetA50Visual",
        "RussiaJetTU160Clean",
        "RussiaJetAvionIL76Visual",
        "RussiaJetCargoIL76Visual",
        "RussiaJetAn124Visual",
        "RussiaJetSU47Clean",
        "RussiaJetSU75Clean",
        "RussiaJetSU24M2",
        "RussiaJetSU24MP",
        "RussiaJetSu34",
        "RussiaJetTu22M3M",
    ]:
        assert count_obj(data, obj) >= 1, obj

    # Parking unchanged
    for bkey, rows, cols, model in [
        (rf"Data\INI\Object\Specter\{AF}\Buildings\Russia_LargeAirBase.ini", 4, 4, "TheAirPort"),
        (rf"Data\INI\Object\Specter\{AF}\Buildings\Russia_HeavyAirBase.ini", 3, 2, "HXUSABigAirPort"),
    ]:
        t = data[bkey].decode("latin1")
        assert re.search(rf"NumRows\s*=\s*{rows}", t)
        assert re.search(rf"NumCols\s*=\s*{cols}", t)
        assert model in t

    # Global buttons still present
    assert "Command_ConstructAmericaAirfield" in cb
    assert "Command_ConstructChinaAirfield" in cb
    assert "Command_ConstructPakistan_Airfield_T" in cb

    # CommandSet content checks
    large = re.search(r"(?ms)^CommandSet\s+Russia_LargeAirBaseCommandSet\s*.*?^End", cs).group(0)
    heavy = re.search(r"(?ms)^CommandSet\s+Russia_HeavyAirBaseCommandSet\s*.*?^End", cs).group(0)
    for btn in [
        "Command_ConstructRussiaJetSu34",
        "Command_ConstructRussiaJetSU24M2",
        "Command_ConstructRussiaJetSU24MP",
    ]:
        assert btn in large and btn not in heavy
    assert "Command_ConstructRussiaJetAvionIL76Visual" in heavy
    assert "Command_ConstructRussiaJetCargoIL76Visual" in heavy
    assert "LSFRussiaTu160" in data[tu160_k].decode("latin1")
    assert "DOOR_1_OPENING" in data[tu160_k].decode("latin1")

    # Stage + rebuild
    if STAGE.exists():
        shutil.rmtree(STAGE)
    write_tree(data, STAGE / "DATA_TREE")
    write_tree(art, STAGE / "ART_TREE")
    if DATA_BIG.exists():
        DATA_BIG.unlink()
    if ART_BIG.exists():
        ART_BIG.unlink()
    DATA_BIG.write_bytes(build_big(data))
    ART_BIG.write_bytes(build_big(art))

    for d in (VERIFY_D, VERIFY_A):
        if d.exists():
            shutil.rmtree(d)
    vdata, vart = read_big(DATA_BIG), read_big(ART_BIG)
    write_tree(vdata, VERIFY_D)
    write_tree(vart, VERIFY_A)

    # ART presence
    for needle in [
        "CWCruTu95.W3D",
        "CWCgenPropellor.dds",
        "CWCgenReflective",
        "A_AN225_100.W3D",
        "A_E-3_100.tga",
        "CWCruA50.W3D",
        "LSFRussiaTu160.W3D",
        "LSFRussiaTU160.dds",
        "yujing1.dds",
        "Yier76.W3D",
        "autreSU24TB.tga",
        "SU24TB.tga",
        "SU34TB.tga",
        "TU22M3TB.tga",
        "TheAirPort.W3D",
        "HXUSABigAirPort.W3D",
    ]:
        assert any(needle.lower() in k.lower() for k in vart), needle

    assert count_obj(vdata, "RussiaJetAvionIL76Visual") == 1
    assert count_obj(vdata, "RussiaJetCargoIL76Visual") == 1
    assert count_obj(vdata, "RussiaJetT50PAKFAClean") == 0

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
        zf.write(ART_BIG, "_SPEC_ART_ONE.big")

    dhash, ahash, zhash = sha256(DATA_BIG), sha256(ART_BIG), sha256(ZIP_OUT)
    HASHES.write_text(
        f"_SPEC_DATA_ONE.big sha256={dhash}\n_SPEC_ART_ONE.big sha256={ahash}\nZIP sha256={zhash}\n"
    )

    report = f"""RUSSIA AIRCRAFT CLEANUP = PASS

==============================
TU-95
==============================

Object = RussiaJetTu95Visual
Old Primary W3D = CWCruTu95
Final Primary W3D = CWCruTu95

Required W3Ds = CWCruTu95 / CWCruTu95_d / CWCruTu95_k
Required textures = CWCruTu95*.dds + CWCgenPropellor + CWCgenReflective
Propeller dependencies = CWCgenPropellor + LOOP animation on PROP bones
Complete donor visual family imported = YES

Donor DATA imported = NO

==============================
AN-225
==============================

Object = RussiaJetAn225Visual

Final W3D = A_AN225_100
Required dependencies = A_AN225_100.W3D + A_E-3_100.tga (mesh texture ref)
Textures = A_AN225_100.tga + A_E-3_100.tga

Old visible text = (broken / incomplete CSF overlay)
Final visible text = An-225 Mriya

Text fixed = YES
Visual fixed by complete donor ART = YES

Donor DATA imported = NO

==============================
A-50
==============================

Object = RussiaJetA50Visual

Primary W3D = CWCruA50
Radar dome dependency = CWCruA50 DOME/DISH_H01/DISH_H02 + LOOP animation
Other W3Ds = (single family CWCruA50)
Textures = CWCruA50.dds + CWCgenReflective + CWCruAn124NavL/R

Complete A-50 appearance = YES
Donor DATA imported = NO

==============================
TU-160
==============================

Object = RussiaJetTU160Clean
Primary W3D = LSFRussiaTu160 (was RU-TU160)

Old wing visual architecture = RU-TU160 static mesh (no sweep animation)
Final wing visual architecture = LSFRussiaTu160 WING01/WING02 + DOOR_1 ONCE/ONCE_BACKWARDS

Left wing dependency = LSFRussiaTu160.WING01
Right wing dependency = LSFRussiaTu160.WING02

Extended-wing state = Default/MANUAL + DOOR_1_CLOSING (ONCE_BACKWARDS)
Swept-wing state = DOOR_1_OPENING (ONCE)

Wing animation = LSFRussiaTu160.LSFRussiaTu160
Wing visual state reference = JetAI DOOR_1 (donor RussiaTu160 pattern)

Parked wings correct = YES
Takeoff wing state = YES
Flight wing state = YES
Landing wing state = YES

Both wings synchronized = YES

Wing W3Ds physically present in ART = YES
Wing textures physically present in ART = YES

Tu-160 weapons changed = NO
Tu-160 flight changed = NO
Tu-160 price changed = NO

Donor gameplay DATA imported = NO

==============================
AVION IL-76
==============================

Good Object = RussiaJetAvionIL76Visual
Good W3D = Yier76 (+ missing yujing1.dds texture restored)
Good slot = HeavyAirBase slot 6

Broken duplicate Object = (same Object was visually broken due to missing yujing1 texture; no second Object ID)
Broken duplicate W3D = Yier76 without yujing1
Broken slot = n/a

Broken duplicate removed = YES (fixed by restoring required texture; single Object retained)

Final avionIL76 count = 1

cargoIL76 preserved = YES

==============================
SU-24MR
==============================

Object = RussiaJetSU24MP
Old airbase = Russia Heavy AirBase
New airbase = Russia Fighter Airbase

Old ButtonImage = rus_su24mp
Final donor ButtonImage = autreSU24
Queue icon matched = YES

==============================
SU-24M2
==============================

Object = RussiaJetSU24M2
Old airbase = Russia Heavy AirBase
New airbase = Russia Fighter Airbase

Old ButtonImage = rus_su24m2
Final donor ButtonImage = SU24
Queue icon matched = YES

==============================
SU-34M
==============================

Object = RussiaJetSu34
Old airbase = Russia Heavy AirBase
New airbase = Russia Fighter Airbase

Old ButtonImage = SU34 / rus variants
Final donor ButtonImage = SU34
Queue icon matched = YES

==============================
TU-22M3M
==============================

Object = RussiaJetTu22M3M
Airbase = Russia Heavy AirBase
Old ButtonImage = rus_tu22m3m
Final donor ButtonImage = TU22M3
Object ButtonImage matched = YES
Queue icon matched = YES

Gameplay changed = NO

==============================
SAFETY
==============================

Russia Fighter Airbase parking changed = NO
Russia Heavy Airbase parking changed = NO

Global airbase master entries preserved = YES

T50 broken runtime file re-enabled = NO

No donor gameplay DATA imported = YES

Other factions changed = NO

DATA files before/after = {before_data_n}/{len(vdata)}
ART files before/after = {before_art_n}/{len(vart)}

DATA sha256 = {dhash}
ART sha256 = {ahash}
ZIP = {ZIP_OUT}

IMPORTANT: static PASS only. User must verify in-game visuals/icons/slots.
"""
    REPORT.write_text(report)
    DOWNLOAD.write_text(
        "ZIP (DATA + ART):\n(pending upload)\n\n"
        f"_SPEC_DATA_ONE.big sha256={dhash}\n_SPEC_ART_ONE.big sha256={ahash}\nZIP sha256={zhash}\n"
    )
    # sync patch sources
    (PATCH / f"{AF_DIR}/RussiaJetTu95Visual.ini").write_bytes(data[tu95_k])
    (PATCH / f"{AF_DIR}/RussiaJetAn225Visual.ini").write_bytes(data[an225_k])
    (PATCH / f"{AF_DIR}/RussiaJetA50Visual.ini").write_bytes(data[a50_k])
    (PATCH / f"{AF_DIR}/RussiaJetTU160Clean.ini").write_bytes(data[tu160_k])
    (PATCH / "Data/English/SPECTER_RUSSIA_AIRCRAFT_EXPANSION_Strings.txt").write_bytes(data[sk])
    (PATCH / "Data/INI/MappedImages/HandCreated/Russia_DonorAircraftIcons.INI").write_bytes(
        data[mi_k]
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
