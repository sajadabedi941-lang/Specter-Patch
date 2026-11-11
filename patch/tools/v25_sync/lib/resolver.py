"""Dependency resolver and transfer planner (stage 2). No game writes."""
from __future__ import annotations

from collections import Counter, defaultdict

from . import compat
from .rewrite import independent_name, rewrite_text

ACTIONS = (
    "REUSE_NATIVE",
    "IMPORT_UNIQUE",
    "RENAME_AND_REWRITE",
    "RECOVER_FROM_V25",
    "INDEPENDENT_ADD",
    "MANUAL_REBUILD",
    "BLOCKED",
    "CYCLE",
)

HARD_KINDS = {
    "Object",
    "Weapon",
    "ObjectCreationList",
    "FXList",
    "Armor",
    "Locomotor",
    "CommandSet",
    "CommandButton",
    "SpecialPower",
    "Upgrade",
    "ArtFile",
}


class Resolver:
    def __init__(self, engine, rules: dict, archive_index):
        self.eng = engine
        self.rules = rules
        self.archive = archive_index
        self.v25 = engine.inventory_v25()
        self.spec = engine.inventory_specter()
        self.spec_damage = compat.specter_damage_types(self.spec)
        self._action_cache: dict[tuple[str, str], dict] = {}
        self._incoming_buttons: dict[str, list[str]] | None = None
        self._incoming_sets: dict[str, list[str]] | None = None

    def node_id(self, kind: str, name: str) -> str:
        return f"{kind}:{name.lower()}"

    def incoming_buttons(self) -> dict[str, list[str]]:
        if self._incoming_buttons is not None:
            return self._incoming_buttons
        idx: dict[str, list[str]] = defaultdict(list)
        for bname, rec in (self.v25.get("CommandButton") or {}).items():
            for obj in (rec.get("named_refs") or {}).get("Object") or []:
                idx[obj.lower()].append(bname)
        self._incoming_buttons = dict(idx)
        return self._incoming_buttons

    def incoming_commandsets(self) -> dict[str, list[str]]:
        if self._incoming_sets is not None:
            return self._incoming_sets
        idx: dict[str, list[str]] = defaultdict(list)
        for sname, rec in (self.v25.get("CommandSet") or {}).items():
            for btn in (rec.get("named_refs") or {}).get("CommandButton") or []:
                idx[btn.lower()].append(sname)
        self._incoming_sets = dict(idx)
        return self._incoming_sets

    def lookup_v25(self, kind: str, name: str):
        return self.eng.lookup(self.v25, kind, name, "v25")

    def lookup_spec(self, kind: str, name: str):
        return self.eng.lookup(self.spec, kind, name, "spec")

    def resolve_node(self, kind: str, name: str) -> dict:
        key = (kind.lower(), name.lower())
        if key in self._action_cache:
            return self._action_cache[key]
        row = self._resolve_node(kind, name)
        self._action_cache[key] = row
        return row

    def _resolve_node(self, kind: str, name: str) -> dict:
        rec = self.lookup_v25(kind, name)
        spec = self.lookup_spec(kind, name)
        archive_hits = self.archive.find_stem(name) if self.archive else []
        source = rec.get("source") if rec else None

        if kind == "DamageType":
            if name.upper() in self.spec_damage:
                return self._row(kind, name, "REUSE_NATIVE", name, source, "DamageType exists on SPECTER Armor tables.")
            if rec or spec:
                return self._row(kind, name, "INDEPENDENT_ADD", name, source, "Custom DamageType; do not patch SPECTER Armor.")
            return self._row(kind, name, "INDEPENDENT_ADD", name, source, "DamageType not in SPECTER Armor tables.")

        if kind == "BehaviorModule":
            stock = {x.lower() for x in self.rules.get("stock_sage_behaviors") or []}
            manual = {x.lower() for x in self.rules.get("cwc_behavior_manual_rebuild") or []}
            independent = {x.lower() for x in self.rules.get("cwc_behavior_independent_add") or []}
            nl = name.lower()
            if nl in stock:
                return self._row(kind, name, "REUSE_NATIVE", name, source, "Stock SAGE module; keep on the unique Object.")
            if nl in manual:
                return self._row(kind, name, "MANUAL_REBUILD", name, source, "CWC module needs a SPECTER-style rebuild; capability is not dropped.")
            if nl in independent:
                return self._row(kind, name, "INDEPENDENT_ADD", name, source, "Module class is kept on the unique Object; SPECTER core is not patched.")
            return self._row(kind, name, "INDEPENDENT_ADD", name, source, "Unknown behavior kept on the unique Object; not deleted.")

        if kind == "ArtFile":
            stem = name.lower().rsplit(".", 1)[0]
            in_v = stem in self.eng._v25_art
            in_s = stem in self.eng._spec_art
            if stem.startswith("ex") and name.lower().endswith((".tga", ".dds")) or stem.startswith("ex"):
                # EXTireTrack / EXTnkTrack live in vanilla ZH ART, not the SPECTER overlay.
                if not in_v and not archive_hits:
                    return self._row(
                        kind, name, "REUSE_NATIVE", name, source,
                        "Stock ZH EX* texture; expected in base Generals ART, not in the SPECTER overlay or V25 zip listing.",
                    )
            if in_v and in_s:
                return self._row(kind, name, "REUSE_NATIVE", name, source, "Same art stem in SPECTER ART BIG.")
            if in_v:
                return self._row(kind, name, "IMPORT_UNIQUE", name, source, "Art stem present in parsed V25 BIGs.")
            if archive_hits:
                return self._row(
                    kind, name, "RECOVER_FROM_V25", name, archive_hits[0],
                    "Not in parsed extract/BIGs; file exists in the V25 zip.",
                    extra={"archive_paths": archive_hits[:8], "missing_from": "extract_vfs"},
                )
            if in_s:
                return self._row(kind, name, "REUSE_NATIVE", name, source, "Art stem already in SPECTER.")
            return self._row(kind, name, "MANUAL_REBUILD", name, source, "Art stem not in parsed VFS, SPECTER, or V25 zip listing.")

        if kind in (self.rules.get("blocked_kinds") or []):
            if rec and spec:
                return self._row(kind, name, "BLOCKED", name, source, f"{kind} is a protected SPECTER public table; do not import or replace.")
            if rec:
                return self._row(kind, name, "BLOCKED", name, source, f"{kind} import is blocked; SPECTER public {kind} stays.")
            if spec:
                return self._row(kind, name, "REUSE_NATIVE", name, source, f"Use SPECTER {kind}; V25 has no override in VFS.")

        pinned = {x.lower() for x in self.rules.get("pinned_reuse_command_buttons") or []}
        if kind == "CommandButton" and name.lower() in pinned and spec:
            return self._row(kind, name, "REUSE_NATIVE", name, source, "Pinned public command; V25 variant is not copied over SPECTER.")

        if rec is None:
            if spec:
                return self._row(kind, name, "REUSE_NATIVE", name, spec.get("source"), "Defined in SPECTER/stock, not re-defined in V25 VFS.")
            if archive_hits:
                return self._row(
                    kind, name, "RECOVER_FROM_V25", name, archive_hits[0],
                    "Missing from parsed INI VFS; matching filename exists in the V25 archive.",
                    extra={"archive_paths": archive_hits[:8], "missing_from": "extract_vfs"},
                )
            return self._row(
                kind, name, "MANUAL_REBUILD", name, None,
                "Not in parsed V25 VFS, not in SPECTER, and no filename in the V25 zip listing.",
                extra={"missing_from": "archive_and_vfs"},
            )

        if spec is None:
            return self._row(kind, name, "IMPORT_UNIQUE", name, source, "Name is free in SPECTER FINAL; unique-path import.")

        if compat.effective_equal(rec, spec):
            return self._row(kind, name, "REUSE_NATIVE", name, source, "Effective gameplay fingerprint matches SPECTER; reuse, do not copy.")

        planned = independent_name(name)
        return self._row(
            kind, name, "RENAME_AND_REWRITE", planned, source,
            "Same name, different effective behavior. SPECTER original stays; V25 copy becomes "
            f"{planned} with a full reference rewrite.",
        )

    def _row(self, kind, name, action, planned, source, reason, extra=None) -> dict:
        row = {
            "kind": kind,
            "name": name,
            "action": action,
            "planned": planned,
            "source": source,
            "reason": reason,
        }
        if extra:
            row.update(extra)
        return row

    def children_of(self, kind: str, name: str) -> list[tuple[str, str]]:
        rec = self.lookup_v25(kind, name)
        out: list[tuple[str, str]] = []
        if rec is None:
            return out
        for nkind, names in (rec.get("named_refs") or {}).items():
            for n in names:
                out.append((nkind, n))
        for a in rec.get("art_refs") or []:
            out.append(("ArtFile", a))
        if kind == "Weapon":
            for dt in rec.get("damage_types") or []:
                out.append(("DamageType", dt))
        for b in rec.get("behaviors") or []:
            out.append(("BehaviorModule", b))
        if kind == "Object":
            for btn in self.incoming_buttons().get(name.lower(), []):
                out.append(("CommandButton", btn))
        # Do not walk factory CommandSets: that would pull every other buildable unit.
        return out

    def walk(self, kind: str, name: str, seen: set | None = None, depth: int = 0) -> list[dict]:
        if seen is None:
            seen = set()
        nid = self.node_id(kind, name)
        if nid in seen:
            return [self._row(kind, name, "CYCLE", name, None, "Cyclic reference; node already visited.")]
        if depth > 16:
            return [self._row(kind, name, "CYCLE", name, None, "Depth cap; possible cycle.")]
        seen.add(nid)
        node = self.resolve_node(kind, name)
        rows = [node]
        for ck, cn in self.children_of(kind, name):
            rows.extend(self.walk(ck, cn, seen, depth + 1))
        return rows

    def uniqueness(self, rows: list[dict]) -> list[dict]:
        seen = set()
        out = []
        for r in rows:
            k = (r["kind"], r["name"].lower(), r["action"])
            if k in seen:
                continue
            seen.add(k)
            out.append(r)
        return out

    def readiness(self, rows: list[dict]) -> str:
        actions = {r["action"] for r in rows if r["action"] != "CYCLE"}
        if "BLOCKED" in actions:
            return "blocked"
        if "MANUAL_REBUILD" in actions or "INDEPENDENT_ADD" in actions:
            # Independent behavior modules on an otherwise unique object are expected.
            hard_manual = [
                r
                for r in rows
                if r["action"] in ("MANUAL_REBUILD", "INDEPENDENT_ADD")
                and r["kind"] in HARD_KINDS
            ]
            # DamageType INDEPENDENT_ADD is a targeting gap vs SPECTER units.
            dmg = [r for r in rows if r["kind"] == "DamageType" and r["action"] == "INDEPENDENT_ADD"]
            cwc_manual = [r for r in rows if r["kind"] == "BehaviorModule" and r["action"] == "MANUAL_REBUILD"]
            if hard_manual or dmg or cwc_manual:
                return "manual_rebuild"
            # leftover INDEPENDENT_ADD on BehaviorModule stock-unknown is still transferable as unique INI
        if "RENAME_AND_REWRITE" in actions or "RECOVER_FROM_V25" in actions:
            return "auto_fixable"
        if actions <= {"REUSE_NATIVE", "IMPORT_UNIQUE", "CYCLE", "INDEPENDENT_ADD"}:
            if "IMPORT_UNIQUE" in actions or "REUSE_NATIVE" in actions:
                # Ready only if the object itself is importable and no hard gaps.
                obj = next((r for r in rows if r["kind"] == "Object"), None)
                if obj and obj["action"] in ("IMPORT_UNIQUE", "RENAME_AND_REWRITE", "REUSE_NATIVE"):
                    if obj["action"] == "REUSE_NATIVE":
                        return "reuse_only"
                    return "ready_transfer"
        return "auto_fixable"

    def plan_object(self, name: str) -> dict:
        rec = self.lookup_v25("Object", name)
        found = rec is not None
        meta = self.eng.object_meta(rec) if rec else {}
        rows = self.uniqueness(self.walk("Object", name)) if found else [
            self._row("Object", name, "MANUAL_REBUILD", name, None, "Object not in V25 VFS.")
        ]
        weapons = []
        for r in rows:
            if r["kind"] == "Weapon" and r["action"] != "CYCLE":
                wrec = self.lookup_v25("Weapon", r["name"])
                if wrec:
                    wrec = dict(wrec)
                    wrec["name"] = r["name"]
                    weapons.append(wrec)
        notes = []
        if rec:
            notes = compat.compatibility_notes(rec, weapons, self.spec_damage, self.rules)
            side = meta.get("side")
            if side in (self.rules.get("blocked_object_sides") or []):
                rows.insert(
                    0,
                    self._row("Object", name, "BLOCKED", name, rec.get("source"), "ZH general / boss side is not imported as a SPECTER faction."),
                )
        rewrite = {r["name"]: r["planned"] for r in rows if r["action"] == "RENAME_AND_REWRITE"}
        sample_body = None
        if rec and rewrite:
            sample_body = {
                "note": "Preview only; not written to disk.",
                "rewritten_head": rewrite_text(rec.get("body") or "", rewrite)[:800],
            }
        ready = self.readiness(rows)
        counts = Counter(r["action"] for r in rows)
        buttons = self.incoming_buttons().get(name.lower(), [])
        dest_side = self.eng.faction_map["side_to_specter"].get(meta.get("side") or "", meta.get("side"))
        planned_obj = next((r["planned"] for r in rows if r["kind"] == "Object"), name)
        return {
            "object": name,
            "found_in_vfs": found,
            "source": rec.get("source") if rec else None,
            "meta": meta,
            "readiness": ready,
            "dest_ini": (
                f"Data\\INI\\Object\\SilentDeath\\{dest_side or 'Unmapped'}\\{planned_obj}.ini"
                if found
                else None
            ),
            "build_buttons": buttons,
            "build_commandsets": [
                cs for b in buttons for cs in self.incoming_commandsets().get(b.lower(), [])
            ],
            "action_counts": dict(counts),
            "deps": rows,
            "rewrite_map": rewrite,
            "compatibility_notes": notes,
            "rewritten_preview": sample_body,
            "applies_to_game": False,
        }

    def plan_all(self, object_names: list[str] | None = None) -> dict:
        names = object_names or sorted((self.v25.get("Object") or {}).keys(), key=str.lower)
        plans = []
        ready = auto = manual = blocked = reuse = 0
        for n in names:
            p = self.plan_object(n)
            plans.append(p)
            r = p["readiness"]
            if r == "ready_transfer":
                ready += 1
            elif r == "auto_fixable":
                auto += 1
            elif r == "blocked":
                blocked += 1
            elif r == "reuse_only":
                reuse += 1
            else:
                manual += 1
        return {
            "objects_planned": len(plans),
            "ready_transfer": ready,
            "auto_fixable": auto,
            "manual_rebuild": manual,
            "blocked": blocked,
            "reuse_only": reuse,
            "note": "ready_transfer is not unique_v25. reuse_only objects already exist in SPECTER with matching behavior.",
            "plans": plans,
        }

    def batch_plan(self, all_plans: list[dict]) -> dict:
        groups: dict[str, list[dict]] = defaultdict(list)
        for p in all_plans:
            meta = p.get("meta") or {}
            groups[f"bucket:{meta.get('bucket') or 'other'}"].append(p)
            groups[f"side:{meta.get('side') or 'none'}"].append(p)
        out = {}
        for key, members in sorted(groups.items()):
            dep_counts: dict[tuple, int] = Counter()
            dep_rows: dict[tuple, dict] = {}
            for p in members:
                seen = set()
                for d in p.get("deps") or []:
                    k = (d["kind"], d["name"].lower())
                    if k in seen:
                        continue
                    seen.add(k)
                    dep_counts[k] += 1
                    dep_rows[k] = d
            shared = []
            for k, c in dep_counts.items():
                if c >= 2:
                    d = dep_rows[k]
                    shared.append({"kind": d["kind"], "name": d["name"], "action": d["action"], "used_by": c})
            data_files = sorted(
                {
                    (p.get("source") or "")
                    for p in members
                    if p.get("source")
                }
            )
            art_files = sorted(
                {
                    path
                    for p in members
                    for d in p.get("deps") or []
                    if d["kind"] == "ArtFile"
                    for path in (d.get("archive_paths") or ([d["source"]] if d.get("source") else []))
                    if path
                }
            )
            conflicts = [p["object"] for p in members if p["readiness"] in ("blocked", "manual_rebuild")]
            rebuild = [p["object"] for p in members if p["readiness"] == "manual_rebuild"]
            # Order: recover/import art+weapons before objects.
            order = (
                [p["object"] for p in members if p["readiness"] == "ready_transfer"]
                + [p["object"] for p in members if p["readiness"] == "auto_fixable"]
                + [p["object"] for p in members if p["readiness"] == "manual_rebuild"]
                + [p["object"] for p in members if p["readiness"] == "blocked"]
            )
            out[key] = {
                "count": len(members),
                "objects": [p["object"] for p in members],
                "readiness": dict(Counter(p["readiness"] for p in members)),
                "shared_deps": shared[:80],
                "data_files": data_files[:80],
                "art_files": art_files[:80],
                "conflicts": conflicts[:80],
                "rebuild": rebuild[:80],
                "transfer_order": order[:200],
                "revert": {
                    "method": "delete unique-path SilentDeath INI/ART added by the batch; never restore by rewriting SPECTER public INI",
                    "paths_pattern": [
                        "Data\\INI\\Object\\SilentDeath\\**",
                        "Data\\INI\\Weapon\\SilentDeath\\**",
                        "Data\\INI\\CommandSet_ZZZZ_SilentDeath_*.ini",
                    ],
                },
            }
        return out
