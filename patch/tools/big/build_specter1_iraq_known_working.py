#!/usr/bin/env python3
"""Accepted SPECTER1 known-working DATA baseline fingerprint.

Baseline is the _SPEC_DATA_ONE.big from SPECTER1.part001-069
extracted into the game root next to Launch_Specter.bat / generals.exe.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

EXPECT = "9629b6a092aaffb606a01af70e29b88d6c38c8dfc0958fe2d4c3a32c8d1da635"
SRC = Path("/tmp/SPECTER1_LOCKED_BASELINE/_SPEC_DATA_ONE.big")


def main() -> int:
    raw = SRC.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECT:
        raise SystemExit(f"BASELINE HASH MISMATCH {sha}")
    print("SOURCE_BASELINE = SPECTER1_PART001_TO_PART069")
    print("SPECTER1_DATA_BYTES", len(raw))
    print("SPECTER1_DATA_SHA256", sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
