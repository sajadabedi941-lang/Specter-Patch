#!/usr/bin/env python3
"""Generate Faction Technology + General Star INI overlays."""
from pathlib import Path

ROOT = Path("/workspace/patch/Data/INI")

UPGRADES = [
    ("America", "StealthSystems", 2200, 50, "SSStealth"),
    ("America", "PrecisionWeapons", 2000, 45, "SSPlaneMissile"),
    ("America", "AdvancedAircraft", 2500, 55, "SSRaptor"),
    ("Russia", "MissileTechnology", 2400, 50, "SSScud"),
    ("Russia", "HeavyArmor", 2000, 45, "SSCompositeArmor"),
    ("Russia", "ElectronicWarfare", 2100, 48, "SSRadarJam"),
    ("China", "DroneTechnology", 1800, 40, "SSDrone"),
    ("China", "MissileSystems", 2300, 50, "SSScud"),
    ("China", "MassProduction", 1600, 35, "SSSupplyLines"),
    ("Iran", "MissileUpgrades", 1900, 42, "SSScud"),
    ("Iran", "DroneTechnology", 1700, 38, "SSDrone"),
    ("Iran", "AirDefense", 2000, 45, "SSPatriot"),
    ("Turkey", "UAVTechnology", 1800, 40, "SSDrone"),
    ("Turkey", "FighterTechnology", 2400, 52, "SSRaptor"),
    ("Turkey", "ModernAirDefense", 2100, 48, "SSPatriot"),
    ("India", "StrategicWeapons", 2600, 55, "SSNuke"),
    ("India", "MissileImprovements", 2200, 48, "SSScud"),
    ("Pakistan", "StrategicWeapons", 2500, 55, "SSNuke"),
    ("Pakistan", "MissileImprovements", 2100, 46, "SSScud"),
    ("Japan", "AdvancedElectronics", 2300, 50, "SSRadar"),
    ("Japan", "DefensiveTechnology", 2200, 48, "SSPatriot"),
    ("Ukraine", "DroneSystems", 1600, 36, "SSDrone"),
    ("Ukraine", "DefensiveSystems", 1800, 40, "SSPatriot"),
    ("SaudiArabia", "HighTechImport", 3200, 55, "SSPlaneMissile"),
    ("SaudiArabia", "AdvancedSystems", 3000, 52, "SSPatriot"),
    ("UAE", "HighTechImport", 3200, 55, "SSPlaneMissile"),
    ("UAE", "AdvancedSystems", 3000, 52, "SSPatriot"),
    ("Iraq", "MissileGuidance", 1800, 40, "SSScud"),
    ("Iraq", "AirDefense", 1700, 38, "SSPatriot"),
    ("NorthKorea", "MissileGuidance", 1500, 42, "SSScud"),
    ("NorthKorea", "ArtilleryNetwork", 1400, 38, "SSArtillery"),
]

TECH_SCIENCES = [
    ("America", "SCIENCE_AMERICA", "StealthSystems", 2),
    ("America", "SCIENCE_AMERICA", "PrecisionWeapons", 2),
    ("America", "SCIENCE_AMERICA", "AdvancedAircraft", 2),
    ("Russia", "SCIENCE_Russia", "MissileTechnology", 2),
    ("Russia", "SCIENCE_Russia", "HeavyArmor", 2),
    ("Russia", "SCIENCE_Russia", "ElectronicWarfare", 2),
    ("China", "SCIENCE_China", "DroneTechnology", 2),
    ("China", "SCIENCE_China", "MissileSystems", 2),
    ("China", "SCIENCE_China", "MassProduction", 1),
    ("Iran", "SCIENCE_Iran", "MissileUpgrades", 2),
    ("Iran", "SCIENCE_Iran", "DroneTechnology", 2),
    ("Iran", "SCIENCE_Iran", "AirDefense", 2),
    ("Turkey", "SCIENCE_Turkey", "UAVTechnology", 2),
    ("Turkey", "SCIENCE_Turkey", "FighterTechnology", 2),
    ("Turkey", "SCIENCE_Turkey", "ModernAirDefense", 2),
    ("India", "SCIENCE_India", "StrategicWeapons", 2),
    ("India", "SCIENCE_India", "MissileImprovements", 2),
    ("Pakistan", "SCIENCE_Pakistan", "StrategicWeapons", 2),
    ("Pakistan", "SCIENCE_Pakistan", "MissileImprovements", 2),
    ("Japan", "SCIENCE_Japan", "AdvancedElectronics", 2),
    ("Japan", "SCIENCE_Japan", "DefensiveTechnology", 2),
    ("Ukraine", "SCIENCE_Ukraine", "DroneSystems", 2),
    ("Ukraine", "SCIENCE_Ukraine", "DefensiveSystems", 2),
    ("SaudiArabia", "SCIENCE_SaudiArabia", "HighTechImport", 2),
    ("SaudiArabia", "SCIENCE_SaudiArabia", "AdvancedSystems", 2),
    ("UAE", "SCIENCE_UAE", "HighTechImport", 2),
    ("UAE", "SCIENCE_UAE", "AdvancedSystems", 2),
    ("Iraq", "SCIENCE_Iraq", "MissileGuidance", 2),
    ("Iraq", "SCIENCE_Iraq", "AirDefense", 2),
    ("NorthKorea", "SCIENCE_NorthKorea", "MissileGuidance", 2),
    ("NorthKorea", "SCIENCE_NorthKorea", "ArtilleryNetwork", 2),
]

