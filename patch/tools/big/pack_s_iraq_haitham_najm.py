#!/usr/bin/env python3
"""Clone Iraq Al-Haitham from Alabaas ICBM and Al-Najm from Sarab7.

Baseline: PR #606 EGKM UI DATA+ART (spawn-safe roster).

Parents (packed last-wins):
  Al-Haitham <- Iraq_Alhussaien (AbbasLauncher.ini)  [NOT Iraq_AlAbbas / Al-Raad]
  Al-Najm    <- Iraq_Sarab7     (AlNida.ini)
  9P117      <- Iraq_R11ScudB   (reference only; not modified)

SPECTER scale (MOTHER / factory B-J):
  1000 km -> AttackRange 1720
  400 kg  -> PrimaryDamage 2000 + death 2200
  10/100 accuracy -> ScatterRadius 175
  5/100 stealth  -> projectile MaxHealth 400
  stealth >= 20  -> RadarPriority LOCAL_UNIT_ONLY
  stealth >= 60  -> RadarPriority NOT_ON_RADAR

Alabaas authorized change: Upgrade_Rearm_Iraq_Alhussaien BuildCost 10000 -> 15000 only.
No factory-TEL riders, no 9P117 edits, no global cooldown, no #603 path.
"""
from __future__ import annotations

import hashlib
import io
import re
import shutil
import struct
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_EGKM_UI/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_EGKM_UI/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_HAITHAM_NAJM"
SRC_DIR = ROOT / "patch/Data/INI"

SHA_DATA_606 = "9067cc23e3465281e83c40053956e0841fa7b6d7d99b4ce08391cea3eba5d7f6"
SIZE_DATA_606 = 366615607
SHA_ART_606 = "f35c8ac324ba22f2f6eafc63ac680e5ebb52cd6e0c22362d7edfda88ec10c16f"
SIZE_ART_606 = 1295762258

CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
CSF_KEY = r"Data\English\generals.csf"
WEAPON_KEY = r"Data\INI\Weapon.ini"
OCL_KEY = r"Data\INI\ObjectCreationList.ini"
UPG_KEY = r"Data\INI\Upgrade_MissileHalfPriceRearm.ini"
REARM_KEY = r"Data\INI\Object\Specter\Iraq Army\MissileHalfPriceRearm.ini"
ABBAS_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini"
SARAB_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AlNida.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
WO_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_WeaponObjects.ini"
SYS_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_Systems.ini"
CB_SLOT_KEY = r"Data\INI\CommandButton_SpecterMissileSlots.ini"

HAITHAM_OBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHaitham.ini"
NAJM_OBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNajm.ini"
HAITHAM_CHAIN_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlHaitham_Chain.ini"
NAJM_PROJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlNajm_Projectile.ini"
WEP_NEW_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlHaithamNajm.ini"

FLAG_KEY = r"Art\Textures\IraqiFlag.dds"
TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")
SHEET = 1024
BLACK = (22, 24, 26)
RED = (168, 32, 28)

# MOTHER / factory scale
KM_SCALE = 1720.0 / 1000.0
KG_SCALE = 2000.0 / 400.0
DEATH_SCALE = 2200.0 / 400.0
SCATTER_AT_10 = 175.0
STEALTH_HP_AT_5 = 400.0

HAITHAM_KM = 2500
HAITHAM_KG = 15000
HAITHAM_ACC = 50
HAITHAM_STEALTH = 85
HAITHAM_BUILD = 300.0
HAITHAM_COST = 30000
HAITHAM_REARM = 20000
HAITHAM_RANGE = int(round(HAITHAM_KM * KM_SCALE))  # 4300
HAITHAM_WH = int(round(HAITHAM_KG * KG_SCALE))  # 75000
HAITHAM_SCATTER = SCATTER_AT_10 * (10.0 / HAITHAM_ACC)  # 35
HAITHAM_HP = int(round(STEALTH_HP_AT_5 * (HAITHAM_STEALTH / 5.0)))  # 6800

NAJM_KM = 800
NAJM_KG = 400
NAJM_ACC = 50
NAJM_STEALTH = 25
NAJM_BUILD = 50.0
NAJM_COST = 2500
NAJM_RANGE = int(round(NAJM_KM * KM_SCALE))  # 1376
NAJM_DMG = int(round(NAJM_KG * KG_SCALE))  # 2000
NAJM_DEATH = int(round(NAJM_KG * DEATH_SCALE))  # 2200
NAJM_SCATTER = SCATTER_AT_10 * (10.0 / NAJM_ACC)  # 35
NAJM_HP = int(round(STEALTH_HP_AT_5 * (NAJM_STEALTH / 5.0)))  # 2000

ALABAAS_REARM = 15000

TIP_L = (
    "Al-Haitham\n"
    "Range: 2500 km\n"
    "Warhead: 15000 kg\n"
    "Point Accuracy: 50/100\n"
    "Radar Stealth: 85/100\n"
    "Build Time: 5 minutes\n"
    "Price: $30,000\n"
    "Rebuild Price: $20,000"
)
TIP_F = (
    "Al-Najm\n"
    "Range: 800 km\n"
    "Warhead: 400 kg × 2\n"
    "Point Accuracy: 50/100\n"
    "Radar Stealth: 25/100\n"
    "Build Time: 50 seconds\n"
    "Price: $2,500"
)


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
        raise SystemExit("not BIGF")
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


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def decode(blob: bytes) -> str:
    return blob.decode("latin1").replace("\r\n", "\n")


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def last_block(kind: str, name: str, text: str):
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\n.*?^End", text))
    return matches[-1] if matches else None


def replace_last_block(kind: str, name: str, text: str, new_block: str) -> str:
    m = last_block(kind, name, text)
    if not m:
        raise SystemExit(f"missing {kind} {name}")
    return text[: m.start()] + new_block.strip() + text[m.end() :]


def object_body(text: str, name: str) -> str | None:
    found = [(m.group(1), m.start()) for m in re.finditer(r"^Object\s+(\S+)\s*$", text, re.M)]
    for i, (n, start) in enumerate(found):
        if n == name:
            end = found[i + 1][1] if i + 1 < len(found) else len(text)
            return text[start:end]
    return None


def replace_object(text: str, name: str, new_body: str) -> str:
    found = [(m.group(1), m.start()) for m in re.finditer(r"^Object\s+(\S+)\s*$", text, re.M)]
    for i, (n, start) in enumerate(found):
        if n != name:
            continue
        end = found[i + 1][1] if i + 1 < len(found) else len(text)
        return text[:start] + new_body.rstrip() + "\n" + text[end:]
    raise SystemExit(f"object {name} missing")


def field(body: str | None, key: str) -> str:
    if not body:
        return ""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", body, re.M)
    return m.group(1).strip() if m else ""


def set_field(body: str, key: str, value: str, count: int = 0) -> str:
    return re.sub(
        rf"^(\s*{re.escape(key)}\s*=\s*).+$",
        rf"\g<1>{value}",
        body,
        count=count,
        flags=re.M,
    )


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


def shade(rgb, t):
    return tuple(max(0, min(255, int(c * t))) for c in rgb) + (255,)


def paste_small_flag(im: Image.Image, flag: Image.Image, xy, size):
    f = flag.resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    im.paste(f, xy, f)


def draw_stencil(im: Image.Image, text: str, center, light_body: bool):
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
    gap = 4
    widths = []
    glyph_h = 0
    for ch in text:
        bb = draw.textbbox((0, 0), ch, font=font)
        widths.append(bb[2] - bb[0])
        glyph_h = max(glyph_h, bb[3] - bb[1])
    total = sum(widths) + gap * (len(text) - 1)
    x = center[0] - total / 2
    bbox = draw.textbbox((0, 0), "A", font=font)
    y = center[1] - glyph_h / 2 - bbox[1]
    plate = [int(x - 14), int(y - 7), int(x + total + 14), int(y + glyph_h + 10)]
    if light_body:
        fill_plate = (28, 26, 22, 230)
        ink = (236, 228, 210)
        outline = (12, 10, 8)
    else:
        fill_plate = (214, 178, 16, 230)
        ink = (18, 16, 12)
        outline = (12, 10, 8)
    draw.rounded_rectangle(plate, radius=6, fill=fill_plate, outline=outline, width=3)
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=ink, stroke_width=1, stroke_fill=(8, 8, 8))
        x += w + gap


