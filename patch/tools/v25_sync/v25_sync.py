#!/usr/bin/env python3
"""Silent Death V25 → SPECTER sync engine (stage 2: resolve / plan; no game writes)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
ROOT = TOOL_DIR.parents[2]
sys.path.insert(0, str(TOOL_DIR))

from lib.engine import Engine  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="V25 → SPECTER sync engine (stage 2 resolve/dry-run; no game writes)"
    )
    p.add_argument(
        "command",
        choices=[
            "health",
            "extract",
            "inventory",
            "dry-run",
            "plan",
            "validate",
            "resolve",
            "plan-object",
            "selftest",
            "apply",
        ],
        help="resolve=full dependency resolver; apply is refused",
    )
    p.add_argument("--root", type=Path, default=ROOT, help="Specter-Patch repo root")
    p.add_argument("--object", help="Object name for plan-object")
    p.add_argument("--json", action="store_true", help="print JSON summary to stdout")
    args = p.parse_args(argv)

    if args.command == "selftest":
        from tests.test_resolver import main as tests_main

        return tests_main()

    eng = Engine(args.root.resolve())
    if args.command == "apply":
        eng.refuse_apply()
        return 2
    if args.command == "health":
        result = eng.health_report()
    elif args.command == "extract":
        root = eng.ensure_extract()
        result = {"extract_root": str(root), "lsf": (root / "00LSF0118.big").is_file()}
    elif args.command == "inventory":
        v25 = eng.inventory_v25()
        spec = eng.inventory_specter()
        result = {
            "v25_objects": len(v25.get("Object") or {}),
            "specter_objects": len(spec.get("Object") or {}),
            "v25_weapons": len(v25.get("Weapon") or {}),
            "specter_weapons": len(spec.get("Weapon") or {}),
        }
    elif args.command == "plan-object":
        if not args.object:
            p.error("--object is required for plan-object")
        from lib.archive_index import ArchiveIndex
        from lib.resolver import Resolver
        from lib import archive as archive_mod

        vols = eng.find_volumes()
        zip_path = archive_mod.stage_volumes(vols, eng.v25_src)
        aidx = ArchiveIndex(zip_path, eng.cache)
        rules = json.loads((eng.data / "compatibility_rules.json").read_text(encoding="utf-8"))
        plan = Resolver(eng, rules, aidx).plan_object(args.object)
        result = plan
    elif args.command == "resolve":
        result = eng.run_stage2()
    elif args.command in ("dry-run", "plan", "validate"):
        eng.health_report()
        result = eng.dry_run()
        result = {
            "mode": "dry-run",
            "game_bigs_modified": False,
            "objects": result["mapping_count"],
            "manifest": result["manifest"],
            "object_status": result["compat"]["object_status"],
            "incomplete_objects": result["compat"]["incomplete_objects"],
            "reports": str(eng.reports),
        }
    else:
        p.error("unknown command")
        return 2

    if args.json:
        print(json.dumps(result, indent=2, default=str)[:20000])
    else:
        print(json.dumps(result, indent=2, default=str)[:4000])
        print(f"\nReports: {eng.reports}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
