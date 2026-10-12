#!/usr/bin/env python3
"""Upgrade Vietnam missile factory from A-H to A-J on the SK / Japan / PR #629 path.

Baseline: packed SPECTER_SK_MISSILES_AJ (PR #631 + #630 + #629).

Preserve accepted Vietnam A-H identities, factory, VT72B construct chain,
PR #627 menu, PR #628 Fire, and PR #629 5-minute reload. Raise any A-H range
below 1000 km or mass below 400 kg. Add I Hung Vuong and J Lac Viet.

Do not rebuild the factory. Do not touch 9P117, Iraq A-M, Japan A-J, or SK A-J.
Live last-wins: CommandSet_VietnamMissiles.ini, CommandButton_VietnamMissiles.ini,
Weapon\\Weapon_Vietnam_Missiles.ini (sorted after Weapon.ini).
"""
from __future__ import annotations

import hashlib
import io
import math
import re
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_SK_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_SK_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_VIETNAM_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SK = "b8e4e37449844e9d075efaa05648dcc6ea12f9418a0f9a822158ff86d3917641"
SIZE_DATA_SK = 367155360
SHA_ART_SK = "9bab43586d69becf388ce2d2765829aed9bee9fdd6114c687135e4e1282fe1a4"
SIZE_ART_SK = 1439153220

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

VN_CB_KEY = r"Data\INI\CommandButton_VietnamMissiles.ini"
VN_CS_KEY = r"Data\INI\CommandSet_VietnamMissiles.ini"
VN_WEP_KEY = r"Data\INI\Weapon\Weapon_Vietnam_Missiles.ini"
VN_FAC_KEY = (
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces"
    r"\Buildings\Vietnam_MissileFactory.ini"
)
VN_VT72B_KEY = r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Tracked\Vietnam_VT72B.ini"

GRAY = (128, 128, 128)
CREAM = (220, 200, 155)
NOSE_W = (236, 228, 210)
NOSE_R = (168, 32, 28)

