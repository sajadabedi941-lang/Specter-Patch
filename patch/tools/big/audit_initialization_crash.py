#!/usr/bin/env python3
"""Initialization-crash audit of packed Specter DATA/ART BIGs."""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_china_heavy_aircraft as ch
import pack_uk_e7_boot_crash_fix as e7

DATA_BIG = Path("/tmp/final_global_roster/_SPEC_DATA_ONE.big")
ART_BIG = Path("/tmp/final_global_roster/_SPEC_ART_ONE.big")
OUT = Path("/workspace")

GLOBAL_TYPES = {
    "Object": r"^Object(?:Reskin)?\s+(\S+)",
    "Weapon": r"^Weapon\s+(\S+)",
    "Armor": r"^Armor\s+(\S+)",
    "Locomotor": r"^Locomotor\s+(\S+)",
    "CommandButton": r"^CommandButton\s+(\S+)",
    "CommandSet": r"^CommandSet\s+(\S+)",
    "Upgrade": r"^Upgrade\s+(\S+)",
    "Science": r"^Science\s+(\S+)",
    "SpecialPower": r"^SpecialPower\s+(\S+)",
    "ObjectCreationList": r"^ObjectCreationList\s+(\S+)",
    "FXList": r"^FXList\s+(\S+)",
    "ParticleSystem": r"^ParticleSystem(?:Template)?\s+(\S+)",
    "MappedImage": r"^MappedImage\s+(\S+)",
    "AudioEvent": r"^AudioEvent\s+(\S+)",
    "EvaEvent": r"^EvaEvent\s+(\S+)",
    "DamageFX": r"^DamageFX\s+(\S+)",
    "ExperienceLevel": r"^ExperienceLevel\s+(\S+)",
    "PlayerTemplate": r"^PlayerTemplate\s+(\S+)",
    "Road": r"^Road\s+(\S+)",
    "Bridge": r"^Bridge\s+(\S+)",
    "Weather": r"^Weather\s+(\S+)",
    "WaterTransparency": r"^WaterTransparency\s+(\S+)",
    "MultiplayerColor": r"^MultiplayerColor\s+(\S+)",
    "Rank": r"^Rank\s+(\S+)",
    "CrateData": r"^CrateData\s+(\S+)",
    "WeaponBonusSet": r"^WeaponBonusSet\s+(\S+)",
    "MusicTrack": r"^MusicTrack\s+(\S+)",
    "DialogEvent": r"^DialogEvent\s+(\S+)",
    "ControlBarScheme": r"^ControlBarScheme\s+(\S+)",
    "Animation": r"^Animation\s+(\S+)",
    "DrawGroupInfo": r"^DrawGroupInfo\s+(\S+)",
    "Video": r"^Video\s+(\S+)",
    "Campaign": r"^Campaign\s+(\S+)",
    "ChallengeGenerals": r"^ChallengeGenerals\s+(\S+)",
    "Credits": r"^Credits\s+(\S+)",
    "MultiplayerSettings": r"^MultiplayerSettings\s+(\S+)",
    "GameData": r"^GameData\s+(\S+)",
    "OnlineChatColor": r"^OnlineChatColor\s+(\S+)",
    "ShellMenuScheme": r"^ShellMenuScheme\s+(\S+)",
    "MapCache": r"^MapCache\s+(\S+)",
}

KNOWN_TOP = set(GLOBAL_TYPES) | {
    "ObjectReskin",
    "ChildObject",
    "End",
    "ParticleSystemTemplate",
    "AudioSettings",
    "MiscAudio",
    "AmbientStream",
    "Multisound",
    "Music",
    "SoundEffects",
    "Speech",
    "Video",
    "Terrain",
    "Weather",
    "Water",
    "HeaderTemplate",
    "Mouse",
    "InGameUI",
    "StaticGameLOD",
    "DynamicGameLOD",
    "Firestorm",
    "WindowTransition",
    "Benchmark",
    "ReallyLowMHz",
    "LightPulse",
    "Draw",
    "Default",
}

ASSIGNMENT_OK = re.compile(
    r"^[A-Za-z][A-Za-z0-9_]*\s*="
)
COMMENT_OR_EMPTY = re.compile(r"^(\s*;|\s*)$")
BLOCK_WORD = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)\b")

