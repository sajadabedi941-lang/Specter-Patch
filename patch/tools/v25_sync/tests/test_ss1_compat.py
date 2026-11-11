#!/usr/bin/env python3
"""SS1 layout + preflight tests. Stage 5 crash classes must fail closed. No game writes."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL))

from lib import catalog, preflight, ss1_layout  # noqa: E402
from lib.pack_sample import KIND_BUNDLE, validate_added_defs  # noqa: E402


class LayoutTests(unittest.TestCase):
    def test_nested_weapon_subdir_is_unloadable(self):
        got = ss1_layout.path_loadable(r"Data\INI\Weapon\SilentDeath\SD25_Weapons.ini")
        self.assertFalse(got["loaded"])
        self.assertEqual(got["confidence"], "unlikely")

    def test_root_weapon_extra_is_proven(self):
        got = ss1_layout.path_loadable(r"Data\INI\Weapon_SilentDeath.ini")
        self.assertTrue(got["loaded"])
        self.assertEqual(got["confidence"], "proven")

    def test_armor_extra_is_proven_same_loader_as_weapon(self):
        got = ss1_layout.path_loadable(r"Data\INI\Armor_SilentDeath.ini")
        self.assertTrue(got["loaded"])
        self.assertEqual(got["confidence"], "proven")
        self.assertNotEqual(got["confidence"], "likely")

    def test_flat_weapon_dir_file_is_proven(self):
        got = ss1_layout.path_loadable(r"Data\INI\Weapon\Weapon_China_Missiles.ini")
        self.assertTrue(got["loaded"])

    def test_object_nested_is_proven(self):
        got = ss1_layout.path_loadable(r"Data\INI\Object\SilentDeath\China\SD25_ChinaCSSA1.ini")
        self.assertTrue(got["loaded"])
        self.assertEqual(got["confidence"], "proven")

    def test_mappedimages_silentdeath_unloadable(self):
        got = ss1_layout.path_loadable(r"Data\INI\MappedImages\SilentDeath\SilentDeathMappedImages.ini")
        self.assertFalse(got["loaded"])

    def test_mappedimages_handcreated_loadable(self):
        got = ss1_layout.path_loadable(r"Data\INI\MappedImages\HandCreated\SilentDeathMappedImages.ini")
        self.assertTrue(got["loaded"])
        self.assertFalse(got.get("protected"))

    def test_public_armor_ini_is_protected(self):
        got = ss1_layout.path_loadable(r"Data\INI\Armor.ini")
        self.assertTrue(got.get("protected"))

    def test_kind_bundle_matches_ss1_emit(self):
        self.assertEqual(KIND_BUNDLE["Weapon"], ss1_layout.emit_path("Weapon", "x"))
        self.assertEqual(KIND_BUNDLE["MappedImage"], ss1_layout.emit_path("MappedImage", "x"))
        self.assertNotIn("Weapon\\SilentDeath", KIND_BUNDLE["Weapon"])
        self.assertNotIn("MappedImages\\SilentDeath", KIND_BUNDLE["MappedImage"])


class PreflightStage5Regressions(unittest.TestCase):
    def test_trees_on_fire_missing_deathweapon_is_fatal(self):
        payloads = {
            r"Data\INI\Object\SilentDeath\China\SD25_CWCgenTreesOnFire.ini": (
                "Object SD25_CWCgenTreesOnFire\n"
                "  Behavior = FireWeaponWhenDeadBehavior ModuleTag_05\n"
                "    DeathWeapon = CWCgenTreeFlameWeapon\n"
                "  End\n"
                "End\n"
            )
        }
        got = preflight.preflight_payloads(payloads, native_defs={})
        self.assertFalse(got["ok"])
        refs = [e.get("ref") for e in got["errors"]]
        self.assertTrue(any(r and r.lower() == "weapon:cwcgentreeflameweapon" for r in refs), got["errors"])

    def test_ignitionfx_missing_is_fatal(self):
        payloads = {
            r"Data\INI\Object\SilentDeath\China\SD25_CWCruS300Missile.ini": (
                "Object SD25_CWCruS300Missile\n"
                "  Behavior = MissileAIUpdate ModuleTag_07\n"
                "    IgnitionFX = FX_CWCruS300MissileIgnition\n"
                "  End\n"
                "End\n"
            )
        }
        got = preflight.preflight_payloads(payloads, native_defs={})
        self.assertFalse(got["ok"])
        refs = [e.get("ref") for e in got["errors"]]
        self.assertTrue(any(r and "FX_CWCruS300MissileIgnition" in r for r in refs), got["errors"])

    def test_locomotor_missing_semicolon_is_fatal(self):
        text = (
            "Locomotor SD25_CWCruS300Locomotor\n"
            "  GroupMovementPriority = MOVES_BACK   Moves in the front of a group\n"
            "End\n"
        )
        got = preflight.preflight_payloads({r"Data\INI\Locomotor_SilentDeath.ini": text})
        self.assertFalse(got["ok"])
        self.assertTrue(any(e.get("code") == "locomotor_uncommented_tail" for e in got["errors"]))

    def test_fxlist_missing_column0_end_is_fatal(self):
        text = "FXList SD25_A\n  LightPulse\n    Radius = 10\n  End\n"
        got = preflight.preflight_payloads({r"Data\INI\FXList_SilentDeath.ini": text})
        self.assertFalse(got["ok"])
        self.assertTrue(any(e.get("code") == "fxlist_missing_column0_end" for e in got["errors"]))

    def test_hq11_tokens_after_object_end_is_fatal(self):
        text = (
            "Object SD25_ChinaHQ11\n"
            "  Draw = W3DTruckDraw ModuleTag_01\n"
            "  End\n"
            "End\n"
            "    ConditionState = DEPLOYED\n"
        )
        got = preflight.preflight_payloads(
            {r"Data\INI\Object\SilentDeath\China\SD25_ChinaHQ11.ini": text}
        )
        self.assertFalse(got["ok"])
        self.assertTrue(any(e.get("code") == "tokens_after_object_end" for e in got["errors"]))

    def test_duplicate_armor_is_fatal(self):
        text = (
            "Armor SD25_ProjectileArmor\n  Armor = DEFAULT 25%\nEnd\n"
            "Armor SD25_ProjectileArmor\n  Armor = DEFAULT 25%\nEnd\n"
        )
        got = preflight.preflight_payloads({r"Data\INI\Armor_SilentDeath.ini": text})
        self.assertFalse(got["ok"])
        self.assertTrue(any(e.get("code") == "duplicate_named_block" for e in got["errors"]))

    def test_object_file_alone_is_not_ready(self):
        v25 = {
            "Object": {
                "V25OnlyTank": {
                    "keys": [("Side", "China")],
                    "named_refs": {"Weapon": ["MissingGun"]},
                    "behaviors": ["AIUpdateInterface"],
                    "body": "Object V25OnlyTank\nEnd\n",
                }
            }
        }
        got = catalog.catalog_objects(v25, {"Object": {}, "Weapon": {}}, {"blocked_object_sides": []})
        row = got["objects"][0]
        self.assertFalse(row["ready_for_safe_transfer"])
        self.assertEqual(row["status"], "needs_fix")
        self.assertIn("Weapon:MissingGun", row["missing_parse_refs"])

    def test_missing_projectile_on_weapon_blocks_object(self):
        v25 = {
            "Object": {
                "FooTank": {
                    "keys": [("Side", "China")],
                    "named_refs": {"Weapon": ["FooGun"]},
                    "behaviors": ["AIUpdateInterface"],
                    "body": "Object FooTank\nEnd\n",
                }
            },
            "Weapon": {
                "FooGun": {
                    "named_refs": {"Object": ["FooShell"]},
                    "keys": [],
                    "behaviors": [],
                    "body": "Weapon FooGun\n  ProjectileObject = FooShell\nEnd\n",
                }
            },
        }
        got = catalog.catalog_objects(v25, {"Object": {}, "Weapon": {}}, {"blocked_object_sides": []})
        row = got["objects"][0]
        self.assertFalse(row["ready_for_safe_transfer"])
        self.assertEqual(row["status"], "needs_fix")
        self.assertTrue(any("FooShell" in r for r in row["missing_parse_refs"]), row)

    def test_complete_unique_chain_is_ready(self):
        v25 = {
            "Object": {
                "FooTank": {
                    "keys": [("Side", "China")],
                    "named_refs": {"Weapon": ["FooGun"], "Armor": ["FooArmor"]},
                    "behaviors": ["AIUpdateInterface"],
                    "body": "Object FooTank\nEnd\n",
                }
            },
            "Weapon": {
                "FooGun": {
                    "named_refs": {},
                    "keys": [],
                    "behaviors": [],
                    "body": "Weapon FooGun\nEnd\n",
                }
            },
            "Armor": {
                "FooArmor": {
                    "named_refs": {},
                    "keys": [],
                    "behaviors": [],
                    "body": "Armor FooArmor\nEnd\n",
                }
            },
        }
        got = catalog.catalog_objects(v25, {"Object": {}, "Weapon": {}, "Armor": {}}, {"blocked_object_sides": []})
        row = got["objects"][0]
        self.assertTrue(row["ready_for_safe_transfer"], row)
        self.assertEqual(row["status"], "unique_import_ready")

    def test_factory_build_list_does_not_block_the_factory(self):
        v25 = {
            "Object": {
                "FooFactory": {
                    "keys": [("Side", "China")],
                    "named_refs": {"CommandSet": ["FooFactorySet"], "Armor": ["FooArmor"]},
                    "behaviors": ["AIUpdateInterface"],
                    "body": "Object FooFactory\nEnd\n",
                }
            },
            "CommandSet": {
                "FooFactorySet": {
                    "named_refs": {"CommandButton": ["Command_BuildMissing"]},
                    "keys": [],
                    "behaviors": [],
                    "body": "CommandSet FooFactorySet\nEnd\n",
                }
            },
            "CommandButton": {
                "Command_BuildMissing": {
                    "named_refs": {"Object": ["MissingUnit"]},
                    "keys": [],
                    "behaviors": [],
                    "body": "CommandButton Command_BuildMissing\nEnd\n",
                }
            },
            "Armor": {
                "FooArmor": {"named_refs": {}, "keys": [], "behaviors": [], "body": "Armor FooArmor\nEnd\n"}
            },
        }
        got = catalog.catalog_objects(v25, {"Object": {}, "Weapon": {}, "Armor": {}}, {"blocked_object_sides": []})
        row = got["objects"][0]
        self.assertTrue(row["ready_for_safe_transfer"], row)
        self.assertFalse(any("MissingUnit" in r for r in row["missing_parse_refs"]))

    def test_missing_command_button_is_not_ready(self):
        v25 = {
            "Object": {
                "FooFactory": {
                    "keys": [("Side", "China")],
                    "named_refs": {"CommandSet": ["FooFactorySet"]},
                    "behaviors": [],
                    "body": "Object FooFactory\nEnd\n",
                }
            },
            "CommandSet": {
                "FooFactorySet": {
                    "named_refs": {"CommandButton": ["Command_Missing"]},
                    "keys": [],
                    "behaviors": [],
                    "body": "CommandSet FooFactorySet\n  1 = Command_Missing\nEnd\n",
                }
            },
        }
        got = catalog.catalog_objects(v25, {"Object": {}, "CommandSet": {}, "CommandButton": {}}, {"blocked_object_sides": []})
        row = got["objects"][0]
        self.assertFalse(row["ready_for_safe_transfer"])
        self.assertEqual(row["status"], "needs_fix")
        self.assertTrue(any("Command_Missing" in r for r in row["missing_parse_refs"]), row)

    def test_validate_rejects_nested_weapon_dir(self):
        added = {
            r"Data\INI\Weapon\SilentDeath\SD25_Weapons.ini": b"Weapon SD25_Gun\nEnd\n",
            r"Data\INI\CommandSet_ZZZZ_SilentDeath_China.ini": (
                b"CommandSet PLAWarFactoryCommandSet\n"
                b"  4 = SD25_Command_ConstructChinaCSSA1\n"
                b"  7 = SD25_Command_ConstructChinaHQ11\nEnd\n"
            ),
            r"Data\INI\Object\SilentDeath\China\SD25_ChinaCSSA1.ini": (
                b"Object SD25_ChinaCSSA1\n  ArmorSet\n    Armor = SD25_TankArmor\n  End\nEnd\n"
            ),
            r"Data\INI\Object\SilentDeath\China\SD25_ChinaHQ11.ini": (
                b"Object SD25_ChinaHQ11\n"
                b"  ArmorSet\n    Armor = SD25_HumveeArmor\n  End\n"
                b"  Behavior = DeployStyleAIUpdate ModuleTag_SD25_Deploy\n"
                b"    TurretsFunctionOnlyWhenDeployed = Yes\n  End\n"
                b"  WeaponSet\n    Conditions = DEPLOYED\n  End\n"
                b"  Draw = W3DTruckDraw ModuleTag_01\n    ConditionState = DEPLOYED\n"
                b"      Model = HQ11\n    End\n  End\nEnd\n"
            ),
            r"Data\INI\Armor_SilentDeath.ini": (
                b"Armor SD25_TankArmor\nEnd\nArmor SD25_HumveeArmor\nEnd\n"
            ),
        }
        got = validate_added_defs(added, {})
        self.assertFalse(got["ok"])
        self.assertTrue(any("unloadable_path" in e and "Weapon\\SilentDeath" in e for e in got["errors"]), got["errors"])


def main():
    loader = unittest.defaultTestLoader
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
