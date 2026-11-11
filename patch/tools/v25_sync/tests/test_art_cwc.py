#!/usr/bin/env python3
"""Stage 3 nested-BIG ART + CWC tests. No SPECTER BIG writes."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL))

from lib import cwc, ini, w3d  # noqa: E402
from lib.art_index import ArtIndex  # noqa: E402
from lib.big import write_big  # noqa: E402
from lib.engine import Engine  # noqa: E402
from lib.resolver import Resolver  # noqa: E402
from tests.test_resolver import RULES, StubArchive, StubEngine, vfs_from  # noqa: E402


RECIPES = cwc.load_recipes(TOOL / "data")


def _stem(name: str) -> str:
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    return base.rsplit(".", 1)[0].lower() if "." in base else base.lower()


class StubArt:
    def __init__(self, stems=None, textures=None):
        self.stems = stems or {}
        self.textures = textures or {}

    def find(self, name: str):
        return list(self.stems.get(_stem(name), []))

    def textures_in_w3d(self, name: str):
        return list(self.textures.get(_stem(name), []))

    def animations_in_w3d(self, name: str):
        return []


class NestedBigTests(unittest.TestCase):
    def test_write_and_index_nested_big(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            inner = td / "Textures.big"
            write_big(inner, {r"Art\Textures\extiretrack.dds": b"DDS_FAKE"})
            cache = td / "cache"
            art = ArtIndex(None, cache)
            art.index_big(inner, "WYS/Textures.big")
            hits = art.find("EXTireTrack")
            self.assertTrue(hits)
            self.assertEqual(hits[0]["container"], "nested_big")
            self.assertEqual(hits[0]["filename"].lower(), "extiretrack.dds")
            self.assertIn("WYS/Textures.big", hits[0]["source_big"])
            self.assertTrue(hits[0]["inner"])

    def test_texture_inside_nested_big_is_exact_stem_only(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            inner = td / "Textures.big"
            write_big(
                inner,
                {
                    r"Art\Textures\extiretrack.dds": b"A",
                    r"Art\Textures\extnktrack.dds": b"B",
                },
            )
            art = ArtIndex(None, td / "cache")
            art.index_big(inner, "WYS/Textures.big")
            self.assertTrue(art.find("EXTireTrack"))
            self.assertTrue(art.find("EXTnkTrack"))
            self.assertFalse(art.find("EXTire"))
            self.assertFalse(art.find("MissingTrack"))

    def test_nested_big_inside_zip(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            nested = td / "Textures.big"
            write_big(nested, {r"Art\Textures\nvbtmstr_d1.dds": b"TEX"})
            zpath = td / "V25.zip"
            with zipfile.ZipFile(zpath, "w") as zf:
                zf.write(nested, "Generals Silent Death V25/WYS/Textures.big")
            art = ArtIndex(zpath, td / "cache")
            hits = art.find("NVBtmstr_D1")
            self.assertTrue(hits)
            self.assertEqual(hits[0]["container"], "nested_big")


class W3dTests(unittest.TestCase):
    def test_multi_texture_model(self):
        blob = b"xxxx CHCSSA1B.tga yyyy CHCSSA1T.dds zzzz SDNSM04.DDS end"
        names = w3d.texture_names(blob)
        self.assertEqual([n.lower() for n in names], ["chcssa1b.tga", "chcssa1t.dds", "sdnsm04.dds"])

    def test_w3d_inside_nested_big_lists_textures(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            model = b"HQ11.HQ11 CHCSSA1B.tga CHCSSA1T.dds Glass1.tga"
            w3dbig = td / "W3D.big"
            texbig = td / "Textures.big"
            write_big(w3dbig, {r"Art\W3D\CHCSSA1.W3D": model})
            write_big(
                texbig,
                {
                    r"Art\Textures\CHCSSA1B.dds": b"1",
                    r"Art\Textures\CHCSSA1T.dds": b"2",
                    r"Art\Textures\Glass1.tga": b"3",
                },
            )
            art = ArtIndex(None, td / "cache")
            art.index_big(w3dbig, "WYS/W3D.big")
            art.index_big(texbig, "WYS/Textures.big")
            tex = art.textures_in_w3d("CHCSSA1")
            self.assertGreaterEqual(len(tex), 3)
            for stem in ("CHCSSA1B", "CHCSSA1T", "Glass1"):
                self.assertTrue(art.find(stem), msg=stem)

    def test_mapped_image_name_is_not_a_missing_file(self):
        text = (
            "MappedImage SSAttackMove2\n  Texture = Atlas.tga\n  Status = OK\nEnd\n"
            "Object Tank\n  ButtonImage = SSAttackMove2\nEnd\n"
        )
        v25 = vfs_from(text)
        eng = StubEngine(v25, {})
        res = Resolver(eng, RULES, StubArchive(), art_index=StubArt())
        row = res.resolve_node("ArtFile", "SSAttackMove2")
        self.assertEqual(row["action"], "IMPORT_UNIQUE")
        self.assertEqual(row.get("found_in"), "mapped_image")

    def test_missing_art_is_not_substituted(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            inner = td / "Textures.big"
            write_big(inner, {r"Art\Textures\nearby.dds": b"X"})
            art = ArtIndex(None, td / "cache")
            art.index_big(inner, "WYS/Textures.big")
            self.assertEqual(art.find("NoW3DHere"), [])
            eng = StubEngine(vfs_from("Object Tank\n  Model = NoW3DHere\nEnd\n"), {})
            res = Resolver(eng, RULES, StubArchive(), art_index=art)
            row = res.resolve_node("ArtFile", "NoW3DHere")
            self.assertEqual(row["action"], "MANUAL_REBUILD")
            self.assertIn("No similar-name substitute", row["reason"])


class SharedArtTests(unittest.TestCase):
    def test_two_objects_share_same_art_hit(self):
        text = (
            "Object A\n  Model = SharedHull\nEnd\n"
            "Object B\n  Model = SharedHull\nEnd\n"
        )
        loc = [
            {
                "container": "nested_big",
                "path": "WYS/W3D.big",
                "inner": r"Art\W3D\SharedHull.W3D",
                "filename": "SharedHull.W3D",
                "source_big": "WYS/W3D.big",
            }
        ]
        art = StubArt(stems={"sharedhull": loc}, textures={"sharedhull": ["SharedHull.dds"]})
        eng = StubEngine(vfs_from(text), {})
        res = Resolver(eng, RULES, StubArchive(), art_index=art, cwc_recipes=RECIPES)
        p1 = res.plan_object("A")
        p2 = res.plan_object("B")
        a1 = next(d for d in p1["deps"] if d["kind"] == "ArtFile" and d["name"] == "SharedHull")
        a2 = next(d for d in p2["deps"] if d["kind"] == "ArtFile" and d["name"] == "SharedHull")
        self.assertEqual(a1["action"], a2["action"])
        self.assertEqual(a1["action"], "RECOVER_FROM_V25")
        self.assertEqual(p1["art_status"], p2["art_status"])
        tex1 = [d["name"] for d in p1["deps"] if d["kind"] == "ArtFile"]
        self.assertIn("SharedHull.dds", tex1)


class CwcTests(unittest.TestCase):
    def test_rider_ocl_deploy_inspected(self):
        body = (
            "Object Tel\n"
            "  Behavior = RiderChangeContain ModuleTag_01\n"
            "    Rider1 = FakeStand RIDER1 WEAPON_RIDER1 STATUS_RIDER1 CmdPacked SET_NORMAL\n"
            "    Rider2 = FakeProne RIDER2 WEAPON_RIDER2 STATUS_RIDER2 CmdDeployed SET_SLUGGISH\n"
            "    Slots = 1\n"
            "  End\n"
            "  Behavior = OCLSpecialPower ModuleTag_02\n"
            "    SpecialPowerTemplate = SpecialAbilityStand\n"
            "    OCL = OCL_Stand\n"
            "  End\n"
            "  Behavior = DeployStyleAIUpdate ModuleTag_03\n"
            "    PackTime = 3000\n"
            "    UnpackTime = 3000\n"
            "    TurretsFunctionOnlyWhenDeployed = Yes\n"
            "  End\n"
            "End\n"
        )
        rec = vfs_from(body)["Object"]["Tel"]
        found = {r["module"]: r for r in cwc.inspect_object(rec, RECIPES)}
        self.assertIn("RiderChangeContain", found)
        self.assertEqual(found["RiderChangeContain"]["rebuild"]["action"], "MANUAL_REBUILD")
        self.assertEqual(len(found["RiderChangeContain"]["riders"]), 2)
        self.assertIn("OCLSpecialPower", found)
        self.assertEqual(found["OCLSpecialPower"]["keys"].get("OCL"), "OCL_Stand")
        self.assertIn("DeployStyleAIUpdate", found)
        self.assertEqual(found["DeployStyleAIUpdate"]["keys"].get("PackTime"), "3000")

    def test_rider_objects_are_named_refs(self):
        text = (
            "Object Tel\n"
            "  Behavior = RiderChangeContain ModuleTag_01\n"
            "    Rider1 = FakeStand RIDER1 WEAPON_RIDER1 STATUS_RIDER1 CmdA SET_NORMAL\n"
            "  End\n"
            "End\n"
        )
        rec = vfs_from(text)["Object"]["Tel"]
        self.assertIn("FakeStand", rec["named_refs"].get("Object") or [])

    def test_deploy_style_is_stock_keep(self):
        eng = StubEngine(vfs_from("Object U\n  Behavior = DeployStyleAIUpdate X\nEnd\n"), {})
        res = Resolver(eng, RULES, StubArchive(), cwc_recipes=RECIPES)
        row = res.resolve_node("BehaviorModule", "DeployStyleAIUpdate")
        self.assertEqual(row["action"], "REUSE_NATIVE")

    def test_rider_module_is_manual(self):
        eng = StubEngine({}, {})
        res = Resolver(eng, RULES, StubArchive(), cwc_recipes=RECIPES)
        self.assertEqual(res.resolve_node("BehaviorModule", "RiderChangeContain")["action"], "MANUAL_REBUILD")
        self.assertEqual(res.resolve_node("BehaviorModule", "OCLSpecialPower")["action"], "MANUAL_REBUILD")

    def test_data_art_status_split(self):
        text = (
            "Object Tel\n"
            "  Model = Hull\n"
            "  Behavior = RiderChangeContain ModuleTag_01\n"
            "  End\n"
            "End\n"
        )
        art = StubArt(
            stems={
                "hull": [
                    {
                        "container": "nested_big",
                        "path": "WYS/W3D.big",
                        "inner": "Hull.W3D",
                        "filename": "Hull.W3D",
                        "source_big": "WYS/W3D.big",
                    }
                ]
            }
        )
        eng = StubEngine(vfs_from(text), {})
        plan = Resolver(eng, RULES, StubArchive(), art_index=art, cwc_recipes=RECIPES).plan_object("Tel")
        self.assertEqual(plan["data_status"], "MANUAL_REBUILD")
        self.assertEqual(plan["art_status"], "AUTO_RECOVERABLE")
        self.assertTrue(plan["cwc"])


class ApplyStillOff(unittest.TestCase):
    def test_apply_refused(self):
        with self.assertRaises(SystemExit):
            Engine(TOOL.parents[2]).refuse_apply()


def main():
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(sys.modules[__name__]))
    from tests import test_resolver

    suite.addTests(loader.loadTestsFromModule(test_resolver))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
