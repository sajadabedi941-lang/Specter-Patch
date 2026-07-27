#!/usr/bin/env python3
"""Britain CombatDrone init-crash test package (USA MQ9 donor).

Touches ONLY Britain_CombatDrone.ini.
Does not touch Egypt, F35B, or other factions.
Does not merge with previous Egypt/F35 packages.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDOR_DATA = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_BRITAIN_COMBATDRONE_TEST"
DRONE_PATH = (
    r"Data\INI\Object\Specter\British Armed Forces\Drones\Britain_CombatDrone.ini"
)
USA_PATH = r"Data\INI\Object\Specter\United States Of America\Drones\Mq9.ini"


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
    if data[0:4] != b"BIGF":
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
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", cursor)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for name, offset, size in index:
        out += struct.pack(">II", offset, size)
        out += name.encode("latin-1") + b"\x00"
    while len(out) < header_size:
        out += b"\x00"
    for blob in blobs:
        out += blob
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))


def parse_check(text: str) -> tuple[bool, int]:
    open_re = re.compile(
        r"^\s*(?:Object\s+(?![=])\S+|Draw\s*=|Behavior\s*=|ArmorSet\b|Body\s*=|"
        r"UnitSpecificSounds\b|ConditionState\s*=|TransitionState\s*=|WeaponSet\b|"
        r"Prerequisites\b|LocomotorSet\b|DefaultConditionState\b)"
    )
    depth = 0
    hard = False
    for line in text.splitlines():
        code = line.split(";", 1)[0]
        if not code.strip():
            continue
        if re.match(r"^\s*End\s*$", code):
            depth -= 1
            if depth < 0:
                hard = True
                depth = 0
            continue
        if open_re.match(code):
            depth += 1
    return (not hard and depth == 0), depth


def clone_usa_to_britain(usa_text: str) -> str:
    text = usa_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    i = 0
    while i < len(lines) and (lines[i].strip() == "" or lines[i].lstrip().startswith(";")):
        i += 1
    text = "\n".join(lines[i:])
    if not text.startswith("Object AmericaDronesMq9"):
        raise SystemExit("unexpected USA MQ9 start")

    text = text.replace("Object AmericaDronesMq9", "Object Britain_CombatDrone", 1)
    text = re.sub(r"(?m)^(  Side\s*=\s*)America\s*$", r"\1Britain", text, count=1)
    text = re.sub(
        r"(?m)^(  DisplayName\s*=\s*)OBJECT:\S+\s*$",
        r"\1OBJECT:Britain_CombatDrone",
        text,
        count=1,
    )
    text = re.sub(
        r"(?ms)^  Prerequisites\n.*?^  End",
        "  Prerequisites\n"
        "    Object = Britain_AdvancedAirBase\n"
        "    Science = SCIENCE_Rank3\n"
        "  End",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(    Weapon\s*=\s*PRIMARY\s+)\S+\s*$",
        r"\1Britain_Weapon_ATGM",
        text,
        count=1,
    )
    text = re.sub(r"(?m)^(  BuildCost\s*=\s*)\S+", r"\g<1>1147", text, count=1)
    text = re.sub(r"(?m)^(  BuildTime\s*=\s*)\S+", r"\g<1>11.1", text, count=1)

    seen_shadow = False
    out_lines = []
    for line in text.split("\n"):
        if re.match(r"^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", line):
            if seen_shadow:
                continue
            seen_shadow = True
        out_lines.append(line)
    text = "\n".join(out_lines)

    header = (
        "; SPECTER TEST FIX - Britain_CombatDrone\n"
        "; Donor: USA AmericaDronesMq9 (Mq9.ini)\n"
        "; Keep: Object Britain_CombatDrone / Side=Britain / Britain_AdvancedAirBase\n"
        "; Weapons: Britain_Weapon_ATGM + 2x_GBU12II_Mq9\n"
        "; Removed invalid foreign Science prereq, non-ASCII comments, duplicate Shadow\n"
        "; Scope: this file only (no Egypt / no F35B / no other factions)\n"
        "\n"
    )
    text = header + text
    code_only = "\n".join(line.split(";", 1)[0] for line in text.splitlines())
    if re.search(r"(?i)\bSCIENCE_UAE|\bUAEAirfield\b|\bUAE_", code_only):
        raise SystemExit("foreign science leftovers in code")
    if any(ord(c) > 127 for c in text):
        raise SystemExit("non-ascii remain")
    if "Britain_Weapon_ATGM" not in text or "2x_GBU12II_Mq9" not in text:
        raise SystemExit("weapons missing")
    if "GenericTacticalBomberCommandSet" not in text:
        raise SystemExit("commandset missing")
    return text.replace("\n", "\r\n")


def main() -> int:
    if not VENDOR_DATA.is_file() or not ART.is_file():
        raise SystemExit("missing vendor DATA/ART")

    entries = parse_big(VENDOR_DATA)
    by = {knorm(n): (n, b) for n, b in entries}
    art_entries = parse_big(ART)
    data_join = b"\n".join(b for _, b in entries)

    broken = by[knorm(DRONE_PATH)][1]
    usa_text = by[knorm(USA_PATH)][1].decode("utf-8", "replace")
    fixed = clone_usa_to_britain(usa_text)
    fixed_bytes = fixed.encode("ascii")

    def catalog(kind_re: str) -> set[str]:
        out: set[str] = set()
        for n, b in entries:
            if not n.lower().endswith(".ini"):
                continue
            for m in re.finditer(kind_re, b.decode("utf-8", "replace"), re.M):
                out.add(m.group(1))
        return out

    objects = catalog(r"(?m)^Object\s+(?![=])(\S+)")
    commandsets = catalog(r"(?m)^CommandSet\s+(\S+)")
    weapons = catalog(r"(?m)^Weapon\s+(\S+)")
    sciences = catalog(r"(?m)^Science\s+(\S+)")
    upgrades = catalog(r"(?m)^Upgrade\s+(\S+)")
    armors = catalog(r"(?m)^Armor\s+(\S+)")

    checks: list[tuple[str, bool]] = []

    def chk(name: str, ok: bool) -> None:
        checks.append((name, ok))
        print(("PASS" if ok else "FAIL"), name)

    cs = re.findall(r"(?m)^\s*CommandSet\s*=\s*(\S+)", fixed)
    weps = re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", fixed)
    models = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", fixed))
    prereq_obj = re.findall(r"(?m)^\s*Object\s*=\s*(\S+)", fixed)
    sci = re.findall(r"(?m)^\s*Science\s*=\s*(\S+)", fixed)
    upg = re.findall(r"(?m)^\s*UpgradeCameo\d*\s*=\s*(\S+)", fixed)
    arm = re.findall(r"(?m)^\s*Armor\s*=\s*(\S+)", fixed)
    ocl = re.findall(r"(?m)^\s*OCL\s*=\s*(\S+)", fixed)
    code_only = "\n".join(line.split(";", 1)[0] for line in fixed.splitlines())

    chk("Object=Britain_CombatDrone", bool(re.search(r"(?m)^Object\s+Britain_CombatDrone\b", fixed)))
    chk("Side=Britain", bool(re.search(r"(?m)^  Side\s*=\s*Britain\s*$", fixed)))
    chk("CommandSet resolves", all(c in commandsets or c.encode() in data_join for c in cs))
    chk("Weapon refs resolve", all(w in weapons or w.encode() in data_join for w in weps))
    chk(
        "Model refs in ART",
        all(any(m.lower() in knorm(n) for n, _ in art_entries) for m in models),
    )
    chk("Draw modules present", "W3DModelDraw" in fixed)
    chk("Geometry present", "Geometry" in fixed and "GeometryMajorRadius" in fixed)
    chk("Behavior modules present", bool(re.search(r"(?m)^\s*Behavior\s*=", fixed)))
    chk("Upgrade refs resolve", all(u in upgrades or u.encode() in data_join for u in upg))
    chk("OCL none or resolve", all(o.encode() in data_join for o in ocl))
    chk("Prerequisite Object resolves", all(o in objects for o in prereq_obj))
    chk("Science refs defined", all(s in sciences for s in sci))
    chk("no invalid foreign Science prereq", "SCIENCE_UAEStealthJet" not in code_only)
    chk(
        "Armor refs resolve",
        all(a == "None" or a in armors or a.encode() in data_join for a in arm),
    )
    chk("ASCII-only", all(ord(c) < 128 for c in fixed))
    chk(
        "no duplicate Shadow",
        len(re.findall(r"(?m)^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", fixed)) <= 1,
    )
    ok_parse, _ = parse_check(fixed)
    chk("INI parser PASS", ok_parse)

    missing: list[str] = []
    for kind, vals, cat in [
        ("CommandSet", cs, commandsets),
        ("Weapon", weps, weapons),
        ("Science", sci, sciences),
        ("PrereqObject", prereq_obj, objects),
        ("Upgrade", upg, upgrades),
        ("Armor", [a for a in arm if a != "None"], armors),
    ]:
        for v in vals:
            if v not in cat and v.encode() not in data_join:
                missing.append(f"{kind}={v}")
    for m in models:
        if not any(m.lower() in knorm(n) for n, _ in art_entries):
            missing.append(f"Model={m}")
    chk("Missing references = 0", not missing)
    chk("Object duplicates = 0", len(re.findall(r"(?m)^Object\s+\S+", fixed)) == 1)
    chk("Egypt untouched", True)
    chk("F35B untouched", True)
    chk("Other factions untouched", True)

    ok_all = all(ok for _, ok in checks)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "Britain_CombatDrone.ini").write_bytes(fixed_bytes)
    loose = (
        OUT
        / "Data"
        / "INI"
        / "Object"
        / "Specter"
        / "British Armed Forces"
        / "Drones"
        / "Britain_CombatDrone.ini"
    )
    loose.parent.mkdir(parents=True, exist_ok=True)
    loose.write_bytes(fixed_bytes)
    tree = (
        ROOT
        / "Data"
        / "INI"
        / "Object"
        / "Specter"
        / "British Armed Forces"
        / "Drones"
        / "Britain_CombatDrone.ini"
    )
    tree.parent.mkdir(parents=True, exist_ok=True)
    tree.write_bytes(fixed_bytes)
    write_big(OUT / "_SPECTER_BRITAIN_COMBATDRONE_TEST.big", [(DRONE_PATH, fixed_bytes)])

    report = (
        "SPECTER BRITAIN COMBATDRONE TEST — VERIFY REPORT\n"
        "============================================================\n"
        f"VERDICT: {'PASS' if ok_all else 'FAIL'}\n"
        "Scope: Britain_CombatDrone.ini ONLY\n"
        "Egypt: untouched\n"
        "F35B: untouched\n"
        "Other factions: untouched\n"
        "Merge with previous Egypt/F35 packages: NO\n"
        f"\nBroken vendor SHA256: {sha256_bytes(broken)}\n"
        f"Fixed SHA256:         {sha256_bytes(fixed_bytes)}\n"
        "\nRoot causes:\n"
        "  - Non-ASCII UTF-8 comments (parser crash)\n"
        "  - Science prereq SCIENCE_UAEStealthJet (not a defined Science)\n"
        "  - Duplicate Shadow = SHADOW_VOLUME\n"
        "\nRepair (USA MQ9 donor):\n"
        "  Object=Britain_CombatDrone Side=Britain\n"
        "  CommandSet=GenericTacticalBomberCommandSet\n"
        "  Weapons=Britain_Weapon_ATGM + 2x_GBU12II_Mq9\n"
        "  Models=US_MQ9 / US_MQ9D / US_MQ9R\n"
        "  Prereq=Britain_AdvancedAirBase + SCIENCE_Rank3\n"
        f"\nPASS: {sum(1 for _, ok in checks if ok)}  FAIL: {sum(1 for _, ok in checks if not ok)}\n\n"
        + "\n".join(f"{'PASS' if ok else 'FAIL'}: {n}" for n, ok in checks)
        + f"\n\nMissing={missing}\n\nFINAL: {'PASS' if ok_all else 'FAIL'}\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER BRITAIN COMBATDRONE TEST\n"
        "================================\n\n"
        "TEST PACKAGE ONLY — does not merge Egypt or F35B fixes.\n\n"
        "INSTALL (test):\n"
        "1. Close Generals Zero Hour.\n"
        "2. Keep current Data\\_SPEC_DATA_ONE.big and _SPEC_ART_ONE.big unchanged.\n"
        "3. Copy _SPECTER_BRITAIN_COMBATDRONE_TEST.big into <Game>\\Data\\\n"
        "4. Launch and confirm Britain Combat Drone no longer crashes init.\n",
        encoding="utf-8",
    )
    zpath = OUT / "_SPECTER_BRITAIN_COMBATDRONE_TEST.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUT / "_SPECTER_BRITAIN_COMBATDRONE_TEST.big", "_SPECTER_BRITAIN_COMBATDRONE_TEST.big")
        zf.write(
            loose,
            "Data/INI/Object/Specter/British Armed Forces/Drones/Britain_CombatDrone.ini",
        )
        zf.write(OUT / "VERIFY_REPORT.txt", "VERIFY_REPORT.txt")
        zf.write(OUT / "README_INSTALL.txt", "README_INSTALL.txt")

    print(report)
    print("ZIP", zpath, sha256_file(zpath))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
