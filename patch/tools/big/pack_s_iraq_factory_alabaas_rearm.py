#!/usr/bin/env python3
"""Reuse the Alabaas OBJECT_UPGRADE payment on spawn-safe factory TELs.

Packed last-wins investigation (PR #593 Alabaas vs factory A-J):

Alabaas (Iraq_Alhussaien) proven chain:
  spawn  InitialPayload GenericFakeRider2 -> WEAPON_RIDER2 armed
  fire   HussieanMissileWeapon FireOCL=OCL_HussienMissileDisarm
         Create GenericFakeRider1 ContainInsideSourceObject=Yes  (DISARM)
         Create hussienPreparationUpgradeRemover NOT contained
  pay    Command_Rearm / Command_BuyAlhussaienMissile = OBJECT_UPGRADE
         Upgrade Type=OBJECT  (engine refuses if funds insufficient)
  restore ObjectCreationUpgrade -> OCL ContainInsideSourceObject GenericFakeRider2
  reset  contained UpgradeDie stripper removes the OBJECT upgrade

Factory A-J in PR #593 are 9P117 clones:
  KindOf without GARRISONABLE_UNTIL_DESTROYED
  WeaponSet Conditions=None only
  no RiderChangeContain / InitialPayload
  empty WeaponSetUpgrade + ProductionUpdate
  they spawn.

PR #594 copied the Alabaas CONTAIN stack onto factory TELs. That is the
spawn crash: InitialPayload into a non-contain 9P117 truck.
PR #595 added GARRISONABLE_UNTIL_DESTROYED but left RiderChangeContain +
InitialPayload. The contain stack is Alabaas-structure, not the payment,
and is not compatible with these models.

This packer:
  * Restores factory A-J object bodies from PR #593 (spawn-safe)
  * Keeps the Alabaas PAYMENT (OBJECT_UPGRADE Type=OBJECT, half BuildCost,
    BuildTime 0.0) already added in PR #594
  * Restores firing via WeaponSetUpgrade already present on these objects
  * Resets via the NON-contained UpgradeDie pattern already in Alabaas
    (hussienPreparationUpgradeRemover), not ContainInsideSourceObject
  * Removes FireOCL OCL_HussienMissileDisarm from factory weapons
    (that OCL inserts a rider inside the firer)

Country TELs that already had RiderChangeContain are left as in PR #595.
ART is a byte-identical copy of PR #593. 9P117 is frozen.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_593_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_TOP_MARKINGS/_SPEC_DATA_ONE.big"
SRC_595_DATA = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_REARM_SPAWN/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_TOP_MARKINGS/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_ALABAAS_REARM"

SHA_593_DATA = "6af19c95f508a80752e26fd603d2745b5c2c51d446890a3f373816d329033f27"
SIZE_593_DATA = 366515208
SHA_595_DATA = "6c3e2d75fdb2b0cbe6063563285bcb4794c03639c124421718de9b16c038e2f9"
SIZE_595_DATA = 366621160
SHA_593_ART = "95a0737f7f6e7d0f15a2a1234b222d1cf9643d1199b00e28e7e87e7c89083ed4"
SIZE_593_ART = 1294467676

R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
STRIP_KEY = r"Data\INI\Object\Specter\Iraq Army\MissileHalfPriceRearm.ini"
UPG_NEW_KEY = r"Data\INI\Upgrade_MissileHalfPriceRearm.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
WEAPON_A_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlFahd500.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
OCL_KEY = r"Data\INI\ObjectCreationList.ini"

FACTORY = [
    {"object": "Iraq_AlFahd500", "weapon": "Weapon_Iraq_AlFahd500", "cost": 2200, "rearm": 1100,
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini", "wkey": WEAPON_A_KEY},
    {"object": "Iraq_AlHusseinII", "weapon": "Weapon_Iraq_AlHusseinII", "cost": 1800, "rearm": 900,
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHusseinII.ini", "wkey": WEAPON_KEY},
    {"object": "Iraq_AlSamoudII", "weapon": "Weapon_Iraq_AlSamoudII", "cost": 1700, "rearm": 850,
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlSamoudII.ini", "wkey": WEAPON_KEY},
    {"object": "Iraq_AlAbbas", "weapon": "Weapon_Iraq_AlAbbas", "cost": 2600, "rearm": 1300,
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini", "wkey": WEAPON_KEY},
    {"object": "Iraq_AlBasrah", "weapon": "Weapon_Iraq_AlBasrah", "cost": 5000, "rearm": 2500,
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlBasrah.ini", "wkey": WEAPON_KEY},
    {"object": "Iraq_AlNasir", "weapon": "Weapon_Iraq_AlNasir", "cost": 6500, "rearm": 3250,
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNasir.ini", "wkey": WEAPON_KEY},
    {"object": "Iraq_AlMansour", "weapon": "Weapon_Iraq_AlMansour", "cost": 8000, "rearm": 4000,
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlMansour.ini", "wkey": WEAPON_KEY},
]

KIND_593 = "PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE"


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


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def decode(blob: bytes) -> str:
    return blob.decode("latin1").replace("\r\n", "\n")


def object_blocks(text: str) -> list[tuple[str, int, int]]:
    found = [(m.group(1), m.start()) for m in re.finditer(r"^Object\s+(\S+)\s*$", text, re.M)]
    spans = []
    for i, (name, start) in enumerate(found):
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


def ids_for(obj: str) -> dict[str, str]:
    # Iraq_AlAbbasCommandSet already belongs to the Al-Abbas BUILDING.
    cmdset = f"{obj}TELCommandSet" if obj == "Iraq_AlAbbas" else f"{obj}CommandSet"
    return {
        "upgrade": f"Upgrade_Rearm_{obj}",
        "button": f"Command_Rearm_{obj}",
        "cmdset": cmdset,
        "ocl": f"OCL_Rearm_{obj}",
        "strip": f"RearmStrip_{obj}",
    }


def patch_factory_object(text_593: str, spec: dict) -> str:
    """Start from the PR #593 spawn-safe object and add only payment modules."""
    ids = ids_for(spec["object"])
    body = object_body(text_593, spec["object"])
    if not body:
        raise SystemExit(f"593 missing {spec['object']}")
    if "RiderChangeContain" in body or "InitialPayload" in body:
        raise SystemExit(f"593 {spec['object']} already has contain stack")
    if field(body, "KindOf") != KIND_593:
        raise SystemExit(f"593 {spec['object']} KindOf unexpected: {field(body,'KindOf')}")
    new = body
    new = re.sub(
        r"(CommandSet\s*=\s*)Scud_B_CommandSet",
        rf"\g<1>{ids['cmdset']}",
        new,
        count=1,
    )
    none_set = (
        "  WeaponSet\n"
        "    Conditions = None\n"
        f"    Weapon = PRIMARY   {spec['weapon']}\n"
        "  End\n"
    )
    player_set = (
        "  WeaponSet\n"
        "    Conditions = PLAYER_UPGRADE\n"
        f"    Weapon = PRIMARY   {spec['weapon']}\n"
        "  End\n"
    )
    if none_set not in new:
        raise SystemExit(f"593 {spec['object']} missing None weapon set")
    if "Conditions = PLAYER_UPGRADE" not in new:
        new = new.replace(none_set, none_set + player_set, 1)
    old_wsu = (
        "  Behavior = WeaponSetUpgrade ModuleTag_09h56u56j\n"
        "  End\n"
    )
    new_wsu = (
        "  Behavior = WeaponSetUpgrade ModuleTag_09h56u56j\n"
        f"    TriggeredBy = {ids['upgrade']}\n"
        "  End\n"
    )
    if old_wsu not in new:
        raise SystemExit(f"593 {spec['object']} missing empty WeaponSetUpgrade")
    new = new.replace(old_wsu, new_wsu, 1)
    if "RiderChangeContain" in new or "GARRISONABLE_UNTIL_DESTROYED" in new:
        raise SystemExit(f"patch reintroduced contain on {spec['object']}")
    if field(new, "BuildCost") != str(spec["cost"]):
        raise SystemExit(f"{spec['object']} BuildCost mutated")
    return text_593.replace(body, new, 1)


