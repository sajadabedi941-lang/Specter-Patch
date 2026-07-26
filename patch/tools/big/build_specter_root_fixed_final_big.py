#!/usr/bin/env python3
"""ROOT CAUSE FIX: rebuild standalone Data BIG from extracted clean files.

Does NOT patch-over an existing BIG archive in-place.
Does NOT ship or rename _SPEC_DATA_ONE.big.

Pipeline:
  1) Scan all BIGs + loose trees for Egypt_CommandCenter.ini copies
  2) Extract vendor SPEC DATA to a clean filesystem tree
  3) Overlay current accepted patch/Data
  4) Delete every Egypt_CommandCenter.ini from the tree
  5) Write ONE USA-donor Egypt_CommandCenter.ini
  6) Pack NEW _SPECTER_ROOT_FIXED_FINAL.big from the tree
  7) Re-extract that BIG and validate (only then PASS)
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
SPEC_DATA = ROOT / "Release/SPECTER_BIG_MERGE/_SPEC_DATA_ONE.big"
SPEC_ART = ROOT / "Release/SPECTER_BIG_MERGE/_SPEC_ART_ONE.big"
PATCH_DATA = ROOT / "Data"
USA_LOOSE = ROOT / (
    "Release/SPECTER_ULTIMATE_LOOSE_FILES_PATCH/Data/INI/Object/Specter/"
    "United States Of America/Buildings/CommandCenter.ini"
)
EGYPT_LIVE = ROOT / (
    "Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
)
OUT_DIR = ROOT / "Release/SPECTER_ROOT_FIXED_FINAL"
EXTRACTED = OUT_DIR / "_extracted_Data"
REEXTRACT = OUT_DIR / "_reextract_validate"
OUT_BIG = OUT_DIR / "_SPECTER_ROOT_FIXED_FINAL.big"
EGYPT_BIG_PATH = (
    r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_CommandCenter.ini"
)

FORBID_RE = re.compile(
    r"irq_|Irq_|Iraq|Iraqi|SUPERWEAPON_Iraq|Iraq_PlayerTemplate"
)
BROKEN_SPEC_SHA = "1b559b9e0d4eb1400e76934196eb71205c1ff21317e610d717c1da1dc7870b61"


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


def is_egypt_cc_name(name: str) -> bool:
    low = name.replace("/", "\\").lower()
    return low.endswith("egypt_commandcenter.ini")


def scan_all_egypt_copies() -> list[dict]:
    hits: list[dict] = []
    for big in sorted(ROOT.rglob("*.big")):
        try:
            entries = read_big(big)
        except Exception as e:
            hits.append(
                {
                    "source": str(big),
                    "path": f"<unreadable: {e}>",
                    "sha256": "",
                    "size": 0,
                    "broken": False,
                }
            )
            continue
        for name, content in entries.items():
            if not is_egypt_cc_name(name):
                continue
            sha = hashlib.sha256(content).hexdigest()
            text = content.decode("latin1", errors="replace")
            broken = (
                sha == BROKEN_SPEC_SHA
                or "irq_comndcntr" in text
                or "Iraq_Adnan1" in text
                or "SUPERWEAPON_Iraq" in text
                or ("Irq_Command" in text and "us_commandcenter" not in text)
            )
            hits.append(
                {
                    "source": str(big),
                    "path": name,
                    "sha256": sha,
                    "size": len(content),
                    "broken": broken,
                }
            )
    for loose in sorted(Path(".").rglob("*Egypt_CommandCenter.ini")):
        # skip workdirs we create
        s = str(loose)
        if "SPECTER_ROOT_FIXED_FINAL" in s:
            continue
        try:
            content = loose.read_bytes()
        except Exception:
            continue
        sha = hashlib.sha256(content).hexdigest()
        text = content.decode("latin1", errors="replace")
        broken = (
            sha == BROKEN_SPEC_SHA
            or "irq_comndcntr" in text
            or "Iraq_Adnan1" in text
            or "SUPERWEAPON_Iraq" in text
        )
        hits.append(
            {
                "source": "LOOSE",
                "path": s,
                "sha256": sha,
                "size": len(content),
                "broken": broken,
            }
        )
    return hits


def extract_egypt_specials(text: str) -> str:
    """Pull Egypt-named special power modules from a prior Egypt file if present."""
    blocks: list[str] = []
    for m in re.finditer(
        r"^[ \t]*Behavior\s*=\s*(?:OCLSpecialPower|SpectreGunshipDeploymentUpdate)"
        r"\s+ModuleTag_Egypt\w*\n(?:.*?\n)*?^[ \t]*End\s*$",
        text,
        re.M,
    ):
        blocks.append(m.group(0).rstrip() + "\n")
    return "\n".join(blocks)


def default_egypt_specials() -> str:
    return """  Behavior           = OCLSpecialPower ModuleTag_EgyptInsertion
    SpecialPowerTemplate = SuperweaponEgyptSFInsertion
    OCL                  = SUPERWEAPON_Paradrop1
    CreateLocation       = CREATE_AT_EDGE_NEAR_SOURCE
    OCLAdjustPositionToPassable = Yes
  End

  Behavior           = OCLSpecialPower ModuleTag_EgyptTu22
    SpecialPowerTemplate = SuperweaponEgyptTu22CruiseMissileStrike
    OCL                  = SUPERWEAPON_Tu22CruiseMissileStrike
    CreateLocation       = CREATE_AT_EDGE_NEAR_SOURCE
  End

  Behavior = SpectreGunshipDeploymentUpdate ModuleTag_EgyptAWACS
    SpecialPowerTemplate = SuperweaponEgyptAWACS
    GunshipTemplateName = US_E3G_AWACS
    AttackAreaRadius = 225
    CreateLocation = CREATE_AT_EDGE_NEAR_SOURCE
  End

  Behavior           = OCLSpecialPower ModuleTag_EgyptParadrop
    SpecialPowerTemplate = SuperweaponEgyptParadrop
    OCL                  = SUPERWEAPON_Paradrop1
    CreateLocation       = CREATE_AT_EDGE_NEAR_SOURCE
    OCLAdjustPositionToPassable = Yes
  End

  Behavior           = OCLSpecialPower ModuleTag_EgyptCruise
    SpecialPowerTemplate = SuperweaponEgyptCruiseStrike
    UpgradeOCL           = SCIENCE_Egypt_CruiseStrike3 SUPERWEAPON_US_CruiseMissileStrike_3
    UpgradeOCL           = SCIENCE_Egypt_CruiseStrike2 SUPERWEAPON_US_CruiseMissileStrike_2
    OCL                  = SUPERWEAPON_AmericaTomahawkStrike1
    CreateLocation       = CREATE_AT_EDGE_NEAR_SOURCE
  End

  Behavior           = OCLSpecialPower ModuleTag_EgyptFOAB
    SpecialPowerTemplate = SuperweaponEgyptFOAB
    OCL                  = SUPERWEAPON_FOAB
    CreateLocation       = CREATE_AT_EDGE_NEAR_SOURCE
  End

  Behavior           = OCLSpecialPower ModuleTag_EgyptRecon
    SpecialPowerTemplate = SuperweaponEgyptReconnaissance
    OCL                  = SUPERWEAPON_SpySatellite
    CreateLocation       = CREATE_AT_EDGE_NEAR_SOURCE
  End
