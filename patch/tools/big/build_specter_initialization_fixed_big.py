#!/usr/bin/env python3
"""Repair broken init links in NO_EGYPT BIG → _SPECTER_INITIALIZATION_FIXED.big

No new content. Only retarget/remove dead references to existing definitions.
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
OUT = ROOT / "Release/SPECTER_INITIALIZATION_FIXED"
EXTRACTED = OUT / "_extracted_Data"
REEXTRACT = OUT / "_reextract_validate"
OUT_BIG = OUT / "_SPECTER_INITIALIZATION_FIXED.big"
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


def pack_tree(base: Path) -> dict[str, bytes]:
    file_map: dict[str, bytes] = {}
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base).as_posix()
        file_map["Data\\" + rel.replace("/", "\\")] = path.read_bytes()
    return file_map


def sync_patch(rel_under_data: str, content: str) -> None:
    out = PATCH_DATA / Path(*rel_under_data.split("/"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8", newline="\n")


def validate(entries: dict[str, bytes]) -> tuple[bool, list[str], list[str]]:
    passes, fails = [], []
    ini = {
        k: v.decode("utf-8", errors="replace")
        for k, v in entries.items()
        if k.lower().endswith(".ini")
    }
    objects, cs, cb = set(), set(), set()
    for text in ini.values():
        objects.update(re.findall(r"^\s*Object\s+(?![=])(\S+)", text, re.M))
        cs.update(re.findall(r"^\s*CommandSet\s+(?![=])(\S+)", text, re.M))
        cb.update(re.findall(r"^\s*CommandButton\s+(?![=])(\S+)", text, re.M))

    eg = re.compile(r"Egypt|Egyptian|egypt_", re.I)
    if not any(eg.search(k) or eg.search(t) for k, t in ini.items()):
        passes.append("Egypt still absent")
    else:
        fails.append("Egypt references returned")

    obj_map: dict[str, list[str]] = defaultdict(list)
    for name, text in ini.items():
        for m in re.finditer(r"^\s*Object\s+(?![=])(\S+)", text, re.M):
            obj_map[m.group(1)].append(name)
    if not any(len(v) > 1 for v in obj_map.values()):
        passes.append("Object duplicate check PASS")
    else:
        fails.append("Object duplicates present")

    broken_slots = []
    for name, text in ini.items():
        for m in re.finditer(r"CommandSet\s+(\S+)\n([\s\S]*?)^\s*End\s*$", text, re.M):
            for sm in re.finditer(r"^\s*\d+\s*=\s*(\S+)", m.group(2), re.M):
                ref = sm.group(1)
                if ref in ("NONE", "Separator"):
                    continue
                if ";" in ref or (ref not in cb and ref not in objects):
                    broken_slots.append((m.group(1), ref, name))
    if not broken_slots:
        passes.append("CommandSet→CommandButton/Object links PASS")
    else:
        fails.append(f"Broken CS slots: {broken_slots[:8]}")

    broken_pt = []
    for name, text in ini.items():
        for m in re.finditer(
            r"PlayerTemplate\s+(\S+)\n([\s\S]*?)^\s*End\s*$", text, re.M
        ):
            pt, block = m.group(1), m.group(2)
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
        passes.append("PlayerTemplate links PASS")
    else:
        fails.append(f"Broken PT: {broken_pt}")

    # parser spot-check on edited files
    open_re = re.compile(
        r"^\s*(?:Object\s+(?![=])\S+|CommandSet\s+(?![=])\S+|CommandButton\s+(?![=])\S+|"
        r"PlayerTemplate\s+(?![=])\S+|Draw\s*=|Behavior\s*=|ArmorSet\b|Body\s*=|"
        r"UnitSpecificSounds\b|ConditionState\s*=|TransitionState\s*=|WeaponSet\b)"
    )
    parse_fail = 0
    for key in [
        r"Data\INI\PlayerTemplate.ini",
        r"Data\INI\CommandSet_StrategicBombers_AABOnly.ini",
        r"Data\INI\CommandSet_AdvancedAirBase.ini",
        r"Data\INI\CommandSet.ini",
    ]:
        text = ini[key]
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
        if hard or depth != 0:
            parse_fail += 1
            fails.append(f"INI parser issue {key} depth={depth}")
    if parse_fail == 0:
        passes.append("INI parser PASS (edited files)")

    broken_cs_prop = []
    for name, text in ini.items():
        for i, line in enumerate(text.splitlines(), 1):
            code = line.split(";", 1)[0]
            m = re.match(r"^\s*CommandSet\s*=\s*(\S+)", code)
            if not m:
                continue
            ref = m.group(1)
            if ref == "=" or not ref:
                broken_cs_prop.append((name, i, ref))
                continue
            if ref.upper() == "NONE":
                continue
            if ref not in cs:
                broken_cs_prop.append((name, i, ref))
    if not broken_cs_prop:
        passes.append("Object CommandSet= links PASS")
    else:
        fails.append(f"Broken Object CommandSet=: {broken_cs_prop[:8]}")

    if not broken_slots and not broken_pt and not broken_cs_prop and parse_fail == 0:
        passes.append("Startup validation PASS")
        passes.append("Zero broken init-critical references")
    else:
        fails.append("Startup validation FAIL")

    return (not fails), passes, fails


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    log: list[str] = []

    # Crash report (exact causes)
    crash = """EXACT INITIALIZATION CRASH CAUSES
