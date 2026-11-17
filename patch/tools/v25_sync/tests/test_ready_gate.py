#!/usr/bin/env python3
"""Ready Gate, output-only normalize, proven SS1 dests, experimental DATA pack.

Never writes SPECTER FINAL BIGs.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL))

from lib import big, catalog, normalize, pack_ready, ss1_layout  # noqa: E402


SS1_DATA = Path("/tmp/ss1/SPECTER FINAL (GeneralsMode.com)/_SPEC_DATA_ONE.big")


def rec(kind, name, refs=None, body=None, side="China", behaviors=None):
    return {
        "keys": [("Side", side)],
        "named_refs": refs or {},
        "behaviors": behaviors or [],
        "body": body or f"{kind} {name}\nEnd\n",
        "art_refs": [],
        "source": "test.ini",
    }


class ProvenDestTests(unittest.TestCase):
    def test_armor_silentdeath_is_proven(self):
        got = ss1_layout.path_loadable(r"Data\INI\Armor_SilentDeath.ini")
        self.assertTrue(got["loaded"])
        self.assertEqual(got["confidence"], "proven")

    def test_root_table_kinds_are_proven_not_likely(self):
        for path in (
            r"Data\INI\Locomotor_SilentDeath.ini",
            r"Data\INI\FXList_SilentDeath.ini",
            r"Data\INI\DamageFX_SilentDeath.ini",
            r"Data\INI\Crate_SilentDeath.ini",
            r"Data\INI\ParticleSystem_SilentDeath.ini",
            r"Data\INI\SoundEffects_SilentDeath.ini",
        ):
            got = ss1_layout.path_loadable(path)
            self.assertTrue(got["loaded"], path)
            self.assertEqual(got["confidence"], "proven", path)
            self.assertNotEqual(got["confidence"], "likely", path)

    def test_unknown_root_prefix_is_not_loaded(self):
        got = ss1_layout.path_loadable(r"Data\INI\NotAKind_SilentDeath.ini")
        self.assertFalse(got["loaded"])
        self.assertEqual(got["confidence"], "unlikely")

    @unittest.skipUnless(SS1_DATA.is_file(), "live SS1 DATA BIG not present")
    def test_live_data_big_proves_root_loader(self):
        layout = ss1_layout.discover(SS1_DATA)
        self.assertGreater(layout["extra_root_ini_count"], 0)
        for kind in ("Armor", "Locomotor", "FXList", "DamageFX", "CrateData", "ParticleSystem", "AudioEvent"):
            self.assertIn(kind, layout["proven_root_kinds"], layout.get("proven_root_kind_evidence"))
        extras = [n.lower() for n in layout["root_ini"] if "_" in n.rsplit("\\", 1)[-1]]
        self.assertTrue(any("weapon_" in n for n in extras), extras[:12])
        got = ss1_layout.path_loadable(r"Data\INI\Armor_SilentDeath.ini", layout)
        self.assertEqual(got["confidence"], "proven")


class NormalizeOutputOnlyTests(unittest.TestCase):
    def test_fxlist_close_end_does_not_mutate_input(self):
        raw = "FXList FX_A\n  LightPulse\n    Radius = 1\n  End\n"
        payloads = {r"Data\INI\FXList_SilentDeath.ini": raw}
        out = normalize.normalize_payloads(payloads)
        self.assertEqual(payloads[r"Data\INI\FXList_SilentDeath.ini"], raw)
        self.assertIn("End", out[r"Data\INI\FXList_SilentDeath.ini"])
        self.assertGreater(
            out[r"Data\INI\FXList_SilentDeath.ini"].count("End"),
            raw.count("End"),
        )

    def test_locomotor_semicolon_is_output_only(self):
        raw = "Locomotor FooLoco\n  GroupMovementPriority = MOVES_BACK   Moves in the front of a group\nEnd\n"
        payloads = {r"Data\INI\Locomotor_SilentDeath.ini": raw}
        out = normalize.normalize_payloads(payloads)
        self.assertEqual(payloads[r"Data\INI\Locomotor_SilentDeath.ini"], raw)
        self.assertIn("MOVES_BACK;", out[r"Data\INI\Locomotor_SilentDeath.ini"])


class ReadyGateTests(unittest.TestCase):
    def test_object_missing_end_is_not_ready(self):
        v25 = {
            "Object": {
                "FooTank": rec(
                    "Object",
                    "FooTank",
                    {"Armor": ["FooArmor"]},
                    "Object FooTank\n  ArmorSet\n    Armor = FooArmor\n  End\n",
                )
            },
            "Armor": {"FooArmor": rec("Armor", "FooArmor")},
        }
        got = catalog.catalog_objects(v25, {"Object": {}, "Armor": {}}, {"blocked_object_sides": []})
        row = got["objects"][0]
        self.assertFalse(row["ready_for_safe_transfer"])
        self.assertEqual(row["status"], "needs_fix")
        self.assertIn("object_missing_end", row["reasons"])

    def test_fxlist_normalize_can_make_ready(self):
        v25 = {
            "Object": {
                "FooTank": rec("Object", "FooTank", {"Armor": ["FooArmor"], "FXList": ["FX_A"]})
            },
            "Armor": {"FooArmor": rec("Armor", "FooArmor")},
            "FXList": {
                "FX_A": rec("FXList", "FX_A", {}, "FXList FX_A\n  LightPulse\n    Radius = 1\n  End\n")
            },
        }
        got = catalog.catalog_objects(
            v25, {"Object": {}, "Armor": {}, "FXList": {}}, {"blocked_object_sides": []}
        )
        row = got["objects"][0]
        self.assertTrue(row["ready_for_safe_transfer"], row)
        self.assertTrue(row.get("needs_normalize"), row)
        self.assertIn("normalized_in_output_only", row["reasons"])

    def test_cwc_manual_rebuild_keeps_modules(self):
        body = (
            "Object ChinaS400\n"
            "  Behavior = RiderChangeContain ModuleTag_01\n"
            "    PayloadTemplateName = RiderA\n"
            "  End\n"
            "  Behavior = OCLSpecialPower ModuleTag_02\n"
            "    SpecialPowerTemplate = SpecialPowerA\n"
            "  End\n"
            "End\n"
        )
        v25 = {
            "Object": {
                "ChinaS400": rec(
                    "Object",
                    "ChinaS400",
                    {},
                    body,
                    behaviors=["RiderChangeContain", "OCLSpecialPower"],
                )
            }
        }
        got = catalog.catalog_objects(v25, {"Object": {}}, {"blocked_object_sides": []})
        row = got["objects"][0]
        self.assertEqual(row["status"], "MANUAL_REBUILD")
        self.assertFalse(row["ready_for_safe_transfer"])
        self.assertIn("RiderChangeContain", row["behaviors"])
        self.assertIn("OCLSpecialPower", row["behaviors"])
        self.assertTrue(any("RiderChangeContain" in c for c in row["required_capabilities"]))
        self.assertTrue(any("OCLSpecialPower" in c for c in row["required_capabilities"]))
        self.assertIn("Behavior = RiderChangeContain", body)
        self.assertIn("Behavior = OCLSpecialPower", body)

    def test_missing_parse_fatal_is_not_ready(self):
        v25 = {
            "Object": {
                "FooTank": rec("Object", "FooTank", {"Weapon": ["MissingGun"]})
            }
        }
        got = catalog.catalog_objects(v25, {"Object": {}, "Weapon": {}}, {"blocked_object_sides": []})
        row = got["objects"][0]
        self.assertFalse(row["ready_for_safe_transfer"])
        self.assertEqual(row["status"], "needs_fix")


class ReadyPackTests(unittest.TestCase):
    def test_select_skips_non_ready(self):
        rows = [
            {"object": "Bad", "ready_for_safe_transfer": False},
            {"object": "TomahawkMissile", "ready_for_safe_transfer": True},
            {"object": "ScudStormMissile", "ready_for_safe_transfer": True},
        ]
        picked = pack_ready.select_ready_group(rows, limit=4)
        self.assertEqual([r["object"] for r in picked], ["TomahawkMissile", "ScudStormMissile"])

    def test_assemble_refuses_non_ready(self):
        rows = [{"object": "Bad", "ready_for_safe_transfer": False, "side": "China"}]
        with self.assertRaises(ValueError):
            pack_ready.assemble_ready_payloads(rows, {"Object": {}}, {}, {}, {})

    def test_pack_only_ready_and_does_not_write_source(self):
        v25 = {
            "Object": {
                "FooTank": rec("Object", "FooTank", {"Armor": ["FooArmor"], "Weapon": ["FooGun"]}),
                "NeedsFix": rec("Object", "NeedsFix", {"Weapon": ["MissingGun"]}),
            },
            "Weapon": {"FooGun": rec("Weapon", "FooGun")},
            "Armor": {"FooArmor": rec("Armor", "FooArmor")},
        }
        spec = {"Object": {}, "Weapon": {}, "Armor": {}}
        cat = catalog.catalog_objects(v25, spec, {"blocked_object_sides": []})
        by_name = {r["object"]: r for r in cat["objects"]}
        self.assertTrue(by_name["FooTank"]["ready_for_safe_transfer"])
        self.assertFalse(by_name["NeedsFix"]["ready_for_safe_transfer"])
        assembled = pack_ready.assemble_ready_payloads(
            [by_name["FooTank"]], v25, spec, catalog._index(spec), {}
        )
        self.assertTrue(assembled["preflight_ok"])
        self.assertTrue(assembled["payloads"])
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = td / "orig" / "_SPEC_DATA_ONE.big"
            src.parent.mkdir()
            big.write_big(
                src,
                {
                    r"Data\INI\Armor.ini": b"; stock\n",
                    r"Data\INI\Weapon.ini": b"; stock\n",
                    r"Data\INI\Weapon_China.ini": b"Weapon Native\nEnd\n",
                },
            )
            before = src.read_bytes()
            dest = td / "out" / "_SPEC_DATA_ONE.big"
            info = pack_ready.write_experimental_data(
                src, dest, assembled["payloads"], {"data\\ini\\armor.ini", "data\\ini\\weapon.ini"}
            )
            self.assertEqual(src.read_bytes(), before)
            self.assertTrue(dest.is_file())
            names = [n.replace("/", "\\").lower() for n in big.list_names(dest)]
            self.assertTrue(any("object\\silentdeath\\" in n for n in names), names)
            self.assertIn("data\\ini\\armor.ini", names)
            self.assertFalse(any(n.endswith("armor.ini") and "silentdeath" not in n and n != "data\\ini\\armor.ini" for n in names))
            self.assertGreater(info["added"], 0)
            with self.assertRaises(ValueError):
                pack_ready.write_experimental_data(src, src, assembled["payloads"], set())

    def test_apply_still_refused_from_engine(self):
        from lib.engine import Engine

        with self.assertRaises(SystemExit):
            Engine(TOOL.parents[2]).refuse_apply()


if __name__ == "__main__":
    raise SystemExit(unittest.main())
