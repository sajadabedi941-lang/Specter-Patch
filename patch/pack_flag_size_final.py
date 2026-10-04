#!/usr/bin/env python3
"""Final Flag_Hs size: 1.5x original (50% of the current 3x oversized flags).

Source ART is the unscaled IRAN_BUILDING_FLAGS pack. Hierarchical continuity
scale is applied at 1.5 so FLAG01/02/03 stay one cloth chain.

Source DATA is FLAG_SIZE_EVERYWHERE (already attaches 20 countries including
Iran/Iraq/NK). This pack adds hide + country Flag_Hs for USA, China, Russia,
Israel, and NATO so those five leftover factions match the same size.
"""
from __future__ import annotations

import argparse
import math
import re
import struct
import zipfile
from pathlib import Path

from pack_flag_hs_continuous import read_pivots, scale_flag_hs_continuous
from pack_flag_size_everywhere import flag_draw
from pack_iran_building_flags import replace_w3d_names, replace_w3d_texture, set_line01
from pack_pp_flag_size_3x import (
    build_big_ordered,
    find_index,
    last_objects,
    mesh_bounds,
    object_spans,
    read_big,
    read_line01_pivot,
    sha256_file,
)

SRC_DATA = Path("/workspace/patch/Release/FLAG_SIZE_EVERYWHERE/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/IRAN_BUILDING_FLAGS/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "c802b3bcecbf735af13ec1e0a25e2505f6538317991b8b2624b3d9a7755f8dc4"
EXPECTED_ART_SHA = "ec4f5bdcc8f9e9171a8d9fb0d9523cffa41089eded03b330f0f1738aaf555760"
RELEASE = Path("/workspace/patch/Release/FLAG_SIZE_FINAL")
PAYLOAD = RELEASE / "payload"

SCALE = 1.5
HALF_POLE = 17.492
TARGET_FLAG03 = 5.859 * SCALE
TARGET_POLE = 34.984 * SCALE

P_IRQ_DONOR = r"Art\W3D\Irq__IqFlag_Hs.W3D"
P_NKR_DONOR = r"Art\W3D\NKr__NKFlag_Hs.W3D"
IRQ_NAME = b"IRQ__IQFLAG_HS"
NKR_NAME = b"NKR__NKFLAG_HS"
DONOR_TEX = b"IraqiFlag.dds"

SCALE_PREFIXES = (
    "jp__", "sk__", "vn__", "in__", "pk__", "ly__", "sy__", "ae__", "sa__",
    "za__", "tr__", "it__", "se__", "uk__", "fr__", "de__", "ua__", "ir__",
)
SKIP_FLAG_HS = ("irq__", "nkr__")

DRAW_RE = re.compile(r"(?i)^\s*Draw\s*=")
ANIM_LOOP_RE = re.compile(r"(?i)^\s*AnimationMode\s*=\s*LOOP\s*$")
HIDE_RE = re.compile(r"(?i)^\s*HideSubObject\s*=")
END_RE = re.compile(r"(?i)^\s*End\s*$")

US_HIDE = "      HideSubObject = F1 F2 F3 FPOLE HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06"
US_SC_HIDE = "      HideSubObject = F1 F2 F3 HOUSECOLOR01 HOUSECOLOR02 HOUSECOLOR03 LINE01"
CHI_HQ_HIDE = "      HideSubObject = FLAG01 FLAG02 FLAG03 HOUSECOLOR01 HOUSECOLOR02 HOUSECOLOR03 LINE01"
CHI_FPOLE_HIDE = US_HIDE
IRQ_CLOTH_HIDE = "      HideSubObject = FLAG01 FLAG02 FLAG03 LINE01"
IRQ_PP_HIDE = "      HideSubObject = FLAG01 FLAG02 FLAG03 BOX08 BOX09 LINE01"

US_LINE01 = {
    "CU": (61.513, -64.028, 0.767 + HALF_POLE),
    "CP": (-31.496, 4.983, -0.516 + HALF_POLE),
    "WF": (46.895, 13.418, 3.622 + HALF_POLE),
    "PP": (44.359, 14.828, 0.385 + HALF_POLE),
    "SC": (33.267, -28.765, 4.450 + HALF_POLE),
}
CN_LINE01 = {
    "CU": (65.191, -21.273, 4.776 + HALF_POLE),
    "CP": (56.497, 35.241, -0.440 + HALF_POLE),
    "WF": (54.770, 25.098, -0.440 + HALF_POLE),
    "PP": (43.709, 19.024, 0.289 + HALF_POLE),
    "SC": (55.025, -20.974, 4.776 + HALF_POLE),
}
RU_LINE01 = {
    "CU": (24.852, -14.408, -0.363 + HALF_POLE),
    "CP": (64.994, -6.164, -0.106 + HALF_POLE),
    "WF": (102.153, 5.996, 0.594 + HALF_POLE),
    "PP": (47.371, -5.839, 0.155 + HALF_POLE),
    "SC": (26.581, -8.290, 4.776 + HALF_POLE),
}
IL_LINE01 = {
    "CU": US_LINE01["CU"],
    "CP": (-30.193, 34.524, 16.101 + HALF_POLE),
    "WF": (53.595, 36.922, 5.945 + HALF_POLE),
    "PP": (-14.342, -32.269, 36.448 + HALF_POLE),
    "SC": (56.662, 29.918, 8.617 + HALF_POLE),
}

# IQ/NK clones keep donor LINE01 (already attached in FLAG_SIZE_EVERYWHERE DATA).
IQ_NK_FLAGS = [
    ("IQ__IQFlag_HsCU", IRQ_NAME, P_IRQ_DONOR, b"IraqiFlag.dds", None),
    ("IQ__IQFlag_HsWF", IRQ_NAME, P_IRQ_DONOR, b"IraqiFlag.dds", None),
    ("IQ__IQFlag_HsCP", IRQ_NAME, P_IRQ_DONOR, b"IraqiFlag.dds", None),
    ("IQ__IQFlag_HsPP", IRQ_NAME, P_IRQ_DONOR, b"IraqiFlag.dds", None),
    ("IQ__IQFlag_HsSC", IRQ_NAME, P_IRQ_DONOR, b"IraqiFlag.dds", None),
    ("NK__NKFlag_HsCU", NKR_NAME, P_NKR_DONOR, b"DPRK_Flag.dds", None),
    ("NK__NKFlag_HsWF", NKR_NAME, P_NKR_DONOR, b"DPRK_Flag.dds", None),
    ("NK__NKFlag_HsCP", NKR_NAME, P_NKR_DONOR, b"DPRK_Flag.dds", None),
    ("NK__NKFlag_HsPP", NKR_NAME, P_NKR_DONOR, b"DPRK_Flag.dds", None),
    ("NK__NKFlag_HsSC", NKR_NAME, P_NKR_DONOR, b"DPRK_Flag.dds", None),
]

NEW_FACTION_FLAGS = [
    ("US__USFlag_HsCU", b"US_Flag.tga", US_LINE01["CU"]),
    ("US__USFlag_HsWF", b"US_Flag.tga", US_LINE01["WF"]),
    ("US__USFlag_HsCP", b"US_Flag.tga", US_LINE01["CP"]),
    ("US__USFlag_HsPP", b"US_Flag.tga", US_LINE01["PP"]),
    ("US__USFlag_HsSC", b"US_Flag.tga", US_LINE01["SC"]),
    ("CN__CNFlag_HsCU", b"CN_Flag.tga", CN_LINE01["CU"]),
    ("CN__CNFlag_HsWF", b"CN_Flag.tga", CN_LINE01["WF"]),
    ("CN__CNFlag_HsCP", b"CN_Flag.tga", CN_LINE01["CP"]),
    ("CN__CNFlag_HsPP", b"CN_Flag.tga", CN_LINE01["PP"]),
    ("CN__CNFlag_HsSC", b"CN_Flag.tga", CN_LINE01["SC"]),
    ("RU__RUFlag_HsCU", b"RU_Flag.tga", RU_LINE01["CU"]),
    ("RU__RUFlag_HsWF", b"RU_Flag.tga", RU_LINE01["WF"]),
    ("RU__RUFlag_HsCP", b"RU_Flag.tga", RU_LINE01["CP"]),
    ("RU__RUFlag_HsPP", b"RU_Flag.tga", RU_LINE01["PP"]),
    ("RU__RUFlag_HsSC", b"RU_Flag.tga", RU_LINE01["SC"]),
    ("IL__ILFlag_HsCU", b"IL_Flag.tga", IL_LINE01["CU"]),
    ("IL__ILFlag_HsWF", b"IL_Flag.tga", IL_LINE01["WF"]),
    ("IL__ILFlag_HsCP", b"IL_Flag.tga", IL_LINE01["CP"]),
    ("IL__ILFlag_HsPP", b"IL_Flag.tga", IL_LINE01["PP"]),
    ("IL__ILFlag_HsSC", b"IL_Flag.tga", IL_LINE01["SC"]),
    ("NT__NTFlag_HsCU", b"NT_Flag.tga", US_LINE01["CU"]),
    ("NT__NTFlag_HsWF", b"NT_Flag.tga", US_LINE01["WF"]),
    ("NT__NTFlag_HsCP", b"NT_Flag.tga", US_LINE01["CP"]),
    ("NT__NTFlag_HsPP", b"NT_Flag.tga", US_LINE01["PP"]),
    ("NT__NTFlag_HsSC", b"NT_Flag.tga", US_LINE01["SC"]),
]

NEW_TARGETS = [
    (r"Data\INI\Object\Specter\United States Of America\Buildings\CommandCenter.ini", "AmericaCommandCenter", "US__USFlag_HsCU", US_HIDE),
    (r"Data\INI\Object\Specter\United States Of America\Buildings\Warfactory.ini", "AmericaWarFactory_T", "US__USFlag_HsWF", US_HIDE),
    (r"Data\INI\Object\Specter\United States Of America\Buildings\Warfactory_AI.ini", "AmericaWarFactory", "US__USFlag_HsWF", US_HIDE),
    (r"Data\INI\Object\Specter\United States Of America\Buildings\Camp.ini", "AmericaBarracks", "US__USFlag_HsCP", US_HIDE),
    (r"Data\INI\Object\Specter\United States Of America\Buildings\PowerPlant.ini", "AmericaPowerPlant", "US__USFlag_HsPP", US_HIDE),
    (r"Data\INI\Object\Specter\United States Of America\Buildings\SupplyCenter.ini", "AmericaSupplyCenter", "US__USFlag_HsSC", US_SC_HIDE),
    (r"Data\INI\Object\Specter\PLA\Buildings\CommandCenter.ini", "ChinaCommandCenter", "CN__CNFlag_HsCU", CHI_HQ_HIDE),
    (r"Data\INI\Object\Specter\PLA\Buildings\Warfactory.ini", "ChinaWarFactory", "CN__CNFlag_HsWF", CHI_FPOLE_HIDE),
    (r"Data\INI\Object\Specter\PLA\Buildings\Camp.ini", "ChinaBarracks", "CN__CNFlag_HsCP", CHI_FPOLE_HIDE),
    (r"Data\INI\Object\Specter\PLA\Buildings\PowerPlant.ini", "ChinaPowerPlant", "CN__CNFlag_HsPP", CHI_FPOLE_HIDE),
    (r"Data\INI\Object\Specter\PLA\Buildings\SupplyCenter.ini", "ChinaSupplyCenter", "CN__CNFlag_HsSC", CHI_HQ_HIDE),
    (r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\CommandCenter.ini", "RussiaCommandCenter", "RU__RUFlag_HsCU", US_HIDE),
    (r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\Warfactory.ini", "RussiaWarFactory", "RU__RUFlag_HsWF", US_HIDE),
    (r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\Warfactory_T.ini", "RussiaWarFactory_T", "RU__RUFlag_HsWF", US_HIDE),
    (r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\Camp.ini", "RussiaBarracks", "RU__RUFlag_HsCP", US_HIDE),
    (r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\PowerPlant.ini", "RussiaPowerPlant", "RU__RUFlag_HsPP", US_HIDE),
    (r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\SupplyCenter.ini", "RussiaSupplyCenter", "RU__RUFlag_HsSC", CHI_HQ_HIDE),
    (r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_CommandCenter.ini", "Israel_CommandCenter", "IL__ILFlag_HsCU", US_HIDE),
    (r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_WarFactory.ini", "Israel_WarFactory", "IL__ILFlag_HsWF", IRQ_CLOTH_HIDE),
    (r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_Barracks.ini", "Israel_Barracks", "IL__ILFlag_HsCP", IRQ_CLOTH_HIDE),
    (r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_PowerPlant.ini", "Israel_PowerPlant", "IL__ILFlag_HsPP", IRQ_PP_HIDE),
    (r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_SupplyCenter.ini", "Israel_SupplyCenter", "IL__ILFlag_HsSC", IRQ_CLOTH_HIDE),
    (r"Data\INI\Object\Specter\NATO\Buildings\CommandCenter.ini", "NatoCommandCenter", "NT__NTFlag_HsCU", US_HIDE),
    (r"Data\INI\Object\Specter\NATO\Buildings\Warfactory.ini", "NatoWarFactory", "NT__NTFlag_HsWF", US_HIDE),
    (r"Data\INI\Object\Specter\NATO\Buildings\Camp.ini", "NatoBootCamp", "NT__NTFlag_HsCP", US_HIDE),
    (r"Data\INI\Object\Specter\NATO\Buildings\PowerStation.ini", "NatoPowerStation", "NT__NTFlag_HsPP", US_HIDE),
    (r"Data\INI\Object\Specter\NATO\Buildings\SupplyCenter.ini", "NatoSupplyCenter", "NT__NTFlag_HsSC", US_SC_HIDE),
]

MATRIX = {
    "Iran": {
        "CommandCenter": ("IranCommandCenter", "IR__IRFlag_HsCU"),
        "WarFactory": ("IranWarFactory", "IR__IRFlag_HsWF"),
        "Camp": ("IranBarracks", "IR__IRFlag_HsCP"),
        "PowerPlant": ("IranPowerplant", "IR__IRFlag_HsPP"),
        "SupplyCenter": ("IranSupplyCenter", "IR__IRFlag_HsSC"),
    },
    "Iraq": {
        "CommandCenter": ("Iraq_CommandCenter", "IQ__IQFlag_HsCU"),
        "WarFactory": ("Iraq_WarFactory_T", "IQ__IQFlag_HsWF"),
        "Camp": ("Iraq_Barracks", "IQ__IQFlag_HsCP"),
        "PowerPlant": ("Iraq_PowerPlant", "IQ__IQFlag_HsPP"),
        "SupplyCenter": ("Iraq_SupplyCenter", "IQ__IQFlag_HsSC"),
    },
    "USA": {
        "CommandCenter": ("AmericaCommandCenter", "US__USFlag_HsCU"),
        "WarFactory": ("AmericaWarFactory_T", "US__USFlag_HsWF"),
        "Camp": ("AmericaBarracks", "US__USFlag_HsCP"),
        "PowerPlant": ("AmericaPowerPlant", "US__USFlag_HsPP"),
        "SupplyCenter": ("AmericaSupplyCenter", "US__USFlag_HsSC"),
    },
    "China": {
        "CommandCenter": ("ChinaCommandCenter", "CN__CNFlag_HsCU"),
        "WarFactory": ("ChinaWarFactory", "CN__CNFlag_HsWF"),
        "Camp": ("ChinaBarracks", "CN__CNFlag_HsCP"),
        "PowerPlant": ("ChinaPowerPlant", "CN__CNFlag_HsPP"),
        "SupplyCenter": ("ChinaSupplyCenter", "CN__CNFlag_HsSC"),
    },
    "Russia": {
        "CommandCenter": ("RussiaCommandCenter", "RU__RUFlag_HsCU"),
        "WarFactory": ("RussiaWarFactory", "RU__RUFlag_HsWF"),
        "Camp": ("RussiaBarracks", "RU__RUFlag_HsCP"),
        "PowerPlant": ("RussiaPowerPlant", "RU__RUFlag_HsPP"),
        "SupplyCenter": ("RussiaSupplyCenter", "RU__RUFlag_HsSC"),
    },
    "Israel": {
        "CommandCenter": ("Israel_CommandCenter", "IL__ILFlag_HsCU"),
        "WarFactory": ("Israel_WarFactory", "IL__ILFlag_HsWF"),
        "Camp": ("Israel_Barracks", "IL__ILFlag_HsCP"),
        "PowerPlant": ("Israel_PowerPlant", "IL__ILFlag_HsPP"),
        "SupplyCenter": ("Israel_SupplyCenter", "IL__ILFlag_HsSC"),
    },
    "NATO": {
        "CommandCenter": ("NatoCommandCenter", "NT__NTFlag_HsCU"),
        "WarFactory": ("NatoWarFactory", "NT__NTFlag_HsWF"),
        "Camp": ("NatoBootCamp", "NT__NTFlag_HsCP"),
        "PowerPlant": ("NatoPowerStation", "NT__NTFlag_HsPP"),
        "SupplyCenter": ("NatoSupplyCenter", "NT__NTFlag_HsSC"),
    },
    "Vietnam": {
        "CommandCenter": ("Vietnam_CommandCenter", "VN__VNFlag_HsCK"),
        "WarFactory": ("Vietnam_WarFactory", "VN__VNFlag_HsWF"),
        "Camp": ("Vietnam_Barracks", "VN__VNFlag_Hs"),
        "PowerPlant": ("Vietnam_PowerPlant", "VN__VNFlag_HsPP"),
        "SupplyCenter": ("Vietnam_SupplyCenter", "VN__VNFlag_HsSC"),
    },
    "SouthKorea": {
        "CommandCenter": ("SouthKorea_CommandCenter", "SK__SKFlag_HsCK"),
        "WarFactory": ("SouthKorea_WarFactory", "SK__SKFlag_HsWF"),
        "Camp": ("SouthKorea_Barracks", "SK__SKFlag_Hs"),
        "PowerPlant": ("SouthKorea_PowerPlant", "SK__SKFlag_HsPP"),
        "SupplyCenter": ("SouthKorea_SupplyCenter", "SK__SKFlag_HsSC"),
    },
    "Japan": {
        "CommandCenter": ("Japan_CommandCenter", "JP__JPFlag_HsCK"),
        "WarFactory": ("Japan_WarFactory", "JP__JPFlag_HsWF"),
        "Camp": ("Japan_Barracks", "JP__JPFlag_Hs"),
        "PowerPlant": ("Japan_PowerPlant", "JP__JPFlag_HsPP"),
        "SupplyCenter": ("Japan_SupplyCenter", "JP__JPFlag_HsSC"),
    },
    "NorthKorea": {
        "CommandCenter": ("NorthKorea_CommandCenter", "NK__NKFlag_HsCU"),
        "WarFactory": ("NorthKorea_WarFactory", "NK__NKFlag_HsWF"),
        "Camp": ("NorthKorea_Barracks", "NK__NKFlag_HsCP"),
        "PowerPlant": ("NorthKorea_PowerPlant", "NK__NKFlag_HsPP"),
        "SupplyCenter": ("NorthKorea_SupplyCenter", "NK__NKFlag_HsSC"),
    },
    "Turkey": {
        "CommandCenter": ("TurkeyCommandCenter", "TR__TRFlag_HsCU"),
        "WarFactory": ("TurkeyWarFactory", "TR__TRFlag_HsWF"),
        "Camp": ("TurkeyBootCamp", "TR__TRFlag_HsCP"),
        "PowerPlant": ("TurkeyPowerStation", "TR__TRFlag_HsPP"),
        "SupplyCenter": ("TurkeySupplyCenter", "TR__TRFlag_HsSC"),
    },
    "Italy": {
        "CommandCenter": ("ItalyCommandCenter", "IT__ITFlag_HsCU"),
        "WarFactory": ("ItalyWarFactory", "IT__ITFlag_HsWF"),
        "Camp": ("ItalyBootCamp", "IT__ITFlag_HsCP"),
        "PowerPlant": ("ItalyPowerStation", "IT__ITFlag_HsPP"),
        "SupplyCenter": ("ItalySupplyCenter", "IT__ITFlag_HsSC"),
    },
    "Sweden": {
        "CommandCenter": ("SwedenCommandCenter", "SE__SEFlag_HsCU"),
        "WarFactory": ("SwedenWarFactory", "SE__SEFlag_HsWF"),
        "Camp": ("SwedenBootCamp", "SE__SEFlag_HsCP"),
        "PowerPlant": ("SwedenPowerStation", "SE__SEFlag_HsPP"),
        "SupplyCenter": ("SwedenSupplyCenter", "SE__SEFlag_HsSC"),
    },
    "Britain": {
        "CommandCenter": ("BritainCommandCenter", "UK__UKFlag_HsCU"),
        "WarFactory": ("BritainWarFactory", "UK__UKFlag_HsWF"),
        "Camp": ("BritainBootCamp", "UK__UKFlag_HsCP"),
        "PowerPlant": ("BritainPowerStation", "UK__UKFlag_HsPP"),
        "SupplyCenter": ("BritainSupplyCenter", "UK__UKFlag_HsSC"),
    },
    "France": {
        "CommandCenter": ("FranceCommandCenter", "FR__FRFlag_HsCU"),
        "WarFactory": ("FranceWarFactory", "FR__FRFlag_HsWF"),
        "Camp": ("FranceBootCamp", "FR__FRFlag_HsCP"),
        "PowerPlant": ("FrancePowerStation", "FR__FRFlag_HsPP"),
        "SupplyCenter": ("FranceSupplyCenter", "FR__FRFlag_HsSC"),
    },
    "Germany": {
        "CommandCenter": ("GermanyCommandCenter", "DE__DEFlag_HsCU"),
        "WarFactory": ("GermanyWarFactory", "DE__DEFlag_HsWF"),
        "Camp": ("GermanyBootCamp", "DE__DEFlag_HsCP"),
        "PowerPlant": ("GermanyPowerStation", "DE__DEFlag_HsPP"),
        "SupplyCenter": ("GermanySupplyCenter", "DE__DEFlag_HsSC"),
    },
    "Ukraine": {
        "CommandCenter": ("UkraineCommandCenter", "UA__UAFlag_HsCU"),
        "WarFactory": ("UkraineWarFactory", "UA__UAFlag_HsWF"),
        "Camp": ("UkraineBootCamp", "UA__UAFlag_HsCP"),
        "PowerPlant": ("UkrainePowerStation", "UA__UAFlag_HsPP"),
        "SupplyCenter": ("UkraineSupplyCenter", "UA__UAFlag_HsSC"),
    },
    "SaudiArabia": {
        "CommandCenter": ("SaudiArabia_CommandCenter", "SA__SAFlag_HsCU"),
        "WarFactory": ("SaudiArabia_WarFactory_T", "SA__SAFlag_HsWF"),
        "Camp": ("SaudiArabia_Barracks", "SA__SAFlag_Hs"),
        "PowerPlant": ("SaudiArabia_PowerPlant", "SA__SAFlag_HsPP"),
        "SupplyCenter": ("SaudiArabia_SupplyCenter", "SA__SAFlag_HsSC"),
    },
    "UAE": {
        "CommandCenter": ("UAE_CommandCenter", "AE__AEFlag_HsCU"),
        "WarFactory": ("UAE_WarFactory_T", "AE__AEFlag_HsWF"),
        "Camp": ("UAE_Barracks", "AE__AEFlag_Hs"),
        "PowerPlant": ("UAE_PowerPlant", "AE__AEFlag_HsPP"),
        "SupplyCenter": ("UAE_SupplyCenter", "AE__AEFlag_HsSC"),
    },
    "Syria": {
        "CommandCenter": ("Syria_CommandCenter", "SY__SYFlag_HsCU"),
        "WarFactory": ("Syria_WarFactory_T", "SY__SYFlag_HsWF"),
        "Camp": ("Syria_Barracks", "SY__SYFlag_Hs"),
        "PowerPlant": ("Syria_PowerPlant", "SY__SYFlag_HsPP"),
        "SupplyCenter": ("Syria_SupplyCenter", "SY__SYFlag_HsSC"),
    },
    "India": {
        "CommandCenter": ("India_CommandCenter", "IN__INFlag_HsCU"),
        "WarFactory": ("India_WarFactory_T", "IN__INFlag_HsWF"),
        "Camp": ("India_Barracks", "IN__INFlag_Hs"),
        "PowerPlant": ("India_PowerPlant", "IN__INFlag_HsPP"),
        "SupplyCenter": ("India_SupplyCenter", "IN__INFlag_HsSC"),
    },
    "Pakistan": {
        "CommandCenter": ("Pakistan_CommandCenter", "PK__PKFlag_HsCU"),
        "WarFactory": ("Pakistan_WarFactory_T", "PK__PKFlag_HsWF"),
        "Camp": ("Pakistan_Barracks", "PK__PKFlag_Hs"),
        "PowerPlant": ("Pakistan_PowerPlant", "PK__PKFlag_HsPP"),
        "SupplyCenter": ("Pakistan_SupplyCenter", "PK__PKFlag_HsSC"),
    },
    "Libya": {
        "CommandCenter": ("Libya_CommandCenter", "LY__LYFlag_HsCU"),
        "WarFactory": ("Libya_WarFactory_T", "LY__LYFlag_HsWF"),
        "Camp": ("Libya_Barracks", "LY__LYFlag_Hs"),
        "PowerPlant": ("Libya_PowerPlant", "LY__LYFlag_HsPP"),
        "SupplyCenter": ("Libya_SupplyCenter", "LY__LYFlag_HsSC"),
    },
    "SouthAfrica": {
        "CommandCenter": ("SouthAfrica_CommandCenter", "ZA__ZAFlag_HsCU"),
        "WarFactory": ("SouthAfrica_WarFactory_T", "ZA__ZAFlag_HsWF"),
        "Camp": ("SouthAfrica_Barracks", "ZA__ZAFlag_Hs"),
        "PowerPlant": ("SouthAfrica_PowerPlant", "ZA__ZAFlag_HsPP"),
        "SupplyCenter": ("SouthAfrica_SupplyCenter", "ZA__ZAFlag_HsSC"),
    },
}

FLAG_TEX = {
    "IR__": b"IR_Flag.tga",
    "IQ__": b"IraqiFlag.dds",
    "US__": b"US_Flag.tga",
    "CN__": b"CN_Flag.tga",
    "RU__": b"RU_Flag.tga",
    "IL__": b"IL_Flag.tga",
    "NT__": b"NT_Flag.tga",
    "VN__": b"VN_Flag.tga",
    "SK__": b"SK_Flag.tga",
    "JP__": b"JP_Flag.tga",
    "NK__": b"DPRK_Flag.dds",
    "TR__": b"TR_Flag.tga",
    "IT__": b"IT_Flag.tga",
    "SE__": b"SE_Flag.tga",
    "UK__": b"UK_Flag.tga",
    "FR__": b"FR_Flag.tga",
    "DE__": b"DE_Flag.tga",
    "UA__": b"UA_Flag.tga",
    "SA__": b"SA_Flag.tga",
    "AE__": b"UAE_Flag.tga",
    "SY__": b"SY_Flag.tga",
    "IN__": b"IN_Flag.tga",
    "PK__": b"PK_Flag.tga",
    "LY__": b"LY_Flag.tga",
    "ZA__": b"ZA_Flag.tga",
}

FROZEN_FILES = [
    r"Data\INI\CommandSet_ZZZZ_OilCapture_SoldierCommand.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\CommandSet_ZZZZ_CommandCenterMatchStart.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\Weapon.ini",
]
FROZEN_ART = [
    r"Art\W3D\Irq__IqFlag_Hs.W3D",
    r"Art\W3D\NKr__NKFlag_Hs.W3D",
    r"Art\W3D\NKor_Powerplant.W3D",
    r"Art\W3D\Iraq_Powerplant.W3D",
    r"Art\W3D\Irq_Command.W3D",
    r"Art\W3D\irq_camp.W3D",
    r"Art\W3D\US_Command.W3D",
    r"Art\W3D\Chi_Hq.W3D",
    r"Art\W3D\RUS_Comms.W3D",
]
PRESERVE_OBJECTS = [
    "Japan_Barracks",
    "SouthKorea_Barracks",
    "Vietnam_Barracks",
    "IranCommandCenter",
    "IranBarracks",
    "IranWarFactory",
    "IranPowerplant",
    "IranSupplyCenter",
    "BritainBootCamp",
    "TurkeyBootCamp",
    "Iraq_CommandCenter",
    "Iraq_Barracks",
    "NorthKorea_Barracks",
]


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def should_scale(name: str) -> bool:
    ln = norm(name)
    if not ln.startswith("art\\w3d\\") or "flag_hs" not in ln:
        return False
    base = ln.split("\\")[-1]
    if any(base.startswith(p) for p in SKIP_FLAG_HS):
        return False
    return any(base.startswith(p) for p in SCALE_PREFIXES)


def raw_line(line: str) -> str:
    raw = line[:-1] if line.endswith("\n") else line
    if raw.endswith("\r"):
        raw = raw[:-1]
    return raw


def line_nl(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    return ""


def indent_of(raw: str) -> int:
    return len(raw) - len(raw.lstrip(" \t"))


def draw_spans(lines: list[str]):
    spans = []
    i = 0
    while i < len(lines):
        raw = raw_line(lines[i])
        if DRAW_RE.match(raw):
            indent = indent_of(raw)
            j = i + 1
            while j < len(lines):
                r = raw_line(lines[j])
                if END_RE.match(r) and indent_of(r) == indent:
                    spans.append((i, j))
                    i = j
                    break
                j += 1
            else:
                raise SystemExit("unterminated Draw")
        i += 1
    return spans


def apply_hide(body: str, hide_line: str) -> str:
    lines = body.splitlines(keepends=True)
    spans = draw_spans(lines)
    if not spans:
        raise SystemExit("no Draw to hide")
    skip = set()
    for s, e in spans:
        chunk = "".join(lines[s : e + 1])
        if "ModuleTag_Flag_Hs" in chunk:
            skip.add((s, e))
            continue
        m = re.search(r"(?im)^\s*Model\s*=\s*(\S+)", chunk)
        model = m.group(1) if m else ""
        if "Strb" in model or "Flag_Hs" in model or "UBArmDeal" in model:
            skip.add((s, e))
    tokens = hide_line.split("=", 1)[1].strip()
    out = []
    changed = 0
    span_i = 0
    span = spans[span_i] if spans else None
    replaced_this = False
    for i, line in enumerate(lines):
        if span and i > span[1]:
            span_i += 1
            span = spans[span_i] if span_i < len(spans) else None
            replaced_this = False
        raw = raw_line(line)
        active = span and span not in skip and span[0] <= i <= span[1]
        if active and HIDE_RE.match(raw):
            out.append(hide_line + line_nl(line))
            changed += 1
            replaced_this = True
            continue
        out.append(line)
        if active and ANIM_LOOP_RE.match(raw) and not replaced_this:
            out.append(hide_line + line_nl(line))
            changed += 1
            replaced_this = True
    if changed < 1:
        raise SystemExit("no HideSubObject applied")
    text = "".join(out)
    if tokens not in text:
        raise SystemExit("hide tokens missing")
    return text


def insert_flag(body: str, model: str) -> str:
    if "ModuleTag_Flag_Hs" in body and model in body:
        return body
    nl = "\r\n" if "\r\n" in body else "\n"
    m = re.search(r"(?im)^[ \t]*PlacementViewAngle\s*=", body)
    if not m:
        raise SystemExit(f"missing PlacementViewAngle for {model}")
    return body[: m.start()] + flag_draw(model, nl) + body[m.start() :]


def patch_object(body: str, model: str, hide_line: str) -> str:
    body = apply_hide(body, hide_line)
    body = insert_flag(body, model)
    if model not in body or "ModuleTag_Flag_Hs" not in body:
        raise SystemExit(f"Flag_Hs missing after patch: {model}")
    return body


def tga_header(w: int = 128, h: int = 64) -> bytes:
    return bytes([0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, w & 255, w >> 8, h & 255, h >> 8, 32, 8])


def pack_tga(pixels: list[tuple[int, int, int, int]]) -> bytes:
    raw = bytearray()
    for b, g, r, a in pixels:
        raw += bytes((b, g, r, a))
    blob = tga_header() + bytes(raw)
    if len(blob) != 32786:
        raise SystemExit(f"TGA size {len(blob)}")
    return blob


def star(px: float, py: float, cx: float, cy: float, r_out: float, r_in: float, n: int = 5, rot: float = -math.pi / 2) -> bool:
    dx, dy = px - cx, py - cy
    ang = math.atan2(dy, dx) - rot
    tau = 2 * math.pi / n
    sector = (ang % tau) / tau
    # interpolate outer/inner radius along each point
    if sector < 0.5:
        t = sector * 2
        rad = r_out * (1 - t) + r_in * t
    else:
        t = (sector - 0.5) * 2
        rad = r_in * (1 - t) + r_out * t
    # tighter fill using inscribed pentagram approximation
    a = (ang % tau)
    edge = min(a, tau - a)
    r = r_in + (r_out - r_in) * max(0.0, 1.0 - edge / (tau * 0.5))
    return dx * dx + dy * dy <= r * r


def point_in_star(x: float, y: float, cx: float, cy: float, r: float, rot: float = -math.pi / 2) -> bool:
    pts = []
    for i in range(5):
        a = rot + i * 2 * math.pi / 5
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    # two triangles of a simple 5-point: use even-odd on the pentagram polyline
    poly = []
    order = [0, 2, 4, 1, 3]
    for i in order:
        poly.append(pts[i])
    inside = False
    j = 4
    for i in range(5):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def make_us_flag() -> bytes:
    w, h = 128, 64
    red, white, blue = (0x00, 0x00, 0xBF, 255), (255, 255, 255, 255), (0x68, 0x22, 0x00, 255)
    pixels = []
    canton_w, canton_h = int(w * 0.40), int(h * 7 / 13)
    for y in range(h):  # y=0 bottom
        visual_y = h - 1 - y
        stripe = visual_y * 13 // h
        row = red if stripe % 2 == 0 else white
        for x in range(w):
            c = row
            if x < canton_w and visual_y < canton_h:
                c = blue
                gx = (x + 0.5) / canton_w
                gy = (visual_y + 0.5) / canton_h
                col = int(gx * 6)
                rowi = int(gy * 5)
                cx = (col + 0.5) / 6 * canton_w
                cy = (rowi + 0.5) / 5 * canton_h
                if (x - cx) ** 2 + (visual_y - cy) ** 2 <= 1.6:
                    c = white
            pixels.append(c)
    return pack_tga(pixels)


def make_cn_flag() -> bytes:
    w, h = 128, 64
    red, gold = (0x00, 0x00, 0xDE, 255), (0x00, 0xD7, 0xFF, 255)
    pixels = []
    big = (22.0, 20.0, 9.0)
    small = [(40, 8, 3.2), (46, 16, 3.2), (46, 26, 3.2), (40, 34, 3.2)]
    for y in range(h):
        visual_y = h - 1 - y
        for x in range(w):
            c = red
            if point_in_star(x, visual_y, *big):
                c = gold
            for sx, sy, sr in small:
                if point_in_star(x, visual_y, sx, sy, sr):
                    c = gold
            pixels.append(c)
    return pack_tga(pixels)


def make_ru_flag() -> bytes:
    w, h = 128, 64
    white, blue, red = (255, 255, 255, 255), (0x8B, 0x3A, 0x00, 255), (0x26, 0x26, 0xD5, 255)
    band = h // 3
    pixels = []
    for y in range(h):
        visual_y = h - 1 - y
        if visual_y < band:
            row = white
        elif visual_y < 2 * band:
            row = blue
        else:
            row = red
        pixels.extend([row] * w)
    return pack_tga(pixels)


def make_il_flag() -> bytes:
    w, h = 128, 64
    white, blue = (255, 255, 255, 255), (0xC8, 0x5A, 0x00, 255)
    pixels = []
    stripe = max(4, h // 10)
    gap = stripe + 2
    for y in range(h):
        visual_y = h - 1 - y
        for x in range(w):
            c = white
            if gap <= visual_y < gap + stripe or h - gap - stripe <= visual_y < h - gap:
                c = blue
            pixels.append(c)
    cx, cy, r = w / 2, h / 2, 10.0
    for y in range(h):
        visual_y = h - 1 - y
        for x in range(w):
            if _hexagram(x, visual_y, cx, cy, r):
                pixels[y * w + x] = blue
    return pack_tga(pixels)


def _hexagram(x: float, y: float, cx: float, cy: float, r: float) -> bool:
    def tri(up: bool) -> bool:
        sign = -1 if up else 1
        relx, rely = x - cx, (y - cy) * sign
        return rely >= -r * 0.5 and rely <= r and abs(relx) <= (r - rely) * (math.sqrt(3) / 3) * 2 * 0.75 + r * 0.15

    # ring: in outer star, not deep interior
    outer = point_in_star(x, y, cx, cy, r) or point_in_star(x, y, cx, cy, r, rot=math.pi / 2)
    # two overlapping triangles
    def in_tri(rot):
        pts = []
        for i in range(3):
            a = rot + i * 2 * math.pi / 3
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        inside = False
        j = 2
        for i in range(3):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi):
                inside = not inside
            j = i
        return inside

    a = in_tri(-math.pi / 2)
    b = in_tri(math.pi / 2)
    # outline-ish: in either triangle near edges
    if not (a or b):
        return False
    # keep a visible star by requiring near-edge of at least one triangle
    def edge_tri(rot, thick=1.6):
        pts = []
        for i in range(3):
            ang = rot + i * 2 * math.pi / 3
            pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
        dmin = 1e9
        for i in range(3):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % 3]
            vx, vy = x2 - x1, y2 - y1
            t = max(0.0, min(1.0, ((x - x1) * vx + (y - y1) * vy) / (vx * vx + vy * vy + 1e-9)))
            px, py = x1 + t * vx, y1 + t * vy
            dmin = min(dmin, math.hypot(x - px, y - py))
        return dmin <= thick

    return edge_tri(-math.pi / 2) or edge_tri(math.pi / 2)


def make_nt_flag() -> bytes:
    w, h = 128, 64
    navy, white = (0x6B, 0x30, 0x00, 255), (255, 255, 255, 255)
    pixels = []
    cx, cy = w / 2, h / 2
    for y in range(h):
        visual_y = h - 1 - y
        for x in range(w):
            c = navy
            dx, dy = x - cx, visual_y - cy
            ang = math.atan2(dy, dx)
            rad = math.hypot(dx, dy)
            # 4-point compass
            arm = min(abs(math.sin(2 * ang)), 1.0)
            if rad < 18 and arm < 0.22 + (18 - rad) * 0.01:
                c = white
            if 7.5 <= rad <= 9.2:
                c = white
            pixels.append(c)
    return pack_tga(pixels)


TGA_BUILDERS = {
    b"US_Flag.tga": make_us_flag,
    b"CN_Flag.tga": make_cn_flag,
    b"RU_Flag.tga": make_ru_flag,
    b"IL_Flag.tga": make_il_flag,
    b"NT_Flag.tga": make_nt_flag,
}


def clone_scaled(donor: bytes, old_name: bytes, model: str, tex: bytes, xyz=None) -> bytes:
    new_name = model.upper().encode("ascii")
    blob = replace_w3d_names(donor, old_name, new_name)
    if tex != DONOR_TEX and old_name == IRQ_NAME:
        blob = replace_w3d_texture(blob, DONOR_TEX, tex)
    if xyz is not None:
        blob = set_line01(blob, xyz)
    blob = scale_flag_hs_continuous(blob, SCALE)
    if tex not in blob:
        raise SystemExit(f"{model} lost {tex}")
    if old_name != new_name and old_name in blob:
        raise SystemExit(f"{model} leaked {old_name}")
    if xyz is not None:
        got = read_line01_pivot(blob)
        if max(abs(a - b) for a, b in zip(got, xyz)) > 0.05:
            raise SystemExit(f"{model} LINE01 {got} != {xyz}")
    return blob


def write_payload(repl: dict[str, bytes]) -> None:
    if PAYLOAD.exists():
        for p in PAYLOAD.rglob("*"):
            if p.is_file():
                p.unlink()
    for name, blob in repl.items():
        dest = PAYLOAD / name.replace("\\", "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)


def assert_size_and_chain(label: str, blob: bytes, orig: bytes) -> None:
    bd = mesh_bounds(blob)
    ob = mesh_bounds(orig)
    fh = bd["FLAG03"]["ymax"] - bd["FLAG03"]["ymin"]
    ph = bd["LINE01"]["ymax"] - bd["LINE01"]["ymin"]
    if abs(fh - TARGET_FLAG03) > 0.08:
        raise SystemExit(f"{label} FLAG03 height {fh:.3f} != {TARGET_FLAG03:.3f}")
    if abs(ph - TARGET_POLE) > 0.12:
        raise SystemExit(f"{label} LINE01 height {ph:.3f} != {TARGET_POLE:.3f}")
    if abs(bd["LINE01"]["ymin"] - ob["LINE01"]["ymin"]) > 0.05:
        raise SystemExit(f"{label} pole base moved")
    if read_line01_pivot(orig) != read_line01_pivot(blob) and label.startswith(("IQ__", "NK__")):
        raise SystemExit(f"{label} IQ/NK LINE01 changed")
    op, np_ = read_pivots(orig), read_pivots(blob)
    ybase = ob["LINE01"]["ymin"]
    line01_i = next(p["i"] for p in op if p["name"] == "LINE01")
    names = [p["name"] for p in np_]
    if names != [p["name"] for p in op]:
        raise SystemExit(f"{label} pivot names drifted")
    for a, c in zip(op, np_):
        if a["parent"] != c["parent"]:
            raise SystemExit(f"{label} hierarchy drifted")
        if a["name"] in ("ROOTTRANSFORM", "LINE01"):
            if max(abs(x - y) for x, y in zip(a["t"], c["t"])) > 0.001:
                raise SystemExit(f"{label} {a['name']} pivot moved")
            continue
        if not (a["name"].startswith("FLAG") or a["name"].startswith("HOUSECOLOR")):
            continue
        ox, oy, oz = a["t"]
        if a["parent"] == line01_i:
            ex, ey, ez = ox * SCALE, (oy - ybase) * SCALE + ybase, oz * SCALE
        else:
            ex, ey, ez = ox * SCALE, oy * SCALE, oz * SCALE
        if max(abs(c["t"][0] - ex), abs(c["t"][1] - ey), abs(c["t"][2] - ez)) > 0.05:
            raise SystemExit(f"{label} {a['name']} T {c['t']} != {(ex, ey, ez)}")


def validate(orig_art, orig_data, new_art, new_data) -> None:
    orig_last, _ = last_objects(orig_data)
    new_last, _ = last_objects(new_data)
    art_m = {norm(n): b for n, b in new_art}
    orig_art_m = {norm(n): b for n, b in orig_art}
    orig_d = {norm(n): b for n, b in orig_data}
    new_d = {norm(n): b for n, b in new_data}

    for obj in PRESERVE_OBJECTS:
        if obj in orig_last and new_last.get(obj) != orig_last[obj]:
            raise SystemExit(f"preserved object changed: {obj}")
    for packed in FROZEN_FILES:
        if orig_d[norm(packed)] != new_d[norm(packed)]:
            raise SystemExit(f"frozen DATA file changed: {packed}")
    for packed in FROZEN_ART:
        if orig_art_m[norm(packed)] != art_m[norm(packed)]:
            raise SystemExit(f"frozen ART changed: {packed}")

    missing = []
    if len(MATRIX) != 25:
        raise SystemExit(f"MATRIX countries {len(MATRIX)} != 25")
    for country, kinds in MATRIX.items():
        if set(kinds) != {"CommandCenter", "WarFactory", "Camp", "PowerPlant", "SupplyCenter"}:
            missing.append(f"{country} building set {sorted(kinds)}")
        for kind, (obj, flag) in kinds.items():
            if obj not in new_last:
                missing.append(f"{country} {kind} missing object {obj}")
                continue
            body = new_last[obj]
            if flag not in body:
                missing.append(f"{country} {kind} {obj} missing {flag}")
            if country in ("USA", "China", "Russia", "Israel", "NATO") and "ModuleTag_Flag_Hs" not in body:
                missing.append(f"{country} {kind} missing ModuleTag_Flag_Hs")
            if country == "NorthKorea" and ("IraqiFlag" in body or "IQ__IQFlag" in body):
                missing.append(f"{country} {kind} inherited Iraq flag")
            if country in ("Japan", "SouthKorea", "Vietnam") and (
                "NKor_Powerplant" in body or "NKr__NKFlag" in body or "DPRK_Flag" in body
            ):
                missing.append(f"{country} {kind} inherited NK flag")
            w3d = f"art\\w3d\\{flag.lower()}.w3d"
            if w3d not in art_m:
                missing.append(f"missing W3D {flag}")
                continue
            blob = art_m[w3d]
            bd = mesh_bounds(blob)
            fh = bd["FLAG03"]["ymax"] - bd["FLAG03"]["ymin"]
            if abs(fh - TARGET_FLAG03) > 0.08:
                missing.append(f"{flag} FLAG03 {fh:.3f} not 1.5x")
            prefix = flag[:4]
            tex = FLAG_TEX[prefix]
            if tex not in blob:
                missing.append(f"{flag} missing {tex}")
            if prefix != "IQ__" and b"IraqiFlag" in blob:
                missing.append(f"{flag} leaked IraqiFlag")
            if prefix != "NK__" and b"DPRK_Flag" in blob:
                missing.append(f"{flag} leaked DPRK")
    if missing:
        raise SystemExit("MATRIX FAIL\n  " + "\n  ".join(missing))

    for donor in (P_IRQ_DONOR, P_NKR_DONOR):
        bd = mesh_bounds(art_m[norm(donor)])
        fh = bd["FLAG03"]["ymax"] - bd["FLAG03"]["ymin"]
        if abs(fh - 5.859) > 0.08:
            raise SystemExit(f"shared donor {donor} was scaled ({fh})")

    for obj, flag in (
        ("Japan_PowerPlant", "JP__JPFlag_HsPP"),
        ("SouthKorea_PowerPlant", "SK__SKFlag_HsPP"),
        ("Vietnam_PowerPlant", "VN__VNFlag_HsPP"),
        ("IranCommandCenter", "IR__IRFlag_HsCU"),
        ("AmericaCommandCenter", "US__USFlag_HsCU"),
        ("ChinaCommandCenter", "CN__CNFlag_HsCU"),
        ("RussiaCommandCenter", "RU__RUFlag_HsCU"),
        ("Israel_CommandCenter", "IL__ILFlag_HsCU"),
        ("NatoCommandCenter", "NT__NTFlag_HsCU"),
    ):
        body = new_last[obj]
        if flag not in body:
            raise SystemExit(f"{obj} lost {flag}")

    print("STATIC VALIDATION: PASS")
    print(f"  matrix {len(MATRIX)} countries x 5 buildings")
    print(f"  FLAG03 target {TARGET_FLAG03:.3f} (50% of 3x 17.578)")
    print("  hierarchical continuity preserved; donors unscaled")
    print("  USA/China/Russia/Israel/NATO now use country Flag_Hs")


def write_docs(data_sha: str, art_sha: str) -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)
    (RELEASE / "AUDIT.txt").write_text(
        "FLAG_SIZE_FINAL\n"
        f"SOURCE_DATA_SHA = {EXPECTED_DATA_SHA}\n"
        f"SOURCE_ART_SHA = {EXPECTED_ART_SHA}\n"
        "SIZE = 1.5x original Flag_Hs = ~50% of current 3x oversized flags.\n"
        "Still larger than the original 1x baked/small flags.\n"
        "SCALE_METHOD = scale_flag_hs_continuous (LINE01 Y from ymin; "
        "FLAG/HOUSECOLOR XYZ*; LINE01 children Ty pole-stretched; deeper T*).\n"
        "NEW = USA China Russia Israel NATO hide baked cloth + country Flag_Hs.\n"
        "IRAN = included (existing IR__IRFlag_Hs* re-scaled 1.5x).\n"
        "SKIP_SHARED = Irq__IqFlag_Hs NKr__NKFlag_Hs building W3Ds\n"
        "INGAME_TESTED = NO\n",
        encoding="utf-8",
    )
    (RELEASE / "CHANGELOG.txt").write_text(
        "FLAG_SIZE_FINAL\n\n"
        "Reduces the current oversized 3x national flags to approximately 50%\n"
        "of that size (1.5x the original Flag_Hs). All 25 listed countries now\n"
        "use the same hierarchical Flag_Hs size on Command Center, War Factory,\n"
        "Camp/Barracks, Power Plant, and Supply Center.\n\n"
        "USA, China, Russia, Israel, and NATO no longer keep the old baked\n"
        "building-mesh flags. Iran is included.\n"
        "FLAG01/02/03 remain one continuous cloth chain.\n"
        "In-game test: NOT PERFORMED.\n",
        encoding="utf-8",
    )
    (RELEASE / "CHANGED_FILES.txt").write_text(
        "ART: re-scaled existing country Flag_Hs (90) to 1.5x\n"
        "ART: IQ/NK Flag_Hs clones at 1.5x\n"
        "ART: US/CN/RU/IL/NT Flag_Hs clones at 1.5x + US/CN/RU/IL/NT_Flag.tga\n"
        "ART skipped: Irq__IqFlag_Hs NKr__NKFlag_Hs building meshes\n"
        "DATA: USA/China/Russia/Israel/NATO five-building hide + Flag_Hs\n"
        "DATA unchanged: CommandSet/CommandButton/Weapon/oil/roster overlays\n",
        encoding="utf-8",
    )
    if data_sha and art_sha:
        (RELEASE / "SHA256.txt").write_text(
            f"_SPEC_DATA_ONE.big {data_sha}\n_SPEC_ART_ONE.big  {art_sha}\n",
            encoding="utf-8",
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", action="store_true")
    args = ap.parse_args()
    if sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    art_work = list(read_big(SRC_ART))
    data_work = list(read_big(SRC_DATA))
    orig_art = list(art_work)
    orig_data = list(data_work)
    repl: dict[str, bytes] = {}

    scaled = 0
    for i, (name, blob) in enumerate(art_work):
        if not should_scale(name):
            continue
        new_blob = scale_flag_hs_continuous(blob, SCALE)
        assert_size_and_chain(name, new_blob, blob)
        art_work[i] = (name, new_blob)
        repl[name] = new_blob
        scaled += 1
    print(f"ART re-scaled existing Flag_Hs: {scaled}")

    for model, old_name, donor_path, tex, xyz in IQ_NK_FLAGS:
        donor = orig_art[find_index(orig_art, donor_path)][1]
        blob = clone_scaled(donor, old_name, model, tex, xyz)
        assert_size_and_chain(model, blob, replace_w3d_names(donor, old_name, model.upper().encode("ascii")))
        packed = rf"Art\W3D\{model}.W3D"
        art_work.append((packed, blob))
        repl[packed] = blob
        scaled += 1
        print("ART NEW", packed)

    irq_donor = orig_art[find_index(orig_art, P_IRQ_DONOR)][1]
    for model, tex, xyz in NEW_FACTION_FLAGS:
        blob = clone_scaled(irq_donor, IRQ_NAME, model, tex, xyz)
        named = replace_w3d_names(irq_donor, IRQ_NAME, model.upper().encode("ascii"))
        named = replace_w3d_texture(named, DONOR_TEX, tex)
        named = set_line01(named, xyz)
        assert_size_and_chain(model, blob, named)
        packed = rf"Art\W3D\{model}.W3D"
        art_work.append((packed, blob))
        repl[packed] = blob
        scaled += 1
        print("ART NEW", packed, "LINE01", xyz)

    for tex, builder in TGA_BUILDERS.items():
        packed = rf"Art\Textures\{tex.decode('ascii')}"
        blob = builder()
        art_work.append((packed, blob))
        repl[packed] = blob
        print("ART TEX", packed, len(blob))

    by_file: dict[str, list] = {}
    for packed, obj, model, hide in NEW_TARGETS:
        by_file.setdefault(packed, []).append((obj, model, hide))
    for packed, jobs in by_file.items():
        idx = find_index(data_work, packed)
        text = data_work[idx][1].decode("latin1", errors="replace")
        names = [n for n, _, _ in object_spans(text)]
        rebuilt = []
        cursor = 0
        for obj, start, end in object_spans(text):
            rebuilt.append(text[cursor:start])
            body = text[start:end]
            job = next((j for j in jobs if j[0] == obj), None)
            if job:
                body = patch_object(body, job[1], job[2])
            rebuilt.append(body)
            cursor = end
        rebuilt.append(text[cursor:])
        new_text = "".join(rebuilt)
        if [n for n, _, _ in object_spans(new_text)] != names:
            raise SystemExit(f"object list drifted: {packed}")
        blob = new_text.encode("latin1", errors="replace")
        data_work[idx] = (data_work[idx][0], blob)
        repl[data_work[idx][0]] = blob
        print("DATA", packed, [j[0] for j in jobs])

    write_payload(repl)
    validate(orig_art, orig_data, art_work, data_work)
    write_docs("", "")

    if args.pack:
        data_out = RELEASE / "_SPEC_DATA_ONE.big"
        art_out = RELEASE / "_SPEC_ART_ONE.big"
        data_out.write_bytes(build_big_ordered(data_work))
        art_out.write_bytes(build_big_ordered(art_work))
        dsha = sha256_file(data_out)
        asha = sha256_file(art_out)
        print("PACKED", data_out, dsha, data_out.stat().st_size)
        print("PACKED", art_out, asha, art_out.stat().st_size)
        write_docs(dsha, asha)
        packed_d = {norm(n): b for n, b in read_big(data_out)}
        src_d = {norm(n): b for n, b in orig_data}
        extra_d = set(packed_d) - set(src_d)
        if extra_d:
            raise SystemExit(f"unexpected DATA extras {extra_d}")
        packed_a = {norm(n): b for n, b in read_big(art_out)}
        src_a = {norm(n): b for n, b in orig_art}
        extra_a = set(packed_a) - set(src_a)
        expect_a = {norm(rf"Art\W3D\{m}.W3D") for m, *_ in IQ_NK_FLAGS}
        expect_a |= {norm(rf"Art\W3D\{m}.W3D") for m, *_ in NEW_FACTION_FLAGS}
        expect_a |= {norm(rf"Art\Textures\{t.decode('ascii')}") for t in TGA_BUILDERS}
        if extra_a != expect_a:
            raise SystemExit(f"unexpected ART extras {extra_a ^ expect_a}")
        print(f"POST-PACK SCOPE: PASS ({scaled} Flag_Hs, {len(extra_a)} new ART, 0 new DATA files)")
        zpath = RELEASE / "FLAG_SIZE_FINAL.zip"
        with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_STORED) as zf:
            zf.write(data_out, "_SPEC_DATA_ONE.big")
            zf.write(art_out, "_SPEC_ART_ONE.big")
            zf.write(RELEASE / "SHA256.txt", "SHA256.txt")
            zf.write(RELEASE / "CHANGELOG.txt", "CHANGELOG.txt")
        print("ZIP", zpath, sha256_file(zpath), zpath.stat().st_size)
    else:
        print("Payload written; BIGs not packed (pass --pack after validation).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