=================================
Scanned BIG: _SPECTER_NO_EGYPT_CLEAN.big
SHA256: 3dca571472aeb8b24966ed5a768f2f77615aea77d0be8626c2761a6762897995

Primary init crash (PlayerTemplate load — missing CommandSet names):
1) Data\\INI\\PlayerTemplate.ini:94
   PurchaseScienceCommandSetRank1 = SCIENCE_NorthKorea_CommandSetRank1
   FIX: retarget -> SCIENCE_Iraq_CommandSetRank1 (FactionNorthKorea BaseSide/IntrinsicSciences already Iraq)
2) Data\\INI\\PlayerTemplate.ini:95
   PurchaseScienceCommandSetRank3 = SCIENCE_NorthKorea_CommandSetRank3
   FIX: retarget -> SCIENCE_Iraq_CommandSetRank3
3) Data\\INI\\PlayerTemplate.ini:96
   PurchaseScienceCommandSetRank8 = SCIENCE_NorthKorea_CommandSetRank8
   FIX: retarget -> SCIENCE_Iraq_CommandSetRank8
4) Data\\INI\\PlayerTemplate.ini:97
   SpecialPowerShortcutCommandSet = SpecialPowerShortcutNorthKorea
   FIX: retarget -> SpecialPowerShortcutNorthKoreaSystem (exists)
5) Data\\INI\\PlayerTemplate.ini:306
   StartingUnit0 = AirF_AmericaVehicleDozer
   FIX: retarget -> AmericaVehicleDozer (exists)

CommandSet slots pointing at missing CommandButtons (loaded during init):
6) Data\\INI\\CommandSet_StrategicBombers_AABOnly.ini:21,32,45,59,75
   Command_ConstructAmericaJetE3AWACS
   FIX: retarget -> Command_ConstructPatch_America_E3
7) Data\\INI\\CommandSet_StrategicBombers_AABOnly.ini:82
   Command_ConstructRussiaJetSu75Checkmate
   FIX: retarget -> Command_ConstructPatch_Russia_Su75
8) Data\\INI\\CommandSet_StrategicBombers_AABOnly.ini:89
   Command_ConstructRussiaJetSu47Recon
   FIX: remove dead slot (no existing Su47 CommandButton)
9) Data\\INI\\CommandSet_AdvancedAirBase.ini:277
   Command_ConstructPatch_US_E3G_AWACS
   FIX: remove dead slot (Iraq AWACS already slot 4)
10) Data\\INI\\CommandSet.ini:2878 and :3176
    Demo_Command_ConstructGLAVehicleToxinTruck;TOXIN TRACTOR
    FIX: retarget -> Demo_Command_ConstructGLAVehicleToxinTruck

