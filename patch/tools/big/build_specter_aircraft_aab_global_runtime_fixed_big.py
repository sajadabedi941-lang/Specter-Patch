#!/usr/bin/env python3
"""Runtime parser repair for Aircraft_AAB_Global.ini inside the released BIG.

The prior GitHub release was re-downloaded and its embedded INI matched the
ASCII-fixed SHA exactly. A stricter module-schema audit found the remaining
parser defect: ArmorSetFlag is not a valid field of ArmorUpgrade. It occurred
27 times. This builder removes only those invalid fields from the one embedded
INI entry, then repeats full validation and extract/byte-match verification.
"""
from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

import build_specter_aircraft_aab_global_fixed_big as prior

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_AAB_GLOBAL_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_AAB_GLOBAL_RUNTIME_FIXED"
TARGET = prior.TARGET
TREE = prior.TREE

EXPECTED_SOURCE_BIG_SHA = "20309b99ead463f412f0b407933a789f3d4a3c38ffdfdbb95f7756fac7e9712d"
EXPECTED_SOURCE_INI_SHA = "3c7e7d404cd62e3014310b3c62247c8274ae81c3a50e9c6d5acf8fcee8180baf"


def strip_invalid_armor_upgrade_field(text: str) -> tuple[str, int]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    output: list[str] = []
    removed = 0
    for line in lines:
        if re.match(r"^\s*ArmorSetFlag\s*=", line):
            removed += 1
            continue
        output.append(line)
    return "\r\n".join(output) + "\r\n", removed


def armor_upgrade_schema_failures(text: str) -> list[str]:
    """ArmorUpgrade accepts TriggeredBy/etc., but not ArmorSetFlag."""
    failures: list[str] = []
    if re.search(r"(?m)^\s*ArmorSetFlag\s*=", text):
        failures.append("invalid ArmorUpgrade field ArmorSetFlag remains")

    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^\s*Behavior\s*=\s*ArmorUpgrade\s+(\S+)", line)
        if not match:
            continue
        tag = match.group(1)
        fields: list[str] = []
        cursor = index + 1
        while cursor < len(lines) and not re.match(r"^\s*End\s*$", lines[cursor]):
            code = lines[cursor].split(";", 1)[0].strip()
            if "=" in code:
                fields.append(code.split("=", 1)[0].strip())
            cursor += 1
        allowed = {"TriggeredBy", "FXListUpgrade", "ConflictsWith", "RequiresAllTriggers"}
        invalid = sorted(set(fields) - allowed)
        if invalid:
            failures.append(f"{tag}: invalid ArmorUpgrade fields {invalid}")
    return failures


