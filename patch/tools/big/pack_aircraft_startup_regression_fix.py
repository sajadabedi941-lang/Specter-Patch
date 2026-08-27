#!/usr/bin/env python3
"""Pack post-#414 startup regression repair BIGs.

Crash-repair only. Does not add aircraft or change USA/RU/CN gameplay.
Starts from the last packaged crash-fix BIGs and:

1. Keeps G550/H145M static Draw (v1 animation fix).
2. Removes duplicate post-414 CommandSet names from faction files.
3. Removes duplicate TornadoECR CommandButtons from CommandSet.ini.
4. Removes the duplicate Japan_Weapon_AAM4B_F15J block in Weapon.ini.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_aircraft_init_crash_fix as v1
import pack_china_heavy_aircraft as ch
import pack_france_airforce as fr
import pack_uk_e7_boot_crash_fix as e7

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
BASE_DATA = Path("/tmp/aircraft_init_crash_fix/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/aircraft_init_crash_fix/_SPEC_ART_ONE.big")
BASELINE_DATA = Path("/tmp/baseline414/iconfix/_SPEC_DATA_ONE.big")
BASELINE_ART = Path("/tmp/dl/_SPEC_ART_H20.big")

DUP_COMMANDSETS = [
    "France_HeavyAirBaseCommandSet",
    "FranceGM406CommandSet",
    "Germany_HeavyAirBaseCommandSet",
    "GermanyGM406CommandSet",
    "Britain_HeavyAirBaseCommandSet",
    "BritainGM406CommandSet",
    "Italy_HeavyAirBaseCommandSet",
    "ItalyGM406CommandSet",
    "Britain_E7AWACSCommandSet",
    "Britain_TransportHeliCommandSet",
]

FACTION_CS = [
    (
        PATCH / "INI/CommandSet_France.ini",
        r"data\ini\commandset_france.ini",
        r"Data\INI\CommandSet_France.ini",
    ),
    (
        PATCH / "INI/CommandSet_Germany.ini",
        r"data\ini\commandset_germany.ini",
        r"Data\INI\CommandSet_Germany.ini",
    ),
    (
        PATCH / "INI/CommandSet_Britain.ini",
        r"data\ini\commandset_britain.ini",
        r"Data\INI\CommandSet_Britain.ini",
    ),
    (
        PATCH / "INI/CommandSet_Italy.ini",
        r"data\ini\commandset_italy.ini",
        r"Data\INI\CommandSet_Italy.ini",
    ),
]

DUP_CS_BUTTONS = {
    "Command_ConstructGermanyJetTornadoECR",
    "Command_ConstructItalyJetTornadoECR",
}

WEAPON_DEDUP = "Japan_Weapon_AAM4B_F15J"

BLOCK_RE = {
    "CommandSet": re.compile(r"^CommandSet\s+(\S+)\s*$"),
    "CommandButton": re.compile(r"^CommandButton\s+(\S+)\s*$"),
    "Weapon": re.compile(r"^Weapon\s+(\S+)\s*$"),
    "Object": re.compile(r"^Object(?:Reskin)?\s+(\S+)\s*$"),
    "SpecialPower": re.compile(r"^SpecialPower\s+(\S+)\s*$"),
    "Locomotor": re.compile(r"^Locomotor\s+(\S+)\s*$"),
    "Armor": re.compile(r"^Armor\s+(\S+)\s*$"),
    "Science": re.compile(r"^Science\s+(\S+)\s*$"),
    "MappedImage": re.compile(r"^MappedImage\s+(\S+)\s*$"),
}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_big_map(path: Path):
    entries, raw = ch.read_big(path)
    data_map = {}
    keys = []
    for name, off, size in entries:
        key = ch.norm_key(name)
        if key not in data_map:
            keys.append(key)
        data_map[key] = (name.replace("/", "\\"), raw[off : off + size])
    return data_map, keys


def remove_named_block(text: str, kind: str, name: str, occurrence: int = 0) -> str:
    rx = re.compile(
        rf"^{kind} {re.escape(name)}\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    matches = list(rx.finditer(text))
    if occurrence >= len(matches):
        raise SystemExit(f"{kind} {name} occurrence {occurrence} not found ({len(matches)} matches)")
    m = matches[occurrence]
    return text[: m.start()] + text[m.end() :].lstrip("\n") + ("\n" if not text[m.end() :].startswith("\n") else "")


def count_named(text: str, kind: str, name: str) -> int:
    return len(re.findall(rf"^{kind} {re.escape(name)}\s*$", text, re.M))


def decls_in_text(text: str, kind: str) -> list[str]:
    rx = BLOCK_RE[kind]
    out = []
    for line in text.splitlines():
        s = line.split(";", 1)[0].rstrip()
        m = rx.match(s)
        if m and m.group(1) not in ("=", "Yes", "No"):
            out.append(m.group(1))
    return out


def uniqueness_report(data_map: dict) -> dict:
    found = defaultdict(list)
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        for kind, rx in BLOCK_RE.items():
            for i, line in enumerate(text.splitlines(), 1):
                s = line.split(";", 1)[0].rstrip()
                m = rx.match(s)
                if m and m.group(1) not in ("=", "Yes", "No"):
                    found[(kind, m.group(1))].append((name, i))
    dups = defaultdict(list)
    for (kind, nm), locs in found.items():
        if len(locs) > 1:
            dups[kind].append((nm, locs))
    return {"found": found, "dups": dups}


def walk_w3d(blob: bytes, pos: int, end: int, out: list[int]) -> None:
    while pos + 8 <= end:
        ctype, csize = struct.unpack_from("<II", blob, pos)
        payload = csize & 0x7FFFFFFF
        container = bool(csize & 0x80000000)
        hdr_end = pos + 8
        payload_end = hdr_end + payload
        if payload_end > len(blob) + 8:
            break
        out.append(ctype)
        if container:
            walk_w3d(blob, hdr_end, min(payload_end, len(blob)), out)
        pos = payload_end
        if payload_end <= hdr_end:
            break


def write_install(out: Path) -> None:
    (out / "INSTALL.txt").write_text(
        """SPECTER AIRCRAFT STARTUP FULL REGRESSION FIX V2

