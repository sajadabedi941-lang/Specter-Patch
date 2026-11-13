#!/usr/bin/env python3
"""Static checks for 0_SPECTER_CountrySupplyIncome.big. Not an in-game test."""
from __future__ import annotations

import hashlib
import json
import re
import struct
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
OVERLAY = HERE / "0_SPECTER_CountrySupplyIncome.big"
REPORT = HERE / "COUNTRY_SUPPLY_INCOME_REPORT.json"
BUILDER = HERE.parents[1] / "tools/big/build_specter_country_supply_income_big.py"

TARGETS = {
    "USA": 1000,
    "China": 950,
    "Germany": 900,
    "Japan": 875,
    "Britain": 850,
    "India": 825,
    "France": 800,
    "Russia": 775,
    "Italy": 750,
    "Spain": 725,
    "South Korea": 700,
    "Turkey": 675,
    "Saudi Arabia": 650,
    "Sweden": 625,
    "Israel": 600,
    "UAE": 575,
    "Vietnam": 550,
    "South Africa": 525,
    "Pakistan": 500,
    "Iran": 475,
    "Iraq": 450,
    "Ukraine": 425,
    "Libya": 400,
    "North Korea": 350,
    "Syria": 300,
}
VPSB = 25


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        out[name] = data[off : off + size]
    return out


class TestCountrySupplyIncome(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = read_big(OVERLAY)
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.blob = OVERLAY.read_bytes()

    def test_overlay_is_bigf_and_hashed(self):
        self.assertTrue(self.blob.startswith(b"BIGF"))
        digest = hashlib.sha256(self.blob).hexdigest()
        self.assertEqual(digest, self.report["overlay_sha256"])
        listed = (OVERLAY.with_suffix(OVERLAY.suffix + ".sha256")).read_text().strip()
        self.assertEqual(digest, listed)

    def test_filename_sorts_as_first_wins_zero_prefix(self):
        self.assertTrue(OVERLAY.name.startswith("0_"))
        self.assertLess(OVERLAY.name.lower(), "0_SPECTER_NatoSpainDisplay.big".lower())
        self.assertLess(OVERLAY.name.lower(), "INIZH.big".lower())
        self.assertLess(OVERLAY.name.lower(), "_SPEC_DATA_ONE.big".lower())

    def test_no_art_or_missile_files(self):
        for name in self.files:
            low = name.lower()
            self.assertFalse(low.startswith("art\\"))
            self.assertNotIn("missile", low)
            self.assertNotIn("warhead", low)
            self.assertNotIn("projectile", low)

    def test_gamedata_value_per_box(self):
        gd = self.files[r"Data\INI\GameData.ini"].decode("latin1")
        m = re.search(r"ValuePerSupplyBox\s*=\s*(\d+)", gd)
        self.assertEqual(int(m.group(1)), VPSB)

    def test_twenty_five_countries_match_table(self):
        rows = {r["country"]: r for r in self.report["countries"]}
        self.assertEqual(set(rows), set(TARGETS))
        spawns = []
        for country, target in TARGETS.items():
            row = rows[country]
            self.assertEqual(row["target_per_delivery"], target)
            self.assertEqual(row["MaxBoxes"] * VPSB, target)
            self.assertEqual(row["effective_per_delivery"], target)
            spawns.append(row["spawn"])
        self.assertEqual(len(set(spawns)), 25)

    def test_usa_clone_is_independent_of_shared_chinook(self):
        usa = self.files[
            r"Data\INI\Object\Specter\PatchSystems\Economy\CountrySupplyIncome\AmericaSupplyChinook_USA.ini"
        ].decode("latin1")
        shared = self.files[
            r"Data\INI\Object\Specter\United States Of America\Airforce\CH47F.ini"
        ].decode("latin1")
        self.assertIn("Object AmericaSupplyChinook_USA", usa)
        self.assertRegex(usa, r"MaxBoxes\s*=\s*40")
        self.assertRegex(shared, r"MaxBoxes\s*=\s*24")
        self.assertIn("Object AmericaVehicleChinook", shared)
        center = self.files[
            r"Data\INI\Object\Specter\United States Of America\Buildings\SupplyCenter.ini"
        ].decode("latin1")
        self.assertIn("SpawnTemplateName = AmericaSupplyChinook_USA", center)

    def test_russia_does_not_keep_china_truck_spawn(self):
        center = self.files[
            r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\SupplyCenter.ini"
        ].decode("latin1")
        self.assertIn("SpawnTemplateName = RussiaSupplyTruck_CountryIncome", center)
        self.assertNotIn("SpawnTemplateName = ChinaVehicleSupplyTruck", center)
        truck = self.files[
            r"Data\INI\Object\Specter\PatchSystems\Economy\CountrySupplyIncome\RussiaSupplyTruck_CountryIncome.ini"
        ].decode("latin1")
        self.assertRegex(truck, r"MaxBoxes\s*=\s*31")

    def test_spain_nato_center_uses_nato_chinook(self):
        center = self.files[r"Data\INI\Object\Specter\NATO\Buildings\SupplyCenter.ini"].decode(
            "latin1"
        )
        self.assertIn("SpawnTemplateName = NatoHelicopterCH47F", center)
        heli = self.files[r"Data\INI\Object\Specter\NATO\Rotary\CH47F.ini"].decode("latin1")
        self.assertRegex(heli, r"MaxBoxes\s*=\s*29")

    def test_builder_exists(self):
        self.assertTrue(BUILDER.is_file())

    def test_warehouse_starting_boxes_scaled_for_vpsb(self):
        expected = {
            "SupplyWarehouse": 3400 * 3,
            "SupplyDock": 5000 * 3,
            "SupplyPile": 350 * 3,
            "SupplyPileSmall": 150 * 3,
        }
        for obj, boxes in expected.items():
            name = (
                "Data\\INI\\Object\\Specter\\PatchSystems\\Economy\\CountrySupplyIncome\\"
                + obj
                + ".ini"
            )
            text = self.files[name].decode("latin1")
            m = re.search(r"StartingBoxes\s*=\s*(\d+)", text)
            self.assertEqual(int(m.group(1)), boxes, obj)

    def test_unique_workers_keep_seventy_five_dollar_trips(self):
        worker_files = [n for n in self.files if n.lower().endswith("worker.ini")]
        self.assertGreaterEqual(len(worker_files), 8)
        for name in worker_files:
            text = self.files[name].decode("latin1")
            boxes = [int(x) for x in re.findall(r"MaxBoxes\s*=\s*(\d+)", text)]
            self.assertTrue(boxes, name)
            self.assertTrue(all(b == 3 for b in boxes), (name, boxes))


if __name__ == "__main__":
    unittest.main()
