#!/usr/bin/env python3
"""Patch India_TejasMk2.ini inside _SPEC_DATA_ONE.big (full INI validation).

Fixes beyond hash-only checks:
  - non-ASCII comments (em-dash / multiply)
  - Egypt Rafale donors (Nat_rafalem / Egy_RafaleM/MD) -> pla_j10c / CHI_J10C*
  - Spectra_ECM_Rafale_AHAM -> Thales_Spectra_ECM_Pod
  - unindented Scale = 0.9
  - duplicate Shadow
  - full Object/Draw/Behavior/WeaponSet/End stack validation

Source: SPECTER_SPEC_DATA_ONE_GERMANY_DRONE_FIXED/_SPEC_DATA_ONE.big
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
    """Validate Object/Draw/Behavior/WeaponSet/ConditionState End matching."""
    issues: list[str] = []
    stack: list[tuple[str, int]] = []
    for i, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0]
        if not code.strip():
            continue
        if re.match(r"^\s*End\s*$", code):
            if not stack:
                issues.append(f"line {i}: EXTRA End with empty stack")
            else:
                stack.pop()
            continue
        for rx, kind in OPENERS:
            if rx.match(code):
                stack.append((kind, i))
                break
    if stack:
        issues.append(
            "UNCLOSED blocks: "
            + ", ".join(f"{k}@{ln}" for k, ln in stack)
        )
    return (not issues), issues


def code_only(text: str) -> str:
    return "\n".join(line.split(";", 1)[0] for line in text.splitlines())


def repair_tejas(raw: bytes) -> str:
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(ascii_safe(line) for line in text.split("\n"))

    # Strip old banners / repair headers until Object line.
    lines = text.split("\n")
    while lines and (
        lines[0].strip() == ""
        or (
            lines[0].lstrip().startswith(";")
            and not re.match(r"^\s*Object\s+", lines[0])
        )
    ):
        # Keep going while leading comments/blank; stop at Object
        if re.match(r"^\s*Object\s+", lines[0]):
            break
        lines.pop(0)
        if lines and re.match(r"^\s*Object\s+", lines[0]):
            break
    # If first remaining is still comments before Object, find Object
    obj_idx = next(
        (i for i, l in enumerate(lines) if re.match(r"^\s*Object\s+India_TejasMk2\b", l)),
        None,
    )
    if obj_idx is None:
        raise SystemExit("Object India_TejasMk2 missing in source")
    lines = lines[obj_idx:]

    text = "\n".join(lines)

    # Identity repair: remove Egypt Rafale donors (known init crash pattern).
    text = re.sub(
        r"(?m)^(  SelectPortrait\s*=\s*)\S+\s*$",
        r"\1pla_j10c",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(  ButtonImage\s*=\s*)\S+\s*$",
        r"\1pla_j10c",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(      Model\s*=\s*)Egy_RafaleM\s*$",
        r"\1CHI_J10C",
        text,
    )
    text = re.sub(
        r"(?m)^(      Model\s*=\s*)Egy_RafaleMD\s*$",
        r"\1CHI_J10C_D",
        text,
    )
    # Rubble states should use rubble model when present.
    # After MD->D replacement, set RUBBLE blocks to CHI_J10C_R.
    def rubble_model(block: str) -> str:
        return re.sub(
            r"(?m)^(      Model\s*=\s*)CHI_J10C_D\s*$",
            r"\1CHI_J10C_R",
            block,
        )

    text = re.sub(
        r"(?ms)(^\s*ConditionState\s*=\s*RUBBLE(?:[^\n]*)\n.*?^\s*End)",
        lambda m: rubble_model(m.group(1)),
        text,
    )
    text = re.sub(
        r"(WeaponTemplate\s*=\s*)Spectra_ECM_Rafale_AHAM",
        r"\1Thales_Spectra_ECM_Pod",
        text,
    )

    # Indent Scale under Object (was column-0).
    text = re.sub(r"(?m)^Scale\s*=\s*", "  Scale = ", text)

    # Deduplicate Shadow = SHADOW_VOLUME
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
        "; SPECTER FIX - India_TejasMk2 (full INI validation)\n"
        "; ASCII repair + identity donors: pla_j10c / CHI_J10C / CHI_J10C_D / CHI_J10C_R\n"
        "; Keep: Object India_TejasMk2 / Side=India / India weapons and balance\n"
        "; Weapons: India_Weapon_AstraMk2_TejasMk2 + 2x_ALCM_ScalpEG + Thales radar\n"
        "; Prereq: SCIENCE_India_TechTejasMk2 + India_MIC + SCIENCE_Rank6\n"
        "; Removed: non-ASCII, Nat_rafalem/Egy_Rafale*, Spectra_ECM_Rafale_AHAM, col0 Scale\n"
        "\n"
    )
    text = header + text

    code = code_only(text)
    if not re.search(r"(?m)^Object\s+India_TejasMk2\b", text):
        raise SystemExit("Object India_TejasMk2 missing")
    if not re.search(r"(?m)^  Side\s*=\s*India\s*$", text):
        raise SystemExit("Side=India missing")
    if "India_Weapon_AstraMk2_TejasMk2" not in text:
        raise SystemExit("Astra Mk2 weapon missing")
    if any(ord(c) > 127 for c in text):
        raise SystemExit("non-ascii remain")
    if re.search(r"(?m)^Scale\s*=", text):
        raise SystemExit("unindented Scale remain")
    if re.search(r"(?m)^\s*(?:SelectPortrait|ButtonImage)\s*=\s*Nat_rafalem\b", code):
        raise SystemExit("Nat_rafalem remain in code")
    if re.search(r"(?m)^\s*Model\s*=\s*Egy_Rafale", code):
        raise SystemExit("Egy_Rafale model remain in code")
    if "Spectra_ECM_Rafale_AHAM" in code:
        raise SystemExit("Spectra_ECM_Rafale_AHAM remain in code")
    if "CHI_J10C" not in code or "pla_j10c" not in code:
        raise SystemExit("CHI_J10C/pla_j10c identity missing")
    ok_blocks, block_issues = full_block_check(text)
    if not ok_blocks:
        raise SystemExit("block syntax fail: " + "; ".join(block_issues))
    return text.replace("\n", "\r\n")


def catalog_all(entries):
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
    cats = catalog_all(entries)

    checks: list[tuple[str, bool]] = []

    def chk(name: str, ok: bool) -> None:
        checks.append((name, ok))
        print(("PASS" if ok else "FAIL"), name)

    code = code_only(fixed)
    cs = re.findall(r"(?m)^\s*CommandSet\s*=\s*(\S+)", fixed)
    weps = re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", fixed)
    wtemplates = re.findall(r"(?m)^\s*WeaponTemplate\s*=\s*(\S+)", fixed)
    models = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", fixed))
    prereq_obj = re.findall(r"(?m)^\s*Object\s*=\s*(\S+)", fixed)
    sci = re.findall(r"(?m)^\s*Science\s*=\s*(\S+)", fixed)
    upg = re.findall(
        r"(?m)^\s*(?:UpgradeCameo\d*|TriggeredBy|UpgradeToGrant)\s*=\s*(\S+)",
        fixed,
    )
    arm = re.findall(r"(?m)^\s*Armor\s*=\s*(\S+)", fixed)
    loco = re.findall(r"(?m)^\s*Locomotor\s*=\s*\S+\s+(\S+)", fixed)
    imgs = re.findall(r"(?m)^\s*(?:SelectPortrait|ButtonImage)\s*=\s*(\S+)", fixed)
    ocl = re.findall(
        r"(?m)^\s*(?:OCLOnGroundDeath|OCLFinalBlowUp|GroundCreationList|"
        r"AirCreationList|CreationList)\s*=\s*(\S+)",
        fixed,
    )
    module_tags = re.findall(r"ModuleTag_\S+", fixed)
    draws = re.findall(r"(?m)^\s*Draw\s*=\s*(\S+)\s+(\S+)", fixed)
    shadows = re.findall(r"(?m)^\s*Shadow\s*=\s*(\S+)", fixed)

    ok_blocks, block_issues = full_block_check(fixed)

    chk("Object=India_TejasMk2", bool(re.search(r"(?m)^Object\s+India_TejasMk2\b", fixed)))
    chk("single Object declaration", len(re.findall(r"(?m)^Object\s+\S+", fixed)) == 1)
    chk("Side=India", bool(re.search(r"(?m)^  Side\s*=\s*India\s*$", fixed)))
    chk("Object/Draw/Behavior/End stack PASS", ok_blocks)
    chk("Draw W3DModelDraw present", bool(draws) and draws[0][0] == "W3DModelDraw")
    chk("single Shadow", len(shadows) == 1 and shadows[0] == "SHADOW_VOLUME")
    chk("no duplicate ModuleTag", len(module_tags) == len(set(module_tags)))
    chk("Scale indented", bool(re.search(r"(?m)^  Scale\s*=\s*0\.9\s*$", fixed)))
    chk("no col0 Scale", not re.search(r"(?m)^Scale\s*=", fixed))
    chk("ASCII-only", all(ord(c) < 128 for c in fixed))
    chk("no Nat_rafalem in code", "Nat_rafalem" not in code)
    chk("no Egy_Rafale in code", "Egy_Rafale" not in code)
    chk("no Spectra_ECM_Rafale in code", "Spectra_ECM_Rafale" not in code)
    chk("pla_j10c portrait", "pla_j10c" in code)
    chk("CHI_J10C models", "CHI_J10C" in code and "CHI_J10C_D" in code and "CHI_J10C_R" in code)
    chk("India Astra weapon kept", "India_Weapon_AstraMk2_TejasMk2" in fixed)
    chk("BuildCost=1744", bool(re.search(r"(?m)^  BuildCost\s*=\s*1744\s*$", fixed)))
    chk("BuildTime=13.8", bool(re.search(r"(?m)^  BuildTime\s*=\s*13\.8\b", fixed)))
    chk("Geometry present", "Geometry" in fixed and "GeometryMajorRadius" in fixed)
    chk("Behavior modules present", bool(re.search(r"(?m)^\s*Behavior\s*=", fixed)))

    missing: list[str] = []

    def resolve(kind: str, vals: list[str], allow_none: bool = False) -> bool:
        ok_all = True
        for v in vals:
            if allow_none and v == "None":
                continue
            ok = v in cats[kind] or v.encode() in data_join
            if not ok:
                missing.append(f"{kind}={v}")
                ok_all = False
        return ok_all

    chk("CommandSet resolves", resolve("CommandSet", cs))
    chk("Weapon slots resolve", resolve("Weapon", weps))
    chk("WeaponTemplate resolve", resolve("Weapon", wtemplates))
    chk("Science resolve", resolve("Science", sci))
    chk("Upgrade resolve", resolve("Upgrade", upg))
    chk("Armor resolve", resolve("Armor", [a for a in arm if a != "None"]))
    chk("Prereq Object resolve", resolve("Object", prereq_obj))
    chk("Locomotor resolve", resolve("Locomotor", loco))
    chk("MappedImage resolve", resolve("MappedImage", imgs))
    chk("OCL resolve", resolve("OCL", [o for o in ocl if o != "None"]))

    model_ok = True
    for m in models:
        w3d_hits = [
            n
            for n, _ in art_entries
            if m.lower() in knorm(n) and n.lower().endswith(".w3d")
        ]
        if not w3d_hits:
            missing.append(f"ModelW3D={m}")
            model_ok = False
    chk("Model W3D present in ART", model_ok)
    chk("Missing references = 0", not missing)

    if block_issues:
        print("BLOCK ISSUES:")
        for iss in block_issues:
            print(" ", iss)
    if missing:
        print("MISSING:")
        for m in missing:
            print(" ", m)

    ok_all = all(ok for _, ok in checks)
    if not ok_all:
        print("VALIDATION FAILED; not writing BIG")
        for n, ok in checks:
            if not ok:
                print(" FAIL:", n)
        return 1

    new_entries = []
    for name, blob in entries:
        if knorm(name) == knorm(TEJAS_PATH):
            new_entries.append((name, fixed_bytes))
        else:
            new_entries.append((name, blob))

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    if out_big.exists():
        out_big.unlink()
    write_big(out_big, new_entries)

    # Hard embed proof: extract from disk and re-validate structure.
    rebuilt_entries = parse_big(out_big)
    rebuilt_by = {knorm(n): (n, b) for n, b in rebuilt_entries}
    if knorm(TEJAS_PATH) not in rebuilt_by:
        raise SystemExit("EMBED FAIL: Tejas path missing after write")
    extracted_name, extracted = rebuilt_by[knorm(TEJAS_PATH)]
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
    extract_path = extract_dir / "India_TejasMk2.ini"
    extract_path.write_bytes(extracted)

    tejas_sha = sha256_bytes(fixed_bytes)
    broken_sha = sha256_bytes(broken)
    extracted_sha = sha256_bytes(extracted)
    if extracted != fixed_bytes or extracted_sha != tejas_sha:
        raise SystemExit(
            "EMBED FAIL: inside-BIG != fixed source\n"
            f" fixed={tejas_sha}\n inside={extracted_sha}"
        )
    if extracted_sha == broken_sha:
        raise SystemExit("EMBED FAIL: still broken vendor content")
    extracted_text = extracted.decode("ascii")
    ok_ext, ext_issues = full_block_check(extracted_text)
    if not ok_ext:
        raise SystemExit("EMBED FAIL: extracted block syntax: " + "; ".join(ext_issues))
    ext_code = code_only(extracted_text)
    if "Egy_Rafale" in ext_code or "Nat_rafalem" in ext_code or "Spectra_ECM_Rafale" in ext_code:
        raise SystemExit("EMBED FAIL: bad donors still in extracted code")
    if any(ord(c) > 127 for c in extracted_text):
        raise SystemExit("EMBED FAIL: non-ascii in extracted")

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

    print("EMBED + FULL INI PROOF PASS")
    print(f"  entry_name={extracted_name}")
    print(f"  inside_BIG_sha={extracted_sha}")
    print(f"  extracted_path={extract_path}")

    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(fixed_bytes)
    (OUT / "India_TejasMk2.ini").write_bytes(fixed_bytes)

    big_sha = sha256_file(out_big)
    big_size = out_big.stat().st_size

    report = (
        "SPECTER INDIA TEJAS MK2 FIXED - FULL INI VERIFY REPORT\n"
        "============================================================\n"
        f"VERDICT: PASS\n"
        "Scope: India_TejasMk2.ini patched INSIDE _SPEC_DATA_ONE.big\n"
        "Validation: full Object/Draw/Behavior/End + refs + W3D + identity\n"
        f"\nSource BIG (Germany drone fixed): {sha256_file(SRC)}\n"
        f"Patched BIG SHA256: {big_sha}\n"
        f"Patched BIG SIZE:   {big_size}\n"
        f"Broken TejasMk2 SHA: {broken_sha}\n"
        f"Fixed TejasMk2 SHA:  {tejas_sha}\n"
        f"Fixed TejasMk2 SIZE: {len(fixed_bytes)}\n"
        "\nProblems fixed:\n"
        "  - Non-ASCII comments\n"
        "  - Nat_rafalem / Egy_RafaleM/MD donors -> pla_j10c / CHI_J10C*\n"
        "  - Spectra_ECM_Rafale_AHAM -> Thales_Spectra_ECM_Pod\n"
        "  - Unindented Scale = 0.9\n"
        "  - Shadow uniqueness + ModuleTag uniqueness\n"
        "\nKept India values:\n"
        "  Object=India_TejasMk2 Side=India\n"
        "  Weapons=India_Weapon_AstraMk2_TejasMk2 + 2x_ALCM_ScalpEG\n"
        "  BuildCost=1744 BuildTime=13.8\n"
        "  Prereq=SCIENCE_India_TechTejasMk2 + India_MIC + SCIENCE_Rank6\n"
        f"\nPASS: {sum(1 for _, ok in checks if ok)}  FAIL: 0\n\n"
        + "\n".join(f"PASS: {n}" for n, _ in checks)
        + f"\n\nMissing={missing}\nBlockIssues={block_issues}\n\nFINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER INDIA TEJAS MK2 FIXED (FULL INI VALIDATION)\n"
        "==================================================\n\n"
        "Replace Data\\_SPEC_DATA_ONE.big with the archive in this package.\n"
        "Keep Data\\_SPEC_ART_ONE.big unchanged.\n"
        "India_TejasMk2 is patched INSIDE the BIG (not overlay-only).\n",
        encoding="ascii",
    )
    hashes = (
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"India_TejasMk2.ini SHA256={tejas_sha} SIZE={len(fixed_bytes)}\n"
        f"Broken vendor India_TejasMk2.ini SHA256={broken_sha}\n"
        f"Source Germany-fixed BIG SHA256={sha256_file(SRC)}\n"
    )
    (OUT / "HASHES.txt").write_text(hashes, encoding="ascii")
    embed_report = (
        "EMBED + FULL INI PROOF\n"
        "======================\n"
        f"path: {extracted_name}\n"
        f"norm: Data/INI/Object/specter/indian armed forces/airforce/india_tejasmk2.ini\n"
        f"fixed_source_sha256: {tejas_sha}\n"
        f"inside_BIG_sha256:   {extracted_sha}\n"
        f"broken_vendor_sha256: {broken_sha}\n"
        f"block_syntax: PASS\n"
        f"identity_donors: pla_j10c / CHI_J10C*\n"
        f"still_broken: NO\n"
        f"BIG_sha256: {big_sha}\n"
        f"BIG_size: {big_size}\n"
    )
    (OUT / "EMBED_PROOF.txt").write_text(embed_report, encoding="ascii")

    for sync in SYNC_DIRS:
        if sync.is_dir():
            shutil.copy2(out_big, sync / "_SPEC_DATA_ONE.big")
            print("synced", sync / "_SPEC_DATA_ONE.big")

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    final_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
    for name in (
        "HASHES.txt",
        "VERIFY_REPORT.txt",
        "README_INSTALL.txt",
        "India_TejasMk2.ini",
        "EMBED_PROOF.txt",
    ):
        shutil.copy2(OUT / name, final_dir / name)
    final_zip = final_dir / "_SPEC_DATA_ONE_FINAL.zip"
    if final_zip.exists():
        final_zip.unlink()
    with zipfile.ZipFile(final_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "India_TejasMk2.ini", "India_TejasMk2.ini")
        zf.write(OUT / "VERIFY_REPORT.txt", "VERIFY_REPORT.txt")
        zf.write(OUT / "README_INSTALL.txt", "README_INSTALL.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "EMBED_PROOF.txt", "EMBED_PROOF.txt")
    with zipfile.ZipFile(final_zip, "r") as zf:
        zip_big = zf.read("_SPEC_DATA_ONE.big")
    # prove zip
    zentries = []
    pos = 16
    count = struct.unpack(">I", zip_big[8:12])[0]
    for _ in range(count):
        offset, size = struct.unpack(">II", zip_big[pos : pos + 8])
        pos += 8
        end = zip_big.index(b"\x00", pos)
        name = zip_big[pos:end].decode("latin-1")
        pos = end + 1
        zentries.append((name, zip_big[offset : offset + size]))
    zip_tejas = next(b for n, b in zentries if knorm(n) == knorm(TEJAS_PATH))
    if sha256_bytes(zip_tejas) != tejas_sha:
        raise SystemExit("FINAL.zip embed fail")
    print("FINAL.zip EMBED PROOF PASS")

    zpath = OUT / "_SPEC_DATA_ONE_INDIA_TEJASMK2_FIXED.zip"
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "India_TejasMk2.ini", "India_TejasMk2.ini")
        zf.write(OUT / "VERIFY_REPORT.txt", "VERIFY_REPORT.txt")
        zf.write(OUT / "README_INSTALL.txt", "README_INSTALL.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "EMBED_PROOF.txt", "EMBED_PROOF.txt")
        zf.write(extract_path, "EXTRACT_VERIFY/India_TejasMk2.ini")

    print(report)
    print(embed_report)
    print("ZIP", zpath, sha256_file(zpath))
    print("BIG", out_big, big_sha, big_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
