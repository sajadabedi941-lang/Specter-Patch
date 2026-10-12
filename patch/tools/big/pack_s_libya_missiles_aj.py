#!/usr/bin/env python3
"""Implement Libya missile roster A-J on the UAE / Saudi / Vietnam / SK / Japan path.

Baseline: packed SPECTER_UAE_MISSILES_AJ (PR #634 + #633 + #632 + #631 + #630 + #629).

Libya has no missile factory. Dozer / Worker / VT72B slot 13 currently constructs
the isolated Sell-only Iraq_AlFahdMissileFactoryBuilding. Replace that slot with a
Libya-only factory. Keep MIC on slot 6.

Preserve existing Libya_ShaheenTEL, Libya_AbabeelTEL, and Libya_Alhussaien.
Slot A keeps the proposed name Fajr as object Libya_Fajr (distinct from
SaudiArabia_Fajr). Unrelated Libya buildings / economy / fighters stay frozen.

Saudi A-J, UAE A-J, Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117
stay frozen.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Satellite last-wins: CommandSet_LibyaMissiles.ini,
CommandButton_LibyaMissiles.ini, Weapon\\Weapon_Libya_Missiles.ini.
Libya flag (red / black+crescent-star / green) + exact names on dorsal UV bands.
Dedicated Lby_TEL truck. No RadarPriority. No rearm. No ZZZZ.
"""
from __future__ import annotations

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
import pack_s_saudi_missiles_aj as sa  # noqa: E402
import pack_s_uae_missiles_aj as uae  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_UAE_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_UAE_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_LIBYA_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_UAE = "2e3bb1ce19a7748f4b81602f1b126eb09073dc4b187ea6b4937af06c0ea90abc"
SIZE_DATA_UAE = 367514516
SHA_ART_UAE = "a238575190cbf4d008b2ed841ffd5aa5b375ee204bcbc2827e025b6ae702572e"
SIZE_ART_UAE = 1543811044

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

LBY_CB_KEY = r"Data\INI\CommandButton_LibyaMissiles.ini"
LBY_CS_KEY = r"Data\INI\CommandSet_LibyaMissiles.ini"
LBY_WEP_KEY = r"Data\INI\Weapon\Weapon_Libya_Missiles.ini"
LBY_FAC_KEY = (
    r"Data\INI\Object\Specter\Libyan Armed Forces"
    r"\Buildings\Libya_MissileFactory.ini"
)
LBY_VT72B_KEY = r"Data\INI\Object\Specter\Libyan Armed Forces\Tracked\VT72B.ini"
LBY_DOZER_KEY = r"Data\INI\Object\Specter\Libyan Armed Forces\Tracked\Libya_Dozer.ini"
LBY_SHAHEEN_KEY = r"Data\INI\Object\Specter\Libyan Armed Forces\Wheeled\Libya_ShaheenTEL.ini"
LBY_ABABEEL_KEY = r"Data\INI\Object\Specter\Libyan Armed Forces\Wheeled\Libya_AbabeelTEL.ini"
LBY_ALHUSS_KEY = r"Data\INI\Object\Specter\Libyan Armed Forces\Wheeled\AbbasLauncher.ini"
LBY_WEP_OLD_KEY = r"Data\INI\Weapon_Libya.ini"
LBY_MIC_KEY = r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_MIC.ini"

TRUCK_TEX = "Lby_TEL.tga"
TRUCKD_TEX = "Lby_TELD.tga"
TRUCK_KEY = rf"Art\Textures\{TRUCK_TEX}"
TRUCKD_KEY = rf"Art\Textures\{TRUCKD_TEX}"

WEP_MARKER = (
    "; ===== Libya missiles A-J "
    "(Weapon.ini load path for Command_FireMainWeapon) ====="
)

BUILDERS = [
    "LibyaDozerCommandSet",
    "Libya_WorkerCommandSet",
    "Libya_VT72BCommandSet",
]

OCHRE = (160, 124, 72)
EARTH = (112, 88, 52)
SOOT = (56, 48, 40)
NOSE_W = (236, 228, 210)
NOSE_R = (196, 16, 28)
NOSE_G = (0, 140, 64)

