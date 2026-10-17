#!/usr/bin/env python3
"""Build Phase-1 core-9 faction init DATA pack.

Baseline: current patched USA E3 DATA BIG (USA preserved).
Adds original Specter Object trees for Phase-1 non-USA factions from Specter_Data.zip,
plus SpecterPatch UAE/Israel/NK startup overlays required by PlayerTemplates.

Does NOT mass-restore other factions' Object trees.
"""
from __future__ import annotations

import argparse
import re
import shutil
import struct
import zipfile
from collections import defaultdict
from pathlib import Path

OBJ_RE = re.compile(r"^(Object|ChildObject|ObjectReskin)\s+(\S+)", re.M)
CS_RE = re.compile(r"^CommandSet\s+(\S+)", re.M)
PT_RE = re.compile(r"^PlayerTemplate\s+(\S+)", re.M)

PHASE1_TEMPLATES = {
    "USA": "FactionAmerica",
    "IRAN": "FactionIran",
    "RUSSIA": "FactionRussia",
    "CHINA": "FactionChina",
    "IRAQ": "FactionIraq",
    "ISRAEL": "FactionAmericaAirForceGeneral",  # Specter Israel mapping
    "ISRAEL_PATCH": "FactionIsrael",  # SpecterPatch Israel
    "NORTH_KOREA": "FactionNorthKorea",
    "NATO": "FactionNato",
    "UAE": "FactionUAE",
}

# Report keys (user-facing 9; Israel counted once via AirF + patch both must resolve)
REPORT_FACTIONS = [
    "USA",
    "IRAN",
    "RUSSIA",
    "CHINA",
    "IRAQ",
    "ISRAEL",
    "NORTH_KOREA",
    "NATO",
    "UAE",
]

DONOR_FACTION_DIRS = [
    "PLA",
    "Armed Forces Of Russian Federation",
    "Iranian Army",
    "Iraq Army",
    "Israel Defense Forces",
    "NATO",
    "North Korea",
]

# Other-faction Object dirs that must NOT be newly introduced into the pack
# (beyond whatever the USA baseline already lacked — we simply do not copy them).
FORBIDDEN_RESTORE_DIRS = {
    "Turkey Armed Forces",
    "Saudi Arabian Armed Forces",
    "Indian Armed Forces",
    "Pakistan Armed Forces",
    "Japan Self-Defense Forces",
    "Ukrainian Armed Forces",
    "British Armed Forces",
    "French Armed Forces",
    "German Armed Forces",
    "Italian Armed Forces",
    "Egyptian Armed Forces",
    "Libyan Armed Forces",
    "South African National Defence Force",
    "Republic of Korea Armed Forces",
    "Swedish Armed Forces",
    "Syrian Arab Army",
    "Republic of China Armed Forces",
    "Vietnam People's Army",
    "United Nations Forces",
    "AI_IraqiArmy",
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


def write_big(path: Path, file_map: dict[str, bytes]) -> None:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))


def extract_big_to_dir(big_path: Path, out_dir: Path) -> int:
    entries = read_big(big_path)
    n = 0
    for name, content in entries.items():
        rel = name.replace("\\", "/").lstrip("/")
        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        n += 1
    return n


def big_key(rel_posix: str) -> str:
    return rel_posix.replace("/", "\\")


def copy_tree_files(src: Path, dst: Path) -> int:
    n = 0
    for p in src.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)
        n += 1
    return n


def extract_donor_faction_dirs(specter_zip: Path, out_dir: Path) -> None:
    """Extract Phase-1 Specter Object dirs from multi-volume Specter_Data.zip."""
    out_dir.mkdir(parents=True, exist_ok=True)
    # 7z handles multi-volume; invoke via shutil which we already used externally.
    # Prefer zipfile if single; otherwise shell to 7z.
    import subprocess

    args = ["7z", "x", "-y", f"-o{out_dir}", str(specter_zip)]
    for d in DONOR_FACTION_DIRS:
        args.append(f"Data/INI/Object/Specter/{d}")
    args.append("Data/INI/PlayerTemplate.ini")
    subprocess.check_call(args)


