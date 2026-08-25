#!/usr/bin/env python3
"""Pack France helicopter force into _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big.

Builds on the France air-force rebuild pack:
  Helicopter Base: Tiger HAD, NH90 Caiman, Caracal EC725
  Heavy Airbase: C-130 + E-3 only
  Tiger HAD: autocannon + ATGM + rockets
  Caracal: Mi-171 appearance donor, French gameplay name
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_china_heavy_aircraft as ch
import pack_france_airforce as fr

ROOT = Path("/workspace")
DONOR = Path("/tmp/donor_france_air")
BASE_DATA = Path("/tmp/france_airforce_rebuild/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/france_airforce_rebuild/_SPEC_ART_ONE.big")
PATCH = ROOT / "patch/Data"

CSF_LABELS = dict(fr.CSF_LABELS)
CSF_LABELS.update(
    {
        "CONTROLBAR:ConstructFranceHelicopterTiger": "Tiger HAD",
        "CONTROLBAR:ToolTipFranceHelicopterTiger": "French Tiger HAD attack helicopter. Autocannon, missiles, and rockets.",
        "OBJECT:FranceHelicopterTiger": "Tiger HAD\r\nCannon + missiles + rockets",
        "CONTROLBAR:ConstructFranceHelicopterNH90": "NH90 Caiman",
        "CONTROLBAR:ToolTipFranceHelicopterNH90": "French NH90 Caiman transport helicopter.",
        "OBJECT:FranceHelicopterNH90": "NH90 Caiman",
        "CONTROLBAR:ConstructFranceHelicopterCaracal": "Caracal EC725",
        "CONTROLBAR:ToolTipFranceHelicopterCaracal": "French Caracal EC725 heavy transport helicopter.",
        "OBJECT:FranceHelicopterCaracal": "Caracal EC725\r\nTroop transport",
        "CONTROLBAR:ConstructFranceHelicopterBase": "Helicopter Base",
        "CONTROLBAR:ToolTipConstructFranceHelicopterBase": "Builds the French helicopter base.",
        "OBJECT:France_HelicopterBase": "Helicopter Base",
    }
)

FIGHTER_COMMANDSET = fr.FIGHTER_COMMANDSET

HEAVY_COMMANDSET = """CommandSet France_HeavyAirBaseCommandSet
  1  = Command_ConstructFranceJetC130
  2  = Command_ConstructFranceAircraftE3
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

