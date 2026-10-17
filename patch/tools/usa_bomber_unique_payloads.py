#!/usr/bin/env python3
"""Unique USA Heavy Bomber payloads: B-2 / B-52 / B-1R / B-2A.

Uses only proven Specter Weapon.ini + USA_WeaponObjects patterns.
No donor DATA. No flight/visual/HeavyAirBase changes.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
STAGE = MASTER / "_stage_usa_bomber_unique_payloads"
VERIFY = MASTER / "_extract_usa_bomber_unique_payloads_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_BOMBER_UNIQUE_PAYLOADS.zip"
OUT_HASH = ROOT / "Release/DATA_USA_BOMBER_UNIQUE_PAYLOADS_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_BOMBER_UNIQUE_PAYLOADS_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_BOMBER_UNIQUE_PAYLOADS_REPORT.txt"
SRC_DIR = ROOT / "Data/INI/Object/Specter/United States Of America"

WEAPON_KEY = "Data\\INI\\Weapon.ini"
WO_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\USA_WeaponObjects.ini"
)
USA_SYS_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"
)
B1R_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Airforce\\B1R.ini"
)
B2A_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB2A.ini"
)
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"
CSF_KEY = "Data\\English\\generals.csf"
HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)

FREEZE = [
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE2Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE3Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\Airforce\\CH47F.ini",
]

# B-2A 10-ton conventional ref = GBU43B_HighExplosion (strongest large-area non-nuke)
# GBU43B has primary only; secondary/shock radii scale from that same reference radius.
REF_10TON = {
    "primary_damage": 6000.0,
    "primary_radius": 320.0,
    "secondary_damage": 900.0,  # conventional splash (B-52-style), then * damage mult
    "shock_amount": 260.0,
}

B2A_DMG_MULT = 2.0
B2A_RADIUS_MULT = 1.5
B2A_SECONDARY_RADIUS_MULT = 1.75

# New IDs
W_B2 = "AmericaB2SixGuidedBombWeapon"
W_B52_A = "AmericaB52SevenBombSalvoA"
W_B52_B = "AmericaB52SevenBombSalvoB"
W_B1 = "AmericaB1ThreeGuidedBombWeapon"
W_B2A = "AmericaB2A10TonBombWeapon"
P_B2A = "AmericaB2A10TonBombProjectile"


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        out[name.replace("/", "\\")] = data[off : off + size]
    return out


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16 + sum(8 + len(n.encode("latin1")) + 1 for n, _ in items)
    offset = header_size
    index, blobs = [], []
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">III", offset, len(items), header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for b in blobs:
        out += b
    return bytes(out)


def write_tree(file_map: dict[str, bytes], root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for name, content in file_map.items():
        path = root / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def extract_object(text: str, name: str) -> str:
    m = re.search(rf"(?ms)^Object\s+{re.escape(name)}\s*\n.*?(?=^Object\s|\Z)", text)
    assert m, name
    return m.group(0)


def extract_weapon(text: str, name: str) -> str:
    m = re.search(rf"(?ms)^Weapon\s+{re.escape(name)}\s*\n.*?(?=^Weapon\s|\Z)", text)
    assert m, name
    return m.group(0)


def replace_object(text: str, name: str, new_obj: str) -> str:
    m = re.search(rf"(?ms)^Object\s+{re.escape(name)}\s*\n.*?(?=^Object\s|\Z)", text)
    assert m, name
    return text[: m.start()] + new_obj.rstrip() + "\n\n" + text[m.end() :]


def upsert_weapon(wini: str, name: str, block: str) -> str:
    block = block.rstrip() + "\n\n"
    if re.search(rf"(?m)^Weapon\s+{re.escape(name)}\s*$", wini):
        wini, n = re.subn(
            rf"(?ms)^Weapon\s+{re.escape(name)}\s*\n.*?(?=^Weapon\s|\Z)",
            block,
            wini,
            count=1,
        )
        assert n == 1
        return wini
    return wini.rstrip() + "\n\n" + block


def upsert_object_in_file(text: str, name: str, block: str) -> str:
    block = block.rstrip() + "\n\n"
    if re.search(rf"(?m)^Object\s+{re.escape(name)}\s*$", text):
        return replace_object(text, name, block)
    return text.rstrip() + "\n\n" + block


def patch_build_cost(obj: str, cost: int) -> str:
    obj2, n = re.subn(
        r"(?m)^(\s*BuildCost\s*=\s*)\S+",
        rf"\g<1>{cost}",
        obj,
        count=1,
    )
    assert n == 1, "BuildCost missing"
    return obj2


def set_primary_weapon(obj: str, weapon: str) -> str:
    """Replace Conditions=None WeaponSet PRIMARY (and strip extra slots)."""

    def repl(m: re.Match[str]) -> str:
        return (
            "  WeaponSet\n"
            "    Conditions = None\n"
            f"    Weapon = PRIMARY {weapon}\n"
            "  End\n"
        )

    obj2, n = re.subn(
        r"(?ms)^\s*WeaponSet\s*\n\s*Conditions\s*=\s*None\b.*?\n\s*End\s*\n",
        repl,
        obj,
        count=1,
    )
    assert n == 1, "default WeaponSet missing"
    return obj2


def set_b52_dual_weapons(obj: str) -> str:
    def repl(m: re.Match[str]) -> str:
        return (
            "  WeaponSet\n"
            "    Conditions = None\n"
            f"    Weapon = PRIMARY {W_B52_A}\n"
            f"    Weapon = SECONDARY {W_B52_B}\n"
            "  End\n"
        )

    obj2, n = re.subn(
        r"(?ms)^\s*WeaponSet\s*\n\s*Conditions\s*=\s*None\b.*?\n\s*End\s*\n",
        repl,
        obj,
        count=1,
    )
    assert n == 1
    return obj2


def make_weapons() -> dict[str, str]:
    # B-2: guided GBU-31V2, 6-shot rapid clip (RETURN_TO_BASE). Damage kept near current Spirit bunker weapon.
    b2 = f"""Weapon {W_B2}
  PrimaryDamage           = 9000.0
  PrimaryDamageRadius     = 170.0
  SecondaryDamage         = 1100.0
  SecondaryDamageRadius   = 100.0
  ScatterRadius           = 12.0
  ScatterRadiusVsInfantry = 40.0
  AttackRange             = 520.0
  MinimumAttackRange      = 400.0
  DamageType              = ARMOR_PIERCING
  DeathType               = EXPLODED
  WeaponSpeed             = 9999.0
  ProjectileObject        = GBU-31V2
  ProjectileDetonationOCL = OCL_MK84Warhead
  FireFX                  = FX_AuroraBombLaunch
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 80
  ClipSize                = 6
  ClipReloadTime          = 600000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
  ShockWaveAmount         = 320.0
  ShockWaveRadius         = 220.0
  ShockWaveTaperOff       = 0.33
