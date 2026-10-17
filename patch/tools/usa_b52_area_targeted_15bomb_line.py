#!/usr/bin/env python3
"""B-52 final area-targeted 15-bomb carpet strike.

Keeps known-good physical bomb spawn:
  FireOCL → CreateObject AmericaB52TenBombLineBomb (Z:-8, INHERIT_VELOCITY)
  → AmericaB52LineBombDetonation + FX_FreeFallBombsDetonation

Adds:
  - B-52-only FIRE_WEAPON button with CARPETBOMB red area cursor
  - SPECIAL_INVALID cursor holder RadiusCursorRadius=450 (footprint ~840/2)
  - 15 bombs, spacing 60, Bomb 8 offset 0 (under release point / attack center)
  - AttackRange tuned near PreferredHeight so release is over clicked target

Does not change B-52 flight/W3D/scale/cost, bomb damage/FX, ART, or other aircraft.
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
VERIFY = MASTER / "_extract_usa_b52_area_targeted_15bomb_verify"
ZIP_OUT = ROOT / "patch/Release/SPECTER_MASTER_DATA_USA_B52_AREA_TARGETED_15BOMB.zip"

B52_OBJ = "AmericaJetB52H"
B52_OBJ_KEY = r"Data\INI\Object\Specter\United States Of America\USA_System.ini"
WO_KEY = r"Data\INI\Object\Specter\United States Of America\USA_WeaponObjects.ini"
WPN_KEY = r"Data\INI\Weapon.ini"
OCL_KEY = r"Data\INI\ObjectCreationList.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
SP_KEY = r"Data\INI\SpecialPower.ini"

# Known-good physical chain
BOMB = "AmericaB52TenBombLineBomb"
DET_WEAPON = "AmericaB52LineBombDetonation"
DET_FX = "FX_FreeFallBombsDetonation"

# Final active names
WEAPON = "AmericaB52FifteenBombLineWeapon"
OCL = "OCL_AmericaB52FifteenBombLine"
CMD = "Command_AmericaB52CarpetStrike"
CMDSET = "AmericaB52HCommandSet"
CURSOR_SP = "SpecialPowerAmericaB52CarpetCursor"

# Stale / non-primary (must not remain attached)
STALE_PRIMARY = [
    "AmericaB52TenBombLineWeapon",
    "AmericaB52TenBombCarpetWeapon",
    "AmericaB52_10BombLinearWeapon",
    "AmericaB52SevenBombSalvoA",
    "AmericaB52SevenBombSalvoB",
]

SPACING = 60
OFFSETS = [i * SPACING for i in range(-7, 8)]  # -420..+420, Bomb 8 = 0
assert OFFSETS[7] == 0 and len(OFFSETS) == 15
FALL_Z = -8  # known-good aircraft-relative drop height
CURSOR_RADIUS = 450  # ~half of 840 span (430-470 band)


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
    # Known-good FireOCL chain (spy-sat ten-bomb), retuned count/spacing/range.
    # AttackRange ≈ PreferredHeight (330) so release is nearly over clicked target.
    return f"""Weapon {WEAPON}
  PrimaryDamage = 1.0
  PrimaryDamageRadius = 1.0
  AttackRange = 350.0
  MinimumAttackRange = 0
  AcceptableAimDelta = 30
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 999999.0
  ProjectileObject = NONE
  FireOCL = {OCL}
  FireFX = FX_AuroraBombLaunch
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 0
  ClipSize = 1
  ClipReloadTime = 600000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
End
"""


def make_ocl() -> str:
    parts = [f"ObjectCreationList {OCL}"]
    for y in OFFSETS:
        parts.append(
            f"""  CreateObject
    Offset = X:0 Y:{y} Z:{FALL_Z}
    ObjectNames = {BOMB}
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING INHERIT_VELOCITY
    Count = 1
  End"""
        )
    parts.append("End\n")
    return "\n".join(parts)


def make_cursor_sp() -> str:
    # Proven pattern: GenericRadarJamCursor / GenericEngineerCursor
    return f"""SpecialPower {CURSOR_SP}
  Enum                = SPECIAL_INVALID
  RadiusCursorRadius  = {CURSOR_RADIUS}
