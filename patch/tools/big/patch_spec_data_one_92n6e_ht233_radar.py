#!/usr/bin/env python3
"""Patch SPE _SPEC_DATA_ONE.big so 92N6E (S-400) and HT-233 (HQ-9) radars
can cue their batteries.

SAGE does not share VisionRange from an independent radar to a launcher.
S-400 / HQ-9 ABM (and S-400 AA) spawn AirdefenseLinkRestarter, which pulses
STATUS NO_ATTACK onto colocated FCS. The designed cue is FireControlRadarDataLink
(SURRENDER / EXTRA_6) killing that restarter (PowerCircleArmor SURRENDER 9999%).

Effective CombatMode DataLink had no DamageDealtAtSelfPosition, so FireWeaponUpdate
does not pulse at the radar and never reaches the restarter. RadarTrackingBeam
is STATUS paint only and is not the intercept path.

This rebuild starts from the GM AD ABM-fix BIG and last-wins only these two
radars plus essential aliases/OCLs. Interceptor weapons are not edited.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path


def read_big(path: Path) -> tuple[list[tuple[str, int, int]], bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def must_replace(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 occurrence of unique block, found {n}")
    return text.replace(old, new)


def decode(raw: bytes) -> tuple[str, str]:
    nl = "\r\n" if b"\r\n" in raw else "\n"
    return raw.decode("latin1"), nl


def encode(text: str) -> bytes:
    return text.encode("latin1")


def normalize_newlines(text: str, nl: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if nl == "\r\n":
        return text.replace("\n", "\r\n")
    return text


def extract_object(text: str, name: str) -> str:
    pat = re.compile(
        rf"(?m)^Object\s+{re.escape(name)}\b.*?(?=^Object\s|\Z)",
        re.S,
    )
    m = pat.search(text)
    if not m:
        raise SystemExit(f"missing Object {name}")
    return m.group(0).rstrip() + "\n"


WEAPON_ZZZZ = r"""
; SPECTER last-win inside _SPEC_DATA_ONE.big.
; Sorts after Weapon.ini. 92N6E / HT-233 fire-control pulse only.
; Kills AirdefenseLinkRestarter (PowerCircleArmor SURRENDER) at the radar.
; Does not last-win interceptor weapons.

Weapon 92N6R_FireControlDataLink
  PrimaryDamage             = 2500
  PrimaryDamageRadius       = 1800
  DamageType                = SURRENDER
  DeathType                 = EXTRA_6
  RadiusDamageAffects       = ALLIES
  DamageDealtAtSelfPosition = Yes
  DelayBetweenShots         = 100
  WeaponSpeed               = 99999
  AttackRange               = 1
  AntiGround                = Yes
  AntiAirborneVehicle       = Yes
  AntiBallisticMissile      = Yes
End

Weapon HT233_FireControlDataLink
  PrimaryDamage             = 2500
  PrimaryDamageRadius       = 1600
  DamageType                = SURRENDER
  DeathType                 = EXTRA_6
  RadiusDamageAffects       = ALLIES
  DamageDealtAtSelfPosition = Yes
  DelayBetweenShots         = 100
  WeaponSpeed               = 99999
  AttackRange               = 1
  AntiGround                = Yes
  AntiAirborneVehicle       = Yes
  AntiBallisticMissile      = Yes
End
"""

OCL_ZZZZ = r"""
; SPECTER last-win inside _SPEC_DATA_ONE.big.
; Sorts after ObjectCreationList.ini and ObjectCreationList_ZZZZ_ZZGmAdAbm.ini.

; Weapon 92N6E_Deploy referenced this OCL; it was missing.
ObjectCreationList OCL_92N6E_Deployed
  CreateObject
    ObjectNames           = Russia_92N6R_CombatMode
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
End

; HQ-9 AA deploy spawned only CombatMode (no FCS, no restarter), so HT-233
; had no launcher FCS to cue. Parallel to OCL_S400R_Deployed.
ObjectCreationList OCL_HQ9_Deployed
  CreateObject
    ObjectNames           = ChinaVehicleHQ9_CombatMode
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = HQ9_FireControlSystem
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = AirdefenseLinkRestarter
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
End
"""

BUTTON_ZZZZ = r"""
; SPECTER last-win. Command_ConstructRussian_92N6E built missing Object Russia_92N6R.
; Packed vehicle RussiaVehicle92N6R is the effective S-400 engagement radar.

