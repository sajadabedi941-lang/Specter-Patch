#!/usr/bin/env python3
"""Iraq Al-Abbas: production BuildTime 30.0; Fire already unlocked.

Live DATA baseline: SPECTER_IRAQ_RADAR_STEALTH_SPEED
ART unchanged.

Object Iraq_AlAbbas BuildTime 35.0 -> 30.0 (factory UNIT_BUILD production).
Rebuild stays Upgrade_Iraq_AlAbbas_Rebuild BuildCost 1300 / BuildTime 35.0.
Fire is Command_FireMainWeapon with no Science/Upgrade/NEED_SPECIAL_POWER_SCIENCE.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_RADAR_STEALTH_SPEED/_SPEC_DATA_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_BUILDTIME"
UNIT_SRC = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlAbbas.ini"

BASE_DATA_SHA = "acaa2a5e8a8851bbb6ce5021e920f7391f80f2d868f933daa0f21e72352bdae4"
BASE_DATA_SIZE = 366473321
PREV_ART_SHA = "e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4"
PREV_ART_SIZE = 1292294758

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CSF_KEY = r"Data\English\generals.csf"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
LOCO_KEY = r"Data\INI\Locomotor.ini"
UNIT_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
PROJ_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini"
WEP_A_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlFahd500.ini"
WEP_NEW_KEY = r"Data\INI\Weapon\Weapon_Iraq_FactoryMissiles.ini"
LOCO_NEW_KEY = r"Data\INI\Locomotor_IraqFactoryMissiles.ini"
UPG_KEY = r"Data\INI\Upgrade_IraqFactoryMissiles.ini"
UNIT_D_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini"
PROJ_D_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlAbbas_Projectile.ini"

OTHER_UNITS = [
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHusseinII.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlSamoudII.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlBasrah.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNasir.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlMansour.ini",
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


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")


def command_block(text: str, kind: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text)
    return m.group(0) if m else None


def slot_map(block: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    expected = header
    for name, off, size in sorted(files, key=lambda x: x[1]):
        if off != expected:
            issues.append(f"overlap/gap {name}")
            break
        expected = off + size
    if expected != len(blob):
        issues.append("trailing gap/overflow")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def last_weapon_block(data: dict[str, bytes], name: str) -> tuple[str, str] | None:
    blocks: list[tuple[str, str]] = []
    wep = data[WEAPON_KEY].decode("latin1")
    b = command_block(wep, "Weapon", name)
    if b:
        blocks.append((WEAPON_KEY, b))
    weapon_dir = [
        k
        for k in data
        if k.replace("/", "\\").lower().startswith(r"data\ini\weapon" + "\\") and k.lower().endswith(".ini")
    ]
    for k in sorted(weapon_dir, key=lambda x: x.lower()):
        t = data[k].decode("utf-8")
        b = command_block(t, "Weapon", name)
        if b:
            blocks.append((k, b))
    return blocks[-1] if blocks else None


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    protected = [
        R11_KEY, WEAPON_KEY, FACTORY_KEY, CB_KEY, CS_KEY, CSF_KEY, LOCO_KEY,
        UNIT_A_KEY, PROJ_A_KEY, WEP_A_KEY, WEP_NEW_KEY, LOCO_NEW_KEY, UPG_KEY, PROJ_D_KEY,
    ] + OTHER_UNITS
    for key in protected:
        if data.get(key) != src.get(key):
            fails.append(f"protected file mutated {key}")

    changed = sorted(k for k in set(data) | set(src) if data.get(k) != src.get(k))
    if changed != [UNIT_D_KEY]:
        fails.append(f"unexpected DATA changes {changed}")

    n = len(re.findall(rb"^Object Iraq_AlAbbas\s*$", b"".join(v for k, v in data.items() if k.lower().endswith(".ini")), re.M))
    if n != 1:
        fails.append(f"Iraq_AlAbbas definition count {n}")

    unit = data[UNIT_D_KEY].decode("utf-8")
    if "BuildTime       = 30.0" not in unit:
        fails.append("BuildTime not 30.0")
    if "BuildTime       = 35.0" in unit:
        fails.append("old BuildTime 35.0 still present")
    if "BuildCost       = 2600" not in unit:
        fails.append("price changed")
    if "SelectPortrait         = specter_missile_d" not in unit or "ButtonImage            = specter_missile_d" not in unit:
        fails.append("queue icon")
    if "Weapon = PRIMARY   Weapon_Iraq_AlAbbas" not in unit:
        fails.append("weapon")
    if "CommandSet    = Iraq_AlAbbas_TELCommandSet" not in unit:
        fails.append("commandset")
    if "ReplaceObject = Iraq_AlAbbas" not in unit or "TriggeredBy   = Upgrade_Iraq_AlAbbas_Rebuild" not in unit:
        fails.append("rebuild ReplaceObjectUpgrade")
    if "IRQ_AF500.IRQ_AF500" not in unit:
        fails.append("launch anim")

    src_unit = src[UNIT_D_KEY].decode("utf-8")
    a = src_unit.replace("BuildTime       = 35.0", "BuildTime       = 30.0", 1)
    if a.replace("\r\n", "\n") != unit.replace("\r\n", "\n"):
        fails.append("Al-Abbas unit has edits besides BuildTime")

    upg = command_block(data[UPG_KEY].decode("utf-8"), "Upgrade", "Upgrade_Iraq_AlAbbas_Rebuild") or ""
    if "BuildCost        = 1300" not in upg or "BuildTime        = 35.0" not in upg:
        fails.append("rebuild upgrade cost/time changed")

    wep = last_weapon_block(data, "Weapon_Iraq_AlAbbas")
    if not wep:
        fails.append("weapon missing")
    else:
        if "AutoReloadsClip             = No" not in wep[1] or "ClipSize                    = 1" not in wep[1]:
            fails.append("clip/rebuild weapon flags")
        if "PrimaryDamage               = 6000.0" not in wep[1] or "AttackRange                 = 2752.0" not in wep[1]:
            fails.append("range/damage")
        if "ScatterRadius               = 70" not in wep[1] or "WeaponSpeed                 = 840" not in wep[1]:
            fails.append("accuracy/speed")
        if "ProjectileObject            = Projectile_Iraq_AlAbbas" not in wep[1]:
            fails.append("projectile")

    proj = data[PROJ_D_KEY].decode("utf-8")
    if "Locomotor = SET_NORMAL Iraq_AlAbbas_Locomotor" not in proj or "Model = Irq_AlAbbas2M" not in proj:
        fails.append("projectile loco/model")

    btn = command_block(data[CB_KEY].decode("latin1"), "CommandButton", "CB_MISSILE_D") or ""
    if "Object        = Iraq_AlAbbas" not in btn or "ButtonImage   = specter_missile_d" not in btn:
        fails.append("CB_MISSILE_D")

    fire = command_block(data[CB_KEY].decode("latin1"), "CommandButton", "Command_FireMainWeapon") or ""
    if "Command           = FIRE_WEAPON" not in fire or "WeaponSlot        = PRIMARY" not in fire:
        fails.append("Fire CommandButton")
    if "NEED_SPECIAL_POWER_SCIENCE" in fire or re.search(r"^\s*Science\s*=", fire, re.M):
        fails.append("Fire still science-gated")
    if "Upgrade" in fire:
        fails.append("Fire has Upgrade field")

    tel = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlAbbas_TELCommandSet") or ""
    slots = slot_map(tel)
    if slots.get(1) != "Command_FireMainWeapon" or slots.get(2) != "CB_Iraq_AlAbbas_Rebuild":
        fails.append(f"TEL CommandSet {slots}")

    fac = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet") or ""
    fslots = slot_map(fac)
    if fslots.get(4) != "CB_MISSILE_D" or fslots.get(1) != "CB_MISSILE_A":
        fails.append(f"factory CommandSet {fslots}")
    for empty in (5, 6, 7, 11, 12):
        if empty in fslots:
            fails.append(f"unwired slot filled {empty}")

    r11 = data[R11_KEY]
    if r11 != src[R11_KEY]:
        fails.append("MOTHER 9P117 mutated")

    zzzz = [k for k in data if "zzzz" in k.lower() and b"Iraq_AlAbbas" in data[k]]
    if zzzz:
        fails.append(f"ZZZZ {zzzz[:4]}")
    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("live DATA baseline mismatch")
    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)
    unit = UNIT_SRC.read_text(encoding="utf-8")
    if "BuildTime       = 30.0" not in unit or "BuildCost       = 2600" not in unit:
        raise SystemExit("workspace Iraq_AlAbbas.ini not updated")
    data[UNIT_D_KEY] = to_crlf(unit)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    extracted = parse_big(packed)

    stage = OUT / "LAST_WINS_EXTRACT"
    (stage / "DATA").mkdir(parents=True)
    for rel in [UNIT_D_KEY, UPG_KEY, R11_KEY]:
        p = stage / "DATA" / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])

    fails = validate(extracted, src)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    data_sha = sha256_path(out_data)
    report = [
        "# SPECTER Iraq Al-Abbas BuildTime 30s; Fire already unlocked",
        "",
        "Object: Iraq_AlAbbas",
        "Construct: CB_MISSILE_D",
        "Fire: Command_FireMainWeapon (no Science / no Upgrade / no NEED_SPECIAL_POWER_SCIENCE)",
        "CommandSet: Iraq_AlAbbas_TELCommandSet slot 1 = Fire, slot 2 = rebuild",
        "BuildTime 35.0 -> 30.0",
        "Price $2600 unchanged. Rebuild $1300 / 35.0s unchanged.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART SHA256 (unchanged): {PREV_ART_SHA}",
        f"- ART size (unchanged): {PREV_ART_SIZE}",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        report.append("RUNTIME TEST: NOT PERFORMED")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static)",
        "- last-wins Iraq_AlAbbas BuildTime = 30.0",
        "- Fire Command_FireMainWeapon has no Science/Upgrade gate (already unlocked; no CommandButton edit)",
        "- rebuild Upgrade_Iraq_AlAbbas_Rebuild $1300 / 35s + ReplaceObjectUpgrade + ClipSize 1 + AutoReloadsClip No",
        "- range/damage/accuracy/speed/loco/projectile/price/queue icon unchanged",
        "- MOTHER/9P117 byte-identical; other missiles unchanged; ART not rebuilt; no ZZZZ",
        "",
        "RUNTIME TEST: NOT PERFORMED",
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
        f"ART_SHA256={PREV_ART_SHA}\n"
        "OBJECT=Iraq_AlAbbas\n"
        "BUILDTIME=35.0->30.0\n"
        "PRICE=2600\n"
        "REBUILD_COST=1300\n"
        "REBUILD_TIME=35.0\n"
        "FIRE=Command_FireMainWeapon already unlocked\n"
        "COMMANDBUTTON_CHANGED=NO\n"
        "PREREQUISITE_REMOVED=none (Fire had no Science/Upgrade gate)\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT PERFORMED\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq Al-Abbas production BuildTime 30s (DATA-only)\n"
        "Place this complete replacement DATA BIG in the game folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "Keep the previous complete ART BIG. Fire was already unlocked.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_BUILDTIME.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
