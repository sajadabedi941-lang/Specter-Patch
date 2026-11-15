#!/usr/bin/env python3
"""America MIM-104F Patriot PAC-3 as Loose Data files only (no BIG).

Merges the Patriot America CC slot onto the healthy tunnel-loader
CommandSet.ini / CommandButton.ini. Does not snapshot live ControlBar files
that lack the 26-country loaders (that is what wiped them in earlier packs).
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

TUNNEL_INI = Path("patch/Release/SPECTER_SS2_TUNNEL_LOADER_DATA_FOLDER/Data/INI")
SRC_CS = TUNNEL_INI / "CommandSet.ini"
SRC_CB = TUNNEL_INI / "CommandButton.ini"
SRC_OBJ = Path(__file__).resolve().parent / "AmericaVehiclePatriotPAC3.ini"
OUT_DIR = Path("patch/Release/SPECTER_SS2_USA_PATRIOT_PAC3")
BACKUP_DIR = OUT_DIR / "backup"
CS_NAME = "AmericaCommandCenterCommandSet"
SLOT = 10
BTN = "Command_ConstructAmericaVehiclePatriotPAC3"
OBJ = "AmericaVehiclePatriotPAC3"
OBJ_REL = "Object/Specter/United States Of America/AirDefense/AmericaVehiclePatriotPAC3.ini"
V25_MODEL = "USPAC3"
V25_MISSING = [
    "USPAC3.W3D",
    "USPAC3.w3d",
    "Art/W3D/USPAC3.W3D",
    "Data/Art/W3D/USPAC3.W3D",
    "AmPatriotVeh.tga",
    "Art/Textures/AmPatriotVeh.tga",
    "Data/Art/Textures/AmPatriotVeh.tga",
]

BTN_BLOCK = """
CommandButton Command_ConstructAmericaVehiclePatriotPAC3
  Command            = UNIT_BUILD
  Object             = AmericaVehiclePatriotPAC3
  TextLabel          = CONTROLBAR:ConstructAmerica_MIM104F
  ButtonImage        = us_mim104e
  ButtonBorderType   = BUILD
  DescriptLabel      = CONTROLBAR:ToolTipUSAAmerica_MIM104F
