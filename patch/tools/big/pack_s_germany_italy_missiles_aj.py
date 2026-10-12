#!/usr/bin/env python3
"""Germany + Italy missile rosters A-J on the Vietnam/SK tooltip baseline.

Baseline: packed SPECTER_VIETNAM_SK_ACC_DESC (PR #646 on #645 / #644).

Packed last-wins audit: Germany and Italy are playable NATO sides
(FactionGermany / FactionItaly, Side=Germany / Italy). Builder is the Dozer
only (GermanyVehicleDozer / ItalyVehicleDozer). Last-wins GermanyDozerCommandSet
and ItalyDozerCommandSet live in CommandSet.ini. Slot 14 constructs isolated
Sell-only Iraq_AlFahdMissileFactoryBuilding. No dedicated missile factory.
Existing DE_Flag.tga / IT_Flag.tga, War Factories, Lgm30 slot 12, THAAD slot 15,
and air-launched Germany_Weapon_Taurus / Italy_Weapon_StormShadow stay frozen.

Germany: precision/tech SPECTER mix. Italy: independent tactical/medium/limited
heavy mix. Neither is a rename of the other. Names are public-program / place
inspiration; km/kg/Acc/CHL are SPECTER design values, not claimed real specs.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Satellites: CommandSet_GermanyMissiles.ini, CommandSet_ItalyMissiles.ini,
CommandButton_GermanyMissiles.ini, CommandButton_ItalyMissiles.ini,
Weapon\\Weapon_Germany_Missiles.ini, Weapon\\Weapon_Italy_Missiles.ini.
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

SRC_DATA = ROOT / "patch/Release/SPECTER_VIETNAM_SK_ACC_DESC/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_VIETNAM_SK_ACC_DESC/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_GERMANY_ITALY_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "cd5a6dfe0ded29f8c76819f5c4de7286025eb45b84530b2161745a85e79b4e59"
SIZE_DATA_SRC = 368542635
SHA_ART_SRC = "3c3872d21e09ad3f71960c11f88f0187ed21a9ff1942664e74846070bd2485bb"
SIZE_ART_SRC = 1830385382

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

DE_CB_KEY = r"Data\INI\CommandButton_GermanyMissiles.ini"
DE_CS_KEY = r"Data\INI\CommandSet_GermanyMissiles.ini"
DE_WEP_KEY = r"Data\INI\Weapon\Weapon_Germany_Missiles.ini"
DE_FAC_KEY = (
    r"Data\INI\Object\Specter\German Armed Forces"
    r"\Buildings\Germany_MissileFactory.ini"
)
DE_DOZER_KEY = r"Data\INI\Object\Specter\German Armed Forces\Wheleed\Dozer.ini"
DE_WF_KEY = r"Data\INI\Object\Specter\German Armed Forces\Buildings\Warfactory.ini"
DE_SC_KEY = r"Data\INI\Object\Specter\German Armed Forces\Buildings\SupplyCenter.ini"
DE_FLAG = r"Art\Textures\DE_Flag.tga"

IT_CB_KEY = r"Data\INI\CommandButton_ItalyMissiles.ini"
IT_CS_KEY = r"Data\INI\CommandSet_ItalyMissiles.ini"
IT_WEP_KEY = r"Data\INI\Weapon\Weapon_Italy_Missiles.ini"
IT_FAC_KEY = (
    r"Data\INI\Object\Specter\Italian Armed Forces"
    r"\Buildings\Italy_MissileFactory.ini"
)
IT_DOZER_KEY = r"Data\INI\Object\Specter\Italian Armed Forces\Wheleed\Dozer.ini"
IT_WF_KEY = r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\Warfactory.ini"
IT_SC_KEY = r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\SupplyCenter.ini"
IT_FLAG = r"Art\Textures\IT_Flag.tga"

DE_TRUCK = "Deu_TEL.tga"
DE_TRUCKD = "Deu_TELD.tga"
IT_TRUCK = "Ita_TEL.tga"
IT_TRUCKD = "Ita_TELD.tga"

NOSE_W = (236, 228, 210)
NOSE_R = (168, 32, 28)
NOSE_B = (20, 48, 140)
NOSE_G = (20, 72, 40)

# Germany: precision/tech. A is feldgrau, not red. Acc != 28.
GERMANY_MISSILES = [
    {"slot": "A", "object": "Germany_KEPD", "name": "KEPD-350",
     "model": "Deu_KEPD", "modeld": "Deu_KEPDD", "proj_model": "Deu_KEPDM",
     "hier": b"DEU_KEPDA", "hierd": b"DEU_KEPDAD", "proj_hier": b"DEU_MSL_A",
     "tex": "Deu_KEPDP.tga", "body": (116, 120, 128), "nose": NOSE_W,
     "expect": "gray", "km": 1000, "kg": 400, "acc": 88, "stealth": 30,
     "rebuild": 16, "price": 900,
     "role": "Precision tactical analogue (Taurus KEPD 350 class; SPECTER floor range)"},
    {"slot": "B", "object": "Germany_JFSM", "name": "JFS-M",
     "model": "Deu_JFSM", "modeld": "Deu_JFSMD", "proj_model": "Deu_JFSMM",
     "hier": b"DEU_JFSMB", "hierd": b"DEU_JFSMBD", "proj_hier": b"DEU_MSL_B",
     "tex": "Deu_JFSMP.tga", "body": (28, 68, 168), "nose": NOSE_W,
     "expect": "blue", "km": 1200, "kg": 500, "acc": 82, "stealth": 35,
     "rebuild": 22, "price": 1400,
     "role": "Joint Fire Support Missile analogue; high Acc, modest payload"},
    {"slot": "C", "object": "Germany_ELSA", "name": "ELSA",
     "model": "Deu_ELSA", "modeld": "Deu_ELSAD", "proj_model": "Deu_ELSAM",
     "hier": b"DEU_ELSAC", "hierd": b"DEU_ELSACD", "proj_hier": b"DEU_MSL_C",
     "tex": "Deu_ELSAP.tga", "body": (228, 224, 216), "nose": NOSE_B,
     "expect": "white", "km": 1400, "kg": 600, "acc": 76, "stealth": 42,
     "rebuild": 28, "price": 1900,
     "role": "European long-range strike analogue; balanced Acc/CHL"},
    {"slot": "D", "object": "Germany_Pfeil", "name": "Pfeil",
     "model": "Deu_Pfeil", "modeld": "Deu_PfeilD", "proj_model": "Deu_PfeilM",
     "hier": b"DEU_PFEID", "hierd": b"DEU_PFEIDD", "proj_hier": b"DEU_MSL_D",
     "tex": "Deu_PfeilP.tga", "body": (214, 178, 28), "nose": NOSE_W,
     "expect": "yellow", "km": 1600, "kg": 900, "acc": 60, "stealth": 25,
     "rebuild": 32, "price": 2200,
     "role": "Cheaper medium; lower CHL than ELSA, heavier warhead"},
    {"slot": "E", "object": "Germany_Adler", "name": "Adler",
     "model": "Deu_Adler", "modeld": "Deu_AdlerD", "proj_model": "Deu_AdlerM",
     "hier": b"DEU_ADLEE", "hierd": b"DEU_ADLEED", "proj_hier": b"DEU_MSL_E",
     "tex": "Deu_AdlerP.tga", "body": (220, 200, 155), "nose": NOSE_B,
     "expect": "cream", "km": 1800, "kg": 800, "acc": 84, "stealth": 48,
     "rebuild": 40, "price": 3600,
     "role": "Expensive precision medium; Acc standout, not the heaviest"},
    {"slot": "F", "object": "Germany_Donar", "name": "Donar",
     "model": "Deu_Donar", "modeld": "Deu_DonarD", "proj_model": "Deu_DonarM",
     "hier": b"DEU_DONAR", "hierd": b"DEU_DONARD", "proj_hier": b"DEU_MSL_F",
     "tex": "Deu_DonarP.tga", "body": (10, 72, 84), "nose": NOSE_W,
     "expect": "petrol", "km": 2100, "kg": 1400, "acc": 55, "stealth": 38,
     "rebuild": 48, "price": 4300,
     "role": "Heavier IRBM analogue; cruder than Adler"},
    {"slot": "G", "object": "Germany_Odin", "name": "Odin",
     "model": "Deu_Odin", "modeld": "Deu_OdinD", "proj_model": "Deu_OdinM",
     "hier": b"DEU_ODING", "hierd": b"DEU_ODINGD", "proj_hier": b"DEU_MSL_G",
     "tex": "Deu_OdinP.tga", "body": (22, 24, 26), "nose": NOSE_W,
     "expect": "black", "km": 2500, "kg": 1800, "acc": 72, "stealth": 52,
     "rebuild": 58, "price": 5600,
     "role": "Advanced medium-heavy; high Acc/CHL, costly"},
    {"slot": "H", "object": "Germany_Siegfried", "name": "Siegfried",
     "model": "Deu_Siegfr", "modeld": "Deu_SiegfrD", "proj_model": "Deu_SiegfrM",
     "hier": b"DEU_SIEGE", "hierd": b"DEU_SIEGED", "proj_hier": b"DEU_MSL_H",
     "tex": "Deu_SiegfrP.tga", "body": (210, 108, 22), "nose": NOSE_W,
     "expect": "orange", "km": 2800, "kg": 2500, "acc": 50, "stealth": 40,
     "rebuild": 68, "price": 6800,
     "role": "Heavy strike; payload over precision"},
    {"slot": "I", "object": "Germany_Polarstern", "name": "Polarstern",
     "model": "Deu_Polar", "modeld": "Deu_PolarD", "proj_model": "Deu_PolarM",
     "hier": b"DEU_POLAR", "hierd": b"DEU_POLARD", "proj_hier": b"DEU_MSL_I",
     "tex": "Deu_PolarP.tga", "body": (8, 162, 56), "nose": NOSE_W,
     "expect": "green", "km": 3400, "kg": 3200, "acc": 66, "stealth": 62,
     "rebuild": 82, "price": 9000,
     "role": "Expensive advanced heavy; CHL standout, not max payload"},
    {"slot": "J", "object": "Germany_Walkure", "name": "Walküre",
     "model": "Deu_Walkur", "modeld": "Deu_WalkurD", "proj_model": "Deu_WalkurM",
     "hier": b"DEU_WALKU", "hierd": b"DEU_WALKUD", "proj_hier": b"DEU_MSL_J",
     "tex": "Deu_WalkurP.tga", "body": (168, 32, 28), "nose": NOSE_W,
     "expect": "red", "km": 3800, "kg": 4800, "acc": 48, "stealth": 36,
     "rebuild": 94, "price": 10400,
     "role": "Flagship heavy; payload costs Acc/CHL versus Polarstern"},
]

# Italy: independent curve. A is navy, not red. Earlier heavy, lower top Acc.
ITALY_MISSILES = [
    {"slot": "A", "object": "Italy_Marte", "name": "Marte",
     "model": "Ita_Marte", "modeld": "Ita_MarteD", "proj_model": "Ita_MarteM",
     "hier": b"ITA_MRTEA", "hierd": b"ITA_MRTEAD", "proj_hier": b"ITA_MSL_A",
     "tex": "Ita_MarteP.tga", "body": (20, 56, 140), "nose": NOSE_W,
     "expect": "blue", "km": 1000, "kg": 400, "acc": 68, "stealth": 22,
     "rebuild": 15, "price": 800,
     "role": "Mobile tactical analogue (Marte family; SPECTER floor)"},
    {"slot": "B", "object": "Italy_Teseo", "name": "Teseo",
     "model": "Ita_Teseo", "modeld": "Ita_TeseoD", "proj_model": "Ita_TeseoM",
     "hier": b"ITA_TESOB", "hierd": b"ITA_TESOBD", "proj_hier": b"ITA_MSL_B",
     "tex": "Ita_TeseoP.tga", "body": (8, 140, 56), "nose": NOSE_W,
     "expect": "green", "km": 1100, "kg": 700, "acc": 50, "stealth": 26,
     "rebuild": 20, "price": 1300,
     "role": "Teseo/Otomat-class analogue; heavier early, modest Acc"},
    {"slot": "C", "object": "Italy_Freccia", "name": "Freccia",
     "model": "Ita_Frecc", "modeld": "Ita_FreccD", "proj_model": "Ita_FreccM",
     "hier": b"ITA_FRECC", "hierd": b"ITA_FRECCD", "proj_hier": b"ITA_MSL_C",
     "tex": "Ita_FreccP.tga", "body": (220, 200, 155), "nose": NOSE_R,
     "expect": "cream", "km": 1300, "kg": 450, "acc": 78, "stealth": 40,
     "rebuild": 24, "price": 1700,
     "role": "Light precision tactical; Acc over payload"},
    {"slot": "D", "object": "Italy_Saetta", "name": "Saetta",
     "model": "Ita_Saett", "modeld": "Ita_SaettD", "proj_model": "Ita_SaettM",
     "hier": b"ITA_SAETD", "hierd": b"ITA_SAETDD", "proj_hier": b"ITA_MSL_D",
     "tex": "Ita_SaettP.tga", "body": (214, 178, 28), "nose": NOSE_W,
     "expect": "yellow", "km": 1500, "kg": 800, "acc": 45, "stealth": 32,
     "rebuild": 30, "price": 2100,
     "role": "Versatile medium; cheaper than Freccia, lower Acc"},
    {"slot": "E", "object": "Italy_Folgore", "name": "Folgore",
     "model": "Ita_Folgo", "modeld": "Ita_FolgoD", "proj_model": "Ita_FolgoM",
     "hier": b"ITA_FOLGE", "hierd": b"ITA_FOLGED", "proj_hier": b"ITA_MSL_E",
     "tex": "Ita_FolgoP.tga", "body": (116, 120, 128), "nose": NOSE_W,
     "expect": "gray", "km": 1700, "kg": 600, "acc": 72, "stealth": 55,
     "rebuild": 36, "price": 2700,
     "role": "CHL standout medium; not a Germany Adler copy"},
    {"slot": "F", "object": "Italy_Vesuvio", "name": "Vesuvio",
     "model": "Ita_Vesuv", "modeld": "Ita_VesuvD", "proj_model": "Ita_VesuvM",
     "hier": b"ITA_VESUF", "hierd": b"ITA_VESUFD", "proj_hier": b"ITA_MSL_F",
     "tex": "Ita_VesuvP.tga", "body": (210, 108, 22), "nose": NOSE_W,
     "expect": "orange", "km": 2000, "kg": 1700, "acc": 38, "stealth": 28,
     "rebuild": 46, "price": 3900,
     "role": "Early heavy; payload before Germany Donar, cruder Acc"},
    {"slot": "G", "object": "Italy_Etna", "name": "Etna",
     "model": "Ita_Etna", "modeld": "Ita_EtnaD", "proj_model": "Ita_EtnaM",
     "hier": b"ITA_ETNAG", "hierd": b"ITA_ETNAGD", "proj_hier": b"ITA_MSL_G",
     "tex": "Ita_EtnaP.tga", "body": (22, 24, 26), "nose": NOSE_W,
     "expect": "black", "km": 2300, "kg": 1500, "acc": 58, "stealth": 36,
     "rebuild": 52, "price": 4700,
     "role": "Balanced heavy-medium; not Germany Odin"},
    {"slot": "H", "object": "Italy_Stromboli", "name": "Stromboli",
     "model": "Ita_Strom", "modeld": "Ita_StromD", "proj_model": "Ita_StromM",
     "hier": b"ITA_STRMH", "hierd": b"ITA_STRMHD", "proj_hier": b"ITA_MSL_H",
     "tex": "Ita_StromP.tga", "body": (10, 72, 84), "nose": NOSE_W,
     "expect": "petrol", "km": 2100, "kg": 1000, "acc": 64, "stealth": 60,
     "rebuild": 50, "price": 4600,
     "role": "Toughness over payload; CHL vs Vesuvio trade"},
    {"slot": "I", "object": "Italy_Aquila", "name": "Aquila",
     "model": "Ita_Aquil", "modeld": "Ita_AquilD", "proj_model": "Ita_AquilM",
     "hier": b"ITA_AQULI", "hierd": b"ITA_AQULID", "proj_hier": b"ITA_MSL_I",
     "tex": "Ita_AquilP.tga", "body": (228, 224, 216), "nose": NOSE_R,
     "expect": "white", "km": 3000, "kg": 2200, "acc": 42, "stealth": 34,
     "rebuild": 70, "price": 6800,
     "role": "Limited strategic; below Germany Polarstern Acc/CHL"},
    {"slot": "J", "object": "Italy_Roma", "name": "Roma",
     "model": "Ita_Roma", "modeld": "Ita_RomaD", "proj_model": "Ita_RomaM",
     "hier": b"ITA_ROMAJ", "hierd": b"ITA_ROMAJD", "proj_hier": b"ITA_MSL_J",
     "tex": "Ita_RomaP.tga", "body": (88, 96, 42), "nose": NOSE_R,
     "expect": "muddy", "km": 3600, "kg": 3800, "acc": 32, "stealth": 28,
     "rebuild": 88, "price": 9000,
     "role": "Flagship; shorter/lighter/cruder than Germany Walküre"},
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


DE_FELD = (70, 78, 72)
DE_GRAPH = (41, 45, 44)
DE_METAL = (133, 137, 130)
IT_OLIVE = (72, 82, 48)
IT_EARTH = (48, 52, 36)
IT_METAL = (120, 124, 110)


def make_germany_flag() -> Image.Image:
    w, h = 900, 600
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, w, h // 3], fill=(0, 0, 0, 255))
    draw.rectangle([0, h // 3, w, 2 * h // 3], fill=(221, 0, 0, 255))
    draw.rectangle([0, 2 * h // 3, w, h], fill=(255, 206, 0, 255))
    return im


def make_italy_flag() -> Image.Image:
    w, h = 900, 600
    im = Image.new("RGBA", (w, h), (0, 146, 70, 255))
    draw = ImageDraw.Draw(im)
    draw.rectangle([0, 0, w // 3, h], fill=(0, 146, 70, 255))
    draw.rectangle([w // 3, 0, 2 * w // 3, h], fill=(244, 245, 240, 255))
    draw.rectangle([2 * w // 3, 0, w, h], fill=(206, 43, 55, 255))
    return im


def has_germany_flag(counts: dict[str, int]) -> bool:
    return (
        counts.get("black", 0) >= 2
        and counts.get("red", 0) >= 3
        and (counts.get("yellow", 0) + counts.get("orange", 0) + counts.get("cream", 0)) >= 2
    )


def has_italy_flag(counts: dict[str, int]) -> bool:
    greenish = counts.get("green", 0) + counts.get("muddy", 0)
    return (
        greenish >= 3
        and counts.get("white", 0) >= 3
        and counts.get("red", 0) >= 3
    )


COUNTRY_DEFS = [
    _country(
        "DE", "Germany", "Germany", "Germany",
        "GermanyDozerCommandSet", "Germany_MissileFactory",
        "Germany_MissileFactoryCommandSet",
        "Command_ConstructGermany_MissileFactory",
        DE_FAC_KEY, DE_CB_KEY, DE_CS_KEY, DE_WEP_KEY,
        "; ===== Germany missiles A-J (Weapon.ini load path for Command_FireMainWeapon) =====",
        r"Data\INI\Object\Specter\German Armed Forces",
        DE_TRUCK, DE_TRUCKD, rf"Art\Textures\{DE_TRUCK}", rf"Art\Textures\{DE_TRUCKD}",
        make_germany_flag, has_germany_flag, GERMANY_MISSILES,
        {"dark": DE_GRAPH, "mid": DE_FELD, "metal": DE_METAL},
    ),
    _country(
        "IT", "Italy", "Italy", "Italy",
        "ItalyDozerCommandSet", "Italy_MissileFactory",
        "Italy_MissileFactoryCommandSet",
        "Command_ConstructItaly_MissileFactory",
        IT_FAC_KEY, IT_CB_KEY, IT_CS_KEY, IT_WEP_KEY,
        "; ===== Italy missiles A-J (Weapon.ini load path for Command_FireMainWeapon) =====",
        r"Data\INI\Object\Specter\Italian Armed Forces",
        IT_TRUCK, IT_TRUCKD, rf"Art\Textures\{IT_TRUCK}", rf"Art\Textures\{IT_TRUCKD}",
        make_italy_flag, has_italy_flag, ITALY_MISSILES,
        {"dark": IT_EARTH, "mid": IT_OLIVE, "metal": IT_METAL},
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

assert GERMANY_MISSILES[0]["expect"] != "red" and ITALY_MISSILES[0]["expect"] != "red"
assert [m["expect"] for m in GERMANY_MISSILES] != [m["expect"] for m in ITALY_MISSILES]
assert GERMANY_MISSILES[-1]["kg"] > ITALY_MISSILES[-1]["kg"]
assert GERMANY_MISSILES[0]["acc"] > ITALY_MISSILES[0]["acc"]
assert ITALY_MISSILES[5]["kg"] > GERMANY_MISSILES[5]["kg"]


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
        "GERMANY + ITALY A-J MISSILE ROSTERS",
        "",
        "Baseline packed last-wins: SPECTER_VIETNAM_SK_ACC_DESC (PR #646).",
        "Germany and Italy had no missile factory. Dozer slot 14 constructed",
        "isolated Iraq_AlFahdMissileFactoryBuilding. That slot now constructs",
        "the country factory. War Factory, Lgm30, THAAD, NASAMS, SkySabre,",
        "Skyranger, and existing air weapons stay frozen.",
        "",
        "SPECTER design values. Not claimed real-world range or payload.",
        "Germany: precision/tech mix. Italy: independent tactical/medium/limited heavy.",
        "A is not red in either country. Color sequences differ.",
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
        DE_DOZER_KEY, DE_WF_KEY, DE_SC_KEY, IT_DOZER_KEY, IT_WF_KEY, IT_SC_KEY,
        sk.R11_KEY, sa.SA_FAC_KEY, uae.UAE_FAC_KEY, vn.VN_FAC_KEY, vn.VN_WEP_KEY,
        jpn.NEW_FAC_KEY, jpn.NEW_WEP_KEY, sk.NEW_FAC_KEY, sk.NEW_WEP_KEY,
    ]
    for key in frozen_data:
        if key in src_data and data.get(key) != src_data.get(key):
            fails.append(f"frozen DATA mutated {key}")
    for key in (DE_FLAG, IT_FLAG, sa.TRUCK_KEY if hasattr(sa, "TRUCK_KEY") else ""):
        if key and key in src_art and art.get(key) != src_art.get(key):
            fails.append(f"frozen ART mutated {key}")

    cs_text = data[CS_KEY].decode("latin1")
    src_cs = src_data[CS_KEY].decode("latin1")
    cb_text = data[CB_KEY].decode("latin1")
    src_cb = src_data[CB_KEY].decode("latin1")
    wep_text = data[WEAPON_KEY].decode("latin1")
    src_wep = src_data[WEAPON_KEY].decode("latin1")

    for key in (DE_CS_KEY, IT_CS_KEY, DE_CB_KEY, IT_CB_KEY, DE_WEP_KEY, IT_WEP_KEY):
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
        "GermanyWarfactoryCommandSet",
        "ItalyWarfactoryCommandSet",
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
        if any(tag in fac for tag in ("CB_VIETNAM_", "CB_UAE_", "CB_JAPAN_", "CB_SOUTHKOREA_")):
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
    ):
        got = sk.csf_get(data[CSF_KEY], key)
        if not got or expect not in got:
            fails.append(f"frozen CSF lost {key}")
    if sk.last_block(wep_text, "Weapon", "Germany_Weapon_Taurus") != sk.last_block(
        src_wep, "Weapon", "Germany_Weapon_Taurus"
    ):
        fails.append("Germany_Weapon_Taurus mutated")
    if sk.last_block(wep_text, "Weapon", "Italy_Weapon_StormShadow") != sk.last_block(
        src_wep, "Weapon", "Italy_Weapon_StormShadow"
    ):
        fails.append("Italy_Weapon_StormShadow mutated")
    de_avg = Image.open(io.BytesIO(art[rf"Art\Textures\{DE_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    it_avg = Image.open(io.BytesIO(art[rf"Art\Textures\{IT_TRUCK}"])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    irq_avg = Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if de_avg == it_avg:
        fails.append(f"trucks identical {de_avg}")
    if de_avg == irq_avg or it_avg == irq_avg:
        fails.append("truck still Iraqi donor")
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
        raise SystemExit("DATA baseline is not SPECTER_VIETNAM_SK_ACC_DESC")
    if sk.sha256_path(SRC_ART) != SHA_ART_SRC or SRC_ART.stat().st_size != SIZE_ART_SRC:
        raise SystemExit("ART baseline is not SPECTER_VIETNAM_SK_ACC_DESC")

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
    zip_path = ROOT / "patch/Release/SPECTER_GERMANY_ITALY_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #646 s-vietnam-sk-aj-acc-desc + #645 + #644",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "GERMANY_FACTORY_NEW=YES",
        "ITALY_FACTORY_NEW=YES",
        "DE_IT_FLAGS_FROZEN=YES",
        "LGM30_THAAD_KEPT=YES",
        "TAURUS_STORMSHADOW_AIR_KEPT=YES",
        "VN_SK_ACC_DESC_KEPT=YES",
        "UAE_JAPAN_ACC_DESC_KEPT=YES",
        "SAUDI_ACC_DESC_KEPT=YES",
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
            "ZIP_FILE=SPECTER_GERMANY_ITALY_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #646",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-germany-italy-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-germany-italy-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-germany-italy-missiles-aj/SPECTER_GERMANY_ITALY_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-germany-italy-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-germany-italy-missiles-aj",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Germany and Italy complete missile rosters A-J.\n"
        "New country factories replace isolated Iraq factory construct on each Dozer slot 14.\n"
        "Existing War Factories, flags, Lgm30, THAAD, and air Taurus/Storm Shadow stay frozen.\n"
        "Accepted tooltip corrections and all prior A-J rosters unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Germany + Italy missiles A-J\n\n"
        "- New Germany_MissileFactory and Italy_MissileFactory. Rally/Sell retained.\n"
        "- Replaces isolated Iraq factory construct on Germany and Italy Dozer slot 14.\n"
        "- Germany: precision/tech SPECTER mix (KEPD-350 … Walküre).\n"
        "- Italy: independent tactical/medium/limited-heavy mix (Marte … Roma).\n"
        "- Existing DE/IT flags, War Factories, Lgm30, THAAD, and air weapons preserved.\n"
        "- Tooltips include Acc/100 and Radar Stealth/100 with caveats.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_GermanyMissiles.ini and CommandSet_ItalyMissiles.ini last-win dozer + factory sets.\n"
        "Weapon\\Weapon_Germany_Missiles.ini and Weapon_Italy_Missiles.ini last-win factory pairs.\n"
        "Germany_Weapon_Taurus and Italy_Weapon_StormShadow air weapons are unchanged.\n"
        "DE_Flag.tga and IT_Flag.tga are frozen. New dorsal stamps are generated, not those files.\n"
        "Vietnam/SK #646, UAE/Japan #645, Saudi #644, NK, India, Pakistan, Iraq, and 9P117 stay frozen.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:70]))


if __name__ == "__main__":
    main()
