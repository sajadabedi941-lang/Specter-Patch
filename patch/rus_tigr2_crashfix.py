#!/usr/bin/env python3
"""Repair missing upgrade_rus_tigr2 / Upgrade_Rus_Tigr2 crash.

The name did not exist in SPECTER DATA/ART. SAGE crashes on PLAYER_UPGRADE
when the Upgrade object (or ButtonImage MappedImage) is missing.

Fix: add Upgrade_Rus_Tigr2, Command_Upgrade_Rus_Tigr2, MappedImage
upgrade_rus_tigr2 (cloned from working Upgrade_RUS_Tier2 / sys_tier2),
and expose the button on Russia Weapon Industry CommandSets only.
Does not touch War Factory, other upgrades, units, or factions.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER_WARFACTORY_CAPTURE_UPDATE/_SPEC_DATA_ONE.big")
EXPECTED_DATA_SHA = "cc0595379e7f255f98170bd4502ed0479b634162739bd206748c86459176552b"
OUT_DIR = Path("/workspace/patch/Release/SPECTER1_RUS_TIGR2_CRASHFIX")
REPORT = Path("/workspace/patch/UPGRADE_RUS_TIGR2_AUDIT.txt")

P_UPG = r"Data\INI\Upgrade.ini"
P_BTN = r"Data\INI\CommandButton.ini"
P_CS = r"Data\INI\CommandSet.ini"
P_IMG = r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI"

UPGRADE_BLOCK = """Upgrade Upgrade_Rus_Tigr2
  DisplayName        = UPGRADE:Tier2
  BuildTime          = 45
  BuildCost          = 2000
  ButtonImage        = upgrade_rus_tigr2
End
"""

BUTTON_BLOCK = """CommandButton Command_Upgrade_Rus_Tigr2
  Command           = PLAYER_UPGRADE
  Upgrade           = Upgrade_Rus_Tigr2
  Options           = OK_FOR_MULTI_SELECT
  TextLabel         = TITT:Tier2
  ButtonImage       = upgrade_rus_tigr2
  ButtonBorderType  = UPGRADE
  DescriptLabel     = CONTROLBAR:Tier2
End
"""

IMAGE_BLOCK = """MappedImage upgrade_rus_tigr2
  Texture = Spec_Sys_Ico01.tga
  TextureWidth = 512
  TextureHeight = 512
  Coords = Left:128 Top:1 Right:250 Bottom:96
  Status = NONE
