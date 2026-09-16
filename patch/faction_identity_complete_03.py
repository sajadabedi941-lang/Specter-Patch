#!/usr/bin/env python3
"""SPECTER1 complete per-country visual identity (DATA-only).

Baseline: SPECTER1_FACTION_FLAG_ART_01 DATA+ART.
Closes the last donor fallbacks in faction UI identity by wiring every
repaired faction's select portrait, side icon, observer icon, and
watermark to its OWN native flag texture (created in the ART pass) via
new MappedImages -- real national flags, no approximation, no fakes.

Per faction (Side -> texture): 4 MappedImages following the
NorthKorea_UI / Turkey_FactionImages convention:
  Watermark<Side>   full 128x64 flag
  <Side>_Logo       center 64x64 crop (select portrait)
  Gameinfo<Side>    center 64x64 crop (side icon)
  SSObserver<Side>  center 64x64 crop (observer icon)

Protected factions, ART, gameplay, units, weapons, animations unchanged.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf
from faction_flag_identity_01 import field, parse_csf, split_templates

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_FACTION_FLAG_ART_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_FACTION_FLAG_ART_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "41ef2ab8e04ea5aba4c34575edf772ab44161897e317667113e6d7b71f686c42"
EXPECTED_ART_SHA = "5cc32f0794d01a6d4f6d2485aebe41352ced0067309ff8ff0339c43d55870340"
OUT_DIR = Path("/tmp/SPECTER1_FACTION_IDENTITY_COMPLETE_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_FACTION_IDENTITY_COMPLETE_01")
RELEASE_NAME = "SPECTER1_FACTION_IDENTITY_COMPLETE_01"

P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_MI = r"Data\INI\MappedImages\HandCreated\Specter_FactionIdentity.INI"

PROTECTED_TEMPLATES = [
    "FactionAmerica", "FactionIsrael", "FactionChina", "FactionRussia",
    "FactionIran", "FactionIraq", "FactionNorthKorea", "FactionNato",
    "FactionEgypt",
]

# Side -> flag texture stem (must exist in ART from the ART pass).
SIDES = {
    "India": "IN_Flag.tga",
    "Germany": "DE_Flag.tga",
    "Japan": "JP_Flag.tga",
    "France": "FR_Flag.tga",
    "SouthKorea": "SK_Flag.tga",
    "SaudiArabia": "SA_Flag.tga",
    "Sweden": "SE_Flag.tga",
    "UAE": "UAE_Flag.tga",
    "Ukraine": "UA_Flag.tga",
    "Libya": "LY_Flag.tga",
    "Syria": "SY_Flag.tga",
    "Pakistan": "PK_Flag.tga",
    "SouthAfrica": "ZA_Flag.tga",
    "Italy": "IT_Flag.tga",
    "Britain": "UK_Flag.tga",
    "Vietnam": "VN_Flag.tga",
}

# Side -> native Abbas flag mesh (None = no Abbas consumer; reference
# standard identical to USA/NATO: house color only, no flag mesh).
ABBAS_MESH = {
    "India": "India_Flag_Hs",
    "Libya": "Libya_Flag_Hs",
    "Pakistan": "Pakistan_Flag_Hs",
    "SaudiArabia": "SaudiArabia_Flag_Hs",
    "Syria": "Syria_Flag_Hs",
    "SouthAfrica": "SouthAfrica_Flag_Hs",
    "UAE": "UAE_Flag_Hs",
    "Japan": "Japan_Flag_Hs",
    "SouthKorea": "SouthKorea_Flag_Hs",
    "Vietnam": "Vietnam_Flag_Hs",
    "Germany": None, "France": None, "Britain": None, "Italy": None,
    "Sweden": None, "Ukraine": None,
}


def mi_block(name: str, tex: str, coords: str) -> str:
    l, t, r, b = coords
    return (
        f"MappedImage {name}\n"
        f"  Texture = {tex}\n"
        f"  TextureWidth = 128\n"
        f"  TextureHeight = 64\n"
        f"  Coords = Left:{l} Top:{t} Right:{r} Bottom:{b}\n"
        f"  Status = NONE\n"
        f"End\n"
    )


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("unexpected DATA SHA")
    if jf.sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("unexpected ART SHA")

    entries = jf.read_big_list(SRC_DATA)
    art_names = {jf.norm(n).lower() for n, _ in jf.read_big_list(SRC_ART)}
    for side, stem in SIDES.items():
        if f"art\\textures\\{stem}".lower() not in art_names:
            raise SystemExit(f"ART missing flag texture {stem}")

    # Collect existing MappedImage names; new names must not collide.
    mi_names: set[str] = set()
    for n, b in entries:
        if "mappedimage" in n.lower():
            for m in re.finditer(r"(?im)^MappedImage\s+(\S+)\s*$",
                                 b.decode("latin1", errors="replace")):
                mi_names.add(m.group(1))

    new_names: dict[str, str] = {}
    for side in SIDES:
        new_names[side] = {
            "GeneralImage": f"{side}_Logo",
            "SideIconImage": f"Gameinfo{side}",
            "EnabledImage": f"SSObserver{side}",
            "FlagWaterMark": f"Watermark{side}",
        }
    for side, mapping in new_names.items():
        for key, name in mapping.items():
            if name in mi_names:
                raise SystemExit(f"MI name collision: {name}")

    # Write the new MappedImages file.
    chunks = ["; SPECTER PATCH - native per-faction identity images (flag-based, real national flags)\n"]
    for side, stem in SIDES.items():
        tex = stem[:-4]
        chunks.append(mi_block(f"Watermark{side}", tex, (0, 0, 128, 64)))
        chunks.append(mi_block(f"{side}_Logo", tex, (32, 0, 96, 64)))
        chunks.append(mi_block(f"Gameinfo{side}", tex, (32, 0, 96, 64)))
        chunks.append(mi_block(f"SSObserver{side}", tex, (32, 0, 96, 64)))
    jf.add_file(entries, P_MI, "\n".join(chunks))

    # Repoint templates.
    protected_before: dict[str, str] = {}
    for pt_path in (P_PT, P_PT_PATCH):
        for name, blk in split_templates(jf.text_of(entries, pt_path)):
            if name in PROTECTED_TEMPLATES:
                protected_before[name] = blk
    parts = split_templates(jf.text_of(entries, P_PT))
    by_name = dict(parts)
    repoints = []
    for side, mapping in new_names.items():
        tname = f"Faction{side}"
        blk = by_name[tname]
        for key, img in mapping.items():
            old = field(blk, key)
            if old is None:
                raise SystemExit(f"{tname} missing {key}")
            if old == img:
                raise SystemExit(f"{tname} {key} already {img}")
            blk = re.sub(rf"(?im)^(\s*{re.escape(key)}\s*=\s*)\S+\s*$",
                         rf"\1{img}", blk, count=1)
            repoints.append(f"{tname} {key} {old} -> {img}")
        by_name[tname] = blk
    for name in PROTECTED_TEMPLATES:
        if name in by_name and by_name[name] != protected_before[name]:
            raise SystemExit(f"protected template mutated: {name}")
    jf.set_text(entries, P_PT, "".join(by_name[n] for n, _ in parts))

    # ---- Validation on packed result ----
    blob = jf.build_big_ordered(entries)
    new_sha = hashlib.sha256(blob).hexdigest()
    WS_OUT.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(blob)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(blob)
    shutil.copy2(SRC_ART, WS_OUT / "_SPEC_ART_ONE.big")
    shutil.copy2(SRC_ART, OUT_DIR / "_SPEC_ART_ONE.big")

    packed = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    packed_mi: set[str] = set()
    for n, b in packed:
        if "mappedimage" in n.lower():
            for m in re.finditer(r"(?im)^MappedImage\s+(\S+)\s*$",
                                 b.decode("latin1", errors="replace")):
                packed_mi.add(m.group(1))
    _ver, labels = parse_csf(jf.raw_of(packed, r"Data\English\generals.csf"))
    csf = dict((n, v) for n, v in labels)
    pt = dict(split_templates(jf.text_of(packed, P_PT)))
    pt.update(dict(split_templates(jf.text_of(packed, P_PT_PATCH))))

    report = []
    all_pass = True
    for side, stem in SIDES.items():
        tname = f"Faction{side}"
        blk = pt[tname]
        dn = field(blk, "DisplayName")
        name_ok = dn in csf
        name_val = csf[dn][0][1] if name_ok else "MISSING"
        logo = field(blk, "GeneralImage")
        logo_ok = logo in packed_mi
        flag_ok = f"art\\textures\\{stem}".lower() in art_names
        mesh = ABBAS_MESH[side]
        if mesh is None:
            bldg = "n/a (USA/NATO reference standard: house color, no flag mesh)"
            bldg_ok = True
        else:
            hits = [b.decode("latin1", errors="replace") for n, b in packed
                    if n.lower().endswith(("_abbas.ini", "_nuclearcenter.ini"))
                    and side.lower() in n.lower().replace(" ", "")]
            want = [h for h in hits if mesh in h and "IqFlag" not in h and "NKFlag" not in h]
            bldg_ok = len(hits) > 0 and len(want) == len(hits)
            bldg = f"{mesh} wired ({len(want)}/{len(hits)} Abbas files native)"
        icons_ok = all(field(blk, k) in packed_mi for k in
                       ("SideIconImage", "EnabledImage", "FlagWaterMark"))
        res = "PASS" if (name_ok and logo_ok and flag_ok and bldg_ok and icons_ok) else "FAIL"
        if res == "FAIL":
            all_pass = False
        report.append(
            f"Faction: {side}\n"
            f"Name: {name_val} ({dn}) [{'ok' if name_ok else 'MISSING'}]\n"
            f"Logo: {logo} [{'ok' if logo_ok else 'MISSING'}]\n"
            f"Flag: {stem} [{'ok' if flag_ok else 'MISSING'}]\n"
            f"Buildings checked: {bldg} [{'ok' if bldg_ok else 'FAIL'}]\n"
            f"Icons: side/observer/watermark [{'ok' if icons_ok else 'FAIL'}]\n"
            f"Result: {res}\n")

    for name in PROTECTED_TEMPLATES:
        if pt[name] != protected_before[name]:
            raise SystemExit(f"protected template changed in pack: {name}")
    if not all_pass:
        raise SystemExit("per-faction audit has FAILs")

    turk = pt["FactionTurkey"]
    if field(turk, "GeneralImage") != "Turkey_Logo":
        raise SystemExit("Turkey wiring regressed")

    lines = [
        "SPECTER1 FACTION IDENTITY COMPLETE 01",
        f"BASELINE_DATA_SHA256 = {EXPECTED_DATA_SHA}",
        f"NEW_DATA_SHA256 = {new_sha}",
        f"ART_SHA256 = {EXPECTED_ART_SHA} (unchanged copy)",
        "ART_CHANGED = NO",
        "GAMEPLAY_CHANGED = NO",
        "PROTECTED_FACTIONS_UNCHANGED = YES (USA, Israel, China, Russia, Iran, Iraq, NorthKorea, NATO, Egypt)",
        "DONOR_FALLBACKS_REMAINING = NO (all 16 repaired factions use native flag-based images)",
        "",
        "PER-FACTION AUDIT:",
        "",
        *report,
        "INGAME_TESTED = NO",
        "DATA_CHANGED = YES (PlayerTemplate.ini repoints + Specter_FactionIdentity.INI)",
        "ART_CHANGED = NO",
    ]
    audit = "\n".join(lines)
    if not audit.endswith("\n"):
        audit += "\n"
    changelog = """SPECTER1 faction identity complete 01 (DATA only)

