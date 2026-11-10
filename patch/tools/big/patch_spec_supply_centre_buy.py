#!/usr/bin/env python3
"""Restore France/USA/China/Russia Supply Centre buy lists in SPEC DATA.

Root cause (effective last-wins, including 0_SPECTER_CountrySupplyIncome.big):

* FranceSupplyCenterCommandSet is sell-only. Other NATO Supply Centres buy
  CH47F; Command_ConstructFranceHelicopterCH47F / FranceHelicopterCH47F exist.
  Overlay spawn already uses FranceHelicopterCH47F, but the CommandSet never
  got the construct button.

* America / China / Russia overlay (0_SPECTER_CountrySupplyIncome.big) assigns
  *_CountryIncome CommandSets and Russia/USA-side harvester objects. Those
  overlay files share SupplyCenter.ini paths with _SPEC_DATA_ONE.big. ASCII
  load order parses 0_* first, then _SPEC_DATA_ONE, so SPEC same-path last-win
  disconnects the overlay CommandSets:

    America -> AmericaVehicleChinook instead of AmericaSupplyChinook_USA
    Russia  -> ChinaVehicleSupplyTruck (Side=China) instead of
               RussiaSupplyTruck_CountryIncome (Side=Russia)
    China   -> original CommandSet name (buttons already match)

This rebuild last-wins both CommandSet names for each country so either
building assignment still shows the designed buy list, and packs the overlay
harvester objects + construct buttons so the chain works from SPEC DATA alone.

Does not change other countries, Global Market, construct cameos, four drones,
92N6E/HT-233, or Iraq radar. ART BIG untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    fm: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        fm[name] = data[off : off + size]
    return fm


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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def last_win_block(file_map: dict[str, bytes], kind: str, name: str) -> tuple[str | None, str | None]:
    pat = re.compile(
        rf"(?m)^{kind}\s+{re.escape(name)}\b.*?(?=^(?:Object|Weapon|Armor|CommandButton|CommandSet|ObjectCreationList|Upgrade|SpecialPower)\s|\Z)",
        re.S,
    )
    last = None
    src = None
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        text = raw.decode("latin1")
        for m in pat.finditer(text):
            last = m.group(0)
            src = path
    return src, last


def slots(body: str | None) -> list[tuple[str, str]]:
    if not body:
        return []
    return re.findall(r"(?m)^\s*(\d+)\s*=\s*(\S+)", body)


COMMANDSET_ZZZZ = """\
; SPECTER last-win inside _SPEC_DATA_ONE.big.
; Restores Supply Centre UNIT_BUILD lists for France, America, China, Russia.
; Sorts after CommandSet.ini / CommandSet_France.ini / overlay
; CommandSet_CountrySupplyIncome.ini. Both original and overlay CommandSet
; names are last-won so either SupplyCenter.ini assignment still works.
; Other countries are not redefined here.

CommandSet FranceSupplyCenterCommandSet
  1 = Command_ConstructFranceHelicopterCH47F
 14 = Command_Sell
End

CommandSet AmericaSupplyCenterCommandSet
  1 = Command_ConstructAmericaSupplyChinook_USA
 13 = Command_SetRallyPoint
 14 = Command_Sell
 16 = Command_ConstructAmericaVehicleM-ATV_AI
End

CommandSet AmericaSupplyCenterCommandSet_CountryIncome
  1 = Command_ConstructAmericaSupplyChinook_USA
 13 = Command_SetRallyPoint
 14 = Command_Sell
 16 = Command_ConstructAmericaVehicleM-ATV_AI
End

CommandSet ChinaSupplyCenterCommandSet
  1 = Command_ConstructChinaVehicleSupplyTruck
 13 = Command_SetRallyPoint
 14 = Command_Sell
End

CommandSet ChinaSupplyCenterCommandSet_CountryIncome
  1 = Command_ConstructChinaVehicleSupplyTruck
 13 = Command_SetRallyPoint
 14 = Command_Sell
End

CommandSet RussiaSupplyCenterCommandSet
  1 = Command_ConstructRussiaSupplyTruck_CountryIncome
  2 = Command_ConstructRussiaHelicopterMi8AMTSh
 14 = Command_Sell
End

CommandSet RussiaSupplyCenterCommandSet_CountryIncome
  1 = Command_ConstructRussiaSupplyTruck_CountryIncome
  2 = Command_ConstructRussiaHelicopterMi8AMTSh
 14 = Command_Sell
