"""V25 → SPECTER inventory, dependency walk, collision map, dry-run planner.

Stage 1 never writes SPECTER BIGs or game INI. Apply is refused.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import archive, big, ini

KINDOF_RE = re.compile(r"KindOf\s*=\s*(.+)", re.I)
SIDE_RE = re.compile(r"Side\s*=\s*(\S+)", re.I)
DISPLAY_RE = re.compile(r"DisplayName\s*=\s*(.+)", re.I)

EQUIPMENT_KINDS = {
    "VEHICLE",
    "AIRCRAFT",
    "INFANTRY",
    "STRUCTURE",
    "FS_BASE_DEFENSE",
    "FS_TECHNOLOGY",
    "FS_FACTORY",
    "FS_BARRACKS",
    "FS_WARFACTORY",
    "FS_AIRFIELD",
    "FS_SUPPLY_PAD",
    "FS_POWER",
    "CAN_ATTACK",
    "PROJECTILE",
}

BUCKET_RULES = [
    ("air_defense", ("FS_BASE_DEFENSE", "CAN_ATTACK_AIRBORNE_VEHICLES", "CAN_ATTACK_MISSILES")),
    ("aircraft", ("AIRCRAFT",)),
    ("vehicle", ("VEHICLE", "HUGE_VEHICLE")),
    ("infantry", ("INFANTRY",)),
    ("structure", ("STRUCTURE", "FS_FACTORY", "FS_BARRACKS", "FS_WARFACTORY", "FS_AIRFIELD", "FS_BASE_DEFENSE", "FS_POWER", "FS_TECHNOLOGY", "IMMOBILE")),
    ("projectile", ("PROJECTILE", "SMALL_MISSILE", "BALLISTIC_MISSILE")),
]

HARD_MISSING_KINDS = {
    "Object",
    "Weapon",
    "ObjectCreationList",
    "FXList",
    "Armor",
    "Locomotor",
    "CommandSet",
    "SpecialPower",
    "Upgrade",
}

PATH_SIDE_HINTS = (
    ("americasuperweapon", "America"),
    ("americalaser", "America"),
    ("americaairforce", "America"),
    ("americaparticlecannon", "America"),
    ("america", "America"),
    ("chinainfantry", "China"),
    ("chinatank", "China"),
    ("chinanuke", "China"),
    ("china", "China"),
    ("glatoxin", "GLA"),
    ("glademolition", "GLA"),
    ("glastealth", "GLA"),
    ("gla", "GLA"),
    ("russia", "Russia"),
    ("iraq", "Iraq"),
    ("iran", "Iran"),
    ("israel", "Israel"),
    ("egypt", "Egypt"),
    ("france", "France"),
    ("germany", "Germany"),
    ("india", "India"),
    ("italy", "Italy"),
    ("japan", "Japan"),
    ("pakistan", "Pakistan"),
    ("saudi", "SaudiArabia"),
    ("southkorea", "SouthKorea"),
    ("korea", "SouthKorea"),
    ("sweden", "Sweden"),
    ("syria", "Syria"),
    ("northkorea", "NorthKorea"),
    ("ukrania", "Ukrania"),
    ("ukraine", "Ukraine"),
    ("poland", "Poland"),
    ("serbia", "Serbia"),
    ("algeria", "Algeria"),
    ("turkey", "Turkey"),
    ("britain", "Britain"),
    ("taiwan", "Taiwan"),
    ("civilian", "Civilian"),
)

PROTECTED_KINDS_ALWAYS_REVIEW = {
    "CommandSet",
    "CommandButton",
    "Weapon",
    "Armor",
    "Locomotor",
    "ObjectCreationList",
    "FXList",
    "SpecialPower",
    "PlayerTemplate",
    "Upgrade",
    "Science",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_stage5_install_docs(dest: Path, report: dict) -> None:
    orig = report.get("original_hashes") or {}
    exp = report.get("experimental_hashes") or {}
    loc = report.get("china_build_location") or {}
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "INSTALL.txt").write_text(
        "\n".join(
            [
                "SPECTER FINAL — Silent Death V25 experimental pack (stage 5)",
                "ChinaCSSA1 + ChinaHQ11. Independent copy. Original install is not modified by the packer.",
                "",
                "Generals.exe was NOT run. This is not an in-game test report.",
                "",
                "Install (replace the two BIGs in the SPECTER FINAL folder):",
                "  1. Quit the game.",
                "  2. Backup the originals:",
                "       copy _SPEC_DATA_ONE.big _SPEC_DATA_ONE.big.bak",
                "       copy _SPEC_ART_TWO.big _SPEC_ART_TWO.big.bak",
                "  3. Copy these files from this ZIP over the SPECTER FINAL folder:",
                "       _SPEC_DATA_ONE.big",
                "       _SPEC_ART_TWO.big",
                "  4. Do not add loose Data\\INI files. This pack is BIG-only.",
                "",
                "Where to build (China / PLA war factory):",
                f"  Building Object: {loc.get('object')}",
                f"  CommandSet: {loc.get('commandset')}",
                f"  SD25_ChinaCSSA1 UNIT_BUILD slot {loc.get('ChinaCSSA1_slot')}",
                f"  SD25_ChinaHQ11 UNIT_BUILD slot {loc.get('ChinaHQ11_slot')}",
                "",
                "Expected original SHA256 (before replace):",
                f"  _SPEC_DATA_ONE.big  {orig.get('_SPEC_DATA_ONE.big')}",
                f"  _SPEC_ART_TWO.big   {orig.get('_SPEC_ART_TWO.big')}",
                "",
                "This pack SHA256:",
                f"  _SPEC_DATA_ONE.big  {exp.get('_SPEC_DATA_ONE.big')}",
                f"  _SPEC_ART_TWO.big   {exp.get('_SPEC_ART_TWO.big')}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (dest / "REVERT.txt").write_text(
        "\n".join(
            [
                "Revert experimental pack — restore SPECTER FINAL originals.",
                "",
                "  1. Quit the game.",
                "  2. Restore the backups made during INSTALL:",
                "       copy /Y _SPEC_DATA_ONE.big.bak _SPEC_DATA_ONE.big",
                "       copy /Y _SPEC_ART_TWO.big.bak  _SPEC_ART_TWO.big",
                "  3. If backups are missing, recopy SPECTER FINAL from the unmodified install.",
                "  4. Original hashes that must match after revert:",
                f"       _SPEC_DATA_ONE.big  {orig.get('_SPEC_DATA_ONE.big')}",
                f"       _SPEC_ART_TWO.big   {orig.get('_SPEC_ART_TWO.big')}",
                "  5. Delete any leftover experimental ZIP files. There are no loose INI to remove.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    sums = []
    for name in ("_SPEC_DATA_ONE.big", "_SPEC_ART_TWO.big", "INSTALL.txt", "REVERT.txt"):
        p = dest / name
        if p.is_file():
            sums.append(f"{sha256_file(p)}  {name}")
    (dest / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")


def tehran_now() -> str:
    # Report times in Asia/Tehran (UTC+3:30).
    from datetime import timedelta

    t = datetime.now(timezone.utc) + timedelta(hours=3, minutes=30)
    return t.strftime("%Y-%m-%d %H:%M Asia/Tehran")


class Engine:
    def __init__(self, root: Path):
        self.root = root
        self.tool = root / "patch" / "tools" / "v25_sync"
        self.data = self.tool / "data"
        self.reports = self.tool / "reports"
        self.reports.mkdir(parents=True, exist_ok=True)
        self.cache = Path("/tmp/v25_sync_cache")
        self.cache.mkdir(parents=True, exist_ok=True)
        self.protected = json.loads((self.data / "protected_paths.json").read_text())
        self.faction_map = json.loads((self.data / "faction_map.json").read_text())
        self.v25_src = Path("/tmp/v25_src")
        self.v25_extract = Path("/tmp/v25_extract")
        self.ss1 = Path("/tmp/ss1/SPECTER FINAL (GeneralsMode.com)")
        self._v25: dict | None = None
        self._spec: dict | None = None
        self._v25_art: set[str] = set()
        self._spec_art: set[str] = set()
        self._v25_ini_files: dict[str, str] = {}
        self._spec_ini_files: dict[str, str] = {}
        self._lookup_cache: dict[tuple[str, str, str], dict | None] = {}
        self._walk_cache: dict[tuple[str, str], dict] = {}

    def search_dirs(self) -> list[Path]:
        dirs = [
            self.v25_src,
            Path("/tmp/v25_src"),
            self.root / "patch",
            self.root,
            Path("/tmp"),
        ]
        return dirs

    def find_volumes(self) -> dict[int, Path]:
        return archive.find_volumes(self.search_dirs())

    def health_report(self) -> dict:
        vols = self.find_volumes()
        health = archive.volume_health(vols)
        staged = None
        test = None
        listing_tail = ""
        if health["complete_for_7z"]:
            staged = archive.stage_volumes(vols, self.v25_src)
            test = archive.test_archive(staged)
            listing = archive.list_archive(staged)
            listing_tail = "\n".join(listing.splitlines()[-25:])
        specter = self.specter_baseline()
        report = {
            "generated_at_utc": utc_now(),
            "generated_at_tehran": tehran_now(),
            "volumes": {k: v for k, v in health.items() if k != "names"},
            "volume_count": health["count"],
            "expected_158_complete": health["complete_for_7z"],
            "missing_expected": health["missing_expected"],
            "extra_volumes": health["extra_volumes"],
            "z62_present": 62 in vols,
            "archive_test": test,
            "listing_tail": listing_tail,
            "specter_baseline": specter,
            "stage1_writes_game_bigs": False,
        }
        (self.reports / "ARCHIVE_HEALTH.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        md = self._health_md(report, vols)
        (self.reports / "ARCHIVE_HEALTH.md").write_text(md, encoding="utf-8")
        return report

    def _health_md(self, report: dict, vols: dict[int, Path]) -> str:
        lines = [
            "# V25 archive health",
            "",
            f"- Generated: {report['generated_at_tehran']}",
            f"- Volumes found: **{report['volume_count']}** (expected zip + z01–z157 = **158**)",
            f"- Complete for 7z: **{report['expected_158_complete']}**",
            f"- z62 present: **{report['z62_present']}**",
            f"- Extra volumes: {report['extra_volumes'] or 'none'}",
            f"- Missing expected: {report['missing_expected'] or 'none'}",
            "",
        ]
        if report.get("archive_test"):
            t = report["archive_test"]
            lines += [
                "## 7z test",
                "",
                f"- ok: **{t['ok']}**",
                f"- returncode: {t['returncode']}",
                "",
                "```",
                t.get("tail") or "",
                "```",
                "",
            ]
        lines += ["## SPECTER FINAL baseline (read-only)", ""]
        sb = report["specter_baseline"]
        for k, v in sb.items():
            lines.append(f"- `{k}`: `{v}`")
        lines += ["", "Original SPECTER BIGs are not modified by this tool in stage 1.", ""]
        return "\n".join(lines)

    def specter_baseline(self) -> dict:
        out = {"folder": str(self.ss1), "present": self.ss1.is_dir()}
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_TWO.big",
            "_SPEC_ART_ONE.big",
        ):
            p = self.ss1 / name
            if p.is_file():
                out[name] = {
                    "bytes": p.stat().st_size,
                    "sha256": sha256_file(p),
                }
            else:
                out[name] = "not in SPECTER FINAL overlay folder"
        loose_cs = self.ss1 / "Data" / "INI" / "CommandSet.ini"
        loose_cb = self.ss1 / "Data" / "INI" / "CommandButton.ini"
        out["loose_CommandSet.ini"] = loose_cs.is_file()
        out["loose_CommandButton.ini"] = loose_cb.is_file()
        return out

    def v25_root(self) -> Path:
        hits = list(self.v25_extract.glob("**/00LSF0118.big"))
        if hits:
            return hits[0].parent
        return self.v25_extract

    def ensure_extract(self) -> Path:
        root = self.v25_root()
        if (root / "00LSF0118.big").is_file() and (root / "Data" / "INI").is_dir():
            return root
        vols = self.find_volumes()
        zip_path = archive.stage_volumes(vols, self.v25_src)
        archive.extract(zip_path, self.v25_extract)
        return self.v25_root()

    def _parse_big_ini(self, path: Path) -> tuple[dict[str, dict], set[str], dict[str, str]]:
        layers: dict[str, dict] = {}
        art: set[str] = set()
        ini_files: dict[str, str] = {}

        def want(name: str) -> bool:
            return big.nkey(name).endswith(".ini")

        for name, blob in big.iter_big(path, want):
            nk = big.nkey(name)
            if nk.endswith(".w3d") or nk.endswith(".tga") or nk.endswith(".dds"):
                art.add(big.stem_lower(name))
            if blob is None or not nk.endswith(".ini"):
                continue
            ini_files[nk] = f"{path.name}:{name}"
            parsed = ini.parse_ini_text(blob.decode("latin1", errors="replace"), f"{path.name}:{name}")
            for kind, defs in parsed.items():
                bucket = layers.setdefault(kind, {})
                bucket.update(defs)
        return layers, art, ini_files

    def _parse_loose_ini(self, folder: Path, label: str) -> tuple[dict[str, dict], dict[str, str]]:
        layers: dict[str, dict] = {}
        ini_files: dict[str, str] = {}
        if not folder.is_dir():
            return layers, ini_files
        for p in sorted(folder.rglob("*.ini")):
            rel = str(p.relative_to(folder.parent.parent) if "INI" in p.parts else p)
            key = "data\\ini\\" + str(p.relative_to(folder)).replace("/", "\\").lower()
            ini_files[key] = f"{label}:{p}"
            parsed = ini.parse_file(p, f"{label}:{p}")
            for kind, defs in parsed.items():
                bucket = layers.setdefault(kind, {})
                bucket.update(defs)
        return layers, ini_files

    def inventory_v25(self) -> dict:
        if self._v25 is not None:
            return self._v25
        root = self.ensure_extract()
        layers = []
        art: set[str] = set()
        ini_files: dict[str, str] = {}

        # SAGE alphabetical BIG order, then loose Data last-win.
        bigs = sorted(
            [p for p in root.glob("*.big") if p.is_file()],
            key=lambda p: p.name.lower(),
        )
        for bp in bigs:
            parsed, a, files = self._parse_big_ini(bp)
            layers.append(parsed)
            art |= a
            ini_files.update(files)

        loose_ini = root / "Data" / "INI"
        parsed, files = self._parse_loose_ini(loose_ini, "loose")
        layers.append(parsed)
        ini_files.update(files)

        merged = ini.merge_vfs(*layers)
        self._v25 = merged
        self._v25_art = art
        self._v25_ini_files = ini_files
        return merged

    def inventory_specter(self) -> dict:
        if self._spec is not None:
            return self._spec
        if not self.ss1.is_dir():
            raise FileNotFoundError(f"SPECTER FINAL not found at {self.ss1}")
        layers = []
        art: set[str] = set()
        ini_files: dict[str, str] = {}
        for name in ("_SPEC_DATA_ONE.big", "_SPEC_ART_ONE.big", "_SPEC_ART_TWO.big"):
            p = self.ss1 / name
            if not p.is_file():
                continue
            parsed, a, files = self._parse_big_ini(p)
            layers.append(parsed)
            art |= a
            ini_files.update(files)
        loose_ini = self.ss1 / "Data" / "INI"
        parsed, files = self._parse_loose_ini(loose_ini, "specter-loose")
        layers.append(parsed)
        ini_files.update(files)
        merged = ini.merge_vfs(*layers)
        self._spec = merged
        self._spec_art = art
        self._spec_ini_files = ini_files
        return merged

    def _side_from_source(self, source: str | None) -> str | None:
        if not source:
            return None
        blob = source.replace("\\", "/").lower()
        for hint, side in PATH_SIDE_HINTS:
            if hint in blob:
                return side
        return None

    def object_meta(self, rec: dict) -> dict:
        kinds: set[str] = set()
        side = None
        display = None
        extra_flags: set[str] = set()
        for k, v in rec.get("keys") or []:
            kl = k.strip().lower()
            if kl == "kindof":
                kinds.update(t.upper() for t in v.split() if t.strip())
            elif kl == "side":
                side = v.split()[0] if v.strip() else side
            elif kl == "displayname":
                display = v.strip()
            elif kl in ("antiair", "canattackairbornevehicles") or "anti_air" in kl:
                extra_flags.add("CAN_ATTACK_AIRBORNE_VEHICLES")
            elif "antimissile" in kl.replace("_", "") or "anti_missile" in kl:
                extra_flags.add("CAN_ATTACK_MISSILES")
        kinds |= extra_flags
        if not side:
            side = self._side_from_source(rec.get("source"))
        # Air defense before generic structure: FS_BASE_DEFENSE + attack flags.
        bucket = "other"
        if kinds.intersection(("CAN_ATTACK_AIRBORNE_VEHICLES", "CAN_ATTACK_MISSILES")) or (
            "FS_BASE_DEFENSE" in kinds and "CAN_ATTACK" in kinds
        ):
            bucket = "air_defense"
        else:
            for name, flags in BUCKET_RULES:
                if kinds.intersection(flags):
                    bucket = name
                    break
        if "CAN_ATTACK" in kinds and bucket == "other":
            bucket = "combat"
        if not kinds and bucket == "other":
            name = (rec.get("name") or "").lower()
            src = (rec.get("source") or "").lower()
            if any(x in name or x in src for x in ("radar", "sam", "s400", "s300", "hq9", "patriot", "thaad", "irondome", "pantsir")):
                bucket = "air_defense"
            elif any(x in src for x in ("vehicle", "tank")):
                bucket = "vehicle"
            elif "air" in src or "jet" in name or "heli" in name:
                bucket = "aircraft"
            elif "infantry" in src:
                bucket = "infantry"
        specter_side = self.faction_map["side_to_specter"].get(side or "")
        return {
            "kindof": sorted(kinds),
            "side": side,
            "specter_side": specter_side,
            "display": display,
            "bucket": bucket,
            "is_equipment": bool(kinds.intersection(EQUIPMENT_KINDS)) or bucket not in ("other",),
        }

    def lookup(self, vfs: dict, kind: str, name: str, tag: str) -> dict | None:
        key = (tag, kind.lower(), name.lower())
        if key in self._lookup_cache:
            return self._lookup_cache[key]
        bucket = vfs.get(kind) or {}
        rec = bucket.get(name)
        if rec is None:
            rec = next((v for k, v in bucket.items() if k.lower() == name.lower()), None)
        if rec is None:
            for alias in ini.KIND_ALIASES.get(kind) or ():
                abucket = vfs.get(alias) or {}
                rec = abucket.get(name) or next(
                    (v for k, v in abucket.items() if k.lower() == name.lower()), None
                )
                if rec is not None:
                    break
        self._lookup_cache[key] = rec
        return rec

    def walk_deps(self, kind: str, name: str, vfs: dict, depth: int = 0, seen: set | None = None) -> dict:
        cache_key = (kind.lower(), name.lower())
        if depth == 0 and cache_key in self._walk_cache:
            return self._walk_cache[cache_key]
        if seen is None:
            seen = set()
        key = (kind.lower(), name.lower())
        if key in seen or depth > 12:
            return {"kind": kind, "name": name, "cycle_or_deep": True}
        seen.add(key)
        rec = self.lookup(vfs, kind, name, "v25")
        if rec is None:
            node = {"kind": kind, "name": name, "missing": True}
            if depth == 0:
                self._walk_cache[cache_key] = node
            return node
        children = []
        # Existence-only kinds: do not treat Armor damage tables / portraits as child defs.
        if kind not in ("Armor", "MappedImage", "AudioEvent", "Locomotor", "ParticleSystem"):
            for nkind, names in (rec.get("named_refs") or {}).items():
                if nkind in ("Armor", "MappedImage", "AudioEvent"):
                    for n in names:
                        child = self.walk_deps(nkind, n, vfs, depth + 1, seen)
                        children.append(child)
                    continue
                for n in names:
                    children.append(self.walk_deps(nkind, n, vfs, depth + 1, seen))
        node = {
            "kind": kind,
            "name": name,
            "source": rec.get("source"),
            "art": rec.get("art_refs") or [],
            "children": children,
        }
        if depth == 0:
            self._walk_cache[cache_key] = node
        return node

    def flatten_missing(self, node: dict, out: list | None = None) -> list:
        if out is None:
            out = []
        if node.get("missing"):
            out.append(f"{node['kind']}:{node['name']}")
        for c in node.get("children") or []:
            self.flatten_missing(c, out)
        return out

    def flatten_names(self, node: dict, out: dict | None = None) -> dict:
        if out is None:
            out = defaultdict(set)
        if not node.get("missing"):
            out[node["kind"]].add(node["name"])
        for c in node.get("children") or []:
            self.flatten_names(c, out)
        return out

    def classify_name(self, kind: str, name: str, v25: dict, spec: dict) -> str:
        vrec = self.lookup(v25, kind, name, "v25")
        srec = self.lookup(spec, kind, name, "spec")
        if vrec is None:
            return "specter_only"
        if srec is None:
            return "unique_v25"
        # Shared name. Compare a stable fingerprint of body without comments.
        vh = hashlib.sha256((vrec.get("body") or "").encode("utf-8", errors="replace")).hexdigest()
        sh = hashlib.sha256((srec.get("body") or "").encode("utf-8", errors="replace")).hexdigest()
        if vh == sh:
            return "shared_identical"
        return "collision_rename"

    def planned_name(self, kind: str, name: str, status: str) -> str:
        if status == "collision_rename":
            return f"SD25_{name}"
        return name

    def dry_run(self) -> dict:
        v25 = self.inventory_v25()
        spec = self.inventory_specter()
        objects = v25.get("Object") or {}
        spec_objects = spec.get("Object") or {}

        mapping = []
        collisions = Counter()
        buckets = Counter()
        sides = Counter()
        missing_total = Counter()
        impact = []
        incomplete = []
        unique_ok = 0
        rename_needed = 0
        reuse_ok = 0

        protected_hits = []

        for name, rec in sorted(objects.items(), key=lambda kv: kv[0].lower()):
            meta = self.object_meta(rec)
            buckets[meta["bucket"]] += 1
            if meta["side"]:
                sides[meta["side"]] += 1
            status = self.classify_name("Object", name, v25, spec)
            collisions[status] += 1
            tree = self.walk_deps("Object", name, v25)
            missing = self.flatten_missing(tree)
            hard_missing = [m for m in missing if m.split(":")[0] in HARD_MISSING_KINDS]
            deps = self.flatten_names(tree)
            for m in missing:
                missing_total[m.split(":")[0]] += 1
            body_l = (rec.get("body") or "").lower()
            independent = []
            for marker, label in (
                ("riderchangecontain", "RiderChangeContain (CWC) — add independently"),
                ("deploystyleaiupdate", "DeployStyleAIUpdate — add independently"),
                ("oclspecialpower", "OCLSpecialPower — add independently"),
                ("special_cia_intelligence", "SPECIAL_CIA_INTELLIGENCE — SPECTER-style rebuild"),
                ("weaponbonustype", "WeaponBonusType — unique INI, do not patch core"),
            ):
                if marker in body_l:
                    independent.append(label)
            new_name = self.planned_name("Object", name, status)
            dep_plan = {}
            obj_protected = []
            for kind, names in deps.items():
                rows = []
                for n in sorted(names, key=str.lower):
                    st = self.classify_name(kind, n, v25, spec)
                    planned = self.planned_name(kind, n, st)
                    rows.append({"name": n, "status": st, "planned": planned})
                    if kind in PROTECTED_KINDS_ALWAYS_REVIEW and st == "collision_rename":
                        hit = {"object": name, "kind": kind, "name": n, "planned": planned}
                        obj_protected.append(hit)
                        protected_hits.append(hit)
                dep_plan[kind] = rows
            art_status = []
            for a in rec.get("art_refs") or []:
                stem = a.lower().rsplit(".", 1)[0]
                in_v = stem in self._v25_art
                in_s = stem in self._spec_art
                art_status.append(
                    {
                        "ref": a,
                        "in_v25_art": in_v,
                        "in_specter_art": in_s,
                        "action": (
                            "reuse_specter"
                            if in_s and in_v
                            else "copy_unique_art"
                            if in_v
                            else "missing_art"
                        ),
                    }
                )
            specter_side = self.faction_map["side_to_specter"].get(meta["side"] or "")
            dest_ini = (
                f"Data\\INI\\Object\\SilentDeath\\{specter_side or meta['side'] or 'Unmapped'}\\"
                f"{new_name}.ini"
            )
            row = {
                "name": name,
                "planned_name": new_name,
                "status": status,
                "side": meta["side"],
                "specter_side": specter_side,
                "display": meta["display"],
                "bucket": meta["bucket"],
                "kindof": meta["kindof"],
                "source": rec.get("source"),
                "dest_ini": dest_ini,
                "dest_art_big": "_SPEC_ART_TWO.big (future apply only; not written in stage 1)",
                "dest_data_big": "_SPEC_DATA_ONE.big unique path only (future apply; not written)",
                "missing_refs": missing,
                "hard_missing_refs": hard_missing,
                "independent_add": independent,
                "deps": dep_plan,
                "art": art_status,
                "protected_dep_collisions": obj_protected,
            }
            mapping.append(row)
            if status == "unique_v25":
                unique_ok += 1
            elif status == "collision_rename":
                rename_needed += 1
                impact.append(
                    {
                        "object": name,
                        "risk": "name collision with SPECTER Object; future apply must rename to "
                        f"{new_name} and rewrite every ref. SPECTER original {name} stays.",
                    }
                )
            elif status == "shared_identical":
                reuse_ok += 1
            if hard_missing:
                incomplete.append({"object": name, "missing": hard_missing})

        # CommandSet / Weapon summary
        kind_summary = {}
        for kind in (
            "Object",
            "Weapon",
            "CommandSet",
            "CommandButton",
            "Armor",
            "Locomotor",
            "ObjectCreationList",
            "FXList",
            "SpecialPower",
            "Upgrade",
            "ParticleSystem",
            "PlayerTemplate",
        ):
            vnames = set((v25.get(kind) or {}).keys())
            snames = set((spec.get(kind) or {}).keys())
            kind_summary[kind] = {
                "v25": len(vnames),
                "specter": len(snames),
                "unique_v25": len(vnames - snames),
                "shared": len(vnames & snames),
                "collision_rename": sum(
                    1
                    for n in (vnames & snames)
                    if self.classify_name(kind, n, v25, spec) == "collision_rename"
                ),
                "shared_identical": sum(
                    1
                    for n in (vnames & snames)
                    if self.classify_name(kind, n, v25, spec) == "shared_identical"
                ),
            }

        compat = {
            "generated_at_utc": utc_now(),
            "generated_at_tehran": tehran_now(),
            "v25_root": str(self.v25_root()),
            "specter_root": str(self.ss1),
            "objects_v25": len(objects),
            "objects_specter": len(spec_objects),
            "object_status": dict(collisions),
            "buckets": dict(buckets),
            "sides": dict(sides),
            "kind_summary": kind_summary,
            "missing_ref_kinds": dict(missing_total),
            "incomplete_objects": len(incomplete),
            "incomplete_hard_deps": len(incomplete),
            "soft_image_or_audio_gaps_are_separate": True,
            "protected_dep_collisions": len(protected_hits),
            "art_stems_v25": len(self._v25_art),
            "art_stems_specter": len(self._spec_art),
            "rules": {
                "never_overwrite_protected_ini": self.protected["ini_paths"],
                "never_touch_specter_bigs_stage1": True,
                "collision_rename_prefix": "SD25_",
                "unique_object_dest": "Data\\INI\\Object\\SilentDeath\\{Side}\\",
                "commandset_future": self.faction_map["specter_commandset_pattern"],
                "apply_enabled": False,
            },
        }

        manifest = {
            "stage": 1,
            "mode": "dry-run",
            "applies_to_game": False,
            "generated_at_tehran": tehran_now(),
            "equipment_count": len(mapping),
            "unique_ok": unique_ok,
            "rename_needed": rename_needed,
            "reuse_identical": reuse_ok,
            "incomplete": len(incomplete),
            "note": "No Object, Weapon, CommandSet, CommandButton, or ART was imported into SPECTER.",
        }

        dry = {
            "generated_at_tehran": tehran_now(),
            "game_bigs_modified": False,
            "generals_exe_run": False,
            "archive_complete": True,
            "objects_scanned": len(mapping),
            "missing_refs": dict(missing_total),
            "collisions": dict(collisions),
            "incomplete_sample": incomplete[:80],
            "impact_sample": impact[:80],
            "impact_count": len(impact),
            "protected_hits_sample": protected_hits[:80],
            "protected_hits": len(protected_hits),
            "validation": {
                "missing_refs_scanned": True,
                "name_collisions_scanned": True,
                "incomplete_deps_scanned": True,
                "object_weapon_ocl_fx_scanned": True,
                "output_big_not_written": True,
                "before_after_diff": "no game files changed; diff is empty by design",
                "specter_behavior_impact_if_applied_later": (
                    "Colliding names would be renamed to SD25_* so original SPECTER defs stay. "
                    "Public CommandSet.ini / CommandButton.ini / Weapon.ini / Armor.ini are blocked. "
                    "Future apply must use unique-path INI only."
                ),
            },
        }

        mapping_out = {
            "generated_at_tehran": tehran_now(),
            "count": len(mapping),
            "items": mapping,
        }
        batches: dict[str, list[str]] = defaultdict(list)
        for row in mapping:
            batches[f"bucket:{row['bucket']}"].append(row["name"])
            batches[f"side:{row.get('side') or 'none'}"].append(row["name"])
            batches[f"status:{row['status']}"].append(row["name"])
        batch_index = {
            "generated_at_tehran": tehran_now(),
            "note": "Select one or more keys to form a future reversible transfer pack. Stage 1 does not write that pack into SPECTER.",
            "keys": {k: {"count": len(v), "objects": v} for k, v in sorted(batches.items())},
        }
        (self.reports / "BATCH_INDEX.json").write_text(
            json.dumps(batch_index) + "\n", encoding="utf-8"
        )

        (self.reports / "COMPATIBILITY.json").write_text(
            json.dumps(compat, indent=2) + "\n", encoding="utf-8"
        )
        (self.reports / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        (self.reports / "MAPPING.json").write_text(
            json.dumps(mapping_out) + "\n", encoding="utf-8"
        )
        (self.reports / "DRY_RUN.json").write_text(
            json.dumps(dry, indent=2) + "\n", encoding="utf-8"
        )
        self._write_compat_md(compat)
        self._write_dry_md(dry, compat)
        self._write_mapping_md(mapping, compat)
        return {"compat": compat, "dry": dry, "manifest": manifest, "mapping_count": len(mapping)}

    def _write_compat_md(self, compat: dict) -> None:
        lines = [
            "# V25 ↔ SPECTER compatibility (stage 1, no import)",
            "",
            f"- Generated: {compat['generated_at_tehran']}",
            f"- V25 Objects: **{compat['objects_v25']}**",
            f"- SPECTER Objects: **{compat['objects_specter']}**",
            f"- Object status: `{compat['object_status']}`",
            f"- Incomplete dependency trees: **{compat['incomplete_objects']}**",
            f"- Protected-kind collisions (Weapon/CommandSet/Armor/…): **{compat['protected_dep_collisions']}**",
            f"- V25 ART stems: {compat['art_stems_v25']}",
            f"- SPECTER ART stems: {compat['art_stems_specter']}",
            "",
            "## Buckets",
            "",
        ]
        for k, v in sorted(compat["buckets"].items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"- {k}: {v}")
        lines += ["", "## Sides (V25 Object Side=)", ""]
        for k, v in sorted(compat["sides"].items(), key=lambda kv: (-kv[1], kv[0])):
            spec = self.faction_map["side_to_specter"].get(k, "UNMAPPED — independent add required")
            lines.append(f"- {k}: {v} → SPECTER `{spec}`")
        lines += ["", "## Named-definition overlap", "", "| Kind | V25 | SPECTER | unique V25 | shared | identical | rename |", "|---|---:|---:|---:|---:|---:|---:|"]
        for kind, row in compat["kind_summary"].items():
            lines.append(
                f"| {kind} | {row['v25']} | {row['specter']} | {row['unique_v25']} | {row['shared']} | "
                f"{row['shared_identical']} | {row['collision_rename']} |"
            )
        lines += [
            "",
            "## Engine rules (future apply — not executed)",
            "",
            "- Existing SPECTER Objects are never edited.",
            "- Public `CommandSet.ini` / `CommandButton.ini` / `Weapon.ini` / `Armor.ini` / `Locomotor.ini` / `PlayerTemplate.ini` are blocked.",
            "- Colliding names become `SD25_<name>` with full reference rewrite.",
            "- Unique V25 names keep their name and go to `Data\\INI\\Object\\SilentDeath\\<Side>\\`.",
            "- If SPECTER lacks a system (CWC rider, deploy AI, unique bomb), the object is flagged `independent_add`, never dropped.",
            "- New air defense must keep AntiAir/AntiMissile KindOf and weapons that already match SPECTER aircraft/missile Armor/DamageType, or add companion DamageType **only in unique INI**.",
            "- Stage 1 writes **no** game BIG.",
            "",
        ]
        (self.reports / "COMPATIBILITY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_dry_md(self, dry: dict, compat: dict) -> None:
        lines = [
            "# Dry run — all V25 equipment (no SPECTER writes)",
            "",
            f"- Generated: {dry['generated_at_tehran']}",
            f"- Objects scanned: **{dry['objects_scanned']}**",
            f"- Game BIGs modified: **{dry['game_bigs_modified']}**",
            f"- Generals.exe run: **{dry['generals_exe_run']}**",
            f"- Collisions: `{dry['collisions']}`",
            f"- Incomplete trees: **{compat['incomplete_objects']}**",
            f"- Later-apply impact rows: **{dry['impact_count']}** (rename-only; originals kept)",
            "",
            "## Validation checklist",
            "",
        ]
        for k, v in dry["validation"].items():
            lines.append(f"- {k}: {v}")
        lines += ["", "## Missing-ref kinds", ""]
        for k, v in sorted(dry["missing_refs"].items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"- {k}: {v}")
        lines += [
            "",
            "## Sample incomplete objects (first 40)",
            "",
        ]
        for row in dry["incomplete_sample"][:40]:
            lines.append(f"- `{row['object']}`: {', '.join(row['missing'][:8])}")
        lines += [
            "",
            "## Sample SPECTER-behavior notes if apply were enabled later",
            "",
        ]
        for row in dry["impact_sample"][:40]:
            lines.append(f"- `{row['object']}`: {row['risk']}")
        lines += [
            "",
            "Dry run made **zero** changes to `_SPEC_DATA_ONE.big`, `_SPEC_ART_TWO.big`, or loose SPECTER INI.",
            "",
        ]
        (self.reports / "DRY_RUN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_mapping_md(self, mapping: list, compat: dict) -> None:
        lines = [
            "# Mapping index (all V25 Objects)",
            "",
            "Full per-object records: `MAPPING.json`.",
            "",
            f"Count: **{len(mapping)}**. Status from dry-run: `{compat['object_status']}`.",
            "",
            "| Object | planned | status | side | bucket | dest INI | missing |",
            "|---|---|---|---|---|---|---|",
        ]
        for row in mapping:
            miss = len(row.get("missing_refs") or [])
            lines.append(
                f"| `{row['name']}` | `{row['planned_name']}` | {row['status']} | "
                f"{row.get('side') or ''} | {row['bucket']} | `{row['dest_ini']}` | {miss} |"
            )
        (self.reports / "MAPPING.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def refuse_apply(self) -> None:
        raise SystemExit(
            "SS1 compat engine: apply is disabled. No SPECTER FINAL BIG is written. "
            "No equipment is imported in this stage."
        )

    def run_compat_infra(self) -> dict:
        """Discover SS1 load rules, catalog all V25 objects, preflight emit paths.

        Does not pack BIGs, does not import units, does not run Generals.exe.
        """
        import gzip

        from . import catalog as catalog_mod
        from . import cwc
        from . import ss1_layout
        from .preflight import native_def_index, preflight_payloads

        orig_data = self.ss1 / "_SPEC_DATA_ONE.big"
        orig_art = self.ss1 / "_SPEC_ART_TWO.big"
        before = {
            "_SPEC_DATA_ONE.big": sha256_file(orig_data) if orig_data.is_file() else None,
            "_SPEC_ART_TWO.big": sha256_file(orig_art) if orig_art.is_file() else None,
        }
        layout = ss1_layout.discover(orig_data)
        (self.reports / "SS1_LAYOUT.json").write_text(
            json.dumps(layout, indent=2) + "\n", encoding="utf-8"
        )
        (self.reports / "SS1_LAYOUT.md").write_text(ss1_layout.layout_markdown(layout), encoding="utf-8")

        rules = json.loads((self.data / "compatibility_rules.json").read_text(encoding="utf-8"))
        recipes = cwc.load_recipes(self.data)
        v25 = self.inventory_v25()
        spec = self.inventory_specter()
        cat = catalog_mod.catalog_objects(v25, spec, rules, recipes)
        counts = cat["counts"]
        (self.reports / "V25_CATALOG.json.gz").write_bytes(
            gzip.compress(json.dumps(cat, default=str).encode("utf-8"), compresslevel=6)
        )

        emit_samples = {
            ss1_layout.emit_path("Weapon", "SD25_x"): b"Weapon SD25_x\nEnd\n",
            ss1_layout.emit_path("Object", "SD25_ChinaCSSA1", "China"): (
                b"Object SD25_ChinaCSSA1\n  ArmorSet\n    Armor = SD25_TankArmor\n  End\nEnd\n"
            ),
            r"Data\INI\Weapon\SilentDeath\SD25_Weapons.ini": b"Weapon SD25_Bad\nEnd\n",
            r"Data\INI\MappedImages\SilentDeath\x.ini": b"MappedImage X\nEnd\n",
        }
        native = native_def_index(spec)
        native.setdefault("armor", set()).add("sd25_tankarmor")
        sample_pf = preflight_payloads(emit_samples, native_defs=native, layout=layout)

        after = {
            "_SPEC_DATA_ONE.big": sha256_file(orig_data) if orig_data.is_file() else None,
            "_SPEC_ART_TWO.big": sha256_file(orig_art) if orig_art.is_file() else None,
        }
        report = {
            "mode": "ss1-compat-infra",
            "generated_at_tehran": tehran_now(),
            "game_bigs_modified": False,
            "original_hashes_unchanged": before == after,
            "original_hashes": after,
            "generals_exe_run": False,
            "loose_ini_written": False,
            "equipment_imported": False,
            "ss1_layout": {
                "root_ini": layout["root_ini_count"],
                "object_recursive": layout["object"]["recursive"],
                "weapon_dir_recursive": layout["weapon_dir"]["recursive"],
                "weapon_nested_files": layout["weapon_dir"]["nested_files"],
                "mappedimage_subdirs": layout["mappedimages"]["subdirs"],
            },
            "catalog_counts": counts,
            "object_count": cat["object_count"],
            "preflight_sample_rejects_nested_weapon": any(
                e.get("code") == "unloadable_path" and "Weapon\\SilentDeath" in str(e.get("path"))
                for e in sample_pf.get("errors") or []
            ),
            "preflight_sample_rejects_mappedimages_silentdeath": any(
                e.get("code") == "unloadable_path" and "MappedImages\\SilentDeath" in str(e.get("path"))
                for e in sample_pf.get("errors") or []
            ),
        }
        (self.reports / "ENGINE_AUDIT.json").write_text(
            json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
        )
        (self.reports / "ENGINE_AUDIT.md").write_text(
            catalog_mod.engine_audit_markdown(report, layout, cat), encoding="utf-8"
        )
        (self.reports / "V25_CATALOG.md").write_text(
            catalog_mod.catalog_markdown(cat, tehran_now()), encoding="utf-8"
        )
        return report

    def run_stage4(self, focus: tuple[str, ...] = ("ChinaCSSA1", "ChinaHQ11")) -> dict:
        from . import archive as archive_mod
        from . import cwc, stage3_reports, stage4_reports
        from .archive_index import ArchiveIndex
        from .art_index import ArtIndex
        from .resolver import Resolver

        vols = self.find_volumes()
        zip_path = archive_mod.stage_volumes(vols, self.v25_src)
        aidx = ArchiveIndex(zip_path, self.cache)
        art = ArtIndex(zip_path, self.cache, extract_root=None)
        rules = json.loads((self.data / "compatibility_rules.json").read_text(encoding="utf-8"))
        recipes = cwc.load_recipes(self.data)
        resolver = Resolver(self, rules, aidx, art_index=art, cwc_recipes=recipes)
        focus_ok = []
        for name in focus:
            plan = resolver.plan_object(name)
            safe = name.replace("/", "_")
            (self.reports / f"TRANSFER_PLAN_{safe}.json").write_text(
                json.dumps(plan, indent=2, default=str) + "\n", encoding="utf-8"
            )
            stage4_reports.write_object_plan_md(plan, self.reports / f"TRANSFER_PLAN_{safe}.md")
            art_rows = [d for d in plan.get("deps") or [] if d["kind"] == "ArtFile"]
            (self.reports / f"ART_CHAIN_{safe}.json").write_text(
                json.dumps(
                    {
                        "object": name,
                        "art_status": plan.get("art_status"),
                        "data_status": plan.get("data_status"),
                        "files": [
                            {
                                "name": d["name"],
                                "action": d["action"],
                                "source": d.get("source"),
                                "archive_paths": d.get("archive_paths"),
                                "art_locations": d.get("art_locations"),
                                "w3d_textures": d.get("w3d_textures"),
                                "w3d_anims": d.get("w3d_anims"),
                                "found_in": d.get("found_in"),
                            }
                            for d in art_rows
                        ],
                    },
                    indent=2,
                    default=str,
                )
                + "\n",
                encoding="utf-8",
            )
            proof = plan.get("deploy_proof") or {}
            (self.reports / f"DATA_REBUILD_{safe}.json").write_text(
                json.dumps(
                    {
                        "object": name,
                        "data_status": plan.get("data_status"),
                        "unique_data_files": plan.get("unique_data_files"),
                        "public_ini_leaks": plan.get("public_ini_leaks"),
                        "independent_clones": [
                            {k: v for k, v in c.items() if k != "preview"}
                            for c in (plan.get("independent_clones") or [])
                        ],
                        "deploy_proof": {
                            "use_deploy_style": proof.get("use_deploy_style"),
                            "use_deployed_weaponset": proof.get("use_deployed_weaponset"),
                            "summary": proof.get("summary"),
                            "proven": proof.get("proven"),
                            "limitations": proof.get("limitations"),
                            "fail_reasons": proof.get("fail_reasons"),
                            "skip_refs": proof.get("skip_refs"),
                        },
                    },
                    indent=2,
                    default=str,
                )
                + "\n",
                encoding="utf-8",
            )
            focus_ok.append(
                {
                    "object": name,
                    "found": plan["found_in_vfs"],
                    "readiness": plan["readiness"],
                    "data_status": plan.get("data_status"),
                    "art_status": plan.get("art_status"),
                    "use_deploy_style": bool(proof.get("use_deploy_style")),
                    "public_ini_leaks": plan.get("public_ini_leaks") or [],
                    "cwc_modules": [c.get("module") for c in (plan.get("cwc") or [])],
                }
            )
        (self.reports / "CWC_BEHAVIORS.json").write_text(
            json.dumps({"generated_at_tehran": tehran_now(), "recipes": recipes, "focus": focus_ok}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        cwc_md = [
            "# CWC behaviors discovered in V25 (SPECTER-safe rebuild)",
            "",
            f"- Generated: {tehran_now()}",
            "",
            "SPECTER runs stock Generals.exe. CWC.exe-only modules are never copied as-is.",
            "Capabilities are kept via independent unique-path INI, not by rewriting SPECTER core.",
            "",
        ]
        for mod, recipe in (recipes.get("modules") or {}).items():
            reb = recipe.get("rebuild") or {}
            cwc_md += [
                f"## `{mod}`",
                "",
                f"- Origin: {recipe.get('origin')}",
                f"- SPECTER exe: {recipe.get('specter_exe')}",
                f"- {recipe.get('what_it_does')}",
                f"- Rebuild: **{reb.get('action')}** — keep `{reb.get('keep_capability')}`",
                "",
            ]
            for step in reb.get("specter_safe") or []:
                cwc_md.append(f"- {step}")
            cwc_md.append("")
        pack = recipes.get("pack_unpack") or {}
        cwc_md += ["## Pack / Unpack (not always DeployStyleAIUpdate)", "", pack.get("comment") or "", ""]
        for step in pack.get("specter_rebuild") or []:
            cwc_md.append(f"- {step}")
        cwc_md.append("")
        (self.reports / "CWC_BEHAVIORS.md").write_text("\n".join(cwc_md) + "\n", encoding="utf-8")
        (self.reports / "MANIFEST.json").write_text(
            json.dumps(
                {
                    "stage": 4,
                    "mode": "data-rebuild-plan",
                    "applies_to_game": False,
                    "generals_exe_run": False,
                    "generated_at_tehran": tehran_now(),
                    "focus": focus_ok,
                    "nested_bigs": art.nested_bigs_indexed,
                    "art_stems": len(art.stems),
                    "note": "No Object, Weapon, CommandSet, CommandButton, or ART was imported into SPECTER.",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        # Keep stage-3 summary beside stage-4 so previous CI keys still parse.
        stage3_reports.write_stage3_summary(focus_ok, {"note": "regenerated during stage 4"}, self.reports / "STAGE3_SUMMARY.json", self.reports / "STAGE3_SUMMARY.md")
        stage4_reports.write_stage4_summary(
            focus_ok,
            {"selftest": "python3 patch/tools/v25_sync/v25_sync.py selftest", "generals_exe_run": False},
            self.reports / "STAGE4_SUMMARY.json",
            self.reports / "STAGE4_SUMMARY.md",
        )
        return {
            "mode": "data-rebuild",
            "game_bigs_modified": False,
            "generals_exe_run": False,
            "nested_bigs": art.nested_bigs_indexed,
            "art_stems": len(art.stems),
            "focus": focus_ok,
            "reports": str(self.reports),
        }

    def run_stage5(self, out_dir: Path | None = None) -> dict:
        from . import archive as archive_mod
        from . import cwc
        from .archive_index import ArchiveIndex
        from .art_index import ArtIndex
        from .pack_sample import SamplePacker
        from .resolver import Resolver

        orig_data = self.ss1 / "_SPEC_DATA_ONE.big"
        orig_art = self.ss1 / "_SPEC_ART_TWO.big"
        before = {
            "_SPEC_DATA_ONE.big": sha256_file(orig_data) if orig_data.is_file() else None,
            "_SPEC_ART_TWO.big": sha256_file(orig_art) if orig_art.is_file() else None,
        }
        vols = self.find_volumes()
        zip_path = archive_mod.stage_volumes(vols, self.v25_src)
        aidx = ArchiveIndex(zip_path, self.cache)
        art = ArtIndex(zip_path, self.cache, extract_root=None)
        rules = json.loads((self.data / "compatibility_rules.json").read_text(encoding="utf-8"))
        recipes = cwc.load_recipes(self.data)
        resolver = Resolver(self, rules, aidx, art_index=art, cwc_recipes=recipes)
        dest = Path(out_dir) if out_dir else Path("/tmp/v25_stage5_pack")
        packer = SamplePacker(self, resolver, art, zip_path, dest)
        report = packer.run()
        after = {
            "_SPEC_DATA_ONE.big": sha256_file(orig_data) if orig_data.is_file() else None,
            "_SPEC_ART_TWO.big": sha256_file(orig_art) if orig_art.is_file() else None,
        }
        report["original_hashes_before"] = before
        report["original_hashes_after"] = after
        report["original_hashes_unchanged"] = before == after
        (self.reports / "STAGE5_PACK.json").write_text(
            json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
        )
        lines = [
            "# Stage 5 — experimental DATA+ART BIG pack (ChinaCSSA1, ChinaHQ11)",
            "",
            f"- Generated: {tehran_now()}",
            f"- Original SPECTER BIGs unchanged: **{report['original_hashes_unchanged']}**",
            f"- Loose INI written: **{report.get('loose_ini_written')}**",
            f"- Generals.exe run: **{report.get('generals_exe_run')}**",
            "",
            "## China build location (extracted from SPECTER Objects, not guessed)",
            "",
        ]
        loc = report.get("china_build_location") or {}
        lines += [
            f"- Building Object: `{loc.get('object')}`",
            f"- CommandSet: `{loc.get('commandset')}`",
            f"- Source: `{loc.get('source')}`",
            f"- ChinaCSSA1 UNIT_BUILD slot: `{loc.get('ChinaCSSA1_slot')}`",
            f"- ChinaHQ11 UNIT_BUILD slot: `{loc.get('ChinaHQ11_slot')}`",
            f"- {loc.get('note')}",
            "",
            "## Experimental BIGs",
            "",
            f"- `{dest / '_SPEC_DATA_ONE.big'}` SHA256 `{report['experimental_hashes']['_SPEC_DATA_ONE.big']}`",
            f"- `{dest / '_SPEC_ART_TWO.big'}` SHA256 `{report['experimental_hashes']['_SPEC_ART_TWO.big']}`",
            "",
            "## Warnings",
            "",
        ]
        for w in report.get("warnings") or ["none"]:
            lines.append(f"- {w}")
        for cap in report.get("capabilities_kept") or []:
            lines.append(f"- kept: {cap}")
        lines += ["", "## Limitations", ""]
        for lim in report.get("limitations") or []:
            lines.append(f"- {lim}")
        lines += ["", "## Added DATA members", ""]
        for n in (report.get("data_big") or {}).get("added_names") or []:
            lines.append(f"- `{n}`")
        lines += ["", "## Added ART members", ""]
        for n in (report.get("art_big") or {}).get("added_names") or []:
            lines.append(f"- `{n}`")
        (self.reports / "STAGE5_PACK.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        write_stage5_install_docs(dest, report)
        (self.reports / "MANIFEST_STAGE5.json").write_text(
            json.dumps(
                {
                    "stage": 5,
                    "mode": "experimental-pack",
                    "applies_to_original_specter": False,
                    "generals_exe_run": False,
                    "generated_at_tehran": tehran_now(),
                    "original_hashes_unchanged": report["original_hashes_unchanged"],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return report

    def run_stage3(self, focus: tuple[str, ...] = ("ChinaCSSA1", "ChinaHQ11")) -> dict:
        from . import archive as archive_mod
        from . import cwc, stage3_reports
        from .archive_index import ArchiveIndex
        from .art_index import ArtIndex
        from .resolver import Resolver

        vols = self.find_volumes()
        zip_path = archive_mod.stage_volumes(vols, self.v25_src)
        aidx = ArchiveIndex(zip_path, self.cache)
        art = ArtIndex(zip_path, self.cache, extract_root=None)
        rules = json.loads((self.data / "compatibility_rules.json").read_text(encoding="utf-8"))
        recipes = cwc.load_recipes(self.data)
        resolver = Resolver(self, rules, aidx, art_index=art, cwc_recipes=recipes)
        focus_ok = []
        for name in focus:
            plan = resolver.plan_object(name)
            safe = name.replace("/", "_")
            (self.reports / f"TRANSFER_PLAN_{safe}.json").write_text(
                json.dumps(plan, indent=2, default=str) + "\n", encoding="utf-8"
            )
            stage3_reports.write_object_plan_md(plan, self.reports / f"TRANSFER_PLAN_{safe}.md")
            art_rows = [d for d in plan.get("deps") or [] if d["kind"] == "ArtFile"]
            (self.reports / f"ART_CHAIN_{safe}.json").write_text(
                json.dumps(
                    {
                        "object": name,
                        "art_status": plan.get("art_status"),
                        "data_status": plan.get("data_status"),
                        "files": [
                            {
                                "name": d["name"],
                                "action": d["action"],
                                "source": d.get("source"),
                                "archive_paths": d.get("archive_paths"),
                                "art_locations": d.get("art_locations"),
                                "w3d_textures": d.get("w3d_textures"),
                                "w3d_anims": d.get("w3d_anims"),
                                "found_in": d.get("found_in"),
                            }
                            for d in art_rows
                        ],
                    },
                    indent=2,
                    default=str,
                )
                + "\n",
                encoding="utf-8",
            )
            focus_ok.append(
                {
                    "object": name,
                    "found": plan["found_in_vfs"],
                    "readiness": plan["readiness"],
                    "data_status": plan.get("data_status"),
                    "art_status": plan.get("art_status"),
                    "cwc_modules": [c.get("module") for c in (plan.get("cwc") or [])],
                }
            )
        (self.reports / "CWC_BEHAVIORS.json").write_text(
            json.dumps({"generated_at_tehran": tehran_now(), "recipes": recipes, "focus": focus_ok}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        cwc_md = [
            "# CWC behaviors discovered in V25 (SPECTER-safe rebuild)",
            "",
            f"- Generated: {tehran_now()}",
            "",
            "SPECTER runs stock Generals.exe. CWC.exe-only modules are never copied as-is.",
            "Capabilities are kept via independent unique-path INI, not by rewriting SPECTER core.",
            "",
        ]
        for mod, recipe in (recipes.get("modules") or {}).items():
            reb = recipe.get("rebuild") or {}
            cwc_md += [
                f"## `{mod}`",
                "",
                f"- Origin: {recipe.get('origin')}",
                f"- SPECTER exe: {recipe.get('specter_exe')}",
                f"- {recipe.get('what_it_does')}",
                f"- Rebuild: **{reb.get('action')}** — keep `{reb.get('keep_capability')}`",
                "",
            ]
            for step in reb.get("specter_safe") or []:
                cwc_md.append(f"- {step}")
            cwc_md.append("")
        pack = recipes.get("pack_unpack") or {}
        cwc_md += ["## Pack / Unpack (not always DeployStyleAIUpdate)", "", pack.get("comment") or "", ""]
        for step in pack.get("specter_rebuild") or []:
            cwc_md.append(f"- {step}")
        cwc_md.append("")
        (self.reports / "CWC_BEHAVIORS.md").write_text("\n".join(cwc_md) + "\n", encoding="utf-8")
        (self.reports / "MANIFEST.json").write_text(
            json.dumps(
                {
                    "stage": 3,
                    "mode": "art-cwc-plan",
                    "applies_to_game": False,
                    "generals_exe_run": False,
                    "generated_at_tehran": tehran_now(),
                    "focus": focus_ok,
                    "nested_bigs": art.nested_bigs_indexed,
                    "art_stems": len(art.stems),
                    "note": "No Object, Weapon, CommandSet, CommandButton, or ART was imported into SPECTER.",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "mode": "art-cwc",
            "game_bigs_modified": False,
            "generals_exe_run": False,
            "nested_bigs": art.nested_bigs_indexed,
            "art_stems": len(art.stems),
            "focus": focus_ok,
            "reports": str(self.reports),
        }

    def run_stage2(self, focus: tuple[str, ...] = ("ChinaCSSA1", "ChinaHQ11"), rerun_dry: bool = True) -> dict:
        from . import archive as archive_mod
        from .archive_index import ArchiveIndex
        from .resolver import Resolver
        from . import stage2_reports

        baseline_path = self.reports / "STAGE1_BASELINE.json"
        if not baseline_path.is_file() and (self.reports / "DRY_RUN.json").is_file():
            baseline_path.write_text((self.reports / "DRY_RUN.json").read_text(encoding="utf-8"), encoding="utf-8")
        stage1_dry = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.is_file() else {}

        if rerun_dry:
            dry_pack = self.dry_run()
            stage2_dry = dry_pack["dry"]
        elif (self.reports / "DRY_RUN.json").is_file():
            stage2_dry = json.loads((self.reports / "DRY_RUN.json").read_text(encoding="utf-8"))
        else:
            stage2_dry = {}

        vols = self.find_volumes()
        zip_path = archive_mod.stage_volumes(vols, self.v25_src)
        aidx = ArchiveIndex(zip_path, self.cache)
        rules = json.loads((self.data / "compatibility_rules.json").read_text(encoding="utf-8"))
        resolver = Resolver(self, rules, aidx)
        result = resolver.plan_all()
        slim = {k: v for k, v in result.items() if k != "plans"}
        stage2_reports.write_summary(result, self.reports, stage1_dry)
        batch = resolver.batch_plan(result["plans"])
        (self.reports / "BATCH_TRANSFER_PLAN.json").write_text(
            json.dumps({"generated_at_tehran": tehran_now(), "groups": batch}, default=str) + "\n",
            encoding="utf-8",
        )
        focus_ok = []
        for name in focus:
            plan = resolver.plan_object(name)
            safe = name.replace("/", "_")
            (self.reports / f"TRANSFER_PLAN_{safe}.json").write_text(
                json.dumps(plan, indent=2, default=str) + "\n", encoding="utf-8"
            )
            stage2_reports.write_object_plan_md(plan, self.reports / f"TRANSFER_PLAN_{safe}.md")
            focus_ok.append({"object": name, "found": plan["found_in_vfs"], "readiness": plan["readiness"]})
        stage2_reports.write_delta_md(stage1_dry, stage2_dry, slim, self.reports / "DRY_RUN_DELTA.md")
        (self.reports / "MANIFEST.json").write_text(
            json.dumps(
                {
                    "stage": 2,
                    "mode": "resolve-dry-run",
                    "applies_to_game": False,
                    "generated_at_tehran": tehran_now(),
                    "ready_transfer": result["ready_transfer"],
                    "auto_fixable": result["auto_fixable"],
                    "manual_rebuild": result["manual_rebuild"],
                    "blocked": result["blocked"],
                    "reuse_only": result["reuse_only"],
                    "objects_planned": result["objects_planned"],
                    "note": "No Object, Weapon, CommandSet, CommandButton, or ART was imported into SPECTER.",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return {
            "mode": "resolve",
            "game_bigs_modified": False,
            "generals_exe_run": False,
            "archive_stems": aidx.file_count,
            "resolver": slim,
            "focus": focus_ok,
            "reports": str(self.reports),
        }
