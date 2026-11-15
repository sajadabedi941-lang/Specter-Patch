#!/usr/bin/env python3
"""Eighteen V25 Russia systems on Command Center empty slots plus independent War Factory 2.

War Factory 2 is built from RussiaVehicleDozerm. Tunnel and old RussiaWarFactory stay.
Merges onto the North Korea V25 CC9 ControlBar.
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
SRC_CS = Path("patch/Release/SPECTER_SS2_NORTHKOREA_V25_CC9/Data/INI/CommandSet.ini")
SRC_CB = Path("patch/Release/SPECTER_SS2_NORTHKOREA_V25_CC9/Data/INI/CommandButton.ini")
SRC_MAP = TOOL / "RussiaV25CCWF_Images.ini"
OUT_DIR = Path("patch/Release/SPECTER_SS2_RUSSIA_V25_CC_WF")
ZIP_ROOT = Path("patch/Release/SPECTER_SS2_RUSSIA_V25_CC_WF.zip")
CC_NAME = "RussiaCommandCenterCommandSet"
DOZERM_CS = "RussiaVehicleDozermCommandSet"
WF2_CS = "RussiaWarFactoryV25CommandSet"
WF2_BTN = "Command_ConstructRussiaWarFactoryV25"
WF2_OBJ = "RussiaWarFactoryV25"
ART_SRC = TOOL / "art"
OBJ_DIR = "Object/Specter/Armed Forces Of Russian Federation/V25CommandCenter"
MAP_REL = "MappedImages/HandCreated/RussiaV25CCWF_Images.ini"

CC_SYSTEMS = [
    {"slot": 9, "btn": "Command_ConstructRussiaVehicleV25S350", "obj": "RussiaVehicleV25S350", "ini": "RussiaVehicleV25S350.ini", "model": "RUS350", "image": "RUS350TB", "w3d": "RUS350.W3D", "need": [b"WEAPONB", b"MUZZLEFX", b"WHEEL01"], "draw": "W3DTruckDraw", "label": "S-350 Vityaz", "v25_obj": "RussiaS350", "v25_btn": "Nuke_Command_ConstructRussiaS350", "building": "CC"},
    {"slot": 11, "btn": "Command_ConstructRussiaVehicleV2550N6A", "obj": "RussiaVehicleV2550N6A", "ini": "RussiaVehicleV2550N6A.ini", "model": "RUS350RD", "image": "50N6ATB", "w3d": "RUS350RD.W3D", "need": [b"WHEEL01"], "draw": "W3DTruckDraw", "label": "50N6A Radar", "no_pitch": True, "radar": True, "v25_obj": "Russia50N6A", "v25_btn": "Nuke_Command_ConstructRussia50N6A", "building": "CC"},
    {"slot": 12, "btn": "Command_ConstructRussiaVehicleV25S300V1", "obj": "RussiaVehicleV25S300V1", "ini": "RussiaVehicleV25S300V1.ini", "model": "URS300V", "image": "RUS300VMTB", "w3d": "URS300V.W3D", "need": [b"CORE", b"WEAPONB", b"WEAPONFX"], "draw": "W3DTankDraw", "label": "S-300V1", "extra_w3d": ("URS300Vw.W3D", [b"CORE", b"WHEEL02", b"WHEEL09"]), "v25_obj": "RussiaS300VM", "v25_btn": "Nuke_Command_ConstructRussiaS300VM", "building": "CC"},
    {"slot": 13, "btn": "Command_ConstructRussiaVehicleV259S32", "obj": "RussiaVehicleV259S32", "ini": "RussiaVehicleV259S32.ini", "model": "UR9S32", "image": "9S32TB", "w3d": "UR9S32.W3D", "need": [b"CORE"], "draw": "W3DTankDraw", "label": "Russia 9S32 Radar", "no_pitch": True, "radar": True, "extra_w3d": ("UR9S32w.W3D", [b"CORE", b"WHEEL02", b"WHEEL08"]), "v25_obj": "Russia9S32", "v25_btn": "Nuke_Command_ConstructRussia9S32", "building": "CC"},
    {"slot": 15, "btn": "Command_ConstructRussiaVehicleV259S119M1", "obj": "RussiaVehicleV259S119M1", "ini": "RussiaVehicleV259S119M1.ini", "model": "UR9S18M1", "image": "RU9S18M1TB", "w3d": "UR9S18M1.W3D", "need": [b"CORE"], "draw": "W3DTankDraw", "label": "9S119M1", "no_pitch": True, "radar": True, "extra_w3d": ("UR9S18M1w.W3D", [b"CORE", b"TIRE01", b"TIRE08"]), "v25_obj": "Russia9S18M1", "v25_btn": "Command_ConstructRussia9S18M1", "building": "CC"},
    {"slot": 16, "btn": "Command_ConstructRussiaVehicleV25S400", "obj": "RussiaVehicleV25S400", "ini": "RussiaVehicleV25S400.ini", "model": "RUS400", "image": "RUS400TB", "w3d": "RUS400.W3D", "need": [b"MISSILE_C", b"MUZZLEFX", b"CAB"], "draw": "W3DTruckDraw", "label": "S-400 Triumph", "v25_obj": "russias400", "v25_btn": "Nuke_Command_ConstructRussiaS400", "building": "CC"},
    {"slot": 17, "btn": "Command_ConstructRussiaVehicleV2540V6MD", "obj": "RussiaVehicleV2540V6MD", "ini": "RussiaVehicleV2540V6MD.ini", "model": "SD40V6MD", "image": "40V6MDTB", "w3d": "SD40V6MD.W3D", "need": [b"CAB", b"TRAILER", b"WHEEL01"], "draw": "W3DTruckDraw", "label": "40V6MD Radar", "no_pitch": True, "radar": True, "v25_obj": "RussianRadar", "v25_btn": "Nuke_Command_ConstructRussianRadar", "building": "CC"},
    {"slot": 18, "btn": "Command_ConstructRussiaVehicleV25S500", "obj": "RussiaVehicleV25S500", "ini": "RussiaVehicleV25S500.ini", "model": "RUS500", "image": "RUS500TB", "w3d": "RUS500.W3D", "need": [b"MISSILE_C", b"MUZZLEFX"], "draw": "W3DTruckDraw", "label": "S-500 Prometey", "v25_obj": "RussiaS500", "v25_btn": "Nuke_Command_ConstructRussiaS500", "building": "CC"},
]
WF_SYSTEMS = [
    {"slot": 1, "btn": "Command_ConstructRussiaVehicleV25Tunguska", "obj": "RussiaVehicleV25Tunguska", "ini": "RussiaVehicleV25Tunguska.ini", "model": "RUTGSK", "image": "TGSK", "w3d": "RUTGSK.W3D", "need": [b"CORE", b"TURRET", b"TURRETEL", b"BARRELFX", b"MISSILE"], "draw": "W3DTankDraw", "label": "Tunguska", "extra_w3d": ("RUTGSKw.W3D", [b"CORE", b"WHEEL02", b"WHEEL09"]), "v25_obj": "Nuke_ChinaTankGattling", "v25_btn": "Nuke_Command_ConstructChinaTankGattling", "building": "WF2"},
    {"slot": 2, "btn": "Command_ConstructRussiaVehicleV25BalE", "obj": "RussiaVehicleV25BalE", "ini": "RussiaVehicleV25BalE.ini", "model": "RUBALE", "image": "BALETB", "w3d": "RUBALE.W3D", "need": [b"WEAPONA", b"WHEEL01"], "draw": "W3DTruckDraw", "label": "Bal-E", "v25_obj": "RussiaCoastal", "v25_btn": "Nuke_Command_ConstructRussiaCoastal", "building": "WF2"},
    {"slot": 3, "btn": "Command_ConstructRussiaVehicleV259K33", "obj": "RussiaVehicleV259K33", "ini": "RussiaVehicleV259K33.ini", "model": "RU9K33", "image": "9K33TB", "w3d": "RU9K33.W3D", "need": [b"TURRET", b"TURRETEL", b"FIREFX", b"TIRE01"], "draw": "W3DTruckDraw", "label": "9K33 Osa", "v25_obj": "RussiaTankT64", "v25_btn": "RU9K33", "building": "WF2"},
    {"slot": 4, "btn": "Command_ConstructRussiaVehicleV2530N6E", "obj": "RussiaVehicleV2530N6E", "ini": "RussiaVehicleV2530N6E.ini", "model": "30N6EFL", "image": "30N6EFLTB", "w3d": "30N6EFL.W3D", "need": [b"WHEEL01", b"WHEEL08"], "draw": "W3DTruckDraw", "label": "30N6E Flap Lid", "no_pitch": True, "radar": True, "v25_obj": "30N6EFLAPLID", "v25_btn": "Nuke_Command_Construct30N6EFLAPLID", "building": "WF2"},
    {"slot": 5, "btn": "Command_ConstructRussiaVehicleV259K31", "obj": "RussiaVehicleV259K31", "ini": "RussiaVehicleV259K31.ini", "model": "UR9K31", "image": "RY9K31TB", "w3d": "UR9K31.W3D", "need": [b"TURRET", b"TURRETEL", b"MUZZLE", b"TIRE01"], "draw": "W3DTruckDraw", "label": "9K31 Strela-1", "v25_obj": "Russia9K31", "v25_btn": "Command_ConstructRussia9K31", "building": "WF2"},
    {"slot": 6, "btn": "Command_ConstructRussiaVehicleV25Shilka", "obj": "RussiaVehicleV25Shilka", "ini": "RussiaVehicleV25Shilka.ini", "model": "NKZSU23", "image": "RUZSU4TB", "w3d": "NKZSU23.W3D", "need": [b"CORE", b"TURRET01", b"TURRETEL01", b"MUZZLE"], "draw": "W3DTankDraw", "label": "Shilka", "extra_w3d": ("NKZSU23w.W3D", [b"CORE", b"TIRE01"]), "v25_obj": "RussiaShilka", "v25_btn": "Command_ConstructRussiaShilka", "building": "WF2"},
    {"slot": 7, "btn": "Command_ConstructRussiaVehicleV259A52", "obj": "RussiaVehicleV259A52", "ini": "RussiaVehicleV259A52.ini", "model": "RU9A52", "image": "9A52TB", "w3d": "RU9A52.W3D", "need": [b"TURRET01", b"TURRETEL02", b"WEAPONA", b"WHEEL01"], "draw": "W3DTruckDraw", "label": "9A52-4 Tornado", "v25_obj": "RussiaUragan", "v25_btn": "Nuke_Command_ConstructRussiaUragan", "building": "WF2"},
    {"slot": 8, "btn": "Command_ConstructRussiaVehicleV25BukM3", "obj": "RussiaVehicleV25BukM3", "ini": "RussiaVehicleV25BukM3.ini", "model": "BUKMM3", "image": "Bukmm3TB", "w3d": "BUKMM3.W3D", "need": [b"CORE", b"TURRET01", b"TURRETEL01", b"MISSILE"], "draw": "W3DTankDraw", "label": "Russia Buk-M3", "extra_w3d": ("BUKMM3w.W3D", [b"CORE", b"TIRE01", b"TIRE08"]), "v25_obj": "RussiaBukMM3", "v25_btn": "Nuke_Command_ConstructRussiaBukMM3", "building": "WF2"},
    {"slot": 9, "btn": "Command_ConstructRussiaVehicleV25Strela10", "obj": "RussiaVehicleV25Strela10", "ini": "RussiaVehicleV25Strela10.ini", "model": "RUMTLB", "image": "RUMTLBTB2", "w3d": "RUMTLB.W3D", "need": [b"CORE", b"TURRET", b"TURRETEL", b"MUZZLE"], "draw": "W3DTankDraw", "label": "9K35 Strela-10", "extra_w3d": ("RUMTLBw.W3D", [b"CORE", b"TIRE01", b"TIRE08"]), "v25_obj": "RussiaMTLB", "v25_btn": "Nuke_Command_ConstructRussiaMTLB", "building": "WF2"},
    {"slot": 10, "btn": "Command_ConstructRussiaVehicleV25Bastion", "obj": "RussiaVehicleV25Bastion", "ini": "RussiaVehicleV25Bastion.ini", "model": "RUK300", "image": "RUK300TB", "w3d": "RUK300.W3D", "need": [b"MISS", b"WHEEL01"], "draw": "W3DTruckDraw", "label": "K-300P Bastion-P", "v25_obj": "RussiaBastion", "v25_btn": "Nuke_Command_ConstructRussiaBastion", "building": "WF2"},
]
SYSTEMS = CC_SYSTEMS + WF_SYSTEMS

RUSSIA_KEEP = {
    1: "Command_ConstructRussiaVehicleDozer",
    2: "Command_ConstructRussiaTankTorM2M",
    3: "Command_ConstructRussiaVehicle9K317",
    4: "Command_ConstructRussiaVehicle55K6E",
    5: "Command_ConstructRussiaVehiclePantsirS1M",
    6: "Command_ConstructRussiaVehicleS400",
    7: "Command_ConstructRussiaVehicleS500",
    8: "Command_ConstructRussiaVehicleDozerm",
    10: "Command_ConstructRussiaVehicleBTR82A",
    14: "Command_Sell",
}
NK_KEEP = {
    1: "Command_ConstructNorthKorea_VT72B",
    2: "Command_ConstructNorthKoreaVehicleV25Strela10",
    12: "Command_ConstructNorthKoreaVehicleV25BM24",
}
BRITAIN_KEEP = {5: "Command_ConstructBritainVehicleV25SkySabre"}
FRANCE_KEEP = {5: "Command_ConstructFranceVehicleV25Roland"}
IRAN_KEEP = {2: "Command_ConstructIranVehicleV25Sayyad2"}
CHINA_KEEP = {1: "Command_ConstructChinaDozer", 4: "Command_ConstructChinaVehicleDozerm"}
USA_KEEP = {1: "Command_ConstructAmericaDozer", 10: "Command_ConstructAmericaVehiclePatriotPAC3"}

FORBIDDEN_BTN = {
    "Command_Sell",
    "Command_SetRallyPoint",
    "Command_ConstructRussiaWarFactory",
    "Command_ConstructRussiaWarFactory_T",
    "Command_ConstructRussiaPowerStationm",
    "Command_ConstructRussiaVehicleDozerm",
    "Command_ConstructRussiaVehicleS400",
    "Command_ConstructRussiaVehicleS500",
    "Command_ConstructNorthKoreaVehicleV25Strela10",
    "Command_ConstructNorthKoreaVehicleV25Shilka",
}
FORBIDDEN_OBJ = {
    "RussiaS350",
    "Russia50N6A",
    "RussiaS300VM",
    "Russia9S32",
    "Russia9S18M1",
    "russias400",
    "RussiaS400",
    "RussiaVehicleS400",
    "RussianRadar",
    "RussiaS500",
    "RussiaVehicleS500",
    "Ukrania2K22",
    "RussiaCoastal",
    "RussiaTankT64",
    "30N6EFLAPLID",
    "Russia9K31",
    "RussiaShilka",
    "RussiaUragan",
    "RussiaBukMM3",
    "RussiaMTLB",
    "NorthKoreaVehicleV25Strela10",
    "NorthKoreaVehicleV25Shilka",
    "RussiaBastion",
    "RussiaWarFactory",
    "RussiaWarFactory_T",
    "RussiaWarFactory3",
}

LABELS = {
    "Command_ConstructRussiaVehicleV25S350": "Russia_S350",
    "Command_ConstructRussiaVehicleV2550N6A": "Russia_50N6A",
    "Command_ConstructRussiaVehicleV25S300V1": "Ukraine_S300V1",
    "Command_ConstructRussiaVehicleV259S32": "Russia_9S32-Radar",
    "Command_ConstructRussiaVehicleV259S119M1": "Russia_9S119M1",
    "Command_ConstructRussiaVehicleV25S400": "Russia_S400",
    "Command_ConstructRussiaVehicleV2540V6MD": "Russia_40V6MD",
    "Command_ConstructRussiaVehicleV25S500": "Russia_S500",
    "Command_ConstructRussiaVehicleV25Tunguska": "OBJECT:TGSK",
    "Command_ConstructRussiaVehicleV25BalE": "Russia_BAL_E",
    "Command_ConstructRussiaVehicleV259K33": "Russia_9K33",
    "Command_ConstructRussiaVehicleV2530N6E": "Russia_30N6EFlapLid",
    "Command_ConstructRussiaVehicleV259K31": "Russia_9K31",
    "Command_ConstructRussiaVehicleV25Shilka": "Russia_Shilka",
    "Command_ConstructRussiaVehicleV259A52": "Russia_9A52",
    "Command_ConstructRussiaVehicleV25BukM3": "Russia_BukMM3",
    "Command_ConstructRussiaVehicleV25Strela10": "Russia_Strela10",
    "Command_ConstructRussiaVehicleV25Bastion": "Russia_K300Bastion",
}

WF2_SET = """CommandSet RussiaWarFactoryV25CommandSet
  1 = Command_ConstructRussiaVehicleV25Tunguska
  2 = Command_ConstructRussiaVehicleV25BalE
  3 = Command_ConstructRussiaVehicleV259K33
  4 = Command_ConstructRussiaVehicleV2530N6E
  5 = Command_ConstructRussiaVehicleV259K31
  6 = Command_ConstructRussiaVehicleV25Shilka
  7 = Command_ConstructRussiaVehicleV259A52
  8 = Command_ConstructRussiaVehicleV25BukM3
  9 = Command_ConstructRussiaVehicleV25Strela10
  10 = Command_ConstructRussiaVehicleV25Bastion
  14 = Command_Sell