def main() -> int:
    if prior.sha256_file(SRC) != EXPECTED_SOURCE_BIG_SHA:
        raise SystemExit("source BIG is not the rechecked GitHub release build")

    entries = prior.parse_big(SRC)
    by = {prior.knorm(name): (name, raw) for name, raw in entries}
    entry_name, old_raw = by[prior.knorm(TARGET)]
    if prior.sha256_bytes(old_raw) != EXPECTED_SOURCE_INI_SHA:
        raise SystemExit("source embedded INI is not the prior fixed version")
    print("PASS source BIG matches downloaded release")
    print("PASS embedded INI matches prior fixed SHA")

    old_text = old_raw.decode("ascii")
    fixed_text, removed = strip_invalid_armor_upgrade_field(old_text)
    if removed != 27:
        raise SystemExit(f"expected 27 invalid ArmorSetFlag fields, found {removed}")
    print(f"REMOVED invalid ArmorSetFlag fields={removed}")

    fixed_raw = fixed_text.encode("ascii")
    candidate = [
        (name, fixed_raw if prior.knorm(name) == prior.knorm(TARGET) else raw)
        for name, raw in entries
    ]
    art_entries = prior.parse_big(ART)
    failures = prior.validate(fixed_text, candidate, art_entries, "PREWRITE")
    failures += armor_upgrade_schema_failures(fixed_text)
    if failures:
        print("PRE-WRITE VALIDATION FAILED")
        for failure in failures:
            print(" ", failure)
        return 1
    print(f"PASS pre-write objects={len(prior.object_blocks(fixed_text))}")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    prior.write_big(out_big, candidate)
    rebuilt = prior.parse_big(out_big)
    rebuilt_by = {prior.knorm(name): (name, raw) for name, raw in rebuilt}
    embedded_name, embedded = rebuilt_by[prior.knorm(TARGET)]
    if embedded != fixed_raw:
        raise SystemExit("embedded bytes do not match repaired source")

    extracted_text = embedded.decode("ascii")
    failures = prior.validate(extracted_text, rebuilt, art_entries, "EXTRACTED")
    failures += armor_upgrade_schema_failures(extracted_text)
    if failures:
        out_big.unlink(missing_ok=True)
        print("EXTRACTED VALIDATION FAILED - BIG deleted")
        for failure in failures:
            print(" ", failure)
        return 1

    rel = Path(*Path(embedded_name.replace("\\", "/")).parts)
    extract_path = OUT / "_EXTRACT_VERIFY" / rel
    extract_path.parent.mkdir(parents=True, exist_ok=True)
    extract_path.write_bytes(embedded)
    if extract_path.read_bytes() != fixed_raw:
        raise SystemExit("disk extract bytes differ from repaired source")

    old_by = {prior.knorm(name): raw for name, raw in entries}
    changed = [
        name
        for name, raw in rebuilt
        if raw != old_by[prior.knorm(name)]
    ]
    if changed != [entry_name]:
        raise SystemExit(f"unrelated BIG entries changed: {changed}")

    TREE.write_bytes(fixed_raw)
    (OUT / "Aircraft_AAB_Global.ini").write_bytes(fixed_raw)
    big_sha = prior.sha256_file(out_big)
    ini_sha = prior.sha256_bytes(fixed_raw)
    big_size = out_big.stat().st_size

    report = (
        "SPECTER AIRCRAFT AAB GLOBAL RUNTIME FIX - VERIFY REPORT\n"
        "=======================================================\n"
        "VERDICT: PASS\n"
        "Rechecked downloaded GitHub release BIG: MATCH\n"
        "Prior embedded ASCII-fixed INI: MATCH\n"
        "Root cause: invalid ArmorSetFlag fields inside ArmorUpgrade modules\n"
        f"Invalid fields removed: {removed}\n"
        f"Objects validated: {len(prior.object_blocks(fixed_text))}\n"
        "Object/Draw/Shadow/ModuleTag/Behavior/WeaponSet/End: PASS\n"
        "ArmorUpgrade module schema: PASS\n"
        "W3D/Art/Weapon/CommandSet/Armor/Upgrade/OCL/SpecialPower refs: PASS\n"
        "Extract-from-BIG byte match: PASS\n"
        "Unrelated BIG entries changed: 0\n"
        f"\nOld INI SHA256: {prior.sha256_bytes(old_raw)}\n"
        f"New INI SHA256: {ini_sha}\n"
        f"BIG SHA256: {big_sha}\n"
        f"BIG SIZE: {big_size}\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT TEST\n"
        "====================\n"
        f"entry={embedded_name}\n"
        f"source_sha256={ini_sha}\n"
        f"embedded_sha256={prior.sha256_bytes(embedded)}\n"
        f"extracted_sha256={prior.sha256_bytes(extract_path.read_bytes())}\n"
        "byte_match=YES\n"
        "full_validation=PASS\n"
        "ArmorSetFlag_remaining=0\n"
        "unrelated_changed=0\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Aircraft_AAB_Global.ini SHA256={ini_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER AIRCRAFT AAB GLOBAL RUNTIME FIX\n"
        "======================================\n\n"
        "Rechecked released BIG and removed invalid ArmorSetFlag fields\n"
        "from Aircraft_AAB_Global.ini inside _SPEC_DATA_ONE.big.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in (
            "HASHES.txt",
            "VERIFY_REPORT.txt",
            "README_INSTALL.txt",
            "EMBED_PROOF.txt",
            "Aircraft_AAB_Global.ini",
        ):
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_AAB_GLOBAL_RUNTIME_FIXED.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "Aircraft_AAB_Global.ini", "Aircraft_AAB_Global.ini")
        zf.write(extract_path, "EXTRACT_VERIFY/Aircraft_AAB_Global.ini")
        for name in ("VERIFY_REPORT.txt", "EMBED_PROOF.txt", "HASHES.txt", "README_INSTALL.txt"):
            zf.write(OUT / name, name)
    if final_dir.is_dir():
        shutil.copy2(zip_path, final_dir / "_SPEC_DATA_ONE_FINAL.zip")

    print(report)
    print("BIG", out_big, big_sha, big_size)
    print("ZIP", zip_path, prior.sha256_file(zip_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
