"""Write stage-2 resolver reports. Never touches SPECTER BIGs."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

from .engine import tehran_now


def write_object_plan_md(plan: dict, dest: Path) -> None:
    lines = [
        f"# Transfer plan: `{plan['object']}`",
        "",
        f"- Generated: {tehran_now()}",
        f"- Found in V25 VFS: **{plan['found_in_vfs']}**",
        f"- Source: `{plan.get('source')}`",
        f"- Readiness: **{plan['readiness']}**",
        f"- Dest INI (future apply only): `{plan.get('dest_ini')}`",
        f"- Build buttons: {plan.get('build_buttons') or 'none found'}",
        f"- CommandSets holding those buttons: {plan.get('build_commandsets') or 'none found'}",
        f"- Action counts: `{plan.get('action_counts')}`",
        f"- Game writes: **{plan.get('applies_to_game')}**",
        "",
        "## Object meta",
        "",
        f"- Side: { (plan.get('meta') or {}).get('side') }",
        f"- SPECTER side map: { (plan.get('meta') or {}).get('specter_side') }",
        f"- Bucket: { (plan.get('meta') or {}).get('bucket') }",
        f"- KindOf: `{ (plan.get('meta') or {}).get('kindof') }`",
        "",
        "## Compatibility notes (reasoned from INI flags, not guessed)",
        "",
    ]
    notes = plan.get("compatibility_notes") or []
    if not notes:
        lines.append("None.")
    for n in notes:
        lines.append(f"- **{n.get('decision')}** `{n.get('rule')}`: {n.get('reason')}")
    lines += ["", "## Dependency actions", "", "| Kind | Name | Action | Planned | Reason | Source |", "|---|---|---|---|---|---|"]
    for d in plan.get("deps") or []:
        src = (d.get("source") or "")
        if len(src) > 80:
            src = src[:77] + "..."
        reason = (d.get("reason") or "").replace("|", "/")
        lines.append(
            f"| {d['kind']} | `{d['name']}` | {d['action']} | `{d['planned']}` | {reason} | `{src}` |"
        )
    recovered = [d for d in (plan.get("deps") or []) if d.get("archive_paths")]
    if recovered:
        lines += ["", "## Archive recoveries (in zip, not in parsed extract)", ""]
        for d in recovered:
            lines.append(f"- `{d['kind']}:{d['name']}` →")
            for p in d["archive_paths"]:
                lines.append(f"  - `{p}`")
    rw = plan.get("rewrite_map") or {}
    lines += ["", "## Planned rewrites (not applied)", ""]
    if not rw:
        lines.append("No RENAME_AND_REWRITE on this chain.")
    else:
        for a, b in rw.items():
            lines.append(f"- `{a}` → `{b}`")
        prev = (plan.get("rewritten_preview") or {}).get("rewritten_head")
        if prev:
            lines += ["", "```", prev, "```"]
    lines += ["", "This is a plan only. No Object/Weapon/CommandSet/ART was imported.", ""]
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(result: dict, reports: Path, stage1: dict | None) -> None:
    plans = result["plans"]
    summary = {
        "generated_at_tehran": tehran_now(),
        "stage": 2,
        "applies_to_game": False,
        "objects_planned": result["objects_planned"],
        "ready_transfer": result["ready_transfer"],
        "auto_fixable": result["auto_fixable"],
        "manual_rebuild": result["manual_rebuild"],
        "blocked": result["blocked"],
        "reuse_only": result["reuse_only"],
        "note": result["note"],
        "by_readiness": {
            r: [p["object"] for p in plans if p["readiness"] == r]
            for r in ("ready_transfer", "auto_fixable", "manual_rebuild", "blocked", "reuse_only")
        },
    }
    (reports / "RESOLVER_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    index = {
        "generated_at_tehran": tehran_now(),
        "items": [
            {
                "object": p["object"],
                "readiness": p["readiness"],
                "dest_ini": p.get("dest_ini"),
                "action_counts": p.get("action_counts"),
                "source": p.get("source"),
            }
            for p in plans
        ],
    }
    (reports / "RESOLVER_INDEX.json.gz").write_bytes(
        gzip.compress((json.dumps(index) + "\n").encode("utf-8"), 9)
    )
    lines = [
        "# Stage 2 resolver summary",
        "",
        f"- Generated: {summary['generated_at_tehran']}",
        f"- Objects planned: **{summary['objects_planned']}**",
        f"- Ready transfer (plan only): **{summary['ready_transfer']}**",
        f"- Auto-fixable (rename/recover): **{summary['auto_fixable']}**",
        f"- Manual rebuild / independent add: **{summary['manual_rebuild']}**",
        f"- Blocked: **{summary['blocked']}**",
        f"- Reuse SPECTER identical: **{summary['reuse_only']}**",
        "",
        summary["note"],
        "",
        "Ready is **not** the unique-name Object count from stage 1.",
        "",
    ]
    (reports / "RESOLVER_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if stage1:
        delta = {
            "generated_at_tehran": tehran_now(),
            "stage1": stage1,
            "stage2_resolver": {
                "ready_transfer": result["ready_transfer"],
                "auto_fixable": result["auto_fixable"],
                "manual_rebuild": result["manual_rebuild"],
                "blocked": result["blocked"],
                "reuse_only": result["reuse_only"],
            },
        }
        (reports / "DRY_RUN_DELTA.json").write_text(json.dumps(delta, indent=2) + "\n", encoding="utf-8")


def write_delta_md(stage1_dry: dict, stage2_dry: dict, resolver: dict, dest: Path) -> None:
    lines = [
        "# Dry-run stage 1 vs stage 2",
        "",
        f"- Generated: {tehran_now()}",
        "",
        "Stage 2 still runs the original dry-run classifier (body-hash collisions) so the scan is comparable.",
        "The resolver uses **effective gameplay fingerprints** and archive recovery; those counts are separate.",
        "",
        "## Dry-run object status",
        "",
        f"- Stage 1: `{stage1_dry.get('collisions')}` objects_scanned={stage1_dry.get('objects_scanned')}",
        f"- Stage 2: `{stage2_dry.get('collisions')}` objects_scanned={stage2_dry.get('objects_scanned')}",
        f"- Stage 1 incomplete sample size / missing kinds: `{stage1_dry.get('missing_refs')}`",
        f"- Stage 2 missing kinds: `{stage2_dry.get('missing_refs')}`",
        "",
        "## Why missing-ref counts can change",
        "",
        "- Stage 2 INI parser also records `FireSound`, `DeathFX`/`DamageFX`, embedded `PSys:`/`FXList:`, and behavior module names.",
        "- Dry-run still reports unresolved names as missing; the resolver then classifies them as REUSE_NATIVE, RECOVER_FROM_V25, or MANUAL_REBUILD.",
        "- No missing name was deleted just to turn the report green.",
        "",
        "## Resolver (not equal to unique_v25)",
        "",
        f"- ready_transfer: **{resolver.get('ready_transfer')}**",
        f"- auto_fixable: **{resolver.get('auto_fixable')}**",
        f"- manual_rebuild: **{resolver.get('manual_rebuild')}**",
        f"- blocked: **{resolver.get('blocked')}**",
        f"- reuse_only: **{resolver.get('reuse_only')}**",
        "",
    ]
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
