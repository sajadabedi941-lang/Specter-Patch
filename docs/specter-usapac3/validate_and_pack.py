#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
OUT_DIR = ROOT / "docs/specter-usapac3"
OUT_BIG = OUT_DIR / "_SPECTER_USAPAC3.big"
PATCH = ROOT / "patch"


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def pack_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin-1")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
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
        out += name.encode("latin-1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def last_wins_cmdset() -> Path | None:
    last = None
    for p in sorted((PATCH / "Data/INI").glob("CommandSet*.ini"), key=lambda x: x.name.lower()):
        text = p.read_text(encoding="latin-1", errors="replace")
        if re.search(r"(?m)^CommandSet\s+America_MilitaryHQCommandSet\s*$", text):
            last = p
    return last


def main() -> int:
    obj = (PATCH / "Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3.ini").read_text(encoding="latin-1")
    wep = (PATCH / "Data/INI/Weapon_USAPAC3.ini").read_text(encoding="latin-1")
    proj = (PATCH / "Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3_Projectile.ini").read_text(encoding="latin-1")
    btn = (PATCH / "Data/INI/CommandButton_USAPAC3.ini").read_text(encoding="latin-1")
    checks = {
        "object": "Object USAPAC3" in obj,
        "no_thaad_redef": "Object America_AD_THAAD" not in obj,
        "no_patriot_redef": "Object America_AD_Patriot" not in obj and "Object AmericaRadarAN/MPQ65" not in obj,
        "model": "Model             = UsaPac3Car" in obj,
        "deployed": "Model             = UsaPac3F" in obj,
        "loco": "Generic8x8Locomotor" in obj,
        "weapon_ref": "USAPAC3_Weapon" in obj,
        "cost": "BuildCost           = 3876" in obj,
        "time": "BuildTime           = 18.6" in obj,
        "wep_range": "AttackRange = 800.0" in wep,
        "wep_speed": "WeaponSpeed = 1500" in wep,
        "wep_abm": "AntiBallisticMissile = Yes" in wep,
        "wep_proj": "ProjectileObject = USAPAC3_Projectile" in wep,
        "proj_model": "Model = pac3mis_m" in proj,
        "button": "Object             = USAPAC3" in btn,
    }
    for name, ok in checks.items():
        print(("OK  " if ok else "FAIL"), name)
        if not ok:
            fail(name)

    thaad = (PATCH / "Data/INI/Object/Specter/PatchSystems/AirDefense/America_AD_THAAD.ini").read_text(encoding="latin-1")
    if "Object America_AD_THAAD" not in thaad or "America_Weapon_THAAD" not in thaad:
        fail("THAAD file damaged")
    print("OK   America_AD_THAAD unchanged identity")

    lw = last_wins_cmdset()
    if lw is None or lw.name != "CommandSet_ZZZZ_USAPAC3.ini":
        fail(f"last-wins HQ set is {lw}")
    cs = lw.read_text(encoding="latin-1")
    if "6 = Command_ConstructUSAPAC3" not in cs:
        fail("slot 6 is not USAPAC3")
    if "12 = Command_ConstructAmerica_AD_NASAMS" not in cs:
        fail("NASAMS not preserved on slot 12")
    if "5 = Command_ConstructAmerica_AD_THAAD" not in cs:
        fail("THAAD slot 5 dropped")
    if "4 = Command_ConstructAmerica_AD_Patriot" not in cs:
        fail("Patriot slot 4 dropped")
    print("OK   HQ slot 6=USAPAC3 slot 12=NASAMS last-wins", lw.name)

    required_art = [
        "Art/W3D/UsaPac3Car.W3D",
        "Art/W3D/UsaPac3Car_d.W3D",
        "Art/W3D/UsaPac3Car_w.W3D",
        "Art/W3D/UsaPac3F.W3D",
        "Art/W3D/UsaPac3F_d.W3D",
        "Art/W3D/pac3mis_m.W3D",
        "Art/Textures/USAPAC3TB.tga",
        "Art/Textures/usaPAC3TRUCKmap.dds",
        "Art/Textures/ABNPatriot02.dds",
    ]
    for rel in required_art:
        p = PATCH / rel
        if not p.exists():
            fail(f"missing art {rel}")
    print("OK   donor art present")

    file_map: dict[str, bytes] = {}
    include = [
        PATCH / "Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3.ini",
        PATCH / "Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3_Projectile.ini",
        PATCH / "Data/INI/Weapon_USAPAC3.ini",
        PATCH / "Data/INI/CommandButton_USAPAC3.ini",
        PATCH / "Data/INI/CommandSet_ZZZZ_USAPAC3.ini",
        PATCH / "Data/INI/MappedImages/HandCreated/USAPAC3_Images.INI",
        PATCH / "Data/English/FactionExpansion_USAPAC3_Strings.txt",
        PATCH / "Data/English/generals.csf",
    ]
    include += [PATCH / rel for rel in required_art]
    include += list((PATCH / "Art/Textures").glob("*pac3*"))
    include += list((PATCH / "Art/Textures").glob("*PAC3*"))
    include += list((PATCH / "Art/Textures").glob("ABNPatriot02*"))
    include += list((PATCH / "Art/Textures").glob("ampac3*"))
    seen = set()
    for path in include:
        if not path.exists():
            fail(f"missing {path}")
        rel = path.relative_to(PATCH).as_posix().replace("/", "\\")
        if rel in seen:
            continue
        seen.add(rel)
        file_map[rel] = path.read_bytes()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    big = pack_big(file_map)
    OUT_BIG.write_bytes(big)
    digest = hashlib.sha256(big).hexdigest()
    (OUT_DIR / (OUT_BIG.name + ".sha256")).write_text(f"{digest}  {OUT_BIG.name}\n", encoding="ascii")
    print(f"PACKED {OUT_BIG} bytes={len(big)} entries={len(file_map)} sha256={digest}")
    print("STATIC_OK")
    print("INGAME_ZH: not executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
