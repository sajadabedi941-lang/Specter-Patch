#!/usr/bin/env python3
"""National Ground CommandBar integration.

Last-wins CommandSet / CommandButton / DisplayName / CSF only.
Does not change Object weapons, armor, locomotor, cost, time, models, or ART.
Does not touch protected USA/Russia/China/Iran/Iraq/Egypt/Israel/NATO bars.
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
    commandset_block,
    construct_button,
    last_named,
    norm,
    parse_big,
)
from build_germany_airfield_commandset_fix import (
    append_missing_buttons,
    index_named,
    repair_commandset_ini,
)
from build_global_commandbar_crashfix import repair_entries
from build_national_ground_names import upsert_csf
from national_ground_names import NAMES
from national_ground_roster import (
    ALIAS_COMMANDSETS,
    COUNTRIES,
    DO_NOT_PACK_OVERLAY,
    LOCKED_BIG_PATHS,
    PROTECTED_COMMANDSETS,
    all_units,
)

SRC_DATA = Path("/tmp/national_ground_identity/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/national_ground_identity/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/national_ground_commandbar")
# Never write CommandSet/CommandButton under Data\INI\Object\.
# ZH's object parser AVs on that (NationalGroundCommandBar.ini crash).
OBJECT_COMMANDBAR_INI = r"Data\INI\Object\Specter\NationalGround\NationalGroundCommandBar.ini"
IDENTITY_ART_SHA = "e72e6334ab7b9691e3327a0d0a76d4fe771b4cb607e656fa97106e4d69b90c12"


def field(blk: str, name: str):
    m = re.search(rf"(?m)^\s*{name}\s+=\s+(\S+)", blk)
    return m.group(1) if m else None


def country_by_key():
    return {c.key: c for c in COUNTRIES}


def extra_commandsets(country) -> tuple[str, ...]:
    # Only rewrite CommandSets that already exist. Do not invent Set1/2/3.
    return (country.cs, country.cs + "1", country.cs + "2", country.cs + "3")


def all_target_commandsets():
    out = []
    for country in COUNTRIES:
        for name in extra_commandsets(country):
            out.append((name, country))
    by_key = country_by_key()
    for alias, key in ALIAS_COMMANDSETS.items():
        out.append((alias, by_key[key]))
    return out


def last_button_image(entries, btn: str, fallback: str) -> str:
    last = None
    for n, blob in entries:
        if not n.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1")
        m = last_named(text, "CommandButton", btn)
        if m:
            last = field(m.group(0), "ButtonImage")
    return last or fallback


def usa_commandset_block(name: str, buttons: list[str]) -> str:
    """Match AmericaWarFactoryCommandSet slot layout: `  1  =` / `  10 =`."""
    lines = [f"CommandSet {name}\r\n"]
    for i, btn in enumerate(buttons, 1):
        lines.append(f"  {i:<2d} = {btn}\r\n")
    lines.append("End\r\n")
    return "".join(lines)


def rewrite_named_commandsets(text: str, wanted: dict[str, list[str]]) -> str:
    hits = []
    for csname, buttons in wanted.items():
        if csname in PROTECTED_COMMANDSETS:
            raise SystemExit(f"refusing protected CS {csname}")
        m = last_named(text, "CommandSet", csname)
        if m:
            hits.append((m.start(), m.end(), csname, buttons))
    hits.sort(key=lambda x: x[0], reverse=True)
    for start, end, csname, buttons in hits:
        if csname == "Japan_WarFactoryCommandSet":
            new_blk = usa_commandset_block(csname, buttons)
        else:
            new_blk = commandset_block(csname, buttons)
        text = text[:start] + new_blk + text[end:]
        print("rewrote", csname, "slots", len(buttons))
    return text


def build_commandbar_ini(entries) -> str:
    by_key = country_by_key()
    chunks = [
        "; National Ground CommandBar Integration\r\n",
        "; Last-wins CommandSet and CommandButton only. No Object data.\r\n",
        "\r\n",
    ]
    seen_cs = set()
    for csname, country in all_target_commandsets():
        if csname in seen_cs:
            continue
        seen_cs.add(csname)
        buttons = [f"Command_Construct{u.obj}" for u in country.units]
        chunks.append(commandset_block(csname, buttons))
        chunks.append("\r\n")
        print("last-wins CS", csname, country.key)

    seen_btn = set()
    for country, unit in all_units():
        btn = f"Command_Construct{unit.obj}"
        if btn in seen_btn:
            continue
        seen_btn.add(btn)
        image = last_button_image(entries, btn, unit.image)
        chunks.append(
            construct_button(
                btn,
                unit.obj,
                f"CONTROLBAR:Construct{unit.obj}",
                f"CONTROLBAR:ToolTip{unit.obj}",
                image,
            )
        )
        chunks.append("\r\n")
    return "".join(chunks)


def patch_object_display(entries, obj: str, display_key: str) -> None:
    last_i = None
    last_m = None
    for i, (n, blob) in enumerate(entries):
        if not n.lower().endswith(".ini"):
            continue
        if norm(n) in {norm(p) for p in LOCKED_BIG_PATHS}:
            continue
        text = blob.decode("latin1")
        m = last_named(text, "Object", obj)
        if m:
            last_i = i
            last_m = m
    if last_i is None or last_m is None:
        raise SystemExit(f"missing object {obj}")
    n, blob = entries[last_i]
    text = blob.decode("latin1")
    blk = last_m.group(0)
    new_blk, count = re.subn(
        r"(?m)^(\s*DisplayName\s+=\s+)\S+",
        rf"\1{display_key}",
        blk,
        count=1,
    )
    if count != 1:
        raise SystemExit(f"DisplayName missing on {obj}")
    if new_blk == blk:
        return
    if re.sub(r"(?m)^\s*DisplayName\s+=\s+\S+", "", blk) != re.sub(
        r"(?m)^\s*DisplayName\s+=\s+\S+", "", new_blk
    ):
        raise SystemExit(f"non-display change on {obj}")
    text = text[: last_m.start()] + new_blk + text[last_m.end() :]
    entries[last_i] = (n, text.encode("latin1"))
    print("display", obj, "->", display_key, "in", n)


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing identity source BIG", file=sys.stderr)
        return 1
    art_sha = hashlib.sha256(SRC_ART.read_bytes()).hexdigest()
    if art_sha != IDENTITY_ART_SHA:
        raise SystemExit(f"ART SHA is not identity pack {IDENTITY_ART_SHA}")

    wanted_objs = {u.obj for _c, u in all_units()}
    if set(NAMES) != wanted_objs:
        raise SystemExit(
            f"name map mismatch extra={set(NAMES) - wanted_objs} missing={wanted_objs - set(NAMES)}"
        )

    data_entries = parse_big(SRC_DATA)
    src_data_names = [n for n, _ in data_entries]
    data_index = {norm(n): i for i, (n, _) in enumerate(data_entries)}
    src_map = {norm(n): b for n, b in data_entries}

    locked = {norm(p) for p in LOCKED_BIG_PATHS}

    # Crash-repair only. Identity already has the live 14-slot WF bars,
    # DisplayName keys, and CSF. Do not rewrite those. Do not rewrite leftover
    # overlay NATO-clone bars into national rosters; repair_entries strips
    # unbound slots and adds construct buttons only when the Object exists.

    dropped = []
    kept = []
    for n, b in data_entries:
        key = norm(n)
        if key == norm(OBJECT_COMMANDBAR_INI) or (
            "nationalgroundcommandbar.ini" in key and "\\object\\" in key
        ):
            dropped.append(n)
            continue
        kept.append((n, b))
    if dropped:
        data_entries[:] = kept
        data_index.clear()
        data_index.update({norm(n): i for i, (n, _) in enumerate(data_entries)})
        print("removed crashing Object CommandBar INI", dropped)

    repair_entries(data_entries)

    for n, b in data_entries:
        if norm(n) in locked and src_map.get(norm(n)) != b:
            raise SystemExit(f"locked file changed {n}")
    if [n for n, _ in data_entries][: len(src_data_names)] != src_data_names:
        raise SystemExit("DATA entry-order prefix changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(data_entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    shutil.copy2(SRC_ART, OUT_DIR / "_SPEC_ART_ONE.big")
    print("DATA_SHA256", hashlib.sha256(data_big).hexdigest())
    print("ART_SHA256", hashlib.sha256((OUT_DIR / "_SPEC_ART_ONE.big").read_bytes()).hexdigest())
    print("DATA_BYTES", len(data_big), "FILES", len(data_entries))
    print("ART copied unchanged from identity pack")
    return 0


if __name__ == "__main__":
    sys.exit(main())
