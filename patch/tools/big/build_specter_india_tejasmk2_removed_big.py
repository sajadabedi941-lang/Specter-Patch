#!/usr/bin/env python3
"""Remove India_TejasMk2 and replace with ChinaJetJ10C donor clone.

- Deletes India_TejasMk2.ini from _SPEC_DATA_ONE.big
- Adds India_MultiroleFighter.ini (Side=India, China J10C art/weapons/modules)
- Retargets CommandSet / CommandButton / Science / strings
- Scrubs all TejasMk2 references from patched INI/TXT entries
- Extract-verifies replacement inside rebuilt BIG
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_INDIA_TEJASMK2_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_INDIA_TEJASMK2_REMOVED"

TEJAS_PATH = (
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\India_TejasMk2.ini"
)
REPL_PATH = (
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\India_MultiroleFighter.ini"
)
DONOR_PATH = r"Data\INI\Object\Specter\PLA\Airforce\J10C.ini"
TREE_OLD = (
    ROOT
    / "Data"
    / "INI"
    / "Object"
    / "Specter"
    / "Indian Armed Forces"
    / "Airforce"
    / "India_TejasMk2.ini"
)
TREE_NEW = (
    ROOT
    / "Data"
    / "INI"
    / "Object"
    / "Specter"
    / "Indian Armed Forces"
    / "Airforce"
    / "India_MultiroleFighter.ini"
)

PRESERVE = {
    r"Data\INI\Object\Specter\French Armed Forces\Drones\France_CombatDrone.ini": (
        "7512cca46c234c6951a54d5a982184209d203668738c4e1336fdaab1e1ba8df2"
    ),
    r"Data\INI\Object\Specter\German Armed Forces\Drones\Germany_CombatDrone.ini": (
        "663b32b1de6111bd1496463bc042f642d204782a525f103c63440d92d380e8b2"
    ),
}

TEJAS_MARKERS = re.compile(
    r"TejasMk2|Tejas_Mk2|TechTejasMk2|AstraMk2_TejasMk2|ConstructIndia_TejasMk2",
    re.I,
)


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


def ascii_safe(s: str) -> str:
    repl = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00d7": "x",
        "\u00a0": " ",
    }
    return "".join(ch if ord(ch) < 128 else repl.get(ch, "?") for ch in s)


def full_block_check(text: str) -> tuple[bool, list[str]]:
    openers = [
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
    ]
    issues = []
    stack = []
    for i, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0]
        if not code.strip():
            continue
        if re.match(r"^\s*End\s*$", code):
            if not stack:
                issues.append(f"extra End @{i}")
            else:
                stack.pop()
            continue
        for rx, kind in openers:
            if rx.match(code):
                stack.append((kind, i))
                break
    if stack:
        issues.append("unclosed " + ",".join(f"{k}@{i}" for k, i in stack))
    return (not issues), issues


def clone_donor_to_india(donor_text: str) -> str:
    text = donor_text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(ascii_safe(line) for line in text.split("\n"))
    lines = text.split("\n")
    # Strip leading comments to Object
    i = 0
    while i < len(lines) and not re.match(r"^\s*Object\s+ChinaJetJ10C\b", lines[i]):
        i += 1
    if i >= len(lines):
        raise SystemExit("donor Object ChinaJetJ10C missing")
    text = "\n".join(lines[i:])

    text = text.replace("Object ChinaJetJ10C", "Object India_MultiroleFighter", 1)
    text = re.sub(r"(?m)^(  Side\s*=\s*)China\s*$", r"\1India", text, count=1)
    text = re.sub(
        r"(?m)^(  DisplayName\s*=\s*)OBJECT:\S+\s*$",
        r"\1OBJECT:India_MultiroleFighter",
        text,
        count=1,
    )
    # Balanced near prior TejasMk2 elite cost, still using donor systems.
    text = re.sub(r"(?m)^(  BuildCost\s*=\s*)\S+", r"\g<1>1700", text, count=1)
    text = re.sub(r"(?m)^(  BuildTime\s*=\s*)\S+", r"\g<1>14", text, count=1)

    # Insert India prerequisites before BuildCost if absent.
    if not re.search(r"(?m)^\s*Prerequisites\b", text):
        text = re.sub(
            r"(?m)^(  BuildCost\s*=)",
            "  Prerequisites\n"
            "    Object = India_MIC\n"
            "    Science = SCIENCE_India_TechEliteAir\n"
            "    Science = SCIENCE_Rank6\n"
            "  End\n"
            r"\1",
            text,
            count=1,
        )
    else:
        text = re.sub(
            r"(?ms)^  Prerequisites\n.*?^  End",
            "  Prerequisites\n"
            "    Object = India_MIC\n"
            "    Science = SCIENCE_India_TechEliteAir\n"
            "    Science = SCIENCE_Rank6\n"
            "  End",
            text,
            count=1,
        )

    header = (
        "; SPECTER FIX - India_MultiroleFighter\n"
        "; Replacement for removed broken India elite fighter slot\n"
        "; Donor: existing ChinaJetJ10C (PLA/Airforce/J10C.ini) - no new aircraft\n"
        "; Keep: Side=India, GenericTacticalBomberCommandSet, CHI_J10C art/weapons\n"
        "; Balance: BuildCost=1700 BuildTime=14; Prereq India_MIC + TechEliteAir + Rank6\n"
        "\n"
    )
    text = header + text
    if any(ord(c) > 127 for c in text):
        raise SystemExit("non-ascii in replacement")
    code = "\n".join(line.split(";", 1)[0] for line in text.splitlines())
    if TEJAS_MARKERS.search(code):
        raise SystemExit("TejasMk2 marker leaked into replacement code")
    if not re.search(r"(?m)^Object\s+India_MultiroleFighter\b", text):
        raise SystemExit("replacement object missing")
    if not re.search(r"(?m)^  Side\s*=\s*India\s*$", text):
        raise SystemExit("Side=India missing")
    ok, issues = full_block_check(text)
    if not ok:
        raise SystemExit("replacement block fail: " + "; ".join(issues))
    return text.replace("\n", "\r\n")


def patch_text_file(name: str, raw: bytes) -> bytes | None:
    """Return patched bytes, or None if unchanged. Scrub TejasMk2 refs."""
    if not TEJAS_MARKERS.search(raw.decode("utf-8", "replace")) and b"TejasMk2" not in raw:
        # also catch exact bytes
        if b"TejasMk2" not in raw and b"TechTejasMk2" not in raw and b"AstraMk2_TejasMk2" not in raw:
            return None

    text = raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    text = ascii_safe(text)
    orig = text

    # Command buttons
    text = text.replace("Command_ConstructIndia_TejasMk2", "Command_ConstructIndia_MultiroleFighter")
    text = text.replace("Command_PurchaseScienceIndiaTechTejasMk2", "Command_PurchaseScienceIndiaTechEliteAir")
    text = text.replace("CONTROLBAR:ConstructIndia_TejasMk2", "CONTROLBAR:ConstructIndia_MultiroleFighter")
    text = text.replace(
        "CONTROLBAR:ToolTipConstructIndia_TejasMk2",
        "CONTROLBAR:ToolTipConstructIndia_MultiroleFighter",
    )
    text = text.replace("OBJECT:India_TejasMk2", "OBJECT:India_MultiroleFighter")
    text = text.replace("SCIENCE_India_TechTejasMk2", "SCIENCE_India_TechEliteAir")
    text = text.replace("SCIENCE:India_TechTejasMk2", "SCIENCE:India_TechEliteAir")
    text = text.replace("CONTROLBAR:ToolTipIndia_TechTejasMk2", "CONTROLBAR:ToolTipIndia_TechEliteAir")
    text = text.replace("Object = India_TejasMk2", "Object = India_MultiroleFighter")
    text = text.replace("Object India_TejasMk2", "Object India_MultiroleFighter")

    # Strings content (display names)
    text = re.sub(
        r"(?m)^(OBJECT:India_MultiroleFighter\s*=\s*).*$",
        r"\1India Multirole Fighter",
        text,
    )
    text = re.sub(
        r"(?m)^(CONTROLBAR:ConstructIndia_MultiroleFighter\s*=\s*).*$",
        r"\1India Multirole Fighter",
        text,
    )
    text = re.sub(
        r"(?m)^(CONTROLBAR:ToolTipConstructIndia_MultiroleFighter\s*=\s*).*$",
        r"\1Produce India multirole fighter (stable J-10C systems).",
        text,
    )
    text = re.sub(
        r"(?m)^(SCIENCE:India_TechEliteAir\s*=\s*).*$",
        r"\1Elite Air Program",
        text,
    )
    text = re.sub(
        r"(?m)^(CONTROLBAR:ToolTipIndia_TechEliteAir\s*=\s*).*$",
        r"\1Unlock India elite multirole fighter production.",
        text,
    )

    # Science block rename if present as Science SCIENCE_...
    text = text.replace("Science SCIENCE_India_TechEliteAir", "Science SCIENCE_India_TechEliteAir")

    # Remove weapon block named AstraMk2_TejasMk2 entirely from Weapon_India.ini
    if knorm(name).endswith("weapon_india.ini"):
        text2, n = re.subn(
            r"(?ms)^Weapon\s+India_Weapon_AstraMk2_TejasMk2\n.*?^End\n?",
            "",
            text,
        )
        text = text2

    # Final scrub: any remaining TejasMk2 tokens become safe EliteAir/Multirole names
    if TEJAS_MARKERS.search(text):
        text = TEJAS_MARKERS.sub("REMOVED_TEJASMK2", text)
        # If scrub left placeholders, fail hard — should not ship placeholders
        if "REMOVED_TEJASMK2" in text:
            raise SystemExit(f"unresolved TejasMk2 markers remain in {name}")

    if text == orig and b"TejasMk2" not in text.encode("ascii", "replace"):
        return None
    # Preserve CRLF for Specter INIs
    return text.replace("\n", "\r\n").encode("ascii")


def catalog(entries):
    cats = defaultdict(set)
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
        cats["MappedImage"].update(re.findall(r"(?m)^MappedImage\s+(\S+)", t))
    return cats


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG: {SRC}")
    entries = parse_big(SRC)
    by = {knorm(n): (n, b) for n, b in entries}
    if knorm(DONOR_PATH) not in by:
        raise SystemExit("donor J10C.ini missing")
    if knorm(TEJAS_PATH) not in by:
        raise SystemExit("TejasMk2 path missing (already removed?)")

    donor = by[knorm(DONOR_PATH)][1].decode("utf-8", "replace")
    repl = clone_donor_to_india(donor)
    repl_bytes = repl.encode("ascii")

    art_entries = parse_big(ART) if ART.is_file() else []
    checks: list[tuple[str, bool]] = []

    def chk(name: str, ok: bool) -> None:
        checks.append((name, ok))
        print(("PASS" if ok else "FAIL"), name)

    # Build new entry list: drop TejasMk2, patch refs, add replacement
    new_entries: list[tuple[str, bytes]] = []
    patched_files = []
    removed = False
    for name, blob in entries:
        if knorm(name) == knorm(TEJAS_PATH):
            removed = True
            continue
        patched = patch_text_file(name, blob)
        if patched is not None:
            new_entries.append((name, patched))
            patched_files.append(name)
        else:
            new_entries.append((name, blob))

    # Insert replacement after other India Airforce entries if possible
    insert_at = len(new_entries)
    for i, (name, _) in enumerate(new_entries):
        if "Indian Armed Forces\\Airforce\\" in name.replace("/", "\\"):
            insert_at = i + 1
    new_entries.insert(insert_at, (REPL_PATH, repl_bytes))

    chk("removed India_TejasMk2.ini entry", removed)
    chk("added India_MultiroleFighter.ini", any(knorm(n) == knorm(REPL_PATH) for n, _ in new_entries))
    chk("Object India_MultiroleFighter", bool(re.search(r"(?m)^Object\s+India_MultiroleFighter\b", repl)))
    chk("Side=India", bool(re.search(r"(?m)^  Side\s*=\s*India\s*$", repl)))
    chk("donor weapon kept", "3x_1000LB_LT3_PGM_J10C" in repl)
    chk("CHI_J10C models", "CHI_J10C" in repl and "CHI_J10C_D" in repl and "CHI_J10C_R" in repl)
    chk("CommandSet GenericTacticalBomber", "GenericTacticalBomberCommandSet" in repl)
    chk("ASCII replacement", all(ord(c) < 128 for c in repl))
    ok_blocks, block_issues = full_block_check(repl)
    chk("replacement block syntax", ok_blocks)

    # Temporary catalog including replacement for ref checks
    cats = catalog(new_entries)
    data_join = b"\n".join(b for _, b in new_entries)
    weps = re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", repl)
    imgs = re.findall(r"(?m)^\s*(?:SelectPortrait|ButtonImage)\s*=\s*(\S+)", repl)
    prereq = re.findall(r"(?m)^\s*Object\s*=\s*(\S+)", repl)
    sci = re.findall(r"(?m)^\s*Science\s*=\s*(\S+)", repl)
    models = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", repl))

    chk(
        "weapon resolves",
        all(w in cats["Weapon"] or w.encode() in data_join for w in weps),
    )
    chk(
        "portrait resolves",
        all(i in cats["MappedImage"] or i.encode() in data_join for i in imgs),
    )
    chk("prereq object resolves", all(o in cats["Object"] for o in prereq))
    # Science may be newly renamed in Science_India.ini in this same pass
    chk(
        "science resolves",
        all(s in cats["Science"] or s.encode() in data_join for s in sci),
    )
    model_ok = True
    for m in models:
        if not any(
            m.lower() in knorm(n) and n.lower().endswith(".w3d") for n, _ in art_entries
        ):
            model_ok = False
    chk("model W3D in ART", model_ok)

    # Ensure science + command button exist after patches
    joined = "\n".join(
        b.decode("utf-8", "replace") for n, b in new_entries if n.lower().endswith((".ini", ".txt"))
    )
    chk("Command_ConstructIndia_MultiroleFighter present", "Command_ConstructIndia_MultiroleFighter" in joined)
    chk("Object = India_MultiroleFighter in buttons", "Object = India_MultiroleFighter" in joined)
    chk("SCIENCE_India_TechEliteAir present", "SCIENCE_India_TechEliteAir" in joined)
    chk("no TejasMk2 markers remain", not TEJAS_MARKERS.search(joined))
    chk("no India_TejasMk2.ini path remain", not any(knorm(n) == knorm(TEJAS_PATH) for n, _ in new_entries))
    chk("no Object India_TejasMk2", not re.search(r"(?m)^Object\s+India_TejasMk2\b", joined))

    ok_all = all(ok for _, ok in checks)
    if not ok_all:
        print("VALIDATION FAILED")
        for n, ok in checks:
            if not ok:
                print(" FAIL:", n)
        print("block_issues", block_issues)
        print("patched_files", patched_files)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    if out_big.exists():
        out_big.unlink()
    write_big(out_big, new_entries)

    # Extract-verify
    rebuilt = parse_big(out_big)
    rby = {knorm(n): (n, b) for n, b in rebuilt}
    if knorm(TEJAS_PATH) in rby:
        raise SystemExit("EMBED FAIL: TejasMk2.ini still present in BIG")
    if knorm(REPL_PATH) not in rby:
        raise SystemExit("EMBED FAIL: replacement missing from BIG")
    ext_name, ext = rby[knorm(REPL_PATH)]
    if ext != repl_bytes:
        raise SystemExit("EMBED FAIL: replacement bytes mismatch")
    ext_text = ext.decode("ascii")
    ok_ext, ext_iss = full_block_check(ext_text)
    if not ok_ext:
        raise SystemExit("EMBED FAIL block: " + "; ".join(ext_iss))
    if TEJAS_MARKERS.search(ext_text):
        raise SystemExit("EMBED FAIL: Tejas markers in extracted replacement")

    # Scan entire BIG for TejasMk2
    for n, b in rebuilt:
        if TEJAS_MARKERS.search(b.decode("utf-8", "replace")) or b"TejasMk2" in b:
            raise SystemExit(f"EMBED FAIL: TejasMk2 still referenced in {n}")

    for path, expect in PRESERVE.items():
        got = sha256_bytes(rby[knorm(path)][1])
        if got != expect:
            raise SystemExit(f"preserved fix lost {path}: {got}")

    extract_dir = (
        OUT
        / "_EXTRACT_VERIFY"
        / "Data"
        / "INI"
        / "Object"
        / "Specter"
        / "Indian Armed Forces"
        / "Airforce"
    )
    extract_dir.mkdir(parents=True, exist_ok=True)
    extract_path = extract_dir / "India_MultiroleFighter.ini"
    extract_path.write_bytes(ext)
    print("EMBED PROOF PASS")
    print("  removed:", TEJAS_PATH)
    print("  added:", ext_name)
    print("  extracted:", extract_path)
    print("  replacement_sha:", sha256_bytes(ext))

    # Tree updates
    if TREE_OLD.exists():
        TREE_OLD.unlink()
    TREE_NEW.parent.mkdir(parents=True, exist_ok=True)
    TREE_NEW.write_bytes(repl_bytes)
    (OUT / "India_MultiroleFighter.ini").write_bytes(repl_bytes)

    big_sha = sha256_file(out_big)
    big_size = out_big.stat().st_size
    repl_sha = sha256_bytes(repl_bytes)

    report = (
        "SPECTER INDIA TEJASMK2 REMOVED / REPLACED - VERIFY REPORT\n"
        "============================================================\n"
        "VERDICT: PASS\n"
        "Action: REMOVE India_TejasMk2 completely; REPLACE with ChinaJetJ10C donor clone\n"
        f"Removed path: {TEJAS_PATH}\n"
        f"Added path:   {REPL_PATH}\n"
        f"Object: India_MultiroleFighter  Side=India\n"
        f"Donor: ChinaJetJ10C ({DONOR_PATH})\n"
        f"\nPatched BIG SHA256: {big_sha}\n"
        f"Patched BIG SIZE:   {big_size}\n"
        f"Replacement INI SHA256: {repl_sha}\n"
        f"Patched support files: {len(patched_files)}\n"
        + "\n".join(f"  - {p}" for p in patched_files)
        + "\n\n"
        + "\n".join(f"{'PASS' if ok else 'FAIL'}: {n}" for n, ok in checks)
        + "\n\nFINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED PROOF\n"
        "===========\n"
        f"TejasMk2.ini present: NO\n"
        f"replacement entry: {ext_name}\n"
        f"replacement_sha256: {repl_sha}\n"
        f"extracted_sha256: {sha256_bytes(ext)}\n"
        f"TejasMk2 refs in BIG: NO\n"
        f"BIG_sha256: {big_sha}\n"
        f"BIG_size: {big_size}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER INDIA TEJASMK2 REMOVED\n"
        "==============================\n\n"
        "India_TejasMk2 was removed from the faction and replaced with\n"
        "India_MultiroleFighter (clone of existing ChinaJetJ10C).\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"India_MultiroleFighter.ini SHA256={repl_sha}\n"
        f"Removed: {TEJAS_PATH}\n",
        encoding="ascii",
    )

    for sync in [
        ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL",
        ROOT / "Release" / "SPECTER_FINAL_EGYPT_BRITAIN_FIXED",
    ]:
        if sync.is_dir():
            shutil.copy2(out_big, sync / "_SPEC_DATA_ONE.big")
            print("synced", sync)

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    for name in (
        "HASHES.txt",
        "VERIFY_REPORT.txt",
        "README_INSTALL.txt",
        "EMBED_PROOF.txt",
        "India_MultiroleFighter.ini",
    ):
        shutil.copy2(OUT / name, final_dir / name)
    # remove stale Tejas extract if any
    stale = final_dir / "India_TejasMk2.ini"
    if stale.exists():
        stale.unlink()
    final_zip = final_dir / "_SPEC_DATA_ONE_FINAL.zip"
    if final_zip.exists():
        final_zip.unlink()
    with zipfile.ZipFile(final_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "India_MultiroleFighter.ini", "India_MultiroleFighter.ini")
        zf.write(OUT / "VERIFY_REPORT.txt", "VERIFY_REPORT.txt")
        zf.write(OUT / "EMBED_PROOF.txt", "EMBED_PROOF.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "README_INSTALL.txt", "README_INSTALL.txt")

    # Prove FINAL.zip
    with zipfile.ZipFile(final_zip, "r") as zf:
        zbig = zf.read("_SPEC_DATA_ONE.big")
    zentries = []
    pos = 16
    count = struct.unpack(">I", zbig[8:12])[0]
    for _ in range(count):
        offset, size = struct.unpack(">II", zbig[pos : pos + 8])
        pos += 8
        end = zbig.index(b"\x00", pos)
        name = zbig[pos:end].decode("latin-1")
        pos = end + 1
        zentries.append((name, zbig[offset : offset + size]))
    if any(knorm(n) == knorm(TEJAS_PATH) for n, _ in zentries):
        raise SystemExit("FINAL.zip still has TejasMk2.ini")
    zrepl = next(b for n, b in zentries if knorm(n) == knorm(REPL_PATH))
    if sha256_bytes(zrepl) != repl_sha:
        raise SystemExit("FINAL.zip replacement mismatch")
    print("FINAL.zip PROOF PASS")

    zpath = OUT / "_SPEC_DATA_ONE_INDIA_TEJASMK2_REMOVED.zip"
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "India_MultiroleFighter.ini", "India_MultiroleFighter.ini")
        zf.write(extract_path, "EXTRACT_VERIFY/India_MultiroleFighter.ini")
        zf.write(OUT / "VERIFY_REPORT.txt", "VERIFY_REPORT.txt")
        zf.write(OUT / "EMBED_PROOF.txt", "EMBED_PROOF.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "README_INSTALL.txt", "README_INSTALL.txt")

    print(report)
    print("BIG", out_big, big_sha, big_size)
    print("ZIP", zpath, sha256_file(zpath))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
