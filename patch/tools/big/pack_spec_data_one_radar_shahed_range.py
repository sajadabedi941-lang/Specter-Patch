#!/usr/bin/env python3
"""Restore AttackRange 3000 on the 18-country radar Shahed launcher.

Confirmed from PR #706/#708/#711: Shahed-136 launcher range was raised to
AttackRange = 3000 (Weapon_Iran_Shahed136Launcher). Those PRs refused to
last-win 5x_Shahed136DroneSwarm so SpecterRadar_ShahedLauncher stayed at
1500. Live DATA still has that old swarm weapon on the radar copy.

This packer only:
- sets AttackRange of 5x_Shahed136DroneSwarm (sole user: SpecterRadar_ShahedLauncher)
  from 1500 to 3000
- sets VisionRange of SpecterRadar_ShahedLauncher from 600 to 3000 so the
  confirmed 3000 AttackRange is usable (same VisionRange #711 set on Iran)

Does not touch IranVehicleShahedLauncher, Weapon_Iran_Shahed136Launcher,
other radar UAV copies, CommandSet.ini, CommandButton.ini, factory K/L/M/N,
or the AD max-3 cap.

Source: ad-max-three _SPEC_DATA_ONE.big
(SHA 8728a24c3856850ff4d958b0b4d15dd443da13f299306fd16e57ea10f6432628).
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/AD_MAX_THREE/_SPEC_DATA_ONE.big"
SRC_SHA = "8728a24c3856850ff4d958b0b4d15dd443da13f299306fd16e57ea10f6432628"
OUT_DIR = ROOT / "Release/RADAR_SHAHED_RANGE"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_UAV = r"Data\INI\Object\Specter\SpecterRadarUavs.ini"
K_IRAN = r"Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini"
K_DF41 = r"Data\INI\Object\Specter\FactoryKLMN\Factory_DF41Once.ini"

RADAR_COUNTRIES = (
    "SwedenGM406CommandSet",
    "UkraineGM406CommandSet",
    "TurkeyGM406CommandSet",
    "ItalyGM406CommandSet",
    "BritainGM406CommandSet",
    "GermanyGM406CommandSet",
    "FranceGM406CommandSet",
    "Iraq_RadarStationCommandSet",
    "India_RadarCommandSet",
    "Pakistan_RadarCommandSet",
    "Syria_RadarCommandSet",
    "SaudiArabia_RadarCommandSet",
    "UAE_RadarCommandSet",
    "Libya_RadarCommandSet",
    "SouthAfrica_RadarCommandSet",
    "SouthKorea_RadarStationCommandSet",
    "Japan_RadarStationCommandSet",
    "Vietnam_RadarStationCommandSet",
)


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


def block(text: str, kind: str, name: str) -> str:
    m = re.search(rf"^{kind} {re.escape(name)}\s*\r?\n", text, re.M)
    if not m:
        raise SystemExit(f"missing {kind} {name}")
    n2 = re.search(rf"^{kind} ", text[m.end() :], re.M)
    end = m.end() + n2.start() if n2 else len(text)
    return text[m.start() : end]


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("VALIDATE FAIL: " + msg)


def patch_weapon(text: str) -> str:
    body = block(text, "Weapon", "5x_Shahed136DroneSwarm")
    require(
        re.search(r"^[ \t]*AttackRange[ \t]*=[ \t]*1500\b", body, re.M) is not None,
        "5x_Shahed136DroneSwarm AttackRange is not 1500",
    )
    new_body, n = re.subn(
        r"^([ \t]*AttackRange[ \t]*=[ \t]*)1500\b",
        r"\g<1>3000",
        body,
        count=1,
        flags=re.M,
    )
    require(n == 1, "did not replace 5x_Shahed136DroneSwarm AttackRange")
    return text.replace(body, new_body, 1)


def patch_uav(text: str) -> str:
    body = block(text, "Object", "SpecterRadar_ShahedLauncher")
    require("Weapon = PRIMARY   5x_Shahed136DroneSwarm" in body, "radar Shahed weapon changed")
    require("BuildCost       = 8000" in body, "radar Shahed cost changed")
    require(
        re.search(r"^[ \t]*VisionRange[ \t]*=[ \t]*600\b", body, re.M) is not None,
        "radar Shahed VisionRange is not 600",
    )
    new_body, n = re.subn(
        r"^([ \t]*VisionRange[ \t]*=[ \t]*)600\b",
        r"\g<1>3000",
        body,
        count=1,
        flags=re.M,
    )
    require(n == 1, "did not replace SpecterRadar_ShahedLauncher VisionRange")
    return text.replace(body, new_body, 1)


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> None:
    require(orig[K_CS] == new[K_CS], "CommandSet.ini changed")
    require(orig[K_CB] == new[K_CB], "CommandButton.ini changed")
    require(orig[K_IRAN] == new[K_IRAN], "IranVehicleShahedLauncher object changed")
    require(orig[K_DF41] == new[K_DF41], "Factory_DF41Once changed")
    cs = new[K_CS].decode("latin1")
    for name in RADAR_COUNTRIES:
        body = block(cs, "CommandSet", name)
        require(
            re.search(
                r"^\s*12\s*=\s*Command_ConstructSpecterRadarShahedLauncher\s*$",
                body,
                re.M,
            )
            is not None,
            f"{name} lost slot 12 Shahed",
        )
    cb = new[K_CB].decode("latin1")
    btn = block(cb, "CommandButton", "Command_ConstructSpecterRadarShahedLauncher")
    require("Object        = SpecterRadar_ShahedLauncher" in btn, "button object")
    require("ButtonImage   = specbtn_shahedlnchr" in btn, "button image")
    wpn = new[K_WPN].decode("latin1")
    swarm = block(wpn, "Weapon", "5x_Shahed136DroneSwarm")
    require(
        re.search(r"^[ \t]*AttackRange[ \t]*=[ \t]*3000\b", swarm, re.M) is not None,
        "swarm AttackRange not 3000",
    )
    require(
        re.search(r"^[ \t]*MinimumAttackRange[ \t]*=[ \t]*1000", swarm, re.M) is not None,
        "swarm MinimumAttackRange changed",
    )
    require("ProjectileObject            = Shahed136_AI_Object" in swarm, "swarm projectile")
    iran_w = block(wpn, "Weapon", "Weapon_Iran_Shahed136Launcher")
    require(
        re.search(r"^[ \t]*AttackRange[ \t]*=[ \t]*3000\b", iran_w, re.M) is not None,
        "Iran Shahed weapon range lost",
    )
    orig_w = orig[K_WPN].decode("latin1")
    require(
        block(orig_w, "Weapon", "Weapon_Iran_Shahed136Launcher") == iran_w,
        "Iran Shahed weapon block changed",
    )
    iran_obj = new[K_IRAN].decode("latin1")
    require("Weapon = PRIMARY   Weapon_Iran_Shahed136Launcher" in iran_obj, "Iran PRIMARY")
    require("BuildCost       = 1500" in iran_obj, "Iran cost")
    uav = new[K_UAV].decode("latin1")
    radar = block(uav, "Object", "SpecterRadar_ShahedLauncher")
    require("Weapon = PRIMARY   5x_Shahed136DroneSwarm" in radar, "radar still swarm PRIMARY")
    require("BuildCost       = 8000" in radar, "radar cost")
    require(
        re.search(r"^[ \t]*VisionRange[ \t]*=[ \t]*3000\b", radar, re.M) is not None,
        "radar VisionRange not 3000",
    )
    for other in ("SpecterRadar_Heron", "SpecterRadar_MQ4", "SpecterRadar_Orlan10"):
        require(
            block(orig[K_UAV].decode("latin1"), "Object", other)
            == block(uav, "Object", other),
            f"{other} changed",
        )
    # only two files may change
    changed = [k for k in orig if orig[k] != new[k]]
    require(set(changed) == {K_WPN, K_UAV}, f"unexpected files changed: {changed}")


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    blob = SRC_BIG.read_bytes()
    if hashlib.sha256(blob).hexdigest() != SRC_SHA:
        raise SystemExit("source BIG sha mismatch")
    orig = read_big(SRC_BIG)
    new = dict(orig)
    new[K_WPN] = patch_weapon(orig[K_WPN].decode("latin1")).encode("latin1")
    new[K_UAV] = patch_uav(orig[K_UAV].decode("latin1")).encode("latin1")
    validate(orig, new)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_blob = build_big(new)
    digest = hashlib.sha256(out_blob).hexdigest()
    OUT_BIG.write_bytes(out_blob)
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(digest + "\n", encoding="ascii")
    for name, key in (("CommandSet.ini", K_CS), ("CommandButton.ini", K_CB)):
        (OUT_DIR / name).write_bytes(new[key])
        (OUT_DIR / f"{name}.sha256").write_text(
            hashlib.sha256(new[key]).hexdigest() + "\n", encoding="ascii"
        )
    print("wrote", OUT_BIG, "bytes", len(out_blob), "sha256", digest)
    print("changed", K_WPN, "and", K_UAV)


if __name__ == "__main__":
    main()
