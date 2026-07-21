#!/usr/bin/env python3
"""Print computed price for hypothetical BaseCost without editing INIs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_dynamic_pricing import compute, load_tables  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--side", required=True)
    ap.add_argument("--base-cost", type=float, required=True)
    ap.add_argument("--base-time", type=float, default=10.0)
    ap.add_argument("--origin", default="Licensed")
    ap.add_argument("--tech", default="Standard")
    ap.add_argument("--category", default="Vehicle")
    ap.add_argument("--upgrade", action="store_true")
    args = ap.parse_args()
    tables = load_tables()
    meta = {
        "Origin": args.origin,
        "TechClass": args.tech,
        "Category": args.category,
        "Side": args.side,
    }
    cost, time, detail = compute(
        args.base_cost, args.base_time, args.side, meta, tables, args.upgrade
    )
    print(f"FinalCost={cost} FinalTime={time} detail={detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
