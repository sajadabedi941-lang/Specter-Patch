#!/usr/bin/env python3
"""Implement United Arab Emirates missile roster A-J on the Saudi / Vietnam / SK / Japan path.

Baseline: packed SPECTER_SAUDI_MISSILES_AJ (PR #633 + #632 + #631 + #630 + #629).

UAE has no missile factory. Dozer / Worker / VT72B slot 13 currently constructs
the isolated Sell-only Iraq_AlFahdMissileFactoryBuilding. Replace that slot with a
UAE-only factory. Keep MIC on slot 6.

Preserve existing UAE_ShaheenTEL, UAE_AbabeelTEL, and UAE_Alhussaien. Preserve
UAE_Flag.tga and unrelated UAE buildings / economy / fighter roster. Slot B keeps
the proposed name Barq as object UAE_Barq (distinct from SaudiArabia_Barq).

Saudi A-J, Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 stay frozen.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Satellite last-wins: CommandSet_UAEMissiles.ini,
CommandButton_UAEMissiles.ini, Weapon\\Weapon_UAE_Missiles.ini.
UAE flag (red hoist + green/white/black stripes) + exact names on dorsal UV bands.
Dedicated Uae_TEL truck. No RadarPriority. No rearm. No ZZZZ.
"""
from __future__ import annotations

import io
import re
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_sk_missiles_aj as sk  # noqa: E402
import pack_s_vietnam_missiles_aj as vn  # noqa: E402
import pack_s_saudi_missiles_aj as sa  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_SAUDI_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_SAUDI_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_UAE_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SA = "817b0090bc306f4ca806f6a0138d0edaa36e2840a24e8b701908f09dffd63742"
SIZE_DATA_SA = 367350979
SHA_ART_SA = "a74545ef775a2d6d32a73e249f9f34a96f5d8b04f9d24d31ae4881e16f9fc2d4"
SIZE_ART_SA = 1496048723

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

UAE_CB_KEY = r"Data\INI\CommandButton_UAEMissiles.ini"
UAE_CS_KEY = r"Data\INI\CommandSet_UAEMissiles.ini"
UAE_WEP_KEY = r"Data\INI\Weapon\Weapon_UAE_Missiles.ini"
UAE_FAC_KEY = (
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces"
    r"\Buildings\UAE_MissileFactory.ini"
)
UAE_VT72B_KEY = r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Tracked\VT72B.ini"
UAE_DOZER_KEY = r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Tracked\UAE_Dozer.ini"
UAE_SHAHEEN_KEY = (
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Wheeled\UAE_ShaheenTEL.ini"
)
UAE_ABABEEL_KEY = (
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Wheeled\UAE_AbabeelTEL.ini"
)
UAE_ALHUSS_KEY = r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Wheeled\AbbasLauncher.ini"
UAE_WEP_OLD_KEY = r"Data\INI\Weapon_UAE.ini"
UAE_MIC_KEY = r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_MIC.ini"
UAE_FLAG_KEY = r"Art\Textures\UAE_Flag.tga"

TRUCK_TEX = "Uae_TEL.tga"
TRUCKD_TEX = "Uae_TELD.tga"
TRUCK_KEY = rf"Art\Textures\{TRUCK_TEX}"
TRUCKD_KEY = rf"Art\Textures\{TRUCKD_TEX}"

WEP_MARKER = (
    "; ===== United Arab Emirates missiles A-J "
    "(Weapon.ini load path for Command_FireMainWeapon) ====="
)

BUILDERS = [
    "UAEDozerCommandSet",
    "UAE_WorkerCommandSet",
    "UAE_VT72BCommandSet",
]

PEARL = (196, 184, 168)
STONE = (148, 140, 128)
STEEL = (88, 92, 96)
NOSE_W = (236, 228, 210)
NOSE_R = (176, 24, 36)
NOSE_G = (8, 120, 64)

