#!/usr/bin/env python3
"""Nine V25 North Korea systems onto SPECTER SS2 North Korea Command Center.

Live NK HQ is NorthKorea_CommandCenter / NorthKorea_CommandCenterCommandSet.
Merges onto the England V25 CC8 ControlBar. Occupied NK CC slots are kept.
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
SRC_CS = Path("patch/Release/SPECTER_SS2_ENGLAND_V25_CC8/Data/INI/CommandSet.ini")
SRC_CB = Path("patch/Release/SPECTER_SS2_ENGLAND_V25_CC8/Data/INI/CommandButton.ini")
SRC_MAP = TOOL / "NorthKoreaV25CC9_Images.ini"
OUT_DIR = Path("patch/Release/SPECTER_SS2_NORTHKOREA_V25_CC9")
ZIP_ROOT = Path("patch/Release/SPECTER_SS2_NORTHKOREA_V25_CC9.zip")
CC_NAME = "NorthKorea_CommandCenterCommandSet"
ART_SRC = TOOL / "art"
OBJ_DIR = "Object/Specter/North Korea/V25CommandCenter"
MAP_REL = "MappedImages/HandCreated/NorthKoreaV25CC9_Images.ini"

SYSTEMS = [
    {"slot": 2, "btn": "Command_ConstructNorthKoreaVehicleV25Strela10", "obj": "NorthKoreaVehicleV25Strela10", "ini": "NorthKoreaVehicleV25Strela10.ini", "model": "RUMTLB", "image": "RUMTLBTB2", "w3d": "RUMTLB.W3D", "need": [b"CORE", b"TURRET", b"TURRETEL", b"MUZZLE"], "draw": "W3DTankDraw", "label": "9K35 Strela-10", "extra_w3d": ("RUMTLBw.W3D", [b"CORE", b"TIRE01", b"TIRE08"]), "v25_obj": "NkoreaStrella10", "v25_btn": "Command_ConstructNkoreaStrella10"},
    {"slot": 3, "btn": "Command_ConstructNorthKoreaVehicleV251S91", "obj": "NorthKoreaVehicleV251S91", "ini": "NorthKoreaVehicleV251S91.ini", "model": "2K12RD", "image": "2K12RDTB", "w3d": "2K12RD.W3D", "need": [b"CORE"], "draw": "W3DTankDraw", "label": "1S91 Radar", "no_pitch": True, "radar": True, "extra_w3d": ("2K12RDw.W3D", [b"CORE", b"TIRE01", b"TIRE08"]), "v25_obj": "Infa_ChinaVehicleListeningOutpost", "v25_btn": "Infa_Command_ConstructChinaVehicleListeningOutpost"},
    {"slot": 5, "btn": "Command_ConstructNorthKoreaVehicleV25SAM6", "obj": "NorthKoreaVehicleV25SAM6", "ini": "NorthKoreaVehicleV25SAM6.ini", "model": "IR2K12", "image": "NK2K12TB", "w3d": "IR2K12.W3D", "need": [b"CORE", b"TURRET", b"TURRETEL", b"MISSILE"], "draw": "W3DTankDraw", "label": "SAM-6", "extra_w3d": ("IR2K12w.W3D", [b"CORE", b"TIRE01", b"TIRE08"]), "v25_obj": "NKoreaSA6", "v25_btn": "Infa_Command_ConstructNKTSA6"},
    {"slot": 6, "btn": "Command_ConstructNorthKoreaVehicleV25Shilka", "obj": "NorthKoreaVehicleV25Shilka", "ini": "NorthKoreaVehicleV25Shilka.ini", "model": "NKZSU23", "image": "Shilka", "w3d": "NKZSU23.W3D", "need": [b"CORE", b"TURRET01", b"TURRETEL01", b"MUZZLE"], "draw": "W3DTankDraw", "label": "Shilka", "extra_w3d": ("NKZSU23w.W3D", [b"CORE", b"TIRE01", b"TIRE08"]), "v25_obj": "Infa_ChinaTankGattling", "v25_btn": "Infa_Command_ConstructChinaTankGattling"},
    {"slot": 8, "btn": "Command_ConstructNorthKoreaVehicleV25VTT323", "obj": "NorthKoreaVehicleV25VTT323", "ini": "NorthKoreaVehicleV25VTT323.ini", "model": "NKVTTMC", "image": "VTTMCTB", "w3d": "NKVTTMC.W3D", "need": [b"CORE", b"MRTRT", b"TURRET01", b"MORT"], "draw": "W3DTankDraw", "label": "VTT-323", "no_pitch": True, "extra_w3d": ("NKVTTMCw.W3D", [b"CORE", b"TIRE01", b"TIRE07"]), "v25_obj": "NkoreaVTTMC", "v25_btn": "Command_ConstructNkoreaVTTMC"},
    {"slot": 9, "btn": "Command_ConstructNorthKoreaVehicleV25KN25", "obj": "NorthKoreaVehicleV25KN25", "ini": "NorthKoreaVehicleV25KN25.ini", "model": "NKKN25", "image": "KN25TB", "w3d": "NKKN25.W3D", "need": [b"TURRET01", b"TURRETEL02", b"MISSILE_C01", b"WHEEL01", b"WHEEL08"], "draw": "W3DTruckDraw", "label": "KN-25", "v25_obj": "NorthKoreaKN25", "v25_btn": "Command_ConstructNorthKoreaKN25"},
    {"slot": 10, "btn": "Command_ConstructNorthKoreaVehicleV25KN400", "obj": "NorthKoreaVehicleV25KN400", "ini": "NorthKoreaVehicleV25KN400.ini", "model": "NKKN400", "image": "KN400TB", "w3d": "NKKN400.W3D", "need": [b"MISSILE_C01", b"CAB", b"TRAILER", b"WHEEL01", b"WHEEL08"], "draw": "W3DTruckDraw", "label": "KN-400", "no_pitch": True, "v25_obj": "NorthKoreaKN400", "v25_btn": "Command_ConstructNorthKoreaKN400"},
    {"slot": 11, "btn": "Command_ConstructNorthKoreaVehicleV25M1973", "obj": "NorthKoreaVehicleV25M1973", "ini": "NorthKoreaVehicleV25M1973.ini", "model": "SDM1973", "image": "M1973", "w3d": "SDM1973.W3D", "need": [b"CORE", b"TURRET01", b"AA", b"SAGR"], "draw": "W3DTankDraw", "label": "M1973", "no_pitch": True, "extra_w3d": ("SDM1973w.W3D", [b"CORE", b"WHEEL01", b"WHEEL07"]), "v25_obj": "Infa_ChinaTankECM", "v25_btn": "Infa_Command_ConstructChinaTankECM"},
    {"slot": 12, "btn": "Command_ConstructNorthKoreaVehicleV25BM24", "obj": "NorthKoreaVehicleV25BM24", "ini": "NorthKoreaVehicleV25BM24.ini", "model": "NKBM24", "image": "NKBM24TB", "w3d": "NKBM24.W3D", "need": [b"TURRET01", b"TURRETEL01", b"MISSILE", b"WHEEL01"], "draw": "W3DTruckDraw", "label": "BM-24", "v25_obj": "NkoreaBM24", "v25_btn": "Command_ConstructNkoreaBM24"},
]

ART_FILES = []
for sub in ("W3D", "Textures"):
    for src in sorted((ART_SRC / sub).iterdir()):
        if src.is_file():
            ART_FILES.append((f"{sub}/{src.name}", f"Art/{sub}/{src.name}"))

NK_KEEP = {
    1: "Command_ConstructNorthKorea_VT72B",
    4: "Command_ConstructNorthKorea_VehicleDozerm",
    7: "Command_ConstructNorthKorea_Hwasong15BB",
    13: "Command_SetRallyPoint",
    14: "Command_Sell",
}
BRITAIN_KEEP = {
    1: "Command_ConstructBritainVehicleDozer",
    5: "Command_ConstructBritainVehicleV25SkySabre",
    12: "Command_ConstructBritainVehicleV25FV432S",
}
FRANCE_KEEP = {
    5: "Command_ConstructFranceVehicleV25Roland",
    10: "Command_ConstructFranceVehicleV25VPM81",
}
IRAN_KEEP = {
    2: "Command_ConstructIranVehicleV25Sayyad2",
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
    "Command_ConstructNorthKorea_VT72B",
    "Command_ConstructNorthKorea_VehicleDozerm",
    "Command_ConstructNorthKorea_Hwasong15BB",
    "Command_ConstructIranVehicleV251S91",
    "Command_ConstructIranVehicleV25SAM6",
}
FORBIDDEN_OBJ = {
    "NorthKorea_VTT323",
    "NorthKorea_KN23",
    "NorthKorea_Hwasong15BB",
    "IranVehicleV251S91",
    "IranVehicleV25SAM6",
    "NkoreaStrella10",
    "NKoreaSA6",
    "Infa_ChinaTankGattling",
    "Infa_ChinaTankECM",
    "Infa_ChinaVehicleListeningOutpost",
    "NorthKoreaKN25",
    "NorthKoreaKN400",
    "NkoreaBM24",
    "NkoreaVTTMC",
}

LABELS = {
    "Command_ConstructNorthKoreaVehicleV25Strela10": "NorthKorea_Strella10",
    "Command_ConstructNorthKoreaVehicleV251S91": "Iran_An1S91",
    "Command_ConstructNorthKoreaVehicleV25SAM6": "Egypt_Sam6",
    "Command_ConstructNorthKoreaVehicleV25Shilka": "Iran_Shilka",
    "Command_ConstructNorthKoreaVehicleV25VTT323": "NorthKorea_VTT-323",
    "Command_ConstructNorthKoreaVehicleV25KN25": "NorthKorea_KN-25",
    "Command_ConstructNorthKoreaVehicleV25KN400": "NorthKorea_KN-400",
    "Command_ConstructNorthKoreaVehicleV25M1973": "CONTROLBAR:M1973",
    "Command_ConstructNorthKoreaVehicleV25BM24": "NorthKorea_BM-24",
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
    if sys["obj"] == "NorthKoreaVehicleV25VTT323" and "NorthKorea_VTT323" in block.split()[1:2]:
        raise SystemExit("VTT-323 must not reuse SS2 NorthKorea_VTT323")
    if sys["obj"] == "NorthKoreaVehicleV25SAM6" and re.search(r"(?m)^\s*Model\s*=\s*IR2K12\b", block) is None:
        raise SystemExit("NK SAM-6 must use IR2K12")
    if sys["obj"] == "NorthKoreaVehicleV25Shilka" and re.search(r"(?m)^\s*Model\s*=\s*NKZSU23\b", block) is None:
        raise SystemExit("Shilka must use NKZSU23")
    if sys.get("extra_w3d") and "AttachToBoneInAnotherModule" not in block:
        raise SystemExit(f"{sys['obj']} wheels must attach to CORE")
    if sys.get("radar") and "StealthDetectorUpdate" not in block:
        raise SystemExit("1S91 missing radar detector")


def main() -> int:
    subprocess.check_call([sys.executable, str(TOOL / "write_objects.py")])
    if not SRC_CS.is_file() or not SRC_CB.is_file():
        raise SystemExit(f"England CC8 ControlBar missing: {SRC_CS}")
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
        raise SystemExit("NorthKorea_CommandCenterCommandSet missing")

    nk_cc = slots_of(cs_blocks[CC_NAME])
    for slot, btn in NK_KEEP.items():
        if nk_cc.get(slot) != btn:
            raise SystemExit(f"{CC_NAME} slot {slot} is {nk_cc.get(slot)}, expected {btn}")
    occupied_keep = set(NK_KEEP)
    for s in SYSTEMS:
        if s["slot"] in occupied_keep:
            raise SystemExit(f"refusing to replace occupied NK slot {s['slot']}")
        if s["slot"] in nk_cc:
            raise SystemExit(f"NK CC slot {s['slot']} already occupied by {nk_cc[s['slot']]}")
    empty = [i for i in range(1, 19) if i not in nk_cc]
    if len(empty) < 9:
        raise SystemExit(f"not enough empty NK CC slots: empty={empty} need=9")

    for name, keep in (
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

    new_btns = [s["btn"] for s in SYSTEMS]
    unique_count(new_btns, "new buttons")
    for s in SYSTEMS:
        s["v25_label"] = LABELS[s["btn"]]
        if s["btn"] in cb_blocks or s["btn"] in FORBIDDEN_BTN:
            raise SystemExit(f"must not reuse button {s['btn']}")
        if s["obj"] in FORBIDDEN_OBJ:
            raise SystemExit(f"must not reuse object {s['obj']}")

    sell_before = cb_blocks["Command_Sell"]
    rally_before = cb_blocks["Command_SetRallyPoint"]
    china_before = cs_blocks["ChinaCommandCenterCommandSet"]
    usa_before = cs_blocks["AmericaCommandCenterCommandSet"]
    iran_before = cs_blocks["IranExpandedHQCommandSet"]
    france_before = cs_blocks["FranceCommandCenterCommandSet"]
    britain_before = cs_blocks["BritainCommandCenterCommandSet"]
    turkey_before = cs_blocks["TurkeyCommandCenterCommandSet"]
    nk_wf_before = cs_blocks.get("NorthKorea_WarFactoryCommandSet", "")
    hwasong_before = button_core(cb_blocks["Command_ConstructNorthKorea_Hwasong15BB"])
    britain_sky_before = button_core(cb_blocks["Command_ConstructBritainVehicleV25SkySabre"])
    iran_sam_before = button_core(cb_blocks["Command_ConstructIranVehicleV25SAM6"])

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
    new_cb = src_cb.rstrip() + "\n\n; SPECTER SS2 North Korea V25 Command Center systems.\n\n" + btn_text

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
    for slot, btn in NK_KEEP.items():
        if won_cc[slot] != btn:
            raise SystemExit(f"kept NK CC slot {slot} lost")
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
    if new_cs_blocks["TurkeyCommandCenterCommandSet"] != turkey_before:
        raise SystemExit("Turkey CC changed")
    if nk_wf_before and new_cs_blocks.get("NorthKorea_WarFactoryCommandSet") != nk_wf_before:
        raise SystemExit("NK War Factory changed")
    if button_core(new_cb_blocks["Command_Sell"]) != button_core(sell_before):
        raise SystemExit("Command_Sell definition changed")
    if button_core(new_cb_blocks["Command_SetRallyPoint"]) != button_core(rally_before):
        raise SystemExit("Command_SetRallyPoint definition changed")
    if button_core(new_cb_blocks["Command_ConstructNorthKorea_Hwasong15BB"]) != hwasong_before:
        raise SystemExit("existing NK Hwasong15BB button changed")
    if button_core(new_cb_blocks["Command_ConstructBritainVehicleV25SkySabre"]) != britain_sky_before:
        raise SystemExit("England Sky Sabre button changed")
    if button_core(new_cb_blocks["Command_ConstructIranVehicleV25SAM6"]) != iran_sam_before:
        raise SystemExit("Iran SAM-6 button changed")

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
    weapons_text = (TOOL / "objects" / "NorthKoreaV25CC9_Weapons.ini").read_text("latin1").replace("\r\n", "\n")
    if "NorthKoreaV25Strela_AA" not in weapons_text or "NorthKoreaV25SAM_AA" not in weapons_text:
        raise SystemExit("shared North Korea weapons missing")
    obj_texts["NorthKoreaV25CC9_Weapons.ini"] = weapons_text if weapons_text.endswith("\n") else weapons_text + "\n"

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
    zip_path = OUT_DIR / "SPECTER_SS2_NORTHKOREA_V25_CC9.zip"
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
        f"  NK CC slot {s['slot']:2} = {s['btn']} -> {s['obj']}  ({s['label']})"
        f"  [V25 {s['v25_btn']} / {s['v25_obj']}]"
        for s in SYSTEMS
    )
    obj_sha = "\n".join(f"SHA-256 {rel:88} {sha256(OUT_DIR / rel)}" for rel in obj_rels)
    art_sha = "\n".join(
        f"SHA-256 {name:44} {sha256(path)}"
        for name, path in art_copied
        if name.endswith(".W3D") or name.lower().endswith("tb.tga") or name.endswith("Shilkatb.tga")
    )
    digest = sha256(zip_path)
    report = f"""SS2 North Korea V25 nine-system Command Center pack (Loose Data, no BIG)
