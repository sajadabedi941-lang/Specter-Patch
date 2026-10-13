#!/usr/bin/env python3
"""Replace Israel's remaining Clear Mines construction slot with the missile factory.

Baseline packed archives: SPECTER_GLOBAL_STORE_FIVE (PR #670).

Packed last-wins audit:
  FactionIsrael StartingUnit0=Israel_VehicleDozer uses IsraelDozerCommandSet.
  IsraelDozerCommandSet slot 14 already constructs Israel_MissileFactory
  (Global Store occupies slot 2). That starting-dozer menu is frozen.
  The remaining Israel-side Clear Mines construction option is
  AirF_AmericaDozerCommandSet slot 14 = Command_DisarmMinesAtPosition.
  AirF_AmericaVehicleDozer last-wins Side=Israel and is produced by
  AirF_AmericaCommandCenter (Israel dozer slot 8).

This pack replaces only that AirF slot 14 with
Command_ConstructIsrael_MissileFactory. Factory object, A-J roster, Fire
chain, and artwork already exist from PR #652/#653 and are reused.

Other countries' Command_DisarmMinesAtPosition slots stay frozen.
ART_ONE / ART_TWO are copied byte-identical.
"""
from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_global_store_expand as gs  # noqa: E402
import pack_s_global_store_five as five  # noqa: E402
import pack_s_iraq_mic_radar_ad as rad  # noqa: E402
import pack_s_radar_uav_slots as uav  # noqa: E402
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_GLOBAL_STORE_FIVE/_SPEC_DATA_ONE.big"
SRC_ART1 = ROOT / "patch/Release/SPECTER_GLOBAL_STORE_FIVE/_SPEC_ART_ONE.big"
SRC_ART2 = ROOT / "patch/Release/SPECTER_GLOBAL_STORE_FIVE/_SPEC_ART_TWO.big"
OUT = ROOT / "patch/Release/SPECTER_ISRAEL_MF_CLEAR_MINES"
INSTALLER = ROOT / "patch/tools/installer"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "283d5b1bd0a60561e32cd58bb99274d2d126fd3fc1276d49ceca3046aa22237d"
SIZE_DATA_SRC = 373897679
SHA_ART1_SRC = "9dc4524ccb44881fcd0149957d2fcce1d378db1483e6c458df67e07c86a86aa8"
SIZE_ART1_SRC = 2144972013
SHA_ART2_SRC = "a5a20d959d2835f12a4bf5431e011c4d45047f24ea3d88841c2281fc0a6c19af"
SIZE_ART2_SRC = 307254782
SAGE_SAFE = 2147483648

CS_INI = five.CS_INI
CB_INI = five.CB_INI
CSF_KEY = five.CSF_KEY
PREV_CS = five.CS_ZZZZ
CS_ZZZZ = r"Data\INI\CommandSet_ZZZZ_ZzIsraelMissileFactory.ini"
IL_CS_KEY = r"Data\INI\CommandSet_IsraelMissiles.ini"
TARGET_CS = "AirF_AmericaDozerCommandSet"
START_CS = "IsraelDozerCommandSet"
OLD_CMD = "Command_DisarmMinesAtPosition"
NEW_CMD = "Command_ConstructIsrael_MissileFactory"
SLOT = "14"
FACTORY = "Israel_MissileFactory"
FACTORY_CS = "Israel_MissileFactoryCommandSet"

MISSILES = [
    ("A", "Israel_Popeye", "CB_ISRAEL_MISSILE_A"),
    ("B", "Israel_Delilah", "CB_ISRAEL_MISSILE_B"),
    ("C", "Israel_LORA", "CB_ISRAEL_MISSILE_C"),
    ("D", "Israel_EXTRA", "CB_ISRAEL_MISSILE_D"),
    ("E", "Israel_Rampage", "CB_ISRAEL_MISSILE_E"),
    ("F", "Israel_Rocks", "CB_ISRAEL_MISSILE_F"),
    ("G", "Israel_Shavit", "CB_ISRAEL_MISSILE_G"),
    ("H", "Israel_Jericho2", "CB_ISRAEL_MISSILE_H"),
    ("I", "Israel_Jericho3", "CB_ISRAEL_MISSILE_I"),
    ("J", "Israel_Keren", "CB_ISRAEL_MISSILE_J"),
]

