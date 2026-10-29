#!/usr/bin/env python3
"""Give 18-country radar Shahed launchers the working Iran Fire path.

IranVehicleShahedLauncher (War Factory, BuildCost 1500) fires because:
  CommandSet = IranShahed136FireCommandSet -> Command_FireMainWeapon
  PRIMARY    = Weapon_Iran_Shahed136Launcher (Weapon.ini, AntiGround)
  projectile = Iran_Shahed136_FireProjectile (DumbProjectileBehavior)

SpecterRadar_ShahedLauncher is the shared radar copy for 18 countries.
It was identical except CommandSet = AmericaTankCrusaderCommandSet (no Fire
button) and PRIMARY = 5x_Shahed136DroneSwarm (Shahed136_AI_Object is a
selectable drone, not a weapon shot). AutoAcquireEnemiesWhenIdle = No, so
without FIRE_WEAPON the unit cannot shoot.

This packer only rewrites those two fields on SpecterRadar_ShahedLauncher.
BuildCost stays 8000. Iran object, Iran cost, Weapon.ini, CommandSet.ini
menus, and CommandButton.ini are not changed. IranShahed136FireCommandSet
is reused (no duplicate CommandSet).

Source: missile-jlmn-buttons _SPEC_DATA_ONE.big
(SHA c775c5cc5ae7ca1a4cb717b061c387ad044a737a19989b15496b88f6172da8ac).
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/MISSILE_JLMN_BUTTONS/_SPEC_DATA_ONE.big"
SRC_SHA = "c775c5cc5ae7ca1a4cb717b061c387ad044a737a19989b15496b88f6172da8ac"
OUT_DIR = ROOT / "Release/RADAR_SHAHED_FIRE"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_UAV = r"Data\INI\Object\Specter\SpecterRadarUavs.ini"
K_IRAN = r"Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini"
K_PROJ = r"Data\INI\Object\Specter\Iranian Army\Iran_Shahed136_FireProjectile.ini"

RADAR_COUNTRIES = (
    ("SwedenGM406CommandSet", "Sweden"),
    ("UkraineGM406CommandSet", "Ukraine"),
    ("TurkeyGM406CommandSet", "Turkey"),
    ("ItalyGM406CommandSet", "Italy"),
    ("BritainGM406CommandSet", "Britain"),
    ("GermanyGM406CommandSet", "Germany"),
    ("FranceGM406CommandSet", "France"),
    ("Iraq_RadarStationCommandSet", "Iraq"),
    ("India_RadarCommandSet", "India"),
    ("Pakistan_RadarCommandSet", "Pakistan"),
    ("Syria_RadarCommandSet", "Syria"),
    ("SaudiArabia_RadarCommandSet", "Saudi Arabia"),
    ("UAE_RadarCommandSet", "UAE"),
    ("Libya_RadarCommandSet", "Libya"),
    ("SouthAfrica_RadarCommandSet", "South Africa"),
    ("SouthKorea_RadarStationCommandSet", "South Korea"),
    ("Japan_RadarStationCommandSet", "Japan"),
    ("Vietnam_RadarStationCommandSet", "Vietnam"),
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


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_uav(text: str) -> str:
    body = block(text, "Object", "SpecterRadar_ShahedLauncher")
    require("Weapon = PRIMARY   5x_Shahed136DroneSwarm" in body, "radar PRIMARY is not swarm")
    require("CommandSet    = AmericaTankCrusaderCommandSet" in body, "radar CS is not Crusader")
    require("BuildCost       = 8000" in body, "radar cost is not 8000")
    new_body, n1 = body.replace(
        "Weapon = PRIMARY   5x_Shahed136DroneSwarm",
        "Weapon = PRIMARY   Weapon_Iran_Shahed136Launcher",
        1,
    ), 1
    require(body.count("Weapon = PRIMARY   5x_Shahed136DroneSwarm") == 1, "PRIMARY count")
    new_body, n2 = new_body.replace(
        "CommandSet    = AmericaTankCrusaderCommandSet",
        "CommandSet    = IranShahed136FireCommandSet",
        1,
    ), 1
    require(body.count("CommandSet    = AmericaTankCrusaderCommandSet") == 1, "CS count")
    require(n1 == 1 and n2 == 1, "replace counts")
    require("BuildCost       = 8000" in new_body, "cost lost in patch")
    require("5x_Shahed136DroneSwarm" not in new_body, "swarm still on radar object")
    return text.replace(body, new_body, 1)


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> None:
    require(orig[K_CS] == new[K_CS], "CommandSet.ini changed")
    require(orig[K_CB] == new[K_CB], "CommandButton.ini changed")
    require(orig[K_WPN] == new[K_WPN], "Weapon.ini changed")
    require(orig[K_IRAN] == new[K_IRAN], "IranVehicleShahedLauncher changed")
    require(orig[K_PROJ] == new[K_PROJ], "Fire projectile changed")

    changed = [k for k in orig if orig[k] != new[k]]
    require(changed == [K_UAV], f"unexpected files changed: {changed}")

    iran = orig[K_IRAN].decode("latin1")
    require("Object IranVehicleShahedLauncher" in iran, "Iran object name")
    require("Weapon = PRIMARY   Weapon_Iran_Shahed136Launcher" in iran, "Iran PRIMARY")
    require("CommandSet    = IranShahed136FireCommandSet" in iran, "Iran CS")
    require("BuildCost       = 1500" in iran, "Iran cost must stay 1500")

    uav = new[K_UAV].decode("latin1")
    radar = block(uav, "Object", "SpecterRadar_ShahedLauncher")
    require("Weapon = PRIMARY   Weapon_Iran_Shahed136Launcher" in radar, "radar PRIMARY")
    require("CommandSet    = IranShahed136FireCommandSet" in radar, "radar CS")
    require("BuildCost       = 8000" in radar, "radar cost 8000")
    require("5x_Shahed136DroneSwarm" not in radar, "radar still swarm")
    require("AmericaTankCrusaderCommandSet" not in radar, "radar still Crusader CS")
    require(uav.count("Object SpecterRadar_ShahedLauncher") == 1, "duplicate radar object")
    for other in ("SpecterRadar_Heron", "SpecterRadar_MQ4", "SpecterRadar_Orlan10"):
        require(
            block(orig[K_UAV].decode("latin1"), "Object", other) == block(uav, "Object", other),
            f"{other} changed",
        )

    cs = new[K_CS].decode("latin1")
    require(len(re.findall(r"(?m)^CommandSet IranShahed136FireCommandSet\b", cs)) == 1, "duplicate Fire CS")
    fire_cs = block(cs, "CommandSet", "IranShahed136FireCommandSet")
    require("Command_FireMainWeapon" in fire_cs, "Fire CS missing FireMainWeapon")
    crusader = block(cs, "CommandSet", "AmericaTankCrusaderCommandSet")
    require("Command_FireMainWeapon" not in crusader, "Crusader CS unexpectedly has Fire")
    require("Command_ConstructIranVehicleShahedLauncher" in block(cs, "CommandSet", "IranWarfactoryCommandSet"), "Iran WF launcher")
    iran_radar = block(cs, "CommandSet", "IranRadarStationCommandSet")
    require("Command_ConstructSpecterRadarShahedLauncher" not in iran_radar, "Iran radar gained shared launcher")
    require("Command_ConstructIranDroneShahed136" in iran_radar, "Iran radar lost drone Shahed")
    for name, _label in RADAR_COUNTRIES:
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
    require("Object        = SpecterRadar_ShahedLauncher" in btn, "construct object")
    fire_btn = block(cb, "CommandButton", "Command_FireMainWeapon")
    require("Command           = FIRE_WEAPON" in fire_btn, "Fire command")
    require("WeaponSlot        = PRIMARY" in fire_btn, "Fire slot")
    require("NEED_TARGET_POS" in fire_btn, "Fire needs target pos")

    wpn = new[K_WPN].decode("latin1")
    iran_w = block(wpn, "Weapon", "Weapon_Iran_Shahed136Launcher")
    require("AntiGround                  = Yes" in iran_w, "Iran weapon AntiGround")
    require("ProjectileObject            = Iran_Shahed136_FireProjectile" in iran_w, "Iran projectile")
    require(
        re.search(r"^[ \t]*AttackRange[ \t]*=[ \t]*3000\b", iran_w, re.M) is not None,
        "Iran weapon range",
    )
    proj = new[K_PROJ].decode("latin1")
    require("KindOf = PROJECTILE BALLISTIC_MISSILE" in proj, "projectile KindOf")
    require("DumbProjectileBehavior" in proj, "projectile behavior")

    obj_hits = [
        k
        for k, v in new.items()
        if b"Object SpecterRadar_ShahedLauncher" in v or b"Object  SpecterRadar_ShahedLauncher" in v
    ]
    require(obj_hits == [K_UAV], f"radar object also defined in {obj_hits}")


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    blob = SRC_BIG.read_bytes()
    require(sha256(blob) == SRC_SHA, "source BIG sha mismatch")
    orig = read_big(SRC_BIG)
    new = dict(orig)
    new[K_UAV] = patch_uav(orig[K_UAV].decode("latin1")).encode("latin1")
    validate(orig, new)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_blob = build_big(new)
    digest = sha256(out_blob)
    OUT_BIG.write_bytes(out_blob)
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(digest + "\n", encoding="ascii")
    lines = [f"{digest}  _SPEC_DATA_ONE.big"]
    for name, key in (("CommandSet.ini", K_CS), ("CommandButton.ini", K_CB)):
        (OUT_DIR / name).write_bytes(new[key])
        h = sha256(new[key])
        (OUT_DIR / f"{name}.sha256").write_text(h + "\n", encoding="ascii")
        lines.append(f"{h}  {name}")
    (OUT_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii")
    print("wrote", OUT_BIG, "bytes", len(out_blob), "sha256", digest)
    print("CS", sha256(new[K_CS]))
    print("CB", sha256(new[K_CB]))
    print("changed", K_UAV)


if __name__ == "__main__":
    main()
