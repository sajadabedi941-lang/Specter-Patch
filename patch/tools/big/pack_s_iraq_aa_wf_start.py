#!/usr/bin/env python3
"""Make Iraq's Arabic Alliance War Factory constructible at match start.

Baseline packed archives: SPECTER_IRAQ_MIC_AA_WARFACTORY (PR #659).
ART_ONE / ART_TWO are copied byte-identical. DATA last-wins overlay only.

Packed last-wins audit (PR #659 DATA, not guessed):
  Iraq_VT72BCommandSet / Iraq_WorkerCommandSet slot 6
    = Command_ConstructArabicArmy_WarFactory
  Command_ConstructArabicArmy_WarFactory = DOZER_CONSTRUCT
    Object ArabicArmy_WarFactory, no Options/Science/Upgrade
  ArabicArmy_WarFactory Prerequisites
    Object = GLASupplyStash Iraq_SupplyCenter   (OR)
  FactionIraq StartingBuilding = Iraq_CommandCenter, StartingUnit0 = Iraq_VT72B
  DefaultStartingCash = 10000  (covers BuildCost 2500)
  Iraq_SupplyCenter itself requires Iraq_PowerPlant — not present at t=0
  Former Iraq_MIC lock was AND of radar + airfield + war factory
  GLAWorkerCommandSet still constructs ArabicArmy_WarFactory
  AA PlayerTemplate StartingBuilding = GLACommandCenter (not GLASupplyStash)

Smallest safe faction-specific change:
  Prerequisites Object = GLASupplyStash Iraq_CommandCenter
  Iraq starts with Iraq_CommandCenter, so the slot is available immediately.
  Arabic Alliance still needs GLASupplyStash.
  Do not empty the shared Prerequisites block (that would drop AA's intended stash gate).
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

SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MIC_AA_WARFACTORY/_SPEC_DATA_ONE.big"
SRC_ART1 = ROOT / "patch/Release/SPECTER_IRAQ_MIC_AA_WARFACTORY/_SPEC_ART_ONE.big"
SRC_ART2 = ROOT / "patch/Release/SPECTER_IRAQ_MIC_AA_WARFACTORY/_SPEC_ART_TWO.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_AA_WF_START"
INSTALLER = ROOT / "patch/tools/installer"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "704b894a198bc24e70366271f61b6303323f109b7ef36211bc371618428b7582"
SIZE_DATA_SRC = 370746407
SHA_ART1_SRC = "dd53835d7119e7609d2bd955879f234da83a0c6c650d7d7ed1194385d9bbd0f2"
SIZE_ART1_SRC = 2144061050
SHA_ART2_SRC = "daf5e3bb3d4b0f763fee4bd39ceafa06000b9c7261f538a0e84a7b6b54fb7f21"
SIZE_ART2_SRC = 307234369
SAGE_SAFE = 2147483648

CS_KEY = r"Data\INI\CommandSet_ZZZZ_IraqMicAaWarFactory.ini"
WF_KEY = r"Data\INI\Object\Specter\Arabic Alliance\Buildings\Warfactory.ini"
MIC_OBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_MIC.ini"

IRAQ_DOZER_CS = "Iraq_VT72BCommandSet"
IRAQ_WORKER_CS = "Iraq_WorkerCommandSet"
AA_WORKER_CS = "GLAWorkerCommandSet"
MIC_CMD = "Command_ConstructIraq_MIC"
AA_WF_CMD = "Command_ConstructArabicArmy_WarFactory"
AA_WF_OBJ = "ArabicArmy_WarFactory"
IRAQ_MIC_OBJ = "Iraq_MIC"
IRAQ_WF_T = "Command_ConstructIraq_WarFactory_T"
IRAQ_MF = "Command_ConstructIraq_AlFahdMissileFactory"
IRAQ_CC = "Iraq_CommandCenter"
IRAQ_SUPPLY = "Iraq_SupplyCenter"
SLOT_RE = re.compile(r"(?m)^([ \t]*)(\d+)([ \t]*=[ \t]*)(\S+)[ \t]*\r?$")

FROZEN = [
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\PlayerTemplate_SpecterPatch.ini",
    r"Data\INI\Weapon.ini",
    r"Data\INI\CommandSet_ZZZZ_IraqMicAaWarFactory.ini",
    r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini",
    r"Data\INI\SpecialPower_ZZZZ_SpySatellite.ini",
    r"Data\INI\CommandButton_ZZZZ_SpySatellite.ini",
    MIC_OBJ_KEY,
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


def splice_start_prereq(text: str) -> str:
    blk = last_block(text, "Object", AA_WF_OBJ)
    if not blk:
        raise SystemExit("missing Object ArabicArmy_WarFactory")
    new_blk, n = re.subn(
        r"(?m)^(\s*Object\s*=\s*)GLASupplyStash Iraq_SupplyCenter\s*$",
        r"\1GLASupplyStash Iraq_CommandCenter",
        blk,
        count=1,
    )
    if n != 1:
        raise SystemExit(
            "failed to replace Iraq_SupplyCenter with Iraq_CommandCenter "
            "on ArabicArmy_WarFactory Prerequisites"
        )
    if IRAQ_CC not in new_blk:
        raise SystemExit("prereq splice lost Iraq_CommandCenter")
    if "GLASupplyStash" not in new_blk:
        raise SystemExit("prereq splice lost GLASupplyStash")
    if IRAQ_SUPPLY in new_blk:
        raise SystemExit("prereq splice left Iraq_SupplyCenter")
    start = text.rfind(blk)
    return text[:start] + new_blk + text[start + len(blk) :]


def slot_map(block: str) -> dict[str, str]:
    return {m.group(2): m.group(4) for m in SLOT_RE.finditer(block or "")}


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_IRAQ_MIC_AA_WARFACTORY")
    if sha256_path(SRC_ART1) != SHA_ART1_SRC or SRC_ART1.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE baseline mismatch")
    if sha256_path(SRC_ART2) != SHA_ART2_SRC or SRC_ART2.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO baseline mismatch")

    files, order = sk.parse_big_ordered(SRC_DATA.read_bytes())
    original = dict(files)

    if WF_KEY not in files:
        raise SystemExit(f"missing {WF_KEY}")
    files[WF_KEY] = splice_start_prereq(files[WF_KEY].decode("latin1")).encode("latin1")

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
    src_aa_btn, aa_btn = last_from(packed_order, packed, "CommandButton", AA_WF_CMD)
    src_aa_obj, aa_obj = last_from(packed_order, packed, "Object", AA_WF_OBJ)
    src_mic_obj, mic_obj = last_from(packed_order, packed, "Object", IRAQ_MIC_OBJ)
    src_cc, cc = last_from(packed_order, packed, "Object", IRAQ_CC)
    src_pt, pt = last_from(packed_order, packed, "PlayerTemplate", "FactionIraq")
    src_gd, gd = last_from(packed_order, packed, "GameData", "TheGameData")
    if not gd:
        # GameData.ini uses a different header in some packs
        for key in packed_order:
            if key.lower().endswith(r"data\ini\gamedata.ini") or key.lower().endswith(
                "gamedata.ini"
            ):
                gd = packed[key].decode("latin1")
                src_gd = key
                break

    dozer_slots = slot_map(dozer)
    worker_slots = slot_map(worker)
    if dozer_slots.get("6") != AA_WF_CMD:
        fails.append(f"Iraq dozer slot 6 is {dozer_slots.get('6')}")
    if worker_slots.get("6") != AA_WF_CMD:
        fails.append(f"Iraq worker slot 6 is {worker_slots.get('6')}")
    if MIC_CMD in dozer or MIC_CMD in worker:
        fails.append("M.I.C. returned to an Iraq construction menu")
    if IRAQ_WF_T not in dozer:
        fails.append("Iraq lost existing War Factory construct")
    if IRAQ_MF not in dozer:
        fails.append("Iraq lost missile factory construct")
    if field(aa_btn, "Command") != "DOZER_CONSTRUCT":
        fails.append("AA WF button is not DOZER_CONSTRUCT")
    if field(aa_btn, "Object") != AA_WF_OBJ:
        fails.append("AA WF button Object mismatch")
    if field(aa_btn, "ButtonImage") != "arb_warfactory":
        fails.append("AA WF button art mismatch")
    if field(aa_btn, "Options"):
        fails.append("AA WF button gained Options gate")
    if field(aa_btn, "Science"):
        fails.append("AA WF button gained Science gate")
    if field(aa_btn, "Upgrade"):
        fails.append("AA WF button gained Upgrade gate")
    if "Arb_warfactory" not in aa_obj:
        fails.append("AA WF lost Arb_warfactory model")
    if field(aa_obj, "CommandSet") != "Arb_WarFactoryCommandSet_T":
        fails.append("AA WF CommandSet changed")
    if field(aa_obj, "Side") != "GLA":
        fails.append("AA WF Side changed")
    if field(aa_obj, "BuildCompletion") != "PLACED_BY_PLAYER":
        fails.append("AA WF BuildCompletion changed")
    if "2000" not in field(aa_obj, "MaxHealth"):
        fails.append("AA WF MaxHealth changed")
    prereq = re.search(
        r"(?ms)^\s*Prerequisites\s*\r?\n.*?(?:^\s*End)\s*$", aa_obj or ""
    )
    prereq_txt = prereq.group(0) if prereq else ""
    if "GLASupplyStash" not in prereq_txt:
        fails.append("AA WF lost GLASupplyStash prereq")
    if IRAQ_CC not in prereq_txt:
        fails.append("AA WF missing Iraq_CommandCenter start-game prereq")
    if IRAQ_SUPPLY in prereq_txt:
        fails.append("AA WF still requires Iraq_SupplyCenter")
    and_lines = re.findall(r"(?m)^\s*Object\s*=", prereq_txt)
    if len(and_lines) != 1:
        fails.append(f"AA WF Prerequisites AND-count {len(and_lines)}")
    if re.search(r"(?m)^\s*Science\s*=", prereq_txt or ""):
        fails.append("AA WF gained Science prerequisite")
    if AA_WF_CMD not in aa_worker:
        fails.append("Arabic Alliance worker lost War Factory construct")
    if MIC_CMD in aa_worker:
        fails.append("Arabic Alliance worker gained Iraq MIC")
    if "Irq_MIC" not in mic_obj:
        fails.append("Iraq_MIC object/model lost")
    if src_mic_obj != MIC_OBJ_KEY:
        fails.append(f"Iraq_MIC last-wins {src_mic_obj}")
    if src_aa_obj != WF_KEY:
        fails.append(f"ArabicArmy_WarFactory last-wins {src_aa_obj}")
    if src_dozer != CS_KEY:
        fails.append(f"{IRAQ_DOZER_CS} last-wins {src_dozer}")
    if src_worker != CS_KEY:
        fails.append(f"{IRAQ_WORKER_CS} last-wins {src_worker}")
    if not cc:
        fails.append("Iraq_CommandCenter missing")
    cc_prereq = re.search(
        r"(?ms)^\s*Prerequisites\s*\r?\n.*?(?:^\s*End)\s*$", cc or ""
    )
    if cc_prereq and re.search(r"(?m)^\s*Object\s*=\s*\S+", cc_prereq.group(0)):
        fails.append("Iraq_CommandCenter unexpectedly has object prereqs")
    if field(pt, "StartingBuilding") != IRAQ_CC:
        fails.append(f"FactionIraq StartingBuilding={field(pt, 'StartingBuilding')}")
    cash = ""
    if gd:
        cash = field(gd, "DefaultStartingCash") or re.search(
            r"(?m)^\s*DefaultStartingCash\s*=\s*(\S+)", gd
        )
        cash = cash.group(1) if hasattr(cash, "group") else cash
    if cash and cash.split()[0].rstrip(";") != "10000":
        fails.append(f"DefaultStartingCash changed {cash}")

    orig_cs = collect_commandsets(order, original)
    packed_cs = collect_commandsets(packed_order, packed)
    orig_dozer_cmds = {m.group(4) for m in SLOT_RE.finditer(orig_cs[IRAQ_DOZER_CS])}
    new_dozer_cmds = {m.group(4) for m in SLOT_RE.finditer(dozer)}
    if orig_dozer_cmds != new_dozer_cmds:
        fails.append(f"Iraq dozer commands changed {sorted(orig_dozer_cmds ^ new_dozer_cmds)}")

    allowed = {WF_KEY}
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
    (ext / "ArabicArmy_WarFactory.ini").write_text(aa_obj + "\n", encoding="utf-8")
    (ext / "Command_ConstructArabicArmy_WarFactory.ini").write_text(
        aa_btn + "\n", encoding="utf-8"
    )
    (ext / "FactionIraq.ini").write_text(pt + "\n", encoding="utf-8")

    (OUT / "INSTALL.txt").write_text(
        "\n".join(
            [
                "SPECTER IRAQ AA WAR FACTORY AT MATCH START — INSTALL",
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
        "Iraq slot 6 constructs ArabicArmy_WarFactory from match start "
        "(prereq Iraq_CommandCenter, which FactionIraq starts with).\n"
        "Arabic Alliance still requires GLASupplyStash.\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    zip_path = OUT / "SPECTER_IRAQ_AA_WF_START.zip"
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
    tag = "s-iraq-aa-wf-start"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/" + tag
    )

    report = "\n".join(
        [
            "STATIC VALIDATION: PASS",
            "RUNTIME_TEST=NOT RUN",
            "BASELINE: PR #659 SPECTER_IRAQ_MIC_AA_WARFACTORY",
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
            f"AA_WF_OBJECT_LASTWINS={src_aa_obj}",
            f"AA_WF_BUTTON={src_aa_btn}",
            f"AA_WORKER_LASTWINS={src_aa_worker}",
            "SLOT6=Command_ConstructArabicArmy_WarFactory",
            "OBJECT=ArabicArmy_WarFactory",
            "AA_WF_PREREQ=GLASupplyStash Iraq_CommandCenter",
            "IRAQ_STARTING_BUILDING=Iraq_CommandCenter",
            "MIC_NOT_ON_IRAQ_MENUS=YES",
            "AA_WORKER_PRESERVED=YES",
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
                "ZIP_FILE=SPECTER_IRAQ_AA_WF_START.zip",
                f"ZIP_SIZE={zip_path.stat().st_size}",
                f"ZIP_SHA256={zip_sha}",
                "BASELINE=PR #659",
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
                f"  {rel_base}/SPECTER_IRAQ_AA_WF_START.zip",
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
                "# Iraq Arabic Alliance War Factory available at match start",
                "",
                "Iraq dozer/worker slot 6 still uses `Command_ConstructArabicArmy_WarFactory`",
                "(`Object = ArabicArmy_WarFactory`).",
                "",
                "`ArabicArmy_WarFactory` Prerequisites are now `GLASupplyStash` **or**",
                "`Iraq_CommandCenter`. FactionIraq starts with `Iraq_CommandCenter`, so",
                "the replacement is constructible immediately. Arabic Alliance still",
                "requires `GLASupplyStash`.",
                "",
                "ART_ONE and ART_TWO are byte-identical to PR #659.",
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
