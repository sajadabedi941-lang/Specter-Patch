#!/usr/bin/env python3
"""Move three Iraq M.I.C. production items onto Iraq War Factory.

Baseline packed archives: SPECTER_IRAQ_MIC_START (PR #661).
ART_ONE / ART_TWO are copied byte-identical. DATA last-wins overlay only.

Packed last-wins audit (PR #661 DATA, not guessed):
  Iraq_MIC CommandSet = Iraq_MICCommandSet
    slot 2 Command_ConstructIraq_Karrar2    -> UNIT_BUILD Iraq_Karrar2   ButtonImage irq_karrar
    slot 4 Command_ConstructIraqVehicleB340 -> UNIT_BUILD IraqVehicleB340 ButtonImage irq_b340
    slot 5 Command_ConstructIraqVehicleFahad3 -> UNIT_BUILD IraqVehicleFahad3 ButtonImage irq_fahad3
  Iraq_MICCommandSet2 / Iraq_MICCommandSet3 are identical copies (unused by the object).
  Iraq_WarFactory_T / Iraq_WarFactory CommandSet = Iraq_WarFactoryCommandSet_T3
    slots 1-8, 11, 14 occupied; 9, 10, 12 free
  Iraq_Karrar2 Prerequisites Object = Iraq_MIC (preserved on the object)
  B340 and Fahad3 have empty Prerequisites
  MappedImage irq_b340 / irq_karrar / irq_fahad3 already exist
  Iraq dozer slot 6 remains Command_ConstructIraq_MIC; Iraq_MIC Prerequisites empty

Smallest safe change: last-wins CommandSet overlay only.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MIC_START/_SPEC_DATA_ONE.big"
SRC_ART1 = ROOT / "patch/Release/SPECTER_IRAQ_MIC_START/_SPEC_ART_ONE.big"
SRC_ART2 = ROOT / "patch/Release/SPECTER_IRAQ_MIC_START/_SPEC_ART_TWO.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MIC_TO_WF"
INSTALLER = ROOT / "patch/tools/installer"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "1c28234616150754afc9c63c0dc445e95c3b02be807d083a5bfa838667479252"
SIZE_DATA_SRC = 370744758
SHA_ART1_SRC = "dd53835d7119e7609d2bd955879f234da83a0c6c650d7d7ed1194385d9bbd0f2"
SIZE_ART1_SRC = 2144061050
SHA_ART2_SRC = "daf5e3bb3d4b0f763fee4bd39ceafa06000b9c7261f538a0e84a7b6b54fb7f21"
SIZE_ART2_SRC = 307234369
SAGE_SAFE = 2147483648

CS_KEY = r"Data\INI\CommandSet_ZZZZ_IraqMicToWf.ini"
MIC_OBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_MIC.ini"
WF_OBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory.ini"
AA_WF_KEY = r"Data\INI\Object\Specter\Arabic Alliance\Buildings\Warfactory.ini"

MIC_CS_NAMES = (
    "Iraq_MICCommandSet",
    "Iraq_MICCommandSet2",
    "Iraq_MICCommandSet3",
)
WF_CS_NAME = "Iraq_WarFactoryCommandSet_T3"
IRAQ_DOZER_CS = "Iraq_VT72BCommandSet"
IRAQ_WORKER_CS = "Iraq_WorkerCommandSet"
MIC_CMD = "Command_ConstructIraq_MIC"
AA_WF_CMD = "Command_ConstructArabicArmy_WarFactory"
MOVE_CMDS = (
    "Command_ConstructIraqVehicleB340",
    "Command_ConstructIraq_Karrar2",
    "Command_ConstructIraqVehicleFahad3",
)
MOVE_OBJS = {
    "Command_ConstructIraqVehicleB340": "IraqVehicleB340",
    "Command_ConstructIraq_Karrar2": "Iraq_Karrar2",
    "Command_ConstructIraqVehicleFahad3": "IraqVehicleFahad3",
}
MOVE_ART = {
    "Command_ConstructIraqVehicleB340": "irq_b340",
    "Command_ConstructIraq_Karrar2": "irq_karrar",
    "Command_ConstructIraqVehicleFahad3": "irq_fahad3",
}
WF_NEW_SLOTS = {
    "9": "Command_ConstructIraqVehicleB340",
    "10": "Command_ConstructIraq_Karrar2",
    "12": "Command_ConstructIraqVehicleFahad3",
}
SLOT_RE = re.compile(r"(?m)^([ \t]*)(\d+)([ \t]*=[ \t]*)(\S+)[ \t]*\r?$")

FROZEN = [
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\PlayerTemplate.ini",
    MIC_OBJ_KEY,
    WF_OBJ_KEY,
    AA_WF_KEY,
    r"Data\INI\Object\Specter\Iraq Army\AirDefense\B340.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Karrar-2.ini",
    r"Data\INI\Object\Specter\Iraq Army\AirDefense\Fahad3.ini",
    r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini",
]


def last_block(text: str, kind: str, name: str) -> str:
    ms = list(
        re.finditer(
            rf"(?ms)^{kind} {re.escape(name)}\s*\r?\n.*?(?:^End|^END)\s*$",
            text,
        )
    )
    return ms[-1].group(0) if ms else ""


def last_from(order, files, kind, name):
    found = ("", "")
    needle = f"{kind} {name}".encode("ascii", errors="replace")
    for key in order:
        blob = files.get(key, b"")
        if needle not in blob:
            continue
        block = last_block(blob.decode("latin1"), kind, name)
        if block:
            found = (key, block)
    return found


def field(block: str, key: str) -> str:
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block or "")
    if not m:
        return ""
    return m.group(1).split(";")[0].strip()


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_commandsets(order, files) -> dict[str, str]:
    cs_map = {}
    for key in order:
        if "commandset" not in key.lower() or not key.lower().endswith(".ini"):
            continue
        text = files[key].decode("latin1")
        for m in re.finditer(
            r"(?ms)^CommandSet (\S+)\s*\r?\n.*?(?:^End|^END)\s*$", text
        ):
            cs_map[m.group(1)] = m.group(0)
    return cs_map


def slot_map(block: str) -> dict[str, str]:
    return {m.group(2): m.group(4) for m in SLOT_RE.finditer(block or "")}


def strip_move_cmds(block: str, name: str) -> str:
    if not all(cmd in block for cmd in MOVE_CMDS):
        raise SystemExit(f"{name} missing one of the three move commands")
    out_lines = []
    for line in block.splitlines(True):
        m = SLOT_RE.match(line.replace("\r\n", "\n").replace("\r", "\n"))
        # SLOT_RE is ^...$ on a single line; handle CRLF by checking command token
        cmd_m = re.match(r"[ \t]*\d+[ \t]*=[ \t]*(\S+)", line)
        if cmd_m and cmd_m.group(1) in MOVE_CMDS:
            continue
        out_lines.append(line)
    new = "".join(out_lines)
    if any(cmd in new for cmd in MOVE_CMDS):
        raise SystemExit(f"{name} still contains a moved command")
    return new


def add_wf_slots(block: str) -> str:
    slots = slot_map(block)
    for num, cmd in WF_NEW_SLOTS.items():
        if num in slots:
            raise SystemExit(f"War Factory slot {num} already used by {slots[num]}")
        if cmd in block:
            raise SystemExit(f"War Factory already has {cmd}")
    slots.update(WF_NEW_SLOTS)
    indent_m = re.search(r"(?m)^([ \t]*)\d+", block)
    indent = indent_m.group(1) if indent_m else "  "
    lines = [f"CommandSet {WF_CS_NAME}\r\n"]
    for num in sorted(slots, key=int):
        lines.append(f"{indent}{num} = {slots[num]}\r\n")
    lines.append("End\r\n")
    return "".join(lines)


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_IRAQ_MIC_START")
    if sha256_path(SRC_ART1) != SHA_ART1_SRC or SRC_ART1.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE baseline mismatch")
    if sha256_path(SRC_ART2) != SHA_ART2_SRC or SRC_ART2.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO baseline mismatch")

    files, order = sk.parse_big_ordered(SRC_DATA.read_bytes())
    original = dict(files)
    cs_map = collect_commandsets(order, files)

    overlays = []
    for name in MIC_CS_NAMES:
        raw = cs_map.get(name)
        if not raw:
            raise SystemExit(f"missing CommandSet {name}")
        overlays.append(strip_move_cmds(raw, name))
    wf_raw = cs_map.get(WF_CS_NAME)
    if not wf_raw:
        raise SystemExit(f"missing CommandSet {WF_CS_NAME}")
    overlays.append(add_wf_slots(wf_raw))
    files[CS_KEY] = sk.to_crlf("\n\n".join(overlays) + "\n")

    for key in FROZEN:
        if files.get(key) != original.get(key):
            raise SystemExit(f"frozen mutated: {key}")

    data_big = sk.build_big(files)
    packed, packed_order = sk.parse_big_ordered(data_big)

    fails = []
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))

    packed_cs = collect_commandsets(packed_order, packed)
    src_dozer, dozer = last_from(packed_order, packed, "CommandSet", IRAQ_DOZER_CS)
    src_worker, worker = last_from(packed_order, packed, "CommandSet", IRAQ_WORKER_CS)
    src_mic_obj, mic_obj = last_from(packed_order, packed, "Object", "Iraq_MIC")
    src_wf_obj, wf_obj = last_from(packed_order, packed, "Object", "Iraq_WarFactory_T")
    src_aa, aa_obj = last_from(packed_order, packed, "Object", "ArabicArmy_WarFactory")

    for name in MIC_CS_NAMES:
        src, blk = last_from(packed_order, packed, "CommandSet", name)
        if src != CS_KEY:
            fails.append(f"{name} last-wins {src}")
        for cmd in MOVE_CMDS:
            if cmd in blk:
                fails.append(f"{name} still offers {cmd}")
        leftover = set(slot_map(cs_map[name]).values()) - set(MOVE_CMDS)
        now = set(slot_map(blk).values())
        if leftover != now:
            fails.append(f"{name} unrelated slots changed {sorted(leftover ^ now)}")

    src_wf_cs, wf_cs = last_from(packed_order, packed, "CommandSet", WF_CS_NAME)
    if src_wf_cs != CS_KEY:
        fails.append(f"{WF_CS_NAME} last-wins {src_wf_cs}")
    wf_slots = slot_map(wf_cs)
    for num, cmd in WF_NEW_SLOTS.items():
        if wf_slots.get(num) != cmd:
            fails.append(f"WF slot {num} is {wf_slots.get(num)}")
    orig_wf = set(slot_map(cs_map[WF_CS_NAME]).values())
    new_wf = set(wf_slots.values())
    if orig_wf - new_wf:
        fails.append(f"WF lost {sorted(orig_wf - new_wf)}")
    if new_wf - orig_wf != set(MOVE_CMDS):
        fails.append(f"WF extra/missing move cmds {sorted(new_wf ^ orig_wf ^ set(MOVE_CMDS))}")
    if len(wf_slots) != len(set(wf_slots)):
        fails.append("WF duplicate slots")
    if len(list(wf_slots.values())) != len(set(wf_slots.values())):
        fails.append("WF duplicate commands")

    for cmd, obj in MOVE_OBJS.items():
        src_btn, btn = last_from(packed_order, packed, "CommandButton", cmd)
        if field(btn, "Command") != "UNIT_BUILD":
            fails.append(f"{cmd} is not UNIT_BUILD")
        if field(btn, "Object") != obj:
            fails.append(f"{cmd} Object={field(btn, 'Object')}")
        if field(btn, "ButtonImage") != MOVE_ART[cmd]:
            fails.append(f"{cmd} ButtonImage={field(btn, 'ButtonImage')}")
        src_o, o = last_from(packed_order, packed, "Object", obj)
        if not o:
            fails.append(f"missing Object {obj}")
        if packed.get(src_o) != original.get(src_o):
            fails.append(f"object file mutated {src_o}")

    src_k, karrar = last_from(packed_order, packed, "Object", "Iraq_Karrar2")
    if "Iraq_MIC" not in (karrar or ""):
        fails.append("Iraq_Karrar2 lost Iraq_MIC prerequisite")

    if field(mic_obj, "CommandSet") != "Iraq_MICCommandSet":
        fails.append("Iraq_MIC CommandSet changed")
    mic_prereq = re.search(r"(?ms)^\s*Prerequisites\s*\r?\n.*?(?:^\s*End)\s*$", mic_obj or "")
    if mic_prereq and re.search(r"(?m)^\s*Object\s*=", mic_prereq.group(0)):
        fails.append("Iraq_MIC regained object prerequisites")
    dozer_slots = slot_map(dozer)
    if dozer_slots.get("6") != MIC_CMD:
        fails.append(f"Iraq dozer slot 6 is {dozer_slots.get('6')}")
    if AA_WF_CMD in dozer or AA_WF_CMD in worker:
        fails.append("AA War Factory leaked onto Iraq construction menu")
    if field(wf_obj, "CommandSet") != WF_CS_NAME:
        fails.append(f"Iraq_WarFactory_T CommandSet={field(wf_obj, 'CommandSet')}")
    aa_prereq = re.search(r"(?ms)^\s*Prerequisites\s*\r?\n.*?(?:^\s*End)\s*$", aa_obj or "")
    if aa_prereq and "Iraq_" in aa_prereq.group(0):
        fails.append("Arabic Alliance War Factory gained Iraq prereq")

    for name, blk in packed_cs.items():
        if name in MIC_CS_NAMES or name == WF_CS_NAME:
            continue
        orig = cs_map.get(name, "")
        gained = [c for c in MOVE_CMDS if c not in orig and c in blk]
        if gained:
            fails.append(f"out-of-scope {name} gained {gained}")

    allowed = {CS_KEY}
    for key in original:
        if key in allowed:
            continue
        if packed.get(key) != original[key]:
            fails.append(f"unrelated mutated {key}")

    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art1_path = OUT / "_SPEC_ART_ONE.big"
    art2_path = OUT / "_SPEC_ART_TWO.big"
    data_path.write_bytes(data_big)
    shutil.copy2(SRC_ART1, art1_path)
    shutil.copy2(SRC_ART2, art2_path)
    (LOOSE / "CommandSet_ZZZZ_IraqMicToWf.ini").write_bytes(files[CS_KEY])

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    for name in MIC_CS_NAMES:
        _, blk = last_from(packed_order, packed, "CommandSet", name)
        (ext / f"{name}.ini").write_text(blk + "\n", encoding="utf-8")
    (ext / f"{WF_CS_NAME}.ini").write_text(wf_cs + "\n", encoding="utf-8")
    for cmd in MOVE_CMDS:
        _, btn = last_from(packed_order, packed, "CommandButton", cmd)
        (ext / f"{cmd}.ini").write_text(btn + "\n", encoding="utf-8")

    (OUT / "INSTALL.txt").write_text(
        "\n".join(
            [
                "SPECTER IRAQ M.I.C. -> WAR FACTORY TRANSFER — INSTALL",
                "",
                "Keep the split ART arrangement. Do not recombine ART.",
                "Place all three uncompressed BIGs next to generals.exe:",
                "  _SPEC_DATA_ONE.big",
                "  _SPEC_ART_ONE.big",
                "  _SPEC_ART_TWO.big",
                "",
                "Zero Hour auto-loads every *.big in that folder.",
                "Each .big must start with BIGF. Do not install gzip as .big.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "Moved Command_ConstructIraqVehicleB340, Command_ConstructIraq_Karrar2, "
        "and Command_ConstructIraqVehicleFahad3 from Iraq_MICCommandSet to "
        "Iraq_WarFactoryCommandSet_T3.\n"
        "ART unchanged. RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    zip_path = OUT / "SPECTER_IRAQ_MIC_TO_WF.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "_SPEC_ART_TWO.big",
            "INSTALL.txt",
            "README.txt",
            "Launch_Specter.bat",
            "Install_SpecterPatch.bat",
        ):
            zf.write(OUT / name, name)

    if sha256_path(art1_path) != SHA_ART1_SRC or art1_path.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE copy is not byte-identical")
    if sha256_path(art2_path) != SHA_ART2_SRC or art2_path.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO copy is not byte-identical")
    if art1_path.stat().st_size >= SAGE_SAFE or art2_path.stat().st_size >= SAGE_SAFE:
        raise SystemExit("ART archive exceeds SAGE 2GiB signed offset limit")

    data_sha = sha256_path(data_path)
    art1_sha = sha256_path(art1_path)
    art2_sha = sha256_path(art2_path)
    zip_sha = sha256_path(zip_path)
    tag = "s-iraq-mic-to-wf"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/" + tag
    )
    changed = [CS_KEY, "patch/Data/INI/CommandSet_ZZZZ_IraqMicToWf.ini"]

    report = "\n".join(
        [
            "STATIC VALIDATION: PASS",
            "RUNTIME_TEST=NOT RUN",
            "BASELINE: PR #661 SPECTER_IRAQ_MIC_START",
            "ART_ONE_UNCHANGED=YES",
            "ART_TWO_UNCHANGED=YES",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_ONE_SIZE={art1_path.stat().st_size}",
            f"ART_ONE_SHA256={art1_sha}",
            f"ART_TWO_SIZE={art2_path.stat().st_size}",
            f"ART_TWO_SHA256={art2_sha}",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            f"CHANGED_PACKED_FILES={CS_KEY}",
            "MIC_REMOVED=Command_ConstructIraqVehicleB340,Command_ConstructIraq_Karrar2,Command_ConstructIraqVehicleFahad3",
            "WF_ADDED_SLOTS=9,10,12",
            "WF_COMMANDSET=Iraq_WarFactoryCommandSet_T3",
            "MIC_START_GAME_PRESERVED=YES",
            "OBJECTS_UNCHANGED=YES",
            "ART_CHANGED=NO",
            "RUNTIME_TEST=NOT RUN",
            "",
        ]
    )
    (OUT / "VALIDATE_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "\n".join(
            [
                "DATA_CHANGED=YES",
                "ART_CHANGED=NO",
                f"DATA_SIZE={data_path.stat().st_size}",
                f"DATA_SHA256={data_sha}",
                f"ART_ONE_SIZE={art1_path.stat().st_size}",
                f"ART_ONE_SHA256={art1_sha}",
                f"ART_TWO_SIZE={art2_path.stat().st_size}",
                f"ART_TWO_SHA256={art2_sha}",
                "ZIP_FILE=SPECTER_IRAQ_MIC_TO_WF.zip",
                f"ZIP_SIZE={zip_path.stat().st_size}",
                f"ZIP_SHA256={zip_sha}",
                "BASELINE=PR #661",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA:",
                f"  {rel_base}/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART textures (unchanged):",
                f"  {rel_base}/_SPEC_ART_ONE.big",
                f"  SIZE={art1_path.stat().st_size}",
                f"  SHA256={art1_sha}",
                "",
                "ART models (unchanged):",
                f"  {rel_base}/_SPEC_ART_TWO.big",
                f"  SIZE={art2_path.stat().st_size}",
                f"  SHA256={art2_sha}",
                "",
                "ZIP:",
                f"  {rel_base}/SPECTER_IRAQ_MIC_TO_WF.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                f"TAG={tag}",
                f"RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/{tag}",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "\n".join(
            [
                "# Iraq: move B_340Radar, karrar_2, fahad_3 from M.I.C. to War Factory",
                "",
                "Removed from `Iraq_MICCommandSet` (and unused copies 2/3):",
                "- `Command_ConstructIraqVehicleB340` (`IraqVehicleB340`, `irq_b340`)",
                "- `Command_ConstructIraq_Karrar2` (`Iraq_Karrar2`, `irq_karrar`)",
                "- `Command_ConstructIraqVehicleFahad3` (`IraqVehicleFahad3`, `irq_fahad3`)",
                "",
                "Added to `Iraq_WarFactoryCommandSet_T3` slots 9 / 10 / 12.",
                "Object definitions, buttons, and ART are unchanged.",
                "`Iraq_Karrar2` still requires `Iraq_MIC` (existing object prerequisite).",
                "M.I.C. remains constructible at match start (PR #661).",
                "",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("PACKED", data_path.stat().st_size, data_sha)
    print("ART_ONE", art1_path.stat().st_size, art1_sha)
    print("ART_TWO", art2_path.stat().st_size, art2_sha)
    print("ZIP", zip_path.stat().st_size, zip_sha)
    print("WF")
    print(wf_cs)
    print("MIC")
    _, mic_cs = last_from(packed_order, packed, "CommandSet", "Iraq_MICCommandSet")
    print(mic_cs)
    print("STATIC VALIDATION: PASS")
    print("RUNTIME_TEST=NOT RUN")


if __name__ == "__main__":
    main()
