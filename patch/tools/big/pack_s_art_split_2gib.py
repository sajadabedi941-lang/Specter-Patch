#!/usr/bin/env python3
"""Split the oversized SPECTER ART archive so every W3D offset is SAGE-safe.

Baseline packed ART/DATA: SPECTER_ISRAEL_JERICHO_CHINA_D30_ICONS (PR #655),
which still carries the Turkey-era ART that first crossed 2^31 bytes.

Loading convention (repository-proven, not assumed):
  Zero Hour auto-loads every *.big next to generals.exe (case-insensitive
  alphabetical order, later archives last-win). SPECTER already ships two
  archives this way (_SPEC_DATA_ONE.big + _SPEC_ART_ONE.big). Overlay BIGs
  such as _SPECTER_PATCH_FINAL.big were designed to load from the same
  folder scan. generals.exe -mod cannot enable more than one extra archive,
  which is why the launcher copies BIGs into the game folder instead.

  Therefore _SPEC_ART_TWO.big in that same folder is loaded. A texture/W3D
  split matches vanilla ZH (Textures.big + W3D.big): the engine resolves
  Art\\Textures\\ and Art\\W3D\\ keys across all loaded archives.

DATA is copied byte-identical. Every source ART entry is preserved
byte-for-byte. No recompress, resize, rename, or Draw-module rewrite.
"""
from __future__ import annotations

import hashlib
import shutil
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_ISRAEL_JERICHO_CHINA_D30_ICONS/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_ISRAEL_JERICHO_CHINA_D30_ICONS/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_ART_SPLIT_2GIB"
INSTALLER = ROOT / "patch/tools/installer"

SHA_DATA_SRC = "06ab43ec2b28fb04a4d13801727c40ac0bbfbd9be728fe37e715ffb489bf2175"
SIZE_DATA_SRC = 370734307
SHA_ART_SRC = "de0e998813bb7f74ff634c4a5aefb901692334e1e0d2a52637d3699b1d8f1f8a"
SIZE_ART_SRC = 2451295403

# SAGE FileInfo offset/size are 32-bit. A signed read of values >= 2^31
# yields a negative offset and the engine cannot seek to the payload.
SAGE_SAFE = 2147483648  # must stay strictly below

REQUIRED_W3D = [
    r"Art\W3D\US_Command.W3D",
    r"Art\W3D\US_WarFactory.W3D",
    r"Art\W3D\US_Supply.W3D",
    r"Art\W3D\Chi_Hq.W3D",
    r"Art\W3D\Arb_Command.W3D",
    r"Art\W3D\Iran_Command.W3D",
    r"Art\W3D\Irq_Command.W3D",
    r"Art\W3D\NKr_Command.W3D",
    r"Art\W3D\Irq_FahdFac.W3D",
    r"Art\W3D\Tur_Atmaca.W3D",
    r"Art\W3D\Esp_Albatr.W3D",
]

W3D_EXTS = {".w3d"}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_slice(mm, off: int, size: int) -> str:
    h = hashlib.sha256()
    h.update(mm[off : off + size])
    return h.hexdigest()


def parse_index_mm(mm):
    if mm[:4] != b"BIGF":
        raise ValueError("not BIGF")
    archive_size = struct.unpack(">I", mm[4:8])[0]
    count = struct.unpack(">I", mm[8:12])[0]
    header_size = struct.unpack(">I", mm[12:16])[0]
    pos = 16
    files = []
    for _ in range(count):
        off, size = struct.unpack(">II", mm[pos : pos + 8])
        pos += 8
        end = mm.find(b"\x00", pos)
        name = mm[pos:end].decode("latin1").replace("/", "\\")
        pos = end + 1
        files.append((name, off, size))
    return archive_size, count, header_size, files


def is_w3d(name: str) -> bool:
    return Path(name.replace("\\", "/")).suffix.lower() in W3D_EXTS


