#!/usr/bin/env python3
"""Canonical Japan / South Korea / Vietnam aircraft roster.

Aircraft are added or replaced only through these country CommandSets.
Faction CommandCenter / Dozer / VT72B chains are locked and must not change.

Each aircraft row is the four-way connection:
  CommandSet slot -> CommandButton -> Object= BuildObject -> Object INI
"""

from __future__ import annotations

from dataclasses import dataclass

LOCKED_BIG_PATHS = (
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\Science.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Tracked\Japan_VT72B.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Tracked\VT72B.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_CommandCenter.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_CommandCenter.ini",
    r"Data\INI\Object\Specter\South Korean Armed Forces\Tracked\SouthKorea_VT72B.ini",
    r"Data\INI\Object\Specter\South Korean Armed Forces\Tracked\VT72B.ini",
    r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_CommandCenter.ini",
    r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\Iraq_CommandCenter.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Tracked\Vietnam_VT72B.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Tracked\VT72B.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_CommandCenter.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_CommandCenter.ini",
)

LOCKED_COMMANDSETS = (
    "Japan_VT72BCommandSet",
    "SouthKorea_VT72BCommandSet",
    "Vietnam_VT72BCommandSet",
    "Japan_CommandCenterCommandSet",
    "SouthKorea_CommandCenterCommandSet",
    "Vietnam_CommandCenterCommandSet",
)

# Overlay files that must never be injected as extra BIG entries.
# ZH last-wins would let them overwrite CommandSet.ini.
DO_NOT_PACK_OVERLAY = (
    r"Data\INI\CommandSet_Japan.ini",
    r"Data\INI\CommandSet_SouthKorea.ini",
    r"Data\INI\CommandSet_Vietnam.ini",
)


@dataclass(frozen=True)
class Aircraft:
    slot: int
    button: str
    obj: str
    image: str
    current_model: str
    donor_art: str


@dataclass(frozen=True)
class CountryAir:
    name: str
    air_cs: str
    heavy_cs: str
    air_obj: str
    heavy_obj: str
    fighters: tuple[Aircraft, ...]
    heavy: tuple[Aircraft, ...]


JAPAN = CountryAir(
    name="Japan",
    air_cs="Japan_AirfieldCommandSet",
    heavy_cs="Japan_HeavyAirBaseCommandSet",
    air_obj="Japan_LargeAirBase",
    heavy_obj="Japan_HeavyAirBase",
    fighters=(
        Aircraft(1, "Command_ConstructJapanJetF35A", "JapanJetF35A", "SPEC_JapanJetF35A", "LSFUSAF35A", "keep LSFUSAF35A until unique JASDF F-35A stem"),
        Aircraft(2, "Command_ConstructJapanJetF35B", "JapanJetF35B", "SPEC_JapanJetF35B", "LSFUSAF35A", "keep LSFUSAF35A; do not use JP_F35B"),
        Aircraft(3, "Command_ConstructJapanJetF15J", "JapanJetF15J", "SPEC_JapanF15J", "LSFJPF15J", "ready"),
        Aircraft(4, "Command_ConstructJapanJetF15DJ", "JapanJetF15DJ", "SPEC_JapanJetF15DJ", "LSFISF15E", "PENDING unique F-15DJ stem"),
        Aircraft(5, "Command_ConstructJapanJetF2A", "JapanJetF2A", "SPEC_JapanF2A", "JPF2", "ready"),
        Aircraft(6, "Command_ConstructJapanJetF2B", "JapanJetF2B", "SPEC_JapanF2B", "AGMZJPF2G", "ready"),
        Aircraft(7, "Command_ConstructJapanJetF2Kai", "JapanJetF2Kai", "SPEC_JapanF2Kai", "LSF02TJ", "ready"),
        Aircraft(8, "Command_ConstructJapanJetF4EJKai", "JapanJetF4EJKai", "SPEC_JapanF4EJKai", "JPF4", "ready"),
        Aircraft(9, "Command_ConstructJapanJetX2Shinshin", "JapanJetX2Shinshin", "SPEC_JapanX2Shinshin", "LSFSX2", "ready"),
        Aircraft(10, "Command_ConstructJapanJetF16", "JapanJetF16", "SPEC_SouthKoreaJetF16C", "US_F16CJ_blk52", "PENDING unique JASDF F-16 stem"),
        Aircraft(11, "Command_ConstructJapanJetFA18", "JapanJetFA18", "SPEC_JapanJetFX", "US_FA18E", "PENDING unique JASDF F/A-18 stem"),
        Aircraft(12, "Command_ConstructJapanJetFX", "JapanJetFX", "SPEC_JapanJetFX", "CHAJ31HXNew", "PENDING unique FX stem"),
    ),
    heavy=(
        Aircraft(1, "Command_ConstructJapanJetE767", "JapanJetE767", "E2avionHE", "JP_E767", "ready unique JP_E767"),
        Aircraft(2, "Command_ConstructJapanJetE2D", "AmericaJetE2Visual", "E2avionHE", "AVHawk", "keep USA E-2D object / AVHawk"),
        Aircraft(3, "Command_ConstructJapanJetC2", "JapanJetC2", "SPEC_JapanC130H", "JP_C2", "ready unique JP_C2"),
        Aircraft(4, "Command_ConstructJapanJetC130H", "JapanJetC130H", "SPEC_JapanC130H", "AVCargoPln", "PENDING unique C-130 stem or keep Hercules"),
        Aircraft(5, "Command_ConstructJapanUAVRQ4", "JapanUAVRQ4", "SPEC_JapanRQ4", "US_RQ-4", "PENDING unique JASDF RQ-4 stem"),
        Aircraft(6, "Command_ConstructJapanHelicopterAH64D", "JapanHelicopterAH64D", "Nat_ah64e", "LSFJapanAH64D", "ready"),
        Aircraft(7, "Command_ConstructJapanHelicopterUH60J", "JapanHelicopterUH60J", "SSChinookUnload", "LSFJPUH60", "ready"),
        Aircraft(8, "Command_ConstructJapanHelicopterCH47J", "JapanHelicopterCH47J", "SSChinookUnload", "US_CH47F", "PENDING unique CH-47J stem"),
        Aircraft(9, "Command_ConstructJapanJetV22", "AmericaJetV22Visual", "C17GlobalMaster", "AVOsprey", "keep USA V-22 object / AVOsprey"),
    ),
)

