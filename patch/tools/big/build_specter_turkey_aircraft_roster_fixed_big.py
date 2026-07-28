#!/usr/bin/env python3
"""Replace broken Turkey aircraft roster with validated faction donors.

Clones complete Object blocks from USA / Russia / China / NATO aircraft that
already exist inside _SPEC_DATA_ONE.big and have W3D art. Identity remaps to
Turkey_* Object names with Side=Turkey while preserving Turkey build prereqs,
cost/time and DisplayName. Dedupes Shadow, ASCII-only output.

Does not invent new art/weapons/locomotors — only references already-present
CommandSet / Weapon / Locomotor / Model assets from the donor objects.
"""
from __future__ import annotations

import re
import shutil
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import build_specter_aircraft_aab_global_fixed_big as base
import build_specter_turkey_faction_ini_batch_fixed_big as turkey_batch

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_FACTION_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_AIRCRAFT_ROSTER_FIXED"
TREE_ROOT = ROOT / "Data/INI/Object/Specter/Turkey Armed Forces"

USA = r"Data\INI\Object\Specter\United States Of America"
RUS = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
AAB = r"Data\INI\Object\Specter\PatchSystems\AdvancedAirBase\Aircraft_AAB_Global.ini"
NATO = r"Data\INI\Object\Specter\NATO"
TUR = r"Data\INI\Object\Specter\Turkey Armed Forces"