def write_big_from_slices(path: Path, items: list[tuple[str, int, int]], mm) -> None:
    items = sorted(items, key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    offset = header_size
    index = []
    for name, src_off, size in items:
        index.append((name, offset, size, src_off))
        offset += size
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as out:
        out.write(b"BIGF")
        out.write(struct.pack(">I", offset))
        out.write(struct.pack(">I", len(items)))
        out.write(struct.pack(">I", header_size))
        for name, off, size, _src in index:
            out.write(struct.pack(">II", off, size))
            out.write(name.encode("latin1") + b"\x00")
        for _name, _off, size, src_off in index:
            out.write(mm[src_off : src_off + size])


def sage_signed_ok(path: Path) -> list[str]:
    """Reject archives the 32-bit SAGE reader cannot address."""
    fails: list[str] = []
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        return [f"{path.name} magic {data[:4]!r} is not BIGF (gzip/other installed as .big?)"]
    size_s = struct.unpack(">i", data[4:8])[0]
    size_u = struct.unpack(">I", data[4:8])[0]
    if size_s < 0:
        fails.append(f"{path.name} signed archive_size negative ({size_s})")
    if size_u != len(data):
        fails.append(f"{path.name} archive_size {size_u} != {len(data)}")
    if size_u >= SAGE_SAFE or len(data) >= SAGE_SAFE:
        fails.append(f"{path.name} size {len(data)} >= {SAGE_SAFE}")
    count = struct.unpack(">I", data[8:12])[0]
    header_size = struct.unpack(">I", data[12:16])[0]
    pos = 16
    seen = set()
    for _ in range(count):
        off_s, size_s = struct.unpack(">ii", data[pos : pos + 8])
        off_u, size_u = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        key = name.replace("/", "\\").lower()
        if key in seen:
            fails.append(f"{path.name} dup {name}")
        seen.add(key)
        if off_s < 0:
            fails.append(f"{path.name} signed offset negative {name} off={off_u}")
        if size_s < 0:
            fails.append(f"{path.name} signed size negative {name} size={size_u}")
        if off_u >= SAGE_SAFE or off_u + size_u > len(data):
            fails.append(f"{path.name} unreadable {name} off={off_u} size={size_u}")
        if off_u + size_u > 0:
            # Engine-style seek: signed offset must land inside the file.
            sample = data[off_u : off_u + min(4, size_u)]
            if size_u >= 4 and len(sample) != 4:
                fails.append(f"{path.name} seek failed {name}")
    if pos != header_size:
        fails.append(f"{path.name} header_size {header_size} != index_end {pos}")
    fails.extend(f"{path.name} {x}" for x in sk.big_structure_ok(data))
    return fails


def index_map(path: Path):
    blob = path.read_bytes()
    _sz, _c, _h, files = parse_index_mm(blob)
    return blob, {n.replace("/", "\\"): (o, s) for n, o, s in files}


def validate(
    src_index,
    src_mm,
    art1: Path,
    art2: Path,
    data_path: Path,
    zip_path: Path,
    launch_src: Path,
    install_src: Path,
) -> list[str]:
    fails: list[str] = []
    if sk.sha256_path(data_path) != SHA_DATA_SRC or data_path.stat().st_size != SIZE_DATA_SRC:
        fails.append("DATA is not byte-identical to the accepted PR #655 archive")

    fails.extend(sage_signed_ok(art1))
    fails.extend(sage_signed_ok(art2))
    data_blob = data_path.read_bytes()
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_blob))
    if data_blob[:4] != b"BIGF":
        fails.append("DATA magic is not BIGF")

    a1_blob, a1 = index_map(art1)
    a2_blob, a2 = index_map(art2)
    a1_lower = {k.lower(): k for k in a1}
    overlap = []
    for name in a2:
        if name.lower() in a1_lower:
            overlap.append(name)
    if overlap:
        fails.append(f"cross-archive duplicate keys: {overlap[:10]}")

    union = dict(a1)
    union.update(a2)
    src_keys = {n.replace("/", "\\"): (o, s) for n, o, s in src_index}
    if set(union) != set(src_keys):
        missing = sorted(set(src_keys) - set(union))
        extra = sorted(set(union) - set(src_keys))
        fails.append(f"union key mismatch missing={len(missing)} extra={len(extra)}")
        if missing:
            fails.append("missing sample " + ", ".join(missing[:8]))
        if extra:
            fails.append("extra sample " + ", ".join(extra[:8]))

    changed = []
    for name, (src_off, src_size) in src_keys.items():
        if name in a1:
            off, size = a1[name]
            blob_src, blob = src_mm, a1_blob
        elif name in a2:
            off, size = a2[name]
            blob_src, blob = src_mm, a2_blob
        else:
            continue
        if size != src_size or sha256_slice(blob, off, size) != sha256_slice(blob_src, src_off, src_size):
            changed.append(name)
    if changed:
        fails.append(f"{len(changed)} entries altered vs source ART")
        fails.extend(changed[:12])

    for key in REQUIRED_W3D:
        if key not in a2:
            fails.append(f"required W3D not in ART_TWO: {key}")
        if key in a1:
            fails.append(f"required W3D unexpectedly in ART_ONE: {key}")

    for name in a2:
        if not is_w3d(name):
            fails.append(f"non-W3D in ART_TWO: {name}")
    for name in a1:
        if is_w3d(name):
            fails.append(f"W3D in ART_ONE: {name}")

    src_tex_basenames = {
        Path(n.replace("\\", "/")).name.lower() for n, _o, _s in src_index if not is_w3d(n)
    }
    tex_basenames = {Path(k.replace("\\", "/")).name.lower() for k in a1}
    for key in REQUIRED_W3D:
        if key not in a2:
            continue
        off, size = a2[key]
        for tex in sk.all_tex(a2_blob[off : off + size]):
            if tex.lower() in src_tex_basenames and tex.lower() not in tex_basenames:
                fails.append(f"{key} texture {tex} missing from ART_ONE")

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        required_zip = {
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "_SPEC_ART_TWO.big",
            "INSTALL.txt",
            "README.txt",
            "Launch_Specter.bat",
            "Install_SpecterPatch.bat",
        }
        for n in required_zip:
            if n not in names:
                fails.append(f"ZIP missing {n}")
        for big_name in ("_SPEC_DATA_ONE.big", "_SPEC_ART_ONE.big", "_SPEC_ART_TWO.big"):
            if big_name in names:
                mag = zf.open(big_name).read(4)
                if mag != b"BIGF":
                    fails.append(f"ZIP {big_name} magic {mag!r} is not BIGF")
        if "_SPEC_ART_ONE.big.gz" in names:
            fails.append("ZIP must not ship gzip ART as an install file")

    launch = launch_src.read_text(encoding="latin1")
    install = install_src.read_text(encoding="latin1")
    for label, text in (("Launch_Specter.bat", launch), ("Install_SpecterPatch.bat", install)):
        if "_SPEC_ART_TWO.big" not in text:
            fails.append(f"{label} does not install _SPEC_ART_TWO.big")

    if art1.stat().st_size >= SAGE_SAFE or art2.stat().st_size >= SAGE_SAFE:
        fails.append("an output ART archive is still over the SAGE 2GiB limit")

    lowers: dict[str, list[tuple[str, str]]] = {}
    for src, mp in ((art1.name, a1), (art2.name, a2)):
        for k in mp:
            lowers.setdefault(k.lower(), []).append((src, k))
    for hits in lowers.values():
        if len(hits) > 1:
            fails.append(f"ambiguous {hits}")

    return fails


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_ISRAEL_JERICHO_CHINA_D30_ICONS")
    if sk.sha256_path(SRC_ART) != SHA_ART_SRC or SRC_ART.stat().st_size != SIZE_ART_SRC:
        raise SystemExit("ART baseline is not SPECTER_ISRAEL_JERICHO_CHINA_D30_ICONS")

    src_blob = SRC_ART.read_bytes()
    archive_size, count, header_size, src_index = parse_index_mm(src_blob)
    if archive_size != len(src_blob) or count != len(src_index):
        raise SystemExit("source ART index is corrupt")

    tex_items = []
    w3d_items = []
    for name, off, size in src_index:
        if is_w3d(name):
            w3d_items.append((name, off, size))
        else:
            tex_items.append((name, off, size))
    if not tex_items or not w3d_items:
        raise SystemExit("split produced an empty archive")
    if len(tex_items) + len(w3d_items) != len(src_index):
        raise SystemExit("split dropped entries")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    data_path = OUT / "_SPEC_DATA_ONE.big"
    art1_path = OUT / "_SPEC_ART_ONE.big"
    art2_path = OUT / "_SPEC_ART_TWO.big"
    shutil.copy2(SRC_DATA, data_path)
    write_big_from_slices(art1_path, tex_items, src_blob)
    write_big_from_slices(art2_path, w3d_items, src_blob)
    del src_blob

    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    install_txt = "\n".join(
        [
            "SPECTER ART 2GiB SPLIT — INSTALL",
            "",
            "The previous single _SPEC_ART_ONE.big is larger than 2,147,483,648 bytes.",
            "Zero Hour stores BIG offsets in 32-bit fields, so W3D models past that",
            "boundary become invisible / white / untextured. DATA is unchanged.",
            "",
            "HOW THE GAME LOADS THESE FILES",
            "  Zero Hour auto-loads every *.big sitting next to generals.exe",
            "  (case-insensitive alphabetical order; later archives last-win).",
            "  SPECTER already uses that scan for _SPEC_DATA_ONE.big and",
            "  _SPEC_ART_ONE.big. Do NOT use generals.exe -mod (one archive only).",
            "  Place all three files in the SPECTER / game folder (same place as",
            "  the current _SPEC_* BIGs):",
            "",
            "    _SPEC_DATA_ONE.big   DATA (byte-identical to PR #655)",
            "    _SPEC_ART_ONE.big    textures (Art\\Textures\\*)",
            "    _SPEC_ART_TWO.big    models   (Art\\W3D\\*)",
            "",
            "  Load order of the SPECTER pair: ART_ONE, then ART_TWO, then DATA_ONE.",
            "  Texture and W3D keys are looked up across all loaded archives, the",
            "  same way vanilla Textures.big + W3D.big already work.",
            "",
            "STEPS",
            "  1. Close the game.",
            "  2. DELETE or REPLACE the old oversized _SPEC_ART_ONE.big",
            "     (2,451,295,403 bytes, SHA256 de0e9988...). Leaving it installed",
            "     keeps the broken offsets.",
            "  3. Copy these three uncompressed BIGs into the SPECTER folder:",
            "       _SPEC_DATA_ONE.big",
            "       _SPEC_ART_ONE.big",
            "       _SPEC_ART_TWO.big",
            "  4. Confirm each file starts with the four bytes BIGF.",
            "     Do not install any .gz / .gzip stream as a .big.",
            "  5. Optional: run Install_SpecterPatch.bat / Launch_Specter.bat from",
            "     this ZIP (they now copy ART_TWO as well).",
            "",
            "Do not keep a combined ART archive over 2,147,483,648 bytes.",
            "",
        ]
    )
    (OUT / "INSTALL.txt").write_text(install_txt, encoding="utf-8")

    zip_path = ROOT / "patch/Release/SPECTER_ART_SPLIT_2GIB.zip"
    (OUT / "README.txt").write_text(
        "SPECTER ART split: textures in _SPEC_ART_ONE.big, models in _SPEC_ART_TWO.big.\n"
        "DATA is unchanged. Place all three uncompressed BIGF files in the SPECTER folder.\n"
        "Delete the old oversized _SPEC_ART_ONE.big. Do not install gzip as .big.\n"
        "Static validation only. The game was not launched.\n",
        encoding="utf-8",
    )
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art1_path, "_SPEC_ART_ONE.big")
        zf.write(art2_path, "_SPEC_ART_TWO.big")
        zf.write(OUT / "INSTALL.txt", "INSTALL.txt")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "Launch_Specter.bat", "Launch_Specter.bat")
        zf.write(OUT / "Install_SpecterPatch.bat", "Install_SpecterPatch.bat")

    # Re-open source ART for hash comparison (released after del).
    src_mm = SRC_ART.read_bytes()
    _, _, _, src_index = parse_index_mm(src_mm)
    fails = validate(
        src_index,
        src_mm,
        art1_path,
        art2_path,
        data_path,
        zip_path,
        INSTALLER / "Launch_Specter.bat",
        INSTALLER / "Install_SpecterPatch.bat",
    )
    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    data_sha = sk.sha256_path(data_path)
    art1_sha = sk.sha256_path(art1_path)
    art2_sha = sk.sha256_path(art2_path)
    zip_sha = sk.sha256_path(zip_path)

    a2_blob, a2 = index_map(art2_path)
    w3d_lines = []
    for key in REQUIRED_W3D:
        o, s = a2[key]
        w3d_lines.append(
            f"  {key} ART_TWO off={o} size={s} sha256={sha256_slice(a2_blob, o, s)}"
        )

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #655 s-israel-jericho-china-d30-icons ART/DATA",
        "DATA_UNCHANGED=YES",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_ONE_SIZE={art1_path.stat().st_size}",
        f"ART_ONE_SHA256={art1_sha}",
        f"ART_TWO_SIZE={art2_path.stat().st_size}",
        f"ART_TWO_SHA256={art2_sha}",
        f"ART_ONE_ENTRIES={len(tex_items)}",
        f"ART_TWO_ENTRIES={len(w3d_items)}",
        f"UNION_ENTRIES={len(tex_items)+len(w3d_items)}",
        f"SOURCE_ENTRIES={len(src_index)}",
        f"SAGE_SAFE_LIMIT={SAGE_SAFE}",
        "SIGNED_OFFSETS_OK=YES",
        "UNION_HASH_MATCH=YES",
        "CROSS_ARCHIVE_DUP=NO",
        "GZIP_NOT_INSTALLED_AS_BIG=YES",
        "LOAD_CONVENTION=ZH auto-loads every *.big next to generals.exe",
        "ART_TWO_FILENAME=_SPEC_ART_TWO.big",
        "",
        "REQUIRED W3D (ART_TWO, signed-safe offsets):",
        *w3d_lines,
        "",
        "MANUAL IN-GAME CHECKLIST (not run here):",
        "  USA Command Center / War Factory / Supply (US_Command, US_WarFactory, US_Supply)",
        "  China Command Center (Chi_Hq)",
        "  Arabic Alliance / GLA Command Center (Arb_Command)",
        "  Iran Command Center (Iran_Command)",
        "  Israel Command Center (US_Command mesh)",
        "  Britain or Turkey Command Center (US_Command mesh)",
        "  Confirm models are textured, not invisible/white.",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    hashes = "\n".join(
        [
            "DATA_CHANGED=NO",
            "ART_CHANGED=YES_SPLIT",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_ONE_SIZE={art1_path.stat().st_size}",
            f"ART_ONE_SHA256={art1_sha}",
            f"ART_TWO_SIZE={art2_path.stat().st_size}",
            f"ART_TWO_SHA256={art2_sha}",
            "ZIP_FILE=SPECTER_ART_SPLIT_2GIB.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #655",
            "STATIC_VALIDATION=PASS",
            "RUNTIME_TEST=NOT RUN",
            "",
        ]
    )
    (OUT / "HASHES.txt").write_text(hashes)
    rel_base = "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-art-split-2gib"
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA (unchanged from PR #655):",
                f"  {rel_base}/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART textures (uncompressed BIGF, under SAGE 2GiB limit):",
                f"  {rel_base}/_SPEC_ART_ONE.big",
                f"  SIZE={art1_path.stat().st_size}",
                f"  SHA256={art1_sha}",
                "",
                "ART models (uncompressed BIGF, under SAGE 2GiB limit):",
                f"  {rel_base}/_SPEC_ART_TWO.big",
                f"  SIZE={art2_path.stat().st_size}",
                f"  SHA256={art2_sha}",
                "",
                "ZIP (DATA + both ART BIGs + INSTALL + launcher):",
                f"  {rel_base}/SPECTER_ART_SPLIT_2GIB.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place all three uncompressed BIGs in the SPECTER folder.",
                "Delete the old oversized _SPEC_ART_ONE.big first.",
                "Do not install gzip as .big. Every .big must start with BIGF.",
                "TAG=s-art-split-2gib",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-art-split-2gib",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# SPECTER ART 2GiB split — restore building models\n\n"
        "The packed ART from PR #650 onward is larger than 2,147,483,648 bytes. "
        "SAGE 32-bit BIG offsets cannot read W3Ds past that boundary, so buildings "
        "stay constructible (DATA) but render invisible/white/untextured.\n\n"
        "This pack splits ART into `_SPEC_ART_ONE.big` (textures) and "
        "`_SPEC_ART_TWO.big` (W3Ds). Every original ART entry is preserved "
        "byte-for-byte. DATA is unchanged.\n\n"
        "Zero Hour auto-loads every `*.big` next to `generals.exe`. Put all three "
        "files in the SPECTER folder and delete the old oversized ART_ONE.\n\n"
        "Static validation only. The game was not launched.\n",
        encoding="utf-8",
    )
    (OUT / "CONFLICTS.txt").write_text(
        "Replaces the oversized single _SPEC_ART_ONE.big (SHA de0e9988..., 2451295403 bytes).\n"
        "Does not modify DATA last-wins, missile INIs, Draw modules, or faction content.\n"
        "Do not keep the old oversized ART_ONE beside ART_TWO.\n"
        "Launcher scripts now require _SPEC_ART_TWO.big next to ART_ONE and DATA_ONE.\n",
        encoding="utf-8",
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:40]))


if __name__ == "__main__":
    main()
