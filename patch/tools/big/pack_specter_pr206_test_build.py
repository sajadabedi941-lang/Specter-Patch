#!/usr/bin/env python3
"""Pack a PR #206 test-ready DATA BIG (no faction rebuild).

Starts from the existing Turkey WeaponObjects FULL REBUILD baseline BIG and
embeds the current branch Turkey Armed Forces INI files from the tree.
Does not rebuild factions or invent new content.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

import build_specter_aircraft_aab_global_fixed_big as base
import build_specter_turkey_weaponobjects_crash_fix_big as turkey_wo

ROOT = Path(__file__).resolve().parents[2]
SRC = (
    ROOT
    / "Release"
    / "SPECTER_SPEC_DATA_ONE_TURKEY_WEAPONOBJECTS_FULL_REBUILD"
    / "_SPEC_DATA_ONE.big"
)
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
TUR_TREE = ROOT / "Data" / "INI" / "Object" / "Specter" / "Turkey Armed Forces"
# One-off crash-fix overlays outside Turkey tree (still one-file source fixes).
EXTRA_OVERLAYS = {
    "United Arab Emirates/Buildings/UAE_MilitaryHQ.ini": (
        ROOT
        / "Data"
        / "INI"
        / "Object"
        / "Specter"
        / "United Arab Emirates"
        / "Buildings"
        / "UAE_MilitaryHQ.ini"
    ),
    "United Arab Emirates/Infantry/UAE_Worker.ini": (
        ROOT
        / "Data"
        / "INI"
        / "Object"
        / "Specter"
        / "United Arab Emirates"
        / "Infantry"
        / "UAE_Worker.ini"
    ),
    "United Arab Emirates/Buildings/UAE_WarFactory.ini": (
        ROOT
        / "Data"
        / "INI"
        / "Object"
        / "Specter"
        / "United Arab Emirates"
        / "Buildings"
        / "UAE_WarFactory.ini"
    ),
}
OUT = ROOT / "Release" / "SPECTER_PR206_TEST_BUILD"


def turkey_tree_bytes(big_name: str) -> bytes | None:
    parts = Path(big_name.replace("\\", "/")).parts
    if "Turkey Armed Forces" in parts:
        idx = parts.index("Turkey Armed Forces")
        rel = Path(*parts[idx:])
        path = ROOT / "Data" / "INI" / "Object" / "Specter" / rel
        if path.is_file():
            return path.read_bytes()
        return None
    # Extra overlays (normalized path suffix match)
    norm = big_name.replace("\\", "/")
    for suffix, path in EXTRA_OVERLAYS.items():
        if norm.endswith(suffix) and path.is_file():
            return path.read_bytes()
    return None


def validate_packed(entries, art_entries) -> list[str]:
    fails: list[str] = []
    cats = turkey_wo.catalog(entries)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }
    # Critical objects / worker fix
    for need in ("Turkey_Worker", "Turkey_WorkerCommandSet", "Turkey_WeaponObjects"):
        # WorkerCommandSet is CommandSet; others Object / file presence
        pass
    if "Turkey_Worker" not in cats["Object"]:
        fails.append("missing Object Turkey_Worker")
    if "Turkey_WorkerCommandSet" not in cats["CommandSet"]:
        fails.append("missing CommandSet Turkey_WorkerCommandSet")

    worker = next(
        (
            b.decode("utf-8", "replace")
            for n, b in entries
            if n.replace("\\", "/").endswith("Turkey_Worker.ini")
        ),
        "",
    )
    if "CommandSet = GLAWorkerCommandSet\n" in worker.replace("\r\n", "\n"):
        fails.append("Turkey_Worker still references missing GLAWorkerCommandSet")
    if "CommandSet = Turkey_WorkerCommandSet" not in worker:
        fails.append("Turkey_Worker missing Turkey_WorkerCommandSet upgrade target")
    if "Model         = UIWRKR_SKN" in worker or "Model = UIWRKR_SKN" in worker:
        fails.append("Turkey_Worker still uses missing UIWRKR_SKN")

    if "UAE_Worker" not in cats["Object"]:
        fails.append("missing Object UAE_Worker")
    if "UAE_WorkerCommandSet" not in cats["CommandSet"]:
        fails.append("missing CommandSet UAE_WorkerCommandSet")
    uae_worker = next(
        (
            b.decode("utf-8", "replace")
            for n, b in entries
            if n.replace("\\", "/").endswith("UAE_Worker.ini")
        ),
        "",
    )
    uae_norm = uae_worker.replace("\r\n", "\n")
    if re.search(r"(?m)^\s*CommandSet\s*=\s*GLAWorkerCommandSet\s*$", uae_norm):
        fails.append("UAE_Worker still references missing GLAWorkerCommandSet")
    if "CommandSet = UAE_WorkerCommandSet" not in uae_norm:
        fails.append("UAE_Worker missing UAE_WorkerCommandSet")
    if re.search(r"(?m)^\s*Model\s*=\s*UIWRKR_SKN\b", uae_norm):
        fails.append("UAE_Worker still uses missing UIWRKR_SKN")
    if any(ord(c) > 127 for c in uae_worker):
        fails.append("UAE_Worker has non-ASCII bytes")

    uae_wf = next(
        (
            b.decode("utf-8", "replace")
            for n, b in entries
            if n.replace("\\", "/").endswith("UAE_WarFactory.ini")
        ),
        "",
    )
    uae_wf_body = "\n".join(l.split(";", 1)[0] for l in uae_wf.splitlines())
    if "UBArmDeal_DNS" in uae_wf_body:
        fails.append("UAE_WarFactory still uses missing UBArmDeal_DNS model")
    if "Object UAE_WarFactory_T" not in uae_wf:
        fails.append("missing Object UAE_WarFactory_T in UAE_WarFactory.ini")
    if any(ord(c) > 127 for c in uae_wf):
        fails.append("UAE_WarFactory has non-ASCII bytes")

    tank = next(
        (
            b.decode("utf-8", "replace")
            for n, b in entries
            if "Turkey_Projectile_Tank.ini" in n.replace("\\", "/")
        ),
        "",
    )
    if "AVTankShel" in tank:
        fails.append("Turkey_Projectile_Tank still uses AVTankShel")
    if "Irq_255mm_Round" not in tank:
        fails.append("Turkey_Projectile_Tank missing Irq_255mm_Round")

    # Turkey Model W3D scan
    for n, b in entries:
        if "Turkey Armed Forces" not in n.replace("/", "\\") or not n.lower().endswith(".ini"):
            continue
        t = b.decode("utf-8", "replace")
        bn = Path(n.replace("\\", "/")).name
        for model in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", t)):
            if model in ("None", "NONE"):
                continue
            if model.lower() not in stems:
                fails.append(f"{bn}: missing W3D Model={model}")
        for cs in re.findall(r"(?m)^\s*CommandSet\s*=\s*(\S+)", t):
            if cs not in cats["CommandSet"]:
                fails.append(f"{bn}: missing CommandSet {cs}")
    return fails


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing baseline BIG {SRC}")
    if not TUR_TREE.is_dir():
        raise SystemExit(f"missing Turkey tree {TUR_TREE}")

    entries = base.parse_big(SRC)
    art_entries = base.parse_big(ART) if ART.is_file() else []

    updated: list[str] = []
    rebuilt: list[tuple[str, bytes]] = []
    for name, raw in entries:
        tree = turkey_tree_bytes(name)
        if tree is not None and tree != raw:
            rebuilt.append((name, tree))
            updated.append(name)
        elif tree is not None:
            rebuilt.append((name, tree))
        else:
            rebuilt.append((name, raw))

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, rebuilt)

    packed = base.parse_big(out_big)
    fails = validate_packed(packed, art_entries)
    if fails:
        print("VALIDATE FAIL")
        for f in fails[:80]:
            print(" ", f)
        return 1

    big_sha = base.sha256_file(out_big)
    zip_path = OUT / "SPECTER_PR206_TEST_BUILD.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, arcname="_SPEC_DATA_ONE.big")
        zf.writestr(
            "README_INSTALL.txt",
            (OUT / "README_INSTALL.txt").read_text(encoding="ascii")
            if (OUT / "README_INSTALL.txt").is_file()
            else "",
        )
    # rewrite zip properly after docs written below

    (OUT / "CHANGED_TURKEY_INIS.txt").write_text(
        "Turkey INI paths embedded from PR #206 tree (diff vs baseline BIG):\n"
        + "\n".join(updated)
        + f"\n\ncount={len(updated)}\n",
        encoding="ascii",
        errors="replace",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER PR #206 TEST BUILD\n"
        "==========================\n\n"
        "Baseline: PR #206 Turkey WeaponObjects full rebuild BIG\n"
        "Plus: current PR #206 branch Turkey Armed Forces INI fixes embedded.\n\n"
        "NOT included: PR #207 / #208 faction reset work.\n"
        "No faction rebuild was performed for this package.\n\n"
        "Install:\n"
        "1. Backup your current Data\\_SPEC_DATA_ONE.big\n"
        "2. Replace Data\\_SPEC_DATA_ONE.big with this package file\n"
        "3. Keep Data\\_SPEC_ART_ONE.big unchanged\n"
        "4. Launch skirmish as Turkey and smoke-test worker/infantry/buildings\n\n"
        "After successful test: merge PR #206 and cut final release.\n",
        encoding="ascii",
    )
    (OUT / "VERIFY_REPORT.txt").write_text(
        "SPECTER PR #206 TEST BUILD - VERIFY\n"
        "==================================\n"
        "VERDICT: PASS\n"
        f"Baseline BIG: {SRC}\n"
        f"Turkey INIs updated from tree: {len(updated)}\n"
        "Checks: Worker CommandSet/W3D, tank projectile model, Turkey Model/CommandSet scan\n"
        f"BIG SHA256: {big_sha}\n"
        f"BIG SIZE: {out_big.stat().st_size}\n"
        "FINAL: PASS\n",
        encoding="ascii",
    )

    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, arcname="_SPEC_DATA_ONE.big")
        for doc in (
            "README_INSTALL.txt",
            "VERIFY_REPORT.txt",
            "CHANGED_TURKEY_INIS.txt",
            "HASHES.txt",
        ):
            # HASHES written next; skip if missing on first pass
            pass
    # write hashes then final zip
    zip_sha_placeholder = ""
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={out_big.stat().st_size}\n",
        encoding="ascii",
    )
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, arcname="_SPEC_DATA_ONE.big")
        zf.write(OUT / "README_INSTALL.txt", arcname="README_INSTALL.txt")
        zf.write(OUT / "VERIFY_REPORT.txt", arcname="VERIFY_REPORT.txt")
        zf.write(OUT / "CHANGED_TURKEY_INIS.txt", arcname="CHANGED_TURKEY_INIS.txt")
        zf.write(OUT / "HASHES.txt", arcname="HASHES.txt")
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={out_big.stat().st_size}\n"
        f"SPECTER_PR206_TEST_BUILD.zip SHA256={zip_sha}\n",
        encoding="ascii",
    )
    # refresh zip with final HASHES
    zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, arcname="_SPEC_DATA_ONE.big")
        zf.write(OUT / "README_INSTALL.txt", arcname="README_INSTALL.txt")
        zf.write(OUT / "VERIFY_REPORT.txt", arcname="VERIFY_REPORT.txt")
        zf.write(OUT / "CHANGED_TURKEY_INIS.txt", arcname="CHANGED_TURKEY_INIS.txt")
        zf.write(OUT / "HASHES.txt", arcname="HASHES.txt")
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={out_big.stat().st_size}\n"
        f"SPECTER_PR206_TEST_BUILD.zip SHA256={zip_sha}\n",
        encoding="ascii",
    )

    print(f"Updated Turkey INIs: {len(updated)}")
    print(f"BIG SHA256={big_sha}")
    print(f"ZIP SHA256={zip_sha}")
    print(f"OUT={OUT}")
    print("FINAL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