# target_entry, turkey_object, donor_entry, donor_object
REPLACEMENTS: list[tuple[str, str, str, str]] = [
    # USA preferred roster
    (rf"{TUR}\Airforce\Turkey_F16V.ini", "Turkey_F16V", rf"{USA}\Airforce\F16CM_BLK50_DB52.ini", "AmericaJetF-16C_AG"),
    (rf"{TUR}\Airforce\Turkey_F16Block70.ini", "Turkey_F16Block70", rf"{USA}\Airforce\F16CM_BLK50_DB52.ini", "AmericaJetF-16C_AG"),
    (rf"{TUR}\Airforce\Turkey_Hurjet.ini", "Turkey_Hurjet", rf"{USA}\Airforce\F15C.ini", "AmericaJetF-15E_AA"),
    (rf"{TUR}\Airforce\Turkey_KAAN.ini", "Turkey_KAAN", rf"{USA}\Airforce\F22A_AA.ini", "AmericaJetF-22A_AA"),
    (rf"{TUR}\Airforce\Turkey_Anka3.ini", "Turkey_Anka3", rf"{USA}\Airforce\F35C.ini", "AmericaJetF35C"),
    (rf"{TUR}\Airforce\Turkey_B2.ini", "Turkey_B2", AAB, "Patch_America_B2"),
    (rf"{TUR}\Airforce\Turkey_B52.ini", "Turkey_B52", rf"{USA}\ScienceObjects\B52H.ini", "AmericaJetB52"),
    (rf"{TUR}\Airforce\Turkey_AWACS.ini", "Turkey_AWACS", rf"{USA}\ScienceObjects\E3G.ini", "US_E3G_AWACS"),
    (rf"{TUR}\Airforce\Turkey_Akinci.ini", "Turkey_Akinci", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Airforce\Turkey_TB2.ini", "Turkey_TB2", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Airforce\Turkey_Tanker.ini", "Turkey_Tanker", AAB, "Patch_Turkey_KC135R"),
    (rf"{TUR}\Airforce\Turkey_Transport.ini", "Turkey_Transport", AAB, "Patch_Turkey_A400M"),
    # Russia
    (rf"{TUR}\Airforce\Turkey_Tu-22M3.ini", "Turkey_Tu-22M3", rf"{RUS}\Airforce\SU34M.ini", "RussiaJetSu34"),
    (rf"{TUR}\Airforce\Turkey_Tu-22M3_AI.ini", "Turkey_Tu-22M3_AI", rf"{RUS}\Airforce\SU34M.ini", "RussiaJetSu34"),
    (rf"{TUR}\Airforce\Turkey_Mig-29A.ini", "Turkey_Mig-29A", rf"{RUS}\Airforce\Mig35.ini", "RussiaJetMig35"),
    (rf"{TUR}\Airforce\Turkey_Mig-25BM.ini", "Turkey_Mig-25BM", rf"{RUS}\Airforce\MIG31K.ini", "RussiaJetMig31K"),
    (rf"{TUR}\Airforce\Turkey_Su-22M3.ini", "Turkey_Su-22M3", rf"{RUS}\Airforce\SU34M.ini", "RussiaJetSu34"),
    (rf"{TUR}\Airforce\Turkey_Su-24MK.ini", "Turkey_Su-24MK", rf"{RUS}\Airforce\Su35S_TS.ini", "RussiaJetSu35AG"),
    (rf"{TUR}\Airforce\Turkey_Su-25K.ini", "Turkey_Su-25K", rf"{RUS}\Airforce\SU57.ini", "RussiaJetSu57"),
    (rf"{TUR}\Airforce\Turkey_Su-24MR.ini", "Turkey_Su-24MR", rf"{RUS}\Airforce\Su35S.ini", "RussiaJetSu35S"),
    # China AAB-validated
    (rf"{TUR}\Airforce\Turkey_Mig-23BN.ini", "Turkey_Mig-23ML", AAB, "Patch_China_J10"),
    (rf"{TUR}\Airforce\Turkey_MirageF1-Bq.ini", "Turkey_MirageF1_Bq", AAB, "Patch_China_J20"),
    (rf"{TUR}\Airforce\Turkey_KAAN.ini", "Turkey_KAAN", rf"{USA}\Airforce\F22A_AA.ini", "AmericaJetF-22A_AA"),  # keep last wins noop
    # Helicopters (USA validated)
    (rf"{TUR}\Airforce\Turkey_Mi-28NE.ini", "Turkey_Mi-28NE", rf"{USA}\Airforce\AH64D.ini", "AmericaVehicleComanche"),
    (rf"{TUR}\Airforce\Turkey_Mi-35M3.ini", "Turkey_Mi-35M3", rf"{USA}\Airforce\AH64E.ini", "AmericaHelicopterAH64E"),
    (rf"{TUR}\Airforce\Turkey_Mi-8.ini", "Turkey_Mi-8T", rf"{USA}\Airforce\AH64E - Bk.ini", "AmericaHelicopterAH64E-BK"),
    (rf"{TUR}\Airforce\Turkey_T129.ini", "Turkey_T129", rf"{USA}\Airforce\AH64E.ini", "AmericaHelicopterAH64E"),
    # Drones
    (rf"{TUR}\Drones\Turkey_Kizilelma.ini", "Turkey_Kizilelma", rf"{USA}\Airforce\F22A_AG.ini", "AmericaJetStealthFighter"),
    (rf"{TUR}\Drones\Turkey_HeavyUAV.ini", "Turkey_HeavyUAV", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Turkey_StealthUAV.ini", "Turkey_StealthUAV", rf"{USA}\Airforce\F22A_AG.ini", "AmericaJetStealthFighter"),
    (rf"{TUR}\Drones\Ababil200.ini", "Turkey_Ababil200", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Ababil200R.ini", "TurkeyDronesAbabil200Recon", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Quds5.ini", "Turkey_Quds5", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Quds5_AI.ini", "TurkeyDroneQuds5_AI", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Sarab3.ini", "Turkey_Sarab3", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    # China J-16 on Su-24MR already Su35; add J16 via replacing Su-24MR? User asked J16 - use for Su-24MR instead:
]

# Deduplicate by target path (last mapping wins) — rebuild clean map.
_MAP: dict[str, tuple[str, str, str]] = {}
for target, tobj, dpath, dobj in REPLACEMENTS:
    _MAP[base.knorm(target)] = (target, tobj, dpath, dobj)

# Explicit final mapping (authoritative; overrides list order issues)
FINAL_MAP: list[tuple[str, str, str, str]] = [
    (rf"{TUR}\Airforce\Turkey_F16V.ini", "Turkey_F16V", rf"{USA}\Airforce\F16CM_BLK50_DB52.ini", "AmericaJetF-16C_AG"),
    (rf"{TUR}\Airforce\Turkey_F16Block70.ini", "Turkey_F16Block70", rf"{USA}\Airforce\F16CM_BLK50_DB52.ini", "AmericaJetF-16C_AG"),
    (rf"{TUR}\Airforce\Turkey_Hurjet.ini", "Turkey_Hurjet", rf"{USA}\Airforce\F15C.ini", "AmericaJetF-15E_AA"),
    (rf"{TUR}\Airforce\Turkey_KAAN.ini", "Turkey_KAAN", rf"{USA}\Airforce\F22A_AA.ini", "AmericaJetF-22A_AA"),
    (rf"{TUR}\Airforce\Turkey_Anka3.ini", "Turkey_Anka3", rf"{USA}\Airforce\F35C.ini", "AmericaJetF35C"),
    (rf"{TUR}\Airforce\Turkey_B2.ini", "Turkey_B2", AAB, "Patch_America_B2"),
    (rf"{TUR}\Airforce\Turkey_B52.ini", "Turkey_B52", rf"{USA}\ScienceObjects\B52H.ini", "AmericaJetB52"),
    (rf"{TUR}\Airforce\Turkey_AWACS.ini", "Turkey_AWACS", rf"{USA}\ScienceObjects\E3G.ini", "US_E3G_AWACS"),
    (rf"{TUR}\Airforce\Turkey_Akinci.ini", "Turkey_Akinci", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Airforce\Turkey_TB2.ini", "Turkey_TB2", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Airforce\Turkey_Tanker.ini", "Turkey_Tanker", AAB, "Patch_Turkey_KC135R"),
    (rf"{TUR}\Airforce\Turkey_Transport.ini", "Turkey_Transport", AAB, "Patch_Turkey_A400M"),
    (rf"{TUR}\Airforce\Turkey_Tu-22M3.ini", "Turkey_Tu-22M3", rf"{RUS}\Airforce\SU34M.ini", "RussiaJetSu34"),
    (rf"{TUR}\Airforce\Turkey_Tu-22M3_AI.ini", "Turkey_Tu-22M3_AI", rf"{RUS}\Airforce\SU34M.ini", "RussiaJetSu34"),
    (rf"{TUR}\Airforce\Turkey_Mig-29A.ini", "Turkey_Mig-29A", rf"{RUS}\Airforce\Mig35.ini", "RussiaJetMig35"),
    (rf"{TUR}\Airforce\Turkey_Mig-25BM.ini", "Turkey_Mig-25BM", rf"{RUS}\Airforce\MIG31K.ini", "RussiaJetMig31K"),
    (rf"{TUR}\Airforce\Turkey_Su-22M3.ini", "Turkey_Su-22M3", rf"{RUS}\Airforce\SU34M.ini", "RussiaJetSu34"),
    (rf"{TUR}\Airforce\Turkey_Su-24MK.ini", "Turkey_Su-24MK", rf"{RUS}\Airforce\Su35S_TS.ini", "RussiaJetSu35AG"),
    (rf"{TUR}\Airforce\Turkey_Su-25K.ini", "Turkey_Su-25K", rf"{RUS}\Airforce\SU57.ini", "RussiaJetSu57"),
    (rf"{TUR}\Airforce\Turkey_Su-24MR.ini", "Turkey_Su-24MR", AAB, "Patch_China_J16"),
    (rf"{TUR}\Airforce\Turkey_Mig-23BN.ini", "Turkey_Mig-23ML", AAB, "Patch_China_J10"),
    (rf"{TUR}\Airforce\Turkey_MirageF1-Bq.ini", "Turkey_MirageF1_Bq", AAB, "Patch_China_J20"),
    (rf"{TUR}\Airforce\Turkey_Mi-28NE.ini", "Turkey_Mi-28NE", rf"{USA}\Airforce\AH64D.ini", "AmericaVehicleComanche"),
    (rf"{TUR}\Airforce\Turkey_Mi-35M3.ini", "Turkey_Mi-35M3", rf"{USA}\Airforce\AH64E.ini", "AmericaHelicopterAH64E"),
    (rf"{TUR}\Airforce\Turkey_Mi-8.ini", "Turkey_Mi-8T", rf"{USA}\Airforce\AH64E - Bk.ini", "AmericaHelicopterAH64E-BK"),
    (rf"{TUR}\Airforce\Turkey_T129.ini", "Turkey_T129", rf"{USA}\Airforce\AH64E.ini", "AmericaHelicopterAH64E"),
    (rf"{TUR}\Drones\Turkey_Kizilelma.ini", "Turkey_Kizilelma", rf"{USA}\Airforce\F22A_AG.ini", "AmericaJetStealthFighter"),
    (rf"{TUR}\Drones\Turkey_HeavyUAV.ini", "Turkey_HeavyUAV", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Turkey_StealthUAV.ini", "Turkey_StealthUAV", rf"{USA}\Airforce\F22A_AG.ini", "AmericaJetStealthFighter"),
    (rf"{TUR}\Drones\Ababil200.ini", "Turkey_Ababil200", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Ababil200R.ini", "TurkeyDronesAbabil200Recon", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Quds5.ini", "Turkey_Quds5", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Quds5_AI.ini", "TurkeyDroneQuds5_AI", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Sarab3.ini", "Turkey_Sarab3", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
]


def extract_object(text: str, object_name: str) -> str:
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Object\s+(\S+)", text)]
    for i, (start, name) in enumerate(starts):
        if name == object_name:
            end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
            return text[start:end]
    raise SystemExit(f"Object {object_name} not found")


def extract_identity(old_text: str, object_name: str) -> dict[str, str]:
    try:
        block = extract_object(old_text, object_name)
    except SystemExit:
        # Some files use different primary names; fall back to first Object.
        objs = re.findall(r"(?m)^Object\s+(\S+)", old_text)
        if not objs:
            return {}
        block = extract_object(old_text, objs[0])
    out: dict[str, str] = {"object": object_name}
    for key, pat in {
        "side": r"(?m)^\s*Side\s*=\s*(\S+)",
        "display": r"(?m)^\s*DisplayName\s*=\s*(\S+)",
        "commandset": r"(?m)^\s*CommandSet\s*=\s*(\S+)",
        "cost": r"(?m)^\s*BuildCost\s*=\s*(\S+)",
        "time": r"(?m)^\s*BuildTime\s*=\s*(\S+)",
    }.items():
        m = re.search(pat, block)
        if m:
            out[key] = m.group(1)
    m = re.search(r"(?ms)^\s*Prerequisites\b.*?^\s*End\s*$", block)
    if m:
        out["prereq"] = m.group(0)
    sciences = re.findall(r"(?m)^\s*Science\s*=\s*(\S+)", block)
    if sciences:
        out["science"] = sciences[0]
    return out


def dedupe_shadow(text: str) -> str:
    seen = False
    lines: list[str] = []
    for line in text.splitlines():
        if re.match(r"^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", line):
            if seen:
                continue
            seen = True
        lines.append(line)
    return "\n".join(lines) + "\n"


def rewrite_prereq_to_turkey(prereq_block: str) -> str:
    block = prereq_block
    block = re.sub(
        r"(?m)^(\s*Object\s*=\s*).*$",
        r"\1Turkey_AdvancedAirBase",
        block,
        count=1,
    )
    return block


def clone_to_turkey(
    donor_block: str,
    *,
    donor_object: str,
    turkey_object: str,
    identity: dict[str, str],
    donor_label: str,
) -> str:
    text = donor_block.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(rf"(?m)^Object\s+{re.escape(donor_object)}\s*$", f"Object {turkey_object}", text, count=1)
    text = re.sub(r"(?m)^(  Side\s*=\s*)\S+\s*$", r"\1Turkey", text, count=1)
    # If Side missing (rare), inject after Object line
    if not re.search(r"(?m)^\s*Side\s*=", text):
        text = re.sub(
            rf"(?m)^(Object\s+{re.escape(turkey_object)}\s*)$",
            r"\1\n  Side = Turkey",
            text,
            count=1,
        )
    display = identity.get("display", f"OBJECT:{turkey_object}")
    if not re.search(r"(?m)^\s*DisplayName\s*=", text):
        text = re.sub(
            rf"(?m)^(Object\s+{re.escape(turkey_object)}\s*)$",
            rf"\1\n  DisplayName = {display}",
            text,
            count=1,
        )
    else:
        text = re.sub(r"(?m)^(  DisplayName\s*=\s*)\S+\s*$", rf"\1{display}", text, count=1)

    if "cost" in identity:
        if re.search(r"(?m)^\s*BuildCost\s*=", text):
            text = re.sub(r"(?m)^(  BuildCost\s*=\s*)\S+", rf"\g<1>{identity['cost']}", text, count=1)
    if "time" in identity:
        if re.search(r"(?m)^\s*BuildTime\s*=", text):
            text = re.sub(r"(?m)^(  BuildTime\s*=\s*)\S+", rf"\g<1>{identity['time']}", text, count=1)

    # Prerequisites: prefer old Turkey prereq block; else rewrite donor airfield to Turkey_AdvancedAirBase
    if "prereq" in identity:
        if re.search(r"(?ms)^\s*Prerequisites\b.*?^\s*End\s*$", text):
            text = re.sub(
                r"(?ms)^\s*Prerequisites\b.*?^\s*End\s*$",
                identity["prereq"].rstrip(),
                text,
                count=1,
            )
        else:
            # insert before KindOf if possible
            text = re.sub(
                r"(?m)^(\s*KindOf\s*=)",
                identity["prereq"].rstrip() + "\n\\1",
                text,
                count=1,
            )
    else:
        text = re.sub(
            r"(?ms)^\s*Prerequisites\b.*?^\s*End\s*$",
            lambda m: rewrite_prereq_to_turkey(m.group(0)),
            text,
            count=1,
        )

    # Keep old CommandSet when present (buttons/build queues already wired)
    if "commandset" in identity and re.search(r"(?m)^\s*CommandSet\s*=", text):
        text = re.sub(
            r"(?m)^(  CommandSet\s*=\s*)\S+",
            rf"\g<1>{identity['commandset']}",
            text,
            count=1,
        )

    # Preserve Turkey science gate when donor has a Science line
    if "science" in identity and re.search(r"(?m)^\s*Science\s*=", text):
        text = re.sub(r"(?m)^(\s*Science\s*=\s*)\S+", rf"\g<1>{identity['science']}", text, count=1)

    text = dedupe_shadow(text)
    text, _ = turkey_batch.remove_armor_set_flag(text)
    text, _ = turkey_batch.sanitize_ascii(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"

    header = (
        f"; SPECTER TURKEY AIRCRAFT ROSTER FIX - {turkey_object}\n"
        f"; Donor: {donor_label} / {donor_object}\n"
        f"; Identity: Object={turkey_object} Side=Turkey DisplayName={display}\n"
        "; Structure/weapons/locomotor/art from validated donor; no new assets\n\n"
    )
    return header + text


def catalog(entries):
    cats: dict[str, set[str]] = defaultdict(set)
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("utf-8", "replace")
        cats["Object"].update(re.findall(r"(?m)^Object\s+(?![=])(\S+)", t))
        cats["CommandSet"].update(re.findall(r"(?m)^CommandSet\s+(\S+)", t))
        cats["Weapon"].update(re.findall(r"(?m)^Weapon\s+(\S+)", t))
        cats["Science"].update(re.findall(r"(?m)^Science\s+(\S+)", t))
        cats["Upgrade"].update(re.findall(r"(?m)^Upgrade\s+(\S+)", t))
        cats["Armor"].update(re.findall(r"(?m)^Armor\s+(\S+)", t))
        cats["Locomotor"].update(re.findall(r"(?m)^Locomotor\s+(\S+)", t))
        cats["MappedImage"].update(re.findall(r"(?m)^MappedImage\s+(\S+)", t))
        cats["OCL"].update(re.findall(r"(?m)^ObjectCreationList\s+(\S+)", t))
    return cats


def validate_replaced(
    text: str,
    *,
    expect_object: str,
    entries,
    art_entries,
    label: str,
) -> list[str]:
    fails: list[str] = []
    cats = catalog(entries)
    data_join = b"\n".join(b for _, b in entries)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }

    if any(ord(c) > 127 for c in text):
        fails.append(f"{label}: non-ASCII")
    objs = re.findall(r"(?m)^Object\s+(\S+)", text)
    if expect_object not in objs:
        fails.append(f"{label}: missing Object {expect_object} (have {objs})")
    if objs != [expect_object]:
        # Allow only the primary Turkey object in replaced files
        fails.append(f"{label}: expected single Object [{expect_object}], got {objs}")
    if not re.search(r"(?m)^\s*Side\s*=\s*Turkey\s*$", text):
        fails.append(f"{label}: Side!=Turkey")
    if not re.search(r"(?m)^\s*Draw\s*=", text):
        fails.append(f"{label}: Draw missing")
    shadows = re.findall(r"(?m)^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", text)
    if len(shadows) > 1:
        fails.append(f"{label}: duplicate Shadow=SHADOW_VOLUME")
    if re.search(r"(?m)^\s*ArmorSetFlag\s*=", text):
        fails.append(f"{label}: ArmorSetFlag remains")
    if re.search(r"(?i)\b(Irq_|Iraq_Su|Adnan)\b", text):
        fails.append(f"{label}: Iraqi crash tokens remain")

    def need(kind: str, vals: list[str]) -> None:
        for v in vals:
            if v in ("None", "NONE"):
                continue
            if v not in cats[kind] and v.encode() not in data_join:
                fails.append(f"{label}: missing {kind}={v}")

    need("Weapon", re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", text))
    need("Weapon", re.findall(r"(?m)^\s*WeaponTemplate\s*=\s*(\S+)", text))
    need("CommandSet", re.findall(r"(?m)^\s*CommandSet\s*=\s*(\S+)", text))
    need("Armor", re.findall(r"(?m)^\s*Armor\s*=\s*(\S+)", text))
    need("Locomotor", re.findall(r"(?m)^\s*Locomotor\s*=\s*\S+\s+(\S+)", text))
    need("MappedImage", re.findall(r"(?m)^\s*(?:SelectPortrait|ButtonImage)\s*=\s*(\S+)", text))
    need("Science", re.findall(r"(?m)^\s*Science\s*=\s*(\S+)", text))
    need("Object", re.findall(r"(?m)^\s*Object\s*=\s*(\S+)", text))
    need(
        "Upgrade",
        re.findall(r"(?m)^\s*(?:UpgradeCameo\d*|TriggeredBy|UpgradeToGrant)\s*=\s*(\S+)", text),
    )
    for m in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)):
        if m in ("None", "NONE"):
            continue
        if m.lower() not in stems:
            fails.append(f"{label}: missing W3D Model={m}")
    return fails


def tree_path_for(entry_name: str) -> Path:
    parts = Path(entry_name.replace("\\", "/")).parts
    idx = list(parts).index("Turkey Armed Forces")
    return TREE_ROOT / Path(*parts[idx + 1 :])


def full_integrity_turkey_air(entries, art_entries) -> list[str]:
    """Validate every Turkey Airforce/Drones Turkey_* / drone object file."""
    fails: list[str] = []
    for name, raw in entries:
        n = name.replace("/", "\\")
        if "Turkey Armed Forces" not in n:
            continue
        if not (r"\Airforce\\" in n or r"\Drones\\" in n):
            continue
        if not n.lower().endswith(".ini"):
            continue
        text = raw.decode("utf-8", "replace")
        bn = Path(n.replace("\\", "/")).name
        fails.extend(turkey_batch.validate_turkey_file(text, name, "INTEGRITY"))
        # W3D check for all models
        stems = {
            Path(a.replace("\\", "/")).stem.lower()
            for a, _ in art_entries
            if a.lower().endswith(".w3d")
        }
        for m in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)):
            if m in ("None", "NONE"):
                continue
            if m.lower() not in stems:
                fails.append(f"INTEGRITY/{bn}: missing W3D Model={m}")
        if re.search(r"(?i)\b(Irq_|Iraq_Su|Adnan)\b", text):
            fails.append(f"INTEGRITY/{bn}: Iraqi tokens")
        sides = set(re.findall(r"(?m)^\s*Side\s*=\s*(\S+)", text))
        if sides and sides != {"Turkey"}:
            fails.append(f"INTEGRITY/{bn}: Side={sides}")
    return fails


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG: {SRC}")
    entries = base.parse_big(SRC)
    by = {base.knorm(n): (n, r) for n, r in entries}
    art_entries = base.parse_big(ART)

    repaired: dict[str, bytes] = {}
    report_rows: list[str] = []

    for target, turkey_object, donor_path, donor_object in FINAL_MAP:
        if base.knorm(target) not in by:
            raise SystemExit(f"missing target {target}")
        if base.knorm(donor_path) not in by:
            raise SystemExit(f"missing donor {donor_path}")
        t_name, t_raw = by[base.knorm(target)]
        d_name, d_raw = by[base.knorm(donor_path)]
        old_text = t_raw.decode("utf-8", "replace")
        donor_text = d_raw.decode("utf-8", "replace")
        identity = extract_identity(old_text, turkey_object)
        identity.setdefault("display", f"OBJECT:{turkey_object}")
        donor_block = extract_object(donor_text, donor_object)
        fixed = clone_to_turkey(
            donor_block,
            donor_object=donor_object,
            turkey_object=turkey_object,
            identity=identity,
            donor_label=Path(d_name.replace("\\", "/")).name,
        )
        repaired[base.knorm(target)] = fixed.encode("ascii")
        report_rows.append(
            f"{turkey_object} <= {donor_object} ({Path(d_name.replace('\\', '/')).name}) "
            f"sha={base.sha256_bytes(repaired[base.knorm(target)])}"
        )
        print(f"CLONED {turkey_object} from {donor_object}")

    candidate = [
        (name, repaired[base.knorm(name)] if base.knorm(name) in repaired else raw)
        for name, raw in entries
    ]

    # Pre-write validation
    failures: list[str] = []
    for target, turkey_object, _, _ in FINAL_MAP:
        text = repaired[base.knorm(target)].decode("ascii")
        failures.extend(
            validate_replaced(
                text,
                expect_object=turkey_object,
                entries=candidate,
                art_entries=art_entries,
                label=f"PREWRITE/{turkey_object}",
            )
        )
    if failures:
        print("PRE-WRITE FAILED")
        for f in failures[:100]:
            print(" ", f)
        return 1
    print(f"PASS pre-write replacements={len(FINAL_MAP)}")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, candidate)
    rebuilt = base.parse_big(out_big)
    rebuilt_by = {base.knorm(n): (n, r) for n, r in rebuilt}

    old_by = {base.knorm(n): r for n, r in entries}
    changed = [n for n, r in rebuilt if r != old_by[base.knorm(n)]]
    unexpected = [n for n in changed if base.knorm(n) not in repaired]
    if unexpected:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"unrelated entries changed: {unexpected[:20]}")

    extract_root = OUT / "_EXTRACT_VERIFY"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True)

    post: list[str] = []
    for target, turkey_object, _, _ in FINAL_MAP:
        emb_name, emb = rebuilt_by[base.knorm(target)]
        expected = repaired[base.knorm(target)]
        if emb != expected:
            post.append(f"byte mismatch {target}")
            continue
        rel = Path(*Path(emb_name.replace("\\", "/")).parts)
        ep = extract_root / rel
        ep.parent.mkdir(parents=True, exist_ok=True)
        ep.write_bytes(emb)
        tp = tree_path_for(emb_name)
        tp.parent.mkdir(parents=True, exist_ok=True)
        tp.write_bytes(expected)
        post.extend(
            validate_replaced(
                emb.decode("ascii"),
                expect_object=turkey_object,
                entries=rebuilt,
                art_entries=art_entries,
                label=f"EXTRACT/{turkey_object}",
            )
        )

    integ = full_integrity_turkey_air(rebuilt, art_entries)
    post.extend(integ)
    if post:
        out_big.unlink(missing_ok=True)
        print("POST VALIDATION FAILED - BIG deleted")
        for f in post[:120]:
            print(" ", f)
        return 1

    big_sha = base.sha256_file(out_big)
    big_size = out_big.stat().st_size
    print(f"CHANGED={len(changed)} BIG SHA256={big_sha} SIZE={big_size}")

    focus_dir = OUT / "replaced"
    focus_dir.mkdir(exist_ok=True)
    for target, turkey_object, _, _ in FINAL_MAP:
        (focus_dir / f"{turkey_object}.ini").write_bytes(repaired[base.knorm(target)])

    verify = (
        "SPECTER TURKEY AIRCRAFT ROSTER REPLACE - VERIFY REPORT\n"
        "=====================================================\n"
        "VERDICT: PASS\n"
        "Patched INSIDE: _SPEC_DATA_ONE.big\n"
        f"Aircraft/drone objects replaced: {len(FINAL_MAP)}\n"
        "Donors: USA F-16/F-15/F-22/F-35/B-2/B-52/AWACS/MQ-9/AH-64/Comanche; "
        "Russia Su-57/Su-35/Su-34/MiG-35/MiG-31; China J-20/J-10/J-16 (AAB)\n"
        "Side=Turkey preserved; Object tokens preserved for CommandButtons\n"
        "Weapon/Locomotor/CommandSet/Model deps from validated donors only\n"
        "Full Turkey Airforce+Drones integrity check: PASS\n"
        "Extract-from-BIG byte match: PASS\n"
        "Unrelated BIG entries changed: 0\n\n"
        "Replacements:\n"
        + "\n".join(f"- {row}" for row in report_rows)
        + f"\n\nBIG SHA256: {big_sha}\nBIG SIZE: {big_size}\nFINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(verify, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT + INTEGRITY\n"
        "===========================\n"
        f"replaced={len(FINAL_MAP)}\n"
        f"changed={len(changed)}\n"
        "byte_match=YES\nintegrity=PASS\nunrelated_changed=0\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER TURKEY AIRCRAFT ROSTER REPLACE\n"
        "=====================================\n\n"
        "Broken/unstable Turkey aircraft replaced with validated USA/Russia/China\n"
        "donor objects (Side=Turkey, Turkey_* Object names preserved).\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )
    (OUT / "REPLACEMENTS.txt").write_text("\n".join(report_rows) + "\n", encoding="ascii")

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in ("HASHES.txt", "VERIFY_REPORT.txt", "README_INSTALL.txt", "EMBED_PROOF.txt"):
            srcp = OUT / name if name != "HASHES.txt" else None
            if name == "HASHES.txt":
                continue
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_TURKEY_AIRCRAFT_ROSTER_FIXED.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "REPLACEMENTS.txt",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"_SPEC_DATA_ONE_TURKEY_AIRCRAFT_ROSTER_FIXED.zip SHA256={zip_sha}\n"
        f"replaced={len(FINAL_MAP)}\n",
        encoding="ascii",
    )
    if final_dir.is_dir():
        shutil.copy2(OUT / "HASHES.txt", final_dir / "HASHES.txt")
        shutil.copy2(OUT / "EMBED_PROOF.txt", final_dir / "EMBED_PROOF.txt")
    print(f"ZIP SHA256={zip_sha}")
    print("FINAL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
