#!/usr/bin/env python3
"""Twelve V25 China systems onto SPECTER SS2 China Command Center.

Merges onto the America V25 CC6 ControlBar (loaders + America packs).
Replaces only China CC slots 13 Rally and 14 Sell. Does not edit Command_Sell
or Command_SetRallyPoint definitions, nor other factions' Rally/Sell slots.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ss2_tunnel_loader"))
from apply_turkey_method import FACTIONS  # noqa: E402

TOOL = Path(__file__).resolve().parent
SRC_CS = Path("patch/Release/SPECTER_SS2_USA_V25_CC6/Data/INI/CommandSet.ini")
SRC_CB = Path("patch/Release/SPECTER_SS2_USA_V25_CC6/Data/INI/CommandButton.ini")
SRC_MAP = TOOL / "ChinaV25CC12_Images.ini"
OUT_DIR = Path("patch/Release/SPECTER_SS2_CHINA_V25_CC12")
CS_NAME = "ChinaCommandCenterCommandSet"
ART_SRC = TOOL / "art"
OBJ_DIR = "Object/Specter/PLA/V25CommandCenter"
MAP_REL = "MappedImages/HandCreated/ChinaV25CC12_Images.ini"
USA_CS = "AmericaCommandCenterCommandSet"

SYSTEMS = [
    {"slot": 2, "btn": "Command_ConstructChinaVehicleV25FK2000", "obj": "ChinaVehicleV25FK2000", "ini": "ChinaVehicleV25FK2000.ini", "model": "FK2000", "image": "FK2000TB", "w3d": "FK2000.W3D", "need": [b"TIRE01", b"TIRE08", b"SYSTEM", b"ANGLE"], "draw": "W3DTruckDraw", "label": "FK-2000"},
    {"slot": 3, "btn": "Command_ConstructChinaVehicleV25AFT10", "obj": "ChinaVehicleV25AFT10", "ini": "ChinaVehicleV25AFT10.ini", "model": "CHAFT10", "image": "AFT10TB", "w3d": "CHAFT10.W3D", "need": [b"TURRET01", b"MISS01"], "draw": "W3DTankDraw", "label": "AFT-10"},
    {"slot": 5, "btn": "Command_ConstructChinaVehicleV25HQ11", "obj": "ChinaVehicleV25HQ11", "ini": "ChinaVehicleV25HQ11.ini", "model": "HQ11", "image": "CHHQ11TB", "w3d": "HQ11.W3D", "need": [b"WHEEL01", b"WHEEL08", b"MISSILE_C01"], "draw": "W3DTruckDraw", "label": "HQ-11"},
    {"slot": 6, "btn": "Command_ConstructChinaVehicleV25LD2000", "obj": "ChinaVehicleV25LD2000", "ini": "ChinaVehicleV25LD2000.ini", "model": "SDLD2000", "image": "LD2000TB", "w3d": "SDLD2000.W3D", "need": [b"TIRE01", b"TURRET", b"TURRETHEL"], "draw": "W3DTruckDraw", "label": "LD-2000"},
    {"slot": 7, "btn": "Command_ConstructChinaVehicleV25HQ9", "obj": "ChinaVehicleV25HQ9", "ini": "ChinaVehicleV25HQ9.ini", "model": "SDCHH9", "image": "HQ9", "w3d": "SDCHH9.W3D", "need": [b"WHEEL01", b"WHEEL08", b"MISSILE_C01"], "draw": "W3DTruckDraw", "label": "HQ-9"},
    {"slot": 8, "btn": "Command_ConstructChinaVehicleV25HT233", "obj": "ChinaVehicleV25HT233", "ini": "ChinaVehicleV25HT233.ini", "model": "SDHT233", "image": "ZZM88", "w3d": "SDHT233.W3D", "need": [b"WHEEL01", b"WHEEL06"], "draw": "W3DTruckDraw", "label": "HT-233 Radar", "ini_forbid_bones": [r"Wheel0[789]", r"WHEEL1"]},
    {"slot": 9, "btn": "Command_ConstructChinaVehicleV25HQ16", "obj": "ChinaVehicleV25HQ16", "ini": "ChinaVehicleV25HQ16.ini", "model": "SDHQ16", "image": "HQ16TB", "w3d": "SDHQ16.W3D", "need": [b"WHEEL01", b"WHEEL06", b"MISSILE_C01"], "draw": "W3DTruckDraw", "label": "HQ-16", "ini_forbid_bones": [r"Wheel0[78]"]},
    {"slot": 10, "btn": "Command_ConstructChinaVehicleV25HQ7B", "obj": "ChinaVehicleV25HQ7B", "ini": "ChinaVehicleV25HQ7B.ini", "model": "SDHQ7", "image": "HQ7BTB", "w3d": "SDHQ7.W3D", "need": [b"TURRET", b"WHEEL01", b"MUZZLE01"], "draw": "W3DTruckDraw", "label": "HQ-7B", "no_pitch": True},
    {"slot": 11, "btn": "Command_ConstructChinaVehicleV25HQ7BRadar", "obj": "ChinaVehicleV25HQ7BRadar", "ini": "ChinaVehicleV25HQ7BRadar.ini", "model": "HQ7RD", "image": "HQ7BRD", "w3d": "HQ7RD.W3D", "need": [b"WHEEL01", b"WHEEL06"], "draw": "W3DTruckDraw", "label": "HQ-7B Radar"},
    {"slot": 12, "btn": "Command_ConstructChinaVehicleV25YJ62A", "obj": "ChinaVehicleV25YJ62A", "ini": "ChinaVehicleV25YJ62A.ini", "model": "SDYJ62A", "image": "YJ62ATB", "w3d": "SDYJ62A.W3D", "need": [b"KOLESO01", b"TURRET", b"WEAPONA01"], "draw": "W3DTruckDraw", "label": "YJ-62A", "no_pitch": True},
    {"slot": 13, "btn": "Command_ConstructChinaVehicleV25CJ10", "obj": "ChinaVehicleV25CJ10", "ini": "ChinaVehicleV25CJ10.ini", "model": "SDCJ10", "image": "CJ10TB", "w3d": "SDCJ10.W3D", "need": [b"KOLESO01", b"TURRET", b"TURRETEL"], "draw": "W3DTruckDraw", "label": "CJ-10"},
    {"slot": 14, "btn": "Command_ConstructChinaVehicleV25WS3", "obj": "ChinaVehicleV25WS3", "ini": "ChinaVehicleV25WS3.ini", "model": "SDCHWS2", "image": "WS3TB", "w3d": "SDCHWS2.W3D", "need": [b"TIRE01", b"TURRET", b"TURRETEL"], "draw": "W3DTruckDraw", "label": "WS-3"},
]

ART_FILES = [
    ("W3D/FK2000.W3D", "Art/W3D/FK2000.W3D"),
    ("W3D/CHAFT10.W3D", "Art/W3D/CHAFT10.W3D"),
    ("W3D/HQ11.W3D", "Art/W3D/HQ11.W3D"),
    ("W3D/SDLD2000.W3D", "Art/W3D/SDLD2000.W3D"),
    ("W3D/SDCHH9.W3D", "Art/W3D/SDCHH9.W3D"),
    ("W3D/SDHT233.W3D", "Art/W3D/SDHT233.W3D"),
    ("W3D/SDHQ16.W3D", "Art/W3D/SDHQ16.W3D"),
    ("W3D/SDHQ7.W3D", "Art/W3D/SDHQ7.W3D"),
    ("W3D/HQ7RD.W3D", "Art/W3D/HQ7RD.W3D"),
    ("W3D/SDYJ62A.W3D", "Art/W3D/SDYJ62A.W3D"),
    ("W3D/SDCJ10.W3D", "Art/W3D/SDCJ10.W3D"),
    ("W3D/SDCHWS2.W3D", "Art/W3D/SDCHWS2.W3D"),
    ("Textures/FK2000TB.tga", "Art/Textures/FK2000TB.tga"),
    ("Textures/AFT10TB.tga", "Art/Textures/AFT10TB.tga"),
    ("Textures/CHHQ11TB.tga", "Art/Textures/CHHQ11TB.tga"),
    ("Textures/LD2000TB.tga", "Art/Textures/LD2000TB.tga"),
    ("Textures/HQ9TB.tga", "Art/Textures/HQ9TB.tga"),
    ("Textures/ZZM88.tga", "Art/Textures/ZZM88.tga"),
    ("Textures/HQ16TB.tga", "Art/Textures/HQ16TB.tga"),
    ("Textures/HQ7BTB.tga", "Art/Textures/HQ7BTB.tga"),
    ("Textures/HQ7BRD.tga", "Art/Textures/HQ7BRD.tga"),
    ("Textures/YJ62ATB.tga", "Art/Textures/YJ62ATB.tga"),
    ("Textures/CJ10TB.tga", "Art/Textures/CJ10TB.tga"),
    ("Textures/WS3TB.tga", "Art/Textures/WS3TB.tga"),
    ("Textures/CHAFT10B.dds", "Art/Textures/CHAFT10B.dds"),
    ("Textures/CHAFT10W.dds", "Art/Textures/CHAFT10W.dds"),
    ("Textures/CHHQ11B.dds", "Art/Textures/CHHQ11B.dds"),
    ("Textures/CHHQ11F.dds", "Art/Textures/CHHQ11F.dds"),
    ("Textures/CHHQ11G.dds", "Art/Textures/CHHQ11G.dds"),
    ("Textures/CHHQ11N.dds", "Art/Textures/CHHQ11N.dds"),
    ("Textures/CHHQ11R.dds", "Art/Textures/CHHQ11R.dds"),
    ("Textures/CHHQ11T.dds", "Art/Textures/CHHQ11T.dds"),
    ("Textures/CHHQ16I.dds", "Art/Textures/CHHQ16I.dds"),
    ("Textures/Glass1.tga", "Art/Textures/Glass1.tga"),
    ("Textures/M163VULCAN_IL.dds", "Art/Textures/M163VULCAN_IL.dds"),
    ("Textures/SDCHHQ16.dds", "Art/Textures/SDCHHQ16.dds"),
    ("Textures/SDCHHQ7.dds", "Art/Textures/SDCHHQ7.dds"),
    ("Textures/SDCHHQ7R.dds", "Art/Textures/SDCHHQ7R.dds"),
    ("Textures/SDCHHQ7T.dds", "Art/Textures/SDCHHQ7T.dds"),
    ("Textures/SDCHHQ9.dds", "Art/Textures/SDCHHQ9.dds"),
    ("Textures/SDCHWS2.dds", "Art/Textures/SDCHWS2.dds"),
    ("Textures/SDCJ10.dds", "Art/Textures/SDCJ10.dds"),
    ("Textures/SDFK2000.dds", "Art/Textures/SDFK2000.dds"),
    ("Textures/SDLD2000.dds", "Art/Textures/SDLD2000.dds"),
    ("Textures/SDNSM04.dds", "Art/Textures/SDNSM04.dds"),
    ("Textures/SDYJ63AL.dds", "Art/Textures/SDYJ63AL.dds"),
]

CHINA_KEEP = {
    1: "Command_ConstructChinaDozer",
    4: "Command_ConstructChinaVehicleDozerm",
}
USA_KEEP = {
    1: "Command_ConstructAmericaDozer",
    4: "Command_ConstructAmericaVehicleDozerm",
    6: "Command_ConstructUSAPAC3",
    10: "Command_ConstructAmericaVehiclePatriotPAC3",
    11: "Command_ConstructAmericaVehiclePatriotPAC3MSE",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def parse_blocks(text: str, kind: str) -> dict[str, str]:
    out: dict[str, str] = {}
    matches = list(re.finditer(rf"(?m)^{kind}\s+(\S+)\s*$", text))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[m.group(1)] = text[start:end]
    return out


def slots_of(block: str) -> dict[int, str]:
    return {int(a): b for a, b in re.findall(r"(?m)^\s*(\d+)\s*=\s*(\S+)", block)}


def button_core(block: str) -> str:
    lines = []
    for line in block.splitlines():
        lines.append(line.rstrip())
        if line.strip() == "End":
            break
    return "\n".join(lines)


def unique_count(names: list[str], label: str) -> None:
    if len(names) != len(set(names)):
        dups = [n for n in set(names) if names.count(n) > 1]
        raise SystemExit(f"duplicate {label}: {dups}")


def verify_w3d(path: Path, need: list[bytes]) -> None:
    data = path.read_bytes().upper()
    missing = [n.decode() for n in need if n.upper() not in data]
    if missing:
        raise SystemExit(f"{path.name} missing bones {missing}")


def btn_block(sys: dict) -> str:
    return (
        f"CommandButton {sys['btn']}\n"
        f"  Command            = UNIT_BUILD\n"
        f"  Object             = {sys['obj']}\n"
        f"  TextLabel          = CONTROLBAR:Construct{sys['obj']}\n"
        f"  ButtonImage        = {sys['image']}\n"
        f"  ButtonBorderType   = BUILD\n"
        f"  DescriptLabel      = CONTROLBAR:ToolTip{sys['obj']}\n"
        f"End\n"
    )


def rewrite_china_cc(cs: str, additions: dict[int, str]) -> str:
    pattern = rf"(?ms)^(CommandSet {re.escape(CS_NAME)}\s*\n)(.*?)(^End\s*$)"

    def repl(m: re.Match[str]) -> str:
        occupied = slots_of(m.group(2))
        if occupied.get(13) != "Command_SetRallyPoint":
            raise SystemExit(f"China slot 13 is {occupied.get(13)}, expected Rally")
        if occupied.get(14) != "Command_Sell":
            raise SystemExit(f"China slot 14 is {occupied.get(14)}, expected Sell")
        lines = []
        for line in m.group(2).splitlines(True):
            mm = re.match(r"\s*(\d+)\s*=", line)
            if mm and int(mm.group(1)) in (13, 14):
                continue
            lines.append(line)
        body = "".join(lines)
        if not body.endswith("\n"):
            body += "\n"
        for slot, button in additions.items():
            if slot in occupied and slot not in (13, 14):
                raise SystemExit(f"{CS_NAME} slot {slot} already occupied by {occupied[slot]}")
            body += f"  {slot} = {button}\n"
        return m.group(1) + body + m.group(3)

    new, n = re.subn(pattern, repl, cs, count=1)
    if n != 1:
        raise SystemExit("failed to patch China Command Center")
    return new


def check_object(sys: dict, text: str) -> None:
    objs = parse_blocks(text, "Object")
    if sys["obj"] not in objs:
        raise SystemExit(f"missing object {sys['obj']}")
    block = objs[sys["obj"]]
    if not re.search(rf"(?m)^\s*Draw\s*=\s*{sys['draw']}", block):
        raise SystemExit(f"{sys['obj']} Draw must be {sys['draw']}")
    if re.search(rf"(?m)^\s*Model\s*=\s*{re.escape(sys['model'])}\b", block) is None:
        raise SystemExit(f"{sys['obj']} must use Model {sys['model']}")
    if "DeployStyleAIUpdate" in block or "AttachToBoneInAnotherModule" in block:
        raise SystemExit(f"{sys['obj']} deploy/attach not allowed")
    if sys["draw"] == "W3DTruckDraw" and "Generic8x8Locomotor" not in block:
        raise SystemExit(f"{sys['obj']} missing Generic8x8Locomotor")
    if sys["draw"] == "W3DTankDraw" and "CrusaderLocomotor" not in block:
        raise SystemExit(f"{sys['obj']} missing CrusaderLocomotor")
    if re.search(r"(?m)^\s*KindOf\s*=.*FS_BASE_DEFENSE", block):
        raise SystemExit(f"{sys['obj']} FS_BASE_DEFENSE not allowed")
    if re.search(r"(?m)^\s*Shadow\s*=", block):
        raise SystemExit(f"{sys['obj']} must not set Shadow")
    if sys.get("no_pitch") and re.search(r"(?m)^\s*TurretPitch\s*=", block):
        raise SystemExit(f"{sys['obj']} must not set TurretPitch")
    for pat in sys.get("ini_forbid_bones", []):
        if re.search(rf"(?m)^\s*\S+TireBone\s*=\s*{pat}", block):
            raise SystemExit(f"{sys['obj']} mapped forbidden bone {pat}")
    if any(name in ("ChinaTankWS3", "ChinaVehicleHQ9", "ChinaVehicleHT233") for name in objs):
        raise SystemExit(f"{sys['obj']} reused a live SS2/V25 substitute object")
    if sys["obj"] == "ChinaVehicleV25CJ10" and re.search(r"(?m)^\s*Model\s*=\s*SDYJ62A\b", block):
        raise SystemExit("CJ-10 must not use YJ-62A model")
    if sys["obj"] == "ChinaVehicleV25WS3" and re.search(r"(?m)^\s*Model\s*=\s*SDPHL03\b", block):
        raise SystemExit("WS-3 must not use PHL-03 model")


def main() -> int:
    import subprocess

    subprocess.check_call([sys.executable, str(TOOL / "write_objects.py")])
    if not SRC_CS.is_file() or not SRC_CB.is_file():
        raise SystemExit(f"CC6 ControlBar missing: {SRC_CS}")

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    src_cs = SRC_CS.read_text("latin1").replace("\r\n", "\n")
    src_cb = SRC_CB.read_text("latin1").replace("\r\n", "\n")
    cs_blocks = parse_blocks(src_cs, "CommandSet")
    cb_blocks = parse_blocks(src_cb, "CommandButton")
    unique_count(list(cs_blocks), "source CommandSet.ini")
    unique_count(list(cb_blocks), "source CommandButton.ini")

    china = slots_of(cs_blocks[CS_NAME])
    for slot, btn in CHINA_KEEP.items():
        if china.get(slot) != btn:
            raise SystemExit(f"China slot {slot} is {china.get(slot)}, expected {btn}")
    usa = slots_of(cs_blocks[USA_CS])
    for slot, btn in USA_KEEP.items():
        if usa.get(slot) != btn:
            raise SystemExit(f"America slot {slot} is {usa.get(slot)}, expected {btn}")

    new_btns = [s["btn"] for s in SYSTEMS]
    unique_count(new_btns, "new buttons")
    forbidden_btns = {
        "Command_ConstructChinaVehicleHQ9",
        "Command_ConstructChinaVehicleHT233",
        "Command_ConstructChinaVehicleListeningOutpost",
        "Command_Sell",
        "Command_SetRallyPoint",
    }
    for btn in new_btns:
        if btn in cb_blocks:
            raise SystemExit(f"button already exists {btn}")
        if btn in forbidden_btns:
            raise SystemExit(f"must not reuse {btn}")

    sell_btn_before = cb_blocks["Command_Sell"]
    rally_btn_before = cb_blocks["Command_SetRallyPoint"]
    turkey_before = cs_blocks["TurkeyCommandCenterCommandSet"]
    gla_before = cs_blocks["GLACommandCenterCommandSet"]
    usa_before = cs_blocks[USA_CS]
    china_up_before = cs_blocks["ChinaCommandCenterCommandSetUpgrade"]
    pla_before = cs_blocks["PLACommandCenterCommandSet"]

    missing_loader_sets = []
    for fac in FACTIONS:
        occupied = slots_of(cs_blocks[fac["cs"]])
        loader_btn = f"Command_Construct{fac['loader']}"
        if occupied.get(fac["slot"]) != loader_btn:
            raise SystemExit(f"{fac['side']} loader slot missing")
        if loader_btn not in cb_blocks:
            raise SystemExit(f"tunnel button missing {loader_btn}")
        if f"{fac['loader']}CommandSet" not in cs_blocks:
            missing_loader_sets.append(f"{fac['loader']}CommandSet")
    if missing_loader_sets:
        raise SystemExit(f"tunnel unique CommandSets missing: {missing_loader_sets}")
    if len(FACTIONS) != 26:
        raise SystemExit("expected 26 factions")

    additions = {s["slot"]: s["btn"] for s in SYSTEMS}
    new_cs = rewrite_china_cc(src_cs, additions)
    btn_text = "\n".join(btn_block(s) for s in SYSTEMS)
    new_cb = src_cb.rstrip() + "\n\n; SPECTER SS2 China V25 Command Center systems.\n\n" + btn_text

    new_cs_blocks = parse_blocks(new_cs, "CommandSet")
    new_cb_blocks = parse_blocks(new_cb, "CommandButton")
    unique_count(list(new_cs_blocks), "patched CommandSet.ini")
    unique_count(list(new_cb_blocks), "patched CommandButton.ini")
    if set(new_cs_blocks) != set(cs_blocks):
        raise SystemExit("CommandSet names were added or removed")
    if set(new_cb_blocks) - set(cb_blocks) != set(new_btns):
        raise SystemExit(f"unexpected CommandButton delta: {set(new_cb_blocks) - set(cb_blocks)}")

    won = slots_of(new_cs_blocks[CS_NAME])
    for s in SYSTEMS:
        if won[s["slot"]] != s["btn"]:
            raise SystemExit(f"slot {s['slot']} patch failed")
    for slot, btn in CHINA_KEEP.items():
        if won[slot] != btn:
            raise SystemExit(f"kept China slot {slot} lost")
    if "Command_Sell" in won.values() or "Command_SetRallyPoint" in won.values():
        raise SystemExit("China CC still has Sell or Rally")
    if new_cs_blocks[USA_CS] != usa_before:
        raise SystemExit("America CC changed")
    if new_cs_blocks["TurkeyCommandCenterCommandSet"] != turkey_before:
        raise SystemExit("Turkey CC changed")
    if new_cs_blocks["GLACommandCenterCommandSet"] != gla_before:
        raise SystemExit("GLA CC changed")
    if new_cs_blocks["ChinaCommandCenterCommandSetUpgrade"] != china_up_before:
        raise SystemExit("China CC Upgrade set changed")
    if new_cs_blocks["PLACommandCenterCommandSet"] != pla_before:
        raise SystemExit("PLA CC changed")
    if button_core(new_cb_blocks["Command_Sell"]) != button_core(sell_btn_before):
        raise SystemExit("Command_Sell definition changed")
    if button_core(new_cb_blocks["Command_SetRallyPoint"]) != button_core(rally_btn_before):
        raise SystemExit("Command_SetRallyPoint definition changed")

    sell_sets_after = sum(1 for b in new_cs_blocks.values() if "Command_Sell" in b)
    sell_sets_before = sum(1 for b in cs_blocks.values() if "Command_Sell" in b)
    if sell_sets_after != sell_sets_before - 1:
        raise SystemExit(f"Sell slot count {sell_sets_before} -> {sell_sets_after}")

    for fac in FACTIONS:
        occupied = slots_of(new_cs_blocks[fac["cs"]])
        loader_btn = f"Command_Construct{fac['loader']}"
        if occupied.get(fac["slot"]) != loader_btn:
            raise SystemExit(f"loader wiped on {fac['side']}")

    obj_texts: dict[str, str] = {}
    weapons_text = (TOOL / "objects" / "ChinaV25CC12_Weapons.ini").read_text("latin1").replace("\r\n", "\n")
    if "ChinaV25SAM_AA" not in weapons_text or "PENALTY" not in weapons_text:
        raise SystemExit("shared SAM AA missing")
    if "ChinaTankWS3" in weapons_text or "SDPHL03" in weapons_text:
        raise SystemExit("PHL-03 leaked into weapons")
    obj_texts["ChinaV25CC12_Weapons.ini"] = weapons_text if weapons_text.endswith("\n") else weapons_text + "\n"

    for s in SYSTEMS:
        src = TOOL / "objects" / s["ini"]
        text = src.read_text("latin1").replace("\r\n", "\n")
        if not text.endswith("\n"):
            text += "\n"
        check_object(s, text)
        obj_texts[s["ini"]] = text
        verify_w3d(ART_SRC / "W3D" / s["w3d"], s["need"])

    map_text = SRC_MAP.read_text("latin1").replace("\r\n", "\n")
    for s in SYSTEMS:
        if f"MappedImage {s['image']}" not in map_text:
            raise SystemExit(f"MappedImage {s['image']} missing")
        img = re.search(r"(?m)^\s*ButtonImage\s*=\s*(\S+)", new_cb_blocks[s["btn"]])
        if not img or img.group(1) != s["image"]:
            raise SystemExit(f"{s['btn']} image mismatch")
        objn = re.search(r"(?m)^\s*Object\s*=\s*(\S+)", new_cb_blocks[s["btn"]])
        if not objn or objn.group(1) != s["obj"]:
            raise SystemExit(f"{s['btn']} object mismatch")

    art_copied: list[tuple[str, Path]] = []
    for rel_src, rel_dst in ART_FILES:
        src = ART_SRC / rel_src
        if not src.is_file():
            raise SystemExit(f"missing V25 art {src}")
        dst = OUT_DIR / rel_dst
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        art_copied.append((rel_dst, dst))

    out_ini = OUT_DIR / "Data" / "INI"
    (out_ini / OBJ_DIR).mkdir(parents=True, exist_ok=True)
    (out_ini / Path(MAP_REL).parent).mkdir(parents=True, exist_ok=True)
    (out_ini / "CommandSet.ini").write_bytes(crlf(new_cs))
    (out_ini / "CommandButton.ini").write_bytes(crlf(new_cb))
    (out_ini / MAP_REL).write_bytes(crlf(map_text if map_text.endswith("\n") else map_text + "\n"))
    obj_rels = []
    for name, text in obj_texts.items():
        rel = f"{OBJ_DIR}/{name}"
        (out_ini / rel).write_bytes(crlf(text))
        obj_rels.append("Data/INI/" + rel)

    zip_names = [dst for _, dst in ART_FILES]
    zip_names += [
        "Data/INI/CommandButton.ini",
        "Data/INI/CommandSet.ini",
        "Data/INI/" + MAP_REL,
        *obj_rels,
    ]
    zip_path = OUT_DIR / "SPECTER_SS2_CHINA_V25_CC12.zip"
    mapping = {name: OUT_DIR / name for name in zip_names}
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in zip_names:
            zf.write(mapping[name], name)
        if zf.namelist() != zip_names:
            raise SystemExit(zf.namelist())
        if any(n.lower().endswith(".big") or n.endswith(".txt") or n.endswith(".md") for n in zf.namelist()):
            raise SystemExit("ZIP must not contain BIG or reports")

    slot_lines = "\n".join(
        f"  China CC slot {s['slot']:2} = {s['btn']} -> {s['obj']}  ({s['label']})"
        for s in SYSTEMS
    )
    obj_sha = "\n".join(f"SHA-256 {rel:60} {sha256(OUT_DIR / rel)}" for rel in obj_rels)
    art_sha = "\n".join(f"SHA-256 {name:44} {sha256(path)}" for name, path in art_copied if name.endswith(".W3D") or name.endswith("TB.tga") or name.endswith("HQ9TB.tga") or name.endswith("ZZM88.tga") or name.endswith("HQ7BRD.tga"))
    report = f"""SS2 China V25 twelve-system Command Center pack (Loose Data, no BIG)
