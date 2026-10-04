#!/usr/bin/env python3
"""Apply 3x Flag_Hs to Iraq and North Korea on all five standard buildings.

The previous PP_FLAG_SIZE_3X pack already enlarged 18 country Flag_Hs sets.
This pack keeps those meshes and attachments, and adds country-specific
3x clones for Iraq and North Korea so shared donors (Irq__IqFlag_Hs,
NKr__NKFlag_Hs) and building meshes stay untouched.

DATA is required: Iraq/NK buildings still use baked FLAG01-03 cloth.
North Korea's Camp button currently constructs Iraq_Barracks; a dedicated
NorthKorea_Barracks Object is added so NK no longer inherits the Iraqi flag.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import zipfile
from pathlib import Path

from pack_iran_building_flags import replace_w3d_names
from pack_pp_flag_size_3x import (
    build_big_ordered,
    extract_object,
    find_index,
    last_objects,
    mesh_bounds,
    object_spans,
    read_big,
    read_line01_pivot,
    replace_object,
    scale_flag_hs,
    sha256_file,
    should_scale,
)

SRC_DATA = Path("/workspace/patch/Release/PP_FLAG_SIZE_3X/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/PP_FLAG_SIZE_3X/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "90bbe149c0797336e53aca6188886e411b82e70057a03b8b57618ff272eba303"
EXPECTED_ART_SHA = "d5564372f4a450eb071a54b645c650acd85f8c6ef52baf3d4cc87f03013d6b70"
RELEASE = Path("/workspace/patch/Release/FLAG_SIZE_EVERYWHERE")
PAYLOAD = RELEASE / "payload"

P_IRQ_DONOR = r"Art\W3D\Irq__IqFlag_Hs.W3D"
P_NKR_DONOR = r"Art\W3D\NKr__NKFlag_Hs.W3D"
IRQ_NAME = b"IRQ__IQFLAG_HS"
NKR_NAME = b"NKR__NKFLAG_HS"

CLOTH_HIDE = "      HideSubObject = FLAG01 FLAG02 FLAG03 LINE01"
POWER_HIDE = "      HideSubObject = FLAG01 FLAG02 FLAG03 BOX08 BOX09 LINE01"
DRAW_RE = re.compile(r"(?i)^\s*Draw\s*=")
ANIM_LOOP_RE = re.compile(r"(?i)^\s*AnimationMode\s*=\s*LOOP\s*$")

# Player-facing Iraq/NK buildings. Camp for Iraq-family is Barracks (irq_camp).
TARGETS = [
    (r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_CommandCenter.ini", "Iraq_CommandCenter", "IQ__IQFlag_HsCU", CLOTH_HIDE),
    (r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory.ini", "Iraq_WarFactory_T", "IQ__IQFlag_HsWF", CLOTH_HIDE),
    (r"Data\INI\Object\Specter\Iraq Army\AI\Iraq_WarFactory.ini", "Iraq_WarFactory", "IQ__IQFlag_HsWF", CLOTH_HIDE),
    (r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory_AI.ini", "IraqMilitaryWarfactory", "IQ__IQFlag_HsWF", CLOTH_HIDE),
    (r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_Barracks.ini", "Iraq_Barracks", "IQ__IQFlag_HsCP", CLOTH_HIDE),
    (r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_PowerPlant.ini", "Iraq_PowerPlant", "IQ__IQFlag_HsPP", POWER_HIDE),
    (r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_SupplyCenter.ini", "Iraq_SupplyCenter", "IQ__IQFlag_HsSC", CLOTH_HIDE),
    (r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_CommandCenter.ini", "NorthKorea_CommandCenter", "NK__NKFlag_HsCU", CLOTH_HIDE),
    (r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_WarFactory.ini", "NorthKorea_WarFactory", "NK__NKFlag_HsWF", CLOTH_HIDE),
    (r"Data\INI\Object\Specter\North Korea\NorthKorea_Systems.ini", "NorthKorea_PowerPlant", "NK__NKFlag_HsPP", POWER_HIDE),
    (r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_SupplyCenter.ini", "NorthKorea_SupplyCenter", "NK__NKFlag_HsSC", CLOTH_HIDE),
]

NK_BARRACKS_PATH = r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_Barracks.ini"
NK_BUTTON_PATH = r"Data\INI\CommandButton_ZZZZ_NKBarracksFlag.ini"
NK_CAMP_FLAG = "NK__NKFlag_HsCP"

NEW_FLAGS = [
    ("IQ__IQFlag_HsCU", IRQ_NAME, P_IRQ_DONOR, b"IraqiFlag.dds"),
    ("IQ__IQFlag_HsWF", IRQ_NAME, P_IRQ_DONOR, b"IraqiFlag.dds"),
    ("IQ__IQFlag_HsCP", IRQ_NAME, P_IRQ_DONOR, b"IraqiFlag.dds"),
    ("IQ__IQFlag_HsPP", IRQ_NAME, P_IRQ_DONOR, b"IraqiFlag.dds"),
    ("IQ__IQFlag_HsSC", IRQ_NAME, P_IRQ_DONOR, b"IraqiFlag.dds"),
    ("NK__NKFlag_HsCU", NKR_NAME, P_NKR_DONOR, b"DPRK_Flag.dds"),
    ("NK__NKFlag_HsWF", NKR_NAME, P_NKR_DONOR, b"DPRK_Flag.dds"),
    ("NK__NKFlag_HsCP", NKR_NAME, P_NKR_DONOR, b"DPRK_Flag.dds"),
    ("NK__NKFlag_HsPP", NKR_NAME, P_NKR_DONOR, b"DPRK_Flag.dds"),
    ("NK__NKFlag_HsSC", NKR_NAME, P_NKR_DONOR, b"DPRK_Flag.dds"),
]

# last-win object + required Flag_Hs for the 5 required types
MATRIX = {
    "Vietnam": {
        "CommandCenter": ("Vietnam_CommandCenter", "VN__VNFlag_HsCK"),
        "WarFactory": ("Vietnam_WarFactory", "VN__VNFlag_HsWF"),
        "Camp": ("Vietnam_Barracks", "VN__VNFlag_Hs"),
        "PowerPlant": ("Vietnam_PowerPlant", "VN__VNFlag_HsPP"),
        "SupplyCenter": ("Vietnam_SupplyCenter", "VN__VNFlag_HsSC"),
    },
    "SouthKorea": {
        "CommandCenter": ("SouthKorea_CommandCenter", "SK__SKFlag_HsCK"),
        "WarFactory": ("SouthKorea_WarFactory", "SK__SKFlag_HsWF"),
        "Camp": ("SouthKorea_Barracks", "SK__SKFlag_Hs"),
        "PowerPlant": ("SouthKorea_PowerPlant", "SK__SKFlag_HsPP"),
        "SupplyCenter": ("SouthKorea_SupplyCenter", "SK__SKFlag_HsSC"),
    },
    "Japan": {
        "CommandCenter": ("Japan_CommandCenter", "JP__JPFlag_HsCK"),
        "WarFactory": ("Japan_WarFactory", "JP__JPFlag_HsWF"),
        "Camp": ("Japan_Barracks", "JP__JPFlag_Hs"),
        "PowerPlant": ("Japan_PowerPlant", "JP__JPFlag_HsPP"),
        "SupplyCenter": ("Japan_SupplyCenter", "JP__VNFlag_HsSC"),
    },
    "Turkey": {
        "CommandCenter": ("TurkeyCommandCenter", "TR__TRFlag_HsCU"),
        "WarFactory": ("TurkeyWarFactory", "TR__TRFlag_HsWF"),
        "Camp": ("TurkeyBootCamp", "TR__TRFlag_HsCP"),
        "PowerPlant": ("TurkeyPowerStation", "TR__TRFlag_HsPP"),
        "SupplyCenter": ("TurkeySupplyCenter", "TR__TRFlag_HsSC"),
    },
    "Italy": {
        "CommandCenter": ("ItalyCommandCenter", "IT__ITFlag_HsCU"),
        "WarFactory": ("ItalyWarFactory", "IT__ITFlag_HsWF"),
        "Camp": ("ItalyBootCamp", "IT__ITFlag_HsCP"),
        "PowerPlant": ("ItalyPowerStation", "IT__ITFlag_HsPP"),
        "SupplyCenter": ("ItalySupplyCenter", "IT__ITFlag_HsSC"),
    },
    "Sweden": {
        "CommandCenter": ("SwedenCommandCenter", "SE__SEFlag_HsCU"),
        "WarFactory": ("SwedenWarFactory", "SE__SEFlag_HsWF"),
        "Camp": ("SwedenBootCamp", "SE__SEFlag_HsCP"),
        "PowerPlant": ("SwedenPowerStation", "SE__SEFlag_HsPP"),
        "SupplyCenter": ("SwedenSupplyCenter", "SE__SEFlag_HsSC"),
    },
    "Britain": {
        "CommandCenter": ("BritainCommandCenter", "UK__UKFlag_HsCU"),
        "WarFactory": ("BritainWarFactory", "UK__UKFlag_HsWF"),
        "Camp": ("BritainBootCamp", "UK__UKFlag_HsCP"),
        "PowerPlant": ("BritainPowerStation", "UK__UKFlag_HsPP"),
        "SupplyCenter": ("BritainSupplyCenter", "UK__UKFlag_HsSC"),
    },
    "France": {
        "CommandCenter": ("FranceCommandCenter", "FR__FRFlag_HsCU"),
        "WarFactory": ("FranceWarFactory", "FR__FRFlag_HsWF"),
        "Camp": ("FranceBootCamp", "FR__FRFlag_HsCP"),
        "PowerPlant": ("FrancePowerStation", "FR__FRFlag_HsPP"),
        "SupplyCenter": ("FranceSupplyCenter", "FR__FRFlag_HsSC"),
    },
    "Germany": {
        "CommandCenter": ("GermanyCommandCenter", "DE__DEFlag_HsCU"),
        "WarFactory": ("GermanyWarFactory", "DE__DEFlag_HsWF"),
        "Camp": ("GermanyBootCamp", "DE__DEFlag_HsCP"),
        "PowerPlant": ("GermanyPowerStation", "DE__DEFlag_HsPP"),
        "SupplyCenter": ("GermanySupplyCenter", "DE__DEFlag_HsSC"),
    },
    "Ukraine": {
        "CommandCenter": ("UkraineCommandCenter", "UA__UAFlag_HsCU"),
        "WarFactory": ("UkraineWarFactory", "UA__UAFlag_HsWF"),
        "Camp": ("UkraineBootCamp", "UA__UAFlag_HsCP"),
        "PowerPlant": ("UkrainePowerStation", "UA__UAFlag_HsPP"),
        "SupplyCenter": ("UkraineSupplyCenter", "UA__UAFlag_HsSC"),
    },
    "SaudiArabia": {
        "CommandCenter": ("SaudiArabia_CommandCenter", "SA__SAFlag_HsCU"),
        "WarFactory": ("SaudiArabia_WarFactory_T", "SA__SAFlag_HsWF"),
        "Camp": ("SaudiArabia_Barracks", "SA__SAFlag_Hs"),
        "PowerPlant": ("SaudiArabia_PowerPlant", "SA__SAFlag_HsPP"),
        "SupplyCenter": ("SaudiArabia_SupplyCenter", "SA__SAFlag_HsSC"),
    },
    "UAE": {
        "CommandCenter": ("UAE_CommandCenter", "AE__AEFlag_HsCU"),
        "WarFactory": ("UAE_WarFactory_T", "AE__AEFlag_HsWF"),
        "Camp": ("UAE_Barracks", "AE__AEFlag_Hs"),
        "PowerPlant": ("UAE_PowerPlant", "AE__AEFlag_HsPP"),
        "SupplyCenter": ("UAE_SupplyCenter", "AE__AEFlag_HsSC"),
    },
    "Syria": {
        "CommandCenter": ("Syria_CommandCenter", "SY__SYFlag_HsCU"),
        "WarFactory": ("Syria_WarFactory_T", "SY__SYFlag_HsWF"),
        "Camp": ("Syria_Barracks", "SY__SYFlag_Hs"),
        "PowerPlant": ("Syria_PowerPlant", "SY__SYFlag_HsPP"),
        "SupplyCenter": ("Syria_SupplyCenter", "SY__SYFlag_HsSC"),
    },
    "India": {
        "CommandCenter": ("India_CommandCenter", "IN__INFlag_HsCU"),
        "WarFactory": ("India_WarFactory_T", "IN__INFlag_HsWF"),
        "Camp": ("India_Barracks", "IN__INFlag_Hs"),
        "PowerPlant": ("India_PowerPlant", "IN__INFlag_HsPP"),
        "SupplyCenter": ("India_SupplyCenter", "IN__INFlag_HsSC"),
    },
    "Pakistan": {
        "CommandCenter": ("Pakistan_CommandCenter", "PK__PKFlag_HsCU"),
        "WarFactory": ("Pakistan_WarFactory_T", "PK__PKFlag_HsWF"),
        "Camp": ("Pakistan_Barracks", "PK__PKFlag_Hs"),
        "PowerPlant": ("Pakistan_PowerPlant", "PK__PKFlag_HsPP"),
        "SupplyCenter": ("Pakistan_SupplyCenter", "PK__PKFlag_HsSC"),
    },
    "Libya": {
        "CommandCenter": ("Libya_CommandCenter", "LY__LYFlag_HsCU"),
        "WarFactory": ("Libya_WarFactory_T", "LY__LYFlag_HsWF"),
        "Camp": ("Libya_Barracks", "LY__LYFlag_Hs"),
        "PowerPlant": ("Libya_PowerPlant", "LY__LYFlag_HsPP"),
        "SupplyCenter": ("Libya_SupplyCenter", "LY__LYFlag_HsSC"),
    },
    "SouthAfrica": {
        "CommandCenter": ("SouthAfrica_CommandCenter", "ZA__ZAFlag_HsCU"),
        "WarFactory": ("SouthAfrica_WarFactory_T", "ZA__ZAFlag_HsWF"),
        "Camp": ("SouthAfrica_Barracks", "ZA__ZAFlag_Hs"),
        "PowerPlant": ("SouthAfrica_PowerPlant", "ZA__ZAFlag_HsPP"),
        "SupplyCenter": ("SouthAfrica_SupplyCenter", "ZA__ZAFlag_HsSC"),
    },
    "Iraq": {
        "CommandCenter": ("Iraq_CommandCenter", "IQ__IQFlag_HsCU"),
        "WarFactory": ("Iraq_WarFactory_T", "IQ__IQFlag_HsWF"),
        "Camp": ("Iraq_Barracks", "IQ__IQFlag_HsCP"),
        "PowerPlant": ("Iraq_PowerPlant", "IQ__IQFlag_HsPP"),
        "SupplyCenter": ("Iraq_SupplyCenter", "IQ__IQFlag_HsSC"),
    },
    "NorthKorea": {
        "CommandCenter": ("NorthKorea_CommandCenter", "NK__NKFlag_HsCU"),
        "WarFactory": ("NorthKorea_WarFactory", "NK__NKFlag_HsWF"),
        "Camp": ("NorthKorea_Barracks", "NK__NKFlag_HsCP"),
        "PowerPlant": ("NorthKorea_PowerPlant", "NK__NKFlag_HsPP"),
        "SupplyCenter": ("NorthKorea_SupplyCenter", "NK__NKFlag_HsSC"),
    },
}

# typo guard — Japan SC must be JP not VN
MATRIX["Japan"]["SupplyCenter"] = ("Japan_SupplyCenter", "JP__JPFlag_HsSC")

PRESERVE_OBJECTS = [
    "Japan_Barracks",
    "SouthKorea_Barracks",
    "Vietnam_Barracks",
    "IranCommandCenter",
    "IranBarracks",
    "IranWarFactory",
    "IranPowerplant",
    "IranSupplyCenter",
    "BritainBootCamp",
    "TurkeyBootCamp",
    "AmericaCommandCenter",
    "ChinaCommandCenter",
    "RussiaCommandCenter",
]

FROZEN_FILES = [
    r"Data\INI\CommandSet_ZZZZ_OilCapture_SoldierCommand.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\CommandSet_ZZZZ_CommandCenterMatchStart.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\Weapon.ini",
]

FROZEN_ART = [
    r"Art\W3D\Irq__IqFlag_Hs.W3D",
    r"Art\W3D\NKr__NKFlag_Hs.W3D",
    r"Art\W3D\NKor_Powerplant.W3D",
    r"Art\W3D\Iraq_Powerplant.W3D",
    r"Art\W3D\Irq_Command.W3D",
    r"Art\W3D\irq_camp.W3D",
    r"Art\Textures\DPRK_Flag.tga",
]


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def container_name(model: str) -> bytes:
    return model.upper().encode("ascii")


def hide_first_draw(body: str, hide_line: str) -> str:
    if hide_line.split("=", 1)[1].strip() in body and body.count("HideSubObject") >= 1:
        # still insert on any LOOP in first draw that lacks hide
        pass
    lines = body.splitlines(keepends=True)
    out = []
    in_first = False
    seen_draw = False
    inserted = 0
    for i, line in enumerate(lines):
        raw = line[:-1] if line.endswith("\n") else line
        if raw.endswith("\r"):
            raw = raw[:-1]
        if DRAW_RE.match(raw):
            if not seen_draw:
                in_first = True
                seen_draw = True
            else:
                in_first = False
        out.append(line)
        if in_first and ANIM_LOOP_RE.match(raw):
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if "HideSubObject" in nxt:
                continue
            nl = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
            out.append(hide_line + nl)
            inserted += 1
    if inserted < 1 and hide_line.split("=", 1)[1].strip() not in body:
        raise SystemExit("no HideSubObject inserts")
    return "".join(out)


def flag_draw(model: str, nl: str) -> str:
    block = f"""  ; ------------ Flag -----------------
  Draw                = W3DModelDraw ModuleTag_Flag_Hs
    ConditionState    = None
      Model           = {model}
      Animation       = {model}.{model}
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT
    AliasConditionState = SNOW
    AliasConditionState = NIGHT SNOW

    ConditionState    = DAMAGED
      Model           = {model}
      Animation       = {model}.{model}
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT DAMAGED
    AliasConditionState = SNOW DAMAGED
    AliasConditionState = NIGHT SNOW DAMAGED

    ConditionState    = REALLYDAMAGED RUBBLE
      Model           = {model}
      Animation       = {model}.{model}
      AnimationMode   = LOOP
    End
  End
