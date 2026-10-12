#!/usr/bin/env python3
"""Implement North Korea missile roster A-J on the India-heavy path.

Baseline: packed SPECTER_INDIA_AJ_HEAVY (PR #642 on Pakistan #641 / #640 / India #639).

Packed last-wins audit: North Korea has no missile factory. The only builder is
NorthKorea_VT72B / NorthKorea_VT72BCommandSet. Last-wins from CommandSet.ini.
Slot 6 currently constructs isolated Sell-only Iraq_AlFahdMissileFactoryBuilding.
No Dozer. No Worker. MIC exists as NorthKorea_MIC but is not on VT72B.
Packed faction path is Data\\INI\\Object\\Specter\\North Korea\\. Side=NorthKorea.
BaseSide=Iraq. StartingBuilding NorthKorea_CommandCenter. StartingUnit0 VT72B.

Preserve existing NorthKorea_Hwasong5, NorthKorea_Hwasong7,
NorthKorea_Hwasong15BB, NorthKorea_KN23, NorthKorea_KN06, NorthKorea_KN09,
WarFactory, MIC object, buildings, and VT72B slots 1-5 and 7-15.

Public Hwasong / Pukguksong / KN families inform names and roles. SPECTER
km/kg/Acc/CHL are fictional game values, not verified military specifications.
North Korea is a crude-heavy peer to India/Pakistan, not a South Korea reskin
and not an automatic winner of range+payload+Acc+CHL.

China has no accepted A-J factory. Iran has no accepted A-J factory.
Do not invent or modify either. South Korea and Japan stay frozen.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Satellite last-wins: CommandSet_NorthKoreaMissiles.ini,
CommandButton_NorthKoreaMissiles.ini, Weapon\\Weapon_NorthKorea_Missiles.ini.
DPRK flag (red field, blue/white stripes, white disk + red star) + names on
dorsal UV. Dedicated Nkr_TEL dark olive-gray truck. No RadarPriority. No rearm.
No ZZZZ.
"""
from __future__ import annotations

import io
import math
import re
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_sk_missiles_aj as sk  # noqa: E402
import pack_s_saudi_missiles_aj as sa  # noqa: E402
import pack_s_uae_missiles_aj as uae  # noqa: E402
import pack_s_libya_missiles_aj as lby  # noqa: E402
import pack_s_syria_missiles_aj as syr  # noqa: E402
import pack_s_southafrica_missiles_aj as saf  # noqa: E402
import pack_s_india_missiles_aj as ind  # noqa: E402
import pack_s_pakistan_missiles_aj as pak  # noqa: E402
import pack_s_pakistan_aj_heavy as pakh  # noqa: E402
import pack_s_india_aj_heavy as indh  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_INDIA_AJ_HEAVY/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_INDIA_AJ_HEAVY/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_NORTHKOREA_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "770075b8d28636ca0d07588e9b152e5b9b4a582310e76e173b6ae41474c6334e"
SIZE_DATA_SRC = 368355059
SHA_ART_SRC = "a7375becdf29e23c8a5e926a3329167561194bfee09dfe4d714ea30573edd24f"
SIZE_ART_SRC = 1782622889

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

NK_CB_KEY = r"Data\INI\CommandButton_NorthKoreaMissiles.ini"
NK_CS_KEY = r"Data\INI\CommandSet_NorthKoreaMissiles.ini"
NK_WEP_KEY = r"Data\INI\Weapon\Weapon_NorthKorea_Missiles.ini"
NK_FAC_KEY = (
    r"Data\INI\Object\Specter\North Korea"
    r"\Buildings\NorthKorea_MissileFactory.ini"
)
NK_VT72B_KEY = r"Data\INI\Object\Specter\North Korea\Tracked\NorthKorea_VT72B.ini"
NK_SYS_KEY = r"Data\INI\Object\Specter\North Korea\NorthKorea_Systems.ini"
NK_WF_KEY = r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_WarFactory.ini"
NK_CC_KEY = r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_CommandCenter.ini"
NK_SC_KEY = r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_SupplyCenter.ini"
NK_FLAG_TGA = r"Art\Textures\DPRK_Flag.tga"
NK_FLAG_DDS = r"Art\Textures\DPRK_Flag.dds"
NK_CMD_W3D = r"Art\W3D\NKr_Command.W3D"
NK_WF_W3D = r"Art\W3D\NKr_WarFactory.W3D"
NK_FLAG_W3D = r"Art\W3D\NKr__NKFlag_Hs.W3D"

TRUCK_TEX = "Nkr_TEL.tga"
TRUCKD_TEX = "Nkr_TELD.tga"
TRUCK_KEY = rf"Art\Textures\{TRUCK_TEX}"
TRUCKD_KEY = rf"Art\Textures\{TRUCKD_TEX}"

WEP_MARKER = (
    "; ===== North Korea missiles A-J "
    "(Weapon.ini load path for Command_FireMainWeapon) ====="
)

BUILDERS = ["NorthKorea_VT72BCommandSet"]

PRESERVED_VT72B = (
    "Command_ConstructNorthKorea_PowerPlant",
    "Command_ConstructNorthKorea_CommandCenter",
    "Command_ConstructNorthKorea_SupplyCenter",
    "Command_ConstructNorthKorea_WarFactory",
    "Command_ConstructNorthKorea_LargeAirBase",
    "Command_ConstructNorthKorea_DefenseSite_SAFE",
    "Command_ConstructNorthKorea_RadarStation",
    "Command_ConstructNorthKorea_HeavyAirBase",
    "Command_ConstructNorthKorea_Barracks_SAFE",
    "Command_ConstructNorthKorea_NuclearCenter",
    "Command_ConstructNorthKorea_D30_SAFE",
    "Command_ConstructNorthKorea_CRAM",
    "Command_ConstructNorthKorea_Hq9_Site",
    "Command_Stop",
)

OLIVE = (42, 52, 38)
EARTH = (36, 40, 32)
SOOT = (24, 26, 22)
NOSE_W = (236, 228, 210)
NOSE_R = (196, 16, 28)
NOSE_B = (20, 48, 140)

