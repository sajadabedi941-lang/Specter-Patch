#!/usr/bin/env python3
"""DELETE broken Turkey_EliteMaroonBerets and INSERT clean USA NavySeal clone.

Does not repair the Iraq-art leftover Maroon Berets body.
Workflow:
1. Remove Turkey_EliteMaroonBerets.ini BIG entry
2. Clone validated USA AmericaInfantryNavySeals_Assault
3. Object Turkey_EliteMaroonBerets / Side=Turkey / Turkey CommandSet
4. DisplayName via OBJECT:Turkey_EliteMaroonBerets -> "Turkey Elite Maroon Berets"
5. Full Turkey integrity (Airborne + SpecialForces preserved); pack ZIP
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
SRC = (
    ROOT
    / "Release"
    / "SPECTER_SPEC_DATA_ONE_TURKEY_SPECIALFORCES_CLEAN_REBUILD"
    / "_SPEC_DATA_ONE.big"
)
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_MAROONBERETS_CLEAN_REBUILD"
TREE = (
    ROOT
    / "Data/INI/Object/Specter/Turkey Armed Forces/Infantry/Turkey_EliteMaroonBerets.ini"
)

NEW_PATH = (
    r"Data\INI\Object\Specter\Turkey Armed Forces\Infantry\Turkey_EliteMaroonBerets.ini"
)
DONOR_PATH = r"Data\INI\Object\Specter\United States Of America\Infantry\NavySeals.ini"
DONOR_OBJ = "AmericaInfantryNavySeals_Assault"
DONOR_CS = "AmericaInfantryNavySeal_AssaultCommandSet"
TURKEY_OBJ = "Turkey_EliteMaroonBerets"
TURKEY_CS = "Turkey_EliteMaroonBeretsCommandSet"
DISPLAY_KEY = "OBJECT:Turkey_EliteMaroonBerets"
DISPLAY_TEXT = "Turkey Elite Maroon Berets"
CS_PATH = r"Data\INI\CommandSet_Turkey.ini"
STRINGS_PATH = r"Data\English\FactionExpansion_PhaseF_Strings.txt"


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


def is_maroon_entry(name: str) -> bool:
    ln = name.lower().replace("/", "\\")
    return (
        "turkey" in ln
        and "elitemaroonberets" in ln
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


def build_maroon(donor_block: str) -> str:
    text = donor_block.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(
        rf"(?m)^Object\s+{re.escape(DONOR_OBJ)}\s*$",
        f"Object {TURKEY_OBJ}",
        text,
        count=1,
    )
    text = re.sub(r"(?m)^(  Side\s*=\s*)\S+\s*$", r"\1Turkey", text, count=1)
    # Engine DisplayName is a string-table key; friendly text set in PhaseF strings.
    text = re.sub(
        r"(?m)^(  DisplayName\s*=\s*)\S+\s*$",
        rf"\1{DISPLAY_KEY}",
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
        "; Prior Turkey_EliteMaroonBerets.ini BIG entry DELETED (not repaired)\n"
        f"; Donor: validated USA {DONOR_OBJ} (NavySeals.ini)\n"
        f"; Side=Turkey | CommandSet={TURKEY_CS} | DisplayName={DISPLAY_TEXT}\n"
        f"; DisplayName key {DISPLAY_KEY} resolved via PhaseF strings\n"
        "; Modules: Object/Draw/WeaponSet/Armor/Locomotor/Behavior/Effects\n\n"
    )
    return header + text


def build_turkey_cs(donor_cs: str) -> str:
    body = re.sub(
        r"(?m)^CommandSet\s+\S+\s*$",
        f"CommandSet {TURKEY_CS}",
        donor_cs,
        count=1,
    )
    return (
        f"\n; SPECTER CLEAN REBUILD - {TURKEY_CS}\n"
        f"; Cloned from {DONOR_CS} for {TURKEY_OBJ}\n"
        + body
        + ("\n" if not body.endswith("\n") else "")
    )


def patch_strings(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Friendly DisplayName text requested by task.
    text, n1 = re.subn(
        rf"(?m)^{re.escape(DISPLAY_KEY)}\s*=\s*.*$",
        f"{DISPLAY_KEY} = {DISPLAY_TEXT}",
        text,
        count=1,
    )
    text, n2 = re.subn(
        r"(?m)^CONTROLBAR:ConstructTurkey_EliteMaroonBerets\s*=\s*.*$",
        f"CONTROLBAR:ConstructTurkey_EliteMaroonBerets = {DISPLAY_TEXT}",
        text,
        count=1,
    )
    text, n3 = re.subn(
        r"(?m)^CONTROLBAR:ToolTipConstructTurkey_EliteMaroonBerets\s*=\s*.*$",
        f"CONTROLBAR:ToolTipConstructTurkey_EliteMaroonBerets = Train {DISPLAY_TEXT}.",
        text,
        count=1,
    )
    if n1 != 1:
        # Append if missing.
        text = text.rstrip() + f"\n{DISPLAY_KEY} = {DISPLAY_TEXT}\n"
    return text


def catalog(entries):
    cats: dict[str, set[str]] = defaultdict(set)
    for n, b in entries:
        if not n.lower().endswith(".ini") and not n.lower().endswith(".txt"):
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


def validate_maroon(text: str, entries, art_entries, label: str) -> list[str]:
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
    if not re.search(rf"(?m)^\s*DisplayName\s*=\s*{re.escape(DISPLAY_KEY)}\s*$", text):
        fails.append(f"{label}: DisplayName key mismatch")
    if not re.search(rf"(?m)^\s*CommandSet\s*=\s*{re.escape(TURKEY_CS)}\s*$", text):
        fails.append(f"{label}: CommandSet!={TURKEY_CS}")
    for field, pat in {
        "Draw": r"(?m)^\s*Draw\s*=\s*W3DModelDraw\b",
        "WeaponSet": r"(?m)^\s*WeaponSet\b",
        "ArmorSet": r"(?m)^\s*ArmorSet\b",
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
    if re.search(r"(?i)\b(Irq_|irq_)\b", text):
        fails.append(f"{label}: Iraq tokens remain")
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
    fails: list[str] = []
    warns: list[str] = []
    cats = catalog(entries)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }
    objs = cats["Object"]

    mb_hits = [n for n, _ in entries if is_maroon_entry(n)]
    if len(mb_hits) != 1:
        fails.append(f"Turkey_EliteMaroonBerets.ini entry count={len(mb_hits)} {mb_hits}")

    required_objects = {
        TURKEY_OBJ,
        "Turkey_Airborne",
        "Turkey_SpecialForces",
    }
    required_cs = {
        TURKEY_CS,
        "Turkey_AirborneCommandSet",
        "Turkey_SpecialForcesCommandSet",
    }
    for o in required_objects:
        if o not in cats["Object"]:
            fails.append(f"missing Object {o}")
    for c in required_cs:
        if c not in cats["CommandSet"]:
            fails.append(f"missing CommandSet {c}")

    # DisplayName friendly text present in strings
    strings_ok = False
    for n, r in entries:
        if base.knorm(n) == base.knorm(STRINGS_PATH):
            t = r.decode("utf-8", "replace")
            if re.search(
                rf"(?m)^{re.escape(DISPLAY_KEY)}\s*=\s*{re.escape(DISPLAY_TEXT)}\s*$",
                t,
            ):
                strings_ok = True
            break
    if not strings_ok:
        fails.append(f"PhaseF strings missing '{DISPLAY_KEY} = {DISPLAY_TEXT}'")

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

        if is_maroon_entry(n):
            if any(ord(c) > 127 for c in text):
                fails.append(f"{bn}: non-ASCII")
            if re.search(r"(?i)\b(Irq_|irq_)\b", text):
                fails.append(f"{bn}: Iraq tokens remain")
            continue
        for msg in parse_stack_fails(text, bn):
            warns.append(msg)
        for model in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)):
            if model in ("None", "NONE", "NULL"):
                continue
            if model.lower() not in stems:
                warns.append(f"{bn}: missing W3D Model={model}")

    return fails, warns


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG: {SRC}")

    entries = base.parse_big(SRC)
    art_entries = base.parse_big(ART)
    by = {base.knorm(n): (n, r) for n, r in entries}

    old_hits = [(n, r) for n, r in entries if is_maroon_entry(n)]
    print(f"DELETE phase: found {len(old_hits)} Turkey_EliteMaroonBerets entries")
    old_shas = set()
    for n, r in old_hits:
        sha = base.sha256_bytes(r)
        old_shas.add(sha)
        print(f"  removing {n} sha={sha[:16]} size={len(r)}")

    purged = [(n, r) for n, r in entries if not is_maroon_entry(n)]
    print(f"PURGED ok; entries {len(entries)} -> {len(purged)}")

    if base.knorm(DONOR_PATH) not in by:
        raise SystemExit("USA NavySeals donor missing")
    donor_block = extract_object(
        by[base.knorm(DONOR_PATH)][1].decode("utf-8", "replace"), DONOR_OBJ
    )
    print(f"DONOR {DONOR_OBJ} bytes={len(donor_block)}")

    cs_stock = None
    for n, r in entries:
        if n.replace("/", "\\").endswith(r"Data\INI\CommandSet.ini"):
            cs_stock = r.decode("utf-8", "replace")
            break
    if cs_stock is None:
        raise SystemExit("CommandSet.ini missing")
    turkey_cs_block = build_turkey_cs(extract_commandset(cs_stock, DONOR_CS))

    new_text = build_maroon(donor_block)
    new_raw = new_text.encode("ascii")
    if base.sha256_bytes(new_raw) in old_shas:
        raise SystemExit("new hash collided with deleted MaroonBerets")
    if b"Irq_" in new_raw or b"irq_" in new_raw:
        raise SystemExit("Iraq tokens leaked into clean rebuild")
    print(f"NEW {TURKEY_OBJ} sha={base.sha256_bytes(new_raw)[:16]} size={len(new_raw)}")

    for req in (CS_PATH, STRINGS_PATH):
        if base.knorm(req) not in by:
            raise SystemExit(f"missing {req}")

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

    str_name, str_raw = by[base.knorm(STRINGS_PATH)]
    str_text = patch_strings(str_raw.decode("utf-8", "replace"))
    str_text, _ = turkey_batch.sanitize_ascii(str_text)
    str_new = str_text.encode("ascii")

    rebuilt = []
    for name, raw in purged:
        kn = base.knorm(name)
        if kn == base.knorm(CS_PATH):
            rebuilt.append((cs_name, cs_new))
        elif kn == base.knorm(STRINGS_PATH):
            rebuilt.append((str_name, str_new))
        else:
            rebuilt.append((name, raw))
    rebuilt.append((NEW_PATH, new_raw))

    counts: dict[str, int] = defaultdict(int)
    for n, _ in rebuilt:
        counts[base.knorm(n)] += 1
    dups = [k for k, v in counts.items() if v > 1]
    if dups:
        raise SystemExit(f"duplicate paths: {dups}")

    failures: list[str] = []
    failures.extend(validate_maroon(new_raw.decode("ascii"), rebuilt, art_entries, "PREWRITE"))
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

    final_hits = [(n, r) for n, r in final_entries if is_maroon_entry(n)]
    if len(final_hits) != 1:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"expected 1 final MaroonBerets entry, got {final_hits}")

    extract_root = OUT / "_EXTRACT_VERIFY"
    if extract_root.exists():
        shutil.rmtree(extract_root)

    post: list[str] = []
    emb_name, emb = final_hits[0]
    if emb != new_raw:
        post.append("byte mismatch MaroonBerets")
    if base.sha256_bytes(emb) in old_shas:
        post.append("old MaroonBerets hash reused")
    if b"Irq_" in emb or b"irq_" in emb:
        post.append("Iraq tokens remain")

    rel = Path(*Path(emb_name.replace("\\", "/")).parts)
    ep = extract_root / rel
    ep.parent.mkdir(parents=True, exist_ok=True)
    ep.write_bytes(emb)
    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(new_raw)

    post.extend(validate_maroon(emb.decode("ascii"), final_entries, art_entries, "EXTRACT"))
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
        "Hard gate: MaroonBerets + Airborne + SpecialForces + BV + DisplayName.\n"
        f"count={len(post_warns)}\n\n"
        + "\n".join(post_warns[:500])
        + ("\n" if post_warns else "none\n"),
        encoding="ascii",
        errors="replace",
    )

    old_by = {base.knorm(n): r for n, r in entries}
    new_by = {base.knorm(n): r for n, r in final_entries}
    allowed = {base.knorm(NEW_PATH), base.knorm(CS_PATH), base.knorm(STRINGS_PATH)}
    changed = [kn for kn in sorted(set(old_by) | set(new_by)) if old_by.get(kn) != new_by.get(kn)]
    unexpected = [c for c in changed if c not in allowed]
    if unexpected:
        raise SystemExit(f"unrelated paths changed: {unexpected[:20]}")
    print(f"CHANGED={len(changed)}")

    big_sha = base.sha256_file(out_big)
    big_size = out_big.stat().st_size
    unit_sha = base.sha256_bytes(new_raw)

    (OUT / f"{TURKEY_OBJ}.ini").write_bytes(new_raw)
    (ROOT / "Data/INI/CommandSet_Turkey.ini").write_bytes(cs_new)
    strings_tree = ROOT / "Data/English/FactionExpansion_PhaseF_Strings.txt"
    if strings_tree.parent.is_dir():
        strings_tree.write_bytes(str_new)
    else:
        strings_tree.parent.mkdir(parents=True, exist_ok=True)
        strings_tree.write_bytes(str_new)

    verify = (
        "SPECTER TURKEY ELITE MAROON BERETS CLEAN DELETE+REBUILD - VERIFY REPORT\n"
        "=======================================================================\n"
        "VERDICT: PASS\n"
        "Method: DELETE prior Turkey_EliteMaroonBerets.ini, INSERT USA NavySeal Assault clone\n"
        f"Donor: USA {DONOR_OBJ} (validated US_NavySeal / Spec_SF_Ind_A W3D)\n"
        "Old Iraq-art leftover content: NOT reused\n"
        f"Removed entries: {len(old_hits)}\n"
        f"Final Object={TURKEY_OBJ} Side=Turkey CommandSet={TURKEY_CS}\n"
        f"DisplayName={DISPLAY_TEXT} (key {DISPLAY_KEY})\n"
        "Modules: Object/Draw/WeaponSet/Armor/Locomotor/Behavior/Effects\n"
        "Prior Turkey_Airborne + Turkey_SpecialForces fixes: PRESERVED\n"
        "Turkey integrity hard gate: PASS\n"
        f"Turkey integrity soft-warns (pre-existing outside MaroonBerets): {len(post_warns)}\n"
        "INI/W3D/Weapon/Armor validation: PASS\n"
        f"\n{TURKEY_OBJ}.ini SHA256: {unit_sha}\n"
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
        f"DisplayName={DISPLAY_TEXT}\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER TURKEY ELITE MAROON BERETS CLEAN DELETE+REBUILD\n"
        "======================================================\n\n"
        "Broken Turkey_EliteMaroonBerets.ini deleted from _SPEC_DATA_ONE.big.\n"
        "Rebuilt from validated USA Navy Seals Assault. Side=Turkey.\n"
        f"CommandSet={TURKEY_CS}. DisplayName={DISPLAY_TEXT}.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "TURKEY_INTEGRITY_WARNINGS.txt",
        ):
            shutil.copy2(OUT / name, final_dir / name)
        shutil.copy2(OUT / f"{TURKEY_OBJ}.ini", final_dir / f"{TURKEY_OBJ}.ini")

    zip_path = OUT / "_SPEC_DATA_ONE_TURKEY_MAROONBERETS_CLEAN_REBUILD.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "TURKEY_INTEGRITY_WARNINGS.txt",
            f"{TURKEY_OBJ}.ini",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"{TURKEY_OBJ}.ini SHA256={unit_sha}\n"
        f"_SPEC_DATA_ONE_TURKEY_MAROONBERETS_CLEAN_REBUILD.zip SHA256={zip_sha}\n",
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
