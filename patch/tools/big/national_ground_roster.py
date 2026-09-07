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
        U("shorad", "JapanVehicleType87", "Type 87 SPAAG", "JGSDF Type 87 self-propelled AA", "LSFJP87V", "US_M6", "us_m6"),
        U("sam", "JapanVehicleChuSAM", "Type 03 Chu-SAM", "JGSDF Type 03 medium-range SAM", "NAT_IRIST_SLM", "US_M1120", "us_m1120"),
        U("radar", "JapanVehicleRadar", "JTPS Radar", "JGSDF air-search radar vehicle", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "JapanVehicleM270", "M270 MLRS", "JGSDF licensed M270 rocket launcher", "LSFJPM270", "US_M270", "us_m270"),
        U("ballistic", "JapanVehicleType12", "Type 12 SSM", "JGSDF Type 12 surface-to-ship missile", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "JapanVehicleType99", "Type 99 SPH", "JGSDF Type 99 self-propelled howitzer", "LSFJP99", "US_M109A7", "us_m109a7"),
        U("at", "JapanVehicleType16AT", "Type 16 AT", "Type 16 with anti-tank load", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "JapanVehicleType11ARV", "Type 11 ARV", "JGSDF recovery and engineering vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "JapanVehicleType12Btry", "Type 12 Battery", "Type 12 coastal missile battery", "US_M1075", "RUS_9K720", "us_m1075"),
    ),
)

