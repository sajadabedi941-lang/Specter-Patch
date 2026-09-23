#!/usr/bin/env python3
"""BUILDING_FLAG_STAGE_04_SAUDI_ARABIA_ONLY.

Baseline: BUILDING_FLAG_STAGE_03_VIETNAM_BARRACKS_ONLY.

Saudi Arabia is the first remaining target-country from the rollout list.
Same Japan/Vietnam method:
  - Original building Model=/Animation= untouched
  - One new country Flag_Hs W3D SA__SAFlag_Hs.W3D from Irq__IqFlag_Hs
    packed name == internal SA__SAFLAG_HS
    texture SA_Flag.tga (already packed)
  - Add Abbas-style ModuleTag_03 only on buildings that still show
    baked Iraqi FLAG01/02/03
  - Retarget SaudiArabia_Abbas existing Flag_Hs Draw (Iraqi pole) to
    the new Saudi W3D. Building mesh Irq_Hussien*_ stays unchanged.

Targets with baked Iraqi flags:
  SaudiArabia_Barracks     irq_camp
  SaudiArabia_PowerPlant   Iraq_Powerplant
  SaudiArabia_SupplyCenter Iraq_Supply
  SaudiArabia_WarFactory_T Irq_WarFactory

Existing incorrect Flag_Hs:
  SaudiArabia_Abbas        ModuleTag_03 Irq__IqFlag_Hs -> SA__SAFlag_Hs

Skipped (no baked *Flag.tga / no incorrect Flag_Hs):
  Radar Irq_P3, CommandCenter US_Command, airfields, MIC

Does not touch irq_camp, Iraq_Powerplant, Iraq_Supply, Irq_WarFactory,
IraqiFlag, DPRK_Flag, donor Flag_Hs, Japan/Vietnam poles,
PlayerTemplate, HUD, or pages.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/BUILDING_FLAG_STAGE_03_VIETNAM_BARRACKS_ONLY/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/BUILDING_FLAG_STAGE_03_VIETNAM_BARRACKS_ONLY/_SPEC_ART_ONE.big")
SRC_DATA_SHA = "1bfc0323e9be111fc4e54ce4861e9ada5755e41447fe29133f0086f78c7d79bd"
SRC_ART_SHA = "f9041fbd281126186c2dfc7873408dfd838f6672088893023827ba53afaac64b"

OUT_DIR = Path("/tmp/BUILDING_FLAG_STAGE_04_SAUDI_ARABIA_ONLY")
WS_OUT = Path("/workspace/patch/Release/BUILDING_FLAG_STAGE_04_SAUDI_ARABIA_ONLY")
RELEASE_NAME = "BUILDING_FLAG_STAGE_04_SAUDI_ARABIA_ONLY"

P_SA_BARRACKS = (
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_Barracks.ini"
)
P_SA_POWER = (
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_PowerPlant.ini"
)
P_SA_SUPPLY = (
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_SupplyCenter.ini"
)
P_SA_WF = (
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_WarFactory.ini"
)
P_SA_ABBAS = (
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_Abbas.ini"
)
P_SA_RADAR = (
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_RadarStation.ini"
)
P_SA_CC = (
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_CommandCenter.ini"
)
P_JP_BARRACKS = (
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_Barracks.ini"
)
P_VN_BARRACKS = (
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_Barracks.ini"
)
P_NEW_W3D = r"Art\W3D\SA__SAFlag_Hs.W3D"
P_JP_W3D = r"Art\W3D\JP__JPFlag_Hs.W3D"
P_VN_W3D = r"Art\W3D\VN__VNFlag_Hs.W3D"
P_DONOR_W3D = r"Art\W3D\Irq__IqFlag_Hs.W3D"
P_NK_W3D = r"Art\W3D\NKr__NKFlag_Hs.W3D"
P_IRQ_CAMP = r"Art\W3D\irq_camp.W3D"
P_IRQ_POWER = r"Art\W3D\Iraq_Powerplant.W3D"
P_IRQ_SUPPLY = r"Art\W3D\Iraq_Supply.W3D"
P_IRQ_WF = r"Art\W3D\Irq_WarFactory.W3D"
P_SA_TGA = r"Art\Textures\SA_Flag.tga"
P_VN_TGA = r"Art\Textures\VN_Flag.tga"
P_JP_TGA = r"Art\Textures\JP_Flag.tga"
P_IRQ_DDS = r"Art\Textures\IraqiFlag.dds"
P_DPRK_TGA = r"Art\Textures\DPRK_Flag.tga"
P_DPRK_DDS = r"Art\Textures\DPRK_Flag.dds"
P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_PAGES = r"Data\INI\MappedImages\HandCreated\Specter_FactionLogoPages.INI"
P_REMAIN = r"Data\INI\MappedImages\HandCreated\Specter_RemainingFlags.INI"
P_CAMP = r"Data\INI\MappedImages\HandCreated\Specter_CampFlags.INI"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_CMDSET = r"Data\INI\CommandSet.ini"

DONOR_NAME = b"IRQ__IQFLAG_HS"
NEW_NAME = b"SA__SAFLAG_HS"
DONOR_TEX = b"IraqiFlag.dds"
NEW_TEX = b"SA_Flag.tga"

ADD_TARGETS = (
    {
        "path": P_SA_BARRACKS,
        "object": "Object SaudiArabia_Barracks",
        "models": {"irq_camp"},
        "anims": {"irq_camp.irq_camp"},
        "allow_hidesub": False,
    },
    {
        "path": P_SA_POWER,
        "object": "Object SaudiArabia_PowerPlant",
        "models": {"Iraq_Powerplant"},
        "anims": {"Iraq_Powerplant.Iraq_Powerplant"},
        "allow_hidesub": False,
    },
    {
        "path": P_SA_SUPPLY,
        "object": "Object SaudiArabia_SupplyCenter",
        "models": {"Iraq_Supply"},
        "anims": {"Iraq_Supply.Iraq_Supply"},
        "allow_hidesub": False,
    },
    {
        "path": P_SA_WF,
        "object": "Object SaudiArabia_WarFactory_T",
        "models": {"Irq_WarFactory", "UBArmDeal_DNS"},
        "anims": {"Irq_WarFactory.Irq_WarFactory", "UBArmDeal_DNS.UBArmDeal_DNS"},
        "allow_hidesub": False,
    },
)


def add_bytes(entries: list[tuple[str, bytes]], name: str, blob: bytes) -> None:
    n = jf.norm(name)
    if any(jf.norm(x).lower() == n.lower() for x, _ in entries):
        raise SystemExit(f"already packed: {name}")
    entries.append((n, bytes(blob)))


def art_of(art: list[tuple[str, bytes]], target: str) -> bytes:
    return jf.raw_of(art, target)


def replace_w3d_names(donor: bytes, old: bytes, new: bytes) -> bytes:
    if len(new) > 15:
        raise SystemExit(f"internal name too long: {new!r}")
    if len(new) > len(old):
        raise SystemExit("new container name longer than donor")
    out = bytearray(donor)
    start = 0
    count = 0
    while True:
        i = out.find(old, start)
        if i < 0:
            break
        nul = out.find(b"\x00", i)
        if nul < 0:
            raise SystemExit(f"unterminated name at {i}")
        cur = bytes(out[i:nul])
        if not cur.startswith(old):
            start = i + 1
            continue
        field_len = 32 if b"." in cur else 16
        old_field = cur + b"\x00" * (field_len - len(cur))
        if bytes(out[i : i + field_len]) != old_field:
            raise SystemExit(
                f"unexpected name field at {i}: {bytes(out[i:i + field_len])!r}"
            )
        replacement = new + cur[len(old) :]
        if len(replacement) + 1 > field_len:
            raise SystemExit(f"renamed field too long: {replacement!r}")
        padded = replacement + b"\x00" * (field_len - len(replacement))
        out[i : i + field_len] = padded
        count += 1
        start = i + field_len
    if count != 19:
        raise SystemExit(f"expected 19 container name fields, got {count}")
    if old in bytes(out):
        raise SystemExit("leftover donor container name")
    if bytes(out).count(new) != 19:
        raise SystemExit(f"new container count {bytes(out).count(new)}")
    return bytes(out)


def replace_w3d_texture(blob: bytes, old: bytes, new: bytes) -> bytes:
    field_len = len(old) + 1
    new_field = new + b"\x00"
    if len(new_field) > field_len:
        raise SystemExit(f"texture name too long: {new!r}")
    new_field += b"\x00" * (field_len - len(new_field))
    out = bytearray(blob)
    count = 0
    start = 0
    while True:
        i = out.find(old, start)
        if i < 0:
            break
        if i + len(old) < len(out) and out[i + len(old)] == 0:
            out[i : i + field_len] = new_field
            count += 1
            start = i + field_len
        else:
            start = i + 1
    if count != 3:
        raise SystemExit(f"expected 3 texture refs, got {count}")
    if old in bytes(out):
        raise SystemExit("leftover donor texture name")
    if bytes(out).count(new) != 3:
        raise SystemExit(f"new texture count {bytes(out).count(new)}")
    return bytes(out)


def make_sa_flag_hs(donor: bytes) -> bytes:
    named = replace_w3d_names(donor, DONOR_NAME, NEW_NAME)
    out = replace_w3d_texture(named, DONOR_TEX, NEW_TEX)
    if len(out) != len(donor):
        raise SystemExit("W3D size changed")
    if DONOR_NAME in out or DONOR_TEX in out:
        raise SystemExit("donor strings remain in new W3D")
    if b"IRQ__IQFLAG_HS" in out or b"NKR__NKFLAG_HS" in out:
        raise SystemExit("Iraq/NK Flag_Hs container leaked into new W3D")
    if b"JP__JPFLAG_HS" in out or b"VN__VNFLAG_HS" in out:
        raise SystemExit("Japan/Vietnam Flag_Hs container leaked into new W3D")
    if b"IraqiFlag" in out or b"DPRK_Flag" in out or b"JP_Flag" in out or b"VN_Flag" in out:
        raise SystemExit("wrong texture leaked into new W3D")
    root = out[20:36]
    expect = NEW_NAME + b"\x00" * (16 - len(NEW_NAME))
    if root != expect:
        raise SystemExit(f"root container mismatch: {root!r}")
    return out


FLAG_DRAW = """  ; ------------ Flag -----------------
  Draw                = W3DModelDraw ModuleTag_03
    ConditionState    = None
      Model           = SA__SAFlag_Hs
      Animation       = SA__SAFlag_Hs.SA__SAFlag_Hs
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT
    AliasConditionState = SNOW
    AliasConditionState = NIGHT SNOW
    
    ConditionState    = DAMAGED
      Model           = SA__SAFlag_Hs
      Animation       = SA__SAFlag_Hs.SA__SAFlag_Hs
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT DAMAGED
    AliasConditionState = SNOW DAMAGED
    AliasConditionState = NIGHT SNOW DAMAGED
    
    ConditionState    = REALLYDAMAGED RUBBLE
      Model           = SA__SAFlag_Hs
      Animation       = SA__SAFlag_Hs.SA__SAFlag_Hs
      AnimationMode   = LOOP
    End
  End
