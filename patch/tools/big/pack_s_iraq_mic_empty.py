#!/usr/bin/env python3
"""Clear Iraq M.I.C. production/upgrade menu; keep WF transfer and start-game MIC.

Baseline packed archives: SPECTER_IRAQ_MIC_TO_WF (PR #662).
ART_ONE / ART_TWO are copied byte-identical. DATA last-wins overlay only.

Packed last-wins audit (PR #662 DATA, not guessed):
  Iraq_MIC CommandSet = Iraq_MICCommandSet; Prerequisites empty (PR #661)
  No CommandSetUpgrade on Iraq_MIC (CS2/CS3 unused by the object)
  Iraq_MICCommandSet / 2 / 3 last-wins CommandSet_ZZZZ_IraqMicToWf.ini:
    PLAYER_UPGRADE: Abbas, BMP-2M2, Hussien, S-8, BMP-1M3, Irq_Tier1/2/3, Mi35Mk3, Kab500
    SELL: Command_Sell
    (the three transferred UNIT_BUILD commands already removed in #662)
  Iraq_WarFactory_T CommandSet = Iraq_WarFactoryCommandSet_T3
    slots 9/10/12 = B340 / Karrar2 / Fahad3
  Iraq_Karrar2 Prerequisites Object = Iraq_MIC  (sole remaining MIC production gate)
  B340 and Fahad3 have empty Prerequisites
  Dozer slot 6 = Command_ConstructIraq_MIC
  Other-country MIC CommandSets that reuse Iraq upgrade commands are left untouched

Smallest safe change:
  1. Last-wins Iraq_MICCommandSet / 2 / 3 to Sell-only
  2. Empty Iraq_Karrar2 Prerequisites so WF production is not gated on MIC
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

SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MIC_TO_WF/_SPEC_DATA_ONE.big"
SRC_ART1 = ROOT / "patch/Release/SPECTER_IRAQ_MIC_TO_WF/_SPEC_ART_ONE.big"
SRC_ART2 = ROOT / "patch/Release/SPECTER_IRAQ_MIC_TO_WF/_SPEC_ART_TWO.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MIC_EMPTY"
INSTALLER = ROOT / "patch/tools/installer"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "08f680c93345fe4dd4941e63d15e3a9dfca66492a6be815f86573eba7bc8f265"
SIZE_DATA_SRC = 370746506
SHA_ART1_SRC = "dd53835d7119e7609d2bd955879f234da83a0c6c650d7d7ed1194385d9bbd0f2"
SIZE_ART1_SRC = 2144061050
SHA_ART2_SRC = "daf5e3bb3d4b0f763fee4bd39ceafa06000b9c7261f538a0e84a7b6b54fb7f21"
SIZE_ART2_SRC = 307234369
SAGE_SAFE = 2147483648

CS_KEY = r"Data\INI\CommandSet_ZZZZ_IraqMicToWfEmpty.ini"
TOWF_KEY = r"Data\INI\CommandSet_ZZZZ_IraqMicToWf.ini"
KARRAR_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Karrar-2.ini"
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
MIC_CONSTRUCT = "Command_ConstructIraq_MIC"
SELL = "Command_Sell"
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
BLOCKED_CMD_TYPES = {
    "UNIT_BUILD",
    "DOZER_CONSTRUCT",
    "PLAYER_UPGRADE",
    "OBJECT_UPGRADE",
    "QUEUE_UPGRADE",
}
PREREQ_RE = re.compile(
    r"(?ms)^([ \t]*)Prerequisites[ \t]*\r?\n"
    r"(?:[ \t]*(?:Object[ \t]*=[^\r\n]+|;[^\r\n]*)\r?\n)+"
    r"[ \t]*End[ \t]*\r?$"
)
SLOT_RE = re.compile(r"(?m)^[ \t]*(\d+)[ \t]*=[ \t]*(\S+)")

FROZEN = [
    TOWF_KEY,
    MIC_OBJ_KEY,
    WF_OBJ_KEY,
    AA_WF_KEY,
    r"Data\INI\CommandButton.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\Object\Specter\Iraq Army\AirDefense\B340.ini",
    r"Data\INI\Object\Specter\Iraq Army\AirDefense\Fahad3.ini",
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


def slot_map(block: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in SLOT_RE.finditer(block or "")}


def sell_only(name: str) -> str:
    return f"CommandSet {name}\r\n  14 = Command_Sell\r\nEnd\r\n"


def splice_karrar_prereq(text: str) -> str:
    blk = last_block(text, "Object", "Iraq_Karrar2")
    if not blk:
        raise SystemExit("missing Object Iraq_Karrar2")
    if "Iraq_MIC" not in blk:
        raise SystemExit("Iraq_Karrar2 missing Iraq_MIC prerequisite to remove")
    new_blk, n = PREREQ_RE.subn(r"\1Prerequisites\r\n\1End", blk, count=1)
    if n != 1:
        raise SystemExit("failed to empty Iraq_Karrar2 Prerequisites")
    prereq = re.search(r"(?ms)^\s*Prerequisites\s*\r?\n.*?(?:^\s*End)\s*$", new_blk)
    if prereq and re.search(r"(?m)^\s*Object\s*=", prereq.group(0)):
        raise SystemExit("Iraq_Karrar2 Prerequisites still list objects")
    if "Iraq_MIC" in new_blk and re.search(
        r"(?ms)Prerequisites.*Iraq_MIC", new_blk
    ):
        raise SystemExit("Iraq_Karrar2 still references Iraq_MIC in Prerequisites")
    start = text.rfind(blk)
    return text[:start] + new_blk + text[start + len(blk) :]


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_IRAQ_MIC_TO_WF")
    if sha256_path(SRC_ART1) != SHA_ART1_SRC or SRC_ART1.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE baseline mismatch")
    if sha256_path(SRC_ART2) != SHA_ART2_SRC or SRC_ART2.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO baseline mismatch")

    files, order = sk.parse_big_ordered(SRC_DATA.read_bytes())
    original = dict(files)

    files[CS_KEY] = sk.to_crlf("\n".join(sell_only(n) for n in MIC_CS_NAMES) + "\n")
    if KARRAR_KEY not in files:
        raise SystemExit(f"missing {KARRAR_KEY}")
    files[KARRAR_KEY] = splice_karrar_prereq(files[KARRAR_KEY].decode("latin1")).encode(
        "latin1"
    )

    for key in FROZEN:
        if files.get(key) != original.get(key):
            raise SystemExit(f"frozen mutated: {key}")

    data_big = sk.build_big(files)
    packed, packed_order = sk.parse_big_ordered(data_big)

    fails = []
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))

    src_dozer, dozer = last_from(packed_order, packed, "CommandSet", IRAQ_DOZER_CS)
    src_mic_obj, mic_obj = last_from(packed_order, packed, "Object", "Iraq_MIC")
    src_wf_obj, wf_obj = last_from(packed_order, packed, "Object", "Iraq_WarFactory_T")
    src_wf_cs, wf_cs = last_from(packed_order, packed, "CommandSet", WF_CS_NAME)
    src_karrar, karrar = last_from(packed_order, packed, "Object", "Iraq_Karrar2")
    src_aa, aa_obj = last_from(packed_order, packed, "Object", "ArabicArmy_WarFactory")

    for name in MIC_CS_NAMES:
        src, blk = last_from(packed_order, packed, "CommandSet", name)
        if src != CS_KEY:
            fails.append(f"{name} last-wins {src}")
        slots = slot_map(blk)
        if set(slots.values()) != {SELL}:
            fails.append(f"{name} commands {sorted(set(slots.values()))}")
        for cmd in slots.values():
            _, btn = last_from(packed_order, packed, "CommandButton", cmd)
            kind = field(btn, "Command")
            if kind in BLOCKED_CMD_TYPES:
                fails.append(f"{name} still exposes {cmd} ({kind})")
            if kind != "SELL":
                fails.append(f"{name} kept non-sell {cmd} ({kind})")
        for cmd in MOVE_CMDS:
            if cmd in blk:
                fails.append(f"{name} regained {cmd}")

    if src_wf_cs != TOWF_KEY:
        fails.append(f"{WF_CS_NAME} last-wins {src_wf_cs}")
    wf_slots = slot_map(wf_cs)
    if wf_slots.get("9") != "Command_ConstructIraqVehicleB340":
        fails.append("WF lost B340")
    if wf_slots.get("10") != "Command_ConstructIraq_Karrar2":
        fails.append("WF lost Karrar2")
    if wf_slots.get("12") != "Command_ConstructIraqVehicleFahad3":
        fails.append("WF lost Fahad3")
    orig_wf = last_from(order, original, "CommandSet", WF_CS_NAME)[1]
    if slot_map(orig_wf) != wf_slots:
        fails.append("WF T3 slots changed")

    for cmd, obj in MOVE_OBJS.items():
        _, btn = last_from(packed_order, packed, "CommandButton", cmd)
        if field(btn, "Command") != "UNIT_BUILD" or field(btn, "Object") != obj:
            fails.append(f"{cmd} button broken")
        if field(btn, "ButtonImage") != MOVE_ART[cmd]:
            fails.append(f"{cmd} art changed")

    k_prereq = re.search(r"(?ms)^\s*Prerequisites\s*\r?\n.*?(?:^\s*End)\s*$", karrar or "")
    if k_prereq and re.search(r"(?m)^\s*Object\s*=", k_prereq.group(0)):
        fails.append("Iraq_Karrar2 still has object prerequisites")
    if re.search(r"(?ms)Prerequisites\s*\r?\n.*?Iraq_MIC", karrar or ""):
        fails.append("Iraq_Karrar2 still depends on Iraq_MIC")
    if field(karrar, "BuildCost") != "2200":
        fails.append("Iraq_Karrar2 BuildCost changed")
    if "Irq_Karrar_A" not in (karrar or ""):
        fails.append("Iraq_Karrar2 model lost")

    if field(mic_obj, "CommandSet") != "Iraq_MICCommandSet":
        fails.append("Iraq_MIC CommandSet pointer changed")
    if "Irq_MIC" not in (mic_obj or ""):
        fails.append("Iraq_MIC model lost")
    mic_prereq = re.search(r"(?ms)^\s*Prerequisites\s*\r?\n.*?(?:^\s*End)\s*$", mic_obj or "")
    if mic_prereq and re.search(r"(?m)^\s*Object\s*=", mic_prereq.group(0)):
        fails.append("Iraq_MIC regained object prerequisites")
    dozer_slots = slot_map(dozer)
    if dozer_slots.get("6") != MIC_CONSTRUCT:
        fails.append(f"Iraq dozer slot 6 is {dozer_slots.get('6')}")
    if field(wf_obj, "CommandSet") != WF_CS_NAME:
        fails.append("Iraq_WarFactory_T CommandSet changed")
    if src_mic_obj != MIC_OBJ_KEY:
        fails.append(f"Iraq_MIC last-wins {src_mic_obj}")
    if src_karrar != KARRAR_KEY:
        fails.append(f"Iraq_Karrar2 last-wins {src_karrar}")

    aa_prereq = re.search(r"(?ms)^\s*Prerequisites\s*\r?\n.*?(?:^\s*End)\s*$", aa_obj or "")
    if aa_prereq and "Iraq_" in aa_prereq.group(0):
        fails.append("Arabic Alliance War Factory gained Iraq prereq")

    # Other-country MIC menus that reused Iraq upgrades must stay intact.
    for name in (
        "NorthKorea_MICCommandSet",
        "SouthKorea_MICCommandSet",
        "Japan_MICCommandSet",
    ):
        src, blk = last_from(packed_order, packed, "CommandSet", name)
        orig = last_from(order, original, "CommandSet", name)[1]
        if blk != orig:
            fails.append(f"other-country {name} mutated")

    allowed = {CS_KEY, KARRAR_KEY}
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
    (LOOSE / "CommandSet_ZZZZ_IraqMicToWfEmpty.ini").write_bytes(files[CS_KEY])

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    for name in MIC_CS_NAMES:
        _, blk = last_from(packed_order, packed, "CommandSet", name)
        (ext / f"{name}.ini").write_text(blk + "\n", encoding="utf-8")
    (ext / f"{WF_CS_NAME}.ini").write_text(wf_cs + "\n", encoding="utf-8")
    (ext / "Iraq_Karrar2.ini").write_text(karrar + "\n", encoding="utf-8")

    (OUT / "INSTALL.txt").write_text(
        "\n".join(
            [
                "SPECTER IRAQ M.I.C. EMPTY MENU — INSTALL",
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
        "Iraq_MICCommandSet / 2 / 3 are Sell-only. "
        "B340, Karrar2, and Fahad3 stay on Iraq_WarFactoryCommandSet_T3. "
        "Iraq_Karrar2 no longer requires Iraq_MIC.\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    zip_path = OUT / "SPECTER_IRAQ_MIC_EMPTY.zip"
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
    tag = "s-iraq-mic-empty"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/" + tag
    )

    report = "\n".join(
        [
            "STATIC VALIDATION: PASS",
            "RUNTIME_TEST=NOT RUN",
            "BASELINE: PR #662 SPECTER_IRAQ_MIC_TO_WF",
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
            f"CHANGED_PACKED_FILES={CS_KEY};{KARRAR_KEY}",
            "MIC_MENU=SELL_ONLY",
            "WF_TRANSFER_PRESERVED=YES",
            "KARRAR2_MIC_PREREQ=REMOVED",
            "MIC_START_GAME_PRESERVED=YES",
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
                "ZIP_FILE=SPECTER_IRAQ_MIC_EMPTY.zip",
                f"ZIP_SIZE={zip_path.stat().st_size}",
                f"ZIP_SHA256={zip_sha}",
                "BASELINE=PR #662",
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
                f"  {rel_base}/SPECTER_IRAQ_MIC_EMPTY.zip",
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
                "# Iraq M.I.C. production/upgrade menu cleared",
                "",
                "`Iraq_MICCommandSet`, `Iraq_MICCommandSet2`, and `Iraq_MICCommandSet3`",
                "are Sell-only. The building remains constructible at match start.",
                "",
                "War Factory T3 still produces B340, Karrar-2, and Fahad-3.",
                "`Iraq_Karrar2` no longer requires `Iraq_MIC`.",
                "",
                "ART_ONE and ART_TWO are byte-identical to PR #662.",
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
    _, mic_cs = last_from(packed_order, packed, "CommandSet", "Iraq_MICCommandSet")
    print("MIC")
    print(mic_cs)
    print("WF")
    print(wf_cs)
    print("STATIC VALIDATION: PASS")
    print("RUNTIME_TEST=NOT RUN")


if __name__ == "__main__":
    main()
