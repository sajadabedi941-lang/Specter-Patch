#!/usr/bin/env python3
"""Pack NEW Iraqi Missile Factory + Iraq_AlFahd500 onto healthy live s.

Authority baseline:
  DATA 366350648 SHA 8fa3dcbde4f4a7256a9dbb85936c9ab5875cf62c7c4f7770246c68bd42796e34
  ART  1246050506 SHA 389803f96644b44b46e527b791857d25c3bc4e6d808a0ae1e7a379a4fa7ef2e3

Does not restore the deleted 8-missile project or Iraq_MissileFactory.
Static validation only. The game is not launched.
"""
from __future__ import annotations

import hashlib
import io
import re
import struct
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_ROLLBACK/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_ROLLBACK/_SPEC_ART_ONE.big"
PATCH_DATA = ROOT / "patch/Data"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD500"
DONOR = Path("/tmp/iqmiss-donor")

HLOD_HEADER = 0x00000701
W3D_NAME_LEN = 16
TEX_CHUNK = 0x00000032

BASE_DATA_SHA = "8fa3dcbde4f4a7256a9dbb85936c9ab5875cf62c7c4f7770246c68bd42796e34"
BASE_ART_SHA = "389803f96644b44b46e527b791857d25c3bc4e6d808a0ae1e7a379a4fa7ef2e3"

CSF_LABELS = {
    "OBJECT:Iraq_AlFahd500": "AL-Fahd 500",
    "CONTROLBAR:ConstructIraq_AlFahd500": "AL-Fahd 500",
    "CONTROLBAR:ToolTipIraq_AlFahd500": "Build AL-Fahd 500. 9P117-class launcher with doubled warhead.",
    "OBJECT:IraqAlFahdMissileFactory": "Missile Factory",
    "CONTROLBAR:ConstructIraqAlFahdMissileFactory": "Missile Factory",
    "CONTROLBAR:ToolTipIraqAlFahdMissileFactory": "Build Missile Factory. Produces AL-Fahd 500.",
}

FACTORY_BUTTON = (
    "\r\n"
    "CommandButton Command_ConstructIraq_AlFahdMissileFactory\r\n"
    "  Command          = DOZER_CONSTRUCT\r\n"
    "  Object           = Iraq_AlFahdMissileFactory\r\n"
    "  TextLabel        = CONTROLBAR:ConstructIraqAlFahdMissileFactory\r\n"
    "  ButtonImage      = irq_warfctry\r\n"
    "  ButtonBorderType = BUILD\r\n"
    "  DescriptLabel    = CONTROLBAR:ToolTipIraqAlFahdMissileFactory\r\n"
    "End\r\n"
    "CommandButton Command_ConstructIraq_AlFahd500\r\n"
    "  Command       = UNIT_BUILD\r\n"
    "  Object        = Iraq_AlFahd500\r\n"
    "  TextLabel     = CONTROLBAR:ConstructIraq_AlFahd500\r\n"
    "  ButtonImage   = irq_9p117\r\n"
    "  ButtonBorderType = BUILD\r\n"
    "  DescriptLabel = CONTROLBAR:ToolTipIraq_AlFahd500\r\n"
    "End\r\n"
)

FACTORY_SET = (
    "CommandSet Iraq_AlFahdMissileFactoryCommandSet\r\n"
    "  1  = Command_ConstructIraq_AlFahd500\r\n"
    "  13 = Command_SetRallyPoint\r\n"
    "  14 = Command_Sell\r\n"
    "End\r\n"
)

OLD_RESIDUE = [
    b"Iraq_AlHussein_New",
    b"Iraq_AlHijarah_New",
    b"Iraq_AlAbbas_New",
    b"Iraq_Badr2000_New",
    b"Iraq_AlSamoud_New",
    b"Iraq_Ababil100_New",
    b"Iraq_Tammuz1_New",
    b"Iraq_AlAbid_New",
    b"Object Iraq_MissileFactory",
    b"Iraq_MissileFactoryCommandSet",
    b"Command_ConstructIraq_MissileFactory",
    b"IQ_AlHussein",
]


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_big(data: bytes):
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


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


def find_ci(files: dict[str, bytes], key: str) -> str | None:
    lk = key.replace("/", "\\").lower()
    for k in files:
        if k.replace("/", "\\").lower() == lk:
            return k
    return None


def to_crlf(data: bytes) -> bytes:
    text = data.decode("latin1").replace("\r\n", "\n").replace("\n", "\r\n")
    return text.encode("latin1")


