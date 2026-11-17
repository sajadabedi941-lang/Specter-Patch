"""Stage-3 ART/CWC reports. Never touches SPECTER BIGs."""
from __future__ import annotations

import json
from pathlib import Path

from .engine import tehran_now

STATUSES = (
    "READY_FOR_TRANSFER_PLAN",
    "AUTO_RECOVERABLE",
    "MANUAL_REBUILD",
    "BLOCKED",
)


def write_object_plan_md(plan: dict, dest: Path) -> None:
    lines = [
        f"# Transfer plan: `{plan['object']}` (stage 3 ART + CWC)",
        "",
        f"- Generated: {tehran_now()}",
        f"- Found in V25 VFS: **{plan['found_in_vfs']}**",
        f"- Source: `{plan.get('source')}`",
        f"- Resolver readiness: **{plan['readiness']}**",
        f"- DATA completeness: **{plan.get('data_status')}**",
        f"- ART completeness: **{plan.get('art_status')}**",
        f"- Dest INI (future apply only): `{plan.get('dest_ini')}`",
        f"- Build buttons: {plan.get('build_buttons') or 'none found'}",
        f"- CommandSets holding those buttons: {plan.get('build_commandsets') or 'none found'}",
        f"- Action counts: `{plan.get('action_counts')}`",
        f"- Game writes: **{plan.get('applies_to_game')}**",
        "",
        "## Object meta",
        "",
        f"- Side: {(plan.get('meta') or {}).get('side')}",
        f"- SPECTER side map: {(plan.get('meta') or {}).get('specter_side')}",
        f"- Bucket: {(plan.get('meta') or {}).get('bucket')}",
        f"- KindOf: `{(plan.get('meta') or {}).get('kindof')}`",
        "",
        "## Completeness",
        "",
        "DATA and ART are scored separately. Neither score imports anything into SPECTER.",
        "",
        "| Track | Status |",
        "|---|---|",
        f"| DATA | `{plan.get('data_status')}` |",
        f"| ART | `{plan.get('art_status')}` |",
        "",
        "## CWC / pack-unpack",
        "",
    ]
    cwc_rows = plan.get("cwc") or []
    if not cwc_rows:
        lines.append("No catalogued CWC module on this Object.")
    for row in cwc_rows:
        rebuild = row.get("rebuild") or {}
        lines += [
            f"### `{row.get('module')}`",
            "",
            f"- Origin: {row.get('origin')}",
            f"- SPECTER exe: {row.get('specter_exe')}",
            f"- What it does: {row.get('what_it_does')}",
            f"- Rebuild action: **{rebuild.get('action')}** (capability kept: {rebuild.get('keep_capability')})",
            f"- Keys: `{row.get('keys')}`",
            f"- Riders: `{row.get('riders')}`",
            "",
        ]
        for step in rebuild.get("specter_safe") or []:
            lines.append(f"- {step}")
        excerpt = row.get("block_excerpt")
        if excerpt:
            lines += ["", "```", excerpt, "```", ""]
    notes = plan.get("compatibility_notes") or []
    lines += ["", "## Compatibility notes (reasoned from INI flags, not guessed)", ""]
    if not notes:
        lines.append("None.")
    for n in notes:
        lines.append(f"- **{n.get('decision')}** `{n.get('rule')}`: {n.get('reason')}")
    lines += ["", "## Dependency actions", "", "| Kind | Name | Action | Planned | Reason | Source |", "|---|---|---|---|---|---|"]
    for d in plan.get("deps") or []:
        src = d.get("source") or ""
        if len(src) > 80:
            src = src[:77] + "..."
        reason = (d.get("reason") or "").replace("|", "/")
        lines.append(
            f"| {d['kind']} | `{d['name']}` | {d['action']} | `{d['planned']}` | {reason} | `{src}` |"
        )
    recovered = [d for d in (plan.get("deps") or []) if d.get("archive_paths") or d.get("art_locations")]
    if recovered:
        lines += ["", "## ART recoveries (exact stem; no similar-name substitute)", ""]
        for d in recovered:
            lines.append(f"- `{d['kind']}:{d['name']}` found_in=`{d.get('found_in')}`")
            for p in d.get("archive_paths") or []:
                lines.append(f"  - `{p}`")
            for loc in d.get("art_locations") or []:
                lines.append(
                    f"  - container=`{loc.get('container')}` file=`{loc.get('filename')}` "
                    f"source_big=`{loc.get('source_big')}` inner=`{loc.get('inner')}`"
                )
            if d.get("w3d_textures"):
                lines.append(f"  - W3D textures: {d['w3d_textures']}")
            if d.get("w3d_anims"):
                lines.append(f"  - W3D anims (inside model, not separate files): {d['w3d_anims']}")
    art_missing = [
        d
        for d in (plan.get("deps") or [])
        if d["kind"] == "ArtFile" and d["action"] in ("MANUAL_REBUILD", "BLOCKED")
    ]
    if art_missing:
        lines += ["", "## ART gaps (exact stem missing; not replaced)", ""]
        for d in art_missing:
            lines.append(f"- `{d['name']}`: {d.get('reason')}")
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


def write_stage3_summary(focus: list[dict], tests: dict, dest_json: Path, dest_md: Path) -> None:
    payload = {
        "generated_at_tehran": tehran_now(),
        "stage": 3,
        "applies_to_game": False,
        "generals_exe_run": False,
        "focus": focus,
        "tests": tests,
        "status_values": list(STATUSES),
        "note": "No Object, Weapon, CommandSet, CommandButton, or ART was imported into SPECTER.",
    }
    dest_json.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    lines = [
        "# Stage 3 — nested ART recovery and CWC rebuild plans",
        "",
        f"- Generated: {payload['generated_at_tehran']}",
        "- Game writes: **False**",
        "- Generals.exe run: **False**",
        "",
        "## Sample equipment",
        "",
        "| Object | DATA | ART | Resolver readiness |",
        "|---|---|---|---|",
    ]
    for row in focus:
        lines.append(
            f"| `{row.get('object')}` | `{row.get('data_status')}` | `{row.get('art_status')}` | `{row.get('readiness')}` |"
        )
    lines += [
        "",
        "## What was actually tested vs analysis-only",
        "",
        "- **Tested:** unit tests in `tests/test_art_cwc.py` and `tests/test_resolver.py` (nested BIG writer/index, exact-stem lookup, multi-texture W3D, missing ART, CWC inspect, shared ART, apply refused).",
        "- **Tested against live V25 volumes (if present):** ArtIndex of nested `WYS/Textures.big` / `WYS/W3D.big`, ChinaCSSA1 + ChinaHQ11 plan regeneration.",
        "- **Not tested:** Generals.exe, in-game spawn, packing SPECTER BIGs, apply.",
        "",
        f"- Unit tests: `{tests}`",
        "",
    ]
    dest_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
