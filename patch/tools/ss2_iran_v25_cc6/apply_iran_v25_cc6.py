#!/usr/bin/env python3
"""Six V25 Iran AD/missile systems onto SPECTER SS2 Iran Command Center.

Merges onto the China V25 CC12 ControlBar. Moves existing Hoveyzeh from
IranExpandedHQCommandSet slot 12 to IranWarfactoryCommandSet slot 9 without
duplicating the Hoveyzeh object or button.
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
SRC_CS = Path("patch/Release/SPECTER_SS2_CHINA_V25_CC12/Data/INI/CommandSet.ini")
SRC_CB = Path("patch/Release/SPECTER_SS2_CHINA_V25_CC12/Data/INI/CommandButton.ini")
SRC_MAP = TOOL / "IranV25CC6_Images.ini"
OUT_DIR = Path("patch/Release/SPECTER_SS2_IRAN_V25_CC6")
CC_NAME = "IranExpandedHQCommandSet"
WF_NAME = "IranWarfactoryCommandSet"
ART_SRC = TOOL / "art"
OBJ_DIR = "Object/Specter/Iranian Army/V25CommandCenter"
MAP_REL = "MappedImages/HandCreated/IranV25CC6_Images.ini"
HOVEYZEH_BTN = "Command_ConstructIranVehicleHoveyzeh"
HOVEYZEH_OBJ = "IranVehicleHoveyzeh"

SYSTEMS = [
    {"slot": 2, "btn": "Command_ConstructIranVehicleV25Sayyad2", "obj": "IranVehicleV25Sayyad2", "ini": "IranVehicleV25Sayyad2.ini", "model": "Sayyad", "image": "SayyadTB", "w3d": "Sayyad.W3D", "need": [b"TURRET01", b"WHEEL01", b"WEAPONA01"], "draw": "W3DTruckDraw", "label": "Sayyad-2", "no_pitch": True},
    {"slot": 3, "btn": "Command_ConstructIranVehicleV251S91", "obj": "IranVehicleV251S91", "ini": "IranVehicleV251S91.ini", "model": "2K12RD", "image": "2K12RDTB", "w3d": "2K12RD.W3D", "need": [b"CORE"], "draw": "W3DTankDraw", "label": "1S91 Radar", "extra_w3d": ("2K12RDw.W3D", [b"TIRE01", b"TIRE08"])},
    {"slot": 4, "btn": "Command_ConstructIranVehicleV25SAM6", "obj": "IranVehicleV25SAM6", "ini": "IranVehicleV25SAM6.ini", "model": "IR2K12", "image": "IR2K12TB", "w3d": "IR2K12.W3D", "need": [b"TURRET", b"TURRETEL", b"MISSILE01"], "draw": "W3DTankDraw", "label": "SAM-6", "extra_w3d": ("IR2K12w.W3D", [b"TIRE01", b"TIRE08"])},
    {"slot": 5, "btn": "Command_ConstructIranVehicleV25Raad", "obj": "IranVehicleV25Raad", "ini": "IranVehicleV25Raad.ini", "model": "IRBUKM", "image": "IRBUKMTB", "w3d": "IRBUKM.W3D", "need": [b"TURRET01", b"TURRETEL01", b"TIRE01"], "draw": "W3DTruckDraw", "label": "Raad"},
    {"slot": 12, "btn": "Command_ConstructIranVehicleV25Kolchuga", "obj": "IranVehicleV25Kolchuga", "ini": "IranVehicleV25Kolchuga.ini", "model": "Kolchuga", "image": "KolchugaTB", "w3d": "Kolchuga.W3D", "need": [b"WHEEL01", b"WHEEL06"], "draw": "W3DTruckDraw", "label": "Kolchuga"},
    {"slot": 14, "btn": "Command_ConstructIranVehicleV25Noor", "obj": "IranVehicleV25Noor", "ini": "IranVehicleV25Noor.ini", "model": "SDNoor", "image": "NoorTB", "w3d": "SDNoor.W3D", "need": [b"WEAPONA01", b"WHEEL01"], "draw": "W3DTruckDraw", "label": "Noor", "no_pitch": True},
]

ART_FILES = [
    ("W3D/Sayyad.W3D", "Art/W3D/Sayyad.W3D"),
    ("W3D/2K12RD.W3D", "Art/W3D/2K12RD.W3D"),
    ("W3D/2K12RDw.W3D", "Art/W3D/2K12RDw.W3D"),
    ("W3D/IR2K12.W3D", "Art/W3D/IR2K12.W3D"),
    ("W3D/IR2K12w.W3D", "Art/W3D/IR2K12w.W3D"),
    ("W3D/IRBUKM.W3D", "Art/W3D/IRBUKM.W3D"),
    ("W3D/Kolchuga.W3D", "Art/W3D/Kolchuga.W3D"),
    ("W3D/SDNoor.W3D", "Art/W3D/SDNoor.W3D"),
    ("Textures/SayyadTB.tga", "Art/Textures/SayyadTB.tga"),
    ("Textures/2K12RDTB.tga", "Art/Textures/2K12RDTB.tga"),
    ("Textures/IR2K12TB.tga", "Art/Textures/IR2K12TB.tga"),
    ("Textures/IRBUKMTB.tga", "Art/Textures/IRBUKMTB.tga"),
    ("Textures/KolchugaTB.tga", "Art/Textures/KolchugaTB.tga"),
    ("Textures/NoorTB.tga", "Art/Textures/NoorTB.tga"),
    ("Textures/2K12RD01.dds", "Art/Textures/2K12RD01.dds"),
    ("Textures/2K12RD02.dds", "Art/Textures/2K12RD02.dds"),
    ("Textures/IRSAM601.dds", "Art/Textures/IRSAM601.dds"),
    ("Textures/IRSAM602.dds", "Art/Textures/IRSAM602.dds"),
    ("Textures/IRSAM603.dds", "Art/Textures/IRSAM603.dds"),
    ("Textures/SDIRBUKM.dds", "Art/Textures/SDIRBUKM.dds"),
    ("Textures/Kolchga1.dds", "Art/Textures/Kolchga1.dds"),
    ("Textures/Kolchga2.dds", "Art/Textures/Kolchga2.dds"),
    ("Textures/NOOR01.dds", "Art/Textures/NOOR01.dds"),
    ("Textures/NOOR02.dds", "Art/Textures/NOOR02.dds"),
    ("Textures/NOOR03.dds", "Art/Textures/NOOR03.dds"),
    ("Textures/NOOR04.dds", "Art/Textures/NOOR04.dds"),
    ("Textures/SDPAC201.dds", "Art/Textures/SDPAC201.dds"),
    ("Textures/RUA222W.dds", "Art/Textures/RUA222W.dds"),
    ("Textures/SDNSM04.dds", "Art/Textures/SDNSM04.dds"),
    ("Textures/Glass1.tga", "Art/Textures/Glass1.tga"),
]

CC_KEEP = {
    1: "Command_ConstructIranVehicleDozer",
    6: "Command_ConstructIran_Bavar",
    7: "Command_ConstructIran_Meraj",
    8: "Command_ConstructIranVehicleBTR60",
    9: "Command_ConstructIranVehicleDozerm",
    10: "Command_ConstructIranVehicleJeepToophan",
    11: "Command_ConstructIranVehicleJeep105",
    13: "Command_ConstructIranVehicleMajid",
}
WF_KEEP = {
    1: "Command_ConstructIranTankKarrar",
    3: "Command_ConstructIranVehicleRaadSPG",
    13: "Command_ConstructIranRaadM2EK",
    14: "Command_Sell",
}
CHINA_KEEP = {1: "Command_ConstructChinaDozer", 4: "Command_ConstructChinaVehicleDozerm"}
USA_KEEP = {
    1: "Command_ConstructAmericaDozer",
    2: "Command_ConstructAmericaVehicleMeadsRadar",
    10: "Command_ConstructAmericaVehiclePatriotPAC3",
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
        f"  TextLabel          = CONTROLBAR:Construct{sys['obj']}\n"
        f"  ButtonImage        = {sys['image']}\n"
        f"  ButtonBorderType   = BUILD\n"
        f"  DescriptLabel      = CONTROLBAR:ToolTip{sys['obj']}\n"
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
    if "DeployStyleAIUpdate" in block:
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
    if any(name in ("IranRaadM2EK", "IranVehicleHoveyzeh", "GLAVehicleRadarVan", "IranShilka") for name in objs):
        raise SystemExit(f"{sys['obj']} reused a live SS2 object")
    if sys["obj"] == "IranVehicleV25SAM6" and re.search(r"(?m)^\s*Model\s*=\s*IRZSU\b", block):
        raise SystemExit("SAM-6 must not use Shilka model")
    if sys["obj"] == "IranVehicleV25Raad" and re.search(r"(?m)^\s*Model\s*=\s*Irn_RaadSam\b", block):
        raise SystemExit("Raad must not reuse SS2 Raad-M2 model")


def main() -> int:
    subprocess.check_call([sys.executable, str(TOOL / "write_objects.py")])
    if not SRC_CS.is_file() or not SRC_CB.is_file():
        raise SystemExit(f"China CC12 ControlBar missing: {SRC_CS}")
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    src_cs = SRC_CS.read_text("latin1").replace("\r\n", "\n")
    src_cb = SRC_CB.read_text("latin1").replace("\r\n", "\n")
    cs_blocks = parse_blocks(src_cs, "CommandSet")
    cb_blocks = parse_blocks(src_cb, "CommandButton")
    unique_count(list(cs_blocks), "source CommandSet.ini")
    unique_count(list(cb_blocks), "source CommandButton.ini")

    iran_cc = slots_of(cs_blocks[CC_NAME])
    for slot, btn in CC_KEEP.items():
        if iran_cc.get(slot) != btn:
            raise SystemExit(f"{CC_NAME} slot {slot} is {iran_cc.get(slot)}, expected {btn}")
    if iran_cc.get(12) != HOVEYZEH_BTN:
        raise SystemExit(f"Hoveyzeh not on CC slot 12: {iran_cc.get(12)}")
    if iran_cc.get(13) != "Command_ConstructIranVehicleMajid":
        raise SystemExit("slot 13 is not Majid")
    if HOVEYZEH_BTN not in cb_blocks:
        raise SystemExit("Hoveyzeh button missing")
    hov_obj = re.search(r"(?m)^\s*Object\s*=\s*(\S+)", cb_blocks[HOVEYZEH_BTN])
    if not hov_obj or hov_obj.group(1) != HOVEYZEH_OBJ:
        raise SystemExit("Hoveyzeh button object mismatch")

    iran_wf = slots_of(cs_blocks[WF_NAME])
    if 9 in iran_wf:
        raise SystemExit(f"WF slot 9 occupied by {iran_wf[9]}")
    for slot, btn in WF_KEEP.items():
        if iran_wf.get(slot) != btn:
            raise SystemExit(f"{WF_NAME} slot {slot} is {iran_wf.get(slot)}, expected {btn}")

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
    forbidden = {HOVEYZEH_BTN, "Command_ConstructGLAVehicleRadarVan", "Command_ConstructIranRaadM2EK", "Command_Sell", "Command_SetRallyPoint"}
    for btn in new_btns:
        if btn in cb_blocks:
            raise SystemExit(f"button already exists {btn}")
        if btn in forbidden:
            raise SystemExit(f"must not reuse {btn}")

    sell_before = cb_blocks["Command_Sell"]
    rally_before = cb_blocks["Command_SetRallyPoint"]
    hov_before = cb_blocks[HOVEYZEH_BTN]
    china_before = cs_blocks["ChinaCommandCenterCommandSet"]
    usa_before = cs_blocks["AmericaCommandCenterCommandSet"]
    turkey_before = cs_blocks["TurkeyCommandCenterCommandSet"]
    iran_hq_unused_before = cs_blocks["IranHQCommandSet"]

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
    new_cs = rewrite_slots(src_cs, CC_NAME, cc_assign, replace=True)
    new_cs = rewrite_slots(new_cs, WF_NAME, {9: HOVEYZEH_BTN}, replace=False)
    btn_text = "\n".join(btn_block(s) for s in SYSTEMS)
    new_cb = src_cb.rstrip() + "\n\n; SPECTER SS2 Iran V25 Command Center systems.\n\n" + btn_text

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
    for slot, btn in CC_KEEP.items():
        if won_cc[slot] != btn:
            raise SystemExit(f"kept CC slot {slot} lost")
    if won_cc.get(12) == HOVEYZEH_BTN:
        raise SystemExit("Hoveyzeh still on CC slot 12")
    if won_cc.get(13) != "Command_ConstructIranVehicleMajid":
        raise SystemExit("slot 13 changed")
    if HOVEYZEH_BTN in won_cc.values():
        raise SystemExit("Hoveyzeh still on Command Center")

    won_wf = slots_of(new_cs_blocks[WF_NAME])
    if won_wf.get(9) != HOVEYZEH_BTN:
        raise SystemExit("Hoveyzeh not on WF slot 9")
    for slot, btn in WF_KEEP.items():
        if won_wf[slot] != btn:
            raise SystemExit(f"kept WF slot {slot} lost")
    if new_cs_blocks["ChinaCommandCenterCommandSet"] != china_before:
        raise SystemExit("China CC changed")
    if new_cs_blocks["AmericaCommandCenterCommandSet"] != usa_before:
        raise SystemExit("America CC changed")
    if new_cs_blocks["TurkeyCommandCenterCommandSet"] != turkey_before:
        raise SystemExit("Turkey CC changed")
    if new_cs_blocks["IranHQCommandSet"] != iran_hq_unused_before:
        raise SystemExit("unused IranHQCommandSet changed")
    if button_core(new_cb_blocks["Command_Sell"]) != button_core(sell_before):
        raise SystemExit("Command_Sell definition changed")
    if button_core(new_cb_blocks["Command_SetRallyPoint"]) != button_core(rally_before):
        raise SystemExit("Command_SetRallyPoint definition changed")
    if button_core(new_cb_blocks[HOVEYZEH_BTN]) != button_core(hov_before):
        raise SystemExit("Hoveyzeh button definition changed")

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
    weapons_text = (TOOL / "objects" / "IranV25CC6_Weapons.ini").read_text("latin1").replace("\r\n", "\n")
    if "IranV25SAM_AA" not in weapons_text or "PENALTY" not in weapons_text:
        raise SystemExit("shared SAM AA missing")
    obj_texts["IranV25CC6_Weapons.ini"] = weapons_text if weapons_text.endswith("\n") else weapons_text + "\n"

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
    zip_path = OUT_DIR / "SPECTER_SS2_IRAN_V25_CC6.zip"
    mapping = {name: OUT_DIR / name for name in zip_names}
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in zip_names:
            zf.write(mapping[name], name)
        if zf.namelist() != zip_names:
            raise SystemExit(zf.namelist())
        if any(n.lower().endswith(".big") or n.endswith(".txt") or n.endswith(".md") for n in zf.namelist()):
            raise SystemExit("ZIP must not contain BIG or reports")

    slot_lines = "\n".join(
        f"  Iran CC slot {s['slot']:2} = {s['btn']} -> {s['obj']}  ({s['label']})"
        for s in SYSTEMS
    )
    obj_sha = "\n".join(f"SHA-256 {rel:72} {sha256(OUT_DIR / rel)}" for rel in obj_rels)
    art_sha = "\n".join(
        f"SHA-256 {name:44} {sha256(path)}"
        for name, path in art_copied
        if name.endswith(".W3D") or name.endswith("TB.tga")
    )
    report = f"""SS2 Iran V25 six-system Command Center pack (Loose Data, no BIG)
