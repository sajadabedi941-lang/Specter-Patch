#!/usr/bin/env python3
"""Britain + France missile rosters A-J on the Germany/Italy baseline.

Baseline: packed SPECTER_GERMANY_ITALY_MISSILES_AJ (PR #647 on #646 / #645 / #644).

Packed last-wins audit: Britain and France are playable NATO sides
(FactionBritain / FactionFrance, Side=Britain / France). Builder is the Dozer
only (BritainVehicleDozer / FranceVehicleDozer). Last-wins BritainDozerCommandSet
and FranceDozerCommandSet live in CommandSet.ini. Slot 14 constructs isolated
Sell-only Iraq_AlFahdMissileFactoryBuilding. No dedicated missile factory.
Existing UK_Flag.tga / FR_Flag.tga, War Factories, Lgm30 slot 12, THAAD slot 15,
Germany/Italy A-J factories, and air-launched Britain_Weapon_StormShadow /
France_Weapon_SCALP_RafaleB stay frozen.

Britain: naval/cruise + mixed medium + expensive strategic SPECTER mix.
France: independent deterrent mix (earlier heavy, CHL standouts, cruder flagship).
Neither is a rename of the other or of Germany/Italy. Names are public-program /
place inspiration; km/kg/Acc/CHL are SPECTER design values, not claimed real specs.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Satellites: CommandSet_BritainMissiles.ini, CommandSet_FranceMissiles.ini,
CommandButton_BritainMissiles.ini, CommandButton_FranceMissiles.ini,
Weapon\\Weapon_Britain_Missiles.ini, Weapon\\Weapon_France_Missiles.ini.
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

SRC_DATA = ROOT / "patch/Release/SPECTER_GERMANY_ITALY_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_GERMANY_ITALY_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_BRITAIN_FRANCE_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "3e42718ca5aa9bcfa8130537e5fba0c8ef664a059e849551ddfe419fe15aabf6"
SIZE_DATA_SRC = 368876498
SHA_ART_SRC = "a60a122876cefdd842f4a16992ddde1e9082c2684ee2df3c253aeea43ca07ca3"
SIZE_ART_SRC = 1925909944

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

GB_CB_KEY = r"Data\INI\CommandButton_BritainMissiles.ini"
GB_CS_KEY = r"Data\INI\CommandSet_BritainMissiles.ini"
GB_WEP_KEY = r"Data\INI\Weapon\Weapon_Britain_Missiles.ini"
GB_FAC_KEY = (
    r"Data\INI\Object\Specter\British Armed Forces"
    r"\Buildings\Britain_MissileFactory.ini"
)
GB_DOZER_KEY = r"Data\INI\Object\Specter\British Armed Forces\Wheleed\Dozer.ini"
GB_WF_KEY = r"Data\INI\Object\Specter\British Armed Forces\Buildings\Warfactory.ini"
GB_SC_KEY = r"Data\INI\Object\Specter\British Armed Forces\Buildings\SupplyCenter.ini"
GB_FLAG = r"Art\Textures\UK_Flag.tga"

FR_CB_KEY = r"Data\INI\CommandButton_FranceMissiles.ini"
FR_CS_KEY = r"Data\INI\CommandSet_FranceMissiles.ini"
FR_WEP_KEY = r"Data\INI\Weapon\Weapon_France_Missiles.ini"
FR_FAC_KEY = (
    r"Data\INI\Object\Specter\French Armed Forces"
    r"\Buildings\France_MissileFactory.ini"
)
FR_DOZER_KEY = r"Data\INI\Object\Specter\French Armed Forces\Wheleed\Dozer.ini"
FR_WF_KEY = r"Data\INI\Object\Specter\French Armed Forces\Buildings\Warfactory.ini"
FR_SC_KEY = r"Data\INI\Object\Specter\French Armed Forces\Buildings\SupplyCenter.ini"
FR_FLAG = r"Art\Textures\FR_Flag.tga"

GB_TRUCK = "Gbr_TEL.tga"
GB_TRUCKD = "Gbr_TELD.tga"
FR_TRUCK = "Fra_TEL.tga"
FR_TRUCKD = "Fra_TELD.tga"

NOSE_W = (236, 228, 210)
NOSE_R = (168, 32, 28)
NOSE_B = (20, 48, 140)
NOSE_G = (20, 72, 40)

# Britain: naval/cruise + mixed medium + expensive strategic. A is olive, not red.
BRITAIN_MISSILES = [
    {"slot": "A", "object": "Britain_Spear", "name": "Spear",
     "model": "Gbr_Spear", "modeld": "Gbr_SpearD", "proj_model": "Gbr_SpearM",
     "hier": b"GBR_SPEAA", "hierd": b"GBR_SPEAAD", "proj_hier": b"GBR_MSL_A",
     "tex": "Gbr_SpearP.tga", "body": (20, 92, 40), "nose": NOSE_W,
     "expect": "green", "km": 1000, "kg": 400, "acc": 80, "stealth": 26,
     "rebuild": 15, "price": 850,
     "role": "Tactical cruise analogue (SPEAR class; SPECTER floor range)"},
    {"slot": "B", "object": "Britain_Perseus", "name": "Perseus",
     "model": "Gbr_Perseu", "modeld": "Gbr_PerseuD", "proj_model": "Gbr_PerseuM",
     "hier": b"GBR_PERSB", "hierd": b"GBR_PERSBD", "proj_hier": b"GBR_MSL_B",
     "tex": "Gbr_PerseuP.tga", "body": (16, 36, 110), "nose": NOSE_W,
     "expect": "blue", "km": 1150, "kg": 550, "acc": 70, "stealth": 32,
     "rebuild": 21, "price": 1350,
     "role": "FC/ASW analogue; naval-leaning medium, modest payload"},
    {"slot": "C", "object": "Britain_FireShadow", "name": "FireShadow",
     "model": "Gbr_FireSh", "modeld": "Gbr_FireShD", "proj_model": "Gbr_FireShM",
     "hier": b"GBR_FIREC", "hierd": b"GBR_FIRECD", "proj_hier": b"GBR_MSL_C",
     "tex": "Gbr_FireShP.tga", "body": (210, 186, 140), "nose": NOSE_B,
     "expect": "cream", "km": 1350, "kg": 500, "acc": 74, "stealth": 44,
     "rebuild": 26, "price": 1800,
     "role": "Loitering-strike analogue; CHL over payload"},
    {"slot": "D", "object": "Britain_Blackbuck", "name": "Blackbuck",
     "model": "Gbr_Blackb", "modeld": "Gbr_BlackbD", "proj_model": "Gbr_BlackbM",
     "hier": b"GBR_BLCKD", "hierd": b"GBR_BLCKDD", "proj_hier": b"GBR_MSL_D",
     "tex": "Gbr_BlackbP.tga", "body": (214, 168, 24), "nose": NOSE_W,
     "expect": "yellow", "km": 1550, "kg": 1000, "acc": 52, "stealth": 24,
     "rebuild": 34, "price": 2400,
     "role": "Cheaper medium; heavier than FireShadow, lower Acc/CHL"},
    {"slot": "E", "object": "Britain_Skybolt", "name": "Skybolt",
     "model": "Gbr_Skyblt", "modeld": "Gbr_SkybltD", "proj_model": "Gbr_SkybltM",
     "hier": b"GBR_SKYBE", "hierd": b"GBR_SKYBED", "proj_hier": b"GBR_MSL_E",
     "tex": "Gbr_SkybltP.tga", "body": (96, 104, 116), "nose": NOSE_B,
     "expect": "gray", "km": 1750, "kg": 750, "acc": 86, "stealth": 50,
     "rebuild": 42, "price": 3800,
     "role": "Expensive precision medium; Acc standout, not the heaviest"},
    {"slot": "F", "object": "Britain_Vanguard", "name": "Vanguard",
     "model": "Gbr_Vangrd", "modeld": "Gbr_VangrdD", "proj_model": "Gbr_VangrdM",
     "hier": b"GBR_VANGF", "hierd": b"GBR_VANGFD", "proj_hier": b"GBR_MSL_F",
     "tex": "Gbr_VangrdP.tga", "body": (8, 88, 96), "nose": NOSE_W,
     "expect": "petrol", "km": 2000, "kg": 1600, "acc": 46, "stealth": 34,
     "rebuild": 50, "price": 4500,
     "role": "SSBN-class analogue; payload over Acc versus Skybolt"},
    {"slot": "G", "object": "Britain_Polaris", "name": "Polaris",
     "model": "Gbr_Polar", "modeld": "Gbr_PolarD", "proj_model": "Gbr_PolarM",
     "hier": b"GBR_POLAG", "hierd": b"GBR_POLAGD", "proj_hier": b"GBR_MSL_G",
     "tex": "Gbr_PolarP.tga", "body": (28, 30, 32), "nose": NOSE_W,
     "expect": "black", "km": 2400, "kg": 2000, "acc": 64, "stealth": 46,
     "rebuild": 60, "price": 5800,
     "role": "Historic SLBM analogue; Acc/CHL cost money"},
    {"slot": "H", "object": "Britain_Resolution", "name": "Resolution",
     "model": "Gbr_Resolu", "modeld": "Gbr_ResoluD", "proj_model": "Gbr_ResoluM",
     "hier": b"GBR_RESLH", "hierd": b"GBR_RESLHD", "proj_hier": b"GBR_MSL_H",
     "tex": "Gbr_ResoluP.tga", "body": (186, 78, 24), "nose": NOSE_W,
     "expect": "orange", "km": 2700, "kg": 2800, "acc": 40, "stealth": 38,
     "rebuild": 72, "price": 7200,
     "role": "Heavy strike; payload over precision"},
    {"slot": "I", "object": "Britain_Sovereign", "name": "Sovereign",
     "model": "Gbr_Sovrng", "modeld": "Gbr_SovrngD", "proj_model": "Gbr_SovrngM",
     "hier": b"GBR_SOVRI", "hierd": b"GBR_SOVRID", "proj_hier": b"GBR_MSL_I",
     "tex": "Gbr_SovrngP.tga", "body": (236, 230, 214), "nose": NOSE_B,
     "expect": "white", "km": 3200, "kg": 3000, "acc": 58, "stealth": 58,
     "rebuild": 80, "price": 8600,
     "role": "Expensive advanced heavy; CHL/Acc versus Resolution payload"},
    {"slot": "J", "object": "Britain_Trafalgar", "name": "Trafalgar",
     "model": "Gbr_Trafal", "modeld": "Gbr_TrafalD", "proj_model": "Gbr_TrafalM",
     "hier": b"GBR_TRAFJ", "hierd": b"GBR_TRAFJD", "proj_hier": b"GBR_MSL_J",
     "tex": "Gbr_TrafalP.tga", "body": (148, 28, 36), "nose": NOSE_W,
     "expect": "red", "km": 3900, "kg": 4200, "acc": 36, "stealth": 30,
     "rebuild": 96, "price": 9800,
     "role": "Flagship long-range; payload costs Acc/CHL versus Sovereign"},
]

# France: independent deterrent. A is azure, not red. Earlier heavy, CHL standouts.
FRANCE_MISSILES = [
    {"slot": "A", "object": "France_MdCN", "name": "MdCN",
     "model": "Fra_MdCN", "modeld": "Fra_MdCND", "proj_model": "Fra_MdCNM",
     "hier": b"FRA_MDCNA", "hierd": b"FRA_MDCNAD", "proj_hier": b"FRA_MSL_A",
     "tex": "Fra_MdCNP.tga", "body": (32, 96, 188), "nose": NOSE_W,
     "expect": "blue", "km": 1000, "kg": 400, "acc": 62, "stealth": 20,
     "rebuild": 16, "price": 780,
     "role": "Naval cruise analogue (MdCN class; SPECTER floor)"},
    {"slot": "B", "object": "France_Hades", "name": "Hades",
     "model": "Fra_Hades", "modeld": "Fra_HadesD", "proj_model": "Fra_HadesM",
     "hier": b"FRA_HADSB", "hierd": b"FRA_HADSBD", "proj_hier": b"FRA_MSL_B",
     "tex": "Fra_HadesP.tga", "body": (12, 96, 36), "nose": NOSE_W,
     "expect": "green", "km": 1200, "kg": 850, "acc": 44, "stealth": 24,
     "rebuild": 22, "price": 1450,
     "role": "Historic SRBM analogue; earlier payload than Britain Perseus"},
    {"slot": "C", "object": "France_ASMPA", "name": "ASMPA",
     "model": "Fra_ASMPA", "modeld": "Fra_ASMPAD", "proj_model": "Fra_ASMPAM",
     "hier": b"FRA_ASMPC", "hierd": b"FRA_ASMPCD", "proj_hier": b"FRA_MSL_C",
     "tex": "Fra_ASMPAP.tga", "body": (240, 242, 246), "nose": NOSE_R,
     "expect": "white", "km": 1400, "kg": 500, "acc": 82, "stealth": 46,
     "rebuild": 27, "price": 2000,
     "role": "Air-sol moyenne portee analogue; Acc over payload"},
    {"slot": "D", "object": "France_Pluton", "name": "Pluton",
     "model": "Fra_Pluton", "modeld": "Fra_PlutonD", "proj_model": "Fra_PlutonM",
     "hier": b"FRA_PLUTD", "hierd": b"FRA_PLUTDD", "proj_hier": b"FRA_MSL_D",
     "tex": "Fra_PlutonP.tga", "body": (204, 156, 28), "nose": NOSE_W,
     "expect": "yellow", "km": 1500, "kg": 1100, "acc": 40, "stealth": 22,
     "rebuild": 33, "price": 2300,
     "role": "Crude medium; heavier/cheaper Acc than ASMPA"},
    {"slot": "E", "object": "France_Maginot", "name": "Maginot",
     "model": "Fra_Magino", "modeld": "Fra_MaginoD", "proj_model": "Fra_MaginoM",
     "hier": b"FRA_MAGIE", "hierd": b"FRA_MAGIED", "proj_hier": b"FRA_MSL_E",
     "tex": "Fra_MaginoP.tga", "body": (140, 136, 128), "nose": NOSE_W,
     "expect": "gray", "km": 1800, "kg": 700, "acc": 68, "stealth": 58,
     "rebuild": 38, "price": 3000,
     "role": "CHL standout medium; not a Britain Skybolt copy"},
    {"slot": "F", "object": "France_M51A", "name": "M51A",
     "model": "Fra_M51A", "modeld": "Fra_M51AD", "proj_model": "Fra_M51AM",
     "hier": b"FRA_M51AF", "hierd": b"FRA_M51AFD", "proj_hier": b"FRA_MSL_F",
     "tex": "Fra_M51AP.tga", "body": (152, 28, 48), "nose": NOSE_W,
     "expect": "red", "km": 1900, "kg": 2200, "acc": 34, "stealth": 30,
     "rebuild": 48, "price": 4100,
     "role": "Early heavy SLBM analogue; payload before Britain Vanguard"},
    {"slot": "G", "object": "France_Triomphant", "name": "Triomphant",
     "model": "Fra_Triomp", "modeld": "Fra_TriompD", "proj_model": "Fra_TriompM",
     "hier": b"FRA_TRIOG", "hierd": b"FRA_TRIOGD", "proj_hier": b"FRA_MSL_G",
     "tex": "Fra_TriompP.tga", "body": (18, 22, 40), "nose": NOSE_W,
     "expect": "black", "km": 2200, "kg": 1600, "acc": 60, "stealth": 42,
     "rebuild": 54, "price": 5000,
     "role": "Balanced SSBN analogue; not Britain Polaris"},
    {"slot": "H", "object": "France_Rubis", "name": "Rubis",
     "model": "Fra_Rubis", "modeld": "Fra_RubisD", "proj_model": "Fra_RubisM",
     "hier": b"FRA_RUBIH", "hierd": b"FRA_RUBIHD", "proj_hier": b"FRA_MSL_H",
     "tex": "Fra_RubisP.tga", "body": (198, 96, 32), "nose": NOSE_W,
     "expect": "orange", "km": 2500, "kg": 1300, "acc": 56, "stealth": 64,
     "rebuild": 56, "price": 5200,
     "role": "Toughness over payload; CHL versus M51A / Resolution"},
    {"slot": "I", "object": "France_Terrible", "name": "Terrible",
     "model": "Fra_Terrib", "modeld": "Fra_TerribD", "proj_model": "Fra_TerribM",
     "hier": b"FRA_TERRI", "hierd": b"FRA_TERRID", "proj_hier": b"FRA_MSL_I",
     "tex": "Fra_TerribP.tga", "body": (220, 208, 170), "nose": NOSE_R,
     "expect": "cream", "km": 3100, "kg": 2600, "acc": 48, "stealth": 40,
     "rebuild": 76, "price": 7600,
     "role": "Limited strategic; below Britain Sovereign Acc/CHL"},
    {"slot": "J", "object": "France_Gaulle", "name": "Gaulle",
     "model": "Fra_Gaulle", "modeld": "Fra_GaulleD", "proj_model": "Fra_GaulleM",
     "hier": b"FRA_GAULJ", "hierd": b"FRA_GAULJD", "proj_hier": b"FRA_MSL_J",
     "tex": "Fra_GaulleP.tga", "body": (88, 96, 42), "nose": NOSE_R,
     "expect": "muddy", "km": 3700, "kg": 5000, "acc": 30, "stealth": 26,
     "rebuild": 92, "price": 10200,
     "role": "Flagship; heavier/cruder/shorter than Britain Trafalgar"},
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


GB_KHAKI = (92, 96, 58)
GB_DARK = (48, 50, 32)
GB_METAL = (128, 124, 108)
FR_HORIZON = (88, 104, 118)
FR_DARK = (36, 44, 56)
FR_METAL = (140, 144, 150)


def make_britain_flag() -> Image.Image:
    w, h = 900, 600
    blue = (1, 33, 105, 255)
    white = (255, 255, 255, 255)
    red = (200, 16, 46, 255)
    im = Image.new("RGBA", (w, h), blue)
    draw = ImageDraw.Draw(im)

    def saltire(color, thickness):
        t = thickness
        draw.polygon([(0, 0), (t, 0), (w, h - t), (w, h), (w - t, h), (0, t)], fill=color)
        draw.polygon([(w, 0), (w, t), (t, h), (0, h), (0, h - t), (w - t, 0)], fill=color)

    saltire(white, 90)
    saltire(red, 36)
    cw, ch = 150, 100
    draw.rectangle([0, (h - ch) // 2, w, (h + ch) // 2], fill=white)
    draw.rectangle([(w - cw) // 2, 0, (w + cw) // 2, h], fill=white)
    rw, rh = 90, 60
    draw.rectangle([0, (h - rh) // 2, w, (h + rh) // 2], fill=red)
    draw.rectangle([(w - rw) // 2, 0, (w + rw) // 2, h], fill=red)
    return im


def make_france_flag() -> Image.Image:
    w, h = 900, 600
    im = Image.new("RGBA", (w, h), (0, 85, 164, 255))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, w // 3, h], fill=(0, 85, 164, 255))
    draw.rectangle([w // 3, 0, 2 * w // 3, h], fill=(255, 255, 255, 255))
    draw.rectangle([2 * w // 3, 0, w, h], fill=(239, 65, 53, 255))
    return im


def has_britain_flag(counts: dict[str, int]) -> bool:
    return (
        counts.get("blue", 0) >= 3
        and counts.get("red", 0) >= 3
        and counts.get("white", 0) >= 3
    )


def has_france_flag(counts: dict[str, int]) -> bool:
    return (
        counts.get("blue", 0) >= 3
        and counts.get("white", 0) >= 3
        and counts.get("red", 0) >= 3
        and counts.get("green", 0) == 0
    )


COUNTRY_DEFS = [
    _country(
        "GB", "Britain", "Britain", "Britain",
        "BritainDozerCommandSet", "Britain_MissileFactory",
        "Britain_MissileFactoryCommandSet",
        "Command_ConstructBritain_MissileFactory",
        GB_FAC_KEY, GB_CB_KEY, GB_CS_KEY, GB_WEP_KEY,
        "; ===== Britain missiles A-J (Weapon.ini load path for Command_FireMainWeapon) =====",
        r"Data\INI\Object\Specter\British Armed Forces",
        GB_TRUCK, GB_TRUCKD, rf"Art\Textures\{GB_TRUCK}", rf"Art\Textures\{GB_TRUCKD}",
        make_britain_flag, has_britain_flag, BRITAIN_MISSILES,
        {"dark": GB_DARK, "mid": GB_KHAKI, "metal": GB_METAL},
    ),
    _country(
        "FR", "France", "France", "France",
        "FranceDozerCommandSet", "France_MissileFactory",
        "France_MissileFactoryCommandSet",
        "Command_ConstructFrance_MissileFactory",
        FR_FAC_KEY, FR_CB_KEY, FR_CS_KEY, FR_WEP_KEY,
        "; ===== France missiles A-J (Weapon.ini load path for Command_FireMainWeapon) =====",
        r"Data\INI\Object\Specter\French Armed Forces",
        FR_TRUCK, FR_TRUCKD, rf"Art\Textures\{FR_TRUCK}", rf"Art\Textures\{FR_TRUCKD}",
        make_france_flag, has_france_flag, FRANCE_MISSILES,
        {"dark": FR_DARK, "mid": FR_HORIZON, "metal": FR_METAL},
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

assert BRITAIN_MISSILES[0]["expect"] != "red" and FRANCE_MISSILES[0]["expect"] != "red"
assert [m["expect"] for m in BRITAIN_MISSILES] != [m["expect"] for m in FRANCE_MISSILES]
assert [m["expect"] for m in BRITAIN_MISSILES] != [m["expect"] for m in gi.GERMANY_MISSILES]
assert [m["expect"] for m in FRANCE_MISSILES] != [m["expect"] for m in gi.ITALY_MISSILES]
assert BRITAIN_MISSILES[0]["acc"] > FRANCE_MISSILES[0]["acc"]
assert FRANCE_MISSILES[5]["kg"] > BRITAIN_MISSILES[5]["kg"]
assert FRANCE_MISSILES[-1]["kg"] > BRITAIN_MISSILES[-1]["kg"]
assert BRITAIN_MISSILES[-1]["km"] > FRANCE_MISSILES[-1]["km"]


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
        "BRITAIN + FRANCE A-J MISSILE ROSTERS",
        "",
        "Baseline packed last-wins: SPECTER_GERMANY_ITALY_MISSILES_AJ (PR #647).",
        "Britain and France had no missile factory. Dozer slot 14 constructed",
        "isolated Iraq_AlFahdMissileFactoryBuilding. That slot now constructs",
        "the country factory. War Factory, Lgm30, THAAD, NASAMS, SkySabre,",
        "Skyranger, Germany/Italy A-J, and existing air weapons stay frozen.",
        "",
        "SPECTER design values. Not claimed real-world range or payload.",
        "Britain: naval/cruise + mixed medium + expensive strategic.",
        "France: independent deterrent; earlier heavy, CHL standouts, cruder J.",
        "A is not red in either country. Color sequences differ from DE/IT.",
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
        GB_DOZER_KEY, GB_WF_KEY, GB_SC_KEY, FR_DOZER_KEY, FR_WF_KEY, FR_SC_KEY,
        gi.DE_DOZER_KEY, gi.DE_WF_KEY, gi.DE_SC_KEY, gi.DE_FAC_KEY,
        gi.IT_DOZER_KEY, gi.IT_WF_KEY, gi.IT_SC_KEY, gi.IT_FAC_KEY,
        gi.DE_WEP_KEY, gi.IT_WEP_KEY,
        sk.R11_KEY, sa.SA_FAC_KEY, uae.UAE_FAC_KEY, vn.VN_FAC_KEY, vn.VN_WEP_KEY,
        jpn.NEW_FAC_KEY, jpn.NEW_WEP_KEY, sk.NEW_FAC_KEY, sk.NEW_WEP_KEY,
    ]
    for key in frozen_data:
        if key in src_data and data.get(key) != src_data.get(key):
            fails.append(f"frozen DATA mutated {key}")
    frozen_art = [
        GB_FLAG, FR_FLAG, gi.DE_FLAG, gi.IT_FLAG,
        gi.DE_TRUCK and rf"Art\Textures\{gi.DE_TRUCK}",
        gi.IT_TRUCK and rf"Art\Textures\{gi.IT_TRUCK}",
    ]
    for key in frozen_art:
        if key and key in src_art and art.get(key) != src_art.get(key):
            fails.append(f"frozen ART mutated {key}")

    cs_text = data[CS_KEY].decode("latin1")
    src_cs = src_data[CS_KEY].decode("latin1")
    cb_text = data[CB_KEY].decode("latin1")
    wep_text = data[WEAPON_KEY].decode("latin1")
    src_wep = src_data[WEAPON_KEY].decode("latin1")

    for key in (GB_CS_KEY, FR_CS_KEY, GB_CB_KEY, FR_CB_KEY, GB_WEP_KEY, FR_WEP_KEY):
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
        "BritainWarfactoryCommandSet",
        "FranceWarfactoryCommandSet",
        "GermanyDozerCommandSet",
        "ItalyDozerCommandSet",
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
        if any(tag in fac for tag in ("CB_VIETNAM_", "CB_UAE_", "CB_JAPAN_", "CB_GERMANY_", "CB_ITALY_")):
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
    gb_avg = Image.open(io.BytesIO(art[rf"Art\Textures\{GB_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    fr_avg = Image.open(io.BytesIO(art[rf"Art\Textures\{FR_TRUCK}"])).convert("RGB").resize(
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
    if gb_avg == fr_avg:
        fails.append(f"trucks identical {gb_avg}")
    if gb_avg in (de_avg, it_avg, irq_avg) or fr_avg in (de_avg, it_avg, irq_avg):
        fails.append(f"truck still donor {gb_avg} {fr_avg}")
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
        raise SystemExit("DATA baseline is not SPECTER_GERMANY_ITALY_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_SRC or SRC_ART.stat().st_size != SIZE_ART_SRC:
        raise SystemExit("ART baseline is not SPECTER_GERMANY_ITALY_MISSILES_AJ")

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
    zip_path = ROOT / "patch/Release/SPECTER_BRITAIN_FRANCE_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #647 s-germany-italy-missiles-aj + #646 + #645 + #644",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "BRITAIN_FACTORY_NEW=YES",
        "FRANCE_FACTORY_NEW=YES",
        "UK_FR_FLAGS_FROZEN=YES",
        "DE_IT_AJ_KEPT=YES",
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
            "ZIP_FILE=SPECTER_BRITAIN_FRANCE_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #647",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-britain-france-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-britain-france-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-britain-france-missiles-aj/SPECTER_BRITAIN_FRANCE_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-britain-france-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-britain-france-missiles-aj",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Britain and France complete missile rosters A-J.\n"
        "New country factories replace isolated Iraq factory construct on each Dozer slot 14.\n"
        "Existing War Factories, flags, Lgm30, THAAD, Germany/Italy A-J, and air Storm Shadow/SCALP stay frozen.\n"
        "Accepted tooltip corrections and all prior A-J rosters unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Britain + France missiles A-J\n\n"
        "- New Britain_MissileFactory and France_MissileFactory. Rally/Sell retained.\n"
        "- Replaces isolated Iraq factory construct on Britain and France Dozer slot 14.\n"
        "- Britain: naval/cruise SPECTER mix (Spear … Trafalgar).\n"
        "- France: independent deterrent mix (MdCN … Gaulle).\n"
        "- Existing UK/FR flags, War Factories, Lgm30, THAAD, Germany/Italy A-J, and air weapons preserved.\n"
        "- Tooltips include Acc/100 and Radar Stealth/100 with caveats.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_BritainMissiles.ini and CommandSet_FranceMissiles.ini last-win dozer + factory sets.\n"
        "Weapon\\Weapon_Britain_Missiles.ini and Weapon_France_Missiles.ini last-win factory pairs.\n"
        "Britain_Weapon_StormShadow and France_Weapon_SCALP_RafaleB air weapons are unchanged.\n"
        "UK_Flag.tga and FR_Flag.tga are frozen. New dorsal stamps are generated, not those files.\n"
        "Germany/Italy #647, Vietnam/SK #646, UAE/Japan #645, Saudi #644, NK, India, Pakistan, Iraq, and 9P117 stay frozen.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:70]))


if __name__ == "__main__":
    main()
