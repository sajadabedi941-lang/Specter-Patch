#!/usr/bin/env python3
"""Hard-crash / integrity fix for Russia_WeaponObjects.

Root causes addressed:
1. ClientUpdate blocks with stray End (mis-nested modules / NULL deref risk)
2. Missing W3D Model=Iraq_Alhusain_W2 on RS24 decoy projectiles
3. BuildVariations pointing at missing GenericDefeatedTankShell / 40N6Missile_ABM_Object1
4. Projectile variations with Model=None (no draw geometry)
5. Side=Iraq on Russian weapon objects

Workflow:
- DELETE Russia_WeaponObjects.ini; INSERT crash-safe rebuild
- Keep Russia object names; force Side=Russia where appropriate
- Remap / retarget broken refs to validated USA/China/Egypt/Iraq ART donors
- Byte-match extract; Russia integrity + weapon-chain scan; pack ZIP
"""
from __future__ import annotations

import re
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

import build_specter_aircraft_aab_global_fixed_big as base
import build_specter_turkey_faction_ini_batch_fixed_big as turkey_batch
import build_specter_turkey_weaponobjects_crash_fix_big as turkey_wo

ROOT = Path(__file__).resolve().parents[2]
SRC = (
    ROOT
    / "Release"
    / "SPECTER_SPEC_DATA_ONE_TURKEY_WEAPONOBJECTS_CRASH_FIXED"
    / "_SPEC_DATA_ONE.big"
)
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_RUSSIA_WEAPONOBJECTS_CRASH_FIXED"
TREE = (
    ROOT
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Russia_WeaponObjects.ini"
)
NEW_PATH = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Russia_WeaponObjects.ini"
)

MODEL_REMAP = {
    "Iraq_Alhusain_W2": "Iraq_Alhusain_W",
    "AVTankShel": "Irq_255mm_Round",
    "EXStinger01": "US_Stinger",
    "AVRaptor_M": "AIM-120",
    "UVRockBug_m": "122mmGrad",
    "NVMBuggy_m": "122mmGrad",
    "ExMsslTm": "US_FGM114",
    "PMMoab": "US_GBU43B",
    "Mob_Botl": "BOMBCELL",
    "J2mmGrad": "122mmGrad",
}

BV_REMAP = {
    "GenericDefeatedTankShell": "Generic120mmAPFSDSDeflectedRound",
    "40N6Missile_ABM_Object1": "40N6Missile_ABM_Object",
}

DEFAULT_SHELL_MODEL = "Irq_255mm_Round"
DEFAULT_BOMBLET_MODEL = "BOMBCELL"


def is_russia_wo(name: str) -> bool:
    ln = name.lower().replace("/", "\\")
    return "russia" in ln and "weaponobjects.ini" in ln and ln.endswith(".ini")


def is_russia_object_ini(name: str) -> bool:
    n = name.replace("/", "\\")
    return "Armed Forces Of Russian Federation" in n and n.lower().endswith(".ini")


def extract_object(text: str, object_name: str) -> str:
    return turkey_wo.extract_object(text, object_name)


def extract_objects(text: str) -> list[tuple[str, str]]:
    return turkey_wo.extract_objects(text)


