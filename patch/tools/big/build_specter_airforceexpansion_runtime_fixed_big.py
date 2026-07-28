#!/usr/bin/env python3
"""Repair Aircraft_AirForceExpansion.ini inside _SPEC_DATA_ONE.big.

Changes only the target entry:
- ASCII-sanitize comment punctuation
- Remove invalid ArmorSetFlag fields from ArmorUpgrade modules
- Validate all 12 Objects, structures, module schema, refs and exact W3Ds
- Extract from rebuilt BIG and byte-match the repaired source
"""
from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

import build_specter_aircraft_aab_global_fixed_big as base
import build_specter_aircraft_aab_global_runtime_fixed_big as runtime

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_RUSSIA_TORM_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_AIRFORCEEXPANSION_FIXED"
TARGET = r"Data\INI\Object\Specter\PatchSystems\AirForceExpansion\Aircraft_AirForceExpansion.ini"
TREE = ROOT / "Data/INI/Object/Specter/PatchSystems/AirForceExpansion/Aircraft_AirForceExpansion.ini"


def repair(text: str) -> tuple[str, int, int]:
    replacements = {"—": "-", "×": "x"}
    non_ascii = sum(ord(c) > 127 for c in text)
    for old, new in replacements.items():
        text = text.replace(old, new)
    if any(ord(c) > 127 for c in text):
        remaining = sorted({f"U+{ord(c):04X}" for c in text if ord(c) > 127})
        raise SystemExit(f"unexpected non-ASCII remains: {remaining}")

    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    output: list[str] = []
    removed = 0
    for line in lines:
        if re.match(r"^\s*ArmorSetFlag\s*=", line):
            removed += 1
            continue
        output.append(line)
    return "\r\n".join(output) + "\r\n", non_ascii, removed


def strict_w3d_failures(text: str, art_entries) -> list[str]:
    stems = {
        Path(name.replace("\\", "/")).stem.lower()
        for name, _ in art_entries
        if name.lower().endswith(".w3d")
    }
    return [
        f"missing exact W3D={model}"
        for model in sorted(set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)))
        if model not in ("None", "NONE") and model.lower() not in stems
    ]


def main() -> int:
    entries = base.parse_big(SRC)
    by = {base.knorm(name): (name, raw) for name, raw in entries}
    if base.knorm(TARGET) not in by:
        raise SystemExit("Aircraft_AirForceExpansion.ini missing from BIG")
    entry_name, old_raw = by[base.knorm(TARGET)]
    old_text = old_raw.decode("utf-8", "strict")

    fixed_text, non_ascii_removed, invalid_fields_removed = repair(old_text)
    if non_ascii_removed != 53:
        raise SystemExit(f"expected 53 non-ASCII characters, got {non_ascii_removed}")
    if invalid_fields_removed != 2:
        raise SystemExit(f"expected 2 invalid ArmorSetFlag fields, got {invalid_fields_removed}")
    print(f"REMOVED non-ASCII={non_ascii_removed}")
    print(f"REMOVED invalid ArmorSetFlag={invalid_fields_removed}")

    fixed_raw = fixed_text.encode("ascii")
    candidate = [
        (name, fixed_raw if base.knorm(name) == base.knorm(TARGET) else raw)
        for name, raw in entries
    ]
    art_entries = base.parse_big(ART)
    failures = base.validate(fixed_text, candidate, art_entries, "PREWRITE")
    failures += runtime.armor_upgrade_schema_failures(fixed_text)
    failures += strict_w3d_failures(fixed_text, art_entries)
    if failures:
        print("PRE-WRITE VALIDATION FAILED")
        for failure in failures:
            print(" ", failure)
        return 1
    objects = len(base.object_blocks(fixed_text))
    if objects != 12:
        raise SystemExit(f"expected 12 Objects, got {objects}")
    print("PASS pre-write validation objects=12")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, candidate)
    rebuilt = base.parse_big(out_big)
    rebuilt_by = {base.knorm(name): (name, raw) for name, raw in rebuilt}
    embedded_name, embedded = rebuilt_by[base.knorm(TARGET)]
    if embedded != fixed_raw:
        raise SystemExit("embedded bytes differ from repaired source")

    extracted_text = embedded.decode("ascii")
    failures = base.validate(extracted_text, rebuilt, art_entries, "EXTRACTED")
    failures += runtime.armor_upgrade_schema_failures(extracted_text)
    failures += strict_w3d_failures(extracted_text, art_entries)
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

    old_by = {base.knorm(name): raw for name, raw in entries}
    changed = [
        name
        for name, raw in rebuilt
        if raw != old_by[base.knorm(name)]
    ]
    if changed != [entry_name]:
        raise SystemExit(f"unrelated BIG entries changed: {changed}")

    TREE.write_bytes(fixed_raw)
    (OUT / "Aircraft_AirForceExpansion.ini").write_bytes(fixed_raw)
    big_sha = base.sha256_file(out_big)
    ini_sha = base.sha256_bytes(fixed_raw)
    big_size = out_big.stat().st_size
    weapon_sets = len(re.findall(r"(?m)^\s*WeaponSet\b", fixed_text))
    report = (
        "SPECTER AIR FORCE EXPANSION PARSE FIX - VERIFY REPORT\n"
        "=====================================================\n"
        "VERDICT: PASS\n"
        "Patched INSIDE: _SPEC_DATA_ONE.big\n"
        f"Entry: {entry_name}\n"
        f"Objects validated: {objects}\n"
        f"WeaponSet blocks validated: {weapon_sets}\n"
        f"Non-ASCII characters removed: {non_ascii_removed}\n"
        f"Invalid ArmorSetFlag fields removed: {invalid_fields_removed}\n"
        "Air Force Expansion identity/functionality otherwise unchanged\n"
        "Object/Draw/Shadow/ModuleTag/Behavior/WeaponSet/End: PASS\n"
        "ArmorUpgrade module schema: PASS\n"
        "Exact W3D/art/weapon/commandset/armor/upgrade/OCL/special-power refs: PASS\n"
        "Extract-from-BIG byte match: PASS\n"
        "Unrelated BIG entries changed: 0\n"
        f"\nOld INI SHA256: {base.sha256_bytes(old_raw)}\n"
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
        f"embedded_sha256={base.sha256_bytes(embedded)}\n"
        f"extracted_sha256={base.sha256_bytes(extract_path.read_bytes())}\n"
        "byte_match=YES\nfull_validation=PASS\nArmorSetFlag_remaining=0\n"
        "unrelated_changed=0\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Aircraft_AirForceExpansion.ini SHA256={ini_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER AIR FORCE EXPANSION PARSE FIX\n"
        "====================================\n\n"
        "Aircraft_AirForceExpansion.ini repaired inside _SPEC_DATA_ONE.big.\n"
        "No unrelated BIG entry changed.\n\n"
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
            "Aircraft_AirForceExpansion.ini",
        ):
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_AIRFORCEEXPANSION_FIXED.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "Aircraft_AirForceExpansion.ini", "Aircraft_AirForceExpansion.ini")
        zf.write(extract_path, "EXTRACT_VERIFY/Aircraft_AirForceExpansion.ini")
        for name in ("VERIFY_REPORT.txt", "EMBED_PROOF.txt", "HASHES.txt", "README_INSTALL.txt"):
            zf.write(OUT / name, name)
    if final_dir.is_dir():
        shutil.copy2(zip_path, final_dir / "_SPEC_DATA_ONE_FINAL.zip")

    print(report)
    print("BIG", out_big, big_sha, big_size)
    print("ZIP", zip_path, base.sha256_file(zip_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
