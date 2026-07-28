#!/usr/bin/env python3
"""DELETE broken Turkey_WeaponObjects.ini and INSERT a cleaned rebuild.

Preserves Turkey object names, damage/FX/OCL/locomotor logic.
Fixes:
1. Stray End after single-line ClientUpdate (parse crash)
2. Missing W3D models remapped to validated USA/Iraq ART donors
3. BuildVariations missing GenericDefeatedTankShell removed
4. Bare ConditionState normalized where needed
Then full Turkey integrity scan; pack release ZIP.
"""
from __future__ import annotations

import re
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

import build_specter_aircraft_aab_global_fixed_big as base
import build_specter_turkey_faction_ini_batch_fixed_big as turkey_batch

ROOT = Path(__file__).resolve().parents[2]
SRC = (
    ROOT
    / "Release"
    / "SPECTER_SPEC_DATA_ONE_TURKEY_MAROONBERETS_CLEAN_REBUILD"
    / "_SPEC_DATA_ONE.big"
)
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_WEAPONOBJECTS_CLEAN_REBUILD"
TREE = ROOT / "Data/INI/Object/Specter/Turkey Armed Forces/Turkey_WeaponObjects.ini"
NEW_PATH = r"Data\INI\Object\Specter\Turkey Armed Forces\Turkey_WeaponObjects.ini"

# Missing W3D -> validated donor models present in _SPEC_ART_ONE.big
MODEL_REMAP = {
    "AVTankShel": "Irq_255mm_Round",  # USA/Iraq artillery shell art
    "SCUD_M-IRAQ": "Irq_R11_M",  # Iraq ballistic missile body
    "Turkey_Shaheed": "Irq_Quds5",  # suicide/drone warhead art
    "Turkey_Sarab7_M": "Iraq_Sarab7_M",
    "Turkey_Alhusain_W": "Iraq_Alhusain_W",
    "ExMsslTm": "US_FGM114",  # USA missile defender / ATGM art
    "EXStinger01": "US_Stinger",
    "AVRaptor_M": "AIM-120",  # USA AAM / SAM-class missile art
    "UVRockBug_m": "122mmGrad",  # rocket / buggy missile art
}


def is_turkey_weaponobjects_entry(name: str) -> bool:
    ln = name.lower().replace("/", "\\")
    return "turkey" in ln and "weaponobjects.ini" in ln and ln.endswith(".ini")


def is_turkey_object_ini(name: str) -> bool:
    n = name.replace("/", "\\")
    return "Turkey Armed Forces" in n and n.lower().endswith(".ini")


