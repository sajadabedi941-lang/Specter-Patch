#!/usr/bin/env python3
"""Remove USAPAC3-only entries from active SPECTER DATA + ART TWO.

Does not delete shared ART (ABNPatriot02, pac3_sudarb), THAAD/Patriot/NASAMS
objects, other countries, or generals.csf string table. Restores America
Command Center to the pre-USAPAC3 block (no slot 6). Previous Releases are
not rewritten.
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
MERGED = ROOT / "docs/specter-usapac3/merged"
DATA = MERGED / "_SPEC_DATA_ONE.big"
ART2 = MERGED / "_SPEC_ART_TWO.big"
CS_LOOSE = MERGED / "CommandSet.ini"
CB_LOOSE = MERGED / "CommandButton.ini"

REMOVE_DATA = {
    "data\\english\\factionexpansion_usapac3_strings.txt",
    "data\\ini\\commandset_zzzz_usapac3.ini",
    "data\\ini\\mappedimages\\handcreated\\usapac3_images.ini",
    "data\\ini\\object\\specter\\patchsystems\\airdefense\\usapac3.ini",
    "data\\ini\\object\\specter\\patchsystems\\airdefense\\usapac3_projectile.ini",
    "data\\ini\\weapon_usapac3.ini",
    "data\\ini\\commandbutton_usapac3.ini",
}

REMOVE_ART = {
    "art\\w3d\\usapac3car.w3d",
    "art\\w3d\\usapac3car_d.w3d",
    "art\\w3d\\usapac3car_w.w3d",
    "art\\w3d\\usapac3f.w3d",
    "art\\w3d\\usapac3f_d.w3d",
    "art\\w3d\\pac3mis_m.w3d",
    "art\\textures\\usapac3truckmap.dds",
    "art\\textures\\usapac3truckmap_d.dds",
    "art\\textures\\ampac3map.dds",
    "art\\textures\\ampac3map_d.dds",
    "art\\textures\\ampac3mapback.dds",
    "art\\textures\\pac3missilemap.dds",
    "art\\textures\\usapac3.tga",
    "art\\textures\\usapac3tb.tga",
}

KEEP_ART = {
    "art\\textures\\abnpatriot02.dds",
    "art\\textures\\abnpatriot02_d.tga",
    "art\\w3d\\pac3_sudarb.w3d",
    "art\\w3d\\abpatriot.w3d",
}

CC_OLD = (
    "CommandSet AmericaCommandCenterCommandSet\r\n"
    "  1  = Command_ConstructAmericaDozer\r\n"
    "  6  = Command_ConstructUSAPAC3\r\n"
    " 12  = Command_ConstructAmericaVehicleUH60\r\n"
    " 13  = Command_ConstructAmericaVehicleM2A3BuskIIIMech\r\n"
    " 14 = Command_Sell\r\n"
    " 15 = Command_ConstructSpecterAI_CZDropMarker\r\n"
    " 16 = Command_ConstrucAmericaDronesMq9AI\r\n"
    " 17 = Command_ConstructAmericaHelicopterCh47F_AI\r\n"
    " 18 = Command_ConstructAmericaDroneMQ4AI\r\n"
    "End"
)
CC_NEW = (
    "CommandSet AmericaCommandCenterCommandSet\r\n"
    "  1  = Command_ConstructAmericaDozer\r\n"
    " 12  = Command_ConstructAmericaVehicleUH60\r\n"
    " 13  = Command_ConstructAmericaVehicleM2A3BuskIIIMech\r\n"
    " 14 = Command_Sell\r\n"
    " 15 = Command_ConstructSpecterAI_CZDropMarker\r\n"
    " 16 = Command_ConstrucAmericaDronesMq9AI\r\n"
    " 17 = Command_ConstructAmericaHelicopterCh47F_AI\r\n"
    " 18 = Command_ConstructAmericaDroneMQ4AI\r\n"
    "End"
)

HQ_OLD = (
    "  5 = Command_ConstructAmerica_AD_THAAD\r\n"
    "  6 = Command_ConstructUSAPAC3\r\n"
    "  7 = Command_ConstructAmerica_AD_Hawk\r\n"
    "  8 = Command_ConstructAmerica_RQ180\r\n"
    "  9 = Command_ConstructAmerica_MQ9Reaper\r\n"
    "  10 = Command_ConstructAmerica_ARRWTEL\r\n"
    "  11 = Command_ConstructAmerica_PGSTEL\r\n"
    "  12 = Command_ConstructAmerica_AD_NASAMS\r\n"
)
HQ_NEW = (
    "  5 = Command_ConstructAmerica_AD_THAAD\r\n"
    "  6 = Command_ConstructAmerica_AD_NASAMS\r\n"
    "  7 = Command_ConstructAmerica_AD_Hawk\r\n"
    "  8 = Command_ConstructAmerica_RQ180\r\n"
    "  9 = Command_ConstructAmerica_MQ9Reaper\r\n"
    "  10 = Command_ConstructAmerica_ARRWTEL\r\n"
    "  11 = Command_ConstructAmerica_PGSTEL\r\n"
)

BTN_RE = re.compile(
    rb"\r?\n; SPECTER PATCH USAPAC3 construct button\..*?"
    rb"CommandButton Command_ConstructUSAPAC3\r?\n.*?\r?\nEnd\r?\n",
    re.S,
)


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        fail(f"not BIGF {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos = end + 1
        entries.append((name, off, size))
    return data, entries


def build_big(file_map: dict[str, bytes]) -> bytes:
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
    out = bytearray(b"BIGF")
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin-1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def key(name: str) -> str:
    return name.replace("/", "\\").lower()


def patch_ini_bytes(blob: bytes, path: str) -> bytes:
    txt = blob.decode("latin-1")
    orig = txt
    k = path.lower()
    if k.endswith("commandset.ini"):
        if CC_OLD not in txt:
            # unix newlines
            if CC_OLD.replace("\r\n", "\n") in txt:
                txt = txt.replace(CC_OLD.replace("\r\n", "\n"), CC_NEW.replace("\r\n", "\n"))
            else:
                fail(f"{path}: AmericaCommandCenterCommandSet USAPAC3 block not found")
        else:
            txt = txt.replace(CC_OLD, CC_NEW)
        if "Command_ConstructUSAPAC3" in txt:
            fail(f"{path}: USAPAC3 still referenced")
    elif k.endswith("commandbutton.ini"):
        new, n = BTN_RE.subn(b"\n", blob)
        if n != 1:
            fail(f"{path}: expected 1 construct button block, got {n}")
        txt = new.decode("latin-1")
        if "Command_ConstructUSAPAC3" in txt:
            fail(f"{path}: button still present")
        return txt.encode("latin-1")
    elif k.endswith("commandset_factionexpansion_armies.ini"):
        if HQ_OLD not in txt:
            if HQ_OLD.replace("\r\n", "\n") in txt:
                txt = txt.replace(HQ_OLD.replace("\r\n", "\n"), HQ_NEW.replace("\r\n", "\n"))
            else:
                fail(f"{path}: HQ USAPAC3 block not found")
        else:
            txt = txt.replace(HQ_OLD, HQ_NEW)
        if "Command_ConstructUSAPAC3" in txt:
            fail(f"{path}: USAPAC3 still in HQ set")
        if "Command_ConstructAmerica_AD_NASAMS" not in txt:
            fail(f"{path}: NASAMS lost")
        if "Command_ConstructAmerica_AD_THAAD" not in txt or "Command_ConstructAmerica_AD_Patriot" not in txt:
            fail(f"{path}: THAAD/Patriot lost")
    if txt == orig and k.endswith("commandset.ini"):
        fail(f"{path}: unchanged")
    return txt.encode("latin-1")


def main() -> int:
    raw, ents = read_big(DATA)
    amap = {}
    removed = []
    for name, off, size in ents:
        k = key(name)
        blob = raw[off : off + size]
        if k in REMOVE_DATA:
            removed.append(name)
            continue
        if k == "data\\ini\\commandset.ini" or k == "data\\ini\\commandbutton.ini" or k.endswith(
            "commandset_factionexpansion_armies.ini"
        ):
            blob = patch_ini_bytes(blob, name)
        amap[name] = blob
    if sorted(key(n) for n in removed) != sorted(REMOVE_DATA & {key(n) for n in removed}):
        pass
    missing = REMOVE_DATA - {key(n) for n in removed}
    # CommandButton_USAPAC3.ini may be absent
    missing -= {"data\\ini\\commandbutton_usapac3.ini"}
    if missing:
        fail(f"DATA remove missing {missing}")
    out = build_big(amap)
    DATA.write_bytes(out)
    print("DATA removed", removed)
    print("DATA", sha_file(DATA), DATA.stat().st_size, "entries", len(amap))

    raw, ents = read_big(ART2)
    amap = {}
    removed_art = []
    for name, off, size in ents:
        k = key(name)
        if k in REMOVE_ART:
            removed_art.append(name)
            continue
        amap[name] = raw[off : off + size]
        if k in KEEP_ART:
            pass
    miss_art = REMOVE_ART - {key(n) for n in removed_art}
    if miss_art:
        fail(f"ART TWO remove missing {miss_art}")
    for keep in KEEP_ART:
        if keep not in {key(n) for n in amap}:
            fail(f"shared ART missing after cleanup {keep}")
    ART2.write_bytes(build_big(amap))
    print("ART2 removed", removed_art)
    print("ART2", sha_file(ART2), ART2.stat().st_size, "entries", len(amap))

    # loose ControlBar copies (first-wins)
    CS_LOOSE.write_bytes(patch_ini_bytes(CS_LOOSE.read_bytes(), "CommandSet.ini"))
    CB_LOOSE.write_bytes(patch_ini_bytes(CB_LOOSE.read_bytes(), "CommandButton.ini"))
    print("loose CommandSet", sha_file(CS_LOOSE))
    print("loose CommandButton", sha_file(CB_LOOSE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
