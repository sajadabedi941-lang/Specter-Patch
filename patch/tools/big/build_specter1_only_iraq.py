#!/usr/bin/env python3
"""Fingerprint for SPECTER1.part001-069 DATA. Never use SPECTER.part001-054."""
from pathlib import Path
import hashlib

EXPECT = "9629b6a092aaffb606a01af70e29b88d6c38c8dfc0958fe2d4c3a32c8d1da635"
SRC = Path("/tmp/SPECTER1_ONLY_LOCKED/_SPEC_DATA_ONE.big")


def main() -> int:
    sha = hashlib.sha256(SRC.read_bytes()).hexdigest()
    if sha != EXPECT:
        raise SystemExit(f"BASELINE HASH MISMATCH {sha}")
    print("SOURCE_ARCHIVE = SPECTER1.part001.rar -> SPECTER1.part069.rar")
    print("OLD_SPECTER_PART001_TO_PART054_USED = NO")
    print("SPECTER1_DATA_SHA256", sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
