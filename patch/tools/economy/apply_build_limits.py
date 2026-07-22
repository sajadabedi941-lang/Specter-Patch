#!/usr/bin/env python3
"""Annotate MaxSimultaneousOfType + LinkKey on Objects by CategoryRule paths.

Uses GlobalBuildLimits_SpecterPatch.ini contract:
  AirDefense path → Patch_AirDefense = 10
  Artillery buildings → Patch_ArtillerySite = 6
  Missile / MLRS / ballistic → Patch_StrategicLauncher = 4

Does not touch Nuclear (keep Patch_Nuclear annotations).
Idempotent: updates existing Patch_* LinkKeys; injects if missing on Side blocks with BuildCost.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OBJECT_ROOT = ROOT / "Data" / "INI" / "Object"

RULES = [
    # (path substring, name regex, max, linkkey)
    ("/AirDefense Sites/", None, 10, "Patch_AirDefense"),
    ("/AirDefense/", None, 10, "Patch_AirDefense"),
    ("/Buildings/", r".*(D30|Howitzer|100mm|Cannon|M777|FireBase|Artillery).*", 6, "Patch_ArtillerySite"),
    ("/Wheeled/", r".*(TRG230|TRG300|TRLG230|Bora|BM-21|BM21|Sarab|Scud|R11|Alhussaien|MLRS|Kaplan).*", 4, "Patch_StrategicLauncher"),
    ("/Tracked/", r".*(MLRS|M270|Bm30).*", 4, "Patch_StrategicLauncher"),
    ("/Airforce/", r".*AWACS.*", 1, "Patch_SupportAircraft"),
    ("/Airforce/", r".*(Tanker|Transport).*", 2, "Patch_SupportAircraft"),
    ("/SupportAircraft/", r".*AWACS.*", 1, "Patch_SupportAircraft"),
    ("/SupportAircraft/", r".*(Tanker|Transport|E3G|A50).*", 2, "Patch_SupportAircraft"),
]

OBJ_RE = re.compile(r"^Object\s+(\S+)\s*$", re.M)
SIDE_RE = re.compile(r"Side\s*=\s*\S+")
COST_RE = re.compile(r"BuildCost\s*=")
# Note: do NOT skip names containing "Combat" alone — BuildVariations like
# Turkey_HISAR_A_Combat must receive the same LinkKey as the primary Object.
SKIP = re.compile(
    r"(Damaged|Debris|Hulk|Lock|Projectile|WeaponObject|FireControl|PackMode|CombatMode|TargetLock|"
    r"WarFactory|CommandCenter|SupplyCenter|PowerPlant|Airfield|AirBase|Barracks|MIC\b|RadarStation)",
    re.I,
)


def split_objects(text: str):
    ms = list(OBJ_RE.finditer(text))
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        yield m.start(), end, m.group(1), text[m.start() : end]


def match_rule(rel: str, name: str):
    rel_n = rel.replace("\\", "/")
    for path_sub, name_rx, mx, key in RULES:
        if path_sub not in rel_n:
            continue
        if name_rx and not re.search(name_rx, name, re.I):
            continue
        return mx, key
    # AirDefense units by HISAR/SIPER/Korkut/Sungur name anywhere under faction tree
    if re.search(r"(HISAR|SIPER|Korkut|Sungur|Roland|Fahad|SA-6|Sam8|ZSU|Pantsir|Tor)", name, re.I):
        if "/Airforce/" in rel_n or "/Infantry/" in rel_n:
            return None
        return 10, "Patch_AirDefense"
    return None


def annotate_block(block: str, mx: int, key: str) -> str:
    if not SIDE_RE.search(block) or not COST_RE.search(block):
        return block
    if SKIP.search(block.split("\n", 1)[0]):
        return block
    if "MaxSimultaneousLinkKey" in block:
        block = re.sub(
            r"MaxSimultaneousOfType\s*=\s*[^\n]+",
            f"MaxSimultaneousOfType = {mx}",
            block,
            count=1,
        )
        block = re.sub(
            r"MaxSimultaneousLinkKey\s*=\s*[^\n]+",
            f"MaxSimultaneousLinkKey = {key}  ; SPECTER PATCH global limit",
            block,
            count=1,
        )
        return block
    if re.search(r"MaxSimultaneousOfType\s*=", block):
        return re.sub(
            r"(MaxSimultaneousOfType\s*=\s*[^\n]+)",
            f"MaxSimultaneousOfType = {mx}\n  MaxSimultaneousLinkKey = {key}  ; SPECTER PATCH global limit",
            block,
            count=1,
        )
    return re.sub(
        r"(Side\s*=\s*\S+[^\n]*\n)",
        rf"\1  MaxSimultaneousOfType = {mx}\n  MaxSimultaneousLinkKey = {key}  ; SPECTER PATCH global limit\n",
        block,
        count=1,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--side-filter", help="Only files under folders containing this string")
    args = ap.parse_args()
    n = 0
    for path in OBJECT_ROOT.rglob("*.ini"):
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        if args.side_filter and args.side_filter not in rel:
            continue
        text = path.read_text(errors="replace")
        new = text
        for start, end, name, block in reversed(list(split_objects(text))):
            if SKIP.search(name):
                continue
            hit = match_rule(rel, name)
            if not hit:
                continue
            mx, key = hit
            nb = annotate_block(block, mx, key)
            if nb != block:
                new = new[:start] + nb + new[end:]
                n += 1
                print(f"  {name}: {key}={mx}")
        if new != text and not args.dry_run:
            path.write_text(new)
    print(f"Annotated {n} objects dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
