#!/usr/bin/env python3
"""Hard-crash fix for Turkey_WeaponObjects (EXCEPTION_ACCESS_VIOLATION @ NULL).

Root causes addressed:
1. Corrupted Turkey_9M14_MissileObject Draw (bare token J2mmGrad / no Model=)
2. Weapon 9M14_AT-3A still pointed at Iraq 9M14_MissileObject with missing UVRockBug_m
3. Turkey unit weapon chains referencing projectiles with missing W3D models
4. BV parent / special-power objects lacking a valid Model=

Workflow:
- DELETE Turkey_WeaponObjects.ini; INSERT crash-safe rebuild
- Replace Turkey_9M14 from Iraq donor with validated ART model
- Retarget Weapon 9M14_AT-3A -> Turkey_9M14_MissileObject
- Remap missing W3D on all projectiles used by Turkey aircraft/vehicles
- Byte-match extract; full Turkey integrity; pack ZIP
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
    / "SPECTER_SPEC_DATA_ONE_TURKEY_WEAPONOBJECTS_CLEAN_REBUILD"
    / "_SPEC_DATA_ONE.big"
)
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_TURKEY_WEAPONOBJECTS_CRASH_FIXED"
TREE = ROOT / "Data/INI/Object/Specter/Turkey Armed Forces/Turkey_WeaponObjects.ini"
NEW_PATH = r"Data\INI\Object\Specter\Turkey Armed Forces\Turkey_WeaponObjects.ini"
WEAPON_INI = r"Data\INI\Weapon.ini"
IRAQ_WO = r"Data\INI\Object\Specter\Iraq Army\Iraq_WeaponObjects.ini"

MODEL_REMAP = {
    "AVTankShel": "Irq_255mm_Round",
    "SCUD_M-IRAQ": "Irq_R11_M",
    "Turkey_Shaheed": "Irq_Quds5",
    "Turkey_Sarab7_M": "Iraq_Sarab7_M",
    "Turkey_Alhusain_W": "Iraq_Alhusain_W",
    "ExMsslTm": "US_FGM114",
    "EXStinger01": "US_Stinger",
    "AVRaptor_M": "AIM-120",
    "UVRockBug_m": "122mmGrad",
    "NVMBuggy_m": "122mmGrad",
    "PMMoab": "US_GBU43B",
    "Mob_Botl": "BOMBCELL",
    "J2mmGrad": "122mmGrad",  # corrupted leftover token
}


def is_turkey_wo(name: str) -> bool:
    ln = name.lower().replace("/", "\\")
    return "turkey" in ln and "weaponobjects.ini" in ln and ln.endswith(".ini")


def is_turkey_object_ini(name: str) -> bool:
    n = name.replace("/", "\\")
    return "Turkey Armed Forces" in n and n.lower().endswith(".ini")


def extract_object(text: str, object_name: str) -> str:
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Object\s+(\S+)", text)]
    for i, (start, name) in enumerate(starts):
        if name == object_name:
            end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
            return text[start:end]
    raise SystemExit(f"missing Object {object_name}")


def extract_objects(text: str) -> list[tuple[str, str]]:
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Object\s+(\S+)", text)]
    out = []
    for i, (start, name) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        out.append((name, text[start:end]))
    return out


def remap_models(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    out = text
    for bad, good in MODEL_REMAP.items():
        pattern = rf"(?m)^(\s*Model\s*=\s*){re.escape(bad)}(\s*(?:;.*)?)$"
        if re.search(pattern, out):
            # \g<1> required: \1 + 122mmGrad is parsed as octal \112 -> 'J'
            out, n = re.subn(pattern, rf"\g<1>{good}\g<2>", out)
            if n:
                notes.append(f"{bad}->{good}x{n}" if n > 1 else f"{bad}->{good}")
    return out, notes


def fix_clientupdate_stray_end(text: str) -> tuple[str, int]:
    new, n = re.subn(
        r"(?m)^(\s*ClientUpdate\s*=\s*\S+[^\n]*\n)\s*End\s*\n",
        r"\1",
        text,
    )
    return new, n


def fix_bare_model_tokens(text: str) -> tuple[str, int]:
    """Repair corrupted Draw lines like bare 'J2mmGrad' into Model = 122mmGrad."""
    lines = text.splitlines()
    out: list[str] = []
    fixed = 0
    in_draw_state = False
    for line in lines:
        code = line.split(";", 1)[0]
        if re.match(r"^\s*(DefaultConditionState|ConditionState)\b", code):
            in_draw_state = True
            out.append(line)
            continue
        if in_draw_state and re.match(r"^\s*End\s*$", code):
            in_draw_state = False
            out.append(line)
            continue
        # Zero-indent or indented bare token (corruption / bad re.sub backref)
        if in_draw_state and re.match(r"^\s*[A-Za-z][A-Za-z0-9_\-]*\s*$", code):
            tok = code.strip()
            if tok not in ("End", "DefaultConditionState", "ConditionState"):
                good = MODEL_REMAP.get(tok, "122mmGrad" if tok == "J2mmGrad" else tok)
                if tok == "J2mmGrad":
                    good = "122mmGrad"
                indent = re.match(r"^(\s*)", line).group(1) or "      "
                out.append(f"{indent}Model = {good}")
                fixed += 1
                continue
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") or text else "\n"), fixed


def build_turkey_9m14_from_iraq(iraq_block: str) -> str:
    text = iraq_block.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(
        r"(?m)^Object\s+9M14_MissileObject\s*$",
        "Object Turkey_9M14_MissileObject",
        text,
        count=1,
    )
    # Ensure Side=Turkey
    if re.search(r"(?m)^\s*Side\s*=", text):
        text = re.sub(r"(?m)^(\s*Side\s*=\s*)\S+\s*$", r"\1Turkey", text, count=1)
    else:
        text = re.sub(
            r"(?m)^(  EditorSorting\s*=)",
            "  Side = Turkey\n\\1",
            text,
            count=1,
        )
    text = text.replace("Model = UVRockBug_m", "Model = 122mmGrad")
    text = text.replace("Model= UVRockBug_m", "Model = 122mmGrad")
    text, _ = remap_models(text)
    text, _ = turkey_batch.sanitize_ascii(text)
    header = (
        "; SPECTER CRASH FIX - Turkey_9M14_MissileObject\n"
        "; Replaced corrupted Draw (bare model token) with Iraq 9M14 donor + 122mmGrad W3D\n"
    )
    return header + text if not text.lstrip().startswith(";") else text


def ensure_draw_model(block: str, model: str) -> str:
    if re.search(r"(?m)^\s*Model\s*=\s*(?!None\b)\S+", block):
        return block
    draw = (
        "  ; *** ART Parameters ***\n"
        "  Draw = W3DModelDraw ModuleTag_DrawCrashFix\n"
        "    OkToChangeModelColor = Yes\n"
        "    DefaultConditionState\n"
        f"      Model = {model}\n"
        "    End\n"
        "  End\n\n"
    )
    # Insert after Object line
    return re.sub(r"(?m)^(Object\s+\S+\s*\n)", r"\1" + draw, block, count=1)


def fix_bv_parent_models(text: str) -> tuple[str, int]:
    """Give BV parent projectiles a real model from first Turkey variation."""
    objs = dict(extract_objects(text))
    fixed = 0
    for name, block in list(objs.items()):
        m = re.search(r"(?m)^\s*BuildVariations\s*=\s*(.+)$", block)
        if not m:
            continue
        vals = m.group(1).split(";")[0].split()
        turkey_vals = [v for v in vals if v.startswith("Turkey_")]
        if not turkey_vals:
            continue
        only_none = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", block)) <= {"None", "NONE"} or not re.search(
            r"(?m)^\s*Model\s*=", block
        )
        if not only_none:
            continue
        donor_name = turkey_vals[0]
        if donor_name not in objs:
            continue
        donor_models = [
            x
            for x in re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", objs[donor_name])
            if x not in ("None", "NONE")
        ]
        if not donor_models:
            continue
        model = donor_models[0]
        # Use \g<1> — plain \1 before digits (e.g. 122mmGrad) becomes octal \112 -> 'J'
        new_block, n = re.subn(
            r"(?m)^(\s*Model\s*=\s*)(?:None|NONE)\s*$",
            rf"\g<1>{model}",
            block,
            count=1,
        )
        if n == 0:
            new_block = ensure_draw_model(block, model)
        objs[name] = new_block
        fixed += 1

    # Reassemble in original order
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Object\s+(\S+)", text)]
    if not starts:
        return text, 0
    prefix = text[: starts[0][0]]
    parts = [prefix]
    for i, (_, name) in enumerate(starts):
        parts.append(objs[name])
    return "".join(parts), fixed


def rebuild_turkey_wo(raw: bytes, iraq_raw: bytes) -> tuple[str, dict]:
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    iraq = iraq_raw.decode("utf-8", "replace")
    stats: dict = {
        "bare_tokens_fixed": 0,
        "bv_parents_fixed": 0,
        "nine_m14_replaced": False,
        "kh22_draw_added": False,
        "model_remaps": [],
    }

    text, stats["bare_tokens_fixed"] = fix_bare_model_tokens(text)
    text, n_cu = fix_clientupdate_stray_end(text)
    stats["clientupdate_ends_removed"] = n_cu
    text, remaps = remap_models(text)
    stats["model_remaps"] = remaps

    # Replace Turkey_9M14 entirely from Iraq donor.
    iraq_9m14 = extract_object(iraq, "9M14_MissileObject")
    new_9m14 = build_turkey_9m14_from_iraq(iraq_9m14)
    objs = extract_objects(text)
    rebuilt_objs: list[tuple[str, str]] = []
    for name, block in objs:
        if name == "Turkey_9M14_MissileObject":
            rebuilt_objs.append((name, new_9m14))
            stats["nine_m14_replaced"] = True
        elif name == "Turkey_KH22B_SpecialPower":
            # Add Draw using KH-22B model used by sibling cruise missile object.
            nb = ensure_draw_model(block, "KH-22B")
            if nb != block:
                stats["kh22_draw_added"] = True
            rebuilt_objs.append((name, nb))
        else:
            rebuilt_objs.append((name, block))
    if not stats["nine_m14_replaced"]:
        raise SystemExit("Turkey_9M14_MissileObject missing from WO file")

    # Prefix comments
    m0 = re.search(r"(?m)^Object\s+\S+", text)
    prefix = text[: m0.start()] if m0 else ""
    body = "".join(b for _, b in rebuilt_objs)
    text = prefix + body
    text, stats["bv_parents_fixed"] = fix_bv_parent_models(text)
    text, _ = remap_models(text)  # again after inserts
    text, more_bare = fix_bare_model_tokens(text)
    stats["bare_tokens_fixed"] += more_bare

    # Strip old headers; write crash-fix header
    m = re.search(r"(?m)^Object\s+\S+", text)
    body = text[m.start() :] if m else text
    header = (
        "; SPECTER CRASH FIX - Turkey_WeaponObjects\n"
        "; EXCEPTION_ACCESS_VIOLATION @ NULL repair\n"
        "; - Replaced corrupted Turkey_9M14_MissileObject (Iraq donor + 122mmGrad)\n"
        "; - Retarget Weapon 9M14_AT-3A ProjectileObject -> Turkey_9M14_MissileObject\n"
        "; - Remapped missing W3D on Turkey weapon projectile chains\n"
        "; - Added Draw for Turkey_KH22B_SpecialPower; fixed BV parent models\n\n"
    )
    cleaned = header + body
    cleaned, _ = turkey_batch.sanitize_ascii(cleaned)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    if not cleaned.endswith("\n"):
        cleaned += "\n"
    stats["objects"] = len(re.findall(r"(?m)^Object\s+", cleaned))
    return cleaned, stats


def patch_weapon_9m14(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    def repl(m: re.Match[str]) -> str:
        block = m.group(0)
        block2, n = re.subn(
            r"(?m)^(\s*ProjectileObject\s*=\s*)9M14_MissileObject\s*$",
            r"\1Turkey_9M14_MissileObject",
            block,
            count=1,
        )
        if n != 1:
            raise SystemExit("9M14_AT-3A ProjectileObject retarget failed")
        return block2

    text2, n = re.subn(
        r"(?ms)^Weapon\s+9M14_AT-3A\s*$.*?(?=^Weapon\s|\Z)",
        repl,
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("Weapon 9M14_AT-3A missing")
    return text2


def remap_file_models(text: str) -> tuple[str, list[str]]:
    return remap_models(text)


def catalog(entries):
    cats: dict[str, set[str]] = defaultdict(set)
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("utf-8", "replace")
        cats["Object"].update(re.findall(r"(?m)^Object\s+(?![=])(\S+)", t))
        cats["CommandSet"].update(re.findall(r"(?m)^CommandSet\s+(\S+)", t))
        cats["Weapon"].update(re.findall(r"(?m)^Weapon\s+(\S+)", t))
        cats["Upgrade"].update(re.findall(r"(?m)^Upgrade\s+(\S+)", t))
        cats["Armor"].update(re.findall(r"(?m)^Armor\s+(\S+)", t))
        cats["Locomotor"].update(re.findall(r"(?m)^Locomotor\s+(\S+)", t))
        cats["MappedImage"].update(re.findall(r"(?m)^MappedImage\s+(\S+)", t))
        cats["OCL"].update(re.findall(r"(?m)^ObjectCreationList\s+(\S+)", t))
        cats["FXList"].update(re.findall(r"(?m)^FXList\s+(\S+)", t))
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
        (re.compile(r"^\s*ConditionState\s*$"), "ConditionState"),
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
    return fails


def validate_wo(text: str, entries, art_entries, label: str) -> list[str]:
    fails: list[str] = []
    cats = catalog(entries)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }
    if any(ord(c) > 127 for c in text):
        fails.append(f"{label}: non-ASCII")
    if not text.startswith("; SPECTER CRASH FIX - Turkey_WeaponObjects"):
        fails.append(f"{label}: missing crash-fix header")
    objs = re.findall(r"(?m)^Object\s+(\S+)", text)
    if len(objs) != len(set(objs)):
        fails.append(f"{label}: duplicate Object names")
    if "Turkey_9M14_MissileObject" not in objs:
        fails.append(f"{label}: missing Turkey_9M14_MissileObject")
    fails.extend(parse_stack_fails(text, label))

    # No bare model tokens
    for i, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0]
        if re.match(r"^[A-Za-z][A-Za-z0-9_\-]*\s*$", code.strip()) and code.strip() in (
            "J2mmGrad",
            "UVRockBug_m",
        ):
            fails.append(f"{label}: bare corrupt token @{i} {code.strip()}")

    nine = extract_object(text, "Turkey_9M14_MissileObject")
    if not re.search(r"(?m)^\s*Model\s*=\s*122mmGrad\s*$", nine):
        fails.append(f"{label}: Turkey_9M14 missing Model=122mmGrad")
    if "J2mmGrad" in nine:
        fails.append(f"{label}: Turkey_9M14 still has J2mmGrad")

    for model in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)):
        if model in ("None", "NONE", "NULL"):
            continue
        if model.lower() not in stems:
            fails.append(f"{label}: missing W3D Model={model}")

    # Weapon retarget present
    wjoin = "\n".join(
        b.decode("utf-8", "replace")
        for n, b in entries
        if n.replace("/", "\\").endswith(r"Data\INI\Weapon.ini")
    )
    if not re.search(
        r"(?ms)^Weapon\s+9M14_AT-3A\s*$.*?^\s*ProjectileObject\s*=\s*Turkey_9M14_MissileObject\s*$",
        wjoin,
    ):
        fails.append(f"{label}: Weapon 9M14_AT-3A not retargeted")
    return fails


def turkey_weapon_chain_scan(entries, art_entries) -> list[str]:
    """Every Turkey unit Weapon template projectile must resolve with valid W3D."""
    fails: list[str] = []
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }
    cats = catalog(entries)

    w2p: dict[str, list[str]] = {}
    for n, r in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = r.decode("utf-8", "replace")
        for m in re.finditer(r"(?ms)^Weapon\s+(\S+)\s*$.*?(?=^Weapon\s|\Z)", t):
            w2p[m.group(1)] = re.findall(
                r"(?m)^\s*ProjectileObject\s*=\s*(\S+)", m.group(0)
            )

    obj_models: dict[str, list[str]] = {}
    for n, r in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = r.decode("utf-8", "replace")
        for name, block in extract_objects(t):
            obj_models[name] = [
                m
                for m in re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", block)
                if m not in ("None", "NONE")
            ]

    used = set()
    for n, r in entries:
        if not is_turkey_object_ini(n):
            continue
        if "WeaponObjects" in n:
            continue
        t = r.decode("utf-8", "replace")
        for w in re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", t):
            if w in ("None", "NONE") or w == "End":
                continue
            used.add(w)

    for w in sorted(used):
        if w not in cats["Weapon"] and w not in w2p:
            # Some tokens are false positives; only fail if clearly a weapon-like name
            if re.match(r"^[0-9A-Za-z_].*", w) and w not in (
                "ExclusiveWeaponDelay",
                "InitialDelay",
            ):
                # soft: skip unknown non-projectile weapons
                continue
        for p in w2p.get(w, []):
            if p in ("None", "NONE"):
                continue
            if p not in cats["Object"]:
                fails.append(f"weapon {w}: missing ProjectileObject {p}")
                continue
            models = obj_models.get(p, [])
            for m in models:
                if m.lower() not in stems:
                    fails.append(f"weapon {w}: projectile {p} missing W3D Model={m}")
    return fails


def turkey_integrity_scan(entries, art_entries) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []
    cats = catalog(entries)
    objs = cats["Object"]

    wo_hits = [n for n, _ in entries if is_turkey_wo(n)]
    if len(wo_hits) != 1:
        fails.append(f"Turkey_WeaponObjects.ini count={len(wo_hits)}")

    for o in ("Turkey_Airborne", "Turkey_SpecialForces", "Turkey_EliteMaroonBerets", "Turkey_9M14_MissileObject"):
        if o not in objs:
            fails.append(f"missing Object {o}")

    fails.extend(turkey_weapon_chain_scan(entries, art_entries))

    for n, r in entries:
        if not is_turkey_object_ini(n):
            continue
        nn = n.replace("/", "\\")
        if "WeaponObjects" in nn or "\\Weapon" in nn or "\\Projectile" in nn:
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
        for msg in parse_stack_fails(text, bn):
            warns.append(msg)
    return fails, warns


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG: {SRC}")
    entries = base.parse_big(SRC)
    art_entries = base.parse_big(ART)
    by = {base.knorm(n): (n, r) for n, r in entries}

    old_hits = [(n, r) for n, r in entries if is_turkey_wo(n)]
    print(f"DELETE phase: {len(old_hits)} Turkey_WeaponObjects.ini")
    old_shas = {base.sha256_bytes(r) for _, r in old_hits}
    old_raw = old_hits[0][1]
    old_names = set(re.findall(r"(?m)^Object\s+(\S+)", old_raw.decode("utf-8", "replace")))
    for n, r in old_hits:
        print(f"  removing {n} sha={base.sha256_bytes(r)[:16]} size={len(r)}")

    purged = [(n, r) for n, r in entries if not is_turkey_wo(n)]
    iraq_name, iraq_raw = by[base.knorm(IRAQ_WO)]

    cleaned, stats = rebuild_turkey_wo(old_raw, iraq_raw)
    new_raw = cleaned.encode("ascii")
    if base.sha256_bytes(new_raw) in old_shas:
        raise SystemExit("hash collision with deleted WO")
    new_names = set(re.findall(r"(?m)^Object\s+(\S+)", cleaned))
    if new_names != old_names:
        raise SystemExit(
            f"object set changed missing={sorted(old_names-new_names)[:10]} extra={sorted(new_names-old_names)[:10]}"
        )
    print(
        f"NEW WO sha={base.sha256_bytes(new_raw)[:16]} size={len(new_raw)} "
        f"objs={stats['objects']} bare={stats['bare_tokens_fixed']} "
        f"9m14={stats['nine_m14_replaced']} bv_parents={stats['bv_parents_fixed']}"
    )

    # Patch Weapon.ini
    if base.knorm(WEAPON_INI) not in by:
        raise SystemExit("Weapon.ini missing")
    w_name, w_raw = by[base.knorm(WEAPON_INI)]
    w_text = patch_weapon_9m14(w_raw.decode("utf-8", "replace"))
    w_text, _ = turkey_batch.sanitize_ascii(w_text)
    w_new = w_text.encode("ascii")

    # Remap missing W3D on projectile objects used by Turkey weapon chains
    # (and Iraq 9M14 still referenced elsewhere).
    patched: dict[str, bytes] = {
        base.knorm(WEAPON_INI): w_new,
    }
    remap_notes: list[str] = []
    for name, raw in purged:
        kn = base.knorm(name)
        if kn == base.knorm(WEAPON_INI):
            continue
        if not name.lower().endswith(".ini"):
            continue
        # Remap models in weaponobject / projectile / stock weapon object files
        ln = name.lower().replace("/", "\\")
        if not any(
            k in ln
            for k in (
                "weaponobjects.ini",
                "\\projectiles\\",
                r"\object\weaponobjects.ini",
            )
        ):
            continue
        text = raw.decode("utf-8", "replace")
        fixed, notes = remap_file_models(text)
        if notes:
            fixed, _ = turkey_batch.sanitize_ascii(fixed)
            patched[kn] = fixed.encode("ascii")
            remap_notes.append(f"{Path(name.replace(chr(92), '/')).name}:{','.join(notes)}")

    rebuilt = []
    for name, raw in purged:
        kn = base.knorm(name)
        if kn in patched:
            rebuilt.append((name if kn != base.knorm(WEAPON_INI) else w_name, patched[kn]))
        else:
            rebuilt.append((name, raw))
    rebuilt.append((NEW_PATH, new_raw))

    counts: dict[str, int] = defaultdict(int)
    for n, _ in rebuilt:
        counts[base.knorm(n)] += 1
    dups = [k for k, v in counts.items() if v > 1]
    if dups:
        raise SystemExit(f"duplicate paths {dups}")

    failures = []
    failures.extend(validate_wo(cleaned, rebuilt, art_entries, "PREWRITE"))
    integ_fails, integ_warns = turkey_integrity_scan(rebuilt, art_entries)
    failures.extend(integ_fails)
    if failures:
        print("PRE-WRITE FAILED")
        for f in failures[:120]:
            print(" ", f)
        return 1
    print(f"PASS pre-write (soft-warns={len(integ_warns)} projectile-file remaps={len(remap_notes)})")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, rebuilt)
    final_entries = base.parse_big(out_big)
    final_hits = [(n, r) for n, r in final_entries if is_turkey_wo(n)]
    if len(final_hits) != 1:
        out_big.unlink(missing_ok=True)
        raise SystemExit(f"expected 1 WO entry got {len(final_hits)}")

    extract_root = OUT / "_EXTRACT_VERIFY"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    emb_name, emb = final_hits[0]
    post = []
    if emb != new_raw:
        post.append("byte mismatch WO")
    if base.sha256_bytes(emb) in old_shas:
        post.append("old hash reused")
    if b"J2mmGrad" in emb:
        post.append("J2mmGrad remains")

    rel = Path(*Path(emb_name.replace("\\", "/")).parts)
    ep = extract_root / rel
    ep.parent.mkdir(parents=True, exist_ok=True)
    ep.write_bytes(emb)
    TREE.parent.mkdir(parents=True, exist_ok=True)
    TREE.write_bytes(new_raw)

    # Also sync Weapon.ini tree if present
    tree_weapon = ROOT / "Data/INI/Weapon.ini"
    if tree_weapon.parent.is_dir():
        tree_weapon.write_bytes(w_new)

    post.extend(validate_wo(emb.decode("ascii"), final_entries, art_entries, "EXTRACT"))
    post_fails, post_warns = turkey_integrity_scan(final_entries, art_entries)
    post.extend(post_fails)
    if post:
        out_big.unlink(missing_ok=True)
        print("EXTRACT/INTEGRITY FAILED")
        for f in post[:120]:
            print(" ", f)
        return 1
    print(f"PASS extract + integrity (soft-warns={len(post_warns)})")

    old_by = {base.knorm(n): r for n, r in entries}
    new_by = {base.knorm(n): r for n, r in final_entries}
    allowed = {base.knorm(NEW_PATH), base.knorm(WEAPON_INI)} | set(patched)
    changed = [kn for kn in sorted(set(old_by) | set(new_by)) if old_by.get(kn) != new_by.get(kn)]
    unexpected = [c for c in changed if c not in allowed]
    if unexpected:
        raise SystemExit(f"unrelated paths changed: {unexpected[:20]}")
    print(f"CHANGED={len(changed)}")

    big_sha = base.sha256_file(out_big)
    big_size = out_big.stat().st_size
    unit_sha = base.sha256_bytes(new_raw)
    (OUT / "Turkey_WeaponObjects.ini").write_bytes(new_raw)
    (OUT / "TURKEY_INTEGRITY_WARNINGS.txt").write_text(
        "TURKEY INTEGRITY SOFT WARNINGS\n"
        f"count={len(post_warns)}\n\n" + "\n".join(post_warns[:500]) + "\n",
        encoding="ascii",
        errors="replace",
    )
    (OUT / "CRASH_FIX_NOTES.txt").write_text(
        "TURKEY WEAPONOBJECTS NULL CRASH FIX\n"
        "==================================\n"
        f"bare_tokens_fixed={stats['bare_tokens_fixed']}\n"
        f"turkey_9m14_replaced={stats['nine_m14_replaced']}\n"
        f"kh22_draw_added={stats['kh22_draw_added']}\n"
        f"bv_parents_fixed={stats['bv_parents_fixed']}\n"
        f"wo_model_remaps={stats['model_remaps']}\n"
        f"projectile_file_remaps={remap_notes}\n"
        "weapon_9m14_projectile=Turkey_9M14_MissileObject\n",
        encoding="ascii",
    )
    verify = (
        "SPECTER TURKEY WEAPONOBJECTS NULL CRASH FIX - VERIFY REPORT\n"
        "===========================================================\n"
        "VERDICT: PASS\n"
        "Crash: EXCEPTION_ACCESS_VIOLATION @ 00000000\n"
        "Cause: corrupted/missing projectile W3D (Turkey_9M14 / UVRockBug_m chains)\n"
        "Fix: DELETE+INSERT Turkey_WeaponObjects; retarget 9M14_AT-3A; remap W3D\n"
        f"Objects preserved: {stats['objects']}\n"
        "Turkey unit weapon->projectile W3D scan: PASS\n"
        "Extract byte-match: PASS\n"
        f"BIG SHA256: {big_sha}\n"
        f"WO SHA256: {unit_sha}\n"
        f"BIG SIZE: {big_size}\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(verify, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "DELETE+INSERT PROOF\n"
        f"removed_shas={sorted(old_shas)}\n"
        f"new_sha256={unit_sha}\n"
        "old_hash_reuse=NO\n"
        f"BIG_sha256={big_sha}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER TURKEY WEAPONOBJECTS NULL CRASH FIX\n"
        "==========================================\n\n"
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
            "CRASH_FIX_NOTES.txt",
            "Turkey_WeaponObjects.ini",
        ):
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_TURKEY_WEAPONOBJECTS_CRASH_FIXED.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "EMBED_PROOF.txt",
            "README_INSTALL.txt",
            "TURKEY_INTEGRITY_WARNINGS.txt",
            "CRASH_FIX_NOTES.txt",
            "Turkey_WeaponObjects.ini",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Turkey_WeaponObjects.ini SHA256={unit_sha}\n"
        f"_SPEC_DATA_ONE_TURKEY_WEAPONOBJECTS_CRASH_FIXED.zip SHA256={zip_sha}\n",
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
