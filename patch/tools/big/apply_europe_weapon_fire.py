#!/usr/bin/env python3
"""Patch France/Germany/Italy/UK overlay aircraft INI for working weapons.

Does not rewrite Russia, China, USA, or other countries.
Does not change airbase CommandSets.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("/workspace/patch/Data/INI/Object/Specter")
SIDES = {
    "French Armed Forces": "France",
    "German Armed Forces": "Germany",
    "Italian Armed Forces": "Italy",
    "British Armed Forces": "Britain",
}
CANNON = {
    "France": "France_Weapon_Cannon_Jet",
    "Germany": "Germany_Weapon_JetCannon",
    "Italy": "Italy_Weapon_JetCannon",
    "Britain": "Britain_Weapon_JetCannon",
}
AWACS = {
    "FranceAircraftE3",
    "GermanyAircraftE3",
    "ItalyAircraftG550CAEW",
    "BritainAircraftE7",
}
TRANSPORT_HINTS = ("A400M", "C130", "C17", "C27J")
SECONDARY_SWAP = {
    "France_Weapon_Bomb_Mirage2000D": "France_Weapon_AASM_Mirage2000D",
}


def object_name(text: str) -> str:
    m = re.search(r"^Object (\S+)\s*$", text, re.M)
    if not m:
        raise SystemExit("missing Object name")
    return m.group(1)


def patch_launch_bones(text: str) -> str:
    if "WeaponLaunchBone    = TERTIARY" in text or re.search(r"WeaponLaunchBone\s+=\s+TERTIARY", text):
        return text
    text, n = re.subn(
        r"(WeaponLaunchBone\s+=\s+SECONDARY\s+\S+)",
        r"\1\n      WeaponLaunchBone    = TERTIARY  Weapon01",
        text,
        count=1,
    )
    return text


def rebuild_weaponset(block: str, cannon: str, aa: bool) -> str:
    primary = re.search(r"Weapon\s+=\s+PRIMARY\s+(\S+)", block)
    secondary = re.search(r"Weapon\s+=\s+SECONDARY\s+(\S+)", block)
    if not primary or not secondary:
        return block
    p = SECONDARY_SWAP.get(primary.group(1), primary.group(1))
    s = SECONDARY_SWAP.get(secondary.group(1), secondary.group(1))
    if aa:
        p_pref, s_pref, t_pref = "AIRCRAFT", "AIRCRAFT", "AIRCRAFT VEHICLE"
    else:
        p_pref, s_pref, t_pref = "VEHICLE STRUCTURE", "AIRCRAFT VEHICLE STRUCTURE", "INFANTRY VEHICLE STRUCTURE"
        if "Meteor" in p or "AMRAAM" in p or "AAM_" in p:
            p_pref = "AIRCRAFT"
        if "MICA" in s or "IRIST" in s or "AIM9" in s or "ASRAAM" in s or "AMRAAM" in s:
            s_pref = "AIRCRAFT"
        elif "Bomb" in s or "Paveway" in s or "JDAM" in s or "AASM" in s or "SCALP" in s or "Taurus" in s or "StormShadow" in s or "Brimstone" in s:
            s_pref = "VEHICLE STRUCTURE"
    return (
        "  WeaponSet\n"
        "    Conditions = None\n"
        f"    Weapon              = PRIMARY    {p}\n"
        f"    PreferredAgainst    = PRIMARY    {p_pref}\n"
        "    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        f"    Weapon              = SECONDARY  {s}\n"
        f"    PreferredAgainst    = SECONDARY  {s_pref}\n"
        "    AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        f"    Weapon              = TERTIARY   {cannon}\n"
        f"    PreferredAgainst    = TERTIARY   {t_pref}\n"
        "    AutoChooseSources   = TERTIARY   FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        "  End"
    )


def patch_drone_weaponset(block: str) -> str:
    primary = re.search(r"Weapon\s+=\s+PRIMARY\s+(\S+)", block)
    secondary = re.search(r"Weapon\s+=\s+SECONDARY\s+(\S+)", block)
    if not primary or not secondary:
        return block
    p, s = primary.group(1), secondary.group(1)
    return (
        "  WeaponSet\n"
        "    Conditions = None\n"
        f"    Weapon              = PRIMARY    {p}\n"
        "    PreferredAgainst    = PRIMARY    VEHICLE STRUCTURE\n"
        "    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        f"    Weapon              = SECONDARY  {s}\n"
        "    PreferredAgainst    = SECONDARY  VEHICLE STRUCTURE\n"
        "    AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI\n"
        "  End"
    )


def patch_jet_ai(text: str) -> str:
    text = re.sub(
        r"(OutOfAmmoDamagePerSecond\s+=\s+)10%",
        r"\g<1>0%",
        text,
        count=1,
    )
    if "AutoAcquireEnemiesWhenIdle" in text:
        text = re.sub(
            r"AutoAcquireEnemiesWhenIdle\s+=\s+No",
            "AutoAcquireEnemiesWhenIdle = Yes",
            text,
            count=1,
        )
    else:
        text = re.sub(
            r"(Behavior = JetAIUpdate[^\n]*\n(?:.*\n)*?)(    ReturnToBaseIdleTime\s+=\s+\d+\n)",
            r"\1\2    AutoAcquireEnemiesWhenIdle = Yes\n",
            text,
            count=1,
        )
        if "AutoAcquireEnemiesWhenIdle" not in text:
            text = re.sub(
                r"(Behavior = JetAIUpdate[^\n]*\n)",
                r"\1    AutoAcquireEnemiesWhenIdle = Yes\n",
                text,
                count=1,
            )
    return text


def patch_file(path: Path, side: str) -> bool:
    original = path.read_text(encoding="ascii")
    text = original.replace("\r\n", "\n").replace("\r", "\n")
    obj = object_name(text)
    changed = False

    if obj in AWACS:
        new = text.replace("CommandSet = GenericTacticalBomberCommandSet", "CommandSet = C17GlobalMasterCommandSet")
        if "CAN_ATTACK" in new:
            new = new.replace(" CAN_ATTACK", "")
        if new != text:
            path.write_bytes(new.encode("ascii") if new.endswith("\n") else (new + "\n").encode("ascii"))
            print(f"AWACS {obj}: radar CommandSet")
            return True
        return False

    if any(h in obj for h in TRANSPORT_HINTS) and "WeaponSet" not in text:
        return False
    if obj.startswith(side + "Helicopter") and "WeaponSet" not in text:
        return False

    if "Drone" in obj and "WeaponSet" in text:
        text = re.sub(
            r"  WeaponSet\n    Conditions = None\n(?:.*\n)*?  End",
            lambda m: patch_drone_weaponset(m.group(0)),
            text,
            count=1,
        )
        text = patch_jet_ai(text)
        if not text.endswith("\n"):
            text += "\n"
        if text != original.replace("\r\n", "\n").replace("\r", "\n"):
            path.write_bytes(text.encode("ascii"))
            print(f"drone {obj}")
            return True
        return False

    if "WeaponSet" in text and "HeliCannon" not in text and "Cannon_Tiger" not in text:
        aa = "F22A_AA_CommandSet" in text
        text = patch_launch_bones(text)
        cannon = CANNON[side]
        text = re.sub(
            r"  WeaponSet\n    Conditions = None\n(?:.*\n)*?  End",
            lambda m: rebuild_weaponset(m.group(0), cannon, aa),
            text,
            count=1,
        )
        text = patch_jet_ai(text)
        changed = True

    if changed:
        if not text.endswith("\n"):
            text += "\n"
        path.write_bytes(text.encode("ascii"))
        print(f"fighter {obj}")
        return True
    return False


def main() -> int:
    n = 0
    keep = re.compile(r"^(France|Germany|Italy|Britain)(Jet|Aircraft|Drone|Bomber|Helicopter)")
    for folder, side in SIDES.items():
        for sub in ("Airforce", "Rotary"):
            d = ROOT / folder / sub
            if not d.exists():
                continue
            for path in sorted(d.glob("*.ini")):
                if not keep.match(path.stem):
                    continue
                if patch_file(path, side):
                    n += 1
    print(f"patched {n} overlay object INI files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