Merge base               China V25 CC12 CS/CB (America packs + China 12 + loaders)
Iran CC CommandSet       IranExpandedHQCommandSet (live IranCommandCenter)
Iran CC keeps            1 Dozer, 6 Bavar, 7 Meraj, 8 BTR60, 9 Tunnel Loader,
                         10 Jeep Toophan, 11 Jeep 105, 13 Majid
Iran CC slot 14          Noor replaces Sell on this CommandSet only
Hoveyzeh                 Command_ConstructIranVehicleHoveyzeh / IranVehicleHoveyzeh
                         moved CC slot 12 -> War Factory slot 9 (same object/button)

{slot_lines}
  Iran WF slot  9 = {HOVEYZEH_BTN} -> {HOVEYZEH_OBJ}  (moved, not duplicated)

Identity notes
- SAM-6 is IranSAM6 / IR2K12, not IranShilka / IRZSU.
- Raad is V25 IranBukM / IRBUKM; V25 has no object named Raad. Not SS2 IranRaadM2EK.
- Kolchuga is unique vs live SS2 GLAVehicleRadarVan.

SHA-256 CommandSet.ini               {sha256(out_ini / 'CommandSet.ini')}
SHA-256 CommandButton.ini            {sha256(out_ini / 'CommandButton.ini')}
SHA-256 MappedImage                  {sha256(out_ini / MAP_REL)}
{obj_sha}
{art_sha}
SHA-256 ZIP                          {sha256(zip_path)}
ZIP {zip_path} {zip_path.stat().st_size} members={len(zip_names)}
26-country tunnel loaders preserved. America and China CC unchanged. No BIG.
Vehicles have no Shadow line. In-game test was not run.
"""
    (OUT_DIR / "BUILD_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SPECTER_SS2_IRAN_V25_CC6.zip.sha256").write_text(
        sha256(zip_path) + "  SPECTER_SS2_IRAN_V25_CC6.zip\n", encoding="ascii"
    )
    print(report)
    print("ZIP members:")
    with zipfile.ZipFile(zip_path) as zf:
        for n in zf.namelist():
            print(" ", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
