#!/usr/bin/env python3
"""Implement Vietnam missile roster A-H from the verified 9P117 / Al-Fahd clone.

Baseline: PR #625 SPECTER_ASIA4_CONSTRUCT_BTNS_FIX (accepted DATA+ART).

MOTHER (do not mutate):
  Object Iraq_R11ScudB in Data\\INI\\Object\\Specter\\Iraq Army\\Wheeled\\9P117.ini
  Weapon SRBM_ALHIJARAH_HE / projectile ALHIJARAH_MRBM_Object
  TEL Irq_9P117 / projectile Irq_R11_M

Clone donor (already isolated from 9P117, UV-remapped for dorsal markings):
  Irq_AlFahd500.W3D / Irq_AlFahd500D.W3D / Irq_AlFahd500M.W3D
  Truck textures stay Irq_9P117.tga; tube/projectile use dedicated Vnm_*P.tga.

Vietnam currently constructs Iraq_AlFahdMissileFactoryBuilding (Sell-only).
A Vietnam-only factory object is required so other isolated countries do not
inherit this roster. Iraq factory A-M and the shared Sell-only building stay
unchanged. No rearm. No ZZZZ files.
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
SRC_DATA = ROOT / "patch/Release/SPECTER_ASIA4_CONSTRUCT_BTNS_FIX/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_ASIA4_CONSTRUCT_BTNS_FIX/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_VIETNAM_MISSILES_AH"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_625 = "36b3dd0b05c8aa715183f454178b547d3dfb426c0035f88f65e5028180b2e5ab"
SIZE_DATA_625 = 366683401
SHA_ART_625 = "02376df9e1ba9dfe8069e368bf41ac71fa0de3a15bc7e7b72f98042a41248521"
SIZE_ART_625 = 1307095498

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

TEL_W3D = r"Art\W3D\Irq_AlFahd500.W3D"
TELD_W3D = r"Art\W3D\Irq_AlFahd500D.W3D"
PROJ_W3D = r"Art\W3D\Irq_AlFahd500M.W3D"
ORIG_W3D = r"Art\W3D\Irq_9P117.W3D"
ORIGD_W3D = r"Art\W3D\Irq_9P117D.W3D"
R11_W3D = r"Art\W3D\Irq_R11_M.W3D"

NEW_CB_KEY = r"Data\INI\CommandButton_VietnamMissiles.ini"
NEW_CS_KEY = r"Data\INI\CommandSet_VietnamMissiles.ini"
NEW_WEP_KEY = r"Data\INI\Weapon\Weapon_Vietnam_Missiles.ini"
NEW_FAC_KEY = (
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces"
    r"\Buildings\Vietnam_MissileFactory.ini"
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

SHEET = 1024
TEL_BAND = (0.16, 0.30)
PROJ_BAND = (0.66, 0.80)
TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

RED = (168, 32, 28)
YELLOW = (214, 178, 28)
OLIVE = (72, 112, 36)
BLUE = (28, 68, 168)
TEAL = (12, 78, 88)
BLACK = (22, 24, 26)
WHITE = (228, 224, 216)
ORANGE = (210, 108, 22)
NOSE_W = (236, 228, 210)
NOSE_R = (176, 36, 32)

MISSILES = [
    {
        "slot": "A",
        "object": "Vietnam_VCM01",
        "name": "VCM-01",
        "model": "Vnm_VCM01",
        "modeld": "Vnm_VCM01D",
        "proj_model": "Vnm_VCM01M",
        "hier": b"VNM_VCM01",
        "hierd": b"VNM_VCM01D",
        "proj_hier": b"VNM_MSL_A",
        "tex": "Vnm_VCM01P.tga",
        "body": RED,
        "nose": NOSE_W,
        "expect": "red",
        "km": 500,
        "kg": 1000,
        "acc": 10,
        "stealth": 5,
        "rebuild": 15,
        "price": 800,
    },
    {
        "slot": "B",
        "object": "Vietnam_VCM02",
        "name": "VCM-02",
        "model": "Vnm_VCM02",
        "modeld": "Vnm_VCM02D",
        "proj_model": "Vnm_VCM02M",
        "hier": b"VNM_VCM02",
        "hierd": b"VNM_VCM02D",
        "proj_hier": b"VNM_MSL_B",
        "tex": "Vnm_VCM02P.tga",
        "body": YELLOW,
        "nose": NOSE_R,
        "expect": "yellow",
        "km": 700,
        "kg": 250,
        "acc": 75,
        "stealth": 15,
        "rebuild": 20,
        "price": 1200,
    },
    {
        "slot": "C",
        "object": "Vietnam_SongHong",
        "name": "Sông Hồng",
        "model": "Vnm_SongH",
        "modeld": "Vnm_SongHD",
        "proj_model": "Vnm_SongHM",
        "hier": b"VNM_SONGH",
        "hierd": b"VNM_SONGHD",
        "proj_hier": b"VNM_MSL_C",
        "tex": "Vnm_SongHP.tga",
        "body": OLIVE,
        "nose": NOSE_R,
        "expect": "olive",
        "km": 800,
        "kg": 400,
        "acc": 25,
        "stealth": 80,
        "rebuild": 25,
        "price": 1600,
    },
    {
        "slot": "D",
        "object": "Vietnam_HongHa",
        "name": "Hồng Hà",
        "model": "Vnm_HongH",
        "modeld": "Vnm_HongHD",
        "proj_model": "Vnm_HongHM",
        "hier": b"VNM_HONGH",
        "hierd": b"VNM_HONGHD",
        "proj_hier": b"VNM_MSL_D",
        "tex": "Vnm_HongHP.tga",
        "body": BLUE,
        "nose": NOSE_W,
        "expect": "blue",
        "km": 900,
        "kg": 1800,
        "acc": 15,
        "stealth": 10,
        "rebuild": 30,
        "price": 2000,
    },
    {
        "slot": "E",
        "object": "Vietnam_CuuLong",
        "name": "Cửu Long",
        "model": "Vnm_CuuLg",
        "modeld": "Vnm_CuuLgD",
        "proj_model": "Vnm_CuuLgM",
        "hier": b"VNM_CUULG",
        "hierd": b"VNM_CUULGD",
        "proj_hier": b"VNM_MSL_E",
        "tex": "Vnm_CuuLgP.tga",
        "body": TEAL,
        "nose": NOSE_W,
        "expect": "teal",
        "km": 1000,
        "kg": 350,
        "acc": 55,
        "stealth": 45,
        "rebuild": 35,
        "price": 2500,
    },
    {
        "slot": "F",
        "object": "Vietnam_TruongSon",
        "name": "Trường Sơn",
        "model": "Vnm_TrSon",
        "modeld": "Vnm_TrSonD",
        "proj_model": "Vnm_TrSonM",
        "hier": b"VNM_TRSON",
        "hierd": b"VNM_TRSOND",
        "proj_hier": b"VNM_MSL_F",
        "tex": "Vnm_TrSonP.tga",
        "body": BLACK,
        "nose": NOSE_R,
        "expect": "black",
        "km": 1100,
        "kg": 600,
        "acc": 85,
        "stealth": 20,
        "rebuild": 40,
        "price": 3000,
    },
    {
        "slot": "G",
        "object": "Vietnam_BachDang",
        "name": "Bạch Đằng",
        "model": "Vnm_BachD",
        "modeld": "Vnm_BachDD",
        "proj_model": "Vnm_BachDM",
        "hier": b"VNM_BACHD",
        "hierd": b"VNM_BACHDD",
        "proj_hier": b"VNM_MSL_G",
        "tex": "Vnm_BachDP.tga",
        "body": WHITE,
        "nose": RED,
        "expect": "white",
        "km": 1300,
        "kg": 500,
        "acc": 30,
        "stealth": 90,
        "rebuild": 50,
        "price": 4000,
    },
    {
        "slot": "H",
        "object": "Vietnam_ThangLong",
        "name": "Thăng Long",
        "model": "Vnm_ThgLg",
        "modeld": "Vnm_ThgLgD",
        "proj_model": "Vnm_ThgLgM",
        "hier": b"VNM_THGLG",
        "hierd": b"VNM_THGLGD",
        "proj_hier": b"VNM_MSL_H",
        "tex": "Vnm_ThgLgP.tga",
        "body": ORANGE,
        "nose": NOSE_W,
        "expect": "orange",
        "km": 1500,
        "kg": 1200,
        "acc": 60,
        "stealth": 55,
        "rebuild": 60,
        "price": 5000,
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
    r"Art\Textures\Irq_9P117.dds",
    r"Art\Textures\Irq_9P117D.dds",
    r"Art\Textures\GENERIC-MISSILES.dds",
    r"Art\Textures\IraqiFlag.dds",
    r"Art\Textures\Irq_AlFahd500P.tga",
    r"Art\Textures\specter_missile_a.tga",
    r"Art\Textures\specter_missile_g.tga",
    r"Art\Textures\Button_MissileFactory.tga",
    r"Art\Textures\Button_kashtan.tga",
    r"Art\Textures\Button_falaq.tga",
]

FROZEN_DATA = [
    R11_KEY,
    FACTORY_KEY,
    BUILDING_KEY,
    UNIT_A_KEY,
    PROJ_A_KEY,
    WEP_A_KEY,
    WEAPON_KEY,
]

for _m in MISSILES:
    assert len(_m["hier"]) == 9, _m["hier"]
    assert len(_m["hierd"]) == 10, _m["hierd"]
    assert len(_m["proj_hier"]) == 9, _m["proj_hier"]
    assert len(_m["model"]) <= 15 and len(_m["modeld"]) <= 15 and len(_m["proj_model"]) <= 15


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
    d["button"] = f"CB_VIETNAM_MISSILE_{m['slot']}"
    d["cameo"] = f"specter_missile_{m['slot'].lower()}"
    d["unit_key"] = (
        r"Data\INI\Object\Specter\Vietnam People's Armed Forces"
        rf"\Wheeled\{m['object']}.ini"
    )
    d["proj_key"] = (
        r"Data\INI\Object\Specter\Vietnam People's Armed Forces"
        rf"\{m['object']}_Projectile.ini"
    )
    d["tex_key"] = rf"Art\Textures\{m['tex']}"
    d["tel_key"] = rf"Art\W3D\{m['model']}.W3D"
    d["teld_key"] = rf"Art\W3D\{m['modeld']}.W3D"
    d["projw_key"] = rf"Art\W3D\{m['proj_model']}.W3D"
    if m["stealth"] >= 60:
        d["radar"] = "NOT_ON_RADAR"
    elif m["stealth"] >= 20:
        d["radar"] = "LOCAL_UNIT_ONLY"
    else:
        d["radar"] = None
    d["tooltip"] = (
        f"{m['name']}\n"
        f"Range: {m['km']} km\n"
        f"Warhead: {m['kg']} kg\n"
        f"Point Accuracy: {m['acc']}/100\n"
        f"Radar Stealth: {m['stealth']}/100\n"
        f"Build Time: {m['rebuild']} sec\n"
        f"Price: ${m['price']}"
    )
    return d


DERIVED = [derived(m) for m in MISSILES]


def fmt_num(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.3f}".rstrip("0").rstrip(".")


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


def last_block(text: str, kind: str, name: str) -> str:
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text))
    return matches[-1].group(0) if matches else ""


def field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block or "", re.M)
    return m.group(1).strip() if m else ""


def last_wins_file(order: list[str], name: str) -> str | None:
    needle = name.lower()
    found = None
    for key in order:
        if key.replace("/", "\\").lower().endswith(needle) or key.replace("/", "\\").lower() == needle:
            found = key
        base = key.split("\\")[-1].lower()
        if base == needle:
            found = key
    return found


def last_commandset(blob: bytes, name: str) -> str:
    return last_block(blob.decode("latin1"), "CommandSet", name)


def last_button(blob: bytes, name: str) -> str:
    return last_block(blob.decode("latin1"), "CommandButton", name)


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
    blob = replace_textures(src, mapping)
    if damaged:
        blob = uniquify(blob, [(b"IRQ_AF500D", m["hierd"])])
        blob = patch_hlod_container(blob, m["modeld"])
    else:
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


def make_vn_flag() -> Image.Image:
    w, h = 450, 300
    im = Image.new("RGBA", (w, h), (218, 37, 29, 255))
    draw = ImageDraw.Draw(im)
    cx, cy = w / 2, h / 2
    outer = h * 0.32
    inner = outer * 0.382
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = outer if i % 2 == 0 else inner
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(pts, fill=(255, 205, 0, 255))
    return im


def paste_flag(im: Image.Image, flag: Image.Image, xy: tuple[int, int], size: tuple[int, int]) -> None:
    fw, fh = size
    flag_im = flag.convert("RGBA").resize((fw, fh), Image.Resampling.NEAREST)
    # White plate so the red flag stays readable on red/black/blue bodies.
    plate = Image.new("RGBA", (fw + 16, fh + 16), (248, 244, 232, 255))
    border = Image.new("RGBA", (fw + 16, fh + 16), (16, 14, 12, 255))
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
    if g > 50 and b > 50 and r < 55 and abs(g - b) < 28:
        return "teal"
    if 50 <= g <= 140 and r < g + 10 and b < 70 and g > b + 18 and r < 110:
        return "olive"
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


def has_vn_flag(counts: dict[str, int]) -> bool:
    return counts.get("red", 0) >= 10 and counts.get("yellow", 0) >= 6


def has_name_plate(im: Image.Image, box: tuple[int, int, int, int]) -> bool:
    counts = region_mode(im, box)
    return counts.get("white", 0) + counts.get("black", 0) + counts.get("other", 0) >= 20


def unit_ini(m: dict) -> str:
    hier = m["hier"].decode()
    hierd = m["hierd"].decode()
    return f"""; Vietnam {m['object']} TEL. Functional clone of Iraq_R11ScudB / 9P117.
