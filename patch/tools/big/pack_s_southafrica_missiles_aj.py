#!/usr/bin/env python3
"""Implement South Africa missile roster A-J on the Syria / Libya path.

Baseline: packed SPECTER_SYRIA_MISSILES_AJ (PR #637 + #636 + #635 + UAE/Saudi/VN/SK/Japan).

South Africa has no missile factory. Dozer / Worker / VT72B slot 13 currently
constructs the isolated Sell-only Iraq_AlFahdMissileFactoryBuilding. Replace that
slot with a SouthAfrica-only factory. Keep MIC on slot 6.

Preserve existing SouthAfrica_ShaheenTEL, SouthAfrica_AbabeelTEL, and
SouthAfrica_Alhussaien. Packed faction path is South African National Defence
Force. Side=SouthAfrica.

The A-J ballistic TEL roster is fictional SPECTER content. South Africa has no
current operational ballistic-missile force. Public history that informs the
profile: cancelled RSA-1/2/3 program, Denel guided weapons (Mokopa, Ingwe,
Umbani, Raptor, Umkhonto, Skerpioen), Valkiri MLRS, Overberg Test Range.
Do not treat in-game km/kg/Acc/CHL as verified military specifications.

Profile vs Syria: better precision (guided-weapon industry), similar regional
reach, lighter warheads, RSA-3 analogue cap below Libya/UAE/Saudi J-class.

Syria A-J, Libya A-J, UAE A-J, Saudi A-J, Vietnam A-J, Japan A-J, South Korea
A-J, Iraq A-M, and 9P117 stay frozen.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Satellite last-wins: CommandSet_SouthAfricaMissiles.ini,
CommandButton_SouthAfricaMissiles.ini, Weapon\\Weapon_SouthAfrica_Missiles.ini.
South Africa flag (Y/pall: black/gold/green/white/red/blue) + names on dorsal UV.
Dedicated Saf_TEL veld truck. No RadarPriority. No rearm. No ZZZZ.
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

SRC_DATA = ROOT / "patch/Release/SPECTER_SYRIA_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_SYRIA_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_SOUTHAFRICA_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SYR = "7bf022bfb3553f269a01ff3c8fccd24e848fe4631d45e71e43691c8517507a75"
SIZE_DATA_SYR = 367847106
SHA_ART_SYR = "92905fd2cfc9b98a5ce398d68c426c16e313f55a009354a2f6004d623ed6214f"
SIZE_ART_SYR = 1639335694

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

SAF_CB_KEY = r"Data\INI\CommandButton_SouthAfricaMissiles.ini"
SAF_CS_KEY = r"Data\INI\CommandSet_SouthAfricaMissiles.ini"
SAF_WEP_KEY = r"Data\INI\Weapon\Weapon_SouthAfrica_Missiles.ini"
SAF_FAC_KEY = (
    r"Data\INI\Object\Specter\South African National Defence Force"
    r"\Buildings\SouthAfrica_MissileFactory.ini"
)
SAF_VT72B_KEY = (
    r"Data\INI\Object\Specter\South African National Defence Force\Tracked\VT72B.ini"
)
SAF_DOZER_KEY = (
    r"Data\INI\Object\Specter\South African National Defence Force"
    r"\Tracked\SouthAfrica_Dozer.ini"
)
SAF_SHAHEEN_KEY = (
    r"Data\INI\Object\Specter\South African National Defence Force"
    r"\Wheeled\SouthAfrica_ShaheenTEL.ini"
)
SAF_ABABEEL_KEY = (
    r"Data\INI\Object\Specter\South African National Defence Force"
    r"\Wheeled\SouthAfrica_AbabeelTEL.ini"
)
SAF_ALHUSS_KEY = (
    r"Data\INI\Object\Specter\South African National Defence Force"
    r"\Wheeled\AbbasLauncher.ini"
)
SAF_WEP_OLD_KEY = r"Data\INI\Weapon_SouthAfrica.ini"
SAF_MIC_KEY = (
    r"Data\INI\Object\Specter\South African National Defence Force"
    r"\Buildings\SouthAfrica_MIC.ini"
)
SAF_LGM_KEY = (
    r"Data\INI\Object\Specter\South African National Defence Force"
    r"\Buildings\SouthAfrica_Lgm30.ini"
)
SAF_ZZZ_CS = r"Data\INI\CommandSet_ZZZZ_AfricaPakistanSyria_AirExp.ini"
SAF_ZZZ_CB = r"Data\INI\CommandButton_ZZZZ_AfricaPakistanSyria_AirExp.ini"

TRUCK_TEX = "Saf_TEL.tga"
TRUCKD_TEX = "Saf_TELD.tga"
TRUCK_KEY = rf"Art\Textures\{TRUCK_TEX}"
TRUCKD_KEY = rf"Art\Textures\{TRUCKD_TEX}"

WEP_MARKER = (
    "; ===== South Africa missiles A-J "
    "(Weapon.ini load path for Command_FireMainWeapon) ====="
)

BUILDERS = [
    "SouthAfricaDozerCommandSet",
    "SouthAfrica_WorkerCommandSet",
    "SouthAfrica_VT72BCommandSet",
]

VELD = (124, 108, 52)
EARTH = (84, 70, 40)
SOOT = (48, 40, 32)
NOSE_W = (236, 228, 210)
NOSE_R = (196, 16, 28)
NOSE_G = (0, 140, 64)

# Distinct slot-to-color map vs Syria/Libya/UAE/Saudi. Veld truck + Y/pall flag.
# Gameplay values are SPECTER design, informed by public mission class, not claimed specs.
MISSILES = [
    {
        "slot": "A", "object": "SouthAfrica_Mokopa", "name": "Mokopa",
        "model": "Saf_Mokopa", "modeld": "Saf_MokopaD", "proj_model": "Saf_MokopaM",
        "hier": b"SAF_MOKPA", "hierd": b"SAF_MOKPAD", "proj_hier": b"SAF_MSL_A",
        "tex": "Saf_MokopaP.tga", "body": (8, 162, 56), "nose": NOSE_W,
        "expect": "green", "km": 1000, "kg": 400, "acc": 70, "stealth": 22,
        "rebuild": 17, "price": 900,
        "role": "Tactical precision analogue (Mokopa ATGM heritage; game floor 1000 km)",
    },
    {
        "slot": "B", "object": "SouthAfrica_Valkiri", "name": "Valkiri",
        "model": "Saf_Valkiri", "modeld": "Saf_ValkiriD", "proj_model": "Saf_ValkiriM",
        "hier": b"SAF_VALKB", "hierd": b"SAF_VALKBD", "proj_hier": b"SAF_MSL_B",
        "tex": "Saf_ValkiriP.tga", "body": (210, 108, 22), "nose": NOSE_W,
        "expect": "orange", "km": 1050, "kg": 450, "acc": 35, "stealth": 18,
        "rebuild": 18, "price": 850,
        "role": "Area rocket analogue (Valkiri MLRS heritage; unguided, cheap)",
    },
    {
        "slot": "C", "object": "SouthAfrica_Ingwe", "name": "Ingwe",
        "model": "Saf_Ingwe", "modeld": "Saf_IngweD", "proj_model": "Saf_IngweM",
        "hier": b"SAF_INGWC", "hierd": b"SAF_INGWCD", "proj_hier": b"SAF_MSL_C",
        "tex": "Saf_IngweP.tga", "body": (222, 182, 28), "nose": NOSE_W,
        "expect": "yellow", "km": 1100, "kg": 400, "acc": 72, "stealth": 24,
        "rebuild": 20, "price": 1100,
        "role": "Guided tactical analogue (Ingwe ATGM heritage)",
    },
    {
        "slot": "D", "object": "SouthAfrica_Skerpioen", "name": "Skerpioen",
        "model": "Saf_Skerpioen", "modeld": "Saf_SkerpioenD", "proj_model": "Saf_SkerpioenM",
        "hier": b"SAF_SKERD", "hierd": b"SAF_SKERDD", "proj_hier": b"SAF_MSL_D",
        "tex": "Saf_SkerpioenP.tga", "body": (28, 68, 168), "nose": NOSE_W,
        "expect": "blue", "km": 1200, "kg": 400, "acc": 76, "stealth": 52,
        "rebuild": 28, "price": 2800,
        "role": "Coastal/anti-ship analogue (Skerpioen/Gabriel heritage; MaxHealth proxy)",
    },
    {
        "slot": "E", "object": "SouthAfrica_Raptor", "name": "Raptor",
        "model": "Saf_Raptor", "modeld": "Saf_RaptorD", "proj_model": "Saf_RaptorM",
        "hier": b"SAF_RAPTE", "hierd": b"SAF_RAPTED", "proj_hier": b"SAF_MSL_E",
        "tex": "Saf_RaptorP.tga", "body": (228, 224, 216), "nose": NOSE_G,
        "expect": "white", "km": 1300, "kg": 500, "acc": 80, "stealth": 30,
        "rebuild": 30, "price": 2500,
        "role": "Precision strike analogue (Denel Raptor glide-PGM heritage)",
    },
    {
        "slot": "F", "object": "SouthAfrica_Overberg", "name": "Overberg",
        "model": "Saf_Overberg", "modeld": "Saf_OverbergD", "proj_model": "Saf_OverbergM",
        "hier": b"SAF_OVERF", "hierd": b"SAF_OVERFD", "proj_hier": b"SAF_MSL_F",
        "tex": "Saf_OverbergP.tga", "body": (220, 200, 155), "nose": NOSE_R,
        "expect": "cream", "km": 1500, "kg": 700, "acc": 55, "stealth": 28,
        "rebuild": 36, "price": 2700,
        "role": "Fictional SRBM named for Overberg Test Range; conservative regional",
    },
    {
        "slot": "G", "object": "SouthAfrica_Karoo", "name": "Karoo",
        "model": "Saf_Karoo", "modeld": "Saf_KarooD", "proj_model": "Saf_KarooM",
        "hier": b"SAF_KAROG", "hierd": b"SAF_KAROGD", "proj_hier": b"SAF_MSL_G",
        "tex": "Saf_KarooP.tga", "body": (88, 96, 42), "nose": NOSE_W,
        "expect": "muddy", "km": 1650, "kg": 800, "acc": 50, "stealth": 32,
        "rebuild": 42, "price": 3200,
        "role": "Fictional inland SRBM (Karoo namesake); heavier than Overberg",
    },
    {
        "slot": "H", "object": "SouthAfrica_Umbani", "name": "Umbani",
        "model": "Saf_Umbani", "modeld": "Saf_UmbaniD", "proj_model": "Saf_UmbaniM",
        "hier": b"SAF_UMBNH", "hierd": b"SAF_UMBNHD", "proj_hier": b"SAF_MSL_H",
        "tex": "Saf_UmbaniP.tga", "body": (10, 72, 84), "nose": NOSE_W,
        "expect": "petrol", "km": 1450, "kg": 550, "acc": 78, "stealth": 36,
        "rebuild": 38, "price": 3100,
        "role": "Precision regional analogue (Umbani PGM heritage; shorter than Karoo)",
    },
    {
        "slot": "I", "object": "SouthAfrica_RSA2", "name": "RSA-2",
        "model": "Saf_RSA2", "modeld": "Saf_RSA2D", "proj_model": "Saf_RSA2M",
        "hier": b"SAF_RSA2I", "hierd": b"SAF_RSA2ID", "proj_hier": b"SAF_MSL_I",
        "tex": "Saf_RSA2P.tga", "body": (128, 128, 128), "nose": NOSE_R,
        "expect": "gray", "km": 1900, "kg": 900, "acc": 45, "stealth": 34,
        "rebuild": 52, "price": 4200,
        "role": "Cancelled RSA-2 analogue; never operational; conservative game stretch",
    },
    {
        "slot": "J", "object": "SouthAfrica_RSA3", "name": "RSA-3",
        "model": "Saf_RSA3", "modeld": "Saf_RSA3D", "proj_model": "Saf_RSA3M",
        "hier": b"SAF_RSA3J", "hierd": b"SAF_RSA3JD", "proj_hier": b"SAF_MSL_J",
        "tex": "Saf_RSA3P.tga", "body": (168, 32, 28), "nose": NOSE_W,
        "expect": "red", "km": 2400, "kg": 1200, "acc": 48, "stealth": 38,
        "rebuild": 65, "price": 5600,
        "role": "Cancelled RSA-3 analogue; not an ICBM; cap below Libya/UAE/Saudi J",
    },
]

NAME_MAP = [
    "A Mokopa new (ATGM heritage stretched to SPECTER 1000 km floor; high Acc)",
    "B Valkiri new as SouthAfrica_Valkiri (MLRS analogue; distinct from SouthAfricaVehicleValkiri)",
    "C Ingwe new (guided ATGM heritage; tactical precision)",
    "D Skerpioen new (Gabriel/AShM coastal analogue; MaxHealth proxy, not stealth)",
    "E Raptor new as SouthAfrica_Raptor (Denel PGM heritage; not AmericaJetRaptor / SpecialPower)",
    "F Overberg new (fictional SRBM; Overberg Test Range namesake)",
    "G Karoo new (fictional inland SRBM; heavier regional)",
    "H Umbani new (PGM heritage; shorter than Karoo, higher Acc)",
    "I RSA-2 new as SouthAfrica_RSA2 (cancelled program analogue; never fielded)",
    "J RSA-3 new as SouthAfrica_RSA3 (cancelled; 2400 km / 1200 kg cap; not ICBM)",
]

FROZEN_DATA = list(syr.FROZEN_DATA) + [
    syr.SYR_FAC_KEY, syr.SYR_CB_KEY, syr.SYR_CS_KEY, syr.SYR_WEP_KEY,
    SAF_VT72B_KEY, SAF_DOZER_KEY, SAF_SHAHEEN_KEY, SAF_ABABEEL_KEY,
    SAF_ALHUSS_KEY, SAF_WEP_OLD_KEY, SAF_MIC_KEY, SAF_LGM_KEY,
    SAF_ZZZ_CS, SAF_ZZZ_CB,
]
FROZEN_DATA += [m["unit_key"] for m in syr.DERIVED]
FROZEN_DATA += [m["proj_key"] for m in syr.DERIVED]

FROZEN_ART = list(syr.FROZEN_ART) + [
    syr.TRUCK_KEY, syr.TRUCKD_KEY,
    r"Art\Textures\Syr_LunaP.tga", r"Art\W3D\Syr_Luna.W3D",
]
FROZEN_ART += [m["tex_key"] for m in syr.DERIVED]
FROZEN_ART += [m["tel_key"] for m in syr.DERIVED]
FROZEN_ART += [m["teld_key"] for m in syr.DERIVED]
FROZEN_ART += [m["projw_key"] for m in syr.DERIVED]

for _m in MISSILES:
    assert len(_m["hier"]) == 9 and len(_m["hierd"]) == 10 and len(_m["proj_hier"]) == 9
    assert 1000 <= _m["km"] <= 4000 and 400 <= _m["kg"] <= 10000


def derived(m: dict) -> dict:
    d = sk.derived({**m, "min_range": sk.MOTHER_MIN_RANGE})
    d["button"] = f"CB_SOUTHAFRICA_MISSILE_{m['slot']}"
    d["unit_key"] = (
        r"Data\INI\Object\Specter\South African National Defence Force"
        rf"\Wheeled\{m['object']}.ini"
    )
    d["proj_key"] = (
        r"Data\INI\Object\Specter\South African National Defence Force"
        rf"\{m['object']}_Projectile.ini"
    )
    return d


DERIVED = [derived(m) for m in MISSILES]


def make_southafrica_flag() -> Image.Image:
    """South African flag: black hoist triangle, gold/green Y pall, red over blue fly."""
    w, h = 900, 600
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    px = im.load()
    red = (222, 26, 43, 255)
    blue = (0, 35, 149, 255)
    green = (0, 122, 61, 255)
    gold = (255, 182, 18, 255)
    white = (255, 255, 255, 255)
    black = (0, 0, 0, 255)
    jx = 0.38 * w
    cy = 0.5 * h
    tri_x = 0.30 * w
    green_hw = 0.12 * h
    white_hw = 0.18 * h
    gold_hw = 0.18 * h
    for y in range(h):
        for x in range(w):
            if x <= jx:
                dist = abs(y - cy)
                hoist = True
            else:
                t = (x - jx) / (w - jx)
                y_up = cy + t * (0 - cy)
                y_dn = cy + t * (h - cy)
                dist = min(abs(y - y_up), abs(y - y_dn))
                hoist = False
            y_top = 0.0 + (x / tri_x) * cy if tri_x else cy
            y_bot = h + (x / tri_x) * (cy - h) if tri_x else cy
            in_black = x <= tri_x and y_top <= y <= y_bot
            if in_black and dist > green_hw:
                px[x, y] = gold if dist <= gold_hw else black
            elif dist <= green_hw:
                px[x, y] = green
            elif hoist and dist <= gold_hw:
                px[x, y] = gold
            elif (not hoist) and dist <= white_hw:
                px[x, y] = white
            elif y < cy:
                px[x, y] = red
            else:
                px[x, y] = blue
    return im


def has_southafrica_flag(counts: dict[str, int]) -> bool:
    goldish = counts.get("yellow", 0) + counts.get("orange", 0) + counts.get("cream", 0)
    greenish = counts.get("green", 0) + counts.get("muddy", 0)
    return (
        counts.get("red", 0) >= 3
        and counts.get("blue", 0) >= 3
        and greenish >= 3
        and goldish >= 2
        and counts.get("white", 0) >= 2
        and counts.get("black", 0) >= 2
    )


def recolor_truck(src: Image.Image, damaged: bool = False) -> Image.Image:
    """Map Iraqi tan sheet to South Africa veld khaki / earth / soot."""
    im = src.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            avg = (r + g + b) / 3.0
            sat = max(r, g, b) - min(r, g, b)
            if avg < 55 and sat < 35:
                px[x, y] = (max(0, int(r * 0.32)), max(0, int(g * 0.28)), max(0, int(b * 0.22)), a)
                continue
            if sat > 70 and avg > 70:
                base = VELD
                t = 0.92
            elif avg < 100:
                base = EARTH
                t = max(0.70, min(1.15, avg / 90.0))
            else:
                base = VELD
                t = max(0.55, min(1.25, avg / 130.0))
            nr = min(255, int(base[0] * t))
            ng = min(255, int(base[1] * t))
            nb = min(255, int(base[2] * t))
            if damaged:
                nr, ng, nb = int(nr * 0.70), int(ng * 0.66), int(nb * 0.58)
            px[x, y] = (nr, ng, nb, a)
    return im


def make_saf_tel_w3d(src: bytes, damaged: bool, m: dict) -> bytes:
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
        .replace("South Korea", "South Africa")
        .replace("Side = SouthKorea", "Side = SouthAfrica")
        .replace(
            "Skr_TEL / Skr_TELD (not Irq_9P117 / Jpn_TEL)",
            "Saf_TEL / Saf_TELD (not Irq_9P117 / Jpn_TEL / Skr_TEL / Sau_TEL / Uae_TEL / Lby_TEL / Syr_TEL)",
        )
    )


def projectile_ini(m: dict) -> str:
    return sk.projectile_ini(m).replace("South Korea", "South Africa")


def weapon_file(missiles: list[dict]) -> str:
    head = (
        WEP_MARKER + "\n"
        "; 9P117 scale. Dedicated South Africa A-J. Distinct from Syria/Libya/UAE/Saudi/Vietnam/Japan/SK/Iraq.\n"
        "; Fictional ballistic TEL roster informed by Denel PGMs and cancelled RSA-2/3. Not an ICBM set.\n"
        "; ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000 (PR #629).\n"
        "; Death HACK is a separate path and is not folded into PrimaryDamage.\n"
        "; Acc/CHL columns are design labels mapped to ScatterRadius / MaxHealth.\n"
    )
    body = sk.weapon_blocks(missiles)
    pairs = body.split("\n\n", 1)[1] if "\n\n" in body else body
    return head + "\n" + pairs


def factory_ini() -> str:
    text = sk.factory_ini()
    text = text.replace("; South Korea missile factory.", "; South Africa missile factory.")
    text = text.replace(
        "with a SouthKorea-only CommandSet (A-J).",
        "with a SouthAfrica-only CommandSet (A-J).",
    )
    text = text.replace("Object SouthKorea_MissileFactory", "Object SouthAfrica_MissileFactory")
    text = text.replace(
        "DisplayName      = OBJECT:SouthKoreaMissileFactory",
        "DisplayName      = OBJECT:SouthAfricaMissileFactory",
    )
    text = text.replace("Side             = SouthKorea", "Side             = SouthAfrica")
    text = text.replace(
        "CommandSet       = SouthKorea_MissileFactoryCommandSet",
        "CommandSet       = SouthAfrica_MissileFactoryCommandSet",
    )
    return text


def factory_commandset() -> str:
    slots = "\r\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(DERIVED, start=1))
    return (
        "CommandSet SouthAfrica_MissileFactoryCommandSet\r\n"
        f"{slots}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def with_southafrica_factory(block: str) -> str:
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in block:
        raise SystemExit(f"expected isolated Iraq factory in:\n{block}")
    if "Command_ConstructSouthAfrica_MissileFactory" in block:
        raise SystemExit("South Africa factory already present on builder")
    return block.replace(
        "Command_ConstructIraq_AlFahdMissileFactoryBuilding",
        "Command_ConstructSouthAfrica_MissileFactory",
    )


def commandbutton_all() -> str:
    lines = [
        "; South Africa missiles A-J production buttons and factory construct button.",
        "; Shared specter_missile_* cameos. Unique Object bindings.",
        "",
        "CommandButton Command_ConstructSouthAfrica_MissileFactory",
        "  Command          = DOZER_CONSTRUCT",
        "  Object           = SouthAfrica_MissileFactory",
        "  TextLabel        = CONTROLBAR:ConstructSouthAfricaMissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel    = CONTROLBAR:ToolTipSouthAfricaMissileFactory",
        "End",
        "",
    ]
    for m in DERIVED:
        lines.extend(
            [
                f"CommandButton {m['button']}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {m['object']}",
                f"  TextLabel     = CONTROLBAR:SouthAfricaMissile{m['slot']}",
                f"  ButtonImage   = {m['cameo']}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTipSouthAfricaMissile{m['slot']}",
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
        "OBJECT:SouthAfricaMissileFactory": "Missile Factory",
        "CONTROLBAR:ConstructSouthAfricaMissileFactory": "Missile Factory",
        "CONTROLBAR:ToolTipSouthAfricaMissileFactory": (
            "Missile Factory\nProduces South Africa missiles A-J\nPrice: $1800"
        ),
    }
    for m in DERIVED:
        mapping[f"OBJECT:{m['object']}"] = m["name"]
        mapping[f"CONTROLBAR:SouthAfricaMissile{m['slot']}"] = f"{m['slot']} {m['name']}"
        mapping[f"CONTROLBAR:ToolTipSouthAfricaMissile{m['slot']}"] = player_tooltip(m)
    return mapping


def mapping_report() -> list[str]:
    lines = [
        "NAME MAPPING:",
        *[f"  {row}" for row in NAME_MAP],
        "",
        "EXISTING SOUTH AFRICA MISSILE OBJECTS PRESERVED (not factory A-J):",
        "  SouthAfrica_ShaheenTEL / SouthAfrica_Weapon_Shaheen",
        "  SouthAfrica_AbabeelTEL / SouthAfrica_Weapon_Ababeel",
        "  SouthAfrica_Alhussaien (AbbasLauncher.ini)",
        "  SouthAfrica_Lgm30 (AmericaLgm30CommandSet) unchanged.",
        "  SouthAfricaVehicleValkiri and SouthAfrica_RaptorMissile SpecialPower unchanged.",
        "",
        "FACTORY CONSTRUCT:",
        "  Pre-change Dozer/Worker/VT72B constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  Post-change those menus construct SouthAfrica_MissileFactory.",
        "  MIC remains on slot 6. Abbas / Lgm30 / FireBase / CRAM unchanged.",
        "",
        "REAL-WORLD vs GAMEPLAY:",
        "  South Africa has no current operational ballistic-missile force.",
        "  Confirmed/historical: Denel Mokopa/Ingwe ATGMs, Umbani/Raptor PGMs, Skerpioen AShM,",
        "  Valkiri MLRS, Umkhonto SAM, Overberg Test Range, cancelled RSA-1/2/3 (1980s-1990s).",
        "  RSA-2/3 were never fielded. Public RSA-3 figures are space-launch / cancelled-ICBM",
        "  class estimates, not verified deployed range or payload.",
        "  SPECTER A-J is a fictional ballistic TEL roster. Names and relative Acc/CHL/cost",
        "  are informed by that industry mix. km/kg values are game design under the 1000-4000",
        "  km and 400-10000 kg bounds, not verified military specifications.",
        "  No public evidence supports an operational South African ICBM or multi-ton BM force.",
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
    sat_cs = data[SAF_CS_KEY].decode("latin1")

    if "ZZZZ" in SAF_CB_KEY or "ZZZZ" in SAF_CS_KEY or "ZZZZ" in SAF_WEP_KEY:
        fails.append("ZZZZ shortcut")
    if SAF_CS_KEY >= r"Data\INI\CommandSet_ZZZZ":
        fails.append("South Africa satellite sorts into ZZZZ")
    if SAF_CS_KEY <= CS_KEY:
        fails.append("South Africa satellite sorts before CommandSet.ini")

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
        "Syria_MissileFactoryCommandSet",
        "SyriaDozerCommandSet",
        "Syria_WorkerCommandSet",
        "Syria_VT72BCommandSet",
    ):
        if sk.last_block(cs_text, "CommandSet", frozen_cs) != sk.last_block(
            src_cs, "CommandSet", frozen_cs
        ):
            fails.append(f"{frozen_cs} mutated in CommandSet.ini")

    for name in BUILDERS:
        new_b = sk.last_block(cs_text, "CommandSet", name)
        if "Command_ConstructSouthAfrica_MissileFactory" not in new_b:
            fails.append(f"{name} catalog missing South Africa factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in new_b:
            fails.append(f"{name} still has isolated Iraq factory")
        if "Command_ConstructSouthAfrica_MIC" not in new_b:
            fails.append(f"{name} lost MIC")
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", name)
        if "Command_ConstructSouthAfrica_MissileFactory" not in lw:
            fails.append(f"last-wins {name} from {_k} missing South Africa factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in lw:
            fails.append(f"last-wins {name} still Iraq factory")
        if name not in sat_cs:
            fails.append(f"satellite missing {name}")

    fac = sk.last_block(cs_text, "CommandSet", "SouthAfrica_MissileFactoryCommandSet")
    if not fac:
        fails.append("CommandSet.ini missing South Africa factory roster")
    slots = re.findall(r"CB_SOUTHAFRICA_MISSILE_([A-Z])", fac)
    if slots != list("ABCDEFGHIJ"):
        fails.append(f"factory slots {slots} != A-J")
    if "Command_Sell" not in fac or "Command_SetRallyPoint" not in fac:
        fails.append("factory missing Rally/Sell")
    if any(
        tag in fac
        for tag in (
            "CB_VIETNAM_", "CB_JAPAN_", "CB_SOUTHKOREA_", "CB_SAUDIARABIA_",
            "CB_UAE_", "CB_LIBYA_", "CB_SYRIA_",
        )
    ):
        fails.append("factory mixed foreign buttons")

    construct = sk.last_block(cb_text, "CommandButton", "Command_ConstructSouthAfrica_MissileFactory")
    if sk.field(construct, "Object") != "SouthAfrica_MissileFactory":
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
    ):
        if sk.field(sk.last_block(cb_text, "CommandButton", btn), "ButtonImage") != img:
            fails.append(f"{btn} image lost")
        if sk.last_block(cb_text, "CommandButton", btn) != sk.last_block(src_cb, "CommandButton", btn):
            fails.append(f"{btn} mutated")

    fac_obj = sk.last_block(data[SAF_FAC_KEY].decode("latin1"), "Object", "SouthAfrica_MissileFactory")
    if sk.field(fac_obj, "Side") != "SouthAfrica":
        fails.append("factory Side")
    if sk.field(fac_obj, "CommandSet") != "SouthAfrica_MissileFactoryCommandSet":
        fails.append("factory object CommandSet")
    if "SouthKorea_SupplyCenter" not in fac_obj:
        fails.append("factory lost SouthKorea_SupplyCenter prereq")
    if "SouthAfrica_SupplyCenter" not in fac_obj:
        fails.append("factory missing SouthAfrica_SupplyCenter prereq")

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
    if sk.last_block(wep_text, "Weapon", "Weapon_Libya_Fajr") != sk.last_block(
        src_wep, "Weapon", "Weapon_Libya_Fajr"
    ):
        fails.append("Libya Fajr weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Syria_Luna") != sk.last_block(
        src_wep, "Weapon", "Weapon_Syria_Luna"
    ):
        fails.append("Syria Luna weapon mutated")
    if sk.last_block(data[SAF_WEP_OLD_KEY].decode("latin1"), "Weapon", "SouthAfrica_Weapon_Shaheen") != sk.last_block(
        src_data[SAF_WEP_OLD_KEY].decode("latin1"), "Weapon", "SouthAfrica_Weapon_Shaheen"
    ):
        fails.append("South Africa Shaheen weapon mutated")

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
    syr_fac = sk.last_block(data[syr.SYR_FAC_KEY].decode("latin1"), "Object", "Syria_MissileFactory")
    if sk.field(syr_fac, "Side") != "Syria":
        fails.append("Syria factory Side mutated")

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
    syr_avg = Image.open(io.BytesIO(src_art[syr.TRUCK_KEY])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == syr_avg:
        fails.append("truck still Syria drab")

    wep_sat = data[SAF_WEP_KEY].decode("latin1")
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
        if sk.field(unit, "Side") != "SouthAfrica":
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
        if "SouthAfrica_ShaheenTEL" in unit or "SouthAfrica_Alhussaien" in unit or "Syria_Luna" in unit:
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
        if sk.csf_get(csf, f"CONTROLBAR:SouthAfricaMissile{m['slot']}") != f"{m['slot']} {m['name']}":
            fails.append(f"{m['slot']} CSF name")
        if sk.csf_get(csf, f"CONTROLBAR:ToolTipSouthAfricaMissile{m['slot']}") != player_tooltip(m):
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
                "Lby_TEL.tga", "Syr_TEL.tga",
            )
        ):
            fails.append(f"{m['slot']} foreign truck")

        im = Image.open(io.BytesIO(art[m["tex_key"]])).convert("RGB")
        tel_flag = sk.region_mode(im, (110, 180, 420, 290))
        if not has_southafrica_flag(tel_flag):
            fails.append(f"{m['slot']} South Africa flag {tel_flag}")
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
    fac_dir = LOOSE / "Object/Specter/South African National Defence Force/Buildings"
    wheel_dir = LOOSE / "Object/Specter/South African National Defence Force/Wheeled"
    proj_dir = LOOSE / "Object/Specter/South African National Defence Force"
    wep_dir = LOOSE / "Weapon"
    for d in (fac_dir, wheel_dir, proj_dir, wep_dir):
        d.mkdir(parents=True, exist_ok=True)
    (fac_dir / "SouthAfrica_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    (wep_dir / "Weapon_SouthAfrica_Missiles.ini").write_text(weapon_file(DERIVED), encoding="utf-8")
    (LOOSE / "CommandButton_SouthAfricaMissiles.ini").write_text(commandbutton_all(), encoding="utf-8")
    (LOOSE / "CommandSet_SouthAfricaMissiles.ini").write_text(commandset_file(builders), encoding="utf-8")
    for m in DERIVED:
        (wheel_dir / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (proj_dir / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_SYR or SRC_DATA.stat().st_size != SIZE_DATA_SYR:
        raise SystemExit("DATA baseline is not SPECTER_SYRIA_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_SYR or SRC_ART.stat().st_size != SIZE_ART_SYR:
        raise SystemExit("ART baseline is not SPECTER_SYRIA_MISSILES_AJ")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art = sk.parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    flag = make_southafrica_flag()
    truck = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])), damaged=False)
    truckd = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCKD_DDS])), damaged=True)
    art[TRUCK_KEY] = sk.make_tga32(truck)
    art[TRUCKD_KEY] = sk.make_tga32(truckd)

    for m in DERIVED:
        skin = sk.make_skin(m["body"], m["nose"], m["name"], flag)
        art[m["tex_key"]] = sk.make_tga32(skin)
        art[m["tel_key"]] = make_saf_tel_w3d(src_art[TEL_W3D], False, m)
        art[m["teld_key"]] = make_saf_tel_w3d(src_art[TELD_W3D], True, m)
        art[m["projw_key"]] = sk.make_proj_w3d(src_art[PROJ_W3D], m)
        data[m["unit_key"]] = sk.to_crlf(unit_ini(m))
        data[m["proj_key"]] = sk.to_crlf(projectile_ini(m))

    data[SAF_FAC_KEY] = sk.to_crlf(factory_ini())
    data[SAF_WEP_KEY] = sk.to_crlf(weapon_file(DERIVED))
    data[SAF_CB_KEY] = sk.to_crlf(commandbutton_all())
    data[CSF_KEY] = sk.csf_upsert(src_data[CSF_KEY], csf_map())

    cs = src_data[CS_KEY].decode("latin1")
    builders = {}
    for name in BUILDERS:
        old = sk.last_block(cs, "CommandSet", name)
        new = with_southafrica_factory(old)
        builders[name] = new
        cs = sk.replace_last(cs, "CommandSet", name, new)
    if sk.last_block(cs, "CommandSet", "SouthAfrica_MissileFactoryCommandSet"):
        cs = sk.replace_last(cs, "CommandSet", "SouthAfrica_MissileFactoryCommandSet", factory_commandset())
    else:
        cs = cs.rstrip("\r\n") + "\r\n\r\n" + factory_commandset() + "\r\n"
    data[CS_KEY] = cs.encode("latin1")
    data[SAF_CS_KEY] = sk.to_crlf(commandset_file(builders))

    cb = src_data[CB_KEY].decode("latin1")
    if "CommandButton Command_ConstructSouthAfrica_MissileFactory" in cb:
        raise SystemExit("CommandButton.ini already had South Africa factory")
    extra = commandbutton_all().replace("\n", "\r\n")
    data[CB_KEY] = (cb.rstrip("\r\n") + "\r\n\r\n" + extra + "\r\n").encode("latin1")

    wep = src_data[WEAPON_KEY].decode("latin1")
    if WEP_MARKER in wep or "Weapon Weapon_SouthAfrica_Mokopa" in wep:
        raise SystemExit("Weapon.ini already had South Africa A-J")
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
    (ext / "CommandSet.ini.SouthAfrica.txt").write_text(
        "\r\n\r\n".join(sk.last_block(packed_cs, "CommandSet", n) for n in BUILDERS)
        + "\r\n\r\n"
        + sk.last_block(packed_cs, "CommandSet", "SouthAfrica_MissileFactoryCommandSet")
        + "\r\n",
        encoding="utf-8",
    )
    (ext / "Weapon.ini.SouthAfrica.txt").write_text(weapon_file(DERIVED), encoding="utf-8")
    (ext / "SouthAfrica_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    for m in DERIVED:
        (ext / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (ext / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    preview = OUT / "PREVIEW"
    preview.mkdir()
    flag.save(preview / "SouthAfricaFlag.png")
    truck.save(preview / "Saf_TEL.png")
    truckd.save(preview / "Saf_TELD.png")
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
    zip_path = ROOT / "patch/Release/SPECTER_SOUTHAFRICA_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    inv = [
        "PRE-CHANGE SOUTH AFRICA (packed last-wins, Syria A-J baseline):",
        "  No SouthAfrica_MissileFactory.",
        "  Dozer/Worker/VT72B constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  MIC on slot 6. Existing ShaheenTEL / AbabeelTEL / Alhussaien / Lgm30 preserved.",
        "  Packed faction path: South African National Defence Force. Side=SouthAfrica.",
        "",
        "POST-CHANGE SOUTH AFRICA:",
        "  Dedicated SouthAfrica_MissileFactory A-J + Rally/Sell.",
        "  Builder slot that held the isolated Iraq factory now builds the South Africa factory.",
        "  Fictional regional profile: 1000-2400 km, 400-1200 kg. Not a Syria/Libya/UAE/Saudi reskin.",
        "",
        "COUNTRY BALANCE (inspected packed / accepted factory A-J, not runtime):",
        "  Factory A-J countries Japan/SK/Vietnam/Saudi/UAE/Libya stretch to 3400-4000 km",
        "  and multi-ton J payloads (Libya J 3900 km / 8000 kg, UAE J 4000/7000,",
        "  Saudi J 4000/4000, Japan J 3600/4000, Vietnam J 4000/4000).",
        "  Syria A-J caps at 2200 km / 1500 kg as a regional force with mixed Acc.",
        "  US/EU do not currently have an A-J missile-factory roster in packed DATA.",
        "  US strategic systems (LGM-30 Minuteman III, UGM-133 Trident II, Tomahawk)",
        "  and European standoff weapons (SCALP, Storm Shadow, Taurus) live on other",
        "  production paths and remain the advanced strategic/standoff set.",
        "  South Africa A-J caps at 2400 km / 1200 kg: slightly longer than Syria J,",
        "  lighter warhead than Syria J, generally higher Acc from the PGM/ATGM heritage.",
        "  CHL is interceptor toughness (MaxHealth), not stealth. Skerpioen is the outlier.",
        "",
        *map_lines,
    ]
    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #637 s-syria-missiles-aj + PR #636 + #635 + #634 + #633 + #632 + #631 + #630 + #629",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "SOUTHAFRICA_FACTORY_NEW=YES",
        "SHAHEEN_ABABEEL_ALHUSS_LGM30_KEPT=YES",
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
        "KM_CEILING_USED=2400",
        "KG_FLOOR=400",
        "KG_CEILING_USED=1200",
        "FICTIONAL_BALLISTIC_ROSTER=YES",
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
            "ZIP_FILE=SPECTER_SOUTHAFRICA_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #637",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-southafrica-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-southafrica-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-southafrica-missiles-aj/SPECTER_SOUTHAFRICA_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-southafrica-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-southafrica-missiles-aj",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "South Africa complete missile roster A-J on the accepted factory/fire path.\n"
        "New country factory replaces the isolated Iraq factory construct on South Africa builders.\n"
        "Existing ShaheenTEL, AbabeelTEL, Alhussaien, and Lgm30 are unchanged.\n"
        "Fictional regional profile 1000-2400 km / 400-1200 kg. Not a Syria/Libya/UAE/Saudi reskin.\n"
        "A-J is not an operational South African ballistic-missile force.\n"
        "Syria A-J, Libya A-J, UAE A-J, Saudi A-J, Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# South Africa missiles A-J\n\n"
        "- New SouthAfrica_MissileFactory. Rally/Sell retained.\n"
        "- Replaces isolated Iraq factory construct on South Africa Dozer, Worker, and VT72B.\n"
        "- MIC, Abbas, Lgm30, ShaheenTEL, AbabeelTEL, and Alhussaien preserved.\n"
        "- South Africa flag (Y/pall: black/gold/green/white/red/blue) + exact names on dorsal UV bands.\n"
        "- Dedicated Saf_TEL veld khaki truck. Ten-color tube palette distinct from Syria/Libya/UAE/Saudi.\n"
        "- Fictional ballistic TEL roster. No operational South African BM force.\n"
        "- Regional capability cap: 2400 km / 1200 kg. Not ICBM-class.\n"
        "- 5-minute clip reload on all ten PRIMARY weapons.\n"
        "- Syria A-J, Libya A-J, UAE A-J, Saudi A-J, Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n", encoding="utf-8")
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_SouthAfricaMissiles.ini last-wins South Africa builder + factory CommandSets.\n"
        "CommandButton_SouthAfricaMissiles.ini last-wins construct + A-J.\n"
        "Weapon\\Weapon_SouthAfrica_Missiles.ini last-wins Weapon_SouthAfrica_* factory pair.\n"
        "Weapon_SouthAfrica.ini (Shaheen/Ababeel and other South Africa weapons) is unchanged.\n"
        "SouthAfrica_Mokopa/Valkiri/Ingwe/Skerpioen/Raptor/Overberg/Karoo/Umbani/RSA2/RSA3 are new objects.\n"
        "SouthAfricaVehicleValkiri and SouthAfrica_RaptorMissile SpecialPower are unchanged.\n"
        "Syria, Libya, UAE, Saudi, Vietnam, Japan, South Korea, Iraq, and 9P117 packed definitions are unchanged.\n"
    )
    art_notes = [
        "SOUTH AFRICA A-J ART MARKINGS (static inspection)",
        "",
        "Flag: black hoist triangle, gold/green Y pall, red upper fly, blue lower fly.",
        "SPECTER Side=SouthAfrica / South African National Defence Force identity.",
        "Not Syria / UAE / Saudi / Iraq / Libya flags.",
        "Dedicated Saf_TEL / Saf_TELD veld truck. Not Irq_9P117 / Skr_TEL / Jpn_TEL / Sau_TEL / Uae_TEL / Lby_TEL / Syr_TEL.",
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
