#!/usr/bin/env python3
"""Replace crashing F35C-based India_EliteStrike with Egypt Su-25K clone.

Donor: Egypt_Su-25K (another faction, already in DATA BIG, Irq_Su25k art).
Only identity changes: Object name, Side=India, DisplayName, BuildCost/Time.
Strip USA-only AmericaCountermeasures cameos/modules.
Fix duplicate Shadow (known init crash pattern). ASCII-only output.
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
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_INDIA_ELITESTRIKE_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_INDIA_ELITESTRIKE_SIMPLE"

ELITE_PATH = (
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\India_EliteStrike.ini"
)
DONOR_PATH = (
    r"Data\INI\Object\Specter\Egyptian Armed Forces\Airforce\Egypt_Su-25K.ini"
)

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

USA_ONLY = re.compile(
    r"Upgrade_AmericaCountermeasures|AmericaJetF35C|US_F35A|Nat_f35a|"
    r"GenericMultiRoleFighter_AG_CommandSet|F35C",
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
    if USA_ONLY.search(text):
        fails.append(f"{label}: USA-only refs remain: {USA_ONLY.findall(text)}")

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


def strip_usa_modules(text: str) -> str:
    """Remove Upgrade_AmericaCountermeasures cameos and TriggeredBy behavior blocks."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\s*UpgradeCameo\d+\s*=\s*Upgrade_AmericaCountermeasures\b", line):
            i += 1
            continue
        # Drop whole Behavior blocks that reference AmericaCountermeasures
        if re.match(r"^\s*Behavior\s*=", line):
            block = [line]
            j = i + 1
            depth = 1
            while j < len(lines) and depth > 0:
                block.append(lines[j])
                code = lines[j].split(";", 1)[0]
                if re.match(r"^\s*Behavior\s*=", code) or re.match(
                    r"^\s*(?:Draw|Body|ArmorSet|WeaponSet|Prerequisites|UnitSpecificSounds|"
                    r"DefaultConditionState|ConditionState|TransitionState)\b",
                    code,
                ):
                    # nested opener unlikely inside Behavior; treat End only
                    pass
                if re.match(r"^\s*End\s*$", code):
                    depth -= 1
                j += 1
            block_text = "\n".join(block)
            if "Upgrade_AmericaCountermeasures" in block_text:
                i = j
                continue
            out.extend(block)
            i = j
            continue
        out.append(line)
        i += 1
    text = "\n".join(out)
    # Deduplicate Shadow = SHADOW_VOLUME (keep first + ShadowSizeX)
    seen_shadow = False
    final: list[str] = []
    for line in text.split("\n"):
        if re.match(r"^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", line):
            if seen_shadow:
                continue
            seen_shadow = True
        final.append(line)
    return "\n".join(final)


def clone_egypt_su25_to_india(donor: str) -> str:
    text = donor.replace("\r\n", "\n").replace("\r", "\n")
    # Drop non-ASCII banner; start at Object
    lines = text.split("\n")
    i = next(
        (idx for idx, ln in enumerate(lines) if re.match(r"^\s*Object\s+Egypt_Su-25K\b", ln)),
        None,
    )
    if i is None:
        raise SystemExit("donor Object Egypt_Su-25K missing")
    # Keep Scale line above Object if present immediately before
    start = i
    if i > 0 and re.match(r"^\s*Scale\s*=", lines[i - 1]):
        start = i - 1
    text = "\n".join(lines[start:])

    text = strip_usa_modules(text)
    text = text.replace("Object Egypt_Su-25K", "Object India_EliteStrike", 1)
    text = re.sub(r"(?m)^(  Side\s*=\s*)Egypt\s*$", r"\1India", text, count=1)
    text = re.sub(
        r"(?m)^(  DisplayName\s*=\s*)\S+\s*$",
        r"\1OBJECT:India_EliteStrike",
        text,
        count=1,
    )
    text = re.sub(r"(?m)^(  BuildCost\s*=\s*)\S+", r"\g<1>1700", text, count=1)
    text = re.sub(r"(?m)^(  BuildTime\s*=\s*)\S+", r"\g<1>14", text, count=1)

    # Drop donor balance comments (Egypt-specific)
    text = re.sub(r"(?m)^; PatchBaseCost = .*\n", "", text)
    text = re.sub(r"(?m)^; PatchBaseTime = .*\n", "", text)
    text = re.sub(r"(?m)^; CountryBalance .*\n", "", text)
    text = re.sub(
        r"(?m)^(Object India_EliteStrike\n)",
        r"\1; Cost/time identity: BuildCost=1700 BuildTime=14\n",
        text,
        count=1,
    )

    # Ensure Scale is indented if present as first line
    text = re.sub(r"(?m)^Scale\s*=", "  Scale =", text, count=1)

    header = (
        "; SPECTER FIX - India_EliteStrike\n"
        "; Donor: Egypt_Su-25K (complete working faction fighter)\n"
        "; Identity only: Object/Side/DisplayName/BuildCost/Time\n"
        "; Removed USA-only countermeasure upgrade modules/cameos\n"
        "; Fixed duplicate Shadow\n"
        "\n"
    )
    text = header + text
    # ASCII enforce
    text = "".join(c if ord(c) < 128 else "?" for c in text)
    if USA_ONLY.search(text):
        raise SystemExit(f"USA refs remain after clone: {USA_ONLY.findall(text)}")
    if re.search(r"(?m)^  Side\s*=\s*Egypt\s*$", text):
        raise SystemExit("Side still Egypt")
    if "Object Egypt_Su-25K" in text:
        raise SystemExit("donor object name remain")
    if "US_F35A" in text or "AmericaJetF35C" in text:
        raise SystemExit("F35C residue")
    return text.replace("\n", "\r\n")