"""


def has_exact_moduletag_03(text: str) -> bool:
    return re.search(r"(?m)\bModuleTag_03\b", text) is not None


def patch_add_flag_draw(
    text: str,
    *,
    object_line: str,
    allowed_models: set[str],
    allowed_anims: set[str],
    allow_hidesub: bool,
) -> str:
    if has_exact_moduletag_03(text):
        raise SystemExit(f"{object_line} already has ModuleTag_03")
    if (not allow_hidesub) and "HideSubObject" in text:
        raise SystemExit(f"{object_line} HideSubObject must not be added")
    if object_line not in text:
        raise SystemExit(f"missing {object_line}")
    nl = jf.file_nl(text)
    draw = jf.to_nl(FLAG_DRAW, nl)
    m = re.search(r"(?im)^[ \t]*PlacementViewAngle\s*=", text)
    if not m:
        raise SystemExit(f"{object_line} missing PlacementViewAngle insert point")
    prefix = text[: m.start()]
    new = prefix + draw + text[m.start() :]
    if not new.startswith(prefix):
        raise SystemExit(f"{object_line} building Draw prefix drifted")
    models = re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", prefix)
    anims = re.findall(r"(?im)^\s*Animation\s*=\s*(\S+)", prefix)
    if not models or any(val not in allowed_models for val in models):
        raise SystemExit(f"{object_line} Model retarget: {models}")
    if not anims or any(val not in allowed_anims for val in anims):
        raise SystemExit(f"{object_line} Animation retarget: {anims}")
    if len(re.findall(r"(?m)\bModuleTag_03\b", new)) != 1:
        raise SystemExit(f"{object_line} expected exactly one ModuleTag_03")
    if new.count("SA__SAFlag_Hs") != 9:
        raise SystemExit(f"{object_line} SA__SAFlag_Hs refs {new.count('SA__SAFlag_Hs')}")
    if len(re.findall(r"(?im)^\s*Model\s*=\s*SA__SAFlag_Hs\s*$", new)) != 3:
        raise SystemExit(f"{object_line} expected 3 ModuleTag_03 Model=SA__SAFlag_Hs")
    if len(re.findall(r"(?im)^\s*Animation\s*=\s*SA__SAFlag_Hs\.SA__SAFlag_Hs\s*$", new)) != 3:
        raise SystemExit(f"{object_line} expected 3 ModuleTag_03 Animation=SA__SAFlag_Hs")
    if (not allow_hidesub) and "HideSubObject" in new:
        raise SystemExit(f"{object_line} HideSubObject leaked")
    return new


def patch_abbas_flag_hs(text: str) -> str:
    if "Object SaudiArabia_Abbas" not in text:
        raise SystemExit("missing Object SaudiArabia_Abbas")
    if not has_exact_moduletag_03(text):
        raise SystemExit("SaudiArabia_Abbas missing ModuleTag_03")
    if text.count("Irq__IqFlag_Hs") != 9:
        raise SystemExit(f"Abbas Irq__IqFlag_Hs refs {text.count('Irq__IqFlag_Hs')}")
    if "SA__SAFlag_Hs" in text:
        raise SystemExit("Abbas already retargeted")
    new = text.replace("Irq__IqFlag_Hs", "SA__SAFlag_Hs")
    if "Irq__IqFlag_Hs" in new:
        raise SystemExit("Abbas leftover Irq__IqFlag_Hs")
    if new.count("SA__SAFlag_Hs") != 9:
        raise SystemExit(f"Abbas SA__SAFlag_Hs refs {new.count('SA__SAFlag_Hs')}")
    models = re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", new)
    anims = re.findall(r"(?im)^\s*Animation\s*=\s*(\S+)", new)
    allowed_models = {"Irq_Hussien", "Irq_Hussien_A1", "SA__SAFlag_Hs"}
    allowed_anims = {
        "Irq_Hussien_A1.Irq_Hussien_A1",
        "SA__SAFlag_Hs.SA__SAFlag_Hs",
    }
    if any(val not in allowed_models for val in models):
        raise SystemExit(f"Abbas Model retarget beyond Flag_Hs: {models}")
    if any(val not in allowed_anims for val in anims):
        raise SystemExit(f"Abbas Animation retarget beyond Flag_Hs: {anims}")
    if "Irq_Hussien_A1" not in models or "Irq_Hussien" not in models:
        raise SystemExit("Abbas building mesh Model= missing")
    if len(re.findall(r"(?im)^\s*Model\s*=\s*SA__SAFlag_Hs\s*$", new)) != 3:
        raise SystemExit("Abbas expected 3 Flag_Hs Model=SA__SAFlag_Hs")
    if len(re.findall(r"(?im)^\s*Animation\s*=\s*SA__SAFlag_Hs\.SA__SAFlag_Hs\s*$", new)) != 3:
        raise SystemExit("Abbas expected 3 Flag_Hs Animation=SA__SAFlag_Hs")
    return new


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def main() -> int:
    if jf.sha256_file(SRC_DATA) != SRC_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if jf.sha256_file(SRC_ART) != SRC_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    data = jf.read_big_list(SRC_DATA)
    art = jf.read_big_list(SRC_ART)
    src_data = list(data)
    src_art = list(art)

    donor = art_of(art, P_DONOR_W3D)
    if len(donor) != 20341:
        raise SystemExit("donor Flag_Hs size unexpected")
    if DONOR_NAME not in donor:
        raise SystemExit("donor container missing")

    sa_tga = art_of(art, P_SA_TGA)
    if len(sa_tga) < 18 or sa_tga[2] != 2:
        raise SystemExit("SA_Flag.tga is not uncompressed truecolor")

    new_w3d = make_sa_flag_hs(donor)
    add_bytes(art, P_NEW_W3D, new_w3d)

    for tgt in ADD_TARGETS:
        src = jf.text_of(data, tgt["path"])
        jf.set_text(
            data,
            tgt["path"],
            patch_add_flag_draw(
                src,
                object_line=tgt["object"],
                allowed_models=tgt["models"],
                allowed_anims=tgt["anims"],
                allow_hidesub=tgt["allow_hidesub"],
            ),
        )
    jf.set_text(data, P_SA_ABBAS, patch_abbas_flag_hs(jf.text_of(data, P_SA_ABBAS)))

    if len(art) != len(src_art) + 1:
        raise SystemExit(f"ART count {len(art)} != {len(src_art)}+1")
    if len(data) != len(src_data):
        raise SystemExit("DATA file count changed")

    src_art_map = {jf.norm(n).lower(): b for n, b in src_art}
    src_data_map = {jf.norm(n).lower(): b for n, b in src_data}
    new_art_map = {jf.norm(n).lower(): b for n, b in art}
    new_data_map = {jf.norm(n).lower(): b for n, b in data}

    if len(new_art_map) != len(art) or len(new_data_map) != len(data):
        raise SystemExit("duplicate packed path")

    added_art = [n for n in new_art_map if n not in src_art_map]
    if added_art != [jf.norm(P_NEW_W3D).lower()]:
        raise SystemExit(f"unexpected ART adds: {added_art}")
    for key, blob in src_art_map.items():
        if new_art_map[key] != blob:
            raise SystemExit(f"existing ART modified: {key}")
    for p in (
        P_DONOR_W3D, P_NK_W3D, P_JP_W3D, P_VN_W3D, P_IRQ_CAMP,
        P_IRQ_POWER, P_IRQ_SUPPLY, P_IRQ_WF, P_IRQ_DDS,
        P_DPRK_TGA, P_DPRK_DDS, P_SA_TGA, P_VN_TGA, P_JP_TGA,
    ):
        key = jf.norm(p).lower()
        if key not in src_art_map:
            continue
        if new_art_map[key] != src_art_map[key]:
            raise SystemExit(f"protected ART changed: {key}")

    expected_data = sorted(
        jf.norm(p).lower()
        for p in (P_SA_BARRACKS, P_SA_POWER, P_SA_SUPPLY, P_SA_WF, P_SA_ABBAS)
    )
    changed_data = sorted(n for n, b in new_data_map.items() if src_data_map.get(n) != b)
    if changed_data != expected_data:
        raise SystemExit(f"unexpected DATA changes: {changed_data}")
    for frozen in (
        P_PT, P_PT_PATCH, P_REMAIN, P_CAMP, P_JP_BARRACKS, P_VN_BARRACKS,
        P_SA_RADAR, P_SA_CC, P_CMDBTN, P_CMDSET,
    ):
        k = jf.norm(frozen).lower()
        if k in src_data_map and new_data_map[k] != src_data_map[k]:
            raise SystemExit(f"frozen DATA changed: {frozen}")
    if jf.norm(P_PAGES).lower() in new_data_map:
        raise SystemExit("faction pages INI must not appear")

    packed_w3d = art_of(art, P_NEW_W3D)
    if packed_w3d != new_w3d:
        raise SystemExit("packed W3D mismatch")
    w3d_names = [
        n for n, _ in art if jf.norm(n).lower().endswith("sa__saflag_hs.w3d")
    ]
    if len(w3d_names) != 1:
        raise SystemExit(f"duplicate SA Flag_Hs path: {w3d_names}")

    data_blob = jf.build_big_ordered(data)
    art_blob = jf.build_big_ordered(art)
    data_sha = sha256_bytes(data_blob)
    art_sha = sha256_bytes(art_blob)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_blob)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_blob)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(data_blob)
    (WS_OUT / "_SPEC_ART_ONE.big").write_bytes(art_blob)

    changed = "\n".join(
        [
            "BUILDING_FLAG_STAGE_04_SAUDI_ARABIA_ONLY changed files",
            "",
            "TARGET AUDIT",
            "  Country = Saudi Arabia only",
            "  Flag_Hs W3D = SA__SAFlag_Hs.W3D (one new file)",
            "  Texture = SA_Flag.tga (already packed, not rewritten)",
            "  Shared donor meshes not edited: irq_camp Iraq_Powerplant Iraq_Supply Irq_WarFactory",
            "",
            "DATA (5 files, Saudi Arabia Armed Forces Buildings only)",
            f"  {P_SA_BARRACKS}",
            "    Object SaudiArabia_Barracks",
            "    ModuleTag_01 UNCHANGED Model=irq_camp Animation=irq_camp.irq_camp",
            "    Added ModuleTag_03 Draw Model=SA__SAFlag_Hs",
            f"  {P_SA_POWER}",
            "    Object SaudiArabia_PowerPlant",
            "    ModuleTag_0231 UNCHANGED Model=Iraq_Powerplant",
            "    Added ModuleTag_03 Draw Model=SA__SAFlag_Hs",
            f"  {P_SA_SUPPLY}",
            "    Object SaudiArabia_SupplyCenter",
            "    ModuleTag_0741 UNCHANGED Model=Iraq_Supply",
            "    Added ModuleTag_03 Draw Model=SA__SAFlag_Hs",
            f"  {P_SA_WF}",
            "    Object SaudiArabia_WarFactory_T",
            "    ModuleTag_01 UNCHANGED Model=Irq_WarFactory",
            "    Added ModuleTag_03 Draw Model=SA__SAFlag_Hs",
            f"  {P_SA_ABBAS}",
            "    Object SaudiArabia_Abbas",
            "    ModuleTag_01 UNCHANGED Model=Irq_Hussien_A1 / Irq_Hussien",
            "    ModuleTag_03 Flag_Hs retarget Irq__IqFlag_Hs -> SA__SAFlag_Hs",
            "    HideSubObject on missiles UNCHANGED; no new HideSubObject",
            "",
            "SKIPPED (no baked donor flags / no incorrect Flag_Hs)",
            f"  {P_SA_RADAR} Model=Irq_P3",
            f"  {P_SA_CC} Model=US_Command",
            "",
            "ART (1 new file)",
            f"  {P_NEW_W3D}",
            "    donor=Art\\W3D\\Irq__IqFlag_Hs.W3D (bytes copied, donor file unmodified)",
            "    internal=SA__SAFLAG_HS  packed=SA__SAFlag_Hs  MATCH",
            "    texture=SA_Flag.tga (already packed)",
            "",
            "UNCHANGED",
            "  Japan_Barracks JP__JPFlag_Hs.W3D",
            "  Vietnam_Barracks VN__VNFlag_Hs.W3D",
            "  irq_camp.W3D Iraq_Powerplant.W3D Iraq_Supply.W3D Irq_WarFactory.W3D",
            "  IraqiFlag.dds Irq__IqFlag_Hs.W3D NKr__NKFlag_Hs.W3D",
            "  PlayerTemplate HUD MappedImages faction pages CommandButton CommandSet",
            "  every other country building Object INI",
        ]
    )
    audit = "\n".join(
        [
            "BUILDING_FLAG_STAGE_04_SAUDI_ARABIA_ONLY",
            "BASELINE = BUILDING_FLAG_STAGE_03_VIETNAM_BARRACKS_ONLY",
            f"SRC_DATA_SHA = {SRC_DATA_SHA}",
            f"SRC_ART_SHA = {SRC_ART_SHA}",
            f"DATA_SHA256 = {data_sha}",
            f"ART_SHA256 = {art_sha}",
            "COUNTRY = Saudi Arabia",
            "OBJECTS = SaudiArabia_Barracks SaudiArabia_PowerPlant SaudiArabia_SupplyCenter SaudiArabia_WarFactory_T SaudiArabia_Abbas",
            "BUILDING_MODEL_UNCHANGED = YES",
            "HIDESUBOBJECT_ADDED = NO",
            "NEW_W3D_COUNT = 1",
            "EXISTING_W3D_MODIFIED = NO",
            "IRAQ_NK_ASSETS_CHANGED = NO",
            "JAPAN_BARRACKS_CHANGED = NO",
            "VIETNAM_BARRACKS_CHANGED = NO",
            "RADAR_CC_CHANGED = NO",
            "UNRELATED_INI_CHANGED = NO",
            "DUPLICATE_W3D_PATH = NO",
            "PACKED_INTERNAL_MATCH = YES",
            "INTERNAL_NAME = SA__SAFLAG_HS",
            "INTERNAL_LEN = 12",
            "TEXTURE = SA_Flag.tga",
            "FIX_APPLIED = YES (Saudi Arabia Flag_Hs only)",
            "BOOT_SAFE = YES",
            "INGAME_TESTED = NO",
            "NEXT = wait for real ZH launch of Saudi Arabia buildings only",
        ]
    )
    changelog = """BUILDING_FLAG_STAGE_04_SAUDI_ARABIA_ONLY