ABILITIES = [
    ("America", "SCIENCE_AMERICA", "StealthStrike", 3, "SPECIAL_ARTILLERY_BARRAGE", 360000, 180),
    ("Russia", "SCIENCE_Russia", "MissileBarrage", 3, "SPECIAL_ARTILLERY_BARRAGE", 380000, 200),
    ("China", "SCIENCE_China", "DroneSwarm", 3, "SPECIAL_PARADROP_AMERICA", 340000, 160),
    ("Iran", "SCIENCE_Iran", "SaturationStrike", 3, "SPECIAL_ARTILLERY_BARRAGE", 370000, 195),
    ("Turkey", "SCIENCE_Turkey", "UAVOverwatch", 3, "SPECIAL_SPY_SATELLITE", 280000, 300),
    ("India", "SCIENCE_India", "AgniStrike", 3, "SPECIAL_ARTILLERY_BARRAGE", 400000, 210),
    ("Pakistan", "SCIENCE_Pakistan", "ShaheenStrike", 3, "SPECIAL_ARTILLERY_BARRAGE", 400000, 210),
    ("Japan", "SCIENCE_Japan", "AegisScan", 2, "SPECIAL_SPY_SATELLITE", 240000, 320),
    ("Ukraine", "SCIENCE_Ukraine", "DroneRecon", 2, "SPECIAL_SPY_SATELLITE", 220000, 280),
    ("SaudiArabia", "SCIENCE_SaudiArabia", "PrecisionImportStrike", 3, "SPECIAL_ARTILLERY_BARRAGE", 360000, 185),
    ("UAE", "SCIENCE_UAE", "PrecisionImportStrike", 3, "SPECIAL_ARTILLERY_BARRAGE", 360000, 185),
    ("Iraq", "SCIENCE_Iraq", "MissileStrike", 3, "SPECIAL_ARTILLERY_BARRAGE", 350000, 190),
    ("NorthKorea", "SCIENCE_NorthKorea", "RocketBarrage", 3, "SPECIAL_ARTILLERY_BARRAGE", 330000, 200),
]

DOCTRINE_FACTIONS = [
    ("Russia", "SCIENCE_Russia"),
    ("China", "SCIENCE_China"),
    ("Iran", "SCIENCE_Iran"),
    ("Ukraine", "SCIENCE_Ukraine"),
    ("Pakistan", "SCIENCE_Pakistan"),
    ("SaudiArabia", "SCIENCE_SaudiArabia"),
    ("UAE", "SCIENCE_UAE"),
    ("India", "SCIENCE_India"),
    ("Japan", "SCIENCE_Japan"),
    ("NorthKorea", "SCIENCE_NorthKorea"),
]


def write_upgrades() -> None:
    lines = [
        "; SPECTER PATCH - Advanced Faction Technology upgrades",
        "; PLAYER_UPGRADE research. Unique IDs. Existing upgrades retained.",
        "",
    ]
    for side, theme, cost, time, img in UPGRADES:
        lines += [
            f"Upgrade Upgrade_{side}_{theme}",
            f"; PatchBaseCost = {cost}",
            f"; PatchBaseTime = {time}.0",
            f"  DisplayName        = UPGRADE:{side}_{theme}",
            f"  BuildTime           = {time}.0",
            f"  BuildCost           = {cost}",
            f"  ButtonImage        = {img}",
            "  ResearchSound      = RaptorVoiceUpgradeCounterMeasures",
            "End",
            "",
        ]
    (ROOT / "Upgrade_FactionTech.ini").write_text("\n".join(lines))


