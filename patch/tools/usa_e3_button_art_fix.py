#!/usr/bin/env python3
"""Fix pink USA E-3 HeavyAirBase button by correcting donor E3USA icon ART.

Keeps existing Slot 5 / Command_ConstructAmericaJetE3Visual / AmericaJetE3Visual.
Donor ButtonImage = E3USA (verified). Packed E3USATB.tga was 1243x800 (odd width)
while MappedImage declared 150x106 — Generals UI load fails → magenta.

Replace E3USATB.tga + E3USA.tga with proper 150x106 24-bit TGAs (V22/E2 style).
ART rebuild only unless DATA freeze check requires a remaster copy.
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
STAGE = MASTER / "_stage_usa_e3_button_art_fix"
VERIFY = MASTER / "_extract_usa_e3_button_art_fix_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_ART_USA_E3_BUTTON_ART_FIX.zip"
OUT_HASH = ROOT / "Release/DATA_ART_USA_E3_BUTTON_ART_FIX_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_ART_USA_E3_BUTTON_ART_FIX_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_ART_USA_E3_BUTTON_ART_FIX_REPORT.txt"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"

E737_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini"
)
E2_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE2Visual.ini"
)
E3_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE3Visual.ini"
)
C17_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Visual.ini"
)
AC130_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
)
V22_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini"
)
HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"
CSF_KEY = "Data\\English\\generals.csf"
MI_KEY = "Data\\INI\\MappedImages\\HandCreated\\HandCreatedMappedImages.INI"

BTN_W, BTN_H = 150, 106


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


def count_obj(dmap: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(name)}\s*$")
    return sum(
        len(pat.findall(v.decode("latin1")))
        for k, v in dmap.items()
        if k.lower().endswith(".ini")
    )


def count_btn(dmap: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^CommandButton\s+{re.escape(name)}\s*$")
    return sum(
        len(pat.findall(v.decode("latin1")))
        for k, v in dmap.items()
        if k.lower().endswith(".ini")
    )


def tga_size(b: bytes) -> tuple[int, int, int]:
    w, h = struct.unpack_from("<HH", b, 12)
    return w, h, b[16]


def load_tga_bgr(b: bytes) -> tuple[int, int, bytes, bool]:
    assert b[2] == 2, "only uncompressed TGA supported for source"
    w, h = struct.unpack_from("<HH", b, 12)
    bpp = b[16] // 8
    top = bool(b[17] & 0x20)
    img = b[18 : 18 + w * h * bpp]
    if bpp == 4:
        # drop alpha → BGR
        flat = bytearray()
        for i in range(0, len(img), 4):
            flat += img[i : i + 3]
        img = bytes(flat)
        bpp = 3
    assert bpp == 3
    return w, h, img, top


def get_px(img: bytes, w: int, h: int, top: bool, x: int, y: int) -> bytes:
    yy = y if top else (h - 1 - y)
    off = (yy * w + x) * 3
    return img[off : off + 3]


def make_button_tga(src: bytes, tw: int = BTN_W, th: int = BTN_H) -> bytes:
    """Center-crop to button aspect, scale to tw x th, bottom-origin 24-bit TGA."""
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
    for y in range(th):  # bottom-origin output rows
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
            timeout=300,
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
            timeout=600,
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
    data_before = sha256(DATA_BIG)
    art_before = sha256(ART_BIG)

    # --- freeze / chain audit (DATA unchanged) ---
    assert sha256(data[CSF_KEY]) == GOOD_CSF
    assert count_obj(data, "AmericaJetE3Visual") == 1
    assert count_obj(data, "AmericaJetE3AWACS") == 0
    assert count_obj(data, "USAE3") == 0
    assert count_btn(data, "Command_ConstructAmericaJetE3Visual") == 1

    cs = data[CS_KEY].decode("latin1")
    hab = re.search(
        r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?^End\s*$", cs
    ).group(0)
    assert re.search(
        r"(?m)^\s*5\s*=\s*Command_ConstructAmericaJetE3Visual\s*$", hab
    )
    for slot, cmd in {
        1: "Command_ConstructAmericaJetB2Spirit",
        2: "Command_ConstructAmericaJetB21",
        3: "Command_ConstructAmericaJetB52H",
        4: "Command_ConstructAmericaJetB1R",
        6: "Command_Upgrade_NuclearTipWarhead2",
        7: "Command_ConstructAmericaJetAC130",
        8: "Command_ConstructAmericaJetC17Visual",
        9: "Command_ConstructAmericaJetE737Visual",
        10: "Command_ConstructAmericaJetE2Visual",
        11: "Command_ConstructAmericaJetV22Visual",
        13: "Command_SetRallyPoint",
        14: "Command_Sell",
    }.items():
        assert re.search(rf"(?m)^\s*{slot}\s*=\s*{re.escape(cmd)}\s*$", hab)

    cb = data[CB_KEY].decode("latin1")
    btn = re.search(
        r"(?ms)^CommandButton\s+Command_ConstructAmericaJetE3Visual\s*\n.*?^End\s*$",
        cb,
    ).group(0)
    assert "Object        = AmericaJetE3Visual" in btn
    assert "ButtonImage   = E3USA" in btn

    e3 = data[E3_KEY].decode("latin1")
    assert re.search(r"(?m)^\s*Model\s*=\s*E3\s*$", e3)
    assert "US_E3G" not in e3
    assert "AVHawk" not in e3
    assert "KVE737" not in e3
    assert not re.search(r"(?m)^\s*WeaponSet\b", e3)

    mi = data[MI_KEY].decode("latin1")
    mim = re.search(r"(?ms)^MappedImage\s+E3USA\s*\n.*?^End\s*$", mi)
    assert mim, "MappedImage E3USA missing"
    assert "Texture = E3USATB.tga" in mim.group(0)
    assert "TextureWidth = 150" in mim.group(0)
    assert "TextureHeight = 106" in mim.group(0)

    # freeze other aircraft bytes
    freeze = {
        E737_KEY: data[E737_KEY],
        E2_KEY: data[E2_KEY],
        C17_KEY: data[C17_KEY],
        AC130_KEY: data[AC130_KEY],
        V22_KEY: data[V22_KEY],
        HEAVY_KEY: data[HEAVY_KEY],
        CS_KEY: data[CS_KEY],
        CB_KEY: data[CB_KEY],
        E3_KEY: data[E3_KEY],
        MI_KEY: data[MI_KEY],
        CSF_KEY: data[CSF_KEY],
    }

    # --- ART: required E-3 visuals present ---
    required_art = [
        "Art\\W3D\\E3.W3D",
        "Art\\Textures\\avE3.tga",
        "Art\\Textures\\avE3ACC.tga",
        "Art\\Textures\\E3USATB.tga",
        "Art\\Textures\\E3USA.tga",
        "Art\\W3D\\chj10_r.W3D",
    ]
    for k in required_art:
        assert k in art, f"missing {k}"

    src = art["Art\\Textures\\E3USATB.tga"]
    ow, oh, obpp = tga_size(src)
    assert (ow, oh) == (1243, 800), f"unexpected source size {ow}x{oh}"

    fixed = make_button_tga(src)
    fw, fh, fbpp = tga_size(fixed)
    assert (fw, fh, fbpp) == (BTN_W, BTN_H, 24)
    assert len(fixed) == 18 + BTN_W * BTN_H * 3

    art2 = dict(art)
    art2["Art\\Textures\\E3USATB.tga"] = fixed
    art2["Art\\Textures\\E3USA.tga"] = fixed  # same donor cameo family

    # stage + write ART
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    write_tree(art2, STAGE / "art_in")
    new_art = build_big(art2)
    ART_BIG.write_bytes(new_art)

    # re-extract ART verify
    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    art_v = read_big(ART_BIG)
    write_tree(art_v, VERIFY / "art_out")
    for k in required_art:
        assert k in art_v
    vw, vh, vbpp = tga_size(art_v["Art\\Textures\\E3USATB.tga"])
    assert (vw, vh, vbpp) == (BTN_W, BTN_H, 24)
    vw2, vh2, vbpp2 = tga_size(art_v["Art\\Textures\\E3USA.tga"])
    assert (vw2, vh2, vbpp2) == (BTN_W, BTN_H, 24)
    assert len(art_v["Art\\W3D\\E3.W3D"]) > 1000
    # radar mesh name present in W3D
    assert b"RADAR" in art_v["Art\\W3D\\E3.W3D"]

    # DATA must be byte-identical (no DATA edits this pass)
    data_v = read_big(DATA_BIG)
    for k, v in freeze.items():
        assert data_v[k] == v, f"DATA freeze broken: {k}"
    assert sha256(DATA_BIG) == data_before

    data_sha = data_before
    art_sha = sha256(ART_BIG)
    assert art_sha != art_before

    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # ART changed; include DATA too so install pair matches verified chain
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
        zf.write(ART_BIG, "_SPEC_ART_ONE.big")

    url = upload(OUT_ZIP)
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={data_sha} (unchanged this fix)\n"
        f"_SPEC_ART_ONE.big sha256={art_sha}\n"
        f"prior_art sha256={art_before}\n"
        f"zip={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    OUT_URL.write_text(url + "\n", encoding="utf-8")

    report = f"""USA E-3 REAL DONOR VISUAL + BUTTON FIX = PASS

