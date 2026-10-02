#!/usr/bin/env python3
"""National WMD completion — patch missing factions only.

DATA only. Preserves packed BIG entry order.
Does not touch Science, CommandCenter, VT72B, or airfield buildings.
PlayerTemplate is edited only on SpecialPowerShortcutCommandSet lines so
unique national WMD can appear instead of shared NATO/NK/Pakistan bars.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/usa_jp_visual_buttons/_SPEC_DATA_ONE.big")
OUT_DIR = Path("/tmp/national_wmd")

RELOAD = "1200000"

LOCKED_PATHS = {
    r"data\ini\science.ini",
    r"data\ini\object\specter\japan self-defense forces\tracked\japan_vt72b.ini",
    r"data\ini\object\specter\japan self-defense forces\tracked\vt72b.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\japan_commandcenter.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\iraq_commandcenter.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\japan_airfield.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\japan_largeairbase.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\japan_heavyairbase.ini",
}

LOCKED_COMMANDSETS = (
    "Japan_VT72BCommandSet",
    "SouthKorea_VT72BCommandSet",
    "Vietnam_VT72BCommandSet",
    "Japan_CommandCenterCommandSet",
    "SouthKorea_CommandCenterCommandSet",
    "Vietnam_CommandCenterCommandSet",
    "SouthKorea_AirfieldCommandSet",
    "SouthKorea_HeavyAirBaseCommandSet",
    "Vietnam_AirfieldCommandSet",
    "Vietnam_HeavyAirBaseCommandSet",
    "Japan_AirfieldCommandSet",
    "Japan_HeavyAirBaseCommandSet",
)

# Surgical PlayerTemplate shortcut remaps only.
PLAYERTEMPLATE_SHORTCUTS = {
    "FactionPakistan": "SpecialPowerShortcutPakistan",
    "FactionSaudiArabia": "SpecialPowerShortcutSaudiArabia",
    "FactionUAE": "SpecialPowerShortcutUAE",
    "FactionIndia": "SpecialPowerShortcutIndia",
    "FactionSyria": "SpecialPowerShortcutSyria",
    "FactionGermany": "SpecialPowerShortcutGermanyCommandSet",
    "FactionFrance": "SpecialPowerShortcutFranceCommandSet",
    "FactionBritain": "SpecialPowerShortcutBritainCommandSet",
    "FactionItaly": "SpecialPowerShortcutItalyCommandSet",
    "FactionSweden": "SpecialPowerShortcutSwedenCommandSet",
    "FactionUkraine": "SpecialPowerShortcutUkraineCommandSet",
    "FactionTurkey": "SpecialPowerShortcutTurkeyCommandSet",
    "FactionLibya": "SpecialPowerShortcutLibya",
    "FactionSouthAfrica": "SpecialPowerShortcutSouthAfrica",
    "FactionSouthKorea": "SpecialPowerShortcutSouthKorea",
    "FactionJapan": "SpecialPowerShortcutJapan",
    "FactionVietnam": "SpecialPowerShortcutVietnam",
}

SYSTEM_FILES = {
    "AmericaSystemSpecialPowerShortcut": r"Data\INI\Object\Specter\United States Of America\USA_System.ini",
    "RussiaSystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Russia_System.ini",
    "ChinaSystemSpecialPowerShortcut": r"Data\INI\Object\Specter\PLA\China_System.ini",
    "IsraelSystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Israel Defense Forces\Israel_Systems.ini",
    "NorthKoreaSystemSpecialPowerShortcut": r"Data\INI\Object\Specter\North Korea\NorthKorea_Systems.ini",
    "IranSystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Iranian Army\Iran_System.ini",
    "BritainSystemSpecialPowerShortcut": r"Data\INI\Object\Specter\British Armed Forces\Nato_Systems.ini",
    "FranceSystemSpecialPowerShortcut": r"Data\INI\Object\Specter\French Armed Forces\Nato_Systems.ini",
    "India_SystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Indian Armed Forces\India_Systems.ini",
    "Pakistan_SystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Pakistan Armed Forces\Pakistan_Systems.ini",
    "JapanSystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Japan_Systems.ini",
    "GermanySystemSpecialPowerShortcut": r"Data\INI\Object\Specter\German Armed Forces\Nato_Systems.ini",
    "SouthKoreaSystemSpecialPowerShortcut": r"Data\INI\Object\Specter\South Korean Armed Forces\SouthKorea_Systems.ini",
    "TurkeySystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Turkish Armed Forces\Nato_Systems.ini",
    "ItalySystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Italian Armed Forces\Nato_Systems.ini",
    "Egypt_SystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Egyptian Armed Forces\Egypt_Systems.ini",
    "VietnamSystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Vietnam_Systems.ini",
    "SaudiArabia_SystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\SaudiArabia_Systems.ini",
    "UAE_SystemSpecialPowerShortcut": r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\UAE_Systems.ini",
    "UkraineSystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Ukrainian Armed Forces\Nato_Systems.ini",
    "Syria_SystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Syrian Armed Forces\Syria_Systems.ini",
    "Libya_SystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Libyan Armed Forces\Libya_Systems.ini",
    "SouthAfrica_SystemSpecialPowerShortcut": r"Data\INI\Object\Specter\South African National Defence Force\SouthAfrica_Systems.ini",
    "SwedenSystemSpecialPowerShortcut": r"Data\INI\Object\Specter\Swedish Armed Forces\Nato_Systems.ini",
}

SYSTEM_COMMANDSET = {
    "BritainSystemSpecialPowerShortcut": "SpecialPowerShortcutBritainCommandSet",
    "FranceSystemSpecialPowerShortcut": "SpecialPowerShortcutFranceCommandSet",
    "GermanySystemSpecialPowerShortcut": "SpecialPowerShortcutGermanyCommandSet",
    "ItalySystemSpecialPowerShortcut": "SpecialPowerShortcutItalyCommandSet",
    "SwedenSystemSpecialPowerShortcut": "SpecialPowerShortcutSwedenCommandSet",
    "UkraineSystemSpecialPowerShortcut": "SpecialPowerShortcutUkraineCommandSet",
    "TurkeySystemSpecialPowerShortcut": "SpecialPowerShortcutTurkeyCommandSet",
    "JapanSystemSpecialPowerShortcut": "SpecialPowerShortcutJapan",
    "SouthKoreaSystemSpecialPowerShortcut": "SpecialPowerShortcutSouthKorea",
    "VietnamSystemSpecialPowerShortcut": "SpecialPowerShortcutVietnam",
    "Pakistan_SystemSpecialPowerShortcut": "SpecialPowerShortcutPakistan",
}

# kind: nuke | missile | chem | bio
POWERS = [
    # existing nuclear — reload/enum only
    ("AmericaSpecialPowerLGM30G", "nuke", True, "USA LGM-30 Minuteman"),
    ("RussiaSpecialPowerRS28", "nuke", True, "Russia RS-28 Sarmat"),
    ("ChinaSpecialPowerDF5C", "nuke", True, "China DF-5C"),
    ("IsraelSpecialPowerJerichoIII", "nuke", True, "Israel Jericho III"),
    ("NorthKorea_NuclearMissile", "nuke", True, "North Korea nuclear missile"),
    # new nuclear
    ("BritainSpecialPowerTrident", "nuke", False, "UK Trident II D5"),
    ("FranceSpecialPowerM51", "nuke", False, "France M51"),
    ("IndiaSpecialPowerAgniV", "nuke", False, "India Agni-V"),
    ("PakistanSpecialPowerShaheenIII", "nuke", False, "Pakistan Shaheen-III"),
    # existing conventional
    ("Iran_SejjilMissile", "missile", True, "Khorramshahr Ballistic Missile"),
    # new conventional / chem / bio
    ("Iran_ChemicalStrike", "chem", False, "Chemical Strike"),
    ("Iran_BiologicalWeapon", "bio", False, "Biological Weapon"),
    ("Japan_Type12Missile", "missile", False, "Type-12 Missile"),
    ("Japan_ChemicalDefense", "chem", False, "Chemical Defense"),
    ("Germany_TaurusMissile", "missile", False, "Taurus Missile"),
    ("Germany_ChemicalStrike", "chem", False, "Chemical Strike"),
    ("SouthKorea_HyunmooMissile", "missile", False, "Hyunmoo Missile"),
    ("SouthKorea_BiologicalWeapon", "bio", False, "Biological Weapon"),
    ("Turkey_BoraMissile", "missile", False, "Bora Missile"),
    ("Turkey_ChemicalStrike", "chem", False, "Chemical Strike"),
    ("Italy_StormShadowMissile", "missile", False, "Storm Shadow Missile"),
    ("Italy_BiologicalWeapon", "bio", False, "Biological Weapon"),
    ("Egypt_ScudDMissile", "missile", False, "Scud-D Missile"),
    ("Egypt_ChemicalStrike", "chem", False, "Chemical Strike"),
    ("Vietnam_K300Missile", "missile", False, "K-300 Missile"),
    ("Vietnam_BiologicalWeapon", "bio", False, "Biological Weapon"),
    ("SaudiArabia_AbabilMissile", "missile", False, "Ababil Ballistic Missile"),
    ("SaudiArabia_ChemicalStrike", "chem", False, "Chemical Strike"),
    ("UAE_ThunderMissile", "missile", False, "Thunder Missile System"),
    ("UAE_BiologicalWeapon", "bio", False, "Biological Weapon"),
    ("Ukraine_Hrim2Missile", "missile", False, "Hrim-2 Ballistic Missile"),
    ("Ukraine_ChemicalStrike", "chem", False, "Chemical Strike"),
    ("Syria_ScudMissile", "missile", False, "Scud Missile"),
    ("Syria_ChemicalStrike", "chem", False, "Chemical Strike"),
    ("Libya_ScudBMissile", "missile", False, "Scud-B Missile"),
    ("Libya_BiologicalWeapon", "bio", False, "Biological Weapon"),
    ("SouthAfrica_RaptorMissile", "missile", False, "Raptor Precision Missile"),
    ("SouthAfrica_ChemicalStrike", "chem", False, "Chemical Strike"),
    ("Sweden_RBS15Missile", "missile", False, "RBS-15 Missile"),
    ("Sweden_BiologicalDefense", "bio", False, "Biological Defense Weapon"),
]

KIND_ENUM = {
    "nuke": "SPECIAL_NEUTRON_MISSILE",
    "missile": "SPECIAL_SCUD_STORM",
    "chem": "SPECIAL_SCUD_STORM",
    "bio": "SPECIAL_ANTHRAX_BOMB",
}
KIND_OCL = {
    "nuke": "SUPERWEAPON_AmericaLGM30G",
    "missile": "SUPERWEAPON_SejjilAttack",
    "chem": "SUPERWEAPON_Arab_Jarrah",
    "bio": "SUPERWEAPON_AnthraxBomb",
}
KIND_IMAGE = {
    "nuke": "SNNukeLaunch",
    "missile": "irq_abbas",
    "chem": "SSScudStorm",
    "bio": "arb_abubaker",
}
KIND_CURSOR = {
    "nuke": "NUCLEARMISSILE",
    "missile": "SCUDSTORM",
    "chem": "SCUDSTORM",
    "bio": "DAISYCUTTER",
}

BUTTONS = [
    # existing nuclear shortcuts stay; new / replacement buttons below
    ("Command_LaunchBritainTridentFromShortcut", "BritainSpecialPowerTrident", "nuke",
     "CONTROLBAR:BritainTrident", "CONTROLBAR:TooltipBritainTrident"),
    ("Command_LaunchFranceM51FromShortcut", "FranceSpecialPowerM51", "nuke",
     "CONTROLBAR:FranceM51", "CONTROLBAR:TooltipFranceM51"),
    ("Command_LaunchIndiaAgniVFromShortcut", "IndiaSpecialPowerAgniV", "nuke",
     "CONTROLBAR:IndiaAgniV", "CONTROLBAR:TooltipIndiaAgniV"),
    ("Command_LaunchPakistanShaheenFromShortcut", "PakistanSpecialPowerShaheenIII", "nuke",
     "CONTROLBAR:PakistanShaheenIII", "CONTROLBAR:TooltipPakistanShaheenIII"),
    ("Command_LaunchIranChemicalFromShortcut", "Iran_ChemicalStrike", "chem",
     "CONTROLBAR:IranChemicalStrike", "CONTROLBAR:TooltipIranChemicalStrike"),
    ("Command_LaunchIranBiologicalFromShortcut", "Iran_BiologicalWeapon", "bio",
     "CONTROLBAR:IranBiologicalWeapon", "CONTROLBAR:TooltipIranBiologicalWeapon"),
    ("Command_LaunchJapanType12FromShortcut", "Japan_Type12Missile", "missile",
     "CONTROLBAR:JapanType12Missile", "CONTROLBAR:TooltipJapanType12Missile"),
    ("Command_LaunchJapanChemicalDefenseFromShortcut", "Japan_ChemicalDefense", "chem",
     "CONTROLBAR:JapanChemicalDefense", "CONTROLBAR:TooltipJapanChemicalDefense"),
    ("Command_LaunchGermanyTaurusFromShortcut", "Germany_TaurusMissile", "missile",
     "CONTROLBAR:GermanyTaurusMissile", "CONTROLBAR:TooltipGermanyTaurusMissile"),
    ("Command_LaunchGermanyChemicalFromShortcut", "Germany_ChemicalStrike", "chem",
     "CONTROLBAR:GermanyChemicalStrike", "CONTROLBAR:TooltipGermanyChemicalStrike"),
    ("Command_LaunchSouthKoreaHyunmooFromShortcut", "SouthKorea_HyunmooMissile", "missile",
     "CONTROLBAR:SouthKoreaHyunmooMissile", "CONTROLBAR:TooltipSouthKoreaHyunmooMissile"),
    ("Command_LaunchSouthKoreaBiologicalFromShortcut", "SouthKorea_BiologicalWeapon", "bio",
     "CONTROLBAR:SouthKoreaBiologicalWeapon", "CONTROLBAR:TooltipSouthKoreaBiologicalWeapon"),
    ("Command_LaunchTurkeyBoraFromShortcut", "Turkey_BoraMissile", "missile",
     "CONTROLBAR:TurkeyBoraMissile", "CONTROLBAR:TooltipTurkeyBoraMissile"),
    ("Command_LaunchTurkeyChemicalFromShortcut", "Turkey_ChemicalStrike", "chem",
     "CONTROLBAR:TurkeyChemicalStrike", "CONTROLBAR:TooltipTurkeyChemicalStrike"),
    ("Command_LaunchItalyStormShadowFromShortcut", "Italy_StormShadowMissile", "missile",
     "CONTROLBAR:ItalyStormShadowMissile", "CONTROLBAR:TooltipItalyStormShadowMissile"),
    ("Command_LaunchItalyBiologicalFromShortcut", "Italy_BiologicalWeapon", "bio",
     "CONTROLBAR:ItalyBiologicalWeapon", "CONTROLBAR:TooltipItalyBiologicalWeapon"),
    ("Command_LaunchEgyptScudDFromShortcut", "Egypt_ScudDMissile", "missile",
     "CONTROLBAR:EgyptScudDMissile", "CONTROLBAR:TooltipEgyptScudDMissile"),
    ("Command_LaunchEgyptChemicalFromShortcut", "Egypt_ChemicalStrike", "chem",
     "CONTROLBAR:EgyptChemicalStrike", "CONTROLBAR:TooltipEgyptChemicalStrike"),
    ("Command_LaunchVietnamK300FromShortcut", "Vietnam_K300Missile", "missile",
     "CONTROLBAR:VietnamK300Missile", "CONTROLBAR:TooltipVietnamK300Missile"),
    ("Command_LaunchVietnamBiologicalFromShortcut", "Vietnam_BiologicalWeapon", "bio",
     "CONTROLBAR:VietnamBiologicalWeapon", "CONTROLBAR:TooltipVietnamBiologicalWeapon"),
    ("Command_LaunchSaudiAbabilFromShortcut", "SaudiArabia_AbabilMissile", "missile",
     "CONTROLBAR:SaudiAbabilMissile", "CONTROLBAR:TooltipSaudiAbabilMissile"),
    ("Command_LaunchSaudiChemicalFromShortcut", "SaudiArabia_ChemicalStrike", "chem",
     "CONTROLBAR:SaudiChemicalStrike", "CONTROLBAR:TooltipSaudiChemicalStrike"),
    ("Command_LaunchUAEThunderFromShortcut", "UAE_ThunderMissile", "missile",
     "CONTROLBAR:UAEThunderMissile", "CONTROLBAR:TooltipUAEThunderMissile"),
    ("Command_LaunchUAEBiologicalFromShortcut", "UAE_BiologicalWeapon", "bio",
     "CONTROLBAR:UAEBiologicalWeapon", "CONTROLBAR:TooltipUAEBiologicalWeapon"),
    ("Command_LaunchUkraineHrim2FromShortcut", "Ukraine_Hrim2Missile", "missile",
     "CONTROLBAR:UkraineHrim2Missile", "CONTROLBAR:TooltipUkraineHrim2Missile"),
    ("Command_LaunchUkraineChemicalFromShortcut", "Ukraine_ChemicalStrike", "chem",
     "CONTROLBAR:UkraineChemicalStrike", "CONTROLBAR:TooltipUkraineChemicalStrike"),
    ("Command_LaunchSyriaScudFromShortcut", "Syria_ScudMissile", "missile",
     "CONTROLBAR:SyriaScudMissile", "CONTROLBAR:TooltipSyriaScudMissile"),
    ("Command_LaunchSyriaChemicalFromShortcut", "Syria_ChemicalStrike", "chem",
     "CONTROLBAR:SyriaChemicalStrike", "CONTROLBAR:TooltipSyriaChemicalStrike"),
    ("Command_LaunchLibyaScudBFromShortcut", "Libya_ScudBMissile", "missile",
     "CONTROLBAR:LibyaScudBMissile", "CONTROLBAR:TooltipLibyaScudBMissile"),
    ("Command_LaunchLibyaBiologicalFromShortcut", "Libya_BiologicalWeapon", "bio",
     "CONTROLBAR:LibyaBiologicalWeapon", "CONTROLBAR:TooltipLibyaBiologicalWeapon"),
    ("Command_LaunchSouthAfricaRaptorFromShortcut", "SouthAfrica_RaptorMissile", "missile",
     "CONTROLBAR:SouthAfricaRaptorMissile", "CONTROLBAR:TooltipSouthAfricaRaptorMissile"),
    ("Command_LaunchSouthAfricaChemicalFromShortcut", "SouthAfrica_ChemicalStrike", "chem",
     "CONTROLBAR:SouthAfricaChemicalStrike", "CONTROLBAR:TooltipSouthAfricaChemicalStrike"),
    ("Command_LaunchSwedenRBS15FromShortcut", "Sweden_RBS15Missile", "missile",
     "CONTROLBAR:SwedenRBS15Missile", "CONTROLBAR:TooltipSwedenRBS15Missile"),
    ("Command_LaunchSwedenBiologicalDefenseFromShortcut", "Sweden_BiologicalDefense", "bio",
     "CONTROLBAR:SwedenBiologicalDefense", "CONTROLBAR:TooltipSwedenBiologicalDefense"),
]

SYSTEM_POWERS = {
    "AmericaSystemSpecialPowerShortcut": ["AmericaSpecialPowerLGM30G"],
    "RussiaSystemSpecialPowerShortcut": ["RussiaSpecialPowerRS28"],
    "ChinaSystemSpecialPowerShortcut": ["ChinaSpecialPowerDF5C"],
    "IsraelSystemSpecialPowerShortcut": ["IsraelSpecialPowerJerichoIII"],
    "NorthKoreaSystemSpecialPowerShortcut": ["NorthKorea_NuclearMissile"],
    "IranSystemSpecialPowerShortcut": ["Iran_SejjilMissile", "Iran_ChemicalStrike", "Iran_BiologicalWeapon"],
    "BritainSystemSpecialPowerShortcut": ["BritainSpecialPowerTrident"],
    "FranceSystemSpecialPowerShortcut": ["FranceSpecialPowerM51"],
    "India_SystemSpecialPowerShortcut": ["IndiaSpecialPowerAgniV"],
    "Pakistan_SystemSpecialPowerShortcut": ["PakistanSpecialPowerShaheenIII"],
    "JapanSystemSpecialPowerShortcut": ["Japan_Type12Missile", "Japan_ChemicalDefense"],
    "GermanySystemSpecialPowerShortcut": ["Germany_TaurusMissile", "Germany_ChemicalStrike"],
    "SouthKoreaSystemSpecialPowerShortcut": ["SouthKorea_HyunmooMissile", "SouthKorea_BiologicalWeapon"],
    "TurkeySystemSpecialPowerShortcut": ["Turkey_BoraMissile", "Turkey_ChemicalStrike"],
    "ItalySystemSpecialPowerShortcut": ["Italy_StormShadowMissile", "Italy_BiologicalWeapon"],
    "Egypt_SystemSpecialPowerShortcut": ["Egypt_ScudDMissile", "Egypt_ChemicalStrike"],
    "VietnamSystemSpecialPowerShortcut": ["Vietnam_K300Missile", "Vietnam_BiologicalWeapon"],
    "SaudiArabia_SystemSpecialPowerShortcut": ["SaudiArabia_AbabilMissile", "SaudiArabia_ChemicalStrike"],
    "UAE_SystemSpecialPowerShortcut": ["UAE_ThunderMissile", "UAE_BiologicalWeapon"],
    "UkraineSystemSpecialPowerShortcut": ["Ukraine_Hrim2Missile", "Ukraine_ChemicalStrike"],
    "Syria_SystemSpecialPowerShortcut": ["Syria_ScudMissile", "Syria_ChemicalStrike"],
    "Libya_SystemSpecialPowerShortcut": ["Libya_ScudBMissile", "Libya_BiologicalWeapon"],
    "SouthAfrica_SystemSpecialPowerShortcut": ["SouthAfrica_RaptorMissile", "SouthAfrica_ChemicalStrike"],
    "SwedenSystemSpecialPowerShortcut": ["Sweden_RBS15Missile", "Sweden_BiologicalDefense"],
}

# CommandSet name -> extra WMD buttons to add (keep existing slots)
COMMANDSET_BUTTONS = {
    "SpecialPowerShortcutIRAN": [
        "Command_LaunchIranChemicalFromShortcut",
        "Command_LaunchIranBiologicalFromShortcut",
    ],
    "SpecialPowerShortcutIranCommandSet": [
        "Command_LaunchIranChemicalFromShortcut",
        "Command_LaunchIranBiologicalFromShortcut",
    ],
    "SpecialPowerShortcutBritainCommandSet": ["Command_LaunchBritainTridentFromShortcut"],
    "SpecialPowerShortcutFranceCommandSet": ["Command_LaunchFranceM51FromShortcut"],
    "SpecialPowerShortcutGermanyCommandSet": [
        "Command_LaunchGermanyTaurusFromShortcut",
        "Command_LaunchGermanyChemicalFromShortcut",
    ],
    "SpecialPowerShortcutItalyCommandSet": [
        "Command_LaunchItalyStormShadowFromShortcut",
        "Command_LaunchItalyBiologicalFromShortcut",
    ],
    "SpecialPowerShortcutSwedenCommandSet": [
        "Command_LaunchSwedenRBS15FromShortcut",
        "Command_LaunchSwedenBiologicalDefenseFromShortcut",
    ],
    "SpecialPowerShortcutUkraineCommandSet": [
        "Command_LaunchUkraineHrim2FromShortcut",
        "Command_LaunchUkraineChemicalFromShortcut",
    ],
    "SpecialPowerShortcutTurkeyCommandSet": [
        "Command_LaunchTurkeyBoraFromShortcut",
        "Command_LaunchTurkeyChemicalFromShortcut",
    ],
    "SpecialPowerShortcutSaudiArabia": [
        "Command_LaunchSaudiAbabilFromShortcut",
        "Command_LaunchSaudiChemicalFromShortcut",
    ],
    "SpecialPowerShortcutSaudiArabiaSystem": [
        "Command_LaunchSaudiAbabilFromShortcut",
        "Command_LaunchSaudiChemicalFromShortcut",
    ],
    "SpecialPowerShortcutUAE": [
        "Command_LaunchUAEThunderFromShortcut",
        "Command_LaunchUAEBiologicalFromShortcut",
    ],
    "SpecialPowerShortcutUAESystem": [
        "Command_LaunchUAEThunderFromShortcut",
        "Command_LaunchUAEBiologicalFromShortcut",
    ],
    "SpecialPowerShortcutIndia": ["Command_LaunchIndiaAgniVFromShortcut"],
    "SpecialPowerShortcutIndiaSystem": ["Command_LaunchIndiaAgniVFromShortcut"],
    "SpecialPowerShortcutSyria": [
        "Command_LaunchSyriaScudFromShortcut",
        "Command_LaunchSyriaChemicalFromShortcut",
    ],
    "SpecialPowerShortcutSyriaSystem": [
        "Command_LaunchSyriaScudFromShortcut",
        "Command_LaunchSyriaChemicalFromShortcut",
    ],
    "SpecialPowerShortcutLibya": [
        "Command_LaunchLibyaScudBFromShortcut",
        "Command_LaunchLibyaBiologicalFromShortcut",
    ],
    "SpecialPowerShortcutLibyaSystem": [
        "Command_LaunchLibyaScudBFromShortcut",
        "Command_LaunchLibyaBiologicalFromShortcut",
    ],
    "SpecialPowerShortcutSouthAfrica": [
        "Command_LaunchSouthAfricaRaptorFromShortcut",
        "Command_LaunchSouthAfricaChemicalFromShortcut",
    ],
    "SpecialPowerShortcutSouthAfricaSystem": [
        "Command_LaunchSouthAfricaRaptorFromShortcut",
        "Command_LaunchSouthAfricaChemicalFromShortcut",
    ],
    "SpecialPowerShortcutPakistan": ["Command_LaunchPakistanShaheenFromShortcut"],
    "SpecialPowerShortcutEgyptSystem": [
        "Command_LaunchEgyptScudDFromShortcut",
        "Command_LaunchEgyptChemicalFromShortcut",
    ],
    "SpecialPowerShortcutIsraelSystem": ["Command_LaunchJerichoIIIFromShortcut"],
    "SpecialPowerShortcutIsraelCommandSet": ["Command_LaunchJerichoIIIFromShortcut"],
}

NEW_COMMANDSETS = {
    "SpecialPowerShortcutJapan": [
        "Command_SelectJapanSystemSpecialPowerShortcut",
        "Command_LaunchJapanType12FromShortcut",
        "Command_LaunchJapanChemicalDefenseFromShortcut",
    ],
    "SpecialPowerShortcutSouthKorea": [
        "Command_SelectSouthKoreaSystemSpecialPowerShortcut",
        "Command_LaunchSouthKoreaHyunmooFromShortcut",
        "Command_LaunchSouthKoreaBiologicalFromShortcut",
    ],
    "SpecialPowerShortcutVietnam": [
        "Command_SelectVietnamSystemSpecialPowerShortcut",
        "Command_LaunchVietnamK300FromShortcut",
        "Command_LaunchVietnamBiologicalFromShortcut",
    ],
}

CSF_LABELS = {
    "CONTROLBAR:BritainTrident": "Trident II D5",
    "CONTROLBAR:TooltipBritainTrident": "British nuclear ballistic missile. Same effect as the USA nuclear superweapon.",
    "CONTROLBAR:FranceM51": "M51",
    "CONTROLBAR:TooltipFranceM51": "French nuclear ballistic missile. Same effect as the USA nuclear superweapon.",
    "CONTROLBAR:IndiaAgniV": "Agni-V",
    "CONTROLBAR:TooltipIndiaAgniV": "Indian nuclear ballistic missile. Same effect as the USA nuclear superweapon.",
    "CONTROLBAR:PakistanShaheenIII": "Shaheen-III",
    "CONTROLBAR:TooltipPakistanShaheenIII": "Pakistani nuclear ballistic missile. Same effect as the USA nuclear superweapon.",
    "CONTROLBAR:KhorramshahrBallisticMissile": "Khorramshahr Ballistic Missile",
    "CONTROLBAR:TooltipKhorramshahrBallisticMissile": "Iranian conventional ballistic missile.",
    "CONTROLBAR:IranChemicalStrike": "Chemical Strike",
    "CONTROLBAR:TooltipIranChemicalStrike": "Chemical strike. Area contamination.",
    "CONTROLBAR:IranBiologicalWeapon": "Biological Weapon",
    "CONTROLBAR:TooltipIranBiologicalWeapon": "Biological weapon. Area contamination.",
    "CONTROLBAR:JapanType12Missile": "Type-12 Missile",
    "CONTROLBAR:TooltipJapanType12Missile": "Japanese Type-12 anti-ship / land-attack missile.",
    "CONTROLBAR:JapanChemicalDefense": "Chemical Defense",
    "CONTROLBAR:TooltipJapanChemicalDefense": "Chemical defense strike.",
    "CONTROLBAR:GermanyTaurusMissile": "Taurus Missile",
    "CONTROLBAR:TooltipGermanyTaurusMissile": "German Taurus cruise missile.",
    "CONTROLBAR:GermanyChemicalStrike": "Chemical Strike",
    "CONTROLBAR:TooltipGermanyChemicalStrike": "Chemical strike. Area contamination.",
    "CONTROLBAR:SouthKoreaHyunmooMissile": "Hyunmoo Missile",
    "CONTROLBAR:TooltipSouthKoreaHyunmooMissile": "South Korean Hyunmoo ballistic missile.",
    "CONTROLBAR:SouthKoreaBiologicalWeapon": "Biological Weapon",
    "CONTROLBAR:TooltipSouthKoreaBiologicalWeapon": "Biological weapon. Area contamination.",
    "CONTROLBAR:TurkeyBoraMissile": "Bora Missile",
    "CONTROLBAR:TooltipTurkeyBoraMissile": "Turkish Bora ballistic missile.",
    "CONTROLBAR:TurkeyChemicalStrike": "Chemical Strike",
    "CONTROLBAR:TooltipTurkeyChemicalStrike": "Chemical strike. Area contamination.",
    "CONTROLBAR:ItalyStormShadowMissile": "Storm Shadow Missile",
    "CONTROLBAR:TooltipItalyStormShadowMissile": "Italian Storm Shadow cruise missile.",
    "CONTROLBAR:ItalyBiologicalWeapon": "Biological Weapon",
    "CONTROLBAR:TooltipItalyBiologicalWeapon": "Biological weapon. Area contamination.",
    "CONTROLBAR:EgyptScudDMissile": "Scud-D Missile",
    "CONTROLBAR:TooltipEgyptScudDMissile": "Egyptian Scud-D ballistic missile.",
    "CONTROLBAR:EgyptChemicalStrike": "Chemical Strike",
    "CONTROLBAR:TooltipEgyptChemicalStrike": "Chemical strike. Area contamination.",
    "CONTROLBAR:VietnamK300Missile": "K-300 Missile",
    "CONTROLBAR:TooltipVietnamK300Missile": "Vietnamese K-300 ballistic missile.",
    "CONTROLBAR:VietnamBiologicalWeapon": "Biological Weapon",
    "CONTROLBAR:TooltipVietnamBiologicalWeapon": "Biological weapon. Area contamination.",
    "CONTROLBAR:SaudiAbabilMissile": "Ababil Ballistic Missile",
    "CONTROLBAR:TooltipSaudiAbabilMissile": "Saudi Ababil ballistic missile.",
    "CONTROLBAR:SaudiChemicalStrike": "Chemical Strike",
    "CONTROLBAR:TooltipSaudiChemicalStrike": "Chemical strike. Area contamination.",
    "CONTROLBAR:UAEThunderMissile": "Thunder Missile System",
    "CONTROLBAR:TooltipUAEThunderMissile": "UAE Thunder missile system.",
    "CONTROLBAR:UAEBiologicalWeapon": "Biological Weapon",
    "CONTROLBAR:TooltipUAEBiologicalWeapon": "Biological weapon. Area contamination.",
    "CONTROLBAR:UkraineHrim2Missile": "Hrim-2 Ballistic Missile",
    "CONTROLBAR:TooltipUkraineHrim2Missile": "Ukrainian Hrim-2 ballistic missile.",
    "CONTROLBAR:UkraineChemicalStrike": "Chemical Strike",
    "CONTROLBAR:TooltipUkraineChemicalStrike": "Chemical strike. Area contamination.",
    "CONTROLBAR:SyriaScudMissile": "Scud Missile",
    "CONTROLBAR:TooltipSyriaScudMissile": "Syrian Scud ballistic missile.",
    "CONTROLBAR:SyriaChemicalStrike": "Chemical Strike",
    "CONTROLBAR:TooltipSyriaChemicalStrike": "Chemical strike. Area contamination.",
    "CONTROLBAR:LibyaScudBMissile": "Scud-B Missile",
    "CONTROLBAR:TooltipLibyaScudBMissile": "Libyan Scud-B ballistic missile.",
    "CONTROLBAR:LibyaBiologicalWeapon": "Biological Weapon",
    "CONTROLBAR:TooltipLibyaBiologicalWeapon": "Biological weapon. Area contamination.",
    "CONTROLBAR:SouthAfricaRaptorMissile": "Raptor Precision Missile",
    "CONTROLBAR:TooltipSouthAfricaRaptorMissile": "South African Raptor precision missile.",
    "CONTROLBAR:SouthAfricaChemicalStrike": "Chemical Strike",
    "CONTROLBAR:TooltipSouthAfricaChemicalStrike": "Chemical strike. Area contamination.",
    "CONTROLBAR:SwedenRBS15Missile": "RBS-15 Missile",
    "CONTROLBAR:TooltipSwedenRBS15Missile": "Swedish RBS-15 anti-ship missile.",
    "CONTROLBAR:SwedenBiologicalDefense": "Biological Defense Weapon",
    "CONTROLBAR:TooltipSwedenBiologicalDefense": "Biological defense weapon.",
    "CONTROLBAR:SejjilMissile": "Khorramshahr Ballistic Missile",
    "CONTROLBAR:TooltipSejjilMissile": "Khorramshahr Ballistic Missile. Conventional strike.",
    "CONTROLBAR:DF5": "DF-5C",
    "CONTROLBAR:NorthKoreaNuclearAttack": "Nuclear Missile",
    "CONTROLBAR:TooltipNorthKoreaNuclearAttack": "North Korean nuclear missile. Same effect as the USA nuclear superweapon.",
}

POWER_KIND = {name: kind for name, kind, _exists, _label in POWERS}


def parse_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for _ in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((name, data[eoff : eoff + esz]))
    return entries


def build_big_ordered(entries):
    header_size = 16
    encoded = [(n.encode("latin1"), b) for n, b in entries]
    for nb, _blob in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for nb, blob in encoded:
        index.append((nb, offset, len(blob)))
        blobs.append(blob)
        offset += len(blob)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def to_nl(block: str, newline: str) -> str:
    return block.replace("\r\n", "\n").replace("\n", newline).strip("\n") + newline


def named(text: str, kind: str, name: str):
    m = re.search(
        rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^[Ee][Nn][Dd]\s*$",
        text,
    )
    return m.group(0) if m else None


def replace_named_block(text: str, kind: str, name: str, replacement: str) -> str:
    pat = rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^[Ee][Nn][Dd]\s*$"
    m = re.search(pat, text)
    if not m:
        raise SystemExit(f"{kind} {name} not found")
    return text[: m.start()] + to_nl(replacement, nl(text)).rstrip() + text[m.end() :]


def last_object_span(text: str, obj: str):
    hits = list(
        re.finditer(
            rf"(?ms)^Object\s+{re.escape(obj)}\s*\r?\n.*?(?=^Object\s|\Z)",
            text,
        )
    )
    return hits[-1] if hits else None


def xor_csf_utf16(s: str) -> bytes:
    return bytes(b ^ 0xFF for b in s.encode("utf-16-le"))


def append_csf_labels(blob: bytes, labels: dict[str, str]) -> bytes:
    if blob[:4] != b" FSC":
        raise SystemExit("generals.csf is not CSF")
    _version, nlabels, nstrings = struct.unpack_from("<III", blob, 4)
    extra = bytearray()
    add_labels = 0
    add_strings = 0
    existing = blob.upper()
    for name, value in labels.items():
        key = name.encode("latin1")
        if key.upper() in existing:
            continue
        extra += b" LBL"
        extra += struct.pack("<II", 1, len(key))
        extra += key
        extra += b" RTS"
        extra += struct.pack("<I", len(value))
        extra += xor_csf_utf16(value)
        add_labels += 1
        add_strings += 1
    if add_labels == 0:
        return blob
    out = bytearray(blob)
    struct.pack_into("<I", out, 8, nlabels + add_labels)
    struct.pack_into("<I", out, 12, nstrings + add_strings)
    out += extra
    return bytes(out)


def specialpower_block(name: str, kind: str) -> str:
    enum = KIND_ENUM[kind]
    sound = "AirRaidSiren" if kind == "nuke" else "ScudStormInitiated"
    extra = ""
    if kind == "nuke":
        extra = "  ;InitiateSound       = ScudStormInitiated\r\n"
    else:
        extra = f"  InitiateSound       = {sound}\r\n"
    loc_sound = "  InitiateAtLocationSound = AirRaidSiren  ; plays at target\r\n" if kind == "nuke" else ""
    return (
        f"SpecialPower {name}\r\n"
        f"  Enum                = {enum}\r\n"
        f"  ReloadTime          = {RELOAD}\r\n"
        f"{extra}{loc_sound}"
        f"  PublicTimer         = Yes\r\n"
        f"  ViewObjectDuration  = 40000\r\n"
        f"  ViewObjectRange     = 250\r\n"
        f"  RadiusCursorRadius  = 200\r\n"
        f"  ShortcutPower       = Yes\r\n"
        f"  AcademyClassify     = ACT_SUPERPOWER\r\n"
        f"End\r\n"
    )


def button_block(name: str, power: str, kind: str, text: str, tip: str) -> str:
    return (
        f"CommandButton {name}\r\n"
        f"  Command           = SPECIAL_POWER_FROM_SHORTCUT\r\n"
        f"  SpecialPower      = {power}\r\n"
        f"  Options           = NEED_SPECIAL_POWER_SCIENCE NEED_TARGET_POS CONTEXTMODE_COMMAND\r\n"
        f"  TextLabel         = {text}\r\n"
        f"  ButtonImage       = {KIND_IMAGE[kind]}\r\n"
        f"  ButtonBorderType  = ACTION\r\n"
        f"  DescriptLabel     = {tip}\r\n"
        f"  RadiusCursorType  = {KIND_CURSOR[kind]}\r\n"
        f"  InvalidCursorName = GenericInvalid\r\n"
        f"End\r\n"
    )


def patch_existing_specialpower(blk: str, kind: str) -> str:
    blk = re.sub(r"(?m)^(\s*Enum\s*=\s*)\S+", r"\g<1>" + KIND_ENUM[kind], blk, count=1)
    blk = re.sub(r"(?m)^(\s*ReloadTime\s*=\s*)\S+", r"\g<1>" + RELOAD, blk, count=1)
    blk = re.sub(r"(?m)^\s*RequiredScience\s*=\s*.*\r?\n", "", blk)
    return blk


def used_slots(blk: str) -> set[int]:
    return {int(n) for n in re.findall(r"(?m)^\s*(\d+)\s*=\s*\S+", blk)}


def add_buttons_to_commandset(blk: str, buttons: list[str]) -> str:
    newline = nl(blk)
    existing = set(re.findall(r"(?m)^\s*\d+\s*=\s*(\S+)", blk))
    to_add = [b for b in buttons if b not in existing]
    if not to_add:
        return blk
    taken = used_slots(blk)
    free = [i for i in range(1, 15) if i not in taken]
    if len(free) < len(to_add):
        raise SystemExit(f"not enough CommandSet slots in {blk.splitlines()[0]}")
    end_m = re.search(r"(?m)^[Ee][Nn][Dd]\s*$", blk)
    if not end_m:
        raise SystemExit("CommandSet missing End")
    insert = "".join(f"  {slot} = {btn}{newline}" for slot, btn in zip(free, to_add))
    return blk[: end_m.start()] + insert + blk[end_m.start() :]


def commandset_block(name: str, buttons: list[str]) -> str:
    lines = [f"CommandSet {name}"]
    for i, btn in enumerate(buttons, 1):
        lines.append(f"  {i} = {btn}")
    lines.append("End")
    return "\n".join(lines) + "\n"


def ocl_modules(powers: list[str]) -> str:
    lines = []
    for i, power in enumerate(powers, 1):
        kind = POWER_KIND[power]
        lines.append(f"  Behavior = OCLSpecialPower ModuleTag_NationalWMD_{i}")
        lines.append(f"    SpecialPowerTemplate = {power}")
        lines.append(f"    OCL                  = {KIND_OCL[kind]}")
        lines.append("  End")
    lines.append("  Behavior = SpecialPowerCreate ModuleTag_NationalWMDCreate")
    lines.append("  End")
    return "\n".join(lines) + "\n"


def patch_system_object(blk: str, obj: str) -> str:
    newline = nl(blk)
    if obj in SYSTEM_COMMANDSET:
        blk = re.sub(
            r"(?m)^(\s*CommandSet\s+=\s+)\S+",
            rf"\1{SYSTEM_COMMANDSET[obj]}",
            blk,
            count=1,
        )
    powers = SYSTEM_POWERS[obj]
    if "ModuleTag_NationalWMD_1" in blk:
        return blk
    mods = to_nl(ocl_modules(powers), newline)
    end_m = None
    for m in re.finditer(r"(?m)^End\s*$", blk):
        end_m = m
    if not end_m:
        raise SystemExit(f"Object {obj} missing End")
    return blk[: end_m.start()] + mods + blk[end_m.start() :]


def patch_player_template(text: str) -> str:
    out = text
    for faction, new_cs in PLAYERTEMPLATE_SHORTCUTS.items():
        pat = rf"(?ms)^(PlayerTemplate\s+{re.escape(faction)}\s*\r?\n.*?^\s*SpecialPowerShortcutCommandSet\s*=\s*)(\S+)"
        m = re.search(pat, out)
        if not m:
            raise SystemExit(f"PlayerTemplate {faction} shortcut not found")
        out = out[: m.start()] + m.group(1) + new_cs + out[m.end() :]
    return out


def retarget_button(text: str, button: str, power: str, kind: str, label: str, tip: str) -> str:
    blk = named(text, "CommandButton", button)
    if not blk:
        raise SystemExit(f"CommandButton {button} not found")
    blk = re.sub(r"(?m)^(\s*SpecialPower\s+=\s+)\S+", rf"\1{power}", blk)
    blk = re.sub(r"(?m)^(\s*TextLabel\s+=\s+)\S+", rf"\1{label}", blk)
    blk = re.sub(r"(?m)^(\s*DescriptLabel\s+=\s+)\S+", rf"\1{tip}", blk)
    blk = re.sub(r"(?m)^(\s*ButtonImage\s+=\s+)\S+", rf"\1{KIND_IMAGE[kind]}", blk)
    blk = re.sub(r"(?m)^(\s*RadiusCursorType\s+=\s+)\S+", rf"\1{KIND_CURSOR[kind]}", blk)
    blk = re.sub(r"(?m)^\s*Science\s+=\s*.*\r?\n", "", blk)
    return replace_named_block(text, "CommandButton", button, blk)


def main() -> int:
    if not SRC_DATA.is_file():
        print("missing source DATA BIG", file=sys.stderr)
        return 1

    data_entries = parse_big(SRC_DATA)
    index = {norm(n): i for i, (n, _) in enumerate(data_entries)}
    src_blobs = {norm(n): b for n, b in data_entries}
    src_cs = src_blobs[norm(r"Data\INI\CommandSet.ini")].decode("latin1")
    locked_cs_before = {name: named(src_cs, "CommandSet", name) for name in LOCKED_COMMANDSETS}

    def mut(path: str, fn):
        key = norm(path)
        if key in LOCKED_PATHS:
            raise SystemExit(f"refusing locked path {path}")
        i = index[key]
        name, blob = data_entries[i]
        if path.lower().endswith(".csf"):
            new = fn(blob)
            if new == blob:
                print("unchanged", path)
                return
            data_entries[i] = (name, new)
            print("patched", path, "delta", len(new) - len(blob))
            return
        old = blob.decode("latin1")
        new = fn(old)
        if new == old:
            print("unchanged", path)
            return
        data_entries[i] = (name, new.encode("latin1"))
        print("patched", path, "delta", len(new) - len(blob))

    def patch_specialpower_file(text: str) -> str:
        newline = nl(text)
        existing_names = set(re.findall(r"(?m)^SpecialPower\s+(\S+)", text))
        for name, kind, already, _label in POWERS:
            if already:
                blk = named(text, "SpecialPower", name)
                if not blk:
                    raise SystemExit(f"existing SpecialPower {name} missing")
                text = replace_named_block(text, "SpecialPower", name, patch_existing_specialpower(blk, kind))
            elif name not in existing_names:
                text = text.rstrip("\r\n") + newline + newline + to_nl(specialpower_block(name, kind), newline)
                existing_names.add(name)
        return text

    def patch_commandbutton_file(text: str) -> str:
        newline = nl(text)
        text = retarget_button(
            text,
            "Command_LaunchJapanNuclearFromShortcut",
            "Japan_Type12Missile",
            "missile",
            "CONTROLBAR:JapanType12Missile",
            "CONTROLBAR:TooltipJapanType12Missile",
        )
        text = retarget_button(
            text,
            "Command_LaunchSouthKoreaNuclearFromShortcut",
            "SouthKorea_HyunmooMissile",
            "missile",
            "CONTROLBAR:SouthKoreaHyunmooMissile",
            "CONTROLBAR:TooltipSouthKoreaHyunmooMissile",
        )
        text = retarget_button(
            text,
            "Command_LaunchVietnamNuclearFromShortcut",
            "Vietnam_K300Missile",
            "missile",
            "CONTROLBAR:VietnamK300Missile",
            "CONTROLBAR:TooltipVietnamK300Missile",
        )
        text = retarget_button(
            text,
            "Command_SejjilFireFromShortcut",
            "Iran_SejjilMissile",
            "missile",
            "CONTROLBAR:KhorramshahrBallisticMissile",
            "CONTROLBAR:TooltipKhorramshahrBallisticMissile",
        )
        text = retarget_button(
            text,
            "Command_SejjilFire",
            "Iran_SejjilMissile",
            "missile",
            "CONTROLBAR:KhorramshahrBallisticMissile",
            "CONTROLBAR:TooltipKhorramshahrBallisticMissile",
        )
        existing = set(re.findall(r"(?m)^CommandButton\s+(\S+)", text))
        for name, power, kind, label, tip in BUTTONS:
            if name in existing:
                continue
            text = text.rstrip("\r\n") + newline + newline + to_nl(button_block(name, power, kind, label, tip), newline)
        return text

    def patch_commandset_file(text: str) -> str:
        newline = nl(text)
        for cs_name, buttons in COMMANDSET_BUTTONS.items():
            blk = named(text, "CommandSet", cs_name)
            if not blk:
                continue
            text = replace_named_block(text, "CommandSet", cs_name, add_buttons_to_commandset(blk, buttons))
        existing = set(re.findall(r"(?m)^CommandSet\s+(\S+)", text))
        for cs_name, buttons in NEW_COMMANDSETS.items():
            if cs_name in existing:
                blk = named(text, "CommandSet", cs_name)
                text = replace_named_block(text, "CommandSet", cs_name, add_buttons_to_commandset(blk, buttons))
            else:
                text = text.rstrip("\r\n") + newline + newline + to_nl(commandset_block(cs_name, buttons), newline)
        return text

    mut(r"Data\INI\SpecialPower.ini", patch_specialpower_file)
    mut(r"Data\INI\CommandButton.ini", patch_commandbutton_file)
    mut(r"Data\INI\CommandSet.ini", patch_commandset_file)
    for extra in (
        r"Data\INI\CommandSet_Egypt.ini",
        r"Data\INI\CommandSet_Israel.ini",
        r"Data\INI\CommandSet_Pakistan.ini",
    ):
        if norm(extra) in index:
            mut(extra, patch_commandset_file)

    mut(r"Data\INI\PlayerTemplate.ini", patch_player_template)

    patched_system_files = {}
    for obj, path in SYSTEM_FILES.items():
        patched_system_files.setdefault(path, []).append(obj)

    for path, objs in patched_system_files.items():

        def make_fn(objects):
            def fn(text: str) -> str:
                for obj in objects:
                    m = last_object_span(text, obj)
                    if not m:
                        raise SystemExit(f"Object {obj} not in {path}")
                    text = text[: m.start()] + patch_system_object(m.group(0), obj) + text[m.end() :]
                return text

            return fn

        mut(path, make_fn(objs))

    mut(r"Data\English\generals.csf", lambda blob: append_csf_labels(blob, CSF_LABELS))

    new_cs = data_entries[index[norm(r"Data\INI\CommandSet.ini")]][1].decode("latin1")
    for name in LOCKED_COMMANDSETS:
        if named(new_cs, "CommandSet", name) != locked_cs_before[name]:
            raise SystemExit(f"locked CommandSet changed: {name}")

    for locked in LOCKED_PATHS:
        src = src_blobs[locked]
        dst = data_entries[index[locked]][1]
        if src != dst:
            raise SystemExit(f"locked path mutated: {locked}")

    names = [n for n, _ in data_entries]
    if names != [n for n, _ in parse_big(SRC_DATA)]:
        raise SystemExit("BIG entry order changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_big = OUT_DIR / "_SPEC_DATA_ONE.big"
    packed = build_big_ordered(data_entries)
    out_big.write_bytes(packed)
    sha = hashlib.sha256(packed).hexdigest()
    print("OUT", out_big)
    print("BYTES", len(packed))
    print("FILES", len(data_entries))
    print("DATA_SHA256", sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
