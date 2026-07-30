#!/usr/bin/env python3
"""FULL REBUILD of Turkey_WeaponObjects.ini (not a line patch).

Recreates every Object from validated USA/stock donors
(RaptorJetMissile / SpectreHowitzerShell / AuroraBomb), preserving
Turkey object names, Side=Turkey, valid ART models, valid locomotors,
and BuildVariations.

Strips ClientUpdate and unverified modules that caused
EXCEPTION_ACCESS_VIOLATION @ NULL at runtime.
"""
from __future__ import annotations

import re
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

import build_specter_aircraft_aab_global_fixed_big as base
import build_specter_turkey_weaponobjects_crash_fix_big as turkey

ROOT = Path(__file__).resolve().parents[2]
SRC = (
    ROOT
    / "Release"
    / "SPECTER_SPEC_DATA_ONE_RUSSIA_WEAPONOBJECTS_FULL_REBUILD"
    / "_SPEC_DATA_ONE.big"
)
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_WEAPONOBJECTS_FULL_REBUILD"
TREE = ROOT / "Data/INI/Object/Specter/Turkey Armed Forces/Turkey_WeaponObjects.ini"
NEW_PATH = r"Data\INI\Object\Specter\Turkey Armed Forces\Turkey_WeaponObjects.ini"

SAFE_MISSILE_MODEL = "AIM-120"
SAFE_SHELL_MODEL = "Irq_255mm_Round"
SAFE_BOMBLET_MODEL = "BOMBCELL"
SAFE_MISSILE_LOCO = "RaptorJetMissileLocomotor"
SAFE_BOMB_LOCO = "AuroraBombLocomotor"

STUB_NAMES = {
    "TurkeyCruiseMissileLauncher",
    "Turkey_255mmAl-FawCannon",
}
BOMB_NAMES = {
    "Turkey_Fab2000",
    "Turkey_Nasr5000",
    "Turkey_Nasr1500",
    "Turkey_Nasr2500",
    "Turkey_Turkey_Fab-250_Scripted",
    "Turkey_Alraad2_WarheadCells",
}


def is_turkey_wo_path(name: str) -> bool:
    ln = name.lower().replace("/", "\\")
    base_name = Path(name.replace("\\", "/")).name.lower()
    if base_name == "turkey_weaponobjects.ini":
        return True
    return turkey.is_turkey_wo(name)


def extract_object(text: str, name: str) -> str:
    return turkey.extract_object(text, name)


def extract_objects(text: str):
    return turkey.extract_objects(text)


def first_valid_model(block: str, stems: set[str], fallback: str) -> str:
    for m in re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", block):
        if m in ("None", "NONE", "NULL"):
            continue
        if m.lower() in stems:
            return m
    return fallback


def first_valid_loco(block: str, locos: set[str], fallback: str | None) -> str | None:
    for line in block.splitlines():
        m = re.match(r"^\s*Locomotor\s*=\s*(.*)$", line)
        if not m:
            continue
        for tok in m.group(1).split(";")[0].split():
            if tok.startswith("SET_") or tok in ("None", "NONE"):
                continue
            if tok in locos:
                return tok
    return fallback


def fix_bv_list(raw: str, known_objects: set[str], local_names: set[str]) -> list[str]:
    vals = raw.split(";")[0].split()
    out: list[str] = []
    for v in vals:
        if v in known_objects or v in local_names:
            out.append(v)
    seen = set()
    uniq = []
    for v in out:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


def classify(name: str, block: str) -> str:
    if name in STUB_NAMES:
        return "stub"
    if name in BOMB_NAMES:
        return "bomb"
    if re.search(r"(?m)^\s*BuildVariations\s*=", block) and "MissileAIUpdate" not in block:
        if "DumbProjectileBehavior" not in block and "MissileAIUpdate" not in block:
            return "bv_parent"
    if "MissileAIUpdate" in block:
        return "missile"
    if "DumbProjectileBehavior" in block or "APFSDS" in name or "Shell" in name:
        return "shell"
    if "Rocket" in name or "Grad" in name or "WarheadCells" in name:
        return "shell"
    if "PROJECTILE" in block:
        return "missile"
    return "missile"


