#!/usr/bin/env python3
"""Rebuild complete current s DATA with the projectiles INI parse fix.

Authority: SPECTER_IRAQ_COMPLETE/_SPEC_DATA_ONE.big (current live s).
Replaces only Iraq_StrategicMissile_Projectiles.ini.
Does not rebuild ART.
Static validation only. Not an in-game runtime test.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_COMPLETE/_SPEC_DATA_ONE.big"
SRC_INI = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Iraq_StrategicMissile_Projectiles.ini"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_PROJECTILES_PARSE_FIX"
PROJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_StrategicMissile_Projectiles.ini"

KEYS = [
    "AlHussein",
    "AlHijarah",
    "AlAbbas",
    "Badr2000",
    "AlSamoud",
    "Ababil100",
    "Tammuz1",
    "AlAbid",
]
OBJECTS = [f"Iraq_{k}_New" for k in KEYS]
PROJS = [f"Projectile_Iraq_{k}_New" for k in KEYS]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes):
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


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


def to_crlf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


def stack_parse(text: str) -> list[str]:
    errors = []
    stack: list[tuple[str, int]] = []
    openers = re.compile(
        r"^(Object|Draw|Behavior|Body|ArmorSet|WeaponSet|Prerequisites|"
        r"ConditionState|DefaultConditionState|TransitionState|AliasConditionState|"
        r"Weapon|ObjectCreationList|CommandSet|CommandButton)\b",
        re.I,
    )
    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.split(";", 1)[0].strip()
        if not s:
            continue
        if re.match(r"^End$", s, re.I):
            if not stack:
                errors.append(f"line {i}: extra End")
            else:
                stack.pop()
            continue
        if openers.match(s):
            stack.append((s.split()[0], i))
    for name, line in stack:
        errors.append(f"line {line}: unclosed {name}")
    return errors


def validate(data_map: dict[str, bytes], packed: bytes, src: dict[str, bytes]) -> list[str]:
    fails = []
    copies = [k for k in data_map if k.lower().endswith("iraq_strategicmissile_projectiles.ini")]
    if copies != [PROJ_KEY]:
        fails.append(f"projectiles path copies={copies}")
    proj = data_map[PROJ_KEY]
    if proj != to_crlf(SRC_INI.read_bytes()):
        fails.append("packed projectiles INI != workspace source CRLF")
    if proj[:3] == b"\xef\xbb\xbf":
        fails.append("BOM on packed projectiles INI")
    if proj.count(b"\r\n") == 0:
        fails.append("packed projectiles INI is not CRLF")
    if b"\x00" in proj:
        fails.append("NUL in projectiles INI")
    try:
        text = proj.decode("ascii")
    except UnicodeDecodeError as e:
        fails.append(f"non-ascii projectiles INI: {e}")
        text = proj.decode("latin1")
    if text != text.encode("latin1").decode("latin1"):
        fails.append("latin1 roundtrip failed")

    ends = stack_parse(text)
    if ends:
        fails.extend(ends)

    for name in PROJS:
        if text.count(f"Object {name}") != 1:
            fails.append(f"{name} definition count={text.count(f'Object {name}')}")
        block = re.search(rf"(?ms)^Object {name}\n.*?^End\n", text.replace("\r\n", "\n"))
        if not block:
            fails.append(f"cannot extract {name}")
            continue
        body = block.group(0)
        if "MissileAIUpdate" not in body:
            fails.append(f"{name} missing MissileAIUpdate")
        if "KindOf = PROJECTILE BALLISTIC_MISSILE" not in body:
            fails.append(f"{name} KindOf changed")
        if "Locomotor = SET_NORMAL" not in body:
            fails.append(f"{name} missing Locomotor")

    ababil = re.search(
        r"(?ms)^Object Projectile_Iraq_Ababil100_New\n.*?^End\n",
        text.replace("\r\n", "\n"),
    )
    if ababil and "PGMRaad2RocketLocomotor" not in ababil.group(0):
        fails.append("Ababil-100 locomotor changed")
    if ababil and "InitialVelocity = 310" not in ababil.group(0):
        fails.append("Ababil-100 MissileAIUpdate not Raad2 donor")

    all_ini = b"\n".join(v for k, v in data_map.items() if k.lower().endswith(".ini"))
    for name in PROJS:
        if all_ini.count(f"Object {name}".encode()) != 1:
            fails.append(f"last-wins Object {name} count={all_ini.count(f'Object {name}'.encode())}")

    # referenced objects / FX / armor / locomotor
    refs = {
        "R11SRBMLocomotor": rb"Locomotor\s+R11SRBMLocomotor|R11SRBMLocomotor",
        "PGMRaad2RocketLocomotor": rb"Locomotor\s+PGMRaad2RocketLocomotor|PGMRaad2RocketLocomotor",
        "SRBMArmor": rb"Armor\s+SRBMArmor|^Armor\s+SRBMArmor",
        "FX_GenericMissileDisintegrate": b"FXList FX_GenericMissileDisintegrate",
        "OCL_GenericMissileDisintegrate": b"ObjectCreationList OCL_GenericMissileDisintegrate",
        "FX_GenericMissileDeath": b"FXList FX_GenericMissileDeath",
        "GenericMissileAmbientLoop": b"GenericMissileAmbientLoop",
        "LRBM_Trail": b"LRBM_Trail",
    }
    for label, pat in refs.items():
        if not re.search(pat, all_ini, re.M):
            # softer: any occurrence is enough for sounds/particles
            if all_ini.count(label.encode()) < 1:
                fails.append(f"missing ref {label}")

    # weapon -> projectile chain unchanged
    weap = data_map[r"Data\INI\Weapon_Iraq_StrategicMissiles.ini"].decode("latin1")
    for key, proj_name in zip(KEYS, PROJS):
        if f"ProjectileObject            = {proj_name}" not in weap:
            fails.append(f"weapon {key} projectile link lost")
        if f"Weapon Weapon_Iraq_{key}_New" not in weap:
            fails.append(f"weapon {key} missing")

    # factory / TELs / 9P117 / Sarab7 / CommandSets must be byte-identical
    unchanged = [
        r"Data\INI\CommandSet_Iraq_MissileFactory.ini",
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_StrategicMissiles_New.ini",
        r"Data\INI\Object\Specter\Iraq Army\Hulk\Iraq_StrategicMissile_Hulks.ini",
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini",
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\AlNida.ini",
        r"Data\INI\Weapon_Iraq_StrategicMissiles.ini",
        r"Data\INI\CommandSet.ini",
        r"Data\INI\CommandButton.ini",
    ]
    for key in unchanged:
        if data_map[key] != src[key]:
            fails.append(f"unrelated DATA mutated {key}")

    extra_cs = data_map[r"Data\INI\CommandSet_Iraq_MissileFactory.ini"].decode("latin1")
    expected_slots = [
        "1  = Command_ConstructIraq_Ababil100_New",
        "2  = Command_ConstructIraq_AlSamoud_New",
        "3  = Command_ConstructIraq_AlHussein_New",
        "4  = Command_ConstructIraq_AlHijarah_New",
        "5  = Command_ConstructIraq_AlAbbas_New",
        "6  = Command_ConstructIraq_Badr2000_New",
        "7  = Command_ConstructIraq_Tammuz1_New",
        "8  = Command_ConstructIraq_AlAbid_New",
        "9  = Command_ConstructIraq_R11ScudB",
        "10 = Command_ConstructIraq_Alhussaien",
        "11 = Command_ConstructIraq_SA-6",
        "12 = Command_ConstructIraq_BM-21",
        "13 = Command_SetRallyPoint",
        "14 = Command_Sell",
    ]
    for slot in expected_slots:
        if slot not in extra_cs:
            fails.append(f"factory slot lost: {slot}")

    # only the projectiles path may differ vs authority s
    changed = [k for k in data_map if data_map[k] != src.get(k)]
    extra = [k for k in data_map if k not in src]
    missing = [k for k in src if k not in data_map]
    if extra:
        fails.append(f"extra BIG files {extra[:5]}")
    if missing:
        fails.append(f"missing BIG files {missing[:5]}")
    if changed != [PROJ_KEY]:
        fails.append(f"changed files beyond projectiles: {changed}")

    extracted = parse_big(packed)
    if extracted[PROJ_KEY] != proj:
        fails.append("re-extract projectiles mismatch")
    if extracted[PROJ_KEY].count(b"MissileAIUpdate") != 8:
        fails.append("re-extract MissileAIUpdate count")

    later = False
    seen = False
    for name in sorted(extracted, key=lambda n: n.lower()):
        if name == PROJ_KEY:
            seen = True
        elif seen and name.lower().endswith("iraq_strategicmissile_projectiles.ini"):
            later = True
    if later:
        fails.append("stale later last-wins projectiles copy")

    return fails


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing current s DATA {SRC_DATA}")
    if not SRC_INI.is_file():
        raise SystemExit(f"missing source INI {SRC_INI}")

    src = parse_big(SRC_DATA.read_bytes())
    data_map = dict(src)
    data_map[PROJ_KEY] = to_crlf(SRC_INI.read_bytes())
    packed = build_big(data_map)

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    out_big.write_bytes(packed)

    fails = validate(parse_big(packed), packed, src)
    report = []
    report.append("# Iraq Strategic Missile Projectiles parse fix")
    report.append("")
    report.append("Static validation only. The game was not launched.")
    report.append("")
    report.append("## Exact parser defect")
    report.append("")
    report.append(
        "Every `Projectile_Iraq_*_New` Object in "
        "`Iraq_StrategicMissile_Projectiles.ini` was `KindOf = PROJECTILE "
        "BALLISTIC_MISSILE` with `Locomotor` but without `MissileAIUpdate` "
        "or `DumbProjectileBehavior`."
    )
    report.append("")
    report.append(
        "Live s ballistic missiles that use `R11SRBMLocomotor` / "
        "`PGMRaad2RocketLocomotor` (ALHIJARAH_MRBM_Object, MRBM_Raad2_Object) "
        "always carry `MissileAIUpdate` immediately before `Locomotor`. "
        "The 8 new projectiles were the only `PROJECTILE BALLISTIC_MISSILE` "
        "templates in current s missing that required module. The engine "
        "throws `error parsing INI file` while loading this file, starting "
        "at the first definition `Object Projectile_Iraq_AlHussein_New`. "
        "All 8 shared the same generator template, so all 8 were illegal."
    )
    report.append("")
    report.append("## Fix")
    report.append("")
    report.append(
        "Inserted the live donor `MissileAIUpdate` block before each "
        "`Locomotor` line. Seven R11-family missiles use ALHIJARAH_MRBM_Object "
        "values. Ababil-100 uses MRBM_Raad2_Object values to keep "
        "`PGMRaad2RocketLocomotor` behavior. Damage, radius, range, reload, "
        "weapon links, Scale, models, and KindOf are unchanged."
    )
    report.append("")
    report.append("## Pack")
    report.append("")
    report.append(f"- DATA path: `{out_big}`")
    report.append(f"- DATA size: {out_big.stat().st_size}")
    report.append(f"- DATA SHA256: {sha256_path(out_big)}")
    report.append(f"- files: {len(data_map)}")
    report.append(f"- projectiles INI bytes: {len(data_map[PROJ_KEY])}")
    report.append("- ART: unchanged; not rebuilt")
    report.append("")
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
        print("\n".join(report))
        return 1
    report.append("## VALIDATION PASS")
    report.append("- parse / End stack")
    report.append("- all 8 Projectile_Iraq_*_New + MissileAIUpdate")
    report.append("- Weapon -> Projectile links")
    report.append("- no duplicate Object names")
    report.append("- no stale later last-wins copy")
    report.append("- unrelated factory / TEL / R11 / Sarab7 / CommandSet bytes unchanged")
    report.append("- re-extract packed INI matches source")
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
    (OUT / "README.txt").write_text(
        "SPECTER Iraq strategic missile projectiles INI parse fix\n"
        "\n"
        "Install the corrected _SPEC_DATA_ONE.big over the current live s DATA.\n"
        "ART is unchanged from s-iraq-complete. Do not replace ART.\n"
        "\n"
        "Static validation only. The game was not launched in this environment.\n",
        encoding="ascii",
    )
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