Live NK CC               NorthKorea_CommandCenter / NorthKorea_CommandCenterCommandSet
Merge base               England V25 CC8 CS/CB (America + China + Iran + France + England + loaders)
NK CC keeps              1 VT72B, 4 Dozerm, 7 Hwasong15BB, 13 Rally, 14 Sell
Empty remaining          15, 16, 17, 18

{slot_lines}

Identity notes
- Strela-10 is NkoreaStrella10 / RUMTLB, not a substitute SAM.
- 1S91 is Infa_ChinaVehicleListeningOutpost / 2K12RD (NK Infantry-General slot).
- SAM-6 is NKoreaSA6 / IR2K12 with NK2K12TB, unique from IranVehicleV25SAM6.
- Shilka is Infa_ChinaTankGattling / NKZSU23.
- VTT-323 is NkoreaVTTMC / NKVTTMC, not SS2 NorthKorea_VTT323.
- KN-25 is NorthKoreaKN25 / NKKN25.
- KN-400 is NorthKoreaKN400 / NKKN400; rider-deploy omitted.
- M1973 is Infa_ChinaTankECM / SDM1973. V25 cameo TGA NKM1973TB.tga is absent from the V25 Art archive.
- BM-24 is NkoreaBM24 / NKBM24.

SHA-256 CommandSet.ini               {sha256(out_ini / 'CommandSet.ini')}
SHA-256 CommandButton.ini            {sha256(out_ini / 'CommandButton.ini')}
SHA-256 MappedImage                  {sha256(out_ini / MAP_REL)}
{obj_sha}
{art_sha}
SHA-256 ZIP                          {digest}
ZIP {zip_path} {zip_path.stat().st_size} members={len(zip_names)}
Copy {ZIP_ROOT}
26-country tunnel loaders preserved. America, China, Iran, France, England CC unchanged. No BIG.
Vehicles have no Shadow line. In-game test was not run.
"""
    (OUT_DIR / "BUILD_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SPECTER_SS2_NORTHKOREA_V25_CC9.zip.sha256").write_text(
        digest + "  SPECTER_SS2_NORTHKOREA_V25_CC9.zip\n", encoding="ascii"
    )
    print(report)
    print("ZIP members:")
    with zipfile.ZipFile(zip_path) as zf:
        for n in zf.namelist():
            print(" ", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
