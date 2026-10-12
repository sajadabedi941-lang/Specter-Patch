#!/usr/bin/env python3
"""Implement Syria missile roster A-J on the Libya / UAE / Saudi path.

Baseline: packed SPECTER_LIBYA_ACC_DESC (PR #636 + #635 + UAE/Saudi/VN/SK/Japan).

Syria has no missile factory. Dozer / Worker / VT72B slot 13 currently constructs
the isolated Sell-only Iraq_AlFahdMissileFactoryBuilding. Replace that slot with a
Syria-only factory. Keep MIC on slot 6.

Preserve existing Syria_ShaheenTEL, Syria_AbabeelTEL, and Syria_Alhussaien.
Packed faction path is Syrian Armed Forces. Side=Syria.

Roster is a regional profile, not a reskin of Libya/UAE/Saudi A-J:
tactical rockets and SRBMs, then one coastal/cruise analogue, then a
conservative high-end cap well below US/EU strategic systems and below
Libya/UAE/Saudi J-class range and payload.

Libya A-J, UAE A-J, Saudi A-J, Vietnam A-J, Japan A-J, South Korea A-J,
Iraq A-M, and 9P117 stay frozen.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Satellite last-wins: CommandSet_SyriaMissiles.ini,
CommandButton_SyriaMissiles.ini, Weapon\\Weapon_Syria_Missiles.ini.
Syria flag (red / white+two green stars / black) + exact names on dorsal UV.
Dedicated Syr_TEL drab truck. No RadarPriority. No rearm. No ZZZZ.
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

SRC_DATA = ROOT / "patch/Release/SPECTER_LIBYA_ACC_DESC/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_LIBYA_ACC_DESC/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_SYRIA_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_LBY = "ae367d5ae8d2b342f31d6c3cbe4c2c73b0acd47c4e16be2ba3954b1f892992a1"
SIZE_DATA_LBY = 367680770
SHA_ART_LBY = "52701d0c089144a4201cdb8946fc8f70f5e5b0a42b45f051c8dca1938ca3fa79"
SIZE_ART_LBY = 1591573341

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

SYR_CB_KEY = r"Data\INI\CommandButton_SyriaMissiles.ini"
SYR_CS_KEY = r"Data\INI\CommandSet_SyriaMissiles.ini"
SYR_WEP_KEY = r"Data\INI\Weapon\Weapon_Syria_Missiles.ini"
SYR_FAC_KEY = (
    r"Data\INI\Object\Specter\Syrian Armed Forces"
    r"\Buildings\Syria_MissileFactory.ini"
)
SYR_VT72B_KEY = r"Data\INI\Object\Specter\Syrian Armed Forces\Tracked\VT72B.ini"
SYR_DOZER_KEY = r"Data\INI\Object\Specter\Syrian Armed Forces\Tracked\Syria_Dozer.ini"
SYR_SHAHEEN_KEY = r"Data\INI\Object\Specter\Syrian Armed Forces\Wheeled\Syria_ShaheenTEL.ini"
SYR_ABABEEL_KEY = r"Data\INI\Object\Specter\Syrian Armed Forces\Wheeled\Syria_AbabeelTEL.ini"
SYR_ALHUSS_KEY = r"Data\INI\Object\Specter\Syrian Armed Forces\Wheeled\AbbasLauncher.ini"
SYR_WEP_OLD_KEY = r"Data\INI\Weapon_Syria.ini"
SYR_MIC_KEY = r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_MIC.ini"
SYR_LGM_KEY = r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_Lgm30.ini"
SYR_ZZZ_CS = r"Data\INI\CommandSet_ZZZZ_AfricaPakistanSyria_AirExp.ini"
SYR_ZZZ_CB = r"Data\INI\CommandButton_ZZZZ_AfricaPakistanSyria_AirExp.ini"

TRUCK_TEX = "Syr_TEL.tga"
TRUCKD_TEX = "Syr_TELD.tga"
TRUCK_KEY = rf"Art\Textures\{TRUCK_TEX}"
TRUCKD_KEY = rf"Art\Textures\{TRUCKD_TEX}"

WEP_MARKER = (
    "; ===== Syria missiles A-J "
    "(Weapon.ini load path for Command_FireMainWeapon) ====="
)

BUILDERS = [
    "SyriaDozerCommandSet",
    "Syria_WorkerCommandSet",
    "Syria_VT72BCommandSet",
]

DRAB = (108, 116, 70)
EARTH = (76, 72, 52)
SOOT = (44, 42, 36)
NOSE_W = (236, 228, 210)
NOSE_R = (196, 16, 28)
NOSE_G = (0, 140, 64)

# Distinct from Libya/UAE/Saudi slot-for-slot colors. Flag-forward drab / sand / navy.
# Gameplay values are SPECTER design, informed by public mission class, not claimed specs.
MISSILES = [
    {
        "slot": "A", "object": "Syria_Luna", "name": "Luna",
        "model": "Syr_Luna", "modeld": "Syr_LunaD", "proj_model": "Syr_LunaM",
        "hier": b"SYR_LUNAA", "hierd": b"SYR_LUNAAD", "proj_hier": b"SYR_MSL_A",
        "tex": "Syr_LunaP.tga", "body": (88, 96, 42), "nose": NOSE_R,
        "expect": "muddy", "km": 1000, "kg": 450, "acc": 30, "stealth": 20,
        "rebuild": 16, "price": 750,
        "role": "Tactical unguided rocket (FROG-7/Luna-M analogue)",
    },
    {
        "slot": "B", "object": "Syria_Tochka", "name": "Tochka",
        "model": "Syr_Tochka", "modeld": "Syr_TochkaD", "proj_model": "Syr_TochkaM",
        "hier": b"SYR_TOCHB", "hierd": b"SYR_TOCHBD", "proj_hier": b"SYR_MSL_B",
        "tex": "Syr_TochkaP.tga", "body": (220, 200, 155), "nose": NOSE_W,
        "expect": "cream", "km": 1050, "kg": 500, "acc": 68, "stealth": 22,
        "rebuild": 20, "price": 1050,
        "role": "Tactical SRBM (SS-21 analogue)",
    },
    {
        "slot": "C", "object": "Syria_Khaibar", "name": "Khaibar",
        "model": "Syr_Khaibar", "modeld": "Syr_KhaibarD", "proj_model": "Syr_KhaibarM",
        "hier": b"SYR_KHAIC", "hierd": b"SYR_KHAICD", "proj_hier": b"SYR_MSL_C",
        "tex": "Syr_KhaibarP.tga", "body": (210, 108, 22), "nose": NOSE_W,
        "expect": "orange", "km": 1100, "kg": 400, "acc": 22, "stealth": 16,
        "rebuild": 18, "price": 850,
        "role": "Heavy rocket artillery (Khaibar-1/M-302 analogue)",
    },
    {
        "slot": "D", "object": "Syria_R17", "name": "R-17",
        "model": "Syr_R17", "modeld": "Syr_R17D", "proj_model": "Syr_R17M",
        "hier": b"SYR_R17SD", "hierd": b"SYR_R17SDD", "proj_hier": b"SYR_MSL_D",
        "tex": "Syr_R17P.tga", "body": (168, 32, 28), "nose": NOSE_W,
        "expect": "red", "km": 1250, "kg": 985, "acc": 32, "stealth": 28,
        "rebuild": 28, "price": 1750,
        "role": "Operational SRBM (Scud-B / R-17 analogue)",
    },
    {
        "slot": "E", "object": "Syria_Homs", "name": "Homs",
        "model": "Syr_Homs", "modeld": "Syr_HomsD", "proj_model": "Syr_HomsM",
        "hier": b"SYR_HOMSE", "hierd": b"SYR_HOMSED", "proj_hier": b"SYR_MSL_E",
        "tex": "Syr_HomsP.tga", "body": (228, 224, 216), "nose": NOSE_R,
        "expect": "white", "km": 1450, "kg": 600, "acc": 34, "stealth": 26,
        "rebuild": 34, "price": 2100,
        "role": "Extended-range SRBM (Scud-C analogue)",
    },
    {
        "slot": "F", "object": "Syria_Tishreen", "name": "Tishreen",
        "model": "Syr_Tishreen", "modeld": "Syr_TishreenD", "proj_model": "Syr_TishreenM",
        "hier": b"SYR_TISHF", "hierd": b"SYR_TISHFD", "proj_hier": b"SYR_MSL_F",
        "tex": "Syr_TishreenP.tga", "body": (8, 162, 56), "nose": NOSE_W,
        "expect": "green", "km": 1350, "kg": 500, "acc": 72, "stealth": 32,
        "rebuild": 32, "price": 2300,
        "role": "Guided SRBM (M-600/Tishreen / Fateh-110 class analogue)",
    },
    {
        "slot": "G", "object": "Syria_Qalamoun", "name": "Qalamoun",
        "model": "Syr_Qalamoun", "modeld": "Syr_QalamounD", "proj_model": "Syr_QalamounM",
        "hier": b"SYR_QLMNG", "hierd": b"SYR_QLMNGD", "proj_hier": b"SYR_MSL_G",
        "tex": "Syr_QalamounP.tga", "body": (222, 182, 28), "nose": NOSE_W,
        "expect": "yellow", "km": 1650, "kg": 700, "acc": 48, "stealth": 30,
        "rebuild": 42, "price": 3000,
        "role": "Improved SRBM (Scud-D analogue)",
    },
    {
        "slot": "H", "object": "Syria_Yakhont", "name": "Yakhont",
        "model": "Syr_Yakhont", "modeld": "Syr_YakhontD", "proj_model": "Syr_YakhontM",
        "hier": b"SYR_YAKHH", "hierd": b"SYR_YAKHHD", "proj_hier": b"SYR_MSL_H",
        "tex": "Syr_YakhontP.tga", "body": (28, 68, 168), "nose": NOSE_W,
        "expect": "blue", "km": 1550, "kg": 400, "acc": 74, "stealth": 58,
        "rebuild": 40, "price": 3400,
        "role": "Coastal/cruise analogue (P-800 Oniks/Yakhont)",
    },
    {
        "slot": "I", "object": "Syria_Sham", "name": "Sham",
        "model": "Syr_Sham", "modeld": "Syr_ShamD", "proj_model": "Syr_ShamM",
        "hier": b"SYR_SHAMI", "hierd": b"SYR_SHAMID", "proj_hier": b"SYR_MSL_I",
        "tex": "Syr_ShamP.tga", "body": (128, 128, 128), "nose": NOSE_R,
        "expect": "gray", "km": 1900, "kg": 1100, "acc": 38, "stealth": 34,
        "rebuild": 55, "price": 4200,
        "role": "Extended regional SRBM (claimed Scud-ER class; uncertain)",
    },
    {
        "slot": "J", "object": "Syria_Barada", "name": "Barada",
        "model": "Syr_Barada", "modeld": "Syr_BaradaD", "proj_model": "Syr_BaradaM",
        "hier": b"SYR_BARAJ", "hierd": b"SYR_BARAJD", "proj_hier": b"SYR_MSL_J",
        "tex": "Syr_BaradaP.tga", "body": (10, 72, 84), "nose": NOSE_G,
        "expect": "petrol", "km": 2200, "kg": 1500, "acc": 42, "stealth": 38,
        "rebuild": 68, "price": 5800,
        "role": "High-end regional (no verified Syrian ICBM)",
    },
]

NAME_MAP = [
    "A Luna new (FROG-7/Luna-M analogue; game floor 1000 km)",
    "B Tochka new (SS-21 analogue; better Acc, modest payload)",
    "C Khaibar new (Khaibar-1/M-302 analogue; unguided rocket)",
    "D R-17 new as Syria_R17 (Scud-B analogue; ~985 kg class payload)",
    "E Homs new (Scud-C analogue; longer than R-17, lighter warhead)",
    "F Tishreen new (documented Syrian M-600/Fateh-110 class name)",
    "G Qalamoun new (Scud-D analogue; improved vs Scud-B)",
    "H Yakhont new (P-800 coastal/cruise analogue; MaxHealth proxy, not stealth)",
    "I Sham new (claimed extended Scud-ER class; conservative game stretch)",
    "J Barada new (high-end regional cap; not an ICBM)",
]

FROZEN_DATA = list(lby.FROZEN_DATA) + [
    lby.LBY_FAC_KEY, lby.LBY_CB_KEY, lby.LBY_CS_KEY, lby.LBY_WEP_KEY,
    SYR_VT72B_KEY, SYR_DOZER_KEY, SYR_SHAHEEN_KEY, SYR_ABABEEL_KEY,
    SYR_ALHUSS_KEY, SYR_WEP_OLD_KEY, SYR_MIC_KEY, SYR_LGM_KEY,
    SYR_ZZZ_CS, SYR_ZZZ_CB,
]
FROZEN_DATA += [m["unit_key"] for m in lby.DERIVED]
FROZEN_DATA += [m["proj_key"] for m in lby.DERIVED]

FROZEN_ART = list(lby.FROZEN_ART) + [
    lby.TRUCK_KEY, lby.TRUCKD_KEY,
    r"Art\Textures\Lby_FajrP.tga", r"Art\W3D\Lby_Fajr.W3D",
]
FROZEN_ART += [m["tex_key"] for m in lby.DERIVED]
FROZEN_ART += [m["tel_key"] for m in lby.DERIVED]
FROZEN_ART += [m["teld_key"] for m in lby.DERIVED]
FROZEN_ART += [m["projw_key"] for m in lby.DERIVED]

for _m in MISSILES:
    assert len(_m["hier"]) == 9 and len(_m["hierd"]) == 10 and len(_m["proj_hier"]) == 9
    assert 1000 <= _m["km"] <= 4000 and 400 <= _m["kg"] <= 10000


def derived(m: dict) -> dict:
    d = sk.derived({**m, "min_range": sk.MOTHER_MIN_RANGE})
    d["button"] = f"CB_SYRIA_MISSILE_{m['slot']}"
    d["unit_key"] = (
        r"Data\INI\Object\Specter\Syrian Armed Forces"
        rf"\Wheeled\{m['object']}.ini"
    )
    d["proj_key"] = (
        r"Data\INI\Object\Specter\Syrian Armed Forces"
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


def make_syria_flag() -> Image.Image:
    """Syrian Arab Republic flag used by SPECTER Side=Syria: red / white / black, two green stars."""
    w, h = 900, 600
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    draw = ImageDraw.Draw(im)
    stripe = h / 3.0
    draw.rectangle([0, 0, w, int(round(stripe))], fill=(206, 17, 38, 255))
    draw.rectangle([0, int(round(stripe)), w, int(round(stripe * 2))], fill=(255, 255, 255, 255))
    draw.rectangle([0, int(round(stripe * 2)), w, h], fill=(0, 0, 0, 255))
    cy = h * 0.50
    r_out = h * 0.13
    r_in = r_out * 0.42
    _star(draw, w * 0.38, cy, r_out, r_in, (0, 122, 61, 255))
    _star(draw, w * 0.62, cy, r_out, r_in, (0, 122, 61, 255))
    return im


def has_syria_flag(counts: dict[str, int]) -> bool:
    greenish = counts.get("green", 0) + counts.get("muddy", 0)
    return (
        counts.get("red", 0) >= 4
        and counts.get("white", 0) >= 4
        and counts.get("black", 0) >= 3
        and greenish >= 2
    )


def recolor_truck(src: Image.Image, damaged: bool = False) -> Image.Image:
    """Map Iraqi tan sheet to Syria drab / earth / soot. Not Libya ochre, Saudi olive, or UAE pearl."""
    im = src.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            avg = (r + g + b) / 3.0
            sat = max(r, g, b) - min(r, g, b)
            if avg < 55 and sat < 35:
                px[x, y] = (max(0, int(r * 0.32)), max(0, int(g * 0.30)), max(0, int(b * 0.26)), a)
                continue
            if sat > 70 and avg > 70:
                base = DRAB
                t = 0.92
            elif avg < 100:
                base = EARTH
                t = max(0.70, min(1.15, avg / 90.0))
            else:
                base = DRAB
                t = max(0.55, min(1.25, avg / 130.0))
            nr = min(255, int(base[0] * t))
            ng = min(255, int(base[1] * t))
            nb = min(255, int(base[2] * t))
            if damaged:
                nr, ng, nb = int(nr * 0.70), int(ng * 0.66), int(nb * 0.58)
            px[x, y] = (nr, ng, nb, a)
    return im


def make_syr_tel_w3d(src: bytes, damaged: bool, m: dict) -> bytes:
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
        .replace("South Korea", "Syria")
        .replace("Side = SouthKorea", "Side = Syria")
        .replace(
            "Skr_TEL / Skr_TELD (not Irq_9P117 / Jpn_TEL)",
            "Syr_TEL / Syr_TELD (not Irq_9P117 / Jpn_TEL / Skr_TEL / Sau_TEL / Uae_TEL / Lby_TEL)",
        )
    )


def projectile_ini(m: dict) -> str:
    return sk.projectile_ini(m).replace("South Korea", "Syria")


def weapon_file(missiles: list[dict]) -> str:
    head = (
        WEP_MARKER + "\n"
        "; 9P117 scale. Dedicated Syria A-J. Distinct from Libya/UAE/Saudi/Vietnam/Japan/SK/Iraq.\n"
        "; Regional profile: tactical/operational SRBM emphasis, not ICBM-class J slots.\n"
        "; ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000 (PR #629).\n"
        "; Death HACK is a separate path and is not folded into PrimaryDamage.\n"
        "; Acc/CHL columns are design labels mapped to ScatterRadius / MaxHealth.\n"
    )
    body = sk.weapon_blocks(missiles)
    pairs = body.split("\n\n", 1)[1] if "\n\n" in body else body
    return head + "\n" + pairs


def factory_ini() -> str:
    text = sk.factory_ini()
    text = text.replace("; South Korea missile factory.", "; Syria missile factory.")
    text = text.replace(
        "with a SouthKorea-only CommandSet (A-J).",
        "with a Syria-only CommandSet (A-J).",
    )
    text = text.replace("Object SouthKorea_MissileFactory", "Object Syria_MissileFactory")
    text = text.replace(
        "DisplayName      = OBJECT:SouthKoreaMissileFactory",
        "DisplayName      = OBJECT:SyriaMissileFactory",
    )
    text = text.replace("Side             = SouthKorea", "Side             = Syria")
    text = text.replace(
        "CommandSet       = SouthKorea_MissileFactoryCommandSet",
        "CommandSet       = Syria_MissileFactoryCommandSet",
    )
    return text


def factory_commandset() -> str:
    slots = "\r\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(DERIVED, start=1))
    return (
        "CommandSet Syria_MissileFactoryCommandSet\r\n"
        f"{slots}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def with_syria_factory(block: str) -> str:
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in block:
        raise SystemExit(f"expected isolated Iraq factory in:\n{block}")
    if "Command_ConstructSyria_MissileFactory" in block:
        raise SystemExit("Syria factory already present on builder")
    return block.replace(
        "Command_ConstructIraq_AlFahdMissileFactoryBuilding",
        "Command_ConstructSyria_MissileFactory",
    )


def commandbutton_all() -> str:
    lines = [
        "; Syria missiles A-J production buttons and factory construct button.",
        "; Shared specter_missile_* cameos. Unique Object bindings.",
        "",
        "CommandButton Command_ConstructSyria_MissileFactory",
        "  Command          = DOZER_CONSTRUCT",
        "  Object           = Syria_MissileFactory",
        "  TextLabel        = CONTROLBAR:ConstructSyriaMissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel    = CONTROLBAR:ToolTipSyriaMissileFactory",
        "End",
        "",
    ]
    for m in DERIVED:
        lines.extend(
            [
                f"CommandButton {m['button']}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {m['object']}",
                f"  TextLabel     = CONTROLBAR:SyriaMissile{m['slot']}",
                f"  ButtonImage   = {m['cameo']}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTipSyriaMissile{m['slot']}",
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
        "OBJECT:SyriaMissileFactory": "Missile Factory",
        "CONTROLBAR:ConstructSyriaMissileFactory": "Missile Factory",
        "CONTROLBAR:ToolTipSyriaMissileFactory": (
            "Missile Factory\nProduces Syria missiles A-J\nPrice: $1800"
        ),
    }
    for m in DERIVED:
        mapping[f"OBJECT:{m['object']}"] = m["name"]
        mapping[f"CONTROLBAR:SyriaMissile{m['slot']}"] = f"{m['slot']} {m['name']}"
        mapping[f"CONTROLBAR:ToolTipSyriaMissile{m['slot']}"] = player_tooltip(m)
    return mapping


def mapping_report() -> list[str]:
    lines = [
        "NAME MAPPING:",
        *[f"  {row}" for row in NAME_MAP],
        "",
        "EXISTING SYRIA MISSILE OBJECTS PRESERVED (not factory A-J):",
        "  Syria_ShaheenTEL / Syria_Weapon_Shaheen",
        "  Syria_AbabeelTEL / Syria_Weapon_Ababeel",
        "  Syria_Alhussaien (AbbasLauncher.ini)",
        "  Syria_Lgm30 (AmericaLgm30CommandSet) unchanged.",
        "",
        "FACTORY CONSTRUCT:",
        "  Pre-change Dozer/Worker/VT72B constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  Post-change those menus construct Syria_MissileFactory.",
        "  MIC remains on slot 6. Abbas / Lgm30 / FireBase / CRAM unchanged.",
        "",
        "REAL-WORLD vs GAMEPLAY:",
        "  Public sources place Syrian ballistic missiles in roughly 70-700 km classes",
        "  (FROG-7, SS-21, Scud-B/C/D, M-600/Tishreen) plus P-800 Yakhont coastal missiles.",
        "  SPECTER floor is 1000 km, so those classes are mapped onto the floor and a",
        "  conservative regional stretch. Values below are SPECTER design, not verified specs.",
        "  No public evidence supports a Syrian ICBM or multi-ton strategic warhead.",
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
    sat_cs = data[SYR_CS_KEY].decode("latin1")

    if "ZZZZ" in SYR_CB_KEY or "ZZZZ" in SYR_CS_KEY or "ZZZZ" in SYR_WEP_KEY:
        fails.append("ZZZZ shortcut")
    if SYR_CS_KEY >= r"Data\INI\CommandSet_ZZZZ":
        fails.append("Syria satellite sorts into ZZZZ")
    if SYR_CS_KEY <= CS_KEY:
        fails.append("Syria satellite sorts before CommandSet.ini")

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
        "Libya_MissileFactoryCommandSet",
        "LibyaDozerCommandSet",
        "Libya_WorkerCommandSet",
        "Libya_VT72BCommandSet",
    ):
        if sk.last_block(cs_text, "CommandSet", frozen_cs) != sk.last_block(
            src_cs, "CommandSet", frozen_cs
        ):
            fails.append(f"{frozen_cs} mutated in CommandSet.ini")

    for name in BUILDERS:
        new_b = sk.last_block(cs_text, "CommandSet", name)
        if "Command_ConstructSyria_MissileFactory" not in new_b:
            fails.append(f"{name} catalog missing Syria factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in new_b:
            fails.append(f"{name} still has isolated Iraq factory")
        if "Command_ConstructSyria_MIC" not in new_b:
            fails.append(f"{name} lost MIC")
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", name)
        if "Command_ConstructSyria_MissileFactory" not in lw:
            fails.append(f"last-wins {name} from {_k} missing Syria factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in lw:
            fails.append(f"last-wins {name} still Iraq factory")
        if name not in sat_cs:
            fails.append(f"satellite missing {name}")

    fac = sk.last_block(cs_text, "CommandSet", "Syria_MissileFactoryCommandSet")
    if not fac:
        fails.append("CommandSet.ini missing Syria factory roster")
    slots = re.findall(r"CB_SYRIA_MISSILE_([A-Z])", fac)
    if slots != list("ABCDEFGHIJ"):
        fails.append(f"factory slots {slots} != A-J")
    if "Command_Sell" not in fac or "Command_SetRallyPoint" not in fac:
        fails.append("factory missing Rally/Sell")
    if any(
        tag in fac
        for tag in (
            "CB_VIETNAM_", "CB_JAPAN_", "CB_SOUTHKOREA_", "CB_SAUDIARABIA_",
            "CB_UAE_", "CB_LIBYA_",
        )
    ):
        fails.append("factory mixed foreign buttons")

    construct = sk.last_block(cb_text, "CommandButton", "Command_ConstructSyria_MissileFactory")
    if sk.field(construct, "Object") != "Syria_MissileFactory":
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
    ):
        if sk.field(sk.last_block(cb_text, "CommandButton", btn), "ButtonImage") != img:
            fails.append(f"{btn} image lost")
        if sk.last_block(cb_text, "CommandButton", btn) != sk.last_block(src_cb, "CommandButton", btn):
            fails.append(f"{btn} mutated")

    fac_obj = sk.last_block(data[SYR_FAC_KEY].decode("latin1"), "Object", "Syria_MissileFactory")
    if sk.field(fac_obj, "Side") != "Syria":
        fails.append("factory Side")
    if sk.field(fac_obj, "CommandSet") != "Syria_MissileFactoryCommandSet":
        fails.append("factory object CommandSet")
    if "SouthKorea_SupplyCenter" not in fac_obj:
        fails.append("factory lost SouthKorea_SupplyCenter prereq")
    if "Syria_SupplyCenter" not in fac_obj:
        fails.append("factory missing Syria_SupplyCenter prereq")

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
    if sk.last_block(data[SYR_WEP_OLD_KEY].decode("latin1"), "Weapon", "Syria_Weapon_Shaheen") != sk.last_block(
        src_data[SYR_WEP_OLD_KEY].decode("latin1"), "Weapon", "Syria_Weapon_Shaheen"
    ):
        fails.append("Syria Shaheen weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Libya_Fajr") != sk.last_block(
        src_wep, "Weapon", "Weapon_Libya_Fajr"
    ):
        fails.append("Libya Fajr weapon mutated")

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
    lby_fac = sk.last_block(data[lby.LBY_FAC_KEY].decode("latin1"), "Object", "Libya_MissileFactory")
    if sk.field(lby_fac, "Side") != "Libya":
        fails.append("Libya factory Side mutated")

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
    lby_avg = Image.open(io.BytesIO(src_art[lby.TRUCK_KEY])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == lby_avg:
        fails.append("truck still Libya ochre")

    wep_sat = data[SYR_WEP_KEY].decode("latin1")
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
        if sk.field(unit, "Side") != "Syria":
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
        if "Syria_ShaheenTEL" in unit or "Syria_Alhussaien" in unit or "Libya_Fajr" in unit:
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
        if sk.csf_get(csf, f"CONTROLBAR:SyriaMissile{m['slot']}") != f"{m['slot']} {m['name']}":
            fails.append(f"{m['slot']} CSF name")
        if sk.csf_get(csf, f"CONTROLBAR:ToolTipSyriaMissile{m['slot']}") != player_tooltip(m):
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
        if any(x in tel_tex for x in ("Skr_TEL.tga", "Jpn_TEL.tga", "Sau_TEL.tga", "Uae_TEL.tga", "Lby_TEL.tga")):
            fails.append(f"{m['slot']} foreign truck")

        im = Image.open(io.BytesIO(art[m["tex_key"]])).convert("RGB")
        tel_flag = sk.region_mode(im, (110, 180, 420, 290))
        if not has_syria_flag(tel_flag):
            fails.append(f"{m['slot']} Syria flag {tel_flag}")
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
    fac_dir = LOOSE / "Object/Specter/Syrian Armed Forces/Buildings"
    wheel_dir = LOOSE / "Object/Specter/Syrian Armed Forces/Wheeled"
    proj_dir = LOOSE / "Object/Specter/Syrian Armed Forces"
    wep_dir = LOOSE / "Weapon"
    for d in (fac_dir, wheel_dir, proj_dir, wep_dir):
        d.mkdir(parents=True, exist_ok=True)
    (fac_dir / "Syria_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    (wep_dir / "Weapon_Syria_Missiles.ini").write_text(weapon_file(DERIVED), encoding="utf-8")
    (LOOSE / "CommandButton_SyriaMissiles.ini").write_text(commandbutton_all(), encoding="utf-8")
    (LOOSE / "CommandSet_SyriaMissiles.ini").write_text(commandset_file(builders), encoding="utf-8")
    for m in DERIVED:
        (wheel_dir / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (proj_dir / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_LBY or SRC_DATA.stat().st_size != SIZE_DATA_LBY:
        raise SystemExit("DATA baseline is not SPECTER_LIBYA_ACC_DESC")
    if sk.sha256_path(SRC_ART) != SHA_ART_LBY or SRC_ART.stat().st_size != SIZE_ART_LBY:
        raise SystemExit("ART baseline is not SPECTER_LIBYA_ACC_DESC")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art = sk.parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    flag = make_syria_flag()
    truck = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])), damaged=False)
    truckd = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCKD_DDS])), damaged=True)
    art[TRUCK_KEY] = sk.make_tga32(truck)
    art[TRUCKD_KEY] = sk.make_tga32(truckd)

    for m in DERIVED:
        skin = sk.make_skin(m["body"], m["nose"], m["name"], flag)
        art[m["tex_key"]] = sk.make_tga32(skin)
        art[m["tel_key"]] = make_syr_tel_w3d(src_art[TEL_W3D], False, m)
        art[m["teld_key"]] = make_syr_tel_w3d(src_art[TELD_W3D], True, m)
        art[m["projw_key"]] = sk.make_proj_w3d(src_art[PROJ_W3D], m)
        data[m["unit_key"]] = sk.to_crlf(unit_ini(m))
        data[m["proj_key"]] = sk.to_crlf(projectile_ini(m))

    data[SYR_FAC_KEY] = sk.to_crlf(factory_ini())
    data[SYR_WEP_KEY] = sk.to_crlf(weapon_file(DERIVED))
    data[SYR_CB_KEY] = sk.to_crlf(commandbutton_all())
    data[CSF_KEY] = sk.csf_upsert(src_data[CSF_KEY], csf_map())

    cs = src_data[CS_KEY].decode("latin1")
    builders = {}
    for name in BUILDERS:
        old = sk.last_block(cs, "CommandSet", name)
        new = with_syria_factory(old)
        builders[name] = new
        cs = sk.replace_last(cs, "CommandSet", name, new)
    if sk.last_block(cs, "CommandSet", "Syria_MissileFactoryCommandSet"):
        cs = sk.replace_last(cs, "CommandSet", "Syria_MissileFactoryCommandSet", factory_commandset())
    else:
        cs = cs.rstrip("\r\n") + "\r\n\r\n" + factory_commandset() + "\r\n"
    data[CS_KEY] = cs.encode("latin1")
    data[SYR_CS_KEY] = sk.to_crlf(commandset_file(builders))

    cb = src_data[CB_KEY].decode("latin1")
    if "CommandButton Command_ConstructSyria_MissileFactory" in cb:
        raise SystemExit("CommandButton.ini already had Syria factory")
    extra = commandbutton_all().replace("\n", "\r\n")
    data[CB_KEY] = (cb.rstrip("\r\n") + "\r\n\r\n" + extra + "\r\n").encode("latin1")

    wep = src_data[WEAPON_KEY].decode("latin1")
    if WEP_MARKER in wep or "Weapon Weapon_Syria_Luna" in wep:
        raise SystemExit("Weapon.ini already had Syria A-J")
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
    (ext / "CommandSet.ini.Syria.txt").write_text(
        "\r\n\r\n".join(sk.last_block(packed_cs, "CommandSet", n) for n in BUILDERS)
        + "\r\n\r\n"
        + sk.last_block(packed_cs, "CommandSet", "Syria_MissileFactoryCommandSet")
        + "\r\n",
        encoding="utf-8",
    )
    (ext / "Weapon.ini.Syria.txt").write_text(weapon_file(DERIVED), encoding="utf-8")
    (ext / "Syria_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    for m in DERIVED:
        (ext / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (ext / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    preview = OUT / "PREVIEW"
    preview.mkdir()
    flag.save(preview / "SyriaFlag.png")
    truck.save(preview / "Syr_TEL.png")
    truckd.save(preview / "Syr_TELD.png")
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
    zip_path = ROOT / "patch/Release/SPECTER_SYRIA_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    inv = [
        "PRE-CHANGE SYRIA (packed last-wins, Libya A-J acc-desc baseline):",
        "  No Syria_MissileFactory.",
        "  Dozer/Worker/VT72B constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  MIC on slot 6. Existing ShaheenTEL / AbabeelTEL / Alhussaien / Lgm30 preserved.",
        "  Packed faction path: Syrian Armed Forces. Side=Syria.",
        "",
        "POST-CHANGE SYRIA:",
        "  Dedicated Syria_MissileFactory A-J + Rally/Sell.",
        "  Builder slot that held the isolated Iraq factory now builds the Syria factory.",
        "  Regional profile: 1000-2200 km, 400-1500 kg. Not a Libya/UAE/Saudi reskin.",
        "",
        "COUNTRY BALANCE (inspected packed / accepted factory A-J, not runtime):",
        "  Factory A-J countries Japan/SK/Vietnam/Saudi/UAE/Libya stretch to 3400-4000 km",
        "  and multi-ton J payloads (Libya J 3900 km / 8000 kg, UAE J 4000/7000,",
        "  Saudi J 4000/4000, Japan J 3600/4000, Vietnam J 4000/4000).",
        "  US/EU do not currently have an A-J missile-factory roster in packed DATA.",
        "  US strategic systems (LGM-30 Minuteman III, UGM-133 Trident II, Tomahawk)",
        "  and European standoff weapons (SCALP, Storm Shadow, Taurus) live on other",
        "  production paths and remain the advanced strategic/standoff set.",
        "  Syria A-J caps at 2200 km / 1500 kg so it stays a regional force.",
        "  Syria Acc is generally lower except Tochka/Tishreen/Yakhont.",
        "  CHL is interceptor toughness (MaxHealth), not stealth. Yakhont is the outlier.",
        "",
        *map_lines,
    ]
    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #636 s-libya-aj-acc-desc + PR #635 + #634 + #633 + #632 + #631 + #630 + #629",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "SYRIA_FACTORY_NEW=YES",
        "SHAHEEN_ABABEEL_ALHUSS_LGM30_KEPT=YES",
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
        "KM_CEILING_USED=2200",
        "KG_FLOOR=400",
        "KG_CEILING_USED=1500",
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
            "ZIP_FILE=SPECTER_SYRIA_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #636",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-syria-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-syria-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-syria-missiles-aj/SPECTER_SYRIA_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-syria-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-syria-missiles-aj",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Syria complete missile roster A-J on the accepted factory/fire path.\n"
        "New country factory replaces the isolated Iraq factory construct on Syria builders.\n"
        "Existing ShaheenTEL, AbabeelTEL, Alhussaien, and Lgm30 are unchanged.\n"
        "Regional profile 1000-2200 km / 400-1500 kg. Not a Libya/UAE/Saudi reskin.\n"
        "Libya A-J, UAE A-J, Saudi A-J, Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Syria missiles A-J\n\n"
        "- New Syria_MissileFactory. Rally/Sell retained.\n"
        "- Replaces isolated Iraq factory construct on Syria Dozer, Worker, and VT72B.\n"
        "- MIC, Abbas, Lgm30, ShaheenTEL, AbabeelTEL, and Alhussaien preserved.\n"
        "- Syria flag (red / white + two green stars / black) + exact names on dorsal UV bands.\n"
        "- Dedicated Syr_TEL drab truck. Ten-color tube palette distinct from Libya/UAE/Saudi.\n"
        "- Regional capability cap: 2200 km / 1500 kg. Not ICBM-class.\n"
        "- 5-minute clip reload on all ten PRIMARY weapons.\n"
        "- Libya A-J, UAE A-J, Saudi A-J, Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n", encoding="utf-8")
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_SyriaMissiles.ini last-wins Syria builder + factory CommandSets.\n"
        "CommandButton_SyriaMissiles.ini last-wins construct + A-J.\n"
        "Weapon\\Weapon_Syria_Missiles.ini last-wins Weapon_Syria_* factory pair.\n"
        "Weapon_Syria.ini (Shaheen/Ababeel and other Syria weapons) is unchanged.\n"
        "Syria_Luna/Tochka/Khaibar/R17/Homs/Tishreen/Qalamoun/Yakhont/Sham/Barada are new objects.\n"
        "Libya, UAE, Saudi, Vietnam, Japan, South Korea, Iraq, and 9P117 packed definitions are unchanged.\n"
    )
    art_notes = [
        "SYRIA A-J ART MARKINGS (static inspection)",
        "",
        "Flag: red upper, white middle with two green stars, black lower.",
        "SPECTER Side=Syria / Syrian Armed Forces identity. Not UAE / Saudi / Iraq / Libya flags.",
        "Dedicated Syr_TEL / Syr_TELD drab truck. Not Irq_9P117 / Skr_TEL / Jpn_TEL / Sau_TEL / Uae_TEL / Lby_TEL.",
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
