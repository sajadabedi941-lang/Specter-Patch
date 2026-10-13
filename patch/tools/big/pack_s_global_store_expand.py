#!/usr/bin/env python3
"""Expand Iraq Global Store to 19 countries and enlarge the isolated GS flag.

Baseline packed archives: SPECTER_IRAQ_GLOBAL_STORE_NAME (PR #668).
Iraq_MIC remains the authoritative Global Store. Country copies reuse its
model, futuristic flag, production CommandSet, $7000 cost, and marketplace
text. ART_ONE is copied byte-identical.

Group A (15): replace Strategy Center construction, except MENA7 which has
no Strategy Center in packed last-wins — SPECTER's analogue is the empty
country MIC at dozer/worker slot 6 (Button_GlobalMarket). Documented below.
Group B (4): replace C-RAM construction at VT72B slot 13.

Flag: scale FLAG01-03 + HOUSECOLOR01-03 meshes in IQ__IQFlag_HsGM.W3D by
1.25 about the pole axis / cloth baseline. LINE01 pole, HsWF, and HsCU
stay byte-identical. SpecterFuturisticFlag.tga is not stretched.
"""
from __future__ import annotations

import math
import re
import shutil
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_iraq_mic_radar_ad as rad  # noqa: E402
import pack_s_radar_uav_slots as uav  # noqa: E402
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_GLOBAL_STORE_NAME/_SPEC_DATA_ONE.big"
SRC_ART1 = ROOT / "patch/Release/SPECTER_IRAQ_GLOBAL_STORE_NAME/_SPEC_ART_ONE.big"
SRC_ART2 = ROOT / "patch/Release/SPECTER_IRAQ_GLOBAL_STORE_NAME/_SPEC_ART_TWO.big"
OUT = ROOT / "patch/Release/SPECTER_GLOBAL_STORE_EXPAND"
INSTALLER = ROOT / "patch/tools/installer"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "86882e2d6116f0b137dc0e198f8276203bdcdc8a3968ad8a40b140391e203215"
SIZE_DATA_SRC = 370921399
SHA_ART1_SRC = "9dc4524ccb44881fcd0149957d2fcce1d378db1483e6c458df67e07c86a86aa8"
SIZE_ART1_SRC = 2144972013
SHA_ART2_SRC = "c2985f5a7bd53ab1a465c30bb85357db05aaa2724d12fabc92492fe12486bf10"
SIZE_ART2_SRC = 307254782
SAGE_SAFE = 2147483648

CS_INI = r"Data\INI\CommandSet.ini"
CB_INI = r"Data\INI\CommandButton.ini"
CSF_KEY = sk.CSF_KEY
MIC_OBJ_KEY = rad.MIC_OBJ_KEY
WF_OBJ_KEY = rad.WF_OBJ_KEY
CC_OBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_CommandCenter.ini"
OBJ_KEY = r"Data\INI\Object\Specter\GlobalStore\CountryGlobalStores.ini"
CB_ZZZZ = r"Data\INI\CommandButton_ZZZZ_ZGlobalStoreExpand.ini"
CS_ZZZZ = r"Data\INI\CommandSet_ZZZZ_ZGlobalStoreExpand.ini"
PREREQ_KEY = r"Data\INI\Object_ZZZZ_ZGlobalStorePrereq.ini"
FLAG_W3D = r"Art\W3D\IQ__IQFlag_HsGM.W3D"
FLAG_WF = r"Art\W3D\IQ__IQFlag_HsWF.W3D"
FLAG_CU = r"Art\W3D\IQ__IQFlag_HsCU.W3D"
FLAG_TEX = r"Art\Textures\SpecterFuturisticFlag.tga"

DISPLAY_KEY = "OBJECT:IraqGlobalStore"
NAME = "Global Store"
DESC_TITLE = "Global Aerospace Market"
DESC_BODY = (
    "An international marketplace for aviation systems, reconnaissance drones, "
    "radar technology, and air-defense equipment."
)
TIP = f"{DESC_TITLE}\n\n{DESC_BODY}"
COST = "7000"
FLAG_SCALE = 1.25
IRAQ_RESEARCH = re.compile(
    r"(?ms)^  Behavior = ObjectCreationUpgrade ModuleTag_(?:14421|6719)\r?\n.*?^  End\r?\n"
)
SLOT_RE = rad.SLOT_RE
MESH_HEADER = 0x0000001F
VERTICES = 0x00000002
SCALE_MESHES = {
    "FLAG01",
    "FLAG02",
    "FLAG03",
    "HOUSECOLOR01",
    "HOUSECOLOR02",
    "HOUSECOLOR03",
}