SOUTH_KOREA = CountryAir(
    name="SouthKorea",
    air_cs="SouthKorea_AirfieldCommandSet",
    heavy_cs="SouthKorea_HeavyAirBaseCommandSet",
    air_obj="SouthKorea_LargeAirBase",
    heavy_obj="SouthKorea_HeavyAirBase",
    fighters=(
        Aircraft(1, "Command_ConstructSouthKoreaJetF35A", "SouthKoreaJetF35A", "SPEC_SouthKoreaJetF35A", "LSFUSAF35A", "keep LSFUSAF35A until unique ROKAF F-35A stem"),
        Aircraft(2, "Command_ConstructSouthKoreaJetF35B", "SouthKoreaJetF35B", "SPEC_SouthKoreaJetF35A", "LSFUSAF35A", "keep LSFUSAF35A"),
        Aircraft(3, "Command_ConstructSouthKoreaJetKF21", "SouthKoreaJetKF21", "SPEC_SouthKoreaJetKF21", "LSFJ31", "ready"),
        Aircraft(4, "Command_ConstructSouthKoreaJetF15KSlam", "SouthKoreaJetF15KSlam", "SPEC_SouthKoreaJetF15KSlam", "LSFF15K", "ready"),
        Aircraft(5, "Command_ConstructSouthKoreaJetF16C", "SouthKoreaJetF16C", "SPEC_SouthKoreaJetF16C", "LSFKF16", "ready"),
        Aircraft(6, "Command_ConstructSouthKoreaJetF16D", "SouthKoreaJetF16D", "SPEC_SouthKoreaJetF16D", "LSFKF16", "ready"),
        Aircraft(7, "Command_ConstructSouthKoreaJetFA50", "SouthKoreaJetFA50", "SPEC_SouthKoreaJetFA50", "LSFT50", "ready"),
        Aircraft(8, "Command_ConstructSouthKoreaJetFA50Blk20", "SouthKoreaJetFA50Blk20", "SPEC_SouthKoreaJetFA50", "LSFT50", "ready"),
        Aircraft(9, "Command_ConstructSouthKoreaJetT50", "SouthKoreaJetT50", "SPEC_SouthKoreaJetT50", "LSFT50", "ready"),
        Aircraft(10, "Command_ConstructSouthKoreaJetF4E", "SouthKoreaJetF4E", "SPEC_SouthKoreaJetF4E", "LSFKoreaF4", "ready"),
        Aircraft(11, "Command_ConstructSouthKoreaJetF5E", "SouthKoreaJetF5E", "SPEC_SouthKoreaJetF5E", "LSFKoreaF5", "ready"),
        Aircraft(12, "Command_ConstructSouthKoreaJetKF21Blk2", "SouthKoreaJetKF21Blk2", "SPEC_SouthKoreaJetKF21Blk2", "NVJ31", "PENDING unique KF-21 Blk2 stem"),
    ),
    heavy=(
        Aircraft(1, "Command_ConstructSouthKoreaJetE737", "SouthKoreaJetE737", "us_e3g", "KVE737", "ready unique KVE737"),
        Aircraft(2, "Command_ConstructSouthKoreaJetRC800", "SouthKoreaJetRC800", "E2avionHE", "SK_RC800", "ready unique SK_RC800"),
        Aircraft(3, "Command_ConstructSouthKoreaJetC130H", "SouthKoreaJetC130H", "SPEC_JapanC130H", "US_C130H", "PENDING unique ROKAF C-130 stem"),
        Aircraft(4, "Command_ConstructSouthKoreaJetCN235", "SouthKoreaJetCN235", "SPEC_JapanC130H", "SK_CN235", "ready unique SK_CN235"),
        Aircraft(5, "Command_ConstructSouthKoreaUAVRQ4", "AmericaUAVGlobalHawk", "SPEC_JapanRQ4", "AVReaper", "keep USA Global Hawk object"),
        Aircraft(6, "Command_ConstructSouthKoreaJetAH64E", "SouthKoreaJetAH64E", "Nat_ah64e", "US_AH64E", "PENDING unique ROKAF AH-64E stem"),
        Aircraft(7, "Command_ConstructSouthKoreaJetUH60P", "SouthKoreaJetUH60P", "us_uh60", "LSFKoreaUH60", "ready"),
        Aircraft(8, "Command_ConstructSouthKoreaHelicopterKUH1", "SouthKoreaHelicopterKUH1", "SSChinookUnload", "SK_KUH1", "ready unique SK_KUH1"),
        Aircraft(9, "Command_ConstructSouthKoreaJetCH47", "SouthKoreaJetCH47", "Nat_ch47", "US_CH47F", "PENDING unique ROKAF CH-47 stem"),
        Aircraft(10, "Command_ConstructSouthKoreaHelicopterLAH", "SouthKoreaHelicopterLAH", "Nat_ah64e", "SK_LAH", "ready unique SK_LAH"),
    ),
)