# Accepted A-H identities kept. Proposed table names documented in NAME_MAP.
# Floors applied: km>=1000, kg>=400. Compliant A-H mass/acc/cost/time kept.
MISSILES = [
    {
        "slot": "A", "object": "Vietnam_VCM01", "name": "VCM-01",
        "model": "Vnm_VCM01", "modeld": "Vnm_VCM01D", "proj_model": "Vnm_VCM01M",
        "hier": b"VNM_VCM01", "hierd": b"VNM_VCM01D", "proj_hier": b"VNM_MSL_A",
        "tex": "Vnm_VCM01P.tga", "body": (168, 32, 28), "nose": NOSE_W,
        "expect": "red", "km": 1000, "kg": 1000, "acc": 10, "stealth": 5,
        "rebuild": 15, "price": 800, "new": False, "floor_km": True, "floor_kg": False,
    },
    {
        "slot": "B", "object": "Vietnam_VCM02", "name": "VCM-02",
        "model": "Vnm_VCM02", "modeld": "Vnm_VCM02D", "proj_model": "Vnm_VCM02M",
        "hier": b"VNM_VCM02", "hierd": b"VNM_VCM02D", "proj_hier": b"VNM_MSL_B",
        "tex": "Vnm_VCM02P.tga", "body": (214, 178, 28), "nose": NOSE_R,
        "expect": "yellow", "km": 1000, "kg": 400, "acc": 75, "stealth": 15,
        "rebuild": 20, "price": 1200, "new": False, "floor_km": True, "floor_kg": True,
    },
    {
        "slot": "C", "object": "Vietnam_SongHong", "name": "Sông Hồng",
        "model": "Vnm_SongH", "modeld": "Vnm_SongHD", "proj_model": "Vnm_SongHM",
        "hier": b"VNM_SONGH", "hierd": b"VNM_SONGHD", "proj_hier": b"VNM_MSL_C",
        "tex": "Vnm_SongHP.tga", "body": (72, 112, 36), "nose": NOSE_R,
        "expect": "muddy", "km": 1000, "kg": 400, "acc": 25, "stealth": 80,
        "rebuild": 25, "price": 1600, "new": False, "floor_km": True, "floor_kg": False,
    },
    {
        "slot": "D", "object": "Vietnam_HongHa", "name": "Hồng Hà",
        "model": "Vnm_HongH", "modeld": "Vnm_HongHD", "proj_model": "Vnm_HongHM",
        "hier": b"VNM_HONGH", "hierd": b"VNM_HONGHD", "proj_hier": b"VNM_MSL_D",
        "tex": "Vnm_HongHP.tga", "body": (28, 68, 168), "nose": NOSE_W,
        "expect": "blue", "km": 1000, "kg": 1800, "acc": 15, "stealth": 10,
        "rebuild": 30, "price": 2000, "new": False, "floor_km": True, "floor_kg": False,
    },
    {
        "slot": "E", "object": "Vietnam_CuuLong", "name": "Cửu Long",
        "model": "Vnm_CuuLg", "modeld": "Vnm_CuuLgD", "proj_model": "Vnm_CuuLgM",
        "hier": b"VNM_CUULG", "hierd": b"VNM_CUULGD", "proj_hier": b"VNM_MSL_E",
        "tex": "Vnm_CuuLgP.tga", "body": (10, 72, 84), "nose": NOSE_W,
        "expect": "petrol", "km": 1000, "kg": 400, "acc": 55, "stealth": 45,
        "rebuild": 35, "price": 2500, "new": False, "floor_km": False, "floor_kg": True,
    },
    {
        "slot": "F", "object": "Vietnam_TruongSon", "name": "Trường Sơn",
        "model": "Vnm_TrSon", "modeld": "Vnm_TrSonD", "proj_model": "Vnm_TrSonM",
        "hier": b"VNM_TRSON", "hierd": b"VNM_TRSOND", "proj_hier": b"VNM_MSL_F",
        "tex": "Vnm_TrSonP.tga", "body": (22, 24, 26), "nose": NOSE_R,
        "expect": "black", "km": 1100, "kg": 600, "acc": 85, "stealth": 20,
        "rebuild": 40, "price": 3000, "new": False, "floor_km": False, "floor_kg": False,
    },
    {
        "slot": "G", "object": "Vietnam_BachDang", "name": "Bạch Đằng",
        "model": "Vnm_BachD", "modeld": "Vnm_BachDD", "proj_model": "Vnm_BachDM",
        "hier": b"VNM_BACHD", "hierd": b"VNM_BACHDD", "proj_hier": b"VNM_MSL_G",
        "tex": "Vnm_BachDP.tga", "body": (228, 224, 216), "nose": NOSE_R,
        "expect": "white", "km": 1300, "kg": 500, "acc": 30, "stealth": 90,
        "rebuild": 50, "price": 4000, "new": False, "floor_km": False, "floor_kg": False,
    },
    {
        "slot": "H", "object": "Vietnam_ThangLong", "name": "Thăng Long",
        "model": "Vnm_ThgLg", "modeld": "Vnm_ThgLgD", "proj_model": "Vnm_ThgLgM",
        "hier": b"VNM_THGLG", "hierd": b"VNM_THGLGD", "proj_hier": b"VNM_MSL_H",
        "tex": "Vnm_ThgLgP.tga", "body": (210, 108, 22), "nose": NOSE_W,
        "expect": "orange", "km": 1500, "kg": 1200, "acc": 60, "stealth": 55,
        "rebuild": 60, "price": 5000, "new": False, "floor_km": False, "floor_kg": False,
    },
    {
        "slot": "I", "object": "Vietnam_HungVuong", "name": "Hùng Vương",
        "model": "Vnm_HungV", "modeld": "Vnm_HungVD", "proj_model": "Vnm_HungVM",
        "hier": b"VNM_HUNGV", "hierd": b"VNM_HUNGVD", "proj_hier": b"VNM_MSL_I",
        "tex": "Vnm_HungVP.tga", "body": GRAY, "nose": NOSE_R,
        "expect": "gray", "km": 3400, "kg": 2500, "acc": 75, "stealth": 50,
        "rebuild": 78, "price": 8200, "new": True, "floor_km": False, "floor_kg": False,
    },
    {
        "slot": "J", "object": "Vietnam_LacViet", "name": "Lạc Việt",
        "model": "Vnm_LacVt", "modeld": "Vnm_LacVtD", "proj_model": "Vnm_LacVtM",
        "hier": b"VNM_LACVT", "hierd": b"VNM_LACVTD", "proj_hier": b"VNM_MSL_J",
        "tex": "Vnm_LacVtP.tga", "body": CREAM, "nose": NOSE_R,
        "expect": "cream", "km": 4000, "kg": 4000, "acc": 20, "stealth": 25,
        "rebuild": 95, "price": 10000, "new": True, "floor_km": False, "floor_kg": False,
    },
]

NAME_MAP = [
    "A VCM-01 kept (proposed table name Sông Hồng is already slot C)",
    "B VCM-02 kept (proposed table name Thăng Long is already slot H)",
    "C Sông Hồng kept (proposed table name Hạ Long unused)",
    "D Hồng Hà kept (proposed table name Tây Sơn unused)",
    "E Cửu Long kept (proposed table name Bạch Đằng is already slot G)",
    "F Trường Sơn kept (same as proposed)",
    "G Bạch Đằng kept (proposed table name Đông Sơn unused)",
    "H Thăng Long kept (proposed table name Cửu Long is already slot E)",
    "I Hùng Vương new (proposed default)",
    "J Lạc Việt new (proposed default)",
]

FROZEN_DATA = [
    sk.R11_KEY, sk.FACTORY_KEY, sk.BUILDING_KEY, sk.UNIT_A_KEY, sk.PROJ_A_KEY, sk.WEP_A_KEY,
    sk.JPN_FAC_KEY, sk.JPN_VT72B_KEY, sk.JPN_WEP_KEY, sk.SK_VT72B_KEY, sk.SK_WF_KEY,
    sk.NEW_FAC_KEY, VN_FAC_KEY, VN_VT72B_KEY, sk.PT_KEY, sk.NG_KEY,
]
FROZEN_ART = [
    sk.ORIG_W3D, sk.ORIGD_W3D, sk.R11_W3D, TEL_W3D, TELD_W3D, PROJ_W3D,
    r"Art\W3D\Irq_9P117R.W3D", sk.TRUCK_DDS, sk.TRUCKD_DDS,
    r"Art\Textures\Jpn_TEL.tga", r"Art\Textures\Skr_TEL.tga",
    r"Art\Textures\Skr_BaekhoP.tga", r"Art\W3D\Skr_Baekho.W3D",
    r"Art\Textures\Vnm_VCM01P.tga", r"Art\W3D\Vnm_VCM01.W3D",
    r"Art\Textures\specter_missile_a.tga", r"Art\Textures\specter_missile_j.tga",
    r"Art\Textures\Button_MissileFactory.tga", r"Art\Textures\Button_kashtan.tga",
    r"Art\Textures\Button_falaq.tga",
]

