"""SPECTER gameplay compatibility notes. Never rewrites public SPECTER defs."""
from __future__ import annotations

from . import ini


def specter_damage_types(spec_vfs: dict) -> set[str]:
    types: set[str] = set()
    for rec in (spec_vfs.get("Armor") or {}).values():
        for t in rec.get("damage_types") or []:
            types.add(t.upper())
        # Older parsed recs without damage_types.
        if not rec.get("damage_types"):
            for k, v in rec.get("keys") or []:
                if k.strip().lower() == "armor":
                    for tok in v.replace("%", " ").split():
                        if not tok.replace(".", "", 1).isdigit():
                            types.add(tok.upper())
    return types


def weapon_targeting(rec: dict) -> dict:
    flags = {}
    for k, v in rec.get("keys") or []:
        kl = k.strip().lower()
        if kl.startswith("anti"):
            flags[k.strip()] = v.split()[0] if v.strip() else ""
    dts = rec.get("damage_types") or []
    if not dts:
        dts = [
            v.split()[0]
            for k, v in rec.get("keys") or []
            if k.strip().lower() == "damagetype" and v.strip()
        ]
    return {"anti": flags, "damage_types": dts}


def compatibility_notes(
    object_rec: dict,
    weapon_recs: list[dict],
    spec_damage: set[str],
    rules: dict,
) -> list[dict]:
    """Return reasoned notes. Empty anti flags are reported, not invented."""
    notes = []
    kindof = set()
    extra = []
    for k, v in object_rec.get("keys") or []:
        kl = k.strip().lower()
        if kl == "kindof":
            kindof.update(t.upper() for t in v.split())
        if kl == "extrarequiredkindof":
            extra.extend(t.upper() for t in v.split())
    air_keys = [x.lower() for x in rules["specter_targeting"]["air_flags"]]
    ground_keys = [x.lower() for x in rules["specter_targeting"]["ground_flags"]]
    air_yes = False
    ground_yes = False
    for w in weapon_recs:
        tgt = weapon_targeting(w)
        for fk, fv in tgt["anti"].items():
            if fk.lower() in air_keys and fv.lower() == "yes":
                air_yes = True
            if fk.lower() in ground_keys and fv.lower() == "yes":
                ground_yes = True
        for dt in tgt["damage_types"]:
            if dt.upper() in (
                "NORMAL",
                "NONE",
                "EXPLODED",
                "CRUSHED",
                "BURNED",
                "SUICIDED",
                "POISONED",
                "LASERED",
                "DETONATED",
            ):
                continue
            if dt.upper() in spec_damage:
                notes.append(
                    {
                        "rule": "damage_type_present_on_specter_armor",
                        "weapon": w.get("name"),
                        "damage_type": dt,
                        "decision": "REUSE_NATIVE",
                        "reason": (
                            f"DamageType {dt} already appears in SPECTER Armor tables, "
                            "so this unique weapon can injure SPECTER units that use those tables. "
                            "SPECTER Armor.ini is not modified."
                        ),
                    }
                )
            else:
                notes.append(
                    {
                        "rule": "unknown_damage_type",
                        "weapon": w.get("name"),
                        "damage_type": dt,
                        "decision": "INDEPENDENT_ADD",
                        "reason": (
                            f"DamageType {dt} is not on SPECTER Armor tables. "
                            "Do not patch SPECTER Armor. Keep it on the new unique weapon and "
                            "expect native SPECTER units to ignore it until a unique companion is designed."
                        ),
                    }
                )
    if extra:
        notes.append(
            {
                "rule": "stealth_detector_filter",
                "extra_required_kindof": extra,
                "decision": "REUSE_NATIVE",
                "reason": "StealthDetector ExtraRequiredKindOf uses stock KindOf tokens already on SPECTER aircraft.",
            }
        )
    if "CAN_ATTACK" in kindof and not air_yes and not ground_yes:
        notes.append(
            {
                "rule": "no_anti_flags_on_weapons",
                "decision": "MANUAL_REBUILD",
                "reason": "CAN_ATTACK object has no AntiGround/AntiAir* = Yes on parsed weapons; targeting vs SPECTER is unverified.",
            }
        )
    if air_yes:
        notes.append(
            {
                "rule": "antiair_flags_present",
                "decision": "KEEP_V25_FLAGS",
                "reason": "Weapon already sets AntiAirborneVehicle and/or anti-missile flags. SPECTER aircraft/missiles keep their KindOf; no SPECTER rewrite.",
            }
        )
    if ground_yes:
        notes.append(
            {
                "rule": "antiground_flags_present",
                "decision": "KEEP_V25_FLAGS",
                "reason": "Weapon already sets AntiGround=Yes. SPECTER ground Armor is not rewritten.",
            }
        )
    return notes


def effective_equal(a: dict | None, b: dict | None) -> bool:
    if not a or not b:
        return False
    return ini.gameplay_fingerprint(a) == ini.gameplay_fingerprint(b)
