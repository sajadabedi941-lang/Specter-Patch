#!/usr/bin/env python3
"""ART-only: recode missile_factory.tga as 24-bit RGB type-2 (no alpha).

Base: known-good Al-Fahd ART
  SHA256 d6ee44bbf52d9afba505c72e4e01fb0cbafb0b55f9483252fd645e9299dd58c0

Adds exactly Art\\Textures\\missile_factory.tga. DATA is not modified.
"""
from __future__ import annotations

import hashlib
import io
import shutil
import struct
from pathlib import Path

from PIL import Image

ROOT = Path("/workspace")
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD500/_SPEC_ART_ONE.big"
SRC_PNG = ROOT / "patch/Art/Textures/UI/missile_factory.png"
OUT = ROOT / "patch/Release/SPECTER_MISSILE_FACTORY_TGA24"

GOOD_ART_SHA = "d6ee44bbf52d9afba505c72e4e01fb0cbafb0b55f9483252fd645e9299dd58c0"
GOOD_ART_SIZE = 1262233475
GOOD_ART_FILES = 4602
TGA_KEY = r"Art\Textures\missile_factory.tga"
TRUEVISION = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")


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
    files = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name] = data[off : off + size]
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


def tga_info(blob: bytes) -> dict:
    imgtype = blob[2]
    w, h = struct.unpack_from("<HH", blob, 12)
    bpp, desc = blob[16], blob[17]
    return {
        "width": w,
        "height": h,
        "type": imgtype,
        "bpp": bpp,
        "alpha_bits": desc & 0x0F,
        "descriptor": f"0x{desc:02x}",
        "origin": "top" if desc & 0x20 else "bottom",
        "size": len(blob),
        "header": blob[:18].hex(),
    }


def make_tga24(png: Path) -> bytes:
    im = Image.open(png).convert("RGB")
    if im.size != (128, 128):
        im = im.resize((128, 128), Image.Resampling.LANCZOS)
    w, h = im.size
    pixels = im.tobytes()  # RGB top-down
    rows = []
    stride = w * 3
    for y in range(h - 1, -1, -1):  # bottom-origin
        src = pixels[y * stride : (y + 1) * stride]
        bgr = bytearray()
        for i in range(0, len(src), 3):
            r, g, b = src[i], src[i + 1], src[i + 2]
            bgr += bytes((b, g, r))
        rows.append(bytes(bgr))
    header = bytearray(18)
    header[2] = 2
    struct.pack_into("<HH", header, 12, w, h)
    header[16] = 24
    header[17] = 0x00
    return bytes(header) + b"".join(rows) + TRUEVISION


def validate_tga(blob: bytes, art: dict[str, bytes]) -> list[str]:
    fails = []
    info = tga_info(blob)
    if info["type"] != 2:
        fails.append(f"type {info['type']}")
    if info["bpp"] != 24:
        fails.append(f"bpp {info['bpp']}")
    if info["alpha_bits"] != 0:
        fails.append(f"alpha {info['alpha_bits']}")
    if info["descriptor"] != "0x00":
        fails.append(f"desc {info['descriptor']}")
    if info["origin"] != "bottom":
        fails.append(f"origin {info['origin']}")
    if info["width"] != 128 or info["height"] != 128:
        fails.append(f"dims {info['width']}x{info['height']}")
    # structure vs working cameos
    for key in [
        r"Art\Textures\F14TB.tga",
        r"Art\Textures\JIAN11TB.tga",
        r"Art\Textures\FEIBAOtb.tga",
    ]:
        ref = tga_info(art[key])
        if ref["type"] != 2 or ref["bpp"] != 24 or ref["descriptor"] != "0x00":
            fails.append(f"reference {key} unexpected {ref}")
        if blob[0:12] != art[key][0:12]:
            # first 12 bytes should be identical (id/cmap/type/origin zeros)
            if blob[0:8] != art[key][0:8]:
                fails.append(f"header prefix mismatch vs {key}")
        if blob[-18:] != art[key][-18:]:
            fails.append(f"TRUEVISION footer mismatch vs {key}")
    return fails, info


def forensic(new_art: dict[str, bytes], good: dict[str, bytes], tga: bytes) -> list[str]:
    fails = []
    gkeys = set(good)
    nkeys = set(new_art)
    deleted = sorted(gkeys - nkeys)
    added = sorted(nkeys - gkeys)
    modified = sorted(k for k in gkeys & nkeys if new_art[k] != good[k])
    if deleted:
        fails.append(f"deleted {len(deleted)} {deleted[:5]}")
    if modified:
        fails.append(f"modified {len(modified)} {modified[:5]}")
    if added != [TGA_KEY]:
        fails.append(f"added {added}")
    if new_art.get(TGA_KEY) != tga:
        fails.append("packed TGA mismatch")
    for kind, ext in [("DDS", ".dds"), ("W3D", ".w3d")]:
        gc = sum(1 for k in good if k.lower().endswith(ext))
        nc = sum(1 for k in new_art if k.lower().endswith(ext))
        if gc != nc:
            fails.append(f"{kind} count {nc} != {gc}")
    gtga = sum(1 for k in good if k.lower().endswith(".tga"))
    ntga = sum(1 for k in new_art if k.lower().endswith(".tga"))
    if ntga != gtga + 1:
        fails.append(f"TGA count {ntga} != {gtga}+1")
    lows = [k.replace("/", "\\").lower() for k in new_art]
    if len(lows) != len(set(lows)):
        fails.append("duplicate texture names")
    return fails, deleted, added, modified