def make_bv_parent(name: str, model: str, variations: list[str]) -> str:
    bv = " ".join(variations) if variations else name
    return (
        f"Object {name}\n"
        f"\n"
        f"  ; SPECTER FULL REBUILD - BV parent from stable stub\n"
        f"  Draw = W3DModelDraw ModuleTag_01\n"
        f"    OkToChangeModelColor = Yes\n"
        f"    ConditionState = NONE\n"
        f"      Model = {model}\n"
        f"    End\n"
        f"  End\n"
        f"\n"
        f"  Side = Turkey\n"
        f"  EditorSorting = SYSTEM\n"
        f"  BuildVariations = {bv}\n"
        f"  KindOf = PROJECTILE\n"
        f"\n"
        f"End\n"
        f";------------------------------------------------------------------------------\n"
    )


def make_stub(name: str, model: str) -> str:
    return (
        f"Object {name}\n"
        f"\n"
        f"  ; SPECTER FULL REBUILD - minimal validated stub (USA-style)\n"
        f"  Draw = W3DModelDraw ModuleTag_01\n"
        f"    OkToChangeModelColor = Yes\n"
        f"    DefaultConditionState\n"
        f"      Model = {model}\n"
        f"    End\n"
        f"  End\n"
        f"\n"
        f"  Side = Turkey\n"
        f"  EditorSorting = SYSTEM\n"
        f"  KindOf = PROJECTILE\n"
        f"  Body = InactiveBody ModuleTag_02\n"
        f"  End\n"
        f"\n"
        f"  Behavior = DestroyDie ModuleTag_03\n"
        f"  End\n"
        f"\n"
        f"  Geometry = Sphere\n"
        f"  GeometryIsSmall = Yes\n"
        f"  GeometryMajorRadius = 1.0\n"
        f"\n"
        f"End\n"
        f";------------------------------------------------------------------------------\n"
    )


def clone_rename(donor: str, new_name: str, model: str, locomotor: str | None) -> str:
    text = donor.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?m)^Object\s+\S+\s*$", f"Object {new_name}", text, count=1)
    if re.search(r"(?m)^\s*Side\s*=", text):
        text = re.sub(r"(?m)^(\s*Side\s*=\s*)\S+", r"\1Turkey", text, count=1)
    else:
        text = re.sub(
            r"(?m)^(  EditorSorting\s*=)",
            "  Side = Turkey\n\\1",
            text,
            count=1,
        )
    text = re.sub(r"(?m)^(\s*Model\s*=\s*)\S+", rf"\g<1>{model}", text)
    if locomotor:
        if re.search(r"(?m)^\s*Locomotor\s*=", text):
            text = re.sub(
                r"(?m)^(\s*Locomotor\s*=\s*SET_NORMAL\s+)\S+",
                rf"\g<1>{locomotor}",
                text,
                count=1,
            )
            text = re.sub(
                r"(?m)^(\s*Locomotor\s*=\s*)(?!SET_NORMAL).*$",
                rf"\1SET_NORMAL {locomotor}",
                text,
                count=1,
            )
        else:
            text = text.replace(
                "\nEnd\n",
                f"\n  Locomotor = SET_NORMAL {locomotor}\n\nEnd\n",
                1,
            )
    else:
        text = re.sub(r"(?m)^\s*Locomotor\s*=.*\n", "", text)

    text = text.replace("Model = AVSpectreShell1", f"Model = {SAFE_SHELL_MODEL}")
    text = text.replace("Model = EXCarptBmb", f"Model = {SAFE_BOMBLET_MODEL}")
    text = text.replace("Model = AVTomahawk_M", f"Model = {SAFE_MISSILE_MODEL}")

    if not re.search(r"(?m)^\s*DisplayName\s*=", text):
        text = re.sub(
            r"(?m)^(  EditorSorting\s*=)",
            "  DisplayName = OBJECT:Missile\n\\1",
            text,
            count=1,
        )

    text = re.sub(
        r"(?m)^(Object\s+\S+\s*\n)",
        r"\1\n  ; SPECTER FULL REBUILD - cloned from validated USA/stock donor\n",
        text,
        count=1,
    )
    if not text.endswith("\n"):
        text += "\n"
    return text


