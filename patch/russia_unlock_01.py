#!/usr/bin/env python3
"""SPECTER1 Russia unlock/scale/Su-24MR fire pass on China Unlock 01 DATA.

No ART. No airbase architecture. No unrelated countries. No donor DATA.
No sidecar CommandSets. Edit live Russian objects and original CommandSet.ini
only if a live starting bar is missing a construct button (it is not).
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/SPECTER1_CHINA_UNLOCK_01/_SPEC_DATA_ONE.big")
EXPECTED_SRC_SHA = "0bf3cc948c19ec25d89448f084bdb049dc271bf50004b08cfd0940098cd7c129"
OUT_DIR = Path("/tmp/SPECTER1_RUSSIA_UNLOCK_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_RUSSIA_UNLOCK_01")

RUS = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
P_SU34 = RUS + r"\Airforce\SU34M.ini"
P_SU24MR = RUS + r"\Airforce\Su24MR.ini"
P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_DOZER = RUS + r"\Tracked\Dozer.ini"
P_CAMP = RUS + r"\Buildings\Camp.ini"
P_WF = RUS + r"\Buildings\Warfactory.ini"
P_AIRFIELD = RUS + r"\Buildings\Airfield.ini"
P_LARGE = RUS + r"\Buildings\Russia_LargeAirBase.ini"
P_HEAVY = RUS + r"\Buildings\Russia_HeavyAirBase.ini"
P_CHINA01 = r"Data\INI\Object\Specter\PLA\China_Update_01.ini"
P_USA01 = r"Data\INI\Object\Specter\United States Of America\USA_Update_01.ini"
P_IRAQ_SU24MR = r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MR.ini"

# (path, object, producer) — live player-buildable units with tech/science/IWC gates
UNLOCK = [
    # Barracks
    (RUS + r"\Infantry\KornetTeam.ini", "RussiaInfantryKornetTeam", "RussiaBarracks"),
    (RUS + r"\Infantry\MortarTeam.ini", "RussiaInfantryMortarTeam", "RussiaBarracks"),
    (RUS + r"\Infantry\Engineer.ini", "RussiaInfantryFieldEngineer", "RussiaBarracks"),
    (RUS + r"\Infantry\SpetsNaz.ini", "RussiaInfantrySpetsNaz_A", "RussiaBarracks"),
    (RUS + r"\Infantry\Sniper.ini", "RussiaInfantryHeavySniper", "RussiaBarracks"),
    (RUS + r"\Infantry\LancetTeam.ini", "RussiaInfantryLancetTeam", "RussiaBarracks"),
    (RUS + r"\Infantry\FPVDroneOperator.ini", "RussiaInfantryDroneOperatorFPV", "RussiaBarracks"),
    (RUS + r"\Infantry\Medic.ini", "RussiaInfantryFieldMedic", "RussiaBarracks"),
    # WarFactory
    (RUS + r"\Tracked\T90A.ini", "RussiaTankT90A", "RussiaWarFactory"),
    (RUS + r"\Wheeled\Bm30.ini", "RussiaVehicleBm30", "RussiaWarFactory"),
    (RUS + r"\Wheeled\Krasukha-4.ini", "RussiaVehicleKrasukha4", "RussiaWarFactory"),
    (RUS + r"\Tracked\2S33.ini", "RussiaArtillery2S19M2", "RussiaWarFactory"),
    (RUS + r"\AirDefense\TorM2M.ini", "RussiaTankTorM2M", "RussiaWarFactory"),
    (RUS + r"\AirDefense\92N6R.ini", "RussiaVehicle92N6R", "RussiaWarFactory"),
    (RUS + r"\AirDefense\S400.ini", "RussiaVehicleS400", "RussiaWarFactory"),
    (RUS + r"\Tracked\Tos-1A.ini", "RussiaTankTos1A", "RussiaWarFactory"),
    (RUS + r"\Wheeled\9K720.ini", "RussiaVehicle9K720", "RussiaWarFactory"),
    (RUS + r"\Wheeled\RS-24_Yars.ini", "RussiaVehicleRS24", "RussiaWarFactory"),
    # Industrial Complex produced
    (RUS + r"\Tracked\2S7M.ini", "RussiaArtillery2S7M", "RussiaIndustrialComplex"),
    (RUS + r"\AirDefense\S500.ini", "RussiaVehicleS500", "RussiaIndustrialComplex"),
    (RUS + r"\AirDefense\96L6TSP.ini", "RussiaVehicle96L6TSP", "RussiaIndustrialComplex"),
    (RUS + r"\IFV\T15.ini", "RussianTankT15", "RussiaIndustrialComplex"),
    (RUS + r"\Tracked\T14.ini", "RussiaTankT14", "RussiaIndustrialComplex"),
    # CommandCenter produced
    (RUS + r"\AirDefense\9K317.ini", "RussiaVehicle9K317", "RussiaCommandCenter"),
    (RUS + r"\AirDefense\55K6E.ini", "RussiaVehicle55K6E", "RussiaCommandCenter"),
    (RUS + r"\APC\BTR82A.ini", "RussiaVehicleBTR82A", "RussiaCommandCenter"),
    # Radar station drones
    (RUS + r"\Drones\Orlan10.ini", "RussiaDroneOrlan10", "Russia91N6E"),
    (RUS + r"\Drones\Orion2.ini", "RussiaDronesOrion2", "Russia91N6E"),
    (RUS + r"\Drones\Lancet3.ini", "RussiaDroneLancet3", "Russia91N6E"),
    # Superweapon silo: keep IndustrialComplex building chain, drop Rank
    (RUS + r"\Buildings\RS28_AI.ini", "RussiaRS28NuclearMissileSilo", "RussiaIndustrialComplex"),
]

# Intended PLAYER_UPGRADE WeaponSet becomes the default Conditions=None set.
# PLAYER_UPGRADE block and WeaponSetUpgrade module are kept.
PROMOTE_LOADOUT = [
    (RUS + r"\Airforce\SU25T_SU39.ini", "RussiaJetSU25T"),
    (P_SU34, "RussiaJetSu34"),
    (RUS + r"\Airforce\Su35S_TS.ini", "RussiaJetSu35AG"),
    (RUS + r"\Airforce\SU24M2.ini", "RussiaJetSU24M2"),
    (RUS + r"\Airforce\MIG31K.ini", "RussiaJetMig31K"),
    (RUS + r"\Airforce\TU22M3M.ini", "RussiaJetTu22M3M"),
    (RUS + r"\Wheeled\Bm30.ini", "RussiaVehicleBm30"),
]

IRAQ_PROTECTED = [
    r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_MirageF1-Bq.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MK.ini",
    P_IRAQ_SU24MR,
    r"Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetL159.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini",
    r"Data\INI\Object\Specter\Iraq Army\APC\BTR90.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_LargeAirBase.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_HeavyAirBase.ini",
]
USA_PROTECTED = [
    P_USA01,
    r"Data\INI\Object\Specter\United States Of America\AmericaJetF117Clean.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaJetF18Prowler.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\F35C_AA.ini",
    r"Data\INI\Object\Specter\United States Of America\AmericaJetC17Visual.ini",
    r"Data\INI\Object\Specter\United States Of America\Buildings\Airfield.ini",
    r"Data\INI\Object\Specter\United States Of America\Buildings\America_LargeAirBase.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaHelicopterAH1Z.ini",
]
CHINA_PROTECTED = [
    P_CHINA01,
    r"Data\INI\Object\Specter\PLA\Airforce\J7.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\ChinaJetQ5.ini",
    r"Data\INI\Object\Specter\PLA\Buildings\Camp.ini",
    r"Data\INI\Object\Specter\PLA\Buildings\Warfactory.ini",
]
ARCH_PROTECTED = [P_DOZER, P_CAMP, P_WF, P_AIRFIELD, P_LARGE, P_HEAVY, P_CMDSET, P_CMDBTN]

# Live starting CommandSets already hold construct buttons. Reported for audit.
BARRACKS_UNITS = [
    ("RussiaInfantryRiflemanAK74M", "RussiaBarracks", "RussiaBarracksCommandSet", 1, RUS + r"\Infantry\Rifleman.ini"),
    ("RussiaInfantryAntitank", "RussiaBarracks", "RussiaBarracksCommandSet", 2, RUS + r"\Infantry\AntiTank.ini"),
    ("RussiaInfantryKornetTeam", "RussiaBarracks", "RussiaBarracksCommandSet", 3, RUS + r"\Infantry\KornetTeam.ini"),
    ("RussiaInfantryMortarTeam", "RussiaBarracks", "RussiaBarracksCommandSet", 4, RUS + r"\Infantry\MortarTeam.ini"),
    ("RussiaInfantryMachinegunner", "RussiaBarracks", "RussiaBarracksCommandSet", 5, RUS + r"\Infantry\Machinegunner.ini"),
    ("RussiaInfantryAntiair", "RussiaBarracks", "RussiaBarracksCommandSet", 6, RUS + r"\Infantry\AntiAir.ini"),
    ("RussiaInfantryFieldEngineer", "RussiaBarracks", "RussiaBarracksCommandSet", 7, RUS + r"\Infantry\Engineer.ini"),
    ("RussiaInfantrySpetsNaz_A", "RussiaBarracks", "RussiaBarracksCommandSet", 8, RUS + r"\Infantry\SpetsNaz.ini"),
    ("RussiaInfantryHeavySniper", "RussiaBarracks", "RussiaBarracksCommandSet", 9, RUS + r"\Infantry\Sniper.ini"),
    ("RussiaInfantryLancetTeam", "RussiaBarracks", "RussiaBarracksCommandSet", 10, RUS + r"\Infantry\LancetTeam.ini"),
    ("RussiaInfantryDroneOperatorFPV", "RussiaBarracks", "RussiaBarracksCommandSet", 11, RUS + r"\Infantry\FPVDroneOperator.ini"),
    ("RussiaInfantryFieldMedic", "RussiaBarracks", "RussiaBarracksCommandSet", 12, RUS + r"\Infantry\Medic.ini"),
]
WF_UNITS = [
    ("RussiaTankT90A", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 1, RUS + r"\Tracked\T90A.ini"),
    ("RussiaTankT72B3M", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 2, RUS + r"\Tracked\T72B3_6_16_23.ini"),
    ("RussiaVehicleBm30", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 3, RUS + r"\Wheeled\Bm30.ini"),
    ("RussiaVehicleKrasukha4", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 4, RUS + r"\Wheeled\Krasukha-4.ini"),
    ("RussiaArtillery2S19M2", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 5, RUS + r"\Tracked\2S33.ini"),
    ("RussiaTankBMP3", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 6, RUS + r"\IFV\BMP3M.ini"),
    ("RussiaTankTorM2M", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 7, RUS + r"\AirDefense\TorM2M.ini"),
    ("RussiaVehiclePantsirS1M", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 8, RUS + r"\AirDefense\Pantsir.ini"),
    ("RussiaVehicle92N6R", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 9, RUS + r"\AirDefense\92N6R.ini"),
    ("RussiaVehicleS400", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 10, RUS + r"\AirDefense\S400.ini"),
    ("RussiaTankTos1A", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 11, RUS + r"\Tracked\Tos-1A.ini"),
    ("RussiaVehicle9K720", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 12, RUS + r"\Wheeled\9K720.ini"),
    ("RussiaVehicleRS24", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 13, RUS + r"\Wheeled\RS-24_Yars.ini"),
]
AIR_UNITS = [
    ("RussiaJetSu75Checkmate", "RussiaAirfield", "RussiaAirfieldCommandSet", 1, RUS + r"\Russia_System.ini"),
    ("RussiaJetSu35S", "RussiaAirfield", "RussiaAirfieldCommandSet", 2, RUS + r"\Airforce\Su35S.ini"),
    ("RussiaJetSu30SM2", "RussiaAirfield", "RussiaAirfieldCommandSet", 3, RUS + r"\Airforce\Su30SM2.ini"),
    ("RussiaJetSU25T", "RussiaAirfield", "RussiaAirfieldCommandSet", 4, RUS + r"\Airforce\SU25T_SU39.ini"),
    ("RussiaJetSu34", "RussiaAirfield", "RussiaAirfieldCommandSet", 5, P_SU34),
    ("RussiaJetSu35AG", "RussiaAirfield", "RussiaAirfieldCommandSet", 6, RUS + r"\Airforce\Su35S_TS.ini"),
    ("RussiaJetSU24M2", "RussiaAirfield", "RussiaAirfieldCommandSet", 7, RUS + r"\Airforce\SU24M2.ini"),
    ("RussiaJetSu47Recon", "RussiaAirfield", "RussiaAirfieldCommandSet", 8, RUS + r"\Russia_System.ini"),
    ("RussiaJetMig31K", "RussiaAirfield", "RussiaAirfieldCommandSet", 9, RUS + r"\Airforce\MIG31K.ini"),
    ("RussiaJetSu24MR", "RussiaAirfield", "RussiaAirfieldCommandSet", 12, P_SU24MR),
    ("RussiaJetTu22M3M", "RussiaAirfield", "RussiaAirfieldCommandSet", 13, RUS + r"\Airforce\TU22M3M.ini"),
    ("RussiaJetSu57AA", "RussiaAirfield", "RussiaAirfieldCommandSet", 14, RUS + r"\Airforce\SU57_AA.ini"),
    ("RussiaJetSuT75", "Russia_LargeAirBase", "Russia_LargeAirBaseCommandSet", 1, RUS + r"\Airforce\SuT75.ini"),
    ("RussiaJetSu39", "Russia_LargeAirBase", "Russia_LargeAirBaseCommandSet", 10, RUS + r"\Airforce\Su39.ini"),
    ("RussiaJetSu47Berkut", "Russia_LargeAirBase", "Russia_LargeAirBaseCommandSet", 11, RUS + r"\Airforce\Su47Berkut.ini"),
    ("RussiaJetDozor600", "Russia_LargeAirBase", "Russia_LargeAirBaseCommandSet", 12, RUS + r"\Airforce\Dozor600.ini"),
    ("RussiaJetSu57Felon", "Russia_LargeAirBase", "Russia_LargeAirBaseCommandSet", 13, RUS + r"\Airforce\Su57Felon.ini"),
    ("RussiaJetSuT50PAKFA", "Russia_LargeAirBase", "Russia_LargeAirBaseCommandSet", 14, RUS + r"\Airforce\SuT50PAKFA.ini"),
    ("RussiaJetSu35Flanker", "Russia_HeavyAirBase", "Russia_HeavyAirBaseCommandSet", 3, RUS + r"\Airforce\Su35Flanker.ini"),
    ("RussiaJetTu95", "Russia_HeavyAirBase", "Russia_HeavyAirBaseCommandSet", 6, RUS + r"\Airforce\RussiaJetTu95.ini"),
    ("RussiaJetTU160", "Russia_HeavyAirBase", "Russia_HeavyAirBaseCommandSet", 7, RUS + r"\Airforce\RussiaJetTU160.ini"),
    ("RussiaJetAn225", "Russia_HeavyAirBase", "Russia_HeavyAirBaseCommandSet", 8, RUS + r"\Airforce\RussiaJetAn225.ini"),
    ("RussiaJetA50", "Russia_HeavyAirBase", "Russia_HeavyAirBaseCommandSet", 9, RUS + r"\Airforce\RussiaJetA50.ini"),
    ("RussiaJetAn124", "Russia_HeavyAirBase", "Russia_HeavyAirBaseCommandSet", 10, RUS + r"\Airforce\RussiaJetAn124.ini"),
    ("RussiaJetAvionIL76", "Russia_HeavyAirBase", "Russia_HeavyAirBaseCommandSet", 11, RUS + r"\Airforce\RussiaJetAvionIL76.ini"),
    ("RussiaJetCargoIL76", "Russia_HeavyAirBase", "Russia_HeavyAirBaseCommandSet", 12, RUS + r"\Airforce\RussiaJetCargoIL76.ini"),
    ("RussiaJetSu33", "Russia_HeavyAirBase", "Russia_HeavyAirBaseCommandSet", 13, RUS + r"\Airforce\Su33.ini"),
    ("RussiaJetSu27Flanker", "Russia_HeavyAirBase", "Russia_HeavyAirBaseCommandSet", 14, RUS + r"\Airforce\Su27Flanker.ini"),
]
HELI_UNITS = [
    ("RussiaHelicopterMi28N", "RussiaAirfield", "RussiaAirfieldCommandSet", 10, RUS + r"\Airforce\MI28N.ini"),
    ("RussiaHelicopterKA52", "RussiaAirfield", "RussiaAirfieldCommandSet", 11, RUS + r"\Airforce\KA52M.ini"),
    ("RussiaHelicopterMi8AMTSh", "RussiaSupplyCenter", "RussiaSupplyCenterCommandSet", 2, RUS + r"\Airforce\Mi8AMTSh.ini"),
]
EXTRA_UNITS = [
    ("RussiaArtillery2S7M", "RussiaIndustrialComplex", "RussiaIndsturialComplexCommandSet", 7, RUS + r"\Tracked\2S7M.ini"),
    ("RussiaVehicleS500", "RussiaIndustrialComplex", "RussiaIndsturialComplexCommandSet", 8, RUS + r"\AirDefense\S500.ini"),
    ("RussiaVehicle96L6TSP", "RussiaIndustrialComplex", "RussiaIndsturialComplexCommandSet", 9, RUS + r"\AirDefense\96L6TSP.ini"),
    ("RussianTankT15", "RussiaIndustrialComplex", "RussiaIndsturialComplexCommandSet", 11, RUS + r"\IFV\T15.ini"),
    ("RussiaTankT14", "RussiaIndustrialComplex", "RussiaIndsturialComplexCommandSet", 12, RUS + r"\Tracked\T14.ini"),
    ("RussiaVehicle9K317", "RussiaCommandCenter", "RussiaCommandCenterCommandSet", 3, RUS + r"\AirDefense\9K317.ini"),
    ("RussiaVehicle55K6E", "RussiaCommandCenter", "RussiaCommandCenterCommandSet", 4, RUS + r"\AirDefense\55K6E.ini"),
    ("RussiaVehicleBTR82A", "RussiaCommandCenter", "RussiaCommandCenterCommandSet", 10, RUS + r"\APC\BTR82A.ini"),
    ("RussiaDroneOrlan10", "Russia91N6E", "RussiaRadarStationCommandSet", 2, RUS + r"\Drones\Orlan10.ini"),
    ("RussiaDronesOrion2", "Russia91N6E", "RussiaRadarStationCommandSet", 4, RUS + r"\Drones\Orion2.ini"),
    ("RussiaDroneLancet3", "Russia91N6E", "RussiaRadarStationCommandSet", 6, RUS + r"\Drones\Lancet3.ini"),
    ("RussiaRS28NuclearMissileSilo", "RussiaIndustrialComplex", "RussiaDozerCommandSet", 8, RUS + r"\Buildings\RS28_AI.ini"),
]
PREVIOUSLY_LOCKED = [
    ("RussiaInfantryKornetTeam", "RussiaBarracks", "RussiaBarracksCommandSet", 3, "SCIENCE_Rank7+RussiaIndustrialComplex"),
    ("RussiaInfantryMortarTeam", "RussiaBarracks", "RussiaBarracksCommandSet", 4, "SCIENCE_Rank5+RussiaIndustrialComplex"),
    ("RussiaInfantryFieldEngineer", "RussiaBarracks", "RussiaBarracksCommandSet", 7, "SCIENCE_Rank4+RussiaIndustrialComplex"),
    ("RussiaInfantrySpetsNaz_A", "RussiaBarracks", "RussiaBarracksCommandSet", 8, "SCIENCE_Rank7+RussiaIndustrialComplex"),
    ("RussiaInfantryHeavySniper", "RussiaBarracks", "RussiaBarracksCommandSet", 9, "SCIENCE_Rank5+RussiaIndustrialComplex"),
    ("RussiaInfantryLancetTeam", "RussiaBarracks", "RussiaBarracksCommandSet", 10, "SCIENCE_Rank8+RussiaIndustrialComplex"),
    ("RussiaInfantryDroneOperatorFPV", "RussiaBarracks", "RussiaBarracksCommandSet", 11, "SCIENCE_Rank8+RussiaIndustrialComplex"),
    ("RussiaInfantryFieldMedic", "RussiaBarracks", "RussiaBarracksCommandSet", 12, "SCIENCE_Rank4+RussiaIndustrialComplex"),
    ("RussiaTankT90A", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 1, "SCIENCE_Rank6"),
    ("RussiaVehicleBm30", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 3, "SCIENCE_Rank5+RussiaIndustrialComplex+Upgrade_WeaponSetUpgrade"),
    ("RussiaVehicleKrasukha4", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 4, "SCIENCE_RS24+SCIENCE_Rank6+RussiaIndustrialComplex"),
    ("RussiaArtillery2S19M2", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 5, "SCIENCE_Rank3+RussiaIndustrialComplex"),
    ("RussiaTankTorM2M", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 7, "SCIENCE_Rank4+RussiaIndustrialComplex"),
    ("RussiaVehicle92N6R", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 9, "SCIENCE_Rank4"),
    ("RussiaVehicleS400", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 10, "SCIENCE_Rank4+RussiaIndustrialComplex"),
    ("RussiaTankTos1A", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 11, "SCIENCE_Rank6"),
    ("RussiaVehicle9K720", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 12, "SCIENCE_Rank7+RussiaIndustrialComplex"),
    ("RussiaVehicleRS24", "RussiaWarFactory", "RussiaWarFactoryCommandSet", 13, "SCIENCE_RS24+SCIENCE_Rank7+RussiaIndustrialComplex"),
    ("RussiaArtillery2S7M", "RussiaIndustrialComplex", "RussiaIndsturialComplexCommandSet", 7, "SCIENCE_Rank7+RussiaWarFactory"),
    ("RussiaVehicleS500", "RussiaIndustrialComplex", "RussiaIndsturialComplexCommandSet", 8, "SCIENCE_Rank4+RussiaIndustrialComplex"),
    ("RussiaVehicle96L6TSP", "RussiaIndustrialComplex", "RussiaIndsturialComplexCommandSet", 9, "SCIENCE_Rank8+RussiaIndustrialComplex"),
    ("RussianTankT15", "RussiaIndustrialComplex", "RussiaIndsturialComplexCommandSet", 11, "SCIENCE_Rank6+RussiaWarFactory"),
    ("RussiaTankT14", "RussiaIndustrialComplex", "RussiaIndsturialComplexCommandSet", 12, "SCIENCE_Rank8+RussiaWarFactory"),
    ("RussiaVehicle9K317", "RussiaCommandCenter", "RussiaCommandCenterCommandSet", 3, "SCIENCE_Rank3+RussiaIndustrialComplex"),
    ("RussiaVehicle55K6E", "RussiaCommandCenter", "RussiaCommandCenterCommandSet", 4, "SCIENCE_Rank4"),
    ("RussiaVehicleBTR82A", "RussiaCommandCenter", "RussiaCommandCenterCommandSet", 10, "RussiaIndustrialComplex+RussiaBarracks"),
    ("RussiaDroneOrlan10", "Russia91N6E", "RussiaRadarStationCommandSet", 2, "RussiaIndustrialComplex"),
    ("RussiaDronesOrion2", "Russia91N6E", "RussiaRadarStationCommandSet", 4, "SCIENCE_Rank4+RussiaIndustrialComplex"),
    ("RussiaDroneLancet3", "Russia91N6E", "RussiaRadarStationCommandSet", 6, "SCIENCE_Rank3+RussiaIndustrialComplex"),
    ("RussiaRS28NuclearMissileSilo", "RussiaIndustrialComplex", "RussiaDozerCommandSet", 8, "SCIENCE_Rank8"),
    ("RussiaJetSU25T", "RussiaAirfield", "RussiaAirfieldCommandSet", 4, "Upgrade_SU39 WeaponSet"),
    ("RussiaJetSu34", "RussiaAirfield", "RussiaAirfieldCommandSet", 5, "Upgrade_MTS WeaponSet"),
    ("RussiaJetSu35AG", "RussiaAirfield", "RussiaAirfieldCommandSet", 6, "Upgrade_MTS WeaponSet"),
    ("RussiaJetSU24M2", "RussiaAirfield", "RussiaAirfieldCommandSet", 7, "Upgrade_MTS WeaponSet"),
    ("RussiaJetMig31K", "RussiaAirfield", "RussiaAirfieldCommandSet", 9, "Upgrade_NuclearTipWarhead WeaponSet"),
    ("RussiaJetTu22M3M", "RussiaAirfield", "RussiaAirfieldCommandSet", 13, "Upgrade_MTS WeaponSet"),
]


def norm(name: str) -> str:
    return name.replace("/", "\\")


def read_big_list(path: Path) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries: list[tuple[str, bytes]] = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded_names: list[bytes] = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded_names.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded_names):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries: list[tuple[str, bytes]], target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 packed path, got {len(hits)}")
    return hits[0]


def text_of(entries, target) -> str:
    return entries[find_index(entries, target)][1].decode("utf-8", errors="replace")


def bytes_of(entries, target) -> bytes:
    return entries[find_index(entries, target)][1]


def set_text(entries, target, text: str) -> None:
    i = find_index(entries, target)
    name = entries[i][0]
    entries[i] = (name, text.encode("utf-8"))


def file_nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def to_nl(s: str, nl: str) -> str:
    return s.replace("\r\n", "\n").replace("\n", nl)


def must_replace_once(text: str, old: str, new: str, label: str) -> str:
    nl = file_nl(text)
    old = to_nl(old, nl)
    new = to_nl(new, nl)
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly 1 occurrence, got {n}; OLD={old[:180]!r}")
    return text.replace(old, new, 1)


def object_block(text: str, obj: str) -> tuple[int, int, str]:
    m = re.search(rf"^Object {re.escape(obj)}\b.*?(?=^Object |\Z)", text, re.M | re.S)
    if not m:
        raise SystemExit(f"missing Object {obj}")
    return m.start(), m.end(), m.group(0)


def unlock_object(text: str, obj: str, producer: str) -> str:
    start, end, block = object_block(text, obj)
    nl = file_nl(text)
    new_pr = to_nl(f"  Prerequisites\n    Object = {producer}\n  End", nl)
    pm = re.search(r"^  Prerequisites[^\n]*\n(?:.*\n)*?^  End", block, re.M)
    if not pm:
        raise SystemExit(f"{obj}: no Prerequisites block")
    block2 = block[: pm.start()] + new_pr + block[pm.end() :]
    block2 = re.sub(r"^  Science\s*=\s*.*\n", "", block2, flags=re.M)
    block2 = re.sub(r"^  RequiredScience\s*=\s*.*\n", "", block2, flags=re.M)
    block2 = re.sub(r"^  ForbiddenScience\s*=\s*.*\n", "", block2, flags=re.M)
    return text[:start] + block2 + text[end:]


def weaponset_blocks(block: str) -> list[re.Match[str]]:
    return list(re.finditer(r"^  WeaponSet\b[^\n]*\n(?:.*\n)*?^  End", block, re.M))


def promote_loadout(text: str, obj: str) -> str:
    start, end, block = object_block(text, obj)
    sets = weaponset_blocks(block)
    none_m = None
    upg_m = None
    for m in sets:
        body = m.group(0)
        if re.search(r"Conditions\s*=\s*PLAYER_UPGRADE\b", body):
            if upg_m is None:
                upg_m = m
            continue
        if re.search(r"Conditions\s*=\s*None\b", body, re.I) and none_m is None:
            none_m = m
    if none_m is None or upg_m is None:
        raise SystemExit(f"{obj}: need default + PLAYER_UPGRADE WeaponSet")
    upg_body = upg_m.group(0)
    # copy everything after the Conditions line from the upgrade set
    upg_lines = upg_body.splitlines(True)
    after_cond = []
    seen_cond = False
    for ln in upg_lines:
        if not seen_cond:
            if re.search(r"Conditions\s*=\s*PLAYER_UPGRADE\b", ln):
                seen_cond = True
            continue
        after_cond.append(ln)
    if not after_cond or not after_cond[-1].strip().endswith("End"):
        raise SystemExit(f"{obj}: upgrade WeaponSet parse failed")
    none_body = none_m.group(0)
    none_lines = none_body.splitlines(True)
    head = []
    seen_cond = False
    for ln in none_lines:
        head.append(ln)
        if re.search(r"Conditions\s*=\s*None\b", ln, re.I):
            seen_cond = True
            break
    if not seen_cond:
        raise SystemExit(f"{obj}: default WeaponSet has no Conditions=None")
    new_none = "".join(head + after_cond)
    if new_none == none_body:
        # already identical; still OK
        return text
    block2 = block[: none_m.start()] + new_none + block[none_m.end() :]
    # upgrade set must still exist
    if not re.search(r"Conditions\s*=\s*PLAYER_UPGRADE\b", block2):
        raise SystemExit(f"{obj}: PLAYER_UPGRADE WeaponSet lost")
    if "WeaponSetUpgrade" not in block2:
        raise SystemExit(f"{obj}: WeaponSetUpgrade module lost")
    return text[:start] + block2 + text[end:]


def science_in_prereq(block: str) -> str:
    m = re.search(r"^  Prerequisites[^\n]*\n(?:.*\n)*?^  End", block, re.M)
    if not m:
        return "NONE"
    sci = re.findall(r"^\s*Science\s*=\s*(\S+)", m.group(0), re.M)
    return ",".join(sci) if sci else "NONE"


def objects_in_prereq(block: str) -> str:
    m = re.search(r"^  Prerequisites[^\n]*\n(?:.*\n)*?^  End", block, re.M)
    if not m:
        return "NONE"
    objs = re.findall(r"^\s*Object\s*=\s*(\S+)", m.group(0), re.M)
    return ",".join(objs) if objs else "NONE"


def cmdset_block(txt: str, name: str) -> str:
    m = re.search(rf"^CommandSet {re.escape(name)}\b.*?(?=^CommandSet |\Z)", txt, re.M | re.S)
    if not m:
        raise SystemExit(f"missing CommandSet {name}")
    return m.group(0)


def unit_locked(block: str, producer: str) -> tuple[bool, str]:
    sci = science_in_prereq(block)
    prereq = objects_in_prereq(block)
    leftover_req = re.findall(r"^\s*RequiredScience\s*=\s*(\S+)", block, re.M)
    leftover_forb = re.findall(r"^\s*ForbiddenScience\s*=\s*(\S+)", block, re.M)
    extra = [x for x in prereq.split(",") if x not in ("NONE", producer, "")]
    # extra producer buildings (IWC while producing from Barracks/WF) are gates
    gated = sci != "NONE" or leftover_req or leftover_forb or extra
    gate = []
    if sci != "NONE":
        gate.append(sci)
    if leftover_req:
        gate.append("RequiredScience=" + ",".join(leftover_req))
    if extra:
        gate.append("EXTRA_OBJECT=" + ",".join(extra))
    return gated, ",".join(gate) if gate else "NONE"


def default_primary_weapon(block: str) -> str:
    for m in weaponset_blocks(block):
        body = m.group(0)
        if re.search(r"Conditions\s*=\s*PLAYER_UPGRADE\b", body):
            continue
        if re.search(r"Conditions\s*=\s*None\b", body, re.I):
            wm = re.search(r"Weapon\s*=\s*PRIMARY\s+(\S+)", body)
            return wm.group(1) if wm else "NONE"
    return "NONE"


def main() -> int:
    print("Reading China Unlock 01 DATA...")
    orig = read_big_list(SRC_DATA)
    src_sha = hashlib.sha256(SRC_DATA.read_bytes()).hexdigest()
    if src_sha != EXPECTED_SRC_SHA:
        raise SystemExit(f"baseline SHA mismatch: {src_sha}")
    entries = list(orig)

    # 1. Su-34MM scale 0.9 -> 1.03 (~+14.4%)
    su34 = text_of(entries, P_SU34)
    s0, s1, sblk = object_block(su34, "RussiaJetSu34")
    if not re.search(r"^Scale = 0\.9\s*$", sblk, re.M):
        raise SystemExit(f"Su34MM live scale not 0.9: {re.findall(r'Scale = .*', sblk)}")
    sblk2 = must_replace_once(sblk, "Scale = 0.9\n", "Scale = 1.03\n", "Su34MM scale")
    # do not touch RussiaJetSu34F
    su34 = su34[:s0] + sblk2 + su34[s1:]
    _, _, fblk = object_block(su34, "RussiaJetSu34F")
    if not re.search(r"^Scale = 0\.9\s*$", fblk, re.M):
        raise SystemExit("Su34F scale drifted")
    set_text(entries, P_SU34, su34)

    # 2. Su-24MR fire from Iraq Su-24MR (CommandSet + attack locomotor). Keep Russian model/name.
    iraq = text_of(entries, P_IRAQ_SU24MR)
    if "CommandSet             = SU24MR_CommandSet" not in iraq and "CommandSet             = SU24MR_CommandSet\r" not in iraq:
        if "SU24MR_CommandSet" not in iraq:
            raise SystemExit("Iraq Su-24MR reference CommandSet missing")
    su24 = text_of(entries, P_SU24MR)
    su24 = must_replace_once(
        su24,
        "  CommandSet        = GenericTacticalBomberCommandSet\n",
        "  CommandSet        = SU24MR_CommandSet\n",
        "RussiaJetSu24MR CommandSet",
    )
    su24 = must_replace_once(
        su24,
        "  Behavior = JetAIUpdate ModuleTag_07\n"
        "    OutOfAmmoDamagePerSecond  = 10%\n"
        "    TakeoffDistForMaxLift      = 0%\n"
        "    TakeoffPause               = 500\n"
        "    MinHeight                  = 5\n"
        "    ParkingOffset              = 3\n"
        "    ReturnToBaseIdleTime       = 10000\n"
        "  End\n",
        "  Behavior = JetAIUpdate ModuleTag_07\n"
        "    OutOfAmmoDamagePerSecond  = 10%\n"
        "    TakeoffDistForMaxLift      = 0%\n"
        "    TakeoffPause               = 500\n"
        "    MinHeight                  = 5\n"
        "    ParkingOffset              = 3\n"
        "    AttackLocomotorType        = SET_SLUGGISH\n"
        "    AttackLocomotorPersistTime = 10\n"
        "    ReturnToBaseIdleTime       = 10000\n"
        "  End\n",
        "RussiaJetSu24MR AttackLocomotor",
    )
    su24 = must_replace_once(
        su24,
        "  Locomotor = SET_NORMAL      Saturn_AL-41F\n"
        "  Locomotor = SET_TAXIING     BasicJetTaxiLocomotor\n",
        "  Locomotor = SET_NORMAL      Saturn_AL-41F\n"
        "  Locomotor = SET_SLUGGISH    Saturn_AL-41F\n"
        "  Locomotor = SET_TAXIING     BasicJetTaxiLocomotor\n",
        "RussiaJetSu24MR SET_SLUGGISH locomotor",
    )
    set_text(entries, P_SU24MR, su24)

    # 3. Unlock production gates
    for path, obj, producer in UNLOCK:
        set_text(entries, path, unlock_object(text_of(entries, path), obj, producer))

    # 4. Promote intended PLAYER_UPGRADE loadouts to default (keep upgraded sets)
    # SU34 / Bm30 already edited above/unlock; promote after those edits.
    for path, obj in PROMOTE_LOADOUT:
        set_text(entries, path, promote_loadout(text_of(entries, path), obj))

    # Architecture / other countries must be byte-identical
    for p in ARCH_PROTECTED + IRAQ_PROTECTED + USA_PROTECTED + CHINA_PROTECTED:
        if bytes_of(entries, p) != bytes_of(orig, p):
            raise SystemExit(f"protected path changed: {p}")

    orig_names = [n for n, _ in orig]
    new_names = [n for n, _ in entries]
    if new_names != orig_names:
        raise SystemExit("DATA path order/count changed")

    def changed_paths(o, n):
        om = {norm(a).lower(): (a, b) for a, b in o}
        nm = {norm(a).lower(): (a, b) for a, b in n}
        changed = [nm[k][0] for k in nm if k in om and om[k][1] != nm[k][1]]
        return changed

    d_changed = changed_paths(orig, entries)
    allowed = {norm(p).lower() for p, _, _ in UNLOCK}
    allowed.update(norm(p).lower() for p, _ in PROMOTE_LOADOUT)
    allowed.add(norm(P_SU34).lower())
    allowed.add(norm(P_SU24MR).lower())
    unrelated = []
    for p in d_changed:
        pl = p.replace("\\", "/").lower()
        if norm(p).lower() not in allowed:
            unrelated.append(p)
        elif "/iraq army/" in pl or "/united states of america/" in pl or "/pla/" in pl:
            unrelated.append(p)
    if unrelated:
        raise SystemExit(f"unrelated path changes: {unrelated}")

    # Content checks
    su34n = text_of(entries, P_SU34)
    _, _, sblk = object_block(su34n, "RussiaJetSu34")
    if "Scale = 1.03" not in sblk:
        raise SystemExit("Su34MM scale not 1.03")
    if re.search(r"^Scale = 0\.9\s*$", sblk, re.M):
        raise SystemExit("Su34MM old scale remains")
    _, _, fblk = object_block(su34n, "RussiaJetSu34F")
    if not re.search(r"^Scale = 0\.9\s*$", fblk, re.M):
        raise SystemExit("Su34F scale must stay 0.9")

    su24n = text_of(entries, P_SU24MR)
    _, _, rblk = object_block(su24n, "RussiaJetSu24MR")
    if "CommandSet        = SU24MR_CommandSet" not in rblk:
        raise SystemExit("Russia Su-24MR CommandSet not SU24MR_CommandSet")
    if "GenericTacticalBomberCommandSet" in rblk:
        raise SystemExit("Russia Su-24MR still using GenericTacticalBomberCommandSet")
    if "AttackLocomotorType        = SET_SLUGGISH" not in rblk:
        raise SystemExit("Russia Su-24MR missing AttackLocomotor")
    if "ALQ_99_RadarJamming" not in rblk:
        raise SystemExit("Russia Su-24MR lost ALQ_99")
    if "Model               = SU24MP" not in rblk:
        raise SystemExit("Russia Su-24MR model changed")
    if "DisplayName         = OBJECT:RussiaSu24MR" not in rblk:
        raise SystemExit("Russia Su-24MR name changed")
    if "Side                = Russia" not in rblk:
        raise SystemExit("Russia Su-24MR side changed")
    if "KindOf = PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT" not in rblk:
        raise SystemExit("Russia Su-24MR KindOf lost CAN_ATTACK")

    iraqn = text_of(entries, P_IRAQ_SU24MR)
    if iraqn != text_of(orig, P_IRAQ_SU24MR):
        raise SystemExit("Iraq Su-24MR changed")

    cmdset = text_of(entries, P_CMDSET)
    for setname, needle in (
        ("RussiaBarracksCommandSet", "Command_ConstructRussiaInfantryKornetTeam"),
        ("RussiaWarFactoryCommandSet", "Command_ConstructRussiaTankT90A"),
        ("RussiaAirfieldCommandSet", "Command_ConstructRussiaJetSu34"),
        ("RussiaAirfieldCommandSet", "Command_ConstructRussiaJetSu24MR"),
        ("Russia_LargeAirBaseCommandSet", "Command_ConstructRussiaJetSuT75"),
        ("Russia_HeavyAirBaseCommandSet", "Command_ConstructRussiaJetSu34"),
        ("RussiaDozerCommandSet", "Command_ConstructRussiaBarracks"),
    ):
        blk = cmdset_block(cmdset, setname)
        if needle not in blk:
            raise SystemExit(f"{setname} missing {needle}")
    if "SU24MR_CommandSet" not in cmdset:
        raise SystemExit("SU24MR_CommandSet missing from CommandSet.ini")
    alq = text_of(entries, P_CMDBTN)
    if "CommandButton Command_ALQ99_Jamming" not in alq:
        raise SystemExit("Command_ALQ99_Jamming missing")

    def rows_for(items):
        out = []
        for obj, producer, live_set, slot, path in items:
            t = text_of(entries, path)
            _, _, block = object_block(t, obj)
            gated, gate = unit_locked(block, producer)
            out.append(
                {
                    "OBJECT": obj,
                    "PRODUCER": producer,
                    "LIVE_COMMANDSET": live_set,
                    "SLOT": str(slot),
                    "NEW_GATE": gate if gated else "NONE",
                    "AVAILABLE_FROM_START": "NO" if gated else "YES",
                    "FILE": path,
                    "PRIMARY": default_primary_weapon(block),
                }
            )
        return out

    b_rows = rows_for(BARRACKS_UNITS)
    w_rows = rows_for(WF_UNITS)
    a_rows = rows_for(AIR_UNITS)
    h_rows = rows_for(HELI_UNITS)
    e_rows = rows_for(EXTRA_UNITS)
    locked_b = [r for r in b_rows if r["AVAILABLE_FROM_START"] != "YES"]
    locked_w = [r for r in w_rows if r["AVAILABLE_FROM_START"] != "YES"]
    locked_a = [r for r in a_rows if r["AVAILABLE_FROM_START"] != "YES"]
    locked_h = [r for r in h_rows if r["AVAILABLE_FROM_START"] != "YES"]
    locked_e = [r for r in e_rows if r["AVAILABLE_FROM_START"] != "YES"]
    if locked_b or locked_w or locked_a or locked_h or locked_e:
        print("LOCKED", locked_b, locked_w, locked_a, locked_h, locked_e)
        raise SystemExit("units still locked after unlock")

    # promoted loadouts must be default
    expect_primary = {
        "RussiaJetSU25T": "9A1472_Vikhr1_SU39",
        "RussiaJetSu34": "4x_GormE2GlideBomb_SU34",
        "RussiaJetSu35AG": "Kh59MK2_CruiseMissile_Su35S",
        "RussiaJetSU24M2": "2x_TVG_Kab1500Kr_Su24M2",
        "RussiaJetMig31K": "KH-47M2_ALBM_NKTWH",
        "RussiaJetTu22M3M": "KH101_CruiseMissile_TU22M3M",
        "RussiaVehicleBm30": "300mm_9M542_PGM_HE",
    }
    loadout_gate_left = 0
    for path, obj in PROMOTE_LOADOUT:
        t = text_of(entries, path)
        _, _, block = object_block(t, obj)
        prim = default_primary_weapon(block)
        if prim != expect_primary[obj]:
            raise SystemExit(f"{obj} default PRIMARY={prim} expected {expect_primary[obj]}")
        if not re.search(r"Conditions\s*=\s*PLAYER_UPGRADE\b", block):
            raise SystemExit(f"{obj} upgraded WeaponSet deleted")
        # default set must already match intended; remaining upgrade is not a production gate
    # remaining loadout production gates on live bars
    for r in b_rows + w_rows + a_rows + h_rows + e_rows:
        t = text_of(entries, r["FILE"])
        _, _, block = object_block(t, r["OBJECT"])
        # PLAYER_UPGRADE WeaponSet still present is OK; production must not require the upgrade
        if "RequiredScience" in science_in_prereq(block):
            loadout_gate_left += 1

    print("Packing DATA...")
    blob = build_big_ordered(entries)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT_DIR / "_SPEC_DATA_ONE.big"
    out_big.write_bytes(blob)
    rt = read_big_list(out_big)
    if [n for n, _ in rt] != [n for n, _ in entries]:
        raise SystemExit("round-trip name mismatch")
    if text_of(rt, P_SU34) != text_of(entries, P_SU34):
        raise SystemExit("round-trip Su34 mismatch")
    if text_of(rt, P_SU24MR) != text_of(entries, P_SU24MR):
        raise SystemExit("round-trip Su24MR mismatch")

    def format_locked_audit():
        lines = []
        path_by_obj = {}
        for items in (BARRACKS_UNITS, WF_UNITS, AIR_UNITS, HELI_UNITS, EXTRA_UNITS):
            for obj, producer, live_set, slot, path in items:
                path_by_obj[obj] = (producer, live_set, slot, path)
        for obj, producer, live_set, slot, old_gate in PREVIOUSLY_LOCKED:
            t = text_of(entries, path_by_obj[obj][3])
            _, _, block = object_block(t, obj)
            gated, gate = unit_locked(block, producer)
            lines.append(
                f"""OBJECT = {obj}
