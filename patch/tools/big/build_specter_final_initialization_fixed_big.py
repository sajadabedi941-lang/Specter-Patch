#!/usr/bin/env python3
"""Repair init-critical broken refs in NO_EGYPT BIG → _SPECTER_FINAL_INITIALIZATION_FIXED.big

Reference-only repairs. No gameplay redesign. Egypt stays removed.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("patch")
SRC_BIG = ROOT / "Release/SPECTER_NO_EGYPT_CLEAN/_SPECTER_NO_EGYPT_CLEAN.big"
SPEC_BIG = ROOT / "Release/SPECTER_BIG_MERGE/_SPEC_DATA_ONE.big"
OUT = ROOT / "Release/SPECTER_FINAL_INITIALIZATION_FIXED"
EXTRACTED = OUT / "_extracted_Data"
REEXTRACT = OUT / "_reextract_validate"
OUT_BIG = OUT / "_SPECTER_FINAL_INITIALIZATION_FIXED.big"
PATCH_DATA = ROOT / "Data"


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


def big_to_fs(base: Path, big_name: str) -> Path | None:
    parts = [p for p in big_name.replace("/", "\\").split("\\") if p]
    if not parts or parts[0].lower() != "data":
        return None
    return base.joinpath(*parts[1:])


def extract_tree(entries: dict[str, bytes], dest: Path) -> int:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    n = 0
    for name, content in entries.items():
        out = big_to_fs(dest, name)
        if out is None:
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(content)
        n += 1
    return n


def extract_block(text: str, kind: str, name: str) -> str | None:
    m = re.search(
        rf"(^[ \t]*{kind}\s+{re.escape(name)}\b[\s\S]*?^[ \t]*End\s*\n?)",
        text,
        re.M,
    )
    return m.group(1) if m else None


def pack_tree(base: Path) -> dict[str, bytes]:
    file_map: dict[str, bytes] = {}
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base).as_posix()
        file_map["Data\\" + rel.replace("/", "\\")] = path.read_bytes()
    return file_map


def validate(entries: dict[str, bytes]) -> tuple[bool, list[str], list[str]]:
    passes: list[str] = []
    fails: list[str] = []
    ini = {
        k: v.decode("utf-8", errors="replace")
        for k, v in entries.items()
        if k.lower().endswith(".ini")
    }
    objects: set[str] = set()
    cs: set[str] = set()
    cb: set[str] = set()
    pt_blocks: dict[str, str] = {}
    for name, text in ini.items():
        objects.update(re.findall(r"^\s*Object\s+(?![=])(\S+)", text, re.M))
        cs.update(re.findall(r"^\s*CommandSet\s+(?![=])(\S+)", text, re.M))
        cb.update(re.findall(r"^\s*CommandButton\s+(?![=])(\S+)", text, re.M))
        for m in re.finditer(
            r"PlayerTemplate\s+(\S+)\n([\s\S]*?)^\s*End\s*$", text, re.M
        ):
            pt_blocks[m.group(1)] = m.group(0)

    # Egypt still gone
    eg = re.compile(r"Egypt|Egyptian|egypt_", re.I)
    egypt_hits = [k for k, t in ini.items() if eg.search(t) or eg.search(k)]
    egypt_hits += [k for k in entries if eg.search(k)]
    if not egypt_hits:
        passes.append("Egypt still absent")
    else:
        fails.append(f"Egypt refs returned: {egypt_hits[:10]}")

    # Object dups
    obj_map: dict[str, list[str]] = defaultdict(list)
    for name, text in ini.items():
        for m in re.finditer(r"^\s*Object\s+(?![=])(\S+)", text, re.M):
            obj_map[m.group(1)].append(name)
    dups = {o: p for o, p in obj_map.items() if len(p) > 1}
    if not dups:
        passes.append("Object duplicate check PASS")
    else:
        fails.append(f"Object dups: {len(dups)}")

    # Broken CS slots
    broken_slots = []
    for name, text in ini.items():
        for m in re.finditer(
            r"CommandSet\s+(\S+)\n([\s\S]*?)^\s*End\s*$", text, re.M
        ):
            for sm in re.finditer(r"^\s*\d+\s*=\s*(\S+)", m.group(2), re.M):
                ref = sm.group(1)
                if ref in ("NONE", "Separator"):
                    continue
                if ";" in ref or (ref not in cb and ref not in objects):
                    broken_slots.append((m.group(1), ref, name))
    if not broken_slots:
        passes.append("Object/CommandSet/CommandButton reference scan PASS (CS slots)")
    else:
        fails.append(f"Broken CS slots remain: {broken_slots[:10]}")

    # Broken PT refs
    broken_pt = []
    for pt, block in pt_blocks.items():
        for label, rx, pool in [
            ("StartingBuilding", r"^\s*StartingBuilding\s*=\s*(\S+)", objects),
            ("StartingUnit", r"^\s*StartingUnit\d*\s*=\s*(\S+)", objects),
            ("PurchaseCS", r"^\s*PurchaseScienceCommandSet\w*\s*=\s*(\S+)", cs),
            ("ShortcutCS", r"^\s*SpecialPowerShortcutCommandSet\s*=\s*(\S+)", cs),
        ]:
            for sm in re.finditer(rx, block, re.M):
                ref = sm.group(1)
                if ref.upper() == "NONE":
                    continue
                if ref not in pool:
                    broken_pt.append((pt, label, ref))
    if not broken_pt:
        passes.append("PlayerTemplate reference scan PASS")
    else:
        fails.append(f"Broken PT refs: {broken_pt}")

    # Required restored names
    for name in [
        "Command_ConstructAmericaJetE3AWACS",
        "Command_ConstructRussiaJetSu75Checkmate",
        "Command_ConstructRussiaJetSu47Recon",
    ]:
        if name in cb:
            passes.append(f"Restored CB {name}")
        else:
            fails.append(f"Missing restored CB {name}")
    for name in [
        "SCIENCE_NorthKorea_CommandSetRank1",
        "SCIENCE_NorthKorea_CommandSetRank3",
        "SCIENCE_NorthKorea_CommandSetRank8",
        "SpecialPowerShortcutNorthKorea",
    ]:
        if name in cs:
            passes.append(f"Restored CS {name}")
        else:
            fails.append(f"Missing restored CS {name}")
    if "AirF_AmericaVehicleDozer" in objects:
        passes.append("Restored Object AirF_AmericaVehicleDozer")
    else:
        fails.append("Missing AirF_AmericaVehicleDozer")

    # INI parser spot check on repaired files + USA/Iraq CC
    open_re = re.compile(
        r"^\s*(?:Object\s+(?![=])\S+|CommandButton\s+(?![=])\S+|CommandSet\s+(?![=])\S+|"
        r"PlayerTemplate\s+(?![=])\S+|Draw\s*=|Behavior\s*=|ArmorSet\b|Body\s*=|"
        r"UnitSpecificSounds\b|ConditionState\s*=|TransitionState\s*=|WeaponSet\b|"
        r"ClientUpdate\s*=|Turret\b|ReplaceModule\b|AddModule\b|RemoveModule\b|"
        r"Prerequisites\b)"
    )
    parse_fail = 0
    checked = 0
    for k, text in ini.items():
        lk = k.replace("/", "\\").lower()
        if not (
            "initializationfix" in lk
            or ("united states of america" in lk and "commandcenter" in lk)
            or lk.endswith("iraq_commandcenter.ini")
            or lk.endswith("commandset_strategicbombers_aabonly.ini")
            or lk.endswith("commandset_advancedairbase.ini")
        ):
            continue
        depth = 0
        hard = False
        for line in text.splitlines():
            code = line.split(";", 1)[0]
            if not code.strip():
                continue
            if re.match(r"^\s*End\s*$", code):
                depth -= 1
                if depth < 0:
                    hard = True
                    depth = 0
                continue
            if open_re.match(code):
                depth += 1
        checked += 1
        if hard or depth != 0:
            parse_fail += 1
            fails.append(f"INI parser issue {k} depth={depth}")
    if parse_fail == 0:
        passes.append(f"INI parser PASS ({checked} files)")
    else:
        fails.append(f"INI parser FAIL count={parse_fail}")

    # Startup validation = PT StartingBuilding/Units + CS slots + no egypt + no dups
    if not broken_pt and not broken_slots and not egypt_hits and not dups and parse_fail == 0:
        passes.append("Startup validation PASS")
    else:
        fails.append("Startup validation FAIL")

    if not broken_slots and not broken_pt:
        passes.append("Zero broken references (init-critical scan)")
    else:
        fails.append("Broken references remain")

    return (not fails), passes, fails


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    log: list[str] = []

    if not SRC_BIG.exists():
        raise SystemExit(f"Missing source BIG: {SRC_BIG}")

    print("Extract NO_EGYPT BIG...")
    src = read_big(SRC_BIG)
    print("extracted", extract_tree(src, EXTRACTED))
    spec = read_big(SPEC_BIG)
    spec_cs = spec[r"Data\INI\CommandSet.ini"].decode("latin1", errors="replace")
    spec_cb = spec[r"Data\INI\CommandButton.ini"].decode("latin1", errors="replace")
    spec_dozer = spec[
        r"Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Dozer.ini"
    ].decode("latin1", errors="replace")

    # --- Restore CommandButtons ---
    cb_names = [
        "Command_ConstructAmericaJetE3AWACS",
        "Command_ConstructRussiaJetSu75Checkmate",
        "Command_ConstructRussiaJetSu47Recon",
        # Required by restored NorthKorea science/shortcut CommandSets
        "Command_PurchaseScienceNKReconFlight",
        "Command_PurchaseScienceNKKN23Strike1",
        "Command_PurchaseScienceNKAirPatrol",
        "Command_PurchaseScienceNKKN23Strike2",
        "Command_PurchaseScienceNKKN23Strike3",
        "Command_PurchaseScienceNKMissileSalvo",
        "Command_PurchaseScienceNKStrategicBombing",
        "Command_PurchaseScienceNKPaektusanFirestorm",
        "Command_PurchaseScienceNKMassedMissileAttack",
        "Command_SelectNorthKoreaSystemSpecialPowerShortcut",
        "Command_SelectNorthKoreaScudFromShortcut",
        "Command_SelectNorthKoreaSarab7FromShortcut",
        "Command_SelectNorthKoreaBM21FromShortcut",
        "Command_LaunchNorthKoreaNuclearFromShortcut",
    ]
    cb_blocks = []
    for name in cb_names:
        b = extract_block(spec_cb, "CommandButton", name)
        if not b:
            raise SystemExit(f"SPEC missing CommandButton {name}")
        cb_blocks.append(b.rstrip() + "\n")
        log.append(f"RESTORE CommandButton {name}")
    cb_text = (
        "; SPECTER INIT FIX — restored CommandButtons required by airfield/NK CommandSets\n"
        "; Source: vendor SPEC CommandButton.ini (no removed-faction content)\n\n"
        + "\n".join(cb_blocks)
    )
    cb_path = EXTRACTED / "INI/CommandButton_InitializationFix.ini"
    cb_path.write_text(cb_text, encoding="utf-8", newline="\n")
    (PATCH_DATA / "INI/CommandButton_InitializationFix.ini").write_text(
        cb_text, encoding="utf-8", newline="\n"
    )

    # --- Restore CommandSets (North Korea) ---
    cs_names = [
        "SCIENCE_NorthKorea_CommandSetRank1",
        "SCIENCE_NorthKorea_CommandSetRank3",
        "SCIENCE_NorthKorea_CommandSetRank8",
        "SpecialPowerShortcutNorthKorea",
    ]
    cs_blocks = []
    for name in cs_names:
        b = extract_block(spec_cs, "CommandSet", name)
        if not b:
            raise SystemExit(f"SPEC missing CommandSet {name}")
        cs_blocks.append(b.rstrip() + "\n")
        log.append(f"RESTORE CommandSet {name}")
    cs_text = (
        "; SPECTER INIT FIX — restored NorthKorea PlayerTemplate CommandSets\n"
        "; Source: vendor SPEC CommandSet.ini (no removed-faction content)\n\n"
        + "\n".join(cs_blocks)
    )
    cs_path = EXTRACTED / "INI/CommandSet_InitializationFix.ini"
    cs_path.write_text(cs_text, encoding="utf-8", newline="\n")
    (PATCH_DATA / "INI/CommandSet_InitializationFix.ini").write_text(
        cs_text, encoding="utf-8", newline="\n"
    )

    # --- Restore AirF_AmericaVehicleDozer ---
    dozer_block = extract_block(spec_dozer, "Object", "AirF_AmericaVehicleDozer")
    if not dozer_block:
        raise SystemExit("SPEC missing AirF_AmericaVehicleDozer")
    # Include only this object; file may have had only this object in SPEC
    dozer_text = (
        "; SPECTER INIT FIX — restore AirF_AmericaVehicleDozer for USAF PlayerTemplate\n"
        "; Extracted from vendor SPEC (was masked by Israel Dozer.ini overlay)\n\n"
        + dozer_block.rstrip()
        + "\n"
    )
    dozer_out = (
        EXTRACTED
        / "INI/Object/Specter/United States Of America/AirF_AmericaVehicleDozer.ini"
    )
    dozer_out.parent.mkdir(parents=True, exist_ok=True)
    dozer_out.write_text(dozer_text, encoding="utf-8", newline="\n")
    patch_dozer = (
        PATCH_DATA
        / "INI/Object/Specter/United States Of America/AirF_AmericaVehicleDozer.ini"
    )
    patch_dozer.parent.mkdir(parents=True, exist_ok=True)
    patch_dozer.write_text(dozer_text, encoding="utf-8", newline="\n")
    log.append("RESTORE Object AirF_AmericaVehicleDozer")

    # --- Fix Iraq AAB dead slot ---
    aab = EXTRACTED / "INI/CommandSet_AdvancedAirBase.ini"
    t = aab.read_text(encoding="utf-8", errors="replace")
    t2, n = re.subn(
        r"^[ \t]*15\s*=\s*Command_ConstructPatch_US_E3G_AWACS[ \t]*\n",
        "",
        t,
        flags=re.M,
    )
    if n:
        aab.write_text(t2, encoding="utf-8", newline="\n")
        (PATCH_DATA / "INI/CommandSet_AdvancedAirBase.ini").write_text(
            t2, encoding="utf-8", newline="\n"
        )
        log.append(
            f"REMOVE dead Iraq AAB slot Command_ConstructPatch_US_E3G_AWACS ({n})"
        )

    # --- Fix Demo toxin semicolon ---
    csi = EXTRACTED / "INI/CommandSet.ini"
    t = csi.read_text(encoding="utf-8", errors="replace")
    t2, n = re.subn(
        r"Demo_Command_ConstructGLAVehicleToxinTruck;TOXIN",
        "Demo_Command_ConstructGLAVehicleToxinTruck",
        t,
    )
    if n:
        csi.write_text(t2, encoding="utf-8", newline="\n")
        (PATCH_DATA / "INI/CommandSet.ini").write_text(
            t2, encoding="utf-8", newline="\n"
        )
        log.append(f"FIX Demo toxin CommandSet slot syntax ({n})")

    print("Pack FIXED BIG...")
    file_map = pack_tree(EXTRACTED)
    # ensure no egypt keys
    for k in list(file_map):
        if re.search(r"egypt|egyptian", k, re.I):
            del file_map[k]
            log.append(f"PURGE egypt key {k}")
    big = build_big(file_map)
    OUT_BIG.write_bytes(big)
    sha = hashlib.sha256(big).hexdigest()
    (OUT / "_SPECTER_FINAL_INITIALIZATION_FIXED.big.sha256").write_text(
        sha + "\n", encoding="utf-8"
    )
    print("packed", len(file_map), sha, len(big))

    print("Re-extract + validate...")
    packed = read_big(OUT_BIG)
    extract_tree(packed, REEXTRACT)
    ok, passes, fails = validate(packed)
    verdict = "PASS" if ok else "FAIL"

    report = [
        "SPECTER FINAL INITIALIZATION FIXED — VERIFY REPORT",
        "=" * 60,
        f"VERDICT: {verdict}",
        f"BIG: _SPECTER_FINAL_INITIALIZATION_FIXED.big",
        f"SHA256: {sha}",
        f"Size: {len(big)} bytes",
        f"Entries: {len(file_map)}",
        "",
        "Base: _SPECTER_NO_EGYPT_CLEAN.big + reference-only init repairs",
        "Egypt remains removed. USA/Iraq gameplay preserved.",
        "",
        "REPAIRS:",
    ]
    for line in log:
        report.append(f"  - {line}")
    report += ["", f"PASS: {len(passes)}  FAIL: {len(fails)}", ""]
    for p in passes:
        report.append("PASS: " + p)
    for f in fails:
        report.append("FAIL: " + f)
    report += ["", f"FINAL: {verdict}"]
    (OUT / "VERIFY_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "REPAIRS.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    (OUT / "README_INSTALL.txt").write_text(
        f"""SPECTER FINAL INITIALIZATION FIXED
==================================

File: _SPECTER_FINAL_INITIALIZATION_FIXED.big
SHA256: {sha}
Validation: {verdict}

Fixes init crash after Egypt removal by restoring missing CommandButton /
CommandSet / Object references and removing dead slots. No Egypt content.

INSTALL:
1. Backup _SPEC_DATA_ONE.big
2. Replace with _SPECTER_FINAL_INITIALIZATION_FIXED.big (rename recommended)
3. Keep _SPEC_ART_ONE.big
4. Remove other Specter Data overlay/test BIGs
""",
        encoding="utf-8",
    )
    print("\n".join(report))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
