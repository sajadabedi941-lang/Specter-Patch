#!/usr/bin/env python3
"""Validate every Turkey_* Object for crash-level missing references."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Data" / "INI"
TURKEY = DATA / "Object" / "Specter" / "Turkey Armed Forces"
OUT = ROOT / "Release" / "TURKEY_FACTION_FULL_RESET" / "VALIDATION_REPORT.txt"

SKIP_WEAPONS = {"None", "NONE", "End", "ExclusiveWeaponDelay", ";ExclusiveWeaponDelay"}


def load_defs():
    weapons, objects = set(), set()
    for p in DATA.rglob("*.ini"):
        text = p.read_text(encoding="utf-8", errors="replace")
        weapons |= set(re.findall(r"^Weapon\s+(\S+)", text, re.M))
        objects |= set(re.findall(r"^Object\s+(\S+)", text, re.M))
    return weapons, objects


def main() -> int:
    weapons, objects = load_defs()
    issues = []
    turkey_objs = []

    for p in sorted(TURKEY.rglob("*.ini")):
        text = p.read_text(encoding="utf-8", errors="replace")
        for obj in re.findall(r"^Object\s+(\S+)", text, re.M):
            turkey_objs.append(obj)
        for w in re.findall(r"^\s*Weapon\s*=\s*\S+\s+(\S+)", text, re.M):
            if w in SKIP_WEAPONS:
                continue
            if w not in weapons:
                issues.append(("MISSING_WEAPON", w, str(p.relative_to(ROOT))))
        for o in re.findall(r"^\s*ProjectileObject\s*=\s*(\S+)", text, re.M):
            if o not in ("None", "NONE") and o not in objects:
                issues.append(("MISSING_PROJECTILE_OBJECT", o, str(p.relative_to(ROOT))))
        for o in re.findall(r"^\s*Object\s*=\s*(\S+)", text, re.M):
            if o not in objects:
                issues.append(("MISSING_PREREQ_OBJECT", o, str(p.relative_to(ROOT))))

    for name in ["Weapon_Turkey.ini", "Weapon_VerificationFixes.ini", "ObjectCreationList_Turkey.ini"]:
        p = DATA / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for o in re.findall(r"^\s*ProjectileObject\s*=\s*(\S+)", text, re.M):
            if o not in ("None", "NONE") and o not in objects:
                issues.append(("MISSING_WEAPON_PROJECTILE", o, name))
        for o in re.findall(r"^\s*Transport\s*=\s*(\S+)", text, re.M):
            if o not in objects:
                issues.append(("MISSING_OCL_TRANSPORT", o, name))
        for o in re.findall(r"^\s*Payload\s*=\s*(\S+)", text, re.M):
            if o not in objects:
                issues.append(("MISSING_OCL_PAYLOAD", o, name))

    # Key aircraft identity
    key = {
        "Turkey_F16Block70": "Airforce/Turkey_F16Block70.ini",
        "Turkey_F16V": "Airforce/Turkey_F16V.ini",
        "Turkey_TB2": "Airforce/Turkey_TB2.ini",
        "Turkey_Akinci": "Airforce/Turkey_Akinci.ini",
        "Turkey_Kizilelma": "Drones/Turkey_Kizilelma.ini",
        "Turkey_Tu-22M3": "Airforce/Turkey_Tu-22M3.ini",
    }
    key_lines = []
    for obj, rel in key.items():
        p = TURKEY / rel
        text = p.read_text(encoding="utf-8", errors="replace")
        objs = re.findall(r"^Object\s+(\S+)", text, re.M)
        ws = re.findall(r"^\s*Weapon\s*=\s*\S+\s+(\S+)", text, re.M)
        side = re.findall(r"^\s*Side\s*=\s*(\S+)", text, re.M)
        ok = obj in objs and all(s == "Turkey" for s in side) and all(w in weapons for w in ws)
        key_lines.append(f"  {'PASS' if ok else 'FAIL'} {obj}: objects={objs} side={side} weapons={ws}")

    wo_objs = re.findall(
        r"^Object\s+(\S+)",
        (TURKEY / "Turkey_WeaponObjects.ini").read_text(encoding="utf-8", errors="replace"),
        re.M,
    )
    proj_objs = []
    for p in (TURKEY / "Projectiles").glob("*.ini"):
        proj_objs.extend(re.findall(r"^Object\s+(\S+)", p.read_text(encoding="utf-8", errors="replace"), re.M))

    lines = [
        "TURKEY FACTION FULL RESET — VALIDATION REPORT",
        f"Turkey Objects defined: {len(turkey_objs)}",
        f"Turkey_WeaponObjects Objects remaining: {len(wo_objs)} (want 0)",
        f"Projectiles Objects remaining: {len(proj_objs)} (want 0)",
        "",
        "KEY AIRCRAFT:",
        *key_lines,
        "",
        f"CRASH-LEVEL ISSUES: {len(issues)}",
    ]
    for kind, name, path in issues:
        lines.append(f"  {kind}: {name} <- {path}")
    if not issues and not wo_objs and not proj_objs:
        lines.append("")
        lines.append("RESULT: PASS — no missing Weapon/ProjectileObject/Prereq/OCL refs for Turkey reset scope.")
    else:
        lines.append("")
        lines.append("RESULT: FAIL")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))
    return 0 if (not issues and not wo_objs and not proj_objs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
