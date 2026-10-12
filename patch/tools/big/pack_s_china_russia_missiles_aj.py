#!/usr/bin/env python3
"""China A-J plus Russia A-J on the Turkey/Spain baseline.

Baseline: packed SPECTER_TURKEY_SPAIN_MISSILES_AJ (PR #650 on #649 / #648).

Packed last-wins audit: FactionChina Side=China, FactionRussia Side=Russia.
ChinaVehicleDozer uses PLADozerCommandSet (not unused ChinaDozerCommandSet).
RussiaVehicleDozer uses RussiaDozerCommandSet. Slot 14 on both live builders
constructs isolated Sell-only Iraq_AlFahdMissileFactoryBuilding. No dedicated
missile factory. CN_Flag.tga / RU_Flag.tga, War Factories, existing DF12/DF17/
DF21C/DF41 TELs, RS28 silo, and TR/ES/SE/UA/GB/FR/DE/IT A-J stay frozen.

China: PLA cruise/ballistic SPECTER mix (YJ18 … DF5B).
Russia: independent tactical/earlier-heavy mix (Kalibr … Voevoda).
Neither is a rename of the other. Names are public-program inspiration;
km/kg/Acc/CHL are SPECTER design values, not claimed real specs.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Satellites: CommandSet_ChinaMissiles.ini, CommandSet_RussiaMissiles.ini,
CommandButton_ChinaMissiles.ini, CommandButton_RussiaMissiles.ini,
Weapon\\Weapon_China_Missiles.ini, Weapon\\Weapon_Russia_Missiles.ini.
No RadarPriority. No rearm. No ZZZZ. Acc != 28.
"""
from __future__ import annotations

import gzip
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
import pack_s_sweden_ukraine_missiles_aj as su  # noqa: E402
import pack_s_turkey_spain_missiles_aj as ts  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_TURKEY_SPAIN_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_TURKEY_SPAIN_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_CHINA_RUSSIA_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "2465e216756685dd2d6dbf9fbc53f6a6a07ae30e323cb977364440bdd5f83cb3"
SIZE_DATA_SRC = 369880031
SHA_ART_SRC = "698ac6178222cb98bb8c777d72044daf308b78955946d13350cb7b5abf0ffac1"
SIZE_ART_SRC = 2212483982

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

CN_CB_KEY = r"Data\INI\CommandButton_ChinaMissiles.ini"
CN_CS_KEY = r"Data\INI\CommandSet_ChinaMissiles.ini"
CN_WEP_KEY = r"Data\INI\Weapon\Weapon_China_Missiles.ini"
CN_FAC_KEY = r"Data\INI\Object\Specter\PLA\Buildings\China_MissileFactory.ini"
CN_DOZER_KEY = r"Data\INI\Object\Specter\PLA\Tracked\Dozer.ini"
CN_WF_KEY = r"Data\INI\Object\Specter\PLA\Buildings\Warfactory.ini"
CN_SC_KEY = r"Data\INI\Object\Specter\PLA\Buildings\SupplyCenter.ini"
CN_FLAG = r"Art\Textures\CN_Flag.tga"

RU_CB_KEY = r"Data\INI\CommandButton_RussiaMissiles.ini"
RU_CS_KEY = r"Data\INI\CommandSet_RussiaMissiles.ini"
RU_WEP_KEY = r"Data\INI\Weapon\Weapon_Russia_Missiles.ini"
RU_FAC_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Buildings\Russia_MissileFactory.ini"
)
RU_DOZER_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Tracked\Dozer.ini"
)
RU_WF_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Buildings\Warfactory.ini"
)
RU_SC_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Buildings\SupplyCenter.ini"
)
RU_FLAG = r"Art\Textures\RU_Flag.tga"

CN_TRUCK = "Chi_TEL.tga"
CN_TRUCKD = "Chi_TELD.tga"
RU_TRUCK = "Rus_TEL.tga"
RU_TRUCKD = "Rus_TELD.tga"

NOSE_W = (236, 228, 210)
NOSE_R = (168, 32, 28)
NOSE_B = (20, 48, 140)
NOSE_G = (20, 72, 40)