for _m in MISSILES:
    assert len(_m["hier"]) == 9 and len(_m["hierd"]) == 10 and len(_m["proj_hier"]) == 9
    assert 1000 <= _m["km"] <= 5000 and 400 <= _m["kg"] <= 10000


def derived(m: dict) -> dict:
    d = sk.derived({**m, "min_range": sk.MOTHER_MIN_RANGE})
    d["button"] = f"CB_VIETNAM_MISSILE_{m['slot']}"
    d["unit_key"] = (
        r"Data\INI\Object\Specter\Vietnam People's Armed Forces"
        rf"\Wheeled\{m['object']}.ini"
    )
    d["proj_key"] = (
        r"Data\INI\Object\Specter\Vietnam People's Armed Forces"
        rf"\{m['object']}_Projectile.ini"
    )
    d["new"] = m["new"]
    d["floor_km"] = m["floor_km"]
    d["floor_kg"] = m["floor_kg"]
    return d


DERIVED = [derived(m) for m in MISSILES]
NEW = [m for m in DERIVED if m["new"]]
EXISTING = [m for m in DERIVED if not m["new"]]


def make_vn_flag() -> Image.Image:
    w, h = 450, 300
    im = Image.new("RGBA", (w, h), (218, 37, 29, 255))
    draw = ImageDraw.Draw(im)
    cx, cy = w / 2, h / 2
    outer = h * 0.32
    inner = outer * 0.382
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = outer if i % 2 == 0 else inner
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(pts, fill=(255, 205, 0, 255))
    return im


def has_vn_flag(counts: dict[str, int]) -> bool:
    return counts.get("red", 0) >= 8 and (counts.get("yellow", 0) + counts.get("cream", 0)) >= 4


def unit_ini(m: dict) -> str:
    return (
        sk.unit_ini(m)
        .replace("South Korea", "Vietnam")
        .replace("Side = SouthKorea", "Side = Vietnam")
        .replace("Skr_TEL / Skr_TELD (not Irq_9P117 / Jpn_TEL)", "Irq_9P117 truck (accepted Vietnam TEL identity)")
    )


def projectile_ini(m: dict) -> str:
    return sk.projectile_ini(m).replace("South Korea", "Vietnam")


def weapon_pair(m: dict) -> str:
    return f"""
Weapon {m['weapon']}
  PrimaryDamage               = {sk.fmt_stat(m['damage'])}
  PrimaryDamageRadius         = 80.0
  SecondaryDamage             = {sk.fmt_stat(m['secondary'])}
  SecondaryDamageRadius       = 10.0
  ScatterRadius               = {sk.fmt_stat(m['scatter'])}
  ScatterRadiusVsInfantry     = {sk.fmt_stat(m['inf_scatter'])}
  AttackRange                 = {sk.fmt_stat(m['range'])}
  MinimumAttackRange          = {sk.fmt_stat(m['min_range'])}
  PreAttackDelay              = 500
  PreAttackType               = PER_SHOT
  DamageType                  = ARMOR_PIERCING
  DeathType                   = EXPLODED
  FireFX                      = FX_IskanderFiringEffects
  ProjectileObject            = {m['projectile']}
  ProjectileDetonationFX      = FX_SmallSRBM_Explosion
  RadiusDamageAffects         = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  FireSound                   = Iskander_Firing
  WeaponSpeed                 = 280
  AcceptableAimDelta          = 360
  DelayBetweenShots           = 3000
  ClipSize                    = 1
  AutoReloadsClip             = Yes
  ClipReloadTime              = 300000
  ShockWaveAmount             = 680.0
  ShockWaveRadius             = 150.0
  ShockWaveTaperOff           = 0.33
  AntiGround                  = Yes
End

Weapon {m['warhead']}
  PrimaryDamage           = {m['death']}
  PrimaryDamageRadius     = 20.0
  AttackRange             = 1
  DamageType              = HACK
  DeathType               = EXPLODED
  WeaponSpeed             = 9999999999
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  ClipSize                = 1
  ProjectileCollidesWith  = STRUCTURES
End
"""


def weapon_file(missiles: list[dict]) -> str:
    head = (
        "; Vietnam missiles A-J. Last-wins via Weapon\\Weapon_Vietnam_Missiles.ini.\n"
        "; 9P117 scale. A-H identities preserved. Floors: 1000 km / 400 kg.\n"
        "; ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000 (PR #629).\n"
        "; Death HACK is a separate path and is not folded into PrimaryDamage.\n"
    )
    return head + "".join(weapon_pair(m) for m in missiles)


