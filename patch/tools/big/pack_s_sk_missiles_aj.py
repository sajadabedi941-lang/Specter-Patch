#!/usr/bin/env python3
"""Implement South Korea missile roster A-J on the PR #630 / #629 path.

Baseline: packed SPECTER_JAPAN_MISSILES_AJ (PR #630 A-J + PR #629 cooldown/damage).

South Korea currently constructs Iraq_AlFahdMissileFactoryBuilding (Sell-only).
A SouthKorea-only factory is required. Japan A-J, Vietnam A-H, Iraq A-M, and
9P117 stay frozen.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Taegeukgi + exact names on dorsal UV bands. Ten-color tube palette.
No Hinomaru. No RadarPriority. No rearm. No ZZZZ.
"""
from __future__ import annotations

import hashlib
import io
import math
import re
import shutil
import struct
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_JAPAN_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_JAPAN_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_SK_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_630 = "45c7f33b50c4927b6e16849dbb15c5ca88a82ff753a8e0ba675e060ba422e924"
SIZE_DATA_630 = 366990039
SHA_ART_630 = "84eb2b41187cc9cb51fa22ec454c380740b15cda2768f0f834f0e0be625b1bc3"
SIZE_ART_630 = 1391390907

TEX_CHUNK = 0x00000032
MESH_HEADER = 0x0000001F
HLOD_HEADER = 0x00000701

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CSF_KEY = r"Data\English\generals.csf"
WEAPON_KEY = r"Data\INI\Weapon.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
BUILDING_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactoryBuilding.ini"
UNIT_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
PROJ_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini"
WEP_A_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlFahd500.ini"
VN_FAC_KEY = (
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces"
    r"\Buildings\Vietnam_MissileFactory.ini"
)
JPN_VT72B_KEY = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Tracked\Japan_VT72B.ini"
JPN_WF_KEY = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_WarFactory.ini"
JPN_FAC_KEY = (
    r"Data\INI\Object\Specter\Japan Self-Defense Forces"
    r"\Buildings\Japan_MissileFactory.ini"
)
SK_VT72B_KEY = r"Data\INI\Object\Specter\South Korean Armed Forces\Tracked\SouthKorea_VT72B.ini"
SK_WF_KEY = r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_WarFactory.ini"
SK_SYS_KEY = r"Data\INI\Object\Specter\South Korean Armed Forces\SouthKorea_Systems.ini"
NG_KEY = r"Data\INI\Object\Specter\NationalGround\NationalGroundForces.ini"
PT_KEY = r"Data\INI\PlayerTemplate.ini"
JPN_WEP_KEY = r"Data\INI\Weapon\Weapon_Japan_Missiles.ini"
JPN_TYPE12_KEY = (
    r"Data\INI\Object\Specter\Japan Self-Defense Forces"
    r"\Wheeled\Japan_Type12Kai.ini"
)

TEL_W3D = r"Art\W3D\Irq_AlFahd500.W3D"
TELD_W3D = r"Art\W3D\Irq_AlFahd500D.W3D"
PROJ_W3D = r"Art\W3D\Irq_AlFahd500M.W3D"
ORIG_W3D = r"Art\W3D\Irq_9P117.W3D"
ORIGD_W3D = r"Art\W3D\Irq_9P117D.W3D"
R11_W3D = r"Art\W3D\Irq_R11_M.W3D"
TRUCK_DDS = r"Art\Textures\Irq_9P117.dds"
TRUCKD_DDS = r"Art\Textures\Irq_9P117D.dds"

NEW_CB_KEY = r"Data\INI\CommandButton_SouthKoreaMissiles.ini"
NEW_CS_KEY = r"Data\INI\CommandSet_SouthKoreaMissiles.ini"
NEW_WEP_KEY = r"Data\INI\Weapon\Weapon_SouthKorea_Missiles.ini"
NEW_FAC_KEY = (
    r"Data\INI\Object\Specter\South Korean Armed Forces"
    r"\Buildings\SouthKorea_MissileFactory.ini"
)
TRUCK_TEX = "Skr_TEL.tga"
TRUCKD_TEX = "Skr_TELD.tga"
TRUCK_KEY = rf"Art\Textures\{TRUCK_TEX}"
TRUCKD_KEY = rf"Art\Textures\{TRUCKD_TEX}"

WEP_MARKER = (
    "; ===== South Korea missiles A-J "
    "(Weapon.ini load path for Command_FireMainWeapon) ====="
)

MOTHER_RANGE = 1720.0
MOTHER_KG = 400
MOTHER_DMG = 2000.0
MOTHER_DEATH = 2200
MOTHER_ACC = 10
MOTHER_SCATTER = 175
MOTHER_STEALTH = 5
MOTHER_HP = 400.0
MOTHER_MIN_RANGE = 800.0
KM_FLOOR = 1000
KM_CEILING = 5000
KG_FLOOR = 400
KG_CEILING = 10000

SHEET = 1024
TEL_BAND = (0.16, 0.30)
PROJ_BAND = (0.66, 0.80)
TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Global 10-color launcher palette (tube identity). Shared truck is cool slate.
GRAY = (128, 128, 128)
BLACK = (22, 24, 26)
BLUE = (28, 68, 168)
PETROL = (10, 72, 84)
WHITE = (228, 224, 216)
RED = (168, 32, 28)
ORANGE = (210, 108, 22)
YELLOW = (214, 178, 28)
MUDDY = (88, 96, 42)
CREAM = (220, 200, 155)
SLATE = (58, 64, 68)
GRAPHITE = (41, 45, 44)
METAL = (133, 137, 130)
NOSE_W = (236, 228, 210)
NOSE_R = (168, 32, 28)

MISSILES = [
    {
        "slot": "A",
        "object": "SouthKorea_Baekho",
        "name": "Baekho",
        "model": "Skr_Baekho",
        "modeld": "Skr_BaekhoD",
        "proj_model": "Skr_BaekhoM",
        "hier": b"SKR_BAEKH",
        "hierd": b"SKR_BAEKHD",
        "proj_hier": b"SKR_MSL_A",
        "tex": "Skr_BaekhoP.tga",
        "body": GRAY,
        "nose": NOSE_R,
        "expect": "gray",
        "km": 1000,
        "kg": 400,
        "acc": 70,
        "stealth": 30,
        "rebuild": 18,
        "price": 900,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "B",
        "object": "SouthKorea_Cheonma",
        "name": "Cheonma",
        "model": "Skr_Chonma",
        "modeld": "Skr_ChonmaD",
        "proj_model": "Skr_ChonmaM",
        "hier": b"SKR_CHNMA",
        "hierd": b"SKR_CHNMAD",
        "proj_hier": b"SKR_MSL_B",
        "tex": "Skr_ChonmaP.tga",
        "body": BLACK,
        "nose": NOSE_W,
        "expect": "black",
        "km": 1100,
        "kg": 800,
        "acc": 50,
        "stealth": 35,
        "rebuild": 24,
        "price": 1400,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "C",
        "object": "SouthKorea_Haeryong",
        "name": "Haeryong",
        "model": "Skr_Haery",
        "modeld": "Skr_HaeryD",
        "proj_model": "Skr_HaeryM",
        "hier": b"SKR_HAERY",
        "hierd": b"SKR_HAERYD",
        "proj_hier": b"SKR_MSL_C",
        "tex": "Skr_HaeryP.tga",
        "body": BLUE,
        "nose": NOSE_W,
        "expect": "blue",
        "km": 1300,
        "kg": 600,
        "acc": 85,
        "stealth": 25,
        "rebuild": 26,
        "price": 1700,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "D",
        "object": "SouthKorea_Hwarang",
        "name": "Hwarang",
        "model": "Skr_Hwara",
        "modeld": "Skr_HwaraD",
        "proj_model": "Skr_HwaraM",
        "hier": b"SKR_HWARA",
        "hierd": b"SKR_HWARAD",
        "proj_hier": b"SKR_MSL_D",
        "tex": "Skr_HwaraP.tga",
        "body": PETROL,
        "nose": NOSE_W,
        "expect": "petrol",
        "km": 1500,
        "kg": 1000,
        "acc": 45,
        "stealth": 65,
        "rebuild": 32,
        "price": 2400,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "E",
        "object": "SouthKorea_Mugunghwa",
        "name": "Mugunghwa",
        "model": "Skr_Mugun",
        "modeld": "Skr_MugunD",
        "proj_model": "Skr_MugunM",
        "hier": b"SKR_MUGUN",
        "hierd": b"SKR_MUGUND",
        "proj_hier": b"SKR_MSL_E",
        "tex": "Skr_MugunP.tga",
        "body": WHITE,
        "nose": NOSE_R,
        "expect": "white",
        "km": 1800,
        "kg": 1200,
        "acc": 80,
        "stealth": 40,
        "rebuild": 40,
        "price": 3200,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "F",
        "object": "SouthKorea_Taebaek",
        "name": "Taebaek",
        "model": "Skr_Taeba",
        "modeld": "Skr_TaebaD",
        "proj_model": "Skr_TaebaM",
        "hier": b"SKR_TAEBA",
        "hierd": b"SKR_TAEBAD",
        "proj_hier": b"SKR_MSL_F",
        "tex": "Skr_TaebaP.tga",
        "body": RED,
        "nose": NOSE_W,
        "expect": "red",
        "km": 2200,
        "kg": 2000,
        "acc": 35,
        "stealth": 45,
        "rebuild": 48,
        "price": 4500,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "G",
        "object": "SouthKorea_Jindallae",
        "name": "Jindallae",
        "model": "Skr_Jinda",
        "modeld": "Skr_JindaD",
        "proj_model": "Skr_JindaM",
        "hier": b"SKR_JINDA",
        "hierd": b"SKR_JINDAD",
        "proj_hier": b"SKR_MSL_G",
        "tex": "Skr_JindaP.tga",
        "body": ORANGE,
        "nose": NOSE_W,
        "expect": "orange",
        "km": 2600,
        "kg": 1500,
        "acc": 40,
        "stealth": 75,
        "rebuild": 55,
        "price": 5200,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "H",
        "object": "SouthKorea_Geommu",
        "name": "Geommu",
        "model": "Skr_Geomu",
        "modeld": "Skr_GeomuD",
        "proj_model": "Skr_GeomuM",
        "hier": b"SKR_GEOMM",
        "hierd": b"SKR_GEOMMD",
        "proj_hier": b"SKR_MSL_H",
        "tex": "Skr_GeomuP.tga",
        "body": YELLOW,
        "nose": NOSE_R,
        "expect": "yellow",
        "km": 3000,
        "kg": 3000,
        "acc": 25,
        "stealth": 35,
        "rebuild": 68,
        "price": 7000,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "I",
        "object": "SouthKorea_Haetsal",
        "name": "Haetsal",
        "model": "Skr_Haets",
        "modeld": "Skr_HaetsD",
        "proj_model": "Skr_HaetsM",
        "hier": b"SKR_HAETS",
        "hierd": b"SKR_HAETSD",
        "proj_hier": b"SKR_MSL_I",
        "tex": "Skr_HaetsP.tga",
        "body": MUDDY,
        "nose": NOSE_W,
        "expect": "muddy",
        "km": 3500,
        "kg": 2500,
        "acc": 75,
        "stealth": 50,
        "rebuild": 75,
        "price": 8000,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "J",
        "object": "SouthKorea_Cheonwang",
        "name": "Cheonwang",
        "model": "Skr_Cheon",
        "modeld": "Skr_CheonD",
        "proj_model": "Skr_CheonM",
        "hier": b"SKR_CHEON",
        "hierd": b"SKR_CHEOND",
        "proj_hier": b"SKR_MSL_J",
        "tex": "Skr_CheonP.tga",
        "body": CREAM,
        "nose": NOSE_R,
        "expect": "cream",
        "km": 4200,
        "kg": 4500,
        "acc": 20,
        "stealth": 25,
        "rebuild": 100,
        "price": 11000,
        "min_range": MOTHER_MIN_RANGE,
    },
]