; Dedicated W3D {m['model']} / {m['modeld']} / {m['proj_model']} so IRQ_9P117 / IRQ_R11_M stay frozen.
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
  Side = Vietnam
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
    radar = ""
    if m["radar"]:
        radar = (
            f"  ; SPECTER radar-stealth Kind for {m['stealth']}/100 "
            f"(MOTHER 5/100 has no RadarPriority).\n"
            f"  RadarPriority = {m['radar']}\n"
        )
    else:
        radar = (
            "  ; MOTHER-like: no RadarPriority, visible on enemy radar "
            f"({m['stealth']}/100).\n"
        )
    return f"""; Vietnam {m['object']} projectile. Clone of ALHIJARAH_MRBM_Object / Projectile_Iraq_AlFahd500.
; Dedicated W3D {m['proj_model']} + {m['tex']}. Donor 9P117 projectile is not modified.

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
{radar}  ArmorSet
    Conditions      = None
    Armor           = SRBMArmor
    DamageFX        = None
  End
  SoundAmbient  = GenericMissileAmbientLoop
  KindOf = PROJECTILE BALLISTIC_MISSILE
  Body = ActiveBody ModuleTag_02
    MaxHealth       = {fmt_num(m['hp'])}.0
    InitialHealth   = {fmt_num(m['hp'])}.0
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


def weapon_ini(missiles: list[dict]) -> str:
    chunks = [
        "; Vietnam missiles A-H. Separate file so Weapon.ini / SRBM_ALHIJARAH_HE / HE_9M729_450kg stay frozen.\n"
        "; Mapping from 9P117 MOTHER: 1000 km -> AttackRange 1720; 400 kg -> PrimaryDamage 2000 + death 2200;\n"
        "; accuracy 10/100 -> ScatterRadius 175. Properties are independent (not auto-chained).\n"
        "; MinimumAttackRange stays 800 (engine units). ClipReloadTime 95000 is fire cycle, not build time.\n"
    ]
    for m in missiles:
        chunks.append(
            f"""