# Sage nested blocks commonly opened without `Type Name` form
NESTED_OPEN = re.compile(
    r"^(Draw|Behavior|Body|ArmorSet|WeaponSet|DefaultConditionState|"
    r"ConditionState|TransitionState|Prerequisites|UnitSpecificSounds|"
    r"Turret|WeaponSlot|Alt|OCL|ParticleSys|"
    r"Attack|Fire|ClientUpdate|LocomotorSet)\b"
)


def load_big(path: Path):
    entries, raw = ch.read_big(path)
    files = []
    for name, off, size in entries:
        files.append((name.replace("/", "\\"), raw[off : off + size]))
    return files


def is_ini(name: str) -> bool:
    return name.lower().endswith(".ini")


def decode_ini(blob: bytes) -> tuple[str, list[str]]:
    flags = []
    if blob.startswith(b"\xef\xbb\xbf"):
        flags.append("BOM")
        blob = blob[3:]
    if b"\r" in blob:
        flags.append("CRLF")
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError:
        text = blob.decode("latin1")
        flags.append("LATIN1")
    if re.search(r"[^\x09\x0a\x0d\x20-\x7e]", text):
        flags.append("NON_ASCII")
    return text, flags


def iter_top_tokens(text: str):
    depth = 0
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith(";"):
            continue
        if s == "End" or s == "END":
            depth = max(0, depth - 1)
            continue
        if depth == 0:
            m = BLOCK_WORD.match(s)
            if m:
                yield i, m.group(1), s
        # crude depth
        if NESTED_OPEN.match(s) or (BLOCK_WORD.match(s) and "=" not in s.split(";", 1)[0]):
            if not s.startswith("Locomotor =") and not s.startswith("CommandSet =") and not s.startswith("Scale ="):
                if s != "End":
                    depth += 1


def extract_defs(text: str, kind: str, pat: str):
    cre = re.compile(pat, re.M)
    out = []
    for m in cre.finditer(text):
        out.append((m.group(1), m.start(), m.start()))
    return out


def w3d_has_anim(blob: bytes) -> bool:
    # W3D_CHUNK_ANIMATION = 0x00000200, COMPRESSED = 0x00000280, MORPH = 0x000002C0
    pos = 0
    n = len(blob)
    while pos + 8 <= n:
        ctype, csize = struct.unpack_from("<II", blob, pos)
        if ctype in (0x00000200, 0x00000280, 0x000002C0, 0x00000250):
            return True
        pos += 8 + csize
        if csize > n:
            break
    return b"ANIM" in blob[: min(len(blob), 4096)]


def w3d_textures(blob: bytes) -> list[str]:
    names = []
    # naive ASCII texture filename harvest
    for m in re.finditer(rb"([\w\-\. ]+\.(?:tga|dds|TGA|DDS))\x00", blob):
        names.append(m.group(1).decode("latin1"))
    return names


