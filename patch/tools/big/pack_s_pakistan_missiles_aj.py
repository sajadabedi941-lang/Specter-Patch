#!/usr/bin/env python3
"""Implement Pakistan missile roster A-J on the India / South Africa path.

Baseline: packed SPECTER_INDIA_MISSILES_AJ (PR #639 + #638 + Syria/Libya/UAE/Saudi/VN/SK/Japan).

Pakistan has no missile factory. Dozer last-wins from CommandSet.ini; Worker and
VT72B last-win from CommandSet_Pakistan.ini. Slot 13 currently constructs the
isolated Sell-only Iraq_AlFahdMissileFactoryBuilding. Replace that slot with a
Pakistan-only factory via CommandSet.ini plus CommandSet_PakistanMissiles.ini
(sorts after CommandSet_Pakistan.ini, before ZZZZ). Keep MIC on slot 6.

Preserve existing Pakistan_ShaheenTEL, Pakistan_AbabeelTEL, Pakistan_Alhussaien,
PakistanVehicleNasr, PakistanVehicleShaheen, Pakistan_Babur_Projectile, and
SpecialPower PakistanSpecialPowerShaheenIII. Packed faction path is Pakistan
Armed Forces. Side=Pakistan.

Public Hatf families (Nasr, Abdali, Ghaznavi, Shaheen-I/II/III, Ghauri, Babur,
Ra'ad, Ababeel) inform names and roles. SPECTER km/kg/Acc/CHL are fictional
game values, not verified military specifications. Public range claims are
uncertain. Pakistan is a peer competitor to India, not a renamed India roster
and not an ICBM-class copy of Agni-V.

India A-J, South Africa A-J, Syria A-J, Libya A-J, UAE A-J, Saudi A-J,
Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 stay frozen.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Satellite last-wins: CommandSet_PakistanMissiles.ini,
CommandButton_PakistanMissiles.ini, Weapon\\Weapon_Pakistan_Missiles.ini.
Pakistan flag (white hoist + green field, crescent and star) + names on dorsal UV.
Dedicated Pak_TEL forest-olive truck. No RadarPriority. No rearm. No ZZZZ.
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
import pack_s_libya_missiles_aj as lby  # noqa: E402
import pack_s_syria_missiles_aj as syr  # noqa: E402
import pack_s_southafrica_missiles_aj as saf  # noqa: E402
import pack_s_india_missiles_aj as ind  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_INDIA_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_INDIA_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_PAKISTAN_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_IND = "7f2a18b1c57ab29d84ee50f9db2c1226f7b0b394f23d5c180546e903066e4108"
SIZE_DATA_IND = 368183171
SHA_ART_IND = "e9c0ecd7dad6becbcd91cd78a1bdda9e32ca7553a0b03fdf8f6c4f803bb3ba74"
SIZE_ART_IND = 1734860456

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

PAK_CB_KEY = r"Data\INI\CommandButton_PakistanMissiles.ini"
PAK_CS_KEY = r"Data\INI\CommandSet_PakistanMissiles.ini"
PAK_WEP_KEY = r"Data\INI\Weapon\Weapon_Pakistan_Missiles.ini"
PAK_FAC_KEY = (
    r"Data\INI\Object\Specter\Pakistan Armed Forces"
    r"\Buildings\Pakistan_MissileFactory.ini"
)
PAK_VT72B_KEY = r"Data\INI\Object\Specter\Pakistan Armed Forces\Tracked\VT72B.ini"
PAK_DOZER_KEY = r"Data\INI\Object\Specter\Pakistan Armed Forces\Tracked\Pakistan_Dozer.ini"
PAK_SHAHEEN_KEY = (
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Wheeled\Pakistan_ShaheenTEL.ini"
)
PAK_ABABEEL_KEY = (
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Wheeled\Pakistan_AbabeelTEL.ini"
)
PAK_ALHUSS_KEY = r"Data\INI\Object\Specter\Pakistan Armed Forces\Wheeled\AbbasLauncher.ini"
PAK_WEP_OLD_KEY = r"Data\INI\Weapon_Pakistan.ini"
PAK_MIC_KEY = r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_MIC.ini"
PAK_LGM_KEY = r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_Lgm30.ini"
PAK_CS_OLD_KEY = r"Data\INI\CommandSet_Pakistan.ini"
PAK_CB_OLD_KEY = r"Data\INI\CommandButton_Pakistan.ini"
PAK_ZZZ_CS = r"Data\INI\CommandSet_ZZZZ_AfricaPakistanSyria_AirExp.ini"
PAK_ZZZ_CB = r"Data\INI\CommandButton_ZZZZ_AfricaPakistanSyria_AirExp.ini"

TRUCK_TEX = "Pak_TEL.tga"
TRUCKD_TEX = "Pak_TELD.tga"
TRUCK_KEY = rf"Art\Textures\{TRUCK_TEX}"
TRUCKD_KEY = rf"Art\Textures\{TRUCKD_TEX}"

WEP_MARKER = (
    "; ===== Pakistan missiles A-J "
    "(Weapon.ini load path for Command_FireMainWeapon) ====="
)

BUILDERS = [
    "PakistanDozerCommandSet",
    "Pakistan_WorkerCommandSet",
    "Pakistan_VT72BCommandSet",
]

FOREST = (56, 88, 52)
EARTH = (48, 60, 40)
SOOT = (32, 36, 28)
NOSE_W = (236, 228, 210)
NOSE_R = (196, 16, 28)
NOSE_G = (0, 140, 64)

# Distinct slot-to-color and stats vs India. Forest-olive truck + green/white flag.
# SPECTER design values informed by public Hatf families, not claimed specs.
MISSILES = [
    {
        "slot": "A", "object": "Pakistan_Nasr", "name": "Nasr",
        "model": "Pak_Nasr", "modeld": "Pak_NasrD", "proj_model": "Pak_NasrM",
        "hier": b"PAK_NASRA", "hierd": b"PAK_NASRAD", "proj_hier": b"PAK_MSL_A",
        "tex": "Pak_NasrP.tga", "body": (222, 182, 28), "nose": NOSE_W,
        "expect": "yellow", "km": 1000, "kg": 400, "acc": 70, "stealth": 20,
        "rebuild": 16, "price": 800,
        "role": "Tactical SRBM analogue (Nasr/Hatf-IX; real ~60 km mapped to SPECTER floor)",
    },
    {
        "slot": "B", "object": "Pakistan_Abdali", "name": "Abdali",
        "model": "Pak_Abdali", "modeld": "Pak_AbdaliD", "proj_model": "Pak_AbdaliM",
        "hier": b"PAK_ABDLB", "hierd": b"PAK_ABDLBD", "proj_hier": b"PAK_MSL_B",
        "tex": "Pak_AbdaliP.tga", "body": (210, 108, 22), "nose": NOSE_W,
        "expect": "orange", "km": 1050, "kg": 400, "acc": 54, "stealth": 18,
        "rebuild": 18, "price": 900,
        "role": "SRBM analogue (Abdali/Hatf-II; modest Acc, cheap)",
    },
    {
        "slot": "C", "object": "Pakistan_Ghaznavi", "name": "Ghaznavi",
        "model": "Pak_Ghaznavi", "modeld": "Pak_GhaznaviD", "proj_model": "Pak_GhaznaviM",
        "hier": b"PAK_GHZNC", "hierd": b"PAK_GHZNCD", "proj_hier": b"PAK_MSL_C",
        "tex": "Pak_GhaznaviP.tga", "body": (88, 96, 42), "nose": NOSE_W,
        "expect": "muddy", "km": 1150, "kg": 500, "acc": 48, "stealth": 24,
        "rebuild": 22, "price": 1250,
        "role": "SRBM analogue (Ghaznavi/Hatf-III; heavier than Abdali)",
    },
    {
        "slot": "D", "object": "Pakistan_Shaheen1", "name": "Shaheen-I",
        "model": "Pak_Shaheen1", "modeld": "Pak_Shaheen1D", "proj_model": "Pak_Shaheen1M",
        "hier": b"PAK_SHN1D", "hierd": b"PAK_SHN1DD", "proj_hier": b"PAK_MSL_D",
        "tex": "Pak_Shaheen1P.tga", "body": (220, 200, 155), "nose": NOSE_R,
        "expect": "cream", "km": 1300, "kg": 700, "acc": 50, "stealth": 28,
        "rebuild": 28, "price": 2000,
        "role": "SRBM analogue (Shaheen-I/Hatf-IV; distinct from Pakistan_ShaheenTEL)",
    },
    {
        "slot": "E", "object": "Pakistan_Babur", "name": "Babur",
        "model": "Pak_Babur", "modeld": "Pak_BaburD", "proj_model": "Pak_BaburM",
        "hier": b"PAK_BABUE", "hierd": b"PAK_BABUED", "proj_hier": b"PAK_MSL_E",
        "tex": "Pak_BaburP.tga", "body": (8, 162, 56), "nose": NOSE_W,
        "expect": "green", "km": 1450, "kg": 450, "acc": 72, "stealth": 54,
        "rebuild": 34, "price": 3000,
        "role": "Land-attack cruise analogue (Babur/Hatf-VII; below India BrahMos Acc/CHL)",
    },
    {
        "slot": "F", "object": "Pakistan_Raad", "name": "Ra'ad",
        "model": "Pak_Raad", "modeld": "Pak_RaadD", "proj_model": "Pak_RaadM",
        "hier": b"PAK_RAADF", "hierd": b"PAK_RAADFD", "proj_hier": b"PAK_MSL_F",
        "tex": "Pak_RaadP.tga", "body": (10, 72, 84), "nose": NOSE_W,
        "expect": "petrol", "km": 1600, "kg": 400, "acc": 78, "stealth": 48,
        "rebuild": 36, "price": 2900,
        "role": "Cruise analogue (Ra'ad/Hatf-VIII ALCM heritage on TEL; SPECTER stretch)",
    },
    {
        "slot": "G", "object": "Pakistan_Ghauri", "name": "Ghauri",
        "model": "Pak_Ghauri", "modeld": "Pak_GhauriD", "proj_model": "Pak_GhauriM",
        "hier": b"PAK_GHRIG", "hierd": b"PAK_GHRIGD", "proj_hier": b"PAK_MSL_G",
        "tex": "Pak_GhauriP.tga", "body": (128, 128, 128), "nose": NOSE_R,
        "expect": "gray", "km": 1900, "kg": 1200, "acc": 36, "stealth": 30,
        "rebuild": 44, "price": 3300,
        "role": "Liquid MRBM analogue (Ghauri/Hatf-V; heavier and less precise than Agni-I)",
    },
    {
        "slot": "H", "object": "Pakistan_Shaheen2", "name": "Shaheen-II",
        "model": "Pak_Shaheen2", "modeld": "Pak_Shaheen2D", "proj_model": "Pak_Shaheen2M",
        "hier": b"PAK_SHN2H", "hierd": b"PAK_SHN2HD", "proj_hier": b"PAK_MSL_H",
        "tex": "Pak_Shaheen2P.tga", "body": (228, 224, 216), "nose": NOSE_G,
        "expect": "white", "km": 2200, "kg": 850, "acc": 54, "stealth": 34,
        "rebuild": 50, "price": 4100,
        "role": "Solid MRBM analogue (Shaheen-II/Hatf-VI; public ~1500-2000 km, SPECTER stretch)",
    },
    {
        "slot": "I", "object": "Pakistan_AbabeelMRV", "name": "Ababeel",
        "model": "Pak_AbabeelMRV", "modeld": "Pak_AbabeelMRVD", "proj_model": "Pak_AbabeelMRVM",
        "hier": b"PAK_ABBLI", "hierd": b"PAK_ABBLID", "proj_hier": b"PAK_MSL_I",
        "tex": "Pak_AbabeelMRVP.tga", "body": (168, 32, 28), "nose": NOSE_W,
        "expect": "red", "km": 2500, "kg": 800, "acc": 46, "stealth": 58,
        "rebuild": 58, "price": 5200,
        "role": "MIRV-class analogue (Ababeel; developmental/uncertain; distinct from Pakistan_AbabeelTEL)",
    },
    {
        "slot": "J", "object": "Pakistan_Shaheen3", "name": "Shaheen-III",
        "model": "Pak_Shaheen3", "modeld": "Pak_Shaheen3D", "proj_model": "Pak_Shaheen3M",
        "hier": b"PAK_SHN3J", "hierd": b"PAK_SHN3JD", "proj_hier": b"PAK_MSL_J",
        "tex": "Pak_Shaheen3P.tga", "body": (28, 68, 168), "nose": NOSE_W,
        "expect": "blue", "km": 3000, "kg": 1100, "acc": 56, "stealth": 38,
        "rebuild": 68, "price": 6200,
        "role": "Long MRBM analogue (Shaheen-III; public ~2750 km uncertain; below India Agni-V cap)",
    },
]

NAME_MAP = [
    "A Nasr new as Pakistan_Nasr (tactical; distinct from PakistanVehicleNasr)",
    "B Abdali new (Hatf-II SRBM analogue)",
    "C Ghaznavi new (Hatf-III SRBM analogue)",
    "D Shaheen-I new as Pakistan_Shaheen1 (distinct from Pakistan_ShaheenTEL / VehicleShaheen)",
    "E Babur new as Pakistan_Babur (cruise analogue; distinct from Pakistan_Babur_Projectile)",
    "F Ra'ad new as Pakistan_Raad (Hatf-VIII ALCM heritage; SPECTER TEL stretch)",
    "G Ghauri new (Hatf-V liquid MRBM analogue; heavy, modest Acc)",
    "H Shaheen-II new as Pakistan_Shaheen2",
    "I Ababeel new as Pakistan_AbabeelMRV (MIRV analogue; distinct from Pakistan_AbabeelTEL)",
    "J Shaheen-III new as Pakistan_Shaheen3 (distinct from SpecialPower PakistanSpecialPowerShaheenIII)",
]

FROZEN_DATA = list(ind.FROZEN_DATA) + [
    ind.IND_FAC_KEY, ind.IND_CB_KEY, ind.IND_CS_KEY, ind.IND_WEP_KEY,
    PAK_VT72B_KEY, PAK_DOZER_KEY, PAK_SHAHEEN_KEY, PAK_ABABEEL_KEY,
    PAK_ALHUSS_KEY, PAK_WEP_OLD_KEY, PAK_MIC_KEY, PAK_LGM_KEY,
    PAK_CS_OLD_KEY, PAK_CB_OLD_KEY, PAK_ZZZ_CS, PAK_ZZZ_CB,
]
FROZEN_DATA += [m["unit_key"] for m in ind.DERIVED]
FROZEN_DATA += [m["proj_key"] for m in ind.DERIVED]

FROZEN_ART = list(ind.FROZEN_ART) + [
    ind.TRUCK_KEY, ind.TRUCKD_KEY,
    r"Art\Textures\Ind_PrahaarP.tga", r"Art\W3D\Ind_Prahaar.W3D",
]
FROZEN_ART += [m["tex_key"] for m in ind.DERIVED]
FROZEN_ART += [m["tel_key"] for m in ind.DERIVED]
FROZEN_ART += [m["teld_key"] for m in ind.DERIVED]
FROZEN_ART += [m["projw_key"] for m in ind.DERIVED]

for _m in MISSILES:
    assert len(_m["hier"]) == 9 and len(_m["hierd"]) == 10 and len(_m["proj_hier"]) == 9
    assert 1000 <= _m["km"] <= 4000 and 400 <= _m["kg"] <= 10000


def derived(m: dict) -> dict:
    d = sk.derived({**m, "min_range": sk.MOTHER_MIN_RANGE})
    d["button"] = f"CB_PAKISTAN_MISSILE_{m['slot']}"
    d["unit_key"] = (
        r"Data\INI\Object\Specter\Pakistan Armed Forces"
        rf"\Wheeled\{m['object']}.ini"
    )
    d["proj_key"] = (
        r"Data\INI\Object\Specter\Pakistan Armed Forces"
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


def make_pakistan_flag() -> Image.Image:
    """Pakistan flag: white hoist stripe, green fly, white crescent and star."""
    w, h = 900, 600
    green = (0, 130, 70, 255)
    white = (255, 255, 255, 255)
    im = Image.new("RGBA", (w, h), green)
    draw = ImageDraw.Draw(im)
    hoist = int(0.25 * w)
    draw.rectangle([0, 0, hoist, h], fill=white)
    cx = hoist + (w - hoist) * 0.48
    cy = h * 0.50
    r_out = h * 0.22
    r_in = h * 0.17
    draw.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill=white)
    ox = cx + h * 0.055
    draw.ellipse([ox - r_in, cy - r_in, ox + r_in, cy + r_in], fill=green)
    star_cx = cx + h * 0.18
    star_cy = cy - h * 0.04
    _star(draw, star_cx, star_cy, h * 0.085, h * 0.034, white)
    return im


def has_pakistan_flag(counts: dict[str, int]) -> bool:
    greenish = counts.get("green", 0) + counts.get("muddy", 0)
    return counts.get("white", 0) >= 4 and greenish >= 8


def recolor_truck(src: Image.Image, damaged: bool = False) -> Image.Image:
    """Map Iraqi tan sheet to Pakistan forest olive / earth / soot."""
    im = src.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            avg = (r + g + b) / 3.0
            sat = max(r, g, b) - min(r, g, b)
            if avg < 55 and sat < 35:
                px[x, y] = (max(0, int(r * 0.28)), max(0, int(g * 0.32)), max(0, int(b * 0.24)), a)
                continue
            if sat > 70 and avg > 70:
                base = FOREST
                t = 0.92
            elif avg < 100:
                base = EARTH
                t = max(0.70, min(1.15, avg / 90.0))
            else:
                base = FOREST
                t = max(0.55, min(1.25, avg / 130.0))
            nr = min(255, int(base[0] * t))
            ng = min(255, int(base[1] * t))
            nb = min(255, int(base[2] * t))
            if damaged:
                nr, ng, nb = int(nr * 0.70), int(ng * 0.72), int(nb * 0.58)
            px[x, y] = (nr, ng, nb, a)
    return im


def make_pak_tel_w3d(src: bytes, damaged: bool, m: dict) -> bytes:
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
        .replace("South Korea", "Pakistan")
        .replace("Side = SouthKorea", "Side = Pakistan")
        .replace(
            "Skr_TEL / Skr_TELD (not Irq_9P117 / Jpn_TEL)",
            "Pak_TEL / Pak_TELD (not Irq_9P117 / Jpn_TEL / Skr_TEL / Sau_TEL / Uae_TEL / Lby_TEL / Syr_TEL / Saf_TEL / Ind_TEL)",
        )
    )


def projectile_ini(m: dict) -> str:
    return sk.projectile_ini(m).replace("South Korea", "Pakistan")


def weapon_file(missiles: list[dict]) -> str:
    head = (
        WEP_MARKER + "\n"
        "; 9P117 scale. Dedicated Pakistan A-J. Distinct from India/SA/Syria/Libya/UAE/Saudi/Vietnam/Japan/SK/Iraq.\n"
        "; Hatf-family informed mix. Shaheen-III below India Agni-V. Ababeel is MIRV analogue, not ICBM.\n"
        "; ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000 (PR #629).\n"
        "; Death HACK is a separate path and is not folded into PrimaryDamage.\n"
        "; Acc/CHL columns are design labels mapped to ScatterRadius / MaxHealth.\n"
    )
    body = sk.weapon_blocks(missiles)
    pairs = body.split("\n\n", 1)[1] if "\n\n" in body else body
    return head + "\n" + pairs


def factory_ini() -> str:
    text = sk.factory_ini()
    text = text.replace("; South Korea missile factory.", "; Pakistan missile factory.")
    text = text.replace(
        "with a SouthKorea-only CommandSet (A-J).",
        "with a Pakistan-only CommandSet (A-J).",
    )
    text = text.replace("Object SouthKorea_MissileFactory", "Object Pakistan_MissileFactory")
    text = text.replace(
        "DisplayName      = OBJECT:SouthKoreaMissileFactory",
        "DisplayName      = OBJECT:PakistanMissileFactory",
    )
    text = text.replace("Side             = SouthKorea", "Side             = Pakistan")
    text = text.replace(
        "CommandSet       = SouthKorea_MissileFactoryCommandSet",
        "CommandSet       = Pakistan_MissileFactoryCommandSet",
    )
    return text


def factory_commandset() -> str:
    slots = "\r\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(DERIVED, start=1))
    return (
        "CommandSet Pakistan_MissileFactoryCommandSet\r\n"
        f"{slots}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def with_pakistan_factory(block: str) -> str:
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in block:
        raise SystemExit(f"expected isolated Iraq factory in:\n{block}")
    if "Command_ConstructPakistan_MissileFactory" in block:
        raise SystemExit("Pakistan factory already present on builder")
    return block.replace(
        "Command_ConstructIraq_AlFahdMissileFactoryBuilding",
        "Command_ConstructPakistan_MissileFactory",
    )


def commandbutton_all() -> str:
    lines = [
        "; Pakistan missiles A-J production buttons and factory construct button.",
        "; Shared specter_missile_* cameos. Unique Object bindings.",
        "",
        "CommandButton Command_ConstructPakistan_MissileFactory",
        "  Command          = DOZER_CONSTRUCT",
        "  Object           = Pakistan_MissileFactory",
        "  TextLabel        = CONTROLBAR:ConstructPakistanMissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel    = CONTROLBAR:ToolTipPakistanMissileFactory",
        "End",
        "",
    ]
    for m in DERIVED:
        lines.extend(
            [
                f"CommandButton {m['button']}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {m['object']}",
                f"  TextLabel     = CONTROLBAR:PakistanMissile{m['slot']}",
                f"  ButtonImage   = {m['cameo']}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTipPakistanMissile{m['slot']}",
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
        f"{m['role']}\n"
        f"Range: {m['km']} km\n"
        f"Warhead: {m['kg']} kg\n"
        f"Accuracy: {m['acc']}/100 (impact scatter, not a hit %)\n"
        f"Radar evasion: {m['stealth']}/100 (interceptor toughness, not stealth)\n"
        f"Build Time: {m['rebuild']} sec\n"
        f"Price: ${m['price']}\n"
        f"SPECTER design values, not verified specs"
    )


def csf_map() -> dict[str, str]:
    mapping = {
        "OBJECT:PakistanMissileFactory": "Missile Factory",
        "CONTROLBAR:ConstructPakistanMissileFactory": "Missile Factory",
        "CONTROLBAR:ToolTipPakistanMissileFactory": (
            "Missile Factory\nProduces Pakistan missiles A-J\nPrice: $1800"
        ),
    }
    for m in DERIVED:
        mapping[f"OBJECT:{m['object']}"] = m["name"]
        mapping[f"CONTROLBAR:PakistanMissile{m['slot']}"] = f"{m['slot']} {m['name']}"
        mapping[f"CONTROLBAR:ToolTipPakistanMissile{m['slot']}"] = player_tooltip(m)
    return mapping


def mapping_report() -> list[str]:
    lines = [
        "NAME MAPPING:",
        *[f"  {row}" for row in NAME_MAP],
        "",
        "EXISTING PAKISTAN MISSILE OBJECTS PRESERVED (not factory A-J):",
        "  Pakistan_ShaheenTEL / Pakistan_Weapon_Shaheen / PakistanVehicleShaheen",
        "  Pakistan_AbabeelTEL / Pakistan_Weapon_Ababeel",
        "  Pakistan_Alhussaien (AbbasLauncher.ini)",
        "  Pakistan_Babur_Projectile / Pakistan_Babur_Cruise_Projectile",
        "  PakistanVehicleNasr",
        "  Pakistan_Lgm30 unchanged.",
        "  SpecialPower PakistanSpecialPowerShaheenIII unchanged.",
        "",
        "FACTORY CONSTRUCT:",
        "  Pre-change Dozer (CommandSet.ini) and Worker/VT72B (CommandSet_Pakistan.ini)",
        "  constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  Post-change CommandSet.ini + CommandSet_PakistanMissiles.ini last-win the Pakistan factory.",
        "  CommandSet_Pakistan.ini is frozen. MIC remains on slot 6.",
        "",
        "REAL-WORLD vs GAMEPLAY:",
        "  Public sources describe Pakistani Hatf families: Nasr, Abdali, Ghaznavi,",
        "  Shaheen-I/II/III, Ghauri, Babur, Ra'ad, and Ababeel (MIRV developmental).",
        "  Reported ranges are often uncertain (Shaheen-III commonly ~2750 km; Ababeel ~2200 km).",
        "  SPECTER floor is 1000 km and ceiling 4000 km. Tactical classes sit on the floor.",
        "  Pakistan J Shaheen-III is 3000 km / 1100 kg, below India Agni-V 4000/1800.",
        "  Values below are SPECTER design, not verified military specifications.",
        "",
        "PUBLIC BACKGROUND (not in-game specs):",
        "  CSIS Missile Threat, Missiles of Pakistan (updated 2022):",
        "    https://missilethreat.csis.org/country/pakistan/",
        "  NTI, Pakistani ballistic and cruise missile models:",
        "    https://www.nti.org/analysis/articles/pakistani-ballistic-and-cruise-missile-models/",
        "  NTI, Nuclear Disarmament Pakistan:",
        "    https://www.nti.org/analysis/articles/pakistan-nuclear-disarmament/",
        "  Bulletin of the Atomic Scientists, Pakistan nuclear weapons 2025:",
        "    https://www.tandfonline.com/doi/full/10.1080/00963402.2025.2543685",
        "  Public status differs by family (Abdali/Ghaznavi/Shaheen-I/II/Ghauri/Nasr/Babur-1A",
        "  commonly described as operational; Shaheen-III/Ababeel/Ra'ad often developmental).",
        "  Reported ranges (Nasr ~60-70 km, Shaheen-III ~2750 km, Ababeel ~2200 km) are uncertain.",
        "  SPECTER values below are fictional game design, not those public figures.",
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
    lines.extend(["", "MISSION ROLES:"])
    for m in DERIVED:
        lines.append(f"  {m['slot']} {m['name']}: {m['role']}")
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
    sat_cs = data[PAK_CS_KEY].decode("latin1")
    old_pak_cs = data[PAK_CS_OLD_KEY].decode("latin1")

    if "ZZZZ" in PAK_CB_KEY or "ZZZZ" in PAK_CS_KEY or "ZZZZ" in PAK_WEP_KEY:
        fails.append("ZZZZ shortcut")
    if PAK_CS_KEY >= r"Data\INI\CommandSet_ZZZZ":
        fails.append("Pakistan satellite sorts into ZZZZ")
    if PAK_CS_KEY <= CS_KEY:
        fails.append("Pakistan satellite sorts before CommandSet.ini")
    if PAK_CS_KEY <= PAK_CS_OLD_KEY:
        fails.append("Pakistan missile satellite sorts before CommandSet_Pakistan.ini")

    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in old_pak_cs:
        fails.append("frozen CommandSet_Pakistan.ini lost Iraq factory (should stay frozen)")
    if "Command_ConstructPakistan_MissileFactory" in old_pak_cs:
        fails.append("CommandSet_Pakistan.ini was mutated with new factory")

    for frozen_cs in (
        "Iraq_AlFahdMissileFactoryCommandSet",
        "Vietnam_MissileFactoryCommandSet",
        "Japan_MissileFactoryCommandSet",
        "SouthKorea_MissileFactoryCommandSet",
        "SaudiArabia_MissileFactoryCommandSet",
        "UAE_MissileFactoryCommandSet",
        "Libya_MissileFactoryCommandSet",
        "Syria_MissileFactoryCommandSet",
        "SouthAfrica_MissileFactoryCommandSet",
        "India_MissileFactoryCommandSet",
        "IndiaDozerCommandSet",
        "India_WorkerCommandSet",
        "India_VT72BCommandSet",
    ):
        if sk.last_block(cs_text, "CommandSet", frozen_cs) != sk.last_block(
            src_cs, "CommandSet", frozen_cs
        ):
            fails.append(f"{frozen_cs} mutated in CommandSet.ini")

    for name in BUILDERS:
        new_b = sk.last_block(cs_text, "CommandSet", name)
        if "Command_ConstructPakistan_MissileFactory" not in new_b:
            fails.append(f"{name} catalog missing Pakistan factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in new_b:
            fails.append(f"{name} catalog still has isolated Iraq factory")
        if "Command_ConstructPakistan_MIC" not in new_b:
            fails.append(f"{name} lost MIC")
        if name == "PakistanDozerCommandSet" and "Command_ConstructPakistan_Lgm30" not in new_b:
            fails.append("Dozer lost Lgm30")
        if name != "PakistanDozerCommandSet" and "Command_ConstructPakistan_Abbas" not in new_b:
            fails.append(f"{name} lost Abbas")
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", name)
        if "Command_ConstructPakistan_MissileFactory" not in lw:
            fails.append(f"last-wins {name} from {_k} missing Pakistan factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in lw:
            fails.append(f"last-wins {name} still Iraq factory")
        if "Command_ConstructPakistan_MIC" not in lw:
            fails.append(f"last-wins {name} lost MIC")
        if name not in sat_cs:
            fails.append(f"satellite missing {name}")

    fac = sk.last_block(cs_text, "CommandSet", "Pakistan_MissileFactoryCommandSet")
    if not fac:
        fails.append("CommandSet.ini missing Pakistan factory roster")
    slots = re.findall(r"CB_PAKISTAN_MISSILE_([A-Z])", fac)
    if slots != list("ABCDEFGHIJ"):
        fails.append(f"factory slots {slots} != A-J")
    if "Command_Sell" not in fac or "Command_SetRallyPoint" not in fac:
        fails.append("factory missing Rally/Sell")
    if any(
        tag in fac
        for tag in (
            "CB_VIETNAM_", "CB_JAPAN_", "CB_SOUTHKOREA_", "CB_SAUDIARABIA_",
            "CB_UAE_", "CB_LIBYA_", "CB_SYRIA_", "CB_SOUTHAFRICA_", "CB_INDIA_",
        )
    ):
        fails.append("factory mixed foreign buttons")

    construct = sk.last_block(cb_text, "CommandButton", "Command_ConstructPakistan_MissileFactory")
    if sk.field(construct, "Object") != "Pakistan_MissileFactory":
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
        ("Button_MissileFactory", "Command_ConstructLibya_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructSyria_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructSouthAfrica_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructIndia_MissileFactory"),
    ):
        if sk.field(sk.last_block(cb_text, "CommandButton", btn), "ButtonImage") != img:
            fails.append(f"{btn} image lost")
        if sk.last_block(cb_text, "CommandButton", btn) != sk.last_block(src_cb, "CommandButton", btn):
            fails.append(f"{btn} mutated")

    fac_obj = sk.last_block(data[PAK_FAC_KEY].decode("latin1"), "Object", "Pakistan_MissileFactory")
    if sk.field(fac_obj, "Side") != "Pakistan":
        fails.append("factory Side")
    if sk.field(fac_obj, "CommandSet") != "Pakistan_MissileFactoryCommandSet":
        fails.append("factory object CommandSet")
    if "SouthKorea_SupplyCenter" not in fac_obj:
        fails.append("factory lost SouthKorea_SupplyCenter prereq")
    if "Pakistan_SupplyCenter" not in fac_obj:
        fails.append("factory missing Pakistan_SupplyCenter prereq")

    if sk.last_block(wep_text, "Weapon", "Weapon_Vietnam_VCM01") != sk.last_block(
        src_wep, "Weapon", "Weapon_Vietnam_VCM01"
    ):
        fails.append("Vietnam VCM01 weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Japan_Tenrai") != sk.last_block(
        src_wep, "Weapon", "Weapon_Japan_Tenrai"
    ):
        fails.append("Japan Tenrai mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_India_Prahaar") != sk.last_block(
        src_wep, "Weapon", "Weapon_India_Prahaar"
    ):
        fails.append("India Prahaar weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_SouthAfrica_Mokopa") != sk.last_block(
        src_wep, "Weapon", "Weapon_SouthAfrica_Mokopa"
    ):
        fails.append("South Africa Mokopa weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Syria_Luna") != sk.last_block(
        src_wep, "Weapon", "Weapon_Syria_Luna"
    ):
        fails.append("Syria Luna weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Libya_Fajr") != sk.last_block(
        src_wep, "Weapon", "Weapon_Libya_Fajr"
    ):
        fails.append("Libya Fajr weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Iraq_AlFahd500") != sk.last_block(
        src_wep, "Weapon", "Weapon_Iraq_AlFahd500"
    ):
        fails.append("AlFahd weapon mutated")
    if sk.last_block(data[PAK_WEP_OLD_KEY].decode("latin1"), "Weapon", "Pakistan_Weapon_Shaheen") != sk.last_block(
        src_data[PAK_WEP_OLD_KEY].decode("latin1"), "Weapon", "Pakistan_Weapon_Shaheen"
    ):
        fails.append("Pakistan Shaheen weapon mutated")

    if sk.illegal_floats(wep_text):
        fails.append(f"illegal floats {sk.illegal_floats(wep_text)}")

    r11 = sk.last_block(data[sk.R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB")
    if sk.field(r11, "BuildCost") != "1200":
        fails.append("9P117 BuildCost")

    ind_fac = sk.last_block(data[ind.IND_FAC_KEY].decode("latin1"), "Object", "India_MissileFactory")
    if sk.field(ind_fac, "Side") != "India":
        fails.append("India factory Side mutated")
    saf_fac = sk.last_block(data[saf.SAF_FAC_KEY].decode("latin1"), "Object", "SouthAfrica_MissileFactory")
    if sk.field(saf_fac, "Side") != "SouthAfrica":
        fails.append("South Africa factory Side mutated")
    syr_fac = sk.last_block(data[syr.SYR_FAC_KEY].decode("latin1"), "Object", "Syria_MissileFactory")
    if sk.field(syr_fac, "Side") != "Syria":
        fails.append("Syria factory Side mutated")
    lby_fac = sk.last_block(data[lby.LBY_FAC_KEY].decode("latin1"), "Object", "Libya_MissileFactory")
    if sk.field(lby_fac, "Side") != "Libya":
        fails.append("Libya factory Side mutated")
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
    ind_avg = Image.open(io.BytesIO(src_art[ind.TRUCK_KEY])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == ind_avg:
        fails.append("truck still India saffron-olive")
    saf_avg = Image.open(io.BytesIO(src_art[saf.TRUCK_KEY])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == saf_avg:
        fails.append("truck still South Africa veld")
    syr_avg = Image.open(io.BytesIO(src_art[syr.TRUCK_KEY])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == syr_avg:
        fails.append("truck still Syria drab")

    wep_sat = data[PAK_WEP_KEY].decode("latin1")
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
        if sk.field(unit, "Side") != "Pakistan":
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
        if "Pakistan_ShaheenTEL" in unit or "Pakistan_AbabeelTEL" in unit or "India_Prahaar" in unit:
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
        if sk.csf_get(csf, f"CONTROLBAR:PakistanMissile{m['slot']}") != f"{m['slot']} {m['name']}":
            fails.append(f"{m['slot']} CSF name")
        if sk.csf_get(csf, f"CONTROLBAR:ToolTipPakistanMissile{m['slot']}") != player_tooltip(m):
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
        if any(
            x in tel_tex
            for x in (
                "Skr_TEL.tga", "Jpn_TEL.tga", "Sau_TEL.tga", "Uae_TEL.tga",
                "Lby_TEL.tga", "Syr_TEL.tga", "Saf_TEL.tga", "Ind_TEL.tga",
            )
        ):
            fails.append(f"{m['slot']} foreign truck")

        im = Image.open(io.BytesIO(art[m["tex_key"]])).convert("RGB")
        tel_flag = sk.region_mode(im, (110, 180, 420, 290))
        if not has_pakistan_flag(tel_flag):
            fails.append(f"{m['slot']} Pakistan flag {tel_flag}")
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
    fac_dir = LOOSE / "Object/Specter/Pakistan Armed Forces/Buildings"
    wheel_dir = LOOSE / "Object/Specter/Pakistan Armed Forces/Wheeled"
    proj_dir = LOOSE / "Object/Specter/Pakistan Armed Forces"
    wep_dir = LOOSE / "Weapon"
    for d in (fac_dir, wheel_dir, proj_dir, wep_dir):
        d.mkdir(parents=True, exist_ok=True)
    (fac_dir / "Pakistan_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    (wep_dir / "Weapon_Pakistan_Missiles.ini").write_text(weapon_file(DERIVED), encoding="utf-8")
    (LOOSE / "CommandButton_PakistanMissiles.ini").write_text(commandbutton_all(), encoding="utf-8")
    (LOOSE / "CommandSet_PakistanMissiles.ini").write_text(commandset_file(builders), encoding="utf-8")
    for m in DERIVED:
        (wheel_dir / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (proj_dir / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_IND or SRC_DATA.stat().st_size != SIZE_DATA_IND:
        raise SystemExit("DATA baseline is not SPECTER_INDIA_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_IND or SRC_ART.stat().st_size != SIZE_ART_IND:
        raise SystemExit("ART baseline is not SPECTER_INDIA_MISSILES_AJ")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art = sk.parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    flag = make_pakistan_flag()
    truck = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])), damaged=False)
    truckd = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCKD_DDS])), damaged=True)
    art[TRUCK_KEY] = sk.make_tga32(truck)
    art[TRUCKD_KEY] = sk.make_tga32(truckd)

    for m in DERIVED:
        skin = sk.make_skin(m["body"], m["nose"], m["name"], flag)
        art[m["tex_key"]] = sk.make_tga32(skin)
        art[m["tel_key"]] = make_pak_tel_w3d(src_art[TEL_W3D], False, m)
        art[m["teld_key"]] = make_pak_tel_w3d(src_art[TELD_W3D], True, m)
        art[m["projw_key"]] = sk.make_proj_w3d(src_art[PROJ_W3D], m)
        data[m["unit_key"]] = sk.to_crlf(unit_ini(m))
        data[m["proj_key"]] = sk.to_crlf(projectile_ini(m))

    data[PAK_FAC_KEY] = sk.to_crlf(factory_ini())
    data[PAK_WEP_KEY] = sk.to_crlf(weapon_file(DERIVED))
    data[PAK_CB_KEY] = sk.to_crlf(commandbutton_all())
    data[CSF_KEY] = sk.csf_upsert(src_data[CSF_KEY], csf_map())

    cs = src_data[CS_KEY].decode("latin1")
    pak_old = src_data[PAK_CS_OLD_KEY].decode("latin1")
    builders = {}
    for name in BUILDERS:
        old = sk.last_block(cs, "CommandSet", name) or sk.last_block(pak_old, "CommandSet", name)
        new = with_pakistan_factory(old)
        builders[name] = new
        if sk.last_block(cs, "CommandSet", name):
            cs = sk.replace_last(cs, "CommandSet", name, new)
        else:
            cs = cs.rstrip("\r\n") + "\r\n\r\n" + new + "\r\n"
    if sk.last_block(cs, "CommandSet", "Pakistan_MissileFactoryCommandSet"):
        cs = sk.replace_last(cs, "CommandSet", "Pakistan_MissileFactoryCommandSet", factory_commandset())
    else:
        cs = cs.rstrip("\r\n") + "\r\n\r\n" + factory_commandset() + "\r\n"
    data[CS_KEY] = cs.encode("latin1")
    data[PAK_CS_KEY] = sk.to_crlf(commandset_file(builders))

    cb = src_data[CB_KEY].decode("latin1")
    if "CommandButton Command_ConstructPakistan_MissileFactory" in cb:
        raise SystemExit("CommandButton.ini already had Pakistan factory")
    extra = commandbutton_all().replace("\n", "\r\n")
    data[CB_KEY] = (cb.rstrip("\r\n") + "\r\n\r\n" + extra + "\r\n").encode("latin1")

    wep = src_data[WEAPON_KEY].decode("latin1")
    if WEP_MARKER in wep or "Weapon Weapon_Pakistan_Nasr" in wep:
        raise SystemExit("Weapon.ini already had Pakistan A-J")
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
    (ext / "CommandSet.ini.Pakistan.txt").write_text(
        "\r\n\r\n".join(sk.last_block(packed_cs, "CommandSet", n) for n in BUILDERS)
        + "\r\n\r\n"
        + sk.last_block(packed_cs, "CommandSet", "Pakistan_MissileFactoryCommandSet")
        + "\r\n",
        encoding="utf-8",
    )
    (ext / "Weapon.ini.Pakistan.txt").write_text(weapon_file(DERIVED), encoding="utf-8")
    (ext / "Pakistan_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    for m in DERIVED:
        (ext / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (ext / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    preview = OUT / "PREVIEW"
    preview.mkdir()
    flag.save(preview / "PakistanFlag.png")
    truck.save(preview / "Pak_TEL.png")
    truckd.save(preview / "Pak_TELD.png")
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
    zip_path = ROOT / "patch/Release/SPECTER_PAKISTAN_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    inv = [
        "PRE-CHANGE PAKISTAN (packed last-wins, India A-J baseline):",
        "  No Pakistan_MissileFactory.",
        "  Dozer last-wins CommandSet.ini; Worker/VT72B last-win CommandSet_Pakistan.ini.",
        "  Slot 13 constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  MIC on slot 6. Existing ShaheenTEL / AbabeelTEL / Alhussaien / Lgm30 preserved.",
        "  Packed faction path: Pakistan Armed Forces. Side=Pakistan.",
        "",
        "POST-CHANGE PAKISTAN:",
        "  Dedicated Pakistan_MissileFactory A-J + Rally/Sell.",
        "  CommandSet_PakistanMissiles.ini last-wins Worker/VT72B over CommandSet_Pakistan.ini.",
        "  Hatf-informed mix 1000-3000 km / 400-1200 kg. Not an India reskin.",
        "",
        "COUNTRY BALANCE (inspected packed / accepted factory A-J, not runtime):",
        "  India J Agni-V 4000 km / 1800 kg Acc 58. Pakistan J Shaheen-III 3000/1100 Acc 56.",
        "  India BrahMos Acc 84 CHL 62. Pakistan Babur Acc 72 CHL 54; Ra'ad Acc 78 CHL 48.",
        "  Pakistan Ghauri 1900/1200 Acc 36 vs India Agni-I 1900/900 Acc 50 (heavier, less precise).",
        "  Ababeel MIRV analogue is Pakistan's unique CHL outlier (58), range 2500 km not max.",
        "  Nasr is cheaper/faster than India Prahaar. Syria J 2200/1500; SA J 2400/1200.",
        "  Libya J 3900/8000. USA/EU strategic systems remain on other production paths.",
        "",
        *map_lines,
    ]
    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #639 s-india-missiles-aj + PR #638 + #637 + #636 + #635 + #634 + #633 + #632 + #631 + #630 + #629",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "PAKISTAN_FACTORY_NEW=YES",
        "SHAHEEN_ABABEEL_ALHUSS_LGM30_KEPT=YES",
        "INDIA_AJ_UNCHANGED=YES",
        "SOUTHAFRICA_AJ_UNCHANGED=YES",
        "SYRIA_AJ_UNCHANGED=YES",
        "LIBYA_AJ_UNCHANGED=YES",
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
        "KM_CEILING_USED=3000",
        "KG_FLOOR=400",
        "KG_CEILING_USED=1200",
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
            "ZIP_FILE=SPECTER_PAKISTAN_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #639",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-pakistan-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-pakistan-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-pakistan-missiles-aj/SPECTER_PAKISTAN_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-pakistan-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-pakistan-missiles-aj",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Pakistan complete missile roster A-J on the accepted factory/fire path.\n"
        "New country factory replaces the isolated Iraq factory construct on Pakistan builders.\n"
        "Existing ShaheenTEL, AbabeelTEL, Alhussaien, Lgm30, VehicleNasr, and Shaheen-III special power are unchanged.\n"
        "Hatf-informed mix 1000-3000 km / 400-1200 kg. Peer to India, not an India reskin or Agni-V copy.\n"
        "India A-J, South Africa A-J, Syria A-J, Libya A-J, UAE A-J, Saudi A-J, Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Pakistan missiles A-J\n\n"
        "- New Pakistan_MissileFactory. Rally/Sell retained.\n"
        "- Replaces isolated Iraq factory construct on Pakistan Dozer, Worker, and VT72B.\n"
        "- CommandSet_PakistanMissiles.ini last-wins Worker/VT72B over frozen CommandSet_Pakistan.ini.\n"
        "- MIC, Abbas, Lgm30, ShaheenTEL, AbabeelTEL, Alhussaien, VehicleNasr, Shaheen-III SP preserved.\n"
        "- Pakistan flag (white hoist, green field, crescent and star) + exact names on dorsal UV.\n"
        "- Dedicated Pak_TEL forest-olive truck. Ten-color tube palette distinct from India/SA/Syria.\n"
        "- Shaheen-III cap 3000 km / 1100 kg. Ababeel MIRV analogue. Not India Agni-V 4000/1800.\n"
        "- 5-minute clip reload on all ten PRIMARY weapons.\n"
        "- India A-J and all previously accepted country rosters unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n", encoding="utf-8")
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_PakistanMissiles.ini last-wins Pakistan builder + factory CommandSets over CommandSet_Pakistan.ini.\n"
        "CommandButton_PakistanMissiles.ini last-wins construct + A-J.\n"
        "Weapon\\Weapon_Pakistan_Missiles.ini last-wins Weapon_Pakistan_* factory pair.\n"
        "Weapon_Pakistan.ini and CommandSet_Pakistan.ini are frozen.\n"
        "Pakistan_Nasr/Abdali/Ghaznavi/Shaheen1/Babur/Raad/Ghauri/Shaheen2/AbabeelMRV/Shaheen3 are new objects.\n"
        "Pakistan_ShaheenTEL, Pakistan_AbabeelTEL, PakistanVehicleNasr, Pakistan_Babur_Projectile, and Shaheen-III special power are unchanged.\n"
        "India, South Africa, Syria, Libya, UAE, Saudi, Vietnam, Japan, South Korea, Iraq, and 9P117 packed definitions are unchanged.\n"
    )
    art_notes = [
        "PAKISTAN A-J ART MARKINGS (static inspection)",
        "",
        "Flag: white hoist stripe, green fly, white crescent and star.",
        "SPECTER Side=Pakistan / Pakistan Armed Forces identity. Not India / SA / Syria flags.",
        "Dedicated Pak_TEL / Pak_TELD forest-olive truck. Not Ind_TEL / Saf_TEL / Syr_TEL / Irq_9P117.",
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