# China: PLA cruise/ballistic mix. A is cream (not red). Avoids ChinaVehicleDF* names.
CHINA_MISSILES = [
    {"slot": "A", "object": "China_YJ18", "name": "YJ18",
     "model": "Chi_YJ18", "modeld": "Chi_YJ18D", "proj_model": "Chi_YJ18M",
     "hier": b"CHN_YJ18A", "hierd": b"CHN_YJ18AD", "proj_hier": b"CHN_MSL_A",
     "tex": "Chi_YJ18P.tga", "body": (236, 220, 170), "nose": NOSE_R,
     "expect": "cream", "km": 1000, "kg": 400, "acc": 72, "stealth": 24,
     "rebuild": 16, "price": 860,
     "role": "Naval cruise analogue (YJ-18 class; SPECTER floor)"},
    {"slot": "B", "object": "China_CJ10", "name": "CJ10",
     "model": "Chi_CJ10", "modeld": "Chi_CJ10D", "proj_model": "Chi_CJ10M",
     "hier": b"CHN_CJ10B", "hierd": b"CHN_CJ10BD", "proj_hier": b"CHN_MSL_B",
     "tex": "Chi_CJ10P.tga", "body": (12, 80, 88), "nose": NOSE_W,
     "expect": "petrol", "km": 1280, "kg": 560, "acc": 78, "stealth": 42,
     "rebuild": 25, "price": 1700,
     "role": "Land-attack cruise analogue; Acc/CHL over payload"},
    {"slot": "C", "object": "China_DF15", "name": "DF15",
     "model": "Chi_DF15", "modeld": "Chi_DF15D", "proj_model": "Chi_DF15M",
     "hier": b"CHN_DF15C", "hierd": b"CHN_DF15CD", "proj_hier": b"CHN_MSL_C",
     "tex": "Chi_DF15P.tga", "body": (214, 178, 28), "nose": NOSE_W,
     "expect": "yellow", "km": 1520, "kg": 900, "acc": 46, "stealth": 20,
     "rebuild": 30, "price": 2100,
     "role": "SRBM analogue; payload over Acc versus CJ10"},
    {"slot": "D", "object": "China_DF16", "name": "DF16",
     "model": "Chi_DF16", "modeld": "Chi_DF16D", "proj_model": "Chi_DF16M",
     "hier": b"CHN_DF16D", "hierd": b"CHN_DF16DD", "proj_hier": b"CHN_MSL_D",
     "tex": "Chi_DF16P.tga", "body": (24, 26, 28), "nose": NOSE_W,
     "expect": "black", "km": 1700, "kg": 1500, "acc": 32, "stealth": 14,
     "rebuild": 35, "price": 2450,
     "role": "Cheaper medium; heavier/cruder than DF15"},
    {"slot": "E", "object": "China_YJ21", "name": "YJ21",
     "model": "Chi_YJ21", "modeld": "Chi_YJ21D", "proj_model": "Chi_YJ21M",
     "hier": b"CHN_YJ21E", "hierd": b"CHN_YJ21ED", "proj_hier": b"CHN_MSL_E",
     "tex": "Chi_YJ21P.tga", "body": (232, 234, 236), "nose": NOSE_B,
     "expect": "white", "km": 1860, "kg": 680, "acc": 86, "stealth": 52,
     "rebuild": 40, "price": 3450,
     "role": "Expensive precision anti-ship analogue; Acc/CHL not payload"},
    {"slot": "F", "object": "China_DF26", "name": "DF26",
     "model": "Chi_DF26", "modeld": "Chi_DF26D", "proj_model": "Chi_DF26M",
     "hier": b"CHN_DF26F", "hierd": b"CHN_DF26FD", "proj_hier": b"CHN_MSL_F",
     "tex": "Chi_DF26P.tga", "body": (110, 114, 118), "nose": NOSE_W,
     "expect": "gray", "km": 2120, "kg": 1900, "acc": 38, "stealth": 28,
     "rebuild": 48, "price": 4350,
     "role": "IRBM analogue; payload versus YJ21 precision"},
    {"slot": "G", "object": "China_JL2", "name": "JL2",
     "model": "Chi_JL2", "modeld": "Chi_JL2D", "proj_model": "Chi_JL2M",
     "hier": b"CHN_JL2AG", "hierd": b"CHN_JL2AGD", "proj_hier": b"CHN_MSL_G",
     "tex": "Chi_JL2P.tga", "body": (20, 48, 128), "nose": NOSE_W,
     "expect": "blue", "km": 2440, "kg": 1600, "acc": 60, "stealth": 44,
     "rebuild": 55, "price": 5150,
     "role": "SLBM analogue; Acc/CHL cost money"},
    {"slot": "H", "object": "China_DF31", "name": "DF31",
     "model": "Chi_DF31", "modeld": "Chi_DF31D", "proj_model": "Chi_DF31M",
     "hier": b"CHN_DF31H", "hierd": b"CHN_DF31HD", "proj_hier": b"CHN_MSL_H",
     "tex": "Chi_DF31P.tga", "body": (200, 96, 28), "nose": NOSE_W,
     "expect": "orange", "km": 2800, "kg": 2600, "acc": 30, "stealth": 32,
     "rebuild": 68, "price": 6850,
     "role": "Heavy strike; payload over precision"},
    {"slot": "I", "object": "China_JL3", "name": "JL3",
     "model": "Chi_JL3", "modeld": "Chi_JL3D", "proj_model": "Chi_JL3M",
     "hier": b"CHN_JL3AI", "hierd": b"CHN_JL3AID", "proj_hier": b"CHN_MSL_I",
     "tex": "Chi_JL3P.tga", "body": (16, 120, 48), "nose": NOSE_W,
     "expect": "green", "km": 3340, "kg": 2900, "acc": 48, "stealth": 50,
     "rebuild": 76, "price": 8050,
     "role": "Expensive advanced heavy; CHL/Acc versus DF31 payload"},
    {"slot": "J", "object": "China_DF5B", "name": "DF5B",
     "model": "Chi_DF5B", "modeld": "Chi_DF5BD", "proj_model": "Chi_DF5BM",
     "hier": b"CHN_DF5BJ", "hierd": b"CHN_DF5BJD", "proj_hier": b"CHN_MSL_J",
     "tex": "Chi_DF5BP.tga", "body": (80, 92, 40), "nose": NOSE_W,
     "expect": "muddy", "km": 3920, "kg": 4200, "acc": 24, "stealth": 22,
     "rebuild": 94, "price": 9700,
     "role": "Flagship long-range; payload costs Acc/CHL versus JL3"},
]

