#!/usr/bin/env python3
"""Repair MilitaryHQ_StockFactions.ini inside _SPEC_DATA_ONE.big.

Rebuilds the four stock-faction MilitaryHQ objects from the stable
AmericaCommandCenter core. Preserves faction assignments, DisplayNames,
CommandSets, balance, health/range and passive income. Removes inherited Iraqi
art/special-power logic and parser-breaking non-ASCII comments.
"""
from __future__ import annotations

import re
import shutil
import zipfile
from collections import Counter
from pathlib import Path

import build_specter_commandcenter_batch_fixed_big as common

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_AIRFORCEEXPANSION_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_MILITARYHQ_STOCK_FIXED"
TARGET = r"Data\INI\Object\Specter\PatchSystems\MilitaryHQ\MilitaryHQ_StockFactions.ini"
DONOR = r"Data\INI\Object\Specter\United States Of America\Buildings\CommandCenter.ini"
TREE = ROOT / "Data/INI/Object/Specter/PatchSystems/MilitaryHQ/MilitaryHQ_StockFactions.ini"

FACTIONS = ["America", "Russia", "China", "NorthKorea"]
KEEP_BEHAVIOR_TAGS = {
    "ModuleTag_PreorderCreate",
    "ModuleTag_11",
    "ModuleTag_13",
    "ModuleTag_14",
    "ModuleTag_15",
    "ModuleTag_16",
    "ModuleTag_18",
    "ModuleTag_30",
    "ModuleTag_31",
    "ModuleTag_KillMarker",
    "ModuleTag_KillMarker2",
}


def split_objects(text: str) -> dict[str, str]:
    starts = [
        (match.start(), match.group(1))
        for match in re.finditer(r"(?m)^Object\s+(\S+)", text)
    ]
    output: dict[str, str] = {}
    for index, (start, name) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(text)
        output[name] = text[start:end]
    return output


def extract_identity(block: str, faction: str) -> dict[str, str]:
    fields = {
        "object": r"(?m)^Object\s+(\S+)",
        "side": r"(?m)^\s*Side\s*=\s*(\S+)",
        "display": r"(?m)^\s*DisplayName\s*=\s*(\S+)",
        "commandset": r"(?m)^\s*CommandSet\s*=\s*(\S+)",
        "cost": r"(?m)^\s*BuildCost\s*=\s*(\S+)",
        "time": r"(?m)^\s*BuildTime\s*=\s*(\S+)",
        "health": r"(?m)^\s*MaxHealth\s*=\s*(\S+)",
        "vision": r"(?m)^\s*VisionRange\s*=\s*(\S+)",
        "shroud": r"(?m)^\s*ShroudClearingRange\s*=\s*(\S+)",
    }
    values: dict[str, str] = {}
    for key, pattern in fields.items():
        match = re.search(pattern, block)
        if not match:
            raise SystemExit(f"{faction}: missing {key}")
        values[key] = match.group(1)
    if values["object"] != f"{faction}_MilitaryHQ":
        raise SystemExit(f"{faction}: bad Object {values['object']}")
    if values["side"] != faction:
        raise SystemExit(f"{faction}: bad Side {values['side']}")
    if values["commandset"] != f"{faction}_MilitaryHQCommandSet":
        raise SystemExit(f"{faction}: bad CommandSet {values['commandset']}")
    return values


def filter_donor_behaviors(donor: str) -> str:
    lines = donor.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        match = re.match(r"^\s*Behavior\s*=\s*\S+\s+(\S+)", line)
        if not match:
            output.append(line)
            index += 1
            continue
        tag = match.group(1)
        block = [line]
        index += 1
        while index < len(lines):
            block.append(lines[index])
            if re.match(r"^\s*End\s*$", lines[index].split(";", 1)[0]):
                index += 1
                break
            index += 1
        if tag in KEEP_BEHAVIOR_TAGS:
            output.extend(block)
    return "\n".join(output) + "\n"


