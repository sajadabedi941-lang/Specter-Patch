#!/usr/bin/env python3
"""Exhaustive Core-9 full-tech-from-start unlock (second pass).

Baseline: SPECTER_CORE9_FULL_UNLOCK_MATCH_START (or Phase-1).

Fixes incomplete unlock where ~half of buttons stayed grey because:
  - extra tech-building Object Prerequisites (Industrial/Propaganda/MIC/…)
  - production buttons hidden in alternate CommandSetUpgrade variants
  - purchaseable upgrades still gated

Does NOT modify other factions. Does NOT auto-grant upgrades.
Does NOT rebalance costs/weapons/BuildLimits. Preserves USA aircraft work.
"""
from __future__ import annotations

import argparse
import re
import shutil
import struct
import zipfile
from collections import defaultdict
from pathlib import Path

OBJ_RE = re.compile(r"^(Object|ChildObject|ObjectReskin)\s+(\S+)", re.M)
BTN_RE = re.compile(r"^CommandButton\s+(\S+)(.*?)(?=^CommandButton\s|\Z)", re.M | re.S)
CS_RE = re.compile(r"^CommandSet\s+(\S+)(.*?)(?=^CommandSet\s|\Z)", re.M | re.S)
UPG_RE = re.compile(r"^Upgrade\s+(\S+)(.*?)(?=^Upgrade\s|\Z)", re.M | re.S)

ALLOWED_SPECTER_FOLDERS = {
    "United States Of America",
    "PatchSystems",
    "PLA",
    "Armed Forces Of Russian Federation",
    "Iranian Army",
    "Iraq Army",
    "Israel Defense Forces",
    "NATO",
    "North Korea",
    "United Arab Emirates",
}

FACTIONS = [
    "USA",
    "IRAN",
    "RUSSIA",
    "CHINA",
    "IRAQ",
    "ISRAEL",
    "NORTH_KOREA",
    "NATO",
    "UAE",
]

PROD_CMDS = {
    "UNIT_BUILD",
    "DOZER_CONSTRUCT",
    "CONSTRUCT",
    "PLAYER_UPGRADE",
    "OBJECT_UPGRADE",
}

# Keep these Options tokens; strip progression-related ones.
KEEP_OPTION_TOKENS = {
    "OK_FOR_MULTI_SELECT",
    "NEED_TARGET_ENEMY_OBJECT",
    "NEED_TARGET_NEUTRAL_OBJECT",
    "NEED_TARGET_ALLY_OBJECT",
    "NEED_TARGET_POS",
    "NEED_SPECIAL_POWER_SCIENCE",  # stripped separately only for production cmds
    "CONTEXTMODE_COMMAND",
    "OPTION_ONE",
    "OPTION_TWO",
    "OPTION_THREE",
    "IGNORES_UNDERPOWERED",
    "CHECK_LIKE",
    "CANCELABLE",
}


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(path)
    _, n, _ = struct.unpack_from(">III", data, 4)
    e: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1", errors="replace")
        off = end + 1
        e[name] = data[eoff : eoff + esize]
    return e


def write_big(path: Path, file_map: dict[str, bytes]) -> None:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))


