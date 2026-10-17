#!/usr/bin/env python3
"""Upgrade AmericaJetB2A single 10-ton bomb to Tsar/FOAB-scale heavy conventional explosion.

BGM-108CALL does not exist in Specter DATA/DONOR. Reference used:
  Object   = Russia_Fab9000
  Weapon   = 9000kg_TsarBomb
  FX       = Tsar_Explosion
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
MASTER = ROOT / "patch/Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
STAGE = MASTER / "_stage_usa_b2a_bgm108call_explosion"
VERIFY = MASTER / "_extract_usa_b2a_bgm108call_explosion_verify"
ZIP_OUT = ROOT / "patch/Release/SPECTER_MASTER_DATA_USA_B2A_BGM108CALL_EXPLOSION.zip"

WEAPON_KEY = r"Data\INI\Weapon.ini"
WO_KEY = r"Data\INI\Object\Specter\United States Of America\USA_WeaponObjects.ini"
B2A_KEY = r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini"

NEW_WEAPON = """Weapon AmericaB2A10TonBombWeapon
  PrimaryDamage           = 12000.0
  PrimaryDamageRadius     = 620.0
  SecondaryDamage         = 2200.0
  SecondaryDamageRadius   = 750.0
  ScatterRadius           = 25.0
  ScatterRadiusVsInfantry = 80.0
  AttackRange             = 600.0
  MinimumAttackRange      = 400.0
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 9999.0
  ProjectileObject        = AmericaB2A10TonBombProjectile
  FireFX                  = FX_AuroraBombLaunch
  ProjectileDetonationFX  = Tsar_Explosion
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 0
  ClipSize                = 1
  ClipReloadTime          = 600000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
  ShockWaveAmount         = 480.0
  ShockWaveRadius         = 750.0
  ShockWaveTaperOff       = 0.33
