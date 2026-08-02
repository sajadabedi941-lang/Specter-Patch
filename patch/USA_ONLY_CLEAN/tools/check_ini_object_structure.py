#!/usr/bin/env python3
"""Structural INI check for Specter/ZH Object files (End nesting + Object headers)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

OBJECT_START = re.compile(r"^Object\s+(\S+)\s*$")
BLOCK_START = re.compile(
    r"^(Draw|Behavior|WeaponSet|ArmorSet|Prerequisites|UnitSpecificSounds|"
    r"ConditionState|DefaultConditionState|TransitionState|Body|"
    r"AttackAreaDecal|TargetingReticleDecal|ClientUpdate|ReplaceModule|AddModule)\b"
)


def check_file(path: Path) -> list[str]:
    lines = path.read_text(errors="replace").splitlines()
    stack: list[tuple[str, int, str]] = []
    errors: list[str] = []
    objects: list[str] = []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if not s or s.startswith(";"):
            continue
        om = OBJECT_START.match(s)
        if om:
            if any(k == "Object" for k, _, _ in stack):
                errors.append(
                    f"L{i}: Object {om.group(1)} while unclosed {[(a, b) for a, b, _ in stack]}"
                )
            objects.append(om.group(1))
            stack = [("Object", i, om.group(1))]
            continue
        bm = BLOCK_START.match(s)
        if bm:
            stack.append((bm.group(1), i, s[:90]))
            continue
        if s == "End":
            if not stack:
                errors.append(f"L{i}: stray End")
            else:
                stack.pop()
            continue
        # orphan Weapon= not under WeaponSet / FireWeapon* Behavior
        if re.match(r"^Weapon\s*=", s):
            if not any(k in ("WeaponSet", "Behavior") for k, _, _ in stack):
                errors.append(f"L{i}: Weapon= outside WeaponSet/Behavior: {s}")
    if stack:
        errors.append(f"EOF: unclosed blocks {[(a, b, c) for a, b, c in stack]}")
    # duplicates
    seen = {}
    for name in objects:
        seen[name] = seen.get(name, 0) + 1
    for name, n in seen.items():
        if n > 1:
            errors.append(f"duplicate Object {name} x{n}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    args = ap.parse_args()
    rc = 0
    for p in args.paths:
        errs = check_file(p)
        if errs:
            rc = 1
            print(f"FAIL {p}")
            for e in errs:
                print(" -", e)
        else:
            print(f"PASS {p}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
