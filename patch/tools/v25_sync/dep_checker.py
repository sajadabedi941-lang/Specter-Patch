#!/usr/bin/env python3
"""Dependency checker for Silent Death V25 objects (read-only)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_DIR))

from lib.engine import Engine  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Walk V25 Object dependency chains")
    p.add_argument("object_name", nargs="?", help="Object name (omit to scan all via dry-run reports)")
    p.add_argument("--root", type=Path, default=TOOL_DIR.parents[2])
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    eng = Engine(args.root.resolve())
    v25 = eng.inventory_v25()
    if not args.object_name:
        print("Pass an Object name, or run: python3 v25_sync.py dry-run")
        print(f"Known Objects: {len(v25.get('Object') or {})}")
        return 0
    tree = eng.walk_deps("Object", args.object_name, v25)
    missing = eng.flatten_missing(tree)
    deps = {k: sorted(v) for k, v in eng.flatten_names(tree).items()}
    out = {
        "object": args.object_name,
        "found": not tree.get("missing"),
        "source": tree.get("source"),
        "missing": missing,
        "deps": deps,
        "art": tree.get("art") or [],
    }
    print(json.dumps(out, indent=2))
    return 0 if out["found"] and not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