VIETNAM = CountryAir(
    name="Vietnam",
    air_cs="Vietnam_AirfieldCommandSet",
    heavy_cs="Vietnam_HeavyAirBaseCommandSet",
    air_obj="Vietnam_LargeAirBase",
    heavy_obj="Vietnam_HeavyAirBase",
    fighters=(
        Aircraft(1, "Command_ConstructVietnamJetMig29S", "VietnamJetMig29S", "LSFRUMIG29", "LSFruMiG29", "PENDING unique VPAF MiG-29 portrait; mesh LSFruMiG29"),
        Aircraft(2, "Command_ConstructVietnamJetMig21", "VietnamJetMig21", "SPEC_VietnamJetMig21", "LSFIDMig21", "PENDING unique VPAF MiG-21 stem"),
        Aircraft(3, "Command_ConstructVietnamJetSu22", "VietnamJetSu22", "SPEC_VietnamJetSu22", "Irq_SU22M3", "PENDING unique VPAF Su-22 stem; do not keep Irq_ mesh"),
        Aircraft(4, "Command_ConstructVietnamJetSu27", "VietnamJetSu27", "SPEC_VietnamJetSu27", "LSFRUSU27SK", "PENDING unique VPAF Su-27 stem"),
        Aircraft(5, "Command_ConstructVietnamJetSu30", "VietnamJetSu30", "SPEC_VietnamJetSu30", "RUS_SU30SM2", "PENDING unique VPAF Su-30 stem"),
        Aircraft(6, "Command_ConstructVietnamJetYak130", "VietnamJetYak130", "SPEC_VietnamJetYak130", "LSFT50", "PENDING unique VPAF Yak-130 stem"),
        Aircraft(7, "Command_ConstructVietnamJetF5E", "VietnamJetF5E", "SPEC_VietnamJetF5E", "AVHawk_P", "PENDING unique VPAF F-5E stem"),
    ),
    heavy=(
        Aircraft(1, "Command_ConstructVietnamJetMi8", "VietnamJetMi8", "rus_mi17", "Irq_Mi8T", "PENDING unique VPAF Mi-8 stem; do not keep Irq_ mesh"),
        Aircraft(2, "Command_ConstructVietnamJetMi17", "VietnamJetMi17", "rus_mi17", "Egy_MI17", "PENDING unique VPAF Mi-17 stem"),
        Aircraft(3, "Command_ConstructVietnamJetIL76", "VietnamJetIL76", "yier76", "Iraq_IL-76", "PENDING unique VPAF IL-76 stem; do not keep Iraq_ mesh"),
    ),
)

COUNTRIES = (JAPAN, SOUTH_KOREA, VIETNAM)


def all_aircraft():
    for country in COUNTRIES:
        for row in country.fighters:
            yield country, "air", row
        for row in country.heavy:
            yield country, "heavy", row


def commandset_text(name: str, rows: tuple[Aircraft, ...]) -> str:
    lines = [f"CommandSet {name}"]
    for row in rows:
        lines.append(f"  {row.slot} = {row.button}")
    lines.append("  13 = Command_SetRallyPoint")
    lines.append("  14 = Command_Sell")
    lines.append("End")
    return "\n".join(lines) + "\n"


def button_text(row: Aircraft) -> str:
    short = row.button[len("Command_Construct") :]
    return (
        f"CommandButton {row.button}\n"
        f"  Command       = UNIT_BUILD\n"
        f"  Object        = {row.obj}\n"
        f"  TextLabel     = CONTROLBAR:Construct{short}\n"
        f"  ButtonImage   = {row.image}\n"
        f"  ButtonBorderType = BUILD\n"
        f"  DescriptLabel = CONTROLBAR:ToolTip{short}\n"
        f"End\n"
    )


def is_iraq_name(name: str | None) -> bool:
    if not name:
        return False
    return name.startswith("Iraq") or name.startswith("Iraq_") or name.startswith("Command_ConstructIraq")
