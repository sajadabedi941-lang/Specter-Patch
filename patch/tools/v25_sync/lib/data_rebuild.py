"""Independent DATA rebuild recipes for V25 sample equipment.

Planning only. Never writes SPECTER public INI (DamageFX.ini, Crate.ini, FXList.ini,
SpecialPower.ini) and never depends on CWC.exe.
"""
from __future__ import annotations

import re
from .rewrite import independent_name

# Unique-path clones. SPECTER public tables stay untouched even when the vanilla
# name already exists in INIZH / DATA BIG.
INDEPENDENT_DAMAGEFX = {
    "TankDamageFX": {
        "planned": "SD25_TankDamageFX",
        "unique_path": r"Data\INI\DamageFX_SilentDeath.ini",
        "never_patch": [r"Data\INI\DamageFX.ini", r"Data\INI\FXList.ini"],
        "reason": (
            "ArmorSet DamageFX is a DamageFX table, not an FXList. Clone V25 "
            "DamageFX.ini TankDamageFX onto a unique path so SPECTER DamageFX.ini is not patched."
        ),
    },
    "TruckDamageFX": {
        "planned": "SD25_TruckDamageFX",
        "unique_path": r"Data\INI\DamageFX_SilentDeath.ini",
        "never_patch": [r"Data\INI\DamageFX.ini", r"Data\INI\FXList.ini"],
        "reason": (
            "Independent unique-path clone of V25 DamageFX TruckDamageFX. SPECTER "
            "public DamageFX.ini is not rewritten."
        ),
    },
}

INDEPENDENT_CRATE = {
    "SalvageCrateData": {
        "planned": "SD25_SalvageCrateData",
        "unique_path": r"Data\INI\Crate_SilentDeath.ini",
        "never_patch": [r"Data\INI\Crate.ini"],
        "reason": (
            "CrateData (not CrateTemplate) table cloned unique-path. CrateObject "
            "SalvageCrate stays a native Generals object when SPECTER/stock already has it."
        ),
    },
}

PUBLIC_INI_BLOCKED = (
    r"Data\INI\DamageFX.ini",
    r"Data\INI\Crate.ini",
    r"Data\INI\FXList.ini",
    r"Data\INI\SpecialPower.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\Weapon.ini",
    r"Data\INI\Armor.ini",
    r"Data\INI\ObjectCreationList.ini",
)

RIDER_RE = re.compile(
    r"^\s*Rider(\d+)\s*=\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$",
    re.I | re.M,
)
WEAPONSET_RE = re.compile(
    r"WeaponSet\s+Conditions\s*=\s*(\S+).*?Weapon\s*=\s*PRIMARY\s+(\S+)",
    re.I | re.S,
)
OCL_POWER_RE = re.compile(
    r"Behavior\s*=\s*OCLSpecialPower\b.*?SpecialPowerTemplate\s*=\s*(\S+).*?OCL\s*=\s*(\S+)",
    re.I | re.S,
)
CREATE_OBJECT_RE = re.compile(
    r"ObjectNames\s*=\s*(\S+)",
    re.I,
)
CONTAIN_INSIDE_RE = re.compile(
    r"ContainInsideSourceObject\s*=\s*Yes",
    re.I,
)
DRAW_RIDER_RE = re.compile(
    r"ConditionState\s*=\s*RIDER2\b",
    re.I,
)
CIA_ENUM_RE = re.compile(
    r"Enum\s*=\s*SPECIAL_CIA_INTELLIGENCE",
    re.I,
)

# SAGE stock DeployStyleAIUpdate contract, proven by vanilla Tomahawk / NukeCannon / Scud
# and by V25's own SDSR5 (ChinaVehicle.ini) which already uses the module.
STOCK_DEPLOY_CONTRACT = {
    "module": "DeployStyleAIUpdate",
    "weaponset_flag": "DEPLOYED",
    "draw_states": ["PACKING", "UNPACKING", "DEPLOYED"],
    "command": "Command_Deploy",
    "command_is_toggle": True,
    "switches_commandset": False,
    "switches_locomotor_set": False,
    "pack_before_move": True,
}

