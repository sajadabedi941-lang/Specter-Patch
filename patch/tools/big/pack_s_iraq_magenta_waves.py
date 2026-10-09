#!/usr/bin/env python3
"""Fix magenta ocean/wave tiles: restore missing Water.ini texture names.

Packed last-wins (PR #598 ART+DATA, ART byte-identical to PR #593):

  Data\\INI\\Water.ini (unchanged vs PR #593) last-wins:

    WaterSet MORNING/AFTERNOON  SkyTexture = TSCloudWis.tga
    WaterSet *                  WaterTexture = TSWater.tga
    WaterTransparency           StandingWaterTexture = TWWater01.tga

  SPECTER ART has TSWater.tga and the WTR wave-mesh env map TSCloudWit.tga,
  but it has never contained TWWater01.tga or TSCloudWis.tga (checked every
  ART BIG in this repo, including COMPLETE and ROLLBACK). SAGE missing-texture
  color is bright magenta. Standing water is drawn as a grid of wave/tile
  segments, which matches the in-game report.

  WTR*.W3D wave meshes already reference existing TSNoiseM.tga / TSCloudWit.tga
  (not missing). Water.ini itself was not changed by PR #594-#598. This is a
  complete-replacement ART hole vs vanilla Water.ini names.

Fix (smallest ART last-wins add, same archive, no unrelated donor rebuild):

  Art\\Textures\\TWWater01.tga  <- copy of Art\\Textures\\TSWater.tga
  Art\\Textures\\TSCloudWis.tga <- copy of Art\\Textures\\TSCloudWit.tga

DATA is copied byte-identical from PR #598 (factory spawn-control preserved).
Factory rearm stays off. Runtime visual test is not performed here.
"""
from __future__ import annotations

import hashlib
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_SPAWN_CONTROL/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_SPAWN_CONTROL/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MAGENTA_WAVES"

SHA_DATA_598 = "ec066f71382d3d1d732d4a9cdde54ffee86258eb0362aa0c8087155bc5e7f4d8"
SIZE_DATA_598 = 366615017
SHA_ART_593 = "95a0737f7f6e7d0f15a2a1234b222d1cf9643d1199b00e28e7e87e7c89083ed4"
SIZE_ART_593 = 1294467676

WATER_INI = r"Data\INI\Water.ini"
TSWATER = r"Art\Textures\TSWater.tga"
TSCLOUDWIT = r"Art\Textures\TSCloudWit.tga"
TWWATER01 = r"Art\Textures\TWWater01.tga"
TSCLOUDWIS = r"Art\Textures\TSCloudWis.tga"