# Distinct from Saudi cream/orange/white/red/yellow/petrol/black/blue/gray/muddy.
MISSILES = [
    {
        "slot": "A", "object": "UAE_Falcon", "name": "Falcon",
        "model": "Uae_Falcon", "modeld": "Uae_FalconD", "proj_model": "Uae_FalconM",
        "hier": b"UAE_FALCA", "hierd": b"UAE_FALCAD", "proj_hier": b"UAE_MSL_A",
        "tex": "Uae_FalconP.tga", "body": (56, 108, 188), "nose": NOSE_W,
        "expect": "blue", "km": 1000, "kg": 400, "acc": 60, "stealth": 30,
        "rebuild": 18, "price": 900,
    },
    {
        "slot": "B", "object": "UAE_Barq", "name": "Barq",
        "model": "Uae_Barq", "modeld": "Uae_BarqD", "proj_model": "Uae_BarqM",
        "hier": b"UAE_BARQB", "hierd": b"UAE_BARQBD", "proj_hier": b"UAE_MSL_B",
        "tex": "Uae_BarqP.tga", "body": (8, 162, 56), "nose": NOSE_W,
        "expect": "green", "km": 1100, "kg": 800, "acc": 45, "stealth": 40,
        "rebuild": 23, "price": 1400,
    },
    {
        "slot": "C", "object": "UAE_Liwa", "name": "Liwa",
        "model": "Uae_Liwa", "modeld": "Uae_LiwaD", "proj_model": "Uae_LiwaM",
        "hier": b"UAE_LIWAC", "hierd": b"UAE_LIWACD", "proj_hier": b"UAE_MSL_C",
        "tex": "Uae_LiwaP.tga", "body": (228, 176, 40), "nose": NOSE_R,
        "expect": "yellow", "km": 1300, "kg": 600, "acc": 75, "stealth": 25,
        "rebuild": 28, "price": 1800,
    },
    {
        "slot": "D", "object": "UAE_Dhafra", "name": "Dhafra",
        "model": "Uae_Dhafra", "modeld": "Uae_DhafraD", "proj_model": "Uae_DhafraM",
        "hier": b"UAE_DHAFR", "hierd": b"UAE_DHAFRD", "proj_hier": b"UAE_MSL_D",
        "tex": "Uae_DhafraP.tga", "body": (188, 20, 44), "nose": NOSE_W,
        "expect": "red", "km": 1500, "kg": 1500, "acc": 35, "stealth": 55,
        "rebuild": 34, "price": 2500,
    },
    {
        "slot": "E", "object": "UAE_AlAin", "name": "Al Ain",
        "model": "Uae_AlAin", "modeld": "Uae_AlAinD", "proj_model": "Uae_AlAinM",
        "hier": b"UAE_ALAIN", "hierd": b"UAE_ALAIND", "proj_hier": b"UAE_MSL_E",
        "tex": "Uae_AlAinP.tga", "body": (8, 140, 132), "nose": NOSE_W,
        "expect": "petrol", "km": 1800, "kg": 1200, "acc": 65, "stealth": 35,
        "rebuild": 41, "price": 3300,
    },
    {
        "slot": "F", "object": "UAE_Buraq", "name": "Buraq",
        "model": "Uae_Buraq", "modeld": "Uae_BuraqD", "proj_model": "Uae_BuraqM",
        "hier": b"UAE_BURAQ", "hierd": b"UAE_BURAQD", "proj_hier": b"UAE_MSL_F",
        "tex": "Uae_BuraqP.tga", "body": (176, 32, 96), "nose": NOSE_W,
        "expect": "other", "km": 2100, "kg": 2500, "acc": 30, "stealth": 50,
        "rebuild": 50, "price": 4600,
    },
    {
        "slot": "G", "object": "UAE_Siraj", "name": "Siraj",
        "model": "Uae_Siraj", "modeld": "Uae_SirajD", "proj_model": "Uae_SirajM",
        "hier": b"UAE_SIRAJ", "hierd": b"UAE_SIRAJD", "proj_hier": b"UAE_MSL_G",
        "tex": "Uae_SirajP.tga", "body": (232, 124, 16), "nose": NOSE_G,
        "expect": "orange", "km": 2400, "kg": 1800, "acc": 50, "stealth": 70,
        "rebuild": 58, "price": 5500,
    },
    {
        "slot": "H", "object": "UAE_Mezyad", "name": "Mezyad",
        "model": "Uae_Mezyad", "modeld": "Uae_MezyadD", "proj_model": "Uae_MezyadM",
        "hier": b"UAE_MEZYA", "hierd": b"UAE_MEZYAD", "proj_hier": b"UAE_MSL_H",
        "tex": "Uae_MezyadP.tga", "body": (186, 168, 142), "nose": NOSE_R,
        "expect": "cream", "km": 2800, "kg": 3500, "acc": 25, "stealth": 45,
        "rebuild": 70, "price": 7200,
    },
    {
        "slot": "I", "object": "UAE_Qamar", "name": "Qamar",
        "model": "Uae_Qamar", "modeld": "Uae_QamarD", "proj_model": "Uae_QamarM",
        "hier": b"UAE_QAMAR", "hierd": b"UAE_QAMARD", "proj_hier": b"UAE_MSL_I",
        "tex": "Uae_QamarP.tga", "body": (116, 120, 128), "nose": NOSE_W,
        "expect": "gray", "km": 3400, "kg": 5000, "acc": 70, "stealth": 55,
        "rebuild": 82, "price": 8700,
    },
    {
        "slot": "J", "object": "UAE_AlWatan", "name": "Al Watan",
        "model": "Uae_AlWatan", "modeld": "Uae_AlWatanD", "proj_model": "Uae_AlWatanM",
        "hier": b"UAE_WATAN", "hierd": b"UAE_WATAND", "proj_hier": b"UAE_MSL_J",
        "tex": "Uae_AlWatanP.tga", "body": (30, 28, 26), "nose": NOSE_R,
        "expect": "black", "km": 4000, "kg": 7000, "acc": 20, "stealth": 30,
        "rebuild": 98, "price": 11000,
    },
]