def write_sciences() -> None:
    lines = [
        "; SPECTER PATCH - Faction Technology and General Stars sciences",
        "; Additive. Do not remove stock or Turkey sciences.",
        "",
        "Science SCIENCE_Iran",
        "  PrerequisiteSciences = None",
        "  SciencePurchasePointCost = 0",
        "  DisplayName = SCIENCE:Iran",
        "End",
        "",
        "Science SCIENCE_NorthKorea",
        "  PrerequisiteSciences = None",
        "  SciencePurchasePointCost = 0",
        "  DisplayName = SCIENCE:NorthKorea",
        "End",
        "",
    ]
    doc_desc = {
        "Bombardment": "CONTROLBAR:TooltipBattlePlansBombardment",
        "HoldTheLine": "CONTROLBAR:TooltipBattlePlansHoldTheLine",
        "SearchAndDestroy": "CONTROLBAR:TooltipBattlePlansSearchAndDestroy",
    }
    for side, root in DOCTRINE_FACTIONS:
        for doc, desc in doc_desc.items():
            lines += [
                f"Science SCIENCE_{side}Doctrine{doc}",
                f"  PrerequisiteSciences = {root} SCIENCE_Rank1",
                "  SciencePurchasePointCost = 1",
                "  IsGrantable = Yes",
                f"  DisplayName = SCIENCE:PatchDoctrine{doc}",
                f"  Description = {desc}",
                "End",
                "",
            ]
    for side, root, theme, pts in TECH_SCIENCES:
        lines += [
            f"Science SCIENCE_{side}_Tech_{theme}",
            f"  PrerequisiteSciences = {root} SCIENCE_Rank3",
            f"  SciencePurchasePointCost = {pts}",
            "  IsGrantable = Yes",
            f"  DisplayName = SCIENCE:{side}_Tech_{theme}",
            f"  Description = CONTROLBAR:ToolTipScience_{side}_{theme}",
            "End",
            "",
        ]
    for side, root, theme, pts, _enum, _reload, _radius in ABILITIES:
        lines += [
            f"Science SCIENCE_{side}_Ability_{theme}",
            f"  PrerequisiteSciences = {root} SCIENCE_Rank8",
            f"  SciencePurchasePointCost = {pts}",
            "  IsGrantable = Yes",
            f"  DisplayName = SCIENCE:{side}_Ability_{theme}",
            f"  Description = CONTROLBAR:ToolTipAbility_{side}_{theme}",
            "End",
            "",
        ]
    (ROOT / "Science_FactionTech.ini").write_text("\n".join(lines))


def write_special_powers() -> None:
    lines = [
        "; SPECTER PATCH - Faction General Star special powers",
        "; Long reload; requires Rank8 ability sciences.",
        "",
    ]
    for side, _root, theme, _pts, enum, reload, radius in ABILITIES:
        lines += [
            f"SpecialPower Superweapon_{side}_{theme}",
            f"  Enum                = {enum}",
            f"  ReloadTime          = {reload}",
            f"  RequiredScience     = SCIENCE_{side}_Ability_{theme}",
            "  PublicTimer         = No",
            "  SharedSyncedTimer   = Yes",
            f"  RadiusCursorRadius  = {radius}",
            "  ShortcutPower       = Yes",
            "  AcademyClassify     = ACT_SUPERPOWER",
            "End",
            "",
        ]
    (ROOT / "SpecialPower_FactionTech.ini").write_text("\n".join(lines))


