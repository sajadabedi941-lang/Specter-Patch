#!/usr/bin/env python3
"""Stage 5 experimental pack tests. Never writes SPECTER FINAL BIGs."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL))

from lib import big  # noqa: E402
from lib.engine import Engine  # noqa: E402
from lib.pack_sample import (  # noqa: E402
    CSSA1_FACTORY_SLOT,
    HQ11_FACTORY_SLOT,
    SPECTER_CHINA_FACTORY_COMMANDSET,
    SPECTER_CHINA_FACTORY_OBJECT,
    build_rename_map,
    factory_overlay_text,
    transform_hq11_body,
    unique_def_name,
    validate_added_defs,
)
from lib.rewrite import independent_name  # noqa: E402


class BigCopyTests(unittest.TestCase):
    def test_copy_adds_unique_path_and_keeps_source(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = td / "orig.big"
            big.write_big(src, {r"Data\INI\CommandSet.ini": b"KEEP"})
            before = src.read_bytes()
            dest = td / "copy.big"
            info = big.copy_big_with_adds(
                src,
                dest,
                {r"Data\INI\Object\SilentDeath\China\SD25_Tank.ini": b"Object SD25_Tank\nEnd\n"},
                protected_nkeys={"data\\ini\\commandset.ini"},
            )
            self.assertEqual(src.read_bytes(), before)
            names = [n.lower().replace("/", "\\") for n in big.list_names(dest)]
            self.assertIn("data\\ini\\commandset.ini", names)
            self.assertIn("data\\ini\\object\\silentdeath\\china\\sd25_tank.ini", names)
            self.assertEqual(info["added"], 1)

    def test_refuses_protected_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = td / "orig.big"
            big.write_big(src, {r"Data\INI\CommandSet.ini": b"KEEP"})
            with self.assertRaises(ValueError):
                big.copy_big_with_adds(
                    src,
                    td / "out.big",
                    {r"Data\INI\CommandSet.ini": b"NO"},
                    protected_nkeys={"data\\ini\\commandset.ini"},
                )


class NamingTests(unittest.TestCase):
    def test_imported_object_gets_sd25_prefix(self):
        self.assertEqual(
            unique_def_name("Object", "ChinaCSSA1", "IMPORT_UNIQUE", "ChinaCSSA1"),
            "SD25_ChinaCSSA1",
        )
        self.assertEqual(
            unique_def_name("Armor", "TankArmor", "RENAME_AND_REWRITE", "SD25_TankArmor"),
            "SD25_TankArmor",
        )
        self.assertIsNone(unique_def_name("Weapon", "Gun", "REUSE_NATIVE", "Gun"))
        self.assertIsNone(unique_def_name("CommandButton", "Command_ConstructChinaCSSA1", "IMPORT_UNIQUE", None))

    def test_rename_map_prefixes_imports(self):
        mp = build_rename_map(
            [
                {"kind": "Object", "name": "ChinaHQ11", "action": "IMPORT_UNIQUE", "planned": "ChinaHQ11"},
                {"kind": "Weapon", "name": "HQ11MissileWeapon", "action": "IMPORT_UNIQUE", "planned": "HQ11MissileWeapon"},
                {"kind": "FXList", "name": "FX_NukeGLA", "action": "REUSE_NATIVE", "planned": "FX_NukeGLA"},
            ]
        )
        self.assertEqual(mp["ChinaHQ11"], "SD25_ChinaHQ11")
        self.assertEqual(mp["HQ11MissileWeapon"], "SD25_HQ11MissileWeapon")
        self.assertNotIn("FX_NukeGLA", mp)


class Hq11TransformTests(unittest.TestCase):
    def test_replaces_riders_with_deploy_style_and_deployed_weaponset(self):
        body = (
            "Object ChinaHQ11\n"
            "  WeaponSet\n"
            "    Conditions = WEAPON_RIDER1\n"
            "    Weapon = PRIMARY None\n"
            "  End\n"
            "  WeaponSet\n"
            "    Conditions = WEAPON_RIDER2\n"
            "    Weapon = PRIMARY HQ11MissileWeapon\n"
            "  End\n"
            "  CommandSet = CWCruS300CommandSet\n"
            "  Behavior = AIUpdateInterface ModuleTag_03\n"
            "    AutoAcquireEnemiesWhenIdle = Yes Stealthed\n"
            "  End\n"
            "  Locomotor = SET_NORMAL SlowLoco\n"
            "  Locomotor = SET_SLUGGISH CrawlLoco\n"
            "  Behavior = RiderChangeContain ModuleTag_Deployment99\n"
            "    Rider1 = FakeStand RIDER1 WEAPON_RIDER1 STATUS_RIDER1 CmdA SET_NORMAL\n"
            "  End\n"
            "  Behavior = OCLSpecialPower ModuleTag_Deployment98\n"
            "    SpecialPowerTemplate = SpecialAbilityX\n"
            "    OCL = OCL_X\n"
            "  End\n"
            "  ConditionState = RIDER2\n"
            "    Model = HQ11\n"
            "  End\n"
            "End\n"
        )
        out = transform_hq11_body(body, "SD25_HQ11MissileWeapon")
        self.assertIn("DeployStyleAIUpdate", out)
        self.assertIn("Conditions = DEPLOYED", out)
        self.assertIn("Weapon = PRIMARY SD25_HQ11MissileWeapon", out)
        self.assertNotIn("RiderChangeContain", out)
        self.assertNotIn("OCLSpecialPower", out)
        self.assertNotIn("AIUpdateInterface", out)
        self.assertIn("CommandSet = SD25_ChinaHQ11CommandSet", out)
        self.assertIn("ConditionState = DEPLOYED", out)
        self.assertIn("SET_SLUGGISH deployed locomotor not bound", out)
        self.assertIn("TurretsFunctionOnlyWhenDeployed = Yes", out)


class FactoryOverlayTests(unittest.TestCase):
    def test_fills_extracted_empty_slots_only(self):
        cs = {
            "keys": [
                ("1", "Command_ConstructChinaTankBattleMaster"),
                ("14", "Command_ConstructChinaVehicleHQ9"),
            ]
        }
        text = factory_overlay_text(cs, "SD25_Command_ConstructChinaCSSA1", "SD25_Command_ConstructChinaHQ11")
        self.assertIn(f"CommandSet {SPECTER_CHINA_FACTORY_COMMANDSET}", text)
        self.assertIn(f"{CSSA1_FACTORY_SLOT} = SD25_Command_ConstructChinaCSSA1", text)
        self.assertIn(f"{HQ11_FACTORY_SLOT} = SD25_Command_ConstructChinaHQ11", text)
        self.assertIn("Command_ConstructChinaTankBattleMaster", text)
        self.assertIn("Command_ConstructChinaVehicleHQ9", text)
        self.assertEqual(SPECTER_CHINA_FACTORY_OBJECT, "ChinaWarFactory")


class ApplyStillOff(unittest.TestCase):
    def test_apply_refused(self):
        with self.assertRaises(SystemExit) as ctx:
            Engine(TOOL.parents[2]).refuse_apply()
        self.assertIn("apply is disabled", str(ctx.exception))

    def test_independent_name(self):
        self.assertEqual(independent_name("ChinaCSSA1"), "SD25_ChinaCSSA1")


class ValidateDefsTests(unittest.TestCase):
    def test_rejects_public_name_and_accepts_overlay(self):
        bad = {
            r"Data\INI\Object\SilentDeath\China\SD25_ChinaCSSA1.ini": b"Object ChinaCSSA1\nEnd\n",
        }
        result = validate_added_defs(bad, {})
        self.assertFalse(result["ok"])
        overlay = (
            "CommandSet PLAWarFactoryCommandSet\n"
            "  4 = SD25_Command_ConstructChinaCSSA1\n"
            "  7 = SD25_Command_ConstructChinaHQ11\n"
            "End\n"
            "CommandSet SD25_ChinaHQ11CommandSet\n"
            "  1 = SD25_Command_ChinaHQ11Deploy\n"
            "End\n"
        )
        hq11 = (
            "Object SD25_ChinaHQ11\n"
            "  Behavior = DeployStyleAIUpdate ModuleTag_SD25_Deploy\n"
            "    PackTime = 2000\n"
            "    TurretsFunctionOnlyWhenDeployed = Yes\n"
            "  End\n"
            "  WeaponSet\n"
            "    Conditions = DEPLOYED\n"
            "    Weapon = PRIMARY SD25_HQ11MissileWeapon\n"
            "  End\n"
            "End\n"
        )
        cssa = "Object SD25_ChinaCSSA1\nEnd\n"
        good = {
            r"Data\INI\CommandSet_ZZZZ_SilentDeath_China.ini": overlay.encode(),
            r"Data\INI\Object\SilentDeath\China\SD25_ChinaHQ11.ini": hq11.encode(),
            r"Data\INI\Object\SilentDeath\China\SD25_ChinaCSSA1.ini": cssa.encode(),
            r"Data\INI\MappedImages\SilentDeath\SilentDeathMappedImages.ini": (
                b"MappedImage CSSA1TB\n  Texture = CSSA1TB.tga\nEnd\n"
                b"MappedImage CHHQ11TB\n  Texture = CHHQ11TB.tga\nEnd\n"
            ),
        }
        art = {
            r"Art\W3D\CHCSSA1.W3D": b"W3D",
            r"Art\Textures\CSSA1TB.tga": b"TGA",
            r"Data\Audio\Sounds\LSF2C6gun.wav": b"RIFF",
        }
        ok = validate_added_defs(good, art)
        self.assertTrue(ok["ok"], ok["errors"])

    def test_armor_assignment_is_not_a_header(self):
        overlay = (
            "CommandSet PLAWarFactoryCommandSet\n"
            "  4 = SD25_Command_ConstructChinaCSSA1\n"
            "  7 = SD25_Command_ConstructChinaHQ11\n"
            "End\n"
            "CommandSet SD25_ChinaHQ11CommandSet\nEnd\n"
        )
        hq11 = (
            "Object SD25_ChinaHQ11\n"
            "  Behavior = DeployStyleAIUpdate ModuleTag_SD25_Deploy\n"
            "    TurretsFunctionOnlyWhenDeployed = Yes\n"
            "  End\n"
            "  WeaponSet\n    Conditions = DEPLOYED\n  End\n"
            "End\n"
        )
        armor = "Armor SD25_TankArmor\n  Armor = DEFAULT 100%\nEnd\n"
        added = {
            r"Data\INI\CommandSet_ZZZZ_SilentDeath_China.ini": overlay.encode(),
            r"Data\INI\Object\SilentDeath\China\SD25_ChinaHQ11.ini": hq11.encode(),
            r"Data\INI\Object\SilentDeath\China\SD25_ChinaCSSA1.ini": b"Object SD25_ChinaCSSA1\nEnd\n",
            r"Data\INI\Armor_SilentDeath.ini": armor.encode(),
        }
        result = validate_added_defs(added, {})
        self.assertTrue(result["ok"], result["errors"])
        names = [h["name"] for h in result["headers"] if h["kind"].lower() == "armor"]
        self.assertEqual(names, ["SD25_TankArmor"])


def main():
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(sys.modules[__name__]))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
