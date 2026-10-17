#!/usr/bin/env python3
"""AC-130 price + V-22 AC-130 firepower at 60% range.

Active AC-130 = AmericaJetAC130 (HeavyAirBase slot 7)
  - PRIMARY only: M102_105mm_Howitzer (AttackRange 5555)
  - JetAIUpdate runway jet (NO SpectreGunshipUpdate)

V-22 = AmericaJetV22Visual keeps JetAI/F100/runway flight.
Creates dedicated AmericaV22GunWeaponPrimary clone (range x0.60).
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
STAGE = MASTER / "_stage_usa_ac130_v22_firepower"
VERIFY = MASTER / "_extract_usa_ac130_v22_firepower_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_AC130_V22_FIREPOWER.zip"
OUT_HASH = ROOT / "Release/DATA_USA_AC130_V22_FIREPOWER_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_AC130_V22_FIREPOWER_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_AC130_V22_FIREPOWER_REPORT.txt"
SRC_DIR = ROOT / "Data/INI/Object/Specter/United States Of America"

WEAPON_KEY = "Data\\INI\\Weapon.ini"
AC130_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
)
V22_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini"
)
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"
CSF_KEY = "Data\\English\\generals.csf"
HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)

AC130_WEAPON = "M102_105mm_Howitzer"
V22_WEAPON = "AmericaV22GunWeaponPrimary"
RANGE_MULT = 0.60
AC130_COST = 20000
V22_COST = 15000

FREEZE = [
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE2Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE3Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB2A.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\Airforce\\B1R.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\ScienceObjects\\AC130W.ini",
]


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


def replace_object_file(text: str, name: str, new_obj: str) -> str:
    # Single-object files: replace whole Object block
    m = re.search(rf"(?ms)^Object\s+{re.escape(name)}\s*\n.*?(?=^Object\s|\Z)", text)
    assert m, name
    return text[: m.start()] + new_obj.rstrip() + "\n"


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


def clone_weapon_for_v22(src: str, new_name: str, range_mult: float) -> tuple[str, dict]:
    body = src
    body = re.sub(
        rf"(?m)^Weapon\s+{re.escape(AC130_WEAPON)}\s*$",
        f"Weapon {new_name}",
        body,
        count=1,
    )
    info = {}
    # AttackRange
    m = re.search(r"(?m)^(\s*AttackRange\s*=\s*)([0-9.]+)", body)
    assert m
    old_r = float(m.group(2))
    new_r = int(round(old_r * range_mult))
    body = body[: m.start()] + f"{m.group(1)}{new_r}" + body[m.end() :]
    info["old_range"] = old_r
    info["new_range"] = new_r

    # MinimumAttackRange if present
    m2 = re.search(r"(?m)^(\s*MinimumAttackRange\s*=\s*)([0-9.]+)", body)
    if m2:
        old_m = float(m2.group(2))
        new_m = int(round(old_m * range_mult))
        # keep min < attack range
        new_m = min(new_m, max(0, new_r - 1))
        body = body[: m2.start()] + f"{m2.group(1)}{new_m}" + body[m2.end() :]
        info["old_min"] = old_m
        info["new_min"] = new_m
    else:
        info["old_min"] = None
        info["new_min"] = None

    # damage / delay unchanged — verify still present
    assert re.search(r"(?m)^\s*PrimaryDamage\s*=\s*500\b", body)
    assert re.search(r"(?m)^\s*DelayBetweenShots\s*=\s*777\b", body)
    assert "SpectreHowitzerShell" in body
    assert "AntiGround             = Yes" in body or "AntiGround = Yes" in body
    return body.rstrip() + "\n", info


def patch_ac130_cost(text: str) -> tuple[str, int]:
    obj = extract_object(text, "AmericaJetAC130")
    old = int(float(re.search(r"(?m)^\s*BuildCost\s*=\s*([0-9.]+)", obj).group(1)))
    obj2, n = re.subn(
        r"(?m)^(\s*BuildCost\s*=\s*)[0-9.]+",
        rf"\g<1>{AC130_COST}",
        obj,
        count=1,
    )
    assert n == 1
    # weapons unchanged
    assert "M102_105mm_Howitzer" in obj2
    assert "SpectreGunshipUpdate" not in obj2
    assert "JetAIUpdate" in obj2

    def strip_cost(t: str) -> str:
        return re.sub(r"(?m)^\s*BuildCost\s*=\s*[0-9.]+\s*$", "", t)

    assert strip_cost(obj) == strip_cost(obj2)
    return replace_object_file(text, "AmericaJetAC130", obj2), old


def patch_v22(text: str) -> tuple[str, int]:
    obj = extract_object(text, "AmericaJetV22Visual")
    old = int(float(re.search(r"(?m)^\s*BuildCost\s*=\s*([0-9.]+)", obj).group(1)))
    models_before = re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", obj)
    jetai_before = re.search(
        r"(?ms)^\s*Behavior\s*=\s*JetAIUpdate.*?\n\s*End\s*$", obj
    ).group(0)
    loco_before = re.findall(r"(?m)^\s*Locomotor\s*=\s*.*$", obj)
    scale_before = re.search(r"(?m)^\s*Scale\s*=\s*(\S+)", obj)

    obj, n = re.subn(
        r"(?m)^(\s*BuildCost\s*=\s*)[0-9.]+",
        rf"\g<1>{V22_COST}",
        obj,
        count=1,
    )
    assert n == 1

    # KindOf += CAN_ATTACK
    def kindof(m: re.Match[str]) -> str:
        indent, vals = m.group(1), m.group(2)
        parts = vals.split()
        if "CAN_ATTACK" not in parts:
            parts.append("CAN_ATTACK")
        return f"{indent}KindOf = " + " ".join(parts)

    obj, n = re.subn(r"(?m)^(\s*)KindOf\s*=\s*(.*)$", kindof, obj, count=1)
    assert n == 1

    weaponset = (
        "  WeaponSet\n"
        "    Conditions = None\n"
        f"    Weapon = PRIMARY {V22_WEAPON}\n"
        "  End\n"
    )
    if re.search(r"(?m)^\s*WeaponSet\b", obj):
        obj, n = re.subn(
            r"(?ms)^\s*WeaponSet\s*\n\s*Conditions\s*=\s*None\b.*?\n\s*End\s*\n",
            weaponset,
            obj,
            count=1,
        )
        assert n == 1
    else:
        # insert after Buildable / before ArmorSet
        obj = re.sub(
            r"(?m)^(\s*ArmorSet\b)",
            weaponset + "\n\\1",
            obj,
            count=1,
        )

    # Safety: no SpectreGunship, flight preserved
    assert "SpectreGunshipUpdate" not in obj
    assert "HelicopterAIUpdate" not in obj
    assert re.search(r"(?ms)^\s*Behavior\s*=\s*JetAIUpdate.*?\n\s*End\s*$", obj).group(
        0
    ) == jetai_before
    assert re.findall(r"(?m)^\s*Locomotor\s*=\s*.*$", obj) == loco_before
    assert re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", obj) == models_before
    scale_after = re.search(r"(?m)^\s*Scale\s*=\s*(\S+)", obj)
    assert (scale_before.group(1) if scale_before else None) == (
        scale_after.group(1) if scale_after else None
    )
    assert V22_WEAPON in obj
    assert "CAN_ATTACK" in re.search(r"(?m)^\s*KindOf\s*=\s*(.*)$", obj).group(1)

    return replace_object_file(text, "AmericaJetV22Visual", obj), old


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


def main() -> None:
    data = read_big(DATA_BIG)
    art_sha = sha256(ART_BIG)
    freeze = {k: data[k] for k in FREEZE if k in data}
    cs_before = data[CS_KEY]
    cb_before = data[CB_KEY]
    csf_before = data[CSF_KEY]
    heavy_before = data[HEAVY_KEY]

    wini = data[WEAPON_KEY].decode("latin1")
    ac_txt = data[AC130_KEY].decode("latin1")
    v22_txt = data[V22_KEY].decode("latin1")

    ac_obj = extract_object(ac_txt, "AmericaJetAC130")
    assert "SpectreGunshipUpdate" not in ac_obj
    assert "JetAIUpdate" in ac_obj
    # Active AC-130: PRIMARY only
    ws = re.search(
        r"(?ms)^\s*WeaponSet\s*\n\s*Conditions\s*=\s*None\b.*?\n\s*End\s*$", ac_obj
    )
    assert ws
    weapons = re.findall(r"(?m)^\s*Weapon\s*=\s*(\w+)\s+(\S+)", ws.group(0))
    assert weapons == [("PRIMARY", AC130_WEAPON)]

    src_w = extract_weapon(wini, AC130_WEAPON)
    m102_before = src_w  # freeze original text for equality check later
    v22_w, info = clone_weapon_for_v22(src_w, V22_WEAPON, RANGE_MULT)
    assert info["new_range"] < info["old_range"]
    assert abs(info["new_range"] / info["old_range"] - RANGE_MULT) < 0.01

    wini2 = upsert_weapon(wini, V22_WEAPON, v22_w)
    # original M102 untouched
    assert extract_weapon(wini2, AC130_WEAPON) == m102_before

    ac_out, ac_old_cost = patch_ac130_cost(ac_txt)
    v22_out, v22_old_cost = patch_v22(v22_txt)

    data2 = dict(data)
    data2[WEAPON_KEY] = wini2.replace("\r\n", "\n").encode("latin1")
    data2[AC130_KEY] = ac_out.replace("\r\n", "\n").encode("latin1")
    data2[V22_KEY] = v22_out.replace("\r\n", "\n").encode("latin1")
    data2[CS_KEY] = cs_before
    data2[CB_KEY] = cb_before
    data2[CSF_KEY] = csf_before
    data2[HEAVY_KEY] = heavy_before
    for k, v in freeze.items():
        data2[k] = v

    SRC_DIR.mkdir(parents=True, exist_ok=True)
    (SRC_DIR / "AmericaJetAC130.ini").write_bytes(data2[AC130_KEY])
    (SRC_DIR / "AmericaJetV22Visual.ini").write_bytes(data2[V22_KEY])

    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    write_tree(data2, STAGE / "in")
    DATA_BIG.write_bytes(build_big(data2))

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    dv = read_big(DATA_BIG)
    write_tree(dv, VERIFY / "out")

    assert sha256(ART_BIG) == art_sha
    assert dv[CS_KEY] == cs_before
    assert dv[CB_KEY] == cb_before
    assert dv[HEAVY_KEY] == heavy_before
    for k, v in freeze.items():
        assert dv[k] == v

    pw = dv[WEAPON_KEY].decode("latin1")
    pac = extract_object(dv[AC130_KEY].decode("latin1"), "AmericaJetAC130")
    pv = extract_object(dv[V22_KEY].decode("latin1"), "AmericaJetV22Visual")

    assert int(re.search(r"BuildCost\s*=\s*([0-9.]+)", pac).group(1)) == AC130_COST
    assert int(re.search(r"BuildCost\s*=\s*([0-9.]+)", pv).group(1)) == V22_COST
    assert extract_weapon(pw, AC130_WEAPON) == m102_before
    assert len(re.findall(rf"(?m)^Weapon\s+{re.escape(V22_WEAPON)}\s*$", pw)) == 1
    vw = extract_weapon(pw, V22_WEAPON)
    assert int(re.search(r"AttackRange\s*=\s*([0-9.]+)", vw).group(1)) == info["new_range"]
    assert int(re.search(r"AttackRange\s*=\s*([0-9.]+)", m102_before).group(1)) == int(
        info["old_range"]
    )
    assert info["new_range"] < info["old_range"]
    assert V22_WEAPON in pv and AC130_WEAPON not in pv
    assert AC130_WEAPON in pac
    assert "SpectreGunshipUpdate" not in pv and "SpectreGunshipUpdate" not in pac
    assert "JetAIUpdate" in pv and "F100_PW_229" in pv and "BasicJetTaxiLocomotor" in pv
    assert "AVOsprey" in pv
    # projectile resolves
    assert any(
        b"Object SpectreHowitzerShell" in v for v in dv.values()
    )

    # HeavyAirBase slot 11 still V22, slot 7 AC130
    cs = dv[CS_KEY].decode("latin1")
    hab = re.search(
        r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?(?=^CommandSet\s|\Z)",
        cs,
    ).group(0)
    assert "Command_ConstructAmericaJetAC130" in hab
    assert "Command_ConstructAmericaJetV22Visual" in hab

    data_sha = sha256(DATA_BIG)
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    url = upload(OUT_ZIP)

    report = f"""AC130 + V22 COMBAT UPDATE = STRUCTURAL PASS

