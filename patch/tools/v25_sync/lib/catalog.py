"""Classify every V25 Object against SS1 load rules and the full dep chain.

An Object is never 'ready' only because its Object INI exists. Dest path must
be loadable in SS1, parse-fatal refs must resolve through the last Weapon /
Projectile / OCL / FXList hop in V25 or SS1, and CWC modules must be
rebuildable. Generals.exe is not run.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .ini import KIND_ALIASES
from .preflight import PARSE_FATAL_KINDS
from .rewrite import independent_name
from .ss1_layout import emit_path, path_loadable

CWC_MANUAL = {
    "riderchangecontain",
    "oclspecialpower",
    "weaponbonusupdate",
}
# Existence-only: do not treat Armor damage tables / portraits as child defs.
NO_WALK_KINDS = {
    "Armor",
    "MappedImage",
    "AudioEvent",
    "DialogEvent",
    "Locomotor",
    "ParticleSystem",
    # CommandButton Object= slots are other units (factory build lists), not
    # this object's projectile/weapon chain. CommandSet itself IS walked so
    # its CommandButton names are existence-checked (parse-fatal).
    "CommandButton",
    "Science",
    "Upgrade",
}


def _index(inv: dict) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for kind, table in inv.items():
        if not isinstance(table, dict):
            continue
        for name in table:
            out[kind.lower()].add(str(name).lower())
    return out


def _lookup_rec(inv: dict, kind: str, name: str) -> dict | None:
    bucket = inv.get(kind) or {}
    rec = bucket.get(name)
    if rec is None:
        rec = next((v for k, v in bucket.items() if k.lower() == name.lower()), None)
    if rec is None:
        for alias in KIND_ALIASES.get(kind) or ():
            rec = _lookup_rec({alias: inv.get(alias) or {}}, alias, name)
            if rec is not None:
                return rec
    return rec


def walk_object_chain(
    kind: str,
    name: str,
    v25: dict,
    spec_idx: dict[str, set[str]],
    cache: dict,
    stack: set | None = None,
) -> dict:
    """Walk V25 named refs to the end. Reuse SS1 when the name is absent from V25."""
    key = (kind.lower(), name.lower())
    if key in cache:
        return cache[key]
    stack = stack if stack is not None else set()
    if key in stack:
        return {"missing_fatal": [], "missing_soft": [], "visited": [], "cycle": True}

    rec = _lookup_rec(v25, kind, name)
    if rec is None:
        if name.lower() in spec_idx.get(kind.lower(), set()):
            result = {"missing_fatal": [], "missing_soft": [], "visited": [], "reused_ss1": True}
        else:
            item = f"{kind}:{name}"
            fatal = kind in PARSE_FATAL_KINDS
            result = {
                "missing_fatal": [item] if fatal else [],
                "missing_soft": [] if fatal else [item],
                "visited": [],
            }
        cache[key] = result
        return result

    stack.add(key)
    fatal: list[str] = []
    soft: list[str] = []
    visited = [f"{kind}:{name}"]
    if kind not in NO_WALK_KINDS:
        for rkind, rnames in (rec.get("named_refs") or {}).items():
            for rn in rnames:
                child = walk_object_chain(rkind, rn, v25, spec_idx, cache, stack)
                fatal.extend(child.get("missing_fatal") or [])
                soft.extend(child.get("missing_soft") or [])
                visited.extend(child.get("visited") or [])
    stack.discard(key)

    def _uniq(seq: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for x in seq:
            xl = x.lower()
            if xl in seen:
                continue
            seen.add(xl)
            out.append(x)
        return out

    result = {
        "missing_fatal": _uniq(fatal),
        "missing_soft": _uniq(soft),
        "visited": _uniq(visited),
    }
    cache[key] = result
    return result


def classify_object(name: str, rec: dict, v25: dict, spec_idx: dict, rules: dict, recipes: dict, cache: dict) -> dict:
    side = ""
    for k, v in rec.get("keys") or []:
        if k.strip().lower() == "side":
            side = v.split()[0]
            break
    blocked_sides = {s.lower() for s in (rules.get("blocked_object_sides") or [])}
    planned = independent_name(name) if name.lower() in spec_idx.get("object", set()) else name
    dest = emit_path("Object", planned, side or "Unmapped")
    load = path_loadable(dest)

    chain = walk_object_chain("Object", name, v25, spec_idx, cache)
    missing_fatal = chain.get("missing_fatal") or []
    missing_soft = list(chain.get("missing_soft") or [])

    behaviors = [b.lower() for b in (rec.get("behaviors") or [])]
    cwc_hits = [b for b in (rec.get("behaviors") or []) if b.lower() in CWC_MANUAL]
    proof = None
    if "riderchangecontain" in behaviors:
        from . import data_rebuild

        proof = data_rebuild.prove_rider_deploy(rec)

    status = "unique_import_ready"
    reasons = []
    if side.lower() in blocked_sides:
        status = "blocked"
        reasons.append(f"blocked_side:{side}")
    elif cwc_hits and not (proof and proof.get("compatible")):
        status = "needs_rebuild"
        reasons.append("cwc:" + ",".join(cwc_hits))
    elif missing_fatal:
        status = "needs_fix"
        reasons.append("missing_parse_ref")
    elif not load.get("loaded"):
        status = "needs_fix"
        reasons.append("unloadable_dest")
    elif name.lower() in spec_idx.get("object", set()):
        status = "rename_or_reuse"
        reasons.append("name_in_ss1")

    ready = status == "unique_import_ready" and not missing_fatal and load.get("loaded")
    if status == "rename_or_reuse":
        reasons.append("not_ready_until_rewrite_plan")

    return {
        "object": name,
        "planned_name": planned,
        "side": side,
        "dest_ini": dest,
        "dest_loadable": bool(load.get("loaded")),
        "dest_confidence": load.get("confidence"),
        "status": status,
        "ready_for_safe_transfer": bool(ready),
        "reasons": reasons,
        "missing_parse_refs": missing_fatal[:20],
        "missing_runtime_refs": missing_soft[:12],
        "dep_count": len(chain.get("visited") or []),
        "cwc_behaviors": cwc_hits,
        "behaviors": rec.get("behaviors") or [],
    }


def catalog_objects(v25: dict, spec: dict, rules: dict, recipes: dict | None = None) -> dict:
    spec_idx = _index(spec)
    objects = v25.get("Object") or {}
    rows = []
    counts: Counter = Counter()
    cache: dict = {}
    for name, rec in objects.items():
        row = classify_object(name, rec, v25, spec_idx, rules, recipes or {}, cache)
        rows.append(row)
        counts[row["status"]] += 1
        if row["ready_for_safe_transfer"]:
            counts["ready_for_safe_transfer"] += 1
    rows.sort(key=lambda r: r["object"].lower())
    return {
        "object_count": len(rows),
        "counts": dict(counts),
        "note": (
            "ready_for_safe_transfer requires SS1-loadable dest, no parse-fatal missing refs "
            "anywhere on the Weapon/Projectile/OCL/FXList chain, and no CWC manual rebuild. "
            "It is not 'Object INI exists'. Generals.exe was not run."
        ),
        "objects": rows,
    }


def _sample_rows(rows: list[dict], status: str, n: int = 12) -> list[dict]:
    return [r for r in rows if r.get("status") == status][:n]


def catalog_markdown(cat: dict, generated_at: str) -> str:
    counts = cat.get("counts") or {}
    rows = cat.get("objects") or []
    lines = [
        "# V25 object catalog against SS1 rules",
        "",
        f"- Generated: {generated_at}",
        f"- V25 Objects: **{cat.get('object_count')}**",
        f"- Ready for safe transfer: **{counts.get('ready_for_safe_transfer', 0)}**",
        f"- unique_import_ready: **{counts.get('unique_import_ready', 0)}**",
        f"- needs_fix (parse refs / dest): **{counts.get('needs_fix', 0)}**",
        f"- needs_rebuild (CWC): **{counts.get('needs_rebuild', 0)}**",
        f"- blocked: **{counts.get('blocked', 0)}**",
        f"- rename_or_reuse (name in SS1): **{counts.get('rename_or_reuse', 0)}**",
        "",
        cat.get("note") or "",
        "",
        "Generals.exe was **not** run. Static catalog only.",
        "",
    ]
    for status, title in (
        ("needs_fix", "Needs fix (sample)"),
        ("needs_rebuild", "Needs rebuild (sample)"),
        ("blocked", "Blocked (sample)"),
        ("rename_or_reuse", "Name in SS1 (sample)"),
        ("unique_import_ready", "Unique import ready (sample)"),
    ):
        sample = _sample_rows(rows, status)
        lines += [f"## {title}", ""]
        if not sample:
            lines.append("- (none)")
        for r in sample:
            miss = ", ".join(r.get("missing_parse_refs") or []) or "-"
            reasons = ", ".join(r.get("reasons") or []) or "-"
            lines.append(
                f"- `{r['object']}` → `{r.get('dest_ini')}` loadable={r.get('dest_loadable')} "
                f"deps={r.get('dep_count', 0)} reasons={reasons} missing={miss}"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def engine_audit_markdown(report: dict, layout: dict, cat: dict) -> str:
    counts = cat.get("counts") or {}
    hashes = report.get("original_hashes") or {}
    lines = [
        "# SS1 compatibility engine audit",
        "",
        f"- Generated: {report.get('generated_at_tehran')}",
        f"- Mode: `{report.get('mode')}`",
        f"- Original SPECTER BIGs modified: **{report.get('game_bigs_modified')}**",
        f"- Original hashes unchanged: **{report.get('original_hashes_unchanged')}**",
        f"- Equipment imported: **{report.get('equipment_imported')}**",
        f"- Loose INI written: **{report.get('loose_ini_written')}**",
        f"- Generals.exe run: **{report.get('generals_exe_run')}**",
        "",
        "## SPECTER FINAL (SS1) hashes (read-only)",
        "",
        f"- `_SPEC_DATA_ONE.big`: `{hashes.get('_SPEC_DATA_ONE.big')}`",
        f"- `_SPEC_ART_TWO.big`: `{hashes.get('_SPEC_ART_TWO.big')}`",
        "",
        "## SS1 load topology (from live DATA BIG)",
        "",
        f"- Data\\INI root files: **{(layout.get('root_ini_count'))}**",
        f"- Object recursive: **{(layout.get('object') or {}).get('recursive')}**",
        f"- Weapon\\ recursive: **{(layout.get('weapon_dir') or {}).get('recursive')}**",
        f"- Weapon\\ nested subdir files: **{(layout.get('weapon_dir') or {}).get('nested_files')}**",
        f"- MappedImages subdirs: `{(layout.get('mappedimages') or {}).get('subdirs')}`",
        "",
        "Proven extra root prefixes:",
        "",
    ]
    for p in layout.get("proven_root_prefixes") or []:
        lines.append(f"- `{p}*`")
    lines += [
        "",
        "Unproven extra root kinds (root `loadDirectory` should still parse first-token blocks):",
        "",
    ]
    for p in layout.get("unproven_root_kinds") or []:
        lines.append(f"- `{p}*`")
    lines += [
        "",
        "## Emit paths (SS1-safe)",
        "",
        "- Objects: `Data\\INI\\Object\\SilentDeath\\{Side}\\{Name}.ini` (recursive, proven)",
        "- Weapons: `Data\\INI\\Weapon_SilentDeath.ini` (root extra, proven). **Never** `Weapon\\SilentDeath\\`",
        "- MappedImages: `Data\\INI\\MappedImages\\HandCreated\\SilentDeathMappedImages.ini`",
        "- CommandSet overlay: `Data\\INI\\CommandSet_ZZZZ_SilentDeath_{Side}.ini`",
        "",
        "## Catalog (entire V25 Object table)",
        "",
        f"- Objects: **{cat.get('object_count')}**",
        f"- Ready for safe transfer: **{counts.get('ready_for_safe_transfer', 0)}**",
        f"- unique_import_ready: **{counts.get('unique_import_ready', 0)}**",
        f"- needs_fix: **{counts.get('needs_fix', 0)}**",
        f"- needs_rebuild: **{counts.get('needs_rebuild', 0)}**",
        f"- blocked: **{counts.get('blocked', 0)}**",
        f"- rename_or_reuse: **{counts.get('rename_or_reuse', 0)}**",
        "",
        "## Stage 5 crash classes now gated by preflight",
        "",
        "- Nested `Weapon\\SilentDeath\\` unloadable",
        "- Nested `MappedImages\\SilentDeath\\` unloadable",
        "- Missing `DeathWeapon` / `IgnitionFX` parse-fatal",
        "- Locomotor uncommented `GroupMovementPriority` tail",
        "- FXList missing column-0 `End`",
        "- Tokens after Object `End` (HQ11 DEPLOYED draw)",
        "- Duplicate named Armor/Weapon/FXList",
        "- Object file existence is not readiness",
        "",
        f"- Preflight rejects nested Weapon: **{report.get('preflight_sample_rejects_nested_weapon')}**",
        f"- Preflight rejects MappedImages\\SilentDeath: **{report.get('preflight_sample_rejects_mappedimages_silentdeath')}**",
        "",
        "## What this engine still is not",
        "",
        "- Not a Generals.exe boot test",
        "- Not an install pack and not a bulk transfer",
        "- Unproven root kinds (Armor_/Locomotor_/FXList_ extras) are warnings, not proof they load",
        "- ART/W3D integrity is not a parse-fatal INI check",
        "",
        "Do not start grouped equipment transfer until ready_for_safe_transfer rows are packed",
        "only after preflight on the actual added payloads.",
        "",
    ]
    return "\n".join(lines) + "\n"
