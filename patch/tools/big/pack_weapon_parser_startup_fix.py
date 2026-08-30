#!/usr/bin/env python3
"""Startup parser repair: invalid DamageType=GUN in packed Weapon.ini.

Does not change aircraft roster, W3Ds, scales, CommandSets, or loadouts.
Starts from airforce-repair-pass-3 DATA/ART. ART is copied unchanged.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/workspace")
BASE_DATA = Path("/tmp/airforce_repair_pass_3/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/airforce_repair_pass_3/_SPEC_ART_ONE.big")
OUT = Path("/tmp/weapon_parser_startup_fix")
EXTRACT = Path("/tmp/weapon_parser_extract")

BLOCK_RE = {
    "CommandSet": re.compile(r"^CommandSet\s+(\S+)\s*$"),
    "CommandButton": re.compile(r"^CommandButton\s+(\S+)\s*$"),
    "Weapon": re.compile(r"^Weapon(?:\s*=)?\s+(\S+)\s*$"),
    "Object": re.compile(r"^Object(?:Reskin)?\s+(\S+)\s*$"),
    "SpecialPower": re.compile(r"^SpecialPower\s+(\S+)\s*$"),
    "Locomotor": re.compile(r"^Locomotor\s+(\S+)\s*$"),
    "Armor": re.compile(r"^Armor\s+(\S+)\s*$"),
    "Science": re.compile(r"^Science\s+(\S+)\s*$"),
    "Upgrade": re.compile(r"^Upgrade\s+(\S+)\s*$"),
}

GUN_FIXES = {
    "VietnamJetMig29S_WpnGun": """Weapon VietnamJetMig29S_WpnGun
  PrimaryDamage = 42.0
  PrimaryDamageRadius = 8.0
  ScatterRadiusVsInfantry = 40.0
  ScatterRadius = 12.0
  AttackRange = 360.0
  MinimumAttackRange = 20.0
  DamageType = COMANCHE_VULCAN
  DeathType = EXTRA_4
  WeaponSpeed = 9999.0
  ProjectileObject = 30mm_API-T_Projectile
  ProjectileDetonationFX = WeaponFX_30mm_API-T_Tracer
  FireSound = 30mm_fire2
  FireFX = None
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots = 180
  ClipSize = 40
  ClipReloadTime = 1800
  AutoReloadsClip = Yes
  AntiAirborneVehicle = Yes
  AntiAirborneInfantry = Yes
  AntiGround = Yes
  ProjectileCollidesWith = ALLIES ENEMIES STRUCTURES WALLS SHRUBBERY
End
""",
    "IraqJetMig25RB_WpnGun": """Weapon IraqJetMig25RB_WpnGun
  PrimaryDamage = 36.0
  PrimaryDamageRadius = 8.0
  ScatterRadiusVsInfantry = 40.0
  ScatterRadius = 12.0
  AttackRange = 300.0
  MinimumAttackRange = 20.0
  DamageType = COMANCHE_VULCAN
  DeathType = EXTRA_4
  WeaponSpeed = 9999.0
  ProjectileObject = 30mm_API-T_Projectile
  ProjectileDetonationFX = WeaponFX_30mm_API-T_Tracer
  FireSound = 30mm_fire2
  FireFX = None
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots = 220
  ClipSize = 30
  ClipReloadTime = 1800
  AutoReloadsClip = Yes
  AntiAirborneVehicle = Yes
  AntiAirborneInfantry = Yes
  AntiGround = Yes
  ProjectileCollidesWith = ALLIES ENEMIES STRUCTURES WALLS SHRUBBERY