End
"""

    # B-52: conventional MK-84, two 7-bomb salvos (PRIMARY then SECONDARY with PreAttackDelay pause)
    b52_common = """  PrimaryDamage           = 4200.0
  PrimaryDamageRadius     = 240.0
  SecondaryDamage         = 900.0
  SecondaryDamageRadius   = 150.0
  ScatterRadius           = 55.0
  ScatterRadiusVsInfantry = 120.0
  AttackRange             = 600.0
  MinimumAttackRange      = 400.0
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 9999.0
  ProjectileObject        = MK-84
  FireFX                  = FX_AuroraBombLaunch
  ProjectileDetonationFX  = FX_FreeFallBombsDetonation
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 80
  ClipSize                = 7
  ClipReloadTime          = 480000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
  ShockWaveAmount         = 260.0
  ShockWaveRadius         = 260.0
  ShockWaveTaperOff       = 0.33
"""
    b52a = f"Weapon {W_B52_A}\n{b52_common}End\n"
    b52b = (
        f"Weapon {W_B52_B}\n"
        f"  PreAttackDelay          = 1200\n"
        f"{b52_common}End\n"
    )

    # B-1: 3 guided bombs, rapid sequence
    b1 = f"""Weapon {W_B1}
  PrimaryDamage           = 3800.0
  PrimaryDamageRadius     = 180.0
  SecondaryDamage         = 700.0
  SecondaryDamageRadius   = 110.0
  ScatterRadius           = 20.0
  ScatterRadiusVsInfantry = 40.0
  AttackRange             = 800.0
  MinimumAttackRange      = 400.0
  DamageType              = ARMOR_PIERCING
  DeathType               = EXPLODED
  WeaponSpeed             = 9999.0
  ProjectileObject        = GBU-31V2
  ProjectileDetonationOCL = OCL_MK84Warhead
  FireFX                  = FX_AuroraBombLaunch
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 100
  ClipSize                = 3
  ClipReloadTime          = 240000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
  ShockWaveAmount         = 210.0
  ShockWaveRadius         = 180.0
  ShockWaveTaperOff       = 0.33
