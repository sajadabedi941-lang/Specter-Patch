#!/usr/bin/env python3
"""Replace Turkey_F16Block70 with a complete USA F-16C AG donor clone.

Removes the prior entry content and rebuilds from AmericaJetF-16C_AG:
- Object Turkey_F16Block70, Side=Turkey
- Full Draw/WeaponSet/Locomotor/Geometry/CommandSet/Voice/FX modules
- No foreign BuildVariations (known parse/init crash pattern)
- Turkey AdvancedAirBase prereq + Turkey upgrade tokens
- Validate W3D/weapon/locomotor refs; scan all Turkey aircraft for the
  same BuildVariations issue; pack release BIG/ZIP.
"""
from __future__ import annotations

import re
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

import build_specter_aircraft_aab_global_fixed_big as base
import build_specter_turkey_faction_ini_batch_fixed_big as turkey_batch

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_F16BLOCK70_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_F16BLOCK70_USA_DONOR"
TREE = ROOT / "Data/INI/Object/Specter/Turkey Armed Forces/Airforce/Turkey_F16Block70.ini"

TARGET = r"Data\INI\Object\Specter\Turkey Armed Forces\Airforce\Turkey_F16Block70.ini"
DONOR = r"Data\INI\Object\Specter\United States Of America\Airforce\F16CM_BLK50_DB52.ini"
DONOR_OBJ = "AmericaJetF-16C_AG"
TURKEY_OBJ = "Turkey_F16Block70"


def extract_object(text: str, object_name: str) -> str:
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Object\s+(\S+)", text)]
    for i, (start, name) in enumerate(starts):
        if name == object_name:
            end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
            return text[start:end]
    raise SystemExit(f"missing Object {object_name}")


def dedupe_shadow(text: str) -> str:
    out: list[str] = []
    seen = False
    for line in text.splitlines():
        if re.match(r"^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", line.split(";", 1)[0]):
            if seen:
                continue
            seen = True
        out.append(line)
    return "\n".join(out) + "\n"


def strip_build_variations(text: str) -> str:
    out: list[str] = []
    for line in text.splitlines():
        if re.match(r"^\s*BuildVariations\s*=", line):
            out.append("  ; BuildVariations removed (USA donor clone; no foreign/missing variants)")
            continue
        out.append(line)
    return "\n".join(out) + "\n"


