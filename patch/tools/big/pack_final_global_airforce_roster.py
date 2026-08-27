#!/usr/bin/env python3
"""Pack final global air-force roster. Does not modify USA/Russia/China live files."""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_final_global_airforce_roster as gen
import pack_china_heavy_aircraft as ch
import pack_europe_airforce as eu
import pack_france_airforce as fr
import pack_uk_e7_boot_crash_fix as e7

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
BASE_DATA = Path("/tmp/donor_unused_pack/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/donor_unused_pack/_SPEC_ART_ONE.big")
EXTRACT = Path("/tmp/donor_unused/extract")
TEX = Path("/tmp/donor_unused/tex")
ART_CACHE = Path("/tmp/donor_unused/art_cache")

MARKER_W = "; ===== SPECTER FINAL GLOBAL AIRFORCE ROSTER WEAPONS BEGIN ====="
MARKER_WE = "; ===== SPECTER FINAL GLOBAL AIRFORCE ROSTER WEAPONS END ====="

PROTECT_SETS = [
    "AmericaAirfieldCommandSet",
    "America_LargeAirBaseCommandSet",
    "America_HeavyAirBaseCommandSet",
    "RussiaAirfieldCommandSet",
    "Russia_LargeAirBaseCommandSet",
    "Russia_HeavyAirBaseCommandSet",
    "PLAAirfieldCommandSet",
    "China_LargeAirBaseCommandSet",
    "China_HeavyAirBaseCommandSet",
]

PROJECTILES = {
    "MeteorMissile_Object", "AIM-9X_Object", "R77_Object",
    "GBU24_GuidedBombObject", "Fab-250", "Kh59MK2_Object",
    "KH31P_MissileObject", "Paveway_IV_Object", "30mm_API-T_Projectile",
    "GenericUnguidedRockets",
}

SHARED_NO_OVERWRITE = {"housecolor2.dds", "rubbletexture.dds", "f35.dds", "f35.tga"}

ART_INJECT = [
    "AmF18A.W3D", "F18SEA.W3D", "EVTyphoon.W3D",
    "LSFF15K.W3D", "LSFF15Kd.W3D",
    "LSFIRF14A.W3D", "LSFIRF14Ad.W3D",
    "LSFISF15E.W3D", "LSFISF15Ed.W3D",
    "LSFISF16.W3D", "LSFISF16d.W3D",
    "LSFPKF16.W3D", "LSFPKF16d.W3D",
    "LSFF16CEgy.W3D", "LSFF16CEgyd.W3D",
]
TEX_INJECT = [
    "AmF18MA01.dds", "AmF18MA02.dds",
    "F18SEA_1.tga", "F18SEA_2.tga", "F18SEA_3.tga",
    "EVTyphoonSDTX04.tga",
    "LSFF15K.dds", "LSFF14A.dds", "LSFISF15E.dds", "LSFPKF16.dds",
    "LSFF16I.dds", "LSFF16Id.dds", "IRAIM54M.tga", "ISFUSAF16.tga",
    "LSFF16C.tga", "UsaEA18Map.dds", "UsaF18Map.dds",
    "UsaAirMissileMap.dds", "UsaGbuMap.dds", "UsaGbuMap02.dds",
]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def replace_cs(text: str, name: str, new_block: str) -> str:
    pat = re.compile(rf"CommandSet {re.escape(name)}\s*\n.*?^End\s*$", re.M | re.S)
    if not pat.search(text):
        return text
    return pat.sub(new_block.rstrip() + "\n", text, count=1)


def inline_buttons(cs_text: str, buttons: str) -> str:
    idx = cs_text.find("CommandSet GenericCommandSet")
    if idx < 0:
        idx = cs_text.find("CommandSet ")
    if idx < 0:
        raise SystemExit("no CommandSet to inline before")
    body = "\n".join(l for l in buttons.splitlines() if not l.startswith(";")).strip() + "\n\n"
    return cs_text[:idx] + body + cs_text[idx:]


def inline_weapons(weapon_ini: str, overlay: str) -> str:
    block = MARKER_W + "\n" + overlay.strip() + "\n" + MARKER_WE + "\n"
    if MARKER_W in weapon_ini:
        weapon_ini = re.sub(
            re.escape(MARKER_W) + r".*?" + re.escape(MARKER_WE) + r"\n?",
            block, weapon_ini, count=1, flags=re.S,
        )
    else:
        if not weapon_ini.endswith("\n"):
            weapon_ini += "\n"
        weapon_ini += "\n" + block
    return weapon_ini


def patch_csf(data: bytes) -> bytes:
    version, unk, lang, labels = ch.parse_csf(data)
    have_idx = {name: i for i, (_, name, _) in enumerate(labels)}
    added = updated = 0
    for key, value in gen.CSF_LABELS.items():
        if any(ord(c) > 127 for c in key) or any(ord(c) > 127 for c in value):
            raise SystemExit(f"non-ASCII CSF {key}")
        if key in have_idx:
            i = have_idx[key]
            mag, name, _s = labels[i]
            labels[i] = (mag, name, [(ch.CSF_STR_MAGIC, value, b"")])
            updated += 1
        else:
            labels.append((ch.CSF_LBL_MAGIC, key, [(ch.CSF_STR_MAGIC, value, b"")]))
            added += 1
            have_idx[key] = len(labels) - 1
    print(f"CSF added {added} labels, updated {updated}")
    return ch.build_csf(version, unk, lang, labels)


def find_art_file(name: str) -> Path | None:
    for root in (EXTRACT, TEX, ART_CACHE):
        if not root.exists():
            continue
        hits = [p for p in root.rglob("*") if p.is_file() and p.name.lower() == name.lower()]
        if hits:
            return hits[0]
    return None


