#!/usr/bin/env python3
"""Japan War Factory CommandBar crash-fix audit.

Focus: Japan_WarFactoryCommandSet only.
Does not require object combat data changes. Fails if CommandSet/CommandButton
blocks are packed under Data\\INI\\Object\\ (ZH object-parser AV).
"""

from __future__ import annotations

import hashlib
import io
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_national_ground_forces import last_named, last_named_any, last_object_any, parse_big
from national_ground_roster import JAPAN, ROLES

DATA = Path("/tmp/national_ground_commandbar/_SPEC_DATA_ONE.big")
ART = Path("/tmp/national_ground_commandbar/_SPEC_ART_ONE.big")
SRC_DATA = Path("/tmp/national_ground_identity/_SPEC_DATA_ONE.big")
REPORT = Path("/opt/cursor/artifacts/japan_wf_commandbar_audit.txt")

USA_CS = "AmericaWarFactoryCommandSet"
GERMANY_CS = "GermanyWarfactoryCommandSet"
JAPAN_CS = "Japan_WarFactoryCommandSet"
JAPAN_ALIASES = (
    "CommandSet_Japan_WarFactoryCommands",
    "Japan_WarFactoryCommands",
    "Japan_WarFactoryCommandSet1",
    "Japan_WarFactoryCommandSet2",
    "Japan_WarFactoryCommandSet3",
)


def fail(msg: str) -> int:
    print("FAIL", msg)
    return 1


def field(blk: str, name: str):
    m = re.search(rf"(?m)^\s*{name}\s+=\s+(\S+)", blk)
    return m.group(1) if m else None


