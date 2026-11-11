"""End-to-end dry-run of the SS1 compatibility engine.

Selects tanks / air defense / buildings / missiles / aircraft / mobile units,
walks each chain to SS1 dest paths, and re-validates catalog-ready rows against
the actual V25 INI bytes. Never writes SPECTER BIGs or loose INI.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from . import catalog
from .normalize import normalize_payloads
from .payloads import assemble_payloads
from .preflight import (
    check_duplicate_named_blocks,
    check_fxlist_ends,
    check_locomotor_comments,
    check_object_orphan_after_end,
    native_def_index,
    preflight_payloads,
)
from .ss1_layout import path_loadable

ROLES = ("tank", "air_defense", "structure", "missile", "aircraft", "mobile")

PREFERRED = {
    "tank": (
        "ChinaTankOverlord",
        "ChinaTankBattleMaster",
        "AmericaTankCrusader",
        "ChinaTankGattling",
        "ChinaCSSA1",
    ),
    "air_defense": (
        "ChinaS400",
        "ChinaHQ9",
        "AmericaPatriotBattery",
        "AmericaThaad",
        "ChinaHQ11",
        "AmericaIronDome",
    ),
    "structure": (
        "ChinaWarFactory",
        "ChinaCommandCenter",
        "AmericaWarFactory",
        "ChinaBarracks",
        "ChinaAirfield",
    ),
    "missile": (
        "TomahawkMissile",
        "ScudStormMissile",
        "AuroraBomb",
        "PatriotMissile",
        "ChinaCSSA1Missile",
    ),
    "aircraft": (
        "AmericaJetRaptor",
        "ChinaMig",
        "AmericaJetAurora",
        "ChinaHelix",
        "AmericaVehicleComanche",
    ),
    "mobile": (
        "AmericaVehicleHumvee",
        "ChinaVehicleTroopCrawler",
        "AmericaVehicleDozer",
        "ChinaVehicleSupplyTruck",
        "AmericaVehicleChinook",
    ),
}

PER_ROLE = 5
READY_RECHECK_CAP = 400

SYNTAX_CODES = {
    "fxlist_missing_column0_end",
    "locomotor_uncommented_tail",
}


def object_role(name: str, rec: dict, meta: dict | None = None) -> str | None:
    kinds = set()
    if meta and meta.get("kindof"):
        kinds.update(str(k).upper() for k in meta["kindof"])
    for k, v in rec.get("keys") or []:
        if k.strip().lower() == "kindof":
            kinds.update(t.upper() for t in v.split() if t.strip())
    bucket = (meta or {}).get("bucket") or ""
    nl = name.lower()
    if kinds.intersection(("PROJECTILE", "SMALL_MISSILE", "BALLISTIC_MISSILE")) or "missile" in nl:
        return "missile"
    if bucket == "air_defense" or kinds.intersection(("CAN_ATTACK_AIRBORNE_VEHICLES", "CAN_ATTACK_MISSILES")):
        return "air_defense"
    if "AIRCRAFT" in kinds or bucket == "aircraft":
        return "aircraft"
    if "TANK" in kinds or ("tank" in nl and "VEHICLE" in kinds):
        return "tank"
    if "STRUCTURE" in kinds or bucket == "structure":
        return "structure"
    if "VEHICLE" in kinds or bucket == "vehicle":
        return "mobile"
    return None


def syntax_audit_v25(v25: dict) -> dict:
    """Scan V25 def bodies for Stage 5 syntax classes. No dest files."""
    counts: Counter = Counter()
    samples: dict[str, list[str]] = defaultdict(list)
    for kind, table in v25.items():
        if not isinstance(table, dict):
            continue
        for name, rec in table.items():
            body = rec.get("body") or ""
            path = f"{kind}:{name}"
            errs = []
            if kind == "FXList":
                errs.extend(check_fxlist_ends(body, path))
            if kind == "Object":
                errs.extend(check_object_orphan_after_end(body, path))
            if kind == "Locomotor":
                errs.extend(check_locomotor_comments(body, path))
            if kind in ("Armor", "Weapon", "FXList", "Object"):
                errs.extend(check_duplicate_named_blocks(body, path))
            for e in errs:
                code = e.get("code") or "syntax"
                counts[code] += 1
                if len(samples[code]) < 8:
                    samples[code].append(path)
    return {"error_counts": dict(counts), "samples": dict(samples), "generals_exe_run": False}


def capabilities(rec: dict) -> list[str]:
    body = (rec.get("body") or "").lower()
    out = []
    for marker, label in (
        ("riderchangecontain", "RiderChangeContain (CWC)"),
        ("oclspecialpower", "OCLSpecialPower (CWC)"),
        ("weaponbonusupdate", "WeaponBonusUpdate (CWC)"),
        ("deploystyleaiupdate", "DeployStyleAIUpdate"),
        ("radarupdate", "RadarUpdate"),
        ("missileaiupdate", "MissileAIUpdate"),
        ("jetaiupdate", "JetAIUpdate"),
        ("pointdefenselaserupdate", "PointDefenseLaserUpdate"),
        ("overlordcontain", "OverlordContain"),
        ("fireweaponwhendeadbehavior", "FireWeaponWhenDeadBehavior"),
        ("assistedtargetingupdate", "AssistedTargetingUpdate"),
    ):
        if marker in body:
            out.append(label)
    return out


def verdict_from(
    cat_row: dict,
    assembled: dict,
    pf: dict,
    rec: dict,
    pf_norm: dict | None = None,
) -> dict:
    reasons = list(cat_row.get("reasons") or [])
    missing = list(assembled["chain"].get("missing_fatal") or [])
    caps = capabilities(rec)
    dest_ini = assembled["dest_ini"]
    load = path_loadable(dest_ini)
    unloadable = [d for d in assembled["dests"] if d.get("dest") and not d.get("dest_loadable")]
    pf_ok = bool(pf.get("ok"))
    pf_norm_ok = bool((pf_norm or {}).get("ok")) if pf_norm is not None else pf_ok
    catalog_ready = bool(cat_row.get("ready_for_safe_transfer"))
    raw_codes = {e.get("code") for e in (pf.get("errors") or [])}

    status = "pass"
    if cat_row.get("status") == "blocked" or any(str(r).startswith("blocked_side") for r in reasons):
        status = "blocked"
        reasons.append("blocked_side")
    elif cat_row.get("status") in ("needs_rebuild", "MANUAL_REBUILD"):
        status = "blocked"
        reasons.append("cwc_rebuild_required")
    elif missing:
        status = "fail"
        reasons.append("missing_parse_ref")
    elif not load.get("loaded") or unloadable:
        status = "fail"
        reasons.append("unloadable_dest")
    elif pf_ok:
        status = "pass"
        if assembled.get("rename"):
            reasons.append("rewrite_planned")
    elif pf_norm_ok and (not raw_codes or raw_codes <= SYNTAX_CODES):
        status = "repairable"
        reasons.append("raw_bytes_need_syntax_normalize")
        reasons.extend(sorted(c for c in raw_codes if c))
    elif not pf_ok:
        status = "fail"
        reasons.append("preflight_bytes")
        for e in (pf.get("errors") or [])[:8]:
            reasons.append(e.get("code") or "preflight")
    else:
        status = "fail"
        reasons.append(cat_row.get("status") or "e2e_fail")

    if status == "pass" and (missing or not pf_ok or unloadable):
        status = "fail"
    false_ready = bool(catalog_ready and status == "fail")
    if false_ready:
        reasons.append("catalog_false_ready")

    return {
        "status": status,
        "false_ready": false_ready,
        "catalog_ready": catalog_ready,
        "catalog_status": cat_row.get("status"),
        "reasons": list(dict.fromkeys(reasons)),
        "missing_parse_refs": missing[:16],
        "preflight_ok": pf_ok,
        "normalized_preflight_ok": pf_norm_ok,
        "preflight_errors": (pf.get("errors") or [])[:12],
        "capabilities": caps,
        "dest_ini": dest_ini,
        "dest_loadable": bool(load.get("loaded")),
        "planned_object": assembled["planned_object"],
        "rename_map": assembled["rename"],
        "dep_count": len(assembled["chain"].get("visited") or []),
        "emitted_files": sorted(assembled["payloads"]),
        "unloadable_dests": unloadable[:8],
        "files_written": [],
    }


def select_samples(v25: dict, spec: dict, cat_rows: list[dict], engine) -> list[dict]:
    by_name = {r["object"]: r for r in cat_rows}
    objects = v25.get("Object") or {}
    grouped: dict[str, list[str]] = {r: [] for r in ROLES}
    for name, rec in objects.items():
        meta = engine.object_meta(rec) if hasattr(engine, "object_meta") else {}
        role = object_role(name, rec, meta)
        if role:
            grouped[role].append(name)

    picked: list[dict] = []
    seen: set[str] = set()

    def add(role: str, name: str) -> None:
        if name in seen or name not in objects:
            return
        seen.add(name)
        rec = objects[name]
        meta = engine.object_meta(rec) if hasattr(engine, "object_meta") else {}
        picked.append(
            {
                "object": name,
                "role": role,
                "catalog": by_name.get(name) or {},
                "rec": rec,
                "meta": meta,
            }
        )

    for role in ROLES:
        for pref in PREFERRED.get(role) or ():
            add(role, pref)
        ready = [n for n in grouped[role] if (by_name.get(n) or {}).get("ready_for_safe_transfer")]
        other = [n for n in grouped[role] if n not in ready]
        for n in ready[: max(0, PER_ROLE - sum(1 for p in picked if p["role"] == role))]:
            add(role, n)
        if sum(1 for p in picked if p["role"] == role) < 3:
            for n in other[: PER_ROLE]:
                add(role, n)
                if sum(1 for p in picked if p["role"] == role) >= PER_ROLE:
                    break
    return picked


def dry_run_object(sample: dict, v25: dict, spec: dict, spec_idx: dict, cache: dict, native: dict) -> dict:
    name = sample["object"]
    rec = sample["rec"]
    cat_row = sample.get("catalog") or {}
    side = cat_row.get("side") or sample.get("meta", {}).get("specter_side") or sample.get("meta", {}).get("side") or "Unmapped"
    assembled = assemble_payloads(name, rec, v25, spec, spec_idx, cache, side)
    pf = preflight_payloads(assembled["payloads"], native_defs=native)
    pf_norm = preflight_payloads(normalize_payloads(assembled["payloads"]), native_defs=native)
    verdict = verdict_from(cat_row, assembled, pf, rec, pf_norm=pf_norm)
    return {
        "object": name,
        "role": sample.get("role"),
        "side": side,
        "kindof": (sample.get("meta") or {}).get("kindof") or [],
        "bucket": (sample.get("meta") or {}).get("bucket"),
        "source": rec.get("source"),
        **verdict,
        "dests": assembled["dests"][:40],
        "art_refs": rec.get("art_refs") or [],
        "bytes_validated": True,
        "generals_exe_run": False,
        "game_files_written": False,
    }


def pick_ready_recheck(cat_rows: list[dict], already: set[str]) -> list[str]:
    ready = [r["object"] for r in cat_rows if r.get("ready_for_safe_transfer") and r["object"] not in already]
    # Stratify by dest side so one faction does not dominate.
    by_side: dict[str, list[str]] = defaultdict(list)
    for r in cat_rows:
        if r.get("ready_for_safe_transfer") and r["object"] not in already:
            by_side[r.get("side") or "Unmapped"].append(r["object"])
    out: list[str] = []
    while len(out) < READY_RECHECK_CAP and any(by_side.values()):
        for side in list(by_side):
            if by_side[side]:
                out.append(by_side[side].pop(0))
            if len(out) >= READY_RECHECK_CAP:
                break
        if not any(by_side.values()):
            break
    return out[:READY_RECHECK_CAP]


def engine_gaps(syntax: dict, summary: dict) -> list[str]:
    gaps = [
        "Generals.exe is not run; pass is static INI/VFS only.",
        "ART/W3D/texture bytes are inventoried as stems, not opened or packed.",
        "Armor_/Locomotor_/FXList_/DamageFX_/Crate_/ParticleSystem_/SoundEffects_ extras are proven as the same Data\\INI root first-token loader as Weapon_*.ini (live stock table + extra root INI).",
        "Bulk CommandSet factory-slot overlay is not planned (Stage 5 did PLAWarFactory slots 4/7 only).",
        "Audio wav recovery from V25 volumes is not part of this dry-run.",
        "Catalog CommandButton existence is now walked from CommandSet; factory Object= slots stay unwalked on purpose.",
        "Shared-name rewrite is planned in memory; it is not applied to a BIG.",
        "Do not start grouped transfer until false_ready is 0 on the byte Ready Gate. Experimental DATA pack is dry-run only.",
    ]
    if syntax.get("error_counts"):
        gaps.insert(
            0,
            "V25 source INI contains Stage 5 syntax classes (FXList End / Object orphan / Locomotor tail / dupes); "
            "bulk copy of raw V25 bodies is unsafe: {0}".format(syntax["error_counts"]),
        )
    if summary.get("false_ready"):
        gaps.insert(
            0,
            f"{summary['false_ready']} catalog-ready objects failed byte preflight — catalog must not be the pack gate.",
        )
    return gaps


def e2e_markdown(report: dict) -> str:
    s = report.get("summary") or {}
    lines = [
        "# SS1 compatibility engine — End-to-End dry-run",
        "",
        f"- Generated: {report.get('generated_at_tehran')}",
        f"- SPECTER BIGs modified: **{report.get('game_bigs_modified')}**",
        f"- Equipment imported: **{report.get('equipment_imported')}**",
        f"- Loose INI written: **{report.get('loose_ini_written')}**",
        f"- Generals.exe run: **{report.get('generals_exe_run')}**",
        "",
        "## Counts",
        "",
        f"- Samples: **{s.get('samples')}**",
        f"- Pass (raw bytes): **{s.get('pass')}**",
        f"- Repairable (known syntax rewrite): **{s.get('repairable')}**",
        f"- Fail: **{s.get('fail')}**",
        f"- Blocked: **{s.get('blocked')}**",
        f"- Catalog-ready rechecked from bytes: **{s.get('ready_rechecked')}**",
        f"- Catalog false-ready (bytes disagree): **{s.get('false_ready')}**",
        "",
        "## Role samples",
        "",
    ]
    for row in report.get("samples") or []:
        lines.append(
            f"- **{row.get('role')}** `{row.get('object')}` → `{row.get('dest_ini')}` "
            f"**{row.get('status')}** deps={row.get('dep_count')} "
            f"catalog={row.get('catalog_status')} reasons={', '.join(row.get('reasons') or []) or '-'} "
            f"caps={', '.join(row.get('capabilities') or []) or '-'}"
        )
    lines += ["", "## Failures", ""]
    fails = [r for r in (report.get("samples") or []) + (report.get("ready_recheck") or []) if r.get("status") == "fail"]
    if not fails:
        lines.append("- none in this run")
    for r in fails[:40]:
        pf = r.get("preflight_errors") or []
        pf_s = "; ".join(f"{e.get('code')}:{e.get('ref') or e.get('path')}" for e in pf[:4])
        lines.append(
            f"- `{r.get('object')}` role={r.get('role') or 'ready_recheck'} "
            f"reasons={', '.join(r.get('reasons') or [])} missing={', '.join(r.get('missing_parse_refs') or []) or '-'} "
            f"preflight={pf_s or '-'}"
        )
    lines += ["", "## V25 syntax audit (whole archive)", ""]
    syn = report.get("syntax_audit") or {}
    lines.append(f"- counts: `{syn.get('error_counts')}`")
    for code, names in (syn.get("samples") or {}).items():
        lines.append(f"- `{code}`: {', '.join(names)}")
    lines += ["", "## Engine gaps before grouped transfer", ""]
    for g in report.get("engine_gaps") or []:
        lines.append(f"- {g}")
    lines += [
        "",
        "## Next stage suggestion",
        "",
        report.get("next_stage") or "",
        "",
    ]
    return "\n".join(lines) + "\n"


def run_e2e(engine) -> dict:
    from . import ss1_layout
    from .engine import sha256_file, tehran_now

    orig_data = engine.ss1 / "_SPEC_DATA_ONE.big"
    orig_art = engine.ss1 / "_SPEC_ART_TWO.big"
    before = {
        "_SPEC_DATA_ONE.big": sha256_file(orig_data) if orig_data.is_file() else None,
        "_SPEC_ART_TWO.big": sha256_file(orig_art) if orig_art.is_file() else None,
    }
    rules = __import__("json").loads((engine.data / "compatibility_rules.json").read_text(encoding="utf-8"))
    v25 = engine.inventory_v25()
    spec = engine.inventory_specter()
    spec_idx = catalog._index(spec)
    native = native_def_index(spec)
    cat = catalog.catalog_objects(v25, spec, rules, {})
    cache: dict = {}
    samples = select_samples(v25, spec, cat["objects"], engine)
    sample_rows = [dry_run_object(s, v25, spec, spec_idx, cache, native) for s in samples]
    already = {s["object"] for s in sample_rows}
    recheck_names = pick_ready_recheck(cat["objects"], already)
    by_name = {r["object"]: r for r in cat["objects"]}
    objects = v25.get("Object") or {}
    recheck_rows = []
    for name in recheck_names:
        rec = objects.get(name)
        if not rec:
            continue
        sample = {
            "object": name,
            "role": object_role(name, rec, engine.object_meta(rec)),
            "catalog": by_name.get(name) or {},
            "rec": rec,
            "meta": engine.object_meta(rec),
        }
        recheck_rows.append(dry_run_object(sample, v25, spec, spec_idx, cache, native))

    all_rows = sample_rows + recheck_rows
    counts = Counter(r["status"] for r in all_rows)
    false_ready = sum(1 for r in all_rows if r.get("false_ready"))
    syn = syntax_audit_v25(v25)
    summary = {
        "samples": len(sample_rows),
        "ready_rechecked": len(recheck_rows),
        "pass": counts.get("pass", 0),
        "repairable": counts.get("repairable", 0),
        "fail": counts.get("fail", 0),
        "blocked": counts.get("blocked", 0),
        "false_ready": false_ready,
        "roles": dict(Counter(r.get("role") for r in sample_rows)),
    }
    next_stage = (
        "Do not start grouped equipment transfer. Ready Gate + output-only normalize + proven "
        "root kinds are in this stage; experimental DATA pack is dry-run only and does not "
        "import equipment into original SPECTER FINAL."
        if false_ready or counts.get("fail")
        else "Ready Gate matched byte preflight on this sample. Next still is not bulk import: ART recovery, then a larger experimental role-group pack."
    )
    after = {
        "_SPEC_DATA_ONE.big": sha256_file(orig_data) if orig_data.is_file() else None,
        "_SPEC_ART_TWO.big": sha256_file(orig_art) if orig_art.is_file() else None,
    }
    report = {
        "mode": "ss1-e2e-dry-run",
        "generated_at_tehran": tehran_now(),
        "game_bigs_modified": False,
        "original_hashes_unchanged": before == after,
        "original_hashes": after,
        "generals_exe_run": False,
        "loose_ini_written": False,
        "equipment_imported": False,
        "files_written": [],
        "ss1_layout": {
            "weapon_nested_files": (ss1_layout.discover(orig_data).get("weapon_dir") or {}).get("nested_files")
            if orig_data.is_file()
            else None
        },
        "summary": summary,
        "syntax_audit": syn,
        "samples": [{k: v for k, v in r.items() if k != "preflight_errors" or True} for r in sample_rows],
        "ready_recheck": [
            {
                "object": r["object"],
                "role": r.get("role"),
                "status": r["status"],
                "false_ready": r.get("false_ready"),
                "reasons": r.get("reasons"),
                "missing_parse_refs": r.get("missing_parse_refs"),
                "preflight_errors": r.get("preflight_errors"),
                "dest_ini": r.get("dest_ini"),
            }
            for r in recheck_rows
            if r["status"] != "pass" or r.get("false_ready")
        ],
        "engine_gaps": engine_gaps(syn, summary),
        "next_stage": next_stage,
        "catalog_counts": cat.get("counts"),
    }
    # Drop bulky dests from markdown-facing samples already stored; keep JSON full samples.
    return report