# Distinct from Saudi and UAE slot-for-slot colors. Desert / flag-forward.
MISSILES = [
    {
        "slot": "A", "object": "Libya_Fajr", "name": "Fajr",
        "model": "Lby_Fajr", "modeld": "Lby_FajrD", "proj_model": "Lby_FajrM",
        "hier": b"LBY_FAJRA", "hierd": b"LBY_FAJRAD", "proj_hier": b"LBY_MSL_A",
        "tex": "Lby_FajrP.tga", "body": (222, 182, 28), "nose": NOSE_R,
        "expect": "yellow", "km": 1000, "kg": 400, "acc": 55, "stealth": 35,
        "rebuild": 17, "price": 800,
    },
    {
        "slot": "B", "object": "Libya_Sahra", "name": "Sahra",
        "model": "Lby_Sahra", "modeld": "Lby_SahraD", "proj_model": "Lby_SahraM",
        "hier": b"LBY_SAHRB", "hierd": b"LBY_SAHRBD", "proj_hier": b"LBY_MSL_B",
        "tex": "Lby_SahraP.tga", "body": (200, 108, 20), "nose": NOSE_W,
        "expect": "orange", "km": 1100, "kg": 700, "acc": 45, "stealth": 30,
        "rebuild": 22, "price": 1200,
    },
    {
        "slot": "C", "object": "Libya_Waha", "name": "Waha",
        "model": "Lby_Waha", "modeld": "Lby_WahaD", "proj_model": "Lby_WahaM",
        "hier": b"LBY_WAHAC", "hierd": b"LBY_WAHACD", "proj_hier": b"LBY_MSL_C",
        "tex": "Lby_WahaP.tga", "body": (236, 228, 214), "nose": NOSE_G,
        "expect": "white", "km": 1250, "kg": 500, "acc": 75, "stealth": 25,
        "rebuild": 26, "price": 1600,
    },
    {
        "slot": "D", "object": "Libya_Jamahiriya", "name": "Jamahiriya",
        "model": "Lby_Jamah", "modeld": "Lby_JamahD", "proj_model": "Lby_JamahM",
        "hier": b"LBY_JAMAH", "hierd": b"LBY_JAMAHD", "proj_hier": b"LBY_MSL_D",
        "tex": "Lby_JamahP.tga", "body": (196, 16, 28), "nose": NOSE_W,
        "expect": "red", "km": 1450, "kg": 1400, "acc": 35, "stealth": 50,
        "rebuild": 32, "price": 2300,
    },
    {
        "slot": "E", "object": "Libya_Murzuq", "name": "Murzuq",
        "model": "Lby_Murzuq", "modeld": "Lby_MurzuqD", "proj_model": "Lby_MurzuqM",
        "hier": b"LBY_MURZU", "hierd": b"LBY_MURZUD", "proj_hier": b"LBY_MSL_E",
        "tex": "Lby_MurzuqP.tga", "body": (90, 88, 36), "nose": NOSE_W,
        "expect": "muddy", "km": 1700, "kg": 1100, "acc": 65, "stealth": 40,
        "rebuild": 39, "price": 3000,
    },
    {
        "slot": "F", "object": "Libya_Akhdar", "name": "Akhdar",
        "model": "Lby_Akhdar", "modeld": "Lby_AkhdarD", "proj_model": "Lby_AkhdarM",
        "hier": b"LBY_AKHDA", "hierd": b"LBY_AKHDAD", "proj_hier": b"LBY_MSL_F",
        "tex": "Lby_AkhdarP.tga", "body": (0, 158, 70), "nose": NOSE_W,
        "expect": "green", "km": 2000, "kg": 2200, "acc": 30, "stealth": 45,
        "rebuild": 47, "price": 4200,
    },
    {
        "slot": "G", "object": "Libya_Sirt", "name": "Sirt",
        "model": "Lby_Sirt", "modeld": "Lby_SirtD", "proj_model": "Lby_SirtM",
        "hier": b"LBY_SIRTG", "hierd": b"LBY_SIRTGD", "proj_hier": b"LBY_MSL_G",
        "tex": "Lby_SirtP.tga", "body": (0, 96, 108), "nose": NOSE_W,
        "expect": "petrol", "km": 2300, "kg": 1800, "acc": 50, "stealth": 70,
        "rebuild": 55, "price": 5100,
    },
    {
        "slot": "H", "object": "Libya_Fezzan", "name": "Fezzan",
        "model": "Lby_Fezzan", "modeld": "Lby_FezzanD", "proj_model": "Lby_FezzanM",
        "hier": b"LBY_FEZZA", "hierd": b"LBY_FEZZAD", "proj_hier": b"LBY_MSL_H",
        "tex": "Lby_FezzanP.tga", "body": (92, 88, 84), "nose": NOSE_R,
        "expect": "gray", "km": 2700, "kg": 3200, "acc": 25, "stealth": 40,
        "rebuild": 67, "price": 6800,
    },
    {
        "slot": "I", "object": "Libya_Orouba", "name": "Orouba",
        "model": "Lby_Orouba", "modeld": "Lby_OroubaD", "proj_model": "Lby_OroubaM",
        "hier": b"LBY_OROUB", "hierd": b"LBY_OROUBD", "proj_hier": b"LBY_MSL_I",
        "tex": "Lby_OroubaP.tga", "body": (36, 32, 112), "nose": NOSE_W,
        "expect": "blue", "km": 3300, "kg": 5500, "acc": 70, "stealth": 55,
        "rebuild": 80, "price": 9000,
    },
    {
        "slot": "J", "object": "Libya_GreatManMadeRiver", "name": "Great Man-Made River",
        "model": "Lby_GMMR", "modeld": "Lby_GMMRD", "proj_model": "Lby_GMMRM",
        "hier": b"LBY_GMMRJ", "hierd": b"LBY_GMMRJD", "proj_hier": b"LBY_MSL_J",
        "tex": "Lby_GMMRP.tga", "body": (188, 164, 112), "nose": NOSE_G,
        "expect": "cream", "km": 3900, "kg": 8000, "acc": 20, "stealth": 30,
        "rebuild": 100, "price": 12000,
    },
]