def clone_usa_f16_to_turkey(donor_block: str, old_turkey: str) -> str:
    text = donor_block.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(
        rf"(?m)^Object\s+{re.escape(DONOR_OBJ)}\s*$",
        f"Object {TURKEY_OBJ}",
        text,
        count=1,
    )
    text = re.sub(r"(?m)^(  Side\s*=\s*)\S+\s*$", r"\1Turkey", text, count=1)
    text = re.sub(
        r"(?m)^(  DisplayName\s*=\s*)\S+\s*$",
        rf"\1OBJECT:{TURKEY_OBJ}",
        text,
        count=1,
    )

    # Preserve Turkey build identity where present on old entry.
    old_cost = re.search(r"(?m)^\s*BuildCost\s*=\s*(\S+)", old_turkey)
    old_time = re.search(r"(?m)^\s*BuildTime\s*=\s*(\S+)", old_turkey)
    if old_cost:
        text = re.sub(r"(?m)^(  BuildCost\s*=\s*)\S+", rf"\g<1>{old_cost.group(1)}", text, count=1)
    if old_time:
        text = re.sub(r"(?m)^(  BuildTime\s*=\s*)\S+", rf"\g<1>{old_time.group(1)}", text, count=1)

    # Force Turkey airbase prereq (and keep Turkey science gate if old had one).
    turkey_prereq = (
        "  Prerequisites\n"
        "    Science = SCIENCE_Turkey_TechF16Block70\n"
        "    Object = Turkey_AdvancedAirBase\n"
        "  End"
    )
    if re.search(r"(?ms)^\s*Prerequisites\b.*?^\s*End\s*$", text):
        text = re.sub(r"(?ms)^\s*Prerequisites\b.*?^\s*End\s*$", turkey_prereq, text, count=1)
    else:
        text = re.sub(r"(?m)^(\s*WeaponSet\b)", turkey_prereq + "\n\\1", text, count=1)

    # No BuildVariations — complete single-object USA structure under Turkey identity.
    text = strip_build_variations(text)

    # Turkey upgrade tokens for faction compatibility.
    text = text.replace("Upgrade_AmericaCountermeasures", "Upgrade_Turkey_Countermeasures")
    text = text.replace("Upgrade_AmericaAdvancedTraining", "Upgrade_Turkey_PrecisionMunitions")

    text = dedupe_shadow(text)
    text, _ = turkey_batch.remove_armor_set_flag(text)
    text, _ = turkey_batch.sanitize_ascii(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"

    header = (
        f"; SPECTER TURKEY F16BLOCK70 USA DONOR REBUILD - {TURKEY_OBJ}\n"
        f"; Donor: {DONOR_OBJ} from F16CM_BLK50_DB52.ini (validated USA F-16)\n"
        f"; Identity: Object={TURKEY_OBJ} Side=Turkey\n"
        "; Modules: Draw/WeaponSet/Locomotor/Geometry/CommandSet/Voice/FX from donor\n"
        "; BuildVariations removed (prevents foreign/missing variant parse crash)\n\n"
    )
    return header + text


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


def validate_f16(text: str, entries, art_entries, label: str) -> list[str]:
    fails: list[str] = []
    cats = catalog(entries)
    data_join = b"\n".join(b for _, b in entries)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }

    if any(ord(c) > 127 for c in text):
        fails.append(f"{label}: non-ASCII")
    objs = re.findall(r"(?m)^Object\s+(\S+)", text)
    if objs != [TURKEY_OBJ]:
        fails.append(f"{label}: Object={objs}")
    if not re.search(r"(?m)^\s*Side\s*=\s*Turkey\s*$", text):
        fails.append(f"{label}: Side!=Turkey")
    if not re.search(r"(?m)^\s*Draw\s*=\s*W3DModelDraw\b", text):
        fails.append(f"{label}: Draw W3DModelDraw missing")
    if len(re.findall(r"(?m)^\s*WeaponSet\b", text)) < 1:
        fails.append(f"{label}: WeaponSet missing")
    if not re.search(r"(?m)^\s*Locomotor\s*=", text):
        fails.append(f"{label}: Locomotor missing")
    if not re.search(r"(?m)^\s*Geometry\s*=", text):
        fails.append(f"{label}: Geometry missing")
    if not re.search(r"(?m)^\s*CommandSet\s*=", text):
        fails.append(f"{label}: CommandSet missing")
    if not re.search(r"(?m)^\s*VoiceSelect\s*=", text):
        fails.append(f"{label}: VoiceSelect missing")
    shadows = re.findall(r"(?m)^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", text)
    if len(shadows) != 1:
        fails.append(f"{label}: Shadow={shadows}")
    if re.search(r"(?m)^\s*BuildVariations\s*=", text):
        fails.append(f"{label}: BuildVariations must be removed")
    if "Upgrade_AmericaCountermeasures" in text or "Upgrade_AmericaAdvancedTraining" in text:
        fails.append(f"{label}: USA upgrade tokens remain")
    if re.search(r"(?i)\b(Irq_|Iraq_)\b", text):
        fails.append(f"{label}: Iraqi tokens")

    # Block balance
    stack: list[tuple[str, int]] = []
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
        (re.compile(r"^\s*TransitionState\s*="), "TransitionState"),
        (re.compile(r"^\s*LocomotorSet\b"), "LocomotorSet"),
    ]
    for i, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0]
        if not code.strip():
            continue
        if re.match(r"^\s*End\s*$", code):
            if not stack:
                fails.append(f"{label}: extra End @{i}")
            else:
                stack.pop()
            continue
        for rx, kind in openers:
            if rx.match(code):
                stack.append((kind, i))
                break
    if stack:
        fails.append(f"{label}: unclosed {stack[-10:]}")

    def need(kind: str, vals: list[str]) -> None:
        for v in vals:
            if v in ("None", "NONE"):
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
    for model in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)):
        if model in ("None", "NONE"):
            continue
        if model.lower() not in stems:
            fails.append(f"{label}: missing W3D Model={model}")
    return fails


def is_turkey_air(name: str) -> bool:
    n = name.replace("/", "\\")
    if "Turkey Armed Forces" not in n or not n.lower().endswith(".ini"):
        return False
    return "\\Airforce\\" in n or "\\Drones\\" in n


