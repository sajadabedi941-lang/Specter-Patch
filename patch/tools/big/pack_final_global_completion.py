#!/usr/bin/env python3
"""Pack final global donor-reuse + UAV completion from the global-donor-airforce BIGs.

ART from DONOR_ART only. Specter gameplay stays native.
Fills unused visible CommandSet slots. Does not rewrite mature USA/RU fighter menus.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_final_global_completion as gen
import pack_china_heavy_aircraft as ch
import pack_europe_airforce as eu
import pack_france_airforce as fr
import pack_uk_e7_boot_crash_fix as e7

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
DONORS = [Path("/tmp/donor_completion"), Path("/tmp/donor_global")]
BASE_DATA = Path("/tmp/global_donor_airforce/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/global_donor_airforce/_SPEC_ART_ONE.big")

MARKER_W = "; ===== SPECTER FINAL GLOBAL COMPLETION WEAPONS BEGIN ====="
MARKER_WE = "; ===== SPECTER FINAL GLOBAL COMPLETION WEAPONS END ====="

NEW_OBJECTS = [s["obj"] for s in gen.AIRCRAFT]
NEW_WEAPONS = re.findall(r"^Weapon (\S+)", gen.WEAPONS, re.M)

PROTECT_SETS = [
    "AmericaAirfieldCommandSet",
    "America_LargeAirBaseCommandSet",
    "America_HeavyAirBaseCommandSet",
    "RussiaAirfieldCommandSet",
    "Russia_LargeAirBaseCommandSet",
    "Russia_HeavyAirBaseCommandSet",
    "PLAAirfieldCommandSet",
    "China_LargeAirBaseCommandSet",
    "ItalyAirfieldCommandSet",
    "Italy_LargeAirBaseCommandSet",
    "BritainAirfieldCommandSet",
    "Britain_LargeAirBaseCommandSet",
    "GermanyAirfieldCommandSet",
    "Germany_LargeAirBaseCommandSet",
    "TurkeyAirfieldCommandSet",
    "Turkey_LargeAirBaseCommandSet",
    "IranAirfieldCommandSet",
    "IranExpandedAirfieldCommandSet",
    "Japan_AirfieldCommandSet",
]

SLOT_ADDS = {
    "Germany_HeavyAirBaseCommandSet": {
        8: "Command_ConstructGermanyUAVEuroMALE",
        9: "Command_ConstructGermanyJetFCASNGF",
    },
    "France_HeavyAirBaseCommandSet": {5: "Command_ConstructFranceUCAVNeuron"},
    "FranceAirfieldCommandSet": {
        11: "Command_ConstructFranceJetMirageF1CR",
        12: "Command_ConstructFranceJetRafaleF4",
    },
    "France_LargeAirBaseCommandSet": {
        11: "Command_ConstructFranceJetMirageF1CR",
        12: "Command_ConstructFranceJetRafaleF4",
    },
    "Britain_HeavyAirBaseCommandSet": {12: "Command_ConstructBritainAircraftTornadoECR"},
    "Japan_HeavyAirBaseCommandSet": {
        7: "Command_ConstructJapanJetC130H",
        8: "Command_ConstructJapanUAVRQ4",
    },
    "China_HeavyAirBaseCommandSet": {12: "Command_ConstructChinaJetJ35A"},
    "Iran_HeavyAirBaseCommandSet": {
        2: "Command_ConstructIranJetMig21Bis",
        3: "Command_ConstructIranJetSu35S",
    },
    "Turkey_HeavyAirBaseCommandSet": {6: "Command_ConstructTurkeyJetF4ETerm"},
    "Italy_HeavyAirBaseCommandSet": {8: "Command_ConstructItalyJetGCAP"},
    "Pakistan_AirfieldCommandSet": {9: "Command_ConstructPakistanJetJ10CE"},
}

SYNC_FILES = {
    "data\\ini\\commandset_france.ini": ["France_HeavyAirBaseCommandSet"],
    "data\\ini\\commandset_germany.ini": ["Germany_HeavyAirBaseCommandSet"],
    "data\\ini\\commandset_italy.ini": ["Italy_HeavyAirBaseCommandSet"],
    "data\\ini\\commandset_britain.ini": ["Britain_HeavyAirBaseCommandSet"],
}

ART_NAMES = {
    "AVCargoPln.W3D", "AVCargoPln_D.W3D", "AVCargoPln_D1.W3D",
    "CHAJ31HXNew.W3D",
    "LSFIDRafale.W3D", "LSFIDRafaled.W3D", "LSFIDRafalek.W3D",
    "LSFIDMig21.W3D", "LSFIDMig21d.W3D",
    "AVCrago2.dds", "AVCrago2_D.dds", "AVCrago2_D1.dds",
    "CHA_J31A.dds",
    "LSFIDRafale.dds", "LSFIDRafaled.dds", "LSFIDRafalek.dds",
    "LSFMig21.dds", "LSFMig21d.dds",
}

PORTRAIT_SRC = {
    "SPEC_GermanyEuroMALE.tga": "US_MQ9.dds",
    "SPEC_FranceNeuron.tga": "PLA_GJ11.dds",
    "SPEC_GermanyFCASNGF.tga": "LSFJ31.dds",
    "SPEC_FranceMirageF1CR.tga": "LSFFRF1.dds",
    "SPEC_FranceRafaleF4.tga": "LSFIDRafale.dds",
    "SPEC_BritainTornadoECR.tga": "LSFTornado.dds",
    "SPEC_JapanC130H.tga": "AVCrago2.dds",
    "SPEC_ChinaJ35A.tga": "CHA_J31A.dds",
    "SPEC_IranMig21Bis.tga": "LSFMig21.dds",
    "SPEC_IranSu35S.tga": "RussiaSU35.dds",
    "SPEC_TurkeyF4ETerm.tga": "LSFJPF4.dds",
    "SPEC_PakistanJ10CE.tga": "PLA_J10C.dds",
    "SPEC_ItalyGCAP.tga": "t50t.tga",
    "SPEC_JapanRQ4.tga": "US_RQ-4.dds",
}

PROJECTILES = {
    "MeteorMissile_Object", "AIM-9X_Object", "R77_Object",
    "GBU24_GuidedBombObject", "Fab-250", "Kh59MK2_Object",
    "KH31P_MissileObject", "Paveway_IV_Object", "GenericUnguidedRockets",
    "30mm_API-T_Projectile",
}

REGRESS = {
    "America_LargeAirBaseCommandSet": "Command_ConstructAmericaJetRaptor",
    "America_HeavyAirBaseCommandSet": "Command_ConstructAmericaJetB2",
    "Russia_LargeAirBaseCommandSet": "Command_ConstructRussiaJetSu35S",
    "PLAAirfieldCommandSet": "Command_ConstructChinaJetJ11B",
    "China_HeavyAirBaseCommandSet": "Command_ConstructChinaJetJ20C",
    "France_LargeAirBaseCommandSet": "Command_ConstructFranceJetRafaleC",
    "FranceAirfieldCommandSet": "Command_ConstructFranceJetMirage20005F",
    "Germany_LargeAirBaseCommandSet": "Command_ConstructGermanyJetTyphoonT4",
    "Italy_LargeAirBaseCommandSet": "Command_ConstructItalyJetTyphoon",
    "Britain_LargeAirBaseCommandSet": "Command_ConstructBritainJetF35B",
    "Britain_HeavyAirBaseCommandSet": "Command_ConstructBritainJetTempest",
    "Japan_AirfieldCommandSet": "Command_ConstructJapanJetF2A",
    "Turkey_HeavyAirBaseCommandSet": "Command_ConstructTurkeyJetKAAN",
    "IranExpandedAirfieldCommandSet": "Command_ConstructIranJetF14A",
    "Iran_HeavyAirBaseCommandSet": "Command_ConstructIranJetF4E",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def find_donor(name: str) -> Path | None:
    for root in DONORS:
        if not root.exists():
            continue
        hits = [p for p in root.rglob("*") if p.is_file() and p.name.lower() == name.lower()]
        if hits:
            return hits[0]
    return None


def rebuild_commandset(block: str, adds: dict[int, str]) -> str:
    m = re.match(r"CommandSet (\S+)", block)
    if not m:
        raise SystemExit("bad commandset block")
    name = m.group(1)
    slots: dict[int, str] = {}
    for line in block.splitlines():
        sm = re.match(r"\s*(\d+)\s*=\s*(\S+)", line)
        if sm:
            slots[int(sm.group(1))] = sm.group(2)
    for slot, btn in adds.items():
        if slot in slots and slots[slot] != btn:
            raise SystemExit(f"{name} slot {slot} occupied by {slots[slot]}")
        slots[slot] = btn
    lines = [f"CommandSet {name}"]
    for slot in sorted(slots):
        lines.append(f"  {slot} = {slots[slot]}")
    lines.append("End")
    return "\n".join(lines) + "\n"


def replace_cs(text: str, name: str, new_block: str) -> str:
    pat = re.compile(rf"CommandSet {re.escape(name)}\s*\n.*?^End\s*$", re.M | re.S)
    if not pat.search(text):
        raise SystemExit(f"missing {name}")
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
    if any(ord(c) > 127 for c in overlay):
        raise SystemExit("non-ASCII weapons")
    block = MARKER_W + "\n" + overlay.strip() + "\n" + MARKER_WE + "\n"
    if MARKER_W in weapon_ini:
        weapon_ini = re.sub(
            re.escape(MARKER_W) + r".*?" + re.escape(MARKER_WE) + r"\n?",
            block,
            weapon_ini,
            count=1,
            flags=re.S,
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


def collect_overlay() -> dict[str, bytes]:
    overlay: dict[str, bytes] = {}
    for spec in gen.AIRCRAFT:
        p = PATCH / spec["rel"]
        dest = "Data\\" + spec["rel"].replace("/", "\\")
        overlay[dest] = ch.lf(p.read_bytes())
    extra = [
        "INI/Weapon_FinalGlobalCompletion.ini",
        "INI/CommandButton_FinalGlobalCompletion.ini",
        "INI/MappedImages/HandCreated/zFinalGlobalCompletion_Portrait_Images.INI",
    ]
    for rel in extra:
        p = PATCH / rel
        dest = "Data\\" + rel.replace("/", "\\")
        overlay[dest] = ch.lf(p.read_bytes())
    return overlay


def write_install(out: Path) -> None:
    text = """SPECTER FINAL GLOBAL AIRCRAFT COMPLETION

