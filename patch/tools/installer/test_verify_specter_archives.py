#!/usr/bin/env python3
"""Static tests for SPECTER installer archive validation.

Does not run Install_SpecterPatch.bat or Launch_Specter.bat. cmd.exe is
not available on this host. These tests cover the shared policy encoded
in Verify_SpecterArchives.bat and the Python replica.
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from verify_specter_archives import (
    LOAD_ORDER,
    OVERLAY_NAME,
    OVERLAY_PATH,
    REQUIRED_ORDER,
    VERIFY_BAT,
    check_dir,
    check_one,
    hashes_from_spec_manifest,
    hashes_from_verify_bat,
    leftover_cannot_conceal_missing_source,
    sha256_file,
)

INSTALLER_DIR = Path(__file__).resolve().parent


class TestAuthoritativeHashes(unittest.TestCase):
    def test_verify_bat_lists_all_four(self):
        found = hashes_from_verify_bat()
        self.assertEqual(set(found), set(REQUIRED_ORDER))

    def test_spec_hashes_match_manifest_not_size_only(self):
        bat = hashes_from_verify_bat()
        man = hashes_from_spec_manifest()
        for name in ("_SPEC_DATA_ONE.big", "_SPEC_ART_ONE.big", "_SPEC_ART_TWO.big"):
            self.assertEqual(bat[name][1], man[name], name)
            self.assertNotEqual(bat[name][1], "")

    def test_overlay_hash_matches_file_bytes(self):
        bat = hashes_from_verify_bat()
        self.assertTrue(OVERLAY_PATH.is_file())
        self.assertEqual(bat[OVERLAY_NAME][0], OVERLAY_PATH.stat().st_size)
        self.assertEqual(bat[OVERLAY_NAME][1], sha256_file(OVERLAY_PATH))
        self.assertEqual(
            bat[OVERLAY_NAME][1],
            "a2558dd5ccea23b55189d96698a42a4ac91b82455db27b0d7511a366ea4b129d",
        )

    def test_sizes_match_known_official_values(self):
        bat = hashes_from_verify_bat()
        self.assertEqual(bat["_SPEC_DATA_ONE.big"][0], 373898957)
        self.assertEqual(bat["_SPEC_ART_ONE.big"][0], 2144972013)
        self.assertEqual(bat["_SPEC_ART_TWO.big"][0], 307254782)
        self.assertEqual(bat[OVERLAY_NAME][0], 1608985)


class TestInstallerAndLauncherWiring(unittest.TestCase):
    def setUp(self):
        self.install = (INSTALLER_DIR / "Install_SpecterPatch.bat").read_text(
            encoding="utf-8"
        )
        self.launch = (INSTALLER_DIR / "Launch_Specter.bat").read_text(
            encoding="utf-8"
        )
        self.verify = VERIFY_BAT.read_text(encoding="utf-8")

    def test_shared_verifier_exists_and_requires_certutil(self):
        self.assertTrue(VERIFY_BAT.is_file())
        self.assertIn("where certutil", self.verify)
        self.assertIn("SHA-256 integrity checks cannot be skipped", self.verify)
        self.assertNotIn("COMPLETED SUCCESSFULLY", self.verify)

    def test_both_scripts_call_verifier_on_source_then_dest(self):
        for label, txt in (("install", self.install), ("launch", self.launch)):
            with self.subTest(label=label):
                self.assertIn("Verify_SpecterArchives.bat", txt)
                src = txt.find('call "%VERIFY%" "%PATCH_DIR%"')
                dst = txt.find('call "%VERIFY%" "%GAME_ROOT%"')
                self.assertGreaterEqual(src, 0, "source verify missing")
                self.assertGreaterEqual(dst, 0, "dest verify missing")
                self.assertLess(src, dst)
                success = max(
                    txt.find("COMPLETED SUCCESSFULLY"),
                    txt.find("SUCCESS: Game launch"),
                )
                self.assertGreater(success, dst)

    def test_art_two_is_required_source_not_optional(self):
        for label, txt in (("install", self.install), ("launch", self.launch)):
            with self.subTest(label=label):
                self.assertIn("A leftover _SPEC_ART_TWO.big beside generals.exe is not enough", txt)
                self.assertIn('Copying _SPEC_ART_TWO.big', txt)
                self.assertNotIn(
                    "if exist \"%PATCH_DIR%_SPEC_ART_TWO.big\" (",
                    txt,
                )

    def test_copy_failures_exit_nonzero_before_success(self):
        for label, txt in (("install", self.install), ("launch", self.launch)):
            with self.subTest(label=label):
                self.assertIn("if errorlevel 1", txt)
                self.assertIn("Failed to copy", txt)
                # four copy /Y of the required names
                for name in REQUIRED_ORDER:
                    self.assertIn(f'copy /Y "%PATCH_DIR%{name}"', txt)

    def test_active_big_list_is_complete_and_game_root(self):
        for label, txt in (("install", self.install), ("launch", self.launch)):
            with self.subTest(label=label):
                for name in REQUIRED_ORDER:
                    self.assertIn(f"%GAME_ROOT%{name}", txt)
                self.assertIn("0_SPECTER_NatoSpainDisplay.big", txt)
                self.assertIn("_SPEC_ART_ONE.big", txt)
                self.assertIn("_SPEC_ART_TWO.big", txt)
                self.assertIn("_SPEC_DATA_ONE.big", txt)

    def test_load_order_comment_matches_stricmp(self):
        names = list(LOAD_ORDER)
        self.assertEqual(names, sorted(names, key=str.lower))
        self.assertEqual(names[0], OVERLAY_NAME)
        self.assertLess(ord("0"), ord("_"))


class TestValidationCases(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="specter_verify_"))
        self.src = self.tmp / "src"
        self.dst = self.tmp / "dst"
        self.src.mkdir()
        self.dst.mkdir()
        self.overlay = OVERLAY_PATH.read_bytes()
        self.overlay_sha = sha256_file(OVERLAY_PATH)
        self.overlay_size = len(self.overlay)
        # Tiny stand-ins for SPEC files so tests do not copy 2GB archives.
        self.fake_required = {
            "_SPEC_DATA_ONE.big": (8, sha256_file_bytes(b"dataone!")),
            "_SPEC_ART_ONE.big": (8, sha256_file_bytes(b"art_one!")),
            "_SPEC_ART_TWO.big": (8, sha256_file_bytes(b"art_two!")),
            OVERLAY_NAME: (self.overlay_size, self.overlay_sha),
        }

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, folder: Path, name: str, data: bytes):
        (folder / name).write_bytes(data)

    def _write_valid_fakes(self, folder: Path):
        self._write(folder, "_SPEC_DATA_ONE.big", b"dataone!")
        self._write(folder, "_SPEC_ART_ONE.big", b"art_one!")
        self._write(folder, "_SPEC_ART_TWO.big", b"art_two!")
        self._write(folder, OVERLAY_NAME, self.overlay)

    def test_missing_source_fails(self):
        self._write_valid_fakes(self.src)
        (self.src / "_SPEC_ART_TWO.big").unlink()
        errs = check_dir(self.src, self.fake_required)
        self.assertTrue(any("ART_TWO" in e for e in errs))

    def test_truncated_source_fails(self):
        self._write_valid_fakes(self.src)
        (self.src / "_SPEC_ART_ONE.big").write_bytes(b"short")
        errs = check_dir(self.src, self.fake_required)
        self.assertTrue(any("size" in e and "ART_ONE" in e for e in errs))

    def test_wrong_hash_same_size_fails(self):
        self._write_valid_fakes(self.src)
        (self.src / "_SPEC_DATA_ONE.big").write_bytes(b"DATAone!")
        self.assertEqual((self.src / "_SPEC_DATA_ONE.big").stat().st_size, 8)
        errs = check_dir(self.src, self.fake_required)
        self.assertTrue(any("sha256" in e for e in errs))

    def test_truncated_destination_leftover_fails(self):
        self._write_valid_fakes(self.dst)
        (self.dst / "_SPEC_ART_TWO.big").write_bytes(b"tiny")
        errs = check_dir(self.dst, self.fake_required)
        self.assertTrue(any("ART_TWO" in e for e in errs))

    def test_valid_complete_dir_passes_fakes_plus_real_overlay(self):
        self._write_valid_fakes(self.src)
        self.assertEqual(check_dir(self.src, self.fake_required), [])
        self.assertIsNone(
            check_one(OVERLAY_PATH, self.overlay_size, self.overlay_sha)
        )

    def test_dest_leftover_does_not_conceal_missing_source(self):
        self._write_valid_fakes(self.dst)
        (self.src / "_SPEC_DATA_ONE.big").write_bytes(b"dataone!")
        (self.src / "_SPEC_ART_ONE.big").write_bytes(b"art_one!")
        (self.src / OVERLAY_NAME).write_bytes(self.overlay)
        # ART_TWO missing from source, present and valid in dest.
        self.assertTrue(
            leftover_cannot_conceal_missing_source(
                self.src, self.dst, self.fake_required
            )
        )
        self.assertEqual(check_dir(self.dst, self.fake_required), [])
        self.assertTrue(check_dir(self.src, self.fake_required))

    def test_overlay_file_not_modified_by_this_package(self):
        self.assertEqual(
            sha256_file(OVERLAY_PATH),
            "a2558dd5ccea23b55189d96698a42a4ac91b82455db27b0d7511a366ea4b129d",
        )


def sha256_file_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


if __name__ == "__main__":
    unittest.main()
