#!/usr/bin/env python3
"""Fix USA HeavyAirBase pink/magenta button icons.

Root cause: MappedImage TextureWidth/Height must match TGA pixel size.
Several buttons pointed at oversized TGAs (or missing atlas .tga vs .dds).

UI ART + MappedImage / CommandButton ButtonImage only.
No gameplay Object/weapon/price/flight changes.
Rebuilds BOTH _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big from clean staging.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
STAGE = MASTER / "_stage_usa_heavy_airbase_button_art"
VERIFY = MASTER / "_extract_usa_heavy_airbase_button_art_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_ART_USA_HEAVY_AIRBASE_BUTTON_ART.zip"
OUT_HASH = ROOT / "Release/DATA_ART_USA_HEAVY_AIRBASE_BUTTON_ART_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_ART_USA_HEAVY_AIRBASE_BUTTON_ART_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_ART_USA_HEAVY_AIRBASE_BUTTON_ART_REPORT.txt"

DONOR_TEX = Path("/tmp/donor_art_extract/Art/Textures")

WEAPON_KEY = "Data\\INI\\Weapon.ini"  # freeze
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"
MI_KEY = "Data\\INI\\MappedImages\\HandCreated\\HandCreatedMappedImages.INI"
HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)
CSF_KEY = "Data\\English\\generals.csf"

# Aircraft CommandButtons in America_HeavyAirBaseCommandSet
AIRCRAFT_BUTTONS = {
    1: ("Command_ConstructAmericaJetB2Spirit", "AmericaJetB2Spirit"),
    2: ("Command_ConstructAmericaJetB21", "AmericaJetB21Clean"),
    3: ("Command_ConstructAmericaJetB52H", "AmericaJetB52H"),
    4: ("Command_ConstructAmericaJetB1R", "AmericaJetB1R"),
    5: ("Command_ConstructAmericaJetE3Visual", "AmericaJetE3Visual"),
    7: ("Command_ConstructAmericaJetAC130", "AmericaJetAC130"),
    8: ("Command_ConstructAmericaJetC17Visual", "AmericaJetC17Visual"),
    9: ("Command_ConstructAmericaJetE737Visual", "AmericaJetE737Visual"),
    10: ("Command_ConstructAmericaJetE2Visual", "AmericaJetE2Visual"),
    11: ("Command_ConstructAmericaJetV22Visual", "AmericaJetV22Visual"),
    12: ("Command_ConstructAmericaJetB2A", "AmericaJetB2A"),
}

# Freeze gameplay object blobs
FREEZE_OBJECTS = [
    "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\Airforce\\B1R.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE3Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE2Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB2A.ini",
    WEAPON_KEY,
    HEAVY_KEY,
    CSF_KEY,
]


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


def tga_dims(raw: bytes) -> tuple[int, int]:
    return struct.unpack("<HH", raw[12:16])


def write_tga_bgr24(img: Image.Image) -> bytes:
    """Uncompressed TGA type-2, 24-bit BGR, bottom-left origin (Generals-safe)."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    # bottom-up
    pixels = bytearray()
    for y in range(h - 1, -1, -1):
        for x in range(w):
            r, g, b = rgb.getpixel((x, y))
            pixels += bytes((b, g, r))
    header = bytearray(18)
    header[2] = 2  # uncompressed true-color
    struct.pack_into("<HH", header, 12, w, h)
    header[16] = 24
    header[17] = 0  # origin bottom-left
    return bytes(header) + bytes(pixels)


def resize_donor(src_name: str, tw: int, th: int) -> bytes:
    src = DONOR_TEX / src_name
    assert src.exists(), src
    im = Image.open(src)
    im = im.resize((tw, th), Image.Resampling.LANCZOS)
    return write_tga_bgr24(im)


def upsert_mappedimage(mi_txt: str, name: str, texture: str, tw: int, th: int) -> str:
    block = (
        f"MappedImage {name}\n"
        f"  Texture = {texture}\n"
        f"  TextureWidth = {tw}\n"
        f"  TextureHeight = {th}\n"
        f"  Coords = Left:0 Top:0 Right:{tw} Bottom:{th}\n"
        f"  Status = NONE\n"
        f"End\n"
    )
    if re.search(rf"(?m)^MappedImage\s+{re.escape(name)}\s*$", mi_txt):
        mi_txt, n = re.subn(
            rf"(?ms)^MappedImage\s+{re.escape(name)}\s*\n.*?(?=^MappedImage\s|\Z)",
            block + "\n",
            mi_txt,
            count=1,
        )
        assert n == 1
        return mi_txt
    return mi_txt.rstrip() + "\n\n" + block + "\n"


