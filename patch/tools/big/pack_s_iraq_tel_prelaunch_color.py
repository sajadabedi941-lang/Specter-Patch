#!/usr/bin/env python3
"""Restore 9P117 TEL color and per-missile pre-launch skins for B/C/D/H/I/J.

Baseline:
  DATA = PR #591 SPECTER_IRAQ_ALHUSSAIEN_ICBM_30S_FIRE/_SPEC_DATA_ONE.big
  ART  = PR #574 SPECTER_IRAQ_MISSILE_SKINS_BCDHIJ/_SPEC_ART_ONE.big

Root cause:
  1. Factory TELs A-J all used Irq_AlFahd500.W3D. Pre-launch missile is mesh
     MISSILE01, textured Irq_AlFahd500P.tga, so B-J looked like A until the
     dedicated projectile W3D spawned after fire.
  2. Vehicle meshes on that TEL used Irq_AlFahd500.tga, a blackened clone of
     Irq_9P117 (avg RGB 21 vs original dds 122/102/75).

Fix (visual only):
  A: remap TEL vehicle textures to original Irq_9P117.tga / Irq_9P117D.tga.
     Keep MISSILE01 = Irq_AlFahd500P.tga. Keep INI Model/Animation.
  B-J: clone the (already UV-remapped) Al-Fahd TEL W3Ds, vehicle tex = 9P117,
     MISSILE01 = that missile's existing projectile P.tga, unique hierarchy
     so they cannot overwrite A or 9P117. Point INI Model/Animation at clones.
  Projectile W3Ds, 9P117 assets, weapons, stealth, costs: unchanged.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ALHUSSAIEN_ICBM_30S_FIRE/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_SKINS_BCDHIJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_TEL_PRELAUNCH_COLOR"
WHEELED = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled"

BASE_DATA_SHA = "a7b8e569c96244014733b1447226e1a8fda5a8065934d794f61a72da55608b24"
BASE_DATA_SIZE = 366514886
BASE_ART_SHA = "e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4"
BASE_ART_SIZE = 1292294758

TEX_CHUNK = 0x00000032
MESH_HEADER = 0x0000001F
HLOD_HEADER = 0x00000701

TEL_W3D = r"Art\W3D\Irq_AlFahd500.W3D"
TELD_W3D = r"Art\W3D\Irq_AlFahd500D.W3D"
ORIG_W3D = r"Art\W3D\Irq_9P117.W3D"
ORIGD_W3D = r"Art\W3D\Irq_9P117D.W3D"
ORIG_TEX = r"Art\Textures\Irq_9P117.dds"
ORIGD_TEX = r"Art\Textures\Irq_9P117D.dds"
PROJ_A_W3D = r"Art\W3D\Irq_AlFahd500M.W3D"
PROJ_A_TEX = r"Art\Textures\Irq_AlFahd500P.tga"

UNIT_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
PROJ_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
UNLOCK_KEY = r"Data\INI\Object\Specter\EU5Unlock\Specter_EU5WFUnlock.ini"
LAUNCHER_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini"

VARIANTS = [
    {
        "slot": "B",
        "object": "Iraq_AlHusseinII",
        "ini": "Iraq_AlHusseinII.ini",
        "model": "Irq_AlHussein2",
        "modeld": "Irq_AlHussein2D",
        "hier": b"IRQ_AH2_T",
        "hierd": b"IRQ_AH2_TD",
        "proj_model": "Irq_AlHussein2M",
        "proj_tex": "Irq_AlHussein2P.tga",
        "proj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlHusseinII_Projectile.ini",
        "weapon": "Weapon_Iraq_AlHusseinII",
    },
    {
        "slot": "C",
        "object": "Iraq_AlSamoudII",
        "ini": "Iraq_AlSamoudII.ini",
        "model": "Irq_AlSamoud2T",
        "modeld": "Irq_AlSamoud2TD",
        "hier": b"IRQ_AS2_T",
        "hierd": b"IRQ_AS2_TD",
        "proj_model": "Irq_AlSamoud2M",
        "proj_tex": "Irq_AlSamoud2P.tga",
        "proj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlSamoudII_Projectile.ini",
        "weapon": "Weapon_Iraq_AlSamoudII",
    },
    {
        "slot": "D",
        "object": "Iraq_AlAbbas",
        "ini": "Iraq_AlAbbas.ini",
        "model": "Irq_AlAbbas2TL",
        "modeld": "Irq_AlAbbas2TLD",
        "hier": b"IRQ_AAB_T",
        "hierd": b"IRQ_AAB_TD",
        "proj_model": "Irq_AlAbbas2M",
        "proj_tex": "Irq_AlAbbas2P.tga",
        "proj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlAbbas_Projectile.ini",
        "weapon": "Weapon_Iraq_AlAbbas",
    },
    {
        "slot": "H",
        "object": "Iraq_AlBasrah",
        "ini": "Iraq_AlBasrah.ini",
        "model": "Irq_AlBasrahTL",
        "modeld": "Irq_AlBasrahTLD",
        "hier": b"IRQ_ABS_T",
        "hierd": b"IRQ_ABS_TD",
        "proj_model": "Irq_AlBasrahM",
        "proj_tex": "Irq_AlBasrahP.tga",
        "proj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlBasrah_Projectile.ini",
        "weapon": "Weapon_Iraq_AlBasrah",
    },
    {
        "slot": "I",
        "object": "Iraq_AlNasir",
        "ini": "Iraq_AlNasir.ini",
        "model": "Irq_AlNasirTEL",
        "modeld": "Irq_AlNasirTELD",
        "hier": b"IRQ_ANS_T",
        "hierd": b"IRQ_ANS_TD",
        "proj_model": "Irq_AlNasirM",
        "proj_tex": "Irq_AlNasirP.tga",
        "proj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlNasir_Projectile.ini",
        "weapon": "Weapon_Iraq_AlNasir",
    },
    {
        "slot": "J",
        "object": "Iraq_AlMansour",
        "ini": "Iraq_AlMansour.ini",
        "model": "Irq_AlMansourT",
        "modeld": "Irq_AlMansourTD",
        "hier": b"IRQ_AMN_T",
        "hierd": b"IRQ_AMN_TD",
        "proj_model": "Irq_AlMansourM",
        "proj_tex": "Irq_AlMansourP.tga",
        "proj_key": r"Data\INI\Object\Specter\Iraq Army\Iraq_AlMansour_Projectile.ini",
        "weapon": "Weapon_Iraq_AlMansour",
    },
]

FROZEN_ART = [
    ORIG_W3D,
    ORIGD_W3D,
    r"Art\W3D\Irq_9P117R.W3D",
    r"Art\W3D\Irq_R11_M.W3D",
    PROJ_A_W3D,
    ORIG_TEX,
    ORIGD_TEX,
    r"Art\Textures\Irq_9P117R.dds",
    PROJ_A_TEX,
    r"Art\Textures\GENERIC-MISSILES.dds",
]
for m in VARIANTS:
    FROZEN_ART.append(rf"Art\W3D\{m['proj_model']}.W3D")
    FROZEN_ART.append(rf"Art\Textures\{m['proj_tex']}")


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


def zstr(buf: bytes) -> str:
    return buf.split(b"\x00", 1)[0].decode("latin1", errors="replace")


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def first_object(text: str, name: str) -> str:
    m = re.search(rf"(?ms)^Object {re.escape(name)}\r?\n.*?(?=^Object |\Z)", text)
    return m.group(0) if m else ""


def field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block or "", re.M)
    return m.group(1).strip() if m else ""


def last_block(text: str, kind: str, name: str) -> str:
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text))
    return matches[-1].group(0) if matches else ""


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
    if damaged:
        mapping = {
            "Irq_AlFahd500D.tga": "Irq_9P117D.tga",
            "Irq_AlFahd500P.tga": m["proj_tex"],
        }
        blob = replace_textures(src, mapping)
        blob = uniquify(blob, [(b"IRQ_AF500D", m["hierd"])])
        blob = patch_hlod_container(blob, m["modeld"])
    else:
        mapping = {
            "Irq_AlFahd500.tga": "Irq_9P117.tga",
            "Irq_AlFahd500P.tga": m["proj_tex"],
        }
        blob = replace_textures(src, mapping)
        blob = uniquify(blob, [(b"IRQ_AF500", m["hier"])])
        blob = patch_hlod_container(blob, m["model"])
    return blob


def restore_a_vehicle(src: bytes, damaged: bool) -> bytes:
    if damaged:
        return replace_textures(src, {"Irq_AlFahd500D.tga": "Irq_9P117D.tga"})
    return replace_textures(src, {"Irq_AlFahd500.tga": "Irq_9P117.tga"})


def unit_key(name: str) -> str:
    return rf"Data\INI\Object\Specter\Iraq Army\Wheeled\{name}"


def validate_data(extracted: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    if extracted[UNIT_A_KEY] != src[UNIT_A_KEY]:
        fails.append("Missile A INI mutated")
    if extracted[PROJ_A_KEY] != src[PROJ_A_KEY]:
        fails.append("Missile A projectile INI mutated")
    if extracted[R11_KEY] != src[R11_KEY]:
        fails.append("9P117 mutated")
    if extracted[FACTORY_KEY] != src[FACTORY_KEY]:
        fails.append("factory mutated")
    if extracted[WEAPON_KEY] != src[WEAPON_KEY]:
        fails.append("Weapon.ini mutated")
    if extracted[UNLOCK_KEY] != src[UNLOCK_KEY]:
        fails.append("EU5 unlock mutated")
    if extracted[LAUNCHER_KEY] != src[LAUNCHER_KEY]:
        fails.append("AbbasLauncher mutated")
    a = first_object(extracted[UNIT_A_KEY].decode("latin1"), "Iraq_AlFahd500")
    if field(a, "BuildCost") != "2200" or not field(a, "BuildTime").startswith("30.0"):
        fails.append("Missile A cost/time")
    if "Model                           = Irq_AlFahd500" not in a:
        fails.append("Missile A TEL model")
    if "IRQ_AF500.IRQ_AF500" not in a:
        fails.append("Missile A animation")
    weap = extracted[WEAPON_KEY].decode("latin1")
    src_weap = src[WEAPON_KEY].decode("latin1")
    for m in VARIANTS:
        if last_block(weap, "Weapon", m["weapon"]) != last_block(src_weap, "Weapon", m["weapon"]):
            fails.append(f"{m['weapon']} mutated")
        if extracted[m["proj_key"]] != src[m["proj_key"]]:
            fails.append(f"{m['slot']} projectile INI mutated")
        unit = extracted[unit_key(m["ini"])].decode("latin1")
        src_unit = src[unit_key(m["ini"])].decode("latin1")
        obj = first_object(unit, m["object"])
        src_obj = first_object(src_unit, m["object"])
        if field(obj, "BuildCost") != field(src_obj, "BuildCost"):
            fails.append(f"{m['slot']} BuildCost changed")
        if field(obj, "BuildTime") != field(src_obj, "BuildTime"):
            fails.append(f"{m['slot']} BuildTime changed")
        if f"Model                           = {m['model']}" not in obj:
            fails.append(f"{m['slot']} missing TEL model {m['model']}")
        if f"Animation       = {m['hier'].decode()}.{m['hier'].decode()}" not in obj:
            fails.append(f"{m['slot']} missing animation")
        if "Irq_AlFahd500" in obj.split("Donor", 1)[0] and "Model                           = Irq_AlFahd500" in obj:
            fails.append(f"{m['slot']} still uses AlFahd TEL model")
        proj = first_object(extracted[m["proj_key"]].decode("latin1"), f"Projectile_{m['object']}")
        if f"Model = {m['proj_model']}" not in proj:
            fails.append(f"{m['slot']} flying model lost")
        if field(proj, "RadarPriority") != field(
            first_object(src[m["proj_key"]].decode("latin1"), f"Projectile_{m['object']}"),
            "RadarPriority",
        ):
            fails.append(f"{m['slot']} RadarPriority changed")
        if field(proj, "MaxHealth") != field(
            first_object(src[m["proj_key"]].decode("latin1"), f"Projectile_{m['object']}"),
            "MaxHealth",
        ):
            fails.append(f"{m['slot']} MaxHealth changed")
    return fails


def validate_art(art: dict[str, bytes], src_art: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    for key in FROZEN_ART:
        if art.get(key) != src_art.get(key):
            fails.append(f"frozen ART mutated {key}")
    a_tex = mesh_tex(art[TEL_W3D])
    if a_tex.get("MISSILE01") != {"Irq_AlFahd500P.tga"}:
        fails.append(f"A pre-launch missile tex {a_tex.get('MISSILE01')}")
    vehicle = set()
    for mesh, names in a_tex.items():
        if mesh != "MISSILE01":
            vehicle |= names
    if vehicle != {"Irq_9P117.tga"}:
        fails.append(f"A vehicle tex {vehicle}")
    ad_tex = mesh_tex(art[TELD_W3D])
    if ad_tex.get("MISSILE01") != {"Irq_AlFahd500P.tga"}:
        fails.append(f"A damaged missile tex {ad_tex.get('MISSILE01')}")
    dvehicle = set()
    for mesh, names in ad_tex.items():
        if mesh != "MISSILE01":
            dvehicle |= names
    if dvehicle != {"Irq_9P117D.tga"}:
        fails.append(f"A damaged vehicle tex {dvehicle}")
    if b"IRQ_AF500" not in art[TEL_W3D] or b"IRQ_9P117" in art[TEL_W3D]:
        fails.append("A hierarchy identity")
    orig = mesh_tex(art[ORIG_W3D])
    if orig.get("MISSILE01") != {"GENERIC-MISSILES.dds"}:
        fails.append("9P117 missile tex mutated")
    for m in VARIANTS:
        tel = art[rf"Art\W3D\{m['model']}.W3D"]
        teld = art[rf"Art\W3D\{m['modeld']}.W3D"]
        mt = mesh_tex(tel)
        md = mesh_tex(teld)
        if mt.get("MISSILE01") != {m["proj_tex"]}:
            fails.append(f"{m['slot']} TEL missile tex {mt.get('MISSILE01')}")
        veh = set()
        for mesh, names in mt.items():
            if mesh != "MISSILE01":
                veh |= names
        if veh != {"Irq_9P117.tga"}:
            fails.append(f"{m['slot']} TEL vehicle tex {veh}")
        if md.get("MISSILE01") != {m["proj_tex"]}:
            fails.append(f"{m['slot']} damaged missile tex {md.get('MISSILE01')}")
        dveh = set()
        for mesh, names in md.items():
            if mesh != "MISSILE01":
                dveh |= names
        if dveh != {"Irq_9P117D.tga"}:
            fails.append(f"{m['slot']} damaged vehicle tex {dveh}")
        if m["hier"] not in tel:
            fails.append(f"{m['slot']} missing hier {m['hier']!r}")
        if b"IRQ_AF500" in tel or b"IRQ_9P117" in tel:
            fails.append(f"{m['slot']} leaked source hier")
        if b"Irq_AlFahd500" in tel:
            fails.append(f"{m['slot']} leaked AlFahd identity")
        if m["hierd"] not in teld:
            fails.append(f"{m['slot']} missing damaged hier")
        proj = mesh_tex(art[rf"Art\W3D\{m['proj_model']}.W3D"])
        if not all(m["proj_tex"] in names for names in proj.values()):
            fails.append(f"{m['slot']} flying W3D tex {proj}")
    return fails


def dump_extract(data: dict[str, bytes], art: dict[str, bytes]) -> None:
    stage = OUT / "LAST_WINS_EXTRACT"
    keys = [UNIT_A_KEY] + [unit_key(m["ini"]) for m in VARIANTS]
    for rel in keys:
        p = stage / "DATA" / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data[rel])
    for m in VARIANTS:
        for stem in (m["model"], m["modeld"]):
            rel = rf"Art\W3D\{stem}.W3D"
            p = stage / "ART" / rel.replace("\\", "/")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(art[rel])
    for rel in (TEL_W3D, TELD_W3D):
        p = stage / "ART" / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(art[rel])


def main() -> int:
    for ident in VARIANTS:
        if len(ident["hier"]) != 9 or len(ident["hierd"]) != 10:
            raise SystemExit(f"hier length {ident['slot']}")
        if len(ident["model"]) > 15 or len(ident["modeld"]) > 15:
            raise SystemExit(f"model length {ident['slot']} {ident['model']} {ident['modeld']}")
    if sha256_path(SRC_DATA) != BASE_DATA_SHA or SRC_DATA.stat().st_size != BASE_DATA_SIZE:
        raise SystemExit("PR #591 DATA baseline mismatch")
    if sha256_path(SRC_ART) != BASE_ART_SHA or SRC_ART.stat().st_size != BASE_ART_SIZE:
        raise SystemExit("PR #574 ART baseline mismatch")

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    for m in VARIANTS:
        src_ini = (WHEELED / m["ini"]).read_text(encoding="latin1")
        data[unit_key(m["ini"])] = to_crlf(src_ini)

    art[TEL_W3D] = restore_a_vehicle(src_art[TEL_W3D], damaged=False)
    art[TELD_W3D] = restore_a_vehicle(src_art[TELD_W3D], damaged=True)
    for m in VARIANTS:
        art[rf"Art\W3D\{m['model']}.W3D"] = make_tel_w3d(src_art[TEL_W3D], False, m)
        art[rf"Art\W3D\{m['modeld']}.W3D"] = make_tel_w3d(src_art[TELD_W3D], True, m)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    packed_data = build_big(data)
    packed_art = build_big(art)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(packed_data)
    out_art.write_bytes(packed_art)
    extracted_data = parse_big(out_data.read_bytes())
    extracted_art = parse_big(out_art.read_bytes())
    dump_extract(extracted_data, extracted_art)

    fails = validate_data(extracted_data, src_data)
    fails.extend(validate_art(extracted_art, src_art))
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed_data))
    fails.extend(f"ART {x}" for x in big_structure_ok(packed_art))
    if len(extracted_data) != len(src_data):
        fails.append(f"DATA file count {len(extracted_data)} != {len(src_data)}")
    if len(extracted_art) != len(src_art) + 12:
        fails.append(f"ART file count {len(extracted_art)} != {len(src_art)+12}")

    data_sha = sha256_path(out_data)
    art_sha = sha256_path(out_art)
    changed_data = sorted(k for k in extracted_data if src_data.get(k) != extracted_data.get(k))
    changed_art = sorted(
        k for k in extracted_art if src_art.get(k) != extracted_art.get(k)
    )
    report = [
        "# SPECTER Iraq TEL pre-launch skins + original 9P117 carrier color",
        "",
        "Baseline DATA: PR #591 Alhussaien ICBM 30s fire.",
        "Baseline ART: PR #574 missile skins BCDHIJ.",
        "",
        "Missile A projectile / INI unchanged. B-J flying projectile W3Ds unchanged.",
        "A-J TEL vehicle meshes now reference original Irq_9P117.tga / Irq_9P117D.tga.",
        "B-J pre-launch MISSILE01 now uses each missile's existing projectile TGA.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted_data)}",
        f"- ART size: {out_art.stat().st_size}",
        f"- ART SHA256: {art_sha}",
        f"- ART files: {len(extracted_art)}",
        f"- Changed DATA: {', '.join(changed_data)}",
        f"- Changed ART: {', '.join(changed_art)}",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        report.append("RUNTIME_TEST=NOT RUN")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static / packed last-wins)",
        "- Missile A INI, projectile INI, and projectile W3D byte-identical",
        "- A TEL MISSILE01 still Irq_AlFahd500P.tga; vehicle meshes Irq_9P117.tga",
        "- B/C/D/H/I/J TEL MISSILE01 uses that variant's projectile P.tga",
        "- B/C/D/H/I/J TEL vehicle meshes Irq_9P117.tga / Irq_9P117D.tga",
        "- Original 9P117 W3D/DDS and GENERIC-MISSILES byte-identical",
        "- Flying projectile W3Ds/TGAs for B-J byte-identical",
        "- Weapons, radar, HP, costs, 9P117 object, factory, EU5, AbbasLauncher unchanged",
        "- 12 new dedicated TEL W3Ds added (6 variants x healthy/damaged)",
        "",
        "Static validation completed; runtime game test not performed.",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=YES\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted_data)}\n"
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={out_art.stat().st_size}\n"
        f"ART_SHA256={art_sha}\n"
        f"ART_FILES={len(extracted_art)}\n"
        f"CHANGED_DATA={', '.join(changed_data)}\n"
        f"CHANGED_ART={', '.join(changed_art)}\n"
        "MISSILE_A=INI+projectile W3D/TGA unchanged; TEL vehicle tex restored to 9P117\n"
        "PRELAUNCH=B-J TEL MISSILE01 retargeted to each projectile P.tga\n"
        "CARRIER=A-J vehicle meshes Irq_9P117.tga / Irq_9P117D.tga (original dds)\n"
        "BASELINE_DATA=PR #591\n"
        "BASELINE_ART=PR #574\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Iraq factory TEL pre-launch missile skins + 9P117 carrier color\n"
        "\n"
        "Missile A is unchanged except the carrier vehicle now uses the original\n"
        "9P117 truck texture instead of the blackened Al-Fahd clone.\n"
        "\n"
        "Missiles B, C, D, H, I, and J keep their existing in-flight models.\n"
        "Before launch they now show those same missile skins on the TEL,\n"
        "instead of sharing missile A's mounted appearance.\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "  _SPEC_ART_ONE.big\n"
        "\n"
        "Static validation completed; runtime game test not performed.\n",
        encoding="utf-8",
    )
    (OUT / "LAST_WINS.txt").write_text(
        "A_TEL=Irq_AlFahd500 vehicle=Irq_9P117.tga missile=Irq_AlFahd500P.tga\n"
        "B_TEL=Irq_AlHussein2 vehicle=Irq_9P117.tga missile=Irq_AlHussein2P.tga\n"
        "C_TEL=Irq_AlSamoud2T vehicle=Irq_9P117.tga missile=Irq_AlSamoud2P.tga\n"
        "D_TEL=Irq_AlAbbas2TL vehicle=Irq_9P117.tga missile=Irq_AlAbbas2P.tga\n"
        "H_TEL=Irq_AlBasrahTL vehicle=Irq_9P117.tga missile=Irq_AlBasrahP.tga\n"
        "I_TEL=Irq_AlNasirTEL vehicle=Irq_9P117.tga missile=Irq_AlNasirP.tga\n"
        "J_TEL=Irq_AlMansourT vehicle=Irq_9P117.tga missile=Irq_AlMansourP.tga\n"
        "FLYING=unchanged Irq_AlFahd500M / Irq_AlHussein2M / Irq_AlSamoud2M / "
        "Irq_AlAbbas2M / Irq_AlBasrahM / Irq_AlNasirM / Irq_AlMansourM\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_TEL_PRELAUNCH_COLOR.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