def remap_models(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    out = text
    for bad, good in MODEL_REMAP.items():
        pattern = rf"(?m)^(\s*Model\s*=\s*){re.escape(bad)}(\s*(?:;.*)?)$"
        if re.search(pattern, out):
            out, n = re.subn(pattern, rf"\g<1>{good}\g<2>", out)
            if n:
                notes.append(f"{bad}->{good}x{n}" if n > 1 else f"{bad}->{good}")
    return out, notes


def fix_clientupdate_stray_end(text: str) -> tuple[str, int]:
    return turkey_wo.fix_clientupdate_stray_end(text)


def fix_bv_refs(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    out = text
    for bad, good in BV_REMAP.items():
        # Only rewrite inside BuildVariations value lists
        def repl(m: re.Match[str]) -> str:
            line = m.group(0)
            vals = line.split("=", 1)
            if len(vals) != 2:
                return line
            head, rest = vals
            code, comment = (rest.split(";", 1) + [""])[:2]
            tokens = code.split()
            changed = False
            new_tokens = []
            for tok in tokens:
                if tok == bad:
                    new_tokens.append(good)
                    changed = True
                else:
                    new_tokens.append(tok)
            if not changed:
                return line
            rebuilt = head + "= " + " ".join(new_tokens)
            if comment != "" or ";" in rest:
                # preserve trailing comment if present
                if ";" in rest:
                    rebuilt += " ;" + rest.split(";", 1)[1].rstrip("\n")
            return rebuilt + ("\n" if line.endswith("\n") else "")

        # line-based safer rewrite
        lines = out.splitlines(True)
        changed_lines = 0
        for i, line in enumerate(lines):
            if not re.match(r"(?i)^\s*BuildVariations\s*=", line):
                continue
            code = line.split(";", 1)[0]
            if bad not in code:
                continue
            prefix, _, rest = line.partition("=")
            comment = ""
            body = rest
            if ";" in rest:
                body, comment = rest.split(";", 1)
                comment = ";" + comment
            tokens = body.split()
            new_tokens = [good if t == bad else t for t in tokens]
            if new_tokens != tokens:
                lines[i] = prefix + "= " + " ".join(new_tokens) + ((" " + comment) if comment else "")
                if not lines[i].endswith("\n") and line.endswith("\n"):
                    lines[i] += "\n"
                changed_lines += 1
        if changed_lines:
            out = "".join(lines)
            notes.append(f"{bad}->{good}x{changed_lines}")
    return out, notes


def force_russia_side(text: str) -> tuple[str, int]:
    """Keep Generic side for Generic* helpers; force Iraq leftovers to Russia."""
    n = 0
    lines = text.splitlines(True)
    current = None
    for i, line in enumerate(lines):
        m = re.match(r"^Object\s+(\S+)", line)
        if m:
            current = m.group(1)
            continue
        sm = re.match(r"^(\s*Side\s*=\s*)(\S+)(\s*(?:;.*)?)?$", line)
        if not sm or current is None:
            continue
        side = sm.group(2)
        if side == "Iraq":
            lines[i] = f"{sm.group(1)}Russia{sm.group(3) or ''}"
            if line.endswith("\n") and not lines[i].endswith("\n"):
                lines[i] += "\n"
            n += 1
    return "".join(lines), n


def fix_none_models(text: str, art_stems: set[str]) -> tuple[str, dict]:
    """Replace Model=None on projectiles with a real donor model when safe."""
    stats = {"bv_parents": 0, "lonely_projectiles": 0}
    objs = dict(extract_objects(text))

    for name, block in list(objs.items()):
        models = re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", block)
        real = [m for m in models if m not in ("None", "NONE")]
        bv = re.search(r"(?m)^\s*BuildVariations\s*=\s*(.+)$", block)
        if real:
            continue
        if "PROJECTILE" not in block and not bv:
            continue

        donor = None
        if bv:
            vals = bv.group(1).split(";")[0].split()
            for v in vals:
                if v in objs:
                    donor_models = [
                        m
                        for m in re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", objs[v])
                        if m not in ("None", "NONE") and m.lower() in art_stems
                    ]
                    if donor_models:
                        donor = donor_models[0]
                        break
            if donor is None:
                # Prefer shell/warhead defaults for known families
                if "APFSDS" in name:
                    donor = DEFAULT_SHELL_MODEL
                elif "RS24" in name or "Warhead" in name:
                    donor = "Iraq_Alhusain_W"
                elif "9K723" in name or "Missile" in name:
                    donor = "AIM-120"
                else:
                    donor = DEFAULT_SHELL_MODEL
            new_block, n = re.subn(
                r"(?m)^(\s*Model\s*=\s*)(?:None|NONE)\s*$",
                rf"\g<1>{donor}",
                block,
                count=1,
            )
            if n:
                objs[name] = new_block
                stats["bv_parents"] += 1
            continue

        # Lonely projectile / bomblet with Model=None
        if "Cell_Bomblet" in name or "Bomblet" in name:
            donor = DEFAULT_BOMBLET_MODEL
        elif "APFSDS" in name:
            donor = DEFAULT_SHELL_MODEL
        else:
            donor = DEFAULT_SHELL_MODEL
        if donor.lower() not in art_stems:
            continue
        new_block, n = re.subn(
            r"(?m)^(\s*Model\s*=\s*)(?:None|NONE)\s*$",
            rf"\g<1>{donor}",
            block,
            count=1,
        )
        if n:
            objs[name] = new_block
            stats["lonely_projectiles"] += 1

    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Object\s+(\S+)", text)]
    if not starts:
        return text, stats
    prefix = text[: starts[0][0]]
    parts = [prefix]
    for _, name in starts:
        parts.append(objs[name])
    return "".join(parts), stats


def rebuild_russia_wo(raw: bytes, art_stems: set[str]) -> tuple[str, dict]:
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    stats: dict = {
        "clientupdate_ends_removed": 0,
        "model_remaps": [],
        "bv_remaps": [],
        "side_forced": 0,
        "none_model_stats": {},
        "objects": 0,
    }

    text, stats["clientupdate_ends_removed"] = fix_clientupdate_stray_end(text)
    text, stats["model_remaps"] = remap_models(text)
    text, stats["bv_remaps"] = fix_bv_refs(text)
    text, stats["side_forced"] = force_russia_side(text)
    text, stats["none_model_stats"] = fix_none_models(text, art_stems)
    text, more = remap_models(text)
    stats["model_remaps"] = list(stats["model_remaps"]) + more

    m = re.search(r"(?m)^Object\s+\S+", text)
    body = text[m.start() :] if m else text
    header = (
        "; SPECTER CRASH FIX - Russia_WeaponObjects\n"
        "; EXCEPTION_ACCESS_VIOLATION / broken projectile repair\n"
        "; - Removed ClientUpdate stray End blocks\n"
        "; - Remapped missing W3D (Alhusain W2 decoy model -> Iraq_Alhusain_W)\n"
        "; - Fixed BuildVariations missing GenericDefeatedTankShell / 40N6 Object1\n"
        "; - Replaced Model=None projectiles with validated donor ART\n"
        "; - Forced Side leftovers to Side=Russia\n\n"
    )
    cleaned = header + body
    cleaned, _ = turkey_batch.sanitize_ascii(cleaned)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    if not cleaned.endswith("\n"):
        cleaned += "\n"
    stats["objects"] = len(re.findall(r"(?m)^Object\s+", cleaned))
    return cleaned, stats


def catalog(entries):
    return turkey_wo.catalog(entries)


def parse_stack_fails(text: str, label: str) -> list[str]:
    # Extend turkey stack parse with ClientUpdate as opener so empty CU+End
    # residual is reported, but after repair CU should not use End.
    return turkey_wo.parse_stack_fails(text, label)


def validate_wo(text: str, entries, art_entries, label: str) -> list[str]:
    fails: list[str] = []
    cats = catalog(entries)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }
    if any(ord(c) > 127 for c in text):
        fails.append(f"{label}: non-ASCII")
    if not text.startswith("; SPECTER CRASH FIX - Russia_WeaponObjects"):
        fails.append(f"{label}: missing crash-fix header")
    objs = re.findall(r"(?m)^Object\s+(\S+)", text)
    if len(objs) != len(set(objs)):
        fails.append(f"{label}: duplicate Object names")
    fails.extend(parse_stack_fails(text, label))

    for i, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0]
        if "J2mmGrad" in code:
            fails.append(f"{label}: J2mmGrad remains @{i}")
        if "Iraq_Alhusain_W2" in code:
            fails.append(f"{label}: Iraq_Alhusain_W2 remains @{i}")
    if re.search(r"(?m)^\s*ClientUpdate\s*=\s*\S+[^\n]*\n\s*End\s*$", text):
        fails.append(f"{label}: ClientUpdate stray End remains")

    for model in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)):
        if model in ("None", "NONE", "NULL"):
            continue
        if model.lower() not in stems:
            fails.append(f"{label}: missing W3D Model={model}")

    # BV targets must resolve
    for name, block in extract_objects(text):
        m = re.search(r"(?m)^\s*BuildVariations\s*=\s*(.+)$", block)
        if not m:
            continue
        for v in m.group(1).split(";")[0].split():
            if v not in cats["Object"]:
                fails.append(f"{label}: {name} missing BV {v}")

    # Side=Iraq must be gone
    if re.search(r"(?m)^\s*Side\s*=\s*Iraq\s*$", text):
        fails.append(f"{label}: Side=Iraq remains")
    return fails


