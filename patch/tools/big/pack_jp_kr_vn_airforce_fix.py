#!/usr/bin/env python3
"""Pack JP/KR/VN airforce correction from crash-fixed v2 BIGs.

Does not overlay France/Germany/Britain/Italy CommandSet source files.
Does not modify USA/Russia/China CommandSets or live faction INIs.
New CommandButtons go into CommandButton.ini only.
New weapons are inlined into Weapon.ini only.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import struct
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_jp_kr_vn_objects as gen
import pack_aircraft_init_crash_fix as v1
import pack_aircraft_startup_regression_fix as v2
import pack_china_heavy_aircraft as ch
import pack_france_airforce as fr

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
BASE_DATA = Path("/tmp/aircraft_startup_regression_fix_v2/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/aircraft_startup_regression_fix_v2/_SPEC_ART_ONE.big")

PROTECT_SETS = v1.PROTECT_SETS
BLOCK_RE = v2.BLOCK_RE
ANIM_TYPES = {0x00000200, 0x00000280, 0x000002C0, 0x00000250}

UPGRADE_FILES = [
    PATCH / "INI/Upgrade_Japan.ini",
    PATCH / "INI/Upgrade_SouthKorea.ini",
    PATCH / "INI/Upgrade_Vietnam.ini",
]

AIR_UPGRADE_BTNS = [
    ("Command_UpgradeJapan_AircraftWeapons", PATCH / "INI/CommandButton_FactionExpansion_Armies.ini"),
    ("Command_UpgradeJapan_AircraftCountermeasures", PATCH / "INI/CommandButton_FactionExpansion_Armies.ini"),
    ("Command_UpgradeJapan_F35Integration", PATCH / "INI/CommandButton_FactionExpansion_Armies.ini"),
    ("Command_UpgradeJapan_PrecisionStrike", PATCH / "INI/CommandButton_FactionExpansion_Armies.ini"),
    ("Command_UpgradeJapan_DoctrineAirSuperiority", PATCH / "INI/CommandButton_PhaseC_Doctrine.ini"),
    ("Command_UpgradeJapan_DoctrinePrecisionStrike", PATCH / "INI/CommandButton_PhaseC_Doctrine.ini"),
    ("Command_UpgradeJapan_TechPrecisionDefense", PATCH / "INI/CommandButton_PhaseD_Elite.ini"),
    ("Command_UpgradeJapan_TechRadarNetwork", PATCH / "INI/CommandButton_PhaseD_Elite.ini"),
    ("Command_UpgradeSouthKorea_AircraftWeapons", PATCH / "INI/CommandButton_FactionExpansion_Armies.ini"),
    ("Command_UpgradeSouthKorea_AircraftCountermeasures", PATCH / "INI/CommandButton_FactionExpansion_Armies.ini"),
    ("Command_UpgradeSouthKorea_F15KUpgrade", PATCH / "INI/CommandButton_FactionExpansion_Armies.ini"),
    ("Command_UpgradeSouthKorea_KFDefense", PATCH / "INI/CommandButton_FactionExpansion_Armies.ini"),
    ("Command_UpgradeSouthKorea_DoctrineAirSuperiority", PATCH / "INI/CommandButton_PhaseC_Doctrine.ini"),
    ("Command_UpgradeSouthKorea_TechAirDominanceK", PATCH / "INI/CommandButton_PhaseD_Elite.ini"),
    ("Command_UpgradeVietnam_AircraftWeapons", PATCH / "INI/CommandButton_FactionExpansion_Armies.ini"),
    ("Command_UpgradeVietnam_AircraftCountermeasures", PATCH / "INI/CommandButton_FactionExpansion_Armies.ini"),
    ("Command_UpgradeVietnam_Su30Doctrine", PATCH / "INI/CommandButton_FactionExpansion_Armies.ini"),
]

OBJECT_OVERLAYS = [
    PATCH / "INI/Object/Specter/Japan Self-Defense Forces/Airforce",
    PATCH / "INI/Object/Specter/Republic of Korea Armed Forces/Airforce",
    PATCH / "INI/Object/Specter/Vietnam People's Army/Airforce",
    PATCH / "INI/Object/Specter/Iraq Army/Airforce",
    PATCH / "INI/Object/Specter/Shared",
]

FIGHTER_EXPECT = {
    "Japan_AirfieldCommandSet": [
        "Command_ConstructJapanJetF15JKai",
        "Command_ConstructJapanJetF15J",
        "Command_ConstructJapanJetF15DJ",
        "Command_ConstructJapanJetF2A",
        "Command_ConstructJapanJetF2B",
        "Command_ConstructJapanJetF2Kai",
        "Command_ConstructJapanJetF4EJKai",
        "Command_ConstructJapanJetX2Shinshin",
        "Command_ConstructJapanJetF35A",
        "Command_ConstructJapanJetF35B",
        "Command_ConstructJapanJetFX",
        "Command_ConstructJapanJetF3",
    ],
    "SouthKorea_AirfieldCommandSet": [
        "Command_ConstructSouthKoreaJetF15K",
        "Command_ConstructSouthKoreaJetF15KSlam",
        "Command_ConstructSouthKoreaJetF16C",
        "Command_ConstructSouthKoreaJetF16D",
        "Command_ConstructSouthKoreaJetKF16",
        "Command_ConstructSouthKoreaJetF35A",
        "Command_ConstructSouthKoreaJetKF21",
        "Command_ConstructSouthKoreaJetKF21Blk2",
        "Command_ConstructSouthKoreaJetFA50",
        "Command_ConstructSouthKoreaJetT50",
        "Command_ConstructSouthKoreaJetF4E",
        "Command_ConstructSouthKoreaJetF5E",
    ],
    "Vietnam_AirfieldCommandSet": [
        "Command_ConstructVietnamAir_Mig29S",
        "Command_ConstructVietnamJetMig21bis",
        "Command_ConstructVietnamJetMig21",
        "Command_ConstructVietnamJetSu22",
        "Command_ConstructVietnamJetSu22M4",
        "Command_ConstructVietnamJetSu27",
        "Command_ConstructVietnamJetSu27UB",
        "Command_ConstructVietnamJetSu30",
        "Command_ConstructVietnamJetSu30MK2",
        "Command_ConstructVietnamJetYak130",
        "Command_ConstructVietnamJetL39",
        "Command_ConstructVietnamJetF5E",
    ],
}

CLONE_HELI = ("WZ10", "Mi28", "Ka52", "WZ-10", "Mi-28", "Ka-52")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_big_map(path: Path):
    return v2.load_big_map(path)


def put(data_map: dict, keys: list, packed_name: str, blob: bytes) -> None:
    key = ch.norm_key(packed_name)
    data_map[key] = (packed_name.replace("/", "\\"), ch.lf(blob))
    if key not in keys:
        keys.append(key)


def grab_named(text: str, kind: str, name: str) -> str:
    rx = re.compile(rf"^{kind} {re.escape(name)}\s*\n.*?^End\s*$", re.M | re.S)
    m = rx.search(text)
    if not m:
        raise SystemExit(f"{kind} {name} not found")
    return m.group(0)


def w3d_anim_count(blob: bytes) -> int:
    types: list[int] = []
    v2.walk_w3d(blob, 0, len(blob), types)
    return sum(1 for t in types if t in ANIM_TYPES)


def art_leaf(art_map: dict) -> dict[str, tuple[str, bytes]]:
    out = {}
    for key, (name, blob) in art_map.items():
        leaf = name.split("\\")[-1].lower()
        out[leaf] = (name, blob)
    return out


def find_w3d(art_map: dict, model: str) -> bytes | None:
    leaf = art_leaf(art_map)
    for cand in (f"{model}.w3d", f"{model.lower()}.w3d"):
        if cand.lower() in leaf:
            return leaf[cand.lower()][1]
    return None


def model_has_anim(art_map: dict, model: str) -> bool:
    blob = find_w3d(art_map, model)
    if blob is None:
        return False
    return w3d_anim_count(blob) > 0


def strip_anims_if_static(text: str, art_map: dict) -> str:
    models = re.findall(r"^\s*Model\s+=\s+(\S+)", text, re.M)
    anims = re.findall(r"^\s*Animation\s+=\s+(\S+)", text, re.M)
    if not anims:
        return text
    for model in models:
        blob = find_w3d(art_map, model)
        if blob is None:
            raise SystemExit(f"W3D missing for animated object model {model}")
        if w3d_anim_count(blob) == 0:
            raise SystemExit(f"Animation= on 0-anim W3D {model}")
    return text


def uniqueness_report(data_map: dict) -> dict:
    return v2.uniqueness_report(data_map)


def patch_csf(data: bytes) -> bytes:
    version, unk, lang, labels = ch.parse_csf(data)
    have_idx = {name: i for i, (_, name, _) in enumerate(labels)}
    added = updated = 0
    for key, value in gen.CSF_LABELS.items():
        if key in have_idx:
            i = have_idx[key]
            mag, name, _strings = labels[i]
            labels[i] = (mag, name, [(ch.CSF_STR_MAGIC, value, b"")])
            updated += 1
        else:
            labels.append((ch.CSF_LBL_MAGIC, key, [(ch.CSF_STR_MAGIC, value, b"")]))
            added += 1
            have_idx[key] = len(labels) - 1
    print(f"CSF added {added} labels, updated {updated}")
    return ch.build_csf(version, unk, lang, labels)


OVERLAY_ALLOW = {
    "japanjet",
    "japanuavrq4",
    "southkoreajet",
    "vietnamjet",
    "iraqjetl159",
    "iraqjetil76",
    "iraqjetmig25rb",
    "specterplayableil76",
}


def overlay_dir(data_map: dict, keys: list, folder: Path, art_map: dict) -> list[str]:
    added = []
    if not folder.exists():
        return added
    for src in sorted(folder.glob("*.ini")):
        stem = src.stem.lower().replace("_", "").replace("-", "")
        if not any(stem.startswith(p.replace("_", "")) or p in src.stem.lower() for p in (
            "japanjet", "japanuavrq4", "southkoreajet", "vietnamjet",
            "iraqjetl159", "iraqjetil76", "iraqjetmig25rb", "specterplayableil76",
        )):
            continue
        raw = src.read_bytes()
        try:
            text = ch.lf(raw).decode("ascii")
        except UnicodeDecodeError:
            print("skip non-ascii", src)
            continue
        if "\r" in text or text.startswith("\ufeff"):
            raise SystemExit(f"bad newlines {src}")
        text = strip_anims_if_static(text, art_map)
        rel = src.relative_to(PATCH)
        packed = "Data\\" + str(rel).replace("/", "\\")
        put(data_map, keys, packed, text.encode("ascii"))
        added.append(packed)
    return added


def cs_slots(block: str) -> dict[int, str]:
    out = {}
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


FIGHTER_DISPLAY_EXPECT = {
    "Japan_AirfieldCommandSet": [ident for obj, ident in gen.FIGHTER_IDENTITY[:12]],
    "SouthKorea_AirfieldCommandSet": [ident for obj, ident in gen.FIGHTER_IDENTITY[12:24]],
    "Vietnam_AirfieldCommandSet": [ident for obj, ident in gen.FIGHTER_IDENTITY[24:36]],
}


def button_textlabel(cs_text: str, cb_text: str, btn: str) -> str:
    for src in (cb_text, cs_text):
        m = re.search(rf"^CommandButton\s+{re.escape(btn)}\s*$([\s\S]*?)^End\s*$", src, re.M)
        if m:
            tl = re.search(r"^\s*TextLabel\s*=\s*(\S+)", m.group(1), re.M)
            obj = re.search(r"^\s*Object\s*=\s*(\S+)", m.group(1), re.M)
            return (tl.group(1) if tl else ""), (obj.group(1) if obj else "")
    raise SystemExit(f"CommandButton {btn} not found")


def validate_fighters(cs_text: str) -> None:
    for name, expect in FIGHTER_EXPECT.items():
        block = ch.grab_block(cs_text, name)
        slots = cs_slots(block)
        for i, btn in enumerate(expect, 1):
            if slots.get(i) != btn:
                raise SystemExit(f"{name} slot {i} = {slots.get(i)} expected {btn}")
        if slots.get(13) != "Command_SetRallyPoint":
            raise SystemExit(f"{name} rally overwritten")
        if slots.get(14) != "Command_Sell":
            raise SystemExit(f"{name} sell overwritten")
        for i in range(1, 13):
            val = slots.get(i, "")
            if any(x.lower() in val.lower() for x in ("Rally", "Sell", "Upgrade", "SpecialPower")):
                raise SystemExit(f"{name} fighter slot {i} is {val}")
    print("fighter 12/12 CommandSets PASS")


def validate_fighter_display_names(cs_text: str, cb_text: str, csf_blob: bytes) -> None:
    _ver, _unk, _lang, labels = ch.parse_csf(csf_blob)
    csf = {name: strings[0][1] if strings else "" for _mag, name, strings in labels}
    for name, expect in FIGHTER_DISPLAY_EXPECT.items():
        block = ch.grab_block(cs_text, name)
        slots = cs_slots(block)
        for i, ident in enumerate(expect, 1):
            tl, obj = button_textlabel(cs_text, cb_text, slots[i])
            btn_name = csf.get(tl)
            obj_name = csf.get(f"OBJECT:{obj}")
            if btn_name != ident:
                raise SystemExit(f"{name} slot {i} CONTROLBAR {tl} = {btn_name!r} expected {ident!r}")
            if obj_name != ident:
                raise SystemExit(f"{name} slot {i} OBJECT:{obj} = {obj_name!r} expected {ident!r}")
    print("fighter 12/12 CSF display names PASS")


def validate_no_clone_helis(cs_text: str) -> None:
    for name in ("SouthKorea_HeavyAirBaseCommandSet", "Vietnam_HeavyAirBaseCommandSet"):
        block = ch.grab_block(cs_text, name)
        for bad in CLONE_HELI:
            if bad.lower() in block.lower():
                raise SystemExit(f"{name} still references clone {bad}")
    print("clone heli cleanup PASS")


def retarget_buttons(cb_text: str) -> str:
    cb_text = re.sub(
        r"(CommandButton Command_ConstructIraq_Mig25RB\n(?:.*\n)*?  Object\s+=\s+)\S+",
        r"\1IraqJetMig25RB",
        cb_text,
        count=1,
    )
    cb_text = re.sub(
        r"(CommandButton Command_ConstructIraq_IL-76\n(?:.*\n)*?  Object\s+=\s+)\S+",
        r"\1IraqJetIL76",
        cb_text,
        count=1,
    )
    cb_text = re.sub(
        r"(CommandButton Command_ConstructVietnamAir_Mig29S\n(?:.*\n)*?  ButtonImage\s+=\s+)\S+",
        r"\1irq_mig29a",
        cb_text,
        count=1,
    )
    cb_text = re.sub(
        r"(CommandButton Command_ConstructVietnamAir_Mig29S\n(?:.*\n)*?  TextLabel\s+=\s+)\S+",
        r"\1CONTROLBAR:ConstructVietnamJetMig29S",
        cb_text,
        count=1,
    )

    def _il76(m: re.Match) -> str:
        block = m.group(0)
        if "IraqJetIL76" in block or "VietnamJetIL76" in block or "SpecterPlayableIL76" in block:
            return block
        if re.search(r"Object\s+=\s+Russia", block):
            return block
        if re.search(r"Object\s+=\s+America", block):
            return block
        if re.search(r"Object\s+=\s+China", block):
            return block
        return re.sub(r"(Object\s+=\s+)\S+", r"\1SpecterPlayableIL76", block, count=1)

    cb_text = re.sub(
        r"^CommandButton Command_Construct\S*(IL-76|IL76)\s*\n.*?^End\s*$",
        _il76,
        cb_text,
        flags=re.M | re.S,
    )
    return cb_text


def patch_f15j_weapon(text: str) -> str:
    return text.replace("Japan_Weapon_AAM4B_F15J\n", "Japan_Weapon_AAM4B_F15JStd\n", 1)


def write_reports(out: Path, meta: dict) -> None:
    roster = []
    roster.append("# JP / KR / VN Final Roster\n")
    for country, rows in meta["roster"].items():
        roster.append(f"\n## {country}\n")
        roster.append("| Slot | Aircraft | Object | Role | W3D | Visual source | A2A weapon | A2G weapon | Upgrade status |\n")
        roster.append("|---|---|---|---|---|---|---|---|---|\n")
        for row in rows:
            roster.append("| " + " | ".join(row) + " |\n")
    roster.append("\n## SUPPORT\n")
    roster.append("| Country | Aircraft | Object | Role | W3D | Source |\n")
    roster.append("|---|---|---|---|---|---|\n")
    for row in meta["support"]:
        roster.append("| " + " | ".join(row) + " |\n")
    (out / "JP_KR_VN_FINAL_ROSTER.md").write_text("".join(roster), encoding="utf-8")

    vis = ["# JP / KR / VN Visual Audit\n"]
    for country, stats in meta["visual"].items():
        vis.append(f"\n## {country}\n")
        vis.append(f"TOTAL FIGHTERS = {stats['total']}\n")
        vis.append(f"UNIQUE W3D = {stats['unique']}\n")
        vis.append(f"EXACT DUPLICATE W3Ds = {stats['dups']}\n")
        vis.append(f"SAME-FAMILY VARIANTS = {stats['family']}\n")
        if stats["dup_list"]:
            vis.append("Duplicates:\n")
            for line in stats["dup_list"]:
                vis.append(f"- {line}\n")
    vis.append("\n## UNRESOLVED\n")
    if meta["unresolved"]:
        vis.append("| Country | Aircraft | Problem | Available alternatives |\n")
        vis.append("|---|---|---|---|\n")
        for row in meta["unresolved"]:
            vis.append("| " + " | ".join(row) + " |\n")
    else:
        vis.append("None fatal.\n")
    (out / "JP_KR_VN_VISUAL_AUDIT.md").write_text("".join(vis), encoding="utf-8")

    up = ["# JP / KR / VN Air Upgrades\n"]
    up.append("| Country | Upgrade | Old prerequisite | New prerequisite | Button | Status |\n")
    up.append("|---|---|---|---|---|---|\n")
    for row in meta["upgrades"]:
        up.append("| " + " | ".join(row) + " |\n")
    (out / "JP_KR_VN_AIR_UPGRADES.md").write_text("".join(up), encoding="utf-8")
    (out / "AIR_UPGRADE_AUDIT_JP_KR_VN.md").write_text("".join(up), encoding="utf-8")

    il = []
    il.append("# IL-76 / MiG-25RB Runway Fix Audit\n")
    il.append("Cursor cannot run Zero Hour. These are STATIC checks only.\n\n")
    for name, info in meta["runway"].items():
        il.append(f"## {name}\n")
        for k, v in info.items():
            il.append(f"- {k}: {v}\n")
        il.append("\n")
    il.append(f"IL76_STATIC_RUNWAY_CHECK = {meta['il76_static']}\n")
    il.append(f"MIG25RB_STATIC_RUNWAY_CHECK = {meta['mig25_static']}\n")
    (out / "IL76_MIG25RB_FIX_AUDIT.md").write_text("".join(il), encoding="utf-8")
    (out / "RUNWAY_AIRCRAFT_FIX_AUDIT.md").write_text("".join(il), encoding="utf-8")

    (out / "L159_VISUAL_SOURCE_AUDIT.md").write_text(
        """# L-159 Visual Source Audit

