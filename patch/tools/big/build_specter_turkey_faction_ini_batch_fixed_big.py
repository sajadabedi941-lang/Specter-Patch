#!/usr/bin/env python3
"""Repair all Turkey_* INI files inside _SPEC_DATA_ONE.big.

Syncs already-cleaned tree versions for repaired aircraft/drone units, then
ASCII-sanitizes and structurally repairs remaining Turkey_* entries:

- Replace non-ASCII punctuation/letters (--, x, i, u)
- Remove invalid ArmorSetFlag fields inside ArmorUpgrade
- Deduplicate Shadow = SHADOW_VOLUME per Object (keep first)
- Comment out bare invalid prose lines that are not End/openers/assignments
- Preserve Side=Turkey identity

Validates every Turkey_* basename under Turkey Armed Forces, writes BIG,
extract/byte-match verifies changed entries, and packs a ZIP release package.
"""
from __future__ import annotations

import re
import shutil
import zipfile
from collections import Counter
from pathlib import Path

import build_specter_aircraft_aab_global_fixed_big as base

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_MILITARYHQ_STOCK_FIXED" / "_SPEC_DATA_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_FACTION_FIXED"
TREE_ROOT = ROOT / "Data/INI/Object/Specter/Turkey Armed Forces"

# Prefer these cleaned tree files over older broken BIG blobs.
TREE_PREFERRED = {
    r"Data\INI\Object\Specter\Turkey Armed Forces\Airforce\Turkey_Akinci.ini",
    r"Data\INI\Object\Specter\Turkey Armed Forces\Airforce\Turkey_F16Block70.ini",
    r"Data\INI\Object\Specter\Turkey Armed Forces\Airforce\Turkey_TB2.ini",
    r"Data\INI\Object\Specter\Turkey Armed Forces\Airforce\Turkey_Tu-22M3.ini",
    r"Data\INI\Object\Specter\Turkey Armed Forces\Airforce\Turkey_Tu-22M3_AI.ini",
    r"Data\INI\Object\Specter\Turkey Armed Forces\Drones\Turkey_Kizilelma.ini",
}

FOCUS = {
    "Turkey_Akinci.ini",
    "Turkey_AWACS.ini",
    "Turkey_Bora.ini",
    "Turkey_EliteMaroonBerets.ini",
    "Turkey_F16Block70.ini",
    "Turkey_Kizilelma.ini",
    "Turkey_TB2.ini",
    "Turkey_Tu-22M3.ini",
    "Turkey_WeaponObjects.ini",
}

ASCII_MAP = {
    "—": "-",
    "–": "-",
    "×": "x",
    "ı": "i",
    "İ": "I",
    "ü": "u",
    "Ü": "U",
    "ö": "o",
    "Ö": "O",
    "ş": "s",
    "Ş": "S",
    "ğ": "g",
    "Ğ": "G",
    "ç": "c",
    "Ç": "C",
    "’": "'",
    "‘": "'",
    "“": '"',
    "”": '"',
    "…": "...",
    "\u00a0": " ",
}


def tree_path_for(entry_name: str) -> Path:
    parts = Path(entry_name.replace("\\", "/")).parts
    idx = list(parts).index("Turkey Armed Forces")
    return TREE_ROOT / Path(*parts[idx + 1 :])


def is_turkey_star(entry_name: str) -> bool:
    if "Turkey Armed Forces" not in entry_name.replace("/", "\\"):
        return False
    if not entry_name.lower().endswith(".ini"):
        return False
    return Path(entry_name.replace("\\", "/")).name.startswith("Turkey_")


def sanitize_ascii(text: str) -> tuple[str, int]:
    removed = sum(ord(c) > 127 for c in text)
    for old, new in ASCII_MAP.items():
        text = text.replace(old, new)
    # Final defensive pass for any unexpected non-ASCII.
    if any(ord(c) > 127 for c in text):
        text = "".join(c if ord(c) < 128 else "?" for c in text)
    return text, removed


