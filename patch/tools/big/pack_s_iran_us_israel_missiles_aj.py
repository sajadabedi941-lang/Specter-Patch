#!/usr/bin/env python3
"""Iran A-J plus America A-J plus Israel A-J on the PR #652 factory baseline.

Baseline: packed SPECTER_IRAN_US_ISRAEL_FACTORY_BTNS (PR #652 on #651).

Packed last-wins audit:
  Iran_MissileFactory / America_MissileFactory / Israel_MissileFactory exist as
  Rally/Sell shells. IranDozerCommandSet slot 10 constructs Iran factory.
  AmericaDozerCommandSet slot 14 constructs America factory.
  AirF_AmericaDozerCommandSet slot 14 constructs Israel factory.
  FactionIsrael StartingUnit0=Israel_VehicleDozer is ABSENT. Packed Israel dozer
  file last-wins Object AirF_AmericaVehicleDozer Side=Israel
  CommandSet=AirF_AmericaDozerCommandSet. FactionAmericaAirForceGeneral shares
  that object.

This pack populates the three existing factories with independent A-J rosters.
It does not recreate factories or change #652 construction slots.
Minimum Israel construction fix: last-win Object Israel_VehicleDozer +
IsraelDozerCommandSet (factory at 14); restore AirF_AmericaDozerCommandSet
slot 14 to Command_DisarmMinesAtPosition for America Air Force General.
Packed AirF_AmericaVehicleDozer file is frozen.

Iran remains Side=Iran. America remains Side=America. Israel remains Side=Israel.
Bavar-373 objects and Command_ConstructIranBavarSiteAI / Command_ConstructIran_Bavar
stay. CN/RU/TR/ES/SE/UA/GB/FR/DE/IT A-J, Iraq 9P117, air CJ10/CJ100/DF21C/SOM/
Storm Shadow/SCALP stay frozen. No RadarPriority. No rearm. No ZZZZ. Acc != 28.
"""
from __future__ import annotations

import gzip
import io
import re
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image

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
import pack_s_china_russia_missiles_aj as cr  # noqa: E402
import pack_s_iran_us_israel_factory_btns as fac  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_IRAN_US_ISRAEL_FACTORY_BTNS/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAN_US_ISRAEL_FACTORY_BTNS/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAN_US_ISRAEL_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "9a20ef1bd5ef08029dfd8e9bee59f411663e05a21092994f7cc4302dddaa495a"
SIZE_DATA_SRC = 370231382
SHA_ART_SRC = "cf83e8cfedff3b3cf3ef5ff890d2ee79dd551dc68d9c6ae3f6295b36935f6d35"
SIZE_ART_SRC = 2308008528

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

IR_CB_KEY = r"Data\INI\CommandButton_IranMissiles.ini"
IR_CS_KEY = r"Data\INI\CommandSet_IranMissiles.ini"
IR_WEP_KEY = r"Data\INI\Weapon\Weapon_Iran_Missiles.ini"
IR_FAC_KEY = r"Data\INI\Object\Specter\Iranian Army\Buildings\Iran_MissileFactory.ini"
IR_DOZER_KEY = r"Data\INI\Object\Specter\Iranian Army\Tracked\Dozer.ini"
IR_FAC_CS_KEY = r"Data\INI\CommandSet_IranMissileFactory.ini"
IR_FAC_CB_KEY = r"Data\INI\CommandButton_IranMissileFactory.ini"
IR_FLAG = r"Art\Textures\IR_Flag.tga"
IR_BAVAR = r"Data\INI\Object\Specter\Iranian Army\AirDefense\Bavar.ini"
IR_BAVAR_AI = r"Data\INI\Object\Specter\Iranian Army\SamSites\BavarAI.ini"

US_CB_KEY = r"Data\INI\CommandButton_AmericaMissiles.ini"
US_CS_KEY = r"Data\INI\CommandSet_AmericaMissiles.ini"
US_WEP_KEY = r"Data\INI\Weapon\Weapon_America_Missiles.ini"
US_FAC_KEY = (
    r"Data\INI\Object\Specter\United States Of America"
    r"\Buildings\America_MissileFactory.ini"
)
US_DOZER_KEY = r"Data\INI\Object\Specter\United States Of America\Wheeled\Dozer.ini"
US_FAC_CS_KEY = r"Data\INI\CommandSet_AmericaMissileFactory.ini"
US_FAC_CB_KEY = r"Data\INI\CommandButton_AmericaMissileFactory.ini"
US_FLAG = r"Art\Textures\US_Flag.tga"

IL_CB_KEY = r"Data\INI\CommandButton_IsraelMissiles.ini"
IL_CS_KEY = r"Data\INI\CommandSet_IsraelMissiles.ini"
IL_WEP_KEY = r"Data\INI\Weapon\Weapon_Israel_Missiles.ini"
IL_FAC_KEY = (
    r"Data\INI\Object\Specter\Israel Defense Forces"
    r"\Buildings\Israel_MissileFactory.ini"
)
IL_AIRF_DOZER_KEY = r"Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Dozer.ini"
IL_DOZER_NEW_KEY = (
    r"Data\INI\Object\Specter\Israel Defense Forces"
    r"\Wheeled\Israel_VehicleDozer.ini"
)
IL_FAC_CS_KEY = r"Data\INI\CommandSet_IsraelMissileFactory.ini"
IL_FAC_CB_KEY = r"Data\INI\CommandButton_IsraelMissileFactory.ini"
IL_FLAG = r"Art\Textures\IL_Flag.tga"
PLAYER_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
PLAYER_INI = r"Data\INI\PlayerTemplate.ini"

IR_TRUCK = "Irn_TEL.tga"
IR_TRUCKD = "Irn_TELD.tga"
US_TRUCK = "Usa_TEL.tga"
US_TRUCKD = "Usa_TELD.tga"
IL_TRUCK = "Isr_TEL.tga"
IL_TRUCKD = "Isr_TELD.tga"

NOSE_W = (236, 228, 210)
NOSE_R = (168, 32, 28)
NOSE_B = (20, 48, 140)
NOSE_G = (20, 72, 40)

