#!/usr/bin/env python3
"""Stage 4 independent DATA rebuild tests. No SPECTER BIG writes."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL))

from lib import cwc, data_rebuild, ini  # noqa: E402
from lib.engine import Engine  # noqa: E402
from lib.resolver import Resolver  # noqa: E402
from tests.test_art_cwc import StubArt  # noqa: E402
from tests.test_resolver import RULES, StubArchive, StubEngine, vfs_from  # noqa: E402

RECIPES = cwc.load_recipes(TOOL / "data")

CSSA1_INI = """
DamageFX TankDamageFX
  ThrottleTime = DEFAULT 100
  MajorFX = DEFAULT FX_DamageTankStruck
  MinorFX = SMALL_ARMS FX_DamageTankStruckSmallArms
  MajorFX = HEALING None
End
FXList FX_DamageTankStruck
  ParticleSystem = Spark
End
FXList FX_DamageTankStruckSmallArms
  ParticleSystem = Spark
End
ParticleSystem Spark
  ParticleName = spark.tga
End
CrateData SalvageCrateData
  CreationChance = 1.0
  KilledByType = SALVAGER
  CrateObject = SalvageCrate 1.0
End
Object SalvageCrate
  KindOf = CRATE
End
Armor TankArmor
  Armor = GATTLING 15%
End
Weapon SA22G
  DamageType = GATTLING
  AntiAirborneVehicle = Yes
End
Weapon SA22AIR
  DamageType = GATTLING
  AntiAirborneVehicle = Yes
End
CommandSet ChinaVehicleBattleMasterCommandSet
  14 = Command_Stop
End
Object ChinaCSSA1
  Model = CHCSSA1
  Weapon = PRIMARY SA22G
  Weapon = SECONDARY SA22AIR
  Armor = TankArmor
  DamageFX = TankDamageFX
  CommandSet = ChinaVehicleBattleMasterCommandSet
  KindOf = VEHICLE CAN_ATTACK
  Behavior = CreateCrateDie ModuleTag_11
    CrateData = SalvageCrateData
  End
  Behavior = AIUpdateInterface ModuleTag_03
  End
End
"""

HQ11_INI = """
DamageFX TruckDamageFX
  ThrottleTime = DEFAULT 100
  MajorFX = DEFAULT FX_DamageTankStruck
End
FXList FX_DamageTankStruck
  ParticleSystem = Spark
End
ParticleSystem Spark
  ParticleName = spark.tga
End
Armor HumveeArmor
  Armor = GATTLING 15%
End
Weapon HQ11MissileWeapon
  DamageType = EXPLOSION
  AntiAirborneVehicle = Yes
  AntiBallisticMissile = Yes
End
Weapon CWCruSA10RadarWeapon
  DamageType = EXPLOSION
  AntiAirborneVehicle = Yes
End
Locomotor CWCruS300Locomotor
  Surfaces = GROUND
End
Locomotor CWCruS300DeployedLocomotor
  Surfaces = GROUND
End
SpecialPower SpecialAbilityCWCruFakeRider_Inf_Stand
  Enum = SPECIAL_CIA_INTELLIGENCE
  ReloadTime = 5000
End
SpecialPower SpecialAbilityCWCruFakeRider_Inf_Prone
  Enum = SPECIAL_CIA_INTELLIGENCE
  ReloadTime = 5000
End
ObjectCreationList OCL_CWCruSpecialAbilityFakeRider_Inf_Stand
  CreateObject
    ObjectNames = CWCruFakeRider_Inf_Stand
    Count = 1
    ContainInsideSourceObject = Yes
  End
End
ObjectCreationList OCL_CWCruSpecialAbilityFakeRider_Inf_Prone
  CreateObject
    ObjectNames = CWCruFakeRider_Inf_Prone
    Count = 1
    ContainInsideSourceObject = Yes
  End
End
Object CWCruFakeRider_Inf_Stand
  KindOf = INFANTRY
End
Object CWCruFakeRider_Inf_Prone
  KindOf = INFANTRY
End
CommandSet CWCruS300CommandSet
  1 = Command_S300_Prone
  14 = Command_Stop
End
CommandSet CWCruS300DeployedCommandSet
  1 = Command_S300_Stand
  14 = Command_Stop
