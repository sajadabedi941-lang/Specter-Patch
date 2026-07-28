#!/usr/bin/env python3
"""FULL SPECTER PATCH AUDIT — report only (no repairs).

Scans:
  - Vendor SPEC DATA BIG (extracted)
  - Accepted patch/Data overlay
  - All Release *.big files for Egypt/load-order conflicts
  - PlayerTemplate / CommandSet / CommandButton references
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("patch")
SPEC_DATA = ROOT / "Release/SPECTER_BIG_MERGE/_SPEC_DATA_ONE.big"
PATCH_DATA = ROOT / "Data"
OUT = ROOT / "Release/SPECTER_FINAL_REPAIRED"
AUDIT = OUT / "AUDIT_REPORT.txt"

OBJ_RE = re.compile(r"^\s*Object\s+(\S+)", re.M)
CS_DEF_RE = re.compile(r"^\s*CommandSet\s+(\S+)", re.M)
CB_DEF_RE = re.compile(r"^\s*CommandButton\s+(\S+)", re.M)
PT_DEF_RE = re.compile(r"^\s*PlayerTemplate\s+(\S+)", re.M)
CS_REF_RE = re.compile(r"^\s*CommandSet\s*=\s*(\S+)", re.M)
CB_REF_RE = re.compile(
    r"^\s*(?:CommandButton|Button|SpecialPowerButton|SciencePurchaseCommandButton)\d*\s*=\s*(\S+)",
    re.M,
)
# also 1 = CommandButtonName style in CommandSet
CS_SLOT_RE = re.compile(r"^\s*\d+\s*=\s*(\S+)", re.M)
START_BLDG_RE = re.compile(r"^\s*StartingBuilding\s*=\s*(\S+)", re.M)
SIDE_RE = re.compile(r"^\s*Side\s*=\s*(\S+)", re.M)
PREREQ_RE = re.compile(r"^\s*Prerequisites\b.*", re.M)
OBJ_IN_PREREQ = re.compile(r"Object\s*=\s*(\S+)")
SCIENCE_IN_PREREQ = re.compile(r"Science\s*=\s*(\S+)")

CRIT_SUFFIXES = (
    "CommandCenter",
    "MilitaryHQ",
    "AdvancedAirBase",
)

BROKEN_EGYPT_SHA = "1b559b9e0d4eb1400e76934196eb71205c1ff21317e610d717c1da1dc7870b61"


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1", errors="replace")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def decode(b: bytes) -> str:
    return b.decode("utf-8", errors="replace")


def soft_parse(text: str, path: str) -> list[str]:
    errs: list[str] = []
    depth = 0
    for i, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0]
        if not code.strip():
            continue
        if re.match(r"^\s*End\s*$", code):
            depth -= 1
            if depth < 0:
                errs.append(f"{path}:{i} End without open block")
                depth = 0
            continue
        if re.match(
            r"^\s*(Object|Draw|Behavior|ArmorSet|Body|UnitSpecificSounds|"
            r"ConditionState|WeaponSet|ActiveBody|LocomotorSet|Animation|"
            r"PlayerTemplate|CommandSet|CommandButton|MappedImage|Science|"
            r"SpecialPower|Upgrade|Weapon|FXList|ObjectCreationList|"
            r"ParticleSystem|AudioEvent|ControlBarScheme)\b",
            code,
        ):
            # multi-value assignment lines like Behavior = X ModuleTag are openers
            # but "Side = Egypt" is not — already excluded by word list
            depth += 1
    if depth != 0:
        errs.append(f"{path}: unbalanced End depth={depth}")
    # obvious broken tokens
    if "\x00" in text:
        errs.append(f"{path}: embedded NUL")
    return errs


def merge_spec_patch() -> dict[str, bytes]:
    """Case-insensitive merge: SPEC then patch/Data wins."""
    spec = read_big(SPEC_DATA)
    merged: dict[str, bytes] = {}
    lower: dict[str, str] = {}
    for name, content in spec.items():
        canon = name.replace("/", "\\")
        if not canon.lower().startswith("data\\"):
            continue
        key = canon.lower()
        lower[key] = canon
        merged[canon] = content
    # overlay patch
    for path in PATCH_DATA.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(PATCH_DATA).as_posix()
        canon = "Data\\" + rel.replace("/", "\\")
        key = canon.lower()
        if key in lower:
            merged[lower[key]] = path.read_bytes()
        else:
            lower[key] = canon
            merged[canon] = path.read_bytes()
    return merged


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    problems: list[dict] = []

    def add(problem: str, path: str, cause: str, fix: str, severity: str = "HIGH"):
        problems.append(
            {
                "severity": severity,
                "problem": problem,
                "path": path,
                "cause": cause,
                "fix": fix,
            }
        )

    print("Merging SPEC + patch/Data for audit...")
    merged = merge_spec_patch()
    print(f"Merged entries: {len(merged)}")

    # Collect definitions
    objects: dict[str, list[str]] = defaultdict(list)
    commandsets: dict[str, list[str]] = defaultdict(list)
    commandbuttons: dict[str, list[str]] = defaultdict(list)
    playertemplates: dict[str, list[str]] = defaultdict(list)
    parse_errors: list[str] = []
    egypt_paths: list[tuple[str, str]] = []

    ini_texts: dict[str, str] = {}
    for name, content in merged.items():
        if not name.lower().endswith(".ini"):
            continue
        text = decode(content)
        ini_texts[name] = text
        parse_errors.extend(soft_parse(text, name))
        for m in OBJ_RE.finditer(text):
            objects[m.group(1)].append(name)
        for m in CS_DEF_RE.finditer(text):
            commandsets[m.group(1)].append(name)
        for m in CB_DEF_RE.finditer(text):
            commandbuttons[m.group(1)].append(name)
        for m in PT_DEF_RE.finditer(text):
            playertemplates[m.group(1)].append(name)
        if name.lower().endswith("egypt_commandcenter.ini"):
            egypt_paths.append((name, hashlib.sha256(content).hexdigest()))

    # 1/2 Duplicate Objects
    obj_dups = {o: ps for o, ps in objects.items() if len(ps) > 1}
    for o, ps in sorted(obj_dups.items()):
        crit = any(o.endswith(s) or s in o for s in CRIT_SUFFIXES)
        sev = "CRITICAL" if crit or o == "Egypt_CommandCenter" else "HIGH"
        add(
            f"Duplicate Object definition: {o} (x{len(ps)})",
            " | ".join(ps),
            "Same Object name defined in multiple INI files in merged Data tree",
            "Keep one authoritative INI; remove or rename obsolete duplicate definitions",
            sev,
        )

    # Critical building/aircraft/unit dups (by name pattern)
    for o, ps in sorted(objects.items()):
        if len(ps) < 2:
            continue
        if any(
            x in o
            for x in (
                "CommandCenter",
                "MilitaryHQ",
                "AdvancedAirBase",
                "Aircraft",
                "Fighter",
                "Bomber",
                "Jet",
                "Helicopter",
            )
        ):
            # already covered by obj_dups
            pass

    # Egypt specifically
    if len(egypt_paths) != 1:
        add(
            f"Egypt_CommandCenter.ini path count = {len(egypt_paths)}",
            " | ".join(p for p, _ in egypt_paths) or "(none)",
            "Expected exactly one Egypt_CommandCenter.ini in merged Data",
            "Delete extras; keep one USA-donor Egypt_CommandCenter.ini",
            "CRITICAL",
        )
    else:
        p, sha = egypt_paths[0]
        text = ini_texts[p]
        if sha == BROKEN_EGYPT_SHA or "irq_comndcntr" in text or "Iraq_Adnan1" in text:
            add(
                "Broken Egypt_CommandCenter still present in merge",
                p,
                f"Broken SPEC donor sha={sha} with irq_/Iraq leftovers",
                "Replace with USA AmericaCommandCenter donor Egypt identity file",
                "CRITICAL",
            )
        # forbid tokens in code
        for i, line in enumerate(text.splitlines(), 1):
            code = line.split(";", 1)[0]
            if re.search(r"irq_|Irq_|Iraq|Iraqi|SUPERWEAPON_Iraq|Iraq_PlayerTemplate", code):
                add(
                    "Forbidden Iraq token in Egypt_CommandCenter",
                    f"{p}:{i}",
                    line.strip(),
                    "Scrub/replace with USA/Egypt equivalents",
                    "CRITICAL",
                )
                break

    egypt_obj = objects.get("Egypt_CommandCenter", [])
    if len(egypt_obj) != 1:
        add(
            f"Object Egypt_CommandCenter defined {len(egypt_obj)} times",
            " | ".join(egypt_obj) or "(none)",
            "Duplicate or missing Object Egypt_CommandCenter",
            "Ensure exactly one Object Egypt_CommandCenter definition",
            "CRITICAL",
        )

    # 3 Parser errors
    for e in parse_errors:
        add(
            "INI parser structure error",
            e.split(":")[0] if ":" in e else e,
            e,
            "Balance End blocks / fix malformed INI structure",
            "HIGH",
        )

    # 5 PlayerTemplate / CommandSet / CommandButton refs
    defined_cs = set(commandsets)
    defined_cb = set(commandbuttons)
    defined_obj = set(objects)
    defined_pt = set(playertemplates)

    missing_cs: dict[str, set[str]] = defaultdict(set)
    missing_cb: dict[str, set[str]] = defaultdict(set)
    missing_start: dict[str, set[str]] = defaultdict(set)
    missing_prereq: dict[str, set[str]] = defaultdict(set)

    for name, text in ini_texts.items():
        for m in CS_REF_RE.finditer(text):
            # skip CommandSet definition lines already handled — CommandSet Name vs CommandSet = Name
            # CS_REF is CommandSet = 
            ref = m.group(1)
            if ref not in defined_cs and not ref.startswith("NONE"):
                missing_cs[ref].add(name)
        for m in START_BLDG_RE.finditer(text):
            ref = m.group(1)
            if ref not in defined_obj:
                missing_start[ref].add(name)
        # CommandSet body slots
        if CS_DEF_RE.search(text):
            for m in CS_SLOT_RE.finditer(text):
                ref = m.group(1)
                if ref in ("NONE", "Separator", ""):
                    continue
                # slots usually reference CommandButtons
                if ref not in defined_cb and ref not in defined_obj:
                    # could be CommandButton
                    missing_cb[ref].add(name)
        # Prerequisites Object=
        for block in re.finditer(
            r"Prerequisites\s*\n(?:.*?\n)*?^\s*End\s*$", text, re.M
        ):
            for m in OBJ_IN_PREREQ.finditer(block.group(0)):
                ref = m.group(1)
                if ref not in defined_obj:
                    missing_prereq[ref].add(name)

    # Duplicate CommandSet / CommandButton / PlayerTemplate
    for cs, ps in sorted(commandsets.items()):
        if len(ps) > 1:
            add(
                f"Duplicate CommandSet: {cs} (x{len(ps)})",
                " | ".join(ps),
                "Same CommandSet redefined in multiple files",
                "Keep one definition; remove obsolete duplicate",
                "MEDIUM",
            )
    for cb, ps in sorted(commandbuttons.items()):
        if len(ps) > 1:
            add(
                f"Duplicate CommandButton: {cb} (x{len(ps)})",
                " | ".join(ps),
                "Same CommandButton redefined in multiple files",
                "Keep one definition; remove obsolete duplicate",
                "MEDIUM",
            )
    for pt, ps in sorted(playertemplates.items()):
        if len(ps) > 1:
            add(
                f"Duplicate PlayerTemplate: {pt} (x{len(ps)})",
                " | ".join(ps),
                "Same PlayerTemplate redefined in multiple files",
                "Keep one definition; remove obsolete duplicate",
                "HIGH",
            )

    # Limit missing ref noise — report aggregates + critical ones
    crit_missing_cs = {
        k: v
        for k, v in missing_cs.items()
        if any(x in k for x in ("CommandCenter", "MilitaryHQ", "AdvancedAirBase", "Egypt"))
    }
    for ref, files in sorted(crit_missing_cs.items()):
        add(
            f"Missing CommandSet reference: {ref}",
            " | ".join(sorted(files)[:5]),
            "Object/PlayerTemplate references CommandSet not defined in merge",
            f"Define CommandSet {ref} or retarget to a valid CommandSet",
            "HIGH",
        )

    for ref, files in sorted(missing_start.items()):
        add(
            f"Missing StartingBuilding Object: {ref}",
            " | ".join(sorted(files)[:5]),
            "PlayerTemplate StartingBuilding points to undefined Object",
            f"Create Object {ref} or change StartingBuilding to existing HQ/CC",
            "CRITICAL",
        )

    # Sample of missing prereqs (cap)
    prereq_items = sorted(missing_prereq.items(), key=lambda kv: -len(kv[1]))[:40]
    for ref, files in prereq_items:
        add(
            f"Missing prerequisite Object: {ref}",
            " | ".join(sorted(files)[:3]),
            "Prerequisites block references undefined Object",
            f"Add Object {ref} or remove/replace prerequisite",
            "MEDIUM",
        )

    # Missing CB for AdvancedAirBase / CC commandsets (cap)
    aab_missing_cb = {
        k: v
        for k, v in missing_cb.items()
        if any("AdvancedAirBase" in f or "CommandCenter" in f or "MilitaryHQ" in f for f in v)
        or "Air" in k
        or "AAB" in k
    }
    for ref, files in sorted(aab_missing_cb.items())[:50]:
        add(
            f"Missing CommandButton (likely): {ref}",
            " | ".join(sorted(files)[:3]),
            "CommandSet slot references name not found as CommandButton or Object",
            f"Define CommandButton {ref} or fix CommandSet slot",
            "MEDIUM",
        )

    # 7 Faction folders
    specter_obj = [
        n
        for n in merged
        if "data\\ini\\object\\specter\\" in n.replace("/", "\\").lower()
    ]
    factions = defaultdict(int)
    for n in specter_obj:
        parts = n.replace("/", "\\").split("\\")
        # Data INI Object Specter <Faction> ...
        try:
            i = [p.lower() for p in parts].index("specter")
            fac = parts[i + 1]
            factions[fac] += 1
        except (ValueError, IndexError):
            pass

    # Iraq / AI_IraqiArmy leftover risk
    for fac in sorted(factions):
        if "iraq" in fac.lower() or "iraqi" in fac.lower():
            add(
                f"Iraq-related faction folder present: {fac}",
                f"Data\\INI\\Object\\Specter\\{fac}\\...",
                "Iraq donor faction content remains in SPEC/patch merge",
                "Do not wire into playable PlayerTemplates; keep isolated or remove if obsolete",
                "MEDIUM",
            )

    # 8/9 Load order conflicts — scan all BIGs for Egypt + critical overlays
    print("Scanning Release BIGs for load-order conflicts...")
    bigs = sorted((ROOT / "Release").rglob("*.big"))
    overlay_candidates = []
    broken_egypt_bigs = []
    for big in bigs:
        # skip huge ART
        if big.name.upper().startswith("_SPEC_ART"):
            continue
        try:
            if big.stat().st_size > 500_000_000:
                continue
            entries = read_big(big)
        except Exception:
            continue
        egypt = [k for k in entries if k.lower().endswith("egypt_commandcenter.ini")]
        if not egypt:
            continue
        for k in egypt:
            sha = hashlib.sha256(entries[k]).hexdigest()
            text = decode(entries[k])
            broken = sha == BROKEN_EGYPT_SHA or "irq_comndcntr" in text
            name = big.name
            # alphabetical load order risk: underscore prefixes
            overlay_candidates.append((name, str(big), sha, broken, len(entries)))
            if broken:
                broken_egypt_bigs.append(str(big))

    # Sort by name for ZH-like ASCII load order
    overlay_candidates.sort(key=lambda x: x[0].lower())
    add(
        "Multiple Specter Data BIGs exist that each contain Egypt_CommandCenter.ini",
        f"{len(overlay_candidates)} BIG files",
        "Zero Hour loads all *.big; later alphabetical overrides can resurrect broken/old Egypt CC",
        "Ship ONE Data BIG only (_SPECTER_FINAL_REPAIRED.big replacing _SPEC_DATA_ONE.big); "
        "remove CLEAN/V2/TEST/ROOT/partial playable BIGs from game folder",
        "CRITICAL",
    )
    for name, path, sha, broken, n in overlay_candidates:
        if broken or name.startswith("_SPEC_DATA") or name.startswith("_SPECTER"):
            add(
                f"Load-order BIG provides Egypt_CommandCenter ({'BROKEN' if broken else 'ok'}): {name}",
                path,
                f"sha={sha} entries={n}",
                "Do not place beside final repaired BIG; obsolete for install",
                "CRITICAL" if broken else "HIGH",
            )

    # 10 Multiplayer sync risks
    add(
        "Multiplayer sync risk: divergent client Data BIG sets",
        "Game folder *.big load stack",
        "If clients have different overlay BIGs or old SPEC vs repaired Data, Object/CRC mismatch desyncs",
        "All clients must use identical final Data BIG only; no mixed overlays",
        "HIGH",
    )
    if obj_dups:
        add(
            f"Multiplayer sync risk: {len(obj_dups)} duplicate Object names in merge",
            "merged Data tree",
            "Duplicate Objects make last-wins load order dependent; clients may resolve differently",
            "Eliminate all duplicate Object definitions before shipping",
            "HIGH",
        )

    # Patch loose stub Egypt files (271 bytes) that can confuse tooling
    for loose in Path(".").rglob("*Egypt_CommandCenter.ini"):
        try:
            b = loose.read_bytes()
        except Exception:
            continue
        if len(b) < 500:
            add(
                "Obsolete stub Egypt_CommandCenter.ini loose file",
                str(loose),
                f"Tiny stub size={len(b)} not a valid Object definition",
                "Delete obsolete stub; do not pack into final BIG",
                "MEDIUM",
            )

    # Summarize
    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    problems.sort(key=lambda p: (sev_order.get(p["severity"], 9), p["problem"]))

    lines = [
        "SPECTER PATCH COMPLETE AUDIT REPORT (NO FIXES APPLIED)",
        "=" * 70,
        f"Merged Data entries (SPEC + patch/Data): {len(merged)}",
        f"Objects defined: {len(objects)}",
        f"Duplicate Object names: {len(obj_dups)}",
        f"CommandSets: {len(commandsets)}  CommandButtons: {len(commandbuttons)}  PlayerTemplates: {len(playertemplates)}",
        f"INI structure parse errors: {len(parse_errors)}",
        f"Egypt_CommandCenter.ini paths in merge: {len(egypt_paths)}",
        f"Faction folders under Object/Specter: {len(factions)}",
        f"BIGs containing Egypt_CommandCenter: {len(overlay_candidates)}",
        f"Total problems listed: {len(problems)}",
        "",
        "FACTION FOLDERS:",
    ]
    for fac, n in sorted(factions.items(), key=lambda kv: kv[0].lower()):
        lines.append(f"  {fac}: {n} files")
    lines.append("")
    lines.append("PROBLEMS (Problem / File path / Cause / Required fix):")
    lines.append("-" * 70)
    for i, p in enumerate(problems, 1):
        lines.append(f"\n[{i}] [{p['severity']}] {p['problem']}")
        lines.append(f"    PATH: {p['path']}")
        lines.append(f"    CAUSE: {p['cause']}")
        lines.append(f"    FIX: {p['fix']}")

    # Duplicate object appendix (full list)
    lines.append("\n\nAPPENDIX A — ALL DUPLICATE OBJECTS")
    lines.append("-" * 70)
    for o, ps in sorted(obj_dups.items()):
        lines.append(f"{o} x{len(ps)}")
        for pth in ps:
            lines.append(f"  - {pth}")

    text = "\n".join(lines) + "\n"
    AUDIT.write_text(text, encoding="utf-8")
    print(f"Wrote {AUDIT} problems={len(problems)} obj_dups={len(obj_dups)} parse={len(parse_errors)}")
    # also print critical summary to stdout
    crit = [p for p in problems if p["severity"] == "CRITICAL"]
    print(f"CRITICAL: {len(crit)}")
    for p in crit[:30]:
        print(" -", p["problem"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