First remaining target-country after the approved Japan and Vietnam
Barracks Flag_Hs poles.

Saudi barracks, power plant, supply center, and war factory still use
Iraqi donor meshes with baked FLAG01/FLAG02/FLAG03. This pair adds one
Saudi Flag_Hs pole (SA__SAFlag_Hs) as a second Draw on those four
objects. Building Model=/Animation= stay on irq_camp, Iraq_Powerplant,
Iraq_Supply, and Irq_WarFactory. Shared donor W3Ds are not edited.

SaudiArabia_Abbas already had an Abbas-style Flag_Hs Draw pointed at
Irq__IqFlag_Hs (Iraqi pole). That Draw is retargeted to SA__SAFlag_Hs.
The Abbas building mesh (Irq_Hussien / Irq_Hussien_A1) is unchanged.

Radar (Irq_P3) and Command Center (US_Command) have no baked donor
flags and are left untouched.

One new W3D: SA__SAFlag_Hs.W3D, authored from Irq__IqFlag_Hs with
internal container SA__SAFLAG_HS (matches packed name) and texture
SA_Flag.tga. Donor Iraq/NK/Japan/Vietnam Flag_Hs files are not modified.

Wait for a real ZH launch of Saudi Arabia buildings before the next country.
"""

    for dest in (OUT_DIR, WS_OUT):
        (dest / "CHANGED_FILES.txt").write_text(changed + "\n", encoding="utf-8")
        (dest / "audit.txt").write_text(audit + "\n", encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")

    sha_tmp = (
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {art_sha}\n"
    )
    (WS_OUT / "SHA256.txt").write_text(sha_tmp, encoding="utf-8")
    zip_path = WS_OUT / f"{RELEASE_NAME}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "SHA256.txt", "SHA256.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
    zip_sha = jf.sha256_file(zip_path)
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {art_sha}\n"
        f"{RELEASE_NAME}.zip  SHA256 {zip_sha}  {zip_path.stat().st_size} bytes\n"
    )
    (WS_OUT / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    (OUT_DIR / "SHA256.txt").write_text(sha_txt, encoding="utf-8")

    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", len(data_blob), data_sha)
    print("WROTE", WS_OUT / "_SPEC_ART_ONE.big", len(art_blob), art_sha)
    print("WROTE", zip_path, zip_path.stat().st_size, zip_sha)
    print(audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