NAME_MAP = [
    "A Fajr new as Libya_Fajr (SaudiArabia_Fajr remains Saudi slot I; different object id)",
    "B Sahra new",
    "C Waha new",
    "D Jamahiriya new",
    "E Murzuq new",
    "F Akhdar new",
    "G Sirt new",
    "H Fezzan new",
    "I Orouba new",
    "J Great Man-Made River new",
]

FROZEN_DATA = list(uae.FROZEN_DATA) + [
    uae.UAE_FAC_KEY, uae.UAE_CB_KEY, uae.UAE_CS_KEY, uae.UAE_WEP_KEY,
    LBY_VT72B_KEY, LBY_DOZER_KEY, LBY_SHAHEEN_KEY, LBY_ABABEEL_KEY,
    LBY_ALHUSS_KEY, LBY_WEP_OLD_KEY, LBY_MIC_KEY,
]
FROZEN_DATA += [m["unit_key"] for m in uae.DERIVED]
FROZEN_DATA += [m["proj_key"] for m in uae.DERIVED]

FROZEN_ART = list(uae.FROZEN_ART) + [
    uae.TRUCK_KEY, uae.TRUCKD_KEY, uae.UAE_FLAG_KEY,
    r"Art\Textures\Uae_FalconP.tga", r"Art\W3D\Uae_Falcon.W3D",
]
FROZEN_ART += [m["tex_key"] for m in uae.DERIVED]
FROZEN_ART += [m["tel_key"] for m in uae.DERIVED]
FROZEN_ART += [m["teld_key"] for m in uae.DERIVED]
FROZEN_ART += [m["projw_key"] for m in uae.DERIVED]

for _m in MISSILES:
    assert len(_m["hier"]) == 9 and len(_m["hierd"]) == 10 and len(_m["proj_hier"]) == 9
    assert 1000 <= _m["km"] <= 4000 and 400 <= _m["kg"] <= 10000


def derived(m: dict) -> dict:
    d = sk.derived({**m, "min_range": sk.MOTHER_MIN_RANGE})
    d["button"] = f"CB_LIBYA_MISSILE_{m['slot']}"
    d["unit_key"] = (
        r"Data\INI\Object\Specter\Libyan Armed Forces"
        rf"\Wheeled\{m['object']}.ini"
    )
    d["proj_key"] = (
        r"Data\INI\Object\Specter\Libyan Armed Forces"
        rf"\{m['object']}_Projectile.ini"
    )
    return d


DERIVED = [derived(m) for m in MISSILES]


def _star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r_out: float, r_in: float, fill) -> None:
    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def make_libya_flag() -> Image.Image:
    """Libya flag: red / black / green equal stripes, white crescent and star in the black band."""
    w, h = 900, 600
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    draw = ImageDraw.Draw(im)
    stripe = h / 3.0
    draw.rectangle([0, 0, w, int(round(stripe))], fill=(231, 0, 19, 255))
    draw.rectangle([0, int(round(stripe)), w, int(round(stripe * 2))], fill=(0, 0, 0, 255))
    draw.rectangle([0, int(round(stripe * 2)), w, h], fill=(35, 158, 70, 255))

    cx, cy = w * 0.47, h * 0.50
    r = h * 0.105
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 255))
    ox = r * 0.34
    ir = r * 0.78
    draw.ellipse([cx - ir + ox, cy - ir, cx + ir + ox, cy + ir], fill=(0, 0, 0, 255))
    _star(draw, cx + r * 0.62, cy, r * 0.38, r * 0.16, (255, 255, 255, 255))
    return im


def has_libya_flag(counts: dict[str, int]) -> bool:
    greenish = counts.get("green", 0) + counts.get("muddy", 0)
    return (
        counts.get("red", 0) >= 4
        and counts.get("black", 0) >= 4
        and greenish >= 3
        and counts.get("white", 0) >= 2
    )


def recolor_truck(src: Image.Image, damaged: bool = False) -> Image.Image:
    """Map Iraqi tan sheet to Libya ochre / earth / soot. Not Saudi olive or UAE pearl."""
    im = src.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            avg = (r + g + b) / 3.0
            sat = max(r, g, b) - min(r, g, b)
            if avg < 55 and sat < 35:
                px[x, y] = (max(0, int(r * 0.36)), max(0, int(g * 0.32)), max(0, int(b * 0.24)), a)
                continue
            if sat > 70 and avg > 70:
                base = OCHRE
                t = 0.95
            elif avg < 100:
                base = EARTH
                t = max(0.70, min(1.15, avg / 90.0))
            else:
                base = OCHRE
                t = max(0.55, min(1.25, avg / 130.0))
            nr = min(255, int(base[0] * t))
            ng = min(255, int(base[1] * t))
            nb = min(255, int(base[2] * t))
            if damaged:
                nr, ng, nb = int(nr * 0.70), int(ng * 0.66), int(nb * 0.58)
            px[x, y] = (nr, ng, nb, a)
    return im