# Russia: tactical/earlier-heavy + CHL standouts. A is gray (not red). Avoids Russia_RS28 silo names.
RUSSIA_MISSILES = [
    {"slot": "A", "object": "Russia_Kalibr", "name": "Kalibr",
     "model": "Rus_Kalibr", "modeld": "Rus_KalibrD", "proj_model": "Rus_KalibrM",
     "hier": b"RUS_KALBA", "hierd": b"RUS_KALBAD", "proj_hier": b"RUS_MSL_A",
     "tex": "Rus_KalibrP.tga", "body": (110, 114, 118), "nose": NOSE_W,
     "expect": "gray", "km": 1000, "kg": 400, "acc": 56, "stealth": 18,
     "rebuild": 15, "price": 750,
     "role": "Naval cruise analogue (Kalibr class; SPECTER floor)"},
    {"slot": "B", "object": "Russia_Iskander", "name": "Iskander",
     "model": "Rus_Iskndr", "modeld": "Rus_IskndrD", "proj_model": "Rus_IskndrM",
     "hier": b"RUS_ISKNB", "hierd": b"RUS_ISKNBD", "proj_hier": b"RUS_MSL_B",
     "tex": "Rus_IskndrP.tga", "body": (176, 72, 20), "nose": NOSE_W,
     "expect": "orange", "km": 1180, "kg": 800, "acc": 42, "stealth": 20,
     "rebuild": 22, "price": 1380,
     "role": "SRBM analogue; earlier payload than China CJ10"},
    {"slot": "C", "object": "Russia_Oniks", "name": "Oniks",
     "model": "Rus_Oniks", "modeld": "Rus_OniksD", "proj_model": "Rus_OniksM",
     "hier": b"RUS_ONIKC", "hierd": b"RUS_ONIKCD", "proj_hier": b"RUS_MSL_C",
     "tex": "Rus_OniksP.tga", "body": (244, 244, 248), "nose": NOSE_R,
     "expect": "white", "km": 1400, "kg": 480, "acc": 80, "stealth": 46,
     "rebuild": 27, "price": 1920,
     "role": "Precision anti-ship analogue; Acc over payload"},
    {"slot": "D", "object": "Russia_Tochka", "name": "Tochka",
     "model": "Rus_Tochka", "modeld": "Rus_TochkaD", "proj_model": "Rus_TochkaM",
     "hier": b"RUS_TOCHD", "hierd": b"RUS_TOCHDD", "proj_hier": b"RUS_MSL_D",
     "tex": "Rus_TochkaP.tga", "body": (214, 178, 28), "nose": NOSE_W,
     "expect": "yellow", "km": 1580, "kg": 1200, "acc": 34, "stealth": 14,
     "rebuild": 33, "price": 2180,
     "role": "Crude medium; heavier/cheaper Acc than Oniks"},
    {"slot": "E", "object": "Russia_Zircon", "name": "Zircon",
     "model": "Rus_Zircon", "modeld": "Rus_ZirconD", "proj_model": "Rus_ZirconM",
     "hier": b"RUS_ZIRCE", "hierd": b"RUS_ZIRCED", "proj_hier": b"RUS_MSL_E",
     "tex": "Rus_ZirconP.tga", "body": (6, 92, 100), "nose": NOSE_W,
     "expect": "petrol", "km": 1740, "kg": 640, "acc": 66, "stealth": 60,
     "rebuild": 38, "price": 3000,
     "role": "CHL standout medium; not a China YJ21 copy"},
    {"slot": "F", "object": "Russia_Kinzhal", "name": "Kinzhal",
     "model": "Rus_Kinzhl", "modeld": "Rus_KinzhlD", "proj_model": "Rus_KinzhlM",
     "hier": b"RUS_KINZF", "hierd": b"RUS_KINZFD", "proj_hier": b"RUS_MSL_F",
     "tex": "Rus_KinzhlP.tga", "body": (160, 24, 32), "nose": NOSE_W,
     "expect": "red", "km": 1900, "kg": 2000, "acc": 26, "stealth": 24,
     "rebuild": 46, "price": 3900,
     "role": "Early heavy; payload before China DF26"},
    {"slot": "G", "object": "Russia_Yars", "name": "Yars",
     "model": "Rus_Yars", "modeld": "Rus_YarsD", "proj_model": "Rus_YarsM",
     "hier": b"RUS_YARSG", "hierd": b"RUS_YARSGD", "proj_hier": b"RUS_MSL_G",
     "tex": "Rus_YarsP.tga", "body": (20, 22, 28), "nose": NOSE_W,
     "expect": "black", "km": 2260, "kg": 1700, "acc": 50, "stealth": 36,
     "rebuild": 53, "price": 4700,
     "role": "Mobile heavy-medium; not China JL2"},
    {"slot": "H", "object": "Russia_Bulava", "name": "Bulava",
     "model": "Rus_Bulava", "modeld": "Rus_BulavaD", "proj_model": "Rus_BulavaM",
     "hier": b"RUS_BULAH", "hierd": b"RUS_BULAHD", "proj_hier": b"RUS_MSL_H",
     "tex": "Rus_BulavaP.tga", "body": (8, 140, 56), "nose": NOSE_W,
     "expect": "green", "km": 2500, "kg": 1300, "acc": 62, "stealth": 66,
     "rebuild": 56, "price": 5280,
     "role": "Toughness over payload; CHL versus Kinzhal / DF31"},
    {"slot": "I", "object": "Russia_Topol", "name": "Topol",
     "model": "Rus_Topol", "modeld": "Rus_TopolD", "proj_model": "Rus_TopolM",
     "hier": b"RUS_TOPOI", "hierd": b"RUS_TOPOID", "proj_hier": b"RUS_MSL_I",
     "tex": "Rus_TopolP.tga", "body": (220, 200, 155), "nose": NOSE_R,
     "expect": "cream", "km": 3100, "kg": 2400, "acc": 40, "stealth": 32,
     "rebuild": 72, "price": 7200,
     "role": "Limited strategic; below China JL3 Acc/CHL"},
    {"slot": "J", "object": "Russia_Voevoda", "name": "Voevoda",
     "model": "Rus_Voevod", "modeld": "Rus_VoevodD", "proj_model": "Rus_VoevodM",
     "hier": b"RUS_VOEVJ", "hierd": b"RUS_VOEVJD", "proj_hier": b"RUS_MSL_J",
     "tex": "Rus_VoevodP.tga", "body": (40, 80, 170), "nose": NOSE_R,
     "expect": "blue", "km": 3700, "kg": 5000, "acc": 20, "stealth": 18,
     "rebuild": 88, "price": 10200,
     "role": "Flagship; heavier/cruder/shorter than China DF5B"},
]


