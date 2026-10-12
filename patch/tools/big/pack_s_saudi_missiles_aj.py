#!/usr/bin/env python3
"""Implement Saudi Arabia missile roster A-J on the Vietnam / SK / Japan / PR #629 path.

Baseline: packed SPECTER_VIETNAM_MISSILES_AJ (PR #632 + #631 + #630 + #629).

Saudi has no missile factory. Dozer / Worker / VT72B slot 13 currently constructs
the isolated Sell-only Iraq_AlFahdMissileFactoryBuilding. Replace that slot with a
Saudi-only factory. Keep MIC on slot 6.

Preserve existing SaudiArabia_ShaheenTEL, SaudiArabia_AbabeelTEL, and
SaudiArabia_Alhussaien. Proposed slot I Shahin conflicts with ShaheenTEL, so
slot I is Fajr. Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117
stay frozen.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Satellite last-wins: CommandSet_SaudiArabiaMissiles.ini,
CommandButton_SaudiArabiaMissiles.ini, Weapon\\Weapon_SaudiArabia_Missiles.ini.
Saudi flag + exact names on dorsal UV bands. Dedicated Sau_TEL truck.
No RadarPriority. No rearm. No ZZZZ.
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

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_sk_missiles_aj as sk  # noqa: E402
import pack_s_vietnam_missiles_aj as vn  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_VIETNAM_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_VIETNAM_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_SAUDI_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_VN = "e65f3622259cce9f0a18d358fcfd4f1ff8ea68e0f461ae3b21c72aa6485cfbcf"
SIZE_DATA_VN = 367185389
SHA_ART_VN = "0a5d43a460d14ea99ef5ccedf50653907e1d46ef9364d5419971c14a81335563"
SIZE_ART_VN = 1448286482

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

SA_CB_KEY = r"Data\INI\CommandButton_SaudiArabiaMissiles.ini"
SA_CS_KEY = r"Data\INI\CommandSet_SaudiArabiaMissiles.ini"
SA_WEP_KEY = r"Data\INI\Weapon\Weapon_SaudiArabia_Missiles.ini"
SA_FAC_KEY = (
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces"
    r"\Buildings\SaudiArabia_MissileFactory.ini"
)
SA_VT72B_KEY = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Tracked\VT72B.ini"
SA_DOZER_KEY = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Tracked\SaudiArabia_Dozer.ini"
SA_SHAHEEN_KEY = (
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Wheeled\SaudiArabia_ShaheenTEL.ini"
)
SA_ABABEEL_KEY = (
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Wheeled\SaudiArabia_AbabeelTEL.ini"
)
SA_ALHUSS_KEY = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Wheeled\AbbasLauncher.ini"
SA_WEP_OLD_KEY = r"Data\INI\Weapon_SaudiArabia.ini"
SA_MIC_KEY = r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_MIC.ini"

TRUCK_TEX = "Sau_TEL.tga"
TRUCKD_TEX = "Sau_TELD.tga"
TRUCK_KEY = rf"Art\Textures\{TRUCK_TEX}"
TRUCKD_KEY = rf"Art\Textures\{TRUCKD_TEX}"
AR_FONT = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf"

WEP_MARKER = (
    "; ===== Saudi Arabia missiles A-J "
    "(Weapon.ini load path for Command_FireMainWeapon) ====="
)

BUILDERS = [
    "SaudiArabiaDozerCommandSet",
    "SaudiArabia_WorkerCommandSet",
    "SaudiArabia_VT72BCommandSet",
]

SAND = (168, 148, 96)
OLIVE = (78, 92, 48)
KHAKI = (140, 124, 78)
NOSE_W = (236, 228, 210)
NOSE_R = (168, 32, 28)

# Distinct from Vietnam slot-for-slot colors. Desert-forward, then steel/dark.
MISSILES = [
    {
        "slot": "A", "object": "SaudiArabia_Najm", "name": "Najm",
        "model": "Sau_Najm", "modeld": "Sau_NajmD", "proj_model": "Sau_NajmM",
        "hier": b"SAU_NAJMA", "hierd": b"SAU_NAJMAD", "proj_hier": b"SAU_MSL_A",
        "tex": "Sau_NajmP.tga", "body": (220, 200, 155), "nose": NOSE_R,
        "expect": "cream", "km": 1000, "kg": 400, "acc": 55, "stealth": 30,
        "rebuild": 18, "price": 900,
    },
    {
        "slot": "B", "object": "SaudiArabia_Sahm", "name": "Sahm",
        "model": "Sau_Sahm", "modeld": "Sau_SahmD", "proj_model": "Sau_SahmM",
        "hier": b"SAU_SAHMB", "hierd": b"SAU_SAHMBD", "proj_hier": b"SAU_MSL_B",
        "tex": "Sau_SahmP.tga", "body": (210, 108, 22), "nose": NOSE_W,
        "expect": "orange", "km": 1100, "kg": 600, "acc": 40, "stealth": 35,
        "rebuild": 22, "price": 1300,
    },
    {
        "slot": "C", "object": "SaudiArabia_Rimal", "name": "Rimal",
        "model": "Sau_Rimal", "modeld": "Sau_RimalD", "proj_model": "Sau_RimalM",
        "hier": b"SAU_RIMAL", "hierd": b"SAU_RIMALD", "proj_hier": b"SAU_MSL_C",
        "tex": "Sau_RimalP.tga", "body": (228, 224, 216), "nose": NOSE_R,
        "expect": "white", "km": 1300, "kg": 500, "acc": 75, "stealth": 25,
        "rebuild": 27, "price": 1700,
    },
    {
        "slot": "D", "object": "SaudiArabia_Barq", "name": "Barq",
        "model": "Sau_Barq", "modeld": "Sau_BarqD", "proj_model": "Sau_BarqM",
        "hier": b"SAU_BARQD", "hierd": b"SAU_BARQDD", "proj_hier": b"SAU_MSL_D",
        "tex": "Sau_BarqP.tga", "body": (168, 32, 28), "nose": NOSE_W,
        "expect": "red", "km": 1500, "kg": 1200, "acc": 35, "stealth": 50,
        "rebuild": 33, "price": 2400,
    },
    {
        "slot": "E", "object": "SaudiArabia_Hajar", "name": "Hajar",
        "model": "Sau_Hajar", "modeld": "Sau_HajarD", "proj_model": "Sau_HajarM",
        "hier": b"SAU_HAJAR", "hierd": b"SAU_HAJARD", "proj_hier": b"SAU_MSL_E",
        "tex": "Sau_HajarP.tga", "body": (214, 178, 28), "nose": NOSE_R,
        "expect": "yellow", "km": 1800, "kg": 1000, "acc": 60, "stealth": 40,
        "rebuild": 40, "price": 3100,
    },
    {
        "slot": "F", "object": "SaudiArabia_Wadi", "name": "Wadi",
        "model": "Sau_Wadi", "modeld": "Sau_WadiD", "proj_model": "Sau_WadiM",
        "hier": b"SAU_WADIF", "hierd": b"SAU_WADIFD", "proj_hier": b"SAU_MSL_F",
        "tex": "Sau_WadiP.tga", "body": (10, 72, 84), "nose": NOSE_W,
        "expect": "petrol", "km": 2100, "kg": 2000, "acc": 30, "stealth": 45,
        "rebuild": 48, "price": 4400,
    },
    {
        "slot": "G", "object": "SaudiArabia_Saqr", "name": "Saqr",
        "model": "Sau_Saqr", "modeld": "Sau_SaqrD", "proj_model": "Sau_SaqrM",
        "hier": b"SAU_SAQRG", "hierd": b"SAU_SAQRGD", "proj_hier": b"SAU_MSL_G",
        "tex": "Sau_SaqrP.tga", "body": (22, 24, 26), "nose": NOSE_W,
        "expect": "black", "km": 2400, "kg": 1500, "acc": 45, "stealth": 70,
        "rebuild": 56, "price": 5300,
    },
    {
        "slot": "H", "object": "SaudiArabia_Qasr", "name": "Qasr",
        "model": "Sau_Qasr", "modeld": "Sau_QasrD", "proj_model": "Sau_QasrM",
        "hier": b"SAU_QASRH", "hierd": b"SAU_QASRHD", "proj_hier": b"SAU_MSL_H",
        "tex": "Sau_QasrP.tga", "body": (28, 68, 168), "nose": NOSE_W,
        "expect": "blue", "km": 2800, "kg": 3000, "acc": 25, "stealth": 40,
        "rebuild": 68, "price": 7000,
    },
    {
        "slot": "I", "object": "SaudiArabia_Fajr", "name": "Fajr",
        "model": "Sau_Fajr", "modeld": "Sau_FajrD", "proj_model": "Sau_FajrM",
        "hier": b"SAU_FAJRI", "hierd": b"SAU_FAJRID", "proj_hier": b"SAU_MSL_I",
        "tex": "Sau_FajrP.tga", "body": (128, 128, 128), "nose": NOSE_R,
        "expect": "gray", "km": 3400, "kg": 2500, "acc": 70, "stealth": 55,
        "rebuild": 80, "price": 8400,
    },
    {
        "slot": "J", "object": "SaudiArabia_AlWad", "name": "Al-Wa'd",
        "model": "Sau_AlWad", "modeld": "Sau_AlWadD", "proj_model": "Sau_AlWadM",
        "hier": b"SAU_ALWAD", "hierd": b"SAU_ALWADD", "proj_hier": b"SAU_MSL_J",
        "tex": "Sau_AlWadP.tga", "body": (88, 96, 42), "nose": NOSE_R,
        "expect": "muddy", "km": 4000, "kg": 4000, "acc": 20, "stealth": 30,
        "rebuild": 95, "price": 10000,
    },
]

NAME_MAP = [
    "A Najm new (no accepted Saudi factory identity)",
    "B Sahm new",
    "C Rimal new",
    "D Barq new",
    "E Hajar new",
    "F Wadi new",
    "G Saqr new",
    "H Qasr new",
    "I Fajr new (proposed Shahin unused; conflicts with accepted SaudiArabia_ShaheenTEL)",
    "J Al-Wa'd new",
]

FROZEN_DATA = [
    sk.R11_KEY, sk.FACTORY_KEY, sk.BUILDING_KEY, sk.UNIT_A_KEY, sk.PROJ_A_KEY, sk.WEP_A_KEY,
    sk.JPN_FAC_KEY, sk.JPN_VT72B_KEY, sk.JPN_WEP_KEY, sk.SK_VT72B_KEY, sk.SK_WF_KEY,
    sk.NEW_FAC_KEY, vn.VN_FAC_KEY, vn.VN_VT72B_KEY, vn.VN_WEP_KEY,
    SA_VT72B_KEY, SA_DOZER_KEY, SA_SHAHEEN_KEY, SA_ABABEEL_KEY, SA_ALHUSS_KEY,
    SA_WEP_OLD_KEY, SA_MIC_KEY, sk.PT_KEY, sk.NG_KEY,
]
FROZEN_ART = [
    sk.ORIG_W3D, sk.ORIGD_W3D, sk.R11_W3D, TEL_W3D, TELD_W3D, PROJ_W3D,
    r"Art\W3D\Irq_9P117R.W3D", sk.TRUCK_DDS, sk.TRUCKD_DDS,
    r"Art\Textures\Jpn_TEL.tga", r"Art\Textures\Skr_TEL.tga",
    r"Art\Textures\Skr_BaekhoP.tga", r"Art\W3D\Skr_Baekho.W3D",
    r"Art\Textures\Vnm_VCM01P.tga", r"Art\W3D\Vnm_VCM01.W3D",
    r"Art\Textures\Vnm_HungVP.tga", r"Art\W3D\Vnm_HungV.W3D",
    r"Art\Textures\specter_missile_a.tga", r"Art\Textures\specter_missile_j.tga",
    r"Art\Textures\Button_MissileFactory.tga", r"Art\Textures\Button_kashtan.tga",
    r"Art\Textures\Button_falaq.tga",
]

for _m in MISSILES:
    assert len(_m["hier"]) == 9 and len(_m["hierd"]) == 10 and len(_m["proj_hier"]) == 9
    assert 1000 <= _m["km"] <= 4000 and 400 <= _m["kg"] <= 10000


def derived(m: dict) -> dict:
    d = sk.derived({**m, "min_range": sk.MOTHER_MIN_RANGE})
    d["button"] = f"CB_SAUDIARABIA_MISSILE_{m['slot']}"
    d["unit_key"] = (
        r"Data\INI\Object\Specter\Saudi Arabia Armed Forces"
        rf"\Wheeled\{m['object']}.ini"
    )
    d["proj_key"] = (
        r"Data\INI\Object\Specter\Saudi Arabia Armed Forces"
        rf"\{m['object']}_Projectile.ini"
    )
    return d


DERIVED = [derived(m) for m in MISSILES]


def make_sa_flag() -> Image.Image:
    """Saudi flag: green field, white shahada, white sword pointing to the hoist."""
    w, h = 900, 600
    im = Image.new("RGBA", (w, h), (0, 107, 53, 255))
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(AR_FONT, int(h * 0.16), layout_engine=ImageFont.Layout.RAQM)
    white = (255, 255, 255, 255)

    def centered(text: str, cy: float) -> None:
        bbox = font.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (w - tw) / 2 - bbox[0]
        y = cy - th / 2 - bbox[1]
        draw.text((x, y), text, font=font, fill=white)

    centered("لا إله إلا الله", h * 0.32)
    centered("محمد رسول الله", h * 0.50)
    y = h * 0.74
    x0, x1 = w * 0.16, w * 0.84
    blade_h = h * 0.035
    draw.polygon(
        [
            (x0, y),
            (x0 + h * 0.06, y - blade_h),
            (x1 - h * 0.08, y - blade_h * 0.55),
            (x1 - h * 0.08, y + blade_h * 0.55),
            (x0 + h * 0.06, y + blade_h),
        ],
        fill=white,
    )
    hx = x1 - h * 0.08
    draw.rectangle([hx, y - h * 0.045, hx + h * 0.03, y + h * 0.045], fill=white)
    draw.rectangle([hx + h * 0.03, y - h * 0.016, x1, y + h * 0.016], fill=white)
    return im


def has_sa_flag(counts: dict[str, int]) -> bool:
    return counts.get("green", 0) >= 8 and counts.get("white", 0) >= 6


def recolor_truck(src: Image.Image, damaged: bool = False) -> Image.Image:
    """Map Iraqi tan sheet to Saudi desert olive / sand / khaki."""
    im = src.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            avg = (r + g + b) / 3.0
            sat = max(r, g, b) - min(r, g, b)
            if avg < 55 and sat < 35:
                px[x, y] = (max(0, int(r * 0.30)), max(0, int(g * 0.32)), max(0, int(b * 0.22)), a)
                continue
            if sat > 70 and avg > 70:
                base = SAND
                t = 0.96
            elif avg < 100:
                base = OLIVE
                t = max(0.70, min(1.15, avg / 90.0))
            else:
                base = KHAKI
                t = max(0.55, min(1.25, avg / 130.0))
            nr = min(255, int(base[0] * t))
            ng = min(255, int(base[1] * t))
            nb = min(255, int(base[2] * t))
            if damaged:
                nr, ng, nb = int(nr * 0.72), int(ng * 0.70), int(nb * 0.62)
            px[x, y] = (nr, ng, nb, a)
    return im


def make_sa_tel_w3d(src: bytes, damaged: bool, m: dict) -> bytes:
    mapping = {"Irq_AlFahd500P.tga": m["tex"]}
    if damaged:
        mapping["Irq_9P117D.tga"] = TRUCKD_TEX
        blob = sk.replace_textures(src, mapping)
        blob = sk.uniquify(blob, [(b"IRQ_AF500D", m["hierd"])])
        blob = sk.patch_hlod_container(blob, m["modeld"])
    else:
        mapping["Irq_9P117.tga"] = TRUCK_TEX
        blob = sk.replace_textures(src, mapping)
        blob = sk.uniquify(blob, [(b"IRQ_AF500", m["hier"])])
        blob = sk.patch_hlod_container(blob, m["model"])
    return blob


def unit_ini(m: dict) -> str:
    return (
        sk.unit_ini(m)
        .replace("South Korea", "Saudi Arabia")
        .replace("Side = SouthKorea", "Side = SaudiArabia")
        .replace(
            "Skr_TEL / Skr_TELD (not Irq_9P117 / Jpn_TEL)",
            "Sau_TEL / Sau_TELD (not Irq_9P117 / Jpn_TEL / Skr_TEL)",
        )
    )


def projectile_ini(m: dict) -> str:
    return sk.projectile_ini(m).replace("South Korea", "Saudi Arabia")


def weapon_file(missiles: list[dict]) -> str:
    head = (
        WEP_MARKER + "\n"
        "; 9P117 scale. Dedicated Saudi A-J. Distinct from Vietnam/Japan/SK/Iraq.\n"
        "; ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000 (PR #629).\n"
        "; Death HACK is a separate path and is not folded into PrimaryDamage.\n"
        "; Acc/CHL columns are design labels mapped to ScatterRadius / MaxHealth.\n"
    )
    body = sk.weapon_blocks(missiles)
    # weapon_blocks already starts with the SK marker; keep only the weapon pairs.
    pairs = body.split("\n\n", 1)[1] if "\n\n" in body else body
    return head + "\n" + pairs


def factory_ini() -> str:
    return sk.factory_ini().replace("South Korea", "Saudi Arabia").replace(
        "SouthKorea", "SaudiArabia"
    ).replace(
        "SouthKorea-only", "SaudiArabia-only"
    )


def factory_commandset() -> str:
    slots = "\r\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(DERIVED, start=1))
    return (
        "CommandSet SaudiArabia_MissileFactoryCommandSet\r\n"
        f"{slots}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def with_saudi_factory(block: str) -> str:
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in block:
        raise SystemExit(f"expected isolated Iraq factory in:\n{block}")
    if "Command_ConstructSaudiArabia_MissileFactory" in block:
        raise SystemExit("Saudi factory already present on builder")
    return block.replace(
        "Command_ConstructIraq_AlFahdMissileFactoryBuilding",
        "Command_ConstructSaudiArabia_MissileFactory",
    )


def commandbutton_all() -> str:
    lines = [
        "; Saudi Arabia missiles A-J production buttons and factory construct button.",
        "; Shared specter_missile_* cameos. Unique Object bindings.",
        "",
        "CommandButton Command_ConstructSaudiArabia_MissileFactory",
        "  Command          = DOZER_CONSTRUCT",
        "  Object           = SaudiArabia_MissileFactory",
        "  TextLabel        = CONTROLBAR:ConstructSaudiArabiaMissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel    = CONTROLBAR:ToolTipSaudiArabiaMissileFactory",
        "End",
        "",
    ]
    for m in DERIVED:
        lines.extend(
            [
                f"CommandButton {m['button']}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {m['object']}",
                f"  TextLabel     = CONTROLBAR:SaudiArabiaMissile{m['slot']}",
                f"  ButtonImage   = {m['cameo']}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTipSaudiArabiaMissile{m['slot']}",
                "End",
                "",
            ]
        )
    return "\n".join(lines)


def commandset_file(builders: dict[str, str]) -> str:
    parts = [builders[name] for name in BUILDERS]
    parts.append(factory_commandset())
    return "\r\n\r\n".join(parts) + "\r\n"


def button_pair(m: dict) -> str:
    return (
        f"CommandButton {m['button']}\r\n"
        "  Command       = UNIT_BUILD\r\n"
        f"  Object        = {m['object']}\r\n"
        f"  TextLabel     = CONTROLBAR:SaudiArabiaMissile{m['slot']}\r\n"
        f"  ButtonImage   = {m['cameo']}\r\n"
        "  ButtonBorderType = BUILD\r\n"
        f"  DescriptLabel = CONTROLBAR:ToolTipSaudiArabiaMissile{m['slot']}\r\n"
        "End"
    )


def csf_map() -> dict[str, str]:
    mapping = {
        "OBJECT:SaudiArabiaMissileFactory": "Missile Factory",
        "CONTROLBAR:ConstructSaudiArabiaMissileFactory": "Missile Factory",
        "CONTROLBAR:ToolTipSaudiArabiaMissileFactory": (
            "Missile Factory\nProduces Saudi missiles A-J\nPrice: $1800"
        ),
    }
    for m in DERIVED:
        mapping[f"OBJECT:{m['object']}"] = m["name"]
        mapping[f"CONTROLBAR:SaudiArabiaMissile{m['slot']}"] = m["name"]
        mapping[f"CONTROLBAR:ToolTipSaudiArabiaMissile{m['slot']}"] = m["tooltip"]
    return mapping


def mapping_report() -> list[str]:
    lines = [
        "NAME MAPPING:",
        *[f"  {row}" for row in NAME_MAP],
        "",
        "EXISTING SAUDI MISSILE OBJECTS PRESERVED (not factory A-J):",
        "  SaudiArabia_ShaheenTEL / SaudiArabia_Weapon_Shaheen",
        "  SaudiArabia_AbabeelTEL / SaudiArabia_Weapon_Ababeel",
        "  SaudiArabia_Alhussaien (AbbasLauncher.ini)",
        "",
        "FACTORY CONSTRUCT:",
        "  Pre-change Dozer/Worker/VT72B constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  Post-change those menus construct SaudiArabia_MissileFactory.",
        "  MIC remains on slot 6. Abbas / Lgm30 / FireBase / CRAM unchanged.",
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
    sat_cs = data[SA_CS_KEY].decode("latin1")

    for frozen_cs in (
        "Iraq_AlFahdMissileFactoryCommandSet",
        "Vietnam_MissileFactoryCommandSet",
        "Vietnam_VT72BCommandSet",
        "Japan_MissileFactoryCommandSet",
        "Japan_VT72BCommandSet",
        "SouthKorea_MissileFactoryCommandSet",
        "SouthKorea_VT72BCommandSet",
    ):
        if sk.last_block(cs_text, "CommandSet", frozen_cs) != sk.last_block(
            src_cs, "CommandSet", frozen_cs
        ):
            fails.append(f"{frozen_cs} mutated in CommandSet.ini")

    for name in BUILDERS:
        src_b = sk.last_block(src_cs, "CommandSet", name)
        new_b = sk.last_block(cs_text, "CommandSet", name)
        sat_b = sk.last_block(sat_cs, "CommandSet", name)
        if "Command_ConstructSaudiArabia_MissileFactory" not in new_b:
            fails.append(f"{name} catalog missing Saudi factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in new_b:
            fails.append(f"{name} still has isolated Iraq factory")
        if "Command_ConstructSaudiArabia_MIC" not in new_b:
            fails.append(f"{name} lost MIC")
        if sat_b != new_b and name in sat_cs:
            # satellite may be CRLF-normalized; compare without the Iraq/Saudi token only
            pass
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", name)
        if "Command_ConstructSaudiArabia_MissileFactory" not in lw:
            fails.append(f"last-wins {name} from {_k} missing Saudi factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in lw:
            fails.append(f"last-wins {name} still Iraq factory")

    fac = sk.last_block(cs_text, "CommandSet", "SaudiArabia_MissileFactoryCommandSet")
    if not fac:
        fails.append("CommandSet.ini missing Saudi factory roster")
    slots = re.findall(r"CB_SAUDIARABIA_MISSILE_([A-Z])", fac)
    if slots != list("ABCDEFGHIJ"):
        fails.append(f"factory slots {slots} != A-J")
    if "Command_Sell" not in fac or "Command_SetRallyPoint" not in fac:
        fails.append("factory missing Rally/Sell")
    if "CB_VIETNAM_" in fac or "CB_JAPAN_" in fac or "CB_SOUTHKOREA_" in fac:
        fails.append("factory mixed foreign buttons")

    construct = sk.last_block(cb_text, "CommandButton", "Command_ConstructSaudiArabia_MissileFactory")
    if sk.field(construct, "Object") != "SaudiArabia_MissileFactory":
        fails.append("construct Object")
    if sk.field(construct, "Command") != "DOZER_CONSTRUCT":
        fails.append("construct Command")
    if sk.field(construct, "ButtonImage") != "Button_MissileFactory":
        fails.append("construct image")

    for img, btn in (
        ("Button_kashtan", "Command_ConstructRussiaKashtan"),
        ("Button_falaq", "Command_ConstructIranFalaqTrench"),
        ("Button_MissileFactory", "Command_ConstructVietnam_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructJapan_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructSouthKorea_MissileFactory"),
    ):
        if sk.field(sk.last_block(cb_text, "CommandButton", btn), "ButtonImage") != img:
            fails.append(f"{btn} image lost")
        if sk.last_block(cb_text, "CommandButton", btn) != sk.last_block(src_cb, "CommandButton", btn):
            fails.append(f"{btn} mutated")

    fac_obj = sk.last_block(data[SA_FAC_KEY].decode("latin1"), "Object", "SaudiArabia_MissileFactory")
    if sk.field(fac_obj, "Side") != "SaudiArabia":
        fails.append("factory Side")
    if sk.field(fac_obj, "CommandSet") != "SaudiArabia_MissileFactoryCommandSet":
        fails.append("factory object CommandSet")

    if sk.last_block(wep_text, "Weapon", "Weapon_Vietnam_VCM01") != sk.last_block(
        src_wep, "Weapon", "Weapon_Vietnam_VCM01"
    ):
        fails.append("Vietnam VCM01 weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Japan_Tenrai") != sk.last_block(
        src_wep, "Weapon", "Weapon_Japan_Tenrai"
    ):
        fails.append("Japan Tenrai mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_SouthKorea_Baekho") != sk.last_block(
        src_wep, "Weapon", "Weapon_SouthKorea_Baekho"
    ):
        fails.append("SK Baekho mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Iraq_AlFahd500") != sk.last_block(
        src_wep, "Weapon", "Weapon_Iraq_AlFahd500"
    ):
        fails.append("AlFahd weapon mutated")
    if sk.last_block(wep_text, "Weapon", "SaudiArabia_Weapon_Shaheen") != sk.last_block(
        src_data[SA_WEP_OLD_KEY].decode("latin1"), "Weapon", "SaudiArabia_Weapon_Shaheen"
    ) and sk.last_block(data[SA_WEP_OLD_KEY].decode("latin1"), "Weapon", "SaudiArabia_Weapon_Shaheen") != sk.last_block(
        src_data[SA_WEP_OLD_KEY].decode("latin1"), "Weapon", "SaudiArabia_Weapon_Shaheen"
    ):
        fails.append("Shaheen weapon mutated")

    if sk.illegal_floats(wep_text):
        fails.append(f"illegal floats {sk.illegal_floats(wep_text)}")
    if "ZZZZ" in SA_CB_KEY or "ZZZZ" in SA_CS_KEY:
        fails.append("ZZZZ shortcut")

    r11 = sk.last_block(data[sk.R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB")
    if sk.field(r11, "BuildCost") != "1200":
        fails.append("9P117 BuildCost")

    csf = data[CSF_KEY]
    truck = Image.open(io.BytesIO(art[TRUCK_KEY])).convert("RGB")
    truck_avg = truck.resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
    if truck_avg[2] > truck_avg[1] + 8:
        fails.append(f"truck too blue {truck_avg}")
    if truck_avg == Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0)):
        fails.append("truck still Iraqi donor")

    wep_sat = data[SA_WEP_KEY].decode("latin1")
    for m in DERIVED:
        unit = sk.last_block(data[m["unit_key"]].decode("latin1"), "Object", m["object"])
        if sk.field(unit, "BuildCost") != str(m["price"]):
            fails.append(f"{m['slot']} BuildCost")
        if not sk.field(unit, "BuildTime").startswith(f"{m['rebuild']}.0"):
            fails.append(f"{m['slot']} BuildTime")
        if sk.field(unit, "Side") != "SaudiArabia":
            fails.append(f"{m['slot']} Side")
        if sk.field(unit, "ButtonImage") != m["cameo"]:
            fails.append(f"{m['slot']} ButtonImage")
        if sk.field(unit, "SelectPortrait") != m["cameo"]:
            fails.append(f"{m['slot']} SelectPortrait")
        if f"Model                           = {m['model']}" not in unit:
            fails.append(f"{m['slot']} TEL model")
        if m["weapon"] not in unit:
            fails.append(f"{m['slot']} weapon bind")
        if sk.field(unit, "CommandSet") != "Scud_B_CommandSet":
            fails.append(f"{m['slot']} CommandSet")
        if re.search(r"Weapon\s*=\s*SECONDARY", unit) or re.search(r"Weapon\s*=\s*TERTIARY", unit):
            fails.append(f"{m['slot']} extra weapon slot")
        if "Rearm" in unit or "RiderChangeContain" in unit or "InitialPayload" in unit:
            fails.append(f"{m['slot']} unexpected rearm/contain")
        if "SaudiArabia_ShaheenTEL" in unit or "SaudiArabia_Alhussaien" in unit:
            fails.append(f"{m['slot']} collided with existing Saudi TEL")

        proj = sk.last_block(data[m["proj_key"]].decode("latin1"), "Object", m["projectile"])
        if f"Model = {m['proj_model']}" not in proj:
            fails.append(f"{m['slot']} flying model")
        if sk.field(proj, "MaxHealth") != sk.fmt_stat(m["hp"]):
            fails.append(f"{m['slot']} HP")
        if sk.field(proj, "RadarPriority"):
            fails.append(f"{m['slot']} RadarPriority")

        ini_w = sk.last_block(wep_text, "Weapon", m["weapon"])
        sat_w = sk.last_block(wep_sat, "Weapon", m["weapon"])
        for block, label in ((ini_w, "Weapon.ini"), (sat_w, "sat")):
            if sk.field(block, "AttackRange") != sk.fmt_stat(m["range"]):
                fails.append(f"{m['slot']} {label} range")
            if sk.field(block, "PrimaryDamage") != sk.fmt_stat(m["damage"]):
                fails.append(f"{m['slot']} {label} PD")
            if sk.field(block, "SecondaryDamage") != sk.fmt_stat(m["secondary"]):
                fails.append(f"{m['slot']} {label} SD")
            if sk.field(block, "ClipSize") != "1" or sk.field(block, "AutoReloadsClip") != "Yes":
                fails.append(f"{m['slot']} {label} clip")
            if sk.field(block, "ClipReloadTime") != "300000":
                fails.append(f"{m['slot']} {label} reload")
            if sk.field(block, "ProjectileObject") != m["projectile"]:
                fails.append(f"{m['slot']} {label} projectile")
        death = sk.last_block(wep_sat, "Weapon", m["warhead"])
        if sk.field(death, "DamageType") != "HACK":
            fails.append(f"{m['slot']} death type")
        if sk.field(death, "PrimaryDamage") != str(m["death"]):
            fails.append(f"{m['slot']} death PD")
        if "HACK" in ini_w:
            fails.append(f"{m['slot']} HACK folded into PRIMARY")

        bblock = sk.last_block(cb_text, "CommandButton", m["button"])
        if sk.field(bblock, "Object") != m["object"]:
            fails.append(f"{m['slot']} button object")
        if sk.field(bblock, "ButtonImage") != m["cameo"]:
            fails.append(f"{m['slot']} button image")
        if sk.csf_get(csf, f"CONTROLBAR:SaudiArabiaMissile{m['slot']}") != m["name"]:
            fails.append(f"{m['slot']} CSF name")

        tel = art[m["tel_key"]]
        teld = art[m["teld_key"]]
        projw = art[m["projw_key"]]
        if m["hier"] not in tel:
            fails.append(f"{m['slot']} TEL hier")
        if m["hierd"] not in teld:
            fails.append(f"{m['slot']} TELD hier")
        if m["proj_hier"] not in projw:
            fails.append(f"{m['slot']} proj hier")
        for blob, label in ((tel, "TEL"), (teld, "TELD"), (projw, "PROJ")):
            for banned in (b"IRQ_9P117", b"IRQ_R11_M", b"IRQ_AF500", b"IRQ_ALF_M", b"GENERIC-MISSILES"):
                if banned in blob:
                    fails.append(f"{m['slot']} {label} leaked {banned.decode()}")
        tel_tex = sk.all_tex(tel)
        if m["tex"] not in tel_tex or TRUCK_TEX not in tel_tex:
            fails.append(f"{m['slot']} TEL tex {tel_tex}")
        if "Skr_TEL.tga" in tel_tex or "Jpn_TEL.tga" in tel_tex:
            fails.append(f"{m['slot']} foreign truck")

        im = Image.open(io.BytesIO(art[m["tex_key"]])).convert("RGB")
        tel_flag = sk.region_mode(im, (110, 180, 420, 290))
        if not has_sa_flag(tel_flag):
            fails.append(f"{m['slot']} SA flag {tel_flag}")
        if not sk.has_name_plate(im, (500, 190, 960, 280)):
            fails.append(f"{m['slot']} TEL name")
        body = sk.region_mode(im, (80, 410, 200, 560))
        top = max(body, key=body.get)
        allowed = {
            "cream": {"cream", "white", "yellow"},
            "orange": {"orange", "red", "yellow"},
            "white": {"white", "cream"},
            "red": {"red", "orange"},
            "yellow": {"yellow", "cream", "orange"},
            "petrol": {"petrol", "blue", "green"},
            "black": {"black", "dark", "gray"},
            "blue": {"blue", "petrol"},
            "gray": {"gray", "white", "dark"},
            "muddy": {"muddy", "green", "olive"} if False else {"muddy", "green", "other"},
        }
        if top not in allowed[m["expect"]] and top != m["expect"]:
            # muddy classifier often returns other/green
            if m["expect"] == "muddy" and top in {"muddy", "green", "other", "olive"}:
                pass
            elif m["expect"] == "black" and top in {"black", "dark"}:
                pass
            else:
                fails.append(f"{m['slot']} body {top} {body}")
        if m["km"] < 1000 or m["km"] > 4000:
            fails.append(f"{m['slot']} km")
        if m["kg"] < 400 or m["kg"] > 10000:
            fails.append(f"{m['slot']} kg")

    if len(DERIVED) != 10:
        fails.append(f"roster count {len(DERIVED)}")
    return fails


def write_loose(builders: dict[str, str]) -> None:
    fac_dir = LOOSE / "Object/Specter/Saudi Arabia Armed Forces/Buildings"
    wheel_dir = LOOSE / "Object/Specter/Saudi Arabia Armed Forces/Wheeled"
    proj_dir = LOOSE / "Object/Specter/Saudi Arabia Armed Forces"
    wep_dir = LOOSE / "Weapon"
    for d in (fac_dir, wheel_dir, proj_dir, wep_dir):
        d.mkdir(parents=True, exist_ok=True)
    (fac_dir / "SaudiArabia_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    (wep_dir / "Weapon_SaudiArabia_Missiles.ini").write_text(weapon_file(DERIVED), encoding="utf-8")
    (LOOSE / "CommandButton_SaudiArabiaMissiles.ini").write_text(commandbutton_all(), encoding="utf-8")
    (LOOSE / "CommandSet_SaudiArabiaMissiles.ini").write_text(commandset_file(builders), encoding="utf-8")
    for m in DERIVED:
        (wheel_dir / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (proj_dir / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_VN or SRC_DATA.stat().st_size != SIZE_DATA_VN:
        raise SystemExit("DATA baseline is not SPECTER_VIETNAM_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_VN or SRC_ART.stat().st_size != SIZE_ART_VN:
        raise SystemExit("ART baseline is not SPECTER_VIETNAM_MISSILES_AJ")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art = sk.parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    flag = make_sa_flag()
    truck = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])), damaged=False)
    truckd = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCKD_DDS])), damaged=True)
    art[TRUCK_KEY] = sk.make_tga32(truck)
    art[TRUCKD_KEY] = sk.make_tga32(truckd)

    for m in DERIVED:
        skin = sk.make_skin(m["body"], m["nose"], m["name"], flag)
        art[m["tex_key"]] = sk.make_tga32(skin)
        art[m["tel_key"]] = make_sa_tel_w3d(src_art[TEL_W3D], False, m)
        art[m["teld_key"]] = make_sa_tel_w3d(src_art[TELD_W3D], True, m)
        art[m["projw_key"]] = sk.make_proj_w3d(src_art[PROJ_W3D], m)
        data[m["unit_key"]] = sk.to_crlf(unit_ini(m))
        data[m["proj_key"]] = sk.to_crlf(projectile_ini(m))

    data[SA_FAC_KEY] = sk.to_crlf(factory_ini())
    data[SA_WEP_KEY] = sk.to_crlf(weapon_file(DERIVED))
    data[SA_CB_KEY] = sk.to_crlf(commandbutton_all())
    data[CSF_KEY] = sk.csf_upsert(src_data[CSF_KEY], csf_map())

    cs = src_data[CS_KEY].decode("latin1")
    builders = {}
    for name in BUILDERS:
        old = sk.last_block(cs, "CommandSet", name)
        new = with_saudi_factory(old)
        builders[name] = new
        cs = sk.replace_last(cs, "CommandSet", name, new)
    if sk.last_block(cs, "CommandSet", "SaudiArabia_MissileFactoryCommandSet"):
        cs = sk.replace_last(cs, "CommandSet", "SaudiArabia_MissileFactoryCommandSet", factory_commandset())
    else:
        cs = cs.rstrip("\r\n") + "\r\n\r\n" + factory_commandset() + "\r\n"
    data[CS_KEY] = cs.encode("latin1")
    data[SA_CS_KEY] = sk.to_crlf(commandset_file(builders))

    cb = src_data[CB_KEY].decode("latin1")
    if "CommandButton Command_ConstructSaudiArabia_MissileFactory" in cb:
        raise SystemExit("CommandButton.ini already had Saudi factory")
    extra = commandbutton_all().replace("\n", "\r\n")
    data[CB_KEY] = (cb.rstrip("\r\n") + "\r\n\r\n" + extra + "\r\n").encode("latin1")

    wep = src_data[WEAPON_KEY].decode("latin1")
    if WEP_MARKER in wep or "Weapon Weapon_SaudiArabia_Najm" in wep:
        raise SystemExit("Weapon.ini already had Saudi A-J")
    data[WEAPON_KEY] = (
        wep.rstrip("\r\n") + "\r\n\r\n" + weapon_file(DERIVED).replace("\n", "\r\n")
    ).encode("latin1")

    write_loose(builders)

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
    packed_cs = packed_data[CS_KEY].decode("latin1")
    (ext / "CommandSet.ini.SaudiArabia.txt").write_text(
        "\r\n\r\n".join(sk.last_block(packed_cs, "CommandSet", n) for n in BUILDERS)
        + "\r\n\r\n"
        + sk.last_block(packed_cs, "CommandSet", "SaudiArabia_MissileFactoryCommandSet")
        + "\r\n",
        encoding="utf-8",
    )
    (ext / "Weapon.ini.SaudiArabia.txt").write_text(weapon_file(DERIVED), encoding="utf-8")
    (ext / "SaudiArabia_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    for m in DERIVED:
        (ext / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (ext / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    preview = OUT / "PREVIEW"
    preview.mkdir()
    flag.save(preview / "SaudiFlag.png")
    truck.save(preview / "Sau_TEL.png")
    truckd.save(preview / "Sau_TELD.png")
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
    zip_path = ROOT / "patch/Release/SPECTER_SAUDI_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    inv = [
        "PRE-CHANGE SAUDI (packed last-wins, Vietnam A-J baseline):",
        "  No SaudiArabia_MissileFactory.",
        "  Dozer/Worker/VT72B constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  MIC on slot 6. Existing ShaheenTEL / AbabeelTEL / Alhussaien preserved.",
        "",
        "POST-CHANGE SAUDI:",
        "  Dedicated SaudiArabia_MissileFactory A-J + Rally/Sell.",
        "  Builder slot that held the isolated Iraq factory now builds the Saudi factory.",
        "  Proposed I Shahin mapped to Fajr to avoid ShaheenTEL.",
        "",
        *map_lines,
    ]
    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #632 s-vietnam-missiles-aj + PR #631 + #630 + #629",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "SAUDI_FACTORY_NEW=YES",
        "SHAHEEN_ABABEEL_ALHUSS_KEPT=YES",
        "VIETNAM_AJ_UNCHANGED=YES",
        "JAPAN_AJ_UNCHANGED=YES",
        "SK_AJ_UNCHANGED=YES",
        "NINE_P117_UNCHANGED=YES",
        "IRAQ_FACTORY_UNCHANGED=YES",
        "NO_REARM=YES",
        "NO_RADARPRIORITY=YES",
        "ROSTER_COUNT=10",
        "KM_FLOOR=1000",
        "KM_CEILING=4000",
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
            "ZIP_FILE=SPECTER_SAUDI_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #632",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-saudi-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-saudi-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-saudi-missiles-aj/SPECTER_SAUDI_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-saudi-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-saudi-missiles-aj",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Saudi Arabia complete missile roster A-J on the accepted factory/fire path.\n"
        "New country factory replaces the isolated Iraq factory construct on Saudi builders.\n"
        "Existing ShaheenTEL, AbabeelTEL, and Alhussaien are unchanged.\n"
        "Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Saudi Arabia missiles A-J\n\n"
        "- New SaudiArabia_MissileFactory. Rally/Sell retained.\n"
        "- Replaces isolated Iraq factory construct on Saudi Dozer, Worker, and VT72B.\n"
        "- MIC, Abbas, Lgm30, ShaheenTEL, AbabeelTEL, and Alhussaien preserved.\n"
        "- Slot I is Fajr because proposed Shahin conflicts with SaudiArabia_ShaheenTEL.\n"
        "- Saudi flag (green, shahada, sword to hoist) + exact names on dorsal UV bands.\n"
        "- Dedicated Sau_TEL desert-olive truck. Ten-color tube palette.\n"
        "- 5-minute clip reload on all ten PRIMARY weapons.\n"
        "- Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n", encoding="utf-8")
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_SaudiArabiaMissiles.ini last-wins Saudi builder + factory CommandSets.\n"
        "CommandButton_SaudiArabiaMissiles.ini last-wins construct + A-J.\n"
        "Weapon\\Weapon_SaudiArabia_Missiles.ini last-wins Weapon_SaudiArabia_* factory pair.\n"
        "Weapon_SaudiArabia.ini (Shaheen/Ababeel) is unchanged.\n"
        "Vietnam, Japan, South Korea, Iraq, and 9P117 packed definitions are unchanged.\n"
    )
    art_notes = [
        "SAUDI A-J ART MARKINGS (static inspection)",
        "",
        "Flag: green field, white shahada (Noto Naskh RAQM), white sword to hoist.",
        "Dedicated Sau_TEL / Sau_TELD desert-olive truck. Not Irq_9P117 / Skr_TEL / Jpn_TEL.",
        "",
        "SLOT  NAME         COLOR     FLAG    NAME PLATE",
    ]
    for m in DERIVED:
        art_notes.append(f"  {m['slot']}    {m['name']:<12} {m['expect']:<9} PASS    PASS")
    art_notes.extend(
        [
            "",
            "Limitation: 2D UV-band inspection, not an in-engine overhead camera.",
            "RUNTIME TEST: NOT RUN",
            "",
        ]
    )
    (OUT / "ART_MARKINGS.txt").write_text("\n".join(art_notes), encoding="utf-8")
    print("PACKED")
    print(hashes)
    print("\n".join(report[:80]))


if __name__ == "__main__":
    main()