End
CommandButton Command_S300_Prone
  Command = SPECIAL_POWER
  SpecialPower = SpecialAbilityCWCruFakeRider_Inf_Prone
End
CommandButton Command_S300_Stand
  Command = SPECIAL_POWER
  SpecialPower = SpecialAbilityCWCruFakeRider_Inf_Stand
End
Object SDSR5
  KindOf = VEHICLE
  Behavior = DeployStyleAIUpdate ModuleTag_04
    PackTime = 2000
    UnpackTime = 2000
    TurretsFunctionOnlyWhenDeployed = Yes
  End
End
Object ChinaHQ11
  Model = HQ11
  DefaultConditionState
    Model = HQ11
    Animation = HQ11.HQ11
    AnimationMode = ONCE_BACKWARDS
  End
  ConditionState = RIDER2
    Model = HQ11
    Animation = HQ11.HQ11
    AnimationMode = ONCE
    WeaponLaunchBone = PRIMARY MISSILE_C
  End
  Armor = HumveeArmor
  DamageFX = TruckDamageFX
  WeaponSet
    Conditions = WEAPON_RIDER1
    Weapon = PRIMARY None
  End
  WeaponSet
    Conditions = WEAPON_RIDER2
    Weapon = PRIMARY HQ11MissileWeapon
  End
  CommandSet = CWCruS300CommandSet
  KindOf = VEHICLE CAN_ATTACK FS_BASE_DEFENSE
  Behavior = RiderChangeContain ModuleTag_Deployment99
    Rider1 = CWCruFakeRider_Inf_Stand RIDER1 WEAPON_RIDER1 STATUS_RIDER1 CWCruS300CommandSet SET_NORMAL
    Rider2 = CWCruFakeRider_Inf_Prone RIDER2 WEAPON_RIDER2 STATUS_RIDER2 CWCruS300DeployedCommandSet SET_SLUGGISH
    Slots = 1
    AllowInsideKindOf = INFANTRY
  End
  Behavior = OCLSpecialPower ModuleTag_Deployment98
    SpecialPowerTemplate = SpecialAbilityCWCruFakeRider_Inf_Stand
    OCL = OCL_CWCruSpecialAbilityFakeRider_Inf_Stand
  End
  Behavior = OCLSpecialPower ModuleTag_Deployment97
    SpecialPowerTemplate = SpecialAbilityCWCruFakeRider_Inf_Prone
    OCL = OCL_CWCruSpecialAbilityFakeRider_Inf_Prone
  End
  Locomotor = SET_NORMAL CWCruS300Locomotor
  Locomotor = SET_SLUGGISH CWCruS300DeployedLocomotor
  Behavior = FireWeaponUpdate ModuleTag_Radar
    Weapon = CWCruSA10RadarWeapon
  End
End
"""

UNPROVEN_TEL = """
Object Tel
  KindOf = VEHICLE
  Behavior = RiderChangeContain ModuleTag_01
    Rider1 = FakeStand RIDER1 WEAPON_RIDER1 STATUS_RIDER1 CmdA SET_NORMAL
  End