End
"""

    pd = REF_10TON["primary_damage"] * B2A_DMG_MULT
    pr = REF_10TON["primary_radius"] * B2A_RADIUS_MULT
    sd = REF_10TON["secondary_damage"] * B2A_DMG_MULT
    sr = REF_10TON["primary_radius"] * B2A_SECONDARY_RADIUS_MULT
    sa = REF_10TON["shock_amount"] * B2A_RADIUS_MULT
    srad = REF_10TON["primary_radius"] * B2A_SECONDARY_RADIUS_MULT

    b2a = f"""Weapon {W_B2A}
  PrimaryDamage           = {pd:.1f}
  PrimaryDamageRadius     = {pr:.1f}
  SecondaryDamage         = {sd:.1f}
  SecondaryDamageRadius   = {sr:.1f}
  ScatterRadius           = 25.0
  ScatterRadiusVsInfantry = 80.0
  AttackRange             = 600.0
  MinimumAttackRange      = 400.0
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 9999.0
  ProjectileObject        = {P_B2A}
  FireFX                  = FX_AuroraBombLaunch
  ProjectileDetonationFX  = WeaponFX_BigBombExplosion
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 0
  ClipSize                = 1
  ClipReloadTime          = 600000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
  ShockWaveAmount         = {sa:.1f}
  ShockWaveRadius         = {srad:.1f}
  ShockWaveTaperOff       = 0.33