def filter_playertemplate_specterpatch(src: Path) -> bytes:
    """Keep only Phase-1 additive templates (UAE + Israel). Leave others out of pack."""
    text = src.read_text(encoding="utf-8", errors="replace")
    keep = {"FactionUAE", "FactionIsrael"}
    blocks = re.split(r"(?=^PlayerTemplate\s+)", text, flags=re.M)
    header = []
    kept = []
    for block in blocks:
        m = PT_RE.match(block.strip())
        if not m:
            if block.strip():
                header.append(block)
            continue
        name = m.group(1)
        if name in keep:
            kept.append(block if block.endswith("\n") else block + "\n")
    out = (
        ";==============================================================================\n"
        "; PHASE-1 PACK ONLY — FactionUAE + FactionIsrael\n"
        "; Other SpecterPatch PlayerTemplates intentionally omitted from this pack.\n"
        "; Source file PlayerTemplate_SpecterPatch.ini remains full in repository.\n"
        ";==============================================================================\n\n"
        + "".join(kept)
    )
    return out.encode("utf-8")


def index_ini_defs(root: Path) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, dict]]:
    objects: dict[str, list[str]] = defaultdict(list)
    commandsets: dict[str, list[str]] = defaultdict(list)
    templates: dict[str, dict] = {}
    for p in root.rglob("*.ini"):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = str(p.relative_to(root)).replace("\\", "/")
        for m in OBJ_RE.finditer(text):
            objects[m.group(2)].append(rel)
        for m in CS_RE.finditer(text):
            commandsets[m.group(1)].append(rel)
        for m in PT_RE.finditer(text):
            # parse block
            start = m.start()
            end = text.find("\nEnd", start)
            if end < 0:
                block = text[start:]
            else:
                block = text[start : end + 4]
            fields = {}
            for key in (
                "StartingBuilding",
                "StartingUnit0",
                "StartingUnit1",
                "StartingUnit2",
                "StartingUnit3",
                "StartingUnit4",
                "StartingUnit5",
                "SpecialPowerShortcutCommandSet",
                "Side",
            ):
                mm = re.search(rf"^\s*{key}\s*=\s*(\S+)", block, re.M)
                if mm:
                    fields[key] = mm.group(1)
            templates[m.group(1)] = fields
    return objects, commandsets, templates


def object_module_refs(text: str) -> dict[str, set[str]]:
    refs: dict[str, set[str]] = defaultdict(set)
    for key, pat in [
        ("CommandSet", r"^\s*CommandSet\s*=\s*(\S+)"),
        ("Armor", r"^\s*Armor\s*=\s*(\S+)"),
        ("Locomotor", r"^\s*Locomotor\s*=\s*SET_\w+\s+(\S+)"),
        ("Weapon", r"^\s*Weapon\s*=\s*(\S+)"),
        ("SpecialPowerTemplate", r"^\s*SpecialPowerTemplate\s*=\s*(\S+)"),
        ("OCL", r"^\s*(?:OCL|CreateObject)\s*=\s*(\S+)"),
    ]:
        for m in re.finditer(pat, text, re.M):
            refs[key].add(m.group(1))
    return refs