def factory_commandset() -> str:
    slots = "\r\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(DERIVED, start=1))
    return (
        "CommandSet Vietnam_MissileFactoryCommandSet\r\n"
        f"{slots}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def vt72b_commandset() -> str:
    return (
        "CommandSet Vietnam_VT72BCommandSet\r\n"
        "  1  = Command_ConstructVietnam_PowerPlant\r\n"
        "  2  = Command_ConstructVietnam_CommandCenter\r\n"
        "  3  = Command_ConstructVietnam_SupplyCenter\r\n"
        "  4  = Command_ConstructVietnam_WarFactory\r\n"
        "  5  = Command_ConstructVietnam_LargeAirBase\r\n"
        "  6  = Command_ConstructVietnam_MissileFactory\r\n"
        "  7  = Command_ConstructVietnam_DefenseSite_SAFE\r\n"
        "  8  = Command_ConstructVietnam_RadarStation\r\n"
        "  9  = Command_ConstructVietnam_HeavyAirBase\r\n"
        "  10 = Command_ConstructVietnam_Barracks_SAFE\r\n"
        "  11 = Command_ConstructVietnam_NuclearCenter\r\n"
        "  12 = Command_ConstructVietnam_D30_SAFE\r\n"
        "  13 = Command_ConstructVietnam_CRAM\r\n"
        "  14 = Command_ConstructVietnam_Hq9_Site\r\n"
        "  15 = Command_Stop\r\n"
        "End"
    )


def commandbutton_all() -> str:
    lines = [
        "; Vietnam missiles A-J production buttons and factory construct button.",
        "; Shared specter_missile_* cameos. Unique Object bindings.",
        "",
        "CommandButton Command_ConstructVietnam_MissileFactory",
        "  Command          = DOZER_CONSTRUCT",
        "  Object           = Vietnam_MissileFactory",
        "  TextLabel        = CONTROLBAR:ConstructVietnamMissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel    = CONTROLBAR:ToolTipVietnamMissileFactory",
        "End",
        "",
    ]
    for m in DERIVED:
        lines.extend(
            [
                f"CommandButton {m['button']}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {m['object']}",
                f"  TextLabel     = CONTROLBAR:VietnamMissile{m['slot']}",
                f"  ButtonImage   = {m['cameo']}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTipVietnamMissile{m['slot']}",
                "End",
                "",
            ]
        )
    return "\n".join(lines)


def commandset_file() -> str:
    return vt72b_commandset() + "\r\n\r\n" + factory_commandset() + "\r\n"


def button_pair(m: dict) -> str:
    return (
        f"CommandButton {m['button']}\r\n"
        "  Command       = UNIT_BUILD\r\n"
        f"  Object        = {m['object']}\r\n"
        f"  TextLabel     = CONTROLBAR:VietnamMissile{m['slot']}\r\n"
        f"  ButtonImage   = {m['cameo']}\r\n"
        "  ButtonBorderType = BUILD\r\n"
        f"  DescriptLabel = CONTROLBAR:ToolTipVietnamMissile{m['slot']}\r\n"
        "End"
    )


def csf_map() -> dict[str, str]:
    mapping = {
        "OBJECT:VietnamMissileFactory": "Missile Factory",
        "CONTROLBAR:ConstructVietnamMissileFactory": "Missile Factory",
        "CONTROLBAR:ToolTipVietnamMissileFactory": (
            "Missile Factory\nProduces Vietnamese missiles A-J\nPrice: $1800"
        ),
    }
    for m in DERIVED:
        mapping[f"OBJECT:{m['object']}"] = m["name"]
        mapping[f"CONTROLBAR:VietnamMissile{m['slot']}"] = m["name"]
        mapping[f"CONTROLBAR:ToolTipVietnamMissile{m['slot']}"] = m["tooltip"]
    return mapping


def make_vn_tel_w3d(src: bytes, damaged: bool, m: dict) -> bytes:
    blob = sk.replace_textures(src, {"Irq_AlFahd500P.tga": m["tex"]})
    if damaged:
        blob = sk.uniquify(blob, [(b"IRQ_AF500D", m["hierd"])])
        blob = sk.patch_hlod_container(blob, m["modeld"])
    else:
        blob = sk.uniquify(blob, [(b"IRQ_AF500", m["hier"])])
        blob = sk.patch_hlod_container(blob, m["model"])
    return blob


def mapping_report() -> list[str]:
    lines = [
        "NAME MAPPING (accepted A-H identities retained):",
        *[f"  {row}" for row in NAME_MAP],
        "",
        "FLOOR CORRECTIONS (A-H):",
        "  A VCM-01 range 500 -> 1000 km (mass 1000 kg kept)",
        "  B VCM-02 range 700 -> 1000 km, mass 250 -> 400 kg",
        "  C Sông Hồng range 800 -> 1000 km (mass 400 kg kept)",
        "  D Hồng Hà range 900 -> 1000 km (mass 1800 kg kept)",
        "  E Cửu Long mass 350 -> 400 kg (range 1000 km kept)",
        "  F-H already at/above floors; accepted stats kept",
        "",
        "GAMEPLAY MAPPING (9P117 MOTHER scale):",
        "  AttackRange 1720 = 1000 km. Formula: 1720 * (km / 1000).",
        "  PrimaryDamage 2000 = 400 kg. Formula: 2000 * (kg / 400).",
        "  SecondaryDamage 100 = 400 kg splash. Formula: 100 * (kg / 400).",
        "  Death HACK 2200 = 400 kg extra. NOT folded into PrimaryDamage.",
        "  ScatterRadius 175 = 10/100 accuracy. Limitation: dispersion, not hit %.",
        "  Projectile MaxHealth 400 = 5/100 intercept proxy. No RadarPriority.",
        "  ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000.",
        "",
        "SLOT  NAME            KM   KG   ACC CHL TIME COST  RANGE  PD     SD    DEATH SCATTER  HP     MINR",
    ]
    for m in DERIVED:
        lines.append(
            f"  {m['slot']}    {m['name']:<14} {m['km']:<4} {m['kg']:<4} "
            f"{m['acc']:<3} {m['stealth']:<3} {m['rebuild']:<4} {m['price']:<5} "
            f"{sk.fmt_stat(m['range']):<6} {sk.fmt_stat(m['damage']):<6} {sk.fmt_stat(m['secondary']):<5} "
            f"{m['death']:<5} {sk.fmt_stat(m['scatter']):<7} {sk.fmt_stat(m['hp']):<6} "
            f"{sk.fmt_stat(m['min_range'])}"
        )
    return lines


def validate(data, art, src_data, src_art, order) -> list[str]:
    fails: list[str] = []
    for key in FROZEN_DATA:
        if data.get(key) != src_data.get(key):
            fails.append(f"frozen DATA mutated {key}")
    for key in FROZEN_ART:
        if key in src_art and art.get(key) != src_art.get(key):
            fails.append(f"frozen ART mutated {key}")

    cs_text = data[CS_KEY].decode("latin1")
    src_cs = src_data[CS_KEY].decode("latin1")
    cb_text = data[CB_KEY].decode("latin1")
    src_cb = src_data[CB_KEY].decode("latin1")
    wep_text = data[WEAPON_KEY].decode("latin1")
    src_wep = src_data[WEAPON_KEY].decode("latin1")

    if sk.last_block(cs_text, "CommandSet", "Vietnam_VT72BCommandSet") != sk.last_block(
        src_cs, "CommandSet", "Vietnam_VT72BCommandSet"
    ):
        fails.append("Vietnam VT72B CommandSet mutated")
    if "Command_ConstructVietnam_MissileFactory" not in sk.last_block(
        cs_text, "CommandSet", "Vietnam_VT72BCommandSet"
    ):
        fails.append("Vietnam VT72B lost factory construct")

    for name, label in (
        ("Japan_MissileFactoryCommandSet", "Japan factory"),
        ("SouthKorea_MissileFactoryCommandSet", "SK factory"),
        ("Iraq_AlFahdMissileFactoryCommandSet", "Iraq factory"),
        ("Iraq_AlFahdMissileFactoryBuildingCommandSet", "Iraq Sell-only"),
    ):
        if sk.last_block(cs_text, "CommandSet", name) != sk.last_block(src_cs, "CommandSet", name):
            fails.append(f"{label} CommandSet mutated")

    fac_cs = sk.last_block(cs_text, "CommandSet", "Vietnam_MissileFactoryCommandSet")
    slots = re.findall(r"CB_VIETNAM_MISSILE_([A-Z])", fac_cs)
    if slots != list("ABCDEFGHIJ"):
        fails.append(f"factory slots {slots} != A-J")
    if "Command_Sell" not in fac_cs or "Command_SetRallyPoint" not in fac_cs:
        fails.append("factory missing Rally/Sell")
    if "CB_JAPAN_" in fac_cs or "CB_SOUTHKOREA_" in fac_cs:
        fails.append("factory mixed foreign buttons")

    _k, lw_fac = sk.last_block_from_files(order, data, "CommandSet", "Vietnam_MissileFactoryCommandSet")
    if _k != VN_CS_KEY:
        fails.append(f"factory CommandSet last-wins {_k}")
    if re.findall(r"CB_VIETNAM_MISSILE_([A-Z])", lw_fac) != list("ABCDEFGHIJ"):
        fails.append("last-wins factory not A-J")

    _k, fac_obj = sk.last_block_from_files(order, data, "Object", "Vietnam_MissileFactory")
    if sk.field(fac_obj, "CommandSet") != "Vietnam_MissileFactoryCommandSet":
        fails.append("factory object CommandSet")
    if sk.field(fac_obj, "Side") != "Vietnam":
        fails.append("factory Side")

    if sk.last_block(cb_text, "CommandButton", "Command_ConstructVietnam_MissileFactory") == "":
        fails.append("CommandButton.ini missing Vietnam construct")
    if sk.last_block(cb_text, "CommandButton", "Command_ConstructSouthKorea_MissileFactory") != sk.last_block(
        src_cb, "CommandButton", "Command_ConstructSouthKorea_MissileFactory"
    ):
        fails.append("SK construct mutated")
    if sk.last_block(cb_text, "CommandButton", "Command_ConstructJapan_MissileFactory") != sk.last_block(
        src_cb, "CommandButton", "Command_ConstructJapan_MissileFactory"
    ):
        fails.append("Japan construct mutated")

    if sk.last_block(wep_text, "Weapon", "SRBM_ALHIJARAH_HE") != sk.last_block(src_wep, "Weapon", "SRBM_ALHIJARAH_HE"):
        fails.append("MOTHER weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Japan_Tenrai") != sk.last_block(src_wep, "Weapon", "Weapon_Japan_Tenrai"):
        fails.append("Japan Tenrai mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_SouthKorea_Baekho") != sk.last_block(
        src_wep, "Weapon", "Weapon_SouthKorea_Baekho"
    ):
        fails.append("SK Baekho mutated")
    if sk.illegal_floats(wep_text):
        fails.append(f"illegal floats {sk.illegal_floats(wep_text)}")

    csf = data[CSF_KEY]
    for m in DERIVED:
        unit = sk.last_block(data[m["unit_key"]].decode("latin1"), "Object", m["object"])
        if sk.field(unit, "BuildCost") != str(m["price"]):
            fails.append(f"{m['slot']} BuildCost")
        if not sk.field(unit, "BuildTime").startswith(f"{m['rebuild']}.0"):
            fails.append(f"{m['slot']} BuildTime")
        if sk.field(unit, "Side") != "Vietnam":
            fails.append(f"{m['slot']} Side")
        if sk.field(unit, "CommandSet") != "Scud_B_CommandSet":
            fails.append(f"{m['slot']} CommandSet")
        if m["weapon"] not in unit:
            fails.append(f"{m['slot']} weapon bind")
        if re.search(r"Weapon\s*=\s*SECONDARY", unit) or re.search(r"Weapon\s*=\s*TERTIARY", unit):
            fails.append(f"{m['slot']} extra weapon slot")
        if "Rearm" in unit or "RiderChangeContain" in unit:
            fails.append(f"{m['slot']} rearm")
        if "SouthKorea_" in unit or "Japan_" in unit:
            fails.append(f"{m['slot']} foreign object")

        proj = sk.last_block(data[m["proj_key"]].decode("latin1"), "Object", m["projectile"])
        if sk.field(proj, "MaxHealth") != sk.fmt_stat(m["hp"]):
            fails.append(f"{m['slot']} HP {sk.field(proj, 'MaxHealth')}")
        if sk.field(proj, "RadarPriority"):
            fails.append(f"{m['slot']} RadarPriority")

        ini_w = sk.last_block(wep_text, "Weapon", m["weapon"])
        _k, wblock = sk.last_block_from_files(order, data, "Weapon", m["weapon"])
        if _k != VN_WEP_KEY:
            fails.append(f"{m['slot']} weapon last-wins {_k}")
        if sk.field(wblock, "AttackRange") != sk.fmt_stat(m["range"]):
            fails.append(f"{m['slot']} range {sk.field(wblock, 'AttackRange')}")
        if sk.field(ini_w, "AttackRange") != sk.fmt_stat(m["range"]):
            fails.append(f"{m['slot']} Weapon.ini range")
        if sk.field(wblock, "PrimaryDamage") != sk.fmt_stat(m["damage"]):
            fails.append(f"{m['slot']} damage")
        if sk.field(wblock, "SecondaryDamage") != sk.fmt_stat(m["secondary"]):
            fails.append(f"{m['slot']} splash")
        if sk.field(wblock, "ClipSize") != "1" or sk.field(wblock, "AutoReloadsClip") != "Yes":
            fails.append(f"{m['slot']} clip")
        if sk.field(wblock, "ClipReloadTime") != "300000":
            fails.append(f"{m['slot']} reload")
        if float(sk.field(wblock, "AttackRange")) < sk.MOTHER_RANGE - 0.01:
            fails.append(f"{m['slot']} range below 1000 km")
        death = sk.last_block(wep_text, "Weapon", m["warhead"])
        if sk.field(death, "PrimaryDamage") != str(m["death"]):
            fails.append(f"{m['slot']} death")
        if sk.field(death, "DamageType") != "HACK":
            fails.append(f"{m['slot']} death type")

        bblock = sk.last_block(cb_text, "CommandButton", m["button"])
        if sk.field(bblock, "Object") != m["object"] or sk.field(bblock, "Command") != "UNIT_BUILD":
            fails.append(f"{m['slot']} button")
        if sk.field(bblock, "ButtonImage") != m["cameo"]:
            fails.append(f"{m['slot']} button image")
        if sk.csf_get(csf, f"CONTROLBAR:VietnamMissile{m['slot']}") != m["name"]:
            fails.append(f"{m['slot']} CSF name")

        tel = art[m["tel_key"]]
        if m["hier"] not in tel or m["tex"] not in sk.all_tex(tel):
            fails.append(f"{m['slot']} TEL identity")
        if m["new"]:
            texes = sk.all_tex(tel)
            if "Irq_9P117.tga" not in texes:
                fails.append(f"{m['slot']} TEL lost accepted truck")
            if "Skr_TEL.tga" in texes or "Jpn_TEL.tga" in texes:
                fails.append(f"{m['slot']} foreign truck")
        im = Image.open(io.BytesIO(art[m["tex_key"]])).convert("RGB")
        tel_flag = sk.region_mode(im, (110, 180, 420, 290))
        if not has_vn_flag(tel_flag):
            fails.append(f"{m['slot']} VN flag {tel_flag}")
        if not sk.has_name_plate(im, (500, 190, 960, 280)):
            fails.append(f"{m['slot']} TEL name")
        if m["new"]:
            body = sk.region_mode(im, (80, 410, 200, 560))
            top = max(body, key=body.get)
            allowed = {"gray": {"gray"}, "cream": {"cream", "white", "yellow"}}
            if top not in allowed[m["expect"]]:
                fails.append(f"{m['slot']} body {top} {body}")
    return fails


def write_loose() -> None:
    fac_dir = LOOSE / "Object/Specter/Vietnam People's Armed Forces/Buildings"
    wheel_dir = LOOSE / "Object/Specter/Vietnam People's Armed Forces/Wheeled"
    proj_dir = LOOSE / "Object/Specter/Vietnam People's Armed Forces"
    wep_dir = LOOSE / "Weapon"
    for d in (fac_dir, wheel_dir, proj_dir, wep_dir):
        d.mkdir(parents=True, exist_ok=True)
    (wep_dir / "Weapon_Vietnam_Missiles.ini").write_text(weapon_file(DERIVED), encoding="utf-8")
    (LOOSE / "CommandButton_VietnamMissiles.ini").write_text(commandbutton_all(), encoding="utf-8")
    (LOOSE / "CommandSet_VietnamMissiles.ini").write_text(commandset_file(), encoding="utf-8")
    for m in NEW:
        (wheel_dir / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (proj_dir / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_SK or SRC_DATA.stat().st_size != SIZE_DATA_SK:
        raise SystemExit("DATA baseline is not SPECTER_SK_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_SK or SRC_ART.stat().st_size != SIZE_ART_SK:
        raise SystemExit("ART baseline is not SPECTER_SK_MISSILES_AJ")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art = sk.parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    flag = make_vn_flag()

    for m in NEW:
        skin = sk.make_skin(m["body"], m["nose"], m["name"], flag)
        art[m["tex_key"]] = sk.make_tga32(skin)
        art[m["tel_key"]] = make_vn_tel_w3d(src_art[TEL_W3D], False, m)
        art[m["teld_key"]] = make_vn_tel_w3d(src_art[TELD_W3D], True, m)
        art[m["projw_key"]] = sk.make_proj_w3d(src_art[PROJ_W3D], m)
        data[m["unit_key"]] = sk.to_crlf(unit_ini(m))
        data[m["proj_key"]] = sk.to_crlf(projectile_ini(m))

    radar_line = re.compile(r"^[ \t]*RadarPriority[ \t]*=.*\r?\n", re.M)
    stealth_cmt = re.compile(r"^[ \t]*; SPECTER radar-stealth Kind.*\r?\n", re.M)
    for m in EXISTING:
        raw = data[m["proj_key"]].decode("latin1")
        if "RadarPriority" in raw:
            raw = radar_line.sub("", raw)
            raw = stealth_cmt.sub(
                "  ; Intercept challenge is projectile MaxHealth only. No RadarPriority.\r\n",
                raw,
            )
            data[m["proj_key"]] = raw.encode("latin1")

    data[VN_WEP_KEY] = sk.to_crlf(weapon_file(DERIVED))
    data[VN_CB_KEY] = sk.to_crlf(commandbutton_all())
    data[VN_CS_KEY] = sk.to_crlf(commandset_file())
    data[CSF_KEY] = sk.csf_upsert(src_data[CSF_KEY], csf_map())

    cs = src_data[CS_KEY].decode("latin1")
    old_fac = sk.last_block(cs, "CommandSet", "Vietnam_MissileFactoryCommandSet")
    if "CB_VIETNAM_MISSILE_H" not in old_fac or "CB_VIETNAM_MISSILE_I" in old_fac:
        raise SystemExit("unexpected CommandSet.ini Vietnam_MissileFactoryCommandSet")
    cs = sk.replace_last(cs, "CommandSet", "Vietnam_MissileFactoryCommandSet", factory_commandset())
    data[CS_KEY] = cs.encode("latin1")

    cb = src_data[CB_KEY].decode("latin1")
    extra = "\r\n\r\n".join(button_pair(m) for m in NEW)
    if "CommandButton CB_VIETNAM_MISSILE_I" in cb:
        raise SystemExit("CommandButton.ini already had Vietnam I")
    data[CB_KEY] = (cb.rstrip("\r\n") + "\r\n\r\n" + extra + "\r\n").encode("latin1")

    wep = src_data[WEAPON_KEY].decode("latin1")
    for m in EXISTING:
        pair = weapon_pair(m).strip() + "\n"
        fire, death = pair.split("\n\n", 1)
        wep = sk.replace_last(wep, "Weapon", m["weapon"], fire)
        wep = sk.replace_last(wep, "Weapon", m["warhead"], death)
    if "Weapon Weapon_Vietnam_HungVuong" in wep:
        raise SystemExit("Weapon.ini already had HungVuong")
    wep = wep.rstrip("\r\n") + "\r\n\r\n" + "".join(weapon_pair(m) for m in NEW).replace("\n", "\r\n")
    data[WEAPON_KEY] = wep.encode("latin1")

    write_loose()

    data_big = sk.build_big(data)
    art_big = sk.build_big(art)
    packed_data, order = sk.parse_big_ordered(data_big)
    packed_art = sk.parse_big(art_big)
    fails = validate(packed_data, packed_art, src_data, src_art, order)
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))
    fails.extend(f"ART {x}" for x in sk.big_structure_ok(art_big))
    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_big)
    art_path.write_bytes(art_big)

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "CommandSet.ini.Vietnam.txt").write_text(
        sk.last_block(packed_data[CS_KEY].decode("latin1"), "CommandSet", "Vietnam_VT72BCommandSet")
        + "\r\n\r\n"
        + sk.last_block(packed_data[CS_KEY].decode("latin1"), "CommandSet", "Vietnam_MissileFactoryCommandSet")
        + "\r\n",
        encoding="utf-8",
    )
    (ext / "Weapon.ini.Vietnam.txt").write_text(weapon_file(DERIVED), encoding="utf-8")
    for m in DERIVED:
        (ext / f"{m['object']}.ini").write_text(
            packed_data[m["unit_key"]].decode("latin1"), encoding="utf-8"
        )
        (ext / f"{m['object']}_Projectile.ini").write_text(
            packed_data[m["proj_key"]].decode("latin1"), encoding="utf-8"
        )
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    preview = OUT / "PREVIEW"
    preview.mkdir()
    flag.save(preview / "VietnamFlag.png")
    for m in DERIVED:
        Image.open(io.BytesIO(packed_art[m["tex_key"]])).save(preview / f"{m['slot']}_{m['object']}.png")
        Image.open(io.BytesIO(packed_art[m["tex_key"]])).crop((40, 150, 980, 320)).save(
            preview / f"{m['slot']}_dorsal_tel.png"
        )
        Image.open(io.BytesIO(packed_art[m["tex_key"]])).crop((40, 660, 980, 830)).save(
            preview / f"{m['slot']}_dorsal_proj.png"
        )

    data_sha = sk.sha256_path(data_path)
    art_sha = sk.sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_VIETNAM_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    inv = [
        "PRE-CHANGE VIETNAM (packed last-wins, SK A-J baseline):",
        "  Vietnam_VT72BCommandSet slot 6 = Command_ConstructVietnam_MissileFactory",
        "  Vietnam_MissileFactoryCommandSet = CB_VIETNAM_MISSILE_A-H + Rally/Sell",
        "  A-H objects/weapons present. I/J missing.",
        "  A/B/C/D ranges below 1000 km; B/E masses below 400 kg.",
        "",
        "POST-CHANGE VIETNAM:",
        "  Factory CommandSet = CB_VIETNAM_MISSILE_A-J + Rally/Sell",
        "  A-H identities kept. I Hùng Vương / J Lạc Việt added.",
        "  Floors applied. 5-minute reload retained.",
        "",
        *map_lines,
    ]
    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #631 s-sk-missiles-aj + PR #630 + PR #629",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "VIETNAM_AH_IDENTITIES_KEPT=YES",
        "VIETNAM_FACTORY_KEPT=YES",
        "JAPAN_AJ_UNCHANGED=YES",
        "SK_AJ_UNCHANGED=YES",
        "NINE_P117_UNCHANGED=YES",
        "IRAQ_FACTORY_UNCHANGED=YES",
        "NO_REARM=YES",
        "NO_RADARPRIORITY=YES",
        "ROSTER_COUNT=10",
        "KM_FLOOR=1000",
        "KG_FLOOR=400",
        "",
        *inv,
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    hashes = "\n".join(
        [
            "DATA_CHANGED=YES",
            "ART_CHANGED=YES",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_SIZE={art_path.stat().st_size}",
            f"ART_SHA256={art_sha}",
            "ZIP_FILE=SPECTER_VIETNAM_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #631",
            "STATIC_VALIDATION=PASS",
            "RUNTIME_TEST=NOT RUN",
            "",
        ]
    )
    (OUT / "HASHES.txt").write_text(hashes)
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-vietnam-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-vietnam-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-vietnam-missiles-aj/SPECTER_VIETNAM_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-vietnam-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-vietnam-missiles-aj",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Vietnam missiles upgraded from A-H to A-J on the accepted factory/fire path.\n"
        "A-H identities kept. Range/mass floors applied. I Hung Vuong and J Lac Viet added.\n"
        "Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Vietnam missiles A-J\n\n"
        "- Continues accepted Vietnam A-H (PR #627 menu, #628 Fire, #629 reload/damage).\n"
        "- Factory still constructed from Vietnam_VT72B slot 6. Rally/Sell retained.\n"
        "- Accepted A-H names kept. Proposed table names mapped in GAMEPLAY_MAPPING.txt.\n"
        "- Raised A/B/C/D ranges below 1000 km and B/E masses below 400 kg.\n"
        "- Added I Hùng Vương (gray, 3400 km / 2500 kg) and J Lạc Việt (cream, 4000 km / 4000 kg).\n"
        "- Vietnamese flag + exact names on I/J dorsal UV bands. A-H art frozen.\n"
        "- 5-minute clip reload on all ten PRIMARY weapons.\n"
        "- 9P117, Iraq A-M, Japan A-J, and South Korea A-J unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n", encoding="utf-8")
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_VietnamMissiles.ini last-wins Vietnam_MissileFactoryCommandSet A-J.\n"
        "CommandButton_VietnamMissiles.ini last-wins construct + A-J.\n"
        "Weapon\\Weapon_Vietnam_Missiles.ini last-wins Weapon_Vietnam_* (sorted after Weapon.ini).\n"
        "Weapon.ini also updated so live catalog matches.\n"
        "A-H unit/W3D/skin files are unchanged. Only I/J ART and objects are new.\n"
        "Japan, South Korea, Iraq, and 9P117 packed definitions are unchanged.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:70]))


if __name__ == "__main__":
    main()
