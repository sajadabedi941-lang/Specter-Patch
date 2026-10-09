#!/usr/bin/env python3
"""Alabaas rider paid-rearm on Iraq_AlFahd500 only.

Spawn-crash split vs PRs #594-#597 (packed last-wins):

  #594  InitialPayload GenericFakeRider2 (GeometryHeight 10000000) into a
        9P117 TEL + Weapon = PRIMARY NONE + shared OCL_HussienMissileDisarm
        + AutoReloadsClip=No. Kept Scud_B_CommandSet. CTD at spawn.
  #595  same contain stack + GARRISONABLE. Still CTD. PRIMARY NONE and
        InitialPayload remained.
  #596  startup CTD: duplicate Iraq_AlAbbasCommandSet.
  #597  no riders; PLAYER_UPGRADE + TriggeredBy + leftover
        OCL_Rearm_Iraq_AlFahd500 (non-contained stripper only) + AutoNo.

Working Alabaas (Iraq_Alhussaien) does NOT use PRIMARY NONE. Unarmed
WEAPON_RIDER1 has no PRIMARY (SECONDARY NONE + TERTIARY dummy). Armed
WEAPON_RIDER2 has the missile. FireOCL OCL_HussienMissileDisarm contains
GenericFakeRider1. OBJECT_UPGRADE -> ObjectCreationUpgrade contains
RearmStrip + GenericFakeRider2. HussieanMissileWeapon has FireOCL and
does NOT set AutoReloadsClip=No.

This packer (missile A only, from PR #599):
  * Keep Conditions=None + Weapon_Iraq_AlFahd500 as the spawn/first-shot set
  * Do NOT use InitialPayload (factory spawn crash ingredient)
  * Do NOT use Weapon = PRIMARY NONE
  * Unique riders / OCLs (not GenericFakeRider, not OCL_HussienMissileDisarm)
  * Unique riders use small geometry (not 10e6 height)
  * RiderChangeContain + GARRISONABLE for post-fire contain
  * Unique CommandSet leftover already in #599 DATA (PR #602 lever)
  * FireOCL = OCL_Disarm_Iraq_AlFahd500 (contain unarmed rider)
  * Replace leftover OCL_Rearm_Iraq_AlFahd500 so payment actually restores
    the armed rider (never a $1100 no-op)
  * No AutoReloadsClip=No (Alabaas fire weapon does not use it)
  * Do not touch ModuleTag_09h56u56j, B-J, MOTHER, Alhussaien, ART
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MAGENTA_WAVES/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MAGENTA_WAVES/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD500_RIDER_REARM"

SHA_DATA_599 = "ec066f71382d3d1d732d4a9cdde54ffee86258eb0362aa0c8087155bc5e7f4d8"
SIZE_DATA_599 = 366615017
SHA_ART_599 = "9c1dc445c17b024f8a4c1c55e699371a94d4991d1dff1eb377f3976a6c54545e"
SIZE_ART_599 = 1295713019

OBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
RIDERS_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Riders.ini"
FAC_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
W_A_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlFahd500.ini"
ABBAS_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini"
OCL_KEY = r"Data\INI\ObjectCreationList.ini"
STRIP_KEY = r"Data\INI\Object\Specter\Iraq Army\MissileHalfPriceRearm.ini"
UPG_KEY = r"Data\INI\Upgrade_MissileHalfPriceRearm.ini"

OTHER_FACTORY = [
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHusseinII.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlSamoudII.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlBasrah.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNasir.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlMansour.ini",
]

NEW_SET = "Iraq_AlFahd500CommandSet"
OLD_SET = "Scud_B_CommandSet"
UNARMED_SET = "Iraq_AlFahd500_UnarmedRearmSet"
RIDER_U = "Iraq_AlFahd500_RiderUnarmed"
RIDER_A = "Iraq_AlFahd500_RiderArmed"
OCL_DISARM = "OCL_Disarm_Iraq_AlFahd500"
OCL_REARM = "OCL_Rearm_Iraq_AlFahd500"
STRIP = "RearmStrip_Iraq_AlFahd500"
UPG = "Upgrade_Rearm_Iraq_AlFahd500"
BTN = "Command_Rearm_Iraq_AlFahd500"
KIND_OLD = "PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE"
KIND_NEW = KIND_OLD + " GARRISONABLE_UNTIL_DESTROYED"

RIDER_FILE = """; Unique Al-Fahd500 contain riders. Not GenericFakeRider.
; Small geometry: #594/#595 InitialPayload used GenericFakeRider
; with enormous GeometryHeight, which CTDs if contain leaks at factory spawn.

