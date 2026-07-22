#!/usr/bin/env python3
"""Multiplayer sync audit for Specter patch INIs.

Exit 0 = clean. Exit 1 = findings that must be fixed before content PRs.
See patch/SYNC_CHECKLIST.md.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # patch/
INI = ROOT / "Data" / "INI"
REPO = ROOT.parent

FOLDER_SIDE = {
    "Turkey Armed Forces": "Turkey",
    "North Korea": "NorthKorea",
    "Iraq Army": "Iraq",
    "Ukrainian Armed Forces": "Ukraine",
    "Pakistan Armed Forces": "Pakistan",
    "Saudi Arabian Armed Forces": "SaudiArabia",
    "United Arab Emirates": "UAE",
    "Indian Armed Forces": "India",
    "Japan Self-Defense Forces": "Japan",
}

# Helpers / projectiles — Side still preferred, but BuildCost Side is hard error.
SOFT_NAME = re.compile(
    r"(Damaged|Debris|Hulk|Lock|Projectile|WeaponObject|FireControl|Explosion|Cloud|"
    r"Warhead|Reentry|Shell|Bomblet|Decal|Rider|Cells?$|FakeRCS|Jammer|MissileObject)",
    re.I,
)

OBJ_RE = re.compile(r"^Object\s+(\S+)\s*$", re.M)
SIDE_RE = re.compile(r"^\s*Side\s*=\s*(\S+)", re.M)
COST_RE = re.compile(r"^\s*BuildCost\s*=", re.M)
TIME_RE = re.compile(r"^\s*BuildTime\s*=", re.M)


def collect(keyword: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = defaultdict(list)
    rx = re.compile(rf"^{keyword}\s+(\S+)\s*$", re.M)
    for p in INI.rglob("*.ini"):
        text = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        for m in rx.finditer(text):
            found[m.group(1)].append(rel)
    return found


def iter_objects(text: str):
    ms = list(OBJ_RE.finditer(text))
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        yield m.group(1), text[m.start() : end]


def expected_side(path: Path) -> str | None:
    for folder, side in FOLDER_SIDE.items():
        if folder in path.parts:
            return side
    return None


def btn_object_map() -> dict[str, str]:
    btn_rx = re.compile(r"^CommandButton\s+(\S+)\s*$", re.M)
    obj_field = re.compile(r"^\s*Object\s*=\s*(\S+)", re.M)
    out: dict[str, str] = {}
    for p in INI.glob("CommandButton*.ini"):
        text = p.read_text(errors="replace")
        ms = list(btn_rx.finditer(text))
        for i, m in enumerate(ms):
            end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
            om = obj_field.search(text[m.start() : end])
            if om:
                out[m.group(1)] = om.group(1)
    return out


def ini_digests(root: Path) -> dict[str, str]:
    """Hash generated gameplay INIs for byte-idempotency checks."""
    base = root / "Data" / "INI"
    return {
        path.relative_to(base).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in base.rglob("*.ini")
    }


def verify_bake_idempotency(errors: list[str]) -> None:
    """Re-run deterministic generators in a temporary patch copy."""
    with tempfile.TemporaryDirectory(prefix="specter-sync-") as temp:
        copied = Path(temp) / "patch"
        shutil.copytree(
            ROOT,
            copied,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        before = ini_digests(copied)
        commands = (
            copied / "tools" / "economy" / "apply_country_balance.py",
            copied / "tools" / "economy" / "apply_build_limits.py",
        )
        for script in commands:
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=copied.parent,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode:
                errors.append(
                    f"BAKE COMMAND FAILED {script.name}: "
                    f"{result.stderr.strip() or result.stdout.strip()}"
                )
                return
        after = ini_digests(copied)
        changed = sorted(
            path
            for path in set(before) | set(after)
            if before.get(path) != after.get(path)
        )
        if changed:
            sample = ", ".join(changed[:8])
            suffix = f" (+{len(changed) - 8} more)" if len(changed) > 8 else ""
            errors.append(
                f"NON-IDEMPOTENT BAKE changed {len(changed)} INIs: {sample}{suffix}"
            )


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

    # Dual BuildCost / BuildTime in one Object
    for p in (INI / "Object").rglob("*.ini"):
        text = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        for name, part in iter_objects(text):
            costs = COST_RE.findall(part)
            times = TIME_RE.findall(part)
            if len(costs) > 1 or len(times) > 1:
                errors.append(
                    f"DUAL COST/TIME {name} in {rel} "
                    f"(BuildCost×{len(costs)} BuildTime×{len(times)})"
                )

    # Active Random* assignments are forbidden. Cosmetic RandomBone is a
    # ParticleSysBone token, not an assignment, and therefore is unaffected.
    rnd = re.compile(
        r"^\s*(Random[A-Za-z0-9_]*)\s*=",
        re.M | re.I,
    )
    for p in INI.rglob("*.ini"):
        text = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        for m in rnd.finditer(text):
            line = text[: m.start()].count("\n") + 1
            errors.append(f"RANDOM FIELD {rel}:{line} {m.group(0).strip()}")

    # LifetimeUpdate / DeletionUpdate with MinLifetime != MaxLifetime (non-deterministic)
    life_rx = re.compile(
        r"Behavior\s*=\s*(LifetimeUpdate|DeletionUpdate)\s+(\S+)\n(.*?)End",
        re.S | re.I,
    )
    for p in INI.rglob("*.ini"):
        text = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        for m in life_rx.finditer(text):
            body = m.group(3)
            mn = re.search(r"MinLifetime\s*=\s*(\d+)", body)
            mx = re.search(r"MaxLifetime\s*=\s*(\d+)", body)
            if mn and mx and mn.group(1) != mx.group(1):
                line = text[: m.start()].count("\n") + 1
                errors.append(
                    f"NONDET LIFETIME {rel}:{line} {m.group(1)} {m.group(2)} "
                    f"Min={mn.group(1)} Max={mx.group(1)} (pin equal for MP)"
                )

    # Player CommandSets constructing *_AI units (by button name)
    ai_btn = re.compile(r"^\s*\d+\s*=\s*(Command_Construct\S*_AI)\s*$", re.M)
    for p in INI.glob("CommandSet*.ini"):
        text = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        for m in ai_btn.finditer(text):
            line = text[: m.start()].count("\n") + 1
            raw = text.splitlines()[line - 1]
            if raw.lstrip().startswith(";"):
                continue
            errors.append(f"PLAYER AI CONSTRUCT {rel}:{line} {m.group(1)}")

    # CommandSet slots → CommandButton Object = *_AI / MilitaryWarfactory
    btn_map = btn_object_map()
    slot_rx = re.compile(r"^\s*(\d+)\s*=\s*(\S+)(?:\s*;.*)?$", re.M)
    cs_rx = re.compile(r"^CommandSet\s+(\S+)\s*$", re.M)
    for p in INI.glob("CommandSet*.ini"):
        text = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        ms = list(cs_rx.finditer(text))
        for i, m in enumerate(ms):
            end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
            block = text[m.start() : end]
            slots: dict[str, list[str]] = defaultdict(list)
            for sm in slot_rx.finditer(block):
                slot = sm.group(1)
                btn = sm.group(2)
                if btn.startswith(";"):
                    continue
                slots[slot].append(btn)
                obj = btn_map.get(btn)
                if not obj:
                    continue
                if obj.endswith("_AI") or "MilitaryWarfactory" in obj:
                    line = text[: m.start() + sm.start()].count("\n") + 1
                    errors.append(
                        f"PLAYER AI OBJECT {rel}:{line} {m.group(1)} -> {btn} -> {obj}"
                    )
            for slot, buttons in slots.items():
                if len(buttons) > 1:
                    errors.append(
                        f"DUPLICATE COMMAND SLOT {rel} {m.group(1)} "
                        f"slot={slot}: {buttons}"
                    )

    # Side ownership for faction-tree Objects with BuildCost
    for p in (INI / "Object").rglob("*.ini"):
        expect = expected_side(p)
        if not expect:
            continue
        if "WeaponObjects" in p.name or "Shells" in p.name:
            continue
        text = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        for name, block in iter_objects(text):
            if not COST_RE.search(block):
                continue
            if SOFT_NAME.search(name):
                continue
            sm = SIDE_RE.search(block)
            if not sm:
                errors.append(f"MISSING Side {name} in {rel} (expect {expect})")
            elif sm.group(1) != expect:
                errors.append(
                    f"SIDE MISMATCH {name}: Side={sm.group(1)} expect {expect} ({rel})"
                )

    # LinkKey required for AD / strategic launcher name families with BuildCost
    link_need = [
        (re.compile(r"(HISAR|SIPER|Korkut|Sungur)", re.I), "Patch_AirDefense"),
        (
            re.compile(
                r"(TRG230|TRG300|TRLG230|Bora|BM-21|AbbasLauncher|Alhussaien|9P117|AlNida|Karrar)",
                re.I,
            ),
            "Patch_StrategicLauncher",
        ),
    ]
    for p in (INI / "Object").rglob("*.ini"):
        text = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        for name, block in iter_objects(text):
            if name.endswith("_AI") or SOFT_NAME.search(name):
                continue
            if not COST_RE.search(block):
                continue
            for rx, key in link_need:
                if not rx.search(name):
                    continue
                if key not in block:
                    errors.append(f"MISSING LinkKey {name} needs {key} ({rel})")
                break

    # PatchBaseCost marker missing on priced Objects (rebake compounding risk)
    for p in (INI / "Object").rglob("*.ini"):
        text = p.read_text(errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        for name, block in iter_objects(text):
            if not COST_RE.search(block):
                continue
            if SOFT_NAME.search(name) or name.endswith("_AI"):
                continue
            if "PatchBaseCost" not in block:
                warnings.append(f"NO PatchBaseCost {name} ({rel})")

    # Vendor archives must never appear dirty in git (patch-only rule)
    for pattern in (
        "Data.zip",
        "Specter_Data*",
        "_SPEC_DATA_ONE*",
        "_SPEC_ART_ONE*",
        "payload.rar",
        "*.big",
    ):
        try:
            r = subprocess.run(
                ["git", "status", "--porcelain", "--", pattern],
                cwd=REPO,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            break
        for line in r.stdout.splitlines():
            if line.strip():
                errors.append(f"VENDOR ARCHIVE MODIFIED (forbidden): {line.strip()}")

    if (REPO / "Data.zip").exists():
        warnings.append(
            "Vendor archive present at repo root (must remain unmodified): Data.zip"
        )

    verify_bake_idempotency(errors)

    manifest_tool = ROOT / "tools" / "economy" / "generate_sync_manifest.py"
    manifest = ROOT / "SYNC_MANIFEST.sha256"
    if not manifest.exists():
        errors.append("MISSING SYNC_MANIFEST.sha256 (generate before distribution)")
    elif manifest_tool.exists():
        result = subprocess.run(
            [sys.executable, str(manifest_tool), "--check"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            errors.append(result.stdout.strip() or result.stderr.strip())

    print("Specter Patch sync_audit")
    print(f"  errors={len(errors)} warnings={len(warnings)}")
    for e in errors:
        print("  ERROR:", e)
    for w in warnings[:40]:
        print("  WARN:", w)
    if len(warnings) > 40:
        print(f"  WARN: ... +{len(warnings) - 40} more")

    if errors:
        print("FAIL — see patch/SYNC_CHECKLIST.md")
        return 1
    print("PASS — deterministic ID/cost/command/Side/LinkKey checks clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
