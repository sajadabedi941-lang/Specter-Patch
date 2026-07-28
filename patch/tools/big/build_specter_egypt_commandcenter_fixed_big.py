#!/usr/bin/env python3
"""Rebuild Egypt_CommandCenter from USA donor → _SPECTER_EGYPT_COMMANDCENTER_FIXED.big

Base: _SPECTER_FINAL_REPAIRED.big (Egypt present)
+ USA-donor Egypt_CommandCenter.ini
+ init link repairs from INITIALIZATION_FIXED (PlayerTemplate/CommandSet slots)
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path("patch")
SRC_BIG = ROOT / "Release/SPECTER_FINAL_REPAIRED/_SPECTER_FINAL_REPAIRED.big"
OUT = ROOT / "Release/SPECTER_EGYPT_COMMANDCENTER_FIXED"
EXTRACTED = OUT / "_extracted_Data"
REEXTRACT = OUT / "_reextract_validate"
OUT_BIG = OUT / "_SPECTER_EGYPT_COMMANDCENTER_FIXED.big"
OUT_ZIP = OUT / "_SPECTER_EGYPT_COMMANDCENTER_FIXED.zip"
CC_SRC = (
    ROOT
    / "Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
)
CC_KEY = r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_CommandCenter.ini"


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


def apply_init_link_repairs(extracted: Path, log: list[str]) -> None:
    """Same critical init link repairs as INITIALIZATION_FIXED (no new content)."""
    pt = extracted / "INI/PlayerTemplate.ini"
    if pt.exists():
        text = pt.read_text(encoding="utf-8", errors="replace")
        reps = [
            (
                r"(^\s*PurchaseScienceCommandSetRank1\s*=\s*)SCIENCE_NorthKorea_CommandSetRank1\b",
                r"\1SCIENCE_Iraq_CommandSetRank1",
            ),
            (
                r"(^\s*PurchaseScienceCommandSetRank3\s*=\s*)SCIENCE_NorthKorea_CommandSetRank3\b",
                r"\1SCIENCE_Iraq_CommandSetRank3",
            ),
            (
                r"(^\s*PurchaseScienceCommandSetRank8\s*=\s*)SCIENCE_NorthKorea_CommandSetRank8\b",
                r"\1SCIENCE_Iraq_CommandSetRank8",
            ),
            (
                r"(^\s*SpecialPowerShortcutCommandSet\s*=\s*)SpecialPowerShortcutNorthKorea\b",
                r"\1SpecialPowerShortcutNorthKoreaSystem",
            ),
            (
                r"(^\s*StartingUnit0\s*=\s*)AirF_AmericaVehicleDozer\b",
                r"\1AmericaVehicleDozer",
            ),
        ]
        for rx, repl in reps:
            text2, n = re.subn(rx, repl, text, flags=re.M)
            if n:
                text = text2
                log.append(f"PlayerTemplate.ini repair x{n}: {rx[:60]}...")
        pt.write_text(text, encoding="utf-8", newline="\n")

    aab = extracted / "INI/CommandSet_StrategicBombers_AABOnly.ini"
    if aab.exists():
        text = aab.read_text(encoding="utf-8", errors="replace")
        text, n = re.subn(
            r"Command_ConstructAmericaJetE3AWACS\b",
            "Command_ConstructPatch_America_E3",
            text,
        )
        if n:
            log.append(f"AABOnly America E3 retarget x{n}")
        text, n = re.subn(
            r"Command_ConstructRussiaJetSu75Checkmate\b",
            "Command_ConstructPatch_Russia_Su75",
            text,
        )
        if n:
            log.append(f"AABOnly Su75 retarget x{n}")
        text, n = re.subn(
            r"^[ \t]*\d+\s*=\s*Command_ConstructRussiaJetSu47Recon[ \t]*\n",
            "",
            text,
            flags=re.M,
        )
        if n:
            log.append(f"AABOnly remove Su47 slot x{n}")
        aab.write_text(text, encoding="utf-8", newline="\n")

    iraq = extracted / "INI/CommandSet_AdvancedAirBase.ini"
    if iraq.exists():
        text = iraq.read_text(encoding="utf-8", errors="replace")
        text, n = re.subn(
            r"^[ \t]*15\s*=\s*Command_ConstructPatch_US_E3G_AWACS[ \t]*\n",
            "",
            text,
            flags=re.M,
        )
        if n:
            log.append(f"AdvancedAirBase remove dead US_E3G slot x{n}")
        iraq.write_text(text, encoding="utf-8", newline="\n")

    cs = extracted / "INI/CommandSet.ini"
    if cs.exists():
        text = cs.read_text(encoding="utf-8", errors="replace")
        text, n = re.subn(
            r"Demo_Command_ConstructGLAVehicleToxinTruck;TOXIN(?:\s+TRACTOR)?",
            "Demo_Command_ConstructGLAVehicleToxinTruck",
            text,
        )
        if n:
            log.append(f"CommandSet.ini toxin syntax x{n}")
        cs.write_text(text, encoding="utf-8", newline="\n")


def catalogs(ini: dict[str, str]):
    cats: dict[str, set[str]] = defaultdict(set)
    for text in ini.values():
        cats["Object"].update(re.findall(r"^\s*Object\s+(?![=])(\S+)", text, re.M))
        cats["CommandSet"].update(
            re.findall(r"^\s*CommandSet\s+(?![=])(\S+)", text, re.M)
        )
        cats["CommandButton"].update(
            re.findall(r"^\s*CommandButton\s+(?![=])(\S+)", text, re.M)
        )
        cats["SpecialPower"].update(
            re.findall(r"^\s*SpecialPower\s+(?![=])(\S+)", text, re.M)
        )
        cats["Science"].update(re.findall(r"^\s*Science\s+(?![=])(\S+)", text, re.M))
        cats["Upgrade"].update(re.findall(r"^\s*Upgrade\s+(?![=])(\S+)", text, re.M))
        cats["Weapon"].update(re.findall(r"^\s*Weapon\s+(?![=])(\S+)", text, re.M))
        cats["OCL"].update(
            re.findall(r"^\s*ObjectCreationList\s+(?![=])(\S+)", text, re.M)
        )
        cats["Armor"].update(re.findall(r"^\s*Armor\s+(?![=])(\S+)", text, re.M))
        cats["DamageFX"].update(re.findall(r"^\s*DamageFX\s+(?![=])(\S+)", text, re.M))
        cats["FXList"].update(re.findall(r"^\s*FXList\s+(?![=])(\S+)", text, re.M))
    return cats


def validate_egypt_cc(ini: dict[str, str], cats: dict[str, set[str]]) -> list[str]:
    missing: list[str] = []
    if CC_KEY not in ini:
        return ["Egypt_CommandCenter.ini missing from BIG"]
    cc = ini[CC_KEY]

    # contamination — code lines only (ignore comments)
    code_only = "\n".join(line.split(";", 1)[0] for line in cc.splitlines())
    if re.search(
        r"\birq_|\bIraq_Adnan1\b|\bIrq_Command\b|\bSUPERWEAPON_Iraqi|\bSUPERWEAPON_Iraq",
        code_only,
    ):
        missing.append("Iraq/irq contamination still present in Egypt_CommandCenter.ini")

    checks = [
        ("CommandSet", r"^\s*CommandSet\s*=\s*(\S+)", "CommandSet"),
        ("SpecialPower", r"^\s*SpecialPowerTemplate\s*=\s*(\S+)", "SpecialPower"),
        ("OCL", r"^\s*(?:OCL|CreationList|UpgradeObject)\s*=\s*(\S+)", "OCL"),
        ("Object", r"^\s*GunshipTemplateName\s*=\s*(\S+)", "Object"),
        ("Upgrade", r"^\s*(?:UpgradeToGrant|TriggeredBy)\s*=\s*(\S+)", "Upgrade"),
        ("Science", r"^\s*GrantScience\s*=\s*(\S+)", "Science"),
        ("Weapon", r"^\s*DeathWeapon\s*=\s*(\S+)", "Weapon"),
        ("Armor", r"^\s*Armor\s*=\s*(\S+)", "Armor"),
        ("DamageFX", r"^\s*DamageFX\s*=\s*(\S+)", "DamageFX"),
        ("FXList", r"^\s*DeathFX\s*=\s*(\S+)", "FXList"),
    ]
    for label, rx, pool in checks:
        for m in re.finditer(rx, cc, re.M):
            ref = m.group(1)
            if ref.upper() == "NONE":
                continue
            if ref not in cats[pool]:
                missing.append(f"{label}={ref}")

    for sci, ocl in re.findall(r"^\s*UpgradeOCL\s*=\s*(\S+)\s+(\S+)", cc, re.M):
        if sci not in cats["Science"]:
            missing.append(f"Science={sci}")
        if ocl not in cats["OCL"]:
            missing.append(f"OCL={ocl}")

    # CommandSet buttons
    cs_name = "Egypt_CommandCenterCommandSet"
    if cs_name not in cats["CommandSet"]:
        missing.append(f"CommandSet={cs_name}")
    else:
        for name, text in ini.items():
            m = re.search(
                rf"CommandSet\s+{re.escape(cs_name)}\n([\s\S]*?)^\s*End\s*$",
                text,
                re.M,
            )
            if not m:
                continue
            for sm in re.finditer(r"^\s*\d+\s*=\s*(\S+)", m.group(1), re.M):
                btn = sm.group(1)
                if btn in ("NONE", "Separator"):
                    continue
                if btn not in cats["CommandButton"] and btn not in cats["Object"]:
                    missing.append(f"CommandButton={btn}")
            break

    # identity
    if not re.search(r"^\s*Object\s+Egypt_CommandCenter\b", cc, re.M):
        missing.append("Object name is not Egypt_CommandCenter")
    if not re.search(r"^\s*Side\s*=\s*Egypt\b", cc, re.M):
        missing.append("Side is not Egypt")
    if "us_commandcenter" not in cc or "US_Command" not in cc:
        missing.append("USA donor ART missing")

    return missing


def parse_check(text: str) -> tuple[bool, int]:
    open_re = re.compile(
        r"^\s*(?:Object\s+(?![=])\S+|Draw\s*=|Behavior\s*=|ArmorSet\b|Body\s*=|"
        r"UnitSpecificSounds\b|ConditionState\s*=|TransitionState\s*=|WeaponSet\b)"
    )
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
    return (not hard and depth == 0), depth


def validate(entries: dict[str, bytes]) -> tuple[bool, list[str], list[str]]:
    passes, fails = [], []
    ini = {
        k: v.decode("utf-8", errors="replace")
        for k, v in entries.items()
        if k.lower().endswith(".ini")
    }
    cats = catalogs(ini)

    # Object dups
    obj_map: dict[str, list[str]] = defaultdict(list)
    for name, text in ini.items():
        for m in re.finditer(r"^\s*Object\s+(?![=])(\S+)", text, re.M):
            obj_map[m.group(1)].append(name)
    dups = {k: v for k, v in obj_map.items() if len(v) > 1}
    if not dups:
        passes.append("Object duplicates = 0")
    else:
        fails.append(f"Object duplicates = {len(dups)} e.g. {list(dups)[:5]}")

    # Egypt CC present and unique
    if obj_map.get("Egypt_CommandCenter") == [CC_KEY]:
        passes.append("Egypt_CommandCenter single definition")
    else:
        fails.append(f"Egypt_CommandCenter defs={obj_map.get('Egypt_CommandCenter')}")

    # AmericaCommandCenter still present (USA not converted)
    if "AmericaCommandCenter" in cats["Object"]:
        passes.append("AmericaCommandCenter preserved")
    else:
        fails.append("AmericaCommandCenter missing (USA damaged)")

    missing = validate_egypt_cc(ini, cats)
    if not missing:
        passes.append("Missing references = 0 (Egypt_CommandCenter)")
    else:
        fails.append("Missing references: " + "; ".join(missing[:20]))

    ok_parse, depth = parse_check(ini.get(CC_KEY, ""))
    if ok_parse:
        passes.append("INI parser PASS (Egypt_CommandCenter)")
    else:
        fails.append(f"INI parser FAIL depth={depth}")

    # Forbidden tokens in CC (code lines only)
    cc = ini.get(CC_KEY, "")
    code_only = "\n".join(line.split(";", 1)[0] for line in cc.splitlines())
    if not re.search(
        r"\birq_|\bIraq_Adnan1\b|\bIrq_Command\b|\bSUPERWEAPON_Iraqi|\bSUPERWEAPON_IraqRecon",
        code_only,
    ):
        passes.append("No Iraq/irq donor crash refs in Egypt_CommandCenter")
    else:
        fails.append("Iraq/irq donor refs still in Egypt_CommandCenter")

    # Startup-critical PlayerTemplate for Egypt
    pt_ok = True
    for name, text in ini.items():
        if not name.lower().endswith("playertemplate.ini"):
            continue
        for m in re.finditer(
            r"PlayerTemplate\s+(\S+)\n([\s\S]*?)^\s*End\s*$", text, re.M
        ):
            if "Egypt" not in m.group(1) and "Egypt" not in m.group(2):
                continue
            block = m.group(2)
            for sm in re.finditer(r"^\s*StartingBuilding\s*=\s*(\S+)", block, re.M):
                if sm.group(1) not in cats["Object"]:
                    fails.append(f"Egypt PT StartingBuilding missing {sm.group(1)}")
                    pt_ok = False
            for sm in re.finditer(
                r"^\s*PurchaseScienceCommandSet\w*\s*=\s*(\S+)", block, re.M
            ):
                if sm.group(1) not in cats["CommandSet"]:
                    fails.append(f"Egypt PT science CS missing {sm.group(1)}")
                    pt_ok = False
    if pt_ok:
        passes.append("Egypt PlayerTemplate links OK")

    if not fails:
        passes.append("Game initialization PASS (static)")
        passes.append("Zero broken Egypt_CommandCenter references")
    else:
        fails.append("Startup validation FAIL")

    return (not fails), passes, fails


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    log: list[str] = []

    crash = """EXACT BROKEN REFERENCES (vendor SPEC Egypt_CommandCenter)
