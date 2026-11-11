#!/usr/bin/env python3
"""GitHub Actions checks for the V25 sync engine.

Does not extract V25 volumes, does not write SPECTER BIGs, and does not run Generals.exe.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent
ROOT = TOOL.parents[2]
REPORTS = TOOL / "reports"
sys.path.insert(0, str(TOOL))

EXPECTED_DATA = "7f8c7f63e972652e8d178c2a43b1f0102904096d630538b010dbf2d081881343"
EXPECTED_ART_TWO = "81d9a4aa10550ef8b3f4a58842f159fda3f54a1af32fcef37df185eb9b9995bf"

FORBIDDEN_SUFFIXES = (
    "_SPEC_DATA_ONE.big",
    "_SPEC_ART_ONE.big",
    "_SPEC_ART_TWO.big",
)
FORBIDDEN_INI = {
    "data/ini/commandset.ini",
    "data/ini/commandbutton.ini",
    "data/ini/weapon.ini",
    "data/ini/armor.ini",
    "data/ini/locomotor.ini",
    "data/ini/playertemplate.ini",
}


def _run_suite(mod) -> tuple[int, int, int]:
    suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    ran = result.testsRun
    failed = len(result.failures) + len(result.errors)
    return ran, failed, 0 if result.wasSuccessful() else 1


def stage3_and_stage2_unit_tests() -> dict:
    from tests import test_art_cwc, test_resolver

    s3_ran, s3_fail, s3_rc = _run_suite(test_art_cwc)
    # test_art_cwc.main() also loads stage-2 resolver tests; run resolver alone too.
    s2_ran, s2_fail, s2_rc = _run_suite(test_resolver)
    selftest = subprocess.run(
        [sys.executable, str(TOOL / "v25_sync.py"), "selftest"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    combined = s3_ran + s2_ran
    ok = s3_rc == 0 and s2_rc == 0 and selftest.returncode == 0 and combined >= 29
    return {
        "name": "unit_tests",
        "ok": ok,
        "stage3_module_tests": s3_ran,
        "stage3_module_failures": s3_fail,
        "stage2_resolver_tests": s2_ran,
        "stage2_resolver_failures": s2_fail,
        "combined_selftest_count": combined,
        "v25_sync_selftest_returncode": selftest.returncode,
        "note": (
            "v25_sync.py selftest loads test_art_cwc + test_resolver (29 tests). "
            "Modules are also executed separately so each stage is visible."
        ),
    }


def stage1_report_checks() -> dict:
    health = json.loads((REPORTS / "ARCHIVE_HEALTH.json").read_text(encoding="utf-8"))
    baseline = json.loads((REPORTS / "STAGE1_BASELINE.json").read_text(encoding="utf-8"))
    dry = json.loads((REPORTS / "DRY_RUN.json").read_text(encoding="utf-8"))
    errors = []
    if health.get("expected_158_complete") is not True:
        errors.append("ARCHIVE_HEALTH.expected_158_complete is not true")
    if health.get("z62_present") is not True:
        errors.append("z62_present is not true")
    if not (health.get("archive_test") or {}).get("ok"):
        errors.append("archive_test.ok is not true")
    if health.get("stage1_writes_game_bigs") is not False:
        errors.append("stage1_writes_game_bigs must be false")
    data = (health.get("specter_baseline") or {}).get("_SPEC_DATA_ONE.big") or {}
    art = (health.get("specter_baseline") or {}).get("_SPEC_ART_TWO.big") or {}
    if data.get("sha256") != EXPECTED_DATA:
        errors.append("ARCHIVE_HEALTH DATA SHA256 mismatch")
    if art.get("sha256") != EXPECTED_ART_TWO:
        errors.append("ARCHIVE_HEALTH ART TWO SHA256 mismatch")
    if baseline.get("game_bigs_modified") is not False:
        errors.append("STAGE1_BASELINE.game_bigs_modified must be false")
    if baseline.get("generals_exe_run") is not False:
        errors.append("STAGE1_BASELINE.generals_exe_run must be false")
    if baseline.get("archive_complete") is not True:
        errors.append("STAGE1_BASELINE.archive_complete is not true")
    if dry.get("game_bigs_modified") is not False:
        errors.append("DRY_RUN.game_bigs_modified must be false")
    if int(baseline.get("objects_scanned") or 0) < 1:
        errors.append("STAGE1_BASELINE has no objects_scanned")
    return {
        "name": "stage1_reports",
        "ok": not errors,
        "errors": errors,
        "live_7z_on_runner": False,
        "note": "V25 158-volume zip is not in git. CI validates committed ARCHIVE_HEALTH / STAGE1_BASELINE / DRY_RUN.",
    }


def resolver_report_checks() -> dict:
    summary = json.loads((REPORTS / "RESOLVER_SUMMARY.json").read_text(encoding="utf-8"))
    s3 = json.loads((REPORTS / "STAGE3_SUMMARY.json").read_text(encoding="utf-8"))
    errors = []
    if summary.get("applies_to_game") is not False:
        errors.append("RESOLVER_SUMMARY.applies_to_game must be false")
    if int(summary.get("ready_transfer") or 0) == int(
        (json.loads((REPORTS / "STAGE1_BASELINE.json").read_text(encoding="utf-8")).get("collisions") or {}).get(
            "unique_v25"
        )
        or 0
    ):
        errors.append("ready_transfer must not equal unique_v25")
    if int(summary.get("objects_planned") or 0) < 1:
        errors.append("no objects planned")
    if s3.get("applies_to_game") is not False:
        errors.append("STAGE3_SUMMARY.applies_to_game must be false")
    if s3.get("generals_exe_run") is not False:
        errors.append("STAGE3_SUMMARY.generals_exe_run must be false")
    focus = {row["object"]: row for row in (s3.get("focus") or [])}
    for name in ("ChinaCSSA1", "ChinaHQ11"):
        if name not in focus:
            errors.append(f"{name} missing from STAGE3_SUMMARY.focus")
        elif focus[name].get("art_status") not in {
            "READY_FOR_TRANSFER_PLAN",
            "AUTO_RECOVERABLE",
            "MANUAL_REBUILD",
            "BLOCKED",
        }:
            errors.append(f"{name} art_status invalid")
    return {
        "name": "resolver_reports",
        "ok": not errors,
        "errors": errors,
        "ready_transfer": summary.get("ready_transfer"),
        "objects_planned": summary.get("objects_planned"),
        "reuse_only": summary.get("reuse_only"),
    }


def apply_still_blocked() -> dict:
    from lib.engine import Engine

    blocked = False
    try:
        Engine(ROOT).refuse_apply()
    except SystemExit as exc:
        blocked = True
        msg = str(exc)
    else:
        msg = "refuse_apply returned"
    proc = subprocess.run(
        [sys.executable, str(TOOL / "v25_sync.py"), "apply"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    cli_blocked = proc.returncode != 0
    return {
        "name": "apply_blocked",
        "ok": blocked and cli_blocked,
        "refuse_apply_raised": blocked,
        "cli_returncode": proc.returncode,
        "message": (msg or "")[:200],
        "cli_stderr": (proc.stderr or proc.stdout or "")[-400:],
    }


def specter_bigs_unchanged() -> dict:
    protected = json.loads((TOOL / "data" / "protected_paths.json").read_text(encoding="utf-8"))
    errors = []
    for name in FORBIDDEN_SUFFIXES:
        if name not in (protected.get("specter_bigs") or []):
            errors.append(f"{name} missing from protected_paths.json")
    base = (os.environ.get("V25_CI_BASE") or "").strip()
    changed: list[str] = []
    if base and all(c == "0" for c in base):
        base = ""
    pr = (os.environ.get("V25_CI_PR") or "").strip()
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    repo = os.environ.get("GITHUB_REPOSITORY") or ""
    if pr and token and repo:
        import urllib.request

        page = 1
        while True:
            url = f"https://api.github.com/repos/{repo}/pulls/{pr}/files?per_page=100&page={page}"
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "v25-sync-ci",
                },
            )
            with urllib.request.urlopen(req) as resp:
                batch = json.load(resp)
            if not batch:
                break
            changed.extend(f["filename"] for f in batch if f.get("filename"))
            if len(batch) < 100:
                break
            page += 1
    elif base:
        diff = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        changed = [ln.strip() for ln in (diff.stdout or "").splitlines() if ln.strip()]
        if diff.returncode != 0:
            errors.append(f"git diff failed: {(diff.stderr or '')[:200]}")
    elif (ROOT / ".git").is_dir():
        diff = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        changed = [ln.strip() for ln in (diff.stdout or "").splitlines() if ln.strip()]
    hits = []
    for path in changed:
        low = path.replace("\\", "/").lower()
        if any(path.endswith(suf) or low.endswith(suf.lower()) for suf in FORBIDDEN_SUFFIXES):
            hits.append(path)
        if low in FORBIDDEN_INI:
            hits.append(path)
        if "/data/ini/" in low and low.endswith(".ini") and "silentdeath" not in low and "v25_sync" not in low:
            if any(tok in low for tok in ("commandset.ini", "commandbutton.ini", "weapon.ini", "armor.ini")):
                hits.append(path)
    if hits:
        errors.append("forbidden game files in diff: " + ", ".join(hits))

    live = {}
    ss1 = Path("/tmp/ss1/SPECTER FINAL (GeneralsMode.com)")
    hashed_live = False
    if ss1.is_dir():
        from lib.engine import sha256_file

        for name, expected in (("_SPEC_DATA_ONE.big", EXPECTED_DATA), ("_SPEC_ART_TWO.big", EXPECTED_ART_TWO)):
            p = ss1 / name
            if p.is_file():
                hashed_live = True
                got = sha256_file(p)
                live[name] = got
                if got != expected:
                    errors.append(f"live {name} SHA256 changed")
    return {
        "name": "specter_bigs_unchanged",
        "ok": not errors,
        "errors": errors,
        "base": base or None,
        "changed_file_count": len(changed),
        "live_hash_checked": hashed_live,
        "live_hashes": live,
        "report_hashes": {"_SPEC_DATA_ONE.big": EXPECTED_DATA, "_SPEC_ART_TWO.big": EXPECTED_ART_TWO},
        "note": (
            "GitHub runners do not have SPECTER FINAL. CI forbids BIG/public INI in the PR diff "
            "and checks committed ARCHIVE_HEALTH hashes. Live SHA256 runs only if /tmp/ss1 exists."
        ),
    }


def main() -> int:
    checks = [
        stage3_and_stage2_unit_tests(),
        stage1_report_checks(),
        resolver_report_checks(),
        apply_still_blocked(),
        specter_bigs_unchanged(),
    ]
    summary = {
        "ok": all(c.get("ok") for c in checks),
        "generals_exe_run": False,
        "game_bigs_modified": False,
        "checks": checks,
    }
    print(json.dumps(summary, indent=2, default=str))
    print()
    for c in checks:
        flag = "PASS" if c.get("ok") else "FAIL"
        print(f"{flag}  {c.get('name')}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
