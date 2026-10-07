#!/usr/bin/env python3
"""Register SPECTER crash-path aliases + dedicated locos for all factory missiles.

DATA-only. ART unchanged. No gameplay stat edits.

Live DATA: SPECTER_IRAQ_ALABBAS_PROJECTILE_CRASH
Al-Abbas already has its alias + Locomotor.ini registration.
This pass adds the same pattern for A/B/C/H/I/J and registers remaining locos.

Does not implement E/F/G/K/L. Does not modify MOTHER/9P117/R11SRBMLocomotor.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_PROJECTILE_CRASH/_SPEC_DATA_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_PROJECTILE_PATHS"
ALIAS_DIR = ROOT / "patch/Data/INI/Specter/Iraq Army"

BASE_DATA_SHA = "2d7d72b46b663189b0d261fe986ec672f46f63279418ae4292d0dac9e662146e"
BASE_DATA_SIZE = 366476915
PREV_ART_SHA = "e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4"
PREV_ART_SIZE = 1292294758

LOCO_KEY = r"Data\INI\Locomotor.ini"
LOCO_NEW_KEY = r"Data\INI\Locomotor_IraqFactoryMissiles.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
WOBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_WeaponObjects.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
WEP_NEW_KEY = r"Data\INI\Weapon\Weapon_Iraq_FactoryMissiles.ini"
WEP_A_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlFahd500.ini"
UPG_KEY = r"Data\INI\Upgrade_IraqFactoryMissiles.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
UNIT_D_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini"
ABBAS_ALIAS = r"Data\INI\Specter\Iraq Army\Iraq-AlAbbas-Projectile.ini"

IMPLEMENTED = [
    {
        "slot": "A",
        "object": "Iraq_AlFahd500",
        "proj": "Projectile_Iraq_AlFahd500",
        "loco": "Iraq_AlFahd500_Locomotor",
        "weapon": "Weapon_Iraq_AlFahd500",
        "warhead": "Weapon_Iraq_AlFahd500_Warhead",
        "model": "Irq_AlFahd500M",
        "tex": "Irq_AlFahd500P.tga",
        "init": "40",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini",
        "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini",
        "alias": "Iraq-AlFahd500-Projectile.ini",
        "existing_alias": False,
    },
    {
        "slot": "B",
        "object": "Iraq_AlHusseinII",
        "proj": "Projectile_Iraq_AlHusseinII",
        "loco": "Iraq_AlHusseinII_Locomotor",
        "weapon": "Weapon_Iraq_AlHusseinII",
        "warhead": "Weapon_Iraq_AlHusseinII_Warhead",
        "model": "Irq_AlHussein2M",
        "tex": "Irq_AlHussein2P.tga",
        "init": "20",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlHusseinII_Projectile.ini",
        "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHusseinII.ini",
        "alias": "Iraq-AlHusseinII-Projectile.ini",
        "existing_alias": False,
    },
    {
        "slot": "C",
        "object": "Iraq_AlSamoudII",
        "proj": "Projectile_Iraq_AlSamoudII",
        "loco": "Iraq_AlSamoudII_Locomotor",
        "weapon": "Weapon_Iraq_AlSamoudII",
        "warhead": "Weapon_Iraq_AlSamoudII_Warhead",
        "model": "Irq_AlSamoud2M",
        "tex": "Irq_AlSamoud2P.tga",
        "init": "60",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlSamoudII_Projectile.ini",
        "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlSamoudII.ini",
        "alias": "Iraq-AlSamoudII-Projectile.ini",
        "existing_alias": False,
    },
    {
        "slot": "D",
        "object": "Iraq_AlAbbas",
        "proj": "Projectile_Iraq_AlAbbas",
        "loco": "Iraq_AlAbbas_Locomotor",
        "weapon": "Weapon_Iraq_AlAbbas",
        "warhead": "Weapon_Iraq_AlAbbas_Warhead",
        "model": "Irq_AlAbbas2M",
        "tex": "Irq_AlAbbas2P.tga",
        "init": "30",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlAbbas_Projectile.ini",
        "unit_key": UNIT_D_KEY,
        "alias": "Iraq-AlAbbas-Projectile.ini",
        "existing_alias": True,
    },
    {
        "slot": "H",
        "object": "Iraq_AlBasrah",
        "proj": "Projectile_Iraq_AlBasrah",
        "loco": "Iraq_AlBasrah_Locomotor",
        "weapon": "Weapon_Iraq_AlBasrah",
        "warhead": "Weapon_Iraq_AlBasrah_Warhead",
        "model": "Irq_AlBasrahM",
        "tex": "Irq_AlBasrahP.tga",
        "init": "120",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlBasrah_Projectile.ini",
        "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlBasrah.ini",
        "alias": "Iraq-AlBasrah-Projectile.ini",
        "existing_alias": False,
    },
    {
        "slot": "I",
        "object": "Iraq_AlNasir",
        "proj": "Projectile_Iraq_AlNasir",
        "loco": "Iraq_AlNasir_Locomotor",
        "weapon": "Weapon_Iraq_AlNasir",
        "warhead": "Weapon_Iraq_AlNasir_Warhead",
        "model": "Irq_AlNasirM",
        "tex": "Irq_AlNasirP.tga",
        "init": "140",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlNasir_Projectile.ini",
        "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNasir.ini",
        "alias": "Iraq-AlNasir-Projectile.ini",
        "existing_alias": False,
    },
    {
        "slot": "J",
        "object": "Iraq_AlMansour",
        "proj": "Projectile_Iraq_AlMansour",
        "loco": "Iraq_AlMansour_Locomotor",
        "weapon": "Weapon_Iraq_AlMansour",
        "warhead": "Weapon_Iraq_AlMansour_Warhead",
        "model": "Irq_AlMansourM",
        "tex": "Irq_AlMansourP.tga",
        "init": "170",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlMansour_Projectile.ini",
        "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlMansour.ini",
        "alias": "Iraq-AlMansour-Projectile.ini",
        "existing_alias": False,
    },
]

UNIMPLEMENTED = ["E", "F", "G", "K", "L"]


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


def append_missing_locos(loco_ini: bytes, factory: bytes) -> bytes:
    src_text = factory.decode("utf-8")
    existing = loco_ini.decode("latin1")
    if locomotor_block(existing, "R11SRBMLocomotor") is None:
        raise SystemExit("R11SRBMLocomotor missing")
    added = []
    suffix_parts = []
    for item in IMPLEMENTED:
        name = item["loco"]
        if locomotor_block(existing, name):
            continue
        block = locomotor_block(src_text, name)
        if not block:
            raise SystemExit(f"{name} missing from sidecar")
        added.append(name)
        suffix_parts.append(block.replace("\r\n", "\n").replace("\n", "\r\n"))
    if not added:
        return loco_ini
    suffix = "\r\n\r\n; Factory dedicated locomotors registered in Locomotor.ini so fire can resolve them.\r\n"
    suffix += "\r\n\r\n".join(suffix_parts)
    if not suffix.endswith("\r\n"):
        suffix += "\r\n"
    out = loco_ini
    if not out.endswith(b"\n"):
        out += b"\r\n"
    return out + suffix.encode("utf-8")


def alias_key(name: str) -> str:
    return rf"Data\INI\Specter\Iraq Army\{name}"


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    protected = [R11_KEY, WOBJ_KEY, WEAPON_KEY, WEP_NEW_KEY, WEP_A_KEY, UPG_KEY, CB_KEY, CS_KEY, FACTORY_KEY, LOCO_NEW_KEY, ABBAS_ALIAS]
    for item in IMPLEMENTED:
        protected.append(item["obj_key"])
        protected.append(item["unit_key"])
    for key in protected:
        if data.get(key) != src.get(key):
            fails.append(f"protected file mutated {key}")

    new_alias_keys = {alias_key(i["alias"]) for i in IMPLEMENTED if not i["existing_alias"]}
    changed = sorted(k for k in set(data) | set(src) if data.get(k) != src.get(k))
    if set(changed) != new_alias_keys | {LOCO_KEY}:
        fails.append(f"unexpected DATA changes {changed}")

    for item in IMPLEMENTED:
        akey = alias_key(item["alias"])
        if akey not in data:
            fails.append(f"missing alias {akey}")
            continue
        alias = data[akey].decode("utf-8")
        if f"Object {item['proj']}" not in alias:
            fails.append(f"alias object {item['slot']}")
        if f"Model = {item['model']}" not in alias:
            fails.append(f"alias model {item['slot']}")
        if f"Locomotor = SET_NORMAL {item['loco']}" not in alias:
            fails.append(f"alias loco {item['slot']}")
        if f"DeathWeapon   = {item['warhead']}" not in alias:
            fails.append(f"alias warhead {item['slot']}")
        if f"InitialVelocity = {item['init']}" not in alias:
            fails.append(f"alias init {item['slot']}")
        if "R11SRBMLocomotor" in alias:
            fails.append(f"alias used MOTHER loco {item['slot']}")

        n = len(
            re.findall(
                rf"^Object {re.escape(item['proj'])}\s*$".encode(),
                b"".join(v for k, v in data.items() if k.lower().endswith(".ini")),
                re.M,
            )
        )
        if n != 2:
            fails.append(f"{item['proj']} definition count {n}")

        wep = last_weapon_block(data, item["weapon"])
        if not wep or f"ProjectileObject            = {item['proj']}" not in wep[1]:
            fails.append(f"weapon {item['weapon']}")
        war = last_weapon_block(data, item["warhead"])
        if not war:
            fails.append(f"warhead {item['warhead']}")

        loco_ini = data[LOCO_KEY].decode("latin1")
        sidecar = data[LOCO_NEW_KEY].decode("utf-8")
        if not locomotor_block(loco_ini, item["loco"]):
            fails.append(f"loco not in Locomotor.ini {item['loco']}")
        if not locomotor_block(sidecar, item["loco"]):
            fails.append(f"loco missing from sidecar {item['loco']}")

    loco_ini = data[LOCO_KEY].decode("latin1")
    src_loco = src[LOCO_KEY].decode("latin1")
    if locomotor_block(loco_ini, "R11SRBMLocomotor") != locomotor_block(src_loco, "R11SRBMLocomotor"):
        fails.append("R11SRBMLocomotor mutated")
    if locomotor_block(loco_ini, "AlAbbasMissileLocomotor") != locomotor_block(src_loco, "AlAbbasMissileLocomotor"):
        fails.append("AlAbbasMissileLocomotor mutated")

    unit = data[UNIT_D_KEY].decode("utf-8")
    if "BuildTime       = 30.0" not in unit or "BuildCost       = 2600" not in unit:
        fails.append("Al-Abbas stats")
    fire = command_block(data[CB_KEY].decode("latin1"), "CommandButton", "Command_FireMainWeapon") or ""
    if "NEED_SPECIAL_POWER_SCIENCE" in fire or re.search(r"^\s*Science\s*=", fire, re.M):
        fails.append("Fire gated")
    tel = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlAbbas_TELCommandSet") or ""
    if slot_map(tel).get(1) != "Command_FireMainWeapon":
        fails.append("Al-Abbas Fire slot")

    fac = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet") or ""
    fslots = slot_map(fac)
    if fslots.get(1) != "CB_MISSILE_A" or fslots.get(8) != "CB_MISSILE_H":
        fails.append(f"factory slots {fslots}")
    for empty in (5, 6, 7, 11, 12):
        if empty in fslots:
            fails.append(f"unwired slot filled {empty}")

    for banned in ("Iraq_AlTammuz", "Iraq_AlQuds", "Iraq_Ababil100", "Projectile_Iraq_AlTammuz"):
        n = len(re.findall(rf"^Object {banned}\s*$".encode(), b"".join(data.values()), re.M))
        if n:
            fails.append(f"invented unimplemented object {banned}")

    if data[R11_KEY] != src[R11_KEY] or b"Object Iraq_R11ScudB" not in data[R11_KEY]:
        fails.append("MOTHER 9P117 mutated")

    zzzz_new = [k for k in data if "zzzz" in k.lower() and k not in src]
    if zzzz_new:
        fails.append(f"ZZZZ added {zzzz_new[:4]}")
    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("live DATA baseline mismatch")
    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)
    for item in IMPLEMENTED:
        if item["existing_alias"]:
            continue
        src_path = ALIAS_DIR / item["alias"]
        if not src_path.is_file():
            raise SystemExit(f"missing workspace alias {item['alias']}")
        data[alias_key(item["alias"])] = to_crlf(src_path.read_text(encoding="utf-8"))
    data[LOCO_KEY] = append_missing_locos(src[LOCO_KEY], src[LOCO_NEW_KEY])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    extracted = parse_big(packed)

    stage = OUT / "LAST_WINS_EXTRACT" / "DATA"
    stage.mkdir(parents=True)
    extract_keys = [R11_KEY, UNIT_D_KEY, LOCO_NEW_KEY] + [alias_key(i["alias"]) for i in IMPLEMENTED] + [i["obj_key"] for i in IMPLEMENTED]
    for rel in extract_keys:
        p = stage / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])
    loco_ini = extracted[LOCO_KEY].decode("latin1")
    tails = []
    for item in IMPLEMENTED:
        tails.append(locomotor_block(loco_ini, item["loco"]) or f"MISSING {item['loco']}")
    (stage / "Data/INI/Locomotor.ini.factory-locos.txt").write_text(
        "\n\n".join(t.replace("\r\n", "\n") for t in tails) + "\n", encoding="utf-8"
    )

    fails = validate(extracted, src)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    data_sha = sha256_path(out_data)
    report = [
        "# SPECTER Iraq factory missile projectile crash-path family fix (DATA-only)",
        "",
        "Same structural crash as Al-Abbas: SPECTER opens Data/INI/Specter/Iraq Army/Iraq-<Name>-Projectile.ini",
        "while the live definition only existed under Data/INI/Object/Specter/Iraq Army/.",
        "Dedicated locos were sidecar-only except Al-Abbas. Register all seven in Locomotor.ini.",
        "E/F/G/K/L remain unimplemented. No gameplay stats changed. ART not rebuilt.",
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
        "- aliases for A/B/C/D/H/I/J present under Data\\INI\\Specter\\Iraq Army\\",
        "- all seven dedicated locos registered in Locomotor.ini; sidecar unchanged",
        "- R11SRBMLocomotor / AlAbbasMissileLocomotor / 9P117 byte-identical",
        "- Al-Abbas BuildTime 30.0 / Fire unlocked / rebuild unchanged",
        "- E/F/G/K/L not invented; factory slots 5-7/11-12 still empty",
        "- ART not rebuilt",
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
        "ALIASES=A,B,C,D,H,I,J\n"
        "UNIMPLEMENTED=E,F,G,K,L\n"
        "LOCOS_IN_LOCOMOTOR_INI=ALL_SEVEN\n"
        "MOTHER_UNCHANGED=YES\n"
        "ALABBAS_BUILDTIME=30.0\n"
        "ALABBAS_FIRE=UNLOCKED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT PERFORMED\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq factory missile projectile crash-path family fix (DATA-only)\n"
        "Place this complete replacement DATA BIG in the game folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "Keep the previous complete ART BIG. ART was not rebuilt.\n",
        encoding="utf-8",
    )
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
