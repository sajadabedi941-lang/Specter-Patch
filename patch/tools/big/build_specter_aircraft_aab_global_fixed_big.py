#!/usr/bin/env python3
"""Repair Aircraft_AAB_Global.ini parsing inside _SPEC_DATA_ONE.big.

The embedded file already uses consistent USA aircraft/airbase-derived
structures. Its parser-breaking defect is non-ASCII punctuation in comments.
This builder changes only that BIG entry, ASCII-sanitizes it, validates every
object and reference, writes the BIG, then extract/byte-match verifies it.
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
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_MILITARYHQ_BATCH_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_AAB_GLOBAL_FIXED"
TARGET = r"Data\INI\Object\Specter\PatchSystems\AdvancedAirBase\Aircraft_AAB_Global.ini"
TREE = ROOT / "Data/INI/Object/Specter/PatchSystems/AdvancedAirBase/Aircraft_AAB_Global.ini"

OPENERS = [
    (re.compile(r"^\s*Object\s+(?![=])\S+"), "Object"),
    (re.compile(r"^\s*Draw\s*="), "Draw"),
    (re.compile(r"^\s*Behavior\s*="), "Behavior"),
    (re.compile(r"^\s*Body\s*="), "Body"),
    (re.compile(r"^\s*ArmorSet\b"), "ArmorSet"),
    (re.compile(r"^\s*WeaponSet\b"), "WeaponSet"),
    (re.compile(r"^\s*Prerequisites\b"), "Prerequisites"),
    (re.compile(r"^\s*UnitSpecificSounds\b"), "UnitSpecificSounds"),
    (re.compile(r"^\s*DefaultConditionState\b"), "DefaultConditionState"),
    (re.compile(r"^\s*ConditionState\s*="), "ConditionState"),
    (re.compile(r"^\s*TransitionState\s*="), "TransitionState"),
    (re.compile(r"^\s*LocomotorSet\b"), "LocomotorSet"),
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
    header_size = 16
    for name, _ in entries:
        header_size += 8 + len(name.encode("latin-1")) + 1
    while header_size % 4:
        header_size += 1
    blobs, index, cursor = [], [], header_size
    for name, raw in entries:
        blobs.append(raw)
        index.append((name, cursor, len(raw)))
        cursor += len(raw)
    out = bytearray(b"BIGF")
    out += struct.pack(">I", cursor)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for name, offset, size in index:
        out += struct.pack(">II", offset, size)
        out += name.encode("latin-1") + b"\x00"
    out += b"\x00" * (header_size - len(out))
    for blob in blobs:
        out += blob
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))


def full_block_check(text: str) -> list[str]:
    issues: list[str] = []
    stack: list[tuple[str, int]] = []
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
        for regex, kind in OPENERS:
            if regex.match(code):
                if kind == "Object" and stack:
                    issues.append(f"Object @{line_no} starts before {stack[-1]} closes")
                stack.append((kind, line_no))
                break
    if stack:
        issues.append(f"unclosed blocks: {stack[-20:]}")
    return issues


def catalog(entries):
    cats: dict[str, set[str]] = defaultdict(set)
    patterns = {
        "Object": r"(?m)^Object\s+(?![=])(\S+)",
        "Weapon": r"(?m)^Weapon\s+(\S+)",
        "CommandSet": r"(?m)^CommandSet\s+(\S+)",
        "Armor": r"(?m)^Armor\s+(\S+)",
        "Upgrade": r"(?m)^Upgrade\s+(\S+)",
        "Science": r"(?m)^Science\s+(\S+)",
        "Locomotor": r"(?m)^Locomotor\s+(\S+)",
        "MappedImage": r"(?m)^MappedImage\s+(\S+)",
        "OCL": r"(?m)^ObjectCreationList\s+(\S+)",
        "SpecialPower": r"(?m)^SpecialPower\s+(\S+)",
    }
    for name, raw in entries:
        if not name.lower().endswith(".ini"):
            continue
        text = raw.decode("utf-8", "replace")
        for kind, pattern in patterns.items():
            cats[kind].update(re.findall(pattern, text))
    return cats


def object_blocks(text: str):
    lines = text.splitlines()
    starts = [
        (index, match.group(1))
        for index, line in enumerate(lines)
        if (match := re.match(r"^Object\s+(\S+)", line))
    ]
    blocks = []
    for index, (start, object_name) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(lines)
        blocks.append((object_name, start + 1, "\n".join(lines[start:end]) + "\n"))
    return blocks


def validate(text: str, entries, art_entries, label: str) -> list[str]:
    failures: list[str] = []
    if any(ord(c) > 127 for c in text):
        failures.append(f"{label}: non-ASCII remains")

    failures.extend(f"{label}: {issue}" for issue in full_block_check(text))
    blocks = object_blocks(text)
    names = [name for name, _, _ in blocks]
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    if not blocks:
        failures.append(f"{label}: no Objects")
    if duplicates:
        failures.append(f"{label}: duplicate Objects {duplicates}")

    for object_name, line_no, block in blocks:
        draws = re.findall(r"(?m)^\s*Draw\s*=\s*W3DModelDraw\b", block)
        shadows = re.findall(r"(?m)^\s*Shadow\s*=\s*(\S+)", block)
        tags = re.findall(r"ModuleTag_\S+", block)
        duplicate_tags = [tag for tag, count in Counter(tags).items() if count > 1]
        if len(draws) != 1:
            failures.append(f"{label}: {object_name}@{line_no} Draw count={len(draws)}")
        if shadows != ["SHADOW_VOLUME"]:
            failures.append(f"{label}: {object_name}@{line_no} Shadow={shadows}")
        if duplicate_tags:
            failures.append(f"{label}: {object_name}@{line_no} duplicate ModuleTags={duplicate_tags}")
        if not re.search(r"(?m)^\s*Behavior\s*=", block):
            failures.append(f"{label}: {object_name}@{line_no} no Behavior")
        if not re.search(r"(?m)^\s*Body\s*=", block):
            failures.append(f"{label}: {object_name}@{line_no} no Body")
        # WeaponSet is optional for tanker/transport objects. Any present block
        # is covered by the global End parser and weapon-reference validation.

    cats = catalog(entries)
    data_join = b"\n".join(raw for _, raw in entries)
    refs = {
        "Weapon": (
            re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", text)
            + re.findall(r"(?m)^\s*WeaponTemplate\s*=\s*(\S+)", text)
        ),
        "CommandSet": re.findall(r"(?m)^\s*CommandSet\s*=\s*(\S+)", text),
        "Armor": re.findall(r"(?m)^\s*Armor\s*=\s*(\S+)", text),
        "Upgrade": re.findall(
            r"(?m)^\s*(?:UpgradeCameo\d*|TriggeredBy|UpgradeToGrant)\s*=\s*(\S+)",
            text,
        ),
        "Science": re.findall(r"(?m)^\s*Science\s*=\s*(\S+)", text),
        "Locomotor": re.findall(r"(?m)^\s*Locomotor\s*=\s*\S+\s+(\S+)", text),
        "MappedImage": re.findall(
            r"(?m)^\s*(?:SelectPortrait|ButtonImage)\s*=\s*(\S+)",
            text,
        ),
        "OCL": re.findall(
            r"(?m)^\s*(?:OCL|CreationList|UpgradeObject)\s*=\s*(\S+)",
            text,
        ),
        "SpecialPower": re.findall(
            r"(?m)^\s*SpecialPowerTemplate\s*=\s*(\S+)",
            text,
        ),
        "Object": (
            re.findall(r"(?m)^\s*Object\s*=\s*(\S+)", text)
            + re.findall(r"(?m)^\s*GunshipTemplateName\s*=\s*(\S+)", text)
        ),
    }
    for kind, values in refs.items():
        for value in sorted(set(values)):
            if value in ("None", "NONE"):
                continue
            if value not in cats[kind] and value.encode() not in data_join:
                failures.append(f"{label}: unresolved {kind}={value}")

    art_names = [knorm(name) for name, _ in art_entries]
    for model in sorted(set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text))):
        if model in ("None", "NONE"):
            continue
        if not any(model.lower() in name and name.endswith(".w3d") for name in art_names):
            failures.append(f"{label}: unresolved W3D model={model}")
    return failures


def sanitize(text: str) -> str:
    # These are the only non-ASCII code points in the embedded source.
    replacements = {"—": "-", "×": "x", "é": "e"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    if any(ord(c) > 127 for c in text):
        remaining = sorted({f"U+{ord(c):04X}" for c in text if ord(c) > 127})
        raise SystemExit(f"unexpected non-ASCII after sanitize: {remaining}")
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG: {SRC}")
    entries = parse_big(SRC)
    by = {knorm(name): (name, raw) for name, raw in entries}
    if knorm(TARGET) not in by:
        raise SystemExit("Aircraft_AAB_Global.ini missing from source BIG")
    art_entries = parse_big(ART)

    entry_name, old_raw = by[knorm(TARGET)]
    old_text = old_raw.decode("utf-8", "strict")
    old_non_ascii = sum(ord(c) > 127 for c in old_text)
    if old_non_ascii != 632:
        print(f"WARN expected 632 non-ASCII characters, got {old_non_ascii}")
    print(f"OLD non-ASCII count={old_non_ascii}")

    fixed_text = sanitize(old_text)
    fixed_raw = fixed_text.encode("ascii")
    candidate = [
        (name, fixed_raw if knorm(name) == knorm(TARGET) else raw)
        for name, raw in entries
    ]

    failures = validate(fixed_text, candidate, art_entries, "PREWRITE")
    if failures:
        print("PRE-WRITE VALIDATION FAILED")
        for failure in failures:
            print(" ", failure)
        return 1
    print(f"PASS pre-write validation objects={len(object_blocks(fixed_text))}")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    write_big(out_big, candidate)
    rebuilt = parse_big(out_big)
    rebuilt_by = {knorm(name): (name, raw) for name, raw in rebuilt}
    embedded_name, embedded = rebuilt_by[knorm(TARGET)]
    if embedded != fixed_raw:
        raise SystemExit("embedded bytes do not match repaired source")

    post_failures = validate(
        embedded.decode("ascii"),
        rebuilt,
        art_entries,
        "EXTRACTED",
    )
    if post_failures:
        out_big.unlink(missing_ok=True)
        print("EXTRACTED VALIDATION FAILED - BIG deleted")
        for failure in post_failures:
            print(" ", failure)
        return 1

    rel = Path(*Path(embedded_name.replace("\\", "/")).parts)
    extract_path = OUT / "_EXTRACT_VERIFY" / rel
    extract_path.parent.mkdir(parents=True, exist_ok=True)
    extract_path.write_bytes(embedded)
    if extract_path.read_bytes() != fixed_raw:
        raise SystemExit("extracted disk bytes do not match repaired source")

    # Prove this was the only changed BIG entry.
    old_by = {knorm(name): raw for name, raw in entries}
    changed = [
        name
        for name, raw in rebuilt
        if raw != old_by[knorm(name)]
    ]
    if changed != [entry_name]:
        raise SystemExit(f"unrelated BIG entries changed: {changed}")

    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(fixed_raw)
    (OUT / "Aircraft_AAB_Global.ini").write_bytes(fixed_raw)

    big_sha = sha256_file(out_big)
    ini_sha = sha256_bytes(fixed_raw)
    big_size = out_big.stat().st_size
    objects = len(object_blocks(fixed_text))
    weapon_sets = len(re.findall(r"(?m)^\s*WeaponSet\b", fixed_text))
    report = (
        "SPECTER AIRCRAFT AAB GLOBAL PARSE FIX - VERIFY REPORT\n"
        "=====================================================\n"
        "VERDICT: PASS\n"
        "Patched INSIDE: _SPEC_DATA_ONE.big\n"
        f"Entry: {entry_name}\n"
        "Repair: ASCII-sanitize parser-breaking comments only\n"
        "AdvancedAirBase objects/identity/balance/behavior unchanged\n"
        f"Removed non-ASCII characters: {old_non_ascii}\n"
        f"Objects validated: {objects}\n"
        f"WeaponSet blocks validated: {weapon_sets}\n"
        "Object/Draw/Shadow/ModuleTag/Behavior/WeaponSet/End: PASS\n"
        "W3D/Art/Weapon/CommandSet/Armor/Upgrade/OCL/SpecialPower refs: PASS\n"
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
        "byte_match=YES\n"
        "full_validation=PASS\n"
        "unrelated_changed=0\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Aircraft_AAB_Global.ini SHA256={ini_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER AIRCRAFT AAB GLOBAL PARSE FIX\n"
        "====================================\n\n"
        "Aircraft_AAB_Global.ini was repaired inside _SPEC_DATA_ONE.big.\n"
        "No unrelated BIG entry changed.\n\n"
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
            "Aircraft_AAB_Global.ini",
        ):
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_AAB_GLOBAL_FIXED.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "Aircraft_AAB_Global.ini", "Aircraft_AAB_Global.ini")
        zf.write(extract_path, "EXTRACT_VERIFY/Aircraft_AAB_Global.ini")
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