def _country(code, label, side, prefix, builder, fac_obj, fac_cs, fac_btn,
             fac_key, cb_key, cs_key, wep_key, wep_marker, path, truck, truckd,
             truck_key, truckd_key, flag_fn, flag_check, missiles, bases,
             wf_keep=None, supply_keep=None, keep_cmds=None):
    return {
        "code": code, "label": label, "side": side, "prefix": prefix,
        "builder": builder, "fac_obj": fac_obj, "fac_cs": fac_cs,
        "fac_btn": fac_btn, "fac_key": fac_key, "cb_key": cb_key,
        "cs_key": cs_key, "wep_key": wep_key, "wep_marker": wep_marker,
        "path": path, "truck": truck, "truckd": truckd,
        "truck_key": truck_key, "truckd_key": truckd_key,
        "flag_fn": flag_fn, "flag_check": flag_check,
        "missiles": missiles, "bases": bases,
        "wf_keep": wf_keep or f"Command_Construct{prefix}WarFactory",
        "supply_keep": supply_keep or f"{prefix}SupplyCenter",
        "keep_cmds": keep_cmds or (),
    }


CN_MID = (56, 88, 40)
CN_DARK = (28, 48, 24)
CN_METAL = (132, 136, 112)
RU_MID = (52, 64, 56)
RU_DARK = (28, 36, 32)
RU_METAL = (118, 122, 116)


def _star(draw, cx, cy, r, fill):
    pts = []
    for i in range(10):
        ang = -90 + i * 36
        rad = r if i % 2 == 0 else r * 0.40
        from math import cos, sin, radians
        pts.append((cx + rad * cos(radians(ang)), cy + rad * sin(radians(ang))))
    draw.polygon(pts, fill=fill)