End
"""


class ParserKindTests(unittest.TestCase):
    def test_damagefx_is_not_fxlist(self):
        rec = vfs_from(CSSA1_INI)["Object"]["ChinaCSSA1"]
        self.assertIn("TankDamageFX", rec["named_refs"].get("DamageFX") or [])
        self.assertNotIn("TankDamageFX", rec["named_refs"].get("FXList") or [])
        dfx = vfs_from(CSSA1_INI)["DamageFX"]["TankDamageFX"]
        fx = dfx["named_refs"].get("FXList") or []
        self.assertIn("FX_DamageTankStruck", fx)
        self.assertIn("FX_DamageTankStruckSmallArms", fx)
        self.assertNotIn("DEFAULT", fx)
        self.assertNotIn("SMALL_ARMS", fx)
        self.assertNotIn("HEALING", fx)

    def test_cratedata_not_cratetemplate_header(self):
        kinds = vfs_from(CSSA1_INI)
        self.assertIn("SalvageCrateData", kinds["CrateData"])
        self.assertIn("SalvageCrate", kinds["CrateData"]["SalvageCrateData"]["named_refs"].get("Object") or [])
        rec = kinds["Object"]["ChinaCSSA1"]
        self.assertIn("SalvageCrateData", rec["named_refs"].get("CrateData") or [])


class Cssa1RebuildTests(unittest.TestCase):
    def test_independent_damagefx_and_crate(self):
        v25 = vfs_from(CSSA1_INI)
        spec = vfs_from(
            "DamageFX TankDamageFX\n  MajorFX = DEFAULT OtherFX\nEnd\n"
            "CrateData SalvageCrateData\n  CreationChance = 0.1\nEnd\n"
            "Armor TankArmor\n  Armor = GATTLING 15%\nEnd\n"
        )
        art = StubArt(
            stems={
                "chcssa1": [
                    {
                        "container": "nested_big",
                        "path": "WYS/W3D.big",
                        "inner": "CHCSSA1.W3D",
                        "filename": "CHCSSA1.W3D",
                        "source_big": "WYS/W3D.big",
                    }
                ]
            }
        )
        plan = Resolver(
            StubEngine(v25, spec), RULES, StubArchive(), art_index=art, cwc_recipes=RECIPES
        ).plan_object("ChinaCSSA1")
        self.assertEqual(plan["data_status"], "READY_FOR_TRANSFER_PLAN")
        dfx = next(d for d in plan["deps"] if d["kind"] == "DamageFX" and d["name"] == "TankDamageFX")
        self.assertEqual(dfx["action"], "INDEPENDENT_ADD")
        self.assertEqual(dfx["planned"], "SD25_TankDamageFX")
        self.assertEqual(dfx["unique_path"], r"Data\INI\DamageFX_SilentDeath.ini")
        crate = next(d for d in plan["deps"] if d["kind"] == "CrateData")
        self.assertEqual(crate["action"], "INDEPENDENT_ADD")
        self.assertEqual(crate["planned"], "SD25_SalvageCrateData")
        self.assertEqual(plan["rewrite_map"].get("TankDamageFX"), "SD25_TankDamageFX")
        self.assertEqual(plan["rewrite_map"].get("SalvageCrateData"), "SD25_SalvageCrateData")
        self.assertFalse(plan["public_ini_leaks"])
        self.assertNotIn(r"Data\INI\DamageFX.ini", plan["unique_data_files"])
        self.assertNotIn(r"Data\INI\Crate.ini", plan["unique_data_files"])
        self.assertTrue(any(c["from"] == "TankDamageFX" for c in plan["independent_clones"]))
        self.assertFalse(plan["applies_to_game"])
        self.assertFalse(plan["generals_exe_run"])

    def test_armor_rename_is_still_ready_data(self):
        v25 = vfs_from(CSSA1_INI)
        spec = vfs_from(
            "Armor TankArmor\n  Armor = EXPLOSION 99%\nEnd\n"
            "CommandButton Command_Stop\n  Command = STOP\nEnd\n"
        )
        plan = Resolver(StubEngine(v25, spec), RULES, StubArchive(), cwc_recipes=RECIPES).plan_object(
            "ChinaCSSA1"
        )
        armor = next(d for d in plan["deps"] if d["kind"] == "Armor" and d["name"] == "TankArmor")
        self.assertEqual(armor["action"], "RENAME_AND_REWRITE")
        self.assertEqual(plan["data_status"], "READY_FOR_TRANSFER_PLAN")

    def test_specter_public_damagefx_not_reused_as_write_target(self):
        v25 = vfs_from(CSSA1_INI)
        spec = vfs_from("DamageFX TankDamageFX\n  MajorFX = DEFAULT FX_DamageTankStruck\nEnd\n")
        plan = Resolver(StubEngine(v25, spec), RULES, StubArchive(), cwc_recipes=RECIPES).plan_object(
            "ChinaCSSA1"
        )
        dfx = next(d for d in plan["deps"] if d["kind"] == "DamageFX")
        self.assertEqual(dfx["action"], "INDEPENDENT_ADD")
        self.assertTrue(dfx["planned"].startswith("SD25_"))


class Hq11RebuildTests(unittest.TestCase):
    def test_proven_deploy_style_and_ocl_replaced(self):
        v25 = vfs_from(HQ11_INI)
        plan = Resolver(
            StubEngine(v25, {}), RULES, StubArchive(), cwc_recipes=RECIPES
        ).plan_object("ChinaHQ11")
        proof = plan["deploy_proof"]
        self.assertTrue(proof["use_deploy_style"])
        self.assertTrue(proof["use_deployed_weaponset"])
        self.assertEqual(plan["data_status"], "READY_FOR_TRANSFER_PLAN")
        rider = next(d for d in plan["deps"] if d["kind"] == "BehaviorModule" and d["name"] == "RiderChangeContain")
        ocl = next(d for d in plan["deps"] if d["kind"] == "BehaviorModule" and d["name"] == "OCLSpecialPower")
        self.assertEqual(rider["action"], "INDEPENDENT_ADD")
        self.assertEqual(ocl["action"], "INDEPENDENT_ADD")
        names = {(d["kind"], d["name"]) for d in plan["deps"]}
        self.assertNotIn(("Object", "CWCruFakeRider_Inf_Stand"), names)
        self.assertNotIn(("SpecialPower", "SpecialAbilityCWCruFakeRider_Inf_Stand"), names)
        self.assertNotIn(("ObjectCreationList", "OCL_CWCruSpecialAbilityFakeRider_Inf_Stand"), names)
        self.assertTrue(any(d["name"] == "SD25_ChinaHQ11CommandSet" for d in plan["deps"]))
        truck = next(d for d in plan["deps"] if d["kind"] == "DamageFX")
        self.assertEqual(truck["planned"], "SD25_TruckDamageFX")
        self.assertIn("SET_SLUGGISH", proof["summary"] + str(proof["limitations"]))
        lim_caps = [x["capability"] for x in proof["limitations"]]
        self.assertTrue(any("CommandSet" in c for c in lim_caps))
        self.assertTrue(any("SET_SLUGGISH" in c for c in lim_caps))
        self.assertIn("Command_Deploy", plan.get("independent_module_preview") or "")
        self.assertIn("Conditions = DEPLOYED", plan["independent_module_preview"])
        self.assertFalse(plan["public_ini_leaks"])
        self.assertNotIn(r"Data\INI\SpecialPower.ini", plan["unique_data_files"])

    def test_unproven_rider_stays_manual(self):
        v25 = vfs_from(UNPROVEN_TEL)
        plan = Resolver(
            StubEngine(v25, {}), RULES, StubArchive(), cwc_recipes=RECIPES
        ).plan_object("Tel")
        self.assertFalse((plan.get("deploy_proof") or {}).get("use_deploy_style"))
        self.assertEqual(plan["data_status"], "MANUAL_REBUILD")
        rider = next(d for d in plan["deps"] if d["name"] == "RiderChangeContain")
        self.assertEqual(rider["action"], "MANUAL_REBUILD")

    def test_ocl_with_extra_payload_is_not_deploy_style(self):
        text = HQ11_INI.replace(
            "ObjectNames = CWCruFakeRider_Inf_Stand",
            "ObjectNames = ExtraSmokeNade",
        )
        v25 = vfs_from(text)
        plan = Resolver(
            StubEngine(v25, {}), RULES, StubArchive(), cwc_recipes=RECIPES
        ).plan_object("ChinaHQ11")
        self.assertFalse(plan["deploy_proof"]["use_deploy_style"])
        self.assertEqual(plan["data_status"], "MANUAL_REBUILD")


class ApplyAndPublicIniTests(unittest.TestCase):
    def test_apply_still_refused(self):
        with self.assertRaises(SystemExit) as ctx:
            Engine(TOOL.parents[2]).refuse_apply()
        self.assertIn("apply is disabled", str(ctx.exception))

    def test_unique_ini_paths_never_public(self):
        for spec in list(data_rebuild.INDEPENDENT_DAMAGEFX.values()) + list(
            data_rebuild.INDEPENDENT_CRATE.values()
        ):
            self.assertTrue(data_rebuild.unique_ini_allowed(spec["unique_path"]))
            for blocked in spec["never_patch"]:
                self.assertFalse(data_rebuild.unique_ini_allowed(blocked))
        self.assertEqual(
            data_rebuild.public_ini_leaks([r"Data\INI\DamageFX.ini", r"Data\INI\DamageFX_SilentDeath.ini"]),
            [r"Data\INI\DamageFX.ini"],
        )


def main():
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(sys.modules[__name__]))
    from tests import test_art_cwc, test_resolver

    suite.addTests(loader.loadTestsFromModule(test_art_cwc))
    suite.addTests(loader.loadTestsFromModule(test_resolver))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