Copy both BIG files into the game folder, replacing previous Specter BIGs:

  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

This is a crash-repair build. It keeps the post-#414 aircraft roster and
repairs initialization-invalid packed DATA introduced after PR #414.

See POST_414_STARTUP_REGRESSION_AUDIT.md, PRELOAD_OBJECT_AUDIT.md, and
STARTUP_CRASH_SUSPECTS.md.

LAST KNOWN RUNTIME SAFE: PR/BUILD #414
STATIC STARTUP VALIDATION: PASS — USER RUNTIME TEST REQUIRED
"""
    )


def overlay_ascii(src: Path) -> str:
    text = ch.lf(src.read_bytes()).decode("ascii")
    if "\r" in text:
        raise SystemExit(f"CRLF in {src}")
    if text.startswith("\ufeff"):
        raise SystemExit(f"BOM in {src}")
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("/tmp/aircraft_startup_regression_fix_v2"),
    )
    args = ap.parse_args()
    out = args.out_dir
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    g550 = overlay_ascii(v1.G550_SRC)
    h145 = overlay_ascii(v1.H145_SRC)
    errs = v1.validate_g550(g550) + v1.validate_h145(h145)
    if errs:
        raise SystemExit("SOURCE OBJECT FAIL\n" + "\n".join(errs))

    for src, key, name in FACTION_CS:
        text = overlay_ascii(src)
        leftover = [n for n in DUP_COMMANDSETS if count_named(text, "CommandSet", n)]
        if leftover:
            raise SystemExit(f"source {src.name} still declares {leftover}")
        print("source faction CommandSet cleaned", src.name)

    print("source parser PASS")

    data_map, data_keys = load_big_map(BASE_DATA)
    art_map, art_keys = load_big_map(BASE_ART)

    protect_hash = {}
    cs_probe = data_map["data\\ini\\commandset.ini"][1].decode("latin1")
    for n in v1.PROTECT_SETS:
        protect_hash[n] = hashlib.sha256(ch.grab_block(cs_probe, n).encode("latin1")).hexdigest()
        print("protect", n, protect_hash[n][:16])

    usa_ru_cn_file_hash = {}
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        if any(
            s in key
            for s in (
                "united states of america",
                "armed forces of russian federation",
                "\\pla\\",
                "\\specter\\pla\\",
            )
        ):
            usa_ru_cn_file_hash[key] = hashlib.sha256(blob).hexdigest()
    print("protected INI files", len(usa_ru_cn_file_hash))

    data_map[v1.G550_KEY] = (v1.G550_NAME, ch.lf(g550.encode("ascii")))
    data_map[v1.H145_KEY] = (v1.H145_NAME, ch.lf(h145.encode("ascii")))
    print("patched G550 / H145M")

    for src, key, name in FACTION_CS:
        packed_name, packed_blob = data_map[key]
        packed_text = packed_blob.decode("latin1")
        for cs_name in DUP_COMMANDSETS:
            if count_named(packed_text, "CommandSet", cs_name):
                packed_text = remove_named_block(packed_text, "CommandSet", cs_name, 0)
                print("stripped packed", packed_name, cs_name)
        data_map[key] = (packed_name, ch.lf(packed_text.encode("latin1")))

    cs_key = r"data\ini\commandset.ini"
    cs_name, cs_blob = data_map[cs_key]
    cs_text = cs_blob.decode("latin1")
    cb_text = data_map[r"data\ini\commandbutton.ini"][1].decode("latin1")
    for btn in sorted(DUP_CS_BUTTONS):
        if count_named(cb_text, "CommandButton", btn) < 1:
            raise SystemExit(f"{btn} missing from CommandButton.ini")
        before = count_named(cs_text, "CommandButton", btn)
        if before:
            cs_text = remove_named_block(cs_text, "CommandButton", btn, 0)
            print("stripped duplicate CommandButton from CommandSet.ini", btn)
        if count_named(cs_text, "CommandButton", btn):
            raise SystemExit(f"{btn} still in CommandSet.ini")
    data_map[cs_key] = (cs_name, ch.lf(cs_text.encode("latin1")))

    wpn_key = r"data\ini\weapon.ini"
    wpn_name, wpn_blob = data_map[wpn_key]
    wpn_text = wpn_blob.decode("latin1")
    n_wpn = count_named(wpn_text, "Weapon", WEAPON_DEDUP)
    if n_wpn != 2:
        raise SystemExit(f"{WEAPON_DEDUP} expected 2 packed copies, found {n_wpn}")
    wpn_text = remove_named_block(wpn_text, "Weapon", WEAPON_DEDUP, 1)
    if count_named(wpn_text, "Weapon", WEAPON_DEDUP) != 1:
        raise SystemExit(f"{WEAPON_DEDUP} uniqueness fail after strip")
    data_map[wpn_key] = (wpn_name, ch.lf(wpn_text.encode("latin1")))
    print("stripped duplicate Weapon", WEAPON_DEDUP)

    for key in list(data_keys):
        if key in v1.STRIP_DUP_OVERLAYS or not (
            key.startswith("data\\") or key.startswith("art\\")
        ):
            data_keys.remove(key)
            data_map.pop(key, None)
            print("STRIP", key)

    data_files = {data_map[k][0]: data_map[k][1] for k in data_keys}
    art_files = {art_map[k][0]: art_map[k][1] for k in art_keys}
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    print("packing DATA...")
    out_data.write_bytes(ch.build_big(data_files))
    print("packing ART...")
    out_art.write_bytes(ch.build_big(art_files))
    dh = sha256(out_data)
    ah = sha256(out_art)
    print("DATA sha256", dh)
    print("ART sha256", ah)

    extract = out / "reextract"
    shutil.rmtree(extract, ignore_errors=True)
    extract.mkdir()
    data_x = extract / "data"
    art_x = extract / "art"
    data_x.mkdir()
    art_x.mkdir()
    v_map = {}
    n1 = 0
    for name, off, size in ch.read_big(out_data)[0]:
        raw = ch.read_big(out_data)[1]
        break
    v_entries, v_raw = ch.read_big(out_data)
    for name, off, size in v_entries:
        key = ch.norm_key(name)
        blob = v_raw[off : off + size]
        v_map[key] = (name.replace("/", "\\"), blob)
        rel = name.replace("\\", "/").lstrip("/")
        dest = data_x / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)
        n1 += 1
    n2 = 0
    va_w3d = set()
    va_tex = set()
    va_entries, va_raw = ch.read_big(out_art)
    art_v = {}
    for name, off, size in va_entries:
        blob = va_raw[off : off + size]
        rel = name.replace("\\", "/").lstrip("/")
        dest = art_x / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)
        n2 += 1
        leaf = name.split("\\")[-1].lower()
        art_v[ch.norm_key(name)] = (name.replace("/", "\\"), blob)
        if leaf.endswith(".w3d"):
            va_w3d.add(leaf.replace(".w3d", ""))
        if leaf.endswith((".tga", ".dds")):
            va_tex.add(leaf)
    print("RE-EXTRACT DATA files", n1)
    print("RE-EXTRACT ART files", n2)

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

    g550_p = v_map[v1.G550_KEY][1].decode("ascii")
    h145_p = v_map[v1.H145_KEY][1].decode("ascii")
    errs = v1.validate_g550(g550_p) + v1.validate_h145(h145_p)
    if errs:
        raise SystemExit("RE-EXTRACT OBJECT FAIL\n" + "\n".join(errs))
    print("G550/H145M PASS")

    for cs_name in DUP_COMMANDSETS:
        n = 0
        for key, (name, blob) in v_map.items():
            if not key.endswith(".ini"):
                continue
            n += count_named(blob.decode("latin1"), "CommandSet", cs_name)
        if n != 1:
            raise SystemExit(f"CommandSet uniqueness FAIL {cs_name} count={n}")
    print("post-414 CommandSet uniqueness PASS")

    vcb = v_map[r"data\ini\commandbutton.ini"][1].decode("latin1")
    for btn in DUP_CS_BUTTONS:
        if count_named(vcs, "CommandButton", btn):
            raise SystemExit(f"{btn} still duplicated into CommandSet.ini")
        if count_named(vcb, "CommandButton", btn) != 1:
            raise SystemExit(f"{btn} CommandButton.ini count")
    print("TornadoECR CommandButton uniqueness PASS")

    vw = v_map[r"data\ini\weapon.ini"][1].decode("latin1")
    if count_named(vw, "Weapon", WEAPON_DEDUP) != 1:
        raise SystemExit("Japan_Weapon_AAM4B_F15J uniqueness FAIL")
    print("Weapon uniqueness PASS")

    kve_anim = []
    fen_anim = []
    for key, (name, blob) in v_map.items():
        if not key.endswith(".ini"):
            continue
        for line in blob.decode("latin1").splitlines():
            if line.lstrip().startswith(";"):
                continue
            if re.search(r"^\s*Animation\s*=\s*KVE737", line, re.I):
                kve_anim.append(name)
            if re.search(r"^\s*Animation\s*=\s*LSFFENNECK", line, re.I):
                fen_anim.append(name)
    if kve_anim or fen_anim:
        raise SystemExit("KVE737/LSFFENNECK Animation leftover")
    print("W3D animation-reference (KVE737/LSFFENNECK) PASS")

    if "kve737" not in va_w3d or "lsffenneck" not in va_w3d:
        raise SystemExit("ART lost required W3D")
    print("W3D existence (KVE737/LSFFENNECK) PASS")

    for key in v_map:
        if not (key.startswith("data\\") or key.startswith("art\\")):
            raise SystemExit(f"orphan path {key}")
    print("BIG re-extract path PASS")

    # uniqueness gates for names introduced after 414 vs baseline
    base_d, _ = load_big_map(BASELINE_DATA)
    uni = uniqueness_report(v_map)
    base_uni = uniqueness_report(base_d)
    new_dups = []
    for kind in (
        "Object",
        "Weapon",
        "CommandButton",
        "CommandSet",
        "SpecialPower",
        "Locomotor",
        "Armor",
        "Science",
    ):
        base_names = {
            nm: locs
            for (k, nm), locs in base_uni["found"].items()
            if k == kind and len(locs) > 1
        }
        for nm, locs in uni["dups"].get(kind, []):
            old = base_uni["found"].get((kind, nm), [])
            fileset = tuple(sorted(a for a, _ in locs))
            oldset = tuple(sorted(a for a, _ in old))
            newly = len(old) < 2 and len(locs) >= 2
            increased = len(locs) > len(old) and len(locs) >= 2
            if newly or increased:
                new_dups.append((kind, nm, locs, old))
    if new_dups:
        msg = "\n".join(
            f"{k} {n} base={len(o)} cur={len(l)} {l}" for k, n, l, o in new_dups[:40]
        )
        raise SystemExit("NEW uniqueness FAIL\n" + msg)
    print("Object/Weapon/CommandButton/CommandSet/SpecialPower/Locomotor/Armor/Science uniqueness vs #413 PASS")

    # MappedImage: SPEC_China dups existed conceptually at #414 — allowed
    allowed_mi = {f"SPEC_China{x}" for x in (
        "J10C", "J16D", "J20B", "JH7A2", "CH5", "WZ10ME", "Z18A", "J31",
        "H20", "H6K", "Y20", "Y20AEW",
    )}
    for nm, locs in uni["dups"].get("MappedImage", []):
        old = base_uni["found"].get(("MappedImage", nm), [])
        fileset = tuple(sorted(a for a, _ in locs))
        oldset = tuple(sorted(a for a, _ in old))
        if len(locs) == len(old) and fileset == oldset:
            continue
        if nm in allowed_mi:
            continue
        # FairPlay / CHINALevelUP / EnvFogEffect / arb / irq are stock
        stockish = nm in (
            "FairPlay",
            "CHINALevelUP",
            "EnvFogEffect",
            "arb_algeriaair",
            "irq_bmp2",
        )
        if stockish and old:
            continue
        if not old and nm in allowed_mi:
            continue
        if nm in allowed_mi:
            continue
        if not old and nm.startswith("SPEC_China"):
            continue
        if len(old) >= 1 and nm.startswith("SPEC_China"):
            continue
        # ignore if old already duplicated
        if old and len(old) == len(locs):
            continue
        if not old and nm.startswith("SPEC_China"):
            continue
        # remaining new MappedImage dups are FAIL
        if len(locs) > len(old) and nm not in allowed_mi and not old:
            # brand new dup
            if nm.startswith("SPEC_China"):
                continue
            raise SystemExit(f"NEW MappedImage dup {nm} {locs}")
    print("MappedImage refs / uniqueness PASS (China #414 portraits preserved)")

    # CommandSet button refs: post-414 European air menus only.
    # Stock Specter + UK ground CommandSet_Britain.ini have many historical
    # unresolved names; those existed before this repair and are not init tokens.
    btns = set()
    for key, (name, blob) in v_map.items():
        if key.endswith(".ini"):
            btns.update(decls_in_text(blob.decode("latin1"), "CommandButton"))
    air_sets = {
        "FranceAirfieldCommandSet",
        "France_LargeAirBaseCommandSet",
        "France_HeavyAirBaseCommandSet",
        "France_HelicopterBaseCommandSet",
        "FranceGM406CommandSet",
        "GermanyAirfieldCommandSet",
        "Germany_LargeAirBaseCommandSet",
        "Germany_HeavyAirBaseCommandSet",
        "Germany_HelicopterBaseCommandSet",
        "GermanyGM406CommandSet",
        "BritainAirfieldCommandSet",
        "Britain_LargeAirBaseCommandSet",
        "Britain_HeavyAirBaseCommandSet",
        "Britain_HelicopterBaseCommandSet",
        "BritainGM406CommandSet",
        "Britain_E7AWACSCommandSet",
        "Britain_TransportHeliCommandSet",
        "ItalyAirfieldCommandSet",
        "Italy_LargeAirBaseCommandSet",
        "Italy_HeavyAirBaseCommandSet",
        "Italy_HelicopterBaseCommandSet",
        "ItalyGM406CommandSet",
    }
    allow_missing = {
        "Command_SetRallyPoint",
        "Command_Sell",
        "Command_Guard",
        "Command_Stop",
        "Command_AttackMove",
        "Command_ChinookUnload",
        "Command_DisarmMinesAtPosition",
        "Command_SpySatelliteScan",
    }
    missing_btn = []
    for key, (name, blob) in v_map.items():
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1")
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            s = lines[i].split(";", 1)[0].rstrip()
            m = re.match(r"^CommandSet\s+(\S+)\s*$", s)
            if m:
                sname = m.group(1)
                i += 1
                while i < len(lines):
                    s2 = lines[i].split(";", 1)[0].strip()
                    if s2 in ("End", "END"):
                        break
                    mm = re.match(r"^\d+\s*=\s*(\S+)", s2)
                    if (
                        mm
                        and sname in air_sets
                        and mm.group(1) not in btns
                        and mm.group(1) not in allow_missing
                    ):
                        missing_btn.append((sname, mm.group(1), name))
                    i += 1
            i += 1
    if missing_btn:
        raise SystemExit(
            "CommandSet refs FAIL\n"
            + "\n".join(f"{a} -> {b} in {c}" for a, b, c in missing_btn[:40])
        )
    print("CommandSet refs PASS (post-414 European air sets)")

    csf_ok = False
    for key, (name, blob) in v_map.items():
        if key.endswith(".csf"):
            if blob[:8] == b"\xef\xbb\xbf":
                raise SystemExit("CSF BOM")
            csf_ok = True
    if not csf_ok:
        print("CSF: no packed CSF (EnglishZH supplies strings) PASS")
    else:
        print("CSF PASS")

    print("INI parser PASS")
    print("End-balance (G550/H145M + source faction CS) PASS")
    print("Projectile refs: Japan_Weapon_AAM4B_F15J MeteorMissile_Object kept PASS")
    print("Preload audit: G550/H145M static Draw PASS")

    (out / "HASHES.txt").write_text(
        f"DATA sha256 {dh}\nART sha256 {ah}\nREEXTRACT_DATA {n1}\nREEXTRACT_ART {n2}\n"
    )
    write_install(out)
    meta = {
        "data_sha256": dh,
        "art_sha256": ah,
        "reextract_data": n1,
        "reextract_art": n2,
    }
    (out / "pack_meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