# Crude-heavy SPECTER mix. Names from public Hwasong/Pukguksong/KN families.
# Values are game design, not claimed real-world payload or range.
MISSILES = [
    {
        "slot": "A", "object": "NorthKorea_KN02", "name": "KN-02",
        "model": "Nkr_KN02", "modeld": "Nkr_KN02D", "proj_model": "Nkr_KN02M",
        "hier": b"NKR_KN02A", "hierd": b"NKR_KN02AD", "proj_hier": b"NKR_MSL_A",
        "tex": "Nkr_KN02P.tga", "body": (222, 182, 28), "nose": NOSE_W,
        "expect": "yellow", "km": 1000, "kg": 400, "acc": 62, "stealth": 18,
        "rebuild": 16, "price": 750,
        "role": "Tactical SRBM analogue (KN-02/Toksa; real short range mapped to SPECTER floor)",
    },
    {
        "slot": "B", "object": "NorthKorea_Hwasong6", "name": "Hwasong-6",
        "model": "Nkr_Hwasong6", "modeld": "Nkr_Hwasong6D", "proj_model": "Nkr_Hwasong6M",
        "hier": b"NKR_HS06B", "hierd": b"NKR_HS06BD", "proj_hier": b"NKR_MSL_B",
        "tex": "Nkr_Hwasong6P.tga", "body": (88, 96, 42), "nose": NOSE_W,
        "expect": "muddy", "km": 1100, "kg": 700, "acc": 38, "stealth": 20,
        "rebuild": 20, "price": 1100,
        "role": "Liquid SRBM analogue (Hwasong-6/Scud-C class; heavier, modest Acc; distinct from Hwasong5/7)",
    },
    {
        "slot": "C", "object": "NorthKorea_KN24", "name": "KN-24",
        "model": "Nkr_KN24", "modeld": "Nkr_KN24D", "proj_model": "Nkr_KN24M",
        "hier": b"NKR_KN24C", "hierd": b"NKR_KN24CD", "proj_hier": b"NKR_MSL_C",
        "tex": "Nkr_KN24P.tga", "body": (220, 200, 155), "nose": NOSE_W,
        "expect": "cream", "km": 1200, "kg": 400, "acc": 72, "stealth": 26,
        "rebuild": 24, "price": 1600,
        "role": "Precision tactical BM analogue (KN-24; higher Acc than Hwasong-6, below India Pralay)",
    },
    {
        "slot": "D", "object": "NorthKorea_Pukguksong2", "name": "Pukguksong-2",
        "model": "Nkr_Pukguksong2", "modeld": "Nkr_Pukguksong2D", "proj_model": "Nkr_Pukguksong2M",
        "hier": b"NKR_PKGSD", "hierd": b"NKR_PKGSDD", "proj_hier": b"NKR_MSL_D",
        "tex": "Nkr_Pukguksong2P.tga", "body": (10, 72, 84), "nose": NOSE_W,
        "expect": "petrol", "km": 1400, "kg": 500, "acc": 68, "stealth": 50,
        "rebuild": 32, "price": 2800,
        "role": "Solid MRBM/SLBM-heritage analogue (Pukguksong-2; CHL standout, not the heaviest)",
    },
    {
        "slot": "E", "object": "NorthKorea_Hwasong10", "name": "Hwasong-10",
        "model": "Nkr_Hwasong10", "modeld": "Nkr_Hwasong10D", "proj_model": "Nkr_Hwasong10M",
        "hier": b"NKR_HS10E", "hierd": b"NKR_HS10ED", "proj_hier": b"NKR_MSL_E",
        "tex": "Nkr_Hwasong10P.tga", "body": (210, 108, 22), "nose": NOSE_W,
        "expect": "orange", "km": 1600, "kg": 900, "acc": 42, "stealth": 28,
        "rebuild": 36, "price": 2600,
        "role": "IRBM analogue (Hwasong-10/Musudan class; heavier/cruder than Pukguksong-2)",
    },
    {
        "slot": "F", "object": "NorthKorea_KN25", "name": "KN-25",
        "model": "Nkr_KN25", "modeld": "Nkr_KN25D", "proj_model": "Nkr_KN25M",
        "hier": b"NKR_KN25F", "hierd": b"NKR_KN25FD", "proj_hier": b"NKR_MSL_F",
        "tex": "Nkr_KN25P.tga", "body": (8, 162, 56), "nose": NOSE_W,
        "expect": "green", "km": 1500, "kg": 600, "acc": 70, "stealth": 32,
        "rebuild": 34, "price": 2400,
        "role": "Guided MLRS/SRBM analogue (KN-25; precision regional, cheaper than Hwasong-10)",
    },
    {
        "slot": "G", "object": "NorthKorea_Hwasong12", "name": "Hwasong-12",
        "model": "Nkr_Hwasong12", "modeld": "Nkr_Hwasong12D", "proj_model": "Nkr_Hwasong12M",
        "hier": b"NKR_HS12G", "hierd": b"NKR_HS12GD", "proj_hier": b"NKR_MSL_G",
        "tex": "Nkr_Hwasong12P.tga", "body": (128, 128, 128), "nose": NOSE_R,
        "expect": "gray", "km": 2000, "kg": 2800, "acc": 34, "stealth": 30,
        "rebuild": 52, "price": 4800,
        "role": "IRBM analogue (Hwasong-12; SPECTER heavy warhead, cruder than India Agni-I)",
    },
    {
        "slot": "H", "object": "NorthKorea_Hwasong14", "name": "Hwasong-14",
        "model": "Nkr_Hwasong14", "modeld": "Nkr_Hwasong14D", "proj_model": "Nkr_Hwasong14M",
        "hier": b"NKR_HS14H", "hierd": b"NKR_HS14HD", "proj_hier": b"NKR_MSL_H",
        "tex": "Nkr_Hwasong14P.tga", "body": (228, 224, 216), "nose": NOSE_B,
        "expect": "white", "km": 2500, "kg": 3600, "acc": 40, "stealth": 34,
        "rebuild": 64, "price": 6200,
        "role": "Early ICBM-class analogue (Hwasong-14; heavier/less precise than India Agni-P)",
    },
    {
        "slot": "I", "object": "NorthKorea_Hwasong15", "name": "Hwasong-15",
        "model": "Nkr_Hwasong15", "modeld": "Nkr_Hwasong15D", "proj_model": "Nkr_Hwasong15M",
        "hier": b"NKR_HS15I", "hierd": b"NKR_HS15ID", "proj_hier": b"NKR_MSL_I",
        "tex": "Nkr_Hwasong15P.tga", "body": (168, 32, 28), "nose": NOSE_W,
        "expect": "red", "km": 3200, "kg": 5500, "acc": 44, "stealth": 36,
        "rebuild": 78, "price": 8200,
        "role": "Heavy ICBM-class analogue (Hwasong-15; distinct from NorthKorea_Hwasong15BB)",
    },
    {
        "slot": "J", "object": "NorthKorea_Hwasong17", "name": "Hwasong-17",
        "model": "Nkr_Hwasong17", "modeld": "Nkr_Hwasong17D", "proj_model": "Nkr_Hwasong17M",
        "hier": b"NKR_HS17J", "hierd": b"NKR_HS17JD", "proj_hier": b"NKR_MSL_J",
        "tex": "Nkr_Hwasong17P.tga", "body": (28, 68, 168), "nose": NOSE_W,
        "expect": "blue", "km": 3800, "kg": 9000, "acc": 32, "stealth": 28,
        "rebuild": 96, "price": 11000,
        "role": "Flagship ICBM-class analogue (Hwasong-17; SPECTER 9000 kg, below 4000 km India cap)",
    },
]

NAME_MAP = [
    "A KN-02 new as NorthKorea_KN02 (tactical; distinct from NorthKorea_KN23/KN06/KN09)",
    "B Hwasong-6 new as NorthKorea_Hwasong6 (distinct from NorthKorea_Hwasong5/7)",
    "C KN-24 new as NorthKorea_KN24 (precision tactical)",
    "D Pukguksong-2 new as NorthKorea_Pukguksong2 (solid/SLBM-heritage CHL standout)",
    "E Hwasong-10 new as NorthKorea_Hwasong10 (Musudan-class IRBM analogue)",
    "F KN-25 new as NorthKorea_KN25 (guided MLRS/SRBM analogue)",
    "G Hwasong-12 new as NorthKorea_Hwasong12 (heavy IRBM analogue)",
    "H Hwasong-14 new as NorthKorea_Hwasong14 (early ICBM-class analogue)",
    "I Hwasong-15 new as NorthKorea_Hwasong15 (distinct from NorthKorea_Hwasong15BB)",
    "J Hwasong-17 new as NorthKorea_Hwasong17 (flagship; 3800 km / 9000 kg SPECTER)",
]

FROZEN_DATA = list(pak.FROZEN_DATA) + [
    pak.PAK_FAC_KEY, pak.PAK_CB_KEY, pak.PAK_CS_KEY, pak.PAK_WEP_KEY,
    ind.IND_FAC_KEY, ind.IND_CB_KEY, ind.IND_CS_KEY, ind.IND_WEP_KEY,
    NK_VT72B_KEY, NK_SYS_KEY, NK_WF_KEY, NK_CC_KEY, NK_SC_KEY, sk.PT_KEY,
]
FROZEN_DATA += [m["unit_key"] for m in pak.DERIVED]
FROZEN_DATA += [m["proj_key"] for m in pak.DERIVED]
FROZEN_DATA += [m["unit_key"] for m in ind.DERIVED]
FROZEN_DATA += [m["proj_key"] for m in ind.DERIVED]
FROZEN_DATA = list(dict.fromkeys(FROZEN_DATA))

FROZEN_ART = list(pak.FROZEN_ART) + [
    pak.TRUCK_KEY, pak.TRUCKD_KEY, ind.TRUCK_KEY, ind.TRUCKD_KEY,
    NK_FLAG_TGA, NK_FLAG_DDS, NK_CMD_W3D, NK_WF_W3D, NK_FLAG_W3D,
]
FROZEN_ART += [m["tex_key"] for m in pak.DERIVED]
FROZEN_ART += [m["tel_key"] for m in pak.DERIVED]
FROZEN_ART += [m["teld_key"] for m in pak.DERIVED]
FROZEN_ART += [m["projw_key"] for m in pak.DERIVED]
FROZEN_ART += [m["tex_key"] for m in ind.DERIVED]
FROZEN_ART += [m["tel_key"] for m in ind.DERIVED]
FROZEN_ART += [m["teld_key"] for m in ind.DERIVED]
FROZEN_ART += [m["projw_key"] for m in ind.DERIVED]
FROZEN_ART = list(dict.fromkeys(FROZEN_ART))

for _m in MISSILES:
    assert len(_m["hier"]) == 9 and len(_m["hierd"]) == 10 and len(_m["proj_hier"]) == 9
    assert 1000 <= _m["km"] <= 4000 and 400 <= _m["kg"] <= 10000
    assert _m["acc"] != 28
