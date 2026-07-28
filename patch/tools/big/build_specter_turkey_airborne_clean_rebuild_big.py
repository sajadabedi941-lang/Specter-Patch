#!/usr/bin/env python3
"""DELETE broken Turkey Airborne.ini and INSERT clean Turkey_Airborne.

Does not repair the multi-object SpecOps/Iraq leftover Airborne.ini body.
Workflow:
1. Remove every Turkey .../Infantry/Airborne.ini BIG entry
2. Clone validated USA AmericaInfantryNavySeals_Assault
3. Rename to Object Turkey_Airborne / Side=Turkey
4. Assign Turkey_AirborneCommandSet (new Turkey CommandSet)
5. Remap America infantry upgrades to Turkey upgrades
6. Retarget Turkey OCL parachute payloads to Turkey_Airborne
7. Full Turkey object integrity scan; pack release ZIP
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
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_TU22M3_CLEAN_REBUILD" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_AIRBORNE_CLEAN_REBUILD"
TREE = ROOT / "Data/INI/Object/Specter/Turkey Armed Forces/Infantry/Airborne.ini"

NEW_PATH = r"Data\INI\Object\Specter\Turkey Armed Forces\Infantry\Airborne.ini"
DONOR_PATH = r"Data\INI\Object\Specter\United States Of America\Infantry\NavySeals.ini"
DONOR_OBJ = "AmericaInfantryNavySeals_Assault"
TURKEY_OBJ = "Turkey_Airborne"
TURKEY_CS = "Turkey_AirborneCommandSet"
CS_PATH = r"Data\INI\CommandSet_Turkey.ini"
OCL_PATH = r"Data\INI\ObjectCreationList_Turkey.ini"

OLD_PAYLOADS = (
    "TurkeyInfantrySpecOps_Akms",
    "TurkeyInfantrySpecOps_AKMGP",
    "TurkeyInfantrySpecOps_Rpk",
    "TurkeyInfantrySpecOps_Mks",
    "TurkeyInfantryAirborneHeavySniper",
)


def extract_object(text: str, object_name: str) -> str:
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Object\s+(\S+)", text)]
    for i, (start, name) in enumerate(starts):
        if name == object_name:
            end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
            return text[start:end]
    raise SystemExit(f"donor Object {object_name} missing")


def extract_commandset(text: str, name: str) -> str:
    m = re.search(
        rf"(?ms)^CommandSet\s+{re.escape(name)}\s*$.*?(?=^CommandSet\s|\Z)",
        text,
    )
    if not m:
        raise SystemExit(f"CommandSet {name} missing")
    return m.group(0).rstrip() + "\n"


def is_turkey_airborne_entry(name: str) -> bool:
    ln = name.lower().replace("/", "\\")
    return (
        "turkey" in ln
        and "airborne.ini" in ln
        and "\\infantry\\" in ln
        and ln.endswith(".ini")
    )


def is_turkey_object_ini(name: str) -> bool:
    n = name.replace("/", "\\")
    return "Turkey Armed Forces" in n and n.lower().endswith(".ini")


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


def build_turkey_airborne(donor_block: str) -> str:
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
    text = re.sub(
        r"(?m)^(  CommandSet\s*=\s*)\S+\s*$",
        rf"\1{TURKEY_CS}",
        text,
        count=1,
    )

    lines = [ln for ln in text.splitlines() if not re.match(r"^\s*BuildVariations\s*=", ln)]
    text = "\n".join(lines) + "\n"

    turkey_prereq = (
        "  Prerequisites\n"
        "    Object = Turkey_MIC\n"
        "  End"
    )
    if re.search(r"(?ms)^\s*Prerequisites\b.*?^\s*End\s*$", text):
        text = re.sub(r"(?ms)^\s*Prerequisites\b.*?^\s*End\s*$", turkey_prereq, text, count=1)
    else:
        text = re.sub(r"(?m)^(\s*WeaponSet\b)", turkey_prereq + "\n\\1", text, count=1)

    text = text.replace("Upgrade_AmericaChemicalSuits", "Upgrade_Turkey_Armor")
    text = text.replace("Upgrade_AmericaAdvancedTraining", "Upgrade_Turkey_GeneralAirAssault")

    text = dedupe_shadow(text)
    text, _ = turkey_batch.remove_armor_set_flag(text)
    text, _ = turkey_batch.sanitize_ascii(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"

    header = (
        f"; SPECTER CLEAN REBUILD - {TURKEY_OBJ}\n"
        "; Prior Turkey Airborne.ini BIG entries DELETED (not repaired)\n"
        f"; Donor: validated USA {DONOR_OBJ} (NavySeals.ini)\n"
        f"; Side=Turkey | CommandSet={TURKEY_CS} | Prereq=Turkey_MIC\n"
        "; Modules: Object/Draw/WeaponSet/Locomotor/Geometry/Behavior/Effects\n\n"
    )
    return header + text


def build_turkey_airborne_commandset(donor_cs: str) -> str:
    body = re.sub(
        r"(?m)^CommandSet\s+\S+\s*$",
        f"CommandSet {TURKEY_CS}",
        donor_cs,
        count=1,
    )
    return (
        f"\n; SPECTER CLEAN REBUILD - {TURKEY_CS}\n"
        f"; Cloned from AmericaInfantryNavySeal_AssaultCommandSet for {TURKEY_OBJ}\n"
        + body
        + ("\n" if not body.endswith("\n") else "")
    )


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


def parse_stack_fails(text: str, label: str) -> list[str]:
    fails: list[str] = []
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
        (re.compile(r"^\s*CommandSet\s+(?![=])\S+"), "CommandSet"),
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
    return fails


def validate_airborne(text: str, entries, art_entries, label: str) -> list[str]:
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
        fails.append(f"{label}: Object mismatch {re.findall(r'(?m)^Object\\s+(\\S+)', text)}")
    if not re.search(r"(?m)^\s*Side\s*=\s*Turkey\s*$", text):
        fails.append(f"{label}: Side!=Turkey")
    if not re.search(rf"(?m)^\s*CommandSet\s*=\s*{re.escape(TURKEY_CS)}\s*$", text):
        fails.append(f"{label}: CommandSet!={TURKEY_CS}")
    for field, pat in {
        "Draw": r"(?m)^\s*Draw\s*=\s*W3DModelDraw\b",
        "WeaponSet": r"(?m)^\s*WeaponSet\b",
        "Locomotor": r"(?m)^\s*Locomotor\s*=",
        "Geometry": r"(?m)^\s*Geometry\s*=",
        "Behavior": r"(?m)^\s*Behavior\s*=",
        "VoiceSelect": r"(?m)^\s*VoiceSelect\s*=",
    }.items():
        if not re.search(pat, text):
            fails.append(f"{label}: missing {field}")
    if re.search(r"(?m)^\s*BuildVariations\s*=", text):
        fails.append(f"{label}: BuildVariations must not exist")
    if "Upgrade_America" in text:
        fails.append(f"{label}: USA upgrade tokens remain")
    if re.search(r"(?i)\b(Irq_|irq_|IraqInfantry|TurkeyInfantrySpecOps)\b", text):
        fails.append(f"{label}: old Iraq/SpecOps tokens remain")
    if not text.startswith(f"; SPECTER CLEAN REBUILD - {TURKEY_OBJ}"):
        fails.append(f"{label}: missing clean-rebuild header")
    fails.extend(parse_stack_fails(text, label))

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


def turkey_integrity_scan(entries, art_entries) -> tuple[list[str], list[str]]:
    """Turkey integrity: hard-fail Airborne/refs/BV; soft-warn other pre-existing issues."""
    fails: list[str] = []
    warns: list[str] = []
    cats = catalog(entries)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }
    objs = cats["Object"]

    airborne_hits = [n for n, _ in entries if is_turkey_airborne_entry(n)]
    if len(airborne_hits) != 1:
        fails.append(f"Turkey Airborne.ini entry count={len(airborne_hits)} {airborne_hits}")

    for old in OLD_PAYLOADS:
        defs = [
            n
            for n, r in entries
            if re.search(rf"(?m)^Object\s+{re.escape(old)}\b".encode(), r)
        ]
        if defs:
            fails.append(f"old object {old} still defined in {defs}")

    for n, r in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = r.decode("utf-8", "replace")
        bn = Path(n.replace("\\", "/")).name
        for old in OLD_PAYLOADS:
            if re.search(rf"(?m)^\s*(?:Payload|Object)\s*=\s*{re.escape(old)}\b", t):
                fails.append(f"{bn}: still references deleted {old}")

    if TURKEY_CS not in cats["CommandSet"]:
        fails.append(f"missing CommandSet {TURKEY_CS}")
    if TURKEY_OBJ not in cats["Object"]:
        fails.append(f"missing Object {TURKEY_OBJ}")

    # Hard checks: foreign/missing BuildVariations on Turkey combat unit object INIs
    # (same corruption pattern as aircraft roster clones). Skip weapon/projectile catalogs.
    for n, r in entries:
        if not is_turkey_object_ini(n):
            continue
        nn = n.replace("/", "\\")
        if "\\Weapon" in nn or "\\Projectile" in nn or "WeaponObjects" in nn:
            continue
        text = r.decode("utf-8", "replace")
        bn = Path(n.replace("\\", "/")).name
        for m in re.finditer(r"(?m)^\s*BuildVariations\s*=\s*(.+)$", text):
            vals = m.group(1).split(";")[0].split()
            foreign = [v for v in vals if not v.startswith("Turkey")]
            missing = [v for v in vals if v not in objs]
            if foreign:
                fails.append(f"{bn}: foreign BV {foreign}")
            if missing:
                fails.append(f"{bn}: missing BV {missing}")

        # Soft: parse/W3D inventory for remaining Turkey objects (pre-existing debt)
        if is_turkey_airborne_entry(n):
            continue
        for msg in parse_stack_fails(text, bn):
            warns.append(msg)
        for model in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)):
            if model in ("None", "NONE", "NULL"):
                continue
            if model.lower() not in stems:
                warns.append(f"{bn}: missing W3D Model={model}")

    return fails, warns


def patch_ocl(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace SpecOps payloads with Turkey_Airborne; drop sniper payload into same unit count.
    text = re.sub(
        r"(?m)^(\s*Payload\s*=\s*)TurkeyInfantrySpecOps_Akms(\s+\d+\s*)$",
        rf"\1{TURKEY_OBJ}\2",
        text,
    )
    text = re.sub(
        r"(?m)^\s*Payload\s*=\s*TurkeyInfantryAirborneHeavySniper\s+\d+\s*\n?",
        "",
        text,
    )
    for old in OLD_PAYLOADS:
        text = re.sub(
            rf"(?m)^(\s*Payload\s*=\s*){re.escape(old)}(\s+\d+\s*)$",
            rf"\1{TURKEY_OBJ}\2",
            text,
        )
    return text


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG: {SRC}")

    entries = base.parse_big(SRC)
    art_entries = base.parse_big(ART)
    by = {base.knorm(n): (n, r) for n, r in entries}

    old_hits = [(n, r) for n, r in entries if is_turkey_airborne_entry(n)]
    print(f"DELETE phase: found {len(old_hits)} Turkey Airborne.ini entries")
    old_shas = set()
    for n, r in old_hits:
        sha = base.sha256_bytes(r)
        old_shas.add(sha)
        print(f"  removing {n} sha={sha[:16]} size={len(r)}")

    purged = [(n, r) for n, r in entries if not is_turkey_airborne_entry(n)]
    if any(is_turkey_airborne_entry(n) for n, _ in purged):
        raise SystemExit("purge failed")
    print(f"PURGED ok; entries {len(entries)} -> {len(purged)}")

    if base.knorm(DONOR_PATH) not in by:
        raise SystemExit("USA NavySeals donor missing")
    donor_text = by[base.knorm(DONOR_PATH)][1].decode("utf-8", "replace")
    donor_block = extract_object(donor_text, DONOR_OBJ)
    print(f"DONOR {DONOR_OBJ} bytes={len(donor_block)}")

    # Donor CommandSet from stock CommandSet.ini
    cs_stock = None
    for n, r in entries:
        if n.replace("/", "\\").endswith(r"Data\INI\CommandSet.ini"):
            cs_stock = r.decode("utf-8", "replace")
            break
    if cs_stock is None:
        raise SystemExit("CommandSet.ini missing")
    donor_cs = extract_commandset(cs_stock, "AmericaInfantryNavySeal_AssaultCommandSet")
    turkey_cs_block = build_turkey_airborne_commandset(donor_cs)

    new_text = build_turkey_airborne(donor_block)
    new_raw = new_text.encode("ascii")
    if base.sha256_bytes(new_raw) in old_shas:
        raise SystemExit("new hash collided with deleted Airborne.ini")
    if b"Irq_" in new_raw or b"irq_" in new_raw or b"TurkeyInfantrySpecOps" in new_raw:
        raise SystemExit("old Iraq/SpecOps tokens leaked into clean rebuild")
    print(f"NEW {TURKEY_OBJ} sha={base.sha256_bytes(new_raw)[:16]} size={len(new_raw)}")

    # Patch CommandSet_Turkey.ini + OCL
    if base.knorm(CS_PATH) not in by:
        raise SystemExit("CommandSet_Turkey.ini missing")
    if base.knorm(OCL_PATH) not in by:
        raise SystemExit("ObjectCreationList_Turkey.ini missing")

    cs_name, cs_raw = by[base.knorm(CS_PATH)]
    cs_text = cs_raw.decode("utf-8", "replace")
    if TURKEY_CS in cs_text:
        cs_text = re.sub(
            rf"(?ms)^CommandSet\s+{re.escape(TURKEY_CS)}\s*$.*?(?=^CommandSet\s|\Z)",
            "",
            cs_text,
        )
    cs_text = cs_text.rstrip() + "\n" + turkey_cs_block
    cs_text, _ = turkey_batch.sanitize_ascii(cs_text)
    cs_new = cs_text.encode("ascii")

    ocl_name, ocl_raw = by[base.knorm(OCL_PATH)]
    ocl_text = patch_ocl(ocl_raw.decode("utf-8", "replace"))
    ocl_text, _ = turkey_batch.sanitize_ascii(ocl_text)
    ocl_new = ocl_text.encode("ascii")

    rebuilt = []
    for name, raw in purged:
        kn = base.knorm(name)
        if kn == base.knorm(CS_PATH):
            rebuilt.append((cs_name, cs_new))
        elif kn == base.knorm(OCL_PATH):
            rebuilt.append((ocl_name, ocl_new))
        else:
            rebuilt.append((name, raw))
    rebuilt.append((NEW_PATH, new_raw))

    counts: dict[str, int] = defaultdict(int)
    for n, _ in rebuilt:
        counts[base.knorm(n)] += 1
    dups = [k for k, v in counts.items() if v > 1]
    if dups:
        raise SystemExit(f"duplicate paths after rebuild: {dups}")

    failures: list[str] = []
    failures.extend(validate_airborne(new_raw.decode("ascii"), rebuilt, art_entries, "PREWRITE"))
    integ_fails, integ_warns = turkey_integrity_scan(rebuilt, art_entries)
    failures.extend(integ_fails)
    if failures:
        print("PRE-WRITE FAILED")
        for f in failures[:100]:
            print(" ", f)
        return 1
    print(f"PASS pre-write (Turkey integrity soft-warns={len(integ_warns)})")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, rebuilt)
    final_entries = base.parse_big(out_big)

    final_hits = [(n, r) for n, r in final_entries if is_turkey_airborne_entry(n)]
    if len(final_hits) != 1:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"expected 1 final Airborne.ini, got {final_hits}")

    extract_root = OUT / "_EXTRACT_VERIFY"
    if extract_root.exists():
        shutil.rmtree(extract_root)

    post: list[str] = []
    emb_name, emb = final_hits[0]
    if emb != new_raw:
        post.append("byte mismatch Airborne.ini")
    if base.sha256_bytes(emb) in old_shas:
        post.append("old Airborne hash reused")
    if b"TurkeyInfantrySpecOps" in emb or b"Irq_" in emb:
        post.append("SpecOps/Iraq remain in Airborne.ini")

    rel = Path(*Path(emb_name.replace("\\", "/")).parts)
    ep = extract_root / rel
    ep.parent.mkdir(parents=True, exist_ok=True)
    ep.write_bytes(emb)
    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(new_raw)

    post.extend(validate_airborne(emb.decode("ascii"), final_entries, art_entries, "EXTRACT"))
    post_fails, post_warns = turkey_integrity_scan(final_entries, art_entries)
    post.extend(post_fails)
    if post:
        out_big.unlink(missing_ok=True)
        print("EXTRACT/INTEGRITY FAILED")
        for f in post[:100]:
            print(" ", f)
        return 1
    print(f"PASS extract + Turkey integrity (soft-warns={len(post_warns)})")
    (OUT / "TURKEY_INTEGRITY_WARNINGS.txt").write_text(
        "TURKEY OBJECT INTEGRITY - PRE-EXISTING SOFT WARNINGS\n"
        "====================================================\n"
        "These are inventory notes outside Airborne.ini hard gate.\n"
        f"count={len(post_warns)}\n\n"
        + "\n".join(post_warns[:500])
        + ("\n" if post_warns else "none\n"),
        encoding="ascii",
        errors="replace",
    )

    old_by = {base.knorm(n): r for n, r in entries}
    new_by = {base.knorm(n): r for n, r in final_entries}
    allowed = {base.knorm(NEW_PATH), base.knorm(CS_PATH), base.knorm(OCL_PATH)}
    # deleted airborne path appears as changed vs missing in old? old had it, new has it - same knorm
    changed = [kn for kn in sorted(set(old_by) | set(new_by)) if old_by.get(kn) != new_by.get(kn)]
    unexpected = [c for c in changed if c not in allowed]
    if unexpected:
        raise SystemExit(f"unrelated paths changed: {unexpected[:20]}")
    print(f"CHANGED={len(changed)}")

    big_sha = base.sha256_file(out_big)
    big_size = out_big.stat().st_size
    unit_sha = base.sha256_bytes(new_raw)

    (OUT / f"{TURKEY_OBJ}.ini").write_bytes(new_raw)
    (OUT / "Airborne.ini").write_bytes(new_raw)

    verify = (
        "SPECTER TURKEY AIRBORNE CLEAN DELETE+REBUILD - VERIFY REPORT\n"
        "============================================================\n"
        "VERDICT: PASS\n"
        "Method: DELETE prior Turkey Airborne.ini, INSERT clean USA NavySeal Assault clone\n"
        f"Donor: USA {DONOR_OBJ} (validated US_NavySeal / Spec_SF_Ind_A W3D)\n"
        "Old SpecOps multi-object / Iraq leftover content: NOT reused\n"
        f"Removed entries: {len(old_hits)}\n"
        f"Final Object={TURKEY_OBJ} Side=Turkey CommandSet={TURKEY_CS}\n"
        "Modules: Object/Draw/WeaponSet/Locomotor/Geometry/Behavior/Effects\n"
        "OCL parachute payloads retargeted to Turkey_Airborne\n"
        "Turkey integrity hard gate (Airborne/BV/dangling SpecOps): PASS\n"
        f"Turkey integrity soft-warns (pre-existing outside Airborne): {len(post_warns)}\n"
        "INI/W3D validation (Turkey_Airborne): PASS\n"
        f"\n{TURKEY_OBJ}.ini / Airborne.ini SHA256: {unit_sha}\n"
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
        f"new_sha256={unit_sha}\n"
        "old_hash_reuse=NO\n"
        "header=SPECTER CLEAN REBUILD\n"
        f"CommandSet={TURKEY_CS}\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER TURKEY AIRBORNE CLEAN DELETE+REBUILD\n"
        "===========================================\n\n"
        "Broken Turkey Airborne.ini deleted from _SPEC_DATA_ONE.big.\n"
        "Rebuilt Object Turkey_Airborne from validated USA Navy Seals Assault.\n"
        f"CommandSet={TURKEY_CS}. Side=Turkey.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in ("VERIFY_REPORT.txt", "EMBED_PROOF.txt", "README_INSTALL.txt"):
            shutil.copy2(OUT / name, final_dir / name)
        shutil.copy2(OUT / "Airborne.ini", final_dir / "Airborne.ini")
        shutil.copy2(OUT / f"{TURKEY_OBJ}.ini", final_dir / f"{TURKEY_OBJ}.ini")

    zip_path = OUT / "_SPEC_DATA_ONE_TURKEY_AIRBORNE_CLEAN_REBUILD.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "TURKEY_INTEGRITY_WARNINGS.txt",
            "Airborne.ini",
            f"{TURKEY_OBJ}.ini",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Airborne.ini SHA256={unit_sha}\n"
        f"_SPEC_DATA_ONE_TURKEY_AIRBORNE_CLEAN_REBUILD.zip SHA256={zip_sha}\n",
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