# Iran: Persian naming family. A is petrol (not red). Avoids Fateh313 / Sejjil silo.
IRAN_MISSILES = [
    {"slot": "A", "object": "Iran_Hormuz", "name": "Hormuz",
     "model": "Irn_Hormuz", "modeld": "Irn_HormuzD", "proj_model": "Irn_HormuzM",
     "hier": b"IRN_HRMZA", "hierd": b"IRN_HRMZAD", "proj_hier": b"IRN_MSL_A",
     "tex": "Irn_HormuzP.tga", "body": (12, 80, 88), "nose": NOSE_W,
     "expect": "petrol", "km": 1000, "kg": 400, "acc": 64, "stealth": 22,
     "rebuild": 16, "price": 820,
     "role": "Anti-ship analogue (Hormuz class; SPECTER floor)"},
    {"slot": "B", "object": "Iran_Qader", "name": "Qader",
     "model": "Irn_Qader", "modeld": "Irn_QaderD", "proj_model": "Irn_QaderM",
     "hier": b"IRN_QADRB", "hierd": b"IRN_QADRBD", "proj_hier": b"IRN_MSL_B",
     "tex": "Irn_QaderP.tga", "body": (214, 178, 28), "nose": NOSE_W,
     "expect": "yellow", "km": 1220, "kg": 520, "acc": 70, "stealth": 36,
     "rebuild": 24, "price": 1580,
     "role": "Coastal cruise analogue; Acc/CHL over payload"},
    {"slot": "C", "object": "Iran_Qiam", "name": "Qiam",
     "model": "Irn_Qiam", "modeld": "Irn_QiamD", "proj_model": "Irn_QiamM",
     "hier": b"IRN_QIAMC", "hierd": b"IRN_QIAMCD", "proj_hier": b"IRN_MSL_C",
     "tex": "Irn_QiamP.tga", "body": (236, 220, 170), "nose": NOSE_R,
     "expect": "cream", "km": 1480, "kg": 880, "acc": 44, "stealth": 18,
     "rebuild": 29, "price": 2050,
     "role": "SRBM analogue; payload over Acc versus Qader"},
    {"slot": "D", "object": "Iran_Emad", "name": "Emad",
     "model": "Irn_Emad", "modeld": "Irn_EmadD", "proj_model": "Irn_EmadM",
     "hier": b"IRN_EMADX", "hierd": b"IRN_EMADXD", "proj_hier": b"IRN_MSL_D",
     "tex": "Irn_EmadP.tga", "body": (16, 120, 48), "nose": NOSE_W,
     "expect": "green", "km": 1660, "kg": 1400, "acc": 34, "stealth": 16,
     "rebuild": 34, "price": 2380,
     "role": "Cheaper medium; heavier/cruder than Qiam"},
    {"slot": "E", "object": "Iran_Khalij", "name": "Khalij",
     "model": "Irn_Khalij", "modeld": "Irn_KhalijD", "proj_model": "Irn_KhalijM",
     "hier": b"IRN_KHLJE", "hierd": b"IRN_KHLJED", "proj_hier": b"IRN_MSL_E",
     "tex": "Irn_KhalijP.tga", "body": (232, 234, 236), "nose": NOSE_B,
     "expect": "white", "km": 1840, "kg": 620, "acc": 84, "stealth": 50,
     "rebuild": 39, "price": 3320,
     "role": "Expensive precision analogue; Acc/CHL not payload"},
    {"slot": "F", "object": "Iran_Dezful", "name": "Dezful",
     "model": "Irn_Dezful", "modeld": "Irn_DezfulD", "proj_model": "Irn_DezfulM",
     "hier": b"IRN_DZFLF", "hierd": b"IRN_DZFLFD", "proj_hier": b"IRN_MSL_F",
     "tex": "Irn_DezfulP.tga", "body": (200, 96, 28), "nose": NOSE_W,
     "expect": "orange", "km": 2080, "kg": 1800, "acc": 36, "stealth": 26,
     "rebuild": 47, "price": 4180,
     "role": "IRBM analogue; payload versus Khalij precision"},
    {"slot": "G", "object": "Iran_Khorram", "name": "Khorram",
     "model": "Irn_Khorrm", "modeld": "Irn_KhorrmD", "proj_model": "Irn_KhorrmM",
     "hier": b"IRN_KHRMG", "hierd": b"IRN_KHRMGD", "proj_hier": b"IRN_MSL_G",
     "tex": "Irn_KhorrmP.tga", "body": (20, 22, 28), "nose": NOSE_W,
     "expect": "black", "km": 2360, "kg": 1500, "acc": 58, "stealth": 40,
     "rebuild": 54, "price": 4980,
     "role": "Mobile heavy-medium; Acc/CHL cost money"},
    {"slot": "H", "object": "Iran_Kheibar", "name": "Kheibar",
     "model": "Irn_Kheibr", "modeld": "Irn_KheibrD", "proj_model": "Irn_KheibrM",
     "hier": b"IRN_KHBRH", "hierd": b"IRN_KHBRHD", "proj_hier": b"IRN_MSL_H",
     "tex": "Irn_KheibrP.tga", "body": (80, 92, 40), "nose": NOSE_W,
     "expect": "muddy", "km": 2720, "kg": 2500, "acc": 30, "stealth": 30,
     "rebuild": 66, "price": 6620,
     "role": "Heavy strike; payload over precision (Acc != 28)"},
    {"slot": "I", "object": "Iran_Ghadr", "name": "Ghadr",
     "model": "Irn_Ghadr", "modeld": "Irn_GhadrD", "proj_model": "Irn_GhadrM",
     "hier": b"IRN_GHDRI", "hierd": b"IRN_GHDRID", "proj_hier": b"IRN_MSL_I",
     "tex": "Irn_GhadrP.tga", "body": (20, 48, 128), "nose": NOSE_W,
     "expect": "blue", "km": 3260, "kg": 2800, "acc": 46, "stealth": 48,
     "rebuild": 74, "price": 7820,
     "role": "Expensive advanced heavy; CHL/Acc versus Kheibar payload"},
    {"slot": "J", "object": "Iran_Simorgh", "name": "Simorgh",
     "model": "Irn_Simrgh", "modeld": "Irn_SimrghD", "proj_model": "Irn_SimrghM",
     "hier": b"IRN_SMRGJ", "hierd": b"IRN_SMRGJD", "proj_hier": b"IRN_MSL_J",
     "tex": "Irn_SimrghP.tga", "body": (110, 114, 118), "nose": NOSE_W,
     "expect": "gray", "km": 3880, "kg": 4500, "acc": 22, "stealth": 20,
     "rebuild": 92, "price": 9550,
     "role": "Flagship long-range; payload costs Acc/CHL versus Ghadr"},
]