def make_lby_tel_w3d(src: bytes, damaged: bool, m: dict) -> bytes:
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
        .replace("South Korea", "Libya")
        .replace("Side = SouthKorea", "Side = Libya")
        .replace(
            "Skr_TEL / Skr_TELD (not Irq_9P117 / Jpn_TEL)",
            "Lby_TEL / Lby_TELD (not Irq_9P117 / Jpn_TEL / Skr_TEL / Sau_TEL / Uae_TEL)",
        )
    )


def projectile_ini(m: dict) -> str:
    return sk.projectile_ini(m).replace("South Korea", "Libya")


def weapon_file(missiles: list[dict]) -> str:
    head = (
        WEP_MARKER + "\n"
        "; 9P117 scale. Dedicated Libya A-J. Distinct from UAE/Saudi/Vietnam/Japan/SK/Iraq.\n"
        "; ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000 (PR #629).\n"
        "; Death HACK is a separate path and is not folded into PrimaryDamage.\n"
        "; Acc/CHL columns are design labels mapped to ScatterRadius / MaxHealth.\n"
    )
    body = sk.weapon_blocks(missiles)
    pairs = body.split("\n\n", 1)[1] if "\n\n" in body else body
    return head + "\n" + pairs


def factory_ini() -> str:
    text = sk.factory_ini()
    text = text.replace("; South Korea missile factory.", "; Libya missile factory.")
    text = text.replace(
        "with a SouthKorea-only CommandSet (A-J).",
        "with a Libya-only CommandSet (A-J).",
    )
    text = text.replace("Object SouthKorea_MissileFactory", "Object Libya_MissileFactory")
    text = text.replace(
        "DisplayName      = OBJECT:SouthKoreaMissileFactory",
        "DisplayName      = OBJECT:LibyaMissileFactory",
    )
    text = text.replace("Side             = SouthKorea", "Side             = Libya")
    text = text.replace(
        "CommandSet       = SouthKorea_MissileFactoryCommandSet",
        "CommandSet       = Libya_MissileFactoryCommandSet",
    )
    return text


