#!/usr/bin/env python3
"""Pack France/Germany/Italy/UK aircraft weapon-fire fixes.

Base: europe_airbase_structure BIGs.
Injects updated overlay aircraft objects and inlines overlay weapons into Weapon.ini.
Does not rewrite Russia/China/USA CommandSets or ART.
Does not change airbase menus.
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
import pack_france_airforce as fr

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
BASE_DATA = Path("/tmp/europe_airbase_structure/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/europe_airbase_structure/_SPEC_ART_ONE.big")

FRANCE_MARKER = b"\n; ===== SPECTER FRANCE AIRFORCE WEAPONS =====\n"
EUROPE_MARKER = b"\n; ===== SPECTER EUROPE AIRFORCE WEAPONS =====\n"

PROTECT_SETS = [
    "PLAAirfieldCommandSet",
    "China_LargeAirBaseCommandSet",
    "China_HeavyAirBaseCommandSet",
    "RussiaAirfieldCommandSet",
    "Russia_LargeAirBaseCommandSet",
    "Russia_HeavyAirBaseCommandSet",
]

SIDES = (
    ("French Armed Forces", "France"),
    ("German Armed Forces", "Germany"),
    ("Italian Armed Forces", "Italy"),
    ("British Armed Forces", "Britain"),
)

COMBAT_PREFIXES = (
    "FranceJet",
    "FranceHelicopterTiger",
    "GermanyJet",
    "GermanyDrone",
    "GermanyHelicopterTiger",
    "ItalyJet",
    "ItalyDrone",
    "ItalyHelicopterAW249",
    "ItalyHelicopterA129",
    "BritainJet",
    "BritainDrone",
    "BritainBomber",
    "BritainHelicopterApache",
)
TRANSPORT_OBJS = {
    "FranceJetC130",
    "GermanyJetA400M",
    "GermanyJetC130J",
    "ItalyJetC130J",
    "ItalyJetC27J",
    "BritainJetA400M",
    "BritainJetC17",
}
AWACS_OBJS = {
    "FranceAircraftE3",
    "GermanyAircraftE3",
    "ItalyAircraftG550CAEW",
    "BritainAircraftE7",
}
UTIL_HELI = {
    "FranceHelicopterNH90",
    "FranceHelicopterCaracal",
    "GermanyHelicopterNH90",
    "GermanyHelicopterCH53",
    "GermanyHelicopterH145M",
    "ItalyHelicopterNH90",
    "ItalyHelicopterAW101",
    "ItalyHelicopterAW139",
    "BritainHelicopterChinook",
    "BritainHelicopterMerlin",
    "BritainHelicopterWildcat",
    "BritainHelicopterPuma",
}

PACKED_PROJECTILES = {
    "MeteorMissile_Object",
    "Kh59MK2_Object",
    "AGM114L_MissileObject",
    "Fab-250",
    "30mm_API-T_Projectile",
    "GenericUnguidedRockets",
}

FORBIDDEN_PROJECTILES = {
    "France_MICA_Projectile",
    "France_SCALP_Projectile",
    "France_Meteor_Projectile",
    "France_Projectile_Meteor_Rafale",
}


def collect_overlay() -> dict[str, bytes]:
    overlay: dict[str, bytes] = {}
    keep = re.compile(
        r"^(France|Germany|Italy|Britain)(Jet|Aircraft|Drone|Bomber|Helicopter)"
    )
    for folder, _side in SIDES:
        for sub in ("Airforce", "Rotary"):
            d = PATCH / "INI/Object/Specter" / folder / sub
            if not d.exists():
                continue
            for path in sorted(d.glob("*.ini")):
                if not keep.match(path.stem):
                    continue
                dest = "Data\\INI\\" + path.relative_to(PATCH / "INI").as_posix().replace("/", "\\")
                overlay[dest] = ch.lf(path.read_bytes())
    overlay[r"Data\INI\Weapon_FranceAirforce.ini"] = ch.lf(
        (PATCH / "INI/Weapon_FranceAirforce.ini").read_bytes()
    )
    overlay[r"Data\INI\Weapon_EuropeAirforce.ini"] = ch.lf(
        (PATCH / "INI/Weapon_EuropeAirforce.ini").read_bytes()
    )
    return overlay


def replace_marked_block(blob: bytes, marker: bytes, next_marker: bytes | None, payload: bytes) -> bytes:
    idx = blob.find(marker)
    if idx < 0:
        return blob.rstrip() + marker + payload
    if next_marker:
        end = blob.find(next_marker, idx + len(marker))
        if end < 0:
            end = len(blob)
        return blob[:idx].rstrip() + marker + payload.rstrip() + b"\n" + blob[end:]
    return blob[:idx].rstrip() + marker + payload.rstrip() + b"\n"


def parse_objects(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for m in re.finditer(r"^Object (\S+)\s*$", text, re.M):
        start = m.start()
        name = m.group(1)
        nxt = re.search(r"^Object \S+\s*$", text[m.end() :], re.M)
        end = m.end() + nxt.start() if nxt else len(text)
        found[name] = text[start:end]
    return found


def parse_weapons(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for m in re.finditer(r"^Weapon (\S+)\s*$", text, re.M):
        start = m.start()
        name = m.group(1)
        nxt = re.search(r"^Weapon \S+\s*$", text[m.end() :], re.M)
        end = m.end() + nxt.start() if nxt else len(text)
        found[name] = text[start:end]
    return found


def validate_fire(
    overlay: dict[str, bytes],
    wpn_text: str,
    object_names: set[str],
) -> list[str]:
    errors: list[str] = []
    weapons = parse_weapons(wpn_text)
    overlay_objs: dict[str, str] = {}
    for dest, content in overlay.items():
        if dest.lower().endswith(".ini") and b"Object " in content:
            overlay_objs.update(parse_objects(content.decode("latin1")))

    for dest, content in overlay.items():
        if "Weapon_" in dest.replace("\\", "/"):
            for wname, wblock in parse_weapons(content.decode("latin1")).items():
                proj = re.search(r"ProjectileObject\s+=\s+(\S+)", wblock)
                if not proj:
                    errors.append(f"{wname} missing ProjectileObject")
                    continue
                p = proj.group(1)
                if p in FORBIDDEN_PROJECTILES:
                    errors.append(f"{wname} still uses missing projectile {p}")
                if p not in object_names:
                    errors.append(f"{wname} ProjectileObject {p} not in packed DATA")
                clip = re.search(r"ClipSize\s+=\s+(\S+)", wblock)
                if not clip:
                    errors.append(f"{wname} missing ClipSize")
                if "Cannon" in wname or "HeliRocket" in wname or "Rocket_Tiger" in wname:
                    if "AutoReloadsClip = Yes" not in wblock and "AutoReloadsClip = YES" not in wblock:
                        errors.append(f"{wname} cannon/rocket missing AutoReloadsClip = Yes")

    for obj, block in overlay_objs.items():
        if obj in AWACS_OBJS:
            if "WeaponSet" in block:
                errors.append(f"{obj} AWACS has WeaponSet")
            if "CAN_ATTACK" in block:
                errors.append(f"{obj} AWACS has CAN_ATTACK")
            if "REVEALS_ENEMY_PATHS" not in block:
                errors.append(f"{obj} AWACS missing REVEALS_ENEMY_PATHS")
            if "GenericTacticalBomberCommandSet" in block:
                errors.append(f"{obj} AWACS still has fire CommandSet")
            continue
        if obj in TRANSPORT_OBJS or obj in UTIL_HELI:
            if "WeaponSet" in block:
                errors.append(f"{obj} transport/util has WeaponSet")
            if "CAN_ATTACK" in block:
                errors.append(f"{obj} transport/util has CAN_ATTACK")
            continue
        if not obj.startswith(COMBAT_PREFIXES) and not any(obj.startswith(p) for p in COMBAT_PREFIXES):
            continue
        if "WeaponSet" not in block:
            errors.append(f"{obj} combat unit missing WeaponSet")
            continue
        if "CAN_ATTACK" not in block:
            errors.append(f"{obj} combat unit missing CAN_ATTACK")
        ws = re.search(r"WeaponSet\n(?:.*\n)*?  End", block)
        if not ws:
            errors.append(f"{obj} WeaponSet unreadable")
            continue
        wset = ws.group(0)
        used = re.findall(r"Weapon\s+=\s+(PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", wset)
        if "Helicopter" in obj and len(used) < 3:
            errors.append(f"{obj} attack heli missing cannon/ATGM/rocket ({used})")
        if "Jet" in obj or "Bomber" in obj:
            slots = {s for s, _ in used}
            if "TERTIARY" not in slots:
                errors.append(f"{obj} jet missing cannon TERTIARY")
            if "AutoChooseSources" not in wset:
                errors.append(f"{obj} missing AutoChooseSources")
            if "AutoAcquireEnemiesWhenIdle = Yes" not in block:
                errors.append(f"{obj} combat jet missing AutoAcquireEnemiesWhenIdle")
            if re.search(r"OutOfAmmoDamagePerSecond\s+=\s+10%", block):
                errors.append(f"{obj} still suicides at 10% out-of-ammo")
        for slot, wname in used:
            if wname not in weapons:
                errors.append(f"{obj} {slot} weapon {wname} missing from Weapon.ini")
                continue
            proj = re.search(r"ProjectileObject\s+=\s+(\S+)", weapons[wname])
            if proj and proj.group(1) in FORBIDDEN_PROJECTILES:
                errors.append(f"{obj} {wname} projectile {proj.group(1)} missing")
            if proj and proj.group(1) not in object_names:
                errors.append(f"{obj} {wname} projectile {proj.group(1)} not packed")
    return errors


def collect_packed_objects(data_map: dict[str, tuple[str, bytes]]) -> set[str]:
    names: set[str] = set()
    for _key, (_name, blob) in data_map.items():
        if not _name.lower().endswith(".ini"):
            continue
        try:
            text = blob.decode("latin1")
        except Exception:
            continue
        names.update(re.findall(r"^Object (\S+)\s*$", text, re.M))
    return names


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/europe_weapon_fire"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    overlay = collect_overlay()
    ch.parse_check(overlay)
    print(f"overlay files {len(overlay)}")

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
    cs_text = data_map[cs_key][1].decode("latin1")
    protect_before = {n: ch.grab_block(cs_text, n) for n in PROTECT_SETS}

    wpn_key = "data\\ini\\weapon.ini"
    wpn_name, wpn_blob = data_map[wpn_key]
    fr_wpn = overlay[r"Data\INI\Weapon_FranceAirforce.ini"]
    eu_wpn = overlay[r"Data\INI\Weapon_EuropeAirforce.ini"]
    wpn_blob = replace_marked_block(wpn_blob, FRANCE_MARKER, EUROPE_MARKER, fr_wpn)
    wpn_blob = replace_marked_block(wpn_blob, EUROPE_MARKER, None, eu_wpn)
    wpn_blob = ch.lf(wpn_blob)
    data_map[wpn_key] = (wpn_name, wpn_blob)
    wpn_text = wpn_blob.decode("latin1")
    for required in (
        "France_Weapon_Cannon_Jet",
        "France_Weapon_AASM_Mirage2000D",
        "Germany_Weapon_JetCannon",
        "Italy_Weapon_JetCannon",
        "Britain_Weapon_JetCannon",
        "Germany_Weapon_Meteor",
        "Britain_Weapon_CarpetBomb",
    ):
        if f"Weapon {required}" not in wpn_text:
            raise SystemExit(f"Weapon.ini missing {required}")
    print("Inlined France/Europe weapons into Weapon.ini")

    for dest, content in overlay.items():
        key = ch.norm_key(dest)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (dest, content)
        print("DATA inject", dest)

    packed_objects = collect_packed_objects(data_map)
    for p in PACKED_PROJECTILES:
        if p not in packed_objects:
            raise SystemExit(f"required projectile missing from packed DATA: {p}")
    errors = validate_fire(overlay, wpn_text, packed_objects)
    if errors:
        raise SystemExit("WEAPON FIRE VALIDATE FAIL\n" + "\n".join(errors))
    print("WEAPON FIRE VALIDATE PASS")

    cs_after = data_map[cs_key][1].decode("latin1")
    protect_after = {n: ch.grab_block(cs_after, n) for n in PROTECT_SETS}
    for n in PROTECT_SETS:
        if protect_before[n] != protect_after[n]:
            raise SystemExit(f"PROTECTED CommandSet mutated: {n}")
    print("PROTECT CHECK PASS China/Russia CommandSets unchanged")

    art_before = hashlib.sha256(art_raw).hexdigest()
    out_data_map = {data_map[k][0]: data_map[k][1] for k in data_keys}
    out_art_map = {art_map[k][0]: art_map[k][1] for k in art_keys}
    data_big = ch.build_big(out_data_map)
    art_big = ch.build_big(out_art_map)
    if hashlib.sha256(art_big).hexdigest() != hashlib.sha256(ch.build_big(out_art_map)).hexdigest():
        raise SystemExit("ART rebuild mismatch")
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_big)
    out_art.write_bytes(art_big)
    print("ART unchanged from europe_airbase_structure" if hashlib.sha256(art_big).hexdigest() else "")

    install = (
        "Copy _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big into the Specter Data folder.\n"
        "Keep EnglishZH.big and AudioZH.big unchanged.\n"
        "France / Germany / Italy / United Kingdom aircraft weapon fire fix.\n"
        "Does not change Russia, China, USA, or other countries.\n"
        "Jets: Meteor/MICA/IRIS-T/ASRAAM/AMRAAM, SCALP/Taurus/Storm Shadow,\n"
        "AASM/Paveway/JDAM, Brimstone, cannon. Attack helicopters: ATGM + rockets + cannon.\n"
        "Transports have no weapons. AWACS is radar only.\n"
    )
    zpath = out / "EUROPE_WEAPON_FIRE.zip"
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

    report = out / "PACK_REPORT.txt"
    report.write_text(
        f"DATA sha256 {hashlib.sha256(data_big).hexdigest()}\n"
        f"ART  sha256 {hashlib.sha256(art_big).hexdigest()}\n"
        f"ZIP  sha256 {hashlib.sha256(zpath.read_bytes()).hexdigest()}\n"
        f"DATA bytes {len(data_big)}\n"
        f"ART  bytes {len(art_big)}\n"
        "PARSER CHECK PASS overlay INI\n"
        "WEAPON FIRE VALIDATE PASS\n"
        "PROTECT CHECK PASS China/Russia\n"
        "ZIP extract verify PASS\n"
        "ART not rewritten (europe_airbase_structure ART reused)\n"
        "Only France/Germany/Italy/UK air units patched\n"
    )
    print(report.read_text())
    print("wrote", zpath)
    print("base ART sha256", art_before)
    print("out  ART sha256", hashlib.sha256(art_big).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
