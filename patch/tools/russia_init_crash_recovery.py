#!/usr/bin/env python3
"""Emergency recovery: roll back ONLY the latest Russia aircraft cleanup.

LAST_GOOD_RUNTIME = commit 7c90bd56 (global airbase ART recovery package vwt6az)
  — last package where user reported in-game aircraft visuals (game launched).

CRASH_BUILD = commit 60880343 / package 0h5vt9 (FINAL RUSSIA AIRCRAFT CLEANUP)

This script:
  1) Diffs last-good vs crash BIGs (report)
  2) Stages COMPLETE last-good DATA+ART into NEW empty folders
  3) Rebuilds _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big from clean staging
  4) Re-extracts and verifies cleanup-touched files match last-good
  5) Confirms crash-only ART assets are absent; T50 remains disabled
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
MASTER = ROOT / "patch/Release/SPECTER_MASTER"
WORK = Path("/tmp/russia_recovery")
LAST_GOOD_DIR = WORK / "last_good"
CRASH_DIR = WORK / "crash"
STAGE_DATA = WORK / "stage_data_clean"
STAGE_ART = WORK / "stage_art_clean"
VERIFY_DATA = WORK / "verify_data_recovery"
VERIFY_ART = WORK / "verify_art_recovery"
ZIP_OUT = ROOT / "patch/Release/SPECTER_MASTER_DATA_ART_RUSSIA_INIT_CRASH_RECOVERY.zip"
REPORT = ROOT / "patch/Release/DATA_RUSSIA_INIT_CRASH_RECOVERY_REPORT.txt"

LAST_GOOD_COMMIT = "7c90bd56"
LAST_GOOD_MSG = "Recover global airbases: pack missing TheAirPort ART meshes."
LAST_GOOD_DATA_SHA = "a3eace60486397c772d9020fef7cd382363e33c86ecb08ab2de0629bd1cbf749"
LAST_GOOD_ART_SHA = "248172a4a1ddfc66743b16016a29b7a2fd70a3389107599b899c041f98f1c592"
CRASH_COMMIT = "60880343"
CRASH_MSG = "Russia aircraft cleanup: fix visuals, wings, icons, and slots."
CRASH_DATA_SHA = "ed2b2eb4c4571c0b1aad3404c9597a30b32af9b9e503a9ea50d168f11e4a2c02"
CRASH_ART_SHA = "addeca8ba2944be12053dd167e70965924c608bc000abc56c74e826d442b1c7d"

CRASH_ONLY_ART = [
    r"Art\Textures\A_E-3_100.tga",
    r"Art\Textures\CWCgenPropellor.dds",
    r"Art\Textures\CWCgenReflective.dds",
    r"Art\Textures\CWCgenReflective.tga",
    r"Art\Textures\LSFRussiaTU160.dds",
    r"Art\Textures\LSFRussiaTU160d.dds",
    r"Art\Textures\LSFRussiaTU160k.dds",
    r"Art\Textures\SU24TB.tga",
    r"Art\Textures\TU22M3.tga",
    r"Art\Textures\TU22M3TB.tga",
    r"Art\Textures\autreSU24.tga",
    r"Art\Textures\autreSU24TB.tga",
    r"Art\Textures\yujing1.dds",
    r"Art\W3D\LSFRussiaTu160.W3D",
    r"Art\W3D\LSFRussiaTu160d.W3D",
    r"Art\W3D\LSFRussiaTu160k.W3D",
]

CLEANUP_DATA_FILES = [
    r"Data\English\SPECTER_RUSSIA_AIRCRAFT_EXPANSION_Strings.txt",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\MappedImages\HandCreated\Russia_DonorAircraftIcons.INI",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\RussiaJetA50Visual.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\RussiaJetAn225Visual.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\RussiaJetTU160Clean.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\RussiaJetTu95Visual.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\SU24M2.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\SU24MP.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\SU34M.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\TU22M3M.ini",
]


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name] = data[off : off + size]
    return files


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
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
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def extract_big_to_dir(big_path: Path, out_dir: Path) -> dict[str, bytes]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    files = read_big(big_path)
    for name, content in files.items():
        # BIG paths use backslash; write flat-safe mirrored tree on Linux
        rel = Path(*name.split("\\"))
        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
    return files


def stage_from_big_map(files: dict[str, bytes], stage_dir: Path) -> None:
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True)
    for name, content in files.items():
        rel = Path(*name.split("\\"))
        dest = stage_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)


def collect_stage(stage_dir: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for p in stage_dir.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(stage_dir)
        # rebuild BIG key with backslashes
        key = "\\".join(rel.parts)
        out[key] = p.read_bytes()
    return out


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def categorize(path: str) -> str:
    p = path.lower().replace("\\", "/")
    if "tu95" in p or "tu-95" in p:
        return "A. Tu-95"
    if "an225" in p or "an-225" in p:
        return "B. An-225"
    if "russiajeta50" in p or re.search(r"(^|/)a[_-]?50", p):
        return "C. A-50"
    if "tu160" in p or "tu-160" in p or "lsfrussiatu160" in p:
        return "D. Tu-160"
    if "il76" in p or "yier76" in p or "yujing" in p or "avionil76" in p:
        return "E. avionIL76"
    if "su24mp" in p or "su24mr" in p or "autresu24" in p:
        return "F. Su-24MR"
    if "su24m2" in p:
        return "G. Su-24M2"
    if "su34" in p:
        return "H. Su-34M"
    if "tu22" in p:
        return "I. Tu-22M3M"
    if any(
        x in p
        for x in (
            "commandset.ini",
            "commandbutton.ini",
            "mappedimage",
            "generals.csf",
            "strings.txt",
        )
    ):
        return "J. shared CommandSet/CommandButton/CSF/MappedImage"
    return "K. unexpected / shared support assets"


def main() -> int:
    lg_data_path = LAST_GOOD_DIR / "_SPEC_DATA_ONE.big"
    lg_art_path = LAST_GOOD_DIR / "_SPEC_ART_ONE.big"
    cr_data_path = CRASH_DIR / "_SPEC_DATA_ONE.big"
    cr_art_path = CRASH_DIR / "_SPEC_ART_ONE.big"
    for p in (lg_data_path, lg_art_path, cr_data_path, cr_art_path):
        if not p.exists():
            raise SystemExit(f"Missing required package extract: {p}")

    assert sha256(lg_data_path.read_bytes()) == LAST_GOOD_DATA_SHA
    assert sha256(lg_art_path.read_bytes()) == LAST_GOOD_ART_SHA
    assert sha256(cr_data_path.read_bytes()) == CRASH_DATA_SHA
    assert sha256(cr_art_path.read_bytes()) == CRASH_ART_SHA

    lg_data = read_big(lg_data_path)
    lg_art = read_big(lg_art_path)
    cr_data = read_big(cr_data_path)
    cr_art = read_big(cr_art_path)

    # Diff
    data_changed = sorted(k for k in lg_data if k in cr_data and lg_data[k] != cr_data[k])
    data_added = sorted(set(cr_data) - set(lg_data))
    data_removed = sorted(set(lg_data) - set(cr_data))
    art_added = sorted(set(cr_art) - set(lg_art))
    art_removed = sorted(set(lg_art) - set(cr_art))
    art_changed = sorted(k for k in lg_art if k in cr_art and lg_art[k] != cr_art[k])

    # Clean staging from COMPLETE last-good trees
    stage_from_big_map(lg_data, STAGE_DATA)
    stage_from_big_map(lg_art, STAGE_ART)

    # Rebuild BIGs from clean staging (not in-place edit of crash BIGs)
    staged_data = collect_stage(STAGE_DATA)
    staged_art = collect_stage(STAGE_ART)
    assert set(staged_data) == set(lg_data)
    assert set(staged_art) == set(lg_art)
    for k in lg_data:
        assert staged_data[k] == lg_data[k], k
    for k in lg_art:
        assert staged_art[k] == lg_art[k], k

    new_data = build_big(staged_data)
    new_art = build_big(staged_art)

    MASTER.mkdir(parents=True, exist_ok=True)
    (MASTER / "_SPEC_DATA_ONE.big").write_bytes(new_data)
    (MASTER / "_SPEC_ART_ONE.big").write_bytes(new_art)

    # Re-extract verification
    v_data = extract_big_to_dir(MASTER / "_SPEC_DATA_ONE.big", VERIFY_DATA)
    v_art = extract_big_to_dir(MASTER / "_SPEC_ART_ONE.big", VERIFY_ART)

    # Cleanup-touched DATA must match last-good exactly
    for k in CLEANUP_DATA_FILES:
        assert k in v_data, f"missing in recovery DATA: {k}"
        assert v_data[k] == lg_data[k], f"DATA mismatch vs last-good: {k}"
        assert v_data[k] != cr_data[k] or lg_data[k] == cr_data[k], f"still crash bytes?: {k}"

    # Crash-only ART must be absent
    stale_art = [k for k in CRASH_ONLY_ART if k in v_art]
    assert not stale_art, f"stale crash ART remaining: {stale_art}"

    # Full ART inventory must equal last-good
    assert set(v_art) == set(lg_art)
    for k in lg_art:
        assert v_art[k] == lg_art[k], k

    # Full DATA inventory must equal last-good
    assert set(v_data) == set(lg_data)
    for k in lg_data:
        assert v_data[k] == lg_data[k], k

    # T50 safety
    t50_files = [k for k in v_data if "t50" in k.lower() or "pakfa" in k.lower()]
    assert not t50_files, t50_files
    t50_object_refs = []
    for k, blob in v_data.items():
        if re.search(rb"RussiaJetT50|russiajett50pakfaclean", blob, re.I):
            t50_object_refs.append(k)
    # strings file may mention T50 historically; Object INI must be absent
    bad = [k for k in t50_object_refs if k.lower().endswith(".ini") and "object" in k.lower()]
    assert not bad, bad

    # Airbase ART preserved from last-good
    for mesh in (r"Art\W3D\TheAirPort.W3D", r"Art\W3D\HXUSABigAirPort.W3D", r"Art\Textures\CJJCWUJUN.dds"):
        assert mesh in v_art
        assert v_art[mesh] == lg_art[mesh]

    data_sha = sha256(new_data)
    art_sha = sha256(new_art)

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(MASTER / "_SPEC_DATA_ONE.big", arcname="_SPEC_DATA_ONE.big")
        zf.write(MASTER / "_SPEC_ART_ONE.big", arcname="_SPEC_ART_ONE.big")

    # Report
    lines: list[str] = []
    lines.append("RUSSIA INIT-CRASH RECOVERY = PASS")
    lines.append("")
    lines.append("Crash type =")
    lines.append("Uncaught Exception during initialization")
    lines.append("")
    lines.append("INI parser line available = NO")
    lines.append("")
    lines.append(f"Last user-tested good commit = {LAST_GOOD_COMMIT} ({LAST_GOOD_MSG})")
    lines.append("Evidence = user reported in-game Tu-160/aircraft visual bugs after airbase recovery package")
    lines.append(f"  package = https://litter.catbox.moe/vwt6az.zip")
    lines.append(f"  DATA sha256 = {LAST_GOOD_DATA_SHA}")
    lines.append(f"  ART  sha256 = {LAST_GOOD_ART_SHA}")
    lines.append("")
    lines.append(f"Crash cleanup commit = {CRASH_COMMIT} ({CRASH_MSG})")
    lines.append(f"  package = https://litter.catbox.moe/0h5vt9.zip")
    lines.append(f"  DATA sha256 = {CRASH_DATA_SHA}")
    lines.append(f"  ART  sha256 = {CRASH_ART_SHA}")
    lines.append("")
    lines.append("------------------------------")
    lines.append("DIFF: LAST_GOOD vs CRASH CLEANUP")
    lines.append("------------------------------")
    lines.append(f"Latest cleanup DATA files changed = {len(data_changed)} modified, {len(data_added)} added, {len(data_removed)} deleted")
    for k in data_changed:
        lines.append(f"  DATA MOD [{categorize(k)}] {k}")
    for k in data_added:
        lines.append(f"  DATA ADD [{categorize(k)}] {k}")
    for k in data_removed:
        lines.append(f"  DATA DEL [{categorize(k)}] {k}")
    lines.append("")
    lines.append(f"Latest cleanup ART files changed = {len(art_changed)} modified, {len(art_added)} added, {len(art_removed)} deleted")
    for k in art_added:
        lines.append(f"  ART ADD [{categorize(k)}] {k}")
    for k in art_changed:
        lines.append(f"  ART MOD [{categorize(k)}] {k}")
    for k in art_removed:
        lines.append(f"  ART DEL [{categorize(k)}] {k}")
    lines.append("")
    unexpected = [k for k in data_changed + art_added if categorize(k).startswith("K.")]
    lines.append("Unexpected shared/global files changed =")
    if unexpected:
        for k in unexpected:
            lines.append(f"  {k}")
    else:
        lines.append("  (none beyond cleanup-related support textures categorized as K)")
    # Note shared globals specifically
    shared = [k for k in data_changed if categorize(k).startswith("J.")]
    lines.append("Shared/global DATA touched by cleanup =")
    for k in shared:
        lines.append(f"  {k}")
    lines.append("")
    lines.append("------------------------------")
    lines.append("RECOVERY BUILD")
    lines.append("------------------------------")
    lines.append("Latest Russia cleanup rolled back = YES")
    lines.append("T50 broken legacy file remains disabled = YES")
    lines.append("  (no russiajett50pakfaclean.ini in DATA)")
    lines.append("Global airbase infrastructure preserved = YES")
    lines.append("  (TheAirPort.W3D / HXUSABigAirPort.W3D / CJJCWUJUN.dds retained from last-good)")
    lines.append("Other factions preserved = YES")
    lines.append("DATA built from complete clean staging = YES")
    lines.append("ART built from complete clean staging = YES")
    lines.append("FINAL extracted DATA matches last-good state for latest-cleanup files = YES")
    lines.append("FINAL extracted ART matches last-good state for latest-cleanup files = YES")
    lines.append(f"Stale crashing-build W3Ds remaining = {len(stale_art)}")
    lines.append("Stale crashing-build animation references remaining = 0")
    lines.append("  (Tu-160 LSFRussiaTu160 Draw/AnimationState rollback with Object INI)")
    lines.append("")
    lines.append(f"RECOVERY DATA sha256 = {data_sha}")
    lines.append(f"RECOVERY ART  sha256 = {art_sha}")
    lines.append(f"ZIP = {ZIP_OUT}")
    lines.append("")
    lines.append("------------------------------")
    lines.append("NEXT ISOLATION PLAN (REPORT ONLY — DO NOT APPLY YET)")
    lines.append("------------------------------")
    lines.append("GROUP 1: button/UI-only changes (Tu-22M3M / Su-24 icons, MappedImage, CSF)")
    lines.append("GROUP 2: Su-24MR / Su-24M2 / Su-34M CommandSet movement")
    lines.append("GROUP 3: avionIL76 duplicate cleanup / yujing1 texture")
    lines.append("GROUP 4: Tu-95 visual family (CWCgenPropellor/Reflective + Draw)")
    lines.append("GROUP 5: An-225 visual family (A_AN225 + A_E-3_100)")
    lines.append("GROUP 6: A-50 visual family")
    lines.append("GROUP 7: Tu-160 variable-wing visual/animation (LAST — highest risk)")
    lines.append("")
    lines.append("IMPORTANT: DO NOT CLAIM GAME-TESTED PASS.")
    lines.append("Wait for user confirmation that the game launches before any reapplication.")

    text = "\n".join(lines) + "\n"
    REPORT.write_text(text, encoding="utf-8")
    (WORK / "RECOVERY_REPORT.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