"""


def build_egypt_cc() -> bytes:
    """ONE clean Egypt_CommandCenter from USA AmericaCommandCenter donor."""
    usa = USA_LOOSE.read_text(encoding="utf-8", errors="replace")
    live_specials = ""
    if EGYPT_LIVE.exists():
        live_specials = extract_egypt_specials(
            EGYPT_LIVE.read_text(encoding="utf-8", errors="replace")
        )
    specials = live_specials.strip() or default_egypt_specials().strip()
    if "US_E3G_AWACS" not in specials:
        specials += (
            "\n\n  Behavior = SpectreGunshipDeploymentUpdate ModuleTag_EgyptAWACS\n"
            "    SpecialPowerTemplate = SuperweaponEgyptAWACS\n"
            "    GunshipTemplateName = US_E3G_AWACS\n"
            "    AttackAreaRadius = 225\n"
            "    CreateLocation = CREATE_AT_EDGE_NEAR_SOURCE\n"
            "  End"
        )

    text = usa
    text = re.sub(
        r"^Object\s+AmericaCommandCenter\b",
        "Object Egypt_CommandCenter",
        text,
        count=1,
        flags=re.M,
    )
    text = re.sub(r"(^\s*Side\s*=\s*)\S+", r"\1Egypt", text, count=1, flags=re.M)
    text = re.sub(
        r"(^\s*CommandSet\s*=\s*)\S+",
        r"\1Egypt_CommandCenterCommandSet",
        text,
        count=1,
        flags=re.M,
    )
    text = re.sub(
        r"(^\s*DisplayName\s*=\s*)\S+",
        r"\1OBJECT:Egypt_CommandCenter",
        text,
        count=1,
        flags=re.M,
    )
    text = re.sub(
        r"(^\s*BuildCost\s*=\s*)\S+",
        lambda m: m.group(1) + "2000",
        text,
        count=1,
        flags=re.M,
    )
    text = re.sub(
        r"(^\s*BuildTime\s*=\s*)[^\n;]+",
        lambda m: m.group(1) + "45.0           ",
        text,
        count=1,
        flags=re.M,
    )
    text = re.sub(
        r"(^\s*MaxHealth\s*=\s*)\S+",
        lambda m: m.group(1) + "5000.0",
        text,
        flags=re.M,
    )
    text = re.sub(
        r"(^\s*InitialHealth\s*=\s*)\S+",
        lambda m: m.group(1) + "5000.0",
        text,
        flags=re.M,
    )
    if not re.search(r"^Scale\s*=", text, re.M):
        text = re.sub(
            r"(Object Egypt_CommandCenter\n)",
            r"\1Scale = 0.8\n",
            text,
            count=1,
        )

    # Remove USA special-power / gunship / America SpecialAbility AWACS+Spectre modules.
    # Keep Production / Die / Flammable / TransitionDamageFX / Geometry / Draw.
    def strip_usa_specials(src: str) -> str:
        lines = src.splitlines(keepends=True)
        out: list[str] = []
        i = 0
        skip_types = (
            "OCLSpecialPower",
            "SpectreGunshipDeploymentUpdate",
        )
        while i < len(lines):
            line = lines[i]
            code = line.split(";", 1)[0]
            m = re.match(
                r"^([ \t]*)Behavior\s*=\s*(\S+)(?:\s+(\S+))?",
                code,
            )
            if m and m.group(2) in skip_types:
                # skip until matching End at same-or-less indent of Behavior block
                i += 1
                while i < len(lines):
                    if re.match(r"^[ \t]*End\s*$", lines[i].split(";", 1)[0]):
                        i += 1
                        break
                    i += 1
                continue
            # Drop America AWACS / Spectre SpecialAbility companions (Egypt uses own)
            if m and m.group(2) == "SpecialAbility":
                # peek block for America templates
                block = [line]
                j = i + 1
                while j < len(lines):
                    block.append(lines[j])
                    if re.match(r"^[ \t]*End\s*$", lines[j].split(";", 1)[0]):
                        break
                    j += 1
                blob = "".join(block)
                if any(
                    x in blob
                    for x in (
                        "SuperweaponAmerica_AWACS",
                        "SuperweaponSpectreGunship",
                        "SuperweaponAmerica",
                    )
                ):
                    i = j + 1
                    continue
            out.append(line)
            i += 1
        return "".join(out)

    text = strip_usa_specials(text)

    specials_block = (
        "\n  ; --- Egypt specials only ---\n" + specials.rstrip() + "\n\n"
    )
    # Insert Egypt specials just before KindOf (engineering section)
    if re.search(r"^[ \t]*KindOf\s*=", text, re.M):
        text = re.sub(
            r"(^[ \t]*KindOf\s*=)",
            specials_block + r"\1",
            text,
            count=1,
            flags=re.M,
        )
    else:
        text = text.replace("\nEnd\n", "\n" + specials_block + "End\n", 1)

    # Absolute scrub of forbidden tokens in code (not model names that shouldn't remain)
    scrubbed_lines = []
    for line in text.splitlines(True):
        code, sep, comment = line.partition(";")
        if FORBID_RE.search(code):
            code = code.replace("Iraq_Adnan1", "US_E3G_AWACS")
            code = re.sub(r"irq_[A-Za-z0-9_]+", "us_commandcenter", code, flags=re.I)
            code = re.sub(r"Irq_[A-Za-z0-9_]+", "US_Command", code)
            code = re.sub(r"SUPERWEAPON_Iraq\w*", "SUPERWEAPON_SpySatellite", code)
            code = re.sub(r"Iraq_PlayerTemplate", "Egypt_PlayerTemplate", code)
            code = re.sub(r"\bIraqi[A-Za-z0-9_]*", "Egypt", code)
            code = re.sub(r"\bIraq\b", "Egypt", code)
            line = code + ((";" + comment) if sep else "")
            if not line.endswith("\n") and line:
                line += "\n"
        scrubbed_lines.append(line)
    text = "".join(scrubbed_lines)

    header = (
        "; SPECTER ROOT FIX - Egypt_CommandCenter\n"
        "; Built from USA AmericaCommandCenter donor (ART/Geometry/Draw/Production/Die)\n"
        "; ART: us_commandcenter / US_Command / US_COM_Strb\n"
        "; Side=Egypt CommandSet=Egypt_CommandCenterCommandSet\n"
        "; BuildCost=2000 BuildTime=45 MaxHealth=5000\n"
        "; Egypt specials only; GunshipTemplateName=US_E3G_AWACS\n"
        "; Forbidden donor identity tokens scrubbed from code lines\n"
        "; Packed into _SPECTER_ROOT_FIXED_FINAL.big from extracted clean files\n\n"
    )
    text = header + text

    def code_only(src: str) -> str:
        return "\n".join(line.split(";", 1)[0] for line in src.splitlines())

    code = code_only(text)
    # Hard checks (code lines only for forbidden tokens)
    checks = [
        ("Object Egypt_CommandCenter", "Object Egypt_CommandCenter" in text),
        ("Side=Egypt", bool(re.search(r"^\s*Side\s*=\s*Egypt\b", text, re.M))),
        ("CommandSet", "Egypt_CommandCenterCommandSet" in text),
        ("BuildCost", bool(re.search(r"^\s*BuildCost\s*=\s*2000\b", text, re.M))),
        ("BuildTime", bool(re.search(r"^\s*BuildTime\s*=\s*45", text, re.M))),
        ("MaxHealth", bool(re.search(r"^\s*MaxHealth\s*=\s*5000", text, re.M))),
        ("us_commandcenter", "us_commandcenter" in text),
        ("US_Command", "US_Command" in text),
        ("US_COM_Strb", "US_COM_Strb" in text),
        ("US_E3G_AWACS", "US_E3G_AWACS" in text),
        ("Geometry BOX", bool(re.search(r"^\s*Geometry\s*=\s*BOX\b", text, re.M))),
        ("ProductionUpdate", "ProductionUpdate" in text),
        ("DestroyDie", "DestroyDie" in text),
        ("no irq_comndcntr", "irq_comndcntr" not in code),
        ("no Iraq_Adnan1", "Iraq_Adnan1" not in code),
        ("no SUPERWEAPON_Iraq", "SUPERWEAPON_Iraq" not in code),
        ("no Iraq_PlayerTemplate", "Iraq_PlayerTemplate" not in code),
        ("not broken SPEC sha", hashlib.sha256(text.encode("utf-8")).hexdigest() != BROKEN_SPEC_SHA),
    ]
    for label, ok in checks:
        if not ok:
            raise SystemExit(f"Egypt CC build failed: {label}")
    for i, line in enumerate(text.splitlines(), 1):
        c = line.split(";", 1)[0]
        if FORBID_RE.search(c):
            raise SystemExit(f"Forbidden token in Egypt CC line {i}: {line}")
    return text.encode("utf-8")


def big_path_to_fs(base: Path, big_name: str) -> Path | None:
    norm = big_name.replace("/", "\\")
    parts = [p for p in norm.split("\\") if p]
    if not parts or parts[0].lower() != "data":
        return None
    return base.joinpath(*parts[1:])


def extract_spec_to_tree(entries: dict[str, bytes], dest: Path) -> int:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    n = 0
    for name, content in entries.items():
        out = big_path_to_fs(dest, name)
        if out is None:
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(content)
        n += 1
    return n


def overlay_patch_data(dest: Path, patch_data: Path) -> int:
    n = 0
    for path in patch_data.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(patch_data)
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(path.read_bytes())
        n += 1
    return n


def find_egypt_cc_on_disk(base: Path) -> list[Path]:
    hits = []
    for p in base.rglob("*"):
        if p.is_file() and p.name.lower() == "egypt_commandcenter.ini":
            hits.append(p)
    return sorted(hits)


def pack_tree(base: Path) -> dict[str, bytes]:
    file_map: dict[str, bytes] = {}
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base).as_posix()
        key = "Data\\" + rel.replace("/", "\\")
        file_map[key] = path.read_bytes()
    # ensure only one egypt cc key (case-insensitive)
    egypt_keys = [k for k in file_map if is_egypt_cc_name(k)]
    for k in egypt_keys:
        if k != EGYPT_BIG_PATH:
            del file_map[k]
    return file_map


def soft_ini_parse(text: str) -> tuple[list[str], list[str]]:
    """Minimal End-balance / Object structure checks."""
    hard: list[str] = []
    soft: list[str] = []
    depth = 0
    for i, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0].rstrip()
        if not code.strip():
            continue
        if re.match(r"^\s*End\s*$", code):
            depth -= 1
            if depth < 0:
                hard.append(f"line {i}: End without open block")
                depth = 0
            continue
        # openers
        if re.match(
            r"^\s*(Object|Draw|Behavior|ArmorSet|Body|UnitSpecificSounds|"
            r"ConditionState|ActiveBody|WeaponSet)\b",
            code,
        ):
            depth += 1
    if depth != 0:
        hard.append(f"unbalanced End depth={depth}")
    if "Object " in text and not re.search(r"^\s*Object\s+\S+", text, re.M):
        hard.append("missing Object header")
    return hard, soft


def validate_reextracted(base: Path) -> tuple[bool, list[str], list[str]]:
    passes: list[str] = []
    fails: list[str] = []

    egypt = find_egypt_cc_on_disk(base)
    if len(egypt) == 1:
        passes.append(f"only one Egypt_CommandCenter.ini: {egypt[0].relative_to(base)}")
    else:
        fails.append(f"Egypt_CommandCenter.ini count={len(egypt)} paths={egypt}")

    # Object Egypt_CommandCenter unique across all INI
    obj_map: dict[str, list[str]] = defaultdict(list)
    obj_re = re.compile(r"^\s*Object\s+(\S+)", re.M)
    for ini in base.rglob("*.ini"):
        try:
            text = ini.read_text(encoding="utf-8", errors="replace")
        except Exception:
            text = ini.read_bytes().decode("latin1", errors="replace")
        for m in obj_re.finditer(text):
            obj_map[m.group(1)].append(str(ini.relative_to(base)))

    egypt_objs = obj_map.get("Egypt_CommandCenter", [])
    if len(egypt_objs) == 1:
        passes.append("Object Egypt_CommandCenter unique")
    else:
        fails.append(f"Object Egypt_CommandCenter defs={len(egypt_objs)} in {egypt_objs}")

    # Object duplicate count for Egypt_CommandCenter specifically must be 0 extras
    dup_egypt = max(0, len(egypt_objs) - 1)
    if dup_egypt == 0:
        passes.append("Object duplicate count = 0 (Egypt_CommandCenter)")
    else:
        fails.append(f"Object duplicate count = {dup_egypt}")

    # Also flag any other Object name with >1 definition under Specter Buildings CC/MHQ/AAB
    crit_dups = {
        o: ps
        for o, ps in obj_map.items()
        if len(ps) > 1
        and any(
            x in o
            for x in ("CommandCenter", "MilitaryHQ", "AdvancedAirBase")
        )
    }
    if not crit_dups:
        passes.append("0 CommandCenter/MilitaryHQ/AAB Object name dups")
    else:
        fails.append(f"critical Object dups: {crit_dups}")

    if egypt:
        text = egypt[0].read_text(encoding="utf-8", errors="replace")
        sha = hashlib.sha256(egypt[0].read_bytes()).hexdigest()
        hard, soft = soft_ini_parse(text)
        if not hard:
            passes.append("INI parser PASS (Egypt_CommandCenter)")
        else:
            fails.append(f"INI parser FAIL: {hard}")
        if soft:
            passes.append(f"INI soft warnings={len(soft)}")

        req = [
            ("Side=Egypt", bool(re.search(r"^\s*Side\s*=\s*Egypt\b", text, re.M))),
            ("Egypt_CommandCenterCommandSet", "Egypt_CommandCenterCommandSet" in text),
            ("us_commandcenter", "us_commandcenter" in text),
            ("US_Command", "US_Command" in text),
            ("US_COM_Strb", "US_COM_Strb" in text),
            ("US_E3G_AWACS", "US_E3G_AWACS" in text),
            ("Geometry", "Geometry" in text),
            ("ProductionUpdate", "ProductionUpdate" in text),
            ("DestroyDie", "DestroyDie" in text),
            ("BuildCost=2000", bool(re.search(r"^\s*BuildCost\s*=\s*2000\b", text, re.M))),
            ("BuildTime=45", bool(re.search(r"^\s*BuildTime\s*=\s*45", text, re.M))),
            ("MaxHealth=5000", bool(re.search(r"^\s*MaxHealth\s*=\s*5000", text, re.M))),
            ("NOT broken SPEC sha", sha != BROKEN_SPEC_SHA),
        ]
        for label, ok in req:
            (passes if ok else fails).append(("PASS: " if ok else "FAIL: ") + label)

        for i, line in enumerate(text.splitlines(), 1):
            code = line.split(";", 1)[0]
            if FORBID_RE.search(code):
                fails.append(f"forbidden token line {i}: {line.strip()}")
                break
        else:
            passes.append("NO irq_/Irq_/Iraq/Iraqi/SUPERWEAPON_Iraq/Iraq_PlayerTemplate")

    return (not fails), passes, fails


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== 1) SCAN all BIG + loose Egypt_CommandCenter copies ===")
    scan = scan_all_egypt_copies()
    broken = [h for h in scan if h.get("broken")]
    print(f"Total Egypt_CommandCenter hits: {len(scan)}")
    print(f"Broken hits: {len(broken)}")

    removed_lines = [
        "REMOVED / SUPERSEDED Egypt_CommandCenter DUPLICATES",
        "==================================================",
        f"Scan hits (BIG+loose): {len(scan)}",
        f"Broken hits found: {len(broken)}",
        "",
        "Broken sources (will NOT be used in ROOT FIXED FINAL):",
    ]
    for h in broken:
        removed_lines.append(
            f"  BROKEN  {h['source']} :: {h['path']}  sha={h['sha256']} size={h['size']}"
        )
    removed_lines.append("")
    removed_lines.append("All scanned copies:")
    for h in scan:
        tag = "BROKEN" if h.get("broken") else "other"
        removed_lines.append(
            f"  [{tag}] {h['source']} :: {h['path']}  sha={h['sha256']}"
        )

    print("=== 2) EXTRACT vendor SPEC DATA to clean filesystem tree ===")
    if not SPEC_DATA.exists():
        raise SystemExit(f"Missing SPEC DATA: {SPEC_DATA}")
    # Explicitly do not reuse/rename SPEC; only read as extraction source.
    spec_entries = read_big(SPEC_DATA)
    print(f"SPEC entries: {len(spec_entries)}")
    # ART scan note
    if SPEC_ART.exists():
        art = read_big(SPEC_ART)
        art_egypt = [k for k in art if is_egypt_cc_name(k)]
        print(f"ART Egypt_CommandCenter.ini count: {len(art_egypt)} (expected 0)")
    n = extract_spec_to_tree(spec_entries, EXTRACTED)
    print(f"Extracted Data files: {n}")

    print("=== 3) Overlay accepted patch/Data ===")
    n_ov = overlay_patch_data(EXTRACTED, PATCH_DATA)
    print(f"Overlayed patch files: {n_ov}")

    print("=== 4) Delete EVERY Egypt_CommandCenter.ini from extracted tree ===")
    before = find_egypt_cc_on_disk(EXTRACTED)
    removed_lines.append("")
    removed_lines.append("Deleted from extracted rebuild tree:")
    for p in before:
        removed_lines.append(f"  DELETED  {p.relative_to(EXTRACTED)}")
        print("  DELETE", p.relative_to(EXTRACTED))
        p.unlink()
    after = find_egypt_cc_on_disk(EXTRACTED)
    if after:
        print("FAIL: egypt still present", after)
        return 1
    print("Deleted count:", len(before))

    print("=== 5) Write ONE clean USA-donor Egypt_CommandCenter.ini ===")
    egypt_bytes = build_egypt_cc()
    egypt_out = (
        EXTRACTED
        / "INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
    )
    egypt_out.parent.mkdir(parents=True, exist_ok=True)
    egypt_out.write_bytes(egypt_bytes)
    EGYPT_LIVE.parent.mkdir(parents=True, exist_ok=True)
    EGYPT_LIVE.write_bytes(egypt_bytes)
    egypt_sha = hashlib.sha256(egypt_bytes).hexdigest()
    print("Wrote", egypt_out.relative_to(EXTRACTED), "sha", egypt_sha)

    print("=== 6) Pack NEW BIG from extracted clean files (not patch-over) ===")
    file_map = pack_tree(EXTRACTED)
    # force canonical egypt
    file_map[EGYPT_BIG_PATH] = egypt_bytes
    egypt_in_map = [k for k in file_map if is_egypt_cc_name(k)]
    print("Egypt keys in pack map:", egypt_in_map)
    if len(egypt_in_map) != 1:
        print("FAIL egypt key count", len(egypt_in_map))
        return 1
    big_bytes = build_big(file_map)
    OUT_BIG.write_bytes(big_bytes)
    big_sha = hashlib.sha256(big_bytes).hexdigest()
    (OUT_DIR / "_SPECTER_ROOT_FIXED_FINAL.big.sha256").write_text(
        big_sha + "\n", encoding="utf-8"
    )
    print("Packed", OUT_BIG, "entries", len(file_map), "sha", big_sha, "size", len(big_bytes))

    print("=== 7) RE-EXTRACT generated BIG and validate ===")
    packed_entries = read_big(OUT_BIG)
    if REEXTRACT.exists():
        shutil.rmtree(REEXTRACT)
    n_re = extract_spec_to_tree(packed_entries, REEXTRACT)
    print(f"Re-extracted files: {n_re}")
    ok, passes, fails = validate_reextracted(REEXTRACT)

    # Also validate directly from BIG entries (belt+suspenders)
    big_egypt = [k for k in packed_entries if is_egypt_cc_name(k)]
    if len(big_egypt) != 1:
        fails.append(f"BIG egypt paths={big_egypt}")
        ok = False
    else:
        passes.append(f"BIG path: {big_egypt[0]}")
        if hashlib.sha256(packed_entries[big_egypt[0]]).hexdigest() != egypt_sha:
            fails.append("BIG egypt content sha mismatch vs written")
            ok = False
        else:
            passes.append("BIG egypt content sha matches written clean file")
        if hashlib.sha256(packed_entries[big_egypt[0]]).hexdigest() == BROKEN_SPEC_SHA:
            fails.append("BIG still contains broken SPEC egypt sha")
            ok = False

    verdict = "PASS" if ok else "FAIL"
    report = [
        "SPECTER ROOT FIXED FINAL — VERIFY REPORT",
        "=" * 60,
        f"VERDICT: {verdict}",
        f"BIG: _SPECTER_ROOT_FIXED_FINAL.big",
        f"SHA256: {big_sha}",
        f"Size: {len(big_bytes)} bytes",
        f"Entries: {len(file_map)}",
        "",
        "Build method: EXTRACT SPEC DATA -> overlay patch/Data -> delete all",
        "Egypt_CommandCenter.ini -> write ONE USA-donor -> pack NEW BIG.",
        "NOT an in-place patch of an old BIG. NOT a reuse/rename of _SPEC_DATA_ONE.big.",
        "",
        f"Egypt content SHA256: {egypt_sha}",
        f"Broken SPEC egypt SHA (must be absent): {BROKEN_SPEC_SHA}",
        f"Pre-scan Egypt copies found: {len(scan)} (broken={len(broken)})",
        f"Deleted from rebuild tree: {len(before)}",
        "",
        f"PASS lines: {len(passes)}  FAIL lines: {len(fails)}",
        "",
    ]
    for p in passes:
        report.append("PASS: " + p if not p.startswith("PASS:") else p)
    for f in fails:
        report.append("FAIL: " + f if not f.startswith("FAIL:") else f)
    report.append("")
    report.append(f"FINAL: {verdict}")
    report_text = "\n".join(report) + "\n"
    (OUT_DIR / "VERIFY_REPORT.txt").write_text(report_text, encoding="utf-8")
    (OUT_DIR / "REMOVED_DUPLICATES.txt").write_text(
        "\n".join(removed_lines) + "\n", encoding="utf-8"
    )

    readme = f"""SPECTER ROOT FIXED FINAL
========================

File: _SPECTER_ROOT_FIXED_FINAL.big

This is a NEW standalone Data BIG rebuilt from extracted clean files.
It is NOT an overlay and NOT a renamed _SPEC_DATA_ONE.big.

ROOT CAUSE:
Vendor _SPEC_DATA_ONE.big still contains broken Egypt_CommandCenter.ini
(sha {BROKEN_SPEC_SHA}) with irq_comndcntr / Irq_Command / Iraq_Adnan1.

INSTALL:
1. Backup your current _SPEC_DATA_ONE.big
2. Copy _SPECTER_ROOT_FIXED_FINAL.big into the Zero Hour / Specter folder
3. Replace _SPEC_DATA_ONE.big with this file (rename to _SPEC_DATA_ONE.big)
4. Keep _SPEC_ART_ONE.big
5. Remove ALL other Specter overlay / CLEAN / V2 / TEST_BUILD patch BIGs
   so only ONE Data BIG provides Egypt_CommandCenter.ini

SHA256: {big_sha}
Validation: {verdict} (see VERIFY_REPORT.txt)
Removed duplicates: see REMOVED_DUPLICATES.txt
"""
    (OUT_DIR / "README_INSTALL.txt").write_text(readme, encoding="utf-8")
    print(report_text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
