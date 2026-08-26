#!/usr/bin/env python3
"""UK E-7 boot-crash fix packer.

Base: current uk_f35_donor_tempest BIGs.
Replaces only BritainAircraftE7.ini and removes duplicate SpecialPower overlay.
Does not rewrite F-35, Tempest, other UK aircraft, or other factions.
ART BIG is copied unchanged.
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
E7_SRC = (
    ROOT
    / "patch/Data/INI/Object/Specter/British Armed Forces/Airforce/BritainAircraftE7.ini"
)
BASE_DATA = Path("/tmp/uk_f35_donor_tempest/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/uk_f35_donor_tempest/_SPEC_ART_ONE.big")

E7_KEY = r"data\ini\object\specter\british armed forces\airforce\britainaircrafte7.ini"
E7_NAME = r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainAircraftE7.ini"
DUP_SP_KEY = r"data\ini\specialpower_britainairforce.ini"

BLOCK_START = re.compile(
    r"^(Object|Draw|DefaultConditionState|ConditionState|ArmorSet|WeaponSet|"
    r"Body|Behavior|UnitSpecificSounds|Prerequisites|Locomotor)\b"
)


def balanced_end(text: str, label: str) -> list[str]:
    errors = []
    depth = 0
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith(";"):
            continue
        if s == "End":
            depth -= 1
            if depth < 0:
                errors.append(f"{label}:{i} extra End")
                depth = 0
            continue
        if BLOCK_START.match(s) or s.startswith("Behavior ") or s.startswith("Draw "):
            # Locomotor = SET_NORMAL is a one-liner, not a block
            if s.startswith("Locomotor ="):
                continue
            if s.startswith("CommandSet =") or s.startswith("Scale ="):
                continue
            depth += 1
    if depth != 0:
        errors.append(f"{label} unbalanced End leftover depth={depth}")
    return errors


def validate_e7(text: str) -> list[str]:
    errors = []
    if text.count("Object BritainAircraftE7") != 1:
        errors.append(f"Object BritainAircraftE7 count={text.count('Object BritainAircraftE7')}")
    if "\r" in text:
        errors.append("CRLF/CR in E-7 INI")
    if text.startswith("\ufeff"):
        errors.append("BOM in E-7 INI")
    if re.search(r"[^\x09\x0a\x0d\x20-\x7e]", text):
        errors.append("non-ASCII bytes in E-7 INI")
    errors.extend(balanced_end(text, "BritainAircraftE7"))
    if re.search(r"KindOf\s*=.*\bRADAR\b", text):
        errors.append("KindOf RADAR still present")
    if re.search(r"Animation\s*=", text):
        errors.append("Animation still present on KVE737")
    if "WeaponSet" in text:
        errors.append("E-7 still has WeaponSet")
    if "FireWeapon" in text:
        errors.append("E-7 still has FireWeapon")
    if "Model = KVE737" not in text:
        errors.append("E-7 lost KVE737 model")
    if "SPEC_BritainE7" not in text:
        errors.append("E-7 lost portrait")
    if "BuildCost = 4300" not in text:
        errors.append("E-7 cost changed")
    if "Britain_E7AWACSCommandSet" not in text:
        errors.append("E-7 lost scan CommandSet")
    if "Britain_SpecialPower_E7Scan" not in text:
        errors.append("E-7 lost scan SpecialPower")
    if "StealthDetectorUpdate" not in text:
        errors.append("E-7 lost stealth detector")
    if "D30-F6_JetLocomotor" not in text:
        errors.append("E-7 lost AIR locomotor")
    if "CAN_ATTACK" in text:
        errors.append("E-7 KindOf still CAN_ATTACK")
    tags = re.findall(r"ModuleTag_\S+", text)
    if len(tags) != len(set(tags)):
        errors.append(f"duplicate module tags {tags}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/uk_e7_boot_crash_fix"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    e7 = ch.lf(E7_SRC.read_bytes()).decode("ascii")
    errors = validate_e7(e7)
    if errors:
        raise SystemExit("E-7 SOURCE FAIL\n" + "\n".join(errors))
    fr.parse_check({E7_NAME: e7.encode("ascii")})
    print("E-7 source parser PASS")

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

    if E7_KEY not in data_map:
        raise SystemExit("packed DATA missing BritainAircraftE7.ini")
    old_e7 = data_map[E7_KEY][1]
    new_e7 = ch.lf(E7_SRC.read_bytes())
    if old_e7 == new_e7:
        raise SystemExit("E-7 packed bytes unchanged; fix not applied")
    data_map[E7_KEY] = (E7_NAME, new_e7)
    print(f"replaced E-7 INI {len(old_e7)} -> {len(new_e7)} bytes")

    removed_dup_sp = False
    if DUP_SP_KEY in data_map:
        data_keys = [k for k in data_keys if k != DUP_SP_KEY]
        del data_map[DUP_SP_KEY]
        removed_dup_sp = True
        print("removed duplicate SpecialPower_BritainAirforce.ini")

    sp_text = data_map["data\\ini\\specialpower.ini"][1].decode("latin1")
    if "SpecialPower Britain_SpecialPower_E7Scan" not in sp_text:
        raise SystemExit("Weapon/SpecialPower.ini missing Britain_SpecialPower_E7Scan")
    if sp_text.count("SpecialPower Britain_SpecialPower_E7Scan") != 1:
        raise SystemExit("duplicate Britain_SpecialPower_E7Scan in SpecialPower.ini")

    cs_text = data_map["data\\ini\\commandset.ini"][1].decode("latin1")
    cb_text = data_map["data\\ini\\commandbutton.ini"][1].decode("latin1")
    if "CommandSet Britain_E7AWACSCommandSet" not in cs_text:
        raise SystemExit("CommandSet.ini missing Britain_E7AWACSCommandSet")
    if cs_text.count("CommandSet Britain_E7AWACSCommandSet") != 1:
        raise SystemExit("duplicate Britain_E7AWACSCommandSet")
    if "CommandButton Command_Britain_E7Scan" not in cs_text and "CommandButton Command_Britain_E7Scan" not in cb_text:
        raise SystemExit("Command_Britain_E7Scan not declared")
    if "Command_ConstructBritainAircraftE7" not in ch.grab_block(cs_text, "Britain_HeavyAirBaseCommandSet"):
        raise SystemExit("E-7 construct button missing from heavy airbase")
    ch.validate_commandset_button_refs(cs_text, cb_text)
    print("CommandButton/CommandSet PASS")

    # Unique Object BritainAircraftE7 across entire DATA tree
    obj_hits = []
    obj_balance_errors = []
    for key in data_keys:
        name, blob = data_map[key]
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1")
        for m in re.finditer(r"^Object\s+BritainAircraftE7\b", text, re.M):
            obj_hits.append(name)
        if "\\object\\" in key:
            obj_balance_errors.extend(balanced_end(text, name)[:3])
    if obj_hits != [E7_NAME]:
        raise SystemExit(f"Object BritainAircraftE7 hits={obj_hits}")
    print("Object BritainAircraftE7 unique PASS")
    if obj_balance_errors:
        print("Object tree End-balance notes:", len(obj_balance_errors))
        # packed stock INI uses many one-liners; do not fail the whole tree on
        # heuristic depth. E-7 itself already passed validate_e7.
    e7_errors = validate_e7(new_e7.decode("ascii"))
    if e7_errors:
        raise SystemExit("PACKED E-7 FAIL\n" + "\n".join(e7_errors))

    # Confirm F-35 / Tempest overlays untouched in this DATA rewrite except E-7/SP.
    for key, label in (
        (r"data\ini\object\specter\british armed forces\airforce\britainjetf35b.ini", "F-35B"),
        (r"data\ini\object\specter\british armed forces\airforce\britainjettempest.ini", "Tempest"),
    ):
        if key not in data_map:
            raise SystemExit(f"missing {label}")
        # still present from base tempest pack
        print(label, "present size", len(data_map[key][1]))

    out_data_map = {data_map[k][0]: data_map[k][1] for k in data_keys}
    out_art_map = {art_map[k][0]: art_map[k][1] for k in art_keys}
    data_big = ch.build_big(out_data_map)
    art_big = art_raw  # preserve current working ART bytes exactly
    # Verify ART reconstruction identity: rebuild from map should match if unchanged.
    art_rebuilt = ch.build_big(out_art_map)
    if hashlib.sha256(art_rebuilt).digest() != hashlib.sha256(art_big).digest():
        # keep original ART file bytes to guarantee identical ART BIG
        print("ART map rebuild differs from original file; keeping original ART bytes")
    else:
        art_big = art_rebuilt

    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_big)
    out_art.write_bytes(art_big)

    v_data_entries, v_data_raw = ch.read_big(out_data)
    v_art_entries, v_art_raw = ch.read_big(out_art)
    v_data = {ch.norm_key(n): (n, v_data_raw[off : off + size]) for n, off, size in v_data_entries}
    if E7_KEY not in v_data:
        raise SystemExit("re-extract missing E-7")
    packed_e7 = v_data[E7_KEY][1].decode("ascii")
    Path("/tmp/e7_crash/reextract_e7.ini").write_text(packed_e7, encoding="ascii")
    e7_errors = validate_e7(packed_e7)
    if e7_errors:
        raise SystemExit("RE-EXTRACT E-7 FAIL\n" + "\n".join(e7_errors))
    hits = []
    for key, (name, blob) in v_data.items():
        if re.search(rb"^Object\s+BritainAircraftE7\b", blob, re.M):
            hits.append(name)
    if hits != [E7_NAME]:
        raise SystemExit(f"re-extract Object BritainAircraftE7 hits={hits}")
    if DUP_SP_KEY in {ch.norm_key(n) for n, _off, _sz in v_data_entries}:
        raise SystemExit("re-extract still has duplicate SpecialPower overlay")
    sp = v_data["data\\ini\\specialpower.ini"][1].decode("latin1")
    if sp.count("SpecialPower Britain_SpecialPower_E7Scan") != 1:
        raise SystemExit("re-extract SpecialPower E7Scan count fail")
    if b"ENF35A" not in v_data[r"data\ini\object\specter\british armed forces\airforce\britainjetf35b.ini"][1]:
        raise SystemExit("F-35B overlay missing after E-7 pack")
    if b"SPEC_OLD_F35" not in v_data[r"data\ini\object\specter\british armed forces\airforce\britainjettempest.ini"][1]:
        raise SystemExit("Tempest overlay missing after E-7 pack")
    print("RE-EXTRACT VERIFY PASS")
    print("Object BritainAircraftE7 count = 1")
    print("duplicate SpecialPower overlay removed =", removed_dup_sp)

    install = (
        "Copy _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big into the Specter Data folder.\n"
        "Keep EnglishZH.big and AudioZH.big unchanged.\n"
        "UK E-7 Wedgetail boot-crash fix only.\n"
        "Does not change F-35, Tempest, or other factions.\n"
        "ART BIG is unchanged from uk-f35-donor-tempest-v1.\n"
    )
    zpath = out / "UK_E7_BOOT_CRASH_FIX.zip"
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
    report = out / "PACK_REPORT.txt"
    report.write_text(
        f"DATA sha256 {data_sha}\n"
        f"ART  sha256 {art_sha}\n"
        f"DATA bytes {len(data_big)}\n"
        f"ART  bytes {len(art_big)}\n"
        "ROOT CAUSE: KindOf RADAR (invalid, unique in DATA) + Animation KVE737.KVE737 "
        "(KVE737.W3D has no animation; PRELOAD loads it at parse).\n"
        "Also removed duplicate SpecialPower_BritainAirforce.ini (E7Scan already in SpecialPower.ini).\n"
        "britaniaircraftE7.ini PASS\n"
        "Object parser PASS\n"
        "Weapon references PASS (E-7 has none)\n"
        "SpecialPower references PASS\n"
        "CommandButton references PASS\n"
        "CommandSet references PASS\n"
        "Object BritainAircraftE7 count=1\n"
        "ART preserved from uk-f35-donor-tempest-v1\n"
        "F-35B/Tempest overlays untouched\n",
        encoding="ascii",
    )
    print(report.read_text())
    print("wrote", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
