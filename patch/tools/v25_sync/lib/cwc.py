"""Inspect CWC / pack-unpack modules on a V25 Object. Planning only."""
from __future__ import annotations

import json
import re
from pathlib import Path

RIDER_RE = re.compile(r"^\s*(Rider\d+)\s*=\s*(.+)$", re.I | re.M)
KEY_RE = re.compile(
    r"^\s*(SpecialPowerTemplate|OCL|PackTime|UnpackTime|TurretsFunctionOnlyWhenDeployed|"
    r"TurretsMustCenterBeforePacking|ResetTurretBeforePacking|Slots|AllowInsideKindOf)\s*=\s*(.+)$",
    re.I | re.M,
)


def load_recipes(data_dir: Path) -> dict:
    return json.loads((data_dir / "cwc_rebuild.json").read_text(encoding="utf-8"))


def module_block(body: str, module: str) -> str:
    low = body.lower()
    needle = f"behavior = {module.lower()}"
    i = low.find(needle)
    if i < 0:
        return ""
    chunk = body[i:]
    # until a top-level End of this behavior: first \n  End after start
    lines = chunk.splitlines()
    out = [lines[0]]
    nest = 1
    for line in lines[1:]:
        t = line.strip().lower()
        if t.startswith("behavior =") and len(out) > 1:
            break
        if t == "end":
            nest -= 1
            out.append(line)
            if nest <= 0:
                break
            continue
        token = line.strip().split()[0].lower() if line.strip() else ""
        if token in ("turret", "altturret") and "=" not in line:
            nest += 1
        out.append(line)
    return "\n".join(out)


def inspect_object(rec: dict, recipes: dict) -> list[dict]:
    body = rec.get("body") or ""
    behaviors = rec.get("behaviors") or []
    found = []
    catalog = (recipes.get("modules") or {})
    for mod in behaviors:
        recipe = catalog.get(mod)
        block = module_block(body, mod)
        riders = [{"slot": m.group(1), "value": m.group(2).strip()} for m in RIDER_RE.finditer(block)]
        keys = {m.group(1): m.group(2).strip() for m in KEY_RE.finditer(block)}
        if recipe:
            row = {
                "module": mod,
                "origin": recipe.get("origin"),
                "specter_exe": recipe.get("specter_exe"),
                "what_it_does": recipe.get("what_it_does"),
                "keys": keys,
                "riders": riders,
                "rebuild": recipe.get("rebuild"),
                "block_excerpt": block[:600],
            }
        elif mod in ("DeployStyleAIUpdate",) or "pack" in mod.lower():
            row = {
                "module": mod,
                "origin": "unknown",
                "specter_exe": "review",
                "what_it_does": "Pack/unpack related module discovered in V25.",
                "keys": keys,
                "riders": riders,
                "rebuild": {
                    "action": "INDEPENDENT_ADD",
                    "keep_capability": "pack/unpack",
                    "specter_safe": ["Keep on unique Object INI; do not patch SPECTER AI tables."],
                },
                "block_excerpt": block[:600],
            }
        else:
            continue
        if recipe or riders or keys or mod in catalog:
            found.append(row)
    # Always include catalog modules present
    present = {f["module"] for f in found}
    for mod, recipe in catalog.items():
        if mod in behaviors and mod not in present:
            found.append(
                {
                    "module": mod,
                    "origin": recipe.get("origin"),
                    "specter_exe": recipe.get("specter_exe"),
                    "what_it_does": recipe.get("what_it_does"),
                    "keys": {},
                    "riders": [],
                    "rebuild": recipe.get("rebuild"),
                    "block_excerpt": module_block(body, mod)[:600],
                }
            )
    return found