Copy both BIG files into the game folder, replacing previous Specter BIGs:

  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

ART-only from DONOR_ART plus native Specter gameplay wrappers.
Does not import donor Object/Weapon/CommandSet INI.

Dotted aliases created as live units:
- Germany Eurodrone MALE (Heavy)
- France nEUROn stealth UCAV (Heavy)
- Germany FCAS NGF Demonstrator (Heavy)
- France Mirage F1CR and Rafale F4 (Fighter)
- UK Tornado ECR (Heavy)
- Japan C-130H transport (Heavy)
- China J-35A (Heavy)

Appearance-only reuse:
- Iran MiG-21bis and Su-35 (Heavy)
- Turkey F-4E Terminator (Heavy)
- Pakistan J-10CE (Airfield)
- Italy GCAP demonstrator (Heavy)
- Japan RQ-4 unarmed HALE UAV (Heavy)

Does not change airbase architecture, Rally, Sell, or USA/Russia fighter menus.
"""
    (out / "INSTALL.txt").write_text(text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/final_global_completion"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

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

    protect_hash = {
        n: hashlib.sha256(ch.grab_block(data_map["data\\ini\\commandset.ini"][1].decode("latin1"), n).encode("latin1")).hexdigest()
        for n in PROTECT_SETS
    }

    cs_key = "data\\ini\\commandset.ini"
    cs_name, cs_blob = data_map[cs_key]
    cs_text = cs_blob.decode("latin1")
    btn_overlay = overlay[r"Data\INI\CommandButton_FinalGlobalCompletion.ini"].decode("ascii")
    cs_text = inline_buttons(cs_text, btn_overlay)
    canonical = {}
    for set_name, adds in SLOT_ADDS.items():
        old = ch.grab_block(cs_text, set_name)
        new = rebuild_commandset(old, adds)
        cs_text = replace_cs(cs_text, set_name, new)
        canonical[set_name] = new
        print("updated", set_name, sorted(adds))
    cb_key = "data\\ini\\commandbutton.ini"
    cb_text = data_map[cb_key][1].decode("latin1")
    ch.validate_commandset_button_refs(cs_text, cb_text)
    data_map[cs_key] = (cs_name, ch.lf(cs_text.encode("latin1")))

    for fkey, names in SYNC_FILES.items():
        if fkey not in data_map:
            raise SystemExit(f"missing {fkey}")
        fname, fblob = data_map[fkey]
        ftext = fblob.decode("latin1")
        for set_name in names:
            if set_name not in canonical:
                continue
            ftext = replace_cs(ftext, set_name, canonical[set_name])
            print("synced", fkey, set_name)
        data_map[fkey] = (fname, ch.lf(ftext.encode("latin1")))

    pk_key = "data\\ini\\commandset_pakistan.ini"
    if pk_key in data_map:
        fname, fblob = data_map[pk_key]
        ftext = fblob.decode("latin1")
        old = re.search(r"CommandSet Pakistan_AirfieldCommandSet\s*\n.*?^End\s*$", ftext, re.M | re.S)
        if old:
            new = rebuild_commandset(old.group(0), SLOT_ADDS["Pakistan_AirfieldCommandSet"])
            ftext = replace_cs(ftext, "Pakistan_AirfieldCommandSet", new)
            data_map[pk_key] = (fname, ch.lf(ftext.encode("latin1")))
            print("synced Pakistan_AirfieldCommandSet overlay")

    wpn_key = "data\\ini\\weapon.ini"
    wpn_name, wpn_blob = data_map[wpn_key]
    wpn_text = wpn_blob.decode("latin1")
    wpn_overlay = overlay[r"Data\INI\Weapon_FinalGlobalCompletion.ini"].decode("ascii")
    for wname in NEW_WEAPONS:
        if f"Weapon {wname}" in wpn_text:
            raise SystemExit(f"Weapon {wname} already in Weapon.ini")
    wpn_text = inline_weapons(wpn_text, wpn_overlay)
    for wname in NEW_WEAPONS:
        if wpn_text.count(f"Weapon {wname}") != 1:
            raise SystemExit(f"Weapon {wname} count {wpn_text.count('Weapon '+wname)}")
    data_map[wpn_key] = (wpn_name, ch.lf(wpn_text.encode("latin1")))
    print("inlined", len(NEW_WEAPONS), "weapons")

    hc_key = "data\\ini\\mappedimages\\handcreated\\handcreatedmappedimages.ini"
    for k in data_map:
        if k.endswith("handcreatedmappedimages.ini"):
            hc_key = k
            break
    hc_name, hc_blob = data_map[hc_key]
    hc_text = hc_blob.decode("latin1")
    por_ini = overlay[r"Data\INI\MappedImages\HandCreated\zFinalGlobalCompletion_Portrait_Images.INI"].decode("ascii")
    if not hc_text.endswith("\n"):
        hc_text += "\n"
    hc_text += "\n" + por_ini.strip() + "\n"
    data_map[hc_key] = (hc_name, ch.lf(hc_text.encode("latin1")))

    csf_key = "data\\english\\generals.csf"
    csf_name, csf_blob = data_map[csf_key]
    csf_new = patch_csf(csf_blob)
    ch.validate_csf(csf_new, list(gen.CSF_LABELS))
    data_map[csf_key] = (csf_name, csf_new)

    skip = {
        "data\\ini\\commandbutton_finalglobalcompletion.ini",
        "data\\ini\\weapon_finalglobalcompletion.ini",
    }
    for dest, content in overlay.items():
        key = ch.norm_key(dest)
        if key in skip:
            continue
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (dest, content)
        print("DATA inject", dest)

    missing_art = []
    for name in sorted(ART_NAMES):
        src = find_donor(name)
        if src is None:
            packed = False
            for _k, (pn, _blob) in art_map.items():
                if pn.split("\\")[-1].lower() == name.lower():
                    packed = True
                    break
            if packed:
                continue
            missing_art.append(name)
            continue
        dest = ("Art\\W3D\\" if name.lower().endswith(".w3d") else "Art\\Textures\\") + name
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, src.read_bytes())
    if missing_art:
        raise SystemExit("missing ART\n" + "\n".join(missing_art))
    print("ART injected from donor")

    packed_tex = {k.split("\\")[-1].lower(): art_map[k][1] for k in art_map if "\\textures\\" in k}
    for dest_name, src_name in PORTRAIT_SRC.items():
        src = find_donor(src_name)
        if src is None:
            leaf = src_name.lower()
            if leaf not in packed_tex:
                raise SystemExit(f"missing portrait source {src_name}")
            tmp = Path("/tmp") / ("portrait_src_" + leaf.replace("/", "_"))
            tmp.write_bytes(packed_tex[leaf])
            src = tmp
        tga = eu.make_portrait_any(src)
        dest = f"Art\\Textures\\{dest_name}"
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, tga)
        print("portrait", dest_name, len(tga))

    obj_hits: dict[str, list[str]] = {o: [] for o in NEW_OBJECTS}
    for key in list(data_map):
        name, blob = data_map[key]
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1")
        for obj in NEW_OBJECTS:
            if re.search(rf"^Object {re.escape(obj)}\b", text, re.M):
                obj_hits[obj].append(name)
        if key in {ch.norm_key(r"Data\\" + s["rel"].replace("/", "\\")) for s in gen.AIRCRAFT}:
            errs = e7.balanced_end(text, name)
            if errs:
                raise SystemExit("End balance FAIL\n" + "\n".join(errs))
    for obj, hits in obj_hits.items():
        expect = [s for s in gen.AIRCRAFT if s["obj"] == obj][0]
        expect_name = "Data\\" + expect["rel"].replace("/", "\\")
        if [h.lower() for h in hits] != [expect_name.lower()]:
            raise SystemExit(f"Object {obj} hits={hits}")
    print("new Object unique PASS")

    art_w3d = {k.split("\\")[-1].lower().replace(".w3d", "") for k in art_map if k.endswith(".w3d")}
    for spec in gen.AIRCRAFT:
        for m in (spec["model"], spec["model_d"], spec["model_k"]):
            if m.lower() not in art_w3d:
                raise SystemExit(f"missing W3D for {spec['obj']} model {m}")
    print("ART/W3D PASS")

    found_proj = set()
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1")
        for p in PROJECTILES:
            if re.search(rf"^Object {re.escape(p)}\b", text, re.M):
                found_proj.add(p)
    missing_proj = PROJECTILES - found_proj
    if missing_proj:
        raise SystemExit("missing projectile objects: " + ", ".join(sorted(missing_proj)))
    print("Projectile references PASS")

    cs_final = data_map[cs_key][1].decode("latin1")
    for n in PROTECT_SETS:
        h = hashlib.sha256(ch.grab_block(cs_final, n).encode("latin1")).hexdigest()
        if h != protect_hash[n]:
            raise SystemExit(f"protected CommandSet changed: {n}")
    print("protected CommandSets unchanged PASS")

    for set_name, adds in SLOT_ADDS.items():
        block = ch.grab_block(cs_final, set_name)
        for slot, btn in adds.items():
            if not re.search(rf"^\s*{slot}\s*=\s*{re.escape(btn)}\s*$", block, re.M):
                raise SystemExit(f"{set_name} missing {slot}={btn}")
        if "Command_Sell" not in block:
            raise SystemExit(f"{set_name} lost Sell")
        slots = [int(x) for x in re.findall(r"^\s*(\d+)\s*=", block, re.M)]
        if len(slots) != len(set(slots)):
            raise SystemExit(f"{set_name} duplicate slots {slots}")
        for slot in adds:
            if slot > 12:
                raise SystemExit(f"{set_name} used off-screen slot {slot}")
    print("slot fill PASS")

    for set_name, btn in REGRESS.items():
        if btn not in ch.grab_block(cs_final, set_name):
            raise SystemExit(f"regression {set_name} lost {btn}")
    print("country regression PASS")

    mapped = set(re.findall(r"^MappedImage (\S+)", data_map[hc_key][1].decode("latin1"), re.M))
    for img in gen.PORTRAITS:
        if img not in mapped:
            raise SystemExit(f"missing MappedImage {img}")
    print("MappedImage PASS")

    out_data_map = {data_map[k][0]: data_map[k][1] for k in data_keys}
    out_art_map = {art_map[k][0]: art_map[k][1] for k in art_keys}
    data_big = ch.build_big(out_data_map)
    art_big = ch.build_big(out_art_map)
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_big)
    out_art.write_bytes(art_big)
    dh = sha256(out_data)
    ah = sha256(out_art)
    print("DATA sha256", dh)
    print("ART sha256", ah)

    v_entries, v_raw = ch.read_big(out_data)
    v_map = {}
    for name, off, size in v_entries:
        v_map[ch.norm_key(name)] = (name, v_raw[off : off + size])
    va_entries, va_raw = ch.read_big(out_art)
    va_w3d = set()
    for name, off, size in va_entries:
        if name.lower().endswith(".w3d"):
            va_w3d.add(name.split("\\")[-1].lower())
    vcs = v_map["data\\ini\\commandset.ini"][1].decode("latin1")
    vwpn = v_map["data\\ini\\weapon.ini"][1].decode("latin1")
    for obj in NEW_OBJECTS:
        hits = []
        for name, blob in v_map.values():
            if name.lower().endswith(".ini") and re.search(rf"^Object {re.escape(obj)}\b", blob.decode("latin1"), re.M):
                hits.append(name)
        if len(hits) != 1:
            raise SystemExit(f"re-extract Object {obj} hits={hits}")
        if f"Command_Construct{obj}" not in vcs:
            raise SystemExit(f"re-extract missing button {obj}")
    for wname in NEW_WEAPONS:
        if f"Weapon {wname}" not in vwpn:
            raise SystemExit(f"re-extract missing weapon {wname}")
    for need in ("avcargopln.w3d", "chaj31hxnew.w3d", "lsfidrafale.w3d", "lsfidmig21.w3d", "nat_heron.w3d", "chi_gj11l.w3d", "us_rq-4.w3d", "qsnt50.w3d"):
        if need not in va_w3d:
            raise SystemExit(f"re-extract ART missing {need}")
    print("re-extract FINAL content PASS")

    write_install(out)
    (out / "PACK_REPORT.txt").write_text(
        f"DATA sha256 {dh}\nART  sha256 {ah}\nDATA bytes {out_data.stat().st_size}\nART  bytes {out_art.stat().st_size}\n"
        f"new aircraft {len(NEW_OBJECTS)}\nnew weapons {len(NEW_WEAPONS)}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