def factory_commandset() -> str:
    slots = "\r\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(DERIVED, start=1))
    return (
        "CommandSet Libya_MissileFactoryCommandSet\r\n"
        f"{slots}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def with_libya_factory(block: str) -> str:
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in block:
        raise SystemExit(f"expected isolated Iraq factory in:\n{block}")
    if "Command_ConstructLibya_MissileFactory" in block:
        raise SystemExit("Libya factory already present on builder")
    return block.replace(
        "Command_ConstructIraq_AlFahdMissileFactoryBuilding",
        "Command_ConstructLibya_MissileFactory",
    )


def commandbutton_all() -> str:
    lines = [
        "; Libya missiles A-J production buttons and factory construct button.",
        "; Shared specter_missile_* cameos. Unique Object bindings.",
        "",
        "CommandButton Command_ConstructLibya_MissileFactory",
        "  Command          = DOZER_CONSTRUCT",
        "  Object           = Libya_MissileFactory",
        "  TextLabel        = CONTROLBAR:ConstructLibyaMissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel    = CONTROLBAR:ToolTipLibyaMissileFactory",
        "End",
        "",
    ]
    for m in DERIVED:
        lines.extend(
            [
                f"CommandButton {m['button']}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {m['object']}",
                f"  TextLabel     = CONTROLBAR:LibyaMissile{m['slot']}",
                f"  ButtonImage   = {m['cameo']}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTipLibyaMissile{m['slot']}",
                "End",
                "",
            ]
        )
    return "\n".join(lines)


def commandset_file(builders: dict[str, str]) -> str:
    parts = [builders[name] for name in BUILDERS]
    parts.append(factory_commandset())
    return "\r\n\r\n".join(parts) + "\r\n"


def player_tooltip(m: dict) -> str:
    """Player-visible production tooltip. Ratings are design indexes, not probabilities."""
    return (
        f"{m['slot']} {m['name']}\n"
        f"Range: {m['km']} km\n"
        f"Warhead: {m['kg']} kg\n"
        f"Accuracy: {m['acc']}/100 (impact scatter, not a hit %)\n"
        f"Radar evasion: {m['stealth']}/100 (interceptor toughness, not stealth)\n"
        f"Build Time: {m['rebuild']} sec\n"
        f"Price: ${m['price']}"
    )


def csf_map() -> dict[str, str]:
    mapping = {
        "OBJECT:LibyaMissileFactory": "Missile Factory",
        "CONTROLBAR:ConstructLibyaMissileFactory": "Missile Factory",
        "CONTROLBAR:ToolTipLibyaMissileFactory": (
            "Missile Factory\nProduces Libya missiles A-J\nPrice: $1800"
        ),
    }
    for m in DERIVED:
        mapping[f"OBJECT:{m['object']}"] = m["name"]
        mapping[f"CONTROLBAR:LibyaMissile{m['slot']}"] = f"{m['slot']} {m['name']}"
        mapping[f"CONTROLBAR:ToolTipLibyaMissile{m['slot']}"] = player_tooltip(m)
    return mapping


def mapping_report() -> list[str]:
    lines = [
        "NAME MAPPING:",
        *[f"  {row}" for row in NAME_MAP],
        "",
        "EXISTING LIBYA MISSILE OBJECTS PRESERVED (not factory A-J):",
        "  Libya_ShaheenTEL / Libya_Weapon_Shaheen",
        "  Libya_AbabeelTEL / Libya_Weapon_Ababeel",
        "  Libya_Alhussaien (AbbasLauncher.ini)",
        "",
        "FACTORY CONSTRUCT:",
        "  Pre-change Dozer/Worker/VT72B constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  Post-change those menus construct Libya_MissileFactory.",
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
        "  Acc/CHL table columns are design labels only.",
        "",
        "SLOT  NAME                    KM   KG   ACC CHL TIME COST  RANGE  PD     SD    DEATH SCATTER  HP     MINR",
    ]
    for m in DERIVED:
        lines.append(
            f"  {m['slot']}    {m['name']:<22} {m['km']:<4} {m['kg']:<4} "
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
    sat_cs = data[LBY_CS_KEY].decode("latin1")

    if "ZZZZ" in LBY_CB_KEY or "ZZZZ" in LBY_CS_KEY or "ZZZZ" in LBY_WEP_KEY:
        fails.append("ZZZZ shortcut")
    if LBY_CS_KEY >= r"Data\INI\CommandSet_ZZZZ":
        fails.append("Libya satellite sorts into ZZZZ")
    if LBY_CS_KEY <= CS_KEY:
        fails.append("Libya satellite sorts before CommandSet.ini")

    for frozen_cs in (
        "Iraq_AlFahdMissileFactoryCommandSet",
        "Vietnam_MissileFactoryCommandSet",
        "Japan_MissileFactoryCommandSet",
        "SouthKorea_MissileFactoryCommandSet",
        "SaudiArabia_MissileFactoryCommandSet",
        "SaudiArabiaDozerCommandSet",
        "UAE_MissileFactoryCommandSet",
        "UAEDozerCommandSet",
        "UAE_WorkerCommandSet",
        "UAE_VT72BCommandSet",
    ):
        if sk.last_block(cs_text, "CommandSet", frozen_cs) != sk.last_block(
            src_cs, "CommandSet", frozen_cs
        ):
            fails.append(f"{frozen_cs} mutated in CommandSet.ini")

    for name in BUILDERS:
        new_b = sk.last_block(cs_text, "CommandSet", name)
        if "Command_ConstructLibya_MissileFactory" not in new_b:
            fails.append(f"{name} catalog missing Libya factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in new_b:
            fails.append(f"{name} still has isolated Iraq factory")
        if "Command_ConstructLibya_MIC" not in new_b:
            fails.append(f"{name} lost MIC")
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", name)
        if "Command_ConstructLibya_MissileFactory" not in lw:
            fails.append(f"last-wins {name} from {_k} missing Libya factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in lw:
            fails.append(f"last-wins {name} still Iraq factory")
        if name not in sat_cs:
            fails.append(f"satellite missing {name}")

    fac = sk.last_block(cs_text, "CommandSet", "Libya_MissileFactoryCommandSet")
    if not fac:
        fails.append("CommandSet.ini missing Libya factory roster")
    slots = re.findall(r"CB_LIBYA_MISSILE_([A-Z])", fac)
    if slots != list("ABCDEFGHIJ"):
        fails.append(f"factory slots {slots} != A-J")
    if "Command_Sell" not in fac or "Command_SetRallyPoint" not in fac:
        fails.append("factory missing Rally/Sell")
    if any(
        tag in fac
        for tag in ("CB_VIETNAM_", "CB_JAPAN_", "CB_SOUTHKOREA_", "CB_SAUDIARABIA_", "CB_UAE_")
    ):
        fails.append("factory mixed foreign buttons")

    construct = sk.last_block(cb_text, "CommandButton", "Command_ConstructLibya_MissileFactory")
    if sk.field(construct, "Object") != "Libya_MissileFactory":
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
        ("Button_MissileFactory", "Command_ConstructSaudiArabia_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructUAE_MissileFactory"),
    ):
        if sk.field(sk.last_block(cb_text, "CommandButton", btn), "ButtonImage") != img:
            fails.append(f"{btn} image lost")
        if sk.last_block(cb_text, "CommandButton", btn) != sk.last_block(src_cb, "CommandButton", btn):
            fails.append(f"{btn} mutated")

    fac_obj = sk.last_block(data[LBY_FAC_KEY].decode("latin1"), "Object", "Libya_MissileFactory")
    if sk.field(fac_obj, "Side") != "Libya":
        fails.append("factory Side")
    if sk.field(fac_obj, "CommandSet") != "Libya_MissileFactoryCommandSet":
        fails.append("factory object CommandSet")
    if "SouthKorea_SupplyCenter" not in fac_obj:
        fails.append("factory lost SouthKorea_SupplyCenter prereq")
    if "Libya_SupplyCenter" not in fac_obj:
        fails.append("factory missing Libya_SupplyCenter prereq")

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
    if sk.last_block(wep_text, "Weapon", "Weapon_SaudiArabia_Najm") != sk.last_block(
        src_wep, "Weapon", "Weapon_SaudiArabia_Najm"
    ):
        fails.append("Saudi Najm weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_UAE_Falcon") != sk.last_block(
        src_wep, "Weapon", "Weapon_UAE_Falcon"
    ):
        fails.append("UAE Falcon weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Iraq_AlFahd500") != sk.last_block(
        src_wep, "Weapon", "Weapon_Iraq_AlFahd500"
    ):
        fails.append("AlFahd weapon mutated")
    if sk.last_block(data[LBY_WEP_OLD_KEY].decode("latin1"), "Weapon", "Libya_Weapon_Shaheen") != sk.last_block(
        src_data[LBY_WEP_OLD_KEY].decode("latin1"), "Weapon", "Libya_Weapon_Shaheen"
    ):
        fails.append("Libya Shaheen weapon mutated")

    if sk.illegal_floats(wep_text):
        fails.append(f"illegal floats {sk.illegal_floats(wep_text)}")

    r11 = sk.last_block(data[sk.R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB")
    if sk.field(r11, "BuildCost") != "1200":
        fails.append("9P117 BuildCost")

    uae_fac = sk.last_block(data[uae.UAE_FAC_KEY].decode("latin1"), "Object", "UAE_MissileFactory")
    if sk.field(uae_fac, "Side") != "UAE":
        fails.append("UAE factory Side mutated")
    sa_fac = sk.last_block(data[sa.SA_FAC_KEY].decode("latin1"), "Object", "SaudiArabia_MissileFactory")
    if sk.field(sa_fac, "Side") != "SaudiArabia":
        fails.append("Saudi factory Side mutated")

    truck = Image.open(io.BytesIO(art[TRUCK_KEY])).convert("RGB")
    truck_avg = truck.resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
    if truck_avg[2] > truck_avg[0] + 20:
        fails.append(f"truck too blue {truck_avg}")
    irq_avg = Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == irq_avg:
        fails.append("truck still Iraqi donor")
    sau_avg = Image.open(io.BytesIO(src_art[sa.TRUCK_KEY])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == sau_avg:
        fails.append("truck still Saudi olive")
    uae_avg = Image.open(io.BytesIO(src_art[uae.TRUCK_KEY])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == uae_avg:
        fails.append("truck still UAE pearl")

    wep_sat = data[LBY_WEP_KEY].decode("latin1")
    baseline_objects = set()
    obj_re = re.compile(rb"^Object (\S+)", re.M)
    for key, blob in src_data.items():
        if key.endswith(".ini") or key.endswith(".INI"):
            baseline_objects.update(mo.group(1).decode("ascii", "ignore") for mo in obj_re.finditer(blob))
    seen_objects = set()
    csf = data[CSF_KEY]
    for m in DERIVED:
        if m["object"] in seen_objects:
            fails.append(f"duplicate object {m['object']}")
        seen_objects.add(m["object"])
        if m["object"] in baseline_objects:
            fails.append(f"{m['slot']} {m['object']} already exists in baseline")

        unit = sk.last_block(data[m["unit_key"]].decode("latin1"), "Object", m["object"])
        if sk.field(unit, "BuildCost") != str(m["price"]):
            fails.append(f"{m['slot']} BuildCost")
        if not sk.field(unit, "BuildTime").startswith(f"{m['rebuild']}.0"):
            fails.append(f"{m['slot']} BuildTime")
        if sk.field(unit, "Side") != "Libya":
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
        if "Libya_ShaheenTEL" in unit or "Libya_Alhussaien" in unit or "SaudiArabia_Fajr" in unit:
            fails.append(f"{m['slot']} collided with existing TEL")

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
        if sk.csf_get(csf, f"CONTROLBAR:LibyaMissile{m['slot']}") != f"{m['slot']} {m['name']}":
            fails.append(f"{m['slot']} CSF name")
        if sk.csf_get(csf, f"CONTROLBAR:ToolTipLibyaMissile{m['slot']}") != player_tooltip(m):
            fails.append(f"{m['slot']} CSF tooltip")

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
        if any(x in tel_tex for x in ("Skr_TEL.tga", "Jpn_TEL.tga", "Sau_TEL.tga", "Uae_TEL.tga")):
            fails.append(f"{m['slot']} foreign truck")

        im = Image.open(io.BytesIO(art[m["tex_key"]])).convert("RGB")
        tel_flag = sk.region_mode(im, (110, 180, 420, 290))
        if not has_libya_flag(tel_flag):
            fails.append(f"{m['slot']} Libya flag {tel_flag}")
        if not sk.has_name_plate(im, (500, 190, 960, 280)):
            fails.append(f"{m['slot']} TEL name")
        body = sk.region_mode(im, (80, 410, 200, 560))
        top = max(body, key=body.get)
        allowed = {
            "yellow": {"yellow", "orange", "cream"},
            "orange": {"orange", "red", "yellow"},
            "white": {"white", "cream"},
            "red": {"red", "orange"},
            "muddy": {"muddy", "green", "other"},
            "green": {"green", "muddy"},
            "petrol": {"petrol", "blue", "green"},
            "gray": {"gray", "white", "dark"},
            "blue": {"blue", "petrol"},
            "cream": {"cream", "white", "yellow"},
        }
        if top not in allowed[m["expect"]] and top != m["expect"]:
            fails.append(f"{m['slot']} body {top} {body}")
        if m["km"] < 1000 or m["km"] > 4000:
            fails.append(f"{m['slot']} km")
        if m["kg"] < 400 or m["kg"] > 10000:
            fails.append(f"{m['slot']} kg")

    if len(DERIVED) != 10:
        fails.append(f"roster count {len(DERIVED)}")
    if len(seen_objects) != 10:
        fails.append(f"unique objects {len(seen_objects)}")
    return fails


def write_loose(builders: dict[str, str]) -> None:
    fac_dir = LOOSE / "Object/Specter/Libyan Armed Forces/Buildings"
    wheel_dir = LOOSE / "Object/Specter/Libyan Armed Forces/Wheeled"
    proj_dir = LOOSE / "Object/Specter/Libyan Armed Forces"
    wep_dir = LOOSE / "Weapon"
    for d in (fac_dir, wheel_dir, proj_dir, wep_dir):
        d.mkdir(parents=True, exist_ok=True)
    (fac_dir / "Libya_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    (wep_dir / "Weapon_Libya_Missiles.ini").write_text(weapon_file(DERIVED), encoding="utf-8")
    (LOOSE / "CommandButton_LibyaMissiles.ini").write_text(commandbutton_all(), encoding="utf-8")
    (LOOSE / "CommandSet_LibyaMissiles.ini").write_text(commandset_file(builders), encoding="utf-8")
    for m in DERIVED:
        (wheel_dir / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (proj_dir / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_UAE or SRC_DATA.stat().st_size != SIZE_DATA_UAE:
        raise SystemExit("DATA baseline is not SPECTER_UAE_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_UAE or SRC_ART.stat().st_size != SIZE_ART_UAE:
        raise SystemExit("ART baseline is not SPECTER_UAE_MISSILES_AJ")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art = sk.parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    flag = make_libya_flag()
    truck = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])), damaged=False)
    truckd = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCKD_DDS])), damaged=True)
    art[TRUCK_KEY] = sk.make_tga32(truck)
    art[TRUCKD_KEY] = sk.make_tga32(truckd)

    for m in DERIVED:
        skin = sk.make_skin(m["body"], m["nose"], m["name"], flag)
        art[m["tex_key"]] = sk.make_tga32(skin)
        art[m["tel_key"]] = make_lby_tel_w3d(src_art[TEL_W3D], False, m)
        art[m["teld_key"]] = make_lby_tel_w3d(src_art[TELD_W3D], True, m)
        art[m["projw_key"]] = sk.make_proj_w3d(src_art[PROJ_W3D], m)
        data[m["unit_key"]] = sk.to_crlf(unit_ini(m))
        data[m["proj_key"]] = sk.to_crlf(projectile_ini(m))

    data[LBY_FAC_KEY] = sk.to_crlf(factory_ini())
    data[LBY_WEP_KEY] = sk.to_crlf(weapon_file(DERIVED))
    data[LBY_CB_KEY] = sk.to_crlf(commandbutton_all())
    data[CSF_KEY] = sk.csf_upsert(src_data[CSF_KEY], csf_map())

    cs = src_data[CS_KEY].decode("latin1")
    builders = {}
    for name in BUILDERS:
        old = sk.last_block(cs, "CommandSet", name)
        new = with_libya_factory(old)
        builders[name] = new
        cs = sk.replace_last(cs, "CommandSet", name, new)
    if sk.last_block(cs, "CommandSet", "Libya_MissileFactoryCommandSet"):
        cs = sk.replace_last(cs, "CommandSet", "Libya_MissileFactoryCommandSet", factory_commandset())
    else:
        cs = cs.rstrip("\r\n") + "\r\n\r\n" + factory_commandset() + "\r\n"
    data[CS_KEY] = cs.encode("latin1")
    data[LBY_CS_KEY] = sk.to_crlf(commandset_file(builders))

    cb = src_data[CB_KEY].decode("latin1")
    if "CommandButton Command_ConstructLibya_MissileFactory" in cb:
        raise SystemExit("CommandButton.ini already had Libya factory")
    extra = commandbutton_all().replace("\n", "\r\n")
    data[CB_KEY] = (cb.rstrip("\r\n") + "\r\n\r\n" + extra + "\r\n").encode("latin1")

    wep = src_data[WEAPON_KEY].decode("latin1")
    if WEP_MARKER in wep or "Weapon Weapon_Libya_Fajr" in wep:
        raise SystemExit("Weapon.ini already had Libya A-J")
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
    (ext / "CommandSet.ini.Libya.txt").write_text(
        "\r\n\r\n".join(sk.last_block(packed_cs, "CommandSet", n) for n in BUILDERS)
        + "\r\n\r\n"
        + sk.last_block(packed_cs, "CommandSet", "Libya_MissileFactoryCommandSet")
        + "\r\n",
        encoding="utf-8",
    )
    (ext / "Weapon.ini.Libya.txt").write_text(weapon_file(DERIVED), encoding="utf-8")
    (ext / "Libya_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    for m in DERIVED:
        (ext / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (ext / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    preview = OUT / "PREVIEW"
    preview.mkdir()
    flag.save(preview / "LibyaFlag.png")
    truck.save(preview / "Lby_TEL.png")
    truckd.save(preview / "Lby_TELD.png")
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
    zip_path = ROOT / "patch/Release/SPECTER_LIBYA_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    inv = [
        "PRE-CHANGE LIBYA (packed last-wins, UAE A-J baseline):",
        "  No Libya_MissileFactory.",
        "  Dozer/Worker/VT72B constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  MIC on slot 6. Existing ShaheenTEL / AbabeelTEL / Alhussaien preserved.",
        "  Packed faction path: Libyan Armed Forces. Side=Libya.",
        "",
        "POST-CHANGE LIBYA:",
        "  Dedicated Libya_MissileFactory A-J + Rally/Sell.",
        "  Builder slot that held the isolated Iraq factory now builds the Libya factory.",
        "  Libya_Fajr is a new Libya object and does not replace SaudiArabia_Fajr.",
        "",
        *map_lines,
    ]
    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #634 s-uae-missiles-aj + PR #633 + #632 + #631 + #630 + #629",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "LIBYA_FACTORY_NEW=YES",
        "SHAHEEN_ABABEEL_ALHUSS_KEPT=YES",
        "UAE_AJ_UNCHANGED=YES",
        "SAUDI_AJ_UNCHANGED=YES",
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
        "KG_CEILING_USED=8000",
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
            "ZIP_FILE=SPECTER_LIBYA_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #634",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-libya-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-libya-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-libya-missiles-aj/SPECTER_LIBYA_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-libya-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-libya-missiles-aj",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Libya complete missile roster A-J on the accepted factory/fire path.\n"
        "New country factory replaces the isolated Iraq factory construct on Libya builders.\n"
        "Existing ShaheenTEL, AbabeelTEL, and Alhussaien are unchanged.\n"
        "UAE A-J, Saudi A-J, Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Libya missiles A-J\n\n"
        "- New Libya_MissileFactory. Rally/Sell retained.\n"
        "- Replaces isolated Iraq factory construct on Libya Dozer, Worker, and VT72B.\n"
        "- MIC, Abbas, Lgm30, ShaheenTEL, AbabeelTEL, and Alhussaien preserved.\n"
        "- Libya flag (red / black crescent-star / green) + exact names on dorsal UV bands.\n"
        "- Dedicated Lby_TEL ochre truck. Ten-color tube palette distinct from UAE and Saudi.\n"
        "- 5-minute clip reload on all ten PRIMARY weapons.\n"
        "- UAE A-J, Saudi A-J, Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n", encoding="utf-8")
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_LibyaMissiles.ini last-wins Libya builder + factory CommandSets.\n"
        "CommandButton_LibyaMissiles.ini last-wins construct + A-J.\n"
        "Weapon\\Weapon_Libya_Missiles.ini last-wins Weapon_Libya_* factory pair.\n"
        "Weapon_Libya.ini (Shaheen/Ababeel and other Libya weapons) is unchanged.\n"
        "Libya_Fajr is not SaudiArabia_Fajr.\n"
        "UAE, Saudi, Vietnam, Japan, South Korea, Iraq, and 9P117 packed definitions are unchanged.\n"
    )
    art_notes = [
        "LIBYA A-J ART MARKINGS (static inspection)",
        "",
        "Flag: red upper, black middle with white crescent and star, green lower.",
        "Not the former all-green Libyan flag. Not UAE / Saudi / Iraq flags.",
        "Dedicated Lby_TEL / Lby_TELD ochre truck. Not Irq_9P117 / Skr_TEL / Jpn_TEL / Sau_TEL / Uae_TEL.",
        "",
        "SLOT  NAME                     COLOR     FLAG    NAME PLATE",
    ]
    for m in DERIVED:
        art_notes.append(f"  {m['slot']}    {m['name']:<24} {m['expect']:<9} PASS    PASS")
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