def dedupe_shadow_volume(text: str) -> tuple[str, int]:
    """Keep only the first Shadow = SHADOW_VOLUME inside each Object."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    out: list[str] = []
    in_object = False
    seen_volume = False
    removed = 0
    for line in lines:
        code = line.split(";", 1)[0]
        if re.match(r"^\s*Object\s+(?![=])\S+", code):
            in_object = True
            seen_volume = False
            out.append(line)
            continue
        if in_object and re.match(r"^\s*End\s*$", code):
            # End may close nested blocks; Shadow lives at Object root usually.
            # Still allow End through; seen_volume resets only on next Object.
            out.append(line)
            continue
        if re.match(r"^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", code):
            if seen_volume:
                removed += 1
                continue
            seen_volume = True
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") or text.endswith("\r\n") else ""), removed


def remove_armor_set_flag(text: str) -> tuple[str, int]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    out: list[str] = []
    removed = 0
    for line in lines:
        if re.match(r"^\s*ArmorSetFlag\s*=", line):
            removed += 1
            continue
        out.append(line)
    return "\n".join(out) + ("\n" if out else ""), removed


def comment_bare_invalid_lines(text: str) -> tuple[str, int]:
    """Comment prose lines that are not assignments, End, or known openers."""
    opener = re.compile(
        r"^\s*(Object|Draw|Behavior|Body|ArmorSet|WeaponSet|Prerequisites|"
        r"UnitSpecificSounds|DefaultConditionState|ConditionState|TransitionState|"
        r"LocomotorSet|Turret|Animation|AnimationState|ClientUpdate|ParticleSysBone|"
        r"ModuleTag|AttackRadiusDebris|FireWeaponWhenDamaged|FireWeaponWhenDead|"
        r"ReplaceSelf|SpecialPower|OCLSpecialPower)\b"
    )
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    out: list[str] = []
    fixed = 0
    for line in lines:
        code = line.split(";", 1)[0]
        stripped = code.strip()
        if not stripped:
            out.append(line)
            continue
        if re.match(r"^\s*End\s*$", code):
            out.append(line)
            continue
        if "=" in code:
            out.append(line)
            continue
        if opener.match(code):
            out.append(line)
            continue
        # Bare identifier-only lines are treated as block headers (e.g. Turret).
        if re.match(r"^\s*[A-Za-z_][A-Za-z0-9_]*\s*$", code):
            out.append(line)
            continue
        # Prose / invalid statement -> comment it.
        indent = re.match(r"^(\s*)", line).group(1)
        out.append(f"{indent}; {stripped}")
        fixed += 1
    return "\n".join(out) + ("\n" if out else ""), fixed


def repair_text(text: str) -> tuple[str, dict[str, int]]:
    text, non_ascii = sanitize_ascii(text)
    text, armor_flags = remove_armor_set_flag(text)
    text, shadows = dedupe_shadow_volume(text)
    text, bare = comment_bare_invalid_lines(text)
    # Ensure trailing newline and LF endings.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"
    stats = {
        "non_ascii": non_ascii,
        "armor_flags": armor_flags,
        "dup_shadow": shadows,
        "bare_lines": bare,
    }
    return text, stats


def object_shadow_failures(text: str) -> list[str]:
    fails: list[str] = []
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Object\s+(\S+)", text)]
    for i, (start, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        block = text[start:end]
        vols = re.findall(r"(?m)^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", block)
        if len(vols) > 1:
            fails.append(f"{name}: duplicate Shadow=SHADOW_VOLUME x{len(vols)}")
    return fails


def validate_turkey_file(text: str, entry_name: str, label: str) -> list[str]:
    fails: list[str] = []
    bn = Path(entry_name.replace("\\", "/")).name
    if any(ord(c) > 127 for c in text):
        fails.append(f"{label}/{bn}: non-ASCII remains")
    if re.search(r"(?m)^\s*ArmorSetFlag\s*=", text):
        fails.append(f"{label}/{bn}: ArmorSetFlag remains")
    fails.extend(f"{label}/{bn}: {x}" for x in object_shadow_failures(text))

    # Bare invalid prose (same detector as repair, should be zero).
    for line_no, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0]
        stripped = code.strip()
        if not stripped or re.match(r"^\s*End\s*$", code) or "=" in code:
            continue
        if re.match(
            r"^\s*(Object|Draw|Behavior|Body|ArmorSet|WeaponSet|Prerequisites|"
            r"UnitSpecificSounds|DefaultConditionState|ConditionState|TransitionState|"
            r"LocomotorSet|Turret|Animation|AnimationState|ClientUpdate|ParticleSysBone|"
            r"ModuleTag)\b",
            code,
        ):
            continue
        if re.match(r"^\s*[A-Za-z_][A-Za-z0-9_]*\s*$", code):
            continue
        fails.append(f"{label}/{bn}: bare invalid @{line_no}: {stripped[:60]}")

    objs = re.findall(r"(?m)^Object\s+(\S+)", text)
    if not objs and bn in FOCUS:
        fails.append(f"{label}/{bn}: no Object blocks")

    # Side=Turkey for unit/building objects (skip pure projectile/weapon object files
    # that may omit Side, but require Turkey when Side is present).
    sides = re.findall(r"(?m)^\s*Side\s*=\s*(\S+)", text)
    bad_sides = [s for s in sides if s != "Turkey"]
    if bad_sides:
        fails.append(f"{label}/{bn}: non-Turkey Side={bad_sides}")
    if bn in FOCUS and bn != "Turkey_WeaponObjects.ini":
        if "Turkey" not in sides:
            fails.append(f"{label}/{bn}: missing Side=Turkey")

    # Basic structural markers for focus combat units.
    if bn in FOCUS and bn != "Turkey_WeaponObjects.ini":
        if not re.search(r"(?m)^\s*Draw\s*=", text):
            fails.append(f"{label}/{bn}: Draw missing")
        if not re.search(r"(?m)^\s*Shadow\s*=", text):
            fails.append(f"{label}/{bn}: Shadow missing")
        if "End" not in text:
            fails.append(f"{label}/{bn}: End missing")

    return fails


def source_bytes_for(entry_name: str, big_raw: bytes) -> tuple[bytes, str]:
    """Return preferred source bytes and origin label."""
    kn = base.knorm(entry_name)
    preferred = {base.knorm(p) for p in TREE_PREFERRED}
    tp = tree_path_for(entry_name)
    if kn in preferred and tp.is_file():
        tree_raw = tp.read_bytes()
        tree_text = tree_raw.decode("utf-8", "replace")
        # Only prefer tree if it is already ASCII-clean enough to be the donor.
        if not any(ord(c) > 127 for c in tree_text):
            return tree_raw, "tree"
    return big_raw, "big"


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG: {SRC}")

    entries = base.parse_big(SRC)
    turkey_entries = [(n, r) for n, r in entries if is_turkey_star(n)]
    if len(turkey_entries) < 80:
        raise SystemExit(f"expected ~90 Turkey_* entries, got {len(turkey_entries)}")
    print(f"Turkey_* entries in BIG: {len(turkey_entries)}")

    repaired: dict[str, bytes] = {}
    stats_total = Counter()
    origins: dict[str, str] = {}
    focus_changed: list[str] = []

    for name, raw in turkey_entries:
        src_raw, origin = source_bytes_for(name, raw)
        origins[base.knorm(name)] = origin
        text = src_raw.decode("utf-8", "replace")
        fixed, stats = repair_text(text)
        for k, v in stats.items():
            stats_total[k] += v
        fixed_raw = fixed.encode("ascii")
        repaired[base.knorm(name)] = fixed_raw
        bn = Path(name.replace("\\", "/")).name
        if bn in FOCUS and fixed_raw != raw:
            focus_changed.append(bn)
        print(
            f"  {bn}: origin={origin} nonASCII={stats['non_ascii']} "
            f"ArmorSetFlag={stats['armor_flags']} dupShadow={stats['dup_shadow']} "
            f"bare={stats['bare_lines']} changed={fixed_raw != raw}"
        )

    candidate = [
        (name, repaired[base.knorm(name)] if base.knorm(name) in repaired else raw)
        for name, raw in entries
    ]

    # Pre-write validation for all Turkey_*.
    failures: list[str] = []
    for name, _ in turkey_entries:
        text = repaired[base.knorm(name)].decode("ascii")
        failures.extend(validate_turkey_file(text, name, "PREWRITE"))
    if failures:
        print("PRE-WRITE VALIDATION FAILED")
        for f in failures[:80]:
            print(" ", f)
        if len(failures) > 80:
            print(f"  ... +{len(failures) - 80} more")
        return 1
    print(f"PASS pre-write validation Turkey_*={len(turkey_entries)}")

    # Ensure focus set present and Side retained.
    for focus in FOCUS:
        hits = [n for n, _ in turkey_entries if Path(n.replace("\\", "/")).name == focus]
        if not hits:
            raise SystemExit(f"missing focus file {focus}")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, candidate)

    rebuilt = base.parse_big(out_big)
    rebuilt_by = {base.knorm(n): (n, r) for n, r in rebuilt}
    extract_root = OUT / "_EXTRACT_VERIFY"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True)

    old_by = {base.knorm(n): r for n, r in entries}
    changed_names: list[str] = []
    for name, raw in rebuilt:
        if raw != old_by[base.knorm(name)]:
            changed_names.append(name)

    # Only Turkey_* may change.
    bad_changed = [n for n in changed_names if base.knorm(n) not in repaired]
    if bad_changed:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"unrelated BIG entries changed: {bad_changed[:20]}")

    # Extract/byte-match every Turkey_* and validate.
    post_fails: list[str] = []
    for name, _ in turkey_entries:
        emb_name, emb = rebuilt_by[base.knorm(name)]
        expected = repaired[base.knorm(name)]
        if emb != expected:
            post_fails.append(f"byte mismatch: {name}")
            continue
        rel = Path(*Path(emb_name.replace("\\", "/")).parts)
        extract_path = extract_root / rel
        extract_path.parent.mkdir(parents=True, exist_ok=True)
        extract_path.write_bytes(emb)
        if extract_path.read_bytes() != expected:
            post_fails.append(f"disk extract mismatch: {name}")
            continue
        # Sync tree.
        tp = tree_path_for(emb_name)
        tp.parent.mkdir(parents=True, exist_ok=True)
        tp.write_bytes(expected)
        post_fails.extend(
            validate_turkey_file(emb.decode("ascii"), emb_name, "EXTRACTED")
        )

    if post_fails:
        out_big.unlink(missing_ok=True)
        print("EXTRACT VALIDATION FAILED - BIG deleted")
        for f in post_fails[:80]:
            print(" ", f)
        return 1

    big_sha = base.sha256_file(out_big)
    big_size = out_big.stat().st_size
    changed_turkey = [n for n in changed_names if is_turkey_star(n)]
    print(f"CHANGED Turkey_* files: {len(changed_turkey)}")
    print(f"STATS {dict(stats_total)}")
    print(f"BIG SHA256={big_sha} SIZE={big_size}")

    # Package docs
    focus_lines = []
    for focus in sorted(FOCUS):
        hits = [n for n, _ in turkey_entries if Path(n.replace("\\", "/")).name == focus]
        name = hits[0]
        raw_new = repaired[base.knorm(name)]
        focus_lines.append(
            f"- {focus}: sha256={base.sha256_bytes(raw_new)} origin={origins[base.knorm(name)]}"
        )

    report = (
        "SPECTER TURKEY FACTION INI BATCH FIX - VERIFY REPORT\n"
        "====================================================\n"
        "VERDICT: PASS\n"
        "Patched INSIDE: _SPEC_DATA_ONE.big\n"
        f"Turkey_* files validated: {len(turkey_entries)}\n"
        f"Turkey_* files changed: {len(changed_turkey)}\n"
        f"Non-ASCII characters removed: {stats_total['non_ascii']}\n"
        f"Invalid ArmorSetFlag fields removed: {stats_total['armor_flags']}\n"
        f"Duplicate Shadow=SHADOW_VOLUME removed: {stats_total['dup_shadow']}\n"
        f"Bare invalid lines commented: {stats_total['bare_lines']}\n"
        "Tree-synced cleaned donors: Akinci/F16Block70/TB2/Tu-22M3/Tu-22M3_AI/Kizilelma\n"
        "Object/Draw/Shadow/Side/ArmorSetFlag/ASCII validation: PASS\n"
        "Extract-from-BIG byte match: PASS\n"
        "Unrelated BIG entries changed: 0\n"
        "\nFocus files:\n"
        + "\n".join(focus_lines)
        + f"\n\nBIG SHA256: {big_sha}\n"
        f"BIG SIZE: {big_size}\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT TEST\n"
        "====================\n"
        f"turkey_star_count={len(turkey_entries)}\n"
        f"changed_count={len(changed_turkey)}\n"
        "byte_match=YES\nfull_validation=PASS\n"
        "ArmorSetFlag_remaining=0\nnon_ascii_remaining=0\n"
        "unrelated_changed=0\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Turkey_star_changed={len(changed_turkey)}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER TURKEY FACTION INI BATCH FIX\n"
        "====================================\n\n"
        "All Turkey_* INI files under Turkey Armed Forces repaired inside\n"
        "_SPEC_DATA_ONE.big. Cleaned tree donors synced for key aircraft/drones.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )
    (OUT / "CHANGED_TURKEY_FILES.txt").write_text(
        "\n".join(sorted(changed_turkey)) + "\n", encoding="ascii"
    )

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in ("HASHES.txt", "VERIFY_REPORT.txt", "README_INSTALL.txt", "EMBED_PROOF.txt"):
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_TURKEY_FACTION_FIXED.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "HASHES.txt",
            "VERIFY_REPORT.txt",
            "README_INSTALL.txt",
            "EMBED_PROOF.txt",
            "CHANGED_TURKEY_FILES.txt",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"_SPEC_DATA_ONE_TURKEY_FACTION_FIXED.zip SHA256={zip_sha}\n"
        f"Turkey_star_changed={len(changed_turkey)}\n",
        encoding="ascii",
    )
    print(f"ZIP SHA256={zip_sha}")
    print("FINAL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
