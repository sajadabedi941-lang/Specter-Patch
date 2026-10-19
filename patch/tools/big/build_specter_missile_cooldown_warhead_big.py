#!/usr/bin/env python3
"""Build 0_SPECTER_MissileCooldown.big from live _SPEC_DATA_ONE.

Task 1: set DelayBetweenShots = 300000 on every factory A-J PRIMARY weapon.
         ClipReloadTime 300000 / ClipSize 1 / AutoReloadsClip Yes are kept.
Task 2: scale splash, shockwave, detonation FX, and Death HACK radius for
         factory missiles whose configured warhead mass (PrimaryDamage / 5)
         exceeds 4000 kg. PrimaryDamage itself is not changed.

Effective last-wins for SPECTER missiles is:
  Data\\INI\\Weapon.ini
  then Data\\INI\\Weapon\\*.ini (TheWeaponStore loads the subdirectory after).
The overlay therefore ships both the named Weapon.ini and the 26 subdirectory
fragments so the cooldown and heavy-warhead radii are not overwritten.

Does not rewrite _SPEC_DATA_ONE.big, ART, or the 59 RAR volumes.
Does not insert new INI keys (CRLF End-insert previously glued Weapon headers).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FACTORY_WEAPON_LIST = SCRIPT_DIR / "factory_aj_launch_weapons.json"

COOLDOWN_MS = "300000"
MASS_SCALE_KG = 400.0
HEAVY_MASS_KG = 4000.0
FX_MID = "FX_LargeWarheadsExplosion2"
FX_HEAVY = "FX_HeavyWarheadCruiseMissileExplosion"
WEAPON_INI_KEY = "data\\ini\\weapon.ini"
WEAPON_DIR_PREFIX = "data\\ini\\weapon\\"
WEAPON_INI_NAME = "Data\\INI\\Weapon.ini"

CONTROL_WEAPONS = (
    "PatriotMissileWeapon",
    "ScorpionTankGun",
    "AmericaTankMissileWeapon",
    "Weapon_Iraq_AlHaitham_AlAbid",
    "Weapon_Iraq_AlHaitham_Hussiean",
)


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


def norm_key(name: str) -> str:
    return name.replace("/", "\\").lower()


def weapon_header_name(raw: str) -> str:
    return raw.strip("\r")


def iter_weapon_spans(text: str):
    pat = re.compile(r"(?mi)^Weapon\s+(\S+)")
    matches = list(pat.finditer(text))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        yield start, end, weapon_header_name(m.group(1))


def parse_blocks(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for start, end, name in iter_weapon_spans(text):
        if name == "=":
            continue
        out[name] = text[start:end]
    return out


def field(block: str, name: str) -> str | None:
    m = re.search(rf"(?mi)^\s*{re.escape(name)}\s*=\s*(.+?)\s*$", block)
    if not m:
        return None
    return m.group(1).split(";", 1)[0].strip()


def set_field(block: str, name: str, value: str) -> str:
    """Replace an existing field. Never insert: CRLF End-insert glued headers."""
    pat = re.compile(rf"(?mi)^(\s*{re.escape(name)}\s*=\s*)(\S+)(.*)$")
    if not pat.search(block):
        raise ValueError(f"missing field {name} in weapon block")
    return pat.sub(lambda mm: mm.group(1) + value + mm.group(3), block, count=1)


def cube_ratio(mass_kg: float) -> float:
    return (mass_kg / MASS_SCALE_KG) ** (1.0 / 3.0)


def capped(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def fmt_num(value: float) -> str:
    rounded = round(value, 1)
    if abs(rounded - round(rounded)) < 1e-9:
        return str(int(round(rounded)))
    return f"{rounded:.1f}"


def mass_kg_of(block: str) -> float:
    pd = float(field(block, "PrimaryDamage") or "0")
    return pd / 5.0


def apply_cooldown(block: str) -> str:
    block = set_field(block, "DelayBetweenShots", COOLDOWN_MS)
    if field(block, "ClipReloadTime") != COOLDOWN_MS:
        block = set_field(block, "ClipReloadTime", COOLDOWN_MS)
    return block


def apply_heavy_launch(block: str, mass: float) -> tuple[str, dict]:
    ratio = cube_ratio(mass)
    old = {
        "PrimaryDamageRadius": field(block, "PrimaryDamageRadius"),
        "SecondaryDamageRadius": field(block, "SecondaryDamageRadius"),
        "ShockWaveAmount": field(block, "ShockWaveAmount"),
        "ShockWaveRadius": field(block, "ShockWaveRadius"),
        "ProjectileDetonationFX": field(block, "ProjectileDetonationFX"),
    }
    pdr = fmt_num(capped(80.0 * ratio, 80.0, 240.0))
    sdr = fmt_num(capped(10.0 * ratio, 10.0, 50.0))
    shock_a = fmt_num(capped(680.0 * ratio, 680.0, 1600.0))
    shock_r = fmt_num(capped(150.0 * ratio, 150.0, 380.0))
    fx = FX_HEAVY if mass > 6000 else FX_MID
    block = set_field(block, "PrimaryDamageRadius", pdr)
    block = set_field(block, "SecondaryDamageRadius", sdr)
    if field(block, "ShockWaveAmount") is not None:
        block = set_field(block, "ShockWaveAmount", shock_a)
    if field(block, "ShockWaveRadius") is not None:
        block = set_field(block, "ShockWaveRadius", shock_r)
    if field(block, "ProjectileDetonationFX") is not None:
        block = set_field(block, "ProjectileDetonationFX", fx)
    new = {
        "PrimaryDamageRadius": field(block, "PrimaryDamageRadius"),
        "SecondaryDamageRadius": field(block, "SecondaryDamageRadius"),
        "ShockWaveAmount": field(block, "ShockWaveAmount"),
        "ShockWaveRadius": field(block, "ShockWaveRadius"),
        "ProjectileDetonationFX": field(block, "ProjectileDetonationFX"),
    }
    return block, {"old": old, "new": new, "ratio": round(ratio, 4)}


def apply_heavy_warhead(block: str, mass: float) -> tuple[str, dict]:
    ratio = cube_ratio(mass)
    old_r = field(block, "PrimaryDamageRadius")
    hack_r = fmt_num(capped(20.0 * ratio, 20.0, 70.0))
    block = set_field(block, "PrimaryDamageRadius", hack_r)
    return block, {
        "old_radius": old_r,
        "new_radius": field(block, "PrimaryDamageRadius"),
        "damage_type": field(block, "DamageType"),
        "primary_damage_unchanged": field(block, "PrimaryDamage"),
    }


def patch_ini_text(text: str, factory: set[str], mass_by_weapon: dict[str, float]) -> str:
    """Surgically rewrite factory launch/warhead blocks; keep every other byte."""
    pieces: list[str] = []
    cursor = 0
    local_mass = dict(mass_by_weapon)
    for start, end, name in iter_weapon_spans(text):
        pieces.append(text[cursor:start])
        block = text[start:end]
        if name in factory:
            local_mass[name] = mass_kg_of(block)
            block = apply_cooldown(block)
            if local_mass[name] > HEAVY_MASS_KG:
                block, _ = apply_heavy_launch(block, local_mass[name])
        elif name.endswith("_Warhead"):
            launch = name[: -len("_Warhead")]
            mass = local_mass.get(launch)
            if mass is None and launch in factory:
                # Warhead may appear before launch in a file; mass filled later
                # from the global map (Weapon.ini / earlier fragment).
                mass = mass_by_weapon.get(launch)
            if launch in factory and mass is not None and mass > HEAVY_MASS_KG:
                block, _ = apply_heavy_warhead(block, mass)
        pieces.append(block)
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)


def last_wins_weapons(file_map: dict[str, bytes]) -> dict[str, str]:
    """Weapon.ini first, then Data\\INI\\Weapon\\* alphabetically."""
    items = [(norm_key(n), n, blob) for n, blob in file_map.items()]
    weapon_ini = [x for x in items if x[0] == WEAPON_INI_KEY]
    frags = sorted(
        [x for x in items if x[0].startswith(WEAPON_DIR_PREFIX)],
        key=lambda t: t[0],
    )
    blocks: dict[str, str] = {}
    for _, _, blob in weapon_ini + frags:
        blocks.update(parse_blocks(blob.decode("latin1")))
    return blocks


def collect_source_files(entries, raw) -> dict[str, bytes]:
    out = {}
    for name, off, size in entries:
        key = norm_key(name)
        if key == WEAPON_INI_KEY or key.startswith(WEAPON_DIR_PREFIX):
            out[name.replace("/", "\\")] = raw[off : off + size]
    return out


def unique_real_names(text: str) -> set[str]:
    names = [name for _, _, name in iter_weapon_spans(text) if name != "="]
    return set(names)


def header_line_count(text: str) -> int:
    return sum(1 for _ in iter_weapon_spans(text))


def validate(
    source_files: dict[str, bytes],
    overlay_files: dict[str, bytes],
    factory: list[str],
    fx_text: str,
) -> dict:
    errors: list[str] = []
    factory_set = set(factory)

    old_ini = source_files[WEAPON_INI_NAME].decode("latin1")
    new_ini = overlay_files[WEAPON_INI_NAME].decode("latin1")
    if "EndWeapon" in new_ini:
        errors.append("Weapon.ini contains glued EndWeapon headers")
    old_names = unique_real_names(old_ini)
    new_names = unique_real_names(new_ini)
    if old_names != new_names:
        errors.append(
            f"Weapon.ini real names changed: missing {sorted(old_names - new_names)[:6]} extra {sorted(new_names - old_names)[:6]}"
        )
    if header_line_count(old_ini) != header_line_count(new_ini):
        errors.append(
            f"Weapon.ini header count {header_line_count(old_ini)} -> {header_line_count(new_ini)}"
        )

    if set(overlay_files) != set(source_files):
        errors.append(
            f"overlay file set mismatch extra={sorted(set(overlay_files)-set(source_files))} missing={sorted(set(source_files)-set(overlay_files))}"
        )

    for rel in overlay_files:
        if "EndWeapon" in overlay_files[rel].decode("latin1"):
            errors.append(f"{rel} contains glued EndWeapon headers")

    old_eff = last_wins_weapons(source_files)
    new_eff = last_wins_weapons(overlay_files)

    delay_ok = 0
    light_radius_changed = []
    missing = []
    for name in factory:
        if name not in new_eff:
            missing.append(name)
            continue
        blk = new_eff[name]
        if field(blk, "DelayBetweenShots") != COOLDOWN_MS:
            errors.append(f"{name} DelayBetweenShots={field(blk, 'DelayBetweenShots')}")
        else:
            delay_ok += 1
        if field(blk, "ClipSize") != "1":
            errors.append(f"{name} ClipSize={field(blk, 'ClipSize')}")
        if field(blk, "AutoReloadsClip") != "Yes":
            errors.append(f"{name} AutoReloadsClip={field(blk, 'AutoReloadsClip')}")
        if field(blk, "ClipReloadTime") != COOLDOWN_MS:
            errors.append(f"{name} ClipReloadTime={field(blk, 'ClipReloadTime')}")
        mass = mass_kg_of(blk)
        if mass <= HEAVY_MASS_KG:
            old_pdr = field(old_eff[name], "PrimaryDamageRadius")
            new_pdr = field(blk, "PrimaryDamageRadius")
            if old_pdr != new_pdr:
                light_radius_changed.append((name, old_pdr, new_pdr))
            old_pd = field(old_eff[name], "PrimaryDamage")
            new_pd = field(blk, "PrimaryDamage")
            if old_pd != new_pd:
                errors.append(f"{name} PrimaryDamage changed {old_pd} -> {new_pd}")
    if missing:
        errors.append(f"factory weapons missing from last-wins: {missing[:8]}")
    if light_radius_changed:
        errors.append(f"non-heavy radius changed: {light_radius_changed[:4]}")

    heavies = []
    for name in factory:
        blk = new_eff[name]
        mass = mass_kg_of(blk)
        if mass <= HEAVY_MASS_KG:
            continue
        old_pdr = float(field(old_eff[name], "PrimaryDamageRadius") or "0")
        new_pdr = float(field(blk, "PrimaryDamageRadius") or "0")
        if new_pdr <= old_pdr:
            errors.append(f"{name} heavy PDR did not increase ({old_pdr} -> {new_pdr})")
        if field(blk, "PrimaryDamage") != field(old_eff[name], "PrimaryDamage"):
            errors.append(f"{name} heavy PrimaryDamage changed")
        fx = field(blk, "ProjectileDetonationFX")
        want = FX_HEAVY if mass > 6000 else FX_MID
        if fx != want:
            errors.append(f"{name} FX {fx} != {want}")
        if fx_text and fx not in fx_text:
            errors.append(f"{name} FX {fx} not found in FXList.ini")
        wh_name = name + "_Warhead"
        wh = new_eff.get(wh_name)
        wh_info = None
        if wh is None:
            errors.append(f"{name} missing last-wins warhead {wh_name}")
        else:
            old_wh_r = float(field(old_eff[wh_name], "PrimaryDamageRadius") or "0")
            new_wh_r = float(field(wh, "PrimaryDamageRadius") or "0")
            if new_wh_r <= old_wh_r:
                errors.append(f"{wh_name} HACK radius did not increase ({old_wh_r} -> {new_wh_r})")
            if field(wh, "PrimaryDamage") != field(old_eff[wh_name], "PrimaryDamage"):
                errors.append(f"{wh_name} PrimaryDamage changed")
            wh_info = {
                "PrimaryDamageRadius": field(wh, "PrimaryDamageRadius"),
                "DamageType": field(wh, "DamageType"),
                "PrimaryDamage": field(wh, "PrimaryDamage"),
            }
        heavies.append(
            {
                "weapon": name,
                "warhead": wh_name,
                "mass_kg": round(mass, 1),
                "primary_damage_unchanged": field(blk, "PrimaryDamage"),
                "old": {
                    "PrimaryDamageRadius": field(old_eff[name], "PrimaryDamageRadius"),
                    "SecondaryDamageRadius": field(old_eff[name], "SecondaryDamageRadius"),
                    "ShockWaveAmount": field(old_eff[name], "ShockWaveAmount"),
                    "ShockWaveRadius": field(old_eff[name], "ShockWaveRadius"),
                    "ProjectileDetonationFX": field(old_eff[name], "ProjectileDetonationFX"),
                },
                "new": {
                    "PrimaryDamageRadius": field(blk, "PrimaryDamageRadius"),
                    "SecondaryDamageRadius": field(blk, "SecondaryDamageRadius"),
                    "ShockWaveAmount": field(blk, "ShockWaveAmount"),
                    "ShockWaveRadius": field(blk, "ShockWaveRadius"),
                    "ProjectileDetonationFX": field(blk, "ProjectileDetonationFX"),
                },
                "warhead_new": wh_info,
            }
        )

    for ctrl in CONTROL_WEAPONS:
        if ctrl not in old_eff:
            continue
        if old_eff[ctrl] != new_eff.get(ctrl):
            errors.append(f"unrelated weapon changed: {ctrl}")

    if delay_ok != 250:
        errors.append(f"cooldown coverage {delay_ok}/250")
    if len(heavies) != 16:
        errors.append(f"heavy count {len(heavies)} != 16")

    return {
        "errors": errors,
        "factory_launch_weapons": delay_ok,
        "heavy_warheads": heavies,
        "weapon_ini_real_names": len(new_names),
        "weapon_ini_headers": header_line_count(new_ini),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--data-big",
        type=Path,
        default=Path("/tmp/sp_work/SPECTER FINAL (GeneralsMode.com)/_SPEC_DATA_ONE.big"),
    )
    ap.add_argument(
        "--out-big",
        type=Path,
        default=Path("/workspace/patch/tools/installer/0_SPECTER_MissileCooldown.big"),
    )
    ap.add_argument(
        "--manifest",
        type=Path,
        default=Path("/workspace/patch/tools/installer/MISSILE_COOLDOWN_MANIFEST.json"),
    )
    args = ap.parse_args()

    entries, raw = read_big(args.data_big)
    source_files = collect_source_files(entries, raw)
    if WEAPON_INI_NAME not in source_files:
        raise SystemExit("Weapon.ini not found in DATA BIG")
    if len(source_files) != 27:
        raise SystemExit(f"expected Weapon.ini + 26 fragments, found {len(source_files)}")

    factory_launch = json.loads(FACTORY_WEAPON_LIST.read_text())
    if len(factory_launch) != 250:
        raise SystemExit(f"expected 250 factory A-J launch weapons, found {len(factory_launch)}")

    fx_text = ""
    for name, off, size in entries:
        if norm_key(name) == "data\\ini\\fxlist.ini":
            fx_text = raw[off : off + size].decode("latin1", errors="replace")
            break
    for fx in (FX_MID, FX_HEAVY, "FX_SmallSRBM_Explosion"):
        if not re.search(rf"(?mi)^FXList\s+{re.escape(fx)}\b", fx_text):
            raise SystemExit(f"FX {fx} missing from packed FXList.ini")

    source_blocks = last_wins_weapons(source_files)
    missing = [name for name in factory_launch if name not in source_blocks]
    if missing:
        raise SystemExit(f"factory weapons missing from last-wins Weapon store: {missing[:8]}")

    mass_by_weapon = {name: mass_kg_of(source_blocks[name]) for name in factory_launch}

    overlay_files: dict[str, bytes] = {}
    # Patch Weapon.ini first, then fragments, using last-wins masses.
    overlay_files[WEAPON_INI_NAME] = patch_ini_text(
        source_files[WEAPON_INI_NAME].decode("latin1"),
        set(factory_launch),
        mass_by_weapon,
    ).encode("latin1")
    for rel, blob in sorted(source_files.items()):
        if rel == WEAPON_INI_NAME:
            continue
        overlay_files[rel] = patch_ini_text(
            blob.decode("latin1"),
            set(factory_launch),
            mass_by_weapon,
        ).encode("latin1")

    report = validate(source_files, overlay_files, factory_launch, fx_text)
    if report["errors"]:
        raise SystemExit("validation failed:\n  " + "\n  ".join(report["errors"]))

    packed = build_big(overlay_files)
    args.out_big.parent.mkdir(parents=True, exist_ok=True)
    args.out_big.write_bytes(packed)

    manifest = {
        "overlay": str(args.out_big.name),
        "files": sorted(overlay_files),
        "sha256": hashlib.sha256(packed).hexdigest(),
        "bytes": len(packed),
        "factory_launch_weapons": report["factory_launch_weapons"],
        "cooldown_delay_ms": int(COOLDOWN_MS),
        "heavy_warheads": report["heavy_warheads"],
        "weapon_ini_real_names": report["weapon_ini_real_names"],
        "weapon_ini_headers": report["weapon_ini_headers"],
        "scale": "400 kg -> PrimaryDamage 2000; mass = PrimaryDamage / 5; radii scale by (mass/400)^(1/3)",
        "notes": [
            "DelayBetweenShots is the live fire interval for ClipSize=1 FIRE_WEAPON.",
            "ClipReloadTime 300000 is preserved so whichever engine path is used waits 300s.",
            "Data\\INI\\Weapon\\*.ini last-wins fragments are included so Weapon.ini is not overwritten.",
            "PrimaryDamage / AttackRange / cost / models are unchanged.",
            "Weapons at or below 4000 kg are not radius-scaled.",
            "No new INI keys are inserted.",
        ],
    }
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"factory launch weapons: {report['factory_launch_weapons']}")
    print(f"heavy warheads >4000 kg: {len(report['heavy_warheads'])}")
    print(f"overlay files: {len(overlay_files)}")
    print(f"wrote {args.out_big} ({len(packed)} bytes)")
    print(f"sha256 {manifest['sha256']}")
    for h in report["heavy_warheads"]:
        print(
            f"  {h['weapon']} mass={h['mass_kg']}kg PDR {h['old']['PrimaryDamageRadius']} -> {h['new']['PrimaryDamageRadius']} FX {h['new']['ProjectileDetonationFX']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