# Packed last-wins audit (PR #668 DATA). Dozer CommandSet names come from the
# starting-unit objects, not guessed suffixes.
COUNTRIES = [
    {
        "display": "Germany",
        "group": "A",
        "side": "Germany",
        "object": "Germany_GlobalStore",
        "cmd": "Command_ConstructGermany_GlobalStore",
        "replaced": "GermanyStrategyCenter",
        "replaced_kind": "Strategy Center",
        "old_cmd": "Command_ConstructGermanyStrategyCenter",
        "slot": "2",
        "commandsets": ["GermanyDozerCommandSet"],
        "prereq_old": ["GermanyStrategyCenter"],
    },
    {
        "display": "France",
        "group": "A",
        "side": "France",
        "object": "France_GlobalStore",
        "cmd": "Command_ConstructFrance_GlobalStore",
        "replaced": "FranceStrategyCenter",
        "replaced_kind": "Strategy Center",
        "old_cmd": "Command_ConstructFranceStrategyCenter",
        "slot": "2",
        "commandsets": ["FranceDozerCommandSet"],
        "prereq_old": ["FranceStrategyCenter"],
    },
    {
        "display": "Britain",
        "group": "A",
        "side": "Britain",
        "object": "Britain_GlobalStore",
        "cmd": "Command_ConstructBritain_GlobalStore",
        "replaced": "BritainStrategyCenter",
        "replaced_kind": "Strategy Center",
        "old_cmd": "Command_ConstructBritainStrategyCenter",
        "slot": "2",
        "commandsets": ["BritainDozerCommandSet"],
        "prereq_old": ["BritainStrategyCenter"],
    },
    {
        "display": "Italy",
        "group": "A",
        "side": "Italy",
        "object": "Italy_GlobalStore",
        "cmd": "Command_ConstructItaly_GlobalStore",
        "replaced": "ItalyStrategyCenter",
        "replaced_kind": "Strategy Center",
        "old_cmd": "Command_ConstructItalyStrategyCenter",
        "slot": "2",
        "commandsets": ["ItalyDozerCommandSet"],
        "prereq_old": ["ItalyStrategyCenter"],
    },
    {
        "display": "NATO",
        "group": "A",
        "side": "Nato",
        "object": "Nato_GlobalStore",
        "cmd": "Command_ConstructNato_GlobalStore",
        "replaced": "NatoStrategyCenter",
        "replaced_kind": "Strategy Center",
        "old_cmd": "Command_ConstructNatoStrategyCenter",
        "slot": "2",
        "commandsets": ["NatoDozerCommandSet"],
        "prereq_old": ["NatoStrategyCenter"],
    },
    {
        "display": "Ukraine",
        "group": "A",
        "side": "Ukraine",
        "object": "Ukraine_GlobalStore",
        "cmd": "Command_ConstructUkraine_GlobalStore",
        "replaced": "UkraineStrategyCenter",
        "replaced_kind": "Strategy Center",
        "old_cmd": "Command_ConstructUkraineStrategyCenter",
        "slot": "2",
        "commandsets": ["UkraineDozerCommandSet"],
        "prereq_old": ["UkraineStrategyCenter"],
    },
    {
        "display": "Turkey",
        "group": "A",
        "side": "Turkey",
        "object": "Turkey_GlobalStore",
        "cmd": "Command_ConstructTurkey_GlobalStore",
        "replaced": "TurkeyStrategyCenter",
        "replaced_kind": "Strategy Center",
        "old_cmd": "Command_ConstructTurkeyStrategyCenter",
        "slot": "2",
        "commandsets": ["TurkeyDozerCommandSet"],
        "prereq_old": ["TurkeyStrategyCenter"],
    },
    {
        "display": "Sweden",
        "group": "A",
        "side": "Sweden",
        "object": "Sweden_GlobalStore",
        "cmd": "Command_ConstructSweden_GlobalStore",
        "replaced": "SwedenStrategyCenter",
        "replaced_kind": "Strategy Center",
        "old_cmd": "Command_ConstructSwedenStrategyCenter",
        "slot": "2",
        "commandsets": ["SwedenDozerCommandSet"],
        "prereq_old": ["SwedenStrategyCenter"],
    },
    {
        "display": "UAE",
        "group": "A",
        "side": "UAE",
        "object": "UAE_GlobalStore",
        "cmd": "Command_ConstructUAE_GlobalStore",
        "replaced": "UAE_MIC",
        "replaced_kind": "MIC (no Strategy Center; slot-6 Global Market analogue)",
        "old_cmd": "Command_ConstructUAE_MIC",
        "slot": "6",
        "commandsets": ["UAEDozerCommandSet", "UAE_WorkerCommandSet", "UAE_VT72BCommandSet"],
        "prereq_old": ["UAE_MIC"],
    },
    {
        "display": "India",
        "group": "A",
        "side": "India",
        "object": "India_GlobalStore",
        "cmd": "Command_ConstructIndia_GlobalStore",
        "replaced": "India_MIC",
        "replaced_kind": "MIC (no Strategy Center; slot-6 Global Market analogue)",
        "old_cmd": "Command_ConstructIndia_MIC",
        "slot": "6",
        "commandsets": ["IndiaDozerCommandSet", "India_WorkerCommandSet", "India_VT72BCommandSet"],
        "prereq_old": ["India_MIC"],
    },
    {
        "display": "Pakistan",
        "group": "A",
        "side": "Pakistan",
        "object": "Pakistan_GlobalStore",
        "cmd": "Command_ConstructPakistan_GlobalStore",
        "replaced": "Pakistan_MIC",
        "replaced_kind": "MIC (no Strategy Center; slot-6 Global Market analogue)",
        "old_cmd": "Command_ConstructPakistan_MIC",
        "slot": "6",
        "commandsets": [
            "PakistanDozerCommandSet",
            "Pakistan_WorkerCommandSet",
            "Pakistan_VT72BCommandSet",
        ],
        "prereq_old": ["Pakistan_MIC"],
    },
    {
        "display": "Syria",
        "group": "A",
        "side": "Syria",
        "object": "Syria_GlobalStore",
        "cmd": "Command_ConstructSyria_GlobalStore",
        "replaced": "Syria_MIC",
        "replaced_kind": "MIC (no Strategy Center; slot-6 Global Market analogue)",
        "old_cmd": "Command_ConstructSyria_MIC",
        "slot": "6",
        "commandsets": ["SyriaDozerCommandSet", "Syria_WorkerCommandSet", "Syria_VT72BCommandSet"],
        "prereq_old": ["Syria_MIC"],
    },
    {
        "display": "Saudi Arabia",
        "group": "A",
        "side": "SaudiArabia",
        "object": "SaudiArabia_GlobalStore",
        "cmd": "Command_ConstructSaudiArabia_GlobalStore",
        "replaced": "SaudiArabia_MIC",
        "replaced_kind": "MIC (no Strategy Center; slot-6 Global Market analogue)",
        "old_cmd": "Command_ConstructSaudiArabia_MIC",
        "slot": "6",
        "commandsets": [
            "SaudiArabiaDozerCommandSet",
            "SaudiArabia_WorkerCommandSet",
            "SaudiArabia_VT72BCommandSet",
        ],
        "prereq_old": ["SaudiArabia_MIC"],
    },
    {
        "display": "Libya",
        "group": "A",
        "side": "Libya",
        "object": "Libya_GlobalStore",
        "cmd": "Command_ConstructLibya_GlobalStore",
        "replaced": "Libya_MIC",
        "replaced_kind": "MIC (no Strategy Center; slot-6 Global Market analogue)",
        "old_cmd": "Command_ConstructLibya_MIC",
        "slot": "6",
        "commandsets": ["LibyaDozerCommandSet", "Libya_WorkerCommandSet", "Libya_VT72BCommandSet"],
        "prereq_old": ["Libya_MIC"],
    },
    {
        "display": "South Africa",
        "group": "A",
        "side": "SouthAfrica",
        "object": "SouthAfrica_GlobalStore",
        "cmd": "Command_ConstructSouthAfrica_GlobalStore",
        "replaced": "SouthAfrica_MIC",
        "replaced_kind": "MIC (no Strategy Center; slot-6 Global Market analogue)",
        "old_cmd": "Command_ConstructSouthAfrica_MIC",
        "slot": "6",
        "commandsets": [
            "SouthAfricaDozerCommandSet",
            "SouthAfrica_WorkerCommandSet",
            "SouthAfrica_VT72BCommandSet",
        ],
        "prereq_old": ["SouthAfrica_MIC"],
    },
    {
        "display": "Japan",
        "group": "B",
        "side": "Japan",
        "object": "Japan_GlobalStore",
        "cmd": "Command_ConstructJapan_GlobalStore",
        "replaced": "Japan_CRAM",
        "replaced_kind": "C-RAM",
        "old_cmd": "Command_ConstructJapan_CRAM",
        "slot": "13",
        "commandsets": ["Japan_VT72BCommandSet"],
        "prereq_old": [],
    },
    {
        "display": "Vietnam",
        "group": "B",
        "side": "Vietnam",
        "object": "Vietnam_GlobalStore",
        "cmd": "Command_ConstructVietnam_GlobalStore",
        "replaced": "Vietnam_CRAM",
        "replaced_kind": "C-RAM",
        "old_cmd": "Command_ConstructVietnam_CRAM",
        "slot": "13",
        "commandsets": ["Vietnam_VT72BCommandSet"],
        "prereq_old": [],
    },
    {
        "display": "South Korea",
        "group": "B",
        "side": "SouthKorea",
        "object": "SouthKorea_GlobalStore",
        "cmd": "Command_ConstructSouthKorea_GlobalStore",
        "replaced": "SouthKorea_CRAM",
        "replaced_kind": "C-RAM",
        "old_cmd": "Command_ConstructSouthKorea_CRAM",
        "slot": "13",
        "commandsets": ["SouthKorea_VT72BCommandSet"],
        "prereq_old": [],
    },
    {
        "display": "North Korea",
        "group": "B",
        "side": "NorthKorea",
        "object": "NorthKorea_GlobalStore",
        "cmd": "Command_ConstructNorthKorea_GlobalStore",
        "replaced": "NorthKorea_CRAM",
        "replaced_kind": "C-RAM",
        "old_cmd": "Command_ConstructNorthKorea_CRAM",
        "slot": "13",
        "commandsets": ["NorthKorea_VT72BCommandSet"],
        "prereq_old": [],
    },
]

