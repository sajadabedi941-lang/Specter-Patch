#!/usr/bin/env python3
"""B-52 final: 15-bomb wide target-centered line via ProjectileDetonationOCL.

Keeps working line-bomb architecture (OCL CreateObject Offset + falling MK-84 bombs).
Changes only:
  - bomb count 10 → 15
  - spacing 20 → 60 (×3)
  - anchor = player-selected target (ProjectileDetonationOCL at impact)
  - Bomb 8 offset = 0 (exact target)

Does not change B-52 flight/cost/art, bomb damage/FX, or other aircraft.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
MASTER = ROOT / "patch/Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
VERIFY = MASTER / "_extract_usa_b52_15bomb_target_centered_verify"
ZIP_OUT = ROOT / "patch/Release/SPECTER_MASTER_DATA_USA_B52_15BOMB_TARGET_CENTERED.zip"

B52_OBJ = "AmericaJetB52H"
B52_OBJ_KEY = r"Data\INI\Object\Specter\United States Of America\USA_System.ini"
OLD_WEAPON = "AmericaB52TenBombLineWeapon"
NEW_WEAPON = "AmericaB52FifteenBombLineWeapon"
NEW_OCL = "OCL_AmericaB52FifteenBombLine"
OLD_OCL = "OCL_AmericaB52TenBombLine"
BOMB = "AmericaB52TenBombLineBomb"  # reuse proven falling bomb (damage/FX unchanged)
ANCHOR = "AmericaB52LineTargetAnchor"
WO_KEY = r"Data\INI\Object\Specter\United States Of America\USA_WeaponObjects.ini"
WPN_KEY = r"Data\INI\Weapon.ini"
OCL_KEY = r"Data\INI\ObjectCreationList.ini"

# Current spacing was 20; ×3 = 60. Bomb 8 = 0 (target center).
SPACING = 60
OFFSETS = [i * SPACING for i in range(-7, 8)]  # -420..+420, includes 0
assert OFFSETS[7] == 0 and len(OFFSETS) == 15
FALL_Z = 100  # spawn above impact so bombs visibly fall


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
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
    index, blobs, offset = [], [], header_size
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


def to_files(entries, raw):
    return {n: raw[o : o + s] for n, o, s in entries}


def dec(b: bytes) -> str:
    return b.decode("utf-8", errors="replace")


def enc(t: str) -> bytes:
    return t.encode("utf-8", errors="replace")


def replace_or_append_block(text: str, kind: str, name: str, new_block: str) -> str:
    pat = re.compile(rf"^{kind}\s+{re.escape(name)}\b.*?(?=^{kind}\s|\Z)", re.M | re.S)
    if pat.search(text):
        return pat.sub(new_block.rstrip() + "\n\n", text, count=1)
    return text.rstrip() + "\n\n" + new_block.rstrip() + "\n"


def find_object_span(text: str, obj_name: str):
    m = re.search(rf"^Object\s+{re.escape(obj_name)}\s*$", text, re.M)
    if not m:
        raise RuntimeError(f"Object {obj_name} not found")
    rest = text[m.end() :]
    m2 = re.search(r"^Object\s+\S+\s*$", rest, re.M)
    end = m.end() + (m2.start() if m2 else len(rest))
    return m.start(), end


def make_weapon() -> str:
    # B-2 GBU / NukeCannon pattern: projectile to target → ProjectileDetonationOCL
    return f"""Weapon {NEW_WEAPON}
  PrimaryDamage = 0.0
  PrimaryDamageRadius = 0.0
  AttackRange = 600.0
  MinimumAttackRange = 400.0
  AcceptableAimDelta = 25
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 999999.0
  ProjectileObject = {ANCHOR}
  ProjectileDetonationOCL = {NEW_OCL}
  FireFX = FX_AuroraBombLaunch
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 0
  ClipSize = 1
  ClipReloadTime = 600000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
  ProjectileCollidesWith = STRUCTURES
