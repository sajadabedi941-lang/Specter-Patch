#!/usr/bin/env python3
"""SPECTER1 Vietnam + Syria ART fix.

Baseline: SPECTER1_Vietnam_Syria_Roster_01 DATA (gameplay preserved) +
SPECTER1_Shadow_AH1Z_ART_01 ART.

Does not modify USA/Russia/China donor object INIs, Iraq Su-24MR, Weapon.ini,
airbase architecture, scales, costs, or weapons. Button IDs kept.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

from PIL import Image

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_VIETNAM_SYRIA_ROSTER_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_VIETNAM_SYRIA_ROSTER_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "791e37840ab208bebe47ab6cd419e79f33806390cc3b60a200aa625075297261"
EXPECTED_ART_SHA = "b8a7f45dd57a1f56c4e68a5a16af04849834e0775db256637ab1ad1853702abe"
DONOR_HELI = Path("/tmp/donor_heli")
CAMEO_DIR = Path("/workspace/patch/art_src/cameos")
OUT_DIR = Path("/tmp/SPECTER1_VIETNAM_SYRIA_ART_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_VIETNAM_SYRIA_ART_01")

P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_IRAQ_MR = r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MR.ini"
P_MAPPED = r"Data\INI\MappedImages\HandCreated\Vietnam_Syria_ArtFix_Images.INI"

VN_YAK = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetYak130.ini"
VN_MIG29 = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetMig29S.ini"
VN_MI17 = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetMi17.ini"
VN_MI8 = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetMi8.ini"
SY_MIG29 = r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\Syria_Mig-29A.ini"
SY_MIRAGE = r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\Syria_MirageF1-Bq.ini"
SY_SU25 = r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\Syria_Su-25K.ini"
SY_MI8 = r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\Syria_Mi-8.ini"
SY_H6K = r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\SyriaBomberH6K.ini"
SY_MIG21 = r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig21.ini"
SY_MIG21MF = r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig21MF.ini"

USA_B21 = r"Data\INI\Object\Specter\United States Of America\AmericaJetB21Clean.ini"
CHINA_H6K = r"Data\INI\Object\Specter\PLA\Airforce\H6K.ini"
USA_AH1Z = r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaHelicopterAH1Z.ini"

AH1Z_REQUIRED = [
    r"Art\W3D\LSFAH1Z.W3D",
    r"Art\W3D\LSFAH1Zd.W3D",
    r"Art\W3D\LSFAH1Zk.W3D",
    r"Art\W3D\LSFAH1ZAIM9.W3D",
    r"Art\Textures\LSFAH1Z.dds",
    r"Art\Textures\LSFAH1Zd.dds",
    r"Art\Textures\LSFAH1Zk.dds",
    r"Art\Textures\AH1ZTB.tga",
]

DONOR_PROTECTED = [
    USA_B21,
    r"Data\INI\Object\Specter\United States Of America\AmericaJetB21A.ini",
    CHINA_H6K,
    r"Data\INI\Object\Specter\PLA\Airforce\H20.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\H20A.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\JH7A2.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\ChinaBomberH6K_B21A.ini",
    USA_AH1Z,
    P_IRAQ_MR,
    P_WEAPON,
]

NEW_SPEC = [
    "SPEC_VietnamJetMig29S",
    "SPEC_VietnamJetMi17",
    "SPEC_Syria_Mig29A",
    "SPEC_Syria_MirageF1",
    "SPEC_Syria_Su25K",
    "SPEC_Syria_Mi8T",
    "SPEC_SyriaBomberH6K",
]


def norm(name: str) -> str:
    return name.replace("/", "\\")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_big_list(path: Path) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries: list[tuple[str, bytes]] = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded_names: list[bytes] = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded_names.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded_names):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries: list[tuple[str, bytes]], target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 packed path, got {len(hits)}")
    return hits[0]


def find_index_opt(entries: list[tuple[str, bytes]], target: str) -> int | None:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) > 1:
        raise SystemExit(f"{target}: expected <=1 packed path, got {len(hits)}")
    return hits[0] if hits else None


def raw_of(entries, target) -> bytes:
    return entries[find_index(entries, target)][1]


def text_of(entries, target) -> str:
    return raw_of(entries, target).decode("latin1", errors="replace")


def set_text(entries, target, text: str) -> None:
    i = find_index(entries, target)
    name = entries[i][0]
    entries[i] = (name, text.encode("latin1", errors="replace"))


def add_file(entries, name: str, blob: bytes) -> None:
    n = norm(name)
    if any(norm(x).lower() == n.lower() for x, _ in entries):
        raise SystemExit(f"already packed: {name}")
    entries.append((n, blob))


def put_file(entries, name: str, blob: bytes) -> str:
    """Replace existing path or append. Returns 'replace' or 'add'."""
    n = norm(name)
    i = find_index_opt(entries, n)
    if i is None:
        entries.append((n, blob))
        return "add"
    entries[i] = (entries[i][0], blob)
    return "replace"


def file_nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def to_nl(s: str, nl: str) -> str:
    return s.replace("\r\n", "\n").replace("\n", nl)


def must_replace_once(text: str, old: str, new: str, label: str) -> str:
    nl = file_nl(text)
    old = to_nl(old, nl)
    new = to_nl(new, nl)
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly 1 occurrence, got {n}; OLD={old[:220]!r}")
    return text.replace(old, new, 1)


def patch_button_image(text: str, button: str, new_image: str, label: str) -> str:
    m = re.search(rf"(?im)^CommandButton\s+{re.escape(button)}\s*$", text)
    if not m:
        raise SystemExit(f"{label}: missing CommandButton {button}")
    m2 = re.search(r"(?im)^CommandButton\s+\S+", text[m.end() :])
    end = m.end() + m2.start() if m2 else len(text)
    block = text[m.start() : end]
    new_block, n = re.subn(
        r"(?im)^(\s*ButtonImage\s*=\s*)\S+",
        rf"\1{new_image}",
        block,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"{label}: ButtonImage replace failed for {button} n={n}")
    return text[: m.start()] + new_block + text[end:]


def patch_object_portraits(text: str, portrait: str) -> str:
    text2, n1 = re.subn(r"(?im)^(\s*SelectPortrait\s*=\s*)\S+", rf"\1{portrait}", text, count=1)
    text3, n2 = re.subn(r"(?im)^(\s*ButtonImage\s*=\s*)\S+", rf"\1{portrait}", text2, count=1)
    if n1 != 1 or n2 != 1:
        raise SystemExit(f"portrait patch failed n1={n1} n2={n2}")
    return text3


def unpack565(c: int) -> tuple[int, int, int]:
    r = ((c >> 11) & 31) * 255 // 31
    g = ((c >> 5) & 63) * 255 // 63
    b = (c & 31) * 255 // 31
    return r, g, b


def decode_dxt1_block(block: bytes, img: Image.Image, x: int, y: int, w: int, h: int) -> None:
    c0, c1 = struct.unpack_from("<HH", block, 0)
    bits = struct.unpack_from("<I", block, 4)[0]
    cols = [unpack565(c0), unpack565(c1)]
    if c0 > c1:
        cols.append(tuple((2 * a + b) // 3 for a, b in zip(cols[0], cols[1])))
        cols.append(tuple((a + 2 * b) // 3 for a, b in zip(cols[0], cols[1])))
        alphas = (255, 255, 255, 255)
    else:
        cols.append(tuple((a + b) // 2 for a, b in zip(cols[0], cols[1])))
        cols.append((0, 0, 0))
        alphas = (255, 255, 255, 0)
    for i in range(16):
        px = x + (i % 4)
        py = y + (i // 4)
        if px >= w or py >= h:
            continue
        idx = (bits >> (2 * i)) & 3
        r, g, b = cols[idx]
        img.putpixel((px, py), (r, g, b, alphas[idx]))


def decode_dxt5_block(block: bytes, img: Image.Image, x: int, y: int, w: int, h: int) -> None:
    a0, a1 = block[0], block[1]
    abits = int.from_bytes(block[2:8], "little")
    alphas = [a0, a1]
    if a0 > a1:
        for i in range(1, 7):
            alphas.append(((7 - i) * a0 + i * a1) // 7)
    else:
        for i in range(1, 5):
            alphas.append(((5 - i) * a0 + i * a1) // 5)
        alphas += [0, 255]
    c0, c1 = struct.unpack_from("<HH", block, 8)
    bits = struct.unpack_from("<I", block, 12)[0]
    cols = [unpack565(c0), unpack565(c1)]
    cols.append(tuple((2 * a + b) // 3 for a, b in zip(cols[0], cols[1])))
    cols.append(tuple((a + 2 * b) // 3 for a, b in zip(cols[0], cols[1])))
    for i in range(16):
        px = x + (i % 4)
        py = y + (i // 4)
        if px >= w or py >= h:
            continue
        idx = (bits >> (2 * i)) & 3
        aidx = (abits >> (3 * i)) & 7
        r, g, b = cols[idx]
        img.putpixel((px, py), (r, g, b, alphas[aidx]))


def load_dds(blob: bytes) -> Image.Image:
    if blob[:4] != b"DDS ":
        raise SystemExit("not DDS")
    h = struct.unpack_from("<I", blob, 12)[0]
    w = struct.unpack_from("<I", blob, 16)[0]
    fourcc = blob[84:88]
    off = 128
    img = Image.new("RGBA", (w, h))
    if fourcc == b"DXT1":
        block_size, decoder = 8, decode_dxt1_block
    elif fourcc in (b"DXT4", b"DXT5"):
        block_size, decoder = 16, decode_dxt5_block
    elif fourcc in (b"DXT2", b"DXT3"):
        block_size = 16

        def decoder(block, img, x, y, w, h):
            decode_dxt1_block(block[8:], img, x, y, w, h)
            alpha = block[:8]
            for i in range(16):
                px = x + (i % 4)
                py = y + (i // 4)
                if px >= w or py >= h:
                    continue
                a = (alpha[i // 2] >> (4 * (i % 2))) & 0xF
                r, g, b, _ = img.getpixel((px, py))
                img.putpixel((px, py), (r, g, b, a * 17))

    else:
        raise SystemExit(f"unhandled DDS fourcc {fourcc!r}")
    bw, bh = (w + 3) // 4, (h + 3) // 4
    p = off
    for by in range(bh):
        for bx in range(bw):
            decoder(blob[p : p + block_size], img, bx * 4, by * 4, w, h)
            p += block_size
    return img


def load_tga(blob: bytes) -> Image.Image:
    idlen, itype = blob[0], blob[2]
    w, h = struct.unpack_from("<HH", blob, 12)
    bpp = blob[16]
    desc = blob[17]
    off = 18 + idlen
    row = w * (bpp // 8)
    pixels = blob[off : off + row * h]
    if itype != 2:
        raise SystemExit(f"tga type {itype}")
    if bpp == 32:
        im = Image.frombytes("RGBA", (w, h), pixels)
        b, g, r, a = im.split()
        im = Image.merge("RGBA", (r, g, b, a))
    elif bpp == 24:
        im = Image.frombytes("RGB", (w, h), pixels)
        b, g, r = im.split()
        im = Image.merge("RGB", (r, g, b)).convert("RGBA")
    else:
        raise SystemExit(f"tga bpp {bpp}")
    if not (desc & 0x20):
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    return im


def cover_crop(im: Image.Image, w: int, h: int, bias: float = 0.5) -> Image.Image:
    im = im.convert("RGBA")
    scale = max(w / im.width, h / im.height)
    nw, nh = max(w, int(im.width * scale + 0.5)), max(h, int(im.height * scale + 0.5))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = int((nw - w) * bias)
    top = int((nh - h) * 0.42)
    left = max(0, min(left, nw - w))
    top = max(0, min(top, nh - h))
    return im.crop((left, top, left + w, top + h))


def write_spec_tga(im: Image.Image) -> bytes:
    im = im.convert("RGBA")
    if im.size != (150, 113):
        im = cover_crop(im, 150, 113)
    header = bytearray(18)
    header[2] = 2
    struct.pack_into("<HH", header, 12, 150, 113)
    header[16] = 32
    header[17] = 0x28
    return bytes(header) + im.tobytes("raw", "BGRA")


def write_rgba_tga(im: Image.Image) -> bytes:
    im = im.convert("RGBA")
    w, h = im.size
    header = bytearray(18)
    header[2] = 2
    struct.pack_into("<HH", header, 12, w, h)
    header[16] = 32
    header[17] = 0x28
    return bytes(header) + im.tobytes("raw", "BGRA")


def mappedimage_block(name: str) -> str:
    return (
        f"MappedImage {name}\r\n"
        f"  Texture = {name}.tga\r\n"
        "  TextureWidth = 150\r\n"
        "  TextureHeight = 113\r\n"
        "  Coords = Left:0 Top:0 Right:150 Bottom:113\r\n"
        "  Status = NONE\r\n"
        "End\r\n\r\n"
    )


def art_lookup(art: list[tuple[str, bytes]]) -> dict[str, int]:
    idx: dict[str, int] = {}
    for i, (n, _) in enumerate(art):
        idx[norm(n).lower()] = i
        idx[Path(n.replace("\\", "/")).name.lower()] = i
    return idx


def art_blob(art: list[tuple[str, bytes]], idx: dict[str, int], key: str) -> bytes:
    k = key.replace("/", "\\").lower()
    if k not in idx:
        k = Path(key.replace("\\", "/")).name.lower()
    if k not in idx:
        raise SystemExit(f"missing ART {key}")
    return art[idx[k]][1]


def png_cameo(name: str) -> Image.Image:
    p = CAMEO_DIR / name
    if not p.exists():
        raise SystemExit(f"missing cameo {p}")
    return Image.open(p).convert("RGBA")


def main() -> int:
    data_sha = sha256_file(SRC_DATA)
    art_sha = sha256_file(SRC_ART)
    if data_sha != EXPECTED_DATA_SHA:
        raise SystemExit(f"DATA SHA mismatch {data_sha}")
    if art_sha != EXPECTED_ART_SHA:
        raise SystemExit(f"ART SHA mismatch {art_sha}")

    data = read_big_list(SRC_DATA)
    art = read_big_list(SRC_ART)
    data_hashes = {norm(n).lower(): hashlib.sha256(b).hexdigest() for n, b in data}
    art_hashes = {norm(n).lower(): hashlib.sha256(b).hexdigest() for n, b in art}
    aidx = art_lookup(art)

    protected = {norm(x).lower() for x in DONOR_PROTECTED}
    donor_before = {p: hashlib.sha256(raw_of(data, p)).hexdigest() for p in DONOR_PROTECTED}

    # --- DATA: Yak-130 model LSFT50d/LSFT50D -> dedicated LSFYAK130 trainer ---
    yak = text_of(data, VN_YAK)
    yak = must_replace_once(
        yak,
        "    DefaultConditionState\n      Model               = LSFT50d\n",
        "    DefaultConditionState\n      Model               = LSFYAK130\n",
        "yak130 default model",
    )
    yak2, n_dmg = re.subn(
        r"(?m)^(\s*Model\s+=\s+)LSFT50D\s*$",
        r"\1LSFYAK130d",
        yak,
    )
    if n_dmg != 5:
        raise SystemExit(f"yak130 damaged model replacements {n_dmg} != 5")
    if re.search(r"(?i)LSFT50", yak2):
        raise SystemExit("yak130 still references LSFT50")
    if "SPEC_VietnamJetYak130" not in yak2:
        raise SystemExit("yak130 button image lost")
    if not re.search(r"(?im)^Scale\s*=\s*0\.82\s*$", yak2):
        raise SystemExit("yak130 scale changed")
    set_text(data, VN_YAK, yak2)

    # portraits / buttons (visual refs only)
    set_text(data, VN_MIG29, patch_object_portraits(text_of(data, VN_MIG29), "SPEC_VietnamJetMig29S"))
    set_text(data, VN_MI17, patch_object_portraits(text_of(data, VN_MI17), "SPEC_VietnamJetMi17"))
    set_text(data, VN_MI8, patch_object_portraits(text_of(data, VN_MI8), "SPEC_VietnamJetMi17"))
    set_text(data, SY_MIG29, patch_object_portraits(text_of(data, SY_MIG29), "SPEC_Syria_Mig29A"))
    set_text(data, SY_MIRAGE, patch_object_portraits(text_of(data, SY_MIRAGE), "SPEC_Syria_MirageF1"))
    set_text(data, SY_SU25, patch_object_portraits(text_of(data, SY_SU25), "SPEC_Syria_Su25K"))
    set_text(data, SY_MI8, patch_object_portraits(text_of(data, SY_MI8), "SPEC_Syria_Mi8T"))
    set_text(data, SY_H6K, patch_object_portraits(text_of(data, SY_H6K), "SPEC_SyriaBomberH6K"))

    if not re.search(r"(?im)^Scale\s*=\s*1\.18\s*$", text_of(data, SY_MIG21)):
        raise SystemExit("syria mig21bis scale lost")
    if not re.search(r"(?im)^Scale\s*=\s*1\.08\s*$", text_of(data, SY_MIG21MF)):
        raise SystemExit("syria mig21mf scale lost")

    btn = text_of(data, P_CMDBTN)
    btn = patch_button_image(btn, "Command_ConstructVietnamJetMig29S", "SPEC_VietnamJetMig29S", "vn mig29 btn")
    btn = patch_button_image(btn, "Command_ConstructVietnamJetMi17", "SPEC_VietnamJetMi17", "vn mi17 btn")
    btn = patch_button_image(btn, "Command_ConstructVietnamJetMi8", "SPEC_VietnamJetMi17", "vn mi8 btn")
    btn = patch_button_image(btn, "Command_ConstructSyria_Mig-29A", "SPEC_Syria_Mig29A", "sy mig29 btn")
    btn = patch_button_image(btn, "Command_ConstructSyria_MirageF1_Bq", "SPEC_Syria_MirageF1", "sy mirage btn")
    btn = patch_button_image(btn, "Command_ConstructSyria_Su-25K", "SPEC_Syria_Su25K", "sy su25 btn")
    btn = patch_button_image(btn, "Command_ConstructSyria_Mi-8T", "SPEC_Syria_Mi8T", "sy mi8 btn")
    btn = patch_button_image(btn, "Command_ConstructSyriaBomberH6K", "SPEC_SyriaBomberH6K", "sy h6k btn")
    set_text(data, P_CMDBTN, btn)

    mapped = "; SPECTER1 Vietnam/Syria ART fix MappedImages. Unique names.\r\n\r\n"
    for name in NEW_SPEC:
        mapped += mappedimage_block(name)
    add_file(data, P_MAPPED, mapped.encode("latin1"))

    for p, h in donor_before.items():
        if hashlib.sha256(raw_of(data, p)).hexdigest() != h:
            raise SystemExit(f"protected donor changed: {p}")

    # --- ART: cameos ---
    chj7 = load_tga(art_blob(art, aidx, r"Art\Textures\CHJ7TB.tga"))
    j11 = load_tga(art_blob(art, aidx, r"Art\Textures\JIAN11TB.tga"))
    su24 = load_tga(art_blob(art, aidx, r"Art\Textures\SU24TB.tga"))
    h6k_photo = load_tga(art_blob(art, aidx, r"Art\Textures\CHNH6KTB.tga"))

    def spec(im: Image.Image, bias: float = 0.5) -> bytes:
        return write_spec_tga(cover_crop(im, 150, 113, bias=bias))

    cameos: dict[str, bytes] = {
        "SPEC_VietnamJetYak130": spec(png_cameo("cameo_yak130.png"), 0.45),
        "SPEC_VietnamJetF5E": spec(png_cameo("cameo_f5e.png"), 0.48),
        "SPEC_VietnamJetL39": spec(png_cameo("cameo_l39.png"), 0.50),
        "SPEC_VietnamJetMig21": spec(chj7, 0.40),
        "SPEC_VietnamJetMig21bis": spec(chj7, 0.60),
        "SPEC_VietnamJetSu22": spec(png_cameo("cameo_su22.png"), 0.42),
        "SPEC_VietnamJetSu22M4": spec(png_cameo("cameo_su22.png"), 0.58),
        "SPEC_VietnamJetSu27": spec(j11, 0.40),
        "SPEC_VietnamJetSu27UB": spec(j11, 0.55),
        "SPEC_VietnamJetSu30": spec(j11, 0.48),
        "SPEC_VietnamJetSu30MK2": spec(j11, 0.62),
        "SPEC_VietnamJetMig29S": spec(png_cameo("cameo_mig29.png"), 0.46),
        "SPEC_VietnamJetMi17": spec(png_cameo("cameo_mi8.png"), 0.50),
        "SPEC_SyriaJetJ7": spec(chj7, 0.52),
        "SPEC_SyriaJetL39": spec(png_cameo("cameo_l39.png"), 0.55),
        "SPEC_SyriaJetMig21": spec(chj7, 0.35),
        "SPEC_SyriaJetMig21MF": spec(chj7, 0.65),
        "SPEC_SyriaJetMig23": spec(png_cameo("cameo_mig23.png"), 0.47),
        "SPEC_SyriaJetMig25": spec(png_cameo("cameo_mig25.png"), 0.50),
        "SPEC_SyriaJetSu22": spec(png_cameo("cameo_su22.png"), 0.38),
        "SPEC_SyriaJetSu22M4": spec(png_cameo("cameo_su22.png"), 0.66),
        "SPEC_SyriaJetSu24": spec(su24, 0.50),
        "SPEC_Syria_Mig29A": spec(png_cameo("cameo_mig29.png"), 0.54),
        "SPEC_Syria_MirageF1": spec(png_cameo("cameo_miragef1.png"), 0.50),
        "SPEC_Syria_Su25K": spec(png_cameo("cameo_su25.png"), 0.48),
        "SPEC_Syria_Mi8T": spec(png_cameo("cameo_mi8.png"), 0.58),
        "SPEC_SyriaBomberH6K": spec(h6k_photo, 0.50),
    }
    for name, blob in cameos.items():
        if len(blob) != 67818:
            raise SystemExit(f"{name} TGA size {len(blob)} != 67818")
        put_file(art, rf"Art\Textures\{name}.tga", blob)

    # --- ART: Yak-130 dedicated trainer mesh (Italy M-346 donor AVHawk, not LSFT50/PAK FA) ---
    hawk = art_blob(art, aidx, r"Art\W3D\AVHawk.W3D")
    hawk_d = art_blob(art, aidx, r"Art\W3D\AVHawk_D.W3D")
    put_file(art, r"Art\W3D\LSFYAK130.W3D", hawk)
    put_file(art, r"Art\W3D\LSFYAK130d.W3D", hawk_d)

    # --- ART: Mi-17 exact .tga aliases for W3D texture names ---
    mi17_tga_src = {
        r"Art\Textures\Egy_MI17.tga": r"Art\Textures\Egy_MI17.dds",
        r"Art\Textures\Egy_MI17D.tga": r"Art\Textures\Egy_MI17D.dds",
        r"Art\Textures\MI8BR.tga": r"Art\Textures\MI8BR.dds",
        r"Art\Textures\MI8_FR.tga": r"Art\Textures\MI8_FR.dds",
    }
    for dst, src in mi17_tga_src.items():
        put_file(art, dst, write_rgba_tga(load_dds(art_blob(art, aidx, src))))

    # --- ART: AH-1Z donor package (re-ship from /tmp/donor_heli) ---
    donor_map = {
        r"Art\W3D\LSFAH1Z.W3D": "LSFAH1Z.W3D",
        r"Art\W3D\LSFAH1Zd.W3D": "LSFAH1Zd.W3D",
        r"Art\W3D\LSFAH1Zk.W3D": "LSFAH1Zk.W3D",
        r"Art\W3D\LSFAH1ZAIM9.W3D": "LSFAH1ZAIM9.W3D",
        r"Art\Textures\LSFAH1Z.dds": "LSFAH1Z.dds",
        r"Art\Textures\LSFAH1Zd.dds": "LSFAH1Zd.dds",
        r"Art\Textures\LSFAH1Zk.dds": "LSFAH1Zk.dds",
        r"Art\Textures\AH1ZTB.tga": "AH1ZTB.tga",
    }
    for dst, fn in donor_map.items():
        p = DONOR_HELI / fn
        if not p.exists():
            raise SystemExit(f"missing AH-1Z donor {p}")
        put_file(art, dst, p.read_bytes())

    # --- audits ---
    for req in AH1Z_REQUIRED:
        if find_index_opt(art, req) is None:
            raise SystemExit(f"AH-1Z missing {req}")
    for m in ("LSFYAK130", "LSFYAK130d", "Egy_MI17", "Egy_MI17D", "UVMig-21", "h6k", "LSFAH1Z"):
        if find_index_opt(art, rf"Art\W3D\{m}.W3D") is None:
            raise SystemExit(f"missing W3D {m}")
    for tex in (
        r"Art\Textures\Egy_MI17.tga",
        r"Art\Textures\MI8BR.tga",
        r"Art\Textures\MI8_FR.tga",
        r"Art\Textures\UVMig-21.dds",
        r"Art\Textures\h6k.tga",
        r"Art\Textures\CHNH6KTB.tga",
        r"Art\Textures\AH1ZTB.tga",
    ):
        if find_index_opt(art, tex) is None:
            raise SystemExit(f"missing texture {tex}")

    # placeholder check on replaced SPEC files
    for name in cameos:
        blob = raw_of(art, rf"Art\Textures\{name}.tga")
        im = load_tga(blob)
        # pink-stripe placeholders have near-uniform magenta columns; real photos do not
        px = list(im.getdata())
        unique = len({(p[0] // 16, p[1] // 16, p[2] // 16) for p in px[::20]})
        if unique < 12:
            raise SystemExit(f"{name} still looks like a placeholder (unique bins={unique})")

    cmdset = text_of(data, P_CMDSET)
    if "Command_ConstructVietnamJetYak130" not in cmdset:
        raise SystemExit("yak130 button id lost from CommandSet")
    if not re.search(r"(?im)^Object\s+VietnamJetYak130\b", text_of(data, VN_YAK)):
        raise SystemExit("yak130 object id lost")

    changed_data = []
    for n, b in data:
        h = hashlib.sha256(b).hexdigest()
        key = norm(n).lower()
        if key not in data_hashes or data_hashes[key] != h:
            changed_data.append(n)
    changed_data.sort()

    changed_art = []
    added_art = []
    for n, b in art:
        h = hashlib.sha256(b).hexdigest()
        key = norm(n).lower()
        if key not in art_hashes:
            added_art.append(n)
            changed_art.append(n)
        elif art_hashes[key] != h:
            changed_art.append(n)
    changed_art.sort()
    added_art.sort()

    data_blob = build_big_ordered(data)
    art_blob_out = build_big_ordered(art)
    new_data_sha = hashlib.sha256(data_blob).hexdigest()
    new_art_sha = hashlib.sha256(art_blob_out).hexdigest()
    if new_art_sha == EXPECTED_ART_SHA:
        raise SystemExit("ART SHA unchanged")
    if new_data_sha == EXPECTED_DATA_SHA:
        raise SystemExit("DATA SHA unchanged but model/icon refs were required")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_blob)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_blob_out)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(data_blob)
    (WS_OUT / "_SPEC_ART_ONE.big").write_bytes(art_blob_out)

    lines: list[str] = []
    p = lines.append
    p("SPECTER1 VIETNAM + SYRIA ART 01")
    p("BASELINE_DATA_SHA256 = " + EXPECTED_DATA_SHA)
    p("BASELINE_ART_SHA256 = " + EXPECTED_ART_SHA)
    p("NEW_DATA_SHA256 = " + new_data_sha)
    p("NEW_ART_SHA256 = " + new_art_sha)
    p("NEW_DATA_BYTES = " + str(len(data_blob)))
    p("NEW_ART_BYTES = " + str(len(art_blob_out)))
    p("NEW_DATA_FILE_COUNT = " + str(len(data)))
    p("NEW_ART_FILE_COUNT = " + str(len(art)))
    p("MODE = ART pack + minimal DATA model/icon reference edits on roster 01")
    p("")
    p("=== VIETNAM YAK-130 ===")
    p("DEDICATED_YAK130_W3D_IN_PRIOR_ART = NONE")
    p("WRONG_PRIOR_MODEL = LSFT50d (F22BODY PAK FA / Su-57 mesh + LSFT50d.dds stealth skin)")
    p("M346_FAMILY_INTENDED_DONOR = ItalyJetM346FA INI comment Donor ART AVHawk.W3D")
    p("NEW_MODEL = LSFYAK130 (clone of AVHawk.W3D conventional twin-seat jet trainer)")
    p("NEW_DAMAGED_MODEL = LSFYAK130d (clone of AVHawk_D.W3D)")
    p("NOT_USED = LSFT50 / LSFT50d / qsnt50 / t50t.tga (PAK FA / T-50 magazine art)")
    p("VIETNAM_YAK130_BUTTON_PRESERVED = SPEC_VietnamJetYak130")
    p("VIETNAM_YAK130_SIDE_PRESERVED = Vietnam")
    p("VIETNAM_YAK130_SCALE_PRESERVED = 0.82")
    p("VIETNAM_YAK130_WEAPONS_PRESERVED = YES")
    p("VIETNAM_YAK130_CAMEO = real Yak-130 / M-346 family photo, not pink placeholder")
    p("VIETNAM_YAK130_VISUAL_FIXED = YES")
    p("")
    p("=== VIETNAM AH-1Z ===")
    p("AH1Z_OBJECT = AmericaHelicopterAH1Z (USA unit; ART missing from original SPECTER1)")
    p("AH1Z_MODEL = LSFAH1Z / LSFAH1Zd / LSFAH1Zk")
    p("AH1Z_CAMEO = AH1ZTB.tga (real AH-1Z photo)")
    p("AH1Z_DONOR_RESPIPPED = YES from /tmp/donor_heli")
    p("AH1Z_WEAPONS_STATS_UNCHANGED = YES")
    p("AH1Z_ART_PRESENT = YES")
    p("")
    p("=== VIETNAM ICONS ===")
    p("PLACEHOLDER_SPEC_TGA_BEFORE = 67818-byte pink-stripe 150x113 images")
    p("REPLACED_VIETNAM_CAMEOS = SPEC_VietnamJetYak130, F5E, L39, Mig21, Mig21bis, Su22, Su22M4, Su27, Su27UB, Su30, Su30MK2, plus new SPEC_VietnamJetMig29S and SPEC_VietnamJetMi17")
    p("VIETNAM_ICONS_FIXED = YES")
    p("")
    p("=== VIETNAM MI-17 ===")
    p("MODEL = Egy_MI17 / Egy_MI17D (unchanged DATA refs)")
    p("PRIOR_BUGFIXES_KEPT = CAN_ATTACK + 16x_80mm_S8_Rockets_Mi17 + Egy_MI17D damaged")
    p("W3D_TEXTURE_NAMES = Egy_MI17.tga / MI8BR.tga / MI8_FR.tga")
    p("FIX = pack matching .tga aliases decoded from existing .dds skins")
    p("VIETNAM_MI17_ART_VERIFIED = YES")
    p("")
    p("=== SYRIA AIRCRAFT BUTTONS ===")
    p("PROBLEM = SPEC_SyriaJet* were pink placeholders; irq_* atlas tiles are mixed tank/building-sheet cameos")
    p("FIX = dedicated 150x113 aircraft photo cameos for every live Airfield/HeavyAirBase aircraft button")
    p("SYRIA_MIG29_BUTTON = SPEC_Syria_Mig29A")
    p("SYRIA_MIRAGE_BUTTON = SPEC_Syria_MirageF1")
    p("SYRIA_SU25_BUTTON = SPEC_Syria_Su25K")
    p("SYRIA_MI8_BUTTON = SPEC_Syria_Mi8T")
    p("SYRIA_H6K_BUTTON = SPEC_SyriaBomberH6K")
    p("SYRIA_SPEC_JET_BUTTONS = SPEC_SyriaJetMig21/MF/23/25/J7/Su22/M4/Su24/L39 replaced in ART")
    p("SYRIA_AIRCRAFT_BUTTONS_FIXED = YES")
    p("")
    p("=== SYRIA MIG-21 ===")
    p("SYRIA_MIG21BIS_OBJECT = SyriaJetMig21")
    p("SYRIA_MIG21BIS_MODEL = UVMig-21 / UVMig-21_D / UVMig-21_E")
    p("SYRIA_MIG21BIS_TEXTURE = UVMig-21.dds")
    p("SYRIA_MIG21BIS_SCALE_PRESERVED = 1.18")
    p("SYRIA_MIG21MF_OBJECT = SyriaJetMig21MF")
    p("SYRIA_MIG21MF_MODEL = UVMig-21 / UVMig-21_D / UVMig-21_E")
    p("SYRIA_MIG21MF_SCALE_PRESERVED = 1.08")
    p("SYRIA_MIG21_ART_VERIFIED = YES")
    p("")
    p("=== SYRIA CHINESE BOMBER ===")
    p("SYRIA_CHINESE_BOMBER_OBJECT = SyriaBomberH6K")
    p("SYRIA_CHINESE_BOMBER_MODEL = h6k")
    p("SYRIA_CHINESE_BOMBER_W3D = Art\\W3D\\h6k.W3D")
    p("SYRIA_CHINESE_BOMBER_TEXTURE = h6k.tga")
    p("SYRIA_CHINESE_BOMBER_PHOTO = CHNH6KTB.tga")
    p("SYRIA_CHINESE_BOMBER_CAMEO = SPEC_SyriaBomberH6K cropped from CHNH6KTB")
    p("CHINA_H6K_DONOR_UNCHANGED = YES")
    p("SYRIA_BOMBER_ART_VERIFIED = YES")
    p("")
    p("=== SAFETY ===")
    p("USA_RUSSIA_CHINA_DONOR_INI_UNCHANGED = YES")
    p("IRAQ_SU24MR_UNCHANGED = YES")
    p("WEAPON_INI_CHANGED = NO")
    p("GAMEPLAY_VALUES_CHANGED = NO")
    p("PREVIOUS_DATA_EDITS_REMOVED = NO")
    p("")
    p("CHANGED_DATA_PATHS =")
    for n in changed_data:
        p("  " + n)
    p("")
    p("CHANGED_ART_FILES =")
    for n in changed_art:
        p("  " + n)
    p("CHANGED_ART_FILE_COUNT = " + str(len(changed_art)))
    p("ADDED_ART_FILES =")
    for n in added_art:
        p("  " + n)
    p("")
    p("DATA_CHANGED = YES")
    p("ART_CHANGED = YES")
    p("INGAME_TESTED = NO")
    p("RELEASE_OVERWRITES_PREVIOUS = NO")

    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 Vietnam + Syria ART 01

Continues from SPECTER1_Vietnam_Syria_Roster_01. Does not revert roster DATA gameplay.
Does not modify USA/Russia/China donor files. New GitHub Release (does not overwrite).

Vietnam:
- Yak-130 no longer uses LSFT50/LSFT50d (PAK FA / T-50 stealth mesh). Dedicated LSFYAK130 / LSFYAK130d cloned from the Italy M-346 family intended donor AVHawk (conventional jet trainer). Button ID SPEC_VietnamJetYak130 kept. Scale 0.82 and weapons kept.
- Yak-130 selection icon replaced (was pink-stripe placeholder) with a Yak-130 / M-346 family photo cameo.
- AH-1Z Viper ART package re-shipped (LSFAH1Z W3D/textures + AH1ZTB cameo). Weapons/stats unchanged.
- All live Vietnam SPEC_* fighter cameos replaced. MiG-29 and Mi-17 buttons now use aircraft photo cameos instead of UV-sheet / mixed atlas tiles.
- Mi-17 Egy_MI17 W3D texture names packed as .tga aliases. Prior Mi-17 fire/CAN_ATTACK DATA kept.

Syria:
- Aircraft production buttons now use dedicated aircraft photo cameos, not tank/building atlas tiles or pink placeholders.
- MiG-21bis / MiG-21MF keep scale 1.18 / 1.08. UVMig-21 model+texture verified present.
- H-6K bomber W3D/texture/photo verified; button uses a CHNH6KTB crop.

INGAME_TESTED = NO
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")

    zpath = WS_OUT / "SPECTER1_Vietnam_Syria_ART_01.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
    (OUT_DIR / "SPECTER1_Vietnam_Syria_ART_01.zip").write_bytes(zpath.read_bytes())

    print(audit)
    print("WROTE DATA", len(data_blob), new_data_sha)
    print("WROTE ART", len(art_blob_out), new_art_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