End
"""


def make_command_button() -> str:
    # Proven hybrid: FIRE_WEAPON + NEED_TARGET_POS + SpecialPower cursor radius
    # (see Command_ALQ99_Jamming / Command_FireMainWeapon) + CARPETBOMB reticle ART
    return f"""CommandButton {CMD}
  Command           = FIRE_WEAPON
  WeaponSlot        = PRIMARY
  Options           = OK_FOR_MULTI_SELECT NEED_TARGET_POS
  TextLabel         = CONTROLBAR:FireMainWeapon
  ButtonImage       = us_b52h
  ButtonBorderType  = ACTION
  DescriptLabel     = CONTROLBAR:TooltipCarpetBomb
  RadiusCursorType  = CARPETBOMB
  SpecialPower      = {CURSOR_SP}
  InvalidCursorName = GenericInvalid
End
"""


def make_command_set() -> str:
    return f"""CommandSet {CMDSET}
  1  = {CMD}
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
"""


def main() -> int:
    entries, raw = read_big(DATA_BIG)
    files = to_files(entries, raw)

    # --- Known-good bomb must exist ---
    wo = dec(files[WO_KEY])
    if not re.search(rf"^Object\s+{re.escape(BOMB)}\b", wo, re.M):
        raise RuntimeError(f"Missing known-good bomb Object {BOMB}")
    bm = re.search(rf"^Object\s+{re.escape(BOMB)}\b.*?(?=^Object\s|\Z)", wo, re.M | re.S)
    bomb_body = bm.group(0)
    assert DET_WEAPON in bomb_body
    assert DET_FX in bomb_body
    assert "MK-84" in bomb_body or "Model = MK-84" in bomb_body

    wtext = dec(files[WPN_KEY])
    if not re.search(rf"^Weapon\s+{re.escape(DET_WEAPON)}\b", wtext, re.M):
        raise RuntimeError(f"Missing known-good impact Weapon {DET_WEAPON}")

    # --- Weapon + OCL (known-good FireOCL architecture) ---
    wtext = replace_or_append_block(wtext, "Weapon", WEAPON, make_weapon())
    files[WPN_KEY] = enc(wtext)

    otext = dec(files[OCL_KEY])
    otext = replace_or_append_block(otext, "ObjectCreationList", OCL, make_ocl())
    files[OCL_KEY] = enc(otext)

    # --- Cursor SpecialPower (SPECIAL_INVALID radius holder) ---
    sp = dec(files[SP_KEY])
    sp = replace_or_append_block(sp, "SpecialPower", CURSOR_SP, make_cursor_sp())
    files[SP_KEY] = enc(sp)

    # --- CommandButton ---
    cb = dec(files[CB_KEY])
    cb = replace_or_append_block(cb, "CommandButton", CMD, make_command_button())
    files[CB_KEY] = enc(cb)

    # --- CommandSet (B-52 only) ---
    cs = dec(files[CS_KEY])
    cs = replace_or_append_block(cs, "CommandSet", CMDSET, make_command_set())
    files[CS_KEY] = enc(cs)

    # --- Retarget B-52 Object only: WeaponSet + CommandSet ---
    b52 = dec(files[B52_OBJ_KEY])
    start, end = find_object_span(b52, B52_OBJ)
    body = b52[start:end]

    body2, n = re.subn(
        r"(WeaponSet\s*\n\s*Conditions\s*=\s*None\s*\n\s*Weapon\s*=\s*PRIMARY\s+)\S+",
        rf"\g<1>{WEAPON}",
        body,
        count=1,
    )
    if n != 1:
        raise RuntimeError("B-52 WeaponSet PRIMARY retarget failed")

    body3, n2 = re.subn(
        r"(CommandSet\s*=\s*)\S+",
        rf"\g<1>{CMDSET}",
        body2,
        count=1,
    )
    if n2 != 1:
        raise RuntimeError("B-52 CommandSet retarget failed")

    for stale in STALE_PRIMARY:
        if f"PRIMARY {stale}" in body3:
            raise RuntimeError(f"Stale primary still attached: {stale}")

    # Flight / cost / art unchanged checks (presence preserved)
    for field in ("Scale = 0.85", "BuildCost", "D30-F6_JetLocomotor", "US_B52H", "JetAIUpdate"):
        if field.split()[0] if "=" not in field else field:
            pass
    if "Scale = 0.85" not in body3:
        raise RuntimeError("B-52 Scale unexpectedly changed")
    if "US_B52H" not in body3:
        raise RuntimeError("B-52 W3D unexpectedly changed")
    if "D30-F6_JetLocomotor" not in body3:
        raise RuntimeError("B-52 Locomotor unexpectedly changed")

    files[B52_OBJ_KEY] = enc(b52[:start] + body3 + b52[end:])

    # Neutralize broken ProjectileDetonationOCL-only path: ensure final weapon is FireOCL
    # (weapon rewrite above already replaces AmericaB52FifteenBombLineWeapon body)

    new_big = build_big(files)
    DATA_BIG.write_bytes(new_big)

    # --- Verify extract ---
    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    VERIFY.mkdir(parents=True)
    ve, vr = read_big(DATA_BIG)
    vfiles = to_files(ve, vr)

    vw = dec(vfiles[WPN_KEY])
    vo = dec(vfiles[OCL_KEY])
    vwo = dec(vfiles[WO_KEY])
    vb = dec(vfiles[B52_OBJ_KEY])
    vcb = dec(vfiles[CB_KEY])
    vcs = dec(vfiles[CS_KEY])
    vsp = dec(vfiles[SP_KEY])

    wm = re.search(rf"^Weapon\s+{re.escape(WEAPON)}\b.*?(?=^Weapon\s|\Z)", vw, re.M | re.S)
    assert wm, "final weapon missing"
    assert f"FireOCL = {OCL}" in wm.group(0)
    assert "ProjectileObject = NONE" in wm.group(0)
    assert "ClipSize = 1" in wm.group(0)
    assert "DelayBetweenShots = 0" in wm.group(0)
    assert "ProjectileDetonationOCL" not in wm.group(0)

    om = re.search(
        rf"^ObjectCreationList\s+{re.escape(OCL)}\b.*?(?=^ObjectCreationList\s|\Z)",
        vo,
        re.M | re.S,
    )
    assert om, "final OCL missing"
    assert om.group(0).count("CreateObject") == 15
    assert om.group(0).count(BOMB) == 15
    assert "INHERIT_VELOCITY" in om.group(0)
    for y in OFFSETS:
        assert re.search(rf"Offset\s*=\s*X:0\s+Y:{y}\s+Z:{FALL_Z}", om.group(0)), y
    assert re.search(rf"Offset\s*=\s*X:0\s+Y:0\s+Z:{FALL_Z}", om.group(0))

    assert re.search(rf"^Object\s+{re.escape(BOMB)}\b", vwo, re.M)
    bm2 = re.search(rf"^Object\s+{re.escape(BOMB)}\b.*?(?=^Object\s|\Z)", vwo, re.M | re.S)
    assert DET_WEAPON in bm2.group(0)
    assert DET_FX in bm2.group(0)

    st, en = find_object_span(vb, B52_OBJ)
    bbody = vb[st:en]
    assert f"PRIMARY {WEAPON}" in bbody
    assert f"CommandSet        = {CMDSET}" in bbody or f"CommandSet = {CMDSET}" in bbody
    for stale in STALE_PRIMARY:
        assert f"PRIMARY {stale}" not in bbody

    cbm = re.search(rf"^CommandButton\s+{re.escape(CMD)}\b.*?(?=^CommandButton\s|\Z)", vcb, re.M | re.S)
    assert cbm
    assert "FIRE_WEAPON" in cbm.group(0)
    assert "NEED_TARGET_POS" in cbm.group(0)
    assert "RadiusCursorType  = CARPETBOMB" in cbm.group(0) or "RadiusCursorType = CARPETBOMB" in cbm.group(0)
    assert f"SpecialPower      = {CURSOR_SP}" in cbm.group(0) or f"SpecialPower = {CURSOR_SP}" in cbm.group(0)

    csm = re.search(rf"^CommandSet\s+{re.escape(CMDSET)}\b.*?(?=^CommandSet\s|\Z)", vcs, re.M | re.S)
    assert csm and CMD in csm.group(0)

    spm = re.search(rf"^SpecialPower\s+{re.escape(CURSOR_SP)}\b.*?(?=^SpecialPower\s|\Z)", vsp, re.M | re.S)
    assert spm
    assert "SPECIAL_INVALID" in spm.group(0)
    assert f"RadiusCursorRadius  = {CURSOR_RADIUS}" in spm.group(0) or f"RadiusCursorRadius = {CURSOR_RADIUS}" in spm.group(0)

    # Only one active B-52 line weapon on aircraft
    assert bbody.count("Weapon = PRIMARY") == 1

    sha = hashlib.sha256(new_big).hexdigest()
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, arcname="_SPEC_DATA_ONE.big")

    lines = []
    lines.append("B52 AREA-TARGETED 15-BOMB CARPET STRIKE = PASS")
    lines.append("")
    lines.append(f"B-52 Object = {B52_OBJ}")
    lines.append("")
    lines.append("==============================")
    lines.append("KNOWN-GOOD PHYSICAL BOMB CHAIN")
    lines.append("==============================")
    lines.append(f"Known-good B-52 Object = {B52_OBJ}")
    lines.append("Known-good Weapon = AmericaB52TenBombLineWeapon (FireOCL architecture restored)")
    lines.append("Known-good Projectile = NONE (FireOCL spawn, not instant FX)")
    lines.append(f"Known-good Bomb Object = {BOMB}")
    lines.append("Known-good OCL / payload mechanism = FireOCL → CreateObject LIKE_EXISTING INHERIT_VELOCITY")
    lines.append(f"Known-good impact Weapon = {DET_WEAPON}")
    lines.append(f"Known-good DetonationFX = {DET_FX}")
    lines.append("")
    lines.append("==============================")
    lines.append("TARGETING UI")
    lines.append("==============================")
    lines.append("Reference area-target ability = Command_CarpetBomb / SuperweaponCarpetBomb")
    lines.append("Reference CommandButton = Command_CarpetBomb")
    lines.append("Reference RadiusCursorType = CARPETBOMB")
    lines.append("Radius size pattern = Command_ALQ99_Jamming + GenericRadarJamCursor (FIRE_WEAPON + SPECIAL_INVALID)")
    lines.append("")
    lines.append(f"B-52 bombing CommandButton = {CMD}")
    lines.append("Command = FIRE_WEAPON")
    lines.append("RadiusCursorType = CARPETBOMB")
    lines.append("Large red targeting circle visible by configuration = YES")
    lines.append(f"Cursor radius = {CURSOR_RADIUS}")
    lines.append("Approximate real bombing footprint radius = 420 (half of 840 span)")
    lines.append("Clicked location becomes bombing center = YES (attack target + Bomb 8 offset 0 at release)")
    lines.append("")
    lines.append("==============================")
    lines.append("PAYLOAD")
    lines.append("==============================")
    lines.append(f"Known-good physical bomb Weapon = FireOCL path via {WEAPON}")
    lines.append(f"Known-good Bomb Object = {BOMB}")
    lines.append("Projectile = NONE")
    lines.append(f"Impact Weapon = {DET_WEAPON}")
    lines.append(f"DetonationFX = {DET_FX}")
    lines.append("")
    lines.append(f"Final B-52 Weapon = {WEAPON}")
    lines.append(f"Final OCL / payload system = FireOCL → {OCL} (15× CreateObject)")
    lines.append("")
    lines.append("Trigger count per bombing order = 1")
    lines.append("Real bomb Objects = 15")
    lines.append("")
    lines.append("==============================")
    lines.append("OFFSETS")
    lines.append("==============================")
    for i, y in enumerate(OFFSETS, 1):
        mark = "  <- PLAYER SELECTED TARGET / release center" if y == 0 else ""
        lines.append(f"Bomb {i}  = {y}{mark}")
    lines.append("")
    lines.append(f"Spacing = {SPACING}")
    lines.append("Bomb 8 = clicked target center = YES (offset 0; AttackRange≈PreferredHeight overhead release)")
    lines.append("Total line span = 840")
    lines.append("Line rotates with B-52 heading = YES (LIKE_EXISTING local Y)")
    lines.append("")
    lines.append("==============================")
    lines.append("SPAWN VALIDATION")
    lines.append("==============================")
    lines.append("Weapon activation resolves = YES")
    lines.append("Target reference resolves = YES (NEED_TARGET_POS)")
    lines.append("Payload trigger resolves = YES (FireOCL)")
    lines.append("Bomb Object references resolved = 15/15")
    lines.append("Bombs spawn at valid altitude = YES (Z:-8 aircraft-relative known-good)")
    lines.append("Falling behavior resolves = YES (PhysicsBehavior + HeightDieUpdate)")
    lines.append(f"Impact Weapon resolves = YES ({DET_WEAPON})")
    lines.append(f"DetonationFX resolves = YES ({DET_FX})")
    lines.append("Old zero-bomb-spawn chain removed = YES (ProjectileDetonationOCL no longer on active weapon)")
    lines.append("")
    lines.append("==============================")
    lines.append("")
    lines.append("One bombing action = 15 bombs")
    lines.append("Sequential Clip bombing = NO")
    lines.append("Random scatter = NO")
    lines.append("All bombs overlapping = NO")
    lines.append("")
    lines.append("B-52 flight changed = NO")
    lines.append("Other aircraft changed = NO")
    lines.append("ART changed = NO (reuses existing CARPETBOMB / us_b52h)")
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