End
""",
}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def norm_key(name: str) -> str:
    return name.replace("/", "\\").lower()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not a BIGF archive: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def load_big_map(path: Path):
    entries, raw = read_big(path)
    data_map = {}
    keys = []
    for name, off, size in entries:
        key = norm_key(name)
        if key not in data_map:
            keys.append(key)
        data_map[key] = (name.replace("/", "\\"), raw[off : off + size])
    return data_map, keys


def uniqueness_report(data_map: dict) -> dict:
    found = defaultdict(list)
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        for kind, rx in BLOCK_RE.items():
            for i, line in enumerate(text.splitlines(), 1):
                s = line.split(";", 1)[0].rstrip()
                m = rx.match(s)
                if m and m.group(1) not in ("=", "Yes", "No"):
                    found[(kind, m.group(1))].append((name, i))
    dups = defaultdict(list)
    for (kind, nm), locs in found.items():
        if len(locs) > 1:
            dups[kind].append((nm, locs))
    return {"found": found, "dups": dups}


def parse_weapons(text: str) -> dict:
    lines = text.splitlines()
    blocks = []
    inside = []
    unfinished = []
    orphan = []
    empty = []
    invalid = []
    cur = None
    start_re = re.compile(r"^( *)Weapon(?:\s*=)?\s+(\S*)\s*$")
    end_re = re.compile(r"^( *)End\s*$")
    for lineno, raw in enumerate(lines, 1):
        code = raw.split(";", 1)[0].rstrip()
        if not code.strip():
            continue
        m = start_re.match(code)
        if m:
            indent, name = m.group(1), m.group(2)
            if cur is not None:
                inside.append((lineno, name, cur["name"], cur["start"]))
            if name == "":
                empty.append(lineno)
            if indent not in ("",):
                invalid.append((lineno, "indented Weapon"))
            cur = {"name": name, "start": lineno, "end": None, "indent": indent}
            continue
        m2 = end_re.match(code)
        if m2:
            indent = m2.group(1)
            if cur is None:
                orphan.append(lineno)
                continue
            if indent == cur["indent"]:
                cur["end"] = lineno
                blocks.append(cur)
                cur = None
    if cur is not None:
        unfinished.append((cur["name"], cur["start"]))
    names = [b["name"] for b in blocks]
    dups = {n: c for n, c in Counter(names).items() if c > 1}
    ci = defaultdict(list)
    for b in blocks:
        ci[b["name"].lower()].append(b["name"])
    ci_dups = {k: sorted(set(v)) for k, v in ci.items() if len(v) > 1}
    return {
        "blocks": blocks,
        "inside": inside,
        "unfinished": unfinished,
        "orphan": orphan,
        "empty": empty,
        "invalid": invalid,
        "dups": dups,
        "ci_dups": ci_dups,
        "lines": lines,
    }


def replace_named_weapon(text: str, name: str, new_block: str) -> str:
    rx = re.compile(
        rf"^Weapon {re.escape(name)}\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    matches = list(rx.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"{name} expected 1 block, found {len(matches)}")
    m = matches[0]
    block = new_block if new_block.endswith("\n") else new_block + "\n"
    return text[: m.start()] + block + text[m.end() :].lstrip("\n")


def context_dump(lines: list[str], lineno: int, before: int = 40, after: int = 40) -> str:
    lo = max(0, lineno - 1 - before)
    hi = min(len(lines), lineno + after)
    out = []
    for i in range(lo, hi):
        mark = ">>" if i + 1 == lineno else "  "
        out.append(f"{mark}{i+1:6d}|{lines[i]}")
    return "\n".join(out)


def extract_big(path: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    entries, raw = read_big(path)
    for name, off, size in entries:
        out = dest / name.replace("\\", "/")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw[off : off + size])


def main() -> None:
    if not BASE_DATA.exists() or not BASE_ART.exists():
        raise SystemExit("pass-3 baseline BIGs missing")

    data_map, _ = load_big_map(BASE_DATA)
    wk = r"data\ini\weapon.ini"
    if wk not in data_map:
        raise SystemExit("packed Weapon.ini missing")
    wname, wblob = data_map[wk]
    text = wblob.decode("latin1", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    before = parse_weapons(text)

    gun_occ = [i + 1 for i, l in enumerate(before["lines"]) if "VietnamJetMig29S_WpnGun" in l]
    decl_occ = [
        i + 1
        for i, l in enumerate(before["lines"])
        if re.match(r"^Weapon VietnamJetMig29S_WpnGun\s*$", l.split(";", 1)[0].rstrip())
    ]
    print("VietnamJetMig29S_WpnGun occurrences", len(gun_occ), "decls", decl_occ)

    gun_block = next(b for b in before["blocks"] if b["name"] == "VietnamJetMig29S_WpnGun")
    idx = before["blocks"].index(gun_block)
    prev = before["blocks"][idx - 1]
    nxt = before["blocks"][idx + 1]
    print("PREV", prev)
    print("GUN", gun_block)
    print("NEXT", nxt)

    if "DamageType = GUN" not in "\n".join(before["lines"][gun_block["start"] - 1 : gun_block["end"]]):
        raise SystemExit("expected DamageType = GUN in reported weapon")

    # Patch both GUN cannons (second would crash next)
    new_text = text
    for name in GUN_FIXES:
        new_text = replace_named_weapon(new_text, name, GUN_FIXES[name])
    if "DamageType = GUN" in new_text:
        raise SystemExit("DamageType = GUN still present after fix")

    after = parse_weapons(new_text)
    gun_after = [
        i + 1
        for i, l in enumerate(after["lines"])
        if re.match(r"^Weapon VietnamJetMig29S_WpnGun\s*$", l.split(";", 1)[0].rstrip())
    ]
    if len(gun_after) != 1:
        raise SystemExit(f"gun decls after fix: {gun_after}")
    if after["dups"] or after["ci_dups"]:
        raise SystemExit(f"weapon dups after fix: {after['dups']} {after['ci_dups']}")
    if after["unfinished"] or after["inside"] or after["empty"]:
        raise SystemExit(f"structure fail: {after['unfinished']} {after['inside']} {after['empty']}")

    # projectile exists once
    uniq_before = uniqueness_report(data_map)
    proj_locs = uniq_before["found"].get(("Object", "30mm_API-T_Projectile"), [])
    if len(proj_locs) != 1:
        raise SystemExit(f"30mm_API-T_Projectile decls: {proj_locs}")

    data_map[wk] = (wname, new_text.encode("latin1"))
    uniq_after = uniqueness_report(data_map)

    def dup_names(rep, kind):
        return {nm for nm, _ in rep["dups"].get(kind, [])}

    for kind in ("Object", "Weapon", "CommandButton", "CommandSet", "SpecialPower", "Science", "Upgrade", "Armor", "Locomotor"):
        extra = dup_names(uniq_after, kind) - dup_names(uniq_before, kind)
        if extra:
            raise SystemExit(f"new {kind} dups: {extra}")

    # CommandSet.ini byte-identical
    cs_k = r"data\ini\commandset.ini"
    base_map, _ = load_big_map(BASE_DATA)
    if data_map[cs_k][1] != base_map[cs_k][1]:
        raise SystemExit("CommandSet.ini mutated")

    OUT.mkdir(parents=True, exist_ok=True)
    file_map = {name: blob for name, blob in data_map.values()}
    data_bytes = build_big(file_map)
    (OUT / "_SPEC_DATA_ONE.big").write_bytes(data_bytes)
    shutil.copy2(BASE_ART, OUT / "_SPEC_ART_ONE.big")

    extract_big(OUT / "_SPEC_DATA_ONE.big", EXTRACT / "DataBig")
    re_map, _ = load_big_map(OUT / "_SPEC_DATA_ONE.big")
    re_text = re_map[wk][1].decode("latin1")
    re_parse = parse_weapons(re_text)
    re_decls = [
        i + 1
        for i, l in enumerate(re_parse["lines"])
        if re.match(r"^Weapon VietnamJetMig29S_WpnGun\s*$", l.split(";", 1)[0].rstrip())
    ]
    if len(re_decls) != 1:
        raise SystemExit(f"reextract decls {re_decls}")
    if "DamageType = GUN" in re_text:
        raise SystemExit("reextract still has GUN")
    gun_b = next(b for b in re_parse["blocks"] if b["name"] == "VietnamJetMig29S_WpnGun")
    prev_b = re_parse["blocks"][re_parse["blocks"].index(gun_b) - 1]
    if prev_b["end"] is None or prev_b["end"] >= gun_b["start"]:
        raise SystemExit("previous weapon not closed")
    if "30mm_API-T_Projectile" not in "\n".join(re_parse["lines"][gun_b["start"] - 1 : gun_b["end"]]):
        raise SystemExit("gun missing projectile")
    if "DamageType = COMANCHE_VULCAN" not in "\n".join(re_parse["lines"][gun_b["start"] - 1 : gun_b["end"]]):
        raise SystemExit("gun missing COMANCHE_VULCAN")

    write_reports(before, after, re_parse, gun_occ, decl_occ, prev, gun_block, nxt)
    data_hash = sha256(OUT / "_SPEC_DATA_ONE.big")
    art_hash = sha256(OUT / "_SPEC_ART_ONE.big")
    print("DATA", data_hash)
    print("ART", art_hash)

    for name in (
        "WEAPON_PARSE_CRASH_CONTEXT.md",
        "WEAPON_DELTA_414_TO_HEAD.md",
        "INSTALL.txt",
    ):
        shutil.copy2(ROOT / name, OUT / name)

    zip_path = OUT / "WEAPON_PARSER_STARTUP_FIX_V1.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "INSTALL.txt",
            "WEAPON_PARSE_CRASH_CONTEXT.md",
            "WEAPON_DELTA_414_TO_HEAD.md",
        ):
            zf.write(OUT / name, name)
    print("ZIP", sha256(zip_path))
    print("PACK OK")


def write_reports(before, after, re_parse, gun_occ, decl_occ, prev, gun_block, nxt) -> None:
    lines = before["lines"]
    ctx = []
    ctx.append("# WEAPON PARSE CRASH CONTEXT\n\n")
    ctx.append("Packed file: `Data\\INI\\Weapon.ini` from `_SPEC_DATA_ONE.big` (airforce-repair-pass-3-v1).\n\n")
    ctx.append("REPORTED_CRASH_FILE = Data\\INI\\Weapon.ini\n")
    ctx.append("REPORTED_CRASH_LINE = Weapon VietnamJetMig29S_WpnGun\n")
    ctx.append(f"REPORTED_WEAPON_OCCURRENCES_BEFORE = {len(decl_occ)} declaration(s) at lines {decl_occ}\n")
    ctx.append(f"All substring hits (including object refs in this file): {gun_occ}\n\n")
    ctx.append(f"PREVIOUS_WEAPON_NAME = {prev['name']} (L{prev['start']}-L{prev['end']})\n")
    ctx.append(f"REPORTED_WEAPON = VietnamJetMig29S_WpnGun (L{gun_block['start']}-L{gun_block['end']})\n")
    ctx.append(f"NEXT_WEAPON_NAME = {nxt['name']} (L{nxt['start']}-L{nxt['end']})\n\n")
    ctx.append("REPORTED_LINE = VietnamJetMig29S_WpnGun\n")
    ctx.append("ACTUAL_BAD_BLOCK = VietnamJetMig29S_WpnGun\n")
    ctx.append(
        "ROOT_CAUSE = Invalid Zero Hour DamageType GUN inside VietnamJetMig29S_WpnGun "
        "(plus tank FireFX/FireSound and AutoReloadsClip=YES). Previous weapon "
        f"{prev['name']} has a matching End at L{prev['end']}. The engine reports the "
        "Weapon header of the block that fails field validation.\n\n"
    )
    ctx.append(
        "SOURCE_FILE_THAT_INTRODUCED_BUG = patch/tools/big/generate_jp_kr_vn_objects.py "
        "function cannon(), inlined into packed Weapon.ini by pack_jp_kr_vn_airforce_fix.py "
        "(JP/KR/VN pass). A second copy of the same broken template is IraqJetMig25RB_WpnGun.\n\n"
    )
    ctx.append(
        "FIX_APPLIED = Replaced both GUN cannons with VietnamJetMig21_WpnGun structural "
        "syntax (DamageType=COMANCHE_VULCAN, ProjectileObject=30mm_API-T_Projectile). "
        "Kept intended balance (damage/clip/delay/range). Fixed cannon() generator so a "
        "future pack cannot reintroduce GUN.\n\n"
    )
    ctx.append("## 40 lines before / after reported declaration\n\n```\n")
    ctx.append(context_dump(lines, gun_block["start"], 40, 40))
    ctx.append("\n```\n\n")
    ctx.append("## Pre-fix sequential parse (Weapon.ini)\n\n")
    ctx.append(f"- Weapon blocks: {len(before['blocks'])}\n")
    ctx.append(f"- duplicate Weapon names: {len(before['dups'])}\n")
    ctx.append(f"- unfinished Weapon blocks: {len(before['unfinished'])}\n")
    ctx.append(f"- Weapon-inside-Weapon: {len(before['inside'])}\n")
    ctx.append(f"- empty Weapon name: {len(before['empty'])}\n")
    ctx.append(
        f"- unindented End with no open Weapon (includes `Weapon = Name` false positives if any): {len(before['orphan'])}\n\n"
    )
    ctx.append("Same-country VietnamJetMig29S_* declarations (unique):\n")
    for b in before["blocks"]:
        if b["name"].startswith("VietnamJetMig29S"):
            ctx.append(f"- {b['name']} L{b['start']}-L{b['end']}\n")
    (ROOT / "WEAPON_PARSE_CRASH_CONTEXT.md").write_text("".join(ctx), encoding="ascii")

    delta = []
    delta.append("# WEAPON DELTA 414 TO HEAD\n\n")
    delta.append(
        "PR #414 packed DATA was not present as a local BIG in this environment. "
        "This delta is reconstructed from packed Weapon.ini section markers and the "
        "packers that appended after the last global roster.\n\n"
    )
    delta.append("Marker: `; ===== SPECTER FINAL GLOBAL AIRFORCE ROSTER WEAPONS BEGIN =====` (L43180)\n")
    delta.append("Marker: `; ===== SPECTER FINAL GLOBAL AIRFORCE ROSTER WEAPONS END =====` (L55675)\n")
    delta.append("Marker: `; SPECTER JP/KR/VN airforce unique weapons. Inlined into Weapon.ini only.` (L55677)\n\n")
    delta.append("## Introduced after global-roster END (JP/KR/VN second append + later passes)\n\n")
    delta.append("| Weapon | Approx pass | Notes |\n|---|---|---|\n")
    rows = [
        ("VietnamJetMig29S_WpnRadar", "jp-korea-vietnam-airforce-fix", "valid A2A"),
        ("VietnamJetMig29S_WpnIR", "jp-korea-vietnam-airforce-fix", "valid A2A; previous block before crash"),
        ("VietnamJetMig29S_WpnGun", "jp-korea-vietnam-airforce-fix", "MALFORMED DamageType=GUN - repaired this pass"),
        ("Japan_Weapon_AAM4B_F15JStd", "jp-korea-vietnam / init-crash-fix", "unique name after earlier dup cleanup"),
        ("IraqJetMig25RB_WpnLT3", "jp-korea-vietnam-airforce-fix", "kept"),
        ("IraqJetMig25RB_WpnGun", "jp-korea-vietnam-airforce-fix", "same GUN template - repaired this pass"),
        ("LibyaJetMig21MF_WpnRkt", "jp-korea-vietnam-airforce-fix", "kept"),
        ("LibyaJetMig21_WpnBombHvy", "jp-korea-vietnam-airforce-fix", "kept"),
        ("UkraineJetMig21_WpnBombMed", "jp-korea-vietnam-airforce-fix", "kept"),
        ("ItalyJetC130J_WpnHeavy", "jp-korea-vietnam-airforce-fix", "kept"),
        ("GermanyJetTornadoIDS_WpnBombHvy", "airforce-repair-pass-3", "kept; not parser-broken"),
        ("GermanyJetTornadoIDS_WpnIR2", "airforce-repair-pass-3", "kept; not parser-broken"),
    ]
    for r in rows:
        delta.append("| " + " | ".join(r) + " |\n")
    delta.append(
        "\nVietnam guns in the *first* roster cluster (VietnamJetMig21_WpnGun, "
        "VietnamJetSu27_WpnGun, ...) already use COMANCHE_VULCAN + 30mm_API-T_Projectile "
        "and are not the crash.\n\n"
        "DO NOT revert post-414 weapons. This pass only rewrote the two GUN cannons.\n"
    )
    (ROOT / "WEAPON_DELTA_414_TO_HEAD.md").write_text("".join(delta), encoding="ascii")

    (ROOT / "INSTALL.txt").write_text(
        "SPECTER WEAPON PARSER STARTUP FIX V1\n\n"
        "Copy _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big into the game folder.\n"
        "ART is unchanged from airforce-repair-pass-3-v1.\n"
        "DATA repairs invalid DamageType=GUN in Weapon.ini.\n"
        "USER RUNTIME BOOT TEST REQUIRED. Cursor cannot launch Zero Hour.\n",
        encoding="ascii",
    )


if __name__ == "__main__":
    main()
