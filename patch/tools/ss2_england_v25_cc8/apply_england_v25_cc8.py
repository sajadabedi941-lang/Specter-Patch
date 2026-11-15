#!/usr/bin/env python3
"""Eight V25 England systems onto SPECTER SS2 Britain Command Center.

Live England HQ is BritainCommandCenter / BritainCommandCenterCommandSet.
Merges onto the France V25 CC6 ControlBar. Occupied Britain CC slots are kept.
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
SRC_CS = Path("patch/Release/SPECTER_SS2_FRANCE_V25_CC6/Data/INI/CommandSet.ini")
SRC_CB = Path("patch/Release/SPECTER_SS2_FRANCE_V25_CC6/Data/INI/CommandButton.ini")
SRC_MAP = TOOL / "EnglandV25CC8_Images.ini"
OUT_DIR = Path("patch/Release/SPECTER_SS2_ENGLAND_V25_CC8")
ZIP_ROOT = Path("patch/Release/SPECTER_SS2_ENGLAND_V25_CC8.zip")
CC_NAME = "BritainCommandCenterCommandSet"
ART_SRC = TOOL / "art"
OBJ_DIR = "Object/Specter/British Armed Forces/V25CommandCenter"
MAP_REL = "MappedImages/HandCreated/EnglandV25CC8_Images.ini"

SYSTEMS = [
    {"slot": 5, "btn": "Command_ConstructBritainVehicleV25SkySabre", "obj": "BritainVehicleV25SkySabre", "ini": "BritainVehicleV25SkySabre.ini", "model": "SkySabre", "image": "SKYSBRTB", "w3d": "SkySabre.W3D", "need": [b"MISSILE_C01", b"WHEEL01", b"WHEEL08"], "draw": "W3DTruckDraw", "label": "Sky Sabre", "no_pitch": True, "v25_obj": "UKSkySabre", "v25_btn": "Command_ConstructUKSkySabre"},
    {"slot": 6, "btn": "Command_ConstructBritainVehicleV25Giraffe", "obj": "BritainVehicleV25Giraffe", "ini": "BritainVehicleV25Giraffe.ini", "model": "SKYSRBR", "image": "SKYSBRRTB", "w3d": "SKYSRBR.W3D", "need": [b"WHEEL01", b"WHEEL08", b"BODY"], "draw": "W3DTruckDraw", "label": "Giraffe Radar", "no_pitch": True, "radar": True, "v25_obj": "UKGiraffe", "v25_btn": "Command_ConstructUKGiraffe"},
    {"slot": 7, "btn": "Command_ConstructBritainVehicleV25CRAM", "obj": "BritainVehicleV25CRAM", "ini": "BritainVehicleV25CRAM.ini", "model": "SDUKPX", "image": "AmericaPhlanx", "w3d": "SDUKPX.W3D", "need": [b"TURRETH", b"TURRETHEL", b"FIRE01", b"WHEEL01"], "draw": "W3DTruckDraw", "label": "C-RAM", "v25_obj": "UKPhlanx", "v25_btn": "Command_ConstructUKPhlanx"},
    {"slot": 8, "btn": "Command_ConstructBritainVehicleV25Cougar", "obj": "BritainVehicleV25Cougar", "ini": "BritainVehicleV25Cougar.ini", "model": "UKCougar", "image": "EgyMrap", "w3d": "UKCougar.W3D", "need": [b"TURRET", b"MUZZLE01", b"TIRE01", b"TIRE04"], "draw": "W3DTruckDraw", "label": "Cougar MRAP", "no_pitch": True, "v25_obj": "Lazr_AmericaTankCrusader", "v25_btn": "Lazr_Command_ConstructAmericaTankCrusader"},
    {"slot": 9, "btn": "Command_ConstructBritainVehicleV25Challenger", "obj": "BritainVehicleV25Challenger", "ini": "BritainVehicleV25Challenger.ini", "model": "UKCHNGR3", "image": "UKCHLNGR3TB", "w3d": "UKCHNGR3.W3D", "need": [b"CORE", b"TURRET01", b"MUZZLE01"], "draw": "W3DTankDraw", "label": "Challenger", "no_pitch": True, "extra_w3d": ("UKCHNGR3w.W3D", [b"CORE", b"TIRE01", b"TIRE08"]), "v25_obj": "UKChallenger3", "v25_btn": "Command_ConstructUKChallenger3"},
    {"slot": 10, "btn": "Command_ConstructBritainVehicleV25Rapier", "obj": "BritainVehicleV25Rapier", "ini": "BritainVehicleV25Rapier.ini", "model": "49KB23", "image": "49KB23TB", "w3d": "49KB23.W3D", "need": [b"CORE", b"TURRET01", b"TURRETEL_E", b"MISSILE01"], "draw": "W3DTankDraw", "label": "Tracked Rapier 49KB23", "v25_obj": "UK49KB23", "v25_btn": "Command_ConstructUK49KB23"},
    {"slot": 11, "btn": "Command_ConstructBritainVehicleV25Stormer", "obj": "BritainVehicleV25Stormer", "ini": "BritainVehicleV25Stormer.ini", "model": "UKStormer", "image": "LSFXGTTB", "w3d": "UKStormer.W3D", "need": [b"CORE", b"TURRET", b"ZHOU", b"CANNTRT"], "draw": "W3DTankDraw", "label": "Alvis Stormer", "extra_w3d": ("UKStormerw.W3D", [b"CORE", b"TIRE01", b"TIRE08"]), "v25_obj": "Lazr_AmericaTankAvenger", "v25_btn": "Lazr_Command_ConstructAmericaVehicleAvenger"},
    {"slot": 12, "btn": "Command_ConstructBritainVehicleV25FV432S", "obj": "BritainVehicleV25FV432S", "ini": "BritainVehicleV25FV432S.ini", "model": "FV432", "image": "UKFV432TB", "w3d": "FV432.W3D", "need": [b"CORE", b"MRTRT", b"TURRET01", b"MORT"], "draw": "W3DTankDraw", "label": "FV432S", "no_pitch": True, "extra_w3d": ("FV432w.W3D", [b"CORE", b"TIRE01", b"TIRE07"]), "v25_obj": "UKFV432S", "v25_btn": "Command_ConstructUKFV432S"},
]

ART_FILES = []
for sub in ("W3D", "Textures"):
    for src in sorted((ART_SRC / sub).iterdir()):
        if src.is_file():
            ART_FILES.append((f"{sub}/{src.name}", f"Art/{sub}/{src.name}"))

BRITAIN_KEEP = {
    1: "Command_ConstructBritainVehicleDozer",
    2: "Command_ConstructBritainTankPumaMech",
    3: "Command_BritainAWACS",
    4: "Command_ConstructBritainVehicleDozerm",
    14: "Command_Sell",
    15: "Command_ConstructBritainDronesMq9_AI",
    16: "Command_ConstructBritainDroneSwitchblade600",
    17: "Command_ConstructBritainDroneRQ4AI",
}
FRANCE_KEEP = {
    5: "Command_ConstructFranceVehicleV25Roland",
    6: "Command_ConstructFranceVehicleV25Arabel",
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
    "Command_ConstructBritainSkySabre",
    "Command_ConstructBritainVehicleSkySabre",
    "Command_ConstructBritainVehicleDozer",
    "Command_ConstructBritainTankPumaMech",
    "Command_BritainAWACS",
    "Command_ConstructBritainVehicleDozerm",
}
FORBIDDEN_OBJ = {
    "BritainSkySabre",
    "BritainVehicleSkySabre",
    "BritainTankChallenger2",
    "BritainVehicleStormer",
    "AmericaVehicleCRAM",
    "UKSkySabre",
    "Lazr_AmericaTankAvenger",
    "Lazr_AmericaTankCrusader",
}

LABELS = {
    "Command_ConstructBritainVehicleV25SkySabre": "UK_Sky-Sabre",
    "Command_ConstructBritainVehicleV25Giraffe": "UK_Giraffe",
    "Command_ConstructBritainVehicleV25CRAM": "America_Phlanx",
    "Command_ConstructBritainVehicleV25Cougar": "America_Mrap",
    "Command_ConstructBritainVehicleV25Challenger": "UK_Challenger3",
    "Command_ConstructBritainVehicleV25Rapier": "UK_49KB23",
    "Command_ConstructBritainVehicleV25Stormer": "UK_Stormer",
    "Command_ConstructBritainVehicleV25FV432S": "UK_FV432S",
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
    if sys["obj"] == "BritainVehicleV25SkySabre" and "Spec_SamIriCnfg" in block:
        raise SystemExit("Sky Sabre must not reuse SS2 IRIS-T structure")
    if sys["obj"] == "BritainVehicleV25Challenger" and re.search(r"(?m)^\s*Model\s*=\s*LSFChallenger2\b", block):
        raise SystemExit("Challenger must not use SS2 LSFChallenger2")
    if sys["obj"] == "BritainVehicleV25CRAM" and re.search(r"(?m)^\s*Model\s*=\s*SDCRAM\b", block):
        raise SystemExit("England C-RAM must use SDUKPX")
    if sys["obj"] == "BritainVehicleV25Stormer" and re.search(r"(?m)^\s*Model\s*=\s*LSFXG\b", block):
        raise SystemExit("Stormer must use UKStormer")
    if sys.get("extra_w3d") and "AttachToBoneInAnotherModule" not in block:
        raise SystemExit(f"{sys['obj']} wheels must attach to CORE")
    if sys.get("radar") and "StealthDetectorUpdate" not in block:
        raise SystemExit("Giraffe missing radar detector")


def main() -> int:
    subprocess.check_call([sys.executable, str(TOOL / "write_objects.py")])
    if not SRC_CS.is_file() or not SRC_CB.is_file():
        raise SystemExit(f"France CC6 ControlBar missing: {SRC_CS}")
    if "EnglandCommandCenterCommandSet" in SRC_CS.read_text("latin1"):
        raise SystemExit("unexpected EnglandCommandCenterCommandSet present")
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
        raise SystemExit("BritainCommandCenterCommandSet missing")

    britain_cc = slots_of(cs_blocks[CC_NAME])
    for slot, btn in BRITAIN_KEEP.items():
        if britain_cc.get(slot) != btn:
            raise SystemExit(f"{CC_NAME} slot {slot} is {britain_cc.get(slot)}, expected {btn}")
    occupied_keep = set(BRITAIN_KEEP)
    for s in SYSTEMS:
        if s["slot"] in occupied_keep:
            raise SystemExit(f"refusing to replace occupied Britain slot {s['slot']}")
        if s["slot"] in britain_cc:
            raise SystemExit(f"Britain CC slot {s['slot']} already occupied by {britain_cc[s['slot']]}")

    for name, keep in (
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
    turkey_before = cs_blocks["TurkeyCommandCenterCommandSet"]
    britain_dozer_before = cs_blocks["BritainDozerCommandSet"]
    britain_wf_before = cs_blocks["BritainWarfactoryCommandSet"]
    sky_before = button_core(cb_blocks["Command_ConstructBritainSkySabre"])

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
    new_cb = src_cb.rstrip() + "\n\n; SPECTER SS2 England V25 Command Center systems.\n\n" + btn_text

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
    for slot, btn in BRITAIN_KEEP.items():
        if won_cc[slot] != btn:
            raise SystemExit(f"kept Britain CC slot {slot} lost")
    if new_cs_blocks["ChinaCommandCenterCommandSet"] != china_before:
        raise SystemExit("China CC changed")
    if new_cs_blocks["AmericaCommandCenterCommandSet"] != usa_before:
        raise SystemExit("America CC changed")
    if new_cs_blocks["IranExpandedHQCommandSet"] != iran_before:
        raise SystemExit("Iran CC changed")
    if new_cs_blocks["FranceCommandCenterCommandSet"] != france_before:
        raise SystemExit("France CC changed")
    if new_cs_blocks["TurkeyCommandCenterCommandSet"] != turkey_before:
        raise SystemExit("Turkey CC changed")
    if new_cs_blocks["BritainDozerCommandSet"] != britain_dozer_before:
        raise SystemExit("Britain Dozer changed")
    if new_cs_blocks["BritainWarfactoryCommandSet"] != britain_wf_before:
        raise SystemExit("Britain War Factory changed")
    if button_core(new_cb_blocks["Command_Sell"]) != button_core(sell_before):
        raise SystemExit("Command_Sell definition changed")
    if button_core(new_cb_blocks["Command_SetRallyPoint"]) != button_core(rally_before):
        raise SystemExit("Command_SetRallyPoint definition changed")
    if button_core(new_cb_blocks["Command_ConstructBritainSkySabre"]) != sky_before:
        raise SystemExit("existing BritainSkySabre button changed")

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
    weapons_text = (TOOL / "objects" / "BritainV25CC8_Weapons.ini").read_text("latin1").replace("\r\n", "\n")
    if "BritainV25SkySabre_AA" not in weapons_text:
        raise SystemExit("shared England weapons missing")
    obj_texts["BritainV25CC8_Weapons.ini"] = weapons_text if weapons_text.endswith("\n") else weapons_text + "\n"

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
    zip_path = OUT_DIR / "SPECTER_SS2_ENGLAND_V25_CC8.zip"
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
        f"  Britain CC slot {s['slot']:2} = {s['btn']} -> {s['obj']}  ({s['label']})"
        f"  [V25 {s['v25_btn']} / {s['v25_obj']}]"
        for s in SYSTEMS
    )
    obj_sha = "\n".join(f"SHA-256 {rel:88} {sha256(OUT_DIR / rel)}" for rel in obj_rels)
    art_sha = "\n".join(
        f"SHA-256 {name:44} {sha256(path)}"
        for name, path in art_copied
        if name.endswith(".W3D") or name.endswith("TB.tga") or name.endswith("Phlanx.tga") or name.endswith("Mrap.tga")
    )
    digest = sha256(zip_path)
    report = f"""SS2 England V25 eight-system Command Center pack (Loose Data, no BIG)
