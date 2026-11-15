#!/usr/bin/env python3
"""Six V25 America systems onto SPECTER SS2 America Command Center.

Merges six UNIT_BUILD buttons onto the PAC-3 MSE pack CommandSet.ini /
CommandButton.ini (loaders + Patriot slot 10 + MSE slot 11). Loose Data only.
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
MSE_INI = Path("patch/Release/SPECTER_SS2_USA_PAC3_MSE/Data/INI")
SRC_CS = MSE_INI / "CommandSet.ini"
SRC_CB = MSE_INI / "CommandButton.ini"
SRC_MAP = TOOL / "AmericaV25CC6_Images.ini"
OUT_DIR = Path("patch/Release/SPECTER_SS2_USA_V25_CC6")
CS_NAME = "AmericaCommandCenterCommandSet"
ART_SRC = TOOL / "art"
OBJ_DIR = "Object/Specter/United States Of America/AirDefense"
MAP_REL = "MappedImages/HandCreated/AmericaV25CC6_Images.ini"

SYSTEMS = [
    {
        "slot": 2,
        "btn": "Command_ConstructAmericaVehicleMeadsRadar",
        "obj": "AmericaVehicleMeadsRadar",
        "ini": "AmericaVehicleMeadsRadar.ini",
        "model": "usradar",
        "image": "USMDSRDTB",
        "w3d": "UsRadar.W3D",
        "need": [b"WHEEL01", b"WHEEL06", b"CORE"],
        "forbid": [b"WHEEL07", b"WHEEL08"],
        "draw": "W3DTruckDraw",
        "label": "MEADS Radar",
    },
    {
        "slot": 3,
        "btn": "Command_ConstructAmericaVehicleTPY2Radar",
        "obj": "AmericaVehicleTPY2Radar",
        "ini": "AmericaVehicleTPY2Radar.ini",
        "model": "USTPY2RD",
        "image": "USTPY2TB",
        "w3d": "USTPY2RD.W3D",
        "need": [b"WHEEL01", b"WHEEL10", b"CAB", b"TRAILER"],
        "forbid": [],
        "draw": "W3DTruckDraw",
        "label": "AN/TPY-2",
    },
    {
        "slot": 5,
        "btn": "Command_ConstructAmericaVehicleANTPQ53",
        "obj": "AmericaVehicleANTPQ53",
        "ini": "AmericaVehicleANTPQ53.ini",
        "model": "USTPQ53",
        "image": "ANTPQ53TB",
        "w3d": "USTPQ53.W3D",
        "need": [b"WHEEL01", b"WHEEL06"],
        "forbid": [],
        "draw": "W3DTruckDraw",
        "label": "AN/TPQ-53",
        "ini_forbid_bones": [r"Wheel0[78]"],
    },
    {
        "slot": 7,
        "btn": "Command_ConstructAmericaVehicleCRAM",
        "obj": "AmericaVehicleCRAM",
        "ini": "AmericaVehicleCRAM.ini",
        "model": "SDCRAM",
        "image": "CRAMTB",
        "w3d": "SDCRAM.W3D",
        "need": [b"TURRET", b"TURRETEL", b"MUZZLE01"],
        "forbid": [],
        "draw": "W3DModelDraw",
        "label": "C-RAM",
    },
    {
        "slot": 8,
        "btn": "Command_ConstructAmericaVehicleIFPC",
        "obj": "AmericaVehicleIFPC",
        "ini": "AmericaVehicleIFPC.ini",
        "model": "IFPC2",
        "image": "IFBCTB",
        "w3d": "IFPC2.W3D",
        "need": [b"WHEEL01", b"WHEEL06", b"PAOTA", b"PAOGUAN", b"WEAPONA01"],
        "forbid": [],
        "draw": "W3DTruckDraw",
        "label": "IFPC Increment 2-L",
    },
    {
        "slot": 9,
        "btn": "Command_ConstructAmericaVehicleRougeFire",
        "obj": "AmericaVehicleRougeFire",
        "ini": "AmericaVehicleRougeFire.ini",
        "model": "RougeFire",
        "image": "RougeFireTB",
        "w3d": "RougeFire.W3D",
        "need": [b"WHEEL01", b"WHEEL05", b"WHEEL08", b"WHEEL11", b"TURRET01", b"TURRETEL01", b"WEAPONM01"],
        "forbid": [],
        "draw": "W3DTruckDraw",
        "label": "Rogue Fires",
    },
]

ART_FILES = [
    ("W3D/UsRadar.W3D", "Art/W3D/UsRadar.W3D"),
    ("W3D/USTPY2RD.W3D", "Art/W3D/USTPY2RD.W3D"),
    ("W3D/USTPQ53.W3D", "Art/W3D/USTPQ53.W3D"),
    ("W3D/SDCRAM.W3D", "Art/W3D/SDCRAM.W3D"),
    ("W3D/IFPC2.W3D", "Art/W3D/IFPC2.W3D"),
    ("W3D/RougeFire.W3D", "Art/W3D/RougeFire.W3D"),
    ("Textures/USMDSRDTB.tga", "Art/Textures/USMDSRDTB.tga"),
    ("Textures/USTPY2TB.tga", "Art/Textures/USTPY2TB.tga"),
    ("Textures/ANTPQ53TB.tga", "Art/Textures/ANTPQ53TB.tga"),
    ("Textures/CRAMTB.tga", "Art/Textures/CRAMTB.tga"),
    ("Textures/IFBCTB.tga", "Art/Textures/IFBCTB.tga"),
    ("Textures/RougeFireTB.tga", "Art/Textures/RougeFireTB.tga"),
    ("Textures/SDAMRDWD.dds", "Art/Textures/SDAMRDWD.dds"),
    ("Textures/Tex_0006_01321.dds", "Art/Textures/Tex_0006_01321.dds"),
    ("Textures/USTPY2RD.dds", "Art/Textures/USTPY2RD.dds"),
    ("Textures/TPYRDHMT.dds", "Art/Textures/TPYRDHMT.dds"),
    ("Textures/T14A1CM.dds", "Art/Textures/T14A1CM.dds"),
    ("Textures/SDNSM04.dds", "Art/Textures/SDNSM04.dds"),
    ("Textures/USTPQ01.dds", "Art/Textures/USTPQ01.dds"),
    ("Textures/USTPQ02.dds", "Art/Textures/USTPQ02.dds"),
    ("Textures/USTPQ03.dds", "Art/Textures/USTPQ03.dds"),
    ("Textures/Glass1.tga", "Art/Textures/Glass1.tga"),
    ("Textures/RUA222W.dds", "Art/Textures/RUA222W.dds"),
    ("Textures/SDCRAMB.dds", "Art/Textures/SDCRAMB.dds"),
    ("Textures/SDCRAMC.dds", "Art/Textures/SDCRAMC.dds"),
    ("Textures/IFBCCM01.dds", "Art/Textures/IFBCCM01.dds"),
    ("Textures/IFBCCM02.dds", "Art/Textures/IFBCCM02.dds"),
    ("Textures/USRGFRL.dds", "Art/Textures/USRGFRL.dds"),
    ("Textures/USRGFRB.dds", "Art/Textures/USRGFRB.dds"),
]

KEEP_SLOTS = {
    1: "Command_ConstructAmericaDozer",
    4: "Command_ConstructAmericaVehicleDozerm",
    6: "Command_ConstructUSAPAC3",
    10: "Command_ConstructAmericaVehiclePatriotPAC3",
    11: "Command_ConstructAmericaVehiclePatriotPAC3MSE",
    12: "Command_ConstructAmericaVehicleUH60",
    13: "Command_ConstructAmericaVehicleM2A3BuskIIIMech",
    14: "Command_Sell",
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


def patch_slots(cs: str, set_name: str, additions: dict[int, str]) -> str:
    pattern = rf"(?ms)^(CommandSet {re.escape(set_name)}\s*\n)(.*?)(^End\s*$)"

    def repl(m: re.Match[str]) -> str:
        body = m.group(2)
        occupied = slots_of(body)
        extra = ""
        for slot, button in additions.items():
            if slot in occupied:
                raise SystemExit(f"{set_name} slot {slot} already occupied by {occupied[slot]}")
            extra += f"  {slot} = {button}\n"
        if not body.endswith("\n"):
            body += "\n"
        return m.group(1) + body + extra + m.group(3)

    new, n = re.subn(pattern, repl, cs, count=1)
    if n != 1:
        raise SystemExit(f"failed to patch {set_name}")
    return new


def unique_count(names: list[str], label: str) -> None:
    if len(names) != len(set(names)):
        dups = [n for n in set(names) if names.count(n) > 1]
        raise SystemExit(f"duplicate {label}: {dups}")


def verify_w3d(path: Path, need: list[bytes], forbid: list[bytes]) -> None:
    data = path.read_bytes().upper()
    missing = [n.decode() for n in need if n.upper() not in data]
    extra = [n.decode() for n in forbid if n.upper() in data]
    if missing:
        raise SystemExit(f"{path.name} missing bones {missing}")
    if extra:
        raise SystemExit(f"{path.name} has unexpected bones {extra}")


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
    if "Generic8x8Locomotor" not in block:
        raise SystemExit(f"{sys['obj']} missing Generic8x8Locomotor")
    if re.search(r"(?m)^\s*KindOf\s*=.*FS_BASE_DEFENSE", block):
        raise SystemExit(f"{sys['obj']} FS_BASE_DEFENSE not allowed")
    if re.search(r"(?m)^\s*Shadow\s*=", block):
        raise SystemExit(f"{sys['obj']} must not set Shadow")
    if "AttachToBoneInAnotherModule" in block:
        raise SystemExit(f"{sys['obj']} AttachToBoneInAnotherModule not allowed")
    if "CWCruHC_B" in block or "LSFIskanderl" in block:
        raise SystemExit(f"{sys['obj']} imported unnecessary V25 overlay")
    for pat in sys.get("ini_forbid_bones", []):
        if re.search(rf"(?m)^\s*\S+TireBone\s*=\s*{pat}\b", block):
            raise SystemExit(f"{sys['obj']} mapped forbidden bone {pat}")
    if sys["obj"] == "AmericaVehicleCRAM":
        if any(name in ("AmericaPhlanx", "AmericaPhalanx") for name in objs):
            raise SystemExit("C-RAM must not substitute Phalanx")
        weps = parse_blocks(text, "Weapon")
        if "AmericaCRAM_Gun" not in weps or "AmericaCRAM_AA" not in weps:
            raise SystemExit("C-RAM unique weapons missing")
        if re.search(r"(?m)^Weapon TGSK", text):
            raise SystemExit("V25 TGSKG must not be imported")
    if sys["obj"] == "AmericaVehicleIFPC":
        weps = parse_blocks(text, "Weapon")
        if "PENALTY" not in weps.get("AmericaIFPC_AA", ""):
            raise SystemExit("IFPC AA is not PENALTY")
        if "CRUSH" not in weps.get("AmericaIFPC_ABM", ""):
            raise SystemExit("IFPC ABM is not CRUSH")
        if re.search(r"(?m)^Weapon IFBC", text):
            raise SystemExit("V25 IFPC weapons must not be imported")
    if sys["obj"] == "AmericaVehicleRougeFire":
        weps = parse_blocks(text, "Weapon")
        if "AmericaRogueFires_NSM" not in weps:
            raise SystemExit("Rogue Fires unique weapon missing")
        if any(name.startswith("NSM") for name in weps):
            raise SystemExit("V25 NSM weapon must not be imported")
        if re.search(r"(?m)^\s*ProjectileObject\s*=\s*NSMMissile\b", text):
            raise SystemExit("V25 NSM projectile must not be imported")
    if sys["obj"] == "AmericaVehicleTPY2Radar":
        if "US_AN_TPY2" in block:
            raise SystemExit("must not reuse live SS2 US_AN_TPY2")


def main() -> int:
    if not SRC_CS.is_file() or not SRC_CB.is_file():
        raise SystemExit(f"MSE ControlBar missing: {SRC_CS} {SRC_CB}")

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    src_cs = SRC_CS.read_text("latin1").replace("\r\n", "\n")
    src_cb = SRC_CB.read_text("latin1").replace("\r\n", "\n")
    cs_blocks = parse_blocks(src_cs, "CommandSet")
    cb_blocks = parse_blocks(src_cb, "CommandButton")
    unique_count(list(cs_blocks), "source CommandSet.ini")
    unique_count(list(cb_blocks), "source CommandButton.ini")

    live = slots_of(cs_blocks[CS_NAME])
    for slot, btn in KEEP_SLOTS.items():
        if live.get(slot) != btn:
            raise SystemExit(f"America slot {slot} is {live.get(slot)}, expected {btn}")
    free = {2, 3, 5, 7, 8, 9}
    taken = set(live) & free
    if taken:
        raise SystemExit(f"expected-free slots occupied: {taken}")

    new_btns = [s["btn"] for s in SYSTEMS]
    unique_count(new_btns, "new buttons")
    for btn in new_btns:
        if btn in cb_blocks:
            raise SystemExit(f"button already exists {btn}")
        if btn == "Command_ConstructAmericaVehicleAN_TPY2":
            raise SystemExit("must not reuse live AN_TPY2 button")

    missing_loader_sets = []
    for fac in FACTIONS:
        if fac["cs"] not in cs_blocks:
            raise SystemExit(f"tunnel CommandSet missing {fac['cs']}")
        occupied = slots_of(cs_blocks[fac["cs"]])
        loader_btn = f"Command_Construct{fac['loader']}"
        tunnel_btn = f"Command_Construct{fac['tunnel']}"
        if occupied.get(fac["slot"]) != loader_btn:
            raise SystemExit(
                f"{fac['side']} {fac['cs']} slot {fac['slot']} is {occupied.get(fac['slot'])}, expected {loader_btn}"
            )
        if loader_btn not in cb_blocks or tunnel_btn not in cb_blocks:
            raise SystemExit(f"tunnel CommandButton missing {loader_btn}/{tunnel_btn}")
        loader_cs = f"{fac['loader']}CommandSet"
        if loader_cs not in cs_blocks:
            missing_loader_sets.append(loader_cs)
    if "SpecterSS2TunnelNetworkCommandSet" not in cs_blocks:
        missing_loader_sets.append("SpecterSS2TunnelNetworkCommandSet")
    if missing_loader_sets:
        raise SystemExit(f"tunnel unique CommandSets missing: {missing_loader_sets}")
    if len(FACTIONS) != 26:
        raise SystemExit(f"expected 26 factions, got {len(FACTIONS)}")

    for other in ("TurkeyCommandCenterCommandSet", "GLACommandCenterCommandSet", "Iran_MissileFactoryCommandSet"):
        if other not in cs_blocks:
            raise SystemExit(f"missing {other}")

    turkey_before = cs_blocks["TurkeyCommandCenterCommandSet"]
    gla_before = cs_blocks["GLACommandCenterCommandSet"]
    iran_factory_before = cs_blocks["Iran_MissileFactoryCommandSet"]
    iran_cc_before = cs_blocks["IranExpandedHQCommandSet"]
    patriot_btn_before = cb_blocks["Command_ConstructAmericaVehiclePatriotPAC3"]
    mse_btn_before = cb_blocks["Command_ConstructAmericaVehiclePatriotPAC3MSE"]
    live_tpy2_before = cb_blocks.get("Command_ConstructAmericaVehicleAN_TPY2", "")

    additions = {s["slot"]: s["btn"] for s in SYSTEMS}
    new_cs = patch_slots(src_cs, CS_NAME, additions)
    btn_text = "\n".join(btn_block(s) for s in SYSTEMS)
    new_cb = (
        src_cb.rstrip()
        + "\n\n; SPECTER SS2 America V25 Command Center systems.\n\n"
        + btn_text
    )

    new_cs_blocks = parse_blocks(new_cs, "CommandSet")
    new_cb_blocks = parse_blocks(new_cb, "CommandButton")
    unique_count(list(new_cs_blocks), "patched CommandSet.ini")
    unique_count(list(new_cb_blocks), "patched CommandButton.ini")
    if set(new_cs_blocks) != set(cs_blocks):
        raise SystemExit("CommandSet names were added or removed; refuse duplicate/redefine")
    if set(new_cb_blocks) - set(cb_blocks) != set(new_btns):
        raise SystemExit(f"unexpected CommandButton delta: {set(new_cb_blocks) - set(cb_blocks)}")

    won = slots_of(new_cs_blocks[CS_NAME])
    for s in SYSTEMS:
        if won[s["slot"]] != s["btn"]:
            raise SystemExit(f"slot {s['slot']} patch failed")
    for slot, btn in KEEP_SLOTS.items():
        if won[slot] != btn:
            raise SystemExit(f"kept slot {slot} lost")
    if new_cs_blocks["TurkeyCommandCenterCommandSet"] != turkey_before:
        raise SystemExit("Turkey CC changed")
    if new_cs_blocks["GLACommandCenterCommandSet"] != gla_before:
        raise SystemExit("GLA CC changed")
    if new_cs_blocks["Iran_MissileFactoryCommandSet"] != iran_factory_before:
        raise SystemExit("Iran factory changed")
    if new_cs_blocks["IranExpandedHQCommandSet"] != iran_cc_before:
        raise SystemExit("Iran CC changed")
    if button_core(new_cb_blocks["Command_ConstructAmericaVehiclePatriotPAC3"]) != button_core(patriot_btn_before):
        raise SystemExit("slot-10 Patriot button changed")
    if button_core(new_cb_blocks["Command_ConstructAmericaVehiclePatriotPAC3MSE"]) != button_core(mse_btn_before):
        raise SystemExit("slot-11 MSE button changed")
    if live_tpy2_before and button_core(new_cb_blocks["Command_ConstructAmericaVehicleAN_TPY2"]) != button_core(live_tpy2_before):
        raise SystemExit("live SS2 AN_TPY2 button changed")
    if "Command_ConstructAmericaVehicleTHAAD" in won.values():
        raise SystemExit("THAAD unexpectedly on America CC")

    for fac in FACTIONS:
        occupied = slots_of(new_cs_blocks[fac["cs"]])
        loader_btn = f"Command_Construct{fac['loader']}"
        if occupied.get(fac["slot"]) != loader_btn:
            raise SystemExit(f"loader wiped on {fac['side']}")
        if loader_btn not in new_cb_blocks:
            raise SystemExit(f"loader button wiped {loader_btn}")

    obj_texts: dict[str, str] = {}
    for s in SYSTEMS:
        src = TOOL / "objects" / s["ini"]
        text = src.read_text("latin1").replace("\r\n", "\n")
        if not text.endswith("\n"):
            text += "\n"
        check_object(s, text)
        if re.search(r"(?m)^Object US_THAAD", text) or re.search(r"(?m)^Object Iraq", text):
            raise SystemExit("THAAD / #672 objects must not be in this file")
        obj_texts[s["ini"]] = text
        w3d = ART_SRC / "W3D" / s["w3d"]
        verify_w3d(w3d, s["need"], s["forbid"])

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
    for s in SYSTEMS:
        rel = f"{OBJ_DIR}/{s['ini']}"
        (out_ini / rel).write_bytes(crlf(obj_texts[s["ini"]]))
        obj_rels.append("Data/INI/" + rel)

    zip_names = [dst for _, dst in ART_FILES]
    zip_names += [
        "Data/INI/CommandButton.ini",
        "Data/INI/CommandSet.ini",
        "Data/INI/" + MAP_REL,
        *obj_rels,
    ]
    zip_path = OUT_DIR / "SPECTER_SS2_USA_V25_CC6.zip"
    mapping = {name: OUT_DIR / name for name in zip_names}
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in zip_names:
            zf.write(mapping[name], name)
        if zf.namelist() != zip_names:
            raise SystemExit(zf.namelist())
        if any(n.lower().endswith(".big") for n in zf.namelist()):
            raise SystemExit("ZIP must not contain BIG files")
        if any(n.endswith(".txt") or n.endswith(".md") for n in zf.namelist()):
            raise SystemExit("ZIP must not contain reports")

    art_sha = "\n".join(f"SHA-256 {name:44} {sha256(path)}" for name, path in art_copied)
    obj_sha = "\n".join(f"SHA-256 {rel:44} {sha256(OUT_DIR / rel)}" for rel in obj_rels)
    slot_lines = "\n".join(
        f"  America CC slot {s['slot']:2} = {s['btn']} -> {s['obj']}  ({s['label']})"
        for s in SYSTEMS
    )
    report = f"""SS2 America V25 six-system Command Center pack (Loose Data, no BIG)