def main() -> int:
    if SRC_ART.stat().st_size != GOOD_ART_SIZE or sha256_path(SRC_ART) != GOOD_ART_SHA:
        raise SystemExit("known-good ART SHA/size mismatch")
    if not SRC_PNG.is_file():
        raise SystemExit("source PNG missing")

    raw = SRC_ART.read_bytes()
    good = parse_big(raw)
    if len(good) != GOOD_ART_FILES:
        raise SystemExit(f"known-good file count {len(good)}")

    tga = make_tga24(SRC_PNG)
    tga_fails, info = validate_tga(tga, good)
    print("=== PRE-PACK TGA ===")
    for k, v in info.items():
        print(f"  {k}: {v}")
    if tga_fails:
        print("TGA FAIL", tga_fails)
        return 1
    print("PRE-PACK TGA: PASS (type 2, 24 bpp, alpha 0, desc 0x00)")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "missile_factory.tga").write_bytes(tga)

    art = dict(good)
    art[TGA_KEY] = tga
    packed = build_big(art)
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_art.write_bytes(packed)

    extracted = parse_big(packed)
    arch, count, header, index_end, files = parse_index(packed)
    issues = []
    if arch != len(packed):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    expected = header
    for name, off, size in sorted(files, key=lambda x: x[1]):
        if off != expected:
            issues.append(f"overlap/gap {name}")
            break
        expected = off + size
    if expected != len(packed):
        issues.append("trailing gap/overflow")

    fails, deleted, added, modified = forensic(extracted, good, tga)
    fails.extend(issues)
    packed_info = tga_info(extracted[TGA_KEY])

    report = [
        "# missile_factory.tga 24-bit RGB recode (ART-only)",
        "",
        "DATA not modified. Known-good Al-Fahd ART + one corrected TGA.",
        "",
        "## Corrected TGA",
        f"- width: {packed_info['width']}",
        f"- height: {packed_info['height']}",
        f"- type: {packed_info['type']}",
        f"- bpp: {packed_info['bpp']}",
        f"- alpha bits: {packed_info['alpha_bits']}",
        f"- descriptor: {packed_info['descriptor']}",
        f"- origin: {packed_info['origin']}",
        f"- file size: {packed_info['size']}",
        "- compared to F14TB.tga / JIAN11TB.tga / FEIBAOtb.tga (type 2, 24 bpp, desc 0x00)",
        "",
        f"- ART size: {out_art.stat().st_size}",
        f"- ART SHA256: {sha256_path(out_art)}",
        f"- ART files: {len(extracted)}",
        f"- deleted: {len(deleted)}",
        f"- modified existing: {len(modified)}",
        f"- added: {added}",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
        print("\n".join(report))
        return 1
    report += [
        "## VALIDATION PASS (static / packed last-wins)",
        "- DELETED FILES = 0",
        "- MODIFIED EXISTING FILES = 0",
        "- ADDED FILES = 1 Art\\Textures\\missile_factory.tga",
        "- DDS/W3D counts unchanged; existing TGA/W3D/DDS byte-identical",
        "- BIG header/index valid; no overlap",
        "",
        "RUNTIME_TEST=NOT RUN",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
    (OUT / "HASHES.txt").write_text(
        f"ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={out_art.stat().st_size}\n"
        f"ART_SHA256={sha256_path(out_art)}\n"
        f"ART_FILES={len(extracted)}\n"
        f"TGA=Art\\Textures\\missile_factory.tga\n"
        f"TGA_TYPE=2\n"
        f"TGA_BPP=24\n"
        f"TGA_ALPHA=0\n"
        f"TGA_DESC=0x00\n"
        f"BASELINE_ART=s-iraq-alfahd500 / {GOOD_ART_SHA}\n"
        f"DATA_CHANGED=NO\n"
        f"STATIC_VALIDATION=PASS\n"
        f"RUNTIME_TEST=NOT RUN\n",
        encoding="ascii",
    )
    (OUT / "README.txt").write_text(
        "SPECTER missile_factory cameo recoded 24-bit RGB TGA (ART-only)\n"
        "\n"
        "Install this complete _SPEC_ART_ONE.big over current live ART.\n"
        "Keep the current DATA (ButtonImage = missile_factory unchanged).\n"
        "\n"
        "Static validation only. The game was not launched.\n",
        encoding="ascii",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "Complete replacement ART:\n"
        "  _SPEC_ART_ONE.big\n"
        f"  SIZE={out_art.stat().st_size}\n"
        f"  SHA256={sha256_path(out_art)}\n",
        encoding="ascii",
    )
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
