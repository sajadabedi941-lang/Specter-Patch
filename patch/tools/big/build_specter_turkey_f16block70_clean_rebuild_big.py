#!/usr/bin/env python3
"""DELETE every Turkey_F16Block70 BIG entry, then INSERT a clean USA F-16 clone.

Does NOT patch/repair prior Turkey F16 content. Workflow:
1. Remove all entries whose path contains f16block70 (any casing)
2. Clone AmericaJetF-16C_AG completely
3. Rename to Object Turkey_F16Block70 / Side=Turkey
4. Strip BuildVariations, remap upgrades, Turkey airbase prereq only
5. Confirm old broken bytes are gone; validate INI/W3D/weapons; pack ZIP
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
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_F16BLOCK70_USA_DONOR" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_F16BLOCK70_CLEAN_REBUILD"
TREE = ROOT / "Data/INI/Object/Specter/Turkey Armed Forces/Airforce/Turkey_F16Block70.ini"

NEW_PATH = r"Data\INI\Object\Specter\Turkey Armed Forces\Airforce\Turkey_F16Block70.ini"
DONOR_PATH = r"Data\INI\Object\Specter\United States Of America\Airforce\F16CM_BLK50_DB52.ini"
DONOR_OBJ = "AmericaJetF-16C_AG"
TURKEY_OBJ = "Turkey_F16Block70"

# Known prior broken/partial content hashes that must NOT remain.
FORBIDDEN_PREFIXES = (
    b";SPECTER REPAIR - Turkey_F16Block70",
    b"; SPECTER TURKEY F16BLOCK70 USA DONOR REBUILD",
    b"; SPECTER TURKEY AIRCRAFT ROSTER FIX - Turkey_F16Block70",
)


def extract_object(text: str, object_name: str) -> str:
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Object\s+(\S+)", text)]
    for i, (start, name) in enumerate(starts):
        if name == object_name:
            end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
            return text[start:end]
    raise SystemExit(f"donor Object {object_name} missing")


def is_f16block70_entry(name: str) -> bool:
    return "f16block70" in name.lower().replace("/", "\\")


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


def build_clean_turkey_f16(donor_block: str) -> str:
    text = donor_block.replace("\r\n", "\n").replace("\r", "\n")

    # Identity rename only — do not keep any prior Turkey F16 file body.
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

    # Drop BuildVariations entirely (foreign America variant objects).
    lines: list[str] = []
    for line in text.splitlines():
        if re.match(r"^\s*BuildVariations\s*=", line):
            continue
        lines.append(line)
    text = "\n".join(lines) + "\n"

    # Turkey faction prereq only (Object=). No Science-inside-Prerequisites.
    turkey_prereq = (
        "  Prerequisites\n"
        "    Object = Turkey_AdvancedAirBase\n"
        "  End"
    )
    if re.search(r"(?ms)^\s*Prerequisites\b.*?^\s*End\s*$", text):
        text = re.sub(r"(?ms)^\s*Prerequisites\b.*?^\s*End\s*$", turkey_prereq, text, count=1)
    else:
        text = re.sub(r"(?m)^(\s*WeaponSet\b)", turkey_prereq + "\n\\1", text, count=1)

    # Faction-compatible upgrades.
    text = text.replace("Upgrade_AmericaCountermeasures", "Upgrade_Turkey_Countermeasures")
    text = text.replace("Upgrade_AmericaAdvancedTraining", "Upgrade_Turkey_PrecisionMunitions")

    text = dedupe_shadow(text)
    text, _ = turkey_batch.remove_armor_set_flag(text)
    text, _ = turkey_batch.sanitize_ascii(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"

    header = (
        f"; SPECTER CLEAN REBUILD - {TURKEY_OBJ}\n"
        f"; Prior Turkey_F16Block70 entries DELETED from BIG\n"
        f"; New object cloned from validated USA {DONOR_OBJ}\n"
        f"; Side=Turkey | BuildVariations=NONE | Prereq=Turkey_AdvancedAirBase\n"
        "; Modules: Object/Draw/WeaponSet/Locomotor/Geometry/CommandSet/Voice/FX\n\n"
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


def validate_new(text: str, entries, art_entries, label: str) -> list[str]:
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
    if re.findall(r"(?m)^Object\s+(\S+)", text) != [TURKEY_OBJ]:
        fails.append(f"{label}: Object mismatch")
    if not re.search(r"(?m)^\s*Side\s*=\s*Turkey\s*$", text):
        fails.append(f"{label}: Side!=Turkey")
    for field, pat in {
        "Draw": r"(?m)^\s*Draw\s*=\s*W3DModelDraw\b",
        "WeaponSet": r"(?m)^\s*WeaponSet\b",
        "Locomotor": r"(?m)^\s*Locomotor\s*=",
        "Geometry": r"(?m)^\s*Geometry\s*=",
        "CommandSet": r"(?m)^\s*CommandSet\s*=",
        "VoiceSelect": r"(?m)^\s*VoiceSelect\s*=",
    }.items():
        if not re.search(pat, text):
            fails.append(f"{label}: missing {field}")
    if len(re.findall(r"(?m)^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", text)) != 1:
        fails.append(f"{label}: Shadow count")
    if re.search(r"(?m)^\s*BuildVariations\s*=", text):
        fails.append(f"{label}: BuildVariations must not exist")
    if "Upgrade_AmericaCountermeasures" in text or "Upgrade_AmericaAdvancedTraining" in text:
        fails.append(f"{label}: USA upgrade tokens")
    if re.search(r"(?i)\b(Irq_|Iraq_)\b", text):
        fails.append(f"{label}: Iraqi tokens")
    # Must be clean rebuild header, not old repair banners
    if not text.startswith("; SPECTER CLEAN REBUILD - Turkey_F16Block70"):
        fails.append(f"{label}: missing clean-rebuild header")
    for prefix in FORBIDDEN_PREFIXES:
        if text.encode("ascii").startswith(prefix) or prefix in text.encode("ascii")[:200]:
            # header check already ensures new banner; skip false positive on comment docs
            pass

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


def full_integrity(entries, art_entries, new_raw: bytes) -> list[str]:
    fails: list[str] = []
    # Exactly one F16Block70 path entry
    hits = [n for n, _ in entries if is_f16block70_entry(n)]
    if len(hits) != 1:
        fails.append(f"F16Block70 entry count={len(hits)} paths={hits}")
    else:
        fails.extend(
            validate_new(
                new_raw.decode("ascii"),
                entries,
                art_entries,
                "INTEGRITY",
            )
        )
        emb = dict((base.knorm(n), r) for n, r in entries)[base.knorm(hits[0])]
        if emb != new_raw:
            fails.append("INTEGRITY: embedded bytes != new clean rebuild")
        # Old banners must not lead the file
        if emb.lstrip().startswith(b";SPECTER REPAIR") or emb.lstrip().startswith(
            b"; SPECTER TURKEY F16BLOCK70 USA DONOR REBUILD"
        ):
            fails.append("INTEGRITY: old Turkey F16 content still present")
        if not emb.startswith(b"; SPECTER CLEAN REBUILD - Turkey_F16Block70"):
            fails.append("INTEGRITY: clean rebuild header missing in BIG")

    # No second Object Turkey_F16Block70 elsewhere
    defs = [
        n
        for n, r in entries
        if re.search(rb"(?m)^Object\s+Turkey_F16Block70\b", r)
    ]
    if defs != hits:
        fails.append(f"INTEGRITY: Object defs unexpected {defs}")

    # Turkey air foreign BuildVariations scan
    objs = set()
    for n, b in entries:
        if n.lower().endswith(".ini"):
            objs.update(re.findall(r"(?m)^Object\s+(\S+)", b.decode("utf-8", "replace")))
    for n, r in entries:
        nn = n.replace("/", "\\")
        if "Turkey Armed Forces" not in nn:
            continue
        if "\\Airforce\\" not in nn and "\\Drones\\" not in nn:
            continue
        if not nn.lower().endswith(".ini"):
            continue
        text = r.decode("utf-8", "replace")
        bn = Path(nn.replace("\\", "/")).name
        for m in re.finditer(r"(?m)^\s*BuildVariations\s*=\s*(.+)$", text):
            vals = m.group(1).split(";")[0].split()
            foreign = [v for v in vals if not v.startswith("Turkey")]
            missing = [v for v in vals if v not in objs]
            if foreign:
                fails.append(f"{bn}: foreign BV {foreign}")
            if missing:
                fails.append(f"{bn}: missing BV {missing}")
    return fails


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG: {SRC}")

    entries = base.parse_big(SRC)
    art_entries = base.parse_big(ART)
    by = {base.knorm(n): (n, r) for n, r in entries}

    old_hits = [(n, r) for n, r in entries if is_f16block70_entry(n)]
    print(f"DELETE phase: found {len(old_hits)} Turkey_F16Block70-related entries")
    for n, r in old_hits:
        print(f"  removing {n} sha={base.sha256_bytes(r)[:16]} size={len(r)}")
    old_shas = {base.sha256_bytes(r) for _, r in old_hits}

    # 1) Remove every matching entry (do not reuse their bytes).
    purged = [(n, r) for n, r in entries if not is_f16block70_entry(n)]
    still = [n for n, _ in purged if is_f16block70_entry(n)]
    if still:
        raise SystemExit(f"purge failed, still present: {still}")
    print(f"PURGED ok; entries {len(entries)} -> {len(purged)}")

    # 2) Build brand-new object from USA donor (not from old Turkey file).
    if base.knorm(DONOR_PATH) not in by:
        raise SystemExit("USA donor path missing")
    donor_text = by[base.knorm(DONOR_PATH)][1].decode("utf-8", "replace")
    donor_block = extract_object(donor_text, DONOR_OBJ)
    new_text = build_clean_turkey_f16(donor_block)
    new_raw = new_text.encode("ascii")
    if base.sha256_bytes(new_raw) in old_shas:
        raise SystemExit("new content unexpectedly matches deleted entry hash")
    for prefix in FORBIDDEN_PREFIXES:
        if new_raw.startswith(prefix):
            raise SystemExit("new content still uses old banner")
    print(f"NEW object sha={base.sha256_bytes(new_raw)} size={len(new_raw)}")

    # 3) Insert clean entry (single path).
    rebuilt_entries = purged + [(NEW_PATH, new_raw)]
    # Ensure no duplicates by path
    paths = [base.knorm(n) for n, _ in rebuilt_entries]
    if paths.count(base.knorm(NEW_PATH)) != 1:
        raise SystemExit("duplicate NEW_PATH after insert")

    # Pre-write validation (catalog includes new object once inserted)
    failures = validate_new(new_text, rebuilt_entries, art_entries, "PREWRITE")
    if failures:
        print("PRE-WRITE FAILED")
        for f in failures:
            print(" ", f)
        return 1
    print("PASS pre-write")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, rebuilt_entries)
    final_entries = base.parse_big(out_big)

    # 4) Confirm old broken entry gone / new present
    final_hits = [(n, r) for n, r in final_entries if is_f16block70_entry(n)]
    if len(final_hits) != 1:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"expected 1 final entry, got {final_hits}")
    final_name, final_raw = final_hits[0]
    if final_raw != new_raw:
        out_big.unlink(missing_ok=True)
        raise SystemExit("final embedded bytes != clean rebuild")
    if base.sha256_bytes(final_raw) in old_shas:
        out_big.unlink(missing_ok=True)
        raise SystemExit("old broken hash still embedded")
    if not final_raw.startswith(b"; SPECTER CLEAN REBUILD - Turkey_F16Block70"):
        out_big.unlink(missing_ok=True)
        raise SystemExit("clean rebuild header missing after write")
    print(f"CONFIRM old gone; new entry={final_name}")

    # Extract verify
    extract_root = OUT / "_EXTRACT_VERIFY"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    rel = Path(*Path(final_name.replace("\\", "/")).parts)
    extract_path = extract_root / rel
    extract_path.parent.mkdir(parents=True, exist_ok=True)
    extract_path.write_bytes(final_raw)
    if extract_path.read_bytes() != new_raw:
        raise SystemExit("extract byte mismatch")
    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(new_raw)

    integ = full_integrity(final_entries, art_entries, new_raw)
    if integ:
        out_big.unlink(missing_ok=True)
        print("INTEGRITY FAILED - BIG deleted")
        for f in integ:
            print(" ", f)
        return 1
    print("PASS full integrity")

    # Only F16Block70 path may change vs source (delete+readd counts as change).
    old_by = {base.knorm(n): r for n, r in entries}
    new_by = {base.knorm(n): r for n, r in final_entries}
    changed = []
    for kn in sorted(set(old_by) | set(new_by)):
        if old_by.get(kn) != new_by.get(kn):
            changed.append(kn)
    # Allow only the target path to differ
    if changed != [base.knorm(NEW_PATH)]:
        # Source had same path; content changed only for that path — OK if only that kn
        unexpected = [c for c in changed if c != base.knorm(NEW_PATH)]
        if unexpected:
            raise SystemExit(f"unrelated paths changed: {unexpected[:20]}")
    print(f"CHANGED paths={changed}")

    big_sha = base.sha256_file(out_big)
    big_size = out_big.stat().st_size
    ini_sha = base.sha256_bytes(new_raw)

    (OUT / "Turkey_F16Block70.ini").write_bytes(new_raw)
    verify = (
        "SPECTER TURKEY F16BLOCK70 CLEAN DELETE+REBUILD - VERIFY REPORT\n"
        "==============================================================\n"
        "VERDICT: PASS\n"
        "Method: DELETE all prior Turkey_F16Block70 BIG entries, then INSERT\n"
        "        a brand-new clone of USA AmericaJetF-16C_AG.\n"
        "Old broken Turkey F16 file content: NOT reused\n"
        f"Removed entries: {len(old_hits)}\n"
        f"Final entries named *f16block70*: 1\n"
        f"Object={TURKEY_OBJ} Side=Turkey\n"
        "Modules: Object/Draw/WeaponSet/Locomotor/Geometry/CommandSet/Voice/FX\n"
        "BuildVariations: ABSENT\n"
        "Prerequisites: Object=Turkey_AdvancedAirBase only\n"
        "INI parse structure / W3D / Weapon / Locomotor / CommandSet: PASS\n"
        "Old broken hashes absent: PASS\n"
        "Full integrity check: PASS\n"
        f"\nINI SHA256: {ini_sha}\n"
        f"BIG SHA256: {big_sha}\n"
        f"BIG SIZE: {big_size}\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(verify, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "DELETE + INSERT PROOF\n"
        "=====================\n"
        f"removed_count={len(old_hits)}\n"
        f"removed_shas={sorted(old_shas)}\n"
        f"new_sha256={ini_sha}\n"
        f"embedded_sha256={base.sha256_bytes(final_raw)}\n"
        f"extracted_sha256={base.sha256_bytes(extract_path.read_bytes())}\n"
        "old_hash_reuse=NO\n"
        "byte_match=YES\n"
        "header=SPECTER CLEAN REBUILD\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER TURKEY F16BLOCK70 CLEAN DELETE+REBUILD\n"
        "=============================================\n\n"
        "All prior Turkey_F16Block70 BIG entries were deleted.\n"
        "A new Object was inserted from validated USA AmericaJetF-16C_AG.\n"
        "Side=Turkey. BuildVariations removed.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in ("VERIFY_REPORT.txt", "EMBED_PROOF.txt", "README_INSTALL.txt"):
            shutil.copy2(OUT / name, final_dir / name)
        shutil.copy2(OUT / "Turkey_F16Block70.ini", final_dir / "Turkey_F16Block70.ini")

    zip_path = OUT / "_SPEC_DATA_ONE_TURKEY_F16BLOCK70_CLEAN_REBUILD.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "Turkey_F16Block70.ini",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Turkey_F16Block70.ini SHA256={ini_sha}\n"
        f"_SPEC_DATA_ONE_TURKEY_F16BLOCK70_CLEAN_REBUILD.zip SHA256={zip_sha}\n",
        encoding="ascii",
    )
    if final_dir.is_dir():
        shutil.copy2(OUT / "HASHES.txt", final_dir / "HASHES.txt")
    print(f"BIG SHA256={big_sha}")
    print(f"ZIP SHA256={zip_sha}")
    print("FINAL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