SOUTHKOREA = CountryGround(
    "SouthKorea",
    "SouthKorea",
    "SouthKorea_WarFactory",
    "SouthKorea_WarFactoryCommandSet",
    (
        U("mbt", "SouthKoreaTankK1A2", "K1A2", "ROK Army K1A2 main battle tank", "LSFK1A1", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "SouthKoreaTankK1A1", "K1A1", "ROK Army K1A1 heavy tank", "LSFK1A1", "US_M1A2Sep2", "us_m1a2"),
        U("recon", "SouthKoreaVehicleK200", "K200", "ROK K200 armored recon", "US_M1126", "US_M1126", "us_m1126"),
        U("ifv", "SouthKoreaVehicleK21", "K21 IFV", "ROK K21 infantry fighting vehicle", "LSFK21", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "SouthKoreaVehicleK200APC", "K200 APC", "ROK K200 armored personnel carrier", "US_M1126", "NAT_VBCI", "us_m1126"),
        U("shorad", "SouthKoreaVehicleK30", "K30 Biho", "ROK K30 Biho self-propelled AA", "US_M6", "US_M6", "us_m6"),
        U("sam", "SouthKoreaVehicleCheongung", "Cheongung", "ROK KM-SAM Cheongung", "NAT_IRIST_SLM", "US_M1120", "us_m1120"),
        U("radar", "SouthKoreaVehicleRadar", "TPS-830K", "ROK air-defense radar vehicle", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "SouthKoreaVehicleChunmoo", "K239 Chunmoo", "ROK K239 Chunmoo MLRS", "KVChunmoo", "US_M270", "us_m270"),
        U("ballistic", "SouthKoreaVehicleHyunmoo", "Hyunmoo-2", "ROK Hyunmoo-2 ballistic TEL", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "SouthKoreaVehicleK9", "K9 Thunder", "ROK K9 self-propelled howitzer", "LSF2S19", "US_M109A7", "us_m109a7"),
        U("at", "SouthKoreaVehicleK21AT", "K21 AT", "K21 with anti-tank missiles", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "SouthKoreaVehicleK288", "K288 ARV", "ROK recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "SouthKoreaVehicleHyunmoo2B", "Hyunmoo Battery", "Hyunmoo long-range missile battery", "LSFIskander", "RUS_9K720", "us_m1075"),
    ),
)

GERMANY = CountryGround(
    "Germany",
    "Germany",
    "GermanyWarFactory",
    "GermanyWarfactoryCommandSet",
    (
        U("mbt", "GermanyTankLeopard2A7", "Leopard 2A7", "Bundeswehr Leopard 2A7", "NAT_L2A7V", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "GermanyTankLeopard2A6", "Leopard 2A6", "Bundeswehr Leopard 2A6", "NAT_L2A7V", "US_M1A2Sep2", "us_m1a2"),
        U("recon", "GermanyVehicleFennek", "Fennek", "Bundeswehr Fennek recon", "US_M1296", "US_M1296", "us_m1126"),
        U("ifv", "GermanyVehiclePuma", "Puma IFV", "Bundeswehr Puma", "NAT_Puma", "NAT_Puma", "us_m2a3"),
        U("apc", "GermanyVehicleBoxer", "Boxer", "Bundeswehr Boxer APC", "LSFBoxer", "NAT_VBCI", "us_m1126"),
        U("shorad", "GermanyVehicleGepard", "Gepard", "Bundeswehr Gepard / Skyranger", "US_M6", "US_M6", "us_m6"),
        U("sam", "GermanyVehicleIRIST", "IRIS-T SLM", "Bundeswehr IRIS-T SLM", "NAT_IRIST_SLM", "NAT_IRIST_SLM", "us_m1120"),
        U("radar", "GermanyVehicleTRML", "TRML-4D", "Bundeswehr TRML-4D radar", "NAT_TRML", "NAT_TRML", "us_an_tpy2"),
        U("mlrs", "GermanyVehicleMARS", "MARS II", "Bundeswehr MARS II / M270", "NAT_M142", "US_M270", "us_m270"),
        U("ballistic", "GermanyVehicleTaurusTEL", "Taurus TEL", "Taurus KEPD cruise-missile launcher", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "GermanyVehiclePzH2000", "PzH 2000", "Bundeswehr PzH 2000", "NAT_Caesar", "US_M109A7", "us_m109a7"),
        U("at", "GermanyVehicleWieselAT", "Wiesel TOW", "Wiesel anti-tank vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "GermanyVehicleBuffel", "BPz3 Buffel", "Bundeswehr recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "GermanyVehicleBoxerAA", "Boxer AA", "Boxer Skyranger air-defense", "LSFBoxer", "NAT_Puma", "us_m6"),
    ),
)

FRANCE = CountryGround(
    "France",
    "France",
    "FranceWarFactory",
    "FranceWarfactoryCommandSet",
    (
        U("mbt", "FranceTankLeclerc", "Leclerc", "Armee de Terre Leclerc", "NAT_L2A7V", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "FranceTankAMX30", "AMX-30B2", "AMX-30B2 Brenus", "LSFAMX30", "NAT_L2A7V", "us_m1a2"),
        U("recon", "FranceVehicleAMX10RC", "AMX-10RC", "AMX-10RC / EBRC Jaguar", "LSFamx10", "US_M1296", "us_m1126"),
        U("ifv", "FranceVehicleVBCI", "VBCI", "VBCI infantry fighting vehicle", "NAT_VBCI", "NAT_VBCI", "us_m2a3"),
        U("apc", "FranceVehicleVAB", "VAB / Griffon", "VAB / VBMR Griffon APC", "NAT_VBCI", "US_M1126", "us_m1126"),
        U("shorad", "FranceVehicleMistral", "Mistral", "Mistral / AMX-30SA short-range AA", "LSFAMX30", "US_M6", "us_m6"),
        U("sam", "FranceVehicleSAMPT", "SAMP/T", "SAMP/T Mamba air defense", "NAT_IRIST_SLM", "US_M1120", "us_m1120"),
        U("radar", "FranceVehicleGM200", "GM 200", "Ground Master 200 radar", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "FranceVehicleLRU", "LRU MLRS", "French M270 LRU", "US_M270", "US_M270", "us_m270"),
        U("ballistic", "FranceVehicleSCALPTEL", "SCALP TEL", "SCALP / MdCN launcher", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "FranceVehicleCaesar", "CAESAR", "CAESAR 155mm howitzer", "NAT_Caesar", "NAT_Caesar", "us_m109a7"),
        U("at", "FranceVehicleVABHOT", "VAB HOT", "VAB HOT / Jaguar MMP", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "FranceVehicleDNG", "Leclerc DNG", "Leclerc recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "FranceVehicleJaguar", "EBRC Jaguar", "EBRC Jaguar combat recon", "LSFamx10", "US_M1296", "us_m1128"),
    ),
)

BRITAIN = CountryGround(
    "Britain",
    "Britain",
    "BritainWarFactory",
    "BritainWarfactoryCommandSet",
    (
        U("mbt", "BritainTankChallenger2", "Challenger 2", "British Army Challenger 2", "LSFChallenger2", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "BritainTankChallenger2TES", "CR2 TES", "Challenger 2 TES heavy urban", "LSFChallenger2", "US_M1A2Sep2", "us_m1a2"),
        U("recon", "BritainVehicleAjax", "Ajax / Scimitar", "Ajax / Scimitar recon", "US_M1296", "US_M1296", "us_m1126"),
        U("ifv", "BritainVehicleWarrior", "Warrior", "FV510 Warrior IFV", "LSFWarrior", "NAT_Puma", "us_m2a3"),
        U("apc", "BritainVehicleMastiff", "Mastiff", "Mastiff / Boxer APC", "LSFBoxer", "US_M1126", "us_m1126"),
        U("shorad", "BritainVehicleStormer", "Stormer HVM", "Stormer HVM Starstreak", "US_M6", "US_M6", "us_m6"),
        U("sam", "BritainVehicleSkySabre", "Sky Sabre", "Sky Sabre air defense", "NAT_IRIST_SLM", "US_M1120", "us_m1120"),
        U("radar", "BritainVehicleGiraffe", "Giraffe", "Giraffe / Land Ceptor radar", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "BritainVehicleGMLRS", "GMLRS", "British M270 GMLRS", "US_M270", "US_M270", "us_m270"),
        U("ballistic", "BritainVehicleStormShadowTEL", "Storm Shadow TEL", "Storm Shadow launcher", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "BritainVehicleAS90", "AS90", "AS90 self-propelled gun", "LSFAS90", "US_M109A7", "us_m109a7"),
        U("at", "BritainVehicleStriker", "Striker", "FV102 Striker / Ajax AT", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "BritainVehicleCRARRV", "CRARRV", "Challenger recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "BritainVehicleTrojan", "Trojan AVRE", "Trojan combat engineer", "LSFChallenger2", "NAT_L2A7V", "us_m1a2"),
    ),
)

ITALY = CountryGround(
    "Italy",
    "Italy",
    "ItalyWarFactory",
    "ItalyWarfactoryCommandSet",
    (
        U("mbt", "ItalyTankAriete", "Ariete", "Esercito Ariete C2", "NAT_L2A7V", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "ItalyTankArieteC1", "Ariete C1", "Ariete C1 heavy tank", "NAT_L2A7V", "US_M1A2Sep2", "us_m1a2"),
        U("recon", "ItalyVehicleCentauro", "Centauro", "Centauro wheeled tank destroyer", "NAT_Cortale", "US_M1128", "us_m1128"),
        U("ifv", "ItalyVehicleDardo", "Dardo / Freccia", "Dardo / Freccia IFV", "NAT_Puma", "NAT_VBCI", "us_m2a3"),
        U("apc", "ItalyVehicleVBM", "VBM Freccia", "VBM Freccia APC", "NAT_VBCI", "US_M1126", "us_m1126"),
        U("shorad", "ItalyVehicleSIDAM", "SIDAM 25", "SIDAM 25 / Draco AA", "US_M6", "US_M6", "us_m6"),
        U("sam", "ItalyVehicleSAMPT", "SAMP/T", "Italian SAMP/T", "NAT_IRIST_SLM", "US_M1120", "us_m1120"),
        U("radar", "ItalyVehicleRAT31", "RAT-31", "RAT-31 / Kronos radar", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "ItalyVehicleM270", "M270 MLRS", "Italian M270", "US_M270", "US_M270", "us_m270"),
        U("ballistic", "ItalyVehicleStormShadowTEL", "Storm Shadow TEL", "Storm Shadow launcher", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "ItalyVehiclePzH2000", "PzH 2000", "Italian PzH 2000", "NAT_Caesar", "US_M109A7", "us_m109a7"),
        U("at", "ItalyVehicleCentauroAT", "Centauro AT", "Centauro with ATGM", "NAT_Cortale", "US_M1128", "us_m1128"),
        U("eng", "ItalyVehicleARV", "Ariete ARV", "Italian recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "ItalyVehicleCentauro2", "Centauro II", "Centauro II 120mm", "NAT_Cortale", "US_M1128", "us_m1128"),
    ),
)

TURKEY = CountryGround(
    "Turkey",
    "Turkey",
    "TurkeyWarFactory",
    "TurkeyWarfactoryCommandSet",
    (
        U("mbt", "TurkeyTankLeopard2A4", "Leopard 2A4", "TSK Leopard 2A4 / Altay stand-in", "NAT_L2A7V", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "TurkeyTankM60T", "M60T Sabra", "TSK M60T Sabra", "US_M1A2Sep2", "US_M1A2Sep2", "us_m1a2"),
        U("recon", "TurkeyVehicleKaplan", "Kaplan", "Kaplan recon / Tulpar scout", "US_M1296", "US_M1296", "us_m1126"),
        U("ifv", "TurkeyVehicleACV15", "ACV-15", "ACV-15 / Tulpar IFV", "NAT_Puma", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "TurkeyVehicleKirpi", "Kirpi / ACV", "Kirpi and ACV APC", "US_M1126", "NAT_VBCI", "us_m1126"),
        U("shorad", "TurkeyVehicleKorkut", "Korkut", "Korkut self-propelled AA", "US_M6", "US_M6", "us_m6"),
        U("sam", "TurkeyVehicleHisar", "Hisar-O", "Hisar-O medium SAM", "NAT_IRIST_SLM", "US_M1120", "us_m1120"),
        U("radar", "TurkeyVehicleKalkan", "Kalkan", "Kalkan air-defense radar", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "TurkeyVehicleKasirga", "T-300 Kasirga", "T-122 / T-300 Kasirga", "US_M270", "Iraq_Bm21", "us_m270"),
        U("ballistic", "TurkeyVehicleBora", "Bora", "Bora / Khan ballistic TEL", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "TurkeyVehicleFirtina", "T-155 Firtina", "T-155 Firtina howitzer", "US_M109A7", "NAT_Caesar", "us_m109a7"),
        U("at", "TurkeyVehicleACVTOW", "ACV TOW", "ACV-15 TOW tank destroyer", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "TurkeyVehicleM88", "M88 ARV", "M88 recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "TurkeyVehicleAltay", "Altay T1", "Altay T1 prototype tank", "NAT_L2A7V", "US_M1A2Sep2", "us_m1a2"),
    ),
)

UKRAINE = CountryGround(
    "Ukraine",
    "Ukraine",
    "UkraineWarFactory",
    "UkraineWarfactoryCommandSet",
    (
        U("mbt", "UkraineTankT84", "T-84 Oplot", "Ukrainian T-84 Oplot / T-64BV", "RUS_T90A", "RUS_T90A", "us_m1a2"),
        U("heavy", "UkraineTankT72AMT", "T-72AMT", "T-72AMT / donated Leopard 2", "Irq_T72M1", "NAT_L2A7V", "us_m1a2"),
        U("recon", "UkraineVehicleBRDM", "BRDM-2", "BRDM-2 / HMMWV recon", "US_MATV", "US_M1296", "us_m1126"),
        U("ifv", "UkraineVehicleBMP2", "BMP-2", "BMP-2 / M2 Bradley", "RUS_BMP3M", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "UkraineVehicleBTR4", "BTR-4", "BTR-4 Bucephalus", "Irq_BTR90", "US_M1126", "us_m1126"),
        U("shorad", "UkraineVehicleGepard", "Gepard / Shilka", "Gepard and ZSU-23-4", "LSFShilka", "US_M6", "us_m6"),
        U("sam", "UkraineVehicleBuk", "Buk / IRIS-T", "Buk-M1 and IRIS-T SLS", "NAT_IRIST_SLM", "RUS_S400", "us_m1120"),
        U("radar", "UkraineVehicleP18", "35D6 Radar", "35D6 / P-18 radar van", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "UkraineVehicleHIMARS", "HIMARS / Vilkha", "HIMARS and Vilkha MLRS", "NAT_M142", "US_M270", "us_m270"),
        U("ballistic", "UkraineVehicleHrim2", "Hrim-2", "Hrim-2 / Tochka-U TEL", "LSFIskander", "RUS_9K720", "us_m1075"),
        U("spa", "UkraineVehicleBohdana", "2S22 Bohdana", "2S22 Bohdana / 2S3", "LSF2S19", "US_M109A7", "us_m109a7"),
        U("at", "UkraineVehicleStugna", "Stugna-P", "Stugna-P / Javelin vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "UkraineVehicleBREM", "BREM", "Ukrainian recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "UkraineTankT64BV", "T-64BV", "T-64BV special heavy tank", "Irq_T72M1", "RUS_T90A", "us_m1a2"),
    ),
)

SWEDEN = CountryGround(
    "Sweden",
    "Sweden",
    "SwedenWarFactory",
    "SwedenWarfactoryCommandSet",
    (
        U("mbt", "SwedenTankStrv122", "Strv 122", "Stridsvagn 122 (Leopard 2S)", "strv122", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "SwedenTankStrv121", "Strv 121", "Stridsvagn 121", "strv122", "NAT_L2A7V", "us_m1a2"),
        U("recon", "SwedenVehicleCV90R", "CV90 Recon", "CV90 recce vehicle", "LSFCV90", "US_M1296", "us_m1126"),
        U("ifv", "SwedenVehicleCV90", "CV90 IFV", "Strf 90 infantry fighting vehicle", "LSFCV90", "NAT_Puma", "us_m2a3"),
        U("apc", "SwedenVehiclePatgb203", "Patgb 203", "Patgb 203 / 360 APC", "PATGB203", "NAT_VBCI", "us_m1126"),
        U("shorad", "SwedenVehicleLvkv90", "Lvkv 90", "Lvkv 90 air-defense CV90", "LSFCV90", "US_M6", "us_m6"),
        U("sam", "SwedenVehicleIRIST", "IRIS-T SLS", "IRIS-T SLS / BAMSE", "NAT_IRIST_SLM", "NAT_IRIST_SLM", "us_m1120"),
        U("radar", "SwedenVehicleGiraffe", "Giraffe AMB", "Giraffe AMB radar", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "SwedenVehiclePULS", "PULS", "PULS rocket launcher (ordered)", "US_M270", "NAT_M142", "us_m270"),
        U("ballistic", "SwedenVehicleRBS15", "RBS-15", "RBS-15 coastal missile launcher", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "SwedenVehicleArcher", "Archer", "Archer FH77BW howitzer", "NAT_Caesar", "US_M109A7", "us_m109a7"),
        U("at", "SwedenVehicleCV90AT", "CV90 AT", "CV90 with ATGM", "LSFCV90", "US_M1128", "us_m1128"),
        U("eng", "SwedenVehicleBgbv120", "Bgbv 120", "Bgbv 120 recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "SwedenTankStrv122B", "Strv 122B+", "Strv 122B+ special tank", "strv122", "NAT_L2A7V", "us_m1a2"),
    ),
)

INDIA = CountryGround(
    "India",
    "India",
    "India_WarFactory_T",
    "India_WarFactoryCommandSet",
    (
        U("mbt", "IndiaTankT90S", "T-90S Bhishma", "Indian T-90S Bhishma", "IndiaT90S", "RUS_T90A", "us_m1a2"),
        U("heavy", "IndiaTankT72Ajeya", "T-72 Ajeya", "T-72M1 Ajeya", "Irq_T72M1", "Irq_T72M1", "us_m1a2"),
        U("recon", "IndiaVehicleNAMICA", "NAMICA", "Nag missile carrier recon", "US_M1296", "US_MATV", "us_m1126"),
        U("ifv", "IndiaVehicleBMP2", "BMP-2 Sarath", "BMP-2 Sarath IFV", "RUS_BMP3M", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "IndiaVehicleKestrel", "Kestrel", "TATA Kestrel / BTR APC", "Irq_BTR90", "US_M1126", "us_m1126"),
        U("shorad", "IndiaVehicleTunguska", "2S6 Tunguska", "2S6 / ZSU-23-4 AA", "LSFShilka", "US_M6", "us_m6"),
        U("sam", "IndiaVehicleAkash", "Akash", "Akash / MR-SAM", "Arb_S300", "US_M1120", "us_m1120"),
        U("radar", "IndiaVehicleRajendra", "Rajendra", "Rajendra / Swordfish radar", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "IndiaVehiclePinaka", "Pinaka", "Pinaka MBRL", "RUS_BM30", "US_M270", "us_m270"),
        U("ballistic", "IndiaVehiclePrahaar", "Prahaar", "Prahaar / Prithvi TEL", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "IndiaVehicleK9Vajra", "K9 Vajra", "K9 Vajra-T howitzer", "LSF2S19", "US_M109A7", "us_m109a7"),
        U("at", "IndiaVehicleNag", "Nag AT", "Nag / NAMICA tank destroyer", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "IndiaVehicleVT72B", "VT-72B", "VT-72B recovery vehicle", "Irq_VT72B", "Irq_VT72B", "us_matv"),
        U("special", "IndiaTankArjun", "Arjun Mk1A", "Arjun Mk1A indigenous MBT", "NAT_L2A7V", "RUS_T90A", "us_m1a2"),
    ),
)

PAKISTAN = CountryGround(
    "Pakistan",
    "Pakistan",
    "Pakistan_WarFactory_T",
    "Pakistan_WarFactoryCommandSet",
    (
        U("mbt", "PakistanTankAlKhalid", "Al-Khalid", "Al-Khalid / VT-4 MBT", "Arb_Khalid", "RUS_T90A", "us_m1a2"),
        U("heavy", "PakistanTankAlZarrar", "Al-Zarrar", "Al-Zarrar / T-80UD", "Irq_T72M1", "Irq_T72M1", "us_m1a2"),
        U("recon", "PakistanVehicleMohafiz", "Mohafiz", "Mohafiz / Talha scout", "US_MATV", "US_M1296", "us_m1126"),
        U("ifv", "PakistanVehicleTalhaIFV", "Talha IFV", "Talha infantry fighting vehicle", "RUS_BMP3M", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "PakistanVehicleTalhaAPC", "Talha APC", "Talha armored personnel carrier", "Irq_BTR90", "US_M1126", "us_m1126"),
        U("shorad", "PakistanVehicleLY80", "LY-80", "LY-80 / HQ-16 SHORAD", "US_M6", "US_M6", "us_m6"),
        U("sam", "PakistanVehicleHQ9P", "HQ-9/P", "HQ-9/P air defense", "Arb_S300", "US_M1120", "us_m1120"),
        U("radar", "PakistanVehicleRadar", "IBIS Radar", "Chinese-supplied AD radar", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "PakistanVehicleA100", "A-100 / Azar", "A-100 and Azar MLRS", "RUS_BM30", "US_M270", "us_m270"),
        U("ballistic", "PakistanVehicleShaheen", "Shaheen / Nasr", "Shaheen and Nasr TEL", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "PakistanVehicleM109", "M109", "M109 / SH-15 howitzer", "US_M109A7", "Arb_M109A6", "us_m109a7"),
        U("at", "PakistanVehicleBaktar", "Baktar-Shikan", "Baktar-Shikan tank destroyer", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "PakistanVehicleARV", "ARV", "Pakistani recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "PakistanVehicleNasr", "Nasr Battery", "Nasr short-range ballistic battery", "LSFIskander", "RUS_9K720", "us_m1075"),
    ),
)

SAUDI = CountryGround(
    "SaudiArabia",
    "SaudiArabia",
    "SaudiArabia_WarFactory_T",
    "SaudiArabia_WarFactoryCommandSet",
    (
        U("mbt", "SaudiArabiaTankM1A2", "M1A2 Abrams", "Royal Saudi M1A2 Abrams", "Arb_M1A2", "US_M1A2Sep2", "us_m1a2"),
        U("heavy", "SaudiArabiaTankM1A2S", "M1A2S", "M1A2S Saudi variant", "US_M1A2Sep2", "Arb_M1A2", "us_m1a2"),
        U("recon", "SaudiArabiaVehicleLAV25", "LAV-25", "LAV-25 recon", "US_M1296", "US_M1126", "us_m1126"),
        U("ifv", "SaudiArabiaVehicleM2", "M2 Bradley", "M2 Bradley IFV", "US_M2A3Bskiii", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "SaudiArabiaVehicleLAV", "LAV-APC", "LAV / M113 APC", "US_M1126", "US_M1126", "us_m1126"),
        U("shorad", "SaudiArabiaVehicleAvenger", "Avenger", "Avenger / Shahine AA", "US_M6", "US_M6", "us_m6"),
        U("sam", "SaudiArabiaVehiclePatriot", "Patriot PAC-3", "MIM-104 Patriot", "ABPatriot", "US_M1120", "us_m1120"),
        U("radar", "SaudiArabiaVehicleMPQ53", "AN/MPQ-53", "Patriot engagement radar", "US_AN_TPY2", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "SaudiArabiaVehicleASTROS", "ASTROS / M270", "ASTROS II and M270", "US_M270", "US_M270", "us_m270"),
        U("ballistic", "SaudiArabiaVehicleATACMS", "ATACMS / Ababil", "ATACMS and Ababil TEL", "US_M1075", "NAT_M142", "us_m1075"),
        U("spa", "SaudiArabiaVehicleM109", "M109A6", "M109A6 Paladin", "Arb_M109A6", "US_M109A7", "us_m109a7"),
        U("at", "SaudiArabiaVehicleLAVAT", "LAV-AT", "LAV-AT TOW", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "SaudiArabiaVehicleM88", "M88 ARV", "M88 recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "SaudiArabiaVehiclePatriotBtry", "Patriot Battery", "Patriot fire unit", "ABPatriot", "US_M1120", "us_m1120"),
    ),
)

UAE = CountryGround(
    "UAE",
    "UAE",
    "UAE_WarFactory_T",
    "UAE_WarFactoryCommandSet",
    (
        U("mbt", "UAETankLeclerc", "Leclerc UAE", "UAE Leclerc tropical variant", "NAT_L2A7V", "NAT_L2A7V", "us_m1a2"),
        U("heavy", "UAEVehicleBMP3", "BMP-3", "UAE BMP-3", "RUS_BMP3M", "Arb_BMP3S", "us_m2a3"),
        U("recon", "UAEVehicleNimr", "Nimr / Rabdan", "Nimr and Rabdan scout", "US_M1296", "US_MATV", "us_m1126"),
        U("ifv", "UAEVehicleRabdan", "Rabdan IFV", "Rabdan 8x8 IFV", "NAT_VBCI", "RUS_BMP3M", "us_m2a3"),
        U("apc", "UAEVehiclePatria", "Patria APC", "Patria / Rabdan APC", "NAT_VBCI", "US_M1126", "us_m1126"),
        U("shorad", "UAEVehiclePantsir", "Pantsir-S1", "UAE Pantsir-S1", "Arb_PantsirS1", "US_M6", "us_m6"),
        U("sam", "UAEVehiclePatriot", "Patriot", "UAE Patriot / THAAD class", "ABPatriot", "US_M1120", "us_m1120"),
        U("radar", "UAEVehicleRadar", "Patriot Radar", "Patriot / THAAD radar", "US_AN_TPY2", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "UAEVehicleHIMARS", "HIMARS", "UAE HIMARS", "NAT_M142", "US_M270", "us_m270"),
        U("ballistic", "UAEVehicleThunder", "Thunder TEL", "Thunder / ATACMS launcher", "US_M1075", "US_M1075", "us_m1075"),
        U("spa", "UAEVehicleG6", "G6 / M109", "G6 Rhino and M109", "LSFG6R", "US_M109A7", "us_m109a7"),
        U("at", "UAEVehicleBMP3AT", "BMP-3 AT", "BMP-3 with Kornet", "RUS_BMP3M", "US_M1128", "us_m1128"),
        U("eng", "UAEVehicleLeclercARV", "Leclerc ARV", "Leclerc recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "UAEVehicleJobaria", "Jobaria MLS", "Jobaria multiple rocket system", "US_M270", "RUS_BM30", "us_m270"),
    ),
)

VIETNAM = CountryGround(
    "Vietnam",
    "Vietnam",
    "Vietnam_WarFactory",
    "Vietnam_WarFactoryCommandSet",
    (
        U("mbt", "VietnamTankT90S", "T-90S", "Vietnamese T-90S", "Egy_T90MS", "RUS_T90A", "us_m1a2"),
        U("heavy", "VietnamTankT54M3", "T-54M3", "T-54M3 / T-62 upgrade", "Irq_T72M1", "Irq_T72M1", "us_m1a2"),
        U("recon", "VietnamVehicleBRDM", "BRDM-2", "BRDM-2 recon", "US_MATV", "US_M1296", "us_m1126"),
        U("ifv", "VietnamVehicleBMP1", "BMP-1/2", "BMP-1 and BMP-2", "RUS_BMP3M", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "VietnamVehicleBTR80", "BTR-80", "BTR-80 / BTR-3", "Irq_BTR90", "US_M1126", "us_m1126"),
        U("shorad", "VietnamVehicleShilka", "ZSU-23-4", "ZSU-23-4 Shilka", "LSFShilka", "US_M6", "us_m6"),
        U("sam", "VietnamVehicleS300", "S-300PMU1", "S-300PMU1 / SPYDER", "Arb_S300", "US_M1120", "us_m1120"),
        U("radar", "VietnamVehicle36D6", "36D6 Radar", "36D6 air-search radar", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "VietnamVehicleBM21", "BM-21 Grad", "BM-21 Grad", "LSFBM21", "Iraq_Bm21", "us_m270"),
        U("ballistic", "VietnamVehicleScud", "Scud / K-300", "Scud and K-300P Bastion", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "VietnamVehicle2S3", "2S3 Akatsiya", "2S3 / 2S1 artillery", "LSF2S19", "US_M109A7", "us_m109a7"),
        U("at", "VietnamVehicleKonkurs", "9P148", "9P148 Konkurs", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "VietnamVehicleBREM", "BREM", "Vietnamese recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "VietnamVehicleBastion", "K-300P Bastion", "Bastion coastal missile battery", "US_M1075", "RUS_9K720", "us_m1075"),
    ),
)

SYRIA = CountryGround(
    "Syria",
    "Syria",
    "Syria_WarFactory_T",
    "Syria_WarFactoryCommandSet",
    (
        U("mbt", "SyriaTankT72", "T-72", "Syrian T-72 / T-90A", "Irq_T72M1", "RUS_T90A", "us_m1a2"),
        U("heavy", "SyriaTankT62", "T-62", "Syrian T-62", "Irq_T72M1", "Irq_T72M1", "us_m1a2"),
        U("recon", "SyriaVehicleBRDM", "BRDM-2", "BRDM-2 recon", "US_MATV", "US_M1296", "us_m1126"),
        U("ifv", "SyriaVehicleBMP1", "BMP-1", "BMP-1 IFV", "RUS_BMP3M", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "SyriaVehicleBTR", "BTR-80", "BTR-80 / BTR-152", "Irq_BTR90", "US_M1126", "us_m1126"),
        U("shorad", "SyriaVehicleShilka", "Shilka / Pantsir", "ZSU-23-4 and Pantsir", "LSFShilka", "Arb_PantsirS1", "us_m6"),
        U("sam", "SyriaVehicleBuk", "Buk / S-200", "Buk-M2 and S-200", "Arb_S300", "US_M1120", "us_m1120"),
        U("radar", "SyriaVehicleP18", "P-18 Radar", "P-18 radar van", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "SyriaVehicleBM21", "BM-21", "BM-21 Grad", "LSFBM21", "Iraq_Bm21", "us_m270"),
        U("ballistic", "SyriaVehicleScud", "Scud", "Scud / Fateh TEL", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "SyriaVehicle2S1", "2S1 / 2S3", "2S1 Gvozdika and 2S3", "LSF2S19", "US_M109A7", "us_m109a7"),
        U("at", "SyriaVehicleKornet", "Kornet", "9K135 Kornet vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "SyriaVehicleBREM", "BREM", "Syrian recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "SyriaVehicleTOS1A", "TOS-1A", "TOS-1A Solntsepek", "RUS_TOS1A", "RUS_TOS1A", "us_m270"),
    ),
)

LIBYA = CountryGround(
    "Libya",
    "Libya",
    "Libya_WarFactory_T",
    "Libya_WarFactoryCommandSet",
    (
        U("mbt", "LibyaTankT72", "T-72", "Libyan T-72", "LibyanT72", "Irq_T72M1", "us_m1a2"),
        U("heavy", "LibyaTankT62", "T-62", "Libyan T-62", "Irq_T72M1", "Irq_T72M1", "us_m1a2"),
        U("recon", "LibyaVehicleBRDM", "BRDM / EE-9", "BRDM-2 and EE-9 Cascavel", "US_MATV", "US_M1296", "us_m1126"),
        U("ifv", "LibyaVehicleBMP1", "BMP-1", "Libyan BMP-1", "RUS_BMP3M", "US_M2A3Bskiii", "us_m2a3"),
        U("apc", "LibyaVehicleM113", "M113 / BTR", "M113 and BTR APC", "US_M1126", "Irq_BTR90", "us_m1126"),
        U("shorad", "LibyaVehicleShilka", "ZSU-23-4", "ZSU-23-4 Shilka", "LSFShilka", "US_M6", "us_m6"),
        U("sam", "LibyaVehicleSA6", "SA-6 / Crotale", "2K12 Kub and Crotale", "Irq_Roland3k", "US_M1120", "us_m1120"),
        U("radar", "LibyaVehicleRadar", "Radar Van", "Libyan air-defense radar", "UVRadarVan", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "LibyaVehicleBM21", "BM-21", "BM-21 Grad", "LSFBM21", "Iraq_Bm21", "us_m270"),
        U("ballistic", "LibyaVehicleScudB", "Scud-B", "Scud-B / FROG-7 TEL", "LSFIskander", "US_M1075", "us_m1075"),
        U("spa", "LibyaVehicle2S1", "2S1 / M109", "2S1 and M109", "US_M109A7", "LSF2S19", "us_m109a7"),
        U("at", "LibyaVehicleATGM", "9K11 AT", "9K11 Malyutka vehicle", "US_M1128", "US_M1128", "us_m1128"),
        U("eng", "LibyaVehicleBREM", "BREM", "Libyan recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "LibyaVehicleScudBtry", "Scud Battery", "Scud-B battery", "LSFIskander", "US_M1075", "us_m1075"),
    ),
)

SOUTHAFRICA = CountryGround(
    "SouthAfrica",
    "SouthAfrica",
    "SouthAfrica_WarFactory_T",
    "SouthAfrica_WarFactoryCommandSet",
    (
        U("mbt", "SouthAfricaTankOlifant", "Olifant Mk2", "SANDF Olifant Mk2", "NAT_L2A7V", "Irq_T72M1", "us_m1a2"),
        U("heavy", "SouthAfricaTankOlifant1B", "Olifant Mk1B", "Olifant Mk1B", "Irq_T72M1", "NAT_L2A7V", "us_m1a2"),
        U("recon", "SouthAfricaVehicleRooikat", "Rooikat", "Rooikat armored car", "NAT_Cortale", "US_M1128", "us_m1128"),
        U("ifv", "SouthAfricaVehicleRatel", "Ratel", "Ratel IFV", "NAT_Puma", "NAT_VBCI", "us_m2a3"),
        U("apc", "SouthAfricaVehicleCasspir", "Casspir", "Casspir / Mamba APC", "US_M1126", "US_M1126", "us_m1126"),
        U("shorad", "SouthAfricaVehicleYstervark", "Ystervark", "Ystervark / Zumlac AA", "US_M6", "US_M6", "us_m6"),
        U("sam", "SouthAfricaVehicleCactus", "Cactus", "Cactus Crotale / Umkhonto", "Irq_Roland3k", "NAT_IRIST_SLM", "us_m1120"),
        U("radar", "SouthAfricaVehicleThutlwa", "Thutlwa", "ESR 220 Thutlwa radar", "NAT_TRML", "US_AN_TPY2", "us_an_tpy2"),
        U("mlrs", "SouthAfricaVehicleValkiri", "Valkiri", "Valkiri / Bateleur MLRS", "LSFBM21", "US_M270", "us_m270"),
        U("ballistic", "SouthAfricaVehicleBateleur", "Bateleur 127", "Bateleur long-range rocket (no ballistic TEL in service)", "US_M270", "RUS_BM30", "us_m270"),
        U("spa", "SouthAfricaVehicleG6", "G6 Rhino", "G6 Rhino 155mm", "LSFG6R", "NAT_Caesar", "us_m109a7"),
        U("at", "SouthAfricaVehicleZT3", "Ratel ZT3", "Ratel ZT3 tank destroyer", "US_M1128", "NAT_Cortale", "us_m1128"),
        U("eng", "SouthAfricaVehicleARV", "Olifant ARV", "Olifant recovery vehicle", "Irq_VT72B", "US_MATV", "us_matv"),
        U("special", "SouthAfricaVehicleRooikat76", "Rooikat 76", "Rooikat 76mm special", "NAT_Cortale", "US_M1128", "us_m1128"),
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