def rebuild_file(
    old_text: str,
    stock_text: str,
    stems: set[str],
    locos: set[str],
    known_objects: set[str],
) -> tuple[str, dict]:
    donor_missile = extract_object(stock_text, "RaptorJetMissile")
    donor_shell = extract_object(stock_text, "SpectreHowitzerShell")
    donor_bomb = extract_object(stock_text, "AuroraBomb")
    donor_bomb = re.sub(
        r"(?m)^(\s*Model\s*=\s*)\S+",
        rf"\g<1>{SAFE_BOMBLET_MODEL}",
        donor_bomb,
    )
    donor_shell = re.sub(
        r"(?m)^(\s*Model\s*=\s*)\S+",
        rf"\g<1>{SAFE_SHELL_MODEL}",
        donor_shell,
    )

    objs = extract_objects(old_text)
    local_names = {n for n, _ in objs}
    stats = defaultdict(int)
    parts: list[str] = []
    header = (
        "; SPECTER FULL REBUILD - Turkey_WeaponObjects\n"
        "; EXCEPTION_ACCESS_VIOLATION @ NULL - complete file recreation\n"
        "; Every Object cloned from validated USA/stock donors (Raptor/Spectre/Aurora)\n"
        "; Preserved: Turkey object names, Side=Turkey, valid ART models, BV lists\n"
        "; Removed: stray client modules, null refs, missing templates, unverified modules\n\n"
    )

    for name, block in objs:
        kind = classify(name, block)
        stats[f"kind_{kind}"] += 1
        bv_m = re.search(r"(?m)^\s*BuildVariations\s*=\s*(.+)$", block)
        bv_list = (
            fix_bv_list(bv_m.group(1), known_objects, local_names) if bv_m else []
        )

        if kind == "bv_parent":
            model = first_valid_model(block, stems, SAFE_MISSILE_MODEL)
            if not bv_list and bv_m:
                raw_vals = bv_m.group(1).split(";")[0].split()
                bv_list = [v for v in raw_vals if v in local_names]
            parts.append(make_bv_parent(name, model, bv_list or [name]))
            stats["rebuilt_bv"] += 1
            continue

        if kind == "stub":
            model = first_valid_model(block, stems, SAFE_MISSILE_MODEL)
            parts.append(make_stub(name, model))
            stats["rebuilt_stub"] += 1
            continue

        if kind == "shell":
            model = first_valid_model(block, stems, SAFE_SHELL_MODEL)
            parts.append(clone_rename(donor_shell, name, model, locomotor=None))
            stats["rebuilt_shell"] += 1
            continue

        if kind == "bomb":
            model = first_valid_model(block, stems, SAFE_BOMBLET_MODEL)
            loco = first_valid_loco(block, locos, SAFE_BOMB_LOCO)
            parts.append(clone_rename(donor_bomb, name, model, loco))
            stats["rebuilt_bomb"] += 1
            continue

        model = first_valid_model(block, stems, SAFE_MISSILE_MODEL)
        loco = first_valid_loco(block, locos, SAFE_MISSILE_LOCO)
        parts.append(clone_rename(donor_missile, name, model, loco))
        stats["rebuilt_missile"] += 1

    body = "\n".join(parts)
    if re.search(r"(?m)^\s*ClientUpdate\s*=", body):
        raise SystemExit("ClientUpdate leaked into full rebuild")
    if "J2mmGrad" in body or "9?317" in body:
        raise SystemExit("corrupt token in rebuild")
    cleaned = header + body
    if not cleaned.endswith("\n"):
        cleaned += "\n"
    if any(ord(c) > 127 for c in cleaned):
        raise SystemExit("non-ASCII in rebuilt WO")
    stats["objects"] = len(re.findall(r"(?m)^Object\s+", cleaned))
    return cleaned, dict(stats)