PROTECTED_CS = (
    "Iraq_VT72BCommandSet",
    "Iraq_WorkerCommandSet",
    "EgyptDozerCommandSet",
    "Egypt_VT72BCommandSet",
    "IranDozerCommandSet",
    "RussiaDozerCommandSet",
    "PLADozerCommandSet",
    "AmericaDozerCommandSet",
    "IsraelDozerCommandSet",
    "ChinaDozerCommandSet",
)
CS_NAMES = tuple(name for c in COUNTRIES for name in c["commandsets"])
CS_BY_NAME = {name: c for c in COUNTRIES for name in c["commandsets"]}


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
    text = iraq.replace("\r\n", "\n")
    if not text.startswith("Object Iraq_MIC"):
        raise SystemExit("Iraq_MIC header mismatch")
    text = IRAQ_RESEARCH.sub("", text)
    if "OCL_AbbasResearchObject" in text or "OCL_HussienResearchObject" in text:
        raise SystemExit("Iraq research modules still present")
    text = text.replace("Object Iraq_MIC", f"Object {country['object']}", 1)
    text = re.sub(r"(?m)^(\s*Side\s*=\s*)Iraq\s*$", rf"\g<1>{country['side']}", text, count=1)
    note = (
        f"; SPECTER country Global Store copy of Iraq_MIC for {country['display']}. "
        f"Side={country['side']}; BuildCost={COST}; production=Iraq_MICCommandSet; "
        "Iraq Abbas/Hussein ObjectCreationUpgrade modules omitted."
    )
    lines = text.split("\n")
    text = f"{lines[0]}\n{note}\n" + "\n".join(lines[1:])
    if not text.endswith("\n"):
        text += "\n"
    return text


