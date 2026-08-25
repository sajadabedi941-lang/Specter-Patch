#!/usr/bin/env python3
"""Pack France air force rebuild into _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big.

Patches packed CommandSet.ini France airbase menus (the live NATO placeholders),
inlines construct buttons, injects confirmed-ART aircraft, portraits, weapons, CSF.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_china_heavy_aircraft as ch

ROOT = Path("/workspace")
DONOR = Path("/tmp/donor_france_air")
BASE_DATA = Path("/tmp/china_aircraft_final_fix/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/china_aircraft_final_fix/_SPEC_ART_ONE.big")
PATCH = ROOT / "patch/Data"

CSF_LABELS = {
    "CONTROLBAR:ConstructFranceJetRafaleC": "Rafale C F4",
    "CONTROLBAR:ToolTipFranceJetRafaleC": "French Rafale C air-superiority fighter. Meteor and MICA.",
    "OBJECT:FranceJetRafaleC": "Rafale C F4\r\nMeteor + MICA",
    "CONTROLBAR:ConstructFranceJetRafaleB": "Rafale B",
    "CONTROLBAR:ToolTipFranceJetRafaleB": "French Rafale B strike fighter. SCALP cruise missiles.",
    "OBJECT:FranceJetRafaleB": "Rafale B\r\nSCALP strike",
    "CONTROLBAR:ConstructFranceJetRafaleM": "Rafale M",
    "CONTROLBAR:ToolTipFranceJetRafaleM": "French Rafale M naval strike fighter. Anti-ship missiles.",
    "OBJECT:FranceJetRafaleM": "Rafale M\r\nAnti-ship",
    "CONTROLBAR:ConstructFranceJetMirage2000": "Mirage 2000",
    "CONTROLBAR:ToolTipFranceJetMirage2000": "French Mirage 2000 fighter.",
    "OBJECT:FranceJetMirage2000": "Mirage 2000",
    "CONTROLBAR:ConstructFranceJetMirage2000D": "Mirage 2000D",
    "CONTROLBAR:ToolTipFranceJetMirage2000D": "French Mirage 2000D strike aircraft.",
    "OBJECT:FranceJetMirage2000D": "Mirage 2000D\r\nStrike",
    "CONTROLBAR:ConstructFranceJetMirageF1CT": "Mirage F1CT",
    "CONTROLBAR:ToolTipFranceJetMirageF1CT": "French Mirage F1CT fighter-bomber.",
    "OBJECT:FranceJetMirageF1CT": "Mirage F1CT",
    "CONTROLBAR:ConstructFranceJetMirageIIIE": "Mirage IIIE",
    "CONTROLBAR:ToolTipFranceJetMirageIIIE": "French Mirage IIIE fighter-bomber.",
    "OBJECT:FranceJetMirageIIIE": "Mirage IIIE",
    "CONTROLBAR:ConstructFranceJetMirage5": "Mirage 5",
    "CONTROLBAR:ToolTipFranceJetMirage5": "French Mirage 5 strike aircraft.",
    "OBJECT:FranceJetMirage5": "Mirage 5",
    "CONTROLBAR:ConstructFranceJetC130": "C-130 Hercules",
    "CONTROLBAR:ToolTipFranceJetC130": "French C-130 Hercules transport.",
    "OBJECT:FranceJetC130": "C-130 Hercules\r\nTransport",
    "CONTROLBAR:ConstructFranceAircraftE3": "E-3 AWACS",
    "CONTROLBAR:ToolTipFranceAircraftE3": "French E-3 airborne radar aircraft.",
    "OBJECT:FranceAircraftE3": "E-3 AWACS",
    "CONTROLBAR:ConstructFranceHelicopterNH90": "NH90 Caiman",
    "CONTROLBAR:ToolTipFranceHelicopterNH90": "French NH90 transport helicopter.",
    "OBJECT:FranceHelicopterNH90": "NH90 Caiman",
    "CONTROLBAR:ConstructFranceHelicopterTiger": "Tiger HAD",
    "CONTROLBAR:ToolTipFranceHelicopterTiger": "French Tiger HAD attack helicopter.",
    "OBJECT:FranceHelicopterTiger": "Tiger HAD",
    "CONTROLBAR:ConstructNatoAirfield": "Fighter Airbase",
    "CONTROLBAR:ToolTipUSABuildNatoAirfield": "Builds the French fighter airbase.",
    "CONTROLBAR:ConstructFrance_Airfield": "Fighter Airbase",
    "CONTROLBAR:ToolTipConstructFrance_Airfield": "Builds the French fighter airbase.",
    "CONTROLBAR:ConstructFrance_HeavyAirBase": "Heavy Airbase",
    "CONTROLBAR:ToolTipConstructFrance_HeavyAirBase": "Builds the French heavy airbase.",
    "OBJECT:France_LargeAirBase": "Fighter Airbase",
    "OBJECT:France_HeavyAirBase": "Heavy Airbase",
    "OBJECT:France_Airfield": "Fighter Airbase",
    "OBJECT:FranceAirfield": "Fighter Airbase",
}

FIGHTER_COMMANDSET = """CommandSet {name}
  1  = Command_ConstructFranceJetRafaleC
  2  = Command_ConstructFranceJetRafaleB
  3  = Command_ConstructFranceJetRafaleM
  4  = Command_ConstructFranceJetMirage2000
  5  = Command_ConstructFranceJetMirage2000D
  6  = Command_ConstructFranceJetMirageF1CT
  7  = Command_ConstructFranceJetMirageIIIE
  8  = Command_ConstructFranceJetMirage5
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

