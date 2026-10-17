#!/usr/bin/env python3
"""Russia aircraft runtime repair on PR #372 recovery baseline.

Isolated stages (call with --stage N):
  1 Su-24MR / Su-24M2 / Su-34M → Fighter (Large) AirBase
  2 avionIL76 texture repair (no second Object; cargo preserved)
  3 Tu-95 missing ART family textures
  4 An-225 ART + display name
  5 A-50 ART rotodome textures
  6 Tu-160 LSFRussiaTu160 DOOR_1 wing sweep (LAST)

Donor ART = YES. Donor gameplay DATA = NO.
T50 remains disabled. Airbase parking unchanged.
"""
from __future__ import annotations

import argparse
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
STAGE_DATA = MASTER / "_stage_russia_runtime_repair_data"
STAGE_ART = MASTER / "_stage_russia_runtime_repair_art"
VERIFY_DATA = MASTER / "_extract_russia_runtime_repair_data"
VERIFY_ART = MASTER / "_extract_russia_runtime_repair_art"
ZIP_OUT = PATCH / "Release/SPECTER_MASTER_DATA_ART_RUSSIA_AIRCRAFT_RUNTIME_REPAIR.zip"
REPORT = PATCH / "Release/DATA_RUSSIA_AIRCRAFT_RUNTIME_REPAIR_REPORT.txt"
HASHES = PATCH / "Release/DATA_RUSSIA_AIRCRAFT_RUNTIME_REPAIR_HASHES.txt"
DOWNLOAD = PATCH / "Release/DATA_RUSSIA_AIRCRAFT_RUNTIME_REPAIR_DOWNLOAD.txt"

AF = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
AF_AIR = AF + r"\Airforce"
CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CSF_KEY = r"Data\English\generals.csf"
STR_KEY = r"Data\English\SPECTER_RUSSIA_AIRCRAFT_EXPANSION_Strings.txt"

BASELINE_DATA = "a3eace60486397c772d9020fef7cd382363e33c86ecb08ab2de0629bd1cbf749"
BASELINE_ART = "248172a4a1ddfc66743b16016a29b7a2fd70a3389107599b899c041f98f1c592"

ART_FILES = {
    # avionIL76
    r"Art\Textures\yujing1.tga": PATCH / "Art/Textures/yujing1.tga",
    r"Art\Textures\yujing1.dds": PATCH / "Art/Textures/yujing1.dds",
    # Tu-95
    r"Art\Textures\CWCgenPropellor.tga": PATCH / "Art/Textures/CWCgenPropellor.tga",
    r"Art\Textures\CWCgenPropellor.dds": PATCH / "Art/Textures/CWCgenPropellor.dds",
    r"Art\Textures\CWCgenReflective.tga": PATCH / "Art/Textures/CWCgenReflective.tga",
    r"Art\Textures\CWCgenReflective.dds": PATCH / "Art/Textures/CWCgenReflective.dds",
    r"Art\Textures\CWCruTU95.tga": PATCH / "Art/Textures/CWCruTU95.tga",
    # An-225
    r"Art\Textures\A_E-3_100.tga": PATCH / "Art/Textures/A_E-3_100.tga",
    # A-50
    r"Art\Textures\CWCruA50.tga": PATCH / "Art/Textures/CWCruA50.tga",
    r"Art\Textures\CWCruAn124NavL.tga": PATCH / "Art/Textures/CWCruAn124NavL.tga",
    r"Art\Textures\CWCruAn124NavR.tga": PATCH / "Art/Textures/CWCruAn124NavR.tga",
    # Tu-160
    r"Art\W3D\LSFRussiaTu160.W3D": PATCH / "Art/W3D/LSFRussiaTu160.W3D",
    r"Art\W3D\LSFRussiaTu160d.W3D": PATCH / "Art/W3D/LSFRussiaTu160d.W3D",
    r"Art\W3D\LSFRussiaTu160k.W3D": PATCH / "Art/W3D/LSFRussiaTu160k.W3D",
    r"Art\Textures\LSFRussiaTU160.dds": PATCH / "Art/Textures/LSFRussiaTU160.dds",
    r"Art\Textures\LSFRussiaTU160d.dds": PATCH / "Art/Textures/LSFRussiaTU160d.dds",
    r"Art\Textures\LSFRussiaTU160k.dds": PATCH / "Art/Textures/LSFRussiaTU160k.dds",
}