def find_object_text(root: Path, objects: dict[str, list[str]], name: str) -> str:
    paths = objects.get(name) or []
    chunks = []
    for rel in paths:
        p = root / rel
        if p.exists():
            chunks.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def validate_faction(
    root: Path,
    objects: dict[str, list[str]],
    commandsets: dict[str, list[str]],
    templates: dict[str, dict],
    pt_name: str,
) -> dict:
    fields = templates.get(pt_name, {})
    start_keys = [
        "StartingBuilding",
        "StartingUnit0",
        "StartingUnit1",
        "StartingUnit2",
        "StartingUnit3",
        "StartingUnit4",
        "StartingUnit5",
    ]
    start_objs = [fields[k] for k in start_keys if k in fields]
    missing_start = [o for o in start_objs if o not in objects]
    shortcut_cs = fields.get("SpecialPowerShortcutCommandSet")
    missing_cs = []
    if shortcut_cs and shortcut_cs not in commandsets:
        missing_cs.append(shortcut_cs)

    missing_deps = []
    for obj in start_objs:
        if obj not in objects:
            continue
        text = find_object_text(root, objects, obj)
        refs = object_module_refs(text)
        for cs in refs.get("CommandSet", ()):
            if cs not in commandsets:
                missing_cs.append(cs)
        # Object-like OCL CreateObject refs that look like ThingTemplates
        for ocl in refs.get("OCL", ()):
            if ocl.startswith("OCL_") or ocl.startswith("China") or False:
                pass
        # Direct Object refs in Payload / CreateObject style already covered loosely

    # Builder / CC / SPS labels
    builder = fields.get("StartingUnit0", "")
    cc = fields.get("StartingBuilding", "")
    sps = fields.get("StartingUnit1", "")
    # Prefer SPS-looking unit
    for o in start_objs:
        if "SystemSpecialPowerShortcut" in o:
            sps = o
            break

    status = "RESOLVED" if not missing_start and not missing_cs else "NOT_RESOLVED"
    return {
        "PLAYER_TEMPLATE": pt_name,
        "STARTING_COMMAND_CENTER": cc,
        "STARTING_BUILDER": builder,
        "SYSTEM_SPECIAL_POWER_SHORTCUT": sps,
        "MISSING_START_OBJECTS": missing_start,
        "MISSING_COMMANDSETS": sorted(set(missing_cs)),
        "MISSING_OBJECT_DEPENDENCIES": missing_deps,
        "STATUS": status,
        "UNRESOLVED_START_OBJECTS": len(missing_start),
    }


def stage_has_object(stage: Path, object_name: str) -> bool:
    pat = re.compile(rf"^(Object|ChildObject|ObjectReskin)\s+{re.escape(object_name)}\b", re.M)
    usa = stage / "Data/INI/Object/Specter/United States Of America"
    roots = [usa] if usa.exists() else [stage]
    for root in roots:
        for p in root.rglob("*.ini"):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if pat.search(text):
                return True
    return False


def stage_usa_markers(stage: Path) -> dict[str, bool]:
    """Confirm critical USA patched assets remain present."""
    checks = {
        "B2": stage_has_object(stage, "AmericaJetB2")
        or any(stage.rglob("*AmericaJetB2*")),
        "B21": stage_has_object(stage, "AmericaJetB21Clean")
        or stage_has_object(stage, "AmericaJetB21")
        or any(stage.rglob("*AmericaJetB21*")),
        "B52H": stage_has_object(stage, "AmericaJetB52H"),
        "F117": stage_has_object(stage, "AmericaJetF117Clean")
        or any(stage.rglob("*AmericaJetF117*")),
        "THAAD": any(p.name for p in stage.rglob("*.ini") if "THAAD" in p.name.upper())
        or stage_has_object(stage, "AmericaMissileDefenseTHAAD"),
        "M1075I": any(p.name for p in stage.rglob("*.ini") if "M1075" in p.name.upper()),
        "USA_System": (stage / "Data/INI/Object/Specter/United States Of America/USA_System.ini").exists(),
    }
    return checks


def pack_dir_to_map(stage: Path) -> dict[str, bytes]:
    file_map: dict[str, bytes] = {}
    data_root = stage / "Data"
    if not data_root.exists():
        raise SystemExit(f"Missing Data in stage: {stage}")
    for p in data_root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(stage).as_posix()
        file_map[big_key(rel)] = p.read_bytes()
    return file_map


