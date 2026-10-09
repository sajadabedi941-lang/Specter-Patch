#!/usr/bin/env python3
"""Fix Iraq factory A-J spawn crash introduced by PR #594.

Baseline: PR #594 SPECTER_MISSILE_HALF_PRICE_REARM DATA + PR #593 ART.

Root cause (packed last-wins vs working Alabaas / PR #593):
  Factory missiles A-J received RiderChangeContain + InitialPayload
  GenericFakeRider2 + WEAPON_RIDER weapon sets, but kept the 9P117 KindOf
  without GARRISONABLE_UNTIL_DESTROYED. Every working Alabaas-pattern TEL
  has that flag; RiderChangeContain is a TransportContain and crashes on
  spawn when InitialPayload is inserted into a non-garrisonable vehicle.
  PR #594 also replaced the Conditions=None WeaponSet, so the unit has no
  weapon set during the window before the rider is applied.

Fix (factory objects only):
  * Add GARRISONABLE_UNTIL_DESTROYED to KindOf (Alabaas contain requirement)
  * Restore WeaponSet Conditions=None with the original primary weapon
  * Forbid infantry/vehicles so the TEL does not become a troop transport
  * Point factory UpgradeDie at ModuleTag_Rearm (the actual host module)

Unrelated country TEL re-arm, weapons damage/speed/range, 9P117, ART,
costs, and factory roster are unchanged.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_MISSILE_HALF_PRICE_REARM/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_MISSILE_HALF_PRICE_REARM/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_REARM_SPAWN"
SRC_DIR = ROOT / "patch/Data/INI"

BASE_DATA_SHA = "af77afe778c7536126b26f6abb29f8a338c0f2fa1697be4d0a3025a4b48675a3"
BASE_DATA_SIZE = 366620007
BASE_ART_SHA = "95a0737f7f6e7d0f15a2a1234b222d1cf9643d1199b00e28e7e87e7c89083ed4"
BASE_ART_SIZE = 1294467676

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
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"},
    {"object": "Iraq_AlHusseinII", "weapon": "Weapon_Iraq_AlHusseinII", "cost": 1800, "rearm": 900,
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHusseinII.ini"},
    {"object": "Iraq_AlSamoudII", "weapon": "Weapon_Iraq_AlSamoudII", "cost": 1700, "rearm": 850,
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlSamoudII.ini"},
    {"object": "Iraq_AlAbbas", "weapon": "Weapon_Iraq_AlAbbas", "cost": 2600, "rearm": 1300,
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini"},
    {"object": "Iraq_AlBasrah", "weapon": "Weapon_Iraq_AlBasrah", "cost": 5000, "rearm": 2500,
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlBasrah.ini"},
    {"object": "Iraq_AlNasir", "weapon": "Weapon_Iraq_AlNasir", "cost": 6500, "rearm": 3250,
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNasir.ini"},
    {"object": "Iraq_AlMansour", "weapon": "Weapon_Iraq_AlMansour", "cost": 8000, "rearm": 4000,
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlMansour.ini"},
]

KIND_OLD = "PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE"
KIND_NEW = KIND_OLD + " GARRISONABLE_UNTIL_DESTROYED"


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
    found = []
    for m in re.finditer(r"^Object\s+(\S+)\s*$", text, re.M):
        found.append((m.group(1), m.start()))
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
    return {
        "upgrade": f"Upgrade_Rearm_{obj}",
        "button": f"Command_Rearm_{obj}",
        "unarmed": f"{obj}_UnarmedRearmSet",
        "ocl": f"OCL_Rearm_{obj}",
        "strip": f"RearmStrip_{obj}",
    }


def patch_factory_object(text: str, spec: dict) -> str:
    body = object_body(text, spec["object"])
    if not body:
        raise SystemExit(f"missing object {spec['object']}")
    new = body
    weapon = spec["weapon"]
    ids = ids_for(spec["object"])

    if "GARRISONABLE_UNTIL_DESTROYED" not in new:
        if KIND_OLD not in new:
            raise SystemExit(f"unexpected KindOf on {spec['object']}")
        new = new.replace(KIND_OLD, KIND_NEW, 1)

    none_set = (
        "  WeaponSet\n"
        "    Conditions = None\n"
        f"    Weapon = PRIMARY   {weapon}\n"
        "  End\n"
    )
    rider_header = (
        "  WeaponSet\n"
        "    Conditions = WEAPON_RIDER1\n"
    )
    if "WeaponSet\n    Conditions = None\n" not in new:
        if rider_header not in new:
            raise SystemExit(f"rider weapon set missing on {spec['object']}")
        new = new.replace(rider_header, none_set + rider_header, 1)

    if "ForbidInsideKindOf" not in new:
        if "AllowInsideKindOf     = PRELOAD\n" not in new:
            raise SystemExit(f"AllowInsideKindOf missing on {spec['object']}")
        new = new.replace(
            "    AllowInsideKindOf     = PRELOAD\n",
            "    AllowInsideKindOf     = PRELOAD\n"
            "    ForbidInsideKindOf    = INFANTRY VEHICLE STRUCTURE\n",
            1,
        )

    if field(new, "BuildCost") != str(spec["cost"]):
        raise SystemExit(f"{spec['object']} BuildCost mutated before patch")
    if ids["upgrade"] not in new:
        raise SystemExit(f"{spec['object']} lost unique re-arm upgrade")
    if "InitialPayload        = GenericFakeRider2_Default_Rank 1" not in new:
        raise SystemExit(f"{spec['object']} lost armed InitialPayload")
    return text.replace(body, new, 1)


def patch_factory_strips(text: str) -> str:
    new = text
    for spec in FACTORY:
        ids = ids_for(spec["object"])
        old = f"UpgradeToRemove     = {ids['upgrade']} ModuleTag_MissileRearm02"
        want = f"UpgradeToRemove     = {ids['upgrade']} ModuleTag_Rearm"
        if old not in new and want not in new:
            raise SystemExit(f"strip tag missing for {spec['object']}")
        new = new.replace(old, want, 1)
    return new


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails = []
    if decode(data[R11_KEY]) != decode(src[R11_KEY]):
        fails.append("9P117 object mutated")
    for spec in FACTORY:
        ids = ids_for(spec["object"])
        body = object_body(decode(data[spec["ini"]]), spec["object"])
        orig = object_body(decode(src[spec["ini"]]), spec["object"])
        if not body:
            fails.append(f"missing {spec['object']}")
            continue
        kind = field(body, "KindOf")
        if "GARRISONABLE_UNTIL_DESTROYED" not in kind:
            fails.append(f"{spec['object']} KindOf missing GARRISONABLE_UNTIL_DESTROYED")
        if "HUGE_VEHICLE" in kind or "SALVAGER" in kind:
            fails.append(f"{spec['object']} gained extra Alabaas KindOf flags")
        if field(body, "BuildCost") != str(spec["cost"]):
            fails.append(f"{spec['object']} BuildCost changed")
        if field(body, "BuildTime") != field(orig, "BuildTime"):
            fails.append(f"{spec['object']} BuildTime changed")
        if field(body, "CommandSet") != "Scud_B_CommandSet":
            fails.append(f"{spec['object']} CommandSet changed")
        sets = re.findall(r"WeaponSet\n((?:.*\n)*?)  End", body)
        conds = []
        for blk in sets:
            m = re.search(r"Conditions = (\S+)", blk)
            conds.append(m.group(1) if m else "?")
        if "None" not in conds:
            fails.append(f"{spec['object']} missing Conditions=None WeaponSet")
        if "WEAPON_RIDER1" not in conds or "WEAPON_RIDER2" not in conds:
            fails.append(f"{spec['object']} missing rider weapon sets")
        if spec["weapon"] not in body:
            fails.append(f"{spec['object']} lost primary weapon")
        if "RiderChangeContain" not in body:
            fails.append(f"{spec['object']} lost RiderChangeContain")
        if "InitialPayload        = GenericFakeRider2_Default_Rank 1" not in body:
            fails.append(f"{spec['object']} not starting armed")
        if "ForbidInsideKindOf    = INFANTRY VEHICLE STRUCTURE" not in body:
            fails.append(f"{spec['object']} missing ForbidInsideKindOf")
        if ids["upgrade"] not in body or ids["ocl"] not in body:
            fails.append(f"{spec['object']} lost re-arm ObjectCreationUpgrade")
        strip = object_body(decode(data[STRIP_KEY]), ids["strip"])
        if not strip or f"{ids['upgrade']} ModuleTag_Rearm" not in strip:
            fails.append(f"{spec['object']} stripper not ModuleTag_Rearm")
        upg = command_block(decode(data[UPG_NEW_KEY]), "Upgrade", ids["upgrade"])
        if field(upg, "BuildCost") != str(spec["rearm"]) or field(upg, "BuildTime") != "0.0":
            fails.append(f"{spec['object']} re-arm upgrade mutated")
        if not command_block(decode(data[CB_KEY]), "CommandButton", ids["button"]):
            fails.append(f"missing button {ids['button']}")
        if not command_block(decode(data[CS_KEY]), "CommandSet", ids["unarmed"]):
            fails.append(f"missing unarmed set {ids['unarmed']}")
        if not command_block(decode(data[OCL_KEY]), "ObjectCreationList", ids["ocl"]):
            fails.append(f"missing OCL {ids['ocl']}")
        wkey = WEAPON_A_KEY if spec["object"] == "Iraq_AlFahd500" else WEAPON_KEY
        wblock = command_block(decode(data[wkey]), "Weapon", spec["weapon"])
        if wkey == WEAPON_A_KEY and not wblock:
            wblock = command_block(decode(data[WEAPON_KEY]), "Weapon", spec["weapon"])
        orig_w = command_block(decode(src[wkey]), "Weapon", spec["weapon"])
        if wkey == WEAPON_A_KEY and not orig_w:
            orig_w = command_block(decode(src[WEAPON_KEY]), "Weapon", spec["weapon"])
        for k in ("WeaponSpeed", "PrimaryDamage", "AttackRange"):
            if field(wblock, k) != field(orig_w, k):
                fails.append(f"{spec['weapon']} {k} changed")
        if "OCL_HussienMissileDisarm" not in (wblock or ""):
            fails.append(f"{spec['weapon']} lost FireOCL")
    # Unrelated country TEL files must be byte-identical except factory + strip.
    allowed = {spec["ini"] for spec in FACTORY} | {STRIP_KEY}
    for key, blob in data.items():
        if src.get(key) != blob and key not in allowed:
            fails.append(f"unrelated DATA path changed: {key}")
    return fails


def main() -> int:
    if sha256_path(SRC_DATA) != BASE_DATA_SHA or SRC_DATA.stat().st_size != BASE_DATA_SIZE:
        raise SystemExit("PR #594 DATA baseline mismatch")
    if sha256_path(SRC_ART) != BASE_ART_SHA or SRC_ART.stat().st_size != BASE_ART_SIZE:
        raise SystemExit("PR #593 ART baseline mismatch")

    src_data = parse_big(SRC_DATA.read_bytes())
    data = dict(src_data)

    for spec in FACTORY:
        text = decode(data[spec["ini"]])
        data[spec["ini"]] = to_crlf(patch_factory_object(text, spec))
        mapped = ROOT / "patch" / spec["ini"].replace("\\", "/")
        if mapped.exists():
            mapped.write_bytes(data[spec["ini"]])

    data[STRIP_KEY] = to_crlf(patch_factory_strips(decode(data[STRIP_KEY])))
    strip_src = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/MissileHalfPriceRearm.ini"
    strip_src.write_bytes(data[STRIP_KEY])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    shutil.copy2(SRC_ART, OUT / "_SPEC_ART_ONE.big")
    extracted = parse_big(out_data.read_bytes())

    fails = validate(extracted, src_data)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    if sha256_path(OUT / "_SPEC_ART_ONE.big") != BASE_ART_SHA:
        fails.append("ART copy not byte-identical")

    changed = sorted(k for k in extracted if src_data.get(k) != extracted.get(k))
    data_sha = sha256_path(out_data)
    report = [
        "# SPECTER Iraq factory missile spawn crash fix (PR #594 regression)",
        "",
        "Baseline: PR #594 half-price re-arm DATA + PR #593 ART.",
        "ART is a byte-identical copy of PR #593.",
        "",
        "ROOT CAUSE: Factory A-J spawn (case B/C). PR #594 copied Alabaas",
        "RiderChangeContain + InitialPayload onto 9P117-style factory TELs that",
        "lack GARRISONABLE_UNTIL_DESTROYED, and removed Conditions=None WeaponSet.",
        "Working Alabaas-pattern TELs all have that KindOf flag. Contain init",
        "crashes when the factory finishes producing the unit.",
        "",
        "FIX: factory objects only — garrison KindOf, restore None WeaponSet,",
        "ForbidInsideKindOf INFANTRY VEHICLE STRUCTURE, stripper ModuleTag_Rearm.",
        "Half-price OBJECT_UPGRADE re-arm, first-shot armed rider, FireOCL disarm,",
        "costs, weapons, 9P117, and unrelated country TELs unchanged.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART size: {BASE_ART_SIZE}",
        f"- ART SHA256: {BASE_ART_SHA}",
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
        "- Factory A-J KindOf includes GARRISONABLE_UNTIL_DESTROYED",
        "- Conditions=None WeaponSet restored; WEAPON_RIDER1/2 retained",
        "- InitialPayload GenericFakeRider2 (first shot armed, no pre-pay)",
        "- Re-arm still 50% BuildCost, BuildTime 0.0, unique OBJECT upgrades",
        "- 9P117 / weapons damage/speed/range / unrelated TELs / ART unchanged",
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
        f"ART_SIZE={BASE_ART_SIZE}\n"
        f"ART_SHA256={BASE_ART_SHA}\n"
        f"CHANGED_DATA={', '.join(changed)}\n"
        "ROOT_CAUSE=factory RiderChangeContain InitialPayload without GARRISONABLE_UNTIL_DESTROYED\n"
        "BASELINE=PR #594 DATA + PR #593 ART\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Iraq factory missile spawn crash fix\n"
        "\n"
        "Fixes the PR #594 crash when the Iraq missile factory produces A-J.\n"
        "Half-price re-arm is preserved. ART is unchanged from PR #593.\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "  _SPEC_ART_ONE.big  (unchanged from PR #593)\n"
        "\n"
        "Static validation completed; runtime game test not performed.\n",
        encoding="utf-8",
    )
    (OUT / "INVENTORY.txt").write_text(
        "Factory A-J spawn fix; re-arm costs unchanged from PR #594:\n"
        "- Iraq_AlFahd500: build $2200 -> re-arm $1100\n"
        "- Iraq_AlHusseinII: build $1800 -> re-arm $900\n"
        "- Iraq_AlSamoudII: build $1700 -> re-arm $850\n"
        "- Iraq_AlAbbas: build $2600 -> re-arm $1300\n"
        "- Iraq_AlBasrah: build $5000 -> re-arm $2500\n"
        "- Iraq_AlNasir: build $6500 -> re-arm $3250\n"
        "- Iraq_AlMansour: build $8000 -> re-arm $4000\n"
        "KindOf += GARRISONABLE_UNTIL_DESTROYED; Conditions=None WeaponSet restored.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_REARM_SPAWN.zip"
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
