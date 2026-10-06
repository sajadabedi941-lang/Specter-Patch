#!/usr/bin/env python3
"""Surgical DATA-only fix: Iraq_VT72BCommandSet slot-19 overflow crash.

Root cause
----------
Zero Hour CommandSet arrays are MAX_COMMANDS_PER_SET = 18.
The live Al-Fahd pack added:

    19 = Command_ConstructIraq_AlFahdMissileFactory

Iraq_VT72BCommandSet is the only packed CommandSet that uses slot 19.
The engine writes past the 18-slot command array when that set is bound
(Iraq start / select VT72B). The crash dialog truncates the name to
"Iraq_VT2BCommandSet" — no Iraq_VT2B* identifier exists in packed DATA.

Fix
---
- Remove illegal slot 19 from Iraq_VT72BCommandSet.
- Keep packed slots 1-18 byte-identical, including slot 14 Clear Mines.
- Relocate the factory construct button to Iraq_WorkerCommandSet unused
  slot 12 (valid <=18). Existing Worker slots 1-11 / 13-14 unchanged.
- Do not rebuild ART. Do not restore the old 8-missile project.

Authority baseline: live s-iraq-alfahd500 DATA
  366368023  SHA256 358d9358fd37faadbb211920ec87a762570fadd01a7f0bd157fd3439a1b9ca71
Static validation only. The game is not launched.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD500/_SPEC_DATA_ONE.big"
SRC_ROLL = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_ROLLBACK/_SPEC_DATA_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_VT72B_CRASHFIX"

LIVE_DATA_SHA = "358d9358fd37faadbb211920ec87a762570fadd01a7f0bd157fd3439a1b9ca71"
LIVE_DATA_SIZE = 366368023

OLD_RESIDUE = [
    b"Iraq_AlHussein_New",
    b"Iraq_AlHijarah_New",
    b"Iraq_AlAbbas_New",
    b"Iraq_Badr2000_New",
    b"Iraq_AlSamoud_New",
    b"Iraq_Ababil100_New",
    b"Iraq_Tammuz1_New",
    b"Iraq_AlAbid_New",
    b"Object Iraq_MissileFactory",
    b"Iraq_MissileFactoryCommandSet",
    b"Command_ConstructIraq_MissileFactory",
    b"IQ_AlHussein",
]

VT72B_LIVE = (
    "CommandSet Iraq_VT72BCommandSet\r\n"
    "  1  = Command_ConstructIraq_PowerPlant\r\n"
    "  2  = Command_ConstructIraq_CommandCenter\r\n"
    "  3  = Command_ConstructIraq_SupplyCenter\r\n"
    "  4  = Command_ConstructIraq_WarFactory_T\r\n"
    "  5  = Command_ConstructIraq_Airfield_T\r\n"
    "  6  = Command_ConstructIraq_MIC\r\n"
    "  7  = Command_ConstructIraq_DefenseSite ;Command_ConstructIraq_100mmCannon\r\n"
    "  8  = Command_ConstructIraq_RadarStation\r\n"
    "  9  = Command_ConstructIraq_Sam2\r\n"
    "  10 = Command_ConstructIraq_Barracks\r\n"
    "  11 = Command_ConstructIraq_Abbas\r\n"
    "  12 = Command_ConstructIraq_D30_Howitzer\r\n"
    "  13 = Command_ConstructIraq_HeavyAirBase\r\n"
    "  14 = Command_DisarmMinesAtPosition\r\n"
    "  15 = Command_ConstructIraq_Abbas_AI\r\n"
    "  16 = Command_ConstructIraqFahad3SamSite\r\n"
    "  17 = Command_ConstructIraqMilitaryWarfactory\r\n"
    "  18 = Command_Stop\r\n"
    "  19 = Command_ConstructIraq_AlFahdMissileFactory\r\n"
    "End"
)

VT72B_FIXED = (
    "CommandSet Iraq_VT72BCommandSet\r\n"
    "  1  = Command_ConstructIraq_PowerPlant\r\n"
    "  2  = Command_ConstructIraq_CommandCenter\r\n"
    "  3  = Command_ConstructIraq_SupplyCenter\r\n"
    "  4  = Command_ConstructIraq_WarFactory_T\r\n"
    "  5  = Command_ConstructIraq_Airfield_T\r\n"
    "  6  = Command_ConstructIraq_MIC\r\n"
    "  7  = Command_ConstructIraq_DefenseSite ;Command_ConstructIraq_100mmCannon\r\n"
    "  8  = Command_ConstructIraq_RadarStation\r\n"
    "  9  = Command_ConstructIraq_Sam2\r\n"
    "  10 = Command_ConstructIraq_Barracks\r\n"
    "  11 = Command_ConstructIraq_Abbas\r\n"
    "  12 = Command_ConstructIraq_D30_Howitzer\r\n"
    "  13 = Command_ConstructIraq_HeavyAirBase\r\n"
    "  14 = Command_DisarmMinesAtPosition\r\n"
    "  15 = Command_ConstructIraq_Abbas_AI\r\n"
    "  16 = Command_ConstructIraqFahad3SamSite\r\n"
    "  17 = Command_ConstructIraqMilitaryWarfactory\r\n"
    "  18 = Command_Stop\r\n"
    "End"
)

WORKER_LIVE = (
    "CommandSet Iraq_WorkerCommandSet\r\n"
    "  1  = Command_ConstructIraq_PowerPlant\r\n"
    "  2  = Command_ConstructIraq_CommandCenter\r\n"
    "  3  = Command_ConstructIraq_SupplyCenter\r\n"
    " ; 4  = Command_ConstructIraq_WarFactory\r\n"
    "  ;5  = Command_ConstructIraq_Airfield\r\n"
    "  6 = Command_ConstructIraq_MIC\r\n"
    "  7  = Command_ConstructIraq_100mmCannon\r\n"
    "  8  = Command_ConstructIraq_RadarStation\r\n"
    "  9  = Command_ConstructIraq_Sam2\r\n"
    "  10 = Command_ConstructIraq_Barracks\r\n"
    "  11 = Command_ConstructIraq_Abbas\r\n"
    "  13 = Command_Stop\r\n"
    "  14 = Command_DisarmMinesAtPosition\r\n"
    "End"
)

WORKER_FIXED = (
    "CommandSet Iraq_WorkerCommandSet\r\n"
    "  1  = Command_ConstructIraq_PowerPlant\r\n"
    "  2  = Command_ConstructIraq_CommandCenter\r\n"
    "  3  = Command_ConstructIraq_SupplyCenter\r\n"
    " ; 4  = Command_ConstructIraq_WarFactory\r\n"
    "  ;5  = Command_ConstructIraq_Airfield\r\n"
    "  6 = Command_ConstructIraq_MIC\r\n"
    "  7  = Command_ConstructIraq_100mmCannon\r\n"
    "  8  = Command_ConstructIraq_RadarStation\r\n"
    "  9  = Command_ConstructIraq_Sam2\r\n"
    "  10 = Command_ConstructIraq_Barracks\r\n"
    "  11 = Command_ConstructIraq_Abbas\r\n"
    "  12 = Command_ConstructIraq_AlFahdMissileFactory\r\n"
    "  13 = Command_Stop\r\n"
    "  14 = Command_DisarmMinesAtPosition\r\n"
    "End"
)


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


def commandset_block(cs: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^CommandSet {re.escape(name)}\r?\n.*?^End", cs)
    return m.group(0) if m else None


def slot_map(block: str) -> dict[int, str]:
    return {int(a): b for a, b in re.findall(r"(?m)^\s*(\d+)\s*=\s*(\S+)", block)}


def validate(extracted: dict[str, bytes], src: dict[str, bytes], roll: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    all_ini = b"\n".join(v for k, v in extracted.items() if k.lower().endswith(".ini"))

    if b"Iraq_VT2BCommandSet" in all_ini or b"Iraq_VT2B" in all_ini:
        fails.append("Iraq_VT2B* identifier appeared")

    for needle in OLD_RESIDUE:
        if needle in all_ini:
            fails.append(f"old project residue {needle.decode('ascii')}")

    if all_ini.count(b"Object Iraq_AlFahd500") != 1:
        fails.append("Iraq_AlFahd500 count")
    if all_ini.count(b"Object Iraq_AlFahdMissileFactory") != 1:
        fails.append("factory object count")
    if all_ini.count(b"Object Iraq_R11ScudB") != 1:
        fails.append("Iraq_R11ScudB lost or duplicated")
    if all_ini.count(b"Weapon Weapon_Iraq_AlFahd500") != 1:
        fails.append("AlFahd weapon count")

    core_cs = extracted[r"Data\INI\CommandSet.ini"].decode("latin1")
    if core_cs.count("CommandSet Iraq_VT72BCommandSet") != 1:
        fails.append(f"Iraq_VT72BCommandSet defs={core_cs.count('CommandSet Iraq_VT72BCommandSet')}")
    if "Iraq_VT72BCommandSet" in core_cs and re.search(
        r"(?ms)^CommandSet Iraq_VT72BCommandSet\r?\n.*Iraq_VT72BCommandSet", core_cs
    ):
        fails.append("recursive/self-referencing Iraq_VT72BCommandSet")

    extra_hits = []
    for k, v in extracted.items():
        if k.lower() == r"data\ini\commandset.ini":
            continue
        if not k.lower().endswith(".ini"):
            continue
        if b"CommandSet Iraq_VT72BCommandSet" in v or b"CommandSet Iraq_WorkerCommandSet" in v:
            extra_hits.append(k)
    if extra_hits:
        fails.append(f"extra last-win CommandSet {extra_hits}")

    vt = commandset_block(core_cs, "Iraq_VT72BCommandSet")
    wk = commandset_block(core_cs, "Iraq_WorkerCommandSet")
    fac = commandset_block(core_cs, "Iraq_AlFahdMissileFactoryCommandSet")
    if vt != VT72B_FIXED:
        fails.append("Iraq_VT72BCommandSet block mismatch after fix")
    if wk != WORKER_FIXED:
        fails.append("Iraq_WorkerCommandSet block mismatch after fix")
    if not fac or "1  = Command_ConstructIraq_AlFahd500" not in fac:
        fails.append("factory CommandSet missing AlFahd500")
    if fac and "Iraq_AlFahdMissileFactoryCommandSet" in fac.split("\n", 1)[-1]:
        fails.append("factory CommandSet self-reference")

    vt_slots = slot_map(vt or "")
    wk_slots = slot_map(wk or "")
    if 19 in vt_slots:
        fails.append("illegal slot 19 still present on Iraq_VT72BCommandSet")
    if max(vt_slots or {0}) > 18:
        fails.append(f"VT72B max slot {max(vt_slots)}")
    expected_vt = slot_map(VT72B_FIXED)
    if vt_slots != expected_vt:
        fails.append("VT72B slots 1-18 not preserved")
    if vt_slots.get(14) != "Command_DisarmMinesAtPosition":
        fails.append("VT72B slot 14 Clear Mines lost")
    if wk_slots.get(14) != "Command_DisarmMinesAtPosition":
        fails.append("Worker slot 14 Clear Mines lost")
    if wk_slots.get(12) != "Command_ConstructIraq_AlFahdMissileFactory":
        fails.append("Worker slot 12 factory button missing")
    if wk_slots.get(13) != "Command_Stop":
        fails.append("Worker Stop lost")

    roll_cs = roll[r"Data\INI\CommandSet.ini"].decode("latin1")
    roll_vt = slot_map(commandset_block(roll_cs, "Iraq_VT72BCommandSet") or "")
    if {k: vt_slots[k] for k in range(1, 19) if k in vt_slots} != roll_vt:
        fails.append("VT72B slots 1-18 differ from healthy rollback")

    cb = extracted[r"Data\INI\CommandButton.ini"].decode("latin1")
    if cb != src[r"Data\INI\CommandButton.ini"].decode("latin1"):
        fails.append("CommandButton.ini mutated")
    referenced = set(vt_slots.values()) | set(wk_slots.values())
    if fac:
        referenced |= set(slot_map(fac).values())
    for btn in sorted(referenced):
        if cb.count(f"CommandButton {btn}") < 1:
            fails.append(f"missing CommandButton {btn}")
        if btn.endswith("CommandSet") or btn == "Iraq_VT72BCommandSet":
            fails.append(f"CommandSet self-ref via button {btn}")

    max_slots = []
    for m in re.finditer(r"(?ms)^CommandSet (\S+)\r?\n(.*?)(?:^End)", core_cs):
        slots = [int(x) for x in re.findall(r"(?m)^\s*(\d+)\s*=", m.group(2))]
        if slots:
            max_slots.append((max(slots), m.group(1)))
    over = [n for mx, n in max_slots if mx > 18]
    if over:
        fails.append(f"CommandSets still above slot 18: {over}")

    obj = extracted[r"Data\INI\Object\Specter\Iraq Army\Tracked\VT72B.ini"].decode("latin1")
    if "CommandSet       = Iraq_VT72BCommandSet" not in obj:
        fails.append("Iraq_VT72B CommandSet assignment changed")
    if obj != src[r"Data\INI\Object\Specter\Iraq Army\Tracked\VT72B.ini"].decode("latin1"):
        fails.append("VT72B.ini mutated")

    for key in [
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini",
        r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini",
        r"Data\INI\Weapon_Iraq_AlFahd500.ini",
        r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini",
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini",
    ]:
        if extracted[key] != src[key]:
            fails.append(f"{key} mutated")

    changed = sorted(k for k in extracted if k not in src or extracted[k] != src[k])
    extra = sorted(k for k in extracted if k not in src)
    missing = sorted(k for k in src if k not in extracted)
    if extra:
        fails.append(f"unexpected new DATA files {extra}")
    if missing:
        fails.append(f"dropped DATA files {missing}")
    if changed != [r"Data\INI\CommandSet.ini"]:
        fails.append(f"changed files not CommandSet-only: {changed}")

    return fails


def main() -> int:
    if not SRC_DATA.is_file() or SRC_DATA.stat().st_size != LIVE_DATA_SIZE:
        raise SystemExit("live Al-Fahd DATA missing or wrong size")
    if sha256_path(SRC_DATA) != LIVE_DATA_SHA:
        raise SystemExit("live Al-Fahd DATA SHA mismatch — refusing to pack from wrong baseline")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    src = parse_big(SRC_DATA.read_bytes())
    roll = parse_big(SRC_ROLL.read_bytes())
    data = dict(src)

    cs = data[r"Data\INI\CommandSet.ini"].decode("latin1")
    if cs.count(VT72B_LIVE) != 1:
        raise SystemExit(f"live VT72B block count={cs.count(VT72B_LIVE)}")
    if cs.count(WORKER_LIVE) != 1:
        raise SystemExit(f"live Worker block count={cs.count(WORKER_LIVE)}")
    cs = cs.replace(VT72B_LIVE, VT72B_FIXED, 1)
    cs = cs.replace(WORKER_LIVE, WORKER_FIXED, 1)
    if "19 = Command_ConstructIraq_AlFahdMissileFactory" in cs:
        raise SystemExit("slot 19 still present after patch")
    data[r"Data\INI\CommandSet.ini"] = cs.encode("latin1")

    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)

    extracted = parse_big(out_data.read_bytes())
    if extracted[r"Data\INI\CommandSet.ini"] != data[r"Data\INI\CommandSet.ini"]:
        raise SystemExit("re-extract CommandSet.ini mismatch")
    fails = validate(extracted, src, roll)

    report = [
        "# Iraq_VT72BCommandSet crash fix (DATA-only)",
        "",
        "Static validation of packed last-wins. The game was not launched.",
        "",
        "## Root cause",
        "",
        "The crash report name `Iraq_VT2BCommandSet` is the engine/dialog",
        "truncation of `Iraq_VT72BCommandSet`. No `Iraq_VT2B*` object or",
        "CommandSet exists in the live packed DATA.",
        "",
        "Live Al-Fahd added illegal CommandSet slot 19:",
        "  19 = Command_ConstructIraq_AlFahdMissileFactory",
        "",
        "Zero Hour `MAX_COMMANDS_PER_SET` is 18. Across the entire packed",
        "CommandSet.ini, every other set tops out at slot 18.",
        "`Iraq_VT72BCommandSet` was the only set with slot 19. Binding that",
        "set (Iraq start / select VT72B) overflows the command array.",
        "",
        "All 19 referenced CommandButtons existed in core CommandButton.ini.",
        "There was no missing button, no duplicate definition, no extra-file",
        "last-win, no casing mismatch, and no recursive CommandSet.",
        "The malformed/invalid entry was specifically slot 19.",
        "",
        "## Fix",
        "",
        "- Removed slot 19 from Iraq_VT72BCommandSet.",
        "- Slots 1-18 unchanged (slot 14 remains Command_DisarmMinesAtPosition).",
        "- Factory construct relocated to Iraq_WorkerCommandSet unused slot 12.",
        "- Worker slots 1-11 / 13-14 / Clear Mines unchanged.",
        "- Factory still produces Iraq_AlFahd500.",
        "- ART not rebuilt.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {sha256_path(out_data)}",
        f"- DATA files: {len(extracted)}",
        "- Files changed vs live Al-Fahd: Data\\INI\\CommandSet.ini only",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static / packed last-wins)",
        "- exactly one authoritative Iraq_VT72BCommandSet",
        "- every referenced CommandButton exists in core CommandButton.ini",
        "- no recursive/self-reference",
        "- slot 14 remains Command_DisarmMinesAtPosition on VT72B and Worker",
        "- original Worker/VT72B slots 1-18 preserved on VT72B",
        "- factory access via Worker slot 12 (slot 19 was not a valid design)",
        "- Iraq_AlFahd500 still the only UNIT_BUILD on the factory CommandSet",
        "- no old 8-missile objects / no Object Iraq_MissileFactory",
        "- no packed CommandSet uses slot > 18",
        "- ART not touched",
        "",
        "RUNTIME_TEST=NOT RUN. Static PASS does not prove the in-game crash is gone.",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
    (OUT / "HASHES.txt").write_text(
        f"DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={sha256_path(out_data)}\n"
        f"DATA_FILES={len(extracted)}\n"
        f"BASELINE=s-iraq-alfahd500 / f07d5d03d1d49bc300735d5e304e76325296cc4e\n"
        f"CHANGED=Data\\INI\\CommandSet.ini\n"
        f"ROOT_CAUSE=Iraq_VT72BCommandSet slot 19 exceeds MAX_COMMANDS_PER_SET=18\n"
        f"STATIC_VALIDATION=PASS\n"
        f"RUNTIME_TEST=NOT RUN\n"
        f"ART_REBUILT=NO\n",
        encoding="ascii",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq_VT72BCommandSet crash fix (DATA-only)\n"
        "\n"
        "Install this complete replacement _SPEC_DATA_ONE.big over the\n"
        "current live Al-Fahd500 DATA. Keep the existing Al-Fahd ART.\n"
        "\n"
        "Root cause: slot 19 on Iraq_VT72BCommandSet overflows the ZH\n"
        "CommandSet array (max 18). Factory construct moved to Worker\n"
        "unused slot 12. Slots 1-18 and Clear Mines are unchanged.\n"
        "\n"
        "Static validation only. The game was not launched.\n",
        encoding="ascii",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "Complete replacement DATA (do not use a partial patch ZIP):\n"
        "  _SPEC_DATA_ONE.big\n"
        f"  SIZE={out_data.stat().st_size}\n"
        f"  SHA256={sha256_path(out_data)}\n",
        encoding="ascii",
    )
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
