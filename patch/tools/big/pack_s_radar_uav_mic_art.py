#!/usr/bin/env python3
"""Correct UAV + Iraq Global Market button art and MIC futuristic flag.

Baseline packed archives: SPECTER_RADAR_UAV_SLOTS (PR #666).
Gameplay (slots, costs, objects, prereqs, weapons) is frozen.

New MappedImages so source-country ButtonImage / SelectPortrait stay identical.
Iraq_MIC gains a cloned factory flag model remapped to SpecterFuturisticFlag.tga.
IraqiFlag.dds and IQ__IQFlag_HsWF stay byte-identical.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import sys
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_iraq_building_buttons as bb  # noqa: E402
import pack_s_iraq_mic_radar_ad as rad  # noqa: E402
import pack_s_radar_uav_slots as uav  # noqa: E402
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_RADAR_UAV_SLOTS/_SPEC_DATA_ONE.big"
SRC_ART1 = ROOT / "patch/Release/SPECTER_RADAR_UAV_SLOTS/_SPEC_ART_ONE.big"
SRC_ART2 = ROOT / "patch/Release/SPECTER_RADAR_UAV_SLOTS/_SPEC_ART_TWO.big"
OUT = ROOT / "patch/Release/SPECTER_RADAR_UAV_MIC_ART"
INSTALLER = ROOT / "patch/tools/installer"
LOOSE = ROOT / "patch/Data/INI"
UI_DIR = ROOT / "patch/Art/Textures/UI/radar_uav_mic"
LOOSE_MAPPED = LOOSE / "MappedImages/HandCreated/SpecterUavMicCameos_Images.INI"
LOOSE_MIC_OBJ = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Buildings/Iraq_MIC.ini"

SHA_DATA_SRC = "a4844ce0dfeacb45300ee2003057088b3c1cd5d3b54253bebc15d9c777f46b86"
SIZE_DATA_SRC = 370916915
SHA_ART1_SRC = "dd53835d7119e7609d2bd955879f234da83a0c6c650d7d7ed1194385d9bbd0f2"
SIZE_ART1_SRC = 2144061050
SHA_ART2_SRC = "daf5e3bb3d4b0f763fee4bd39ceafa06000b9c7261f538a0e84a7b6b54fb7f21"
SIZE_ART2_SRC = 307234369
SAGE_SAFE = 2147483648

CS_INI = r"Data\INI\CommandSet.ini"
CB_INI = r"Data\INI\CommandButton.ini"
CS_ZZZZ = r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini"
CB_ZZZZ = rad.CB_KEY
CS_MIC_ZZZZ = rad.CS_KEY
MIC_OBJ_KEY = rad.MIC_OBJ_KEY
WF_OBJ_KEY = rad.WF_OBJ_KEY
CC_OBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_CommandCenter.ini"
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\SpecterUavMicCameos_Images.INI"
FLAG_W3D_SRC = r"Art\W3D\IQ__IQFlag_HsWF.W3D"
FLAG_W3D_NEW = r"Art\W3D\IQ__IQFlag_HsGM.W3D"
FLAG_TEX_KEY = r"Art\Textures\SpecterFuturisticFlag.tga"
IRAQI_FLAG_KEY = r"Art\Textures\IraqiFlag.dds"
FLAG_MODEL = "IQ__IQFlag_HsGM"
FLAG_W3D_ID = b"IQ__IQFLAG_HSGM"
FLAG_W3D_OLD = b"IQ__IQFLAG_HSWF"

TRUEVISION = bb.TRUEVISION

UAV_ART = [
    {
        "png": "heron.png",
        "mapped": "specbtn_heron",
        "cmd": "Command_ConstructSpecterRadarHeron",
        "copy": "SpecterRadar_Heron",
        "old_btn": "Nat_heron",
        "src_cmd": "Command_ConstructIsraelDroneHeron",
        "slot": "9",
        "cost": "10000",
        "label": "Heron",
        "uploaded": "heron.png",
    },
    {
        "png": "mq4_global_hawk.png",
        "mapped": "specbtn_mq4",
        "cmd": "Command_ConstructSpecterRadarMQ4",
        "copy": "SpecterRadar_MQ4",
        "old_btn": "us_mq4",
        "src_cmd": "Command_ConstructAmericaDroneMQ4",
        "slot": "10",
        "cost": "12000",
        "label": "MQ-4 Global Hawk",
        "uploaded": "MQ_4 Global hawk.png",
    },
    {
        "png": "orlan_10.png",
        "mapped": "specbtn_orlan10",
        "cmd": "Command_ConstructSpecterRadarOrlan10",
        "copy": "SpecterRadar_Orlan10",
        "old_btn": "rus_orlan10",
        "src_cmd": "Command_ConstructRussiaDroneOrlan10",
        "slot": "11",
        "cost": "10000",
        "label": "Orlan-10",
        "uploaded": "orlan_10.png",
    },
    {
        "png": "shahed_136_mobile.png",
        "mapped": "specbtn_shahedlnchr",
        "cmd": "Command_ConstructSpecterRadarShahedLauncher",
        "copy": "SpecterRadar_ShahedLauncher",
        "old_btn": "irn_shahedlncher",
        "src_cmd": "Command_ConstructIranVehicleShahedLauncher",
        "slot": "12",
        "cost": "8000",
        "label": "Shahed-136 Mobile Launcher",
        "uploaded": "shahed_136 mobile.png",
    },
]

MIC_ART = [
    {
        "png": "arrow_aam_launcher.png",
        "mapped": "specbtn_mic_arrow",
        "cmd": "Command_ConstructIraq_MIC_Arrow",
        "copy": "Iraq_MIC_Arrow",
        "old_btn": "isi_arrow",
        "src_cmd": "Command_ConstructIsrael_Arrow",
        "slot": "1",
        "label": "Arrow AAM Launcher",
        "uploaded": "Arrow AAM Launcher.png",
    },
    {
        "png": "radar_an.png",
        "mapped": "specbtn_mic_tpy2",
        "cmd": "Command_ConstructIraq_MIC_AN_TPY2",
        "copy": "Iraq_MIC_AN_TPY2",
        "old_btn": "isi_tpy2",
        "src_cmd": "Command_ConstructIsrael_AN_TPY2",
        "slot": "2",
        "label": "Israeli AN/TPY-2 (Radar an)",
        "uploaded": "Radar an.png",
    },
    {
        "png": "92n6e_radar.png",
        "mapped": "specbtn_mic_92n6r",
        "cmd": "Command_ConstructIraq_MIC_92N6R",
        "copy": "Iraq_MIC_92N6R",
        "old_btn": "rus_92n6r",
        "src_cmd": "Command_ConstructRussiaVehicle92N6R",
        "slot": "3",
        "label": "92N6E Radar",
        "uploaded": "92N6E Radar.png",
    },
    {
        "png": "s400_tel.png",
        "mapped": "specbtn_mic_s400",
        "cmd": "Command_ConstructIraq_MIC_S400",
        "copy": "Iraq_MIC_S400",
        "old_btn": "rus_s400r",
        "src_cmd": "Command_ConstructRussiaVehicleS400",
        "slot": "4",
        "label": "S-400 TEL",
        "uploaded": "S-400 TEL.png",
    },
    {
        "png": "pantsir_s1m.png",
        "mapped": "specbtn_mic_pantsir",
        "cmd": "Command_ConstructIraq_MIC_PantsirS1M",
        "copy": "Iraq_MIC_PantsirS1M",
        "old_btn": "rus_pantsirs1m",
        "src_cmd": "Command_ConstructRussiaVehiclePantsirS1M",
        "slot": "5",
        "label": "Pantsir-S1M",
        "uploaded": "Pantsir-S1M.png",
    },
    {
        "png": "krasukha_4.png",
        "mapped": "specbtn_mic_krasukha",
        "cmd": "Command_ConstructIraq_MIC_Krasukha4",
        "copy": "Iraq_MIC_Krasukha4",
        "old_btn": "rus_krasukha4",
        "src_cmd": "Command_ConstructRussiaVehicleKrasukha4",
        "slot": "6",
        "label": "Krasukha-4",
        "uploaded": "Krasukha-4.png",
    },
    {
        "png": "96l6_tsp.png",
        "mapped": "specbtn_mic_96l6tsp",
        "cmd": "Command_ConstructIraq_MIC_96L6TSP",
        "copy": "Iraq_MIC_96L6TSP",
        "old_btn": "rus_96l6tsp",
        "src_cmd": "Command_ConstructRussiaVehicle96L6TSP",
        "slot": "7",
        "label": "96L6-TSP",
        "uploaded": "96L6-TSP.png",
    },
    {
        "png": "s500_tel.png",
        "mapped": "specbtn_mic_s500",
        "cmd": "Command_ConstructIraq_MIC_S500",
        "copy": "Iraq_MIC_S500",
        "old_btn": "rus_s500",
        "src_cmd": "Command_ConstructRussiaVehicleS500",
        "slot": "8",
        "label": "S-500 TEL",
        "uploaded": "S-500 TEL.png",
    },
    {
        "png": "hq9b_tel.png",
        "mapped": "specbtn_mic_hq9",
        "cmd": "Command_ConstructIraq_MIC_HQ9",
        "copy": "Iraq_MIC_HQ9",
        "old_btn": "pla_hq9b",
        "src_cmd": "Command_ConstructChinaVehicleHQ9",
        "slot": "9",
        "label": "HQ-9B TEL",
        "uploaded": "HQ-9B TEL.png",
    },
    {
        "png": "ht233_radar.png",
        "mapped": "specbtn_mic_ht233",
        "cmd": "Command_ConstructIraq_MIC_HT233",
        "copy": "Iraq_MIC_HT233",
        "old_btn": "pla_ht233",
        "src_cmd": "Command_ConstructChinaVehicleHT233",
        "slot": "10",
        "label": "HT-233 Radar",
        "uploaded": "HT-233 Radar.png",
    },
    {
        "png": "trml_4d.png",
        "mapped": "specbtn_mic_trml4d",
        "cmd": "Command_ConstructIraq_MIC_TRML4D",
        "copy": "Iraq_MIC_TRML4D",
        "old_btn": "Nat_trml4d",
        "src_cmd": "Command_ConstructNatoVehicleTRML4D",
        "slot": "11",
        "label": "TRML-4D",
        "uploaded": "TRML-4D.png",
    },
    {
        "png": "iris_t_system.png",
        "mapped": "specbtn_mic_irist",
        "cmd": "Command_ConstructIraq_MIC_IRIST",
        "copy": "Iraq_MIC_IRIST",
        "old_btn": "Nat_irist",
        "src_cmd": "Command_ConstructNatoVehicleIRIST",
        "slot": "12",
        "label": "NATO IRIS-T (System)",
        "uploaded": "system matching the existing repository object.png",
    },
    {
        "png": "radar_system_usa.png",
        "mapped": "specbtn_mic_ustpy2",
        "cmd": "Command_ConstructIraq_MIC_US_AN_TPY2",
        "copy": "Iraq_MIC_US_AN_TPY2",
        "old_btn": "us_tpy2",
        "src_cmd": "Command_ConstructAmericaVehicleAN_TPY2",
        "slot": "13",
        "label": "US AN/TPY-2",
        "uploaded": "Radar System usa.png",
    },
    {
        "png": "thaad.png",
        "mapped": "specbtn_mic_thaad",
        "cmd": "Command_ConstructIraq_MIC_THAAD",
        "copy": "Iraq_MIC_THAAD",
        "old_btn": "us_thaad",
        "src_cmd": "Command_ConstructAmericaVehicleTHAAD",
        "slot": "14",
        "label": "THAAD",
        "uploaded": "THAAD Air Defence System.png",
    },
]

BTN_MAP = {item["cmd"]: item["mapped"] for item in UAV_ART + MIC_ART}
ALL_MAPPED = [item["mapped"] for item in UAV_ART + MIC_ART]

FLAG_DRAW = """  Draw                = W3DModelDraw ModuleTag_Flag_Hs
    ConditionState    = None
      Model           = IQ__IQFlag_HsGM
      Animation       = IQ__IQFlag_HsGM.IQ__IQFlag_HsGM
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT
    AliasConditionState = SNOW
    AliasConditionState = NIGHT SNOW

    ConditionState    = DAMAGED
      Model           = IQ__IQFlag_HsGM
      Animation       = IQ__IQFlag_HsGM.IQ__IQFlag_HsGM
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT DAMAGED
    AliasConditionState = SNOW DAMAGED
    AliasConditionState = NIGHT SNOW DAMAGED

    ConditionState    = REALLYDAMAGED RUBBLE
      Model           = IQ__IQFlag_HsGM
      Animation       = IQ__IQFlag_HsGM.IQ__IQFlag_HsGM
      AnimationMode   = LOOP
    End
  End"""

FROZEN_SOURCE_BTNS = [item["src_cmd"] for item in UAV_ART + MIC_ART]
FROZEN_KEYS = [
    CS_INI,
    CS_ZZZZ,
    CS_MIC_ZZZZ,
    uav.CS_PAK,
    uav.OBJ_KEY,
    rad.OBJ_KEY,
    rad.WF_OBJ_KEY,
    rad.AA_WF_KEY,
    rad.KARRAR_KEY,
    CC_OBJ_KEY,
    IRAQI_FLAG_KEY,
    FLAG_W3D_SRC,
    r"Data\INI\Object\Specter\Israel Defense Forces\Drones\Heron.ini",
    r"Data\INI\Object\Specter\United States Of America\Drones\Mq4.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Drones\Orlan10.ini",
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini",
]


def sha256_path(path: Path) -> str:
    return rad.sha256_path(path)


def last_from(order, files, kind, name):
    return sk.last_block_from_files(order, files, kind, name)


def field(block: str, key: str) -> str:
    return sk.field(block, key)


def catalog_block(text: str, kind: str, name: str) -> str:
    return sk.last_block(text, kind, name)


def slot_map(block: str) -> dict[str, str]:
    return rad.slot_map(block)


def make_tga24(im: Image.Image, size: tuple[int, int] | None = None) -> bytes:
    rgb = im.convert("RGB")
    if size and rgb.size != size:
        rgb = rgb.resize(size, Image.Resampling.LANCZOS)
    w, h = rgb.size
    pixels = rgb.tobytes()
    rows = []
    stride = w * 3
    for y in range(h - 1, -1, -1):
        src = pixels[y * stride : (y + 1) * stride]
        bgr = bytearray()
        for i in range(0, len(src), 3):
            r, g, b = src[i], src[i + 1], src[i + 2]
            bgr += bytes((b, g, r))
        rows.append(bytes(bgr))
    header = bytearray(18)
    header[2] = 2
    struct.pack_into("<HH", header, 12, w, h)
    header[16] = 24
    header[17] = 0x00
    return bytes(header) + b"".join(rows) + TRUEVISION


def mapped_ini(names: list[str]) -> str:
    lines = [
        "; SPECTER UAV radar + Iraq Global Market radar/AD cameos.",
        "; Converted from uploaded patch/ PNGs after visual identity check.",
        "; Do not reuse these MappedImages as SelectPortrait.",
        "",
    ]
    for name in names:
        lines += [
            f"MappedImage {name}",
            f"  Texture = {name}.tga",
            "  TextureWidth = 128",
            "  TextureHeight = 128",
            "  Coords = Left:0 Top:0 Right:128 Bottom:128",
            "  Status = NONE",
            "End",
            "",
        ]
    return "\r\n".join(lines)


def splice_button_images(blob: bytes, mapping: dict[str, str]) -> bytes:
    return bb.splice_button_images(blob, mapping)


def insert_flag(mic_text: str) -> str:
    text = mic_text.replace("\r\n", "\n")
    if "ModuleTag_Flag_Hs" in text:
        raise SystemExit("Iraq_MIC already has Flag_Hs")
    marker = "  PlacementViewAngle = 45"
    if marker not in text:
        raise SystemExit("Iraq_MIC missing PlacementViewAngle = 45")
    return text.replace(marker, FLAG_DRAW + "\n\n" + marker, 1)


def strip_flag(mic_text: str) -> str:
    text = mic_text.replace("\r\n", "\n")
    return re.sub(
        r"\n  Draw\s+=\s+W3DModelDraw ModuleTag_Flag_Hs\n.*?\n  End\n+",
        "\n",
        text,
        count=1,
        flags=re.S,
    )


def clone_flag_w3d(src: bytes) -> bytes:
    if FLAG_W3D_OLD not in src:
        raise SystemExit("source flag W3D missing IQ__IQFLAG_HSWF")
    if src.count(FLAG_W3D_OLD) < 1:
        raise SystemExit("source flag identity missing")
    cloned = sk.uniquify(src, [(FLAG_W3D_OLD, FLAG_W3D_ID)])
    cloned = sk.replace_textures(cloned, {"IraqiFlag.dds": "SpecterFuturisticFlag.tga"})
    cloned = sk.patch_hlod_container(cloned, FLAG_W3D_ID.decode("ascii"))
    tex = sk.mesh_tex(cloned)
    for mesh in ("FLAG01", "FLAG02", "FLAG03"):
        if tex.get(mesh) != {"SpecterFuturisticFlag.tga"}:
            raise SystemExit(f"{mesh} textures {tex.get(mesh)}")
    for mesh in ("HOUSECOLOR01", "HOUSECOLOR02", "HOUSECOLOR03", "LINE01"):
        if tex.get(mesh) != {"Spec_BoardsAndVins.tga"}:
            raise SystemExit(f"{mesh} retargeted {tex.get(mesh)}")
    if "IraqiFlag.dds" in sk.all_tex(cloned):
        raise SystemExit("cloned flag still references IraqiFlag.dds")
    if FLAG_W3D_OLD in cloned:
        raise SystemExit("cloned flag still named HsWF")
    return cloned


def tga_ok(blob: bytes, w: int, h: int) -> bool:
    info = bb.tga_info(blob)
    return (
        info["type"] == 2
        and info["bpp"] == 24
        and info["alpha_bits"] == 0
        and info["width"] == w
        and info["height"] == h
        and info["origin"] == "bottom"
    )


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_RADAR_UAV_SLOTS")
    if sha256_path(SRC_ART1) != SHA_ART1_SRC or SRC_ART1.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE baseline mismatch")
    if sha256_path(SRC_ART2) != SHA_ART2_SRC or SRC_ART2.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO baseline mismatch")

    tgas: dict[str, bytes] = {}
    for item in UAV_ART + MIC_ART:
        path = UI_DIR / item["png"]
        if not path.is_file():
            raise SystemExit(f"missing processed cameo {path}")
        im = Image.open(path)
        tgas[item["mapped"]] = make_tga24(im, (128, 128))
        if not tga_ok(tgas[item["mapped"]], 128, 128):
            raise SystemExit(f"bad TGA {item['mapped']}")
    flag_png = UI_DIR / "futuristic_flag.png"
    if not flag_png.is_file():
        raise SystemExit("missing processed futuristic flag")
    flag_tga = make_tga24(Image.open(flag_png), (128, 64))
    if not tga_ok(flag_tga, 128, 64):
        raise SystemExit("bad flag TGA")

    mapped_text = mapped_ini(ALL_MAPPED)
    btn_map = dict(BTN_MAP)

    print("parsing DATA...")
    files, order = sk.parse_big_ordered(SRC_DATA.read_bytes())
    original = dict(files)

    files[CB_INI] = splice_button_images(files[CB_INI], btn_map)
    files[CB_ZZZZ] = splice_button_images(files[CB_ZZZZ], {k: v for k, v in btn_map.items() if k.startswith("Command_ConstructIraq_MIC_")})
    files[MAPPED_KEY] = mapped_text.encode("latin1")
    mic_text = files[MIC_OBJ_KEY].decode("latin1")
    files[MIC_OBJ_KEY] = sk.to_crlf(insert_flag(mic_text))

    print("parsing ART_ONE...")
    art1, _ = sk.parse_big_ordered(SRC_ART1.read_bytes())
    original_art1 = dict(art1)
    for name, blob in tgas.items():
        art1[rf"Art\Textures\{name}.tga"] = blob
    art1[FLAG_TEX_KEY] = flag_tga

    print("parsing ART_TWO...")
    art2, _ = sk.parse_big_ordered(SRC_ART2.read_bytes())
    original_art2 = dict(art2)
    art2[FLAG_W3D_NEW] = clone_flag_w3d(art2[FLAG_W3D_SRC])

    fails: list[str] = []
    print("building DATA...")
    data_big = sk.build_big(files)
    print("building ART_ONE...")
    art1_big = sk.build_big(art1)
    print("building ART_TWO...")
    art2_big = sk.build_big(art2)
    packed, packed_order = sk.parse_big_ordered(data_big)
    art1p, art1_order = sk.parse_big_ordered(art1_big)
    art2p, art2_order = sk.parse_big_ordered(art2_big)

    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))
    fails.extend(f"ART1 {x}" for x in sk.big_structure_ok(art1_big))
    fails.extend(f"ART2 {x}" for x in sk.big_structure_ok(art2_big))
    if len(art1_big) >= SAGE_SAFE:
        fails.append(f"ART_ONE {len(art1_big)} exceeds SAGE 2GiB")
    if len(art2_big) >= SAGE_SAFE:
        fails.append(f"ART_TWO {len(art2_big)} exceeds SAGE 2GiB")

    live_cs = packed[CS_INI].decode("latin1")
    live_cb = packed[CB_INI].decode("latin1")
    zzzz_cb = packed[CB_ZZZZ].decode("latin1")
    zzzz_cs = packed[CS_ZZZZ].decode("latin1")

    table = [
        "country|radar_object|commandset|s9_cmd|s9_img|s9_obj|s9_cost|"
        "s10_cmd|s10_img|s10_obj|s10_cost|s11_cmd|s11_img|s11_obj|s11_cost|"
        "s12_cmd|s12_img|s12_obj|s12_cost"
    ]
    for country in uav.COUNTRIES:
        live_blk = catalog_block(live_cs, "CommandSet", country["cs"])
        zzzz_blk = catalog_block(zzzz_cs, "CommandSet", country["cs"])
        src_cs, packed_blk = last_from(packed_order, packed, "CommandSet", country["cs"])
        orig_src, orig_blk = last_from(order, original, "CommandSet", country["cs"])
        live_slots = slot_map(live_blk)
        zzzz_slots = slot_map(zzzz_blk)
        packed_slots = slot_map(packed_blk)
        orig_slots = slot_map(orig_blk)
        row = [country["display"], country["radar"], country["cs"]]
        for item in UAV_ART:
            if live_slots.get(item["slot"]) != item["cmd"]:
                fails.append(f"LIVE {country['cs']} slot {item['slot']}={live_slots.get(item['slot'])}")
            if zzzz_slots.get(item["slot"]) != item["cmd"]:
                fails.append(f"ZZZZ {country['cs']} slot {item['slot']}={zzzz_slots.get(item['slot'])}")
            if packed_slots.get(item["slot"]) != item["cmd"]:
                fails.append(f"PACKED {country['cs']} slot {item['slot']}")
            btn = catalog_block(live_cb, "CommandButton", item["cmd"])
            if field(btn, "ButtonImage") != item["mapped"]:
                fails.append(f"{country['display']} {item['cmd']} img {field(btn, 'ButtonImage')}")
            if field(btn, "Object") != item["copy"]:
                fails.append(f"{item['cmd']} object {field(btn, 'Object')}")
            obj_src, obj = last_from(packed_order, packed, "Object", item["copy"])
            if field(obj, "BuildCost") != item["cost"]:
                fails.append(f"{item['copy']} cost {field(obj, 'BuildCost')}")
            row += [item["cmd"], item["mapped"], item["copy"], item["cost"]]
        if orig_slots != packed_slots:
            fails.append(f"{country['cs']} slots changed")
        table.append("|".join(row))

    for item in UAV_ART + MIC_ART:
        src, img = last_from(packed_order, packed, "MappedImage", item["mapped"])
        if src != MAPPED_KEY:
            fails.append(f"{item['mapped']} last-wins {src}")
        if field(img, "Texture") != f"{item['mapped']}.tga":
            fails.append(f"{item['mapped']} texture {field(img, 'Texture')}")
        key = rf"Art\Textures\{item['mapped']}.tga"
        if art1p.get(key) != tgas[item["mapped"]]:
            fails.append(f"ART last-wins mismatch {key}")
        if not tga_ok(art1p[key], 128, 128):
            fails.append(f"packed TGA bad {key}")

        live_btn = catalog_block(live_cb, "CommandButton", item["cmd"])
        packed_src, packed_btn = last_from(packed_order, packed, "CommandButton", item["cmd"])
        if field(live_btn, "ButtonImage") != item["mapped"]:
            fails.append(f"LIVE {item['cmd']} ButtonImage {field(live_btn, 'ButtonImage')}")
        if field(packed_btn, "ButtonImage") != item["mapped"]:
            fails.append(f"PACKED {item['cmd']} ButtonImage {field(packed_btn, 'ButtonImage')}")
        if field(packed_btn, "Command") != "UNIT_BUILD":
            fails.append(f"{item['cmd']} Command changed")
        if field(packed_btn, "Object") != item["copy"]:
            fails.append(f"{item['cmd']} Object changed")
        if "SelectPortrait" in (packed_btn or ""):
            fails.append(f"{item['cmd']} mixed SelectPortrait onto button")
        orig_src, orig_obj = last_from(order, original, "Object", item["copy"])
        new_src, new_obj = last_from(packed_order, packed, "Object", item["copy"])
        if orig_obj != new_obj:
            fails.append(f"object mutated {item['copy']}")
        if field(new_obj, "SelectPortrait") == item["mapped"]:
            fails.append(f"{item['copy']} SelectPortrait retargeted to button cameo")

        src_cmd_src, src_cmd_blk = last_from(packed_order, packed, "CommandButton", item["src_cmd"])
        orig_cmd_src, orig_cmd_blk = last_from(order, original, "CommandButton", item["src_cmd"])
        if orig_cmd_blk != src_cmd_blk:
            fails.append(f"source button mutated {item['src_cmd']}")
        if field(src_cmd_blk, "ButtonImage") != item["old_btn"] and item["cmd"] != "Command_ConstructIraq_MIC_S500":
            # S500 source last-wins rus_s400r; copy old_btn is rus_s500.
            if field(orig_cmd_blk, "ButtonImage") != field(src_cmd_blk, "ButtonImage"):
                fails.append(f"source ButtonImage changed {item['src_cmd']}")

        orig_img_src, orig_img = last_from(order, original, "MappedImage", item["old_btn"])
        new_img_src, new_img = last_from(packed_order, packed, "MappedImage", item["old_btn"])
        if orig_img != new_img:
            fails.append(f"source MappedImage mutated {item['old_btn']}")

    for item in MIC_ART:
        zbtn = catalog_block(zzzz_cb, "CommandButton", item["cmd"])
        if field(zbtn, "ButtonImage") != item["mapped"]:
            fails.append(f"ZZZZ {item['cmd']} ButtonImage {field(zbtn, 'ButtonImage')}")
        packed_src, packed_btn = last_from(packed_order, packed, "CommandButton", item["cmd"])
        if packed_src != CB_ZZZZ:
            fails.append(f"MIC {item['cmd']} last-wins {packed_src}")

    expect_mic = {item["slot"]: item["cmd"] for item in rad.COPIES}
    expect_mic["15"] = rad.SELL
    for name in rad.MIC_CS_NAMES:
        live_mic = slot_map(catalog_block(live_cs, "CommandSet", name))
        src_mic, packed_mic = last_from(packed_order, packed, "CommandSet", name)
        orig_mic_src, orig_mic = last_from(order, original, "CommandSet", name)
        if live_mic != expect_mic:
            fails.append(f"LIVE MIC {name} {live_mic}")
        if slot_map(packed_mic) != expect_mic:
            fails.append(f"PACKED MIC {name}")
        if orig_mic != packed_mic:
            fails.append(f"MIC CommandSet mutated {name}")

    live_t3 = slot_map(catalog_block(live_cs, "CommandSet", rad.WF_CS_NAME))
    orig_t3 = slot_map(last_from(order, original, "CommandSet", rad.WF_CS_NAME)[1])
    packed_t3 = slot_map(last_from(packed_order, packed, "CommandSet", rad.WF_CS_NAME)[1])
    if live_t3 != orig_t3 or packed_t3 != orig_t3:
        fails.append("WF T3 slots changed")
    if live_t3.get("9") != "Command_ConstructIraqVehicleB340":
        fails.append("LIVE T3 missing B340")

    for name in uav.UNRELATED_CS:
        orig_src, orig_blk = last_from(order, original, "CommandSet", name)
        new_src, new_blk = last_from(packed_order, packed, "CommandSet", name)
        if orig_blk != new_blk:
            fails.append(f"unrelated CS mutated {name}")

    radar_an = next(x for x in MIC_ART if x["uploaded"] == "Radar an.png")
    system = next(x for x in MIC_ART if "system matching" in x["uploaded"])
    if radar_an["copy"] != "Iraq_MIC_AN_TPY2" or radar_an["mapped"] != "specbtn_mic_tpy2":
        fails.append("Radar an mapping drifted")
    if system["copy"] != "Iraq_MIC_IRIST" or system["mapped"] != "specbtn_mic_irist":
        fails.append("System mapping drifted")
    packed_src, packed_tpy = last_from(packed_order, packed, "CommandButton", radar_an["cmd"])
    packed_src, packed_iris = last_from(packed_order, packed, "CommandButton", system["cmd"])
    if field(packed_tpy, "ButtonImage") != "specbtn_mic_tpy2":
        fails.append("Radar an not on Israeli AN/TPY-2 copy button")
    if field(packed_iris, "ButtonImage") != "specbtn_mic_irist":
        fails.append("System not on NATO IRIS-T copy button")

    mic_src, mic_obj = last_from(packed_order, packed, "Object", "Iraq_MIC")
    orig_mic_src, orig_mic_obj = last_from(order, original, "Object", "Iraq_MIC")
    if field(mic_obj, "CommandSet") != "Iraq_MICCommandSet":
        fails.append("Iraq_MIC CommandSet pointer changed")
    if field(mic_obj, "SelectPortrait") != "irq_mic":
        fails.append("Iraq_MIC SelectPortrait changed")
    if field(mic_obj, "ButtonImage") != "irq_mic":
        fails.append("Iraq_MIC object ButtonImage changed")
    if "ModuleTag_Flag_Hs" not in mic_obj:
        fails.append("Iraq_MIC missing Flag_Hs")
    if FLAG_MODEL not in mic_obj:
        fails.append("Iraq_MIC missing IQ__IQFlag_HsGM")
    if "SpecterFuturisticFlag" in mic_obj and "ButtonImage" in mic_obj.split("SpecterFuturisticFlag")[0][-80:]:
        fails.append("futuristic assigned as button")
    if "IQ__IQFlag_HsWF" in mic_obj:
        fails.append("Iraq_MIC still points at HsWF")
    stripped = strip_flag(mic_obj).replace("\r\n", "\n").strip()
    orig_norm = orig_mic_obj.replace("\r\n", "\n").strip()
    if stripped != orig_norm:
        fails.append("Iraq_MIC changed beyond Flag_Hs")
    if FLAG_MODEL in orig_mic_obj:
        fails.append("baseline Iraq_MIC already had HsGM")

    wf_src, wf_obj = last_from(packed_order, packed, "Object", "Iraq_WarFactory")
    orig_wf_src, orig_wf = last_from(order, original, "Object", "Iraq_WarFactory")
    if wf_obj != orig_wf:
        fails.append("Iraq_WarFactory mutated")
    if "IQ__IQFlag_HsWF" not in (wf_obj or ""):
        fails.append("War Factory lost HsWF flag")
    cc_src, cc_obj = last_from(packed_order, packed, "Object", "Iraq_CommandCenter")
    orig_cc_src, orig_cc = last_from(order, original, "Object", "Iraq_CommandCenter")
    if cc_obj != orig_cc:
        fails.append("Iraq_CommandCenter mutated")

    if art1p.get(IRAQI_FLAG_KEY) != original_art1.get(IRAQI_FLAG_KEY):
        fails.append("IraqiFlag.dds mutated")
    if art2p.get(FLAG_W3D_SRC) != original_art2.get(FLAG_W3D_SRC):
        fails.append("IQ__IQFlag_HsWF mutated")
    if FLAG_TEX_KEY not in art1p:
        fails.append("missing SpecterFuturisticFlag.tga in ART_ONE")
    elif art1p[FLAG_TEX_KEY] != flag_tga or not tga_ok(art1p[FLAG_TEX_KEY], 128, 64):
        fails.append("flag TGA last-wins mismatch")
    if FLAG_W3D_NEW not in art2p:
        fails.append("missing IQ__IQFlag_HsGM.W3D in ART_TWO")
    else:
        tex = sk.mesh_tex(art2p[FLAG_W3D_NEW])
        if tex.get("FLAG01") != {"SpecterFuturisticFlag.tga"}:
            fails.append(f"FLAG01 tex {tex.get('FLAG01')}")
        if "IraqiFlag.dds" in sk.all_tex(art2p[FLAG_W3D_NEW]):
            fails.append("cloned W3D still uses IraqiFlag.dds")
        wf_tex = sk.mesh_tex(art2p[FLAG_W3D_SRC])
        if wf_tex.get("FLAG01") != {"IraqiFlag.dds"}:
            fails.append("source HsWF FLAG01 retargeted")

    expected_art1_add = {rf"Art\Textures\{n}.tga" for n in ALL_MAPPED} | {FLAG_TEX_KEY}
    added_art1 = set(art1p) - set(original_art1)
    if added_art1 != expected_art1_add:
        fails.append(f"ART_ONE added unexpected {added_art1 ^ expected_art1_add}")
    mutated_art1 = [k for k in original_art1 if original_art1[k] != art1p.get(k)]
    if mutated_art1:
        fails.append(f"existing ART_ONE mutated {mutated_art1[:8]}")
    added_art2 = set(art2p) - set(original_art2)
    if added_art2 != {FLAG_W3D_NEW}:
        fails.append(f"ART_TWO added unexpected {added_art2}")
    mutated_art2 = [k for k in original_art2 if original_art2[k] != art2p.get(k)]
    if mutated_art2:
        fails.append(f"existing ART_TWO mutated {mutated_art2[:8]}")

    allowed_data = {CB_INI, CB_ZZZZ, MAPPED_KEY, MIC_OBJ_KEY}
    for key in original:
        if key in allowed_data:
            continue
        if packed.get(key) != original[key]:
            fails.append(f"unrelated DATA mutated {key}")
    if set(packed) - set(original) != {MAPPED_KEY}:
        fails.append(f"DATA added unexpected {set(packed) - set(original)}")

    irqbtn_src, irqbtn = last_from(packed_order, packed, "MappedImage", "irqbtn_warfac")
    orig_irq_src, orig_irq = last_from(order, original, "MappedImage", "irqbtn_warfac")
    if irqbtn != orig_irq:
        fails.append("irqbtn_warfac mutated")

    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art1_path = OUT / "_SPEC_ART_ONE.big"
    art2_path = OUT / "_SPEC_ART_TWO.big"
    data_path.write_bytes(data_big)
    art1_path.write_bytes(art1_big)
    art2_path.write_bytes(art2_big)

    LOOSE_MAPPED.parent.mkdir(parents=True, exist_ok=True)
    LOOSE_MAPPED.write_bytes(files[MAPPED_KEY])
    loose_cb = LOOSE / "CommandButton.ini"
    loose_cb.write_bytes(splice_button_images(loose_cb.read_bytes(), btn_map))
    loose_zzzz = LOOSE / "CommandButton_ZZZZ_IraqMicRadarAd.ini"
    loose_zzzz.write_bytes(files[CB_ZZZZ])
    LOOSE_MIC_OBJ.parent.mkdir(parents=True, exist_ok=True)
    LOOSE_MIC_OBJ.write_bytes(files[MIC_OBJ_KEY])

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "COUNTRY_UAV_TABLE.txt").write_text("\n".join(table) + "\n", encoding="utf-8")
    mapping_lines = [
        "uploaded|processed_png|visual_id|unit|slot|command|mapped_image|art_texture|notes"
    ]
    for item in UAV_ART:
        mapping_lines.append(
            "|".join(
                [
                    item["uploaded"],
                    item["png"],
                    item["label"],
                    item["copy"],
                    f"radar-{item['slot']}",
                    item["cmd"],
                    item["mapped"],
                    f"{item['mapped']}.tga",
                    "ButtonImage only; SelectPortrait unchanged",
                ]
            )
        )
    for item in MIC_ART:
        mapping_lines.append(
            "|".join(
                [
                    item["uploaded"],
                    item["png"],
                    item["label"],
                    item["copy"],
                    f"mic-{item['slot']}",
                    item["cmd"],
                    item["mapped"],
                    f"{item['mapped']}.tga",
                    "ButtonImage only; SelectPortrait unchanged",
                ]
            )
        )
    mapping_lines.append(
        "Futuristic Orbital Globe Emblem Flag.png|futuristic_flag.png|"
        "futuristic orbital globe emblem|Iraq_MIC building flag surface|n/a|"
        "ModuleTag_Flag_Hs IQ__IQFlag_HsGM|n/a|SpecterFuturisticFlag.tga|"
        "cloned from IQ__IQFlag_HsWF; FLAG01-03 only; not a production button"
    )
    (ext / "IMAGE_MAPPING.txt").write_text("\n".join(mapping_lines) + "\n", encoding="utf-8")
    (ext / "Iraq_MIC.ini").write_bytes(files[MIC_OBJ_KEY])
    (ext / "CommandButton_ZZZZ_IraqMicRadarAd.ini").write_bytes(files[CB_ZZZZ])
    (ext / "SpecterUavMicCameos_Images.INI").write_bytes(files[MAPPED_KEY])

    (OUT / "INSTALL.txt").write_text(
        "\n".join(
            [
                "SPECTER UAV / IRAQ GLOBAL MARKET ART — INSTALL",
                "",
                "Keep the split ART arrangement. Do not recombine ART.",
                "Place all three uncompressed BIGs next to generals.exe:",
                "  _SPEC_DATA_ONE.big",
                "  _SPEC_ART_ONE.big",
                "  _SPEC_ART_TWO.big",
                "",
                "Zero Hour auto-loads every *.big in that folder.",
                "Each .big must start with BIGF. Do not install gzip as .big.",
                "Replace SPECTER_RADAR_UAV_SLOTS DATA and both ART archives.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "Corrects 18-country radar UAV button art (slots 9-12) and Iraq Global "
        "Market radar/AD button art from uploaded images. Sets the Iraq Global "
        "Market building flag to the futuristic globe emblem via a cloned HsWF "
        "flag model. Gameplay unchanged. RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    zip_path = OUT / "SPECTER_RADAR_UAV_MIC_ART.zip"
    print("zipping...")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "_SPEC_ART_TWO.big",
            "INSTALL.txt",
            "README.txt",
            "Launch_Specter.bat",
            "Install_SpecterPatch.bat",
        ):
            zf.write(OUT / name, name)

    data_sha = sha256_path(data_path)
    art1_sha = sha256_path(art1_path)
    art2_sha = sha256_path(art2_path)
    zip_sha = sha256_path(zip_path)
    tag = "s-radar-uav-mic-art"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/" + tag
    )
    mic_map = [
        f"  {item['slot']:>2} {item['copy']:<22} {item['mapped']:<22} {item['uploaded']}"
        for item in MIC_ART
    ]
    report = "\n".join(
        [
            "STATIC VALIDATION: PASS",
            "RUNTIME_TEST=NOT RUN",
            "BASELINE: PR #666 SPECTER_RADAR_UAV_SLOTS",
            "LIVE_CATALOG_PATCHED=CommandButton.ini (ButtonImage only)",
            "ZZZZ_PATCHED=CommandButton_ZZZZ_IraqMicRadarAd.ini (ButtonImage only)",
            "MAPPEDIMAGES=SpecterUavMicCameos_Images.INI",
            "IRAQ_MIC_FLAG=IQ__IQFlag_HsGM + SpecterFuturisticFlag.tga",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_ONE_SIZE={art1_path.stat().st_size}",
            f"ART_ONE_SHA256={art1_sha}",
            f"ART_TWO_SIZE={art2_path.stat().st_size}",
            f"ART_TWO_SHA256={art2_sha}",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "SOURCE_BUTTONS_UNCHANGED=YES",
            "SELECTPORTRAIT_UNCHANGED=YES",
            "UAV_SLOTS_COSTS_OBJECTS_UNCHANGED=YES",
            "MIC_SLOTS_UNCHANGED=YES",
            "WF_T3_UNCHANGED=YES",
            "IRAQIFLAG_DDS_UNCHANGED=YES",
            "HSWF_W3D_UNCHANGED=YES",
            "RADAR_AN=Iraq_MIC_AN_TPY2/specbtn_mic_tpy2",
            "SYSTEM=Iraq_MIC_IRIST/specbtn_mic_irist",
            "RUNTIME_TEST=NOT RUN",
            "",
            "UAV coverage (18 countries, slots 9-12):",
            *table,
            "",
            "Iraq Global Market radar/AD ButtonImage mapping:",
            *mic_map,
            "",
            "Building flag: cloned IQ__IQFlag_HsWF -> IQ__IQFlag_HsGM, FLAG01-03",
            "remapped IraqiFlag.dds -> SpecterFuturisticFlag.tga (128x64 TGA24).",
            "IraqiFlag.dds and War Factory / Command Center flags unchanged.",
            "",
        ]
    )
    (OUT / "VALIDATE_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "\n".join(
            [
                "DATA_CHANGED=YES",
                "ART_CHANGED=YES",
                f"DATA_SIZE={data_path.stat().st_size}",
                f"DATA_SHA256={data_sha}",
                f"ART_ONE_SIZE={art1_path.stat().st_size}",
                f"ART_ONE_SHA256={art1_sha}",
                f"ART_TWO_SIZE={art2_path.stat().st_size}",
                f"ART_TWO_SHA256={art2_sha}",
                "ZIP_FILE=SPECTER_RADAR_UAV_MIC_ART.zip",
                f"ZIP_SIZE={zip_path.stat().st_size}",
                f"ZIP_SHA256={zip_sha}",
                "BASELINE=PR #666",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA:",
                f"  {rel_base}/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART textures:",
                f"  {rel_base}/_SPEC_ART_ONE.big",
                f"  SIZE={art1_path.stat().st_size}",
                f"  SHA256={art1_sha}",
                "",
                "ART models:",
                f"  {rel_base}/_SPEC_ART_TWO.big",
                f"  SIZE={art2_path.stat().st_size}",
                f"  SHA256={art2_sha}",
                "",
                "ZIP:",
                f"  {rel_base}/SPECTER_RADAR_UAV_MIC_ART.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                f"TAG={tag}",
                f"RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/{tag}",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "\n".join(
            [
                "# UAV and Iraq Global Market button art + futuristic MIC flag",
                "",
                "Corrects production ButtonImage artwork for the four PR #666 UAV",
                "options on 18 radar menus and the 14 Iraq Global Market radar /",
                "air-defense copies. Assigns the uploaded futuristic globe emblem",
                "to the Iraq Global Market building flag surface.",
                "",
                "Gameplay (slots, costs, objects, prerequisites, weapons) is unchanged.",
                "Source-country unit buttons and SelectPortrait values stay original.",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("PACKED", data_path.stat().st_size, data_sha)
    print("ART_ONE", art1_path.stat().st_size, art1_sha)
    print("ART_TWO", art2_path.stat().st_size, art2_sha)
    print("ZIP", zip_path.stat().st_size, zip_sha)
    print("\n".join(table[:3]), "...")
    print("STATIC VALIDATION: PASS")
    print("RUNTIME_TEST=NOT RUN")


if __name__ == "__main__":
    main()