# America: distinct US naming family. A is white (not red). Avoids Tomahawk/Trident/LGM30.
AMERICA_MISSILES = [
    {"slot": "A", "object": "America_LRASM", "name": "LRASM",
     "model": "Usa_LRASM", "modeld": "Usa_LRASMD", "proj_model": "Usa_LRASMM",
     "hier": b"USA_LRSMA", "hierd": b"USA_LRSMAD", "proj_hier": b"USA_MSL_A",
     "tex": "Usa_LRASMP.tga", "body": (232, 234, 236), "nose": NOSE_B,
     "expect": "white", "km": 1000, "kg": 400, "acc": 76, "stealth": 28,
     "rebuild": 17, "price": 920,
     "role": "Anti-ship cruise analogue (LRASM class; SPECTER floor)"},
    {"slot": "B", "object": "America_JASSM", "name": "JASSM",
     "model": "Usa_JASSM", "modeld": "Usa_JASSMD", "proj_model": "Usa_JASSMM",
     "hier": b"USA_JASMB", "hierd": b"USA_JASMBD", "proj_hier": b"USA_MSL_B",
     "tex": "Usa_JASSMP.tga", "body": (110, 114, 118), "nose": NOSE_W,
     "expect": "gray", "km": 1260, "kg": 540, "acc": 82, "stealth": 44,
     "rebuild": 26, "price": 1780,
     "role": "Land-attack cruise analogue; Acc/CHL over payload"},
    {"slot": "C", "object": "America_ATACMS", "name": "ATACMS",
     "model": "Usa_ATACMS", "modeld": "Usa_ATACMSD", "proj_model": "Usa_ATACMSM",
     "hier": b"USA_ATCMC", "hierd": b"USA_ATCMCD", "proj_hier": b"USA_MSL_C",
     "tex": "Usa_ATACMSP.tga", "body": (24, 26, 28), "nose": NOSE_W,
     "expect": "black", "km": 1440, "kg": 720, "acc": 52, "stealth": 22,
     "rebuild": 28, "price": 1980,
     "role": "Tactical ballistic analogue; earlier payload than JASSM"},
    {"slot": "D", "object": "America_PrSM", "name": "PrSM",
     "model": "Usa_PrSM", "modeld": "Usa_PrSMD", "proj_model": "Usa_PrSMM",
     "hier": b"USA_PRSMD", "hierd": b"USA_PRSMDD", "proj_hier": b"USA_MSL_D",
     "tex": "Usa_PrSMP.tga", "body": (40, 80, 170), "nose": NOSE_W,
     "expect": "blue", "km": 1620, "kg": 900, "acc": 68, "stealth": 38,
     "rebuild": 36, "price": 2680,
     "role": "Precision successor analogue; Acc versus ATACMS payload"},
    {"slot": "E", "object": "America_ALCM", "name": "ALCM",
     "model": "Usa_ALCM", "modeld": "Usa_ALCMD", "proj_model": "Usa_ALCMM",
     "hier": b"USA_ALCME", "hierd": b"USA_ALCMED", "proj_hier": b"USA_MSL_E",
     "tex": "Usa_ALCMP.tga", "body": (220, 200, 155), "nose": NOSE_R,
     "expect": "cream", "km": 1820, "kg": 600, "acc": 88, "stealth": 54,
     "rebuild": 42, "price": 3580,
     "role": "Expensive precision cruise; Acc/CHL not payload"},
    {"slot": "F", "object": "America_PershingII", "name": "PershingII",
     "model": "Usa_Prsh2", "modeld": "Usa_Prsh2D", "proj_model": "Usa_Prsh2M",
     "hier": b"USA_PRSHF", "hierd": b"USA_PRSHFD", "proj_hier": b"USA_MSL_F",
     "tex": "Usa_Prsh2P.tga", "body": (214, 178, 28), "nose": NOSE_W,
     "expect": "yellow", "km": 2040, "kg": 1600, "acc": 40, "stealth": 24,
     "rebuild": 45, "price": 4020,
     "role": "Theater ballistic analogue; payload versus ALCM precision"},
    {"slot": "G", "object": "America_MX", "name": "MX",
     "model": "Usa_MX", "modeld": "Usa_MXD", "proj_model": "Usa_MXM",
     "hier": b"USA_MXICG", "hierd": b"USA_MXICGD", "proj_hier": b"USA_MSL_G",
     "tex": "Usa_MXP.tga", "body": (176, 72, 20), "nose": NOSE_W,
     "expect": "orange", "km": 2320, "kg": 1800, "acc": 54, "stealth": 42,
     "rebuild": 52, "price": 4920,
     "role": "Mobile heavy-medium; not Iran Khorram"},
    {"slot": "H", "object": "America_D5", "name": "D5",
     "model": "Usa_D5", "modeld": "Usa_D5D", "proj_model": "Usa_D5M",
     "hier": b"USA_D5TRH", "hierd": b"USA_D5TRHD", "proj_hier": b"USA_MSL_H",
     "tex": "Usa_D5P.tga", "body": (8, 140, 56), "nose": NOSE_W,
     "expect": "green", "km": 2680, "kg": 2200, "acc": 48, "stealth": 48,
     "rebuild": 62, "price": 6120,
     "role": "SLBM analogue; balanced Acc/CHL versus MX"},
    {"slot": "I", "object": "America_Sentinel", "name": "Sentinel",
     "model": "Usa_Sentnl", "modeld": "Usa_SentnlD", "proj_model": "Usa_SentnlM",
     "hier": b"USA_SENTI", "hierd": b"USA_SENTID", "proj_hier": b"USA_MSL_I",
     "tex": "Usa_SentnlP.tga", "body": (6, 92, 100), "nose": NOSE_W,
     "expect": "petrol", "km": 3220, "kg": 2600, "acc": 42, "stealth": 36,
     "rebuild": 70, "price": 6980,
     "role": "Limited strategic; below Iran Ghadr CHL"},
    {"slot": "J", "object": "America_PK", "name": "PK",
     "model": "Usa_PK", "modeld": "Usa_PKD", "proj_model": "Usa_PKM",
     "hier": b"USA_PCEKJ", "hierd": b"USA_PCEKJD", "proj_hier": b"USA_MSL_J",
     "tex": "Usa_PKP.tga", "body": (80, 92, 40), "nose": NOSE_W,
     "expect": "muddy", "km": 3960, "kg": 3800, "acc": 26, "stealth": 26,
     "rebuild": 90, "price": 9400,
     "role": "Flagship; longer/lighter than Iran Simorgh"},
]

# Israel: Hebrew/Israeli naming family. A is cream (not red). Avoids Arrow / JerichoNuclearWarhead.
ISRAEL_MISSILES = [
    {"slot": "A", "object": "Israel_Popeye", "name": "Popeye",
     "model": "Isr_Popeye", "modeld": "Isr_PopeyeD", "proj_model": "Isr_PopeyeM",
     "hier": b"ISR_POPYA", "hierd": b"ISR_POPYAD", "proj_hier": b"ISR_MSL_A",
     "tex": "Isr_PopeyeP.tga", "body": (236, 220, 170), "nose": NOSE_B,
     "expect": "cream", "km": 1000, "kg": 400, "acc": 70, "stealth": 26,
     "rebuild": 16, "price": 880,
     "role": "Air-to-ground analogue (Popeye class; SPECTER floor)"},
    {"slot": "B", "object": "Israel_Delilah", "name": "Delilah",
     "model": "Isr_Delilh", "modeld": "Isr_DelilhD", "proj_model": "Isr_DelilhM",
     "hier": b"ISR_DLLHB", "hierd": b"ISR_DLLHBD", "proj_hier": b"ISR_MSL_B",
     "tex": "Isr_DelilhP.tga", "body": (20, 48, 128), "nose": NOSE_W,
     "expect": "blue", "km": 1200, "kg": 480, "acc": 86, "stealth": 48,
     "rebuild": 25, "price": 1720,
     "role": "Loitering cruise analogue; Acc/CHL over payload"},
    {"slot": "C", "object": "Israel_LORA", "name": "LORA",
     "model": "Isr_LORA", "modeld": "Isr_LORAD", "proj_model": "Isr_LORAM",
     "hier": b"ISR_LORAC", "hierd": b"ISR_LORACD", "proj_hier": b"ISR_MSL_C",
     "tex": "Isr_LORAP.tga", "body": (244, 244, 248), "nose": NOSE_R,
     "expect": "white", "km": 1420, "kg": 800, "acc": 50, "stealth": 22,
     "rebuild": 28, "price": 1960,
     "role": "Tactical ballistic analogue; payload versus Delilah"},
    {"slot": "D", "object": "Israel_EXTRA", "name": "EXTRA",
     "model": "Isr_EXTRA", "modeld": "Isr_EXTRAD", "proj_model": "Isr_EXTRAM",
     "hier": b"ISR_EXTRD", "hierd": b"ISR_EXTRDD", "proj_hier": b"ISR_MSL_D",
     "tex": "Isr_EXTRAP.tga", "body": (110, 114, 118), "nose": NOSE_W,
     "expect": "gray", "km": 1600, "kg": 1100, "acc": 38, "stealth": 16,
     "rebuild": 32, "price": 2240,
     "role": "Cheaper medium; heavier/cruder than LORA"},
    {"slot": "E", "object": "Israel_Rampage", "name": "Rampage",
     "model": "Isr_Rampag", "modeld": "Isr_RampagD", "proj_model": "Isr_RampagM",
     "hier": b"ISR_RMPGE", "hierd": b"ISR_RMPGED", "proj_hier": b"ISR_MSL_E",
     "tex": "Isr_RampagP.tga", "body": (214, 178, 28), "nose": NOSE_W,
     "expect": "yellow", "km": 1780, "kg": 560, "acc": 90, "stealth": 56,
     "rebuild": 41, "price": 3500,
     "role": "Expensive precision analogue; Acc/CHL not payload"},
    {"slot": "F", "object": "Israel_Rocks", "name": "Rocks",
     "model": "Isr_Rocks", "modeld": "Isr_RocksD", "proj_model": "Isr_RocksM",
     "hier": b"ISR_ROCKF", "hierd": b"ISR_ROCKFD", "proj_hier": b"ISR_MSL_F",
     "tex": "Isr_RocksP.tga", "body": (16, 120, 48), "nose": NOSE_W,
     "expect": "green", "km": 1960, "kg": 1700, "acc": 32, "stealth": 22,
     "rebuild": 44, "price": 3780,
     "role": "Early heavy; payload versus Rampage precision"},
    {"slot": "G", "object": "Israel_Shavit", "name": "Shavit",
     "model": "Isr_Shavit", "modeld": "Isr_ShavitD", "proj_model": "Isr_ShavitM",
     "hier": b"ISR_SHVTG", "hierd": b"ISR_SHVTGD", "proj_hier": b"ISR_MSL_G",
     "tex": "Isr_ShavitP.tga", "body": (200, 96, 28), "nose": NOSE_W,
     "expect": "orange", "km": 2280, "kg": 1400, "acc": 60, "stealth": 52,
     "rebuild": 50, "price": 4800,
     "role": "Boost analogue; Acc/CHL versus Rocks payload"},
    {"slot": "H", "object": "Israel_Jericho2", "name": "Jericho2",
     "model": "Isr_Jeri2", "modeld": "Isr_Jeri2D", "proj_model": "Isr_Jeri2M",
     "hier": b"ISR_JER2H", "hierd": b"ISR_JER2HD", "proj_hier": b"ISR_MSL_H",
     "tex": "Isr_Jeri2P.tga", "body": (12, 80, 88), "nose": NOSE_W,
     "expect": "petrol", "km": 2560, "kg": 2000, "acc": 36, "stealth": 34,
     "rebuild": 58, "price": 5480,
     "role": "Theater heavy; not America D5"},
    {"slot": "I", "object": "Israel_Jericho3", "name": "Jericho3",
     "model": "Isr_Jeri3", "modeld": "Isr_Jeri3D", "proj_model": "Isr_Jeri3M",
     "hier": b"ISR_JER3I", "hierd": b"ISR_JER3ID", "proj_hier": b"ISR_MSL_I",
     "tex": "Isr_Jeri3P.tga", "body": (20, 22, 28), "nose": NOSE_W,
     "expect": "black", "km": 3180, "kg": 2300, "acc": 44, "stealth": 40,
     "rebuild": 71, "price": 7100,
     "role": "Limited strategic; below America Sentinel range"},
    {"slot": "J", "object": "Israel_Keren", "name": "Keren",
     "model": "Isr_Keren", "modeld": "Isr_KerenD", "proj_model": "Isr_KerenM",
     "hier": b"ISR_KERNJ", "hierd": b"ISR_KERNJD", "proj_hier": b"ISR_MSL_J",
     "tex": "Isr_KerenP.tga", "body": (80, 92, 40), "nose": NOSE_W,
     "expect": "muddy", "km": 3760, "kg": 3600, "acc": 24, "stealth": 24,
     "rebuild": 86, "price": 8900,
     "role": "Flagship; shorter/lighter than America PK"},
]


