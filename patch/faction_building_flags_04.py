#!/usr/bin/env python3
"""SPECTER1 3D building flags for all repaired factions (ART clones + DATA).

Baseline: SPECTER1_FACTION_IDENTITY_COMPLETE_01 DATA+ART.
Problem: buildings whose W3D models carry another nation's baked FLAG
cloth (Iraq-lineage -> IraqiFlag.tga, NK-lineage -> DPRK_Flag.tga).
Fix: per-faction W3D clones that are byte-identical except the texture
name inside FLAG01/02/03 MESH chunks (size-preserving in-place swap),
retargeting DATA Draw Model= refs Side -> native clone. Geometry,
animations (embedded, names unchanged), hierarchy, and all other
materials untouched.

US-lineage models (US_Command, US_WarFactory, ...) carry NO flag cloth
(FPOLE is a camo pole, canopies are house color) = the correct USA/NATO
reference standard, so they are left as-is. Radars (Irq_P3, US_RadarSt,
Nat_RadarSt) are flag-free dishes and stay as-is.

Protected factions (USA, Israel, China, Russia, Iran, Iraq, NorthKorea,
NATO, Egypt) keep the donor meshes: byte-identical.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_FACTION_IDENTITY_COMPLETE_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_FACTION_IDENTITY_COMPLETE_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "bd4e898d6b2d4e1c2b33e3491743fe677bb0ec9ced5d5b9c44de7ef546ef6072"
EXPECTED_ART_SHA = "5cc32f0794d01a6d4f6d2485aebe41352ced0067309ff8ff0339c43d55870340"
OUT_DIR = Path("/tmp/SPECTER1_BUILDING_FLAGS_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_BUILDING_FLAGS_01")
RELEASE_NAME = "SPECTER1_BUILDING_FLAGS_01"

# donor mesh -> (donor flag texture, {faction CC: flag texture stem})
JOBS = {
    "Irq_WarFactory": ("IraqiFlag.tga", {"IN": "IN_Flag.tga", "LY": "LY_Flag.tga",
        "PK": "PK_Flag.tga", "SA": "SA_Flag.tga", "SY": "SY_Flag.tga",
        "ZA": "ZA_Flag.tga", "UAE": "UAE_Flag.tga"}),
    "Iraq_Powerplant": ("IraqiFlag.tga", {"IN": "IN_Flag.tga", "LY": "LY_Flag.tga",
        "PK": "PK_Flag.tga", "SA": "SA_Flag.tga", "SY": "SY_Flag.tga",
        "ZA": "ZA_Flag.tga", "UAE": "UAE_Flag.tga"}),
    "Iraq_Supply": ("IraqiFlag.tga", {"IN": "IN_Flag.tga", "LY": "LY_Flag.tga",
        "PK": "PK_Flag.tga", "SA": "SA_Flag.tga", "SY": "SY_Flag.tga",
        "ZA": "ZA_Flag.tga", "UAE": "UAE_Flag.tga"}),
    "irq_camp": ("IraqiFlag.tga", {"IN": "IN_Flag.tga", "LY": "LY_Flag.tga",
        "PK": "PK_Flag.tga", "SA": "SA_Flag.tga", "SY": "SY_Flag.tga",
        "ZA": "ZA_Flag.tga", "UAE": "UAE_Flag.tga", "JP": "JP_Flag.tga",
        "SK": "SK_Flag.tga", "VN": "VN_Flag.tga"}),
    "NKr_WarFactory": ("DPRK_Flag.tga", {"JP": "JP_Flag.tga", "SK": "SK_Flag.tga",
        "VN": "VN_Flag.tga"}),
    "NKor_Powerplant": ("DPRK_Flag.tga", {"JP": "JP_Flag.tga", "SK": "SK_Flag.tga",
        "VN": "VN_Flag.tga"}),
    "NKor_Supply": ("DPRK_Flag.tga", {"JP": "JP_Flag.tga", "SK": "SK_Flag.tga",
        "VN": "VN_Flag.tga"}),
}
CC_SIDE = {"IN": "India", "LY": "Libya", "PK": "Pakistan", "SA": "SaudiArabia",
           "SY": "Syria", "ZA": "SouthAfrica", "UAE": "UAE", "JP": "Japan",
           "SK": "SouthKorea", "VN": "Vietnam"}
REPAIRED_SIDES = set(CC_SIDE.values())

def in_protected_folder(fname: str) -> bool:
    segs = jf.norm(fname).lower().split("\\")
    return any(seg in (p.lower() for p in PROTECTED_FOLDERS) for seg in segs)

# Object-name prefixes attributing Side when the block omits Side=.
NAME_PREFIX_SIDE = {
    "India": "India", "Libya": "Libya", "Pakistan": "Pakistan",
    "SaudiArabia": "SaudiArabia", "Syria": "Syria", "SouthAfrica": "SouthAfrica",
    "UAE": "UAE", "Japan": "Japan", "SouthKorea": "SouthKorea",
    "Vietnam": "Vietnam", "Turkey": "Turkey", "Germany": "Germany",
    "France": "France", "Britain": "Britain", "Italy": "Italy",
    "Sweden": "Sweden", "Ukraine": "Ukraine",
}


def object_side(oname: str, blk: str) -> str | None:
    sm = re.search(r"(?im)^\s*Side\s*=\s*(\S+)\s*$", blk)
    if sm:
        return sm.group(1)
    for prefix, side in NAME_PREFIX_SIDE.items():
        if oname.startswith(prefix):
            return side
    return None
PROTECTED_FOLDERS = ["United States Of America", "Israel Defense Forces", "PLA",
    "Armed Forces Of Russian Federation", "Iranian Army", "Iraq Army",
    "North Korea", "NATO", "Egyptian Armed Forces"]


def kids(buf: bytes):
    out, p = [], 0
    while p + 8 <= len(buf):
        ct, raw = struct.unpack("<II", buf[p:p + 8])
        sz = raw & 0x7FFFFFFF
        if sz < 0 or p + sz + 8 > len(buf):
            raise SystemExit(f"W3D parse error ct=0x{ct:x}")
        out.append((p, ct, sz, buf[p + 8:p + sz + 8]))
        p += sz + 8
    if p != len(buf):
        raise SystemExit("W3D trailing bytes")
    return out


def mesh_name(mpay: bytes) -> str:
    for _, c2, _, p2 in kids(mpay):
        if c2 == 0x1F:
            parts = p2[8:].split(b"\x00")
            return parts[0].decode("ascii")
    raise SystemExit("MESH without 0x1F header")


def clone_w3d(donor: bytes, donor_tex: str, new_stem: str) -> bytes:
    dt = donor_tex.encode("ascii")
    field_len = len(dt) + 1
    new_field = new_stem.encode("ascii") + b"\x00"
    if len(new_field) > field_len:
        raise SystemExit(f"texture name too long: {new_stem}")
    new_field = new_field + b"\x00" * (field_len - len(new_field))
    out = bytearray(donor)
    replaced = 0
    for off, ct, _sz, pay in kids(bytes(out)):
        if ct != 0x0:
            continue
        name = mesh_name(pay)
        allowed = "FLAG" in name.upper() or (name.upper().startswith("BOX") and dt in pay)
        if not allowed:
            if dt in pay:
                raise SystemExit(f"{dt.decode()} in non-flag mesh {name}: refusing")
            continue
        n = pay.count(dt)
        if n < 1:
            raise SystemExit(f"FLAG mesh {name} lacks {dt.decode()}")
        start = 0
        while True:
            i = bytes(out).find(dt, off + 8 + start, off + 8 + len(pay))
            if i < 0:
                break
            out[i:i + field_len] = new_field
            replaced += 1
            start = (i - off - 8) + field_len
    if replaced < 1:
        raise SystemExit("no FLAG texture refs replaced")
    if bytes(out).count(dt) != donor.count(dt) - replaced:
        raise SystemExit("replacement count mismatch")
    assert len(out) == len(donor)
    return bytes(out)


def parse_objects(text: str):
    out = []
    for m in re.finditer(r"(?im)^Object\s+(\S+)\s*$", text):
        m2 = re.search(r"(?im)^Object\s+\S+", text[m.end():])
        out.append((m.group(1), m.start(),
                    m.end() + m2.start() if m2 else len(text)))
    return out


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("unexpected DATA SHA")
    if jf.sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("unexpected ART SHA")
    data_entries = jf.read_big_list(SRC_DATA)
    art_entries = jf.read_big_list(SRC_ART)
    data_base = {jf.norm(n).lower(): bytes(b) for n, b in data_entries}
    art_base = {jf.norm(n).lower(): bytes(b) for n, b in art_entries}
    art_names = set(art_base)

    for _donor, (_dt, facs) in JOBS.items():
        for _cc, stem in facs.items():
            if f"art\\textures\\{stem}".lower() not in art_names:
                raise SystemExit(f"ART missing {stem}")

    # ---- ART clones ----
    clone_of: dict[str, str] = {}
    for donor, (dtex, facs) in JOBS.items():
        donor_bytes = bytes(jf.raw_of(art_entries, f"Art\\W3D\\{donor}.W3D"))
        for cc, stem in facs.items():
            clone = f"{donor}_{cc}"
            w3d = clone_w3d(donor_bytes, dtex, stem)
            assert dtex.encode("ascii") not in w3d
            assert stem.encode("ascii") in w3d
            rel = f"Art\\W3D\\{clone}.W3D"
            if jf.norm(rel).lower() in art_names:
                raise SystemExit(f"already packed: {rel}")
            art_entries.append((jf.norm(rel), w3d))
            art_names.add(jf.norm(rel).lower())
            clone_of[(donor, CC_SIDE[cc])] = clone
    n_clones = len(clone_of)

    # ---- DATA repoints (Side-scoped, repaired factions only) ----
    donor_names = sorted(set(JOBS), key=len, reverse=True)
    changed_files = set()
    swap_count = 0
    for idx, (fname, blob) in enumerate(data_entries):
        if not fname.lower().endswith(".ini"):
            continue
        if in_protected_folder(fname):
            continue
        text = blob.decode("latin1", errors="replace")
        parts = []
        last = 0
        dirty = False
        for oname, start, end in parse_objects(text):
            parts.append(text[last:start])
            blk = text[start:end]
            side = object_side(oname, blk)
            if side and side in REPAIRED_SIDES:
                def rep(m: re.Match) -> str:
                    for dnr in donor_names:
                        if m.group(2) == dnr and (dnr, side) in clone_of:
                            return m.group(1) + clone_of[(dnr, side)]
                    return m.group(0)
                blk2 = re.sub(r"(?im)^(\s*Model\s*=\s*)(\S+)\s*$", rep, blk)
                if blk2 != blk:
                    dirty = True
                    for dnr in donor_names:
                        if (dnr, side) in clone_of:
                            swap_count += len(re.findall(
                                rf"(?im)^\s*Model\s*=\s*{re.escape(dnr)}\s*$", blk))
                blk = blk2
            parts.append(blk)
            last = end
        parts.append(text[last:])
        if dirty:
            data_entries[idx] = (fname, "".join(parts).encode("latin1"))
            changed_files.add(fname)

    if not changed_files:
        raise SystemExit("no DATA files changed")
    for f in changed_files:
        if in_protected_folder(f):
            raise SystemExit(f"protected file changed: {f}")

    data_blob = jf.build_big_ordered(data_entries)
    art_blob = jf.build_big_ordered(art_entries)
    new_data_sha = hashlib.sha256(data_blob).hexdigest()
    new_art_sha = hashlib.sha256(art_blob).hexdigest()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(data_blob)
    (WS_OUT / "_SPEC_ART_ONE.big").write_bytes(art_blob)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_blob)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_blob)

    # ---- Validation on packed result ----
    packed_data = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    packed_art = jf.read_big_list(WS_OUT / "_SPEC_ART_ONE.big")
    p_art = {jf.norm(n).lower(): bytes(b) for n, b in packed_art}
    for (donor, side), clone in clone_of.items():
        w = p_art.get(jf.norm(f"Art\\W3D\\{clone}.W3D").lower())
        if w is None:
            raise SystemExit(f"clone missing in pack: {clone}")
    # every FLAG mesh in every clone uses the native texture
    for (donor, side), clone in clone_of.items():
        w = p_art[jf.norm(f"Art\\W3D\\{clone}.W3D").lower()]
        want = [c for c, s in CC_SIDE.items() if s == side][0]
        stem = JOBS[donor][1][want]
        for _off, ct, _sz, pay in kids(w):
            if ct != 0x0:
                continue
            if "FLAG" in mesh_name(pay).upper():
                if stem.encode("ascii") not in pay:
                    raise SystemExit(f"{clone}: FLAG mesh lacks {stem}")
                if JOBS[donor][0].encode("ascii") in pay:
                    raise SystemExit(f"{clone}: FLAG mesh keeps donor tex")
    # ART add-only
    for n, b in packed_art:
        k = jf.norm(n).lower()
        if k in art_base and art_base[k] != bytes(b):
            raise SystemExit(f"ART modified: {n}")
    # per-faction x building audit
    def classify(oname: str) -> str | None:
        o = oname.lower()
        if "abbas" in o or "nuclearcenter" in o:
            return "Abbas"
        if "command" in o or "militaryhq" in o or o.endswith("hq"):
            return "Command Center"
        if "war" in o and "factor" in o or o.endswith("mic") or "warfactory" in o:
            return "War Factory"
        if "radar" in o or "listening" in o:
            return "Radar"
        if "power" in o or "reactor" in o or "nuclear" in o:
            return "Power"
        if "supply" in o or "depot" in o or "warehouse" in o:
            return "Supply"
        if "barrack" in o or "bootcamp" in o or o.endswith("camp") or "training" in o:
            return "Barracks"
        return None
    native_tex = {}
    for donor, (_dt, facs) in JOBS.items():
        for cc, stem in facs.items():
            native_tex.setdefault(CC_SIDE[cc], set()).add(stem)
    for cc, side in CC_SIDE.items():
        stem = [s for (_d, (_t, f)) in JOBS.items() for c, s in f.items() if c == cc]
        native_tex[side] = set(stem)
    foreign = {"IraqiFlag.tga", "DPRK_Flag.tga"}
    report = []
    for cc, side in CC_SIDE.items():
        blk_lines = [f"Faction: {side}"]
        ok_all = True
        seen: dict[str, str] = {}
        for _n, b in packed_data:
            if not _n.lower().endswith(".ini"):
                continue
            t = b.decode("latin1", errors="replace")
            for oname, start, end in parse_objects(t):
                oblk = t[start:end]
                if object_side(oname, oblk) != side:
                    continue
                typ = classify(oname)
                if typ is None or typ in seen:
                    continue
                status = "PASS"
                for mm in re.finditer(r"(?im)^\s*Model\s*=\s*(\S+)\s*$", oblk):
                    w = p_art.get(jf.norm(f"Art\\W3D\\{mm.group(1)}.W3D").lower())
                    if w is None:
                        continue
                    texs = set(re.findall(rb"[A-Za-z0-9_]+\.(?:tga|dds)", w))
                    bad = {x.decode() for x in texs} & foreign - native_tex.get(side, set())
                    if bad:
                        status = f"FAIL foreign {sorted(bad)} in {mm.group(1)}"
                        ok_all = False
                seen[typ] = status
        for typ in ["Command Center", "War Factory", "Radar", "Power", "Supply", "Barracks", "Abbas"]:
            blk_lines.append(f"{typ} Flag: {seen.get(typ, 'n/a (no such building)')}")
        blk_lines.append(f"Result: {'PASS' if ok_all else 'FAIL'}")
        report.append("\n".join(blk_lines))
        if not ok_all:
            raise SystemExit(f"audit FAIL for {side}")

    lines = [
        "SPECTER1 BUILDING FLAGS 01",
        f"BASELINE_DATA_SHA256 = {EXPECTED_DATA_SHA}",
        f"NEW_DATA_SHA256 = {new_data_sha}",
        f"BASELINE_ART_SHA256 = {EXPECTED_ART_SHA}",
        f"NEW_ART_SHA256 = {new_art_sha}",
        "ART_MODE = add-only (no existing entry modified)",
        f"W3D_CLONES = {n_clones} (byte-identical except FLAG-mesh texture)",
        f"DATA_MODEL_SWAPS = {swap_count} Model= lines in {len(changed_files)} files",
        "GAMEPLAY_CHANGED = NO (Model= refs only; animations/hierarchy/names unchanged)",
        "PROTECTED_FACTIONS_UNCHANGED = YES (USA, Israel, China, Russia, Iran, Iraq, NorthKorea, NATO, Egypt)",
        "US_LINEAGE = house-color reference standard (no flag cloth in models; FPOLE is a camo pole)",
        "RADARS = flag-free dishes (Irq_P3/US_RadarSt/Nat_RadarSt), unchanged",
        "",
        "PER-FACTION x BUILDING AUDIT (no foreign flag texture in any Draw model):",
        "",
        *report,
        "",
        "INGAME_TESTED = NO",
    ]
    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 building flags 01

Continues from SPECTER1_FACTION_IDENTITY_COMPLETE_01. Forty per-faction
W3D clones give every repaired faction native 3D flags on its War
Factory, Power Plant, Supply Center, and Barracks: Iraq-lineage models
for India/Libya/Pakistan/Saudi Arabia/Syria/South Africa/UAE,
NK-lineage models for Japan/South Korea/Vietnam, plus irq_camp for all
ten. Clones are byte-identical except the FLAG01-03 texture name.
US-lineage buildings and radars carry no flag cloth in any faction
(house-color reference standard) and are unchanged. Protected
factions, gameplay, units, weapons, and animations unchanged.

INGAME_TESTED = NO
"""
    install = f"""{RELEASE_NAME}
==============================

Native 3D building flags on the identity-complete baseline.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
4. Launch Specter.

Checksums:
  DATA SHA256 {new_data_sha}
  ART  SHA256 {new_art_sha}

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
    sha_txt = (f"_SPEC_DATA_ONE.big  SHA256 {new_data_sha}\n"
               f"_SPEC_ART_ONE.big   SHA256 {new_art_sha}\n"
               f"{zpath.name}  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n")
    for dest in (OUT_DIR, WS_OUT):
        (dest / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    print(audit)
    print("ZIP", zpath, zpath.stat().st_size, zip_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