def patch_weapon(text: str, spec: dict) -> str:
    ids = ids_for(spec["object"])
    block = command_block(text, "Weapon", spec["weapon"])
    if not block:
        return text
    new = block
    if re.search(r"^\s*FireOCL\s*=", new, re.M):
        new = re.sub(
            r"^(\s*FireOCL\s*=\s*)\S+",
            rf"\g<1>{ids['ocl']}",
            new,
            count=1,
            flags=re.M,
        )
    else:
        if re.search(r"^\s*FireFX\s*=", new, re.M):
            new = re.sub(
                r"(^\s*FireFX\s*=\s*\S+\s*$)",
                rf"\1\n  FireOCL                     = {ids['ocl']}",
                new,
                count=1,
                flags=re.M,
            )
        else:
            new = re.sub(
                r"(^\s*ProjectileObject\s*=\s*\S+\s*$)",
                rf"\1\n  FireOCL                     = {ids['ocl']}",
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
    if ids["ocl"] not in new:
        raise SystemExit(f"FireOCL retarget failed {spec['weapon']}")
    if "OCL_HussienMissileDisarm" in new:
        raise SystemExit(f"{spec['weapon']} still uses contain FireOCL")
    return text.replace(block, new, 1)


def rewrite_factory_ocl(ocl_text: str, spec: dict) -> str:
    """Replace contain-inside rearm OCL with Alabaas non-contained stripper create."""
    ids = ids_for(spec["object"])
    old = command_block(ocl_text, "ObjectCreationList", ids["ocl"])
    if not old:
        raise SystemExit(f"missing {ids['ocl']}")
    new = (
        f"ObjectCreationList {ids['ocl']}\n"
        f"  CreateObject\n"
        f"    Offset = X:0 Y:0 Z:10\n"
        f"    ObjectNames = {ids['strip']}\n"
        f"    IgnorePrimaryObstacle = Yes\n"
        f"    Disposition = LIKE_EXISTING\n"
        f"    Count = 1\n"
        f"    RequiresLivePlayer = Yes\n"
        f"  End\n"
        f"End"
    )
    return ocl_text.replace(old, new, 1)


def patch_factory_strips(text: str) -> str:
    new = text
    for spec in FACTORY:
        ids = ids_for(spec["object"])
        # Match either leftover tag from #594/#595.
        new = re.sub(
            rf"(UpgradeToRemove\s*=\s*{re.escape(ids['upgrade'])}\s+)\S+",
            r"\g<1>ModuleTag_09h56u56j",
            new,
            count=1,
        )
        body = object_body(new, ids["strip"])
        if not body or "ModuleTag_09h56u56j" not in body:
            raise SystemExit(f"strip tag patch failed {spec['object']}")
    return new


def make_commandsets() -> str:
    chunks = ["\n"]
    for spec in FACTORY:
        ids = ids_for(spec["object"])
        chunks.append(
            f"CommandSet {ids['cmdset']}\n"
            f"  1 = Command_FireMainWeapon\n"
            f"  5 = {ids['button']}\n"
            f"  6 = Command_ScudSwitchToHE\n"
            f"  8 = Command_ScudSwitchToHE_NI\n"
            f"  10 = Command_ScudSwitchToHE_CH\n"
            f"  12 = Command_AttackMove\n"
            f"  13 = Command_Guard\n"
            f"  14 = Command_Stop\n"
            f"End\n\n"
        )
    return "".join(chunks)


def validate(data: dict[str, bytes], d593: dict[str, bytes], d595: dict[str, bytes]) -> list[str]:
    fails = []
    if decode(data[R11_KEY]) != decode(d593[R11_KEY]):
        fails.append("9P117 mutated vs PR #593")
    if decode(data[R11_KEY]) != decode(d595[R11_KEY]):
        fails.append("9P117 mutated vs PR #595")
    cs = decode(data[CS_KEY])
    cb = decode(data[CB_KEY])
    ocl = decode(data[OCL_KEY])
    upg = decode(data[UPG_NEW_KEY])
    strips = decode(data[STRIP_KEY])
    for spec in FACTORY:
        ids = ids_for(spec["object"])
        body = object_body(decode(data[spec["ini"]]), spec["object"])
        b593 = object_body(decode(d593[spec["ini"]]), spec["object"])
        if not body:
            fails.append(f"missing {spec['object']}")
            continue
        if "RiderChangeContain" in body or "InitialPayload" in body:
            fails.append(f"{spec['object']} still has contain/payload")
        if "GARRISONABLE_UNTIL_DESTROYED" in field(body, "KindOf"):
            fails.append(f"{spec['object']} still garrisonable")
        if "ObjectCreationUpgrade" in body:
            fails.append(f"{spec['object']} still has ObjectCreationUpgrade contain restore")
        if field(body, "KindOf") != KIND_593:
            fails.append(f"{spec['object']} KindOf {field(body,'KindOf')}")
        if field(body, "BuildCost") != str(spec["cost"]):
            fails.append(f"{spec['object']} BuildCost changed")
        if field(body, "BuildTime") != field(b593, "BuildTime"):
            fails.append(f"{spec['object']} BuildTime changed")
        if field(body, "CommandSet") != ids["cmdset"]:
            fails.append(f"{spec['object']} CommandSet {field(body,'CommandSet')}")
        if "Conditions = None" not in body or spec["weapon"] not in body:
            fails.append(f"{spec['object']} lost None weapon set")
        if "Conditions = PLAYER_UPGRADE" not in body:
            fails.append(f"{spec['object']} missing PLAYER_UPGRADE weapon set")
        wsu = re.search(r"(?ms)Behavior = WeaponSetUpgrade ModuleTag_09h56u56j\n.*?^  End", body)
        if not wsu or ids["upgrade"] not in wsu.group(0):
            fails.append(f"{spec['object']} WeaponSetUpgrade not wired to unique upgrade")
        u = command_block(upg, "Upgrade", ids["upgrade"])
        if field(u, "BuildCost") != str(spec["rearm"]) or field(u, "BuildTime") != "0.0" or field(u, "Type") != "OBJECT":
            fails.append(f"{spec['object']} payment upgrade mutated")
        if not command_block(cb, "CommandButton", ids["button"]):
            fails.append(f"missing {ids['button']}")
        setb = command_block(cs, "CommandSet", ids["cmdset"])
        if not setb or ids["button"] not in setb or "Command_FireMainWeapon" not in setb:
            fails.append(f"missing/incomplete {ids['cmdset']}")
        o = command_block(ocl, "ObjectCreationList", ids["ocl"])
        if not o:
            fails.append(f"missing {ids['ocl']}")
        elif "ContainInsideSourceObject" in o:
            fails.append(f"{ids['ocl']} still contains inside source (spawn/fire crash)")
        elif ids["strip"] not in o:
            fails.append(f"{ids['ocl']} missing stripper")
        st = object_body(strips, ids["strip"])
        if not st or "ModuleTag_09h56u56j" not in st:
            fails.append(f"{ids['strip']} not targeting WeaponSetUpgrade")
        wtext = decode(data[spec["wkey"]])
        wblock = command_block(wtext, "Weapon", spec["weapon"])
        if spec["wkey"] == WEAPON_A_KEY and not wblock:
            wblock = command_block(decode(data[WEAPON_KEY]), "Weapon", spec["weapon"])
        orig = command_block(decode(d593[spec["wkey"]]), "Weapon", spec["weapon"])
        if spec["wkey"] == WEAPON_A_KEY and not orig:
            orig = command_block(decode(d593[WEAPON_KEY]), "Weapon", spec["weapon"])
        for k in ("WeaponSpeed", "PrimaryDamage", "AttackRange"):
            if field(wblock, k) != field(orig, k):
                fails.append(f"{spec['weapon']} {k} changed")
        if field(wblock, "AutoReloadsClip") != "No":
            fails.append(f"{spec['weapon']} AutoReloadsClip {field(wblock,'AutoReloadsClip')}")
        if ids["ocl"] not in (wblock or ""):
            fails.append(f"{spec['weapon']} FireOCL not factory disarm OCL")
        if "OCL_HussienMissileDisarm" in (wblock or ""):
            fails.append(f"{spec['weapon']} still FireOCL contain")
    # Country Alabaas-pattern TELs must keep their #595 rider stack.
    abbas = object_body(decode(data[r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini"]), "Iraq_Alhussaien")
    if "RiderChangeContain" not in (abbas or "") or "Upgrade_Rearm_Iraq_Alhussaien" not in (abbas or ""):
        fails.append("Iraq_Alhussaien rider payment path mutated")
    return fails


def main() -> int:
    if sha256_path(SRC_593_DATA) != SHA_593_DATA or SRC_593_DATA.stat().st_size != SIZE_593_DATA:
        raise SystemExit("PR #593 DATA mismatch")
    if sha256_path(SRC_595_DATA) != SHA_595_DATA or SRC_595_DATA.stat().st_size != SIZE_595_DATA:
        raise SystemExit("PR #595 DATA mismatch")
    if sha256_path(SRC_ART) != SHA_593_ART or SRC_ART.stat().st_size != SIZE_593_ART:
        raise SystemExit("PR #593 ART mismatch")

    d593 = parse_big(SRC_593_DATA.read_bytes())
    d595 = parse_big(SRC_595_DATA.read_bytes())
    data = dict(d595)

    for spec in FACTORY:
        restored = decode(d593[spec["ini"]])
        data[spec["ini"]] = to_crlf(patch_factory_object(restored, spec))
        mapped = ROOT / "patch" / spec["ini"].replace("\\", "/")
        if mapped.exists():
            mapped.write_bytes(data[spec["ini"]])

    wtext = decode(data[WEAPON_KEY])
    for spec in FACTORY:
        if spec["wkey"] == WEAPON_KEY:
            wtext = patch_weapon(wtext, spec)
    data[WEAPON_KEY] = to_crlf(wtext)
    if WEAPON_A_KEY in data:
        data[WEAPON_A_KEY] = to_crlf(patch_weapon(decode(data[WEAPON_A_KEY]), FACTORY[0]))
        src_a = ROOT / "patch/Data/INI/Weapon/Weapon_Iraq_AlFahd500.ini"
        if src_a.exists():
            src_a.write_bytes(data[WEAPON_A_KEY])

    ocl = decode(data[OCL_KEY])
    for spec in FACTORY:
        ocl = rewrite_factory_ocl(ocl, spec)
    data[OCL_KEY] = to_crlf(ocl)

    data[STRIP_KEY] = to_crlf(patch_factory_strips(decode(data[STRIP_KEY])))
    strip_src = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/MissileHalfPriceRearm.ini"
    strip_src.write_bytes(data[STRIP_KEY])

    data[CS_KEY] = data[CS_KEY] + to_crlf(make_commandsets())

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    shutil.copy2(SRC_ART, OUT / "_SPEC_ART_ONE.big")
    extracted = parse_big(out_data.read_bytes())

    fails = validate(extracted, d593, d595)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    if sha256_path(OUT / "_SPEC_ART_ONE.big") != SHA_593_ART:
        fails.append("ART copy not byte-identical")

    changed_vs_593 = sorted(k for k in extracted if d593.get(k) != extracted.get(k))
    changed_vs_595 = sorted(k for k in extracted if d595.get(k) != extracted.get(k))
    data_sha = sha256_path(out_data)
    report = [
        "# SPECTER factory A-J: Alabaas payment without contain spawn crash",
        "",
        "Alabaas chain (packed last-wins):",
        "  fire HussieanMissileWeapon",
        "    -> FireOCL OCL_HussienMissileDisarm",
        "    -> GenericFakeRider1 ContainInsideSourceObject (DISARM)",
        "    -> pay OBJECT_UPGRADE Upgrade_Rearm_Iraq_Alhussaien",
        "    -> ObjectCreationUpgrade ModuleTag_Rearm",
        "    -> OCL_Rearm_Iraq_Alhussaien GenericFakeRider2 contain (RESTORE)",
        "    -> UpgradeDie stripper (RESET)",
        "",
        "Factory A-J cannot use that contain stack (PR #594/#595 spawn crash).",
        "Restored PR #593 factory object bodies. Reused only:",
        "  OBJECT_UPGRADE Type=OBJECT half BuildCost BuildTime 0.0  (Alabaas pay)",
        "  WeaponSetUpgrade already on the 9P117-style objects     (restore)",
        "  non-contained UpgradeDie like hussienPreparationUpgradeRemover (reset)",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART size: {SIZE_593_ART}",
        f"- ART SHA256: {SHA_593_ART}",
        f"- Changed vs PR #593: {', '.join(changed_vs_593)}",
        f"- Changed vs PR #595: {', '.join(changed_vs_595)}",
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
        "- Factory A-J have no RiderChangeContain / InitialPayload / GARRISONABLE",
        "- KindOf matches PR #593 spawn-safe 9P117 clones",
        "- First shot: Conditions=None primary weapon, no pre-pay",
        "- Pay: unique OBJECT upgrade at 50% BuildCost, BuildTime 0.0",
        "- Restore: WeaponSetUpgrade -> PLAYER_UPGRADE weapon set",
        "- Reset: non-contained FireOCL stripper (no ContainInsideSourceObject)",
        "- Factory weapons damage/speed/range unchanged; contain FireOCL removed",
        "- Iraq_Alhussaien rider path and 9P117 unchanged; ART = PR #593",
        "",
        "Static validation completed; runtime game test not performed.",
        "Unresolved runtime steps: produce A-J, first shot, pay re-arm,",
        "insufficient funds, repeat fire/re-arm.",
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
        f"ART_SIZE={SIZE_593_ART}\n"
        f"ART_SHA256={SHA_593_ART}\n"
        f"CHANGED_VS_593={', '.join(changed_vs_593)}\n"
        f"CHANGED_VS_595={', '.join(changed_vs_595)}\n"
        "ALABAAS_CHAIN=fire FireOCL contain rider1 -> OBJECT_UPGRADE -> contain rider2 -> UpgradeDie\n"
        "FACTORY_ADAPT=PR593 spawn body + OBJECT_UPGRADE + WeaponSetUpgrade + non-contained UpgradeDie\n"
        "BASELINE=PR #595 DATA history + PR #593 factory objects/ART\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: factory A-J spawn-safe Alabaas payment re-arm\n"
        "\n"
        "Removes the incompatible RiderChangeContain/InitialPayload copy that\n"
        "crashed factory production in PR #594/#595. Factory missiles spawn as\n"
        "in PR #593. Re-arm payment is the Alabaas OBJECT_UPGRADE at half cost.\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "  _SPEC_ART_ONE.big  (unchanged from PR #593)\n"
        "\n"
        "Static validation completed; runtime game test not performed.\n",
        encoding="utf-8",
    )
    (OUT / "INVENTORY.txt").write_text(
        "Alabaas (unchanged rider path): Iraq_Alhussaien build $20000 -> re-arm $10000\n"
        "Factory A-J (PR #593 spawn body + OBJECT_UPGRADE payment):\n"
        "- Iraq_AlFahd500: build $2200 -> re-arm $1100\n"
        "- Iraq_AlHusseinII: build $1800 -> re-arm $900\n"
        "- Iraq_AlSamoudII: build $1700 -> re-arm $850\n"
        "- Iraq_AlAbbas: build $2600 -> re-arm $1300\n"
        "- Iraq_AlBasrah: build $5000 -> re-arm $2500\n"
        "- Iraq_AlNasir: build $6500 -> re-arm $3250\n"
        "- Iraq_AlMansour: build $8000 -> re-arm $4000\n"
        "No RiderChangeContain / InitialPayload / GARRISONABLE on factory A-J.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_ALABAAS_REARM.zip"
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
