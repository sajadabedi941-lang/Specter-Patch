#!/usr/bin/env python3
"""SPECTER1 faction flag + identity (DATA-only) pass.

Baseline: SPECTER1_WARFACTORY_BUILD_FIX DATA+ART.
Does not modify protected factions (USA, Israel, China, Russia, Iran, Iraq,
North Korea, NATO, Egypt): their PlayerTemplate blocks, object INIs, and CSF
keys stay byte-identical.
Does not modify ART, models, animations, weapons, units, or gameplay.
Only UI images (MappedImages), faction data (PlayerTemplate, CSF strings),
and building flag Draw Model references.

Universal faction flag mapping (applied + validated across ALL buildings):
  GLA-bloc Abbas flag mesh : Irq__IqFlag_Hs  (Iraq, Egypt, India, Libya,
                             Pakistan, Saudi Arabia, Syria, South Africa, UAE)
  North Korea Abbas mesh    : NKr__NKFlag_Hs  (North Korea ONLY)
  Command Centers           : faction CC model map below (US_Command for the
                             USA/NATO/Egypt-bloc; native meshes untouched)
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_WARFACTORY_BUILD_FIX/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_WARFACTORY_BUILD_FIX/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "1a4bbd0ff08c3f4c18ea70eb4b4af4d501ef69cdaf7bd77dafef10b1ff31561a"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_FACTION_FLAG_IDENTITY_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_FACTION_FLAG_IDENTITY_01")
RELEASE_NAME = "SPECTER1_FACTION_FLAG_IDENTITY_01"

P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_CSF = r"Data\English\generals.csf"
P_TURKEY_IMG = r"Data\INI\MappedImages\HandCreated\Turkey_FactionImages.INI"
P_TURKEY_STR = r"Data\English\Turkey_FactionStrings.txt"
WS_TURKEY_IMG = Path("/workspace/patch/Data/INI/MappedImages/HandCreated/Turkey_FactionImages.INI")
WS_TURKEY_STR = Path("/workspace/patch/Data/English/Turkey_FactionStrings.txt")

PROTECTED_TEMPLATES = [
    "FactionAmerica", "FactionIsrael", "FactionChina", "FactionRussia",
    "FactionIran", "FactionIraq", "FactionNorthKorea", "FactionNato",
    "FactionEgypt",
]
PROTECTED_FOLDERS = [
    "United States Of America", "Israel Defense Forces", "PLA",
    "Armed Forces Of Russian Federation", "Iranian Army", "Iraq Army",
    "North Korea", "NATO", "Egyptian Armed Forces",
]

# Japan / South Korea / Vietnam were cloned from the North Korea donor chain:
# Command Center draws NKr_Command (DPRK flag baked in) and the Abbas-type
# building draws NKr__NKFlag_Hs. Repoint onto the neutral donor meshes used
# by every other non-native faction (same as Egypt/NATO references).
CC_SWAPS = {
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_CommandCenter.ini":
        ("NKr_Command", "US_Command"),
    r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_CommandCenter.ini":
        ("NKr_Command", "US_Command"),
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_CommandCenter.ini":
        ("NKr_Command", "US_Command"),
}
ABBAS_SWAPS = {
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_NuclearCenter.ini":
        ("NKr__NKFlag_Hs", "Irq__IqFlag_Hs"),
    r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_NuclearCenter.ini":
        ("NKr__NKFlag_Hs", "Irq__IqFlag_Hs"),
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_NuclearCenter.ini":
        ("NKr__NKFlag_Hs", "Irq__IqFlag_Hs"),
}

# Universal Abbas flag map: Side -> required flag Draw mesh (None = no
# Abbas-type flag mesh expected; CC-embedded flags only).
ABBAS_FLAG_MAP = {
    "Iraq": "Irq__IqFlag_Hs",
    "Egypt": "Irq__IqFlag_Hs",
    "India": "Irq__IqFlag_Hs",
    "Libya": "Irq__IqFlag_Hs",
    "Pakistan": "Irq__IqFlag_Hs",
    "SaudiArabia": "Irq__IqFlag_Hs",
    "Syria": "Irq__IqFlag_Hs",
    "SouthAfrica": "Irq__IqFlag_Hs",
    "UAE": "Irq__IqFlag_Hs",
    "Japan": "Irq__IqFlag_Hs",
    "SouthKorea": "Irq__IqFlag_Hs",
    "Vietnam": "Irq__IqFlag_Hs",
    "NorthKorea": "NKr__NKFlag_Hs",
}

# DisplayName keys that do not exist in CSF ("*Forces") -> existing CSF keys.
DISPLAYNAME_FIX = {
    "FactionGermany": ("INI:FactionGermanyForces", "INI:FactionGermany"),
    "FactionFrance": ("INI:FactionFranceForces", "INI:FactionFrance"),
    "FactionBritain": ("INI:FactionBritainForces", "INI:FactionBritain"),
    "FactionItaly": ("INI:FactionItalyForces", "INI:FactionItaly"),
    "FactionSweden": ("INI:FactionSwedenForces", "INI:FactionSweden"),
    "FactionUkraine": ("INI:FactionUkraineForces", "INI:FactionUkraine"),
    "FactionTurkey": ("INI:FactionTurkeyForces", "INI:FactionTurkey"),
}

TURKEY_IMAGES = {
    "FlagWaterMark": "WatermarkTurkey",
    "EnabledImage": "SSObserverTurkey",
    "SideIconImage": "GameinfoTurkey",
    "GeneralImage": "Turkey_Logo",
}
TURKEY_TEXTURES = ["WatermarkTurkey", "GameinfoTurkey", "Turkey_Logo", "SSObserverTurkey"]

# Japan/SouthKorea/Vietnam GeneralImage points at MappedImages that do not
# exist anywhere (no national logo art in ART). Repoint at the resolving
# NorthKorea_Logo donor so the select portrait renders instead of missing.
# GAP: true national logos need new ART.
NK_LOGO_FIX = {
    "FactionJapan": "Japan_Logo",
    "FactionSouthKorea": "SouthKorea_Logo",
    "FactionVietnam": "Vietnam_Logo",
}

# Tooltip clone-boilerplate cleanup (cosmetic strings only).
TOOLTIP_FIX = {
    "India": "Indian Armed Forces \u2014 combined-arms doctrine with armor, airpower, and artillery.",
    "Germany": "Germany Armed Forces \u2014 combined-arms doctrine with Leopard armor and layered air defense.",
    "Japan": "Japan Self-Defense Forces \u2014 combined-arms doctrine with advanced airpower and missile defense.",
    "France": "French Armed Forces \u2014 combined-arms doctrine with Leclerc armor and layered air defense.",
    "SouthKorea": "Republic of Korea Armed Forces \u2014 combined-arms doctrine with K2 armor and layered air defense.",
    "SaudiArabia": "Saudi Arabia Armed Forces \u2014 combined-arms doctrine with armor, airpower, and artillery.",
    "Sweden": "Swedish Armed Forces \u2014 combined-arms doctrine with Gripen airpower and layered air defense.",
    "UAE": "United Arab Emirates Armed Forces \u2014 combined-arms doctrine with armor, airpower, and artillery.",
    "Ukraine": "Ukrainian Armed Forces \u2014 combined-arms doctrine with armor, airpower, and artillery.",
    "Turkey": "Turkish Armed Forces \u2014 combined-arms doctrine with strong air and drone support.",
    "Libya": "Libyan Armed Forces \u2014 combined-arms doctrine with armor, airpower, and artillery.",
    "Syria": "Syrian Armed Forces \u2014 combined-arms doctrine with armor, airpower, and artillery.",
    "SouthAfrica": "South African National Defence Force \u2014 combined-arms doctrine with Olifant armor and artillery.",
    "Italy": "Italian Armed Forces \u2014 combined-arms doctrine with armor, airpower, and layered air defense.",
    "Britain": "British Armed Forces \u2014 combined-arms doctrine with Challenger armor and layered air defense.",
    "Vietnam": "Vietnam People's Armed Forces \u2014 combined-arms doctrine with armor, airpower, and artillery.",
}


def field(block: str, key: str) -> str | None:
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block)
    return m.group(1).strip() if m else None


def split_templates(text: str) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    matches = list(re.finditer(r"(?im)^PlayerTemplate\s+(\S+)\s*$", text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        parts.append((m.group(1), text[m.start():end]))
    return parts


def parse_objects(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"(?im)^Object\s+(\S+)\s*$", text):
        m2 = re.search(r"(?im)^Object\s+\S+", text[m.end():])
        out[m.group(1)] = text[m.start(): m.end() + m2.start() if m2 else len(text)]
    return out


def dexor(b: bytes) -> bytes:
    return bytes(x ^ 0xFF for x in b)


def parse_csf(data: bytes) -> tuple[int, list]:
    assert data[:4] == b' FSC'
    ver, nlab, _nstr = struct.unpack("<III", data[4:16])
    pos = 24
    labels = []
    for _ in range(nlab):
        assert data[pos:pos + 4] == b' LBL', (pos, data[pos:pos + 4])
        cnt = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        nlen = struct.unpack("<I", data[pos + 8:pos + 12])[0]
        name = data[pos + 12:pos + 12 + nlen].decode("ascii")
        pos += 12 + nlen
        vals = []
        for _ in range(cnt):
            tag = data[pos:pos + 4]
            pos += 4
            vlen = struct.unpack("<I", data[pos:pos + 4])[0]
            pos += 4
            raw = data[pos:pos + vlen * 2]
            pos += vlen * 2
            extra = None
            if tag == b'WRTS':
                extra = data[pos:pos + 4]
                pos += 4
            vals.append((tag, dexor(raw).decode("utf-16-le"), extra))
        labels.append((name, vals))
    assert pos == len(data), (pos, len(data))
    return ver, labels


def serialize_csf(ver: int, labels: list) -> bytes:
    out = bytearray()
    out += b' FSC' + struct.pack("<I", ver)
    nstr = sum(len(v) for _, v in labels)
    out += struct.pack("<III", len(labels), nstr, 0) + b'\x00' * 4
    for name, vals in labels:
        nb = name.encode("ascii")
        out += b' LBL' + struct.pack("<II", len(vals), len(nb)) + nb
        for tag, val, extra in vals:
            vb = dexor(val.encode("utf-16-le"))
            out += tag + struct.pack("<I", len(val)) + vb
            if tag == b'WRTS':
                out += extra
    return bytes(out)


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("unexpected DATA SHA")
    if jf.sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("unexpected ART SHA")
    if not WS_TURKEY_IMG.is_file():
        raise SystemExit("missing workspace Turkey_FactionImages.INI")
    if not WS_TURKEY_STR.is_file():
        raise SystemExit("missing workspace Turkey_FactionStrings.txt")

    entries = jf.read_big_list(SRC_DATA)
    baseline = {jf.norm(n).lower(): bytes(b) for n, b in entries}
    art_names = {jf.norm(n).lower() for n, _ in jf.read_big_list(SRC_ART)}

    for tex in TURKEY_TEXTURES:
        if not any(n.endswith(("\\" + tex + ".tga").lower()) or n.endswith(("/" + tex + ".tga").lower()) for n in art_names):
            raise SystemExit(f"Turkey texture missing from ART: {tex}")

    protected_templates_before: dict[str, str] = {}
    for pt_path in (P_PT, P_PT_PATCH):
        for name, blk in split_templates(jf.text_of(entries, pt_path)):
            if name in PROTECTED_TEMPLATES:
                protected_templates_before[name] = blk
    if len(protected_templates_before) != len(PROTECTED_TEMPLATES):
        raise SystemExit("protected template missing")

    # ---- 1. Command Center + Abbas flag Draw swaps (JP/SK/VN) ----
    draw_changed = []
    for path, (old_mesh, new_mesh) in {**CC_SWAPS, **ABBAS_SWAPS}.items():
        if any(f.lower() in jf.norm(path).lower() for f in PROTECTED_FOLDERS):
            raise SystemExit(f"refusing protected path {path}")
        old = jf.text_of(entries, path)
        new, n_model = re.subn(
            rf"(?im)^(\s*Model\s*=\s*){re.escape(old_mesh)}\b", rf"\1{new_mesh}", old)
        new, n_anim = re.subn(
            rf"(?im)^(\s*Animation\s*=\s*){re.escape(old_mesh)}\.{re.escape(old_mesh)}\b",
            rf"\1{new_mesh}.{new_mesh}", new)
        if n_model < 1 or n_anim < 1:
            raise SystemExit(f"{path}: expected Model/Animation pairs, got {n_model}/{n_anim}")
        if re.search(rf"(?im)^\s*(Model|Animation)\s*=\s*{re.escape(old_mesh)}", new):
            raise SystemExit(f"{path}: old mesh still referenced")
        jf.set_text(entries, path, new)
        draw_changed.append((path, old_mesh, new_mesh, n_model, n_anim))

    # ---- 2. PlayerTemplate identity fields ----
    parts = split_templates(jf.text_of(entries, P_PT))
    by_name = dict(parts)
    pt_changes: list[str] = []
    for tname, (old_dn, new_dn) in DISPLAYNAME_FIX.items():
        blk = by_name[tname]
        if field(blk, "DisplayName") != old_dn:
            raise SystemExit(f"{tname}: DisplayName != {old_dn}")
        by_name[tname] = re.sub(rf"(?im)^(\s*DisplayName\s*=\s*){re.escape(old_dn)}\s*$",
                                rf"\1{new_dn}", blk, count=1)
        pt_changes.append(f"{tname} DisplayName {old_dn} -> {new_dn}")
    tblk = by_name["FactionTurkey"]
    for key, img in TURKEY_IMAGES.items():
        if field(tblk, key) is None:
            raise SystemExit(f"Turkey template missing {key}")
        tblk = re.sub(rf"(?im)^(\s*{re.escape(key)}\s*=\s*)\S+\s*$", rf"\1{img}", tblk, count=1)
        pt_changes.append(f"FactionTurkey {key} -> {img}")
    by_name["FactionTurkey"] = tblk
    for tname, old_logo in NK_LOGO_FIX.items():
        blk = by_name[tname]
        if field(blk, "GeneralImage") != old_logo:
            raise SystemExit(f"{tname}: GeneralImage != {old_logo}")
        by_name[tname] = re.sub(rf"(?im)^(\s*GeneralImage\s*=\s*){re.escape(old_logo)}\s*$",
                                r"\1NorthKorea_Logo", blk, count=1)
        pt_changes.append(f"{tname} GeneralImage {old_logo} -> NorthKorea_Logo (GAP: no national logo in ART)")
    for name in PROTECTED_TEMPLATES:
        if name in by_name and by_name[name] != protected_templates_before[name]:
            raise SystemExit(f"protected template mutated: {name}")
    new_pt = "".join(by_name[n] for n, _ in parts)
    jf.set_text(entries, P_PT, new_pt)

    # ---- 3. New files: Turkey MappedImages + strings ----
    jf.add_file(entries, P_TURKEY_IMG, WS_TURKEY_IMG.read_text(encoding="utf-8"))
    jf.add_file(entries, P_TURKEY_STR, WS_TURKEY_STR.read_text(encoding="utf-8"))

    # ---- 4. CSF tooltip cleanup ----
    ver, labels = parse_csf(jf.raw_of(entries, P_CSF))
    csf_map = dict((n, v) for n, v in labels)
    for need in list(DISPLAYNAME_FIX.values()):
        for _, new_dn in [need]:
            if new_dn not in csf_map:
                raise SystemExit(f"CSF missing {new_dn}")
    csf_changed = []
    for faction, text in TOOLTIP_FIX.items():
        key = f"TOOLTIP:BioStrategyLong_{faction}"
        if key not in csf_map:
            raise SystemExit(f"CSF missing {key}")
        old_val = csf_map[key][0][1]
        if "clone" not in old_val:
            raise SystemExit(f"{key} does not look like clone boilerplate: {old_val[:60]}")
        csf_map[key] = [(csf_map[key][0][0], text, csf_map[key][0][2])]
        csf_changed.append(key)
    new_labels = [(n, csf_map[n]) for n, _ in labels]
    new_csf = serialize_csf(ver, new_labels)
    ver2, labels2 = parse_csf(new_csf)
    if dict((n, v) for n, v in labels2) != csf_map:
        raise SystemExit("CSF re-parse mismatch")
    i = jf.find_index(entries, P_CSF)
    entries[i] = (entries[i][0], new_csf)

    # ---- 5. Global change audit: only expected paths differ ----
    expected_changed = {jf.norm(p).lower() for p in
                        list(CC_SWAPS) + list(ABBAS_SWAPS) + [P_PT, P_CSF]}
    expected_new = {jf.norm(P_TURKEY_IMG).lower(), jf.norm(P_TURKEY_STR).lower()}
    changed, added = [], []
    for n, b in entries:
        key = jf.norm(n).lower()
        if key not in baseline:
            added.append(n)
        elif baseline[key] != bytes(b):
            changed.append(n)
    if set(jf.norm(a).lower() for a in added) != expected_new:
        raise SystemExit(f"unexpected added files: {added}")
    if set(jf.norm(c).lower() for c in changed) != expected_changed:
        raise SystemExit(f"unexpected changed files: {changed}")

    blob = jf.build_big_ordered(entries)
    new_sha = hashlib.sha256(blob).hexdigest()
    if new_sha == EXPECTED_DATA_SHA:
        raise SystemExit("DATA SHA unchanged")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(blob)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(blob)
    shutil.copy2(SRC_ART, OUT_DIR / "_SPEC_ART_ONE.big")
    shutil.copy2(SRC_ART, WS_OUT / "_SPEC_ART_ONE.big")
    if jf.sha256_file(WS_OUT / "_SPEC_ART_ONE.big") != EXPECTED_ART_SHA:
        raise SystemExit("ART copy changed")

    # ---- 6. Validate packed result ----
    packed = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    objs: dict[str, str] = {}
    for n, b in packed:
        if n.lower().endswith(".ini"):
            objs.update(parse_objects(b.decode("latin1", errors="replace")))
    mi_names: set[str] = set()
    for n, b in packed:
        if "mappedimage" in n.lower():
            for m in re.finditer(r"(?im)^MappedImage\s+(\S+)\s*$", b.decode("latin1", errors="replace")):
                mi_names.add(m.group(1))

    # Universal flag check across ALL buildings.
    flag_checked = 0
    for oname, oblk in objs.items():
        side = field(oblk, "Side")
        if not side:
            continue
        models = re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", oblk)
        flag_models = [m for m in models if m.endswith("Flag_Hs")]
        if not flag_models:
            continue
        want = ABBAS_FLAG_MAP.get(side)
        if want is None:
            raise SystemExit(f"{oname} (Side={side}) has flag mesh but no mapping")
        for fm in set(flag_models):
            if fm != want:
                raise SystemExit(f"{oname} flag {fm} != mapped {want} for Side={side}")
            flag_checked += 1
    # CC model check for repaired factions.
    for cc_path, (_old, want) in CC_SWAPS.items():
        txt = jf.text_of(packed, cc_path)
        if not re.search(rf"(?im)^\s*Model\s*=\s*{re.escape(want)}\b", txt):
            raise SystemExit(f"{cc_path}: CC model != {want}")

    # Template checks: DisplayName keys exist in CSF; images resolve.
    # Donor images shared with protected (known-correct) factions resolve via
    # the same path as those factions (mod or base game); newly wired names
    # (Turkey_*, NorthKorea_Logo) must exist as mod MappedImages.
    ver3, labels3 = parse_csf(jf.raw_of(packed, P_CSF))
    csf_keys = set(n for n, _ in labels3)
    pt_parts = dict(split_templates(jf.text_of(packed, P_PT)))
    pt_parts.update(dict(split_templates(jf.text_of(packed, P_PT_PATCH))))
    ref_images: set[str] = set()
    for tname in PROTECTED_TEMPLATES:
        for key in ("SideIconImage", "GeneralImage", "EnabledImage", "FlagWaterMark",
                    "ScoreScreenImage", "LoadScreenImage"):
            v = field(pt_parts[tname], key)
            if v:
                ref_images.add(v)
    for tname in list(DISPLAYNAME_FIX) + list(NK_LOGO_FIX) + ["FactionTurkey", "FactionIndia",
            "FactionSaudiArabia", "FactionUAE", "FactionSyria", "FactionLibya",
            "FactionPakistan", "FactionSouthAfrica"]:
        blk = pt_parts[tname]
        dn = field(blk, "DisplayName")
        if dn not in csf_keys:
            raise SystemExit(f"{tname}: DisplayName {dn} missing from CSF")
        for key in ("SideIconImage", "GeneralImage", "EnabledImage", "FlagWaterMark"):
            img = field(blk, key)
            if img not in mi_names and img not in ref_images:
                raise SystemExit(f"{tname}: {key}={img} has no MappedImage (mod or base)")
    for tname in PROTECTED_TEMPLATES:
        if pt_parts[tname] != protected_templates_before[tname]:
            raise SystemExit(f"protected template changed in pack: {tname}")

    repaired = ["India", "Germany", "Japan", "France", "SouthKorea", "SaudiArabia",
                "Sweden", "UAE", "Ukraine", "Turkey", "Libya", "Syria", "Pakistan",
                "SouthAfrica", "Italy", "Britain", "Vietnam"]
    lines = [
        "SPECTER1 FACTION FLAG + IDENTITY 01",
        f"BASELINE_DATA_SHA256 = {EXPECTED_DATA_SHA}",
        f"NEW_DATA_SHA256 = {new_sha}",
        f"ART_SHA256 = {EXPECTED_ART_SHA} (unchanged copy)",
        "ART_CHANGED = NO",
        "MODELS_CHANGED = NO",
        "WEAPONS_CHANGED = NO",
        "UPGRADES_CHANGED = NO",
        "PROTECTED_FACTIONS_UNCHANGED = YES (USA, Israel, China, Russia, Iran, Iraq, NorthKorea, NATO, Egypt)",
        "REPAIRED = " + ", ".join(repaired),
        "",
        "FLAG SYSTEM = universal Side->mesh map validated across ALL building objects "
        f"({flag_checked} Abbas flag Draw refs checked)",
        "DRAW_FIXES (NK donor -> neutral donor, JP/SK/VN only):",
    ]
    for path, old_mesh, new_mesh, nm, na in draw_changed:
        lines.append(f"  {path}: {old_mesh} -> {new_mesh} ({nm} Model + {na} Animation)")
    lines += [
        "",
        "IDENTITY_FIXES:",
        *[f"  {c}" for c in pt_changes],
        "  + packed Turkey_FactionImages.INI (WatermarkTurkey/GameinfoTurkey/Turkey_Logo/SSObserverTurkey/Turkey_Flag)",
        "  + packed Turkey_FactionStrings.txt",
        *[f"  CSF {k} tooltip de-cloned" for k in csf_changed],
        "",
        "GAPS (need new ART, not fixable DATA-only):",
        "  - JP/SK/VN + all other repaired factions have no national logo/flag textures in ART;",
        "    select portraits show donor (NK/GLA/USA) images; Turkey is fully wired.",
        "  - True per-nation building flags need new flag W3Ds; Abbas/CC flags now match",
        "    the correct-faction reference standard (Egypt/NATO pattern).",
        "",
        "INGAME_TESTED = NO",
        "DATA_CHANGED = YES",
        "ART_CHANGED = NO",
    ]
    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 faction flag + identity 01 (DATA only)

Continues from SPECTER1_WARFACTORY_BUILD_FIX. Protected factions
(USA, Israel, China, Russia, Iran, Iraq, North Korea, NATO, Egypt)
are byte-identical. ART, models, animations, weapons, units, and
gameplay unchanged.

Building flags: Japan / South Korea / Vietnam Command Centers and
Abbas-type buildings were cloned from the North Korea donor chain and
displayed the DPRK flag. Repointed onto the neutral donor meshes used
by every other non-native faction (US_Command, Irq__IqFlag_Hs — the
Egypt/NATO reference standard). A universal Side->flag-mesh map is now
validated across all building objects in the pack step.

Identity: Germany / France / Britain / Italy / Sweden / Ukraine /
Turkey faction names were blank (templates pointed at INI:Faction*Forces
keys that do not exist in generals.csf). Repointed at the existing
INI:Faction* keys. Turkey select images wired to its packed ART
(Turkey_Logo / GameinfoTurkey / SSObserverTurkey / WatermarkTurkey).
Japan / South Korea / Vietnam portraits repointed at the resolving
NorthKorea_Logo donor (no national logo art exists). Clone-boilerplate
tooltips replaced with national text in generals.csf.

Still needs new ART for true national logos/flags (all factions except
Turkey) and true per-nation building flags.

INGAME_TESTED = NO
"""
    install = f"""{RELEASE_NAME}
==============================

Faction flag + identity fix on the SPECTER1 WarFactory-fix baseline.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
   ART is an unchanged copy of the current SPECTER1 ART pack.
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
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", new_sha)
    print("ZIP", zpath, zpath.stat().st_size, zip_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