def write_buttons() -> None:
    lines = [
        "; SPECTER PATCH - Faction Technology CommandButtons",
        "; PLAYER_UPGRADE + PLAYER_SCIENCE / PURCHASE_SCIENCE. Additive.",
        "",
    ]
    for side, theme, _c, _t, img in UPGRADES:
        lines += [
            f"CommandButton Command_Upgrade_{side}_{theme}",
            "  Command       = PLAYER_UPGRADE",
            f"  Upgrade       = Upgrade_{side}_{theme}",
            f"  ButtonImage   = {img}",
            "  ButtonBorderType = UPGRADE",
            f"  TextLabel     = CONTROLBAR:Upgrade_{side}_{theme}",
            f"  DescriptLabel = CONTROLBAR:ToolTipUpgrade_{side}_{theme}",
            "End",
            "",
        ]
    for side, root in DOCTRINE_FACTIONS:
        for doc in ("Bombardment", "HoldTheLine", "SearchAndDestroy"):
            img = {
                "Bombardment": "SSBombardment",
                "HoldTheLine": "SSHoldTheLine",
                "SearchAndDestroy": "SSSearchAndDestroy",
            }[doc]
            lines += [
                f"CommandButton Command_PurchaseScience_{side}Doctrine{doc}",
                "  Command       = PLAYER_SCIENCE",
                f"  Science       = SCIENCE_{side}Doctrine{doc}",
                f"  ButtonImage   = {img}",
                "  ButtonBorderType = UPGRADE",
                f"  TextLabel     = CONTROLBAR:InitiateBattlePlan{doc}",
                f"  DescriptLabel = CONTROLBAR:TooltipBattlePlans{doc}",
                "End",
                "",
            ]
    for side, _root, theme, _pts in TECH_SCIENCES:
        lines += [
            f"CommandButton Command_PurchaseScience_{side}_Tech_{theme}",
            "  Command       = PLAYER_SCIENCE",
            f"  Science       = SCIENCE_{side}_Tech_{theme}",
            "  ButtonImage   = SSAdvancedTraining",
            "  ButtonBorderType = UPGRADE",
            f"  TextLabel     = CONTROLBAR:Science_{side}_{theme}",
            f"  DescriptLabel = CONTROLBAR:ToolTipScience_{side}_{theme}",
            "End",
            "",
        ]
    for side, _root, theme, _pts, _e, _r, _rad in ABILITIES:
        lines += [
            f"CommandButton Command_PurchaseScience_{side}_Ability_{theme}",
            "  Command       = PURCHASE_SCIENCE",
            f"  Science       = SCIENCE_{side}_Ability_{theme}",
            "  ButtonImage   = SSBombardment",
            "  ButtonBorderType = UPGRADE",
            f"  TextLabel     = CONTROLBAR:Ability_{side}_{theme}",
            f"  DescriptLabel = CONTROLBAR:ToolTipAbility_{side}_{theme}",
            "End",
            "",
            f"CommandButton Command_FireAbility_{side}_{theme}",
            f"  Command       = SPECIAL_POWER",
            f"  SpecialPower  = Superweapon_{side}_{theme}",
            "  Options       = NEED_TARGET_POS CONTEXTMODE_COMMAND",
            "  TextLabel     = CONTROLBAR:Ability_{side}_{theme}",
            "  ButtonImage   = SSBombardment",
            "  ButtonBorderType = ACTION",
            f"  DescriptLabel = CONTROLBAR:ToolTipAbility_{side}_{theme}",
            "End",
            "",
        ]
    (ROOT / "CommandButton_FactionTech.ini").write_text("\n".join(lines))


def write_commandsets() -> None:
    lines = [
        "; SPECTER PATCH - Faction Technology General Stars CommandSets",
        "; New national Rank CS for patch factions. America/Turkey extended elsewhere.",
        "",
    ]
    # National Rank sets for patch PlayerTemplates
    national = [
        ("Ukraine", ["DroneSystems", "DefensiveSystems"], "DroneRecon"),
        ("Pakistan", ["StrategicWeapons", "MissileImprovements"], "ShaheenStrike"),
        ("SaudiArabia", ["HighTechImport", "AdvancedSystems"], "PrecisionImportStrike"),
        ("UAE", ["HighTechImport", "AdvancedSystems"], "PrecisionImportStrike"),
        ("India", ["StrategicWeapons", "MissileImprovements"], "AgniStrike"),
        ("Japan", ["AdvancedElectronics", "DefensiveTechnology"], "AegisScan"),
        ("Iran", ["MissileUpgrades", "DroneTechnology", "AirDefense"], "SaturationStrike"),
        ("NorthKorea", ["MissileGuidance", "ArtilleryNetwork"], "RocketBarrage"),
        ("Iraq", ["MissileGuidance", "AirDefense"], "MissileStrike"),
        ("Russia", ["MissileTechnology", "HeavyArmor", "ElectronicWarfare"], "MissileBarrage"),
        ("China", ["DroneTechnology", "MissileSystems", "MassProduction"], "DroneSwarm"),
    ]
    for side, techs, ability in national:
        lines.append(f"CommandSet SCIENCE_{side}_CommandSetRank1")
        slot = 1
        for doc in ("Bombardment", "HoldTheLine", "SearchAndDestroy"):
            lines.append(f"  {slot} = Command_PurchaseScience_{side}Doctrine{doc}")
            slot += 1
        lines.append("End")
        lines.append("")
        lines.append(f"CommandSet SCIENCE_{side}_CommandSetRank3")
        slot = 1
        for theme in techs:
            lines.append(f"  {slot} = Command_PurchaseScience_{side}_Tech_{theme}")
            slot += 1
        lines.append("End")
        lines.append("")
        lines.append(f"CommandSet SCIENCE_{side}_CommandSetRank8")
        lines.append(f"  1 = Command_PurchaseScience_{side}_Ability_{ability}")
        lines.append("End")
        lines.append("")
        lines.append(f"CommandSet SpecialPowerShortcut_{side}")
        lines.append(f"  1 = Command_FireAbility_{side}_{ability}")
        lines.append("End")
        lines.append("")

    (ROOT / "CommandSet_FactionTech.ini").write_text("\n".join(lines))


def main() -> None:
    write_upgrades()
    write_sciences()
    write_special_powers()
    write_buttons()
    write_commandsets()
    print("generated faction tech INIs")


if __name__ == "__main__":
    main()