def make_button(country: dict) -> str:
    return (
        f"CommandButton {country['cmd']}\n"
        f"  Command       = DOZER_CONSTRUCT\n"
        f"  Object        = {country['object']}\n"
        f"  TextLabel     = CONTROLBAR:ConstructIraq_MIC\n"
        f"  ButtonImage   = Button_GlobalMarket\n"
        f"  ButtonBorderType        = BUILD\n"
        f"  DescriptLabel           = CONTROLBAR:ToolTipIraq_MIC\n"
        f"End\n"
    )


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


def retarget_prereq(block: str, old: str, new: str) -> tuple[str, int]:
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        body, n = re.subn(
            rf"(?m)^(\s*Object\s*=\s*){re.escape(old)}(\b)",
            rf"\1{new}\2",
            m.group(0),
        )
        count += n
        return body

    out = re.sub(r"(?ms)^[ \t]*Prerequisites\s*\r?\n.*?^[ \t]*End\s*$", repl, block)
    return out, count


def collect_last_objects(order, files):
    found: dict[str, tuple[str, str]] = {}
    obj_re = re.compile(r"(?ms)^Object (\S+)\r?\n.*?^End")
    for key in order:
        blob = files[key]
        if b"Object " not in blob:
            continue
        try:
            text = blob.decode("latin1")
        except Exception:
            continue
        for m in obj_re.finditer(text):
            found[m.group(1)] = (key, m.group(0))
    return found