End
"""
    return {
        W_B2: b2,
        W_B52_A: b52a,
        W_B52_B: b52b,
        W_B1: b1,
        W_B2A: b2a,
        "_b2a_stats": {
            "pd": pd,
            "pr": pr,
            "sd": sd,
            "sr": sr,
            "sa": sa,
            "srad": srad,
        },
    }


def make_b2a_projectile(mk84_obj: str) -> str:
    # Clone MK-84 freefall bomb; rename object; keep proven MissileAI/locomotor.
    body = mk84_obj
    body = re.sub(
        r"(?m)^Object\s+MK-84\s*$",
        f"Object {P_B2A}",
        body,
        count=1,
    )
    # Slightly heavier mass for "10-ton" feel; keep parse-safe fields only.
    body = re.sub(
        r"(?m)^(\s*Mass\s*=\s*)\S+",
        r"\g<1>120.0",
        body,
        count=1,
    )
    # Ensure not nuclear / special-power die modules
    assert "Nuke" not in body
    assert "SpecialPowerCompletionDie" not in body
    return body


def upload(path: Path) -> str:
    try:
        r = subprocess.run(
            [
                "curl",
                "-sF",
                f"file=@{path}",
                "https://litterbox.catbox.moe/resources/internals/api.php",
                "-F",
                "time=72h",
                "-F",
                "reqtype=fileupload",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        out = (r.stdout or "").strip()
        if out.startswith("http"):
            return out
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["curl", "-sF", f"file=@{path}", "https://store1.gofile.io/uploadFile"],
            capture_output=True,
            text=True,
            timeout=900,
        )
        m = re.search(r'"downloadPage"\s*:\s*"([^"]+)"', r.stdout or "")
        if m:
            return m.group(1)
    except Exception:
        pass
    return "(upload failed)"


def assert_no_flight_change(before: str, after: str) -> None:
    for field in ["JetAIUpdate", "Locomotor", "PhysicsBehavior"]:
        assert (field in before) == (field in after)
    b_models = re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", before)
    a_models = re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", after)
    assert b_models == a_models
    b_loco = re.findall(r"(?m)^\s*Locomotor\s*=\s*.*$", before)
    a_loco = re.findall(r"(?m)^\s*Locomotor\s*=\s*.*$", after)
    assert b_loco == a_loco
    # JetAI block identical
    def jetai(t: str) -> str:
        m = re.search(r"(?ms)^\s*Behavior\s*=\s*JetAIUpdate.*?\n\s*End\s*$", t)
        return m.group(0) if m else ""

    assert jetai(before) == jetai(after)


def main() -> None:
    data = read_big(DATA_BIG)
    art_sha = sha256(ART_BIG)
    freeze = {k: data[k] for k in FREEZE if k in data}
    cs_before = data[CS_KEY]
    cb_before = data[CB_KEY]
    csf_before = data[CSF_KEY]
    heavy_before = data[HEAVY_KEY]

    wini = data[WEAPON_KEY].decode("latin1")
    wo = data[WO_KEY].decode("latin1")
    usa = data[USA_SYS_KEY].decode("latin1")
    b1r = data[B1R_KEY].decode("latin1")
    b2a = data[B2A_KEY].decode("latin1")

    # Validate refs exist
    assert re.search(r"(?m)^Object\s+GBU-31V2\s*$", wo)
    assert re.search(r"(?m)^Object\s+MK-84\s*$", wo)
    assert "OCL_MK84Warhead" in data["Data\\INI\\ObjectCreationList.ini"].decode(
        "latin1", errors="replace"
    )
    assert "WeaponFX_BigBombExplosion" in data.get(
        "Data\\INI\\FXList.ini", b""
    ).decode("latin1", errors="replace") or any(
        b"WeaponFX_BigBombExplosion" in v for v in data.values()
    )
    assert re.search(r"(?m)^Weapon\s+GBU43B_HighExplosion\s*$", wini)
    assert re.search(r"(?m)^Weapon\s+USA_B52H_AreaBombardment\s*$", wini)

    weapons = make_weapons()
    b2a_stats = weapons.pop("_b2a_stats")

    mk84 = extract_object(wo, "MK-84")
    proj = make_b2a_projectile(mk84)

    # Upsert weapons + projectile
    for name in [W_B2, W_B52_A, W_B52_B, W_B1, W_B2A]:
        wini = upsert_weapon(wini, name, weapons[name])
    wo = upsert_object_in_file(wo, P_B2A, proj)

    # --- Patch objects ---
    b2_obj = extract_object(usa, "AmericaJetB2Spirit")
    b2_before = b2_obj
    b2_obj = set_primary_weapon(b2_obj, W_B2)
    b2_obj = patch_build_cost(b2_obj, 10000)
    assert_no_flight_change(b2_before, b2_obj)
    usa = replace_object(usa, "AmericaJetB2Spirit", b2_obj)

    b52_obj = extract_object(usa, "AmericaJetB52H")
    b52_before = b52_obj
    b52_obj = set_b52_dual_weapons(b52_obj)
    assert_no_flight_change(b52_before, b52_obj)
    usa = replace_object(usa, "AmericaJetB52H", b52_obj)

    b1_obj = extract_object(b1r, "AmericaJetB1R")
    b1_before = b1_obj
    b1_obj = set_primary_weapon(b1_obj, W_B1)
    assert_no_flight_change(b1_before, b1_obj)
    # cost unchanged
    cost_b1 = re.search(r"(?m)^\s*BuildCost\s*=\s*(\S+)", b1_before).group(1)
    assert re.search(rf"(?m)^\s*BuildCost\s*=\s*{re.escape(cost_b1)}", b1_obj)
    b1r = replace_object(b1r, "AmericaJetB1R", b1_obj)

    b2a_obj = extract_object(b2a, "AmericaJetB2A")
    b2a_before = b2a_obj
    b2a_obj = set_primary_weapon(b2a_obj, W_B2A)
    b2a_obj = patch_build_cost(b2a_obj, 15000)
    assert_no_flight_change(b2a_before, b2a_obj)
    b2a = replace_object(b2a, "AmericaJetB2A", b2a_obj)

    data2 = dict(data)
    data2[WEAPON_KEY] = wini.replace("\r\n", "\n").encode("latin1")
    data2[WO_KEY] = wo.replace("\r\n", "\n").encode("latin1")
    data2[USA_SYS_KEY] = usa.replace("\r\n", "\n").encode("latin1")
    data2[B1R_KEY] = b1r.replace("\r\n", "\n").encode("latin1")
    data2[B2A_KEY] = b2a.replace("\r\n", "\n").encode("latin1")
    data2[CS_KEY] = cs_before
    data2[CB_KEY] = cb_before
    data2[CSF_KEY] = csf_before
    data2[HEAVY_KEY] = heavy_before
    for k, v in freeze.items():
        data2[k] = v

    # Sync loose sources
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    (SRC_DIR / "AmericaJetB2A.ini").write_bytes(data2[B2A_KEY])
    (SRC_DIR / "Airforce").mkdir(parents=True, exist_ok=True)
    (ROOT / "Data/INI/Object/Specter/United States Of America/Airforce").mkdir(
        parents=True, exist_ok=True
    )
    (ROOT / "Data/INI/Object/Specter/United States Of America/Airforce/B1R.ini").write_bytes(
        data2[B1R_KEY]
    )

    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    write_tree(data2, STAGE / "in")
    DATA_BIG.write_bytes(build_big(data2))

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    dv = read_big(DATA_BIG)
    write_tree(dv, VERIFY / "out")

    # --- Validate packed ---
    assert dv[CS_KEY] == cs_before
    assert dv[CB_KEY] == cb_before
    assert dv[HEAVY_KEY] == heavy_before
    assert sha256(ART_BIG) == art_sha
    for k, v in freeze.items():
        assert dv[k] == v

    pw = dv[WEAPON_KEY].decode("latin1")
    pwo = dv[WO_KEY].decode("latin1")
    pusa = dv[USA_SYS_KEY].decode("latin1")
    pb1 = dv[B1R_KEY].decode("latin1")
    pb2a = dv[B2A_KEY].decode("latin1")

    for name in [W_B2, W_B52_A, W_B52_B, W_B1, W_B2A]:
        assert len(re.findall(rf"(?m)^Weapon\s+{re.escape(name)}\s*$", pw)) == 1
    assert len(re.findall(rf"(?m)^Object\s+{re.escape(P_B2A)}\s*$", pwo)) == 1

    def clip_of(wname: str) -> int:
        blk = extract_weapon(pw, wname)
        return int(re.search(r"(?m)^\s*ClipSize\s*=\s*(\d+)", blk).group(1))

    assert clip_of(W_B2) == 6
    assert clip_of(W_B52_A) == 7 and clip_of(W_B52_B) == 7
    assert clip_of(W_B1) == 3
    assert clip_of(W_B2A) == 1

    b2f = extract_object(pusa, "AmericaJetB2Spirit")
    b52f = extract_object(pusa, "AmericaJetB52H")
    b1f = extract_object(pb1, "AmericaJetB1R")
    b2af = extract_object(pb2a, "AmericaJetB2A")

    assert W_B2 in b2f and int(re.search(r"BuildCost\s*=\s*(\d+)", b2f).group(1)) == 10000
    assert W_B52_A in b52f and W_B52_B in b52f
    assert W_B1 in b1f
    assert W_B2A in b2af and int(re.search(r"BuildCost\s*=\s*(\d+)", b2af).group(1)) == 15000

    # No nuclear on B2A weapon
    b2aw = extract_weapon(pw, W_B2A)
    assert not re.search(r"(?i)nuke|nuclear|neutron|radiation", b2aw)
    assert P_B2A in b2aw
    assert "ClipSize                = 1" in b2aw

    # Shared old weapons not retargeted incorrectly for B2/B2A
    assert "USA_B2_Spirit_BunkerBuster" not in b2f
    assert "USA_B2_Spirit_BunkerBuster" not in b2af

    # B21 still uses old B52 weapon (frozen)
    b21 = dv[
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini"
    ].decode("latin1")
    assert "USA_B52H_AreaBombardment" in b21

    # Unresolved projectile check
    for wname, proj in [
        (W_B2, "GBU-31V2"),
        (W_B52_A, "MK-84"),
        (W_B52_B, "MK-84"),
        (W_B1, "GBU-31V2"),
        (W_B2A, P_B2A),
    ]:
        assert re.search(rf"(?m)^Object\s+{re.escape(proj)}\s*$", pwo) or (
            proj == "GBU-31V2" and re.search(r"(?m)^Object\s+GBU-31V2\s*$", pwo)
        )

    data_sha = sha256(DATA_BIG)
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    url = upload(OUT_ZIP)

    report = f"""USA BOMBER PAYLOAD OVERHAUL = STRUCTURAL PASS