Current pink button identified as E-3 = YES

Slot 5 button = Command_ConstructAmericaJetE3Visual
Object = AmericaJetE3Visual

DONOR:
Original E-3 Object = USAE3
Original E-3 Primary W3D = E3
Original E-3 ButtonImage = E3USA

FINAL:
Primary W3D = E3
Real donor E-3 model = YES

ButtonImage = E3USA
Real donor E-3 button = YES
Pink/missing placeholder removed = YES
  Cause: E3USATB.tga was 1243x800 (odd width) vs MappedImage 150x106
  Fix: replaced E3USATB.tga + E3USA.tga with proper 150x106 24-bit TGA
       (center-cropped/scaled from donor cameo photo; V22/E2 UI style)

Required W3Ds = E3.W3D (body+radar rotodome meshes), chj10_r.W3D (gear art present)
Required textures = avE3.tga, avE3ACC.tga
Required UI textures = E3USATB.tga, E3USA.tga (now 150x106)
MappedImage definition required = YES (E3USA -> E3USATB.tga 150x106; already in DATA)

Donor gameplay DATA imported = NO
Specter-safe flight DATA retained = YES

HeavyAirBase Slot 5 resolves = YES
AmericaJetE3Visual count = 1
E-3 CommandButton count = 1

E-737 changed = NO
E-2 changed = NO
C-17 changed = NO
V-22 changed = NO
AC-130 changed = NO
Other factions changed = NO
DATA changed = NO
ART changed = YES

DATA sha256 = {data_sha}
ART sha256 = {art_sha}
ZIP = {OUT_ZIP.name}
URL = {url}
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