def validate_full(text: str, entries, art_entries, label: str) -> list[str]:
    fails: list[str] = []
    cats = turkey.catalog(entries)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }
    if not text.startswith("; SPECTER FULL REBUILD - Turkey_WeaponObjects"):
        fails.append(f"{label}: missing full-rebuild header")
    objs = re.findall(r"(?m)^Object\s+(\S+)", text)
    if len(objs) != len(set(objs)):
        fails.append(f"{label}: duplicate Object names")
    fails.extend(turkey.parse_stack_fails(text, label))
    if re.search(r"(?m)^\s*ClientUpdate\s*=", text):
        fails.append(f"{label}: ClientUpdate remains")
    if "J2mmGrad" in text or "9?317" in text:
        fails.append(f"{label}: corrupt token remains")

    for model in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)):
        if model in ("None", "NONE", "NULL"):
            fails.append(f"{label}: Model=None remains")
            continue
        if model.lower() not in stems:
            fails.append(f"{label}: missing W3D Model={model}")

    for a in set(re.findall(r"(?m)^\s*Armor\s*=\s*(\S+)", text)):
        if a not in ("None", "NONE") and a not in cats["Armor"]:
            fails.append(f"{label}: missing Armor {a}")
    for fx in set(re.findall(r"(?m)^\s*FXList\s*=\s*(\S+)", text)):
        if fx not in ("None", "NONE") and fx not in cats["FXList"]:
            fails.append(f"{label}: missing FXList {fx}")
    for fx in set(re.findall(r"(?m)^\s*FX\s*=\s*(\S+)", text)):
        if fx not in ("None", "NONE") and fx not in cats["FXList"]:
            fails.append(f"{label}: missing FX {fx}")
    for ocl in set(re.findall(r"(?m)^\s*OCL\s*=\s*(\S+)", text)):
        if ocl not in ("None", "NONE") and ocl not in cats["OCL"]:
            fails.append(f"{label}: missing OCL {ocl}")

    for line in text.splitlines():
        m = re.match(r"^\s*Locomotor\s*=\s*(.*)$", line)
        if not m:
            continue
        for tok in m.group(1).split(";")[0].split():
            if tok.startswith("SET_") or tok in ("None", "NONE"):
                continue
            if tok not in cats["Locomotor"]:
                fails.append(f"{label}: missing Locomotor {tok}")

    for name, block in extract_objects(text):
        m = re.search(r"(?m)^\s*BuildVariations\s*=\s*(.+)$", block)
        if m:
            for v in m.group(1).split(";")[0].split():
                if v not in cats["Object"]:
                    fails.append(f"{label}: {name} missing BV {v}")
        if not re.search(r"(?m)^\s*Draw\s*=", block):
            fails.append(f"{label}: {name} missing Draw")
        if "PROJECTILE" not in block:
            fails.append(f"{label}: {name} missing KindOf PROJECTILE")
        if not re.search(r"(?m)^\s*Side\s*=\s*Turkey\s*$", block):
            fails.append(f"{label}: {name} Side not Turkey")
    return fails