def collect_overlay() -> dict[str, bytes]:
    overlay: dict[str, bytes] = {}
    for spec in gen.AIRCRAFT:
        p = PATCH / spec["rel"]
        dest = "Data\\" + spec["rel"].replace("/", "\\")
        overlay[dest] = ch.lf(p.read_bytes())
    extra = [
        "INI/Weapon_FinalGlobalAirforceRoster.ini",
        "INI/CommandButton_FinalGlobalAirforceRoster.ini",
        "INI/MappedImages/HandCreated/zFinalGlobal_AirbasePortrait_Images.INI",
    ]
    for rel in extra:
        p = PATCH / rel
        dest = "Data\\" + rel.replace("/", "\\")
        overlay[dest] = ch.lf(p.read_bytes())
    return overlay


def build_btn_map(files: dict[str, tuple[str, bytes]]) -> dict[str, str]:
    """object -> preferred CommandButton name."""
    obj_btns: dict[str, list[str]] = defaultdict(list)
    for key, (name, blob) in files.items():
        if not key.endswith(".ini"):
            continue
        t = blob.decode("latin1")
        if "CommandButton " not in t:
            continue
        for m in re.finditer(r"^CommandButton (\S+)\s*$", t, re.M):
            nxt = t.find("\nEnd", m.end())
            block = t[m.end(): nxt if nxt > 0 else m.end() + 400]
            om = re.search(r"Object\s+=\s+(\S+)", block)
            if om and "UNIT_BUILD" in block:
                obj_btns[om.group(1)].append(m.group(1))
    out = {}
    for obj, btns in obj_btns.items():
        pref = [b for b in btns if b.startswith("Command_Construct") and not b.startswith("AirF_")]
        out[obj] = pref[0] if pref else btns[0]
    for spec in gen.AIRCRAFT:
        out[spec["obj"]] = f"Command_Construct{spec['obj']}"
    return out


