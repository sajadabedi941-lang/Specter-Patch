#!/usr/bin/env python3
"""Global CommandSet/CommandBar crash repair for the 17 National Ground countries.

Adds missing CommandButtons only when the Object already exists.
Unglues End+CommandSet concatenation for those countries.
Strips dangling slot refs that cannot be bound to an existing Object.
Does not change Object/Weapon/Armor/Locomotor/ART/CSF/cost/balance.
Does not rewrite protected-faction CommandSet definitions.
Does not rewrite the live 14-slot national ground War Factory bars.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_national_ground_forces import (
    build_big_ordered,
    construct_button,
    last_named,
    norm,
    parse_big,
)
from national_ground_roster import COUNTRIES, LOCKED_BIG_PATHS, PROTECTED_COMMANDSETS

SRC_DATA = Path("/tmp/national_ground_identity/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/national_ground_identity/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/national_ground_commandbar")
IDENTITY_ART_SHA = "e72e6334ab7b9691e3327a0d0a76d4fe771b4cb607e656fa97106e4d69b90c12"

COUNTRY_PREFIXES = tuple(c.key for c in COUNTRIES)


def is_country_commandset(name: str) -> bool:
    for p in COUNTRY_PREFIXES:
        if name.startswith(p):
            return True
        if f"Shortcut{p}" in name:
            return True
        if f"SCIENCE_{p}" in name:
            return True
    return False


def field(blk: str, name: str):
    m = re.search(rf"(?m)^\s*{name}\s+=\s+(\S+)", blk)
    return m.group(1) if m else None


def commandset_core(blk: str) -> str:
    """Header through End, ignoring trailing whitespace after the block."""
    m = re.search(r"(?ms)^CommandSet\s+\S+.*?^(?:End|END)[^\S\n\r]*", blk)
    return m.group(0) if m else blk.strip()


def index_kind(entries, kind: str) -> dict[str, str]:
    found = {}
    for n, blob in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = blob.decode("latin1")
        for m in re.finditer(rf"(?m)^{kind}\s+(\S+)\s*$", t):
            found[m.group(1)] = n
    return found


def last_block_map(entries, kind: str) -> dict[str, tuple[int, str, str]]:
    """name -> (entry_index, filename, block)."""
    found = {}
    for i, (n, blob) in enumerate(entries):
        if not n.lower().endswith(".ini"):
            continue
        t = blob.decode("latin1")
        for m in re.finditer(rf"(?ms)^{kind}\s+(\S+)\s*\r?\n.*?(?=^{kind}\s|\Z)", t):
            found[m.group(1)] = (i, n, m.group(0))
    return found


def object_image(obj_blk: str, fallback: str = "SNCameo") -> str:
    return field(obj_blk, "ButtonImage") or field(obj_blk, "SelectPortrait") or fallback


def unglue_country_commandsets(text: str) -> str:
    # A CR sitting immediately before CommandSet makes `^CommandSet` fail, and
    # last-wins then swallows later bars into the previous block.
    text, ncr = re.subn(r"\r+(?=CommandSet\s)", "", text)

    def repl(m):
        endtok, nxt = m.group(1), m.group(2)
        if is_country_commandset(nxt):
            # LF-only blank line. `End\r\n\r\nCommandSet` leaves `^` on a CR.
            return f"{endtok}\r\n\nCommandSet {nxt}"
        return m.group(0)

    new, n = re.subn(r"(End|END)\r?\nCommandSet (\S+)", repl, text)
    if n or ncr:
        print("unglued", n, "CommandSet boundaries;", ncr, "CR-prefixed headers")
    return new


def strip_unbound_slots(blk: str, buttons: set[str], objects: set[str]) -> str:
    nl = "\r\n" if "\r\n" in blk else "\n"
    lines = blk.splitlines()
    out = []
    for line in lines:
        m = re.match(r"^(\s*)(\d+)\s+=\s+(\S+)", line)
        if not m:
            out.append(line)
            continue
        btn = m.group(3).split(";")[0]
        if btn in buttons:
            out.append(line)
            continue
        obj = btn[len("Command_Construct") :] if btn.startswith("Command_Construct") else None
        if obj and obj in objects:
            out.append(line)
            continue
        print("  strip unbound slot", m.group(2), btn)
    body = nl.join(out)
    if blk.endswith(("\r\n", "\n")) and not body.endswith(("\r\n", "\n")):
        body += nl
    return body


def verify_live_wf_rosters(data_entries) -> None:
    commandsets = last_block_map(data_entries, "CommandSet")
    buttons = set(index_kind(data_entries, "CommandButton"))
    for country in COUNTRIES:
        if country.cs not in commandsets:
            raise SystemExit(f"missing live WF CommandSet {country.cs}")
        blk = commandsets[country.cs][2]
        slots = {int(a): b.split(";")[0] for a, b in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", blk)}
        if set(slots) != set(range(1, 15)):
            raise SystemExit(f"{country.key} live WF slots {sorted(slots)}")
        for i, unit in enumerate(country.units, start=1):
            btn = f"Command_Construct{unit.obj}"
            if slots.get(i) != btn:
                raise SystemExit(f"{country.key} slot {i} {slots.get(i)} != {btn}")
            if btn not in buttons:
                raise SystemExit(f"{country.key} slot {i} missing button {btn}")


def repair_entries(data_entries):
    """Mutate DATA entries in place. Returns the same list."""
    src_map = {norm(n): b for n, b in data_entries}
    data_index = {norm(n): i for i, (n, _) in enumerate(data_entries)}
    locked = {norm(p) for p in LOCKED_BIG_PATHS}

    src_commandsets = last_block_map(data_entries, "CommandSet")
    protected_src = {}
    for name, (_i, _fn, blk) in src_commandsets.items():
        if name in PROTECTED_COMMANDSETS or not is_country_commandset(name):
            protected_src[name] = commandset_core(blk)

    # Pass 1: unglue first so later last_named / last_block_map see real headers.
    for i, (n, blob) in enumerate(list(data_entries)):
        key = norm(n)
        if key in locked:
            continue
        if not n.lower().endswith(".ini") or "commandset" not in n.lower():
            continue
        text = blob.decode("latin1")
        new = unglue_country_commandsets(text)
        if new != text:
            data_entries[i] = (n, new.encode("latin1"))
            print("unglue patched", n, "delta", len(new) - len(text))

    buttons = set(index_kind(data_entries, "CommandButton"))
    objects = last_block_map(data_entries, "Object")
    object_names = set(objects)
    commandsets = last_block_map(data_entries, "CommandSet")

    needed = {}
    country_cs = [name for name in commandsets if is_country_commandset(name)]
    print("country CommandSets", len(country_cs))
    for csname in country_cs:
        _i, _fn, blk = commandsets[csname]
        for _slot, btn in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", blk):
            btn = btn.split(";")[0]
            if btn in buttons or btn in needed:
                continue
            if not btn.startswith("Command_Construct"):
                continue
            obj = btn[len("Command_Construct") :]
            if obj in object_names:
                img = object_image(objects[obj][2])
                needed[btn] = (obj, img)
                print("need button", btn, "->", obj, img)

    # Pass 2: strip unbound slots from 17-country CommandSets only.
    for i, (n, blob) in enumerate(list(data_entries)):
        key = norm(n)
        if key in locked:
            continue
        if not n.lower().endswith(".ini") or "commandset" not in n.lower():
            continue
        text = blob.decode("latin1")
        orig = text
        hits = []
        for csname in country_cs:
            if commandsets[csname][1] != n:
                continue
            m = last_named(text, "CommandSet", csname)
            if m:
                hits.append((m.start(), m.end(), csname, m.group(0)))
        hits.sort(key=lambda x: x[0], reverse=True)
        for start, end, csname, blk in hits:
            if csname in PROTECTED_COMMANDSETS:
                continue
            new_blk = strip_unbound_slots(blk, buttons | set(needed), object_names)
            if new_blk != blk:
                print("stripped slots in", csname)
                text = text[:start] + new_blk + text[end:]
        if text != orig:
            data_entries[i] = (n, text.encode("latin1"))
            print("strip patched", n, "delta", len(text) - len(orig))

    cb_key = norm(r"Data\INI\CommandButton.ini")
    i = data_index[cb_key]
    text = data_entries[i][1].decode("latin1")
    chunks = []
    for btn, (obj, img) in sorted(needed.items()):
        if last_named(text, "CommandButton", btn):
            continue
        chunks.append(
            construct_button(
                btn,
                obj,
                f"CONTROLBAR:Construct{obj}",
                f"CONTROLBAR:ToolTip{obj}",
                img,
            )
        )
        buttons.add(btn)
        print("add button", btn)
    if chunks:
        if not text.endswith("\n"):
            text += "\r\n"
        text = text + "\r\n" + "\r\n".join(chunks)
        data_entries[i] = (data_entries[i][0], text.encode("latin1"))
        print("patched CommandButton.ini added", len(chunks))

    commandsets = last_block_map(data_entries, "CommandSet")
    for name, src_blk in protected_src.items():
        if name not in commandsets:
            raise SystemExit(f"protected CS disappeared {name}")
        got = commandset_core(commandsets[name][2])
        if got != src_blk:
            raise SystemExit(f"protected CommandSet definition changed {name}")
        print("OK protected CS unchanged", name)

    verify_live_wf_rosters(data_entries)

    for n, b in data_entries:
        if norm(n) in locked and src_map.get(norm(n)) != b:
            raise SystemExit(f"locked file changed {n}")
        if n.lower().endswith(".ini") and "\\object\\" in n.replace("/", "\\").lower():
            if b != src_map.get(norm(n)):
                raise SystemExit(f"object INI changed {n}")
    return data_entries


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing identity packed BIG", file=sys.stderr)
        return 1
    art_sha = hashlib.sha256(SRC_ART.read_bytes()).hexdigest()
    if art_sha != IDENTITY_ART_SHA:
        raise SystemExit(f"ART SHA is not identity pack {IDENTITY_ART_SHA}")

    data_entries = parse_big(SRC_DATA)
    src_names = [n for n, _ in data_entries]
    data_entries = repair_entries(data_entries)
    if [n for n, _ in data_entries] != src_names:
        raise SystemExit("DATA entry names/order changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(data_entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    shutil.copy2(SRC_ART, OUT_DIR / "_SPEC_ART_ONE.big")
    print("DATA_SHA256", hashlib.sha256(data_big).hexdigest())
    print("ART_SHA256", hashlib.sha256((OUT_DIR / "_SPEC_ART_ONE.big").read_bytes()).hexdigest())
    print("DATA_BYTES", len(data_big), "FILES", len(data_entries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
