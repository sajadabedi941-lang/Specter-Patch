#!/usr/bin/env python3
"""Build and validate _SPECTER_PATCH_FINAL_CLEAN.big from canonical patch/Data + Art.

Steps:
  1. Scan SPEC DATA + staged overlay for Object collisions / Egypt_CommandCenter versions
  2. Exclude obsolete/dangerous files from the pack
  3. Pack overlay BIG
  4. Simulate Zero Hour BIG load order (case-insensitive) with _SPEC_DATA_ONE.big
  5. Fail if Egypt_CommandCenter is not the latest repaired version
  6. Fail on duplicate Objects under Data\\INI
  7. Only then write the CLEAN artifact

Does NOT modify original _SPEC_* BIGs.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import struct
import sys
from collections import defaultdict
from pathlib import Path

OBJ_RE = re.compile(rb"^(Object|ChildObject|ObjectReskin)\s+(\S+)", re.M)
EGYPT_CC_PATH = (
    r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_CommandCenter.ini"
)

# Files excluded from CLEAN pack (obsolete / misplaced / superseding risk)
EXCLUDE_REL_POSIX = {
    # Misplaced stock AirF object inside Israel folder — SPEC already has this path;
    # shipping it again adds no repair value. Neutralized separately if needed.
    "Data/INI/Object/Specter/Israel Defense Forces/Buildings/Industry Planet.ini",
}


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
        name = data[off:end].decode("latin1", errors="replace")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
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
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def egypt_is_repaired(content: bytes) -> tuple[bool, list[str]]:
    text = content.decode("utf-8", errors="replace")
    issues = []
    if "Object Egypt_CommandCenter" not in text:
        issues.append("missing Object Egypt_CommandCenter")
    if "irq_comndcntr" in text:
        issues.append("broken irq_comndcntr portrait")
    if "Iraq_Adnan1" in text:
        issues.append("broken Iraq_Adnan1 gunship")
    if "US_E3G_AWACS" not in text:
        issues.append("missing US_E3G_AWACS gunship")
    if "us_commandcenter" not in text:
        issues.append("missing us_commandcenter ART")
    if not re.search(r"^\s*BuildCost\s*=\s*2000\b", text, re.M):
        issues.append("BuildCost != 2000")
    if not re.search(r"^\s*MaxHealth\s*=\s*5000", text, re.M):
        issues.append("MaxHealth != 5000")
    if "P00" in text and "BuildCost" not in text:
        issues.append("P00 field corruption")
    if "h00.0" in text:
        issues.append("h00.0 field corruption")
    return (not issues), issues


def index_objects(file_map: dict[str, bytes], prefix_filter: str | None = "data\\ini\\"):
    obj_map: dict[str, list[str]] = defaultdict(list)
    for name, content in file_map.items():
        key = name.replace("/", "\\")
        if prefix_filter and not key.lower().startswith(prefix_filter):
            continue
        if not key.lower().endswith(".ini"):
            continue
        for m in OBJ_RE.finditer(content):
            obj_map[m.group(2).decode("latin1")].append(name)
    return obj_map


def stage_patch(patch_root: Path, stage: Path) -> dict[str, bytes]:
    if stage.exists():
        shutil.rmtree(stage)
    data_src = patch_root / "Data"
    art_src = patch_root / "Art"
    file_map: dict[str, bytes] = {}

    for path in sorted(data_src.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(data_src).as_posix()
        posix_key = "Data/" + rel
        if posix_key in EXCLUDE_REL_POSIX:
            continue
        big_name = ("Data\\" + rel.replace("/", "\\"))
        content = path.read_bytes()
        dest = stage / "Data" / Path(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        file_map[big_name] = content

    if art_src.exists():
        for path in sorted(art_src.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(patch_root).as_posix()
            big_name = rel.replace("/", "\\")
            content = path.read_bytes()
            dest = stage / Path(rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
            file_map[big_name] = content

    return file_map


def simulate_zh_load(spec: dict[str, bytes], overlay: dict[str, bytes]) -> dict[str, bytes]:
    """Case-insensitive BIG name order: _SPEC_DATA then _SPECTER_PATCH_* wins same paths."""
    final = dict(spec)
    final.update(overlay)
    return final


def validate_startup(final: dict[str, bytes], overlay: dict[str, bytes], report: list[str]) -> bool:
    ok = True

    # 1) Egypt_CommandCenter single path + repaired
    eg_paths = [n for n in final if "egypt" in n.lower() and "commandcenter" in n.lower().replace("_", "")]
    # tighter
    eg_paths = [n for n in final if n.replace("/", "\\").lower().endswith("egypt_commandcenter.ini")]
    report.append(f"Egypt_CommandCenter.ini paths in final load: {eg_paths}")
    if len(eg_paths) != 1:
        report.append(f"FAIL: expected exactly 1 Egypt_CommandCenter.ini path, got {len(eg_paths)}")
        ok = False
    else:
        content = final[eg_paths[0]]
        # Must come from overlay (repaired), not SPEC broken
        if eg_paths[0] not in overlay:
            report.append("FAIL: Egypt_CommandCenter not provided by overlay")
            ok = False
        if overlay.get(eg_paths[0]) != content:
            report.append("FAIL: loaded Egypt_CommandCenter is not overlay bytes")
            ok = False
        repaired, issues = egypt_is_repaired(content)
        if not repaired:
            report.append(f"FAIL: Egypt_CommandCenter not repaired: {issues}")
            ok = False
        else:
            report.append(
                f"PASS: Egypt_CommandCenter repaired sha256={hashlib.sha256(content).hexdigest()}"
            )
        # Ensure SPEC broken markers are not what loaded
        if b"irq_comndcntr" in content or b"Iraq_Adnan1" in content:
            report.append("FAIL: loaded Egypt still has broken Iraq markers")
            ok = False

    # 2) No duplicate Objects under Data\INI
    obj_map = index_objects(final, "data\\ini\\")
    dups = {k: v for k, v in obj_map.items() if len(v) > 1}
    report.append(f"Data\\INI Object defs: {len(obj_map)}; cross-path dups: {len(dups)}")
    if dups:
        ok = False
        report.append("FAIL: duplicate Objects under Data\\INI:")
        for k, v in sorted(dups.items())[:30]:
            report.append(f"  {k}: {v}")

    # 3) Overlay-internal Object uniqueness
    ovl_objs = index_objects(overlay, None)
    ovl_dups = {k: v for k, v in ovl_objs.items() if len(v) > 1}
    report.append(f"Overlay Object defs: {len(ovl_objs)}; dups: {len(ovl_dups)}")
    if ovl_dups:
        ok = False
        report.append("FAIL: overlay has duplicate Objects")
        for k, v in sorted(ovl_dups.items())[:30]:
            report.append(f"  {k}: {v}")

    # 4) PlayerTemplate → StartingBuilding chain (Egypt + key countries)
    pt_files = [n for n in final if n.lower().endswith("playertemplate_specterpatch.ini")]
    if not pt_files:
        # may live only in overlay
        pt_files = [n for n in overlay if "playertemplate" in n.lower()]
    if not pt_files:
        report.append("FAIL: PlayerTemplate_SpecterPatch.ini missing from load stack")
        ok = False
    else:
        pt = final.get(pt_files[0], overlay.get(pt_files[0], b"")).decode("utf-8", errors="replace")
        for faction, building in [
            ("FactionEgypt", "Egypt_CommandCenter"),  # may start from MHQ
            ("FactionEgypt", "Egypt_MilitaryHQ"),
            ("FactionTurkey", "Turkey_MilitaryHQ"),
            ("FactionIsrael", "Israel_MilitaryHQ"),
        ]:
            m = re.search(rf"PlayerTemplate {faction}\n(.*?)(?:\nEnd\n)", pt, re.S)
            if not m:
                report.append(f"WARN: missing {faction}")
                continue
            block = m.group(1)
            if "SCIENCE_Iraq" in block or "Iraq_VT72B" in block:
                report.append(f"FAIL: {faction} still has Iraq identity leftovers")
                ok = False
            start = re.search(r"StartingBuilding\s*=\s*(\S+)", block)
            if start:
                bname = start.group(1)
                if bname not in obj_map:
                    report.append(f"FAIL: {faction} StartingBuilding {bname} not defined")
                    ok = False
                else:
                    report.append(f"PASS: {faction} StartingBuilding {bname}")

    # 5) CommandSet refs used by Egypt CC exist
    eg_content = final.get(EGYPT_CC_PATH, b"").decode("utf-8", errors="replace")
    cs = re.search(r"^\s*CommandSet\s*=\s*(\S+)", eg_content, re.M)
    if cs:
        cs_name = cs.group(1)
        cs_defs = set()
        for name, content in final.items():
            if not name.lower().endswith(".ini"):
                continue
            if not name.replace("/", "\\").lower().startswith("data\\ini\\"):
                continue
            for m in re.finditer(rb"^CommandSet\s+(\S+)", content, re.M):
                cs_defs.add(m.group(1).decode("latin1"))
        if cs_name not in cs_defs:
            report.append(f"FAIL: Egypt CC CommandSet {cs_name} not defined in Data\\INI")
            ok = False
        else:
            report.append(f"PASS: Egypt CC CommandSet {cs_name} defined")

    # 6) Parse corruption sweep on overlay Object INIs
    corrupt = 0
    for name, content in overlay.items():
        if not name.lower().endswith(".ini"):
            continue
        text = content.decode("utf-8", errors="replace")
        if re.search(r"^P00\s*$", text, re.M) or "\nh00.0\n" in text:
            corrupt += 1
            report.append(f"FAIL: corruption markers in {name}")
            ok = False
    if corrupt == 0:
        report.append("PASS: no P00/h00.0 corruption in overlay INIs")

    report.append("STARTUP_VALIDATION=" + ("PASS" if ok else "FAIL"))
    return ok


def remove_obsolete_release_egypt(patch_root: Path, report: list[str]) -> list[str]:
    """Delete broken Egypt_CommandCenter copies under Release/ (not canonical Data/)."""
    removed = []
    canonical = (
        patch_root
        / "Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
    )
    canon_bytes = canonical.read_bytes()
    canon_ok, _ = egypt_is_repaired(canon_bytes)
    if not canon_ok:
        raise SystemExit("Canonical patch/Data Egypt_CommandCenter is not repaired")

    for path in patch_root.joinpath("Release").rglob("*Egypt*CommandCenter*.ini"):
        # never touch patch/Data
        if "/Data/INI/Object/Specter/" in str(path).replace("\\", "/") and "Release" not in str(path):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if text.lstrip().startswith("; OBSOLETE DUPLICATE REMOVED"):
            report.append(f"ALREADY STUB: {path}")
            continue
        content = path.read_bytes()
        ok, issues = egypt_is_repaired(content)
        if ok:
            # If a Release "good" copy differs from canonical, sync it
            if content != canon_bytes:
                path.write_bytes(canon_bytes)
                report.append(f"SYNCED Release Egypt CC to canonical: {path}")
            else:
                report.append(f"KEEP good Release copy: {path}")
            continue
        # replace with pointer file so nothing broken remains
        note = (
            "; OBSOLETE DUPLICATE REMOVED\n"
            "; This broken Egypt_CommandCenter.ini was deleted from the CLEAN pass.\n"
            "; Canonical repaired file:\n"
            ";   patch/Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini\n"
            "; Do NOT copy this Release path into the game folder.\n"
        )
        path.write_text(note, encoding="utf-8")
        removed.append(str(path))
        report.append(f"REMOVED broken Egypt CC -> stub: {path} ({issues})")
    return removed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--patch-root", type=Path, default=Path("patch"))
    ap.add_argument(
        "--spec-data",
        type=Path,
        default=Path("patch/Release/SPECTER_BIG_MERGE/_SPEC_DATA_ONE.big"),
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("patch/Release/SPECTER_PATCH_FINAL_CLEAN"),
    )
    ap.add_argument("--skip-release-cleanup", action="store_true")
    args = ap.parse_args()

    report: list[str] = []
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stage = args.out_dir / "_stage"

    if not args.skip_release_cleanup:
        removed = remove_obsolete_release_egypt(args.patch_root, report)
        report.append(f"Obsolete Release Egypt CC stubs written: {len(removed)}")

    # Stage + pack map
    file_map = stage_patch(args.patch_root, stage)
    report.append(f"Staged overlay entries: {len(file_map)}")
    report.append(f"Excluded: {sorted(EXCLUDE_REL_POSIX)}")

    # Pre-check Egypt in stage
    if EGYPT_CC_PATH not in file_map:
        report.append("FAIL: staged overlay missing Egypt_CommandCenter.ini")
        (args.out_dir / "VALIDATION_REPORT.txt").write_text("\n".join(report), encoding="utf-8")
        print("\n".join(report))
        return 1
    ok_eg, issues = egypt_is_repaired(file_map[EGYPT_CC_PATH])
    if not ok_eg:
        report.append(f"FAIL: staged Egypt not repaired: {issues}")
        (args.out_dir / "VALIDATION_REPORT.txt").write_text("\n".join(report), encoding="utf-8")
        print("\n".join(report))
        return 1
    report.append("PASS: staged Egypt_CommandCenter is repaired")

    # Count Egypt paths in stage
    eg_stage = [n for n in file_map if n.lower().endswith("egypt_commandcenter.ini")]
    report.append(f"Staged Egypt_CommandCenter paths: {eg_stage}")
    if len(eg_stage) != 1:
        report.append("FAIL: multiple Egypt_CommandCenter.ini in stage")
        (args.out_dir / "VALIDATION_REPORT.txt").write_text("\n".join(report), encoding="utf-8")
        print("\n".join(report))
        return 1

    # Load SPEC and simulate
    if not args.spec_data.exists():
        report.append(f"FAIL: missing SPEC DATA big: {args.spec_data}")
        (args.out_dir / "VALIDATION_REPORT.txt").write_text("\n".join(report), encoding="utf-8")
        print("\n".join(report))
        return 1
    spec = read_big(args.spec_data)
    report.append(f"SPEC DATA entries: {len(spec)}")
    if EGYPT_CC_PATH in spec:
        spec_ok, spec_issues = egypt_is_repaired(spec[EGYPT_CC_PATH])
        report.append(
            f"SPEC Egypt_CommandCenter repaired? {spec_ok} issues={spec_issues} "
            f"sha={hashlib.sha256(spec[EGYPT_CC_PATH]).hexdigest()}"
        )

    # Load-order note
    names = [
        "_SPEC_ART_ONE.big",
        "_SPEC_DATA_ONE.big",
        "_SPECTER_PATCH_FINAL_CLEAN.big",
    ]
    report.append(f"Case-insensitive BIG order: {sorted(names, key=str.lower)}")

    final = simulate_zh_load(spec, file_map)
    report.append(
        f"Final stack entries={len(final)} overlay_overrides={len(set(file_map)&set(spec))} "
        f"overlay_unique={len(set(file_map)-set(spec))}"
    )

    passed = validate_startup(final, file_map, report)

    # Write report always
    (args.out_dir / "VALIDATION_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))

    if not passed:
        print("REFUSING to write _SPECTER_PATCH_FINAL_CLEAN.big — validation FAILED")
        return 1

    # Build candidate BIG bytes and re-validate that exact blob (GameRoot copy simulation).
    # Do not copy the multi-hundred-MB SPEC DATA into out-dir; load SPEC from --spec-data path.
    big_bytes = build_big(file_map)
    candidate = args.out_dir / "_SPECTER_PATCH_FINAL_CLEAN.candidate.big"
    candidate.write_bytes(big_bytes)

    loaded_overlay = read_big(candidate)
    final2 = simulate_zh_load(spec, loaded_overlay)
    report2: list[str] = ["=== REVALIDATE EXACT CANDIDATE BIG (game-folder bytes) ==="]
    passed2 = validate_startup(final2, loaded_overlay, report2)
    print("\n".join(report2))
    (args.out_dir / "VALIDATION_REPORT.txt").write_text(
        "\n".join(report) + "\n\n" + "\n".join(report2) + "\n", encoding="utf-8"
    )
    if not passed2:
        candidate.unlink(missing_ok=True)
        print("REFUSING CLEAN big — candidate revalidation FAILED")
        return 1

    # Promote to release name only after pass
    final_out = args.out_dir / "_SPECTER_PATCH_FINAL_CLEAN.big"
    final_out.write_bytes(big_bytes)
    candidate.unlink(missing_ok=True)
    sha = hashlib.sha256(big_bytes).hexdigest()
    (args.out_dir / "_SPECTER_PATCH_FINAL_CLEAN.big.sha256").write_text(
        f"{sha}  _SPECTER_PATCH_FINAL_CLEAN.big\n", encoding="utf-8"
    )
    (args.out_dir / "README_INSTALL.txt").write_text(
        "SPECTER PATCH FINAL CLEAN overlay\n"
        "=================================\n\n"
        "Copy into Generals Zero Hour / Specter game folder beside:\n"
        "  _SPEC_ART_ONE.big\n"
        "  _SPEC_DATA_ONE.big\n"
        "  EnglishZH.big\n"
        "  AudioZH.big\n\n"
        "File: _SPECTER_PATCH_FINAL_CLEAN.big\n"
        f"SHA256: {sha}\n\n"
        "Loads AFTER _SPEC_DATA_ONE.big (case-insensitive name order) and overrides\n"
        "Data\\INI\\Object\\Specter\\Egyptian Armed Forces\\Buildings\\Egypt_CommandCenter.ini\n"
        "with the latest repaired version (USA ART + US_E3G_AWACS).\n\n"
        "Do NOT copy old Release/*/Egypt_CommandCenter.ini trees into the game folder.\n"
        "Do NOT replace original Specter BIGs.\n",
        encoding="utf-8",
    )
    print(f"WROTE {final_out} entries={len(file_map)} bytes={len(big_bytes)} SHA256={sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