HQ11_PACK_MS = 2000  # same as V25 SDSR5 DeployStyleAIUpdate; CWC rider swap time is not in INI.


def unique_ini_allowed(path: str) -> bool:
    low = path.replace("/", "\\").lower()
    return low not in {p.replace("/", "\\").lower() for p in PUBLIC_INI_BLOCKED}


def overlay_damagefx_row(row: dict) -> dict:
    spec = INDEPENDENT_DAMAGEFX.get(row.get("name") or "")
    if not spec or row.get("kind") != "DamageFX":
        return row
    out = dict(row)
    out["action"] = "INDEPENDENT_ADD"
    out["planned"] = spec["planned"]
    out["reason"] = spec["reason"]
    out["unique_path"] = spec["unique_path"]
    out["never_patch"] = list(spec["never_patch"])
    return out


def overlay_crate_row(row: dict) -> dict:
    name = row.get("name") or ""
    if row.get("kind") not in ("CrateData", "CrateTemplate"):
        return row
    spec = INDEPENDENT_CRATE.get(name)
    if not spec:
        return row
    out = dict(row)
    out["kind"] = "CrateData"
    out["action"] = "INDEPENDENT_ADD"
    out["planned"] = spec["planned"]
    out["reason"] = spec["reason"]
    out["unique_path"] = spec["unique_path"]
    out["never_patch"] = list(spec["never_patch"])
    return out