NAME_MAP = [
    "A Falcon new (no accepted UAE factory identity)",
    "B Barq new as UAE_Barq (SaudiArabia_Barq remains Saudi slot D; different object id)",
    "C Liwa new",
    "D Dhafra new",
    "E Al Ain new",
    "F Buraq new",
    "G Siraj new",
    "H Mezyad new",
    "I Qamar new",
    "J Al Watan new",
]

FROZEN_DATA = list(sa.FROZEN_DATA) + [
    sa.SA_FAC_KEY, sa.SA_CB_KEY, sa.SA_CS_KEY, sa.SA_WEP_KEY,
    UAE_VT72B_KEY, UAE_DOZER_KEY, UAE_SHAHEEN_KEY, UAE_ABABEEL_KEY,
    UAE_ALHUSS_KEY, UAE_WEP_OLD_KEY, UAE_MIC_KEY,
]
FROZEN_DATA += [m["unit_key"] for m in sa.DERIVED]
FROZEN_DATA += [m["proj_key"] for m in sa.DERIVED]

FROZEN_ART = list(sa.FROZEN_ART) + [
    sa.TRUCK_KEY, sa.TRUCKD_KEY, UAE_FLAG_KEY,
    r"Art\Textures\Sau_NajmP.tga", r"Art\W3D\Sau_Najm.W3D",
    r"Art\Textures\Sau_BarqP.tga", r"Art\W3D\Sau_Barq.W3D",
]
FROZEN_ART += [m["tex_key"] for m in sa.DERIVED]
FROZEN_ART += [m["tel_key"] for m in sa.DERIVED]
FROZEN_ART += [m["teld_key"] for m in sa.DERIVED]
FROZEN_ART += [m["projw_key"] for m in sa.DERIVED]

for _m in MISSILES:
    assert len(_m["hier"]) == 9 and len(_m["hierd"]) == 10 and len(_m["proj_hier"]) == 9
    assert 1000 <= _m["km"] <= 4000 and 400 <= _m["kg"] <= 10000


def derived(m: dict) -> dict:
    d = sk.derived({**m, "min_range": sk.MOTHER_MIN_RANGE})
    d["button"] = f"CB_UAE_MISSILE_{m['slot']}"
    d["unit_key"] = (
        r"Data\INI\Object\Specter\United Arab Emirates Armed Forces"
        rf"\Wheeled\{m['object']}.ini"
    )
    d["proj_key"] = (
        r"Data\INI\Object\Specter\United Arab Emirates Armed Forces"
        rf"\{m['object']}_Projectile.ini"
    )
    return d


DERIVED = [derived(m) for m in MISSILES]


def make_uae_flag() -> Image.Image:
    """UAE flag: vertical red hoist, then horizontal green / white / black stripes."""
    w, h = 900, 600
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    draw = ImageDraw.Draw(im)
    red_w = int(w * 0.25)
    stripe = h / 3.0
    draw.rectangle([red_w, 0, w, int(round(stripe))], fill=(0, 115, 47, 255))
    draw.rectangle([red_w, int(round(stripe)), w, int(round(stripe * 2))], fill=(255, 255, 255, 255))
    draw.rectangle([red_w, int(round(stripe * 2)), w, h], fill=(0, 0, 0, 255))
    draw.rectangle([0, 0, red_w, h], fill=(200, 16, 46, 255))
    return im