def walk_chunks(blob: bytes, start: int = 0, end: int | None = None):
    if end is None:
        end = len(blob)
    pos = start
    while pos + 8 <= end:
        cid, raw = struct.unpack_from("<II", blob, pos)
        sz = raw & 0x7FFFFFFF
        cont = bool(raw & 0x80000000)
        cs, ce = pos + 8, pos + 8 + sz
        if ce > end + 8:
            break
        yield cid, cont, pos, cs, min(ce, len(blob))
        if cont:
            yield from walk_chunks(blob, cs, min(ce, end))
        pos = ce


def zstr(buf: bytes) -> str:
    return buf.split(b"\x00", 1)[0].decode("latin1", errors="replace")


def hlod_fields(blob: bytes) -> tuple[str | None, str | None]:
    for cid, _c, _p, cs, ce in walk_chunks(blob):
        if cid == HLOD_HEADER and ce - cs >= 40:
            return zstr(blob[cs + 8 : cs + 24]), zstr(blob[cs + 24 : cs + 40])
    return None, None


def patch_hlod_name(blob: bytes, new_name: str) -> bytes:
    if len(new_name) >= W3D_NAME_LEN:
        raise ValueError(f"HLod name too long: {new_name}")
    padded = new_name.encode("ascii") + b"\x00" * (W3D_NAME_LEN - len(new_name))
    out = bytearray(blob)
    for cid, _c, _p, cs, ce in walk_chunks(blob):
        if cid == HLOD_HEADER and ce - cs >= 40:
            out[cs + 8 : cs + 24] = padded
    return bytes(out)


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


def texture_names(blob: bytes) -> set[str]:
    found = set()
    for cid, _c, _p, cs, ce in walk_chunks(blob):
        if cid == TEX_CHUNK:
            found.add(zstr(blob[cs:ce]))
    return found


def save_tga(im: Image.Image) -> bytes:
    buf = io.BytesIO()
    im.convert("RGBA").save(buf, format="TGA")
    return buf.getvalue()


