#!/usr/bin/env python3
"""America MIM-104F Patriot PAC-3 as Loose Data files only (no BIG)."""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path("/tmp/ss2/SPECTER FINAL (GeneralsMode.com)")
SRC_CS = ROOT / "Data/INI/CommandSet.ini"
SRC_CB = ROOT / "Data/INI/CommandButton.ini"
SRC_OBJ = Path(__file__).resolve().parent / "AmericaVehiclePatriotPAC3.ini"
OUT_DIR = Path("patch/Release/SPECTER_SS2_USA_PATRIOT_PAC3")
BACKUP_DIR = OUT_DIR / "backup"
CS_NAME = "AmericaCommandCenterCommandSet"
SLOT = 10
BTN = "Command_ConstructAmericaVehiclePatriotPAC3"
OBJ = "AmericaVehiclePatriotPAC3"
OBJ_REL = "Object/Specter/United States Of America/AirDefense/AmericaVehiclePatriotPAC3.ini"

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


def main() -> int:
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
    if BTN in cb_blocks:
        raise SystemExit("button already exists")
    if "GLAVehicleRocketBuggyCommandSet" not in cs_blocks:
        raise SystemExit("missing GLAVehicleRocketBuggyCommandSet")
    live = slots_of(cs_blocks[CS_NAME])
    if live.get(1) != "Command_ConstructAmericaDozer":
        raise SystemExit(f"America slot 1 is {live.get(1)}")
    if live.get(6) != "Command_ConstructUSAPAC3":
        raise SystemExit("USAPAC3 slot 6 missing")
    if SLOT in live:
        raise SystemExit(f"slot {SLOT} occupied by {live[SLOT]}")
    for other in ("TurkeyCommandCenterCommandSet", "GLACommandCenterCommandSet", "Iran_MissileFactoryCommandSet"):
        if other not in cs_blocks:
            raise SystemExit(f"missing {other}")

    new_cs = patch_slot(src_cs, CS_NAME, SLOT, BTN)
    new_cb = src_cb.rstrip() + "\n\n; SPECTER SS2 America Patriot PAC-3 unique CommandButton.\n\n" + BTN_BLOCK

    new_cs_blocks = parse_blocks(new_cs, "CommandSet")
    new_cb_blocks = parse_blocks(new_cb, "CommandButton")
    won = slots_of(new_cs_blocks[CS_NAME])
    if won[SLOT] != BTN:
        raise SystemExit("slot patch failed")
    if won[1] != "Command_ConstructAmericaDozer":
        raise SystemExit("dozer lost")
    if won[6] != "Command_ConstructUSAPAC3":
        raise SystemExit("USAPAC3 lost")
    if new_cs_blocks["TurkeyCommandCenterCommandSet"] != cs_blocks["TurkeyCommandCenterCommandSet"]:
        raise SystemExit("Turkey CC changed")
    if new_cs_blocks["GLACommandCenterCommandSet"] != cs_blocks["GLACommandCenterCommandSet"]:
        raise SystemExit("GLA CC changed")
    if new_cs_blocks["Iran_MissileFactoryCommandSet"] != cs_blocks["Iran_MissileFactoryCommandSet"]:
        raise SystemExit("Iran factory changed")
    if "Command_ConstructAmericaVehicleTHAAD" in won.values():
        raise SystemExit("THAAD unexpectedly on America CC")
    btn_obj = re.search(r"(?m)^\s*Object\s*=\s*(\S+)", new_cb_blocks[BTN]).group(1)
    if btn_obj != OBJ:
        raise SystemExit("button object mismatch")
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
    if "TIRE01" not in obj_blocks[OBJ] or "UsaPac3Car" not in obj_blocks[OBJ]:
        raise SystemExit("wheel bones/model missing")
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
backup CommandSet.ini     {sha256(bak / 'CommandSet.ini')}
backup CommandButton.ini  {sha256(bak / 'CommandButton.ini')}
SHA-256 CommandSet.ini    {sha256(out_ini / 'CommandSet.ini')}
SHA-256 CommandButton.ini {sha256(out_ini / 'CommandButton.ini')}
SHA-256 Object INI        {sha256(out_ini / OBJ_REL)}
SHA-256 ZIP               {sha256(zip_path)}
ZIP {zip_path} {zip_path.stat().st_size} members={len(zip_names)}
America CC slot {SLOT} = {BTN} -> {OBJ}
Draw=W3DTruckDraw UsaPac3Car TIRE01-08, Generic8x8Locomotor, no TracksDraw, no deploy.
AA=THAAD PENALTY clone. ABM=THAAD CRUSH+fuze clone.
No BIG files. US_THAAD/Turkey/GLA/Iran factory unchanged.
In-game test was not run. Crash fix is not in-game verified.
"""
    (OUT_DIR / "BUILD_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SPECTER_SS2_USA_PATRIOT_PAC3.zip.sha256").write_text(
        f"{sha256(zip_path)}  SPECTER_SS2_USA_PATRIOT_PAC3.zip\n", encoding="ascii"
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
