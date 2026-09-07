#!/usr/bin/env python3
"""Resolve the Japan airfield CommandSet the way Launch_Specter.bat + ZH load it.

Launch_Specter.bat copies _SPEC_ART_ONE.big and _SPEC_DATA_ONE.big next to
generals.exe. Zero Hour then mounts every *.big in that folder in
case-insensitive alphabetical order. Later same-path wins. Loose Data\\
overrides every BIG.

This is the check that static overlay greps cannot replace. It walks the
actual game folder after the launcher copy step.

Exit 0 only when:
  Japan_Airfield / Japan_LargeAirBase
    -> Japan_JASDF_AirfieldCommandSet
    -> defined in _SPEC_DATA_ONE.big
    -> 12 JASDF fighters
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path

REQUIRED_SET = "Japan_JASDF_AirfieldCommandSet"
REQUIRED_ARCHIVE = "_SPEC_DATA_ONE.big"
REQUIRED_FILE = "data\\ini\\commandset_zzz_japanairforce.ini"
REQUIRED_SLOTS = [
    "Command_ConstructJapan_F35A",
    "Command_ConstructJapan_F35B",
    "Command_ConstructJapan_F15JKai",
    "Command_ConstructJapan_F15DJ",
    "Command_ConstructJapan_F2A",
    "Command_ConstructJapan_F2B",
    "Command_ConstructJapan_X2Shinshin",
    "Command_ConstructJapan_F3GCAP",
    "Command_ConstructJapan_F4EJKai",
    "Command_ConstructJapan_F3",
    "Command_ConstructJapan_F16AJ",
    "Command_ConstructJapan_F2Kai",
]
FORBIDDEN_BUTTON = re.compile(
    r"(Iraq|MiG|SU-?2|mirage|JetF35C|EF2000|CH47|MQ9|JetF16D)",
    re.I,
)
BUILDINGS = ("Japan_Airfield", "Japan_LargeAirBase")


def norm_key(name: str) -> str:
    return name.replace("/", "\\").lower()


def read_big(path: Path) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not a BIGF archive: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out = []
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        out.append((name, data[off : off + size]))
    return out


def big_load_order(game_root: Path) -> list[Path]:
    bigs = [p for p in game_root.iterdir() if p.is_file() and p.suffix.lower() == ".big"]
    return sorted(bigs, key=lambda p: p.name.casefold())


def mount_vfs(game_root: Path) -> tuple[list[Path], dict[str, tuple[str, str, bytes]]]:
    """Return (big_order, vfs). vfs[key] = (archive_or_loose, display_path, bytes)."""
    order = big_load_order(game_root)
    vfs: dict[str, tuple[str, str, bytes]] = {}
    for big in order:
        for name, blob in read_big(big):
            vfs[norm_key(name)] = (big.name, name.replace("/", "\\"), blob)
    data_root = game_root / "Data"
    if data_root.is_dir():
        for path in data_root.rglob("*"):
            if not path.is_file():
                continue
            rel = Path("Data") / path.relative_to(data_root)
            display = str(rel).replace("/", "\\")
            vfs[norm_key(display)] = ("LOOSE Data\\", display, path.read_bytes())
    return order, vfs


def decode(blob: bytes) -> str:
    return blob.decode("latin1", errors="replace")


def iter_command_files(vfs: dict[str, tuple[str, str, bytes]], prefix: str):
    files = []
    for key, (src, display, blob) in vfs.items():
        base = key.replace("\\", "/").rsplit("/", 1)[-1]
        if base.startswith(prefix) and base.endswith(".ini"):
            files.append((key, src, display, blob))
    files.sort(key=lambda item: item[0])
    return files


def parse_named_blocks(text: str, kind: str) -> list[tuple[str, dict[str, str], str]]:
    blocks = []
    pattern = re.compile(
        rf"(?ms)^[ \t]*{kind}[ \t]+(\S+)[ \t]*\n(.*?)^[ \t]*End[ \t]*\n?",
    )
    for m in pattern.finditer(text):
        body = m.group(2)
        fields: dict[str, str] = {}
        for line in body.splitlines():
            line = line.split(";", 1)[0].strip()
            if "=" not in line:
                continue
            left, right = line.split("=", 1)
            fields[left.strip()] = right.strip()
        blocks.append((m.group(1), fields, m.group(0)))
    return blocks


def first_wins(
    files, kind: str
) -> tuple[dict[str, tuple[str, str, dict[str, str]]], list[str]]:
    found: dict[str, tuple[str, str, dict[str, str]]] = {}
    crashes = []
    for _key, src, display, blob in files:
        text = decode(blob)
        for name, fields, _raw in parse_named_blocks(text, kind):
            if name in found:
                prev_src, prev_path, _ = found[name]
                crashes.append(
                    f"{kind} already defined: {name} first={prev_src}:{prev_path} "
                    f"again={src}:{display}"
                )
                continue
            found[name] = (src, display, fields)
    return found, crashes


def object_commandset(text: str, object_name: str) -> str:
    """Read CommandSet from an Object body. Nested Prerequisites/ArmorSet End
    markers must not stop the scan — that is what hid the airfield set."""
    obj_re = re.compile(rf"(?m)^[ \t]*Object[ \t]+{re.escape(object_name)}[ \t]*$")
    m = obj_re.search(text)
    if not m:
        return ""
    rest = text[m.end() :]
    # Prerequisites uses "Object = Foo"; that is not a new Object block.
    nxt = re.search(r"(?m)^[ \t]*Object[ \t]+(?!=)\S+", rest)
    if nxt:
        rest = rest[: nxt.start()]
    cs = re.search(r"(?m)^[ \t]*CommandSet[ \t]*=[ \t]*(\S+)", rest)
    return cs.group(1) if cs else ""


def find_object(vfs, object_name: str):
    matches = []
    obj_re = re.compile(rf"(?m)^[ \t]*Object[ \t]+{re.escape(object_name)}[ \t]*$")
    for key, (src, display, blob) in vfs.items():
        if not key.endswith(".ini"):
            continue
        text = decode(blob)
        if not obj_re.search(text):
            continue
        fields = {"CommandSet": object_commandset(text, object_name)}
        matches.append((key, src, display, fields))
    matches.sort(key=lambda item: item[0])
    return matches


def resolve(game_root: Path) -> dict:
    order, vfs = mount_vfs(game_root)
    cs_files = iter_command_files(vfs, "commandset")
    cb_files = iter_command_files(vfs, "commandbutton")
    commandsets, cs_crashes = first_wins(cs_files, "CommandSet")
    buttons, cb_crashes = first_wins(cb_files, "CommandButton")

    buildings = {}
    for name in BUILDINGS:
        hits = find_object(vfs, name)
        buildings[name] = {
            "definitions": [
                {
                    "source": src,
                    "path": display,
                    "CommandSet": fields.get("CommandSet", ""),
                }
                for _key, src, display, fields in hits
            ],
            "active": None if not hits else hits[0][1:],
        }

    report = {
        "game_root": str(game_root),
        "big_order": [p.name for p in order],
        "has_spec_art": any(p.name == "_SPEC_ART_ONE.big" for p in order),
        "has_spec_data": any(p.name == "_SPEC_DATA_ONE.big" for p in order),
        "inizh_index": next(
            (i for i, p in enumerate(order) if p.name.casefold() == "inizh.big"),
            None,
        ),
        "spec_data_index": next(
            (i for i, p in enumerate(order) if p.name == "_SPEC_DATA_ONE.big"),
            None,
        ),
        "commandset_files": [
            {"source": src, "path": display} for _k, src, display, _b in cs_files
        ],
        "commandsets": commandsets,
        "buttons": buttons,
        "cs_crashes": cs_crashes,
        "cb_crashes": cb_crashes,
        "buildings": buildings,
    }
    return report


def prove(report: dict) -> tuple[bool, list[str], list[str]]:
    lines = []
    fails = []
    order = report["big_order"]
    lines.append("Launch_Specter.bat load (copy two SPEC BIGs, then ZH mounts *.big):")
    for i, name in enumerate(order):
        mark = ""
        if name == "_SPEC_DATA_ONE.big":
            mark = "  <-- required Japan source"
        elif name.casefold() == "inizh.big":
            mark = "  <-- wins Data\\INI\\CommandSet.ini (stock ZH, no Japan)"
        lines.append(f"  {i:02d} {name}{mark}")
    if not report["has_spec_art"] or not report["has_spec_data"]:
        fails.append("game folder is missing _SPEC_ART_ONE.big or _SPEC_DATA_ONE.big")
    if (
        report["spec_data_index"] is not None
        and report["inizh_index"] is not None
        and report["spec_data_index"] > report["inizh_index"]
    ):
        fails.append("unexpected BIG order: _SPEC_DATA_ONE.big loaded after INIZH.big")

    lines.append("")
    lines.append("CommandSet*.ini files in first-definition-wins order:")
    for item in report["commandset_files"]:
        lines.append(f"  {item['source']} -> {item['path']}")

    lines.append("")
    for name in BUILDINGS:
        info = report["buildings"][name]
        defs = info["definitions"]
        lines.append(f"Object {name}: {len(defs)} definition(s)")
        if not defs:
            fails.append(f"{name} is not defined after Launch_Specter load")
            continue
        if len(defs) > 1:
            fails.append(f"{name} is defined {len(defs)} times (Object already defined)")
        src, path, fields = info["active"]
        used = fields.get("CommandSet", "")
        lines.append(f"  source: {src} -> {path}")
        lines.append(f"  CommandSet = {used}")
        if used != REQUIRED_SET:
            fails.append(f"{name} uses {used or '(none)'}, expected {REQUIRED_SET}")

    cs = report["commandsets"].get(REQUIRED_SET)
    lines.append("")
    if not cs:
        fails.append(f"{REQUIRED_SET} is not defined after Launch_Specter load")
        lines.append(f"{REQUIRED_SET}: MISSING")
    else:
        src, path, fields = cs
        lines.append(f"{REQUIRED_SET}:")
        lines.append(f"  source archive: {src}")
        lines.append(f"  source file:    {path}")
        slots = []
        for i in range(1, 13):
            btn = fields.get(str(i), "")
            slots.append(btn)
            obj = ""
            if btn in report["buttons"]:
                obj = report["buttons"][btn][2].get("Object", "")
            lines.append(f"  {i:2d} = {btn} -> {obj or '(no CommandButton)'}")
            if btn != REQUIRED_SLOTS[i - 1]:
                fails.append(f"slot {i} is {btn or '(empty)'}, expected {REQUIRED_SLOTS[i - 1]}")
            if FORBIDDEN_BUTTON.search(btn):
                fails.append(f"slot {i} is a leftover Iraq/NATO button: {btn}")
            if not obj:
                fails.append(f"slot {i} button {btn} has no CommandButton Object")
        if src != REQUIRED_ARCHIVE:
            fails.append(
                f"{REQUIRED_SET} source is {src}, expected {REQUIRED_ARCHIVE}"
            )
        if norm_key(path) != REQUIRED_FILE:
            fails.append(
                f"{REQUIRED_SET} file is {path}, expected CommandSet_zzz_JapanAirForce.ini"
            )
        if src.startswith("LOOSE"):
            fails.append(f"{REQUIRED_SET} was overridden by a loose Data\\ file")

    old = report["commandsets"].get("Japan_AirfieldCommandSet")
    if old:
        src, path, fields = old
        slots = ", ".join(fields.get(str(i), "-") for i in range(1, 8))
        lines.append("")
        lines.append(
            f"NOTE: leftover Japan_AirfieldCommandSet exists in {src} -> {path}"
        )
        lines.append(f"      slots 1-7: {slots}")
        lines.append("      Buildings must not use this name.")

    if report["cs_crashes"]:
        lines.append("")
        lines.append("CommandSet already defined:")
        for row in report["cs_crashes"]:
            lines.append(f"  {row}")
            if REQUIRED_SET in row:
                fails.append(row)

    ok = not fails
    lines.append("")
    if ok:
        lines.append(
            "PROOF: Launch_Specter load uses "
            f"{REQUIRED_ARCHIVE} -> {REQUIRED_SET} -> 12 fighters."
        )
    else:
        lines.append("PROOF FAILED:")
        for row in fails:
            lines.append(f"  - {row}")
    return ok, lines, fails


def write_debug(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-root", type=Path, required=True)
    ap.add_argument("--write-debug", action="store_true")
    ap.add_argument("--debug-path", type=Path)
    args = ap.parse_args()
    game_root = args.game_root.resolve()
    if not game_root.is_dir():
        print(f"ERROR: game folder not found: {game_root}", file=sys.stderr)
        return 2
    report = resolve(game_root)
    ok, lines, _fails = prove(report)
    text = "\n".join(lines)
    print(text)
    if args.write_debug or args.debug_path:
        out = args.debug_path or (game_root / "SPECTER_JAPAN_AIRFIELD_DEBUG.txt")
        write_debug(out, lines)
        print(f"\nWrote {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