def make_skin(body, nose, stamp: str, flag: Image.Image) -> Image.Image:
    w = h = SHEET
    im = Image.new("RGBA", (w, h), shade(body, 1.0))
    px = im.load()
    nose_hi = int(0.14 * h)
    body_lo = int(0.18 * h)
    body_hi = int(0.82 * h)
    rear_lo = int(0.88 * h)
    mid_u0, mid_u1 = int(0.32 * w), int(0.68 * w)
    for y in range(h):
        for x in range(w):
            if y < nose_hi:
                circ = 1.0 - 0.10 * abs((x / w) - 0.5)
                px[x, y] = shade(nose, circ)
            elif y < body_lo:
                px[x, y] = shade(body, 0.78)
            elif y < body_hi:
                circ = 1.04 - 0.18 * abs((y - (body_lo + body_hi) / 2) / max(1, (body_hi - body_lo) / 2))
                px[x, y] = shade(body, circ)
            elif y < rear_lo:
                px[x, y] = shade(body, 0.80)
            else:
                px[x, y] = shade(body, 0.88)
    draw = ImageDraw.Draw(im)
    for x in (int(0.30 * w), int(0.70 * w)):
        draw.line([(x, body_lo + 4), (x, body_hi - 4)], fill=(12, 12, 12, 80), width=2)
    light = body[0] + body[1] + body[2] > 360
    paste_small_flag(im, flag, (mid_u0 + 18, body_lo + 36), (168, 96))
    paste_small_flag(im, flag, (mid_u0 + 18, body_lo + 250), (168, 96))
    draw_stencil(im, stamp, ((mid_u0 + mid_u1) // 2, body_lo + 160), light)
    draw_stencil(im, stamp, ((mid_u0 + mid_u1) // 2, body_lo + 372), light)
    im = ImageEnhance.Contrast(im).enhance(1.04)
    im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=40, threshold=3))
    return im.convert("RGBA")


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


def uniquify(blob: bytes, old: bytes, new: bytes) -> bytes:
    if len(old) != len(new):
        raise ValueError(f"identity length {old!r} -> {new!r}")
    if old not in blob:
        raise SystemExit(f"identity {old!r} missing")
    return blob.replace(old, new)


def clone_w3d(src: bytes, replacements: list[tuple[bytes, bytes]]) -> bytes:
    out = src
    for old, new in replacements:
        out = uniquify(out, old, new)
    return out


def fmt_num(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".")


def ensure_radar(body: str, priority: str) -> str:
    if re.search(r"^\s*RadarPriority\s*=", body, re.M):
        return set_field(body, "RadarPriority", priority)
    return re.sub(r"(^\s*KindOf\s*=)", f"  RadarPriority = {priority}\n\\1", body, count=1, flags=re.M)


def clone_haitham_tel(abbas_body: str) -> str:
    body = abbas_body
    body = re.sub(r"^Object Iraq_Alhussaien\s*$", "Object Iraq_AlHaitham", body, count=1, flags=re.M)
    body = set_field(body, "DisplayName", "OBJECT:AlHaitham")
    body = set_field(body, "SelectPortrait", "specter_missile_l")
    body = set_field(body, "ButtonImage", "specter_missile_l")
    body = set_field(body, "BuildCost", str(HAITHAM_COST))
    body = set_field(body, "BuildTime", f"{fmt_num(HAITHAM_BUILD)}")
    body = body.replace("Iraq_AlhussaienArmedCommandSet", "Iraq_AlHaithamArmedCommandSet")
    body = body.replace("Iraq_Alhussaien_UnarmedRearmSet", "Iraq_AlHaitham_UnarmedRearmSet")
    body = body.replace("Iraq_AlhussaienCommandSet", "Iraq_AlHaithamCommandSet")
    body = body.replace("Upgrade_Rearm_Iraq_Alhussaien", "Upgrade_Rearm_Iraq_AlHaitham")
    body = body.replace("OCL_Rearm_Iraq_Alhussaien", "OCL_Rearm_Iraq_AlHaitham")
    body = body.replace("AlAbidMissileWeapon", "Weapon_Iraq_AlHaitham_AlAbid")
    body = body.replace("HussieanMissileWeapon", "Weapon_Iraq_AlHaitham_Hussiean")
    # Dedicated launcher copies (same-length hierarchy IRQ_ALHTHM_*).
    for old, new in [
        ("Irq_Abbas_L_AD", "Irq_AlHthm_L_AD"),
        ("Irq_Abbas_L_A", "Irq_AlHthm_L_A"),
        ("Irq_Abbas_L_D", "Irq_AlHthm_L_D"),
        ("Irq_Abbas_L_R", "Irq_AlHthm_L_R"),
        ("Irq_Abbas_L", "Irq_AlHthm_L"),
    ]:
        body = body.replace(old, new)
    leftovers = [
        line
        for line in body.splitlines()
        if ("Iraq_Alhussaien" in line or "Irq_Abbas_L" in line)
        and "Irq_Abbas_T" not in line
    ]
    if leftovers:
        raise SystemExit("Haitham TEL still references parent IDs/models: " + leftovers[0])
    return body


def clone_najm_tel(sarab_body: str) -> str:
    body = sarab_body
    body = re.sub(r"^Object Iraq_Sarab7\s*$", "Object Iraq_AlNajm", body, count=1, flags=re.M)
    body = set_field(body, "DisplayName", "OBJECT:AlNajm")
    body = set_field(body, "SelectPortrait", "specter_missile_f")
    body = set_field(body, "ButtonImage", "specter_missile_f")
    body = set_field(body, "BuildCost", str(NAJM_COST))
    body = set_field(body, "BuildTime", f"{fmt_num(NAJM_BUILD)}          ;in seconds")
    body = body.replace("2x_MRPGM_Raad2", "Weapon_Iraq_AlNajm")
    body = body.replace("Irq_Sarab7", "Irq_AlNajm")
    if "Iraq_Sarab7" in body or "Irq_Sarab7" in body:
        raise SystemExit("Najm TEL still references parent IDs/models")
    return body


def clone_haitham_chain(wo: str, sys: str) -> str:
    alabid = object_body(wo, "AlAbidMissile")
    huss = object_body(wo, "HussieanMissile")
    alabid_rv = object_body(wo, "AlAbidWarheadReentryProjectile")
    huss_rv = object_body(wo, "HussieanWarheadReentryProjectile")
    alabid_re = object_body(sys, "AlAbidReentryObject")
    huss_re = object_body(sys, "HussieanWarheadReentryObject")
    if not all([alabid, huss, alabid_rv, huss_rv, alabid_re, huss_re]):
        raise SystemExit("missing ICBM chain parent object")

    def flying(src: str, name: str, ocl: str) -> str:
        b = src
        b = re.sub(r"^Object \S+\s*$", f"Object {name}", b, count=1, flags=re.M)
        b = b.replace("Model = Irq_AbbasM", "Model = Irq_AlHaithamM")
        b = set_field(b, "MaxHealth", f"{HAITHAM_HP}.0")
        b = set_field(b, "InitialHealth", f"{HAITHAM_HP}.0")
        b = b.replace("OCL_AlAbidWareheadsReentry", ocl)
        b = b.replace("OCL_HussieanWareheadsReentry", ocl)
        b = ensure_radar(b, "NOT_ON_RADAR")
        return b.rstrip() + "\n"

    def rv(src: str, name: str, death: str) -> str:
        b = src
        b = re.sub(r"^Object \S+\s*$", f"Object {name}", b, count=1, flags=re.M)
        b = b.replace("AlAbidWarheadDamage", death)
        b = b.replace("HussieanWarheadDamage", death)
        return b.rstrip() + "\n"

    def reentry(src: str, name: str, weapon: str) -> str:
        b = src
        b = re.sub(r"^Object \S+\s*$", f"Object {name}", b, count=1, flags=re.M)
        b = b.replace("AlAbidMirvReentryWeapon", weapon)
        b = b.replace("HussieanWarheadReentryWeapon", weapon)
        return b.rstrip() + "\n"

    parts = [
        "; Haitham ICBM chain cloned from AlAbid/Hussiean. Parents are not modified.\n",
        flying(alabid, "Projectile_Iraq_AlHaitham_AlAbid", "OCL_AlHaitham_AlAbidReentry"),
        flying(huss, "Projectile_Iraq_AlHaitham_Hussiean", "OCL_AlHaitham_HussieanReentry"),
        rv(alabid_rv, "Projectile_Iraq_AlHaitham_AlAbidRV", "Weapon_Iraq_AlHaitham_AlAbidWH"),
        rv(huss_rv, "Projectile_Iraq_AlHaitham_HussieanRV", "Weapon_Iraq_AlHaitham_HussieanWH"),
        reentry(alabid_re, "Iraq_AlHaitham_AlAbidReentryObject", "Weapon_Iraq_AlHaitham_AlAbidMirv"),
        reentry(huss_re, "Iraq_AlHaitham_HussieanReentryObject", "Weapon_Iraq_AlHaitham_HussieanMirv"),
    ]
    return "\n".join(parts)


def clone_najm_projectile(wo: str) -> str:
    src = object_body(wo, "MRBM_Raad2_Object")
    if not src:
        raise SystemExit("missing MRBM_Raad2_Object")
    b = src
    b = re.sub(r"^Object \S+\s*$", "Object Projectile_Iraq_AlNajm", b, count=1, flags=re.M)
    b = b.replace("Model = Irq_Raad2M", "Model = Irq_AlNajmM")
    b = set_field(b, "MaxHealth", f"{NAJM_HP}.0")
    b = set_field(b, "InitialHealth", f"{NAJM_HP}.0")
    b = b.replace("9M542_AP_Warhead", "Weapon_Iraq_AlNajm_Warhead")
    b = ensure_radar(b, "LOCAL_UNIT_ONLY")
    return "; Najm projectile cloned from MRBM_Raad2_Object. Parent is not modified.\n" + b


def make_weapons(wpn: str) -> str:
    alabid = last_block("Weapon", "AlAbidMissileWeapon", wpn)
    huss = last_block("Weapon", "HussieanMissileWeapon", wpn)
    alabid_mirv = last_block("Weapon", "AlAbidMirvReentryWeapon", wpn)
    huss_mirv = last_block("Weapon", "HussieanWarheadReentryWeapon", wpn)
    alabid_wh = last_block("Weapon", "AlAbidWarheadDamage", wpn)
    huss_wh = last_block("Weapon", "HussieanWarheadDamage", wpn)
    raad = last_block("Weapon", "2x_MRPGM_Raad2", wpn)
    death = last_block("Weapon", "9M542_AP_Warhead", wpn)
    if not all([alabid, huss, alabid_mirv, huss_mirv, alabid_wh, huss_wh, raad, death]):
        raise SystemExit("missing parent weapon")

    def launch(src: str, name: str, proj: str) -> str:
        b = src
        b = re.sub(r"^Weapon \S+\s*$", f"Weapon {name}", b, count=1, flags=re.M)
        b = set_field(b, "AttackRange", str(HAITHAM_RANGE))
        b = set_field(b, "ProjectileObject", proj)
        return b.rstrip() + "\n"

    def mirv(src: str, name: str, proj: str) -> str:
        b = src
        b = re.sub(r"^Weapon \S+\s*$", f"Weapon {name}", b, count=1, flags=re.M)
        b = set_field(b, "ScatterRadius", fmt_num(HAITHAM_SCATTER))
        b = set_field(b, "ProjectileObject", proj)
        return b.rstrip() + "\n"

    def warhead(src: str, name: str, dmg: int) -> str:
        b = src
        b = re.sub(r"^Weapon \S+\s*$", f"Weapon {name}", b, count=1, flags=re.M)
        b = set_field(b, "PrimaryDamage", f"{dmg}.0" if "." not in str(dmg) else str(dmg))
        return b.rstrip() + "\n"

    najm = raad.group(0)
    najm = re.sub(r"^Weapon \S+\s*$", "Weapon Weapon_Iraq_AlNajm", najm, count=1, flags=re.M)
    najm = set_field(najm, "PrimaryDamage", str(NAJM_DMG))
    najm = set_field(najm, "ScatterRadius", f"{fmt_num(NAJM_SCATTER)} ; CEP 50/100")
    najm = set_field(najm, "AttackRange", str(NAJM_RANGE))
    najm = set_field(najm, "ProjectileObject", "Projectile_Iraq_AlNajm")
    if "ClipSize                    = 2" not in najm:
        raise SystemExit("Najm lost ClipSize 2")

    najm_wh = death.group(0)
    najm_wh = re.sub(r"^Weapon \S+\s*$", "Weapon Weapon_Iraq_AlNajm_Warhead", najm_wh, count=1, flags=re.M)
    najm_wh = set_field(najm_wh, "PrimaryDamage", str(NAJM_DEATH))

    chunks = [
        "; Iraq Al-Haitham / Al-Najm weapons. Last-wins via Data\\INI\\Weapon\\.\n",
        "; Cloned from AlAbid/Hussiean and 2x_MRPGM_Raad2. Parents are not modified.\n",
        "; Scale: 1720/km1000, 2000 dmg/400kg, scatter 175@10acc, HP 400@5 stealth.\n",
        launch(alabid.group(0), "Weapon_Iraq_AlHaitham_AlAbid", "Projectile_Iraq_AlHaitham_AlAbid"),
        launch(huss.group(0), "Weapon_Iraq_AlHaitham_Hussiean", "Projectile_Iraq_AlHaitham_Hussiean"),
        mirv(alabid_mirv.group(0), "Weapon_Iraq_AlHaitham_AlAbidMirv", "Projectile_Iraq_AlHaitham_AlAbidRV"),
        mirv(huss_mirv.group(0), "Weapon_Iraq_AlHaitham_HussieanMirv", "Projectile_Iraq_AlHaitham_HussieanRV"),
        # Hussiean ICBM fire is 1 RV: full 15000 kg. AlAbid parent deploys 4 RVs;
        # keep per-RV yield at 15000 kg / 4 so the salvo still totals 15000 kg.
        warhead(alabid_wh.group(0), "Weapon_Iraq_AlHaitham_AlAbidWH", HAITHAM_WH // 4),
        warhead(huss_wh.group(0), "Weapon_Iraq_AlHaitham_HussieanWH", HAITHAM_WH),
        najm.rstrip() + "\n",
        najm_wh.rstrip() + "\n",
    ]
    return "\n".join(chunks)


def make_ocl_additions() -> str:
    return """
ObjectCreationList OCL_AlHaitham_AlAbidReentry
 CreateObject
   ObjectNames = Iraq_AlHaitham_AlAbidReentryObject
    Disposition = LIKE_EXISTING
 End
 CreateObject
   ObjectNames = RS24WarheadReentryDecoyObject
    Disposition = LIKE_EXISTING
 End
 CreateObject
   ObjectNames = PostBoostReentryVehicle
    Disposition = LIKE_EXISTING
 End
End

ObjectCreationList OCL_AlHaitham_HussieanReentry
 CreateObject
   ObjectNames = Iraq_AlHaitham_HussieanReentryObject
    Disposition = LIKE_EXISTING
 End
 CreateObject
   ObjectNames = RS24WarheadReentryDecoyObject
    Disposition = LIKE_EXISTING
 End
End

ObjectCreationList OCL_Rearm_Iraq_AlHaitham
  CreateObject
    ObjectNames       = RearmStrip_Iraq_AlHaitham
    Count             = 1
    ContainInsideSourceObject = Yes
  End
  CreateObject
    ObjectNames       = GenericFakeRider2_Default_Rank
    Count             = 1
    ContainInsideSourceObject = Yes
  End
End
"""


def make_rearm_strip(parent_strip: str) -> str:
    b = parent_strip
    b = re.sub(r"^Object \S+\s*$", "Object RearmStrip_Iraq_AlHaitham", b, count=1, flags=re.M)
    b = b.replace("Upgrade_Rearm_Iraq_Alhussaien", "Upgrade_Rearm_Iraq_AlHaitham")
    return b.rstrip() + "\n"


def factory_set_new() -> str:
    return (
        "CommandSet Iraq_AlFahdMissileFactoryCommandSet\r\n"
        "  1  = CB_MISSILE_A\r\n"
        "  2  = CB_MISSILE_B\r\n"
        "  3  = CB_MISSILE_C\r\n"
        "  4  = CB_MISSILE_D\r\n"
        "  5  = CB_MISSILE_E\r\n"
        "  6  = CB_MISSILE_F\r\n"
        "  7  = CB_MISSILE_G\r\n"
        "  8  = CB_MISSILE_H\r\n"
        "  9  = CB_MISSILE_I\r\n"
        "  10 = CB_MISSILE_J\r\n"
        "  11 = CB_MISSILE_K\r\n"
        "  12 = CB_MISSILE_L\r\n"
        "  13 = CB_MISSILE_M\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def append_commandsets(cs: str) -> str:
    extra = """
CommandSet Iraq_AlHaithamCommandSet
  1 = Command_TacticalStrike
  5 = Command_Rearm_Iraq_AlHaitham
  12 = Command_IraqDeployUnitWeapon
  16 = Command_AttackMove
  17 = Command_Guard
  14 = Command_Stop
End

CommandSet Iraq_AlHaithamArmedCommandSet
  1 = Command_IraqAlHaithamICBMFire
  5 = Command_AlHaithamAlAbidStrike
  12 = Command_IraqDeployUnitWeapon
  16 = Command_AttackMove
  17 = Command_Guard
  14 = Command_Stop
End

CommandSet Iraq_AlHaitham_UnarmedRearmSet
  1 = Command_TacticalStrike
  5 = Command_Rearm_Iraq_AlHaitham
  12 = Command_IraqDeployUnitWeapon
  16 = Command_AttackMove
  17 = Command_Guard
  14 = Command_Stop
End
"""
    return cs.rstrip() + "\n" + extra


def patch_commandbuttons(cb: str) -> str:
    f = last_block("CommandButton", "CB_MISSILE_F", cb)
    l = last_block("CommandButton", "CB_MISSILE_L", cb)
    if not f or not l:
        raise SystemExit("missing CB_MISSILE_F/L")
    f_new = """CommandButton CB_MISSILE_F
  Command       = UNIT_BUILD
  Object        = Iraq_AlNajm
  TextLabel     = CONTROLBAR:SpecterMissileF
  ButtonImage   = specter_missile_f
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipSpecterMissileF
End"""
    l_new = """CommandButton CB_MISSILE_L
  Command       = UNIT_BUILD
  Object        = Iraq_AlHaitham
  TextLabel     = CONTROLBAR:SpecterMissileL
  ButtonImage   = specter_missile_l
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipSpecterMissileL
End"""
    cb = replace_last_block("CommandButton", "CB_MISSILE_F", cb, f_new)
    cb = replace_last_block("CommandButton", "CB_MISSILE_L", cb, l_new)
    extra = """
CommandButton Command_IraqAlHaithamICBMFire
  Command             = FIRE_WEAPON
  WeaponSlot          = SECONDARY
  Options             = OK_FOR_MULTI_SELECT NEED_TARGET_POS CONTEXTMODE_COMMAND
  TextLabel           = CONTROLBAR:TacticalThermoNuclearStrike
  ButtonImage         = sys_fire
  ButtonBorderType    = ACTION
  DescriptLabel       = CONTROLBAR:ToolTipTacticalThermoNuclearStrike
  CursorName          = LaserGuidedMissiles
  RadiusCursorType    = NUCLEARMISSILE
End

CommandButton Command_AlHaithamAlAbidStrike
  Command             = FIRE_WEAPON
  WeaponSlot          = PRIMARY
  Options             = OK_FOR_MULTI_SELECT NEED_TARGET_POS CONTEXTMODE_COMMAND
  TextLabel           = CONTROLBAR:AlAbidMissileStrike
  ButtonImage         = Sys_AlAbid
  ButtonBorderType    = ACTION
  DescriptLabel       = CONTROLBAR:ToolTipAlAbidMissileStrike
  CursorName          = LaserGuidedMissiles
  RadiusCursorType    = NUCLEARMISSILE
End

CommandButton Command_Rearm_Iraq_AlHaitham
  Command                 = OBJECT_UPGRADE
  UnitSpecificSound       = MoneyWithdraw
  Upgrade                 = Upgrade_Rearm_Iraq_AlHaitham
  TextLabel               = CONTROLBAR:icbmrearm
  Options                 = OK_FOR_MULTI_SELECT NOT_QUEUEABLE
  ButtonImage             = SNNukeLaunch
  ButtonBorderType        = UPGRADE
  DescriptLabel           = CONTROLBAR:ToolTipicbmrearm
  PurchasedLabel          = CONTROLBAR:ToolTipicbmrearm
End
"""
    return cb.rstrip() + "\n" + extra


def patch_upgrades(upg: str) -> str:
    blk = last_block("Upgrade", "Upgrade_Rearm_Iraq_Alhussaien", upg)
    if not blk:
        raise SystemExit("missing Upgrade_Rearm_Iraq_Alhussaien")
    new = set_field(blk.group(0), "BuildCost", str(ALABAAS_REARM))
    upg = replace_last_block("Upgrade", "Upgrade_Rearm_Iraq_Alhussaien", upg, new)
    extra = f"""
Upgrade Upgrade_Rearm_Iraq_AlHaitham
  DisplayName      = UPGRADE:hussienwarhead
  Type             = OBJECT
  BuildTime        = 0.0
  BuildCost        = {HAITHAM_REARM}
  ButtonImage      = SNNukeLaunch
  ResearchSound    = SUSuicideAttk
End
"""
    return upg.rstrip() + "\n" + extra


def classify(rgb):
    r, g, b = rgb
    if r > 140 and g < 90 and b < 90:
        return "red"
    if r < 55 and g < 55 and b < 55:
        return "black"
    if r > 190 and g > 185 and b > 175:
        return "white"
    return "other"


def region_mode(im: Image.Image, box):
    crop = im.convert("RGB").crop(box)
    px = crop.load()
    w, h = crop.size
    counts = {"red": 0, "white": 0, "black": 0, "other": 0}
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            counts[classify(px[x, y])] += 1
    return counts


def validate(data: dict[str, bytes], art: dict[str, bytes], src_data: dict[str, bytes], src_art: dict[str, bytes]) -> list[str]:
    fails = []
    if big_structure_ok(build_big(data)):
        fails.append("data structure after rebuild check used live map; see main")
    for key in [ABBAS_KEY, SARAB_KEY, R11_KEY]:
        if data[key] != src_data[key]:
            fails.append(f"parent file mutated {key}")
    if object_body(decode(data[ABBAS_KEY]), "Iraq_AlHaitham"):
        fails.append("Haitham overwritten AbbasLauncher")
    if object_body(decode(data[SARAB_KEY]), "Iraq_AlNajm"):
        fails.append("Najm overwritten AlNida")

    haitham = object_body(decode(data[HAITHAM_OBJ_KEY]), "Iraq_AlHaitham")
    najm = object_body(decode(data[NAJM_OBJ_KEY]), "Iraq_AlNajm")
    parent_h = object_body(decode(data[ABBAS_KEY]), "Iraq_Alhussaien")
    parent_n = object_body(decode(data[SARAB_KEY]), "Iraq_Sarab7")
    parent_g = object_body(decode(data[R11_KEY]), "Iraq_R11ScudB")
    if not haitham:
        fails.append("Iraq_AlHaitham missing")
    if not najm:
        fails.append("Iraq_AlNajm missing")
    if not parent_h or field(parent_h, "BuildCost") != "20000":
        fails.append("Alabaas BuildCost mutated")
    if not parent_h or not field(parent_h, "BuildTime").startswith("30.0"):
        fails.append("Alabaas BuildTime mutated")
    if parent_n and field(parent_n, "BuildCost") != "1200":
        fails.append("Sarab7 BuildCost mutated")
    if parent_g and field(parent_g, "BuildCost") != "1200":
        fails.append("9P117 mutated")

    if haitham:
        if field(haitham, "BuildCost") != str(HAITHAM_COST):
            fails.append(f"Haitham BuildCost {field(haitham, 'BuildCost')}")
        if field(haitham, "BuildTime") != fmt_num(HAITHAM_BUILD):
            fails.append(f"Haitham BuildTime {field(haitham, 'BuildTime')}")
        if field(haitham, "Side") != "Iraq":
            fails.append("Haitham Side")
        if field(haitham, "SelectPortrait") != "specter_missile_l":
            fails.append("Haitham portrait")
        if "Weapon_Iraq_AlHaitham_AlAbid" not in haitham:
            fails.append("Haitham primary weapon")
        if "Upgrade_Rearm_Iraq_AlHaitham" not in haitham:
            fails.append("Haitham rearm upgrade")
        if "RiderChangeContain" not in haitham:
            fails.append("Haitham lost rider contain")
    if najm:
        if field(najm, "BuildCost") != str(NAJM_COST):
            fails.append(f"Najm BuildCost {field(najm, 'BuildCost')}")
        if not field(najm, "BuildTime").startswith(fmt_num(NAJM_BUILD)):
            fails.append(f"Najm BuildTime {field(najm, 'BuildTime')}")
        if field(najm, "Side") != "Iraq":
            fails.append("Najm Side")
        if "Weapon_Iraq_AlNajm" not in najm:
            fails.append("Najm weapon")
        if "RiderChangeContain" in najm:
            fails.append("Najm gained rider contain")

    wep = decode(data[WEP_NEW_KEY])
    w_huss = last_block("Weapon", "Weapon_Iraq_AlHaitham_Hussiean", wep)
    w_abid = last_block("Weapon", "Weapon_Iraq_AlHaitham_AlAbid", wep)
    w_hwh = last_block("Weapon", "Weapon_Iraq_AlHaitham_HussieanWH", wep)
    w_awh = last_block("Weapon", "Weapon_Iraq_AlHaitham_AlAbidWH", wep)
    w_hm = last_block("Weapon", "Weapon_Iraq_AlHaitham_HussieanMirv", wep)
    w_n = last_block("Weapon", "Weapon_Iraq_AlNajm", wep)
    w_nw = last_block("Weapon", "Weapon_Iraq_AlNajm_Warhead", wep)
    for label, blk, rng in [
        ("Haitham Hussiean range", w_huss, str(HAITHAM_RANGE)),
        ("Haitham AlAbid range", w_abid, str(HAITHAM_RANGE)),
        ("Najm range", w_n, str(NAJM_RANGE)),
    ]:
        if not blk or field(blk.group(0), "AttackRange") != rng:
            fails.append(f"{label} {field(blk.group(0), 'AttackRange') if blk else 'missing'}")
    if not w_hwh or field(w_hwh.group(0), "PrimaryDamage") not in {str(HAITHAM_WH), f"{HAITHAM_WH}.0"}:
        fails.append(f"Haitham Hussiean WH {field(w_hwh.group(0), 'PrimaryDamage') if w_hwh else 'missing'}")
    if not w_awh or field(w_awh.group(0), "PrimaryDamage") not in {str(HAITHAM_WH // 4), f"{HAITHAM_WH // 4}.0"}:
        fails.append(f"Haitham AlAbid WH {field(w_awh.group(0), 'PrimaryDamage') if w_awh else 'missing'}")
    if not w_hm or field(w_hm.group(0), "ScatterRadius") != fmt_num(HAITHAM_SCATTER):
        fails.append("Haitham accuracy scatter")
    if not w_n or field(w_n.group(0), "PrimaryDamage") != str(NAJM_DMG):
        fails.append("Najm damage")
    if not w_n or "ClipSize                    = 2" not in w_n.group(0):
        fails.append("Najm ClipSize")
    if not w_n or fmt_num(NAJM_SCATTER) not in field(w_n.group(0), "ScatterRadius"):
        fails.append("Najm scatter")
    if not w_nw or field(w_nw.group(0), "PrimaryDamage") != str(NAJM_DEATH):
        fails.append("Najm death warhead")

    # Parent weapons unchanged in Weapon.ini
    src_w = decode(src_data[WEAPON_KEY])
    new_w = decode(data[WEAPON_KEY])
    for name in ["AlAbidMissileWeapon", "HussieanMissileWeapon", "2x_MRPGM_Raad2", "SRBM_ALHIJARAH_HE"]:
        a = last_block("Weapon", name, src_w)
        b = last_block("Weapon", name, new_w)
        if not a or not b or a.group(0) != b.group(0):
            fails.append(f"Weapon.ini {name} changed")

    upg = decode(data[UPG_KEY])
    u_ab = last_block("Upgrade", "Upgrade_Rearm_Iraq_Alhussaien", upg)
    u_ht = last_block("Upgrade", "Upgrade_Rearm_Iraq_AlHaitham", upg)
    if not u_ab or field(u_ab.group(0), "BuildCost") != str(ALABAAS_REARM):
        fails.append("Alabaas rebuild not 15000")
    if not u_ht or field(u_ht.group(0), "BuildCost") != str(HAITHAM_REARM):
        fails.append("Haitham rebuild not 20000")
    if u_ab and field(u_ab.group(0), "BuildCost") == str(HAITHAM_REARM):
        fails.append("Alabaas accidentally got Haitham rebuild")

    cs = decode(data[CS_KEY])
    fac = last_block("CommandSet", "Iraq_AlFahdMissileFactoryCommandSet", cs)
    if not fac:
        fails.append("factory CS missing")
    else:
        slots = {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)\s*$", fac.group(0), re.M)}
        expect = {
            1: "CB_MISSILE_A",
            2: "CB_MISSILE_B",
            3: "CB_MISSILE_C",
            4: "CB_MISSILE_D",
            5: "CB_MISSILE_E",
            6: "CB_MISSILE_F",
            7: "CB_MISSILE_G",
            8: "CB_MISSILE_H",
            9: "CB_MISSILE_I",
            10: "CB_MISSILE_J",
            11: "CB_MISSILE_K",
            12: "CB_MISSILE_L",
            13: "CB_MISSILE_M",
            14: "Command_Sell",
        }
        if slots != expect:
            fails.append(f"factory slots {slots}")
    if not last_block("CommandSet", "Iraq_AlHaithamArmedCommandSet", cs):
        fails.append("Haitham armed CS missing")

    cb = decode(data[CB_KEY])
    for name, obj in [("CB_MISSILE_F", "Iraq_AlNajm"), ("CB_MISSILE_L", "Iraq_AlHaitham")]:
        blk = last_block("CommandButton", name, cb)
        if not blk or field(blk.group(0), "Object") != obj:
            fails.append(f"{name} object")
    for name in ["CB_MISSILE_E", "CB_MISSILE_G", "CB_MISSILE_K"]:
        a = last_block("CommandButton", name, decode(src_data[CB_KEY]))
        b = last_block("CommandButton", name, cb)
        if not a or not b or a.group(0) != b.group(0):
            fails.append(f"{name} changed")

    chain = decode(data[HAITHAM_CHAIN_KEY])
    for n in [
        "Projectile_Iraq_AlHaitham_AlAbid",
        "Projectile_Iraq_AlHaitham_Hussiean",
        "Projectile_Iraq_AlHaitham_AlAbidRV",
        "Projectile_Iraq_AlHaitham_HussieanRV",
        "Iraq_AlHaitham_AlAbidReentryObject",
        "Iraq_AlHaitham_HussieanReentryObject",
    ]:
        if not object_body(chain, n):
            fails.append(f"missing {n}")
    fly = object_body(chain, "Projectile_Iraq_AlHaitham_Hussiean")
    if fly and field(fly, "MaxHealth") != f"{HAITHAM_HP}.0":
        fails.append("Haitham stealth HP")
    if fly and field(fly, "RadarPriority") != "NOT_ON_RADAR":
        fails.append("Haitham radar")
    nproj = object_body(decode(data[NAJM_PROJ_KEY]), "Projectile_Iraq_AlNajm")
    if not nproj or field(nproj, "MaxHealth") != f"{NAJM_HP}.0":
        fails.append("Najm stealth HP")
    if nproj and field(nproj, "RadarPriority") != "LOCAL_UNIT_ONLY":
        fails.append("Najm radar")

    # uniqueness
    names = []
    for key, blob in data.items():
        if not key.lower().endswith(".ini"):
            continue
        names.extend(re.findall(r"^Object\s+(\S+)\s*$", decode(blob), re.M))
    dups = [n for n in names if names.count(n) > 1 and n in {"Iraq_AlHaitham", "Iraq_AlNajm"}]
    if dups:
        fails.append(f"duplicate objects {dups}")

    # ART parents intact
    for key in [
        r"Art\W3D\Irq_AbbasM.W3D",
        r"Art\W3D\Irq_Abbas_L.W3D",
        r"Art\W3D\Irq_Sarab7.W3D",
        r"Art\W3D\Irq_Raad2M.W3D",
        r"Art\Textures\Irq_AbbasMissile.dds",
        r"Art\Textures\Irq_Sarab7.dds",
        r"Art\Textures\AAM-GENTEX.dds",
        r"Art\W3D\Irq_R11_M.W3D" if r"Art\W3D\Irq_R11_M.W3D" in src_art else None,
    ]:
        if key and src_art.get(key) and art.get(key) != src_art[key]:
            fails.append(f"parent ART mutated {key}")

    for tex_key, expect in [
        (r"Art\Textures\AlHaithamMissile.tga", "black"),
        (r"Art\Textures\AlNajmSkin.tga", "red"),
    ]:
        tex = art.get(tex_key)
        if not tex:
            fails.append(f"missing {tex_key}")
            continue
        im = Image.open(io.BytesIO(tex)).convert("RGB")
        body = region_mode(im, (40, 200, 280, 780))
        flag = region_mode(im, (340, 230, 530, 350))
        if body.get(expect, 0) < 80:
            fails.append(f"{tex_key} body not {expect} {body}")
        if flag["red"] < 40 or flag["white"] < 15 or flag["black"] < 30:
            fails.append(f"{tex_key} missing Iraqi flag {flag}")

    for w3d_key, old_id, new_id, old_tex, new_tex in [
        (r"Art\W3D\Irq_AlHaithamM.W3D", b"IRQ_ABBASM", b"IRQ_ALHTHM", b"Irq_AbbasMissile.tga", b"AlHaithamMissile.tga"),
        (r"Art\W3D\Irq_AlNajmM.W3D", b"IRQ_RAAD2M", b"IRQ_ALNAJM", b"AAM-GENTEX.dds", b"AlNajmSkin.tga"),
        (r"Art\W3D\Irq_AlNajm.W3D", b"IRQ_SARAB7", b"IRQ_ALNAJT", b"AAM-GENTEX.dds", b"AlNajmSkin.tga"),
    ]:
        blob = art.get(w3d_key)
        if not blob:
            fails.append(f"missing {w3d_key}")
            continue
        if old_id in blob:
            fails.append(f"{w3d_key} still has {old_id!r}")
        if new_id not in blob:
            fails.append(f"{w3d_key} missing {new_id!r}")
        if old_tex in blob:
            fails.append(f"{w3d_key} still uses {old_tex!r}")
        if new_tex not in blob:
            fails.append(f"{w3d_key} missing {new_tex!r}")

    csf = data[CSF_KEY]
    if csf_get(csf, "OBJECT:AlHaitham") != "Al-Haitham":
        fails.append("CSF Al-Haitham")
    if csf_get(csf, "OBJECT:AlNajm") != "Al-Najm":
        fails.append("CSF Al-Najm")
    tip_l = csf_get(csf, "CONTROLBAR:ToolTipSpecterMissileL") or ""
    tip_f = csf_get(csf, "CONTROLBAR:ToolTipSpecterMissileF") or ""
    if "15000 kg" not in tip_l or "$30,000" not in tip_l or "$20,000" not in tip_l:
        fails.append("Haitham tooltip")
    if "400 kg" not in tip_f or "$2,500" not in tip_f:
        fails.append("Najm tooltip")
    return fails


def write_source_mirrors(haitham, najm, chain, nproj, weps, strip):
    wheeled = SRC_DIR / "Object/Specter/Iraq Army/Wheeled"
    iraq = SRC_DIR / "Object/Specter/Iraq Army"
    wheeled.mkdir(parents=True, exist_ok=True)
    (wheeled / "Iraq_AlHaitham.ini").write_text(haitham.replace("\r\n", "\n"), encoding="latin1")
    (wheeled / "Iraq_AlNajm.ini").write_text(najm.replace("\r\n", "\n"), encoding="latin1")
    (iraq / "Iraq_AlHaitham_Chain.ini").write_text(chain.replace("\r\n", "\n"), encoding="latin1")
    (iraq / "Iraq_AlNajm_Projectile.ini").write_text(nproj.replace("\r\n", "\n"), encoding="latin1")
    (SRC_DIR / "Weapon/Weapon_Iraq_AlHaithamNajm.ini").write_text(weps.replace("\r\n", "\n"), encoding="latin1")
    # safe source upgrades / buttons
    upg_src = SRC_DIR / "Upgrade_MissileHalfPriceRearm.ini"
    txt = upg_src.read_text(encoding="latin1")
    txt = re.sub(
        r"(Upgrade Upgrade_Rearm_Iraq_Alhussaien\n(?:.*\n)*?  BuildCost        = )10000",
        rf"\g<1>{ALABAAS_REARM}",
        txt,
        count=1,
    )
    if "Upgrade_Rearm_Iraq_AlHaitham" not in txt:
        txt = txt.rstrip() + (
            f"\n\nUpgrade Upgrade_Rearm_Iraq_AlHaitham\n"
            f"  DisplayName      = UPGRADE:hussienwarhead\n"
            f"  Type             = OBJECT\n"
            f"  BuildTime        = 0.0\n"
            f"  BuildCost        = {HAITHAM_REARM}\n"
            f"  ButtonImage      = SNNukeLaunch\n"
            f"  ResearchSound    = SUSuicideAttk\n"
            f"End\n"
        )
    upg_src.write_text(txt, encoding="latin1")
    rearm_src = iraq / "MissileHalfPriceRearm.ini"
    rtxt = rearm_src.read_text(encoding="latin1")
    if "RearmStrip_Iraq_AlHaitham" not in rtxt:
        rearm_src.write_text(rtxt.rstrip() + "\n\n" + strip + "\n", encoding="latin1")
    cb_src = SRC_DIR / "CommandButton_SpecterMissileSlots.ini"
    cbt = cb_src.read_text(encoding="latin1")
    cbt = cbt.replace(
        "CommandButton CB_MISSILE_F\n  Command       = UNIT_BUILD\n  TextLabel",
        "CommandButton CB_MISSILE_F\n  Command       = UNIT_BUILD\n  Object        = Iraq_AlNajm\n  TextLabel",
    )
    cbt = cbt.replace(
        "CommandButton CB_MISSILE_L\n  Command       = UNIT_BUILD\n  TextLabel",
        "CommandButton CB_MISSILE_L\n  Command       = UNIT_BUILD\n  Object        = Iraq_AlHaitham\n  TextLabel",
    )
    cbt = cbt.replace(
        "; F/L omit Object until a real missile is connected.",
        "; F=Al-Najm (Iraq_AlNajm), L=Al-Haitham (Iraq_AlHaitham).",
    )
    cb_src.write_text(cbt, encoding="latin1")


def main() -> int:
    if SRC_DATA.stat().st_size != SIZE_DATA_606 or sha256_path(SRC_DATA) != SHA_DATA_606:
        raise SystemExit("DATA baseline is not PR #606")
    if SRC_ART.stat().st_size != SIZE_ART_606 or sha256_path(SRC_ART) != SHA_ART_606:
        raise SystemExit("ART baseline is not PR #606")
    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    abbas = decode(data[ABBAS_KEY])
    sarab = decode(data[SARAB_KEY])
    wo = decode(data[WO_KEY])
    sysini = decode(data[SYS_KEY])
    wpn = decode(data[WEAPON_KEY])
    cs = decode(data[CS_KEY])
    cb = decode(data[CB_KEY])
    upg = decode(data[UPG_KEY])
    rearm = decode(data[REARM_KEY])
    ocl = decode(data[OCL_KEY])

    parent_h = object_body(abbas, "Iraq_Alhussaien")
    parent_n = object_body(sarab, "Iraq_Sarab7")
    if not parent_h or not parent_n:
        raise SystemExit("parent objects missing in packed #606")
    haitham = clone_haitham_tel(parent_h)
    najm = clone_najm_tel(parent_n)
    chain = clone_haitham_chain(wo, sysini)
    nproj = clone_najm_projectile(wo)
    weps = make_weapons(wpn)
    strip_parent = object_body(rearm, "RearmStrip_Iraq_Alhussaien")
    if not strip_parent:
        raise SystemExit("missing RearmStrip_Iraq_Alhussaien")
    strip = make_rearm_strip(strip_parent)

    data[HAITHAM_OBJ_KEY] = to_crlf(haitham)
    data[NAJM_OBJ_KEY] = to_crlf(najm)
    data[HAITHAM_CHAIN_KEY] = to_crlf(chain)
    data[NAJM_PROJ_KEY] = to_crlf(nproj)
    data[WEP_NEW_KEY] = to_crlf(weps)
    data[REARM_KEY] = to_crlf(rearm.rstrip() + "\n\n" + strip + "\n")
    data[OCL_KEY] = to_crlf(ocl.rstrip() + "\n" + make_ocl_additions())
    data[UPG_KEY] = to_crlf(patch_upgrades(upg))
    cs = replace_last_block(
        "CommandSet",
        "Iraq_AlFahdMissileFactoryCommandSet",
        cs,
        factory_set_new().replace("\r\n", "\n"),
    )
    data[CS_KEY] = to_crlf(append_commandsets(cs))
    data[CB_KEY] = to_crlf(patch_commandbuttons(cb))
    if CB_SLOT_KEY in data:
        slot = decode(data[CB_SLOT_KEY])
        slot = patch_commandbuttons(slot) if last_block("CommandButton", "CB_MISSILE_F", slot) else slot
        # slot file only has F/L without extra fire buttons; keep simple object insert
        slot = decode(src_data[CB_SLOT_KEY])
        slot = slot.replace(
            "CommandButton CB_MISSILE_F\n  Command       = UNIT_BUILD\n  TextLabel",
            "CommandButton CB_MISSILE_F\n  Command       = UNIT_BUILD\n  Object        = Iraq_AlNajm\n  TextLabel",
        )
        slot = slot.replace(
            "CommandButton CB_MISSILE_L\n  Command       = UNIT_BUILD\n  TextLabel",
            "CommandButton CB_MISSILE_L\n  Command       = UNIT_BUILD\n  Object        = Iraq_AlHaitham\n  TextLabel",
        )
        data[CB_SLOT_KEY] = to_crlf(slot)

    data[CSF_KEY] = csf_upsert(
        data[CSF_KEY],
        {
            "OBJECT:AlHaitham": "Al-Haitham",
            "OBJECT:AlNajm": "Al-Najm",
            "CONTROLBAR:SpecterMissileF": "Al-Najm",
            "CONTROLBAR:SpecterMissileL": "Al-Haitham",
            "CONTROLBAR:ToolTipSpecterMissileF": TIP_F,
            "CONTROLBAR:ToolTipSpecterMissileL": TIP_L,
        },
    )

    flag = Image.open(io.BytesIO(art[FLAG_KEY])).convert("RGBA")
    haitham_tex = make_tga32(make_skin(BLACK, BLACK, "AL-HAITHAM", flag))
    najm_tex = make_tga32(make_skin(RED, RED, "AL-NAJM", flag))
    art[r"Art\Textures\AlHaithamMissile.tga"] = haitham_tex
    art[r"Art\Textures\AlNajmSkin.tga"] = najm_tex

    art[r"Art\W3D\Irq_AlHaithamM.W3D"] = clone_w3d(
        art[r"Art\W3D\Irq_AbbasM.W3D"],
        [(b"IRQ_ABBASM", b"IRQ_ALHTHM"), (b"Irq_AbbasMissile.tga", b"AlHaithamMissile.tga")],
    )
    # Launcher copies: unique hierarchy, missile texture only.
    launcher_map = [
        (r"Art\W3D\Irq_Abbas_L.W3D", r"Art\W3D\Irq_AlHthm_L.W3D", b"IRQ_ABBAS_L", b"IRQ_ALHTM_L"),
        (r"Art\W3D\Irq_Abbas_L_A.W3D", r"Art\W3D\Irq_AlHthm_L_A.W3D", b"IRQ_ABBAS_L_A", b"IRQ_ALHTM_L_A"),
        (r"Art\W3D\Irq_Abbas_L_AD.W3D", r"Art\W3D\Irq_AlHthm_L_AD.W3D", b"IRQ_ABBAS_L_AD", b"IRQ_ALHTM_L_AD"),
        (r"Art\W3D\Irq_Abbas_L_D.W3D", r"Art\W3D\Irq_AlHthm_L_D.W3D", b"IRQ_ABBAS_L_D", b"IRQ_ALHTM_L_D"),
        (r"Art\W3D\Irq_Abbas_L_R.W3D", r"Art\W3D\Irq_AlHthm_L_R.W3D", b"IRQ_ABBAS_L_R", b"IRQ_ALHTM_L_R"),
    ]
    for src_k, dst_k, old_id, new_id in launcher_map:
        blob = art[src_k]
        # IRQ_ABBAS_L is a prefix of IRQ_ABBAS_L_A; replace longer first (already ordered).
        blob = uniquify(blob, old_id, new_id)
        if b"Irq_AbbasMissile.dds" in blob:
            blob = uniquify(blob, b"Irq_AbbasMissile.dds", b"AlHaithamMissile.tga")
        # Keep W3D internal model-name strings aligned with the new filename.
        name_pairs = [
            (b"Irq_Abbas_L_AD", b"Irq_AlHthm_L_AD"),
            (b"Irq_Abbas_L_A", b"Irq_AlHthm_L_A"),
            (b"Irq_Abbas_L_D", b"Irq_AlHthm_L_D"),
            (b"Irq_Abbas_L_R", b"Irq_AlHthm_L_R"),
            (b"Irq_Abbas_L", b"Irq_AlHthm_L"),
        ]
        for old_n, new_n in name_pairs:
            if old_n in blob:
                blob = uniquify(blob, old_n, new_n)
        art[dst_k] = blob

    art[r"Art\W3D\Irq_AlNajmM.W3D"] = clone_w3d(
        art[r"Art\W3D\Irq_Raad2M.W3D"],
        [(b"IRQ_RAAD2M", b"IRQ_ALNAJM"), (b"AAM-GENTEX.dds", b"AlNajmSkin.tga")],
    )
    art[r"Art\W3D\Irq_AlNajm.W3D"] = clone_w3d(
        art[r"Art\W3D\Irq_Sarab7.W3D"],
        [(b"IRQ_SARAB7", b"IRQ_ALNAJT"), (b"AAM-GENTEX.dds", b"AlNajmSkin.tga")],
    )
    if r"Art\W3D\Irq_Sarab7D.W3D" in art:
        art[r"Art\W3D\Irq_AlNajmD.W3D"] = clone_w3d(
            art[r"Art\W3D\Irq_Sarab7D.W3D"],
            [(b"IRQ_SARAB7D", b"IRQ_ALNAJMD"), (b"AAM-GENTEX.dds", b"AlNajmSkin.tga")],
        )
        # Najm TEL damaged model name Irq_AlNajm is used for all states in the clone
        # (parent also reused Irq_Sarab7 for damaged). No extra INI model name.

    write_source_mirrors(haitham, najm, chain, nproj, weps, strip)

    fails = validate(data, art, src_data, src_art)
    out_data = build_big(data)
    out_art = build_big(art)
    fails.extend([f"DATA {x}" for x in big_structure_ok(out_data)])
    fails.extend([f"ART {x}" for x in big_structure_ok(out_art)])
    if fails:
        raise SystemExit("VALIDATION FAIL\n" + "\n".join(fails))

    # Re-extract last-wins confirmation
    packed = parse_big(out_data)
    packed_art = parse_big(out_art)
    fails2 = validate(packed, packed_art, src_data, src_art)
    if fails2:
        raise SystemExit("RE-EXTRACT FAIL\n" + "\n".join(fails2))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_SPEC_DATA_ONE.big").write_bytes(out_data)
    (OUT / "_SPEC_ART_ONE.big").write_bytes(out_art)
    data_sha = sha256_path(OUT / "_SPEC_DATA_ONE.big")
    art_sha = sha256_path(OUT / "_SPEC_ART_ONE.big")

    report = [
        "SPECTER Iraq Al-Haitham + Al-Najm packed last-wins validation",
        f"DATA {len(out_data)} {data_sha}",
        f"ART  {len(out_art)} {art_sha}",
        f"DATA files {len(packed)} ART files {len(packed_art)}",
        "",
        "PARENTS (unchanged objects):",
        "  Alabaas ICBM = Iraq_Alhussaien (AbbasLauncher.ini) BuildCost 20000 BuildTime 30.0",
        "  Sarab7       = Iraq_Sarab7     (AlNida.ini)        BuildCost 1200  BuildTime 22.0",
        "  9P117        = Iraq_R11ScudB   (9P117.ini)         NOT MODIFIED",
        "",
        "NEW OBJECTS:",
        f"  Iraq_AlHaitham slot L  range {HAITHAM_RANGE} (=2500 km)  HussieanWH {HAITHAM_WH}  AlAbidWH {HAITHAM_WH // 4} x4  scatter {fmt_num(HAITHAM_SCATTER)}  HP {HAITHAM_HP} NOT_ON_RADAR  build 300s ${HAITHAM_COST} rearm ${HAITHAM_REARM}",
        f"  Iraq_AlNajm    slot F  range {NAJM_RANGE} (=800 km)   dmg {NAJM_DMG}+{NAJM_DEATH} ClipSize 2  scatter {fmt_num(NAJM_SCATTER)}  HP {NAJM_HP} LOCAL_UNIT_ONLY  build 50s ${NAJM_COST} (no rearm; parent has none)",
        "",
        f"Alabaas rebuild Upgrade_Rearm_Iraq_Alhussaien BuildCost {ALABAAS_REARM} (was 10000).",
        "Alabaas object/weapon/art/production otherwise unchanged.",
        "",
        "ACCURACY = ScatterRadius on the real weapon (MIRV for Haitham, 2x_MRPGM clone for Najm).",
        "RADAR STEALTH = projectile MaxHealth + RadarPriority (NOT speed).",
        "WARHEAD = DeathWeapon PrimaryDamage on the cloned ICBM RV / Najm AP warhead + Najm PrimaryDamage.",
        "",
        "STATIC_VALIDATION=PASS",
        "RUNTIME_TEST=NOT RUN",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=YES\n"
        f"DATA_SIZE={len(out_data)}\n"
        f"DATA_SHA256={data_sha}\n"
        f"ART_SIZE={len(out_art)}\n"
        f"ART_SHA256={art_sha}\n"
        "BASELINE=PR #606 EGKM UI\n"
        "PARENT_HAITHAM=Iraq_Alhussaien\n"
        "PARENT_NAJM=Iraq_Sarab7\n"
        "PARENT_REFERENCE=Iraq_R11ScudB\n"
        f"HAITHAM_RANGE={HAITHAM_RANGE}\n"
        f"HAITHAM_WARHEAD={HAITHAM_WH}\n"
        f"HAITHAM_SCATTER={fmt_num(HAITHAM_SCATTER)}\n"
        f"HAITHAM_HP={HAITHAM_HP}\n"
        f"HAITHAM_BUILD={fmt_num(HAITHAM_BUILD)}\n"
        f"HAITHAM_COST={HAITHAM_COST}\n"
        f"HAITHAM_REARM={HAITHAM_REARM}\n"
        f"NAJM_RANGE={NAJM_RANGE}\n"
        f"NAJM_DAMAGE={NAJM_DMG}\n"
        f"NAJM_DEATH={NAJM_DEATH}\n"
        f"NAJM_SCATTER={fmt_num(NAJM_SCATTER)}\n"
        f"NAJM_HP={NAJM_HP}\n"
        f"NAJM_BUILD={fmt_num(NAJM_BUILD)}\n"
        f"NAJM_COST={NAJM_COST}\n"
        f"ALABAAS_REARM={ALABAAS_REARM}\n"
        "COOLDOWN=NOT IMPLEMENTED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Iraq Al-Haitham + Al-Najm\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder.\n"
        "Al-Haitham (factory L) is cloned from Iraq_Alhussaien / Alabaas ICBM.\n"
        "Al-Najm (factory F) is cloned from Iraq_Sarab7.\n"
        "Alabaas rebuild/reload is $15,000. 9P117 is unchanged.\n"
        "No global cooldown. Static packed validation only.\n",
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Iraq Al-Haitham and Al-Najm\n"
        "\n"
        "- Clone Al-Haitham (`Iraq_AlHaitham`) from Alabaas ICBM `Iraq_Alhussaien`.\n"
        "- Clone Al-Najm (`Iraq_AlNajm`) from `Iraq_Sarab7`.\n"
        "- Factory slot F = Al-Najm, slot L = Al-Haitham.\n"
        "- Alabaas rebuild upgrade is $15,000. Haitham rebuild is $20,000.\n"
        "- Dedicated black / red missile art with Iraqi markings.\n"
        "- Parents and 9P117 remain in place.\n",
        encoding="utf-8",
    )
    (OUT / "CONFLICTS.txt").write_text(
        "Alabaas card still shows 15000k / 5 minutes / 1400k; those remain display-only on the parent.\n"
        "Haitham AlAbid alternate strike uses 4 parent MIRVs; each DeathWeapon is 15000 kg / 4 so the salvo totals 15000 kg.\n"
        "Haitham primary ICBM fire (Hussiean) is 1 RV at 15000 kg.\n"
        "Sarab7 parent still has AttackRange 1200 / PrimaryDamage 1200 vs its old 400k card.\n"
        "Najm range 800 is implemented as 800 km on the MOTHER 1.72/km scale (AttackRange 1376), not raw 800.\n"
        "Radar stealth is projectile MaxHealth + RadarPriority, not a native 0-100 field and not speed.\n"
        "Accuracy is ScatterRadius, not a native 0-100 field.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_HAITHAM_NAJM.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
        zf.write(OUT / "CONFLICTS.txt", "CONFLICTS.txt")
        zf.write(OUT / "RELEASE_NOTES.md", "RELEASE_NOTES.md")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size} sha={sha256_path(zip_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
