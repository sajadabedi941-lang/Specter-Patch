#!/usr/bin/env python3
"""Add Global Store to Russia, China, Iran, America, and Israel.

Baseline packed archives: SPECTER_GLOBAL_STORE_EXPAND (PR #669).
ART_ONE / ART_TWO are copied byte-identical (HsGM flag already scaled).

Packed last-wins construction slots:
  Russia  RussiaDozerCommandSet slot 2  RussiaIndustrialComplex
  China   PLADozerCommandSet    slot 6  ChinaIndustrialWeaponComplex
          (no ChinaIndustrialComplex object exists)
  Iran    IranDozerCommandSet   slot 2  IranIndustrialComplex
  America AmericaDozerCommandSet slot 2 AmericaStrategyCenter_T
          (slot 15 AmericaStrategyCenter is left intact — one GS only)
  Israel  IsraelDozerCommandSet slot 2  AirF_AmericaStrategyCenter

Iraq_MIC and the 19 PR #669 country copies are not rebuilt.
"""
from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_global_store_expand as gs  # noqa: E402
import pack_s_iraq_mic_radar_ad as rad  # noqa: E402
import pack_s_radar_uav_slots as uav  # noqa: E402
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_GLOBAL_STORE_EXPAND/_SPEC_DATA_ONE.big"
SRC_ART1 = ROOT / "patch/Release/SPECTER_GLOBAL_STORE_EXPAND/_SPEC_ART_ONE.big"
SRC_ART2 = ROOT / "patch/Release/SPECTER_GLOBAL_STORE_EXPAND/_SPEC_ART_TWO.big"
OUT = ROOT / "patch/Release/SPECTER_GLOBAL_STORE_FIVE"
INSTALLER = ROOT / "patch/tools/installer"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "98ee820bdfd4afdc6a907eea1ce90ecff0a7552470cb5e1120891bf8375195bc"
SIZE_DATA_SRC = 373098243
SHA_ART1_SRC = "9dc4524ccb44881fcd0149957d2fcce1d378db1483e6c458df67e07c86a86aa8"
SIZE_ART1_SRC = 2144972013
SHA_ART2_SRC = "a5a20d959d2835f12a4bf5431e011c4d45047f24ea3d88841c2281fc0a6c19af"
SIZE_ART2_SRC = 307254782
SAGE_SAFE = 2147483648

CS_INI = gs.CS_INI
CB_INI = gs.CB_INI
CSF_KEY = gs.CSF_KEY
MIC_OBJ_KEY = gs.MIC_OBJ_KEY
PREV_OBJ = gs.OBJ_KEY
PREV_CS = gs.CS_ZZZZ
PREV_CB = gs.CB_ZZZZ
PREV_PREREQ = gs.PREREQ_KEY
OBJ_KEY = r"Data\INI\Object\Specter\GlobalStore\CountryGlobalStoresFive.ini"
CB_ZZZZ = r"Data\INI\CommandButton_ZZZZ_ZGlobalStoreFive.ini"
CS_ZZZZ = r"Data\INI\CommandSet_ZZZZ_ZGlobalStoreFive.ini"
PREREQ_KEY = r"Data\INI\Object_ZZZZ_ZzGlobalStoreFivePrereq.ini"
FLAG_W3D = gs.FLAG_W3D
FLAG_WF = gs.FLAG_WF
FLAG_CU = gs.FLAG_CU

DISPLAY_KEY = gs.DISPLAY_KEY
NAME = gs.NAME
TIP = gs.TIP
COST = gs.COST

