#!/usr/bin/env python3
"""Repair India_CommandCenter inside _SPEC_DATA_ONE.big (USA CommandCenter donor).

Same pattern as Egypt_CommandCenter / France-Germany aircraft fixes:
- Patch INSIDE the DATA BIG (not loose-only)
- Full Object/Draw/Shadow/ModuleTag/End/W3D/ref validation
- Extract-from-BIG verify after write

Donor: AmericaCommandCenter (proven working building structure).
Keep: Object India_CommandCenter, Side=India, India_CommandCenterCommandSet,
      India DisplayName. Strip Iraq/Irq crash tokens and non-ASCII.
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
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_INDIA_ELITESTRIKE_SIMPLE" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_INDIA_CC_FIXED"

CC_PATH = (
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_CommandCenter.ini"
)
USA_PATH = (
    r"Data\INI\Object\Specter\United States Of America\Buildings\CommandCenter.ini"
)
TREE = (
    ROOT
    / "Data/INI/Object/Specter/Indian Armed Forces/Buildings/India_CommandCenter.ini"
)

PRESERVE = {
    r"Data\INI\Object\Specter\French Armed Forces\Drones\France_CombatDrone.ini": (
        "7512cca46c234c6951a54d5a982184209d203668738c4e1336fdaab1e1ba8df2"
    ),
    r"Data\INI\Object\Specter\German Armed Forces\Drones\Germany_CombatDrone.ini": (
        "663b32b1de6111bd1496463bc042f642d204782a525f103c63440d92d380e8b2"
    ),
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\India_EliteStrike.ini": (
        "0f9af6019f0976cd219d393f94fda3e17bb6d74eeb933513a0f48aa13b665533"
    ),
}

CRASH_TOKENS = re.compile(
    r"Irq_Command|irq_comndcntr|Iraq_Adnan1|SUPERWEAPON_Iraqi|SUPERWEAPON_Iraq|"
    r"Iraq_CommandCenter|Object Iraq_",
    re.I,
)

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


def full_block_check(text: str) -> tuple[bool, list[str]]:
    issues: list[str] = []
    stack: list[tuple[str, int]] = []
    for i, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0]
        if not code.strip():
            continue
        if re.match(r"^\s*End\s*$", code):
            if not stack:
                issues.append(f"EXTRA End @{i}")
            else:
                stack.pop()
            continue
        for rx, kind in OPENERS:
            if rx.match(code):
                stack.append((kind, i))
                break
    if stack:
        issues.append("UNCLOSED " + ",".join(f"{k}@{i}" for k, i in stack))
    return (not issues), issues


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
        cats["SpecialPower"].update(re.findall(r"(?m)^SpecialPower\s+(\S+)", t))
    return cats


def validate_building_ini(
    text: str,
    *,
    expect_object: str,
    expect_side: str,
    entries,
    art_entries,
    label: str,
) -> list[str]:
    fails: list[str] = []
    cats = catalog(entries)
    data_join = b"\n".join(b for _, b in entries)

    if any(ord(c) > 127 for c in text):
        fails.append(f"{label}: non-ASCII")
    ok, issues = full_block_check(text)
    if not ok:
        fails.append(f"{label}: block syntax {issues}")
    objs = re.findall(r"(?m)^Object\s+(\S+)", text)
    if objs != [expect_object]:
        fails.append(f"{label}: Object={objs} expected [{expect_object}]")
    if not re.search(rf"(?m)^  Side\s*=\s*{re.escape(expect_side)}\s*$", text):
        fails.append(f"{label}: Side!={expect_side}")
    if not re.search(r"(?m)^\s*Draw\s*=\s*W3DModelDraw\b", text):
        fails.append(f"{label}: Draw W3DModelDraw missing")
    shadows = re.findall(r"(?m)^\s*Shadow\s*=\s*(\S+)", text)
    if len(shadows) != 1 or shadows[0] != "SHADOW_VOLUME":
        fails.append(f"{label}: Shadow={shadows}")
    tags = re.findall(r"ModuleTag_\S+", text)
    dups = [t for t, c in Counter(tags).items() if c > 1]
    if dups:
        fails.append(f"{label}: duplicate ModuleTags {dups}")
    if "Geometry" not in text or "GeometryMajorRadius" not in text:
        fails.append(f"{label}: Geometry missing")
    if not re.search(r"(?m)^\s*KindOf\s*=", text):
        fails.append(f"{label}: KindOf missing")
    if "COMMANDCENTER" not in text:
        fails.append(f"{label}: KindOf COMMANDCENTER missing")
    if CRASH_TOKENS.search(text):
        fails.append(f"{label}: crash tokens {CRASH_TOKENS.findall(text)}")

    def need(kind: str, vals: list[str]) -> None:
        for v in vals:
            if v in ("None", "NONE"):
                continue
            if v not in cats[kind] and v.encode() not in data_join:
                fails.append(f"{label}: missing {kind}={v}")

    need("CommandSet", re.findall(r"(?m)^\s*CommandSet\s*=\s*(\S+)", text))
    need("Armor", re.findall(r"(?m)^\s*Armor\s*=\s*(\S+)", text))
    need("Science", re.findall(r"(?m)^\s*(?:Science|GrantScience)\s*=\s*(\S+)", text))
    need("Object", re.findall(r"(?m)^\s*Object\s*=\s*(\S+)", text))
    need(
        "Upgrade",
        re.findall(r"(?m)^\s*(?:UpgradeCameo\d*|TriggeredBy|UpgradeToGrant)\s*=\s*(\S+)", text),
    )
    need("MappedImage", re.findall(r"(?m)^\s*(?:SelectPortrait|ButtonImage)\s*=\s*(\S+)", text))
    need("OCL", re.findall(r"(?m)^\s*(?:OCL|CreationList|UpgradeObject)\s*=\s*(\S+)", text))
    need(
        "OCL",
        re.findall(r"(?m)^\s*UpgradeOCL\s*=\s*\S+\s+(\S+)", text),
    )
    need(
        "SpecialPower",
        re.findall(r"(?m)^\s*SpecialPowerTemplate\s*=\s*(\S+)", text),
    )
    need("Object", re.findall(r"(?m)^\s*GunshipTemplateName\s*=\s*(\S+)", text))

    for m in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)):
        if m in ("None", "NONE"):
            continue
        w3d = [
            n
            for n, _ in art_entries
            if m.lower() in knorm(n) and n.lower().endswith(".w3d")
        ]
        if not w3d:
            fails.append(f"{label}: ModelW3D missing {m}")
    return fails


def clone_usa_to_india(usa_text: str) -> str:
    text = usa_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    i = 0
    while i < len(lines) and (lines[i].strip() == "" or lines[i].lstrip().startswith(";")):
        i += 1
    text = "\n".join(lines[i:])
    if not text.startswith("Object AmericaCommandCenter"):
        raise SystemExit("unexpected USA CommandCenter start")

    text = text.replace("Object AmericaCommandCenter", "Object India_CommandCenter", 1)
    text = re.sub(r"(?m)^(  Side\s*=\s*)America\s*$", r"\1India", text, count=1)
    text = re.sub(
        r"(?m)^(  DisplayName\s*=\s*)OBJECT:CommandCenter\s*$",
        r"\1OBJECT:India_CommandCenter",
        text,
        count=1,
    )
    # Keep India naming for CommandSet (build buttons stay India_*)
    text = re.sub(
        r"(?m)^(  CommandSet\s*=\s*)AmericaCommandCenterCommandSet\s*$",
        r"\1India_CommandCenterCommandSet",
        text,
        count=1,
    )

    # Deduplicate Shadow if donor ever doubles it
    seen_shadow = False
    out_lines: list[str] = []
    for line in text.split("\n"):
        if re.match(r"^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", line):
            if seen_shadow:
                continue
            seen_shadow = True
        out_lines.append(line)
    text = "\n".join(out_lines)

    header = (
        "; SPECTER FIX - India_CommandCenter\n"
        "; Donor: AmericaCommandCenter (complete working CommandCenter structure)\n"
        "; Keep: Object India_CommandCenter / Side=India / India_CommandCenterCommandSet\n"
        "; Art/behaviors from USA CC (US_Command); no Iraq/Irq modules\n"
        "; Full validation + embed-in-BIG extract verify\n"
        "\n"
    )
    text = header + text
    text = "".join(c if ord(c) < 128 else "?" for c in text)

    if "Object India_CommandCenter" not in text:
        raise SystemExit("Object India_CommandCenter missing")
    if not re.search(r"(?m)^  Side\s*=\s*India\s*$", text):
        raise SystemExit("Side India missing")
    if "India_CommandCenterCommandSet" not in text:
        raise SystemExit("India CommandSet missing")
    if CRASH_TOKENS.search(text):
        raise SystemExit(f"Iraq/Irq tokens remain: {CRASH_TOKENS.findall(text)}")
    if "US_Command" not in text or "us_commandcenter" not in text:
        raise SystemExit("USA model/icons missing")
    if "Object AmericaCommandCenter" in text:
        raise SystemExit("donor object name remain")
    return text.replace("\n", "\r\n")


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG {SRC}")
    entries = parse_big(SRC)
    by = {knorm(n): (n, b) for n, b in entries}
    art_entries = parse_big(ART) if ART.is_file() else []
    if knorm(USA_PATH) not in by:
        raise SystemExit("USA CommandCenter donor missing")
    if knorm(CC_PATH) not in by:
        raise SystemExit("India_CommandCenter missing from source BIG")

    usa_raw = by[knorm(USA_PATH)][1]
    usa_text = usa_raw.decode("utf-8", "replace")
    old_raw = by[knorm(CC_PATH)][1]
    old_text = old_raw.decode("utf-8", "replace")

    # Confirm broken before replace
    old_fails = []
    if any(ord(c) > 127 for c in old_text):
        old_fails.append("non-ASCII")
    if CRASH_TOKENS.search(old_text):
        old_fails.append(f"crash tokens {CRASH_TOKENS.findall(old_text)}")
    print("OLD India_CommandCenter issues:", old_fails or ["none flagged"])

    donor_fails = validate_building_ini(
        usa_text,
        expect_object="AmericaCommandCenter",
        expect_side="America",
        entries=entries,
        art_entries=art_entries,
        label="DONOR_USA_CC",
    )
    if donor_fails:
        print("DONOR VALIDATION FAILED")
        for f in donor_fails:
            print(" ", f)
        return 1
    print("PASS donor AmericaCommandCenter full validation")

    repl = clone_usa_to_india(usa_text)
    tmp_entries = [(n, b) for n, b in entries if knorm(n) != knorm(CC_PATH)]
    tmp_entries.append((CC_PATH, repl.encode("ascii")))
    repl_fails = validate_building_ini(
        repl,
        expect_object="India_CommandCenter",
        expect_side="India",
        entries=tmp_entries,
        art_entries=art_entries,
        label="INDIA_CC",
    )
    if repl_fails:
        print("REPLACEMENT VALIDATION FAILED (not writing BIG)")
        for f in repl_fails:
            print(" ", f)
        return 1
    print("PASS India_CommandCenter full validation (pre-write)")

    new_entries: list[tuple[str, bytes]] = []
    replaced = False
    for name, blob in entries:
        if knorm(name) == knorm(CC_PATH):
            new_entries.append((name, repl.encode("ascii")))
            replaced = True
        else:
            new_entries.append((name, blob))
    if not replaced:
        raise SystemExit("failed to replace India_CommandCenter entry")

    checks: list[tuple[str, bool]] = []

    def chk(n: str, ok: bool) -> None:
        checks.append((n, ok))
        print(("PASS" if ok else "FAIL"), n)

    chk("replaced India_CommandCenter", replaced)
    chk("Object India_CommandCenter", "Object India_CommandCenter" in repl)
    chk("Side India", bool(re.search(r"(?m)^  Side\s*=\s*India\s*$", repl)))
    chk("India CommandSet", "India_CommandCenterCommandSet" in repl)
    chk("USA model US_Command", "US_Command" in repl)
    chk("USA portrait", "us_commandcenter" in repl)
    chk("no Irq_Command", "Irq_Command" not in repl)
    chk("no irq_comndcntr", "irq_comndcntr" not in repl)
    chk("no Iraq_Adnan1", "Iraq_Adnan1" not in repl)
    chk("no SUPERWEAPON_Iraqi", "SUPERWEAPON_Iraqi" not in repl)
    chk("single Shadow", len(re.findall(r"(?m)^\s*Shadow\s*=", repl)) == 1)
    chk("ASCII only", all(ord(c) < 128 for c in repl))
    chk("COMMANDCENTER KindOf", "COMMANDCENTER" in repl)

    if not all(ok for _, ok in checks):
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    if out_big.exists():
        out_big.unlink()
    write_big(out_big, new_entries)

    rebuilt = parse_big(out_big)
    rby = {knorm(n): (n, b) for n, b in rebuilt}
    if knorm(CC_PATH) not in rby:
        raise SystemExit("EXTRACT FAIL: India_CommandCenter missing")
    ename, ebytes = rby[knorm(CC_PATH)]
    repl_bytes = repl.encode("ascii")
    if ebytes != repl_bytes:
        raise SystemExit("EXTRACT FAIL: embedded bytes != replacement")
    etext = ebytes.decode("ascii")
    post_fails = validate_building_ini(
        etext,
        expect_object="India_CommandCenter",
        expect_side="India",
        entries=rebuilt,
        art_entries=art_entries,
        label="EXTRACTED",
    )
    if post_fails:
        out_big.unlink(missing_ok=True)
        print("EXTRACTED VALIDATION FAILED - BIG deleted")
        for f in post_fails:
            print(" ", f)
        return 1

    extract_dir = (
        OUT
        / "_EXTRACT_VERIFY"
        / "Data"
        / "INI"
        / "Object"
        / "Specter"
        / "Indian Armed Forces"
        / "Buildings"
    )
    extract_dir.mkdir(parents=True, exist_ok=True)
    extract_path = extract_dir / "India_CommandCenter.ini"
    extract_path.write_bytes(ebytes)
    if extract_path.read_bytes() != repl_bytes:
        raise SystemExit("EXTRACT FAIL: disk extract mismatch")

    for path, expect in PRESERVE.items():
        got = sha256_bytes(rby[knorm(path)][1])
        if got != expect:
            raise SystemExit(f"preserve lost {path}: {got}")

    # Ensure only CC content changed among preserved set + CC
    old_by = {knorm(n): b for n, b in entries}
    changed = [n for n, b in rebuilt if old_by[knorm(n)] != b]
    if changed != [ename]:
        # Allow only India_CommandCenter
        if not (len(changed) == 1 and knorm(changed[0]) == knorm(CC_PATH)):
            raise SystemExit(f"unexpected changed entries: {changed}")

    print("EXTRACT + FULL INI TEST PASS")
    print("  embedded:", ename)
    print("  sha:", sha256_bytes(ebytes))

    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(repl_bytes)
    (OUT / "India_CommandCenter.ini").write_bytes(repl_bytes)

    big_sha = sha256_file(out_big)
    big_size = out_big.stat().st_size
    repl_sha = sha256_bytes(repl_bytes)

    report = (
        "SPECTER INDIA COMMAND CENTER (USA DONOR) - VERIFY REPORT\n"
        "========================================================\n"
        "VERDICT: PASS\n"
        "Patched INSIDE: _SPEC_DATA_ONE.big\n"
        "Path: Data\\INI\\Object\\Specter\\Indian Armed Forces\\Buildings\\India_CommandCenter.ini\n"
        "Donor: AmericaCommandCenter (complete working CommandCenter)\n"
        "Keep: Object/Side=India/India_CommandCenterCommandSet/DisplayName\n"
        "Removed: Iraq/Irq model, irq portrait, Iraq_Adnan1, SUPERWEAPON_Iraqi*, non-ASCII\n"
        f"\nOld India_CC SHA256: {sha256_bytes(old_raw)}\n"
        f"New India_CC SHA256: {repl_sha}\n"
        f"BIG SHA256: {big_sha}\n"
        f"BIG SIZE:   {big_size}\n"
        "\nValidation: donor PASS, pre-write PASS, extract-from-BIG PASS\n"
        "Checked: Object/Draw/Shadow/ModuleTags/Ends/W3D/CommandSet/OCL/SpecialPower\n"
        "Preserved: France CombatDrone, Germany CombatDrone, India_EliteStrike\n"
        + "\n".join(f"PASS: {n}" for n, _ in checks)
        + "\nFINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT TEST\n"
        "====================\n"
        f"India_CommandCenter entry: {ename}\n"
        f"embedded_sha256: {repl_sha}\n"
        f"extracted_sha256: {sha256_bytes(extract_path.read_bytes())}\n"
        f"bytes_match_replacement: YES\n"
        f"full_ini_validation: PASS\n"
        f"Iraq_Irq_tokens: NONE\n"
        f"BIG_sha256: {big_sha}\n"
        f"BIG_size: {big_size}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER INDIA COMMAND CENTER FIX\n"
        "================================\n\n"
        "India_CommandCenter patched INSIDE _SPEC_DATA_ONE.big.\n"
        "Rebuilt from USA AmericaCommandCenter working structure.\n"
        "Side=India, India_CommandCenterCommandSet, US_Command art.\n"
        "All Iraq/Irq crash tokens removed.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"India_CommandCenter.ini SHA256={repl_sha}\n"
        f"Donor AmericaCommandCenter SHA256={sha256_bytes(usa_raw)}\n",
        encoding="ascii",
    )

    for sync in [
        ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL",
        ROOT / "Release" / "SPECTER_FINAL_EGYPT_BRITAIN_FIXED",
    ]:
        if sync.is_dir():
            shutil.copy2(out_big, sync / "_SPEC_DATA_ONE.big")

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    for name in (
        "HASHES.txt",
        "VERIFY_REPORT.txt",
        "README_INSTALL.txt",
        "EMBED_PROOF.txt",
        "India_CommandCenter.ini",
    ):
        if (OUT / name).exists():
            shutil.copy2(OUT / name, final_dir / name)

    final_zip = final_dir / "_SPEC_DATA_ONE_FINAL.zip"
    if final_zip.exists():
        final_zip.unlink()
    with zipfile.ZipFile(final_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "India_CommandCenter.ini", "India_CommandCenter.ini")
        zf.write(extract_path, "EXTRACT_VERIFY/India_CommandCenter.ini")
        zf.write(OUT / "VERIFY_REPORT.txt", "VERIFY_REPORT.txt")
        zf.write(OUT / "EMBED_PROOF.txt", "EMBED_PROOF.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "README_INSTALL.txt", "README_INSTALL.txt")

    zpath = OUT / "_SPEC_DATA_ONE_INDIA_CC_FIXED.zip"
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "India_CommandCenter.ini", "India_CommandCenter.ini")
        zf.write(extract_path, "EXTRACT_VERIFY/India_CommandCenter.ini")
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
