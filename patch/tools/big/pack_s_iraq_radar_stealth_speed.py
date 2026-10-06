#!/usr/bin/env python3
"""Radar Stealth = real projectile travel speed for Iraq factory missiles.

Live DATA baseline: SPECTER_IRAQ_MISSILE_DATA_BCDHIJ
ART unchanged.

MOTHER (Iraq_R11ScudB / ALHIJARAH_MRBM_Object / R11SRBMLocomotor / SRBM_ALHIJARAH_HE)
is the 5/100 speed baseline and is not modified:

  Locomotor Speed        = 450 dist/sec   (THRUST cruise)
  Locomotor Acceleration = 250
  WeaponSpeed            = 280
  InitialVelocity        = 10

Scale = score / 5. Dedicated locos so R11SRBMLocomotor stays byte-identical.
RadarPriority / HP-as-stealth are removed. Projectile HP restored to MOTHER 400.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_DATA_BCDHIJ/_SPEC_DATA_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_RADAR_STEALTH_SPEED"
SRC = ROOT / "patch/Data/INI"

BASE_DATA_SHA = "87ce408d2fa679b82f9fad22b515b10a9b993aa4453cc32175e2af093410a126"
BASE_DATA_SIZE = 366469264
PREV_ART_SHA = "e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4"
PREV_ART_SIZE = 1292294758

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CSF_KEY = r"Data\English\generals.csf"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
LOCO_KEY = r"Data\INI\Locomotor.ini"
WOBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_WeaponObjects.ini"
UNIT_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
PROJ_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini"
WEP_A_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlFahd500.ini"
WEP_NEW_KEY = r"Data\INI\Weapon\Weapon_Iraq_FactoryMissiles.ini"
LOCO_NEW_KEY = r"Data\INI\Locomotor_IraqFactoryMissiles.ini"
UPG_KEY = r"Data\INI\Upgrade_IraqFactoryMissiles.ini"

MISSILES = [
    {"slot": "A", "object": "Iraq_AlFahd500", "score": 20, "wpn": "Weapon_Iraq_AlFahd500",
     "proj": "Projectile_Iraq_AlFahd500", "loco": "Iraq_AlFahd500_Locomotor",
     "wpn_speed": 1120, "speed": 1800, "accel": 1000, "init": 40,
     "proj_key": PROJ_A_KEY, "unit_key": UNIT_A_KEY},
    {"slot": "B", "object": "Iraq_AlHusseinII", "score": 10, "wpn": "Weapon_Iraq_AlHusseinII",
     "proj": "Projectile_Iraq_AlHusseinII", "loco": "Iraq_AlHusseinII_Locomotor",
     "wpn_speed": 560, "speed": 900, "accel": 500, "init": 20,
     "proj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlHusseinII_Projectile.ini",
     "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHusseinII.ini"},
    {"slot": "D", "object": "Iraq_AlAbbas", "score": 15, "wpn": "Weapon_Iraq_AlAbbas",
     "proj": "Projectile_Iraq_AlAbbas", "loco": "Iraq_AlAbbas_Locomotor",
     "wpn_speed": 840, "speed": 1350, "accel": 750, "init": 30,
     "proj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlAbbas_Projectile.ini",
     "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini"},
    {"slot": "C", "object": "Iraq_AlSamoudII", "score": 30, "wpn": "Weapon_Iraq_AlSamoudII",
     "proj": "Projectile_Iraq_AlSamoudII", "loco": "Iraq_AlSamoudII_Locomotor",
     "wpn_speed": 1680, "speed": 2700, "accel": 1500, "init": 60,
     "proj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlSamoudII_Projectile.ini",
     "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlSamoudII.ini"},
    {"slot": "H", "object": "Iraq_AlBasrah", "score": 60, "wpn": "Weapon_Iraq_AlBasrah",
     "proj": "Projectile_Iraq_AlBasrah", "loco": "Iraq_AlBasrah_Locomotor",
     "wpn_speed": 3360, "speed": 5400, "accel": 3000, "init": 120,
     "proj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlBasrah_Projectile.ini",
     "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlBasrah.ini"},
    {"slot": "I", "object": "Iraq_AlNasir", "score": 70, "wpn": "Weapon_Iraq_AlNasir",
     "proj": "Projectile_Iraq_AlNasir", "loco": "Iraq_AlNasir_Locomotor",
     "wpn_speed": 3920, "speed": 6300, "accel": 3500, "init": 140,
     "proj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlNasir_Projectile.ini",
     "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNasir.ini"},
    {"slot": "J", "object": "Iraq_AlMansour", "score": 85, "wpn": "Weapon_Iraq_AlMansour",
     "proj": "Projectile_Iraq_AlMansour", "loco": "Iraq_AlMansour_Locomotor",
     "wpn_speed": 4760, "speed": 7650, "accel": 4250, "init": 170,
     "proj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlMansour_Projectile.ini",
     "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlMansour.ini"},
]

OLD_SPEED = {
    "MOTHER": {"loco": "R11SRBMLocomotor", "speed": 450, "accel": 250, "wpn_speed": 280, "init": 10, "hp": 400, "radar": None},
    "Iraq_AlFahd500": {"loco": "R11SRBMLocomotor", "speed": 450, "accel": 250, "wpn_speed": 280, "init": 10, "hp": 1600, "radar": "LOCAL_UNIT_ONLY"},
    "Iraq_AlHusseinII": {"loco": "R11SRBMLocomotor", "speed": 450, "accel": 250, "wpn_speed": 280, "init": 10, "hp": 800, "radar": None},
    "Iraq_AlAbbas": {"loco": "R11SRBMLocomotor", "speed": 450, "accel": 250, "wpn_speed": 280, "init": 10, "hp": 1200, "radar": None},
    "Iraq_AlSamoudII": {"loco": "R11SRBMLocomotor", "speed": 450, "accel": 250, "wpn_speed": 280, "init": 10, "hp": 2400, "radar": "LOCAL_UNIT_ONLY"},
    "Iraq_AlBasrah": {"loco": "R11SRBMLocomotor", "speed": 450, "accel": 250, "wpn_speed": 280, "init": 10, "hp": 4800, "radar": "NOT_ON_RADAR"},
    "Iraq_AlNasir": {"loco": "R11SRBMLocomotor", "speed": 450, "accel": 250, "wpn_speed": 280, "init": 10, "hp": 5600, "radar": "NOT_ON_RADAR"},
    "Iraq_AlMansour": {"loco": "R11SRBMLocomotor", "speed": 450, "accel": 250, "wpn_speed": 280, "init": 10, "hp": 6800, "radar": "NOT_ON_RADAR"},
}


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes) -> dict[str, bytes]:
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


def parse_index(data: bytes):
    archive_size = struct.unpack(">I", data[4:8])[0]
    count = struct.unpack(">I", data[8:12])[0]
    header_size = struct.unpack(">I", data[12:16])[0]
    pos = 16
    files = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files.append((name, off, size))
    return archive_size, count, header_size, pos, files


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
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
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")


def command_block(text: str, kind: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text)
    return m.group(0) if m else None


def slot_map(block: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    expected = header
    for name, off, size in sorted(files, key=lambda x: x[1]):
        if off != expected:
            issues.append(f"overlap/gap {name}")
            break
        expected = off + size
    if expected != len(blob):
        issues.append("trailing gap/overflow")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def last_weapon_block(data: dict[str, bytes], name: str) -> tuple[str, str] | None:
    blocks: list[tuple[str, str]] = []
    wep = data[WEAPON_KEY].decode("latin1")
    b = command_block(wep, "Weapon", name)
    if b:
        blocks.append((WEAPON_KEY, b))
    weapon_dir = [k for k in data if k.replace("/", "\\").lower().startswith(r"data\ini\weapon" + "\\") and k.lower().endswith(".ini")]
    for k in sorted(weapon_dir, key=lambda x: x.lower()):
        t = data[k].decode("utf-8")
        b = command_block(t, "Weapon", name)
        if b:
            blocks.append((k, b))
    return blocks[-1] if blocks else None


def last_loco_block(data: dict[str, bytes], name: str) -> tuple[str, str] | None:
    blocks: list[tuple[str, str]] = []
    for k in sorted(data, key=lambda x: x.lower()):
        lk = k.replace("/", "\\").lower()
        if not lk.endswith(".ini"):
            continue
        if "locomotor" not in lk:
            continue
        t = data[k].decode("utf-8", errors="replace")
        b = command_block(t, "Locomotor", name)
        if b:
            blocks.append((k, b))
    return blocks[-1] if blocks else None


def csf_get(csf: bytes, key: str) -> str | None:
    if csf[:4] != b" FSC":
        return None
    pos = 24
    while pos < len(csf):
        if csf[pos : pos + 4] != b" LBL":
            break
        pos += 4
        cnt, nlen = struct.unpack_from("<II", csf, pos)
        pos += 8
        name = csf[pos : pos + nlen].decode("latin1")
        pos += nlen
        val = None
        for _ in range(cnt):
            smag = csf[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4
            raw = csf[pos : pos + slen * 2]
            pos += slen * 2
            val = bytes(x ^ 0xFF for x in raw).decode("utf-16le")
            if smag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4 + elen
        if name == key:
            return val
    return None


def workspace_overlay() -> dict[str, bytes]:
    mapping = {
        PROJ_A_KEY: SRC / "Object/Specter/Iraq Army/Iraq_AlFahd500_Projectile.ini",
        WEP_A_KEY: SRC / "Weapon/Weapon_Iraq_AlFahd500.ini",
        WEP_NEW_KEY: SRC / "Weapon/Weapon_Iraq_FactoryMissiles.ini",
        LOCO_NEW_KEY: SRC / "Locomotor_IraqFactoryMissiles.ini",
    }
    for m in MISSILES:
        if m["slot"] == "A":
            continue
        mapping[m["proj_key"]] = SRC / f"Object/Specter/Iraq Army/{m['object']}_Projectile.ini"
    return {k: to_crlf(p.read_text(encoding="utf-8")) for k, p in mapping.items()}


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    all_ini = b"".join(v for k, v in data.items() if k.lower().endswith(".ini"))

    for key in (R11_KEY, WEAPON_KEY, FACTORY_KEY, CB_KEY, CS_KEY, CSF_KEY, UNIT_A_KEY, UPG_KEY, LOCO_KEY, WOBJ_KEY):
        if key in src and data.get(key) != src[key]:
            fails.append(f"protected file mutated {key}")

    r11 = data[R11_KEY].decode("latin1")
    if "Weapon = PRIMARY   SRBM_ALHIJARAH_HE" not in r11 or "BuildCost       = 1200" not in r11:
        fails.append("MOTHER TEL changed")

    mother_w = command_block(data[WEAPON_KEY].decode("latin1"), "Weapon", "SRBM_ALHIJARAH_HE") or ""
    if "WeaponSpeed                 = 280" not in mother_w or "AttackRange                 = 1720.0" not in mother_w:
        fails.append("MOTHER weapon speed/range")
    if "PrimaryDamage               = 2000.0" not in mother_w or "ScatterRadius               = 175" not in mother_w:
        fails.append("MOTHER damage/accuracy")

    mother_p = command_block(data[WOBJ_KEY].decode("latin1"), "Object", "ALHIJARAH_MRBM_Object") or ""
    if "Locomotor = SET_NORMAL R11SRBMLocomotor" not in mother_p:
        fails.append("MOTHER projectile loco")
    if "InitialVelocity = 10" not in mother_p or "MaxHealth       = 400.0" not in mother_p:
        fails.append("MOTHER projectile speed/HP")
    if re.search(r"^\s*RadarPriority\s*=", mother_p, re.M):
        fails.append("MOTHER projectile gained RadarPriority")

    mother_l = last_loco_block(data, "R11SRBMLocomotor")
    if not mother_l or "Speed = 450" not in mother_l[1] or "Acceleration = 250" not in mother_l[1]:
        fails.append("MOTHER R11SRBMLocomotor speed changed")
    if mother_l and mother_l[0].replace("/", "\\").lower() != LOCO_KEY.lower():
        fails.append(f"R11SRBMLocomotor last-wins {mother_l[0]}")

    unit_a = data[UNIT_A_KEY].decode("utf-8")
    if "BuildCost       = 2200" not in unit_a or "BuildTime       = 30.0" not in unit_a:
        fails.append("Al-Fahd cost/time")
    if "IRQ_AF500.IRQ_AF500" not in unit_a or "SelectPortrait         = specter_missile_a" not in unit_a:
        fails.append("Al-Fahd art/queue")

    last_a = last_weapon_block(data, "Weapon_Iraq_AlFahd500")
    if not last_a:
        fails.append("Al-Fahd weapon missing")
    else:
        if "PrimaryDamage               = 8000.0" not in last_a[1] or "AttackRange                 = 1720.0" not in last_a[1]:
            fails.append("Al-Fahd damage/range")
        if "ScatterRadius               = 175" not in last_a[1]:
            fails.append("Al-Fahd accuracy")
        if "WeaponSpeed                 = 1120" not in last_a[1]:
            fails.append("Al-Fahd WeaponSpeed not 4x MOTHER 280")
        if "ProjectileObject            = Projectile_Iraq_AlFahd500" not in last_a[1]:
            fails.append("Al-Fahd projectile retargeted")

    fac = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet") or ""
    slots = slot_map(fac)
    expect = {1: "CB_MISSILE_A", 2: "CB_MISSILE_B", 3: "CB_MISSILE_C", 4: "CB_MISSILE_D",
              8: "CB_MISSILE_H", 9: "CB_MISSILE_I", 10: "CB_MISSILE_J",
              13: "Command_SetRallyPoint", 14: "Command_Sell"}
    for k, v in expect.items():
        if slots.get(k) != v:
            fails.append(f"factory slot {k}={slots.get(k)}")
    for empty in (5, 6, 7, 11, 12):
        if empty in slots:
            fails.append(f"E/F/G/K/L-range slot {empty} wired")

    for ch in "EFGKL":
        btn = command_block(data[CB_KEY].decode("latin1"), "CommandButton", f"CB_MISSILE_{ch}") or ""
        if re.search(r"^\s*Object\s*=", btn, re.M):
            fails.append(f"CB_MISSILE_{ch} wired")

    tip = csf_get(data[CSF_KEY], "CONTROLBAR:ToolTipSpecterMissileA") or ""
    if "Radar Stealth: 20/100" not in tip or "Al-Fahd500" not in tip:
        fails.append("Al-Fahd tooltip Radar Stealth label lost")
    if any(ord(c) > 127 for c in tip):
        fails.append("Al-Fahd tooltip not English")

    for m in MISSILES:
        n_obj = len(re.findall(rf"^Object {re.escape(m['proj'])}\s*$".encode("ascii"), all_ini, re.M))
        if n_obj != 1:
            fails.append(f"{m['proj']} count {n_obj}")
        proj = data[m["proj_key"]].decode("utf-8")
        if f"Locomotor = SET_NORMAL {m['loco']}" not in proj:
            fails.append(f"{m['object']} loco")
        if f"InitialVelocity = {m['init']}" not in proj:
            fails.append(f"{m['object']} InitialVelocity")
        if "MaxHealth       = 400.0" not in proj:
            fails.append(f"{m['object']} HP not restored to MOTHER 400")
        if re.search(r"^\s*RadarPriority\s*=", proj, re.M):
            fails.append(f"{m['object']} projectile still has RadarPriority")
        wep = last_weapon_block(data, m["wpn"])
        if not wep or f"WeaponSpeed                 = {m['wpn_speed']}" not in wep[1]:
            fails.append(f"{m['wpn']} WeaponSpeed")
        if wep and f"ProjectileObject            = {m['proj']}" not in wep[1]:
            fails.append(f"{m['wpn']} projectile")
        loco = last_loco_block(data, m["loco"])
        if not loco or f"Speed = {m['speed']}" not in loco[1] or f"Acceleration = {m['accel']}" not in loco[1]:
            fails.append(f"{m['loco']} Speed/Accel")
        if loco and loco[0].replace("/", "\\").lower() != LOCO_NEW_KEY.lower():
            fails.append(f"{m['loco']} last-wins {loco[0]}")
        unit = data[m["unit_key"]].decode("utf-8")
        if m["slot"] != "A":
            if "ReplaceObject" not in unit or "AutoReloadsClip" in unit:
                pass
            if f"ButtonImage            = specter_missile_{m['slot'].lower()}" not in unit:
                fails.append(f"{m['object']} queue icon")

    # B-J rebuild preserved
    for m in MISSILES:
        if m["slot"] == "A":
            continue
        unit = data[m["unit_key"]].decode("utf-8")
        if f"ReplaceObject = {m['object']}" not in unit:
            fails.append(f"{m['object']} rebuild lost")
        wep = last_weapon_block(data, m["wpn"])
        if not wep or "AutoReloadsClip             = No" not in wep[1]:
            fails.append(f"{m['wpn']} AutoReloadsClip")

    zzzz = [k for k in data if "zzzz" in k.lower() and (b"Iraq_AlFahd500" in data[k] or b"Iraq_AlHusseinII" in data[k])]
    if zzzz:
        fails.append(f"ZZZZ {zzzz[:4]}")

    changed = sorted(k for k in set(data) | set(src) if data.get(k) != src.get(k))
    allowed = {PROJ_A_KEY, WEP_A_KEY, WEP_NEW_KEY, LOCO_NEW_KEY} | {m["proj_key"] for m in MISSILES}
    unexpected = [k for k in changed if k not in allowed]
    if unexpected:
        fails.append(f"unexpected DATA changes {unexpected[:8]}")
    return fails


def speed_audit() -> str:
    lines = [
        "# Radar Stealth speed audit (MOTHER 5/100 = R11SRBMLocomotor Speed 450)",
        "",
        "Authoritative stack: Locomotor Speed (cruise) + Acceleration + WeaponSpeed + InitialVelocity.",
        "Scale = score / 5 vs MOTHER. R11SRBMLocomotor / SRBM_ALHIJARAH_HE / ALHIJARAH_MRBM_Object UNCHANGED.",
        "",
        "| Missile | Score | Loco | Speed old→new | Accel old→new | WeaponSpeed old→new | InitVel old→new | HP old→new | RadarPriority old→new | Expected TTI |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    rows = [
        ("MOTHER / Iraq_R11ScudB", 5, "R11SRBMLocomotor", 450, 450, 250, 250, 280, 280, 10, 10, 400, 400, "none", "none", "baseline slowest"),
    ]
    for m in MISSILES:
        old = OLD_SPEED[m["object"]]
        rows.append((
            f"{m['object']}",
            m["score"],
            m["loco"],
            old["speed"], m["speed"],
            old["accel"], m["accel"],
            old["wpn_speed"], m["wpn_speed"],
            old["init"], m["init"],
            old["hp"], 400,
            old["radar"] or "none", "none (removed)",
            f"{m['score']/5:.0f}x MOTHER cruise",
        ))
    for r in rows:
        if r[0].startswith("MOTHER"):
            lines.append(
                f"| {r[0]} | {r[1]}/100 | {r[2]} | {r[3]} → {r[4]} | {r[5]} → {r[6]} | {r[7]} → {r[8]} | {r[9]} → {r[10]} | {r[11]} → {r[12]} | {r[13]} → {r[14]} | {r[15]} |"
            )
        else:
            lines.append(
                f"| {r[0]} | {r[1]}/100 | {r[2]} | {r[3]} → {r[4]} | {r[5]} → {r[6]} | {r[7]} → {r[8]} | {r[9]} → {r[10]} | {r[11]} → {r[12]} | {r[13]} → {r[14]} | {r[15]} |"
            )
    lines += [
        "",
        "Relative order (slowest to fastest): MOTHER 5 < Al-Hussein II 10 < Al-Abbas 15 < Al-Fahd500 20 < Al-Samoud II 30 < Al-Basrah 60 < Al-Nasir 70 < Al-Mansour 85.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("live DATA baseline mismatch")

    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)
    overlay = workspace_overlay()
    data.update(overlay)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    extracted = parse_big(packed)

    stage = OUT / "LAST_WINS_EXTRACT"
    (stage / "DATA").mkdir(parents=True)
    dump = [PROJ_A_KEY, WEP_A_KEY, WEP_NEW_KEY, LOCO_NEW_KEY, R11_KEY, UNIT_A_KEY]
    dump += [m["proj_key"] for m in MISSILES]
    for rel in dump:
        p = stage / "DATA" / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])

    fails = validate(extracted, src)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    data_sha = sha256_path(out_data)
    audit = speed_audit()
    (OUT / "SPEED_AUDIT.txt").write_text(audit + "\n", encoding="utf-8")

    report = [
        "# SPECTER Radar Stealth = projectile travel speed",
        "",
        "MOTHER / 9P117 UNCHANGED. ART UNCHANGED.",
        "Radar Stealth UI label kept. Mechanic is Locomotor Speed + WeaponSpeed + InitialVelocity.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART SHA256 (unchanged): {PREV_ART_SHA}",
        f"- ART size (unchanged): {PREV_ART_SIZE}",
        "",
        audit,
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        report.append("RUNTIME TEST: NOT PERFORMED")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static)",
        "- MOTHER loco/weapon/projectile byte-identical",
        "- dedicated locos last-win from Locomotor_IraqFactoryMissiles.ini",
        "- projectile HP restored to 400; RadarPriority removed from projectiles",
        "- range/damage/accuracy/cost/rebuild/CommandSet unchanged",
        "- E/F/G/K/L unwired; no ZZZZ; ART not rebuilt",
        "",
        "RUNTIME TEST: NOT PERFORMED",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=NO\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted)}\n"
        "ART_FILE=unchanged previous _SPEC_ART_ONE.big\n"
        f"ART_SHA256={PREV_ART_SHA}\n"
        "MECHANIC=Locomotor Speed + Acceleration + WeaponSpeed + InitialVelocity\n"
        "SCALE=score/5 vs MOTHER Speed 450\n"
        "HP_RESTORED=400\n"
        "RADARPRIORITY_REMOVED=projectile\n"
        "MOTHER_UNCHANGED=YES\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT PERFORMED\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Radar Stealth = missile travel speed (DATA-only)\n"
        "Place this complete replacement DATA BIG in the game folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "Keep the previous complete ART BIG (_SPEC_ART_ONE.big).\n"
        "9P117 / MOTHER is unmodified.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_RADAR_STEALTH_SPEED.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
        zf.write(OUT / "SPEED_AUDIT.txt", "SPEED_AUDIT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
