#!/usr/bin/env python3
"""DATA-only: #578 + register six existing factory locos in Locomotor.ini.

Root cause: Object parse reads locomotors from Locomotor.ini only.
Al-Abbas already registered there. The other six dedicated locos lived only
in Locomotor_IraqFactoryMissiles.ini, so Windows crashed on Al-Basrah.

Does not add hyphenated Data\\INI\\Specter\\Iraq Army\\ files.
Does not modify sidecar, Objects, weapons, construction, MOTHER, or ART.
Does not invent E/F/G/K/L. Does not change loco values.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_PROJECTILE_CRASH/_SPEC_DATA_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_LOCO_REGISTER"

BASE_DATA_SHA = "2d7d72b46b663189b0d261fe986ec672f46f63279418ae4292d0dac9e662146e"
BASE_DATA_SIZE = 366476915
PREV_ART_SHA = "e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4"
PREV_ART_SIZE = 1292294758
EXPECTED_LOCO_DEFS = 522
BASE_LOCO_DEFS = 516
BASE_LOCO_SIZE = 664015

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

REGISTER = [
    "Iraq_AlFahd500_Locomotor",
    "Iraq_AlHusseinII_Locomotor",
    "Iraq_AlSamoudII_Locomotor",
    "Iraq_AlBasrah_Locomotor",
    "Iraq_AlNasir_Locomotor",
    "Iraq_AlMansour_Locomotor",
]

FORBIDDEN_HYPHEN = [
    r"Data\INI\Specter\Iraq Army\Iraq-AlFahd500-Projectile.ini",
    r"Data\INI\Specter\Iraq Army\Iraq-AlHusseinII-Projectile.ini",
    r"Data\INI\Specter\Iraq Army\Iraq-AlSamoudII-Projectile.ini",
    r"Data\INI\Specter\Iraq Army\Iraq-AlBasrah-Projectile.ini",
    r"Data\INI\Specter\Iraq Army\Iraq-AlNasir-Projectile.ini",
    r"Data\INI\Specter\Iraq Army\Iraq-AlMansour-Projectile.ini",
]

IMPLEMENTED = [
    {
        "slot": "A",
        "object": "Iraq_AlFahd500",
        "proj": "Projectile_Iraq_AlFahd500",
        "loco": "Iraq_AlFahd500_Locomotor",
        "weapon": "Weapon_Iraq_AlFahd500",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini",
        "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini",
    },
    {
        "slot": "B",
        "object": "Iraq_AlHusseinII",
        "proj": "Projectile_Iraq_AlHusseinII",
        "loco": "Iraq_AlHusseinII_Locomotor",
        "weapon": "Weapon_Iraq_AlHusseinII",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlHusseinII_Projectile.ini",
        "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHusseinII.ini",
    },
    {
        "slot": "C",
        "object": "Iraq_AlSamoudII",
        "proj": "Projectile_Iraq_AlSamoudII",
        "loco": "Iraq_AlSamoudII_Locomotor",
        "weapon": "Weapon_Iraq_AlSamoudII",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlSamoudII_Projectile.ini",
        "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlSamoudII.ini",
    },
    {
        "slot": "D",
        "object": "Iraq_AlAbbas",
        "proj": "Projectile_Iraq_AlAbbas",
        "loco": "Iraq_AlAbbas_Locomotor",
        "weapon": "Weapon_Iraq_AlAbbas",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlAbbas_Projectile.ini",
        "unit_key": UNIT_D_KEY,
    },
    {
        "slot": "H",
        "object": "Iraq_AlBasrah",
        "proj": "Projectile_Iraq_AlBasrah",
        "loco": "Iraq_AlBasrah_Locomotor",
        "weapon": "Weapon_Iraq_AlBasrah",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlBasrah_Projectile.ini",
        "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlBasrah.ini",
    },
    {
        "slot": "I",
        "object": "Iraq_AlNasir",
        "proj": "Projectile_Iraq_AlNasir",
        "loco": "Iraq_AlNasir_Locomotor",
        "weapon": "Weapon_Iraq_AlNasir",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlNasir_Projectile.ini",
        "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNasir.ini",
    },
    {
        "slot": "J",
        "object": "Iraq_AlMansour",
        "proj": "Projectile_Iraq_AlMansour",
        "loco": "Iraq_AlMansour_Locomotor",
        "weapon": "Weapon_Iraq_AlMansour",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlMansour_Projectile.ini",
        "unit_key": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlMansour.ini",
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


def command_block(text: str, kind: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text)
    return m.group(0) if m else None


def locomotor_block(text: str, name: str) -> str | None:
    return command_block(text, "Locomotor", name)


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


def normalize_block(block: str) -> str:
    return block.replace("\r\n", "\n").strip()


def append_missing_locos(loco_ini: bytes, factory: bytes) -> bytes:
    src_text = factory.decode("utf-8")
    existing = loco_ini.decode("latin1")
    if locomotor_block(existing, "R11SRBMLocomotor") is None:
        raise SystemExit("R11SRBMLocomotor missing")
    if locomotor_block(existing, "Iraq_AlAbbas_Locomotor") is None:
        raise SystemExit("Iraq_AlAbbas_Locomotor missing from #578 Locomotor.ini")
    added = []
    suffix_parts = []
    for name in REGISTER:
        if locomotor_block(existing, name):
            raise SystemExit(f"{name} already in Locomotor.ini — not #578 baseline")
        block = locomotor_block(src_text, name)
        if not block:
            raise SystemExit(f"{name} missing from sidecar")
        added.append(name)
        suffix_parts.append(block.replace("\r\n", "\n").replace("\n", "\r\n"))
    if added != REGISTER:
        raise SystemExit(f"register order {added}")
    suffix = (
        "\r\n\r\n; Factory dedicated locomotors registered in Locomotor.ini "
        "so Object parse can resolve them.\r\n"
    )
    suffix += "\r\n\r\n".join(suffix_parts)
    if not suffix.endswith("\r\n"):
        suffix += "\r\n"
    out = loco_ini
    if not out.endswith(b"\n"):
        out += b"\r\n"
    return out + suffix.encode("utf-8")


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

    changed = sorted(k for k in set(data) | set(src) if data.get(k) != src.get(k))
    if set(changed) != {LOCO_KEY}:
        fails.append(f"unexpected DATA changes {changed}")

    for key in FORBIDDEN_HYPHEN:
        if key in data:
            fails.append(f"hyphenated Specter file present {key}")

    hyphenated = [
        k
        for k in data
        if k.replace("/", "\\").lower().startswith("data\\ini\\specter\\iraq army\\")
        and "-" in Path(k.replace("\\", "/")).name
    ]
    if hyphenated != [ABBAS_ALIAS]:
        fails.append(f"unexpected Specter-path files {hyphenated}")

    loco_ini = data[LOCO_KEY].decode("latin1")
    src_loco = src[LOCO_KEY].decode("latin1")
    n_loco = len(re.findall(r"^Locomotor ", loco_ini, re.M))
    if n_loco != EXPECTED_LOCO_DEFS:
        fails.append(f"Locomotor.ini def count {n_loco} != {EXPECTED_LOCO_DEFS}")
    src_n = len(re.findall(r"^Locomotor ", src_loco, re.M))
    if src_n != BASE_LOCO_DEFS:
        fails.append(f"#578 Locomotor.ini def count {src_n} != {BASE_LOCO_DEFS}")
    if len(src[LOCO_KEY]) != BASE_LOCO_SIZE:
        fails.append(f"#578 Locomotor.ini size {len(src[LOCO_KEY])} != {BASE_LOCO_SIZE}")

    names = re.findall(r"^Locomotor (\S+)", loco_ini, re.M)
    if len(names) != len(set(names)):
        fails.append("duplicate locomotor names in Locomotor.ini")

    abbas_new = locomotor_block(loco_ini, "Iraq_AlAbbas_Locomotor")
    abbas_old = locomotor_block(src_loco, "Iraq_AlAbbas_Locomotor")
    if not abbas_new or normalize_block(abbas_new) != normalize_block(abbas_old or ""):
        fails.append("Iraq_AlAbbas_Locomotor mutated")

    r11_new = locomotor_block(loco_ini, "R11SRBMLocomotor")
    r11_old = locomotor_block(src_loco, "R11SRBMLocomotor")
    if r11_new != r11_old:
        fails.append("R11SRBMLocomotor mutated")

    sidecar = data[LOCO_NEW_KEY].decode("utf-8")
    if data[LOCO_NEW_KEY] != src[LOCO_NEW_KEY]:
        fails.append("sidecar mutated")
    if not locomotor_block(sidecar, "Iraq_AlAbbas_Locomotor"):
        fails.append("Al-Abbas loco missing from sidecar")
    for name in REGISTER:
        side = locomotor_block(sidecar, name)
        live = locomotor_block(loco_ini, name)
        if not side:
            fails.append(f"loco missing from sidecar {name}")
        if not live:
            fails.append(f"loco missing from Locomotor.ini {name}")
        if side and live and normalize_block(side) != normalize_block(live):
            fails.append(f"Locomotor.ini block != sidecar {name}")

    for item in IMPLEMENTED:
        if item["obj_key"] not in data:
            fails.append(f"missing Object-path {item['obj_key']}")
            continue
        obj = data[item["obj_key"]].decode("utf-8")
        extras = re.findall(r"^Object (\S+)", obj, re.M)
        if extras != [item["proj"]]:
            fails.append(f"object names {item['slot']} {extras}")
        if f"Locomotor = SET_NORMAL {item['loco']}" not in obj:
            fails.append(f"object loco {item['slot']}")
        n = len(
            re.findall(
                rf"^Object {re.escape(item['proj'])}\s*$".encode(),
                b"".join(v for k, v in data.items() if k.lower().endswith(".ini")),
                re.M,
            )
        )
        expected_n = 2 if item["slot"] == "D" else 1
        if n != expected_n:
            fails.append(f"{item['proj']} definition count {n} != {expected_n}")
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
    data[LOCO_KEY] = append_missing_locos(src[LOCO_KEY], src[LOCO_NEW_KEY])
    if data[LOCO_NEW_KEY] != src[LOCO_NEW_KEY]:
        raise SystemExit("packer mutated sidecar")
    for key in FORBIDDEN_HYPHEN:
        if key in data:
            raise SystemExit(f"packer kept hyphenated file {key}")

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
        LOCO_NEW_KEY,
        VT72B_KEY,
        FACTORY_KEY,
        WF_KEY,
        RADAR_KEY,
        ABBAS_ALIAS,
    ] + [i["obj_key"] for i in IMPLEMENTED]
    for rel in extract_keys:
        p = stage / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])

    loco_text = extracted[LOCO_KEY].decode("latin1")
    sidecar = extracted[LOCO_NEW_KEY].decode("utf-8")
    tail_lines = [
        f"Locomotor.ini defs={len(re.findall(r'^Locomotor ', loco_text, re.M))} bytes={len(extracted[LOCO_KEY])}",
        "ALABBAS_UNCHANGED=YES",
        "SIDECAR_UNCHANGED=YES",
        "REGISTERED_FROM_SIDECAR:",
    ]
    for name in ["Iraq_AlAbbas_Locomotor", *REGISTER]:
        live = locomotor_block(loco_text, name)
        side = locomotor_block(sidecar, name)
        match = "YES" if live and side and normalize_block(live) == normalize_block(side) else "NO"
        tail_lines.append(f"  {name} sidecar_match={match}")
        tail_lines.append("")
        tail_lines.append(live or f"MISSING {name}")
        tail_lines.append("")
    (stage / "Data/INI/Locomotor.ini.factory-locos.txt").write_text("\n".join(tail_lines) + "\n", encoding="utf-8")

    fails = validate(extracted, src)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    data_sha = sha256_path(out_data)
    loco_n = len(re.findall(r"^Locomotor ", extracted[LOCO_KEY].decode("latin1"), re.M))
    report = [
        "# SPECTER Iraq factory missile Locomotor.ini registration (DATA-only)",
        "",
        "Based on exact PR #578 DATA.",
        "Registers the six existing dedicated factory locos in Locomotor.ini.",
        "Does NOT add hyphenated Data\\INI\\Specter\\Iraq Army\\ duplicates.",
        "Al-Abbas Locomotor.ini registration unchanged from #578.",
        "Sidecar unchanged. No gameplay stats, construction, MOTHER, or ART changes.",
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
        "- Locomotor.ini has 522 definitions; six new blocks match sidecar exactly",
        "- Iraq_AlAbbas_Locomotor / R11SRBMLocomotor unchanged",
        "- Locomotor_IraqFactoryMissiles.ini byte-identical to #578",
        "- no hyphenated Specter-path files for A/B/C/H/I/J",
        "- Al-Abbas hyphenated #578 file kept; all Object-path projectiles kept",
        "- no duplicate locomotor names; factory projectile Objects count 1 (Al-Abbas 2 = #578 alias)",
        "- R11 / 9P117 / construction files byte-identical",
        "- Al-Abbas BuildTime 30.0 / Fire unlocked / rebuild unchanged",
        "- E/F/G/K/L not invented; factory slots 5-7/11-12 still empty",
        "- ART not rebuilt",
        "- packed DATA re-extracted and last-wins/duplicate audited",
        "",
        "RUNTIME TEST: WINDOWS NOT TESTED IN THIS ENVIRONMENT",
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
        "LOCOMOTOR_INI_IDENTICAL_TO_578=NO_SIX_LOCOS_APPENDED\n"
        "SIX_LOCOS_IN_LOCOMOTOR_INI=YES\n"
        "SIX_LOCOS_MATCH_SIDECAR=YES\n"
        "SIDECAR_UNCHANGED=YES\n"
        "HYPHENATED_A_B_C_H_I_J=ABSENT\n"
        "ALABBAS_SPECTER_FILE=KEPT_FROM_578\n"
        f"ART_SHA256={PREV_ART_SHA}\n"
        f"ART_SIZE={PREV_ART_SIZE}\n"
        "IMPLEMENTED=A,B,C,D,H,I,J\n"
        "UNIMPLEMENTED=E,F,G,K,L\n"
        "MOTHER_UNCHANGED=YES\n"
        "ALABBAS_BUILDTIME=30.0\n"
        "ALABBAS_FIRE=UNLOCKED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_WINDOWS=NOT_TESTED\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq factory missile Locomotor.ini registration (DATA-only)\n"
        "Based on PR #578. Registers six existing dedicated locos in Locomotor.ini.\n"
        "Does not add hyphenated Data/INI/Specter/Iraq Army/ duplicates.\n"
        "Place this complete replacement DATA BIG in the game folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "Keep the previous complete ART BIG. ART was not rebuilt.\n",
        encoding="utf-8",
    )
    (OUT / "AUDIT.txt").write_text(
        "Windows crash at Al-Basrah was missing Iraq_AlBasrah_Locomotor in Locomotor.ini.\n"
        "This pack = #578 + six sidecar loco blocks appended to Locomotor.ini.\n"
        "Hyphenated Specter-path duplicates for A/B/C/H/I/J are not present.\n"
        "Sidecar, Objects, construction, MOTHER, stats, ART unchanged.\n"
        "Windows runtime: NOT TESTED in this environment.\n",
        encoding="utf-8",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "Primary package (DATA):\n"
        "  PLACEHOLDER — GitHub Release withheld until real Windows runtime passes\n"
        "\n"
        "Place this complete replacement DATA file in the game folder:\n"
        "\n"
        "DATA:\n"
        "  FILE=_SPEC_DATA_ONE.big\n"
        f"  SIZE={out_data.stat().st_size}\n"
        f"  SHA256={data_sha}\n"
        f"  FILES={len(extracted)}\n"
        "\n"
        "ART unchanged — keep previous complete ART BIG:\n"
        "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-alabbas-data-art/_SPEC_ART_ONE.big\n"
        f"  SIZE={PREV_ART_SIZE}\n"
        f"  SHA256={PREV_ART_SHA}\n"
        "\n"
        "BASED_ON=PR578\n"
        "CHANGE=REGISTER_SIX_EXISTING_LOCOS_IN_LOCOMOTOR_INI\n"
        "HYPHENATED_A_B_C_H_I_J=ABSENT\n"
        "UNIMPLEMENTED=E,F,G,K,L\n"
        f"LOCOMOTOR_INI_DEFS={loco_n}\n"
        f"LOCOMOTOR_INI_BYTES={len(extracted[LOCO_KEY])}\n"
        "SIX_LOCOS_MATCH_SIDECAR=YES\n"
        "SIDECAR_UNCHANGED=YES\n"
        "MOTHER_UNCHANGED=YES\n"
        "ALABBAS_BUILDTIME=30.0\n"
        "ALABBAS_FIRE=UNLOCKED\n"
        "ART_REBUILT=NO\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_WINDOWS=NOT_TESTED\n"
        "TAG=s-iraq-missile-loco-register\n",
        encoding="utf-8",
    )
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