=======================================================
File: Data\\INI\\Object\\Specter\\Egyptian Armed Forces\\Buildings\\Egypt_CommandCenter.ini

SPEC (broken Iraq-donor clone) crash refs:
1) SelectPortrait/ButtonImage = irq_comndcntr
2) Model = Irq_Command
3) GunshipTemplateName = Iraq_Adnan1
4) OCL = SUPERWEAPON_IraqiSFInsertion
5) OCL = SUPERWEAPON_IraqiParadrop
6) OCL = SUPERWEAPON_IraqiCruiseStrike1/2/3
7) OCL = SUPERWEAPON_IraqReconnaissance
8) MaxHealth = 2000 (wrong), BuildCost = 1615 (wrong)

FIX: Rebuild from USA AmericaCommandCenter donor structure.
- Object Egypt_CommandCenter / Side=Egypt / CommandSet=Egypt_CommandCenterCommandSet
- ART us_commandcenter / US_Command / US_COM_Strb
- BuildCost=2000 BuildTime=45 MaxHealth=5000
- Egypt Superweapons + safe existing OCL/Object targets
- USA AWACS module pattern (SpecialAbility + SpectreGunshipDeploymentUpdate)
"""
    (OUT / "CRASH_REPORT.txt").write_text(crash, encoding="utf-8")
    print(crash)

    if not SRC_BIG.exists():
        print("MISSING", SRC_BIG)
        return 1
    if not CC_SRC.exists():
        print("MISSING", CC_SRC)
        return 1

    print("Extracting FINAL_REPAIRED...")
    src = read_big(SRC_BIG)
    print("extracted", extract_tree(src, EXTRACTED))

    # Install rebuilt Egypt_CommandCenter
    cc_text = CC_SRC.read_text(encoding="utf-8", errors="replace")
    cc_out = (
        EXTRACTED
        / "INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
    )
    cc_out.parent.mkdir(parents=True, exist_ok=True)
    cc_out.write_text(cc_text, encoding="utf-8", newline="\n")
    log.append("Installed USA-donor rebuilt Egypt_CommandCenter.ini")

    apply_init_link_repairs(EXTRACTED, log)

    print("Packing BIG...")
    file_map = pack_tree(EXTRACTED)
    big = build_big(file_map)
    OUT_BIG.write_bytes(big)
    sha = hashlib.sha256(big).hexdigest()
    (OUT / "_SPECTER_EGYPT_COMMANDCENTER_FIXED.big.sha256").write_text(
        sha + "\n", encoding="utf-8"
    )
    print("sha", sha, "entries", len(file_map), "size", len(big))

    print("Re-extract + validate...")
    packed = read_big(OUT_BIG)
    extract_tree(packed, REEXTRACT)
    ok, passes, fails = validate(packed)
    verdict = "PASS" if ok else "FAIL"

    report = [
        "SPECTER EGYPT COMMANDCENTER FIXED — VERIFY REPORT",
        "=" * 60,
        f"VERDICT: {verdict}",
        "BIG: _SPECTER_EGYPT_COMMANDCENTER_FIXED.big",
        f"SHA256: {sha}",
        f"Size: {len(big)} bytes",
        f"Entries: {len(file_map)}",
        "",
        "Rebuilt Egypt_CommandCenter.ini from USA AmericaCommandCenter donor.",
        "Egypt faction retained. USA/Iraq factions not converted.",
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
        f"""SPECTER EGYPT COMMANDCENTER FIXED
=================================

File: _SPECTER_EGYPT_COMMANDCENTER_FIXED.big
SHA256: {sha}
Validation: {verdict}

Egypt_CommandCenter rebuilt from USA AmericaCommandCenter donor.
Iraq-donor crash refs (irq_comndcntr / Iraq_Adnan1 / SUPERWEAPON_Iraqi*) removed.
Egypt faction kept. Object name / Side / CommandSet remain Egypt.

INSTALL:
1. Backup _SPEC_DATA_ONE.big
2. Replace with _SPECTER_EGYPT_COMMANDCENTER_FIXED.big
3. Keep _SPEC_ART_ONE.big
4. Remove other Specter Data overlay BIGs
""",
        encoding="utf-8",
    )

    # ZIP package
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in [
            "_SPECTER_EGYPT_COMMANDCENTER_FIXED.big",
            "_SPECTER_EGYPT_COMMANDCENTER_FIXED.big.sha256",
            "README_INSTALL.txt",
            "VERIFY_REPORT.txt",
            "CRASH_REPORT.txt",
            "REPAIRS.txt",
        ]:
            zf.write(OUT / name, arcname=name)

    print("\n".join(report))
    print("ZIP", OUT_ZIP, OUT_ZIP.stat().st_size)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