Object Iraq_AlFahd500_RiderUnarmed
  Side               = Iraq
  EditorSorting      = SYSTEM
  TransportSlotCount = 1
  ArmorSet
    Conditions       = None
    Armor            = InvulnerableAllArmor
    DamageFX         = EmptyDamageFX
  End
  KindOf = PRELOAD CAN_CAST_REFLECTIONS NO_COLLIDE IMMOBILE
  Body = ActiveBody ModuleTag_02
    MaxHealth        = 10.0
    InitialHealth    = 10.0
  End
  Behavior = AIUpdateInterface ModuleTag_03
  End
  Behavior = DestroyDie ModuleTag_Die01
  End
  Geometry = CYLINDER
  GeometryMajorRadius = 5.0
  GeometryMinorRadius = 5.0
  GeometryHeight = 5.0
  GeometryIsSmall = Yes
End

Object Iraq_AlFahd500_RiderArmed
  Side               = Iraq
  EditorSorting      = SYSTEM
  TransportSlotCount = 1
  ArmorSet
    Conditions       = None
    Armor            = InvulnerableAllArmor
    DamageFX         = EmptyDamageFX
  End
  KindOf = PRELOAD CAN_CAST_REFLECTIONS NO_COLLIDE IMMOBILE
  Body = ActiveBody ModuleTag_02
    MaxHealth        = 10.0
    InitialHealth    = 10.0
  End
  Behavior = AIUpdateInterface ModuleTag_03
  End
  Behavior = DestroyDie ModuleTag_Die01
  End
  Geometry = CYLINDER
  GeometryMajorRadius = 5.0
  GeometryMinorRadius = 5.0
  GeometryHeight = 5.0
  GeometryIsSmall = Yes
End
"""

OCL_DISARM_BLOCK = """ObjectCreationList OCL_Disarm_Iraq_AlFahd500
  CreateObject
    ObjectNames       = Iraq_AlFahd500_RiderUnarmed
    Count             = 1
    ContainInsideSourceObject = Yes
  End
End
"""

OCL_REARM_BLOCK = """ObjectCreationList OCL_Rearm_Iraq_AlFahd500
  CreateObject
    ObjectNames       = RearmStrip_Iraq_AlFahd500
    Count             = 1
    ContainInsideSourceObject = Yes
  End
  CreateObject
    ObjectNames       = Iraq_AlFahd500_RiderArmed
    Count             = 1
    ContainInsideSourceObject = Yes
  End
End
"""

WEAPONSET_OLD = """  WeaponSet
    Conditions = None
    Weapon = PRIMARY   Weapon_Iraq_AlFahd500
  End
"""

WEAPONSET_NEW = """  WeaponSet
    Conditions = None
    Weapon = PRIMARY   Weapon_Iraq_AlFahd500
  End
  WeaponSet
    Conditions = WEAPON_RIDER1
    Weapon = SECONDARY  NONE
    AutoChooseSources = SECONDARY  NONE
  End
  WeaponSet
    Conditions = WEAPON_RIDER2
    Weapon = PRIMARY   Weapon_Iraq_AlFahd500
  End
"""

RIDER_BEHAVIORS = """  Behavior = RiderChangeContain ModuleTag_AlFahd500Rider
    Rider1 = Iraq_AlFahd500_RiderUnarmed RIDER1 WEAPON_RIDER1 STATUS_RIDER1 Iraq_AlFahd500_UnarmedRearmSet SET_NORMAL
    Rider2 = Iraq_AlFahd500_RiderArmed RIDER2 WEAPON_RIDER2 STATUS_RIDER2 Iraq_AlFahd500CommandSet SET_NORMAL
    Slots                 = 1
    DamagePercentToUnits  = 100%
    BurnedDeathToUnits    = No
    AllowInsideKindOf     = PRELOAD
    ScuttleDelay          = 1
    ScuttleStatus         = TOPPLED
  End
  Behavior = ObjectCreationUpgrade ModuleTag_AlFahd500Rearm
    TriggeredBy    = Upgrade_Rearm_Iraq_AlFahd500
    UpgradeObject  = OCL_Rearm_Iraq_AlFahd500
  End