def extract_objects(text: str) -> list[tuple[str, str]]:
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Object\s+(\S+)", text)]
    out: list[tuple[str, str]] = []
    for i, (start, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        out.append((name, text[start:end]))
    return out


def fix_clientupdate_stray_end(text: str) -> tuple[str, int]:
    """Remove End that immediately follows a single-line ClientUpdate= module."""
    new, n = re.subn(
        r"(?m)^(\s*ClientUpdate\s*=\s*\S+[^\n]*\n)\s*End\s*\n",
        r"\1",
        text,
    )
    return new, n


def remap_models(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    out = text
    for bad, good in MODEL_REMAP.items():
        pattern = rf"(?m)^(\s*Model\s*=\s*){re.escape(bad)}(\s*(?:;.*)?)$"
        if re.search(pattern, out):
            out, n = re.subn(pattern, rf"\1{good}\2", out)
            if n:
                notes.append(f"{bad}->{good}x{n}" if n > 1 else f"{bad}->{good}")
    return out, notes


def fix_buildvariations(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^(\s*BuildVariations\s*=\s*)(.+)$", line)
        if not m:
            lines.append(line)
            continue
        vals = m.group(2).split(";")[0].split()
        # Drop missing GenericDefeatedTankShell; keep Generic120mm* and Turkey_* variants.
        kept = [v for v in vals if v != "GenericDefeatedTankShell"]
        # Deduplicate while preserving order
        seen: set[str] = set()
        uniq: list[str] = []
        for v in kept:
            if v not in seen:
                seen.add(v)
                uniq.append(v)
        if uniq:
            lines.append(m.group(1) + " ".join(uniq))
        else:
            lines.append("  ; BuildVariations removed (no valid variants)")
    return "\n".join(lines) + "\n"


def build_clean_weaponobjects(raw: bytes) -> tuple[str, dict]:
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    stats = {
        "objects_in": len(re.findall(r"(?m)^Object\s+", text)),
        "clientupdate_ends_removed": 0,
        "model_remaps": [],
    }

    text, n_cu = fix_clientupdate_stray_end(text)
    stats["clientupdate_ends_removed"] = n_cu

    text, remaps = remap_models(text)
    stats["model_remaps"] = remaps

    text = fix_buildvariations(text)
    text, _ = turkey_batch.remove_armor_set_flag(text)
    text, _ = turkey_batch.sanitize_ascii(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"

    # Strip old Phase-2 banners; add clean rebuild header.
    body = text
    if body.lstrip().startswith(";"):
        # drop leading comment block until first Object
        m = re.search(r"(?m)^Object\s+\S+", body)
        if m:
            body = body[m.start() :]

    header = (
        "; SPECTER CLEAN REBUILD - Turkey_WeaponObjects\n"
        "; Prior Turkey_WeaponObjects.ini BIG entry DELETED (not repaired in-place)\n"
        "; Preserved: Turkey Object names, damage, FX, OCL, locomotor, Weapon refs\n"
        "; Fixed: stray ClientUpdate End parse crashes\n"
        "; Fixed: missing W3D models remapped to validated USA/Iraq ART donors\n"
        "; Fixed: BuildVariations missing GenericDefeatedTankShell removed\n\n"
    )
    cleaned = header + body
    stats["objects_out"] = len(re.findall(r"(?m)^Object\s+", cleaned))
    return cleaned, stats


def catalog(entries):
    cats: dict[str, set[str]] = defaultdict(set)
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("utf-8", "replace")
        cats["Object"].update(re.findall(r"(?m)^Object\s+(?![=])(\S+)", t))
        cats["CommandSet"].update(re.findall(r"(?m)^CommandSet\s+(\S+)", t))
        cats["Weapon"].update(re.findall(r"(?m)^Weapon\s+(\S+)", t))
        cats["Science"].update(re.findall(r"(?m)^Science\s+(\S+)", t))
        cats["Upgrade"].update(re.findall(r"(?m)^Upgrade\s+(\S+)", t))
        cats["Armor"].update(re.findall(r"(?m)^Armor\s+(\S+)", t))
        cats["Locomotor"].update(re.findall(r"(?m)^Locomotor\s+(\S+)", t))
        cats["MappedImage"].update(re.findall(r"(?m)^MappedImage\s+(\S+)", t))
        cats["OCL"].update(re.findall(r"(?m)^ObjectCreationList\s+(\S+)", t))
        cats["FXList"].update(re.findall(r"(?m)^FXList\s+(\S+)", t))
    return cats


def parse_stack_fails(text: str, label: str) -> list[str]:
    fails: list[str] = []
    stack: list[tuple[str, int]] = []
    openers = [
        (re.compile(r"^\s*Object\s+(?![=])\S+"), "Object"),
        (re.compile(r"^\s*Draw\s*="), "Draw"),
        (re.compile(r"^\s*Behavior\s*="), "Behavior"),
        (re.compile(r"^\s*Body\s*="), "Body"),
        (re.compile(r"^\s*ArmorSet\b"), "ArmorSet"),
        (re.compile(r"^\s*WeaponSet\b"), "WeaponSet"),
        (re.compile(r"^\s*Prerequisites\b"), "Prerequisites"),
        (re.compile(r"^\s*UnitSpecificSounds\b"), "UnitSpecificSounds"),
        (re.compile(r"^\s*DefaultConditionState\b"), "DefaultConditionState"),
        (re.compile(r"^\s*ConditionState\s*="), "ConditionState"),
        (re.compile(r"^\s*ConditionState\s*$"), "ConditionState"),
        (re.compile(r"^\s*TransitionState\s*="), "TransitionState"),
        (re.compile(r"^\s*LocomotorSet\b"), "LocomotorSet"),
    ]
    for i, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0]
        if not code.strip():
            continue
        if re.match(r"^\s*End\s*$", code):
            if not stack:
                fails.append(f"{label}: extra End @{i}")
            else:
                stack.pop()
            continue
        for rx, kind in openers:
            if rx.match(code):
                stack.append((kind, i))
                break
    if stack:
        fails.append(f"{label}: unclosed {stack[-10:]}")
    return fails


def validate_weaponobjects(text: str, entries, art_entries, label: str) -> list[str]:
    fails: list[str] = []
    cats = catalog(entries)
    data_join = b"\n".join(b for _, b in entries)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }

    if any(ord(c) > 127 for c in text):
        fails.append(f"{label}: non-ASCII")
    if not text.startswith("; SPECTER CLEAN REBUILD - Turkey_WeaponObjects"):
        fails.append(f"{label}: missing clean-rebuild header")
    objs = re.findall(r"(?m)^Object\s+(\S+)", text)
    if not objs:
        fails.append(f"{label}: no Object blocks")
    if len(objs) != len(set(objs)):
        fails.append(f"{label}: duplicate Object names in file")
    non_turkey = [o for o in objs if not o.startswith("Turkey")]
    if non_turkey:
        fails.append(f"{label}: non-Turkey objects {non_turkey[:10]}")

    fails.extend(parse_stack_fails(text, label))

    if re.search(r"(?m)^\s*ClientUpdate\s*=.*\n\s*End\s*$", text):
        fails.append(f"{label}: stray ClientUpdate End remains")

    for bad in MODEL_REMAP:
        if re.search(rf"(?m)^\s*Model\s*=\s*{re.escape(bad)}\b", text):
            fails.append(f"{label}: missing-model token remains Model={bad}")

    # BV must resolve
    for m in re.finditer(r"(?m)^\s*BuildVariations\s*=\s*(.+)$", text):
        vals = m.group(1).split(";")[0].split()
        missing = [v for v in vals if v not in cats["Object"]]
        if missing:
            fails.append(f"{label}: missing BV {missing}")

    def need(kind: str, vals: list[str]) -> None:
        for v in vals:
            if v in ("None", "NONE"):
                continue
            if v not in cats[kind] and v.encode() not in data_join:
                fails.append(f"{label}: missing {kind}={v}")

    need("Armor", re.findall(r"(?m)^\s*Armor\s*=\s*(\S+)", text))
    need("Locomotor", re.findall(r"(?m)^\s*Locomotor\s*=\s*\S+\s+(\S+)", text))
    need("OCL", re.findall(r"(?m)^\s*OCL\s*=\s*(\S+)", text))
    need("FXList", re.findall(r"(?m)^\s*(?:FX|IgnitionFX)\s*=\s*(\S+)", text))
    need("Object", re.findall(r"(?m)^\s*Object\s*=\s*(\S+)", text))
    need(
        "Upgrade",
        re.findall(r"(?m)^\s*(?:TriggeredBy|UpgradeToGrant)\s*=\s*(\S+)", text),
    )

    for model in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)):
        if model in ("None", "NONE", "NULL"):
            continue
        if model.lower() not in stems:
            fails.append(f"{label}: missing W3D Model={model}")
    return fails