def overlay_independent_rows(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        if row.get("kind") == "DamageFX":
            out.append(overlay_damagefx_row(row))
        elif row.get("kind") in ("CrateData", "CrateTemplate"):
            out.append(overlay_crate_row(row))
        else:
            out.append(row)
    return out


def rewrite_map_from_rows(rows: list[dict]) -> dict[str, str]:
    mp = {}
    for row in rows:
        if row.get("action") in ("RENAME_AND_REWRITE", "INDEPENDENT_ADD"):
            old = row.get("name")
            new = row.get("planned")
            if old and new and old != new:
                mp[old] = new
    return mp


def clone_def_preview(kind: str, old_name: str, new_name: str, body: str) -> str:
    text = body or ""
    header = f"{kind} {new_name}"
    # Replace only the opening kind/name line.
    lines = text.splitlines()
    if lines:
        first = lines[0]
        if first.strip().lower().startswith(kind.lower()):
            lines[0] = header
        else:
            lines.insert(0, header)
    else:
        lines = [header, "End"]
    note = (
        f"; Independent unique-path clone of {kind} {old_name}. "
        "Preview only; SPECTER public INI is not written."
    )
    return note + "\n" + "\n".join(lines) + ("\n" if lines else "")


def parse_riders(body: str) -> list[dict]:
    out = []
    for m in RIDER_RE.finditer(body or ""):
        out.append(
            {
                "slot": int(m.group(1)),
                "object": m.group(2),
                "model_condition": m.group(3),
                "weaponset": m.group(4),
                "status": m.group(5),
                "commandset": m.group(6),
                "locomotor_set": m.group(7),
            }
        )
    return out


def parse_weaponsets(body: str) -> dict[str, str]:
    found = {}
    chunk = body or ""
    # Split on WeaponSet so PRIMARY belongs to the nearest Conditions.
    parts = re.split(r"(?i)\bWeaponSet\b", chunk)
    for part in parts[1:]:
        cond = re.search(r"Conditions\s*=\s*(\S+)", part, re.I)
        weap = re.search(r"Weapon\s*=\s*PRIMARY\s+(\S+)", part, re.I)
        if cond and weap:
            found[cond.group(1).upper()] = weap.group(1)
    return found


def parse_ocl_powers(body: str) -> list[dict]:
    found = []
    low = (body or "").lower()
    start = 0
    needle = "behavior = oclspecialpower"
    while True:
        i = low.find(needle, start)
        if i < 0:
            break
        chunk = (body or "")[i:]
        lines = []
        nest = 1
        for line in chunk.splitlines():
            t = line.strip().lower()
            if t.startswith("behavior =") and lines:
                break
            if t == "end":
                nest -= 1
                lines.append(line)
                if nest <= 0:
                    break
                continue
            lines.append(line)
        block = "\n".join(lines)
        sp = re.search(r"SpecialPowerTemplate\s*=\s*(\S+)", block, re.I)
        ocl = re.search(r"OCL\s*=\s*(\S+)", block, re.I)
        found.append(
            {
                "special_power": sp.group(1) if sp else None,
                "ocl": ocl.group(1) if ocl else None,
                "block": block,
            }
        )
        start = i + len(needle)
    return found


def ocl_is_fake_rider(ocl_rec: dict | None, rider_objects: set[str]) -> tuple[bool, str]:
    if not ocl_rec:
        return False, "OCL def not in V25 VFS"
    body = ocl_rec.get("body") or ""
    names = {m.group(1) for m in CREATE_OBJECT_RE.finditer(body)}
    if not names:
        return False, "OCL creates no ObjectNames"
    extra = {n for n in names if n.lower() not in {r.lower() for r in rider_objects}}
    if extra:
        return False, f"OCL creates non-rider objects: {sorted(extra)}"
    if not CONTAIN_INSIDE_RE.search(body):
        return False, "OCL does not set ContainInsideSourceObject = Yes"
    return True, "OCL only injects the fake rider inside the vehicle"


def special_power_is_cia_hijack(sp_rec: dict | None) -> bool:
    if not sp_rec:
        return False
    return bool(CIA_ENUM_RE.search(sp_rec.get("body") or ""))


def v25_has_stock_deploy(inventory: dict | None) -> bool:
    for rec in (inventory or {}).get("Object", {}).values():
        if "DeployStyleAIUpdate" in (rec.get("behaviors") or []):
            return True
    return False


def prove_rider_deploy(rec: dict | None, lookup_v25=None, inventory=None) -> dict:
    """Return a proof record. DeployStyleAIUpdate is used only when compatible is True."""
    empty = {
        "compatible": False,
        "use_deploy_style": False,
        "use_deployed_weaponset": False,
        "skip_refs": [],
        "limitations": [],
        "proven": [],
        "rebuild_for": {},
        "summary": "No Object record.",
        "pack_ms": HQ11_PACK_MS,
        "unpack_ms": HQ11_PACK_MS,
    }
    if not rec:
        return empty
    body = rec.get("body") or ""
    behaviors = rec.get("behaviors") or []
    riders = parse_riders(body)
    result = dict(empty)
    result["riders"] = riders
    result["weaponsets"] = parse_weaponsets(body)
    result["ocl_powers"] = parse_ocl_powers(body)
    result["has_rider_contain"] = "RiderChangeContain" in behaviors
    result["has_ocl_special"] = "OCLSpecialPower" in behaviors
    result["has_draw_rider2"] = bool(DRAW_RIDER_RE.search(body))
    result["stock_deploy_in_v25"] = v25_has_stock_deploy(inventory)

    if "RiderChangeContain" not in behaviors:
        result["summary"] = "No RiderChangeContain; DeployStyle mapping is not required."
        return result

    reasons_fail = []
    proven = []

    if len(riders) != 2:
        reasons_fail.append(f"RiderChangeContain has {len(riders)} rider slots; HQ11-style proof needs exactly 2.")
    else:
        r1, r2 = riders[0], riders[1]
        if r1["weaponset"].upper() != "WEAPON_RIDER1" or r2["weaponset"].upper() != "WEAPON_RIDER2":
            reasons_fail.append("Riders are not WEAPON_RIDER1 then WEAPON_RIDER2.")
        else:
            proven.append("Two rider slots encode packed vs deployed weapon flags.")
        if r1["model_condition"].upper() != "RIDER1" or r2["model_condition"].upper() != "RIDER2":
            reasons_fail.append("ModelConditions are not RIDER1 / RIDER2.")
        else:
            proven.append("Draw RIDER1 = packed, RIDER2 = deployed.")
        if r1["locomotor_set"].upper() != "SET_NORMAL" or r2["locomotor_set"].upper() != "SET_SLUGGISH":
            reasons_fail.append("Locomotor sets are not SET_NORMAL / SET_SLUGGISH.")
        else:
            proven.append("Packed uses SET_NORMAL; deployed uses SET_SLUGGISH (CWC-only switch).")

    weapons = result["weaponsets"]
    packed_w = weapons.get("WEAPON_RIDER1")
    deployed_w = weapons.get("WEAPON_RIDER2")
    if packed_w and packed_w.lower() == "none" and deployed_w and deployed_w.lower() != "none":
        proven.append(
            f"WeaponSet WEAPON_RIDER1 PRIMARY None / WEAPON_RIDER2 PRIMARY {deployed_w} "
            "maps 1:1 onto stock Conditions = None vs DEPLOYED."
        )
    else:
        reasons_fail.append(
            f"WeaponSets are not packed-None / deployed-weapon (got {weapons})."
        )

    if not result["has_draw_rider2"]:
        reasons_fail.append("Draw has no ConditionState = RIDER2 to map onto DEPLOYED.")
    else:
        proven.append("HQ11.HQ11 ONCE_BACKWARDS (packed) vs ONCE with MISSILE_C (deployed) stays on the same W3D.")

    rider_objects = {r["object"] for r in riders}
    skip = []
    ocl_ok = True
    if not result["ocl_powers"]:
        reasons_fail.append("No OCLSpecialPower modules to prove as rider-only injectors.")
        ocl_ok = False
    for power in result["ocl_powers"]:
        ocl_name = power.get("ocl")
        sp_name = power.get("special_power")
        ocl_rec = lookup_v25("ObjectCreationList", ocl_name) if lookup_v25 and ocl_name else None
        ok, why = ocl_is_fake_rider(ocl_rec, rider_objects)
        power["ocl_proof"] = why
        if not ok:
            ocl_ok = False
            reasons_fail.append(f"{ocl_name}: {why}")
        else:
            proven.append(f"{ocl_name}: {why}")
        sp_rec = lookup_v25("SpecialPower", sp_name) if lookup_v25 and sp_name else None
        if special_power_is_cia_hijack(sp_rec):
            proven.append(
                f"{sp_name} uses SPECIAL_CIA_INTELLIGENCE; it must not be imported (would hijack CIA intel)."
            )
        if ocl_name:
            skip.append(("ObjectCreationList", ocl_name))
        if sp_name:
            skip.append(("SpecialPower", sp_name))
    if ocl_ok:
        proven.append("OCLSpecialPower exists only to inject fake riders; stock Command_Deploy replaces it.")

    for obj in rider_objects:
        skip.append(("Object", obj))
    for r in riders:
        skip.append(("CommandSet", r["commandset"]))

    limitations = [
        {
            "capability": "Runtime CommandSet swap (packed vs deployed button labels)",
            "v25": "RiderChangeContain overrides CommandSet per rider (CWCruS300CommandSet vs DeployedCommandSet).",
            "stock": "DeployStyleAIUpdate does not swap CommandSet. One unique CommandSet with Command_Deploy + Command_Stop.",
            "kept": "State swap (pack/unpack) stays. Separate SHIFANG/BUSHU labels collapse to one Deploy toggle.",
        },
        {
            "capability": "SET_SLUGGISH locomotor while deployed",
            "v25": "Rider2 binds SET_SLUGGISH CWCruS300DeployedLocomotor so the TEL can crawl while unpacked.",
            "stock": "DeployStyleAIUpdate does not switch LocomotorSet. The unit packs, then moves on SET_NORMAL.",
            "kept": "Settled firing posture is kept. Slow-move-while-deployed is not available on stock Generals.exe.",
        },
        {
            "capability": "Pack / unpack duration",
            "v25": "CWC rider swap timing is not an INI PackTime; ScuttleDelay=1500 is TOPPLED scuttle, not pack.",
            "stock": f"PackTime = UnpackTime = {HQ11_PACK_MS} copied from V25 SDSR5 DeployStyleAIUpdate in the same ChinaVehicle.ini.",
            "kept": "Pack/unpack exists. Exact CWC millisecond timing is not claimed.",
        },
    ]

    use = (
        not reasons_fail
        and result["has_rider_contain"]
        and result["has_ocl_special"]
        and result["has_draw_rider2"]
    )
    # Stock module does not have to appear on this object; it must exist as a SAGE module.
    # V25 SDSR5 proves the same INI tree already authors DeployStyleAIUpdate.
    if use and inventory is not None and not result["stock_deploy_in_v25"]:
        # Tests may omit a second object; the SAGE contract is still used if the INI pattern matches.
        proven.append(
            "DeployStyleAIUpdate is a stock ZH module (Tomahawk/NukeCannon/Scud). "
            "A second V25 object using it was not in this inventory snapshot."
        )
    elif use and result["stock_deploy_in_v25"]:
        proven.append("V25 itself already authors DeployStyleAIUpdate (e.g. SDSR5) in the same vehicle INI.")

    result["compatible"] = use
    result["use_deploy_style"] = use
    result["use_deployed_weaponset"] = use
    result["skip_refs"] = skip if use else []
    result["limitations"] = limitations if use else [{"capability": "DeployStyle mapping", "kept": "not used", "stock": "; ".join(reasons_fail) or "pattern mismatch", "v25": "RiderChangeContain present"}]
    result["proven"] = proven
    result["fail_reasons"] = reasons_fail
    result["deployed_weapon"] = deployed_w
    result["packed_weapon"] = packed_w
    if use:
        result["summary"] = (
            "RiderChangeContain + rider-only OCLSpecialPower is proven equivalent to "
            "stock DeployStyleAIUpdate + WeaponSet Conditions = DEPLOYED for pack/unpack "
            "and fire-only-when-deployed. CommandSet swap and SET_SLUGGISH-while-deployed are not."
        )
        result["rebuild_for"] = {
            "RiderChangeContain": {
                "action": "INDEPENDENT_ADD",
                "keep_capability": "packed vs deployed weapon and draw; pack/unpack",
                "specter_safe": [
                    "Do not copy RiderChangeContain onto SPECTER. It is CWC.exe-only.",
                    "Replace with DeployStyleAIUpdate on the unique Object (PackTime/UnpackTime "
                    f"{HQ11_PACK_MS}, TurretsFunctionOnlyWhenDeployed = Yes, "
                    "TurretsMustCenterBeforePacking = Yes, ResetTurretBeforePacking = Yes).",
                    "Map Draw RIDER1 → DefaultConditionState / PACKING; RIDER2 → DEPLOYED / UNPACKING.",
                    "Map WeaponSet WEAPON_RIDER1 → Conditions = None PRIMARY None; "
                    "WEAPON_RIDER2 → Conditions = DEPLOYED PRIMARY <missile>.",
                    "Do not spawn fake-rider infantry.",
                ],
            },
            "OCLSpecialPower": {
                "action": "INDEPENDENT_ADD",
                "keep_capability": "button that switches packed/deployed state",
                "specter_safe": [
                    "Do not import OCLSpecialPower, the CIA-intel SpecialPower templates, or the fake-rider OCLs.",
                    "Replace both buttons with stock Command_Deploy on one unique CommandSet (plus Command_Stop).",
                    "SPECIAL_CIA_INTELLIGENCE must not be reused; it would hijack SPECTER CIA intel.",
                ],
            },
        }
        result["independent_modules"] = hq11_independent_modules(deployed_w)
        result["unique_commandset"] = {
            "name": "SD25_ChinaHQ11CommandSet",
            "unique_path": r"Data\INI\CommandSet_ZZZZ_SilentDeath_China.ini",
            "buttons": ["Command_Deploy", "Command_Stop"],
            "never_patch": [r"Data\INI\CommandSet.ini", r"Data\INI\CommandButton.ini"],
        }
    else:
        result["summary"] = "DeployStyleAIUpdate is NOT used: " + (
            "; ".join(reasons_fail) or "pattern not proven"
        )
        result["rebuild_for"] = {
            "RiderChangeContain": {
                "action": "MANUAL_REBUILD",
                "keep_capability": "deployed vs undeployed weapon set",
                "specter_safe": ["Do not copy RiderChangeContain. Compatibility with DeployStyleAIUpdate was not proven."],
            },
            "OCLSpecialPower": {
                "action": "MANUAL_REBUILD",
                "keep_capability": "state-swap button",
                "specter_safe": ["Do not import CWC OCLSpecialPower templates until a stock equivalent is proven."],
            },
        }
    return result


def hq11_independent_modules(deployed_weapon: str | None) -> str:
    weap = deployed_weapon or "HQ11MissileWeapon"
    return f"""; Independent unique-path preview for ChinaHQ11 DATA. Not written to disk.
; SPECTER public INI / CWC.exe are not used.

  WeaponSet
    Conditions = None
    Weapon = PRIMARY None
  End
  WeaponSet
    Conditions = DEPLOYED
    Weapon = PRIMARY {weap}
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_AI FROM_SCRIPT
    PreferredAgainst = PRIMARY BALLISTIC_MISSILE AIRCRAFT
  End
  CommandSet = SD25_ChinaHQ11CommandSet

  Behavior = DeployStyleAIUpdate ModuleTag_Deploy
    AutoAcquireEnemiesWhenIdle = Yes Stealthed
    PackTime = {HQ11_PACK_MS}
    UnpackTime = {HQ11_PACK_MS}
    TurretsFunctionOnlyWhenDeployed = Yes
    TurretsMustCenterBeforePacking = Yes
    ResetTurretBeforePacking = Yes
  End
  Locomotor = SET_NORMAL CWCruS300Locomotor
  ; SET_SLUGGISH CWCruS300DeployedLocomotor is NOT bound: stock DeployStyle cannot switch locomotor sets.

  ; Removed (CWC.exe / CIA hijack — capability kept via DeployStyle + Command_Deploy):
  ;   RiderChangeContain, OCLSpecialPower x2, fake-rider Objects, SpecialAbilityCWCruFakeRider_*
"""


def apply_deploy_overlay(rows: list[dict], proof: dict) -> list[dict]:
    if not proof or not proof.get("use_deploy_style"):
        return rows
    skip = {(k.lower(), n.lower()) for k, n in (proof.get("skip_refs") or [])}
    out = []
    for row in rows:
        key = (row.get("kind", "").lower(), (row.get("name") or "").lower())
        if key in skip:
            continue
        if row.get("kind") == "BehaviorModule" and row.get("name") in ("RiderChangeContain", "OCLSpecialPower"):
            reb = (proof.get("rebuild_for") or {}).get(row["name"]) or {}
            row = dict(row)
            row["action"] = reb.get("action") or "INDEPENDENT_ADD"
            row["reason"] = proof.get("summary") or row.get("reason")
            row["limitations"] = proof.get("limitations")
            row["proven"] = proof.get("proven")
        out.append(row)
    # Unique CommandSet is an independent add, not a copy of the CWC sets.
    ucs = proof.get("unique_commandset") or {}
    if ucs:
        out.append(
            {
                "kind": "CommandSet",
                "name": ucs["name"],
                "action": "INDEPENDENT_ADD",
                "planned": ucs["name"],
                "source": "stage4-independent",
                "reason": "One unique CommandSet with stock Command_Deploy + Command_Stop. CWC packed/deployed sets are not imported.",
                "unique_path": ucs.get("unique_path"),
                "never_patch": ucs.get("never_patch"),
            }
        )
    return out


def unique_data_files(rows: list[dict], dest_ini: str | None) -> list[str]:
    files = []
    seen = set()
    for path in [dest_ini] + [r.get("unique_path") for r in rows if r.get("unique_path")]:
        if not path:
            continue
        if path.lower() in seen:
            continue
        seen.add(path.lower())
        files.append(path)
    return files


def public_ini_leaks(paths: list[str]) -> list[str]:
    blocked = {p.replace("/", "\\").lower() for p in PUBLIC_INI_BLOCKED}
    leaks = []
    for path in paths:
        if (path or "").replace("/", "\\").lower() in blocked:
            leaks.append(path)
    return leaks


def independent_name_or(name: str) -> str:
    return independent_name(name)
