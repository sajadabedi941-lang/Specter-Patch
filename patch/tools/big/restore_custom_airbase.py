#!/usr/bin/env python3
"""Restore OLD _SPEC AdvancedAirBase infrastructure onto a PR #482 DATA stage.

Donor-only: copies the custom 16-pad AAB objects/buttons/images/strings from OLD
_SPEC and last-wins builder CommandSets so playable factions construct AAB
instead of the broken PR #482 LargeAirBase/HeavyAirBase TheAirPort chain.

Does not import old PlayerTemplate, Weapon.ini, CommandSet.ini, faction
expansion, the India .z01 leftover, or PR #483 stock-airfield Draw patches.
AAB production CommandSets reuse PR #482 aircraft buttons (Large+Heavy merged)
so Iraq unlocks survive.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
from collections import defaultdict
from pathlib import Path

OLD = Path("/tmp/SPEC_OLD_DONOR_STAGE")
PR = Path("/tmp/PR482_DATA_STAGE")
STAGE = Path("/tmp/AAB_RESTORE_STAGE")
OUT_DIR = Path("/tmp/AAB_RESTORE_OUT")
REPORT = Path("/tmp/AAB_RESTORE/restore_report.txt")

PACKED = lambda p: str(p).replace("/", "\\")

# PR #482 stub folders that renamed the OLD faction directory
STUB_PATH_MAP = {
    Path("Data/INI/Object/Specter/Saudi Arabian Armed Forces/Buildings/SaudiArabia_AdvancedAirBase.ini"):
        Path("Data/INI/Object/Specter/Saudi Arabia Armed Forces/Buildings/SaudiArabia_AdvancedAirBase.ini"),
    Path("Data/INI/Object/Specter/Syrian Arab Army/Buildings/Syria_AdvancedAirBase.ini"):
        Path("Data/INI/Object/Specter/Syrian Armed Forces/Buildings/Syria_AdvancedAirBase.ini"),
    Path("Data/INI/Object/Specter/United Arab Emirates/Buildings/UAE_AdvancedAirBase.ini"):
        Path("Data/INI/Object/Specter/United Arab Emirates Armed Forces/Buildings/UAE_AdvancedAirBase.ini"),
}

# Builder CommandSet -> AAB construct button (and optional second slot to clear)
BUILDER_AAB_WIRE = {
    "AmericaDozerCommandSet": ("Command_ConstructAmerica_AdvancedAirBase",),
    "PLADozerCommandSet": ("Command_ConstructChina_AdvancedAirBase",),
    "ChinaDozerCommandSet": ("Command_ConstructChina_AdvancedAirBase",),
    "IranDozerCommandSet": ("Command_ConstructIran_AdvancedAirBase",),
    "Iraq_VT72BCommandSet": ("Command_ConstructIraq_AdvancedAirBase",),
    "RussiaDozerCommandSet": ("Command_ConstructRussia_AdvancedAirBase",),
    "NatoDozerCommandSet": ("Command_ConstructNato_AdvancedAirBase",),
    "AirF_AmericaDozerCommandSet": ("Command_ConstructAirF_AmericaAdvancedAirBase",),
    "NorthKorea_VT72BCommandSet": ("Command_ConstructNorthKorea_AdvancedAirBase",),
    "PakistanDozerCommandSet": ("Command_ConstructPakistan_AdvancedAirBase",),
    "SaudiArabiaDozerCommandSet": ("Command_ConstructSaudiArabia_AdvancedAirBase",),
    "UAEDozerCommandSet": ("Command_ConstructUAE_AdvancedAirBase",),
    "IndiaDozerCommandSet": ("Command_ConstructIndia_AdvancedAirBase",),
    "SyriaDozerCommandSet": ("Command_ConstructSyria_AdvancedAirBase",),
    "GermanyDozerCommandSet": ("Command_ConstructGermany_AdvancedAirBase",),
    "FranceDozerCommandSet": ("Command_ConstructFrance_AdvancedAirBase",),
    "France_WorkerCommandSet": ("Command_ConstructFrance_AdvancedAirBase",),
    "Germany_WorkerCommandSet": ("Command_ConstructGermany_AdvancedAirBase",),
    "Italy_WorkerCommandSet": ("Command_ConstructItaly_AdvancedAirBase",),
    "ItalyDozerCommandSet": ("Command_ConstructItaly_AdvancedAirBase",),
    "SwedenDozerCommandSet": ("Command_ConstructSweden_AdvancedAirBase",),
    "UkraineDozerCommandSet": ("Command_ConstructUkraine_AdvancedAirBase",),
    "TurkeyDozerCommandSet": ("Command_ConstructTurkey_AdvancedAirBase",),
    "LibyaDozerCommandSet": ("Command_ConstructLibya_AdvancedAirBase",),
    "SouthAfricaDozerCommandSet": ("Command_ConstructSouthAfrica_AdvancedAirBase",),
    "SouthKorea_VT72BCommandSet": ("Command_ConstructSouthKorea_AdvancedAirBase",),
    "Japan_VT72BCommandSet": ("Command_ConstructJapan_AdvancedAirBase",),
    "Vietnam_VT72BCommandSet": ("Command_ConstructVietnam_AdvancedAirBase",),
    "Egypt_WorkerCommandSet": ("Command_ConstructEgypt_AdvancedAirBase",),
    "EgyptDozerCommandSet": ("Command_ConstructEgypt_AdvancedAirBase",),
    "GLAWorkerCommandSet": ("Command_ConstructGLA_AdvancedAirBase",),
    "GLAWorkerCommandSetg": ("Command_ConstructGLA_AdvancedAirBase",),
}

# AAB object CommandSet -> PR482 production sources to merge
AAB_PRODUCTION_SOURCES = {
    "America_AdvancedAirBaseCommandSet": ("America_LargeAirBaseCommandSet", "America_HeavyAirBaseCommandSet"),
    "China_AdvancedAirBaseCommandSet": ("China_LargeAirBaseCommandSet", "China_HeavyAirBaseCommandSet"),
    "Russia_AdvancedAirBaseCommandSet": ("Russia_LargeAirBaseCommandSet", "Russia_HeavyAirBaseCommandSet"),
    "Iran_AdvancedAirBaseCommandSet": ("Iran_LargeAirBaseCommandSet", "Iran_HeavyAirBaseCommandSet"),
    "Iraq_AdvancedAirBaseCommandSet": ("Iraq_LargeAirBaseCommandSet", "Iraq_HeavyAirBaseCommandSet"),
    "Nato_AdvancedAirBaseCommandSet": ("Nato_LargeAirBaseCommandSet", "Nato_HeavyAirBaseCommandSet"),
    "GLA_AdvancedAirBaseCommandSet": ("ArabicAirfieldCommandSet", "ArabicAirfield_TCommandSet"),
    "AirF_AmericaAdvancedAirBaseCommandSet": ("AirF_AmericaAirfieldCommandSet", "Israel_HeavyAirBaseCommandSet", "Israel_LargeAirBaseCommandSet"),
    "Israel_AdvancedAirBaseCommandSet": ("Israel_LargeAirBaseCommandSet", "Israel_HeavyAirBaseCommandSet", "AirF_AmericaAirfieldCommandSet"),
    "Egypt_AdvancedAirBaseCommandSet": ("Egypt_AirfieldCommandSet",),
    "France_AdvancedAirBaseCommandSet": ("France_LargeAirBaseCommandSet", "France_HeavyAirBaseCommandSet", "France_AirfieldCommandSet"),
    "Germany_AdvancedAirBaseCommandSet": ("Germany_LargeAirBaseCommandSet", "Germany_HeavyAirBaseCommandSet"),
    "Britain_AdvancedAirBaseCommandSet": ("Britain_LargeAirBaseCommandSet", "Britain_HeavyAirBaseCommandSet"),
    "Italy_AdvancedAirBaseCommandSet": ("Italy_LargeAirBaseCommandSet", "Italy_HeavyAirBaseCommandSet"),
    "Sweden_AdvancedAirBaseCommandSet": ("Sweden_LargeAirBaseCommandSet", "Sweden_HeavyAirBaseCommandSet"),
    "Ukraine_AdvancedAirBaseCommandSet": ("Ukraine_LargeAirBaseCommandSet", "Ukraine_HeavyAirBaseCommandSet"),
    "Turkey_AdvancedAirBaseCommandSet": ("Turkey_LargeAirBaseCommandSet", "Turkey_HeavyAirBaseCommandSet"),
    "India_AdvancedAirBaseCommandSet": ("India_LargeAirBaseCommandSet", "India_HeavyAirBaseCommandSet"),
    "Pakistan_AdvancedAirBaseCommandSet": ("Pakistan_LargeAirBaseCommandSet", "Pakistan_HeavyAirBaseCommandSet"),
    "SaudiArabia_AdvancedAirBaseCommandSet": ("SaudiArabia_LargeAirBaseCommandSet", "SaudiArabia_HeavyAirBaseCommandSet"),
    "UAE_AdvancedAirBaseCommandSet": ("UAE_LargeAirBaseCommandSet", "UAE_HeavyAirBaseCommandSet"),
    "Syria_AdvancedAirBaseCommandSet": ("Syria_LargeAirBaseCommandSet", "Syria_HeavyAirBaseCommandSet"),
    "Libya_AdvancedAirBaseCommandSet": ("Libya_LargeAirBaseCommandSet", "Libya_HeavyAirBaseCommandSet"),
    "SouthAfrica_AdvancedAirBaseCommandSet": ("SouthAfrica_LargeAirBaseCommandSet", "SouthAfrica_HeavyAirBaseCommandSet"),
    "SouthKorea_AdvancedAirBaseCommandSet": ("SouthKorea_LargeAirBaseCommandSet", "SouthKorea_HeavyAirBaseCommandSet"),
    "Japan_AdvancedAirBaseCommandSet": ("Japan_LargeAirBaseCommandSet", "Japan_HeavyAirBaseCommandSet"),
    "NorthKorea_AdvancedAirBaseCommandSet": ("NorthKorea_LargeAirBaseCommandSet", "NorthKorea_HeavyAirBaseCommandSet"),
    "Vietnam_AdvancedAirBaseCommandSet": ("Vietnam_LargeAirBaseCommandSet", "Vietnam_HeavyAirBaseCommandSet"),
    "Taiwan_AdvancedAirBaseCommandSet": ("Taiwan_AirfieldCommandSet",),
    "UN_AdvancedAirBaseCommandSet": ("UN_AirfieldCommandSet",),
}

UNIT_SLOT_ORDER = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def parse_big(path: Path):
    src = path.read_bytes()
    n = int.from_bytes(src[8:12], "big")
    off = 16
    entries = []
    for _ in range(n):
        eoff = int.from_bytes(src[off : off + 4], "big")
        esz = int.from_bytes(src[off + 4 : off + 8], "big")
        off += 8
        z = src.index(b"\x00", off)
        name = src[off:z].decode("latin-1")
        off = z + 1
        entries.append(name)
    return entries


def parse_commandsets(root: Path) -> dict[str, dict[int, str]]:
    files = sorted(root.glob("Data/INI/CommandSet*.ini"))
    result: dict[str, dict[int, str]] = {}
    cs_re = re.compile(r"^CommandSet\s+(\S+)\s*$")
    slot_re = re.compile(r"^(\s*)(\d+)\s*=\s*(\S+)")
    for p in files:
        text = p.read_text(encoding="latin-1", errors="replace")
        cur = None
        slots: dict[int, str] = {}
        for line in text.splitlines():
            raw = line.split(";", 1)[0].rstrip()
            m = cs_re.match(raw)
            if m:
                if cur is not None:
                    result[cur] = slots
                cur = m.group(1)
                slots = {}
                continue
            if raw.strip() == "End" and cur is not None:
                result[cur] = slots
                cur = None
                slots = {}
                continue
            sm = slot_re.match(raw)
            if sm and cur is not None:
                slots[int(sm.group(2))] = sm.group(3)
        if cur is not None:
            result[cur] = slots
    return result


def format_commandset(name: str, slots: dict[int, str]) -> str:
    lines = [f"CommandSet {name}"]
    for k in sorted(slots):
        lines.append(f"  {k} = {slots[k]}")
    lines.append("End")
    lines.append("")
    return "\n".join(lines)


def copy_stage():
    if STAGE.exists():
        shutil.rmtree(STAGE)
    shutil.copytree(PR, STAGE, symlinks=True)


def collect_old_aab_files() -> list[tuple[Path, Path]]:
    """Return (src, dest_relative) pairs from OLD."""
    pairs = []
    # object files
    for p in OLD.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(OLD)
        name = p.name.lower()
        path_s = str(rel).replace("\\", "/")
        if "AdvancedAirBase" in p.name or "AdvancedAirBase" in path_s:
            if path_s.endswith(".z01"):
                continue
            # Aircraft overlays are old gameplay, not airbase infrastructure.
            if "Aircraft_AAB_" in p.name:
                continue
            dest = STUB_PATH_MAP.get(rel, rel)
            pairs.append((p, dest))
    extras = [
        Path("Data/INI/CommandButton_AdvancedAirBase_SpecterFactions.ini"),
        Path("Data/INI/MappedImages/HandCreated/AdvancedAirBase_Images.INI"),
        Path("Data/English/AdvancedAirBase_Strings.txt"),
        Path("Data/INI/Object/Specter/PatchSystems/AdvancedAirBase/RUNWAY_SYSTEM.txt"),
    ]
    for rel in extras:
        src = OLD / rel
        if src.is_file():
            pairs.append((src, rel))
    # Israel construct button lives in AirForceFinal in OLD; add it locally later
    return pairs


def ensure_israel_button(text: str) -> str:
    if "Command_ConstructIsrael_AdvancedAirBase" in text:
        return text
    extra = """