FROZEN_ART = [
    ORIG_W3D,
    ORIGD_W3D,
    R11_W3D,
    TEL_W3D,
    TELD_W3D,
    PROJ_W3D,
    r"Art\W3D\Irq_9P117R.W3D",
    TRUCK_DDS,
    TRUCKD_DDS,
    r"Art\Textures\GENERIC-MISSILES.dds",
    r"Art\Textures\IraqiFlag.dds",
    r"Art\Textures\Irq_AlFahd500P.tga",
    r"Art\Textures\specter_missile_a.tga",
    r"Art\Textures\specter_missile_g.tga",
    r"Art\Textures\specter_missile_h.tga",
    r"Art\Textures\specter_missile_j.tga",
    r"Art\Textures\Jpn_TEL.tga",
    r"Art\Textures\Jpn_Type12P.tga",
    r"Art\W3D\Jpn_Type12.W3D",
    r"Art\Textures\Button_MissileFactory.tga",
    r"Art\Textures\Button_kashtan.tga",
    r"Art\Textures\Button_falaq.tga",
    r"Art\W3D\Vnm_VCM01.W3D",
    r"Art\Textures\Vnm_VCM01P.tga",
]

FROZEN_DATA = [
    R11_KEY,
    FACTORY_KEY,
    BUILDING_KEY,
    UNIT_A_KEY,
    PROJ_A_KEY,
    WEP_A_KEY,
    VN_FAC_KEY,
    JPN_VT72B_KEY,
    JPN_WF_KEY,
    JPN_FAC_KEY,
    JPN_WEP_KEY,
    JPN_TYPE12_KEY,
    SK_VT72B_KEY,
    SK_WF_KEY,
    SK_SYS_KEY,
    NG_KEY,
    PT_KEY,
]

for _m in MISSILES:
    assert len(_m["hier"]) == 9, _m["hier"]
    assert len(_m["hierd"]) == 10, _m["hierd"]
    assert len(_m["proj_hier"]) == 9, _m["proj_hier"]
    assert len(_m["model"]) <= 15 and len(_m["modeld"]) <= 15 and len(_m["proj_model"]) <= 15
    assert KM_FLOOR <= _m["km"] <= KM_CEILING, _m
    assert KG_FLOOR <= _m["kg"] <= KG_CEILING, _m


def fmt_stat(v: float) -> str:
    """Legal SAGE float. Never emit 62.5.0 (fmt_num(x)+'.0' bug from PR #628)."""
    if abs(v - round(v)) < 1e-9:
        return f"{int(round(v))}.0"
    return f"{v:.3f}".rstrip("0").rstrip(".")


def derived(m: dict) -> dict:
    d = dict(m)
    d["range"] = MOTHER_RANGE * (m["km"] / 1000.0)
    d["damage"] = MOTHER_DMG * (m["kg"] / MOTHER_KG)
    d["death"] = int(round(MOTHER_DEATH * (m["kg"] / MOTHER_KG)))
    d["scatter"] = MOTHER_SCATTER * (MOTHER_ACC / m["acc"])
    d["inf_scatter"] = d["scatter"] * (280.0 / 175.0)
    d["hp"] = MOTHER_HP * (m["stealth"] / MOTHER_STEALTH)
    d["secondary"] = 100.0 * (m["kg"] / MOTHER_KG)
    d["weapon"] = f"Weapon_{m['object']}"
    d["warhead"] = f"Weapon_{m['object']}_Warhead"
    d["projectile"] = f"Projectile_{m['object']}"
    d["button"] = f"CB_SOUTHKOREA_MISSILE_{m['slot']}"
    d["cameo"] = f"specter_missile_{m['slot'].lower()}"
    d["unit_key"] = (
        r"Data\INI\Object\Specter\South Korean Armed Forces"
        rf"\Wheeled\{m['object']}.ini"
    )
    d["proj_key"] = (
        r"Data\INI\Object\Specter\South Korean Armed Forces"
        rf"\{m['object']}_Projectile.ini"
    )
    d["tex_key"] = rf"Art\Textures\{m['tex']}"
    d["tel_key"] = rf"Art\W3D\{m['model']}.W3D"
    d["teld_key"] = rf"Art\W3D\{m['modeld']}.W3D"
    d["projw_key"] = rf"Art\W3D\{m['proj_model']}.W3D"
    # Honest tooltip: design values + engine mapping, no fake hit/intercept %.
    d["tooltip"] = (
        f"{m['name']}\n"
        f"Range: {m['km']} km\n"
        f"Warhead: {m['kg']} kg\n"
        f"Build Time: {m['rebuild']} sec\n"
        f"Price: ${m['price']}"
    )
    if d["range"] < MOTHER_MIN_RANGE and m["min_range"] >= d["range"]:
        raise SystemExit(f"{m['slot']} min_range {m['min_range']} >= range {d['range']}")
    if m["km"] < KM_FLOOR or m["km"] > KM_CEILING:
        raise SystemExit(f"{m['slot']} km {m['km']} outside {KM_FLOOR}-{KM_CEILING}")
    if m["kg"] < KG_FLOOR or m["kg"] > KG_CEILING:
        raise SystemExit(f"{m['slot']} kg {m['kg']} outside {KG_FLOOR}-{KG_CEILING}")
    return d


DERIVED = [derived(m) for m in MISSILES]


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
    files: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


def parse_big_ordered(data: bytes):
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files = {}
    order = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        key = name.replace("/", "\\")
        files[key] = data[off : off + size]
        order.append(key)
    return files, order


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


def big_structure_ok(data: bytes) -> list[str]:
    fails = []
    archive_size, count, header_size, hdr_end, files = parse_index(data)
    if archive_size != len(data):
        fails.append(f"archive size {archive_size} != {len(data)}")
    if count != len(files):
        fails.append("count mismatch")
    if header_size != hdr_end:
        fails.append("header size mismatch")
    seen = set()
    for name, off, size in files:
        key = name.replace("/", "\\").lower()
        if key in seen:
            fails.append(f"dup {name}")
        seen.add(key)
        if off < header_size or off + size > len(data):
            fails.append(f"range {name}")
    return fails


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def last_spans(text: str, kind: str, name: str):
    return list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text))


def last_block(text: str, kind: str, name: str) -> str:
    matches = last_spans(text, kind, name)
    return matches[-1].group(0) if matches else ""


def replace_last(text: str, kind: str, name: str, new_block: str) -> str:
    ms = last_spans(text, kind, name)
    if not ms:
        raise SystemExit(f"missing {kind} {name}")
    m = ms[-1]
    return text[: m.start()] + new_block + text[m.end() :]


def field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block or "", re.M)
    return m.group(1).strip() if m else ""


def last_block_from_files(order: list[str], files: dict[str, bytes], kind: str, name: str):
    found = ("", "")
    needle = f"{kind} {name}".encode("ascii")
    for key in order:
        blob = files[key]
        if needle not in blob:
            continue
        try:
            text = blob.decode("latin1")
        except Exception:
            continue
        block = last_block(text, kind, name)
        if block:
            found = (key, block)
    return found


def zstr(buf: bytes) -> str:
    return buf.split(b"\x00", 1)[0].decode("latin1", errors="replace")


def replace_textures(blob: bytes, mapping: dict[str, str]) -> bytes:
    lowmap = {k.lower(): v for k, v in mapping.items()}

    def rebuild(data: bytes) -> bytes:
        out = bytearray()
        pos = 0
        end = len(data)
        while pos + 8 <= end:
            cid, raw = struct.unpack_from("<II", data, pos)
            sz = raw & 0x7FFFFFFF
            cont = bool(raw & 0x80000000)
            cs, ce = pos + 8, pos + 8 + sz
            if ce > end:
                break
            payload = data[cs:ce]
            if cont:
                payload = rebuild(payload)
            elif cid == TEX_CHUNK:
                old = zstr(payload)
                if old.lower() in lowmap:
                    payload = lowmap[old.lower()].encode("ascii") + b"\x00"
            new_raw = len(payload) | (0x80000000 if cont else 0)
            out += struct.pack("<II", cid, new_raw)
            out += payload
            pos = ce
        if pos < end:
            out += data[pos:]
        return bytes(out)

    return rebuild(blob)


def uniquify(blob: bytes, replacements: list[tuple[bytes, bytes]]) -> bytes:
    out = blob
    for old, new in replacements:
        if len(old) != len(new):
            raise ValueError(f"identity length {old!r} -> {new!r}")
        out = out.replace(old, new)
    return out


def patch_hlod_container(blob: bytes, new_name: str) -> bytes:
    if len(new_name) > 15:
        raise ValueError(f"HLod name too long: {new_name}")
    padded = new_name.encode("ascii") + b"\x00" * (16 - len(new_name))
    out = bytearray(blob)

    def rec(start: int, stop: int) -> None:
        p = start
        while p + 8 <= stop:
            cid, raw = struct.unpack_from("<II", out, p)
            sz = raw & 0x7FFFFFFF
            cont = bool(raw & 0x80000000)
            cs, ce = p + 8, p + 8 + sz
            if ce > stop:
                break
            if cid == HLOD_HEADER and ce - cs >= 40:
                out[cs + 8 : cs + 24] = padded
            elif cont:
                rec(cs, ce)
            p = ce

    rec(0, len(out))
    return bytes(out)


def mesh_tex(blob: bytes) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    mesh = ""

    def rec(data: bytes, start: int, stop: int) -> None:
        nonlocal mesh
        p = start
        while p + 8 <= stop:
            cid, raw = struct.unpack_from("<II", data, p)
            sz = raw & 0x7FFFFFFF
            cont = bool(raw & 0x80000000)
            cs, ce = p + 8, p + 8 + sz
            if ce > stop:
                break
            if cid == MESH_HEADER and ce - cs >= 24:
                mesh = zstr(data[cs + 8 : cs + 24])
            if cont:
                rec(data, cs, ce)
            elif cid == TEX_CHUNK:
                found.setdefault(mesh, set()).add(zstr(data[cs:ce]))
            p = ce

    rec(blob, 0, len(blob))
    return found


def all_tex(blob: bytes) -> set[str]:
    out: set[str] = set()
    for names in mesh_tex(blob).values():
        out |= names
    return out


def make_tel_w3d(src: bytes, damaged: bool, m: dict) -> bytes:
    mapping = {"Irq_AlFahd500P.tga": m["tex"]}
    if damaged:
        mapping["Irq_9P117D.tga"] = TRUCKD_TEX
        blob = replace_textures(src, mapping)
        blob = uniquify(blob, [(b"IRQ_AF500D", m["hierd"])])
        blob = patch_hlod_container(blob, m["modeld"])
    else:
        mapping["Irq_9P117.tga"] = TRUCK_TEX
        blob = replace_textures(src, mapping)
        blob = uniquify(blob, [(b"IRQ_AF500", m["hier"])])
        blob = patch_hlod_container(blob, m["model"])
    return blob


def make_proj_w3d(src: bytes, m: dict) -> bytes:
    blob = replace_textures(src, {"Irq_AlFahd500P.tga": m["tex"]})
    blob = uniquify(blob, [(b"IRQ_ALF_M", m["proj_hier"])])
    blob = patch_hlod_container(blob, m["proj_model"])
    return blob


