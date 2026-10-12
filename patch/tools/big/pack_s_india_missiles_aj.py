#!/usr/bin/env python3
"""Implement India missile roster A-J on the South Africa / Syria path.

Baseline: packed SPECTER_SOUTHAFRICA_MISSILES_AJ (PR #638 + #637 + #636 + UAE/Saudi/VN/SK/Japan).

India has no missile factory. Dozer / Worker / VT72B slot 13 currently
constructs the isolated Sell-only Iraq_AlFahdMissileFactoryBuilding. Replace that
slot with an India-only factory. Keep MIC on slot 6.

Preserve existing India_ShaheenTEL, India_AbabeelTEL, and India_Alhussaien.
Packed faction path is Indian Armed Forces. Side=India.

India has a documented indigenous ballistic and cruise-missile program (DRDO:
Prahaar, Prithvi, Pralay, Shaurya, BrahMos, Nirbhay, Agni-I/P/III/V). SPECTER
km/kg/Acc/CHL are fictional game values informed by that mix, not verified
military specifications. Agni-V is mapped to the SPECTER 4000 km cap; public
estimates of Agni-V range exceed that cap and are uncertain.

Profile vs Syria/South Africa: longer strategic reach (Agni-III/V), more
precise cruise/tactical analogues (BrahMos, Pralay), not a USA/Japan copy and
not a Libya-style multi-ton J payload.

South Africa A-J, Syria A-J, Libya A-J, UAE A-J, Saudi A-J, Vietnam A-J,
Japan A-J, South Korea A-J, Iraq A-M, and 9P117 stay frozen.

Live catalogs: CommandSet.ini, CommandButton.ini, Weapon.ini.
Satellite last-wins: CommandSet_IndiaMissiles.ini,
CommandButton_IndiaMissiles.ini, Weapon\\Weapon_India_Missiles.ini.
India flag (saffron / white + Ashoka chakra / green) + names on dorsal UV.
Dedicated Ind_TEL saffron-olive truck. No RadarPriority. No rearm. No ZZZZ.
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

SRC_DATA = ROOT / "patch/Release/SPECTER_SOUTHAFRICA_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_SOUTHAFRICA_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_INDIA_MISSILES_AJ"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SAF = "1409644315a0f01e071ecacd96cc0d21aab61721ce2ea2560b17136f97415304"
SIZE_DATA_SAF = 368016423
SHA_ART_SAF = "bda1e04614392571bf2755b0202654627e5602feb81bb0cfc8d12b66ded127ff"
SIZE_ART_SAF = 1687098071

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY
TEL_W3D = sk.TEL_W3D
TELD_W3D = sk.TELD_W3D
PROJ_W3D = sk.PROJ_W3D

IND_CB_KEY = r"Data\INI\CommandButton_IndiaMissiles.ini"
IND_CS_KEY = r"Data\INI\CommandSet_IndiaMissiles.ini"
IND_WEP_KEY = r"Data\INI\Weapon\Weapon_India_Missiles.ini"
IND_FAC_KEY = (
    r"Data\INI\Object\Specter\Indian Armed Forces"
    r"\Buildings\India_MissileFactory.ini"
)
IND_VT72B_KEY = r"Data\INI\Object\Specter\Indian Armed Forces\Tracked\VT72B.ini"
IND_DOZER_KEY = r"Data\INI\Object\Specter\Indian Armed Forces\Tracked\India_Dozer.ini"
IND_SHAHEEN_KEY = (
    r"Data\INI\Object\Specter\Indian Armed Forces\Wheeled\India_ShaheenTEL.ini"
)
IND_ABABEEL_KEY = (
    r"Data\INI\Object\Specter\Indian Armed Forces\Wheeled\India_AbabeelTEL.ini"
)
IND_ALHUSS_KEY = r"Data\INI\Object\Specter\Indian Armed Forces\Wheeled\AbbasLauncher.ini"
IND_WEP_OLD_KEY = r"Data\INI\Weapon_India.ini"
IND_MIC_KEY = r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_MIC.ini"
IND_LGM_KEY = r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_Lgm30.ini"
IND_ZZZ_CS = r"Data\INI\CommandSet_ZZZZ_AfricaPakistanSyria_AirExp.ini"
IND_ZZZ_CB = r"Data\INI\CommandButton_ZZZZ_AfricaPakistanSyria_AirExp.ini"

TRUCK_TEX = "Ind_TEL.tga"
TRUCKD_TEX = "Ind_TELD.tga"
TRUCK_KEY = rf"Art\Textures\{TRUCK_TEX}"
TRUCKD_KEY = rf"Art\Textures\{TRUCKD_TEX}"

WEP_MARKER = (
    "; ===== India missiles A-J "
    "(Weapon.ini load path for Command_FireMainWeapon) ====="
)

BUILDERS = [
    "IndiaDozerCommandSet",
    "India_WorkerCommandSet",
    "India_VT72BCommandSet",
]

OLIVE = (138, 96, 40)
EARTH = (92, 64, 36)
SOOT = (48, 36, 28)
NOSE_W = (236, 228, 210)
NOSE_R = (196, 16, 28)
NOSE_G = (0, 140, 64)
NOSE_B = (20, 48, 140)

# Slot-to-color map is not Syria/SA/Libya. Saffron-olive truck + Tiranga.
# Gameplay values are SPECTER design, informed by public mission class, not claimed specs.
MISSILES = [
    {
        "slot": "A", "object": "India_Prahaar", "name": "Prahaar",
        "model": "Ind_Prahaar", "modeld": "Ind_PrahaarD", "proj_model": "Ind_PrahaarM",
        "hier": b"IND_PRAHA", "hierd": b"IND_PRAHAD", "proj_hier": b"IND_MSL_A",
        "tex": "Ind_PrahaarP.tga", "body": (210, 108, 22), "nose": NOSE_W,
        "expect": "orange", "km": 1000, "kg": 400, "acc": 74, "stealth": 22,
        "rebuild": 17, "price": 950,
        "role": "Tactical SRBM analogue (Prahaar; real ~150 km mapped to SPECTER floor)",
    },
    {
        "slot": "B", "object": "India_Prithvi", "name": "Prithvi",
        "model": "Ind_Prithvi", "modeld": "Ind_PrithviD", "proj_model": "Ind_PrithviM",
        "hier": b"IND_PRTHB", "hierd": b"IND_PRTHBD", "proj_hier": b"IND_MSL_B",
        "tex": "Ind_PrithviP.tga", "body": (88, 96, 42), "nose": NOSE_W,
        "expect": "muddy", "km": 1100, "kg": 800, "acc": 46, "stealth": 26,
        "rebuild": 24, "price": 1500,
        "role": "SRBM analogue (Prithvi-II class; heavier warhead, modest Acc)",
    },
    {
        "slot": "C", "object": "India_Pralay", "name": "Pralay",
        "model": "Ind_Pralay", "modeld": "Ind_PralayD", "proj_model": "Ind_PralayM",
        "hier": b"IND_PRALC", "hierd": b"IND_PRALCD", "proj_hier": b"IND_MSL_C",
        "tex": "Ind_PralayP.tga", "body": (222, 182, 28), "nose": NOSE_W,
        "expect": "yellow", "km": 1200, "kg": 400, "acc": 78, "stealth": 28,
        "rebuild": 26, "price": 1900,
        "role": "Precision tactical BM analogue (Pralay; higher Acc than Prithvi)",
    },
    {
        "slot": "D", "object": "India_Shaurya", "name": "Shaurya",
        "model": "Ind_Shaurya", "modeld": "Ind_ShauryaD", "proj_model": "Ind_ShauryaM",
        "hier": b"IND_SHAUD", "hierd": b"IND_SHAUDD", "proj_hier": b"IND_MSL_D",
        "tex": "Ind_ShauryaP.tga", "body": (10, 72, 84), "nose": NOSE_W,
        "expect": "petrol", "km": 1350, "kg": 500, "acc": 72, "stealth": 58,
        "rebuild": 34, "price": 3300,
        "role": "Boost-glide/canister analogue (Shaurya; MaxHealth proxy, not stealth)",
    },
    {
        "slot": "E", "object": "India_BrahMos", "name": "BrahMos",
        "model": "Ind_BrahMos", "modeld": "Ind_BrahMosD", "proj_model": "Ind_BrahMosM",
        "hier": b"IND_BRAHE", "hierd": b"IND_BRAHED", "proj_hier": b"IND_MSL_E",
        "tex": "Ind_BrahMosP.tga", "body": (28, 68, 168), "nose": NOSE_W,
        "expect": "blue", "km": 1500, "kg": 400, "acc": 84, "stealth": 62,
        "rebuild": 32, "price": 3600,
        "role": "Supersonic cruise analogue (BrahMos; high Acc/CHL, SPECTER range stretch)",
    },
    {
        "slot": "F", "object": "India_Nirbhay", "name": "Nirbhay",
        "model": "Ind_Nirbhay", "modeld": "Ind_NirbhayD", "proj_model": "Ind_NirbhayM",
        "hier": b"IND_NIRBF", "hierd": b"IND_NIRBFD", "proj_hier": b"IND_MSL_F",
        "tex": "Ind_NirbhayP.tga", "body": (8, 162, 56), "nose": NOSE_W,
        "expect": "green", "km": 1700, "kg": 550, "acc": 76, "stealth": 44,
        "rebuild": 38, "price": 3200,
        "role": "Subsonic cruise analogue (Nirbhay; longer than BrahMos, lower CHL)",
    },
    {
        "slot": "G", "object": "India_Agni1", "name": "Agni-I",
        "model": "Ind_Agni1", "modeld": "Ind_Agni1D", "proj_model": "Ind_Agni1M",
        "hier": b"IND_AGN1G", "hierd": b"IND_AGN1GD", "proj_hier": b"IND_MSL_G",
        "tex": "Ind_Agni1P.tga", "body": (220, 200, 155), "nose": NOSE_R,
        "expect": "cream", "km": 1900, "kg": 900, "acc": 50, "stealth": 32,
        "rebuild": 46, "price": 4000,
        "role": "SRBM/MRBM analogue (Agni-I; public ~700-1200 km, SPECTER stretch)",
    },
    {
        "slot": "H", "object": "India_AgniP", "name": "Agni-P",
        "model": "Ind_AgniP", "modeld": "Ind_AgniPD", "proj_model": "Ind_AgniPM",
        "hier": b"IND_AGNPH", "hierd": b"IND_AGNPHD", "proj_hier": b"IND_MSL_H",
        "tex": "Ind_AgniPP.tga", "body": (228, 224, 216), "nose": NOSE_G,
        "expect": "white", "km": 2500, "kg": 700, "acc": 68, "stealth": 38,
        "rebuild": 52, "price": 4600,
        "role": "Canister MRBM analogue (Agni Prime; lighter/more precise than Agni-I)",
    },
    {
        "slot": "I", "object": "India_Agni3", "name": "Agni-III",
        "model": "Ind_Agni3", "modeld": "Ind_Agni3D", "proj_model": "Ind_Agni3M",
        "hier": b"IND_AGN3I", "hierd": b"IND_AGN3ID", "proj_hier": b"IND_MSL_I",
        "tex": "Ind_Agni3P.tga", "body": (128, 128, 128), "nose": NOSE_R,
        "expect": "gray", "km": 3300, "kg": 1200, "acc": 52, "stealth": 36,
        "rebuild": 62, "price": 5600,
        "role": "IRBM analogue (Agni-III; public ~3000-3500 km class, uncertain)",
    },
    {
        "slot": "J", "object": "India_Agni5", "name": "Agni-V",
        "model": "Ind_Agni5", "modeld": "Ind_Agni5D", "proj_model": "Ind_Agni5M",
        "hier": b"IND_AGN5J", "hierd": b"IND_AGN5JD", "proj_hier": b"IND_MSL_J",
        "tex": "Ind_Agni5P.tga", "body": (168, 32, 28), "nose": NOSE_W,
        "expect": "red", "km": 4000, "kg": 1800, "acc": 58, "stealth": 42,
        "rebuild": 75, "price": 7200,
        "role": "ICBM-class analogue capped at SPECTER 4000 km (public estimates higher/uncertain)",
    },
]

NAME_MAP = [
    "A Prahaar new as India_Prahaar (tactical SRBM; distinct from IndiaVehiclePrahaar)",
    "B Prithvi new (Prithvi-II class SRBM analogue; heavier, modest Acc)",
    "C Pralay new (precision tactical BM analogue)",
    "D Shaurya new (boost-glide/canister analogue; MaxHealth proxy, not stealth)",
    "E BrahMos new as India_BrahMos (supersonic cruise analogue; SPECTER range stretch)",
    "F Nirbhay new (subsonic cruise analogue; longer than BrahMos)",
    "G Agni-I new as India_Agni1 (SRBM/MRBM analogue; SPECTER stretch)",
    "H Agni-P new as India_AgniP (Agni Prime canister MRBM analogue)",
    "I Agni-III new as India_Agni3 (IRBM analogue; public class uncertain)",
    "J Agni-V new as India_Agni5 (distinct from SpecialPower IndiaSpecialPowerAgniV; SPECTER cap)",
]

FROZEN_DATA = list(saf.FROZEN_DATA) + [
    saf.SAF_FAC_KEY, saf.SAF_CB_KEY, saf.SAF_CS_KEY, saf.SAF_WEP_KEY,
    IND_VT72B_KEY, IND_DOZER_KEY, IND_SHAHEEN_KEY, IND_ABABEEL_KEY,
    IND_ALHUSS_KEY, IND_WEP_OLD_KEY, IND_MIC_KEY, IND_LGM_KEY,
    IND_ZZZ_CS, IND_ZZZ_CB,
]
FROZEN_DATA += [m["unit_key"] for m in saf.DERIVED]
FROZEN_DATA += [m["proj_key"] for m in saf.DERIVED]

FROZEN_ART = list(saf.FROZEN_ART) + [
    saf.TRUCK_KEY, saf.TRUCKD_KEY,
    r"Art\Textures\Saf_MokopaP.tga", r"Art\W3D\Saf_Mokopa.W3D",
]
FROZEN_ART += [m["tex_key"] for m in saf.DERIVED]
FROZEN_ART += [m["tel_key"] for m in saf.DERIVED]
FROZEN_ART += [m["teld_key"] for m in saf.DERIVED]
FROZEN_ART += [m["projw_key"] for m in saf.DERIVED]

for _m in MISSILES:
    assert len(_m["hier"]) == 9 and len(_m["hierd"]) == 10 and len(_m["proj_hier"]) == 9
    assert 1000 <= _m["km"] <= 4000 and 400 <= _m["kg"] <= 10000


def derived(m: dict) -> dict:
    d = sk.derived({**m, "min_range": sk.MOTHER_MIN_RANGE})
    d["button"] = f"CB_INDIA_MISSILE_{m['slot']}"
    d["unit_key"] = (
        r"Data\INI\Object\Specter\Indian Armed Forces"
        rf"\Wheeled\{m['object']}.ini"
    )
    d["proj_key"] = (
        r"Data\INI\Object\Specter\Indian Armed Forces"
        rf"\{m['object']}_Projectile.ini"
    )
    return d


DERIVED = [derived(m) for m in MISSILES]


def make_india_flag() -> Image.Image:
    """Tiranga: saffron / white + navy Ashoka chakra / India green."""
    w, h = 900, 600
    im = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(im)
    saffron = (255, 153, 51, 255)
    white = (255, 255, 255, 255)
    green = (19, 136, 8, 255)
    navy = (0, 0, 128, 255)
    draw.rectangle([0, 0, w, h // 3], fill=saffron)
    draw.rectangle([0, h // 3, w, 2 * h // 3], fill=white)
    draw.rectangle([0, 2 * h // 3, w, h], fill=green)
    cx, cy = w / 2.0, h / 2.0
    r_out = h * 0.145
    width = max(5, int(h * 0.022))
    draw.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], outline=navy, width=width)
    spoke_w = max(3, int(h * 0.014))
    for i in range(24):
        ang = math.radians(-90 + i * 15)
        x2 = cx + r_out * 0.90 * math.cos(ang)
        y2 = cy + r_out * 0.90 * math.sin(ang)
        draw.line([(cx, cy), (x2, y2)], fill=navy, width=spoke_w)
    r_in = r_out * 0.20
    draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=navy)
    return im


def has_india_flag(counts: dict[str, int]) -> bool:
    saffronish = counts.get("orange", 0) + counts.get("yellow", 0) + counts.get("cream", 0)
    greenish = counts.get("green", 0) + counts.get("muddy", 0)
    return (
        saffronish >= 4
        and counts.get("white", 0) >= 4
        and greenish >= 4
        and counts.get("blue", 0) >= 2
    )


def recolor_truck(src: Image.Image, damaged: bool = False) -> Image.Image:
    """Map Iraqi tan sheet to India saffron-olive / earth / soot."""
    im = src.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            avg = (r + g + b) / 3.0
            sat = max(r, g, b) - min(r, g, b)
            if avg < 55 and sat < 35:
                px[x, y] = (max(0, int(r * 0.34)), max(0, int(g * 0.26)), max(0, int(b * 0.20)), a)
                continue
            if sat > 70 and avg > 70:
                base = OLIVE
                t = 0.92
            elif avg < 100:
                base = EARTH
                t = max(0.70, min(1.15, avg / 90.0))
            else:
                base = OLIVE
                t = max(0.55, min(1.25, avg / 130.0))
            nr = min(255, int(base[0] * t))
            ng = min(255, int(base[1] * t))
            nb = min(255, int(base[2] * t))
            if damaged:
                nr, ng, nb = int(nr * 0.70), int(ng * 0.66), int(nb * 0.58)
            px[x, y] = (nr, ng, nb, a)
    return im


def make_ind_tel_w3d(src: bytes, damaged: bool, m: dict) -> bytes:
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
        .replace("South Korea", "India")
        .replace("Side = SouthKorea", "Side = India")
        .replace(
            "Skr_TEL / Skr_TELD (not Irq_9P117 / Jpn_TEL)",
            "Ind_TEL / Ind_TELD (not Irq_9P117 / Jpn_TEL / Skr_TEL / Sau_TEL / Uae_TEL / Lby_TEL / Syr_TEL / Saf_TEL)",
        )
    )


def projectile_ini(m: dict) -> str:
    return sk.projectile_ini(m).replace("South Korea", "India")


def weapon_file(missiles: list[dict]) -> str:
    head = (
        WEP_MARKER + "\n"
        "; 9P117 scale. Dedicated India A-J. Distinct from SA/Syria/Libya/UAE/Saudi/Vietnam/Japan/SK/Iraq.\n"
        "; Indigenous BM/cruise mix. Agni-V capped at SPECTER 4000 km. Not a multi-ton Libya J.\n"
        "; ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000 (PR #629).\n"
        "; Death HACK is a separate path and is not folded into PrimaryDamage.\n"
        "; Acc/CHL columns are design labels mapped to ScatterRadius / MaxHealth.\n"
    )
    body = sk.weapon_blocks(missiles)
    pairs = body.split("\n\n", 1)[1] if "\n\n" in body else body
    return head + "\n" + pairs


def factory_ini() -> str:
    text = sk.factory_ini()
    text = text.replace("; South Korea missile factory.", "; India missile factory.")
    text = text.replace(
        "with a SouthKorea-only CommandSet (A-J).",
        "with an India-only CommandSet (A-J).",
    )
    text = text.replace("Object SouthKorea_MissileFactory", "Object India_MissileFactory")
    text = text.replace(
        "DisplayName      = OBJECT:SouthKoreaMissileFactory",
        "DisplayName      = OBJECT:IndiaMissileFactory",
    )
    text = text.replace("Side             = SouthKorea", "Side             = India")
    text = text.replace(
        "CommandSet       = SouthKorea_MissileFactoryCommandSet",
        "CommandSet       = India_MissileFactoryCommandSet",
    )
    return text


def factory_commandset() -> str:
    slots = "\r\n".join(f"  {i}  = {m['button']}" for i, m in enumerate(DERIVED, start=1))
    return (
        "CommandSet India_MissileFactoryCommandSet\r\n"
        f"{slots}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def with_india_factory(block: str) -> str:
    if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" not in block:
        raise SystemExit(f"expected isolated Iraq factory in:\n{block}")
    if "Command_ConstructIndia_MissileFactory" in block:
        raise SystemExit("India factory already present on builder")
    return block.replace(
        "Command_ConstructIraq_AlFahdMissileFactoryBuilding",
        "Command_ConstructIndia_MissileFactory",
    )


def commandbutton_all() -> str:
    lines = [
        "; India missiles A-J production buttons and factory construct button.",
        "; Shared specter_missile_* cameos. Unique Object bindings.",
        "",
        "CommandButton Command_ConstructIndia_MissileFactory",
        "  Command          = DOZER_CONSTRUCT",
        "  Object           = India_MissileFactory",
        "  TextLabel        = CONTROLBAR:ConstructIndiaMissileFactory",
        "  ButtonImage      = Button_MissileFactory",
        "  ButtonBorderType = BUILD",
        "  DescriptLabel    = CONTROLBAR:ToolTipIndiaMissileFactory",
        "End",
        "",
    ]
    for m in DERIVED:
        lines.extend(
            [
                f"CommandButton {m['button']}",
                "  Command       = UNIT_BUILD",
                f"  Object        = {m['object']}",
                f"  TextLabel     = CONTROLBAR:IndiaMissile{m['slot']}",
                f"  ButtonImage   = {m['cameo']}",
                "  ButtonBorderType = BUILD",
                f"  DescriptLabel = CONTROLBAR:ToolTipIndiaMissile{m['slot']}",
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
        f"Range: {m['km']} km\n"
        f"Warhead: {m['kg']} kg\n"
        f"Accuracy: {m['acc']}/100 (impact scatter, not a hit %)\n"
        f"Radar evasion: {m['stealth']}/100 (interceptor toughness, not stealth)\n"
        f"Build Time: {m['rebuild']} sec\n"
        f"Price: ${m['price']}"
    )


def csf_map() -> dict[str, str]:
    mapping = {
        "OBJECT:IndiaMissileFactory": "Missile Factory",
        "CONTROLBAR:ConstructIndiaMissileFactory": "Missile Factory",
        "CONTROLBAR:ToolTipIndiaMissileFactory": (
            "Missile Factory\nProduces India missiles A-J\nPrice: $1800"
        ),
    }
    for m in DERIVED:
        mapping[f"OBJECT:{m['object']}"] = m["name"]
        mapping[f"CONTROLBAR:IndiaMissile{m['slot']}"] = f"{m['slot']} {m['name']}"
        mapping[f"CONTROLBAR:ToolTipIndiaMissile{m['slot']}"] = player_tooltip(m)
    return mapping


def mapping_report() -> list[str]:
    lines = [
        "NAME MAPPING:",
        *[f"  {row}" for row in NAME_MAP],
        "",
        "EXISTING INDIA MISSILE OBJECTS PRESERVED (not factory A-J):",
        "  India_ShaheenTEL / India_Weapon_Shaheen",
        "  India_AbabeelTEL / India_Weapon_Ababeel",
        "  India_Alhussaien (AbbasLauncher.ini)",
        "  India_Lgm30 unchanged.",
        "  IndiaVehiclePrahaar / IndiaVehiclePinaka / IndiaVehicleAkash / IndiaVehicleNag unchanged.",
        "  SpecialPower IndiaSpecialPowerAgniV and Command_LaunchIndiaAgniVFromShortcut unchanged.",
        "",
        "FACTORY CONSTRUCT:",
        "  Pre-change Dozer/Worker/VT72B constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  Post-change those menus construct India_MissileFactory.",
        "  MIC remains on slot 6. Abbas / Lgm30 / FireBase / CRAM unchanged.",
        "",
        "REAL-WORLD vs GAMEPLAY:",
        "  Public sources credit India with an indigenous BM and cruise program: Prahaar,",
        "  Prithvi, Pralay, Shaurya, BrahMos (JV), Nirbhay, and Agni-I/II/III/IV/P/V.",
        "  Reported ranges are often uncertain (Agni-V commonly cited above 5000 km).",
        "  SPECTER floor is 1000 km and ceiling 4000 km, so tactical classes sit on the floor",
        "  and Agni-V is capped at 4000 km. Payloads stay in a 400-1800 kg band; not Libya J.",
        "  Values below are SPECTER design, not verified military specifications.",
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
    lines.extend(["", "MISSION ROLES:"])
    for m in DERIVED:
        lines.append(f"  {m['slot']} {m['name']}: {m['role']}")
    return lines


def validate(data, art, src_data, src_art, order) -> list[str]:
    fails: list[str] = []
    for key in FROZEN_DATA:
        if data.get(key) != src_data.get(key):
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
    sat_cs = data[IND_CS_KEY].decode("latin1")

    if "ZZZZ" in IND_CB_KEY or "ZZZZ" in IND_CS_KEY or "ZZZZ" in IND_WEP_KEY:
        fails.append("ZZZZ shortcut")
    if IND_CS_KEY >= r"Data\INI\CommandSet_ZZZZ":
        fails.append("India satellite sorts into ZZZZ")
    if IND_CS_KEY <= CS_KEY:
        fails.append("India satellite sorts before CommandSet.ini")

    for frozen_cs in (
        "Iraq_AlFahdMissileFactoryCommandSet",
        "Vietnam_MissileFactoryCommandSet",
        "Japan_MissileFactoryCommandSet",
        "SouthKorea_MissileFactoryCommandSet",
        "SaudiArabia_MissileFactoryCommandSet",
        "SaudiArabiaDozerCommandSet",
        "UAE_MissileFactoryCommandSet",
        "UAEDozerCommandSet",
        "UAE_WorkerCommandSet",
        "UAE_VT72BCommandSet",
        "Libya_MissileFactoryCommandSet",
        "LibyaDozerCommandSet",
        "Libya_WorkerCommandSet",
        "Libya_VT72BCommandSet",
        "Syria_MissileFactoryCommandSet",
        "SyriaDozerCommandSet",
        "Syria_WorkerCommandSet",
        "Syria_VT72BCommandSet",
        "SouthAfrica_MissileFactoryCommandSet",
        "SouthAfricaDozerCommandSet",
        "SouthAfrica_WorkerCommandSet",
        "SouthAfrica_VT72BCommandSet",
    ):
        if sk.last_block(cs_text, "CommandSet", frozen_cs) != sk.last_block(
            src_cs, "CommandSet", frozen_cs
        ):
            fails.append(f"{frozen_cs} mutated in CommandSet.ini")

    for name in BUILDERS:
        new_b = sk.last_block(cs_text, "CommandSet", name)
        if "Command_ConstructIndia_MissileFactory" not in new_b:
            fails.append(f"{name} catalog missing India factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in new_b:
            fails.append(f"{name} still has isolated Iraq factory")
        if "Command_ConstructIndia_MIC" not in new_b:
            fails.append(f"{name} lost MIC")
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", name)
        if "Command_ConstructIndia_MissileFactory" not in lw:
            fails.append(f"last-wins {name} from {_k} missing India factory")
        if "Command_ConstructIraq_AlFahdMissileFactoryBuilding" in lw:
            fails.append(f"last-wins {name} still Iraq factory")
        if name not in sat_cs:
            fails.append(f"satellite missing {name}")

    fac = sk.last_block(cs_text, "CommandSet", "India_MissileFactoryCommandSet")
    if not fac:
        fails.append("CommandSet.ini missing India factory roster")
    slots = re.findall(r"CB_INDIA_MISSILE_([A-Z])", fac)
    if slots != list("ABCDEFGHIJ"):
        fails.append(f"factory slots {slots} != A-J")
    if "Command_Sell" not in fac or "Command_SetRallyPoint" not in fac:
        fails.append("factory missing Rally/Sell")
    if any(
        tag in fac
        for tag in (
            "CB_VIETNAM_", "CB_JAPAN_", "CB_SOUTHKOREA_", "CB_SAUDIARABIA_",
            "CB_UAE_", "CB_LIBYA_", "CB_SYRIA_", "CB_SOUTHAFRICA_",
        )
    ):
        fails.append("factory mixed foreign buttons")

    construct = sk.last_block(cb_text, "CommandButton", "Command_ConstructIndia_MissileFactory")
    if sk.field(construct, "Object") != "India_MissileFactory":
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
    ):
        if sk.field(sk.last_block(cb_text, "CommandButton", btn), "ButtonImage") != img:
            fails.append(f"{btn} image lost")
        if sk.last_block(cb_text, "CommandButton", btn) != sk.last_block(src_cb, "CommandButton", btn):
            fails.append(f"{btn} mutated")

    fac_obj = sk.last_block(data[IND_FAC_KEY].decode("latin1"), "Object", "India_MissileFactory")
    if sk.field(fac_obj, "Side") != "India":
        fails.append("factory Side")
    if sk.field(fac_obj, "CommandSet") != "India_MissileFactoryCommandSet":
        fails.append("factory object CommandSet")
    if "SouthKorea_SupplyCenter" not in fac_obj:
        fails.append("factory lost SouthKorea_SupplyCenter prereq")
    if "India_SupplyCenter" not in fac_obj:
        fails.append("factory missing India_SupplyCenter prereq")

    if sk.last_block(wep_text, "Weapon", "Weapon_Vietnam_VCM01") != sk.last_block(
        src_wep, "Weapon", "Weapon_Vietnam_VCM01"
    ):
        fails.append("Vietnam VCM01 weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Japan_Tenrai") != sk.last_block(
        src_wep, "Weapon", "Weapon_Japan_Tenrai"
    ):
        fails.append("Japan Tenrai mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_SouthKorea_Baekho") != sk.last_block(
        src_wep, "Weapon", "Weapon_SouthKorea_Baekho"
    ):
        fails.append("SK Baekho mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_SaudiArabia_Najm") != sk.last_block(
        src_wep, "Weapon", "Weapon_SaudiArabia_Najm"
    ):
        fails.append("Saudi Najm weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_UAE_Falcon") != sk.last_block(
        src_wep, "Weapon", "Weapon_UAE_Falcon"
    ):
        fails.append("UAE Falcon weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Iraq_AlFahd500") != sk.last_block(
        src_wep, "Weapon", "Weapon_Iraq_AlFahd500"
    ):
        fails.append("AlFahd weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Libya_Fajr") != sk.last_block(
        src_wep, "Weapon", "Weapon_Libya_Fajr"
    ):
        fails.append("Libya Fajr weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_Syria_Luna") != sk.last_block(
        src_wep, "Weapon", "Weapon_Syria_Luna"
    ):
        fails.append("Syria Luna weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_SouthAfrica_Mokopa") != sk.last_block(
        src_wep, "Weapon", "Weapon_SouthAfrica_Mokopa"
    ):
        fails.append("South Africa Mokopa weapon mutated")
    if sk.last_block(data[IND_WEP_OLD_KEY].decode("latin1"), "Weapon", "India_Weapon_Shaheen") != sk.last_block(
        src_data[IND_WEP_OLD_KEY].decode("latin1"), "Weapon", "India_Weapon_Shaheen"
    ):
        fails.append("India Shaheen weapon mutated")

    if sk.illegal_floats(wep_text):
        fails.append(f"illegal floats {sk.illegal_floats(wep_text)}")

    r11 = sk.last_block(data[sk.R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB")
    if sk.field(r11, "BuildCost") != "1200":
        fails.append("9P117 BuildCost")

    uae_fac = sk.last_block(data[uae.UAE_FAC_KEY].decode("latin1"), "Object", "UAE_MissileFactory")
    if sk.field(uae_fac, "Side") != "UAE":
        fails.append("UAE factory Side mutated")
    sa_fac = sk.last_block(data[sa.SA_FAC_KEY].decode("latin1"), "Object", "SaudiArabia_MissileFactory")
    if sk.field(sa_fac, "Side") != "SaudiArabia":
        fails.append("Saudi factory Side mutated")
    lby_fac = sk.last_block(data[lby.LBY_FAC_KEY].decode("latin1"), "Object", "Libya_MissileFactory")
    if sk.field(lby_fac, "Side") != "Libya":
        fails.append("Libya factory Side mutated")
    syr_fac = sk.last_block(data[syr.SYR_FAC_KEY].decode("latin1"), "Object", "Syria_MissileFactory")
    if sk.field(syr_fac, "Side") != "Syria":
        fails.append("Syria factory Side mutated")
    saf_fac = sk.last_block(data[saf.SAF_FAC_KEY].decode("latin1"), "Object", "SouthAfrica_MissileFactory")
    if sk.field(saf_fac, "Side") != "SouthAfrica":
        fails.append("South Africa factory Side mutated")

    truck = Image.open(io.BytesIO(art[TRUCK_KEY])).convert("RGB")
    truck_avg = truck.resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
    if truck_avg[2] > truck_avg[0] + 20:
        fails.append(f"truck too blue {truck_avg}")
    irq_avg = Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == irq_avg:
        fails.append("truck still Iraqi donor")
    sau_avg = Image.open(io.BytesIO(src_art[sa.TRUCK_KEY])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == sau_avg:
        fails.append("truck still Saudi olive")
    uae_avg = Image.open(io.BytesIO(src_art[uae.TRUCK_KEY])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == uae_avg:
        fails.append("truck still UAE pearl")
    lby_avg = Image.open(io.BytesIO(src_art[lby.TRUCK_KEY])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == lby_avg:
        fails.append("truck still Libya ochre")
    syr_avg = Image.open(io.BytesIO(src_art[syr.TRUCK_KEY])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == syr_avg:
        fails.append("truck still Syria drab")
    saf_avg = Image.open(io.BytesIO(src_art[saf.TRUCK_KEY])).convert("RGB").resize(
        (1, 1), Image.Resampling.BOX
    ).getpixel((0, 0))
    if truck_avg == saf_avg:
        fails.append("truck still South Africa veld")

    wep_sat = data[IND_WEP_KEY].decode("latin1")
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
        if sk.field(unit, "Side") != "India":
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
        if "India_ShaheenTEL" in unit or "India_Alhussaien" in unit or "SouthAfrica_Mokopa" in unit:
            fails.append(f"{m['slot']} collided with existing TEL")

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
        if sk.csf_get(csf, f"CONTROLBAR:IndiaMissile{m['slot']}") != f"{m['slot']} {m['name']}":
            fails.append(f"{m['slot']} CSF name")
        if sk.csf_get(csf, f"CONTROLBAR:ToolTipIndiaMissile{m['slot']}") != player_tooltip(m):
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
                "Lby_TEL.tga", "Syr_TEL.tga", "Saf_TEL.tga",
            )
        ):
            fails.append(f"{m['slot']} foreign truck")

        im = Image.open(io.BytesIO(art[m["tex_key"]])).convert("RGB")
        tel_flag = sk.region_mode(im, (110, 180, 420, 290))
        if not has_india_flag(tel_flag):
            fails.append(f"{m['slot']} India flag {tel_flag}")
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
    fac_dir = LOOSE / "Object/Specter/Indian Armed Forces/Buildings"
    wheel_dir = LOOSE / "Object/Specter/Indian Armed Forces/Wheeled"
    proj_dir = LOOSE / "Object/Specter/Indian Armed Forces"
    wep_dir = LOOSE / "Weapon"
    for d in (fac_dir, wheel_dir, proj_dir, wep_dir):
        d.mkdir(parents=True, exist_ok=True)
    (fac_dir / "India_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    (wep_dir / "Weapon_India_Missiles.ini").write_text(weapon_file(DERIVED), encoding="utf-8")
    (LOOSE / "CommandButton_IndiaMissiles.ini").write_text(commandbutton_all(), encoding="utf-8")
    (LOOSE / "CommandSet_IndiaMissiles.ini").write_text(commandset_file(builders), encoding="utf-8")
    for m in DERIVED:
        (wheel_dir / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (proj_dir / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_SAF or SRC_DATA.stat().st_size != SIZE_DATA_SAF:
        raise SystemExit("DATA baseline is not SPECTER_SOUTHAFRICA_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_SAF or SRC_ART.stat().st_size != SIZE_ART_SAF:
        raise SystemExit("ART baseline is not SPECTER_SOUTHAFRICA_MISSILES_AJ")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art = sk.parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    flag = make_india_flag()
    truck = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCK_DDS])), damaged=False)
    truckd = recolor_truck(Image.open(io.BytesIO(src_art[sk.TRUCKD_DDS])), damaged=True)
    art[TRUCK_KEY] = sk.make_tga32(truck)
    art[TRUCKD_KEY] = sk.make_tga32(truckd)

    for m in DERIVED:
        skin = sk.make_skin(m["body"], m["nose"], m["name"], flag)
        art[m["tex_key"]] = sk.make_tga32(skin)
        art[m["tel_key"]] = make_ind_tel_w3d(src_art[TEL_W3D], False, m)
        art[m["teld_key"]] = make_ind_tel_w3d(src_art[TELD_W3D], True, m)
        art[m["projw_key"]] = sk.make_proj_w3d(src_art[PROJ_W3D], m)
        data[m["unit_key"]] = sk.to_crlf(unit_ini(m))
        data[m["proj_key"]] = sk.to_crlf(projectile_ini(m))

    data[IND_FAC_KEY] = sk.to_crlf(factory_ini())
    data[IND_WEP_KEY] = sk.to_crlf(weapon_file(DERIVED))
    data[IND_CB_KEY] = sk.to_crlf(commandbutton_all())
    data[CSF_KEY] = sk.csf_upsert(src_data[CSF_KEY], csf_map())

    cs = src_data[CS_KEY].decode("latin1")
    builders = {}
    for name in BUILDERS:
        old = sk.last_block(cs, "CommandSet", name)
        new = with_india_factory(old)
        builders[name] = new
        cs = sk.replace_last(cs, "CommandSet", name, new)
    if sk.last_block(cs, "CommandSet", "India_MissileFactoryCommandSet"):
        cs = sk.replace_last(cs, "CommandSet", "India_MissileFactoryCommandSet", factory_commandset())
    else:
        cs = cs.rstrip("\r\n") + "\r\n\r\n" + factory_commandset() + "\r\n"
    data[CS_KEY] = cs.encode("latin1")
    data[IND_CS_KEY] = sk.to_crlf(commandset_file(builders))

    cb = src_data[CB_KEY].decode("latin1")
    if "CommandButton Command_ConstructIndia_MissileFactory" in cb:
        raise SystemExit("CommandButton.ini already had India factory")
    extra = commandbutton_all().replace("\n", "\r\n")
    data[CB_KEY] = (cb.rstrip("\r\n") + "\r\n\r\n" + extra + "\r\n").encode("latin1")

    wep = src_data[WEAPON_KEY].decode("latin1")
    if WEP_MARKER in wep or "Weapon Weapon_India_Prahaar" in wep:
        raise SystemExit("Weapon.ini already had India A-J")
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
    (ext / "CommandSet.ini.India.txt").write_text(
        "\r\n\r\n".join(sk.last_block(packed_cs, "CommandSet", n) for n in BUILDERS)
        + "\r\n\r\n"
        + sk.last_block(packed_cs, "CommandSet", "India_MissileFactoryCommandSet")
        + "\r\n",
        encoding="utf-8",
    )
    (ext / "Weapon.ini.India.txt").write_text(weapon_file(DERIVED), encoding="utf-8")
    (ext / "India_MissileFactory.ini").write_text(factory_ini(), encoding="utf-8")
    for m in DERIVED:
        (ext / f"{m['object']}.ini").write_text(unit_ini(m), encoding="utf-8")
        (ext / f"{m['object']}_Projectile.ini").write_text(projectile_ini(m), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    preview = OUT / "PREVIEW"
    preview.mkdir()
    flag.save(preview / "IndiaFlag.png")
    truck.save(preview / "Ind_TEL.png")
    truckd.save(preview / "Ind_TELD.png")
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
    zip_path = ROOT / "patch/Release/SPECTER_INDIA_MISSILES_AJ.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    inv = [
        "PRE-CHANGE INDIA (packed last-wins, South Africa A-J baseline):",
        "  No India_MissileFactory.",
        "  Dozer/Worker/VT72B constructed isolated Iraq_AlFahdMissileFactoryBuilding.",
        "  MIC on slot 6. Existing ShaheenTEL / AbabeelTEL / Alhussaien / Lgm30 preserved.",
        "  Packed faction path: Indian Armed Forces. Side=India.",
        "",
        "POST-CHANGE INDIA:",
        "  Dedicated India_MissileFactory A-J + Rally/Sell.",
        "  Builder slot that held the isolated Iraq factory now builds the India factory.",
        "  Indigenous BM/cruise profile: 1000-4000 km, 400-1800 kg. Not a Syria/SA/Libya reskin.",
        "",
        "COUNTRY BALANCE (inspected packed / accepted factory A-J, not runtime):",
        "  Syria A-J caps 2200 km / 1500 kg. South Africa A-J caps 2400 km / 1200 kg.",
        "  Libya J 3900/8000, UAE J 4000/7000, Saudi J 4000/4000, Japan J 3600/4000.",
        "  India J Agni-V 4000 km / 1800 kg: SPECTER range cap, payload below Libya/UAE/Saudi J",
        "  and below Japan J kg, above Syria/SA J range. Acc generally higher on cruise/tactical",
        "  analogues (BrahMos 84, Pralay 78) than Syria/SA unguided rockets.",
        "  US/EU strategic systems remain on other production paths.",
        "  CHL is interceptor toughness (MaxHealth), not stealth. BrahMos/Shaurya are outliers.",
        "",
        *map_lines,
    ]
    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #638 s-southafrica-missiles-aj + PR #637 + #636 + #635 + #634 + #633 + #632 + #631 + #630 + #629",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "INDIA_FACTORY_NEW=YES",
        "SHAHEEN_ABABEEL_ALHUSS_LGM30_KEPT=YES",
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
        "NO_REARM=YES",
        "NO_RADARPRIORITY=YES",
        "ROSTER_COUNT=10",
        "KM_FLOOR=1000",
        "KM_CEILING_USED=4000",
        "KG_FLOOR=400",
        "KG_CEILING_USED=1800",
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
            "ZIP_FILE=SPECTER_INDIA_MISSILES_AJ.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #638",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-india-missiles-aj/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-india-missiles-aj/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-india-missiles-aj/SPECTER_INDIA_MISSILES_AJ.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-india-missiles-aj",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-india-missiles-aj",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "India complete missile roster A-J on the accepted factory/fire path.\n"
        "New country factory replaces the isolated Iraq factory construct on India builders.\n"
        "Existing ShaheenTEL, AbabeelTEL, Alhussaien, and Lgm30 are unchanged.\n"
        "Indigenous BM/cruise profile 1000-4000 km / 400-1800 kg. Not a Syria/SA/Libya reskin.\n"
        "Agni-V is capped at the SPECTER 4000 km ceiling; public range estimates are uncertain.\n"
        "South Africa A-J, Syria A-J, Libya A-J, UAE A-J, Saudi A-J, Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# India missiles A-J\n\n"
        "- New India_MissileFactory. Rally/Sell retained.\n"
        "- Replaces isolated Iraq factory construct on India Dozer, Worker, and VT72B.\n"
        "- MIC, Abbas, Lgm30, ShaheenTEL, AbabeelTEL, and Alhussaien preserved.\n"
        "- India Tiranga (saffron / white + Ashoka chakra / green) + exact names on dorsal UV bands.\n"
        "- Dedicated Ind_TEL saffron-olive truck. Ten-color tube palette distinct from SA/Syria/Libya.\n"
        "- Indigenous BM/cruise mix. Agni-V capped at SPECTER 4000 km / 1800 kg. Not ICBM-payload Libya J.\n"
        "- 5-minute clip reload on all ten PRIMARY weapons.\n"
        "- South Africa A-J, Syria A-J, Libya A-J, UAE A-J, Saudi A-J, Vietnam A-J, Japan A-J, South Korea A-J, Iraq A-M, and 9P117 unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(inv) + "\n", encoding="utf-8")
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_IndiaMissiles.ini last-wins India builder + factory CommandSets.\n"
        "CommandButton_IndiaMissiles.ini last-wins construct + A-J.\n"
        "Weapon\\Weapon_India_Missiles.ini last-wins Weapon_India_* factory pair.\n"
        "Weapon_India.ini (Shaheen/Ababeel and other India weapons) is unchanged.\n"
        "India_Prahaar/Prithvi/Pralay/Shaurya/BrahMos/Nirbhay/Agni1/AgniP/Agni3/Agni5 are new objects.\n"
        "IndiaVehiclePrahaar and SpecialPower IndiaSpecialPowerAgniV are unchanged.\n"
        "South Africa, Syria, Libya, UAE, Saudi, Vietnam, Japan, South Korea, Iraq, and 9P117 packed definitions are unchanged.\n"
    )
    art_notes = [
        "INDIA A-J ART MARKINGS (static inspection)",
        "",
        "Flag: saffron upper, white middle with navy Ashoka chakra, green lower.",
        "SPECTER Side=India / Indian Armed Forces identity. Not SA / Syria / UAE / Saudi / Iraq flags.",
        "Dedicated Ind_TEL / Ind_TELD saffron-olive truck. Not Irq_9P117 / Skr_TEL / Jpn_TEL / Sau_TEL / Uae_TEL / Lby_TEL / Syr_TEL / Saf_TEL.",
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
