#!/usr/bin/env python3
"""Restore factory DF-41 launch to the live WeaponA bone.

Source: PR #714 / iraq-factory-cs-crash _SPEC_DATA_ONE.big
(SHA d5a8ed982e7ff37de1fa9923f1ee96abe16312f481f563891d95e1b4dffb26c8),
byte-identical to PR #713 DATA.

Cause: #712 applied the Khormshar Show-MISSILE01 helper to Factory_DF41Once
and injected WeaponLaunchBone = PRIMARY MISSILE01 on the truck draw (12
states). Live ChinaVehicleDF41 launches only from ModuleTag_Bones
WeaponLaunchBone = PRIMARY WeaponA (model DF41_Bones). The shared
projectile DF41_ICBM_Sgl_Object is BALLISTIC_MISSILE with
MissileAIUpdate DistanceToTravelBeforeTurning = 1750 and locomotor
DF41MissileLocomotor (Surfaces=AIR, PreferredHeight=1600). Spawned from
horizontal MISSILE01 it travels that first 1750 along the ground.

Fix: delete only the injected PRIMARY MISSILE01 / PRIMARY WEAPONFX truck
lines. Keep ShowSubObject MISSILE01, ModuleTag_Bones WeaponA, one-clip
weapon, BuildCost 30000. Live DF41.ini and A-M slots are not touched.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
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
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/IRAQ_FACTORY_CS_CRASH/_SPEC_DATA_ONE.big"
SRC_SHA = "d5a8ed982e7ff37de1fa9923f1ee96abe16312f481f563891d95e1b4dffb26c8"
OUT_DIR = ROOT / "Release/DF41_FACTORY_BALLISTIC"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_DF41 = r"Data\INI\Object\Specter\PLA\Wheeled\DF41.ini"
K_FAC = r"Data\INI\Object\Specter\FactoryKLMN\Factory_DF41Once.ini"
K_KHOR = r"Data\INI\Object\Specter\FactoryKLMN\Factory_KhormsharOnce.ini"
K_RS24 = r"Data\INI\Object\Specter\FactoryKLMN\Factory_RS24YarsOnce.ini"
K_WO = r"Data\INI\Object\Specter\PLA\Chines_WeaponObjects.ini"


def strip_injected_missile01_launch(text: str) -> str:
    nl = "\r\n" if "\r\n" in text else "\n"
    out: list[str] = []
    removed_launch = 0
    removed_fx = 0
    for line in text.splitlines():
        if re.search(r"WeaponLaunchBone\s*=\s*PRIMARY\s+MISSILE01\b", line, re.I):
            removed_launch += 1
            continue
        if re.search(r"WeaponFireFXBone\s*=\s*PRIMARY\s+WEAPONFX\b", line, re.I):
            removed_fx += 1
            continue
        out.append(line)
    if removed_launch != 12:
        raise RuntimeError(f"expected 12 injected MISSILE01 launch bones, got {removed_launch}")
    if removed_fx != 12:
        raise RuntimeError(f"expected 12 injected PRIMARY WEAPONFX bones, got {removed_fx}")
    result = nl.join(out)
    if not result.endswith(nl):
        result += nl
    return result


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("VALIDATE FAIL: " + msg)


def slots_of(cs_text: str, name: str) -> dict[int, str]:
    m = re.search(
        rf"^CommandSet {re.escape(name)}\s*\r?\n(.*?)(?=^CommandSet |\Z)",
        cs_text,
        re.M | re.S,
    )
    require(m is not None, f"missing CS {name}")
    return {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", m.group(1), re.M)}


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> list[str]:
    notes: list[str] = []
    for key in (K_CS, K_CB, K_WPN, K_DF41, K_KHOR, K_RS24, K_WO):
        require(orig[key] == new[key], f"{key} must stay identical")

    fac = new[K_FAC].decode("latin1")
    live = new[K_DF41].decode("latin1")
    w = new[K_WPN].decode("latin1")
    wo = new[K_WO].decode("latin1")

    require("Object Factory_DF41Once" in fac, "factory object name")
    require(re.search(r"BuildCost\s*=\s*30000\b", fac) is not None, "price 30000")
    require("Weapon_Factory_DF41Once" in fac, "one-clip weapon")
    require("FactoryOnceFireCommandSet" in fac, "fire CS")
    require("ShowSubObject     = MISSILE01" in fac, "visible missile")
    require(
        re.search(r"WeaponLaunchBone\s*=\s*PRIMARY\s+WeaponA\b", fac) is not None,
        "live WeaponA launch bone lost",
    )
    require(
        re.search(r"WeaponLaunchBone\s*=\s*PRIMARY\s+MISSILE01\b", fac) is None,
        "injected MISSILE01 launch bone still present",
    )
    require("ChinaWarFactory" not in fac, "factory gated again")

    require("Object ChinaVehicleDF41" in live, "live DF-41 object")
    require(re.search(r"BuildCost\s*=\s*3500\b", live) is not None, "live DF-41 cost")
    require(
        re.search(r"WeaponLaunchBone\s*=\s*PRIMARY\s+MISSILE01\b", live) is None,
        "live DF-41 unexpectedly has MISSILE01 launch",
    )

    require("Weapon Weapon_Factory_DF41Once" in w, "factory weapon")
    require("AutoReloadsClip             = No" in w, "one-clip")
    require("ProjectileObject            = DF41_ICBM_Sgl_Object" in w, "live projectile")
    require("Object DF41_ICBM_Sgl_Object" in wo, "projectile object")
    require("KindOf = UNATTACKABLE PROJECTILE BALLISTIC_MISSILE" in wo, "ballistic kind")
    require("Locomotor = SET_NORMAL DF41MissileLocomotor" in wo, "air locomotor")
    require("DistanceToTravelBeforeTurning = 1750" in wo, "turn-after-climb")

    cs = new[K_CS].decode("latin1")
    cb = new[K_CB].decode("latin1")
    require("Object        = Factory_DF41Once" in cb, "slot N button")
    ru = slots_of(cs, "Russia_MissileFactoryCommandSet")
    require(ru[14] == "CB_FACTORY_SLOT_N", "Russia N")
    require(ru[13] == "CB_FACTORY_SLOT_M", "Russia M")
    require(ru[12] == "CB_FACTORY_SLOT_L", "Russia L")
    require(ru[11] == "CB_FACTORY_SLOT_K", "Russia K")
    iq = slots_of(cs, "Iraq_AlFahdMissileFactoryCommandSet")
    require(iq[14] == "CB_FACTORY_SLOT_N", "Iraq N")
    require(iq[13] == "CB_FACTORY_SLOT_M", "Iraq M")
    for i in range(1, 11):
        require(iq[i] == f"CB_MISSILE_{chr(ord('A') + i - 1)}", f"Iraq A-J {i}")

    notes.append("stripped_PRIMARY_MISSILE01=12")
    notes.append("kept_WeaponA=yes")
    notes.append("kept_oneclip_30000=yes")
    return notes


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    src_sha = hashlib.sha256(SRC_BIG.read_bytes()).hexdigest()
    if src_sha != SRC_SHA:
        raise SystemExit(f"source BIG sha mismatch: {src_sha}")
    orig = read_big(SRC_BIG)
    new = dict(orig)
    new[K_FAC] = strip_injected_missile01_launch(orig[K_FAC].decode("latin1")).encode("latin1")
    notes = validate(orig, new)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    blob = build_big(new)
    OUT_BIG.write_bytes(blob)
    digest = hashlib.sha256(blob).hexdigest()
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(digest + "\n", encoding="ascii")
    for name, key in (("CommandSet.ini", K_CS), ("CommandButton.ini", K_CB)):
        (OUT_DIR / name).write_bytes(new[key])
        (OUT_DIR / f"{name}.sha256").write_text(
            hashlib.sha256(new[key]).hexdigest() + "\n", encoding="ascii"
        )
    print("wrote", OUT_BIG, "bytes", len(blob), "sha256", digest, "entries", len(new))
    for n in notes:
        print(" ", n)


if __name__ == "__main__":
    main()