def csf_parse(csf: bytes):
    if csf[:4] != b" FSC":
        raise SystemExit(f"unexpected CSF magic {csf[:4]!r}")
    magic, ver, nlab, nstr, unused, lang = struct.unpack_from("<4sIIIII", csf, 0)
    labels = []
    pos = 24
    while pos < len(csf):
        if csf[pos : pos + 4] != b" LBL":
            break
        pos += 4
        cnt, nlen = struct.unpack_from("<II", csf, pos)
        pos += 8
        name = csf[pos : pos + nlen].decode("latin1")
        pos += nlen
        strs = []
        for _ in range(cnt):
            smag = csf[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4
            raw = csf[pos : pos + slen * 2]
            pos += slen * 2
            val = bytes(x ^ 0xFF for x in raw).decode("utf-16le")
            extra = None
            if smag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4
                extra = csf[pos : pos + elen]
                pos += elen
            strs.append((smag, val, extra))
        labels.append((name, strs))
    return magic, ver, unused, lang, labels


def csf_build(magic, ver, unused, lang, labels) -> bytes:
    body = bytearray()
    nstr = 0
    for name, strs in labels:
        body += b" LBL"
        body += struct.pack("<II", len(strs), len(name))
        body += name.encode("latin1")
        for smag, val, extra in strs:
            encoded = val.encode("utf-16le")
            xored = bytes(x ^ 0xFF for x in encoded)
            tag = smag if smag in (b" RTS", b"WRTS") else b" RTS"
            body += tag
            body += struct.pack("<I", len(val))
            body += xored
            nstr += 1
            if tag == b"WRTS" and extra is not None:
                body += struct.pack("<I", len(extra))
                body += extra
    header = bytearray()
    header += magic
    header += struct.pack("<IIIII", ver, len(labels), nstr, unused, lang)
    return bytes(header + body)


def csf_upsert(csf: bytes, mapping: dict[str, str]) -> bytes:
    magic, ver, unused, lang, labels = csf_parse(csf)
    by_name = {n: i for i, (n, _) in enumerate(labels)}
    for key, value in mapping.items():
        if key in by_name:
            i = by_name[key]
            name, strs = labels[i]
            if strs:
                smag, _old, extra = strs[0]
                strs[0] = (smag, value, extra)
            else:
                strs.append((b" RTS", value, None))
            labels[i] = (name, strs)
        else:
            labels.append((key, [(b" RTS", value, None)]))
    return csf_build(magic, ver, unused, lang, labels)


def csf_get(csf: bytes, key: str) -> str | None:
    _m, _v, _u, _l, labels = csf_parse(csf)
    for name, strs in labels:
        if name == key and strs:
            return strs[0][1]
    return None


def make_tga32(im: Image.Image) -> bytes:
    rgba = im.convert("RGBA")
    w, h = rgba.size
    pixels = rgba.tobytes()
    rows = []
    stride = w * 4
    for y in range(h - 1, -1, -1):
        src = pixels[y * stride : (y + 1) * stride]
        bgra = bytearray()
        for i in range(0, len(src), 4):
            r, g, b, a = src[i : i + 4]
            bgra += bytes((b, g, r, a))
        rows.append(bytes(bgra))
    header = bytearray(18)
    header[2] = 2
    struct.pack_into("<HH", header, 12, w, h)
    header[16] = 32
    header[17] = 0x08
    return bytes(header) + b"".join(rows) + TRUEVISION


def shade(color: tuple[int, int, int], t: float) -> tuple[int, int, int, int]:
    t = max(0.72, min(1.08, t))
    return (
        min(255, int(color[0] * t)),
        min(255, int(color[1] * t)),
        min(255, int(color[2] * t)),
        255,
    )


def _trigram(draw: ImageDraw.ImageDraw, cx: float, cy: float, pattern: str, scale: float) -> None:
    """pattern is 3 chars: '1' solid, '0' broken. Drawn horizontally, stacked top to bottom."""
    bar_w, bar_h, gap = scale * 2.4, scale * 0.28, scale * 0.22
    ink = (17, 17, 17, 255)
    for i, bit in enumerate(pattern):
        y = cy - scale * 0.55 + i * (bar_h + gap)
        if bit == "1":
            draw.rectangle([cx - bar_w / 2, y, cx + bar_w / 2, y + bar_h], fill=ink)
        else:
            mid = scale * 0.18
            draw.rectangle([cx - bar_w / 2, y, cx - mid, y + bar_h], fill=ink)
            draw.rectangle([cx + mid, y, cx + bar_w / 2, y + bar_h], fill=ink)


def make_sk_flag() -> Image.Image:
    """Taegeukgi: white field, red-over-blue taegeuk swirl, four black trigrams.

    Official corners: UL geon ☰, UR gam ☵, LL ri ☲, LR gon ☷.
    The taegeuk is a two-comma swirl (no Chinese-style eyes): red head toward
    the upper hoist, blue head toward the lower fly.
    """
    w, h = 450, 300
    im = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    red, blue = (205, 46, 58, 255), (0, 71, 160, 255)
    side = int(h * 0.50)
    tg = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    d = ImageDraw.Draw(tg)
    cx = cy = side / 2.0
    r = side / 2.0 - 1.0
    box = [cx - r, cy - r, cx + r, cy + r]
    d.pieslice(box, 90, 270, fill=blue)
    d.pieslice(box, 270, 450, fill=red)
    r2 = r / 2.0
    d.ellipse([cx - r2, cy - r, cx + r2, cy], fill=red)
    d.ellipse([cx - r2, cy, cx + r2, cy + r], fill=blue)
    tg = tg.rotate(45, resample=Image.Resampling.BICUBIC, expand=False)
    im.paste(tg, (int((w - side) / 2), int((h - side) / 2)), tg)
    draw = ImageDraw.Draw(im)
    s = h * 0.11
    _trigram(draw, w * 0.18, h * 0.20, "111", s)
    _trigram(draw, w * 0.82, h * 0.20, "010", s)
    _trigram(draw, w * 0.18, h * 0.72, "101", s)
    _trigram(draw, w * 0.82, h * 0.72, "000", s)
    return im


def paste_flag(im: Image.Image, flag: Image.Image, xy: tuple[int, int], size: tuple[int, int]) -> None:
    fw, fh = size
    flag_im = flag.convert("RGBA").resize((fw, fh), Image.Resampling.NEAREST)
    plate = Image.new("RGBA", (fw + 16, fh + 16), (248, 244, 232, 255))
    bordered = Image.new("RGBA", (fw + 16, fh + 16), (16, 14, 12, 255))
    bordered.paste(plate, (0, 0))
    bordered.paste(flag_im, (8, 8), flag_im)
    draw = ImageDraw.Draw(bordered)
    draw.rectangle([0, 0, fw + 15, fh + 15], outline=(16, 14, 12), width=3)
    im.paste(bordered, (xy[0] - 4, xy[1] - 4), bordered)


def draw_name(im: Image.Image, text: str, box: tuple[int, int, int, int], light_body: bool) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(im)
    if light_body:
        plate = (28, 26, 22, 235)
        ink = (236, 228, 210)
    else:
        plate = (244, 236, 210, 235)
        ink = (18, 16, 12)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=plate, outline=(12, 10, 8), width=3)
    size = 48
    font = ImageFont.truetype(FONT, size)
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    while (tw > (x1 - x0 - 16) or th > (y1 - y0 - 8)) and size > 22:
        size -= 2
        font = ImageFont.truetype(FONT, size)
        bbox = font.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = x0 + (x1 - x0 - tw) / 2 - bbox[0]
    ty = y0 + (y1 - y0 - th) / 2 - bbox[1]
    draw.text((tx, ty), text, font=font, fill=ink)


def paint_dorsal(im: Image.Image, flag: Image.Image, stamp: str, v0: float, v1: float, light: bool) -> None:
    w = h = SHEET
    y0, y1 = int(v0 * h), int(v1 * h)
    pad = 6
    band_h = y1 - y0
    flag_h = min(124, band_h - 2 * pad)
    flag_w = 380
    fx = int(0.06 * w)
    fy = y0 + (band_h - flag_h) // 2
    paste_flag(im, flag, (fx, fy), (flag_w, flag_h))
    nx0 = fx + flag_w + 24
    nx1 = int(0.96 * w)
    ny0 = fy + 6
    ny1 = fy + flag_h - 6
    draw_name(im, stamp, (nx0, ny0, nx1, ny1), light)


def make_skin(body: tuple[int, int, int], nose: tuple[int, int, int], stamp: str, flag: Image.Image) -> Image.Image:
    w = h = SHEET
    im = Image.new("RGBA", (w, h), shade(body, 1.0))
    px = im.load()
    nose_hi = int(0.14 * h)
    body_lo = int(0.18 * h)
    body_hi = int(0.82 * h)
    for y in range(h):
        for x in range(w):
            if y < nose_hi:
                circ = 1.0 - 0.10 * abs((x / w) - 0.5)
                px[x, y] = shade(nose, circ)
            elif y < body_lo:
                px[x, y] = shade(body, 0.78)
            elif y < body_hi:
                circ = 1.04 - 0.12 * abs((y - (body_lo + body_hi) / 2) / max(1, (body_hi - body_lo) / 2))
                px[x, y] = shade(body, circ)
            else:
                px[x, y] = shade(body, 0.88)
    light = body[0] + body[1] + body[2] > 360
    paint_dorsal(im, flag, stamp, TEL_BAND[0], TEL_BAND[1], light)
    paint_dorsal(im, flag, stamp, PROJ_BAND[0], PROJ_BAND[1], light)
    im = ImageEnhance.Contrast(im).enhance(1.04)
    im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=40, threshold=3))
    return im.convert("RGBA")


def recolor_truck(src: Image.Image, damaged: bool = False) -> Image.Image:
    """Map Iraqi tan sheet to South Korean cool slate / graphite / metal."""
    im = src.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            avg = (r + g + b) / 3.0
            sat = max(r, g, b) - min(r, g, b)
            if avg < 55 and sat < 35:
                px[x, y] = (max(0, int(r * 0.28)), max(0, int(g * 0.28)), max(0, int(b * 0.28)), a)
                continue
            if sat > 70 and avg > 70:
                base = METAL
                t = 0.92
            elif avg < 100:
                base = GRAPHITE
                t = max(0.70, min(1.15, avg / 90.0))
            else:
                base = SLATE
                t = max(0.55, min(1.25, avg / 130.0))
            nr = min(255, int(base[0] * t))
            ng = min(255, int(base[1] * t))
            nb = min(255, int(base[2] * t))
            if damaged:
                nr, ng, nb = int(nr * 0.72), int(ng * 0.70), int(nb * 0.68)
            px[x, y] = (nr, ng, nb, a)
    return im


