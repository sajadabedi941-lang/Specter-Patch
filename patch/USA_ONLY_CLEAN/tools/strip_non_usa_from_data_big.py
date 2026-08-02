#!/usr/bin/env python3
"""USA-only DATA BIG cleaner. Does not edit CommandSet.ini contents.

Keeps stock cores + America AAB / USA heavy aircraft / USA drones / USA strings.
Kills old PatchSystems overlays, faction-framework strings, STRINGS_TO_ADD,
Phase/AirForce/UN CommandButton+CommandSet packs, and non-USA Specter factions.
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

# Exact English .txt basename whitelist (ASCII USA overlays only).
KEEP_ENGLISH_TXT = {
    "advancedairbase_strings.txt",
    "advancedawacs_strings.txt",
    "usa_heavyaircraft_strings.txt",
}

# Top-level Data\INI\* overlays allowed besides stock cores.
KEEP_TOP_INI_EXACT = {
    "data\\ini\\commandbutton_usa_advancedairbase.ini",
    "data\\ini\\commandbutton_advancedairbase_aircraft.ini",
    "data\\ini\\commandbutton_advancedawacs.ini",
    "data\\ini\\commandset_usa_advancedairbase.ini",
    "data\\ini\\commandset_advancedawacs.ini",
    "data\\ini\\specialpower_advancedawacs.ini",
    "data\\ini\\weapon_advancedawacs.ini",
    "data\\ini\\science_generalstar_addon.ini",
    "data\\ini\\commandbutton_generalstar_addon.ini",
    "data\\ini\\upgrade_runtimefix_america.ini",
}

# Stock / always-keep top-level names (never strip by overlay rules).
STOCK_TOP_KEEP_PREFIXES = (
    "data\\ini\\animation2d.ini",
    "data\\ini\\armor.ini",
    "data\\ini\\audiosettings.ini",
    "data\\ini\\challengemode.ini",
    "data\\ini\\commandbutton.ini",
    "data\\ini\\commandmap",
    "data\\ini\\commandset.ini",
    "data\\ini\\controlbarresizer.ini",
    "data\\ini\\controlbarscheme.ini",
    "data\\ini\\crate.ini",
    "data\\ini\\damagefx.ini",
    "data\\ini\\drawgroupinfo.ini",
    "data\\ini\\edit.exe",
    "data\\ini\\eva.ini",
    "data\\ini\\fxlist.ini",
    "data\\ini\\gamedata.ini",
    "data\\ini\\gamelod",
    "data\\ini\\ingameui.ini",
    "data\\ini\\locomotor.ini",
    "data\\ini\\memorypools.ini",
    "data\\ini\\miscaudio.ini",
    "data\\ini\\mouse.ini",
    "data\\ini\\objectcreationlist.ini",
    "data\\ini\\particlesystem.ini",
    "data\\ini\\playertemplate.ini",
    "data\\ini\\rank.ini",
    "data\\ini\\science.ini",
    "data\\ini\\soundeffects.ini",
    "data\\ini\\specialpower.ini",
    "data\\ini\\upgrade.ini",
    "data\\ini\\voice.ini",
    "data\\ini\\water.ini",
    "data\\ini\\weapon.ini",
    "data\\ini\\readme_",
)


def read_big(path: Path):
    data = path.read_bytes()
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(n):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        sz = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, data[off : off + sz]))
    return entries


def build_big(file_map: dict) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index, blobs, offset = [], [], header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for b in blobs:
        out += b
    return bytes(out)


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def is_stock_top(low: str) -> bool:
    if not low.startswith("data\\ini\\"):
        return False
    # Nested Default\ etc.
    if low.startswith("data\\ini\\default\\"):
        return True
    if low.startswith("data\\ini\\mappedimages\\"):
        # Keep USA mapped images + stock UI; drop Specter faction power windows.
        base = low.rsplit("\\", 1)[-1]
        if any(
            x in base
            for x in (
                "arab_",
                "irn_",
                "pla_",
                "rus_",
            )
        ):
            return False
        if "advancedairbase_images.ini" in base:
            return True
        return True
    # Only top-level Data\INI\file
    if low.count("\\") != 2:
        return False
    for p in STOCK_TOP_KEEP_PREFIXES:
        if low.startswith(p) or low == p.rstrip("."):
            # commandmap matches commandmapdebug/demo
            if p.endswith("commandmap") and low.startswith("data\\ini\\commandmap"):
                return True
            if p.endswith("gamelod") and low.startswith("data\\ini\\gamelod"):
                return True
            if low == p or (p.endswith(".ini") and low == p):
                return True
            if p.endswith("_") and low.startswith(p):
                return True
    # Exact stock cores
    if low in KEEP_TOP_INI_EXACT:
        return True
    return False


def patchsystems_keep(low: str) -> bool:
    """Whitelist PatchSystems paths."""
    if "\\patchsystems\\aaa_usa_heavyrunway\\" in low:
        return True
    if "\\patchsystems\\drones\\" in low:
        base = low.rsplit("\\", 1)[-1]
        return base.startswith("america_")
    return False


def should_kill(name: str) -> bool:
    low = norm(name)

    # Never kill stock CommandSet.ini (content preserved; we just keep the entry).
    if low == "data\\ini\\commandset.ini":
        return False

    # English string dumps: whitelist only.
    if "\\english\\" in low and low.endswith(".txt"):
        base = low.rsplit("\\", 1)[-1]
        if base in KEEP_ENGLISH_TXT:
            return False
        # Explicit kills for known crash sources.
        if (
            base == "strings_to_add.txt"
            or base == "factionframework_strings.txt"
            or base.startswith("factionexpansion_")
            or "faction" in base
            or base.startswith("airforce")
            or "turkey" in base
        ):
            return True
        return True

    # Specter object tree.
    if "object\\specter\\" in low:
        rest = low.split("object\\specter\\", 1)[1]
        first = rest.split("\\", 1)[0]
        if first == "united states of america":
            return False
        if first == "patchsystems":
            return not patchsystems_keep(low)
        # Kill every other Specter faction folder (Egypt, Britain, France, …).
        return True

    # Top-level overlay INIs.
    if low.startswith("data\\ini\\") and low.count("\\") == 2 and low.endswith(".ini"):
        if low in KEEP_TOP_INI_EXACT:
            return False
        if is_stock_top(low):
            return False
        base = low.rsplit("\\", 1)[-1]
        # Kill multi-faction / phase / airforce / UN / specterpatch overlays.
        kill_tokens = (
            "airforce",
            "phase",
            "faction",
            "specter",
            "un_",
            "_un.ini",
            "egypt",
            "britain",
            "france",
            "germany",
            "india",
            "japan",
            "turkey",
            "doctrine",
            "verification",
            "integrity",
            "patcheconomy",
            "nuclearstrategic",
            "strategicbombers",
            "advancedairbase_specter",
            "commandset_advancedairbase.ini",  # multi; keep USA_ only
            "commandbutton_advancedairbase_specter",
            "countrybalance",
            "playertemplate_specter",
        )
        if any(t in base for t in kill_tokens):
            return True
        # Any remaining CommandButton_/CommandSet_/Science_/Weapon_/SpecialPower_/Upgrade_ overlay
        if base.startswith(
            (
                "commandbutton_",
                "commandset_",
                "science_",
                "weapon_",
                "specialpower_",
                "upgrade_",
                "objectcreationlist_",
                "locomotor_",
                "controlbarscheme_",
                "countrydoctrine_",
            )
        ):
            return True
        return False

    # MappedImages faction power windows.
    if "mappedimages" in low and any(x in low for x in ("arab_", "irn_", "pla_", "rus_")):
        return True

    # Path-based faction keywords (avoid stock China*.ini / MD_China movies).
    if "object\\specter\\" in low or "commandbutton_" in low or "commandset_" in low:
        for term in (
            "egypt",
            "britain",
            "france",
            "germany",
            "india",
            "pakistan",
            "saudi",
            "uae",
            "turkey",
            "ukraine",
            "japan",
            "taiwan",
            "korea",
            "sweden",
            "italy",
            "syria",
            "libya",
            "vietnam",
            "southafrica",
            "united nations",
            "nato",
            "factionexpansion",
            "factionframework",
            "strings_to_add",
        ):
            if term in low:
                return True

    # Explicit leftover overlay names often present in merged packs.
    for bad in (
        "factionframework",
        "strings_to_add",
        "airforceexpansion",
        "airforcefinal",
        "projectile_factionexpansion",
        "militaryhq_stockfactions",
        "boss_faction_objects",
        "russia_rs24",
        "playertemplate_specterpatch",
        "commandbutton_factionexpansion",
        "aircraft_aab_global",
        "aircraft_aab_strategicbombers",
        "aircraft_airforcefinal",
        "advancedairbase_allfactions",
        "advancedairbase_futurefactions",
        "commandbutton_advancedairbase_specterfactions",
    ):
        if bad in low:
            return True

    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    args = ap.parse_args()
    kept = {}
    killed = []
    for name, blob in read_big(args.data_big):
        if should_kill(name):
            killed.append(name)
            continue
        kept[name] = blob
    args.out_big.parent.mkdir(parents=True, exist_ok=True)
    args.out_big.write_bytes(build_big(kept))
    print(f"killed={len(killed)} kept={len(kept)} -> {args.out_big}")
    # Summarize kills by category for audit.
    cats = {
        "english_txt": 0,
        "patchsystems": 0,
        "specter_faction": 0,
        "command_overlay": 0,
        "other": 0,
    }
    for n in killed:
        low = norm(n)
        if "\\english\\" in low and low.endswith(".txt"):
            cats["english_txt"] += 1
        elif "\\patchsystems\\" in low:
            cats["patchsystems"] += 1
        elif "object\\specter\\" in low:
            cats["specter_faction"] += 1
        elif "commandbutton_" in low or "commandset_" in low:
            cats["command_overlay"] += 1
        else:
            cats["other"] += 1
    print("kill_cats", cats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