def turkey_integrity(entries, art_entries) -> tuple[list[str], list[str]]:
    fails, warns = turkey.turkey_integrity_scan(entries, art_entries)
    hits = [n for n, _ in entries if is_turkey_wo_path(n)]
    if len(hits) != 1:
        fails.append(f"turkey_weaponobjects.ini count={len(hits)} paths={hits}")
    for n, r in entries:
        if is_turkey_wo_path(n):
            t = r.decode("ascii", "replace")
            if not t.startswith("; SPECTER FULL REBUILD - Turkey_WeaponObjects"):
                fails.append("WO missing FULL REBUILD header")
            if re.search(r"(?m)^\s*ClientUpdate\s*=", t):
                fails.append("WO still has ClientUpdate")
    return fails, warns


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing SRC {SRC}")
    entries = base.parse_big(SRC)
    art_entries = base.parse_big(ART)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }
    cats = turkey.catalog(entries)
    locos = cats["Locomotor"]
    known_objects = cats["Object"]

    old_hits = [(n, r) for n, r in entries if is_turkey_wo_path(n)]
    print(f"DELETE phase: {len(old_hits)} turkey_weaponobjects.ini")
    if not old_hits:
        raise SystemExit("no turkey weaponobjects entries found")
    old_shas = {base.sha256_bytes(r) for _, r in old_hits}
    old_raw = old_hits[0][1]
    old_text = old_raw.decode("utf-8", "replace")
    old_names = set(re.findall(r"(?m)^Object\s+(\S+)", old_text))
    for n, r in old_hits:
        print(f"  removing {n!r} sha={base.sha256_bytes(r)[:16]} size={len(r)}")

    stock_raw = None
    for n, r in entries:
        if n.replace("/", "\\").endswith(r"Data\INI\Object\WeaponObjects.ini"):
            stock_raw = r
            break
    if stock_raw is None:
        raise SystemExit("stock WeaponObjects.ini missing")

    purged = [(n, r) for n, r in entries if not is_turkey_wo_path(n)]
    purged = [
        (n, r)
        for n, r in purged
        if Path(n.replace("\\", "/")).name.lower() != "turkey_weaponobjects.ini"
    ]

    cleaned, stats = rebuild_file(
        old_text,
        stock_raw.decode("utf-8", "replace"),
        stems,
        locos,
        known_objects | old_names,
    )
    new_raw = cleaned.encode("ascii")
    if base.sha256_bytes(new_raw) in old_shas:
        raise SystemExit("hash collision with deleted WO")
    new_names = set(re.findall(r"(?m)^Object\s+(\S+)", cleaned))
    if new_names != old_names:
        raise SystemExit(
            "object set changed "
            f"missing={sorted(old_names - new_names)[:20]} "
            f"extra={sorted(new_names - old_names)[:20]}"
        )
    print(
        f"NEW WO sha={base.sha256_bytes(new_raw)[:16]} size={len(new_raw)} "
        f"stats={stats}"
    )

    rebuilt = list(purged) + [(NEW_PATH, new_raw)]
    counts: dict[str, int] = defaultdict(int)
    for n, _ in rebuilt:
        counts[base.knorm(n)] += 1
        if Path(n.replace("\\", "/")).name.lower() == "turkey_weaponobjects.ini":
            counts["__basename_turkey_wo__"] += 1
    dups = [k for k, v in counts.items() if v > 1]
    if dups:
        raise SystemExit(f"duplicate paths {dups}")
    if counts["__basename_turkey_wo__"] != 1:
        raise SystemExit("basename turkey_weaponobjects count != 1")

    failures = []
    failures.extend(validate_full(cleaned, rebuilt, art_entries, "PREWRITE"))
    integ_fails, integ_warns = turkey_integrity(rebuilt, art_entries)
    failures.extend(integ_fails)
    failures.extend(turkey.turkey_weapon_chain_scan(rebuilt, art_entries))
    if failures:
        print("PRE-WRITE FAILED")
        for f in failures[:160]:
            print(" ", f)
        return 1
    print(f"PASS pre-write (soft-warns={len(integ_warns)})")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, rebuilt)
    final_entries = base.parse_big(out_big)
    final_hits = [(n, r) for n, r in final_entries if is_turkey_wo_path(n)]
    if len(final_hits) != 1:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"final WO count {len(final_hits)}")

    extract_root = OUT / "_EXTRACT_VERIFY"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    emb_name, emb = final_hits[0]
    post: list[str] = []
    if emb != new_raw:
        post.append("byte mismatch WO")
    if base.sha256_bytes(emb) in old_shas:
        post.append("old hash reused")
    if re.search(br"(?m)^\s*ClientUpdate\s*=", emb):
        post.append("ClientUpdate assignment remains")
    for n, r in final_entries:
        if is_turkey_wo_path(n) and base.sha256_bytes(r) in old_shas:
            post.append(f"old entry still present: {n}")

    rel = Path(*Path(emb_name.replace("\\", "/")).parts)
    ep = extract_root / rel
    ep.parent.mkdir(parents=True, exist_ok=True)
    ep.write_bytes(emb)
    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(new_raw)

    post.extend(validate_full(emb.decode("ascii"), final_entries, art_entries, "EXTRACT"))
    post_fails, post_warns = turkey_integrity(final_entries, art_entries)
    post.extend(post_fails)
    post.extend(turkey.turkey_weapon_chain_scan(final_entries, art_entries))
    if post:
        out_big.unlink(missing_ok=True)
        print("EXTRACT/INTEGRITY FAILED")
        for f in post[:160]:
            print(" ", f)
        return 1
    print(f"PASS extract + integrity (soft-warns={len(post_warns)})")

    old_by = {base.knorm(n): r for n, r in entries}
    new_by = {base.knorm(n): r for n, r in final_entries}
    allowed = {base.knorm(NEW_PATH)} | {base.knorm(n) for n, _ in old_hits}
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
    (OUT / "Turkey_WeaponObjects.ini").write_bytes(new_raw)
    (OUT / "TURKEY_INTEGRITY_WARNINGS.txt").write_text(
        "TURKEY INTEGRITY SOFT WARNINGS\n"
        f"count={len(post_warns)}\n\n" + "\n".join(post_warns[:500]) + "\n",
        encoding="ascii",
        errors="replace",
    )
    (OUT / "FULL_REBUILD_NOTES.txt").write_text(
        "TURKEY WEAPONOBJECTS FULL REBUILD\n"
        "================================\n"
        f"deleted_shas={sorted(old_shas)}\n"
        f"new_sha={unit_sha}\n"
        f"stats={stats}\n"
        f"donors=RaptorJetMissile,SpectreHowitzerShell,AuroraBomb\n"
        "clientupdate=REMOVED\n"
        "side=Turkey\n",
        encoding="ascii",
    )
    verify = (
        "SPECTER TURKEY WEAPONOBJECTS FULL REBUILD - VERIFY REPORT\n"
        "========================================================\n"
        "VERDICT: PASS\n"
        "Crash: EXCEPTION_ACCESS_VIOLATION @ 00000000\n"
        "Fix: FULL recreate of Turkey_WeaponObjects from USA/stock donors\n"
        f"Objects preserved: {stats['objects']}\n"
        "ClientUpdate: NONE\n"
        "Turkey WO entries in BIG: 1\n"
        "Old broken hash reused: NO\n"
        "Weapon/Projectile/FX/Locomotor/Armor validation: PASS\n"
        "Turkey unit weapon->projectile W3D scan: PASS\n"
        "Extract byte-match: PASS\n"
        f"BIG SHA256: {big_sha}\n"
        f"WO SHA256: {unit_sha}\n"
        f"BIG SIZE: {big_size}\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(verify, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "FULL REBUILD DELETE+INSERT PROOF\n"
        f"removed_shas={sorted(old_shas)}\n"
        f"new_sha256={unit_sha}\n"
        "old_hash_reuse=NO\n"
        f"final_wo_count=1\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER TURKEY WEAPONOBJECTS FULL REBUILD\n"
        "========================================\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n"
        "This build fully recreates turkey_weaponobjects.ini from validated donors.\n",
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
            "FULL_REBUILD_NOTES.txt",
            "Turkey_WeaponObjects.ini",
        ):
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_TURKEY_WEAPONOBJECTS_FULL_REBUILD.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "TURKEY_INTEGRITY_WARNINGS.txt",
            "FULL_REBUILD_NOTES.txt",
            "Turkey_WeaponObjects.ini",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Turkey_WeaponObjects.ini SHA256={unit_sha}\n"
        f"_SPEC_DATA_ONE_TURKEY_WEAPONOBJECTS_FULL_REBUILD.zip SHA256={zip_sha}\n",
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