"""
    return block.replace("\n", nl)


def insert_flag(body: str, model: str) -> str:
    if "ModuleTag_Flag_Hs" in body and model in body:
        return body
    nl = "\r\n" if "\r\n" in body else "\n"
    m = re.search(r"(?im)^[ \t]*PlacementViewAngle\s*=", body)
    if not m:
        raise SystemExit(f"missing PlacementViewAngle for {model}")
    return body[: m.start()] + flag_draw(model, nl) + body[m.start() :]


def patch_object(body: str, model: str, hide_line: str) -> str:
    body = hide_first_draw(body, hide_line)
    body = insert_flag(body, model)
    if model not in body:
        raise SystemExit(f"Flag_Hs missing after patch: {model}")
    if "ModuleTag_Flag_Hs" not in body:
        raise SystemExit("ModuleTag_Flag_Hs missing")
    return body


def clone_scaled_flag(donor: bytes, old_name: bytes, model: str, tex: bytes) -> bytes:
    new_name = container_name(model)
    blob = replace_w3d_names(donor, old_name, new_name)
    blob = scale_flag_hs(blob)
    if tex not in blob:
        raise SystemExit(f"{model} lost {tex}")
    if b"IraqiFlag" in blob and tex != b"IraqiFlag.dds":
        raise SystemExit(f"{model} leaked IraqiFlag")
    if b"DPRK_Flag" in blob and tex != b"DPRK_Flag.dds":
        raise SystemExit(f"{model} leaked DPRK")
    return blob


def make_nk_barracks(iraq_body: str) -> str:
    if not iraq_body.startswith("Object Iraq_Barracks"):
        raise SystemExit("Iraq_Barracks header unexpected")
    body = "Object NorthKorea_Barracks" + iraq_body[len("Object Iraq_Barracks") :]
    body = re.sub(r"(?im)^(\s*Side\s*=\s*)Iraq\s*$", r"\1NorthKorea", body, count=1)
    body = patch_object(body, NK_CAMP_FLAG, CLOTH_HIDE)
    return body


def make_nk_button() -> str:
    return (
        "CommandButton Command_ConstructNorthKorea_Barracks_SAFE\r\n"
        "  Command          = DOZER_CONSTRUCT\r\n"
        "  Object           = NorthKorea_Barracks\r\n"
        "  TextLabel        = CONTROLBAR:ConstructNorthKoreaBarracks\r\n"
        "  ButtonImage      = irq_barracks\r\n"
        "  ButtonBorderType = BUILD\r\n"
        "  DescriptLabel    = CONTROLBAR:ToolTipNorthKoreaBarracks\r\n"
        "End\r\n"
    )


def write_payload(repl: dict[str, bytes]) -> None:
    if PAYLOAD.exists():
        for p in PAYLOAD.rglob("*"):
            if p.is_file():
                p.unlink()
    for name, blob in repl.items():
        dest = PAYLOAD / name.replace("\\", "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)


def validate(orig_art, orig_data, new_art, new_data) -> None:
    orig_last, _ = last_objects(orig_data)
    new_last, new_src = last_objects(new_data)
    art_m = {norm(n): b for n, b in new_art}
    orig_art_m = {norm(n): b for n, b in orig_art}

    for obj in PRESERVE_OBJECTS:
        if obj in orig_last and new_last.get(obj) != orig_last[obj]:
            raise SystemExit(f"preserved object changed: {obj}")

    orig_d = {norm(n): b for n, b in orig_data}
    new_d = {norm(n): b for n, b in new_data}
    for packed in FROZEN_FILES:
        if orig_d[norm(packed)] != new_d[norm(packed)]:
            raise SystemExit(f"frozen DATA file changed: {packed}")

    for packed in FROZEN_ART:
        if orig_art_m[norm(packed)] != art_m[norm(packed)]:
            raise SystemExit(f"frozen ART changed: {packed}")

    # Japan/SK/VN PP must stay free of NK baked flags
    for obj, flag in (
        ("Japan_PowerPlant", "JP__JPFlag_HsPP"),
        ("SouthKorea_PowerPlant", "SK__SKFlag_HsPP"),
        ("Vietnam_PowerPlant", "VN__VNFlag_HsPP"),
    ):
        body = new_last[obj]
        if "NKor_Powerplant" in body or "DPRK_Flag" in body or "NKr__NKFlag" in body:
            raise SystemExit(f"{obj} regained NK flag")
        if flag not in body:
            raise SystemExit(f"{obj} lost {flag}")

    missing = []
    for country, kinds in MATRIX.items():
        for kind, (obj, flag) in kinds.items():
            if obj not in new_last:
                missing.append(f"{country} {kind} object {obj}")
                continue
            body = new_last[obj]
            if flag not in body:
                missing.append(f"{country} {kind} {obj} missing {flag}")
                continue
            if country == "NorthKorea" and ("IraqiFlag" in body or "IQ__IQFlag" in body):
                missing.append(f"{country} {kind} inherited Iraq flag")
            if country in ("Japan", "SouthKorea", "Vietnam") and (
                "NKor_Powerplant" in body or "NKr__NKFlag" in body
            ):
                missing.append(f"{country} {kind} inherited NK flag")
            w3d = f"art\\w3d\\{flag.lower()}.w3d"
            if w3d not in art_m:
                missing.append(f"missing W3D {flag}")
                continue
            bd = mesh_bounds(art_m[w3d])
            fh = bd["FLAG03"]["ymax"] - bd["FLAG03"]["ymin"]
            if abs(fh - 17.578) > 0.08:
                missing.append(f"{flag} FLAG03 height {fh:.3f} not 3x")
    if missing:
        raise SystemExit("MATRIX FAIL\n  " + "\n  ".join(missing))

    # NK construct button last-win
    btn_text = new_d[norm(NK_BUTTON_PATH)].decode("latin1")
    if "Object           = NorthKorea_Barracks" not in btn_text:
        raise SystemExit("NK barracks button overlay missing Object")

    # donors unscaled
    for donor in (P_IRQ_DONOR, P_NKR_DONOR):
        bd = mesh_bounds(art_m[norm(donor)])
        fh = bd["FLAG03"]["ymax"] - bd["FLAG03"]["ymin"]
        if abs(fh - 5.859) > 0.08:
            raise SystemExit(f"shared donor {donor} was scaled ({fh})")

    print("STATIC VALIDATION: PASS")
    print(f"  matrix {len(MATRIX)} countries x 5 buildings")
    print("  Iraq/NK Flag_Hs clones 3x; shared donors unchanged")
    print("  NorthKorea_Barracks last-win + construct overlay")
    print("  JP/SK/VN Power Plants remain country Flag_HsPP")


def write_docs(data_sha: str, art_sha: str) -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)
    (RELEASE / "AUDIT.txt").write_text(
        "FLAG_SIZE_EVERYWHERE\n"
        f"SOURCE_DATA_SHA = {EXPECTED_DATA_SHA}\n"
        f"SOURCE_ART_SHA = {EXPECTED_ART_SHA}\n"
        "PRIOR = PP_FLAG_SIZE_3X already 3x for 18 country Flag_Hs sets.\n"
        "GAP = Iraq/NK still used baked FLAG01-03 on building meshes; "
        "NK Camp button constructed Iraq_Barracks.\n"
        "FIX = country-specific 3x Flag_Hs clones + hide baked cloth; "
        "NorthKorea_Barracks Object + CommandButton overlay.\n"
        "SKIP_SHARED = Irq__IqFlag_Hs NKr__NKFlag_Hs building W3Ds\n"
        "CAMP = BootCamp for EU; Barracks (irq_camp) for Iraq-family; "
        "NorthKorea_Barracks for NK.\n"
        "INGAME_TESTED = NO\n",
        encoding="utf-8",
    )
    (RELEASE / "CHANGELOG.txt").write_text(
        "FLAG_SIZE_EVERYWHERE\n\n"
        "3x national Flag_Hs now covers Vietnam, South Korea, Japan, Turkey,\n"
        "Italy, Sweden, Britain, France, Germany, Ukraine, Saudi Arabia, UAE,\n"
        "Syria, India, Pakistan, Libya, South Africa, Iraq, and North Korea\n"
        "on Command Center, War Factory, Camp/Barracks, Power Plant, and\n"
        "Supply Center. Iran's already-correct 3x flags are preserved.\n"
        "Iraq and North Korea no longer rely on small baked building flags.\n"
        "Shared Irq__IqFlag_Hs / NKr__NKFlag_Hs donors are unchanged.\n"
        "In-game test: NOT PERFORMED.\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", action="store_true")
    args = ap.parse_args()
    if sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    art_work = list(read_big(SRC_ART))
    data_work = list(read_big(SRC_DATA))
    orig_art = list(art_work)
    orig_data = list(data_work)
    repl: dict[str, bytes] = {}

    # ART clones
    for model, old_name, donor_path, tex in NEW_FLAGS:
        donor = art_work[find_index(art_work, donor_path)][1]
        blob = clone_scaled_flag(donor, old_name, model, tex)
        packed = rf"Art\W3D\{model}.W3D"
        art_work.append((packed, blob))
        repl[packed] = blob
        print("ART", packed, len(blob))

    # DATA patches
    by_file: dict[str, list] = {}
    for packed, obj, model, hide in TARGETS:
        by_file.setdefault(packed, []).append((obj, model, hide))

    for packed, jobs in by_file.items():
        idx = find_index(data_work, packed)
        text = data_work[idx][1].decode("latin1", errors="replace")
        names = [n for n, _, _ in object_spans(text)]
        rebuilt = []
        cursor = 0
        for obj, start, end in object_spans(text):
            rebuilt.append(text[cursor:start])
            body = text[start:end]
            job = next((j for j in jobs if j[0] == obj), None)
            if job:
                body = patch_object(body, job[1], job[2])
            rebuilt.append(body)
            cursor = end
        rebuilt.append(text[cursor:])
        new_text = "".join(rebuilt)
        new_names = [n for n, _, _ in object_spans(new_text)]
        if new_names != names:
            raise SystemExit(f"object list drifted: {packed}")
        blob = new_text.encode("latin1", errors="replace")
        data_work[idx] = (data_work[idx][0], blob)
        repl[data_work[idx][0]] = blob
        print("DATA", packed, [j[0] for j in jobs])

    iraq_barracks = extract_object(
        orig_data[find_index(orig_data, r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_Barracks.ini")][1].decode(
            "latin1", errors="replace"
        ),
        "Iraq_Barracks",
    )
    nk_body = make_nk_barracks(iraq_barracks)
    data_work.append((NK_BARRACKS_PATH, nk_body.encode("latin1", errors="replace")))
    repl[NK_BARRACKS_PATH] = data_work[-1][1]
    print("DATA NEW", NK_BARRACKS_PATH)

    btn = make_nk_button().encode("latin1")
    data_work.append((NK_BUTTON_PATH, btn))
    repl[NK_BUTTON_PATH] = btn
    print("DATA NEW", NK_BUTTON_PATH)

    write_payload(repl)
    validate(orig_art, orig_data, art_work, data_work)
    write_docs("", "")

    if args.pack:
        data_out = RELEASE / "_SPEC_DATA_ONE.big"
        art_out = RELEASE / "_SPEC_ART_ONE.big"
        data_out.write_bytes(build_big_ordered(data_work))
        art_out.write_bytes(build_big_ordered(art_work))
        dsha = sha256_file(data_out)
        asha = sha256_file(art_out)
        print("PACKED", data_out, dsha, data_out.stat().st_size)
        print("PACKED", art_out, asha, art_out.stat().st_size)
        write_docs(dsha, asha)
        (RELEASE / "SHA256.txt").write_text(
            f"_SPEC_DATA_ONE.big {dsha}\n_SPEC_ART_ONE.big  {asha}\n",
            encoding="utf-8",
        )

        packed_d = {norm(n): b for n, b in read_big(data_out)}
        src_d = {norm(n): b for n, b in orig_data}
        extra_d = set(packed_d) - set(src_d)
        if extra_d != {norm(NK_BARRACKS_PATH), norm(NK_BUTTON_PATH)}:
            raise SystemExit(f"unexpected DATA extras {extra_d}")
        packed_a = {norm(n): b for n, b in read_big(art_out)}
        src_a = {norm(n): b for n, b in orig_art}
        extra_a = set(packed_a) - set(src_a)
        expect_a = {norm(rf"Art\W3D\{m}.W3D") for m, *_ in NEW_FLAGS}
        if extra_a != expect_a:
            raise SystemExit(f"unexpected ART extras {extra_a}")
        for k in src_a:
            if k in {norm(p) for p, *_ in []} :
                pass
        print(f"POST-PACK SCOPE: PASS ({len(packed_d)-len(src_d)} new DATA, {len(extra_a)} new ART)")

        zpath = RELEASE / "FLAG_SIZE_EVERYWHERE.zip"
        with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_STORED) as zf:
            zf.write(data_out, "_SPEC_DATA_ONE.big")
            zf.write(art_out, "_SPEC_ART_ONE.big")
            zf.write(RELEASE / "SHA256.txt", "SHA256.txt")
            zf.write(RELEASE / "CHANGELOG.txt", "CHANGELOG.txt")
        print("ZIP", zpath, sha256_file(zpath), zpath.stat().st_size)
    else:
        print("Payload written; BIGs not packed (pass --pack after validation).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
