#!/usr/bin/env python3
"""Six V25 France systems onto SPECTER SS2 France Command Center.

Merges onto the Iran V25 CC6 ControlBar so America, China, and Iran packs
plus 26 tunnel loaders stay intact. Occupied France CC slots are kept.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ss2_tunnel_loader"))
from apply_turkey_method import FACTIONS  # noqa: E402

TOOL = Path(__file__).resolve().parent
SRC_CS = Path("patch/Release/SPECTER_SS2_IRAN_V25_CC6/Data/INI/CommandSet.ini")
SRC_CB = Path("patch/Release/SPECTER_SS2_IRAN_V25_CC6/Data/INI/CommandButton.ini")
SRC_MAP = TOOL / "FranceV25CC6_Images.ini"
OUT_DIR = Path("patch/Release/SPECTER_SS2_FRANCE_V25_CC6")
CC_NAME = "FranceCommandCenterCommandSet"
ART_SRC = TOOL / "art"
OBJ_DIR = "Object/Specter/French Armed Forces/V25CommandCenter"
MAP_REL = "MappedImages/HandCreated/FranceV25CC6_Images.ini"

SYSTEMS = [
    {
        "slot": 5,
        "btn": "Command_ConstructFranceVehicleV25Roland",
        "obj": "FranceVehicleV25Roland",
        "ini": "FranceVehicleV25Roland.ini",
        "model": "SDGRRLD",
        "image": "FRRLDTB",
        "w3d": "SDGRRLD.W3D",
        "need": [b"CORE", b"TURRET", b"TURRETEL", b"BARRELMS"],
        "draw": "W3DTankDraw",
        "label": "Roland",
        "extra_w3d": ("SDGRRLDw.W3D", [b"CORE", b"WHEEL02", b"WHEEL09"]),
        "v25_obj": "FranceRolland",
        "v25_btn": "Command_ConstructFranceRolland",
    },
    {
        "slot": 6,
        "btn": "Command_ConstructFranceVehicleV25Arabel",
        "obj": "FranceVehicleV25Arabel",
        "ini": "FranceVehicleV25Arabel.ini",
        "model": "Arabel",
        "image": "FranceV25ArabelTB",
        "w3d": "Arabel.W3D",
        "need": [b"WHEEL01", b"WHEEL08", b"BODY"],
        "draw": "W3DTruckDraw",
        "label": "Arabel Radar",
        "no_pitch": True,
        "radar": True,
        "v25_obj": "SupW_AmericaVehicleSentryDrone",
        "v25_btn": "SupW_Command_ConstructAmericaVehicleSentryDrone",
    },
    {
        "slot": 7,
        "btn": "Command_ConstructFranceVehicleV25Aster30",
        "obj": "FranceVehicleV25Aster30",
        "ini": "FranceVehicleV25Aster30.ini",
        "model": "FRAster",
        "image": "FranceV25AsterTB",
        "w3d": "FRAster.W3D",
        "need": [b"MISSILE_C01", b"WHEEL01", b"WHEEL08"],
        "draw": "W3DTruckDraw",
        "label": "Aster 30 Mamba",
        "no_pitch": True,
        "v25_obj": "FranceZiYuan",
        "v25_btn": "SupW_Command_ConstructZiYuan",
    },
    {
        "slot": 8,
        "btn": "Command_ConstructFranceVehicleV25Crotale",
        "obj": "FranceVehicleV25Crotale",
        "ini": "FranceVehicleV25Crotale.ini",
        "model": "FRCrotal",
        "image": "LSFFSATB",
        "w3d": "FRCrotal.W3D",
        "need": [b"TURRET", b"TURTTQ", b"MUZZLE01", b"WHEEL01"],
        "draw": "W3DTruckDraw",
        "label": "Crotale",
        "v25_obj": "SupW_AmericaTankAvenger",
        "v25_btn": "SupW_Command_ConstructAmericaVehicleAvenger",
    },
    {
        "slot": 9,
        "btn": "Command_ConstructFranceVehicleV25Mephisto",
        "obj": "FranceVehicleV25Mephisto",
        "ini": "FranceVehicleV25Mephisto.ini",
        "model": "VABHOT",
        "image": "VABHOTTB",
        "w3d": "VABHOT.W3D",
        "need": [b"BODY", b"MISSILE01", b"WHEEL01", b"WHEEL08"],
        "draw": "W3DTruckDraw",
        "label": "VAB Mephisto",
        "no_pitch": True,
        "v25_obj": "FranceAMX10P",
        "v25_btn": "Command_ConstructFranceAMX10P",
    },
    {
        "slot": 10,
        "btn": "Command_ConstructFranceVehicleV25VPM81",
        "obj": "FranceVehicleV25VPM81",
        "ini": "FranceVehicleV25VPM81.ini",
        "model": "VPM81",
        "image": "VPM81TB",
        "w3d": "VPM81.W3D",
        "need": [b"MRTRT", b"TURRET01", b"MORT", b"WHEEL01"],
        "draw": "W3DTruckDraw",
        "label": "VAB VPM 81",
        "no_pitch": True,
        "v25_obj": "SupW_AmericaTankCrusader",
        "v25_btn": "Command_ConstructFranceVPM81",
    },
]

ART_FILES = [
    ("W3D/SDGRRLD.W3D", "Art/W3D/SDGRRLD.W3D"),
    ("W3D/SDGRRLDw.W3D", "Art/W3D/SDGRRLDw.W3D"),
    ("W3D/Arabel.W3D", "Art/W3D/Arabel.W3D"),
    ("W3D/FRAster.W3D", "Art/W3D/FRAster.W3D"),
    ("W3D/FRCrotal.W3D", "Art/W3D/FRCrotal.W3D"),
    ("W3D/VABHOT.W3D", "Art/W3D/VABHOT.W3D"),
    ("W3D/VPM81.W3D", "Art/W3D/VPM81.W3D"),
    ("Textures/FRRLDTB.tga", "Art/Textures/FRRLDTB.tga"),
    ("Textures/FranceV25ArabelTB.tga", "Art/Textures/FranceV25ArabelTB.tga"),
    ("Textures/FranceV25AsterTB.tga", "Art/Textures/FranceV25AsterTB.tga"),
    ("Textures/LSFFSATB.tga", "Art/Textures/LSFFSATB.tga"),
    ("Textures/VABHOTTB.tga", "Art/Textures/VABHOTTB.tga"),
    ("Textures/VPM81TB.tga", "Art/Textures/VPM81TB.tga"),
    ("Textures/FRArabel.dds", "Art/Textures/FRArabel.dds"),
    ("Textures/FRCrotal.dds", "Art/Textures/FRCrotal.dds"),
    ("Textures/FRVPM81.dds", "Art/Textures/FRVPM81.dds"),
    ("Textures/SDVABHOT.dds", "Art/Textures/SDVABHOT.dds"),
    ("Textures/Aster30B.dds", "Art/Textures/Aster30B.dds"),
    ("Textures/Aster30L.dds", "Art/Textures/Aster30L.dds"),
    ("Textures/SDNSM04.dds", "Art/Textures/SDNSM04.dds"),
    ("Textures/RUA222W.dds", "Art/Textures/RUA222W.dds"),
    ("Textures/T14A1CM.dds", "Art/Textures/T14A1CM.dds"),
    ("Textures/SDGRRDCM.dds", "Art/Textures/SDGRRDCM.dds"),
    ("Textures/SDGRRDTR.dds", "Art/Textures/SDGRRDTR.dds"),
    ("Textures/Glass1.tga", "Art/Textures/Glass1.tga"),
]

FRANCE_KEEP = {
    1: "Command_ConstructFranceVehicleDozer",
    2: "Command_ConstructFranceTankPumaMech",
    3: "Command_FranceAWACS",
    4: "Command_ConstructFranceVehicleDozerm",
    14: "Command_Sell",
    15: "Command_ConstructFranceDronesMq9_AI",
    16: "Command_ConstructFranceDroneSwitchblade600",
    17: "Command_ConstructFranceDroneRQ4AI",
}
IRAN_KEEP = {
    1: "Command_ConstructIranVehicleDozer",
    2: "Command_ConstructIranVehicleV25Sayyad2",
    3: "Command_ConstructIranVehicleV251S91",
    4: "Command_ConstructIranVehicleV25SAM6",
    5: "Command_ConstructIranVehicleV25Raad",
    9: "Command_ConstructIranVehicleDozerm",
    12: "Command_ConstructIranVehicleV25Kolchuga",
    13: "Command_ConstructIranVehicleMajid",
    14: "Command_ConstructIranVehicleV25Noor",
}
CHINA_KEEP = {1: "Command_ConstructChinaDozer", 4: "Command_ConstructChinaVehicleDozerm"}
USA_KEEP = {
    1: "Command_ConstructAmericaDozer",
    2: "Command_ConstructAmericaVehicleMeadsRadar",
    10: "Command_ConstructAmericaVehiclePatriotPAC3",
}

FORBIDDEN_BTN = {
    "Command_Sell",
    "Command_SetRallyPoint",
    "Command_ConstructFranceVehicleCortaleMK3",
    "Command_ConstructFranceVehicleDozer",
    "Command_ConstructFranceTankPumaMech",
    "Command_FranceAWACS",
    "Command_ConstructFranceVehicleDozerm",
}
FORBIDDEN_OBJ = {
    "FranceVehicleCortaleMK3",
    "FranceVAB",
    "SupW_AmericaTankAvenger",
    "SupW_AmericaTankCrusader",
    "SupW_AmericaVehicleSentryDrone",
    "ItalyArabel",
    "ItalyAster30",
    "UkraineArabel",
    "UkraineAster30",
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
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[m.group(1)] = text[m.start():end]
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
        f"  TextLabel          = {sys['v25_label']}\n"
        f"  ButtonImage        = {sys['image']}\n"
        f"  ButtonBorderType   = BUILD\n"
        f"  DescriptLabel      = {sys['v25_label']}\n"
        f"End\n"
    )


LABELS = {
    "Command_ConstructFranceVehicleV25Roland": "Germany_Rolland",
    "Command_ConstructFranceVehicleV25Arabel": "France_Arabel",
    "Command_ConstructFranceVehicleV25Aster30": "France_Aster-30",
    "Command_ConstructFranceVehicleV25Crotale": "Croatal_AA",
    "Command_ConstructFranceVehicleV25Mephisto": "France_VAB-Hot",
    "Command_ConstructFranceVehicleV25VPM81": "France_VPM81",
}


def rewrite_slots(cs: str, name: str, assignments: dict[int, str], *, replace: bool) -> str:
    pattern = rf"(?ms)^(CommandSet {re.escape(name)}\s*\n)(.*?)(^End\s*$)"

    def repl(m: re.Match[str]) -> str:
        occupied = slots_of(m.group(2))
        lines = []
        assigned = set(assignments)
        for line in m.group(2).splitlines(True):
            mm = re.match(r"\s*(\d+)\s*=", line)
            if mm and int(mm.group(1)) in assigned:
                continue
            lines.append(line)
        body = "".join(lines)
        if not body.endswith("\n"):
            body += "\n"
        for slot, button in assignments.items():
            if slot in occupied and not replace:
                raise SystemExit(f"{name} slot {slot} already occupied by {occupied[slot]}")
            body += f"  {slot} = {button}\n"
        return m.group(1) + body + m.group(3)

    new, n = re.subn(pattern, repl, cs, count=1)
    if n != 1:
        raise SystemExit(f"failed to patch {name}")
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
    if "DeployStyleAIUpdate" in block:
        raise SystemExit(f"{sys['obj']} deploy not allowed")
    if "RiderChangeContain" in block:
        raise SystemExit(f"{sys['obj']} rider deploy not allowed")
    if sys["draw"] == "W3DTruckDraw" and sys["obj"] != "FranceVehicleV25Roland" and "Generic8x8Locomotor" not in block:
        raise SystemExit(f"{sys['obj']} missing Generic8x8Locomotor")
    if sys["draw"] == "W3DTankDraw" and "CrusaderLocomotor" not in block:
        raise SystemExit(f"{sys['obj']} missing CrusaderLocomotor")
    if re.search(r"(?m)^\s*KindOf\s*=.*FS_BASE_DEFENSE", block):
        raise SystemExit(f"{sys['obj']} FS_BASE_DEFENSE not allowed")
    if re.search(r"(?m)^\s*Shadow\s*=", block):
        raise SystemExit(f"{sys['obj']} must not set Shadow")
    if sys.get("no_pitch") and re.search(r"(?m)^\s*TurretPitch\s*=", block):
        raise SystemExit(f"{sys['obj']} must not set TurretPitch")
    if any(name in FORBIDDEN_OBJ for name in objs):
        raise SystemExit(f"{sys['obj']} reused a forbidden object")
    if sys["obj"] == "FranceVehicleV25Arabel" and re.search(r"(?m)^\s*Model\s*=\s*AMX10", block):
        raise SystemExit("Arabel must not use AMX-10 model")
    if sys["obj"] == "FranceVehicleV25Crotale" and re.search(r"(?m)^\s*Model\s*=\s*(AVAVENGER|Cortale)", block, re.I):
        raise SystemExit("Crotale must use FRCrotal")
    if sys["obj"] == "FranceVehicleV25Mephisto" and re.search(r"(?m)^\s*Model\s*=\s*SDFRVab\b", block):
        raise SystemExit("Mephisto must not use generic VAB")
    if sys["obj"] == "FranceVehicleV25VPM81" and re.search(r"(?m)^\s*Model\s*=\s*AVCRUSADER\b", block):
        raise SystemExit("VPM81 must not use Crusader tank")
    if sys["obj"] == "FranceVehicleV25Roland" and "AttachToBoneInAnotherModule" not in block:
        raise SystemExit("Roland wheels must attach to CORE")
    if sys.get("radar") and "StealthDetectorUpdate" not in block:
        raise SystemExit("Arabel missing radar detector")


def main() -> int:
    subprocess.check_call([sys.executable, str(TOOL / "write_objects.py")])
    if not SRC_CS.is_file() or not SRC_CB.is_file():
        raise SystemExit(f"Iran CC6 ControlBar missing: {SRC_CS}")
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    src_cs = SRC_CS.read_text("latin1").replace("\r\n", "\n")
    src_cb = SRC_CB.read_text("latin1").replace("\r\n", "\n")
    cs_blocks = parse_blocks(src_cs, "CommandSet")
    cb_blocks = parse_blocks(src_cb, "CommandButton")
    unique_count(list(cs_blocks), "source CommandSet.ini")
    unique_count(list(cb_blocks), "source CommandButton.ini")

    france_cc = slots_of(cs_blocks[CC_NAME])
    for slot, btn in FRANCE_KEEP.items():
        if france_cc.get(slot) != btn:
            raise SystemExit(f"{CC_NAME} slot {slot} is {france_cc.get(slot)}, expected {btn}")
    occupied_keep = set(FRANCE_KEEP)
    for s in SYSTEMS:
        if s["slot"] in occupied_keep:
            raise SystemExit(f"refusing to replace occupied France slot {s['slot']}")
        if s["slot"] in france_cc:
            raise SystemExit(f"France CC slot {s['slot']} already occupied by {france_cc[s['slot']]}")

    iran = slots_of(cs_blocks["IranExpandedHQCommandSet"])
    for slot, btn in IRAN_KEEP.items():
        if iran.get(slot) != btn:
            raise SystemExit(f"Iran slot {slot} is {iran.get(slot)}")
    china = slots_of(cs_blocks["ChinaCommandCenterCommandSet"])
    for slot, btn in CHINA_KEEP.items():
        if china.get(slot) != btn:
            raise SystemExit(f"China slot {slot} is {china.get(slot)}")
    usa = slots_of(cs_blocks["AmericaCommandCenterCommandSet"])
    for slot, btn in USA_KEEP.items():
        if usa.get(slot) != btn:
            raise SystemExit(f"America slot {slot} is {usa.get(slot)}")

    new_btns = [s["btn"] for s in SYSTEMS]
    unique_count(new_btns, "new buttons")
    for s in SYSTEMS:
        s["v25_label"] = LABELS[s["btn"]]
        if s["btn"] in cb_blocks:
            raise SystemExit(f"button already exists {s['btn']}")
        if s["btn"] in FORBIDDEN_BTN:
            raise SystemExit(f"must not reuse {s['btn']}")
        if s["obj"] in FORBIDDEN_OBJ:
            raise SystemExit(f"must not reuse object {s['obj']}")

    sell_before = cb_blocks["Command_Sell"]
    rally_before = cb_blocks["Command_SetRallyPoint"]
    china_before = cs_blocks["ChinaCommandCenterCommandSet"]
    usa_before = cs_blocks["AmericaCommandCenterCommandSet"]
    iran_before = cs_blocks["IranExpandedHQCommandSet"]
    turkey_before = cs_blocks["TurkeyCommandCenterCommandSet"]
    iran_wf_before = cs_blocks["IranWarfactoryCommandSet"]
    france_wf_before = cs_blocks.get("FranceWarfactoryCommandSet", "")
    cortale_before = button_core(cb_blocks["Command_ConstructFranceVehicleCortaleMK3"])

    for fac in FACTIONS:
        occupied = slots_of(cs_blocks[fac["cs"]])
        loader_btn = f"Command_Construct{fac['loader']}"
        if occupied.get(fac["slot"]) != loader_btn:
            raise SystemExit(f"{fac['side']} loader slot missing")
        if loader_btn not in cb_blocks:
            raise SystemExit(f"tunnel button missing {loader_btn}")
    if len(FACTIONS) != 26:
        raise SystemExit("expected 26 factions")

    cc_assign = {s["slot"]: s["btn"] for s in SYSTEMS}
    new_cs = rewrite_slots(src_cs, CC_NAME, cc_assign, replace=False)
    btn_text = "\n".join(btn_block(s) for s in SYSTEMS)
    new_cb = src_cb.rstrip() + "\n\n; SPECTER SS2 France V25 Command Center systems.\n\n" + btn_text

    new_cs_blocks = parse_blocks(new_cs, "CommandSet")
    new_cb_blocks = parse_blocks(new_cb, "CommandButton")
    unique_count(list(new_cs_blocks), "patched CommandSet.ini")
    unique_count(list(new_cb_blocks), "patched CommandButton.ini")
    if set(new_cs_blocks) != set(cs_blocks):
        raise SystemExit("CommandSet names were added or removed")
    if set(new_cb_blocks) - set(cb_blocks) != set(new_btns):
        raise SystemExit(f"unexpected CommandButton delta: {set(new_cb_blocks) - set(cb_blocks)}")

    won_cc = slots_of(new_cs_blocks[CC_NAME])
    for s in SYSTEMS:
        if won_cc[s["slot"]] != s["btn"]:
            raise SystemExit(f"CC slot {s['slot']} patch failed")
    for slot, btn in FRANCE_KEEP.items():
        if won_cc[slot] != btn:
            raise SystemExit(f"kept France CC slot {slot} lost")
    if new_cs_blocks["ChinaCommandCenterCommandSet"] != china_before:
        raise SystemExit("China CC changed")
    if new_cs_blocks["AmericaCommandCenterCommandSet"] != usa_before:
        raise SystemExit("America CC changed")
    if new_cs_blocks["IranExpandedHQCommandSet"] != iran_before:
        raise SystemExit("Iran CC changed")
    if new_cs_blocks["TurkeyCommandCenterCommandSet"] != turkey_before:
        raise SystemExit("Turkey CC changed")
    if new_cs_blocks["IranWarfactoryCommandSet"] != iran_wf_before:
        raise SystemExit("Iran WF changed")
    if france_wf_before and new_cs_blocks["FranceWarfactoryCommandSet"] != france_wf_before:
        raise SystemExit("France War Factory changed")
    if button_core(new_cb_blocks["Command_Sell"]) != button_core(sell_before):
        raise SystemExit("Command_Sell definition changed")
    if button_core(new_cb_blocks["Command_SetRallyPoint"]) != button_core(rally_before):
        raise SystemExit("Command_SetRallyPoint definition changed")
    if button_core(new_cb_blocks["Command_ConstructFranceVehicleCortaleMK3"]) != cortale_before:
        raise SystemExit("France Cortale MK3 button changed")

    sell_sets_after = sum(1 for b in new_cs_blocks.values() if "Command_Sell" in b)
    sell_sets_before = sum(1 for b in cs_blocks.values() if "Command_Sell" in b)
    if sell_sets_after != sell_sets_before:
        raise SystemExit(f"Sell slot count {sell_sets_before} -> {sell_sets_after}")

    for fac in FACTIONS:
        occupied = slots_of(new_cs_blocks[fac["cs"]])
        loader_btn = f"Command_Construct{fac['loader']}"
        if occupied.get(fac["slot"]) != loader_btn:
            raise SystemExit(f"loader wiped on {fac['side']}")

    obj_texts: dict[str, str] = {}
    weapons_text = (TOOL / "objects" / "FranceV25CC6_Weapons.ini").read_text("latin1").replace("\r\n", "\n")
    if "FranceV25Roland_AA" not in weapons_text or "FranceV25Aster_AA" not in weapons_text:
        raise SystemExit("shared France weapons missing")
    obj_texts["FranceV25CC6_Weapons.ini"] = weapons_text if weapons_text.endswith("\n") else weapons_text + "\n"

    for s in SYSTEMS:
        src = TOOL / "objects" / s["ini"]
        text = src.read_text("latin1").replace("\r\n", "\n")
        if not text.endswith("\n"):
            text += "\n"
        check_object(s, text)
        obj_texts[s["ini"]] = text
        verify_w3d(ART_SRC / "W3D" / s["w3d"], s["need"])
        if s.get("extra_w3d"):
            extra_name, extra_need = s["extra_w3d"]
            verify_w3d(ART_SRC / "W3D" / extra_name, extra_need)

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
    zip_path = OUT_DIR / "SPECTER_SS2_FRANCE_V25_CC6.zip"
    mapping = {name: OUT_DIR / name for name in zip_names}
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in zip_names:
            zf.write(mapping[name], name)
        if zf.namelist() != zip_names:
            raise SystemExit(zf.namelist())
        if any(n.lower().endswith(".big") or n.endswith(".txt") or n.endswith(".md") for n in zf.namelist()):
            raise SystemExit("ZIP must not contain BIG or reports")

    slot_lines = "\n".join(
        f"  France CC slot {s['slot']:2} = {s['btn']} -> {s['obj']}  ({s['label']})"
        f"  [V25 {s['v25_btn']} / {s['v25_obj']}]"
        for s in SYSTEMS
    )
    obj_sha = "\n".join(f"SHA-256 {rel:80} {sha256(OUT_DIR / rel)}" for rel in obj_rels)
    art_sha = "\n".join(
        f"SHA-256 {name:44} {sha256(path)}"
        for name, path in art_copied
        if name.endswith(".W3D") or name.endswith("TB.tga") or name.endswith("ArabelTB.tga") or name.endswith("AsterTB.tga")
    )
    keep = ", ".join(f"{k}={v.split('Command_')[-1]}" for k, v in sorted(FRANCE_KEEP.items()))
    report = f"""SS2 France V25 six-system Command Center pack (Loose Data, no BIG)