Merge base               America V25 CC6 CS/CB (loaders + Patriot/MSE/six USA systems)
China CC keeps           slot 1 Dozer, slot 4 Tunnel Loader
China CC replaces        slot 13 Rally and slot 14 Sell only (this CommandSet)
Command_Sell / Rally     button definitions unchanged; other factions unchanged

{slot_lines}

Identity notes
- WS-3 is ChinaTanksy400rocket / SDCHWS2 / WS3TB, not ChinaTankWS3 (PHL-03).
- CJ-10 is ChinaTankYJ62 / SDCJ10 / CJ10TB, not ChinaYJ62A.
- HT-233 is ChinaVehicleListeningOutpost / SDHT233, unique vs SS2 ChinaVehicleHT233.
- HQ-9 is ChinaHQ9 / SDCHH9, unique vs SS2 ChinaVehicleHQ9.
- FK-2000/AFT-10/HQ-11 come from V25 China Supply Center, not a substitute WF unit.

SHA-256 CommandSet.ini               {sha256(out_ini / 'CommandSet.ini')}
SHA-256 CommandButton.ini            {sha256(out_ini / 'CommandButton.ini')}
SHA-256 MappedImage                  {sha256(out_ini / MAP_REL)}
{obj_sha}
{art_sha}
SHA-256 ZIP                          {sha256(zip_path)}
ZIP {zip_path} {zip_path.stat().st_size} members={len(zip_names)}
26-country tunnel loaders preserved. America CC unchanged. No BIG.
Vehicles have no Shadow line. In-game test was not run.
"""
    (OUT_DIR / "BUILD_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SPECTER_SS2_CHINA_V25_CC12.zip.sha256").write_text(
        sha256(zip_path) + "  SPECTER_SS2_CHINA_V25_CC12.zip\n", encoding="ascii"
    )
    print(report)
    print("ZIP members:")
    with zipfile.ZipFile(zip_path) as zf:
        for n in zf.namelist():
            print(" ", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