def classify(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    mx, mn = max(r, g, b), min(r, g, b)
    avg = (r + g + b) / 3
    if mx - mn < 28 and avg >= 175:
        return "white"
    if r < 55 and g < 55 and b < 55:
        return "black"
    if b > r + 30 and b > g + 20 and b > 90:
        return "blue"
    if r < 55 and g > 50 and b > 50 and abs(g - b) < 28:
        return "petrol"
    if avg >= 155 and r > b + 18 and g > b + 8 and g > 140 and b < 180:
        return "cream"
    if 50 <= g <= 150 and r < g + 12 and b < 80 and g > b + 10 and r < 120:
        return "muddy"
    if g > r + 18 and g > b + 18 and g > 80:
        return "green"
    if r > 140 and g < 90 and b < 90:
        return "red"
    if r > 170 and 70 < g < 160 and b < 70:
        return "orange"
    if r > 160 and g > 130 and b < 80:
        return "yellow"
    if mx - mn < 28 and 85 <= avg <= 165:
        return "gray"
    return "other"


def region_mode(im: Image.Image, box: tuple[int, int, int, int]) -> dict[str, int]:
    crop = im.convert("RGB").crop(box)
    px = crop.load()
    w, h = crop.size
    counts: dict[str, int] = {}
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            k = classify(px[x, y])
            counts[k] = counts.get(k, 0) + 1
    return counts


def has_sk_flag(counts: dict[str, int]) -> bool:
    return (
        counts.get("white", 0) >= 8
        and counts.get("red", 0) >= 4
        and counts.get("blue", 0) >= 4
    )


def has_name_plate(im: Image.Image, box: tuple[int, int, int, int]) -> bool:
    counts = region_mode(im, box)
    return counts.get("white", 0) + counts.get("black", 0) + counts.get("other", 0) >= 20


def unit_ini(m: dict) -> str:
    hier = m["hier"].decode()
    hierd = m["hierd"].decode()
    return f"""; South Korea {m['object']} TEL. Functional clone of Iraq_R11ScudB / 9P117.
; Dedicated W3D {m['model']} / {m['modeld']} / {m['proj_model']}.
; Truck textures remapped to Skr_TEL / Skr_TELD (not Irq_9P117 / Jpn_TEL).
; No rearm. Factory production only.

Object {m['object']}
Scale = 0.9
  SelectPortrait         = {m['cameo']}
  ButtonImage            = {m['cameo']}
  UpgradeCameo1 = Upgrade_ChinaNeutronShells
  Draw = W3DTruckDraw ModuleTag_01
    OkToChangeModelColor = Yes
    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY TERTIARY
    DefaultConditionState
      Model                           = {m['model']}
      WeaponLaunchBone                = PRIMARY MISSILE
      WeaponFireFXBone                = PRIMARY MISSILE
      WeaponLaunchBone                = SECONDARY MISSILE
      WeaponFireFXBone                = SECONDARY MISSILE
      WeaponLaunchBone                = TERTIARY MISSILE
      WeaponFireFXBone                = TERTIARY MISSILE
      Turret                          = Turrettt
      Flags                           = START_FRAME_FIRST
    End
    ConditionState                    = REALLYDAMAGED
      Model                           = {m['modeld']}
      WeaponLaunchBone                = PRIMARY MISSILE
      WeaponFireFXBone                = PRIMARY WEAPONA01
      WeaponLaunchBone                = SECONDARY MISSILE
      WeaponFireFXBone                = SECONDARY WEAPONA01
      WeaponLaunchBone                = TERTIARY MISSILE
      WeaponFireFXBone                = TERTIARY WEAPONA01
      Turret                          = Turrettt
      Flags                           = START_FRAME_FIRST
    End
    ConditionState                    = RUBBLE
      Model                           = {m['modeld']}
      WeaponLaunchBone                = PRIMARY MISSILE
      WeaponFireFXBone                = PRIMARY WEAPONA01
      WeaponLaunchBone                = SECONDARY MISSILE
      WeaponFireFXBone                = SECONDARY WEAPONA01
      WeaponLaunchBone                = TERTIARY MISSILE
      WeaponFireFXBone                = TERTIARY WEAPONA01
      Turret                          = Turrettt
      Flags                           = START_FRAME_FIRST
    End
    ConditionState    = MOVING
      Animation       = {hier}.{hier}
      AnimationMode   = ONCE_BACKWARDS
      Flags           = START_FRAME_FIRST
    End
    AliasConditionState = MOVING BETWEEN_FIRING_SHOTS_A
    AliasConditionState = BETWEEN_FIRING_SHOTS_A
    ConditionState    = REALLYDAMAGED MOVING
      Model           = {m['modeld']}
      Animation       = {hierd}.{hierd}
      AnimationMode   = ONCE_BACKWARDS
      Flags           = START_FRAME_FIRST
    End
    AliasConditionState = REALLYDAMAGED MOVING BETWEEN_FIRING_SHOTS_A
    ConditionState    = UNPACKING
      Animation       = {hier}.{hier}
      AnimationMode   = ONCE
    End
    AliasConditionState = UNPACKING BETWEEN_FIRING_SHOTS_A
    ConditionState    = REALLYDAMAGED UNPACKING
      Model           = {m['modeld']}
      Animation       = {hierd}.{hierd}
      AnimationMode   = ONCE
    End
    AliasConditionState = REALLYDAMAGED UNPACKING BETWEEN_FIRING_SHOTS_A
    ConditionState    = PACKING
      Animation       = {hier}.{hier}
      AnimationMode   = ONCE_BACKWARDS
      Flags           = START_FRAME_LAST
    End
    AliasConditionState = PACKING BETWEEN_FIRING_SHOTS_A
    ConditionState    = REALLYDAMAGED PACKING
      Model           = {m['modeld']}
      Animation       = {hierd}.{hierd}
      AnimationMode   = MANUAL
    End
    AliasConditionState = REALLYDAMAGED PACKING BETWEEN_FIRING_SHOTS_A
    ConditionState  = DEPLOYED
      Animation       = {hier}.{hier}
      AnimationMode   = ONCE
      Flags           = START_FRAME_LAST
      TransitionKey   = TRANS_FIRING_A
    End
    AliasConditionState = DEPLOYED FIRING_A
    AliasConditionState = DEPLOYED BETWEEN_FIRING_SHOTS_A
    AliasConditionState = DEPLOYED RELOADING_A
    AliasConditionState = DEPLOYED MOVING
    ConditionState  = DEPLOYED REALLYDAMAGED
      Model           = {m['modeld']}
      Animation       = {hierd}.{hierd}
      AnimationMode   = ONCE
      Flags           = START_FRAME_LAST
      TransitionKey   = TRANS_FIRING_A
      HideSubObject   = TURRETFRONT TURRETBACK
      ShowSubObject   = TURRET01
    End
    AliasConditionState = DEPLOYED REALLYDAMAGED FIRING_A
    AliasConditionState = DEPLOYED REALLYDAMAGED BETWEEN_FIRING_SHOTS_A
    AliasConditionState = DEPLOYED REALLYDAMAGED RELOADING_A
    AliasConditionState = DEPLOYED REALLYDAMAGED MOVING
    TrackMarks = EXTireTrack.tga
    Dust = ScudLauncherDust
    DirtSpray = RocketBuggyDirtSpray
    PowerslideSpray = RocketBuggyDirtPowerSlide
    LeftFrontTireBone = Tire01
    RightFrontTireBone = Tire05
    LeftRearTireBone = Tire04
    RightRearTireBone = Tire08
    MidLeftFrontTireBone = Tire02
    MidRightFrontTireBone = Tire06
    MidLeftRearTireBone = Tire03
    MidRightRearTireBone = Tire07
    TireRotationMultiplier = 0.2
  End
  DisplayName      = OBJECT:{m['object']}
  Side = SouthKorea
  EditorSorting   = VEHICLE
  TransportSlotCount = 10
  WeaponSet
    Conditions = None
    Weapon = PRIMARY   {m['weapon']}
  End
  ArmorSet
    Conditions      = None
    Armor           = TruckArmor
    DamageFX        = TankDamageFX
  End
  BuildCost       = {m['price']}
  BuildTime       = {m['rebuild']}.0
  VisionRange     = 650
  ShroudClearingRange = 150
  ExperienceValue = 50 100 200 400
  ExperienceRequired = 0 400 600 1000
  IsTrainable = Yes
  CrusherLevel           = 2
  CrushableLevel         = 2
  CommandSet    = Scud_B_CommandSet
  VoiceSelect = ScudLauncherVoiceSelect
  VoiceMove = ScudLauncherVoiceMove
  VoiceGuard = ScudLauncherVoiceMove
  VoiceAttack = ScudLauncherVoiceAttack
  SoundMoveStart = ScudLauncherMoveStart
  SoundMoveStartDamaged = ScudLauncherMoveStart
  UnitSpecificSounds
    VoiceCreate       = ScudLauncherVoiceCreate
    TurretMoveStart = NoSound
    TurretMoveLoop = TurretMoveLoop
    TruckLandingSound = NoSound
    TruckPowerslideSound = NoSound
    VoiceCrush = ScudLauncherVoiceCrush
    VoiceEnter = ScudLauncherVoiceMove
    VoicePrimaryWeaponMode = ScudLauncherVoiceModeHiEx
    VoiceSecondaryWeaponMode = ScudLauncherVoiceModeHiEx
    VoiceTertiaryWeaponMode = ScudLauncherVoiceModeAnthrax
    Deploy              = ScudLauncherVoiceAttack
    Undeploy            = ScudLauncherVoiceCrush
  End
  RadarPriority = UNIT
  KindOf = PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE
  Body = ActiveBody ModuleTag_02
    MaxHealth       = 500.0
    InitialHealth   = 500.0
    SubdualDamageCap = 480
    SubdualDamageHealRate = 500
    SubdualDamageHealAmount = 50
  End
  Behavior = DeployStyleAIUpdate ModuleTag_04
    AutoAcquireEnemiesWhenIdle = No
    PackTime = 6555
    UnpackTime = 6555
    TurretsFunctionOnlyWhenDeployed = Yes
    TurretsMustCenterBeforePacking = Yes
    ManualDeployAnimations = Yes
  End
  Locomotor = SET_NORMAL Generic8x8Locomotor
  Behavior = PhysicsBehavior ModuleTag_05
    Mass = 400.0
  End
  Behavior = WeaponSetUpgrade ModuleTag_09h56u56j
  End
  Behavior = TransitionDamageFX ModuleTag_MB708
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuous01
    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_ScudLauncherDamageTransition
  End
  Behavior = SlowDeathBehavior ModuleTag_L8F09
    DeathTypes = ALL -CRUSHED -SPLATTED
    ProbabilityModifier = 50
    DestructionDelay = 100
    DestructionDelayVariance = 300
    FX  = INITIAL  FX_CrusaderCatchFire
    OCL = FINAL    OCL_9P117DeathEffect
    FX  = FINAL    FX_HE_ALBM_Explosion
  End
  Behavior = FXListDie ModuleTag_10F66
    DeathTypes = NONE +CRUSHED +SPLATTED
    DeathFX = FX_CarCrush
  End
  Behavior = CreateObjectDie ModuleTag_11J6
    DeathTypes = NONE +CRUSHED +SPLATTED
    CreationList = OCL_CrusaderTank_CrushEffect
  End
  Behavior = FlammableUpdate ModuleTag_21VHN
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
  End
  Behavior = DestroyDie ModuleTag_22MYUJ76
    DeathTypes = NONE +CRUSHED +SPLATTED
  End
  Behavior = ProductionUpdate ModuleTag_12
    MaxQueueEntries = 1
  End
  Geometry = BOX
  GeometryMajorRadius = 32.0
  GeometryMinorRadius = 10.0
  GeometryHeight = 17.0
  GeometryIsSmall = No
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 45
End
"""


def projectile_ini(m: dict) -> str:
    return f"""; South Korea {m['object']} projectile. Clone of ALHIJARAH_MRBM_Object.
; Dedicated W3D {m['proj_model']} + {m['tex']}. No RadarPriority.
; Intercept toughness is projectile MaxHealth only ({fmt_stat(m['hp'])} from {m['stealth']}/100 design).

Object {m['projectile']}
Scale = 0.9
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    ParticlesAttachedToAnimatedBones = Yes
    ConditionState
      Model = {m['proj_model']}
      ParticleSysBone = ENGINE01 LRBM_Trail
      ParticleSysBone = ENGINE01 LRBM_Flare2
      ParticleSysBone = ENGINE01 AGM_MissileLenzFlare
      ParticleSysBone = Engine01 SmallCruiseMissileFlare
    End
    ConditionState = POWER_PLANT_UPGRADED
      Model = {m['proj_model']}
    End
  End
  DisplayName      = OBJECT:{m['object']}
  EditorSorting   = SYSTEM
  VisionRange = 100.0
  ShroudClearingRange = 50
  ArmorSet
    Conditions      = None
    Armor           = SRBMArmor
    DamageFX        = None
  End
  SoundAmbient  = GenericMissileAmbientLoop
  KindOf = PROJECTILE BALLISTIC_MISSILE
  Body = ActiveBody ModuleTag_02
    MaxHealth       = {fmt_stat(m['hp'])}
    InitialHealth   = {fmt_stat(m['hp'])}
    SubdualDamageCap = 800
    SubdualDamageHealRate = 100000
    SubdualDamageHealAmount = 50
  End
  Behavior = InstantDeathBehavior DeathModuleTag_01
    DeathTypes = NONE +DETONATED
  End
  Behavior = InstantDeathBehavior DeathModuleTag_02
    DeathTypes = NONE +LASERED
    FX         = FX_GenericMissileDisintegrate
    OCL        = OCL_GenericMissileDisintegrate
  End
  Behavior = InstantDeathBehavior DeathModuleTag_03
    DeathTypes = ALL -LASERED -DETONATED
    FX         = FX_GenericMissileDeath
  End
  Behavior = FireWeaponUpdate ModuleTag_Booster
      Weapon = SRBM_Boosters_Igniter2
      InitialDelay = 6800
  End
  Behavior = PowerPlantUpgrade ModuleTag_IBK
    TriggeredBy = Upgrade_ICBM_BoosterKiller
  End
  Behavior = PowerPlantUpdate ModuleTag_IBKT
    RodsExtendTime = 6500
  End
  Behavior = FireWeaponWhenDeadBehavior ModuleTag_WEC
    DeathWeapon   = {m['warhead']}
    StartsActive  = Yes
  End
  Behavior = PhysicsBehavior ModuleTag_04cwe
    Mass = 15
    ShockResistance       = 0.5
    AerodynamicFriction   = 0.5
    CenterOfMassOffset    = 2
    AllowBouncing = Yes
    AllowCollideForce = Yes
    PitchRollYawFactor  = 1.5
  End
  Behavior = MissileAIUpdate ModuleTag_07
    DetonateCallsKill = Yes
    TryToFollowTarget = No
    FuelLifetime = 0
    IgnitionDelay = 0
    InitialVelocity = 10
    DistanceToTravelBeforeTurning = 1000
    DistanceToTargetBeforeDiving = 800
  End
  Locomotor = SET_NORMAL R11SRBMLocomotor
  Geometry            = Cylinder
  GeometryMajorRadius = 4.0
  GeometryHeight      = 4.0
  GeometryIsSmall     = Yes
  Shadow = SHADOW_DECAL
End
"""


def weapon_blocks(missiles: list[dict]) -> str:
    chunks = [
        WEP_MARKER + "\n"
        "; 9P117 scale: 1000 km -> AttackRange 1720; 400 kg -> PD 2000 / SD 100;\n"
        "; accuracy 10/100 -> ScatterRadius 175; intercept 5/100 -> MaxHealth 400.\n"
        "; All South Korea missiles >= 1000 km (AttackRange >= 1720) so MinimumAttackRange 800 is legal.\n"
        "; Distinct SK balance: not a copy of Japan A-J identities or values.\n"
        "; ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000 (PR #629).\n"
        "; Death HACK is a separate path and is not folded into PrimaryDamage.\n"
    ]
    for m in missiles:
        chunks.append(
            f"""
Weapon {m['weapon']}
  PrimaryDamage               = {fmt_stat(m['damage'])}
  PrimaryDamageRadius         = 80.0
  SecondaryDamage             = {fmt_stat(m['secondary'])}
  SecondaryDamageRadius       = 10.0
  ScatterRadius               = {fmt_stat(m['scatter'])}
  ScatterRadiusVsInfantry     = {fmt_stat(m['inf_scatter'])}
  AttackRange                 = {fmt_stat(m['range'])}
  MinimumAttackRange          = {fmt_stat(m['min_range'])}
  PreAttackDelay              = 500
  PreAttackType               = PER_SHOT
  DamageType                  = ARMOR_PIERCING
  DeathType                   = EXPLODED
  FireFX                      = FX_IskanderFiringEffects
  ProjectileObject            = {m['projectile']}
  ProjectileDetonationFX      = FX_SmallSRBM_Explosion
  RadiusDamageAffects         = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  FireSound                   = Iskander_Firing
  WeaponSpeed                 = 280
  AcceptableAimDelta          = 360
  DelayBetweenShots           = 3000
  ClipSize                    = 1
  AutoReloadsClip             = Yes
  ClipReloadTime              = 300000
  ShockWaveAmount             = 680.0
  ShockWaveRadius             = 150.0
  ShockWaveTaperOff           = 0.33
  AntiGround                  = Yes
End

Weapon {m['warhead']}
  PrimaryDamage           = {m['death']}
  PrimaryDamageRadius     = 20.0
  AttackRange             = 1
  DamageType              = HACK
  DeathType               = EXPLODED
  WeaponSpeed             = 9999999999
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  ClipSize                = 1
  ProjectileCollidesWith  = STRUCTURES
End
"""
        )
    return "".join(chunks)


def factory_ini() -> str:
    return """; South Korea missile factory. Clone of Iraq_AlFahdMissileFactoryBuilding visuals
; and production modules, with a SouthKorea-only CommandSet (A-J). Shared Sell-only
; Iraq_AlFahdMissileFactoryBuilding is unchanged for other isolated countries.
; Japan_MissileFactory remains the Japan A-J factory.

Object SouthKorea_MissileFactory
  SelectPortrait         = irq_warfctry
  ButtonImage            = irq_warfctry
  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    DefaultConditionState
      Model              = Irq_FahdFac
    End
    ConditionState       = DAMAGED
      Model              = Irq_FahdFac
    End
    ConditionState       = REALLYDAMAGED RUBBLE
      Model              = Irq_FahdFacD
    End
  End
  PlacementViewAngle  = -135
  DisplayName      = OBJECT:SouthKoreaMissileFactory
  Side             = SouthKorea
  EditorSorting    = STRUCTURE
  Prerequisites
    Object = SouthKorea_SupplyCenter Iraq_SupplyCenter UkraineSupplyCenter TurkeySupplyCenter ItalySupplyCenter SwedenSupplyCenter BritainSupplyCenter FranceSupplyCenter GermanySupplyCenter NatoSupplyCenter ChinaSupplyCenter Japan_SupplyCenter NorthKorea_SupplyCenter Vietnam_SupplyCenter India_SupplyCenter Pakistan_SupplyCenter SaudiArabia_SupplyCenter UAE_SupplyCenter Syria_SupplyCenter Libya_SupplyCenter SouthAfrica_SupplyCenter RussiaSupplyCenter
  End
  BuildCost        = 1800
  BuildTime        = 20.0
  EnergyProduction = -2
  CommandSet       = SouthKorea_MissileFactoryCommandSet
  VisionRange     = 200.0
  ShroudClearingRange = 200
  ArmorSet
    Conditions        = None
    Armor             = GLAUpgradedStructureArmor
    DamageFX          = StructureDamageFXNoShake
  End
  ExperienceValue     = 200 200 200 200
  VoiceSelect = WarFactoryGLASelect
  SoundOnDamaged        = BuildingDamagedStateLight
  SoundOnReallyDamaged  = BuildingDestroy
  UnitSpecificSounds
    UnderConstruction     = UnderConstructionLoop
  End
  RadarPriority     = STRUCTURE
  KindOf            = PRELOAD STRUCTURE SELECTABLE IMMOBILE CAPTURABLE AUTO_RALLYPOINT MP_COUNT_FOR_VICTORY SCORE_CREATE FS_FACTORY
  Body              = StructureBody ModuleTag_05
    MaxHealth       = 1800.0
    InitialHealth   = 1800.0
    SubdualDamageCap = 2000
    SubdualDamageHealRate = 500
    SubdualDamageHealAmount = 100
  End
  Behavior             = DestroyDie ModuleTag_07
  End
  Behavior             = CreateObjectDie ModuleTag_08
    CreationList  = OCL_LargeStructureDebris
  End
  Behavior             = FXListDie ModuleTag_09
    DeathFX       = FX_StructureMediumDeath
  End
  Behavior = ProductionUpdate ModuleTag_10
    NumDoorAnimations            = 1
    DoorOpeningTime              = 2000
    DoorWaitOpenTime             = 3000
    DoorCloseTime                = 2000
    ConstructionCompleteDuration = 1500
  End
  Behavior = DefaultProductionExitUpdate ModuleTag_11
    UnitCreatePoint   = X: -20.0  Y:-15.0   Z:0.0
    NaturalRallyPoint = X: 40.0  Y:-15.0   Z:0.0
  End
  Behavior = FlammableUpdate ModuleTag_14
    AflameDuration = 5000
    AflameDamageAmount = 5
    AflameDamageDelay = 500
  End
  Behavior = TransitionDamageFX ModuleTag_31
    DamagedParticleSystem1       = Bone:None RandomBone:No PSys:StructureTransitionMediumSmoke
    ReallyDamagedParticleSystem1 = Bone:None RandomBone:No PSys:StructureTransitionMediumSmoke
    ReallyDamagedParticleSystem2 = Bone:None RandomBone:No PSys:StructureTransitionMediumExplosion
    ReallyDamagedParticleSystem3 = Bone:None RandomBone:No PSys:StructureTransitionMediumShockwave
  End
  Geometry            = BOX
  GeometryMajorRadius = 40.0
  GeometryMinorRadius = 62.0
  GeometryHeight      = 25.0
  GeometryIsSmall     = No
  FactoryExitWidth    = 25
  Shadow              = SHADOW_VOLUME
  BuildCompletion     = PLACED_BY_PLAYER
End
"""


def commandbutton_ini(missiles: list[dict]) -> str:
    lines = [
        "; South Korea missiles A-J production buttons and factory construct button.",
        "; Shared specter_missile_* cameos. Unique Object bindings. No Iraq/Japan/Vietnam CB edits.",
        "",
        "CommandButton Command_ConstructSouthKorea_MissileFactory",
        "  Command          = DOZER_CONSTRUCT",
        "  Object           = SouthKorea_MissileFactory",
        "  TextLabel        = CONTROLBAR:ConstructSouthKoreaMissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel    = CONTROLBAR:ToolTipSouthKoreaMissileFactory",
        "End",
        "",
    ]
    for m in missiles:
        lines.extend(
            [
                f"CommandButton {m['button']}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {m['object']}",
                f"  TextLabel     = CONTROLBAR:SouthKoreaMissile{m['slot']}",
                f"  ButtonImage   = {m['cameo']}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTipSouthKoreaMissile{m['slot']}",
                "End",
                "",
            ]
        )
    return "\n".join(lines)


def vt72b_commandset() -> str:
    return (
        "CommandSet SouthKorea_VT72BCommandSet\r\n"
        "  1  = Command_ConstructSouthKorea_PowerPlant\r\n"
        "  2  = Command_ConstructSouthKorea_CommandCenter\r\n"
        "  3  = Command_ConstructSouthKorea_SupplyCenter\r\n"
        "  4  = Command_ConstructSouthKorea_WarFactory\r\n"
        "  5  = Command_ConstructSouthKorea_LargeAirBase\r\n"
        "  6  = Command_ConstructSouthKorea_MissileFactory\r\n"
        "  7  = Command_ConstructSouthKorea_DefenseSite_SAFE\r\n"
        "  8  = Command_ConstructSouthKorea_RadarStation\r\n"
        "  9  = Command_ConstructSouthKorea_HeavyAirBase\r\n"
        "  10 = Command_ConstructSouthKorea_Barracks_SAFE\r\n"
        "  11 = Command_ConstructSouthKorea_NuclearCenter\r\n"
        "  12 = Command_ConstructSouthKorea_D30_SAFE\r\n"
        "  13 = Command_ConstructSouthKorea_CRAM\r\n"
        "  14 = Command_ConstructSouthKorea_Hq9_Site\r\n"
        "  15 = Command_Stop\r\n"
        "End"
    )


def factory_commandset() -> str:
    slots = "\r\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(DERIVED, start=1))
    return (
        "CommandSet SouthKorea_MissileFactoryCommandSet\r\n"
        f"{slots}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def commandset_ini() -> str:
    return vt72b_commandset() + "\r\n\r\n" + factory_commandset() + "\r\n"


def csf_map() -> dict[str, str]:
    mapping = {
        "OBJECT:SouthKoreaMissileFactory": "Missile Factory",
        "CONTROLBAR:ConstructSouthKoreaMissileFactory": "Missile Factory",
        "CONTROLBAR:ToolTipSouthKoreaMissileFactory": (
            "Missile Factory\nProduces South Korean missiles A-J\nPrice: $1800"
        ),
    }
    for m in DERIVED:
        mapping[f"OBJECT:{m['object']}"] = m["name"]
        mapping[f"CONTROLBAR:SouthKoreaMissile{m['slot']}"] = m["name"]
        mapping[f"CONTROLBAR:ToolTipSouthKoreaMissile{m['slot']}"] = m["tooltip"]
    return mapping


def write_loose() -> None:
    fac_dir = LOOSE / "Object/Specter/South Korean Armed Forces/Buildings"
    wheel_dir = LOOSE / "Object/Specter/South Korean Armed Forces/Wheeled"
    proj_dir = LOOSE / "Object/Specter/South Korean Armed Forces"
    wep_dir = LOOSE / "Weapon"
    fac_dir.mkdir(parents=True, exist_ok=True)
    wheel_dir.mkdir(parents=True, exist_ok=True)
    proj_dir.mkdir(parents=True, exist_ok=True)
    wep_dir.mkdir(parents=True, exist_ok=True)
    (fac_dir / "SouthKorea_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    (wep_dir / "Weapon_SouthKorea_Missiles.ini").write_text(weapon_blocks(DERIVED), encoding="utf-8")
    (LOOSE / "CommandButton_SouthKoreaMissiles.ini").write_text(commandbutton_ini(DERIVED), encoding="utf-8")
    (LOOSE / "CommandSet_SouthKoreaMissiles.ini").write_text(commandset_ini(), encoding="utf-8")
    for m in DERIVED:
        (wheel_dir / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (proj_dir / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")


def illegal_floats(text: str) -> list[str]:
    return re.findall(r"\b\d+\.\d+\.0\b", text)


def validate(
    data: dict[str, bytes],
    art: dict[str, bytes],
    src_data: dict[str, bytes],
    src_art: dict[str, bytes],
    order: list[str],
) -> list[str]:
    fails: list[str] = []
    for key in FROZEN_DATA:
        if data.get(key) != src_data.get(key):
            fails.append(f"frozen DATA mutated {key}")
    for key in FROZEN_ART:
        if key in src_art and art.get(key) != src_art.get(key):
            fails.append(f"frozen ART mutated {key}")

    cs_text = data[CS_KEY].decode("latin1")
    src_cs = src_data[CS_KEY].decode("latin1")
    cb_text = data[CB_KEY].decode("latin1")
    src_cb = src_data[CB_KEY].decode("latin1")
    wep_text = data[WEAPON_KEY].decode("latin1")
    src_wep = src_data[WEAPON_KEY].decode("latin1")

    if last_block(cs_text, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet") != last_block(
        src_cs, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet"
    ):
        fails.append("Iraq factory roster mutated")
    if last_block(cs_text, "CommandSet", "Iraq_AlFahdMissileFactoryBuildingCommandSet") != last_block(
        src_cs, "CommandSet", "Iraq_AlFahdMissileFactoryBuildingCommandSet"
    ):
        fails.append("Iraq Sell-only building CommandSet mutated")
    if last_block(cs_text, "CommandSet", "Vietnam_MissileFactoryCommandSet") != last_block(
        src_cs, "CommandSet", "Vietnam_MissileFactoryCommandSet"
    ):
        fails.append("Vietnam factory CommandSet mutated")
    if last_block(cs_text, "CommandSet", "Vietnam_VT72BCommandSet") != last_block(
        src_cs, "CommandSet", "Vietnam_VT72BCommandSet"
    ):
        fails.append("Vietnam VT72B CommandSet mutated")
    nk_cs = last_block(cs_text, "CommandSet", "NorthKorea_VT72BCommandSet")
    src_nk = last_block(src_cs, "CommandSet", "NorthKorea_VT72BCommandSet")
    if nk_cs != src_nk:
        fails.append("NorthKorea VT72B mutated")
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in nk_cs:
        fails.append("NorthKorea lost shared Sell-only factory")
    if "Command_ConstructSouthKorea_MissileFactory" in nk_cs:
        fails.append("NorthKorea gained South Korea factory")
    if "Command_ConstructJapan_MissileFactory" in nk_cs:
        fails.append("NorthKorea gained Japan factory")

    jp_cs = last_block(cs_text, "CommandSet", "Japan_VT72BCommandSet")
    src_jp = last_block(src_cs, "CommandSet", "Japan_VT72BCommandSet")
    if jp_cs != src_jp:
        fails.append("Japan VT72B CommandSet mutated")
    if "Command_ConstructJapan_MissileFactory" not in jp_cs:
        fails.append("CommandSet.ini Japan VT72B not Japan factory")
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in jp_cs:
        fails.append("CommandSet.ini Japan VT72B still Sell-only factory")
    if last_block(cs_text, "CommandSet", "Japan_MissileFactoryCommandSet") != last_block(
        src_cs, "CommandSet", "Japan_MissileFactoryCommandSet"
    ):
        fails.append("Japan factory CommandSet mutated")

    sk_cs = last_block(cs_text, "CommandSet", "SouthKorea_VT72BCommandSet")
    if "Command_ConstructSouthKorea_MissileFactory" not in sk_cs:
        fails.append("CommandSet.ini SouthKorea VT72B not SK factory")
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in sk_cs:
        fails.append("CommandSet.ini SouthKorea VT72B still Sell-only factory")
    if "Command_ConstructJapan_MissileFactory" in sk_cs:
        fails.append("SouthKorea gained Japan factory")

    fac_cs = last_block(cs_text, "CommandSet", "SouthKorea_MissileFactoryCommandSet")
    if not fac_cs:
        fails.append("CommandSet.ini missing SouthKorea_MissileFactoryCommandSet")
    for m in DERIVED:
        if m["button"] not in fac_cs:
            fails.append(f"factory missing {m['button']}")
    if "Command_Sell" not in fac_cs:
        fails.append("factory missing Sell")
    if "Command_SetRallyPoint" not in fac_cs:
        fails.append("factory missing Rally")
    fac_slots = re.findall(r"CB_SOUTHKOREA_MISSILE_([A-Z])", fac_cs)
    if fac_slots != list("ABCDEFGHIJ"):
        fails.append(f"factory slots {fac_slots} != A-J")
    if "CB_JAPAN_MISSILE_" in fac_cs or "CB_VIETNAM_MISSILE_" in fac_cs or "CB_IRAQ_" in fac_cs:
        fails.append("factory mixed foreign missile buttons")
    if len(DERIVED) != 10:
        fails.append(f"roster count {len(DERIVED)}")

    _k, lw_cs = last_block_from_files(order, data, "CommandSet", "SouthKorea_VT72BCommandSet")
    if "Command_ConstructSouthKorea_MissileFactory" not in lw_cs:
        fails.append(f"last-wins VT72B from {_k} not SK factory")
    _k, lw_fac = last_block_from_files(order, data, "CommandSet", "SouthKorea_MissileFactoryCommandSet")
    if not lw_fac:
        fails.append("last-wins missing SouthKorea_MissileFactoryCommandSet")

    _k, fac_obj = last_block_from_files(order, data, "Object", "SouthKorea_MissileFactory")
    if field(fac_obj, "CommandSet") != "SouthKorea_MissileFactoryCommandSet":
        fails.append(f"factory object CommandSet {field(fac_obj, 'CommandSet')} from {_k}")
    if field(fac_obj, "Side") != "SouthKorea":
        fails.append("factory Side")

    _k, construct = last_block_from_files(
        order, data, "CommandButton", "Command_ConstructSouthKorea_MissileFactory"
    )
    if field(construct, "Object") != "SouthKorea_MissileFactory":
        fails.append(f"construct Object from {_k}")
    if field(construct, "Command") != "DOZER_CONSTRUCT":
        fails.append("construct Command")
    if field(construct, "ButtonImage") != "Button_MissileFactory":
        fails.append("construct image")
    if last_block(cb_text, "CommandButton", "Command_ConstructSouthKorea_MissileFactory") == "":
        fails.append("CommandButton.ini missing construct button")
    if last_block(cb_text, "CommandButton", "Command_ConstructJapan_MissileFactory") != last_block(
        src_cb, "CommandButton", "Command_ConstructJapan_MissileFactory"
    ):
        fails.append("Japan construct button mutated")

    for img, btn in (
        ("Button_kashtan", "Command_ConstructRussiaKashtan"),
        ("Button_falaq", "Command_ConstructIranFalaqTrench"),
        ("Button_Bio", "Command_ConstructIraq_Abbas"),
        ("Button_MissileFactory", "Command_ConstructVietnam_MissileFactory"),
    ):
        if field(last_block(cb_text, "CommandButton", btn), "ButtonImage") != img:
            fails.append(f"{btn} image lost")
        if last_block(cb_text, "CommandButton", btn) != last_block(src_cb, "CommandButton", btn):
            fails.append(f"{btn} mutated")

    r11 = last_block(data[R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB")
    if field(r11, "BuildCost") != "1200":
        fails.append("9P117 BuildCost")
    if "Irq_9P117" not in r11:
        fails.append("9P117 model")

    mother = last_block(wep_text, "Weapon", "SRBM_ALHIJARAH_HE")
    src_mother = last_block(src_wep, "Weapon", "SRBM_ALHIJARAH_HE")
    if mother != src_mother:
        fails.append("MOTHER weapon mutated")
    if field(mother, "PrimaryDamage") != "2000.0":
        fails.append("MOTHER PrimaryDamage")
    if field(mother, "SecondaryDamage") != "100.0":
        fails.append("MOTHER SecondaryDamage")
    if field(mother, "ClipReloadTime") != "300000":
        fails.append("MOTHER ClipReloadTime")
    if last_block(wep_text, "Weapon", "HE_9M729_450kg") != last_block(src_wep, "Weapon", "HE_9M729_450kg"):
        fails.append("MOTHER warhead mutated")
    if last_block(wep_text, "Weapon", "Weapon_Vietnam_VCM01") != last_block(
        src_wep, "Weapon", "Weapon_Vietnam_VCM01"
    ):
        fails.append("Vietnam VCM01 weapon mutated")
    if last_block(wep_text, "Weapon", "Weapon_Iraq_AlFahd500") != last_block(
        src_wep, "Weapon", "Weapon_Iraq_AlFahd500"
    ):
        fails.append("AlFahd weapon mutated")
    if last_block(wep_text, "Weapon", "Weapon_Japan_Type12Kai") != last_block(
        src_wep, "Weapon", "Weapon_Japan_Type12Kai"
    ):
        fails.append("Japan Type12Kai weapon mutated")
    if last_block(wep_text, "Weapon", "Weapon_Japan_Tenrai") != last_block(
        src_wep, "Weapon", "Weapon_Japan_Tenrai"
    ):
        fails.append("Japan Tenrai weapon mutated")

    if illegal_floats(wep_text):
        fails.append(f"illegal floats {illegal_floats(wep_text)}")
    if "ZZZZ" in NEW_CB_KEY or "ZZZZ" in NEW_CS_KEY:
        fails.append("ZZZZ shortcut")

    csf = data[CSF_KEY]
    truck = Image.open(io.BytesIO(art[TRUCK_KEY])).convert("RGB")
    truck_avg = truck.resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
    if truck_avg[1] > truck_avg[2] + 8:
        fails.append(f"truck still green {truck_avg}")
    if max(truck_avg) - min(truck_avg) > 35:
        fails.append(f"truck not slate-neutral {truck_avg}")
    if not (40 <= (sum(truck_avg) / 3.0) <= 130):
        fails.append(f"truck brightness {truck_avg}")

    for m in DERIVED:
        unit = last_block(data[m["unit_key"]].decode("latin1"), "Object", m["object"])
        if field(unit, "BuildCost") != str(m["price"]):
            fails.append(f"{m['slot']} BuildCost")
        if not field(unit, "BuildTime").startswith(f"{m['rebuild']}.0"):
            fails.append(f"{m['slot']} BuildTime")
        if field(unit, "Side") != "SouthKorea":
            fails.append(f"{m['slot']} Side")
        if field(unit, "ButtonImage") != m["cameo"]:
            fails.append(f"{m['slot']} cameo")
        if field(unit, "SelectPortrait") != m["cameo"]:
            fails.append(f"{m['slot']} portrait")
        if f"Model                           = {m['model']}" not in unit:
            fails.append(f"{m['slot']} TEL model")
        hier = m["hier"].decode()
        if f"{hier}.{hier}" not in unit:
            fails.append(f"{m['slot']} animation")
        if m["weapon"] not in unit:
            fails.append(f"{m['slot']} weapon bind")
        if field(unit, "CommandSet") != "Scud_B_CommandSet":
            fails.append(f"{m['slot']} CommandSet")
        if re.search(r"Weapon\s*=\s*SECONDARY", unit) or re.search(r"Weapon\s*=\s*TERTIARY", unit):
            fails.append(f"{m['slot']} extra weapon slot")
        if "Rearm" in unit or "RiderChangeContain" in unit or "InitialPayload" in unit:
            fails.append(f"{m['slot']} unexpected rearm/contain")
        if "JapanVehicleType12" in unit or "Japan_Type12" in unit:
            fails.append(f"{m['slot']} collided with Japan Type 12")
        if "SouthKoreaVehicleHyunmoo" in unit or "Hwasong" in unit:
            fails.append(f"{m['slot']} collided with Hyunmoo/Hwasong")

        proj = last_block(data[m["proj_key"]].decode("latin1"), "Object", m["projectile"])
        if f"Model = {m['proj_model']}" not in proj:
            fails.append(f"{m['slot']} flying model")
        if field(proj, "MaxHealth") != fmt_stat(m["hp"]):
            fails.append(f"{m['slot']} HP {field(proj, 'MaxHealth')}")
        if field(proj, "RadarPriority"):
            fails.append(f"{m['slot']} unexpected RadarPriority")

        ini_w = last_block(wep_text, "Weapon", m["weapon"])
        if not ini_w:
            fails.append(f"{m['slot']} missing from Weapon.ini")
        _k, wblock = last_block_from_files(order, data, "Weapon", m["weapon"])
        if field(ini_w, "AttackRange") != fmt_stat(m["range"]):
            fails.append(f"{m['slot']} Weapon.ini range {field(ini_w, 'AttackRange')}")
        if field(wblock, "AttackRange") != fmt_stat(m["range"]):
            fails.append(f"{m['slot']} range {field(wblock, 'AttackRange')}")
        if field(wblock, "PrimaryDamage") != fmt_stat(m["damage"]):
            fails.append(f"{m['slot']} damage")
        if field(wblock, "SecondaryDamage") != fmt_stat(m["secondary"]):
            fails.append(f"{m['slot']} splash {field(wblock, 'SecondaryDamage')}")
        if field(wblock, "ScatterRadius") != fmt_stat(m["scatter"]):
            fails.append(f"{m['slot']} scatter {field(wblock, 'ScatterRadius')}")
        if field(wblock, "ProjectileObject") != m["projectile"]:
            fails.append(f"{m['slot']} projectile bind")
        if field(wblock, "MinimumAttackRange") != fmt_stat(m["min_range"]):
            fails.append(f"{m['slot']} min range {field(wblock, 'MinimumAttackRange')}")
        if field(wblock, "ClipSize") != "1":
            fails.append(f"{m['slot']} ClipSize")
        if field(wblock, "AutoReloadsClip") != "Yes":
            fails.append(f"{m['slot']} AutoReloadsClip")
        if field(wblock, "ClipReloadTime") != "300000":
            fails.append(f"{m['slot']} ClipReloadTime")
        death = last_block(wep_text, "Weapon", m["warhead"])
        if field(death, "PrimaryDamage") != str(m["death"]):
            fails.append(f"{m['slot']} death {field(death, 'PrimaryDamage')}")
        if field(death, "DamageType") != "HACK":
            fails.append(f"{m['slot']} death type")

        bblock = last_block(cb_text, "CommandButton", m["button"])
        if field(bblock, "Object") != m["object"]:
            fails.append(f"{m['slot']} button object")
        if field(bblock, "ButtonImage") != m["cameo"]:
            fails.append(f"{m['slot']} button image")
        if field(bblock, "Command") != "UNIT_BUILD":
            fails.append(f"{m['slot']} button command")
        if csf_get(csf, f"CONTROLBAR:SouthKoreaMissile{m['slot']}") != m["name"]:
            fails.append(f"{m['slot']} CSF name")
        if csf_get(csf, f"CONTROLBAR:ToolTipSouthKoreaMissile{m['slot']}") != m["tooltip"]:
            fails.append(f"{m['slot']} CSF tooltip")

        tel = art[m["tel_key"]]
        teld = art[m["teld_key"]]
        projw = art[m["projw_key"]]
        if m["hier"] not in tel:
            fails.append(f"{m['slot']} TEL hier")
        if m["hierd"] not in teld:
            fails.append(f"{m['slot']} TEL D hier")
        if m["proj_hier"] not in projw:
            fails.append(f"{m['slot']} proj hier")
        for blob, label in ((tel, "TEL"), (teld, "TELD"), (projw, "PROJ")):
            for banned in (b"IRQ_9P117", b"IRQ_R11_M", b"IRQ_AF500", b"IRQ_ALF_M", b"GENERIC-MISSILES"):
                if banned in blob:
                    fails.append(f"{m['slot']} {label} leaked {banned.decode()}")
        tel_tex = all_tex(tel)
        teld_tex = all_tex(teld)
        proj_tex = all_tex(projw)
        if m["tex"] not in tel_tex or TRUCK_TEX not in tel_tex:
            fails.append(f"{m['slot']} TEL tex {tel_tex}")
        if "Irq_9P117.tga" in tel_tex or "Irq_9P117D.tga" in tel_tex:
            fails.append(f"{m['slot']} TEL still Iraqi truck")
        if m["tex"] not in teld_tex or TRUCKD_TEX not in teld_tex:
            fails.append(f"{m['slot']} TELD tex {teld_tex}")
        if proj_tex != {m["tex"]}:
            fails.append(f"{m['slot']} proj tex {proj_tex}")

        im = Image.open(io.BytesIO(art[m["tex_key"]])).convert("RGB")
        if im.size != (SHEET, SHEET):
            fails.append(f"{m['slot']} skin size {im.size}")
        body = region_mode(im, (80, 410, 200, 560))
        top_body = max(body, key=body.get)
        allowed = {
            "muddy": {"muddy", "olive", "green"},
            "cream": {"cream", "white", "yellow"},
            "red": {"red"},
            "blue": {"blue"},
            "white": {"white"},
            "petrol": {"petrol", "teal", "blue"},
            "black": {"black"},
            "gray": {"gray"},
            "orange": {"orange", "yellow"},
            "yellow": {"yellow", "orange"},
        }
        if top_body not in allowed[m["expect"]]:
            fails.append(f"{m['slot']} body {top_body} {body}")
        if m["km"] < KM_FLOOR or m["km"] > KM_CEILING:
            fails.append(f"{m['slot']} km {m['km']}")
        if m["kg"] < KG_FLOOR or m["kg"] > KG_CEILING:
            fails.append(f"{m['slot']} kg {m['kg']}")
        if float(field(wblock, "AttackRange")) < MOTHER_RANGE * (KM_FLOOR / 1000.0) - 0.01:
            fails.append(f"{m['slot']} range below 1000 km")
        tel_flag = region_mode(im, (110, 180, 420, 290))
        proj_flag = region_mode(im, (110, 690, 420, 800))
        if not has_sk_flag(tel_flag):
            fails.append(f"{m['slot']} TEL flag {tel_flag}")
        if not has_sk_flag(proj_flag):
            fails.append(f"{m['slot']} proj flag {proj_flag}")
        if not has_name_plate(im, (500, 190, 960, 280)):
            fails.append(f"{m['slot']} TEL name plate")
        if not has_name_plate(im, (500, 700, 960, 790)):
            fails.append(f"{m['slot']} proj name plate")

    jp_vt = last_block(data[JPN_VT72B_KEY].decode("latin1"), "Object", "Japan_VT72B")
    if field(jp_vt, "CommandSet") != "Japan_VT72BCommandSet":
        fails.append("Japan_VT72B CommandSet mutated")
    if field(jp_vt, "Side") != "Japan":
        fails.append("Japan_VT72B Side")
    sk_vt = last_block(data[SK_VT72B_KEY].decode("latin1"), "Object", "SouthKorea_VT72B")
    if field(sk_vt, "CommandSet") != "SouthKorea_VT72BCommandSet":
        fails.append("SouthKorea_VT72B CommandSet mutated")
    if field(sk_vt, "Side") != "SouthKorea":
        fails.append("SouthKorea_VT72B Side")
    if "SouthKoreaVehicleHyunmoo" not in data[NG_KEY].decode("latin1"):
        fails.append("Hyunmoo missing from NationalGround")
    return fails


def mapping_report() -> list[str]:
    lines = [
        "GAMEPLAY MAPPING (9P117 MOTHER scale, properties independent):",
        "  AttackRange 1720 = 1000 km design. Formula: 1720 * (km / 1000).",
        "  PrimaryDamage 2000 = 400 kg. Formula: 2000 * (kg / 400).",
        "  SecondaryDamage 100 = 400 kg splash. Formula: 100 * (kg / 400).",
        "  Death warhead HACK 2200 = 400 kg extra. Formula: 2200 * (kg / 400).",
        "    Death HACK is a separate path and is NOT folded into PrimaryDamage.",
        "  ScatterRadius 175 = 10/100 accuracy design. Formula: 175 * (10 / acc).",
        "    Limitation: ScatterRadius is impact dispersion, not a hit-chance percent.",
        "  Projectile MaxHealth 400 = 5/100 intercept-challenge design.",
        "    Formula: 400 * (challenge / 5). No RadarPriority.",
        "    Limitation: no native interception-probability percentage.",
        "  All missiles >= 1000 km so MinimumAttackRange stays 800.",
        "  South Korea roster is independently balanced (not a copy of Japan A-J).",
        "  ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000 (5 minutes).",
        "  PRIMARY only; no SECONDARY/TERTIARY fire path to bypass cooldown.",
        "  BuildCost / BuildTime set on the unit Object (factory production).",
        "",
        "SLOT  NAME            KM   KG   ACC CHL TIME COST  RANGE  PD     SD    DEATH SCATTER  HP     MINR",
    ]
    for m in DERIVED:
        lines.append(
            f"  {m['slot']}    {m['name']:<14} {m['km']:<4} {m['kg']:<4} "
            f"{m['acc']:<3} {m['stealth']:<3} {m['rebuild']:<4} {m['price']:<5} "
            f"{fmt_stat(m['range']):<6} {fmt_stat(m['damage']):<6} {fmt_stat(m['secondary']):<5} "
            f"{m['death']:<5} {fmt_stat(m['scatter']):<7} {fmt_stat(m['hp']):<6} "
            f"{fmt_stat(m['min_range'])}"
        )
    return lines


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_630 or SRC_DATA.stat().st_size != SIZE_DATA_630:
        raise SystemExit("DATA baseline is not PR #630 SPECTER_JAPAN_MISSILES_AJ")
    if sha256_path(SRC_ART) != SHA_ART_630 or SRC_ART.stat().st_size != SIZE_ART_630:
        raise SystemExit("ART baseline is not PR #630 SPECTER_JAPAN_MISSILES_AJ")

    src_data, _ = parse_big_ordered(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    flag = make_sk_flag()
    truck = recolor_truck(Image.open(io.BytesIO(src_art[TRUCK_DDS])), damaged=False)
    truckd = recolor_truck(Image.open(io.BytesIO(src_art[TRUCKD_DDS])), damaged=True)
    art[TRUCK_KEY] = make_tga32(truck)
    art[TRUCKD_KEY] = make_tga32(truckd)

    for m in DERIVED:
        skin = make_skin(m["body"], m["nose"], m["name"], flag)
        art[m["tex_key"]] = make_tga32(skin)
        art[m["tel_key"]] = make_tel_w3d(src_art[TEL_W3D], False, m)
        art[m["teld_key"]] = make_tel_w3d(src_art[TELD_W3D], True, m)
        art[m["projw_key"]] = make_proj_w3d(src_art[PROJ_W3D], m)
        data[m["unit_key"]] = to_crlf(unit_ini(m))
        data[m["proj_key"]] = to_crlf(projectile_ini(m))

    data[NEW_FAC_KEY] = to_crlf(factory_ini())
    data[NEW_WEP_KEY] = to_crlf(weapon_blocks(DERIVED))
    data[NEW_CB_KEY] = to_crlf(commandbutton_ini(DERIVED))
    data[NEW_CS_KEY] = to_crlf(commandset_ini())
    data[CSF_KEY] = csf_upsert(src_data[CSF_KEY], csf_map())

    cs = src_data[CS_KEY].decode("latin1")
    old_sk = last_block(cs, "CommandSet", "SouthKorea_VT72BCommandSet")
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in old_sk:
        raise SystemExit("unexpected CommandSet.ini SouthKorea_VT72BCommandSet")
    if "Command_ConstructSouthKorea_MissileFactory" in old_sk:
        raise SystemExit("SouthKorea_VT72BCommandSet already had SK factory")
    cs = replace_last(cs, "CommandSet", "SouthKorea_VT72BCommandSet", vt72b_commandset())
    if last_block(cs, "CommandSet", "SouthKorea_MissileFactoryCommandSet"):
        cs = replace_last(cs, "CommandSet", "SouthKorea_MissileFactoryCommandSet", factory_commandset())
    else:
        cs = cs.rstrip("\r\n") + "\r\n\r\n" + factory_commandset() + "\r\n"
    data[CS_KEY] = cs.encode("latin1")

    cb = src_data[CB_KEY].decode("latin1")
    extra = commandbutton_ini(DERIVED).replace("\n", "\r\n")
    if "CommandButton Command_ConstructSouthKorea_MissileFactory" in cb:
        raise SystemExit("CommandButton.ini already had SK construct; inspect before splicing")
    data[CB_KEY] = (cb.rstrip("\r\n") + "\r\n\r\n" + extra).encode("latin1")

    wep = src_data[WEAPON_KEY].decode("latin1")
    if WEP_MARKER in wep:
        raise SystemExit("Weapon.ini already had South Korea marker; inspect before splicing")
    data[WEAPON_KEY] = (wep.rstrip("\r\n") + "\r\n\r\n" + weapon_blocks(DERIVED).replace("\n", "\r\n")).encode("latin1")

    write_loose()

    data_big = build_big(data)
    art_big = build_big(art)
    packed_data, order = parse_big_ordered(data_big)
    packed_art = parse_big(art_big)
    fails = validate(packed_data, packed_art, src_data, src_art, order)
    fails.extend(f"DATA {x}" for x in big_structure_ok(data_big))
    fails.extend(f"ART {x}" for x in big_structure_ok(art_big))
    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_big)
    art_path.write_bytes(art_big)

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "CommandSet.ini.SouthKorea.txt").write_text(
        last_block(packed_data[CS_KEY].decode("latin1"), "CommandSet", "SouthKorea_VT72BCommandSet")
        + "\r\n\r\n"
        + last_block(packed_data[CS_KEY].decode("latin1"), "CommandSet", "SouthKorea_MissileFactoryCommandSet")
        + "\r\n",
        encoding="utf-8",
    )
    (ext / "Weapon.ini.SouthKorea.txt").write_text(weapon_blocks(DERIVED), encoding="utf-8")
    (ext / "SouthKorea_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    for m in DERIVED:
        (ext / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (ext / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    preview = OUT / "PREVIEW"
    preview.mkdir(parents=True)
    truck.save(preview / "Skr_TEL.png")
    truckd.save(preview / "Skr_TELD.png")
    flag.save(preview / "Taegeukgi.png")
    Image.open(io.BytesIO(src_art[TRUCK_DDS])).convert("RGB").save(preview / "Irq_9P117_donor.png")
    for m in DERIVED:
        Image.open(io.BytesIO(packed_art[m["tex_key"]])).save(preview / f"{m['slot']}_{m['object']}.png")
        Image.open(io.BytesIO(packed_art[m["tex_key"]])).crop((40, 150, 980, 320)).save(
            preview / f"{m['slot']}_dorsal_tel.png"
        )
        Image.open(io.BytesIO(packed_art[m["tex_key"]])).crop((40, 660, 980, 830)).save(
            preview / f"{m['slot']}_dorsal_proj.png"
        )

    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_SK_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    inv = [
        "PRE-CHANGE SOUTH KOREA ROSTER (packed last-wins, PR #630 Japan A-J):",
        "  FactionSouthKorea StartingUnit0 = SouthKorea_VT72B",
        "  SouthKorea_VT72B CommandSet = SouthKorea_VT72BCommandSet",
        "  SouthKorea_VT72BCommandSet slot 6 = Command_ConstructIraq_AlFahdMissileFactoryBuilding (Sell-only)",
        "  SouthKorea_MissileFactory: MISSING",
        "  SouthKorea_WarFactory: USA vehicle roster (untouched)",
        "  SouthKoreaVehicleHyunmoo / SouthKorea Hwasong: existing unrelated units (untouched)",
        "  Japan A-J factory and weapons remain in the baseline (frozen).",
        "",
        "POST-CHANGE SOUTH KOREA ROSTER:",
        "  SouthKorea_VT72BCommandSet slot 6 = Command_ConstructSouthKorea_MissileFactory",
        "  SouthKorea_MissileFactory / SouthKorea_MissileFactoryCommandSet = CB_SOUTHKOREA_MISSILE_A-J",
        "  Weapons last-wins in Data\\INI\\Weapon.ini",
        "  Buttons last-wins in Data\\INI\\CommandButton.ini",
        "  PRIMARY only + Scud_B_CommandSet / Command_FireMainWeapon",
        "  5-minute clip reload. No RadarPriority. No rearm.",
        "",
        *map_lines,
        "",
        "NEW / SPLICED DATA FILES:",
        f"  {CS_KEY} (SouthKorea_VT72BCommandSet + SouthKorea_MissileFactoryCommandSet)",
        f"  {CB_KEY} (construct + CB_SOUTHKOREA_MISSILE_A-J)",
        f"  {WEAPON_KEY} (Weapon_SouthKorea_* + warheads)",
        f"  {CSF_KEY}",
        f"  {NEW_CS_KEY}",
        f"  {NEW_CB_KEY}",
        f"  {NEW_WEP_KEY}",
        f"  {NEW_FAC_KEY}",
    ]
    for m in DERIVED:
        inv.append(f"  {m['unit_key']}")
        inv.append(f"  {m['proj_key']}")
    inv.append("")
    inv.append("NEW ART FILES:")
    inv.append(f"  {TRUCK_KEY} / {TRUCKD_KEY}")
    for m in DERIVED:
        inv.append(f"  {m['tel_key']} / {m['teld_key']} / {m['projw_key']} / {m['tex_key']}")

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #630 s-japan-missiles-aj + PR #629 cooldown/damage",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "IRAQ_FACTORY_ROSTER_UNCHANGED=YES",
        "VIETNAM_AH_UNCHANGED=YES",
        "JAPAN_AJ_UNCHANGED=YES",
        "NINE_P117_UNCHANGED=YES",
        "KASHTAN_FALAQ_RETAINED=YES",
        "IRAQ_ABBAS_BIO_RETAINED=YES",
        "SK_HYUNMOO_HWASONG_UNCHANGED=YES",
        "NO_REARM=YES",
        "NO_ZZZZ=YES",
        "NO_RADARPRIORITY=YES",
        "ROSTER_COUNT=10",
        "KM_FLOOR=1000",
        "KG_FLOOR=400",
        "",
        *inv,
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    hashes = "\n".join(
        [
            "DATA_CHANGED=YES",
            "ART_CHANGED=YES",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_SIZE={art_path.stat().st_size}",
            f"ART_SHA256={art_sha}",
            "ZIP_FILE=SPECTER_SK_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #630",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-sk-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-sk-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-sk-missiles-aj/SPECTER_SK_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-sk-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-sk-missiles-aj",
                "BASELINE=PR #630",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "South Korea missiles A-J on the verified 9P117 / Al-Fahd / Vietnam / Japan / PR #630 path.\n"
        "Ten-missile factory roster. Japan A-J, Iraq A-M, Vietnam A-H, and 9P117 unchanged.\n"
        "Cool-slate trucks, ten-color tube palette, Taegeukgi + exact names on dorsal UV bands.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# South Korea missiles A-J\n\n"
        "- Ten independently identifiable South Korean TELs cloned from 9P117 / Al-Fahd.\n"
        "- Dedicated SouthKorea_MissileFactory; dozer slot 6 no longer builds the Sell-only Iraq factory.\n"
        "- Fictional SPECTER roster: Baekho, Cheonma, Haeryong, Hwarang, Mugunghwa, Taebaek, Jindallae, Geommu, Haetsal, Cheonwang.\n"
        "- All missiles >= 1000 km and >= 400 kg. Distinct SK balance, not a copy of Japan A-J.\n"
        "- Shared cool-slate South Korean truck; per-missile tube color from the global 10-color palette.\n"
        "- Top-facing Taegeukgi + exact missile name on TEL and projectile dorsal UV bands.\n"
        "- Weapons spliced into Weapon.ini. Buttons/CommandSets spliced into live catalogs.\n"
        "- 5-minute clip reload. Damage scaled from 9P117 400 kg = 2000/100.\n"
        "- 9P117, Iraq factory A-M, Japan A-J, Vietnam A-H, Kashtan, Falaq, and Abbas Bio are unchanged.\n"
        "- Existing South Korea Hyunmoo / Hwasong / WarFactory / construction buttons are untouched.\n"
        "- No rearm. No ZZZZ overrides. No RadarPriority.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n", encoding="utf-8")
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet.ini last SouthKorea_VT72BCommandSet is now the South Korea factory construct.\n"
        "CommandSet_SouthKoreaMissiles.ini last-wins the same two CommandSets.\n"
        "CommandButton.ini now defines the construct + A-J buttons; satellite file matches.\n"
        "Weapon.ini last-wins Weapon_SouthKorea_* (satellite Weapon\\Weapon_SouthKorea_Missiles.ini is not the load path).\n"
        "Japan A-J factory/weapons, Iraq factory, Vietnam factory, and 9P117 are unchanged.\n"
        "SouthKoreaVehicleHyunmoo and Hwasong units are untouched.\n"
        "SouthKorea_WarFactory and existing SK construction buttons are untouched.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:60]))


if __name__ == "__main__":
    main()
