#!/usr/bin/env python3
"""Align HT-233 / 92N6E CombatMode DataLink with working AN/TPY-2.

US_AN_TPY2_CombatMode (healthy):
  FireWeaponUpdate FCRL = FireControlRadarDataLink
  ExclusiveWeaponDelay = 1000
  FireControlRadarDataLink = SURRENDER/EXTRA_6/ALLIES, radius 250,
  no DamageDealtAtSelfPosition, no AntiBallisticMissile.

Previous 92N6E/HT-233 last-win replaced that with dedicated weapons:
  DamageDealtAtSelfPosition = Yes, radius 1600-1800,
  AntiGround + AntiAirborneVehicle + AntiBallisticMissile,
  ExclusiveWeaponDelay removed.

Those pulses EXTRA_6-kill AirdefenseLinkRestarter across a huge
ALLIES radius. Restarter CreateObjectDie (EXTRA_6 -> OCL_SAMBLABLA)
immediately respawns it, so nearby FCS keep receiving STATUS NO_ATTACK
and never intercept. TPY-2 never does this.

This rebuild last-wins only the two CombatMode objects and the two
dedicated DataLink names so they match TPY-2. Interceptor weapons,
TPY-2, Iraq radar, and Supply Centre last-wins are not edited.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path


CS_IRAQ = r"Data\INI\CommandSet_ZZZZ_ZZZIraqRadar.ini"
OBJ_IRAQ = r"Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini"
OBJ_DIR = r"Data\INI\Object\zzzzz_SpecterRadarTpy2Cue"
WPN_LATER = r"Data\INI\Weapon_ZZZZ_ZZZZTpy2RadarCue.ini"


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    fm: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        fm[name] = data[off : off + size]
    return fm


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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def last_win_block(file_map: dict[str, bytes], kind: str, name: str) -> tuple[str | None, str | None]:
    pat = re.compile(
        rf"(?m)^{kind}\s+{re.escape(name)}\b.*?(?=^(?:Object|Weapon|Armor|CommandButton|CommandSet|ObjectCreationList|Upgrade|SpecialPower)\s|\Z)",
        re.S,
    )
    last = None
    src = None
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        text = raw.decode("latin1")
        for m in pat.finditer(text):
            last = m.group(0)
            src = path
    return src, last


def crlf(body: str) -> bytes:
    return body.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


WEAPON_TPY2_CUE = """\
; SPECTER last-win. Dedicated 92N6E / HT-233 DataLink names are forced
; to the working AN/TPY-2 FireControlRadarDataLink stats so a leftover
; CombatMode reference cannot keep the 1600-1800 self-pulse.

Weapon 92N6R_FireControlDataLink
  PrimaryDamage             = 2500
  PrimaryDamageRadius       = 250
  DamageType                = SURRENDER
  DeathType                 = EXTRA_6
  RadiusDamageAffects       = ALLIES
  DelayBetweenShots         = 100
End

Weapon HT233_FireControlDataLink
  PrimaryDamage             = 2500
  PrimaryDamageRadius       = 250
  DamageType                = SURRENDER
  DeathType                 = EXTRA_6
  RadiusDamageAffects       = ALLIES
  DelayBetweenShots         = 100