COUNTRIES = [
    {
        "display": "Russia",
        "group": "IC",
        "side": "Russia",
        "object": "Russia_GlobalStore",
        "cmd": "Command_ConstructRussia_GlobalStore",
        "replaced": "RussiaIndustrialComplex",
        "replaced_kind": "Industrial Complex",
        "old_cmd": "Command_ConstructRussiaIndustrialComplex",
        "slot": "2",
        "commandsets": ["RussiaDozerCommandSet"],
        "prereq_old": ["RussiaIndustrialComplex"],
        "note": "IC factory queue (T14/T15/S500/96L6TSP/2S7M) is not merged into Global Store.",
    },
    {
        "display": "China",
        "group": "IC",
        "side": "China",
        "object": "China_GlobalStore",
        "cmd": "Command_ConstructChina_GlobalStore",
        "replaced": "ChinaIndustrialWeaponComplex",
        "replaced_kind": "Industrial Complex (Weapon Industry Plant; no ChinaIndustrialComplex object)",
        "old_cmd": "Command_ConstructChinaIndustrialWeaponComplex",
        "slot": "6",
        "commandsets": ["PLADozerCommandSet"],
        "prereq_old": ["ChinaIndustrialWeaponComplex"],
        "note": "Starting dozer uses PLADozerCommandSet, not ChinaDozerCommandSet.",
    },
    {
        "display": "Iran",
        "group": "IC",
        "side": "Iran",
        "object": "Iran_GlobalStore",
        "cmd": "Command_ConstructIran_GlobalStore",
        "replaced": "IranIndustrialComplex",
        "replaced_kind": "Industrial Complex",
        "old_cmd": "Command_ConstructIranIndustrialComplex",
        "slot": "2",
        "commandsets": ["IranDozerCommandSet"],
        "prereq_old": ["IranIndustrialComplex"],
        "note": "",
    },
    {
        "display": "America",
        "group": "SC",
        "side": "America",
        "object": "America_GlobalStore",
        "cmd": "Command_ConstructAmerica_GlobalStore",
        "replaced": "AmericaStrategyCenter_T",
        "replaced_kind": "Strategy Center (slot 2 AmericaStrategyCenter_T; slot 15 original SC kept)",
        "old_cmd": "Command_ConstructAmericaStrategyCenter_T",
        "slot": "2",
        "commandsets": ["AmericaDozerCommandSet"],
        "prereq_old": ["AmericaStrategyCenter_T"],
        "note": "Slot 15 Command_ConstructAmericaStrategyCenter left intact so one GS exists.",
    },
    {
        "display": "Israel",
        "group": "SC",
        "side": "Israel",
        "object": "Israel_GlobalStore",
        "cmd": "Command_ConstructIsrael_GlobalStore",
        "replaced": "AirF_AmericaStrategyCenter",
        "replaced_kind": "Strategy Center (Industry Planet / AirF_AmericaStrategyCenter)",
        "old_cmd": "AirF_Command_ConstructAmericaStrategyCenter",
        "slot": "2",
        "commandsets": ["IsraelDozerCommandSet"],
        "prereq_old": ["AirF_AmericaStrategyCenter"],
        "note": "AirF/Lazr/SupW America general dozers are not patched.",
    },
]

CS_NAMES = tuple(name for c in COUNTRIES for name in c["commandsets"])
CS_BY_NAME = {name: c for c in COUNTRIES for name in c["commandsets"]}
PREV19 = tuple(c["object"] for c in gs.COUNTRIES)
PROTECTED_CS = (
    "Iraq_VT72BCommandSet",
    "Iraq_WorkerCommandSet",
    "EgyptDozerCommandSet",
    "GermanyDozerCommandSet",
    "Japan_VT72BCommandSet",
    "AirF_AmericaDozerCommandSet",
    "Lazr_AmericaDozerCommandSet",
    "SupW_AmericaDozerCommandSet",
    "Nuke_ChinaDozerCommandSet",
    "ChinaDozerCommandSet",
)


def last_from(order, files, kind, name):
    return sk.last_block_from_files(order, files, kind, name)


def field(block: str, key: str) -> str:
    return sk.field(block, key)


def slot_map(block: str) -> dict[str, str]:
    return rad.slot_map(block)


def catalog_block(text: str, kind: str, name: str) -> str:
    return sk.last_block(text, kind, name)


def sha256_path(path: Path) -> str:
    return rad.sha256_path(path)


def clone_store(iraq: str, country: dict) -> str:
    return gs.clone_store(iraq, country)


def make_button(country: dict) -> str:
    return gs.make_button(country)


