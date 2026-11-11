#!/usr/bin/env python3
"""First-transfer guards. Never writes SPECTER FINAL BIGs."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL))

from lib import big, pack_transfer  # noqa: E402
from lib.art_prove import _stem, collect_chain_art  # noqa: E402
from lib.pack_sample import construct_button  # noqa: E402


class SelectAndOverlayTests(unittest.TestCase):
    def test_select_only_unique_ready(self):
        rows = [
            {"object": "ChinaS75", "ready_for_safe_transfer": True, "status": "unique_import_ready"},
            {"object": "ChinaZFB05", "ready_for_safe_transfer": True, "status": "unique_import_ready"},
            {"object": "Bad", "ready_for_safe_transfer": False, "status": "needs_fix"},
            {"object": "CWC", "ready_for_safe_transfer": False, "status": "MANUAL_REBUILD"},
        ]
        got = pack_transfer.select_ready_rows(rows)
        self.assertEqual([r["object"] for r in got], ["ChinaS75", "ChinaZFB05"])

    def test_factory_overlay_refuses_occupied_slot(self):
        cs = {"keys": [("1", "Command_Keep"), ("4", "Command_Occupied")]}
        with self.assertRaises(ValueError):
            pack_transfer.factory_overlay("PLAWarFactoryCommandSet", cs, {"4": "SD25_New"})

    def test_factory_overlay_fills_empty_only(self):
        cs = {"keys": [("1", "Command_Keep")]}
        text = pack_transfer.factory_overlay("PLAWarFactoryCommandSet", cs, {"4": "SD25_New"})
        self.assertIn("1 = Command_Keep", text)
        self.assertIn("4 = SD25_New", text)
        self.assertIn("CommandSet PLAWarFactoryCommandSet", text)

    def test_construct_button_points_at_planned_object(self):
        text = construct_button("SD25_Command_ConstructChinaS75", "ChinaS75", "CHS75TB", "CONTROLBAR:SD25_ChinaS75")
        self.assertIn("Object        = ChinaS75", text)
        self.assertIn("UNIT_BUILD", text)

    def test_armor_equals_row_does_not_drop_later_defs(self):
        from lib.pack_sample import dedupe_named_blocks

        a = "Armor SD25_ProjectileArmor\n  Armor = EXPLOSION 70%\nEnd\nArmor SD25_TankArmor\nEnd\n"
        b = "Armor SD25_ProjectileArmor\n  Armor = EXPLOSION 70%\nEnd\nArmor StructureArmorWatchTower\nEnd\n"
        merged = "".join(dedupe_named_blocks("Armor", [a, b]))
        self.assertIn("Armor SD25_ProjectileArmor", merged)
        self.assertIn("Armor SD25_TankArmor", merged)
        self.assertIn("Armor StructureArmorWatchTower", merged)
        self.assertEqual(merged.count("Armor SD25_ProjectileArmor"), 1)

    def test_validate_requires_w3d_and_unique_paths(self):
        proved = [
            {"row": {"object": "ChinaS75"}, "planned": "ChinaS75"},
            {"row": {"object": "ChinaZFB05"}, "planned": "ChinaZFB05"},
        ]
        data = {
            r"Data\INI\Object\SilentDeath\China\ChinaS75.ini": b"Object ChinaS75\nEnd\n",
            r"Data\INI\Object\SilentDeath\China\ChinaZFB05.ini": b"Object ChinaZFB05\nEnd\n",
            r"Data\INI\CommandButton_SilentDeath.ini": (
                b"CommandButton SD25_Command_ConstructChinaS75\nEnd\n"
                b"CommandButton SD25_Command_ConstructChinaZFB05\nEnd\n"
            ),
            r"Data\INI\CommandSet_ZZZZ_SilentDeath_China.ini": (
                b"CommandSet PLAWarFactoryCommandSet\n  4 = SD25_Command_ConstructChinaS75\nEnd\n"
            ),
        }
        art = {r"Art\W3D\CHS75.W3D": b"w3d", r"Art\Textures\CHS75TB.tga": b"tga"}
        factories = [
            {
                "side": "China",
                "commandset": "PLAWarFactoryCommandSet",
                "fills": {"4": "SD25_Command_ConstructChinaS75"},
            }
        ]
        v = pack_transfer.validate_first_transfer(data, art, proved, factories)
        self.assertTrue(v["ok"], v["errors"])
        bad = pack_transfer.validate_first_transfer(data, {}, proved, factories)
        self.assertFalse(bad["ok"])


class ArtStemTests(unittest.TestCase):
    def test_subobject_stem_is_model(self):
        self.assertEqual(_stem("SDHT233.SDHT233"), "sdht233")
        self.assertEqual(_stem("EXTireTrack.tga"), "extiretrack")

    def test_collect_skips_commandbutton_ui_art(self):
        v25 = {
            "Object": {
                "Foo": {
                    "named_refs": {"CommandButton": ["SSEvacButton"]},
                    "art_refs": ["FooModel", "FooModel.FooModel"],
                    "keys": [],
                    "behaviors": [],
                    "body": "Object Foo\nEnd\n",
                }
            },
            "CommandButton": {
                "SSEvacButton": {
                    "named_refs": {},
                    "art_refs": ["SSEvacButton"],
                    "keys": [],
                    "behaviors": [],
                    "body": "CommandButton SSEvacButton\nEnd\n",
                }
            },
        }
        arts = collect_chain_art("Foo", v25, {"object": set()}, {})
        self.assertEqual(arts, ["FooModel"])
        self.assertNotIn("SSEvacButton", arts)


class PackWriteTests(unittest.TestCase):
    def test_refuses_write_over_source(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = td / "_SPEC_DATA_ONE.big"
            big.write_big(src, {r"Data\INI\Armor.ini": b"x"})
            with self.assertRaises(ValueError):
                from lib.pack_ready import write_experimental_data

                write_experimental_data(src, src, {r"Data\INI\Armor_SilentDeath.ini": "Armor A\nEnd\n"}, set())

    def test_apply_still_refused(self):
        from lib.engine import Engine

        with self.assertRaises(SystemExit):
            Engine(TOOL.parents[2]).refuse_apply()


if __name__ == "__main__":
    raise SystemExit(unittest.main())
