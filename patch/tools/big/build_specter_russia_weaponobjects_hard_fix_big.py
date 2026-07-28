#!/usr/bin/env python3
"""HARD FIX: Russia_WeaponObjects still crashing after prior repair.

Root cause (NULL / EXCEPTION_ACCESS_VIOLATION):
- Cyrillic capital Em U+041C in '9М317' tokens was sanitize_ascii'd to '?'
- Weapon.ini ended up with Weapon 4x_MRSAM_9?317 / 6x_MRSAM_9?317M3
- Russia 9K317.ini still references 4x_MRSAM_9М317 (Cyrillic) -> MISSING weapon -> NULL
- Russia_WeaponObjects locomotor refs became 9?317MissileLocomotor -> MISSING

Hard workflow:
1. DELETE ALL russia_weaponobjects.ini path variants from BIG (no duplicates)
2. Rebuild one clean Russia_WeaponObjects from prior fixed content + ASCII 9M317
3. Normalize 9M317 tokens across Weapon.ini / Locomotor.ini / Russia 9K317.ini
4. Full Russia weapon/projectile/FX/locomotor integrity; extract byte-match; ZIP
"""
from __future__ import annotations

import re
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

import build_specter_aircraft_aab_global_fixed_big as base
import build_specter_russia_weaponobjects_crash_fix_big as prev
import build_specter_turkey_faction_ini_batch_fixed_big as turkey_batch

ROOT = Path(__file__).resolve().parents[2]
SRC = (
    ROOT
    / "Release"
    / "SPECTER_SPEC_DATA_ONE_RUSSIA_WEAPONOBJECTS_CRASH_FIXED"
    / "_SPEC_DATA_ONE.big"
)
# Prefer MERGE original WO only as reference for Cyrillic; primary source is SRC.
MERGE = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_RUSSIA_WEAPONOBJECTS_HARD_FIXED"
TREE = (
    ROOT
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Russia_WeaponObjects.ini"
)
NEW_PATH = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Russia_WeaponObjects.ini"
)
CYR_M = "\u041c"  # Cyrillic capital Em


def is_russia_wo_path(name: str) -> bool:
    """Match ANY russia weaponobjects.ini path variant (case/slash/folder)."""
    ln = name.lower().replace("/", "\\")
    base_name = Path(name.replace("\\", "/")).name.lower()
    if base_name == "russia_weaponobjects.ini":
        return True
    if "weaponobjects.ini" not in ln:
        return False
    return ("russia" in ln) or ("russian" in ln) or ("federation" in ln and "weaponobjects" in ln)


def normalize_9m317_tokens(text: str) -> tuple[str, int]:
    """Map Cyrillic М and corrupted '?' in 9M317 tokens to ASCII M."""
    n = 0
    out = text
    # Cyrillic Em between 9 and 317
    out2, c = re.subn(rf"9{CYR_M}317", "9M317", out)
    out, n = out2, n + c
    # Corrupted question mark left by sanitize_ascii
    out2, c = re.subn(r"9\?317", "9M317", out)
    out, n = out2, n + c
    return out, n


