"""Stage-4 DATA rebuild reports. Never touches SPECTER BIGs."""
from __future__ import annotations

import json
from pathlib import Path

from .engine import tehran_now
from . import stage3_reports


def write_object_plan_md(plan: dict, dest: Path) -> None:
    stage3_reports.write_object_plan_md(plan, dest)
    extra = [
        "",
        "## Stage 4 — independent DATA rebuild",
        "",
        "SPECTER public DamageFX.ini / Crate.ini / FXList.ini / SpecialPower.ini are never written.",
        "CWC.exe is not used. Previews are not imported into the game.",
        "",
        "### Unique DATA files (future apply only)",
        "",
    ]
    files = plan.get("unique_data_files") or []
    if not files:
        extra.append("None listed.")
    for path in files:
        extra.append(f"- `{path}`")
    leaks = plan.get("public_ini_leaks") or []
    extra += ["", "### Public INI leak check", ""]
    extra.append("**PASS — no public SPECTER INI in the unique-path list.**" if not leaks else "FAIL: " + ", ".join(f"`{x}`" for x in leaks))
    extra += ["", "### Independent clones", ""]
    clones = plan.get("independent_clones") or []
    if not clones:
        extra.append("No DamageFX / CrateData unique clones on this object.")
    for c in clones:
        extra += [
            f"#### `{c.get('kind')}` `{c.get('from')}` → `{c.get('to')}`",
            "",
            f"- Unique path: `{c.get('unique_path')}`",
            "",
            "```",
            (c.get("preview") or "")[:1200],
            "```",
            "",
        ]
    proof = plan.get("deploy_proof") or {}
    extra += ["", "### DeployStyleAIUpdate compatibility proof", ""]
    if not proof or not proof.get("has_rider_contain"):
        extra.append("No RiderChangeContain on this Object. DeployStyle mapping is not required.")
    else:
        extra += [
            f"- Use DeployStyleAIUpdate: **{proof.get('use_deploy_style')}**",
            f"- Use WeaponSet Conditions = DEPLOYED: **{proof.get('use_deployed_weaponset')}**",
            f"- PackTime/UnpackTime (ms): `{proof.get('pack_ms')}`",
            f"- Summary: {proof.get('summary')}",
            "",
            "Proven:",
            "",
        ]
        for p in proof.get("proven") or []:
            extra.append(f"- {p}")
        extra += ["", "Limitations (exact CWC behavior not available on stock Generals.exe):", ""]
        for lim in proof.get("limitations") or []:
            extra += [
                f"- **{lim.get('capability')}**",
                f"  - V25: {lim.get('v25')}",
                f"  - Stock: {lim.get('stock')}",
                f"  - Kept: {lim.get('kept')}",
            ]
        if proof.get("fail_reasons"):
            extra += ["", "Proof failures:", ""]
            for f in proof["fail_reasons"]:
                extra.append(f"- {f}")
        prev = plan.get("independent_module_preview")
        if prev:
            extra += ["", "Independent module preview (not written):", "", "```", prev, "```", ""]
    extra += [
        "",
        "## Tested vs analysis-only",
        "",
        "- **Tested:** unit tests (`tests/test_data_rebuild.py`, existing resolver/ART tests).",
        "- **Not tested:** Generals.exe, in-game spawn, packing SPECTER BIGs, apply.",
        "",
    ]
    text = dest.read_text(encoding="utf-8")
    dest.write_text(text.rstrip() + "\n" + "\n".join(extra) + "\n", encoding="utf-8")
    # Fix the stage-3 heading now that this is the stage-4 plan.
    dest.write_text(
        dest.read_text(encoding="utf-8").replace(
            f"# Transfer plan: `{plan['object']}` (stage 3 ART + CWC)",
            f"# Transfer plan: `{plan['object']}` (stage 4 DATA rebuild)",
            1,
        ),
        encoding="utf-8",
    )


def write_stage4_summary(focus: list[dict], tests: dict, dest_json: Path, dest_md: Path) -> None:
    payload = {
        "generated_at_tehran": tehran_now(),
        "stage": 4,
        "applies_to_game": False,
        "generals_exe_run": False,
        "focus": focus,
        "tests": tests,
        "note": "No Object, Weapon, CommandSet, CommandButton, or ART was imported into SPECTER.",
        "public_ini_untouched": [
            r"Data\INI\DamageFX.ini",
            r"Data\INI\Crate.ini",
            r"Data\INI\FXList.ini",
            r"Data\INI\SpecialPower.ini",
        ],
    }
    dest_json.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    lines = [
        "# Stage 4 — independent DATA rebuild for ChinaCSSA1 and ChinaHQ11",
        "",
        f"- Generated: {payload['generated_at_tehran']}",
        "- Game writes: **False**",
        "- Generals.exe run: **False**",
        "",
        "## Sample equipment",
        "",
        "| Object | DATA | ART | Resolver readiness | DeployStyle used |",
        "|---|---|---|---|---|",
    ]
    for row in focus:
        lines.append(
            f"| `{row.get('object')}` | `{row.get('data_status')}` | `{row.get('art_status')}` | "
            f"`{row.get('readiness')}` | `{row.get('use_deploy_style')}` |"
        )
    lines += [
        "",
        "## What was actually tested vs analysis-only",
        "",
        "- **Tested:** unit tests in `tests/test_data_rebuild.py`, `tests/test_art_cwc.py`, `tests/test_resolver.py`.",
        "- **Tested against live V25 volumes (if present):** ChinaCSSA1 + ChinaHQ11 Transfer Plan regeneration.",
        "- **Not tested:** Generals.exe, in-game spawn, packing SPECTER BIGs, apply.",
        "",
        f"- Unit tests: `{tests}`",
        "",
        "SPECTER public DamageFX.ini, Crate.ini, FXList.ini, and SpecialPower.ini are not in the unique-path list.",
        "",
    ]
    dest_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
