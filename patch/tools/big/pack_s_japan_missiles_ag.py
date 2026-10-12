#!/usr/bin/env python3
"""Implement Japan missile roster A-G from the verified 9P117 / Al-Fahd / Vietnam path.

Baseline: PR #629 SPECTER_MISSILE_5MIN_CD_DMG (accepted DATA+ART).

Japan currently constructs Iraq_AlFahdMissileFactoryBuilding (Sell-only).
A Japan-only factory object is required so other isolated countries do not
inherit this roster. Live catalogs are CommandSet.ini, CommandButton.ini,
and Weapon.ini (satellite Weapon\\*.ini is not a reliable load path).

ART: dedicated W3D clones. Truck meshes remap Irq_9P117.tga / Irq_9P117D.tga
to Japanese olive-drab Jpn_TEL.tga / Jpn_TELD.tga. Tube/projectile use
per-missile Jpn_*P.tga with Hinomaru + exact name on proven dorsal UV bands.

No RadarPriority. Intercept toughness = projectile MaxHealth only.
No rearm / RiderChangeContain. No ZZZZ files. 9P117 and Vietnam A-H stay frozen.
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
SRC_DATA = ROOT / "patch/Release/SPECTER_MISSILE_5MIN_CD_DMG/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_MISSILE_5MIN_CD_DMG/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_JAPAN_MISSILES_AG"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_629 = "2c6b967ce57236e1e1682faf375a38b5e531925607139e2345ca57d2d86cc53c"
SIZE_DATA_629 = 366826867
SHA_ART_629 = "3030c68abc11b801121feeac44a21af4407ffa9be385fba0f979d01fd7e4ab44"
SIZE_ART_629 = 1343628546

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

TEL_W3D = r"Art\W3D\Irq_AlFahd500.W3D"
TELD_W3D = r"Art\W3D\Irq_AlFahd500D.W3D"
PROJ_W3D = r"Art\W3D\Irq_AlFahd500M.W3D"
ORIG_W3D = r"Art\W3D\Irq_9P117.W3D"
ORIGD_W3D = r"Art\W3D\Irq_9P117D.W3D"
R11_W3D = r"Art\W3D\Irq_R11_M.W3D"
TRUCK_DDS = r"Art\Textures\Irq_9P117.dds"
TRUCKD_DDS = r"Art\Textures\Irq_9P117D.dds"

NEW_CB_KEY = r"Data\INI\CommandButton_JapanMissiles.ini"
NEW_CS_KEY = r"Data\INI\CommandSet_JapanMissiles.ini"
NEW_WEP_KEY = r"Data\INI\Weapon\Weapon_Japan_Missiles.ini"
NEW_FAC_KEY = (
    r"Data\INI\Object\Specter\Japan Self-Defense Forces"
    r"\Buildings\Japan_MissileFactory.ini"
)
TRUCK_TEX = "Jpn_TEL.tga"
TRUCKD_TEX = "Jpn_TELD.tga"
TRUCK_KEY = rf"Art\Textures\{TRUCK_TEX}"
TRUCKD_KEY = rf"Art\Textures\{TRUCKD_TEX}"

WEP_MARKER = (
    "; ===== Japan missiles A-G "
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
TYPE12_MIN_RANGE = 400.0  # 350 km -> AttackRange 602 < 800; smallest fireable fix

SHEET = 1024
TEL_BAND = (0.16, 0.30)
PROJ_BAND = (0.66, 0.80)
TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

OLIVE = (70, 83, 68)          # #465344
GRAPHITE = (41, 45, 44)       # #292D2C
VERMILION = (188, 58, 50)     # #BC3A32
METAL = (133, 137, 130)       # #858982
KHAKI = (90, 98, 62)
SLATE = (48, 62, 118)
SAGE = (150, 154, 140)
NAVY = (36, 42, 52)
IRON = (28, 30, 28)
NOSE_W = (236, 228, 210)
NOSE_R = (188, 58, 50)

MISSILES = [
    {
        "slot": "A",
        "object": "Japan_Type12Kai",
        "name": "Type 12 Kai",
        "model": "Jpn_Type12",
        "modeld": "Jpn_Type12D",
        "proj_model": "Jpn_Type12M",
        "hier": b"JPN_TYP12",
        "hierd": b"JPN_TYP12D",
        "proj_hier": b"JPN_MSL_A",
        "tex": "Jpn_Type12P.tga",
        "body": (62, 96, 48),
        "nose": NOSE_W,
        "expect": "olive",
        "km": 350,
        "kg": 250,
        "acc": 85,
        "stealth": 25,
        "rebuild": 15,
        "price": 800,
        "min_range": TYPE12_MIN_RANGE,
    },
    {
        "slot": "B",
        "object": "Japan_Type88Kai",
        "name": "Type 88 Kai",
        "model": "Jpn_Type88",
        "modeld": "Jpn_Type88D",
        "proj_model": "Jpn_Type88M",
        "hier": b"JPN_TYP88",
        "hierd": b"JPN_TYP88D",
        "proj_hier": b"JPN_MSL_B",
        "tex": "Jpn_Type88P.tga",
        "body": KHAKI,
        "nose": NOSE_R,
        "expect": "olive",
        "km": 550,
        "kg": 400,
        "acc": 70,
        "stealth": 35,
        "rebuild": 20,
        "price": 1200,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "C",
        "object": "Japan_Koryu",
        "name": "Kōryū",
        "model": "Jpn_Koryu",
        "modeld": "Jpn_KoryuD",
        "proj_model": "Jpn_KoryuM",
        "hier": b"JPN_KORYU",
        "hierd": b"JPN_KORYUD",
        "proj_hier": b"JPN_MSL_C",
        "tex": "Jpn_KoryuP.tga",
        "body": GRAPHITE,
        "nose": NOSE_R,
        "expect": "black",
        "km": 800,
        "kg": 600,
        "acc": 45,
        "stealth": 70,
        "rebuild": 28,
        "price": 1800,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "D",
        "object": "Japan_Raijin",
        "name": "Raijin",
        "model": "Jpn_Raijin",
        "modeld": "Jpn_RaijinD",
        "proj_model": "Jpn_RaijinM",
        "hier": b"JPN_RAIJN",
        "hierd": b"JPN_RAIJND",
        "proj_hier": b"JPN_MSL_D",
        "tex": "Jpn_RaijinP.tga",
        "body": SLATE,
        "nose": NOSE_W,
        "expect": "blue",
        "km": 1300,
        "kg": 1200,
        "acc": 35,
        "stealth": 45,
        "rebuild": 38,
        "price": 3000,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "E",
        "object": "Japan_Hayate",
        "name": "Hayate",
        "model": "Jpn_Hayate",
        "modeld": "Jpn_HayateD",
        "proj_model": "Jpn_HayateM",
        "hier": b"JPN_HAYAT",
        "hierd": b"JPN_HAYATD",
        "proj_hier": b"JPN_MSL_E",
        "tex": "Jpn_HayateP.tga",
        "body": SAGE,
        "nose": NOSE_R,
        "expect": "gray",
        "km": 1800,
        "kg": 800,
        "acc": 80,
        "stealth": 55,
        "rebuild": 42,
        "price": 3800,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "F",
        "object": "Japan_Yamato",
        "name": "Yamato",
        "model": "Jpn_Yamato",
        "modeld": "Jpn_YamatoD",
        "proj_model": "Jpn_YamatoM",
        "hier": b"JPN_YAMAT",
        "hierd": b"JPN_YAMATD",
        "proj_hier": b"JPN_MSL_F",
        "tex": "Jpn_YamatoP.tga",
        "body": NAVY,
        "nose": NOSE_W,
        "expect": "black",
        "km": 2500,
        "kg": 2500,
        "acc": 25,
        "stealth": 30,
        "rebuild": 65,
        "price": 6500,
        "min_range": MOTHER_MIN_RANGE,
    },
    {
        "slot": "G",
        "object": "Japan_Kurogane",
        "name": "Kurogane",
        "model": "Jpn_Kurogn",
        "modeld": "Jpn_KurognD",
        "proj_model": "Jpn_KurognM",
        "hier": b"JPN_KUROG",
        "hierd": b"JPN_KUROGD",
        "proj_hier": b"JPN_MSL_G",
        "tex": "Jpn_KurognP.tga",
        "body": IRON,
        "nose": NOSE_R,
        "expect": "black",
        "km": 3200,
        "kg": 3500,
        "acc": 15,
        "stealth": 20,
        "rebuild": 85,
        "price": 9000,
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
]

for _m in MISSILES:
    assert len(_m["hier"]) == 9, _m["hier"]
    assert len(_m["hierd"]) == 10, _m["hierd"]
    assert len(_m["proj_hier"]) == 9, _m["proj_hier"]
    assert len(_m["model"]) <= 15 and len(_m["modeld"]) <= 15 and len(_m["proj_model"]) <= 15
    assert _m["km"] <= 4000 and _m["kg"] <= 10000


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
    d["button"] = f"CB_JAPAN_MISSILE_{m['slot']}"
    d["cameo"] = f"specter_missile_{m['slot'].lower()}"
    d["unit_key"] = (
        r"Data\INI\Object\Specter\Japan Self-Defense Forces"
        rf"\Wheeled\{m['object']}.ini"
    )
    d["proj_key"] = (
        r"Data\INI\Object\Specter\Japan Self-Defense Forces"
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


def make_jp_flag() -> Image.Image:
    w, h = 450, 300
    im = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)
    r = int(h * 0.30)
    cx, cy = w // 2, h // 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(188, 0, 45, 255))
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
    """Map Iraqi tan sheet to Japanese olive / graphite / vermilion / metal."""
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
                base = OLIVE
                t = max(0.55, min(1.25, avg / 130.0))
            nr = min(255, int(base[0] * t))
            ng = min(255, int(base[1] * t))
            nb = min(255, int(base[2] * t))
            if damaged:
                nr, ng, nb = int(nr * 0.72), int(ng * 0.70), int(nb * 0.68)
            px[x, y] = (nr, ng, nb, a)
    draw = ImageDraw.Draw(im)
    verm = (*VERMILION, 255)
    # Top-down bed / roof (lower half of the 512 UV sheet) and a side-panel accent.
    draw.rectangle([28, 322, 484, 330], fill=verm)
    draw.rectangle([28, 402, 484, 410], fill=verm)
    draw.rectangle([198, 174, 502, 180], fill=verm)
    draw.rectangle([18, 248, 26, 292], fill=verm)
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
    if 50 <= g <= 150 and r < g + 12 and b < 80 and g > b + 10 and r < 120:
        return "olive"
    if g > r + 18 and g > b + 18 and g > 80:
        return "green"
    if r > 140 and g < 90 and b < 90:
        return "red"
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


def has_jp_flag(counts: dict[str, int]) -> bool:
    return counts.get("white", 0) >= 10 and counts.get("red", 0) >= 6


def has_name_plate(im: Image.Image, box: tuple[int, int, int, int]) -> bool:
    counts = region_mode(im, box)
    return counts.get("white", 0) + counts.get("black", 0) + counts.get("other", 0) >= 20


def unit_ini(m: dict) -> str:
    hier = m["hier"].decode()
    hierd = m["hierd"].decode()
    return f"""; Japan {m['object']} TEL. Functional clone of Iraq_R11ScudB / 9P117.