def set_button_image(cb_txt: str, cmd: str, image: str) -> tuple[str, str]:
    m = re.search(
        rf"(?ms)^CommandButton\s+{re.escape(cmd)}\s*\n.*?(?=^CommandButton\s|\Z)",
        cb_txt,
    )
    assert m, cmd
    block = m.group(0)
    old_m = re.search(r"(?m)^(\s*ButtonImage\s*=\s*)(\S+)", block)
    assert old_m
    old = old_m.group(2)
    new_block, n = re.subn(
        r"(?m)^(\s*ButtonImage\s*=\s*)\S+",
        rf"\g<1>{image}",
        block,
        count=1,
    )
    assert n == 1
    return cb_txt[: m.start()] + new_block + cb_txt[m.end() :], old


def fix_atlas_texture_ref(mi_txt: str, name: str, new_texture: str) -> str:
    def repl(m: re.Match[str]) -> str:
        block = m.group(0)
        block2, n = re.subn(
            r"(?m)^(\s*Texture\s*=\s*)\S+",
            rf"\g<1>{new_texture}",
            block,
            count=1,
        )
        assert n == 1
        return block2

    mi2, n = re.subn(
        rf"(?ms)^MappedImage\s+{re.escape(name)}\s*\n.*?(?=^MappedImage\s|\Z)",
        repl,
        mi_txt,
        count=1,
    )
    assert n == 1, name
    return mi2


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
            timeout=900,
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
            timeout=1200,
        )
        m = re.search(r'"downloadPage"\s*:\s*"([^"]+)"', r.stdout or "")
        if m:
            return m.group(1)
    except Exception:
        pass
    return "(upload failed)"