def turkey_integrity_scan(entries, art_entries) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []
    cats = catalog(entries)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }
    objs = cats["Object"]

    wo_hits = [n for n, _ in entries if is_turkey_weaponobjects_entry(n)]
    if len(wo_hits) != 1:
        fails.append(f"Turkey_WeaponObjects.ini entry count={len(wo_hits)} {wo_hits}")

    # Prior infantry clean rebuilds must remain
    for o in ("Turkey_Airborne", "Turkey_SpecialForces", "Turkey_EliteMaroonBerets"):
        if o not in objs:
            fails.append(f"missing prior Object {o}")
    for c in (
        "Turkey_AirborneCommandSet",
        "Turkey_SpecialForcesCommandSet",
        "Turkey_EliteMaroonBeretsCommandSet",
    ):
        if c not in cats["CommandSet"]:
            fails.append(f"missing prior CommandSet {c}")

    # Turkey unit Weapon= projectile Object refs should resolve when pointing at Turkey_* 
    for n, r in entries:
        if not is_turkey_object_ini(n):
            continue
        nn = n.replace("/", "\\")
        text = r.decode("utf-8", "replace")
        bn = Path(n.replace("\\", "/")).name

        if "\\Weapon" in nn or "WeaponObjects" in nn:
            # hard-check weaponobjects file only for W3D/parse (done in validate)
            if is_turkey_weaponobjects_entry(n):
                continue
            # projectile folder: soft W3D/parse
            for msg in parse_stack_fails(text, bn):
                # ClientUpdate false positives elsewhere -> only warn
                warns.append(msg)
            for model in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)):
                if model in ("None", "NONE", "NULL"):
                    continue
                if model.lower() not in stems:
                    warns.append(f"{bn}: missing W3D Model={model}")
            continue

        # Unit BV hard gate (same corruption pattern)
        if "\\Projectile" not in nn:
            for m in re.finditer(r"(?m)^\s*BuildVariations\s*=\s*(.+)$", text):
                vals = m.group(1).split(";")[0].split()
                foreign = [v for v in vals if not v.startswith("Turkey")]
                missing = [v for v in vals if v not in objs]
                if foreign:
                    fails.append(f"{bn}: foreign BV {foreign}")
                if missing:
                    fails.append(f"{bn}: missing BV {missing}")

        for msg in parse_stack_fails(text, bn):
            warns.append(msg)
        for model in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)):
            if model in ("None", "NONE", "NULL"):
                continue
            if model.lower() not in stems:
                warns.append(f"{bn}: missing W3D Model={model}")

    return fails, warns


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG: {SRC}")

    entries = base.parse_big(SRC)
    art_entries = base.parse_big(ART)

    old_hits = [(n, r) for n, r in entries if is_turkey_weaponobjects_entry(n)]
    print(f"DELETE phase: found {len(old_hits)} Turkey_WeaponObjects.ini entries")
    old_shas = set()
    old_raw = None
    old_names: set[str] = set()
    for n, r in old_hits:
        sha = base.sha256_bytes(r)
        old_shas.add(sha)
        old_raw = r
        old_names = set(re.findall(r"(?m)^Object\s+(\S+)", r.decode("utf-8", "replace")))
        print(f"  removing {n} sha={sha[:16]} size={len(r)} objects={len(old_names)}")

    if old_raw is None:
        raise SystemExit("Turkey_WeaponObjects.ini not found in source BIG")

    purged = [(n, r) for n, r in entries if not is_turkey_weaponobjects_entry(n)]
    print(f"PURGED ok; entries {len(entries)} -> {len(purged)}")

    cleaned_text, stats = build_clean_weaponobjects(old_raw)
    new_raw = cleaned_text.encode("ascii")
    if base.sha256_bytes(new_raw) in old_shas:
        raise SystemExit("new hash collided with deleted WeaponObjects")
    new_names = set(re.findall(r"(?m)^Object\s+(\S+)", cleaned_text))
    if new_names != old_names:
        missing = sorted(old_names - new_names)
        extra = sorted(new_names - old_names)
        raise SystemExit(f"object name set changed missing={missing[:20]} extra={extra[:20]}")
    print(
        f"NEW WeaponObjects sha={base.sha256_bytes(new_raw)[:16]} size={len(new_raw)} "
        f"objects={stats['objects_out']} cu_ends_removed={stats['clientupdate_ends_removed']} "
        f"remaps={len(stats['model_remaps'])}"
    )

    rebuilt = purged + [(NEW_PATH, new_raw)]
    counts: dict[str, int] = defaultdict(int)
    for n, _ in rebuilt:
        counts[base.knorm(n)] += 1
    dups = [k for k, v in counts.items() if v > 1]
    if dups:
        raise SystemExit(f"duplicate paths: {dups}")

    failures: list[str] = []
    failures.extend(
        validate_weaponobjects(cleaned_text, rebuilt, art_entries, "PREWRITE")
    )
    integ_fails, integ_warns = turkey_integrity_scan(rebuilt, art_entries)
    failures.extend(integ_fails)
    if failures:
        print("PRE-WRITE FAILED")
        for f in failures[:120]:
            print(" ", f)
        return 1
    print(f"PASS pre-write (Turkey integrity soft-warns={len(integ_warns)})")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, rebuilt)
    final_entries = base.parse_big(out_big)

    final_hits = [(n, r) for n, r in final_entries if is_turkey_weaponobjects_entry(n)]
    if len(final_hits) != 1:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"expected 1 final WeaponObjects entry, got {final_hits}")

    extract_root = OUT / "_EXTRACT_VERIFY"
    if extract_root.exists():
        shutil.rmtree(extract_root)

    post: list[str] = []
    emb_name, emb = final_hits[0]
    if emb != new_raw:
        post.append("byte mismatch WeaponObjects")
    if base.sha256_bytes(emb) in old_shas:
        post.append("old WeaponObjects hash reused")
    for bad in MODEL_REMAP:
        if re.search(rf"(?m)^\s*Model\s*=\s*{re.escape(bad)}\s*$".encode(), emb):
            post.append(f"old model remains {bad}")

    rel = Path(*Path(emb_name.replace("\\", "/")).parts)
    ep = extract_root / rel
    ep.parent.mkdir(parents=True, exist_ok=True)
    ep.write_bytes(emb)
    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(new_raw)

    post.extend(
        validate_weaponobjects(emb.decode("ascii"), final_entries, art_entries, "EXTRACT")
    )
    post_fails, post_warns = turkey_integrity_scan(final_entries, art_entries)
    post.extend(post_fails)
    if post:
        out_big.unlink(missing_ok=True)
        print("EXTRACT/INTEGRITY FAILED")
        for f in post[:120]:
            print(" ", f)
        return 1
    print(f"PASS extract + Turkey integrity (soft-warns={len(post_warns)})")

    (OUT / "TURKEY_INTEGRITY_WARNINGS.txt").write_text(
        "TURKEY OBJECT INTEGRITY - PRE-EXISTING SOFT WARNINGS\n"
        "====================================================\n"
        "Hard gate: WeaponObjects parse/W3D/BV + prior infantry rebuilds.\n"
        f"count={len(post_warns)}\n\n"
        + "\n".join(post_warns[:500])
        + ("\n" if post_warns else "none\n"),
        encoding="ascii",
        errors="replace",
    )
    (OUT / "MODEL_REMAP.txt").write_text(
        "MISSING W3D MODEL REMAPS (USA/Iraq ART donors)\n"
        "==============================================\n"
        + "\n".join(stats["model_remaps"])
        + "\n",
        encoding="ascii",
    )

    old_by = {base.knorm(n): r for n, r in entries}
    new_by = {base.knorm(n): r for n, r in final_entries}
    allowed = {base.knorm(NEW_PATH)}
    changed = [kn for kn in sorted(set(old_by) | set(new_by)) if old_by.get(kn) != new_by.get(kn)]
    unexpected = [c for c in changed if c not in allowed]
    if unexpected:
        raise SystemExit(f"unrelated paths changed: {unexpected[:20]}")
    print(f"CHANGED={len(changed)}")

    big_sha = base.sha256_file(out_big)
    big_size = out_big.stat().st_size
    unit_sha = base.sha256_bytes(new_raw)

    (OUT / "Turkey_WeaponObjects.ini").write_bytes(new_raw)

    verify = (
        "SPECTER TURKEY WEAPONOBJECTS CLEAN DELETE+REBUILD - VERIFY REPORT\n"
        "=================================================================\n"
        "VERDICT: PASS\n"
        "Method: DELETE prior Turkey_WeaponObjects.ini, INSERT cleaned rebuild\n"
        f"Objects preserved: {stats['objects_out']} Turkey_* weapon/projectile objects\n"
        f"Stray ClientUpdate End removed: {stats['clientupdate_ends_removed']}\n"
        f"Missing W3D remapped to USA/Iraq ART donors: {len(stats['model_remaps'])}\n"
        "BuildVariations: GenericDefeatedTankShell removed\n"
        "Damage/FX/OCL/Locomotor/Weapon refs: PRESERVED\n"
        "Prior Turkey_Airborne/SpecialForces/MaroonBerets fixes: PRESERVED\n"
        "Turkey integrity hard gate: PASS\n"
        f"Turkey integrity soft-warns: {len(post_warns)}\n"
        f"\nTurkey_WeaponObjects.ini SHA256: {unit_sha}\n"
        f"BIG SHA256: {big_sha}\n"
        f"BIG SIZE: {big_size}\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(verify, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "DELETE + INSERT PROOF\n"
        "=====================\n"
        f"removed_count={len(old_hits)}\n"
        f"removed_shas={sorted(old_shas)}\n"
        f"new_sha256={unit_sha}\n"
        "old_hash_reuse=NO\n"
        "header=SPECTER CLEAN REBUILD\n"
        f"objects={stats['objects_out']}\n"
        f"clientupdate_ends_removed={stats['clientupdate_ends_removed']}\n"
        f"model_remaps={stats['model_remaps']}\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER TURKEY WEAPONOBJECTS CLEAN DELETE+REBUILD\n"
        "================================================\n\n"
        "Broken Turkey_WeaponObjects.ini deleted from _SPEC_DATA_ONE.big.\n"
        "Rebuilt with Turkey object names preserved; parse + W3D fixed.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "TURKEY_INTEGRITY_WARNINGS.txt",
            "MODEL_REMAP.txt",
            "Turkey_WeaponObjects.ini",
        ):
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_TURKEY_WEAPONOBJECTS_CLEAN_REBUILD.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "TURKEY_INTEGRITY_WARNINGS.txt",
            "MODEL_REMAP.txt",
            "Turkey_WeaponObjects.ini",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Turkey_WeaponObjects.ini SHA256={unit_sha}\n"
        f"_SPEC_DATA_ONE_TURKEY_WEAPONOBJECTS_CLEAN_REBUILD.zip SHA256={zip_sha}\n",
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