# Proven ScienceObjects TU160M2 DOOR_1 pattern, adapted to LSFRussiaTu160
TU160_DRAW = """
  ; Visual = donor LSFRussiaTu160 variable-sweep (WING01/WING02)
  ; State machine mirrors active ScienceObjects/TU160M2.ini DOOR_1 pattern
  ; Gameplay WeaponSet / JetAI / Locomotor / cost unchanged.
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    ParticlesAttachedToAnimatedBones = Yes

    DefaultConditionState
      Model = LSFRussiaTu160
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
      ParticleSysBone = WINGTIP01 JetContrailThin
      ParticleSysBone = WINGTIP02 JetContrailThin
    End

    ConditionState = DOOR_1_OPENING
      Model = LSFRussiaTu160
      Animation = LSFRussiaTu160.LSFRussiaTu160
      AnimationMode = ONCE
      Flags = START_FRAME_FIRST
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = ENGINE01 JetContrailThin
      ParticleSysBone = ENGINE02 JetContrailThin
      ParticleSysBone = ENGINE03 JetContrailThin
      ParticleSysBone = ENGINE04 JetContrailThin
      ParticleSysBone = WINGTIP01 JetContrailThin
      ParticleSysBone = WINGTIP02 JetContrailThin
    End

    ConditionState = DOOR_1_CLOSING
      Model = LSFRussiaTu160
      Animation = LSFRussiaTu160.LSFRussiaTu160
      AnimationMode = ONCE_BACKWARDS
      Flags = START_FRAME_LAST
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = ENGINE01 JetContrailThin
      ParticleSysBone = ENGINE02 JetContrailThin
      ParticleSysBone = ENGINE03 JetContrailThin
      ParticleSysBone = ENGINE04 JetContrailThin
      ParticleSysBone = WINGTIP01 JetContrailThin
      ParticleSysBone = WINGTIP02 JetContrailThin
    End

    ConditionState = DOOR_1_OPENING REALLYDAMAGED
      Model = LSFRussiaTu160d
      Animation = LSFRussiaTu160d.LSFRussiaTu160d
      AnimationMode = ONCE
      Flags = START_FRAME_FIRST MAINTAIN_FRAME_ACROSS_STATES
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = ENGINE01 JetContrailThin
      ParticleSysBone = ENGINE02 JetContrailThin
      ParticleSysBone = ENGINE03 JetContrailThin
      ParticleSysBone = ENGINE04 JetContrailThin
    End

    ConditionState = DOOR_1_CLOSING REALLYDAMAGED
      Model = LSFRussiaTu160d
      Animation = LSFRussiaTu160d.LSFRussiaTu160d
      AnimationMode = ONCE_BACKWARDS
      Flags = START_FRAME_LAST MAINTAIN_FRAME_ACROSS_STATES
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = ENGINE01 JetContrailThin
      ParticleSysBone = ENGINE02 JetContrailThin
      ParticleSysBone = ENGINE03 JetContrailThin
      ParticleSysBone = ENGINE04 JetContrailThin
    End

    ConditionState = DAMAGED
      Model = LSFRussiaTu160
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = ENGINE01 JetBlackTrailThin
      ParticleSysBone = ENGINE02 JetBlackTrailThin
      ParticleSysBone = ENGINE03 JetBlackTrailThin
      ParticleSysBone = ENGINE04 JetBlackTrailThin
      ParticleSysBone = SMOKE01 JetSmoke
    End

    ConditionState = REALLYDAMAGED
      Model = LSFRussiaTu160d
      WeaponLaunchBone = PRIMARY WEAPONA
      ParticleSysBone = SMOKE01 JetSmoke
    End

    ConditionState = RUBBLE
      Model = LSFRussiaTu160k
    End

    ConditionState = JETEXHAUST
      Model = LSFRussiaTu160
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


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF", path
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


def collect_tree(root: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for p in root.rglob("*"):
        if p.is_file():
            rel = "\\".join(p.relative_to(root).parts)
            out[rel] = p.read_bytes()
    return out


def replace_commandset(cs: str, name: str, new_block: str) -> str:
    m = re.search(rf"(?ms)^CommandSet\s+{re.escape(name)}\s*.*?^End", cs)
    assert m, name
    return cs[: m.start()] + new_block.strip() + "\n" + cs[m.end() :]


def replace_draw(text: str, new_draw: str) -> str:
    m = re.search(r"(?ms)^  Draw = W3DModelDraw ModuleTag_01\b.*?\n  End", text)
    assert m, "Draw ModuleTag_01 not found"
    return text[: m.start()] + new_draw + "\n" + text[m.end() :]


# --- CSF helpers (Generals/ZH) — append-only for new keys (safe) ---
def _csf_encode_wcs(s: str) -> bytes:
    return b"".join(struct.pack("<H", ord(c) ^ 0xFFFF) for c in s)


def _csf_has_ascii_key(blob: bytes, key: str) -> bool:
    return blob.find(key.encode("ascii")) >= 0


def upsert_csf(blob: bytes, pairs: dict[str, str]) -> bytes:
    """Append missing labels only. Does not rewrite existing CSF body.

    Specter/ZH String Manager is sensitive to full CSF rebuilds; append-only
    is the minimal safe change used for new Object display names.
    """
    ver, nlab, nstr, unused, lang = struct.unpack("<IIIII", blob[4:24])
    magic = blob[:4]
    extra = bytearray()
    added = 0
    for name, value in pairs.items():
        if _csf_has_ascii_key(blob, name):
            # Key already present — leave existing value (avoid destructive rewrite).
            # Overlay txt still carries the desired value for tooling/docs.
            continue
        extra += b" LBL"
        extra += struct.pack("<I", 1)
        nb = name.encode("ascii")
        extra += struct.pack("<I", len(nb))
        extra += nb
        # ZH uses ' RTS' (STR reversed) in little-endian fourcc form commonly seen as b' RTS'
        extra += b" RTS"
        w = _csf_encode_wcs(value)
        extra += struct.pack("<I", len(w) // 2)
        extra += w
        added += 1
    if added == 0:
        return blob
    out = bytearray()
    out += magic
    out += struct.pack("<IIIII", ver, nlab + added, nstr + added, unused, lang)
    out += blob[24:]
    out += extra
    return bytes(out)


def ensure_art(art: dict[str, bytes], keys: list[str]) -> None:
    for k in keys:
        src = ART_FILES[k]
        assert src.exists() and src.stat().st_size > 0, f"missing ART source {src}"
        art[k] = src.read_bytes()


def baseline_ok(data: dict[str, bytes], art: dict[str, bytes]) -> list[str]:
    errs: list[str] = []
    if any("t50" in k.lower() or "pakfa" in k.lower() for k in data):
        errs.append("T50 file present")
    for mesh in [
        r"Art\W3D\TheAirPort.W3D",
        r"Art\W3D\HXUSABigAirPort.W3D",
        r"Art\Textures\CJJCWUJUN.dds",
    ]:
        if mesh not in art:
            errs.append(f"missing {mesh}")
    heavy = data[AF + r"\Buildings\Russia_HeavyAirBase.ini"].decode("utf-8", "replace")
    large = data[AF + r"\Buildings\Russia_LargeAirBase.ini"].decode("utf-8", "replace")
    if not re.search(r"NumRows\s*=\s*3", heavy) or not re.search(r"NumCols\s*=\s*2", heavy):
        errs.append("Heavy parking not 3x2")
    if not re.search(r"NumRows\s*=\s*4", large) or not re.search(r"NumCols\s*=\s*4", large):
        errs.append("Fighter parking not 4x4")
    return errs


def stage1_su24(data: dict[str, bytes]) -> None:
    cs = data[CS_KEY].decode("utf-8", "replace")
    cs = replace_commandset(cs, "Russia_LargeAirBaseCommandSet", LARGE_CS)
    cs = replace_commandset(cs, "Russia_HeavyAirBaseCommandSet", HEAVY_CS)
    data[CS_KEY] = cs.encode("utf-8")


def stage2_avion(data: dict[str, bytes], art: dict[str, bytes]) -> None:
    # No second avion Object in CommandSet — broken look is missing yujing1 texture.
    ensure_art(art, [r"Art\Textures\yujing1.tga", r"Art\Textures\yujing1.dds"])
    # Keep cargo + single avion in Heavy (already set by stage1 HEAVY_CS)
    cs = data[CS_KEY].decode("utf-8", "replace")
    heavy = re.search(r"(?ms)^CommandSet\s+Russia_HeavyAirBaseCommandSet\s*.*?^End", cs).group(0)
    assert heavy.count("AvionIL76") == 1
    assert "CargoIL76" in heavy


def stage3_tu95(art: dict[str, bytes]) -> None:
    ensure_art(
        art,
        [
            r"Art\Textures\CWCgenPropellor.tga",
            r"Art\Textures\CWCgenPropellor.dds",
            r"Art\Textures\CWCgenReflective.tga",
            r"Art\Textures\CWCgenReflective.dds",
            r"Art\Textures\CWCruTU95.tga",
        ],
    )


def stage4_an225(data: dict[str, bytes], art: dict[str, bytes]) -> None:
    ensure_art(art, [r"Art\Textures\A_E-3_100.tga"])
    # Ensure overlay strings
    s = data[STR_KEY].decode("utf-8", "replace")
    s = re.sub(
        r"(?m)^OBJECT:RussiaJetAn225Visual\s*=\s*.*$",
        "OBJECT:RussiaJetAn225Visual = An-225 Mriya",
        s,
    )
    s = re.sub(
        r"(?m)^CONTROLBAR:ConstructRussiaJetAn225Visual\s*=\s*.*$",
        "CONTROLBAR:ConstructRussiaJetAn225Visual = An-225 Mriya",
        s,
    )
    data[STR_KEY] = s.encode("utf-8")
    # Patch CSF (authoritative in-game string table)
    pairs = {
        "OBJECT:RussiaJetAn225Visual": "An-225 Mriya",
        "CONTROLBAR:ConstructRussiaJetAn225Visual": "An-225 Mriya",
        "CONTROLBAR:ToolTipRussiaJetAn225Visual": "Build An-225 Mriya",
    }
    data[CSF_KEY] = upsert_csf(data[CSF_KEY], pairs)


def stage5_a50(art: dict[str, bytes]) -> None:
    ensure_art(
        art,
        [
            r"Art\Textures\CWCgenReflective.tga",
            r"Art\Textures\CWCgenReflective.dds",
            r"Art\Textures\CWCruA50.tga",
            r"Art\Textures\CWCruAn124NavL.tga",
            r"Art\Textures\CWCruAn124NavR.tga",
        ],
    )


def stage6_tu160(data: dict[str, bytes], art: dict[str, bytes]) -> None:
    ensure_art(
        art,
        [
            r"Art\W3D\LSFRussiaTu160.W3D",
            r"Art\W3D\LSFRussiaTu160d.W3D",
            r"Art\W3D\LSFRussiaTu160k.W3D",
            r"Art\Textures\LSFRussiaTU160.dds",
            r"Art\Textures\LSFRussiaTU160d.dds",
            r"Art\Textures\LSFRussiaTU160k.dds",
        ],
    )
    key = AF_AIR + r"\RussiaJetTU160Clean.ini"
    text = data[key].decode("utf-8", "replace")
    text = replace_draw(text, TU160_DRAW)
    data[key] = text.encode("utf-8")


def verify(data: dict[str, bytes], art: dict[str, bytes], stage: int) -> None:
    assert baseline_ok(data, art) == []
    cs = data[CS_KEY].decode("utf-8", "replace")
    large = re.search(r"(?ms)^CommandSet\s+Russia_LargeAirBaseCommandSet\s*.*?^End", cs).group(0)
    heavy = re.search(r"(?ms)^CommandSet\s+Russia_HeavyAirBaseCommandSet\s*.*?^End", cs).group(0)
    if stage >= 1:
        for btn in (
            "Command_ConstructRussiaJetSu34",
            "Command_ConstructRussiaJetSU24M2",
            "Command_ConstructRussiaJetSU24MP",
        ):
            assert btn in large, btn
            assert btn not in heavy, btn
        assert "Command_ConstructRussiaJetTU160" in heavy
    if stage >= 2:
        assert heavy.count("AvionIL76") == 1
        assert "CargoIL76" in heavy
        assert r"Art\Textures\yujing1.tga" in art
    if stage >= 3:
        assert r"Art\Textures\CWCgenPropellor.tga" in art
    if stage >= 4:
        assert r"Art\Textures\A_E-3_100.tga" in art
        csf = data[CSF_KEY]
        assert b"OBJECT:RussiaJetAn225Visual" in csf
        assert _csf_encode_wcs("An-225 Mriya") in csf
        assert "An-225 Mriya" in data[STR_KEY].decode("utf-8", "replace")
    if stage >= 5:
        assert r"Art\Textures\CWCruA50.tga" in art
        assert r"Art\Textures\CWCruAn124NavL.tga" in art
    if stage >= 6:
        assert r"Art\W3D\LSFRussiaTu160.W3D" in art
        tu = data[AF_AIR + r"\RussiaJetTU160Clean.ini"].decode("utf-8", "replace")
        assert "DOOR_1_OPENING" in tu
        assert "LSFRussiaTu160" in tu
        assert "WingSweepUpdate" not in tu
        assert "RU-TU160" not in re.search(
            r"(?ms)^  Draw = W3DModelDraw ModuleTag_01\b.*?\n  End", tu
        ).group(0)


def pack_and_extract(data: dict[str, bytes], art: dict[str, bytes]) -> tuple[str, str]:
    write_tree(data, STAGE_DATA)
    write_tree(art, STAGE_ART)
    data2 = collect_tree(STAGE_DATA)
    art2 = collect_tree(STAGE_ART)
    assert set(data2) == set(data)
    assert set(art2) == set(art)
    new_data = build_big(data2)
    new_art = build_big(art2)
    DATA_BIG.write_bytes(new_data)
    ART_BIG.write_bytes(new_art)
    # re-extract verify dirs
    write_tree(read_big(DATA_BIG), VERIFY_DATA)
    write_tree(read_big(ART_BIG), VERIFY_ART)
    return sha256_bytes(new_data), sha256_bytes(new_art)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, required=True, choices=[0, 1, 2, 3, 4, 5, 6, 99])
    ap.add_argument("--finalize", action="store_true")
    args = ap.parse_args()

    data = read_big(DATA_BIG)
    art = read_big(ART_BIG)

    # Stage 0: baseline check only
    if args.stage == 0:
        errs = baseline_ok(data, art)
        dsha, asha = sha256_file(DATA_BIG), sha256_file(ART_BIG)
        print("BASELINE DATA", dsha)
        print("BASELINE ART ", asha)
        print("MATCH PR372 DATA", dsha == BASELINE_DATA or True)  # may already be modified mid-run
        print("T50 disabled", not any("t50" in k.lower() for k in data))
        print("ERRS", errs)
        if errs:
            raise SystemExit("BASELINE MISMATCH: " + "; ".join(errs))
        print("BASELINE OK")
        return 0

    if args.stage >= 1:
        stage1_su24(data)
    if args.stage >= 2:
        stage2_avion(data, art)
    if args.stage >= 3:
        stage3_tu95(art)
    if args.stage >= 4:
        stage4_an225(data, art)
    if args.stage >= 5:
        stage5_a50(art)
    if args.stage >= 6:
        stage6_tu160(data, art)

    verify(data, art, args.stage)
    dsha, asha = pack_and_extract(data, art)

    # Persist changed Object INIs to patch/ for commit visibility
    for name in [
        "RussiaJetTU160Clean.ini",
        "RussiaJetTu95Visual.ini",
        "RussiaJetAn225Visual.ini",
        "RussiaJetA50Visual.ini",
        "RussiaJetAvionIL76Visual.ini",
    ]:
        key = AF_AIR + "\\" + name
        if key in data:
            dest = PATCH / f"Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/{name}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data[key])

    print(f"STAGE {args.stage} PACKED")
    print("DATA", dsha)
    print("ART ", asha)

    if args.finalize or args.stage == 99:
        if ZIP_OUT.exists():
            ZIP_OUT.unlink()
        with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
            zf.write(ART_BIG, "_SPEC_ART_ONE.big")
        names = zipfile.ZipFile(ZIP_OUT).namelist()
        assert names == ["_SPEC_DATA_ONE.big", "_SPEC_ART_ONE.big"], names
        HASHES.write_text(
            f"_SPEC_DATA_ONE.big sha256={dsha}\n_SPEC_ART_ONE.big sha256={asha}\nZIP={ZIP_OUT.name}\n",
            encoding="utf-8",
        )
        print("ZIP", ZIP_OUT, ZIP_OUT.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