PROTECTED_CS = (
    "Iraq_VT72BCommandSet",
    "Iraq_WorkerCommandSet",
    "EgyptDozerCommandSet",
    "GermanyDozerCommandSet",
    "Japan_VT72BCommandSet",
    "Lazr_AmericaDozerCommandSet",
    "SupW_AmericaDozerCommandSet",
    "Nuke_ChinaDozerCommandSet",
    "ChinaDozerCommandSet",
    "AmericaDozerCommandSet",
    "IranDozerCommandSet",
    "RussiaDozerCommandSet",
    "PLADozerCommandSet",
)


def last_from(order, files, kind, name):
    return sk.last_block_from_files(order, files, kind, name)


def field(block: str, key: str) -> str:
    return sk.field(block, key)


def slot_map(block: str) -> dict[str, str]:
    return rad.slot_map(block)


def sha256_path(path: Path) -> str:
    return rad.sha256_path(path)


def patch_airf_slot(block: str) -> str:
    sl = slot_map(block)
    current = sl.get(SLOT)
    if current not in (OLD_CMD, NEW_CMD):
        raise SystemExit(f"{TARGET_CS} slot {SLOT} is {current}")
    new, n = re.subn(
        rf"(?m)^(\s*{SLOT}\s*=\s*){re.escape(OLD_CMD)}\s*$",
        rf"\g<1>{NEW_CMD}",
        block.replace("\r\n", "\n"),
        count=1,
    )
    if n == 0 and sl.get(SLOT) == NEW_CMD:
        return block.replace("\r\n", "\n")
    if n != 1:
        raise SystemExit(f"failed to retarget {TARGET_CS} slot {SLOT}")
    return new


def overlay_text() -> str:
    return (LOOSE / "CommandSet_ZZZZ_ZzIsraelMissileFactory.ini").read_text(encoding="latin1")


CS_BLOCK_RE = re.compile(
    r"(?ms)^CommandSet (\S+)\s*\r?\n.*?(?=^CommandSet |\Z)"
)


def iter_cs_blocks(text: str):
    for m in CS_BLOCK_RE.finditer(text):
        yield m.group(1), m.group(0)


def all_last_cs(order, files) -> dict[str, tuple[str, str]]:
    last: dict[str, tuple[str, str]] = {}
    for key in order:
        blob = files[key]
        if b"CommandSet " not in blob:
            continue
        for name, blk in iter_cs_blocks(blob.decode("latin1")):
            last[name] = (key, blk)
    return last


