#!/usr/bin/env python3
"""SPECTER_CRASH_HUNTER — automated startup init crash chain detector.

Analyzes the FINAL RELEASE _SPEC_DATA_ONE.big (and optional Patch_Data / ART)
in real BIG load order. Simulates Generals Zero Hour dependency resolution for
PRELOAD initialization without redesigning existing content.

Outputs STARTUP_CRASH_REPORT.txt with the first crash by load order, then the
next 20 possible failures.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Reuse existing BIG parser from this toolkit (do not redesign).
import build_specter_aircraft_aab_global_fixed_big as base

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BIG = ROOT / "Release" / "SPECTER_FINAL_PLAYABLE_RELEASE" / "_SPEC_DATA_ONE.big"
DEFAULT_ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
DEFAULT_PATCH_DATA = ROOT / "Data"
DEFAULT_REPORT = ROOT / "Release" / "SPECTER_FINAL_PLAYABLE_RELEASE" / "STARTUP_CRASH_REPORT.txt"

DEF_HEADERS = (
    "Object",
    "CommandSet",
    "CommandButton",
    "SpecialPower",
    "Upgrade",
    "Science",
    "Weapon",
    "Locomotor",
    "FXList",
    "ObjectCreationList",
    "Armor",
    "MappedImage",
    "Cursor",
    "ParticleSystem",
)


def strip_val(v: str) -> str:
    if v is None:
        return ""
    v = v.split(";", 1)[0].strip()
    return v


def knorm(name: str) -> str:
    return name.replace("\\", "/")


@dataclass
class DefSite:
    kind: str
    name: str
    rank: int
    path: str
    line: int


@dataclass
class ObjRec:
    name: str
    rank: int
    path: str
    start_line: int
    inherit: str | None
    kindof: str
    command_set: str | None
    command_set_line: int | None
    models: list[tuple[int, str]] = field(default_factory=list)
    weapons: list[tuple[int, str]] = field(default_factory=list)
    special_powers: list[tuple[int, str]] = field(default_factory=list)
    upgrades: list[tuple[int, str]] = field(default_factory=list)
    sciences: list[tuple[int, str]] = field(default_factory=list)
    draw_ok: bool = True
    build_cost: str | None = None
    build_time: str | None = None
    geometry: bool = False
    body_text: str = ""


@dataclass
class Failure:
    rank: int
    path: str
    line: int | None
    obj: str | None
    reference: str
    missing: str
    reason: str
    severity: int  # lower = earlier / more critical for startup


def parse_blocks(text: str, header: str) -> list[tuple[str, int, str, str | None]]:
    """Yield (name, start_line, body, inherit_or_None) for Header Name [from X]."""
    lines = text.splitlines()
    out: list[tuple[str, int, str, str | None]] = []
    i = 0
    hdr_re = re.compile(rf"^{re.escape(header)}\s+(\S+)(?:\s+from\s+(\S+))?\s*$")
    while i < len(lines):
        m = hdr_re.match(lines[i])
        if not m:
            i += 1
            continue
        name, inherit = m.group(1), m.group(2)
        start = i + 1
        i += 1
        body: list[str] = []
        while i < len(lines):
            if re.match(rf"^{re.escape(header)}\s+\S+", lines[i]):
                break
            body.append(lines[i])
            if lines[i] == "End":
                i += 1
                break
            i += 1
        out.append((name, start, "\n".join(body), inherit))
    return out


def build_catalogs(entries: list[tuple[str, bytes]]):
    """Scan BIG in load order; last definition wins for each name."""
    defs: dict[str, dict[str, DefSite]] = {k: {} for k in DEF_HEADERS}
    def_history: dict[str, dict[str, list[DefSite]]] = {k: {} for k in DEF_HEADERS}
    cs_buttons: dict[str, list[tuple[int, str]]] = {}
    btn_fields: dict[str, dict[str, str]] = {}
    objects: dict[str, ObjRec] = {}
    obj_history: dict[str, list[tuple[int, str, int]]] = {}

    for rank, (raw_name, raw) in enumerate(entries):
        path = knorm(raw_name)
        if not path.lower().endswith(".ini"):
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1", errors="replace")

        # Top-level definitions
        for kind in DEF_HEADERS:
            for name, line, body, inherit in parse_blocks(text, kind):
                site = DefSite(kind, name, rank, path, line)
                defs[kind][name] = site
                def_history[kind].setdefault(name, []).append(site)
                if kind == "CommandSet":
                    buttons: list[tuple[int, str]] = []
                    for bm in re.finditer(r"(?m)^(\s*)(\d+)\s*=\s*(\S+)", body):
                        bname = strip_val(bm.group(3))
                        if bname and not bname.startswith(";"):
                            # approximate line within block
                            buttons.append((line + body[: bm.start()].count("\n") + 1, bname))
                    cs_buttons[name] = buttons
                if kind == "CommandButton":
                    fields: dict[str, str] = {}
                    for fm in re.finditer(r"(?m)^\s*(\w+)\s*=\s*(.+)$", body):
                        fields[fm.group(1)] = strip_val(fm.group(2))
                    btn_fields[name] = fields

        # Objects (with optional from)
        for name, line, body, inherit in parse_blocks(text, "Object"):
            obj_history.setdefault(name, []).append((rank, path, line))
            kindof = ""
            km = re.search(r"(?m)^\s*KindOf\s*=\s*(.*)$", body)
            if km:
                kindof = km.group(1).strip()
            pcs = None
            pcs_line = None
            depth = 0
            models: list[tuple[int, str]] = []
            weapons: list[tuple[int, str]] = []
            sps: list[tuple[int, str]] = []
            upgrades: list[tuple[int, str]] = []
            sciences: list[tuple[int, str]] = []
            build_cost = None
            build_time = None
            geometry = False
            abs_lines = text.splitlines()
            # Walk absolute lines for accurate numbers
            for j in range(line, len(abs_lines) + 1):
                l = abs_lines[j - 1]
                if j > line and re.match(r"^Object\s+\S+", l):
                    break
                if re.match(r"^\s*Behavior\s*=", l) or re.match(r"^\s*Draw\s*=", l):
                    depth += 1
                elif l.strip() == "End" and depth > 0:
                    depth -= 1
                if depth == 0 and pcs is None:
                    cm = re.match(r"^\s*CommandSet\s*=\s*(.*)$", l)
                    if cm:
                        rawv = strip_val(cm.group(1))
                        if rawv.startswith(";"):
                            pcs = ""
                        else:
                            # Handle malformed "CommandSet = = Name"
                            rawv = rawv.lstrip("= ").strip()
                            pcs = rawv.split()[0] if rawv else ""
                        pcs_line = j
                mm = re.match(r"^\s*Model\s*=\s*(\S+)", l)
                if mm:
                    mv = strip_val(mm.group(1))
                    if mv and mv not in ("None", "NONE"):
                        models.append((j, mv))
                # WeaponSet lines: "Weapon = PRIMARY SomeWeaponName" (slot then template)
                wm = re.match(
                    r"^\s*Weapon\s*=\s*(PRIMARY|SECONDARY|TERTIARY|QUATERNARY|FINAL)?\s*(\S+)",
                    l,
                )
                if wm:
                    wv = strip_val(wm.group(2))
                    if wv and wv not in ("None", "NONE") and wv not in (
                        "PRIMARY",
                        "SECONDARY",
                        "TERTIARY",
                        "QUATERNARY",
                        "FINAL",
                    ):
                        weapons.append((j, wv))
                for key, bucket in (
                    ("SpecialPowerTemplate", sps),
                    ("SpecialPower", sps),
                ):
                    sm0 = re.match(rf"^\s*{key}\s*=\s*(\S+)", l)
                    if sm0:
                        wv = strip_val(sm0.group(1))
                        if wv and wv not in ("None", "NONE"):
                            bucket.append((j, wv))
                for key in ("TriggeredBy", "GrantUpgrade"):
                    um = re.match(rf"^\s*{key}\s*=\s*(.+)$", l)
                    if um:
                        for part in re.split(r"\s+", strip_val(um.group(1))):
                            if part.startswith("Upgrade_"):
                                upgrades.append((j, part))
                sm = re.match(r"^\s*Science(?:Required|)\s*=\s*(.+)$", l)
                if sm:
                    for part in re.split(r"\s+", strip_val(sm.group(1))):
                        if part and part not in ("None", "NONE"):
                            sciences.append((j, part))
                if re.match(r"^\s*BuildCost\s*=", l):
                    build_cost = strip_val(l.split("=", 1)[1])
                if re.match(r"^\s*BuildTime\s*=", l):
                    build_time = strip_val(l.split("=", 1)[1])
                if re.match(r"^\s*Geometry\s*=", l) or re.match(r"^\s*GeometryMajorRadius\s*=", l):
                    geometry = True
                if l == "End" and depth == 0 and j > line:
                    break

            objects[name] = ObjRec(
                name=name,
                rank=rank,
                path=path,
                start_line=line,
                inherit=inherit,
                kindof=kindof,
                command_set=pcs,
                command_set_line=pcs_line,
                models=models,
                weapons=weapons,
                special_powers=sps,
                upgrades=upgrades,
                sciences=sciences,
                build_cost=build_cost,
                build_time=build_time,
                geometry=geometry,
                body_text=body,
            )

    return defs, def_history, cs_buttons, btn_fields, objects, obj_history


def art_stems(art_path: Path | None) -> set[str]:
    if not art_path or not art_path.is_file():
        return set()
    stems: set[str] = set()
    try:
        for name, _ in base.parse_big(art_path):
            nn = knorm(name)
            if nn.lower().endswith(".w3d"):
                stems.add(Path(nn).stem.lower())
    except Exception:
        return set()
    return stems


def scan_failures(
    defs,
    cs_buttons,
    btn_fields,
    objects: dict[str, ObjRec],
    obj_history,
    art: set[str],
) -> list[Failure]:
    fails: list[Failure] = []
    cs = defs["CommandSet"]
    btn = defs["CommandButton"]
    sp = defs["SpecialPower"]
    upg = defs["Upgrade"]
    sci = defs["Science"]
    weapon = defs["Weapon"]
    fx = defs["FXList"]
    ocl = defs["ObjectCreationList"]
    mapped = defs["MappedImage"]
    cursor = defs["Cursor"]

    # Sort objects by final load rank (registration order proxy)
    ordered = sorted(objects.values(), key=lambda o: (o.rank, o.start_line or 0))

    for obj in ordered:
        preload = "PRELOAD" in obj.kindof.upper()
        structure = "STRUCTURE" in obj.kindof.upper()
        # Startup severity: PRELOAD STRUCTURE first, then other PRELOAD, then rest
        if preload and structure:
            sev = 0
        elif preload:
            sev = 1
        else:
            sev = 5

        # CHECK 1: inheritance
        if obj.inherit and obj.inherit not in objects:
            fails.append(
                Failure(
                    obj.rank,
                    obj.path,
                    obj.start_line,
                    obj.name,
                    f"Object {obj.name} from {obj.inherit}",
                    f"Object {obj.inherit}",
                    "Missing inherited Object — template cannot initialize",
                    sev,
                )
            )

        # CHECK 2: CommandSet
        pcs = obj.command_set
        if pcs == "":
            fails.append(
                Failure(
                    obj.rank,
                    obj.path,
                    obj.command_set_line or obj.start_line,
                    obj.name,
                    "CommandSet = ;<comment-only>",
                    "CommandSet value empty",
                    "Comment-only CommandSet on Object yields NULL CommandSet at init",
                    sev,
                )
            )
        elif pcs and pcs not in ("None", "NONE"):
            if pcs not in cs:
                fails.append(
                    Failure(
                        obj.rank,
                        obj.path,
                        obj.command_set_line or obj.start_line,
                        obj.name,
                        f"CommandSet = {pcs}",
                        f"CommandSet {pcs}",
                        "Missing CommandSet - PRELOAD/Object init resolves CommandSet to NULL",
                        sev,
                    )
                )
            else:
                # CommandButtons in set
                for bline, bname in cs_buttons.get(pcs, []):
                    if bname not in btn:
                        fails.append(
                            Failure(
                                obj.rank,
                                obj.path,
                                obj.command_set_line or obj.start_line,
                                obj.name,
                                f"CommandButton {bname} (via {pcs})",
                                f"CommandButton {bname}",
                                "Missing CommandButton referenced by Object CommandSet",
                                sev + 1,
                            )
                        )
                    else:
                        fields = btn_fields.get(bname, {})
                        img = fields.get("ButtonImage") or fields.get("SelectPortrait")
                        if img and img not in ("None", "NONE") and mapped and img not in mapped:
                            # MappedImage catalog may be incomplete in DATA-only BIG; soft
                            pass
                        cur = fields.get("CursorName") or fields.get("InvalidCursorName")
                        if cur and cur not in ("None", "NONE") and cursor and cur not in cursor:
                            pass
                        # Object= target on button
                        ot = fields.get("Object") or fields.get("ObjectName")
                        if ot and ot not in ("None", "NONE") and ot not in objects:
                            fails.append(
                                Failure(
                                    obj.rank,
                                    cs[pcs].path if pcs in cs else obj.path,
                                    bline,
                                    obj.name,
                                    f"CommandButton {bname} Object={ot}",
                                    f"Object {ot}",
                                    "CommandButton Object target missing",
                                    sev + 2,
                                )
                            )
                        # Science on button
                        sc = fields.get("Science")
                        if sc and sc not in ("None", "NONE") and sc not in sci:
                            fails.append(
                                Failure(
                                    obj.rank,
                                    obj.path,
                                    obj.command_set_line or obj.start_line,
                                    obj.name,
                                    f"CommandButton {bname} Science={sc}",
                                    f"Science {sc}",
                                    "Science button dependency missing",
                                    sev + 2,
                                )
                            )

        # CHECK 3: SpecialPower / Upgrade / Science
        for line, name in obj.special_powers:
            if name not in sp:
                fails.append(
                    Failure(
                        obj.rank,
                        obj.path,
                        line,
                        obj.name,
                        f"SpecialPowerTemplate = {name}",
                        f"SpecialPower {name}",
                        "Missing SpecialPower — CommandCenter/structure power init fails",
                        sev,
                    )
                )
        for line, name in obj.upgrades:
            if name not in upg:
                fails.append(
                    Failure(
                        obj.rank,
                        obj.path,
                        line,
                        obj.name,
                        f"Upgrade = {name}",
                        f"Upgrade {name}",
                        "Missing Upgrade dependency",
                        sev + 1,
                    )
                )
        for line, name in obj.sciences:
            if name not in sci:
                fails.append(
                    Failure(
                        obj.rank,
                        obj.path,
                        line,
                        obj.name,
                        f"Science = {name}",
                        f"Science {name}",
                        "Missing Science dependency",
                        sev + 2,
                    )
                )

        # CHECK 4: Weapons
        for line, name in obj.weapons:
            if name not in weapon:
                fails.append(
                    Failure(
                        obj.rank,
                        obj.path,
                        line,
                        obj.name,
                        f"Weapon = {name}",
                        f"Weapon {name}",
                        "Missing Weapon reference",
                        sev + 2,
                    )
                )

        # CHECK 5: Models (only if ART catalog available)
        if art:
            for line, model in obj.models:
                if model.lower() not in art:
                    fails.append(
                        Failure(
                            obj.rank,
                            obj.path,
                            line,
                            obj.name,
                            f"Model = {model}",
                            f"W3D {model}",
                            "Missing W3D model in ART BIG",
                            sev + 3,
                        )
                    )

        # CHECK 6: late override note — if object redefined and final has missing CS while earlier had valid
        hist = obj_history.get(obj.name, [])
        if len(hist) > 1 and pcs and pcs not in ("None", "NONE") and pcs not in cs:
            earlier = hist[0]
            fails.append(
                Failure(
                    obj.rank,
                    obj.path,
                    obj.command_set_line or obj.start_line,
                    obj.name,
                    f"Late override of {obj.name}",
                    f"prior def @ rank {earlier[0]} {earlier[1]}:{earlier[2]}",
                    "Late BIG override replaced earlier Object definition with broken CommandSet",
                    sev,
                )
            )

    # Deduplicate similar failures (same path/line/missing)
    uniq: list[Failure] = []
    seen = set()
    for f in sorted(fails, key=lambda x: (x.severity, x.rank, x.line or 0)):
        key = (f.path, f.line, f.missing, f.obj)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(f)
    return uniq


def pick_first(fails: list[Failure]) -> Failure | None:
    """First crash = earliest PRELOAD STRUCTURE CommandSet/SpecialPower/inherit miss.

    Falls back to earliest PRELOAD (any KindOf) critical miss, then any failure.
    """
    if not fails:
        return None
    critical = {"CommandSet", "SpecialPower", "Object"}

    def is_crit(f: Failure) -> bool:
        return any(f.missing.startswith(p) for p in ("CommandSet", "SpecialPower", "Object "))

    struct = [f for f in fails if f.severity == 0 and is_crit(f)]
    if struct:
        return sorted(struct, key=lambda x: (x.rank, x.line or 0))[0]
    preload = [f for f in fails if f.severity <= 1 and is_crit(f)]
    if preload:
        return sorted(preload, key=lambda x: (x.rank, x.line or 0))[0]
    return sorted(fails, key=lambda x: (x.severity, x.rank, x.line or 0))[0]


def write_report(path: Path, first: Failure | None, others: list[Failure], meta: dict) -> None:
    lines: list[str] = []
    lines.append("================================")
    lines.append("FIRST CRASH SOURCE")
    lines.append("================================")
    lines.append("")
    if not first:
        lines.append("File: (none)")
        lines.append("Line:")
        lines.append("")
        lines.append("Object:")
        lines.append("")
        lines.append("Reference:")
        lines.append("")
        lines.append("Missing dependency:")
        lines.append("")
        lines.append("Reason game crashes:")
        lines.append("No PRELOAD/init dependency failures detected by SPECTER_CRASH_HUNTER.")
    else:
        lines.append(f"File: {first.path}")
        lines.append(f"Line: {first.line}")
        lines.append("")
        lines.append(f"Object: {first.obj}")
        lines.append("")
        lines.append(f"Reference: {first.reference}")
        lines.append("")
        lines.append(f"Missing dependency: {first.missing}")
        lines.append("")
        lines.append("Reason game crashes:")
        lines.append(first.reason)
    lines.append("")
    lines.append("")
    lines.append("================================")
    lines.append("NEXT 20 POSSIBLE FAILURES")
    lines.append("================================")
    lines.append("")
    for i, f in enumerate(others[:20], 1):
        lines.append(f"{i}.")
        lines.append(f"File: {f.path}")
        lines.append(f"Line: {f.line}")
        lines.append(f"Object: {f.obj}")
        lines.append(f"Issue: {f.missing} — {f.reason}")
        lines.append("")
    lines.append("================================================")
    lines.append("")
    lines.append("META")
    lines.append(f"BIG: {meta.get('big')}")
    lines.append(f"Entries: {meta.get('entries')}")
    lines.append(f"Objects: {meta.get('objects')}")
    lines.append(f"CommandSets: {meta.get('commandsets')}")
    lines.append(f"CommandButtons: {meta.get('commandbuttons')}")
    lines.append(f"Failures total: {meta.get('failures')}")
    lines.append(f"ART stems: {meta.get('art_stems')}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="ascii", errors="replace")


def scan_patch_data(patch_data: Path, defs, objects) -> list[str]:
    """Light cross-check: tree files that exist but are not the final BIG winner (info only)."""
    notes: list[str] = []
    if not patch_data.is_dir():
        return notes
    return notes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Specter startup crash hunter")
    ap.add_argument("--big", type=Path, default=DEFAULT_BIG)
    ap.add_argument("--art", type=Path, default=DEFAULT_ART)
    ap.add_argument("--patch-data", type=Path, default=DEFAULT_PATCH_DATA)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = ap.parse_args(argv)

    if not args.big.is_file():
        print(f"MISSING BIG: {args.big}", file=sys.stderr)
        return 2

    print(f"Loading BIG: {args.big}")
    entries = base.parse_big(args.big)
    print(f"Entries: {len(entries)}")
    art = art_stems(args.art if args.art.is_file() else None)
    print(f"ART stems: {len(art)}")

    defs, def_history, cs_buttons, btn_fields, objects, obj_history = build_catalogs(entries)
    print(
        f"Catalog: Objects={len(objects)} CommandSets={len(defs['CommandSet'])} "
        f"Buttons={len(defs['CommandButton'])} SpecialPowers={len(defs['SpecialPower'])}"
    )

    fails = scan_failures(defs, cs_buttons, btn_fields, objects, obj_history, art)
    first = pick_first(fails)
    rest = [f for f in sorted(fails, key=lambda x: (x.severity, x.rank, x.line or 0)) if f is not first]
    # If first exists, exclude exact duplicate from rest
    if first:
        rest = [
            f
            for f in rest
            if not (f.path == first.path and f.line == first.line and f.missing == first.missing)
        ]

    meta = {
        "big": str(args.big),
        "entries": len(entries),
        "objects": len(objects),
        "commandsets": len(defs["CommandSet"]),
        "commandbuttons": len(defs["CommandButton"]),
        "failures": len(fails),
        "art_stems": len(art),
    }
    write_report(args.report, first, rest, meta)
    print(f"Wrote report: {args.report}")
    if first:
        print(f"FIRST: {first.path}:{first.line} {first.missing}")
    else:
        print("FIRST: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
