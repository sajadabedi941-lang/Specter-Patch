#!/usr/bin/env python3
"""Replace VT72B Clear Mines with the Missile Factory construct.

Live baseline: s-iraq-factory-visible
  366368035  SHA256 95e5331c29f161c570586d7b18dee1e43670e128817d6fe6f08feb84349296ab

Playable builder is Iraq_VT72B -> Iraq_VT72BCommandSet.
Clear Mines is slot 14. Factory currently occupies slot 15 (previous fix).

Requested behavior:
  14 = Command_ConstructIraq_AlFahdMissileFactory
  15 = Command_ConstructIraq_Abbas_AI
  no Command_DisarmMinesAtPosition on Iraq_VT72BCommandSet
  no second factory button, no slot 19

ART not rebuilt. Static validation only. The game is not launched.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_VISIBLE/_SPEC_DATA_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_SLOT14"

LIVE_DATA_SHA = "95e5331c29f161c570586d7b18dee1e43670e128817d6fe6f08feb84349296ab"
LIVE_DATA_SIZE = 366368035

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
    "  15 = Command_ConstructIraq_AlFahdMissileFactory\r\n"
    "  16 = Command_ConstructIraqFahad3SamSite\r\n"
    "  17 = Command_ConstructIraqMilitaryWarfactory\r\n"
    "  18 = Command_Stop\r\n"
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
    "  14 = Command_ConstructIraq_AlFahdMissileFactory\r\n"
    "  15 = Command_ConstructIraq_Abbas_AI\r\n"
    "  16 = Command_ConstructIraqFahad3SamSite\r\n"
    "  17 = Command_ConstructIraqMilitaryWarfactory\r\n"
    "  18 = Command_Stop\r\n"
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


def validate(extracted: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    all_ini = b"\n".join(v for k, v in extracted.items() if k.lower().endswith(".ini"))
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
        fails.append("Iraq_VT72BCommandSet definition count")

    extra_hits = []
    for k, v in extracted.items():
        if k.lower() == r"data\ini\commandset.ini" or not k.lower().endswith(".ini"):
            continue
        if b"CommandSet Iraq_VT72BCommandSet" in v:
            extra_hits.append(k)
    if extra_hits:
        fails.append(f"extra last-win CommandSet {extra_hits}")

    vt = commandset_block(core_cs, "Iraq_VT72BCommandSet")
    if vt != VT72B_FIXED:
        fails.append("Iraq_VT72BCommandSet block mismatch")
    vt_slots = slot_map(vt or "")
    if any(s > 18 for s in vt_slots):
        fails.append("slot > 18 present")
    if 19 in vt_slots:
        fails.append("illegal slot 19 present")
    if vt_slots.get(14) != "Command_ConstructIraq_AlFahdMissileFactory":
        fails.append("slot 14 is not factory")
    if vt_slots.get(15) != "Command_ConstructIraq_Abbas_AI":
        fails.append("slot 15 not restored to Abbas_AI")
    if "Command_DisarmMinesAtPosition" in (vt or ""):
        fails.append("Clear Mines still on Iraq_VT72BCommandSet")
    factory_slots = [s for s, b in vt_slots.items() if b == "Command_ConstructIraq_AlFahdMissileFactory"]
    if factory_slots != [14]:
        fails.append(f"factory slots {factory_slots}")

    over = []
    for m in re.finditer(r"(?ms)^CommandSet (\S+)\r?\n(.*?)(?:^End)", core_cs):
        slots = [int(x) for x in re.findall(r"(?m)^\s*(\d+)\s*=", m.group(2))]
        if slots and max(slots) > 18:
            over.append(m.group(1))
    if over:
        fails.append(f"CommandSets still above slot 18: {over}")

    cb = extracted[r"Data\INI\CommandButton.ini"].decode("latin1")
    if cb != src[r"Data\INI\CommandButton.ini"].decode("latin1"):
        fails.append("CommandButton.ini mutated")
    btn = re.search(
        r"(?ms)^CommandButton Command_ConstructIraq_AlFahdMissileFactory\r?\n.*?^End", cb
    )
    if not btn or "Object           = Iraq_AlFahdMissileFactory" not in btn.group(0):
        fails.append("factory CommandButton missing or wrong Object")
    if not btn or "Command          = DOZER_CONSTRUCT" not in btn.group(0):
        fails.append("factory button not DOZER_CONSTRUCT")

    fac = commandset_block(core_cs, "Iraq_AlFahdMissileFactoryCommandSet")
    if not fac or "1  = Command_ConstructIraq_AlFahd500" not in fac:
        fails.append("factory CommandSet missing AlFahd500")

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
        r"Data\INI\Object\Specter\Iraq Army\Infantry\Iraq_Worker.ini",
        r"Data\English\generals.csf",
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
        raise SystemExit("factory-visible DATA missing or wrong size")
    if sha256_path(SRC_DATA) != LIVE_DATA_SHA:
        raise SystemExit("factory-visible DATA SHA mismatch")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)
    cs = data[r"Data\INI\CommandSet.ini"].decode("latin1")
    if cs.count(VT72B_LIVE) != 1:
        raise SystemExit(f"live VT72B block count={cs.count(VT72B_LIVE)}")
    cs = cs.replace(VT72B_LIVE, VT72B_FIXED, 1)
    if "19 = Command_ConstructIraq_AlFahdMissileFactory" in cs:
        raise SystemExit("slot 19 present")
    data[r"Data\INI\CommandSet.ini"] = cs.encode("latin1")

    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    extracted = parse_big(out_data.read_bytes())
    if extracted[r"Data\INI\CommandSet.ini"] != data[r"Data\INI\CommandSet.ini"]:
        raise SystemExit("re-extract CommandSet.ini mismatch")
    fails = validate(extracted, src)

    report = [
        "# Iraq VT72B: Clear Mines replaced by Missile Factory",
        "",
        "Static validation of packed last-wins. The game was not launched.",
        "",
        "Playable object: Iraq_VT72B",
        "CommandSet: Iraq_VT72BCommandSet (exactly one, no extra last-win)",
        "Old slot 14: Command_DisarmMinesAtPosition",
        "New slot 14: Command_ConstructIraq_AlFahdMissileFactory",
        "Slot 15 restored: Command_ConstructIraq_Abbas_AI",
        "CommandButton: Command_ConstructIraq_AlFahdMissileFactory",
        "Factory object: Iraq_AlFahdMissileFactory (produces Iraq_AlFahd500)",
        "No slot 19. No second factory button on VT72B. ART not rebuilt.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {sha256_path(out_data)}",
        f"- DATA files: {len(extracted)}",
        "- Files changed: Data\\INI\\CommandSet.ini only",
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
        "- slot 14 factory; slot 15 Abbas_AI; Clear Mines gone from VT72B",
        "- factory CommandButton Object = Iraq_AlFahdMissileFactory",
        "- factory CommandSet still builds Iraq_AlFahd500",
        "- no CommandSet slot > 18; crash-fix slot 19 not reintroduced",
        "- no old 8-missile objects / no Object Iraq_MissileFactory",
        "- ART not touched",
        "",
        "RUNTIME_TEST=NOT RUN",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
    (OUT / "HASHES.txt").write_text(
        f"DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={sha256_path(out_data)}\n"
        f"DATA_FILES={len(extracted)}\n"
        f"BASELINE=s-iraq-factory-visible / 1f03e385e985f77d43275e2772087eeebe054160\n"
        f"CHANGED=Data\\INI\\CommandSet.ini\n"
        f"VT72B_SLOT14=Command_ConstructIraq_AlFahdMissileFactory\n"
        f"VT72B_SLOT15=Command_ConstructIraq_Abbas_AI\n"
        f"CLEAR_MINES_ON_VT72B=NO\n"
        f"STATIC_VALIDATION=PASS\n"
        f"RUNTIME_TEST=NOT RUN\n"
        f"ART_REBUILT=NO\n",
        encoding="ascii",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq VT72B: Missile Factory replaces Clear Mines (DATA-only)\n"
        "\n"
        "Install this complete replacement _SPEC_DATA_ONE.big over the\n"
        "current live factory-visible DATA. Keep the existing Al-Fahd ART.\n"
        "\n"
        "Iraq_VT72BCommandSet slot 14 is now the Missile Factory.\n"
        "Slot 15 is restored to Abbas_AI. Clear Mines is gone from VT72B.\n"
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