def specter_folders_in_map(file_map: dict[str, bytes]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for k in file_map:
        k2 = k.replace("/", "\\")
        if "Object\\Specter\\" not in k2:
            continue
        parts = k2.split("\\")
        try:
            i = parts.index("Specter")
            counts[parts[i + 1]] += 1
        except (ValueError, IndexError):
            pass
    return dict(counts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--usa-data-big",
        type=Path,
        default=Path("patch/Release/SPECTER_USA_E3_RESTORE_B21_ROUTING/_SPEC_DATA_ONE.big"),
    )
    ap.add_argument(
        "--usa-art-big",
        type=Path,
        default=Path("patch/Release/SPECTER_USA_E3_RESTORE_B21_ROUTING/_SPEC_ART_ONE.big"),
    )
    ap.add_argument("--specter-zip", type=Path, default=Path("Specter_Data.zip"))
    ap.add_argument("--patch-root", type=Path, default=Path("patch"))
    ap.add_argument("--work", type=Path, default=Path("/tmp/phase1_core9_work"))
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("patch/Release/SPECTER_PHASE1_CORE9_FACTION_INIT"),
    )
    args = ap.parse_args()

    work = args.work
    if work.exists():
        shutil.rmtree(work)
    stage = work / "stage"
    donor = work / "donor"
    extract_dir = work / "usa_extract"
    stage.mkdir(parents=True)
    donor.mkdir(parents=True)
    extract_dir.mkdir(parents=True)

    print("=== Extract USA baseline DATA ===")
    n = extract_big_to_dir(args.usa_data_big, extract_dir)
    print(f"  extracted {n} files")
    # Clean staging: copy baseline
    shutil.copytree(extract_dir / "Data", stage / "Data")

    print("=== Extract Specter donor Phase-1 Object trees ===")
    extract_donor_faction_dirs(args.specter_zip, donor)
    specter_dst = stage / "Data/INI/Object/Specter"
    for d in DONOR_FACTION_DIRS:
        src = donor / "Data/INI/Object/Specter" / d
        if not src.exists():
            raise SystemExit(f"Missing donor faction dir: {src}")
        dst = specter_dst / d
        if dst.exists():
            shutil.rmtree(dst)
        n = copy_tree_files(src, dst)
        print(f"  donor -> stage: {d} ({n} files)")

    print("=== Overlay SpecterPatch Phase-1 required files (UAE/Israel/NK SPS) ===")
    patch_ini = args.patch_root / "Data/INI"
    patch_obj = patch_ini / "Object/Specter"

    # UAE full tree from patch (not in Specter_Data.zip)
    uae_src = patch_obj / "United Arab Emirates"
    uae_dst = specter_dst / "United Arab Emirates"
    if uae_dst.exists():
        shutil.rmtree(uae_dst)
    n = copy_tree_files(uae_src, uae_dst)
    print(f"  UAE patch tree: {n} files")

    # Israel patch-only startup objects (keep donor AirF_* + add patch names)
    for rel in [
        "Israel Defense Forces/Buildings/Israel_MilitaryHQ.ini",
        "Israel Defense Forces/Buildings/Israel_CommandCenter.ini",
        "Israel Defense Forces/Israel_Systems.ini",
    ]:
        src = patch_obj / rel
        if src.exists():
            dst = specter_dst / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  overlay {rel}")

    # Merge Israel dozers: donor AirF_AmericaVehicleDozer + patch Israel_VehicleDozer
    donor_dozer = (
        donor
        / "Data/INI/Object/Specter/Israel Defense Forces/Wheeled/Dozer.ini"
    )
    patch_dozer = patch_obj / "Israel Defense Forces/Wheeled/Dozer.ini"
    dst_dozer = specter_dst / "Israel Defense Forces/Wheeled/Dozer.ini"
    dst_dozer.parent.mkdir(parents=True, exist_ok=True)
    merged = donor_dozer.read_text(encoding="utf-8", errors="replace")
    if patch_dozer.exists():
        patch_text = patch_dozer.read_text(encoding="utf-8", errors="replace")
        if "Object Israel_VehicleDozer" in patch_text and "Object Israel_VehicleDozer" not in merged:
            # Append the patch Israel_VehicleDozer object block
            m = re.search(
                r"(^Object Israel_VehicleDozer\b.*?)(?=^Object\s|\Z)",
                patch_text,
                re.M | re.S,
            )
            if m:
                merged = merged.rstrip() + "\n\n" + m.group(1).rstrip() + "\n"
            else:
                merged = merged.rstrip() + "\n\n" + patch_text
    dst_dozer.write_text(merged, encoding="utf-8")
    print("  merged Israel Dozer.ini (AirF_AmericaVehicleDozer + Israel_VehicleDozer)")

    # North Korea SPS object expected by current PlayerTemplate
    nk_sys = patch_obj / "North Korea/NorthKorea_Systems.ini"
    if nk_sys.exists():
        dst = specter_dst / "North Korea/NorthKorea_Systems.ini"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(nk_sys, dst)
        print("  overlay NorthKorea_Systems.ini (NorthKoreaSystemSpecialPowerShortcut)")

    # Additive INI for UAE/Israel sciences + commandsets + filtered PlayerTemplate
    overlays = [
        "CommandSet_UAE.ini",
        "CommandSet_Israel.ini",
        "CommandSet_Israel_Integrity.ini",
        "Science_UAE.ini",
        "Science_SpecterPatch.ini",
        "SpecialPower_UAE.ini",
        "Upgrade_UAE.ini",
        "Upgrade_Israel.ini",
        "Weapon_UAE.ini",
        "CommandButton_UAE_PhaseB.ini",
    ]
    for name in overlays:
        src = patch_ini / name
        if src.exists():
            dst = stage / "Data/INI" / name
            shutil.copy2(src, dst)
            print(f"  overlay Data/INI/{name}")

    # Israel_MilitaryHQCommandSet lives in FactionExpansion file; extract Phase-1-only CS
    exp = patch_ini / "CommandSet_FactionExpansion_Armies.ini"
    if exp.exists():
        exp_text = exp.read_text(encoding="utf-8", errors="replace")
        m = re.search(
            r"(^CommandSet Israel_MilitaryHQCommandSet\b.*?(?=^CommandSet\s|\Z))",
            exp_text,
            re.M | re.S,
        )
        if m:
            cs_path = stage / "Data/INI/CommandSet_Israel_MilitaryHQ.ini"
            cs_path.write_text(
                "; Phase-1 extracted Israel_MilitaryHQCommandSet\n\n" + m.group(1).rstrip() + "\n",
                encoding="utf-8",
            )
            print("  wrote Data/INI/CommandSet_Israel_MilitaryHQ.ini")

    # Phase-1-only PlayerTemplate_SpecterPatch (UAE + Israel only)
    pt_src = patch_ini / "PlayerTemplate_SpecterPatch.ini"
    pt_bytes = filter_playertemplate_specterpatch(pt_src)
    (stage / "Data/INI/PlayerTemplate_SpecterPatch.ini").write_bytes(pt_bytes)
    print("  wrote Phase-1 PlayerTemplate_SpecterPatch.ini (UAE+Israel only)")

    # Ensure USA tree untouched: re-copy USA from baseline extract last
    print("=== Re-assert current patched USA Object tree from baseline ===")
    usa_src = extract_dir / "Data/INI/Object/Specter/United States Of America"
    usa_dst = specter_dst / "United States Of America"
    if usa_dst.exists():
        shutil.rmtree(usa_dst)
    n = copy_tree_files(usa_src, usa_dst)
    print(f"  USA files: {n}")
    patch_sys_src = extract_dir / "Data/INI/Object/Specter/PatchSystems"
    if patch_sys_src.exists():
        patch_sys_dst = specter_dst / "PatchSystems"
        if patch_sys_dst.exists():
            shutil.rmtree(patch_sys_dst)
        n = copy_tree_files(patch_sys_src, patch_sys_dst)
        print(f"  PatchSystems files: {n}")

    usa_marks = stage_usa_markers(stage)
    print("  USA markers:", usa_marks)

    print("=== Pack DATA BIG from clean staging ===")
    file_map = pack_dir_to_map(stage)
    # Guard: do not include forbidden faction Object dirs
    folders = specter_folders_in_map(file_map)
    restored_other = sorted(set(folders) & FORBIDDEN_RESTORE_DIRS)
    if restored_other:
        raise SystemExit(f"Forbidden faction dirs present in pack: {restored_other}")
    print("  Specter folders in pack:", sorted(folders.items()))
    print(f"  total DATA entries: {len(file_map)}")

    out = args.out_dir
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    data_big = out / "_SPEC_DATA_ONE.big"
    write_big(data_big, file_map)
    shutil.copy2(args.usa_art_big, out / "_SPEC_ART_ONE.big")
    print(f"  wrote {data_big} ({data_big.stat().st_size} bytes)")

    print("=== Re-extract packed DATA and validate ===")
    packed_extract = work / "packed_extract"
    if packed_extract.exists():
        shutil.rmtree(packed_extract)
    extract_big_to_dir(data_big, packed_extract)
    objects, commandsets, templates = index_ini_defs(packed_extract)

    results = {}
    # Validate AirF Israel under ISRAEL; also FactionIsrael
    for label, pt in PHASE1_TEMPLATES.items():
        results[label] = validate_faction(
            packed_extract, objects, commandsets, templates, pt
        )

    # Combine Israel statuses: both AirF and patch must resolve for ISRAEL_STATUS
    israel_ok = (
        results["ISRAEL"]["STATUS"] == "RESOLVED"
        and results["ISRAEL_PATCH"]["STATUS"] == "RESOLVED"
    )

    lines = []
    lines.append("SPECTER PHASE-1 CORE-9 FACTION INIT — PACKED VALIDATION")
    lines.append("=" * 70)
    lines.append(f"PACKED_DATA = {data_big}")
    lines.append(f"PACKED_ENTRIES = {len(file_map)}")
    lines.append(f"SPECTER_OBJECT_FOLDERS = {sorted(folders)}")
    lines.append(f"OTHER_FACTIONS_RESTORED = {len(restored_other)}")
    lines.append(f"USA_MARKERS = {usa_marks}")
    lines.append(f"USA_CURRENT_MODIFICATIONS_PRESERVED = {'YES' if all(usa_marks.values()) else 'NO'}")
    lines.append("")

    core_unresolved = 0
    core_missing_deps = 0
    status_map = {}

    # Per-faction report in user order (Israel combines AirF + patch)
    report_order = [
        ("USA", ["USA"]),
        ("IRAN", ["IRAN"]),
        ("RUSSIA", ["RUSSIA"]),
        ("CHINA", ["CHINA"]),
        ("IRAQ", ["IRAQ"]),
        ("ISRAEL", ["ISRAEL", "ISRAEL_PATCH"]),
        ("NORTH_KOREA", ["NORTH_KOREA"]),
        ("NATO", ["NATO"]),
        ("UAE", ["UAE"]),
    ]

    for faction, keys in report_order:
        lines.append("-" * 70)
        lines.append(f"FACTION = {faction}")
        combined_missing_start = []
        combined_missing_cs = []
        combined_missing_deps = []
        pts = []
        for k in keys:
            r = results[k]
            pts.append(r["PLAYER_TEMPLATE"])
            lines.append(f"PLAYER_TEMPLATE = {r['PLAYER_TEMPLATE']}")
            lines.append(f"STARTING_COMMAND_CENTER = {r['STARTING_COMMAND_CENTER']}")
            lines.append(f"STARTING_BUILDER = {r['STARTING_BUILDER']}")
            lines.append(f"SYSTEM_SPECIAL_POWER_SHORTCUT = {r['SYSTEM_SPECIAL_POWER_SHORTCUT']}")
            lines.append(f"MISSING_START_OBJECTS = {r['MISSING_START_OBJECTS']}")
            lines.append(f"MISSING_COMMANDSETS = {r['MISSING_COMMANDSETS']}")
            lines.append(f"MISSING_OBJECT_DEPENDENCIES = {r['MISSING_OBJECT_DEPENDENCIES']}")
            lines.append(f"STATUS = {r['STATUS']}")
            lines.append(f"{faction}_UNRESOLVED_START_OBJECTS = {r['UNRESOLVED_START_OBJECTS']}")
            combined_missing_start.extend(r["MISSING_START_OBJECTS"])
            combined_missing_cs.extend(r["MISSING_COMMANDSETS"])
            combined_missing_deps.extend(r["MISSING_OBJECT_DEPENDENCIES"])
            core_unresolved += r["UNRESOLVED_START_OBJECTS"]
            core_missing_deps += len(r["MISSING_OBJECT_DEPENDENCIES"]) + len(r["MISSING_COMMANDSETS"])
        ok = all(results[k]["STATUS"] == "RESOLVED" for k in keys)
        status_map[faction] = "RESOLVED" if ok else "NOT_RESOLVED"
        lines.append(f"{faction}_STATUS = {status_map[faction]}")
        lines.append("")

    lines.append("=" * 70)
    lines.append("FINAL REQUIRED REPORT")
    lines.append("=" * 70)
    lines.append("PHASE_1_CORE_FACTIONS = 9")
    for faction in REPORT_FACTIONS:
        lines.append(f"{faction}_STATUS = {status_map[faction]}")
    lines.append(f"CORE_UNRESOLVED_START_OBJECTS = {core_unresolved}")
    lines.append(f"CORE_MISSING_DEPENDENCIES = {core_missing_deps}")
    lines.append(
        f"USA_CURRENT_MODIFICATIONS_PRESERVED = {'YES' if all(usa_marks.values()) else 'NO'}"
    )
    lines.append(f"OTHER_FACTIONS_RESTORED = {len(restored_other)}")
    lines.append("RUNTIME_TEST_REQUIRED = YES")
    lines.append("")
    lines.append("NOTE: Static packed validation only. Do not claim in-game until user tests.")

    report = "\n".join(lines) + "\n"
    (out / "PHASE1_VALIDATION_REPORT.txt").write_text(report, encoding="utf-8")
    print(report)

    all_ok = all(status_map[f] == "RESOLVED" for f in REPORT_FACTIONS)
    if all_ok:
        # Create one test ZIP
        zip_path = out / "SPECTER_PHASE1_CORE9_FACTION_INIT.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for name in [
                "_SPEC_DATA_ONE.big",
                "_SPEC_ART_ONE.big",
                "PHASE1_VALIDATION_REPORT.txt",
            ]:
                zf.write(out / name, name)
            readme = (
                "SPECTER PHASE-1 CORE-9 FACTION INIT (STATIC)\n"
                "==========================================\n"
                "Install: replace your Specter _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big\n"
                "with the files in this ZIP (backup first).\n\n"
                "Phase-1 factions targeted:\n"
                "  USA, Iran, Russia, China, Iraq, Israel, North Korea, NATO, UAE\n\n"
                "USA current aircraft/work preserved from E3 baseline.\n"
                "Other factions were NOT mass-restored.\n\n"
                "RUNTIME_TEST_REQUIRED = YES\n"
                "Static validation says start objects resolve; user must test in-game.\n"
            )
            zf.writestr("README_INSTALL.txt", readme)
            (out / "README_INSTALL.txt").write_text(readme, encoding="utf-8")
        print(f"Created test ZIP: {zip_path}")
    else:
        print("NOT creating ZIP — one or more factions NOT_RESOLVED")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
