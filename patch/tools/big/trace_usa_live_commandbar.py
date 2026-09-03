#!/usr/bin/env python3
"""Resolve the CommandSets the game UI actually uses.

Simulates Zero Hour archive order: every *.big in the game folder
(case-insensitive alpha), later same-path wins, then loose Data\\
overrides every BIG. Then traces:

  Building object -> CommandSet -> CommandButton -> Object

and draws the 14-button ControlBar grid from ControlBar.wnd comments.
This is the live building CommandSet, not an unused unique file.
"""

from __future__ import annotations

import argparse
import re
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

GRID = [1, 3, 5, 7, 9, 11, 13, 2, 4, 6, 8, 10, 12, 14]

BUILDINGS = {
    "AmericaCommandCenter": {
        "want_set": "AmericaCommandCenterCommandSet",
        "must": {3: "Command_UpgradeAmerica_AirForceBombs"},
    },
    "AmericaAirfield": {
        "want_set": "AmericaAirfieldCommandSet",
        "must": {
            5: "Command_ConstructAmericaJetF35C_AA",
            6: "Command_ConstructAmerica_AuterF22",
        },
        "keep": {
            1: "Command_ConstructAmericaJetRaptor",
            2: "Command_ConstructAmericaVehicleComanche",
            3: "Command_ConstructAmericaJetAurora",
            4: "Command_ConstructAmericaJetStealthFighter",
        },
    },
    "America_LargeAirBase": {
        "want_set": "America_LargeAirBaseCommandSet",
        "must": {9: "Command_ConstructAmerica_B21A"},
        "keep_heavies": {
            10: "Command_ConstructAmericaJetEA18",
            13: "Command_ConstructAmericaJetF117",
        },
    },
}


def read_big_index(path: Path):
    data = path.read_bytes()
    if data[:4] not in (b"BIGF", b"BIG4"):
        return {}
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files = {}
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace").replace("/", "\\")
        pos = end + 1
        files[name.lower()] = data[off : off + size]
    return files


def mount_game_folder(game_root: Path) -> dict[str, bytes]:
    mounted: dict[str, bytes] = {}
    sources: dict[str, str] = {}
    bigs = sorted(
        [p for p in game_root.iterdir() if p.suffix.lower() == ".big"],
        key=lambda p: p.name.lower(),
    )
    for big in bigs:
        files = read_big_index(big)
        for key, blob in files.items():
            mounted[key] = blob
            sources[key] = big.name
    data_dir = game_root / "Data"
    if data_dir.is_dir():
        for path in data_dir.rglob("*"):
            if not path.is_file():
                continue
            rel = "Data\\" + str(path.relative_to(data_dir)).replace("/", "\\")
            mounted[rel.lower()] = path.read_bytes()
            sources[rel.lower()] = f"LOOSE:{rel}"
    return mounted


def decode(blob: bytes) -> str:
    return blob.decode("latin1", errors="replace")


def find_object_block(mounted: dict[str, bytes], obj: str) -> tuple[str, str]:
    """Last-parsed Object block wins when names collide (INIZH then Specter).

    ZH fatally errors on a second Object definition. In practice the first
    definition from FactionBuilding.ini is the live USA CC/Airfield. Prefer
    FactionBuilding.ini when present; otherwise last match.
    """
    faction = None
    last = None
    pat = re.compile(rf"^Object\s+{re.escape(obj)}\s*$", re.M)
    for key, blob in mounted.items():
        if not key.endswith(".ini"):
            continue
        text = decode(blob)
        for m in pat.finditer(text):
            nxt = re.search(r"^Object\s+", text[m.end() :], re.M)
            block = text[m.start() : m.end() + nxt.start() if nxt else m.start() + 6000]
            last = (key, block)
            if key.endswith(r"object\factionbuilding.ini"):
                faction = (key, block)
    if obj in ("AmericaCommandCenter", "AmericaAirfield") and faction:
        return faction
    if last:
        return last
    raise SystemExit(f"Object {obj} not found in mounted game files")


def parse_commandset(text: str, name: str) -> dict[int, str]:
    m = re.search(rf"^CommandSet\s+{re.escape(name)}\s*$", text, re.M)
    if not m:
        return {}
    nxt = re.search(r"^End\s*$", text[m.end() :], re.M)
    block = text[m.start() : m.end() + nxt.end() if nxt else m.start() + 800]
    return {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M)}


def parse_button(text: str, name: str) -> dict[str, str]:
    m = re.search(rf"^CommandButton\s+{re.escape(name)}\s*$", text, re.M)
    if not m:
        return {}
    nxt = re.search(r"^End\s*$", text[m.end() :], re.M)
    block = text[m.start() : m.end() + nxt.end() if nxt else m.start() + 400]
    out = {}
    for k in ("Command", "Object", "Upgrade", "TextLabel", "ButtonImage"):
        mm = re.search(rf"^\s*{k}\s*=\s*(\S+)", block, re.M)
        if mm:
            out[k] = mm.group(1)
    return out


def short_label(button: str, info: dict[str, str]) -> str:
    obj = info.get("Object") or info.get("Upgrade") or ""
    obj = obj.replace("AmericaJet", "").replace("America", "").replace("Command_", "")
    if button.endswith("F35C_AA"):
        return "F-35B JSF"
    if button.endswith("AuterF22"):
        return "Auter F22"
    if button.endswith("B21A"):
        return "B-21A"
    if button.endswith("AirForceBombs"):
        return "AF Bombs"
    if button.endswith("StealthFighter"):
        return "F-22 AG"
    if button.endswith("JetRaptor"):
        return "Raptor"
    if button.endswith("Comanche"):
        return "Comanche"
    if button.endswith("Aurora"):
        return "Aurora"
    if button.endswith("JetF117"):
        return "F-117"
    if button.endswith("JetEA18"):
        return "EA-18"
    if button.endswith("Dozer"):
        return "Dozer"
    if button.endswith("Sell"):
        return "Sell"
    if button.endswith("SetRallyPoint"):
        return "Rally"
    return (obj or button.replace("Command_", ""))[:16]


