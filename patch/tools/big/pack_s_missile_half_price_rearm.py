#!/usr/bin/env python3
"""Half-price immediate re-arm for Alabaas-pattern ICBM/TELs and Iraq factory TELs.

Baseline: PR #593 SPECTER_IRAQ_MISSILE_TOP_MARKINGS (DATA+ART).
ART is a byte-identical copy. DATA only.

Reference mechanic (Iraq_Alhussaien / Alabaas ICBM):
  FireOCL OCL_HussienMissileDisarm -> unarmed rider / no fire
  OBJECT_UPGRADE -> ObjectCreationUpgrade -> OCL inserts armed rider
  UpgradeDie removes the OBJECT upgrade so it can be bought again

This packer:
  * Gives every existing Alhussaien-rearm launcher its own OBJECT upgrade
    costing exactly 50% of that unit's BuildCost, with BuildTime 0.0
  * Adds the same rider/OCL re-arm to factory missiles A-J
  * Does not replace the launcher object, change visuals, weapons, or 9P117
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_TOP_MARKINGS/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_TOP_MARKINGS/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_MISSILE_HALF_PRICE_REARM"
SRC_DIR = ROOT / "patch/Data/INI"

BASE_DATA_SHA = "6af19c95f508a80752e26fd603d2745b5c2c51d446890a3f373816d329033f27"
BASE_DATA_SIZE = 366515208
BASE_ART_SHA = "95a0737f7f6e7d0f15a2a1234b222d1cf9643d1199b00e28e7e87e7c89083ed4"
BASE_ART_SIZE = 1294467676

UPG_KEY = r"Data\INI\Upgrade.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
OCL_KEY = r"Data\INI\ObjectCreationList.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
WEAPON_A_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlFahd500.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
STRIP_KEY = r"Data\INI\Object\Specter\Iraq Army\MissileHalfPriceRearm.ini"
UPG_NEW_KEY = r"Data\INI\Upgrade_MissileHalfPriceRearm.ini"

FACTORY = [
    {"object": "Iraq_AlFahd500", "weapon": "Weapon_Iraq_AlFahd500", "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"},
    {"object": "Iraq_AlHusseinII", "weapon": "Weapon_Iraq_AlHusseinII", "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHusseinII.ini"},
    {"object": "Iraq_AlSamoudII", "weapon": "Weapon_Iraq_AlSamoudII", "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlSamoudII.ini"},
    {"object": "Iraq_AlAbbas", "weapon": "Weapon_Iraq_AlAbbas", "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini"},
    {"object": "Iraq_AlBasrah", "weapon": "Weapon_Iraq_AlBasrah", "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlBasrah.ini"},
    {"object": "Iraq_AlNasir", "weapon": "Weapon_Iraq_AlNasir", "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNasir.ini"},
    {"object": "Iraq_AlMansour", "weapon": "Weapon_Iraq_AlMansour", "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlMansour.ini"},
]

SKIP_NAME = (
    "Removal",
    "Remover",
    "WarheadUpgrade",
    "Preparation",
)

FROZEN_DATA = [
    R11_KEY,
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_R11ScudB.ini",
]


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


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def decode(blob: bytes) -> str:
    return blob.decode("latin1").replace("\r\n", "\n")


def half_cost(cost: int) -> int:
    return (cost + 1) // 2


def ids_for(obj: str) -> dict[str, str]:
    return {
        "upgrade": f"Upgrade_Rearm_{obj}",
        "button": f"Command_Rearm_{obj}",
        "unarmed": f"{obj}_UnarmedRearmSet",
        "ocl": f"OCL_Rearm_{obj}",
        "strip": f"RearmStrip_{obj}",
    }


def object_blocks(text: str) -> list[tuple[str, int, int]]:
    found = []
    for m in re.finditer(r"^Object\s+(\S+)\s*$", text, re.M):
        found.append((m.group(1), m.start(), m.end()))
    spans = []
    for i, (name, start, _) in enumerate(found):
        end = found[i + 1][1] if i + 1 < len(found) else len(text)
        spans.append((name, start, end))
    return spans


def object_body(text: str, name: str) -> str | None:
    for n, start, end in object_blocks(text):
        if n == name:
            return text[start:end]
    return None


def field(body: str | None, key: str) -> str:
    if not body:
        return ""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", body, re.M)
    return m.group(1).strip() if m else ""


def command_block(text: str, kind: str, name: str) -> str | None:
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text))
    return matches[-1].group(0) if matches else None


def discover_existing(data: dict[str, bytes]) -> list[dict]:
    found: dict[str, dict] = {}
    for key, blob in data.items():
        if not key.lower().endswith(".ini"):
            continue
        text = decode(blob)
        for name, start, end in object_blocks(text):
            if any(s in name for s in SKIP_NAME):
                continue
            body = text[start:end]
            if "Upgrade_AlhussaienWarheadRearm" not in body:
                continue
            kind = field(body, "KindOf")
            if "PROJECTILE" in kind:
                continue
            cost_s = field(body, "BuildCost")
            if not cost_s:
                continue
            try:
                cost = int(float(cost_s))
            except ValueError:
                continue
            found[name] = {
                "object": name,
                "cost": cost,
                "file": key,
                "factory": False,
                "weapon": None,
            }
    return [found[k] for k in sorted(found)]


def patch_existing_object(text: str, spec: dict) -> str:
    ids = ids_for(spec["object"])
    body = object_body(text, spec["object"])
    if not body:
        return text

    new = body
    new = re.sub(
        r"(TriggeredBy\s*=\s*)Upgrade_AlhussaienWarheadRearm",
        rf"\g<1>{ids['upgrade']}",
        new,
    )
    new = re.sub(
        r"(UpgradeObject\s*=\s*)OCL_HussienWareheadRearm",
        rf"\g<1>{ids['ocl']}",
        new,
    )
    # Rider1 ... <CommandSet> SET_NORMAL
    new = re.sub(
        r"(Rider1\s*=\s*\S+\s+RIDER1\s+WEAPON_RIDER1\s+STATUS_RIDER1\s+)\S+(\s+SET_NORMAL)",
        rf"\g<1>{ids['unarmed']}\2",
        new,
    )
    if new == body:
        if "Upgrade_AlhussaienWarheadRearm" in body:
            raise SystemExit(f"existing object patch produced no change: {spec['object']}")
        return text
    return text.replace(body, new, 1)


def patch_factory_object(text: str, spec: dict) -> str:
    ids = ids_for(spec["object"])
    body = object_body(text, spec["object"])
    if not body:
        return text
    weapon = spec["weapon"]
    new = body
    new = re.sub(
        r"  WeaponSet\n"
        r"    Conditions = None\n"
        r"    Weapon = PRIMARY\s+" + re.escape(weapon) + r"\n"
        r"  End\n",
        "  WeaponSet\n"
        "    Conditions = WEAPON_RIDER1\n"
        "    Weapon = PRIMARY   NONE\n"
        "    AutoChooseSources = PRIMARY  NONE\n"
        "  End\n"
        "  WeaponSet\n"
        "    Conditions = WEAPON_RIDER2\n"
        f"    Weapon = PRIMARY   {weapon}\n"
        "  End\n",
        new,
        count=1,
    )
    if "WEAPON_RIDER2" not in new:
        raise SystemExit(f"factory weaponset patch failed: {spec['object']}")
    insert = (
        "  Behavior = RiderChangeContain ModuleTag_WarheadRider\n"
        f"    Rider1 = GenericFakeRider1_Default_Rank RIDER1 WEAPON_RIDER1 STATUS_RIDER1 {ids['unarmed']} SET_NORMAL\n"
        "    Rider2 = GenericFakeRider2_Default_Rank RIDER2 WEAPON_RIDER2 STATUS_RIDER2 Scud_B_CommandSet SET_NORMAL\n"
        "    Slots                 = 1\n"
        "    InitialPayload        = GenericFakeRider2_Default_Rank 1\n"
        "    DamagePercentToUnits  = 100%\n"
        "    BurnedDeathToUnits    = No\n"
        "    AllowInsideKindOf     = PRELOAD\n"
        "    ScuttleDelay          = 1\n"
        "    ScuttleStatus         = TOPPLED\n"
        "  End\n"
        "  Behavior = ObjectCreationUpgrade ModuleTag_Rearm\n"
        f"    TriggeredBy    = {ids['upgrade']}\n"
        f"    UpgradeObject  = {ids['ocl']}\n"
        "  End\n"
    )
    if "ModuleTag_WarheadRider" in new:
        raise SystemExit(f"factory already has rider: {spec['object']}")
    if "Behavior = ProductionUpdate" in new:
        new = new.replace("  Behavior = ProductionUpdate", insert + "  Behavior = ProductionUpdate", 1)
    else:
        new = new.replace("  Geometry = BOX", insert + "  Geometry = BOX", 1)
    return text.replace(body, new, 1)


def patch_weapon_block(text: str, weapon: str) -> str:
    block = command_block(text, "Weapon", weapon)
    if not block:
        return text
    new = block
    if "FireOCL" not in new:
        if "FireFX" in new:
            new = re.sub(
                r"(^\s*FireFX\s*=\s*\S+\s*$)",
                r"\1\n  FireOCL                     = OCL_HussienMissileDisarm",
                new,
                count=1,
                flags=re.M,
            )
        else:
            new = re.sub(
                r"(^\s*ProjectileObject\s*=\s*\S+\s*$)",
                r"\1\n  FireOCL                     = OCL_HussienMissileDisarm",
                new,
                count=1,
                flags=re.M,
            )
    if re.search(r"^\s*AutoReloadsClip\s*=", new, re.M):
        new = re.sub(r"^(\s*AutoReloadsClip\s*=\s*)\S+", r"\g<1>No", new, count=1, flags=re.M)
    else:
        new = re.sub(
            r"(^\s*ClipSize\s*=\s*\S+\s*$)",
            r"\1\n  AutoReloadsClip             = No",
            new,
            count=1,
            flags=re.M,
        )
    if "OCL_HussienMissileDisarm" not in new:
        raise SystemExit(f"FireOCL insert failed: {weapon}")
    if "WeaponSpeed" in block:
        old_s = field(block, "WeaponSpeed")
        new_s = field(new, "WeaponSpeed")
        if old_s != new_s:
            raise SystemExit(f"WeaponSpeed mutated {weapon}")
    return text.replace(block, new, 1)


def make_upgrade_file(specs: list[dict]) -> str:
    chunks = [
        "; Per-object half-price immediate re-arm. Type=OBJECT so each TEL pays itself.\n"
        "; BuildTime 0.0 = immediate after successful payment.\n"
    ]
    for spec in specs:
        ids = ids_for(spec["object"])
        chunks.append(
            f"\nUpgrade {ids['upgrade']}\n"
            f"  DisplayName      = UPGRADE:hussienwarhead\n"
            f"  Type             = OBJECT\n"
            f"  BuildTime        = 0.0\n"
            f"  BuildCost        = {spec['rearm']}\n"
            f"  ButtonImage      = SNNukeLaunch\n"
            f"  ResearchSound    = SUSuicideAttk\n"
            f"End\n"
        )
    return "".join(chunks)


def make_buttons(specs: list[dict]) -> str:
    chunks = ["\n"]
    for spec in specs:
        ids = ids_for(spec["object"])
        chunks.append(
            f"CommandButton {ids['button']}\n"
            f"  Command                 = OBJECT_UPGRADE\n"
            f"  UnitSpecificSound       = MoneyWithdraw\n"
            f"  Upgrade                 = {ids['upgrade']}\n"
            f"  TextLabel               = CONTROLBAR:icbmrearm\n"
            f"  Options                 = OK_FOR_MULTI_SELECT NOT_QUEUEABLE\n"
            f"  ButtonImage             = SNNukeLaunch\n"
            f"  ButtonBorderType        = UPGRADE\n"
            f"  DescriptLabel           = CONTROLBAR:ToolTipicbmrearm\n"
            f"  PurchasedLabel          = CONTROLBAR:ToolTipicbmrearm\n"
            f"End\n\n"
        )
    return "".join(chunks)


def make_commandsets(specs: list[dict]) -> str:
    chunks = ["\n"]
    for spec in specs:
        ids = ids_for(spec["object"])
        if spec.get("factory"):
            chunks.append(
                f"CommandSet {ids['unarmed']}\n"
                f"  1 = {ids['button']}\n"
                f"  12 = Command_AttackMove\n"
                f"  13 = Command_Guard\n"
                f"  14 = Command_Stop\n"
                f"End\n\n"
            )
        else:
            chunks.append(
                f"CommandSet {ids['unarmed']}\n"
                f"  1 = Command_TacticalStrike\n"
                f"  5 = {ids['button']}\n"
                f"  12 = Command_IraqDeployUnitWeapon\n"
                f"  16 = Command_AttackMove\n"
                f"  17 = Command_Guard\n"
                f"  14 = Command_Stop\n"
                f"End\n\n"
            )
    return "".join(chunks)


def make_ocls(specs: list[dict]) -> str:
    chunks = ["\n"]
    for spec in specs:
        ids = ids_for(spec["object"])
        chunks.append(
            f"ObjectCreationList {ids['ocl']}\n"
            f"  CreateObject\n"
            f"    ObjectNames       = {ids['strip']}\n"
            f"    Count             = 1\n"
            f"    ContainInsideSourceObject = Yes\n"
            f"  End\n"
            f"  CreateObject\n"
            f"    ObjectNames       = GenericFakeRider2_Default_Rank\n"
            f"    Count             = 1\n"
            f"    ContainInsideSourceObject = Yes\n"
            f"  End\n"
            f"End\n\n"
        )
    return "".join(chunks)


def make_strip_objects(specs: list[dict]) -> str:
    chunks = ["; Upgrade strippers for half-price immediate re-arm. Lifetime 100ms.\n"]
    for spec in specs:
        ids = ids_for(spec["object"])
        chunks.append(
            f"\nObject {ids['strip']}\n"
            f"  Side                = GLA\n"
            f"  EditorSorting       = SYSTEM\n"
            f"  TransportSlotCount  = 0\n"
            f"  ArmorSet\n"
            f"    Conditions        = None\n"
            f"    Armor             = InvulnerableAllArmor\n"
            f"    DamageFX          = EmptyDamageFX\n"
            f"  End\n"
            f"  KindOf = PRELOAD CAN_CAST_REFLECTIONS\n"
            f"  Body = ActiveBody ModuleTag_03\n"
            f"    MaxHealth       = 100.0\n"
            f"    InitialHealth   = 100.0\n"
            f"  End\n"
            f"  Behavior = AIUpdateInterface ModuleTag_04\n"
            f"  End\n"
            f"  Locomotor = SET_NORMAL RemovingLocomotor\n"
            f"  Behavior = PhysicsBehavior ModuleTag_05\n"
            f"    Mass = 50.0\n"
            f"    KillWhenRestingOnGround = Yes\n"
            f"    AllowBouncing = No\n"
            f"  End\n"
            f"  Behavior = SlavedUpdate ModuleTag_07\n"
            f"    StayOnSameLayerAsMaster = Yes\n"
            f"  End\n"
            f"  Behavior = DestroyDie ModuleTag_08\n"
            f"    DeathTypes = ALL\n"
            f"  End\n"
            f"  Behavior = UpgradeDie  ModuleTag_12\n"
            f"    DeathTypes = ALL\n"
            f"    UpgradeToRemove     = {ids['upgrade']} ModuleTag_MissileRearm02\n"
            f"  End\n"
            f"  Behavior = LifetimeUpdate ModuleTag_032\n"
            f"    MinLifetime = 100\n"
            f"    MaxLifetime = 100\n"
            f"  End\n"
            f"  Geometry = CYLINDER\n"
            f"  GeometryMajorRadius = 5.0\n"
            f"  GeometryMinorRadius = 5.0\n"
            f"  GeometryHeight = 5.0\n"
            f"  GeometryIsSmall = Yes\n"
            f"End\n"
        )
    return "".join(chunks)


def patch_shared_upgrade(text: str) -> str:
    block = command_block(text, "Upgrade", "Upgrade_AlhussaienWarheadRearm")
    if not block:
        raise SystemExit("Upgrade_AlhussaienWarheadRearm missing")
    new = re.sub(r"^(\s*BuildTime\s*=\s*)\S+", r"\g<1>0.0", block, count=1, flags=re.M)
    return text.replace(block, new, 1)


def validate(data: dict[str, bytes], src: dict[str, bytes], specs: list[dict]) -> list[str]:
    fails = []
    upg = decode(data[UPG_NEW_KEY])
    cs = decode(data[CS_KEY])
    cb = decode(data[CB_KEY])
    ocl = decode(data[OCL_KEY])
    strips = decode(data[STRIP_KEY])
    weapons = decode(data[WEAPON_KEY])
    shared = command_block(decode(data[UPG_KEY]), "Upgrade", "Upgrade_AlhussaienWarheadRearm")
    if field(shared, "BuildTime") != "0.0":
        fails.append("shared rearm BuildTime not 0.0")
    if field(shared, "BuildCost") != "2000":
        fails.append("shared rearm BuildCost mutated")

    r11 = decode(data[R11_KEY])
    if r11 != decode(src[R11_KEY]):
        fails.append("9P117 object mutated")

    for spec in specs:
        ids = ids_for(spec["object"])
        u = command_block(upg, "Upgrade", ids["upgrade"])
        if not u:
            fails.append(f"missing upgrade {ids['upgrade']}")
            continue
        if field(u, "BuildCost") != str(spec["rearm"]):
            fails.append(f"{spec['object']} rearm cost {field(u,'BuildCost')} != {spec['rearm']}")
        if field(u, "BuildTime") != "0.0":
            fails.append(f"{spec['object']} rearm time {field(u,'BuildTime')}")
        if field(u, "Type") != "OBJECT":
            fails.append(f"{spec['object']} upgrade not OBJECT")
        if not command_block(cb, "CommandButton", ids["button"]):
            fails.append(f"missing button {ids['button']}")
        setb = command_block(cs, "CommandSet", ids["unarmed"])
        if not setb or ids["button"] not in setb:
            fails.append(f"unarmed set missing button {spec['object']}")
        if not command_block(ocl, "ObjectCreationList", ids["ocl"]):
            fails.append(f"missing OCL {ids['ocl']}")
        if f"Object {ids['strip']}" not in strips:
            fails.append(f"missing strip {ids['strip']}")
        body = object_body(decode(data[spec["file"]]), spec["object"])
        if not body:
            fails.append(f"object missing after patch {spec['object']}")
            continue
        if field(body, "BuildCost") != str(spec["cost"]):
            fails.append(f"{spec['object']} BuildCost changed")
        if ids["upgrade"] not in body:
            fails.append(f"{spec['object']} TriggeredBy not unique upgrade")
        if "Upgrade_AlhussaienWarheadRearm" in body and "TriggeredBy" in body:
            # factory never had it; existing must be fully retargeted
            if not spec.get("factory"):
                fails.append(f"{spec['object']} still references shared upgrade")
        if spec.get("factory"):
            if "InitialPayload        = GenericFakeRider2_Default_Rank 1" not in body:
                fails.append(f"{spec['object']} not starting armed")
            if ids["unarmed"] not in body:
                fails.append(f"{spec['object']} rider1 set missing")
            wblock = command_block(weapons, "Weapon", spec["weapon"])
            if spec["object"] == "Iraq_AlFahd500":
                wblock = command_block(decode(data[WEAPON_A_KEY]), "Weapon", spec["weapon"]) or wblock
            if not wblock or "OCL_HussienMissileDisarm" not in wblock:
                fails.append(f"{spec['weapon']} missing FireOCL")
            if field(wblock, "AutoReloadsClip") != "No":
                fails.append(f"{spec['weapon']} AutoReloadsClip {field(wblock,'AutoReloadsClip')}")
            orig_key = WEAPON_A_KEY if spec["object"] == "Iraq_AlFahd500" and WEAPON_A_KEY in src else WEAPON_KEY
            orig = command_block(decode(src[orig_key]), "Weapon", spec["weapon"])
            if orig is None:
                orig = command_block(decode(src[WEAPON_KEY]), "Weapon", spec["weapon"])
            for k in ("WeaponSpeed", "PrimaryDamage", "AttackRange"):
                if field(wblock, k) != field(orig, k):
                    fails.append(f"{spec['weapon']} {k} changed")
    return fails


def main() -> int:
    if sha256_path(SRC_DATA) != BASE_DATA_SHA or SRC_DATA.stat().st_size != BASE_DATA_SIZE:
        raise SystemExit("PR #593 DATA baseline mismatch")
    if sha256_path(SRC_ART) != BASE_ART_SHA or SRC_ART.stat().st_size != BASE_ART_SIZE:
        raise SystemExit("PR #593 ART baseline mismatch")

    src_data = parse_big(SRC_DATA.read_bytes())
    data = dict(src_data)

    existing = discover_existing(data)
    specs: list[dict] = []
    for spec in existing:
        spec = dict(spec)
        spec["rearm"] = half_cost(spec["cost"])
        specs.append(spec)
    for f in FACTORY:
        text = decode(data[f["ini"]])
        body = object_body(text, f["object"])
        cost = int(float(field(body, "BuildCost")))
        specs.append(
            {
                "object": f["object"],
                "cost": cost,
                "rearm": half_cost(cost),
                "file": f["ini"],
                "factory": True,
                "weapon": f["weapon"],
            }
        )

    # Patch existing Alhussaien-pattern objects in every file that defines them.
    for spec in specs:
        if spec.get("factory"):
            continue
        for key, blob in list(data.items()):
            if not key.lower().endswith(".ini"):
                continue
            text = decode(blob)
            if re.search(rf"^Object {re.escape(spec['object'])}\s*$", text, re.M):
                data[key] = to_crlf(patch_existing_object(text, spec))

    for spec in specs:
        if not spec.get("factory"):
            continue
        text = decode(data[spec["file"]])
        data[spec["file"]] = to_crlf(patch_factory_object(text, spec))
        # Keep workspace source INI in sync.
        src_path = SRC_DIR / spec["file"].split("Data\\INI\\", 1)[-1].replace("\\", "/")
        # files live under patch/Data/INI/... mapped from Data\INI\...
        mapped = ROOT / "patch" / spec["file"].replace("\\", "/")
        if mapped.exists():
            mapped.write_bytes(data[spec["file"]])

    data[WEAPON_KEY] = to_crlf(decode(data[WEAPON_KEY]))
    wtext = decode(data[WEAPON_KEY])
    for spec in specs:
        if spec.get("weapon"):
            wtext = patch_weapon_block(wtext, spec["weapon"])
    data[WEAPON_KEY] = to_crlf(wtext)
    if WEAPON_A_KEY in data:
        data[WEAPON_A_KEY] = to_crlf(patch_weapon_block(decode(data[WEAPON_A_KEY]), "Weapon_Iraq_AlFahd500"))
        src_a = ROOT / "patch/Data/INI/Weapon/Weapon_Iraq_AlFahd500.ini"
        if src_a.exists():
            src_a.write_bytes(data[WEAPON_A_KEY])

    data[UPG_KEY] = to_crlf(patch_shared_upgrade(decode(data[UPG_KEY])))
    data[UPG_NEW_KEY] = to_crlf(make_upgrade_file(specs))
    data[CB_KEY] = data[CB_KEY] + to_crlf(make_buttons(specs))
    data[CS_KEY] = data[CS_KEY] + to_crlf(make_commandsets(specs))
    data[OCL_KEY] = data[OCL_KEY] + to_crlf(make_ocls(specs))
    data[STRIP_KEY] = to_crlf(make_strip_objects(specs))

    # Write reviewable overlay sources.
    (SRC_DIR / "Upgrade_MissileHalfPriceRearm.ini").write_bytes(data[UPG_NEW_KEY])
    strip_src = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/MissileHalfPriceRearm.ini"
    strip_src.parent.mkdir(parents=True, exist_ok=True)
    strip_src.write_bytes(data[STRIP_KEY])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    packed_data = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed_data)
    shutil.copy2(SRC_ART, OUT / "_SPEC_ART_ONE.big")
    extracted = parse_big(out_data.read_bytes())

    fails = validate(extracted, src_data, specs)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed_data))
    if sha256_path(OUT / "_SPEC_ART_ONE.big") != BASE_ART_SHA:
        fails.append("ART copy not byte-identical")

    changed = sorted(k for k in extracted if src_data.get(k) != extracted.get(k))
    inventory_lines = [
        f"- {s['object']}: build ${s['cost']} -> re-arm ${s['rearm']}"
        + (" [factory A-J]" if s.get("factory") else " [Alabaas-pattern]")
        for s in specs
    ]
    data_sha = sha256_path(out_data)
    art_sha = BASE_ART_SHA
    report = [
        "# SPECTER half-price immediate missile re-arm",
        "",
        "Baseline: PR #593 missile top-surface markings (DATA+ART).",
        "ART is a byte-identical copy. DATA adds per-object half-price re-arm.",
        "",
        "Reference: Iraq_Alhussaien OBJECT_UPGRADE + ObjectCreationUpgrade + OCL rider restore.",
        "Each launcher now has its own OBJECT upgrade at 50% of its BuildCost, BuildTime 0.0.",
        "Factory missiles A-J gain the same rider re-arm (start armed; after fire, pay to restore).",
        "Iraq_R11ScudB / 9P117, weapons damage/speed/range, and all ART are unchanged.",
        "",
        "## Inventory",
        *inventory_lines,
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART size: {BASE_ART_SIZE}",
        f"- ART SHA256: {art_sha}",
        f"- Changed DATA: {', '.join(changed)}",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        report.append("RUNTIME_TEST=NOT RUN")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static / packed last-wins)",
        "- Each listed launcher re-arm cost is exactly ceil(BuildCost/2)",
        "- Each re-arm upgrade BuildTime is 0.0 (immediate after payment)",
        "- Unique OBJECT upgrades; shared Upgrade_AlhussaienWarheadRearm time set to 0.0 fallback only",
        "- Factory A-J start with Rider2 (first shot unchanged) and FireOCL disarm",
        "- 9P117 / Iraq_R11ScudB, weapon damage/speed/range, ART unchanged",
        "",
        "Static validation completed; runtime game test not performed.",
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
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={BASE_ART_SIZE}\n"
        f"ART_SHA256={art_sha}\n"
        f"CHANGED_DATA={', '.join(changed)}\n"
        "REARM=half BuildCost, BuildTime 0.0, Alabaas OBJECT_UPGRADE/OCL rider\n"
        "BASELINE=PR #593\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: half-price immediate missile re-arm\n"
        "\n"
        "After a listed missile system fires, pay 50% of its build cost to\n"
        "restore firing immediately. The launcher is not replaced.\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "  _SPEC_ART_ONE.big  (unchanged from PR #593)\n"
        "\n"
        "Static validation completed; runtime game test not performed.\n",
        encoding="utf-8",
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inventory_lines) + "\n", encoding="utf-8")
    zip_path = ROOT / "patch/Release/SPECTER_MISSILE_HALF_PRICE_REARM.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "INVENTORY.txt", "INVENTORY.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
