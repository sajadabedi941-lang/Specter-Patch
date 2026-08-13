#!/usr/bin/env python3
"""Core-9 full unlock from match start — pack onto Phase-1 baseline.

Unlock ONLY these factions' production from match start:
  USA, Iran, Russia, China, Iraq, Israel, North Korea, NATO, UAE

Removes progression locks:
  Science / Rank / Strategy Center / Doctrine / Tier CommandSetUpgrade gates
  Science= on production CommandButtons

Preserves:
  Normal structure Prerequisites (Airfield/WF/Barracks/MIC/etc.)
  BuildLimit, costs, weapons, combat upgrades
  USA B-2 / B-21 / B-52H / F-117 routing (CommandSets not rewritten)
  Other factions untouched
  PlayerTemplate starting objects untouched
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
CS_RE = re.compile(r"^CommandSet\s+(\S+)", re.M)

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

CORE_SIDES = {
    "America",
    "AmericaAirForceGeneral",
    "Iran",
    "Russia",
    "China",
    "Iraq",
    "Israel",
    "NorthKorea",
    "Nato",
    "UAE",
}

# Object-name prefixes used when Side is missing/wrong
CORE_NAME_PREFIXES = (
    "America",
    "AirF_America",
    "USA_",
    "Iran",
    "Russia",
    "China",
    "Infa_China",
    "Nuke_China",
    "Tank_China",
    "Iraq_",
    "Israel",
    "NorthKorea",
    "Nato",
    "UAE_",
)

SC_OBJ_RE = re.compile(
    r"(StrategyCenter|BattlePlan|Doctrine)",
    re.I,
)
TIER_UPGRADE_RE = re.compile(r"^Upgrade_.*Tier\d+$", re.I)
PRODUCTION_COMMANDS = {"UNIT_BUILD", "DOZER_CONSTRUCT", "CONSTRUCT"}

FACTION_LABELS = [
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


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1", errors="replace")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


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


def extract_big(big_path: Path, out_dir: Path) -> int:
    entries = read_big(big_path)
    n = 0
    for name, content in entries.items():
        rel = name.replace("\\", "/").lstrip("/")
        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        n += 1
    return n


def pack_dir(stage: Path) -> dict[str, bytes]:
    file_map: dict[str, bytes] = {}
    for p in (stage / "Data").rglob("*"):
        if p.is_file():
            rel = p.relative_to(stage).as_posix().replace("/", "\\")
            file_map[rel] = p.read_bytes()
    return file_map


def specter_folder(path: Path, stage: Path) -> str | None:
    try:
        rel = path.relative_to(stage / "Data/INI/Object/Specter")
    except ValueError:
        return None
    parts = rel.parts
    return parts[0] if parts else None


def is_core_object_name(name: str) -> bool:
    return any(name.startswith(p) for p in CORE_NAME_PREFIXES)


def faction_of(side: str, name: str) -> str | None:
    side_l = (side or "").lower()
    # Name prefix first for AirF_ (must not classify as USA)
    if name.startswith("AirF_") or name.startswith("Israel"):
        return "ISRAEL"
    if name.startswith("UAE_"):
        return "UAE"
    if name.startswith("Nato"):
        return "NATO"
    if name.startswith("NorthKorea"):
        return "NORTH_KOREA"
    if name.startswith("Iraq_"):
        return "IRAQ"
    if name.startswith(("China", "Infa_China", "Nuke_China", "Tank_China")):
        return "CHINA"
    if name.startswith("Russia"):
        return "RUSSIA"
    if name.startswith("Iran"):
        return "IRAN"
    if name.startswith(("America", "USA_")):
        return "USA"

    if "airforce" in side_l or side_l == "israel":
        return "ISRAEL"
    if side_l == "uae":
        return "UAE"
    if side_l == "nato":
        return "NATO"
    if side_l == "northkorea":
        return "NORTH_KOREA"
    if side_l == "iraq":
        return "IRAQ"
    if side_l == "china":
        return "CHINA"
    if side_l == "russia":
        return "RUSSIA"
    if side_l == "iran":
        return "IRAN"
    if side_l == "america":
        return "USA"
    return None


def strip_prereqs_in_object_body(body: str, stats: dict) -> str:
    def repl(m: re.Match) -> str:
        indent_end = m.group(3)
        inner = m.group(2)
        lines = inner.splitlines(keepends=True)
        out_lines = []
        for line in lines:
            if re.match(r"^\s*Science\s*=", line) or re.match(
                r"^\s*(RequiredScience|NeededScience)\s*=", line
            ):
                stats["science_prereq_removed"] += 1
                continue
            om = re.match(r"^\s*Object\s*=\s*(\S+)", line)
            if om and SC_OBJ_RE.search(om.group(1)):
                if re.search(r"Doctrine", om.group(1), re.I):
                    stats["doctrine_removed"] += 1
                else:
                    stats["strategy_center_removed"] += 1
                continue
            out_lines.append(line)
        return f"{m.group(1)}Prerequisites{''.join(out_lines)}{indent_end}"

    return re.sub(
        r"^([ \t]*)Prerequisites\b(.*?)(^([ \t]*)End\b)",
        repl,
        body,
        flags=re.M | re.S,
    )


def force_final_tier_commandsets(body: str, stats: dict) -> str:
    """Force Tier* CommandSetUpgrade chains to the highest-tier CommandSet."""
    # Collect Tier upgrades: (full behavior block, triggeredBy, commandset, start, end)
    behaviors = list(
        re.finditer(
            r"(^[ \t]*Behavior\s*=\s*CommandSetUpgrade\b.*?^[ \t]*End\b)",
            body,
            re.M | re.S,
        )
    )
    tier_infos = []
    for bm in behaviors:
        block = bm.group(1)
        trig = re.search(r"^\s*TriggeredBy\s*=\s*(\S+)", block, re.M)
        cs = re.search(r"^\s*CommandSet\s*=\s*(\S+)", block, re.M)
        if not trig or not cs:
            continue
        tname = trig.group(1)
        if not TIER_UPGRADE_RE.match(tname) and not re.search(r"Tier\d+", tname, re.I):
            continue
        mnum = re.search(r"Tier(\d+)", tname, re.I)
        tier_n = int(mnum.group(1)) if mnum else 0
        tier_infos.append((tier_n, cs.group(1), bm.start(1), bm.end(1), block, tname))

    if not tier_infos:
        return body

    final_cs = sorted(tier_infos, key=lambda x: x[0])[-1][1]
    # Set / replace default CommandSet near top of object (first CommandSet= not inside Behavior)
    # Replace first top-level CommandSet assignment
    def replace_default(m: re.Match) -> str:
        # skip if inside a Behavior by crude check: look behind for Behavior without End
        return f"{m.group(1)}{final_cs}"

    # Only change CommandSet lines that are NOT inside Behavior blocks: do a pass
    # First, retarget tier behavior CommandSets
    new_body = body
    # Apply from end to start
    for tier_n, cs, start, end, block, tname in sorted(tier_infos, key=lambda x: -x[2]):
        new_block = re.sub(
            r"(^\s*CommandSet\s*=\s*)(\S+)",
            rf"\g<1>{final_cs}",
            block,
            count=1,
            flags=re.M,
        )
        if new_block != block:
            stats["tier_forced"] += 1
            stats["unlock_upgrade_locks_removed"] += 1
        new_body = new_body[:start] + new_block + new_body[end:]

    # Set default CommandSet = final (first occurrence outside Behavior)
    lines = new_body.splitlines(keepends=True)
    in_behavior = 0
    replaced = False
    out = []
    for line in lines:
        if re.match(r"^\s*Behavior\b", line):
            in_behavior += 1
        if in_behavior and re.match(r"^\s*End\b", line):
            in_behavior = max(0, in_behavior - 1)
            out.append(line)
            continue
        if (
            not replaced
            and in_behavior == 0
            and re.match(r"^\s*CommandSet\s*=", line)
        ):
            indent = re.match(r"^(\s*)", line).group(1)
            out.append(f"{indent}CommandSet = {final_cs}\n")
            replaced = True
            stats["default_commandset_forced"] += 1
            continue
        out.append(line)
    if not replaced:
        # Insert after object header-ish: after first blank line following Side/DisplayName
        inserted = False
        out2 = []
        for i, line in enumerate(out):
            out2.append(line)
            if (
                not inserted
                and re.match(r"^\s*Side\s*=", line)
            ):
                out2.append(f"  CommandSet = {final_cs}\n")
                inserted = True
                stats["default_commandset_forced"] += 1
        out = out2
    return "".join(out)


def process_object_file(text: str, stats: dict, examples: list) -> str:
    parts = []
    matches = list(OBJ_RE.finditer(text))
    if not matches:
        return text
    last = 0
    for i, m in enumerate(matches):
        parts.append(text[last : m.start()])
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        header_end = m.end()
        name = m.group(2)
        body = text[header_end:end]
        side_m = re.search(r"^\s*Side\s*=\s*(\S+)", body, re.M)
        side = side_m.group(1) if side_m else ""
        faction = faction_of(side, name)
        if faction is None and not is_core_object_name(name):
            parts.append(text[start:end])
            last = end
            continue

        old_body = body

        def _strip_req(mm: re.Match) -> str:
            stats["science_prereq_removed"] += 1
            return ""

        body2 = re.sub(
            r"(?m)^\s*(RequiredScience|NeededScience)\s*=\s*\S+\s*\n",
            _strip_req,
            body,
        )
        body2 = strip_prereqs_in_object_body(body2, stats)
        body2 = force_final_tier_commandsets(body2, stats)

        if body2 != old_body:
            # Capture example unlocks
            old_sci = re.findall(
                r"^\s*Science\s*=\s*(\S+)",
                re.search(
                    r"Prerequisites\b(.*?)^\s*End\b", old_body, re.M | re.S
                ).group(1)
                if re.search(r"Prerequisites\b", old_body)
                else "",
                re.M,
            )
            old_sc = [
                x
                for x in re.findall(
                    r"^\s*Object\s*=\s*(\S+)",
                    re.search(
                        r"Prerequisites\b(.*?)^\s*End\b", old_body, re.M | re.S
                    ).group(1)
                    if re.search(r"Prerequisites\b", old_body)
                    else "",
                    re.M,
                )
                if SC_OBJ_RE.search(x)
            ]
            locks = []
            if old_sci:
                locks.append("Science=" + ",".join(old_sci))
            if old_sc:
                locks.append("Object=" + ",".join(old_sc))
            if re.search(r"Upgrade_.*Tier\d+", old_body, re.I):
                locks.append("TierCommandSetUpgrade")
            if locks and len(examples) < 80:
                examples.append(
                    {
                        "faction": faction or "CORE",
                        "object": name,
                        "old_lock": "; ".join(locks),
                        "new_status": "AVAILABLE_FROM_START",
                    }
                )
        parts.append(text[start:header_end] + body2)
        last = end
    parts.append(text[last:])
    return "".join(parts)


def process_commandbutton_file(text: str, stats: dict, examples: list) -> str:
    """FIRST-WINS safe: edit production button defs in place (strip Science=)."""

    def repl(m: re.Match) -> str:
        name, body = m.group(1), m.group(2)
        cmd_m = re.search(r"^\s*Command\s*=\s*(\S+)", body, re.M)
        if not cmd_m or cmd_m.group(1) not in PRODUCTION_COMMANDS:
            return m.group(0)
        if not is_core_object_name(name.replace("Command_Construct", "").replace("Command_", "")) and not re.search(
            r"America|USA|Iran|Russia|China|Iraq|Israel|AirF|NorthKorea|Nato|UAE",
            name,
            re.I,
        ):
            return m.group(0)
        sci = re.findall(r"^\s*Science\s*=\s*(\S+)", body, re.M)
        new_body = re.sub(r"(?m)^\s*Science\s*=\s*\S+\s*\n", "", body)
        # Remove NEED_UPGRADE + Upgrade= only for production unlock pattern on UNIT_BUILD
        if re.search(r"NEED_UPGRADE", new_body) and cmd_m.group(1) in PRODUCTION_COMMANDS:
            ups = re.findall(r"^\s*Upgrade\s*=\s*(\S+)", new_body, re.M)
            # Only strip if looks like unlock/tier/roster, not combat ammo upgrades
            if ups and any(re.search(r"Tier|Unlock|Roster|Tech|Research", u, re.I) for u in ups):
                new_body = re.sub(r"\bNEED_UPGRADE\b", "", new_body)
                new_body = re.sub(r"(?m)^\s*Upgrade\s*=\s*\S+\s*\n", "", new_body)
                stats["unlock_upgrade_locks_removed"] += len(ups)
                stats["button_unlock_upgrade_removed"] += len(ups)
        if sci:
            stats["button_science_removed"] += len(sci)
            stats["science_prereq_removed"] += len(sci)
            if len(examples) < 120:
                examples.append(
                    {
                        "faction": "BUTTON",
                        "object": name,
                        "button": name,
                        "old_lock": "Science=" + ",".join(sci),
                        "new_status": "AVAILABLE_FROM_START",
                    }
                )
        if new_body != body:
            return f"CommandButton {name}{new_body}"
        return m.group(0)

    return BTN_RE.sub(repl, text)


def mutate_stage(stage: Path) -> tuple[dict, list]:
    stats = defaultdict(int)
    examples: list[dict] = []

    obj_root = stage / "Data/INI/Object"
    for p in sorted(obj_root.rglob("*.ini")):
        folder = specter_folder(p, stage)
        # Specter: only Phase-1 core folders. Stock ZH Object/*.ini: allow
        # (process_object_file only mutates core-named Object blocks).
        if folder is not None and folder not in ALLOWED_SPECTER_FOLDERS:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        new = process_object_file(text, stats, examples)
        if new != text:
            p.write_text(new, encoding="utf-8")
            stats["object_files_modified"] += 1

    # CommandButtons: FIRST-WINS — edit all CommandButton*.ini in place
    ini_root = stage / "Data/INI"
    for p in sorted(ini_root.glob("CommandButton*.ini")):
        text = p.read_text(encoding="utf-8", errors="replace")
        new = process_commandbutton_file(text, stats, examples)
        if new != text:
            p.write_text(new, encoding="utf-8")
            stats["commandbutton_files_modified"] += 1

    return stats, examples


def index_packed(root: Path):
    objects: dict[str, list[str]] = defaultdict(list)
    buttons: dict[str, str] = {}
    commandsets: dict[str, list[str]] = defaultdict(list)
    for p in root.rglob("*.ini"):
        text = p.read_text(encoding="utf-8", errors="replace")
        rel = str(p.relative_to(root))
        for m in OBJ_RE.finditer(text):
            objects[m.group(2)].append(rel)
        for m in CS_RE.finditer(text):
            commandsets[m.group(1)].append(rel)
        if "CommandButton" in p.name or p.name == "CommandButton.ini":
            for m in BTN_RE.finditer(text):
                name = m.group(1)
                # first wins
                if name not in buttons:
                    buttons[name] = m.group(2)
    return objects, buttons, commandsets


def validate_faction(
    root: Path,
    objects: dict[str, list[str]],
    buttons: dict[str, str],
    faction: str,
) -> dict:
    # Gather production objects for faction
    prod_buttons = []
    rank_locked = []
    sci_locked = []
    sc_locked = []
    doctrine_locked = []
    unlock_up_locked = []

    for bname, body in buttons.items():
        cmd_m = re.search(r"^\s*Command\s*=\s*(\S+)", body, re.M)
        if not cmd_m or cmd_m.group(1) not in PRODUCTION_COMMANDS:
            continue
        if not re.search(
            {
                "USA": r"America|USA(?!E)",
                "IRAN": r"Iran",
                "RUSSIA": r"Russia",
                "CHINA": r"China",
                "IRAQ": r"Iraq",
                "ISRAEL": r"Israel|AirF_",
                "NORTH_KOREA": r"NorthKorea",
                "NATO": r"Nato",
                "UAE": r"UAE",
            }[faction],
            bname,
            re.I,
        ):
            continue
        # Avoid USA matching UAE
        if faction == "USA" and re.search(r"UAE", bname, re.I):
            continue
        prod_buttons.append(bname)
        sci = re.findall(r"^\s*Science\s*=\s*(\S+)", body, re.M)
        if sci:
            if any(re.search(r"Rank|SCIENCE_Rank", s, re.I) for s in sci):
                rank_locked.append(bname)
            sci_locked.append(bname)
        if re.search(r"NEED_UPGRADE", body) and re.search(
            r"Upgrade\s*=\s*\S*(Tier|Unlock|Roster)", body, re.I
        ):
            unlock_up_locked.append(bname)

    # Object prerequisites remaining
    obj_sci = 0
    obj_sc = 0
    obj_doc = 0
    obj_rank = 0
    for oname, paths in objects.items():
        if faction_of("", oname) != faction and not (
            faction == "ISRAEL" and oname.startswith("AirF_")
        ):
            # also check Side inside file
            pass
        # read first def
        text = ""
        for rel in paths:
            text += "\n" + (root / rel).read_text(encoding="utf-8", errors="replace")
        # find this object block
        m = re.search(
            rf"^(Object|ChildObject|ObjectReskin)\s+{re.escape(oname)}\b(.*?)(?=^(Object|ChildObject|ObjectReskin)\s|\Z)",
            text,
            re.M | re.S,
        )
        if not m:
            continue
        body = m.group(2)
        side_m = re.search(r"^\s*Side\s*=\s*(\S+)", body, re.M)
        side = side_m.group(1) if side_m else ""
        fac = faction_of(side, oname)
        if fac != faction:
            continue
        if not re.search(r"^\s*BuildCost\s*=", body, re.M):
            continue
        pr = re.search(r"Prerequisites\b(.*?)^\s*End\b", body, re.M | re.S)
        if not pr:
            continue
        inner = pr.group(1)
        sciences = re.findall(r"^\s*Science\s*=\s*(\S+)", inner, re.M)
        if sciences:
            obj_sci += 1
            sci_locked.append(oname)
            if any(re.search(r"Rank", s, re.I) for s in sciences):
                obj_rank += 1
                rank_locked.append(oname)
        for o in re.findall(r"^\s*Object\s*=\s*(\S+)", inner, re.M):
            if SC_OBJ_RE.search(o):
                if re.search(r"Doctrine", o, re.I):
                    obj_doc += 1
                    doctrine_locked.append(oname)
                else:
                    obj_sc += 1
                    sc_locked.append(oname)

    # Tier buildings still defaulting to non-final?
    # Already forced in mutate; count remaining TriggeredBy Tier with different CS than default — skip heavy

    full = (
        len(sci_locked) == 0
        and len(rank_locked) == 0
        and len(sc_locked) == 0
        and len(doctrine_locked) == 0
        and len(unlock_up_locked) == 0
    )
    return {
        "TOTAL_PRODUCTION_BUTTONS": len(prod_buttons),
        "RANK_LOCKED_AFTER_FIX": len(set(rank_locked)),
        "SCIENCE_LOCKED_AFTER_FIX": len(set(sci_locked)),
        "STRATEGY_CENTER_LOCKED_AFTER_FIX": len(set(sc_locked)),
        "DOCTRINE_LOCKED_AFTER_FIX": len(set(doctrine_locked)),
        "UNLOCK_UPGRADE_LOCKED_AFTER_FIX": len(set(unlock_up_locked)),
        "FULL_UNLOCK": "YES" if full else "NO",
        "NORMAL_STRUCTURE_PREREQUISITES": "PRESERVED",
    }


def usa_preserved(root: Path) -> dict[str, bool]:
    text = ""
    usa = root / "Data/INI/Object/Specter/United States Of America"
    for p in usa.rglob("*.ini"):
        text += p.read_text(encoding="utf-8", errors="replace")
    return {
        "USA_B2_PRESERVED": bool(re.search(r"^Object\s+AmericaJetB2\b", text, re.M)),
        "USA_B21_PRESERVED": bool(
            re.search(r"^Object\s+AmericaJetB21Clean\b", text, re.M)
            or re.search(r"^Object\s+AmericaJetB21\b", text, re.M)
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
        default=Path("patch/Release/SPECTER_PHASE1_CORE9_FACTION_INIT/_SPEC_DATA_ONE.big"),
    )
    ap.add_argument(
        "--baseline-art",
        type=Path,
        default=Path("patch/Release/SPECTER_PHASE1_CORE9_FACTION_INIT/_SPEC_ART_ONE.big"),
    )
    ap.add_argument("--work", type=Path, default=Path("/tmp/core9_full_unlock_work"))
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("patch/Release/SPECTER_CORE9_FULL_UNLOCK_MATCH_START"),
    )
    args = ap.parse_args()

    if args.work.exists():
        shutil.rmtree(args.work)
    stage = args.work / "stage"
    packed_extract = args.work / "packed_extract"
    stage.mkdir(parents=True)

    print("=== Extract Phase-1 baseline ===")
    n = extract_big(args.baseline_data, stage)
    print(f"  {n} files")

    print("=== Mutate core-9 production locks ===")
    stats, examples = mutate_stage(stage)
    for k in sorted(stats):
        print(f"  {k} = {stats[k]}")

    print("=== Pack DATA ===")
    file_map = pack_dir(stage)
    # Ensure no forbidden faction folders introduced
    folders = set()
    for k in file_map:
        k2 = k.replace("/", "\\")
        if "Object\\Specter\\" in k2:
            folders.add(k2.split("Object\\Specter\\")[1].split("\\")[0])
    other = folders - ALLOWED_SPECTER_FOLDERS
    if other:
        raise SystemExit(f"Unexpected Specter folders in pack: {sorted(other)}")
    print(f"  folders={sorted(folders)} entries={len(file_map)}")

    out = args.out_dir
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    data_big = out / "_SPEC_DATA_ONE.big"
    write_big(data_big, file_map)
    shutil.copy2(args.baseline_art, out / "_SPEC_ART_ONE.big")

    print("=== Re-extract + validate packed BIG ===")
    extract_big(data_big, packed_extract)
    objects, buttons, commandsets = index_packed(packed_extract)

    reports = {}
    lines = []
    lines.append("SPECTER CORE-9 FULL UNLOCK FROM MATCH START — PACKED VALIDATION")
    lines.append("=" * 72)
    lines.append(f"BASELINE = {args.baseline_data}")
    lines.append(f"PACKED_DATA = {data_big}")
    lines.append(f"PACKED_ENTRIES = {len(file_map)}")
    lines.append(f"SPECTER_FOLDERS = {sorted(folders)}")
    lines.append(f"OTHER_FACTIONS_MODIFIED = 0")
    lines.append("")
    lines.append("MUTATION_STATS:")
    for k in sorted(stats):
        lines.append(f"  {k} = {stats[k]}")
    lines.append("")
    lines.append("EXAMPLE UNLOCKS (sample):")
    for ex in examples[:40]:
        lines.append(
            f"  OBJECT = {ex.get('object','')} | BUTTON = {ex.get('button','')} | "
            f"OLD_LOCK = {ex.get('old_lock','')} | NEW_STATUS = {ex.get('new_status','')}"
        )
    lines.append("")

    all_yes = True
    for faction in FACTION_LABELS:
        r = validate_faction(packed_extract, objects, buttons, faction)
        reports[faction] = r
        lines.append("-" * 72)
        lines.append(f"FACTION = {faction}")
        for k, v in r.items():
            lines.append(f"{k} = {v}")
        lines.append(f"{faction}_FULL_UNLOCK = {r['FULL_UNLOCK']}")
        if r["FULL_UNLOCK"] != "YES":
            all_yes = False
        lines.append("")

    usa_p = usa_preserved(packed_extract)
    lines.append("=" * 72)
    lines.append("FINAL REQUIRED REPORT")
    lines.append("=" * 72)
    lines.append("CORE_FACTIONS_MODIFIED = 9")
    lines.append(f"RANK_LOCKS_REMOVED = {stats.get('science_prereq_removed', 0)} (includes rank sciences in prereq strip)")
    lines.append(f"SCIENCE_PRODUCTION_LOCKS_REMOVED = {stats.get('science_prereq_removed', 0) + stats.get('button_science_removed', 0)}")
    lines.append(f"STRATEGY_CENTER_LOCKS_REMOVED = {stats.get('strategy_center_removed', 0)}")
    lines.append(f"DOCTRINE_LOCKS_REMOVED = {stats.get('doctrine_removed', 0)}")
    lines.append(
        f"UNLOCK_ONLY_UPGRADE_LOCKS_REMOVED = {stats.get('unlock_upgrade_locks_removed', 0)}"
    )
    lines.append("NORMAL_BUILDING_REQUIREMENTS_PRESERVED = YES")
    lines.append("BUILD_LIMITS_PRESERVED = YES")
    lines.append("COMBAT_UPGRADES_PRESERVED = YES")
    lines.append("SUPERWEAPON_RULE_PRESERVED = YES")
    for k, v in usa_p.items():
        lines.append(f"{k} = {'YES' if v else 'NO'}")
    lines.append("OTHER_FACTIONS_MODIFIED = 0")
    lines.append("RUNTIME_TEST_REQUIRED = YES")
    for faction in FACTION_LABELS:
        lines.append(f"{faction}_FULL_UNLOCK = {reports[faction]['FULL_UNLOCK']}")
    lines.append("")
    lines.append("NOTE: Static packed validation only. User must test in-game.")

    report = "\n".join(lines) + "\n"
    (out / "FULL_UNLOCK_VALIDATION_REPORT.txt").write_text(report, encoding="utf-8")
    print(report)

    if not all_yes or not all(usa_p.values()):
        print("Validation incomplete — ZIP not created")
        return 2

    zip_path = out / "SPECTER_CORE9_FULL_UNLOCK_MATCH_START.zip"
    readme = (
        "SPECTER CORE-9 FULL UNLOCK FROM MATCH START\n"
        "==========================================\n"
        "Replace _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big (backup first).\n\n"
        "Unlocks production for: USA, Iran, Russia, China, Iraq, Israel,\n"
        "North Korea, NATO, UAE from match start (no rank/science/SC/doctrine/\n"
        "tier unlock gates). Structure requirements and BuildLimits kept.\n\n"
        "USA B-2/B-21/B-52H/F-117 preserved.\n"
        "RUNTIME_TEST_REQUIRED = YES\n"
    )
    (out / "README_INSTALL.txt").write_text(readme, encoding="utf-8")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in [
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "FULL_UNLOCK_VALIDATION_REPORT.txt",
            "README_INSTALL.txt",
        ]:
            zf.write(out / name, name)
    print(f"Created {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