assert MISSILES[-1]["kg"] < 10000
assert MISSILES[-1]["km"] < 4000
assert MISSILES[3]["stealth"] == max(m["stealth"] for m in MISSILES)
assert MISSILES[-1]["kg"] > indh.NEW_BY["J"]["kg"]
assert MISSILES[-1]["acc"] < indh.NEW_BY["J"]["acc"]
assert MISSILES[-1]["km"] < indh.NEW_BY["J"]["km"]


def derived(m: dict) -> dict:
    d = sk.derived({**m, "min_range": sk.MOTHER_MIN_RANGE})
    d["button"] = f"CB_NORTHKOREA_MISSILE_{m['slot']}"
    d["unit_key"] = (
        r"Data\INI\Object\Specter\North Korea"
        rf"\Wheeled\{m['object']}.ini"
    )
    d["proj_key"] = (
        r"Data\INI\Object\Specter\North Korea"
        rf"\{m['object']}_Projectile.ini"
    )
    return d


DERIVED = [derived(m) for m in MISSILES]


def _star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r_out: float, r_in: float, fill) -> None:
    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def make_northkorea_flag() -> Image.Image:
    """DPRK-inspired flag for dorsal UV: blue/white/red/white/blue + disk/star."""
    w, h = 900, 600
    blue = (2, 79, 162, 255)
    white = (255, 255, 255, 255)
    red = (237, 28, 36, 255)
    im = Image.new("RGBA", (w, h), red)
    draw = ImageDraw.Draw(im)
    # 6:2:22:2:6 of 38 units.
    u = h / 38.0
    draw.rectangle([0, 0, w, int(6 * u)], fill=blue)
    draw.rectangle([0, int(6 * u), w, int(8 * u)], fill=white)
    draw.rectangle([0, int(30 * u), w, int(32 * u)], fill=white)
    draw.rectangle([0, int(32 * u), w, h], fill=blue)
    cy = h * 0.50
    cx = w * 0.32
    r_disk = h * 0.16
    draw.ellipse([cx - r_disk, cy - r_disk, cx + r_disk, cy + r_disk], fill=white)
    _star(draw, cx, cy, h * 0.11, h * 0.044, red)
    return im


def has_northkorea_flag(counts: dict[str, int]) -> bool:
    return (
        counts.get("red", 0) >= 8
        and counts.get("blue", 0) >= 2
        and counts.get("white", 0) >= 2
    )


def recolor_truck(src: Image.Image, damaged: bool = False) -> Image.Image:
    """Map Iraqi tan sheet to North Korean dark olive-gray / earth / soot."""
    im = src.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            avg = (r + g + b) / 3.0
            sat = max(r, g, b) - min(r, g, b)
            if avg < 55 and sat < 35:
                px[x, y] = (max(0, int(r * 0.26)), max(0, int(g * 0.28)), max(0, int(b * 0.22)), a)
                continue
            if sat > 70 and avg > 70:
                base = OLIVE
                t = 0.90
            elif avg < 100:
                base = EARTH
                t = max(0.70, min(1.15, avg / 90.0))
            else:
                base = OLIVE
                t = max(0.55, min(1.20, avg / 130.0))
            nr = min(255, int(base[0] * t))
            ng = min(255, int(base[1] * t))
            nb = min(255, int(base[2] * t))
            if damaged:
                nr, ng, nb = int(nr * 0.68), int(ng * 0.70), int(nb * 0.56)
            px[x, y] = (nr, ng, nb, a)
    return im


def make_nk_tel_w3d(src: bytes, damaged: bool, m: dict) -> bytes:
    mapping = {"Irq_AlFahd500P.tga": m["tex"]}
    if damaged:
        mapping["Irq_9P117D.tga"] = TRUCKD_TEX
        blob = sk.replace_textures(src, mapping)
        blob = sk.uniquify(blob, [(b"IRQ_AF500D", m["hierd"])])
        blob = sk.patch_hlod_container(blob, m["modeld"])
    else:
        mapping["Irq_9P117.tga"] = TRUCK_TEX
        blob = sk.replace_textures(src, mapping)
        blob = sk.uniquify(blob, [(b"IRQ_AF500", m["hier"])])
        blob = sk.patch_hlod_container(blob, m["model"])
    return blob


def unit_ini(m: dict) -> str:
    return (
        sk.unit_ini(m)
        .replace("South Korea", "North Korea")
        .replace("Side = SouthKorea", "Side = NorthKorea")
        .replace(
            "Skr_TEL / Skr_TELD (not Irq_9P117 / Jpn_TEL)",
            "Nkr_TEL / Nkr_TELD (not Irq_9P117 / Jpn_TEL / Skr_TEL / Pak_TEL / Ind_TEL)",
        )
    )


def projectile_ini(m: dict) -> str:
    return sk.projectile_ini(m).replace("South Korea", "North Korea")


def weapon_file(missiles: list[dict]) -> str:
    head = (
        WEP_MARKER + "\n"
        "; 9P117 scale. Dedicated North Korea A-J. Distinct from SK/Japan/India/Pakistan.\n"
        "; Hwasong/Pukguksong/KN informed mix. Hwasong-17 below India Agni-V reach, heavier payload.\n"
        "; ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000 (PR #629).\n"
        "; Death HACK is a separate path and is not folded into PrimaryDamage.\n"
        "; Acc/CHL columns are design labels mapped to ScatterRadius / MaxHealth.\n"
    )
    body = sk.weapon_blocks(missiles)
    pairs = body.split("\n\n", 1)[1] if "\n\n" in body else body
    return head + "\n" + pairs


def factory_ini() -> str:
    text = sk.factory_ini()
    text = text.replace("; South Korea missile factory.", "; North Korea missile factory.")
    text = text.replace(
        "with a SouthKorea-only CommandSet (A-J).",
        "with a NorthKorea-only CommandSet (A-J).",
    )
    text = text.replace("Object SouthKorea_MissileFactory", "Object NorthKorea_MissileFactory")
    text = text.replace(
        "DisplayName      = OBJECT:SouthKoreaMissileFactory",
        "DisplayName      = OBJECT:NorthKoreaMissileFactory",
    )
    text = text.replace("Side             = SouthKorea", "Side             = NorthKorea")
    text = text.replace(
        "CommandSet       = SouthKorea_MissileFactoryCommandSet",
        "CommandSet       = NorthKorea_MissileFactoryCommandSet",
    )
    return text