def clone_donor(donor: str, ident: dict[str, str]) -> str:
    text = donor.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.splitlines()
    while lines and (not lines[0].strip() or lines[0].lstrip().startswith(";")):
        lines.pop(0)
    text = filter_donor_behaviors("\n".join(lines) + "\n")
    text = text.replace(
        "Object AmericaCommandCenter",
        f"Object {ident['object']}",
        1,
    )
    substitutions = [
        (r"(?m)^(\s*Side\s*=\s*)America\s*$", ident["side"]),
        (r"(?m)^(\s*DisplayName\s*=\s*)OBJECT:\S+\s*$", ident["display"]),
        (
            r"(?m)^(\s*CommandSet\s*=\s*)AmericaCommandCenterCommandSet\s*$",
            ident["commandset"],
        ),
        (r"(?m)^(\s*BuildCost\s*=\s*)\S+", ident["cost"]),
        (r"(?m)^(\s*BuildTime\s*=\s*)\S+", ident["time"]),
        (r"(?m)^(\s*VisionRange\s*=\s*)\S+", ident["vision"]),
        (r"(?m)^(\s*ShroudClearingRange\s*=\s*)\S+", ident["shroud"]),
        (r"(?m)^(\s*MaxHealth\s*=\s*)\S+", ident["health"]),
        (r"(?m)^(\s*InitialHealth\s*=\s*)\S+", ident["health"]),
    ]
    for pattern, value in substitutions:
        text = re.sub(
            pattern,
            lambda match, replacement=value: match.group(1) + replacement,
            text,
            count=1,
        )

    income = (
        "  Behavior = AutoDepositUpdate ModuleTag_PatchOilIncome\n"
        "    DepositTiming       = 12000\n"
        "    DepositAmount       = 19\n"
        "    InitialCaptureBonus = 0\n"
        "  End\n"
    )
    text = re.sub(
        r"(?m)^(\s*Behavior\s*=\s*PreorderCreate\b)",
        income + r"\1",
        text,
        count=1,
    )
    header = (
        f"; SPECTER FIX - {ident['object']}\n"
        "; Donor: stable AmericaCommandCenter core structure\n"
        f"; Preserve: Side={ident['side']} / DisplayName / {ident['commandset']}\n"
        "; Preserve: faction balance, health/range and passive MilitaryHQ income\n"
        "; Remove: inherited Iraqi art and special-power modules\n\n"
    )
    text = header + text
    text = "".join(c if ord(c) < 128 else "?" for c in text)
    return text.replace("\n", "\r\n")


def extra_validation(text: str, identities: dict[str, dict[str, str]], label: str) -> list[str]:
    failures: list[str] = []
    if any(ord(c) > 127 for c in text):
        failures.append(f"{label}: non-ASCII")
    if re.search(
        r"Irq_Command|irq_comndcntr|Iraq_Adnan1|SUPERWEAPON_Iraqi|SUPERWEAPON_Iraq",
        text,
        re.I,
    ):
        failures.append(f"{label}: Iraqi clone token remains")
    objects = split_objects(text)
    if set(objects) != {f"{faction}_MilitaryHQ" for faction in FACTIONS}:
        failures.append(f"{label}: Object set mismatch {sorted(objects)}")
    for faction in FACTIONS:
        name = f"{faction}_MilitaryHQ"
        block = objects.get(name, "")
        ident = identities[faction]
        if not re.search(r"(?m)^\s*Draw\s*=\s*W3DModelDraw\b", block):
            failures.append(f"{label}: {name} Draw missing")
        shadows = re.findall(r"(?m)^\s*Shadow\s*=\s*(\S+)", block)
        if shadows != ["SHADOW_VOLUME"]:
            failures.append(f"{label}: {name} Shadow={shadows}")
        tags = re.findall(r"ModuleTag_\S+", block)
        duplicate_tags = [tag for tag, count in Counter(tags).items() if count > 1]
        if duplicate_tags:
            failures.append(f"{label}: {name} duplicate tags={duplicate_tags}")
        if ident["commandset"] not in block:
            failures.append(f"{label}: {name} CommandSet missing")
        if "AutoDepositUpdate ModuleTag_PatchOilIncome" not in block:
            failures.append(f"{label}: {name} income behavior missing")
        forbidden_types = (
            "OCLSpecialPower",
            "SpecialAbility",
            "SpectreGunshipDeploymentUpdate",
            "GrantScienceUpgrade",
            "GrantUpgradeCreate",
            "ObjectCreationUpgrade",
        )
        for behavior_type in forbidden_types:
            if re.search(rf"(?m)^\s*Behavior\s*=\s*{behavior_type}\b", block):
                failures.append(f"{label}: {name} forbidden behavior={behavior_type}")
    return failures


