#!/usr/bin/env python3
"""Canonical 14-slot national ground rosters.

Protected factions are not listed and must not be edited:
USA, Russia, China, Iran, Iraq, Egypt, Israel, North Korea, NATO.
"""

from __future__ import annotations

from dataclasses import dataclass

LOCKED_BIG_PATHS = (
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\Science.ini",
    r"Data\INI\SpecialPower.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Tracked\Japan_VT72B.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_CommandCenter.ini",
    r"Data\INI\Object\Specter\South Korean Armed Forces\Tracked\SouthKorea_VT72B.ini",
    r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_CommandCenter.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Tracked\Vietnam_VT72B.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_CommandCenter.ini",
)

DO_NOT_PACK_OVERLAY = (
    r"Data\INI\CommandSet_Japan.ini",
    r"Data\INI\CommandSet_SouthKorea.ini",
    r"Data\INI\CommandSet_Vietnam.ini",
)

PROTECTED_COMMANDSETS = (
    "AmericaWarFactoryCommandSet",
    "RussiaWarFactoryCommandSet",
    "PLAWarFactoryCommandSet",
    "ChinaWarFactoryCommandSet",
    "IranWarfactoryCommandSet",
    "Iraq_WarFactoryCommandSet",
    "Egypt_WarFactoryCommandSet",
    "EgyptWarFactoryCommandSet",
    "Israel_WarFactoryCommandSet",
    "NorthKorea_WarFactoryCommandSet",
    "NatoWarfactoryCommandSet",
)

# Leftover overlay CommandSets that still list missing NATO-clone buttons.
# Live War Factories use the no-underscore names (GermanyWarfactoryCommandSet).
# These aliases must still be complete national 14-slot menus.
ALIAS_COMMANDSETS = {
    "Germany_WarFactoryCommandSet": "Germany",
    "France_WarFactoryCommandSet": "France",
    "Britain_WarFactoryCommandSet": "Britain",
    "Italy_WarFactoryCommandSet": "Italy",
}

ROLES = (
    "MBT",
    "Heavy Tank",
    "Recon",
    "IFV",
    "APC",
    "SHORAD",
    "Mobile SAM",
    "Radar",
    "MLRS",
    "Ballistic/Cruise TEL",
    "SPA",
    "AT Vehicle",
    "Engineer",
    "Special",
)

# role -> (template object, default cost, default time, default cameo)
TEMPLATES = {
    "mbt": ("AmericaTankCrusader", 1200, 20, "us_m1a2"),
    "heavy": ("GermanyTankLeopard2A7Plus", 1600, 22, "us_m1a2"),
    "recon": ("AmericaVehicleM1296", 800, 15, "us_m1126"),
    "ifv": ("AmericaTankMicrowave", 900, 16, "us_m2a3"),
    "apc": ("AmericaVehicleHumvee", 700, 14, "us_m1126"),
    "shorad": ("AmericaTankAvenger", 800, 16, "us_m6"),
    "sam": ("US_THAAD", 2200, 28, "us_m1120"),
    "radar": ("US_AN_TPY2", 2000, 24, "us_an_tpy2"),
    "mlrs": ("AmericaVehicleTomahawk", 1400, 20, "us_m270"),
    "ballistic": ("US_M1075T_BGM109", 1800, 26, "us_m1075"),
    "spa": ("AmericaTankPaladin", 1300, 20, "us_m109a7"),
    "at": ("AmericaVehicle_M1128", 900, 16, "us_m1128"),
    "eng": ("AmericaVehicleSentryDrone", 700, 14, "us_matv"),
    "special": ("GermanyTankLeopard2A7Plus", 2000, 24, "us_m1a2"),
}


@dataclass(frozen=True)
class GroundUnit:
    role: str
    obj: str
    display: str
    tooltip: str
    model_pref: str
    model_fallback: str
    image: str


@dataclass(frozen=True)
class CountryGround:
    key: str
    side: str
    wf: str
    cs: str
    units: tuple[GroundUnit, ...]


def U(role, obj, display, tooltip, pref, fallback, image):
    return GroundUnit(role, obj, display, tooltip, pref, fallback, image)