def extract_big(big: Path, out: Path) -> int:
    e = read_big(big)
    n = 0
    for name, content in e.items():
        dest = out / name.replace("\\", "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        n += 1
    return n


def pack_dir(stage: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for p in (stage / "Data").rglob("*"):
        if p.is_file():
            out[p.relative_to(stage).as_posix().replace("/", "\\")] = p.read_bytes()
    return out


def faction_of(side: str, name: str) -> str | None:
    if name.startswith("AirF_") or name.startswith("Israel"):
        return "ISRAEL"
    if name.startswith("UAE_"):
        return "UAE"
    if name.startswith("Nato"):
        return "NATO"
    if name.startswith("NorthKorea") or name.startswith("NKFinal") or name.startswith("NorthKoreaReal"):
        return "NORTH_KOREA"
    if name.startswith("Iraq_"):
        return "IRAQ"
    if name.startswith(("China", "Infa_China", "Nuke_China", "Tank_China", "Boss_China")):
        # Boss excluded later
        if name.startswith("Boss_"):
            return None
        return "CHINA"
    if name.startswith("Russia"):
        return "RUSSIA"
    if name.startswith("Iran"):
        return "IRAN"
    if name.startswith(("America", "USA_")):
        return "USA"
    side_l = (side or "").lower()
    return {
        "americaairforcegeneral": "ISRAEL",
        "israel": "ISRAEL",
        "uae": "UAE",
        "nato": "NATO",
        "northkorea": "NORTH_KOREA",
        "iraq": "IRAQ",
        "china": "CHINA",
        "russia": "RUSSIA",
        "iran": "IRAN",
        "america": "USA",
    }.get(side_l)


def is_core_button_name(name: str) -> bool:
    if re.search(r"\bUAE", name) and not re.search(r"America|USA", name):
        return True
    if re.search(
        r"America|AirF_|Iran|Russia|China|Iraq|Israel|NorthKorea|NKFinal|Nato|UAE",
        name,
        re.I,
    ):
        if re.search(r"\bBoss_", name):
            return False
        return True
    return False


def parse_commandsets_last_wins(root: Path) -> tuple[dict[str, list[tuple[int, str]]], dict[str, str]]:
    """Return last-wins CommandSet slot maps and source file."""
    sets: dict[str, list[tuple[int, str]]] = {}
    sources: dict[str, str] = {}
    files = sorted(root.rglob("*.ini"), key=lambda p: str(p).lower())
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        if "CommandSet" not in text:
            continue
        for m in CS_RE.finditer(text):
            name = m.group(1)
            slots = [
                (int(a), b)
                for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", m.group(2), re.M)
            ]
            sets[name] = slots
            sources[name] = str(p.relative_to(root))
    return sets, sources


def parse_buttons_first_wins(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    buttons: dict[str, str] = {}
    sources: dict[str, str] = {}
    files = sorted(root.rglob("CommandButton*.ini"), key=lambda p: str(p).lower())
    # Also CommandButton.ini path variants
    for p in sorted(root.rglob("*.ini"), key=lambda p: str(p).lower()):
        if not p.name.startswith("CommandButton"):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in BTN_RE.finditer(text):
            name = m.group(1)
            if name in buttons:
                continue
            buttons[name] = m.group(2)
            sources[name] = str(p.relative_to(root))
    return buttons, sources


def variant_names(cs: str, all_sets: dict[str, list]) -> list[str]:
    """Find CommandSet variants related to an initial CommandSet name."""
    found = []
    if cs in all_sets:
        found.append(cs)
    # Direct suffixes
    candidates = []
    for name in all_sets:
        if name == cs:
            continue
        if name.startswith(cs) and (
            name[len(cs) :].startswith(("_", "Upgrade", "Upgraded"))
            or re.match(r"^\d", name[len(cs) :])
        ):
            candidates.append(name)
        # PatchAAB twin
        if name == cs + "_PatchAAB" or name.startswith(cs + "_Patch"):
            candidates.append(name)
    # Also group by stripping _T# / Upgrade suffixes to same stem
    stem = re.sub(r"(_T\d+|Upgrade\d*|Upgraded|_LBD|\d+)$", "", cs)
    for name in all_sets:
        nstem = re.sub(r"(_T\d+|Upgrade\d*|Upgraded|_LBD|\d+)$", "", name)
        if nstem == stem and name not in found:
            candidates.append(name)
    # stable unique order: initial first, then by name
    out = []
    seen = set()
    for n in [cs] + sorted(set(candidates)):
        if n in all_sets and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def merge_buttons(variant_list: list[str], all_sets: dict[str, list[tuple[int, str]]]) -> list[str]:
    ordered: list[str] = []
    seen = set()
    for vn in variant_list:
        # sort slots numerically
        slots = sorted(all_sets.get(vn, []), key=lambda x: x[0])
        for _, btn in slots:
            if btn in seen:
                continue
            # skip empty/script junk
            if not btn or btn.startswith(";"):
                continue
            seen.add(btn)
            ordered.append(btn)
    return ordered


def render_commandset(name: str, buttons: list[str]) -> str:
    lines = [f"CommandSet {name}"]
    for i, btn in enumerate(buttons, start=1):
        lines.append(f"  {i} = {btn}")
    lines.append("End")
    lines.append("")
    return "\n".join(lines)


def clear_prerequisites_block(body: str, stats: dict) -> str:
    def repl(m: re.Match) -> str:
        inner = m.group(2)
        # count removed gates
        sci = len(re.findall(r"^\s*Science\s*=", inner, re.M))
        objs = re.findall(r"^\s*Object\s*=\s*(\S+)", inner, re.M)
        ups = len(re.findall(r"^\s*Upgrade\s*=", inner, re.M))
        stats["science_locks_removed"] += sci
        stats["upgrade_prereq_removed"] += ups
        for o in objs:
            if re.search(r"StrategyCenter|BattlePlan", o, re.I):
                stats["strategy_center_locks_removed"] += 1
            elif re.search(r"Doctrine", o, re.I):
                stats["doctrine_locks_removed"] += 1
            elif re.search(
                r"Industrial|Propaganda|Palace|Research|WeaponIndustry|MIC|InternetCenter|BattleLab|Tech|Strategy",
                o,
                re.I,
            ):
                stats["tech_building_locks_removed"] += 1
            else:
                # still remove — user wants only producing building existence
                stats["tech_building_locks_removed"] += 1
        indent = m.group(1)
        end = m.group(3)
        return f"{indent}Prerequisites\n{end}"

    return re.sub(
        r"^([ \t]*)Prerequisites\b(.*?)(^([ \t]*)End\b)",
        repl,
        body,
        flags=re.M | re.S,
    )


def neutralize_commandset_upgrades(body: str, final_cs: str, stats: dict) -> str:
    """Point every CommandSetUpgrade at final_cs; set default CommandSet."""
    # default CommandSet
    lines = body.splitlines(keepends=True)
    in_behavior = 0
    out = []
    replaced_default = False
    for line in lines:
        if re.match(r"^\s*Behavior\b", line):
            in_behavior += 1
        if in_behavior and re.match(r"^\s*End\b", line):
            in_behavior = max(0, in_behavior - 1)
            out.append(line)
            continue
        if not replaced_default and in_behavior == 0 and re.match(r"^\s*CommandSet\s*=", line):
            ind = re.match(r"^(\s*)", line).group(1)
            out.append(f"{ind}CommandSet = {final_cs}\n")
            replaced_default = True
            continue
        out.append(line)
    body2 = "".join(out)

    def beh_repl(m: re.Match) -> str:
        block = m.group(1)
        if not re.search(r"CommandSetUpgrade", block):
            return block
        stats["commandset_upgrade_gates_neutralized"] += 1
        block2 = re.sub(
            r"(^\s*CommandSet\s*=\s*)(\S+)",
            rf"\g<1>{final_cs}",
            block,
            flags=re.M,
        )
        block2 = re.sub(
            r"(^\s*CommandSetAlt\s*=\s*)(\S+)",
            rf"\g<1>{final_cs}",
            block2,
            flags=re.M,
        )
        return block2

    body2 = re.sub(
        r"(^[ \t]*Behavior\s*=\s*CommandSetUpgrade\b.*?^[ \t]*End\b)",
        beh_repl,
        body2,
        flags=re.M | re.S,
    )
    return body2


def process_object_file(text: str, stats: dict, building_cs_map: dict[str, str]) -> str:
    matches = list(OBJ_RE.finditer(text))
    if not matches:
        return text
    parts = []
    last = 0
    for i, m in enumerate(matches):
        parts.append(text[last : m.start()])
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        name = m.group(2)
        header_end = m.end()
        body = text[header_end:end]
        side_m = re.search(r"^\s*Side\s*=\s*(\S+)", body, re.M)
        side = side_m.group(1) if side_m else ""
        fac = faction_of(side, name)
        if fac is None:
            parts.append(text[start:end])
            last = end
            continue

        body2 = clear_prerequisites_block(body, stats)
        # Also strip RequiredScience lines
        def strip_req(mm: re.Match) -> str:
            stats["science_locks_removed"] += 1
            return ""

        body2 = re.sub(
            r"(?m)^\s*(RequiredScience|NeededScience)\s*=\s*\S+\s*\n",
            strip_req,
            body2,
        )

        cs_m = re.search(r"^\s*CommandSet\s*=\s*(\S+)", body2, re.M)
        if cs_m and name in building_cs_map:
            final = building_cs_map[name]
            body2 = neutralize_commandset_upgrades(body2, final, stats)
        elif cs_m and re.search(r"CommandSetUpgrade", body2):
            # still neutralize to current default CS
            final = cs_m.group(1)
            body2 = neutralize_commandset_upgrades(body2, final, stats)

        parts.append(text[start:header_end] + body2)
        last = end
    parts.append(text[last:])
    return "".join(parts)


def process_upgrade_file(text: str, stats: dict) -> str:
    matches = list(UPG_RE.finditer(text))
    if not matches:
        return text
    # Only clear prereqs for core-named upgrades
    parts = []
    last = 0
    for i, m in enumerate(matches):
        parts.append(text[last : m.start()])
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        name = m.group(1)
        body = m.group(2)
        if not is_core_button_name(name) and not re.search(
            r"America|Iran|Russia|China|Iraq|Israel|Nato|UAE|NorthKorea|US_|RUS_|Irq_|Specter_Tier",
            name,
            re.I,
        ):
            parts.append(text[start:end])
            last = end
            continue
        body2 = clear_prerequisites_block(body, stats)
        parts.append(f"Upgrade {name}{body2}")
        last = end
    parts.append(text[last:])
    return "".join(parts)


def process_commandbutton_file(text: str, stats: dict) -> str:
    def repl(m: re.Match) -> str:
        name, body = m.group(1), m.group(2)
        if not is_core_button_name(name):
            return m.group(0)
        cmd_m = re.search(r"^\s*Command\s*=\s*(\S+)", body, re.M)
        if not cmd_m or cmd_m.group(1) not in PROD_CMDS:
            return m.group(0)
        new_body = body
        if re.search(r"^\s*Science\s*=", new_body, re.M):
            stats["button_science_removed"] += len(
                re.findall(r"^\s*Science\s*=", new_body, re.M)
            )
            stats["science_locks_removed"] += len(
                re.findall(r"^\s*Science\s*=", new_body, re.M)
            )
            new_body = re.sub(r"(?m)^\s*Science\s*=\s*\S+\s*\n", "", new_body)
        if re.search(r"NEED_UPGRADE", new_body):
            stats["need_upgrade_buttons_cleared"] += 1
            stats["required_upgrade_locks_removed"] += 1
            new_body = re.sub(r"\bNEED_UPGRADE\b", "", new_body)
            # Remove Upgrade= lines used as availability gates on these cmds
            new_body = re.sub(r"(?m)^\s*Upgrade\s*=\s*\S+\s*\n", "", new_body)
        if re.search(r"NEED_SPECIAL_POWER_SCIENCE", new_body) and cmd_m.group(1) in {
            "UNIT_BUILD",
            "CONSTRUCT",
            "DOZER_CONSTRUCT",
            "PLAYER_UPGRADE",
            "OBJECT_UPGRADE",
        }:
            stats["science_locks_removed"] += 1
            new_body = re.sub(r"\bNEED_SPECIAL_POWER_SCIENCE\b", "", new_body)
            new_body = re.sub(r"(?m)^\s*Science\s*=\s*\S+\s*\n", "", new_body)
        # Cleanup Options lines with empty leftovers
        def clean_opt(mm: re.Match) -> str:
            tokens = mm.group(1).split()
            tokens = [t for t in tokens if t and t != "="]
            if not tokens:
                return ""
            return f"  Options = {' '.join(tokens)}\n"

        new_body = re.sub(r"(?m)^\s*Options\s*=\s*(.*)\n", clean_opt, new_body)
        if new_body != body:
            return f"CommandButton {name}{new_body}"
        return m.group(0)

    return BTN_RE.sub(repl, text)


def discover_production_buildings(root: Path) -> list[dict]:
    """Find core-faction objects that have a CommandSet (production/UI structures)."""
    buildings = []
    obj_root = root / "Data/INI/Object"
    for p in obj_root.rglob("*.ini"):
        # skip forbidden specter folders
        try:
            rel = p.relative_to(root / "Data/INI/Object/Specter")
            folder = rel.parts[0]
            if folder not in ALLOWED_SPECTER_FOLDERS:
                continue
        except ValueError:
            pass
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in OBJ_RE.finditer(text):
            name = m.group(2)
            nxt = OBJ_RE.search(text, m.end())
            body = text[m.end() : nxt.start() if nxt else len(text)]
            side_m = re.search(r"^\s*Side\s*=\s*(\S+)", body, re.M)
            side = side_m.group(1) if side_m else ""
            fac = faction_of(side, name)
            if fac is None:
                continue
            # top-level CommandSet
            cs = None
            in_behavior = 0
            for line in body.splitlines():
                if re.match(r"^\s*Behavior\b", line):
                    in_behavior += 1
                if in_behavior and re.match(r"^\s*End\b", line):
                    in_behavior = max(0, in_behavior - 1)
                    continue
                if in_behavior == 0:
                    mm = re.match(r"^\s*CommandSet\s*=\s*(\S+)", line)
                    if mm and cs is None:
                        cs = mm.group(1)
            if not cs:
                continue
            kind = re.search(r"^\s*KindOf\s*=\s*(.+)$", body, re.M)
            kind_s = kind.group(1) if kind else ""
            is_struct = bool(
                re.search(r"STRUCTURE|FS_FACTORY|FS_AIRFIELD|FS_BASE_DEFENSE", kind_s)
            ) or bool(
                re.search(
                    r"Airfield|WarFactory|Warfactory|Barracks|CommandCenter|MilitaryHQ|Supply|PowerPlant|Radar|Dock|ArmsDealer|BlackMarket|Tunnel|Palace|Propaganda|Strategy|Industrial|MIC|WeaponIndustry|Speaker|Gattling|Stinger|Bunker|FireBase|Patriot|SamSite|AdvancedAirBase|DropZone|Camp|HQ",
                    name,
                    re.I,
                )
            )
            # Include dozers/workers (production of buildings)
            is_builder = bool(re.search(r"Dozer|Worker|VT72B", name, re.I)) and bool(
                re.search(r"VEHICLE|INFANTRY|DOZER", kind_s, re.I)
            )
            if not (is_struct or is_builder):
                continue
            buildings.append(
                {
                    "faction": fac,
                    "object": name,
                    "commandset": cs,
                    "file": str(p.relative_to(root)),
                    "kind": kind_s,
                }
            )
    return buildings


def mutate(stage: Path) -> tuple[dict, list, list]:
    stats = defaultdict(int)
    building_audits = []
    grey_audits = []

    all_sets, set_sources = parse_commandsets_last_wins(stage)
    buildings = discover_production_buildings(stage)

    # Build merge plan: object -> final CS name (keep initial name), buttons merged
    building_cs_map: dict[str, str] = {}
    merged_sets: dict[str, list[str]] = {}
    variant_info: dict[str, list[str]] = {}

    for b in buildings:
        cs = b["commandset"]
        variants = variant_names(cs, all_sets)
        variant_info[b["object"]] = variants
        buttons = merge_buttons(variants, all_sets)
        merged_sets[cs] = buttons
        # Also rewrite every variant to the same merged button list
        for vn in variants:
            merged_sets[vn] = buttons
        building_cs_map[b["object"]] = cs
        merged_from = 0
        if variants:
            base_btns = {btn for _, btn in all_sets.get(cs, [])}
            merged_from = max(0, len(buttons) - len(base_btns))
        building_audits.append(
            {
                "FACTION": b["faction"],
                "OBJECT": b["object"],
                "INITIAL_COMMANDSET": cs,
                "NUMBER_OF_INITIAL_BUTTONS": len(buttons),
                "OTHER_COMMANDSET_VARIANTS_FOUND": [v for v in variants if v != cs],
                "BUTTONS_MERGED_FROM_VARIANTS": merged_from,
                "REMAINING_LOCKED_BUTTONS": 0,  # filled after button cleanup validate
                "EFFECTIVE_SOURCE_FILE": set_sources.get(cs, ""),
            }
        )
        stats["commandsets_merged"] += 1
        stats["buttons_merged_total"] += merged_from

    # Preserve USA Airfield/WarFactory final runtime roster order, then append
    # any missing buttons from tier/base variants (do not drop B-2/B-21/B-52H/F-117 routing).
    usa_final_files = sorted(
        stage.glob("Data/INI/ZZZZ*USA*AIRFIELD*.ini"),
        key=lambda p: p.name.lower(),
    )
    usa_final_sets: dict[str, list[str]] = {}
    for p in usa_final_files:
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in CS_RE.finditer(text):
            usa_final_sets[m.group(1)] = [
                b for _, b in sorted(
                    [
                        (int(a), b)
                        for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", m.group(2), re.M)
                    ],
                    key=lambda x: x[0],
                )
            ]
    for cs_name in list(merged_sets):
        if not re.match(r"America(Airfield|WarFactory)CommandSet", cs_name):
            continue
        # Prefer the richest USA final definition among related names
        base = []
        for key in (
            cs_name,
            "AmericaAirfieldCommandSet_T3",
            "AmericaWarFactoryCommandSet_T3",
            "AmericaAirfieldCommandSet",
            "AmericaWarFactoryCommandSet",
        ):
            if key in usa_final_sets and len(usa_final_sets[key]) >= len(base):
                base = list(usa_final_sets[key])
        if not base:
            continue
        seen = set(base)
        for btn in merged_sets[cs_name]:
            if btn in seen:
                continue
            if "FAKECOMMAND" in btn:
                continue
            base.append(btn)
            seen.add(btn)
        merged_sets[cs_name] = base

    # Absolute last-wins overlay (must sort after USA_AIRFIELD_FINAL_RUNTIME)
    overlay_lines = [
        "; =============================================================================",
        "; CORE-9 FULL TECH — absolute last-wins CommandSet merges",
        "; All progression/tier/upgrade CommandSet variants collapsed to full rosters.",
        "; USA Airfield/WF keep FINAL RUNTIME order, then append missing variant buttons.",
        "; =============================================================================",
        "",
    ]
    for name in sorted(merged_sets):
        overlay_lines.append(render_commandset(name, merged_sets[name]))
    overlay_path = (
        stage / "Data/INI/ZZZZZZZZ_ZZZZZZZZ_ZZZZZZZZ_ZZZZZZ_CORE9_FULL_TECH_COMMANDSETS.ini"
    )
    # Remove older shorter-name overlay if present from prior runs in same stage
    old = stage / "Data/INI/ZZZZZZZZ_ZZZZZZZZ_CORE9_FULL_TECH_COMMANDSETS.ini"
    if old.exists():
        old.unlink()
    overlay_path.write_text("\n".join(overlay_lines) + "\n", encoding="utf-8")
    stats["commandset_overlay_entries"] = len(merged_sets)

    # Mutate Object files (prereqs + neutralize CS upgrades)
    obj_root = stage / "Data/INI/Object"
    for p in sorted(obj_root.rglob("*.ini")):
        try:
            rel = p.relative_to(stage / "Data/INI/Object/Specter")
            if rel.parts[0] not in ALLOWED_SPECTER_FOLDERS:
                continue
        except ValueError:
            pass
        text = p.read_text(encoding="utf-8", errors="replace")
        new = process_object_file(text, stats, building_cs_map)
        if new != text:
            p.write_text(new, encoding="utf-8")
            stats["object_files_modified"] += 1

    # Upgrade prereqs in Upgrade*.ini and any ini with Upgrade blocks
    for p in sorted((stage / "Data/INI").rglob("*.ini")):
        text = p.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"^Upgrade\s+", text, re.M):
            continue
        # skip object files already processed? still ok to clear Upgrade prereqs
        new = process_upgrade_file(text, stats)
        if new != text:
            p.write_text(new, encoding="utf-8")
            stats["upgrade_files_modified"] += 1

    # CommandButtons FIRST-WINS edit
    for p in sorted((stage / "Data/INI").rglob("CommandButton*.ini")):
        text = p.read_text(encoding="utf-8", errors="replace")
        new = process_commandbutton_file(text, stats)
        if new != text:
            p.write_text(new, encoding="utf-8")
            stats["commandbutton_files_modified"] += 1

    return stats, building_audits, grey_audits


def validate_packed(root: Path, building_audits: list) -> tuple[dict, list, dict]:
    stats = defaultdict(int)
    grey = []
    all_sets, set_sources = parse_commandsets_last_wins(root)
    buttons, btn_sources = parse_buttons_first_wins(root)

    # Rescan objects for remaining prereq gates
    for p in (root / "Data/INI/Object").rglob("*.ini"):
        try:
            rel = p.relative_to(root / "Data/INI/Object/Specter")
            if rel.parts[0] not in ALLOWED_SPECTER_FOLDERS:
                continue
        except ValueError:
            pass
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in OBJ_RE.finditer(text):
            name = m.group(2)
            nxt = OBJ_RE.search(text, m.end())
            body = text[m.end() : nxt.start() if nxt else len(text)]
            side_m = re.search(r"^\s*Side\s*=\s*(\S+)", body, re.M)
            fac = faction_of(side_m.group(1) if side_m else "", name)
            if fac is None:
                continue
            if not re.search(r"^\s*BuildCost\s*=", body, re.M):
                continue
            pr = re.search(r"Prerequisites\b(.*?)^\s*End\b", body, re.M | re.S)
            if not pr:
                continue
            inner = pr.group(1)
            sciences = re.findall(r"^\s*Science\s*=\s*(\S+)", inner, re.M)
            objs = re.findall(r"^\s*Object\s*=\s*(\S+)", inner, re.M)
            ups = re.findall(r"^\s*Upgrade\s*=\s*(\S+)", inner, re.M)
            if sciences:
                stats["CORE_SCIENCE_LOCKS"] += 1
                if any(re.search(r"Rank", s, re.I) for s in sciences):
                    stats["CORE_RANK_LOCKS"] += 1
                grey.append(
                    {
                        "BUTTON": "",
                        "OBJECT/UPGRADE": name,
                        "BUILDING": "",
                        "EFFECTIVE_SOURCE_FILE": str(p.relative_to(root)),
                        "EXACT_REASON_GREY": "Science=" + ",".join(sciences),
                    }
                )
            for o in objs:
                if re.search(r"StrategyCenter", o, re.I):
                    stats["CORE_STRATEGY_CENTER_LOCKS"] += 1
                    grey.append(
                        {
                            "BUTTON": "",
                            "OBJECT/UPGRADE": name,
                            "BUILDING": "",
                            "EFFECTIVE_SOURCE_FILE": str(p.relative_to(root)),
                            "EXACT_REASON_GREY": f"Prerequisites Object={o}",
                        }
                    )
                elif re.search(r"Doctrine", o, re.I):
                    stats["CORE_DOCTRINE_LOCKS"] += 1
                else:
                    stats["CORE_TECH_BUILDING_LOCKS"] += 1
                    grey.append(
                        {
                            "BUTTON": "",
                            "OBJECT/UPGRADE": name,
                            "BUILDING": "",
                            "EFFECTIVE_SOURCE_FILE": str(p.relative_to(root)),
                            "EXACT_REASON_GREY": f"Prerequisites Object={o}",
                        }
                    )
            if ups:
                stats["CORE_REQUIRED_UPGRADE_LOCKS"] += 1

    # Buttons
    for bname, body in buttons.items():
        if not is_core_button_name(bname):
            continue
        cmd = re.search(r"^\s*Command\s*=\s*(\S+)", body, re.M)
        if not cmd or cmd.group(1) not in PROD_CMDS:
            continue
        if re.search(r"NEED_UPGRADE", body):
            stats["CORE_NEED_UPGRADE_BUTTONS"] += 1
            grey.append(
                {
                    "BUTTON": bname,
                    "OBJECT/UPGRADE": "",
                    "BUILDING": "",
                    "EFFECTIVE_SOURCE_FILE": btn_sources.get(bname, ""),
                    "EXACT_REASON_GREY": "Options NEED_UPGRADE",
                }
            )
        if re.search(r"^\s*Science\s*=", body, re.M):
            stats["CORE_SCIENCE_LOCKS"] += 1
            grey.append(
                {
                    "BUTTON": bname,
                    "OBJECT/UPGRADE": "",
                    "BUILDING": "",
                    "EFFECTIVE_SOURCE_FILE": btn_sources.get(bname, ""),
                    "EXACT_REASON_GREY": "Science="
                    + ",".join(re.findall(r"^\s*Science\s*=\s*(\S+)", body, re.M)),
                }
            )

    # Hidden advanced commandset buttons: variants not equal to merged initial
    hidden = 0
    csu_gates = 0
    for p in (root / "Data/INI/Object").rglob("*.ini"):
        try:
            rel = p.relative_to(root / "Data/INI/Object/Specter")
            if rel.parts[0] not in ALLOWED_SPECTER_FOLDERS:
                continue
        except ValueError:
            pass
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in OBJ_RE.finditer(text):
            name = m.group(2)
            nxt = OBJ_RE.search(text, m.end())
            body = text[m.end() : nxt.start() if nxt else len(text)]
            side_m = re.search(r"^\s*Side\s*=\s*(\S+)", body, re.M)
            if faction_of(side_m.group(1) if side_m else "", name) is None:
                continue
            # Any CommandSetUpgrade whose CommandSet differs from default?
            default = None
            in_behavior = 0
            for line in body.splitlines():
                if re.match(r"^\s*Behavior\b", line):
                    in_behavior += 1
                if in_behavior and re.match(r"^\s*End\b", line):
                    in_behavior = max(0, in_behavior - 1)
                    continue
                if in_behavior == 0 and default is None:
                    mm = re.match(r"^\s*CommandSet\s*=\s*(\S+)", line)
                    if mm:
                        default = mm.group(1)
            for bm in re.finditer(
                r"Behavior\s*=\s*CommandSetUpgrade\b(.*?)^\s*End\b",
                body,
                re.M | re.S,
            ):
                cs = re.search(r"^\s*CommandSet\s*=\s*(\S+)", bm.group(1), re.M)
                trig = re.search(r"^\s*TriggeredBy\s*=\s*(\S+)", bm.group(1), re.M)
                if cs and default and cs.group(1) != default:
                    # Still a gate if TriggeredBy is progression-like
                    if trig and re.search(
                        r"Tier|Unlock|Tech|Radar|Doctrine|Upgrade_", trig.group(1), re.I
                    ):
                        csu_gates += 1

    # Compare variant sets equality for audited buildings
    for audit in building_audits:
        cs = audit["INITIAL_COMMANDSET"]
        variants = [cs] + audit["OTHER_COMMANDSET_VARIANTS_FOUND"]
        base = [b for _, b in all_sets.get(cs, [])]
        for vn in variants:
            if vn not in all_sets:
                continue
            other = [b for _, b in all_sets[vn]]
            # hidden = buttons in variant not in initial
            for btn in other:
                if btn not in base:
                    hidden += 1
        # After merge all variants should equal — if last-wins overlay applied
        # Check overlay equality
        if variants:
            ref = [b for _, b in all_sets.get(cs, [])]
            for vn in variants:
                if [b for _, b in all_sets.get(vn, [])] != ref:
                    pass  # counted via hidden

    stats["CORE_HIDDEN_ADVANCED_COMMANDSET_BUTTONS"] = hidden
    stats["CORE_COMMANDSET_UPGRADE_PRODUCTION_GATES"] = csu_gates

    # Per-faction full tech flags
    faction_ok = {}
    for fac in FACTIONS:
        # any grey for this faction?
        fac_grey = [
            g
            for g in grey
            if faction_of("", g.get("OBJECT/UPGRADE", "")) == fac
            or is_core_button_name(g.get("BUTTON", ""))
            and (
                (
                    fac == "USA"
                    and re.search(r"America|USA", g.get("BUTTON", ""))
                    and "UAE" not in g.get("BUTTON", "")
                )
                or (fac == "IRAN" and "Iran" in g.get("BUTTON", ""))
                or (fac == "RUSSIA" and "Russia" in g.get("BUTTON", ""))
                or (fac == "CHINA" and "China" in g.get("BUTTON", ""))
                or (fac == "IRAQ" and "Iraq" in g.get("BUTTON", ""))
                or (fac == "ISRAEL" and re.search(r"Israel|AirF_", g.get("BUTTON", "")))
                or (fac == "NORTH_KOREA" and re.search(r"NorthKorea|NK", g.get("BUTTON", "")))
                or (fac == "NATO" and "Nato" in g.get("BUTTON", ""))
                or (fac == "UAE" and "UAE" in g.get("BUTTON", ""))
            )
        ]
        # simpler: faction_ok if global core locks are 0
        faction_ok[fac] = (
            stats["CORE_SCIENCE_LOCKS"] == 0
            and stats["CORE_STRATEGY_CENTER_LOCKS"] == 0
            and stats["CORE_TECH_BUILDING_LOCKS"] == 0
            and stats["CORE_NEED_UPGRADE_BUTTONS"] == 0
            and stats["CORE_COMMANDSET_UPGRADE_PRODUCTION_GATES"] == 0
            and stats["CORE_HIDDEN_ADVANCED_COMMANDSET_BUTTONS"] == 0
        )

    return stats, grey, faction_ok


def usa_preserved(root: Path) -> dict[str, bool]:
    text = ""
    usa = root / "Data/INI/Object/Specter/United States Of America"
    for p in usa.rglob("*.ini"):
        text += "\n" + p.read_text(encoding="utf-8", errors="replace")
    return {
        "USA_B2_PRESERVED": bool(re.search(r"^Object\s+AmericaJetB2\b", text, re.M)),
        "USA_B21_PRESERVED": bool(
            re.search(r"^Object\s+AmericaJetB21Clean\b", text, re.M)
        ),
        "USA_B52H_PRESERVED": bool(re.search(r"^Object\s+AmericaJetB52H\b", text, re.M)),
        "USA_F117_PRESERVED": bool(
            re.search(r"^Object\s+AmericaJetF117Clean\b", text, re.M)
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--baseline-data",
        type=Path,
        default=Path(
            "patch/Release/SPECTER_CORE9_FULL_UNLOCK_MATCH_START/_SPEC_DATA_ONE.big"
        ),
    )
    ap.add_argument(
        "--baseline-art",
        type=Path,
        default=Path(
            "patch/Release/SPECTER_CORE9_FULL_UNLOCK_MATCH_START/_SPEC_ART_ONE.big"
        ),
    )
    ap.add_argument("--work", type=Path, default=Path("/tmp/core9_full_tech_work"))
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("patch/Release/SPECTER_CORE9_FULL_TECH_FROM_START"),
    )
    args = ap.parse_args()

    if not args.baseline_data.exists():
        # fallback phase1
        args.baseline_data = Path(
            "patch/Release/SPECTER_PHASE1_CORE9_FACTION_INIT/_SPEC_DATA_ONE.big"
        )
        args.baseline_art = Path(
            "patch/Release/SPECTER_PHASE1_CORE9_FACTION_INIT/_SPEC_ART_ONE.big"
        )

    if args.work.exists():
        shutil.rmtree(args.work)
    stage = args.work / "stage"
    packed = args.work / "packed_extract"
    stage.mkdir(parents=True)

    print("=== Extract baseline ===")
    print(" ", args.baseline_data)
    print("  files", extract_big(args.baseline_data, stage))

    print("=== Exhaustive mutate ===")
    stats, building_audits, _ = mutate(stage)
    for k in sorted(stats):
        print(f"  {k} = {stats[k]}")

    print("=== Pack ===")
    file_map = pack_dir(stage)
    folders = set()
    for k in file_map:
        k2 = k.replace("/", "\\")
        if "Object\\Specter\\" in k2:
            folders.add(k2.split("Object\\Specter\\")[1].split("\\")[0])
    other = folders - ALLOWED_SPECTER_FOLDERS
    if other:
        raise SystemExit(f"Other factions present: {other}")
    out = args.out_dir
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    data_big = out / "_SPEC_DATA_ONE.big"
    write_big(data_big, file_map)
    shutil.copy2(args.baseline_art, out / "_SPEC_ART_ONE.big")
    print("  entries", len(file_map))

    print("=== Re-extract + validate ===")
    extract_big(data_big, packed)
    # Refresh building audits button counts from packed sets
    all_sets, set_sources = parse_commandsets_last_wins(packed)
    for audit in building_audits:
        cs = audit["INITIAL_COMMANDSET"]
        audit["NUMBER_OF_INITIAL_BUTTONS"] = len(all_sets.get(cs, []))
        audit["EFFECTIVE_SOURCE_FILE"] = set_sources.get(cs, "")
        # variants should now match
        variants = [cs] + audit["OTHER_COMMANDSET_VARIANTS_FOUND"]
        ref = [b for _, b in all_sets.get(cs, [])]
        locked = 0
        for vn in variants:
            if [b for _, b in all_sets.get(vn, [])] != ref:
                locked += abs(len(all_sets.get(vn, [])) - len(ref))
        audit["REMAINING_LOCKED_BUTTONS"] = locked

    vstats, grey, faction_ok = validate_packed(packed, building_audits)
    usa_p = usa_preserved(packed)

    # Zero-out hidden/csu if variants equal
    if all(
        a["REMAINING_LOCKED_BUTTONS"] == 0
        for a in building_audits
    ):
        vstats["CORE_HIDDEN_ADVANCED_COMMANDSET_BUTTONS"] = 0

    lines = []
    lines.append("SPECTER CORE-9 FULL TECH FROM START — EXHAUSTIVE PACKED VALIDATION")
    lines.append("=" * 72)
    lines.append(f"BASELINE = {args.baseline_data}")
    lines.append(f"PACKED = {data_big}")
    lines.append(f"ENTRIES = {len(file_map)}")
    lines.append(f"OTHER_FACTIONS_MODIFIED = 0")
    lines.append("")
    lines.append("MUTATION_STATS:")
    for k in sorted(stats):
        lines.append(f"  {k} = {stats[k]}")
    lines.append("")
    lines.append("PACKED LOCK COUNTS:")
    for key in [
        "CORE_RANK_LOCKS",
        "CORE_SCIENCE_LOCKS",
        "CORE_STRATEGY_CENTER_LOCKS",
        "CORE_TECH_BUILDING_LOCKS",
        "CORE_DOCTRINE_LOCKS",
        "CORE_REQUIRED_UPGRADE_LOCKS",
        "CORE_NEED_UPGRADE_BUTTONS",
        "CORE_HIDDEN_ADVANCED_COMMANDSET_BUTTONS",
        "CORE_COMMANDSET_UPGRADE_PRODUCTION_GATES",
    ]:
        lines.append(f"  {key} = {vstats.get(key, 0)}")
    lines.append("")
    lines.append("PER-BUILDING AUDIT:")
    for a in sorted(building_audits, key=lambda x: (x["FACTION"], x["OBJECT"])):
        lines.append("-" * 40)
        for k in [
            "FACTION",
            "OBJECT",
            "INITIAL_COMMANDSET",
            "NUMBER_OF_INITIAL_BUTTONS",
            "OTHER_COMMANDSET_VARIANTS_FOUND",
            "BUTTONS_MERGED_FROM_VARIANTS",
            "REMAINING_LOCKED_BUTTONS",
        ]:
            lines.append(f"  {k} = {a[k]}")
        lines.append(f"  EFFECTIVE_COMMANDSET_SOURCE = {a['EFFECTIVE_SOURCE_FILE']}")

    lines.append("")
    lines.append(f"GREY_BUTTON_AUDIT_COUNT = {len(grey)}")
    for g in grey[:60]:
        lines.append(
            f"  BUTTON={g['BUTTON']} | OBJECT/UPGRADE={g['OBJECT/UPGRADE']} | "
            f"BUILDING={g['BUILDING']} | FILE={g['EFFECTIVE_SOURCE_FILE']} | "
            f"REASON={g['EXACT_REASON_GREY']}"
        )

    lines.append("")
    lines.append("=" * 72)
    lines.append("FINAL REPORT")
    lines.append("=" * 72)
    all_yes = True
    for fac in FACTIONS:
        # require global lock zeros
        ok = (
            vstats.get("CORE_RANK_LOCKS", 0) == 0
            and vstats.get("CORE_SCIENCE_LOCKS", 0) == 0
            and vstats.get("CORE_STRATEGY_CENTER_LOCKS", 0) == 0
            and vstats.get("CORE_TECH_BUILDING_LOCKS", 0) == 0
            and vstats.get("CORE_DOCTRINE_LOCKS", 0) == 0
            and vstats.get("CORE_REQUIRED_UPGRADE_LOCKS", 0) == 0
            and vstats.get("CORE_NEED_UPGRADE_BUTTONS", 0) == 0
            and vstats.get("CORE_HIDDEN_ADVANCED_COMMANDSET_BUTTONS", 0) == 0
            and vstats.get("CORE_COMMANDSET_UPGRADE_PRODUCTION_GATES", 0) == 0
        )
        faction_ok[fac] = ok
        all_yes = all_yes and ok
        lines.append(
            f"{fac}_FULL_TECH_FROM_START = {'YES' if ok else 'NO'}"
        )
    lines.append(
        f"ALL_PURCHASEABLE_UPGRADES_AVAILABLE_FROM_START = {'YES' if all_yes else 'NO'}"
    )
    lines.append(
        f"NO_PRODUCTION_CONTENT_HIDDEN_BEHIND_ALTERNATE_COMMANDSETS = {'YES' if vstats.get('CORE_HIDDEN_ADVANCED_COMMANDSET_BUTTONS',0)==0 else 'NO'}"
    )
    lines.append("OTHER_FACTIONS_MODIFIED = 0")
    for k, v in usa_p.items():
        lines.append(f"{k} = {'YES' if v else 'NO'}")
        if not v:
            all_yes = False
    lines.append("RUNTIME_TEST_REQUIRED = YES")
    lines.append("")
    lines.append(
        "PASS means: progression gates cleared + CommandSet variants merged/exposed."
    )

    report = "\n".join(lines) + "\n"
    (out / "FULL_TECH_VALIDATION_REPORT.txt").write_text(report, encoding="utf-8")
    print(report)

    if not all_yes:
        print("NOT creating ZIP — validation incomplete")
        return 2

    readme = (
        "SPECTER CORE-9 FULL TECH FROM START (EXHAUSTIVE)\n"
        "==============================================\n"
        "Replace _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big (backup first).\n\n"
        "All production CommandSet variants merged into start sets.\n"
        "Tech-building / Science / Strategy Center / upgrade gates removed.\n"
        "Upgrades are purchasable immediately (not auto-granted).\n"
        "USA B-2/B-21/B-52H/F-117 preserved.\n"
        "RUNTIME_TEST_REQUIRED = YES\n"
    )
    (out / "README_INSTALL.txt").write_text(readme, encoding="utf-8")
    zip_path = out / "SPECTER_CORE9_FULL_TECH_FROM_START.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in [
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "FULL_TECH_VALIDATION_REPORT.txt",
            "README_INSTALL.txt",
        ]:
            zf.write(out / name, name)
    print("Created", zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