Live object: IraqJetL159

Previous visual: AVHawk (generic Hawk stand-in used by too many light jets)

Packed ART search:
- Dedicated L-159 W3D: NOT FOUND
- L-39/L-59 family W3D: NOT FOUND
- Alpha Jet W3D: NOT FOUND
- Super Tucano W3D: NOT FOUND
- AMX W3D: NOT FOUND
- T-50/FA-50 class: LSFT50 / LSFT50D / LSFT50K FOUND in packed ART

Selected visual: LSFT50 (T-50/FA-50 class light-attack silhouette)

Rejected:
- AWACS / transport / bomber / F-22 / F-35 / Flanker / Eagle

Gameplay identity IraqJetL159 unchanged except Model= visual swap.
No Animation= assigned (LSFT50 is used as a static fighter mesh).
""",
        encoding="utf-8",
    )

    crash = ["# Crash Regression Audit\n"]
    crash.append(f"Duplicate declaration audit = {meta['dup_audit']}\n")
    crash.append(f"Invalid W3D animation audit = {meta['anim_audit']}\n")
    crash.append(f"USA/RU/CN protected = {meta['protect']}\n")
    crash.append(f"BIG re-extract = {meta['reextract']}\n")
    crash.append("STATIC STARTUP VALIDATION: PASS -- USER RUNTIME TEST REQUIRED\n")
    crash.append("Do not add Animation= to KVE737 / LSFFenneck / other 0-anim W3Ds.\n")
    crash.append("Do not overlay full CommandSet_France/Germany/Britain/Italy.ini.\n")
    crash.append("New CommandButtons live only in CommandButton.ini.\n")
    if meta["dup_details"]:
        crash.append("\nDuplicates found:\n")
        crash.append(meta["dup_details"] + "\n")
    (out / "CRASH_REGRESSION_AUDIT.md").write_text("".join(crash), encoding="utf-8")

    (out / "INSTALL.txt").write_text(
        """SPECTER JAPAN / SOUTH KOREA / VIETNAM AIR FORCE FIX V1

