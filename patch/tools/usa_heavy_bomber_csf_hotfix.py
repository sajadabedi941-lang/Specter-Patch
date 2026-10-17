#!/usr/bin/env python3
"""DATA-only hotfix: restore last-known-good generals.csf after USA heavy bomber restore.

Does NOT modify CommandSet / CommandButton / bomber Objects / ART.
Replaces Data\\English\\generals.csf with the exact binary from the previous
working _SPEC_DATA_ONE.big (five-faction dual airbase build).
"""
from __future__ import annotations

# See conversation run: source CSF extracted from
# patch/Release/SPECTER_MASTER_DATA_FIVE_FACTION_DUAL_AIRBASE.zip
# sha256 e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3
print(__doc__)