def scale_hsgm(blob: bytes, scale: float = FLAG_SCALE) -> bytes:
    out = bytearray(blob)
    mesh = ""
    header_at = -1
    verts: dict[str, tuple[int, int, list[tuple[float, float, float]]]] = {}

    def rec(start: int, stop: int) -> None:
        nonlocal mesh, header_at
        p = start
        while p + 8 <= stop:
            cid, raw = struct.unpack_from("<II", out, p)
            sz = raw & 0x7FFFFFFF
            cont = bool(raw & 0x80000000)
            cs, ce = p + 8, p + 8 + sz
            if ce > stop:
                break
            if cid == MESH_HEADER and ce - cs >= 116:
                mesh = out[cs + 8 : cs + 24].split(b"\x00", 1)[0].decode("latin1")
                header_at = cs
            if cont:
                rec(cs, ce)
            elif cid == VERTICES and mesh in SCALE_MESHES:
                n = sz // 12
                pts = []
                for i in range(n):
                    pts.append(struct.unpack_from("<fff", out, cs + i * 12))
                verts[mesh] = (header_at, cs, pts)
            p = ce

    rec(0, len(out))
    if set(verts) != SCALE_MESHES:
        raise SystemExit(f"HsGM scale meshes {sorted(verts)} != {sorted(SCALE_MESHES)}")
    for name, (hcs, vcs, pts) in verts.items():
        ys = [p[1] for p in pts]
        ymin = min(ys)
        scaled = []
        for x, y, z in pts:
            scaled.append((x * scale, ymin + (y - ymin) * scale, z * scale))
        for i, (x, y, z) in enumerate(scaled):
            struct.pack_into("<fff", out, vcs + i * 12, x, y, z)
        xs = [p[0] for p in scaled]
        ys = [p[1] for p in scaled]
        zs = [p[2] for p in scaled]
        mn = (min(xs), min(ys), min(zs))
        mx = (max(xs), max(ys), max(zs))
        sph = ((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2)
        radius = math.sqrt(sum((mx[i] - sph[i]) ** 2 for i in range(3))) * 1.05
        struct.pack_into("<fff", out, hcs + 76, *mn)
        struct.pack_into("<fff", out, hcs + 88, *mx)
        struct.pack_into("<fff", out, hcs + 100, *sph)
        struct.pack_into("<f", out, hcs + 112, radius)
    if FLAG_WF.split("\\")[-1].encode() in out:
        pass
    return bytes(out)


def mesh_vert_aabb(blob: bytes) -> dict[str, tuple[float, ...]]:
    found: dict[str, tuple[float, ...]] = {}
    mesh = ""

    def rec(start: int, stop: int) -> None:
        nonlocal mesh
        p = start
        while p + 8 <= stop:
            cid, raw = struct.unpack_from("<II", blob, p)
            sz = raw & 0x7FFFFFFF
            cont = bool(raw & 0x80000000)
            cs, ce = p + 8, p + 8 + sz
            if ce > stop:
                break
            if cid == MESH_HEADER and ce - cs >= 24:
                mesh = blob[cs + 8 : cs + 24].split(b"\x00", 1)[0].decode("latin1")
            if cont:
                rec(cs, ce)
            elif cid == VERTICES:
                n = sz // 12
                xs, ys, zs = [], [], []
                for i in range(n):
                    x, y, z = struct.unpack_from("<fff", blob, cs + i * 12)
                    xs.append(x)
                    ys.append(y)
                    zs.append(z)
                if xs:
                    found[mesh] = (
                        min(xs),
                        max(xs),
                        min(ys),
                        max(ys),
                        min(zs),
                        max(zs),
                        n,
                    )
            p = ce

    rec(0, len(blob))
    return found


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_IRAQ_GLOBAL_STORE_NAME")
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
        raise SystemExit("Iraq_MIC is not the PR #668 Global Store")
    if "IQ__IQFlag_HsGM" not in iraq:
        raise SystemExit("Iraq_MIC missing HsGM flag")

    obj_parts = [clone_store(iraq, c) for c in COUNTRIES]
    files[OBJ_KEY] = sk.to_crlf("\n".join(obj_parts) + "\n")

    btn_parts = [make_button(c) for c in COUNTRIES]
    files[CB_ZZZZ] = sk.to_crlf("\n".join(btn_parts) + "\n")
    files[CB_INI] = sk.to_crlf(append_buttons(files[CB_INI].decode("latin1")))

    cs_zzzz_parts = []
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

    for name in CS_NAMES:
        src, blk = last_from(order, original, "CommandSet", name)
        if not blk:
            raise SystemExit(f"missing CommandSet {name}")
        cs_zzzz_parts.append(patch_commandset(blk, name))
    files[CS_ZZZZ] = sk.to_crlf("\n".join(cs_zzzz_parts) + "\n")

    print("collecting last-wins objects for prereq retarget...")
    last_objs = collect_last_objects(order, original)
    prereq_parts = []
    prereq_table = []
    for country in COUNTRIES:
        for old in country["prereq_old"]:
            hits = []
            for obj_name, (src, blk) in last_objs.items():
                if obj_name == old or obj_name.endswith("_GlobalStore"):
                    continue
                if field(blk, "Side") != country["side"]:
                    continue
                if not re.search(rf"(?m)^\s*Object\s*=\s*{re.escape(old)}\b", blk):
                    continue
                new_blk, nrep = retarget_prereq(blk, old, country["object"])
                if nrep < 1:
                    raise SystemExit(f"prereq retarget failed {obj_name} {old} n={nrep}")
                if re.search(rf"(?m)^\s*Object\s*=\s*{re.escape(old)}\b", new_blk):
                    raise SystemExit(f"{obj_name} still names {old} after retarget")
                prereq_parts.append(new_blk)
                hits.append(obj_name)
            prereq_table.append(f"{country['display']}|{old}|{country['object']}|{len(hits)}")
    files[PREREQ_KEY] = sk.to_crlf("\n\n".join(prereq_parts) + ("\n" if prereq_parts else ""))

    print("parsing ART_TWO...")
    art2, _ = sk.parse_big_ordered(SRC_ART2.read_bytes())
    original_hsgm = art2[FLAG_W3D]
    original_wf = art2[FLAG_WF]
    original_cu = art2[FLAG_CU]
    art2[FLAG_W3D] = scale_hsgm(original_hsgm, FLAG_SCALE)

    print("building DATA...")
    data_big = sk.build_big(files)
    print("building ART_TWO...")
    art2_big = sk.build_big(art2)
    packed, packed_order = sk.parse_big_ordered(data_big)
    art2p, _ = sk.parse_big_ordered(art2_big)
    fails: list[str] = []
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))
    fails.extend(f"ART2 {x}" for x in sk.big_structure_ok(art2_big))
    if len(art2_big) >= SAGE_SAFE:
        fails.append("ART_TWO exceeds SAGE 2GiB")

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
            if field(blk, "DescriptLabel") != "CONTROLBAR:ToolTipIraq_MIC":
                fails.append(f"{label} {country['cmd']} DescriptLabel")
        _, packed_btn = last_from(packed_order, packed, "CommandButton", country["cmd"])
        if field(packed_btn, "Object") != country["object"]:
            fails.append(f"last-wins button {country['cmd']}")
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
                fails.append(f"{cs_name} unexpected extra slot changes {new_sl} vs {expect}")
        # original replaced object still exists and is unchanged
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

    src_mic, mic = last_from(packed_order, packed, "Object", "Iraq_MIC")
    orig_mic = last_from(order, original, "Object", "Iraq_MIC")[1]
    if mic != orig_mic:
        fails.append("Iraq_MIC mutated")
    if field(mic, "BuildCost") != COST or field(mic, "DisplayName") != DISPLAY_KEY:
        fails.append("Iraq Global Store identity lost")
    src_btn, iraq_btn = last_from(packed_order, packed, "CommandButton", "Command_ConstructIraq_MIC")
    orig_btn = last_from(order, original, "CommandButton", "Command_ConstructIraq_MIC")[1]
    if iraq_btn != orig_btn:
        fails.append("Command_ConstructIraq_MIC mutated")

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
        for item in uav.COPIES:
            if packed_slots.get(item["slot"]) != item["cmd"]:
                fails.append(f"{country['display']} lost UAV slot {item['slot']}")

    csf = packed[CSF_KEY]
    orig_csf = original[CSF_KEY]
    if csf != orig_csf:
        fails.append("CSF mutated")
    if sk.csf_get(csf, DISPLAY_KEY) != NAME:
        fails.append("CSF Global Store name lost")
    if sk.csf_get(csf, "CONTROLBAR:ConstructIraq_MIC") != NAME:
        fails.append("construct label lost")
    if sk.csf_get(csf, "CONTROLBAR:ToolTipIraq_MIC") != TIP:
        fails.append("tooltip lost")
    if sk.csf_get(csf, "OBJECT:MIC") != sk.csf_get(orig_csf, "OBJECT:MIC"):
        fails.append("shared OBJECT:MIC mutated")

    for name in ("Egypt_MIC", "IranDozerCommandSet"):
        pass
    for name in ("Egypt_MIC",):
        if last_from(order, original, "Object", name)[1] != last_from(packed_order, packed, "Object", name)[1]:
            fails.append("Egypt_MIC mutated")

    # prereq last-wins
    prereq_counts = []
    for country in COUNTRIES:
        n = 0
        for old in country["prereq_old"]:
            for obj_name, (_src, blk) in collect_last_objects(packed_order, packed).items():
                if obj_name in {country["object"], old}:
                    continue
                if field(blk, "Side") != country["side"]:
                    continue
                if re.search(rf"(?m)^\s*Object\s*=\s*{re.escape(country['object'])}\b", blk):
                    n += 1
                if re.search(rf"(?m)^\s*Object\s*=\s*{re.escape(old)}\b", blk):
                    fails.append(f"{obj_name} still requires {old}")
        prereq_counts.append(f"{country['display']}|retargeted_or_none|{n}")

    # flag isolation
    if art2p[FLAG_WF] != original_wf:
        fails.append("HsWF mutated")
    if art2p[FLAG_CU] != original_cu:
        fails.append("HsCU mutated")
    if art2p[FLAG_W3D] == original_hsgm:
        fails.append("HsGM not scaled")
    if sk.mesh_tex(art2p[FLAG_W3D]) != sk.mesh_tex(original_hsgm):
        fails.append("HsGM textures changed")
    if "SpecterFuturisticFlag.tga" not in sk.all_tex(art2p[FLAG_W3D]):
        fails.append("HsGM lost futuristic flag texture")
    if "IraqiFlag.dds" in sk.all_tex(art2p[FLAG_W3D]):
        fails.append("HsGM gained IraqiFlag.dds")
    before = mesh_vert_aabb(original_hsgm)
    after = mesh_vert_aabb(art2p[FLAG_W3D])
    for name in SCALE_MESHES:
        b, a = before[name], after[name]
        bw = b[1] - b[0]
        aw = a[1] - a[0]
        ratio = aw / bw if bw else 0
        if abs(ratio - FLAG_SCALE) > 0.02:
            fails.append(f"{name} width ratio {ratio}")
        if abs(a[2] - b[2]) > 0.02:
            fails.append(f"{name} ymin moved {a[2]} vs {b[2]}")
        if a[6] != b[6]:
            fails.append(f"{name} vert count changed")
    if before["LINE01"] != after["LINE01"]:
        fails.append("LINE01 pole scaled")

    wf_obj = last_from(packed_order, packed, "Object", "Iraq_WarFactory")[1]
    orig_wf = last_from(order, original, "Object", "Iraq_WarFactory")[1]
    if wf_obj != orig_wf or "IQ__IQFlag_HsWF" not in wf_obj:
        fails.append("Iraq_WarFactory flag mutated")
    cc_obj = last_from(packed_order, packed, "Object", "Iraq_CommandCenter")[1]
    orig_cc = last_from(order, original, "Object", "Iraq_CommandCenter")[1]
    if cc_obj != orig_cc:
        fails.append("Iraq_CommandCenter mutated")

    if CS_ZZZZ.lower() <= r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini".lower():
        fails.append("CS overlay does not sort after SpySatellite")
    if PREREQ_KEY.lower() <= r"Data\INI\Object_ZZZZ_SpySatelliteFeeStrip.ini".lower():
        fails.append("prereq overlay does not sort after SpySatellite objects")

    allowed_prefix = {OBJ_KEY, CB_ZZZZ, CS_ZZZZ, PREREQ_KEY, CB_INI}
    for key, blob in original.items():
        if key in allowed_prefix:
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
    art2_path.write_bytes(art2_big)

    LOOSE.joinpath("Object/Specter/GlobalStore").mkdir(parents=True, exist_ok=True)
    (LOOSE / "Object/Specter/GlobalStore/CountryGlobalStores.ini").write_bytes(files[OBJ_KEY])
    (LOOSE / "CommandButton_ZZZZ_ZGlobalStoreExpand.ini").write_bytes(files[CB_ZZZZ])
    (LOOSE / "CommandSet_ZZZZ_ZGlobalStoreExpand.ini").write_bytes(files[CS_ZZZZ])

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "CountryGlobalStores.ini").write_bytes(files[OBJ_KEY])
    (ext / "COUNTRY_TABLE.txt").write_text("\n".join(table) + "\n", encoding="utf-8")
    (ext / "PREREQ_RETARGET.txt").write_text("\n".join(prereq_table) + "\n", encoding="utf-8")
    (ext / "FLAG.txt").write_text(
        "\n".join(
            [
                f"MODEL=IQ__IQFlag_HsGM",
                f"SCALE={FLAG_SCALE}",
                "MESHES=FLAG01,FLAG02,FLAG03,HOUSECOLOR01,HOUSECOLOR02,HOUSECOLOR03",
                "POLE=LINE01 unchanged",
                "TEXTURE=SpecterFuturisticFlag.tga unchanged",
                "ISOLATED_FROM=IQ__IQFlag_HsWF,IQ__IQFlag_HsCU",
                "PIVOT=pole axis X/Z=0, cloth ymin kept",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (OUT / "INSTALL.txt").write_text(
        "\n".join(
            [
                "SPECTER GLOBAL STORE EXPAND — INSTALL",
                "",
                "Keep the split ART arrangement. Do not recombine ART.",
                "Place all three uncompressed BIGs next to generals.exe:",
                "  _SPEC_DATA_ONE.big",
                "  _SPEC_ART_ONE.big",
                "  _SPEC_ART_TWO.big",
                "",
                "Zero Hour auto-loads every *.big in that folder.",
                "Each .big must start with BIGF. Do not install gzip as .big.",
                "Replace SPECTER_IRAQ_GLOBAL_STORE_NAME. ART_TWO includes the",
                "enlarged Global Store flag. ART_ONE is unchanged from PR #667/#668.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "19-country Global Store expansion from Iraq_MIC. Group A replaces "
        "Strategy Center (MENA7: empty MIC analogue). Group B replaces C-RAM. "
        "Isolated HsGM flag scaled 1.25. RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    zip_path = OUT / "SPECTER_GLOBAL_STORE_EXPAND.zip"
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
    if art1_path.stat().st_size >= SAGE_SAFE or art2_path.stat().st_size >= SAGE_SAFE:
        raise SystemExit("ART archive exceeds SAGE 2GiB signed offset limit")

    data_sha = sha256_path(data_path)
    art1_sha = sha256_path(art1_path)
    art2_sha = sha256_path(art2_path)
    zip_sha = sha256_path(zip_path)
    tag = "s-global-store-expand"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/" + tag
    )
    report = "\n".join(
        [
            "STATIC VALIDATION: PASS",
            "RUNTIME_TEST=NOT RUN",
            "BASELINE: PR #668 SPECTER_IRAQ_GLOBAL_STORE_NAME",
            "COUNTRIES=19 (Group A 15, Group B 4)",
            "IRAQ_GLOBAL_STORE_UNCHANGED=YES",
            "FLAG_HSGM_SCALE=1.25 FLAG+HOUSECOLOR only",
            "FLAG_HSWF_HSCU_UNCHANGED=YES",
            "ART_ONE_UNCHANGED=YES",
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
        ]
    )
    (OUT / "VALIDATE_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "\n".join(
            [
                "DATA_CHANGED=YES",
                "ART_ONE_CHANGED=NO",
                "ART_TWO_CHANGED=YES",
                f"DATA_SIZE={data_path.stat().st_size}",
                f"DATA_SHA256={data_sha}",
                f"ART_ONE_SIZE={art1_path.stat().st_size}",
                f"ART_ONE_SHA256={art1_sha}",
                f"ART_TWO_SIZE={art2_path.stat().st_size}",
                f"ART_TWO_SHA256={art2_sha}",
                "ZIP_FILE=SPECTER_GLOBAL_STORE_EXPAND.zip",
                f"ZIP_SIZE={zip_path.stat().st_size}",
                f"ZIP_SHA256={zip_sha}",
                "BASELINE=PR #668",
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
                "ART textures (unchanged from PR #667 / #668):",
                f"  {rel_base}/_SPEC_ART_ONE.big",
                f"  SIZE={art1_path.stat().st_size}",
                f"  SHA256={art1_sha}",
                "",
                "ART models (HsGM flag scaled 1.25):",
                f"  {rel_base}/_SPEC_ART_TWO.big",
                f"  SIZE={art2_path.stat().st_size}",
                f"  SHA256={art2_sha}",
                "",
                "ZIP:",
                f"  {rel_base}/SPECTER_GLOBAL_STORE_EXPAND.zip",
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
                "# Global Store expansion to 19 countries",
                "",
                "The existing Iraq Global Store (`Iraq_MIC`) is copied to 19 countries.",
                "Group A replaces Strategy Center construction (MENA7 has no Strategy",
                "Center; the empty country MIC / Global Market slot is the analogue).",
                "Group B replaces C-RAM construction.",
                "",
                "Name remains **Global Store**, cost **$7,000**, description title",
                "**Global Aerospace Market**. Production slots 1–14 plus Sell at 15",
                "are unchanged. The isolated `IQ__IQFlag_HsGM` flag cloth is scaled",
                "1.25; War Factory / Command Center flags are untouched.",
                "",
                "Units that required the replaced Strategy Center or MENA MIC are",
                "retargeted to that country's Global Store so tech trees still unlock.",
                "Strategy Center upgrades and C-RAM weapons are not merged into Global Store.",
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
