#!/usr/bin/env python3
"""Make the Al-Fahd Missile Factory button visible on the live Iraq builder.

Root cause
----------
The crash-fix pack put Command_ConstructIraq_AlFahdMissileFactory on
Iraq_WorkerCommandSet slot 12. That chain is internally valid, but the
player never sees it:

  StartingUnit0 = Iraq_VT72B
  Command Center slot 1 = Command_ConstructIraq_VT72B
  Command_ConstructIraq_Worker exists only as a CommandButton definition
    and is referenced by ZERO CommandSets
  Iraq_SupplyCenter produces Ural375 supply trucks, not Iraq_Worker

The unit with Clear Mines that the player actually selects is Iraq_VT72B
(Iraq_VT72BCommandSet). That set has no factory button. Slots 1-18 are
full. Slot 15 is Command_ConstructIraq_Abbas_AI — same portrait/text as
slot 11 Command_ConstructIraq_Abbas (human Abbas). Abbas_AI is the
cheaper AI-priced duplicate.

Fix
---
Replace VT72B slot 15 (Abbas_AI duplicate) with the factory construct.
Keep Worker slot 12 (map-placed workers). Keep slot 14 Clear Mines.
Do not use slot 19. Do not rebuild ART.

Authority baseline: s-iraq-vt72b-commandset-fix DATA
  366368023  SHA256 a9edfd222bf1964a34423bf882fb730bdf9dc7f46d064cb9325eeee7d9e675dd
Static validation only. The game is not launched.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_VT72B_CRASHFIX/_SPEC_DATA_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_VISIBLE"

LIVE_DATA_SHA = "a9edfd222bf1964a34423bf882fb730bdf9dc7f46d064cb9325eeee7d9e675dd"
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
    "End"
)

VT72B_FIXED = VT72B_LIVE.replace(
    "  15 = Command_ConstructIraq_Abbas_AI\r\n",
    "  15 = Command_ConstructIraq_AlFahdMissileFactory\r\n",
)

WORKER_KEEP = (
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


def validate(extracted: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    all_ini = b"\n".join(v for k, v in extracted.items() if k.lower().endswith(".ini"))

    if b"Iraq_VT2BCommandSet" in all_ini:
        fails.append("Iraq_VT2BCommandSet appeared")
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
    if core_cs.count("CommandSet Iraq_WorkerCommandSet") != 1:
        fails.append("Iraq_WorkerCommandSet definition count")

    extra_hits = []
    for k, v in extracted.items():
        if k.lower() == r"data\ini\commandset.ini" or not k.lower().endswith(".ini"):
            continue
        if b"CommandSet Iraq_VT72BCommandSet" in v or b"CommandSet Iraq_WorkerCommandSet" in v:
            extra_hits.append(k)
    if extra_hits:
        fails.append(f"extra last-win CommandSet {extra_hits}")

    vt = commandset_block(core_cs, "Iraq_VT72BCommandSet")
    wk = commandset_block(core_cs, "Iraq_WorkerCommandSet")
    fac = commandset_block(core_cs, "Iraq_AlFahdMissileFactoryCommandSet")
    if vt != VT72B_FIXED:
        fails.append("Iraq_VT72BCommandSet block mismatch")
    if wk != WORKER_KEEP:
        fails.append("Iraq_WorkerCommandSet changed")
    if not fac or "1  = Command_ConstructIraq_AlFahd500" not in fac:
        fails.append("factory CommandSet missing AlFahd500")

    vt_slots = slot_map(vt or "")
    wk_slots = slot_map(wk or "")
    if any(s > 18 for s in list(vt_slots) + list(wk_slots)):
        fails.append("slot > 18 present")
    if 19 in vt_slots or 19 in wk_slots:
        fails.append("illegal slot 19 present")
    if vt_slots.get(14) != "Command_DisarmMinesAtPosition":
        fails.append("VT72B Clear Mines lost")
    if wk_slots.get(14) != "Command_DisarmMinesAtPosition":
        fails.append("Worker Clear Mines lost")
    if vt_slots.get(15) != "Command_ConstructIraq_AlFahdMissileFactory":
        fails.append("VT72B slot 15 factory missing")
    if vt_slots.get(11) != "Command_ConstructIraq_Abbas":
        fails.append("human Abbas slot 11 lost")
    if wk_slots.get(12) != "Command_ConstructIraq_AlFahdMissileFactory":
        fails.append("Worker slot 12 factory missing")

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
    if not btn:
        fails.append("factory CommandButton missing")
    else:
        if "Command          = DOZER_CONSTRUCT" not in btn.group(0):
            fails.append("factory button not DOZER_CONSTRUCT")
        if "Object           = Iraq_AlFahdMissileFactory" not in btn.group(0):
            fails.append("factory button Object mismatch")
        if re.search(r"(?m)^\s*(Science|Upgrade|SpecialPower)\s*=", btn.group(0)):
            fails.append("factory button has hide/lock fields")

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

    # Worker still untrainable — documented, not a fail, but factory must be on VT72B.
    if all_ini.count(b"Command_ConstructIraq_Worker") == 1:
        # button def only is expected
        pass
    return fails


def main() -> int:
    if not SRC_DATA.is_file() or SRC_DATA.stat().st_size != LIVE_DATA_SIZE:
        raise SystemExit("crash-fix DATA missing or wrong size")
    if sha256_path(SRC_DATA) != LIVE_DATA_SHA:
        raise SystemExit("crash-fix DATA SHA mismatch — refusing to pack from wrong baseline")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)

    cs = data[r"Data\INI\CommandSet.ini"].decode("latin1")
    if cs.count(VT72B_LIVE) != 1:
        raise SystemExit(f"live VT72B block count={cs.count(VT72B_LIVE)}")
    if cs.count(WORKER_KEEP) != 1:
        raise SystemExit(f"live Worker block count={cs.count(WORKER_KEEP)}")
    cs = cs.replace(VT72B_LIVE, VT72B_FIXED, 1)
    if "19 = Command_ConstructIraq_AlFahdMissileFactory" in cs:
        raise SystemExit("slot 19 reintroduced")
    data[r"Data\INI\CommandSet.ini"] = cs.encode("latin1")

    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)

    extracted = parse_big(out_data.read_bytes())
    if extracted[r"Data\INI\CommandSet.ini"] != data[r"Data\INI\CommandSet.ini"]:
        raise SystemExit("re-extract CommandSet.ini mismatch")
    fails = validate(extracted, src)

    report = [
        "# Iraq Missile Factory button visibility (DATA-only)",
        "",
        "Static validation of packed last-wins. The game was not launched.",
        "",
        "## Root cause",
        "",
        "The factory CommandButton and Worker slot 12 were valid, but the",
        "player never selects Iraq_Worker.",
        "",
        "Assigned CommandSets:",
        "  Object Iraq_VT72B  -> Iraq_VT72BCommandSet   (StartingUnit0)",
        "  Object Iraq_Worker -> Iraq_WorkerCommandSet  (untrainable)",
        "",
        "Command_ConstructIraq_Worker is not referenced by any CommandSet.",
        "Command Center produces Iraq_VT72B. Supply Center produces Ural375.",
        "The command bar that still showed Clear Mines is Iraq_VT72BCommandSet",
        "slot 14. That set had no factory button. Slot 12 on the Worker set",
        "is unreachable in normal play.",
        "",
        "The factory button itself is valid (DOZER_CONSTRUCT, Object =",
        "Iraq_AlFahdMissileFactory, ButtonImage irq_warfctry present,",
        "no Science/Upgrade/SpecialPower hide fields).",
        "",
        "VT72B slots 1-18 were all occupied. Slot 15 Command_ConstructIraq_Abbas_AI",
        "is the legitimate duplicate of slot 11 Command_ConstructIraq_Abbas",
        "(same ButtonImage irq_alhussien, same TextLabel, cheaper AI object).",
        "",
        "## Fix",
        "",
        "- Iraq_VT72BCommandSet slot 15 = Command_ConstructIraq_AlFahdMissileFactory",
        "- slot 11 Abbas kept; slot 14 Clear Mines kept; no slot 19",
        "- Iraq_WorkerCommandSet slot 12 factory kept for map-placed workers",
        "- Worker slot 14 Clear Mines kept",
        "- factory still produces Iraq_AlFahd500; ART not rebuilt",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {sha256_path(out_data)}",
        f"- DATA files: {len(extracted)}",
        "- Files changed vs crash-fix DATA: Data\\INI\\CommandSet.ini only",
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
        "- exactly one Iraq_VT72BCommandSet and one Iraq_WorkerCommandSet",
        "- factory button on reachable VT72B slot 15",
        "- CommandButton Command_ConstructIraq_AlFahdMissileFactory -> Iraq_AlFahdMissileFactory",
        "- factory CommandSet still builds Iraq_AlFahd500",
        "- Clear Mines remains slot 14 on VT72B and Worker",
        "- no CommandSet slot > 18; crash-fix slot 19 not reintroduced",
        "- no old 8-missile objects / no Object Iraq_MissileFactory",
        "- ART not touched",
        "",
        "RUNTIME_TEST=NOT RUN. Static PASS does not prove in-game visibility.",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
    (OUT / "HASHES.txt").write_text(
        f"DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={sha256_path(out_data)}\n"
        f"DATA_FILES={len(extracted)}\n"
        f"BASELINE=s-iraq-vt72b-commandset-fix / a3163815e75112050d9638552f1c5e6f60bbd0fd\n"
        f"CHANGED=Data\\INI\\CommandSet.ini\n"
        f"ROOT_CAUSE=factory was on untrainable Iraq_WorkerCommandSet; player uses Iraq_VT72BCommandSet\n"
        f"FACTORY_SLOT=Iraq_VT72BCommandSet slot 15\n"
        f"CLEAR_MINES=slot 14\n"
        f"STATIC_VALIDATION=PASS\n"
        f"RUNTIME_TEST=NOT RUN\n"
        f"ART_REBUILT=NO\n",
        encoding="ascii",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq Missile Factory visibility fix (DATA-only)\n"
        "\n"
        "Install this complete replacement _SPEC_DATA_ONE.big over the\n"
        "current live crash-fix DATA. Keep the existing Al-Fahd ART.\n"
        "\n"
        "Root cause: factory button was on Iraq_Worker, which Iraq cannot\n"
        "train. The in-game builder is Iraq_VT72B. Factory is now VT72B\n"
        "slot 15 (replaced duplicate Abbas_AI). Clear Mines stays slot 14.\n"
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