Weapon {m['weapon']}
  PrimaryDamage               = {fmt_num(m['damage'])}.0
  PrimaryDamageRadius         = 80.0
  SecondaryDamage             = {fmt_num(m['secondary'])}.0
  SecondaryDamageRadius       = 10.0
  ScatterRadius               = {fmt_num(m['scatter'])}
  ScatterRadiusVsInfantry     = {fmt_num(m['inf_scatter'])}
  AttackRange                 = {fmt_num(m['range'])}.0
  MinimumAttackRange          = 800.0
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
  ClipReloadTime              = 95000
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
    return """; Vietnam missile factory. Clone of Iraq_AlFahdMissileFactoryBuilding visuals
; and production modules, with a Vietnam-only CommandSet (A-H). Shared Sell-only
; Iraq_AlFahdMissileFactoryBuilding is unchanged for other isolated countries.

Object Vietnam_MissileFactory
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
  DisplayName      = OBJECT:VietnamMissileFactory
  Side             = Vietnam
  EditorSorting    = STRUCTURE
  Prerequisites
    Object = Vietnam_SupplyCenter Iraq_SupplyCenter UkraineSupplyCenter TurkeySupplyCenter ItalySupplyCenter SwedenSupplyCenter BritainSupplyCenter FranceSupplyCenter GermanySupplyCenter NatoSupplyCenter ChinaSupplyCenter SouthKorea_SupplyCenter NorthKorea_SupplyCenter Japan_SupplyCenter India_SupplyCenter Pakistan_SupplyCenter SaudiArabia_SupplyCenter UAE_SupplyCenter Syria_SupplyCenter Libya_SupplyCenter SouthAfrica_SupplyCenter RussiaSupplyCenter
  End
  BuildCost        = 1800
  BuildTime        = 20.0
  EnergyProduction = -2
  CommandSet       = Vietnam_MissileFactoryCommandSet
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
        "; Vietnam missiles A-H production buttons and factory construct button.",
        "; Shared specter_missile_* cameos. Unique Object bindings. No Iraq CB_MISSILE_* edits.",
        "",
        "CommandButton Command_ConstructVietnam_MissileFactory",
        "  Command          = DOZER_CONSTRUCT",
        "  Object           = Vietnam_MissileFactory",
        "  TextLabel        = CONTROLBAR:ConstructVietnamMissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel    = CONTROLBAR:ToolTipVietnamMissileFactory",
        "End",
        "",
    ]
    for m in missiles:
        lines.extend(
            [
                f"CommandButton {m['button']}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {m['object']}",
                f"  TextLabel     = CONTROLBAR:VietnamMissile{m['slot']}",
                f"  ButtonImage   = {m['cameo']}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTipVietnamMissile{m['slot']}",
                "End",
                "",
            ]
        )
    return "\n".join(lines)


def commandset_ini() -> str:
    slots = "\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(DERIVED, start=1))
    return f"""CommandSet Vietnam_VT72BCommandSet
  1  = Command_ConstructVietnam_PowerPlant
  2  = Command_ConstructVietnam_CommandCenter
  3  = Command_ConstructVietnam_SupplyCenter
  4  = Command_ConstructVietnam_WarFactory
  5  = Command_ConstructVietnam_LargeAirBase
  6  = Command_ConstructVietnam_MissileFactory
  7  = Command_ConstructVietnam_DefenseSite_SAFE
  8  = Command_ConstructVietnam_RadarStation
  9  = Command_ConstructVietnam_HeavyAirBase
  10 = Command_ConstructVietnam_Barracks_SAFE
  11 = Command_ConstructVietnam_NuclearCenter
  12 = Command_ConstructVietnam_D30_SAFE
  13 = Command_ConstructVietnam_CRAM
  14 = Command_ConstructVietnam_Hq9_Site
  15 = Command_Stop