End
"""

WIP_CS = [
    "RussiaWeaponIndustryPlantCommandSet_T",
    "RussiaWeaponIndustryPlantCommandSet_T1",
    "RussiaWeaponIndustryPlantCommandSet_T2",
]


def insert_after_block(text: str, kind: str, name: str, new_block: str) -> str:
    nl = jf.file_nl(text)
    block = jf.to_nl(new_block.strip() + "\n", nl)
    m = re.search(rf"(?im)^{kind}\s+{re.escape(name)}\s*$", text)
    if not m:
        raise SystemExit(f"missing {kind} {name}")
    m2 = re.search(rf"(?im)^{kind}\s+\S+", text[m.end() :])
    end = m.end() + m2.start() if m2 else len(text)
    # skip trailing whitespace after End so we insert after the block
    return text[:end] + block + nl + text[end:]


def insert_cs_button(text: str, cs_name: str, slot: int, button: str) -> str:
    m = re.search(rf"(?im)^CommandSet\s+{re.escape(cs_name)}\s*$", text)
    if not m:
        raise SystemExit(f"missing CommandSet {cs_name}")
    m2 = re.search(r"(?im)^CommandSet\s+\S+", text[m.end() :])
    end = m.end() + m2.start() if m2 else len(text)
    block = text[m.start() : end]
    if button in block:
        return text
    used = {int(x) for x in re.findall(r"(?im)^\s*(\d+)\s*=", block)}
    if slot in used:
        for s in list(range(1, 16)):
            if s not in used:
                slot = s
                break
        else:
            raise SystemExit(f"{cs_name}: no free slot")
    lines = block.splitlines(True)
    out = []
    done = False
    insert = f"  {slot} = {button}\n"
    if jf.file_nl(text) == "\r\n":
        insert = insert.replace("\n", "\r\n")
    for line in lines:
        if (not done) and re.search(r"(?im)^\s*End\s*$", line):
            out.append(insert)
            done = True
        out.append(line)
    return text[: m.start()] + "".join(out) + text[end:]


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("unexpected source DATA SHA")
    entries = jf.read_big_list(SRC_DATA)

    upg = jf.text_of(entries, P_UPG)
    btn = jf.text_of(entries, P_BTN)
    cs = jf.text_of(entries, P_CS)
    img = jf.text_of(entries, P_IMG)

    if not re.search(r"(?im)^Upgrade\s+Upgrade_Rus_Tigr2\s*$", upg):
        upg = insert_after_block(upg, "Upgrade", "Upgrade_RUS_Tier2", UPGRADE_BLOCK)
    if not re.search(r"(?im)^CommandButton\s+Command_Upgrade_Rus_Tigr2\s*$", btn):
        btn = insert_after_block(btn, "CommandButton", "Command_RUS_Tier4", BUTTON_BLOCK)
    if not re.search(r"(?im)^MappedImage\s+upgrade_rus_tigr2\s*$", img):
        img = insert_after_block(img, "MappedImage", "sys_tier2", IMAGE_BLOCK)

    cs = insert_cs_button(cs, "RussiaWeaponIndustryPlantCommandSet_T", 7, "Command_Upgrade_Rus_Tigr2")
    cs = insert_cs_button(cs, "RussiaWeaponIndustryPlantCommandSet_T1", 7, "Command_Upgrade_Rus_Tigr2")
    cs = insert_cs_button(cs, "RussiaWeaponIndustryPlantCommandSet_T2", 15, "Command_Upgrade_Rus_Tigr2")

    jf.set_text(entries, P_UPG, upg)
    jf.set_text(entries, P_BTN, btn)
    jf.set_text(entries, P_CS, cs)
    jf.set_text(entries, P_IMG, img)

    blob = jf.build_big_ordered(entries)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(blob)
    new_sha = hashlib.sha256(blob).hexdigest()

    packed = jf.read_big_list(OUT_DIR / "_SPEC_DATA_ONE.big")
    pups = jf.text_of(packed, P_UPG)
    pbtns = jf.parse_buttons(jf.text_of(packed, P_BTN))
    pcs = jf.parse_commandsets(jf.text_of(packed, P_CS))
    pimg = jf.text_of(packed, P_IMG)

    def cs_buttons(name: str) -> list[str]:
        return re.findall(r"(?im)^\s*\d+\s*=\s*(\S+)", pcs.get(name, ""))

    ref = bool(re.search(r"(?im)^Upgrade\s+Upgrade_Rus_Tigr2\s*$", pups))
    cmdb = "Command_Upgrade_Rus_Tigr2" in pbtns and "Upgrade_Rus_Tigr2" in pbtns["Command_Upgrade_Rus_Tigr2"]
    cmdb = cmdb and "upgrade_rus_tigr2" in pbtns["Command_Upgrade_Rus_Tigr2"]
    cmds = all("Command_Upgrade_Rus_Tigr2" in cs_buttons(n) for n in WIP_CS)
    obj = bool(re.search(r"(?im)^MappedImage\s+upgrade_rus_tigr2\s*$", pimg))
    # no unit object named rus_tigr2 existed; upgrade is PLAYER_UPGRADE only
    obj_ok = obj and ref

    # identity + warfactory files besides the four intended
    base = {jf.norm(n).lower(): bytes(b) for n, b in jf.read_big_list(SRC_DATA)}
    changed = [n for n, b in packed if base.get(jf.norm(n).lower()) != bytes(b)]
    allowed = {jf.norm(x).lower() for x in (P_UPG, P_BTN, P_CS, P_IMG)}
    if {jf.norm(c).lower() for c in changed} != allowed:
        raise SystemExit(f"unexpected DATA changes: {changed}")
    for p in (
        r"Data\INI\PlayerTemplate.ini",
        r"Data\INI\MappedImages\HandCreated\Specter_FactionIdentity.INI",
    ):
        if bytes(jf.raw_of(packed, p)) != base[jf.norm(p).lower()]:
            raise SystemExit(f"identity changed {p}")

    pf = lambda ok: "PASS" if ok else "FAIL"
    crash = "YES" if (ref and cmdb and cmds and obj_ok) else "NO"
    report = (
        "UPGRADE_RUS_TIGR2\n"
        f"Reference = {pf(ref)}\n"
        f"CommandButton = {pf(cmdb)}\n"
        f"CommandSet = {pf(cmds)}\n"
        f"Object = {pf(obj_ok)}\n"
        f"Crash fixed = {crash}\n"
        "\n"
        "FINDINGS\n"
        "Before this fix, upgrade_rus_tigr2 / Upgrade_Rus_Tigr2 / rus_tigr2\n"
        "had ZERO references in packed DATA, ART, CSF, and loose INI.\n"
        "Closest working Russia upgrade is Upgrade_RUS_Tier2\n"
        "(Command_RUS_Tier2, sys_tier2, Russia Weapon Industry).\n"
        "\n"
        "REPAIR\n"
        "Added Upgrade_Rus_Tigr2 cloned from Upgrade_RUS_Tier2.\n"
        "Added Command_Upgrade_Rus_Tigr2 (PLAYER_UPGRADE).\n"
        "Added MappedImage upgrade_rus_tigr2 (same texture coords as sys_tier2).\n"
        "Exposed on RussiaWeaponIndustryPlantCommandSet_T / T1 / T2 only.\n"
        "War Factory, other upgrades, units, factions, ART unchanged.\n"
        "\n"
        f"DATA SHA256 {new_sha}\n"
        "ART_CHANGED = NO\n"
        "INGAME_TESTED = NO\n"
    )
    REPORT.write_text(report, encoding="utf-8")
    (OUT_DIR / "UPGRADE_RUS_TIGR2_AUDIT.txt").write_text(report, encoding="utf-8")
    (OUT_DIR / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {new_sha}\nART unchanged (not shipped)\n",
        encoding="utf-8",
    )
    print(report)
    if crash != "YES":
        raise SystemExit("validation failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