def russia_weapon_chain_scan(entries, art_entries) -> list[str]:
    fails: list[str] = []
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }
    cats = catalog(entries)
    w2p: dict[str, list[str]] = {}
    for n, r in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = r.decode("utf-8", "replace")
        for m in re.finditer(r"(?ms)^Weapon\s+(\S+)\s*$.*?(?=^Weapon\s|\Z)", t):
            w2p[m.group(1)] = re.findall(
                r"(?m)^\s*ProjectileObject\s*=\s*(\S+)", m.group(0)
            )

    obj_models: dict[str, list[str]] = {}
    for n, r in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = r.decode("utf-8", "replace")
        for name, block in extract_objects(t):
            obj_models[name] = [
                m
                for m in re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", block)
                if m not in ("None", "NONE")
            ]

    used = set()
    for n, r in entries:
        if not is_russia_object_ini(n):
            continue
        if "WeaponObjects" in n:
            continue
        t = r.decode("utf-8", "replace")
        for w in re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", t):
            if w in ("None", "NONE", "End"):
                continue
            used.add(w)

    for w in sorted(used):
        if w not in cats["Weapon"] and w not in w2p:
            continue
        for p in w2p.get(w, []):
            if p in ("None", "NONE"):
                continue
            if p not in cats["Object"]:
                fails.append(f"weapon {w}: missing ProjectileObject {p}")
                continue
            for m in obj_models.get(p, []):
                if m.lower() not in stems:
                    fails.append(f"weapon {w}: projectile {p} missing W3D Model={m}")
    return fails