def has_uae_flag(counts: dict[str, int]) -> bool:
    # Official UAE green (~0,115,47) classifies as muddy before green.
    greenish = counts.get("green", 0) + counts.get("muddy", 0)
    return (
        counts.get("red", 0) >= 4
        and counts.get("white", 0) >= 3
        and greenish >= 3
        and counts.get("black", 0) >= 2
    )


def recolor_truck(src: Image.Image, damaged: bool = False) -> Image.Image:
    """Map Iraqi tan sheet to UAE pearl-sand / stone / steel. Not Saudi olive."""
    im = src.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            avg = (r + g + b) / 3.0
            sat = max(r, g, b) - min(r, g, b)
            if avg < 55 and sat < 35:
                px[x, y] = (max(0, int(r * 0.34)), max(0, int(g * 0.34)), max(0, int(b * 0.32)), a)
                continue
            if sat > 70 and avg > 70:
                base = STEEL
                t = 0.94
            elif avg < 100:
                base = STONE
                t = max(0.70, min(1.15, avg / 90.0))
            else:
                base = PEARL
                t = max(0.55, min(1.25, avg / 130.0))
            nr = min(255, int(base[0] * t))
            ng = min(255, int(base[1] * t))
            nb = min(255, int(base[2] * t))
            if damaged:
                nr, ng, nb = int(nr * 0.72), int(ng * 0.70), int(nb * 0.64)
            px[x, y] = (nr, ng, nb, a)
    return im


def make_uae_tel_w3d(src: bytes, damaged: bool, m: dict) -> bytes:
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
        .replace("South Korea", "United Arab Emirates")
        .replace("Side = SouthKorea", "Side = UAE")
        .replace(
            "Skr_TEL / Skr_TELD (not Irq_9P117 / Jpn_TEL)",
            "Uae_TEL / Uae_TELD (not Irq_9P117 / Jpn_TEL / Skr_TEL / Sau_TEL)",
        )
    )


def projectile_ini(m: dict) -> str:
    return sk.projectile_ini(m).replace("South Korea", "United Arab Emirates")


def weapon_file(missiles: list[dict]) -> str:
    head = (
        WEP_MARKER + "\n"
        "; 9P117 scale. Dedicated UAE A-J. Distinct from Saudi/Vietnam/Japan/SK/Iraq.\n"
        "; ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000 (PR #629).\n"
        "; Death HACK is a separate path and is not folded into PrimaryDamage.\n"
        "; Acc/CHL columns are design labels mapped to ScatterRadius / MaxHealth.\n"
    )
    body = sk.weapon_blocks(missiles)
    pairs = body.split("\n\n", 1)[1] if "\n\n" in body else body
    return head + "\n" + pairs


def factory_ini() -> str:
    text = sk.factory_ini()
    text = text.replace("; South Korea missile factory.", "; United Arab Emirates missile factory.")
    text = text.replace(
        "with a SouthKorea-only CommandSet (A-J).",
        "with a UAE-only CommandSet (A-J).",
    )
    text = text.replace("Object SouthKorea_MissileFactory", "Object UAE_MissileFactory")
    text = text.replace(
        "DisplayName      = OBJECT:SouthKoreaMissileFactory",
        "DisplayName      = OBJECT:UAEMissileFactory",
    )
    text = text.replace("Side             = SouthKorea", "Side             = UAE")
    text = text.replace(
        "CommandSet       = SouthKorea_MissileFactoryCommandSet",
        "CommandSet       = UAE_MissileFactoryCommandSet",
    )
    return text


