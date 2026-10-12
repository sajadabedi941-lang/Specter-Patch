#!/usr/bin/env python3
"""Make original Iraq_MIC constructible at match start.

Baseline packed archives: SPECTER_SPY_SATELLITE_25_COUNTRIES (PR #658).
ART_ONE / ART_TWO are copied byte-identical. DATA last-wins overlay only.

Do not continue PRs #659/#660 (Arabic Alliance War Factory replacement).

Packed last-wins audit (PR #658 DATA, not guessed):
  Iraq_VT72BCommandSet / Iraq_WorkerCommandSet slot 6
    = Command_ConstructIraq_MIC
  Command_ConstructIraq_MIC = DOZER_CONSTRUCT Object Iraq_MIC
    no Options / Science / Upgrade
  Object Iraq_MIC last-wins Data\\INI\\Object\\Specter\\Iraq Army\\Buildings\\Iraq_MIC.ini
    Model Irq_MIC, CommandSet Iraq_MICCommandSet, BuildCost 7000
    Prerequisites AND:
      Iraq_RadarStation | NorthKorea_RadarStation
      IraqMilitaryAirfield | Iraq_Airfield_T | NorthKorea_Airfield
      IraqMilitaryWarfactory | Iraq_WarFactory_T | NorthKorea_WarFactory
  FactionIraq StartingBuilding = Iraq_CommandCenter
  DefaultStartingCash = 10000 (covers 7000)
  ArabicArmy_WarFactory still Prerequisites Object = GLASupplyStash only

Smallest safe change:
  Empty Iraq_MIC Prerequisites. Leave CommandSets, AA, and all other objects untouched.
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

SRC_DATA = ROOT / "patch/Release/SPECTER_SPY_SATELLITE_25_COUNTRIES/_SPEC_DATA_ONE.big"
SRC_ART1 = ROOT / "patch/Release/SPECTER_SPY_SATELLITE_25_COUNTRIES/_SPEC_ART_ONE.big"
SRC_ART2 = ROOT / "patch/Release/SPECTER_SPY_SATELLITE_25_COUNTRIES/_SPEC_ART_TWO.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MIC_START"
INSTALLER = ROOT / "patch/tools/installer"

SHA_DATA_SRC = "00b07a188d25edabe9b18d8671c514467bd6cbb07c78f81d89a8015ee30c4bf3"
SIZE_DATA_SRC = 370744963
SHA_ART1_SRC = "dd53835d7119e7609d2bd955879f234da83a0c6c650d7d7ed1194385d9bbd0f2"
SIZE_ART1_SRC = 2144061050
SHA_ART2_SRC = "daf5e3bb3d4b0f763fee4bd39ceafa06000b9c7261f538a0e84a7b6b54fb7f21"
SIZE_ART2_SRC = 307234369
SAGE_SAFE = 2147483648

MIC_OBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_MIC.ini"
WF_KEY = r"Data\INI\Object\Specter\Arabic Alliance\Buildings\Warfactory.ini"

IRAQ_DOZER_CS = "Iraq_VT72BCommandSet"
IRAQ_WORKER_CS = "Iraq_WorkerCommandSet"
AA_WORKER_CS = "GLAWorkerCommandSet"
MIC_CMD = "Command_ConstructIraq_MIC"
AA_WF_CMD = "Command_ConstructArabicArmy_WarFactory"
AA_WF_OBJ = "ArabicArmy_WarFactory"
IRAQ_MIC_OBJ = "Iraq_MIC"
IRAQ_WF_T = "Command_ConstructIraq_WarFactory_T"
IRAQ_MF = "Command_ConstructIraq_AlFahdMissileFactory"
SLOT_RE = re.compile(r"(?m)^([ \t]*)(\d+)([ \t]*=[ \t]*)(\S+)[ \t]*\r?$")
PREREQ_RE = re.compile(
    r"(?ms)^([ \t]*)Prerequisites[ \t]*\r?\n(?:[ \t]*Object[ \t]*=[^\r\n]+\r?\n)+[ \t]*End[ \t]*\r?$"
)

FROZEN = [
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\PlayerTemplate_SpecterPatch.ini",
    r"Data\INI\Weapon.ini",
    r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini",
    r"Data\INI\SpecialPower_ZZZZ_SpySatellite.ini",
    r"Data\INI\CommandButton_ZZZZ_SpySatellite.ini",
    r"Data\INI\CommandSet_ArabicAllianceUnlock.ini",
    WF_KEY,
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
    return {m.group(2): m.group(4) for m in SLOT_RE.finditer(block or "")}


def splice_empty_prereq(text: str) -> str:
    blk = last_block(text, "Object", IRAQ_MIC_OBJ)
    if not blk:
        raise SystemExit("missing Object Iraq_MIC")
    new_blk, n = PREREQ_RE.subn(r"\1Prerequisites\r\n\1End", blk, count=1)
    if n != 1:
        raise SystemExit("failed to empty Iraq_MIC Prerequisites")
    if re.search(r"(?m)^\s*Object\s*=", new_blk):
        # remaining Object= in Prerequisites only — reject any leftover prereq objects
        prereq = re.search(r"(?ms)^\s*Prerequisites\s*\r?\n.*?(?:^\s*End)\s*$", new_blk)
        if prereq and re.search(r"(?m)^\s*Object\s*=", prereq.group(0)):
            raise SystemExit("Iraq_MIC Prerequisites still list objects")
    start = text.rfind(blk)
    return text[:start] + new_blk + text[start + len(blk) :]


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_SPY_SATELLITE_25_COUNTRIES")
    if sha256_path(SRC_ART1) != SHA_ART1_SRC or SRC_ART1.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE baseline mismatch")
    if sha256_path(SRC_ART2) != SHA_ART2_SRC or SRC_ART2.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO baseline mismatch")

    files, order = sk.parse_big_ordered(SRC_DATA.read_bytes())
    original = dict(files)

    if MIC_OBJ_KEY not in files:
        raise SystemExit(f"missing {MIC_OBJ_KEY}")
    files[MIC_OBJ_KEY] = splice_empty_prereq(files[MIC_OBJ_KEY].decode("latin1")).encode(
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
    src_worker, worker = last_from(packed_order, packed, "CommandSet", IRAQ_WORKER_CS)
    src_aa_worker, aa_worker = last_from(packed_order, packed, "CommandSet", AA_WORKER_CS)
    src_mic_btn, mic_btn = last_from(packed_order, packed, "CommandButton", MIC_CMD)
    src_mic_obj, mic_obj = last_from(packed_order, packed, "Object", IRAQ_MIC_OBJ)
    src_aa_obj, aa_obj = last_from(packed_order, packed, "Object", AA_WF_OBJ)
    src_mic_cs, mic_cs = last_from(packed_order, packed, "CommandSet", "Iraq_MICCommandSet")
    src_pt, pt = last_from(packed_order, packed, "PlayerTemplate", "FactionIraq")

    dozer_slots = slot_map(dozer)
    worker_slots = slot_map(worker)
    if dozer_slots.get("6") != MIC_CMD:
        fails.append(f"Iraq dozer slot 6 is {dozer_slots.get('6')}")
    if worker_slots.get("6") != MIC_CMD:
        fails.append(f"Iraq worker slot 6 is {worker_slots.get('6')}")
    if AA_WF_CMD in dozer or AA_WF_CMD in worker:
        fails.append("Arabic Alliance War Factory leaked onto an Iraq construction menu")
    if IRAQ_WF_T not in dozer:
        fails.append("Iraq lost existing War Factory construct")
    if IRAQ_MF not in dozer:
        fails.append("Iraq lost missile factory construct")
    if field(mic_btn, "Command") != "DOZER_CONSTRUCT":
        fails.append("MIC button is not DOZER_CONSTRUCT")
    if field(mic_btn, "Object") != IRAQ_MIC_OBJ:
        fails.append("MIC button Object mismatch")
    if field(mic_btn, "ButtonImage") != "Button_GlobalMarket":
        fails.append("MIC button art mismatch")
    if field(mic_btn, "Options"):
        fails.append("MIC button gained Options gate")
    if field(mic_btn, "Science"):
        fails.append("MIC button gained Science gate")
    if field(mic_btn, "Upgrade"):
        fails.append("MIC button gained Upgrade gate")
    if "Irq_MIC" not in mic_obj:
        fails.append("Iraq_MIC lost Irq_MIC model")
    if field(mic_obj, "CommandSet") != "Iraq_MICCommandSet":
        fails.append("Iraq_MIC CommandSet changed")
    if field(mic_obj, "Side") != "Iraq":
        fails.append("Iraq_MIC Side changed")
    if field(mic_obj, "BuildCost") != "7000":
        fails.append("Iraq_MIC BuildCost changed")
    if field(mic_obj, "BuildCompletion") != "PLACED_BY_PLAYER":
        fails.append("Iraq_MIC BuildCompletion changed")
    prereq = re.search(r"(?ms)^\s*Prerequisites\s*\r?\n.*?(?:^\s*End)\s*$", mic_obj or "")
    prereq_txt = prereq.group(0) if prereq else ""
    if re.search(r"(?m)^\s*Object\s*=", prereq_txt):
        fails.append("Iraq_MIC still has object prerequisites")
    if re.search(r"(?m)^\s*Science\s*=", prereq_txt):
        fails.append("Iraq_MIC gained Science prerequisite")
    if src_mic_obj != MIC_OBJ_KEY:
        fails.append(f"Iraq_MIC last-wins {src_mic_obj}")
    if not mic_cs:
        fails.append("Iraq_MICCommandSet missing")
    if field(pt, "StartingBuilding") != "Iraq_CommandCenter":
        fails.append(f"FactionIraq StartingBuilding={field(pt, 'StartingBuilding')}")
    aa_prereq = re.search(r"(?ms)^\s*Prerequisites\s*\r?\n.*?(?:^\s*End)\s*$", aa_obj or "")
    aa_prereq_txt = aa_prereq.group(0) if aa_prereq else ""
    if "GLASupplyStash" not in aa_prereq_txt:
        fails.append("Arabic Alliance War Factory lost GLASupplyStash prereq")
    if "Iraq_SupplyCenter" in aa_prereq_txt or "Iraq_CommandCenter" in aa_prereq_txt:
        fails.append("Arabic Alliance War Factory gained Iraq prereq")
    if AA_WF_CMD not in aa_worker:
        fails.append("Arabic Alliance worker lost War Factory construct")
    if MIC_CMD in aa_worker:
        fails.append("Arabic Alliance worker gained Iraq MIC")

    orig_dozer, orig_dozer_blk = last_from(order, original, "CommandSet", IRAQ_DOZER_CS)
    if orig_dozer_blk != dozer:
        fails.append("Iraq dozer CommandSet mutated")
    orig_worker, orig_worker_blk = last_from(order, original, "CommandSet", IRAQ_WORKER_CS)
    if orig_worker_blk != worker:
        fails.append("Iraq worker CommandSet mutated")

    allowed = {MIC_OBJ_KEY}
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

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "Iraq_VT72BCommandSet.ini").write_text(dozer + "\n", encoding="utf-8")
    (ext / "Iraq_WorkerCommandSet.ini").write_text(worker + "\n", encoding="utf-8")
    (ext / "Iraq_MIC.ini").write_text(mic_obj + "\n", encoding="utf-8")
    (ext / "Command_ConstructIraq_MIC.ini").write_text(mic_btn + "\n", encoding="utf-8")

    (OUT / "INSTALL.txt").write_text(
        "\n".join(
            [
                "SPECTER IRAQ M.I.C. AT MATCH START — INSTALL",
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
        "Iraq slot 6 constructs original Iraq_MIC from match start "
        "(object Prerequisites emptied; CommandSets unchanged).\n"
        "Arabic Alliance is untouched.\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    zip_path = OUT / "SPECTER_IRAQ_MIC_START.zip"
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
    tag = "s-iraq-mic-start"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/" + tag
    )

    report = "\n".join(
        [
            "STATIC VALIDATION: PASS",
            "RUNTIME_TEST=NOT RUN",
            "BASELINE: PR #658 SPECTER_SPY_SATELLITE_25_COUNTRIES",
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
            f"IRAQ_DOZER_LASTWINS={src_dozer}",
            f"IRAQ_WORKER_LASTWINS={src_worker}",
            f"IRAQ_MIC_OBJECT_LASTWINS={src_mic_obj}",
            f"IRAQ_MIC_BUTTON={src_mic_btn}",
            f"AA_WF_OBJECT_LASTWINS={src_aa_obj}",
            f"AA_WORKER_LASTWINS={src_aa_worker}",
            "SLOT6=Command_ConstructIraq_MIC",
            "OBJECT=Iraq_MIC",
            "IRAQ_MIC_PREREQ=EMPTY",
            "AA_WF_UNCHANGED=YES",
            "IRAQ_COMMANDSETS_UNCHANGED=YES",
            "IRAQ_WARFACTORY_T_PRESERVED=YES",
            "IRAQ_MISSILE_FACTORY_PRESERVED=YES",
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
                "ZIP_FILE=SPECTER_IRAQ_MIC_START.zip",
                f"ZIP_SIZE={zip_path.stat().st_size}",
                f"ZIP_SHA256={zip_sha}",
                "BASELINE=PR #658",
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
                f"  {rel_base}/SPECTER_IRAQ_MIC_START.zip",
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
                "# Iraq M.I.C. constructible at match start",
                "",
                "Iraq dozer/worker slot 6 still uses `Command_ConstructIraq_MIC`",
                "(`Object = Iraq_MIC`, model `Irq_MIC`, `CommandSet = Iraq_MICCommandSet`).",
                "",
                "The original three-building AND prerequisites (radar + airfield + war factory)",
                "are removed. No upgrade, science, or tier gate remains on the construct button.",
                "Arabic Alliance and all other Iraq construction slots are unchanged.",
                "",
                "ART_ONE and ART_TWO are byte-identical to PR #658.",
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
    print("PREREQ")
    print(prereq_txt)
    print("STATIC VALIDATION: PASS")
    print("RUNTIME_TEST=NOT RUN")


if __name__ == "__main__":
    main()