End
"""

COMMANDBUTTON_ZZZZ = """\
; SPECTER last-win. Overlay 0_SPECTER_CountrySupplyIncome.big already defines
; these buttons on a unique path; packing them here keeps the USA/Russia
; Supply Centre buy list valid when only _SPEC_DATA_ONE.big is installed.

CommandButton Command_ConstructAmericaSupplyChinook_USA
  Command       = UNIT_BUILD
  Object        = AmericaSupplyChinook_USA
  TextLabel     = CONTROLBAR:ConstructAmericaVehicleChinook
  ButtonImage   = SAChinook
  ButtonBorderType        = BUILD
  DescriptLabel           = CONTROLBAR:ToolTipUSABUildChinook
End

CommandButton Command_ConstructRussiaSupplyTruck_CountryIncome
  Command       = UNIT_BUILD
  Object        = RussiaSupplyTruck_CountryIncome
  TextLabel     = CONTROLBAR:ConstructChinaVehicleSupplyTruck
  ButtonImage   = SNSupplyTruck
  ButtonBorderType        = BUILD
  DescriptLabel           = CONTROLBAR:ToolTipChinaBuildSupplyTruck
End
"""

PRESERVE_COMMANDSETS = [
    "Iraq_RadarStationCommandSet",
    "Command_ConstructRussian_92N6E",
    "Command_ConstructChinaVehicleHT233",
    "Command_ConstructSpecterRadarHeron",
    "Command_ConstructIraq_MIC_S400",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--src",
        default="patch/Release/CONSTRUCT_BUTTON_IMAGES/_SPEC_DATA_ONE.big",
        type=Path,
    )
    ap.add_argument(
        "--dst",
        default="patch/Release/SUPPLY_CENTRE_BUY_LIST/_SPEC_DATA_ONE.big",
        type=Path,
    )
    args = ap.parse_args()

    root = Path("patch/Data/INI/Object/Specter/PatchSystems/Economy/CountrySupplyIncome")
    usa_obj = (root / "AmericaSupplyChinook_USA.ini").read_bytes()
    rus_obj = (root / "RussiaSupplyTruck_CountryIncome.ini").read_bytes()

    fm = read_big(args.src)
    before_count = len(fm)

    fm[r"Data\INI\CommandSet_ZZZZ_ZZZZSupplyCentreBuy.ini"] = COMMANDSET_ZZZZ.replace("\n", "\r\n").encode("latin1")
    fm[r"Data\INI\CommandButton_ZZZZ_ZZZZSupplyCentreBuy.ini"] = COMMANDBUTTON_ZZZZ.replace("\n", "\r\n").encode("latin1")
    fm[r"Data\INI\Object\zzzzz_SpecterSupplyCentreBuy\AmericaSupplyChinook_USA.ini"] = usa_obj
    fm[r"Data\INI\Object\zzzzz_SpecterSupplyCentreBuy\RussiaSupplyTruck_CountryIncome.ini"] = rus_obj

    blob = build_big(fm)
    args.dst.parent.mkdir(parents=True, exist_ok=True)
    args.dst.write_bytes(blob)
    digest = sha256(args.dst)
    (args.dst.parent / "_SPEC_DATA_ONE.big.sha256").write_text(digest + "\n", encoding="ascii")

    chk = read_big(args.dst)

    report: dict = {
        "src": str(args.src),
        "dst": str(args.dst),
        "src_entries": before_count,
        "dst_entries": len(chk),
        "size": args.dst.stat().st_size,
        "sha256": digest,
        "art_untouched": True,
        "countries": {},
        "preserved": {},
    }

    expected = {
        "France": {
            "object": "FranceSupplyCenter",
            "sets": ["FranceSupplyCenterCommandSet"],
            "buy": {
                "Command_ConstructFranceHelicopterCH47F": "FranceHelicopterCH47F",
            },
        },
        "America": {
            "object": "AmericaSupplyCenter",
            "sets": [
                "AmericaSupplyCenterCommandSet",
                "AmericaSupplyCenterCommandSet_CountryIncome",
            ],
            "buy": {
                "Command_ConstructAmericaSupplyChinook_USA": "AmericaSupplyChinook_USA",
                "Command_ConstructAmericaVehicleM-ATV_AI": "AmericaVehicleM-ATV_AI",
            },
        },
        "China": {
            "object": "ChinaSupplyCenter",
            "sets": [
                "ChinaSupplyCenterCommandSet",
                "ChinaSupplyCenterCommandSet_CountryIncome",
            ],
            "buy": {
                "Command_ConstructChinaVehicleSupplyTruck": "ChinaVehicleSupplyTruck",
            },
        },
        "Russia": {
            "object": "RussiaSupplyCenter",
            "sets": [
                "RussiaSupplyCenterCommandSet",
                "RussiaSupplyCenterCommandSet_CountryIncome",
            ],
            "buy": {
                "Command_ConstructRussiaSupplyTruck_CountryIncome": "RussiaSupplyTruck_CountryIncome",
                "Command_ConstructRussiaHelicopterMi8AMTSh": "RussiaHelicopterMi8AMTSh",
            },
        },
    }

    errors: list[str] = []
    for country, spec in expected.items():
        src, body = last_win_block(chk, "Object", spec["object"])
        cs = None
        if body:
            m = re.search(r"(?im)^\s*CommandSet\s*=\s*(\S+)", body)
            cs = m.group(1) if m else None
        csets = {}
        for name in spec["sets"]:
            ssrc, sbody = last_win_block(chk, "CommandSet", name)
            csets[name] = {"src": ssrc, "slots": slots(sbody)}
            if not ssrc or "ZZZZSupplyCentreBuy" not in (ssrc or ""):
                errors.append(f"{country} CommandSet {name} last-win is {ssrc}")
        buys = {}
        for btn, obj in spec["buy"].items():
            bsrc, bbody = last_win_block(chk, "CommandButton", btn)
            osrc, obody = last_win_block(chk, "Object", obj)
            bobj = None
            if bbody:
                m = re.search(r"(?im)^\s*Object\s*=\s*(\S+)", bbody)
                bobj = m.group(1) if m else None
            buys[btn] = {
                "button_src": bsrc,
                "button_object": bobj,
                "object_src": osrc,
                "object_defined": bool(obody),
            }
            if bobj != obj:
                errors.append(f"{country} {btn} Object={bobj} expected {obj}")
            if not obody:
                errors.append(f"{country} missing Object {obj}")
        # slot collision check
        for name, rec in csets.items():
            seen = {}
            for slot, cmd in rec["slots"]:
                if slot in seen:
                    errors.append(f"{country} {name} duplicate slot {slot}")
                seen[slot] = cmd
        report["countries"][country] = {
            "building_src": src,
            "building_commandset": cs,
            "commandsets": csets,
            "buttons": buys,
        }

    # Prior last-wins must still be the same files as the construct-button BIG.
    src_fm = read_big(args.src)
    for name in [
        "Iraq_RadarStationCommandSet",
        "Iraq_RadarStation",
        "Command_ConstructRussian_92N6E",
        "Command_ConstructChinaVehicleHT233",
        "Command_ConstructSpecterRadarHeron",
        "Command_ConstructIraq_MIC_S400",
        "Command_ConstructAmerica_MIC_S400",
        "BritainSupplyCenterCommandSet",
        "GermanySupplyCenterCommandSet",
        "IranSupplyCenterCommandSet",
        "Iraq_SupplyCenterCommandSet",
    ]:
        kind = "CommandSet" if name.endswith("CommandSet") else ("CommandButton" if name.startswith("Command_") else "Object")
        a = last_win_block(src_fm, kind, name)
        b = last_win_block(chk, kind, name)
        report["preserved"][name] = {"src": a[0], "dst": b[0], "same": (a[1] == b[1])}
        if a[1] != b[1]:
            errors.append(f"preserved last-win changed: {name}")

    # Other-country Supply Centres must keep the same CommandSet last-win body.
    for name in [
        "BritainSupplyCenterCommandSet",
        "GermanySupplyCenterCommandSet",
        "ItalySupplyCenterCommandSet",
        "NatoSupplyCenterCommandSet",
        "SwedenSupplyCenterCommandSet",
        "TurkeySupplyCenterCommandSet",
        "UkraineSupplyCenterCommandSet",
        "IranSupplyCenterCommandSet",
        "Iraq_SupplyCenterCommandSet",
        "Japan_SupplyCenterCommandSet",
    ]:
        a = last_win_block(src_fm, "CommandSet", name)
        b = last_win_block(chk, "CommandSet", name)
        if a[1] != b[1]:
            errors.append(f"other-country CommandSet changed: {name}")

    report["errors"] = errors
    (args.dst.parent / "patch_summary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    (args.dst.parent / "DOWNLOAD.txt").write_text(
        f"sha256 {digest}\nsize {args.dst.stat().st_size}\n", encoding="ascii"
    )

    print(json.dumps({k: report[k] for k in ("dst", "size", "sha256", "dst_entries", "errors")}, indent=2))
    if errors:
        raise SystemExit("validation failed:\n  " + "\n  ".join(errors))


if __name__ == "__main__":
    main()
