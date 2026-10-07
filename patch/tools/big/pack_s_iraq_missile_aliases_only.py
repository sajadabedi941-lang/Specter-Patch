#!/usr/bin/env python3
"""DATA-only: #578 + six SPECTER projectile aliases. No Locomotor.ini append.

Isolation proved appending all six dedicated locos to Locomotor.ini (522 defs /
667166 bytes) reproduces the #579 silent exit. Those locos already live in
Locomotor_IraqFactoryMissiles.ini. This pack keeps Locomotor.ini byte-identical
to #578 (516 defs / 664015 bytes, Al-Abbas registration only).

Does not modify MOTHER/9P117, construction, VT-72B, stats, CommandSets, ART.
Does not invent E/F/G/K/L objects.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_PROJECTILE_CRASH/_SPEC_DATA_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_ALIASES_ONLY"
ALIAS_DIR = ROOT / "patch/Data/INI/Specter/Iraq Army"

BASE_DATA_SHA = "2d7d72b46b663189b0d261fe986ec672f46f63279418ae4292d0dac9e662146e"
BASE_DATA_SIZE = 366476915
PREV_ART_SHA = "e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4"
PREV_ART_SIZE = 1292294758
EXPECTED_LOCO_DEFS = 516
EXPECTED_LOCO_SIZE = 664015

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
VT72B_KEY = r"Data\INI\Object\Specter\Iraq Army\Tracked\VT72B.ini"
WF_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory.ini"
RADAR_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_RadarStation.ini"
PT_KEY = r"Data\INI\PlayerTemplate.ini"

FORBIDDEN_LOCOS = [
    "Iraq_AlFahd500_Locomotor",
    "Iraq_AlHusseinII_Locomotor",
    "Iraq_AlSamoudII_Locomotor",
    "Iraq_AlBasrah_Locomotor",
    "Iraq_AlNasir_Locomotor",
    "Iraq_AlMansour_Locomotor",
]

IMPLEMENTED = [
    {
        "slot": "A",
        "object": "Iraq_AlFahd500",
        "proj": "Projectile_Iraq_AlFahd500",
        "loco": "Iraq_AlFahd500_Locomotor",
        "weapon": "Weapon_Iraq_AlFahd500",
        "warhead": "Weapon_Iraq_AlFahd500_Warhead",
        "model": "Irq_AlFahd500M",
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
        "init": "170",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlMansour_Projectile.ini",
        "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlMansour.ini",
        "alias": "Iraq-AlMansour-Projectile.ini",
        "existing_alias": False,
    },
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


def alias_key(name: str) -> str:
    return rf"Data\INI\Specter\Iraq Army\{name}"


def obj_body(text: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^Object {re.escape(name)}\r?\n.*?^End\s*$", text)
    return m.group(0).replace("\r\n", "\n").strip() if m else None


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    protected = [
        R11_KEY,
        WOBJ_KEY,
        WEAPON_KEY,
        WEP_NEW_KEY,
        WEP_A_KEY,
        UPG_KEY,
        CB_KEY,
        CS_KEY,
        FACTORY_KEY,
        LOCO_KEY,
        LOCO_NEW_KEY,
        ABBAS_ALIAS,
        UNIT_D_KEY,
        VT72B_KEY,
        WF_KEY,
        RADAR_KEY,
        PT_KEY,
    ]
    for item in IMPLEMENTED:
        protected.append(item["obj_key"])
        protected.append(item["unit_key"])
    for key in protected:
        if data.get(key) != src.get(key):
            fails.append(f"protected file mutated {key}")

    new_alias_keys = {alias_key(i["alias"]) for i in IMPLEMENTED if not i["existing_alias"]}
    changed = sorted(k for k in set(data) | set(src) if data.get(k) != src.get(k))
    if set(changed) != new_alias_keys:
        fails.append(f"unexpected DATA changes {changed}")

    if data[LOCO_KEY] != src[LOCO_KEY]:
        fails.append("Locomotor.ini not byte-identical to #578")
    loco_ini = data[LOCO_KEY].decode("latin1")
    n_loco = len(re.findall(r"^Locomotor ", loco_ini, re.M))
    if n_loco != EXPECTED_LOCO_DEFS:
        fails.append(f"Locomotor.ini def count {n_loco} != {EXPECTED_LOCO_DEFS}")
    if len(data[LOCO_KEY]) != EXPECTED_LOCO_SIZE:
        fails.append(f"Locomotor.ini size {len(data[LOCO_KEY])} != {EXPECTED_LOCO_SIZE}")
    if locomotor_block(loco_ini, "Iraq_AlAbbas_Locomotor") is None:
        fails.append("Al-Abbas loco missing from Locomotor.ini")
    for name in FORBIDDEN_LOCOS:
        if locomotor_block(loco_ini, name):
            fails.append(f"forbidden loco in Locomotor.ini {name}")

    sidecar = data[LOCO_NEW_KEY].decode("utf-8")
    if not locomotor_block(sidecar, "Iraq_AlAbbas_Locomotor"):
        fails.append("Al-Abbas loco missing from sidecar")
    for name in FORBIDDEN_LOCOS:
        if not locomotor_block(sidecar, name):
            fails.append(f"loco missing from sidecar {name}")

    if locomotor_block(loco_ini, "R11SRBMLocomotor") != locomotor_block(src[LOCO_KEY].decode("latin1"), "R11SRBMLocomotor"):
        fails.append("R11SRBMLocomotor mutated")

    for item in IMPLEMENTED:
        akey = alias_key(item["alias"])
        if akey not in data:
            fails.append(f"missing alias {akey}")
            continue
        alias = data[akey].decode("utf-8")
        extras = re.findall(r"^Object (\S+)", alias, re.M)
        if extras != [item["proj"]]:
            fails.append(f"alias objects {item['slot']} {extras}")
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
        live = data[item["obj_key"]].decode("utf-8")
        if obj_body(alias, item["proj"]) != obj_body(live, item["proj"]):
            fails.append(f"alias body != Object-path {item['slot']}")

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
        raise SystemExit("live DATA baseline mismatch — need exact #578 BIG")
    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)
    for item in IMPLEMENTED:
        if item["existing_alias"]:
            continue
        src_path = ALIAS_DIR / item["alias"]
        if not src_path.is_file():
            raise SystemExit(f"missing workspace alias {item['alias']}")
        data[alias_key(item["alias"])] = to_crlf(src_path.read_text(encoding="utf-8"))
    if data[LOCO_KEY] != src[LOCO_KEY]:
        raise SystemExit("packer mutated Locomotor.ini")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    extracted = parse_big(packed)

    stage = OUT / "LAST_WINS_EXTRACT" / "DATA"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    extract_keys = [
        R11_KEY,
        UNIT_D_KEY,
        LOCO_KEY,
        LOCO_NEW_KEY,
        VT72B_KEY,
        FACTORY_KEY,
        WF_KEY,
        RADAR_KEY,
    ] + [alias_key(i["alias"]) for i in IMPLEMENTED] + [i["obj_key"] for i in IMPLEMENTED]
    for rel in extract_keys:
        p = stage / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])

    fails = validate(extracted, src)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    data_sha = sha256_path(out_data)
    loco_n = len(re.findall(r"^Locomotor ", extracted[LOCO_KEY].decode("latin1"), re.M))
    report = [
        "# SPECTER Iraq factory missile SPECTER-path aliases only (DATA-only)",
        "",
        "Based on PR #578 DATA. Adds six SPECTER crash-path aliases.",
        "Does NOT append the six dedicated locomotors to Locomotor.ini.",
        "Those locos remain only in Locomotor_IraqFactoryMissiles.ini.",
        "Al-Abbas Locomotor.ini registration unchanged from #578.",
        "E/F/G/K/L remain unimplemented. No gameplay stats changed. ART not rebuilt.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- Locomotor.ini defs: {loco_n}",
        f"- Locomotor.ini bytes: {len(extracted[LOCO_KEY])}",
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
        "- six aliases A/B/C/H/I/J added under Data\\INI\\Specter\\Iraq Army\\",
        "- Al-Abbas alias unchanged from #578",
        "- Locomotor.ini byte-identical to #578 (516 defs, Al-Abbas only extra)",
        "- six dedicated locos present in sidecar only; not in Locomotor.ini",
        "- R11SRBMLocomotor / 9P117 / construction files byte-identical",
        "- Al-Abbas BuildTime 30.0 / Fire unlocked / rebuild unchanged",
        "- E/F/G/K/L not invented; factory slots 5-7/11-12 still empty",
        "- ART not rebuilt",
        "- packed DATA re-extracted and last-wins/duplicate audited",
        "",
        "RUNTIME TEST: PENDING",
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
        f"LOCOMOTOR_INI_DEFS={loco_n}\n"
        f"LOCOMOTOR_INI_BYTES={len(extracted[LOCO_KEY])}\n"
        "LOCOMOTOR_INI_IDENTICAL_TO_578=YES\n"
        "SIX_LOCOS_IN_LOCOMOTOR_INI=NO\n"
        "SIX_LOCOS_IN_SIDECAR=YES\n"
        f"ART_SHA256={PREV_ART_SHA}\n"
        f"ART_SIZE={PREV_ART_SIZE}\n"
        "ALIASES=A,B,C,D,H,I,J\n"
        "UNIMPLEMENTED=E,F,G,K,L\n"
        "MOTHER_UNCHANGED=YES\n"
        "ALABBAS_BUILDTIME=30.0\n"
        "ALABBAS_FIRE=UNLOCKED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=PENDING\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq factory missile SPECTER-path aliases only (DATA-only)\n"
        "Based on PR #578. Adds six projectile aliases. Does NOT register the\n"
        "six dedicated locomotors in Locomotor.ini.\n"
        "Place this complete replacement DATA BIG in the game folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "Keep the previous complete ART BIG. ART was not rebuilt.\n",
        encoding="utf-8",
    )
    (OUT / "AUDIT.txt").write_text(
        "Isolation: six Locomotor.ini appends (522 defs) caused silent exit.\n"
        "This pack = #578 + six Specter aliases only.\n"
        "Locomotor.ini 516 defs / 664015 bytes, byte-identical to #578.\n"
        "Sidecar still has all seven dedicated factory locos.\n"
        "No construction / VT-72B / MOTHER / stats / ART changes.\n",
        encoding="utf-8",
    )
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
