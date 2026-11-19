#!/usr/bin/env python3
"""Python replica of Verify_SpecterArchives.bat rules for tests.

Windows installs use the .bat + certutil. This module does not claim to
execute those bats. It encodes the same size/SHA-256 policy so missing,
truncated, leftover, and wrong-hash cases can be checked here.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

INSTALLER_DIR = Path(__file__).resolve().parent
VERIFY_BAT = INSTALLER_DIR / "Verify_SpecterArchives.bat"
SPEC_MANIFEST = INSTALLER_DIR.parents[2] / "SPECTER_SPEC_ART_DATA.SHA256.txt"
OVERLAY_NAME = "0_SPECTER_NatoSpainDisplay.big"
OVERLAY_PATH = INSTALLER_DIR / OVERLAY_NAME

REQUIRED_ORDER = (
    "_SPEC_DATA_ONE.big",
    "_SPEC_ART_ONE.big",
    "_SPEC_ART_TWO.big",
    OVERLAY_NAME,
)

# First-wins named files: engine registers *.big with _stricmp.
LOAD_ORDER = (
    OVERLAY_NAME,
    "_SPEC_ART_ONE.big",
    "_SPEC_ART_TWO.big",
    "_SPEC_DATA_ONE.big",
)

CHECK_ONE_RE = re.compile(
    r'call :CHECK_ONE "%DIR%([^"]+)" (\d+) ([0-9a-f]{64})',
    re.I,
)


def hashes_from_verify_bat(text: str | None = None) -> dict[str, tuple[int, str]]:
    blob = VERIFY_BAT.read_text(encoding="utf-8") if text is None else text
    found = {}
    for name, size, sha in CHECK_ONE_RE.findall(blob):
        found[name] = (int(size), sha.lower())
    return found


def hashes_from_spec_manifest() -> dict[str, str]:
    out = {}
    for line in SPEC_MANIFEST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sha, name = line.split()
        out[name] = sha.lower()
    return out


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_one(path: Path, exp_size: int, exp_sha: str) -> str | None:
    """Return an error string, or None if the file matches."""
    if not path.is_file():
        return f"missing {path.name}"
    got_size = path.stat().st_size
    if got_size != exp_size:
        return f"size {got_size} != {exp_size} for {path.name}"
    got_sha = sha256_file(path)
    if got_sha.lower() != exp_sha.lower():
        return f"sha256 mismatch for {path.name}"
    return None


def check_dir(directory: Path, required: dict[str, tuple[int, str]] | None = None) -> list[str]:
    required = required or hashes_from_verify_bat()
    errors = []
    for name in REQUIRED_ORDER:
        exp_size, exp_sha = required[name]
        err = check_one(directory / name, exp_size, exp_sha)
        if err:
            errors.append(err)
    return errors


def leftover_cannot_conceal_missing_source(
    source_dir: Path, dest_dir: Path, required: dict[str, tuple[int, str]] | None = None
) -> bool:
    """True when dest leftovers must not make a missing source look complete."""
    src_err = check_dir(source_dir, required)
    return bool(src_err)
