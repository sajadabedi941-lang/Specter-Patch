#!/usr/bin/env python3
"""Assemble the SPECTER unified install pack from the proven #722 chain.

Does not stack old DATA BIGs. Source DATA is the #722 rebuild of the #720
cc-vt72b-nk-hwasong BIG (which already carries #718 WF strip, #719 spy-sat
clear, AD cap 3, Shahed range 3000, factory K/L/M/N). Overlays #721 and #722
are copied as separate 0_ archives with unique Art\\Textures paths.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DATA = ROOT / "Release/MISSILE_JLMN_BUTTONS/_SPEC_DATA_ONE.big"
SRC_DATA_SHA = "c775c5cc5ae7ca1a4cb717b061c387ad044a737a19989b15496b88f6172da8ac"
SRC_CS = ROOT / "Release/MISSILE_JLMN_BUTTONS/CommandSet.ini"
SRC_CS_SHA = "a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87"
SRC_CB = ROOT / "Release/MISSILE_JLMN_BUTTONS/CommandButton.ini"
SRC_CB_SHA = "60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba"
SRC_GS = ROOT / "Release/GS_CAMEO_RESTORE/0_SPECTER_GlobalStoreCameos.big"
SRC_GS_SHA = "1ac22af21f78515b7a3eafdf72b2f8ecdb2c15f1ed196963ff9c3cc0706c59fc"
SRC_MS = ROOT / "Release/MISSILE_JLMN_BUTTONS/0_SPECTER_MissileJLMNCameos.big"
SRC_MS_SHA = "618c6dabb192b8033f074a005e5141af2a756182be746d71f2c2fdda125fbfae"
OUT = ROOT / "Release/SPECTER_UNIFIED"
ZIP_NAME = "SPECTER_UNIFIED_INSTALL.zip"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("VALIDATE FAIL: " + msg)


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    require(data[:4] == b"BIGF", f"not BIGF {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    total = struct.unpack_from(">I", data, 4)[0]
    require(total == len(data), f"BIG size field {total} != {len(data)}")
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def big_names(path: Path) -> set[str]:
    return set(read_big(path))


def main() -> None:
    files = {
        SRC_DATA: SRC_DATA_SHA,
        SRC_CS: SRC_CS_SHA,
        SRC_CB: SRC_CB_SHA,
        SRC_GS: SRC_GS_SHA,
        SRC_MS: SRC_MS_SHA,
    }
    for path, expect in files.items():
        require(path.is_file(), f"missing {path}")
        got = sha256(path)
        require(got == expect, f"sha mismatch {path.name}: {got}")

    data_map = read_big(SRC_DATA)
    cs = data_map[r"Data\INI\CommandSet.ini"]
    cb = data_map[r"Data\INI\CommandButton.ini"]
    require(hashlib.sha256(cs).hexdigest() == SRC_CS_SHA, "DATA CommandSet.ini != loose")
    require(hashlib.sha256(cb).hexdigest() == SRC_CB_SHA, "DATA CommandButton.ini != loose")
    require(cs == SRC_CS.read_bytes(), "CS bytes drift")
    require(cb == SRC_CB.read_bytes(), "CB bytes drift")

    cs_txt = cs.decode("latin1")
    cb_txt = cb.decode("latin1")

    # #720 CC
    require("Command_ConstructJapan_VT72B" in cs_txt, "#720 JP")
    require("Command_ConstructVietnam_VT72B" in cs_txt, "#720 VN")
    require("Command_ConstructSouthKorea_VT72B" in cs_txt, "#720 SK")
    require("Command_ConstructNorthKorea_Hwasong15BB" in cs_txt, "#720 NK")
    jp = re.search(r"(?m)^CommandSet Japan_CommandCenterCommandSet\r?\n[\s\S]*?^End", cs_txt)
    require(jp is not None and "VT72B" in jp.group(0), "JP CC")

    # #719: live country radars in CommandSet.ini must not offer Spy Sat.
    # Stock USA / shortcut buttons may still exist; they are not those 12 radars.
    radar_no_spy = (
        "Iraq_RadarStationCommandSet",
        "AmericaRadarStationCommandSet",
        "IranRadarStationCommandSet",
        "RussiaRadarStationCommandSet",
        "ChinaRadarStationCommandSet",
        "IsraelRadarStationCommandSet",
        "Pakistan_RadarCommandSet",
        "SaudiArabia_RadarCommandSet",
        "UAE_RadarCommandSet",
        "India_RadarCommandSet",
        "Syria_RadarCommandSet",
        "Libya_RadarCommandSet",
        "SouthAfrica_RadarCommandSet",
        "SouthKorea_RadarStationCommandSet",
        "Japan_RadarStationCommandSet",
        "Vietnam_RadarStationCommandSet",
        "NorthKorea_RadarStationCommandSet",
    )
    for name in radar_no_spy:
        m = re.search(rf"(?m)^CommandSet {re.escape(name)}\s*(?:;.*)?\r?\n([\s\S]*?)^End", cs_txt)
        if not m:
            continue
        require("SpySatellite" not in m.group(0), f"#719 {name} still has SpySatellite")

    # #718 live WF objects
    ru = data_map[r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\Warfactory.ini"].decode("latin1")
    cn = data_map[r"Data\INI\Object\Specter\PLA\Buildings\Warfactory.ini"].decode("latin1")
    ir = data_map[r"Data\INI\Object\Specter\Iranian Army\Buildings\Warfactory.ini"].decode("latin1")
    require("RussiaWarFactoryCommandSet" in ru, "RU WF CS")
    require("PLAWarFactoryCommandSet" in cn, "CN WF CS")
    require("IranWarfactoryCommandSet" in ir, "IR WF CS")
    pla = re.search(r"(?m)^CommandSet PLAWarFactoryCommandSet\r?\n[\s\S]*?^End", cs_txt).group(0)
    irwf = re.search(r"(?m)^CommandSet IranWarfactoryCommandSet\r?\n[\s\S]*?^End", cs_txt).group(0)
    ruwf = re.search(r"(?m)^CommandSet RussiaWarFactoryCommandSet\r?\n[\s\S]*?^End", cs_txt).group(0)
    require("DF41" not in pla and "RS24" not in pla, "#718 PLA WF")
    require("Khormshar" not in irwf, "#718 Iran WF")
    require("RS24" not in ruwf and "VehicleRS24" not in ruwf, "#718 RU WF")

    # #721 / #722 images
    require(cb_txt.count("ButtonImage   = Neon") == 25, "J Neon count")
    require("ButtonImage   = Futuristic" in cb_txt, "L Futuristic")
    require("ButtonImage   = Nuclear" in cb_txt, "M Nuclear")
    require("ButtonImage   = pla_df41" in cb_txt, "N pla_df41")
    require("specbtn_mic_s400" in cb_txt, "GS shop image")
    require("Button_GlobalMarket" in cb_txt, "GS building image")
    require(r"Data\INI\MappedImages\HandCreated\zSpecterJLMN_Images.INI" in data_map, "JLMN mapped")

    gs = big_names(SRC_GS)
    ms = big_names(SRC_MS)
    require(gs & ms == set(), "overlay path overlap")
    require(all(n.startswith(r"Art\Textures\\") or n.startswith("Art\\Textures\\") for n in gs | ms), "overlay not textures")
    require(r"Art\Textures\Button_GlobalMarket.tga" in gs, "GS TGA")
    require(r"Art\Textures\specbtn_mic_s400.tga" in gs, "GS S400 TGA")
    require(r"Art\Textures\specter_missile_j.tga" in ms, "J TGA")
    require(r"Art\Textures\specter_missile_l.tga" in ms, "L TGA")
    require(r"Art\Textures\specter_missile_m.tga" in ms, "M TGA")
    require("0_SPECTER_GlobalStoreCameos.big" < "0_SPECTER_MissileJLMNCameos.big", "overlay sort")
    require("0_SPECTER_GlobalStoreCameos.big" < "_SPEC_ART_ONE.big", "GS before ART ONE")

    # factory slots still present
    require("CB_FACTORY_SLOT_L" in cs_txt and "CB_FACTORY_SLOT_N" in cs_txt, "factory L/N")
    require("Iraq_AlFahdMissileFactoryCommandSet" in cs_txt, "Iraq factory")

    OUT.mkdir(parents=True, exist_ok=True)
    copies = {
        "_SPEC_DATA_ONE.big": SRC_DATA,
        "CommandSet.ini": SRC_CS,
        "CommandButton.ini": SRC_CB,
        "0_SPECTER_GlobalStoreCameos.big": SRC_GS,
        "0_SPECTER_MissileJLMNCameos.big": SRC_MS,
    }
    lines = []
    for name, src in copies.items():
        dest = OUT / name
        if dest.resolve() != src.resolve():
            shutil.copy2(src, dest)
        digest = sha256(dest)
        lines.append(f"{digest}  {name}")
        (OUT / f"{name}.sha256").write_text(digest + "\n", encoding="ascii")
        print(name, dest.stat().st_size, digest)

    (OUT / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii")

    zip_path = OUT / ZIP_NAME
    payload = [
        "_SPEC_DATA_ONE.big",
        "CommandSet.ini",
        "CommandButton.ini",
        "0_SPECTER_GlobalStoreCameos.big",
        "0_SPECTER_MissileJLMNCameos.big",
        "Install_SpecterUnified.bat",
        "Restore_SpecterUnifiedBackup.bat",
        "README_INSTALL.txt",
        "SHA256SUMS.txt",
        "UNIFIED_RELEASE_REPORT.md",
    ]
    # installer/readme may be written after this script; zip in a second pass if missing
    present = [n for n in payload if (OUT / n).is_file()]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for name in present:
            print("zip", name)
            zf.write(OUT / name, arcname=f"SPECTER_UNIFIED_INSTALL/{name}")
    print("ZIP", zip_path.stat().st_size, sha256(zip_path))
    (OUT / f"{ZIP_NAME}.sha256").write_text(sha256(zip_path) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