def render_bar(title: str, slots: dict[int, str], infos: dict[str, dict], out: Path) -> None:
    w, h = 980, 280
    img = Image.new("RGB", (w, h), (18, 22, 28))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except OSError:
        font = font_sm = font_b = ImageFont.load_default()
    draw.text((16, 10), title, fill=(230, 230, 230), font=font_b)
    cell_w, cell_h = 128, 88
    x0, y0 = 16, 44
    for i, slot in enumerate(GRID):
        col = i % 7
        row = i // 7
        x = x0 + col * (cell_w + 8)
        y = y0 + row * (cell_h + 10)
        btn = slots.get(slot)
        if btn:
            info = infos.get(btn, {})
            highlight = btn in {
                "Command_UpgradeAmerica_AirForceBombs",
                "Command_ConstructAmericaJetF35C_AA",
                "Command_ConstructAmerica_AuterF22",
                "Command_ConstructAmerica_B21A",
            }
            fill = (36, 92, 48) if highlight else (42, 52, 68)
            outline = (120, 220, 140) if highlight else (90, 110, 130)
            label = short_label(btn, info)
        else:
            fill, outline, label = (28, 32, 40), (55, 60, 70), ""
        draw.rectangle([x, y, x + cell_w, y + cell_h], fill=fill, outline=outline, width=2)
        draw.text((x + 6, y + 6), f"{slot:02d}", fill=(180, 190, 200), font=font_sm)
        if label:
            draw.text((x + 6, y + 28), label, fill=(250, 250, 250), font=font)
            target = infos.get(btn, {}).get("Object") or infos.get(btn, {}).get("Upgrade") or ""
            if target:
                draw.text((x + 6, y + 50), target[:18], fill=(180, 210, 180), font=font_sm)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-root", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    mounted = mount_game_folder(args.game_root)
    cs_blob = mounted.get(r"data\ini\commandset.ini")
    cb_blob = mounted.get(r"data\ini\commandbutton.ini")
    if not cs_blob or not cb_blob:
        raise SystemExit("mounted game folder missing CommandSet.ini or CommandButton.ini")
    cs_text = decode(cs_blob)
    cb_text = decode(cb_blob)

    errors: list[str] = []
    report = []
    report.append(f"Game root: {args.game_root}")
    report.append("Mounted CommandSet.ini / CommandButton.ini after BIG alpha + loose Data")
    report.append("")

    unused = [
        "AmericaAirfieldCommandSet_USAAirForce",
        "AmericaCommandCenterCommandSet_USAAirForce",
    ]
    for name in unused:
        if re.search(rf"^CommandSet\s+{re.escape(name)}\s*$", cs_text, re.M):
            errors.append(f"unused CommandSet still present in live CommandSet.ini: {name}")

    for obj, spec in BUILDINGS.items():
        src, block = find_object_block(mounted, obj)
        m = re.search(r"^\s*CommandSet\s+=\s+(\S+)", block, re.M)
        used = m.group(1) if m else ""
        report.append(f"BUILDING {obj}")
        report.append(f"  defined in {src}")
        report.append(f"  CommandSet = {used}")
        if used != spec["want_set"]:
            errors.append(f"{obj} uses {used}, expected {spec['want_set']}")
        slots = parse_commandset(cs_text, used)
        if not slots:
            errors.append(f"{obj} CommandSet {used} is empty/missing in live CommandSet.ini")
        infos = {}
        for slot, btn in sorted(slots.items()):
            info = parse_button(cb_text, btn)
            infos[btn] = info
            target = info.get("Object") or info.get("Upgrade") or "MISSING_BUTTON"
            visible = "VISIBLE" if 1 <= slot <= 14 else "INVISIBLE"
            report.append(f"  [{visible} {slot:02d}] {btn} -> {target}")
            if not info:
                errors.append(f"{used} slot {slot} button {btn} is not in live CommandButton.ini")
            if 1 <= slot <= 14 and info.get("Command") == "UNIT_BUILD" and not info.get("Object"):
                errors.append(f"{btn} UNIT_BUILD has no Object")
        for slot, btn in spec.get("must", {}).items():
            if slots.get(slot) != btn:
                errors.append(f"{obj} visible slot {slot} is {slots.get(slot)!r}, expected {btn}")
            elif slot > 14:
                errors.append(f"{btn} is not on a visible ControlBar slot")
        for slot, btn in spec.get("keep", {}).items():
            if slots.get(slot) != btn:
                errors.append(f"{obj} lost existing aircraft slot {slot} {btn}")
        for slot, btn in spec.get("keep_heavies", {}).items():
            if slots.get(slot) != btn:
                errors.append(f"{obj} lost existing heavy slot {slot} {btn}")
        png = args.out_dir / f"{obj}_commandbar.png"
        render_bar(f"{obj}  ->  {used}", slots, infos, png)
        report.append(f"  rendered {png}")
        report.append("")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "usa_live_commandset_trace.txt").write_text("\n".join(report) + "\n", "utf-8")
    print("\n".join(report))
    if errors:
        print("LIVE COMMANDSET TRACE FAILED")
        for e in errors:
            print("  ERROR:", e)
        return 1
    print("LIVE COMMANDSET TRACE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
