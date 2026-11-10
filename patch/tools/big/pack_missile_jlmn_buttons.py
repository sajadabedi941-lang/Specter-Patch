#!/usr/bin/env python3
"""Wire factory J/L/M/N construct-button images to real patch assets.

Live DATA already has:
  slot 10  country J / Iraq CB_MISSILE_J
  slot 12  CB_FACTORY_SLOT_L = Factory_KhormsharOnce @ 20000
  slot 13  CB_FACTORY_SLOT_M = Factory_RS24YarsOnce @ 27000
  slot 14  CB_FACTORY_SLOT_N = Factory_DF41Once @ 30000

Requested ButtonImage names Neon / Futuristic / Nuclear are not in the
patch as textures. MappedImage aliases point at the existing slot TGA
from PR #571/#606 (specter_missile_j/l/m). N keeps pla_df41 (the DF-41
atlas cameo already in HandCreatedMappedImages.INI).

CommandSet.ini is not rewritten. #720 Command Centers and #721 Global
Store overlay are left alone. Iraq A–M production buttons are not copied
to other countries.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/CC_VT72B_NK_HWASONG/_SPEC_DATA_ONE.big"
SRC_SHA = "52baa018c53015e90bf55b1451a33d22cad9de0951b4924168287129eeb2144a"
OUT_DIR = ROOT / "Release/MISSILE_JLMN_BUTTONS"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
OUT_ART = OUT_DIR / "0_SPECTER_MissileJLMNCameos.big"
TGA_SRC = Path("/tmp/missile-jlmn-tga")
TGA_FOOTER = b"\x00" * 8 + b"TRUEVISION-XFILE.\x00"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_MAP = r"Data\INI\MappedImages\HandCreated\zSpecterJLMN_Images.INI"
K_L = r"Data\INI\Object\Specter\FactoryKLMN\Factory_KhormsharOnce.ini"
K_M = r"Data\INI\Object\Specter\FactoryKLMN\Factory_RS24YarsOnce.ini"
K_N = r"Data\INI\Object\Specter\FactoryKLMN\Factory_DF41Once.ini"

ALIASES = (
    ("Neon", "specter_missile_j.tga"),
    ("Futuristic", "specter_missile_l.tga"),
    ("Nuclear", "specter_missile_m.tga"),
)

J_BUTTON_RE = re.compile(
    r"(?m)^(CommandButton (?:CB_MISSILE_J|CB_[A-Z]+_MISSILE_J)\r?\n"
    r"(?:.*\r?\n)*?  ButtonImage   = )specter_missile_j(\r?\n)"
)


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index, blobs, offset = [], [], header_size
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


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("VALIDATE FAIL: " + msg)


def png_to_tga24(png: Path) -> bytes:
    im = Image.open(png).convert("RGB")
    require(im.size == (128, 128), f"{png} not 128x128")
    im = im.transpose(Image.FLIP_TOP_BOTTOM)
    raw = bytearray()
    for px in im.getdata():
        raw += bytes((px[2], px[1], px[0]))
    header = bytes([0, 0, 2]) + b"\x00" * 9 + struct.pack("<HH", 128, 128) + bytes([24, 0])
    return header + bytes(raw) + TGA_FOOTER


def is_tga128_24(blob: bytes) -> bool:
    if len(blob) < 18 + 128 * 128 * 3:
        return False
    return blob[2] == 2 and struct.unpack_from("<HH", blob, 12) == (128, 128) and blob[16] == 24


def patch_buttonimage(cb: str, button: str, image: str) -> str:
    m = re.search(rf"(?m)^CommandButton {re.escape(button)}\r?\n[\s\S]*?^End", cb)
    require(m is not None, f"missing {button}")
    block = m.group(0)
    new_block, n = re.subn(r"(?m)^(  ButtonImage   = )\S+", rf"\g<1>{image}", block, count=1)
    require(n == 1, f"ButtonImage not patched {button}")
    return cb[: m.start()] + new_block + cb[m.end() :]


def patch_portrait(ini: str, image: str) -> str:
    out, n1 = re.subn(r"(?m)^(  SelectPortrait\s+= )\S+", rf"\g<1>{image}", ini, count=1)
    out, n2 = re.subn(r"(?m)^(  ButtonImage\s+= )\S+", rf"\g<1>{image}", out, count=1)
    require(n1 == 1 and n2 == 1, "portrait fields missing")
    return out


def mapped_ini() -> str:
    parts = [
        "; SPECTER factory J/L/M construct cameos.\n",
        "; Requested ButtonImage names mapped to existing slot TGA (PR #571 / #606).\n",
        "; Texture files are the original specter_missile_j/l/m.tga. No new pixels.\n",
        "; N stays pla_df41 (HandCreatedMappedImages.INI).\n\n",
    ]
    for name, tex in ALIASES:
        parts.append(
            f"MappedImage {name}\n"
            f"  Texture = {tex}\n"
            f"  TextureWidth = 128\n"
            f"  TextureHeight = 128\n"
            f"  Coords = Left:0 Top:0 Right:128 Bottom:128\n"
            f"  Status = NONE\n"
            f"End\n\n"
        )
    return "".join(parts)


def main() -> None:
    require(SRC_BIG.is_file() and hashlib.sha256(SRC_BIG.read_bytes()).hexdigest() == SRC_SHA, "src DATA sha")
    files = read_big(SRC_BIG)
    cs = files[K_CS]
    cb = files[K_CB].decode("latin1")

    tga_j = (TGA_SRC / "specter_missile_j.tga").read_bytes()
    tga_l = (TGA_SRC / "specter_missile_l.tga").read_bytes()
    tga_m = png_to_tga24(TGA_SRC / "specter_missile_m.png")
    for name, blob in (("j", tga_j), ("l", tga_l), ("m", tga_m)):
        require(is_tga128_24(blob), f"bad TGA {name}")
    require(len({hashlib.sha256(x).hexdigest() for x in (tga_j, tga_l, tga_m)}) == 3, "duplicate TGA")

    # J buttons: only the J construct commands, not other specter_missile_j mentions
    cb2, n_j = J_BUTTON_RE.subn(r"\1Neon\2", cb)
    require(n_j >= 20, f"too few J buttons patched: {n_j}")
    cb2 = patch_buttonimage(cb2, "CB_FACTORY_SLOT_L", "Futuristic")
    cb2 = patch_buttonimage(cb2, "CB_FACTORY_SLOT_M", "Nuclear")
    # N already pla_df41
    m_n = re.search(r"(?m)^CommandButton CB_FACTORY_SLOT_N\r?\n[\s\S]*?^End", cb2)
    require(m_n is not None and "ButtonImage   = pla_df41" in m_n.group(0), "N image drifted")
    require("Object        = Factory_KhormsharOnce" in cb2, "L object")
    require("Object        = Factory_RS24YarsOnce" in cb2, "M object")
    require("Object        = Factory_DF41Once" in cb2, "N object")
    require("Object        = Iraq_AlMansour" in cb2, "Iraq J object")

    l_ini = patch_portrait(files[K_L].decode("latin1"), "Futuristic")
    m_ini = patch_portrait(files[K_M].decode("latin1"), "Nuclear")
    n_ini = files[K_N].decode("latin1")
    require("pla_df41" in n_ini, "N portrait")
    require("BuildCost       = 20000" in l_ini or "BuildCost = 20000" in l_ini, "L cost")
    require("27000" in m_ini, "M cost")
    require("30000" in n_ini, "N cost")

    files[K_CB] = cb2.encode("latin1")
    files[K_L] = l_ini.encode("latin1")
    files[K_M] = m_ini.encode("latin1")
    files[K_MAP] = mapped_ini().encode("latin1")
    require(files[K_CS] == cs, "CommandSet.ini mutated")

    cs_txt = cs.decode("latin1")
    require("Japan_CommandCenterCommandSet" in cs_txt, "#720 JP CC")
    require("Command_ConstructNorthKorea_Hwasong15BB" in cs_txt, "#720 NK")
    require("  10 = CB_MISSILE_J" in cs_txt, "Iraq J slot")
    require("  12 = CB_FACTORY_SLOT_L" in cs_txt, "Iraq L slot")
    require("Iraq_AlFahdMissileFactoryCommandSet" in cs_txt, "Iraq factory CS")
    # Iraq A-M buttons must not appear on other factory sets
    for name in re.findall(r"(?m)^CommandSet (\S+_MissileFactoryCommandSet)", cs_txt):
        if name.startswith("Iraq_"):
            continue
        body = re.search(rf"(?m)^CommandSet {re.escape(name)}\r?\n[\s\S]*?^End", cs_txt).group(0)
        require("CB_MISSILE_A" not in body, f"Iraq roster leaked into {name}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tga_dir = OUT_DIR / "tga"
    tga_dir.mkdir(exist_ok=True)
    (tga_dir / "specter_missile_j.tga").write_bytes(tga_j)
    (tga_dir / "specter_missile_l.tga").write_bytes(tga_l)
    (tga_dir / "specter_missile_m.tga").write_bytes(tga_m)

    art_map = {
        r"Art\Textures\specter_missile_j.tga": tga_j,
        r"Art\Textures\specter_missile_l.tga": tga_l,
        r"Art\Textures\specter_missile_m.tga": tga_m,
    }
    art_blob = build_big(art_map)
    data_blob = build_big(files)
    OUT_ART.write_bytes(art_blob)
    OUT_BIG.write_bytes(data_blob)
    (OUT_DIR / "CommandSet.ini").write_bytes(cs)
    (OUT_DIR / "CommandButton.ini").write_bytes(files[K_CB])
    (OUT_DIR / "zSpecterJLMN_Images.INI").write_bytes(files[K_MAP])

    for path in (OUT_BIG, OUT_ART, OUT_DIR / "CommandSet.ini", OUT_DIR / "CommandButton.ini"):
        (OUT_DIR / (path.name + ".sha256")).write_text(
            hashlib.sha256(path.read_bytes()).hexdigest() + "\n", encoding="ascii"
        )

    rebuilt = read_big(OUT_BIG)
    require(rebuilt[K_CS] == cs, "rebuilt CS drift")
    require("ButtonImage   = Neon" in rebuilt[K_CB].decode("latin1"), "Neon missing")
    require("ButtonImage   = Futuristic" in rebuilt[K_CB].decode("latin1"), "Futuristic missing")
    require("ButtonImage   = Nuclear" in rebuilt[K_CB].decode("latin1"), "Nuclear missing")
    require("ButtonImage   = pla_df41" in rebuilt[K_CB].decode("latin1"), "pla_df41 missing")
    print("DATA", len(data_blob), hashlib.sha256(data_blob).hexdigest())
    print("ART ", len(art_blob), hashlib.sha256(art_blob).hexdigest())
    print("J buttons", n_j)


if __name__ == "__main__":
    main()