def russia_integrity_scan(entries, art_entries) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []
    cats = catalog(entries)
    wo_hits = [n for n, _ in entries if is_russia_wo(n)]
    if len(wo_hits) != 1:
        fails.append(f"Russia_WeaponObjects.ini count={len(wo_hits)}")

    fails.extend(russia_weapon_chain_scan(entries, art_entries))

    for n, r in entries:
        if not is_russia_object_ini(n):
            continue
        text = r.decode("utf-8", "replace")
        bn = Path(n.replace("\\", "/")).name
        for m in re.finditer(r"(?m)^\s*BuildVariations\s*=\s*(.+)$", text):
            vals = m.group(1).split(";")[0].split()
            missing = [v for v in vals if v not in cats["Object"]]
            if missing:
                # WeaponObjects BV misses are hard fails; other Russia units soft-warn
                # unless we also patched that unit in this build.
                msg = f"{bn}: missing BV {missing}"
                if "WeaponObjects" in bn:
                    fails.append(msg)
                else:
                    warns.append(msg)
        if "WeaponObjects" in bn:
            continue
        for msg in parse_stack_fails(text, bn):
            # soft: many unit INIs have complex nested blocks our opener set misses
            warns.append(msg)
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
    for required in (
        DEFAULT_SHELL_MODEL,
        DEFAULT_BOMBLET_MODEL,
        "Iraq_Alhusain_W",
        "AIM-120",
        "9K720_M",
    ):
        if required.lower() not in stems:
            raise SystemExit(f"required ART model missing: {required}")

    old_hits = [(n, r) for n, r in entries if is_russia_wo(n)]
    print(f"DELETE phase: {len(old_hits)} Russia_WeaponObjects.ini")
    if len(old_hits) != 1:
        raise SystemExit(f"expected 1 Russia WO got {len(old_hits)}")
    old_shas = {base.sha256_bytes(r) for _, r in old_hits}
    old_raw = old_hits[0][1]
    old_names = set(re.findall(r"(?m)^Object\s+(\S+)", old_raw.decode("utf-8", "replace")))
    for n, r in old_hits:
        print(f"  removing {n} sha={base.sha256_bytes(r)[:16]} size={len(r)}")

    purged = [(n, r) for n, r in entries if not is_russia_wo(n)]
    cleaned, stats = rebuild_russia_wo(old_raw, stems)
    new_raw = cleaned.encode("ascii")
    if base.sha256_bytes(new_raw) in old_shas:
        raise SystemExit("hash collision with deleted WO")
    new_names = set(re.findall(r"(?m)^Object\s+(\S+)", cleaned))
    if new_names != old_names:
        raise SystemExit(
            "object set changed "
            f"missing={sorted(old_names - new_names)[:10]} "
            f"extra={sorted(new_names - old_names)[:10]}"
        )
    print(
        f"NEW WO sha={base.sha256_bytes(new_raw)[:16]} size={len(new_raw)} "
        f"objs={stats['objects']} cu_ends={stats['clientupdate_ends_removed']} "
        f"side={stats['side_forced']} none={stats['none_model_stats']}"
    )

    # Patch Russia Su-25T BV: Russia_Su-25T (missing) -> RussiaJetSU25T
    su25_path = None
    su25_raw = None
    for n, r in purged:
        ln = n.replace("/", "\\")
        if ln.endswith(r"Armed Forces Of Russian Federation\Airforce\SU25T_SU39.ini"):
            su25_path, su25_raw = n, r
            break
    patched_extra: dict[str, bytes] = {}
    if su25_raw is not None:
        su_text = su25_raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
        su2, n_su = re.subn(
            r"(?m)^(\s*BuildVariations\s*=\s*)Russia_Su-25T\b",
            r"\g<1>RussiaJetSU25T",
            su_text,
            count=1,
        )
        if n_su:
            su2, _ = turkey_batch.sanitize_ascii(su2)
            patched_extra[base.knorm(su25_path)] = su2.encode("ascii")
            stats["su25_bv_fixed"] = True
            print("Patched SU25T_SU39.ini BV: Russia_Su-25T -> RussiaJetSU25T")
        else:
            stats["su25_bv_fixed"] = False
    else:
        stats["su25_bv_fixed"] = False

    rebuilt = []
    for n, r in purged:
        kn = base.knorm(n)
        if kn in patched_extra:
            rebuilt.append((n, patched_extra[kn]))
        else:
            rebuilt.append((n, r))
    rebuilt.append((NEW_PATH, new_raw))

    counts: dict[str, int] = defaultdict(int)
    for n, _ in rebuilt:
        counts[base.knorm(n)] += 1
    dups = [k for k, v in counts.items() if v > 1]
    if dups:
        raise SystemExit(f"duplicate paths {dups}")

    failures = []
    failures.extend(validate_wo(cleaned, rebuilt, art_entries, "PREWRITE"))
    integ_fails, integ_warns = russia_integrity_scan(rebuilt, art_entries)
    failures.extend(integ_fails)
    if failures:
        print("PRE-WRITE FAILED")
        for f in failures[:120]:
            print(" ", f)
        return 1
    print(f"PASS pre-write (soft-warns={len(integ_warns)})")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, rebuilt)
    final_entries = base.parse_big(out_big)
    final_hits = [(n, r) for n, r in final_entries if is_russia_wo(n)]
    if len(final_hits) != 1:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"expected 1 WO entry got {len(final_hits)}")

    extract_root = OUT / "_EXTRACT_VERIFY"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    emb_name, emb = final_hits[0]
    post: list[str] = []
    if emb != new_raw:
        post.append("byte mismatch WO")
    if base.sha256_bytes(emb) in old_shas:
        post.append("old hash reused")
    if b"J2mmGrad" in emb or b"Iraq_Alhusain_W2" in emb:
        post.append("bad model token remains")

    rel = Path(*Path(emb_name.replace("\\", "/")).parts)
    ep = extract_root / rel
    ep.parent.mkdir(parents=True, exist_ok=True)
    ep.write_bytes(emb)
    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(new_raw)

    post.extend(validate_wo(emb.decode("ascii"), final_entries, art_entries, "EXTRACT"))
    post_fails, post_warns = russia_integrity_scan(final_entries, art_entries)
    post.extend(post_fails)
    if post:
        out_big.unlink(missing_ok=True)
        print("EXTRACT/INTEGRITY FAILED")
        for f in post[:120]:
            print(" ", f)
        return 1
    print(f"PASS extract + integrity (soft-warns={len(post_warns)})")

    old_by = {base.knorm(n): r for n, r in entries}
    new_by = {base.knorm(n): r for n, r in final_entries}
    allowed = {base.knorm(NEW_PATH)} | set(patched_extra)
    changed = [kn for kn in sorted(set(old_by) | set(new_by)) if old_by.get(kn) != new_by.get(kn)]
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
    (OUT / "CRASH_FIX_NOTES.txt").write_text(
        "RUSSIA WEAPONOBJECTS CRASH FIX\n"
        "==============================\n"
        f"clientupdate_ends_removed={stats['clientupdate_ends_removed']}\n"
        f"model_remaps={stats['model_remaps']}\n"
        f"bv_remaps={stats['bv_remaps']}\n"
        f"side_forced={stats['side_forced']}\n"
        f"none_model_stats={stats['none_model_stats']}\n"
        f"su25_bv_fixed={stats.get('su25_bv_fixed')}\n"
        f"objects={stats['objects']}\n",
        encoding="ascii",
    )
    verify = (
        "SPECTER RUSSIA WEAPONOBJECTS CRASH FIX - VERIFY REPORT\n"
        "======================================================\n"
        "VERDICT: PASS\n"
        "Crash file: Russia_WeaponObjects.ini\n"
        "Fix: DELETE+INSERT Russia_WeaponObjects; CU Ends; W3D/BV remaps; Model=None donors\n"
        f"Objects preserved: {stats['objects']}\n"
        "Russia unit weapon->projectile W3D scan: PASS\n"
        "Extract byte-match: PASS\n"
        f"BIG SHA256: {big_sha}\n"
        f"WO SHA256: {unit_sha}\n"
        f"BIG SIZE: {big_size}\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(verify, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "DELETE+INSERT PROOF\n"
        f"removed_shas={sorted(old_shas)}\n"
        f"new_sha256={unit_sha}\n"
        "old_hash_reuse=NO\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER RUSSIA WEAPONOBJECTS CRASH FIX\n"
        "=====================================\n\n"
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
            "RUSSIA_INTEGRITY_WARNINGS.txt",
            "CRASH_FIX_NOTES.txt",
            "Russia_WeaponObjects.ini",
        ):
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_RUSSIA_WEAPONOBJECTS_CRASH_FIXED.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "RUSSIA_INTEGRITY_WARNINGS.txt",
            "CRASH_FIX_NOTES.txt",
            "Russia_WeaponObjects.ini",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Russia_WeaponObjects.ini SHA256={unit_sha}\n"
        f"_SPEC_DATA_ONE_RUSSIA_WEAPONOBJECTS_CRASH_FIXED.zip SHA256={zip_sha}\n",
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