def factory_commandset() -> str:
    slots = "\r\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(DERIVED, start=1))
    return (
        "CommandSet NorthKorea_MissileFactoryCommandSet\r\n"
        f"{slots}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def with_northkorea_factory(block: str) -> str:
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in block:
        raise SystemExit(f"expected isolated Iraq factory in:\n{block}")
    if "Command_ConstructNorthKorea_MissileFactory" in block:
        raise SystemExit("North Korea factory already present on builder")
    return block.replace(
        "Command_ConstructIraq_AlFahdMissileFactoryBuilding",
        "Command_ConstructNorthKorea_MissileFactory",
    )


def commandbutton_all() -> str:
    lines = [
        "; North Korea missiles A-J production buttons and factory construct button.",
        "; Shared specter_missile_* cameos. Unique Object bindings.",
        "",
        "CommandButton Command_ConstructNorthKorea_MissileFactory",
        "  Command          = DOZER_CONSTRUCT",
        "  Object           = NorthKorea_MissileFactory",
        "  TextLabel        = CONTROLBAR:ConstructNorthKoreaMissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel    = CONTROLBAR:ToolTipNorthKoreaMissileFactory",
        "End",
        "",
    ]
    for m in DERIVED:
        lines.extend(
            [
                f"CommandButton {m['button']}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {m['object']}",
                f"  TextLabel     = CONTROLBAR:NorthKoreaMissile{m['slot']}",
                f"  ButtonImage   = {m['cameo']}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTipNorthKoreaMissile{m['slot']}",
                "End",
                "",
            ]
        )
    return "\n".join(lines)


def commandset_file(builders: dict[str, str]) -> str:
    parts = [builders[name] for name in BUILDERS]
    parts.append(factory_commandset())
    return "\r\n\r\n".join(parts) + "\r\n"


def player_tooltip(m: dict) -> str:
    """Player-visible production tooltip. Ratings are design indexes, not probabilities."""
    return (
        f"{m['slot']} {m['name']}\n"
        f"{m['role']}\n"
        f"Range: {m['km']} km\n"
        f"Warhead: {m['kg']} kg\n"
        f"Accuracy: {m['acc']}/100 (impact scatter, not a hit %)\n"
        f"Radar evasion: {m['stealth']}/100 (interceptor toughness, not stealth)\n"
        f"Build Time: {m['rebuild']} sec\n"
        f"Price: ${m['price']}\n"
        f"SPECTER design values, not verified specs"
    )


def csf_map() -> dict[str, str]:
    mapping = {
        "OBJECT:NorthKoreaMissileFactory": "Missile Factory",
        "CONTROLBAR:ConstructNorthKoreaMissileFactory": "Missile Factory",
        "CONTROLBAR:ToolTipNorthKoreaMissileFactory": (
            "Missile Factory\nProduces North Korean missiles A-J\nPrice: $1800"
        ),
    }
    for m in DERIVED:
        mapping[f"OBJECT:{m['object']}"] = m["name"]
        mapping[f"CONTROLBAR:NorthKoreaMissile{m['slot']}"] = f"{m['slot']} {m['name']}"
        mapping[f"CONTROLBAR:ToolTipNorthKoreaMissile{m['slot']}"] = player_tooltip(m)
    return mapping


def mapping_report() -> list[str]:
    lines = [
        "NAME MAPPING:",
        *[f"  {row}" for row in NAME_MAP],
        "",
        "EXISTING NORTH KOREA MISSILE OBJECTS PRESERVED (not factory A-J):",
        "  NorthKorea_Hwasong5 / NK_Hwasong5_SRBM",
        "  NorthKorea_Hwasong7 / NK_Hwasong7_MRBM",
        "  NorthKorea_Hwasong15BB / NK_Hwasong15_BunkerBuster",
        "  NorthKorea_KN23 / NK_KN23_SRBM",
        "  NorthKorea_KN06 / NorthKorea_KN09 (SAM / MLRS, not factory A-J)",
        "  NorthKorea_MIC object and MIC command sets unchanged and not added to VT72B.",
        "  NorthKorea_WarFactory, CommandCenter, SupplyCenter, VT72B object unchanged.",
        "",
        "FACTORY CONSTRUCT:",
        "  Pre-change NorthKorea_VT72BCommandSet last-wins CommandSet.ini slot 6",
        "  constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  Post-change CommandSet.ini + CommandSet_NorthKoreaMissiles.ini last-win the NK factory.",
        "  Slots 1-5 and 7-15 preserved (Power/CC/Supply/WF/LargeAirBase/Defense/Radar/",
        "  HeavyAirBase/Barracks/Nuclear/D30/CRAM/Hq9/Stop). No Dozer/Worker to patch.",
        "",
        "REAL-WORLD vs GAMEPLAY:",
        "  Public sources describe KN-02, Hwasong-6, KN-24, Pukguksong-2, Hwasong-10,",
        "  KN-25, Hwasong-12, Hwasong-14, Hwasong-15, and Hwasong-17 families.",
        "  Reported ranges (KN-02 ~120-220 km; Hwasong-17 ICBM-class) are uncertain.",
        "  SPECTER floor is 1000 km and ceiling 4000 km. Tactical classes sit on the floor.",
        "  North Korea J Hwasong-17 is 3800 km / 9000 kg Acc 32, below India Agni-V reach",
        "  and Acc/CHL, above India payload, below the 10000 kg global ceiling.",
        "  Values below are SPECTER design, not verified military specifications.",
        "",
        "PUBLIC BACKGROUND (not in-game specs):",
        "  CSIS Missile Threat, Missiles of North Korea:",
        "    https://missilethreat.csis.org/country/dprk/",
        "  NTI, North Korea missile overview:",
        "    https://www.nti.org/countries/north-korea/",
        "  Public names (KN-02/Toksa, Hwasong-6, KN-24, Pukguksong-2, Hwasong-10/Musudan,",
        "  KN-25, Hwasong-12/14/15/17) inform identity only. SPECTER km/kg are fictional.",
        "",
        "GAMEPLAY MAPPING (9P117 MOTHER scale):",
        "  AttackRange 1720 = 1000 km. Formula: 1720 * (km / 1000).",
        "  PrimaryDamage 2000 = 400 kg. Formula: 2000 * (kg / 400).",
        "  SecondaryDamage 100 = 400 kg splash. Formula: 100 * (kg / 400).",
        "  Death HACK 2200 = 400 kg extra. NOT folded into PrimaryDamage.",
        "  ScatterRadius 175 = 10/100 accuracy. Limitation: dispersion, not hit %.",
        "  Projectile MaxHealth 400 = 5/100 intercept proxy. No RadarPriority.",
        "  ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000.",
        "  Acc/CHL table columns are design labels only.",
        "",
        "SLOT  NAME                    KM   KG   ACC CHL TIME COST  RANGE  PD     SD    DEATH SCATTER  HP     MINR",
    ]
    for m in DERIVED:
        lines.append(
            f"  {m['slot']}    {m['name']:<22} {m['km']:<4} {m['kg']:<4} "
            f"{m['acc']:<3} {m['stealth']:<3} {m['rebuild']:<4} {m['price']:<5} "
            f"{sk.fmt_stat(m['range']):<6} {sk.fmt_stat(m['damage']):<6} {sk.fmt_stat(m['secondary']):<5} "
            f"{m['death']:<5} {sk.fmt_stat(m['scatter']):<7} {sk.fmt_stat(m['hp']):<6} "
            f"{sk.fmt_stat(m['min_range'])}"
        )
    lines.extend(
        [
            "",
            "MISSION ROLES:",
        ]
    )
    for m in DERIVED:
        lines.append(f"  {m['slot']} {m['name']}: {m['role']}")
    lines.extend(
        [
            "",
            "COUNTRY BALANCE (packed inspected, not runtime):",
            f"  India J Agni-V {indh.NEW_BY['J']['km']} km / {indh.NEW_BY['J']['kg']} kg "
            f"Acc {indh.NEW_BY['J']['acc']} CHL {indh.NEW_BY['J']['stealth']} "
            f"${indh.NEW_BY['J']['price']} t{indh.NEW_BY['J']['rebuild']}.",
            f"  Pakistan J Shaheen-III {pakh.NEW_BY['J']['km']} km / {pakh.NEW_BY['J']['kg']} kg "
            f"Acc {pakh.NEW_BY['J']['acc']} CHL {pakh.NEW_BY['J']['stealth']} "
            f"${pakh.NEW_BY['J']['price']} t{pakh.NEW_BY['J']['rebuild']}.",
            "  North Korea J Hwasong-17 3800 km / 9000 kg Acc 32 CHL 28 $11000 t96.",
            "    NK is heavier and cruder: more payload, less reach, worse Acc/CHL, higher cost/time.",
            f"  India I Agni-III {indh.NEW_BY['I']['km']}/{indh.NEW_BY['I']['kg']} Acc {indh.NEW_BY['I']['acc']} "
            f"vs NK I Hwasong-15 3200/5500 Acc 44.",
            f"  India G Agni-I {indh.NEW_BY['G']['km']}/{indh.NEW_BY['G']['kg']} Acc {indh.NEW_BY['G']['acc']} "
            f"vs NK G Hwasong-12 2000/2800 Acc 34 vs Pakistan G Ghauri "
            f"{pakh.NEW_BY['G']['km']}/{pakh.NEW_BY['G']['kg']} Acc {pakh.NEW_BY['G']['acc']}.",
            "  NK D Pukguksong-2 is the CHL standout (50), below India Shaurya 58 and Pakistan Babur 54.",
            "  SK uses Korean flower/myth names; NK uses Hwasong/KN/Pukguksong. Japan stays precision-first.",
            "  SK J Cheonwang 4200/4500 Acc 20 (accepted SK anomaly, not modified). Japan J Tenrai 3600/4000 Acc 20.",
            "  Libya J 3900/8000 Acc 20. UAE J 4000/7000 Acc 20. Saudi J 4000/4000 Acc 20.",
            "  China has no accepted A-J factory roster. Iran has no accepted A-J factory roster.",
            "  USA/EU strategic systems remain on other production paths.",
        ]
    )
    return lines


def validate(data, art, src_data, src_art, order) -> list[str]:
    fails: list[str] = []
    for key in FROZEN_DATA:
        if key in src_data and data.get(key) != src_data.get(key):
            fails.append(f"frozen DATA mutated {key}")
    for key in FROZEN_ART:
        if key in src_art and art.get(key) != src_art.get(key):
            fails.append(f"frozen ART mutated {key}")

    cs_text = data[CS_KEY].decode("latin1")
    src_cs = src_data[CS_KEY].decode("latin1")
    cb_text = data[CB_KEY].decode("latin1")
    src_cb = src_data[CB_KEY].decode("latin1")
    wep_text = data[WEAPON_KEY].decode("latin1")
    src_wep = src_data[WEAPON_KEY].decode("latin1")
    sat_cs = data[NK_CS_KEY].decode("latin1")

    if "ZZZZ" in NK_CB_KEY or "ZZZZ" in NK_CS_KEY or "ZZZZ" in NK_WEP_KEY:
        fails.append("ZZZZ shortcut")
    if NK_CS_KEY >= r"Data\INI\CommandSet_ZZZZ":
        fails.append("North Korea satellite sorts into ZZZZ")
    if NK_CS_KEY <= CS_KEY:
        fails.append("North Korea satellite sorts before CommandSet.ini")

    for frozen_cs in (
        "Iraq_AlFahdMissileFactoryCommandSet",
        "Vietnam_MissileFactoryCommandSet",
        "Japan_MissileFactoryCommandSet",
        "SouthKorea_MissileFactoryCommandSet",
        "SaudiArabia_MissileFactoryCommandSet",
        "UAE_MissileFactoryCommandSet",
        "Libya_MissileFactoryCommandSet",
        "Syria_MissileFactoryCommandSet",
        "SouthAfrica_MissileFactoryCommandSet",
        "India_MissileFactoryCommandSet",
        "Pakistan_MissileFactoryCommandSet",
        "SouthKorea_VT72BCommandSet",
        "Japan_VT72BCommandSet",
        "India_VT72BCommandSet",
        "Pakistan_VT72BCommandSet",
    ):
        if sk.last_block(cs_text, "CommandSet", frozen_cs) != sk.last_block(
            src_cs, "CommandSet", frozen_cs
        ):
            fails.append(f"{frozen_cs} mutated in CommandSet.ini")

    for name in BUILDERS:
        new_b = sk.last_block(cs_text, "CommandSet", name)
        if "Command_ConstructNorthKorea_MissileFactory" not in new_b:
            fails.append(f"{name} catalog missing North Korea factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in new_b:
            fails.append(f"{name} catalog still has isolated Iraq factory")
        if "Command_ConstructSouthKorea_MissileFactory" in new_b:
            fails.append(f"{name} gained South Korea factory")
        if "Command_ConstructJapan_MissileFactory" in new_b:
            fails.append(f"{name} gained Japan factory")
        for keep in PRESERVED_VT72B:
            if keep not in new_b:
                fails.append(f"{name} lost {keep}")
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", name)
        if "Command_ConstructNorthKorea_MissileFactory" not in lw:
            fails.append(f"last-wins {name} from {_k} missing North Korea factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in lw:
            fails.append(f"last-wins {name} still Iraq factory")
        if name not in sat_cs:
            fails.append(f"satellite missing {name}")

    fac = sk.last_block(cs_text, "CommandSet", "NorthKorea_MissileFactoryCommandSet")
    if not fac:
        fails.append("CommandSet.ini missing North Korea factory roster")
    slots = re.findall(r"CB_NORTHKOREA_MISSILE_([A-Z])", fac)
    if slots != list("ABCDEFGHIJ"):
        fails.append(f"factory slots {slots} != A-J")
    if "Command_Sell" not in fac or "Command_SetRallyPoint" not in fac:
        fails.append("factory missing Rally/Sell")
    if any(
        tag in fac
        for tag in (
            "CB_VIETNAM_", "CB_JAPAN_", "CB_SOUTHKOREA_", "CB_SAUDIARABIA_",
            "CB_UAE_", "CB_LIBYA_", "CB_SYRIA_", "CB_SOUTHAFRICA_",
            "CB_INDIA_", "CB_PAKISTAN_",
        )
    ):
        fails.append("factory mixed foreign buttons")

    construct = sk.last_block(cb_text, "CommandButton", "Command_ConstructNorthKorea_MissileFactory")
    if sk.field(construct, "Object") != "NorthKorea_MissileFactory":
        fails.append("construct Object")
    if sk.field(construct, "Command") != "DOZER_CONSTRUCT":
        fails.append("construct Command")
    if sk.field(construct, "ButtonImage") != "Button_MissileFactory":
        fails.append("construct image")

    for img, btn in (
        ("Button_kashtan", "Command_ConstructRussiaKashtan"),
        ("Button_falaq", "Command_ConstructIranFalaqTrench"),
        ("Button_MissileFactory", "Command_ConstructVietnam_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructJapan_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructSouthKorea_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructSaudiArabia_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructUAE_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructLibya_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructSyria_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructSouthAfrica_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructIndia_MissileFactory"),
        ("Button_MissileFactory", "Command_ConstructPakistan_MissileFactory"),
    ):
        if sk.field(sk.last_block(cb_text, "CommandButton", btn), "ButtonImage") != img:
            fails.append(f"{btn} image lost")
        if sk.last_block(cb_text, "CommandButton", btn) != sk.last_block(src_cb, "CommandButton", btn):
            fails.append(f"{btn} mutated")

    for btn in (
        "Command_ConstructNorthKorea_Hwasong5",
        "Command_ConstructNorthKorea_Hwasong7",
        "Command_ConstructNorthKorea_Hwasong15BB",
        "Command_ConstructNorthKorea_KN23",
    ):
        if sk.last_block(cb_text, "CommandButton", btn) != sk.last_block(src_cb, "CommandButton", btn):
            fails.append(f"{btn} mutated")

    fac_obj = sk.last_block(data[NK_FAC_KEY].decode("latin1"), "Object", "NorthKorea_MissileFactory")
    if sk.field(fac_obj, "Side") != "NorthKorea":
        fails.append("factory Side")
    if sk.field(fac_obj, "CommandSet") != "NorthKorea_MissileFactoryCommandSet":
        fails.append("factory object CommandSet")
    if "SouthKorea_SupplyCenter" not in fac_obj:
        fails.append("factory lost SouthKorea_SupplyCenter prereq")
    if "NorthKorea_SupplyCenter" not in fac_obj:
        fails.append("factory missing NorthKorea_SupplyCenter prereq")

    if sk.last_block(wep_text, "Weapon", "Weapon_Vietnam_VCM01") != sk.last_block(
        src_wep, "Weapon", "Weapon_Vietnam_VCM01"
    ):
        fails.append("Vietnam VCM01 weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Japan_Tenrai") != sk.last_block(
        src_wep, "Weapon", "Weapon_Japan_Tenrai"
    ):
        fails.append("Japan Tenrai mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_India_Agni5") != sk.last_block(
        src_wep, "Weapon", "Weapon_India_Agni5"
    ):
        fails.append("India Agni-V weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Pakistan_Shaheen3") != sk.last_block(
        src_wep, "Weapon", "Weapon_Pakistan_Shaheen3"
    ):
        fails.append("Pakistan Shaheen-III weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_SouthKorea_Cheonwang") != sk.last_block(
        src_wep, "Weapon", "Weapon_SouthKorea_Cheonwang"
    ):
        fails.append("South Korea Cheonwang mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_SouthAfrica_Mokopa") != sk.last_block(
        src_wep, "Weapon", "Weapon_SouthAfrica_Mokopa"
    ):
        fails.append("South Africa Mokopa weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Syria_Luna") != sk.last_block(
        src_wep, "Weapon", "Weapon_Syria_Luna"
    ):
        fails.append("Syria Luna weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Libya_Fajr") != sk.last_block(
        src_wep, "Weapon", "Weapon_Libya_Fajr"
    ):
        fails.append("Libya Fajr weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Iraq_AlFahd500") != sk.last_block(
        src_wep, "Weapon", "Weapon_Iraq_AlFahd500"
    ):
        fails.append("AlFahd weapon mutated")
    if sk.last_block(wep_text, "Weapon", "NK_Hwasong5_SRBM") != sk.last_block(
        src_wep, "Weapon", "NK_Hwasong5_SRBM"
    ):
        fails.append("existing NK Hwasong5 weapon mutated")
    if sk.last_block(wep_text, "Weapon", "NK_Hwasong15_BunkerBuster") != sk.last_block(
        src_wep, "Weapon", "NK_Hwasong15_BunkerBuster"
    ):
        fails.append("existing NK Hwasong15BB weapon mutated")

    if sk.illegal_floats(wep_text):
        fails.append(f"illegal floats {sk.illegal_floats(wep_text)}")

    r11 = sk.last_block(data[sk.R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB")
    if sk.field(r11, "BuildCost") != "1200":
        fails.append("9P117 BuildCost")

    if sk.last_block(data[NK_SYS_KEY].decode("latin1"), "Object", "NorthKorea_Hwasong5") != sk.last_block(
        src_data[NK_SYS_KEY].decode("latin1"), "Object", "NorthKorea_Hwasong5"
    ):
        fails.append("NorthKorea_Hwasong5 mutated")
    if sk.last_block(data[NK_SYS_KEY].decode("latin1"), "Object", "NorthKorea_Hwasong15BB") != sk.last_block(
        src_data[NK_SYS_KEY].decode("latin1"), "Object", "NorthKorea_Hwasong15BB"
    ):
        fails.append("NorthKorea_Hwasong15BB mutated")
    if sk.last_block(data[NK_SYS_KEY].decode("latin1"), "Object", "NorthKorea_KN23") != sk.last_block(
        src_data[NK_SYS_KEY].decode("latin1"), "Object", "NorthKorea_KN23"
    ):
        fails.append("NorthKorea_KN23 mutated")

    if sk.last_block_from_files(order, data, "Object", "China_MissileFactory")[1]:
        fails.append("China factory was invented")
    if sk.last_block_from_files(order, data, "Object", "Iran_MissileFactory")[1]:
        fails.append("Iran factory was invented")

    ind_fac = sk.last_block(data[ind.IND_FAC_KEY].decode("latin1"), "Object", "India_MissileFactory")
    if sk.field(ind_fac, "Side") != "India":
        fails.append("India factory Side mutated")
    pak_fac = sk.last_block(data[pak.PAK_FAC_KEY].decode("latin1"), "Object", "Pakistan_MissileFactory")
    if sk.field(pak_fac, "Side") != "Pakistan":
        fails.append("Pakistan factory Side mutated")
    sk_fac = sk.last_block(data[sk.NEW_FAC_KEY].decode("latin1"), "Object", "SouthKorea_MissileFactory")
    if sk.field(sk_fac, "Side") != "SouthKorea":
        fails.append("South Korea factory Side mutated")
    jp_fac = sk.last_block(data[sk.JPN_FAC_KEY].decode("latin1"), "Object", "Japan_MissileFactory")
    if sk.field(jp_fac, "Side") != "Japan":
        fails.append("Japan factory Side mutated")

    truck = Image.open(io.BytesIO(art[TRUCK_KEY])).convert("RGB")
    truck_avg = truck.resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
    if truck_avg[2] > truck_avg[0] + 20:
        fails.append(f"truck too blue {truck_avg}")
    irq_avg = Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == irq_avg:
        fails.append("truck still Iraqi donor")
    for label, key in (
        ("Pakistan forest", pak.TRUCK_KEY),
        ("India saffron-olive", ind.TRUCK_KEY),
        ("South Korea slate", r"Art\Textures\Skr_TEL.tga"),
        ("Japan truck", r"Art\Textures\Jpn_TEL.tga"),
    ):
        if key in src_art:
            other = Image.open(io.BytesIO(src_art[key])).convert("RGB").resize(
                (1, 1), Image.Resampling.BOX
            ).getpixel((0, 0))
            if truck_avg == other:
                fails.append(f"truck still {label}")

    wep_sat = data[NK_WEP_KEY].decode("latin1")
    baseline_objects = set()
    obj_re = re.compile(rb"^Object (\S+)", re.M)
    for key, blob in src_data.items():
        if key.endswith(".ini") or key.endswith(".INI"):
            baseline_objects.update(mo.group(1).decode("ascii", "ignore") for mo in obj_re.finditer(blob))
    seen_objects = set()
    csf = data[CSF_KEY]
    for m in DERIVED:
        if m["object"] in seen_objects:
            fails.append(f"duplicate object {m['object']}")
        seen_objects.add(m["object"])
        if m["object"] in baseline_objects:
            fails.append(f"{m['slot']} {m['object']} already exists in baseline")

        unit = sk.last_block(data[m["unit_key"]].decode("latin1"), "Object", m["object"])
        if sk.field(unit, "BuildCost") != str(m["price"]):
            fails.append(f"{m['slot']} BuildCost")
        if not sk.field(unit, "BuildTime").startswith(f"{m['rebuild']}.0"):
            fails.append(f"{m['slot']} BuildTime")
        if sk.field(unit, "Side") != "NorthKorea":
            fails.append(f"{m['slot']} Side")
        if sk.field(unit, "ButtonImage") != m["cameo"]:
            fails.append(f"{m['slot']} ButtonImage")
        if sk.field(unit, "SelectPortrait") != m["cameo"]:
            fails.append(f"{m['slot']} SelectPortrait")
        if f"Model                           = {m['model']}" not in unit:
            fails.append(f"{m['slot']} TEL model")
        if m["weapon"] not in unit:
            fails.append(f"{m['slot']} weapon bind")
        if sk.field(unit, "CommandSet") != "Scud_B_CommandSet":
            fails.append(f"{m['slot']} CommandSet")
        if re.search(r"Weapon\s*=\s*SECONDARY", unit) or re.search(r"Weapon\s*=\s*TERTIARY", unit):
            fails.append(f"{m['slot']} extra weapon slot")
        if "Rearm" in unit or "RiderChangeContain" in unit or "InitialPayload" in unit:
            fails.append(f"{m['slot']} unexpected rearm/contain")
        if "NorthKorea_Hwasong5" in unit or "NorthKorea_Hwasong15BB" in unit or "NorthKorea_KN23" in unit:
            fails.append(f"{m['slot']} collided with existing NK missile")

        proj = sk.last_block(data[m["proj_key"]].decode("latin1"), "Object", m["projectile"])
        if f"Model = {m['proj_model']}" not in proj:
            fails.append(f"{m['slot']} flying model")
        if sk.field(proj, "MaxHealth") != sk.fmt_stat(m["hp"]):
            fails.append(f"{m['slot']} HP")
        if sk.field(proj, "RadarPriority"):
            fails.append(f"{m['slot']} RadarPriority")

        ini_w = sk.last_block(wep_text, "Weapon", m["weapon"])
        sat_w = sk.last_block(wep_sat, "Weapon", m["weapon"])
        for block, label in ((ini_w, "Weapon.ini"), (sat_w, "sat")):
            if sk.field(block, "AttackRange") != sk.fmt_stat(m["range"]):
                fails.append(f"{m['slot']} {label} range")
            if sk.field(block, "PrimaryDamage") != sk.fmt_stat(m["damage"]):
                fails.append(f"{m['slot']} {label} PD")
            if sk.field(block, "SecondaryDamage") != sk.fmt_stat(m["secondary"]):
                fails.append(f"{m['slot']} {label} SD")
            if sk.field(block, "ClipSize") != "1" or sk.field(block, "AutoReloadsClip") != "Yes":
                fails.append(f"{m['slot']} {label} clip")
            if sk.field(block, "ClipReloadTime") != "300000":
                fails.append(f"{m['slot']} {label} reload")
            if sk.field(block, "ProjectileObject") != m["projectile"]:
                fails.append(f"{m['slot']} {label} projectile")
            if sk.field(block, "WeaponSpeed") != "280":
                fails.append(f"{m['slot']} {label} speed")
        death = sk.last_block(wep_sat, "Weapon", m["warhead"])
        if sk.field(death, "DamageType") != "HACK":
            fails.append(f"{m['slot']} death type")
        if sk.field(death, "PrimaryDamage") != str(m["death"]):
            fails.append(f"{m['slot']} death PD")
        if "HACK" in ini_w:
            fails.append(f"{m['slot']} HACK folded into PRIMARY")

        bblock = sk.last_block(cb_text, "CommandButton", m["button"])
        if sk.field(bblock, "Object") != m["object"]:
            fails.append(f"{m['slot']} button object")
        if sk.field(bblock, "ButtonImage") != m["cameo"]:
            fails.append(f"{m['slot']} button image")
        if sk.csf_get(csf, f"CONTROLBAR:NorthKoreaMissile{m['slot']}") != f"{m['slot']} {m['name']}":
            fails.append(f"{m['slot']} CSF name")
        if sk.csf_get(csf, f"CONTROLBAR:ToolTipNorthKoreaMissile{m['slot']}") != player_tooltip(m):
            fails.append(f"{m['slot']} CSF tooltip")

        tel = art[m["tel_key"]]
        teld = art[m["teld_key"]]
        projw = art[m["projw_key"]]
        if m["hier"] not in tel:
            fails.append(f"{m['slot']} TEL hier")
        if m["hierd"] not in teld:
            fails.append(f"{m['slot']} TELD hier")
        if m["proj_hier"] not in projw:
            fails.append(f"{m['slot']} proj hier")
        for blob, label in ((tel, "TEL"), (teld, "TELD"), (projw, "PROJ")):
            for banned in (b"IRQ_9P117", b"IRQ_R11_M", b"IRQ_AF500", b"IRQ_ALF_M", b"GENERIC-MISSILES"):
                if banned in blob:
                    fails.append(f"{m['slot']} {label} leaked {banned.decode()}")
        tel_tex = sk.all_tex(tel)
        if m["tex"] not in tel_tex or TRUCK_TEX not in tel_tex:
            fails.append(f"{m['slot']} TEL tex {tel_tex}")
        if any(
            x in tel_tex
            for x in (
                "Skr_TEL.tga", "Jpn_TEL.tga", "Sau_TEL.tga", "Uae_TEL.tga",
                "Lby_TEL.tga", "Syr_TEL.tga", "Saf_TEL.tga", "Ind_TEL.tga",
                "Pak_TEL.tga",
            )
        ):
            fails.append(f"{m['slot']} foreign truck")

        im = Image.open(io.BytesIO(art[m["tex_key"]])).convert("RGB")
        tel_flag = sk.region_mode(im, (110, 180, 420, 290))
        if not has_northkorea_flag(tel_flag):
            fails.append(f"{m['slot']} North Korea flag {tel_flag}")
        if not sk.has_name_plate(im, (500, 190, 960, 280)):
            fails.append(f"{m['slot']} TEL name")
        body = sk.region_mode(im, (80, 410, 200, 560))
        top = max(body, key=body.get)
        allowed = {
            "yellow": {"yellow", "orange", "cream"},
            "orange": {"orange", "red", "yellow"},
            "white": {"white", "cream"},
            "red": {"red", "orange"},
            "muddy": {"muddy", "green", "other"},
            "green": {"green", "muddy"},
            "petrol": {"petrol", "blue", "green"},
            "gray": {"gray", "white", "dark"},
            "blue": {"blue", "petrol"},
            "cream": {"cream", "white", "yellow"},
        }
        if top not in allowed[m["expect"]] and top != m["expect"]:
            fails.append(f"{m['slot']} body {top} {body}")
        if m["km"] < 1000 or m["km"] > 4000:
            fails.append(f"{m['slot']} km")
        if m["kg"] < 400 or m["kg"] > 10000:
            fails.append(f"{m['slot']} kg")

    if len(DERIVED) != 10:
        fails.append(f"roster count {len(DERIVED)}")
    if len(seen_objects) != 10:
        fails.append(f"unique objects {len(seen_objects)}")
    return fails


def write_loose(builders: dict[str, str]) -> None:
    fac_dir = LOOSE / "Object/Specter/North Korea/Buildings"
    wheel_dir = LOOSE / "Object/Specter/North Korea/Wheeled"
    proj_dir = LOOSE / "Object/Specter/North Korea"
    wep_dir = LOOSE / "Weapon"
    for d in (fac_dir, wheel_dir, proj_dir, wep_dir):
        d.mkdir(parents=True, exist_ok=True)
    (fac_dir / "NorthKorea_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    (wep_dir / "Weapon_NorthKorea_Missiles.ini").write_text(weapon_file(DERIVED), encoding="utf-8")
    (LOOSE / "CommandButton_NorthKoreaMissiles.ini").write_text(commandbutton_all(), encoding="utf-8")
    (LOOSE / "CommandSet_NorthKoreaMissiles.ini").write_text(commandset_file(builders), encoding="utf-8")
    for m in DERIVED:
        (wheel_dir / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (proj_dir / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_INDIA_AJ_HEAVY")
    if sk.sha256_path(SRC_ART) != SHA_ART_SRC or SRC_ART.stat().st_size != SIZE_ART_SRC:
        raise SystemExit("ART baseline is not SPECTER_INDIA_AJ_HEAVY")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art = sk.parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    flag = make_northkorea_flag()
    truck = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])), damaged=False)
    truckd = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCKD_DDS])), damaged=True)
    art[TRUCK_KEY] = sk.make_tga32(truck)
    art[TRUCKD_KEY] = sk.make_tga32(truckd)

    for m in DERIVED:
        skin = sk.make_skin(m["body"], m["nose"], m["name"], flag)
        art[m["tex_key"]] = sk.make_tga32(skin)
        art[m["tel_key"]] = make_nk_tel_w3d(src_art[TEL_W3D], False, m)
        art[m["teld_key"]] = make_nk_tel_w3d(src_art[TELD_W3D], True, m)
        art[m["projw_key"]] = sk.make_proj_w3d(src_art[PROJ_W3D], m)
        data[m["unit_key"]] = sk.to_crlf(unit_ini(m))
        data[m["proj_key"]] = sk.to_crlf(projectile_ini(m))

    data[NK_FAC_KEY] = sk.to_crlf(factory_ini())
    data[NK_WEP_KEY] = sk.to_crlf(weapon_file(DERIVED))
    data[NK_CB_KEY] = sk.to_crlf(commandbutton_all())
    data[CSF_KEY] = sk.csf_upsert(src_data[CSF_KEY], csf_map())

    cs = src_data[CS_KEY].decode("latin1")
    builders = {}
    for name in BUILDERS:
        old = sk.last_block(cs, "CommandSet", name)
        if not old:
            raise SystemExit(f"missing {name} in CommandSet.ini")
        new = with_northkorea_factory(old)
        builders[name] = new
        cs = sk.replace_last(cs, "CommandSet", name, new)
    if sk.last_block(cs, "CommandSet", "NorthKorea_MissileFactoryCommandSet"):
        cs = sk.replace_last(cs, "CommandSet", "NorthKorea_MissileFactoryCommandSet", factory_commandset())
    else:
        cs = cs.rstrip("\r\n") + "\r\n\r\n" + factory_commandset() + "\r\n"
    data[CS_KEY] = cs.encode("latin1")
    data[NK_CS_KEY] = sk.to_crlf(commandset_file(builders))

    cb = src_data[CB_KEY].decode("latin1")
    if "CommandButton Command_ConstructNorthKorea_MissileFactory" in cb:
        raise SystemExit("CommandButton.ini already had North Korea factory")
    extra = commandbutton_all().replace("\n", "\r\n")
    data[CB_KEY] = (cb.rstrip("\r\n") + "\r\n\r\n" + extra + "\r\n").encode("latin1")

    wep = src_data[WEAPON_KEY].decode("latin1")
    if WEP_MARKER in wep or "Weapon Weapon_NorthKorea_KN02" in wep:
        raise SystemExit("Weapon.ini already had North Korea A-J")
    data[WEAPON_KEY] = (
        wep.rstrip("\r\n") + "\r\n\r\n" + weapon_file(DERIVED).replace("\n", "\r\n")
    ).encode("latin1")

    write_loose(builders)

    data_big = sk.build_big(data)
    art_big = sk.build_big(art)
    packed_data, order = sk.parse_big_ordered(data_big)
    packed_art = sk.parse_big(art_big)
    fails = validate(packed_data, packed_art, src_data, src_art, order)
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))
    fails.extend(f"ART {x}" for x in sk.big_structure_ok(art_big))
    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_big)
    art_path.write_bytes(art_big)

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    packed_cs = packed_data[CS_KEY].decode("latin1")
    (ext / "CommandSet.ini.NorthKorea.txt").write_text(
        "\r\n\r\n".join(sk.last_block(packed_cs, "CommandSet", n) for n in BUILDERS)
        + "\r\n\r\n"
        + sk.last_block(packed_cs, "CommandSet", "NorthKorea_MissileFactoryCommandSet")
        + "\r\n",
        encoding="utf-8",
    )
    (ext / "Weapon.ini.NorthKorea.txt").write_text(weapon_file(DERIVED), encoding="utf-8")
    (ext / "NorthKorea_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    for m in DERIVED:
        (ext / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (ext / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    preview = OUT / "PREVIEW"
    preview.mkdir()
    flag.save(preview / "NorthKoreaFlag.png")
    truck.save(preview / "Nkr_TEL.png")
    truckd.save(preview / "Nkr_TELD.png")
    for m in DERIVED:
        Image.open(io.BytesIO(packed_art[m["tex_key"]])).save(preview / f"{m['slot']}_{m['object']}.png")
        Image.open(io.BytesIO(packed_art[m["tex_key"]])).crop((40, 150, 980, 320)).save(
            preview / f"{m['slot']}_dorsal_tel.png"
        )
        Image.open(io.BytesIO(packed_art[m["tex_key"]])).crop((40, 660, 980, 830)).save(
            preview / f"{m['slot']}_dorsal_proj.png"
        )

    data_sha = sk.sha256_path(data_path)
    art_sha = sk.sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_NORTHKOREA_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    inv = [
        "PRE-CHANGE NORTH KOREA (packed last-wins, India A-J heavy baseline):",
        "  No NorthKorea_MissileFactory.",
        "  Only builder NorthKorea_VT72B last-wins CommandSet.ini.",
        "  Slot 6 constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  Existing Hwasong5 / Hwasong7 / Hwasong15BB / KN23 / KN06 / KN09 preserved.",
        "  Packed faction path: North Korea. Side=NorthKorea. BaseSide=Iraq.",
        "",
        "POST-CHANGE NORTH KOREA:",
        "  Dedicated NorthKorea_MissileFactory A-J + Rally/Sell.",
        "  CommandSet_NorthKoreaMissiles.ini last-wins VT72B + factory roster.",
        "  Hwasong/KN/Pukguksong mix 1000-3800 km / 400-9000 kg. Crude-heavy, not SK/Japan/India.",
        "",
        "COUNTRY BALANCE (inspected packed / accepted factory A-J, not runtime):",
        "  India J Agni-V 4000 km / 7000 kg Acc 58. Pakistan J Shaheen-III 3000/3600 Acc 56.",
        "  North Korea J Hwasong-17 3800/9000 Acc 32 CHL 28. Heavier, shorter, cruder, costlier.",
        "  SK J Cheonwang 4200/4500 Acc 20 (accepted, not modified). Japan J Tenrai 3600/4000 Acc 20.",
        "  China factory ABSENT. Iran factory ABSENT. Not invented.",
        "",
        *map_lines,
    ]
    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #642 s-india-aj-heavy + PR #641 + #640 + #639 + #638 + #637 + #636 + #635 + #634 + #633 + #632 + #631 + #630 + #629",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "NORTHKOREA_FACTORY_NEW=YES",
        "EXISTING_HWASONG5_7_15BB_KN23_KEPT=YES",
        "INDIA_AJ_HEAVY_UNCHANGED=YES",
        "PAKISTAN_AJ_HEAVY_UNCHANGED=YES",
        "SOUTHAFRICA_AJ_UNCHANGED=YES",
        "SYRIA_AJ_UNCHANGED=YES",
        "LIBYA_AJ_UNCHANGED=YES",
        "UAE_AJ_UNCHANGED=YES",
        "SAUDI_AJ_UNCHANGED=YES",
        "VIETNAM_AJ_UNCHANGED=YES",
        "JAPAN_AJ_UNCHANGED=YES",
        "SK_AJ_UNCHANGED=YES",
        "NINE_P117_UNCHANGED=YES",
        "IRAQ_FACTORY_UNCHANGED=YES",
        "CHINA_FACTORY_ABSENT=YES",
        "IRAN_FACTORY_ABSENT=YES",
        "NO_REARM=YES",
        "NO_RADARPRIORITY=YES",
        "ROSTER_COUNT=10",
        "KM_FLOOR=1000",
        "KM_CEILING_USED=3800",
        "KG_FLOOR=400",
        "KG_CEILING_USED=9000",
        "",
        *inv,
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    hashes = "\n".join(
        [
            "DATA_CHANGED=YES",
            "ART_CHANGED=YES",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_SIZE={art_path.stat().st_size}",
            f"ART_SHA256={art_sha}",
            "ZIP_FILE=SPECTER_NORTHKOREA_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #642",
            "STATIC_VALIDATION=PASS",
            "RUNTIME_TEST=NOT RUN",
            "",
        ]
    )
    (OUT / "HASHES.txt").write_text(hashes)
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-northkorea-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-northkorea-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-northkorea-missiles-aj/SPECTER_NORTHKOREA_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-northkorea-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-northkorea-missiles-aj",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "North Korea complete missile roster A-J on the accepted factory/fire path.\n"
        "New country factory replaces the isolated Iraq factory construct on NorthKorea_VT72B slot 6.\n"
        "Existing Hwasong5, Hwasong7, Hwasong15BB, KN23, KN06, KN09, WarFactory, and MIC object are unchanged.\n"
        "Hwasong/KN/Pukguksong mix 1000-3800 km / 400-9000 kg. Crude-heavy peer to India, not a SK/Japan reskin.\n"
        "India A-J heavy, Pakistan A-J heavy, South Africa, Syria, Libya, UAE, Saudi, Vietnam, Japan, South Korea, Iraq A-M, and 9P117 unchanged.\n"
        "China and Iran A-J factory rosters remain absent.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# North Korea missiles A-J\n\n"
        "- New NorthKorea_MissileFactory. Rally/Sell retained.\n"
        "- Replaces isolated Iraq factory construct on NorthKorea_VT72B slot 6.\n"
        "- CommandSet_NorthKoreaMissiles.ini last-wins VT72B + factory roster.\n"
        "- Existing Hwasong5/7/15BB, KN23/06/09, WarFactory, MIC object, and VT72B slots 1-5/7-15 preserved.\n"
        "- DPRK flag (red field, blue/white stripes, white disk + red star) + exact names on dorsal UV.\n"
        "- Dedicated Nkr_TEL dark olive-gray truck. Ten-color tube palette distinct from SK/Japan/India/Pakistan.\n"
        "- Hwasong-17 cap 3800 km / 9000 kg Acc 32. Below India Agni-V reach/Acc/CHL. Above India payload.\n"
        "- 5-minute clip reload on all ten PRIMARY weapons.\n"
        "- India A-J heavy, Pakistan A-J heavy, and all previously accepted country rosters unchanged.\n"
        "- China and Iran A-J factories were not invented.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n", encoding="utf-8")
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_NorthKoreaMissiles.ini last-wins NorthKorea_VT72BCommandSet and factory CommandSet.\n"
        "CommandButton_NorthKoreaMissiles.ini last-wins construct + A-J.\n"
        "Weapon\\Weapon_NorthKorea_Missiles.ini last-wins Weapon_NorthKorea_* factory pair.\n"
        "NorthKorea_Systems.ini, VT72B object, WarFactory, existing Hwasong5/7/15BB/KN23/KN06/KN09 are frozen.\n"
        "NorthKorea_KN02/Hwasong6/KN24/Pukguksong2/Hwasong10/KN25/Hwasong12/Hwasong14/Hwasong15/Hwasong17 are new.\n"
        "India, Pakistan, South Africa, Syria, Libya, UAE, Saudi, Vietnam, Japan, South Korea, Iraq, and 9P117 packed definitions are unchanged.\n"
        "China and Iran A-J factory objects remain absent.\n"
    )
    art_notes = [
        "NORTH KOREA A-J ART MARKINGS (static inspection)",
        "",
        "Flag: red field, blue/white stripes, white disk + red star.",
        "SPECTER Side=NorthKorea / North Korea identity. Not SK Taegeuk / Japan Hinomaru / India Tiranga / Pakistan flag.",
        "Dedicated Nkr_TEL / Nkr_TELD dark olive-gray truck. Not Skr_TEL / Jpn_TEL / Ind_TEL / Pak_TEL / Irq_9P117.",
        "Existing DPRK_Flag.tga/dds, NKr_Command.W3D, NKr_WarFactory.W3D, NKr__NKFlag_Hs.W3D frozen.",
        "",
        "SLOT  NAME                     COLOR     FLAG    NAME PLATE",
    ]
    for m in DERIVED:
        art_notes.append(f"  {m['slot']}    {m['name']:<24} {m['expect']:<9} PASS    PASS")
    art_notes.extend(
        [
            "",
            "Limitation: 2D UV-band inspection, not an in-engine overhead camera.",
            "RUNTIME TEST: NOT RUN",
            "",
        ]
    )
    (OUT / "ART_MARKINGS.txt").write_text("\n".join(art_notes), encoding="utf-8")
    print("PACKED")
    print(hashes)
    print("\n".join(report[:80]))


if __name__ == "__main__":
    main()
