"""Experimental DATA pack of a small READY group.

Writes only to an independent output directory. Original SPECTER FINAL BIGs are
never opened for write. No loose INI. Generals.exe is not run.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from . import big, catalog
from .pack_sample import dedupe_named_blocks
from .payloads import byte_gate
from .preflight import native_def_index, preflight_payloads
from .ss1_layout import path_is_protected, path_loadable

PREFERRED_READY = (
    "TomahawkMissile",
    "ScudStormMissile",
    "AuroraBomb",
    "PatriotMissile",
)
MAX_GROUP = 4

KIND_FROM_PATH = (
    ("weapon_", "Weapon"),
    ("armor_", "Armor"),
    ("locomotor_", "Locomotor"),
    ("fxlist_", "FXList"),
    ("damagefx_", "DamageFX"),
    ("crate_", "CrateData"),
    ("objectcreationlist_", "ObjectCreationList"),
    ("particlesystem_", "ParticleSystem"),
    ("soundeffects_", "AudioEvent"),
    ("commandbutton_", "CommandButton"),
    ("commandset_", "CommandSet"),
    ("specialpower_", "SpecialPower"),
    ("upgrade_", "Upgrade"),
    ("science_", "Science"),
    ("mappedimages", "MappedImage"),
    (r"object\silentdeath", "Object"),
)


def select_ready_group(
    rows: list[dict],
    limit: int = MAX_GROUP,
    preferred: tuple[str, ...] = PREFERRED_READY,
) -> list[dict]:
    """Only objects that already passed the byte Ready Gate."""
    ready = [r for r in rows if r.get("ready_for_safe_transfer")]
    by_name = {r["object"]: r for r in ready}
    picked: list[dict] = []
    seen: set[str] = set()
    for name in preferred:
        row = by_name.get(name)
        if row and name not in seen and len(picked) < limit:
            picked.append(row)
            seen.add(name)
    for row in ready:
        if row["object"] in seen:
            continue
        if len(picked) >= limit:
            break
        picked.append(row)
        seen.add(row["object"])
    return picked


def merge_payloads(parts: list[dict[str, str]]) -> dict[str, str]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for payloads in parts:
        for path, text in payloads.items():
            buckets[path].append(text)
    out: dict[str, str] = {}
    for path, chunks in buckets.items():
        kind = "Object"
        low = path.replace("/", "\\").lower()
        for token, mapped in KIND_FROM_PATH:
            if token in low:
                kind = mapped
                break
        out[path] = "\n".join(dedupe_named_blocks(kind, chunks)).rstrip() + "\n"
    return out


def assemble_ready_payloads(
    rows: list[dict],
    v25: dict,
    spec: dict,
    spec_idx: dict,
    cache: dict,
) -> dict:
    """Normalized unique-path payloads for READY rows only. Nothing is written."""
    not_ready = [r["object"] for r in rows if not r.get("ready_for_safe_transfer")]
    if not_ready:
        raise ValueError("refusing to pack non-READY objects: " + ", ".join(not_ready[:12]))
    parts: list[dict[str, str]] = []
    objects: list[dict] = []
    for row in rows:
        name = row["object"]
        rec = catalog._lookup_rec(v25, "Object", name)
        if rec is None:
            raise ValueError(f"READY object missing from V25 inventory: {name}")
        side = row.get("side") or "Unmapped"
        gate = byte_gate(name, rec, v25, spec, spec_idx, cache, side)
        if not gate.get("ok"):
            raise ValueError(f"Ready Gate rejected {name}: {gate.get('missing_parse_refs') or gate.get('unloadable')}")
        parts.append(gate["normalized_payloads"])
        objects.append(
            {
                "object": name,
                "planned_name": gate["assembled"].get("planned_object"),
                "dest_ini": gate["assembled"].get("dest_ini"),
                "side": side,
                "needs_normalize": bool(row.get("needs_normalize")),
            }
        )
    merged = merge_payloads(parts)
    for path in merged:
        load = path_loadable(path)
        if not load.get("loaded") or load.get("confidence") != "proven":
            raise ValueError(f"unproven or unloadable dest in pack: {path} {load}")
        if path_is_protected(path):
            raise ValueError(f"protected dest in pack: {path}")
    native = native_def_index(spec)
    pf = preflight_payloads(merged, native_defs=native)
    if not pf.get("ok"):
        raise ValueError("merged READY payloads failed preflight: " + str((pf.get("errors") or [])[:8]))
    return {
        "payloads": merged,
        "objects": objects,
        "preflight_ok": True,
        "generals_exe_run": False,
    }


def write_experimental_data(
    src_big: Path,
    dest_big: Path,
    payloads: dict[str, str],
    protected: set[str],
) -> dict:
    """Copy DATA BIG into an independent dest and append unique-path members.

    `src_big` is opened read-only. `dest_big` must not be the original path.
    """
    src_big = Path(src_big)
    dest_big = Path(dest_big)
    if dest_big.resolve() == src_big.resolve():
        raise ValueError("refusing to write experimental DATA over the original SS1 BIG")
    if dest_big.parent.resolve() == src_big.parent.resolve():
        raise ValueError("refusing to write experimental DATA into the original SPECTER FINAL folder")
    adds = {path: text.encode("latin1", errors="replace") for path, text in payloads.items()}
    info = big.copy_big_with_adds(src_big, dest_big, adds, protected)
    return {
        "source": str(src_big),
        "dest": str(dest_big),
        "added": info.get("added"),
        "added_names": info.get("added_names"),
        "source_bytes_unchanged": True,
        "loose_ini_written": False,
        "generals_exe_run": False,
        **info,
    }