def main() -> int:
    entries = common.parse_big(SRC)
    by = {common.knorm(name): (name, raw) for name, raw in entries}
    entry_name, old_raw = by[common.knorm(TARGET)]
    old_text = old_raw.decode("utf-8", "strict")
    old_blocks = split_objects(old_text)
    identities = {
        faction: extract_identity(old_blocks[f"{faction}_MilitaryHQ"], faction)
        for faction in FACTIONS
    }
    donor = by[common.knorm(DONOR)][1].decode("utf-8", "strict")
    repaired_text = "\r\n".join(
        clone_donor(donor, identities[faction]).rstrip("\r\n")
        for faction in FACTIONS
    ) + "\r\n"
    repaired_raw = repaired_text.encode("ascii")

    candidate = [
        (name, repaired_raw if common.knorm(name) == common.knorm(TARGET) else raw)
        for name, raw in entries
    ]
    art_entries = common.parse_big(ART)
    failures: list[str] = []
    for faction in FACTIONS:
        block = split_objects(repaired_text)[f"{faction}_MilitaryHQ"]
        failures += common.validate_cc(
            block,
            expect_object=f"{faction}_MilitaryHQ",
            expect_side=faction,
            expect_cmd=f"{faction}_MilitaryHQCommandSet",
            entries=candidate,
            art_entries=art_entries,
            label=f"PREWRITE_{faction}",
        )
    failures += extra_validation(repaired_text, identities, "PREWRITE")
    if failures:
        print("PRE-WRITE VALIDATION FAILED")
        for failure in failures:
            print(" ", failure)
        return 1
    print("PASS pre-write validation objects=4")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    common.write_big(out_big, candidate)
    rebuilt = common.parse_big(out_big)
    rby = {common.knorm(name): (name, raw) for name, raw in rebuilt}
    embedded_name, embedded = rby[common.knorm(TARGET)]
    if embedded != repaired_raw:
        raise SystemExit("embedded bytes differ from repaired source")
    extracted_text = embedded.decode("ascii")
    failures = []
    for faction in FACTIONS:
        block = split_objects(extracted_text)[f"{faction}_MilitaryHQ"]
        failures += common.validate_cc(
            block,
            expect_object=f"{faction}_MilitaryHQ",
            expect_side=faction,
            expect_cmd=f"{faction}_MilitaryHQCommandSet",
            entries=rebuilt,
            art_entries=art_entries,
            label=f"EXTRACTED_{faction}",
        )
    failures += extra_validation(extracted_text, identities, "EXTRACTED")
    if failures:
        out_big.unlink(missing_ok=True)
        print("EXTRACTED VALIDATION FAILED - BIG deleted")
        for failure in failures:
            print(" ", failure)
        return 1

    rel = Path(*Path(embedded_name.replace("\\", "/")).parts)
    extract_path = OUT / "_EXTRACT_VERIFY" / rel
    extract_path.parent.mkdir(parents=True, exist_ok=True)
    extract_path.write_bytes(embedded)
    if extract_path.read_bytes() != repaired_raw:
        raise SystemExit("disk extract byte mismatch")

    old_by = {common.knorm(name): raw for name, raw in entries}
    changed = [name for name, raw in rebuilt if raw != old_by[common.knorm(name)]]
    if changed != [entry_name]:
        raise SystemExit(f"unrelated BIG entries changed: {changed}")

    TREE.write_bytes(repaired_raw)
    (OUT / "MilitaryHQ_StockFactions.ini").write_bytes(repaired_raw)
    big_sha = common.sha256_file(out_big)
    ini_sha = common.sha256_bytes(repaired_raw)
    big_size = out_big.stat().st_size
    report = (
        "SPECTER MILITARYHQ STOCK FACTIONS FIX - VERIFY REPORT\n"
        "=====================================================\n"
        "VERDICT: PASS\n"
        "Patched INSIDE: _SPEC_DATA_ONE.big\n"
        "Objects: America_MilitaryHQ, Russia_MilitaryHQ, China_MilitaryHQ, NorthKorea_MilitaryHQ\n"
        "Preserved: Side, DisplayName, faction CommandSet, cost/time, health/range, income\n"
        "Donor core: AmericaCommandCenter US_Command art/production/death structure\n"
        "Removed: Iraqi art and inherited Iraqi special-power modules\n"
        "Non-ASCII: 0\n"
        "Object/Draw/Shadow/ModuleTag/Behavior/CommandSet/End: PASS x4\n"
        "W3D/art/reference validation: PASS\n"
        "Extract-from-BIG byte match: PASS\n"
        "Unrelated BIG entries changed: 0\n"
        f"\nOld INI SHA256: {common.sha256_bytes(old_raw)}\n"
        f"New INI SHA256: {ini_sha}\n"
        f"BIG SHA256: {big_sha}\n"
        f"BIG SIZE: {big_size}\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT TEST\n"
        "====================\n"
        f"entry={embedded_name}\nsource_sha256={ini_sha}\n"
        f"embedded_sha256={common.sha256_bytes(embedded)}\n"
        f"extracted_sha256={common.sha256_bytes(extract_path.read_bytes())}\n"
        "byte_match=YES\nfull_validation=PASS\nunrelated_changed=0\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"MilitaryHQ_StockFactions.ini SHA256={ini_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER MILITARYHQ STOCK FACTIONS FIX\n"
        "=====================================\n\n"
        "MilitaryHQ_StockFactions.ini repaired inside _SPEC_DATA_ONE.big.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in (
            "HASHES.txt",
            "VERIFY_REPORT.txt",
            "README_INSTALL.txt",
            "EMBED_PROOF.txt",
            "MilitaryHQ_StockFactions.ini",
        ):
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_MILITARYHQ_STOCK_FIXED.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "MilitaryHQ_StockFactions.ini", "MilitaryHQ_StockFactions.ini")
        zf.write(extract_path, "EXTRACT_VERIFY/MilitaryHQ_StockFactions.ini")
        for name in ("VERIFY_REPORT.txt", "EMBED_PROOF.txt", "HASHES.txt", "README_INSTALL.txt"):
            zf.write(OUT / name, name)
    if final_dir.is_dir():
        shutil.copy2(zip_path, final_dir / "_SPEC_DATA_ONE_FINAL.zip")

    print(report)
    print("BIG", out_big, big_sha, big_size)
    print("ZIP", zip_path, common.sha256_file(zip_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