def slots_of(blk: str) -> dict[int, str]:
    return {int(a): b for a, b in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", blk)}


def _run() -> int:
    errors = 0
    if not DATA.is_file():
        return fail("missing packed CommandBar DATA")
    data = parse_big(DATA)
    src = parse_big(SRC_DATA) if SRC_DATA.is_file() else []

    print("SPECTER JAPAN WAR FACTORY COMMANDBAR — CRASH-FIX AUDIT")
    print("=" * 72)
    print("Focus: Japan_WarFactoryCommandSet")
    print("CommandSet / CommandButton references only.")
    print("ART, Object combat, Weapon, Armor, Locomotor are not modified.")
    print()
    print("DATA_SHA256", hashlib.sha256(DATA.read_bytes()).hexdigest())
    if ART.is_file():
        print("ART_SHA256", hashlib.sha256(ART.read_bytes()).hexdigest())
    print("DATA_FILES", len(data))

    print()
    print("=== 1. Crash file / Object-folder CommandSet+Button ===")
    for _i, n, b in data:
        nl = n.replace("/", "\\").lower()
        if "nationalgroundcommandbar.ini" in nl:
            errors += fail(f"NationalGroundCommandBar.ini still packed at {n}")
        if nl.endswith(".ini") and "\\object\\" in nl:
            t = b.decode("latin1", "replace")
            if re.search(r"(?m)^CommandSet\s+", t) or re.search(r"(?m)^CommandButton\s+", t):
                errors += fail(f"CommandSet/CommandButton under Object\\ {n}")
    if errors == 0:
        print("OK no CommandSet/CommandButton under Data\\INI\\Object\\")

    print()
    print("=== 2. CommandSet name ===")
    phantom = last_named_any(data, "CommandSet", "CommandSet_Japan_WarFactoryCommands")
    if phantom:
        errors += fail("found literal CommandSet_Japan_WarFactoryCommands")
    else:
        print("OK CommandSet_Japan_WarFactoryCommands is not a real set name")
        print("   live name is Japan_WarFactoryCommandSet")
    for alias in JAPAN_ALIASES:
        hit = last_named_any(data, "CommandSet", alias)
        if hit and alias != JAPAN_CS:
            errors += fail(f"unexpected Japan alias CS {alias} in {hit[0]}")
        elif not hit:
            print(f"OK no phantom {alias}")

    wf = last_named_any(data, "Object", JAPAN.wf)
    if not wf:
        return fail(f"missing WF object {JAPAN.wf}")
    wired = field(wf[1], "CommandSet")
    if wired != JAPAN_CS:
        errors += fail(f"{JAPAN.wf} CommandSet={wired} != {JAPAN_CS}")
    else:
        print(f"OK {JAPAN.wf} CommandSet= {JAPAN_CS}")

    jp = last_named_any(data, "CommandSet", JAPAN_CS)
    if not jp:
        return fail(f"missing {JAPAN_CS}")
    jp_file, jp_blk = jp
    if "\\object\\" in jp_file.replace("/", "\\").lower():
        errors += fail(f"{JAPAN_CS} last-wins under Object\\ {jp_file}")
    if not jp_file.lower().endswith("commandset.ini"):
        errors += fail(f"{JAPAN_CS} last-wins {jp_file}, expected CommandSet.ini")
    else:
        print(f"OK {JAPAN_CS} last-wins {jp_file}")

    usa = last_named_any(data, "CommandSet", USA_CS)
    ger = last_named_any(data, "CommandSet", GERMANY_CS)
    if not usa or not ger:
        return fail("missing USA/Germany WarFactory CommandSet")
    print(f"OK USA last-wins {usa[0]}")
    print(f"OK Germany last-wins {ger[0]}")
    if "\\object\\" in usa[0].replace("/", "\\").lower():
        errors += fail("USA CS last-wins under Object\\")
    if "\\object\\" in ger[0].replace("/", "\\").lower():
        errors += fail("Germany CS last-wins under Object\\")

    print()
    print("=== 3. USA / Germany structure compare ===")
    print("USA slots:")
    for k, v in slots_of(usa[1]).items():
        print(f"  {k:2d} {v}")
    print("Germany slots:")
    for k, v in slots_of(ger[1]).items():
        print(f"  {k:2d} {v}")
    print("Japan slots:")
    jp_slots = slots_of(jp_blk)
    for k in sorted(jp_slots):
        print(f"  {k:2d} {jp_slots[k]}")
    if set(jp_slots) != set(range(1, 15)):
        errors += fail(f"Japan slots {sorted(jp_slots)} != 1-14")
    else:
        print("OK Japan has slots 1-14 like a complete WF bar")
    if any(v.startswith("Command_ConstructNato") or "Leopard2A7Plus" in v for v in jp_slots.values()):
        errors += fail("Japan bar still has NATO placeholder buttons")

    print()
    print("=== 4. CommandButton.ini + Object existence ===")
    seen_btn = []
    seen_obj = []
    for idx, unit in enumerate(JAPAN.units, 1):
        role = ROLES[idx - 1]
        btn = f"Command_Construct{unit.obj}"
        if jp_slots.get(idx) != btn:
            errors += fail(f"slot {idx} {jp_slots.get(idx)} != {btn}")
        bdefs = []
        for _i, n, b in data:
            if not n.lower().endswith(".ini"):
                continue
            t = b.decode("latin1", "replace")
            m = last_named(t, "CommandButton", btn)
            if m:
                bdefs.append((n, m))
        if not bdefs:
            errors += fail(f"missing CommandButton {btn}")
            continue
        last_file, last_blk = bdefs[-1]
        if not last_file.lower().endswith("commandbutton.ini"):
            errors += fail(f"{btn} last-wins {last_file}, expected CommandButton.ini")
        obj = field(last_blk, "Object")
        if obj != unit.obj:
            errors += fail(f"{btn} Object={obj}")
        if field(last_blk, "Command") != "UNIT_BUILD":
            errors += fail(f"{btn} Command={field(last_blk, 'Command')}")
        ohit = last_object_any(data, unit.obj)
        if not ohit:
            errors += fail(f"missing Object {unit.obj}")
        seen_btn.append(btn)
        seen_obj.append(unit.obj)
        print(
            f"  {idx:2d} {role:22s} {btn} -> {obj}  "
            f"button={Path(last_file.replace(chr(92), '/')).name}  "
            f"object={'OK' if ohit else 'MISSING'}"
        )

    print()
    print("=== 5. Duplicate / missing reference audit ===")
    btn_dups = [k for k, v in Counter(seen_btn).items() if v > 1]
    obj_dups = [k for k, v in Counter(seen_obj).items() if v > 1]
    if btn_dups:
        errors += fail(f"duplicate Japan buttons {btn_dups}")
    else:
        print("OK no duplicate Japan CommandButtons on the bar")
    if obj_dups:
        errors += fail(f"duplicate Japan Objects {obj_dups}")
    else:
        print("OK no duplicate Japan Objects on the bar")
    if len(seen_btn) != 14 or len(seen_obj) != 14:
        errors += fail(f"Japan refs buttons={len(seen_btn)} objects={len(seen_obj)}")
    else:
        print("OK 14 buttons and 14 objects")

    # same button defined twice in CommandButton.ini
    for _i, n, b in data:
        if not n.lower().endswith("commandbutton.ini"):
            continue
        names = re.findall(r"(?m)^CommandButton\s+(Command_ConstructJapan\S+)", b.decode("latin1", "replace"))
        dups = [k for k, v in Counter(names).items() if v > 1]
        if dups:
            errors += fail(f"duplicate Japan button defs in {n}: {dups}")
        else:
            print("OK CommandButton.ini has unique Japan construct buttons")

    if src:
        src_objs = {}
        dst_objs = {}
        for pack, into in ((src, src_objs), (data, dst_objs)):
            for unit in JAPAN.units:
                hit = last_object_any(pack, unit.obj)
                if hit:
                    into[unit.obj] = re.sub(r"(?m)^\s*DisplayName\s+=\s+\S+\s*$", "", hit[1])
        for obj in dst_objs:
            if obj in src_objs and dst_objs[obj] != src_objs[obj]:
                errors += fail(f"object combat/model data changed {obj}")
        if not any(obj in src_objs and dst_objs.get(obj) != src_objs[obj] for obj in dst_objs):
            print("OK Japan object combat data unchanged")

    print()
    print("=== Packed BIG audit ===")
    if errors:
        print("AUDIT_FAIL", errors)
        return 1
    print("AUDIT_OK")
    return 0


def main() -> int:
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        code = _run()
    finally:
        sys.stdout = old
    text = buf.getvalue()
    print(text, end="")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text)
    print("wrote", REPORT)
    return code


if __name__ == "__main__":
    sys.exit(main())