def make_china_flag() -> Image.Image:
    w, h = 900, 600
    red = (222, 41, 16, 255)
    yellow = (255, 222, 0, 255)
    im = Image.new("RGBA", (w, h), red)
    draw = ImageDraw.Draw(im)
    _star(draw, int(w * 0.22), int(h * 0.32), int(h * 0.16), yellow)
    for dx, dy in ((0.42, 0.14), (0.50, 0.26), (0.50, 0.42), (0.42, 0.54)):
        _star(draw, int(w * dx), int(h * dy), int(h * 0.055), yellow)
    return im


def make_russia_flag() -> Image.Image:
    w, h = 900, 600
    im = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, w, h // 3], fill=(255, 255, 255, 255))
    draw.rectangle([0, h // 3, w, 2 * h // 3], fill=(0, 57, 166, 255))
    draw.rectangle([0, 2 * h // 3, w, h], fill=(213, 43, 30, 255))
    return im


def has_china_flag(counts: dict[str, int]) -> bool:
    yellowish = counts.get("yellow", 0) + counts.get("orange", 0) + counts.get("cream", 0)
    return counts.get("red", 0) >= 4 and yellowish >= 2


def has_russia_flag(counts: dict[str, int]) -> bool:
    return (
        counts.get("white", 0) >= 2
        and counts.get("blue", 0) >= 2
        and counts.get("red", 0) >= 2
    )


COUNTRY_DEFS = [
    _country(
        "CN", "China", "China", "China",
        "PLADozerCommandSet", "China_MissileFactory",
        "China_MissileFactoryCommandSet",
        "Command_ConstructChina_MissileFactory",
        CN_FAC_KEY, CN_CB_KEY, CN_CS_KEY, CN_WEP_KEY,
        "; ===== China missiles A-J (Weapon.ini load path for Command_FireMainWeapon) =====",
        r"Data\INI\Object\Specter\PLA",
        CN_TRUCK, CN_TRUCKD, rf"Art\Textures\{CN_TRUCK}", rf"Art\Textures\{CN_TRUCKD}",
        make_china_flag, has_china_flag, CHINA_MISSILES,
        {"dark": CN_DARK, "mid": CN_MID, "metal": CN_METAL},
        keep_cmds=(
            "Command_ConstructChinaWarFactory",
            "Command_ConstructChinaSupplyCenter",
            "Command_ConstructChinaDF5NuclearMissileSilo",
            "Command_ConstructChina_Hq9_Site",
        ),
    ),
    _country(
        "RU", "Russia", "Russia", "Russia",
        "RussiaDozerCommandSet", "Russia_MissileFactory",
        "Russia_MissileFactoryCommandSet",
        "Command_ConstructRussia_MissileFactory",
        RU_FAC_KEY, RU_CB_KEY, RU_CS_KEY, RU_WEP_KEY,
        "; ===== Russia missiles A-J (Weapon.ini load path for Command_FireMainWeapon) =====",
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation",
        RU_TRUCK, RU_TRUCKD, rf"Art\Textures\{RU_TRUCK}", rf"Art\Textures\{RU_TRUCKD}",
        make_russia_flag, has_russia_flag, RUSSIA_MISSILES,
        {"dark": RU_DARK, "mid": RU_MID, "metal": RU_METAL},
        keep_cmds=(
            "Command_ConstructRussiaWarFactory",
            "Command_ConstructRussiaSupplyCenter",
            "Command_ConstructRussiaRS28NuclearMissileSilo",
            "Command_ConstructRussiaKashtan",
            "Command_ConstructRussia_HeavyAirBase",
        ),
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

assert CHINA_MISSILES[0]["expect"] != "red" and RUSSIA_MISSILES[0]["expect"] != "red"
assert [m["expect"] for m in CHINA_MISSILES] != [m["expect"] for m in RUSSIA_MISSILES]
assert [m["expect"] for m in CHINA_MISSILES] != [m["expect"] for m in su.SWEDEN_MISSILES]
assert [m["expect"] for m in RUSSIA_MISSILES] != [m["expect"] for m in su.UKRAINE_MISSILES]
assert [m["expect"] for m in CHINA_MISSILES] != [m["expect"] for m in gi.GERMANY_MISSILES]
assert [m["expect"] for m in RUSSIA_MISSILES] != [m["expect"] for m in gi.ITALY_MISSILES]
assert [m["expect"] for m in CHINA_MISSILES] != [m["expect"] for m in bf.BRITAIN_MISSILES]
assert [m["expect"] for m in RUSSIA_MISSILES] != [m["expect"] for m in bf.FRANCE_MISSILES]
assert [m["expect"] for m in CHINA_MISSILES] != [m["expect"] for m in ts.TURKEY_MISSILES]
assert [m["expect"] for m in RUSSIA_MISSILES] != [m["expect"] for m in ts.SPAIN_MISSILES]
assert CHINA_MISSILES[0]["acc"] > RUSSIA_MISSILES[0]["acc"]
assert RUSSIA_MISSILES[5]["kg"] > CHINA_MISSILES[5]["kg"]
assert RUSSIA_MISSILES[-1]["kg"] > CHINA_MISSILES[-1]["kg"]
assert CHINA_MISSILES[-1]["km"] > RUSSIA_MISSILES[-1]["km"]


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
        "CHINA + RUSSIA A-J MISSILE ROSTERS",
        "",
        "Baseline packed last-wins: SPECTER_TURKEY_SPAIN_MISSILES_AJ (PR #650).",
        "China and Russia had no missile factory. Live builders PLADozerCommandSet",
        "and RussiaDozerCommandSet constructed isolated",
        "Iraq_AlFahdMissileFactoryBuilding on slot 14. That slot now constructs",
        "China_MissileFactory / Russia_MissileFactory. Unused ChinaDozerCommandSet",
        "is frozen. Existing DF12/DF17/DF21C/DF41 TELs, RS28 silo, War Factories,",
        "CN/RU flags, and TR/ES/SE/UA/GB/FR/DE/IT A-J stay frozen.",
        "",
        "SPECTER design values. Not claimed real-world range or payload.",
        "China: PLA cruise/ballistic mix. Russia: independent tactical/",
        "earlier-heavy + CHL standouts. A is not red. Color sequences differ.",
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
        CN_DOZER_KEY, CN_WF_KEY, CN_SC_KEY, RU_DOZER_KEY, RU_WF_KEY, RU_SC_KEY,
        ts.TR_DOZER_KEY, ts.TR_WF_KEY, ts.TR_SC_KEY, ts.TR_FAC_KEY, ts.TR_WEP_KEY,
        ts.TR_CS_KEY, ts.TR_CB_KEY, ts.ES_CS_KEY, ts.ES_CB_KEY,
        ts.NT_DOZER_KEY, ts.NT_WF_KEY, ts.NT_SC_KEY, ts.ES_FAC_KEY, ts.ES_WEP_KEY,
        su.SE_DOZER_KEY, su.SE_WF_KEY, su.SE_SC_KEY, su.SE_FAC_KEY, su.SE_WEP_KEY,
        su.UA_DOZER_KEY, su.UA_WF_KEY, su.UA_SC_KEY, su.UA_FAC_KEY, su.UA_WEP_KEY,
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
        CN_FLAG, RU_FLAG, ts.TR_FLAG, ts.TR_FLAG2, ts.NT_FLAG, su.SE_FLAG, su.UA_FLAG,
        bf.GB_FLAG, bf.FR_FLAG, gi.DE_FLAG, gi.IT_FLAG,
        rf"Art\Textures\{ts.TR_TRUCK}", rf"Art\Textures\{ts.ES_TRUCK}",
        rf"Art\Textures\{su.SE_TRUCK}", rf"Art\Textures\{su.UA_TRUCK}",
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

    for key in (CN_CS_KEY, RU_CS_KEY, CN_CB_KEY, RU_CB_KEY, CN_WEP_KEY, RU_WEP_KEY):
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
        "Sweden_MissileFactoryCommandSet",
        "Ukraine_MissileFactoryCommandSet",
        "BritainDozerCommandSet",
        "FranceDozerCommandSet",
        "GermanyDozerCommandSet",
        "ItalyDozerCommandSet",
        "SwedenDozerCommandSet",
        "UkraineDozerCommandSet",
        "SwedenWarfactoryCommandSet",
        "UkraineWarfactoryCommandSet",
        "Turkey_MissileFactoryCommandSet",
        "Spain_MissileFactoryCommandSet",
        "TurkeyDozerCommandSet",
        "NatoDozerCommandSet",
        "ChinaDozerCommandSet",
        "TurkeyWarfactoryCommandSet",
        "NatoWarfactoryCommandSet",
        "ChinaWarFactoryCommandSet",
        "RussiaWarFactoryCommandSet",
        "Iraq_VT72BCommandSet",
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
        for keep in (c["wf_keep"], *c["keep_cmds"]):
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
        own = f"CB_{c['prefix'].upper()}_"
        foreign = (
            "CB_VIETNAM_", "CB_UAE_", "CB_JAPAN_", "CB_GERMANY_", "CB_ITALY_",
            "CB_BRITAIN_", "CB_FRANCE_", "CB_SWEDEN_", "CB_UKRAINE_",
            "CB_TURKEY_", "CB_SPAIN_", "CB_CHINA_", "CB_RUSSIA_",
        )
        if any(tag in fac for tag in foreign if tag != own):
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
        if c["supply_keep"] not in fac_obj:
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
        ("CONTROLBAR:SwedenMissileA", "A RBS15"),
        ("CONTROLBAR:UkraineMissileA", "A Neptune"),
        ("CONTROLBAR:ToolTipSwedenMissileA", "Accuracy: 78/100"),
        ("CONTROLBAR:ToolTipUkraineMissileA", "Accuracy: 58/100"),
        ("CONTROLBAR:TurkeyMissileA", "A Atmaca"),
        ("CONTROLBAR:SpainMissileA", "A Albatros"),
        ("CONTROLBAR:ToolTipTurkeyMissileA", "Accuracy: 74/100"),
        ("CONTROLBAR:ToolTipSpainMissileA", "Accuracy: 60/100"),
    ):
        got = sk.csf_get(data[CSF_KEY], key)
        if not got or expect not in got:
            fails.append(f"frozen CSF lost {key}")
    for wep_name in (
        "Germany_Weapon_Taurus",
        "Italy_Weapon_StormShadow",
        "Britain_Weapon_StormShadow",
        "France_Weapon_SCALP_RafaleB",
        "Turkey_Weapon_SOM_F16C",
        "Turkey_Weapon_SOM_Ozgur",
        "China_Weapon_CJ10_H6K",
        "China_Weapon_CJ100_H20",
        "MRBM_DF21C",
    ):
        if sk.last_block(wep_text, "Weapon", wep_name) != sk.last_block(src_wep, "Weapon", wep_name):
            fails.append(f"{wep_name} mutated")
    cn_avg = Image.open(io.BytesIO(art[rf"Art\Textures\{CN_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    ru_avg = Image.open(io.BytesIO(art[rf"Art\Textures\{RU_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    donors = []
    for key in (
        rf"Art\Textures\{ts.TR_TRUCK}", rf"Art\Textures\{ts.ES_TRUCK}",
        rf"Art\Textures\{su.SE_TRUCK}", rf"Art\Textures\{su.UA_TRUCK}",
        rf"Art\Textures\{bf.GB_TRUCK}", rf"Art\Textures\{bf.FR_TRUCK}",
        rf"Art\Textures\{gi.DE_TRUCK}", rf"Art\Textures\{gi.IT_TRUCK}",
        sk.TRUCK_DDS,
    ):
        donors.append(
            Image.open(io.BytesIO(src_art[key])).convert("RGB").resize(
                (1, 1), Image.Resampling.BOX
            ).getpixel((0, 0))
        )
    if cn_avg == ru_avg:
        fails.append(f"trucks identical {cn_avg}")
    if cn_avg in donors or ru_avg in donors:
        fails.append(f"truck still donor {cn_avg} {ru_avg}")
    if art.get(CN_FLAG) != src_art.get(CN_FLAG):
        fails.append("CN_Flag.tga mutated")
    if art.get(RU_FLAG) != src_art.get(RU_FLAG):
        fails.append("RU_Flag.tga mutated")
    for name, btn in (
        ("TurkeyDozerCommandSet", "Command_ConstructTurkey_MissileFactory"),
        ("NatoDozerCommandSet", "Command_ConstructSpain_MissileFactory"),
        ("SwedenDozerCommandSet", "Command_ConstructSweden_MissileFactory"),
        ("UkraineDozerCommandSet", "Command_ConstructUkraine_MissileFactory"),
        ("BritainDozerCommandSet", "Command_ConstructBritain_MissileFactory"),
        ("FranceDozerCommandSet", "Command_ConstructFrance_MissileFactory"),
        ("GermanyDozerCommandSet", "Command_ConstructGermany_MissileFactory"),
        ("ItalyDozerCommandSet", "Command_ConstructItaly_MissileFactory"),
        ("Iraq_VT72BCommandSet", "Command_ConstructIraq_AlFahdMissileFactory"),
    ):
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", name)
        if not lw or btn not in lw:
            fails.append(f"preserved slot 14 lost {name}")
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
        raise SystemExit("DATA baseline is not SPECTER_TURKEY_SPAIN_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_SRC or SRC_ART.stat().st_size != SIZE_ART_SRC:
        raise SystemExit("ART baseline is not SPECTER_TURKEY_SPAIN_MISSILES_AJ")

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
    art_gz_path = OUT / "_SPEC_ART_ONE.big.gz"
    with art_path.open("rb") as src, gzip.open(art_gz_path, "wb", compresslevel=6) as dst:
        shutil.copyfileobj(src, dst, 1024 * 1024)
    art_gz_sha = sk.sha256_path(art_gz_path)
    zip_path = ROOT / "patch/Release/SPECTER_CHINA_RUSSIA_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)
    tag = "s-china-russia-missiles-aj"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/"
        + tag
    )

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #650 s-turkey-spain-missiles-aj + #649 + #648 + #647 + #646",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        f"ART_GZ_SIZE={art_gz_path.stat().st_size}",
        f"ART_GZ_SHA256={art_gz_sha}",
        "CHINA_FACTORY_NEW=YES",
        "RUSSIA_FACTORY_NEW=YES",
        "CHINA_REMAINS_CHINA=YES",
        "RUSSIA_REMAINS_RUSSIA=YES",
        "PLA_DOZER_SLOT14=Command_ConstructChina_MissileFactory",
        "RUSSIA_DOZER_SLOT14=Command_ConstructRussia_MissileFactory",
        "UNUSED_CHINA_DOZER_FROZEN=YES",
        "CN_RU_FLAGS_FROZEN=YES",
        "DF12_DF17_DF21C_DF41_KEPT=YES",
        "RS28_RS24_YARS_AI_KEPT=YES",
        "TR_ES_SE_UA_GB_FR_DE_IT_AJ_KEPT=YES",
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
            f"ART_GZ_SIZE={art_gz_path.stat().st_size}",
            f"ART_GZ_SHA256={art_gz_sha}",
            "ZIP_FILE=SPECTER_CHINA_RUSSIA_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #650",
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
                f"  {rel_base}/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement (complete BIG, gzipped for GitHub's 2 GiB asset limit):",
                f"  {rel_base}/_SPEC_ART_ONE.big.gz",
                f"  GZ_SIZE={art_gz_path.stat().st_size}",
                f"  GZ_SHA256={art_gz_sha}",
                f"  UNCOMPRESSED_SIZE={art_path.stat().st_size}",
                f"  UNCOMPRESSED_SHA256={art_sha}",
                "  gunzip -k _SPEC_ART_ONE.big.gz",
                "",
                "ART is also inside the ZIP as uncompressed _SPEC_ART_ONE.big (same SHA).",
                "GitHub rejects raw files >= 2147483648 bytes.",
                "",
                "ZIP (complete uncompressed DATA + ART BIGs):",
                f"  {rel_base}/SPECTER_CHINA_RUSSIA_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both uncompressed BIGs in the SPECTER folder.",
                f"TAG={tag}",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/"
                + tag,
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "China complete missile roster A-J plus Russia complete missile roster A-J.\n"
        "New factories replace isolated Iraq factory construct on PLA and Russia Dozer slot 14.\n"
        "China remains China. Russia remains Russia. Unused ChinaDozerCommandSet is frozen.\n"
        "Existing War Factories, CN/RU flags, DF12/DF17/DF21C/DF41 TELs, RS28 silo,\n"
        "TR/ES/SE/UA/GB/FR/DE/IT A-J, and air weapons stay frozen.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# China + Russia missiles A-J\n\n"
        "- New China_MissileFactory and Russia_MissileFactory. Rally/Sell retained.\n"
        "- Replaces isolated Iraq factory construct on PLADozerCommandSet and "
        "RussiaDozerCommandSet slot 14. Unused ChinaDozerCommandSet is frozen.\n"
        "- China: PLA cruise/ballistic SPECTER mix (YJ18 … DF5B).\n"
        "- Russia: independent tactical/earlier-heavy mix (Kalibr … Voevoda).\n"
        "- China remains China. Russia remains Russia. No faction conversion.\n"
        "- Existing CN/RU flags, War Factories, DF12/DF17/DF21C/DF41 TELs, RS28 silo, "
        "TR/ES/SE/UA/GB/FR/DE/IT A-J, and air weapons preserved.\n"
        "- Tooltips include Acc/100 and Radar Stealth/100 with caveats.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_ChinaMissiles.ini last-wins PLADozerCommandSet (live China builder).\n"
        "CommandSet_RussiaMissiles.ini last-wins RussiaDozerCommandSet.\n"
        "Unused ChinaDozerCommandSet stays on isolated Iraq factory (not the live builder).\n"
        "Weapon\\Weapon_China_Missiles.ini and Weapon_Russia_Missiles.ini last-win factory pairs.\n"
        "China_Weapon_CJ10_H6K / CJ100_H20 / MRBM_DF21C air weapons are unchanged.\n"
        "CN_Flag.tga and RU_Flag.tga are frozen. Dorsal stamps are generated.\n"
        "ChinaVehicleDF12/DF17/DF21C/DF41 and Russia_RS28 / Russia_RS24_Yars_AI stay frozen.\n"
        "Turkey/Spain #650, Sweden/Ukraine #649, Britain/France #648, Germany/Italy #647, "
        "Vietnam/SK, UAE/Japan, Saudi, NK, India, Pakistan, Iraq, and 9P117 stay frozen.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:70]))


if __name__ == "__main__":
    main()
