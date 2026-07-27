#!/usr/bin/env python3
"""Patch France_CombatDrone.ini inside _SPEC_DATA_ONE.big (USA MQ9 donor).

Same crash pattern as Britain_CombatDrone:
  - non-ASCII comments (em-dash / multiply)
  - Science = SCIENCE_UAEStealthJet
  - duplicate Shadow = SHADOW_VOLUME

Patches the corrected file INTO the DATA BIG (not overlay-only).
Source: SPECTER_SPEC_DATA_ONE_EGYPT_MHQ_VERIFIED/_SPEC_DATA_ONE.big
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_EGYPT_MHQ_VERIFIED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FRANCE_DRONE_FIXED"
FRANCE_PATH = (
    r"Data\INI\Object\Specter\French Armed Forces\Drones\France_CombatDrone.ini"
)
USA_PATH = r"Data\INI\Object\Specter\United States Of America\Drones\Mq9.ini"
TREE = (
    ROOT
    / "Data"
    / "INI"
    / "Object"
    / "Specter"
    / "French Armed Forces"
    / "Drones"
    / "France_CombatDrone.ini"
)
SYNC_DIRS = [
    ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL",
    ROOT / "Release" / "SPECTER_FINAL_EGYPT_BRITAIN_FIXED",
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


def clone_usa_to_france(usa_text: str) -> str:
    text = usa_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    i = 0
    while i < len(lines) and (lines[i].strip() == "" or lines[i].lstrip().startswith(";")):
        i += 1
    text = "\n".join(lines[i:])
    if not text.startswith("Object AmericaDronesMq9"):
        raise SystemExit("unexpected USA MQ9 start")

    text = text.replace("Object AmericaDronesMq9", "Object France_CombatDrone", 1)
    text = re.sub(r"(?m)^(  Side\s*=\s*)America\s*$", r"\1France", text, count=1)
    text = re.sub(
        r"(?m)^(  DisplayName\s*=\s*)OBJECT:\S+\s*$",
        r"\1OBJECT:France_CombatDrone",
        text,
        count=1,
    )
    text = re.sub(
        r"(?ms)^  Prerequisites\n.*?^  End",
        "  Prerequisites\n"
        "    Object = France_AdvancedAirBase\n"
        "    Science = SCIENCE_Rank3\n"
        "  End",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(    Weapon\s*=\s*PRIMARY\s+)\S+\s*$",
        r"\1France_Weapon_ATGM",
        text,
        count=1,
    )
    text = re.sub(r"(?m)^(  BuildCost\s*=\s*)\S+", r"\g<1>1093", text, count=1)
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
        "; SPECTER FIX - France_CombatDrone\n"
        "; Donor: USA AmericaDronesMq9 (Mq9.ini) - same pattern as Britain_CombatDrone fix\n"
        "; Keep: Object France_CombatDrone / Side=France / France_AdvancedAirBase\n"
        "; Weapons: France_Weapon_ATGM + 2x_GBU12II_Mq9\n"
        "; Removed: non-ASCII comments, SCIENCE_UAEStealthJet, duplicate Shadow\n"
        "\n"
    )
    text = header + text
    code_only = "\n".join(line.split(";", 1)[0] for line in text.splitlines())
    if re.search(r"(?i)\bSCIENCE_UAE|\bUAEAirfield\b|\bUAE_", code_only):
        raise SystemExit("foreign science leftovers in code")
    if any(ord(c) > 127 for c in text):
        raise SystemExit("non-ascii remain")
    if "France_Weapon_ATGM" not in text or "2x_GBU12II_Mq9" not in text:
        raise SystemExit("weapons missing")
    if "GenericTacticalBomberCommandSet" not in text:
        raise SystemExit("commandset missing")
    if "France_AdvancedAirBase" not in code_only:
        raise SystemExit("prereq missing")
    return text.replace("\n", "\r\n")


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source DATA BIG: {SRC}")

    entries = parse_big(SRC)
    by = {knorm(n): (n, b) for n, b in entries}
    if knorm(FRANCE_PATH) not in by:
        raise SystemExit("France_CombatDrone.ini missing from source BIG")
    if knorm(USA_PATH) not in by:
        raise SystemExit("USA Mq9.ini missing from source BIG")

    broken = by[knorm(FRANCE_PATH)][1]
    usa_text = by[knorm(USA_PATH)][1].decode("utf-8", "replace")
    fixed = clone_usa_to_france(usa_text)
    fixed_bytes = fixed.encode("ascii")

    art_entries = parse_big(ART) if ART.is_file() else []
    data_join = b"\n".join(b for _, b in entries)

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

    chk("Object=France_CombatDrone", bool(re.search(r"(?m)^Object\s+France_CombatDrone\b", fixed)))
    chk("Side=France", bool(re.search(r"(?m)^  Side\s*=\s*France\s*$", fixed)))
    chk("CommandSet resolves", all(c in commandsets or c.encode() in data_join for c in cs))
    chk("Weapon refs resolve", all(w in weapons or w.encode() in data_join for w in weps))
    if art_entries:
        chk(
            "Model refs in ART",
            all(any(m.lower() in knorm(n) for n, _ in art_entries) for m in models),
        )
    else:
        chk("Model refs in ART (skipped, no ART)", True)
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
    if art_entries:
        for m in models:
            if not any(m.lower() in knorm(n) for n, _ in art_entries):
                missing.append(f"Model={m}")
    chk("Missing references = 0", not missing)
    chk("Object duplicates = 0", len(re.findall(r"(?m)^Object\s+\S+", fixed)) == 1)

    ok_all = all(ok for _, ok in checks)
    if not ok_all:
        print("VALIDATION FAILED; not writing BIG")
        for n, ok in checks:
            if not ok:
                print(" FAIL:", n)
        print("Missing=", missing)
        return 1

    # Patch inside DATA BIG (preserve entry order/names)
    new_entries = []
    for name, blob in entries:
        if knorm(name) == knorm(FRANCE_PATH):
            new_entries.append((name, fixed_bytes))
        else:
            new_entries.append((name, blob))

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    write_big(out_big, new_entries)

    # Re-extract and verify round-trip
    rebuilt_entries = parse_big(out_big)
    rebuilt_by = {knorm(n): (n, b) for n, b in rebuilt_entries}
    rebuilt = rebuilt_by[knorm(FRANCE_PATH)][1]
    if rebuilt != fixed_bytes:
        raise SystemExit("round-trip France content mismatch")
    rebuilt_text = rebuilt.decode("ascii")
    if any(ord(c) > 127 for c in rebuilt_text):
        raise SystemExit("rebuilt non-ascii")
    if "SCIENCE_UAEStealthJet" in "\n".join(
        line.split(";", 1)[0] for line in rebuilt_text.splitlines()
    ):
        raise SystemExit("rebuilt still has SCIENCE_UAEStealthJet")

    # Other files unchanged
    src_by = {knorm(n): b for n, b in entries}
    for n, b in rebuilt_entries:
        k = knorm(n)
        if k == knorm(FRANCE_PATH):
            continue
        if src_by[k] != b:
            raise SystemExit(f"other file changed: {n}")

    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(fixed_bytes)
    (OUT / "France_CombatDrone.ini").write_bytes(fixed_bytes)

    big_sha = sha256_file(out_big)
    big_size = out_big.stat().st_size
    france_sha = sha256_bytes(fixed_bytes)
    broken_sha = sha256_bytes(broken)

    report = (
        "SPECTER FRANCE COMBATDRONE FIXED - VERIFY REPORT\n"
        "============================================================\n"
        f"VERDICT: {'PASS' if ok_all else 'FAIL'}\n"
        "Scope: France_CombatDrone.ini patched INSIDE _SPEC_DATA_ONE.big\n"
        "Overlay-only: NO (file is inside DATA BIG)\n"
        f"\nSource BIG (Egypt MHQ verified): {sha256_file(SRC)}\n"
        f"Patched BIG SHA256: {big_sha}\n"
        f"Patched BIG SIZE:   {big_size}\n"
        f"Broken France SHA:  {broken_sha}\n"
        f"Fixed France SHA:   {france_sha}\n"
        f"Fixed France SIZE:  {len(fixed_bytes)}\n"
        "\nRoot causes (same as Britain_CombatDrone):\n"
        "  - Non-ASCII UTF-8 comments (parser crash)\n"
        "  - Science prereq SCIENCE_UAEStealthJet (not a defined Science)\n"
        "  - Duplicate Shadow = SHADOW_VOLUME\n"
        "\nRepair (USA MQ9 donor):\n"
        "  Object=France_CombatDrone Side=France\n"
        "  CommandSet=GenericTacticalBomberCommandSet\n"
        "  Weapons=France_Weapon_ATGM + 2x_GBU12II_Mq9\n"
        "  Models=US_MQ9 / US_MQ9D / US_MQ9R\n"
        "  Prereq=France_AdvancedAirBase + SCIENCE_Rank3\n"
        "  BuildCost=1093 BuildTime=11.1\n"
        f"\nPASS: {sum(1 for _, ok in checks if ok)}  FAIL: {sum(1 for _, ok in checks if not ok)}\n\n"
        + "\n".join(f"{'PASS' if ok else 'FAIL'}: {n}" for n, ok in checks)
        + f"\n\nMissing={missing}\n\nFINAL: {'PASS' if ok_all else 'FAIL'}\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER FRANCE COMBATDRONE FIXED\n"
        "================================\n\n"
        "This package replaces Data\\_SPEC_DATA_ONE.big with France_CombatDrone\n"
        "already patched INSIDE the archive (not an external overlay).\n\n"
        "INSTALL:\n"
        "1. Close Generals Zero Hour.\n"
        "2. Backup existing Data\\_SPEC_DATA_ONE.big.\n"
        "3. Copy _SPEC_DATA_ONE.big into <Game>\\Data\\\n"
        "4. Keep Data\\_SPEC_ART_ONE.big unchanged.\n"
        "5. Launch and confirm France Combat Drone no longer crashes init.\n",
        encoding="ascii",
    )
    hashes = (
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"France_CombatDrone.ini SHA256={france_sha} SIZE={len(fixed_bytes)}\n"
        f"Broken vendor France_CombatDrone.ini SHA256={broken_sha}\n"
        f"Source Egypt MHQ verified BIG SHA256={sha256_file(SRC)}\n"
    )
    (OUT / "HASHES.txt").write_text(hashes, encoding="ascii")

    for sync in SYNC_DIRS:
        if sync.is_dir():
            shutil.copy2(out_big, sync / "_SPEC_DATA_ONE.big")
            print("synced", sync / "_SPEC_DATA_ONE.big")

    zpath = OUT / "_SPEC_DATA_ONE_FRANCE_DRONE_FIXED.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "France_CombatDrone.ini", "France_CombatDrone.ini")
        zf.write(OUT / "VERIFY_REPORT.txt", "VERIFY_REPORT.txt")
        zf.write(OUT / "README_INSTALL.txt", "README_INSTALL.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")

    print(report)
    print("ZIP", zpath, sha256_file(zpath))
    print("BIG", out_big, big_sha, big_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
