#!/usr/bin/env python3
"""Resolver / rewrite tests. No SPECTER BIG writes. No V25 extract required."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL))

from lib import compat, ini  # noqa: E402
from lib.rewrite import independent_name, rewrite_text  # noqa: E402
from lib.resolver import Resolver  # noqa: E402


RULES = json.loads((TOOL / "data" / "compatibility_rules.json").read_text(encoding="utf-8"))


class StubArchive:
    def __init__(self, stems=None):
        self.stems = stems or {}

    def find_stem(self, name: str):
        stem = name.rsplit(".", 1)[0].lower()
        return list(self.stems.get(stem, []))


class StubEngine:
    def __init__(self, v25, spec, art_v=None, art_s=None):
        self._v25 = v25
        self._spec = spec
        self._v25_art = set(art_v or [])
        self._spec_art = set(art_s or [])
        self.faction_map = json.loads((TOOL / "data" / "faction_map.json").read_text(encoding="utf-8"))

    def inventory_v25(self):
        return self._v25

    def inventory_specter(self):
        return self._spec

    def lookup(self, vfs, kind, name, tag):
        rec = (vfs.get(kind) or {}).get(name)
        if rec:
            return rec
        for k, v in (vfs.get(kind) or {}).items():
            if k.lower() == name.lower():
                return v
        return None

    def object_meta(self, rec):
        return {
            "side": "China",
            "specter_side": "China",
            "bucket": "vehicle",
            "kindof": ["VEHICLE", "CAN_ATTACK"],
            "display": None,
            "is_equipment": True,
        }


def vfs_from(text: str, source="test.ini"):
    return ini.parse_ini_text(text, source)


class RewriteTests(unittest.TestCase):
    def test_rename_updates_object_and_weapon_refs(self):
        text = (
            "Object TankA\n"
            "  Weapon = PRIMARY GunA\n"
            "  CommandSet = SetA\n"
            "End\n"
            "Weapon GunA\n"
            "  ProjectileObject = ShellA\n"
            "End\n"
        )
        mapping = {"TankA": "SD25_TankA", "GunA": "SD25_GunA"}
        out = rewrite_text(text, mapping)
        self.assertIn("Object SD25_TankA", out)
        self.assertIn("Weapon = PRIMARY SD25_GunA", out)
        self.assertIn("Weapon SD25_GunA", out)
        self.assertNotIn("Object TankA\n", out)
        self.assertIn("ProjectileObject = ShellA", out)

    def test_does_not_replace_prefix_inside_longer_name(self):
        text = "Object Foo\n  Weapon = PRIMARY FooBar\nEnd\n"
        out = rewrite_text(text, {"Foo": "SD25_Foo"})
        self.assertIn("Object SD25_Foo", out)
        self.assertIn("FooBar", out)
        self.assertNotIn("SD25_FooBar", out)


class FingerprintTests(unittest.TestCase):
    def test_same_name_different_weapon_is_not_equal(self):
        a = vfs_from("Object U\n  Weapon = PRIMARY GunA\n  KindOf = VEHICLE\nEnd\n")["Object"]["U"]
        b = vfs_from("Object U\n  Weapon = PRIMARY GunB\n  KindOf = VEHICLE\nEnd\n")["Object"]["U"]
        self.assertFalse(compat.effective_equal(a, b))

    def test_comment_only_difference_is_equal(self):
        a = vfs_from("Object U\n  KindOf = VEHICLE\n  Weapon = PRIMARY GunA\nEnd\n")["Object"]["U"]
        b = vfs_from("Object U\n  ; comment\n  KindOf = VEHICLE\n  Weapon = PRIMARY GunA\nEnd\n")["Object"]["U"]
        self.assertTrue(compat.effective_equal(a, b))


class ResolverTests(unittest.TestCase):
    def _res(self, v25, spec, archive=None, art_v=None):
        eng = StubEngine(v25, spec, art_v=art_v)
        return Resolver(eng, RULES, archive or StubArchive())

    def test_duplicate_unique_import(self):
        v25 = vfs_from("Object OnlyV25\n  KindOf = VEHICLE\nEnd\n")
        spec = vfs_from("Object Other\n  KindOf = VEHICLE\nEnd\n")
        r = self._res(v25, spec).resolve_node("Object", "OnlyV25")
        self.assertEqual(r["action"], "IMPORT_UNIQUE")

    def test_same_name_different_content_renames(self):
        v25 = vfs_from("Object Shared\n  KindOf = VEHICLE\n  Weapon = PRIMARY GunA\nEnd\n")
        spec = vfs_from("Object Shared\n  KindOf = VEHICLE\n  Weapon = PRIMARY GunB\nEnd\n")
        r = self._res(v25, spec).resolve_node("Object", "Shared")
        self.assertEqual(r["action"], "RENAME_AND_REWRITE")
        self.assertEqual(r["planned"], "SD25_Shared")

    def test_multihop_weapon_projectile(self):
        text = (
            "Object Tank\n  Weapon = PRIMARY Gun\nEnd\n"
            "Weapon Gun\n  ProjectileObject = Shell\n  DamageType = GATTLING\n  AntiGround = Yes\nEnd\n"
            "Object Shell\n  KindOf = PROJECTILE\nEnd\n"
        )
        v25 = vfs_from(text)
        spec = vfs_from("Armor TankArmor\n  Armor = GATTLING 15%\nEnd\n")
        rows = self._res(v25, spec).walk("Object", "Tank")
        kinds = {(r["kind"], r["name"]) for r in rows}
        self.assertIn(("Weapon", "Gun"), kinds)
        self.assertIn(("Object", "Shell"), kinds)
        self.assertIn(("DamageType", "GATTLING"), kinds)

    def test_cycle_does_not_loop_forever(self):
        text = (
            "Object A\n  SpawnObject = B\nEnd\n"
            "Object B\n  SpawnObject = A\nEnd\n"
        )
        v25 = vfs_from(text)
        rows = self._res(v25, {}).walk("Object", "A")
        self.assertTrue(any(r["action"] == "CYCLE" for r in rows))
        self.assertLess(len(rows), 10)

    def test_missing_ref_manual_rebuild_when_absent_from_archive(self):
        v25 = vfs_from("Object Tank\n  Weapon = PRIMARY NoSuchGun\nEnd\n")
        r = self._res(v25, {}).resolve_node("Weapon", "NoSuchGun")
        self.assertEqual(r["action"], "MANUAL_REBUILD")
        self.assertEqual(r.get("missing_from"), "archive_and_vfs")

    def test_recover_from_other_layer_and_archive(self):
        layer1 = vfs_from("Object Tank\n  Weapon = PRIMARY HiddenGun\nEnd\n", "a.ini")
        layer2 = vfs_from("Weapon HiddenGun\n  DamageType = GATTLING\nEnd\n", "other.big:Weapon.ini")
        v25 = ini.merge_vfs(layer1, layer2)
        r = self._res(v25, {}).resolve_node("Weapon", "HiddenGun")
        self.assertEqual(r["action"], "IMPORT_UNIQUE")
        art = StubArchive({"lostmodel": ["Generals Silent Death V25/Art/W3D/LostModel.W3D"]})
        r2 = self._res(v25, {}, archive=art).resolve_node("ArtFile", "LostModel")
        self.assertEqual(r2["action"], "RECOVER_FROM_V25")
        self.assertEqual(r2.get("missing_from"), "extract_vfs")

    def test_cwc_rider_is_manual_rebuild(self):
        v25 = vfs_from(
            "Object Tel\n  Behavior = RiderChangeContain ModuleTag_01\n  KindOf = VEHICLE\nEnd\n"
        )
        r = self._res(v25, {}).resolve_node("BehaviorModule", "RiderChangeContain")
        self.assertEqual(r["action"], "MANUAL_REBUILD")

    def test_missing_w3d_without_archive(self):
        v25 = vfs_from("Object Tank\n  Model = NoW3DHere\nEnd\n")
        r = self._res(v25, {}).resolve_node("ArtFile", "NoW3DHere")
        self.assertEqual(r["action"], "MANUAL_REBUILD")

    def test_shared_weapon_two_objects(self):
        text = (
            "Object T1\n  Weapon = PRIMARY SharedGun\nEnd\n"
            "Object T2\n  Weapon = PRIMARY SharedGun\nEnd\n"
            "Weapon SharedGun\n  DamageType = EXPLOSION\nEnd\n"
        )
        v25 = vfs_from(text)
        res = self._res(v25, {})
        p1 = res.plan_object("T1")
        p2 = res.plan_object("T2")
        g1 = next(d for d in p1["deps"] if d["kind"] == "Weapon")
        g2 = next(d for d in p2["deps"] if d["kind"] == "Weapon")
        self.assertEqual(g1["name"], g2["name"])
        self.assertEqual(g1["action"], g2["action"])

    def test_weapon_ocl_fx_armor_collision_rename(self):
        v25 = vfs_from(
            "Weapon W\n  DamageType = GATTLING\nEnd\n"
            "ObjectCreationList O\n  CreateObject\n    ObjectNames = Debris\n  End\nEnd\n"
            "FXList F\n  ParticleSystem = P\nEnd\n"
            "Armor A\n  Armor = GATTLING 10%\nEnd\n"
        )
        spec = vfs_from(
            "Weapon W\n  DamageType = EXPLOSION\nEnd\n"
            "ObjectCreationList O\n  CreateObject\n    ObjectNames = Other\n  End\nEnd\n"
            "FXList F\n  ParticleSystem = Q\nEnd\n"
            "Armor A\n  Armor = EXPLOSION 10%\nEnd\n"
        )
        res = self._res(v25, spec)
        self.assertEqual(res.resolve_node("Weapon", "W")["action"], "RENAME_AND_REWRITE")
        self.assertEqual(res.resolve_node("ObjectCreationList", "O")["action"], "RENAME_AND_REWRITE")
        self.assertEqual(res.resolve_node("FXList", "F")["action"], "RENAME_AND_REWRITE")
        self.assertEqual(res.resolve_node("Armor", "A")["action"], "RENAME_AND_REWRITE")

    def test_rewrite_map_covers_all_renamed_refs(self):
        text = (
            "Object Tank\n  Weapon = PRIMARY Gun\nEnd\n"
            "Weapon Gun\n  ProjectileObject = Shell\nEnd\n"
            "Object Shell\n  KindOf = PROJECTILE\nEnd\n"
        )
        v25 = vfs_from(text)
        spec = vfs_from(
            "Object Tank\n  Weapon = PRIMARY Other\nEnd\n"
            "Weapon Gun\n  ProjectileObject = OtherShell\nEnd\n"
            "Object Shell\n  KindOf = PROJECTILE SMALL_MISSILE\nEnd\n"
        )
        plan = self._res(v25, spec).plan_object("Tank")
        mp = plan["rewrite_map"]
        body = v25["Object"]["Tank"]["body"] + "\n" + v25["Weapon"]["Gun"]["body"]
        out = rewrite_text(body, mp)
        for old, new in mp.items():
            self.assertIn(new, out)
            self.assertNotEqual(old, new)


def main():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
