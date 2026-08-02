#!/usr/bin/env python3
"""Build USA AAB final-fix source overlays (strings + America-only AFF)."""
from __future__ import annotations

import collections
import re
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
USA = ROOT / "USA_ONLY_CLEAN"
DATA = ROOT / "Data"
BASE_BIG = ROOT / "Release" / "SPECTER_USA_AIRCRAFT_STRING_BUTTON_FIX" / "_SPEC_DATA_ONE.big"


def read_big(path: Path):
    data = path.read_bytes()
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    m = {}
    for _ in range(n):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        sz = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        m[name] = data[off : off + sz]
    return m


def main() -> int:
    m = read_big(BASE_BIG)

    # 1) Deduplicated ASCII strings -> single file
    files = [
        "Data\\English\\AdvancedAirBase_Strings.txt",
        "Data\\English\\AdvancedAWACS_Strings.txt",
        "Data\\English\\USA_HeavyAircraft_Strings.txt",
    ]
    merged: collections.OrderedDict[str, str] = collections.OrderedDict()
    for f in files:
        text = m[f].decode("ascii")
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith(";") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            k, v = k.strip(), v.strip()
            if k not in merged:
                merged[k] = v
    for k, v in [
        ("OBJECT:America_AdvancedAirBase", "America Advanced Air Base"),
        ("OBJECT:Patch_America_B2", "B-2 Spirit"),
        ("OBJECT:Patch_America_B1", "B-1B Lancer"),
        ("OBJECT:Patch_America_B52", "B-52 Stratofortress"),
        ("OBJECT:Patch_America_E3", "E-3 Sentry AWACS"),
        ("OBJECT:Patch_America_C17", "C-17 Globemaster"),
        ("OBJECT:Patch_America_KC135", "KC-135 Tanker"),
        ("OBJECT:Patch_America_AC130Spectre", "AC-130 Spectre"),
        ("OBJECT:Patch_America_AssaultHelo", "Assault Helicopter"),
        ("OBJECT:AmericaJetB2Spirit", "B-2 Spirit"),
        ("OBJECT:AmericaJetB52H", "B-52H Stratofortress"),
        ("OBJECT:AmericaJetE3AWACS", "E-3 AWACS"),
    ]:
        merged.setdefault(k, v)

    body = ["; USA AAB / aircraft strings (ASCII, deduplicated single overlay)\n"]
    for k, v in sorted(merged.items()):
        body.append(f"{k} = {v}\n")
    single = USA / "Data/English/USA_HeavyAircraft_Strings.txt"
    single.write_text("".join(body), encoding="ascii")
    stub = "; superseded by USA_HeavyAircraft_Strings.txt (deduplicated)\n"
    for name in ("AdvancedAirBase_Strings.txt", "AdvancedAWACS_Strings.txt"):
        (USA / "Data/English" / name).write_text(stub, encoding="ascii")
        (DATA / "English" / name).parent.mkdir(parents=True, exist_ok=True)
        (DATA / "English" / name).write_text(stub, encoding="ascii")
    (DATA / "English").mkdir(parents=True, exist_ok=True)
    (DATA / "English/USA_HeavyAircraft_Strings.txt").write_text(
        single.read_text(encoding="ascii"), encoding="ascii"
    )
    print(f"strings keys={len(merged)} -> {single}")

    # 2) America-only AirForceExpansion aircraft
    aff_key = [k for k in m if k.lower().endswith("aircraft_airforceexpansion.ini")][0]
    text = m[aff_key].decode("latin1", errors="replace")
    parts = re.split(r"(?=^(?:Object|ObjectReskin)\s+)", text, flags=re.M)
    keep_aff = {
        "Patch_America_Aurora",
        "Patch_America_StealthHawk",
        "Patch_America_E2C",
        "Patch_America_B3",
    }
    blocks = []
    for part in parts:
        om = re.match(r"(?:Object|ObjectReskin)\s+(\S+)", part)
        if om and om.group(1) in keep_aff:
            blocks.append(part.rstrip() + "\n\n")
            print("AFF keep", om.group(1))
    header = (
        "; USA-only AirForceExpansion aircraft (America objects only).\n"
        "; Removes non-USA faction aircraft. AC-130 lives in Aircraft_USA_Heavy_Runway.ini.\n"
        "; Does not edit CommandSet.ini.\n\n"
    )
    aff_out = (
        USA
        / "Data/INI/Object/Specter/PatchSystems/AirForceExpansion/Aircraft_AirForceExpansion.ini"
    )
    aff_out.parent.mkdir(parents=True, exist_ok=True)
    aff_out.write_text(
        (header + "".join(blocks)).encode("ascii", "replace").decode("ascii"),
        encoding="ascii",
    )

    # 3) America-only projectiles
    proj_key = [k for k in m if k.lower().endswith("projectiles_airforceexpansion.ini")][0]
    ptext = m[proj_key].decode("latin1", errors="replace")
    pparts = re.split(r"(?=^(?:Object|ObjectReskin)\s+)", ptext, flags=re.M)
    keep_proj = {
        "Patch_Projectile_AuroraFuelAir",
        "Patch_Projectile_StealthHawkAAM",
        "Patch_Projectile_E2C_SelfDefense",
        "Patch_Projectile_B3Cruise",
        "Patch_Projectile_SpectreHowitzer",
    }
    pblocks = []
    for part in pparts:
        om = re.match(r"(?:Object|ObjectReskin)\s+(\S+)", part)
        if om and om.group(1) in keep_proj:
            pblocks.append(part.rstrip() + "\n\n")
            print("PROJ keep", om.group(1))
    proj_out = (
        USA
        / "Data/INI/Object/Specter/PatchSystems/AirForceExpansion/Projectiles/Projectiles_AirForceExpansion.ini"
    )
    proj_out.parent.mkdir(parents=True, exist_ok=True)
    proj_out.write_text(
        ("; USA-only AirForceExpansion projectiles\n\n" + "".join(pblocks))
        .encode("ascii", "replace")
        .decode("ascii"),
        encoding="ascii",
    )

    # 4) Fighters.ini: drop AFF duplicates
    fighters = (
        USA
        / "Data/INI/Object/Specter/PatchSystems/AAA_USA_HeavyRunway/Aircraft_USA_AAB_Fighters.ini"
    )
    ft = fighters.read_text(encoding="ascii")
    fparts = re.split(r"(?=^(?:Object|ObjectReskin)\s+)", ft, flags=re.M)
    drop = {
        "Patch_America_Aurora",
        "Patch_America_StealthHawk",
        "Patch_America_B3",
        "Patch_America_E2C",
    }
    kept = []
    hdr = []
    for part in fparts:
        om = re.match(r"(?:Object|ObjectReskin)\s+(\S+)", part)
        if not om:
            if part.strip():
                hdr.append(part)
            continue
        if om.group(1) in drop:
            print("FIGHTERS drop dup", om.group(1))
            continue
        kept.append(part.rstrip() + "\n\n")
    new_f = (
        "; USA AAB fighter aircraft objects (America only).\n"
        "; No multi-faction AAB_Global. No duplicate AFF objects.\n\n"
        + "".join(kept)
    )
    fighters.write_text(new_f.encode("ascii", "replace").decode("ascii"), encoding="ascii")
    print(
        "fighters objects",
        re.findall(r"^(?:Object|ObjectReskin)\s+(\S+)", fighters.read_text(), re.M),
    )

    # sync into patch/Data
    for src, rel in [
        (fighters, "INI/Object/Specter/PatchSystems/AAA_USA_HeavyRunway/Aircraft_USA_AAB_Fighters.ini"),
        (aff_out, "INI/Object/Specter/PatchSystems/AirForceExpansion/Aircraft_AirForceExpansion.ini"),
        (
            proj_out,
            "INI/Object/Specter/PatchSystems/AirForceExpansion/Projectiles/Projectiles_AirForceExpansion.ini",
        ),
    ]:
        dst = DATA / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print("synced patch/Data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
