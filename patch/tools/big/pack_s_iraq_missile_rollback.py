#!/usr/bin/env python3
"""Rollback the Iraq 8-missile + Missile Factory project from live s.

Starts from current live s DATA/ART, removes only files and core-file
patches introduced after commit 220b7feb (first missile-factory add).
Compares the stripped maps to the pre-project live s archives in
/tmp/s-bigs, which are the exact BIGs the project started from
(FLAG_SIZE_FINAL-era s, dated 2026-10-04).

Does not invent new units, ART, or balance. Static validation only.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
from pathlib import Path

ROOT = Path("/workspace")
CUR_DATA = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_COMMANDSET/_SPEC_DATA_ONE.big"
CUR_ART = ROOT / "patch/Release/SPECTER_IRAQ_TEL_VISIBLE/_SPEC_ART_ONE.big"
PRE_DATA = Path("/tmp/s-bigs/_SPEC_DATA_ONE.big")
PRE_ART = Path("/tmp/s-bigs/_SPEC_ART_ONE.big")
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_ROLLBACK"

DATA_EXTRAS = [
    r"Data\INI\CommandSet_Iraq_MissileFactory.ini",
    r"Data\INI\ObjectCreationList_Iraq_StrategicMissiles.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_MissileFactory.ini",
    r"Data\INI\Object\Specter\Iraq Army\Hulk\Iraq_StrategicMissile_Hulks.ini",
    r"Data\INI\Object\Specter\Iraq Army\Iraq_StrategicMissile_Projectiles.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_StrategicMissiles_New.ini",
    r"Data\INI\Weapon_Iraq_StrategicMissiles.ini",
]

CORE_RESTORES = [
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\English\generals.csf",
]

FORBIDDEN = [
    b"Iraq_AlHussein_New",
    b"Iraq_AlHijarah_New",
    b"Iraq_AlAbbas_New",
    b"Iraq_Badr2000_New",
    b"Iraq_AlSamoud_New",
    b"Iraq_Ababil100_New",
    b"Iraq_Tammuz1_New",
    b"Iraq_AlAbid_New",
    b"Projectile_Iraq_AlHussein_New",
    b"Command_ConstructIraq_AlHussein_New",
    b"Command_ConstructIraq_AlHijarah_New",
    b"Command_ConstructIraq_AlAbbas_New",
    b"Command_ConstructIraq_Badr2000_New",
    b"Command_ConstructIraq_AlSamoud_New",
    b"Command_ConstructIraq_Ababil100_New",
    b"Command_ConstructIraq_Tammuz1_New",
    b"Command_ConstructIraq_AlAbid_New",
    b"Command_ConstructIraq_MissileFactory",
    b"Iraq_MissileFactoryCommandSet",
    b"Object Iraq_MissileFactory",
]

KEEP = [
    b"Object Iraq_R11ScudB",
    b"Object Iraq_Sarab7",
    b"Object Iraq_Alhussaien",
    b"Command_ConstructIraq_R11ScudB",
    b"Command_ConstructIraq_Alhussaien",
    b"Command_ConstructIraq_SA-6",
    b"Command_ConstructIraq_BM-21",
    b"Command_ConstructIraq_HeavyAirBase",
    b"Command_DisarmMinesAtPosition",
]

DONORS = [
    "Irq_9P117",
    "Irq_9P117D",
    "Irq_9P117R",
    "Irq_R11_M",
    "Irq_Abbas_L",
    "Irq_AbbasM",
    "Irq_Sarab7",
    "Irq_Lamiaa",
    "Iraq_Alhusain_L",
    "Iraq_Alhusain_M",
    "RUS_9K720K",
    "RUS_9K720KD",
    "RUS_RS24",
    "RUS_RS24M",
    "Hwasong7",
    "Irq_Alraad2M",
    "Irq_WarFactory",
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


def find_ci(files: dict[str, bytes], key: str) -> str | None:
    lk = key.replace("/", "\\").lower()
    for k in files:
        if k.replace("/", "\\").lower() == lk:
            return k
    return None


def is_project_art(name: str) -> bool:
    lk = name.replace("/", "\\").lower()
    stem = Path(name.replace("\\", "/")).stem.lower()
    if lk.startswith("art\\w3d\\") or lk.startswith("art\\textures\\"):
        if stem.startswith(("iq_al", "iq_badr", "iq_tammuz", "iq_ababil")):
            return True
        if stem.startswith(("lsfiqmchechang", "lsfmchechangcb")):
            return True
        if stem in {
            "camo net",
            "camo netd",
            "camo netk",
            "lsfchinabase",
            "lsfchinabased",
            "lsfchinabasee",
            "lsfdf11m",
            "lsfdf11md",
            "lsfdustpaodao",
            "lsfdustpaodaod",
            "lsfdustpaodaoe",
            "yilake",
            "yilaked",
        }:
            return True
    return False


def validate(data: dict[str, bytes], art: dict[str, bytes], pre_d: dict[str, bytes], pre_a: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    all_ini = b"\n".join(v for k, v in data.items() if k.lower().endswith(".ini"))

    for needle in FORBIDDEN:
        if needle in all_ini:
            fails.append(f"forbidden leftover {needle.decode('ascii')}")

    for needle in KEEP:
        if needle not in all_ini:
            fails.append(f"lost preexisting {needle.decode('ascii')}")

    core = data[r"Data\INI\CommandSet.ini"].decode("latin1")
    m = re.search(r"(?ms)^CommandSet Iraq_VT72BCommandSet\r?\n.*?^End", core)
    if not m or "14 = Command_DisarmMinesAtPosition" not in m.group(0):
        fails.append("VT72B slot 14 not restored to Clear Mines")
    if "Command_ConstructIraq_MissileFactory" in core:
        fails.append("VT72B still references Missile Factory")
    w = re.search(r"(?ms)^CommandSet Iraq_WorkerCommandSet\r?\n.*?^End", core)
    if not w or "14 = Command_DisarmMinesAtPosition" not in w.group(0):
        fails.append("Worker CommandSet damaged")
    if "CommandSet Iraq_MissileFactoryCommandSet" in core:
        fails.append("factory CommandSet still in core")

    cb = data[r"Data\INI\CommandButton.ini"].decode("latin1")
    if "CommandButton Command_ConstructIraq_MissileFactory" in cb:
        fails.append("factory button still in CommandButton.ini")

    for extra in DATA_EXTRAS:
        if extra in data or find_ci(data, extra):
            fails.append(f"DATA extra still present {extra}")

    for name in art:
        if is_project_art(name):
            fails.append(f"project ART leftover {name}")

    for donor in DONORS:
        pk = find_ci(pre_a, f"Art\\W3D\\{donor}.W3D")
        ck = find_ci(art, f"Art\\W3D\\{donor}.W3D")
        if pk is None or ck is None:
            fails.append(f"donor missing {donor}")
        elif pre_a[pk] != art[ck]:
            fails.append(f"donor mutated {donor}")

    if set(data) != set(pre_d):
        fails.append(f"DATA path set != pre-project extra={sorted(set(data)-set(pre_d))[:5]} missing={sorted(set(pre_d)-set(data))[:5]}")
    if set(art) != set(pre_a):
        fails.append(f"ART path set != pre-project extra={sorted(set(art)-set(pre_a))[:5]} missing={sorted(set(pre_a)-set(art))[:5]}")

    mismatch_d = [k for k in pre_d if data.get(k) != pre_d[k]]
    mismatch_a = [k for k in pre_a if art.get(k) != pre_a[k]]
    if mismatch_d:
        fails.append(f"DATA bytes differ from pre-project {mismatch_d[:5]}")
    if mismatch_a:
        fails.append(f"ART bytes differ from pre-project {mismatch_a[:5]}")

    return fails


def main() -> int:
    for p in (CUR_DATA, CUR_ART, PRE_DATA, PRE_ART):
        if not p.is_file():
            raise SystemExit(f"missing {p}")

    cur_d = parse_big(CUR_DATA.read_bytes())
    cur_a = parse_big(CUR_ART.read_bytes())
    pre_d = parse_big(PRE_DATA.read_bytes())
    pre_a = parse_big(PRE_ART.read_bytes())

    notes = []
    data = dict(cur_d)
    art = dict(cur_a)

    for key in DATA_EXTRAS:
        hit = find_ci(data, key)
        if hit:
            del data[hit]
            notes.append(f"removed DATA {hit}")
        else:
            notes.append(f"already absent DATA {key}")

    for key in CORE_RESTORES:
        if data.get(key) != pre_d[key]:
            data[key] = pre_d[key]
            notes.append(f"restored DATA {key} from pre-project s")

    removed_art = 0
    for key in list(art):
        if is_project_art(key) and find_ci(pre_a, key) is None:
            del art[key]
            removed_art += 1
    notes.append(f"removed ART files {removed_art}")

    fails = validate(data, art, pre_d, pre_a)
    OUT.mkdir(parents=True, exist_ok=True)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"

    # After proving stripped maps match pre-project content, ship the
    # original pre-project BIG bytes so packing/index matches last healthy s.
    if not fails:
        shutil.copyfile(PRE_DATA, out_data)
        shutil.copyfile(PRE_ART, out_art)

    extracted_d = parse_big(out_data.read_bytes()) if out_data.is_file() and not fails else data
    extracted_a = parse_big(out_art.read_bytes()) if out_art.is_file() and not fails else art
    if not fails:
        fails = validate(extracted_d, extracted_a, pre_d, pre_a)

    report = [
        "# Iraq 8-missile + Missile Factory rollback",
        "",
        "Static validation only. The game was not launched.",
        "",
        "## Pre-project healthy state",
        "",
        "Last git commit before this project: 0ff5d1c2582b3972ac6b74bfcb0a5f5f21297e8e",
        "(Add files via upload). First project commit: 220b7feb Add Iraqi Missile Factory.",
        "Live s BIGs the project started from: /tmp/s-bigs (FLAG_SIZE_FINAL-era, 2026-10-04).",
        "All later live-s commits were this project only. No unrelated packed-BIG changes.",
        "",
        "## Removed from current live s",
        "",
    ]
    report.extend(f"- {n}" for n in notes)
    report += [
        "",
        "## Pack",
        "",
        f"- DATA path: `{out_data}`",
        f"- DATA size: {out_data.stat().st_size if out_data.is_file() else 'n/a'}",
        f"- DATA SHA256: {sha256_path(out_data) if out_data.is_file() else 'n/a'}",
        f"- DATA files: {len(extracted_d)}",
        f"- ART path: `{out_art}`",
        f"- ART size: {out_art.stat().st_size if out_art.is_file() else 'n/a'}",
        f"- ART SHA256: {sha256_path(out_art) if out_art.is_file() else 'n/a'}",
        f"- ART files: {len(extracted_a)}",
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
        "- no 8 new Objects / buttons / projectiles / weapons / OCLs / hulks",
        "- no Iraq_MissileFactory / construct button / factory CommandSet",
        "- no IQ_* family clones; no factory LSF imports",
        "- donor W3Ds byte-identical to pre-project s",
        "- existing R11 / Sarab7 / Alhussaien / SA-6 / BM-21 / HeavyAirBase intact",
        "- Iraq_VT72BCommandSet slot 14 restored to Command_DisarmMinesAtPosition",
        "- Iraq_WorkerCommandSet unchanged",
        "- stripped DATA/ART maps byte-identical to pre-project /tmp/s-bigs",
        "- shipped BIGs are the original pre-project live s archives",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
    (OUT / "README.txt").write_text(
        "SPECTER Iraq 8-missile + Missile Factory rollback\n"
        "\n"
        "Install both BIGs over current live s.\n"
        "This returns DATA and ART to the last healthy live s\n"
        "immediately before the Iraqi Missile Factory / 8-missile project.\n"
        "\n"
        "Static validation only. The game was not launched.\n",
        encoding="ascii",
    )
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