End
"""


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def fcrl_block(body: str | None) -> str:
    m = re.search(
        r"Behavior\s*=\s*FireWeaponUpdate\s+ModuleTag_FCRL\s*.*?End",
        body or "",
        re.S,
    )
    return m.group(0) if m else ""


def validate(file_map: dict[str, bytes]) -> None:
    tpy_src, tpy = last_win_block(file_map, "Object", "US_AN_TPY2_CombatMode")
    _req(tpy_src and "US_AN_TPY2.ini" in (tpy_src or ""), f"TPY-2 CombatMode last-win moved to {tpy_src}")
    tpy_fcrl = fcrl_block(tpy)
    _req("FireControlRadarDataLink" in tpy_fcrl, "TPY-2 lost FireControlRadarDataLink")
    _req("ExclusiveWeaponDelay      = 1000" in tpy_fcrl, "TPY-2 lost ExclusiveWeaponDelay")
    _req("DamageDealtAtSelfPosition" not in tpy_fcrl, "TPY-2 FCRL unexpectedly has self-position")

    _, isr = last_win_block(file_map, "Object", "IsraelTPY2CombatMode")
    _req("FireControlRadarDataLink" in fcrl_block(isr), "Israel TPY-2 DataLink changed")

    _, stock = last_win_block(file_map, "Weapon", "FireControlRadarDataLink")
    _req(bool(stock) and "PrimaryDamageRadius       = 250" in stock, "stock FireControlRadarDataLink radius changed")
    _req("DamageDealtAtSelfPosition" not in (stock or ""), "stock DataLink gained self-position")
    _req("AntiBallisticMissile" not in (stock or ""), "stock DataLink gained AntiBM")

    for wname in ("92N6R_FireControlDataLink", "HT233_FireControlDataLink"):
        src, body = last_win_block(file_map, "Weapon", wname)
        _req(src == WPN_LATER, f"{wname} last-win moved to {src}")
        _req("PrimaryDamageRadius       = 250" in (body or ""), f"{wname} radius not 250")
        _req("DamageDealtAtSelfPosition" not in (body or ""), f"{wname} still self-position")
        _req("AntiBallisticMissile" not in (body or ""), f"{wname} still AntiBM")
        _req("AntiAirborneVehicle" not in (body or ""), f"{wname} still AntiAir")
        _req("SURRENDER" in (body or "") and "EXTRA_6" in (body or ""), f"{wname} lost SURRENDER/EXTRA_6")
        _req("ALLIES" in (body or ""), f"{wname} lost ALLIES")

    for obj, src_need in (
        ("ChinaVehicleHT233_CombatMode", OBJ_DIR),
        ("Russia_92N6R_CombatMode", OBJ_DIR),
    ):
        src, body = last_win_block(file_map, "Object", obj)
        _req(src_need.replace("\\", "") in (src or "").replace("\\", ""), f"{obj} last-win not {src_need} ({src})")
        blk = fcrl_block(body)
        _req("FireControlRadarDataLink" in blk, f"{obj} FCRL not TPY-2 DataLink")
        _req("ExclusiveWeaponDelay      = 1000" in blk, f"{obj} missing ExclusiveWeaponDelay")
        _req("HT233_FireControlDataLink" not in blk, f"{obj} still uses HT233 dedicated DataLink")
        _req("92N6R_FireControlDataLink" not in blk, f"{obj} still uses 92N6R dedicated DataLink")
        _req("RadarTrackingBeam" in (body or ""), f"{obj} lost RadarTrackingBeam")
        _req("StealthDetectorUpdate" in (body or ""), f"{obj} lost stealth detect")

    # Interceptors unchanged
    _, s400 = last_win_block(file_map, "Weapon", "3x_LRSAM_40N6KMissile_ABM")
    _req(bool(s400) and "CRUSH" in s400, "S-400 ABM interceptor changed")
    _, hq = last_win_block(file_map, "Weapon", "Hq9_AA_Missile_ABM")
    _req(bool(hq) and "CRUSH" in hq, "HQ-9 ABM interceptor changed")
    _, pac = last_win_block(file_map, "Weapon", "10x_PAC3_MSE_ABM")
    _req(bool(pac) and "CRUSH" in pac, "Patriot interceptor changed")

    # Prior accepted last-wins
    obj_src, obj = last_win_block(file_map, "Object", "Iraq_RadarStation")
    _req(obj_src == OBJ_IRAQ, f"Iraq radar object last-win moved to {obj_src}")
    ru = re.search(r"Behavior\s*=\s*RadarUpgrade.*?End", obj or "", re.S)
    _req(bool(ru) and "TriggeredBy" in ru.group(0) and "Upgrade_AmericaRadar" in ru.group(0), "Iraq RadarUpgrade TriggeredBy lost")
    cs_src, cs = last_win_block(file_map, "CommandSet", "Iraq_RadarStationCommandSet")
    _req(cs_src == CS_IRAQ, f"Iraq CS last-win moved to {cs_src}")
    _req("Command_SpySatelliteScan" not in (cs or ""), "Iraq CS regained Spy Sat")

    am_src, am = last_win_block(file_map, "Object", "AmericaSupplyCenter")
    _req("zzzzz_SpecterSupplyCentreBuy" in (am_src or ""), f"America Supply Centre last-win lost ({am_src})")
    _req("AmericaSupplyCenterCommandSet" in (am or ""), "America Supply Centre CommandSet lost")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    ap.add_argument(
        "--objects",
        type=Path,
        default=Path("patch/Data/INI/Object/zzzzz_SpecterRadarTpy2Cue"),
    )
    args = ap.parse_args()

    fm = read_big(args.src_big)
    extras: dict[str, bytes] = {WPN_LATER: crlf(WEAPON_TPY2_CUE)}
    for ini in sorted(args.objects.glob("*.ini")):
        extras[rf"{OBJ_DIR}\{ini.name}"] = crlf(ini.read_text(encoding="latin1"))

    changed = []
    for name, body in extras.items():
        prev = fm.get(name)
        fm[name] = body
        changed.append(("update" if prev is not None else "add", name))

    validate(fm)

    args.out_big.parent.mkdir(parents=True, exist_ok=True)
    blob = build_big(fm)
    args.out_big.write_bytes(blob)
    hdr = struct.unpack(">I", blob[4:8])[0]
    if hdr != len(blob):
        raise SystemExit(f"BIG size field {hdr} != file {len(blob)}")
    digest = sha256(args.out_big)
    Path(str(args.out_big) + ".sha256").write_text(digest + "\n")
    print(f"SRC  size={args.src_big.stat().st_size} sha256={sha256(args.src_big)}")
    print(f"OUT  size={args.out_big.stat().st_size} sha256={digest} entries={len(fm)}")
    for op, name in changed:
        print(f"  {op} {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