Continues from SPECTER1_FACTION_FLAG_ART_01. Every repaired faction's
country-select portrait, side icon, observer icon, and watermark now
points at its own native flag texture through 64 new MappedImages in
Specter_FactionIdentity.INI. No donor fallbacks remain (Turkey was
already native). Names resolve via generals.csf; Abbas buildings draw
native flag meshes (ART pass). Protected factions, ART, gameplay,
units, weapons, and animations unchanged.

INGAME_TESTED = NO
"""
    install = f"""{RELEASE_NAME}
==============================

Complete per-country visual identity on the flag-ART baseline.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
   ART is an unchanged copy of the SPECTER1 flag-ART pack.
4. Launch Specter.

Checksums:
  DATA SHA256 {new_sha}
  ART  SHA256 {EXPECTED_ART_SHA}

INGAME_TESTED = NO
"""
    for dest in (OUT_DIR, WS_OUT):
        (dest / "audit.txt").write_text(audit, encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "INSTALL.txt").write_text(install, encoding="utf-8")
    zpath = WS_OUT / f"{RELEASE_NAME}.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
        zf.write(WS_OUT / "INSTALL.txt", "INSTALL.txt")
    (OUT_DIR / zpath.name).write_bytes(zpath.read_bytes())
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {new_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {EXPECTED_ART_SHA} (unchanged copy)\n"
        f"{zpath.name}  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n"
    )
    for dest in (OUT_DIR, WS_OUT):
        (dest / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    print(audit)
    print("ZIP", zpath, zpath.stat().st_size, zip_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