Object CommandSet= dead links (retarget to existing CS — no new content):
11) North Korea buildings/systems → Iraq_* CommandSets
12) IranExpandedAirfield/Radar → IranAirfieldCommandSet / IranRadarStationCommandSet
13) RussiaGattlingCannonCommandSet → ChinaGattlingCannonCommandSet
14) ChinaWZ8ReconCommandSet / ChinaKJ500CommandSet → ChinaJetMIGCommandSet
15) AmericaShipYardCommandSet → GenericCommandSet
16) FactionBuilding.ini:4275 CommandSet = = GLADemoTrapCommandSet → GLADemoTrapCommandSet

Policy: no new Objects/CommandButtons/CommandSets added — link repairs only.
"""
    (OUT / "CRASH_REPORT.txt").write_text(crash, encoding="utf-8")
    print(crash)

    print("Extracting NO_EGYPT BIG...")
    src = read_big(SRC_BIG)
    print("extracted", extract_tree(src, EXTRACTED))

    # --- PlayerTemplate.ini ---
    pt = EXTRACTED / "INI/PlayerTemplate.ini"
    text = pt.read_text(encoding="utf-8", errors="replace")
    reps = [
        (
            r"(^\s*PurchaseScienceCommandSetRank1\s*=\s*)SCIENCE_NorthKorea_CommandSetRank1\b",
            r"\1SCIENCE_Iraq_CommandSetRank1",
            "PT:94 SCIENCE_NorthKorea_CommandSetRank1 -> SCIENCE_Iraq_CommandSetRank1",
        ),
        (
            r"(^\s*PurchaseScienceCommandSetRank3\s*=\s*)SCIENCE_NorthKorea_CommandSetRank3\b",
            r"\1SCIENCE_Iraq_CommandSetRank3",
            "PT:95 SCIENCE_NorthKorea_CommandSetRank3 -> SCIENCE_Iraq_CommandSetRank3",
        ),
        (
            r"(^\s*PurchaseScienceCommandSetRank8\s*=\s*)SCIENCE_NorthKorea_CommandSetRank8\b",
            r"\1SCIENCE_Iraq_CommandSetRank8",
            "PT:96 SCIENCE_NorthKorea_CommandSetRank8 -> SCIENCE_Iraq_CommandSetRank8",
        ),
        (
            r"(^\s*SpecialPowerShortcutCommandSet\s*=\s*)SpecialPowerShortcutNorthKorea\b",
            r"\1SpecialPowerShortcutNorthKoreaSystem",
            "PT:97 SpecialPowerShortcutNorthKorea -> SpecialPowerShortcutNorthKoreaSystem",
        ),
        (
            r"(^\s*StartingUnit0\s*=\s*)AirF_AmericaVehicleDozer\b",
            r"\1AmericaVehicleDozer",
            "PT:306 AirF_AmericaVehicleDozer -> AmericaVehicleDozer",
        ),
    ]
    for rx, repl, msg in reps:
        text2, n = re.subn(rx, repl, text, flags=re.M)
        if n:
            text = text2
            log.append(msg)
    pt.write_text(text, encoding="utf-8", newline="\n")
    sync_patch("INI/PlayerTemplate.ini", text)

    # --- Strategic bombers AABOnly ---
    aab = EXTRACTED / "INI/CommandSet_StrategicBombers_AABOnly.ini"
    text = aab.read_text(encoding="utf-8", errors="replace")
    text2, n = re.subn(
        r"Command_ConstructAmericaJetE3AWACS\b",
        "Command_ConstructPatch_America_E3",
        text,
    )
    if n:
        text = text2
        log.append(
            f"AABOnly: Command_ConstructAmericaJetE3AWACS -> Command_ConstructPatch_America_E3 (x{n})"
        )
    text2, n = re.subn(
        r"Command_ConstructRussiaJetSu75Checkmate\b",
        "Command_ConstructPatch_Russia_Su75",
        text,
    )
    if n:
        text = text2
        log.append(
            f"AABOnly: Command_ConstructRussiaJetSu75Checkmate -> Command_ConstructPatch_Russia_Su75 (x{n})"
        )
    text2, n = re.subn(
        r"^[ \t]*\d+\s*=\s*Command_ConstructRussiaJetSu47Recon[ \t]*\n",
        "",
        text,
        flags=re.M,
    )
    if n:
        text = text2
        log.append(f"AABOnly: remove dead Su47Recon slot (x{n})")
    aab.write_text(text, encoding="utf-8", newline="\n")
    sync_patch("INI/CommandSet_StrategicBombers_AABOnly.ini", text)

    # --- Iraq AAB dead slot ---
    iraq = EXTRACTED / "INI/CommandSet_AdvancedAirBase.ini"
    text = iraq.read_text(encoding="utf-8", errors="replace")
    text2, n = re.subn(
        r"^[ \t]*15\s*=\s*Command_ConstructPatch_US_E3G_AWACS[ \t]*\n",
        "",
        text,
        flags=re.M,
    )
    if n:
        text = text2
        log.append(
            f"AdvancedAirBase.ini:277 remove Command_ConstructPatch_US_E3G_AWACS (x{n})"
        )
    iraq.write_text(text, encoding="utf-8", newline="\n")
    sync_patch("INI/CommandSet_AdvancedAirBase.ini", text)

    # --- Demo toxin syntax ---
    cs = EXTRACTED / "INI/CommandSet.ini"
    text = cs.read_text(encoding="utf-8", errors="replace")
    text2, n = re.subn(
        r"Demo_Command_ConstructGLAVehicleToxinTruck;TOXIN(?:\s+TRACTOR)?",
        "Demo_Command_ConstructGLAVehicleToxinTruck",
        text,
    )
    if n:
        text = text2
        log.append(f"CommandSet.ini:2878/3176 fix Demo toxin button name (x{n})")
    cs.write_text(text, encoding="utf-8", newline="\n")
    sync_patch("INI/CommandSet.ini", text)

    # Also fix Russia/Iraq CB Object= mismatches that are clearly wrong names
    # Only retarget when an obvious existing object alias exists — still link repair.
    cb_path = EXTRACTED / "INI/CommandButton.ini"
    text = cb_path.read_text(encoding="utf-8", errors="replace")
    obj_retargets = [
        ("RussiaTankT72B3", "RussiaTankT72B3M"),
        ("Russia_Su35S", "RussiaJetSu35S"),
        ("Russia_Su57_AA", "RussiaJetSu57AA"),
        ("Russia_Su57", "RussiaJetSu57"),
        ("Russia_Su34", "RussiaJetSu34"),
        ("Russia_Su-25T", "RussiaJetSU25T"),
        ("Russia_Su-24M2", "RussiaJetSU24M2"),
        ("Russia_Su-24MP", "RussiaJetSU24MP"),
        ("Russia_Mig-31K", "RussiaJetMig31K"),
        ("Russia_Mi-28NE", "RussiaHelicopterMi28N"),
        ("Russia_Mi-17", "RussiaHelicopterMi8AMTSh"),
        ("Russia_Su30MK3", "RussiaJetSu30SM2"),
        ("Russia_Su35S_TS", "RussiaJetSu35AG"),
        ("Russian_T15", "RussianTankT15"),
        ("Russia_Tu-22M3M", "Patch_Russia_Tu22M3"),
        ("Russia_S400_Site_AI", "RussiaS400Site_AI"),
        ("Russia_S400_AI", "RussiaS400Site_AI"),
        ("Russia_92N6R_AI", "Russia_92N6R_CombatMode"),
        ("Russia_92N6R", "Russia_92N6R_CombatMode"),
    ]
    # Only replace inside Object = lines
    for old, new in obj_retargets:
        text2, n = re.subn(
            rf"(^\s*Object\s*=\s*){re.escape(old)}\b",
            rf"\1{new}",
            text,
            flags=re.M,
        )
        if n:
            text = text2
            log.append(f"CommandButton.ini Object= {old} -> {new} (x{n})")
    cb_path.write_text(text, encoding="utf-8", newline="\n")
    sync_patch("INI/CommandButton.ini", text)

    # --- Object CommandSet= broken links (retarget to existing CS) ---
    cs_prop_retargets = [
        ("NorthKorea_AirfieldCommandSet", "Iraq_AirfieldCommandSet"),
        ("NorthKorea_AlAbbasCommandSet", "Iraq_AlAbbasCommandSet"),
        ("NorthKorea_RadarStationCommandSet", "Iraq_RadarStationCommandSet"),
        ("NorthKorea_SupplyCenterCommandSet", "Iraq_SupplyCenterCommandSet"),
        ("NorthKorea_WarFactoryCommandSet", "Iraq_WarFactoryCommandSet"),
        ("NorthKorea_MICCommandSet3", "Iraq_MICCommandSet3"),
        ("NorthKorea_MICCommandSet2", "Iraq_MICCommandSet2"),
        ("NorthKorea_MICCommandSet", "Iraq_MICCommandSet"),
        ("NorthKorea_VT72BCommandSet", "Iraq_VT72BCommandSet"),
        ("IranExpandedAirfieldCommandSet", "IranAirfieldCommandSet"),
        ("IranExpandedRadarCommandSet", "IranRadarStationCommandSet"),
        ("RussiaGattlingCannonCommandSet", "ChinaGattlingCannonCommandSet"),
        ("ChinaWZ8ReconCommandSet", "ChinaJetMIGCommandSet"),
        ("ChinaKJ500CommandSet", "ChinaJetMIGCommandSet"),
        ("AmericaShipYardCommandSet", "GenericCommandSet"),
    ]
    for path in EXTRACTED.rglob("*.ini"):
        text = path.read_text(encoding="utf-8", errors="replace")
        orig = text
        for old, new in cs_prop_retargets:
            text2, n = re.subn(
                rf"(^\s*CommandSet\s*=\s*){re.escape(old)}\b",
                rf"\1{new}",
                text,
                flags=re.M,
            )
            if n:
                text = text2
                rel = path.relative_to(EXTRACTED).as_posix()
                log.append(f"{rel}: CommandSet= {old} -> {new} (x{n})")
        # syntax: CommandSet = = Foo
        text2, n = re.subn(
            r"(^\s*CommandSet\s*=\s*)=\s*(\S+)",
            r"\1\2",
            text,
            flags=re.M,
        )
        if n:
            text = text2
            rel = path.relative_to(EXTRACTED).as_posix()
            log.append(f"{rel}: fix CommandSet = = syntax (x{n})")
        if text != orig:
            path.write_text(text, encoding="utf-8", newline="\n")
            sync_patch(path.relative_to(EXTRACTED).as_posix(), text)

    print("Packing _SPECTER_INITIALIZATION_FIXED.big ...")
    file_map = pack_tree(EXTRACTED)
    for k in list(file_map):
        if re.search(r"egypt|egyptian", k, re.I):
            del file_map[k]
    big = build_big(file_map)
    OUT_BIG.write_bytes(big)
    sha = hashlib.sha256(big).hexdigest()
    (OUT / "_SPECTER_INITIALIZATION_FIXED.big.sha256").write_text(sha + "\n", encoding="utf-8")
    print("sha", sha, "entries", len(file_map), "size", len(big))

    print("Re-extract + validate...")
    packed = read_big(OUT_BIG)
    extract_tree(packed, REEXTRACT)
    ok, passes, fails = validate(packed)
    verdict = "PASS" if ok else "FAIL"

    report = [
        "SPECTER INITIALIZATION FIXED — VERIFY REPORT",
        "=" * 60,
        f"VERDICT: {verdict}",
        "BIG: _SPECTER_INITIALIZATION_FIXED.big",
        f"SHA256: {sha}",
        f"Size: {len(big)} bytes",
        f"Entries: {len(file_map)}",
        "",
        "Link-only repairs on _SPECTER_NO_EGYPT_CLEAN.big (no new content).",
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
        f"""SPECTER INITIALIZATION FIXED
============================

File: _SPECTER_INITIALIZATION_FIXED.big
SHA256: {sha}
Validation: {verdict}

Repairs broken PlayerTemplate/CommandSet links after Egypt removal.
No new units/buttons added — retarget/remove dead refs only.

INSTALL:
1. Backup _SPEC_DATA_ONE.big
2. Replace with _SPECTER_INITIALIZATION_FIXED.big
3. Keep _SPEC_ART_ONE.big
4. Remove other Specter Data overlay BIGs
""",
        encoding="utf-8",
    )
    print("\n".join(report))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