def main() -> int:
    print("Loading DATA", DATA_BIG)
    data_files = load_big(DATA_BIG)
    print("DATA files", len(data_files))
    print("Loading ART", ART_BIG)
    art_files = load_big(ART_BIG)
    print("ART files", len(art_files))

    art_leaf = {}
    w3d_blobs = {}
    tex_leaf = set()
    for name, blob in art_files:
        leaf = name.split("\\")[-1]
        low = leaf.lower()
        art_leaf[low] = name
        if low.endswith(".w3d"):
            w3d_blobs[low[:-4]] = blob
        if low.endswith((".tga", ".dds")):
            tex_leaf.add(low)

    ini_files = [(n, b) for n, b in data_files if is_ini(n)]
    # BIG index order == pack order == likely load order
    parsed = []
    parser_rows = []
    defs = defaultdict(lambda: defaultdict(list))  # type -> name -> [(file, line)]
    unknown_top = []
    end_errors = []
    encoding_flags = []
    md_in_ini = []
    truncated = []

    for name, blob in ini_files:
        text, flags = decode_ini(blob)
        rel = name
        if flags:
            encoding_flags.append((rel, flags))
        if "```" in text or text.lstrip().startswith("# "):
            md_in_ini.append(rel)
        if blob and not blob.endswith(b"\n") and b"Object " in blob[:200]:
            truncated.append(rel)
        errs = e7.balanced_end(text, rel)
        if errs:
            end_errors.extend(errs)
        status = "PASS"
        reasons = []
        if "CRLF" in flags:
            reasons.append("CRLF")
        if "BOM" in flags:
            reasons.append("BOM")
        if errs:
            reasons.append("END_BALANCE")
            status = "FAIL"
        for i, tok, s in iter_top_tokens(text):
            if tok in ("End", "END"):
                continue
            if ASSIGNMENT_OK.match(s):
                continue
            if tok not in KNOWN_TOP and tok not in GLOBAL_TYPES:
                # allow nested-looking leftovers
                if tok[0].isupper() and "=" not in s:
                    unknown_top.append((rel, i, tok, s[:120]))
                    reasons.append(f"UNKNOWN:{tok}")
                    status = "FAIL"
        for kind, pat in GLOBAL_TYPES.items():
            for nm, start, _ in extract_defs(text, kind, pat):
                line = text[:start].count("\n") + 1
                defs[kind][nm].append((rel, line))
        parser_rows.append((rel, status, ";".join(reasons) if reasons else "ok", len(text)))
        parsed.append((name, text))

    # duplicates
    dup_rows = []
    for kind, names in defs.items():
        for nm, locs in names.items():
            if len(locs) > 1:
                files = [a for a, _ in locs]
                # same file twice is always unsafe
                same_file = len(set(files)) == 1
                overlayish = any(
                    "weapon_" in f.lower()
                    or "commandbutton_" in f.lower()
                    or "commandset_" in f.lower()
                    or "z" + kind.lower() in f.lower()
                    or "portrait" in f.lower()
                    or "mappedimages" in f.lower()
                    for f in files
                )
                unsafe = True
                action = "REMOVE later duplicate overlay file or rename"
                if kind == "MappedImage" and overlayish:
                    action = "STRIP duplicate z* portrait INI; keep HandCreatedMappedImages.ini"
                if kind in ("Weapon", "CommandButton", "CommandSet", "SpecialPower", "Object"):
                    action = "STRIP later overlay INI that redefines this name"
                dup_rows.append(
                    {
                        "name": nm,
                        "type": kind,
                        "locs": locs,
                        "after414": overlayish,
                        "unsafe": unsafe,
                        "action": action,
                    }
                )

    # CommandButton load-order simulation
    seen_buttons = set()
    cs_order_errs = []
    slot_errs = []
    for name, text in parsed:
        # register buttons as we go
        pos = 0
        tokens = []
        for m in re.finditer(r"^(CommandButton|CommandSet) (\S+)\s*$", text, re.M):
            tokens.append((m.start(), m.group(1), m.group(2)))
        for _, kind, nm in tokens:
            if kind == "CommandButton":
                seen_buttons.add(nm)
            else:
                # grab block
                block = ""
                m = re.search(
                    rf"^CommandSet {re.escape(nm)}\s*\n(.*?)(?:^End\s*$)",
                    text,
                    re.M | re.S,
                )
                if m:
                    block = m.group(1)
                slots = []
                for line in block.splitlines():
                    sm = re.match(r"^\s*(\d+)\s*=\s*(\S+)", line)
                    if not sm:
                        continue
                    slot, btn = int(sm.group(1)), sm.group(2)
                    slots.append(slot)
                    if slot <= 0:
                        slot_errs.append((name, nm, f"slot {slot}"))
                    if slot > 18:
                        slot_errs.append((name, nm, f"slot {slot} > 18"))
                    if btn not in seen_buttons and btn != "None":
                        cs_order_errs.append((name, nm, btn, "button not yet declared"))
                if len(slots) != len(set(slots)):
                    slot_errs.append((name, nm, f"dup slots {slots}"))

    # objects / weapons / models
    obj_pat = re.compile(r"^Object(?:Reskin)?\s+(\S+)", re.M)
    objects = {}
    for name, text in parsed:
        for m in obj_pat.finditer(text):
            obj = m.group(1)
            start = m.start()
            nxt = obj_pat.search(text, m.end())
            end = nxt.start() if nxt else len(text)
            objects[obj] = (name, text[start:end])

    weapons = {}
    wpat = re.compile(r"^Weapon\s+(\S+)", re.M)
    for name, text in parsed:
        for m in wpat.finditer(text):
            wn = m.group(1)
            start = m.start()
            nxt = wpat.search(text, m.end())
            end = nxt.start() if nxt else len(text)
            weapons[wn] = (name, text[start:end])

    locos = set(defs["Locomotor"])
    armors = set(defs["Armor"])
    commandsets = set(defs["CommandSet"])
    fxlists = set(defs["FXList"])
    ocls = set(defs["ObjectCreationList"])
    specials = set(defs["SpecialPower"])
    upgrades = set(defs["Upgrade"])
    sciences = set(defs["Science"])
    mapped = set(defs["MappedImage"])
    particles = set(defs["ParticleSystem"])

    missing_wpn = []
    missing_proj = []
    missing_loco = []
    missing_armor = []
    missing_cs = []
    missing_w3d = []
    anim_no_anim = []
    radar_kindof = []
    moduletag_dups = []
    missing_fx = []
    missing_ocl = []
    missing_sp = []
    missing_up = []
    missing_sci = []
    missing_mi = []
    missing_tex = []
    weapon_field_errs = []
    heli_vs_jet = []

    model_re = re.compile(r"^\s*Model\s*=\s*(\S+)", re.M)
    anim_re = re.compile(r"^\s*Animation\s*=\s*(\S+)", re.M)
    wpn_slot_re = re.compile(r"Weapon\s*=\s*(\S+)", re.M)
    loco_re = re.compile(r"Locomotor\s*=\s*\S+\s+(\S+)", re.M)
    armor_re = re.compile(r"^\s*Armor\s*=\s*(\S+)", re.M)
    cs_re = re.compile(r"^\s*CommandSet\s*=\s*(\S+)", re.M)
    fx_re = re.compile(r"(?:FX|FireFX|ProjectileDetonationFX|VeterancyFireFX)\s*=\s*(\S+)", re.M)
    ocl_re = re.compile(r"(?:OCL|CreationList|OCLInitialDeath|OCLSecondary)\s*=\s*(\S+)", re.M)
    sp_re = re.compile(r"SpecialPower(?:Template)?\s*=\s*(\S+)", re.M)
    up_re = re.compile(r"(?:TriggeredBy|RequiresUpgrade|UpgradeCameo\d+)\s*=\s*(\S+)", re.M)
    sci_re = re.compile(r"Science(?:Required)?\s*=\s*(\S+)", re.M)
    tag_re = re.compile(r"ModuleTag_(\S+)", re.M)
    kind_re = re.compile(r"KindOf\s*=\s*(.+)", re.M)
    proj_re = re.compile(r"ProjectileObject\s*=\s*(\S+)", re.M)
    btn_img_re = re.compile(r"ButtonImage\s*=\s*(\S+)", re.M)

    ENGINE_FX = {"None", "NONE"}
    ENGINE_OCL = {"None", "NONE", "FINAL", "INITIAL", "MIDPOINT"}
    ENGINE_LOCO = {"None", "NONE"}
    ENGINE_OBJ = {"None", "NONE"}

    for obj, (fn, block) in objects.items():
        models = model_re.findall(block)
        anims = anim_re.findall(block)
        for md in models:
            key = md.lower()
            if key not in w3d_blobs and (key + ".w3d") not in art_leaf:
                missing_w3d.append((obj, fn, md))
            else:
                blob = w3d_blobs.get(key)
                if blob is None:
                    # try exact
                    for k, b in w3d_blobs.items():
                        if k.lower() == key:
                            blob = b
                            break
                if blob:
                    for tex in w3d_textures(blob):
                        if tex.lower() not in tex_leaf:
                            missing_tex.append((obj, md, tex))
                    if anims and not w3d_has_anim(blob):
                        anim_no_anim.append((obj, fn, md, anims[:3]))
        km = kind_re.search(block)
        if km and re.search(r"\bRADAR\b", km.group(1)):
            radar_kindof.append((obj, fn, km.group(1).strip()))
        tags = tag_re.findall(block)
        if len(tags) != len(set(tags)):
            seen = set()
            dups = []
            for t in tags:
                if t in seen:
                    dups.append(t)
                seen.add(t)
            moduletag_dups.append((obj, fn, dups))
        for wpn in wpn_slot_re.findall(block):
            if wpn not in weapons and wpn not in ENGINE_OBJ:
                missing_wpn.append((obj, fn, wpn))
        for loco in loco_re.findall(block):
            if loco not in locos and loco not in ENGINE_LOCO:
                missing_loco.append((obj, fn, loco))
        for ar in armor_re.findall(block):
            if ar not in armors and ar not in ENGINE_OBJ:
                missing_armor.append((obj, fn, ar))
        for cs in cs_re.findall(block):
            if cs not in commandsets and cs not in ENGINE_OBJ:
                missing_cs.append((obj, fn, cs))
        # helicopter vs jet
        is_heli = "HelicopterAIUpdate" in block or "KindOf" in block and "HELICOPTER" in (km.group(1) if km else "")
        is_jet = "JetAIUpdate" in block
        if is_heli and is_jet:
            heli_vs_jet.append((obj, fn, "both HelicopterAI and JetAI"))
        if km and "AIRCRAFT" in km.group(1) and "HelicopterAIUpdate" in block and "JetAIUpdate" not in block:
            pass
        if km and "AIRCRAFT" in km.group(1) and "HELICOPTER" in km.group(1):
            heli_vs_jet.append((obj, fn, "KindOf AIRCRAFT+HELICOPTER"))

    for wn, (fn, block) in weapons.items():
        pm = proj_re.search(block)
        if pm:
            proj = pm.group(1)
            if proj not in objects and proj not in ENGINE_OBJ:
                missing_proj.append((wn, fn, proj))
        for fx in fx_re.findall(block):
            if fx not in fxlists and fx not in ENGINE_FX:
                missing_fx.append((f"Weapon:{wn}", fn, fx))
        for key in (
            "PrimaryDamage",
            "AttackRange",
            "WeaponSpeed",
        ):
            if re.search(rf"{key}\s*=", block):
                vm = re.search(rf"{key}\s*=\s*(\S+)", block)
                if vm and not re.match(r"^-?\d", vm.group(1)):
                    if vm.group(1) not in ("Yes", "No"):
                        weapon_field_errs.append((wn, key, vm.group(1)))

    # CommandButton object/image
    missing_btn_obj = []
    missing_btn_img = []
    btn_pat = re.compile(r"^CommandButton (\S+)\s*$", re.M)
    for name, text in parsed:
        for m in btn_pat.finditer(text):
            btn = m.group(1)
            nxt = text.find("\nEnd", m.end())
            block = text[m.end() : nxt if nxt > 0 else m.end() + 500]
            if "UNIT_BUILD" in block:
                om = re.search(r"Object\s+=\s+(\S+)", block)
                if om and om.group(1) not in objects:
                    missing_btn_obj.append((btn, name, om.group(1)))
            im = re.search(r"ButtonImage\s+=\s+(\S+)", block)
            if im and im.group(1) not in mapped and im.group(1) not in ENGINE_OBJ:
                missing_btn_img.append((btn, name, im.group(1)))

    # summarize duplicate overlay files
    dup_files = defaultdict(lambda: defaultdict(int))
    for row in dup_rows:
        files = [f for f, _ in row["locs"]]
        for f in files[1:]:
            dup_files[row["type"]][f] += 1

    def write(path: Path, text: str):
        path.write_text(text, encoding="utf-8")
        print("wrote", path, "bytes", path.stat().st_size)

    # INI_PARSER_AUDIT
    fail_n = sum(1 for _, s, *_ in parser_rows if s == "FAIL")
    lines = [
        "# INI_PARSER_AUDIT.md",
        "",
        f"Packed DATA: `{DATA_BIG}`",
        f"INI files: {len(parser_rows)}",
        f"PASS: {len(parser_rows) - fail_n}",
        f"FAIL: {fail_n}",
        "",
        "| FILE | STATUS | NOTES | BYTES |",
        "|---|---|---|---|",
    ]
    for rel, status, notes, n in parser_rows:
        lines.append(f"| `{rel}` | {status} | {notes} | {n} |")
    if unknown_top:
        lines += ["", "## Unknown top-level tokens", ""]
        for rel, i, tok, s in unknown_top[:200]:
            lines.append(f"- `{rel}:{i}` `{tok}` :: `{s}`")
    if end_errors:
        lines += ["", "## End-balance errors", ""]
        for e in end_errors[:200]:
            lines.append(f"- {e}")
    write(OUT / "INI_PARSER_AUDIT.md", "\n".join(lines) + "\n")

    # DUPLICATE_DEFINITION_AUDIT
    lines = [
        "# DUPLICATE_DEFINITION_AUDIT.md",
        "",
        f"Duplicate named globals: **{len(dup_rows)}**",
        "",
    ]
    by_type = defaultdict(int)
    for row in dup_rows:
        by_type[row["type"]] += 1
    for k, v in sorted(by_type.items(), key=lambda kv: -kv[1]):
        lines.append(f"- {k}: {v}")
    lines += ["", "---", ""]
    for row in dup_rows:
        locs = row["locs"]
        lines += [
            f"NAME: {row['name']}",
            f"TYPE: {row['type']}",
            f"FILE 1: {locs[0][0]}:{locs[0][1]}",
            f"FILE 2: {locs[1][0]}:{locs[1][1]}",
            f"INTRODUCED AFTER #414: {'YES-CANDIDATE' if row['after414'] else 'UNKNOWN'}",
            f"SAFE OVERRIDE / UNSAFE DUPLICATE: {'UNSAFE DUPLICATE' if row['unsafe'] else 'SAFE OVERRIDE'}",
            f"ACTION: {row['action']}",
            "",
        ]
    lines += ["", "## Overlay files that re-declare names", ""]
    for kind, files in sorted(dup_files.items()):
        lines.append(f"### {kind}")
        for f, n in sorted(files.items(), key=lambda kv: -kv[1]):
            lines.append(f"- `{f}` x{n}")
        lines.append("")
    write(OUT / "DUPLICATE_DEFINITION_AUDIT.md", "\n".join(lines) + "\n")

    # MODULETAG
    lines = ["# MODULETAG_AUDIT.md", "", f"Objects with duplicate ModuleTags: {len(moduletag_dups)}", ""]
    for obj, fn, dups in moduletag_dups:
        lines.append(f"- `{obj}` in `{fn}` duplicates: {dups}")
    write(OUT / "MODULETAG_AUDIT.md", "\n".join(lines) + "\n")

    # WEAPON
    lines = [
        "# WEAPON_REFERENCE_AUDIT.md",
        "",
        f"Weapons defined: {len(weapons)}",
        f"Aircraft/object missing weapon: {len(missing_wpn)}",
        f"Weapon missing projectile: {len(missing_proj)}",
        f"Weapon field errors: {len(weapon_field_errs)}",
        "",
        "## Missing weapons on objects",
    ]
    for a, b, c in missing_wpn[:300]:
        lines.append(f"- {a} ({b}) -> `{c}`")
    lines += ["", "## Missing ProjectileObject"]
    for a, b, c in missing_proj[:300]:
        lines.append(f"- {a} ({b}) -> `{c}`")
    lines += ["", "## Field errors"]
    for a, b, c in weapon_field_errs[:100]:
        lines.append(f"- {a} {b}={c}")
    write(OUT / "WEAPON_REFERENCE_AUDIT.md", "\n".join(lines) + "\n")

    # summary dump for the fixer
    summary = {
        "dup_count": len(dup_rows),
        "dup_by_type": dict(by_type),
        "dup_files": {k: dict(v) for k, v in dup_files.items()},
        "cs_order": cs_order_errs[:50],
        "cs_order_n": len(cs_order_errs),
        "slot_errs": slot_errs[:50],
        "missing_w3d": missing_w3d[:80],
        "anim_no_anim": anim_no_anim[:80],
        "radar": radar_kindof[:40],
        "moduletag": moduletag_dups[:40],
        "missing_proj": missing_proj[:40],
        "missing_wpn": missing_wpn[:40],
        "missing_loco": missing_loco[:40],
        "missing_btn_obj": missing_btn_obj[:40],
        "missing_btn_img_n": len(missing_btn_img),
        "unknown_top_n": len(unknown_top),
        "end_errors_n": len(end_errors),
        "parser_fail_n": fail_n,
        "missing_tex_n": len(missing_tex),
        "heli_vs_jet": heli_vs_jet[:20],
    }
    import json

    Path("/tmp/init_audit_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print("SUMMARY")
    print(json.dumps({k: (v if not isinstance(v, list) else len(v) if k.endswith("n") or True else v) for k, v in summary.items() if not isinstance(v, (list, dict)) or k in ("dup_by_type", "dup_files")}, indent=2, default=str))
    print("cs_order_n", len(cs_order_errs), "slot", len(slot_errs), "w3d", len(missing_w3d), "anim", len(anim_no_anim), "radar", len(radar_kindof), "mtag", len(moduletag_dups), "proj", len(missing_proj), "wpn", len(missing_wpn), "unknown", len(unknown_top), "end", len(end_errors), "btn_obj", len(missing_btn_obj), "btn_img", len(missing_btn_img), "tex", len(missing_tex))
    if cs_order_errs[:10]:
        print("CS ORDER SAMPLE", cs_order_errs[:10])
    if anim_no_anim[:10]:
        print("ANIM SAMPLE", anim_no_anim[:10])
    if radar_kindof[:10]:
        print("RADAR SAMPLE", radar_kindof[:10])
    if unknown_top[:10]:
        print("UNKNOWN SAMPLE", unknown_top[:10])
    if missing_w3d[:10]:
        print("W3D SAMPLE", missing_w3d[:10])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