def ascii_safe_russia_wo(text: str) -> tuple[str, dict]:
    """Rebuild WO text with hard crash fixes + ASCII 9M317, without '?' corruption."""
    stats: dict = {}
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Normalize 9M317 BEFORE any sanitize
    text, stats["nine_m317_fixes"] = normalize_9m317_tokens(text)
    # Map remaining Cyrillic Em to ASCII M globally in this file
    if CYR_M in text:
        c = text.count(CYR_M)
        text = text.replace(CYR_M, "M")
        stats["cyr_m_replaced"] = c
    else:
        stats["cyr_m_replaced"] = 0

    text, stats["clientupdate_ends_removed"] = prev.fix_clientupdate_stray_end(text)
    text, stats["model_remaps"] = prev.remap_models(text)
    text, stats["bv_remaps"] = prev.fix_bv_refs(text)
    text, stats["side_forced"] = prev.force_russia_side(text)

    art_stems = getattr(ascii_safe_russia_wo, "_art_stems", set())
    text, stats["none_model_stats"] = prev.fix_none_models(text, art_stems)
    text, more = prev.remap_models(text)
    stats["model_remaps"] = list(stats["model_remaps"]) + more
    text, more317 = normalize_9m317_tokens(text)
    stats["nine_m317_fixes"] += more317

    # Sanitize using map that includes Cyrillic Em -> M (never '?')
    text2 = text
    for old, new in list(turkey_batch.ASCII_MAP.items()) + [(CYR_M, "M")]:
        text2 = text2.replace(old, new)
    # Refuse to emit '?' for leftover non-ascii — drop/replace known safe
    if any(ord(c) > 127 for c in text2):
        bad = sorted({c for c in text2 if ord(c) > 127})
        raise SystemExit(f"non-ASCII remains after map: {[hex(ord(c)) for c in bad]}")
    text = text2

    # Strip prior headers; write hard-fix header
    m = re.search(r"(?m)^Object\s+\S+", text)
    body = text[m.start() :] if m else text
    header = (
        "; SPECTER HARD FIX - Russia_WeaponObjects\n"
        "; EXCEPTION_ACCESS_VIOLATION @ NULL - broken BIG entry fully replaced\n"
        "; - DELETE all russia_weaponobjects.ini variants; INSERT one clean file\n"
        "; - Fixed 9M317 Cyrillic/corrupt '?' locomotor + DisplayName tokens\n"
        "; - Removed ClientUpdate stray Ends; remapped missing W3D/BV; Model=None donors\n"
        "; - Side forced to Russia; object names preserved\n\n"
    )
    cleaned = header + body
    if not cleaned.endswith("\n"):
        cleaned += "\n"
    stats["objects"] = len(re.findall(r"(?m)^Object\s+", cleaned))
    if "9?317" in cleaned or CYR_M in cleaned:
        raise SystemExit("9M317 normalization failed inside WO")
    return cleaned, stats


def patch_text_file(raw: bytes, label: str) -> tuple[bytes, int]:
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    text, n = normalize_9m317_tokens(text)
    if n == 0 and "9?317" not in text and f"9{CYR_M}317" not in text:
        return raw, 0
    # ASCII map without blindly nuking unrelated non-ascii into '?'
    for old, new in list(turkey_batch.ASCII_MAP.items()) + [(CYR_M, "M")]:
        text = text.replace(old, new)
    text, n2 = normalize_9m317_tokens(text)
    n += n2
    if "9?317" in text or f"9{CYR_M}317" in text:
        raise SystemExit(f"{label}: 9M317 token still corrupt")
    # Keep file encoding ascii where possible; if other non-ascii remains, keep UTF-8 bytes
    if any(ord(c) > 127 for c in text):
        return text.encode("utf-8"), n
    return text.encode("ascii"), n


def should_patch_aux(name: str) -> bool:
    ln = name.lower().replace("/", "\\")
    if ln.endswith(r"data\ini\weapon.ini"):
        return True
    if ln.endswith(r"data\ini\locomotor.ini"):
        return True
    if ln.endswith(r"armed forces of russian federation\airdefense\9k317.ini"):
        return True
    # Egypt WO also has corrupt 9?317 locomotor refs
    if "egypt_weaponobjects.ini" in ln:
        return True
    if "northkorea_systems.ini" in ln:
        return True
    return False


def validate_wo(text: str, entries, art_entries, label: str) -> list[str]:
    fails = prev.validate_wo(text, entries, art_entries, label)
    # Override header check from prev (expects CRASH FIX)
    fails = [f for f in fails if "missing crash-fix header" not in f]
    if not text.startswith("; SPECTER HARD FIX - Russia_WeaponObjects"):
        fails.append(f"{label}: missing hard-fix header")
    if "9?317" in text or CYR_M in text:
        fails.append(f"{label}: corrupt 9M317 token remains")
    cats = prev.catalog(entries)
    # Every locomotor in WO must resolve
    for line in text.splitlines():
        m = re.match(r"^\s*Locomotor\s*=\s*(.*)$", line)
        if not m:
            continue
        for tok in m.group(1).split(";")[0].split():
            if tok.startswith("SET_") or tok in ("None", "NONE"):
                continue
            if tok not in cats["Locomotor"]:
                fails.append(f"{label}: missing Locomotor {tok}")
    return fails