CommandButton Command_ConstructRussian_92N6E
  Command       = UNIT_BUILD
  Object        = RussiaVehicle92N6R
  TextLabel     = CONTROLBAR:Construct92N6R
  ButtonImage   = rus_92n6r
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTip92N6R
End

CommandButton Command_ConstructRussian_92N6E_AI
  Command       = UNIT_BUILD
  Object        = RussiaVehicle92N6R
  TextLabel     = CONTROLBAR:Construct92N6R
  ButtonImage   = rus_92n6r
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTip92N6R
End
"""


def patch_92n6r_combat(text: str) -> str:
    return must_replace(
        text,
        "  Behavior                    = FireWeaponUpdate ModuleTag_FCRL\n"
        "    Weapon                    = FireControlRadarDataLink\n"
        "    ExclusiveWeaponDelay      = 1000\n"
        "  End\n",
        "  Behavior                    = FireWeaponUpdate ModuleTag_FCRL\n"
        "    Weapon                    = 92N6R_FireControlDataLink\n"
        "  End\n",
        "92N6R CombatMode DataLink",
    )


def patch_ht233_combat(text: str) -> str:
    return must_replace(
        text,
        "  Behavior                    = FireWeaponUpdate ModuleTag_FCRL\n"
        "    Weapon                    = FireControlRadarDataLink\n"
        "    ExclusiveWeaponDelay      = 1000\n"
        "  End\n",
        "  Behavior                    = FireWeaponUpdate ModuleTag_FCRL\n"
        "    Weapon                    = HT233_FireControlDataLink\n"
        "  End\n",
        "HT233 CombatMode DataLink",
    )


INPLACE = {
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\92N6R.ini": patch_92n6r_combat,
    r"Data\INI\Object\Specter\PLA\AirDefense\HT233.ini": patch_ht233_combat,
}


def last_win_block(file_map: dict[str, bytes], kind: str, name: str) -> str | None:
    pat = re.compile(
        rf"(?m)^{kind}\s+{re.escape(name)}\b.*?(?=^(?:Object|Weapon|Armor|CommandButton|CommandSet|ObjectCreationList|Upgrade)\s|\Z)",
        re.S,
    )
    last = None
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        text = raw.decode("latin1")
        for m in pat.finditer(text):
            last = m.group(0)
    return last


def validate(file_map: dict[str, bytes]) -> None:
    w = b"".join(v for k, v in file_map.items() if k.lower().endswith(".ini"))
    text = w.decode("latin1")

    if "Weapon 92N6R_FireControlDataLink" not in text:
        raise SystemExit("missing 92N6R_FireControlDataLink")
    if "Weapon HT233_FireControlDataLink" not in text:
        raise SystemExit("missing HT233_FireControlDataLink")
    if "DamageDealtAtSelfPosition = Yes" not in last_win_block(file_map, "Weapon", "92N6R_FireControlDataLink"):
        raise SystemExit("92N6R DataLink missing DamageDealtAtSelfPosition")
    if "DamageDealtAtSelfPosition = Yes" not in last_win_block(file_map, "Weapon", "HT233_FireControlDataLink"):
        raise SystemExit("HT233 DataLink missing DamageDealtAtSelfPosition")

    cs = last_win_block(file_map, "Object", "Russia_92N6R_CombatMode") or ""
    if "92N6R_FireControlDataLink" not in cs:
        raise SystemExit("92N6R CombatMode not using 92N6R_FireControlDataLink")
    if "FireControlRadarDataLink" in cs:
        raise SystemExit("92N6R CombatMode still uses stock DataLink")

    ht = last_win_block(file_map, "Object", "ChinaVehicleHT233_CombatMode") or ""
    if "HT233_FireControlDataLink" not in ht:
        raise SystemExit("HT233 CombatMode not using HT233_FireControlDataLink")
    if "FireControlRadarDataLink" in ht:
        raise SystemExit("HT233 CombatMode still uses stock DataLink")

    btn = last_win_block(file_map, "CommandButton", "Command_ConstructRussian_92N6E") or ""
    if "Object        = RussiaVehicle92N6R" not in btn:
        raise SystemExit("92N6E button still not targeting RussiaVehicle92N6R")
    if last_win_block(file_map, "Object", "RussiaVehicle92N6R") is None:
        raise SystemExit("RussiaVehicle92N6R missing")
    if last_win_block(file_map, "Object", "Russia_92N6R") is None:
        raise SystemExit("alias Object Russia_92N6R missing")

    ocl_e = last_win_block(file_map, "ObjectCreationList", "OCL_92N6E_Deployed") or ""
    if "Russia_92N6R_CombatMode" not in ocl_e:
        raise SystemExit("OCL_92N6E_Deployed missing CombatMode")

    ocl_hq = last_win_block(file_map, "ObjectCreationList", "OCL_HQ9_Deployed") or ""
    if "HQ9_FireControlSystem" not in ocl_hq:
        raise SystemExit("OCL_HQ9_Deployed missing HQ9_FireControlSystem")
    if "AirdefenseLinkRestarter" not in ocl_hq:
        raise SystemExit("OCL_HQ9_Deployed missing restarter (would allow fire without radar)")

    # Interceptors / other systems must stay as in the source ABM-fix BIG.
    if "Weapon 10x_PAC3_MSE_ABM" not in text:
        raise SystemExit("Patriot weapon missing")
    abm = last_win_block(file_map, "Weapon", "3x_LRSAM_40N6KMissile_ABM") or ""
    if "DamageType                 = CRUSH" not in abm and "DamageType                  = CRUSH" not in abm:
        raise SystemExit("S-400 ABM interceptor CRUSH lost")
    hqabm = last_win_block(file_map, "Weapon", "Hq9_AA_Missile_ABM") or ""
    if "CRUSH" not in hqabm:
        raise SystemExit("HQ-9 ABM interceptor CRUSH lost")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    args = ap.parse_args()

    entries, raw = read_big(args.src_big)
    file_map: dict[str, bytes] = {}
    for name, off, size in entries:
        file_map[name] = raw[off : off + size]

    changed = []
    for inner, fn in INPLACE.items():
        if inner not in file_map:
            raise SystemExit(f"missing inner file {inner}")
        text, nl = decode(file_map[inner])
        work = text.replace("\r\n", "\n")
        patched = fn(work)
        patched = normalize_newlines(patched, nl)
        if patched == text:
            raise SystemExit(f"no change applied to {inner}")
        file_map[inner] = encode(patched)
        changed.append(inner)

    rus_ini = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\92N6R.ini"
    rus_text, rus_nl = decode(file_map[rus_ini])
    packed = extract_object(rus_text.replace("\r\n", "\n"), "RussiaVehicle92N6R")
    alias = packed.replace("Object RussiaVehicle92N6R", "Object Russia_92N6R", 1)
    if alias == packed:
        raise SystemExit("failed to rename RussiaVehicle92N6R alias")
    alias_path = r"Data\INI\Object\zzzz_Specter92N6Ht233\Russia_92N6R.ini"
    extras = {
        r"Data\INI\Weapon_ZZZZ_ZZZ92N6Ht233.ini": WEAPON_ZZZZ,
        r"Data\INI\ObjectCreationList_ZZZZ_ZZZ92N6Ht233.ini": OCL_ZZZZ,
        r"Data\INI\CommandButton_ZZZZ_ZZZ92N6E.ini": BUTTON_ZZZZ,
        alias_path: "; Alias for Command_ConstructRussian_92N6E / scripts that spawn Russia_92N6R.\n"
        + alias,
    }
    for name, body in extras.items():
        if name in file_map:
            raise SystemExit(f"already present: {name}")
        file_map[name] = encode(normalize_newlines(body.replace("\r\n", "\n"), "\r\n"))
        changed.append(name + " (added)")

    validate(file_map)

    args.out_big.parent.mkdir(parents=True, exist_ok=True)
    out = build_big(file_map)
    args.out_big.write_bytes(out)

    rebuilt, rraw = read_big(args.out_big)
    if len(rebuilt) != len(file_map):
        raise SystemExit("rebuild entry count mismatch")
    hdr_size = struct.unpack(">I", rraw[4:8])[0]
    if hdr_size != len(rraw):
        raise SystemExit(f"BIG size field {hdr_size} != file {len(rraw)}")

    src_sha = sha256(args.src_big)
    out_sha = sha256(args.out_big)
    print(f"SRC  size={args.src_big.stat().st_size} sha256={src_sha}")
    print(f"OUT  size={args.out_big.stat().st_size} sha256={out_sha} entries={len(file_map)}")
    print("Changed:")
    for c in changed:
        print(f"  {c}")
    Path(str(args.out_big) + ".sha256").write_text(out_sha + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