def blacken(im: Image.Image) -> Image.Image:
    src = im.convert("RGBA")
    px = src.load()
    w, h = src.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            lum = (r * 30 + g * 59 + b * 11) // 100
            tone = max(8, min(48, lum // 5))
            px[x, y] = (tone, tone, min(52, tone + 4), a)
    return src


def yellow_missile_atlas(generic: Image.Image, flag: Image.Image) -> Image.Image:
    im = generic.convert("RGBA")
    px = im.load()
    w, h = im.size
    # Primary missile UV box from Irq_R11_M (D3D V).
    u0, u1, v0, v1 = 0.148, 0.732, 0.221, 0.863
    x0, x1 = int(u0 * w), int(u1 * w)
    y0, y1 = int(v0 * h), int(v1 * h)
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(w, x1)):
            r, g, b, a = px[x, y]
            if a < 8:
                continue
            lum = (r * 30 + g * 59 + b * 11) // 100
            nr = min(255, int(lum * 1.55 + 40))
            ng = min(255, int(lum * 1.35 + 20))
            nb = min(40, lum // 6)
            px[x, y] = (nr, ng, nb, a)
    fw = flag.convert("RGBA").resize((96, 48), Image.Resampling.NEAREST)
    cx = int(((u0 + 0.530) / 2) * w) - fw.size[0] // 2
    cy = int(((v0 + v1) / 2) * h) - fw.size[1] // 2
    im.paste(fw, (max(0, cx), max(0, cy)), fw)
    return im


def csf_append(csf: bytes, labels: dict[str, str]) -> bytes:
    if csf[:4] != b" FSC":
        raise SystemExit(f"unexpected CSF magic {csf[:4]!r}")
    _magic, ver, nlab, nstr, unused, lang = struct.unpack_from("<4sIIIII", csf, 0)
    existing = set()
    pos = 24
    while pos < len(csf):
        if csf[pos : pos + 4] != b" LBL":
            break
        pos += 4
        cnt, nlen = struct.unpack_from("<II", csf, pos)
        pos += 8
        name = csf[pos : pos + nlen].decode("latin1")
        pos += nlen
        existing.add(name)
        for _ in range(cnt):
            smag = csf[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4 + slen * 2
            if smag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4 + elen
    extra = bytearray()
    added = 0
    for key, value in labels.items():
        if key in existing:
            continue
        encoded = value.encode("utf-16le")
        xored = bytes(x ^ 0xFF for x in encoded)
        extra += b" LBL"
        extra += struct.pack("<II", 1, len(key))
        extra += key.encode("latin1")
        extra += b" RTS"
        extra += struct.pack("<I", len(value))
        extra += xored
        added += 1
    if not added:
        return csf
    out = bytearray(csf)
    struct.pack_into("<I", out, 8, nlab + added)
    struct.pack_into("<I", out, 12, nstr + added)
    out += extra
    return bytes(out)


def patch_vt72b_slot19(cs: str) -> str:
    old = (
        "CommandSet Iraq_VT72BCommandSet\r\n"
        "  1  = Command_ConstructIraq_PowerPlant\r\n"
        "  2  = Command_ConstructIraq_CommandCenter\r\n"
        "  3  = Command_ConstructIraq_SupplyCenter\r\n"
        "  4  = Command_ConstructIraq_WarFactory_T\r\n"
        "  5  = Command_ConstructIraq_Airfield_T\r\n"
        "  6  = Command_ConstructIraq_MIC\r\n"
        "  7  = Command_ConstructIraq_DefenseSite ;Command_ConstructIraq_100mmCannon\r\n"
        "  8  = Command_ConstructIraq_RadarStation\r\n"
        "  9  = Command_ConstructIraq_Sam2\r\n"
        "  10 = Command_ConstructIraq_Barracks\r\n"
        "  11 = Command_ConstructIraq_Abbas\r\n"
        "  12 = Command_ConstructIraq_D30_Howitzer\r\n"
        "  13 = Command_ConstructIraq_HeavyAirBase\r\n"
        "  14 = Command_DisarmMinesAtPosition\r\n"
        "  15 = Command_ConstructIraq_Abbas_AI\r\n"
        "  16 = Command_ConstructIraqFahad3SamSite\r\n"
        "  17 = Command_ConstructIraqMilitaryWarfactory\r\n"
        "  18 = Command_Stop\r\n"
        "End"
    )
    if cs.count(old) != 1:
        raise SystemExit(f"unique VT72B block count={cs.count(old)}")
    if "19 = Command_ConstructIraq_AlFahdMissileFactory" in cs:
        return cs
    new = old.replace(
        "  18 = Command_Stop\r\nEnd",
        "  18 = Command_Stop\r\n  19 = Command_ConstructIraq_AlFahdMissileFactory\r\nEnd",
    )
    return cs.replace(old, new, 1)


def validate(data: dict[str, bytes], art: dict[str, bytes], src_data: dict[str, bytes], src_art: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    all_ini = b"\n".join(v for k, v in data.items() if k.lower().endswith(".ini"))

    for needle in OLD_RESIDUE:
        if needle in all_ini:
            fails.append(f"old project residue {needle.decode('ascii')}")

    if all_ini.count(b"Object Iraq_AlFahd500") != 1:
        fails.append("Iraq_AlFahd500 count")
    if all_ini.count(b"Object Iraq_AlFahdMissileFactory") != 1:
        fails.append("factory object count")
    if all_ini.count(b"Object Iraq_R11ScudB") != 1:
        fails.append("Iraq_R11ScudB lost or duplicated")
    if all_ini.count(b"Weapon Weapon_Iraq_AlFahd500") != 1:
        fails.append("AlFahd weapon count")
    if all_ini.count(b"Weapon SRBM_ALHIJARAH_HE") < 1:
        fails.append("donor weapon missing")

    r11 = src_data[r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"]
    if data[r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"] != r11:
        fails.append("9P117.ini mutated")

    wep = data[r"Data\INI\Weapon.ini"].decode("latin1")
    m = re.search(r"(?ms)^Weapon SRBM_ALHIJARAH_HE\r?\n.*?^End", wep)
    if not m or "PrimaryDamage               = 2000.0" not in m.group(0):
        fails.append("9P117 donor damage changed")

    alf = data[r"Data\INI\Weapon_Iraq_AlFahd500.ini"].decode("latin1")
    if "PrimaryDamage               = 4000.0" not in alf:
        fails.append("AlFahd damage not 4000")
    if "AttackRange                 = 1720.0" not in alf or "MinimumAttackRange          = 800.0" not in alf:
        fails.append("AlFahd range mismatch")
    if "PreAttackDelay              = 500" not in alf or "DelayBetweenShots           = 3000" not in alf:
        fails.append("AlFahd timing mismatch")
    if "ClipReloadTime              = 95000" not in alf:
        fails.append("AlFahd reload mismatch")

    unit = data[r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"].decode("latin1")
    if "BuildCost       = 3000" not in unit or "BuildTime       = 17.0" not in unit:
        fails.append("AlFahd cost/time")
    if "Locomotor = SET_NORMAL Generic8x8Locomotor" not in unit:
        fails.append("AlFahd locomotor")
    if "Weapon = PRIMARY   Weapon_Iraq_AlFahd500" not in unit:
        fails.append("AlFahd weapon link")
    if "PackTime = 6555" not in unit or "UnpackTime = 6555" not in unit:
        fails.append("AlFahd deploy timing")
    if "Model                           = Irq_AlFahd500" not in unit:
        fails.append("AlFahd model")

    proj = data[r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini"].decode("latin1")
    if "MissileAIUpdate" not in proj or "R11SRBMLocomotor" not in proj:
        fails.append("projectile AI/locomotor")
    if "Model = Irq_AlFahd500M" not in proj:
        fails.append("projectile model")

    core_cs = data[r"Data\INI\CommandSet.ini"].decode("latin1")
    vt = re.search(r"(?ms)^CommandSet Iraq_VT72BCommandSet\r?\n.*?^End", core_cs)
    if not vt or "14 = Command_DisarmMinesAtPosition" not in vt.group(0):
        fails.append("VT72B Clear Mines lost")
    if not vt or "19 = Command_ConstructIraq_AlFahdMissileFactory" not in vt.group(0):
        fails.append("VT72B slot 19 missing")
    wk = re.search(r"(?ms)^CommandSet Iraq_WorkerCommandSet\r?\n.*?^End", core_cs)
    src_cs = src_data[r"Data\INI\CommandSet.ini"].decode("latin1")
    src_wk = re.search(r"(?ms)^CommandSet Iraq_WorkerCommandSet\r?\n.*?^End", src_cs)
    if not wk or not src_wk or wk.group(0) != src_wk.group(0):
        fails.append("Worker CommandSet changed")
    if core_cs.count("CommandSet Iraq_AlFahdMissileFactoryCommandSet") != 1:
        fails.append("factory CommandSet count")
    if "Command_ConstructIraq_R11ScudB" not in core_cs:
        fails.append("R11 war factory button lost")

    cb = data[r"Data\INI\CommandButton.ini"].decode("latin1")
    if cb.count("CommandButton Command_ConstructIraq_AlFahd500") != 1:
        fails.append("AlFahd button")
    if cb.count("CommandButton Command_ConstructIraq_AlFahdMissileFactory") != 1:
        fails.append("factory button")
    if cb.count("CommandButton Command_ConstructIraq_R11ScudB") != 1:
        fails.append("R11 button lost")

    for stem, expect in [
        ("Irq_AlFahd500", "Irq_AlFahd500"),
        ("Irq_AlFahd500D", "Irq_AlFahd500D"),
        ("Irq_AlFahd500M", "Irq_AlFahd500M"),
        ("Irq_FahdFac", "Irq_FahdFac"),
        ("Irq_FahdFacD", "Irq_FahdFacD"),
    ]:
        key = find_ci(art, f"Art\\W3D\\{stem}.W3D")
        if not key:
            fails.append(f"missing W3D {stem}")
            continue
        name, _hier = hlod_fields(art[key])
        if name != expect:
            fails.append(f"HLod {name!r} != {expect}")
        for tex in texture_names(art[key]):
            tkey = find_ci(art, f"Art\\Textures\\{tex}")
            if tkey is None:
                alt = tex[:-4] + ".dds" if tex.lower().endswith(".tga") else tex[:-4] + ".tga"
                if find_ci(art, f"Art\\Textures\\{alt}") is None:
                    fails.append(f"{stem} missing tex {tex}")

    for donor in ["Irq_9P117", "Irq_9P117D", "Irq_R11_M", "Irq_WarFactory"]:
        sk = find_ci(src_art, f"Art\\W3D\\{donor}.W3D")
        dk = find_ci(art, f"Art\\W3D\\{donor}.W3D")
        if not sk or not dk or src_art[sk] != art[dk]:
            fails.append(f"donor W3D mutated {donor}")
    for tex in ["GENERIC-MISSILES.dds", "Irq_9P117.dds", "IraqiFlag.dds"]:
        sk = find_ci(src_art, f"Art\\Textures\\{tex}")
        dk = find_ci(art, f"Art\\Textures\\{tex}")
        if not sk or not dk or src_art[sk] != art[dk]:
            fails.append(f"shared texture mutated {tex}")

    iq = [k for k in art if re.search(r"iq_al(hussein|hijarah|abbas|abid|samoud)|iq_badr|iq_tammuz|iq_ababil", k, re.I)]
    if iq:
        fails.append(f"old IQ clones returned {iq[:4]}")

    extra_art = [k for k in art if k not in src_art]
    extra_data = [k for k in data if k not in src_data]
    if len(extra_data) < 4:
        fails.append(f"too few new DATA files {extra_data}")
    return fails, extra_data, extra_art


def main() -> int:
    if sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("baseline DATA SHA mismatch")
    if sha256_path(SRC_ART) != BASE_ART_SHA:
        raise SystemExit("baseline ART SHA mismatch")

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    # --- ART: black TEL + yellow missile ---
    tel = Image.open(io.BytesIO(src_art[r"Art\Textures\Irq_9P117.dds"]))
    teld = Image.open(io.BytesIO(src_art[r"Art\Textures\Irq_9P117D.dds"]))
    gen = Image.open(io.BytesIO(src_art[r"Art\Textures\GENERIC-MISSILES.dds"]))
    flag = Image.open(io.BytesIO(src_art[r"Art\Textures\IraqiFlag.dds"]))
    art[r"Art\Textures\Irq_AlFahd500.tga"] = save_tga(blacken(tel))
    art[r"Art\Textures\Irq_AlFahd500D.tga"] = save_tga(blacken(teld))
    art[r"Art\Textures\Irq_AlFahd500M.tga"] = save_tga(yellow_missile_atlas(gen, flag))

    tel_map = {"Irq_9P117.tga": "Irq_AlFahd500.tga", "GENERIC-MISSILES.dds": "Irq_AlFahd500M.tga"}
    teld_map = {"Irq_9P117D.tga": "Irq_AlFahd500D.tga", "GENERIC-MISSILES.dds": "Irq_AlFahd500M.tga"}
    msl_map = {"GENERIC-MISSILES.dds": "Irq_AlFahd500M.tga"}

    w = patch_hlod_name(replace_textures(src_art[r"Art\W3D\Irq_9P117.W3D"], tel_map), "Irq_AlFahd500")
    art[r"Art\W3D\Irq_AlFahd500.W3D"] = w
    w = patch_hlod_name(replace_textures(src_art[r"Art\W3D\Irq_9P117D.W3D"], teld_map), "Irq_AlFahd500D")
    art[r"Art\W3D\Irq_AlFahd500D.W3D"] = w
    w = patch_hlod_name(replace_textures(src_art[r"Art\W3D\Irq_R11_M.W3D"], msl_map), "Irq_AlFahd500M")
    art[r"Art\W3D\Irq_AlFahd500M.W3D"] = w

    # --- ART: factory mesh clones (unique HLod, no abarfrccmd import) ---
    fac_tex = {
        "abarfrccmd.dds": "Camo net.tga",
        "abarfrccmd_d.dds": "Camo netd.tga",
    }
    for src_name, dest_stem in [
        ("LSFIQMCheChang.W3D", "Irq_FahdFac"),
        ("LSFIQMCheChangd.W3D", "Irq_FahdFacD"),
        ("LSFIQMCheChange.W3D", "Irq_FahdFacE"),
    ]:
        raw = (DONOR / src_name).read_bytes()
        cloned = patch_hlod_name(replace_textures(raw, fac_tex), dest_stem)
        art[f"Art\\W3D\\{dest_stem}.W3D"] = cloned
        for tex in texture_names(cloned):
            if find_ci(art, f"Art\\Textures\\{tex}") is None:
                donor_tex = DONOR / "textures" / tex
                if not donor_tex.is_file():
                    raise SystemExit(f"factory texture missing {tex}")
                art[f"Art\\Textures\\{tex}"] = donor_tex.read_bytes()

    # --- DATA extras ---
    extras = {
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini": PATCH_DATA
        / "INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlFahd500.ini",
        r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini": PATCH_DATA
        / "INI/Object/Specter/Iraq Army/Iraq_AlFahd500_Projectile.ini",
        r"Data\INI\Weapon_Iraq_AlFahd500.ini": PATCH_DATA / "INI/Weapon_Iraq_AlFahd500.ini",
        r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini": PATCH_DATA
        / "INI/Object/Specter/Iraq Army/Buildings/Iraq_AlFahdMissileFactory.ini",
    }
    for key, path in extras.items():
        data[key] = to_crlf(path.read_bytes())

    cb = data[r"Data\INI\CommandButton.ini"].decode("latin1")
    if "Command_ConstructIraq_AlFahd500" in cb:
        raise SystemExit("AlFahd button already present")
    data[r"Data\INI\CommandButton.ini"] = (cb + FACTORY_BUTTON).encode("latin1")

    cs = data[r"Data\INI\CommandSet.ini"].decode("latin1")
    cs = patch_vt72b_slot19(cs)
    if not cs.endswith("\r\n"):
        cs += "\r\n"
    cs += "\r\n" + FACTORY_SET
    data[r"Data\INI\CommandSet.ini"] = cs.encode("latin1")

    data[r"Data\English\generals.csf"] = csf_append(data[r"Data\English\generals.csf"], CSF_LABELS)

    packed_data = build_big(data)
    packed_art = build_big(art)
    OUT.mkdir(parents=True, exist_ok=True)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(packed_data)
    out_art.write_bytes(packed_art)

    extracted_d = parse_big(packed_data)
    extracted_a = parse_big(packed_art)
    fails, extra_d, extra_a = validate(extracted_d, extracted_a, src_data, src_art)

    zip_path = OUT / "SPECTER_IRAQ_ALFAHD500.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")

    report = [
        "# Iraq AL-Fahd 500 + new Missile Factory",
        "",
        "Static validation only. The game was not launched.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {sha256_path(out_data)}",
        f"- DATA files: {len(extracted_d)}",
        f"- ART size: {out_art.stat().st_size}",
        f"- ART SHA256: {sha256_path(out_art)}",
        f"- ART files: {len(extracted_a)}",
        f"- ZIP size: {zip_path.stat().st_size}",
        f"- ZIP SHA256: {sha256_path(zip_path)}",
        "",
        "## New DATA files",
        "",
    ]
    report.extend(f"- {k}" for k in extra_d)
    report += ["", "## New ART files", ""]
    report.extend(f"- {k}" for k in extra_a)
    report += [
        "",
        "## Core DATA patches",
        "- CommandButton.ini: factory + AL-Fahd construct buttons",
        "- CommandSet.ini: VT72B slot 19 factory construct; new factory CommandSet",
        "- generals.csf: AL-Fahd / factory labels",
        "- Worker CommandSet unchanged; War Factory / 9P117 unchanged",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
        print("\n".join(report))
        return 1
    report += [
        "## VALIDATION PASS",
        "- Iraq_AlFahd500 exists; cost 3000; damage 4000; range 1720/800; build 17.0",
        "- fire/reload/deploy/locomotor match 9P117",
        "- Iraq_R11ScudB and SRBM_ALHIJARAH_HE unchanged (2000 damage)",
        "- factory produces only AL-Fahd 500; VT72B Clear Mines kept; Worker untouched",
        "- cloned W3D HLod names match Model=; textures resolve",
        "- donor 9P117 / Irq_R11_M / GENERIC-MISSILES byte-identical",
        "- no old 8-missile / Iraq_*_New / IQ_* residue",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
    (OUT / "HASHES.txt").write_text(
        f"DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={sha256_path(out_data)}\n"
        f"DATA_FILES={len(extracted_d)}\n"
        f"ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={out_art.stat().st_size}\n"
        f"ART_SHA256={sha256_path(out_art)}\n"
        f"ART_FILES={len(extracted_a)}\n"
        f"ZIP=SPECTER_IRAQ_ALFAHD500.zip\n"
        f"ZIP_SIZE={zip_path.stat().st_size}\n"
        f"ZIP_SHA256={sha256_path(zip_path)}\n"
        f"BASELINE=FLAG_SIZE_FINAL / s-iraq-missile-rollback\n"
        f"STATIC_VALIDATION=PASS\n"
        f"RUNTIME_TEST=NOT RUN\n",
        encoding="ascii",
    )
    (OUT / "README.txt").write_text(
        "SPECTER new Iraqi Missile Factory + AL-Fahd 500\n"
        "\n"
        "Install both _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big over current live s.\n"
        "This is a new implementation on the post-rollback baseline.\n"
        "It does not restore the old 8-missile project.\n"
        "\n"
        "Static validation only. The game was not launched.\n",
        encoding="ascii",
    )
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
