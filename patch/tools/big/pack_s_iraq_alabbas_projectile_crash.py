#!/usr/bin/env python3
"""Fix Iraq Al-Abbas projectile runtime crash. DATA-only. ART unchanged.

Root cause:
  1. Crash path Data/INI/Specter/Iraq Army/Iraq-AlAbbas-Projectile.ini is missing
     from the packed DATA (only Object\\...\\Iraq_AlAbbas_Projectile.ini exists).
  2. Dedicated Iraq_AlAbbas_Locomotor lives only in Locomotor_IraqFactoryMissiles.ini
     and is not registered in the always-loaded Locomotor.ini.

Does not change Al-Abbas gameplay stats, MOTHER/9P117, other missiles, flags,
buildings, ART, Fire unlock, or rebuild.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_DATA_ART/_SPEC_DATA_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_PROJECTILE_CRASH"
ALIAS_SRC = ROOT / "patch/Data/INI/Specter/Iraq Army/Iraq-AlAbbas-Projectile.ini"

BASE_DATA_SHA = "d57a6f7451c0032ab774ce352d736715ddea1b20ae6176393a1967bbc659c30c"
BASE_DATA_SIZE = 366473321
PREV_ART_SHA = "e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4"
PREV_ART_SIZE = 1292294758

LOCO_KEY = r"Data\INI\Locomotor.ini"
LOCO_NEW_KEY = r"Data\INI\Locomotor_IraqFactoryMissiles.ini"
ALIAS_KEY = r"Data\INI\Specter\Iraq Army\Iraq-AlAbbas-Projectile.ini"
PROJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlAbbas_Projectile.ini"
UNIT_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
WOBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_WeaponObjects.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
WEP_NEW_KEY = r"Data\INI\Weapon\Weapon_Iraq_FactoryMissiles.ini"
UPG_KEY = r"Data\INI\Upgrade_IraqFactoryMissiles.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"

OTHER_PROJ = [
    r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini",
    r"Data\INI\Object\Specter\Iraq Army\Iraq_AlHusseinII_Projectile.ini",
    r"Data\INI\Object\Specter\Iraq Army\Iraq_AlSamoudII_Projectile.ini",
    r"Data\INI\Object\Specter\Iraq Army\Iraq_AlBasrah_Projectile.ini",
    r"Data\INI\Object\Specter\Iraq Army\Iraq_AlNasir_Projectile.ini",
    r"Data\INI\Object\Specter\Iraq Army\Iraq_AlMansour_Projectile.ini",
]
OTHER_UNITS = [
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini",
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


def locomotor_block(text: str, name: str) -> str | None:
    return command_block(text, "Locomotor", name)


def append_loco(loco_ini: bytes, factory: bytes) -> bytes:
    src_text = factory.decode("utf-8")
    block = locomotor_block(src_text, "Iraq_AlAbbas_Locomotor")
    if not block:
        raise SystemExit("Iraq_AlAbbas_Locomotor missing from factory loco file")
    existing = loco_ini.decode("latin1")
    if locomotor_block(existing, "Iraq_AlAbbas_Locomotor"):
        return loco_ini
    if locomotor_block(existing, "R11SRBMLocomotor") is None:
        raise SystemExit("R11SRBMLocomotor missing from Locomotor.ini")
    suffix = "\r\n\r\n; Factory Al-Abbas dedicated locomotor (registered in Locomotor.ini so fire can resolve it).\r\n"
    suffix += block.replace("\r\n", "\n").replace("\n", "\r\n")
    if not suffix.endswith("\r\n"):
        suffix += "\r\n"
    if loco_ini.endswith(b"\r\n"):
        return loco_ini + suffix.encode("utf-8")
    if loco_ini.endswith(b"\n"):
        return loco_ini + suffix.encode("utf-8")
    return loco_ini + b"\r\n" + suffix.encode("utf-8")


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    protected = [
        R11_KEY, WOBJ_KEY, WEAPON_KEY, WEP_NEW_KEY, UPG_KEY, CB_KEY, CS_KEY,
        FACTORY_KEY, PROJ_KEY, UNIT_KEY, LOCO_NEW_KEY,
    ] + OTHER_PROJ + OTHER_UNITS
    for key in protected:
        if data.get(key) != src.get(key):
            fails.append(f"protected file mutated {key}")

    changed = sorted(k for k in set(data) | set(src) if data.get(k) != src.get(k))
    if set(changed) != {LOCO_KEY, ALIAS_KEY}:
        fails.append(f"unexpected DATA changes {changed}")

    if ALIAS_KEY not in data:
        fails.append("crash-path alias missing")
    alias = data[ALIAS_KEY].decode("utf-8")
    if "Object Projectile_Iraq_AlAbbas" not in alias:
        fails.append("alias missing Projectile_Iraq_AlAbbas")
    if "Model = Irq_AlAbbas2M" not in alias:
        fails.append("alias model")
    if "Locomotor = SET_NORMAL Iraq_AlAbbas_Locomotor" not in alias:
        fails.append("alias locomotor")
    if "DeathWeapon   = Weapon_Iraq_AlAbbas_Warhead" not in alias:
        fails.append("alias warhead")
    if "InitialVelocity = 30" not in alias:
        fails.append("alias InitialVelocity")
    if "R11SRBMLocomotor" in alias:
        fails.append("alias used shared MOTHER locomotor")

    n = len(
        re.findall(
            rb"^Object Projectile_Iraq_AlAbbas\s*$",
            b"".join(v for k, v in data.items() if k.lower().endswith(".ini")),
            re.M,
        )
    )
    if n != 2:
        fails.append(f"Projectile_Iraq_AlAbbas definition count {n}")

    unit = data[UNIT_KEY].decode("utf-8")
    if "BuildTime       = 30.0" not in unit or "BuildCost       = 2600" not in unit:
        fails.append("Al-Abbas unit stats changed")
    if "CommandSet    = Iraq_AlAbbas_TELCommandSet" not in unit:
        fails.append("TEL CommandSet")
    if "ReplaceObject = Iraq_AlAbbas" not in unit:
        fails.append("rebuild")

    loco_ini = data[LOCO_KEY].decode("latin1")
    src_loco = src[LOCO_KEY].decode("latin1")
    if locomotor_block(loco_ini, "R11SRBMLocomotor") != locomotor_block(src_loco, "R11SRBMLocomotor"):
        fails.append("R11SRBMLocomotor mutated")
    if locomotor_block(loco_ini, "AlAbbasMissileLocomotor") != locomotor_block(src_loco, "AlAbbasMissileLocomotor"):
        fails.append("AlAbbasMissileLocomotor mutated")
    block = locomotor_block(loco_ini, "Iraq_AlAbbas_Locomotor") or ""
    if "Speed = 1350" not in block or "Acceleration = 750" not in block:
        fails.append("dedicated loco values")
    if "Appearance = THRUST" not in block or "MinSpeed = 70" not in block:
        fails.append("dedicated loco THRUST/MinSpeed")

    fac = locomotor_block(data[LOCO_NEW_KEY].decode("utf-8"), "Iraq_AlAbbas_Locomotor") or ""
    if "Speed = 1350" not in fac:
        fails.append("factory sidecar loco changed")

    wep = last_weapon_block(data, "Weapon_Iraq_AlAbbas")
    if not wep or "ProjectileObject            = Projectile_Iraq_AlAbbas" not in wep[1]:
        fails.append("Weapon_Iraq_AlAbbas")
    else:
        if "WeaponSpeed                 = 840" not in wep[1] or "AttackRange                 = 2752.0" not in wep[1]:
            fails.append("Al-Abbas weapon stats")
        if "PrimaryDamage               = 6000.0" not in wep[1] or "ScatterRadius               = 70" not in wep[1]:
            fails.append("Al-Abbas damage/accuracy")

    war = last_weapon_block(data, "Weapon_Iraq_AlAbbas_Warhead")
    if not war or "PrimaryDamage           = 6600" not in war[1]:
        fails.append("warhead")

    fire = command_block(data[CB_KEY].decode("latin1"), "CommandButton", "Command_FireMainWeapon") or ""
    if "NEED_SPECIAL_POWER_SCIENCE" in fire or re.search(r"^\s*Science\s*=", fire, re.M):
        fails.append("Fire gated")
    tel = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlAbbas_TELCommandSet") or ""
    slots = slot_map(tel)
    if slots.get(1) != "Command_FireMainWeapon":
        fails.append(f"TEL fire slot {slots}")

    r11 = data[R11_KEY]
    if r11 != src[R11_KEY]:
        fails.append("MOTHER 9P117 mutated")
    if b"Object Iraq_R11ScudB" not in r11 or b"BuildTime       = 17.0" not in r11:
        fails.append("MOTHER object/buildtime")

    zzzz = [k for k in data if "zzzz" in k.lower() and b"AlAbbas" in data[k]]
    if zzzz:
        fails.append(f"ZZZZ {zzzz[:4]}")
    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("live DATA baseline mismatch")
    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)
    if not ALIAS_SRC.is_file():
        raise SystemExit("workspace crash-path alias missing")
    data[ALIAS_KEY] = to_crlf(ALIAS_SRC.read_text(encoding="utf-8"))
    data[LOCO_KEY] = append_loco(src[LOCO_KEY], src[LOCO_NEW_KEY])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    extracted = parse_big(packed)

    stage = OUT / "LAST_WINS_EXTRACT" / "DATA"
    stage.mkdir(parents=True)
    for rel in [ALIAS_KEY, PROJ_KEY, UNIT_KEY, LOCO_NEW_KEY, R11_KEY]:
        p = stage / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])
    loco_stage = stage / "Data/INI/Locomotor.ini.AlAbbas-tail.txt"
    tail = locomotor_block(extracted[LOCO_KEY].decode("latin1"), "Iraq_AlAbbas_Locomotor") or ""
    loco_stage.write_text(tail.replace("\r\n", "\n") + "\n", encoding="utf-8")

    fails = validate(extracted, src)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    data_sha = sha256_path(out_data)
    report = [
        "# SPECTER Iraq Al-Abbas projectile crash fix (DATA-only)",
        "",
        "Crash path: Data/INI/Specter/Iraq Army/Iraq-AlAbbas-Projectile.ini",
        "Root cause: that path was missing; dedicated Iraq_AlAbbas_Locomotor was not in Locomotor.ini.",
        "Fix: add the crash-path alias INI + register Iraq_AlAbbas_Locomotor in Locomotor.ini.",
        "Al-Abbas stats/model/skin/rebuild/Fire/MOTHER/other missiles/ART unchanged.",
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
        "- crash-path alias Data\\INI\\Specter\\Iraq Army\\Iraq-AlAbbas-Projectile.ini present",
        "- Object Projectile_Iraq_AlAbbas still uses Irq_AlAbbas2M + Iraq_AlAbbas_Locomotor + InitialVelocity 30",
        "- Iraq_AlAbbas_Locomotor Speed=1350 Acceleration=750 now in Locomotor.ini",
        "- R11SRBMLocomotor / AlAbbasMissileLocomotor / 9P117 byte-identical",
        "- Al-Abbas BuildTime 30.0 / $2600 / range / damage / accuracy / rebuild / Fire unchanged",
        "- other factory missiles unchanged; ART not rebuilt",
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
        f"ART_SIZE={PREV_ART_SIZE}\n"
        "OBJECT=Projectile_Iraq_AlAbbas\n"
        "CRASH_PATH=Data/INI/Specter/Iraq Army/Iraq-AlAbbas-Projectile.ini\n"
        "LOCO=Iraq_AlAbbas_Locomotor registered in Locomotor.ini\n"
        "STATS_UNCHANGED=YES\n"
        "MOTHER_UNCHANGED=YES\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT PERFORMED\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq Al-Abbas projectile crash fix (DATA-only)\n"
        "Place this complete replacement DATA BIG in the game folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "Keep the previous complete ART BIG. ART was not rebuilt.\n",
        encoding="utf-8",
    )
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