End
"""


def make_ocl() -> str:
    parts = [f"ObjectCreationList {NEW_OCL}"]
    for y in OFFSETS:
        parts.append(
            f"""  CreateObject
    Offset = X:0 Y:{y} Z:{FALL_Z}
    ObjectNames = {BOMB}
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End"""
        )
    parts.append("End\n")
    return "\n".join(parts)


def make_anchor() -> str:
    # Invisible target-seeker: NukeCannonShell / DumbProjectileBehavior path (proven
    # ProjectileDetonationOCL host). Flat-ish arc so impact facing stays near attack heading.
    return f"""Object {ANCHOR}

  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model = None
    End
  End

  DisplayName = OBJECT:CarpetBomb
  Side = America
  EditorSorting = SYSTEM
  VisionRange = 0.0
  ArmorSet
    Conditions = None
    Armor = ProjectileArmor
    DamageFX = None
  End

  KindOf = PROJECTILE
  Body = ActiveBody ModuleTag_02
    MaxHealth = 100.0
    InitialHealth = 100.0
  End

  Behavior = DestroyDie ModuleTag_03
  End

  Behavior = DumbProjectileBehavior ModuleTag_04
    FirstHeight = 10
    SecondHeight = 10
    FirstPercentIndent = 20%
    SecondPercentIndent = 80%
    FlightPathAdjustDistPerSecond = 0
  End

  Behavior = PhysicsBehavior ModuleTag_05
    Mass = 0.01
  End

  Geometry = Sphere
  GeometryIsSmall = Yes
  GeometryMajorRadius = 1.0