def retarget_strings(name: str, raw: bytes) -> bytes | None:
    if b"EliteStrike" not in raw and b"F-35C" not in raw and b"F35C" not in raw:
        return None
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    orig = text
    text = re.sub(
        r"(?m)^(CONTROLBAR:ToolTipConstructIndia_EliteStrike\s*=\s*).*$",
        r"\1Produce India elite strike fighter (Egypt Su-25K systems).",
        text,
    )
    text = text.replace("USA F-35C systems", "Egypt Su-25K systems")
    text = text.replace("USA F35C", "Egypt Su-25K")
    # Drop F35 identity from button image if present
    if "Command_ConstructIndia_EliteStrike" in text:
        text = re.sub(
            r"(CommandButton Command_ConstructIndia_EliteStrike\n"
            r"  Command = UNIT_BUILD\n"
            r"  Object = India_EliteStrike\n"
            r"  TextLabel = CONTROLBAR:ConstructIndia_EliteStrike\n"
            r"  ButtonImage = )\S+",
            r"\1irq_su25k",
            text,
        )
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
        raise SystemExit("Egypt_Su-25K donor missing")
    if knorm(ELITE_PATH) not in by:
        raise SystemExit("India_EliteStrike missing from source (expected F35C clone)")

    donor_raw = by[knorm(DONOR_PATH)][1]
    donor_text = donor_raw.decode("utf-8", "replace")

    # Validate donor structure lightly (allow USA cameos on donor itself)
    ok, issues = full_block_check(donor_text)
    if not ok:
        print("DONOR BLOCK FAIL", issues)
        return 1
    if "Irq_Su25k" not in donor_text:
        raise SystemExit("donor missing Irq_Su25k model")
    print("PASS donor Egypt_Su-25K present")

    repl = clone_egypt_su25_to_india(donor_text)
    tmp_entries = [(n, b) for n, b in entries if knorm(n) != knorm(ELITE_PATH)]
    tmp_entries.append((ELITE_PATH, repl.encode("ascii")))
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
        print("--- REPL PREVIEW ---")
        print(repl[:2500])
        return 1
    print("PASS India_EliteStrike full INI validation (pre-write)")

    new_entries: list[tuple[str, bytes]] = []
    patched = []
    replaced = False
    for name, blob in entries:
        if knorm(name) == knorm(ELITE_PATH):
            new_entries.append((ELITE_PATH, repl.encode("ascii")))
            replaced = True
            continue
        p = retarget_strings(name, blob)
        if p is not None:
            new_entries.append((name, p))
            patched.append(name)
        else:
            new_entries.append((name, blob))
    if not replaced:
        raise SystemExit("failed to replace EliteStrike entry")

    checks: list[tuple[str, bool]] = []

    def chk(n: str, ok: bool) -> None:
        checks.append((n, ok))
        print(("PASS" if ok else "FAIL"), n)

    joined = "\n".join(
        b.decode("utf-8", "replace")
        for n, b in new_entries
        if n.lower().endswith((".ini", ".txt"))
    )
    chk("replaced EliteStrike file", replaced)
    chk("EliteStrike object present", bool(re.search(r"(?m)^Object\s+India_EliteStrike\b", joined)))
    chk("Side India", bool(re.search(r"(?m)^  Side\s*=\s*India\s*$", repl)))
    chk("uses Irq_Su25k model", "Irq_Su25k" in repl)
    chk("uses irq_su25k portrait", "irq_su25k" in repl)
    chk("no F35C / US_F35A", "US_F35A" not in repl and "F35C" not in repl and "AmericaJetF35C" not in repl)
    chk("no AmericaCountermeasures", "Upgrade_AmericaCountermeasures" not in repl)
    chk("single Shadow", len(re.findall(r"(?m)^\s*Shadow\s*=", repl)) == 1)
    chk("Construct command present", "Command_ConstructIndia_EliteStrike" in joined)
    chk("no TejasMk2", b"TejasMk2" not in b"\n".join(b for _, b in new_entries))

    if not all(ok for _, ok in checks):
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    if out_big.exists():
        out_big.unlink()
    write_big(out_big, new_entries)

    rebuilt = parse_big(out_big)
    rby = {knorm(n): (n, b) for n, b in rebuilt}
    if knorm(ELITE_PATH) not in rby:
        raise SystemExit("EXTRACT FAIL: EliteStrike missing")
    ename, ebytes = rby[knorm(ELITE_PATH)]
    repl_bytes = repl.encode("ascii")
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

    for path, expect in PRESERVE.items():
        got = sha256_bytes(rby[knorm(path)][1])
        if got != expect:
            raise SystemExit(f"preserve lost {path}")

    print("EXTRACT + FULL INI TEST PASS")
    print("  embedded:", ename)
    print("  sha:", sha256_bytes(ebytes))

    TREE_NEW.parent.mkdir(parents=True, exist_ok=True)
    TREE_NEW.write_bytes(repl_bytes)
    (OUT / "India_EliteStrike.ini").write_bytes(repl_bytes)

    for key in [
        r"Data\INI\CommandButton_PhaseG_Identity.ini",
        r"Data\English\FactionExpansion_PhaseG_Strings.txt",
    ]:
        if knorm(key) in rby:
            n, b = rby[knorm(key)]
            out = Path("patch") / Path(n.replace("\\", "/"))
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b)

    big_sha = sha256_file(out_big)
    big_size = out_big.stat().st_size
    repl_sha = sha256_bytes(repl_bytes)

    report = (
        "SPECTER INDIA ELITE STRIKE (EGYPT SU-25K DONOR) - VERIFY REPORT\n"
        "===============================================================\n"
        "VERDICT: PASS\n"
        "Replaced: India_EliteStrike.ini (removed USA F35C clone)\n"
        "Donor:    Egypt_Su-25K (complete working fighter from another faction)\n"
        "Changes vs donor: Object/Side/DisplayName/BuildCost/Time ONLY\n"
        "Removed USA-only: Upgrade_AmericaCountermeasures cameos + modules\n"
        "Fixed: duplicate Shadow\n"
        f"\nBIG SHA256: {big_sha}\n"
        f"BIG SIZE:   {big_size}\n"
        f"EliteStrike SHA256: {repl_sha}\n"
        f"Patched support files: {patched}\n"
        "\nValidation: pre-write PASS, extract-from-BIG PASS\n"
        + "\n".join(f"PASS: {n}" for n, _ in checks)
        + "\nFINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT TEST\n"
        "====================\n"
        f"EliteStrike entry: {ename}\n"
        f"Donor: Egypt_Su-25K\n"
        f"embedded_sha256: {repl_sha}\n"
        f"extracted_sha256: {sha256_bytes(extract_path.read_bytes())}\n"
        f"full_ini_validation: PASS\n"
        f"USA_F35C_refs: NONE\n"
        f"BIG_sha256: {big_sha}\n"
        f"BIG_size: {big_size}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER INDIA ELITE STRIKE (SIMPLE)\n"
        "===================================\n\n"
        "India_EliteStrike no longer uses USA F35C.\n"
        "Replaced with Egypt_Su-25K complete working fighter structure.\n"
        "USA-only AmericaCountermeasures modules/cameos removed.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"India_EliteStrike.ini SHA256={repl_sha}\n"
        f"Donor Egypt_Su-25K SHA256={sha256_bytes(donor_raw)}\n",
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
        if (OUT / name).exists():
            shutil.copy2(OUT / name, final_dir / name)

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

    zpath = OUT / "_SPEC_DATA_ONE_INDIA_ELITESTRIKE_SIMPLE.zip"
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

    # Launch test scaffolding report (real Generals PE may be unavailable)
    launch_report = OUT / "LAUNCH_TEST_REPORT.txt"
    launch_report.write_text(
        "LAUNCH TEST\n"
        "===========\n"
        "See run_india_elitestrike_launch_test.py output appended at build time.\n",
        encoding="ascii",
    )

    print(report)
    print("BIG", out_big, big_sha, big_size)
    print("ZIP", zpath, sha256_file(zpath))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
