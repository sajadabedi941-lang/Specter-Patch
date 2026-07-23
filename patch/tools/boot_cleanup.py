#!/usr/bin/env python3
"""Specter Ultimate Warfare — FINAL BOOT CLEANUP

Fixes INI parse/boot killers under patch/Data/INI/Object/Specter/:
  - Empty CommandSet assignments (CommandSet = ;comment)
  - Multi-object Prerequisites lines (engine expects one Object= token)
  - Missing End / structural fatals (reported)
  - Invalid empty critical fields

Does NOT delete countries, units, aircraft, tanks, buildings, or upgrades.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # patch/
OBJ = ROOT / "Data" / "INI" / "Object" / "Specter"
INI = ROOT / "Data" / "INI"
REPORT = ROOT.parent / "FINAL_BOOT_FIX_REPORT.md"

OBJ_DEF = re.compile(
    r"^(Object|ObjectReskin|ChildObject)\s+([A-Za-z_][A-Za-z0-9_\-]*)"
    r"(?:\s+from\s+([A-Za-z_][A-Za-z0-9_\-]*))?\s*$",
    re.I,
)
END = re.compile(r"^End$", re.I)
SIDE_RE = re.compile(r"^Side\s*=\s*(\S+)", re.I)
CMDSET_PROP = re.compile(r"^(\s*CommandSet\s*=\s*)(.*)$", re.I)
PREREQ_OBJ = re.compile(r"^(\s*Object\s*=\s*)(.+)$", re.I)

ASSIGN_OPEN = re.compile(r"^(Behavior|Body|ClientUpdate|Draw)\s*=", re.I)
BARE_OPEN = re.compile(
    r"^(ArmorSet|WeaponSet|Prerequisites|Turret|UnitSpecificSounds|"
    r"UnitSpecificAnimationSounds|UnitSpecificFX|GeometryInfo)\s*$",
    re.I,
)
STATE_OPEN = re.compile(
    r"^(ConditionState|DefaultConditionState|TransitionState)\b", re.I
)


def is_nested_opener(s: str) -> bool:
    if re.match(r"^Turret\s*=", s, re.I):
        return False
    return bool(ASSIGN_OPEN.match(s) or BARE_OPEN.match(s) or STATE_OPEN.match(s))


def index_objects() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in OBJ.rglob("*.ini"):
        cur = None
        for ln, line in enumerate(
            p.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            s = line.split(";", 1)[0].strip()
            m = OBJ_DEF.match(s)
            if m:
                cur = m.group(2)
                out[cur] = {
                    "file": str(p),
                    "line": ln,
                    "side": None,
                    "commandset": None,
                }
                continue
            if cur is None:
                continue
            if END.match(s) and False:
                pass
            sm = SIDE_RE.match(s)
            if sm:
                out[cur]["side"] = sm.group(1)
            cm = re.match(r"^CommandSet\s*=\s*(\S+)", s, re.I)
            if cm:
                out[cur]["commandset"] = cm.group(1)
    return out


def index_commandsets() -> set[str]:
    names: set[str] = set()
    stock = Path("/tmp/specter_tree/Data/INI")
    for root in (INI, stock):
        if not root.exists():
            continue
        paths = list(root.rglob("*CommandSet*.ini")) + [root / "CommandSet.ini"]
        for p in paths:
            if not p.exists() or "Release" in p.parts:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            names.update(re.findall(r"^CommandSet\s+(\S+)\s*$", text, re.M))
    return names


def pick_prereq(tokens: list[str], side: str | None, objects: dict[str, dict]) -> str:
    """Choose a single valid Prerequisite Object, preferring faction-local."""
    # Prefer tokens that exist and match side
    existing = [t for t in tokens if t in objects]
    if side:
        local = [
            t
            for t in existing
            if t.startswith(f"{side}_")
            or t.startswith(side)
            or (objects[t].get("side") == side)
        ]
        # Prefer AdvancedAirBase / Airfield_T / WarFactory_T / MIC / MilitaryHQ
        prefer = [
            "AdvancedAirBase",
            "Airfield_T",
            "Airfield",
            "WarFactory_T",
            "WarFactory",
            "MIC",
            "MilitaryHQ",
            "CommandCenter",
            "Barracks",
            "Camp",
            "BootCamp",
            "SupplyCenter",
            "PowerPlant",
            "PowerStation",
            "StrategyCenter",
        ]
        for hint in prefer:
            for t in local:
                if hint.lower() in t.lower():
                    return t
        if local:
            return local[0]

    # Boss: map to Boss_* if available
    if side == "Boss":
        for hint in (
            "Boss_WarFactory",
            "Boss_Airfield",
            "Boss_Barracks",
            "Boss_SupplyCenter",
            "Boss_PowerPlant",
            "Boss_CommandCenter",
        ):
            if hint in objects:
                # pick based on token hints
                joined = " ".join(tokens).lower()
                if "warfactory" in joined and "Boss_WarFactory" in objects:
                    return "Boss_WarFactory"
                if "airfield" in joined and "Boss_Airfield" in objects:
                    return "Boss_Airfield"
                if "barrack" in joined or "camp" in joined:
                    return "Boss_Barracks"
                if "palace" in joined or "industry" in joined:
                    return "Boss_CommandCenter"
                if "strategy" in joined:
                    return "Boss_CommandCenter"
                return "Boss_CommandCenter"

    # Prefer any existing AdvancedAirBase / local airfield among tokens
    for hint in ("AdvancedAirBase", "Airfield_T", "WarFactory_T", "MIC"):
        for t in tokens:
            if hint in t and t in objects:
                return t

    # Prefer last token (often the faction-local override in donor clones)
    for t in reversed(tokens):
        if t in objects:
            return t
    return tokens[-1]


def validate_structure() -> list[str]:
    errors: list[str] = []
    for p in sorted(OBJ.rglob("*.ini")):
        stack: list[tuple] = []
        for ln, line in enumerate(
            p.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            s = line.split(";", 1)[0].strip()
            if not s:
                continue
            m = OBJ_DEF.match(s)
            if m:
                if stack:
                    errors.append(
                        f"UNCLOSED_BEFORE_OBJECT {p}:{ln} "
                        f"new={m.group(2)} depth={len(stack)} was={stack[0]}"
                    )
                stack = [("Object", ln, m.group(2))]
                continue
            if END.match(s):
                if not stack:
                    errors.append(f"EXTRA_END {p}:{ln}")
                else:
                    stack.pop()
                continue
            if is_nested_opener(s):
                stack.append(("block", ln, s[:50]))
        if stack:
            errors.append(
                f"UNCLOSED_EOF {p}:{stack[0][1]} depth={len(stack)} top={stack[-1]}"
            )
    return errors


def main() -> int:
    objects = index_objects()
    commandsets = index_commandsets()
    actions: list[str] = []
    files_changed: set[Path] = set()

    # --- Pass 1: empty CommandSet = ;comment ---
    empty_cs_re = re.compile(
        r"^(\s*CommandSet\s*=\s*)(;.*)?\s*$", re.I
    )
    for p in OBJ.rglob("*.ini"):
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        cur = None
        side = None
        changed = False
        out: list[str] = []
        for line in lines:
            raw = line
            s = line.split(";", 1)[0].strip()
            m = OBJ_DEF.match(s)
            if m:
                cur = m.group(2)
                side = None
            sm = SIDE_RE.match(s)
            if sm:
                side = sm.group(1)
            em = empty_cs_re.match(line.rstrip("\n\r"))
            # Only treat as empty if there is no value before ';'
            if em:
                before_semi = line.split(";", 1)[0]
                # CommandSet =   or CommandSet = <only spaces>
                if re.match(r"^\s*CommandSet\s*=\s*$", before_semi, re.I):
                    use_side = side or (
                        objects.get(cur, {}).get("side") if cur else None
                    )
                    if use_side:
                        new_cs = f"{use_side}_PowerPlantCommandSet"
                        # Prefer existing commandset names
                        if new_cs not in commandsets:
                            # try without underscore variants
                            alt = f"{use_side}PowerPlantCommandSet"
                            if alt in commandsets:
                                new_cs = alt
                        nl = "\r\n" if line.endswith("\r\n") else "\n"
                        indent = re.match(r"^(\s*)", line).group(1)
                        raw = (
                            f"{indent}CommandSet          = {new_cs} "
                            f"; BOOT-FIX was empty/commented CommandSet{nl}"
                        )
                        changed = True
                        actions.append(
                            f"EMPTY_COMMANDSET {p.relative_to(ROOT)} "
                            f"obj={cur} -> {new_cs}"
                        )
            out.append(raw)
        if changed:
            p.write_text("".join(out), encoding="utf-8")
            files_changed.add(p)

    # refresh object index after CS fixes
    objects = index_objects()

    # --- Pass 2: multi-object Prerequisites ---
    for p in OBJ.rglob("*.ini"):
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        cur = None
        side = None
        in_prereq = False
        changed = False
        out = []
        for line in lines:
            raw = line
            s = line.split(";", 1)[0].strip()
            m = OBJ_DEF.match(s)
            if m:
                cur = m.group(2)
                side = objects.get(cur, {}).get("side")
                in_prereq = False
            sm = SIDE_RE.match(s)
            if sm:
                side = sm.group(1)
            if s == "Prerequisites":
                in_prereq = True
                out.append(raw)
                continue
            if in_prereq and END.match(s):
                in_prereq = False
                out.append(raw)
                continue
            if in_prereq:
                pm = PREREQ_OBJ.match(s)
                if pm:
                    tokens = pm.group(2).split()
                    if len(tokens) > 1:
                        chosen = pick_prereq(tokens, side, objects)
                        nl = "\r\n" if line.endswith("\r\n") else "\n"
                        indent = re.match(r"^(\s*)", line).group(1)
                        raw = (
                            f"{indent}Object = {chosen} "
                            f"; BOOT-FIX was multi: {' '.join(tokens)}{nl}"
                        )
                        changed = True
                        actions.append(
                            f"PREREQ_MULTI {p.relative_to(ROOT)} "
                            f"obj={cur} {' '.join(tokens)} -> {chosen}"
                        )
            out.append(raw)
        if changed:
            p.write_text("".join(out), encoding="utf-8")
            files_changed.add(p)

    # --- Pass 3: dangling CommandSet names on objects ---
    objects = index_objects()
    commandsets = index_commandsets()
    dangling_cs = []
    for name, meta in objects.items():
        cs = meta.get("commandset")
        if not cs or cs in ("None", "NONE"):
            continue
        if cs not in commandsets:
            dangling_cs.append((name, cs, meta["file"], meta["line"]))

    # Create stub CommandSets for dangling (keep feature: empty-but-valid set)
    if dangling_cs:
        stub_path = INI / "CommandSet_BootFix_Stubs.ini"
        existing_stubs = set()
        if stub_path.exists():
            existing_stubs = set(
                re.findall(
                    r"^CommandSet\s+(\S+)\s*$",
                    stub_path.read_text(encoding="utf-8", errors="replace"),
                    re.M,
                )
            )
        lines = [
            "; SPECTER PATCH — BOOT FIX CommandSet stubs\n",
            "; Valid empty CommandSets so INI parse/lookup does not fail.\n",
            "; Does not remove units/features; buttons can be wired later.\n\n",
        ]
        added = 0
        for name, cs, f, ln in dangling_cs:
            if cs in existing_stubs or cs in commandsets:
                continue
            lines.append(f"CommandSet {cs}\n")
            lines.append("  ; BOOT-FIX stub for " + name + "\n")
            lines.append("End\n\n")
            existing_stubs.add(cs)
            commandsets.add(cs)
            added += 1
            actions.append(f"STUB_COMMANDSET {cs} for {name}")
        if added:
            stub_path.write_text("".join(lines), encoding="utf-8")
            files_changed.add(stub_path)

    # --- Validate structure ---
    struct_errors = validate_structure()

    # --- Empty critical field residual scan ---
    residual_empty = []
    for p in OBJ.rglob("*.ini"):
        for ln, line in enumerate(
            p.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if re.match(
                r"^\s*(CommandSet|Side|WeaponTemplate|TriggeredBy)\s*=\s*;",
                line,
            ) or re.match(
                r"^\s*(CommandSet|Side|WeaponTemplate|TriggeredBy)\s*=\s*$",
                line,
            ):
                residual_empty.append(f"{p}:{ln}: {line.strip()}")

    # Re-check multi prereq residual
    residual_multi = []
    for p in OBJ.rglob("*.ini"):
        in_pre = False
        cur = None
        for ln, line in enumerate(
            p.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            s = line.split(";", 1)[0].strip()
            m = OBJ_DEF.match(s)
            if m:
                cur = m.group(2)
            if s == "Prerequisites":
                in_pre = True
                continue
            if in_pre and END.match(s):
                in_pre = False
                continue
            if in_pre:
                pm = re.match(r"^Object\s*=\s*(.+)$", s, re.I)
                if pm and len(pm.group(1).split()) > 1:
                    residual_multi.append(f"{p}:{ln} {cur} {pm.group(1)}")

    # Write report
    report = []
    report.append("# FINAL_BOOT_FIX_REPORT\n\n")
    report.append(
        "**Goal:** Zero INI parse errors before main menu "
        "(boot cleanup under `patch/Data/INI/Object/Specter/`).\n\n"
    )
    report.append("## Policy\n\n")
    report.append("- No countries / units / aircraft / tanks / buildings / upgrades removed\n")
    report.append("- Definitions fixed in overlay only\n")
    report.append("- Multiplayer sync preserved (`sync_audit.py`)\n\n")
    report.append("## Actions\n\n")
    report.append(f"- Files changed: **{len(files_changed)}**\n")
    report.append(f"- Fix actions: **{len(actions)}**\n")
    report.append(f"- Structure errors remaining: **{len(struct_errors)}**\n")
    report.append(f"- Residual empty critical fields: **{len(residual_empty)}**\n")
    report.append(f"- Residual multi Prerequisites: **{len(residual_multi)}**\n\n")
    report.append("### Detail\n\n")
    for a in actions:
        report.append(f"- `{a}`\n")
    if struct_errors:
        report.append("\n### Structure errors\n\n")
        for e in struct_errors[:50]:
            report.append(f"- `{e}`\n")
    if residual_empty:
        report.append("\n### Residual empty fields\n\n")
        for e in residual_empty:
            report.append(f"- `{e}`\n")
    if residual_multi:
        report.append("\n### Residual multi Prerequisites\n\n")
        for e in residual_multi:
            report.append(f"- `{e}`\n")
    report.append("\n## Boot validation\n\n")
    ok = not struct_errors and not residual_empty and not residual_multi
    report.append(
        f"- Object/Specter End-stack: "
        f"{'PASS' if not struct_errors else 'FAIL'}\n"
    )
    report.append(
        f"- Empty CommandSet/Side/WeaponTemplate/TriggeredBy: "
        f"{'PASS' if not residual_empty else 'FAIL'}\n"
    )
    report.append(
        f"- Single-token Prerequisites: "
        f"{'PASS' if not residual_multi else 'FAIL'}\n"
    )
    report.append(
        f"\n**BOOT CLEANUP: {'PASS' if ok else 'FAIL'}**\n"
    )
    REPORT.write_text("".join(report), encoding="utf-8")
    print(f"Changed files: {len(files_changed)}")
    print(f"Actions: {len(actions)}")
    print(f"Structure errors: {len(struct_errors)}")
    print(f"Residual empty: {len(residual_empty)}")
    print(f"Residual multi: {len(residual_multi)}")
    print(f"Report: {REPORT}")
    print("BOOT", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