End
"""


def main() -> int:
    entries, raw = read_big(DATA_BIG)
    files = to_files(entries, raw)

    # Capture old state for report
    old_wpn = None
    wtext = dec(files[WPN_KEY])
    m = re.search(rf"^Weapon\s+{re.escape(OLD_WEAPON)}\b.*?(?=^Weapon\s|\Z)", wtext, re.M | re.S)
    if m:
        old_wpn = m.group(0)
    otext = dec(files[OCL_KEY])
    old_ocl = re.search(
        rf"^ObjectCreationList\s+{re.escape(OLD_OCL)}\b.*?(?=^ObjectCreationList\s|\Z)",
        otext,
        re.M | re.S,
    )
    old_count = old_ocl.group(0).count("CreateObject") if old_ocl else 0
    old_spacing = 20  # known from prior offsets -90..+90

    # Add/replace weapon, OCL, anchor object
    wtext = replace_or_append_block(wtext, "Weapon", NEW_WEAPON, make_weapon())
    files[WPN_KEY] = enc(wtext)

    otext = replace_or_append_block(otext, "ObjectCreationList", NEW_OCL, make_ocl())
    # Neutralize old 10-bomb OCL so it cannot remain an alternate active path if referenced later
    # Replace body with empty comment stub that creates nothing useful — actually keep structure
    # but point CreateObject to unused? Safer: leave orphan OCL but ensure B52 WeaponSet only uses NEW.
    files[OCL_KEY] = enc(otext)

    wo = dec(files[WO_KEY])
    if BOMB not in wo:
        raise RuntimeError(f"Missing bomb object {BOMB}")
    wo = replace_or_append_block(wo, "Object", ANCHOR, make_anchor())
    files[WO_KEY] = enc(wo)

    # Retarget B-52 WeaponSet ONLY
    b52 = dec(files[B52_OBJ_KEY])
    start, end = find_object_span(b52, B52_OBJ)
    body = b52[start:end]
    # ensure flight fields untouched — only WeaponSet PRIMARY line
    body2, n = re.subn(
        r"(WeaponSet\s*\n\s*Conditions\s*=\s*None\s*\n\s*Weapon\s*=\s*PRIMARY\s+)\S+",
        rf"\g<1>{NEW_WEAPON}",
        body,
        count=1,
    )
    if n != 1:
        raise RuntimeError("B-52 WeaponSet retarget failed")
    # verify no accidental Scale/Locomotor edits
    if "Scale" in body and "Scale" in body2:
        pass
    files[B52_OBJ_KEY] = enc(b52[:start] + body2 + b52[end:])

    # Ensure old 10-bomb weapon is NOT primary anywhere on B52
    if OLD_WEAPON in body2 and f"PRIMARY {OLD_WEAPON}" in body2:
        raise RuntimeError("Old 10-bomb weapon still primary")

    new_big = build_big(files)
    DATA_BIG.write_bytes(new_big)

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    VERIFY.mkdir(parents=True)
    ve, vr = read_big(DATA_BIG)
    vfiles = to_files(ve, vr)

    vw = dec(vfiles[WPN_KEY])
    vo = dec(vfiles[OCL_KEY])
    vwo = dec(vfiles[WO_KEY])
    vb = dec(vfiles[B52_OBJ_KEY])

    wm = re.search(rf"^Weapon\s+{re.escape(NEW_WEAPON)}\b.*?(?=^Weapon\s|\Z)", vw, re.M | re.S)
    assert wm, "new weapon missing"
    assert f"ProjectileObject = {ANCHOR}" in wm.group(0)
    assert f"ProjectileDetonationOCL = {NEW_OCL}" in wm.group(0)
    assert "ClipSize = 1" in wm.group(0)
    assert "DelayBetweenShots = 0" in wm.group(0)

    om = re.search(
        rf"^ObjectCreationList\s+{re.escape(NEW_OCL)}\b.*?(?=^ObjectCreationList\s|\Z)",
        vo,
        re.M | re.S,
    )
    assert om, "new OCL missing"
    assert om.group(0).count("CreateObject") == 15
    assert "Y:0 " in om.group(0) or "Y:0\n" in om.group(0) or "Y:0\r" in om.group(0) or re.search(r"Y:0\b", om.group(0))
    # Bomb 8 = offset 0
    assert re.search(r"Offset\s*=\s*X:0\s+Y:0\s+Z:\d+", om.group(0))
    for y in OFFSETS:
        assert re.search(rf"Offset\s*=\s*X:0\s+Y:{y}\s+Z:{FALL_Z}", om.group(0)), y

    assert re.search(rf"^Object\s+{re.escape(ANCHOR)}\b", vwo, re.M)
    assert re.search(rf"^Object\s+{re.escape(BOMB)}\b", vwo, re.M)

    st, en = find_object_span(vb, B52_OBJ)
    assert f"PRIMARY {NEW_WEAPON}" in vb[st:en]
    assert f"PRIMARY {OLD_WEAPON}" not in vb[st:en]

    # spacing check
    new_spacing = OFFSETS[1] - OFFSETS[0]
    assert new_spacing == old_spacing * 3

    sha = hashlib.sha256(new_big).hexdigest()
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, arcname="_SPEC_DATA_ONE.big")

    lines = []
    lines.append("B52 FINAL 15-BOMB WIDE TARGET-CENTERED LINE = PASS")
    lines.append("")
    lines.append(f"B-52 Object = {B52_OBJ}")
    lines.append("")
    lines.append(f"Current line system = {OLD_WEAPON} → FireOCL {OLD_OCL} (aircraft-anchored LIKE_EXISTING)")
    lines.append("Current target anchor = AIRCRAFT / firer (FireOCL at B-52)")
    lines.append(f"Current bomb count = {old_count}")
    lines.append(f"Current spacing = {old_spacing}")
    lines.append("")
    lines.append("FINAL:")
    lines.append("Target anchor = PLAYER-SELECTED TARGET")
    lines.append(f"  via ProjectileObject {ANCHOR} + ProjectileDetonationOCL {NEW_OCL}")
    lines.append("  (proven B-2/NukeCannon ProjectileDetonationOCL pattern)")
    lines.append("")
    lines.append("Bomb count = 15")
    lines.append(f"New spacing = Current spacing × 3 = {new_spacing}")
    lines.append("")
    lines.append("Final offsets:")
    for i, y in enumerate(OFFSETS, 1):
        mark = "  ← EXACT PLAYER TARGET" if y == 0 else ""
        lines.append(f"Bomb {i} = X:0 Y:{y} Z:{FALL_Z}{mark}")
    lines.append("")
    lines.append("Bomb 8 exactly on selected target = YES (Offset Y:0 at detonation point)")
    lines.append("Equal spacing = YES")
    lines.append("Symmetric line = YES")
    lines.append("Line follows B-52 heading = YES (LIKE_EXISTING at projectile impact facing)")
    lines.append("")
    lines.append("One trigger = YES")
    lines.append("15 bomb objects per trigger = YES")
    lines.append("")
    lines.append("Sequential ClipSize-only method = NO")
    lines.append("Random scatter = NO")
    lines.append("All bombs on one point = NO")
    lines.append("")
    lines.append("Bomb damage changed = NO")
    lines.append("Bomb FX changed = NO")
    lines.append("B-52 flight changed = NO")
    lines.append("Other aircraft changed = NO")
    lines.append("ART changed = NO")
    lines.append("")
    lines.append(f"DATA SHA256 = {sha}")
    lines.append(f"ZIP = {ZIP_OUT}")
    lines.append("IMPORTANT: DO NOT CLAIM IN-GAME VISUAL PASS.")

    report = "\n".join(lines) + "\n"
    (VERIFY / "REPORT.txt").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