End
""".strip() + "\n"


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


def patch_slot(cs: str, set_name: str, slot: int, button: str) -> str:
    pattern = rf"(?ms)^(CommandSet {re.escape(set_name)}\s*\n)(.*?)(^End\s*$)"

    def repl(m: re.Match[str]) -> str:
        body = m.group(2)
        if re.search(rf"(?m)^\s*{slot}\s*=", body):
            raise SystemExit(f"{set_name} slot {slot} already occupied")
        if not body.endswith("\n"):
            body += "\n"
        body += f"  {slot} = {button}\n"
        return m.group(1) + body + m.group(3)

    new, n = re.subn(pattern, repl, cs, count=1)
    if n != 1:
        raise SystemExit(f"failed to patch {set_name}")
    return new


def unique_count(names: list[str], label: str) -> None:
    if len(names) != len(set(names)):
        dups = [n for n in set(names) if names.count(n) > 1]
        raise SystemExit(f"duplicate {label}: {dups}")


def v25_art_present() -> list[str]:
    found: list[str] = []
    needles = {"uspac3.w3d", "ampatriotveh.tga"}
    candidates = [
        Path("/tmp/v25/Generals Silent Death V25/Art/W3D/USPAC3.W3D"),
        Path("/tmp/v25/Generals Silent Death V25/Data/Art/W3D/USPAC3.W3D"),
        Path("/tmp/ss2/SPECTER FINAL (GeneralsMode.com)/Art/W3D/USPAC3.W3D"),
        Path("/tmp/ss2/SPECTER FINAL (GeneralsMode.com)/Data/Art/W3D/USPAC3.W3D"),
        Path("patch/Art/W3D/USPAC3.W3D"),
        Path("/tmp/v25/Generals Silent Death V25/Art/Textures/AmPatriotVeh.tga"),
        Path("/tmp/ss2/SPECTER FINAL (GeneralsMode.com)/Art/Textures/AmPatriotVeh.tga"),
        Path("patch/Art/Textures/AmPatriotVeh.tga"),
    ]
    for p in candidates:
        if p.is_file() and p.name.lower() in needles:
            found.append(str(p))
    return found


def main() -> int:
    if not SRC_CS.is_file() or not SRC_CB.is_file():
        raise SystemExit(f"healthy tunnel-loader ControlBar missing: {SRC_CS} {SRC_CB}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bak = BACKUP_DIR / "Data" / "INI"
    bak.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC_CS, bak / "CommandSet.ini")
    shutil.copy2(SRC_CB, bak / "CommandButton.ini")

    src_cs = SRC_CS.read_text("latin1").replace("\r\n", "\n")
    src_cb = SRC_CB.read_text("latin1").replace("\r\n", "\n")
    obj_text = SRC_OBJ.read_text("latin1").replace("\r\n", "\n")
    cs_blocks = parse_blocks(src_cs, "CommandSet")
    cb_blocks = parse_blocks(src_cb, "CommandButton")
    unique_count(list(cs_blocks), "source CommandSet.ini")
    unique_count(list(cb_blocks), "source CommandButton.ini")
    if BTN in cb_blocks:
        raise SystemExit("button already exists")
    if "GLAVehicleRocketBuggyCommandSet" not in cs_blocks:
        raise SystemExit("missing GLAVehicleRocketBuggyCommandSet")
    live = slots_of(cs_blocks[CS_NAME])
    if live.get(1) != "Command_ConstructAmericaDozer":
        raise SystemExit(f"America slot 1 is {live.get(1)}")
    if live.get(6) != "Command_ConstructUSAPAC3":
        raise SystemExit("USAPAC3 slot 6 missing")
    if live.get(4) != "Command_ConstructAmericaVehicleDozerm":
        raise SystemExit("tunnel source missing America loader slot 4")
    if SLOT in live:
        raise SystemExit(f"slot {SLOT} occupied by {live[SLOT]}")

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

    new_cs = patch_slot(src_cs, CS_NAME, SLOT, BTN)
    new_cb = src_cb.rstrip() + "\n\n; SPECTER SS2 America Patriot PAC-3 unique CommandButton.\n\n" + BTN_BLOCK

    new_cs_blocks = parse_blocks(new_cs, "CommandSet")
    new_cb_blocks = parse_blocks(new_cb, "CommandButton")
    unique_count(list(new_cs_blocks), "patched CommandSet.ini")
    unique_count(list(new_cb_blocks), "patched CommandButton.ini")
    if set(new_cs_blocks) != set(cs_blocks):
        raise SystemExit("CommandSet names were added or removed; refuse duplicate/redefine")
    if set(new_cb_blocks) - set(cb_blocks) != {BTN}:
        raise SystemExit(f"unexpected CommandButton delta: {set(new_cb_blocks) - set(cb_blocks)}")

    won = slots_of(new_cs_blocks[CS_NAME])
    if won[SLOT] != BTN:
        raise SystemExit("slot patch failed")
    if won[1] != "Command_ConstructAmericaDozer":
        raise SystemExit("dozer lost")
    if won[6] != "Command_ConstructUSAPAC3":
        raise SystemExit("USAPAC3 lost")
    if won[4] != "Command_ConstructAmericaVehicleDozerm":
        raise SystemExit("America tunnel loader lost")
    if new_cs_blocks["TurkeyCommandCenterCommandSet"] != turkey_before:
        raise SystemExit("Turkey CC changed")
    if new_cs_blocks["GLACommandCenterCommandSet"] != gla_before:
        raise SystemExit("GLA CC changed")
    if new_cs_blocks["Iran_MissileFactoryCommandSet"] != iran_factory_before:
        raise SystemExit("Iran factory changed")
    if new_cs_blocks["IranExpandedHQCommandSet"] != iran_cc_before:
        raise SystemExit("Iran CC changed after America slot patch")
    if "Command_ConstructAmericaVehicleTHAAD" in won.values():
        raise SystemExit("THAAD unexpectedly on America CC")
    btn_obj = re.search(r"(?m)^\s*Object\s*=\s*(\S+)", new_cb_blocks[BTN]).group(1)
    if btn_obj != OBJ:
        raise SystemExit("button object mismatch")

    loader_lines = []
    for fac in FACTIONS:
        occupied = slots_of(new_cs_blocks[fac["cs"]])
        loader_btn = f"Command_Construct{fac['loader']}"
        if occupied.get(fac["slot"]) != loader_btn:
            raise SystemExit(f"loader wiped on {fac['side']}")
        if loader_btn not in new_cb_blocks:
            raise SystemExit(f"loader button wiped {loader_btn}")
        loader_lines.append(
            f"{fac['side']:22} {fac['cs']} slot {fac['slot']} = {loader_btn}"
        )

    obj_blocks = parse_blocks(obj_text, "Object")
    wep_blocks = parse_blocks(obj_text, "Weapon")
    for name in (OBJ, "AmericaPatriotPAC3_AA_Object", "AmericaPatriotPAC3_ABM_Object"):
        if name not in obj_blocks:
            raise SystemExit(f"missing object {name}")
    for name in ("AmericaPatriotPAC3_AA", "AmericaPatriotPAC3_ABM", "AmericaPatriotPAC3_ABM_Fuze"):
        if name not in wep_blocks:
            raise SystemExit(f"missing weapon {name}")
    if "PENALTY" not in wep_blocks["AmericaPatriotPAC3_AA"] or "AntiAirborneVehicle" not in wep_blocks["AmericaPatriotPAC3_AA"]:
        raise SystemExit("AA is not THAAD-style PENALTY")
    if "CRUSH" not in wep_blocks["AmericaPatriotPAC3_ABM"] or "AntiBallisticMissile" not in wep_blocks["AmericaPatriotPAC3_ABM"]:
        raise SystemExit("ABM is not THAAD-style CRUSH")
    if "AntiSmallMissile" not in wep_blocks["AmericaPatriotPAC3_ABM"]:
        raise SystemExit("ABM missing AntiSmallMissile")
    if "Weapon = AmericaPatriotPAC3_ABM_Fuze" not in obj_blocks["AmericaPatriotPAC3_ABM_Object"]:
        raise SystemExit("ABM projectile missing CRUSH fuze")
    if not re.search(r"(?m)^\s*Draw\s*=\s*W3DTruckDraw", obj_blocks[OBJ]):
        raise SystemExit("vehicle must use W3DTruckDraw")
    if "DeployStyleAIUpdate" in obj_blocks[OBJ] or re.search(r"(?m)^\s*ConditionState\s*=\s*DEPLOYED", obj_blocks[OBJ]):
        raise SystemExit("deploy states not allowed")
    if "Generic8x8Locomotor" not in obj_blocks[OBJ]:
        raise SystemExit("missing wheeled locomotor")
    if re.search(r"(?m)^\s*AttachToBoneInAnotherModule\s*=", obj_blocks[OBJ]):
        raise SystemExit("TracksDraw/AttachToBone is not valid with Generic8x8Locomotor")
    if re.search(r"(?m)^\s*(LeftFrontTireBone|RightFrontTireBone)\s*=\s*TIRE09", obj_blocks[OBJ]):
        raise SystemExit("second 2-bone wheel draw is not valid with Generic8x8Locomotor")
    if re.search(r"(?m)^\s*Model\s*=\s*UsaPac3Car_w\b", obj_blocks[OBJ]):
        raise SystemExit("second 2-bone wheel draw is not valid with Generic8x8Locomotor")
    if re.search(r"(?m)^\s*KindOf\s*=.*FS_BASE_DEFENSE", obj_blocks[OBJ]):
        raise SystemExit("FS_BASE_DEFENSE not allowed")
    if "CommandSet         = GLAVehicleRocketBuggyCommandSet" not in obj_blocks[OBJ]:
        raise SystemExit("unit CommandSet must reuse live GLAVehicleRocketBuggyCommandSet")
    if re.search(r"(?m)^Object US_THAAD", obj_text):
        raise SystemExit("THAAD object redefined")
    if re.search(r"(?m)^Object Iraq", obj_text):
        raise SystemExit("Iraq / #672 objects must not be in this file")

    art = v25_art_present()
    appearance_note = (
        "V25 appearance NOT applied. Real Patriot PAC-3 art is missing; "
        "UsaPac3Car was not substituted in this rebuild. Object Draw is unchanged."
        if not art
        else f"V25 art found: {art}"
    )
    if art:
        raise SystemExit(f"V25 art unexpectedly present; wire USPAC3 instead of leaving Object unchanged: {art}")
    if re.search(rf"(?m)^\s*Model\s*=\s*{V25_MODEL}\b", obj_blocks[OBJ]):
        raise SystemExit("Object claims USPAC3 but V25 W3D is not on disk")

    out_ini = OUT_DIR / "Data" / "INI"
    (out_ini / Path(OBJ_REL).parent).mkdir(parents=True, exist_ok=True)
    (out_ini / "CommandSet.ini").write_bytes(crlf(new_cs))
    (out_ini / "CommandButton.ini").write_bytes(crlf(new_cb))
    (out_ini / OBJ_REL).write_bytes(crlf(obj_text if obj_text.endswith("\n") else obj_text + "\n"))

    zip_names = [
        "Data/INI/CommandButton.ini",
        "Data/INI/CommandSet.ini",
        "Data/INI/" + OBJ_REL,
    ]
    zip_path = OUT_DIR / "SPECTER_SS2_USA_PATRIOT_PAC3.zip"
    mapping = {
        zip_names[0]: out_ini / "CommandButton.ini",
        zip_names[1]: out_ini / "CommandSet.ini",
        zip_names[2]: out_ini / OBJ_REL,
    }
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in zip_names:
            zf.write(mapping[name], name)
        if zf.namelist() != zip_names:
            raise SystemExit(zf.namelist())

    report = f"""SS2 America MIM-104F Patriot PAC-3 (Loose Data, no BIG)
