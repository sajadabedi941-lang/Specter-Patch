#!/usr/bin/env python3
"""Add the Iraq missile factory BUILDING button to other countries.

Baseline: PR #612 / s-iraq-haitham-najm-fire-color DATA+ART.

Only the construction button is transferred.
Do not copy Iraq missiles, roster, or factory production CommandSet.
Do not change missile objects, weapons, costs, or gameplay.
Do not re-add paid rearm.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_HAITHAM_NAJM_FIRE_COLOR/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_HAITHAM_NAJM_FIRE_COLOR/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_MISSILE_FACTORY_EXPORT"

SHA_DATA_612 = "21a7746b6a68203bedf306c3e96121fa6d916a1b059129963702e655f3228caf"
SIZE_DATA_612 = 366669703
SHA_ART_612 = "fa46c291d9cec1b106977e7a5ec3ded54e9bc0c9e2c94ab4d4852b90d4e96359"
SIZE_ART_612 = 1305667638

CS_KEY = r"Data\INI\CommandSet.ini"
PK_KEY = r"Data\INI\CommandSet_Pakistan.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
FACTORY_BTN = "Command_ConstructIraq_AlFahdMissileFactory"

# Live construction CommandSets from #612 object last-wins.
CLEAR_MINES_SETS = [
    "UkraineDozerCommandSet",
    "TurkeyDozerCommandSet",
    "ItalyDozerCommandSet",
    "SwedenDozerCommandSet",
    "BritainDozerCommandSet",
    "FranceDozerCommandSet",
    "GermanyDozerCommandSet",
    "NatoDozerCommandSet",
    "PLADozerCommandSet",  # live ChinaVehicleDozer
    "ChinaDozerCommandSet",
]

MIC_SETS = [
    "SouthKorea_VT72BCommandSet",
    "NorthKorea_VT72BCommandSet",
    "Vietnam_VT72BCommandSet",
    "Japan_VT72BCommandSet",
]

STOP_SETS_CS = [
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
]

STOP_SETS_PK = [
    "Pakistan_WorkerCommandSet",
    "Pakistan_VT72BCommandSet",
]

MISSILE_SETS = [
    "Iraq_AlFahdMissileFactoryCommandSet",
    "Iraq_AlhussaienCommandSet",
    "Iraq_AlhussaienArmedCommandSet",
    "Iraq_AlHaithamArmedCommandSet",
    "Iraq_AlAbbasCommandSet",
    "Iraq_WarFactoryCommandSet_T",
    "Iraq_WarFactoryCommandSet_T1",
    "Iraq_WarFactoryCommandSet_T2",
    "Iraq_WarFactoryCommandSet_T3",
    "Iraq_WarFactoryCommandSet",
    "Smerch_CommandSet",
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
        raise SystemExit("not BIGF")
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
    offset = header_size
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", 0)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    blobs = []
    for name, content in items:
        content = bytes(content)
        out += struct.pack(">II", offset, len(content))
        out += name.encode("latin1") + b"\x00"
        blobs.append(content)
        offset += len(content)
    out[4:8] = struct.pack(">I", offset)
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


def command_block(text: str, name: str) -> str | None:
    matches = list(re.finditer(rf"(?ms)^CommandSet {re.escape(name)}\r?\n.*?^End", text))
    return matches[-1].group(0) if matches else None


def slot_map(block: str | None) -> dict[int, str]:
    out: dict[int, str] = {}
    if not block:
        return out
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def splice_block(text: str, old: str, new: str) -> str:
    idx = text.rfind(old)
    if idx < 0:
        raise SystemExit("block splice failed")
    return text[:idx] + new + text[idx + len(old) :]


def replace_slot_button(block: str, pred, new_btn: str, set_name: str) -> str:
    slots = slot_map(block)
    hits = [slot for slot, btn in slots.items() if pred(slot, btn)]
    if len(hits) != 1:
        raise SystemExit(f"{set_name}: expected 1 target slot, got {hits} from {slots}")
    slot = hits[0]
    old_btn = slots[slot]
    new, n = re.subn(
        rf"^(\s*{slot}\s*=\s*){re.escape(old_btn)}\s*$",
        rf"\g<1>{new_btn}",
        block,
        count=1,
        flags=re.M,
    )
    if n != 1:
        raise SystemExit(f"{set_name}: slot {slot} replace failed")
    if slot_map(new).get(slot) != new_btn:
        raise SystemExit(f"{set_name}: slot {slot}={slot_map(new).get(slot)}")
    return new


def patch_named_sets(text: str, names: list[str], pred, label: str) -> str:
    for name in names:
        old = command_block(text, name)
        if not old:
            raise SystemExit(f"missing CommandSet {name} while patching {label}")
        new = replace_slot_button(old, pred, FACTORY_BTN, name)
        text = splice_block(text, old, new)
    return text


def add_russia_slot(text: str) -> str:
    old = command_block(text, "RussiaDozerCommandSet")
    if not old:
        raise SystemExit("missing RussiaDozerCommandSet")
    slots = slot_map(old)
    if 14 in slots:
        raise SystemExit(f"Russia slot 14 already occupied: {slots[14]}")
    if FACTORY_BTN in old:
        raise SystemExit("Russia already has factory button")
    end = re.search(r"^End", old, re.M)
    if not end:
        raise SystemExit("Russia End missing")
    nl = "\r\n" if "\r\n" in old else "\n"
    new = old[: end.start()] + f" 14 = {FACTORY_BTN}{nl}" + old[end.start() :]
    if slot_map(new).get(14) != FACTORY_BTN:
        raise SystemExit("Russia slot 14 insert failed")
    return splice_block(text, old, new)


def remove_iraq_factory(text: str) -> str:
    vt = command_block(text, "Iraq_VT72BCommandSet")
    if not vt:
        raise SystemExit("missing Iraq_VT72BCommandSet")
    if slot_map(vt).get(14) != FACTORY_BTN:
        raise SystemExit(f"Iraq VT72B slot 14={slot_map(vt).get(14)}")
    vt_new, n = re.subn(
        rf"^(\s*14\s*=\s*){re.escape(FACTORY_BTN)}\s*$",
        r"\1Command_DisarmMinesAtPosition",
        vt,
        count=1,
        flags=re.M,
    )
    if n != 1:
        raise SystemExit("Iraq VT72B factory remove failed")
    text = splice_block(text, vt, vt_new)

    wk = command_block(text, "Iraq_WorkerCommandSet")
    if not wk:
        raise SystemExit("missing Iraq_WorkerCommandSet")
    if slot_map(wk).get(12) != FACTORY_BTN:
        raise SystemExit(f"Iraq Worker slot 12={slot_map(wk).get(12)}")
    wk_new, n = re.subn(
        rf"^\s*12\s*=\s*{re.escape(FACTORY_BTN)}\s*\r?\n",
        "",
        wk,
        count=1,
        flags=re.M,
    )
    if n != 1 or FACTORY_BTN in wk_new:
        raise SystemExit("Iraq Worker factory remove failed")
    return splice_block(text, wk, wk_new)


def mines_pred(_slot: int, btn: str) -> bool:
    return btn == "Command_DisarmMinesAtPosition"


def mic_pred(_slot: int, btn: str) -> bool:
    return "MIC" in btn.upper()


def stop_pred(_slot: int, btn: str) -> bool:
    return btn == "Command_Stop"


def field(body: str | None, key: str) -> str:
    if not body:
        return ""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", body, re.M)
    return m.group(1).strip() if m else ""


def command_button(text: str, name: str) -> str | None:
    matches = list(re.finditer(rf"(?ms)^CommandButton {re.escape(name)}\r?\n.*?^End", text))
    return matches[-1].group(0) if matches else None


def validate(data: dict[str, bytes], art: dict[str, bytes], src_data: dict[str, bytes], src_art: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    if set(data) != set(src_data):
        fails.append("DATA file set changed")
    if art != src_art:
        fails.append("ART mutated")
    changed = sorted(k for k in src_data if src_data[k] != data.get(k))
    allowed = {CS_KEY, PK_KEY}
    unexpected = [k for k in changed if k not in allowed]
    if unexpected:
        fails.append(f"unexpected mutated files: {unexpected[:8]}")

    cs = data[CS_KEY].decode("latin1")
    src_cs = src_data[CS_KEY].decode("latin1")
    pk = data[PK_KEY].decode("latin1")
    src_pk = src_data[PK_KEY].decode("latin1")
    cb = data[CB_KEY].decode("latin1")
    factory = data[FACTORY_KEY].decode("latin1")
    src_factory = src_data[FACTORY_KEY].decode("latin1")

    if factory != src_factory:
        fails.append("factory object mutated")
    if "Object Iraq_AlFahdMissileFactory" not in factory:
        fails.append("missing Iraq_AlFahdMissileFactory")
    if field(factory, "BuildCost") != "1800":
        fails.append(f"factory BuildCost={field(factory, 'BuildCost')}")
    if field(factory, "BuildTime") != "20.0":
        fails.append(f"factory BuildTime={field(factory, 'BuildTime')}")
    if field(factory, "CommandSet") != "Iraq_AlFahdMissileFactoryCommandSet":
        fails.append("factory production CommandSet changed")
    if "Iraq_SupplyCenter" not in factory:
        fails.append("factory prerequisites changed")

    btn = command_button(cb, FACTORY_BTN)
    if field(btn, "Object") != "Iraq_AlFahdMissileFactory":
        fails.append(f"construct button Object={field(btn, 'Object')}")
    if field(btn, "Command") != "DOZER_CONSTRUCT":
        fails.append(f"construct Command={field(btn, 'Command')}")

    for name in CLEAR_MINES_SETS:
        slots = slot_map(command_block(cs, name))
        if FACTORY_BTN not in slots.values():
            fails.append(f"{name} missing factory button")
        if "Command_DisarmMinesAtPosition" in slots.values():
            fails.append(f"{name} still has Clear Mines")
        src_slots = slot_map(command_block(src_cs, name))
        factory_slots = [s for s, b in slots.items() if b == FACTORY_BTN]
        mine_slots = [s for s, b in src_slots.items() if b == "Command_DisarmMinesAtPosition"]
        if factory_slots != mine_slots:
            fails.append(f"{name} replaced {mine_slots} but now {factory_slots}")

    for name in MIC_SETS:
        slots = slot_map(command_block(cs, name))
        if slots.get(6) != FACTORY_BTN:
            fails.append(f"{name} slot 6={slots.get(6)}")
        if any("MIC" in b.upper() for b in slots.values()):
            fails.append(f"{name} still has MIC")

    for name in STOP_SETS_CS:
        slots = slot_map(command_block(cs, name))
        if FACTORY_BTN not in slots.values():
            fails.append(f"{name} missing factory button")
        if "Command_Stop" in slots.values():
            fails.append(f"{name} still has Stop")
        src_slots = slot_map(command_block(src_cs, name))
        factory_slots = [s for s, b in slots.items() if b == FACTORY_BTN]
        stop_slots = [s for s, b in src_slots.items() if b == "Command_Stop"]
        if factory_slots != stop_slots:
            fails.append(f"{name} replaced {stop_slots} but now {factory_slots}")

    for name in STOP_SETS_PK:
        slots = slot_map(command_block(pk, name))
        if FACTORY_BTN not in slots.values():
            fails.append(f"{name} missing factory button")
        if "Command_Stop" in slots.values():
            fails.append(f"{name} still has Stop")

    rus = slot_map(command_block(cs, "RussiaDozerCommandSet"))
    src_rus = slot_map(command_block(src_cs, "RussiaDozerCommandSet"))
    if rus.get(14) != FACTORY_BTN:
        fails.append(f"Russia slot 14={rus.get(14)}")
    if src_rus.get(14):
        fails.append("baseline Russia slot 14 was not empty")
    for slot, btn in src_rus.items():
        if rus.get(slot) != btn:
            fails.append(f"Russia replaced existing slot {slot}")

    iraq_vt = slot_map(command_block(cs, "Iraq_VT72BCommandSet"))
    iraq_wk = slot_map(command_block(cs, "Iraq_WorkerCommandSet"))
    if FACTORY_BTN in iraq_vt.values() or FACTORY_BTN in iraq_wk.values():
        fails.append("Iraq construction still has factory button")
    if iraq_vt.get(14) != "Command_DisarmMinesAtPosition":
        fails.append(f"Iraq VT72B slot 14={iraq_vt.get(14)}")

    for name in MISSILE_SETS:
        if command_block(cs, name) != command_block(src_cs, name):
            fails.append(f"missile CommandSet mutated: {name}")

    factory_cs = command_block(cs, "Iraq_AlFahdMissileFactoryCommandSet") or ""
    if FACTORY_BTN in factory_cs:
        fails.append("factory production menu gained construct button")
    if "CB_MISSILE_" not in factory_cs:
        fails.append("factory production roster missing")

    if data[CB_KEY] != src_data[CB_KEY]:
        fails.append("CommandButton.ini mutated")

    blob = "\n".join(
        data[k].decode("latin1", errors="ignore")
        for k in (CS_KEY, PK_KEY, FACTORY_KEY)
    )
    for banned in (
        "Upgrade_Rearm_Iraq_Alhussaien",
        "Upgrade_Rearm_Iraq_AlHaitham",
        "Command_ConstructIraq_AlNajm",
        "Command_ConstructIraq_AlHaitham",
    ):
        if banned in blob and banned not in src_cs + src_pk:
            fails.append(f"new missile transfer residue: {banned}")
    return fails


def write_extracts(out_data: bytes) -> None:
    packed = parse_big(out_data)
    ext = OUT / "LAST_WINS_EXTRACT/DATA"
    ext.mkdir(parents=True, exist_ok=True)
    cs = packed[CS_KEY].decode("latin1")
    pk = packed[PK_KEY].decode("latin1")
    names = (
        CLEAR_MINES_SETS
        + MIC_SETS
        + STOP_SETS_CS
        + ["RussiaDozerCommandSet", "Iraq_VT72BCommandSet", "Iraq_WorkerCommandSet"]
    )
    chunks = [command_block(cs, n) for n in names]
    chunks += [command_block(pk, n) for n in STOP_SETS_PK]
    (ext / "ConstructionCommandSets.ini").write_text(
        "\n\n".join(c for c in chunks if c) + "\n", encoding="latin1"
    )
    (ext / "Iraq_AlFahdMissileFactoryCommandSet.ini").write_text(
        (command_block(cs, "Iraq_AlFahdMissileFactoryCommandSet") or "") + "\n",
        encoding="latin1",
    )


def main() -> int:
    if SRC_DATA.stat().st_size != SIZE_DATA_612 or sha256_path(SRC_DATA) != SHA_DATA_612:
        raise SystemExit("DATA baseline is not PR #612")
    if SRC_ART.stat().st_size != SIZE_ART_612 or sha256_path(SRC_ART) != SHA_ART_612:
        raise SystemExit("ART baseline is not PR #612")

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    cs = data[CS_KEY].decode("latin1")
    cs = patch_named_sets(cs, CLEAR_MINES_SETS, mines_pred, "clear-mines")
    cs = patch_named_sets(cs, MIC_SETS, mic_pred, "mic")
    cs = patch_named_sets(cs, STOP_SETS_CS, stop_pred, "stop")
    cs = add_russia_slot(cs)
    cs = remove_iraq_factory(cs)
    data[CS_KEY] = cs.encode("latin1")

    pk = data[PK_KEY].decode("latin1")
    pk = patch_named_sets(pk, STOP_SETS_PK, stop_pred, "pakistan-stop")
    data[PK_KEY] = pk.encode("latin1")

    fails = validate(data, art, src_data, src_art)
    out_data = build_big(data)
    out_art = build_big(art)
    fails.extend([f"DATA {x}" for x in big_structure_ok(out_data)])
    fails.extend([f"ART {x}" for x in big_structure_ok(out_art)])
    fails.extend(validate(parse_big(out_data), parse_big(out_art), src_data, src_art))
    if fails:
        raise SystemExit("VALIDATION FAIL\n" + "\n".join(fails))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_SPEC_DATA_ONE.big").write_bytes(out_data)
    (OUT / "_SPEC_ART_ONE.big").write_bytes(out_art)
    data_sha = sha256_path(OUT / "_SPEC_DATA_ONE.big")
    art_sha = sha256_path(OUT / "_SPEC_ART_ONE.big")
    write_extracts(out_data)

    report = [
        "SPECTER missile factory building button export",
        f"DATA {len(out_data)} {data_sha}",
        f"ART  {len(out_art)} {art_sha}",
        "",
        "BUILDING ONLY:",
        "  Same Iraq_AlFahdMissileFactory object / model / health / cost / time.",
        "  Factory production CommandSet unchanged. No missiles transferred.",
        "  Iraq construct button removed from VT72B/Worker.",
        "",
        "SLOTS:",
        "  Group1 Clear Mines -> factory on EU/NATO/China dozers.",
        "  Group2 MIC -> factory on SK/NK/Vietnam/Japan VT72B.",
        "  Group3 Stop -> factory on India/Pakistan/Saudi/UAE/Syria/Libya/SA construction sets.",
        "  Russia empty slot 14 -> factory. No existing Russia command replaced.",
        "",
        "STATIC_VALIDATION=PASS",
        "RUNTIME_TEST=NOT RUN",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=NO\n"
        f"DATA_SIZE={len(out_data)}\n"
        f"DATA_SHA256={data_sha}\n"
        f"ART_SIZE={len(out_art)}\n"
        f"ART_SHA256={art_sha}\n"
        "BASELINE=PR #612\n"
        "FACTORY_OBJECT=Iraq_AlFahdMissileFactory\n"
        "MISSILES_TRANSFERRED=NO\n"
        "PAID_REARM=NONE\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Iraq missile factory BUILDING button added to listed countries.\n"
        "No missiles, roster, or factory production menu were copied.\n"
        "Place both complete replacement BIGs in the SPECTER folder.\n"
        "STATIC ONLY.\n",
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Missile factory building button export\n"
        "\n"
        "- Adds only `Command_ConstructIraq_AlFahdMissileFactory` to listed countries.\n"
        "- Same Iraq factory object. No missile units or production CommandSets copied.\n"
        "- Iraq construction units no longer have the factory build button.\n",
        encoding="utf-8",
    )
    (OUT / "CONFLICTS.txt").write_text(
        "Replaces Clear Mines / MIC / Stop on the listed construction CommandSets.\n"
        "Russia uses previously empty slot 14.\n"
        "STATIC ONLY.\n",
        encoding="utf-8",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "DATA/ART/ZIP links are filled after the GitHub Release is published.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_MISSILE_FACTORY_EXPORT.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
        zf.write(OUT / "RELEASE_NOTES.md", "RELEASE_NOTES.md")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size} sha={sha256_path(zip_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