def _country(code, label, side, prefix, builder, fac_obj, fac_cs, fac_btn,
             fac_key, cb_key, cs_key, wep_key, wep_marker, path, truck, truckd,
             truck_key, truckd_key, flag_key, flag_check, missiles, bases,
             supply_keep, keep_cmds):
    return {
        "code": code, "label": label, "side": side, "prefix": prefix,
        "builder": builder, "fac_obj": fac_obj, "fac_cs": fac_cs,
        "fac_btn": fac_btn, "fac_key": fac_key, "cb_key": cb_key,
        "cs_key": cs_key, "wep_key": wep_key, "wep_marker": wep_marker,
        "path": path, "truck": truck, "truckd": truckd,
        "truck_key": truck_key, "truckd_key": truckd_key,
        "flag_key": flag_key, "flag_check": flag_check,
        "missiles": missiles, "bases": bases,
        "supply_keep": supply_keep,
        "keep_cmds": keep_cmds,
    }


IR_MID = (140, 112, 64)
IR_DARK = (68, 48, 28)
IR_METAL = (168, 148, 112)
US_MID = (44, 52, 34)
US_DARK = (24, 28, 18)
US_METAL = (120, 118, 96)
IL_MID = (168, 160, 138)
IL_DARK = (72, 68, 60)
IL_METAL = (184, 180, 168)


def has_iran_flag(counts: dict[str, int]) -> bool:
    return (
        counts.get("green", 0) + counts.get("petrol", 0) >= 2
        and counts.get("white", 0) + counts.get("cream", 0) >= 2
        and counts.get("red", 0) >= 2
    )


def has_usa_flag(counts: dict[str, int]) -> bool:
    return (
        counts.get("blue", 0) >= 2
        and counts.get("red", 0) >= 2
        and counts.get("white", 0) >= 2
    )


def has_israel_flag(counts: dict[str, int]) -> bool:
    return counts.get("white", 0) >= 2 and counts.get("blue", 0) >= 2


IRAN_KEEP = fac.COUNTRIES[0]["keep"]
AMERICA_KEEP = fac.COUNTRIES[1]["keep"]
ISRAEL_KEEP = fac.COUNTRIES[2]["keep"]

COUNTRY_DEFS = [
    _country(
        "IR", "Iran", "Iran", "Iran",
        "IranDozerCommandSet", "Iran_MissileFactory",
        "Iran_MissileFactoryCommandSet",
        "Command_ConstructIran_MissileFactory",
        IR_FAC_KEY, IR_CB_KEY, IR_CS_KEY, IR_WEP_KEY,
        "; ===== Iran missiles A-J (Weapon.ini load path for Command_FireMainWeapon) =====",
        r"Data\INI\Object\Specter\Iranian Army",
        IR_TRUCK, IR_TRUCKD, rf"Art\Textures\{IR_TRUCK}", rf"Art\Textures\{IR_TRUCKD}",
        IR_FLAG, has_iran_flag, IRAN_MISSILES,
        {"dark": IR_DARK, "mid": IR_MID, "metal": IR_METAL},
        "IranSupplyCenter", IRAN_KEEP,
    ),
    _country(
        "US", "America", "America", "America",
        "AmericaDozerCommandSet", "America_MissileFactory",
        "America_MissileFactoryCommandSet",
        "Command_ConstructAmerica_MissileFactory",
        US_FAC_KEY, US_CB_KEY, US_CS_KEY, US_WEP_KEY,
        "; ===== America missiles A-J (Weapon.ini load path for Command_FireMainWeapon) =====",
        r"Data\INI\Object\Specter\United States Of America",
        US_TRUCK, US_TRUCKD, rf"Art\Textures\{US_TRUCK}", rf"Art\Textures\{US_TRUCKD}",
        US_FLAG, has_usa_flag, AMERICA_MISSILES,
        {"dark": US_DARK, "mid": US_MID, "metal": US_METAL},
        "AmericaSupplyCenter", AMERICA_KEEP,
    ),
    _country(
        "IL", "Israel", "Israel", "Israel",
        "IsraelDozerCommandSet", "Israel_MissileFactory",
        "Israel_MissileFactoryCommandSet",
        "Command_ConstructIsrael_MissileFactory",
        IL_FAC_KEY, IL_CB_KEY, IL_CS_KEY, IL_WEP_KEY,
        "; ===== Israel missiles A-J (Weapon.ini load path for Command_FireMainWeapon) =====",
        r"Data\INI\Object\Specter\Israel Defense Forces",
        IL_TRUCK, IL_TRUCKD, rf"Art\Textures\{IL_TRUCK}", rf"Art\Textures\{IL_TRUCKD}",
        IL_FLAG, has_israel_flag, ISRAEL_MISSILES,
        {"dark": IL_DARK, "mid": IL_MID, "metal": IL_METAL},
        "AirF_AmericaSupplyCenter", ISRAEL_KEEP,
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

assert IRAN_MISSILES[0]["expect"] != "red"
assert AMERICA_MISSILES[0]["expect"] != "red"
assert ISRAEL_MISSILES[0]["expect"] != "red"
_seqs = [
    [m["expect"] for m in IRAN_MISSILES],
    [m["expect"] for m in AMERICA_MISSILES],
    [m["expect"] for m in ISRAEL_MISSILES],
    [m["expect"] for m in cr.CHINA_MISSILES],
    [m["expect"] for m in cr.RUSSIA_MISSILES],
    [m["expect"] for m in ts.TURKEY_MISSILES],
    [m["expect"] for m in ts.SPAIN_MISSILES],
    [m["expect"] for m in su.SWEDEN_MISSILES],
    [m["expect"] for m in su.UKRAINE_MISSILES],
    [m["expect"] for m in bf.BRITAIN_MISSILES],
    [m["expect"] for m in bf.FRANCE_MISSILES],
    [m["expect"] for m in gi.GERMANY_MISSILES],
    [m["expect"] for m in gi.ITALY_MISSILES],
]
for i, a in enumerate(_seqs):
    for j, b in enumerate(_seqs):
        if i < j:
            assert a != b, f"color sequence collision {i} {j}"
assert AMERICA_MISSILES[0]["acc"] > IRAN_MISSILES[0]["acc"]
assert ISRAEL_MISSILES[4]["acc"] > AMERICA_MISSILES[4]["acc"]
assert IRAN_MISSILES[-1]["kg"] > AMERICA_MISSILES[-1]["kg"]
assert AMERICA_MISSILES[-1]["km"] > ISRAEL_MISSILES[-1]["km"]


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
            f"{m['truck']} / {m['truckd']} (not Irq_9P117 / Skr_TEL / Jpn_TEL / Chi_TEL donor)",
        )
    )


