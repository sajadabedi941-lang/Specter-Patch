#!/usr/bin/env python3
"""Restore original Global Store construct/buy cameo TGAs as a 0_ ART overlay.

Live DATA (cc-vt72b-nk-hwasong) already first-wins:
  CommandButton.ini  -> ButtonImage specbtn_mic_* / Button_GlobalMarket
  MappedImages       -> Texture = specbtn_mic_*.tga / Button_GlobalMarket.tga
Those TGA files are absent from the repo split-zip ART (445,953,809 B, 0 specbtn)
and were only packed in PR #693 ART (SHA e796fadc..., 19 TGA).

Later DATA-only releases (#710-#720) never re-shipped ART. Full Release ART ONE
is a different 2.1 GiB archive. Replacing it with the 447 MB #693 ART would drop
models. Unique TGA paths are first-won by the first *.big (game.dat _stricmp,
replace=0). A 0_ overlay sorts before _SPEC_ART_ONE.big / INIZH.big.

This copies the original #693 Art\\Textures TGA bytes (no reconvert, no new art)
into 0_SPECTER_GlobalStoreCameos.big. Radar drone specbtn_heron/mq4/orlan/shahed
are out of scope. CommandSet.ini / CommandButton.ini / DATA BIG are not modified.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_ART = Path("/tmp/construct-art/_SPEC_ART_ONE.big")
SRC_ART_SHA = "e796fadcae1d0184a1e79e95e32a986782562c8040c13720873916a98fe9631f"
DATA_BIG = ROOT / "Release/CC_VT72B_NK_HWASONG/_SPEC_DATA_ONE.big"
DATA_SHA = "52baa018c53015e90bf55b1451a33d22cad9de0951b4924168287129eeb2144a"
OUT_DIR = ROOT / "Release/GS_CAMEO_RESTORE"
OUT_BIG = OUT_DIR / "0_SPECTER_GlobalStoreCameos.big"
TGA_DIR = OUT_DIR / "tga"

# Global Store construct + shop only. Radar drone cameos are not this task.
TGA_NAMES = (
    "Button_GlobalMarket.tga",
    "specbtn_mic_arrow.tga",
    "specbtn_mic_tpy2.tga",
    "specbtn_mic_92n6r.tga",
    "specbtn_mic_s400.tga",
    "specbtn_mic_pantsir.tga",
    "specbtn_mic_krasukha.tga",
    "specbtn_mic_96l6tsp.tga",
    "specbtn_mic_s500.tga",
    "specbtn_mic_hq9.tga",
    "specbtn_mic_ht233.tga",
    "specbtn_mic_trml4d.tga",
    "specbtn_mic_irist.tga",
    "specbtn_mic_ustpy2.tga",
    "specbtn_mic_thaad.tga",
)

BUTTONS = (
    ("Command_ConstructIraq_MIC", "Button_GlobalMarket"),
    ("Command_ConstructAmerica_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructBritain_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructChina_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructFrance_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructGermany_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructIndia_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructIran_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructIsrael_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructItaly_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructJapan_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructLibya_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructNato_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructNorthKorea_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructPakistan_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructRussia_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructSaudiArabia_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructSouthAfrica_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructSouthKorea_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructSweden_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructSyria_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructTurkey_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructUAE_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructUkraine_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructVietnam_GlobalStore", "Button_GlobalMarket"),
    ("Command_ConstructIraq_MIC_Arrow", "specbtn_mic_arrow"),
    ("Command_ConstructIraq_MIC_AN_TPY2", "specbtn_mic_tpy2"),
    ("Command_ConstructIraq_MIC_92N6R", "specbtn_mic_92n6r"),
    ("Command_ConstructIraq_MIC_S400", "specbtn_mic_s400"),
    ("Command_ConstructIraq_MIC_PantsirS1M", "specbtn_mic_pantsir"),
    ("Command_ConstructIraq_MIC_Krasukha4", "specbtn_mic_krasukha"),
    ("Command_ConstructIraq_MIC_96L6TSP", "specbtn_mic_96l6tsp"),
    ("Command_ConstructIraq_MIC_S500", "specbtn_mic_s500"),
    ("Command_ConstructIraq_MIC_HQ9", "specbtn_mic_hq9"),
    ("Command_ConstructIraq_MIC_HT233", "specbtn_mic_ht233"),
    ("Command_ConstructIraq_MIC_TRML4D", "specbtn_mic_trml4d"),
    ("Command_ConstructIraq_MIC_IRIST", "specbtn_mic_irist"),
    ("Command_ConstructIraq_MIC_US_AN_TPY2", "specbtn_mic_ustpy2"),
    ("Command_ConstructIraq_MIC_THAAD", "specbtn_mic_thaad"),
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


def is_tga128(blob: bytes) -> bool:
    if len(blob) < 18 + 128 * 128 * 4:
        return False
    # uncompressed truecolor, 128x128, 32-bit
    return blob[2] == 2 and struct.unpack_from("<HH", blob, 12) == (128, 128) and blob[16] == 32


def main() -> None:
    if not SRC_ART.is_file():
        raise SystemExit(f"missing #693 ART {SRC_ART}")
    art_blob = SRC_ART.read_bytes()
    require(hashlib.sha256(art_blob).hexdigest() == SRC_ART_SHA, "source ART sha mismatch")
    require(DATA_BIG.is_file() and hashlib.sha256(DATA_BIG.read_bytes()).hexdigest() == DATA_SHA, "DATA BIG sha mismatch")

    art = read_big(SRC_ART)
    data = read_big(DATA_BIG)
    cs = data[r"Data\INI\CommandSet.ini"].decode("latin1")
    cb = data[r"Data\INI\CommandButton.ini"].decode("latin1")
    mapped = data[r"Data\INI\MappedImages\HandCreated\SpecterUavMicCameos_Images.INI"].decode("latin1")
    mapped_gm = data[r"Data\INI\MappedImages\HandCreated\IraqConstructFix_Images.INI"].decode("latin1")

    packed: dict[str, bytes] = {}
    TGA_DIR.mkdir(parents=True, exist_ok=True)
    shas: dict[str, str] = {}
    for name in TGA_NAMES:
        key = "Art\\Textures\\" + name
        require(key in art, f"missing original TGA {key}")
        blob = art[key]
        require(is_tga128(blob), f"not 128x128 32-bit TGA: {name}")
        packed[key] = blob
        (TGA_DIR / name).write_bytes(blob)
        shas[name] = hashlib.sha256(blob).hexdigest()
    require(len(set(shas.values())) == len(shas), "duplicate TGA payloads")
    require("specbtn_heron.tga" not in {Path(k).name for k in packed}, "radar drone TGA leaked")

    # DATA refs already correct — do not rewrite CommandButton / CommandSet
    for btn, image in BUTTONS:
        require(f"CommandButton {btn}" in cb, f"missing button {btn}")
        # first (only) ButtonImage after that header
        idx = cb.index(f"CommandButton {btn}")
        end = cb.find("\nEnd", idx)
        block = cb[idx:end]
        require(f"ButtonImage   = {image}" in block or f"ButtonImage   = {image}\r" in block,
                f"{btn} ButtonImage is not {image}: {block}")
        if image.startswith("specbtn_"):
            require(f"MappedImage {image}" in mapped, f"MappedImage missing {image}")
            require(f"Texture = {image}.tga" in mapped, f"MappedImage texture mismatch {image}")
        else:
            require(f"MappedImage {image}" in mapped_gm, f"GM MappedImage missing {image}")
            require(f"Texture = {image}.tga" in mapped_gm, f"GM texture mismatch {image}")

    require("Iraq_MICCommandSet" in cs, "Iraq_MICCommandSet missing")
    require("Command_ConstructIraq_MIC_Arrow" in cs, "shop Arrow slot missing")
    require("Japan_CommandCenterCommandSet" in cs, "#720 JP CC missing")
    require("Command_ConstructNorthKorea_Hwasong15BB" in cs, "#720 NK missile missing")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_blob = build_big(packed)
    digest = hashlib.sha256(out_blob).hexdigest()
    OUT_BIG.write_bytes(out_blob)
    (OUT_DIR / "0_SPECTER_GlobalStoreCameos.big.sha256").write_text(digest + "\n", encoding="ascii")
    # copy live INIs unchanged for a compatible install
    for name, key in (("CommandSet.ini", r"Data\INI\CommandSet.ini"),
                      ("CommandButton.ini", r"Data\INI\CommandButton.ini")):
        (OUT_DIR / name).write_bytes(data[key])
        (OUT_DIR / f"{name}.sha256").write_text(
            hashlib.sha256(data[key]).hexdigest() + "\n", encoding="ascii"
        )
    (OUT_DIR / "tga.sha256").write_text(
        "\n".join(f"{shas[n]}  {n}" for n in TGA_NAMES) + "\n", encoding="ascii"
    )
    rebuilt = read_big(OUT_BIG)
    require(set(rebuilt) == set(packed), "overlay entry mismatch")
    for k, v in packed.items():
        require(rebuilt[k] == v, f"overlay bytes changed {k}")
        require(k.startswith("Art\\Textures\\"), f"wrong path {k}")
    print("wrote", OUT_BIG, "bytes", len(out_blob), "sha256", digest)
    print("tgas", len(packed))


if __name__ == "__main__":
    main()
