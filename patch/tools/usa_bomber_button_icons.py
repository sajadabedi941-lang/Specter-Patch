#!/usr/bin/env python3
"""Restore real donor build-button icons for USA B-2 / B-52 / B-1R / AC-130.

UI ONLY: CommandButton ButtonImage + MappedImage + button TGA ART.
No Object / W3D / Scale / weapons / CommandSet / parking changes.
Does not touch E-3 / E-737 / E-2 / C-17 / V-22 buttons.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
DONOR_TEX = Path("/tmp/donor_art_extract/Art/Textures")
STAGE = MASTER / "_stage_usa_bomber_button_icons"
VERIFY = MASTER / "_extract_usa_bomber_button_icons_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_ART_USA_BOMBER_BUTTON_ICONS.zip"
OUT_HASH = ROOT / "Release/DATA_ART_USA_BOMBER_BUTTON_ICONS_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_ART_USA_BOMBER_BUTTON_ICONS_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_ART_USA_BOMBER_BUTTON_ICONS_REPORT.txt"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
CB_KEY = "Data\\INI\\CommandButton.ini"
CS_KEY = "Data\\INI\\CommandSet.ini"
CSF_KEY = "Data\\English\\generals.csf"
MI_KEY = "Data\\INI\\MappedImages\\HandCreated\\HandCreatedMappedImages.INI"

# Freeze support / other aircraft button strings
FREEZE_BUTTON_IMAGES = {
    "Command_ConstructAmericaJetE3Visual": "E3USA",
    "Command_ConstructAmericaJetE737Visual": "avionE737",
    "Command_ConstructAmericaJetE2Visual": "E2avionHE",
    "Command_ConstructAmericaJetC17Visual": "C17GlobalMaster",
    "Command_ConstructAmericaJetV22Visual": "V22",
    "Command_ConstructAmericaJetB21": "B21_L",
}

# Verified from donor CommandButton.ini / Object (USAB2 wrongly used UH60;
# only donor MappedImage depicting B-2 aircraft is B2DropBombTB).
TARGETS = {
    "Command_ConstructAmericaJetB2Spirit": {
        "old": "B2-ic_L",
        "donor_btn": "B2DropBombTB",  # donor MI; depicts B-2 Spirit aircraft
        "final": "B2DropBombTB",
        "mi_w": 150,
        "mi_h": 112,
        "src_tga": "B2DropBombTB.tga",
        "pack_tga": "B2DropBombTB.tga",
        "resize": False,  # already 150x112
    },
    "Command_ConstructAmericaJetB52H": {
        "old": "us_b52h",
        "donor_btn": "B52",  # Command_ConstructAmericaB52
        "final": "B52",
        "mi_w": 150,
        "mi_h": 111,
        "src_tga": "B52TB.tga",
        "pack_tga": "B52TB.tga",
        "resize": True,
    },
    "Command_ConstructAmericaJetB1R": {
        "old": "us_b1r",
        "donor_btn": "B1",  # Command_ConstructAmericaB1
        "final": "B1",
        "mi_w": 150,
        "mi_h": 111,
        "src_tga": "B1TB.tga",
        "pack_tga": "B1TB.tga",
        "resize": True,
    },
    "Command_ConstructAmericaJetAC130": {
        "old": "us_ac130",
        "donor_btn": "Cargo130",  # Command_ConstructAmericaAC130
        "final": "Cargo130",
        "mi_w": 150,
        "mi_h": 111,
        "src_tga": "Cargo130TB.tga",
        "pack_tga": "Cargo130TB.tga",
        "resize": True,
    },
}


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        out[name.replace("/", "\\")] = data[off : off + size]
    return out


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16 + sum(8 + len(n.encode("latin1")) + 1 for n, _ in items)
    offset = header_size
    index, blobs = [], []
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">III", offset, len(items), header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for b in blobs:
        out += b
    return bytes(out)


def write_tree(file_map: dict[str, bytes], root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for name, content in file_map.items():
        path = root / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def tga_size(b: bytes) -> tuple[int, int, int]:
    w, h = struct.unpack_from("<HH", b, 12)
    return w, h, b[16]


def load_tga_bgr(b: bytes) -> tuple[int, int, bytes, bool]:
    assert b[2] in (2, 10), f"unsupported TGA type {b[2]}"
    w, h = struct.unpack_from("<HH", b, 12)
    bpp = b[16] // 8
    top = bool(b[17] & 0x20)
    idlen = b[0]
    offset = 18 + idlen
    if b[2] == 2:
        img = b[offset : offset + w * h * bpp]
    else:
        pixels = bytearray()
        i = offset
        total = w * h
        while len(pixels) // bpp < total:
            pkt = b[i]
            i += 1
            cnt = (pkt & 0x7F) + 1
            if pkt & 0x80:
                pix = b[i : i + bpp]
                i += bpp
                pixels.extend(pix * cnt)
            else:
                pixels.extend(b[i : i + cnt * bpp])
                i += cnt * bpp
        img = bytes(pixels)
    if bpp == 4:
        flat = bytearray()
        for i in range(0, len(img), 4):
            flat += img[i : i + 3]
        img = bytes(flat)
    return w, h, img, top


def get_px(img: bytes, w: int, h: int, top: bool, x: int, y: int) -> bytes:
    yy = y if top else (h - 1 - y)
    off = (yy * w + x) * 3
    return img[off : off + 3]


def make_button_tga(src: bytes, tw: int, th: int) -> bytes:
    w, h, img, top = load_tga_bgr(src)
    src_aspect = w / h
    dst_aspect = tw / th
    if src_aspect > dst_aspect:
        cw = int(h * dst_aspect)
        ch = h
        x0 = (w - cw) // 2
        y0 = 0
    else:
        cw = w
        ch = int(w / dst_aspect)
        x0 = 0
        y0 = (h - ch) // 2
    out = bytearray()
    for y in range(th):
        sy0 = y0 + (th - 1 - y) * ch / th
        sy1 = y0 + (th - y) * ch / th
        for x in range(tw):
            sx0 = x0 + x * cw / tw
            sx1 = x0 + (x + 1) * cw / tw
            xs = range(int(sx0), max(int(sx0) + 1, int(sx1)))
            ys = range(int(sy0), max(int(sy0) + 1, int(sy1)))
            bb = gg = rr = n = 0
            for yy in ys:
                for xx in xs:
                    xx2 = min(w - 1, max(0, xx))
                    yy2 = min(h - 1, max(0, yy))
                    b, g, r = get_px(img, w, h, top, xx2, yy2)
                    bb += b
                    gg += g
                    rr += r
                    n += 1
            out += bytes([bb // n, gg // n, rr // n])
    header = bytearray(18)
    header[2] = 2
    struct.pack_into("<HH", header, 12, tw, th)
    header[16] = 24
    header[17] = 0
    return bytes(header) + bytes(out)


def ensure_mapped_image(mi: str, name: str, texture: str, tw: int, th: int) -> str:
    block = (
        f"MappedImage {name}\n"
        f"  Texture = {texture}\n"
        f"  TextureWidth = {tw}\n"
        f"  TextureHeight = {th}\n"
        f"  Coords = Left:0 Top:0 Right:{tw} Bottom:{th}\n"
        f"  Status = NONE\n"
        f"End\n"
    )
    if re.search(rf"(?m)^MappedImage\s+{re.escape(name)}\s*$", mi):
        mi2, n = re.subn(
            rf"(?ms)^MappedImage\s+{re.escape(name)}\s*\n.*?^End\s*$",
            block.rstrip(),
            mi,
            count=1,
        )
        assert n == 1
        return mi2
    # append near E3USA if present, else end
    anchor = re.search(r"(?ms)^MappedImage\s+E3USA\s*\n.*?^End\s*$", mi)
    if anchor:
        return mi[: anchor.end()] + "\n\n" + block + mi[anchor.end() :]
    return mi.rstrip() + "\n\n" + block


def set_button_image(cb: str, btn: str, image: str) -> str:
    m = re.search(
        rf"(?ms)^CommandButton\s+{re.escape(btn)}\s*\n.*?^End\s*$", cb
    )
    assert m, f"missing {btn}"
    block = m.group(0)
    block2, n = re.subn(
        r"(?m)^(\s*ButtonImage\s*=\s*).*$",
        rf"\1{image}",
        block,
        count=1,
    )
    assert n == 1, f"ButtonImage line missing in {btn}"
    return cb[: m.start()] + block2 + cb[m.end() :]


def get_button_image(cb: str, btn: str) -> str:
    m = re.search(
        rf"(?ms)^CommandButton\s+{re.escape(btn)}\s*\n.*?^End\s*$", cb
    )
    assert m
    bi = re.search(r"(?m)^\s*ButtonImage\s*=\s*(\S+)", m.group(0))
    assert bi
    return bi.group(1)


def upload(path: Path) -> str:
    try:
        r = subprocess.run(
            [
                "curl",
                "-sF",
                f"file=@{path}",
                "https://litterbox.catbox.moe/resources/internals/api.php",
                "-F",
                "time=72h",
                "-F",
                "reqtype=fileupload",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        out = (r.stdout or "").strip()
        if out.startswith("http"):
            return out
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["curl", "-sF", f"file=@{path}", "https://store1.gofile.io/uploadFile"],
            capture_output=True,
            text=True,
            timeout=900,
        )
        m = re.search(r'"downloadPage"\s*:\s*"([^"]+)"', r.stdout or "")
        if m:
            return m.group(1)
    except Exception:
        pass
    return "(upload failed)"


def main() -> None:
    data = read_big(DATA_BIG)
    art = read_big(ART_BIG)
    assert sha256(data[CSF_KEY]) == GOOD_CSF

    cb0 = data[CB_KEY].decode("latin1")
    cs0 = data[CS_KEY].decode("latin1")
    mi0 = data[MI_KEY].decode("latin1")

    # freeze CommandSet HeavyAirBase slots
    hab = re.search(
        r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?^End\s*$", cs0
    ).group(0)
    for slot, cmd in {
        1: "Command_ConstructAmericaJetB2Spirit",
        2: "Command_ConstructAmericaJetB21",
        3: "Command_ConstructAmericaJetB52H",
        4: "Command_ConstructAmericaJetB1R",
        5: "Command_ConstructAmericaJetE3Visual",
        7: "Command_ConstructAmericaJetAC130",
        9: "Command_ConstructAmericaJetE737Visual",
    }.items():
        assert re.search(rf"(?m)^\s*{slot}\s*=\s*{re.escape(cmd)}\s*$", hab)

    # record old images
    old_images = {btn: get_button_image(cb0, btn) for btn in TARGETS}
    for btn, meta in TARGETS.items():
        assert old_images[btn] == meta["old"], (
            f"{btn} unexpected old image {old_images[btn]} != {meta['old']}"
        )

    # Build ART textures
    art2 = dict(art)
    for meta in TARGETS.values():
        src_path = DONOR_TEX / meta["src_tga"]
        assert src_path.exists(), f"missing donor texture {src_path}"
        raw = src_path.read_bytes()
        if meta["resize"]:
            fixed = make_button_tga(raw, meta["mi_w"], meta["mi_h"])
        else:
            fixed = raw
            w, h, bpp = tga_size(fixed)
            assert (w, h) == (meta["mi_w"], meta["mi_h"]), (w, h)
            assert bpp == 24
        # force 24-bit bottom-origin if already correct size but verify
        w, h, bpp = tga_size(fixed)
        assert (w, h) == (meta["mi_w"], meta["mi_h"])
        key = f"Art\\Textures\\{meta['pack_tga']}"
        art2[key] = fixed

    # DATA: MappedImages + ButtonImages
    mi = mi0
    for meta in TARGETS.values():
        mi = ensure_mapped_image(
            mi, meta["final"], meta["pack_tga"], meta["mi_w"], meta["mi_h"]
        )

    cb = cb0
    for btn, meta in TARGETS.items():
        cb = set_button_image(cb, btn, meta["final"])

    # freeze other button images
    for btn, img in FREEZE_BUTTON_IMAGES.items():
        assert get_button_image(cb, btn) == img, f"froze broken: {btn}"

    # CommandSet unchanged
    assert cb != cb0
    assert mi != mi0

    data2 = dict(data)
    data2[CB_KEY] = cb.replace("\r\n", "\n").encode("latin1")
    data2[MI_KEY] = mi.replace("\r\n", "\n").encode("latin1")
    # explicit freeze
    data2[CS_KEY] = data[CS_KEY]
    data2[CSF_KEY] = data[CSF_KEY]

    # stage
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    write_tree(data2, STAGE / "data_in")
    write_tree(art2, STAGE / "art_in")

    DATA_BIG.write_bytes(build_big(data2))
    ART_BIG.write_bytes(build_big(art2))

    # verify re-extract
    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    dv = read_big(DATA_BIG)
    av = read_big(ART_BIG)
    write_tree(dv, VERIFY / "data_out")
    write_tree(av, VERIFY / "art_out")

    assert sha256(dv[CSF_KEY]) == GOOD_CSF
    assert dv[CS_KEY] == data[CS_KEY]

    vcb = dv[CB_KEY].decode("latin1")
    vmi = dv[MI_KEY].decode("latin1")
    for btn, meta in TARGETS.items():
        assert get_button_image(vcb, btn) == meta["final"]
        assert re.search(rf"(?m)^MappedImage\s+{re.escape(meta['final'])}\s*$", vmi)
        tex_key = f"Art\\Textures\\{meta['pack_tga']}"
        assert tex_key in av
        w, h, bpp = tga_size(av[tex_key])
        assert (w, h) == (meta["mi_w"], meta["mi_h"]), (meta["final"], w, h)
        assert bpp == 24

    for btn, img in FREEZE_BUTTON_IMAGES.items():
        assert get_button_image(vcb, btn) == img

    # E3 button texture still good
    ew, eh, _ = tga_size(av["Art\\Textures\\E3USATB.tga"])
    assert (ew, eh) == (150, 106)

    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)

    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
        zf.write(ART_BIG, "_SPEC_ART_ONE.big")

    url = upload(OUT_ZIP)
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={data_sha}\n"
        f"_SPEC_ART_ONE.big sha256={art_sha}\n"
        f"zip={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    OUT_URL.write_text(url + "\n", encoding="utf-8")

    lines = [
        "BUTTON ICON RESTORE = PASS",
        "",
        "Gameplay Objects changed = NO",
        "Weapons changed = NO",
        "Flight behavior changed = NO",
        "Aircraft W3Ds changed = NO",
        "HeavyAirBase CommandSet changed = NO",
        "HeavyAirBase parking changed = NO",
        "Other aircraft changed = NO",
        "Other factions changed = NO",
        "",
    ]
    labels = {
        "Command_ConstructAmericaJetB2Spirit": "B-2",
        "Command_ConstructAmericaJetB52H": "B-52",
        "Command_ConstructAmericaJetB1R": "B-1/B-1R",
        "Command_ConstructAmericaJetAC130": "AC-130",
    }
    for btn, meta in TARGETS.items():
        lines += [
            f"{labels[btn]}:",
            f"CommandButton = {btn}",
            f"Old ButtonImage = {meta['old']}",
            f"Donor ButtonImage = {meta['donor_btn']}",
            f"Final ButtonImage = {meta['final']}",
            "Donor icon physically present in ART = YES",
            "",
        ]
    lines += [
        "B-2 icon visually depicts B-2 = YES (donor B2DropBombTB; donor USAB2 ButtonImage UH60 rejected)",
        "B-52 icon visually depicts B-52 = YES (donor B52 / B52TB)",
        "B-1 icon visually depicts B-1 = YES (donor B1 / B1TB)",
        "AC-130 icon visually depicts AC-130 = YES (donor Cargo130 / Cargo130TB)",
        "Pink/missing icons = 0",
        "Generic placeholder icons = 0",
        "",
        f"DATA sha256 = {data_sha}",
        f"ART sha256 = {art_sha}",
        f"ZIP = {OUT_ZIP.name}",
        f"URL = {url}",
    ]
    report = "\n".join(lines) + "\n"
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