def patch_commandset(block: str, cs_name: str) -> str:
    country = CS_BY_NAME[cs_name]
    sl = slot_map(block)
    current = sl.get(country["slot"])
    if current not in (country["old_cmd"], country["cmd"]):
        raise SystemExit(f"{cs_name} slot {country['slot']} is {current}")
    new, n = re.subn(
        rf"(?m)^(\s*{country['slot']}\s*=\s*){re.escape(country['old_cmd'])}\s*$",
        rf"\g<1>{country['cmd']}",
        block.replace("\r\n", "\n"),
        count=1,
    )
    if n == 0 and sl.get(country["slot"]) == country["cmd"]:
        return block.replace("\r\n", "\n")
    if n != 1:
        raise SystemExit(f"failed to retarget {cs_name} slot {country['slot']}")
    return new


def patch_text_commandsets(text: str) -> tuple[str, list[str]]:
    text = text.replace("\r\n", "\n")
    patched = []
    for name in CS_NAMES:
        blk = catalog_block(text, "CommandSet", name)
        if not blk:
            continue
        text = sk.replace_last(text, "CommandSet", name, patch_commandset(blk, name))
        patched.append(name)
    return text, patched


def retarget_prereq(block: str, old: str, new: str) -> tuple[str, int]:
    """Replace old object token anywhere on Prerequisites Object= lines.

    America uses `Object = AmericaStrategyCenter AmericaStrategyCenter_T` (OR).
    Replacing only the token immediately after Object= would miss `_T`.
    """
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        body, n = re.subn(rf"\b{re.escape(old)}\b", new, m.group(0))
        count += n
        return body

    out = re.sub(r"(?ms)^[ \t]*Prerequisites\s*\r?\n.*?^[ \t]*End\s*$", repl, block)
    return out, count


