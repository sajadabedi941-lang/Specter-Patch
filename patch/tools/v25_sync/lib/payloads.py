"""In-memory unique-path payload assembly. Never writes game files."""
from __future__ import annotations

import hashlib
from collections import defaultdict

from . import catalog
from .normalize import normalize_payloads, object_missing_end
from .pack_sample import rewrite_header
from .preflight import native_def_index, preflight_payloads
from .rewrite import independent_name, rewrite_text
from .ss1_layout import emit_path, path_loadable


def emit_kind_for(kind: str) -> str:
    if kind == "CrateTemplate":
        return "CrateData"
    return kind


def _lookup(inv: dict, kind: str, name: str) -> dict | None:
    return catalog._lookup_rec(inv, kind, name)


def _body_hash(rec: dict | None) -> str:
    return hashlib.sha256(((rec or {}).get("body") or "").encode("utf-8", errors="replace")).hexdigest()


def assemble_payloads(
    name: str,
    rec: dict,
    v25: dict,
    spec: dict,
    spec_idx: dict,
    cache: dict,
    side: str,
) -> dict:
    """Build unique-path dest payloads in memory. Nothing is written."""
    chain = catalog.walk_object_chain("Object", name, v25, spec_idx, cache)
    rename: dict[str, str] = {}
    pending: list[tuple[str, str, str, dict]] = []
    dests: list[dict] = []
    visited = chain.get("visited") or [f"Object:{name}"]
    seen_emit: set[tuple[str, str]] = set()

    for item in visited:
        if ":" not in item:
            continue
        kind, dep = item.split(":", 1)
        vrec = _lookup(v25, kind, dep)
        if vrec is None:
            dests.append({"kind": kind, "name": dep, "action": "REUSE_NATIVE_OR_MISSING", "dest": None})
            continue
        srec = _lookup(spec, kind, dep)
        action = "IMPORT_UNIQUE"
        new = dep
        if srec is not None:
            if _body_hash(vrec) == _body_hash(srec):
                dests.append(
                    {
                        "kind": kind,
                        "name": dep,
                        "action": "REUSE_NATIVE",
                        "dest": None,
                        "planned": dep,
                    }
                )
                continue
            action = "RENAME_AND_REWRITE"
            new = independent_name(dep)
            rename[dep] = new
        out_kind = emit_kind_for(kind)
        key = (out_kind.lower(), new.lower())
        if key in seen_emit:
            continue
        seen_emit.add(key)
        dest = emit_path(out_kind, new, side or "Unmapped")
        load = path_loadable(dest)
        dests.append(
            {
                "kind": out_kind,
                "name": dep,
                "planned": new,
                "action": action,
                "dest": dest,
                "dest_loadable": bool(load.get("loaded")),
                "dest_confidence": load.get("confidence"),
            }
        )
        pending.append((out_kind, new, dest, vrec))

    payloads: dict[str, list[str]] = defaultdict(list)
    for out_kind, new, dest, vrec in pending:
        payloads[dest].append(rewrite_header(out_kind, new, rewrite_text(vrec.get("body") or "", rename)))

    planned_obj = rename.get(name, name)
    obj_dest = emit_path("Object", planned_obj, side or "Unmapped")
    joined = {path: "\n".join(chunks) for path, chunks in payloads.items()}
    if rec.get("body") is not None and obj_dest not in joined:
        joined[obj_dest] = rewrite_header("Object", planned_obj, rewrite_text(rec.get("body") or "", rename))

    return {
        "payloads": joined,
        "dests": dests,
        "rename": rename,
        "chain": chain,
        "planned_object": planned_obj,
        "dest_ini": obj_dest,
    }


def byte_gate(name: str, rec: dict, v25: dict, spec: dict, spec_idx: dict, cache: dict, side: str) -> dict:
    """Preflight raw + normalized payloads. Generals.exe is not run."""
    assembled = assemble_payloads(name, rec, v25, spec, spec_idx, cache, side)
    native = native_def_index(spec)
    raw = assembled["payloads"]
    missing_end = []
    for path, text in raw.items():
        if object_missing_end(text, path):
            missing_end.append(path)
    pf = preflight_payloads(raw, native_defs=native)
    if pf.get("ok"):
        norm = raw
        pf_norm = pf
    else:
        norm = normalize_payloads(raw)
        pf_norm = preflight_payloads(norm, native_defs=native)
    unloadable = [d for d in assembled["dests"] if d.get("dest") and not d.get("dest_loadable")]
    unproven = [
        d for d in assembled["dests"] if d.get("dest") and d.get("dest_confidence") != "proven" and d.get("dest_loadable")
    ]
    missing = list(assembled["chain"].get("missing_fatal") or [])
    ok = (
        bool(pf_norm.get("ok"))
        and not missing
        and not missing_end
        and not unloadable
        and not unproven
    )
    return {
        "ok": ok,
        "assembled": assembled,
        "preflight": pf,
        "preflight_normalized": pf_norm,
        "missing_end_objects": missing_end,
        "unloadable": unloadable,
        "unproven_dests": unproven,
        "missing_parse_refs": missing[:20],
        "normalized_payloads": norm,
        "generals_exe_run": False,
    }