HEAVY_COMMANDSET = """CommandSet France_HeavyAirBaseCommandSet
  1  = Command_ConstructFranceJetC130
  2  = Command_ConstructFranceAircraftE3
  3  = Command_ConstructFranceHelicopterNH90
  4  = Command_ConstructFranceHelicopterTiger
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

SUPPLY_COMMANDSET = """CommandSet FranceSupplyCenterCommandSet
  14 = Command_Sell
End
"""

NATO_REMOVED = [
    "Command_ConstructFranceJetRafaleF3",
    "Command_ConstructFranceJetF35C",
    "Command_ConstructFranceJetEF2000T4",
    "Command_ConstructFranceJetEA18G",
    "Command_ConstructFranceJetF16DBlk52",
    "Command_ConstructFranceJetF35C_AA",
    "Command_ConstructFranceJetEF2000T4_AA",
    "Command_ConstructFranceJetEF2000T4_CAS",
    "Command_ConstructFranceHelicopterAH64E",
    "Command_ConstructFranceJetTornadoECR",
    "Command_ConstructFranceJetE3AAWACS",
    "Command_ConstructFranceHelicopterUH60",
    "Command_ConstructFranceHelicopterCH47F",
    "Command_ConstructFrance_JetF35C",
    "Command_ConstructFrance_JetEF2000T4",
    "Command_ConstructFrance_JetF16DBlk52",
    "Command_ConstructFrance_JetEF2000T4_CAS",
    "Command_ConstructFrance_HelicopterCH47F",
    "Command_ConstructFrance_E3A",
    "Command_ConstructFrance_Rafale",
]

NEW_BTNS = [
    "Command_ConstructFranceJetRafaleC",
    "Command_ConstructFranceJetRafaleB",
    "Command_ConstructFranceJetRafaleM",
    "Command_ConstructFranceJetMirage2000",
    "Command_ConstructFranceJetMirage2000D",
    "Command_ConstructFranceJetMirageF1CT",
    "Command_ConstructFranceJetMirageIIIE",
    "Command_ConstructFranceJetMirage5",
    "Command_ConstructFranceJetC130",
    "Command_ConstructFranceAircraftE3",
    "Command_ConstructFranceHelicopterNH90",
    "Command_ConstructFranceHelicopterTiger",
]

OBJECT_FILES = [
    ("INI/Object/Specter/French Armed Forces/Airforce/FranceJetRafaleC.ini", r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleC.ini"),
    ("INI/Object/Specter/French Armed Forces/Airforce/FranceJetRafaleB.ini", r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleB.ini"),
    ("INI/Object/Specter/French Armed Forces/Airforce/FranceJetRafaleM.ini", r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetRafaleM.ini"),
    ("INI/Object/Specter/French Armed Forces/Airforce/FranceJetMirage2000.ini", r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage2000.ini"),
    ("INI/Object/Specter/French Armed Forces/Airforce/FranceJetMirage2000D.ini", r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage2000D.ini"),
    ("INI/Object/Specter/French Armed Forces/Airforce/FranceJetMirageF1CT.ini", r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirageF1CT.ini"),
    ("INI/Object/Specter/French Armed Forces/Airforce/FranceJetMirageIIIE.ini", r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirageIIIE.ini"),
    ("INI/Object/Specter/French Armed Forces/Airforce/FranceJetMirage5.ini", r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetMirage5.ini"),
    ("INI/Object/Specter/French Armed Forces/Airforce/FranceJetC130.ini", r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetC130.ini"),
    ("INI/Object/Specter/French Armed Forces/Airforce/FranceAircraftE3.ini", r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceAircraftE3.ini"),
    ("INI/Object/Specter/French Armed Forces/Rotary/FranceHelicopterNH90.ini", r"Data\INI\Object\Specter\French Armed Forces\Rotary\FranceHelicopterNH90.ini"),
    ("INI/Object/Specter/French Armed Forces/Rotary/FranceHelicopterTiger.ini", r"Data\INI\Object\Specter\French Armed Forces\Rotary\FranceHelicopterTiger.ini"),
    ("INI/CommandSet_France.ini", r"Data\INI\CommandSet_France.ini"),
    ("INI/CommandButton_FranceAirforce.ini", r"Data\INI\CommandButton_FranceAirforce.ini"),
    ("INI/Weapon_FranceAirforce.ini", r"Data\INI\Weapon_FranceAirforce.ini"),
    ("INI/MappedImages/HandCreated/zFrance_AirbasePortrait_Images.INI", r"Data\INI\MappedImages\HandCreated\zFrance_AirbasePortrait_Images.INI"),
]

ART_FILES = [
    "Art/w3d/LSFRafale.W3D",
    "Art/w3d/LSFRafaled.W3D",
    "Art/w3d/LSFRafalek.W3D",
    "Art/w3d/LSFRafaleAS.W3D",
    "Art/w3d/LSFRafaleASd.W3D",
    "Art/w3d/LSFMirage2000.W3D",
    "Art/w3d/LSFMirage2000d.W3D",
    "Art/w3d/LSFMirage2000k.W3D",
    "Art/w3d/LSFMirage2KD.W3D",
    "Art/w3d/LSFMirage2KDd.W3D",
    "Art/w3d/LSFMirage2KDk.W3D",
    "Art/w3d/LSFFRF1.W3D",
    "Art/w3d/LSFFRF1d.W3D",
    "Art/w3d/LSFFRF1k.W3D",
    "Art/w3d/LSFMirage3.W3D",
    "Art/w3d/LSFMirage3d.W3D",
    "Art/w3d/LSFMirage3k.W3D",
    "Art/w3d/LSFMirage5.W3D",
    "Art/w3d/LSFMirage5d.W3D",
    "Art/w3d/LSFMirage5k.W3D",
    "Art/w3d/LSFUSAC130.W3D",
    "Art/w3d/LSFUSAC130d.W3D",
    "Art/w3d/LSFUSAC130k.W3D",
    "Art/w3d/E3.W3D",
    "Art/w3d/LSFFRNH90.W3D",
    "Art/w3d/LSFFRTiger.W3D",
    "Art/w3d/LSFFRTigerd.W3D",
    "Art/w3d/LSFFRTigerk.W3D",
    "Art/Textures/LSFRafale.dds",
    "Art/Textures/LSFRafaled.dds",
    "Art/Textures/LSFRafalek.dds",
    "Art/Textures/Mirage2000.dds",
    "Art/Textures/Mirage2000d.dds",
    "Art/Textures/Mirage2000k.dds",
    "Art/Textures/LSFMirage2KD.dds",
    "Art/Textures/LSFMirage2KDd.dds",
    "Art/Textures/LSFMirage2KDk.dds",
    "Art/Textures/LSFFRF1.dds",
    "Art/Textures/LSFFRF1d.dds",
    "Art/Textures/LSFFRF1k.dds",
    "Art/Textures/LSFMirage5.dds",
    "Art/Textures/LSFMirage5d.dds",
    "Art/Textures/LSFMirage5k.dds",
    "Art/Textures/LSFFRTiger.dds",
    "Art/Textures/LSFFRTigerd.dds",
    "Art/Textures/LSFFRTigerk.dds",
    "Art/Textures/LSFUSAC130.tga",
]

PORTRAIT_SRC = {
    "SPEC_FranceRafaleC.tga": "Art/Textures/RafaleAntiAirTB.tga",
    "SPEC_FranceRafaleB.tga": "Art/Textures/RafaleStrike1.tga",
    "SPEC_FranceRafaleM.tga": "Art/Textures/SuperRafaleTB.tga",
    "SPEC_FranceMirage2000.tga": "Art/Textures/mirage2000egyTB.tga",
    "SPEC_FranceMirage2000D.tga": "Art/Textures/Mirage2000DStrike.tga",
    "SPEC_FranceMirageF1CT.tga": "Art/Textures/LSFFRF1.dds",
    "SPEC_FranceMirageIIIE.tga": "Art/Textures/autreM2000egyTB.tga",
    "SPEC_FranceMirage5.tga": "Art/Textures/LSFMirage5.dds",
    "SPEC_FranceC130.tga": "Art/Textures/LSFUSAC130.tga",
    "SPEC_FranceE3.tga": "Art/Textures/USAawacs.tga",
    "SPEC_FranceNH90.tga": "Art/Textures/EUNH90TB.tga",
    "SPEC_FranceTiger.tga": "Art/Textures/LSFFRTiger.dds",
}


def replace_block(text: str, name: str, new_block: str) -> str:
    pat = re.compile(rf"CommandSet {re.escape(name)}\s*\n.*?^End\s*$", re.M | re.S)
    if not pat.search(text):
        raise SystemExit(f"{name} not found")
    return pat.sub(new_block.rstrip() + "\n", text, count=1)


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


def parse_tga(data: bytes):
    w, h = struct.unpack_from("<HH", data, 12)
    bpp = data[16]
    origin = data[17]
    img_type = data[2]
    if img_type != 2 or bpp not in (24, 32):
        raise SystemExit(f"unsupported TGA type={img_type} bpp={bpp}")
    idlen = data[0]
    payload = data[18 + idlen :]
    pixels = []
    top = bool(origin & 0x20)
    stride = (bpp // 8) * w
    for y in range(h):
        src_y = y if top else (h - 1 - y)
        row = []
        off = src_y * stride
        for x in range(w):
            p = off + x * (bpp // 8)
            b, g, r = payload[p], payload[p + 1], payload[p + 2]
            a = payload[p + 3] if bpp == 32 else 255
            row.append((r, g, b, a))
        pixels.append(row)
    return pixels


def resize(pixels, tw=150, th=113):
    h = len(pixels)
    w = len(pixels[0])
    out = []
    for y in range(th):
        sy = min(h - 1, y * h // th)
        row = []
        for x in range(tw):
            sx = min(w - 1, x * w // tw)
            row.append(pixels[sy][sx])
        out.append(row)
    return out


def make_portrait(src: Path) -> bytes:
    raw = src.read_bytes()
    if src.suffix.lower() == ".dds":
        _w, _h, pixels = ch.decode_dds_rgba(raw)
    else:
        pixels = parse_tga(raw)
    h = len(pixels)
    w = len(pixels[0])
    if w != 150 or h not in (110, 111, 113):
        pixels = resize(pixels, 150, 113)
    return ch.write_tga32(pixels)


def parse_check(files: dict[str, bytes]) -> None:
    errors = []
    for name, content in files.items():
        if not name.lower().endswith(".ini"):
            continue
        text = content.decode("utf-8")
        if "\r" in text:
            errors.append(f"{name}: CRLF")
        n_obj = len(re.findall(r"^Object\s+\S+", text, re.M))
        n_wpn = len(re.findall(r"^Weapon\s+\S+", text, re.M))
        n_btn = len(re.findall(r"^CommandButton\s+\S+", text, re.M))
        n_end = len(re.findall(r"^End\s*$", text, re.M))
        if n_end == 0 and (n_obj + n_wpn + n_btn) > 0:
            errors.append(f"{name}: missing End")
    if errors:
        raise SystemExit("PARSER CHECK FAIL\n" + "\n".join(errors))
    print("PARSER CHECK PASS overlay INI")


def validate_france_menus(cs_text: str, cb_text: str) -> None:
    errors = []
    fighter_sets = ("FranceAirfieldCommandSet", "France_LargeAirBaseCommandSet", "France_AirfieldCommandSet")
    core = set(re.findall(r"^CommandButton (\S+)\s*$", cb_text, re.M))
    for name in ("FranceAirfieldCommandSet", "France_LargeAirBaseCommandSet", "France_HeavyAirBaseCommandSet"):
        if cs_text.count(f"CommandSet {name}") != 1:
            errors.append(f"{name} count != 1")
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
    for btn in NEW_BTNS[:8]:
        if btn not in fighter:
            errors.append(f"fighter menu missing {btn}")
    heavy = ch.grab_block(cs_text, "France_HeavyAirBaseCommandSet")
    for btn in NEW_BTNS[8:]:
        if btn not in heavy:
            errors.append(f"heavy menu missing {btn}")
    supply = ch.grab_block(cs_text, "FranceSupplyCenterCommandSet")
    if "Command_ConstructFranceHelicopterCH47F" in supply:
        errors.append("CH-47 still on France supply center")
    if errors:
        raise SystemExit("PARSER CHECK FAIL CommandButton refs\n" + "\n".join(errors))
    print("PARSER CHECK PASS CommandButton refs")


def inline_buttons(cs_text: str, buttons: str) -> str:
    needle = "CommandSet FranceAirfieldCommandSet"
    idx = cs_text.find(needle)
    if idx < 0:
        raise SystemExit("FranceAirfieldCommandSet not found")
    for m in re.finditer(r"CommandButton (\S+)\s*\n.*?^End\s*$", buttons, re.M | re.S):
        btn = m.group(1)
        cs_text, n = re.subn(
            rf"CommandButton {re.escape(btn)}\s*\n.*?^End\s*\n?",
            "",
            cs_text,
            count=1,
            flags=re.M | re.S,
        )
        if n:
            print(f"Relocated {btn}")
    idx = cs_text.find(needle)
    cs_text = cs_text[:idx] + buttons.rstrip() + "\n\n" + cs_text[idx:]
    print("Inlined France construct buttons before FranceAirfieldCommandSet")
    return cs_text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/france_airforce_rebuild"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    overlay: dict[str, bytes] = {}
    for rel, dest in OBJECT_FILES:
        p = PATCH / rel
        overlay[dest] = ch.lf(p.read_bytes())
    parse_check(overlay)
    buttons = overlay[r"Data\INI\CommandButton_FranceAirforce.ini"].decode("ascii")
    # strip leading comments for inline
    btn_body = "\n".join(
        line for line in buttons.splitlines() if not line.startswith(";")
    ).strip() + "\n"

    data_entries, data_raw = ch.read_big(BASE_DATA)
    art_entries, art_raw = ch.read_big(BASE_ART)
    data_map: dict[str, tuple[str, bytes]] = {}
    data_keys = []
    for name, off, size in data_entries:
        key = ch.norm_key(name)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (name.replace("/", "\\"), data_raw[off:off + size])
    art_map: dict[str, tuple[str, bytes]] = {}
    art_keys = []
    for name, off, size in art_entries:
        key = ch.norm_key(name)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (name.replace("/", "\\"), art_raw[off:off + size])

    cs_key = "data\\ini\\commandset.ini"
    cb_key = "data\\ini\\commandbutton.ini"
    cs_name, cs_blob = data_map[cs_key]
    cb_name, cb_blob = data_map[cb_key]
    cs_text = cs_blob.decode("latin1")
    cb_text = cb_blob.decode("latin1")

    cs_text = inline_buttons(cs_text, btn_body)
    cs_text = replace_block(cs_text, "FranceAirfieldCommandSet", FIGHTER_COMMANDSET.format(name="FranceAirfieldCommandSet"))
    cs_text = replace_block(cs_text, "France_LargeAirBaseCommandSet", FIGHTER_COMMANDSET.format(name="France_LargeAirBaseCommandSet"))
    cs_text = replace_block(cs_text, "France_HeavyAirBaseCommandSet", HEAVY_COMMANDSET)
    cs_text = replace_block(cs_text, "FranceSupplyCenterCommandSet", SUPPLY_COMMANDSET)
    data_map[cs_key] = (cs_name, ch.lf(cs_text.encode("latin1")))

    validate_france_menus(cs_text, cb_text)
    ch.validate_commandset_button_refs(cs_text, cb_text)

    wpn_key = "data\\ini\\weapon.ini"
    wpn_name, wpn_blob = data_map[wpn_key]
    extra_wpn = overlay[r"Data\INI\Weapon_FranceAirforce.ini"]
    marker = b"\n; ===== SPECTER FRANCE AIRFORCE WEAPONS =====\n"
    if b"France_Weapon_Meteor_RafaleC" not in wpn_blob:
        data_map[wpn_key] = (wpn_name, wpn_blob.rstrip() + marker + extra_wpn)
        print("Inlined France weapons into Weapon.ini")
    else:
        print("France weapons already in Weapon.ini")

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
            continue  # inlined into CommandSet.ini
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (dest, content)
        print("DATA inject", dest)

    for rel in ART_FILES:
        src = DONOR / rel
        if not src.exists():
            raise SystemExit(f"missing donor ART {src}")
        dest = rel.replace("/", "\\")
        dest = dest.replace("Art\\w3d\\", "Art\\W3D\\")
        dest = dest.replace("Art\\Textures\\", "Art\\Textures\\")
        # normalize W3D folder case to Art\W3D\
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
        tga = make_portrait(src)
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

    zpath = out / "FRANCE_AIRFORCE_REBUILD.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.writestr(
            "INSTALL.txt",
            "Copy _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big into the Specter Data folder.\n"
            "Keep EnglishZH.big and AudioZH.big unchanged.\n"
            "France Fighter Airbase: Rafale C/B/M, Mirage 2000/2000D/F1CT/IIIE/5.\n"
            "France Heavy Airbase: C-130, E-3, NH90, Tiger HAD.\n",
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
    )
    print(report.read_text())
    print("wrote", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