def append_buttons(cb_text: str) -> str:
    text = cb_text.replace("\r\n", "\n")
    missing = []
    for country in COUNTRIES:
        if catalog_block(text, "CommandButton", country["cmd"]):
            continue
        missing.append(make_button(country).rstrip() + "\n")
    if missing:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + "\n".join(missing)
    return text


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_GLOBAL_STORE_EXPAND")
    if sha256_path(SRC_ART1) != SHA_ART1_SRC or SRC_ART1.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE baseline mismatch")
    if sha256_path(SRC_ART2) != SHA_ART2_SRC or SRC_ART2.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO baseline mismatch")

    print("parsing DATA...")
    files, order = sk.parse_big_ordered(SRC_DATA.read_bytes())
    original = dict(files)

    iraq_src, iraq = last_from(order, files, "Object", "Iraq_MIC")
    if iraq_src != MIC_OBJ_KEY:
        raise SystemExit(f"Iraq_MIC last-wins {iraq_src}")
    if field(iraq, "BuildCost") != COST or field(iraq, "DisplayName") != DISPLAY_KEY:
        raise SystemExit("Iraq_MIC is not the accepted Global Store")

    obj_parts = [clone_store(iraq, c) for c in COUNTRIES]
    files[OBJ_KEY] = sk.to_crlf("\n".join(obj_parts) + "\n")
    btn_parts = [make_button(c) for c in COUNTRIES]
    files[CB_ZZZZ] = sk.to_crlf("\n".join(btn_parts) + "\n")
    files[CB_INI] = sk.to_crlf(append_buttons(files[CB_INI].decode("latin1")))

    changed_cs_files = []
    for key in list(files):
        blob = files[key]
        if not key.lower().endswith(".ini"):
            continue
        if b"CommandSet " not in blob:
            continue
        if not any(f"CommandSet {name}".encode("ascii") in blob for name in CS_NAMES):
            continue
        text, patched = patch_text_commandsets(blob.decode("latin1"))
        if patched:
            files[key] = sk.to_crlf(text)
            changed_cs_files.append(f"{key}:{','.join(patched)}")

    cs_zzzz_parts = []
    for name in CS_NAMES:
        src, blk = last_from(order, original, "CommandSet", name)
        if not blk:
            raise SystemExit(f"missing CommandSet {name}")
        cs_zzzz_parts.append(patch_commandset(blk, name))
    files[CS_ZZZZ] = sk.to_crlf("\n".join(cs_zzzz_parts) + "\n")

    print("collecting last-wins objects for prereq retarget...")
    last_objs = gs.collect_last_objects(order, original)
    prereq_parts = []
    prereq_table = []
    prereq_detail = []
    for country in COUNTRIES:
        for old in country["prereq_old"]:
            hits = []
            for obj_name, (src, blk) in last_objs.items():
                if obj_name == old or obj_name.endswith("_GlobalStore"):
                    continue
                if field(blk, "Side") != country["side"]:
                    continue
                pr = re.search(r"(?ms)^\s*Prerequisites.*?(?:^\s*End)", blk)
                if not pr or not re.search(rf"\b{re.escape(old)}\b", pr.group(0)):
                    continue
                new_blk, nrep = retarget_prereq(blk, old, country["object"])
                if nrep < 1:
                    raise SystemExit(f"prereq retarget failed {obj_name} {old} n={nrep}")
                prereq_parts.append(new_blk)
                hits.append(obj_name)
                prereq_detail.append(
                    f"{country['display']}|{obj_name}|{old}->{country['object']}|same-side tech lockout"
                )
            prereq_table.append(f"{country['display']}|{old}|{country['object']}|{len(hits)}")
    files[PREREQ_KEY] = sk.to_crlf("\n\n".join(prereq_parts) + ("\n" if prereq_parts else ""))

    print("building DATA...")
    data_big = sk.build_big(files)
    packed, packed_order = sk.parse_big_ordered(data_big)
    fails: list[str] = []
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))

    live_cs = packed[CS_INI].decode("latin1")
    live_cb = packed[CB_INI].decode("latin1")
    table = [
        "country|group|replaced_kind|replaced_object|slot|old_cmd|gs_object|gs_cmd|cost|commandsets"
    ]
    for country in COUNTRIES:
        src, obj = last_from(packed_order, packed, "Object", country["object"])
        if src != OBJ_KEY:
            fails.append(f"{country['object']} last-wins {src}")
        if field(obj, "Side") != country["side"]:
            fails.append(f"{country['object']} Side {field(obj, 'Side')}")
        if field(obj, "BuildCost") != COST:
            fails.append(f"{country['object']} cost {field(obj, 'BuildCost')}")
        if field(obj, "DisplayName") != DISPLAY_KEY:
            fails.append(f"{country['object']} DisplayName")
        if field(obj, "CommandSet") != "Iraq_MICCommandSet":
            fails.append(f"{country['object']} CommandSet")
        if "IQ__IQFlag_HsGM" not in obj:
            fails.append(f"{country['object']} missing HsGM")
        if "OCL_AbbasResearchObject" in obj:
            fails.append(f"{country['object']} inherited Abbas research")
        btn = catalog_block(live_cb, "CommandButton", country["cmd"])
        zbtn = catalog_block(packed[CB_ZZZZ].decode("latin1"), "CommandButton", country["cmd"])
        for label, blk in (("LIVE", btn), ("ZZZZ", zbtn)):
            if field(blk, "Command") != "DOZER_CONSTRUCT":
                fails.append(f"{label} {country['cmd']} Command")
            if field(blk, "Object") != country["object"]:
                fails.append(f"{label} {country['cmd']} Object")
            if field(blk, "ButtonImage") != "Button_GlobalMarket":
                fails.append(f"{label} {country['cmd']} image")
            if field(blk, "TextLabel") != "CONTROLBAR:ConstructIraq_MIC":
                fails.append(f"{label} {country['cmd']} TextLabel")
        gs_slots = [s for s, v in slot_map(
            last_from(packed_order, packed, "CommandSet", country["commandsets"][0])[1]
        ).items() if v == country["cmd"]]
        if gs_slots != [country["slot"]]:
            fails.append(f"{country['display']} GS slots {gs_slots}")
        for cs_name in country["commandsets"]:
            live_blk = catalog_block(live_cs, "CommandSet", cs_name)
            src_cs, packed_cs = last_from(packed_order, packed, "CommandSet", cs_name)
            zzzz_cs = catalog_block(packed[CS_ZZZZ].decode("latin1"), "CommandSet", cs_name)
            for label, blk in (("LIVE", live_blk), ("PACKED", packed_cs), ("ZZZZ", zzzz_cs)):
                sl = slot_map(blk)
                if sl.get(country["slot"]) != country["cmd"]:
                    fails.append(
                        f"{label} {cs_name} slot {country['slot']}={sl.get(country['slot'])}"
                    )
                if country["old_cmd"] in sl.values():
                    fails.append(f"{label} {cs_name} still has {country['old_cmd']}")
            orig_sl = slot_map(last_from(order, original, "CommandSet", cs_name)[1])
            new_sl = slot_map(packed_cs)
            expect = dict(orig_sl)
            expect[country["slot"]] = country["cmd"]
            if new_sl != expect:
                fails.append(f"{cs_name} unexpected extra slot changes")
        orig_o = last_from(order, original, "Object", country["replaced"])[1]
        new_o = last_from(packed_order, packed, "Object", country["replaced"])[1]
        if orig_o != new_o:
            fails.append(f"replaced object mutated {country['replaced']}")
        table.append(
            "|".join(
                [
                    country["display"],
                    country["group"],
                    country["replaced_kind"],
                    country["replaced"],
                    country["slot"],
                    country["old_cmd"],
                    country["object"],
                    country["cmd"],
                    COST,
                    ",".join(country["commandsets"]),
                ]
            )
        )

    america_sl = slot_map(last_from(packed_order, packed, "CommandSet", "AmericaDozerCommandSet")[1])
    if america_sl.get("15") != "Command_ConstructAmericaStrategyCenter":
        fails.append("America slot 15 original SC lost")
    if america_sl.get("2") != "Command_ConstructAmerica_GlobalStore":
        fails.append("America slot 2 is not Global Store")

    src_mic, mic = last_from(packed_order, packed, "Object", "Iraq_MIC")
    orig_mic = last_from(order, original, "Object", "Iraq_MIC")[1]
    if mic != orig_mic:
        fails.append("Iraq_MIC mutated")
    src_btn, iraq_btn = last_from(packed_order, packed, "CommandButton", "Command_ConstructIraq_MIC")
    orig_btn = last_from(order, original, "CommandButton", "Command_ConstructIraq_MIC")[1]
    if iraq_btn != orig_btn:
        fails.append("Command_ConstructIraq_MIC mutated")

    for name in PREV19:
        orig_o = last_from(order, original, "Object", name)[1]
        new_o = last_from(packed_order, packed, "Object", name)[1]
        if orig_o != new_o:
            fails.append(f"PR669 GS mutated {name}")
        if last_from(packed_order, packed, "Object", name)[0] != PREV_OBJ:
            fails.append(f"PR669 GS last-wins moved {name}")

    for c19 in gs.COUNTRIES:
        packed_cs = slot_map(last_from(packed_order, packed, "CommandSet", c19["commandsets"][0])[1])
        orig_cs = slot_map(last_from(order, original, "CommandSet", c19["commandsets"][0])[1])
        if packed_cs != orig_cs:
            fails.append(f"PR669 CS mutated {c19['commandsets'][0]}")
        if packed_cs.get(c19["slot"]) != c19["cmd"]:
            fails.append(f"PR669 lost GS slot {c19['display']}")

    expect_mic = {item["slot"]: item["cmd"] for item in rad.COPIES}
    expect_mic["15"] = rad.SELL
    for name in rad.MIC_CS_NAMES:
        packed_mic = slot_map(last_from(packed_order, packed, "CommandSet", name)[1])
        orig_mic_cs = slot_map(last_from(order, original, "CommandSet", name)[1])
        if packed_mic != expect_mic or orig_mic_cs != packed_mic:
            fails.append(f"MIC menu mutated {name}")

    orig_t3 = slot_map(last_from(order, original, "CommandSet", rad.WF_CS_NAME)[1])
    packed_t3 = slot_map(last_from(packed_order, packed, "CommandSet", rad.WF_CS_NAME)[1])
    if orig_t3 != packed_t3:
        fails.append("WF T3 mutated")

    iraq_dozer = slot_map(catalog_block(live_cs, "CommandSet", "Iraq_VT72BCommandSet"))
    orig_dozer = slot_map(
        catalog_block(original[CS_INI].decode("latin1"), "CommandSet", "Iraq_VT72BCommandSet")
    )
    if iraq_dozer != orig_dozer or iraq_dozer.get("6") != "Command_ConstructIraq_MIC":
        fails.append("Iraq dozer mutated")

    for name in PROTECTED_CS:
        orig_src, orig_blk = last_from(order, original, "CommandSet", name)
        new_src, new_blk = last_from(packed_order, packed, "CommandSet", name)
        if orig_blk != new_blk:
            fails.append(f"protected CS mutated {name}")

    for country in uav.COUNTRIES:
        orig_slots = slot_map(last_from(order, original, "CommandSet", country["cs"])[1])
        packed_slots = slot_map(last_from(packed_order, packed, "CommandSet", country["cs"])[1])
        if orig_slots != packed_slots:
            fails.append(f"UAV CS mutated {country['cs']}")

    csf = packed[CSF_KEY]
    orig_csf = original[CSF_KEY]
    if csf != orig_csf:
        fails.append("CSF mutated")
    if sk.csf_get(csf, DISPLAY_KEY) != NAME:
        fails.append("CSF Global Store name lost")
    if sk.csf_get(csf, "CONTROLBAR:ToolTipIraq_MIC") != TIP:
        fails.append("tooltip lost")

    packed_last = gs.collect_last_objects(packed_order, packed)
    for country in COUNTRIES:
        for old in country["prereq_old"]:
            for obj_name, (_src, blk) in packed_last.items():
                if obj_name in {country["object"], old}:
                    continue
                if field(blk, "Side") != country["side"]:
                    continue
                pr = re.search(r"(?ms)^\s*Prerequisites.*?(?:^\s*End)", blk)
                if pr and re.search(rf"\b{re.escape(old)}\b", pr.group(0)):
                    fails.append(f"{obj_name} still requires {old}")

    if packed.get(PREV_OBJ) != original.get(PREV_OBJ):
        fails.append("PR669 CountryGlobalStores.ini mutated")

    if CS_ZZZZ.lower() <= PREV_CS.lower():
        fails.append("CS overlay does not sort after PR669 overlay")
    if PREREQ_KEY.lower() <= PREV_PREREQ.lower():
        fails.append("prereq overlay does not sort after PR669 prereq")

    allowed = {OBJ_KEY, CB_ZZZZ, CS_ZZZZ, PREREQ_KEY, CB_INI}
    for key, blob in original.items():
        if key in allowed:
            continue
        if key == CS_INI:
            continue
        if any(f"CommandSet {name}".encode("ascii") in blob for name in CS_NAMES):
            continue
        if packed.get(key) != blob:
            fails.append(f"unrelated DATA mutated {key}")

    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails[:80]) + f"\n({len(fails)} total)")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art1_path = OUT / "_SPEC_ART_ONE.big"
    art2_path = OUT / "_SPEC_ART_TWO.big"
    data_path.write_bytes(data_big)
    shutil.copy2(SRC_ART1, art1_path)
    shutil.copy2(SRC_ART2, art2_path)

    LOOSE.joinpath("Object/Specter/GlobalStore").mkdir(parents=True, exist_ok=True)
    (LOOSE / "Object/Specter/GlobalStore/CountryGlobalStoresFive.ini").write_bytes(files[OBJ_KEY])
    (LOOSE / "CommandButton_ZZZZ_ZGlobalStoreFive.ini").write_bytes(files[CB_ZZZZ])
    (LOOSE / "CommandSet_ZZZZ_ZGlobalStoreFive.ini").write_bytes(files[CS_ZZZZ])

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "CountryGlobalStoresFive.ini").write_bytes(files[OBJ_KEY])
    (ext / "COUNTRY_TABLE.txt").write_text("\n".join(table) + "\n", encoding="utf-8")
    (ext / "PREREQ_RETARGET.txt").write_text(
        "\n".join(prereq_table + [""] + prereq_detail) + "\n", encoding="utf-8"
    )

    (OUT / "INSTALL.txt").write_text(
        "\n".join(
            [
                "SPECTER GLOBAL STORE FIVE — INSTALL",
                "",
                "Keep the split ART arrangement. Do not recombine ART.",
                "Place all three uncompressed BIGs next to generals.exe:",
                "  _SPEC_DATA_ONE.big",
                "  _SPEC_ART_ONE.big",
                "  _SPEC_ART_TWO.big",
                "",
                "Zero Hour auto-loads every *.big in that folder.",
                "Replace SPECTER_GLOBAL_STORE_EXPAND DATA. ART is unchanged from PR #669.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "Global Store added to Russia, China, Iran, America, and Israel. "
        "ART unchanged from PR #669. RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    zip_path = OUT / "SPECTER_GLOBAL_STORE_FIVE.zip"
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
    tag = "s-global-store-five"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/" + tag
    )
    prev_art = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/"
        "s-global-store-expand"
    )
    report = "\n".join(
        [
            "STATIC VALIDATION: PASS",
            "RUNTIME_TEST=NOT RUN",
            "BASELINE: PR #669 SPECTER_GLOBAL_STORE_EXPAND",
            "COUNTRIES=5 (Russia China Iran Industrial Complex; America Israel Strategy Center)",
            "IRAQ_GLOBAL_STORE_UNCHANGED=YES",
            "PR669_19_GLOBAL_STORES_UNCHANGED=YES",
            "ART_UNCHANGED=YES",
            "MIC_SLOTS_1_14_SELL_15=YES",
            "UAV_SLOTS_9_12_UNCHANGED=YES",
            "WF_T3_UNCHANGED=YES",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_ONE_SIZE={art1_path.stat().st_size}",
            f"ART_ONE_SHA256={art1_sha}",
            f"ART_TWO_SIZE={art2_path.stat().st_size}",
            f"ART_TWO_SHA256={art2_sha}",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "RUNTIME_TEST=NOT RUN",
            "",
            *table,
            "",
            "PREREQ_RETARGET:",
            *prereq_table,
            "",
            "PREREQ_DETAIL:",
            *prereq_detail,
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
                "ZIP_FILE=SPECTER_GLOBAL_STORE_FIVE.zip",
                f"ZIP_SIZE={zip_path.stat().st_size}",
                f"ZIP_SHA256={zip_sha}",
                "BASELINE=PR #669",
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
                "ART textures (unchanged; standalone asset on tag s-iraq-global-store-name):",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-global-store-name/_SPEC_ART_ONE.big",
                f"  SIZE={art1_path.stat().st_size}",
                f"  SHA256={art1_sha}",
                "",
                "ART models (unchanged from PR #669 / tag s-global-store-expand):",
                f"  {prev_art}/_SPEC_ART_TWO.big",
                f"  SIZE={art2_path.stat().st_size}",
                f"  SHA256={art2_sha}",
                "",
                "ZIP:",
                f"  {rel_base}/SPECTER_GLOBAL_STORE_FIVE.zip",
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
                "# Global Store for Russia, China, Iran, America, and Israel",
                "",
                "Adds country-specific Global Store copies of `Iraq_MIC` for five",
                "countries, replacing Industrial Complex (Russia, China, Iran) or",
                "Strategy Center (America slot 2 `_T`, Israel Industry Planet).",
                "",
                "Name remains **Global Store**, cost **$7,000**. Production slots",
                "1–14 plus Sell at 15 and the enlarged HsGM flag are unchanged.",
                "ART is byte-identical to PR #669. The 19 existing Global Stores",
                "and Iraq's original building are not rebuilt.",
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
    print("STATIC VALIDATION: PASS")
    print("RUNTIME_TEST=NOT RUN")
    print("CS files", len(changed_cs_files))
    print("prereq objects", len(prereq_parts))


if __name__ == "__main__":
    main()