CommandButton Command_ConstructIsrael_AdvancedAirBase
  Command       = DOZER_CONSTRUCT
  Object        = Israel_AdvancedAirBase
  TextLabel     = CONTROLBAR:ConstructPatch_AdvancedAirBase
  ButtonImage   = Patch_AdvancedAirBase
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipPatchBuildAdvancedAirBase
End
"""
    return text.rstrip() + "\n" + extra


def replace_airbase_construct(slots: dict[int, str], new_btn: str) -> dict[int, str]:
    out = dict(slots)
    replaced = False
    to_del = []
    for k, v in out.items():
        if re.search(r"(Large|Heavy)AirBase", v):
            if not replaced:
                out[k] = new_btn
                replaced = True
            else:
                to_del.append(k)
    for k in to_del:
        del out[k]
    if not replaced:
        used = set(out)
        for slot in UNIT_SLOT_ORDER + [5, 6, 12, 15, 16]:
            if slot not in used:
                out[slot] = new_btn
                break
        else:
            out[max(used, default=0) + 1] = new_btn
    return out


def merge_production(sets: dict[str, dict[int, str]], sources: tuple[str, ...]) -> dict[int, str]:
    buttons: list[str] = []
    seen = set()
    rally = "Command_SetRallyPoint"
    sell = "Command_Sell"
    for src in sources:
        slots = sets.get(src) or {}
        for k in sorted(slots):
            btn = slots[k]
            if btn in (rally, sell):
                continue
            if btn in seen:
                continue
            seen.add(btn)
            buttons.append(btn)
    out: dict[int, str] = {}
    for i, btn in enumerate(buttons):
        if i >= len(UNIT_SLOT_ORDER):
            break
        out[UNIT_SLOT_ORDER[i]] = btn
    out[13] = rally
    out[14] = sell
    return out


def write_overlay(sets: dict[str, dict[int, str]]) -> str:
    chunks = [
        "; PR #482 last-win overlay - restore OLD AdvancedAirBase construct + production.",
        "; Builder CommandSets keep every PR #482 non-airbase slot.",
        "; LargeAirBase/HeavyAirBase construct buttons are replaced with AAB.",
        "; Production CommandSets merge PR #482 Large+Heavy aircraft buttons.",
        "",
    ]
    for name, btns in BUILDER_AAB_WIRE.items():
        if name not in sets:
            # synthesize GLAWorkerCommandSet from the g variant if needed
            if name == "GLAWorkerCommandSet" and "GLAWorkerCommandSetg" in sets:
                base = dict(sets["GLAWorkerCommandSetg"])
            else:
                continue
        else:
            base = dict(sets[name])
        new_slots = replace_airbase_construct(base, btns[0])
        chunks.append(format_commandset(name, new_slots))
        sets[name] = new_slots
    for aab_set, sources in AAB_PRODUCTION_SOURCES.items():
        merged = merge_production(sets, sources)
        if len(merged) <= 2:
            # no aircraft found; still emit Rally/Sell so the building is valid
            pass
        chunks.append(format_commandset(aab_set, merged))
    return "\n".join(chunks) + "\n"


def apply_restore() -> dict:
    copy_stage()
    added = []
    changed = []
    pairs = collect_old_aab_files()
    # skip CommandSet_AdvancedAirBase.ini (Patch aircraft / PatchAAB dozers)
    pairs = [(s, d) for s, d in pairs if s.name != "CommandSet_AdvancedAirBase.ini"]
    pairs = [(s, d) for s, d in pairs if s.name != "CommandButton_AdvancedAirBase_Aircraft.ini"]
    for src, dest_rel in pairs:
        dest = STAGE / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = src.read_bytes()
        if dest_rel.name == "CommandButton_AdvancedAirBase_SpecterFactions.ini":
            text = ensure_israel_button(data.decode("latin-1"))
            data = text.encode("latin-1")
        existed = dest.is_file()
        if existed and dest.read_bytes() == data:
            continue
        dest.write_bytes(data)
        packed = PACKED(dest_rel)
        if existed:
            changed.append((packed, "OLD_SPEC", "Overwrite stub/disabled AdvancedAirBase with OLD object"))
        else:
            added.append((packed, "OLD_SPEC", "Restore OLD custom AdvancedAirBase infrastructure"))

    sets = parse_commandsets(STAGE)
    overlay = write_overlay(sets)
    overlay_rel = Path("Data/INI/CommandSet_ZZZZ_RestoreAdvancedAirBase.ini")
    overlay_path = STAGE / overlay_rel
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_path.write_text(overlay, encoding="latin-1")
    added.append((PACKED(overlay_rel), "PR482+OLD_SPEC", "Last-win builder wiring + AAB production from PR482 aircraft"))

    # sanity: do not touch protected Egypt files
    protected = [
        "Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini",
        "Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_WarFactory.ini",
        "Data/INI/Object/Specter/Egyptian Armed Forces/Infantry/Egypt_Worker.ini",
        "Data/INI/PlayerTemplate.ini",
    ]
    for rel in protected:
        a = (PR / rel).read_bytes()
        b = (STAGE / rel).read_bytes()
        assert a == b, f"protected file changed: {rel}"

    return {"added": added, "changed": changed, "sets": sets}


def pack_big(stage: Path, order: list[str], out: Path) -> str:
    blobs = []
    for name in order:
        p = stage / name.replace("\\", "/")
        if not p.is_file():
            raise SystemExit(f"missing staged file: {name}")
        blobs.append((name, p.read_bytes()))
    header_size = 16
    for name, _ in blobs:
        header_size += 8 + len(name.encode("latin-1")) + 1
    offset = header_size
    index = []
    for name, content in blobs:
        index.append((name, offset, len(content)))
        offset += len(content)
    out_bytes = bytearray()
    out_bytes += b"BIGF"
    out_bytes += struct.pack(">I", offset)
    out_bytes += struct.pack(">I", len(blobs))
    out_bytes += struct.pack(">I", header_size)
    for name, off, size in index:
        out_bytes += struct.pack(">II", off, size)
        out_bytes += name.encode("latin-1") + b"\x00"
    for _, content in blobs:
        out_bytes += content
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(out_bytes))
    return sha256_bytes(bytes(out_bytes))


def main():
    info = apply_restore()
    pr_order = parse_big(Path("/tmp/PR482_BASELINE/_SPEC_DATA_ONE.big"))
    stage_files = {PACKED(p.relative_to(STAGE)) for p in STAGE.rglob("*") if p.is_file()}
    # keep PR482 order for existing paths; append new paths
    new_order = [n for n in pr_order if n in stage_files]
    extras = sorted(stage_files - set(new_order))
    new_order.extend(extras)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_big = OUT_DIR / "_SPEC_DATA_ONE.big"
    digest = pack_big(STAGE, new_order, out_big)
    report = []
    report.append(f"NEW_DATA_BYTES = {out_big.stat().st_size}")
    report.append(f"NEW_DATA_SHA256 = {digest}")
    report.append(f"NEW_DATA_FILE_COUNT = {len(new_order)}")
    report.append(f"ADDED_PATH_COUNT = {len(info['added'])}")
    report.append(f"CONTENT_CHANGED_PATH_COUNT = {len(info['changed'])}")
    report.append("ADDED:")
    for p, src, why in info["added"]:
        report.append(f"  {p} | SOURCE={src} | {why}")
    report.append("CHANGED:")
    for p, src, why in info["changed"]:
        report.append(f"  {p} | SOURCE={src} | {why}")
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report[:40]))
    print("...")
    print(f"wrote {out_big} {out_big.stat().st_size} {digest}")
    print(f"added={len(info['added'])} changed={len(info['changed'])} extras={len(extras)}")


if __name__ == "__main__":
    main()