PRODUCER = {producer}
LIVE_COMMANDSET = {live_set}
SLOT = {slot}
OLD_GATE = {old_gate}
NEW_GATE = {"NONE" if not gated else gate}
AVAILABLE_FROM_START = {"NO" if gated else "YES"}
"""
            )
        return "\n".join(lines)

    audit = f"""SPECTER1 Russia unlock/scale/Su-24MR fire audit
BASELINE = China Unlock 01 DATA
BASELINE_DATA_SHA256 = {src_sha}
NEW_DATA_SHA256 = {hashlib.sha256(blob).hexdigest()}
NEW_DATA_BYTES = {len(blob)}
NEW_DATA_FILE_COUNT = {len(entries)}

RUSSIA_SU34MM_OBJECT = RussiaJetSu34
RUSSIA_SU34MM_OLD_SCALE = 0.9
RUSSIA_SU34MM_NEW_SCALE = 1.03
RUSSIA_SU34MM_SCALE_CHANGED = YES

RUSSIA_SU24MR_OBJECT = RussiaJetSu24MR
IRAQ_SU24MR_REFERENCE_OBJECT = Iraq_Su-24MR
IRAQ_SU24MR_REFERENCE_WEAPON = ALQ_99_RadarJamming
RUSSIA_SU24MR_FIRE_FIXED = YES
RUSSIA_SU24MR_REFERENCE_USED = IRAQ_SU24MR
RUSSIA_SU24MR_CAN_ATTACK = YES
RUSSIA_SU24MR_COMMANDSET = SU24MR_CommandSet
RUSSIA_SU24MR_FIRE_BUTTON = Command_ALQ99_Jamming

