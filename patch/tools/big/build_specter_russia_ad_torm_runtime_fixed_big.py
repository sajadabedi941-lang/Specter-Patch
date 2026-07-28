#!/usr/bin/env python3
"""Repair Russia_AD_TorM.ini inside _SPEC_DATA_ONE.big.

Uses the complete working RussiaTankTorM2M object from the same DATA BIG as
the donor. Keeps Russia_AD_TorM identity, Side, DisplayName, cost/time,
health/range balance, build limit and Patch_Weapon_TorM role.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_AAB_GLOBAL_RUNTIME_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_RUSSIA_TORM_FIXED"
TARGET = r"Data\INI\Object\Specter\PatchSystems\AirDefense\Russia_AD_TorM.ini"
DONOR_FILE = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\TorM2M.ini"
TREE = ROOT / "Data/INI/Object/Specter/PatchSystems/AirDefense/Russia_AD_TorM.ini"

OPENERS = [
    re.compile(r"^\s*Object\s+(?![=])\S+"),
    re.compile(r"^\s*Draw\s*="),
    re.compile(r"^\s*Behavior\s*="),
    re.compile(r"^\s*Body\s*="),
    re.compile(r"^\s*ArmorSet\b"),
    re.compile(r"^\s*WeaponSet\b"),
    re.compile(r"^\s*Prerequisites\b"),
    re.compile(r"^\s*UnitSpecificSounds\b"),
    re.compile(r"^\s*DefaultConditionState\b"),
    re.compile(r"^\s*ConditionState\s*="),
    re.compile(r"^\s*TransitionState\s*="),
    re.compile(r"^\s*Turret\s*$"),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def knorm(name: str) -> str:
    return name.lower().replace("/", "\\")


def parse_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    entries = []
    pos = 16
    for _ in range(count):
        offset, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos = end + 1
        entries.append((name, data[offset : offset + size]))
    return entries


def write_big(path: Path, entries) -> None:
    header_size = 16 + sum(
        8 + len(name.encode("latin-1")) + 1 for name, _ in entries
    )
    while header_size % 4:
        header_size += 1
    cursor = header_size
    index = []
    for name, raw in entries:
        index.append((name, cursor, len(raw)))
        cursor += len(raw)
    output = bytearray(b"BIGF")
    output += struct.pack(">I", cursor)
    output += struct.pack(">I", len(entries))
    output += struct.pack(">I", header_size)
    for name, offset, size in index:
        output += struct.pack(">II", offset, size)
        output += name.encode("latin-1") + b"\x00"
    output += b"\x00" * (header_size - len(output))
    for _, raw in entries:
        output += raw
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(output))


def extract_object(file_text: str, object_name: str) -> str:
    lines = file_text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    start = next(
        (
            index
            for index, line in enumerate(lines)
            if re.match(rf"^Object\s+{re.escape(object_name)}\s*$", line)
        ),
        None,
    )
    if start is None:
        raise SystemExit(f"donor Object missing: {object_name}")
    depth = 0
    output: list[str] = []
    for line in lines[start:]:
        output.append(line)
        code = line.split(";", 1)[0]
        if re.match(r"^\s*End\s*$", code):
            depth -= 1
            if depth == 0:
                return "\n".join(output) + "\n"
            continue
        if any(regex.match(code) for regex in OPENERS):
            depth += 1
    raise SystemExit(f"donor Object unclosed: {object_name}")


def full_block_check(text: str) -> list[str]:
    stack: list[int] = []
    issues: list[str] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0]
        if not code.strip():
            continue
        if re.match(r"^\s*End\s*$", code):
            if not stack:
                issues.append(f"extra End @{line_no}")
            else:
                stack.pop()
            continue
        if any(regex.match(code) for regex in OPENERS):
            stack.append(line_no)
    if stack:
        issues.append(f"unclosed blocks opened at {stack}")
    return issues


def catalog(entries):
    cats: dict[str, set[str]] = defaultdict(set)
    patterns = {
        "Object": r"(?m)^Object\s+(?![=])(\S+)",
        "Weapon": r"(?m)^Weapon\s+(\S+)",
        "CommandSet": r"(?m)^CommandSet\s+(\S+)",
        "Armor": r"(?m)^Armor\s+(\S+)",
        "Science": r"(?m)^Science\s+(\S+)",
        "Locomotor": r"(?m)^Locomotor\s+(\S+)",
        "MappedImage": r"(?m)^MappedImage\s+(\S+)",
        "OCL": r"(?m)^ObjectCreationList\s+(\S+)",
    }
    for name, raw in entries:
        if not name.lower().endswith(".ini"):
            continue
        text = raw.decode("utf-8", "replace")
        for kind, pattern in patterns.items():
            cats[kind].update(re.findall(pattern, text))
    return cats


def validate(text: str, entries, art_entries, label: str) -> list[str]:
    failures = [f"{label}: {issue}" for issue in full_block_check(text)]
    if any(ord(c) > 127 for c in text):
        failures.append(f"{label}: non-ASCII")
    objects = re.findall(r"(?m)^Object\s+(\S+)", text)
    if objects != ["Russia_AD_TorM"]:
        failures.append(f"{label}: Objects={objects}")
    if not re.search(r"(?m)^\s*Side\s*=\s*Russia\s*$", text):
        failures.append(f"{label}: Side Russia missing")
    if not re.search(r"(?m)^\s*DisplayName\s*=\s*OBJECT:Russia_AD_TorM\s*$", text):
        failures.append(f"{label}: DisplayName missing")
    draws = re.findall(r"(?m)^\s*Draw\s*=\s*(\S+)", text)
    if draws != ["W3DTankDraw", "W3DModelDraw"]:
        failures.append(f"{label}: Draw modules={draws}")
    shadows = re.findall(r"(?m)^\s*Shadow\s*=\s*(\S+)", text)
    if shadows != ["SHADOW_VOLUME"]:
        failures.append(f"{label}: Shadow={shadows}")
    tags = re.findall(r"ModuleTag_\S+", text)
    duplicate_tags = [tag for tag, count in Counter(tags).items() if count > 1]
    if duplicate_tags:
        failures.append(f"{label}: duplicate ModuleTags={duplicate_tags}")
    if len(re.findall(r"(?m)^\s*WeaponSet\b", text)) != 1:
        failures.append(f"{label}: WeaponSet count invalid")
    if not re.search(
        r"(?m)^\s*Weapon\s*=\s*PRIMARY\s+Patch_Weapon_TorM\s*$",
        text,
    ):
        failures.append(f"{label}: Patch_Weapon_TorM missing")
    if not re.search(r"(?m)^\s*Behavior\s*=", text):
        failures.append(f"{label}: no Behavior")

    cats = catalog(entries)
    refs = {
        "Weapon": (
            re.findall(r"(?m)^\s*Weapon\s*=\s*(?:PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", text)
            + re.findall(r"(?m)^\s*Behavior\s*=\s*FireWeaponUpdate\s+\S+\n\s*Weapon\s*=\s*(\S+)", text)
        ),
        "CommandSet": re.findall(r"(?m)^\s*CommandSet\s*=\s*(\S+)", text),
        "Armor": re.findall(r"(?m)^\s*Armor\s*=\s*(\S+)", text),
        "Science": re.findall(r"(?m)^\s*Science\s*=\s*(\S+)", text),
        "Locomotor": re.findall(r"(?m)^\s*Locomotor\s*=\s*\S+\s+(\S+)", text),
        "MappedImage": re.findall(
            r"(?m)^\s*(?:SelectPortrait|ButtonImage)\s*=\s*(\S+)",
            text,
        ),
        "Object": re.findall(r"(?m)^\s*Object\s*=\s*(\S+)", text),
        "OCL": re.findall(r"(?m)^\s*OCL\s*=\s*(?:FINAL\s+)?(\S+)", text),
    }
    for kind, values in refs.items():
        for value in sorted(set(values)):
            if value not in cats[kind]:
                failures.append(f"{label}: unresolved {kind}={value}")

    art_stems = {
        Path(name.replace("\\", "/")).stem.lower()
        for name, _ in art_entries
        if name.lower().endswith(".w3d")
    }
    for model in sorted(set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text))):
        if model == "None":
            continue
        if model.lower() not in art_stems:
            failures.append(f"{label}: missing W3D={model}")
    return failures


def clone_donor(donor: str) -> str:
    text = donor.replace("Object RussiaTankTorM2M", "Object Russia_AD_TorM", 1)
    text = re.sub(r"(?m)^\s*BuildVariations\s*=.*\n", "", text, count=1)
    text = re.sub(
        r"(?m)^(\s*DisplayName\s*=\s*)\S+\s*$",
        r"\1OBJECT:Russia_AD_TorM",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(\s*Weapon\s*=\s*PRIMARY\s+)\S+\s*$",
        r"\1Patch_Weapon_TorM",
        text,
        count=1,
    )
    text = re.sub(r"(?m)^(\s*BuildCost\s*=\s*)\S+", r"\g<1>1529", text, count=1)
    text = re.sub(r"(?m)^(\s*BuildTime\s*=\s*)\S+", r"\g<1>14.9", text, count=1)
    text = re.sub(r"(?m)^(\s*VisionRange\s*=\s*)\S+", r"\g<1>300", text, count=1)
    text = re.sub(
        r"(?m)^(\s*ShroudClearingRange\s*=\s*)\S+",
        r"\g<1>260",
        text,
        count=1,
    )
    text = re.sub(r"(?m)^(\s*MaxHealth\s*=\s*)\S+", r"\g<1>420.0", text, count=1)
    text = re.sub(
        r"(?m)^(\s*InitialHealth\s*=\s*)\S+",
        r"\g<1>420.0",
        text,
        count=1,
    )
    # The stock donor references this OCL, but it has no definition in the
    # current DATA BIG. Debris is nonessential; remove the unresolved ref.
    text = re.sub(
        r"(?m)^\s*OCL\s*=\s*FINAL\s+OCL_RussiaTankECMDebris\s*\n",
        "",
        text,
        count=1,
    )
    text = re.sub(
        r"(?ms)^\s*Prerequisites\n.*?^\s*End\n",
        "  Prerequisites\n"
        "    Object = Russia_AdvancedAirBase\n"
        "    Science = SCIENCE_Rank3\n"
        "  End\n",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(\s*Side\s*=\s*Russia\s*)$",
        r"\1\n  MaxSimultaneousOfType = 10\n"
        r"  MaxSimultaneousLinkKey = Patch_AirDefense",
        text,
        count=1,
    )
    header = (
        "; SPECTER FIX - Russia_AD_TorM\n"
        "; Donor: complete working RussiaTankTorM2M from the same DATA BIG\n"
        "; Keep: Russia_AD_TorM / Side Russia / display / cost-time / health-range\n"
        "; Role: Patch_Weapon_TorM air and ballistic-missile defense\n"
        "; ASCII-only; patched and extract-verified inside _SPEC_DATA_ONE.big\n\n"
    )
    text = header + text
    text = "".join(c if ord(c) < 128 else "?" for c in text)
    return text.replace("\n", "\r\n")


def main() -> int:
    entries = parse_big(SRC)
    by = {knorm(name): (name, raw) for name, raw in entries}
    old_name, old_raw = by[knorm(TARGET)]
    donor_file = by[knorm(DONOR_FILE)][1].decode("utf-8", "strict")
    donor = extract_object(donor_file, "RussiaTankTorM2M")
    if full_block_check(donor):
        raise SystemExit(f"donor invalid: {full_block_check(donor)}")
    print("PASS RussiaTankTorM2M donor structure")

    fixed_text = clone_donor(donor)
    fixed_raw = fixed_text.encode("ascii")
    candidate = [
        (name, fixed_raw if knorm(name) == knorm(TARGET) else raw)
        for name, raw in entries
    ]
    art_entries = parse_big(ART)
    failures = validate(fixed_text, candidate, art_entries, "PREWRITE")
    if failures:
        print("PRE-WRITE VALIDATION FAILED")
        for failure in failures:
            print(" ", failure)
        return 1
    print("PASS pre-write validation")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    write_big(out_big, candidate)
    rebuilt = parse_big(out_big)
    rby = {knorm(name): (name, raw) for name, raw in rebuilt}
    embedded_name, embedded = rby[knorm(TARGET)]
    if embedded != fixed_raw:
        raise SystemExit("embedded bytes differ from repaired source")
    failures = validate(embedded.decode("ascii"), rebuilt, art_entries, "EXTRACTED")
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
    if extract_path.read_bytes() != fixed_raw:
        raise SystemExit("disk extract bytes differ")

    old_by = {knorm(name): raw for name, raw in entries}
    changed = [name for name, raw in rebuilt if raw != old_by[knorm(name)]]
    if changed != [old_name]:
        raise SystemExit(f"unrelated BIG entries changed: {changed}")

    TREE.write_bytes(fixed_raw)
    (OUT / "Russia_AD_TorM.ini").write_bytes(fixed_raw)
    big_sha = sha256_file(out_big)
    ini_sha = sha256_bytes(fixed_raw)
    big_size = out_big.stat().st_size
    report = (
        "SPECTER RUSSIA AD TOR-M FIX - VERIFY REPORT\n"
        "==========================================\n"
        "VERDICT: PASS\n"
        "Patched INSIDE: _SPEC_DATA_ONE.big\n"
        "Donor: RussiaTankTorM2M from current DATA BIG\n"
        "Identity: Russia_AD_TorM / Side Russia / OBJECT:Russia_AD_TorM\n"
        "Balance: cost=1529 time=14.9 health=420 vision=300 shroud=260\n"
        "Role: Patch_Weapon_TorM vs BALLISTIC_MISSILE AIRCRAFT\n"
        "Non-ASCII: 0\n"
        "Object/Draw/Shadow/ModuleTag/WeaponSet/Behavior/End: PASS\n"
        "W3D/art/weapon/armor/locomotor/prerequisite refs: PASS\n"
        "Extract-from-BIG byte match: PASS\n"
        "Unrelated BIG entries changed: 0\n"
        f"\nOld INI SHA256: {sha256_bytes(old_raw)}\n"
        f"New INI SHA256: {ini_sha}\n"
        f"BIG SHA256: {big_sha}\n"
        f"BIG SIZE: {big_size}\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT TEST\n"
        "====================\n"
        f"entry={embedded_name}\n"
        f"source_sha256={ini_sha}\n"
        f"embedded_sha256={sha256_bytes(embedded)}\n"
        f"extracted_sha256={sha256_bytes(extract_path.read_bytes())}\n"
        "byte_match=YES\nfull_validation=PASS\nunrelated_changed=0\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Russia_AD_TorM.ini SHA256={ini_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER RUSSIA AD TOR-M FIX\n"
        "==========================\n\n"
        "Russia_AD_TorM.ini repaired inside _SPEC_DATA_ONE.big.\n\n"
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
            "Russia_AD_TorM.ini",
        ):
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_RUSSIA_TORM_FIXED.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "Russia_AD_TorM.ini", "Russia_AD_TorM.ini")
        zf.write(extract_path, "EXTRACT_VERIFY/Russia_AD_TorM.ini")
        for name in ("VERIFY_REPORT.txt", "EMBED_PROOF.txt", "HASHES.txt", "README_INSTALL.txt"):
            zf.write(OUT / name, name)
    if final_dir.is_dir():
        shutil.copy2(zip_path, final_dir / "_SPEC_DATA_ONE_FINAL.zip")

    print(report)
    print("BIG", out_big, big_sha, big_size)
    print("ZIP", zip_path, sha256_file(zip_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