End

CommandSet Vietnam_MissileFactoryCommandSet
{slots}
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""


def csf_map() -> dict[str, str]:
    mapping = {
        "OBJECT:VietnamMissileFactory": "Missile Factory",
        "CONTROLBAR:ConstructVietnamMissileFactory": "Missile Factory",
        "CONTROLBAR:ToolTipVietnamMissileFactory": (
            "Missile Factory\nProduces Vietnamese missiles A-H\nPrice: $1800"
        ),
    }
    for m in DERIVED:
        mapping[f"OBJECT:{m['object']}"] = m["name"]
        mapping[f"CONTROLBAR:VietnamMissile{m['slot']}"] = m["name"]
        mapping[f"CONTROLBAR:ToolTipVietnamMissile{m['slot']}"] = m["tooltip"]
    return mapping


def write_loose() -> None:
    fac_dir = LOOSE / "Object/Specter/Vietnam People's Armed Forces/Buildings"
    wheel_dir = LOOSE / "Object/Specter/Vietnam People's Armed Forces/Wheeled"
    proj_dir = LOOSE / "Object/Specter/Vietnam People's Armed Forces"
    wep_dir = LOOSE / "Weapon"
    fac_dir.mkdir(parents=True, exist_ok=True)
    wheel_dir.mkdir(parents=True, exist_ok=True)
    proj_dir.mkdir(parents=True, exist_ok=True)
    wep_dir.mkdir(parents=True, exist_ok=True)
    (fac_dir / "Vietnam_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    (wep_dir / "Weapon_Vietnam_Missiles.ini").write_text(weapon_ini(DERIVED), encoding="utf-8")
    (LOOSE / "CommandButton_VietnamMissiles.ini").write_text(commandbutton_ini(DERIVED), encoding="utf-8")
    (LOOSE / "CommandSet_VietnamMissiles.ini").write_text(commandset_ini(), encoding="utf-8")
    for m in DERIVED:
        (wheel_dir / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (proj_dir / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")


def last_file_for_name(order: list[str], files: dict[str, bytes], needle: str) -> str | None:
    found = None
    low = needle.lower()
    for key in order:
        if files[key] and needle.encode("ascii") in files[key]:
            if key.lower().endswith(".ini") or key.lower().endswith(".csf"):
                found = key
    # prefer exact filename matches later
    for key in order:
        if key.split("\\")[-1].lower() == low:
            found = key
    return found


def validate(data: dict[str, bytes], art: dict[str, bytes], src_data: dict[str, bytes], src_art: dict[str, bytes], order: list[str]) -> list[str]:
    fails: list[str] = []
    for key in FROZEN_DATA:
        if data.get(key) != src_data.get(key):
            fails.append(f"frozen DATA mutated {key}")
    for key in FROZEN_ART:
        if art.get(key) != src_art.get(key):
            fails.append(f"frozen ART mutated {key}")

    cs_text = data[CS_KEY].decode("latin1")
    if last_block(cs_text, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet") != last_block(
        src_data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet"
    ):
        fails.append("Iraq factory roster mutated")
    if last_block(cs_text, "CommandSet", "Iraq_AlFahdMissileFactoryBuildingCommandSet") != last_block(
        src_data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlFahdMissileFactoryBuildingCommandSet"
    ):
        fails.append("Iraq Sell-only building CommandSet mutated")
    for country in ("NorthKorea", "SouthKorea", "Japan"):
        a = last_block(cs_text, "CommandSet", f"{country}_VT72BCommandSet")
        b = last_block(src_data[CS_KEY].decode("latin1"), "CommandSet", f"{country}_VT72BCommandSet")
        if a != b:
            fails.append(f"{country} VT72B CommandSet mutated")

    vn_cs = last_block(data[NEW_CS_KEY].decode("latin1"), "CommandSet", "Vietnam_VT72BCommandSet")
    if "Command_ConstructVietnam_MissileFactory" not in vn_cs:
        fails.append("Vietnam VT72B slot 6 not retargeted")
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in vn_cs:
        fails.append("Vietnam still constructs shared Sell-only factory")
    # last-wins: new file must sort after CommandSet.ini and before ZZZZ
    cs_names = [k for k in order if k.lower().endswith("commandset.ini") or "commandset_" in k.lower()]
    if NEW_CS_KEY not in order:
        fails.append("missing CommandSet_VietnamMissiles.ini")
    else:
        idx_cs = next(i for i, k in enumerate(order) if k.replace("/", "\\").lower() == CS_KEY.lower())
        idx_new = next(i for i, k in enumerate(order) if k.replace("/", "\\").lower() == NEW_CS_KEY.lower())
        if idx_new <= idx_cs:
            fails.append("Vietnam CommandSet does not last-wins over CommandSet.ini")

    fac = last_block(data[NEW_FAC_KEY].decode("latin1"), "Object", "Vietnam_MissileFactory")
    if field(fac, "CommandSet") != "Vietnam_MissileFactoryCommandSet":
        fails.append("factory CommandSet")
    if field(fac, "Side") != "Vietnam":
        fails.append("factory Side")

    fac_cs = last_block(data[NEW_CS_KEY].decode("latin1"), "CommandSet", "Vietnam_MissileFactoryCommandSet")
    for m in DERIVED:
        if m["button"] not in fac_cs:
            fails.append(f"factory missing {m['button']}")

    btn_text = data[NEW_CB_KEY].decode("latin1")
    src_btn = src_data[CB_KEY].decode("latin1")
    if src_data[CB_KEY] != data[CB_KEY]:
        fails.append("CommandButton.ini mutated")
    for ch in "ABCDEFGHIJKLM":
        if last_block(src_btn, "CommandButton", f"CB_MISSILE_{ch}") != last_block(
            src_btn, "CommandButton", f"CB_MISSILE_{ch}"
        ):
            fails.append(f"CB_MISSILE_{ch}")
    for img, btn in (
        ("Button_kashtan", "Command_ConstructRussiaKashtan"),
        ("Button_falaq", "Command_ConstructIranFalaqTrench"),
        ("Button_Bio", "Command_ConstructIraq_Abbas"),
    ):
        block = last_block(src_btn, "CommandButton", btn)
        if field(block, "ButtonImage") != img:
            fails.append(f"{btn} image lost")

    r11 = last_block(data[R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB")
    if field(r11, "BuildCost") != "1200":
        fails.append("9P117 BuildCost")
    if "specter_missile_g" not in r11:
        fails.append("9P117 portrait")
    if "Irq_9P117" not in r11:
        fails.append("9P117 model")

    wep = data[NEW_WEP_KEY].decode("latin1")
    src_wep = src_data[WEAPON_KEY].decode("latin1")
    if last_block(src_wep, "Weapon", "SRBM_ALHIJARAH_HE") != last_block(
        data[WEAPON_KEY].decode("latin1"), "Weapon", "SRBM_ALHIJARAH_HE"
    ):
        fails.append("MOTHER weapon mutated")
    if last_block(src_wep, "Weapon", "HE_9M729_450kg") != last_block(
        data[WEAPON_KEY].decode("latin1"), "Weapon", "HE_9M729_450kg"
    ):
        fails.append("MOTHER warhead mutated")

    csf = data[CSF_KEY]
    for m in DERIVED:
        unit = last_block(data[m["unit_key"]].decode("latin1"), "Object", m["object"])
        if field(unit, "BuildCost") != str(m["price"]):
            fails.append(f"{m['slot']} BuildCost")
        if not field(unit, "BuildTime").startswith(f"{m['rebuild']}.0"):
            fails.append(f"{m['slot']} BuildTime")
        if field(unit, "Side") != "Vietnam":
            fails.append(f"{m['slot']} Side")
        if field(unit, "ButtonImage") != m["cameo"]:
            fails.append(f"{m['slot']} cameo")
        if f"Model                           = {m['model']}" not in unit:
            fails.append(f"{m['slot']} TEL model")
        hier = m["hier"].decode()
        if f"{hier}.{hier}" not in unit:
            fails.append(f"{m['slot']} animation")
        if m["weapon"] not in unit:
            fails.append(f"{m['slot']} weapon bind")
        if "Rearm" in unit or "Contain" in unit:
            fails.append(f"{m['slot']} unexpected rearm/contain")
        proj = last_block(data[m["proj_key"]].decode("latin1"), "Object", m["projectile"])
        if f"Model = {m['proj_model']}" not in proj:
            fails.append(f"{m['slot']} flying model")
        if field(proj, "MaxHealth") != f"{fmt_num(m['hp'])}.0":
            fails.append(f"{m['slot']} HP {field(proj, 'MaxHealth')}")
        if m["radar"]:
            if field(proj, "RadarPriority") != m["radar"]:
                fails.append(f"{m['slot']} radar {field(proj, 'RadarPriority')}")
        elif field(proj, "RadarPriority"):
            fails.append(f"{m['slot']} unexpected RadarPriority")
        wblock = last_block(wep, "Weapon", m["weapon"])
        if field(wblock, "AttackRange") != f"{fmt_num(m['range'])}.0":
            fails.append(f"{m['slot']} range {field(wblock, 'AttackRange')}")
        if field(wblock, "PrimaryDamage") != f"{fmt_num(m['damage'])}.0":
            fails.append(f"{m['slot']} damage")
        if field(wblock, "ScatterRadius") != fmt_num(m["scatter"]):
            fails.append(f"{m['slot']} scatter {field(wblock, 'ScatterRadius')}")
        if field(wblock, "ProjectileObject") != m["projectile"]:
            fails.append(f"{m['slot']} projectile bind")
        if field(wblock, "MinimumAttackRange") != "800.0":
            fails.append(f"{m['slot']} min range scaled")
        death = last_block(wep, "Weapon", m["warhead"])
        if field(death, "PrimaryDamage") != str(m["death"]):
            fails.append(f"{m['slot']} death {field(death, 'PrimaryDamage')}")
        bblock = last_block(btn_text, "CommandButton", m["button"])
        if field(bblock, "Object") != m["object"]:
            fails.append(f"{m['slot']} button object")
        if field(bblock, "ButtonImage") != m["cameo"]:
            fails.append(f"{m['slot']} button image")
        if csf_get(csf, f"CONTROLBAR:VietnamMissile{m['slot']}") != m["name"]:
            fails.append(f"{m['slot']} CSF name")
        if csf_get(csf, f"CONTROLBAR:ToolTipVietnamMissile{m['slot']}") != m["tooltip"]:
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
        if m["tex"] not in tel_tex or "Irq_9P117.tga" not in tel_tex:
            fails.append(f"{m['slot']} TEL tex {tel_tex}")
        if m["tex"] not in teld_tex or "Irq_9P117D.tga" not in teld_tex:
            fails.append(f"{m['slot']} TELD tex {teld_tex}")
        if proj_tex != {m["tex"]}:
            fails.append(f"{m['slot']} proj tex {proj_tex}")

        im = Image.open(io.BytesIO(art[m["tex_key"]])).convert("RGB")
        if im.size != (SHEET, SHEET):
            fails.append(f"{m['slot']} skin size {im.size}")
        body = region_mode(im, (80, 410, 200, 560))
        top_body = max(body, key=body.get)
        allowed = {
            "red": {"red"},
            "yellow": {"yellow", "orange"},
            "olive": {"olive", "green"},
            "blue": {"blue"},
            "teal": {"teal", "blue"},
            "black": {"black"},
            "white": {"white"},
            "orange": {"orange", "yellow"},
        }
        if top_body not in allowed[m["expect"]]:
            fails.append(f"{m['slot']} body {top_body} {body}")
        tel_flag = region_mode(im, (110, 180, 420, 290))
        proj_flag = region_mode(im, (110, 690, 420, 800))
        if not has_vn_flag(tel_flag):
            fails.append(f"{m['slot']} TEL flag {tel_flag}")
        if not has_vn_flag(proj_flag):
            fails.append(f"{m['slot']} proj flag {proj_flag}")
        if not has_name_plate(im, (500, 190, 960, 280)):
            fails.append(f"{m['slot']} TEL name plate")
        if not has_name_plate(im, (500, 700, 960, 790)):
            fails.append(f"{m['slot']} proj name plate")

    # Isolation: other countries still construct the Sell-only building.
    for country in ("NorthKorea", "SouthKorea", "Japan"):
        block = last_block(cs_text, "CommandSet", f"{country}_VT72BCommandSet")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in block:
            fails.append(f"{country} lost shared factory construct")
        if "Command_ConstructVietnam_MissileFactory" in block:
            fails.append(f"{country} gained Vietnam factory")

    if "ZZZZ" in NEW_CB_KEY or "ZZZZ" in NEW_CS_KEY:
        fails.append("ZZZZ shortcut")
    return fails


def mapping_report() -> list[str]:
    lines = [
        "GAMEPLAY MAPPING (9P117 MOTHER scale, properties independent):",
        "  AttackRange 1720 = 1000 km design. Formula: 1720 * (km / 1000).",
        "  PrimaryDamage 2000 = 400 kg design. Formula: 2000 * (kg / 400).",
        "  Death warhead 2200 = 400 kg extra. Formula: 2200 * (kg / 400).",
        "  ScatterRadius 175 = 10/100 accuracy. Formula: 175 * (10 / acc).",
        "    Limitation: ScatterRadius is impact dispersion, not a 0-100 hit chance.",
        "  Projectile MaxHealth 400 = 5/100 stealth. Formula: 400 * (stealth / 5).",
        "  RadarPriority: <20 none (on radar); >=20 LOCAL_UNIT_ONLY; >=60 NOT_ON_RADAR.",
        "    Limitation: not a true intercept-probability percentage.",
        "  MinimumAttackRange kept at 800 engine units (not scaled).",
        "  BuildCost / BuildTime set on the unit Object (factory production).",
        "  Optional researched Vietnam production upgrades can still multiply cost/time.",
        "",
        "SLOT  NAME            KM   KG   ACC STL TIME COST  RANGE  DMG    DEATH SCATTER  HP     RADAR",
    ]
    for m in DERIVED:
        radar = m["radar"] or "on-radar"
        lines.append(
            f"  {m['slot']}    {m['name']:<14} {m['km']:<4} {m['kg']:<4} "
            f"{m['acc']:<3} {m['stealth']:<3} {m['rebuild']:<4} {m['price']:<5} "
            f"{fmt_num(m['range']):<6} {fmt_num(m['damage']):<6} {m['death']:<5} "
            f"{fmt_num(m['scatter']):<7} {fmt_num(m['hp']):<6} {radar}"
        )
    return lines


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_625 or SRC_DATA.stat().st_size != SIZE_DATA_625:
        raise SystemExit("DATA baseline is not PR #625 SPECTER_ASIA4_CONSTRUCT_BTNS_FIX")
    if sha256_path(SRC_ART) != SHA_ART_625 or SRC_ART.stat().st_size != SIZE_ART_625:
        raise SystemExit("ART baseline is not PR #625 SPECTER_ASIA4_CONSTRUCT_BTNS_FIX")

    src_data, _ = parse_big_ordered(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    flag = make_vn_flag()
    for m in DERIVED:
        skin = make_skin(m["body"], m["nose"], m["name"], flag)
        art[m["tex_key"]] = make_tga32(skin)
        art[m["tel_key"]] = make_tel_w3d(src_art[TEL_W3D], False, m)
        art[m["teld_key"]] = make_tel_w3d(src_art[TELD_W3D], True, m)
        art[m["projw_key"]] = make_proj_w3d(src_art[PROJ_W3D], m)
        data[m["unit_key"]] = to_crlf(unit_ini(m))
        data[m["proj_key"]] = to_crlf(projectile_ini(m))

    data[NEW_FAC_KEY] = to_crlf(factory_ini())
    data[NEW_WEP_KEY] = to_crlf(weapon_ini(DERIVED))
    data[NEW_CB_KEY] = to_crlf(commandbutton_ini(DERIVED))
    data[NEW_CS_KEY] = to_crlf(commandset_ini())
    data[CSF_KEY] = csf_upsert(src_data[CSF_KEY], csf_map())
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
    (ext / "CommandSet_VietnamMissiles.ini").write_text(commandset_ini(), encoding="utf-8")
    (ext / "CommandButton_VietnamMissiles.ini").write_text(commandbutton_ini(DERIVED), encoding="utf-8")
    (ext / "Weapon_Vietnam_Missiles.ini").write_text(weapon_ini(DERIVED), encoding="utf-8")
    (ext / "Vietnam_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    for m in DERIVED:
        (ext / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (ext / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")

    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_VIETNAM_MISSILES_AH.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    inv = [
        "Vietnam missiles A-H last-wins (static).",
        "Factory: Vietnam_MissileFactory / Vietnam_MissileFactoryCommandSet.",
        "Vietnam_VT72BCommandSet slot 6 = Command_ConstructVietnam_MissileFactory.",
        "Other isolated countries still construct Iraq_AlFahdMissileFactoryBuilding (Sell-only).",
        "Iraq factory A-M, 9P117, Kashtan, Falaq, Abbas Bio unchanged.",
        "",
        *map_lines,
        "",
        "NEW DATA FILES:",
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
    for m in DERIVED:
        inv.append(f"  {m['tel_key']} / {m['teld_key']} / {m['projw_key']} / {m['tex_key']}")

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #625 s-asia4-construct-btns-fix",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "IRAQ_FACTORY_ROSTER_UNCHANGED=YES",
        "NINE_P117_UNCHANGED=YES",
        "KASHTAN_FALAQ_RETAINED=YES",
        "IRAQ_ABBAS_BIO_RETAINED=YES",
        "NO_REARM=YES",
        "NO_ZZZZ=YES",
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
            "ZIP_FILE=SPECTER_VIETNAM_MISSILES_AH.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #625",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-vietnam-missiles-ah/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-vietnam-missiles-ah/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-vietnam-missiles-ah/SPECTER_VIETNAM_MISSILES_AH.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-vietnam-missiles-ah",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-vietnam-missiles-ah",
                "BASELINE=PR #625",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Vietnam missiles A-H cloned from the verified 9P117 / Al-Fahd implementation.\n"
        "Vietnam-only factory roster. Shared Sell-only factory and Iraq A-M unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Vietnam missiles A-H\n\n"
        "- Eight independently identifiable Vietnamese TELs cloned from 9P117 / Al-Fahd.\n"
        "- Dedicated W3D, textures, weapons, projectiles, buttons, and factory CommandSet.\n"
        "- Vietnam dozer slot 6 constructs `Vietnam_MissileFactory` instead of the shared Sell-only building.\n"
        "- Top-facing Vietnamese flag + exact name on TEL and projectile dorsal UV bands.\n"
        "- 9P117, Iraq factory A-M, Kashtan, Falaq, and Abbas Bio are unchanged.\n"
        "- No rearm. No ZZZZ overrides.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n", encoding="utf-8")
    print("PACKED")
    print(hashes)
    print("\n".join(report[:50]))


if __name__ == "__main__":
    main()