RUSSIA_BARRACKS_LOCKED_UNIT_COUNT = {len(locked_b)}
RUSSIA_WARFACTORY_LOCKED_UNIT_COUNT = {len(locked_w)}
RUSSIA_AIRCRAFT_LOCKED_UNIT_COUNT = {len(locked_a)}
RUSSIA_HELICOPTER_LOCKED_UNIT_COUNT = {len(locked_h)}
RUSSIA_WEAPON_LOADOUT_UPGRADE_GATE_COUNT = {loadout_gate_left}

PREVIOUS_IRAQ_CHANGES_PRESERVED = YES
PREVIOUS_USA_CHANGES_PRESERVED = YES
PREVIOUS_CHINA_CHANGES_PRESERVED = YES
UNRELATED_COUNTRY_CHANGED_PATH_COUNT = {len(unrelated)}
AIRBASE_ARCHITECTURE_CHANGED = NO
ART_CHANGED = NO
DONOR_DATA_USED = NO
COMMANDSET_INI_CHANGED = NO
SIDECAR_COMMANDSET_CREATED = NO

DATA_CHANGED_PATHS =
{chr(10).join('  ' + p for p in d_changed)}

=== PREVIOUSLY LOCKED PLAYABLE RUSSIAN ITEMS ===
{format_locked_audit()}
"""
    changelog = """SPECTER1 Russia unlock / Su-34MM scale / Su-24MR fire (DATA only)

Baseline: SPECTER1_CHINA_UNLOCK_01 DATA. Iraq, USA, and China packed files unchanged. No ART. No Release.

1. RussiaJetSu34 (Su-34MM) visual Scale 0.9 -> 1.03 (~+14.4%). Model/weapons/locomotor/armor/price/slot/producer unchanged. RussiaJetSu34F untouched.
2. RussiaJetSu24MR FIRE: keep Russian model/name/producer/side. Switch unit CommandSet GenericTacticalBomberCommandSet -> SU24MR_CommandSet (Iraq working Command_ALQ99_Jamming + ALQ_99_RadarJamming PRIMARY). Add AttackLocomotorType SET_SLUGGISH like Iraq. Iraq_Su-24MR.ini not edited.
3. Live Russian production gates (Science/Rank/IWC/RS24) stripped from player-buildable units. Starting live CommandSets already held construct buttons; CommandSet.ini not rewritten.
4. Intended PLAYER_UPGRADE aircraft/Bm30 loadouts copied onto Conditions=None. Upgraded WeaponSets and WeaponSetUpgrade modules kept.
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    print(audit)
    print("WROTE", out_big, len(blob))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