JAPAN = CountryGround(
    "Japan",
    "Japan",
    "Japan_WarFactory",
    "Japan_WarFactoryCommandSet",
    (
        U("mbt", "JapanTankType10", "Type 10", "JGSDF Type 10 main battle tank", "LSFJapan10Tank", "US_M1A2Sep2", "us_m1a2"),
        U("heavy", "JapanTankType90", "Type 90", "JGSDF Type 90 main battle tank", "LSF90tank", "NAT_L2A7V", "us_m1a2"),
        U("recon", "JapanVehicleType16", "Type 16 MCV", "JGSDF Type 16 maneuver combat vehicle", "US_M1296", "US_M1296", "us_m1126"),
        U("ifv", "JapanVehicleType89", "Type 89 IFV", "JGSDF Type 89 infantry fighting vehicle", "LSFJP89W", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "JapanVehicleType96", "Type 96 WAPC", "JGSDF Type 96 wheeled APC", "NAT_VBCI", "US_M1126", "us_m1126"),
        U("shorad", "JapanVehicleType87", "Type 87 SPAAG", "JGSDF Type 87 self-propelled anti-aircraft gun", "LSFJP87V", "US_M6", "us_m6"),
        U("sam", "JapanVehicleChuSAM", "Type 03 Chu-SAM", "JGSDF Type 03 Chu-SAM medium-range SAM", "NAT_IRIST_SLM", "US_M1120", "us_m1120"),
        U("radar", "JapanVehicleRadar", "J/TPS-P18", "JGSDF J/TPS-P18 air-search radar", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "JapanVehicleM270", "M270 MLRS", "JGSDF licensed M270 rocket launcher", "LSFJPM270", "US_M270", "us_m270"),
        U("ballistic", "JapanVehicleType12", "Type 12 SSM", "JGSDF Type 12 surface-to-ship missile", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "JapanVehicleType99", "Type 99 SPH", "JGSDF Type 99 self-propelled howitzer", "LSFJP99", "US_M109A7", "us_m109a7"),
        U("at", "JapanVehicleType16AT", "Type 96 MPMS", "JGSDF Type 96 multi-purpose missile system", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "JapanVehicleType11ARV", "Type 11 ARV", "JGSDF Type 11 armored recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "JapanVehicleType12Btry", "Type 88 SSM", "JGSDF Type 88 surface-to-ship missile", "US_M1075", "RUS_9K720", "us_m1075"),
    ),
)

SOUTHKOREA = CountryGround(
    "SouthKorea",
    "SouthKorea",
    "SouthKorea_WarFactory",
    "SouthKorea_WarFactoryCommandSet",
    (
        U("mbt", "SouthKoreaTankK1A2", "K2 Black Panther", "ROK Army K2 Black Panther main battle tank", "LSFK1A1", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "SouthKoreaTankK1A1", "K1A2", "ROK Army K1A2 main battle tank", "LSFK1A1", "US_M1A2Sep2", "us_m1a2"),
        U("recon", "SouthKoreaVehicleK200", "K806 White Tiger", "ROK Army K806 White Tiger recon vehicle", "US_M1126", "US_M1126", "us_m1126"),
        U("ifv", "SouthKoreaVehicleK21", "K21 IFV", "ROK Army K21 infantry fighting vehicle", "LSFK21", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "SouthKoreaVehicleK200APC", "K200A1", "ROK Army K200A1 armored personnel carrier", "US_M1126", "NAT_VBCI", "us_m1126"),
        U("shorad", "SouthKoreaVehicleK30", "K30 Biho", "ROK Army K30 Biho self-propelled AA", "US_M6", "US_M6", "us_m6"),
        U("sam", "SouthKoreaVehicleCheongung", "KM-SAM", "ROK Army KM-SAM Cheongung", "NAT_IRIST_SLM", "US_M1120", "us_m1120"),
        U("radar", "SouthKoreaVehicleRadar", "TPS-830K", "ROK Army TPS-830K air-defense radar", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "SouthKoreaVehicleChunmoo", "K239 Chunmoo", "ROK Army K239 Chunmoo MLRS", "KVChunmoo", "US_M270", "us_m270"),
        U("ballistic", "SouthKoreaVehicleHyunmoo", "Hyunmoo Missile", "ROK Army Hyunmoo-2 ballistic missile TEL", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "SouthKoreaVehicleK9", "K9 Thunder", "ROK Army K9 Thunder self-propelled howitzer", "LSF2S19", "US_M109A7", "us_m109a7"),
        U("at", "SouthKoreaVehicleK21AT", "AT-1K Raybolt", "ROK Army AT-1K Raybolt anti-tank vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "SouthKoreaVehicleK288", "K288 ARV", "ROK Army K288 recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "SouthKoreaVehicleHyunmoo2B", "Hyunmoo-3", "ROK Army Hyunmoo-3 cruise-missile TEL", "LSFIskander", "RUS_9K720", "us_m1075"),
    ),
)

GERMANY = CountryGround(
    "Germany",
    "Germany",
    "GermanyWarFactory",
    "GermanyWarfactoryCommandSet",
    (
        U("mbt", "GermanyTankLeopard2A7", "Leopard 2A7", "Bundeswehr Leopard 2A7 main battle tank", "NAT_L2A7V", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "GermanyTankLeopard2A6", "Leopard 2A6", "Bundeswehr Leopard 2A6 main battle tank", "NAT_L2A7V", "US_M1A2Sep2", "us_m1a2"),
        U("recon", "GermanyVehicleFennek", "Fennek", "Bundeswehr Fennek recon vehicle", "US_M1296", "US_M1296", "us_m1126"),
        U("ifv", "GermanyVehiclePuma", "Puma", "Bundeswehr Puma infantry fighting vehicle", "NAT_Puma", "NAT_Puma", "us_m2a3"),
        U("apc", "GermanyVehicleBoxer", "Boxer", "Bundeswehr Boxer armored personnel carrier", "LSFBoxer", "NAT_VBCI", "us_m1126"),
        U("shorad", "GermanyVehicleGepard", "Gepard", "Bundeswehr Gepard self-propelled AA", "US_M6", "US_M6", "us_m6"),
        U("sam", "GermanyVehicleIRIST", "IRIS-T", "Bundeswehr IRIS-T SLM", "NAT_IRIST_SLM", "NAT_IRIST_SLM", "us_m1120"),
        U("radar", "GermanyVehicleTRML", "TRML-4D", "Bundeswehr TRML-4D air-defense radar", "NAT_TRML", "NAT_TRML", "us_an_tpy2"),
        U("mlrs", "GermanyVehicleMARS", "MARS II", "Bundeswehr MARS II / M270 MLRS", "NAT_M142", "US_M270", "us_m270"),
        U("ballistic", "GermanyVehicleTaurusTEL", "Taurus", "Taurus KEPD 350 cruise-missile launcher", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "GermanyVehiclePzH2000", "PzH 2000", "Bundeswehr PzH 2000 self-propelled howitzer", "NAT_Caesar", "US_M109A7", "us_m109a7"),
        U("at", "GermanyVehicleWieselAT", "Wiesel TOW", "Wiesel 1 TOW anti-tank vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "GermanyVehicleBuffel", "BPz3 Buffel", "Bundeswehr BPz3 Buffel recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "GermanyVehicleBoxerAA", "Boxer Skyranger", "Boxer Skyranger 30 air-defense vehicle", "LSFBoxer", "NAT_Puma", "us_m6"),
    ),
)

FRANCE = CountryGround(
    "France",
    "France",
    "FranceWarFactory",
    "FranceWarfactoryCommandSet",
    (
        U("mbt", "FranceTankLeclerc", "Leclerc", "Armee de Terre Leclerc main battle tank", "NAT_L2A7V", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "FranceTankAMX30", "AMX-30B2", "AMX-30B2 Brenus heavy tank", "LSFAMX30", "NAT_L2A7V", "us_m1a2"),
        U("recon", "FranceVehicleAMX10RC", "AMX-10RC", "AMX-10RC armored recon vehicle", "LSFamx10", "US_M1296", "us_m1126"),
        U("ifv", "FranceVehicleVBCI", "VBCI", "VBCI infantry fighting vehicle", "NAT_VBCI", "NAT_VBCI", "us_m2a3"),
        U("apc", "FranceVehicleVAB", "VBMR Griffon", "VBMR Griffon armored personnel carrier", "NAT_VBCI", "US_M1126", "us_m1126"),
        U("shorad", "FranceVehicleMistral", "Mistral", "Mistral short-range air-defense vehicle", "LSFAMX30", "US_M6", "us_m6"),
        U("sam", "FranceVehicleSAMPT", "SAMP/T", "SAMP/T Mamba air-defense system", "NAT_IRIST_SLM", "US_M1120", "us_m1120"),
        U("radar", "FranceVehicleGM200", "Ground Master 200", "Thales Ground Master 200 radar", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "FranceVehicleLRU", "M270", "French M270 LRU rocket launcher", "US_M270", "US_M270", "us_m270"),
        U("ballistic", "FranceVehicleSCALPTEL", "SCALP", "SCALP / MdCN cruise-missile launcher", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "FranceVehicleCaesar", "Caesar", "CAESAR 155mm self-propelled howitzer", "NAT_Caesar", "NAT_Caesar", "us_m109a7"),
        U("at", "FranceVehicleVABHOT", "VAB HOT", "VAB HOT anti-tank vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "FranceVehicleDNG", "Leclerc DNG", "Leclerc DNG recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "FranceVehicleJaguar", "EBRC Jaguar", "EBRC Jaguar combat recon vehicle", "LSFamx10", "US_M1296", "us_m1128"),
    ),
)

BRITAIN = CountryGround(
    "Britain",
    "Britain",
    "BritainWarFactory",
    "BritainWarfactoryCommandSet",
    (
        U("mbt", "BritainTankChallenger2", "Challenger 2", "British Army Challenger 2 main battle tank", "LSFChallenger2", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "BritainTankChallenger2TES", "Challenger 2 TES", "Challenger 2 TES heavy urban tank", "LSFChallenger2", "US_M1A2Sep2", "us_m1a2"),
        U("recon", "BritainVehicleAjax", "Ajax", "Ajax armored recon vehicle", "US_M1296", "US_M1296", "us_m1126"),
        U("ifv", "BritainVehicleWarrior", "Warrior", "FV510 Warrior infantry fighting vehicle", "LSFWarrior", "NAT_Puma", "us_m2a3"),
        U("apc", "BritainVehicleMastiff", "Mastiff", "Mastiff protected patrol vehicle / APC", "LSFBoxer", "US_M1126", "us_m1126"),
        U("shorad", "BritainVehicleStormer", "Stormer HVM", "Stormer HVM Starstreak SHORAD", "US_M6", "US_M6", "us_m6"),
        U("sam", "BritainVehicleSkySabre", "Sky Sabre", "Sky Sabre air-defense system", "NAT_IRIST_SLM", "US_M1120", "us_m1120"),
        U("radar", "BritainVehicleGiraffe", "Giraffe", "Saab Giraffe radar for Sky Sabre", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "BritainVehicleGMLRS", "M270 GMLRS", "British M270 GMLRS rocket launcher", "US_M270", "US_M270", "us_m270"),
        U("ballistic", "BritainVehicleStormShadowTEL", "Storm Shadow", "Storm Shadow cruise-missile launcher", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "BritainVehicleAS90", "AS90", "AS90 self-propelled gun", "LSFAS90", "US_M109A7", "us_m109a7"),
        U("at", "BritainVehicleStriker", "FV102 Striker", "FV102 Striker anti-tank vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "BritainVehicleCRARRV", "CRARRV", "Challenger armored repair and recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "BritainVehicleTrojan", "Trojan AVRE", "Trojan combat engineer vehicle", "LSFChallenger2", "NAT_L2A7V", "us_m1a2"),
    ),
)

ITALY = CountryGround(
    "Italy",
    "Italy",
    "ItalyWarFactory",
    "ItalyWarfactoryCommandSet",
    (
        U("mbt", "ItalyTankAriete", "C2 Ariete", "Esercito C2 Ariete main battle tank", "NAT_L2A7V", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "ItalyTankArieteC1", "C1 Ariete", "Esercito C1 Ariete heavy tank", "NAT_L2A7V", "US_M1A2Sep2", "us_m1a2"),
        U("recon", "ItalyVehicleCentauro", "B1 Centauro", "B1 Centauro wheeled tank destroyer", "NAT_Cortale", "US_M1128", "us_m1128"),
        U("ifv", "ItalyVehicleDardo", "Dardo", "Dardo infantry fighting vehicle", "NAT_Puma", "NAT_VBCI", "us_m2a3"),
        U("apc", "ItalyVehicleVBM", "Freccia", "VBM Freccia armored personnel carrier", "NAT_VBCI", "US_M1126", "us_m1126"),
        U("shorad", "ItalyVehicleSIDAM", "SIDAM 25", "SIDAM 25 self-propelled AA", "US_M6", "US_M6", "us_m6"),
        U("sam", "ItalyVehicleSAMPT", "SAMP/T", "Italian SAMP/T air-defense system", "NAT_IRIST_SLM", "US_M1120", "us_m1120"),
        U("radar", "ItalyVehicleRAT31", "RAT-31DL", "RAT-31DL air-defense radar", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "ItalyVehicleM270", "M270 MLRS", "Italian M270 rocket launcher", "US_M270", "US_M270", "us_m270"),
        U("ballistic", "ItalyVehicleStormShadowTEL", "Storm Shadow", "Storm Shadow cruise-missile launcher", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "ItalyVehiclePzH2000", "PzH 2000", "Italian PzH 2000 self-propelled howitzer", "NAT_Caesar", "US_M109A7", "us_m109a7"),
        U("at", "ItalyVehicleCentauroAT", "Centauro 105", "B1 Centauro 105mm anti-tank vehicle", "NAT_Cortale", "US_M1128", "us_m1128"),
        U("eng", "ItalyVehicleARV", "Ariete ARV", "Ariete armored recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "ItalyVehicleCentauro2", "Centauro II", "Centauro II 120mm wheeled tank destroyer", "NAT_Cortale", "US_M1128", "us_m1128"),
    ),
)

TURKEY = CountryGround(
    "Turkey",
    "Turkey",
    "TurkeyWarFactory",
    "TurkeyWarfactoryCommandSet",
    (
        U("mbt", "TurkeyTankLeopard2A4", "Leopard 2A4", "TSK Leopard 2A4 main battle tank", "NAT_L2A7V", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "TurkeyTankM60T", "M60T Sabra", "TSK M60T Sabra heavy tank", "US_M1A2Sep2", "US_M1A2Sep2", "us_m1a2"),
        U("recon", "TurkeyVehicleKaplan", "Kaplan-20", "Kaplan-20 recon / light tracked vehicle", "US_M1296", "US_M1296", "us_m1126"),
        U("ifv", "TurkeyVehicleACV15", "Tulpar IFV", "Tulpar infantry fighting vehicle", "NAT_Puma", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "TurkeyVehicleKirpi", "Kirpi", "BMC Kirpi armored personnel carrier", "US_M1126", "NAT_VBCI", "us_m1126"),
        U("shorad", "TurkeyVehicleKorkut", "Korkut", "Korkut self-propelled AA", "US_M6", "US_M6", "us_m6"),
        U("sam", "TurkeyVehicleHisar", "Hisar", "Hisar-O medium-range SAM", "NAT_IRIST_SLM", "US_M1120", "us_m1120"),
        U("radar", "TurkeyVehicleKalkan", "Kalkan", "Kalkan air-defense radar", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "TurkeyVehicleKasirga", "T-300 Kasirga", "T-300 Kasirga multiple rocket launcher", "US_M270", "Iraq_Bm21", "us_m270"),
        U("ballistic", "TurkeyVehicleBora", "Bora Missile", "Bora / Khan ballistic missile TEL", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "TurkeyVehicleFirtina", "T-155 Firtina", "T-155 Firtina self-propelled howitzer", "US_M109A7", "NAT_Caesar", "us_m109a7"),
        U("at", "TurkeyVehicleACVTOW", "ACV-15 TOW", "ACV-15 TOW anti-tank vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "TurkeyVehicleM88", "M88 ARV", "M88 armored recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "TurkeyVehicleAltay", "Altay", "Altay indigenous main battle tank", "NAT_L2A7V", "US_M1A2Sep2", "us_m1a2"),
    ),
)

UKRAINE = CountryGround(
    "Ukraine",
    "Ukraine",
    "UkraineWarFactory",
    "UkraineWarfactoryCommandSet",
    (
        U("mbt", "UkraineTankT84", "T-84", "Ukrainian T-84 Oplot main battle tank", "RUS_T90A", "RUS_T90A", "us_m1a2"),
        U("heavy", "UkraineTankT72AMT", "T-72AMT", "Ukrainian T-72AMT heavy tank", "Irq_T72M1", "NAT_L2A7V", "us_m1a2"),
        U("recon", "UkraineVehicleBRDM", "BRDM-2", "BRDM-2 armored recon vehicle", "US_MATV", "US_M1296", "us_m1126"),
        U("ifv", "UkraineVehicleBMP2", "BMP-2", "BMP-2 infantry fighting vehicle", "RUS_BMP3M", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "UkraineVehicleBTR4", "BTR-4", "BTR-4 Bucephalus armored personnel carrier", "Irq_BTR90", "US_M1126", "us_m1126"),
        U("shorad", "UkraineVehicleGepard", "Gepard", "Flakpanzer Gepard self-propelled AA", "LSFShilka", "US_M6", "us_m6"),
        U("sam", "UkraineVehicleBuk", "Buk-M1", "Buk-M1 medium-range SAM", "NAT_IRIST_SLM", "RUS_S400", "us_m1120"),
        U("radar", "UkraineVehicleP18", "35D6", "35D6 / ST-68 air-search radar", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "UkraineVehicleHIMARS", "HIMARS", "M142 HIMARS rocket launcher", "NAT_M142", "US_M270", "us_m270"),
        U("ballistic", "UkraineVehicleHrim2", "Hrim-2", "Hrim-2 ballistic missile TEL", "LSFIskander", "RUS_9K720", "us_m1075"),
        U("spa", "UkraineVehicleBohdana", "2S22 Bohdana", "2S22 Bohdana self-propelled howitzer", "LSF2S19", "US_M109A7", "us_m109a7"),
        U("at", "UkraineVehicleStugna", "Stugna-P", "Stugna-P anti-tank missile vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "UkraineVehicleBREM", "BREM-1", "BREM-1 armored recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "UkraineTankT64BV", "Neptune", "R-360 Neptune coastal missile launcher", "Irq_T72M1", "RUS_T90A", "us_m1a2"),
    ),
)

SWEDEN = CountryGround(
    "Sweden",
    "Sweden",
    "SwedenWarFactory",
    "SwedenWarfactoryCommandSet",
    (
        U("mbt", "SwedenTankStrv122", "Strv 122", "Stridsvagn 122 main battle tank", "strv122", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "SwedenTankStrv121", "Strv 121", "Stridsvagn 121 heavy tank", "strv122", "NAT_L2A7V", "us_m1a2"),
        U("recon", "SwedenVehicleCV90R", "CV90 Recce", "CV90 recce vehicle", "LSFCV90", "US_M1296", "us_m1126"),
        U("ifv", "SwedenVehicleCV90", "CV90", "Strf 90 infantry fighting vehicle", "LSFCV90", "NAT_Puma", "us_m2a3"),
        U("apc", "SwedenVehiclePatgb203", "Patgb 203", "Patgb 203 armored personnel carrier", "PATGB203", "NAT_VBCI", "us_m1126"),
        U("shorad", "SwedenVehicleLvkv90", "Lvkv 90", "Lvkv 90 air-defense CV90", "LSFCV90", "US_M6", "us_m6"),
        U("sam", "SwedenVehicleIRIST", "IRIS-T SLS", "IRIS-T SLS short-range SAM", "NAT_IRIST_SLM", "NAT_IRIST_SLM", "us_m1120"),
        U("radar", "SwedenVehicleGiraffe", "Giraffe AMB", "Giraffe AMB air-defense radar", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "SwedenVehiclePULS", "PULS", "PULS multiple rocket launcher", "US_M270", "NAT_M142", "us_m270"),
        U("ballistic", "SwedenVehicleRBS15", "RBS-15", "RBS-15 coastal missile launcher", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "SwedenVehicleArcher", "Archer", "Archer FH77BW self-propelled howitzer", "NAT_Caesar", "US_M109A7", "us_m109a7"),
        U("at", "SwedenVehicleCV90AT", "CV90120", "CV90120 anti-tank vehicle", "LSFCV90", "US_M1128", "us_m1128"),
        U("eng", "SwedenVehicleBgbv120", "Bgbv 120", "Bgbv 120 recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "SwedenTankStrv122B", "Strv 122B+", "Stridsvagn 122B+ special tank", "strv122", "NAT_L2A7V", "us_m1a2"),
    ),
)

INDIA = CountryGround(
    "India",
    "India",
    "India_WarFactory_T",
    "India_WarFactoryCommandSet",
    (
        U("mbt", "IndiaTankT90S", "T-90 Bhishma", "Indian T-90S Bhishma main battle tank", "IndiaT90S", "RUS_T90A", "us_m1a2"),
        U("heavy", "IndiaTankT72Ajeya", "T-72 Ajeya", "T-72M1 Ajeya heavy tank", "Irq_T72M1", "Irq_T72M1", "us_m1a2"),
        U("recon", "IndiaVehicleNAMICA", "NAMICA", "Nag missile carrier recon vehicle", "US_M1296", "US_MATV", "us_m1126"),
        U("ifv", "IndiaVehicleBMP2", "BMP-2", "BMP-2 Sarath infantry fighting vehicle", "RUS_BMP3M", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "IndiaVehicleKestrel", "Tata Kestrel", "Tata Kestrel wheeled APC", "Irq_BTR90", "US_M1126", "us_m1126"),
        U("shorad", "IndiaVehicleTunguska", "2S6 Tunguska", "2S6 Tunguska self-propelled AA", "LSFShilka", "US_M6", "us_m6"),
        U("sam", "IndiaVehicleAkash", "Akash", "Akash medium-range SAM", "Arb_S300", "US_M1120", "us_m1120"),
        U("radar", "IndiaVehicleRajendra", "Rajendra", "Rajendra 3D air-defense radar", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "IndiaVehiclePinaka", "Pinaka", "Pinaka multiple rocket launcher", "RUS_BM30", "US_M270", "us_m270"),
        U("ballistic", "IndiaVehiclePrahaar", "Prahaar", "Prahaar tactical ballistic missile TEL", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "IndiaVehicleK9Vajra", "K9 Vajra", "K9 Vajra-T self-propelled howitzer", "LSF2S19", "US_M109A7", "us_m109a7"),
        U("at", "IndiaVehicleNag", "Nag", "Nag anti-tank missile vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "IndiaVehicleVT72B", "VT-72B", "VT-72B armored recovery vehicle", "Irq_VT72B", "Irq_VT72B", "us_matv"),
        U("special", "IndiaTankArjun", "Arjun", "Arjun Mk1A indigenous main battle tank", "NAT_L2A7V", "RUS_T90A", "us_m1a2"),
    ),
)

PAKISTAN = CountryGround(
    "Pakistan",
    "Pakistan",
    "Pakistan_WarFactory_T",
    "Pakistan_WarFactoryCommandSet",
    (
        U("mbt", "PakistanTankAlKhalid", "Al-Khalid", "Al-Khalid main battle tank", "Arb_Khalid", "RUS_T90A", "us_m1a2"),
        U("heavy", "PakistanTankAlZarrar", "Al-Zarrar", "Al-Zarrar heavy tank", "Irq_T72M1", "Irq_T72M1", "us_m1a2"),
        U("recon", "PakistanVehicleMohafiz", "Mohafiz", "Mohafiz scout vehicle", "US_MATV", "US_M1296", "us_m1126"),
        U("ifv", "PakistanVehicleTalhaIFV", "Saad", "Saad infantry fighting vehicle", "RUS_BMP3M", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "PakistanVehicleTalhaAPC", "Talha", "Talha armored personnel carrier", "Irq_BTR90", "US_M1126", "us_m1126"),
        U("shorad", "PakistanVehicleLY80", "LY-80", "LY-80 / HQ-16 short-range SAM", "US_M6", "US_M6", "us_m6"),
        U("sam", "PakistanVehicleHQ9P", "HQ-9/P", "HQ-9/P air-defense system", "Arb_S300", "US_M1120", "us_m1120"),
        U("radar", "PakistanVehicleRadar", "IBIS-150", "IBIS-150 air-defense radar", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "PakistanVehicleA100", "A-100", "A-100 multiple rocket launcher", "RUS_BM30", "US_M270", "us_m270"),
        U("ballistic", "PakistanVehicleShaheen", "Shaheen-II", "Shaheen-II ballistic missile TEL", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "PakistanVehicleM109", "M109A2", "M109A2 self-propelled howitzer", "US_M109A7", "Arb_M109A6", "us_m109a7"),
        U("at", "PakistanVehicleBaktar", "Baktar-Shikan", "Baktar-Shikan anti-tank vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "PakistanVehicleARV", "Al-Hadeed", "Al-Hadeed armored recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "PakistanVehicleNasr", "Nasr", "Nasr short-range ballistic missile TEL", "LSFIskander", "RUS_9K720", "us_m1075"),
    ),
)

SAUDI = CountryGround(
    "SaudiArabia",
    "SaudiArabia",
    "SaudiArabia_WarFactory_T",
    "SaudiArabia_WarFactoryCommandSet",
    (
        U("mbt", "SaudiArabiaTankM1A2", "M1A2S Abrams", "Royal Saudi M1A2S Abrams main battle tank", "Arb_M1A2", "US_M1A2Sep2", "us_m1a2"),
        U("heavy", "SaudiArabiaTankM1A2S", "M1A2 Abrams", "Royal Saudi M1A2 Abrams heavy tank", "US_M1A2Sep2", "Arb_M1A2", "us_m1a2"),
        U("recon", "SaudiArabiaVehicleLAV25", "LAV-25", "LAV-25 recon vehicle", "US_M1296", "US_M1126", "us_m1126"),
        U("ifv", "SaudiArabiaVehicleM2", "M2 Bradley", "M2 Bradley infantry fighting vehicle", "US_M2A3Bskiii", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "SaudiArabiaVehicleLAV", "Tuwaiq-2", "Tuwaiq-2 8x8 armored personnel carrier", "US_M1126", "US_M1126", "us_m1126"),
        U("shorad", "SaudiArabiaVehicleAvenger", "Avenger", "M1097 Avenger short-range AA", "US_M6", "US_M6", "us_m6"),
        U("sam", "SaudiArabiaVehiclePatriot", "Patriot PAC-3", "MIM-104 Patriot PAC-3", "ABPatriot", "US_M1120", "us_m1120"),
        U("radar", "SaudiArabiaVehicleMPQ53", "AN/MPQ-53", "Patriot AN/MPQ-53 engagement radar", "US_AN_TPY2", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "SaudiArabiaVehicleASTROS", "HIMARS", "M142 HIMARS rocket launcher", "US_M270", "US_M270", "us_m270"),
        U("ballistic", "SaudiArabiaVehicleATACMS", "ATACMS", "MGM-140 ATACMS ballistic missile TEL", "US_M1075", "NAT_M142", "us_m1075"),
        U("spa", "SaudiArabiaVehicleM109", "M109A6 Paladin", "M109A6 Paladin self-propelled howitzer", "Arb_M109A6", "US_M109A7", "us_m109a7"),
        U("at", "SaudiArabiaVehicleLAVAT", "LAV-AT", "LAV-AT TOW anti-tank vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "SaudiArabiaVehicleM88", "M88 ARV", "M88 armored recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "SaudiArabiaVehiclePatriotBtry", "THAAD", "Terminal High Altitude Area Defense", "ABPatriot", "US_M1120", "us_m1120"),
    ),
)

UAE = CountryGround(
    "UAE",
    "UAE",
    "UAE_WarFactory_T",
    "UAE_WarFactoryCommandSet",
    (
        U("mbt", "UAETankLeclerc", "Leclerc UAE", "UAE Leclerc tropical main battle tank", "NAT_L2A7V", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "UAEVehicleBMP3", "BMP-3", "UAE BMP-3 infantry fighting vehicle", "RUS_BMP3M", "Arb_BMP3S", "us_m2a3"),
        U("recon", "UAEVehicleNimr", "Nimr Ajban", "Nimr Ajban scout vehicle", "US_M1296", "US_MATV", "us_m1126"),
        U("ifv", "UAEVehicleRabdan", "Rabdan", "Rabdan 8x8 infantry fighting vehicle", "NAT_VBCI", "RUS_BMP3M", "us_m2a3"),
        U("apc", "UAEVehiclePatria", "Nimr Hafeet", "Nimr Hafeet armored personnel carrier", "NAT_VBCI", "US_M1126", "us_m1126"),
        U("shorad", "UAEVehiclePantsir", "Pantsir-S1", "UAE Pantsir-S1 short-range AA", "Arb_PantsirS1", "US_M6", "us_m6"),
        U("sam", "UAEVehiclePatriot", "Patriot PAC-3", "UAE MIM-104 Patriot PAC-3", "ABPatriot", "US_M1120", "us_m1120"),
        U("radar", "UAEVehicleRadar", "AN/MPQ-65", "Patriot AN/MPQ-65 engagement radar", "US_AN_TPY2", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "UAEVehicleHIMARS", "HIMARS", "UAE M142 HIMARS rocket launcher", "NAT_M142", "US_M270", "us_m270"),
        U("ballistic", "UAEVehicleThunder", "ATACMS", "MGM-140 ATACMS ballistic missile TEL", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "UAEVehicleG6", "G6 Rhino", "G6 Rhino 155mm self-propelled howitzer", "LSFG6R", "US_M109A7", "us_m109a7"),
        U("at", "UAEVehicleBMP3AT", "BMP-3 Kornet", "BMP-3 with Kornet anti-tank missiles", "RUS_BMP3M", "US_M1128", "us_m1128"),
        U("eng", "UAEVehicleLeclercARV", "Leclerc ARV", "Leclerc armored recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "UAEVehicleJobaria", "Jobaria MLS", "Jobaria multiple launch rocket system", "US_M270", "RUS_BM30", "us_m270"),
    ),
)

VIETNAM = CountryGround(
    "Vietnam",
    "Vietnam",
    "Vietnam_WarFactory",
    "Vietnam_WarFactoryCommandSet",
    (
        U("mbt", "VietnamTankT90S", "T-90S", "Vietnamese T-90S main battle tank", "Egy_T90MS", "RUS_T90A", "us_m1a2"),
        U("heavy", "VietnamTankT54M3", "T-54M3", "T-54M3 upgraded heavy tank", "Irq_T72M1", "Irq_T72M1", "us_m1a2"),
        U("recon", "VietnamVehicleBRDM", "BRDM-2", "BRDM-2 armored recon vehicle", "US_MATV", "US_M1296", "us_m1126"),
        U("ifv", "VietnamVehicleBMP1", "BMP-2", "BMP-2 infantry fighting vehicle", "RUS_BMP3M", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "VietnamVehicleBTR80", "BTR-80", "BTR-80 armored personnel carrier", "Irq_BTR90", "US_M1126", "us_m1126"),
        U("shorad", "VietnamVehicleShilka", "ZSU-23-4", "ZSU-23-4 Shilka self-propelled AA", "LSFShilka", "US_M6", "us_m6"),
        U("sam", "VietnamVehicleS300", "S-300PMU1", "S-300PMU1 air-defense system", "Arb_S300", "US_M1120", "us_m1120"),
        U("radar", "VietnamVehicle36D6", "36D6", "36D6 air-search radar", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "VietnamVehicleBM21", "BM-21 Grad", "BM-21 Grad multiple rocket launcher", "LSFBM21", "Iraq_Bm21", "us_m270"),
        U("ballistic", "VietnamVehicleScud", "Scud-B", "Scud-B ballistic missile TEL", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "VietnamVehicle2S3", "2S3 Akatsiya", "2S3 Akatsiya self-propelled howitzer", "LSF2S19", "US_M109A7", "us_m109a7"),
        U("at", "VietnamVehicleKonkurs", "9P148 Konkurs", "9P148 Konkurs anti-tank vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "VietnamVehicleBREM", "BREM-1", "BREM-1 armored recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "VietnamVehicleBastion", "K-300P Bastion", "K-300P Bastion coastal missile launcher", "US_M1075", "RUS_9K720", "us_m1075"),
    ),
)

SYRIA = CountryGround(
    "Syria",
    "Syria",
    "Syria_WarFactory_T",
    "Syria_WarFactoryCommandSet",
    (
        U("mbt", "SyriaTankT72", "T-72", "Syrian T-72 main battle tank", "Irq_T72M1", "RUS_T90A", "us_m1a2"),
        U("heavy", "SyriaTankT62", "T-62", "Syrian T-62 heavy tank", "Irq_T72M1", "Irq_T72M1", "us_m1a2"),
        U("recon", "SyriaVehicleBRDM", "BRDM-2", "BRDM-2 armored recon vehicle", "US_MATV", "US_M1296", "us_m1126"),
        U("ifv", "SyriaVehicleBMP1", "BMP-1", "BMP-1 infantry fighting vehicle", "RUS_BMP3M", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "SyriaVehicleBTR", "BTR-80", "BTR-80 armored personnel carrier", "Irq_BTR90", "US_M1126", "us_m1126"),
        U("shorad", "SyriaVehicleShilka", "ZSU-23-4", "ZSU-23-4 Shilka self-propelled AA", "LSFShilka", "Arb_PantsirS1", "us_m6"),
        U("sam", "SyriaVehicleBuk", "Buk-M2", "Buk-M2 medium-range SAM", "Arb_S300", "US_M1120", "us_m1120"),
        U("radar", "SyriaVehicleP18", "P-18", "P-18 air-search radar", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "SyriaVehicleBM21", "BM-21 Grad", "BM-21 Grad multiple rocket launcher", "LSFBM21", "Iraq_Bm21", "us_m270"),
        U("ballistic", "SyriaVehicleScud", "Scud", "Scud ballistic missile TEL", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "SyriaVehicle2S1", "2S1 Gvozdika", "2S1 Gvozdika self-propelled howitzer", "LSF2S19", "US_M109A7", "us_m109a7"),
        U("at", "SyriaVehicleKornet", "9K135 Kornet", "9K135 Kornet anti-tank vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "SyriaVehicleBREM", "BREM-1", "BREM-1 armored recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "SyriaVehicleTOS1A", "TOS-1A", "TOS-1A Solntsepek heavy flamethrower", "RUS_TOS1A", "RUS_TOS1A", "us_m270"),
    ),
)

LIBYA = CountryGround(
    "Libya",
    "Libya",
    "Libya_WarFactory_T",
    "Libya_WarFactoryCommandSet",
    (
        U("mbt", "LibyaTankT72", "T-72", "Libyan T-72 main battle tank", "LibyanT72", "Irq_T72M1", "us_m1a2"),
        U("heavy", "LibyaTankT62", "T-62", "Libyan T-62 heavy tank", "Irq_T72M1", "Irq_T72M1", "us_m1a2"),
        U("recon", "LibyaVehicleBRDM", "EE-9 Cascavel", "EE-9 Cascavel armored recon vehicle", "US_MATV", "US_M1296", "us_m1126"),
        U("ifv", "LibyaVehicleBMP1", "BMP-1", "Libyan BMP-1 infantry fighting vehicle", "RUS_BMP3M", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "LibyaVehicleM113", "M113", "M113 armored personnel carrier", "US_M1126", "Irq_BTR90", "us_m1126"),
        U("shorad", "LibyaVehicleShilka", "ZSU-23-4", "ZSU-23-4 Shilka self-propelled AA", "LSFShilka", "US_M6", "us_m6"),
        U("sam", "LibyaVehicleSA6", "2K12 Kub", "2K12 Kub / SA-6 air-defense system", "Irq_Roland3k", "US_M1120", "us_m1120"),
        U("radar", "LibyaVehicleRadar", "P-15", "P-15 air-search radar", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "LibyaVehicleBM21", "BM-21 Grad", "BM-21 Grad multiple rocket launcher", "LSFBM21", "Iraq_Bm21", "us_m270"),
        U("ballistic", "LibyaVehicleScudB", "Scud-B", "Scud-B ballistic missile TEL", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "LibyaVehicle2S1", "2S1 Gvozdika", "2S1 Gvozdika self-propelled howitzer", "US_M109A7", "LSF2S19", "us_m109a7"),
        U("at", "LibyaVehicleATGM", "9P122 Malyutka", "9P122 Malyutka anti-tank vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "LibyaVehicleBREM", "BREM-1", "BREM-1 armored recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "LibyaVehicleScudBtry", "9K52 Luna-M", "9K52 Luna-M / FROG-7 rocket TEL", "LSFIskander", "US_M1075", "us_m1075"),
    ),
)

SOUTHAFRICA = CountryGround(
    "SouthAfrica",
    "SouthAfrica",
    "SouthAfrica_WarFactory_T",
    "SouthAfrica_WarFactoryCommandSet",
    (
        U("mbt", "SouthAfricaTankOlifant", "Olifant Mk2", "SANDF Olifant Mk2 main battle tank", "NAT_L2A7V", "Irq_T72M1", "us_m1a2"),
        U("heavy", "SouthAfricaTankOlifant1B", "Olifant Mk1B", "SANDF Olifant Mk1B heavy tank", "Irq_T72M1", "NAT_L2A7V", "us_m1a2"),
        U("recon", "SouthAfricaVehicleRooikat", "Rooikat", "Rooikat armored recon vehicle", "NAT_Cortale", "US_M1128", "us_m1128"),
        U("ifv", "SouthAfricaVehicleRatel", "Ratel", "Ratel infantry fighting vehicle", "NAT_Puma", "NAT_VBCI", "us_m2a3"),
        U("apc", "SouthAfricaVehicleCasspir", "Casspir", "Casspir armored personnel carrier", "US_M1126", "US_M1126", "us_m1126"),
        U("shorad", "SouthAfricaVehicleYstervark", "Ystervark", "Ystervark self-propelled AA", "US_M6", "US_M6", "us_m6"),
        U("sam", "SouthAfricaVehicleCactus", "Cactus", "Cactus / Crotale air-defense system", "Irq_Roland3k", "NAT_IRIST_SLM", "us_m1120"),
        U("radar", "SouthAfricaVehicleThutlwa", "Thutlwa", "ESR 220 Thutlwa air-defense radar", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "SouthAfricaVehicleValkiri", "Valkiri", "Valkiri multiple rocket launcher", "LSFBM21", "US_M270", "us_m270"),
        U("ballistic", "SouthAfricaVehicleBateleur", "Bateleur", "Bateleur 127mm multiple rocket launcher", "US_M270", "RUS_BM30", "us_m270"),
        U("spa", "SouthAfricaVehicleG6", "G6 Rhino", "G6 Rhino 155mm self-propelled howitzer", "LSFG6R", "NAT_Caesar", "us_m109a7"),
        U("at", "SouthAfricaVehicleZT3", "Ratel ZT3", "Ratel ZT3 anti-tank vehicle", "US_M1128", "NAT_Cortale", "us_m1128"),
        U("eng", "SouthAfricaVehicleARV", "Olifant ARV", "Olifant armored recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "SouthAfricaVehicleRooikat76", "Rooikat 76", "Rooikat 76mm fire-support vehicle", "NAT_Cortale", "US_M1128", "us_m1128"),
    ),
)

COUNTRIES = (
    JAPAN,
    SOUTHKOREA,
    GERMANY,
    FRANCE,
    BRITAIN,
    ITALY,
    TURKEY,
    UKRAINE,
    SWEDEN,
    INDIA,
    PAKISTAN,
    SAUDI,
    UAE,
    VIETNAM,
    SYRIA,
    LIBYA,
    SOUTHAFRICA,
)


def all_units():
    for c in COUNTRIES:
        for u in c.units:
            yield c, u
