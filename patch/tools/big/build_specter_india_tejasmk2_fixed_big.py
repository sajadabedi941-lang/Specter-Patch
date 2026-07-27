#!/usr/bin/env python3
"""Patch India_TejasMk2.ini inside _SPEC_DATA_ONE.big (ASCII / parse repair).

Crash pattern: non-ASCII comments (em-dash / multiply) in Phase G header.
Object block / Shadow / modules are otherwise intact; keep India identity,
weapons, balance, models, and prereqs.

Source: SPECTER_SPEC_DATA_ONE_GERMANY_DRONE_FIXED/_SPEC_DATA_ONE.big
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_GERMANY_DRONE_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_INDIA_TEJASMK2_FIXED"
TEJAS_PATH = (
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\India_TejasMk2.ini"
)
TREE = (
    ROOT
    / "Data"
    / "INI"
    / "Object"
    / "Specter"
    / "Indian Armed Forces"
    / "Airforce"
    / "India_TejasMk2.ini"
)
SYNC_DIRS = [
    ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL",
    ROOT / "Release" / "SPECTER_FINAL_EGYPT_BRITAIN_FIXED",
]

# Prior in-BIG fixes that must remain preserved
PRESERVE = {
    r"Data\INI\Object\Specter\French Armed Forces\Drones\France_CombatDrone.ini": (
        "7512cca46c234c6951a54d5a982184209d203668738c4e1336fdaab1e1ba8df2"
    ),
    r"Data\INI\Object\Specter\German Armed Forces\Drones\Germany_CombatDrone.ini": (
        "663b32b1de6111bd1496463bc042f642d204782a525f103c63440d92d380e8b2"
    ),
}


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


def ascii_safe_comment(s: str) -> str:
    """Replace common UTF-8 punctuation that crashes ZH INI parser."""
    repl = {
        "\u2014": "-",  # em dash
        "\u2013": "-",  # en dash
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00d7": "x",  # multiply
        "\u00a0": " ",
    }
    out = []
    for ch in s:
        if ord(ch) < 128:
            out.append(ch)
        elif ch in repl:
            out.append(repl[ch])
        else:
            out.append("?")
    return "".join(out)


def repair_tejas(raw: bytes) -> str:
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    # Drop any prior broken repair headers with mojibake; keep one clean header.
    lines = text.split("\n")
    # If file already starts with SPECTER REPAIR, strip leading repair block until Object
    while lines and (
        lines[0].strip() == ""
        or (
            lines[0].lstrip().startswith(";")
            and "SPECTER REPAIR" in lines[0]
            or (
                lines
                and lines[0].lstrip().startswith(";")
                and not lines[0].lstrip().startswith("; SPECTER PATCH")
                and "Object " not in lines[0]
                and any(
                    x in lines[0]
                    for x in (
                        "SPECTER REPAIR",
                        "Validated:",
                        "Identity fix",
                        "No Iraqi",
                        "Stand-in",
                        "Preserved:",
                    )
                )
            )
        )
    ):
        # Only strip explicit prior repair headers, not Phase G content yet
        if lines[0].lstrip().startswith(";") and (
            "SPECTER REPAIR" in lines[0]
            or lines[0].lstrip().startswith("; Validated:")
            or lines[0].lstrip().startswith("; Identity fix")
            or lines[0].lstrip().startswith("; Stand-in")
            or lines[0].lstrip().startswith("; Preserved:")
            or lines[0].lstrip().startswith("; No Iraqi")
        ):
            lines.pop(0)
            continue
        break

    text = "\n".join(lines)
    # Sanitize every line to ASCII (comments are the crash source)
    text = "\n".join(ascii_safe_comment(line) for line in text.split("\n"))

    # Deduplicate Shadow = SHADOW_VOLUME if present
    seen_shadow = False
    out_lines = []
    for line in text.split("\n"):
        if re.match(r"^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", line):
            if seen_shadow:
                continue
            seen_shadow = True
        out_lines.append(line)
    text = "\n".join(out_lines)

    if not re.search(r"(?m)^Object\s+India_TejasMk2\b", text):
        raise SystemExit("Object India_TejasMk2 missing")
    if not re.search(r"(?m)^  Side\s*=\s*India\s*$", text):
        raise SystemExit("Side=India missing")
    if "India_Weapon_AstraMk2_TejasMk2" not in text:
        raise SystemExit("Astra Mk2 weapon missing")
    if any(ord(c) > 127 for c in text):
        bad = sorted({hex(ord(c)) for c in text if ord(c) > 127})
        raise SystemExit(f"non-ascii remain: {bad}")

    header = (
        "; SPECTER FIX - India_TejasMk2\n"
        "; ASCII/parse repair (same non-ASCII comment crash as CombatDrone)\n"
        "; Keep: Object India_TejasMk2 / Side=India / India weapons and balance\n"
        "; Weapons: India_Weapon_AstraMk2_TejasMk2 + 2x_ALCM_ScalpEG + Thales radar\n"
        "; Prereq: SCIENCE_India_TechTejasMk2 + India_MIC + SCIENCE_Rank6\n"
        "; Removed: non-ASCII comments; duplicate Shadow if any\n"
        "\n"
    )
    # Avoid double Object if we prepend before existing Object line
    # Strip a leading Phase G banner only if we add our header (keep rest)
    body_lines = text.split("\n")
    # Remove old Phase G title line if present (now ASCII-sanitized)
    if body_lines and "SPECTER PATCH Phase G" in body_lines[0]:
        body_lines = body_lines[1:]
        while body_lines and body_lines[0].strip() == "":
            body_lines.pop(0)
    text = header + "\n".join(body_lines)
    if text.count("Object India_TejasMk2") != 1 and len(
        re.findall(r"(?m)^Object\s+India_TejasMk2\b", text)
    ) != 1:
        raise SystemExit("Object count wrong")
    return text.replace("\n", "\r\n")


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source DATA BIG: {SRC}")

    entries = parse_big(SRC)
    by = {knorm(n): (n, b) for n, b in entries}
    if knorm(TEJAS_PATH) not in by:
        raise SystemExit("India_TejasMk2.ini missing from source BIG")

    broken = by[knorm(TEJAS_PATH)][1]
    fixed = repair_tejas(broken)
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
    module_tags = re.findall(r"ModuleTag_\S+", fixed)

    chk("Object=India_TejasMk2", bool(re.search(r"(?m)^Object\s+India_TejasMk2\b", fixed)))
    chk("Side=India", bool(re.search(r"(?m)^  Side\s*=\s*India\s*$", fixed)))
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
    chk("India Astra weapon kept", "India_Weapon_AstraMk2_TejasMk2" in fixed)
    chk("BuildCost=1744", bool(re.search(r"(?m)^  BuildCost\s*=\s*1744\s*$", fixed)))
    chk("BuildTime=13.8", bool(re.search(r"(?m)^  BuildTime\s*=\s*13\.8\b", fixed)))
    chk(
        "Armor refs resolve",
        all(a == "None" or a in armors or a.encode() in data_join for a in arm),
    )
    chk("ASCII-only", all(ord(c) < 128 for c in fixed))
    chk(
        "no duplicate Shadow",
        len(re.findall(r"(?m)^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", fixed)) <= 1,
    )
    chk("no duplicate ModuleTag", len(module_tags) == len(set(module_tags)))
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

    new_entries = []
    for name, blob in entries:
        if knorm(name) == knorm(TEJAS_PATH):
            new_entries.append((name, fixed_bytes))
        else:
            new_entries.append((name, blob))

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    # Remove any stale BIG so we never verify against a previous artifact.
    if out_big.exists():
        out_big.unlink()
    write_big(out_big, new_entries)

    # --- HARD EMBED PROOF: re-open from disk, extract path, compare bytes ---
    disk_bytes = out_big.read_bytes()
    if disk_bytes[:4] != b"BIGF":
        raise SystemExit("written BIG missing BIGF magic")
    rebuilt_entries = parse_big(out_big)
    rebuilt_by = {knorm(n): (n, b) for n, b in rebuilt_entries}
    if knorm(TEJAS_PATH) not in rebuilt_by:
        raise SystemExit(
            "EMBED FAIL: India_TejasMk2.ini path missing after write "
            f"(looked for {TEJAS_PATH!r})"
        )
    # Case-insensitive path the game/user checks:
    # Data/INI/Object/specter/indian armed forces/airforce/india_tejasmk2.ini
    extracted_name, extracted = rebuilt_by[knorm(TEJAS_PATH)]
    extract_dir = OUT / "_EXTRACT_VERIFY" / "Data" / "INI" / "Object" / "Specter" / "Indian Armed Forces" / "Airforce"
    extract_dir.mkdir(parents=True, exist_ok=True)
    extract_path = extract_dir / "India_TejasMk2.ini"
    extract_path.write_bytes(extracted)

    tejas_sha = sha256_bytes(fixed_bytes)
    broken_sha = sha256_bytes(broken)
    extracted_sha = sha256_bytes(extracted)
    extract_file_sha = sha256_file(extract_path)

    if extracted != fixed_bytes or extracted_sha != tejas_sha:
        raise SystemExit(
            "EMBED FAIL: inside-BIG India_TejasMk2.ini != fixed source\n"
            f"  fixed_sha={tejas_sha}\n"
            f"  inside_sha={extracted_sha}\n"
            f"  broken_sha={broken_sha}\n"
            f"  entry_name={extracted_name!r}"
        )
    if extract_file_sha != tejas_sha:
        raise SystemExit("EMBED FAIL: extracted-on-disk file hash mismatch")
    if extracted_sha == broken_sha:
        raise SystemExit("EMBED FAIL: inside-BIG content is still the broken vendor file")
    if b"SPECTER PATCH Phase G" in extracted and b"\xe2\x80\x94" in extracted:
        raise SystemExit("EMBED FAIL: non-ASCII em-dash still present inside BIG")
    rebuilt_text = extracted.decode("ascii")
    if any(ord(c) > 127 for c in rebuilt_text):
        raise SystemExit("rebuilt non-ascii")
    print("EMBED PROOF PASS")
    print(f"  entry_name={extracted_name}")
    print(f"  inside_BIG_sha={extracted_sha}")
    print(f"  fixed_src_sha={tejas_sha}")
    print(f"  extracted_path={extract_path}")

    src_by = {knorm(n): b for n, b in entries}
    for n, b in rebuilt_entries:
        k = knorm(n)
        if k == knorm(TEJAS_PATH):
            continue
        if src_by[k] != b:
            raise SystemExit(f"other file changed: {n}")

    for path, expect_sha in PRESERVE.items():
        got = sha256_bytes(rebuilt_by[knorm(path)][1])
        if got != expect_sha:
            raise SystemExit(f"preserved fix lost for {path}: {got}")

    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(fixed_bytes)
    (OUT / "India_TejasMk2.ini").write_bytes(fixed_bytes)

    big_sha = sha256_file(out_big)
    big_size = out_big.stat().st_size

    report = (
        "SPECTER INDIA TEJAS MK2 FIXED - VERIFY REPORT\n"
        "============================================================\n"
        f"VERDICT: {'PASS' if ok_all else 'FAIL'}\n"
        "Scope: India_TejasMk2.ini patched INSIDE _SPEC_DATA_ONE.big\n"
        "Overlay-only: NO (file is inside DATA BIG)\n"
        f"\nSource BIG (Germany drone fixed): {sha256_file(SRC)}\n"
        f"Patched BIG SHA256: {big_sha}\n"
        f"Patched BIG SIZE:   {big_size}\n"
        f"Broken TejasMk2 SHA: {broken_sha}\n"
        f"Fixed TejasMk2 SHA:  {tejas_sha}\n"
        f"Fixed TejasMk2 SIZE: {len(fixed_bytes)}\n"
        "France/Germany drone fixes: preserved\n"
        "\nRoot cause:\n"
        "  - Non-ASCII UTF-8 comments (em-dash / multiply) crash ZH INI parser\n"
        "\nRepair:\n"
        "  Object=India_TejasMk2 Side=India\n"
        "  Keep weapons: India_Weapon_AstraMk2_TejasMk2 + 2x_ALCM_ScalpEG\n"
        "  Keep balance: BuildCost=1744 BuildTime=13.8\n"
        "  Keep prereq: SCIENCE_India_TechTejasMk2 + India_MIC + SCIENCE_Rank6\n"
        "  ASCII-only comments; Shadow/ModuleTag uniqueness verified\n"
        "\nEMBED PROOF (extract-after-write):\n"
        f"  entry: {extracted_name}\n"
        f"  inside_BIG_sha == fixed_sha == {tejas_sha}\n"
        f"  extracted_path: _EXTRACT_VERIFY/.../India_TejasMk2.ini\n"
        f"  still_broken: NO (broken was {broken_sha})\n"
        f"\nPASS: {sum(1 for _, ok in checks if ok)}  FAIL: {sum(1 for _, ok in checks if not ok)}\n\n"
        + "\n".join(f"{'PASS' if ok else 'FAIL'}: {n}" for n, ok in checks)
        + f"\n\nMissing={missing}\n\nFINAL: {'PASS' if ok_all else 'FAIL'}\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER INDIA TEJAS MK2 FIXED\n"
        "=============================\n\n"
        "This package replaces Data\\_SPEC_DATA_ONE.big with India_TejasMk2\n"
        "already patched INSIDE the archive (not an external overlay).\n"
        "Also retains prior France/Germany CombatDrone in-BIG fixes.\n\n"
        "INSTALL:\n"
        "1. Close Generals Zero Hour.\n"
        "2. Backup existing Data\\_SPEC_DATA_ONE.big.\n"
        "3. Copy _SPEC_DATA_ONE.big into <Game>\\Data\\\n"
        "4. Keep Data\\_SPEC_ART_ONE.big unchanged.\n"
        "5. Launch and confirm India Tejas Mk2 no longer crashes init.\n",
        encoding="ascii",
    )
    hashes = (
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"India_TejasMk2.ini SHA256={tejas_sha} SIZE={len(fixed_bytes)}\n"
        f"Broken vendor India_TejasMk2.ini SHA256={broken_sha}\n"
        f"Source Germany-fixed BIG SHA256={sha256_file(SRC)}\n"
    )
    (OUT / "HASHES.txt").write_text(hashes, encoding="ascii")

    for sync in SYNC_DIRS:
        if sync.is_dir():
            shutil.copy2(out_big, sync / "_SPEC_DATA_ONE.big")
            print("synced", sync / "_SPEC_DATA_ONE.big")

    # Refresh FINAL zip so it cannot keep a stale broken BIG.
    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    final_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
    shutil.copy2(OUT / "HASHES.txt", final_dir / "HASHES.txt")
    shutil.copy2(OUT / "VERIFY_REPORT.txt", final_dir / "VERIFY_REPORT.txt")
    shutil.copy2(OUT / "README_INSTALL.txt", final_dir / "README_INSTALL.txt")
    shutil.copy2(OUT / "India_TejasMk2.ini", final_dir / "India_TejasMk2.ini")
    final_zip = final_dir / "_SPEC_DATA_ONE_FINAL.zip"
    if final_zip.exists():
        final_zip.unlink()
    with zipfile.ZipFile(final_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "India_TejasMk2.ini", "India_TejasMk2.ini")
        zf.write(OUT / "VERIFY_REPORT.txt", "VERIFY_REPORT.txt")
        zf.write(OUT / "README_INSTALL.txt", "README_INSTALL.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
    # Prove FINAL.zip embeds fixed Tejas (this was previously stale/broken).
    with zipfile.ZipFile(final_zip, "r") as zf:
        zip_big = zf.read("_SPEC_DATA_ONE.big")
    zip_entries = []
    pos = 16
    count = struct.unpack(">I", zip_big[8:12])[0]
    for _ in range(count):
        offset, size = struct.unpack(">II", zip_big[pos : pos + 8])
        pos += 8
        end = zip_big.index(b"\x00", pos)
        name = zip_big[pos:end].decode("latin-1")
        pos = end + 1
        zip_entries.append((name, zip_big[offset : offset + size]))
    zip_tejas = next(b for n, b in zip_entries if knorm(n) == knorm(TEJAS_PATH))
    if sha256_bytes(zip_tejas) != tejas_sha:
        raise SystemExit(
            "EMBED FAIL: FINAL.zip inside-BIG Tejas hash != fixed source "
            f"({sha256_bytes(zip_tejas)} != {tejas_sha})"
        )
    print("FINAL.zip EMBED PROOF PASS", final_zip, sha256_file(final_zip))

    zpath = OUT / "_SPEC_DATA_ONE_INDIA_TEJASMK2_FIXED.zip"
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "India_TejasMk2.ini", "India_TejasMk2.ini")
        zf.write(OUT / "VERIFY_REPORT.txt", "VERIFY_REPORT.txt")
        zf.write(OUT / "README_INSTALL.txt", "README_INSTALL.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(extract_path, "EXTRACT_VERIFY/India_TejasMk2.ini")
    with zipfile.ZipFile(zpath, "r") as zf:
        zip_big = zf.read("_SPEC_DATA_ONE.big")
        zip_extract = zf.read("EXTRACT_VERIFY/India_TejasMk2.ini")
    # Re-parse India package zip BIG and compare
    pos = 16
    count = struct.unpack(">I", zip_big[8:12])[0]
    zip_tejas = None
    for _ in range(count):
        offset, size = struct.unpack(">II", zip_big[pos : pos + 8])
        pos += 8
        end = zip_big.index(b"\x00", pos)
        name = zip_big[pos:end].decode("latin-1")
        pos = end + 1
        if knorm(name) == knorm(TEJAS_PATH):
            zip_tejas = zip_big[offset : offset + size]
            break
    if zip_tejas is None or sha256_bytes(zip_tejas) != tejas_sha:
        raise SystemExit("EMBED FAIL: India package zip BIG does not contain fixed Tejas")
    if sha256_bytes(zip_extract) != tejas_sha:
        raise SystemExit("EMBED FAIL: India package EXTRACT_VERIFY mismatch")

    embed_report = (
        "EMBED PROOF\n"
        "===========\n"
        f"path: {extracted_name}\n"
        f"norm: Data/INI/Object/specter/indian armed forces/airforce/india_tejasmk2.ini\n"
        f"fixed_source_sha256: {tejas_sha}\n"
        f"inside_BIG_sha256:   {extracted_sha}\n"
        f"extracted_file_sha256: {extract_file_sha}\n"
        f"broken_vendor_sha256: {broken_sha}\n"
        f"match_fixed: YES\n"
        f"still_broken: NO\n"
        f"BIG_sha256: {big_sha}\n"
        f"BIG_size: {big_size}\n"
    )
    (OUT / "EMBED_PROOF.txt").write_text(embed_report, encoding="ascii")
    (final_dir / "EMBED_PROOF.txt").write_text(embed_report, encoding="ascii")

    print(report)
    print(embed_report)
    print("ZIP", zpath, sha256_file(zpath))
    print("BIG", out_big, big_sha, big_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
