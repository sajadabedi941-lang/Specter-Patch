#!/usr/bin/env python3
"""Backward-compatible entry point → Country Balance System.

Central config: patch/Data/INI/CountryBalance.ini
Prefer: python3 patch/tools/economy/apply_country_balance.py
"""

from apply_country_balance import main

if __name__ == "__main__":
    raise SystemExit(main())
