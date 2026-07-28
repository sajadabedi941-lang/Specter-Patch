#!/usr/bin/env python3
"""DELETE broken Turkey_Tu-22M3 entries and INSERT clean Russia Tu-22M3M clones.

Does not repair old Turkey Tu-22 content (Su-34 roster clones). Workflow:
1. Remove every BIG entry path containing turkey_tu-22m3
2. Clone validated RussiaJetTu22M3M
3. Create Turkey_Tu-22M3 (+ AI twin) with Side=Turkey
4. Strip BuildVariations, remap America upgrades, Turkey airbase prereq
5. Scan remaining Turkey aircraft for foreign BuildVariations
6. Validate INI/W3D/weapons; pack release ZIP
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
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_F16BLOCK70_CLEAN_REBUILD" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_TU22M3_CLEAN_REBUILD"
TREE_AIR = ROOT / "Data/INI/Object/Specter/Turkey Armed Forces/Airforce"

DONOR_PATH = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\TU22M3M.ini"
)
DONOR_OBJ = "RussiaJetTu22M3M"

TARGETS = [
    (
        r"Data\INI\Object\Specter\Turkey Armed Forces\Airforce\Turkey_Tu-22M3.ini",
        "Turkey_Tu-22M3",
    ),
    (
        r"Data\INI\Object\Specter\Turkey Armed Forces\Airforce\Turkey_Tu-22M3_AI.ini",
        "Turkey_Tu-22M3_AI",
    ),
]


def extract_object(text: str, object_name: str) -> str:
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Object\s+(\S+)", text)]
    for i, (start, name) in enumerate(starts):
        if name == object_name:
            end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
            return text[start:end]
    raise SystemExit(f"donor Object {object_name} missing")


def is_turkey_tu22_entry(name: str) -> bool:
    ln = name.lower().replace("/", "\\")
    return "turkey" in ln and ("tu-22m3" in ln or "tu22m3" in ln) and ln.endswith(".ini")


def is_turkey_air(name: str) -> bool:
    n = name.replace("/", "\\")
    if "Turkey Armed Forces" not in n or not n.lower().endswith(".ini"):
        return False
    return "\\Airforce\\" in n or "\\Drones\\" in n


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


def build_clean_turkey_bomber(donor_block: str, turkey_object: str) -> str:
    text = donor_block.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(
        rf"(?m)^Object\s+{re.escape(DONOR_OBJ)}\s*$",
        f"Object {turkey_object}",
        text,
        count=1,
    )
    text = re.sub(r"(?m)^(  Side\s*=\s*)\S+\s*$", r"\1Turkey", text, count=1)
    text = re.sub(
        r"(?m)^(  DisplayName\s*=\s*)\S+\s*$",
        rf"\1OBJECT:{turkey_object}",
        text,
        count=1,
    )

    # Drop any BuildVariations.
    lines = [ln for ln in text.splitlines() if not re.match(r"^\s*BuildVariations\s*=", ln)]
    text = "\n".join(lines) + "\n"

    turkey_prereq = (
        "  Prerequisites\n"
        "    Object = Turkey_AdvancedAirBase\n"
        "  End"
    )
    if re.search(r"(?ms)^\s*Prerequisites\b.*?^\s*End\s*$", text):
        text = re.sub(r"(?ms)^\s*Prerequisites\b.*?^\s*End\s*$", turkey_prereq, text, count=1)
    else:
        text = re.sub(r"(?m)^(\s*WeaponSet\b)", turkey_prereq + "\n\\1", text, count=1)

    text = text.replace("Upgrade_AmericaCountermeasures", "Upgrade_Turkey_Countermeasures")
    text = text.replace("Upgrade_AmericaAdvancedTraining", "Upgrade_Turkey_PrecisionMunitions")

    # AI twin keeps full Draw/WeaponSet/Locomotor/Geometry/CommandSet/Effects; not buildable.
    if turkey_object.endswith("_AI"):
        text = re.sub(r"(?m)^\s*Buildable\s*=.*(?:\n)?", "", text)
        text = re.sub(
            r"(?m)^(\s*KindOf\s*=.*\n)",
            r"\1  Buildable = No\n",
            text,
            count=1,
        )

    text = dedupe_shadow(text)
    text, _ = turkey_batch.remove_armor_set_flag(text)
    text, _ = turkey_batch.sanitize_ascii(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"

    header = (
        f"; SPECTER CLEAN REBUILD - {turkey_object}\n"
        f"; Prior Turkey Tu-22M3 BIG entries DELETED (not repaired)\n"
        f"; Donor: validated Russia {DONOR_OBJ} (TU22M3M.ini)\n"
        f"; Side=Turkey | BuildVariations=NONE | Prereq=Turkey_AdvancedAirBase\n"
        "; Modules: Object/Draw/WeaponSet/Locomotor/Geometry/CommandSet/Effects\n\n"
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


def validate_bomber(text: str, expect_object: str, entries, art_entries, label: str) -> list[str]:
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
    if re.findall(r"(?m)^Object\s+(\S+)", text) != [expect_object]:
        fails.append(f"{label}: Object mismatch {re.findall(r'(?m)^Object\\s+(\\S+)', text)}")
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
    if "RUS_SU34" in text:
        fails.append(f"{label}: old Su-34 roster model remains")
    if not text.startswith(f"; SPECTER CLEAN REBUILD - {expect_object}"):
        fails.append(f"{label}: missing clean-rebuild header")
    if "RUS_TU22M3M" not in text:
        fails.append(f"{label}: expected RUS_TU22M3M model")

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


def scan_turkey_air_bv(entries) -> list[str]:
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

    old_hits = [(n, r) for n, r in entries if is_turkey_tu22_entry(n)]
    print(f"DELETE phase: found {len(old_hits)} Turkey Tu-22M3-related INI entries")
    old_shas = set()
    for n, r in old_hits:
        sha = base.sha256_bytes(r)
        old_shas.add(sha)
        print(f"  removing {n} sha={sha[:16]} size={len(r)}")

    purged = [(n, r) for n, r in entries if not is_turkey_tu22_entry(n)]
    if any(is_turkey_tu22_entry(n) for n, _ in purged):
        raise SystemExit("purge failed")
    print(f"PURGED ok; entries {len(entries)} -> {len(purged)}")

    if base.knorm(DONOR_PATH) not in by:
        raise SystemExit("Russia Tu-22M3M donor missing")
    donor_text = by[base.knorm(DONOR_PATH)][1].decode("utf-8", "replace")
    donor_block = extract_object(donor_text, DONOR_OBJ)
    print(f"DONOR {DONOR_OBJ} bytes={len(donor_block)}")

    new_files: dict[str, bytes] = {}
    for path, obj in TARGETS:
        text = build_clean_turkey_bomber(donor_block, obj)
        raw = text.encode("ascii")
        if base.sha256_bytes(raw) in old_shas:
            raise SystemExit(f"{obj}: new hash collided with deleted content")
        if b"RUS_SU34" in raw:
            raise SystemExit(f"{obj}: Su-34 model leaked into clean rebuild")
        if not raw.startswith(f"; SPECTER CLEAN REBUILD - {obj}".encode("ascii")):
            raise SystemExit(f"{obj}: bad header")
        new_files[base.knorm(path)] = raw
        print(f"NEW {obj} sha={base.sha256_bytes(raw)[:16]} size={len(raw)}")

    # Scrub foreign BV on remaining Turkey air (same corruption pattern).
    scrubbed: dict[str, bytes] = {}
    for name, raw in purged:
        if not is_turkey_air(name):
            continue
        text = raw.decode("utf-8", "replace")
        fixed, changed = scrub_foreign_buildvariations(text)
        if changed:
            fixed = fixed.replace(
                "Upgrade_AmericaCountermeasures", "Upgrade_Turkey_Countermeasures"
            )
            fixed, _ = turkey_batch.sanitize_ascii(fixed)
            scrubbed[base.knorm(name)] = fixed.encode("ascii")
            print(f"SCRUB BV {Path(name.replace(chr(92), '/')).name}")

    rebuilt = []
    for name, raw in purged:
        kn = base.knorm(name)
        if kn in scrubbed:
            rebuilt.append((name, scrubbed[kn]))
        else:
            rebuilt.append((name, raw))
    # Insert new Tu-22 entries
    for path, obj in TARGETS:
        rebuilt.append((path, new_files[base.knorm(path)]))

    # Duplicate path guard
    counts: dict[str, int] = defaultdict(int)
    for n, _ in rebuilt:
        counts[base.knorm(n)] += 1
    dups = [k for k, v in counts.items() if v > 1]
    if dups:
        raise SystemExit(f"duplicate paths after rebuild: {dups}")

    failures: list[str] = []
    for path, obj in TARGETS:
        failures.extend(
            validate_bomber(
                new_files[base.knorm(path)].decode("ascii"),
                obj,
                rebuilt,
                art_entries,
                f"PREWRITE/{obj}",
            )
        )
    failures.extend(scan_turkey_air_bv(rebuilt))
    if failures:
        print("PRE-WRITE FAILED")
        for f in failures[:80]:
            print(" ", f)
        return 1
    print("PASS pre-write")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, rebuilt)
    final_entries = base.parse_big(out_big)

    final_hits = [(n, r) for n, r in final_entries if is_turkey_tu22_entry(n)]
    if len(final_hits) != 2:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"expected 2 final Tu-22 entries, got {final_hits}")

    extract_root = OUT / "_EXTRACT_VERIFY"
    if extract_root.exists():
        shutil.rmtree(extract_root)

    post: list[str] = []
    for path, obj in TARGETS:
        emb_name, emb = next(
            (n, r) for n, r in final_entries if base.knorm(n) == base.knorm(path)
        )
        expected = new_files[base.knorm(path)]
        if emb != expected:
            post.append(f"byte mismatch {obj}")
            continue
        if base.sha256_bytes(emb) in old_shas:
            post.append(f"old hash reused {obj}")
            continue
        if b"RUS_SU34" in emb:
            post.append(f"Su-34 remains {obj}")
            continue
        rel = Path(*Path(emb_name.replace("\\", "/")).parts)
        ep = extract_root / rel
        ep.parent.mkdir(parents=True, exist_ok=True)
        ep.write_bytes(emb)
        tp = TREE_AIR / Path(emb_name.replace("\\", "/")).name
        tp.write_bytes(expected)
        post.extend(
            validate_bomber(emb.decode("ascii"), obj, final_entries, art_entries, f"EXTRACT/{obj}")
        )

    post.extend(scan_turkey_air_bv(final_entries))
    if post:
        out_big.unlink(missing_ok=True)
        print("EXTRACT/INTEGRITY FAILED")
        for f in post[:80]:
            print(" ", f)
        return 1
    print("PASS extract + integrity")

    # Change scope: only target Tu-22 paths (+ optional BV scrubs)
    old_by = {base.knorm(n): r for n, r in entries}
    new_by = {base.knorm(n): r for n, r in final_entries}
    allowed = {base.knorm(p) for p, _ in TARGETS} | set(scrubbed)
    changed = [kn for kn in sorted(set(old_by) | set(new_by)) if old_by.get(kn) != new_by.get(kn)]
    unexpected = [c for c in changed if c not in allowed]
    if unexpected:
        raise SystemExit(f"unrelated paths changed: {unexpected[:20]}")
    print(f"CHANGED={len(changed)}")

    big_sha = base.sha256_file(out_big)
    big_size = out_big.stat().st_size
    main_sha = base.sha256_bytes(new_files[base.knorm(TARGETS[0][0])])

    for path, obj in TARGETS:
        (OUT / f"{obj}.ini").write_bytes(new_files[base.knorm(path)])

    verify = (
        "SPECTER TURKEY TU-22M3 CLEAN DELETE+REBUILD - VERIFY REPORT\n"
        "===========================================================\n"
        "VERDICT: PASS\n"
        "Method: DELETE prior Turkey_Tu-22M3(+AI) BIG entries, INSERT new clones\n"
        f"Donor: Russia {DONOR_OBJ} (validated RUS_TU22M3M W3D)\n"
        "Old Su-34 roster clone content: NOT reused\n"
        f"Removed entries: {len(old_hits)}\n"
        "Final Turkey Tu-22M3 INI entries: 2 (main + AI)\n"
        "Object=Turkey_Tu-22M3 / Turkey_Tu-22M3_AI Side=Turkey\n"
        "Modules: Object/Draw/WeaponSet/Locomotor/Geometry/CommandSet/Effects\n"
        "BuildVariations: ABSENT\n"
        "Turkey aircraft foreign-BuildVariations scan: PASS\n"
        "INI/W3D/Weapon/Locomotor validation: PASS\n"
        "Old broken hashes absent: PASS\n"
        f"\nTurkey_Tu-22M3.ini SHA256: {main_sha}\n"
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
        f"new_main_sha256={main_sha}\n"
        "old_hash_reuse=NO\nsu34_model=ABSENT\n"
        "header=SPECTER CLEAN REBUILD\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER TURKEY TU-22M3 CLEAN DELETE+REBUILD\n"
        "==========================================\n\n"
        "Broken Turkey_Tu-22M3 entries deleted from _SPEC_DATA_ONE.big.\n"
        "Rebuilt from validated Russia Tu-22M3M bomber. Side=Turkey.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in ("VERIFY_REPORT.txt", "EMBED_PROOF.txt", "README_INSTALL.txt"):
            shutil.copy2(OUT / name, final_dir / name)
        shutil.copy2(OUT / "Turkey_Tu-22M3.ini", final_dir / "Turkey_Tu-22M3.ini")

    zip_path = OUT / "_SPEC_DATA_ONE_TURKEY_TU22M3_CLEAN_REBUILD.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "Turkey_Tu-22M3.ini",
            "Turkey_Tu-22M3_AI.ini",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Turkey_Tu-22M3.ini SHA256={main_sha}\n"
        f"_SPEC_DATA_ONE_TURKEY_TU22M3_CLEAN_REBUILD.zip SHA256={zip_sha}\n",
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
