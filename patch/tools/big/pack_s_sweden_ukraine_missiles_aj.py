#!/usr/bin/env python3
"""Sweden + Ukraine missile rosters A-J on the Britain/France baseline.

Baseline: packed SPECTER_BRITAIN_FRANCE_MISSILES_AJ (PR #648 on #647 / #646).

Packed last-wins audit: Sweden and Ukraine are playable NATO sides
(FactionSweden / FactionUkraine, Side=Sweden / Ukraine). Builder is the Dozer
only (SwedenVehicleDozer / UkraineVehicleDozer). Last-wins SwedenDozerCommandSet
and UkraineDozerCommandSet live in CommandSet.ini. Slot 14 constructs isolated
Sell-only Iraq_AlFahdMissileFactoryBuilding. No dedicated missile factory.
Existing SE_Flag.tga / UA_Flag.tga, War Factories, Lgm30 slot 12, THAAD slot 15,
Britain/France/Germany/Italy A-J factories stay frozen.

Sweden: Nordic precision/naval mix. Ukraine: mobile tactical + earlier heavy
+ CHL standouts. Neither is a rename of the other or of GB/FR/DE/IT. Names are
public-program / place inspiration; km/kg/Acc/CHL are SPECTER design values,
not claimed real specs.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Satellites: CommandSet_SwedenMissiles.ini, CommandSet_UkraineMissiles.ini,
CommandButton_SwedenMissiles.ini, CommandButton_UkraineMissiles.ini,
Weapon\\Weapon_Sweden_Missiles.ini, Weapon\\Weapon_Ukraine_Missiles.ini.
No RadarPriority. No rearm. No ZZZZ. Acc != 28.
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
import pack_s_uae_missiles_aj as uae  # noqa: E402
import pack_s_japan_missiles_aj as jpn  # noqa: E402
import pack_s_saudi_missiles_aj as sa  # noqa: E402
import pack_s_germany_italy_missiles_aj as gi  # noqa: E402
import pack_s_britain_france_missiles_aj as bf  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_BRITAIN_FRANCE_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_BRITAIN_FRANCE_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_SWEDEN_UKRAINE_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "104f01eb0310cdb05b54d9a260ce37a3f1b33725276fb7d9e5cc0ac8dcfbb50b"
SIZE_DATA_SRC = 369211512
SHA_ART_SRC = "d7bba4b32dc053b7d8857fa64d9a27db6bb98b73def0544871b4aa7911d6a523"
SIZE_ART_SRC = 2021434626

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

SE_CB_KEY = r"Data\INI\CommandButton_SwedenMissiles.ini"
SE_CS_KEY = r"Data\INI\CommandSet_SwedenMissiles.ini"
SE_WEP_KEY = r"Data\INI\Weapon\Weapon_Sweden_Missiles.ini"
SE_FAC_KEY = (
    r"Data\INI\Object\Specter\Swedish Armed Forces"
    r"\Buildings\Sweden_MissileFactory.ini"
)
SE_DOZER_KEY = r"Data\INI\Object\Specter\Swedish Armed Forces\Wheleed\Dozer.ini"
SE_WF_KEY = r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\Warfactory.ini"
SE_SC_KEY = r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\SupplyCenter.ini"
SE_FLAG = r"Art\Textures\SE_Flag.tga"

UA_CB_KEY = r"Data\INI\CommandButton_UkraineMissiles.ini"
UA_CS_KEY = r"Data\INI\CommandSet_UkraineMissiles.ini"
UA_WEP_KEY = r"Data\INI\Weapon\Weapon_Ukraine_Missiles.ini"
UA_FAC_KEY = (
    r"Data\INI\Object\Specter\Ukrainian Armed Forces"
    r"\Buildings\Ukraine_MissileFactory.ini"
)
UA_DOZER_KEY = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Wheleed\Dozer.ini"
UA_WF_KEY = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\Warfactory.ini"
UA_SC_KEY = r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\SupplyCenter.ini"
UA_FLAG = r"Art\Textures\UA_Flag.tga"

SE_TRUCK = "Swe_TEL.tga"
SE_TRUCKD = "Swe_TELD.tga"
UA_TRUCK = "Ukr_TEL.tga"
UA_TRUCKD = "Ukr_TELD.tga"

NOSE_W = (236, 228, 210)
NOSE_R = (168, 32, 28)
NOSE_B = (20, 48, 140)
NOSE_G = (20, 72, 40)

# Sweden: Nordic precision/naval. A is yellow (flag), not red.
SWEDEN_MISSILES = [
    {"slot": "A", "object": "Sweden_RBS15", "name": "RBS15",
     "model": "Swe_RBS15", "modeld": "Swe_RBS15D", "proj_model": "Swe_RBS15M",
     "hier": b"SWE_RBS1A", "hierd": b"SWE_RBS1AD", "proj_hier": b"SWE_MSL_A",
     "tex": "Swe_RBS15P.tga", "body": (214, 178, 28), "nose": NOSE_W,
     "expect": "yellow", "km": 1000, "kg": 400, "acc": 78, "stealth": 28,
     "rebuild": 16, "price": 880,
     "role": "Coastal cruise analogue (RBS15 class; SPECTER floor range)"},
    {"slot": "B", "object": "Sweden_Gungnir", "name": "Gungnir",
     "model": "Swe_Gungnr", "modeld": "Swe_GungnrD", "proj_model": "Swe_GungnrM",
     "hier": b"SWE_GUNGB", "hierd": b"SWE_GUNGBD", "proj_hier": b"SWE_MSL_B",
     "tex": "Swe_GungnrP.tga", "body": (20, 48, 128), "nose": NOSE_W,
     "expect": "blue", "km": 1250, "kg": 600, "acc": 72, "stealth": 36,
     "rebuild": 23, "price": 1500,
     "role": "Nordic strike analogue; Acc over payload"},
    {"slot": "C", "object": "Sweden_Norrsken", "name": "Norrsken",
     "model": "Swe_Norrsk", "modeld": "Swe_NorrskD", "proj_model": "Swe_NorrskM",
     "hier": b"SWE_NORRC", "hierd": b"SWE_NORRCD", "proj_hier": b"SWE_MSL_C",
     "tex": "Swe_NorrskP.tga", "body": (220, 200, 155), "nose": NOSE_B,
     "expect": "cream", "km": 1450, "kg": 550, "acc": 84, "stealth": 48,
     "rebuild": 29, "price": 2100,
     "role": "Precision medium; Acc/CHL standout, light warhead"},
    {"slot": "D", "object": "Sweden_Vidar", "name": "Vidar",
     "model": "Swe_Vidar", "modeld": "Swe_VidarD", "proj_model": "Swe_VidarM",
     "hier": b"SWE_VIDAD", "hierd": b"SWE_VIDADD", "proj_hier": b"SWE_MSL_D",
     "tex": "Swe_VidarP.tga", "body": (110, 114, 118), "nose": NOSE_W,
     "expect": "gray", "km": 1600, "kg": 1100, "acc": 50, "stealth": 22,
     "rebuild": 35, "price": 2500,
     "role": "Cheaper medium; heavier than Norrsken, lower Acc/CHL"},
    {"slot": "E", "object": "Sweden_Berserk", "name": "Berserk",
     "model": "Swe_Bersrk", "modeld": "Swe_BersrkD", "proj_model": "Swe_BersrkM",
     "hier": b"SWE_BERSE", "hierd": b"SWE_BERSED", "proj_hier": b"SWE_MSL_E",
     "tex": "Swe_BersrkP.tga", "body": (12, 80, 88), "nose": NOSE_B,
     "expect": "petrol", "km": 1850, "kg": 800, "acc": 76, "stealth": 52,
     "rebuild": 41, "price": 3400,
     "role": "Expensive precision medium; not the heaviest"},
    {"slot": "F", "object": "Sweden_Fenrir", "name": "Fenrir",
     "model": "Swe_Fenrir", "modeld": "Swe_FenrirD", "proj_model": "Swe_FenrirM",
     "hier": b"SWE_FENRF", "hierd": b"SWE_FENRFD", "proj_hier": b"SWE_MSL_F",
     "tex": "Swe_FenrirP.tga", "body": (24, 26, 28), "nose": NOSE_W,
     "expect": "black", "km": 2050, "kg": 1700, "acc": 42, "stealth": 32,
     "rebuild": 49, "price": 4400,
     "role": "Heavy-medium; payload over Acc versus Berserk"},
    {"slot": "G", "object": "Sweden_Sleipnir", "name": "Sleipnir",
     "model": "Swe_Sleipn", "modeld": "Swe_SleipnD", "proj_model": "Swe_SleipnM",
     "hier": b"SWE_SLEIG", "hierd": b"SWE_SLEIGD", "proj_hier": b"SWE_MSL_G",
     "tex": "Swe_SleipnP.tga", "body": (16, 120, 48), "nose": NOSE_W,
     "expect": "green", "km": 2450, "kg": 1500, "acc": 66, "stealth": 54,
     "rebuild": 57, "price": 5400,
     "role": "Advanced medium-heavy; Acc/CHL cost money"},
    {"slot": "H", "object": "Sweden_Midgard", "name": "Midgard",
     "model": "Swe_Midgrd", "modeld": "Swe_MidgrdD", "proj_model": "Swe_MidgrdM",
     "hier": b"SWE_MIDGH", "hierd": b"SWE_MIDGHD", "proj_hier": b"SWE_MSL_H",
     "tex": "Swe_MidgrdP.tga", "body": (200, 96, 28), "nose": NOSE_W,
     "expect": "orange", "km": 2750, "kg": 2400, "acc": 38, "stealth": 36,
     "rebuild": 70, "price": 7000,
     "role": "Heavy strike; payload over precision"},
    {"slot": "I", "object": "Sweden_Aurora", "name": "Aurora",
     "model": "Swe_Aurora", "modeld": "Swe_AuroraD", "proj_model": "Swe_AuroraM",
     "hier": b"SWE_AUROI", "hierd": b"SWE_AUROID", "proj_hier": b"SWE_MSL_I",
     "tex": "Swe_AuroraP.tga", "body": (232, 234, 236), "nose": NOSE_B,
     "expect": "white", "km": 3300, "kg": 2800, "acc": 60, "stealth": 60,
     "rebuild": 78, "price": 8400,
     "role": "Expensive advanced heavy; CHL/Acc versus Midgard payload"},
    {"slot": "J", "object": "Sweden_Yggdrasil", "name": "Yggdrasil",
     "model": "Swe_Yggdra", "modeld": "Swe_YggdraD", "proj_model": "Swe_YggdraM",
     "hier": b"SWE_YGGDJ", "hierd": b"SWE_YGGDJD", "proj_hier": b"SWE_MSL_J",
     "tex": "Swe_YggdraP.tga", "body": (80, 92, 40), "nose": NOSE_W,
     "expect": "muddy", "km": 3850, "kg": 4000, "acc": 34, "stealth": 28,
     "rebuild": 94, "price": 9600,
     "role": "Flagship long-range; payload costs Acc/CHL versus Aurora"},
]

# Ukraine: mobile tactical + earlier heavy + CHL standouts. A is petrol, not red.
UKRAINE_MISSILES = [
    {"slot": "A", "object": "Ukraine_Neptune", "name": "Neptune",
     "model": "Ukr_Neptun", "modeld": "Ukr_NeptunD", "proj_model": "Ukr_NeptunM",
     "hier": b"UKR_NEPTA", "hierd": b"UKR_NEPTAD", "proj_hier": b"UKR_MSL_A",
     "tex": "Ukr_NeptunP.tga", "body": (6, 92, 100), "nose": NOSE_W,
     "expect": "petrol", "km": 1000, "kg": 400, "acc": 58, "stealth": 18,
     "rebuild": 15, "price": 760,
     "role": "Coastal cruise analogue (Neptune class; SPECTER floor)"},
    {"slot": "B", "object": "Ukraine_Vilkha", "name": "Vilkha",
     "model": "Ukr_Vilkha", "modeld": "Ukr_VilkhaD", "proj_model": "Ukr_VilkhaM",
     "hier": b"UKR_VILKB", "hierd": b"UKR_VILKBD", "proj_hier": b"UKR_MSL_B",
     "tex": "Ukr_VilkhaP.tga", "body": (176, 72, 20), "nose": NOSE_W,
     "expect": "orange", "km": 1150, "kg": 900, "acc": 42, "stealth": 22,
     "rebuild": 21, "price": 1400,
     "role": "MLRS-class analogue; earlier payload than Sweden Gungnir"},
    {"slot": "C", "object": "Ukraine_Hrim", "name": "Hrim",
     "model": "Ukr_Hrim", "modeld": "Ukr_HrimD", "proj_model": "Ukr_HrimM",
     "hier": b"UKR_HRIMC", "hierd": b"UKR_HRIMCD", "proj_hier": b"UKR_MSL_C",
     "tex": "Ukr_HrimP.tga", "body": (244, 244, 248), "nose": NOSE_R,
     "expect": "white", "km": 1400, "kg": 550, "acc": 70, "stealth": 40,
     "rebuild": 25, "price": 1850,
     "role": "Tactical ballistic analogue; Acc over payload"},
    {"slot": "D", "object": "Ukraine_Sapsan", "name": "Sapsan",
     "model": "Ukr_Sapsan", "modeld": "Ukr_SapsanD", "proj_model": "Ukr_SapsanM",
     "hier": b"UKR_SAPSD", "hierd": b"UKR_SAPSDD", "proj_hier": b"UKR_MSL_D",
     "tex": "Ukr_SapsanP.tga", "body": (200, 160, 20), "nose": NOSE_W,
     "expect": "yellow", "km": 1550, "kg": 1200, "acc": 36, "stealth": 20,
     "rebuild": 32, "price": 2250,
     "role": "Crude medium; heavier/cheaper Acc than Hrim"},
    {"slot": "E", "object": "Ukraine_Dnipro", "name": "Dnipro",
     "model": "Ukr_Dnipro", "modeld": "Ukr_DniproD", "proj_model": "Ukr_DniproM",
     "hier": b"UKR_DNIPE", "hierd": b"UKR_DNIPED", "proj_hier": b"UKR_MSL_E",
     "tex": "Ukr_DniproP.tga", "body": (128, 124, 118), "nose": NOSE_W,
     "expect": "gray", "km": 1700, "kg": 700, "acc": 64, "stealth": 50,
     "rebuild": 37, "price": 2900,
     "role": "CHL standout medium; not a Sweden Berserk copy"},
    {"slot": "F", "object": "Ukraine_Grom", "name": "Grom",
     "model": "Ukr_Grom", "modeld": "Ukr_GromD", "proj_model": "Ukr_GromM",
     "hier": b"UKR_GROMF", "hierd": b"UKR_GROMFD", "proj_hier": b"UKR_MSL_F",
     "tex": "Ukr_GromP.tga", "body": (160, 24, 32), "nose": NOSE_W,
     "expect": "red", "km": 1950, "kg": 2000, "acc": 32, "stealth": 26,
     "rebuild": 47, "price": 4000,
     "role": "Early heavy; payload before Sweden Fenrir"},
    {"slot": "G", "object": "Ukraine_Kozak", "name": "Kozak",
     "model": "Ukr_Kozak", "modeld": "Ukr_KozakD", "proj_model": "Ukr_KozakM",
     "hier": b"UKR_KOZAG", "hierd": b"UKR_KOZAGD", "proj_hier": b"UKR_MSL_G",
     "tex": "Ukr_KozakP.tga", "body": (20, 22, 28), "nose": NOSE_W,
     "expect": "black", "km": 2250, "kg": 1400, "acc": 54, "stealth": 38,
     "rebuild": 53, "price": 4800,
     "role": "Balanced heavy-medium; not Sweden Sleipnir"},
    {"slot": "H", "object": "Ukraine_Odesa", "name": "Odesa",
     "model": "Ukr_Odesa", "modeld": "Ukr_OdesaD", "proj_model": "Ukr_OdesaM",
     "hier": b"UKR_ODESH", "hierd": b"UKR_ODESHD", "proj_hier": b"UKR_MSL_H",
     "tex": "Ukr_OdesaP.tga", "body": (8, 140, 56), "nose": NOSE_W,
     "expect": "green", "km": 2400, "kg": 1100, "acc": 60, "stealth": 62,
     "rebuild": 55, "price": 5000,
     "role": "Toughness over payload; CHL versus Grom / Midgard"},
    {"slot": "I", "object": "Ukraine_Kyiv", "name": "Kyiv",
     "model": "Ukr_Kyiv", "modeld": "Ukr_KyivD", "proj_model": "Ukr_KyivM",
     "hier": b"UKR_KYIVI", "hierd": b"UKR_KYIVID", "proj_hier": b"UKR_MSL_I",
     "tex": "Ukr_KyivP.tga", "body": (216, 196, 150), "nose": NOSE_R,
     "expect": "cream", "km": 3050, "kg": 2400, "acc": 46, "stealth": 34,
     "rebuild": 74, "price": 7300,
     "role": "Limited strategic; below Sweden Aurora Acc/CHL"},
    {"slot": "J", "object": "Ukraine_Tryzub", "name": "Tryzub",
     "model": "Ukr_Tryzub", "modeld": "Ukr_TryzubD", "proj_model": "Ukr_TryzubM",
     "hier": b"UKR_TRYZJ", "hierd": b"UKR_TRYZJD", "proj_hier": b"UKR_MSL_J",
     "tex": "Ukr_TryzubP.tga", "body": (40, 80, 170), "nose": NOSE_R,
     "expect": "blue", "km": 3650, "kg": 4600, "acc": 26, "stealth": 24,
     "rebuild": 90, "price": 9900,
     "role": "Flagship; heavier/cruder/shorter than Sweden Yggdrasil"},
]


def _country(code, label, side, prefix, builder, fac_obj, fac_cs, fac_btn,
             fac_key, cb_key, cs_key, wep_key, wep_marker, path, truck, truckd,
             truck_key, truckd_key, flag_fn, flag_check, missiles, bases):
    return {
        "code": code, "label": label, "side": side, "prefix": prefix,
        "builder": builder, "fac_obj": fac_obj, "fac_cs": fac_cs,
        "fac_btn": fac_btn, "fac_key": fac_key, "cb_key": cb_key,
        "cs_key": cs_key, "wep_key": wep_key, "wep_marker": wep_marker,
        "path": path, "truck": truck, "truckd": truckd,
        "truck_key": truck_key, "truckd_key": truckd_key,
        "flag_fn": flag_fn, "flag_check": flag_check,
        "missiles": missiles, "bases": bases,
    }


SE_MID = (110, 118, 124)
SE_DARK = (52, 58, 64)
SE_METAL = (150, 154, 158)
UA_MID = (108, 100, 62)
UA_DARK = (52, 48, 32)
UA_METAL = (132, 128, 112)


def make_sweden_flag() -> Image.Image:
    w, h = 900, 600
    blue = (0, 82, 147, 255)
    yellow = (254, 204, 0, 255)
    im = Image.new("RGBA", (w, h), blue)
    draw = ImageDraw.Draw(im)
    cw, ch = 140, 90
    vx = int(w * 0.32)
    draw.rectangle([vx - cw // 2, 0, vx + cw // 2, h], fill=yellow)
    draw.rectangle([0, (h - ch) // 2, w, (h + ch) // 2], fill=yellow)
    return im


def make_ukraine_flag() -> Image.Image:
    w, h = 900, 600
    im = Image.new("RGBA", (w, h), (0, 87, 183, 255))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, w, h // 2], fill=(0, 87, 183, 255))
    draw.rectangle([0, h // 2, w, h], fill=(255, 215, 0, 255))
    return im


def has_sweden_flag(counts: dict[str, int]) -> bool:
    yellowish = counts.get("yellow", 0) + counts.get("orange", 0) + counts.get("cream", 0)
    return counts.get("blue", 0) >= 3 and yellowish >= 3


def has_ukraine_flag(counts: dict[str, int]) -> bool:
    yellowish = counts.get("yellow", 0) + counts.get("orange", 0) + counts.get("cream", 0)
    return counts.get("blue", 0) >= 3 and yellowish >= 3


COUNTRY_DEFS = [
    _country(
        "SE", "Sweden", "Sweden", "Sweden",
        "SwedenDozerCommandSet", "Sweden_MissileFactory",
        "Sweden_MissileFactoryCommandSet",
        "Command_ConstructSweden_MissileFactory",
        SE_FAC_KEY, SE_CB_KEY, SE_CS_KEY, SE_WEP_KEY,
        "; ===== Sweden missiles A-J (Weapon.ini load path for Command_FireMainWeapon) =====",
        r"Data\INI\Object\Specter\Swedish Armed Forces",
        SE_TRUCK, SE_TRUCKD, rf"Art\Textures\{SE_TRUCK}", rf"Art\Textures\{SE_TRUCKD}",
        make_sweden_flag, has_sweden_flag, SWEDEN_MISSILES,
        {"dark": SE_DARK, "mid": SE_MID, "metal": SE_METAL},
    ),
    _country(
        "UA", "Ukraine", "Ukraine", "Ukraine",
        "UkraineDozerCommandSet", "Ukraine_MissileFactory",
        "Ukraine_MissileFactoryCommandSet",
        "Command_ConstructUkraine_MissileFactory",
        UA_FAC_KEY, UA_CB_KEY, UA_CS_KEY, UA_WEP_KEY,
        "; ===== Ukraine missiles A-J (Weapon.ini load path for Command_FireMainWeapon) =====",
        r"Data\INI\Object\Specter\Ukrainian Armed Forces",
        UA_TRUCK, UA_TRUCKD, rf"Art\Textures\{UA_TRUCK}", rf"Art\Textures\{UA_TRUCKD}",
        make_ukraine_flag, has_ukraine_flag, UKRAINE_MISSILES,
        {"dark": UA_DARK, "mid": UA_MID, "metal": UA_METAL},
    ),
]

def player_tooltip(m: dict) -> str:
    return (
        f"{m['slot']} {m['name']}\n"
        f"Range: {m['km']} km\n"
        f"Warhead: {m['kg']} kg\n"
        f"Accuracy: {m['acc']}/100\n"
        f"Radar Stealth: {m['stealth']}/100\n"
        f"Accuracy is impact scatter, not a hit %.\n"
        f"Radar Stealth is a rating for interceptor toughness, not stealth "
        f"and not a penetration %.\n"
        f"Build Time: {m['rebuild']} sec\n"
        f"Price: ${m['price']}"
    )


def derived(m: dict, c: dict) -> dict:
    d = sk.derived({**m, "min_range": sk.MOTHER_MIN_RANGE})
    d["button"] = f"CB_{c['prefix'].upper()}_MISSILE_{m['slot']}"
    d["unit_key"] = rf"{c['path']}\Wheeled\{m['object']}.ini"
    d["proj_key"] = rf"{c['path']}\{m['object']}_Projectile.ini"
    d["side"] = c["side"]
    d["label"] = c["label"]
    d["prefix"] = c["prefix"]
    d["truck"] = c["truck"]
    d["truckd"] = c["truckd"]
    d["tooltip"] = player_tooltip(d)
    d["caption"] = f"{d['slot']} {d['name']}"
    return d


for _c in COUNTRY_DEFS:
    for _m in _c["missiles"]:
        assert len(_m["hier"]) == 9 and len(_m["hierd"]) == 10 and len(_m["proj_hier"]) == 9
        assert len(_m["model"]) <= 15 and len(_m["modeld"]) <= 15 and len(_m["proj_model"]) <= 15
        assert 1000 <= _m["km"] <= 4000 and 400 <= _m["kg"] <= 10000
        assert _m["acc"] != 28
    _c["derived"] = [derived(m, _c) for m in _c["missiles"]]

assert SWEDEN_MISSILES[0]["expect"] != "red" and UKRAINE_MISSILES[0]["expect"] != "red"
assert [m["expect"] for m in SWEDEN_MISSILES] != [m["expect"] for m in UKRAINE_MISSILES]
assert [m["expect"] for m in SWEDEN_MISSILES] != [m["expect"] for m in gi.GERMANY_MISSILES]
assert [m["expect"] for m in SWEDEN_MISSILES] != [m["expect"] for m in gi.ITALY_MISSILES]
assert [m["expect"] for m in SWEDEN_MISSILES] != [m["expect"] for m in bf.BRITAIN_MISSILES]
assert [m["expect"] for m in UKRAINE_MISSILES] != [m["expect"] for m in bf.FRANCE_MISSILES]
assert SWEDEN_MISSILES[0]["acc"] > UKRAINE_MISSILES[0]["acc"]
assert UKRAINE_MISSILES[5]["kg"] > SWEDEN_MISSILES[5]["kg"]
assert UKRAINE_MISSILES[-1]["kg"] > SWEDEN_MISSILES[-1]["kg"]
assert SWEDEN_MISSILES[-1]["km"] > UKRAINE_MISSILES[-1]["km"]


def recolor_truck(src: Image.Image, bases: dict, damaged: bool = False) -> Image.Image:
    im = src.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            avg = (r + g + b) / 3.0
            sat = max(r, g, b) - min(r, g, b)
            if avg < 55 and sat < 35:
                px[x, y] = (max(0, int(r * 0.30)), max(0, int(g * 0.30)), max(0, int(b * 0.28)), a)
                continue
            if sat > 70 and avg > 70:
                base, t = bases["metal"], 0.92
            elif avg < 100:
                base, t = bases["dark"], max(0.70, min(1.15, avg / 90.0))
            else:
                base, t = bases["mid"], max(0.55, min(1.25, avg / 130.0))
            nr = min(255, int(base[0] * t))
            ng = min(255, int(base[1] * t))
            nb = min(255, int(base[2] * t))
            if damaged:
                nr, ng, nb = int(nr * 0.72), int(ng * 0.70), int(nb * 0.64)
            px[x, y] = (nr, ng, nb, a)
    return im


def make_tel_w3d(src: bytes, damaged: bool, m: dict) -> bytes:
    mapping = {"Irq_AlFahd500P.tga": m["tex"]}
    if damaged:
        mapping["Irq_9P117D.tga"] = m["truckd"]
        blob = sk.replace_textures(src, mapping)
        blob = sk.uniquify(blob, [(b"IRQ_AF500D", m["hierd"])])
        blob = sk.patch_hlod_container(blob, m["modeld"])
    else:
        mapping["Irq_9P117.tga"] = m["truck"]
        blob = sk.replace_textures(src, mapping)
        blob = sk.uniquify(blob, [(b"IRQ_AF500", m["hier"])])
        blob = sk.patch_hlod_container(blob, m["model"])
    return blob


def unit_ini(m: dict) -> str:
    return (
        sk.unit_ini(m)
        .replace("South Korea", m["label"])
        .replace("Side = SouthKorea", f"Side = {m['side']}")
        .replace(
            "Skr_TEL / Skr_TELD (not Irq_9P117 / Jpn_TEL)",
            f"{m['truck']} / {m['truckd']} (not Irq_9P117 / Skr_TEL / Jpn_TEL / Deu_TEL / Ita_TEL donor)",
        )
    )


def projectile_ini(m: dict) -> str:
    return sk.projectile_ini(m).replace("South Korea", m["label"])


def weapon_file(c: dict) -> str:
    head = (
        c["wep_marker"] + "\n"
        f"; Dedicated {c['label']} A-J. Distinct from the other new country and all accepted rosters.\n"
        "; ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000.\n"
        "; Death HACK is a separate path and is not folded into PrimaryDamage.\n"
        "; Acc/CHL columns are design labels mapped to ScatterRadius / MaxHealth.\n"
    )
    body = sk.weapon_blocks(c["derived"])
    pairs = body.split("\n\n", 1)[1] if "\n\n" in body else body
    return head + "\n" + pairs


def factory_ini(c: dict) -> str:
    text = sk.factory_ini()
    text = text.replace("; South Korea missile factory.", f"; {c['label']} missile factory.")
    text = text.replace(
        "with a SouthKorea-only CommandSet (A-J).",
        f"with a {c['side']}-only CommandSet (A-J).",
    )
    text = text.replace("Object SouthKorea_MissileFactory", f"Object {c['fac_obj']}")
    text = text.replace(
        "DisplayName      = OBJECT:SouthKoreaMissileFactory",
        f"DisplayName      = OBJECT:{c['prefix']}MissileFactory",
    )
    text = text.replace("Side             = SouthKorea", f"Side             = {c['side']}")
    text = text.replace(
        "CommandSet       = SouthKorea_MissileFactoryCommandSet",
        f"CommandSet       = {c['fac_cs']}",
    )
    return text


def factory_commandset(c: dict) -> str:
    slots = "\r\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(c["derived"], start=1))
    return (
        f"CommandSet {c['fac_cs']}\r\n"
        f"{slots}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def with_country_factory(block: str, c: dict) -> str:
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in block:
        raise SystemExit(f"expected isolated Iraq factory in:\n{block}")
    if c["fac_btn"] in block:
        raise SystemExit(f"{c['label']} factory already present on builder")
    return block.replace(
        "Command_ConstructIraq_AlFahdMissileFactoryBuilding",
        c["fac_btn"],
    )


def commandbutton_all(c: dict) -> str:
    lines = [
        f"; {c['label']} missiles A-J production buttons and factory construct button.",
        "; Shared specter_missile_* cameos. Unique Object bindings.",
        "",
        f"CommandButton {c['fac_btn']}",
        "  Command          = DOZER_CONSTRUCT",
        f"  Object           = {c['fac_obj']}",
        f"  TextLabel        = CONTROLBAR:Construct{c['prefix']}MissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        f"  DescriptLabel    = CONTROLBAR:ToolTip{c['prefix']}MissileFactory",
        "End",
        "",
    ]
    for m in c["derived"]:
        lines.extend(
            [
                f"CommandButton {m['button']}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {m['object']}",
                f"  TextLabel     = CONTROLBAR:{c['prefix']}Missile{m['slot']}",
                f"  ButtonImage   = {m['cameo']}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTip{c['prefix']}Missile{m['slot']}",
                "End",
                "",
            ]
        )
    return "\n".join(lines)


def commandset_file(c: dict, builder_block: str) -> str:
    return builder_block + "\r\n\r\n" + factory_commandset(c) + "\r\n"


def csf_map() -> dict[str, str]:
    mapping = {}
    for c in COUNTRY_DEFS:
        mapping[f"OBJECT:{c['prefix']}MissileFactory"] = "Missile Factory"
        mapping[f"CONTROLBAR:Construct{c['prefix']}MissileFactory"] = "Missile Factory"
        mapping[f"CONTROLBAR:ToolTip{c['prefix']}MissileFactory"] = (
            f"Missile Factory\nProduces {c['label']} missiles A-J\nPrice: $1800"
        )
        for m in c["derived"]:
            mapping[f"OBJECT:{m['object']}"] = m["name"]
            mapping[f"CONTROLBAR:{c['prefix']}Missile{m['slot']}"] = m["caption"]
            mapping[f"CONTROLBAR:ToolTip{c['prefix']}Missile{m['slot']}"] = m["tooltip"]
    return mapping


def mapping_report() -> list[str]:
    lines = [
        "SWEDEN + UKRAINE A-J MISSILE ROSTERS",
        "",
        "Baseline packed last-wins: SPECTER_BRITAIN_FRANCE_MISSILES_AJ (PR #648).",
        "Sweden and Ukraine had no missile factory. Dozer slot 14 constructed",
        "isolated Iraq_AlFahdMissileFactoryBuilding. That slot now constructs",
        "the country factory. War Factory, Lgm30, THAAD, NASAMS, SkySabre,",
        "Skyranger, GB/FR/DE/IT A-J, and existing air weapons stay frozen.",
        "",
        "SPECTER design values. Not claimed real-world range or payload.",
        "Sweden: Nordic precision/naval mix. Ukraine: mobile tactical + earlier",
        "heavy + CHL standouts. A is not red. Color sequences differ from GB/FR/DE/IT.",
        "",
        "ENGINE:",
        "  AttackRange 1720 = 1000 km. Formula: 1720 * (km / 1000).",
        "  PrimaryDamage 2000 = 400 kg. Formula: 2000 * (kg / 400).",
        "  SecondaryDamage 100 = 400 kg splash. Formula: 100 * (kg / 400).",
        "  Death HACK 2200 = 400 kg extra. NOT folded into PrimaryDamage.",
        "  ScatterRadius 175 = 10/100 accuracy. Dispersion, not hit %.",
        "  Projectile MaxHealth 400 = 5/100 intercept proxy. No RadarPriority.",
        "  ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000.",
        "",
        "CTRY  SLOT NAME            KM   KG   ACC CHL TIME COST  SCATTER  HP     PD      SD    HACK",
    ]
    for c in COUNTRY_DEFS:
        for m in c["derived"]:
            lines.append(
                f"  {c['code']:<4} {m['slot']}    {m['name']:<14} {m['km']:<4} {m['kg']:<4} "
                f"{m['acc']:<3} {m['stealth']:<3} {m['rebuild']:<4} {m['price']:<5} "
                f"{sk.fmt_stat(m['scatter']):<7} {sk.fmt_stat(m['hp']):<6} "
                f"{sk.fmt_stat(m['damage']):<7} {sk.fmt_stat(m['secondary']):<5} {m['death']}"
            )
    return lines


ALLOWED_BODY = {
    "blue": {"blue", "petrol"},
    "green": {"green", "muddy"},
    "yellow": {"yellow", "orange", "cream"},
    "red": {"red", "orange"},
    "petrol": {"petrol", "blue", "green"},
    "orange": {"orange", "red", "yellow"},
    "cream": {"cream", "white", "yellow"},
    "gray": {"gray", "white", "other"},
    "black": {"black", "gray", "other"},
    "white": {"white", "cream", "gray"},
    "muddy": {"muddy", "green", "other"},
}


def validate(data, art, src_data, src_art, order) -> list[str]:
    fails: list[str] = []
    frozen_data = [
        SE_DOZER_KEY, SE_WF_KEY, SE_SC_KEY, UA_DOZER_KEY, UA_WF_KEY, UA_SC_KEY,
        bf.GB_DOZER_KEY, bf.GB_WF_KEY, bf.GB_SC_KEY, bf.GB_FAC_KEY, bf.GB_WEP_KEY,
        bf.FR_DOZER_KEY, bf.FR_WF_KEY, bf.FR_SC_KEY, bf.FR_FAC_KEY, bf.FR_WEP_KEY,
        gi.DE_DOZER_KEY, gi.DE_WF_KEY, gi.DE_SC_KEY, gi.DE_FAC_KEY, gi.DE_WEP_KEY,
        gi.IT_DOZER_KEY, gi.IT_WF_KEY, gi.IT_SC_KEY, gi.IT_FAC_KEY, gi.IT_WEP_KEY,
        sk.R11_KEY, sa.SA_FAC_KEY, uae.UAE_FAC_KEY, vn.VN_FAC_KEY, vn.VN_WEP_KEY,
        jpn.NEW_FAC_KEY, jpn.NEW_WEP_KEY, sk.NEW_FAC_KEY, sk.NEW_WEP_KEY,
    ]
    for key in frozen_data:
        if key in src_data and data.get(key) != src_data.get(key):
            fails.append(f"frozen DATA mutated {key}")
    frozen_art = [
        SE_FLAG, UA_FLAG, bf.GB_FLAG, bf.FR_FLAG, gi.DE_FLAG, gi.IT_FLAG,
        rf"Art\Textures\{bf.GB_TRUCK}", rf"Art\Textures\{bf.FR_TRUCK}",
        rf"Art\Textures\{gi.DE_TRUCK}", rf"Art\Textures\{gi.IT_TRUCK}",
    ]
    for key in frozen_art:
        if key and key in src_art and art.get(key) != src_art.get(key):
            fails.append(f"frozen ART mutated {key}")

    cs_text = data[CS_KEY].decode("latin1")
    src_cs = src_data[CS_KEY].decode("latin1")
    cb_text = data[CB_KEY].decode("latin1")
    wep_text = data[WEAPON_KEY].decode("latin1")
    src_wep = src_data[WEAPON_KEY].decode("latin1")

    for key in (SE_CS_KEY, UA_CS_KEY, SE_CB_KEY, UA_CB_KEY, SE_WEP_KEY, UA_WEP_KEY):
        if "ZZZZ" in key:
            fails.append(f"ZZZZ {key}")
        if key.startswith(r"Data\INI\CommandSet_") and key <= CS_KEY:
            fails.append(f"satellite sorts before CommandSet.ini {key}")

    for frozen_cs in (
        "Iraq_AlFahdMissileFactoryCommandSet",
        "Vietnam_MissileFactoryCommandSet",
        "SouthKorea_MissileFactoryCommandSet",
        "UAE_MissileFactoryCommandSet",
        "Japan_MissileFactoryCommandSet",
        "SaudiArabia_MissileFactoryCommandSet",
        "NorthKorea_MissileFactoryCommandSet",
        "Germany_MissileFactoryCommandSet",
        "Italy_MissileFactoryCommandSet",
        "Britain_MissileFactoryCommandSet",
        "France_MissileFactoryCommandSet",
        "BritainDozerCommandSet",
        "FranceDozerCommandSet",
        "GermanyDozerCommandSet",
        "ItalyDozerCommandSet",
        "SwedenWarfactoryCommandSet",
        "UkraineWarfactoryCommandSet",
    ):
        if sk.last_block(cs_text, "CommandSet", frozen_cs) != sk.last_block(src_cs, "CommandSet", frozen_cs):
            fails.append(f"{frozen_cs} mutated in CommandSet.ini")

    obj_re = re.compile(rb"^Object (\S+)", re.M)
    baseline_objects = set()
    for key, blob in src_data.items():
        if key.endswith(".ini") or key.endswith(".INI"):
            baseline_objects.update(mo.group(1).decode("ascii", "ignore") for mo in obj_re.finditer(blob))

    for c in COUNTRY_DEFS:
        new_b = sk.last_block(cs_text, "CommandSet", c["builder"])
        if c["fac_btn"] not in new_b:
            fails.append(f"{c['builder']} catalog missing factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in new_b:
            fails.append(f"{c['builder']} still isolated Iraq factory")
        for keep in (
            "Command_ConstructAmericaLgm30",
            "Command_ConstructAmericaVehicleTHAAD_AI",
            f"Command_Construct{c['prefix']}WarFactory",
        ):
            if keep not in new_b:
                fails.append(f"{c['builder']} lost {keep}")
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", c["builder"])
        if c["fac_btn"] not in lw:
            fails.append(f"last-wins {c['builder']} from {_k} missing factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in lw:
            fails.append(f"last-wins {c['builder']} still Iraq factory")

        fac = sk.last_block(cs_text, "CommandSet", c["fac_cs"])
        slots = re.findall(rf"CB_{c['prefix'].upper()}_MISSILE_([A-Z])", fac)
        if slots != list("ABCDEFGHIJ"):
            fails.append(f"{c['code']} factory slots {slots}")
        if "Command_Sell" not in fac or "Command_SetRallyPoint" not in fac:
            fails.append(f"{c['code']} factory missing Rally/Sell")
        if any(tag in fac for tag in ("CB_VIETNAM_", "CB_UAE_", "CB_JAPAN_", "CB_GERMANY_", "CB_ITALY_", "CB_BRITAIN_", "CB_FRANCE_")):
            fails.append(f"{c['code']} factory mixed foreign buttons")

        construct = sk.last_block(cb_text, "CommandButton", c["fac_btn"])
        if sk.field(construct, "Object") != c["fac_obj"]:
            fails.append(f"{c['code']} construct Object")
        if sk.field(construct, "Command") != "DOZER_CONSTRUCT":
            fails.append(f"{c['code']} construct Command")
        if sk.field(construct, "ButtonImage") != "Button_MissileFactory":
            fails.append(f"{c['code']} construct image")

        fac_obj = sk.last_block(data[c["fac_key"]].decode("latin1"), "Object", c["fac_obj"])
        if sk.field(fac_obj, "Side") != c["side"]:
            fails.append(f"{c['code']} factory Side")
        if sk.field(fac_obj, "CommandSet") != c["fac_cs"]:
            fails.append(f"{c['code']} factory CommandSet")
        if f"{c['prefix']}SupplyCenter" not in fac_obj:
            fails.append(f"{c['code']} factory missing own supply prereq")

        wep_sat = data[c["wep_key"]].decode("latin1")
        if wep_sat != src_data.get(c["wep_key"], b"").decode("latin1") and c["wep_key"] in src_data:
            fails.append(f"{c['code']} unexpected pre-existing weapon sat")
        csf = data[CSF_KEY]
        seen = set()
        for m in c["derived"]:
            if m["object"] in seen:
                fails.append(f"{c['code']} {m['slot']} duplicate")
            seen.add(m["object"])
            if m["object"] in baseline_objects:
                fails.append(f"{c['code']} {m['slot']} {m['object']} already exists")
            unit = sk.last_block(data[m["unit_key"]].decode("latin1"), "Object", m["object"])
            if sk.field(unit, "BuildCost") != str(m["price"]):
                fails.append(f"{c['code']} {m['slot']} BuildCost")
            if not sk.field(unit, "BuildTime").startswith(f"{m['rebuild']}.0"):
                fails.append(f"{c['code']} {m['slot']} BuildTime")
            if sk.field(unit, "Side") != c["side"]:
                fails.append(f"{c['code']} {m['slot']} Side")
            if sk.field(unit, "ButtonImage") != m["cameo"]:
                fails.append(f"{c['code']} {m['slot']} ButtonImage")
            if m["weapon"] not in unit:
                fails.append(f"{c['code']} {m['slot']} weapon bind")
            if sk.field(unit, "CommandSet") != "Scud_B_CommandSet":
                fails.append(f"{c['code']} {m['slot']} CommandSet")
            if "Rearm" in unit or "RiderChangeContain" in unit:
                fails.append(f"{c['code']} {m['slot']} rearm")
            proj = sk.last_block(data[m["proj_key"]].decode("latin1"), "Object", m["projectile"])
            if sk.field(proj, "MaxHealth") != sk.fmt_stat(m["hp"]):
                fails.append(f"{c['code']} {m['slot']} HP")
            if sk.field(proj, "RadarPriority"):
                fails.append(f"{c['code']} {m['slot']} RadarPriority")
            wkey, w = sk.last_block_from_files(order, data, "Weapon", m["weapon"])
            death = sk.last_block(wep_sat, "Weapon", m["warhead"])
            if sk.field(w, "ScatterRadius") != sk.fmt_stat(m["scatter"]):
                fails.append(f"{c['code']} {m['slot']} scatter")
            if sk.field(w, "PrimaryDamage") != sk.fmt_stat(m["damage"]):
                fails.append(f"{c['code']} {m['slot']} PD")
            if sk.field(w, "SecondaryDamage") != sk.fmt_stat(m["secondary"]):
                fails.append(f"{c['code']} {m['slot']} SD")
            if sk.field(w, "ClipReloadTime") != "300000" or sk.field(w, "WeaponSpeed") != "280":
                fails.append(f"{c['code']} {m['slot']} reload/speed")
            if "HACK" in w:
                fails.append(f"{c['code']} {m['slot']} HACK in PRIMARY")
            if sk.field(death, "DamageType") != "HACK":
                fails.append(f"{c['code']} {m['slot']} death type")
            if sk.field(death, "PrimaryDamage") != str(m["death"]):
                fails.append(f"{c['code']} {m['slot']} death PD")
            cap = sk.csf_get(csf, f"CONTROLBAR:{c['prefix']}Missile{m['slot']}")
            tip = sk.csf_get(csf, f"CONTROLBAR:ToolTip{c['prefix']}Missile{m['slot']}")
            if cap != m["caption"]:
                fails.append(f"{c['code']} {m['slot']} CSF caption")
            if not tip or f"Accuracy: {m['acc']}/100" not in tip or f"Radar Stealth: {m['stealth']}/100" not in tip:
                fails.append(f"{c['code']} {m['slot']} CSF tooltip")
            if "not a hit %" not in (tip or "") or "not stealth" not in (tip or ""):
                fails.append(f"{c['code']} {m['slot']} tooltip caveat")
            bblock = sk.last_block(cb_text, "CommandButton", m["button"])
            if sk.field(bblock, "Object") != m["object"]:
                fails.append(f"{c['code']} {m['slot']} button object")
            tel = art[m["tel_key"]]
            if m["hier"] not in tel or m["tex"] not in sk.all_tex(tel) or m["truck"] not in sk.all_tex(tel):
                fails.append(f"{c['code']} {m['slot']} TEL asset")
            for banned in (b"IRQ_9P117", b"IRQ_AF500", b"GENERIC-MISSILES"):
                if banned in tel:
                    fails.append(f"{c['code']} {m['slot']} leaked {banned.decode()}")
            im = Image.open(io.BytesIO(art[m["tex_key"]])).convert("RGB")
            if not c["flag_check"](sk.region_mode(im, (110, 180, 420, 290))):
                fails.append(f"{c['code']} {m['slot']} flag {sk.region_mode(im, (110, 180, 420, 290))}")
            if not sk.has_name_plate(im, (500, 190, 960, 280)):
                fails.append(f"{c['code']} {m['slot']} TEL name")
            body = sk.region_mode(im, (80, 410, 200, 560))
            top = max(body, key=body.get)
            if top not in ALLOWED_BODY[m["expect"]] and top != m["expect"]:
                fails.append(f"{c['code']} {m['slot']} body {top} {body}")
        if len(c["derived"]) != 10:
            fails.append(f"{c['code']} roster count")

    if sk.illegal_floats(wep_text):
        fails.append(f"illegal floats {sk.illegal_floats(wep_text)}")
    r11 = sk.last_block(data[sk.R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB")
    if sk.field(r11, "BuildCost") != "1200":
        fails.append("9P117 BuildCost")
    for key, expect in (
        ("CONTROLBAR:ToolTipVietnamMissileA", "Accuracy: 10/100"),
        ("CONTROLBAR:ToolTipSouthKoreaMissileJ", "4200 km"),
        ("CONTROLBAR:ToolTipUAEMissileA", "Accuracy: 60/100"),
        ("CONTROLBAR:ToolTipJapanMissileA", "Accuracy: 85/100"),
        ("CONTROLBAR:ToolTipSaudiArabiaMissileA", "Accuracy: 55/100"),
        ("CONTROLBAR:ToolTipGermanyMissileA", "Accuracy: 88/100"),
        ("CONTROLBAR:ToolTipItalyMissileA", "Accuracy: 68/100"),
        ("CONTROLBAR:GermanyMissileA", "A KEPD-350"),
        ("CONTROLBAR:ItalyMissileA", "A Marte"),
        ("CONTROLBAR:BritainMissileA", "A Spear"),
        ("CONTROLBAR:FranceMissileA", "A MdCN"),
        ("CONTROLBAR:ToolTipBritainMissileA", "Accuracy: 80/100"),
        ("CONTROLBAR:ToolTipFranceMissileA", "Accuracy: 62/100"),
    ):
        got = sk.csf_get(data[CSF_KEY], key)
        if not got or expect not in got:
            fails.append(f"frozen CSF lost {key}")
    for wep_name in (
        "Germany_Weapon_Taurus",
        "Italy_Weapon_StormShadow",
        "Britain_Weapon_StormShadow",
        "France_Weapon_SCALP_RafaleB",
    ):
        if sk.last_block(wep_text, "Weapon", wep_name) != sk.last_block(src_wep, "Weapon", wep_name):
            fails.append(f"{wep_name} mutated")
    se_avg = Image.open(io.BytesIO(art[rf"Art\Textures\{SE_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    ua_avg = Image.open(io.BytesIO(art[rf"Art\Textures\{UA_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    gb_avg = Image.open(io.BytesIO(src_art[rf"Art\Textures\{bf.GB_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    fr_avg = Image.open(io.BytesIO(src_art[rf"Art\Textures\{bf.FR_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    de_avg = Image.open(io.BytesIO(src_art[rf"Art\Textures\{gi.DE_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    it_avg = Image.open(io.BytesIO(src_art[rf"Art\Textures\{gi.IT_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    irq_avg = Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    donors = (gb_avg, fr_avg, de_avg, it_avg, irq_avg)
    if se_avg == ua_avg:
        fails.append(f"trucks identical {se_avg}")
    if se_avg in donors or ua_avg in donors:
        fails.append(f"truck still donor {se_avg} {ua_avg}")
    return fails


def write_loose(builders: dict[str, str]) -> None:
    for c in COUNTRY_DEFS:
        fac_dir = LOOSE / c["path"].replace("Data\\INI\\", "").replace("\\", "/") / "Buildings"
        wheel_dir = LOOSE / c["path"].replace("Data\\INI\\", "").replace("\\", "/") / "Wheeled"
        proj_dir = LOOSE / c["path"].replace("Data\\INI\\", "").replace("\\", "/")
        wep_dir = LOOSE / "Weapon"
        for d in (fac_dir, wheel_dir, proj_dir, wep_dir):
            d.mkdir(parents=True, exist_ok=True)
        (fac_dir / f"{c['fac_obj']}.ini").write_text(factory_ini(c), encoding="utf-8")
        (wep_dir / Path(c["wep_key"].replace("\\", "/")).name).write_text(weapon_file(c), encoding="utf-8")
        (LOOSE / Path(c["cb_key"].replace("\\", "/")).name).write_text(commandbutton_all(c), encoding="utf-8")
        (LOOSE / Path(c["cs_key"].replace("\\", "/")).name).write_text(
            commandset_file(c, builders[c["builder"]]), encoding="utf-8"
        )
        for m in c["derived"]:
            (wheel_dir / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
            (proj_dir / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_BRITAIN_FRANCE_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_SRC or SRC_ART.stat().st_size != SIZE_ART_SRC:
        raise SystemExit("ART baseline is not SPECTER_BRITAIN_FRANCE_MISSILES_AJ")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art = sk.parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    donor_truck = Image.open(io.BytesIO(src_art[sk.TRUCK_DDS]))
    donor_truckd = Image.open(io.BytesIO(src_art[sk.TRUCKD_DDS]))

    cs = src_data[CS_KEY].decode("latin1")
    cb = src_data[CB_KEY].decode("latin1")
    wep = src_data[WEAPON_KEY].decode("latin1")
    builders = {}
    flags = {}
    for c in COUNTRY_DEFS:
        flags[c["code"]] = c["flag_fn"]()
        truck = recolor_truck(donor_truck, c["bases"], False)
        truckd = recolor_truck(donor_truckd, c["bases"], True)
        art[c["truck_key"]] = sk.make_tga32(truck)
        art[c["truckd_key"]] = sk.make_tga32(truckd)
        for m in c["derived"]:
            skin = sk.make_skin(m["body"], m["nose"], m["name"], flags[c["code"]])
            art[m["tex_key"]] = sk.make_tga32(skin)
            art[m["tel_key"]] = make_tel_w3d(src_art[TEL_W3D], False, m)
            art[m["teld_key"]] = make_tel_w3d(src_art[TELD_W3D], True, m)
            art[m["projw_key"]] = sk.make_proj_w3d(src_art[PROJ_W3D], m)
            data[m["unit_key"]] = sk.to_crlf(unit_ini(m))
            data[m["proj_key"]] = sk.to_crlf(projectile_ini(m))
        data[c["fac_key"]] = sk.to_crlf(factory_ini(c))
        data[c["wep_key"]] = sk.to_crlf(weapon_file(c))
        data[c["cb_key"]] = sk.to_crlf(commandbutton_all(c))
        old = sk.last_block(cs, "CommandSet", c["builder"])
        new = with_country_factory(old, c)
        builders[c["builder"]] = new
        cs = sk.replace_last(cs, "CommandSet", c["builder"], new)
        if sk.last_block(cs, "CommandSet", c["fac_cs"]):
            cs = sk.replace_last(cs, "CommandSet", c["fac_cs"], factory_commandset(c))
        else:
            cs = cs.rstrip("\r\n") + "\r\n\r\n" + factory_commandset(c) + "\r\n"
        data[c["cs_key"]] = sk.to_crlf(commandset_file(c, new))
        if c["fac_btn"] in cb:
            raise SystemExit(f"CommandButton.ini already had {c['fac_btn']}")
        extra = commandbutton_all(c).replace("\n", "\r\n")
        cb = cb.rstrip("\r\n") + "\r\n\r\n" + extra + "\r\n"
        if c["wep_marker"] in wep or f"Weapon Weapon_{c['derived'][0]['object']}" in wep:
            raise SystemExit(f"Weapon.ini already had {c['label']} A-J")
        wep = wep.rstrip("\r\n") + "\r\n\r\n" + weapon_file(c).replace("\n", "\r\n")

    data[CS_KEY] = cs.encode("latin1")
    data[CB_KEY] = cb.encode("latin1")
    data[WEAPON_KEY] = wep.encode("latin1")
    data[CSF_KEY] = sk.csf_upsert(src_data[CSF_KEY], csf_map())
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
    parts = []
    for c in COUNTRY_DEFS:
        parts.append(sk.last_block(packed_cs, "CommandSet", c["builder"]))
        parts.append(sk.last_block(packed_cs, "CommandSet", c["fac_cs"]))
        (ext / Path(c["wep_key"].replace("\\", "/")).name).write_text(weapon_file(c), encoding="utf-8")
        (ext / f"{c['fac_obj']}.ini").write_text(factory_ini(c), encoding="utf-8")
        for m in c["derived"]:
            (ext / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
    (ext / "CommandSets.txt").write_text("\r\n\r\n".join(parts) + "\r\n", encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    preview = OUT / "PREVIEW"
    preview.mkdir()
    for c in COUNTRY_DEFS:
        flags[c["code"]].save(preview / f"{c['code']}Flag.png")
        Image.open(io.BytesIO(packed_art[c["truck_key"]])).save(preview / c["truck"].replace(".tga", ".png"))
        for m in c["derived"]:
            Image.open(io.BytesIO(packed_art[m["tex_key"]])).save(
                preview / f"{c['code']}_{m['slot']}_{m['object']}.png"
            )

    data_sha = sk.sha256_path(data_path)
    art_sha = sk.sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_SWEDEN_UKRAINE_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #648 s-britain-france-missiles-aj + #647 + #646 + #645 + #644",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "SWEDEN_FACTORY_NEW=YES",
        "UKRAINE_FACTORY_NEW=YES",
        "SE_UA_FLAGS_FROZEN=YES",
        "GB_FR_DE_IT_AJ_KEPT=YES",
        "LGM30_THAAD_KEPT=YES",
        "STORMSHADOW_SCALP_AIR_KEPT=YES",
        "NO_REARM=YES",
        "NO_RADARPRIORITY=YES",
        "ROSTER_COUNT=20",
        "",
        *map_lines,
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
            "ZIP_FILE=SPECTER_SWEDEN_UKRAINE_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #648",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-sweden-ukraine-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-sweden-ukraine-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-sweden-ukraine-missiles-aj/SPECTER_SWEDEN_UKRAINE_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-sweden-ukraine-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-sweden-ukraine-missiles-aj",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Sweden and Ukraine complete missile rosters A-J.\n"
        "New country factories replace isolated Iraq factory construct on each Dozer slot 14.\n"
        "Existing War Factories, flags, Lgm30, THAAD, GB/FR/DE/IT A-J, and air Storm Shadow/SCALP stay frozen.\n"
        "Accepted tooltip corrections and all prior A-J rosters unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Sweden + Ukraine missiles A-J\n\n"
        "- New Sweden_MissileFactory and Ukraine_MissileFactory. Rally/Sell retained.\n"
        "- Replaces isolated Iraq factory construct on Sweden and Ukraine Dozer slot 14.\n"
        "- Sweden: Nordic precision/naval SPECTER mix (RBS15 … Yggdrasil).\n"
        "- Ukraine: independent tactical/earlier-heavy mix (Neptune … Tryzub).\n"
        "- Existing SE/UA flags, War Factories, Lgm30, THAAD, GB/FR/DE/IT A-J, and air weapons preserved.\n"
        "- Tooltips include Acc/100 and Radar Stealth/100 with caveats.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_SwedenMissiles.ini and CommandSet_UkraineMissiles.ini last-win dozer + factory sets.\n"
        "Weapon\\Weapon_Sweden_Missiles.ini and Weapon_Ukraine_Missiles.ini last-win factory pairs.\n"
        "Britain_Weapon_StormShadow and France_Weapon_SCALP_RafaleB air weapons are unchanged.\n"
        "SE_Flag.tga and UA_Flag.tga are frozen. New dorsal stamps are generated, not those files.\n"
        "Britain/France #648, Germany/Italy #647, Vietnam/SK #646, UAE/Japan #645, Saudi #644, NK, India, Pakistan, Iraq, and 9P117 stay frozen.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:70]))


if __name__ == "__main__":
    main()
