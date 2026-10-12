#!/usr/bin/env python3
"""Turkey A-J plus Spain-ready Nato A-J on the Sweden/Ukraine baseline.

Baseline: packed SPECTER_SWEDEN_UKRAINE_MISSILES_AJ (PR #649 on #648 / #647).

Packed last-wins audit: FactionTurkey Side=Turkey, FactionNato Side=Nato.
Builders are TurkeyVehicleDozer / NatoVehicleDozer. Last-wins
TurkeyDozerCommandSet and NatoDozerCommandSet live in CommandSet.ini. Slot 14
constructs isolated Sell-only Iraq_AlFahdMissileFactoryBuilding. No dedicated
missile factory. TR_Flag.tga / Turkey_Flag.tga / NT_Flag.tga, War Factories,
Lgm30 slot 12, THAAD slot 15, SE/UA/GB/FR/DE/IT A-J factories stay frozen.

Turkey: indigenous precision/naval SPECTER mix (Atmaca … Gokturk).
Nato/Spain: Spanish-identity roster owned by Side=Nato so the current Nato
faction can build it. The Nato faction is NOT converted to Spain in this pack.
Dorsal stamps are Spanish red-yellow-red, not NT_Flag.tga.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Satellites: CommandSet_TurkeyMissiles.ini, CommandSet_SpainMissiles.ini,
CommandButton_TurkeyMissiles.ini, CommandButton_SpainMissiles.ini,
Weapon\\Weapon_Turkey_Missiles.ini, Weapon\\Weapon_Spain_Missiles.ini.
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
import pack_s_sweden_ukraine_missiles_aj as su  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_SWEDEN_UKRAINE_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_SWEDEN_UKRAINE_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_TURKEY_SPAIN_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "2f4ea581ca6f7e14aed998af6e06f23a9d95deb9cc6fdc6b8492c0c14c6adf42"
SIZE_DATA_SRC = 369546080
SHA_ART_SRC = "fd9a4649a51aac2a1fa3f6533b2b3ffd428cdac913535125752d6210ec1fd93c"
SIZE_ART_SRC = 2116959300

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

TR_CB_KEY = r"Data\INI\CommandButton_TurkeyMissiles.ini"
TR_CS_KEY = r"Data\INI\CommandSet_TurkeyMissiles.ini"
TR_WEP_KEY = r"Data\INI\Weapon\Weapon_Turkey_Missiles.ini"
TR_FAC_KEY = (
    r"Data\INI\Object\Specter\Turkish Armed Forces"
    r"\Buildings\Turkey_MissileFactory.ini"
)
TR_DOZER_KEY = r"Data\INI\Object\Specter\Turkish Armed Forces\Wheleed\Dozer.ini"
TR_WF_KEY = r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\Warfactory.ini"
TR_SC_KEY = r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\SupplyCenter.ini"
TR_FLAG = r"Art\Textures\TR_Flag.tga"
TR_FLAG2 = r"Art\Textures\Turkey_Flag.tga"

ES_CB_KEY = r"Data\INI\CommandButton_SpainMissiles.ini"
ES_CS_KEY = r"Data\INI\CommandSet_SpainMissiles.ini"
ES_WEP_KEY = r"Data\INI\Weapon\Weapon_Spain_Missiles.ini"
ES_FAC_KEY = (
    r"Data\INI\Object\Specter\Spanish Armed Forces"
    r"\Buildings\Spain_MissileFactory.ini"
)
NT_DOZER_KEY = r"Data\INI\Object\Specter\NATO\Wheleed\Dozer.ini"
NT_WF_KEY = r"Data\INI\Object\Specter\NATO\Buildings\Warfactory.ini"
NT_SC_KEY = r"Data\INI\Object\Specter\NATO\Buildings\SupplyCenter.ini"
NT_FLAG = r"Art\Textures\NT_Flag.tga"

TR_TRUCK = "Tur_TEL.tga"
TR_TRUCKD = "Tur_TELD.tga"
ES_TRUCK = "Esp_TEL.tga"
ES_TRUCKD = "Esp_TELD.tga"

NOSE_W = (236, 228, 210)
NOSE_R = (168, 32, 28)
NOSE_B = (20, 48, 140)
NOSE_G = (20, 72, 40)

# Turkey: indigenous precision/naval. A is orange (not red). Avoids Bora/Kasirga/KAAN object names.
TURKEY_MISSILES = [
    {"slot": "A", "object": "Turkey_Atmaca", "name": "Atmaca",
     "model": "Tur_Atmaca", "modeld": "Tur_AtmacaD", "proj_model": "Tur_AtmacaM",
     "hier": b"TUR_ATMCA", "hierd": b"TUR_ATMCAD", "proj_hier": b"TUR_MSL_A",
     "tex": "Tur_AtmacaP.tga", "body": (200, 96, 28), "nose": NOSE_W,
     "expect": "orange", "km": 1000, "kg": 400, "acc": 74, "stealth": 26,
     "rebuild": 16, "price": 840,
     "role": "Coastal cruise analogue (Atmaca class; SPECTER floor)"},
    {"slot": "B", "object": "Turkey_SOM", "name": "SOM",
     "model": "Tur_SOM", "modeld": "Tur_SOMD", "proj_model": "Tur_SOMM",
     "hier": b"TUR_SOMAB", "hierd": b"TUR_SOMABD", "proj_hier": b"TUR_MSL_B",
     "tex": "Tur_SOMP.tga", "body": (12, 80, 88), "nose": NOSE_W,
     "expect": "petrol", "km": 1220, "kg": 520, "acc": 82, "stealth": 46,
     "rebuild": 24, "price": 1650,
     "role": "Stand-off analogue; Acc/CHL over payload"},
    {"slot": "C", "object": "Turkey_Tayfun", "name": "Tayfun",
     "model": "Tur_Tayfun", "modeld": "Tur_TayfunD", "proj_model": "Tur_TayfunM",
     "hier": b"TUR_TAYFC", "hierd": b"TUR_TAYFCD", "proj_hier": b"TUR_MSL_C",
     "tex": "Tur_TayfunP.tga", "body": (220, 200, 155), "nose": NOSE_R,
     "expect": "cream", "km": 1480, "kg": 650, "acc": 58, "stealth": 32,
     "rebuild": 29, "price": 2050,
     "role": "SRBM analogue; mid Acc, modest payload"},
    {"slot": "D", "object": "Turkey_Cenk", "name": "Cenk",
     "model": "Tur_Cenk", "modeld": "Tur_CenkD", "proj_model": "Tur_CenkM",
     "hier": b"TUR_CENKD", "hierd": b"TUR_CENKDD", "proj_hier": b"TUR_MSL_D",
     "tex": "Tur_CenkP.tga", "body": (24, 26, 28), "nose": NOSE_W,
     "expect": "black", "km": 1620, "kg": 1250, "acc": 38, "stealth": 18,
     "rebuild": 34, "price": 2350,
     "role": "Cheaper medium; payload over Acc/CHL"},
    {"slot": "E", "object": "Turkey_Gezgin", "name": "Gezgin",
     "model": "Tur_Gezgin", "modeld": "Tur_GezginD", "proj_model": "Tur_GezginM",
     "hier": b"TUR_GEZGE", "hierd": b"TUR_GEZGED", "proj_hier": b"TUR_MSL_E",
     "tex": "Tur_GezginP.tga", "body": (232, 234, 236), "nose": NOSE_R,
     "expect": "white", "km": 1820, "kg": 720, "acc": 80, "stealth": 54,
     "rebuild": 41, "price": 3350,
     "role": "Expensive precision cruise; Acc/CHL not payload"},
    {"slot": "F", "object": "Turkey_Yildirim", "name": "Yildirim",
     "model": "Tur_Yildrm", "modeld": "Tur_YildrmD", "proj_model": "Tur_YildrmM",
     "hier": b"TUR_YILDF", "hierd": b"TUR_YILDFD", "proj_hier": b"TUR_MSL_F",
     "tex": "Tur_YildrmP.tga", "body": (110, 114, 118), "nose": NOSE_W,
     "expect": "gray", "km": 1980, "kg": 1750, "acc": 34, "stealth": 30,
     "rebuild": 47, "price": 4250,
     "role": "Heavy-medium; payload versus Gezgin precision"},
    {"slot": "G", "object": "Turkey_Bozkurt", "name": "Bozkurt",
     "model": "Tur_Bozkrt", "modeld": "Tur_BozkrtD", "proj_model": "Tur_BozkrtM",
     "hier": b"TUR_BOZKG", "hierd": b"TUR_BOZKGD", "proj_hier": b"TUR_MSL_G",
     "tex": "Tur_BozkrtP.tga", "body": (214, 178, 28), "nose": NOSE_W,
     "expect": "yellow", "km": 2380, "kg": 1450, "acc": 64, "stealth": 50,
     "rebuild": 56, "price": 5250,
     "role": "Advanced medium-heavy; Acc/CHL cost money"},
    {"slot": "H", "object": "Turkey_Sancak", "name": "Sancak",
     "model": "Tur_Sancak", "modeld": "Tur_SancakD", "proj_model": "Tur_SancakM",
     "hier": b"TUR_SANCH", "hierd": b"TUR_SANCHD", "proj_hier": b"TUR_MSL_H",
     "tex": "Tur_SancakP.tga", "body": (20, 48, 128), "nose": NOSE_W,
     "expect": "blue", "km": 2700, "kg": 2300, "acc": 36, "stealth": 34,
     "rebuild": 69, "price": 6900,
     "role": "Heavy strike; payload over precision"},
    {"slot": "I", "object": "Turkey_Anadolu", "name": "Anadolu",
     "model": "Tur_Anadol", "modeld": "Tur_AnadolD", "proj_model": "Tur_AnadolM",
     "hier": b"TUR_ANADI", "hierd": b"TUR_ANADID", "proj_hier": b"TUR_MSL_I",
     "tex": "Tur_AnadolP.tga", "body": (16, 120, 48), "nose": NOSE_W,
     "expect": "green", "km": 3280, "kg": 2650, "acc": 52, "stealth": 56,
     "rebuild": 77, "price": 8150,
     "role": "Expensive advanced heavy; CHL/Acc versus Sancak payload"},
    {"slot": "J", "object": "Turkey_Gokturk", "name": "Gokturk",
     "model": "Tur_Goktrk", "modeld": "Tur_GoktrkD", "proj_model": "Tur_GoktrkM",
     "hier": b"TUR_GOKTJ", "hierd": b"TUR_GOKTJD", "proj_hier": b"TUR_MSL_J",
     "tex": "Tur_GoktrkP.tga", "body": (80, 92, 40), "nose": NOSE_W,
     "expect": "muddy", "km": 3820, "kg": 3700, "acc": 30, "stealth": 24,
     "rebuild": 93, "price": 9450,
     "role": "Flagship long-range; payload costs Acc/CHL versus Anadolu"},
]

# Spain-ready Nato roster. Spanish names/visuals. A is cream (not red). Side=Nato.
SPAIN_MISSILES = [
    {"slot": "A", "object": "Spain_Albatros", "name": "Albatros",
     "model": "Esp_Albatr", "modeld": "Esp_AlbatrD", "proj_model": "Esp_AlbatrM",
     "hier": b"ESP_ALBTA", "hierd": b"ESP_ALBTAD", "proj_hier": b"ESP_MSL_A",
     "tex": "Esp_AlbatrP.tga", "body": (236, 220, 170), "nose": NOSE_R,
     "expect": "cream", "km": 1000, "kg": 400, "acc": 60, "stealth": 20,
     "rebuild": 15, "price": 770,
     "role": "Naval cruise analogue; SPECTER floor"},
    {"slot": "B", "object": "Spain_Halcon", "name": "Halcon",
     "model": "Esp_Halcon", "modeld": "Esp_HalconD", "proj_model": "Esp_HalconM",
     "hier": b"ESP_HALCB", "hierd": b"ESP_HALCBD", "proj_hier": b"ESP_MSL_B",
     "tex": "Esp_HalconP.tga", "body": (214, 178, 28), "nose": NOSE_W,
     "expect": "yellow", "km": 1160, "kg": 880, "acc": 44, "stealth": 22,
     "rebuild": 21, "price": 1420,
     "role": "Tactical analogue; earlier payload than Turkey SOM"},
    {"slot": "C", "object": "Spain_Tridente", "name": "Tridente",
     "model": "Esp_Tridnt", "modeld": "Esp_TridntD", "proj_model": "Esp_TridntM",
     "hier": b"ESP_TRIDC", "hierd": b"ESP_TRIDCD", "proj_hier": b"ESP_MSL_C",
     "tex": "Esp_TridntP.tga", "body": (6, 92, 100), "nose": NOSE_W,
     "expect": "petrol", "km": 1380, "kg": 500, "acc": 88, "stealth": 48,
     "rebuild": 26, "price": 1980,
     "role": "Precision medium; Acc/CHL standout, light warhead"},
    {"slot": "D", "object": "Spain_Pelayo", "name": "Pelayo",
     "model": "Esp_Pelayo", "modeld": "Esp_PelayoD", "proj_model": "Esp_PelayoM",
     "hier": b"ESP_PELYD", "hierd": b"ESP_PELYDD", "proj_hier": b"ESP_MSL_D",
     "tex": "Esp_PelayoP.tga", "body": (8, 140, 56), "nose": NOSE_W,
     "expect": "green", "km": 1560, "kg": 1180, "acc": 36, "stealth": 16,
     "rebuild": 32, "price": 2200,
     "role": "Crude medium; heavier/cheaper Acc than Tridente"},
    {"slot": "E", "object": "Spain_Cid", "name": "Cid",
     "model": "Esp_Cid", "modeld": "Esp_CidD", "proj_model": "Esp_CidM",
     "hier": b"ESP_CIDAE", "hierd": b"ESP_CIDAED", "proj_hier": b"ESP_MSL_E",
     "tex": "Esp_CidP.tga", "body": (244, 244, 248), "nose": NOSE_R,
     "expect": "white", "km": 1720, "kg": 660, "acc": 70, "stealth": 64,
     "rebuild": 37, "price": 3050,
     "role": "CHL standout medium; not a Turkey Gezgin copy"},
    {"slot": "F", "object": "Spain_Castilla", "name": "Castilla",
     "model": "Esp_Castil", "modeld": "Esp_CastilD", "proj_model": "Esp_CastilM",
     "hier": b"ESP_CASTF", "hierd": b"ESP_CASTFD", "proj_hier": b"ESP_MSL_F",
     "tex": "Esp_CastilP.tga", "body": (160, 24, 32), "nose": NOSE_W,
     "expect": "red", "km": 1880, "kg": 2150, "acc": 30, "stealth": 26,
     "rebuild": 45, "price": 3980,
     "role": "Early heavy; payload before Turkey Yildirim"},
    {"slot": "G", "object": "Spain_Armada", "name": "Armada",
     "model": "Esp_Armada", "modeld": "Esp_ArmadaD", "proj_model": "Esp_ArmadaM",
     "hier": b"ESP_ARMAG", "hierd": b"ESP_ARMAGD", "proj_hier": b"ESP_MSL_G",
     "tex": "Esp_ArmadaP.tga", "body": (128, 124, 118), "nose": NOSE_W,
     "expect": "gray", "km": 2220, "kg": 1500, "acc": 56, "stealth": 42,
     "rebuild": 52, "price": 4750,
     "role": "Naval heavy-medium; not Turkey Bozkurt"},
    {"slot": "H", "object": "Spain_Escorial", "name": "Escorial",
     "model": "Esp_Escorl", "modeld": "Esp_EscorlD", "proj_model": "Esp_EscorlM",
     "hier": b"ESP_ESCRH", "hierd": b"ESP_ESCRHD", "proj_hier": b"ESP_MSL_H",
     "tex": "Esp_EscorlP.tga", "body": (20, 22, 28), "nose": NOSE_W,
     "expect": "black", "km": 2520, "kg": 1250, "acc": 68, "stealth": 68,
     "rebuild": 57, "price": 5350,
     "role": "Toughness over payload; CHL versus Castilla / Sancak"},
    {"slot": "I", "object": "Spain_Hispania", "name": "Hispania",
     "model": "Esp_Hispn", "modeld": "Esp_HispnD", "proj_model": "Esp_HispnM",
     "hier": b"ESP_HISPI", "hierd": b"ESP_HISPID", "proj_hier": b"ESP_MSL_I",
     "tex": "Esp_HispnP.tga", "body": (176, 72, 20), "nose": NOSE_W,
     "expect": "orange", "km": 3080, "kg": 2450, "acc": 44, "stealth": 38,
     "rebuild": 73, "price": 7250,
     "role": "Limited strategic; below Turkey Anadolu Acc/CHL"},
    {"slot": "J", "object": "Spain_Iberia", "name": "Iberia",
     "model": "Esp_Iberia", "modeld": "Esp_IberiaD", "proj_model": "Esp_IberiaM",
     "hier": b"ESP_IBERJ", "hierd": b"ESP_IBERJD", "proj_hier": b"ESP_MSL_J",
     "tex": "Esp_IberiaP.tga", "body": (40, 80, 170), "nose": NOSE_R,
     "expect": "blue", "km": 3680, "kg": 4900, "acc": 22, "stealth": 20,
     "rebuild": 90, "price": 10100,
     "role": "Flagship; heavier/cruder/shorter than Turkey Gokturk"},
]


def _country(code, label, side, prefix, builder, fac_obj, fac_cs, fac_btn,
             fac_key, cb_key, cs_key, wep_key, wep_marker, path, truck, truckd,
             truck_key, truckd_key, flag_fn, flag_check, missiles, bases,
             wf_keep=None, supply_keep=None):
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
    }


TR_MID = (72, 84, 48)
TR_DARK = (40, 52, 36)
TR_METAL = (148, 140, 118)
ES_MID = (168, 124, 72)
ES_DARK = (72, 40, 32)
ES_METAL = (176, 156, 128)


def make_turkey_flag() -> Image.Image:
    w, h = 900, 600
    red = (227, 10, 23, 255)
    white = (255, 255, 255, 255)
    im = Image.new("RGBA", (w, h), red)
    draw = ImageDraw.Draw(im)
    cx, cy = int(w * 0.38), h // 2
    r_out = int(h * 0.28)
    draw.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill=white)
    ox = cx + int(r_out * 0.28)
    r_in = int(r_out * 0.78)
    draw.ellipse([ox - r_in, cy - r_in, ox + r_in, cy + r_in], fill=red)
    sx = cx + int(r_out * 0.72)
    star = int(h * 0.09)
    draw.polygon(
        [
            (sx, cy - star),
            (sx + int(star * 0.28), cy - int(star * 0.22)),
            (sx + star, cy - int(star * 0.18)),
            (sx + int(star * 0.38), cy + int(star * 0.08)),
            (sx + int(star * 0.55), cy + star),
            (sx, cy + int(star * 0.38)),
            (sx - int(star * 0.55), cy + star),
            (sx - int(star * 0.38), cy + int(star * 0.08)),
            (sx - star, cy - int(star * 0.18)),
            (sx - int(star * 0.28), cy - int(star * 0.22)),
        ],
        fill=white,
    )
    return im


def make_spain_flag() -> Image.Image:
    w, h = 900, 600
    red = (198, 11, 30, 255)
    yellow = (250, 189, 0, 255)
    im = Image.new("RGBA", (w, h), red)
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, w, h // 4], fill=red)
    draw.rectangle([0, h // 4, w, 3 * h // 4], fill=yellow)
    draw.rectangle([0, 3 * h // 4, w, h], fill=red)
    return im


def has_turkey_flag(counts: dict[str, int]) -> bool:
    return counts.get("red", 0) >= 4 and counts.get("white", 0) >= 2


def has_spain_flag(counts: dict[str, int]) -> bool:
    yellowish = counts.get("yellow", 0) + counts.get("orange", 0) + counts.get("cream", 0)
    return counts.get("red", 0) >= 3 and yellowish >= 3


COUNTRY_DEFS = [
    _country(
        "TR", "Turkey", "Turkey", "Turkey",
        "TurkeyDozerCommandSet", "Turkey_MissileFactory",
        "Turkey_MissileFactoryCommandSet",
        "Command_ConstructTurkey_MissileFactory",
        TR_FAC_KEY, TR_CB_KEY, TR_CS_KEY, TR_WEP_KEY,
        "; ===== Turkey missiles A-J (Weapon.ini load path for Command_FireMainWeapon) =====",
        r"Data\INI\Object\Specter\Turkish Armed Forces",
        TR_TRUCK, TR_TRUCKD, rf"Art\Textures\{TR_TRUCK}", rf"Art\Textures\{TR_TRUCKD}",
        make_turkey_flag, has_turkey_flag, TURKEY_MISSILES,
        {"dark": TR_DARK, "mid": TR_MID, "metal": TR_METAL},
    ),
    _country(
        "ES", "Spain", "Nato", "Spain",
        "NatoDozerCommandSet", "Spain_MissileFactory",
        "Spain_MissileFactoryCommandSet",
        "Command_ConstructSpain_MissileFactory",
        ES_FAC_KEY, ES_CB_KEY, ES_CS_KEY, ES_WEP_KEY,
        "; ===== Spain-ready Nato missiles A-J (Weapon.ini load path for Command_FireMainWeapon) =====",
        r"Data\INI\Object\Specter\Spanish Armed Forces",
        ES_TRUCK, ES_TRUCKD, rf"Art\Textures\{ES_TRUCK}", rf"Art\Textures\{ES_TRUCKD}",
        make_spain_flag, has_spain_flag, SPAIN_MISSILES,
        {"dark": ES_DARK, "mid": ES_MID, "metal": ES_METAL},
        wf_keep="Command_ConstructNatoWarFactory",
        supply_keep="NatoSupplyCenter",
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

assert TURKEY_MISSILES[0]["expect"] != "red" and SPAIN_MISSILES[0]["expect"] != "red"
assert [m["expect"] for m in TURKEY_MISSILES] != [m["expect"] for m in SPAIN_MISSILES]
assert [m["expect"] for m in TURKEY_MISSILES] != [m["expect"] for m in su.SWEDEN_MISSILES]
assert [m["expect"] for m in SPAIN_MISSILES] != [m["expect"] for m in su.UKRAINE_MISSILES]
assert [m["expect"] for m in TURKEY_MISSILES] != [m["expect"] for m in gi.GERMANY_MISSILES]
assert [m["expect"] for m in SPAIN_MISSILES] != [m["expect"] for m in gi.ITALY_MISSILES]
assert [m["expect"] for m in TURKEY_MISSILES] != [m["expect"] for m in bf.BRITAIN_MISSILES]
assert [m["expect"] for m in SPAIN_MISSILES] != [m["expect"] for m in bf.FRANCE_MISSILES]
assert TURKEY_MISSILES[0]["acc"] > SPAIN_MISSILES[0]["acc"]
assert SPAIN_MISSILES[5]["kg"] > TURKEY_MISSILES[5]["kg"]
assert SPAIN_MISSILES[-1]["kg"] > TURKEY_MISSILES[-1]["kg"]
assert TURKEY_MISSILES[-1]["km"] > SPAIN_MISSILES[-1]["km"]


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
        "TURKEY + SPAIN-READY NATO A-J MISSILE ROSTERS",
        "",
        "Baseline packed last-wins: SPECTER_SWEDEN_UKRAINE_MISSILES_AJ (PR #649).",
        "Turkey and Nato had no missile factory. Dozer slot 14 constructed",
        "isolated Iraq_AlFahdMissileFactoryBuilding. That slot now constructs",
        "Turkey_MissileFactory / Spain_MissileFactory. Spain objects use Side=Nato",
        "so FactionNato can build them. The Nato faction is NOT converted to Spain.",
        "War Factory, Lgm30, THAAD, NASAMS, SkySabre, Skyranger, SE/UA/GB/FR/DE/IT",
        "A-J, NT_Flag.tga, and existing air weapons stay frozen.",
        "",
        "SPECTER design values. Not claimed real-world range or payload.",
        "Turkey: indigenous precision/naval mix. Spain: independent tactical/",
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
        TR_DOZER_KEY, TR_WF_KEY, TR_SC_KEY, NT_DOZER_KEY, NT_WF_KEY, NT_SC_KEY,
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
        TR_FLAG, TR_FLAG2, NT_FLAG, su.SE_FLAG, su.UA_FLAG,
        bf.GB_FLAG, bf.FR_FLAG, gi.DE_FLAG, gi.IT_FLAG,
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

    for key in (TR_CS_KEY, ES_CS_KEY, TR_CB_KEY, ES_CB_KEY, TR_WEP_KEY, ES_WEP_KEY):
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
        "TurkeyWarfactoryCommandSet",
        "NatoWarfactoryCommandSet",
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
            c["wf_keep"],
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
        own = f"CB_{c['prefix'].upper()}_"
        foreign = (
            "CB_VIETNAM_", "CB_UAE_", "CB_JAPAN_", "CB_GERMANY_", "CB_ITALY_",
            "CB_BRITAIN_", "CB_FRANCE_", "CB_SWEDEN_", "CB_UKRAINE_",
            "CB_TURKEY_", "CB_SPAIN_",
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
    ):
        if sk.last_block(wep_text, "Weapon", wep_name) != sk.last_block(src_wep, "Weapon", wep_name):
            fails.append(f"{wep_name} mutated")
    tr_avg = Image.open(io.BytesIO(art[rf"Art\Textures\{TR_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    es_avg = Image.open(io.BytesIO(art[rf"Art\Textures\{ES_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    se_avg = Image.open(io.BytesIO(src_art[rf"Art\Textures\{su.SE_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    ua_avg = Image.open(io.BytesIO(src_art[rf"Art\Textures\{su.UA_TRUCK}"])).convert("RGB").resize(
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
    donors = (se_avg, ua_avg, gb_avg, fr_avg, de_avg, it_avg, irq_avg)
    if tr_avg == es_avg:
        fails.append(f"trucks identical {tr_avg}")
    if tr_avg in donors or es_avg in donors:
        fails.append(f"truck still donor {tr_avg} {es_avg}")
    if NT_FLAG not in art or art[NT_FLAG] != src_art[NT_FLAG]:
        fails.append("NT_Flag.tga mutated")
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
        raise SystemExit("DATA baseline is not SPECTER_SWEDEN_UKRAINE_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_SRC or SRC_ART.stat().st_size != SIZE_ART_SRC:
        raise SystemExit("ART baseline is not SPECTER_SWEDEN_UKRAINE_MISSILES_AJ")

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
    zip_path = ROOT / "patch/Release/SPECTER_TURKEY_SPAIN_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #649 s-sweden-ukraine-missiles-aj + #648 + #647 + #646 + #645",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "TURKEY_FACTORY_NEW=YES",
        "SPAIN_FACTORY_NEW=YES",
        "NATO_FACTION_NOT_CONVERTED=YES",
        "SPAIN_OBJECTS_SIDE=Nato",
        "TR_NT_FLAGS_FROZEN=YES",
        "SE_UA_GB_FR_DE_IT_AJ_KEPT=YES",
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
            "ZIP_FILE=SPECTER_TURKEY_SPAIN_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #649",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-turkey-spain-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-turkey-spain-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-turkey-spain-missiles-aj/SPECTER_TURKEY_SPAIN_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-turkey-spain-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-turkey-spain-missiles-aj",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Turkey complete missile roster A-J plus Spain-ready Nato missile roster A-J.\n"
        "New factories replace isolated Iraq factory construct on Turkey and Nato Dozer slot 14.\n"
        "Spain_MissileFactory and Spain_* launchers use Side=Nato. The Nato faction is NOT converted.\n"
        "Existing War Factories, TR/NT flags, Lgm30, THAAD, SE/UA/GB/FR/DE/IT A-J, and air weapons stay frozen.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Turkey + Spain-ready Nato missiles A-J\n\n"
        "- New Turkey_MissileFactory and Spain_MissileFactory. Rally/Sell retained.\n"
        "- Replaces isolated Iraq factory construct on Turkey and Nato Dozer slot 14.\n"
        "- Turkey: indigenous precision/naval SPECTER mix (Atmaca … Gokturk).\n"
        "- Spain-ready Nato: Spanish names/visuals (Albatros … Iberia), Side=Nato.\n"
        "- Nato faction is NOT converted to Spain. NT_Flag.tga remains the Nato flag.\n"
        "- Existing TR flags, War Factories, Lgm30, THAAD, SE/UA/GB/FR/DE/IT A-J, and air weapons preserved.\n"
        "- Tooltips include Acc/100 and Radar Stealth/100 with caveats.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_TurkeyMissiles.ini last-wins TurkeyDozerCommandSet.\n"
        "CommandSet_SpainMissiles.ini last-wins NatoDozerCommandSet (Spain factory on slot 14).\n"
        "Weapon\\Weapon_Turkey_Missiles.ini and Weapon_Spain_Missiles.ini last-win factory pairs.\n"
        "Turkey_Weapon_SOM_F16C air weapon is unchanged. Weapon_Turkey_SOM is the factory missile.\n"
        "TR_Flag.tga, Turkey_Flag.tga, and NT_Flag.tga are frozen. Dorsal stamps are generated.\n"
        "Sweden/Ukraine #649, Britain/France #648, Germany/Italy #647, Vietnam/SK #646, UAE/Japan #645, Saudi #644, NK, India, Pakistan, Iraq, and 9P117 stay frozen.\n"
    )
    (OUT / "SPAIN_CONVERSION.txt").write_text(
        "FUTURE NATO-TO-SPAIN CONVERSION (not done in this pack)\n"
        "\n"
        "Already Spain-specific (keep, do not duplicate):\n"
        "  Spain_MissileFactory, Spain_MissileFactoryCommandSet\n"
        "  Command_ConstructSpain_MissileFactory\n"
        "  Spain_Albatros … Spain_Iberia launchers and projectiles\n"
        "  CB_SPAIN_MISSILE_A-J, CONTROLBAR:SpainMissileA-J\n"
        "  CommandSet_SpainMissiles.ini, CommandButton_SpainMissiles.ini\n"
        "  Weapon\\Weapon_Spain_Missiles.ini\n"
        "  Art\\Textures\\Esp_TEL.tga / Esp_TELD.tga and Esp_* skins\n"
        "\n"
        "Must remain Nato for current load (change in the conversion task):\n"
        "  FactionNato (Side=Nato, StartingUnit0=NatoVehicleDozer,\n"
        "    StartingBuilding=NatoCommandCenter, DisplayName=INI:FactionNatoForces)\n"
        "  NatoDozerCommandSet (builder name referenced by NatoVehicleDozer)\n"
        "  NatoVehicleDozer CommandSet = NatoDozerCommandSet\n"
        "  NatoWarFactory, NatoSupplyCenter, NatoCommandCenter, and other Nato*\n"
        "  NT_Flag.tga (Nato flag). Missile dorsal stamps are already Spanish.\n"
        "  Spain_* object Side=Nato (required so FactionNato can own them now)\n"
        "\n"
        "Conversion checklist:\n"
        "  1. Add FactionSpain Side=Spain. Retire or hide FactionNato.\n"
        "  2. Rename or last-win NatoDozerCommandSet -> SpainDozerCommandSet and\n"
        "     point the Spain dozer CommandSet at it. Keep slot 14 =\n"
        "     Command_ConstructSpain_MissileFactory.\n"
        "  3. Change Side=Nato to Side=Spain on Spain_MissileFactory and Spain_* TELs.\n"
        "  4. Provide SpainSupplyCenter (or keep NatoSupplyCenter in the OR prereq\n"
        "     list until renamed). Do not add a second missile factory.\n"
        "  5. Replace NT_Flag.tga / Nato UI with Spanish country identity.\n"
        "  6. Leave Turkey_MissileFactory and Turkey A-J untouched.\n"
        "  7. Do not create NATO-named duplicate missiles.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:70]))


if __name__ == "__main__":
    main()