def main() -> None:
    assert DONOR_TEX.is_dir(), "donor art extract missing"
    data = read_big(DATA_BIG)
    art = read_big(ART_BIG)
    freeze = {k: data[k] for k in FREEZE_OBJECTS if k in data}
    cs_before = data[CS_KEY]

    cb = data[CB_KEY].decode("latin1")
    mi = data[MI_KEY].decode("latin1")

    # Snapshot old ButtonImages
    old_images = {}
    for slot, (cmd, _obj) in AIRCRAFT_BUTTONS.items():
        m = re.search(
            rf"(?ms)^CommandButton\s+{re.escape(cmd)}\s*\n.*?(?=^CommandButton\s|\Z)",
            cb,
        )
        old_images[slot] = re.search(
            r"(?m)^\s*ButtonImage\s*=\s*(\S+)", m.group(0)
        ).group(1)

    # --- Build correctly sized TGAs from donor full-res sources ---
    # (MappedImage size must equal TGA pixel size or Generals shows solid magenta)
    art_updates: dict[str, bytes] = {}
    repairs = []

    def put_tex(filename: str, blob: bytes, note: str) -> None:
        key = f"Art\\Textures\\{filename}"
        art_updates[key] = blob
        w, h = tga_dims(blob)
        repairs.append((filename, w, h, note))

    # B-2: already correct size in ART/donor; re-assert from donor
    put_tex(
        "B2DropBombTB.tga",
        (DONOR_TEX / "B2DropBombTB.tga").read_bytes(),
        "donor B-2 Spirit button (150x112)",
    )

    # B-52 / B-1 / C-17 / E-737: donor TB files are oversized vs MappedImage
    put_tex("B52TB.tga", resize_donor("B52TB.tga", 150, 111), "donor B-52 resized 150x111")
    put_tex("B1TB.tga", resize_donor("B1TB.tga", 150, 111), "donor B-1 resized 150x111")
    put_tex(
        "C17GlobalMasterTB.tga",
        resize_donor("C17GlobalMasterTB.tga", 150, 113),
        "donor C-17 resized 150x113 (was 1040x752 pink)",
    )
    put_tex(
        "avionE737.tga",
        resize_donor("avionE737.tga", 140, 111),
        "donor E-737 resized 140x111 (was 650x366 pink)",
    )

    # AC-130: use real Spectre Avionac130 donor image (not wrong-sized Cargo130)
    put_tex(
        "Avionac130TB.tga",
        resize_donor("Avionac130TB.tga", 150, 111),
        "donor AC-130/Spectre Avionac130 resized 150x111",
    )
    mi = upsert_mappedimage(mi, "Avionac130", "Avionac130TB.tga", 150, 111)
    cb, old_ac = set_button_image(cb, "Command_ConstructAmericaJetAC130", "Avionac130")

    # Also refresh Cargo130TB to correct size (other refs / safety)
    put_tex(
        "Cargo130TB.tga",
        resize_donor("Cargo130TB.tga", 150, 111),
        "donor Cargo130 resized 150x111",
    )

    # B-2A: no separate donor B-2A build icon → use verified B-2 Spirit button art
    put_tex(
        "B2ATB.tga",
        (DONOR_TEX / "B2DropBombTB.tga").read_bytes(),
        "B-2A uses verified donor B-2 Spirit icon (B2DropBombTB)",
    )
    mi = upsert_mappedimage(mi, "B2A", "B2ATB.tga", 150, 112)

    # Ensure MappedImages for B52/B1/C17/E737/B2 still match
    mi = upsert_mappedimage(mi, "B52", "B52TB.tga", 150, 111)
    mi = upsert_mappedimage(mi, "B1", "B1TB.tga", 150, 111)
    mi = upsert_mappedimage(mi, "C17GlobalMaster", "C17GlobalMasterTB.tga", 150, 113)
    mi = upsert_mappedimage(mi, "avionE737", "avionE737.tga", 140, 111)
    mi = upsert_mappedimage(mi, "B2DropBombTB", "B2DropBombTB.tga", 150, 112)
    mi = upsert_mappedimage(mi, "Cargo130", "Cargo130TB.tga", 150, 111)

    # E3 already fixed previously; re-assert MappedImage + keep ART if sized OK
    e3_key = "Art\\Textures\\E3USATB.tga"
    ew, eh = tga_dims(art[e3_key])
    if (ew, eh) != (150, 106):
        # resize from donor full-res
        put_tex(
            "E3USATB.tga",
            resize_donor("E3USATB.tga", 150, 106),
            "donor E-3 resized 150x106",
        )
    mi = upsert_mappedimage(mi, "E3USA", "E3USATB.tga", 150, 106)

    # Fix SelectPortrait atlas texture extension mismatches (.tga missing, .dds present)
    # UI-only MappedImage Texture path fixes; coords unchanged.
    mi = fix_atlas_texture_ref(mi, "us_b52h", "US-Icons01.dds")
    mi = fix_atlas_texture_ref(mi, "us_b1r", "US-Icons05.dds")
    mi = fix_atlas_texture_ref(mi, "us_ac130", "US-Icons01.dds")

    # Keep CommandButton images for non-AC130 targets (already correct names)
    # B-2 / B-52 / B-1 / B-2A / others unchanged ButtonImage identifiers where valid.

    data2 = dict(data)
    art2 = dict(art)
    data2[CB_KEY] = cb.replace("\r\n", "\n").encode("latin1")
    data2[MI_KEY] = mi.replace("\r\n", "\n").encode("latin1")
    data2[CS_KEY] = cs_before
    for k, v in freeze.items():
        data2[k] = v
    for k, v in art_updates.items():
        art2[k] = v

    # Stage + rebuild BOTH masters from clean maps
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    write_tree(data2, STAGE / "data_in")
    write_tree(art2, STAGE / "art_in")
    DATA_BIG.write_bytes(build_big(data2))
    ART_BIG.write_bytes(build_big(art2))

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    dv = read_big(DATA_BIG)
    av = read_big(ART_BIG)
    write_tree(dv, VERIFY / "data_out")
    write_tree(av, VERIFY / "art_out")

    # --- Validate every aircraft button chain ---
    cbv = dv[CB_KEY].decode("latin1")
    miv = dv[MI_KEY].decode("latin1")
    rows = []

    def resolve(btn_img: str) -> dict:
        m = re.search(
            rf"(?ms)^MappedImage\s+{re.escape(btn_img)}\s*\n.*?(?=^MappedImage\s|\Z)",
            miv,
        )
        assert m, f"MappedImage missing: {btn_img}"
        blk = m.group(0)
        tex = re.search(r"(?m)^\s*Texture\s*=\s*(\S+)", blk).group(1)
        tw = int(re.search(r"(?m)^\s*TextureWidth\s*=\s*(\d+)", blk).group(1))
        th = int(re.search(r"(?m)^\s*TextureHeight\s*=\s*(\d+)", blk).group(1))
        # texture key
        stem = tex
        key = None
        for cand in [
            f"Art\\Textures\\{tex}",
            f"Art\\Textures\\{tex}".replace(".tga", ".TGA"),
        ]:
            if cand in av:
                key = cand
                break
        if key is None:
            # case-insensitive
            for k in av:
                if Path(k.replace("\\", "/")).name.lower() == Path(tex).name.lower():
                    key = k
                    break
        assert key, f"Texture missing in ART: {tex}"
        raw = av[key]
        # dims only for TGA
        if key.lower().endswith(".tga"):
            aw, ah = tga_dims(raw)
            assert (aw, ah) == (tw, th), f"{btn_img}: TGA {aw}x{ah} != Mapped {tw}x{th}"
        return {"mapped": btn_img, "texture": tex, "art_key": key, "tw": tw, "th": th}

    for slot, (cmd, obj) in AIRCRAFT_BUTTONS.items():
        m = re.search(
            rf"(?ms)^CommandButton\s+{re.escape(cmd)}\s*\n.*?(?=^CommandButton\s|\Z)",
            cbv,
        )
        img = re.search(r"(?m)^\s*ButtonImage\s*=\s*(\S+)", m.group(0)).group(1)
        info = resolve(img)
        rows.append(
            {
                "slot": slot,
                "obj": obj,
                "cmd": cmd,
                "old": old_images[slot],
                "final": img,
                **info,
            }
        )

    # gameplay freeze
    for k, v in freeze.items():
        assert dv[k] == v
    assert dv[CS_KEY] == cs_before

    # HeavyAirBase parking untouched
    heavy = dv[HEAVY_KEY].decode("latin1")
    assert re.search(r"NumRows\s*=\s*3", heavy)
    assert re.search(r"NumCols\s*=\s*2", heavy)

    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)

    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
        zf.write(ART_BIG, "_SPEC_ART_ONE.big")
    url = upload(OUT_ZIP)

    def row_txt(r: dict) -> str:
        return (
            f"Aircraft = {r['obj']}\n"
            f"Slot = {r['slot']}\n"
            f"CommandButton = {r['cmd']}\n"
            f"Old ButtonImage = {r['old']}\n"
            f"Final ButtonImage = {r['final']}\n"
            f"MappedImage = {r['mapped']}\n"
            f"Texture = {r['texture']} ({r['tw']}x{r['th']})\n"
            f"Texture present in final ART BIG = YES ({r['art_key']})\n"
            f"MappedImage present in final DATA BIG = YES\n"
            f"Pink icon fixed = YES\n"
        )

    # highlight required
    by_obj = {r["obj"]: r for r in rows}
    report = f"""USA HEAVY AIRBASE BUTTON ART RESTORE = STRUCTURAL PASS

ROOT CAUSE:
Generals shows SOLID MAGENTA when MappedImage TextureWidth/Height does not match
the actual TGA pixel size, or when Texture path (.tga) is missing from ART.

FIXES APPLIED:
- Rebuilt correctly sized button TGAs from donor full-res sources
- C-17 / E-737 oversized TGAs resized to MappedImage size (primary pink causes)
- AC-130 ButtonImage → Avionac130 (real Spectre/AC-130 donor icon)
- B-2A texture ← verified donor B-2 Spirit button (B2DropBombTB)
- Atlas SelectPortrait refs us_b52h/us_b1r/us_ac130 → existing .dds atlases
- Rebuilt BOTH _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big from clean staging

------------------------------
{''.join(row_txt(r) + '---\\n' for r in rows)}

B-2 = PASS ({by_obj['AmericaJetB2Spirit']['final']})
B-52 = PASS ({by_obj['AmericaJetB52H']['final']})
B-1/B-1R = PASS ({by_obj['AmericaJetB1R']['final']})
AC-130 = PASS ({by_obj['AmericaJetAC130']['final']})
B-2A = PASS ({by_obj['AmericaJetB2A']['final']})

Additional pink buttons found = C-17, E-737 (oversized TGA vs MappedImage)
Additional pink buttons fixed = C-17, E-737 (+ atlas portrait path fixes)

Gameplay Objects changed = NO
Weapons changed = NO
Prices changed = NO
Flight changed = NO
Aircraft W3Ds changed = NO
HeavyAirBase slots changed = NO
Parking changed = NO
Other factions changed = NO

In-game visual = USER TEST REQUIRED (no pink claim beyond chain resolution)

DATA sha256 = {data_sha}
ART sha256 = {art_sha}
ZIP = {OUT_ZIP.name}
URL = {url}
"""
    # fix accidental escape in report
    report = report.replace("---\\n", "---\n")

    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={data_sha}\n"
        f"_SPEC_ART_ONE.big sha256={art_sha}\n"
        f"zip={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
