#!/usr/bin/env python3
"""Silent Death V25 → SPECTER SS1 sync engine. Original BIGs untouched. apply refused."""
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
        description="V25 → SPECTER sync engine (stage 5 experimental pack; original BIGs untouched)"
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
            "art-cwc",
            "data-rebuild",
            "pack-sample",
            "ss1-layout",
            "catalog",
            "preflight",
            "selftest",
            "apply",
        ],
        help="ss1-layout/catalog=SS1-rule engine; pack-sample=experimental copy only; apply is refused",
    )
    p.add_argument("--root", type=Path, default=ROOT, help="Specter-Patch repo root")
    p.add_argument("--object", help="Object name for plan-object")
    p.add_argument("--out", type=Path, help="experimental output directory for pack-sample")
    p.add_argument("--json", action="store_true", help="print JSON summary to stdout")
    args = p.parse_args(argv)

    if args.command == "selftest":
        import unittest

        suite = unittest.defaultTestLoader.discover(str(TOOL_DIR / "tests"), pattern="test_*.py")
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        return 0 if result.wasSuccessful() else 1

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
        from lib import archive as archive_mod
        from lib import cwc
        from lib.archive_index import ArchiveIndex
        from lib.art_index import ArtIndex
        from lib.resolver import Resolver

        vols = eng.find_volumes()
        zip_path = archive_mod.stage_volumes(vols, eng.v25_src)
        aidx = ArchiveIndex(zip_path, eng.cache)
        art = ArtIndex(zip_path, eng.cache)
        rules = json.loads((eng.data / "compatibility_rules.json").read_text(encoding="utf-8"))
        recipes = cwc.load_recipes(eng.data)
        plan = Resolver(eng, rules, aidx, art_index=art, cwc_recipes=recipes).plan_object(args.object)
        result = plan
    elif args.command == "art-cwc":
        result = eng.run_stage3()
    elif args.command == "data-rebuild":
        result = eng.run_stage4()
    elif args.command == "pack-sample":
        result = eng.run_stage5(out_dir=args.out)
    elif args.command == "resolve":
        result = eng.run_stage2()
    elif args.command in ("ss1-layout", "catalog", "preflight"):
        result = eng.run_compat_infra()
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