WATER_INI_TEXTURES = [
    "TSCloudWis.tga",
    "TSWater.tga",
    "TSCloudSun.tga",
    "TSStarFeld.tga",
    "TWWater01.tga",
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


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


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


def art_basename_map(files: dict[str, bytes]) -> dict[str, str]:
    out: dict[str, str] = {}
    for name in files:
        out[name.replace("/", "\\").split("\\")[-1].lower()] = name
    return out


def validate(art: dict[str, bytes], data: dict[str, bytes], src_art: dict[str, bytes]) -> list[str]:
    fails = []
    water = data[WATER_INI].decode("latin1")
    if "StandingWaterTexture = TWWater01.tga" not in water:
        fails.append("Water.ini StandingWaterTexture changed")
    if "SkyTexture = TSCloudWis.tga" not in water:
        fails.append("Water.ini SkyTexture TSCloudWis missing")
    names = art_basename_map(art)
    for tex in WATER_INI_TEXTURES:
        if tex.lower() not in names:
            fails.append(f"Water.ini texture still missing from ART: {tex}")
    if TWWATER01 not in art:
        fails.append("TWWater01.tga path missing")
    elif art[TWWATER01] != src_art[TSWATER]:
        fails.append("TWWater01.tga is not the in-archive TSWater.tga copy")
    if TSCLOUDWIS not in art:
        fails.append("TSCloudWis.tga path missing")
    elif art[TSCLOUDWIS] != src_art[TSCLOUDWIT]:
        fails.append("TSCloudWis.tga is not the in-archive TSCloudWit.tga copy")
    src_keys = set(src_art)
    new_keys = set(art)
    added = sorted(new_keys - src_keys)
    removed = sorted(src_keys - new_keys)
    if added != [TSCLOUDWIS, TWWATER01] and added != [TWWATER01, TSCLOUDWIS]:
        fails.append(f"unexpected ART adds: {added}")
    if removed:
        fails.append(f"ART removed files: {removed}")
    for k in src_keys:
        if art.get(k) != src_art[k]:
            fails.append(f"unrelated ART mutated: {k}")
            break
    lows = {}
    for n in art:
        lows.setdefault(n.replace("/", "\\").lower(), []).append(n)
    for low, names_list in lows.items():
        if len(names_list) > 1:
            fails.append(f"duplicate ART path {names_list}")
    return fails


def main() -> int:
    if sha256_path(SRC_DATA) != SHA_DATA_598 or SRC_DATA.stat().st_size != SIZE_DATA_598:
        raise SystemExit("PR #598 DATA mismatch")
    if sha256_path(SRC_ART) != SHA_ART_593 or SRC_ART.stat().st_size != SIZE_ART_593:
        raise SystemExit("PR #593/#598 ART mismatch")

    src_art = parse_big(SRC_ART.read_bytes())
    src_data = parse_big(SRC_DATA.read_bytes())
    if TSWATER not in src_art or TSCLOUDWIT not in src_art:
        raise SystemExit("donor textures missing from current ART")
    if TWWATER01 in src_art or TSCLOUDWIS in src_art:
        raise SystemExit("expected missing names already present")

    art = dict(src_art)
    art[TWWATER01] = src_art[TSWATER]
    art[TSCLOUDWIS] = src_art[TSCLOUDWIT]

    tex_dir = ROOT / "patch/Art/Textures"
    tex_dir.mkdir(parents=True, exist_ok=True)
    (tex_dir / "TWWater01.tga").write_bytes(art[TWWATER01])
    (tex_dir / "TSCloudWis.tga").write_bytes(art[TSCLOUDWIS])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    packed_art = build_big(art)
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art.write_bytes(packed_art)
    shutil.copy2(SRC_DATA, out_data)

    extracted_art = parse_big(out_art.read_bytes())
    extracted_data = parse_big(out_data.read_bytes())
    fails = validate(extracted_art, extracted_data, src_art)
    fails.extend(f"ART {x}" for x in big_structure_ok(packed_art))
    data_sha = sha256_path(out_data)
    art_sha = sha256_path(out_art)
    if data_sha != SHA_DATA_598:
        fails.append("DATA is not byte-identical to PR #598")

    added = sorted(set(extracted_art) - set(src_art))
    report = [
        "# SPECTER magenta ocean/wave tiles: missing Water.ini textures",
        "",
        "ROOT CAUSE: packed last-wins Data\\INI\\Water.ini (same as PR #593)",
        "names StandingWaterTexture TWWater01.tga and SkyTexture TSCloudWis.tga.",
        "Neither file exists in SPECTER ART (PR #593/#598, COMPLETE, ROLLBACK).",
        "SAGE missing textures render bright magenta. Standing water is a grid",
        "of wave/tile segments. WTR wave meshes already resolve in ART.",
        "PR #598 DATA was not the cause; factory spawn-control DATA is unchanged.",
        "",
        "FIX: add two last-wins ART aliases copied from this same ART archive:",
        f"  {TWWATER01}  <- {TSWATER}  sha {sha256_bytes(art[TWWATER01])}",
        f"  {TSCLOUDWIS} <- {TSCLOUDWIT} sha {sha256_bytes(art[TSCLOUDWIS])}",
        "",
        f"- DATA size: {out_data.stat().st_size} (UNCHANGED vs PR #598)",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted_data)}",
        f"- ART size: {out_art.stat().st_size}",
        f"- ART SHA256: {art_sha}",
        f"- ART files: {len(extracted_art)} (was {len(src_art)}; added {', '.join(added)})",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        report.append("RUNTIME_TEST=NOT RUN")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static / packed last-wins)",
        "- DATA SHA-256 identical to PR #598 spawn-control",
        "- Water.ini StandingWaterTexture / SkyTexture names unchanged",
        "- TWWater01.tga and TSCloudWis.tga now present and match in-archive donors",
        "- All Water.ini texture basenames resolve in ART (case-insensitive)",
        "- No other ART files added, removed, or mutated; no path duplicates",
        "",
        "Static validation completed; runtime game test not performed.",
        "Magenta water is NOT claimed fixed. Unresolved: look at ocean tiles in Zero Hour.",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=NO\n"
        "ART_CHANGED=YES\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted_data)}\n"
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={out_art.stat().st_size}\n"
        f"ART_SHA256={art_sha}\n"
        f"ART_FILES={len(extracted_art)}\n"
        f"ART_ADDED={', '.join(added)}\n"
        f"TWWATER01_SHA256={sha256_bytes(art[TWWATER01])}\n"
        f"TWWATER01_DONOR={TSWATER}\n"
        f"TSCLOUDWIS_SHA256={sha256_bytes(art[TSCLOUDWIS])}\n"
        f"TSCLOUDWIS_DONOR={TSCLOUDWIT}\n"
        "ROOT_CAUSE=Water.ini TWWater01.tga and TSCloudWis.tga missing from SPECTER ART\n"
        "FIX=alias copies from TSWater.tga and TSCloudWit.tga already in this ART\n"
        "BASELINE=PR #598 DATA (byte-identical) + PR #593 ART + 2 texture aliases\n"
        "FACTORY_REARM=STILL REMOVED from A-J\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n"
        "MAGENTA_WATER_CLAIMED_FIXED=NO\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: magenta ocean/wave tile fix\n"
        "\n"
        "Adds TWWater01.tga and TSCloudWis.tga to ART so Water.ini last-wins\n"
        "names resolve. DATA is unchanged from PR #598 spawn-control.\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big  (same as PR #598)\n"
        "  _SPEC_ART_ONE.big   (PR #593 ART + two texture aliases)\n"
        "\n"
        "Static validation completed; runtime visual test not performed.\n",
        encoding="utf-8",
    )
    (OUT / "ROOT_CAUSE.txt").write_text(
        "Offending references (Data\\INI\\Water.ini last-wins):\n"
        "  StandingWaterTexture = TWWater01.tga   (missing from ART)\n"
        "  SkyTexture           = TSCloudWis.tga  (MORNING/AFTERNOON; missing from ART)\n"
        "\n"
        "Not the cause:\n"
        "  WTR*.W3D wave meshes (TSNoiseM.tga / TSCloudWit.tga present)\n"
        "  PR #598 factory object/weapon DATA (byte-identical, rearm still off)\n"
        "  ART file mutations vs PR #593 (ART was byte-identical before this add)\n"
        "\n"
        "SAGE draws missing textures as bright magenta. Standing water is a\n"
        "tessellated grid, which appears as magenta wave/tile segments.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_MAGENTA_WAVES.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
        zf.write(OUT / "ROOT_CAUSE.txt", "ROOT_CAUSE.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