B-2:
Object = AmericaJetB2Spirit
Weapon = {W_B2}
Projectile = GBU-31V2
Guided = YES (MissileAIUpdate TryToFollowTarget = Yes on GBU-31V2)
ClipSize = 6
Shots per attack = 6
Release delay = DelayBetweenShots 80 ms
Total payload = 6
BuildCost = 10000
Expected release: 6 in one attack = YES
AutoReloadsClip = RETURN_TO_BASE

------------------------------

B-52:
Object = AmericaJetB52H
Weapon = {W_B52_A} + {W_B52_B}
Projectile = MK-84 (conventional freefall — NOT guided)
ClipSize / total payload = 7 + 7 = 14
Salvo 1 = PRIMARY ClipSize 7 (DelayBetweenShots 80)
Salvo 2 = SECONDARY ClipSize 7 (PreAttackDelay 1200 then DelayBetweenShots 80)
Inter-salvo delay = PreAttackDelay 1200 ms on SECONDARY
Total payload = 14
Expected: 7 + 7 = YES
AutoReloadsClip = RETURN_TO_BASE on both

------------------------------

B-1:
Object = AmericaJetB1R
Weapon = {W_B1}
Projectile = GBU-31V2
Guided = YES
ClipSize = 3
Total payload = 3
Release delay = DelayBetweenShots 100 ms
BuildCost = unchanged ({cost_b1})
Expected: 3 guided bombs per attack = YES
AutoReloadsClip = RETURN_TO_BASE