def factory_commandset() -> str:
    slots = "\r\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(DERIVED, start=1))
    return (
        "CommandSet UAE_MissileFactoryCommandSet\r\n"
        f"{slots}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def with_uae_factory(block: str) -> str:
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in block:
        raise SystemExit(f"expected isolated Iraq factory in:\n{block}")
    if "Command_ConstructUAE_MissileFactory" in block:
        raise SystemExit("UAE factory already present on builder")
    return block.replace(
        "Command_ConstructIraq_AlFahdMissileFactoryBuilding",
        "Command_ConstructUAE_MissileFactory",
    )


def commandbutton_all() -> str:
    lines = [
        "; United Arab Emirates missiles A-J production buttons and factory construct button.",
        "; Shared specter_missile_* cameos. Unique Object bindings.",
        "",
        "CommandButton Command_ConstructUAE_MissileFactory",
        "  Command          = DOZER_CONSTRUCT",
        "  Object           = UAE_MissileFactory",
        "  TextLabel        = CONTROLBAR:ConstructUAEMissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel    = CONTROLBAR:ToolTipUAEMissileFactory",
        "End",
        "",
    ]
    for m in DERIVED:
        lines.extend(
            [
                f"CommandButton {m['button']}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {m['object']}",
                f"  TextLabel     = CONTROLBAR:UAEMissile{m['slot']}",
                f"  ButtonImage   = {m['cameo']}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTipUAEMissile{m['slot']}",
                "End",
                "",
            ]
        )
    return "\n".join(lines)


def commandset_file(builders: dict[str, str]) -> str:
    parts = [builders[name] for name in BUILDERS]
    parts.append(factory_commandset())
    return "\r\n\r\n".join(parts) + "\r\n"


def csf_map() -> dict[str, str]:
    mapping = {
        "OBJECT:UAEMissileFactory": "Missile Factory",
        "CONTROLBAR:ConstructUAEMissileFactory": "Missile Factory",
        "CONTROLBAR:ToolTipUAEMissileFactory": (
            "Missile Factory\nProduces UAE missiles A-J\nPrice: $1800"
        ),
    }
    for m in DERIVED:
        mapping[f"OBJECT:{m['object']}"] = m["name"]
        mapping[f"CONTROLBAR:UAEMissile{m['slot']}"] = m["name"]
        mapping[f"CONTROLBAR:ToolTipUAEMissile{m['slot']}"] = m["tooltip"]
    return mapping


def mapping_report() -> list[str]:
    lines = [
        "NAME MAPPING:",
        *[f"  {row}" for row in NAME_MAP],
        "",
        "EXISTING UAE MISSILE OBJECTS PRESERVED (not factory A-J):",
        "  UAE_ShaheenTEL / UAE_Weapon_Shaheen",
        "  UAE_AbabeelTEL / UAE_Weapon_Ababeel",
        "  UAE_Alhussaien (AbbasLauncher.ini)",
        "",
        "FACTORY CONSTRUCT:",
        "  Pre-change Dozer/Worker/VT72B constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  Post-change those menus construct UAE_MissileFactory.",
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
    sat_cs = data[UAE_CS_KEY].decode("latin1")

    if "ZZZZ" in UAE_CB_KEY or "ZZZZ" in UAE_CS_KEY or "ZZZZ" in UAE_WEP_KEY:
        fails.append("ZZZZ shortcut")
    if r"Data\INI\CommandSet_UAE.ini" in data and data[r"Data\INI\CommandSet_UAE.ini"] != src_data.get(
        r"Data\INI\CommandSet_UAE.ini"
    ):
        fails.append("stale CommandSet_UAE.ini packed")
    if UAE_CS_KEY >= r"Data\INI\CommandSet_ZZZZ":
        fails.append("UAE satellite sorts into ZZZZ")
    if UAE_CS_KEY <= CS_KEY:
        fails.append("UAE satellite sorts before CommandSet.ini")

    for frozen_cs in (
        "Iraq_AlFahdMissileFactoryCommandSet",
        "Vietnam_MissileFactoryCommandSet",
        "Vietnam_VT72BCommandSet",
        "Japan_MissileFactoryCommandSet",
        "Japan_VT72BCommandSet",
        "SouthKorea_MissileFactoryCommandSet",
        "SouthKorea_VT72BCommandSet",
        "SaudiArabia_MissileFactoryCommandSet",
        "SaudiArabiaDozerCommandSet",
        "SaudiArabia_WorkerCommandSet",
        "SaudiArabia_VT72BCommandSet",
    ):
        if sk.last_block(cs_text, "CommandSet", frozen_cs) != sk.last_block(
            src_cs, "CommandSet", frozen_cs
        ):
            fails.append(f"{frozen_cs} mutated in CommandSet.ini")

    for name in BUILDERS:
        new_b = sk.last_block(cs_text, "CommandSet", name)
        if "Command_ConstructUAE_MissileFactory" not in new_b:
            fails.append(f"{name} catalog missing UAE factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in new_b:
            fails.append(f"{name} still has isolated Iraq factory")
        if "Command_ConstructUAE_MIC" not in new_b:
            fails.append(f"{name} lost MIC")
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", name)
        if "Command_ConstructUAE_MissileFactory" not in lw:
            fails.append(f"last-wins {name} from {_k} missing UAE factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in lw:
            fails.append(f"last-wins {name} still Iraq factory")
        if name not in sat_cs:
            fails.append(f"satellite missing {name}")

    fac = sk.last_block(cs_text, "CommandSet", "UAE_MissileFactoryCommandSet")
    if not fac:
        fails.append("CommandSet.ini missing UAE factory roster")
    slots = re.findall(r"CB_UAE_MISSILE_([A-Z])", fac)
    if slots != list("ABCDEFGHIJ"):
        fails.append(f"factory slots {slots} != A-J")
    if "Command_Sell" not in fac or "Command_SetRallyPoint" not in fac:
        fails.append("factory missing Rally/Sell")
    if any(tag in fac for tag in ("CB_VIETNAM_", "CB_JAPAN_", "CB_SOUTHKOREA_", "CB_SAUDIARABIA_")):
        fails.append("factory mixed foreign buttons")

    construct = sk.last_block(cb_text, "CommandButton", "Command_ConstructUAE_MissileFactory")
    if sk.field(construct, "Object") != "UAE_MissileFactory":
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
    ):
        if sk.field(sk.last_block(cb_text, "CommandButton", btn), "ButtonImage") != img:
            fails.append(f"{btn} image lost")
        if sk.last_block(cb_text, "CommandButton", btn) != sk.last_block(src_cb, "CommandButton", btn):
            fails.append(f"{btn} mutated")

    fac_obj = sk.last_block(data[UAE_FAC_KEY].decode("latin1"), "Object", "UAE_MissileFactory")
    if sk.field(fac_obj, "Side") != "UAE":
        fails.append("factory Side")
    if sk.field(fac_obj, "CommandSet") != "UAE_MissileFactoryCommandSet":
        fails.append("factory object CommandSet")
    if "SouthKorea_SupplyCenter" not in fac_obj:
        fails.append("factory lost SouthKorea_SupplyCenter prereq")
    if "UAE_SupplyCenter" not in fac_obj:
        fails.append("factory missing UAE_SupplyCenter prereq")

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
    if sk.last_block(wep_text, "Weapon", "Weapon_Iraq_AlFahd500") != sk.last_block(
        src_wep, "Weapon", "Weapon_Iraq_AlFahd500"
    ):
        fails.append("AlFahd weapon mutated")
    if sk.last_block(data[UAE_WEP_OLD_KEY].decode("latin1"), "Weapon", "UAE_Weapon_Shaheen") != sk.last_block(
        src_data[UAE_WEP_OLD_KEY].decode("latin1"), "Weapon", "UAE_Weapon_Shaheen"
    ):
        fails.append("UAE Shaheen weapon mutated")

    if sk.illegal_floats(wep_text):
        fails.append(f"illegal floats {sk.illegal_floats(wep_text)}")

    r11 = sk.last_block(data[sk.R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB")
    if sk.field(r11, "BuildCost") != "1200":
        fails.append("9P117 BuildCost")

    sa_fac = sk.last_block(
        data[sa.SA_FAC_KEY].decode("latin1"), "Object", "SaudiArabia_MissileFactory"
    )
    if sk.field(sa_fac, "Side") != "SaudiArabia":
        fails.append("Saudi factory Side mutated")

    csf = data[CSF_KEY]
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

    wep_sat = data[UAE_WEP_KEY].decode("latin1")
    baseline_objects = set()
    obj_re = re.compile(rb"^Object (\S+)", re.M)
    for key, blob in src_data.items():
        if key.endswith(".ini") or key.endswith(".INI"):
            baseline_objects.update(mo.group(1).decode("ascii", "ignore") for mo in obj_re.finditer(blob))
    seen_objects = set()
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
        if sk.field(unit, "Side") != "UAE":
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
        if "UAE_ShaheenTEL" in unit or "UAE_Alhussaien" in unit or "SaudiArabia_Barq" in unit:
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
        if sk.csf_get(csf, f"CONTROLBAR:UAEMissile{m['slot']}") != m["name"]:
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
        if any(x in tel_tex for x in ("Skr_TEL.tga", "Jpn_TEL.tga", "Sau_TEL.tga")):
            fails.append(f"{m['slot']} foreign truck")

        im = Image.open(io.BytesIO(art[m["tex_key"]])).convert("RGB")
        tel_flag = sk.region_mode(im, (110, 180, 420, 290))
        if not has_uae_flag(tel_flag):
            fails.append(f"{m['slot']} UAE flag {tel_flag}")
        if not sk.has_name_plate(im, (500, 190, 960, 280)):
            fails.append(f"{m['slot']} TEL name")
        body = sk.region_mode(im, (80, 410, 200, 560))
        top = max(body, key=body.get)
        allowed = {
            "blue": {"blue", "petrol"},
            "green": {"green", "muddy"},
            "yellow": {"yellow", "orange", "cream"},
            "red": {"red", "orange"},
            "petrol": {"petrol", "blue", "green"},
            "other": {"other", "red", "blue"},
            "orange": {"orange", "red", "yellow"},
            "cream": {"cream", "white", "yellow"},
            "gray": {"gray", "white", "dark"},
            "black": {"black", "dark", "gray"},
        }
        if top not in allowed[m["expect"]] and top != m["expect"]:
            if m["expect"] == "black" and top in {"black", "dark", "other"}:
                pass
            else:
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
    fac_dir = LOOSE / "Object/Specter/United Arab Emirates Armed Forces/Buildings"
    wheel_dir = LOOSE / "Object/Specter/United Arab Emirates Armed Forces/Wheeled"
    proj_dir = LOOSE / "Object/Specter/United Arab Emirates Armed Forces"
    wep_dir = LOOSE / "Weapon"
    for d in (fac_dir, wheel_dir, proj_dir, wep_dir):
        d.mkdir(parents=True, exist_ok=True)
    (fac_dir / "UAE_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    (wep_dir / "Weapon_UAE_Missiles.ini").write_text(weapon_file(DERIVED), encoding="utf-8")
    (LOOSE / "CommandButton_UAEMissiles.ini").write_text(commandbutton_all(), encoding="utf-8")
    (LOOSE / "CommandSet_UAEMissiles.ini").write_text(commandset_file(builders), encoding="utf-8")
    for m in DERIVED:
        (wheel_dir / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (proj_dir / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_SA or SRC_DATA.stat().st_size != SIZE_DATA_SA:
        raise SystemExit("DATA baseline is not SPECTER_SAUDI_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_SA or SRC_ART.stat().st_size != SIZE_ART_SA:
        raise SystemExit("ART baseline is not SPECTER_SAUDI_MISSILES_AJ")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art = sk.parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    flag = make_uae_flag()
    truck = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])), damaged=False)
    truckd = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCKD_DDS])), damaged=True)
    art[TRUCK_KEY] = sk.make_tga32(truck)
    art[TRUCKD_KEY] = sk.make_tga32(truckd)

    for m in DERIVED:
        skin = sk.make_skin(m["body"], m["nose"], m["name"], flag)
        art[m["tex_key"]] = sk.make_tga32(skin)
        art[m["tel_key"]] = make_uae_tel_w3d(src_art[TEL_W3D], False, m)
        art[m["teld_key"]] = make_uae_tel_w3d(src_art[TELD_W3D], True, m)
        art[m["projw_key"]] = sk.make_proj_w3d(src_art[PROJ_W3D], m)
        data[m["unit_key"]] = sk.to_crlf(unit_ini(m))
        data[m["proj_key"]] = sk.to_crlf(projectile_ini(m))

    data[UAE_FAC_KEY] = sk.to_crlf(factory_ini())
    data[UAE_WEP_KEY] = sk.to_crlf(weapon_file(DERIVED))
    data[UAE_CB_KEY] = sk.to_crlf(commandbutton_all())
    data[CSF_KEY] = sk.csf_upsert(src_data[CSF_KEY], csf_map())

    cs = src_data[CS_KEY].decode("latin1")
    builders = {}
    for name in BUILDERS:
        old = sk.last_block(cs, "CommandSet", name)
        new = with_uae_factory(old)
        builders[name] = new
        cs = sk.replace_last(cs, "CommandSet", name, new)
    if sk.last_block(cs, "CommandSet", "UAE_MissileFactoryCommandSet"):
        cs = sk.replace_last(cs, "CommandSet", "UAE_MissileFactoryCommandSet", factory_commandset())
    else:
        cs = cs.rstrip("\r\n") + "\r\n\r\n" + factory_commandset() + "\r\n"
    data[CS_KEY] = cs.encode("latin1")
    data[UAE_CS_KEY] = sk.to_crlf(commandset_file(builders))

    cb = src_data[CB_KEY].decode("latin1")
    if "CommandButton Command_ConstructUAE_MissileFactory" in cb:
        raise SystemExit("CommandButton.ini already had UAE factory")
    extra = commandbutton_all().replace("\n", "\r\n")
    data[CB_KEY] = (cb.rstrip("\r\n") + "\r\n\r\n" + extra + "\r\n").encode("latin1")

    wep = src_data[WEAPON_KEY].decode("latin1")
    if WEP_MARKER in wep or "Weapon Weapon_UAE_Falcon" in wep:
        raise SystemExit("Weapon.ini already had UAE A-J")
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
    (ext / "CommandSet.ini.UAE.txt").write_text(
        "\r\n\r\n".join(sk.last_block(packed_cs, "CommandSet", n) for n in BUILDERS)
        + "\r\n\r\n"
        + sk.last_block(packed_cs, "CommandSet", "UAE_MissileFactoryCommandSet")
        + "\r\n",
        encoding="utf-8",
    )
    (ext / "Weapon.ini.UAE.txt").write_text(weapon_file(DERIVED), encoding="utf-8")
    (ext / "UAE_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    for m in DERIVED:
        (ext / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (ext / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    preview = OUT / "PREVIEW"
    preview.mkdir()
    flag.save(preview / "UAEFlag.png")
    truck.save(preview / "Uae_TEL.png")
    truckd.save(preview / "Uae_TELD.png")
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
    zip_path = ROOT / "patch/Release/SPECTER_UAE_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    inv = [
        "PRE-CHANGE UAE (packed last-wins, Saudi A-J baseline):",
        "  No UAE_MissileFactory.",
        "  Dozer/Worker/VT72B constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  MIC on slot 6. Existing ShaheenTEL / AbabeelTEL / Alhussaien preserved.",
        "  Packed faction path: United Arab Emirates Armed Forces. Side=UAE.",
        "",
        "POST-CHANGE UAE:",
        "  Dedicated UAE_MissileFactory A-J + Rally/Sell.",
        "  Builder slot that held the isolated Iraq factory now builds the UAE factory.",
        "  UAE_Barq is a new UAE object and does not replace SaudiArabia_Barq.",
        "",
        *map_lines,
    ]
    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #633 s-saudi-missiles-aj + PR #632 + #631 + #630 + #629",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "UAE_FACTORY_NEW=YES",
        "SHAHEEN_ABABEEL_ALHUSS_KEPT=YES",
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
        "KG_CEILING_USED=7000",
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
            "ZIP_FILE=SPECTER_UAE_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #633",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-uae-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-uae-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-uae-missiles-aj/SPECTER_UAE_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-uae-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-uae-missiles-aj",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "United Arab Emirates complete missile roster A-J on the accepted factory/fire path.\n"
        "New country factory replaces the isolated Iraq factory construct on UAE builders.\n"
        "Existing ShaheenTEL, AbabeelTEL, and Alhussaien are unchanged.\n"
        "Saudi A-J, Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# United Arab Emirates missiles A-J\n\n"
        "- New UAE_MissileFactory. Rally/Sell retained.\n"
        "- Replaces isolated Iraq factory construct on UAE Dozer, Worker, and VT72B.\n"
        "- MIC, Abbas, Lgm30, ShaheenTEL, AbabeelTEL, and Alhussaien preserved.\n"
        "- UAE flag (red hoist, green/white/black stripes) + exact names on dorsal UV bands.\n"
        "- Dedicated Uae_TEL pearl-sand truck. Ten-color tube palette distinct from Saudi.\n"
        "- 5-minute clip reload on all ten PRIMARY weapons.\n"
        "- Saudi A-J, Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n", encoding="utf-8")
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_UAEMissiles.ini last-wins UAE builder + factory CommandSets.\n"
        "CommandButton_UAEMissiles.ini last-wins construct + A-J.\n"
        "Weapon\\Weapon_UAE_Missiles.ini last-wins Weapon_UAE_* factory pair.\n"
        "Weapon_UAE.ini (Shaheen/Ababeel and other UAE weapons) is unchanged.\n"
        "UAE_Barq is not SaudiArabia_Barq. Existing UAE_Flag.tga is unchanged.\n"
        "Saudi, Vietnam, Japan, South Korea, Iraq, and 9P117 packed definitions are unchanged.\n"
    )
    art_notes = [
        "UAE A-J ART MARKINGS (static inspection)",
        "",
        "Flag: vertical red hoist, horizontal green / white / black stripes.",
        "Dedicated Uae_TEL / Uae_TELD pearl-sand truck. Not Irq_9P117 / Skr_TEL / Jpn_TEL / Sau_TEL.",
        "Existing Art\\Textures\\UAE_Flag.tga is frozen and not overwritten.",
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
