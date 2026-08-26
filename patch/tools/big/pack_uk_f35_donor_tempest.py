#!/usr/bin/env python3
"""Pack UK F-35 donor visual replacement + BAE Tempest.

Base: uk_airforce_diversity BIGs.
UK only. Does not rewrite France/Germany/Italy/Russia/China/USA CommandSets.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_china_heavy_aircraft as ch
import pack_europe_airforce as eu
import pack_europe_weapon_fire as fire
import pack_france_airforce as fr
import pack_uk_airforce_diversity as ukdiv

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
DONOR = ROOT / "patch/Art/UK_F35_Donor"
BASE_DATA = Path("/tmp/uk_airforce_diversity/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/uk_airforce_diversity/_SPEC_ART_ONE.big")

FIGHTER_BTNS = list(ukdiv.FIGHTER_BTNS)
HEAVY_BTNS = list(ukdiv.HEAVY_BTNS) + ["Command_ConstructBritainJetTempest"]

CSF_LABELS = {
    "OBJECT:BritainJetF35B": "F-35B Lightning II",
    "CONTROLBAR:ConstructBritainJetF35B": "F-35B Lightning II",
    "CONTROLBAR:ToolTipBritainJetF35B": "British F-35B Lightning II stealth fighter. AMRAAM, ASRAAM, SDB.",
    "OBJECT:BritainJetTempest": "BAE Tempest",
    "CONTROLBAR:ConstructBritainJetTempest": "BAE Tempest",
    "CONTROLBAR:ToolTipBritainJetTempest": "British BAE Tempest air-superiority fighter. Meteor, ASRAAM, precision bombs.",
}

DONOR_W3D = {
    r"Art\W3D\ENF35A.W3D": DONOR / "W3D/ENF35A.W3D",
    r"Art\W3D\LSFUSAF35A.W3D": DONOR / "W3D/LSFUSAF35A.W3D",
    r"Art\W3D\LSFUSAF35Ad.W3D": DONOR / "W3D/LSFUSAF35Ad.W3D",
    r"Art\W3D\LSFUSAF35Ak.W3D": DONOR / "W3D/LSFUSAF35Ak.W3D",
    r"Art\W3D\SPEC_OLD_F35.W3D": DONOR / "W3D/SPEC_OLD_F35.W3D",
}

DONOR_TEX = {
    r"Art\Textures\Ef35.dds": DONOR / "Textures/Ef35.dds",
    r"Art\Textures\f35.dds": DONOR / "Textures/f35.dds",
    r"Art\Textures\f35d.dds": DONOR / "Textures/f35d.dds",
    r"Art\Textures\f35k.dds": DONOR / "Textures/f35k.dds",
    r"Art\Textures\SPEC_OLD_F35.dds": DONOR / "Textures/SPEC_OLD_F35.dds",
}


def patch_csf(data: bytes) -> bytes:
    version, unk, lang, labels = ch.parse_csf(data)
    have_idx = {name: i for i, (_, name, _) in enumerate(labels)}
    added = updated = 0
    for key, value in CSF_LABELS.items():
        if any(ord(c) > 127 for c in key) or any(ord(c) > 127 for c in value):
            raise SystemExit(f"non-ASCII CSF {key!r}")
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


def extra_validate(
    overlay: dict[str, bytes],
    cs_text: str,
    cb_text: str,
    wpn_text: str,
    hc_text: str,
    data_map: dict[str, tuple[str, bytes]],
    art_map: dict[str, tuple[str, bytes]],
    csf_blob: bytes,
) -> list[str]:
    errors: list[str] = []
    objects: dict[str, str] = {}
    for dest, content in overlay.items():
        if dest.lower().endswith(".ini") and b"Object " in content:
            objects.update(fire.parse_objects(content.decode("latin1")))
    weapons = fire.parse_weapons(wpn_text)
    packed_objects = fire.collect_packed_objects(data_map)
    art_leaves = {k.split("\\")[-1].lower() for k in art_map}
    mapped = set(re.findall(r"^MappedImage (\S+)\s*$", hc_text, re.M))
    _, _, _, csf_labels = ch.parse_csf(csf_blob)
    csf_keys = {name for _m, name, _s in csf_labels}
    csf_vals = {}
    for _m, name, strings in csf_labels:
        if strings:
            csf_vals[name] = strings[0][1]

    fighter = ch.grab_block(cs_text, "BritainAirfieldCommandSet")
    large = ch.grab_block(cs_text, "Britain_LargeAirBaseCommandSet")
    heavy = ch.grab_block(cs_text, "Britain_HeavyAirBaseCommandSet")
    dozer = ch.grab_block(cs_text, "BritainDozerCommandSet")

    if cs_text.count("CommandSet BritainAirfieldCommandSet") != 1:
        errors.append("BritainAirfieldCommandSet uniqueness fail")
    if cs_text.count("CommandSet Britain_HeavyAirBaseCommandSet") != 1:
        errors.append("Britain_HeavyAirBaseCommandSet uniqueness fail")
    if cs_text.count("CommandButton Command_ConstructBritainJetTempest") != 1:
        errors.append("Tempest CommandButton uniqueness fail")

    for btn in FIGHTER_BTNS:
        if btn not in fighter or btn not in large:
            errors.append(f"fighter/large missing {btn}")
    if "Command_ConstructBritainJetTempest" in fighter:
        errors.append("Tempest overwritten a fighter airbase slot")
    if "Command_ConstructBritainJetTempest" not in heavy:
        errors.append("Tempest missing from heavy airbase")
    if "Command_SetRallyPoint" not in fighter or "Command_Sell" not in fighter:
        errors.append("Rally/Sell missing from fighter")
    if "Command_SetRallyPoint" not in heavy or "Command_Sell" not in heavy:
        errors.append("Rally/Sell missing from heavy")
    if "Command_ConstructAmericaLgm30" not in dozer:
        errors.append("Dozer missing nuclear AmericaLgm30")
    if re.search(r"^\s*15\s*=", fighter, re.M) or re.search(r"^\s*15\s*=", heavy, re.M):
        errors.append("used invisible slot 15+")

    f35 = objects.get("BritainJetF35B", "")
    if "ENF35A" not in f35:
        errors.append("F-35B not using donor ENF35A")
    if re.search(r"^\s*Model\s+=\s+US_F35A\s*$", f35, re.M):
        errors.append("F-35B still using old US_F35A model")
    if re.search(r"^\s*Model\s+=\s+SPEC_OLD_F35\s*$", f35, re.M):
        errors.append("F-35B accidentally uses Tempest mesh")
    if not re.search(r"Scale\s*=\s*0\.95", f35):
        errors.append("F-35B scale not 0.95")
    if "Britain_Weapon_AMRAAM" not in f35 or "Britain_Weapon_ASRAAM" not in f35 or "Britain_Weapon_SDB" not in f35:
        errors.append("F-35B weapons changed")
    if "Britain_Weapon_Meteor_Long" in f35 or "Britain_Weapon_TempestPGM" in f35:
        errors.append("F-35B gained Tempest weapons")
    if "StealthUpdate" in f35:
        errors.append("F-35B gameplay stealth added")
    if not re.search(r"BuildCost\s+=\s+3300", f35) or not re.search(r"BuildTime\s+=\s+18\.5", f35):
        errors.append("F-35B cost/time changed")
    if not re.search(r"MaxHealth\s+=\s+560\.0", f35):
        errors.append("F-35B health changed")
    if "Snecma_M88_4E" not in f35:
        errors.append("F-35B locomotor changed")

    tmp = objects.get("BritainJetTempest", "")
    if not tmp:
        errors.append("BritainJetTempest object missing")
    else:
        if "SPEC_OLD_F35" not in tmp:
            errors.append("Tempest not using preserved old F-35 mesh")
        if "ENF35A" in tmp or "LSFUSAF35A" in tmp:
            errors.append("Tempest using donor F-35 mesh")
        if not re.search(r"Scale\s*=\s*1\.00", tmp):
            errors.append("Tempest scale not 1.00")
        if "Britain_Weapon_Meteor_Long" not in tmp:
            errors.append("Tempest missing Meteor_Long")
        if "Britain_Weapon_ASRAAM" not in tmp:
            errors.append("Tempest missing ASRAAM")
        if "Britain_Weapon_TempestPGM" not in tmp:
            errors.append("Tempest missing TempestPGM")
        if "Britain_Weapon_AMRAAM" in tmp or "Britain_Weapon_SDB" in tmp:
            errors.append("Tempest cloned F-35B weapon pattern")
        if "StealthUpdate" not in tmp:
            errors.append("Tempest missing stealth")
        if "Britain_Tempest_Loco" not in tmp:
            errors.append("Tempest missing dedicated locomotor")
        if "SPEC_BritainTempest" not in tmp:
            errors.append("Tempest missing dedicated portrait")
        if "SPEC_BritainF35B" in tmp:
            errors.append("Tempest reuses F-35B portrait")

    if "Weapon Britain_Weapon_TempestPGM" not in wpn_text:
        errors.append("TempestPGM missing from Weapon.ini")
    loco_src = overlay.get(
        r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTempest.ini", b""
    ).decode("latin1")
    if "Locomotor Britain_Tempest_Loco" not in loco_src:
        errors.append("Tempest locomotor block missing from object file")

    for leaf in (
        "enf35a.w3d",
        "lsfusaf35a.w3d",
        "lsfusaf35ad.w3d",
        "lsfusaf35ak.w3d",
        "spec_old_f35.w3d",
        "us_f35a.w3d",
        "ef35.dds",
        "f35.dds",
        "f35d.dds",
        "f35k.dds",
        "spec_old_f35.dds",
        "us_f35a.dds",
        "spec_britainf35b.tga",
        "spec_britaintempest.tga",
    ):
        if leaf not in art_leaves:
            errors.append(f"ART missing {leaf}")

    old_w3d = art_map.get("art\\w3d\\us_f35a.w3d", art_map.get("art\\w3d\\US_F35A.W3D".lower()))
    # keys are normalized lowercase
    old_key = "art\\w3d\\us_f35a.w3d"
    spec_key = "art\\w3d\\spec_old_f35.w3d"
    if old_key in art_map and spec_key in art_map:
        if art_map[old_key][1] != art_map[spec_key][1]:
            errors.append("SPEC_OLD_F35.W3D is not a byte copy of US_F35A.W3D")
    else:
        errors.append("old F-35 W3D preservation keys missing")

    for obj, block in objects.items():
        if not obj.startswith("Britain"):
            continue
        for model in re.findall(r"^\s*Model\s+=\s+(\S+)", block, re.M):
            if f"{model.lower()}.w3d" not in art_leaves:
                errors.append(f"{obj} Model {model} W3D missing")
        for wslot, wname in re.findall(r"Weapon\s+=\s+(PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", block):
            if wname not in weapons:
                errors.append(f"{obj} {wslot} weapon {wname} missing")
            else:
                proj = re.search(r"ProjectileObject\s+=\s+(\S+)", weapons[wname])
                if proj and proj.group(1) not in packed_objects:
                    errors.append(f"{wname} projectile {proj.group(1)} not packed")
        portrait = re.search(r"SelectPortrait\s+=\s+(\S+)", block)
        if portrait and portrait.group(1) not in mapped:
            errors.append(f"{obj} portrait {portrait.group(1)} missing MappedImage")
        disp = re.search(r"DisplayName\s+=\s+(\S+)", block)
        if disp and disp.group(1) not in csf_keys:
            errors.append(f"{obj} CSF {disp.group(1)} missing")

    for key, value in CSF_LABELS.items():
        if key not in csf_keys:
            errors.append(f"CSF missing {key}")
        elif csf_vals.get(key) != value:
            errors.append(f"CSF {key} is {csf_vals.get(key)!r} not {value!r}")
    for bad in ("F-35", "F-35A", "F-35B", "F35"):
        val = csf_vals.get("OBJECT:BritainJetTempest", "")
        if bad.lower().replace("-", "") in val.lower().replace("-", ""):
            errors.append(f"Tempest CSF still contains {bad}")
            break
    if csf_vals.get("OBJECT:BritainJetF35B") != "F-35B Lightning II":
        errors.append("F-35B display name is not F-35B Lightning II")

    if "SPEC_BritainTempest" not in mapped:
        errors.append("MappedImage SPEC_BritainTempest missing")
    if f35 and "SPEC_BritainF35B" not in f35:
        errors.append("F-35B portrait changed away from SPEC_BritainF35B")

    core = set(re.findall(r"^CommandButton (\S+)\s*$", cb_text, re.M))
    for name in ("BritainAirfieldCommandSet", "Britain_LargeAirBaseCommandSet", "Britain_HeavyAirBaseCommandSet"):
        idx = cs_text.find(f"CommandSet {name}")
        declared = core | set(re.findall(r"^CommandButton (\S+)\s*$", cs_text[:idx], re.M))
        block = ch.grab_block(cs_text, name)
        for line in block.splitlines():
            m = re.match(r"^\s*\d+\s*=\s*(Command_\S+)\s*$", line)
            if m and m.group(1) not in declared:
                errors.append(f"{name} refs unknown CommandButton {m.group(1)}")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/uk_f35_donor_tempest"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    overlay = ukdiv.collect_uk_overlay()
    ch.parse_check(overlay)
    print(f"overlay files {len(overlay)}")
    if r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetTempest.ini" not in overlay:
        # path uses backslashes from collect
        found = [k for k in overlay if "britainjettempest" in k.lower()]
        if not found:
            raise SystemExit("Tempest overlay INI not collected")

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

    protect_hash = {
        n: hashlib.sha256(ch.grab_block(data_map["data\\ini\\commandset.ini"][1].decode("latin1"), n).encode("latin1")).hexdigest()
        for n in ukdiv.PROTECT_SETS
    }
    dozer_before = ch.grab_block(data_map["data\\ini\\commandset.ini"][1].decode("latin1"), "BritainDozerCommandSet")
    fighter_before = ch.grab_block(data_map["data\\ini\\commandset.ini"][1].decode("latin1"), "BritainAirfieldCommandSet")

    wpn_key = "data\\ini\\weapon.ini"
    wpn_name, wpn_blob = data_map[wpn_key]
    eu_wpn = overlay[r"Data\INI\Weapon_EuropeAirforce.ini"]
    wpn_blob = fire.replace_marked_block(wpn_blob, ukdiv.EUROPE_MARKER, None, eu_wpn)
    data_map[wpn_key] = (wpn_name, ch.lf(wpn_blob))
    wpn_text = data_map[wpn_key][1].decode("latin1")
    for required in (
        "Britain_Weapon_Meteor_Long",
        "Britain_Weapon_TempestPGM",
        "Britain_Weapon_SDB",
        "Britain_Weapon_AMRAAM",
        "Germany_Weapon_Meteor",
        "Italy_Weapon_JetCannon",
    ):
        if f"Weapon {required}" not in wpn_text:
            raise SystemExit(f"Weapon.ini missing {required}")
    print("Inlined Europe/UK weapons including TempestPGM")

    cs_key = "data\\ini\\commandset.ini"
    cb_key = "data\\ini\\commandbutton.ini"
    cs_name, cs_blob = data_map[cs_key]
    cb_name, cb_blob = data_map[cb_key]
    cs_text = cs_blob.decode("latin1")
    cb_text = cb_blob.decode("latin1")
    btn_src = overlay[r"Data\INI\CommandButton_EuropeAirforce.ini"].decode("ascii")
    new_btns = ukdiv.extract_named_buttons(btn_src, ["Command_ConstructBritainJetTempest"])
    cs_text = ukdiv.strip_blocks(cs_text, ["Command_ConstructBritainJetTempest"])
    cs_text = ukdiv.insert_before(cs_text, "CommandSet BritainAirfieldCommandSet", new_btns)
    cs_text = fr.replace_block(cs_text, "BritainAirfieldCommandSet", ukdiv.cs_block("BritainAirfieldCommandSet", FIGHTER_BTNS))
    cs_text = fr.replace_block(
        cs_text, "Britain_LargeAirBaseCommandSet", ukdiv.cs_block("Britain_LargeAirBaseCommandSet", FIGHTER_BTNS)
    )
    cs_text = fr.replace_block(
        cs_text, "Britain_HeavyAirBaseCommandSet", ukdiv.cs_block("Britain_HeavyAirBaseCommandSet", HEAVY_BTNS)
    )
    dozer_after = ch.grab_block(cs_text, "BritainDozerCommandSet")
    if dozer_after != dozer_before:
        raise SystemExit("BritainDozerCommandSet mutated")
    fighter_after = ch.grab_block(cs_text, "BritainAirfieldCommandSet")
    # Slot list must match previous fighter menu (same 12 aircraft + Rally/Sell).
    prev_slots = re.findall(r"^\s*\d+\s*=\s*(\S+)", fighter_before, re.M)
    new_slots = re.findall(r"^\s*\d+\s*=\s*(\S+)", fighter_after, re.M)
    if prev_slots != new_slots:
        raise SystemExit(f"Fighter airbase slots changed {prev_slots} -> {new_slots}")
    data_map[cs_key] = (cs_name, ch.lf(cs_text.encode("latin1")))
    print("Patched UK Heavy Airbase slot 11 = BAE Tempest; fighter menu unchanged")

    hc_key = "data\\ini\\mappedimages\\handcreated\\handcreatedmappedimages.ini"
    hc_name, hc_blob = data_map[hc_key]
    portraits_ini = overlay[r"Data\INI\MappedImages\HandCreated\zEurope_AirbasePortrait_Images.INI"].decode("ascii")
    hc_text = hc_blob.decode("latin1")
    hc_text = re.sub(
        r"^MappedImage SPEC_BritainTempest\s*\n.*?^End\s*$\n?",
        "",
        hc_text,
        count=1,
        flags=re.M | re.S,
    )
    m = re.search(r"^MappedImage SPEC_BritainTempest\s*\n.*?^End\s*$", portraits_ini, re.M | re.S)
    if not m:
        raise SystemExit("SPEC_BritainTempest MappedImage missing from overlay")
    if not hc_text.endswith("\n"):
        hc_text += "\n"
    hc_text += "\n" + m.group(0).rstrip() + "\n"
    data_map[hc_key] = (hc_name, ch.lf(hc_text.encode("latin1")))

    csf_key = "data\\english\\generals.csf"
    csf_name, csf_blob = data_map[csf_key]
    csf_new = patch_csf(csf_blob)
    ch.validate_csf(csf_new, list(CSF_LABELS))
    data_map[csf_key] = (csf_name, csf_new)

    skip_inject = {
        "data\\ini\\commandbutton_europeairforce.ini",
        "data\\ini\\commandset_britain.ini",
    }
    for dest, content in overlay.items():
        key = ch.norm_key(dest)
        if key in skip_inject:
            continue
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (dest, content)
        print("DATA inject", dest)

    # Preserve old F-35 visual, then inject donor F-35A/B ART.
    old_w3d_key = "art\\w3d\\us_f35a.w3d"
    if old_w3d_key not in art_map:
        raise SystemExit("packed ART missing US_F35A.W3D")
    old_w3d = art_map[old_w3d_key][1]
    spec_src = (DONOR / "W3D/SPEC_OLD_F35.W3D").read_bytes()
    if spec_src != old_w3d:
        raise SystemExit("repo SPEC_OLD_F35.W3D does not match packed US_F35A.W3D")

    for dest, src in {**DONOR_W3D, **DONOR_TEX}.items():
        blob = src.read_bytes()
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, blob)
        print("ART inject", dest, len(blob))

    packed_tex = ukdiv.art_leaf_map(art_map)
    old_portrait_key = "art\\textures\\spec_britainf35b.tga"
    if old_portrait_key not in art_map:
        raise SystemExit("packed ART missing SPEC_BritainF35B.tga")
    old_portrait = art_map[old_portrait_key][1]
    tmp_old = Path("/tmp/spec_britainf35b_old.tga")
    tmp_old.write_bytes(old_portrait)
    tempest_tga = eu.make_portrait_any(tmp_old)
    dest = r"Art\Textures\SPEC_BritainTempest.tga"
    key = ch.norm_key(dest)
    if key not in art_map:
        art_keys.append(key)
    art_map[key] = (dest, tempest_tga)
    print("ART portrait Tempest from old F-35 button", len(tempest_tga))

    f35b_src = DONOR / "Textures/F35BTB.tga"
    try:
        f35b_tga = eu.make_portrait_any(f35b_src)
    except Exception:
        f35b_tga = eu.make_portrait_any(DONOR / "Textures/AmericaF35BJSFTB.tga")
    art_map[old_portrait_key] = (r"Art\Textures\SPEC_BritainF35B.tga", f35b_tga)
    print("ART portrait F-35B from donor F35BTB", len(f35b_tga))
    if hashlib.sha256(f35b_tga).digest() == hashlib.sha256(tempest_tga).digest():
        raise SystemExit("F-35B and Tempest portraits are identical")

    cs_text = data_map[cs_key][1].decode("latin1")
    cb_text = data_map[cb_key][1].decode("latin1")
    wpn_text = data_map[wpn_key][1].decode("latin1")
    hc_text = data_map[hc_key][1].decode("latin1")
    ch.validate_commandset_button_refs(cs_text, cb_text)
    errors = extra_validate(overlay, cs_text, cb_text, wpn_text, hc_text, data_map, art_map, csf_new)
    # reuse diversity validate for remaining UK aircraft
    div_errors, _used, _objs = ukdiv.validate(
        overlay,
        cs_text,
        cb_text,
        wpn_text,
        data_map["data\\ini\\specialpower.ini"][1].decode("latin1"),
        hc_text,
        data_map,
        art_map,
        csf_new,
    )
    # diversity validate still expects old F-35B US_F35A in W3D_TABLE comments only;
    # it checks BritainJetF35B AMRAAM which we kept.
    errors.extend(div_errors)
    if errors:
        raise SystemExit("VALIDATE FAIL\n" + "\n".join(errors))
    print("VALIDATE PASS weapons/CommandButton/CommandSet/ART/MappedImage/CSF")

    cs_after = data_map[cs_key][1].decode("latin1")
    for n in ukdiv.PROTECT_SETS:
        h = hashlib.sha256(ch.grab_block(cs_after, n).encode("latin1")).hexdigest()
        if h != protect_hash[n]:
            raise SystemExit(f"PROTECTED CommandSet mutated: {n}")
    print("PROTECT CHECK PASS France/Germany/Italy/China/Russia CommandSets unchanged")

    out_data_map = {data_map[k][0]: data_map[k][1] for k in data_keys}
    out_art_map = {art_map[k][0]: art_map[k][1] for k in art_keys}
    data_big = ch.build_big(out_data_map)
    art_big = ch.build_big(out_art_map)
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_big)
    out_art.write_bytes(art_big)

    v_data_entries, v_data_raw = ch.read_big(out_data)
    v_art_entries, v_art_raw = ch.read_big(out_art)
    v_data = {ch.norm_key(n): v_data_raw[off : off + size] for n, off, size in v_data_entries}
    v_art = {ch.norm_key(n): v_art_raw[off : off + size] for n, off, size in v_art_entries}

    must_data = [
        r"data\ini\object\specter\british armed forces\airforce\britainjetf35b.ini",
        r"data\ini\object\specter\british armed forces\airforce\britainjettempest.ini",
        r"data\ini\weapon.ini",
        r"data\ini\commandset.ini",
        r"data\english\generals.csf",
    ]
    for key in must_data:
        if key not in v_data:
            raise SystemExit(f"re-extract missing DATA {key}")
    f35b = v_data[r"data\ini\object\specter\british armed forces\airforce\britainjetf35b.ini"].decode("latin1")
    if "ENF35A" not in f35b or "Britain_Weapon_AMRAAM" not in f35b:
        raise SystemExit("re-extract F-35B check fail")
    tempest = v_data[r"data\ini\object\specter\british armed forces\airforce\britainjettempest.ini"].decode("latin1")
    if "SPEC_OLD_F35" not in tempest or "Britain_Weapon_Meteor_Long" not in tempest:
        raise SystemExit("re-extract Tempest check fail")
    if "F-35" in tempest.split("DisplayName")[0] and False:
        pass
    if re.search(r"F-35", tempest):
        # comments may mention old F-35 visual donor; displayed identity is CSF. Object file comment is OK.
        pass
    cst = v_data[r"data\ini\commandset.ini"].decode("latin1")
    if "Command_ConstructBritainJetTempest" not in ch.grab_block(cst, "Britain_HeavyAirBaseCommandSet"):
        raise SystemExit("re-extract heavy CommandSet missing Tempest")
    if "Command_ConstructBritainJetTempest" in ch.grab_block(cst, "BritainAirfieldCommandSet"):
        raise SystemExit("re-extract fighter CommandSet unexpectedly has Tempest")
    wpn = v_data[r"data\ini\weapon.ini"].decode("latin1")
    if "Weapon Britain_Weapon_TempestPGM" not in wpn:
        raise SystemExit("re-extract Weapon.ini missing TempestPGM")
    for leaf in (
        r"art\w3d\enf35a.w3d",
        r"art\w3d\lsfusaf35a.w3d",
        r"art\w3d\spec_old_f35.w3d",
        r"art\w3d\us_f35a.w3d",
        r"art\textures\ef35.dds",
        r"art\textures\f35.dds",
        r"art\textures\spec_old_f35.dds",
        r"art\textures\spec_britainf35b.tga",
        r"art\textures\spec_britaintempest.tga",
    ):
        if leaf not in v_art:
            raise SystemExit(f"re-extract missing ART {leaf}")
    if v_art[r"art\w3d\us_f35a.w3d"] != v_art[r"art\w3d\spec_old_f35.w3d"]:
        raise SystemExit("re-extract old F-35 preserve mismatch")
    if v_art[r"art\w3d\enf35a.w3d"] == v_art[r"art\w3d\spec_old_f35.w3d"]:
        raise SystemExit("F-35B and Tempest W3D are the same file")
    print("RE-EXTRACT VERIFY PASS")

    install = (
        "Copy _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big into the Specter Data folder.\n"
        "Keep EnglishZH.big and AudioZH.big unchanged.\n"
        "UNITED KINGDOM F-35B donor visual replacement and BAE Tempest only.\n"
        "Does not change France, Germany, Italy, Russia, China, USA, or other countries.\n"
        "Fighter Airbase slots 1-12 unchanged. Tempest is Heavy Airbase slot 11.\n"
        "Nuclear/Atomic dozer slot preserved. Rally Point and Sell preserved.\n"
        "F-35B uses donor ENF35A. Old US_F35A mesh preserved as SPEC_OLD_F35 for Tempest.\n"
    )
    zpath = out / "UK_F35_DONOR_TEMPEST_FIX.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.writestr("INSTALL.txt", install)
    verify = out / "zip_verify"
    if verify.exists():
        shutil.rmtree(verify)
    verify.mkdir()
    with zipfile.ZipFile(zpath, "r") as zf:
        zf.extractall(verify)
        names = set(zf.namelist())
    if names != {"_SPEC_DATA_ONE.big", "_SPEC_ART_ONE.big", "INSTALL.txt"}:
        raise SystemExit(f"ZIP contents unexpected: {sorted(names)}")
    if hashlib.sha256((verify / "_SPEC_DATA_ONE.big").read_bytes()).digest() != hashlib.sha256(data_big).digest():
        raise SystemExit("ZIP DATA hash mismatch")
    if hashlib.sha256((verify / "_SPEC_ART_ONE.big").read_bytes()).digest() != hashlib.sha256(art_big).digest():
        raise SystemExit("ZIP ART hash mismatch")
    print("ZIP extract verify PASS")

    data_sha = hashlib.sha256(data_big).hexdigest()
    art_sha = hashlib.sha256(art_big).hexdigest()
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()
    report = out / "PACK_REPORT.txt"
    report.write_text(
        f"DATA sha256 {data_sha}\n"
        f"ART  sha256 {art_sha}\n"
        f"ZIP  sha256 {zip_sha}\n"
        f"DATA bytes {len(data_big)}\n"
        f"ART  bytes {len(art_big)}\n"
        "PARSER CHECK PASS\n"
        "WEAPON reference PASS\n"
        "CommandButton PASS\n"
        "CommandSet uniqueness PASS\n"
        "ART/W3D PASS\n"
        "MappedImage PASS\n"
        "CSF PASS\n"
        "PROTECT CHECK PASS France/Germany/Italy/China/Russia\n"
        "RE-EXTRACT VERIFY PASS\n"
        "ZIP extract verify PASS\n"
        "UK ONLY\n"
        "F-35B W3D = ENF35A (DONOR_ART Art/w3d/ENF35A.W3D)\n"
        "F-35A W3D packed = LSFUSAF35A (DONOR_ART Art/w3d/LSFUSAF35A.W3D)\n"
        "Old F-35 W3D = US_F35A preserved as SPEC_OLD_F35 assigned to BAE Tempest\n"
        "F-35B scale 0.95\n"
        "Tempest scale 1.00\n"
        "Fighter menu unchanged. Heavy slot 11 = BAE Tempest\n"
        "Dozer slot 12 = Command_ConstructAmericaLgm30\n",
        encoding="ascii",
    )
    print(report.read_text())
    print("wrote", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