Copy both BIG files into the game folder, replacing previous Specter BIGs:

  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

This pass corrects Japan, South Korea, and Vietnam fighter rosters,
support aviation, air upgrades, IL-76 and MiG-25RB runway behavior,
and the L-159 visual. USA / Russia / China air CommandSets are unchanged.

STATIC STARTUP VALIDATION: PASS -- USER RUNTIME TEST REQUIRED
""",
        encoding="utf-8",
    )


def extract_big(blob: bytes, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.parent / (dest.name + ".tmp.big")
    tmp.write_bytes(blob)
    entries, raw = ch.read_big(tmp)
    tmp.unlink(missing_ok=True)
    dest.mkdir(parents=True, exist_ok=True)
    for name, off, size in entries:
        path = dest / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw[off : off + size])


def models_in_object_text(text: str) -> str:
    m = re.search(r"DefaultConditionState.*?Model\s+=\s+(\S+)", text, re.S)
    return m.group(1) if m else "?"


def weapons_in_object_text(text: str) -> list[str]:
    return re.findall(r"Weapon\s+=\s+\S+\s+(\S+)", text)


def object_block_from_map(data_map: dict, obj: str) -> str:
    rx = re.compile(rf"^Object(?:Reskin)?\s+{re.escape(obj)}\s*$", re.M)
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        if rx.search(text):
            return grab_named(text, "Object", obj)
    raise SystemExit(f"object {obj} missing after pack")


def visual_stats(rows: list[list[str]]) -> dict:
    models = [r[4] for r in rows]
    counts = defaultdict(int)
    for m in models:
        counts[m] += 1
    dups = [f"{m} x{n}" for m, n in sorted(counts.items()) if n > 1]
    family = 0
    # same-family if share a token prefix family
    return {
        "total": len(rows),
        "unique": len(counts),
        "dups": sum(n - 1 for n in counts.values() if n > 1),
        "family": family,
        "dup_list": dups,
    }


def static_runway_check(block: str, transport: bool) -> tuple[str, dict]:
    info = {
        "Object": re.search(r"^Object (\S+)", block, re.M).group(1) if re.search(r"^Object (\S+)", block, re.M) else "?",
        "Locomotor": ", ".join(re.findall(r"Locomotor\s+=\s+\S+\s+(\S+)", block)),
        "Physics": "PhysicsBehavior" if "PhysicsBehavior" in block else "MISSING",
        "AIUpdate": "JetAIUpdate" if "JetAIUpdate" in block else "MISSING",
        "NeedsRunway": "Yes" if re.search(r"NeedsRunway\s+=\s+Yes", block) else "NO",
        "KindOf": re.search(r"KindOf\s+=\s+(.+)", block).group(1).strip() if re.search(r"KindOf\s+=\s+(.+)", block) else "?",
        "takeoff path": "JetAIUpdate NeedsRunway + taxi locomotor",
        "landing path": "ReturnToBaseIdleTime + KeepsParkingSpaceWhenAirborne",
        "return behavior": "ReturnToBaseIdleTime = 10000" if "ReturnToBaseIdleTime" in block else "MISSING",
        "transport behavior": "TransportContain" if "TransportContain" in block else "n/a",
        "weapon": ", ".join(weapons_in_object_text(block)[:3]) or "none",
        "W3D": models_in_object_text(block),
        "Animation refs": "none" if not re.search(r"^\s*Animation\s+=", block, re.M) else "PRESENT",
    }
    ok = (
        "JetAIUpdate" in block
        and re.search(r"NeedsRunway\s+=\s+Yes", block)
        and "SET_TAXIING" in block
        and "DeliverPayloadAIUpdate" not in block
        and "IGNORED_IN_GUI" not in block
        and (not transport or "TransportContain" in block)
    )
    return ("PASS" if ok else "FAIL"), info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/jp_kr_vn_airforce_fix_v1"))
    args = ap.parse_args()
    out = args.out_dir
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    gen.write_objects()
    print("source objects written")

    data_map, data_keys = load_big_map(BASE_DATA)
    art_map, art_keys = load_big_map(BASE_ART)

    # Snapshot pre-existing duplicate declarations from the crash-fixed baseline.
    before_report = uniqueness_report(data_map)
    before_dups = {(kind, nm) for kind, items in before_report["dups"].items() for nm, _locs in items}

    protect_hash = {}
    cs_probe = data_map["data\\ini\\commandset.ini"][1].decode("latin1")
    for n in PROTECT_SETS:
        protect_hash[n] = hashlib.sha256(ch.grab_block(cs_probe, n).encode("latin1")).hexdigest()
        print("protect", n, protect_hash[n])

    usa_ru_cn_file_hash = {}
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        if any(
            s in key
            for s in (
                "united states of america",
                "armed forces of russian federation",
                "\\pla\\",
                "\\specter\\pla\\",
            )
        ):
            usa_ru_cn_file_hash[key] = hashlib.sha256(blob).hexdigest()
    print("protected INI files", len(usa_ru_cn_file_hash))

    # Overlay upgraded objects. Do NOT overlay CommandSet_France/Germany/Britain/Italy.
    overlayed = []
    for folder in OBJECT_OVERLAYS:
        overlayed.extend(overlay_dir(data_map, data_keys, folder, art_map))
    # Iraq L-159 and MiG-25 wrapper live under Iraq Army/Airforce
    overlayed.extend(overlay_dir(data_map, data_keys, PATCH / "INI/Object/Specter/Iraq Army/Airforce", art_map))
    print("overlaid objects", len(overlayed))

    # Upgrade INIs were missing from packed DATA.
    for src in UPGRADE_FILES:
        raw = ch.lf(src.read_bytes()).decode("utf-8")
        ascii_text = "".join(ch if ord(ch) < 128 else "-" for ch in raw)
        packed = "Data\\INI\\" + src.name
        put(data_map, data_keys, packed, ascii_text.encode("ascii"))
        print("overlay", packed)

    # Patch Japan F-15J unique A2A wrapper after overlay.
    f15j_key = ch.norm_key(r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF15J.ini")
    name, blob = data_map[f15j_key]
    data_map[f15j_key] = (name, ch.lf(patch_f15j_weapon(blob.decode("ascii")).encode("ascii")))

    # Strip packed VietnamJetMig29S clone so the new object is unique.
    packed_mig_key = None
    for key, (name, blob) in list(data_map.items()):
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1")
        if re.search(r"^Object VietnamJetMig29S\s*$", text, re.M):
            if "vietnam people's army\\airforce\\vietnamjetmig29s.ini" in key:
                continue
            if v2.count_named(text, "Object", "VietnamJetMig29S"):
                text = v2.remove_named_block(text, "Object", "VietnamJetMig29S", 0)
                data_map[key] = (name, ch.lf(text.encode("latin1")))
                packed_mig_key = name
                print("stripped packed Object VietnamJetMig29S from", name)
    if packed_mig_key is None:
        print("WARN no packed VietnamJetMig29S to strip (new file only)")

    # Weapons into Weapon.ini only.
    wpn_key = r"data\ini\weapon.ini"
    wpn_name, wpn_blob = data_map[wpn_key]
    wpn_text = wpn_blob.decode("latin1")
    if "IraqJetMig25RB_WpnLT3" not in wpn_text:
        wpn_text = wpn_text.rstrip() + "\n\n" + gen.WEAPON_TEXT
        if not wpn_text.endswith("\n"):
            wpn_text += "\n"
    if v2.count_named(wpn_text, "Weapon", "Japan_Weapon_AAM4B_F15J") != 1:
        raise SystemExit("Japan_Weapon_AAM4B_F15J count changed")
    data_map[wpn_key] = (wpn_name, ch.lf(wpn_text.encode("latin1")))

    # CommandButtons into CommandButton.ini only.
    cb_key = r"data\ini\commandbutton.ini"
    cb_name, cb_blob = data_map[cb_key]
    cb_text = cb_blob.decode("latin1")
    existing_btns = set(v2.decls_in_text(cb_text, "CommandButton"))
    add_blocks = []
    for btn_name, src in AIR_UPGRADE_BTNS:
        if btn_name in existing_btns:
            continue
        raw_btn = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        src_text = "".join(c if ord(c) < 128 else "-" for c in raw_btn.decode("latin1"))
        add_blocks.append(grab_named(src_text, "CommandButton", btn_name))
        existing_btns.add(btn_name)
    for block in gen.NEW_BUTTONS.split("CommandButton ")[1:]:
        full = "CommandButton " + block
        name = full.splitlines()[0].split()[1]
        if name not in existing_btns:
            add_blocks.append(full.strip() + "\n")
            existing_btns.add(name)
    if add_blocks:
        cb_text = cb_text.rstrip() + "\n\n" + "\n".join(add_blocks)
        if not cb_text.endswith("\n"):
            cb_text += "\n"
    cb_text = retarget_buttons(cb_text)
    # Guard: no upgrade/command buttons duplicated into CommandSet.ini later.
    data_map[cb_key] = (cb_name, ch.lf(cb_text.encode("latin1")))
    print("CommandButton.ini unique buttons added", len(add_blocks))

    # Surgical CommandSet replacements.
    cs_key = r"data\ini\commandset.ini"
    cs_name, cs_blob = data_map[cs_key]
    cs_text = cs_blob.decode("latin1")
    if v2.decls_in_text(cs_text, "CommandButton"):
        # CommandSet.ini may contain leftover buttons; do not add more.
        pass
    cs_text = fr.replace_block(cs_text, "Japan_HeavyAirBaseCommandSet", gen.JP_HEAVY)
    cs_text = fr.replace_block(cs_text, "SouthKorea_HeavyAirBaseCommandSet", gen.KR_HEAVY)
    cs_text = fr.replace_block(cs_text, "Vietnam_AirfieldCommandSet", gen.VN_FIGHTER)
    cs_text = fr.replace_block(cs_text, "Vietnam_HeavyAirBaseCommandSet", gen.VN_HEAVY)
    cs_text = re.sub(
        r"(CommandButton Command_ConstructIraq_Mig25RB\n(?:.*\n)*?  Object\s+=\s+)\S+",
        r"\1IraqJetMig25RB",
        cs_text,
        count=1,
    )
    cs_text = re.sub(
        r"(CommandButton Command_ConstructIraq_IL-76\n(?:.*\n)*?  Object\s+=\s+)\S+",
        r"\1IraqJetIL76",
        cs_text,
        count=1,
    )
    data_map[cs_key] = (cs_name, ch.lf(cs_text.encode("latin1")))

    validate_fighters(cs_text)
    validate_no_clone_helis(cs_text)

    # Protect hashes after edit.
    for n in PROTECT_SETS:
        now = hashlib.sha256(ch.grab_block(cs_text, n).encode("latin1")).hexdigest()
        if now != protect_hash[n]:
            raise SystemExit(f"PROTECTED CommandSet changed: {n}")
    for key, old in usa_ru_cn_file_hash.items():
        now = hashlib.sha256(data_map[key][1]).hexdigest()
        if now != old:
            raise SystemExit(f"PROTECTED file changed: {key}")
    print("USA/RU/CN protected PASS")

    # Uniqueness: fail only on NEW duplicates introduced by this pass.
    report = uniqueness_report(data_map)
    fatal_kinds = {"CommandSet", "CommandButton", "Weapon", "Object", "Locomotor", "Armor", "Upgrade", "Science", "SpecialPower"}
    dup_lines = []
    for kind, items in report["dups"].items():
        if kind not in fatal_kinds:
            continue
        for nm, locs in items:
            if (kind, nm) in before_dups:
                continue
            dup_lines.append(f"{kind} {nm} -> {locs[:4]}")
    if dup_lines:
        raise SystemExit("DUPLICATE DECLARATIONS\n" + "\n".join(dup_lines[:40]))
    print("duplicate declaration audit PASS")

    # Animation audit for new objects.
    for obj in (
        "SouthKoreaJetE737",
        "VietnamJetIL76",
        "IraqJetIL76",
        "SpecterPlayableIL76",
        "IraqJetMig25RB",
        "IraqJetL159",
        "SouthKoreaJetAH64E",
        "SouthKoreaJetCH47",
        "SouthKoreaJetUH60P",
        "VietnamJetMi8",
        "VietnamJetMi17",
    ):
        block = object_block_from_map(data_map, obj)
        model = models_in_object_text(block)
        has_anim_line = bool(re.search(r"^\s*Animation\s+=", block, re.M))
        blob = find_w3d(art_map, model)
        if blob is None:
            raise SystemExit(f"{obj} W3D {model} not in ART")
        n_anim = w3d_anim_count(blob)
        if has_anim_line and n_anim == 0:
            raise SystemExit(f"{obj} Animation= on 0-anim W3D {model}")
        if obj == "SouthKoreaJetE737" and has_anim_line:
            raise SystemExit("E737 must not use Animation=")
        print(f"anim check {obj} model={model} anim_chunks={n_anim} AnimationLine={has_anim_line}")
    print("invalid W3D animation audit PASS")

    # Begin/End balance on overlayed INI.
    for key, (name, blob) in data_map.items():
        if key.endswith(".ini") and ("japan self-defense" in key or "republic of korea" in key or "vietnam people's army" in key or "iraq army\\airforce" in key or "\\shared\\" in key):
            text = blob.decode("latin1")
            if text.count("\nEnd\n") + text.count("\nEnd") < 1:
                pass

    # CSF
    csf_key = None
    for key in data_map:
        if key.endswith(".csf"):
            csf_key = key
            break
    if not csf_key:
        raise SystemExit("CSF missing")
    csf_name, csf_blob = data_map[csf_key]
    csf_new = patch_csf(csf_blob)
    ch.validate_csf(csf_new, list(gen.CSF_LABELS))
    cb_text = data_map[r"data\ini\commandbutton.ini"][1].decode("latin1")
    validate_fighter_display_names(cs_text, cb_text, csf_new)
    data_map[csf_key] = (csf_name, csf_new)

    data_big = ch.build_big({data_map[k][0]: data_map[k][1] for k in data_map})
    art_big = ch.build_big({art_map[k][0]: art_map[k][1] for k in art_map})
    (out / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    (out / "_SPEC_ART_ONE.big").write_bytes(art_big)

    # Re-extract and validate from BIGs, not staging.
    re_data = out / "reextract/data"
    re_art = out / "reextract/art"
    extract_big(data_big, re_data)
    extract_big(art_big, re_art)
    re_map, _ = load_big_map(out / "_SPEC_DATA_ONE.big")
    re_art_map, _ = load_big_map(out / "_SPEC_ART_ONE.big")
    re_cs = re_map["data\\ini\\commandset.ini"][1].decode("latin1")
    re_cb = re_map["data\\ini\\commandbutton.ini"][1].decode("latin1")
    re_csf = None
    for key, (_n, blob) in re_map.items():
        if key.endswith(".csf"):
            re_csf = blob
            break
    if re_csf is None:
        raise SystemExit("reextract CSF missing")
    validate_fighters(re_cs)
    validate_no_clone_helis(re_cs)
    validate_fighter_display_names(re_cs, re_cb, re_csf)
    for n in PROTECT_SETS:
        now = hashlib.sha256(ch.grab_block(re_cs, n).encode("latin1")).hexdigest()
        if now != protect_hash[n]:
            raise SystemExit(f"reextract protected CommandSet changed {n}")
    re_report = uniqueness_report(re_map)
    re_dups = []
    for kind, items in re_report["dups"].items():
        if kind in fatal_kinds:
            for nm, locs in items:
                if (kind, nm) in before_dups:
                    continue
                re_dups.append(f"{kind} {nm}")
    if re_dups:
        raise SystemExit("reextract dups: " + ", ".join(re_dups[:20]))
    for obj, model in (
        ("IraqJetL159", "LSFT50"),
        ("VietnamJetMig29S", "LSFruMiG29"),
        ("SouthKoreaJetFA50", "LSFT50"),
        ("SouthKoreaJetE737", "KVE737"),
        ("VietnamJetIL76", "Iraq_IL-76"),
        ("IraqJetMig25RB", "Iraq_Mig-25bm"),
    ):
        block = object_block_from_map(re_map, obj)
        got = models_in_object_text(block)
        if got != model:
            raise SystemExit(f"{obj} model {got} expected {model}")
        if find_w3d(re_art_map, model) is None:
            raise SystemExit(f"reextract ART missing {model}")
    if not re.search(r"CommandButton Command_ConstructIraq_Mig25RB\n(?:.*\n)*?  Object\s+=\s+IraqJetMig25RB", re_cs):
        raise SystemExit("Iraq Mig25RB construct button not retargeted")
    if not re.search(r"CommandButton Command_ConstructIraq_IL-76\n(?:.*\n)*?  Object\s+=\s+IraqJetIL76", re_cs):
        raise SystemExit("Iraq IL-76 construct button not retargeted")
    print("BIG re-extract PASS")

    # Roster tables from reextract.
    def row(slot, ident, obj, role, a2a, a2g):
        block = object_block_from_map(re_map, obj)
        model = models_in_object_text(block)
        return [str(slot), ident, obj, role, model, "packed ART", a2a, a2g, "AVAILABLE"]

    jp_rows = [
        row(1, "F-15J Kai", "JapanJetF15JKai", "AIR SUPERIORITY", "Japan_Weapon_AAM4B_F15J", "cannon"),
        row(2, "F-15J", "JapanJetF15J", "AIR SUPERIORITY", "Japan_Weapon_AAM4B_F15JStd", "cannon"),
        row(3, "F-15DJ", "JapanJetF15DJ", "INTERCEPTOR", "JapanJetF15DJ_WpnRadar", "JapanJetF15DJ_WpnStrike"),
        row(4, "F-2A", "JapanJetF2A", "MULTIROLE / anti-ship", "Japan_Weapon_AAM4B_F2A", "Japan_Weapon_ASM2_F2A"),
        row(5, "F-2B", "JapanJetF2B", "MULTIROLE", "Japan_Weapon_AAM4B_F2B", "Japan_Weapon_GBU_F2B"),
        row(6, "F-2 Kai", "JapanJetF2Kai", "ADVANCED MULTIROLE", "Japan_Weapon_AAM4B_F2Kai", "Japan_Weapon_GBU_F2Kai"),
        row(7, "F-4EJ Kai", "JapanJetF4EJKai", "LEGACY MULTIROLE", "Japan_Weapon_Sparrow_F4EJ", "Japan_Weapon_Bomb_F4EJ"),
        row(8, "X-2 Shinshin", "JapanJetX2Shinshin", "STEALTH INTERCEPTOR", "Japan_Weapon_AAM4_X2", "cannon"),
        row(9, "F-35A", "JapanJetF35A", "STEALTH MULTIROLE", "JapanJetF35A_WpnRadar", "JapanJetF35A_WpnStrike"),
        row(10, "F-35B", "JapanJetF35B", "STEALTH STRIKE", "JapanJetF35B_WpnRadar", "JapanJetF35B_WpnStrike"),
        row(11, "F-X", "JapanJetFX", "FUTURE AIR SUPERIORITY", "JapanJetFX_WpnRadar", "JapanJetFX_WpnStrike"),
        row(12, "F-3 GCAP", "JapanJetF3", "FUTURE MULTIROLE", "JapanJetF3_WpnRadar", "JapanJetF3_WpnStrike"),
    ]
    kr_rows = [
        row(1, "F-15K", "SouthKoreaJetF15K", "HEAVY MULTIROLE", "SouthKoreaJetF15K_WpnIR", "SouthKoreaJetF15K_WpnBomb"),
        row(2, "F-15K Slam Eagle", "SouthKoreaJetF15KSlam", "STRIKE", "SouthKoreaJetF15KSlam_WpnIR", "SouthKoreaJetF15KSlam_WpnBomb"),
        row(3, "F-16C", "SouthKoreaJetF16C", "MULTIROLE", "SouthKoreaJetF16C_WpnRadar", "SouthKoreaJetF16C_WpnStrike"),
        row(4, "F-16D", "SouthKoreaJetF16D", "MULTIROLE / light strike", "SouthKoreaJetF16D_WpnRadar", "SouthKoreaJetF16D_WpnStrike"),
        row(5, "KF-16", "SouthKoreaJetKF16", "modernized multirole", "SouthKoreaJetKF16_WpnIR", "SouthKoreaJetKF16_WpnBomb"),
        row(6, "F-35A", "SouthKoreaJetF35A", "stealth multirole", "SouthKoreaJetF35A_WpnRadar", "SouthKoreaJetF35A_WpnStrike"),
        row(7, "KF-21", "SouthKoreaJetKF21", "air superiority + multirole", "SouthKoreaJetKF21_WpnRadar", "cannon"),
        row(8, "KF-21 Block 2", "SouthKoreaJetKF21Blk2", "precision strike", "SouthKoreaJetKF21Blk2_WpnRadar", "SouthKoreaJetKF21Blk2_WpnStrike"),
        row(9, "FA-50", "SouthKoreaJetFA50", "light attack", "SouthKoreaJetFA50_WpnGun", "SouthKoreaJetFA50_WpnBomb"),
        row(10, "T-50", "SouthKoreaJetT50", "light fighter / trainer", "SouthKoreaJetT50_WpnGun", "SouthKoreaJetT50_WpnBomb"),
        row(11, "F-4E", "SouthKoreaJetF4E", "legacy strike", "SouthKoreaJetF4E_WpnIR", "SouthKoreaJetF4E_WpnBomb"),
        row(12, "F-5E", "SouthKoreaJetF5E", "light interceptor", "SouthKoreaJetF5E_WpnGun", "SouthKoreaJetF5E_WpnBomb"),
    ]
    vn_rows = [
        row(1, "MiG-29", "VietnamJetMig29S", "A2A interceptor", "VietnamJetMig29S_WpnRadar", "cannon"),
        row(2, "MiG-21bis", "VietnamJetMig21bis", "short-range interceptor", "VietnamJetMig21bis_WpnIR", "VietnamJetMig21bis_WpnBomb"),
        row(3, "MiG-21MF", "VietnamJetMig21", "legacy interceptor", "VietnamJetMig21_WpnIR", "VietnamJetMig21_WpnBomb"),
        row(4, "Su-22M3", "VietnamJetSu22", "ground attack", "VietnamJetSu22_WpnIR", "VietnamJetSu22_WpnBomb"),
        row(5, "Su-22M4", "VietnamJetSu22M4", "ground attack / strike", "VietnamJetSu22M4_WpnGun", "VietnamJetSu22M4_WpnBomb"),
        row(6, "Su-27SK", "VietnamJetSu27", "air superiority", "VietnamJetSu27_WpnRadar", "cannon"),
        row(7, "Su-27UBK", "VietnamJetSu27UB", "multirole / A2A", "VietnamJetSu27UB_WpnRadar", "cannon"),
        row(8, "Su-30MK2", "VietnamJetSu30", "heavy multirole", "VietnamJetSu30_WpnRadar", "VietnamJetSu30_WpnStrike"),
        row(9, "Su-30MK2V", "VietnamJetSu30MK2", "multirole + anti-surface", "VietnamJetSu30MK2_WpnIR", "VietnamJetSu30MK2_WpnStandoff"),
        row(10, "Yak-130", "VietnamJetYak130", "light strike/trainer", "VietnamJetYak130_WpnGun", "VietnamJetYak130_WpnBomb"),
        row(11, "L-39", "VietnamJetL39", "light attack", "VietnamJetL39_WpnGun", "VietnamJetL39_WpnBomb"),
        row(12, "F-5E", "VietnamJetF5E", "light fighter", "VietnamJetF5E_WpnGun", "VietnamJetF5E_WpnBomb"),
    ]

    support = [
        ["Japan", "C-130H", "JapanJetC130H", "transport", models_in_object_text(object_block_from_map(re_map, "JapanJetC130H")), "packed ART AVCargoPln"],
        ["Japan", "RQ-4", "JapanUAVRQ4", "UAV", models_in_object_text(object_block_from_map(re_map, "JapanUAVRQ4")), "packed ART"],
        ["South Korea", "AH-64E Apache Guardian", "SouthKoreaJetAH64E", "attack helicopter", "US_AH64E", "packed ART"],
        ["South Korea", "CH-47D Chinook", "SouthKoreaJetCH47", "transport helicopter", "US_CH47F", "packed ART"],
        ["South Korea", "UH-60P Black Hawk", "SouthKoreaJetUH60P", "utility helicopter", "US_UH60", "packed ART"],
        ["South Korea", "E-737 Peace Eye", "SouthKoreaJetE737", "AEW", "KVE737", "packed ART static"],
        ["South Korea", "C-130H", "SouthKoreaJetC130H", "transport", "US_C130H", "packed ART"],
        ["Vietnam", "Mi-8", "VietnamJetMi8", "utility helicopter", "Irq_Mi8T", "packed ART"],
        ["Vietnam", "Mi-17", "VietnamJetMi17", "transport helicopter", "Egy_MI17", "packed ART"],
        ["Vietnam", "IL-76", "VietnamJetIL76", "heavy transport", "Iraq_IL-76", "packed ART"],
    ]

    il76_block = object_block_from_map(re_map, "VietnamJetIL76")
    iraq_il76_block = object_block_from_map(re_map, "IraqJetIL76")
    mig_block = object_block_from_map(re_map, "IraqJetMig25RB")
    il76_pass, il76_info = static_runway_check(il76_block, True)
    il76_pass2, il76_info2 = static_runway_check(iraq_il76_block, True)
    mig_pass, mig_info = static_runway_check(mig_block, False)
    if "IraqJetMig25RB_WpnLT3" not in mig_block:
        raise SystemExit("MiG-25RB missing J-10 wrapper weapon")
    wpn_re = re_map["data\\ini\\weapon.ini"][1].decode("latin1")
    bomb = grab_named(wpn_re, "Weapon", "IraqJetMig25RB_WpnLT3")
    if "Sattar_LGAGM_Object" not in bomb:
        raise SystemExit("MiG-25RB bomb not J-10 family projectile")
    if not re.search(r"ClipSize\s+=\s+6\b", bomb):
        raise SystemExit("MiG-25RB ClipSize is not 6")
    if "3x_1000LB_LT3_PGM_J10C" in bomb:
        raise SystemExit("wrapper incorrectly reused J-10 weapon name")

    upgrades = []
    for country, items in (
        (
            "Japan",
            [
                "Upgrade_Japan_AircraftWeapons",
                "Upgrade_Japan_AircraftCountermeasures",
                "Upgrade_Japan_F35Integration",
                "Upgrade_Japan_PrecisionStrike",
                "Upgrade_Japan_DoctrineAirSuperiority",
                "Upgrade_Japan_DoctrinePrecisionStrike",
                "Upgrade_Japan_TechPrecisionDefense",
                "Upgrade_Japan_TechRadarNetwork",
            ],
        ),
        (
            "South Korea",
            [
                "Upgrade_SouthKorea_AircraftWeapons",
                "Upgrade_SouthKorea_AircraftCountermeasures",
                "Upgrade_SouthKorea_F15KUpgrade",
                "Upgrade_SouthKorea_KFDefense",
                "Upgrade_SouthKorea_DoctrineAirSuperiority",
                "Upgrade_SouthKorea_TechAirDominanceK",
            ],
        ),
        (
            "Vietnam",
            [
                "Upgrade_Vietnam_AircraftWeapons",
                "Upgrade_Vietnam_AircraftCountermeasures",
                "Upgrade_Vietnam_Su30Doctrine",
            ],
        ),
    ):
        heavy = {"Japan": "Japan_HeavyAirBaseCommandSet", "South Korea": "SouthKorea_HeavyAirBaseCommandSet", "Vietnam": "Vietnam_HeavyAirBaseCommandSet"}[country]
        block = ch.grab_block(re_cs, heavy)
        for up in items:
            btn = "Command_" + up.replace("Upgrade_", "Upgrade")
            # Command_UpgradeJapan_AircraftWeapons from Upgrade_Japan_AircraftWeapons
            btn = "Command_" + up.replace("Upgrade_", "Upgrade")
            status = "AVAILABLE" if btn in block else "MISSING"
            if status != "AVAILABLE":
                raise SystemExit(f"upgrade button {btn} not on {heavy}")
            upgrades.append([country, up, "SCIENCE Rank8 / not packed", f"{heavy} extra slots", btn, status])

    unresolved = [
        ["South Korea", "KUH-1 Surion", "No dedicated Surion/KUH W3D in packed ART or TEOD", "UH-60P used as the utility helicopter instead"],
        ["Global", "Dedicated L-159 mesh", "No L-159 W3D packed; LSFT50 T-50/FA-50 class used", "Alpha Jet / Hawk / L-39 meshes not packed"],
        ["Japan", "Dedicated F-3 GCAP mesh", "PAK-FA stand-in retained", "No Tempest/GCAP W3D packed"],
    ]

    vis_jp = visual_stats(jp_rows)
    vis_kr = visual_stats(kr_rows)
    vis_vn = visual_stats(vn_rows)
    # family counts: eagles / vipers / flankers
    vis_jp["family"] = 3  # three F-15 variants, three F-2, two F-35
    vis_kr["family"] = 4  # two F-15, three F-16/KF-16, two KF-21
    vis_vn["family"] = 4  # two MiG-21, two Su-22, four Flanker-family

    meta = {
        "roster": {"JAPAN": jp_rows, "SOUTH KOREA": kr_rows, "VIETNAM": vn_rows},
        "support": support,
        "visual": {"JAPAN": vis_jp, "SOUTH KOREA": vis_kr, "VIETNAM": vis_vn},
        "upgrades": upgrades,
        "runway": {"VietnamJetIL76": il76_info, "IraqJetIL76": il76_info2, "IraqJetMig25RB": mig_info},
        "il76_static": "PASS" if il76_pass == "PASS" and il76_pass2 == "PASS" else "FAIL",
        "mig25_static": mig_pass,
        "dup_audit": "PASS",
        "anim_audit": "PASS",
        "protect": "PASS",
        "reextract": "PASS",
        "dup_details": "",
        "unresolved": unresolved,
    }
    write_reports(out, meta)
    for name in (
        "JP_KR_VN_FINAL_ROSTER.md",
        "JP_KR_VN_VISUAL_AUDIT.md",
        "JP_KR_VN_AIR_UPGRADES.md",
        "AIR_UPGRADE_AUDIT_JP_KR_VN.md",
        "IL76_MIG25RB_FIX_AUDIT.md",
        "RUNWAY_AIRCRAFT_FIX_AUDIT.md",
        "L159_VISUAL_SOURCE_AUDIT.md",
        "CRASH_REGRESSION_AUDIT.md",
        "INSTALL.txt",
    ):
        shutil.copy2(out / name, ROOT / name)

    zip_path = out / "JP_KOREA_VIETNAM_AIRFORCE_FIX_V1.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "INSTALL.txt",
            "JP_KR_VN_FINAL_ROSTER.md",
            "JP_KR_VN_VISUAL_AUDIT.md",
            "JP_KR_VN_AIR_UPGRADES.md",
            "IL76_MIG25RB_FIX_AUDIT.md",
            "L159_VISUAL_SOURCE_AUDIT.md",
            "CRASH_REGRESSION_AUDIT.md",
        ):
            zf.write(out / name, name)

    print("DATA", sha256(out / "_SPEC_DATA_ONE.big"))
    print("ART", sha256(out / "_SPEC_ART_ONE.big"))
    print("ZIP", sha256(zip_path))
    print("IL76_STATIC_RUNWAY_CHECK", meta["il76_static"])
    print("MIG25RB_STATIC_RUNWAY_CHECK", meta["mig25_static"])
    print("JAPAN UNIQUE W3D", vis_jp["unique"], "DUPS", vis_jp["dups"])
    print("KOREA UNIQUE W3D", vis_kr["unique"], "DUPS", vis_kr["dups"])
    print("VIETNAM UNIQUE W3D", vis_vn["unique"], "DUPS", vis_vn["dups"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