; Dedicated W3D {m['model']} / {m['modeld']} / {m['proj_model']}.
; Truck textures remapped to Jpn_TEL / Jpn_TELD (not Irq_9P117).
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
  Side = Japan
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
    return f"""; Japan {m['object']} projectile. Clone of ALHIJARAH_MRBM_Object.
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
        "; Type 12 Kai MinimumAttackRange = 400 because 350 km -> 602 < 800.\n"
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
    return """; Japan missile factory. Clone of Iraq_AlFahdMissileFactoryBuilding visuals
; and production modules, with a Japan-only CommandSet (A-G). Shared Sell-only
; Iraq_AlFahdMissileFactoryBuilding is unchanged for other isolated countries.

Object Japan_MissileFactory
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
  DisplayName      = OBJECT:JapanMissileFactory
  Side             = Japan
  EditorSorting    = STRUCTURE
  Prerequisites
    Object = Japan_SupplyCenter Iraq_SupplyCenter UkraineSupplyCenter TurkeySupplyCenter ItalySupplyCenter SwedenSupplyCenter BritainSupplyCenter FranceSupplyCenter GermanySupplyCenter NatoSupplyCenter ChinaSupplyCenter SouthKorea_SupplyCenter NorthKorea_SupplyCenter Vietnam_SupplyCenter India_SupplyCenter Pakistan_SupplyCenter SaudiArabia_SupplyCenter UAE_SupplyCenter Syria_SupplyCenter Libya_SupplyCenter SouthAfrica_SupplyCenter RussiaSupplyCenter
  End
  BuildCost        = 1800
  BuildTime        = 20.0
  EnergyProduction = -2
  CommandSet       = Japan_MissileFactoryCommandSet
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
        "; Japan missiles A-G production buttons and factory construct button.",
        "; Shared specter_missile_* cameos. Unique Object bindings. No Iraq/Vietnam CB edits.",
        "",
        "CommandButton Command_ConstructJapan_MissileFactory",
        "  Command          = DOZER_CONSTRUCT",
        "  Object           = Japan_MissileFactory",
        "  TextLabel        = CONTROLBAR:ConstructJapanMissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel    = CONTROLBAR:ToolTipJapanMissileFactory",
        "End",
        "",
    ]
    for m in missiles:
        lines.extend(
            [
                f"CommandButton {m['button']}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {m['object']}",
                f"  TextLabel     = CONTROLBAR:JapanMissile{m['slot']}",
                f"  ButtonImage   = {m['cameo']}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTipJapanMissile{m['slot']}",
                "End",
                "",
            ]
        )
    return "\n".join(lines)


