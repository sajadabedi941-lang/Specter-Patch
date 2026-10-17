#!/usr/bin/env python3
"""Put Iraq_MissileFactoryCommandSet into core CommandSet.ini.

Authority: SPECTER_IRAQ_PROJECTILES_PARSE_FIX/_SPEC_DATA_ONE.big (current live s).
Preserves the projectile MissileAIUpdate parse fix byte-for-byte.
Does not rebuild ART.
Static validation only. Not an in-game runtime test.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_PROJECTILES_PARSE_FIX/_SPEC_DATA_ONE.big"
EXTRA_SRC = ROOT / "patch/Data/INI/CommandSet_Iraq_MissileFactory.ini"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_COMMANDSET"

CS_KEY = r"Data\INI\CommandSet.ini"
EXTRA_KEY = r"Data\INI\CommandSet_Iraq_MissileFactory.ini"
PROJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_StrategicMissile_Projectiles.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_MissileFactory.ini"

FACTORY_SET = (
    "CommandSet Iraq_MissileFactoryCommandSet\r\n"
    "  1  = Command_ConstructIraq_Ababil100_New\r\n"
    "  2  = Command_ConstructIraq_AlSamoud_New\r\n"
    "  3  = Command_ConstructIraq_AlHussein_New\r\n"
    "  4  = Command_ConstructIraq_AlHijarah_New\r\n"
    "  5  = Command_ConstructIraq_AlAbbas_New\r\n"
    "  6  = Command_ConstructIraq_Badr2000_New\r\n"
    "  7  = Command_ConstructIraq_Tammuz1_New\r\n"
    "  8  = Command_ConstructIraq_AlAbid_New\r\n"
    "  9  = Command_ConstructIraq_R11ScudB\r\n"
    "  10 = Command_ConstructIraq_Alhussaien\r\n"
    "  11 = Command_ConstructIraq_SA-6\r\n"
    "  12 = Command_ConstructIraq_BM-21\r\n"
    "  13 = Command_SetRallyPoint\r\n"
    "  14 = Command_Sell\r\n"
    "End\r\n"
)

SLOTS = [
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

BUTTONS = [
    ("Command_ConstructIraq_Ababil100_New", "Iraq_Ababil100_New"),
    ("Command_ConstructIraq_AlSamoud_New", "Iraq_AlSamoud_New"),
    ("Command_ConstructIraq_AlHussein_New", "Iraq_AlHussein_New"),
    ("Command_ConstructIraq_AlHijarah_New", "Iraq_AlHijarah_New"),
    ("Command_ConstructIraq_AlAbbas_New", "Iraq_AlAbbas_New"),
    ("Command_ConstructIraq_Badr2000_New", "Iraq_Badr2000_New"),
    ("Command_ConstructIraq_Tammuz1_New", "Iraq_Tammuz1_New"),
    ("Command_ConstructIraq_AlAbid_New", "Iraq_AlAbid_New"),
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


def inject_core_set(cs: str) -> str:
    if "CommandSet Iraq_MissileFactoryCommandSet" in cs:
        raise SystemExit("core CommandSet.ini already has Iraq_MissileFactoryCommandSet")
    if "\r\n" not in cs:
        raise SystemExit("s CommandSet.ini is not CRLF")
    if not cs.endswith("\r\n"):
        cs += "\r\n"
    return cs + "\r\n" + FACTORY_SET


def validate(data_map: dict[str, bytes], packed: bytes, src: dict[str, bytes]) -> list[str]:
    fails = []
    all_ini = b"\n".join(v for k, v in data_map.items() if k.lower().endswith(".ini"))
    nset = all_ini.count(b"CommandSet Iraq_MissileFactoryCommandSet")
    if nset != 1:
        fails.append(f"Iraq_MissileFactoryCommandSet count={nset}")
    nobj = all_ini.count(b"Object Iraq_MissileFactory")
    if nobj != 1:
        fails.append(f"Object Iraq_MissileFactory count={nobj}")

    core = data_map[CS_KEY].decode("latin1")
    extra = data_map[EXTRA_KEY].decode("latin1")
    factory = data_map[FACTORY_KEY].decode("latin1")
    if "CommandSet Iraq_MissileFactoryCommandSet" not in core:
        fails.append("core CommandSet.ini missing Iraq_MissileFactoryCommandSet")
    if re.search(r"(?m)^CommandSet Iraq_MissileFactoryCommandSet\b", extra):
        fails.append("extra CommandSet still defines Iraq_MissileFactoryCommandSet")
    if "CommandSet       = Iraq_MissileFactoryCommandSet" not in factory:
        fails.append("factory object CommandSet pointer lost")
    m = re.search(r"(?ms)^CommandSet Iraq_MissileFactoryCommandSet\r?\n.*?^End", core)
    if not m:
        fails.append("cannot extract core factory CommandSet")
    else:
        body = m.group(0)
        for slot in SLOTS:
            if slot not in body:
                fails.append(f"missing slot {slot}")
    if "CommandSet Iraq_VT72BCommandSet" in extra:
        fails.append("extra CommandSet overrides VT72B")
    if "14 = Command_ConstructIraq_MissileFactory" not in core:
        fails.append("VT72B slot 14 lost Missile Factory")
    wk = re.search(r"CommandSet Iraq_WorkerCommandSet\r?\n.*?^End", core, re.M | re.S)
    if not wk or "14 = Command_DisarmMinesAtPosition" not in wk.group(0):
        fails.append("Worker Clear Mines lost")

    cb = data_map[r"Data\INI\CommandButton.ini"].decode("latin1")
    for btn, obj in BUTTONS:
        if cb.count(f"CommandButton {btn}") != 1:
            fails.append(f"button {btn} count={cb.count(f'CommandButton {btn}')}")
        if f"Object        = {obj}" not in cb and f"Object           = {obj}" not in cb:
            # allow either spacing
            if not re.search(rf"(?ms)^CommandButton {re.escape(btn)}\r?\n.*?Object\s+=\s+{re.escape(obj)}\b", cb):
                fails.append(f"button {btn} Object != {obj}")

    proj = data_map[PROJ_KEY]
    if proj != src[PROJ_KEY]:
        fails.append("projectile parse-fix INI mutated")
    if proj.count(b"MissileAIUpdate") != 8:
        fails.append(f"MissileAIUpdate count={proj.count(b'MissileAIUpdate')}")
    for key in [
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini",
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\AlNida.ini",
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_StrategicMissiles_New.ini",
        r"Data\INI\Weapon_Iraq_StrategicMissiles.ini",
        r"Data\INI\CommandButton.ini",
        FACTORY_KEY,
    ]:
        if data_map[key] != src[key]:
            fails.append(f"unrelated DATA mutated {key}")

    changed = [k for k in data_map if data_map[k] != src.get(k)]
    extra_files = [k for k in data_map if k not in src]
    missing = [k for k in src if k not in data_map]
    if extra_files:
        fails.append(f"extra BIG files {extra_files[:5]}")
    if missing:
        fails.append(f"missing BIG files {missing[:5]}")
    if sorted(changed) != sorted([CS_KEY, EXTRA_KEY]):
        fails.append(f"changed files unexpected: {changed}")

    extracted = parse_big(packed)
    if extracted[CS_KEY] != data_map[CS_KEY]:
        fails.append("re-extract CommandSet.ini mismatch")
    if extracted[PROJ_KEY] != src[PROJ_KEY]:
        fails.append("re-extract projectiles mismatch")
    later = False
    seen = False
    for name in sorted(extracted, key=lambda n: n.lower()):
        if name == CS_KEY:
            seen = True
        elif seen and b"CommandSet Iraq_MissileFactoryCommandSet" in extracted[name]:
            later = True
            fails.append(f"later last-wins factory CommandSet in {name}")
    if later:
        fails.append("stale later factory CommandSet override")
    return fails


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing current s DATA {SRC_DATA}")
    if not EXTRA_SRC.is_file():
        raise SystemExit(f"missing extra CommandSet source {EXTRA_SRC}")

    src = parse_big(SRC_DATA.read_bytes())
    data_map = dict(src)
    cs = inject_core_set(data_map[CS_KEY].decode("latin1"))
    data_map[CS_KEY] = cs.encode("latin1")
    extra = to_crlf(EXTRA_SRC.read_bytes())
    if b"CommandSet Iraq_MissileFactoryCommandSet" in extra:
        raise SystemExit("extra source must not redefine Iraq_MissileFactoryCommandSet")
    if b"CommandSet Iraq_StrategicMissileNewCommandSet" not in extra:
        raise SystemExit("TEL CommandSet lost from extra source")
    data_map[EXTRA_KEY] = extra

    packed = build_big(data_map)
    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    out_big.write_bytes(packed)

    fails = validate(parse_big(packed), packed, src)
    report = [
        "# Iraq Missile Factory CommandSet restore",
        "",
        "Static validation only. The game was not launched.",
        "",
        "## Exact empty-bar cause",
        "",
        "`Iraq_MissileFactory` already pointed at `Iraq_MissileFactoryCommandSet`.",
        "All 14 CommandButtons existed once in core `CommandButton.ini`.",
        "The CommandSet itself existed only in extra `CommandSet_Iraq_MissileFactory.ini`.",
        "Core `CommandSet.ini` had zero `Iraq_MissileFactoryCommandSet` definitions.",
        "SPECTER runtime uses core `CommandSet.ini` as the visible CommandSet store",
        "(same class of bug as extra `Iraq_VT72BCommandSet` last-win being invisible).",
        "A factory CommandSet that exists only on an extra path is not applied,",
        "so the built factory shows an empty production bar.",
        "",
        "## Fix",
        "",
        "Appended the 14-slot `Iraq_MissileFactoryCommandSet` to core `CommandSet.ini`.",
        "Removed that definition from the extra CommandSet file so it exists exactly once.",
        "Left `Iraq_StrategicMissileNewCommandSet` in the extra file (TELs untouched).",
        "Projectile parse-fix INI / MissileAIUpdate blocks unchanged.",
        "",
        "## Pack",
        "",
        f"- DATA path: `{out_big}`",
        f"- DATA size: {out_big.stat().st_size}",
        f"- DATA SHA256: {sha256_path(out_big)}",
        f"- files: {len(data_map)}",
        "- ART: unchanged; not rebuilt",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
        print("\n".join(report))
        return 1
    report += [
        "## VALIDATION PASS",
        "- factory object CommandSet = Iraq_MissileFactoryCommandSet",
        "- CommandSet defined exactly once, in core CommandSet.ini",
        "- all 14 slots present",
        "- all 8 new construct CommandButtons resolve once",
        "- no later last-wins override",
        "- VT72B slot 14 / Worker Clear Mines unchanged",
        "- projectile MissileAIUpdate x8 unchanged",
        "- 9P117 / Sarab7 / TELs / weapons / factory object / CommandButton.ini unchanged",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
    (OUT / "README.txt").write_text(
        "SPECTER Iraq Missile Factory CommandSet restore\n"
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
