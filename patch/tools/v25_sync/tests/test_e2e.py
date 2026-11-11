#!/usr/bin/env python3
"""E2E dry-run tests. No SPECTER BIG writes."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL))

from lib import catalog, e2e  # noqa: E402
from lib.ss1_layout import emit_path  # noqa: E402


def rec(kind, name, refs=None, body=None, side="China", kindof="VEHICLE TANK CAN_ATTACK"):
    keys = [("Side", side), ("KindOf", kindof)]
    text = body or f"{kind} {name}\nEnd\n"
    return {
        "keys": keys,
        "named_refs": refs or {},
        "behaviors": [],
        "body": text,
        "art_refs": [],
        "source": "test.ini",
    }


class MetaEng:
    def object_meta(self, rec_):
        kinds = []
        side = ""
        for k, v in rec_.get("keys") or []:
            if k.strip().lower() == "kindof":
                kinds = [t.upper() for t in v.split()]
            if k.strip().lower() == "side":
                side = v.split()[0]
        bucket = "vehicle"
        if "AIRCRAFT" in kinds:
            bucket = "aircraft"
        if "STRUCTURE" in kinds:
            bucket = "structure"
        if "PROJECTILE" in kinds:
            bucket = "projectile"
        return {"kindof": kinds, "side": side, "specter_side": side, "bucket": bucket}


class E2EDryRunTests(unittest.TestCase):
    def test_weapon_dest_is_ss1_root_not_nested(self):
        v25 = {
            "Object": {
                "FooTank": rec(
                    "Object",
                    "FooTank",
                    {"Weapon": ["FooGun"], "Armor": ["FooArmor"]},
                    "Object FooTank\n  ArmorSet\n    Armor = FooArmor\n  End\n  Weapon = PRIMARY FooGun\nEnd\n",
                )
            },
            "Weapon": {"FooGun": rec("Weapon", "FooGun", {}, "Weapon FooGun\nEnd\n")},
            "Armor": {"FooArmor": rec("Armor", "FooArmor", {}, "Armor FooArmor\nEnd\n")},
        }
        spec = {"Object": {}, "Weapon": {}, "Armor": {}}
        spec_idx = catalog._index(spec)
        assembled = e2e.assemble_payloads("FooTank", v25["Object"]["FooTank"], v25, spec, spec_idx, {}, "China")
        dests = [d.get("dest") for d in assembled["dests"] if d.get("dest")]
        self.assertIn(r"Data\INI\Weapon_SilentDeath.ini", dests)
        self.assertFalse(any(d and "Weapon\\SilentDeath" in d for d in dests))
        self.assertEqual(assembled["dest_ini"], emit_path("Object", "FooTank", "China"))
        self.assertTrue(assembled["payloads"])

    def test_missing_projectile_is_not_pass(self):
        v25 = {
            "Object": {
                "FooTank": rec("Object", "FooTank", {"Weapon": ["FooGun"]}),
            },
            "Weapon": {
                "FooGun": rec("Weapon", "FooGun", {"Object": ["FooShell"]}, "Weapon FooGun\n  ProjectileObject = FooShell\nEnd\n"),
            },
        }
        spec = {"Object": {}, "Weapon": {}}
        cat = catalog.catalog_objects(v25, spec, {"blocked_object_sides": []})
        sample = {
            "object": "FooTank",
            "role": "tank",
            "catalog": cat["objects"][0],
            "rec": v25["Object"]["FooTank"],
            "meta": MetaEng().object_meta(v25["Object"]["FooTank"]),
        }
        row = e2e.dry_run_object(sample, v25, spec, catalog._index(spec), {}, {})
        self.assertEqual(row["status"], "fail")
        self.assertFalse(row.get("game_files_written"))
        self.assertTrue(any("FooShell" in x for x in row["missing_parse_refs"]))

    def test_locomotor_syntax_downgrades_catalog_ready(self):
        loco = (
            "Locomotor FooLoco\n"
            "  GroupMovementPriority = MOVES_BACK   Moves in the front of a group\n"
            "End\n"
        )
        v25 = {
            "Object": {
                "FooTank": rec("Object", "FooTank", {"Locomotor": ["FooLoco"], "Armor": ["FooArmor"]}),
            },
            "Locomotor": {"FooLoco": rec("Locomotor", "FooLoco", {}, loco)},
            "Armor": {"FooArmor": rec("Armor", "FooArmor", {}, "Armor FooArmor\nEnd\n")},
        }
        spec = {"Object": {}, "Locomotor": {}, "Armor": {}}
        cat = catalog.catalog_objects(v25, spec, {"blocked_object_sides": []})
        self.assertTrue(cat["objects"][0]["ready_for_safe_transfer"], cat["objects"][0])
        sample = {
            "object": "FooTank",
            "role": "tank",
            "catalog": cat["objects"][0],
            "rec": v25["Object"]["FooTank"],
            "meta": MetaEng().object_meta(v25["Object"]["FooTank"]),
        }
        row = e2e.dry_run_object(sample, v25, spec, catalog._index(spec), {}, {})
        self.assertEqual(row["status"], "repairable", row)
        self.assertFalse(row["false_ready"])
        self.assertTrue(row["normalized_preflight_ok"])
        self.assertIn("raw_bytes_need_syntax_normalize", row["reasons"])

    def test_complete_unique_chain_passes_and_writes_nothing(self):
        v25 = {
            "Object": {
                "FooTank": rec("Object", "FooTank", {"Weapon": ["FooGun"], "Armor": ["FooArmor"]}),
            },
            "Weapon": {"FooGun": rec("Weapon", "FooGun", {}, "Weapon FooGun\nEnd\n")},
            "Armor": {"FooArmor": rec("Armor", "FooArmor", {}, "Armor FooArmor\nEnd\n")},
        }
        spec = {"Object": {}, "Weapon": {}, "Armor": {}}
        cat = catalog.catalog_objects(v25, spec, {"blocked_object_sides": []})
        sample = {
            "object": "FooTank",
            "role": "tank",
            "catalog": cat["objects"][0],
            "rec": v25["Object"]["FooTank"],
            "meta": MetaEng().object_meta(v25["Object"]["FooTank"]),
        }
        row = e2e.dry_run_object(sample, v25, spec, catalog._index(spec), {}, {})
        self.assertEqual(row["status"], "pass", row)
        self.assertEqual(row["files_written"], [])
        self.assertFalse(row["game_files_written"])

    def test_select_samples_covers_roles(self):
        v25 = {
            "Object": {
                "ChinaTankOverlord": rec("Object", "ChinaTankOverlord", {}, kindof="VEHICLE TANK CAN_ATTACK"),
                "ChinaS400": rec("Object", "ChinaS400", {}, kindof="STRUCTURE FS_BASE_DEFENSE CAN_ATTACK CAN_ATTACK_AIRBORNE_VEHICLES"),
                "ChinaWarFactory": rec("Object", "ChinaWarFactory", {}, kindof="STRUCTURE FS_WARFACTORY IMMOBILE"),
                "ScudStormMissile": rec("Object", "ScudStormMissile", {}, kindof="PROJECTILE SMALL_MISSILE"),
                "AmericaJetRaptor": rec("Object", "AmericaJetRaptor", {}, kindof="AIRCRAFT CAN_ATTACK"),
                "AmericaVehicleHumvee": rec("Object", "AmericaVehicleHumvee", {}, kindof="VEHICLE CAN_ATTACK"),
            }
        }
        spec = {"Object": {}}
        cat = catalog.catalog_objects(v25, spec, {"blocked_object_sides": []})
        picked = e2e.select_samples(v25, spec, cat["objects"], MetaEng())
        roles = {p["role"] for p in picked}
        for role in e2e.ROLES:
            self.assertIn(role, roles, picked)

    def test_syntax_audit_finds_fxlist_end(self):
        v25 = {
            "FXList": {
                "FX_Bad": rec("FXList", "FX_Bad", {}, "FXList FX_Bad\n  LightPulse\n    Radius = 1\n  End\n")
            }
        }
        got = e2e.syntax_audit_v25(v25)
        self.assertIn("fxlist_missing_column0_end", got["error_counts"])


    def test_temp_dir_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            before = list(Path(td).iterdir())
            v25 = {"Object": {"A": rec("Object", "A", {}, kindof="VEHICLE TANK")}}
            spec = {"Object": {}}
            cat = catalog.catalog_objects(v25, spec, {"blocked_object_sides": []})
            sample = {
                "object": "A",
                "role": "tank",
                "catalog": cat["objects"][0],
                "rec": v25["Object"]["A"],
                "meta": MetaEng().object_meta(v25["Object"]["A"]),
            }
            e2e.dry_run_object(sample, v25, spec, catalog._index(spec), {}, {})
            self.assertEqual(list(Path(td).iterdir()), before)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
