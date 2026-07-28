#!/usr/bin/env python3
"""Replace crashing India_MultiroleFighter with proven AmericaJetF35C Object.

Uses the exact working USA F35C.ini Object structure from Specter.
Only identity fields change: Object name, Side, DisplayName, Prerequisites,
BuildCost/Time. No new aircraft design.

Removes India_MultiroleFighter.ini; adds India_EliteStrike.ini.
Rebuild writes BIG only after in-memory validation; then extract-tests the
embedded INI before packaging.
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
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_INDIA_TEJASMK2_REMOVED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_INDIA_ELITESTRIKE_FIXED"

OLD_PATH = (
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\India_MultiroleFighter.ini"
)
NEW_PATH = (
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\India_EliteStrike.ini"
)
DONOR_PATH = r"Data\INI\Object\Specter\United States Of America\Airforce\F35C.ini"

TREE_OLD = ROOT / "Data/INI/Object/Specter/Indian Armed Forces/Airforce/India_MultiroleFighter.ini"
TREE_NEW = ROOT / "Data/INI/Object/Specter/Indian Armed Forces/Airforce/India_EliteStrike.ini"

PRESERVE = {
    r"Data\INI\Object\Specter\French Armed Forces\Drones\France_CombatDrone.ini": (
        "7512cca46c234c6951a54d5a982184209d203668738c4e1336fdaab1e1ba8df2"
    ),
    r"Data\INI\Object\Specter\German Armed Forces\Drones\Germany_CombatDrone.ini": (
        "663b32b1de6111bd1496463bc042f642d204782a525f103c63440d92d380e8b2"
    ),
}

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

MULTI_MARKERS = re.compile(
    r"India_MultiroleFighter|ConstructIndia_MultiroleFighter|MultiroleFighter",
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
    return cats


def validate_aircraft_ini(
    text: str,
    *,
    expect_object: str,
    expect_side: str,
    entries,
    art_entries,
    label: str,
) -> list[str]:
    """Full structural + reference validation. Returns list of failure strings."""
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
    if not re.search(r"(?m)^\s*WeaponSet\b", text):
        fails.append(f"{label}: WeaponSet missing")
    shadows = re.findall(r"(?m)^\s*Shadow\s*=\s*(\S+)", text)
    if len(shadows) != 1 or shadows[0] != "SHADOW_VOLUME":
        fails.append(f"{label}: Shadow={shadows}")
    tags = re.findall(r"ModuleTag_\S+", text)
    dups = [t for t, c in Counter(tags).items() if c > 1]
    if dups:
        fails.append(f"{label}: duplicate ModuleTags {dups}")
    if "Geometry" not in text or "GeometryMajorRadius" not in text:
        fails.append(f"{label}: Geometry missing")
    if not re.search(r"(?m)^\s*Behavior\s*=", text):
        fails.append(f"{label}: Behavior missing")

    def need(kind: str, vals: list[str]) -> None:
        for v in vals:
            if v == "None":
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
        w3d = [
            n
            for n, _ in art_entries
            if m.lower() in knorm(n) and n.lower().endswith(".w3d")
        ]
        if not w3d:
            fails.append(f"{label}: ModelW3D missing {m}")
    return fails


def clone_f35c_to_india(donor: str) -> str:
    text = donor.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    i = next(
        (idx for idx, ln in enumerate(lines) if re.match(r"^\s*Object\s+AmericaJetF35C\b", ln)),
        None,
    )
    if i is None:
        raise SystemExit("donor Object AmericaJetF35C missing")
    # Keep only from Object downward (proven structure, drop file banner)
    text = "\n".join(lines[i:])

    text = text.replace("Object AmericaJetF35C", "Object India_EliteStrike", 1)
    text = re.sub(r"(?m)^(  Side\s*=\s*)America\s*$", r"\1India", text, count=1)
    text = re.sub(
        r"(?m)^(  DisplayName\s*=\s*)OBJECT:\S+\s*$",
        r"\1OBJECT:India_EliteStrike",
        text,
        count=1,
    )
    text = re.sub(r"(?m)^(  BuildCost\s*=\s*)\S+", r"\g<1>1700", text, count=1)
    text = re.sub(r"(?m)^(  BuildTime\s*=\s*)\S+", r"\g<1>14", text, count=1)

    prereq = (
        "  Prerequisites\n"
        "    Object = India_MIC\n"
        "    Science = SCIENCE_India_TechEliteAir\n"
        "    Science = SCIENCE_Rank6\n"
        "  End\n"
    )
    if re.search(r"(?m)^\s*Prerequisites\b", text):
        text = re.sub(r"(?ms)^  Prerequisites\n.*?^  End\n?", prereq, text, count=1)
    else:
        text = re.sub(r"(?m)^(  BuildCost\s*=)", prereq + r"\1", text, count=1)

    header = (
        "; SPECTER FIX - India_EliteStrike\n"
        "; Proven donor Object structure: AmericaJetF35C (F35C.ini) verbatim modules\n"
        "; Identity only: Object/Side/DisplayName/Prereq/BuildCost/Time\n"
        "; Art/Weapons/Draw/Shadow/CommandSet unchanged from USA F35C\n"
        "\n"
    )
    text = header + text
    if any(ord(c) > 127 for c in text):
        raise SystemExit("non-ascii in EliteStrike")
    if "AmericaJetF35C" in text or "Side                    = America" in text:
        # Side line format may vary
        pass
    if re.search(r"(?m)^  Side\s*=\s*America\s*$", text):
        raise SystemExit("Side still America")
    if "Object AmericaJetF35C" in text:
        raise SystemExit("donor object name remain")
    return text.replace("\n", "\r\n")


def retarget_multirole(name: str, raw: bytes) -> bytes | None:
    if b"MultiroleFighter" not in raw and b"Multirole" not in raw:
        return None
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    orig = text
    text = text.replace("Command_ConstructIndia_MultiroleFighter", "Command_ConstructIndia_EliteStrike")
    text = text.replace("CONTROLBAR:ConstructIndia_MultiroleFighter", "CONTROLBAR:ConstructIndia_EliteStrike")
    text = text.replace(
        "CONTROLBAR:ToolTipConstructIndia_MultiroleFighter",
        "CONTROLBAR:ToolTipConstructIndia_EliteStrike",
    )
    text = text.replace("OBJECT:India_MultiroleFighter", "OBJECT:India_EliteStrike")
    text = text.replace("Object = India_MultiroleFighter", "Object = India_EliteStrike")
    text = text.replace("Object India_MultiroleFighter", "Object India_EliteStrike")
    text = text.replace("India_MultiroleFighter", "India_EliteStrike")
    text = re.sub(
        r"(?m)^(OBJECT:India_EliteStrike\s*=\s*).*$",
        r"\1India Elite Strike Fighter",
        text,
    )
    text = re.sub(
        r"(?m)^(CONTROLBAR:ConstructIndia_EliteStrike\s*=\s*).*$",
        r"\1India Elite Strike",
        text,
    )
    text = re.sub(
        r"(?m)^(CONTROLBAR:ToolTipConstructIndia_EliteStrike\s*=\s*).*$",
        r"\1Produce India elite strike fighter (USA F-35C systems).",
        text,
    )
    if MULTI_MARKERS.search(text):
        raise SystemExit(f"Multirole markers remain in {name}")
    if text == orig:
        return None
    return text.replace("\n", "\r\n").encode("ascii", "strict")


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG {SRC}")
    entries = parse_big(SRC)
    by = {knorm(n): (n, b) for n, b in entries}
    art_entries = parse_big(ART) if ART.is_file() else []
    if knorm(DONOR_PATH) not in by:
        raise SystemExit("F35C donor missing")
    if knorm(OLD_PATH) not in by:
        raise SystemExit("India_MultiroleFighter missing from source")

    donor_raw = by[knorm(DONOR_PATH)][1]
    donor_text = donor_raw.decode("utf-8", "replace")

    # STEP 1: validate donor itself before any clone
    donor_fails = validate_aircraft_ini(
        donor_text,
        expect_object="AmericaJetF35C",
        expect_side="America",
        entries=entries,
        art_entries=art_entries,
        label="DONOR_F35C",
    )
    if donor_fails:
        print("DONOR VALIDATION FAILED")
        for f in donor_fails:
            print(" ", f)
        return 1
    print("PASS donor AmericaJetF35C full INI validation")

    # STEP 2: minimal identity clone
    repl = clone_f35c_to_india(donor_text)
    # Temporary entry list for validation including replacement, excluding Multirole
    tmp_entries = [(n, b) for n, b in entries if knorm(n) != knorm(OLD_PATH)]
    tmp_entries.append((NEW_PATH, repl.encode("ascii")))
    repl_fails = validate_aircraft_ini(
        repl,
        expect_object="India_EliteStrike",
        expect_side="India",
        entries=tmp_entries,
        art_entries=art_entries,
        label="ELITESTRIKE",
    )
    if repl_fails:
        print("REPLACEMENT VALIDATION FAILED (not writing BIG)")
        for f in repl_fails:
            print(" ", f)
        return 1
    print("PASS India_EliteStrike full INI validation (pre-write)")

    # STEP 3: build new BIG entries
    new_entries: list[tuple[str, bytes]] = []
    patched = []
    removed = False
    for name, blob in entries:
        if knorm(name) == knorm(OLD_PATH):
            removed = True
            continue
        p = retarget_multirole(name, blob)
        if p is not None:
            new_entries.append((name, p))
            patched.append(name)
        else:
            new_entries.append((name, blob))
    insert_at = len(new_entries)
    for i, (name, _) in enumerate(new_entries):
        if "Indian Armed Forces\\Airforce\\" in name.replace("/", "\\"):
            insert_at = i + 1
    repl_bytes = repl.encode("ascii")
    new_entries.insert(insert_at, (NEW_PATH, repl_bytes))

    checks: list[tuple[str, bool]] = []

    def chk(n: str, ok: bool) -> None:
        checks.append((n, ok))
        print(("PASS" if ok else "FAIL"), n)

    joined = "\n".join(
        b.decode("utf-8", "replace")
        for n, b in new_entries
        if n.lower().endswith((".ini", ".txt"))
    )
    chk("removed Multirole file", removed)
    chk("added EliteStrike file", any(knorm(n) == knorm(NEW_PATH) for n, _ in new_entries))
    chk("no Multirole object", not re.search(r"(?m)^Object\s+India_MultiroleFighter\b", joined))
    chk("no Multirole path", not any(knorm(n) == knorm(OLD_PATH) for n, _ in new_entries))
    chk("EliteStrike object present", bool(re.search(r"(?m)^Object\s+India_EliteStrike\b", joined)))
    chk("Construct command present", "Command_ConstructIndia_EliteStrike" in joined)
    chk("button Object=India_EliteStrike", "Object = India_EliteStrike" in joined)
    chk("uses USA F35C CommandSet", "GenericMultiRoleFighter_AG_CommandSet" in repl)
    chk("uses US_F35A model", "US_F35A" in repl)
    chk("uses Nat_f35a portrait", "Nat_f35a" in repl)
    chk("no TejasMk2", b"TejasMk2" not in b"\n".join(b for _, b in new_entries))

    if not all(ok for _, ok in checks):
        return 1

    # STEP 4: write BIG
    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    if out_big.exists():
        out_big.unlink()
    write_big(out_big, new_entries)

    # STEP 5: extract and test embedded INI BEFORE packaging success
    rebuilt = parse_big(out_big)
    rby = {knorm(n): (n, b) for n, b in rebuilt}
    if knorm(OLD_PATH) in rby:
        raise SystemExit("EXTRACT FAIL: Multirole still in BIG")
    if knorm(NEW_PATH) not in rby:
        raise SystemExit("EXTRACT FAIL: EliteStrike missing")
    ename, ebytes = rby[knorm(NEW_PATH)]
    if ebytes != repl_bytes:
        raise SystemExit("EXTRACT FAIL: embedded bytes != source replacement")
    etext = ebytes.decode("ascii")
    post_fails = validate_aircraft_ini(
        etext,
        expect_object="India_EliteStrike",
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
        / "Airforce"
    )
    extract_dir.mkdir(parents=True, exist_ok=True)
    extract_path = extract_dir / "India_EliteStrike.ini"
    extract_path.write_bytes(ebytes)
    # also confirm extract file roundtrip
    if extract_path.read_bytes() != repl_bytes:
        raise SystemExit("EXTRACT FAIL: disk extract mismatch")

    for n, b in rebuilt:
        if b"MultiroleFighter" in b or b"India_MultiroleFighter" in b:
            raise SystemExit(f"EXTRACT FAIL: Multirole remain in {n}")
        if b"TejasMk2" in b:
            raise SystemExit(f"EXTRACT FAIL: TejasMk2 remain in {n}")

    for path, expect in PRESERVE.items():
        got = sha256_bytes(rby[knorm(path)][1])
        if got != expect:
            raise SystemExit(f"preserve lost {path}")

    print("EXTRACT + FULL INI TEST PASS")
    print("  embedded:", ename)
    print("  sha:", sha256_bytes(ebytes))
    print("  extract:", extract_path)

    # Tree
    if TREE_OLD.exists():
        TREE_OLD.unlink()
    TREE_NEW.parent.mkdir(parents=True, exist_ok=True)
    TREE_NEW.write_bytes(repl_bytes)
    (OUT / "India_EliteStrike.ini").write_bytes(repl_bytes)

    # Sync patched support files into tree
    for key in [
        r"Data\INI\CommandButton_PhaseG_Identity.ini",
        r"Data\INI\CommandSet_AdvancedAirBase.ini",
        r"Data\INI\CommandSet_India.ini",
        r"Data\English\FactionExpansion_PhaseG_Strings.txt",
    ]:
        if knorm(key) in rby:
            n, b = rby[knorm(key)]
            out = ROOT / Path(n.replace("\\", "/"))
            # ROOT is patch/, n starts with Data\
            out = Path("patch") / Path(n.replace("\\", "/"))
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b)

    big_sha = sha256_file(out_big)
    big_size = out_big.stat().st_size
    repl_sha = sha256_bytes(repl_bytes)

    report = (
        "SPECTER INDIA ELITE STRIKE (USA F35C DONOR) - VERIFY REPORT\n"
        "============================================================\n"
        "VERDICT: PASS\n"
        "Removed: India_MultiroleFighter.ini (crashing J10C clone)\n"
        "Added:   India_EliteStrike.ini\n"
        "Donor:   AmericaJetF35C / F35C.ini (proven working Object structure)\n"
        "Changes vs donor: Object/Side/DisplayName/Prereq/BuildCost/Time ONLY\n"
        f"\nBIG SHA256: {big_sha}\n"
        f"BIG SIZE:   {big_size}\n"
        f"EliteStrike SHA256: {repl_sha}\n"
        f"Patched support files: {patched}\n"
        "\nValidation: donor PASS, pre-write PASS, extract-from-BIG PASS\n"
        "Checked: Object/Draw/WeaponSet/Shadow/ModuleTags/Ends/Weapon refs/W3D\n"
        + "\n".join(f"PASS: {n}" for n, _ in checks)
        + "\nFINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT TEST\n"
        "====================\n"
        f"Multirole present: NO\n"
        f"EliteStrike entry: {ename}\n"
        f"embedded_sha256: {repl_sha}\n"
        f"extracted_sha256: {sha256_bytes(extract_path.read_bytes())}\n"
        f"full_ini_validation: PASS\n"
        f"BIG_sha256: {big_sha}\n"
        f"BIG_size: {big_size}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER INDIA ELITE STRIKE\n"
        "==========================\n\n"
        "India_MultiroleFighter removed. Replaced with India_EliteStrike\n"
        "using proven AmericaJetF35C Object structure (US_F35A).\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"India_EliteStrike.ini SHA256={repl_sha}\n"
        f"Donor AmericaJetF35C F35C.ini SHA256={sha256_bytes(donor_raw)}\n",
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
        "India_EliteStrike.ini",
    ):
        shutil.copy2(OUT / name, final_dir / name)
    for stale in ("India_MultiroleFighter.ini", "India_TejasMk2.ini"):
        p = final_dir / stale
        if p.exists():
            p.unlink()
    final_zip = final_dir / "_SPEC_DATA_ONE_FINAL.zip"
    if final_zip.exists():
        final_zip.unlink()
    with zipfile.ZipFile(final_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "India_EliteStrike.ini", "India_EliteStrike.ini")
        zf.write(extract_path, "EXTRACT_VERIFY/India_EliteStrike.ini")
        zf.write(OUT / "VERIFY_REPORT.txt", "VERIFY_REPORT.txt")
        zf.write(OUT / "EMBED_PROOF.txt", "EMBED_PROOF.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "README_INSTALL.txt", "README_INSTALL.txt")

    # Prove zip extract
    with zipfile.ZipFile(final_zip, "r") as zf:
        zbig = zf.read("_SPEC_DATA_ONE.big")
        zext = zf.read("EXTRACT_VERIFY/India_EliteStrike.ini")
    if sha256_bytes(zext) != repl_sha:
        raise SystemExit("FINAL.zip extract mismatch")
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
    if any(knorm(n) == knorm(OLD_PATH) for n, _ in zentries):
        raise SystemExit("FINAL.zip still has Multirole")
    zb = next(b for n, b in zentries if knorm(n) == knorm(NEW_PATH))
    if sha256_bytes(zb) != repl_sha:
        raise SystemExit("FINAL.zip EliteStrike mismatch")

    zpath = OUT / "_SPEC_DATA_ONE_INDIA_ELITESTRIKE_FIXED.zip"
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "India_EliteStrike.ini", "India_EliteStrike.ini")
        zf.write(extract_path, "EXTRACT_VERIFY/India_EliteStrike.ini")
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