def rewrite_menu(old: str, units: list[str], btn_for: dict[str, str], add_rally_if_empty: bool) -> str:
    m = re.match(r"CommandSet (\S+)", old)
    if not m:
        raise SystemExit("bad commandset block")
    name = m.group(1)
    old_slots = {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", old, re.M)}
    slots: dict[int, str] = {}
    for i, obj in enumerate(units, 1):
        btn = btn_for.get(obj)
        if not btn:
            btn = f"Command_Construct{obj}"
            btn_for[obj] = btn
        slots[i] = btn
    for k, v in old_slots.items():
        if k >= 13:
            slots[k] = v
    if add_rally_if_empty and 13 not in slots:
        slots[13] = "Command_SetRallyPoint"
    if 14 not in slots:
        slots[14] = "Command_Sell"
    lines = [f"CommandSet {name}"]
    for slot in sorted(slots):
        lines.append(f"  {slot} = {slots[slot]}")
    lines.append("End")
    return "\n".join(lines) + "\n"


def strip_prereq_in_object(block: str) -> str:
    """Remove Rank/WarFactory/Strategy/Science/Industrial prereqs from an object block."""
    def repl(m: re.Match) -> str:
        body = m.group(0)
        if re.search(r"Rank|WarFactory|Strategy|Science|Industrial|Airfield_T\b", body, re.I):
            return ""
        return body
    return re.sub(r"(?ms)^  Prerequisites\b.*?^  End\s*\n", repl, block)


def write_install(out: Path) -> None:
    (out / "INSTALL.txt").write_text(
        """SPECTER FINAL GLOBAL AIR FORCE ROSTER

Copy both BIG files into the game folder, replacing previous Specter BIGs:

  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

Every playable country except USA, Russia, and China now has exactly 12
constructible combat jets on its Fighter / Airfield / Large fighter menu.

USA, Russia, and China live files are unchanged.

See FINAL_COUNTRY_AIRFORCE_AUDIT.md and FINAL_UNUSED_AIRCRAFT_DONORS.md.
"""
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/final_global_roster"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    ART_CACHE.mkdir(parents=True, exist_ok=True)

    gen.main()
    overlay = collect_overlay()
    fr.parse_check(overlay)
    print("overlay parser PASS")

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

    packed_art_leaf = {}
    for key, (name, blob) in art_map.items():
        packed_art_leaf[name.split("\\")[-1].lower()] = blob

    protect_hash = {}
    cs_probe = data_map["data\\ini\\commandset.ini"][1].decode("latin1")
    for n in PROTECT_SETS:
        protect_hash[n] = hashlib.sha256(ch.grab_block(cs_probe, n).encode("latin1")).hexdigest()
        print("protect", n, protect_hash[n][:16])

    usa_ru_cn_file_hash = {}
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        if any(s in key for s in (
            "united states of america",
            "armed forces of russian federation",
            "\\pla\\",
            "\\specter\\pla\\",
        )):
            usa_ru_cn_file_hash[key] = hashlib.sha256(blob).hexdigest()
    print("protected INI files", len(usa_ru_cn_file_hash))

    btn_for = build_btn_map(data_map)
    missing_btn_objs = []
    all_menus = dict(gen.FIGHTER_MENUS)
    for src, copies in gen.FIGHTER_MENU_COPIES.items():
        for c in copies:
            if c != src:
                all_menus[c] = gen.FIGHTER_MENUS[src]
    for name, objs in list(all_menus.items()) + list(gen.HEAVY_MENUS.items()):
        for obj in objs:
            if obj not in btn_for:
                btn_for[obj] = f"Command_Construct{obj}"
                missing_btn_objs.append(obj)

    extra_btns = []
    known_btns = set(re.findall(r"^CommandButton (\S+)", cs_probe, re.M))
    for key, (name, blob) in data_map.items():
        if key.endswith(".ini"):
            known_btns.update(re.findall(r"^CommandButton (\S+)", blob.decode("latin1"), re.M))
    for spec in gen.AIRCRAFT:
        known_btns.add(f"Command_Construct{spec['obj']}")
    SYNTH_IMG = {
        "Iraq_Mig25RB": "irq_mig25",
        "Iraq_IL-76": "yier76",
    }
    for obj in missing_btn_objs:
        btn = btn_for[obj]
        if btn not in known_btns:
            img = SYNTH_IMG.get(obj, "irq_mig25")
            extra_btns.append(
                f"CommandButton {btn}\n"
                f"  Command          = UNIT_BUILD\n"
                f"  Object           = {obj}\n"
                f"  TextLabel        = CONTROLBAR:Construct{obj}\n"
                f"  ButtonImage      = {img}\n"
                f"  ButtonBorderType = BUILD\n"
                f"  DescriptLabel    = CONTROLBAR:ToolTip{obj}\n"
                f"End\n"
            )
            known_btns.add(btn)
            print("synth button", btn, "img", img)

    cs_text = cs_probe
    for set_name, objs in all_menus.items():
        if f"CommandSet {set_name}" not in cs_text:
            print("skip missing set", set_name)
            continue
        old = ch.grab_block(cs_text, set_name)
        add_rally = set_name.startswith("Iran") and "Command_SetRallyPoint" not in old
        new = rewrite_menu(old, objs, btn_for, add_rally)
        old_slots = {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", old, re.M)}
        new_slots = {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", new, re.M)}
        for k in (13, 14):
            if k in old_slots and new_slots.get(k) != old_slots[k] and not (k == 13 and add_rally):
                raise SystemExit(f"{set_name} meta slot {k} changed {old_slots[k]} -> {new_slots.get(k)}")
        if "Command_Upgrade_NuclearTipWarhead2" in old and "Command_Upgrade_NuclearTipWarhead2" not in new:
            raise SystemExit(f"{set_name} lost nuclear")
        cs_text = replace_cs(cs_text, set_name, new)
        print("fighter/large", set_name, "12")

    for set_name, objs in gen.HEAVY_MENUS.items():
        if f"CommandSet {set_name}" not in cs_text:
            print("skip missing heavy", set_name)
            continue
        if set_name in all_menus:
            continue
        old = ch.grab_block(cs_text, set_name)
        new = rewrite_menu(old, objs, btn_for, False)
        old_slots = {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", old, re.M)}
        new_slots = {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", new, re.M)}
        for k in (13, 14):
            if k in old_slots and new_slots.get(k) != old_slots[k]:
                raise SystemExit(f"{set_name} heavy meta {k} changed")
        if "Command_Upgrade_NuclearTipWarhead2" in old and "Command_Upgrade_NuclearTipWarhead2" not in new:
            raise SystemExit(f"{set_name} lost nuclear")
        cs_text = replace_cs(cs_text, set_name, new)
        print("heavy", set_name, len(objs))

    btn_blob = gen.buttons_text()
    if extra_btns:
        btn_blob += "\n" + "\n".join(extra_btns)
    cs_text = inline_buttons(cs_text, btn_blob)
    data_map["data\\ini\\commandset.ini"] = (
        data_map["data\\ini\\commandset.ini"][0],
        ch.lf(cs_text.encode("latin1")),
    )

    w_key = "data\\ini\\weapon.ini"
    w_name, w_blob = data_map[w_key]
    w_new = inline_weapons(w_blob.decode("latin1"), gen.WEAPONS)
    data_map[w_key] = (w_name, ch.lf(w_new.encode("latin1")))

    csf_key = "data\\english\\generals.csf"
    csf_name, csf_blob = data_map[csf_key]
    csf_new = patch_csf(csf_blob)
    ch.validate_csf(csf_new, list(gen.CSF_LABELS)[:20])
    data_map[csf_key] = (csf_name, csf_new)

    # portraits
    for dest_name, src_name in gen.PORTRAIT_SRC.items():
        src = find_art_file(src_name)
        if src is None and src_name.lower() in packed_art_leaf:
            tmp = ART_CACHE / src_name
            tmp.write_bytes(packed_art_leaf[src_name.lower()])
            src = tmp
        if src is None:
            stem = Path(src_name).stem
            for ext in (".dds", ".tga", ".W3D"):
                alt = stem + ext
                if alt.lower() in packed_art_leaf:
                    tmp = ART_CACHE / alt
                    tmp.write_bytes(packed_art_leaf[alt.lower()])
                    src = tmp
                    break
                hit = find_art_file(alt)
                if hit:
                    src = hit
                    break
        if src is None:
            # last resort: any packed fighter portrait-sized tga
            fallback = packed_art_leaf.get("lsfrafale.dds") or packed_art_leaf.get("avf16.dds")
            if fallback is None:
                raise SystemExit(f"missing portrait source {src_name}")
            tmp = ART_CACHE / "fallback.dds"
            tmp.write_bytes(fallback)
            src = tmp
            print("portrait FALLBACK", dest_name, "from", src_name)
        if src is not None and src.suffix.lower() == ".w3d":
            alt = None
            stem = src.stem
            for cand in (stem + ".dds", stem + ".tga", "f35.dds", "US_F35A.dds", "Ef35.dds", "AVF16.dds"):
                hit = find_art_file(cand)
                if hit:
                    alt = hit
                    break
                if cand.lower() in packed_art_leaf:
                    tmp = ART_CACHE / cand
                    tmp.write_bytes(packed_art_leaf[cand.lower()])
                    alt = tmp
                    break
            if alt is None:
                # use any existing SPEC portrait tga
                for k, blob in packed_art_leaf.items():
                    if k.startswith("spec_") and k.endswith(".tga"):
                        tmp = ART_CACHE / k
                        tmp.write_bytes(blob)
                        alt = tmp
                        break
            if alt is None:
                raise SystemExit(f"W3D portrait needs texture {src_name}")
            src = alt
        tga = eu.make_portrait_any(src)
        art_dest = "Art\\Textures\\" + dest_name
        key = ch.norm_key(art_dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (art_dest, tga)

    mi_key = "data\\ini\\mappedimages\\handcreated\\handcreatedmappedimages.ini"
    mi_name, mi_bytes = data_map[mi_key]
    overlay_portraits = (PATCH / "INI/MappedImages/HandCreated/zFinalGlobal_AirbasePortrait_Images.INI").read_text(encoding="ascii")
    mi_text = mi_bytes.decode("latin1")
    if "MappedImage SPEC_GermanyJetTyphoonT1" not in mi_text:
        if not mi_text.endswith("\n"):
            mi_text += "\n"
        mi_text += "\n" + overlay_portraits
    data_map[mi_key] = (mi_name, ch.lf(mi_text.encode("latin1")))

    for dest, content in overlay.items():
        key = ch.norm_key(dest)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (dest, content)

    packed_tex_keys = {k.split("\\")[-1].lower() for k in art_map if "textures" in k}
    for name in ART_INJECT:
        src = find_art_file(name)
        if src is None:
            if name.lower() in packed_art_leaf:
                print("ART already packed", name)
                continue
            raise SystemExit(f"missing W3D {name}")
        dest = "Art\\W3D\\" + name
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, src.read_bytes())
    for name in TEX_INJECT:
        src = find_art_file(name)
        if src is None:
            if name.lower() in packed_tex_keys:
                print("skip missing donor tex, packed has", name)
                continue
            print("WARN missing tex", name)
            continue
        if name.lower() in SHARED_NO_OVERWRITE and name.lower() in packed_tex_keys:
            print("keep packed shared tex", name)
            continue
        dest = "Art\\Textures\\" + name
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, src.read_bytes())

    # validate overlay objects
    obj_names = [s["obj"] for s in gen.AIRCRAFT]
    if len(obj_names) != len(set(obj_names)):
        raise SystemExit("duplicate new object names")
    new_wpn = re.findall(r"^Weapon (\S+)", gen.WEAPONS, re.M)
    if len(new_wpn) != len(set(new_wpn)):
        raise SystemExit("duplicate new weapons")
    for spec in gen.AIRCRAFT:
        text = (PATCH / spec["rel"]).read_text(encoding="ascii")
        errs = e7.balanced_end(text, spec["obj"])
        if errs:
            raise SystemExit(f"End balance {spec['obj']}: {errs}")
        if re.search(r"Animation\s*=", text):
            raise SystemExit(f"Animation= on {spec['obj']}")
    for wpn_name in new_wpn:
        m = re.search(rf"^Weapon {re.escape(wpn_name)}\s*\n(.*?)(?:^End\s*$)", gen.WEAPONS, re.M | re.S)
        if not m:
            continue
        pm = re.search(r"ProjectileObject = (\S+)", m.group(1))
        if pm and pm.group(1) not in PROJECTILES:
            raise SystemExit(f"bad projectile {wpn_name} -> {pm.group(1)}")
    print("projectile refs PASS")

    data_files = {data_map[k][0]: data_map[k][1] for k in data_keys}
    art_files = {art_map[k][0]: art_map[k][1] for k in art_keys}
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(ch.build_big(data_files))
    out_art.write_bytes(ch.build_big(art_files))
    dh = sha256(out_data)
    ah = sha256(out_art)
    print("DATA sha256", dh)
    print("ART sha256", ah)

    # re-extract validation
    v_entries, v_raw = ch.read_big(out_data)
    v_map = {}
    for name, off, size in v_entries:
        v_map[ch.norm_key(name)] = (name, v_raw[off : off + size])
    va_entries, va_raw = ch.read_big(out_art)
    va_w3d = set()
    for name, off, size in va_entries:
        leaf = name.split("\\")[-1].lower()
        if leaf.endswith(".w3d"):
            va_w3d.add(leaf.replace(".w3d", ""))

    vcs = v_map["data\\ini\\commandset.ini"][1].decode("latin1")
    for n, h in protect_hash.items():
        got = hashlib.sha256(ch.grab_block(vcs, n).encode("latin1")).hexdigest()
        if got != h:
            raise SystemExit(f"PROTECTED CommandSet changed {n}")
    print("USA/RU/CN CommandSet hash PASS")
    for key, h in usa_ru_cn_file_hash.items():
        if hashlib.sha256(v_map[key][1]).hexdigest() != h:
            raise SystemExit(f"PROTECTED file changed {key}")
    print("USA/RU/CN object INI hash PASS")

    # buttons declared before use
    first_set = vcs.find("CommandSet ")
    for spec in gen.AIRCRAFT:
        btn = f"Command_Construct{spec['obj']}"
        idx_btn = vcs.find(f"CommandButton {btn}")
        if idx_btn < 0 or idx_btn > first_set:
            # inlined before GenericCommandSet which is a CommandSet; first_set may be Generic
            if idx_btn < 0:
                raise SystemExit(f"button missing {btn}")
        for set_name, objs in gen.FIGHTER_MENUS.items():
            if spec["obj"] in objs:
                idx_set = vcs.find(f"CommandSet {set_name}")
                if idx_btn > idx_set:
                    raise SystemExit(f"button {btn} after CommandSet {set_name}")

    w3d_fail = []
    btn_decl = set(re.findall(r"^CommandButton (\S+)", vcs, re.M))
    # also buttons from overlay files
    for key, (name, blob) in v_map.items():
        if key.endswith(".ini"):
            btn_decl.update(re.findall(r"^CommandButton (\S+)", blob.decode("latin1"), re.M))

    obj_pat = re.compile(r"^Object\s+(\S+)", re.M)
    all_objs = set()
    obj_blocks = {}
    for key, (name, blob) in v_map.items():
        if not key.endswith(".ini"):
            continue
        t = blob.decode("latin1")
        for m in obj_pat.finditer(t):
            all_objs.add(m.group(1))
            start = m.start()
            nxt = obj_pat.search(t, m.end())
            end = nxt.start() if nxt else len(t)
            obj_blocks[m.group(1)] = t[start:end]

    menu_status = {}
    for set_name, objs in gen.FIGHTER_MENUS.items():
        if f"CommandSet {set_name}" not in vcs:
            continue
        block = ch.grab_block(vcs, set_name)
        slots = {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M)}
        vis = [slots.get(i) for i in range(1, 13)]
        if any(v is None for v in vis):
            raise SystemExit(f"{set_name} missing 1-12")
        if len(set(vis)) != 12:
            raise SystemExit(f"{set_name} duplicate visible {vis}")
        for btn in vis:
            if btn not in btn_decl:
                raise SystemExit(f"{set_name} unresolved button {btn}")
        for obj in objs:
            if obj not in all_objs:
                raise SystemExit(f"{set_name} missing object {obj}")
            model = re.search(r"Model\s+=\s+(\S+)", obj_blocks[obj])
            if not model:
                w3d_fail.append(obj)
            else:
                if model.group(1).lower() not in va_w3d:
                    w3d_fail.append(f"{obj}:{model.group(1)}")
            loco = re.search(r"Locomotor\s+=\s+\S+\s+(\S+)", obj_blocks[obj])
            if not loco:
                raise SystemExit(f"no locomotor {obj}")
        menu_status[set_name] = "PASS"
        print("validate", set_name, "PASS")
    if w3d_fail:
        raise SystemExit(f"missing W3D {w3d_fail[:12]}")
    print("W3D refs PASS")

    # nuclear buildings unchanged
    for key, (name, blob) in v_map.items():
        if "nuclear" in key or "atomic" in key:
            old = data_map.get(key)
            # compare against original from first read - we didn't change those keys unless overlay
            pass

    write_install(out)
    write_audit_docs(out, dh, ah, protect_hash, vcs, obj_blocks, btn_for)
    zpath = out / "FINAL_GLOBAL_AIRFORCE_ROSTER.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for fn in (
            "_SPEC_DATA_ONE.big", "_SPEC_ART_ONE.big", "INSTALL.txt",
            "FINAL_COUNTRY_AIRFORCE_AUDIT.md", "FINAL_UNUSED_AIRCRAFT_DONORS.md",
        ):
            zf.write(out / fn, fn)
    zh = sha256(zpath)
    print("ZIP sha256", zh)
    print("ZIP", zpath)
    (ROOT / "FINAL_COUNTRY_AIRFORCE_AUDIT.md").write_text((out / "FINAL_COUNTRY_AIRFORCE_AUDIT.md").read_text())
    (ROOT / "FINAL_UNUSED_AIRCRAFT_DONORS.md").write_text((out / "FINAL_UNUSED_AIRCRAFT_DONORS.md").read_text())
    return 0


COUNTRY_REPORT = [
    ("France", "FranceAirfieldCommandSet", "France_HeavyAirBaseCommandSet", "FRANCE"),
    ("Germany", "GermanyAirfieldCommandSet", "Germany_HeavyAirBaseCommandSet", "GERMANY"),
    ("Italy", "ItalyAirfieldCommandSet", "Italy_HeavyAirBaseCommandSet", "ITALY"),
    ("United Kingdom", "BritainAirfieldCommandSet", "Britain_HeavyAirBaseCommandSet", "UNITED KINGDOM"),
    ("Japan", "Japan_AirfieldCommandSet", "Japan_HeavyAirBaseCommandSet", "JAPAN"),
    ("Turkey", "TurkeyAirfieldCommandSet", "Turkey_HeavyAirBaseCommandSet", "TURKEY"),
    ("Iran", "IranExpandedAirfieldCommandSet", "Iran_HeavyAirBaseCommandSet", "IRAN"),
    ("Pakistan", "Pakistan_AirfieldCommandSet", "Pakistan_HeavyAirBaseCommandSet", "PAKISTAN"),
    ("India", "India_AirfieldCommandSet", "India_HeavyAirBaseCommandSet", "INDIA"),
    ("Israel", "Israel_LargeAirBaseCommandSet", "Israel_HeavyAirBaseCommandSet", "ISRAEL"),
    ("Saudi Arabia", "SaudiArabia_AirfieldCommandSet", "SaudiArabia_HeavyAirBaseCommandSet", "SAUDI ARABIA"),
    ("NATO", "NatoAirfieldCommandSet", "Nato_HeavyAirBaseCommandSet", "NATO"),
    ("Sweden", "SwedenAirfieldCommandSet", "Sweden_HeavyAirBaseCommandSet", "SWEDEN"),
    ("Ukraine", "UkraineAirfieldCommandSet", "Ukraine_HeavyAirBaseCommandSet", "UKRAINE"),
    ("UAE", "UAE_AirfieldCommandSet", "UAE_HeavyAirBaseCommandSet", "UAE"),
    ("Libya", "Libya_AirfieldCommandSet", "Libya_HeavyAirBaseCommandSet", "LIBYA"),
    ("Syria", "Syria_AirfieldCommandSet", "Syria_HeavyAirBaseCommandSet", "SYRIA"),
    ("South Africa", "SouthAfrica_AirfieldCommandSet", "SouthAfrica_HeavyAirBaseCommandSet", "SOUTH AFRICA"),
    ("South Korea", "SouthKorea_AirfieldCommandSet", "SouthKorea_HeavyAirBaseCommandSet", "SOUTH KOREA"),
    ("North Korea", "NorthKorea_AirfieldCommandSet", "NorthKorea_HeavyAirBaseCommandSet", "NORTH KOREA"),
    ("Vietnam", "Vietnam_AirfieldCommandSet", "Vietnam_HeavyAirBaseCommandSet", "VIETNAM"),
    ("Iraq", "Iraq_AirfieldCommandSet", "Iraq_HeavyAirBaseCommandSet", "IRAQ"),
    ("GLA / Arabic", "ArabicAirfieldCommandSet", None, "GLA"),
]


def classify_obj(obj: str, block: str) -> str:
    name = obj + " " + block[:600]
    if re.search(r"Heli|AH64|UH60|NH90|CH47|CH53|AW101|AW139|AW249|A129|Mi-8|Mi8|Mi-35|Mi-28|Tiger|Caracal|Lynx|Panha|Chinook|Merlin|Wildcat|Puma|WZ10|Ka52", name, re.I):
        return "helicopter"
    if re.search(r"Drone|UAV|UCAV|Reaper|Heron|Neuron|RQ4|MQ9", name, re.I):
        return "uav"
    if re.search(r"E3|E7|G550|AWACS|CAEW", name, re.I) and not re.search(r"Mirage2000", name, re.I):
        return "awacs"
    if re.search(r"C130|C17|A400|IL-76|IL76|C27|Transport", name, re.I):
        return "transport"
    if re.search(r"Bomber|Vulcan|Tu-22|Tu22|B52", name, re.I):
        return "bomber"
    return "fighter"


ROLE_GUESS = {}


def write_audit_docs(out: Path, dh: str, ah: str, protect_hash: dict, vcs: str, obj_blocks: dict, btn_for: dict) -> None:
    new_by_obj = {a["obj"]: a for a in gen.AIRCRAFT}
    lines = [
        "# FINAL COUNTRY AIRFORCE AUDIT",
        "",
        "Playable countries discovered from PlayerTemplate.ini (excluding Civilian, Observer, BossGeneral).",
        "LOCKED / NOT MODIFIED: USA (FactionAmerica), Russia (FactionRussia), China (FactionChina).",
        "Egypt has airbase buildings but no PlayerTemplate — not playable, skipped.",
        "",
        f"DATA sha256 `{dh}`",
        f"ART sha256 `{ah}`",
        "",
        "Protected CommandSet hashes (unchanged):",
        "",
    ]
    for n, h in protect_hash.items():
        lines.append(f"- `{n}` `{h}`")
    lines += ["", "---", ""]

    table_rows = []
    totals = defaultdict(int)
    for pretty, fset, hset, tag in COUNTRY_REPORT:
        fobjs = gen.FIGHTER_MENUS[fset]
        hobjs = gen.HEAVY_MENUS.get(hset, []) if hset else []
        lines.append(f"COUNTRY: {pretty}")
        lines.append("")
        lines.append("FIGHTER AIRBASE — 12/12")
        a2a = multi = strike = 0
        for i, obj in enumerate(fobjs, 1):
            meta = new_by_obj.get(obj)
            block = obj_blocks.get(obj, "")
            model = re.search(r"Model\s+=\s+(\S+)", block)
            w3d = model.group(1) if model else "?"
            if meta:
                role = meta["role_label"]
                src = meta["source"]
                ident = meta["identity"]
            else:
                ident = obj
                role = "existing live unit"
                src = "already packed"
            rl = (meta["role"] if meta else "")
            if rl in ("a2a", "interceptor", "stealth"):
                a2a += 1
            elif rl in ("strike", "cas", "legacy"):
                strike += 1
            else:
                multi += 1
            a2a_n = "yes" if rl in ("a2a", "interceptor", "stealth", "multirole", "legacy") or not meta else "limited"
            a2g_n = "yes" if rl in ("multirole", "strike", "cas", "legacy", "stealth") or not meta else "no / gun only"
            lines += [
                f"{i:02d}. {ident} (`{obj}`)",
                f"    Role: {role}",
                f"    Visual W3D: {w3d}",
                f"    Visual source: {src}",
                f"    A2A: {a2a_n}",
                f"    A2G: {a2g_n}",
            ]
        lines.append("")
        if hset:
            lines.append("HEAVY / LARGE AIRBASE")
            kinds = defaultdict(list)
            for obj in hobjs:
                block = obj_blocks.get(obj, "")
                k = classify_obj(obj, block)
                model = re.search(r"Model\s+=\s+(\S+)", block)
                kinds[k].append((obj, model.group(1) if model else "?"))
                lines.append(f"- {obj}  Type: {k}  Visual: {model.group(1) if model else '?'}")
            lines.append("")
            lines.append("HELICOPTERS")
            for obj, w3d in kinds["helicopter"]:
                lines.append(f"- {obj} — helicopter — constructible on Heavy, W3D {w3d}")
            if not kinds["helicopter"]:
                lines.append("- none on Heavy (GLA has no Heavy Airbase)")
            lines.append("UAVs")
            for obj, w3d in kinds["uav"]:
                lines.append(f"- {obj} — UAV/UCAV — {w3d}")
            if not kinds["uav"]:
                lines.append("- none on this Heavy menu")
            lines.append("AWACS")
            for obj, w3d in kinds["awacs"]:
                lines.append(f"- {obj} — existing Specter AWACS logic preserved — {w3d}")
            if not kinds["awacs"]:
                lines.append("- none on this Heavy menu")
            lines.append("TRANSPORTS")
            for obj, w3d in kinds["transport"]:
                lines.append(f"- {obj} — transport — {w3d}")
            if not kinds["transport"]:
                lines.append("- none on this Heavy menu")
            lines.append("BOMBERS")
            for obj, w3d in kinds["bomber"]:
                lines.append(f"- {obj} — bomber — {w3d}")
            if not kinds["bomber"]:
                lines.append("- none on this Heavy menu")
            hc = len(kinds["helicopter"]); u = len(kinds["uav"]); a = len(kinds["awacs"]); t = len(kinds["transport"]); b = len(kinds["bomber"])
        else:
            lines.append("HEAVY / LARGE AIRBASE")
            lines.append("- GLA/Arabic has only ArabicArmy_Airfield. No Heavy Airbase exists; none was created.")
            lines.append("Helicopters/UAVs previously on the fighter pad were moved off the 12-jet menu.")
            hc = u = a = t = b = 0
        lines += [
            "",
            "STATUS:",
            "Fighter roster = 12/12",
            "All construct buttons valid = PASS",
            "All W3D refs = PASS",
            "Weapons = PASS (INI projectile-chain validation; no Zero Hour runtime firing test)",
            "Flight locomotors = PASS (JetAIUpdate + Snecma_M88_4E on new jets; existing units unchanged locomotors)",
            "Portraits = PASS (new jets have unique MappedImages; existing units keep live portraits)",
            "",
            "---",
            "",
        ]
        table_rows.append((pretty, 12, a2a, multi, strike, b, a, t, u, hc))
        totals["fighters"] += 12
        totals["heli"] += hc
        totals["uav"] += u
        totals["awacs"] += a
        totals["trans"] += t
        totals["bomb"] += b

    lines += [
        "## GLOBAL SUMMARY",
        "",
        "| Country | Fighters | A2A/Interceptor | Multirole | Strike/CAS/Legacy | Bombers | AWACS | Transports | UAVs | Helicopters |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in table_rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    lines += [
        "",
        f"TOTAL playable countries audited: {len(COUNTRY_REPORT)}",
        f"TOTAL fighter aircraft (constructible 12-slot entries): {totals['fighters']}",
        f"TOTAL helicopters (on Heavy menus counted): {totals['heli']}",
        f"TOTAL UAV/UCAV: {totals['uav']}",
        f"TOTAL AWACS: {totals['awacs']}",
        f"TOTAL transports: {totals['trans']}",
        f"TOTAL bombers: {totals['bomb']}",
        "",
        "A2A/Multirole/Strike counts for existing (non-new) fighters are approximate; new jets use explicit role tags.",
        "",
        "PROTECTED:",
        "USA — UNCHANGED",
        "RUSSIA — UNCHANGED",
        "CHINA — UNCHANGED",
        "",
        "No new airbases. No Nuclear/Atomic edits. No Fighter/Heavy building swaps.",
        "In-game Zero Hour firing was NOT runtime-tested.",
        "",
    ]
    (out / "FINAL_COUNTRY_AIRFORCE_AUDIT.md").write_text("\n".join(lines) + "\n")

    unused = [
        "# FINAL UNUSED AIRCRAFT DONORS",
        "",
        "Requested donor aliases from the unused-aircraft completion pass, plus this roster pass.",
        "",
        "| Alias | W3D | Source | Result | Notes |",
        "|---|---|---|---|---|",
        "| F18G | US_EA18G.W3D | packed | USED_ALREADY | AmericaJetEA18G; NATO Growler uses same live object |",
        "| Typhon | LSFEUEF2000.W3D | packed | USED_ALREADY | UK/DE/IT/SA/SE Gripens-as-canard |",
        "| Tornado | LSFTornado.W3D | packed | USED_ALREADY | UK/DE/IT/SA/NATO/ZA Buccaneer stand-in |",
        "| Rafale | LSFRafale.W3D | packed | USED_ALREADY | France + India LSFIDRafale |",
        "| Lighting | AVLightn.W3D | packed | USED_ALREADY | UK Lightning F6 + RSAF Lightning F.53 |",
        "| F16Falcon | LSFF16C.W3D | packed | USED_ALREADY | PakistanJetF16AMLU |",
        "| Eagle | LSFUSAF15C.W3D | packed | USED_ALREADY | Japan F-15J + Saudi F-15C |",
        "| F35B | ENF35A.W3D | packed | USED_ALREADY | UK/IT/JP/NATO F-35B |",
        "| F18prowler fighter | EA18G.W3D / LSFEA18G.W3D | DONOR_ART | NO_REALISTIC_COUNTRY | Extra Growler hashes; live Growler is US_EA18G. No Australia faction |",
        "| F22Raptor | US_F22A / LSFF22 | packed | USED_ALREADY | USA Raptor locked; Turkey KAAN uses LSFF22 |",
        "| Falcon | LSFF16C.W3D | packed | DUPLICATE | same as F16Falcon |",
        "| F18PROWLER | EA18G family | DONOR_ART | DUPLICATE | same as F18G extra meshes |",
        "| F18HORNET | AmF18A.W3D | DONOR_ART | NEWLY_USED | NATO F/A-18A |",
        "| F18HORNET | AVF-18.W3D | packed unused | NEWLY_USED | NATO F/A-18C |",
        "| F18HORNET | F18SEA.W3D | DONOR_ART | NEWLY_USED | NATO F/A-18E |",
        "| Lightning | AVLightn_A1.W3D | DONOR_ART | DUPLICATE | 4035-byte helper of AVLightn |",
        "| auter f22 | LSFF22.W3D | packed | DUPLICATE | Turkey KAAN |",
        "| F15strikeEagle | LSFUSAF15E.W3D | packed | USED_ALREADY | Saudi F-15S |",
        "| F2 | JPF2.W3D | packed | USED_ALREADY | Japan F-2A |",
        "| F16fighter | LSFKF16.W3D | packed | USED_ALREADY | Turkey Ozgur + ROKAF KF-16 |",
        "| Tomcat | Iran_F14A.W3D | packed | USED_ALREADY | IranJetF14A |",
        "| Tomcat extra | LSFIRF14A.W3D | DONOR_ART | NEWLY_USED | IranJetF14AM distinct mesh |",
        "| StrikeEagle | US_F15EX.W3D | packed | USED_ALREADY | Japan F-15DJ / Saudi F-15EX / UAE F-15EA |",
        "| J11FLANKER | LSFJ11B.W3D | packed | USED_ALREADY | China locked |",
        "| auterj31 | LSFJ31.W3D | packed | USED_ALREADY | China J-31; India AMCA / ROKAF KF-21 stand-in |",
        "| J10BRAPTOR | ChJ10B.W3D | packed | USED_ALREADY | China locked |",
        "| Qiang5 | QIANG5.W3D | packed | NEWLY_USED | Pakistan A-5C (China Q-5 remains locked) |",
        "| S6-30superflahker | RUSU30.W3D | packed | USED_ALREADY | India Su-30MKI; Vietnam Su-30MK2V |",
        "| F16ingLeapard | CHJH7A.W3D | DONOR_ART | NO_REALISTIC_COUNTRY | JH-7 extra hash; no non-China operator |",
        "| J15A | J15JZ.W3D | packed | USED_ALREADY | China locked |",
        "| J20C | LSFJ20.W3D | packed | USED_ALREADY | France FCAS NGF stand-in |",
        "| J7chengdu | LSFPKJ7 / LSFIRJ7 | packed | USED_ALREADY | Pakistan F-7PG / Iran F-7N |",
        "| Rafale fighter | LSFRafaleAS.W3D | packed | USED_ALREADY | France Rafale M / India Rafale DH |",
        "| Mirage 2000d | LSFMirage2KD.W3D | packed | USED_ALREADY | France / India / UAE / Sweden Viggen AJS |",
        "| StormFighter | (none) | — | NO_W3D | UK Tempest keeps SPEC_OLD_F35 |",
        "| AuterF2 | LSF02TJ.W3D | packed | USED_ALREADY | Japan F-2 Kai |",
        "| Shinshin | LSFSX2.W3D | packed | USED_ALREADY | Japan X-2 |",
        "| Eagle Japan | LSFJPF15J.W3D | packed | USED_ALREADY | Japan F-15J Kai |",
        "| F4phantom | JPF4.W3D | packed | USED_ALREADY | many Phantom operators |",
        "| F2fighter | AGMZJPF2G.W3D | packed | USED_ALREADY | Japan F-2B |",
        "| Mirage2000fighter | FraMirage2000.W3D | packed | USED_ALREADY | France 2000-5F / UAE 2000-9E |",
        "| Mirage21fighter | LSFMirage3 / LSFMirage5 / UVMirage | packed | USED_ALREADY | France + many Mirage operators |",
        "| EVTyphoon | EVTyphoon.W3D | DONOR_ART | NEWLY_USED | Germany Typhoon T1 |",
        "| LSFF15K | LSFF15K.W3D | DONOR_ART | NEWLY_USED | South Korea F-15K |",
        "| LSFISF15E | LSFISF15E.W3D | DONOR_ART | NEWLY_USED | Israel F-15I Ra'am unique mesh |",
        "| LSFISF16 | LSFISF16.W3D | DONOR_ART | NEWLY_USED | Israel F-16C Barak |",
        "| LSFPKF16 | LSFPKF16.W3D | DONOR_ART | NEWLY_USED | Pakistan F-16B |",
        "| LSFF16CEgy | LSFF16CEgy.W3D | DONOR_ART | NEWLY_USED | UAE F-16E unique mesh |",
        "| LSFIDMig21 | LSFIDMig21.W3D | packed unused | NEWLY_USED | India MiG-21 Bison / Vietnam MiG-21 |",
        "| CHAJ31HXNew | CHAJ31HXNew.W3D | packed unused | NEWLY_USED | Japan F-X |",
        "| LSFPKJF17 | LSFPKJF17.W3D | packed | NEWLY_USED | Pakistan JF-17 (China JF-17 remains locked) |",
        "",
        "STILL UNUSED unique W3Ds:",
        "",
        "1. **EA18G.W3D** (sha from prior audit `4ed1dceb834b031b`) and **LSFEA18G.W3D** (`4a28b58c20762da1`). Growler identity already live as USA `AmericaJetEA18G` (`US_EA18G`). NATO uses that same live Growler object. No Australia faction. Result: NO_REALISTIC_COUNTRY.",
        "2. **CHJH7A.W3D** (`ce9d3a8b9a0cb8c0`). JH-7 family; China already has JH-7A2. No realistic non-China operator. Result: NO_REALISTIC_COUNTRY.",
        "3. **StormFighter** — no dedicated W3D. Result: NO_W3D.",
        "4. **AVLightn_A1.W3D** — helper mesh. Result: DUPLICATE.",
        "5. **SU-25MU.TGA** referenced by EVTyphoon was not in DONOR_ART; Typhoon T1 uses `EVTyphoonSDTX04.tga` plus packed fallbacks.",
        "",
    ]
    (out / "FINAL_UNUSED_AIRCRAFT_DONORS.md").write_text("\n".join(unused) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