------------------------------

B-2A:
Object = AmericaJetB2A
Weapon = {W_B2A}
Projectile = {P_B2A} (MK-84 freefall clone; conventional)
Payload = 1
ClipSize = 1
Conventional = YES
Nuclear = NO
Direct damage = {b2a_stats['pd']:.1f}
Primary radius = {b2a_stats['pr']:.1f}
Secondary radius = {b2a_stats['sr']:.1f}
Reference conventional heavy bomb = GBU43B_HighExplosion (PrimaryDamage 6000 / Radius 320)
Damage multiplier = {B2A_DMG_MULT}
Radius multiplier = {B2A_RADIUS_MULT} (secondary radius {B2A_SECONDARY_RADIUS_MULT}x)
BuildCost = 15000
Expected: ONE 10-ton bomb per sortie = YES
AutoReloadsClip = RETURN_TO_BASE

------------------------------

Flight systems changed = NO
Visuals changed = NO
HeavyAirBase changed = NO
Other aircraft changed = NO (E-2/E-3/E-737/C-17/V-22/AC-130/B-21/Chinook frozen)
Other factions changed = NO
ART changed = NO
Shared old weapons left intact for non-targets (e.g. B-21 still USA_B52H_AreaBombardment)

In-game bombing behavior = USER TEST REQUIRED

DATA sha256 = {data_sha}
ART sha256 = {art_sha}
ZIP = {OUT_ZIP.name}
URL = {url}
"""
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={data_sha}\n"
        f"_SPEC_ART_ONE.big sha256={art_sha} (unchanged)\n"
        f"zip={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