def vt72b_commandset() -> str:
    return (
        "CommandSet Japan_VT72BCommandSet\r\n"
        "  1  = Command_ConstructJapan_PowerPlant\r\n"
        "  2  = Command_ConstructJapan_CommandCenter\r\n"
        "  3  = Command_ConstructJapan_SupplyCenter\r\n"
        "  4  = Command_ConstructJapan_WarFactory\r\n"
        "  5  = Command_ConstructJapan_LargeAirBase\r\n"
        "  6  = Command_ConstructJapan_MissileFactory\r\n"
        "  7  = Command_ConstructJapan_DefenseSite_SAFE\r\n"
        "  8  = Command_ConstructJapan_RadarStation\r\n"
        "  9  = Command_ConstructJapan_HeavyAirBase\r\n"
        "  10 = Command_ConstructJapan_Barracks_SAFE\r\n"
        "  11 = Command_ConstructJapan_NuclearCenter\r\n"
        "  12 = Command_ConstructJapan_D30_SAFE\r\n"
        "  13 = Command_ConstructJapan_CRAM\r\n"
        "  14 = Command_ConstructJapan_Hq9_Site\r\n"
        "  15 = Command_Stop\r\n"
        "End"
    )


def factory_commandset() -> str:
    slots = "\r\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(DERIVED, start=1))
    return (
        "CommandSet Japan_MissileFactoryCommandSet\r\n"
        f"{slots}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def commandset_ini() -> str:
    return vt72b_commandset() + "\r\n\r\n" + factory_commandset() + "\r\n"


def csf_map() -> dict[str, str]:
    mapping = {
        "OBJECT:JapanMissileFactory": "Missile Factory",
        "CONTROLBAR:ConstructJapanMissileFactory": "Missile Factory",
        "CONTROLBAR:ToolTipJapanMissileFactory": (
            "Missile Factory\nProduces Japanese missiles A-G\nPrice: $1800"
        ),
    }
    for m in DERIVED:
        mapping[f"OBJECT:{m['object']}"] = m["name"]
        mapping[f"CONTROLBAR:JapanMissile{m['slot']}"] = m["name"]
        mapping[f"CONTROLBAR:ToolTipJapanMissile{m['slot']}"] = m["tooltip"]
    return mapping


def write_loose() -> None:
    fac_dir = LOOSE / "Object/Specter/Japan Self-Defense Forces/Buildings"
    wheel_dir = LOOSE / "Object/Specter/Japan Self-Defense Forces/Wheeled"
    proj_dir = LOOSE / "Object/Specter/Japan Self-Defense Forces"
    wep_dir = LOOSE / "Weapon"
    fac_dir.mkdir(parents=True, exist_ok=True)
    wheel_dir.mkdir(parents=True, exist_ok=True)
    proj_dir.mkdir(parents=True, exist_ok=True)
    wep_dir.mkdir(parents=True, exist_ok=True)
    (fac_dir / "Japan_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    (wep_dir / "Weapon_Japan_Missiles.ini").write_text(weapon_blocks(DERIVED), encoding="utf-8")
    (LOOSE / "CommandButton_JapanMissiles.ini").write_text(commandbutton_ini(DERIVED), encoding="utf-8")
    (LOOSE / "CommandSet_JapanMissiles.ini").write_text(commandset_ini(), encoding="utf-8")
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
    for country in ("NorthKorea", "SouthKorea"):
        if last_block(cs_text, "CommandSet", f"{country}_VT72BCommandSet") != last_block(
            src_cs, "CommandSet", f"{country}_VT72BCommandSet"
        ):
            fails.append(f"{country} VT72B mutated")
        block = last_block(cs_text, "CommandSet", f"{country}_VT72BCommandSet")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in block:
            fails.append(f"{country} lost shared Sell-only factory")
        if "Command_ConstructJapan_MissileFactory" in block:
            fails.append(f"{country} gained Japan factory")

    jp_cs = last_block(cs_text, "CommandSet", "Japan_VT72BCommandSet")
    if "Command_ConstructJapan_MissileFactory" not in jp_cs:
        fails.append("CommandSet.ini Japan VT72B not Japan factory")
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in jp_cs:
        fails.append("CommandSet.ini Japan VT72B still Sell-only factory")

    fac_cs = last_block(cs_text, "CommandSet", "Japan_MissileFactoryCommandSet")
    if not fac_cs:
        fails.append("CommandSet.ini missing Japan_MissileFactoryCommandSet")
    for m in DERIVED:
        if m["button"] not in fac_cs:
            fails.append(f"factory missing {m['button']}")
    if "Command_Sell" not in fac_cs:
        fails.append("factory missing Sell")

    _k, lw_cs = last_block_from_files(order, data, "CommandSet", "Japan_VT72BCommandSet")
    if "Command_ConstructJapan_MissileFactory" not in lw_cs:
        fails.append(f"last-wins VT72B from {_k} not Japan factory")
    _k, lw_fac = last_block_from_files(order, data, "CommandSet", "Japan_MissileFactoryCommandSet")
    if not lw_fac:
        fails.append("last-wins missing Japan_MissileFactoryCommandSet")

    _k, fac_obj = last_block_from_files(order, data, "Object", "Japan_MissileFactory")
    if field(fac_obj, "CommandSet") != "Japan_MissileFactoryCommandSet":
        fails.append(f"factory object CommandSet {field(fac_obj, 'CommandSet')} from {_k}")
    if field(fac_obj, "Side") != "Japan":
        fails.append("factory Side")

    _k, construct = last_block_from_files(order, data, "CommandButton", "Command_ConstructJapan_MissileFactory")
    if field(construct, "Object") != "Japan_MissileFactory":
        fails.append(f"construct Object from {_k}")
    if field(construct, "Command") != "DOZER_CONSTRUCT":
        fails.append("construct Command")
    if field(construct, "ButtonImage") != "Button_MissileFactory":
        fails.append("construct image")
    if last_block(cb_text, "CommandButton", "Command_ConstructJapan_MissileFactory") == "":
        fails.append("CommandButton.ini missing construct button")

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

    if illegal_floats(wep_text):
        fails.append(f"illegal floats {illegal_floats(wep_text)}")
    if "ZZZZ" in NEW_CB_KEY or "ZZZZ" in NEW_CS_KEY:
        fails.append("ZZZZ shortcut")

    csf = data[CSF_KEY]
    truck = Image.open(io.BytesIO(art[TRUCK_KEY])).convert("RGB")
    truck_avg = truck.resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
    if not (truck_avg[1] >= truck_avg[0] and truck_avg[1] > truck_avg[2] + 4 and truck_avg[0] < 110):
        fails.append(f"truck not olive {truck_avg}")
    if classify(truck.getpixel((40, 326))) != "red" and classify(truck.getpixel((200, 326))) != "red":
        # vermilion stripe sample
        stripe = truck.getpixel((80, 326))
        if stripe[0] < 140 or stripe[1] > 90:
            fails.append(f"truck stripe not vermilion {stripe}")

    for m in DERIVED:
        unit = last_block(data[m["unit_key"]].decode("latin1"), "Object", m["object"])
        if field(unit, "BuildCost") != str(m["price"]):
            fails.append(f"{m['slot']} BuildCost")
        if not field(unit, "BuildTime").startswith(f"{m['rebuild']}.0"):
            fails.append(f"{m['slot']} BuildTime")
        if field(unit, "Side") != "Japan":
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
        if "JapanVehicleType12" in unit:
            fails.append(f"{m['slot']} collided with JapanVehicleType12")

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
        if csf_get(csf, f"CONTROLBAR:JapanMissile{m['slot']}") != m["name"]:
            fails.append(f"{m['slot']} CSF name")
        if csf_get(csf, f"CONTROLBAR:ToolTipJapanMissile{m['slot']}") != m["tooltip"]:
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
            "olive": {"olive", "green"},
            "black": {"black"},
            "blue": {"blue", "gray"},
            "gray": {"gray", "olive", "green", "white"},
        }
        if top_body not in allowed[m["expect"]]:
            fails.append(f"{m['slot']} body {top_body} {body}")
        tel_flag = region_mode(im, (110, 180, 420, 290))
        proj_flag = region_mode(im, (110, 690, 420, 800))
        if not has_jp_flag(tel_flag):
            fails.append(f"{m['slot']} TEL flag {tel_flag}")
        if not has_jp_flag(proj_flag):
            fails.append(f"{m['slot']} proj flag {proj_flag}")
        if not has_name_plate(im, (500, 190, 960, 280)):
            fails.append(f"{m['slot']} TEL name plate")
        if not has_name_plate(im, (500, 700, 960, 790)):
            fails.append(f"{m['slot']} proj name plate")

    vt72b = last_block(data[JPN_VT72B_KEY].decode("latin1"), "Object", "Japan_VT72B")
    if field(vt72b, "CommandSet") != "Japan_VT72BCommandSet":
        fails.append("Japan_VT72B CommandSet mutated")
    if field(vt72b, "Side") != "Japan":
        fails.append("Japan_VT72B Side")
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
        "  Type 12 Kai MinimumAttackRange = 400 (350 km -> AttackRange 602 < 800).",
        "  Other missiles keep MinimumAttackRange 800.",
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
    if sha256_path(SRC_DATA) != SHA_DATA_629 or SRC_DATA.stat().st_size != SIZE_DATA_629:
        raise SystemExit("DATA baseline is not PR #629 SPECTER_MISSILE_5MIN_CD_DMG")
    if sha256_path(SRC_ART) != SHA_ART_629 or SRC_ART.stat().st_size != SIZE_ART_629:
        raise SystemExit("ART baseline is not PR #629 SPECTER_MISSILE_5MIN_CD_DMG")

    src_data, _ = parse_big_ordered(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    flag = make_jp_flag()
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
    old_jp = last_block(cs, "CommandSet", "Japan_VT72BCommandSet")
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in old_jp:
        raise SystemExit("unexpected CommandSet.ini Japan_VT72BCommandSet")
    cs = replace_last(cs, "CommandSet", "Japan_VT72BCommandSet", vt72b_commandset())
    if last_block(cs, "CommandSet", "Japan_MissileFactoryCommandSet"):
        cs = replace_last(cs, "CommandSet", "Japan_MissileFactoryCommandSet", factory_commandset())
    else:
        cs = cs.rstrip("\r\n") + "\r\n\r\n" + factory_commandset() + "\r\n"
    data[CS_KEY] = cs.encode("latin1")

    cb = src_data[CB_KEY].decode("latin1")
    extra = commandbutton_ini(DERIVED).replace("\n", "\r\n")
    if "CommandButton Command_ConstructJapan_MissileFactory" in cb:
        raise SystemExit("CommandButton.ini already had Japan construct; inspect before splicing")
    data[CB_KEY] = (cb.rstrip("\r\n") + "\r\n\r\n" + extra).encode("latin1")

    wep = src_data[WEAPON_KEY].decode("latin1")
    if WEP_MARKER in wep:
        raise SystemExit("Weapon.ini already had Japan marker; inspect before splicing")
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
    (ext / "CommandSet.ini.Japan.txt").write_text(
        last_block(packed_data[CS_KEY].decode("latin1"), "CommandSet", "Japan_VT72BCommandSet")
        + "\r\n\r\n"
        + last_block(packed_data[CS_KEY].decode("latin1"), "CommandSet", "Japan_MissileFactoryCommandSet")
        + "\r\n",
        encoding="utf-8",
    )
    (ext / "Weapon.ini.Japan.txt").write_text(weapon_blocks(DERIVED), encoding="utf-8")
    (ext / "Japan_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    for m in DERIVED:
        (ext / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (ext / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    preview = OUT / "PREVIEW"
    preview.mkdir(parents=True)
    truck.save(preview / "Jpn_TEL.png")
    truckd.save(preview / "Jpn_TELD.png")
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
    zip_path = ROOT / "patch/Release/SPECTER_JAPAN_MISSILES_AG.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    inv = [
        "PRE-CHANGE JAPAN ROSTER (packed last-wins, PR #629):",
        "  FactionJapan StartingUnit0 = Japan_VT72B",
        "  Japan_VT72B CommandSet = Japan_VT72BCommandSet",
        "  Japan_VT72BCommandSet slot 6 = Command_ConstructIraq_AlFahdMissileFactoryBuilding (Sell-only)",
        "  Japan_MissileFactory: MISSING",
        "  Japan_WarFactory: USA vehicle roster (untouched)",
        "  JapanVehicleType12 / Japan_Hwasong5: existing unrelated units (untouched)",
        "",
        "POST-CHANGE JAPAN ROSTER:",
        "  Japan_VT72BCommandSet slot 6 = Command_ConstructJapan_MissileFactory",
        "  Japan_MissileFactory / Japan_MissileFactoryCommandSet = CB_JAPAN_MISSILE_A-G",
        "  Weapons last-wins in Data\\INI\\Weapon.ini",
        "  Buttons last-wins in Data\\INI\\CommandButton.ini",
        "  PRIMARY only + Scud_B_CommandSet / Command_FireMainWeapon",
        "  5-minute clip reload. No RadarPriority. No rearm.",
        "",
        *map_lines,
        "",
        "NEW / SPLICED DATA FILES:",
        f"  {CS_KEY} (Japan_VT72BCommandSet + Japan_MissileFactoryCommandSet)",
        f"  {CB_KEY} (construct + CB_JAPAN_MISSILE_A-G)",
        f"  {WEAPON_KEY} (Weapon_Japan_* + warheads)",
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
        "BASELINE: PR #629 s-missile-5min-cd-dmg",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "IRAQ_FACTORY_ROSTER_UNCHANGED=YES",
        "VIETNAM_AH_UNCHANGED=YES",
        "NINE_P117_UNCHANGED=YES",
        "KASHTAN_FALAQ_RETAINED=YES",
        "IRAQ_ABBAS_BIO_RETAINED=YES",
        "NO_REARM=YES",
        "NO_ZZZZ=YES",
        "NO_RADARPRIORITY=YES",
        "TYPE12_MINRANGE=400",
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
            "ZIP_FILE=SPECTER_JAPAN_MISSILES_AG.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #629",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-japan-missiles-ag/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-japan-missiles-ag/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-japan-missiles-ag/SPECTER_JAPAN_MISSILES_AG.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-japan-missiles-ag",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-japan-missiles-ag",
                "BASELINE=PR #629",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Japan missiles A-G cloned from the verified 9P117 / Al-Fahd / Vietnam path.\n"
        "Japan-only factory roster. Shared Sell-only factory, Iraq A-M, and Vietnam A-H unchanged.\n"
        "Olive-drab trucks, Hinomaru + exact names on dorsal UV bands.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Japan missiles A-G\n\n"
        "- Seven independently identifiable Japanese TELs cloned from 9P117 / Al-Fahd.\n"
        "- Dedicated W3D, Japanese olive truck textures, weapons, projectiles, buttons, factory CommandSet.\n"
        "- Japan dozer slot 6 constructs `Japan_MissileFactory` instead of the shared Sell-only building.\n"
        "- Top-facing Hinomaru + exact missile name on TEL and projectile dorsal UV bands.\n"
        "- Weapons spliced into Weapon.ini. Buttons/CommandSets spliced into live catalogs.\n"
        "- 5-minute clip reload. Damage scaled from 9P117 400 kg = 2000/100.\n"
        "- Type 12 Kai MinimumAttackRange lowered to 400 so 350 km (AttackRange 602) can fire.\n"
        "- 9P117, Iraq factory A-M, Vietnam A-H, Kashtan, Falaq, and Abbas Bio are unchanged.\n"
        "- No rearm. No ZZZZ overrides. No RadarPriority.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n", encoding="utf-8")
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet.ini last Japan_VT72BCommandSet is now the Japan factory construct.\n"
        "CommandSet_JapanMissiles.ini last-wins the same two CommandSets.\n"
        "CommandButton.ini now defines the construct + A-G buttons; satellite file matches.\n"
        "Weapon.ini last-wins Weapon_Japan_* (satellite Weapon\\Weapon_Japan_Missiles.ini is not the load path).\n"
        "Other country VT72B sets, Iraq factory, Vietnam factory, and 9P117 are unchanged.\n"
        "JapanVehicleType12 and Japan_Hwasong5 are untouched.\n"
        "Japan_WarFactory is untouched.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:60]))


if __name__ == "__main__":
    main()
