#!/usr/bin/env python3
"""Isolate Iraq missile roster from the exported factory building.

Baseline: PR #620 SPECTER_MENA7_CONSTRUCT_BTNS
  DATA 366677659 SHA fbf7748816d2229b8819ea05c8fbe0917d72362a10b4b7a809dafd7236e07f33
  ART  1306997028 SHA d487dd508857a496502bfee0fd5919210346db0d83b80832289035002a0dbdc3

Read-only audit of packed last-wins:

- All 21 assigned countries construct Command_ConstructIraq_AlFahdMissileFactory
  -> Object Iraq_AlFahdMissileFactory
  -> CommandSet Iraq_AlFahdMissileFactoryCommandSet
  -> CB_MISSILE_A..M (Iraq_AlFahd500 .. Iraq_BM-21).
- No country-prefixed CommandSet received CB_MISSILE_* or a copied roster.
  The only post-#612 diffs are the intended factory construct-button slots.
- Pre-existing WarFactory Command_ConstructIraq_Alhussaien buttons (Saudi/UAE/
  Syria/Libya/SouthAfrica) are unchanged since #612 and are out of scope.
- Iraq factory object CommandSet and roster are identical to #612 except the
  #614 supply-center OR prerequisite, which is preserved.

Fix: assigned countries construct a building-only clone with Sell only.
Iraq keeps Iraq_AlFahdMissileFactory + Iraq_AlFahdMissileFactoryCommandSet.
ART and construction-button images are unchanged.
Static validation only.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_MENA7_CONSTRUCT_BTNS/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_MENA7_CONSTRUCT_BTNS/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_FACTORY_ROSTER_ISOLATE"
LOOSE_OBJ = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Buildings/Iraq_AlFahdMissileFactoryBuilding.ini"
LOOSE_CB = ROOT / "patch/Data/INI/CommandButton.ini"

SHA_DATA_620 = "fbf7748816d2229b8819ea05c8fbe0917d72362a10b4b7a809dafd7236e07f33"
SIZE_DATA_620 = 366677659
SHA_ART_620 = "d487dd508857a496502bfee0fd5919210346db0d83b80832289035002a0dbdc3"
SIZE_ART_620 = 1306997028

CS_KEY = r"Data\INI\CommandSet.ini"
PK_KEY = r"Data\INI\CommandSet_Pakistan.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
BUILDING_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactoryBuilding.ini"

FACTORY_BTN = "Command_ConstructIraq_AlFahdMissileFactory"
FACTORY_OBJ = "Iraq_AlFahdMissileFactory"
FACTORY_CS = "Iraq_AlFahdMissileFactoryCommandSet"
BUILDING_BTN = "Command_ConstructIraq_AlFahdMissileFactoryBuilding"
BUILDING_OBJ = "Iraq_AlFahdMissileFactoryBuilding"
BUILDING_CS = "Iraq_AlFahdMissileFactoryBuildingCommandSet"

IRAQ_ROSTER = {
    1: ("CB_MISSILE_A", "Iraq_AlFahd500"),
    2: ("CB_MISSILE_B", "Iraq_AlHusseinII"),
    3: ("CB_MISSILE_C", "Iraq_AlSamoudII"),
    4: ("CB_MISSILE_D", "Iraq_AlAbbas"),
    5: ("CB_MISSILE_E", "Iraq_Sarab7"),
    6: ("CB_MISSILE_F", "Iraq_AlNajm"),
    7: ("CB_MISSILE_G", "Iraq_R11ScudB"),
    8: ("CB_MISSILE_H", "Iraq_AlBasrah"),
    9: ("CB_MISSILE_I", "Iraq_AlNasir"),
    10: ("CB_MISSILE_J", "Iraq_AlMansour"),
    11: ("CB_MISSILE_K", "Iraq_Alhussaien"),
    12: ("CB_MISSILE_L", "Iraq_AlHaitham"),
    13: ("CB_MISSILE_M", "Iraq_BM-21"),
    14: ("Command_Sell", ""),
}

CS_SETS = [
    "PLADozerCommandSet",
    "ChinaDozerCommandSet",
    "RussiaDozerCommandSet",
    "BritainDozerCommandSet",
    "GermanyDozerCommandSet",
    "FranceDozerCommandSet",
    "ItalyDozerCommandSet",
    "UkraineDozerCommandSet",
    "SwedenDozerCommandSet",
    "TurkeyDozerCommandSet",
    "NatoDozerCommandSet",
    "IndiaDozerCommandSet",
    "India_WorkerCommandSet",
    "India_VT72BCommandSet",
    "PakistanDozerCommandSet",
    "SaudiArabiaDozerCommandSet",
    "SaudiArabia_WorkerCommandSet",
    "SaudiArabia_VT72BCommandSet",
    "UAEDozerCommandSet",
    "UAE_WorkerCommandSet",
    "UAE_VT72BCommandSet",
    "SyriaDozerCommandSet",
    "Syria_WorkerCommandSet",
    "Syria_VT72BCommandSet",
    "LibyaDozerCommandSet",
    "Libya_WorkerCommandSet",
    "Libya_VT72BCommandSet",
    "SouthAfricaDozerCommandSet",
    "SouthAfrica_WorkerCommandSet",
    "SouthAfrica_VT72BCommandSet",
    "SouthKorea_VT72BCommandSet",
    "NorthKorea_VT72BCommandSet",
    "Vietnam_VT72BCommandSet",
    "Japan_VT72BCommandSet",
]

PK_SETS = [
    "Pakistan_WorkerCommandSet",
    "Pakistan_VT72BCommandSet",
]

COUNTRIES = [
    ("China", ["PLADozerCommandSet", "ChinaDozerCommandSet"]),
    ("Russia", ["RussiaDozerCommandSet"]),
    ("Britain", ["BritainDozerCommandSet"]),
    ("Germany", ["GermanyDozerCommandSet"]),
    ("France", ["FranceDozerCommandSet"]),
    ("Italy", ["ItalyDozerCommandSet"]),
    ("Ukraine", ["UkraineDozerCommandSet"]),
    ("Sweden", ["SwedenDozerCommandSet"]),
    ("Turkey", ["TurkeyDozerCommandSet"]),
    ("NATO", ["NatoDozerCommandSet"]),
    ("Saudi Arabia", ["SaudiArabiaDozerCommandSet", "SaudiArabia_VT72BCommandSet", "SaudiArabia_WorkerCommandSet"]),
    ("UAE", ["UAEDozerCommandSet", "UAE_VT72BCommandSet", "UAE_WorkerCommandSet"]),
    ("Syria", ["SyriaDozerCommandSet", "Syria_VT72BCommandSet", "Syria_WorkerCommandSet"]),
    ("India", ["IndiaDozerCommandSet", "India_VT72BCommandSet", "India_WorkerCommandSet"]),
    ("Pakistan", ["PakistanDozerCommandSet", "Pakistan_VT72BCommandSet", "Pakistan_WorkerCommandSet"]),
    ("Libya", ["LibyaDozerCommandSet", "Libya_VT72BCommandSet", "Libya_WorkerCommandSet"]),
    ("South Africa", ["SouthAfricaDozerCommandSet", "SouthAfrica_VT72BCommandSet", "SouthAfrica_WorkerCommandSet"]),
    ("Japan", ["Japan_VT72BCommandSet"]),
    ("Vietnam", ["Vietnam_VT72BCommandSet"]),
    ("South Korea", ["SouthKorea_VT72BCommandSet"]),
    ("North Korea", ["NorthKorea_VT72BCommandSet"]),
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
    files = {}
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


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def command_block(text: str, kind: str, name: str) -> str | None:
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text))
    return matches[-1].group(0) if matches else None


def slot_map(block: str | None) -> dict[int, str]:
    out: dict[int, str] = {}
    if not block:
        return out
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def field(body: str | None, key: str) -> str:
    if not body:
        return ""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(\S+)", body, re.M)
    return m.group(1) if m else ""


def splice_block(text: str, old: str, new: str) -> str:
    idx = text.rfind(old)
    if idx < 0:
        raise SystemExit("block splice failed")
    return text[:idx] + new + text[idx + len(old) :]


def retarget_sets(text: str, names: list[str]) -> str:
    for name in names:
        old = command_block(text, "CommandSet", name)
        if not old:
            raise SystemExit(f"missing CommandSet {name}")
        slots = slot_map(old)
        hits = [s for s, b in slots.items() if b == FACTORY_BTN]
        if len(hits) != 1:
            raise SystemExit(f"{name}: expected 1 factory construct slot, got {hits}")
        new, n = re.subn(
            rf"^(\s*{hits[0]}\s*=\s*){re.escape(FACTORY_BTN)}\s*$",
            rf"\g<1>{BUILDING_BTN}",
            old,
            count=1,
            flags=re.M,
        )
        if n != 1 or slot_map(new).get(hits[0]) != BUILDING_BTN:
            raise SystemExit(f"{name}: retarget failed")
        if slot_map(new) != {**slots, hits[0]: BUILDING_BTN}:
            raise SystemExit(f"{name}: unexpected slot mutation")
        text = splice_block(text, old, new)
    return text


def append_block(text: str, block: str) -> str:
    nl = "\r\n" if "\r\n" in text else "\n"
    body = text.rstrip("\x00")
    block = block.replace("\r\n", "\n").replace("\r", "\n").replace("\n", nl)
    if not body.endswith(nl):
        body += nl
    return body + nl + block + nl


def make_building_object(factory_ini: str) -> str:
    text = factory_ini
    text = text.replace(f"Object {FACTORY_OBJ}", f"Object {BUILDING_OBJ}", 1)
    text = re.sub(
        rf"^(\s*CommandSet\s*=\s*){re.escape(FACTORY_CS)}\s*$",
        rf"\g<1>{BUILDING_CS}",
        text,
        count=1,
        flags=re.M,
    )
    if f"Object {BUILDING_OBJ}" not in text or field(text, "CommandSet") != BUILDING_CS:
        raise SystemExit("building object clone failed")
    if field(text, "BuildCost") != field(factory_ini, "BuildCost"):
        raise SystemExit("BuildCost drifted")
    if field(text, "BuildTime") != field(factory_ini, "BuildTime"):
        raise SystemExit("BuildTime drifted")
    return text


def make_building_button(factory_btn: str) -> str:
    text = factory_btn.replace(
        f"CommandButton {FACTORY_BTN}",
        f"CommandButton {BUILDING_BTN}",
        1,
    )
    text = re.sub(
        rf"^(\s*Object\s*=\s*){re.escape(FACTORY_OBJ)}\s*$",
        rf"\g<1>{BUILDING_OBJ}",
        text,
        count=1,
        flags=re.M,
    )
    if field(text, "Object") != BUILDING_OBJ:
        raise SystemExit("building button Object failed")
    if field(text, "ButtonImage") != field(factory_btn, "ButtonImage"):
        raise SystemExit("ButtonImage drifted")
    if field(text, "Command") != "DOZER_CONSTRUCT":
        raise SystemExit("construct Command drifted")
    return text


def make_building_commandset() -> str:
    return f"CommandSet {BUILDING_CS}\n  14 = Command_Sell\nEnd"


def last_cs(data: dict[str, bytes], name: str) -> str:
    last = ""
    for key in (CS_KEY, PK_KEY):
        block = command_block(data[key].decode("latin1"), "CommandSet", name)
        if block:
            last = block
    return last


def last_btn(data: dict[str, bytes], name: str) -> str:
    return command_block(data[CB_KEY].decode("latin1"), "CommandButton", name) or ""


def validate(data, art, src_data, src_art) -> list[str]:
    fails: list[str] = []
    added = set(data) - set(src_data)
    if added != {BUILDING_KEY}:
        fails.append(f"DATA added unexpected {added}")
    if set(src_data) - set(data):
        fails.append("DATA removed files")
    mutated = sorted(k for k in src_data if src_data[k] != data.get(k))
    if mutated != [CB_KEY, CS_KEY, PK_KEY]:
        fails.append(f"unexpected DATA mutations: {mutated}")
    if art != src_art:
        fails.append("ART mutated")
    if data[FACTORY_KEY] != src_data[FACTORY_KEY]:
        fails.append("Iraq factory object mutated")

    src_cs = src_data[CS_KEY].decode("latin1")
    new_cs = data[CS_KEY].decode("latin1")
    src_pk = src_data[PK_KEY].decode("latin1")
    new_pk = data[PK_KEY].decode("latin1")

    if command_block(new_cs, "CommandSet", FACTORY_CS) != command_block(src_cs, "CommandSet", FACTORY_CS):
        fails.append("Iraq factory production CommandSet mutated")
    iraq_vt = command_block(new_cs, "CommandSet", "Iraq_VT72BCommandSet")
    src_iraq_vt = command_block(src_cs, "CommandSet", "Iraq_VT72BCommandSet")
    if iraq_vt != src_iraq_vt:
        fails.append("Iraq_VT72BCommandSet mutated")
    if slot_map(iraq_vt).get(14) != FACTORY_BTN:
        fails.append("Iraq lost original factory construct button")

    src_factory_btn = command_block(src_data[CB_KEY].decode("latin1"), "CommandButton", FACTORY_BTN)
    new_factory_btn = command_block(data[CB_KEY].decode("latin1"), "CommandButton", FACTORY_BTN)
    if src_factory_btn != new_factory_btn:
        fails.append("original factory construct button mutated")

    bld_btn = command_block(data[CB_KEY].decode("latin1"), "CommandButton", BUILDING_BTN)
    if field(bld_btn, "Object") != BUILDING_OBJ:
        fails.append("building button Object wrong")
    if field(bld_btn, "ButtonImage") != "Button_MissileFactory":
        fails.append("building button image changed")
    if field(bld_btn, "Command") != "DOZER_CONSTRUCT":
        fails.append("building button Command wrong")

    bld_obj = data[BUILDING_KEY].decode("latin1")
    fac_obj = data[FACTORY_KEY].decode("latin1")
    if field(bld_obj, "CommandSet") != BUILDING_CS:
        fails.append("building object CommandSet wrong")
    if field(bld_obj, "BuildCost") != field(fac_obj, "BuildCost"):
        fails.append("building BuildCost drifted")
    if field(bld_obj, "BuildTime") != field(fac_obj, "BuildTime"):
        fails.append("building BuildTime drifted")
    if field(fac_obj, "CommandSet") != FACTORY_CS:
        fails.append("Iraq factory CommandSet drifted")

    bld_cs = command_block(new_cs, "CommandSet", BUILDING_CS)
    if slot_map(bld_cs) != {14: "Command_Sell"}:
        fails.append(f"building CommandSet slots={slot_map(bld_cs)}")
    if "CB_MISSILE_" in (bld_cs or ""):
        fails.append("building CommandSet still has Iraq missiles")

    fac_cs = command_block(new_cs, "CommandSet", FACTORY_CS)
    fac_slots = slot_map(fac_cs)
    for slot, (btn, obj) in IRAQ_ROSTER.items():
        if fac_slots.get(slot) != btn:
            fails.append(f"Iraq roster slot {slot}={fac_slots.get(slot)}")
        if obj:
            body = command_block(data[CB_KEY].decode("latin1"), "CommandButton", btn)
            if field(body, "Object") != obj:
                fails.append(f"{btn} Object={field(body, 'Object')}")

    for name in CS_SETS:
        src_slots = slot_map(command_block(src_cs, "CommandSet", name))
        new_slots = slot_map(command_block(new_cs, "CommandSet", name))
        hits = [s for s, b in src_slots.items() if b == FACTORY_BTN]
        if len(hits) != 1:
            fails.append(f"baseline {name} factory slots {hits}")
            continue
        slot = hits[0]
        expect = {**src_slots, slot: BUILDING_BTN}
        if new_slots != expect:
            fails.append(f"{name} slots drifted: {new_slots}")
        if FACTORY_BTN in new_slots.values():
            fails.append(f"{name} still constructs Iraq factory object")
        if "CB_MISSILE_" in (command_block(new_cs, "CommandSet", name) or ""):
            fails.append(f"{name} gained missile roster")

    for name in PK_SETS:
        src_slots = slot_map(command_block(src_pk, "CommandSet", name))
        new_slots = slot_map(command_block(new_pk, "CommandSet", name))
        hits = [s for s, b in src_slots.items() if b == FACTORY_BTN]
        if len(hits) != 1:
            fails.append(f"baseline {name} factory slots {hits}")
            continue
        expect = {**src_slots, hits[0]: BUILDING_BTN}
        if new_slots != expect:
            fails.append(f"{name} PK slots drifted")

    # Pre-existing war-factory Alhussaien buttons must remain.
    for name in (
        "SaudiArabia_WarFactoryCommandSet",
        "UAE_WarFactoryCommandSet",
        "Syria_WarFactoryCommandSet",
        "Libya_WarFactoryCommandSet",
        "SouthAfrica_WarFactoryCommandSet",
    ):
        if command_block(new_cs, "CommandSet", name) != command_block(src_cs, "CommandSet", name):
            fails.append(f"unrelated WF mutated: {name}")
    return fails


def inventory_lines(data: dict[str, bytes]) -> list[str]:
    lines = [
        "STATIC AUDIT / FIX REPORT",
        "RUNTIME TEST: NOT RUN",
        "",
        "Iraq factory object: Iraq_AlFahdMissileFactory (UNCHANGED)",
        f"Iraq factory CommandSet: {FACTORY_CS} (UNCHANGED)",
        "Iraq construct button: Command_ConstructIraq_AlFahdMissileFactory -> Iraq_AlFahdMissileFactory (UNCHANGED)",
        "",
        "Assigned-country factory now constructs Iraq_AlFahdMissileFactoryBuilding",
        "with CommandSet Iraq_AlFahdMissileFactoryBuildingCommandSet = Sell only.",
        "No missile production menu was invented.",
        "",
    ]
    cb = data[CB_KEY].decode("latin1")
    for country, sets in COUNTRIES:
        lines.append(f"# {country}")
        for name in sets:
            body = last_cs(data, name)
            slots = slot_map(body)
            fac = [(s, b) for s, b in slots.items() if "MissileFactory" in b]
            lines.append(f"## {name}")
            if not fac:
                lines.append("  factory construct button: MISSING")
                continue
            for slot, btn in fac:
                block = command_block(cb, "CommandButton", btn) or ""
                obj = field(block, "Object")
                obj_block = ""
                if obj == BUILDING_OBJ:
                    obj_block = data[BUILDING_KEY].decode("latin1")
                elif obj == FACTORY_OBJ:
                    obj_block = data[FACTORY_KEY].decode("latin1")
                prod = field(obj_block, "CommandSet")
                prod_block = last_cs(data, prod)
                units = []
                for s, b in slot_map(prod_block).items():
                    bbody = command_block(cb, "CommandButton", b) or ""
                    if field(bbody, "Command") == "UNIT_BUILD":
                        units.append(field(bbody, "Object"))
                iraq_refs = [u for u in units if u.startswith("Iraq_")]
                lines.append(
                    f"  slot {slot} | {btn} | {obj} | prod={prod} | "
                    f"units={units or ['(none)']} | Iraq-specific production={bool(iraq_refs)} | "
                    f"action={'retargeted to building-only factory' if obj == BUILDING_OBJ else 'NONE'}"
                )
        lines.append(
            "  pre-transfer: no factory / no factory missile menu. "
            "War-factory Alhussaien (if present) is pre-#613 and was left unchanged."
        )
        lines.append("")
    return lines


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_620 or SRC_DATA.stat().st_size != SIZE_DATA_620:
        raise SystemExit("DATA baseline mismatch")
    if sha256_path(SRC_ART) != SHA_ART_620 or SRC_ART.stat().st_size != SIZE_ART_620:
        raise SystemExit("ART baseline mismatch")

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    factory_ini = src_data[FACTORY_KEY].decode("latin1")
    cb_text = src_data[CB_KEY].decode("latin1")
    cs_text = src_data[CS_KEY].decode("latin1")
    pk_text = src_data[PK_KEY].decode("latin1")
    factory_btn = command_block(cb_text, "CommandButton", FACTORY_BTN)
    if not factory_btn:
        raise SystemExit("missing factory construct button")

    building_ini = make_building_object(factory_ini)
    building_btn = make_building_button(factory_btn)
    building_cs = make_building_commandset()

    data[BUILDING_KEY] = building_ini.encode("latin1")
    data[CB_KEY] = append_block(cb_text, building_btn).encode("latin1")
    cs_text = retarget_sets(cs_text, CS_SETS)
    cs_text = append_block(cs_text, building_cs)
    data[CS_KEY] = cs_text.encode("latin1")
    data[PK_KEY] = retarget_sets(pk_text, PK_SETS).encode("latin1")

    fails = validate(data, art, src_data, src_art)
    data_big = build_big(data)
    art_big = build_big(art)
    fails.extend(f"DATA {x}" for x in big_structure_ok(data_big))
    fails.extend(f"ART {x}" for x in big_structure_ok(art_big))
    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    LOOSE_OBJ.parent.mkdir(parents=True, exist_ok=True)
    LOOSE_OBJ.write_text(building_ini.replace("\r\n", "\n"), encoding="latin1")
    if LOOSE_CB.is_file() and BUILDING_BTN.encode("ascii") not in LOOSE_CB.read_bytes():
        raw = LOOSE_CB.read_text(encoding="latin1")
        LOOSE_CB.write_text(raw.rstrip() + "\n\n" + building_btn.replace("\r\n", "\n") + "\n", encoding="latin1")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_big)
    art_path.write_bytes(art_big)

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    inv = inventory_lines(data)
    (ext / "Iraq_AlFahdMissileFactory.ini").write_bytes(data[FACTORY_KEY])
    (ext / "Iraq_AlFahdMissileFactoryBuilding.ini").write_bytes(data[BUILDING_KEY])
    (ext / "Iraq_AlFahdMissileFactoryCommandSet.ini").write_text(
        command_block(data[CS_KEY].decode("latin1"), "CommandSet", FACTORY_CS) + "\n"
    )
    (ext / "Iraq_AlFahdMissileFactoryBuildingCommandSet.ini").write_text(
        command_block(data[CS_KEY].decode("latin1"), "CommandSet", BUILDING_CS) + "\n"
    )
    assigned = [last_cs(data, n) for n, _ in ((s, None) for s in CS_SETS + PK_SETS)]
    (ext / "AssignedBuilderCommandSets.ini").write_text("\n\n".join(assigned) + "\n")
    (ext / "INVENTORY.txt").write_text("\n".join(inv) + "\n")

    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_FACTORY_ROSTER_ISOLATE.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #620 s-mena7-construct-btns",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "ART_UNCHANGED=YES",
        "IRAQ_FACTORY_OBJECT_UNCHANGED=YES",
        "IRAQ_FACTORY_COMMANDSET_UNCHANGED=YES",
        "IRAQ_VT72B_FACTORY_BUTTON_RETAINED=YES",
        "CONSTRUCTION_BUTTON_IMAGES_UNCHANGED=YES",
        "",
        "CONFIRMED TRANSFER:",
        "  Shared construct button built Iraq_AlFahdMissileFactory, whose CommandSet",
        "  is Iraq_AlFahdMissileFactoryCommandSet (CB_MISSILE_A..M).",
        "  Country-prefixed CommandSets did not copy the roster; the object reference did.",
        "",
        "CORRECTIVE ACTION:",
        "  Assigned countries now construct Iraq_AlFahdMissileFactoryBuilding",
        "  (same model/cost/time/health/prereqs, Sell-only CommandSet).",
        "  Iraq factory object, roster, and Iraq construct button are unchanged.",
        "  Pre-existing war-factory Alhussaien buttons were not part of #613 and were left alone.",
        "",
        *inv,
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n")
    hashes = "\n".join(
        [
            "DATA_CHANGED=YES",
            "ART_CHANGED=NO",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_SIZE={art_path.stat().st_size}",
            f"ART_SHA256={art_sha}",
            "ZIP_FILE=SPECTER_FACTORY_ROSTER_ISOLATE.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #620",
            "STATIC_VALIDATION=PASS",
            "RUNTIME_TEST=NOT RUN",
            "",
        ]
    )
    (OUT / "HASHES.txt").write_text(hashes)
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-factory-roster-isolate/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-factory-roster-isolate/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-factory-roster-isolate/SPECTER_FACTORY_ROSTER_ISOLATE.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-factory-roster-isolate",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-factory-roster-isolate",
                "BASELINE=PR #620",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Assigned countries keep the Iraq missile factory BUILDING but no longer\n"
        "receive Iraq_AlFahdMissileFactoryCommandSet (missiles A-M).\n"
        "Iraq factory object and roster are unchanged. ART unchanged.\n"
        "Static validation only.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Isolate Iraq missile roster from the exported factory building\n\n"
        "- The 21 assigned countries still construct the Iraq missile factory building.\n"
        "- They now build a building-only clone with a Sell-only CommandSet.\n"
        "- Iraq's factory object, A-M roster, and Iraq construct button are unchanged.\n"
        "- Construction-button images and ART are unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "New object Iraq_AlFahdMissileFactoryBuilding and CommandSet/button names are unique.\n"
        "Iraq_AlFahdMissileFactory last-wins path is unchanged.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n")
    print("PACKED")
    print(hashes)
    print("\n".join(report[:35]))


if __name__ == "__main__":
    main()