Source ControlBar        healthy tunnel-loader pack (PR #786)
backup CommandSet.ini     {sha256(bak / 'CommandSet.ini')}
backup CommandButton.ini  {sha256(bak / 'CommandButton.ini')}
SHA-256 CommandSet.ini    {sha256(out_ini / 'CommandSet.ini')}
SHA-256 CommandButton.ini {sha256(out_ini / 'CommandButton.ini')}
SHA-256 Object INI        {sha256(out_ini / OBJ_REL)}
SHA-256 ZIP               {sha256(zip_path)}
ZIP {zip_path} {zip_path.stat().st_size} members={len(zip_names)}
America CC slot {SLOT} = {BTN} -> {OBJ}
America CC slot 4 loader kept. Slot 1 Dozer and slot 6 USAPAC3 kept.
26-country tunnel loaders preserved. No duplicate CommandSet names.
#672 Iraq radar not touched. US_THAAD/Turkey/GLA/Iran factory unchanged.
{appearance_note}
Missing V25 art files:
{chr(10).join('  - ' + n for n in V25_MISSING)}
  plus any textures named inside USPAC3.W3D (cannot be listed without the W3D).
In-game test was not run. Do not treat this as in-game verified.
"""
    (OUT_DIR / "BUILD_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "LOADER_MERGE_REPORT.txt").write_text(
        "Tunnel loaders after Patriot merge\n"
        + "\n".join(loader_lines)
        + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / "MISSING_V25_ART.txt").write_text(
        "V25 Patriot PAC-3 art is not on this machine.\n"
        "V25 install tree is Data/INI only (no Art, no W3D BIG).\n"
        "SS2 _SPEC_ART_ONE.big / _SPEC_ART_TWO.big / W3DZH.big have 0 USPAC3 members.\n"
        "Required files that were searched and not found:\n"
        + "\n".join(V25_MISSING)
        + "\nV25 INI reference (Data/INI/object/AmericaVehicle.ini Object AmericaPATRIO):\n"
        "  Model = USPAC3\n"
        "  bones: TURRET01, TURRETEL, WeaponA, CAB, TRAILER, Wheel01-08\n"
        "  SelectPortrait/ButtonImage = AmPatriotVeh -> AmPatriotVeh.tga\n"
        "  TrackMarks = EXTireTrack.tga (this TGA exists in SS2; the W3D does not)\n"
        "Object Draw was not rewritten to USPAC3 and was not replaced with another stand-in.\n",
        encoding="utf-8",
    )
    (OUT_DIR / "SPECTER_SS2_USA_PATRIOT_PAC3.zip.sha256").write_text(
        f"{sha256(zip_path)}  SPECTER_SS2_USA_PATRIOT_PAC3.zip\n", encoding="ascii"
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