End
"""

WF2_BUTTON = """CommandButton Command_ConstructRussiaWarFactoryV25
  Command          = DOZER_CONSTRUCT
  Object           = RussiaWarFactoryV25
  TextLabel        = Russia_WarFactoryIII
  ButtonImage      = RUWARFCIII
  ButtonBorderType = BUILD
  DescriptLabel    = Russia_WarFactoryIII
End
"""


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
    if "DeployStyleAIUpdate" in block or "RiderChangeContain" in block:
        raise SystemExit(f"{sys['obj']} deploy not allowed")
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
    if any(name in FORBIDDEN_OBJ for name in objs):
        raise SystemExit(f"{sys['obj']} reused a forbidden object")
    if sys.get("extra_w3d") and "AttachToBoneInAnotherModule" not in block:
        raise SystemExit(f"{sys['obj']} wheels must attach to CORE")
    if sys.get("radar") and "StealthDetectorUpdate" not in block:
        raise SystemExit(f"{sys['obj']} missing radar detector")


def needed_art() -> list[tuple[str, str]]:
    names: set[str] = set()
    w3ds: list[str] = []
    for s in SYSTEMS:
        w3ds.append(s["w3d"])
        names.add(s["image"] + ".tga" if not s["image"].endswith(".tga") else s["image"])
        if s.get("extra_w3d"):
            w3ds.append(s["extra_w3d"][0])
    w3ds.append("StructureHamVhe.W3D")
    names.update(["RUWARFCIII.tga", "RUMTLBTB2.tga"])
    files: list[tuple[str, str]] = []
    for w3d in w3ds:
        files.append((f"W3D/{w3d}", f"Art/W3D/{w3d}"))
        data = (ART_SRC / "W3D" / w3d).read_bytes()
        for m in re.finditer(rb"[\w\-\.]{3,64}\.(dds|tga|DDS|TGA)", data):
            tex = m.group(0).decode("latin1")
            if tex.lower().startswith("tex_"):
                continue
            src = ART_SRC / "Textures" / tex
            if not src.is_file():
                # case-insensitive fallback already aliased during extract
                continue
            files.append((f"Textures/{tex}", f"Art/Textures/{tex}"))
    for cam in sorted(names):
        src = ART_SRC / "Textures" / cam
        if src.is_file():
            files.append((f"Textures/{cam}", f"Art/Textures/{cam}"))
    # unique preserve order
    seen: set[str] = set()
    out = []
    for a, b in files:
        if b in seen:
            continue
        seen.add(b)
        out.append((a, b))
    return out


def main() -> int:
    subprocess.check_call([sys.executable, str(TOOL / "write_objects.py")])
    if not SRC_CS.is_file() or not SRC_CB.is_file():
        raise SystemExit(f"NK CC9 ControlBar missing: {SRC_CS}")
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    src_cs = SRC_CS.read_text("latin1").replace("\r\n", "\n")
    src_cb = SRC_CB.read_text("latin1").replace("\r\n", "\n")
    cs_blocks = parse_blocks(src_cs, "CommandSet")
    cb_blocks = parse_blocks(src_cb, "CommandButton")
    unique_count(list(cs_blocks), "source CommandSet.ini")
    unique_count(list(cb_blocks), "source CommandButton.ini")
    if CC_NAME not in cs_blocks:
        raise SystemExit("RussiaCommandCenterCommandSet missing")
    if DOZERM_CS not in cs_blocks:
        raise SystemExit("RussiaVehicleDozermCommandSet missing")
    if WF2_CS in cs_blocks:
        raise SystemExit("RussiaWarFactoryV25CommandSet already exists")
    if WF2_BTN in cb_blocks:
        raise SystemExit("Command_ConstructRussiaWarFactoryV25 already exists")

    ru_cc = slots_of(cs_blocks[CC_NAME])
    for slot, btn in RUSSIA_KEEP.items():
        if ru_cc.get(slot) != btn:
            raise SystemExit(f"{CC_NAME} slot {slot} is {ru_cc.get(slot)}, expected {btn}")
    occupied_keep = set(RUSSIA_KEEP)
    for s in CC_SYSTEMS:
        if s["slot"] in occupied_keep:
            raise SystemExit(f"refusing to replace occupied Russia CC slot {s['slot']}")
        if s["slot"] in ru_cc:
            raise SystemExit(f"Russia CC slot {s['slot']} already occupied by {ru_cc[s['slot']]}")
    empty = [i for i in range(1, 19) if i not in ru_cc]
    if empty != [9, 11, 12, 13, 15, 16, 17, 18]:
        raise SystemExit(f"unexpected Russia CC empty slots: {empty}")

    dozerm = slots_of(cs_blocks[DOZERM_CS])
    if dozerm.get(1) != "Command_ConstructRussiaPowerStationm":
        raise SystemExit(f"dozerm tunnel missing: {dozerm}")
    if 2 in dozerm:
        raise SystemExit(f"dozerm slot 2 occupied by {dozerm[2]}")

    old_dozer = slots_of(cs_blocks["RussiaDozerCommandSet"])
    if old_dozer.get(9) != "Command_ConstructRussiaWarFactory":
        raise SystemExit("old dozer War Factory button missing")
    wf_old = cs_blocks["RussiaWarFactoryCommandSet"]

    for name, keep in (
        ("NorthKorea_CommandCenterCommandSet", NK_KEEP),
        ("BritainCommandCenterCommandSet", BRITAIN_KEEP),
        ("FranceCommandCenterCommandSet", FRANCE_KEEP),
        ("IranExpandedHQCommandSet", IRAN_KEEP),
        ("ChinaCommandCenterCommandSet", CHINA_KEEP),
        ("AmericaCommandCenterCommandSet", USA_KEEP),
    ):
        occupied = slots_of(cs_blocks[name])
        for slot, btn in keep.items():
            if occupied.get(slot) != btn:
                raise SystemExit(f"{name} slot {slot} is {occupied.get(slot)}")

    new_btns = [s["btn"] for s in SYSTEMS] + [WF2_BTN]
    unique_count(new_btns, "new buttons")
    unique_count([s["obj"] for s in SYSTEMS] + [WF2_OBJ], "new objects")
    if len(SYSTEMS) != 18:
        raise SystemExit(f"expected 18 systems, got {len(SYSTEMS)}")
    osa = [s for s in SYSTEMS if "9K33" in s["label"] or s["obj"].endswith("9K33")]
    if len(osa) != 1:
        raise SystemExit(f"9K33 Osa must appear once, found {len(osa)}")
    for s in SYSTEMS:
        s["v25_label"] = LABELS[s["btn"]]
        if s["btn"] in cb_blocks or s["btn"] in FORBIDDEN_BTN:
            raise SystemExit(f"must not reuse button {s['btn']}")
        if s["obj"] in FORBIDDEN_OBJ:
            raise SystemExit(f"must not reuse object {s['obj']}")

    sell_before = cb_blocks["Command_Sell"]
    old_wf_btn = button_core(cb_blocks["Command_ConstructRussiaWarFactory"])
    tunnel_btn = button_core(cb_blocks["Command_ConstructRussiaPowerStationm"])
    china_before = cs_blocks["ChinaCommandCenterCommandSet"]
    usa_before = cs_blocks["AmericaCommandCenterCommandSet"]
    iran_before = cs_blocks["IranExpandedHQCommandSet"]
    france_before = cs_blocks["FranceCommandCenterCommandSet"]
    britain_before = cs_blocks["BritainCommandCenterCommandSet"]
    nk_before = cs_blocks["NorthKorea_CommandCenterCommandSet"]
    turkey_before = cs_blocks["TurkeyCommandCenterCommandSet"]

    for fac in FACTIONS:
        occupied = slots_of(cs_blocks[fac["cs"]])
        loader_btn = f"Command_Construct{fac['loader']}"
        if occupied.get(fac["slot"]) != loader_btn:
            raise SystemExit(f"{fac['side']} loader slot missing")
        if loader_btn not in cb_blocks:
            raise SystemExit(f"tunnel button missing {loader_btn}")
    if len(FACTIONS) != 26:
        raise SystemExit("expected 26 factions")

    cc_assign = {s["slot"]: s["btn"] for s in CC_SYSTEMS}
    new_cs = rewrite_slots(src_cs, CC_NAME, cc_assign, replace=False)
    new_cs = rewrite_slots(new_cs, DOZERM_CS, {2: WF2_BTN}, replace=False)
    new_cs = new_cs.rstrip() + "\n\n; SPECTER SS2 independent Russia War Factory 2 (V25).\n\n" + WF2_SET
    btn_text = "\n".join(btn_block(s) for s in SYSTEMS)
    new_cb = (
        src_cb.rstrip()
        + "\n\n; SPECTER SS2 Russia V25 Command Center and independent War Factory 2.\n\n"
        + btn_text
        + "\n"
        + WF2_BUTTON
    )

    new_cs_blocks = parse_blocks(new_cs, "CommandSet")
    new_cb_blocks = parse_blocks(new_cb, "CommandButton")
    unique_count(list(new_cs_blocks), "patched CommandSet.ini")
    unique_count(list(new_cb_blocks), "patched CommandButton.ini")
    if set(new_cs_blocks) - set(cs_blocks) != {WF2_CS}:
        raise SystemExit(f"unexpected CommandSet delta: {set(new_cs_blocks) - set(cs_blocks)}")
    if set(new_cb_blocks) - set(cb_blocks) != set(new_btns):
        raise SystemExit(f"unexpected CommandButton delta: {set(new_cb_blocks) - set(cb_blocks)}")

    won_cc = slots_of(new_cs_blocks[CC_NAME])
    for s in CC_SYSTEMS:
        if won_cc[s["slot"]] != s["btn"]:
            raise SystemExit(f"CC slot {s['slot']} patch failed")
    for slot, btn in RUSSIA_KEEP.items():
        if won_cc[slot] != btn:
            raise SystemExit(f"kept Russia CC slot {slot} lost")
    won_dozerm = slots_of(new_cs_blocks[DOZERM_CS])
    if won_dozerm.get(1) != "Command_ConstructRussiaPowerStationm":
        raise SystemExit("tunnel wiped from dozerm")
    if won_dozerm.get(2) != WF2_BTN:
        raise SystemExit("WF2 button missing on dozerm")
    if slots_of(new_cs_blocks["RussiaDozerCommandSet"]).get(9) != "Command_ConstructRussiaWarFactory":
        raise SystemExit("old dozer War Factory changed")
    if new_cs_blocks["RussiaWarFactoryCommandSet"] != wf_old:
        raise SystemExit("old Russia War Factory CommandSet changed")
    won_wf2 = slots_of(new_cs_blocks[WF2_CS])
    for s in WF_SYSTEMS:
        if won_wf2[s["slot"]] != s["btn"]:
            raise SystemExit(f"WF2 slot {s['slot']} patch failed")
    if won_wf2.get(14) != "Command_Sell":
        raise SystemExit("WF2 missing Sell")
    if 11 in won_wf2 or 12 in won_wf2 or 13 in won_wf2:
        raise SystemExit("WF2 must not occupy old-factory extra slots")
    if new_cs_blocks["ChinaCommandCenterCommandSet"] != china_before:
        raise SystemExit("China CC changed")
    if new_cs_blocks["AmericaCommandCenterCommandSet"] != usa_before:
        raise SystemExit("America CC changed")
    if new_cs_blocks["IranExpandedHQCommandSet"] != iran_before:
        raise SystemExit("Iran CC changed")
    if new_cs_blocks["FranceCommandCenterCommandSet"] != france_before:
        raise SystemExit("France CC changed")
    if new_cs_blocks["BritainCommandCenterCommandSet"] != britain_before:
        raise SystemExit("Britain CC changed")
    if new_cs_blocks["NorthKorea_CommandCenterCommandSet"] != nk_before:
        raise SystemExit("NK CC changed")
    if new_cs_blocks["TurkeyCommandCenterCommandSet"] != turkey_before:
        raise SystemExit("Turkey CC changed")
    if button_core(new_cb_blocks["Command_Sell"]) != button_core(sell_before):
        raise SystemExit("Command_Sell definition changed")
    if button_core(new_cb_blocks["Command_ConstructRussiaWarFactory"]) != old_wf_btn:
        raise SystemExit("old War Factory button changed")
    if button_core(new_cb_blocks["Command_ConstructRussiaPowerStationm"]) != tunnel_btn:
        raise SystemExit("tunnel button changed")
    if button_core(new_cb_blocks[WF2_BTN]).find("Object           = RussiaWarFactoryV25") < 0 and "Object           = RussiaWarFactoryV25" not in button_core(new_cb_blocks[WF2_BTN]):
        if re.search(r"(?m)^\s*Object\s+=\s+RussiaWarFactoryV25\s*$", new_cb_blocks[WF2_BTN]) is None:
            raise SystemExit("WF2 construct button object mismatch")

    sell_sets_after = sum(1 for b in new_cs_blocks.values() if "Command_Sell" in b)
    sell_sets_before = sum(1 for b in cs_blocks.values() if "Command_Sell" in b)
    if sell_sets_after != sell_sets_before + 1:
        raise SystemExit(f"Sell slot count {sell_sets_before} -> {sell_sets_after}")

    for fac in FACTIONS:
        occupied = slots_of(new_cs_blocks[fac["cs"]])
        loader_btn = f"Command_Construct{fac['loader']}"
        if occupied.get(fac["slot"]) != loader_btn:
            raise SystemExit(f"loader wiped on {fac['side']}")

    obj_texts: dict[str, str] = {}
    weapons_text = (TOOL / "objects" / "RussiaV25CCWF_Weapons.ini").read_text("latin1").replace("\r\n", "\n")
    if "RussiaV25SAM_AA" not in weapons_text or "RussiaV25Strela_AA" not in weapons_text:
        raise SystemExit("shared Russia weapons missing")
    obj_texts["RussiaV25CCWF_Weapons.ini"] = weapons_text if weapons_text.endswith("\n") else weapons_text + "\n"

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

    factory_text = (TOOL / "objects" / "RussiaWarFactoryV25.ini").read_text("latin1").replace("\r\n", "\n")
    fac_objs = parse_blocks(factory_text, "Object")
    if WF2_OBJ not in fac_objs:
        raise SystemExit("RussiaWarFactoryV25 object missing")
    fac_block = fac_objs[WF2_OBJ]
    if "RussiaWarFactoryV25CommandSet" not in fac_block:
        raise SystemExit("WF2 CommandSet mismatch")
    if re.search(r"(?m)^\s*Model\s*=\s*StructureHamVhe\b", fac_block) is None:
        raise SystemExit("WF2 must use StructureHamVhe")
    if "RussiaWarFactoryCommandSet" in fac_block and "RussiaWarFactoryV25CommandSet" not in fac_block:
        raise SystemExit("WF2 reused old factory CommandSet")
    if re.search(r"(?m)^\s*KindOf\s*=.*FS_WARFACTORY", fac_block) is None:
        raise SystemExit("WF2 missing FS_WARFACTORY")
    obj_texts["RussiaWarFactoryV25.ini"] = factory_text if factory_text.endswith("\n") else factory_text + "\n"
    verify_w3d(ART_SRC / "W3D" / "StructureHamVhe.W3D", [b"cAb"])

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
    if "MappedImage RUWARFCIII" not in map_text:
        raise SystemExit("MappedImage RUWARFCIII missing")

    art_files = needed_art()
    art_copied: list[tuple[str, Path]] = []
    for rel_src, rel_dst in art_files:
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

    zip_names = [dst for _, dst in art_files]
    zip_names += [
        "Data/INI/CommandButton.ini",
        "Data/INI/CommandSet.ini",
        "Data/INI/" + MAP_REL,
        *obj_rels,
    ]
    zip_path = OUT_DIR / "SPECTER_SS2_RUSSIA_V25_CC_WF.zip"
    mapping = {name: OUT_DIR / name for name in zip_names}
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in zip_names:
            zf.write(mapping[name], name)
        if zf.namelist() != zip_names:
            raise SystemExit(zf.namelist())
        if any(n.lower().endswith(".big") or n.endswith(".txt") or n.endswith(".md") for n in zf.namelist()):
            raise SystemExit("ZIP must not contain BIG or reports")
    shutil.copy2(zip_path, ZIP_ROOT)

    slot_lines = "\n".join(
        f"  {s['building']:3} slot {s['slot']:2} = {s['btn']} -> {s['obj']}  ({s['label']})"
        f"  [V25 {s['v25_btn']} / {s['v25_obj']}]"
        for s in SYSTEMS
    )
    obj_sha = "\n".join(f"SHA-256 {rel:96} {sha256(OUT_DIR / rel)}" for rel in obj_rels)
    art_sha = "\n".join(
        f"SHA-256 {name:44} {sha256(path)}"
        for name, path in art_copied
        if name.endswith(".W3D") or name.lower().endswith("tb.tga") or name.endswith("RUWARFCIII.tga")
    )
    digest = sha256(zip_path)
    report = f"""SS2 Russia V25 Command Center + independent War Factory 2 pack (Loose Data, no BIG)
