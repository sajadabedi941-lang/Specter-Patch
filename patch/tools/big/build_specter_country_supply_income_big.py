#!/usr/bin/env python3
"""Build first-wins overlay 0_SPECTER_CountrySupplyIncome.big.

SAGE pays supply cash as:
    boxes_delivered * GameData.ValuePerSupplyBox
ValuePerSupplyBox is global. Per-country delivery amounts are applied by
giving each country a unique gatherer MaxBoxes so that:
    MaxBoxes * 25 = target dollars per full equivalent dump.

This overlay first-wins (filename starts with 0_) over INIZH.big and
_SPEC_DATA_ONE.big. It does not rebuild ART, missiles, or _SPEC_DATA_ONE.big.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_DATA = Path("/tmp/specter_accepted_release/_SPEC_DATA_ONE.big")
DEFAULT_OUT = Path(
    "/workspace/patch/tools/installer/0_SPECTER_CountrySupplyIncome.big"
)
DEFAULT_REPORT = Path(
    "/workspace/patch/tools/installer/COUNTRY_SUPPLY_INCOME_REPORT.json"
)

VPSB = 25  # common divisor of every requested delivery amount

# country, target $, packed supply-center path, current spawn, unique spawn, gatherer files
COUNTRIES = [
    {
        "country": "USA",
        "target": 1000,
        "center_path": r"Data\INI\Object\Specter\United States Of America\Buildings\SupplyCenter.ini",
        "center_object": "AmericaSupplyCenter",
        "spawn_from": "AmericaVehicleChinook",
        "spawn_to": "AmericaSupplyChinook_USA",
        "gatherers": [],  # clone handled separately
        "commandset": "AmericaSupplyCenterCommandSet",
        "commandset_to": "AmericaSupplyCenterCommandSet_CountryIncome",
        "construct_old": "Command_ConstructAmericaVehicleChinook",
        "construct_new": "Command_ConstructAmericaSupplyChinook_USA",
        "clone_from_path": r"Data\INI\Object\Specter\United States Of America\Airforce\CH47F.ini",
        "clone_from_object": "AmericaVehicleChinook",
        "clone_object": "AmericaSupplyChinook_USA",
        "clone_path": r"Data\INI\Object\Specter\PatchSystems\Economy\CountrySupplyIncome\AmericaSupplyChinook_USA.ini",
        "clone_side": "America",
        "button_src": "Command_ConstructAmericaVehicleChinook",
    },
    {
        "country": "China",
        "target": 950,
        "center_path": r"Data\INI\Object\Specter\PLA\Buildings\SupplyCenter.ini",
        "center_object": "ChinaSupplyCenter",
        "spawn_from": "ChinaVehicleSupplyTruck",
        "spawn_to": "ChinaVehicleSupplyTruck",
        "gatherers": [],  # extracted China truck object with new MaxBoxes
        "commandset": "ChinaSupplyCenterCommandSet",
        "commandset_to": "ChinaSupplyCenterCommandSet_CountryIncome",
        "construct_old": "Command_ConstructChinaVehicleSupplyTruck",
        "construct_new": "Command_ConstructChinaVehicleSupplyTruck",
        "extract_truck": True,
    },
    {
        "country": "Germany",
        "target": 900,
        "center_path": r"Data\INI\Object\Specter\German Armed Forces\Buildings\SupplyCenter.ini",
        "center_object": "GermanySupplyCenter",
        "spawn_from": "AmericaVehicleChinook",
        "spawn_to": "GermanyHelicopterCH47F",
        "gatherers": [
            r"Data\INI\Object\Specter\German Armed Forces\Rotary\CH47F.ini",
        ],
    },
    {
        "country": "Japan",
        "target": 875,
        "center_path": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_SupplyCenter.ini",
        "center_object": "Japan_SupplyCenter",
        "spawn_from": "Japan_Ural375_Supply",
        "spawn_to": "Japan_Ural375_Supply",
        "gatherers": [
            r"Data\INI\Object\Specter\Japan Self-Defense Forces\Wheeled\Japan_Ural375_Supply.ini",
        ],
    },
    {
        "country": "Britain",
        "target": 850,
        "center_path": r"Data\INI\Object\Specter\British Armed Forces\Buildings\SupplyCenter.ini",
        "center_object": "BritainSupplyCenter",
        "spawn_from": "AmericaVehicleChinook",
        "spawn_to": "BritainHelicopterCH47F",
        "gatherers": [
            r"Data\INI\Object\Specter\British Armed Forces\Rotary\CH47F.ini",
        ],
    },
    {
        "country": "India",
        "target": 825,
        "center_path": r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_SupplyCenter.ini",
        "center_object": "India_SupplyCenter",
        "spawn_from": "India_Ural375_Supply",
        "spawn_to": "India_Ural375_Supply",
        "gatherers": [
            r"Data\INI\Object\Specter\Indian Armed Forces\Wheeled\India_Ural375_Supply.ini",
            r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\India_Mi-8.ini",
        ],
    },
    {
        "country": "France",
        "target": 800,
        "center_path": r"Data\INI\Object\Specter\French Armed Forces\Buildings\SupplyCenter.ini",
        "center_object": "FranceSupplyCenter",
        "spawn_from": "AmericaVehicleChinook",
        "spawn_to": "FranceHelicopterCH47F",
        "gatherers": [
            r"Data\INI\Object\Specter\French Armed Forces\Rotary\CH47F.ini",
        ],
    },
    {
        "country": "Russia",
        "target": 775,
        "center_path": r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\SupplyCenter.ini",
        "center_object": "RussiaSupplyCenter",
        "spawn_from": "ChinaVehicleSupplyTruck",
        "spawn_to": "RussiaSupplyTruck_CountryIncome",
        "gatherers": [],
        "commandset": "RussiaSupplyCenterCommandSet",
        "commandset_to": "RussiaSupplyCenterCommandSet_CountryIncome",
        "construct_old": "Command_ConstructChinaVehicleSupplyTruck",
        "construct_new": "Command_ConstructRussiaSupplyTruck_CountryIncome",
        "clone_from_object": "ChinaVehicleSupplyTruck",
        "clone_from_china_ini": True,
        "clone_object": "RussiaSupplyTruck_CountryIncome",
        "clone_path": r"Data\INI\Object\Specter\PatchSystems\Economy\CountrySupplyIncome\RussiaSupplyTruck_CountryIncome.ini",
        "clone_side": "Russia",
        "button_src": "Command_ConstructChinaVehicleSupplyTruck",
    },
    {
        "country": "Italy",
        "target": 750,
        "center_path": r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\SupplyCenter.ini",
        "center_object": "ItalySupplyCenter",
        "spawn_from": "AmericaVehicleChinook",
        "spawn_to": "ItalyHelicopterCH47F",
        "gatherers": [
            r"Data\INI\Object\Specter\Italian Armed Forces\Rotary\CH47F.ini",
        ],
    },
    {
        "country": "Spain",
        "target": 725,
        "center_path": r"Data\INI\Object\Specter\NATO\Buildings\SupplyCenter.ini",
        "center_object": "NatoSupplyCenter",
        "spawn_from": "AmericaVehicleChinook",
        "spawn_to": "NatoHelicopterCH47F",
        "gatherers": [
            r"Data\INI\Object\Specter\NATO\Rotary\CH47F.ini",
        ],
    },
    {
        "country": "South Korea",
        "target": 700,
        "center_path": r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_SupplyCenter.ini",
        "center_object": "SouthKorea_SupplyCenter",
        "spawn_from": "SouthKorea_Ural375_Supply",
        "spawn_to": "SouthKorea_Ural375_Supply",
        "gatherers": [
            r"Data\INI\Object\Specter\South Korean Armed Forces\Wheeled\SouthKorea_Ural375_Supply.ini",
        ],
    },
    {
        "country": "Turkey",
        "target": 675,
        "center_path": r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\SupplyCenter.ini",
        "center_object": "TurkeySupplyCenter",
        "spawn_from": "AmericaVehicleChinook",
        "spawn_to": "TurkeyHelicopterCH47F",
        "gatherers": [
            r"Data\INI\Object\Specter\Turkish Armed Forces\Rotary\CH47F.ini",
        ],
    },
    {
        "country": "Saudi Arabia",
        "target": 650,
        "center_path": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_SupplyCenter.ini",
        "center_object": "SaudiArabia_SupplyCenter",
        "spawn_from": "SaudiArabia_Ural375_Supply",
        "spawn_to": "SaudiArabia_Ural375_Supply",
        "gatherers": [
            r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Wheeled\SaudiArabia_Ural375_Supply.ini",
            r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiArabia_Mi-8.ini",
        ],
    },
    {
        "country": "Sweden",
        "target": 625,
        "center_path": r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\SupplyCenter.ini",
        "center_object": "SwedenSupplyCenter",
        "spawn_from": "AmericaVehicleChinook",
        "spawn_to": "SwedenHelicopterCH47F",
        "gatherers": [
            r"Data\INI\Object\Specter\Swedish Armed Forces\Rotary\CH47F.ini",
        ],
    },
    {
        "country": "Israel",
        "target": 600,
        "center_path": r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Supply.ini",
        "center_object": "AirF_AmericaSupplyCenter",
        "spawn_from": "AFG_AmericaVehicleChinook",
        "spawn_to": "AFG_AmericaVehicleChinook",
        "gatherers": [
            r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\UH60.ini",
        ],
    },
    {
        "country": "UAE",
        "target": 575,
        "center_path": r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_SupplyCenter.ini",
        "center_object": "UAE_SupplyCenter",
        "spawn_from": "UAE_Ural375_Supply",
        "spawn_to": "UAE_Ural375_Supply",
        "gatherers": [
            r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Wheeled\UAE_Ural375_Supply.ini",
            r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Airforce\UAE_Mi-8.ini",
        ],
    },
    {
        "country": "Vietnam",
        "target": 550,
        "center_path": r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_SupplyCenter.ini",
        "center_object": "Vietnam_SupplyCenter",
        "spawn_from": "Vietnam_Ural375_Supply",
        "spawn_to": "Vietnam_Ural375_Supply",
        "gatherers": [
            r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Wheeled\Vietnam_Ural375_Supply.ini",
        ],
    },
    {
        "country": "South Africa",
        "target": 525,
        "center_path": r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_SupplyCenter.ini",
        "center_object": "SouthAfrica_SupplyCenter",
        "spawn_from": "SouthAfrica_Ural375_Supply",
        "spawn_to": "SouthAfrica_Ural375_Supply",
        "gatherers": [
            r"Data\INI\Object\Specter\South African National Defence Force\Wheeled\SouthAfrica_Ural375_Supply.ini",
        ],
    },
    {
        "country": "Pakistan",
        "target": 500,
        "center_path": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_SupplyCenter.ini",
        "center_object": "Pakistan_SupplyCenter",
        "spawn_from": "Pakistan_Ural375_Supply",
        "spawn_to": "Pakistan_Ural375_Supply",
        "gatherers": [
            r"Data\INI\Object\Specter\Pakistan Armed Forces\Wheeled\Pakistan_Ural375_Supply.ini",
            r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\Pakistan_Mi-8.ini",
        ],
    },
    {
        "country": "Iran",
        "target": 475,
        "center_path": r"Data\INI\Object\Specter\Iranian Army\Buildings\SupplyCenter.ini",
        "center_object": "IranSupplyCenter",
        "spawn_from": "IranVehicleUral375",
        "spawn_to": "IranVehicleUral375",
        "gatherers": [
            r"Data\INI\Object\Specter\Iranian Army\Wheeled\Ural.ini",
        ],
        "gatherer_objects": ["IranVehicleUral375"],
    },
    {
        "country": "Iraq",
        "target": 450,
        "center_path": r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_SupplyCenter.ini",
        "center_object": "Iraq_SupplyCenter",
        "spawn_from": "Iraq_Ural375_Supply",
        "spawn_to": "Iraq_Ural375_Supply",
        "gatherers": [
            r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_Ural375_Supply.ini",
            r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Mi-8.ini",
        ],
    },
    {
        "country": "Ukraine",
        "target": 425,
        "center_path": r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\SupplyCenter.ini",
        "center_object": "UkraineSupplyCenter",
        "spawn_from": "AmericaVehicleChinook",
        "spawn_to": "UkraineHelicopterCH47F",
        "gatherers": [
            r"Data\INI\Object\Specter\Ukrainian Armed Forces\Rotary\CH47F.ini",
        ],
    },
    {
        "country": "Libya",
        "target": 400,
        "center_path": r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_SupplyCenter.ini",
        "center_object": "Libya_SupplyCenter",
        "spawn_from": "Libya_Ural375_Supply",
        "spawn_to": "Libya_Ural375_Supply",
        "gatherers": [
            r"Data\INI\Object\Specter\Libyan Armed Forces\Wheeled\Libya_Ural375_Supply.ini",
            r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\Libya_Mi-8.ini",
        ],
    },
    {
        "country": "North Korea",
        "target": 350,
        "center_path": r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_SupplyCenter.ini",
        "center_object": "NorthKorea_SupplyCenter",
        "spawn_from": "NorthKorea_Ural375_Supply",
        "spawn_to": "NorthKorea_Ural375_Supply",
        "gatherers": [
            r"Data\INI\Object\Specter\North Korea\Wheeled\NorthKorea_Ural375_Supply.ini",
        ],
    },
    {
        "country": "Syria",
        "target": 300,
        "center_path": r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_SupplyCenter.ini",
        "center_object": "Syria_SupplyCenter",
        "spawn_from": "Syria_Ural375_Supply",
        "spawn_to": "Syria_Ural375_Supply",
        "gatherers": [
            r"Data\INI\Object\Specter\Syrian Armed Forces\Wheeled\Syria_Ural375_Supply.ini",
            r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\Syria_Mi-8.ini",
        ],
    },
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


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


def big_map(entries, raw) -> dict[str, bytes]:
    return {name: raw[off : off + size] for name, off, size in entries}


def to_text(blob: bytes) -> str:
    return blob.decode("latin1", errors="replace")


def to_bytes(text: str) -> bytes:
    return text.encode("latin1", errors="replace")


def extract_object(text: str, obj_name: str) -> str:
    m = re.search(
        rf"(?ms)^Object {re.escape(obj_name)}\s*\r?\n.*?(?=^Object |\Z)",
        text,
    )
    if not m:
        raise KeyError(f"Object {obj_name} not found")
    return m.group(0)


def extract_block(text: str, kind: str, name: str) -> str:
    m = re.search(
        rf"(?ms)^{kind} {re.escape(name)}\s*\r?\n.*?(?=^{kind} |\Z)",
        text,
    )
    if not m:
        raise KeyError(f"{kind} {name} not found")
    return m.group(0)


def set_max_boxes(text: str, boxes: int, objects: list[str] | None = None) -> str:
    if objects:
        out = []
        parts = re.split(r"(?m)^(?=Object \S+)", text)
        for part in parts:
            m = re.match(r"Object (\S+)", part)
            if m and m.group(1) in objects:
                part = re.sub(
                    r"(MaxBoxes\s*=\s*)\d+", rf"\g<1>{boxes}", part
                )
                part = re.sub(
                    r"(UpgradedSupplyBoost\s*=\s*)\d+", r"\g<1>0", part
                )
            out.append(part)
        return "".join(out)
    text = re.sub(r"(MaxBoxes\s*=\s*)\d+", rf"\g<1>{boxes}", text)
    text = re.sub(r"(UpgradedSupplyBoost\s*=\s*)\d+", r"\g<1>0", text)
    return text


def set_spawn(text: str, new_spawn: str) -> str:
    return re.sub(
        r"(SpawnTemplateName\s*=\s*)\S+",
        rf"\g<1>{new_spawn}",
        text,
        count=1,
    )


def set_commandset(text: str, new_set: str) -> str:
    return re.sub(
        r"(^\s*CommandSet\s*=\s*)\S+",
        rf"\g<1>{new_set}",
        text,
        count=1,
        flags=re.M,
    )


def rename_object(text: str, old: str, new: str) -> str:
    text = re.sub(rf"^Object {re.escape(old)}\b", f"Object {new}", text, count=1, flags=re.M)
    return text


def set_side(text: str, side: str) -> str:
    return re.sub(r"(^\s*Side\s*=\s*)\S+", rf"\g<1>{side}", text, count=1, flags=re.M)


def nl_join(lines: list[str], sample: str) -> str:
    nl = "\r\n" if "\r\n" in sample else "\n"
    body = nl.join(lines)
    if not body.endswith(nl):
        body += nl
    return body


def boxes_for(target: int) -> int:
    if target % VPSB:
        raise ValueError(f"target {target} not divisible by {VPSB}")
    return target // VPSB


def gatherer_stats(text: str) -> dict:
    boxes = re.findall(r"MaxBoxes\s*=\s*(\d+)", text)
    wh = re.findall(r"SupplyWarehouseActionDelay\s*=\s*(\d+)", text)
    sc = re.findall(r"SupplyCenterActionDelay\s*=\s*(\d+)", text)
    objs = re.findall(r"(?m)^Object (\S+)", text)
    return {
        "objects": objs,
        "MaxBoxes": [int(x) for x in boxes],
        "WarehouseDelayMS": [int(x) for x in wh],
        "CenterDelayMS": [int(x) for x in sc],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-big", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = ap.parse_args()

    entries, raw = read_big(args.data_big)
    packed = big_map(entries, raw)
    overlay: dict[str, bytes] = {}
    report = {
        "ValuePerSupplyBox": VPSB,
        "formula": "cash_per_full_dump = MaxBoxes * ValuePerSupplyBox",
        "source_data_big": str(args.data_big),
        "source_data_sha256": sha256_bytes(raw),
        "countries": [],
        "files": [],
    }

    gamedata_name = r"Data\INI\GameData.ini"
    gd = to_text(packed[gamedata_name])
    if "ValuePerSupplyBox = 75" not in gd and "ValuePerSupplyBox = 25" not in gd:
        raise SystemExit("unexpected GameData ValuePerSupplyBox")
    gd = gd.replace("ValuePerSupplyBox = 75", "ValuePerSupplyBox = 25")
    overlay[gamedata_name] = to_bytes(gd)

    # Keep shared AmericaVehicleChinook (UN / Taiwan / leftover spawns) at the
    # previous 8-box * 75 dump ($600) after VPSB becomes 25: 24 * 25 = 600.
    usa_chinook_path = r"Data\INI\Object\Specter\United States Of America\Airforce\CH47F.ini"
    usa_chinook = set_max_boxes(to_text(packed[usa_chinook_path]), 24)
    overlay[usa_chinook_path] = to_bytes(usa_chinook)

    # Egypt is not in the 25-country table. Keep its previous 7*75 and 8*75 dumps.
    preserve = (
        (
            r"Data\INI\Object\Specter\Egyptian Armed Forces\Wheeled\Egypt_Ural375_Supply.ini",
            21,
        ),
        (
            r"Data\INI\Object\Specter\Egyptian Armed Forces\Airforce\Egypt_Mi-8.ini",
            24,
        ),
    )
    for ppath, pboxes in preserve:
        overlay[ppath] = to_bytes(set_max_boxes(to_text(packed[ppath]), pboxes))

    # Keep map pile dollar totals after VPSB 75 -> 25: StartingBoxes * 3.
    civilian = to_text(packed[r"Data\INI\Object\CivilianBuilding.ini"])
    warehouse_scale = {
        "SupplyWarehouse": 3,
        "SupplyDock": 3,
        "SupplyPile": 3,
        "SupplyPileSmall": 3,
    }
    for obj_name, mult in warehouse_scale.items():
        block = extract_object(civilian, obj_name)

        def _scale_boxes(match, m=mult):
            return f"{match.group(1)}{int(match.group(2)) * m}"

        scaled = re.sub(
            r"(StartingBoxes\s*=\s*)(\d+)",
            _scale_boxes,
            block,
        )
        overlay[
            rf"Data\INI\Object\Specter\PatchSystems\Economy\CountrySupplyIncome\{obj_name}.ini"
        ] = to_bytes(scaled)

    # Worker trips were 1 * 75. With VPSB=25 keep $75 by using 3 boxes.
    for n, blob in packed.items():
        if not n.lower().endswith("worker.ini"):
            continue
        text = to_text(blob)
        if not re.search(r"MaxBoxes\s*=\s*1\b", text):
            continue
        overlay[n] = to_bytes(
            re.sub(r"(MaxBoxes\s*=\s*)1\b", r"\g<1>3", text)
        )

    china_ini = to_text(packed[r"Data\INI\Object\ChinaVehicle.ini"])
    china_truck = extract_object(china_ini, "ChinaVehicleSupplyTruck")
    buttons = to_text(packed[r"Data\INI\CommandButton.ini"])
    commandsets = to_text(packed[r"Data\INI\CommandSet.ini"])

    extra_buttons: list[str] = []
    extra_sets: list[str] = []

    for spec in COUNTRIES:
        boxes = boxes_for(spec["target"])
        center_name = spec["center_path"]
        if center_name not in packed:
            raise SystemExit(f"missing center {center_name}")
        center = to_text(packed[center_name])
        if spec["center_object"] not in center:
            raise SystemExit(f"{spec['center_object']} not in {center_name}")
        center = set_spawn(center, spec["spawn_to"])
        if spec.get("commandset_to"):
            center = set_commandset(center, spec["commandset_to"])
            old_set = extract_block(commandsets, "CommandSet", spec["commandset"])
            new_set = old_set.replace(
                f"CommandSet {spec['commandset']}",
                f"CommandSet {spec['commandset_to']}",
                1,
            )
            if spec["construct_old"] != spec["construct_new"]:
                new_set = new_set.replace(spec["construct_old"], spec["construct_new"])
            extra_sets.append(new_set.strip())
            if spec["construct_old"] != spec["construct_new"]:
                src_btn = extract_block(buttons, "CommandButton", spec["button_src"])
                new_btn = src_btn.replace(
                    f"CommandButton {spec['button_src']}",
                    f"CommandButton {spec['construct_new']}",
                    1,
                )
                new_btn = re.sub(
                    r"(Object\s*=\s*)\S+",
                    rf"\g<1>{spec['spawn_to']}",
                    new_btn,
                    count=1,
                )
                extra_buttons.append(new_btn.strip())
        overlay[center_name] = to_bytes(center)

        gatherer_payloads = []
        if spec.get("clone_object"):
            if spec.get("clone_from_china_ini"):
                src = china_truck
                src = rename_object(src, "ChinaVehicleSupplyTruck", spec["clone_object"])
            else:
                src = extract_object(
                    to_text(packed[spec["clone_from_path"]]),
                    spec["clone_from_object"],
                )
                src = rename_object(src, spec["clone_from_object"], spec["clone_object"])
            src = set_side(src, spec["clone_side"])
            src = set_max_boxes(src, boxes)
            overlay[spec["clone_path"]] = to_bytes(src)
            gatherer_payloads.append((spec["clone_object"], src))

        if spec.get("extract_truck"):
            truck = set_max_boxes(china_truck, boxes)
            overlay[
                r"Data\INI\Object\Specter\PatchSystems\Economy\CountrySupplyIncome\ChinaVehicleSupplyTruck.ini"
            ] = to_bytes(truck)
            gatherer_payloads.append(("ChinaVehicleSupplyTruck", truck))

        for gpath in spec["gatherers"]:
            if gpath not in packed:
                raise SystemExit(f"missing gatherer {gpath}")
            gtext = to_text(packed[gpath])
            if not re.search(r"MaxBoxes\s*=\s*\d+", gtext):
                continue
            gtext = set_max_boxes(gtext, boxes, spec.get("gatherer_objects"))
            overlay[gpath] = to_bytes(gtext)
            gatherer_payloads.append((Path(gpath.replace("\\", "/")).name, gtext))

        stats = []
        for label, payload in gatherer_payloads:
            st = gatherer_stats(payload)
            st["label"] = label
            stats.append(st)
            if boxes not in st["MaxBoxes"]:
                raise SystemExit(f"{spec['country']} {label} MaxBoxes not {boxes}: {st}")

        delay_wh = stats[0]["WarehouseDelayMS"][0] if stats and stats[0]["WarehouseDelayMS"] else None
        delay_sc = stats[0]["CenterDelayMS"][0] if stats and stats[0]["CenterDelayMS"] else None
        load_unload_ms = None
        per_min = None
        if delay_wh is not None and delay_sc is not None:
            load_unload_ms = boxes * delay_wh + delay_sc
            per_min = round(spec["target"] * 60000 / load_unload_ms, 1)

        report["countries"].append(
            {
                "country": spec["country"],
                "target_per_delivery": spec["target"],
                "ValuePerSupplyBox": VPSB,
                "MaxBoxes": boxes,
                "effective_per_delivery": boxes * VPSB,
                "center_object": spec["center_object"],
                "spawn": spec["spawn_to"],
                "warehouse_delay_ms_per_box": delay_wh,
                "center_unload_ms": delay_sc,
                "load_unload_ms_no_travel": load_unload_ms,
                "income_per_minute_no_travel": per_min,
                "gatherers": stats,
            }
        )

    if extra_buttons:
        overlay[r"Data\INI\CommandButton_CountrySupplyIncome.ini"] = to_bytes(
            nl_join(extra_buttons, extra_buttons[0])
        )
    if extra_sets:
        overlay[r"Data\INI\CommandSet_CountrySupplyIncome.ini"] = to_bytes(
            nl_join(extra_sets, extra_sets[0])
        )

    # Japan/SK/Vietnam also had earlier Iraq-clone SupplyCenter files that
    # redefine the same Object name. Overlay the dedicated file only; also
    # neutralize the Iraq-clone spawn by overlaying those files to the unique truck.
    for clone_path, obj, spawn in (
        (
            r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_SupplyCenter.ini",
            "Japan_SupplyCenter",
            "Japan_Ural375_Supply",
        ),
        (
            r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\Iraq_SupplyCenter.ini",
            "SouthKorea_SupplyCenter",
            "SouthKorea_Ural375_Supply",
        ),
        (
            r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_SupplyCenter.ini",
            "Vietnam_SupplyCenter",
            "Vietnam_Ural375_Supply",
        ),
    ):
        text = set_spawn(to_text(packed[clone_path]), spawn)
        overlay[clone_path] = to_bytes(text)

    blob = build_big(overlay)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(blob)
    digest = sha256_bytes(blob)
    args.out.with_suffix(args.out.suffix + ".sha256").write_text(
        digest + "\n", encoding="utf-8"
    )
    report["overlay_big"] = str(args.out)
    report["overlay_bytes"] = len(blob)
    report["overlay_sha256"] = digest
    report["overlay_entries"] = len(overlay)
    report["files"] = sorted(overlay)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"entries={len(overlay)} bytes={len(blob)} SHA256={digest}")
    mismatch = [
        c for c in report["countries"] if c["effective_per_delivery"] != c["target_per_delivery"]
    ]
    if mismatch:
        raise SystemExit(f"effective != target: {mismatch}")
    print(f"countries={len(report['countries'])} all effective dumps match targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