Merge base               Iran V25 CC6 CS/CB (America + China 12 + Iran 6 + loaders)
France CC CommandSet     FranceCommandCenterCommandSet (live FranceCommandCenter)
France CC keeps          {keep}

{slot_lines}

Identity notes
- Roland is FranceRolland / SDGRRLD + SDGRRLDw, not a substitute SAM.
- Arabel is Arabel.W3D from the France WF SentryDrone slot, not AMX-10 / Italy / Ukraine.
- Aster 30 is FranceZiYuan / FRAster, not ItalyAster30 / UkraineAster30.
- Crotale is FRCrotal from the France WF Avenger slot, not SS2 FranceVehicleCortaleMK3.
- VAB Mephisto is FranceAMX10P / VABHOT (France_VAB-Hot), not FranceVAB / SDFRVab.
- VAB VPM 81 is VPM81 from the France WF Crusader slot, not AmericaTankCrusader.

SHA-256 CommandSet.ini               {sha256(out_ini / 'CommandSet.ini')}
SHA-256 CommandButton.ini            {sha256(out_ini / 'CommandButton.ini')}
SHA-256 MappedImage                  {sha256(out_ini / MAP_REL)}
{obj_sha}
{art_sha}
SHA-256 ZIP                          {sha256(zip_path)}
ZIP {zip_path} {zip_path.stat().st_size} members={len(zip_names)}
26-country tunnel loaders preserved. America, China, Iran CC unchanged. No BIG.
Vehicles have no Shadow line. In-game test was not run.
"""
    (OUT_DIR / "BUILD_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SPECTER_SS2_FRANCE_V25_CC6.zip.sha256").write_text(
        sha256(zip_path) + "  SPECTER_SS2_FRANCE_V25_CC6.zip\n", encoding="ascii"
    )
    print(report)
    print("ZIP members:")
    with zipfile.ZipFile(zip_path) as zf:
        for n in zf.namelist():
            print(" ", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
