#!/usr/bin/env python3
"""Zero Hour initialization validation against a packed _SPEC_DATA_ONE.big.

Unlike source-tree audits, this tool:
  1. Extracts INI bytes from the FINAL packed BIG (raw)
  2. Parses Object blocks in BIG load order
  3. Simulates PRELOAD object factory resolution (Weapon / Locomotor /
     FireWeapon / Science / CommandSet) — including projectile PRELOAD
     cases that SPECTER_CRASH_HUNTER historically under-reported

Exit code 0 = CLEAN, 1 = FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import sys
import zlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def decode_raw(raw: bytes) -> str:
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    try:
        return raw.decode("utf-8")
    except Exception:
        return raw.decode("latin-1", errors="replace")


def parse_big_ordered(path: Path) -> list[tuple[str, bytes]]:
    """Return entries in archive index order (ZH load-ish order)."""
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"not BIGF: {path}")
    n = struct.unpack(">I", data[8:12])[0]
    off = 16
    out: list[tuple[str, bytes]] = []
    for _ in range(n):
        o, s = struct.unpack(">II", data[off : off + 8])
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin-1")
        off = end + 1
        raw = data[o : o + s]
        if len(raw) >= 8 and raw[:2] in (b"CK", b"PM"):
            try:
                raw = zlib.decompress(raw[8:])
            except Exception:
                pass
        out.append((name.replace("\\", "/"), raw))
    return out


def iter_objects(text: str) -> list[tuple[str, int, str]]:
    lines = text.splitlines()
    objs: list[tuple[str, int, str]] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^Object\s+(\S+)\s*$", lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1)
        start = i + 1
        j = i + 1
        while j < len(lines) and not re.match(r"^Object\s+(\S+)\s*$", lines[j]):
            j += 1
        body = "\n".join(lines[start:j])
        objs.append((name, start + 1, body))
        i = j
    return objs


def kindof(body: str) -> str:
    m = re.search(r"(?m)^\s*KindOf\s*=\s*(.+)$", body)
    return m.group(1).split(";", 1)[0].strip() if m else ""


def catalog_defs(entries: list[tuple[str, bytes]]) -> dict[str, set[str]]:
    cats: dict[str, set[str]] = defaultdict(set)
    headers = (
        "Weapon",
        "Locomotor",
        "Science",
        "CommandSet",
        "FXList",
        "Armor",
        "ObjectCreationList",
        "Object",
    )
    for name, raw in entries:
        if not name.lower().endswith(".ini"):
            continue
        text = decode_raw(raw)
        for hdr in headers:
            for m in re.finditer(rf"(?m)^{hdr}\s+(\S+)\s*$", text):
                cats[hdr].add(m.group(1))
    return cats


@dataclass
class Issue:
    severity: str
    path: str
    line: int | None
    obj: str
    detail: str


@dataclass
class ValidationResult:
    issues: list[Issue] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "FATAL" for i in self.issues)


def validate_object_block_structure(path: str, obj: str, line: int, body: str) -> list[Issue]:
    """Structural checks for one Object body (header line already consumed)."""
    issues: list[Issue] = []
    stack: list[str] = ["Object"]
    for i, raw in enumerate(body.splitlines(), line):
        s = raw.strip()
        if not s or s.startswith(";"):
            continue
        if any(c in s for c in "{}"):
            issues.append(Issue("FATAL", path, i, obj, f"invalid brace syntax: {s}"))
        m = re.match(r"^Behavior\s*=\s*(\S+)", s)
        if m and m.group(1) in {"Behavoir", "Behvior", "MissileAIUpate", "PhysicsBehavoir"}:
            issues.append(Issue("FATAL", path, i, obj, f"invalid Module entry: {m.group(1)}"))
        if re.search(r"Weapon\s*=\s*PRIMARY\s*$", s):
            issues.append(Issue("FATAL", path, i, obj, "malformed Weapon=PRIMARY missing template"))
        if re.match(r"^(Draw|Behavior|Body|ClientUpdate|ClientBehavior)\s*=", s):
            stack.append("mod")
        elif re.match(r"^(WeaponSet|ArmorSet|DefaultConditionState|TransitionState)\s*$", s):
            stack.append("blk")
        elif re.match(r"^(ConditionState|AliasConditionState)\s*=", s):
            stack.append("cond")
        elif re.match(r"^(UnitSpecificSounds|UnitSpecificFX)\s*$", s):
            stack.append("uss")
        elif s == "End" or s.startswith("End "):
            if not stack:
                issues.append(Issue("FATAL", path, i, obj, "extra End"))
            else:
                stack.pop()
    if stack:
        issues.append(Issue("FATAL", path, line, obj, f"unclosed blocks: {stack}"))
    return issues


def validate_preload_deps(
    path: str, obj: str, line: int, body: str, cats: dict[str, set[str]]
) -> list[Issue]:
    issues: list[Issue] = []
    ko = kindof(body)
    if "PRELOAD" not in ko.upper():
        return issues

    # Locomotor (None/NONE = intentional immobile / no-loco stub in Specter)
    for m in re.finditer(r"(?m)^\s*Locomotor\s*=\s*SET_NORMAL\s+(\S+)", body):
        loc = m.group(1)
        if loc in {"None", "NONE", "none"}:
            continue
        if loc not in cats["Locomotor"]:
            issues.append(
                Issue(
                    "FATAL",
                    path,
                    line,
                    obj,
                    f"PRELOAD missing Locomotor template: {loc}",
                )
            )

    # WeaponSet weapons
    for m in re.finditer(
        r"(?m)^\s*Weapon\s*=\s*(PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", body
    ):
        w = m.group(2)
        if w not in {"NONE", "None", "none"} and w not in cats["Weapon"]:
            issues.append(
                Issue("FATAL", path, line, obj, f"PRELOAD missing Weapon template: {w}")
            )

    # FireWeaponUpdate
    for m in re.finditer(r"(?m)^\s*FireWeapon\s*=\s*(\S+)", body):
        # skip InitialDelay-only contexts — FireWeapon = Name
        w = m.group(1)
        if w not in {"NONE", "None"} and w not in cats["Weapon"]:
            # Could be "Weapon = X" under FireWeaponUpdate — handled above as Weapon= without slot
            pass
    for m in re.finditer(r"(?m)^\s*Weapon\s*=\s*(?!PRIMARY|SECONDARY|TERTIARY)(\S+)\s*$", body):
        w = m.group(1)
        if w not in {"NONE", "None"} and w not in cats["Weapon"]:
            issues.append(
                Issue(
                    "FATAL",
                    path,
                    line,
                    obj,
                    f"PRELOAD FireWeaponUpdate missing Weapon: {w}",
                )
            )

    # Science
    for m in re.finditer(r"(?m)^\s*Science\s*=\s*(.+)$", body):
        for tok in m.group(1).split(";")[0].split():
            if tok not in cats["Science"]:
                issues.append(
                    Issue("FATAL", path, line, obj, f"PRELOAD missing Science: {tok}")
                )

    # CommandSet
    for m in re.finditer(r"(?m)^\s*CommandSet\s*=\s*(\S+)", body):
        cs = m.group(1)
        if cs not in {"None", "NONE"} and cs not in cats["CommandSet"]:
            issues.append(
                Issue("FATAL", path, line, obj, f"PRELOAD missing CommandSet: {cs}")
            )

    return issues


def validate_specific_9m317(entries: list[tuple[str, bytes]], cats: dict[str, set[str]]) -> list[Issue]:
    """Hard checks for the reported crash object inside packed BIG only."""
    issues: list[Issue] = []
    target = None
    path = None
    raw = None
    for name, blob in entries:
        low = name.lower()
        if low.endswith("russia_weaponobjects.ini") and "russian federation" in low:
            path = name
            raw = blob
            break
    if raw is None:
        return [Issue("FATAL", "?", None, "9M317_MissileObject", "russia_weaponobjects.ini missing from BIG")]

    text = decode_raw(raw)
    # duplicate object names in this file
    counts: dict[str, int] = defaultdict(int)
    for obj, line, body in iter_objects(text):
        counts[obj] += 1
        if obj == "9M317_MissileObject":
            target = (obj, line, body)

    dups = [n for n, c in counts.items() if c > 1]
    for d in dups:
        if d in {"9M317_MissileObject", "9M317M3_MissileObject"}:
            issues.append(Issue("FATAL", path, None, d, f"duplicate Object name x{counts[d]}"))

    if not target:
        issues.append(Issue("FATAL", path, None, "9M317_MissileObject", "Object block missing"))
        return issues

    obj, line, body = target
    # header syntax already matched by iter_objects
    issues.extend(validate_object_block_structure(path, obj, line, body))

    ko = kindof(body)
    if "PRELOAD" in ko.upper():
        issues.append(
            Issue(
                "FATAL",
                path,
                line,
                obj,
                "KindOf incorrectly includes PRELOAD (donor-rebuild regression; "
                "original Specter projectile is not PRELOAD — ZH init instantiates it and crashes)",
            )
        )

    # Locomotor must still resolve (weapon projectile create path)
    m = re.search(r"(?m)^\s*Locomotor\s*=\s*SET_NORMAL\s+(\S+)", body)
    if not m:
        issues.append(Issue("FATAL", path, line, obj, "missing Locomotor = SET_NORMAL"))
    else:
        loc = m.group(1)
        # Original Specter uses Cyrillic Em (U+041C) in 9М317* locomotor names;
        # that is valid when the matching Locomotor.ini template exists.
        if loc not in cats["Locomotor"]:
            issues.append(Issue("FATAL", path, line, obj, f"missing Locomotor template: {loc}"))

    # FireWeaponUpdate weapon
    for m in re.finditer(r"(?m)^\s*Weapon\s*=\s*(?!PRIMARY|SECONDARY|TERTIARY)(\S+)\s*$", body):
        w = m.group(1)
        if w not in cats["Weapon"]:
            issues.append(Issue("FATAL", path, line, obj, f"missing FireWeapon Weapon: {w}"))

    # unsupported fields / donor junk markers
    if "SPECTER FULL REBUILD - cloned from validated USA/stock donor" in body:
        issues.append(
            Issue(
                "FATAL",
                path,
                line,
                obj,
                "still contains USA-donor rebuild stub (broken block not restored)",
            )
        )

    return issues


def run_validation(big: Path, baseline: Path | None = None) -> ValidationResult:
    res = ValidationResult()
    entries = parse_big_ordered(big)
    cats = catalog_defs(entries)
    res.checks.append(f"BIG entries={len(entries)}")
    res.checks.append(f"SHA256={hashlib.sha256(big.read_bytes()).hexdigest()}")
    res.checks.append(f"SIZE={big.stat().st_size}")
    res.checks.append(f"Weapon defs={len(cats['Weapon'])} Locomotor defs={len(cats['Locomotor'])}")

    # Specific reported crash target (raw packed file)
    res.issues.extend(validate_specific_9m317(entries, cats))
    res.checks.append("raw-parse 9M317_MissileObject from packed russia_weaponobjects.ini: done")

    # Full PRELOAD dependency walk (Object INIs only).
    # Structure End-balance is only enforced on the reported crash object to
    # avoid false positives from stock INI styles Crash Hunter already accepts.
    preload_checked = 0
    for name, raw in entries:
        low = name.lower()
        if not low.endswith(".ini"):
            continue
        if "/object/" not in low and not low.startswith("data/ini/object/"):
            continue
        text = decode_raw(raw)
        for obj, line, body in iter_objects(text):
            if "PRELOAD" not in kindof(body).upper():
                continue
            preload_checked += 1
            res.issues.extend(validate_preload_deps(name, obj, line, body, cats))
    res.checks.append(f"PRELOAD objects dependency-checked={preload_checked}")

    # Dedup identical issues
    seen = set()
    uniq: list[Issue] = []
    for iss in res.issues:
        key = (iss.severity, iss.path, iss.obj, iss.detail)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(iss)
    res.issues = uniq

    # Subtract baseline (original Specter) PRELOAD dependency misses — those boot.
    if baseline and baseline.exists():
        base_entries = parse_big_ordered(baseline)
        base_cats = catalog_defs(base_entries)
        base_res = ValidationResult()
        for name, raw in base_entries:
            low = name.lower()
            if not low.endswith(".ini"):
                continue
            if "/object/" not in low and not low.startswith("data/ini/object/"):
                continue
            text = decode_raw(raw)
            for obj, line, body in iter_objects(text):
                if "PRELOAD" not in kindof(body).upper():
                    continue
                base_res.issues.extend(validate_preload_deps(name, obj, line, body, base_cats))
        base_keys = {(i.obj, i.detail) for i in base_res.issues}
        kept: list[Issue] = []
        for iss in res.issues:
            # Always keep specific 9M317 structural/PRELOAD regressions
            if iss.obj in {"9M317_MissileObject", "9M317M3_MissileObject"}:
                kept.append(iss)
                continue
            if (iss.obj, iss.detail) in base_keys:
                continue
            kept.append(iss)
        removed = len(res.issues) - len(kept)
        res.issues = kept
        res.checks.append(f"baseline-filtered original-also PRELOAD misses={removed}")
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--big", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Original Specter BIG for regression filtering",
    )
    args = ap.parse_args()

    res = run_validation(args.big, args.baseline)
    lines: list[str] = []
    lines.append("ZERO HOUR INITIALIZATION VALIDATION (PACKED BIG)")
    lines.append("=" * 50)
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"BIG: {args.big}")
    if args.baseline:
        lines.append(f"BASELINE: {args.baseline}")
    for c in res.checks:
        lines.append(f"CHECK: {c}")
    lines.append("")
    fatals = [i for i in res.issues if i.severity == "FATAL"]
    lines.append(f"FATAL issues: {len(fatals)}")
    if fatals:
        lines.append("FAILURES:")
        for i in fatals[:100]:
            loc = f"L{i.line}" if i.line else "L?"
            lines.append(f"  [{i.severity}] {i.path}:{loc} Object {i.obj}: {i.detail}")
        if len(fatals) > 100:
            lines.append(f"  ... +{len(fatals)-100} more")
        lines.append("")
        lines.append("VERDICT: FAIL")
    else:
        lines.append("No FATAL PRELOAD/init parser failures detected.")
        lines.append("")
        lines.append("VERDICT: PASS")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.report.read_text())
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