def mines_snapshot(order, files) -> dict[str, dict[str, str]]:
    snap = {}
    for name, (_src, blk) in all_last_cs(order, files).items():
        sl = slot_map(blk)
        if OLD_CMD in sl.values():
            snap[name] = sl
    return snap


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_GLOBAL_STORE_FIVE")
    if sha256_path(SRC_ART1) != SHA_ART1_SRC or SRC_ART1.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE baseline mismatch")
    if sha256_path(SRC_ART2) != SHA_ART2_SRC or SRC_ART2.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO baseline mismatch")

    print("parsing DATA...")
    files, order = sk.parse_big_ordered(SRC_DATA.read_bytes())
    original = dict(files)
    orig_mines = mines_snapshot(order, original)

    src_airf, airf = last_from(order, files, "CommandSet", TARGET_CS)
    if slot_map(airf).get(SLOT) != OLD_CMD:
        raise SystemExit(f"baseline {TARGET_CS} slot {SLOT} is not Clear Mines")
    src_start, start_cs = last_from(order, files, "CommandSet", START_CS)
    start_slots = slot_map(start_cs)
    if start_slots.get(SLOT) != NEW_CMD:
        raise SystemExit("baseline IsraelDozerCommandSet slot 14 is not missile factory")
    if start_slots.get("2") != "Command_ConstructIsrael_GlobalStore":
        raise SystemExit("baseline IsraelDozerCommandSet lost Global Store")

    patched_cs_files = []
    for key in list(files):
        blob = files[key]
        if not key.lower().endswith(".ini"):
            continue
        if f"CommandSet {TARGET_CS}".encode("ascii") not in blob:
            continue
        text = blob.decode("latin1")
        blk = sk.last_block(text, "CommandSet", TARGET_CS)
        if not blk:
            continue
        text = sk.replace_last(text, "CommandSet", TARGET_CS, patch_airf_slot(blk))
        files[key] = sk.to_crlf(text)
        patched_cs_files.append(key)

    files[CS_ZZZZ] = sk.to_crlf(overlay_text())

    print("building DATA...")
    data_big = sk.build_big(files)
    packed, packed_order = sk.parse_big_ordered(data_big)
    fails: list[str] = []
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))

    live_cs = packed[CS_INI].decode("latin1")
    live_cb = packed[CB_INI].decode("latin1")
    zzzz_cs = packed[CS_ZZZZ].decode("latin1")

    live_airf = sk.last_block(live_cs, "CommandSet", TARGET_CS)
    packed_src, packed_airf = last_from(packed_order, packed, "CommandSet", TARGET_CS)
    zzzz_airf = sk.last_block(zzzz_cs, "CommandSet", TARGET_CS)
    orig_airf_slots = slot_map(airf)
    expect_airf = dict(orig_airf_slots)
    expect_airf[SLOT] = NEW_CMD
    for label, blk in (("LIVE", live_airf), ("PACKED", packed_airf), ("ZZZZ", zzzz_airf)):
        sl = slot_map(blk)
        if sl.get(SLOT) != NEW_CMD:
            fails.append(f"{label} {TARGET_CS} slot {SLOT}={sl.get(SLOT)}")
        if OLD_CMD in sl.values():
            fails.append(f"{label} {TARGET_CS} still has Clear Mines")
        mf_slots = [s for s, v in sl.items() if v == NEW_CMD]
        if mf_slots != [SLOT]:
            fails.append(f"{label} {TARGET_CS} MF slots {mf_slots}")
        if sl != expect_airf:
            fails.append(f"{label} {TARGET_CS} unexpected extra slot changes")
    if packed_src != CS_ZZZZ:
        fails.append(f"{TARGET_CS} last-wins {packed_src}")

    src_start2, packed_start = last_from(packed_order, packed, "CommandSet", START_CS)
    packed_start_slots = slot_map(packed_start)
    if packed_start_slots != start_slots:
        fails.append("IsraelDozerCommandSet mutated")
    if packed_start_slots.get(SLOT) != NEW_CMD:
        fails.append("Israel starting dozer lost missile factory")
    if packed_start_slots.get("2") != "Command_ConstructIsrael_GlobalStore":
        fails.append("Israel starting dozer lost Global Store")
    if src_start2 != src_start:
        fails.append(f"IsraelDozerCommandSet last-wins moved to {src_start2}")

    src_dozer, dozer = last_from(packed_order, packed, "Object", "Israel_VehicleDozer")
    if field(dozer, "CommandSet") != START_CS or field(dozer, "Side") != "Israel":
        fails.append("Israel_VehicleDozer CommandSet/Side")
    src_airf_obj, airf_obj = last_from(packed_order, packed, "Object", "AirF_AmericaVehicleDozer")
    if field(airf_obj, "CommandSet") != TARGET_CS:
        fails.append("AirF_AmericaVehicleDozer CommandSet retargeted")
    if field(airf_obj, "Side") != "Israel":
        fails.append("AirF_AmericaVehicleDozer Side changed")
    orig_airf_obj = last_from(order, original, "Object", "AirF_AmericaVehicleDozer")[1]
    if airf_obj != orig_airf_obj:
        fails.append("AirF_AmericaVehicleDozer object mutated")
    orig_isr_dozer = last_from(order, original, "Object", "Israel_VehicleDozer")[1]
    if dozer != orig_isr_dozer:
        fails.append("Israel_VehicleDozer object mutated")

    btn = sk.last_block(live_cb, "CommandButton", NEW_CMD)
    src_btn, packed_btn = last_from(packed_order, packed, "CommandButton", NEW_CMD)
    orig_btn = last_from(order, original, "CommandButton", NEW_CMD)[1]
    if packed_btn != orig_btn:
        fails.append("Command_ConstructIsrael_MissileFactory mutated")
    if field(btn, "Command") != "DOZER_CONSTRUCT":
        fails.append("construct Command")
    if field(btn, "Object") != FACTORY:
        fails.append("construct Object")
    if field(btn, "ButtonImage") != "Button_MissileFactory":
        fails.append("construct ButtonImage")
    if field(btn, "TextLabel") != "CONTROLBAR:ConstructIsraelMissileFactory":
        fails.append("construct TextLabel")
    if field(btn, "DescriptLabel") != "CONTROLBAR:ToolTipIsraelMissileFactory":
        fails.append("construct DescriptLabel")

    src_fac, fac = last_from(packed_order, packed, "Object", FACTORY)
    orig_fac = last_from(order, original, "Object", FACTORY)[1]
    if fac != orig_fac:
        fails.append("Israel_MissileFactory mutated")
    if field(fac, "Side") != "Israel":
        fails.append("factory Side")
    if field(fac, "CommandSet") != FACTORY_CS:
        fails.append("factory CommandSet")
    if field(fac, "SelectPortrait") != "irq_warfctry":
        fails.append("factory SelectPortrait")
    if field(fac, "ButtonImage") != "irq_warfctry":
        fails.append("factory object ButtonImage")
    if "Irq_FahdFac" not in fac:
        fails.append("factory model")

    src_fcs, fcs = last_from(packed_order, packed, "CommandSet", FACTORY_CS)
    orig_fcs = last_from(order, original, "CommandSet", FACTORY_CS)[1]
    if fcs != orig_fcs:
        fails.append("Israel_MissileFactoryCommandSet mutated")
    fslots = slot_map(fcs)
    for i, (_slot, obj, cb) in enumerate(MISSILES, start=1):
        if fslots.get(str(i)) != cb:
            fails.append(f"factory slot {i}={fslots.get(str(i))}")
        src_obj, oblk = last_from(packed_order, packed, "Object", obj)
        src_cb, cblk = last_from(packed_order, packed, "CommandButton", cb)
        if not oblk:
            fails.append(f"missing missile {obj}")
            continue
        if not cblk:
            fails.append(f"missing button {cb}")
            continue
        if field(oblk, "Side") != "Israel":
            fails.append(f"{obj} Side")
        if field(cblk, "Command") != "UNIT_BUILD" or field(cblk, "Object") != obj:
            fails.append(f"{cb} binding")
        weapon = field(oblk, "Weapon") if False else None
        weapons = re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", oblk)
        if not weapons:
            fails.append(f"{obj} has no PRIMARY weapon")
        else:
            wsrc, wblk = last_from(packed_order, packed, "Weapon", weapons[0])
            if not wblk:
                fails.append(f"missing weapon {weapons[0]}")
            else:
                proj = field(wblk, "ProjectileObject")
                if not proj:
                    fails.append(f"{weapons[0]} missing ProjectileObject")
                else:
                    psrc, pblk = last_from(packed_order, packed, "Object", proj)
                    if not pblk:
                        fails.append(f"missing projectile {proj}")
                warhead = weapons[0] + "_Warhead"
                whsrc, whblk = last_from(packed_order, packed, "Weapon", warhead)
                if not whblk:
                    fails.append(f"missing warhead {warhead}")
        tel_cs = field(oblk, "CommandSet")
        tsrc, tblk = last_from(packed_order, packed, "CommandSet", tel_cs)
        tel_slots = slot_map(tblk)
        if tel_slots.get("1") != "Command_FireMainWeapon":
            fails.append(f"{obj} Fire slot {tel_slots.get('1')}")
        fire_src, fire_blk = last_from(packed_order, packed, "CommandButton", "Command_FireMainWeapon")
        if field(fire_blk, "Command") != "FIRE_WEAPON":
            fails.append("Command_FireMainWeapon")

    csf = packed[CSF_KEY]
    orig_csf = original[CSF_KEY]
    if csf != orig_csf:
        fails.append("CSF mutated")
    if sk.csf_get(csf, "OBJECT:IsraelMissileFactory") != "Missile Factory":
        fails.append("CSF factory name")
    if sk.csf_get(csf, "CONTROLBAR:ConstructIsraelMissileFactory") != "Missile Factory":
        fails.append("CSF construct label")

    packed_mines = mines_snapshot(packed_order, packed)
    if TARGET_CS in packed_mines:
        fails.append("AirF still in Clear Mines snapshot")
    if TARGET_CS not in orig_mines:
        fails.append("baseline missed AirF Clear Mines")
    for name, sl in orig_mines.items():
        if name == TARGET_CS:
            continue
        if packed_mines.get(name) != sl:
            fails.append(f"other Clear Mines mutated {name}")
    extra = set(packed_mines) - (set(orig_mines) - {TARGET_CS})
    if extra:
        fails.append(f"unexpected remaining Clear Mines CS {sorted(extra)[:8]}")

    for name in PROTECTED_CS:
        orig_src, orig_blk = last_from(order, original, "CommandSet", name)
        new_src, new_blk = last_from(packed_order, packed, "CommandSet", name)
        if orig_blk != new_blk:
            fails.append(f"protected CS mutated {name}")

    for country in five.COUNTRIES:
        packed_cs = slot_map(last_from(packed_order, packed, "CommandSet", country["commandsets"][0])[1])
        orig_cs = slot_map(last_from(order, original, "CommandSet", country["commandsets"][0])[1])
        if packed_cs != orig_cs:
            fails.append(f"PR670 CS mutated {country['commandsets'][0]}")
        src_obj, obj = last_from(packed_order, packed, "Object", country["object"])
        orig_obj = last_from(order, original, "Object", country["object"])[1]
        if obj != orig_obj:
            fails.append(f"PR670 GS mutated {country['object']}")

    for c19 in gs.COUNTRIES:
        packed_cs = slot_map(last_from(packed_order, packed, "CommandSet", c19["commandsets"][0])[1])
        orig_cs = slot_map(last_from(order, original, "CommandSet", c19["commandsets"][0])[1])
        if packed_cs != orig_cs:
            fails.append(f"PR669 CS mutated {c19['commandsets'][0]}")

    orig_mic = last_from(order, original, "Object", "Iraq_MIC")[1]
    packed_mic = last_from(packed_order, packed, "Object", "Iraq_MIC")[1]
    if orig_mic != packed_mic:
        fails.append("Iraq_MIC mutated")

    expect_mic = {item["slot"]: item["cmd"] for item in rad.COPIES}
    expect_mic["15"] = rad.SELL
    for name in rad.MIC_CS_NAMES:
        packed_mic_cs = slot_map(last_from(packed_order, packed, "CommandSet", name)[1])
        orig_mic_cs = slot_map(last_from(order, original, "CommandSet", name)[1])
        if packed_mic_cs != expect_mic or orig_mic_cs != packed_mic_cs:
            fails.append(f"MIC menu mutated {name}")

    orig_t3 = slot_map(last_from(order, original, "CommandSet", rad.WF_CS_NAME)[1])
    packed_t3 = slot_map(last_from(packed_order, packed, "CommandSet", rad.WF_CS_NAME)[1])
    if orig_t3 != packed_t3:
        fails.append("WF T3 mutated")

    for country in uav.COUNTRIES:
        orig_slots = slot_map(last_from(order, original, "CommandSet", country["cs"])[1])
        packed_slots = slot_map(last_from(packed_order, packed, "CommandSet", country["cs"])[1])
        if orig_slots != packed_slots:
            fails.append(f"UAV CS mutated {country['cs']}")

    if CS_ZZZZ.lower() <= PREV_CS.lower():
        fails.append("CS overlay does not sort after PR670 overlay")

    allowed = {CS_ZZZZ, CS_INI, IL_CS_KEY}
    for key, blob in original.items():
        if key in allowed:
            continue
        if f"CommandSet {TARGET_CS}".encode("ascii") in blob:
            continue
        if packed.get(key) != blob:
            fails.append(f"unrelated DATA mutated {key}")

    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails[:80]) + f"\n({len(fails)} total)")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art1_path = OUT / "_SPEC_ART_ONE.big"
    art2_path = OUT / "_SPEC_ART_TWO.big"
    data_path.write_bytes(data_big)
    shutil.copy2(SRC_ART1, art1_path)
    shutil.copy2(SRC_ART2, art2_path)

    (LOOSE / "CommandSet_ZZZZ_ZzIsraelMissileFactory.ini").write_bytes(files[CS_ZZZZ])

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "CommandSet_ZZZZ_ZzIsraelMissileFactory.ini").write_bytes(files[CS_ZZZZ])
    (ext / "AirF_AmericaDozerCommandSet.ini").write_text(zzzz_airf + "\n", encoding="utf-8")
    (ext / "IsraelDozerCommandSet.ini").write_text(packed_start + "\n", encoding="utf-8")

    (OUT / "INSTALL.txt").write_text(
        "\n".join(
            [
                "SPECTER ISRAEL MISSILE FACTORY / CLEAR MINES — INSTALL",
                "",
                "Keep the split ART arrangement. Do not recombine ART.",
                "Place all three uncompressed BIGs next to generals.exe:",
                "  _SPEC_DATA_ONE.big",
                "  _SPEC_ART_ONE.big",
                "  _SPEC_ART_TWO.big",
                "",
                "Zero Hour auto-loads every *.big in that folder.",
                "Replace SPECTER_GLOBAL_STORE_FIVE DATA. ART is unchanged from PR #670.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "Israel AirF-cloned dozer slot 14 Clear Mines replaced by missile factory. "
        "ART unchanged from PR #670. RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    zip_path = OUT / "SPECTER_ISRAEL_MF_CLEAR_MINES.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "_SPEC_ART_TWO.big",
            "INSTALL.txt",
            "README.txt",
            "Launch_Specter.bat",
            "Install_SpecterPatch.bat",
        ):
            zf.write(OUT / name, name)

    if sha256_path(art1_path) != SHA_ART1_SRC or art1_path.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE copy is not byte-identical")
    if sha256_path(art2_path) != SHA_ART2_SRC or art2_path.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO copy is not byte-identical")
    if art1_path.stat().st_size >= SAGE_SAFE or art2_path.stat().st_size >= SAGE_SAFE:
        raise SystemExit("ART archive exceeds SAGE 2GiB signed offset limit")

    data_sha = sha256_path(data_path)
    art1_sha = sha256_path(art1_path)
    art2_sha = sha256_path(art2_path)
    zip_sha = sha256_path(zip_path)
    tag = "s-israel-mf-clear-mines"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/" + tag
    )
    report = "\n".join(
        [
            "STATIC VALIDATION: PASS",
            "RUNTIME_TEST=NOT RUN",
            "BASELINE: PR #670 SPECTER_GLOBAL_STORE_FIVE",
            "ISRAEL_STARTING_DOZER=Israel_VehicleDozer / IsraelDozerCommandSet",
            "ISRAEL_STARTING_DOZER_SLOT14=Command_ConstructIsrael_MissileFactory (unchanged)",
            "ISRAEL_STARTING_DOZER_SLOT2=Command_ConstructIsrael_GlobalStore (unchanged)",
            "CLEARED_MINES_CS=AirF_AmericaDozerCommandSet",
            "CLEARED_MINES_SLOT=14",
            "OLD_CMD=Command_DisarmMinesAtPosition",
            "NEW_CMD=Command_ConstructIsrael_MissileFactory",
            "FACTORY=Israel_MissileFactory",
            "FACTORY_CS=Israel_MissileFactoryCommandSet",
            "CONSTRUCT_BUTTON_IMAGE=Button_MissileFactory",
            "FACTORY_SELECT_PORTRAIT=irq_warfctry",
            "ROSTER=Israel A-J reused (Popeye..Keren)",
            "OTHER_COUNTRIES_CLEAR_MINES_UNCHANGED=YES",
            "PR670_GLOBAL_STORES_UNCHANGED=YES",
            "IRAQ_GLOBAL_STORE_UNCHANGED=YES",
            "ART_UNCHANGED=YES",
            "MIC_SLOTS_1_14_SELL_15=YES",
            "UAV_SLOTS_9_12_UNCHANGED=YES",
            "WF_T3_UNCHANGED=YES",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_ONE_SIZE={art1_path.stat().st_size}",
            f"ART_ONE_SHA256={art1_sha}",
            f"ART_TWO_SIZE={art2_path.stat().st_size}",
            f"ART_TWO_SHA256={art2_sha}",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "RUNTIME_TEST=NOT RUN",
            "",
            "patched CommandSet files:",
            *patched_cs_files,
            "",
        ]
    )
    (OUT / "VALIDATE_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "\n".join(
            [
                "DATA_CHANGED=YES",
                "ART_CHANGED=NO",
                f"DATA_SIZE={data_path.stat().st_size}",
                f"DATA_SHA256={data_sha}",
                f"ART_ONE_SIZE={art1_path.stat().st_size}",
                f"ART_ONE_SHA256={art1_sha}",
                f"ART_TWO_SIZE={art2_path.stat().st_size}",
                f"ART_TWO_SHA256={art2_sha}",
                "ZIP_FILE=SPECTER_ISRAEL_MF_CLEAR_MINES.zip",
                f"ZIP_SIZE={zip_path.stat().st_size}",
                f"ZIP_SHA256={zip_sha}",
                "BASELINE=PR #670",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA:",
                f"  {rel_base}/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART textures (unchanged; standalone asset on tag s-iraq-global-store-name):",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-global-store-name/_SPEC_ART_ONE.big",
                f"  SIZE={art1_path.stat().st_size}",
                f"  SHA256={art1_sha}",
                "",
                "ART models (unchanged from PR #669 / tag s-global-store-expand):",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-global-store-expand/_SPEC_ART_TWO.big",
                f"  SIZE={art2_path.stat().st_size}",
                f"  SHA256={art2_sha}",
                "",
                "ZIP:",
                f"  {rel_base}/SPECTER_ISRAEL_MF_CLEAR_MINES.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                f"TAG={tag}",
                f"RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/{tag}",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "\n".join(
            [
                "# Israel missile factory replaces Clear Mines",
                "",
                "Replaces Israel's remaining Clear Mines construction option",
                "(`AirF_AmericaDozerCommandSet` slot 14) with the existing",
                "`Command_ConstructIsrael_MissileFactory` button.",
                "",
                "Israel's starting dozer (`IsraelDozerCommandSet`) already had the",
                "missile factory at slot 14 and Global Store at slot 2; those slots",
                "are unchanged. The factory object, A-J roster, Fire commands, and",
                "artwork are reused. Other countries keep Clear Mines.",
                "",
                "ART is byte-identical to PR #670. RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("PACKED", data_path.stat().st_size, data_sha)
    print("ART_ONE", art1_path.stat().st_size, art1_sha)
    print("ART_TWO", art2_path.stat().st_size, art2_sha)
    print("ZIP", zip_path.stat().st_size, zip_sha)
    print("STATIC VALIDATION: PASS")
    print("RUNTIME_TEST=NOT RUN")
    print("patched", patched_cs_files)


if __name__ == "__main__":
    main()