Live Russia CC           RussiaCommandCenter / RussiaCommandCenterCommandSet
Merge base               North Korea V25 CC9 CS/CB (USA + China + Iran + France + England + NK + loaders)
Russia CC keeps          1 Dozer, 2 TorM2M, 3 9K317, 4 55K6E, 5 PantsirS1M, 6 S400, 7 S500, 8 Dozerm, 10 BTR82A, 14 Sell
Empty used               9, 11, 12, 13, 15, 16, 17, 18
New loader               RussiaVehicleDozerm
Tunnel                   RussiaPowerStationm / Command_ConstructRussiaPowerStationm (dozerm slot 1, unchanged)
Old War Factory          RussiaWarFactory / Command_ConstructRussiaWarFactory (old dozer slot 9, unchanged)
New War Factory          RussiaWarFactoryV25 / Command_ConstructRussiaWarFactoryV25 (dozerm slot 2)
New WF CommandSet        RussiaWarFactoryV25CommandSet
New WF model             StructureHamVhe (V25 RussiaWarFactory3)

{slot_lines}

Identity notes
- S-400/S-500 V25 ports use RussiaVehicleV25S400/S500, not live SS2 RussiaVehicleS400/S500.
- 9S119M1 maps to V25 Russia9S18M1 / UR9S18M1 (Buk Snow Drift); V25 has no 9S119M1 object.
- Tunguska is V25 Ukrania2K22 / INTGSK, the only Tunguska 2K22 in V25.
- 9K33 Osa is ported once from V25 RussiaTankT64 / RU9K33.
- Strela-10 is V25 RussiaMTLB / RUMTLB, unique object vs NorthKoreaVehicleV25Strela10.
- Independent WF2 does not replace RussiaWarFactory or RussiaWarFactory_T.

SHA-256 CommandSet.ini               {sha256(out_ini / 'CommandSet.ini')}
SHA-256 CommandButton.ini            {sha256(out_ini / 'CommandButton.ini')}
SHA-256 MappedImage                  {sha256(out_ini / MAP_REL)}
{obj_sha}
{art_sha}
SHA-256 ZIP                          {digest}
ZIP {zip_path} {zip_path.stat().st_size} members={len(zip_names)}
Copy {ZIP_ROOT}
26-country tunnel loaders preserved. America, China, Iran, France, England, NK CC unchanged.
Old Russia War Factory unchanged. Vehicles have no Shadow line. In-game test was not run.
"""
    (OUT_DIR / "BUILD_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SPECTER_SS2_RUSSIA_V25_CC_WF.zip.sha256").write_text(
        digest + "  SPECTER_SS2_RUSSIA_V25_CC_WF.zip\n", encoding="ascii"
    )
    print(report)
    print("ZIP members:")
    with zipfile.ZipFile(zip_path) as zf:
        for n in zf.namelist():
            print(" ", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
