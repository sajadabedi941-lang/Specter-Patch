#!/usr/bin/env python3
"""Fix Turkey_F16Block70 parse/init crash and same pattern on Turkey aircraft.

Root cause introduced by aircraft-roster donor clone:
1. BuildVariations pointed at foreign America/Russia Objects (and Turkey F16V
   Mixed/AGM/GBU24 variants were deleted), which breaks Object resolution.
2. USA Upgrade_* tokens and AmericaHelicopter ReplaceObject targets remained.

Repair:
- Restore Turkey_F16Block70 + multi-object Turkey_F16V from the last
  Turkey-faction-validated BIG (Side=Turkey, Turkey weapons/upgrades/BV).
- Strip foreign BuildVariations on all Turkey Airforce/Drones files.
- Remap Upgrade_AmericaCountermeasures -> Upgrade_Turkey_Countermeasures.
- Remap Upgrade_AmericaAdvancedTraining -> Upgrade_Turkey_PrecisionMunitions.
- Remove ReplaceObject lines targeting non-Turkey objects.
- Validate Weapons/Locomotors/Models/Draw and pack release BIG/ZIP.
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
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_AIRCRAFT_ROSTER_FIXED" / "_SPEC_DATA_ONE.big"
DONOR_BIG = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_FACTION_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_F16BLOCK70_FIXED"
TREE_ROOT = ROOT / "Data/INI/Object/Specter/Turkey Armed Forces"

F16BLOCK70 = r"Data\INI\Object\Specter\Turkey Armed Forces\Airforce\Turkey_F16Block70.ini"
F16V = r"Data\INI\Object\Specter\Turkey Armed Forces\Airforce\Turkey_F16V.ini"

RESTORE = {base.knorm(F16BLOCK70), base.knorm(F16V)}


def is_turkey_air(entry_name: str) -> bool:
    n = entry_name.replace("/", "\\")
    if "Turkey Armed Forces" not in n or not n.lower().endswith(".ini"):
        return False
    return "\\Airforce\\" in n or "\\Drones\\" in n


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


def sanitize_restored(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text, _ = turkey_batch.sanitize_ascii(text)
    text = text.replace("Upgrade_AmericaCountermeasures", "Upgrade_Turkey_Countermeasures")
    text = text.replace("Upgrade_AmericaAdvancedTraining", "Upgrade_Turkey_PrecisionMunitions")
    # Ensure no foreign BuildVariations slipped in.
    text = strip_foreign_build_variations(text, set())  # object set unused when forcing turkey-only
    text = dedupe_shadow(text)
    if not text.endswith("\n"):
        text += "\n"
    return text


def dedupe_shadow(text: str) -> str:
    lines = []
    seen = False
    in_object = False
    for line in text.splitlines():
        code = line.split(";", 1)[0]
        if re.match(r"^\s*Object\s+(?![=])\S+", code):
            in_object = True
            seen = False
        if re.match(r"^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", code):
            if seen:
                continue
            seen = True
        lines.append(line)
    return "\n".join(lines) + "\n"


def strip_foreign_build_variations(text: str, object_names: set[str]) -> str:
    """Remove BuildVariations lines that reference non-Turkey or missing Objects."""
    out: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^(\s*BuildVariations\s*=\s*)(.+)$", line)
        if not m:
            out.append(line)
            continue
        raw_vals = m.group(2).split(";", 1)[0]
        vals = raw_vals.split()
        comment = ""
        if ";" in m.group(2):
            comment = ";" + m.group(2).split(";", 1)[1]
        keep = []
        for v in vals:
            if not v.startswith("Turkey"):
                continue
            if object_names and v not in object_names:
                continue
            keep.append(v)
        if not keep:
            # Drop the field entirely — safest parse-compatible fix.
            out.append(f"  ; REMOVED BuildVariations (foreign/missing): {' '.join(vals)}")
            continue
        out.append(f"{m.group(1)}{' '.join(keep)}{comment}")
    return "\n".join(out) + "\n"


def remap_usa_upgrades(text: str) -> str:
    text = text.replace("Upgrade_AmericaCountermeasures", "Upgrade_Turkey_Countermeasures")
    text = text.replace("Upgrade_AmericaAdvancedTraining", "Upgrade_Turkey_PrecisionMunitions")
    return text


def strip_foreign_replace_object(text: str) -> tuple[str, int]:
    removed = 0
    out: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^(\s*ReplaceObject\s*=\s*)(\S+)(.*)$", line)
        if m and not m.group(2).startswith("Turkey"):
            out.append(f"{m.group(1)[:0]}; REMOVED ReplaceObject = {m.group(2)}{m.group(3)}")
            # keep indentation as comment
            indent = re.match(r"^(\s*)", line).group(1)
            out[-1] = f"{indent}; REMOVED ReplaceObject = {m.group(2)}"
            removed += 1
            continue
        out.append(line)
    return "\n".join(out) + "\n", removed


def repair_turkey_air(text: str, object_names: set[str]) -> tuple[str, dict[str, int]]:
    stats = {"buildvariations": 0, "replaceobject": 0, "usa_upgrade": 0}
    old = text
    if "Upgrade_AmericaCountermeasures" in text or "Upgrade_AmericaAdvancedTraining" in text:
        stats["usa_upgrade"] = len(re.findall(r"Upgrade_America(?:Countermeasures|AdvancedTraining)", text))
    text = remap_usa_upgrades(text)
    # Count BV removals
    before_bv = len(re.findall(r"(?m)^\s*BuildVariations\s*=", text))
    text = strip_foreign_build_variations(text, object_names)
    after_bv = len(re.findall(r"(?m)^\s*BuildVariations\s*=", text))
    stats["buildvariations"] = before_bv - after_bv
    text, removed_ro = strip_foreign_replace_object(text)
    stats["replaceobject"] = removed_ro
    text, _ = turkey_batch.sanitize_ascii(text)
    text = dedupe_shadow(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"
    return text, stats


def validate_aircraft(text: str, entry_name: str, entries, art_entries, label: str) -> list[str]:
    fails: list[str] = []
    cats = catalog(entries)
    data_join = b"\n".join(b for _, b in entries)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }
    bn = Path(entry_name.replace("\\", "/")).name

    if any(ord(c) > 127 for c in text):
        fails.append(f"{label}/{bn}: non-ASCII")
    if not re.search(r"(?m)^Object\s+\S+", text):
        fails.append(f"{label}/{bn}: no Object")
    sides = set(re.findall(r"(?m)^\s*Side\s*=\s*(\S+)", text))
    if sides and sides != {"Turkey"}:
        fails.append(f"{label}/{bn}: Side={sides}")
    if not re.search(r"(?m)^\s*Draw\s*=", text):
        fails.append(f"{label}/{bn}: Draw missing")
    if re.search(r"(?m)^\s*ArmorSetFlag\s*=", text):
        fails.append(f"{label}/{bn}: ArmorSetFlag")
    if re.findall(r"(?m)^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", text).count("Shadow") > 1:
        pass
    vols = re.findall(r"(?m)^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", text)
    # per-file allow multiple objects each with one volume; check per object below
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Object\s+(\S+)", text)]
    for i, (start, obj) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        block = text[start:end]
        if len(re.findall(r"(?m)^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", block)) > 1:
            fails.append(f"{label}/{bn}: {obj} duplicate Shadow")
        if not re.search(r"(?m)^\s*Side\s*=\s*Turkey\s*$", block):
            # some helper objects may omit Side; require for primary Turkey_* / TurkeyDrones*
            if obj.startswith("Turkey_") or obj.startswith("TurkeyDrones") or obj.startswith("TurkeyDrone"):
                # Allow weapon-like subobjects without Side
                if re.search(r"(?m)^\s*KindOf\s*=.*AIRCRAFT", block) or re.search(
                    r"(?m)^\s*Draw\s*=", block
                ):
                    if "Side" in block and not re.search(r"(?m)^\s*Side\s*=\s*Turkey\s*$", block):
                        fails.append(f"{label}/{bn}: {obj} Side!=Turkey")

    # Foreign BuildVariations must be gone
    for m in re.finditer(r"(?m)^\s*BuildVariations\s*=\s*(.+)$", text):
        vals = m.group(1).split(";")[0].split()
        bad = [v for v in vals if not v.startswith("Turkey")]
        miss = [v for v in vals if v not in cats["Object"]]
        if bad:
            fails.append(f"{label}/{bn}: foreign BuildVariations {bad}")
        if miss:
            fails.append(f"{label}/{bn}: missing BuildVariations {miss}")

    for m in re.finditer(r"(?m)^\s*ReplaceObject\s*=\s*(\S+)", text):
        if not m.group(1).startswith("Turkey"):
            fails.append(f"{label}/{bn}: foreign ReplaceObject {m.group(1)}")
        elif m.group(1) not in cats["Object"]:
            fails.append(f"{label}/{bn}: missing ReplaceObject {m.group(1)}")

    if "Upgrade_AmericaCountermeasures" in text or "Upgrade_AmericaAdvancedTraining" in text:
        fails.append(f"{label}/{bn}: USA upgrade tokens remain")

    def need(kind: str, vals: list[str]) -> None:
        for v in vals:
            if v in ("None", "NONE"):
                continue
            if v not in cats[kind] and v.encode() not in data_join:
                fails.append(f"{label}/{bn}: missing {kind}={v}")

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
            fails.append(f"{label}/{bn}: missing W3D Model={model}")

    # Strict Object/Draw/End balance for F-16 focus files; other air gets pattern/deps checks.
    bn_lower = bn.lower()
    if "f16" in bn_lower:
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
                    fails.append(f"{label}/{bn}: extra End @{i}")
                else:
                    stack.pop()
                continue
            for rx, kind in openers:
                if rx.match(code):
                    stack.append((kind, i))
                    break
        if stack:
            fails.append(f"{label}/{bn}: unclosed {stack[-10:]}")
    return fails


def tree_path_for(entry_name: str) -> Path:
    parts = Path(entry_name.replace("\\", "/")).parts
    idx = list(parts).index("Turkey Armed Forces")
    return TREE_ROOT / Path(*parts[idx + 1 :])


def main() -> int:
    if not SRC.is_file() or not DONOR_BIG.is_file():
        raise SystemExit("missing source/donor BIG")

    entries = base.parse_big(SRC)
    donor_entries = base.parse_big(DONOR_BIG)
    donor_by = {base.knorm(n): (n, r) for n, r in donor_entries}
    art_entries = base.parse_big(ART)

    # Provisional object set after planned F16V restore
    object_names: set[str] = set()
    for n, b in entries:
        if n.lower().endswith(".ini"):
            object_names.update(re.findall(r"(?m)^Object\s+(\S+)", b.decode("utf-8", "replace")))
    # Add restored F16V variants from donor BIG
    _, f16v_raw = donor_by[base.knorm(F16V)]
    object_names.update(re.findall(r"(?m)^Object\s+(\S+)", f16v_raw.decode("utf-8", "replace")))

    repaired: dict[str, bytes] = {}
    stats_total = defaultdict(int)
    notes: list[str] = []

    for name, raw in entries:
        kn = base.knorm(name)
        if kn in RESTORE:
            dname, draw = donor_by[kn]
            text = sanitize_restored(draw.decode("utf-8", "replace"))
            # For restored F16 files, keep Turkey BuildVariations that resolve.
            text = strip_foreign_build_variations(text, object_names)
            text = remap_usa_upgrades(text)
            repaired[kn] = text.encode("ascii")
            notes.append(f"RESTORED {Path(name.replace(chr(92),'/')).name} from Turkey faction-fixed BIG")
            print(notes[-1])
            continue
        if not is_turkey_air(name):
            continue
        text = raw.decode("utf-8", "replace")
        fixed, stats = repair_turkey_air(text, object_names)
        for k, v in stats.items():
            stats_total[k] += v
        if fixed.encode("ascii") != raw:
            repaired[kn] = fixed.encode("ascii")
            bn = Path(name.replace("\\", "/")).name
            print(f"REPAIRED {bn} stats={stats}")

    # Ensure both restores present
    for path in (F16BLOCK70, F16V):
        if base.knorm(path) not in repaired:
            raise SystemExit(f"restore missing for {path}")

    candidate = [
        (name, repaired[base.knorm(name)] if base.knorm(name) in repaired else raw)
        for name, raw in entries
    ]

    # Focus validation for F16Block70
    f16_text = repaired[base.knorm(F16BLOCK70)].decode("ascii")
    if "AmericaJet" in f16_text and re.search(r"(?m)^\s*BuildVariations\s*=.*America", f16_text):
        raise SystemExit("F16Block70 still has America BuildVariations")
    if not re.search(r"(?m)^\s*Side\s*=\s*Turkey\s*$", f16_text):
        raise SystemExit("F16Block70 Side!=Turkey")
    if "Upgrade_America" in f16_text:
        raise SystemExit("F16Block70 still has USA upgrades")

    failures: list[str] = []
    for name, raw in candidate:
        if not is_turkey_air(name):
            continue
        text = raw.decode("utf-8", "replace")
        if any(ord(c) > 127 for c in text):
            failures.append(f"PREWRITE nonascii {name}")
            continue
        failures.extend(validate_aircraft(text, name, candidate, art_entries, "PREWRITE"))

    if failures:
        print("PRE-WRITE FAILED")
        for f in failures[:100]:
            print(" ", f)
        return 1
    print("PASS pre-write Turkey air validation")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, candidate)
    rebuilt = base.parse_big(out_big)
    rebuilt_by = {base.knorm(n): (n, r) for n, r in rebuilt}

    old_by = {base.knorm(n): r for n, r in entries}
    changed = [n for n, r in rebuilt if r != old_by[base.knorm(n)]]
    unexpected = [n for n in changed if base.knorm(n) not in repaired]
    if unexpected:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"unrelated changed: {unexpected[:20]}")

    extract_root = OUT / "_EXTRACT_VERIFY"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True)

    post: list[str] = []
    for kn, expected in repaired.items():
        emb_name, emb = rebuilt_by[kn]
        if emb != expected:
            post.append(f"byte mismatch {emb_name}")
            continue
        rel = Path(*Path(emb_name.replace("\\", "/")).parts)
        ep = extract_root / rel
        ep.parent.mkdir(parents=True, exist_ok=True)
        ep.write_bytes(emb)
        tp = tree_path_for(emb_name)
        tp.parent.mkdir(parents=True, exist_ok=True)
        tp.write_bytes(expected)
        post.extend(
            validate_aircraft(emb.decode("ascii"), emb_name, rebuilt, art_entries, "EXTRACT")
        )

    if post:
        out_big.unlink(missing_ok=True)
        print("EXTRACT FAILED")
        for f in post[:100]:
            print(" ", f)
        return 1

    # Explicit F16Block70 proof
    f16_emb = rebuilt_by[base.knorm(F16BLOCK70)][1].decode("ascii")
    proof = []
    proof.append(f"objects={re.findall(r'(?m)^Object\\s+(\\S+)', f16_emb)}")
    proof.append(f"side={re.findall(r'(?m)^\\s*Side\\s*=\\s*(\\S+)', f16_emb)}")
    proof.append(f"BV={re.findall(r'(?m)^\\s*BuildVariations\\s*=\\s*(.+)$', f16_emb)}")
    proof.append(f"draw={bool(re.search(r'(?m)^\\s*Draw\\s*=', f16_emb))}")
    print("F16Block70", "; ".join(proof))

    big_sha = base.sha256_file(out_big)
    big_size = out_big.stat().st_size
    print(f"CHANGED={len(changed)} SHA256={big_sha} SIZE={big_size}")

    (OUT / "Turkey_F16Block70.ini").write_bytes(repaired[base.knorm(F16BLOCK70)])
    (OUT / "Turkey_F16V.ini").write_bytes(repaired[base.knorm(F16V)])

    verify = (
        "SPECTER TURKEY F16BLOCK70 PARSE FIX - VERIFY REPORT\n"
        "===================================================\n"
        "VERDICT: PASS\n"
        "Patched INSIDE: _SPEC_DATA_ONE.big\n"
        "Exact error pattern: BuildVariations referenced foreign America/Russia\n"
        "  Objects after roster clone; Turkey_F16V Mixed/AGM/GBU24 variants missing.\n"
        "Repair:\n"
        "- Restored Turkey_F16Block70.ini + Turkey_F16V.ini (4 Objects) from\n"
        "  Turkey-faction-validated BIG with Side=Turkey\n"
        "- Removed foreign BuildVariations on Turkey aircraft\n"
        "- Remapped Upgrade_America* -> Upgrade_Turkey_*\n"
        "- Removed foreign ReplaceObject targets\n"
        "Validation: Object/Draw/Shadow/Weapon/Locomotor/Model/CommandSet/End PASS\n"
        "All Turkey Airforce+Drones scanned for same pattern: PASS\n"
        "Extract-from-BIG byte match: PASS\n"
        "Unrelated BIG entries changed: 0\n"
        f"Files changed: {len(changed)}\n"
        f"Stats: {dict(stats_total)}\n"
        f"\nBIG SHA256: {big_sha}\nBIG SIZE: {big_size}\nFINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(verify, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT\n"
        "===============\n"
        f"Turkey_F16Block70 restored+validated\n"
        f"Turkey_F16V variants restored\n"
        f"changed={len(changed)}\n"
        "byte_match=YES\nforeign_BuildVariations=0\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER TURKEY F16BLOCK70 PARSE FIX\n"
        "===================================\n\n"
        "Fixes Turkey_F16Block70.ini foreign BuildVariations crash pattern and\n"
        "applies the same cleanup across Turkey aircraft.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )
    (OUT / "CHANGED_FILES.txt").write_text("\n".join(sorted(changed)) + "\n", encoding="ascii")

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in ("VERIFY_REPORT.txt", "EMBED_PROOF.txt", "README_INSTALL.txt"):
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_TURKEY_F16BLOCK70_FIXED.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "CHANGED_FILES.txt",
            "Turkey_F16Block70.ini",
            "Turkey_F16V.ini",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"_SPEC_DATA_ONE_TURKEY_F16BLOCK70_FIXED.zip SHA256={zip_sha}\n",
        encoding="ascii",
    )
    if final_dir.is_dir():
        shutil.copy2(OUT / "HASHES.txt", final_dir / "HASHES.txt")
    print(f"ZIP SHA256={zip_sha}")
    print("FINAL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