Live England CC          BritainCommandCenter / BritainCommandCenterCommandSet
                         (EnglandCommandCenterCommandSet does not exist in SS2)
Merge base               France V25 CC6 CS/CB (America + China + Iran + France + loaders)
Britain CC keeps         1 Dozer, 2 Puma, 3 AWACS, 4 Dozerm, 14 Sell, 15-17 AI drones

{slot_lines}

Identity notes
- Sky Sabre is UKSkySabre / SkySabre.W3D, not SS2 BritainSkySabre / Spec_SamIriCnfg.
- Giraffe is UKGiraffe / SKYSRBR.
- C-RAM is UKPhlanx / SDUKPX, not AmericaVehicleCRAM / SDCRAM.
- Cougar MRAP is UKCougar from the Laser Crusader slot.
- Challenger is UKChallenger3 / UKCHNGR3, not SS2 BritainTankChallenger2 / LSFChallenger2.
- Tracked Rapier is UK49KB23 / 49KB23.
- Alvis Stormer is UKStormer from the Laser Avenger slot.
- FV432S is UKFV432S / FV432 + FV432w.

SHA-256 CommandSet.ini               {sha256(out_ini / 'CommandSet.ini')}
SHA-256 CommandButton.ini            {sha256(out_ini / 'CommandButton.ini')}
SHA-256 MappedImage                  {sha256(out_ini / MAP_REL)}
{obj_sha}
{art_sha}
SHA-256 ZIP                          {digest}
ZIP {zip_path} {zip_path.stat().st_size} members={len(zip_names)}
Copy {ZIP_ROOT}
26-country tunnel loaders preserved. America, China, Iran, France CC unchanged. No BIG.
Vehicles have no Shadow line. In-game test was not run.
"""
    (OUT_DIR / "BUILD_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SPECTER_SS2_ENGLAND_V25_CC8.zip.sha256").write_text(
        digest + "  SPECTER_SS2_ENGLAND_V25_CC8.zip\n", encoding="ascii"
    )
    print(report)
    print("ZIP members:")
    with zipfile.ZipFile(zip_path) as zf:
        for n in zf.namelist():
            print(" ", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