def russia_full_integrity(entries, art_entries) -> tuple[list[str], list[str]]:
    fails, warns = prev.russia_integrity_scan(entries, art_entries)
    cats = prev.catalog(entries)
    # Hard: every Russia unit weapon template must exist
    for n, r in entries:
        if not prev.is_russia_object_ini(n):
            continue
        if "WeaponObjects" in n:
            continue
        t = r.decode("utf-8", "replace")
        bn = Path(n.replace("\\", "/")).name
        for w in re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", t):
            if w in ("None", "NONE", "End"):
                continue
            if w.startswith(";") or w.startswith("ExclusiveWeapon"):
                continue
            if w not in cats["Weapon"]:
                fails.append(f"{bn}: missing Weapon template {w!r}")
        # no corrupt 9?317 in russia units
        code_only = "\n".join(
            line.split(";", 1)[0] for line in t.splitlines()
        )
        if "9?317" in code_only or (f"9{CYR_M}317" in t):
            fails.append(f"{bn}: corrupt/Cyrillic 9M317 token")
    # Weapon.ini must expose ASCII 9M317 weapons
    for need in ("4x_MRSAM_9M317", "6x_MRSAM_9M317M3"):
        if need not in cats["Weapon"]:
            fails.append(f"Weapon.ini missing {need}")
    for need in ("9M317MissileLocomotor", "9M317M3MissileLocomotor"):
        if need not in cats["Locomotor"]:
            fails.append(f"Locomotor.ini missing {need}")
    # Prove single WO entry
    hits = [n for n, _ in entries if is_russia_wo_path(n)]
    if len(hits) != 1:
        fails.append(f"russia_weaponobjects.ini count={len(hits)} paths={hits}")
    return fails, warns


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG: {SRC}")
    entries = base.parse_big(SRC)
    art_entries = base.parse_big(ART)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }
    ascii_safe_russia_wo._art_stems = stems

    # --- HARD DELETE all russia weaponobjects variants ---
    old_hits = [(n, r) for n, r in entries if is_russia_wo_path(n)]
    print(f"DELETE phase: {len(old_hits)} russia_weaponobjects.ini variant(s)")
    if not old_hits:
        raise SystemExit("no russia weaponobjects entries found to delete")
    old_shas = {base.sha256_bytes(r) for _, r in old_hits}
    old_raw = old_hits[0][1]
    old_names = set(
        re.findall(r"(?m)^Object\s+(\S+)", old_raw.decode("utf-8", "replace"))
    )
    for n, r in old_hits:
        print(f"  removing {n!r} sha={base.sha256_bytes(r)[:16]} size={len(r)}")

    purged = [(n, r) for n, r in entries if not is_russia_wo_path(n)]
    # Belt-and-suspenders: purge again by knorm basename
    purged2 = []
    for n, r in purged:
        if Path(n.replace("\\", "/")).name.lower() == "russia_weaponobjects.ini":
            print(f"  EXTRA delete by basename: {n!r}")
            old_shas.add(base.sha256_bytes(r))
            continue
        purged2.append((n, r))
    purged = purged2

    cleaned, stats = ascii_safe_russia_wo(old_raw.decode("utf-8", "replace"))
    new_raw = cleaned.encode("ascii")
    if base.sha256_bytes(new_raw) in old_shas:
        raise SystemExit("new WO hash collides with deleted entry")
    new_names = set(re.findall(r"(?m)^Object\s+(\S+)", cleaned))
    if new_names != old_names:
        raise SystemExit(
            "object set changed "
            f"missing={sorted(old_names - new_names)[:10]} "
            f"extra={sorted(new_names - old_names)[:10]}"
        )
    print(
        f"NEW WO sha={base.sha256_bytes(new_raw)[:16]} size={len(new_raw)} "
        f"objs={stats['objects']} nine_m317={stats['nine_m317_fixes']} "
        f"cu={stats['clientupdate_ends_removed']}"
    )

    # Patch aux files (Weapon / Locomotor / 9K317 / Egypt WO / NK)
    patched: dict[str, bytes] = {}
    aux_notes: list[str] = []
    for n, r in purged:
        if not should_patch_aux(n):
            continue
        new_b, nfix = patch_text_file(r, n)
        if nfix:
            patched[base.knorm(n)] = new_b
            aux_notes.append(f"{Path(n.replace(chr(92), '/')).name}:{nfix}")
            print(f"  patched {n} fixes={nfix}")

    rebuilt: list[tuple[str, bytes]] = []
    for n, r in purged:
        kn = base.knorm(n)
        rebuilt.append((n, patched[kn]) if kn in patched else (n, r))
    # INSERT exactly one clean Russia WO at canonical path
    rebuilt.append((NEW_PATH, new_raw))

    # Duplicate path guard
    counts: dict[str, int] = defaultdict(int)
    for n, _ in rebuilt:
        counts[base.knorm(n)] += 1
        if Path(n.replace("\\", "/")).name.lower() == "russia_weaponobjects.ini":
            counts["__basename_russia_wo__"] += 1
    dups = [k for k, v in counts.items() if v > 1]
    if dups:
        raise SystemExit(f"duplicate paths after rebuild: {dups}")
    if counts["__basename_russia_wo__"] != 1:
        raise SystemExit(
            f"expected exactly 1 russia_weaponobjects.ini got {counts['__basename_russia_wo__']}"
        )

    failures = []
    failures.extend(validate_wo(cleaned, rebuilt, art_entries, "PREWRITE"))
    integ_fails, integ_warns = russia_full_integrity(rebuilt, art_entries)
    failures.extend(integ_fails)
    if failures:
        print("PRE-WRITE FAILED")
        for f in failures[:150]:
            print(" ", f)
        return 1
    print(f"PASS pre-write (soft-warns={len(integ_warns)} aux={aux_notes})")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, rebuilt)
    final_entries = base.parse_big(out_big)
    final_hits = [(n, r) for n, r in final_entries if is_russia_wo_path(n)]
    if len(final_hits) != 1:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"expected 1 WO entry got {len(final_hits)}: {[n for n,_ in final_hits]}")

    extract_root = OUT / "_EXTRACT_VERIFY"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    emb_name, emb = final_hits[0]
    post: list[str] = []
    if emb != new_raw:
        post.append("byte mismatch WO")
    if base.sha256_bytes(emb) in old_shas:
        post.append("OLD broken hash still present / reused")
    if b"9?317" in emb or CYR_M.encode("utf-8") in emb:
        post.append("corrupt 9M317 remains in embedded WO")
    # Ensure NO entry in final BIG still has old sha
    for n, r in final_entries:
        if base.sha256_bytes(r) in old_shas and is_russia_wo_path(n):
            post.append(f"old broken entry still in BIG: {n}")

    rel = Path(*Path(emb_name.replace("\\", "/")).parts)
    ep = extract_root / rel
    ep.parent.mkdir(parents=True, exist_ok=True)
    ep.write_bytes(emb)
    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(new_raw)

    post.extend(validate_wo(emb.decode("ascii"), final_entries, art_entries, "EXTRACT"))
    post_fails, post_warns = russia_full_integrity(final_entries, art_entries)
    post.extend(post_fails)
    if post:
        out_big.unlink(missing_ok=True)
        print("EXTRACT/INTEGRITY FAILED")
        for f in post[:150]:
            print(" ", f)
        return 1
    print(f"PASS extract + integrity (soft-warns={len(post_warns)})")

    old_by = {base.knorm(n): r for n, r in entries}
    new_by = {base.knorm(n): r for n, r in final_entries}
    allowed = {base.knorm(NEW_PATH)} | set(patched)
    # Also allow path rename if old WO path knorm equals NEW
    for n, _ in old_hits:
        allowed.add(base.knorm(n))
    changed = [
        kn for kn in sorted(set(old_by) | set(new_by)) if old_by.get(kn) != new_by.get(kn)
    ]
    unexpected = [c for c in changed if c not in allowed]
    if unexpected:
        raise SystemExit(f"unrelated paths changed: {unexpected[:20]}")
    print(f"CHANGED={len(changed)}")

    big_sha = base.sha256_file(out_big)
    big_size = out_big.stat().st_size
    unit_sha = base.sha256_bytes(new_raw)
    (OUT / "Russia_WeaponObjects.ini").write_bytes(new_raw)
    (OUT / "RUSSIA_INTEGRITY_WARNINGS.txt").write_text(
        "RUSSIA INTEGRITY SOFT WARNINGS\n"
        f"count={len(post_warns)}\n\n" + "\n".join(post_warns[:500]) + "\n",
        encoding="ascii",
        errors="replace",
    )
    (OUT / "HARD_FIX_NOTES.txt").write_text(
        "RUSSIA WEAPONOBJECTS HARD FIX\n"
        "============================\n"
        f"deleted_variants={len(old_hits)}\n"
        f"deleted_shas={sorted(old_shas)}\n"
        f"new_sha={unit_sha}\n"
        f"stats={stats}\n"
        f"aux_patches={aux_notes}\n"
        "normalized=9M317 ASCII (Cyrillic Em / '?' removed)\n"
        "weapons=4x_MRSAM_9M317 6x_MRSAM_9M317M3\n"
        "locomotors=9M317MissileLocomotor 9M317M3MissileLocomotor\n",
        encoding="ascii",
    )
    verify = (
        "SPECTER RUSSIA WEAPONOBJECTS HARD FIX - VERIFY REPORT\n"
        "====================================================\n"
        "VERDICT: PASS\n"
        "Crash: EXCEPTION_ACCESS_VIOLATION @ NULL\n"
        "Cause: Cyrillic/corrupt 9M317 weapon+locomotor names (missing templates)\n"
        "Fix: DELETE ALL russia_weaponobjects.ini; INSERT one clean file;\n"
        "     normalize 9M317 across Weapon/Locomotor/9K317/WO\n"
        f"Objects preserved: {stats['objects']}\n"
        f"Russia WO entries in BIG: 1\n"
        "Old broken hash reused: NO\n"
        "Russia unit weapon templates: PASS\n"
        "Extract byte-match: PASS\n"
        f"BIG SHA256: {big_sha}\n"
        f"WO SHA256: {unit_sha}\n"
        f"BIG SIZE: {big_size}\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(verify, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "HARD DELETE+INSERT PROOF\n"
        f"removed_paths={[n for n,_ in old_hits]}\n"
        f"removed_shas={sorted(old_shas)}\n"
        f"new_path={NEW_PATH}\n"
        f"new_sha256={unit_sha}\n"
        "old_hash_reuse=NO\n"
        f"final_wo_count=1\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER RUSSIA WEAPONOBJECTS HARD FIX\n"
        "====================================\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n"
        "This build fully removes prior broken russia_weaponobjects.ini entries.\n",
        encoding="ascii",
    )

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "RUSSIA_INTEGRITY_WARNINGS.txt",
            "HARD_FIX_NOTES.txt",
            "Russia_WeaponObjects.ini",
        ):
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_RUSSIA_WEAPONOBJECTS_HARD_FIXED.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "RUSSIA_INTEGRITY_WARNINGS.txt",
            "HARD_FIX_NOTES.txt",
            "Russia_WeaponObjects.ini",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Russia_WeaponObjects.ini SHA256={unit_sha}\n"
        f"_SPEC_DATA_ONE_RUSSIA_WEAPONOBJECTS_HARD_FIXED.zip SHA256={zip_sha}\n",
        encoding="ascii",
    )
    if final_dir.is_dir():
        shutil.copy2(OUT / "HASHES.txt", final_dir / "HASHES.txt")
    print(f"BIG SHA256={big_sha}")
    print(f"ZIP SHA256={zip_sha}")
    print("FINAL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