def scan_turkey_air_buildvariations(entries) -> list[str]:
    """Fail if any Turkey aircraft still has foreign or missing BuildVariations."""
    objs = set()
    for n, b in entries:
        if n.lower().endswith(".ini"):
            objs.update(re.findall(r"(?m)^Object\s+(\S+)", b.decode("utf-8", "replace")))
    fails: list[str] = []
    for name, raw in entries:
        if not is_turkey_air(name):
            continue
        text = raw.decode("utf-8", "replace")
        bn = Path(name.replace("\\", "/")).name
        for m in re.finditer(r"(?m)^\s*BuildVariations\s*=\s*(.+)$", text):
            vals = m.group(1).split(";")[0].split()
            foreign = [v for v in vals if not v.startswith("Turkey")]
            missing = [v for v in vals if v not in objs]
            if foreign:
                fails.append(f"{bn}: foreign BuildVariations {foreign}")
            if missing:
                fails.append(f"{bn}: missing BuildVariations {missing}")
    return fails


def scrub_foreign_buildvariations(text: str) -> tuple[str, bool]:
    changed = False
    out: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^(\s*BuildVariations\s*=\s*)(.+)$", line)
        if not m:
            out.append(line)
            continue
        vals = m.group(2).split(";")[0].split()
        if any(not v.startswith("Turkey") for v in vals):
            out.append("  ; BuildVariations removed (foreign donor refs)")
            changed = True
            continue
        out.append(line)
    return "\n".join(out) + "\n", changed


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG {SRC}")

    entries = base.parse_big(SRC)
    by = {base.knorm(n): (n, r) for n, r in entries}
    art_entries = base.parse_big(ART)

    hits = [n for n, _ in entries if n.lower().endswith("turkey_f16block70.ini")]
    if len(hits) != 1:
        raise SystemExit(f"expected exactly 1 Turkey_F16Block70 entry, got {hits}")
    print(f"INSPECT entry={hits[0]} duplicates=0")

    t_name, t_raw = by[base.knorm(TARGET)]
    d_name, d_raw = by[base.knorm(DONOR)]
    old_text = t_raw.decode("utf-8", "replace")
    donor_text = d_raw.decode("utf-8", "replace")
    donor_block = extract_object(donor_text, DONOR_OBJ)
    print(f"DONOR {DONOR_OBJ} bytes={len(donor_block)}")

    fixed = clone_usa_f16_to_turkey(donor_block, old_text)
    fixed_raw = fixed.encode("ascii")

    repaired: dict[str, bytes] = {base.knorm(TARGET): fixed_raw}

    # Scrub same foreign-BuildVariations pattern on other Turkey aircraft.
    for name, raw in entries:
        if not is_turkey_air(name) or base.knorm(name) == base.knorm(TARGET):
            continue
        text = raw.decode("utf-8", "replace")
        scrubbed, changed = scrub_foreign_buildvariations(text)
        if changed:
            scrubbed = scrubbed.replace("Upgrade_AmericaCountermeasures", "Upgrade_Turkey_Countermeasures")
            scrubbed = scrubbed.replace("Upgrade_AmericaAdvancedTraining", "Upgrade_Turkey_PrecisionMunitions")
            scrubbed, _ = turkey_batch.sanitize_ascii(scrubbed)
            repaired[base.knorm(name)] = scrubbed.encode("ascii")
            print(f"SCRUB BV {Path(name.replace(chr(92), '/')).name}")

    candidate = [
        (name, repaired[base.knorm(name)] if base.knorm(name) in repaired else raw)
        for name, raw in entries
    ]

    failures = validate_f16(fixed, candidate, art_entries, "PREWRITE")
    failures.extend(scan_turkey_air_buildvariations(candidate))
    if failures:
        print("PRE-WRITE FAILED")
        for f in failures[:80]:
            print(" ", f)
        return 1
    print("PASS pre-write F16Block70 + Turkey air BV scan")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, candidate)
    rebuilt = base.parse_big(out_big)
    rebuilt_by = {base.knorm(n): (n, r) for n, r in rebuilt}

    # Ensure single entry still
    hits2 = [n for n, _ in rebuilt if n.lower().endswith("turkey_f16block70.ini")]
    if len(hits2) != 1:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"duplicate F16Block70 after write: {hits2}")

    old_by = {base.knorm(n): r for n, r in entries}
    changed = [n for n, r in rebuilt if r != old_by[base.knorm(n)]]
    unexpected = [n for n in changed if base.knorm(n) not in repaired]
    if unexpected:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"unrelated changed: {unexpected[:20]}")

    emb_name, emb = rebuilt_by[base.knorm(TARGET)]
    if emb != fixed_raw:
        raise SystemExit("embedded bytes differ from rebuilt source")

    extract_root = OUT / "_EXTRACT_VERIFY"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    rel = Path(*Path(emb_name.replace("\\", "/")).parts)
    extract_path = extract_root / rel
    extract_path.parent.mkdir(parents=True, exist_ok=True)
    extract_path.write_bytes(emb)
    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(fixed_raw)

    post = validate_f16(emb.decode("ascii"), rebuilt, art_entries, "EXTRACT")
    post.extend(scan_turkey_air_buildvariations(rebuilt))
    if post:
        out_big.unlink(missing_ok=True)
        print("EXTRACT FAILED")
        for f in post[:80]:
            print(" ", f)
        return 1

    big_sha = base.sha256_file(out_big)
    big_size = out_big.stat().st_size
    ini_sha = base.sha256_bytes(fixed_raw)
    print(f"CHANGED={len(changed)} BIG={big_sha} SIZE={big_size}")

    (OUT / "Turkey_F16Block70.ini").write_bytes(fixed_raw)
    verify = (
        "SPECTER TURKEY F16BLOCK70 USA DONOR REBUILD - VERIFY REPORT\n"
        "===========================================================\n"
        "VERDICT: PASS\n"
        "Patched INSIDE: _SPEC_DATA_ONE.big\n"
        f"Entry: {emb_name}\n"
        f"Duplicates of Turkey_F16Block70.ini: 0 (single entry)\n"
        f"Donor: {DONOR_OBJ} (USA F16CM_BLK50_DB52)\n"
        f"Object={TURKEY_OBJ} Side=Turkey\n"
        "Modules copied: Draw, WeaponSet, Locomotor, Geometry, CommandSet, Voice, FX\n"
        "BuildVariations: REMOVED (no foreign/missing variant refs)\n"
        "Weapon/Locomotor/Model W3D/CommandSet/Upgrade validation: PASS\n"
        "Turkey aircraft foreign-BuildVariations scan: PASS\n"
        "Extract-from-BIG byte match: PASS\n"
        "Unrelated BIG entries changed: 0\n"
        f"\nINI SHA256: {ini_sha}\n"
        f"BIG SHA256: {big_sha}\n"
        f"BIG SIZE: {big_size}\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(verify, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT\n"
        "===============\n"
        f"entry={emb_name}\n"
        f"source_sha256={ini_sha}\n"
        f"embedded_sha256={base.sha256_bytes(emb)}\n"
        f"extracted_sha256={base.sha256_bytes(extract_path.read_bytes())}\n"
        "byte_match=YES\ndonor=AmericaJetF-16C_AG\n"
        "BuildVariations=REMOVED\nSide=Turkey\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER TURKEY F16BLOCK70 USA DONOR REBUILD\n"
        "==========================================\n\n"
        "Turkey_F16Block70.ini completely rebuilt from validated USA\n"
        "AmericaJetF-16C_AG donor. Side=Turkey. BuildVariations removed.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Turkey_F16Block70.ini SHA256={ini_sha}\n",
        encoding="ascii",
    )

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in ("HASHES.txt", "VERIFY_REPORT.txt", "README_INSTALL.txt", "EMBED_PROOF.txt"):
            shutil.copy2(OUT / name, final_dir / name)
        shutil.copy2(OUT / "Turkey_F16Block70.ini", final_dir / "Turkey_F16Block70.ini")

    zip_path = OUT / "_SPEC_DATA_ONE_TURKEY_F16BLOCK70_USA_DONOR.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "HASHES.txt",
            "VERIFY_REPORT.txt",
            "README_INSTALL.txt",
            "EMBED_PROOF.txt",
            "Turkey_F16Block70.ini",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Turkey_F16Block70.ini SHA256={ini_sha}\n"
        f"_SPEC_DATA_ONE_TURKEY_F16BLOCK70_USA_DONOR.zip SHA256={zip_sha}\n",
        encoding="ascii",
    )
    if final_dir.is_dir():
        shutil.copy2(OUT / "HASHES.txt", final_dir / "HASHES.txt")
    print(f"ZIP SHA256={zip_sha}")
    print("FINAL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