AC-130:
Object = AmericaJetAC130
Old BuildCost = {ac_old_cost}
New BuildCost = {AC130_COST}

Primary weapon = {AC130_WEAPON}
Range = {info['old_range']}
Damage = 500
DelayBetweenShots = 777
ClipSize = 0 (infinite continuous howitzer, same as before)
ProjectileObject = SpectreHowitzerShell
FireFX = WeaponFX_GenericTankGunNoTracer
ProjectileDetonationFX = FX_FreeFallBombsDetonation

Secondary weapon = NONE (active airfield AC-130 has PRIMARY only)
Tertiary weapon = NONE

SpectreGunshipUpdate on AC-130 = NO (already JetAIUpdate runway jet)
Weapons changed = NO
Weapon range unchanged = YES

--------------------------------

V-22:
Object = AmericaJetV22Visual
Old BuildCost = {v22_old_cost}
New BuildCost = {V22_COST}

Primary weapon = {V22_WEAPON}
AC-130 source weapon = {AC130_WEAPON}
AC-130 range = {info['old_range']}
V-22 final range = {info['new_range']}  ({RANGE_MULT*100:.0f}% → {info['new_range']})

Secondary weapon = NONE
Tertiary weapon = NONE

All V-22 ranges approximately 60% of AC-130 = YES
Damage copied = YES (500)
Fire rate copied = YES (DelayBetweenShots 777 + ContinuousFire bonuses)
AC-130 weapon definitions directly modified = NO
Dedicated V-22 weapon clones = YES

V-22 flight system changed = NO
V-22 remains runway-based = YES (JetAIUpdate + F100_PW_229 + BasicJetTaxiLocomotor)

SpectreGunshipUpdate copied = NO
Reason = Active AmericaJetAC130 does not use SpectreGunshipUpdate; V-22 uses normal WeaponSet + JetAIUpdate attack firing (same fire-control family as the airfield AC-130).

HeavyAirBase changed = NO
ART changed = NO
Other aircraft changed = NO

In-game combat = USER TEST REQUIRED

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
