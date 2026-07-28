#!/usr/bin/env python3
"""FULL REPAIR + rebuild _SPECTER_FINAL_REPAIRED.big from cleaned extracted tree.

Applies only the audit-required fixes; keeps valid countries/units/upgrades.
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
PATCH_DATA = ROOT / "Data"
USA_LOOSE = ROOT / (
    "Release/SPECTER_ULTIMATE_LOOSE_FILES_PATCH/Data/INI/Object/Specter/"
    "United States Of America/Buildings/CommandCenter.ini"
)
EGYPT_LIVE = ROOT / (
    "Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
)
OUT = ROOT / "Release/SPECTER_FINAL_REPAIRED"
EXTRACTED = OUT / "_extracted_Data"
REEXTRACT = OUT / "_reextract_validate"
OUT_BIG = OUT / "_SPECTER_FINAL_REPAIRED.big"
EGYPT_BIG = (
    r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_CommandCenter.ini"
)
BROKEN_EGYPT_SHA = "1b559b9e0d4eb1400e76934196eb71205c1ff21317e610d717c1da1dc7870b61"
FORBID_RE = re.compile(r"irq_|Irq_|Iraq|Iraqi|SUPERWEAPON_Iraq|Iraq_PlayerTemplate")

AIRFIELD_CS = [
    "AmericaAirfieldCommandSet",
    "AmericaAirfieldCommandSet_T",
    "AmericaAirfieldCommandSet_T1",
    "AmericaAirfieldCommandSet_T2",
    "AmericaAirfieldCommandSet_T3",
    "ChinaAirfieldCommandSet",
    "RussiaAirfieldCommandSet",
]
RUSSIA_CB_DUPES = [
    "Command_ConstructRussiaAirfield_T",
    "Command_ConstructRussiaArtillery2S7M",
    "Command_ConstructRussiaTankT90A",
    "Command_ConstructRussiaVehicleS500",
    "Command_ConstructRussiaWarFactory_T",
]


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


def overlay_patch(dest: Path, patch: Path) -> int:
    n = 0
    for path in patch.rglob("*"):
        if not path.is_file():
            continue
        out = dest / path.relative_to(patch)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(path.read_bytes())
        n += 1
    return n


def remove_named_blocks(text: str, kind: str, names: list[str], keep_first: bool = False) -> tuple[str, list[str]]:
    """Remove CommandSet/CommandButton blocks by name.

    keep_first=True: delete 2nd+ occurrences only.
    keep_first=False: delete all occurrences (used when another file keeps the def).
    """
    removed: list[str] = []
    for name in names:
        pattern = re.compile(
            rf"(^[ \t]*{kind}\s+{re.escape(name)}\b[\s\S]*?^[ \t]*End\s*\n?)",
            re.M,
        )
        matches = list(pattern.finditer(text))
        if not matches:
            continue
        if keep_first:
            # remove from last to second
            for m in reversed(matches[1:]):
                text = text[: m.start()] + text[m.end() :]
                removed.append(f"{kind} {name} (duplicate)")
        else:
            for m in reversed(matches):
                text = text[: m.start()] + text[m.end() :]
                removed.append(f"{kind} {name}")
    return text, removed


def extract_egypt_specials(text: str) -> str:
    blocks = []
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
    usa = USA_LOOSE.read_text(encoding="utf-8", errors="replace")
    specials = ""
    if EGYPT_LIVE.exists():
        specials = extract_egypt_specials(
            EGYPT_LIVE.read_text(encoding="utf-8", errors="replace")
        )
    specials = (specials.strip() or default_egypt_specials().strip())
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

    # Strip USA special powers / America AWACS+Spectre SpecialAbility
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    skip_types = {"OCLSpecialPower", "SpectreGunshipDeploymentUpdate"}
    while i < len(lines):
        line = lines[i]
        code = line.split(";", 1)[0]
        m = re.match(r"^([ \t]*)Behavior\s*=\s*(\S+)", code)
        if m and m.group(2) in skip_types:
            i += 1
            while i < len(lines):
                if re.match(r"^[ \t]*End\s*$", lines[i].split(";", 1)[0]):
                    i += 1
                    break
                i += 1
            continue
        if m and m.group(2) == "SpecialAbility":
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
    text = "".join(out)

    specials_block = "\n  ; --- Egypt specials only ---\n" + specials.rstrip() + "\n\n"
    text = re.sub(
        r"(^[ \t]*KindOf\s*=)",
        specials_block + r"\1",
        text,
        count=1,
        flags=re.M,
    )

    header = (
        "; SPECTER FINAL REPAIRED - Egypt_CommandCenter\n"
        "; USA AmericaCommandCenter donor (ART/Geometry/Draw/Production/Die)\n"
        "; Side=Egypt CommandSet=Egypt_CommandCenterCommandSet\n"
        "; BuildCost=2000 BuildTime=45 MaxHealth=5000 Gunship=US_E3G_AWACS\n\n"
    )
    text = header + text
    for i, line in enumerate(text.splitlines(), 1):
        if FORBID_RE.search(line.split(";", 1)[0]):
            raise SystemExit(f"Egypt forbid token line {i}: {line}")
    req = [
        "Object Egypt_CommandCenter",
        "Side",
        "Egypt_CommandCenterCommandSet",
        "us_commandcenter",
        "US_Command",
        "US_COM_Strb",
        "US_E3G_AWACS",
        "ProductionUpdate",
        "DestroyDie",
        "Geometry",
    ]
    for r in req:
        if r == "Side":
            if not re.search(r"^\s*Side\s*=\s*Egypt\b", text, re.M):
                raise SystemExit("Egypt missing Side=Egypt")
        elif r not in text:
            raise SystemExit(f"Egypt missing {r}")
    return text.encode("utf-8")


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
    obj_re = re.compile(r"^\s*Object\s+(?![=])(\S+)", re.M)
    cs_re = re.compile(r"^\s*CommandSet\s+(?![=])(\S+)", re.M)
    cb_re = re.compile(r"^\s*CommandButton\s+(?![=])(\S+)", re.M)
    pt_re = re.compile(r"^\s*PlayerTemplate\s+(?![=])(\S+)", re.M)
    start_re = re.compile(r"^\s*StartingBuilding\s*=\s*(\S+)", re.M)
    cs_ref = re.compile(r"^\s*CommandSet\s*=\s*(\S+)", re.M)

    objects: dict[str, list[str]] = defaultdict(list)
    cs: dict[str, list[str]] = defaultdict(list)
    cb: dict[str, list[str]] = defaultdict(list)
    pts: dict[str, str] = {}
    for name, text in ini.items():
        for m in obj_re.finditer(text):
            objects[m.group(1)].append(name)
        for m in cs_re.finditer(text):
            cs[m.group(1)].append(name)
        for m in cb_re.finditer(text):
            cb[m.group(1)].append(name)
        for m in pt_re.finditer(text):
            pts[m.group(1)] = name

    dups = {o: ps for o, ps in objects.items() if len(ps) > 1}
    if not dups:
        passes.append("Object uniqueness: 0 duplicate Object names")
    else:
        fails.append(f"Object duplicates remain: {len(dups)}")

    egypt_paths = [k for k in entries if k.lower().endswith("egypt_commandcenter.ini")]
    if len(egypt_paths) == 1:
        passes.append(f"One Egypt_CommandCenter.ini: {egypt_paths[0]}")
    else:
        fails.append(f"Egypt_CommandCenter.ini count={len(egypt_paths)}")

    if objects.get("Egypt_CommandCenter") and len(objects["Egypt_CommandCenter"]) == 1:
        passes.append("Object Egypt_CommandCenter unique")
    else:
        fails.append("Object Egypt_CommandCenter not unique")

    if egypt_paths:
        raw = entries[egypt_paths[0]]
        sha = hashlib.sha256(raw).hexdigest()
        text = raw.decode("utf-8", errors="replace")
        if sha == BROKEN_EGYPT_SHA:
            fails.append("Broken SPEC Egypt sha present")
        else:
            passes.append("Egypt not broken SPEC sha")
        # parser End balance with TransitionState
        open_re = re.compile(
            r"^\s*(?:Object\s+(?![=])\S+|Draw\s*=|Behavior\s*=|ArmorSet\b|Body\s*=|"
            r"UnitSpecificSounds\b|ConditionState\s*=|TransitionState\s*=|WeaponSet\b|"
            r"ClientUpdate\s*=|Turret\b|ReplaceModule\b|AddModule\b|RemoveModule\b|"
            r"Prerequisites\b)"
        )
        depth = 0
        hard = []
        for i, line in enumerate(text.splitlines(), 1):
            code = line.split(";", 1)[0]
            if not code.strip():
                continue
            if re.match(r"^\s*End\s*$", code):
                depth -= 1
                if depth < 0:
                    hard.append(i)
                    depth = 0
                continue
            if open_re.match(code):
                depth += 1
        if depth == 0 and not hard:
            passes.append("INI parser PASS (Egypt_CommandCenter)")
        else:
            fails.append(f"INI parser FAIL Egypt depth={depth} badEnds={hard[:5]}")
        for i, line in enumerate(text.splitlines(), 1):
            if FORBID_RE.search(line.split(";", 1)[0]):
                fails.append(f"Egypt forbid token line {i}")
                break
        else:
            passes.append("Egypt forbid-token scrub PASS")
        for label, ok in [
            ("us_commandcenter", "us_commandcenter" in text),
            ("US_Command", "US_Command" in text),
            ("Side=Egypt", bool(re.search(r"^\s*Side\s*=\s*Egypt\b", text, re.M))),
            ("CommandSet", "Egypt_CommandCenterCommandSet" in text),
            ("US_E3G_AWACS", "US_E3G_AWACS" in text),
        ]:
            (passes if ok else fails).append(("CC " + label) if ok else ("missing " + label))

    # CS / CB uniqueness for repaired names
    for name in AIRFIELD_CS:
        n = len(cs.get(name, []))
        if n == 1:
            passes.append(f"CommandSet {name} unique")
        else:
            fails.append(f"CommandSet {name} defs={n} in {cs.get(name)}")
    for name in RUSSIA_CB_DUPES + ["Command_ConstructPatch_Iraq_AWACS"]:
        n = len(cb.get(name, []))
        if n == 1:
            passes.append(f"CommandButton {name} unique")
        else:
            fails.append(f"CommandButton {name} defs={n} in {cb.get(name)}")

    # Iran
    iran_files = objects.get("IranCommandCenter", [])
    if iran_files:
        t = ini[iran_files[0]]
        m = cs_ref.search(t)
        if m and m.group(1) in cs:
            passes.append(f"IranCommandCenter CommandSet OK ({m.group(1)})")
        else:
            fails.append(f"IranCommandCenter CommandSet missing ({m.group(1) if m else None})")

    # PlayerTemplate StartingBuilding
    missing_start = []
    for pt, path in pts.items():
        t = ini[path]
        # find block
        m = re.search(
            rf"PlayerTemplate\s+{re.escape(pt)}\b([\s\S]*?)^\s*End\s*$", t, re.M
        )
        block = m.group(0) if m else t
        sm = start_re.search(block)
        if sm and sm.group(1) not in objects:
            missing_start.append((pt, sm.group(1)))
    if not missing_start:
        passes.append("PlayerTemplate StartingBuilding refs resolve")
    else:
        fails.append(f"Missing StartingBuilding: {missing_start[:10]}")

    # AAB refs
    aab_missing = []
    for o, paths in objects.items():
        if "AdvancedAirBase" not in o:
            continue
        t = ini[paths[0]]
        m = cs_ref.search(t)
        if not m or m.group(1) not in cs:
            aab_missing.append((o, m.group(1) if m else None))
    if not aab_missing:
        passes.append("Advanced Air Base CommandSet refs OK")
    else:
        fails.append(f"AAB missing CS: {aab_missing[:10]}")

    # Aircraft/AAB CommandButton Object refs — Specter/Patch scoped only.
    # Stock Generals variants (AirF_/Nuke_/Boss_/vanilla ChinaJetMIG etc.) use
    # ReplaceModule inheritance and are outside this patch repair scope.
    specter_missing = []
    stock_missing = []
    for name, paths in cb.items():
        if "Construct" not in name:
            continue
        if not any(
            x in name
            for x in ("Air", "Jet", "AWACS", "Bomber", "Fighter", "Raptor", "AAB", "Patch_")
        ):
            continue
        t = ini[paths[0]]
        m = re.search(
            rf"CommandButton\s+{re.escape(name)}\b([\s\S]*?)^\s*End\s*$", t, re.M
        )
        if not m:
            continue
        om = re.search(r"^\s*Object\s*=\s*(\S+)", m.group(1), re.M)
        if not om or om.group(1) in objects:
            continue
        obj = om.group(1)
        stockish = (
            name.startswith(("AirF_", "Nuke_", "Boss_", "SupW_", "Tank_", "Infy_", "Lazr_"))
            or obj.startswith(("AirF_", "Nuke_", "Boss_", "SupW_", "Tank_", "Infy_", "Lazr_"))
            or name in ("Command_ConstructChinaJetMIG",)
            or obj in ("ChinaJetMIG",)
        )
        if stockish:
            stock_missing.append((name, obj))
        else:
            specter_missing.append((name, obj))
    if not specter_missing:
        passes.append("Specter/Patch aircraft CommandButton Object refs OK")
    else:
        for a in specter_missing[:20]:
            fails.append(f"Missing Specter aircraft Object for {a[0]} -> {a[1]}")
    if stock_missing:
        passes.append(
            f"Stock Generals missing-ref note (not patch scope): {len(stock_missing)}"
        )

    return (not fails), passes, fails


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    fixed_log: list[str] = []

    print("=== EXTRACT SPEC DATA ===")
    spec = read_big(SPEC_DATA)
    n = extract_tree(spec, EXTRACTED)
    print("extracted", n)

    print("=== OVERLAY patch/Data ===")
    print("overlayed", overlay_patch(EXTRACTED, PATCH_DATA))

    print("=== REPAIR: Egypt_CommandCenter ONE USA donor ===")
    for p in EXTRACTED.rglob("*"):
        if p.is_file() and p.name.lower() == "egypt_commandcenter.ini":
            fixed_log.append(f"DELETED duplicate/old {p.relative_to(EXTRACTED)}")
            p.unlink()
    egypt = build_egypt_cc()
    egypt_path = (
        EXTRACTED
        / "INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
    )
    egypt_path.parent.mkdir(parents=True, exist_ok=True)
    egypt_path.write_bytes(egypt)
    EGYPT_LIVE.parent.mkdir(parents=True, exist_ok=True)
    EGYPT_LIVE.write_bytes(egypt)
    fixed_log.append(
        f"WROTE one Egypt_CommandCenter.ini sha={hashlib.sha256(egypt).hexdigest()}"
    )

    print("=== REPAIR: IranCommandCenter CommandSet ===")
    iran = (
        EXTRACTED / "INI/Object/Specter/Iranian Army/Buildings/Command.ini"
    )
    if iran.exists():
        t = iran.read_text(encoding="utf-8", errors="replace")
        if "IranExpandedHQCommandSet" in t:
            t2 = t.replace("IranExpandedHQCommandSet", "IranHQCommandSet")
            iran.write_bytes(t2.encode("utf-8"))
            # sync into patch/Data for source of truth
            patch_iran = PATCH_DATA / "INI/Object/Specter/Iranian Army/Buildings/Command.ini"
            write_text(patch_iran, t2)
            fixed_log.append(
                "IranCommandCenter CommandSet IranExpandedHQCommandSet -> IranHQCommandSet"
            )

    print("=== REPAIR: duplicate CommandButton Patch_Iraq_AWACS ===")
    aff = EXTRACTED / "INI/CommandButton_AirForceFinal.ini"
    if aff.exists():
        t = aff.read_text(encoding="utf-8", errors="replace")
        t2, rem = remove_named_blocks(
            t, "CommandButton", ["Command_ConstructPatch_Iraq_AWACS"], keep_first=False
        )
        if rem:
            aff.write_text(t2, encoding="utf-8", newline="\n")
            write_text(PATCH_DATA / "INI/CommandButton_AirForceFinal.ini", t2)
            fixed_log.extend(f"REMOVED from AirForceFinal: {r}" for r in rem)

    print("=== REPAIR: duplicate Russia CommandButtons in CommandButton.ini ===")
    cbi = EXTRACTED / "INI/CommandButton.ini"
    if cbi.exists():
        t = cbi.read_text(encoding="utf-8", errors="replace")
        t2, rem = remove_named_blocks(t, "CommandButton", RUSSIA_CB_DUPES, keep_first=True)
        if rem:
            cbi.write_text(t2, encoding="utf-8", newline="\n")
            write_text(PATCH_DATA / "INI/CommandButton.ini", t2)
            fixed_log.extend(f"REMOVED from CommandButton.ini: {r}" for r in rem)

    print("=== REPAIR: duplicate Airfield CommandSets in CommandSet.ini ===")
    csi = EXTRACTED / "INI/CommandSet.ini"
    if csi.exists():
        t = csi.read_text(encoding="utf-8", errors="replace")
        t2, rem = remove_named_blocks(t, "CommandSet", AIRFIELD_CS, keep_first=False)
        if rem:
            csi.write_text(t2, encoding="utf-8", newline="\n")
            write_text(PATCH_DATA / "INI/CommandSet.ini", t2)
            fixed_log.extend(
                f"REMOVED from CommandSet.ini (kept AABOnly): {r}" for r in rem
            )

    print("=== PACK NEW BIG from cleaned tree ===")
    file_map = pack_tree(EXTRACTED)
    # ensure canonical egypt
    file_map[EGYPT_BIG] = egypt
    # purge any other egypt keys
    for k in list(file_map):
        if k.lower().endswith("egypt_commandcenter.ini") and k != EGYPT_BIG:
            del file_map[k]
            fixed_log.append(f"PURGED pack key {k}")
    big = build_big(file_map)
    OUT_BIG.write_bytes(big)
    big_sha = hashlib.sha256(big).hexdigest()
    (OUT / "_SPECTER_FINAL_REPAIRED.big.sha256").write_text(big_sha + "\n", encoding="utf-8")
    print("packed", OUT_BIG, "entries", len(file_map), "sha", big_sha)

    print("=== RE-EXTRACT + VALIDATE ===")
    packed = read_big(OUT_BIG)
    extract_tree(packed, REEXTRACT)
    ok, passes, fails = validate(packed)
    verdict = "PASS" if ok else "FAIL"

    report = [
        "SPECTER FINAL REPAIRED — VERIFY REPORT",
        "=" * 60,
        f"VERDICT: {verdict}",
        f"BIG: _SPECTER_FINAL_REPAIRED.big",
        f"SHA256: {big_sha}",
        f"Size: {len(big)} bytes",
        f"Entries: {len(file_map)}",
        "",
        "Build: EXTRACT SPEC -> overlay patch/Data -> audit repairs -> pack NEW BIG",
        "Not an overlay. Not a rename of _SPEC_DATA_ONE.big.",
        "",
        "PROBLEMS FIXED:",
    ]
    for line in fixed_log:
        report.append(f"  - {line}")
    report += ["", f"PASS: {len(passes)}  FAIL: {len(fails)}", ""]
    for p in passes:
        report.append("PASS: " + p)
    for f in fails:
        report.append("FAIL: " + f)
    report += ["", f"FINAL: {verdict}"]
    (OUT / "VERIFY_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "PROBLEMS_FIXED.txt").write_text("\n".join(fixed_log) + "\n", encoding="utf-8")

    readme = f"""SPECTER FINAL REPAIRED
======================

File: _SPECTER_FINAL_REPAIRED.big
SHA256: {big_sha}
Validation: {verdict}

INSTALL:
1. Backup _SPEC_DATA_ONE.big
2. Copy _SPECTER_FINAL_REPAIRED.big into Zero Hour / Specter folder
3. Replace _SPEC_DATA_ONE.big with this file (rename recommended)
4. Keep _SPEC_ART_ONE.big
5. DELETE all other Specter Data/test/clean/fixed/V2/ROOT overlay BIGs
   so only ONE Data BIG is loaded

See VERIFY_REPORT.txt and AUDIT_REPORT.txt
"""
    (OUT / "README_INSTALL.txt").write_text(readme, encoding="utf-8")
    print("\n".join(report))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