Merge base               PAC-3 MSE pack CS/CB (#795 Patriot + slot 11 MSE + 26 loaders)
V25 is art/object source only. Destination is SPECTER SS2 Loose Data/Art.

Per-system identity
1. MEADS Radar
   V25 Object/Button     AmericaMeadsRadar / Command_ConstructAmericaMeadsRadar
   V25 production        AmericaWarFactory2 / AmericafakeWarFactoryCommandSet slot 11
   SS2 Object/Button     AmericaVehicleMeadsRadar / Command_ConstructAmericaVehicleMeadsRadar
   Model                 usradar (UsRadar.W3D) wheels WHEEL01-06
   Not imported          UsRadarh AttachToBone, CWCruHC_B, KJ2000 lasers
2. AN/TPY-2
   V25 Object/Button     AmericaTPY2Radar / Command_ConstructAmericaTPY2Radar
   V25 production        AmericaWarFactory2 slot 13
   SS2 Object/Button     AmericaVehicleTPY2Radar / Command_ConstructAmericaVehicleTPY2Radar
   Model                 USTPY2RD CAB+TRAILER Wheel01-10
   Not reused            live SS2 US_AN_TPY2 / Command_ConstructAmericaVehicleAN_TPY2
3. AN/TPQ-53
   V25 Object/Button     AmericaANTPQ53 / Command_ConstructAmericaANTPQ53
   V25 production        AmericaWarFactory slot 13
   SS2 Object/Button     AmericaVehicleANTPQ53 / Command_ConstructAmericaVehicleANTPQ53
   Model                 USTPQ53 Wheel01-06 (Wheel07/08 absent from W3D, not mapped)
4. C-RAM
   V25 Object/Button     AmericaCRAM / Command_ConstructAmericaCRAM (DOZER_CONSTRUCT)
   V25 production        AmericaGAZ_66 slot 9 (not War Factory Phalanx)
   SS2 Object/Button     AmericaVehicleCRAM / Command_ConstructAmericaVehicleCRAM
   Model                 SDCRAM TURRET/TURRETEL/MUZZLE
   Not substituted       AmericaPhlanx
5. IFPC Increment 2-L
   V25 Object/Button     AmericaIFPC / Command_ConstructAmericaIFPC
   V25 production        AmericaWarFactory slot 10
   SS2 Object/Button     AmericaVehicleIFPC / Command_ConstructAmericaVehicleIFPC
   Model                 IFPC2 PaoTa/PAOGUAN WEAPONA01-15 WHEEL01-06
   Weapons               unique AmericaIFPC_AA (PENALTY) / AmericaIFPC_ABM (CRUSH)
6. Rogue Fires
   V25 Object/Button     AmericaRougeFire / Command_ConstructAmericaRougeFire
   V25 production        AmericaWarFactoryIII slot 8
   SS2 Object/Button     AmericaVehicleRougeFire / Command_ConstructAmericaVehicleRougeFire
   Model                 RougeFire TURRET01/TURRETEL01 WEAPONM WHEEL01/05/08/11
   Weapon                unique AmericaRogueFires_NSM (SS2 TomahawkMissile)

America Command Center slots after merge
{slot_lines}
  Kept: 1 Dozer, 4 Tunnel Loader, 6 USAPAC3, 10 Patriot PAC-3, 11 PAC-3 MSE,
        12 UH60, 13 M2A3, 14 Sell, 15-18 AI drones/helos.

SHA-256 CommandSet.ini               {sha256(out_ini / 'CommandSet.ini')}
SHA-256 CommandButton.ini            {sha256(out_ini / 'CommandButton.ini')}
SHA-256 MappedImage                  {sha256(out_ini / MAP_REL)}
{obj_sha}
{art_sha}
SHA-256 ZIP                          {sha256(zip_path)}
ZIP {zip_path} {zip_path.stat().st_size} members={len(zip_names)}
26-country tunnel loaders preserved. No duplicate CommandSet names. No BIG.
Vehicles have no Shadow line. In-game test was not run.
"""
    (OUT_DIR / "BUILD_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SPECTER_SS2_USA_V25_CC6.zip.sha256").write_text(
        sha256(zip_path) + "  SPECTER_SS2_USA_V25_CC6.zip\n", encoding="ascii"
    )
    print(report)
    print("ZIP members:")
    with zipfile.ZipFile(zip_path) as zf:
        for n in zf.namelist():
            print(" ", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