"""


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
        raise SystemExit("not BIGF")
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


def decode(blob: bytes) -> str:
    return blob.decode("latin1").replace("\r\n", "\n")


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def object_body(text: str, name: str) -> str | None:
    found = [(m.group(1), m.start()) for m in re.finditer(r"^Object\s+(\S+)\s*$", text, re.M)]
    for i, (n, start) in enumerate(found):
        if n == name:
            end = found[i + 1][1] if i + 1 < len(found) else len(text)
            return text[start:end]
    return None


def field(body: str | None, key: str) -> str:
    if not body:
        return ""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", body, re.M)
    return m.group(1).strip() if m else ""


def last_block(kind: str, name: str, text: str) -> str | None:
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text))
    return matches[-1].group(0) if matches else None


def replace_last_block(kind: str, name: str, text: str, new_block: str) -> str:
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text))
    if not matches:
        return text.rstrip() + "\n\n" + new_block.strip() + "\n"
    m = matches[-1]
    return text[: m.start()] + new_block.strip() + text[m.end() :]


def patch_object(text: str) -> str:
    body = object_body(text, "Iraq_AlFahd500")
    if not body:
        raise SystemExit("Iraq_AlFahd500 missing")
    if field(body, "CommandSet") != OLD_SET:
        raise SystemExit(f"expected {OLD_SET}, got {field(body, 'CommandSet')}")
    new = body
    new = re.sub(
        rf"^(\s*CommandSet\s*=\s*){re.escape(OLD_SET)}\s*$",
        rf"\1{NEW_SET}",
        new,
        count=1,
        flags=re.M,
    )
    if KIND_OLD not in new or KIND_NEW in new:
        raise SystemExit("KindOf patch failed")
    new = new.replace(KIND_OLD, KIND_NEW, 1)
    if WEAPONSET_OLD not in new:
        raise SystemExit("WeaponSet Conditions=None block not found")
    new = new.replace(WEAPONSET_OLD, WEAPONSET_NEW, 1)
    if "InitialPayload" in new:
        raise SystemExit("InitialPayload must not be introduced")
    if "PRIMARY   NONE" in new or "PRIMARY NONE" in new:
        raise SystemExit("PRIMARY NONE must not be introduced")
    if "Behavior = ProductionUpdate" not in new:
        raise SystemExit("ProductionUpdate missing")
    if "ModuleTag_AlFahd500Rider" in new:
        raise SystemExit("rider already present")
    new = new.replace("  Behavior = ProductionUpdate", RIDER_BEHAVIORS + "  Behavior = ProductionUpdate", 1)
    return text[: text.find(body)] + new + text[text.find(body) + len(body) :]


def patch_weapon(text: str) -> str:
    block = last_block("Weapon", "Weapon_Iraq_AlFahd500", text)
    if not block:
        raise SystemExit("Weapon_Iraq_AlFahd500 missing")
    if "FireOCL" in block:
        raise SystemExit("weapon already has FireOCL")
    if field(block, "PrimaryDamage") != "8000.0":
        raise SystemExit("damage baseline mutated before patch")
    if field(block, "AttackRange") != "1720.0":
        raise SystemExit("range baseline mutated before patch")
    if field(block, "WeaponSpeed") != "280":
        raise SystemExit("speed baseline mutated before patch")
    if field(block, "ClipReloadTime") != "95000":
        raise SystemExit("ClipReloadTime baseline mutated before patch")
    new = re.sub(
        r"(^\s*FireFX\s*=\s*\S+\s*$)",
        rf"\1\n  FireOCL                     = {OCL_DISARM}",
        block,
        count=1,
        flags=re.M,
    )
    if OCL_DISARM not in new:
        raise SystemExit("FireOCL insert failed")
    if "AutoReloadsClip" in new:
        raise SystemExit("do not add AutoReloadsClip")
    if "OCL_HussienMissileDisarm" in new:
        raise SystemExit("must not reuse Alabaas FireOCL")
    return text.replace(block, new, 1)


def patch_ocl(text: str) -> str:
    new = replace_last_block("ObjectCreationList", OCL_REARM, text, OCL_REARM_BLOCK)
    if last_block("ObjectCreationList", OCL_DISARM, new):
        new = replace_last_block("ObjectCreationList", OCL_DISARM, new, OCL_DISARM_BLOCK)
    else:
        new = new.rstrip() + "\n\n" + OCL_DISARM_BLOCK
    return new


def patch_strip(text: str) -> str:
    body = object_body(text, STRIP)
    if not body:
        raise SystemExit("RearmStrip_Iraq_AlFahd500 missing")
    new = body.replace("ModuleTag_09h56u56j", "ModuleTag_AlFahd500Rearm")
    if "ModuleTag_AlFahd500Rearm" not in new:
        raise SystemExit("stripper module retarget failed")
    if "Upgrade_Rearm_Iraq_AlFahd500" not in new:
        raise SystemExit("stripper upgrade name missing")
    return text[: text.find(body)] + new + text[text.find(body) + len(body) :]


def validate(data: dict[str, bytes], baseline: dict[str, bytes]) -> list[str]:
    fails = []
    changed = sorted(k for k in set(list(data) + list(baseline)) if baseline.get(k) != data.get(k))
    allowed = {OBJ_KEY, W_A_KEY, OCL_KEY, STRIP_KEY, RIDERS_KEY}
    extra = [k for k in changed if k not in allowed]
    if extra:
        fails.append(f"unexpected changed paths {extra}")
    missing_new = [k for k in allowed if k != RIDERS_KEY and k not in data]
    if missing_new:
        fails.append(f"missing {missing_new}")
    if RIDERS_KEY not in data:
        fails.append("unique rider file missing")
    body = object_body(decode(data[OBJ_KEY]), "Iraq_AlFahd500")
    if field(body, "CommandSet") != NEW_SET:
        fails.append(f"CommandSet {field(body, 'CommandSet')}")
    if field(body, "KindOf") != KIND_NEW:
        fails.append(f"KindOf {field(body, 'KindOf')}")
    if field(body, "BuildCost") != "2200":
        fails.append("BuildCost mutated")
    if "InitialPayload" in (body or ""):
        fails.append("InitialPayload present (spawn-crash ingredient)")
    if re.search(r"PRIMARY\s+NONE", body or ""):
        fails.append("PRIMARY NONE present (spawn-crash ingredient)")
    if "GenericFakeRider" in (body or ""):
        fails.append("reused GenericFakeRider")
    if "WEAPON_RIDER1" not in (body or "") or "WEAPON_RIDER2" not in (body or ""):
        fails.append("rider weapon sets missing")
    if "Conditions = None" not in (body or ""):
        fails.append("spawn Conditions=None missing")
    if "ModuleTag_AlFahd500Rider" not in (body or "") or "ModuleTag_AlFahd500Rearm" not in (body or ""):
        fails.append("rider/rearm modules missing")
    if "ModuleTag_09h56u56j" not in (body or ""):
        fails.append("stock WeaponSetUpgrade removed")
    if "PLAYER_UPGRADE" in (body or ""):
        fails.append("#597 PLAYER_UPGRADE present")
    w = last_block("Weapon", "Weapon_Iraq_AlFahd500", decode(data[W_A_KEY])) or ""
    if field(w, "FireOCL") != OCL_DISARM:
        fails.append(f"FireOCL {field(w, 'FireOCL')}")
    if field(w, "PrimaryDamage") != "8000.0" or field(w, "AttackRange") != "1720.0":
        fails.append("weapon combat stats mutated")
    if field(w, "WeaponSpeed") != "280" or field(w, "ClipReloadTime") != "95000":
        fails.append("weapon speed/reload mutated")
    if "AutoReloadsClip" in w:
        fails.append("AutoReloadsClip added")
    ocl = decode(data[OCL_KEY])
    disarm = last_block("ObjectCreationList", OCL_DISARM, ocl) or ""
    rearm = last_block("ObjectCreationList", OCL_REARM, ocl) or ""
    if RIDER_U not in disarm or "ContainInsideSourceObject = Yes" not in disarm:
        fails.append("disarm OCL missing contained unarmed rider")
    if RIDER_A not in rearm or STRIP not in rearm:
        fails.append("rearm OCL missing armed rider or stripper")
    if "ContainInsideSourceObject = Yes" not in rearm:
        fails.append("rearm OCL not contained (would charge without restore)")
    if "IgnorePrimaryObstacle" in rearm:
        fails.append("leftover #597 non-contained rearm OCL remains")
    riders = decode(data[RIDERS_KEY])
    if not object_body(riders, RIDER_U) or not object_body(riders, RIDER_A):
        fails.append("unique rider objects missing")
    if re.search(r"GeometryHeight\s*=\s*10000000", riders):
        fails.append("huge rider geometry")
    strip = object_body(decode(data[STRIP_KEY]), STRIP) or ""
    if "ModuleTag_AlFahd500Rearm" not in strip:
        fails.append("stripper still points at ModuleTag_09h56u56j")
    upg = last_block("Upgrade", UPG, decode(data[UPG_KEY])) or ""
    if field(upg, "BuildCost") != "1100" or field(upg, "Type") != "OBJECT":
        fails.append(f"upgrade {field(upg, 'Type')} {field(upg, 'BuildCost')}")
    cs = decode(data[CS_KEY])
    cb = decode(data[CB_KEY])
    if data[CS_KEY] != baseline[CS_KEY]:
        fails.append("CommandSet.ini mutated")
    telset = last_block("CommandSet", NEW_SET, cs) or ""
    unarmed = last_block("CommandSet", UNARMED_SET, cs) or ""
    if BTN not in telset or "Command_FireMainWeapon" not in telset:
        fails.append("armed command set incomplete")
    if BTN not in unarmed or "Command_FireMainWeapon" in unarmed:
        fails.append("unarmed command set incomplete")
    btn = last_block("CommandButton", BTN, cb) or ""
    if "OBJECT_UPGRADE" not in btn or UPG not in btn:
        fails.append("rearm button not OBJECT_UPGRADE")
    btn_a = last_block("CommandButton", "CB_MISSILE_A", cb) or ""
    if "Iraq_AlFahd500" not in btn_a:
        fails.append("CB_MISSILE_A no longer builds Iraq_AlFahd500")
    fac = object_body(decode(data[FAC_KEY]), "Iraq_AlFahdMissileFactory")
    if field(fac, "CommandSet") != "Iraq_AlFahdMissileFactoryCommandSet":
        fails.append("factory CommandSet mutated")
    r11 = object_body(decode(data[R11_KEY]), "Iraq_R11ScudB")
    if field(r11, "CommandSet") != OLD_SET:
        fails.append("MOTHER CommandSet mutated")
    if data[R11_KEY] != baseline[R11_KEY]:
        fails.append("9P117 file mutated")
    if data[ABBAS_KEY] != baseline[ABBAS_KEY]:
        fails.append("Iraq_Alhussaien file mutated")
    for key in OTHER_FACTORY:
        if data[key] != baseline[key]:
            fails.append(f"factory sibling mutated: {key}")
    lows: dict[str, list[str]] = {}
    for m in re.finditer(r"^CommandSet (\S+)", cs, re.M):
        lows.setdefault(m.group(1).lower(), []).append(m.group(1))
    for names in lows.values():
        if len(names) > 1:
            fails.append(f"duplicate CommandSet {names}")
    return fails


def write_source(data: dict[str, bytes]) -> None:
    mapped = {
        OBJ_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlFahd500.ini",
        W_A_KEY: ROOT / "patch/Data/INI/Weapon/Weapon_Iraq_AlFahd500.ini",
        RIDERS_KEY: ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Iraq_AlFahd500_Riders.ini",
    }
    for key, path in mapped.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data[key])


def main() -> int:
    if sha256_path(SRC_DATA) != SHA_DATA_599 or SRC_DATA.stat().st_size != SIZE_DATA_599:
        raise SystemExit("PR #599 DATA mismatch")
    if sha256_path(SRC_ART) != SHA_ART_599 or SRC_ART.stat().st_size != SIZE_ART_599:
        raise SystemExit("PR #599 ART mismatch")

    baseline = parse_big(SRC_DATA.read_bytes())
    data = dict(baseline)
    data[OBJ_KEY] = to_crlf(patch_object(decode(data[OBJ_KEY])))
    data[W_A_KEY] = to_crlf(patch_weapon(decode(data[W_A_KEY])))
    data[OCL_KEY] = to_crlf(patch_ocl(decode(data[OCL_KEY])))
    data[STRIP_KEY] = to_crlf(patch_strip(decode(data[STRIP_KEY])))
    data[RIDERS_KEY] = to_crlf(RIDER_FILE)
    write_source(data)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    shutil.copy2(SRC_ART, OUT / "_SPEC_ART_ONE.big")
    extracted = parse_big(out_data.read_bytes())
    fails = validate(extracted, baseline)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    if sha256_path(OUT / "_SPEC_ART_ONE.big") != SHA_ART_599:
        fails.append("ART copy not byte-identical to PR #599")

    data_sha = sha256_path(out_data)
    changed = sorted(k for k in set(list(extracted) + list(baseline)) if baseline.get(k) != extracted.get(k))
    report = [
        "# SPECTER Iraq_AlFahd500 Alabaas-style unique rider rearm",
        "",
        "Missile A only. First shot uses spawn-safe Conditions=None (no InitialPayload).",
        "FireOCL contains unique unarmed rider. $1100 OBJECT_UPGRADE contains unique",
        "armed rider + stripper. Not a CommandSet-only / payment-only patch.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART size: {SIZE_ART_599}",
        f"- ART SHA256: {SHA_ART_599}",
        f"- Changed vs PR #599: {', '.join(changed)}",
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
        "- Unique riders/OCLs; leftover OCL_Rearm_Iraq_AlFahd500 now contains armed rider",
        "- No InitialPayload, no PRIMARY NONE, no GenericFakeRider, no Alabaas FireOCL ID",
        "- Conditions=None kept; GARRISONABLE + RiderChangeContain for post-fire contain",
        "- CB_MISSILE_A still builds Iraq_AlFahd500; Scud_B / B-J / MOTHER / Alhussaien unchanged",
        "- ART byte-identical to PR #599",
        "",
        "Static validation completed; runtime game test not performed.",
        "Spawn CTD is NOT claimed fixed. Do not proceed to missile B.",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=NO\n"
        "LEVER=Alabaas rider machine on Iraq_AlFahd500 (no InitialPayload, unique IDs)\n"
        "PAID_REARM_LOOP_COMPLETE=STATIC_ONLY\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted)}\n"
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={SIZE_ART_599}\n"
        f"ART_SHA256={SHA_ART_599}\n"
        "ART_BYTE_IDENTICAL_TO_PR599=YES\n"
        f"CHANGED_VS_599={', '.join(changed)}\n"
        "BASELINE=PR #599\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n"
        "SPAWN_CTD_CLAIMED_FIXED=NO\n"
        "REARM_COST=1100\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Iraq_AlFahd500 unique-ID Alabaas rider rearm\n"
        "\n"
        "After missile A fires, pay $1100 to restore the armed rider.\n"
        "No InitialPayload / PRIMARY NONE. ART unchanged from PR #599.\n"
        "Place both BIGs in the SPECTER folder. Runtime spawn test not performed.\n",
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "\n".join(
            [
                "# Iraq_AlFahd500 unique Alabaas rider rearm",
                "",
                "From PR #599. Missile A only. Incorporates the leftover unique CommandSet",
                "(`Iraq_AlFahd500CommandSet`) because the rearm button must live on this TEL",
                "without editing `Scud_B_CommandSet`.",
                "",
                "## Rider chain",
                "",
                "1. Spawn: `Conditions=None` + `Weapon_Iraq_AlFahd500`. No `InitialPayload`.",
                "2. Fire: `FireOCL = OCL_Disarm_Iraq_AlFahd500` contains `Iraq_AlFahd500_RiderUnarmed`",
                "   -> `WEAPON_RIDER1` (no PRIMARY) + `Iraq_AlFahd500_UnarmedRearmSet`.",
                "3. Pay: `Command_Rearm_Iraq_AlFahd500` OBJECT_UPGRADE `Upgrade_Rearm_Iraq_AlFahd500` $1100.",
                "4. Restore: `ObjectCreationUpgrade` -> `OCL_Rearm_Iraq_AlFahd500` contains",
                "   `RearmStrip_Iraq_AlFahd500` + `Iraq_AlFahd500_RiderArmed` -> `WEAPON_RIDER2`.",
                "5. Stripper `UpgradeDie` clears the object upgrade so the next cycle can pay again.",
                "",
                "## Spawn-crash fix vs #594/#595",
                "",
                "- #594/#595 used `InitialPayload GenericFakeRider2` (height 1e7) and",
                "  `Weapon = PRIMARY NONE`. Alabaas unarmed sets have **no PRIMARY**.",
                "- This build omits `InitialPayload`, keeps `Conditions=None` for the first shot,",
                "  uses unique small-geometry riders, and unique OCLs.",
                "- Leftover `#597` `OCL_Rearm_Iraq_AlFahd500` only spawned a non-contained stripper;",
                "  it is replaced so $1100 actually restores the armed rider.",
                "",
                "Static checks are not runtime safety. Game session was not completed in this environment.",
                "Do not proceed to missile B.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD500_RIDER_REARM.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
        zf.write(OUT / "RELEASE_NOTES.md", "RELEASE_NOTES.md")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
