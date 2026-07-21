#!/usr/bin/env python3
"""Multiplayer sync audit for Specter patch INIs.

Exit 0 = clean. Exit 1 = findings that must be fixed before content PRs.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # patch/
INI = ROOT / "Data" / "INI"

SKIP_OBJ = re.compile(
    r"(Damaged|Debris|Hulk|Lock|Projectile|WeaponObject|FireControl|Explosion|Cloud)",
    re.I,
)


def collect(keyword: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = defaultdict(list)
    rx = re.compile(rf"^{keyword}\s+(\S+)\s*$", re.M)
    for p in INI.rglob("*.ini"):
        text = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        for m in rx.finditer(text):
            found[m.group(1)].append(rel)
    return found


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for kind in (
        "Object",
        "Upgrade",
        "Science",
        "CommandSet",
        "CommandButton",
        "PlayerTemplate",
        "Weapon",
    ):
        d = collect(kind)
        for name, files in sorted(d.items()):
            if len(files) > 1:
                errors.append(f"DUPLICATE {kind} {name}: {files}")

    # Dual BuildCost in one Object
    for p in (INI / "Object").rglob("*.ini"):
        text = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        for part in re.split(r"(?=^Object )", text, flags=re.M):
            if not part.startswith("Object "):
                continue
            name = part.split("\n", 1)[0].replace("Object ", "").strip()
            costs = re.findall(r"^\s*BuildCost\s*=", part, re.M)
            times = re.findall(r"^\s*BuildTime\s*=", part, re.M)
            if len(costs) > 1 or len(times) > 1:
                errors.append(f"DUAL COST/TIME {name} in {rel} (BuildCost×{len(costs)} BuildTime×{len(times)})")

    # Gameplay Random* (exclude RandomBone cosmetic and comments)
    rnd = re.compile(
        r"^\s*(RandomValue|RandomDelay|RandomDuration|RandomRange|RandomNumber)\s*=",
        re.M | re.I,
    )
    for p in INI.rglob("*.ini"):
        text = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        for m in rnd.finditer(text):
            line = text[: m.start()].count("\n") + 1
            errors.append(f"RANDOM FIELD {rel}:{line} {m.group(0).strip()}")

    # Player CommandSets constructing *_AI units
    ai_btn = re.compile(
        r"^\s*\d+\s*=\s*(Command_Construct\S*_AI)\s*$",
        re.M,
    )
    for p in INI.glob("CommandSet*.ini"):
        text = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        # Split CommandSets; flag non-comment AI constructs
        for m in ai_btn.finditer(text):
            # allow if line commented
            line = text[: m.start()].count("\n") + 1
            raw = text.splitlines()[line - 1]
            if raw.lstrip().startswith(";"):
                continue
            errors.append(f"PLAYER AI CONSTRUCT {rel}:{line} {m.group(1)}")

    # Archive modification guard: patch tools must not write outside patch/
    for p in ROOT.parent.glob("Data.zip"):
        warnings.append("Vendor archive present at repo root (must remain unmodified): Data.zip")
        break

    print("Specter Patch sync_audit")
    print(f"  errors={len(errors)} warnings={len(warnings)}")
    for e in errors:
        print("  ERROR:", e)
    for w in warnings:
        print("  WARN:", w)

    if errors:
        print("FAIL — see patch/SYNC_CHECKLIST.md")
        return 1
    print("PASS — deterministic ID/cost/command checks clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