HELI_COMMANDSET = """CommandSet France_HelicopterBaseCommandSet
  1  = Command_ConstructFranceHelicopterTiger
  2  = Command_ConstructFranceHelicopterNH90
  3  = Command_ConstructFranceHelicopterCaracal
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

SUPPLY_COMMANDSET = fr.SUPPLY_COMMANDSET

NATO_REMOVED = list(fr.NATO_REMOVED)

FIGHTER_BTNS = [
    "Command_ConstructFranceJetRafaleC",
    "Command_ConstructFranceJetRafaleB",
    "Command_ConstructFranceJetRafaleM",
    "Command_ConstructFranceJetMirage2000",
    "Command_ConstructFranceJetMirage2000D",
    "Command_ConstructFranceJetMirageF1CT",
    "Command_ConstructFranceJetMirageIIIE",
    "Command_ConstructFranceJetMirage5",
]
HEAVY_BTNS = [
    "Command_ConstructFranceJetC130",
    "Command_ConstructFranceAircraftE3",
]
HELI_BTNS = [
    "Command_ConstructFranceHelicopterTiger",
    "Command_ConstructFranceHelicopterNH90",
    "Command_ConstructFranceHelicopterCaracal",
]

OBJECT_FILES = list(fr.OBJECT_FILES) + [
    ("INI/Object/Specter/French Armed Forces/Rotary/FranceHelicopterCaracal.ini", r"Data\INI\Object\Specter\French Armed Forces\Rotary\FranceHelicopterCaracal.ini"),
    ("INI/Object/Specter/French Armed Forces/Buildings/France_HelicopterBase.ini", r"Data\INI\Object\Specter\French Armed Forces\Buildings\France_HelicopterBase.ini"),
]

ART_FILES = list(fr.ART_FILES) + [
    "Art/w3d/LSFRUMi171.W3D",
    "Art/w3d/LSFRUMi171d.W3D",
    "Art/w3d/LSFRUMi171k.W3D",
    "Art/Textures/LSFRUMi171.dds",
    "Art/Textures/LSFRUMi171d.dds",
    "Art/Textures/LSFRUMi171k.dds",
]

PORTRAIT_SRC = dict(fr.PORTRAIT_SRC)
PORTRAIT_SRC.update(
    {
        "SPEC_FranceCaracal.tga": "Art/Textures/LSFRUMi171.dds",
        "SPEC_FranceHelicopterBase.tga": "Art/Textures/EUNH90TB.tga",
    }
)

HELI_DOZER_BTN = """CommandButton Command_ConstructFranceHelicopterBase
  Command       = DOZER_CONSTRUCT
  Object        = France_HelicopterBase
  TextLabel     = CONTROLBAR:ConstructFranceHelicopterBase
  ButtonImage   = SPEC_FranceHelicopterBase
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipConstructFranceHelicopterBase
End
"""

WPN_MARKER = b"\n; ===== SPECTER FRANCE AIRFORCE WEAPONS =====\n"


def patch_csf(data: bytes) -> bytes:
    version, unk, lang, labels = ch.parse_csf(data)
    have_idx = {name: i for i, (_, name, _) in enumerate(labels)}
    added = updated = 0
    for key, value in CSF_LABELS.items():
        if key in have_idx:
            i = have_idx[key]
            mag, name, _strings = labels[i]
            labels[i] = (mag, name, [(ch.CSF_STR_MAGIC, value, b"")])
            updated += 1
        else:
            labels.append((ch.CSF_LBL_MAGIC, key, [(ch.CSF_STR_MAGIC, value, b"")]))
            added += 1
            have_idx[key] = len(labels) - 1
    print(f"CSF added {added} labels, updated {updated}")
    return ch.build_csf(version, unk, lang, labels)


def insert_heli_commandset(cs_text: str) -> str:
    if "CommandSet France_HelicopterBaseCommandSet" in cs_text:
        return fr.replace_block(cs_text, "France_HelicopterBaseCommandSet", HELI_COMMANDSET)
    pat = re.compile(r"(CommandSet France_HeavyAirBaseCommandSet\s*\n.*?^End\s*$)", re.M | re.S)
    if not pat.search(cs_text):
        raise SystemExit("France_HeavyAirBaseCommandSet missing; cannot insert heli commandset")
    return pat.sub(r"\1\n\n" + HELI_COMMANDSET.rstrip() + "\n", cs_text, count=1)


def patch_dozer(cs_text: str) -> str:
    block = ch.grab_block(cs_text, "FranceDozerCommandSet")
    if "Command_ConstructFranceHelicopterBase" in block:
        print("FranceDozerCommandSet already has Helicopter Base")
        return cs_text
    new_block, n = re.subn(
        r"^( 12\s*=\s*)Command_ConstructAmericaLgm30\s*$",
        r"\1Command_ConstructFranceHelicopterBase",
        block,
        count=1,
        flags=re.M,
    )
    if n != 1:
        raise SystemExit("FranceDozerCommandSet slot 12 is not Command_ConstructAmericaLgm30")
    return fr.replace_block(cs_text, "FranceDozerCommandSet", new_block)


def insert_dozer_button(cb_text: str) -> str:
    cb_text = re.sub(
        r"CommandButton Command_ConstructFranceHelicopterBase\s*\n.*?^End\s*\n?",
        "",
        cb_text,
        count=1,
        flags=re.M | re.S,
    )
    needle = "CommandButton Command_ConstructFrance_HeavyAirBase"
    idx = cb_text.find(needle)
    if idx < 0:
        raise SystemExit("Command_ConstructFrance_HeavyAirBase not in CommandButton.ini")
    # insert after that button's End
    m = re.search(r"CommandButton Command_ConstructFrance_HeavyAirBase\s*\n.*?^End\s*$", cb_text, re.M | re.S)
    if not m:
        raise SystemExit("HeavyAirBase button block not found")
    insert_at = m.end()
    cb_text = cb_text[:insert_at] + "\n\n" + HELI_DOZER_BTN.rstrip() + "\n" + cb_text[insert_at:]
    print("Inserted Command_ConstructFranceHelicopterBase into CommandButton.ini")
    return cb_text


def replace_weapon_block(wpn_blob: bytes, extra_wpn: bytes) -> bytes:
    idx = wpn_blob.find(WPN_MARKER)
    if idx < 0:
        idx = wpn_blob.find(b"France_Weapon_Meteor_RafaleC")
        if idx >= 0:
            # fall back: append if marker missing
            return wpn_blob.rstrip() + WPN_MARKER + extra_wpn
        return wpn_blob.rstrip() + WPN_MARKER + extra_wpn
    return wpn_blob[:idx].rstrip() + WPN_MARKER + extra_wpn


def validate_france_menus(cs_text: str, cb_text: str) -> None:
    errors = []
    core = set(re.findall(r"^CommandButton (\S+)\s*$", cb_text, re.M))
    names = (
        "FranceAirfieldCommandSet",
        "France_LargeAirBaseCommandSet",
        "France_HeavyAirBaseCommandSet",
        "France_HelicopterBaseCommandSet",
        "FranceDozerCommandSet",
    )
    for name in names:
        if cs_text.count(f"CommandSet {name}") != 1:
            errors.append(f"{name} count={cs_text.count(f'CommandSet {name}')}")
        block = ch.grab_block(cs_text, name)
        idx = cs_text.find(f"CommandSet {name}")
        declared = core | set(re.findall(r"^CommandButton (\S+)\s*$", cs_text[:idx], re.M))
        for line in block.splitlines():
            m = re.match(r"^\s*\d+\s*=\s*(Command_\S+)\s*$", line)
            if not m:
                continue
            btn = m.group(1)
            if btn not in declared:
                errors.append(f"{name} refs unknown CommandButton {btn}")
            if btn in NATO_REMOVED:
                errors.append(f"{name} still has NATO button {btn}")
        slots = [int(x) for x in re.findall(r"^\s*(\d+)\s*=", block, re.M)]
        if len(slots) != len(set(slots)):
            errors.append(f"{name} duplicate slots {slots}")

    fighter = ch.grab_block(cs_text, "France_LargeAirBaseCommandSet")
    for btn in FIGHTER_BTNS:
        if btn not in fighter:
            errors.append(f"fighter menu missing {btn}")
    heavy = ch.grab_block(cs_text, "France_HeavyAirBaseCommandSet")
    for btn in HEAVY_BTNS:
        if btn not in heavy:
            errors.append(f"heavy menu missing {btn}")
    for btn in HELI_BTNS:
        if btn in heavy:
            errors.append(f"heavy menu still has heli {btn}")
    heli = ch.grab_block(cs_text, "France_HelicopterBaseCommandSet")
    for btn in HELI_BTNS:
        if btn not in heli:
            errors.append(f"heli menu missing {btn}")
    dozer = ch.grab_block(cs_text, "FranceDozerCommandSet")
    if "Command_ConstructFranceHelicopterBase" not in dozer:
        errors.append("dozer missing Command_ConstructFranceHelicopterBase")
    supply = ch.grab_block(cs_text, "FranceSupplyCenterCommandSet")
    if "Command_ConstructFranceHelicopterCH47F" in supply:
        errors.append("CH-47 still on France supply center")

    # unique SPEC_France portraits on new heli buttons
    for btn, img in (
        ("Command_ConstructFranceHelicopterTiger", "SPEC_FranceTiger"),
        ("Command_ConstructFranceHelicopterNH90", "SPEC_FranceNH90"),
        ("Command_ConstructFranceHelicopterCaracal", "SPEC_FranceCaracal"),
        ("Command_ConstructFranceHelicopterBase", "SPEC_FranceHelicopterBase"),
    ):
        blob = cs_text + "\n" + cb_text
        m = re.search(rf"CommandButton {re.escape(btn)}\s*\n.*?^End\s*$", blob, re.M | re.S)
        if not m:
            errors.append(f"missing CommandButton {btn}")
            continue
        if f"ButtonImage      = {img}" not in m.group(0) and f"ButtonImage   = {img}" not in m.group(0) and f"ButtonImage      = {img}" not in m.group(0):
            if f"ButtonImage" not in m.group(0) or img not in m.group(0):
                errors.append(f"{btn} missing portrait {img}")

    if errors:
        raise SystemExit("PARSER CHECK FAIL CommandButton refs\n" + "\n".join(errors))
    print("PARSER CHECK PASS CommandButton refs")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/france_helicopter_force"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    overlay: dict[str, bytes] = {}
    for rel, dest in OBJECT_FILES:
        p = PATCH / rel
        overlay[dest] = ch.lf(p.read_bytes())
    fr.parse_check(overlay)
    buttons = overlay[r"Data\INI\CommandButton_FranceAirforce.ini"].decode("ascii")
    btn_body = "\n".join(line for line in buttons.splitlines() if not line.startswith(";")).strip() + "\n"

    data_entries, data_raw = ch.read_big(BASE_DATA)
    art_entries, art_raw = ch.read_big(BASE_ART)
    data_map: dict[str, tuple[str, bytes]] = {}
    data_keys = []
    for name, off, size in data_entries:
        key = ch.norm_key(name)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (name.replace("/", "\\"), data_raw[off : off + size])
    art_map: dict[str, tuple[str, bytes]] = {}
    art_keys = []
    for name, off, size in art_entries:
        key = ch.norm_key(name)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (name.replace("/", "\\"), art_raw[off : off + size])

    cs_key = "data\\ini\\commandset.ini"
    cb_key = "data\\ini\\commandbutton.ini"
    cs_name, cs_blob = data_map[cs_key]
    cb_name, cb_blob = data_map[cb_key]
    cs_text = cs_blob.decode("latin1")
    cb_text = cb_blob.decode("latin1")

    cb_text = insert_dozer_button(cb_text)
    data_map[cb_key] = (cb_name, ch.lf(cb_text.encode("latin1")))

    cs_text = fr.inline_buttons(cs_text, btn_body)
    cs_text = fr.replace_block(cs_text, "FranceAirfieldCommandSet", FIGHTER_COMMANDSET.format(name="FranceAirfieldCommandSet"))
    cs_text = fr.replace_block(cs_text, "France_LargeAirBaseCommandSet", FIGHTER_COMMANDSET.format(name="France_LargeAirBaseCommandSet"))
    cs_text = fr.replace_block(cs_text, "France_HeavyAirBaseCommandSet", HEAVY_COMMANDSET)
    cs_text = insert_heli_commandset(cs_text)
    cs_text = fr.replace_block(cs_text, "FranceSupplyCenterCommandSet", SUPPLY_COMMANDSET)
    cs_text = patch_dozer(cs_text)
    data_map[cs_key] = (cs_name, ch.lf(cs_text.encode("latin1")))

    validate_france_menus(cs_text, cb_text)
    ch.validate_commandset_button_refs(cs_text, cb_text)

    wpn_key = "data\\ini\\weapon.ini"
    wpn_name, wpn_blob = data_map[wpn_key]
    extra_wpn = overlay[r"Data\INI\Weapon_FranceAirforce.ini"]
    data_map[wpn_key] = (wpn_name, replace_weapon_block(wpn_blob, extra_wpn))
    print("Replaced France weapons block in Weapon.ini")
    if b"France_Weapon_Rocket_Tiger" not in data_map[wpn_key][1]:
        raise SystemExit("Tiger rocket weapon missing after Weapon.ini patch")
    if b"France_Weapon_Cannon_Tiger" not in data_map[wpn_key][1]:
        raise SystemExit("Tiger cannon weapon missing after Weapon.ini patch")

    hc_key = "data\\ini\\mappedimages\\handcreated\\handcreatedmappedimages.ini"
    hc_name, hc_blob = data_map[hc_key]
    portraits_ini = overlay[r"Data\INI\MappedImages\HandCreated\zFrance_AirbasePortrait_Images.INI"].decode("ascii")
    hc_text = hc_blob.decode("latin1")
    for name in (
        "SPEC_FranceRafaleC",
        "SPEC_FranceRafaleB",
        "SPEC_FranceRafaleM",
        "SPEC_FranceMirage2000",
        "SPEC_FranceMirage2000D",
        "SPEC_FranceMirageF1CT",
        "SPEC_FranceMirageIIIE",
        "SPEC_FranceMirage5",
        "SPEC_FranceC130",
        "SPEC_FranceE3",
        "SPEC_FranceNH90",
        "SPEC_FranceTiger",
        "SPEC_FranceCaracal",
        "SPEC_FranceHelicopterBase",
    ):
        hc_text = re.sub(
            rf"^MappedImage {re.escape(name)}\s*\n.*?^End\s*$\n?",
            "",
            hc_text,
            count=1,
            flags=re.M | re.S,
        )
    if not hc_text.endswith("\n"):
        hc_text += "\n"
    hc_text += "\n" + portraits_ini.strip() + "\n"
    data_map[hc_key] = (hc_name, ch.lf(hc_text.encode("latin1")))

    csf_key = "data\\english\\generals.csf"
    csf_name, csf_blob = data_map[csf_key]
    csf_new = patch_csf(csf_blob)
    ch.validate_csf(csf_new, list(CSF_LABELS))
    data_map[csf_key] = (csf_name, csf_new)

    for dest, content in overlay.items():
        key = ch.norm_key(dest)
        if key.endswith("commandbutton_franceairforce.ini"):
            continue
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (dest, content)
        print("DATA inject", dest)

    for rel in ART_FILES:
        src = DONOR / rel
        if not src.exists():
            raise SystemExit(f"missing donor ART {src}")
        dest = rel.replace("/", "\\")
        parts = dest.split("\\")
        if parts[1].lower() == "w3d":
            dest = "Art\\W3D\\" + parts[2]
        elif parts[1].lower() == "textures":
            dest = "Art\\Textures\\" + parts[2]
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, src.read_bytes())
    print(f"ART injected {len(ART_FILES)} donor files")

    for dest_name, src_rel in PORTRAIT_SRC.items():
        src = DONOR / src_rel
        tga = fr.make_portrait(src)
        dest = f"Art\\Textures\\{dest_name}"
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, tga)
        print("portrait", dest_name, len(tga))

    out_data_map = {data_map[k][0]: data_map[k][1] for k in data_keys}
    out_art_map = {art_map[k][0]: art_map[k][1] for k in art_keys}
    data_big = ch.build_big(out_data_map)
    art_big = ch.build_big(out_art_map)
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_big)
    out_art.write_bytes(art_big)

    zpath = out / "FRANCE_HELICOPTER_FORCE.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.writestr(
            "INSTALL.txt",
            "Copy _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big into the Specter Data folder.\n"
            "Keep EnglishZH.big and AudioZH.big unchanged.\n"
            "France Fighter Airbase: Rafale C/B/M, Mirage 2000/2000D/F1CT/IIIE/5.\n"
            "France Heavy Airbase: C-130, E-3.\n"
            "France Helicopter Base: Tiger HAD, NH90 Caiman, Caracal EC725.\n",
        )
    report = out / "PACK_REPORT.txt"
    report.write_text(
        f"DATA sha256 {hashlib.sha256(data_big).hexdigest()}\n"
        f"ART  sha256 {hashlib.sha256(art_big).hexdigest()}\n"
        f"ZIP  sha256 {hashlib.sha256(zpath.read_bytes()).hexdigest()}\n"
        f"DATA bytes {len(data_big)}\n"
        f"ART  bytes {len(art_big)}\n"
        "PARSER CHECK PASS overlay INI\n"
        "PARSER CHECK PASS CommandButton refs\n"
        "CSF CHECK PASS\n"
        "PACKAGING=DATA+ART _SPEC_DATA_ONE.big _SPEC_ART_ONE.big\n"
        "HELI Tiger HAD LSFFRTiger cannon+ATGM+rockets\n"
        "HELI NH90 Caiman LSFFRNH90 transport/support\n"
        "HELI Caracal EC725 LSFRUMi171 donor troop transport\n"
        "BUILDING France_HelicopterBase Tiger/NH90/Caracal\n"
        "HEAVY C-130 + E-3 only\n"
        "SKIPPED naval heli (no French mesh)\n"
    )
    print(report.read_text())
    print("wrote", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