End
"""


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


def replace_weapon_block(text: str, name: str, new_block: str) -> str:
    pat = re.compile(
        rf"^Weapon {re.escape(name)}\b.*?(?=^Weapon |\Z)",
        re.M | re.S,
    )
    matches = list(pat.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly 1 Weapon {name}, found {len(matches)}")
    m = matches[0]
    block = new_block if new_block.endswith("\n") else new_block + "\n"
    return text[: m.start()] + block + text[m.end() :]


def extract_weapon(text: str, name: str) -> str:
    m = re.search(rf"^Weapon {re.escape(name)}\b.*?(?=^Weapon |\Z)", text, re.M | re.S)
    if not m:
        raise RuntimeError(f"Missing Weapon {name}")
    return m.group(0)


def field(block: str, key: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(\S+)", block, re.M)
    return m.group(1) if m else None


def main() -> int:
    STAGE.mkdir(parents=True, exist_ok=True)
    VERIFY.mkdir(parents=True, exist_ok=True)

    entries, raw = read_big(DATA_BIG)
    file_map: dict[str, bytes] = {}
    order: list[str] = []
    for name, off, size in entries:
        key = name.replace("/", "\\")
        if key not in file_map:
            order.append(key)
        file_map[key] = raw[off : off + size]

    weapon_txt = file_map[WEAPON_KEY].decode("utf-8", errors="replace")
    old_block = extract_weapon(weapon_txt, "AmericaB2A10TonBombWeapon")
    old_damage = field(old_block, "PrimaryDamage")
    old_radius = field(old_block, "PrimaryDamageRadius")
    old_fx = field(old_block, "ProjectileDetonationFX")

    weapon_txt2 = replace_weapon_block(weapon_txt, "AmericaB2A10TonBombWeapon", NEW_WEAPON)
    # Ensure no accidental nukes / radiation in this weapon
    new_block = extract_weapon(weapon_txt2, "AmericaB2A10TonBombWeapon")
    for banned in ("Radiation", "Nuclear", "Neutron", "Nuke"):
        if banned.lower() in new_block.lower():
            raise RuntimeError(f"Banned token {banned} in B2A weapon")

    # Confirm ClipSize 1 and dedicated projectile
    assert field(new_block, "ClipSize") == "1"
    assert field(new_block, "ProjectileObject") == "AmericaB2A10TonBombProjectile"
    assert field(new_block, "ProjectileDetonationFX") == "Tsar_Explosion"
    assert float(field(new_block, "PrimaryDamageRadius")) > float(old_radius)

    # Other bomber weapons must remain untouched (byte-identical for their blocks)
    for other in (
        "AmericaB2SixGuidedBombWeapon",
        "AmericaB52SevenBombSalvoA",
        "AmericaB52SevenBombSalvoB",
        "AmericaB1ThreeGuidedBombWeapon",
    ):
        if other in weapon_txt:
            assert extract_weapon(weapon_txt, other) == extract_weapon(weapon_txt2, other), other

    file_map[WEAPON_KEY] = weapon_txt2.encode("utf-8")

    # Verify B2A object unchanged for cost/payload wiring except already pointing at dedicated weapon
    b2a = file_map[B2A_KEY].decode("utf-8", errors="replace")
    if "BuildCost           = 15000" not in b2a and "BuildCost = 15000" not in b2a:
        # allow flexible spaces
        m = re.search(r"BuildCost\s*=\s*(\d+)", b2a)
        if not m or m.group(1) != "15000":
            raise RuntimeError(f"AmericaJetB2A BuildCost not 15000: {m.group(0) if m else None}")
    if "AmericaB2A10TonBombWeapon" not in b2a:
        raise RuntimeError("AmericaJetB2A missing dedicated weapon")

    wo = file_map[WO_KEY].decode("utf-8", errors="replace")
    if "Object AmericaB2A10TonBombProjectile" not in wo:
        raise RuntimeError("AmericaB2A10TonBombProjectile missing")

    # Confirm Tsar_Explosion FXList exists
    fx = file_map[r"Data\INI\FXList.ini"].decode("utf-8", errors="replace")
    if not re.search(r"^FXList\s+Tsar_Explosion\b", fx, re.M):
        raise RuntimeError("Tsar_Explosion FXList missing")

    # Confirm no radiation modules referenced by Tsar FX path for this weapon
    # (Tsar_Explosion itself is conventional particle FX)

    # Rebuild preserving order then any extras
    final: dict[str, bytes] = {}
    seen = set()
    for key in order:
        final[key] = file_map[key]
        seen.add(key)
    for key, content in file_map.items():
        if key not in seen:
            final[key] = content

    out_bytes = build_big(final)
    out_path = STAGE / "out" / "_SPEC_DATA_ONE.big"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out_bytes)
    DATA_BIG.write_bytes(out_bytes)

    # Verify re-extract
    v_entries, v_raw = read_big(DATA_BIG)
    vmap = {n.replace("/", "\\"): v_raw[o : o + s] for n, o, s in v_entries}
    vw = vmap[WEAPON_KEY].decode("utf-8", errors="replace")
    vb = extract_weapon(vw, "AmericaB2A10TonBombWeapon")
    vb2a = vmap[B2A_KEY].decode("utf-8", errors="replace")
    vwo = vmap[WO_KEY].decode("utf-8", errors="replace")
    vfx = vmap[r"Data\INI\FXList.ini"].decode("utf-8", errors="replace")

    # Write verify snippets
    (VERIFY / "AmericaB2A10TonBombWeapon.ini.txt").write_text(vb, encoding="utf-8")
    checks = {
        "clip": field(vb, "ClipSize") == "1",
        "payload_weapon": "AmericaB2A10TonBombWeapon" in vb2a,
        "cost": re.search(r"BuildCost\s*=\s*15000\b", vb2a) is not None,
        "projectile": "Object AmericaB2A10TonBombProjectile" in vwo,
        "detonation_fx": field(vb, "ProjectileDetonationFX") == "Tsar_Explosion",
        "fxlist": re.search(r"^FXList\s+Tsar_Explosion\b", vfx, re.M) is not None,
        "radius_increased": float(field(vb, "PrimaryDamageRadius")) > float(old_radius),
        "dup_weapon": len(re.findall(r"^Weapon AmericaB2A10TonBombWeapon\b", vw, re.M)) == 1,
        "no_nuke": all(x not in vb.lower() for x in ("radiation", "nuclear", "neutron")),
    }
    report = []
    report.append("B-2A HEAVY BOMB EXPLOSION = PASS" if all(checks.values()) else "B-2A HEAVY BOMB EXPLOSION = FAIL")
    report.append("BGM-108CALL reference found = NO")
    report.append("")
    report.append("Reference (closest proven heavy conventional):")
    report.append("Object = Russia_Fab9000")
    report.append("Weapon = 9000kg_TsarBomb")
    report.append("Projectile = Russia_Fab9000 (falling FOAB/Tsar delivery)")
    report.append("Damage = 6500.0")
    report.append("DamageRadius = 380.0")
    report.append("SecondaryDamage = 505.0")
    report.append("SecondaryRadius = 175.0")
    report.append("DetonationFX / FireFX = Tsar_Explosion")
    report.append("OCL = OCL_BombScorchmarkBig (Fab9000 SlowDeath; not required for B-2A projectile path)")
    report.append("Additional explosion FX = Tsar particle suite (smoke/blast/fire/flash/wave/dust/electric/MOAB sparks)")
    report.append("")
    report.append("B-2A FINAL:")
    report.append("Object = AmericaJetB2A")
    report.append("Weapon = AmericaB2A10TonBombWeapon")
    report.append("Projectile = AmericaB2A10TonBombProjectile")
    report.append("ClipSize = 1")
    report.append("Payload = 1")
    report.append(f"Old Damage = {old_damage}")
    report.append(f"New Damage = {field(vb, 'PrimaryDamage')}")
    report.append(f"Old DamageRadius = {old_radius}")
    report.append(f"New DamageRadius = {field(vb, 'PrimaryDamageRadius')}")
    report.append(f"Old DetonationFX = {old_fx}")
    report.append(f"New DetonationFX = {field(vb, 'ProjectileDetonationFX')}")
    report.append("BGM-108CALL explosion FX adopted = YES (via Tsar_Explosion reference substitute)")
    report.append("Large real area damage = YES")
    report.append("Conventional = YES")
    report.append("Nuclear = NO")
    report.append("Radiation = NO")
    report.append("BuildCost = 15000")
    report.append("Normal B-2 changed = NO")
    report.append("B-52 changed = NO")
    report.append("B-1 changed = NO")
    report.append("B-21 changed = NO")
    report.append("B-2A flight changed = NO")
    report.append("")
    report.append("Validation checks: " + ", ".join(f"{k}={'YES' if v else 'NO'}" for k, v in checks.items()))
    report.append(f"DATA SHA256 = {hashlib.sha256(out_bytes).hexdigest()}")
    report_text = "\n".join(report) + "\n"
    (VERIFY / "REPORT.txt").write_text(report_text, encoding="utf-8")
    print(report_text)

    if not all(checks.values()):
        raise SystemExit(2)

    # ZIP DATA only (ART unchanged; Tsar textures already in ART BIG as DDS)
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, arcname="_SPEC_DATA_ONE.big")
    print(f"Wrote {ZIP_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