def projectile_ini(m: dict) -> str:
    return sk.projectile_ini(m).replace("South Korea", m["label"])


def weapon_file(c: dict) -> str:
    head = (
        c["wep_marker"] + "\n"
        f"; Dedicated {c['label']} A-J. Distinct from the other new countries and all accepted rosters.\n"
        "; ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000.\n"
        "; Death HACK is a separate path and is not folded into PrimaryDamage.\n"
        "; Acc/CHL columns are design labels mapped to ScatterRadius / MaxHealth.\n"
    )
    body = sk.weapon_blocks(c["derived"])
    pairs = body.split("\n\n", 1)[1] if "\n\n" in body else body
    return head + "\n" + pairs


def factory_commandset(c: dict) -> str:
    slots = "\r\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(c["derived"], start=1))
    return (
        f"CommandSet {c['fac_cs']}\r\n"
        f"{slots}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def commandbutton_all(c: dict) -> str:
    lines = [
        f"; {c['label']} missiles A-J production buttons. Factory construct button is PR #652.",
        "; Shared specter_missile_* cameos. Unique Object bindings.",
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


def restore_airf(block: str) -> str:
    if "Command_ConstructIsrael_MissileFactory" not in block:
        raise SystemExit("expected Israel factory on AirF_AmericaDozerCommandSet")
    if "Command_DisarmMinesAtPosition" in block:
        raise SystemExit("AirF already has Clear Mines")
    return block.replace(
        "Command_ConstructIsrael_MissileFactory",
        "Command_DisarmMinesAtPosition",
    )


def israel_builder(airf_with_factory: str) -> str:
    if not airf_with_factory.startswith("CommandSet AirF_AmericaDozerCommandSet"):
        raise SystemExit("expected AirF header")
    return airf_with_factory.replace(
        "CommandSet AirF_AmericaDozerCommandSet",
        "CommandSet IsraelDozerCommandSet",
        1,
    )


def israel_dozer_ini(src: str) -> str:
    if "Object AirF_AmericaVehicleDozer" not in src:
        raise SystemExit("expected packed AirF_AmericaVehicleDozer")
    text = src.replace("Object AirF_AmericaVehicleDozer", "Object Israel_VehicleDozer", 1)
    text = text.replace(
        "CommandSet          = AirF_AmericaDozerCommandSet",
        "CommandSet          = IsraelDozerCommandSet",
        1,
    )
    if "Object AirF_AmericaVehicleDozer" in text:
        raise SystemExit("failed to retarget dozer object")
    if "AirF_AmericaDozerCommandSet" in text:
        raise SystemExit("new Israel dozer still bound to AirF commandset")
    if "Side                = Israel" not in text:
        raise SystemExit("Israel dozer lost Side=Israel")
    return (
        "; SPECTER last-wins Israel starting dozer. Cloned from packed AirF_AmericaVehicleDozer.\n"
        "; CommandSet=IsraelDozerCommandSet so FactionIsrael can construct Israel_MissileFactory.\n"
        "; Packed AirF_AmericaVehicleDozer / AirF_AmericaDozerCommandSet remain for AFG.\n"
        + text
    )


def commandset_file(blocks: list[str]) -> str:
    return "\r\n\r\n".join(blocks) + "\r\n"


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
        "IRAN + AMERICA + ISRAEL A-J MISSILE ROSTERS",
        "",
        "Baseline packed last-wins: SPECTER_IRAN_US_ISRAEL_FACTORY_BTNS (PR #652).",
        "Factories already existed as Rally/Sell shells. This pack fills A-J production.",
        "Iran dozer slot 10 and America/Israel construction slots from #652 are unchanged.",
        "",
        "ISRAEL DOZER packed last-wins resolution:",
        "  FactionIsrael StartingUnit0=Israel_VehicleDozer was ABSENT in #652.",
        "  Packed Israel dozer file still last-wins Object AirF_AmericaVehicleDozer",
        "  Side=Israel CommandSet=AirF_AmericaDozerCommandSet (FROZEN, shared with AFG).",
        "  NEW last-wins Object Israel_VehicleDozer CommandSet=IsraelDozerCommandSet",
        "  with slot 14=Command_ConstructIsrael_MissileFactory.",
        "  AirF_AmericaDozerCommandSet slot 14 restored to Command_DisarmMinesAtPosition.",
        "",
        "SPECTER design values. Not claimed real-world range or payload.",
        "Iran: Persian family (Hormuz … Simorgh). America: US family (LRASM … PK).",
        "Israel: Hebrew/Israeli family (Popeye … Keren). A is not red.",
        "Bavar-373 objects and IranHQ Command_ConstructIran_Bavar stay.",
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
        IR_FAC_KEY, US_FAC_KEY, IL_FAC_KEY,
        IR_FAC_CS_KEY, US_FAC_CS_KEY, IL_FAC_CS_KEY,
        IR_FAC_CB_KEY, US_FAC_CB_KEY, IL_FAC_CB_KEY,
        IR_DOZER_KEY, US_DOZER_KEY, IL_AIRF_DOZER_KEY,
        IR_BAVAR, IR_BAVAR_AI, PLAYER_PATCH, PLAYER_INI,
        cr.CN_DOZER_KEY, cr.CN_WF_KEY, cr.CN_SC_KEY, cr.CN_FAC_KEY, cr.CN_WEP_KEY,
        cr.CN_CS_KEY, cr.CN_CB_KEY, cr.RU_DOZER_KEY, cr.RU_WF_KEY, cr.RU_SC_KEY,
        cr.RU_FAC_KEY, cr.RU_WEP_KEY, cr.RU_CS_KEY, cr.RU_CB_KEY,
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
        IR_FLAG, US_FLAG, IL_FLAG, cr.CN_FLAG, cr.RU_FLAG,
        ts.TR_FLAG, ts.TR_FLAG2, ts.NT_FLAG, su.SE_FLAG, su.UA_FLAG,
        bf.GB_FLAG, bf.FR_FLAG, gi.DE_FLAG, gi.IT_FLAG,
        rf"Art\Textures\{ts.TR_TRUCK}", rf"Art\Textures\{ts.ES_TRUCK}",
        rf"Art\Textures\{su.SE_TRUCK}", rf"Art\Textures\{su.UA_TRUCK}",
        rf"Art\Textures\{bf.GB_TRUCK}", rf"Art\Textures\{bf.FR_TRUCK}",
        rf"Art\Textures\{gi.DE_TRUCK}", rf"Art\Textures\{gi.IT_TRUCK}",
        rf"Art\Textures\{cr.CN_TRUCK}", rf"Art\Textures\{cr.RU_TRUCK}",
    ]
    for key in frozen_art:
        if key and key in src_art and art.get(key) != src_art.get(key):
            fails.append(f"frozen ART mutated {key}")

    cs_text = data[CS_KEY].decode("latin1")
    src_cs = src_data[CS_KEY].decode("latin1")
    cb_text = data[CB_KEY].decode("latin1")
    src_cb = src_data[CB_KEY].decode("latin1")
    wep_text = data[WEAPON_KEY].decode("latin1")
    src_wep = src_data[WEAPON_KEY].decode("latin1")

    for key in (IR_CS_KEY, US_CS_KEY, IL_CS_KEY, IR_CB_KEY, US_CB_KEY, IL_CB_KEY,
                IR_WEP_KEY, US_WEP_KEY, IL_WEP_KEY, IL_DOZER_NEW_KEY):
        if "ZZZZ" in key:
            fails.append(f"ZZZZ {key}")
        if key.startswith(r"Data\INI\CommandSet_") and key <= CS_KEY:
            fails.append(f"satellite sorts before CommandSet.ini {key}")

    if IR_CS_KEY <= IR_FAC_CS_KEY:
        fails.append("Iran Missiles CS sorts before factory CS satellite")
    if US_CS_KEY <= US_FAC_CS_KEY:
        fails.append("America Missiles CS sorts before factory CS satellite")
    if IL_CS_KEY <= IL_FAC_CS_KEY:
        fails.append("Israel Missiles CS sorts before factory CS satellite")

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
        "Turkey_MissileFactoryCommandSet",
        "Spain_MissileFactoryCommandSet",
        "TurkeyDozerCommandSet",
        "NatoDozerCommandSet",
        "ChinaDozerCommandSet",
        "PLADozerCommandSet",
        "RussiaDozerCommandSet",
        "China_MissileFactoryCommandSet",
        "Russia_MissileFactoryCommandSet",
        "IranHQCommandSet",
        "Iraq_VT72BCommandSet",
    ):
        if sk.last_block(cs_text, "CommandSet", frozen_cs) != sk.last_block(src_cs, "CommandSet", frozen_cs):
            fails.append(f"{frozen_cs} mutated in CommandSet.ini")

    bavar_btn = sk.last_block(cb_text, "CommandButton", "Command_ConstructIranBavarSiteAI")
    src_bavar = sk.last_block(src_cb, "CommandButton", "Command_ConstructIranBavarSiteAI")
    if bavar_btn != src_bavar:
        fails.append("Command_ConstructIranBavarSiteAI mutated")
    mines_btn = sk.last_block(cb_text, "CommandButton", "Command_DisarmMinesAtPosition")
    src_mines = sk.last_block(src_cb, "CommandButton", "Command_DisarmMinesAtPosition")
    if mines_btn != src_mines:
        fails.append("Command_DisarmMinesAtPosition mutated")

    obj_re = re.compile(rb"^Object (\S+)", re.M)
    baseline_objects = set()
    for key, blob in src_data.items():
        if key.endswith(".ini") or key.endswith(".INI"):
            baseline_objects.update(mo.group(1).decode("ascii", "ignore") for mo in obj_re.finditer(blob))

    for c in COUNTRY_DEFS:
        new_b = sk.last_block(cs_text, "CommandSet", c["builder"])
        if c["fac_btn"] not in new_b:
            fails.append(f"{c['builder']} catalog missing factory")
        for keep in c["keep_cmds"]:
            if keep not in new_b:
                fails.append(f"{c['builder']} lost {keep}")
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", c["builder"])
        if c["fac_btn"] not in lw:
            fails.append(f"last-wins {c['builder']} from {_k} missing factory")
        if c["code"] == "IR" and "Command_ConstructIranBavarSiteAI" in lw:
            fails.append("Iran dozer slot 10 reverted to Bavar")
        if c["code"] == "US" and "Command_DisarmMinesAtPosition" in lw:
            fails.append("America dozer slot 14 reverted to Clear Mines")

        fac_cs = sk.last_block(cs_text, "CommandSet", c["fac_cs"])
        slots = re.findall(rf"CB_{c['prefix'].upper()}_MISSILE_([A-Z])", fac_cs)
        if slots != list("ABCDEFGHIJ"):
            fails.append(f"{c['code']} factory catalog slots {slots}")
        if "Command_Sell" not in fac_cs or "Command_SetRallyPoint" not in fac_cs:
            fails.append(f"{c['code']} factory missing Rally/Sell")
        _fk, fac_lw = sk.last_block_from_files(order, data, "CommandSet", c["fac_cs"])
        lw_slots = re.findall(rf"CB_{c['prefix'].upper()}_MISSILE_([A-Z])", fac_lw)
        if lw_slots != list("ABCDEFGHIJ"):
            fails.append(f"{c['code']} last-wins factory slots {lw_slots} from {_fk}")
        own = f"CB_{c['prefix'].upper()}_"
        foreign = (
            "CB_VIETNAM_", "CB_UAE_", "CB_JAPAN_", "CB_GERMANY_", "CB_ITALY_",
            "CB_BRITAIN_", "CB_FRANCE_", "CB_SWEDEN_", "CB_UKRAINE_",
            "CB_TURKEY_", "CB_SPAIN_", "CB_CHINA_", "CB_RUSSIA_",
            "CB_IRAN_", "CB_AMERICA_", "CB_ISRAEL_",
        )
        if any(tag in fac_lw for tag in foreign if tag != own):
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
            if sk.field(unit, "SelectPortrait") != m["cameo"]:
                fails.append(f"{c['code']} {m['slot']} SelectPortrait")
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
            if sk.field(bblock, "ButtonImage") != m["cameo"]:
                fails.append(f"{c['code']} {m['slot']} button image")
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

    airf_k, airf_lw = sk.last_block_from_files(order, data, "CommandSet", "AirF_AmericaDozerCommandSet")
    if not airf_lw or "Command_DisarmMinesAtPosition" not in airf_lw:
        fails.append(f"AFG AirF last-wins missing Clear Mines from {airf_k}")
    if airf_lw and "Command_ConstructIsrael_MissileFactory" in airf_lw:
        fails.append("AFG AirF still has Israel factory")
    for keep in ISRAEL_KEEP:
        if keep not in (airf_lw or ""):
            fails.append(f"AFG AirF lost {keep}")

    airf_obj = sk.last_block(data[IL_AIRF_DOZER_KEY].decode("latin1"), "Object", "AirF_AmericaVehicleDozer")
    if sk.field(airf_obj, "CommandSet") != "AirF_AmericaDozerCommandSet":
        fails.append("AirF_AmericaVehicleDozer CommandSet mutated")
    if sk.field(airf_obj, "Side") != "Israel":
        fails.append("AirF_AmericaVehicleDozer Side mutated")

    _dk, isr_dozer = sk.last_block_from_files(order, data, "Object", "Israel_VehicleDozer")
    if not isr_dozer:
        fails.append("Israel_VehicleDozer missing")
    elif sk.field(isr_dozer, "CommandSet") != "IsraelDozerCommandSet":
        fails.append("Israel_VehicleDozer CommandSet")
    elif sk.field(isr_dozer, "Side") != "Israel":
        fails.append("Israel_VehicleDozer Side")

    faction = sk.last_block(data[PLAYER_PATCH].decode("latin1"), "PlayerTemplate", "FactionIsrael")
    if "StartingUnit0     = Israel_VehicleDozer" not in faction:
        fails.append("FactionIsrael StartingUnit0 changed")
    afg = sk.last_block(data[PLAYER_INI].decode("latin1"), "PlayerTemplate", "FactionAmericaAirForceGeneral")
    if "StartingUnit0     = AirF_AmericaVehicleDozer" not in afg:
        fails.append("AFG StartingUnit0 changed")

    if sk.illegal_floats(wep_text):
        fails.append(f"illegal floats {sk.illegal_floats(wep_text)}")
    r11 = sk.last_block(data[sk.R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB")
    if sk.field(r11, "BuildCost") != "1200":
        fails.append("9P117 BuildCost")
    for obj in ("IranBavarSiteAI", "Iran_Bavar", "Iran_Bavar_CombatMode", "BavarMissile",
                "China_YJ18", "Russia_Kalibr", "Turkey_Atmaca", "Spain_Albatros"):
        if not sk.last_block_from_files(order, data, "Object", obj)[1]:
            fails.append(f"lost object {obj}")
    for key, expect in (
        ("CONTROLBAR:ToolTipVietnamMissileA", "Accuracy: 10/100"),
        ("CONTROLBAR:ChinaMissileA", "A YJ18"),
        ("CONTROLBAR:RussiaMissileA", "A Kalibr"),
        ("CONTROLBAR:TurkeyMissileA", "A Atmaca"),
        ("CONTROLBAR:SpainMissileA", "A Albatros"),
        ("CONTROLBAR:ConstructIranBavarSiteAI", "Bavar-373"),
        ("CONTROLBAR:BritainMissileA", "A Spear"),
        ("CONTROLBAR:FranceMissileA", "A MdCN"),
        ("CONTROLBAR:GermanyMissileA", "A KEPD-350"),
        ("CONTROLBAR:ItalyMissileA", "A Marte"),
        ("CONTROLBAR:SwedenMissileA", "A RBS15"),
        ("CONTROLBAR:UkraineMissileA", "A Neptune"),
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
    avgs = []
    for key in (rf"Art\Textures\{IR_TRUCK}", rf"Art\Textures\{US_TRUCK}", rf"Art\Textures\{IL_TRUCK}"):
        avgs.append(
            Image.open(io.BytesIO(art[key])).convert("RGB").resize(
                (1, 1), Image.Resampling.BOX
            ).getpixel((0, 0))
        )
    donors = []
    for key in (
        rf"Art\Textures\{ts.TR_TRUCK}", rf"Art\Textures\{ts.ES_TRUCK}",
        rf"Art\Textures\{su.SE_TRUCK}", rf"Art\Textures\{su.UA_TRUCK}",
        rf"Art\Textures\{bf.GB_TRUCK}", rf"Art\Textures\{bf.FR_TRUCK}",
        rf"Art\Textures\{gi.DE_TRUCK}", rf"Art\Textures\{gi.IT_TRUCK}",
        rf"Art\Textures\{cr.CN_TRUCK}", rf"Art\Textures\{cr.RU_TRUCK}",
        sk.TRUCK_DDS,
    ):
        donors.append(
            Image.open(io.BytesIO(src_art[key])).convert("RGB").resize(
                (1, 1), Image.Resampling.BOX
            ).getpixel((0, 0))
        )
    if len(set(avgs)) != 3:
        fails.append(f"trucks not distinct {avgs}")
    if any(a in donors for a in avgs):
        fails.append(f"truck still donor {avgs}")
    for name, btn in (
        ("PLADozerCommandSet", "Command_ConstructChina_MissileFactory"),
        ("RussiaDozerCommandSet", "Command_ConstructRussia_MissileFactory"),
        ("TurkeyDozerCommandSet", "Command_ConstructTurkey_MissileFactory"),
        ("NatoDozerCommandSet", "Command_ConstructSpain_MissileFactory"),
        ("SwedenDozerCommandSet", "Command_ConstructSweden_MissileFactory"),
        ("UkraineDozerCommandSet", "Command_ConstructUkraine_MissileFactory"),
        ("BritainDozerCommandSet", "Command_ConstructBritain_MissileFactory"),
        ("FranceDozerCommandSet", "Command_ConstructFrance_MissileFactory"),
        ("GermanyDozerCommandSet", "Command_ConstructGermany_MissileFactory"),
        ("ItalyDozerCommandSet", "Command_ConstructItaly_MissileFactory"),
        ("Iraq_VT72BCommandSet", "Command_ConstructIraq_AlFahdMissileFactory"),
        ("IranHQCommandSet", "Command_ConstructIran_Bavar"),
        ("IranDozerCommandSet", "Command_ConstructIran_MissileFactory"),
        ("AmericaDozerCommandSet", "Command_ConstructAmerica_MissileFactory"),
    ):
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", name)
        if not lw or btn not in lw:
            fails.append(f"preserved slot lost {name}")
    return fails


def write_loose(blocks: dict[str, list[str]], israel_dozer: str) -> None:
    for c in COUNTRY_DEFS:
        wheel_dir = LOOSE / c["path"].replace("Data\\INI\\", "").replace("\\", "/") / "Wheeled"
        proj_dir = LOOSE / c["path"].replace("Data\\INI\\", "").replace("\\", "/")
        wep_dir = LOOSE / "Weapon"
        for d in (wheel_dir, proj_dir, wep_dir):
            d.mkdir(parents=True, exist_ok=True)
        (wep_dir / Path(c["wep_key"].replace("\\", "/")).name).write_text(weapon_file(c), encoding="utf-8")
        (LOOSE / Path(c["cb_key"].replace("\\", "/")).name).write_text(commandbutton_all(c), encoding="utf-8")
        (LOOSE / Path(c["cs_key"].replace("\\", "/")).name).write_text(
            commandset_file(blocks[c["code"]]), encoding="utf-8"
        )
        for m in c["derived"]:
            (wheel_dir / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
            (proj_dir / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")
    dozer_path = LOOSE / IL_DOZER_NEW_KEY.replace("Data\\INI\\", "").replace("\\", "/")
    dozer_path.parent.mkdir(parents=True, exist_ok=True)
    dozer_path.write_text(israel_dozer, encoding="utf-8")


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_IRAN_US_ISRAEL_FACTORY_BTNS")
    if sk.sha256_path(SRC_ART) != SHA_ART_SRC or SRC_ART.stat().st_size != SIZE_ART_SRC:
        raise SystemExit("ART baseline is not SPECTER_IRAN_US_ISRAEL_FACTORY_BTNS")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art = sk.parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    donor_truck = Image.open(io.BytesIO(src_art[sk.TRUCK_DDS]))
    donor_truckd = Image.open(io.BytesIO(src_art[sk.TRUCKD_DDS]))

    cs = src_data[CS_KEY].decode("latin1")
    cb = src_data[CB_KEY].decode("latin1")
    wep = src_data[WEAPON_KEY].decode("latin1")

    airf_old = sk.last_block(cs, "CommandSet", "AirF_AmericaDozerCommandSet")
    airf_new = restore_airf(airf_old)
    isr_dozer_cs = israel_builder(airf_old)
    cs = sk.replace_last(cs, "CommandSet", "AirF_AmericaDozerCommandSet", airf_new)
    if sk.last_block(cs, "CommandSet", "IsraelDozerCommandSet"):
        cs = sk.replace_last(cs, "CommandSet", "IsraelDozerCommandSet", isr_dozer_cs)
    else:
        cs = cs.rstrip("\r\n") + "\r\n\r\n" + isr_dozer_cs + "\r\n"

    israel_dozer = israel_dozer_ini(src_data[IL_AIRF_DOZER_KEY].decode("latin1"))
    data[IL_DOZER_NEW_KEY] = sk.to_crlf(israel_dozer)

    flags = {}
    satellite_blocks = {}
    for c in COUNTRY_DEFS:
        flags[c["code"]] = Image.open(io.BytesIO(src_art[c["flag_key"]])).convert("RGBA")
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
        data[c["wep_key"]] = sk.to_crlf(weapon_file(c))
        data[c["cb_key"]] = sk.to_crlf(commandbutton_all(c))
        builder = sk.last_block(cs, "CommandSet", c["builder"])
        if c["fac_btn"] not in builder:
            raise SystemExit(f"{c['builder']} missing factory before A-J fill")
        fac_cs = factory_commandset(c)
        if sk.last_block(cs, "CommandSet", c["fac_cs"]):
            cs = sk.replace_last(cs, "CommandSet", c["fac_cs"], fac_cs)
        else:
            cs = cs.rstrip("\r\n") + "\r\n\r\n" + fac_cs + "\r\n"
        if c["code"] == "IL":
            blocks = [airf_new, builder, fac_cs]
        else:
            blocks = [builder, fac_cs]
        satellite_blocks[c["code"]] = blocks
        data[c["cs_key"]] = sk.to_crlf(commandset_file(blocks))
        extra = commandbutton_all(c).replace("\n", "\r\n")
        if c["derived"][0]["button"] in cb:
            raise SystemExit(f"CommandButton.ini already had {c['label']} A-J")
        cb = cb.rstrip("\r\n") + "\r\n\r\n" + extra + "\r\n"
        if c["wep_marker"] in wep or f"Weapon Weapon_{c['derived'][0]['object']}" in wep:
            raise SystemExit(f"Weapon.ini already had {c['label']} A-J")
        wep = wep.rstrip("\r\n") + "\r\n\r\n" + weapon_file(c).replace("\n", "\r\n")

    data[CS_KEY] = cs.encode("latin1")
    data[CB_KEY] = cb.encode("latin1")
    data[WEAPON_KEY] = wep.encode("latin1")
    data[CSF_KEY] = sk.csf_upsert(src_data[CSF_KEY], csf_map())
    write_loose(satellite_blocks, israel_dozer)

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
    parts = [
        sk.last_block(packed_cs, "CommandSet", "AirF_AmericaDozerCommandSet"),
        sk.last_block(packed_cs, "CommandSet", "IsraelDozerCommandSet"),
    ]
    for c in COUNTRY_DEFS:
        parts.append(sk.last_block(packed_cs, "CommandSet", c["builder"]))
        parts.append(sk.last_block(packed_cs, "CommandSet", c["fac_cs"]))
        (ext / Path(c["wep_key"].replace("\\", "/")).name).write_text(weapon_file(c), encoding="utf-8")
        for m in c["derived"]:
            (ext / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
    (ext / "Israel_VehicleDozer.ini").write_text(israel_dozer, encoding="utf-8")
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
    zip_path = ROOT / "patch/Release/SPECTER_IRAN_US_ISRAEL_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)
    tag = "s-iran-us-israel-missiles-aj"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/"
        + tag
    )

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #652 s-iran-us-israel-factory-btns + #651 + #650 + #649 + #648 + #647",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        f"ART_GZ_SIZE={art_gz_path.stat().st_size}",
        f"ART_GZ_SHA256={art_gz_sha}",
        "IRAN_FACTORY_EXISTING=YES",
        "AMERICA_FACTORY_EXISTING=YES",
        "ISRAEL_FACTORY_EXISTING=YES",
        "IRAN_REMAINS_IRAN=YES",
        "AMERICA_REMAINS_AMERICA=YES",
        "ISRAEL_REMAINS_ISRAEL=YES",
        "IRAN_DOZER_SLOT10=Command_ConstructIran_MissileFactory",
        "AMERICA_DOZER_SLOT14=Command_ConstructAmerica_MissileFactory",
        "ISRAEL_DOZER_SLOT14=Command_ConstructIsrael_MissileFactory",
        "AIRF_SLOT14_RESTORED=Command_DisarmMinesAtPosition",
        "ISRAEL_VEHICLE_DOZER_LASTWINS=YES",
        "AIRF_AMERICA_VEHICLE_DOZER_FROZEN=YES",
        "BAVAR373_KEPT=YES",
        "IR_US_IL_FLAGS_FROZEN=YES",
        "CN_RU_TR_ES_SE_UA_GB_FR_DE_IT_AJ_KEPT=YES",
        "NO_REARM=YES",
        "NO_RADARPRIORITY=YES",
        "ROSTER_COUNT=30",
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
            "ZIP_FILE=SPECTER_IRAN_US_ISRAEL_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #652",
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
                "  Do not install the .gz file as the game BIG.",
                "",
                "ART is also inside the ZIP as uncompressed _SPEC_ART_ONE.big (same SHA).",
                "GitHub rejects raw files >= 2147483648 bytes.",
                "",
                "ZIP (complete uncompressed DATA + ART BIGs):",
                f"  {rel_base}/SPECTER_IRAN_US_ISRAEL_MISSILES_AJ.zip",
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
        "Iran complete missile roster A-J, America complete missile roster A-J,\n"
        "and Israel complete missile roster A-J on existing PR #652 factories.\n"
        "Israel starting dozer object is last-won so FactionIsrael can construct.\n"
        "America Air Force General Clear Mines is restored on AirF_AmericaDozerCommandSet.\n"
        "Bavar-373, CN/RU/TR/ES/SE/UA/GB/FR/DE/IT A-J, and IR/US/IL flags stay frozen.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Iran + USA + Israel missiles A-J\n\n"
        "- Uses existing Iran_MissileFactory, America_MissileFactory, Israel_MissileFactory.\n"
        "- Iran: Hormuz … Simorgh. America: LRASM … PK. Israel: Popeye … Keren.\n"
        "- Israel_VehicleDozer last-wins with IsraelDozerCommandSet (factory slot 14).\n"
        "- AirF_AmericaDozerCommandSet slot 14 restored to Clear Mines for AFG.\n"
        "- Iran remains Iran. America remains America. Israel remains Israel.\n"
        "- Bavar-373, IR/US/IL flags, and previous country A-J rosters preserved.\n"
        "- Tooltips include Acc/100 and Radar Stealth/100 with caveats.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_IranMissiles.ini last-wins IranDozerCommandSet and Iran_MissileFactoryCommandSet.\n"
        "CommandSet_AmericaMissiles.ini last-wins AmericaDozerCommandSet and America_MissileFactoryCommandSet.\n"
        "CommandSet_IsraelMissiles.ini last-wins IsraelDozerCommandSet, Israel_MissileFactoryCommandSet,\n"
        "and restores AirF_AmericaDozerCommandSet to Clear Mines after CommandSet_IsraelMissileFactory.ini.\n"
        "Packed AirF_AmericaVehicleDozer file is frozen. NEW Israel_VehicleDozer.ini last-wins the starting dozer.\n"
        "Factory object INIs from PR #652 are frozen (Rally/Sell CommandSet field still valid; menu last-wins).\n"
        "IR_Flag.tga / US_Flag.tga / IL_Flag.tga are frozen. Dorsal stamps are generated.\n"
        "Bavar-373 objects and Command_ConstructIranBavarSiteAI / Command_ConstructIran_Bavar stay.\n"
        "China/Russia #651, Turkey/Spain #650, Sweden/Ukraine #649, Britain/France #648, Germany/Italy #647 stay.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:80]))


if __name__ == "__main__":
    main()
