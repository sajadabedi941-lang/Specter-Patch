#!/usr/bin/env python3
"""Pack new construct-button cameos into SPE ART/DATA BIGs.

Root cause: CommandButtons already last-win ButtonImage to specbtn_* /
Button_GlobalMarket, but those TGA files were never inside _SPEC_ART_ONE.big.
Missing textures fall through to each object's SelectPortrait (old atlas
cameos). Native country AD/radar UNIT_BUILD buttons still name those atlas
MappedImages (rus_s400r, pla_hq9b, ...).

This rebuild:
  * converts the uploaded 128x128 construct PNGs to SAGE 32-bit TGA
  * inserts them as Art\\Textures\\*.tga into _SPEC_ART_ONE.big
  * last-wins native UNIT_BUILD CommandButton ButtonImage only (not
    SelectPortrait, not GM shop names, not SpecterRadar drone names)

Starts from the Iraq-radar DATA BIG and the split-zip ART BIG.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

from PIL import Image

TGA_FOOTER = b"\x00" * 8 + b"TRUEVISION-XFILE.\x00"

PNG_TO_TGA = {
    "heron.png": "specbtn_heron.tga",
    "MQ_4 Global hawk.png": "specbtn_mq4.tga",
    "orlan_10.png": "specbtn_orlan10.tga",
    "shahed_136 mobile.png": "specbtn_shahedlnchr.tga",
    "Arrow AAM Launcher.png": "specbtn_mic_arrow.tga",
    "Radar an.png": "specbtn_mic_tpy2.tga",
    "92N6E Radar.png": "specbtn_mic_92n6r.tga",
    "S-400 TEL.png": "specbtn_mic_s400.tga",
    "Pantsir-S1M.png": "specbtn_mic_pantsir.tga",
    "Krasukha-4.png": "specbtn_mic_krasukha.tga",
    "96L6-TSP.png": "specbtn_mic_96l6tsp.tga",
    "S-500 TEL.png": "specbtn_mic_s500.tga",
    "HQ-9B TEL.png": "specbtn_mic_hq9.tga",
    "HT-233 Radar.png": "specbtn_mic_ht233.tga",
    "TRML-4D.png": "specbtn_mic_trml4d.tga",
    "system matching the existing repository object.png": "specbtn_mic_irist.tga",
    "Radar System usa.png": "specbtn_mic_ustpy2.tga",
    "THAAD Air Defence System.png": "specbtn_mic_thaad.tga",
}

GM_BUILDING_PNG = Path("patch/Art/Textures/Button_GlobalMarket.png")
GM_BUILDING_TGA = "Button_GlobalMarket.tga"

# Native UNIT_BUILD objects that still use old atlas ButtonImages.
# Iraq_MIC_* shop products already last-win to specbtn_mic_* — skip those.
OBJECT_BUTTONIMAGE = {
    "RussiaVehicleS400": "specbtn_mic_s400",
    "Russia_S400_Real": "specbtn_mic_s400",
    "Russia_S400_AI": "specbtn_mic_s400",
    "RussiaVehicleS500": "specbtn_mic_s500",
    "RussiaVehicle92N6R": "specbtn_mic_92n6r",
    "Russia_92N6R": "specbtn_mic_92n6r",
    "Arb_92N6E": "specbtn_mic_92n6r",
    "RussiaVehicle96L6TSP": "specbtn_mic_96l6tsp",
    "RussiaVehiclePantsirS1M": "specbtn_mic_pantsir",
    "Russia_PantsirS1M": "specbtn_mic_pantsir",
    "IranVehiclePantsirS1M": "specbtn_mic_pantsir",
    "Arb_Pantsir": "specbtn_mic_pantsir",
    "UAEVehiclePantsir": "specbtn_mic_pantsir",
    "RussiaVehicleKrasukha4": "specbtn_mic_krasukha",
    "Russia_Krasukha-4": "specbtn_mic_krasukha",
    "ChinaVehicleKrasukha4": "specbtn_mic_krasukha",
    "Arab_Krasukha-4": "specbtn_mic_krasukha",
    "ChinaVehicleHQ9": "specbtn_mic_hq9",
    "ChinaVehicleHT233": "specbtn_mic_ht233",
    "NatoVehicleTRML4D": "specbtn_mic_trml4d",
    "GermanyVehicleTRML4D": "specbtn_mic_trml4d",
    "FranceVehicleTRML4D": "specbtn_mic_trml4d",
    "BritainVehicleTRML4D": "specbtn_mic_trml4d",
    "ItalyVehicleTRML4D": "specbtn_mic_trml4d",
    "SwedenVehicleTRML4D": "specbtn_mic_trml4d",
    "TurkeyVehicleTRML4D": "specbtn_mic_trml4d",
    "UkraineVehicleTRML4D": "specbtn_mic_trml4d",
    "Specter_EU5_TRML4D": "specbtn_mic_trml4d",
    "NatoVehicleIRIST": "specbtn_mic_irist",
    "GermanyVehicleIRIST": "specbtn_mic_irist",
    "FranceVehicleIRIST": "specbtn_mic_irist",
    "BritainVehicleIRIST": "specbtn_mic_irist",
    "ItalyVehicleIRIST": "specbtn_mic_irist",
    "SwedenVehicleIRIST": "specbtn_mic_irist",
    "TurkeyVehicleIRIST": "specbtn_mic_irist",
    "UkraineVehicleIRIST": "specbtn_mic_irist",
    "Specter_EU5_IRIST": "specbtn_mic_irist",
    "Israel_Arrow": "specbtn_mic_arrow",
    "Israel_AN_TPY2": "specbtn_mic_tpy2",
    "US_AN_TPY2": "specbtn_mic_ustpy2",
    "US_THAAD": "specbtn_mic_thaad",
    "US_THAAD_Site_AI": "specbtn_mic_thaad",
}

DRONE_BUTTONS = (
    "Command_ConstructSpecterRadarHeron",
    "Command_ConstructSpecterRadarMQ4",
    "Command_ConstructSpecterRadarOrlan10",
    "Command_ConstructSpecterRadarShahedLauncher",
)

MIC_BUTTONS = (
    "Command_ConstructIraq_MIC_Arrow",
    "Command_ConstructIraq_MIC_AN_TPY2",
    "Command_ConstructIraq_MIC_92N6R",
    "Command_ConstructIraq_MIC_S400",
    "Command_ConstructIraq_MIC_PantsirS1M",
    "Command_ConstructIraq_MIC_Krasukha4",
    "Command_ConstructIraq_MIC_96L6TSP",
    "Command_ConstructIraq_MIC_S500",
    "Command_ConstructIraq_MIC_HQ9",
    "Command_ConstructIraq_MIC_HT233",
    "Command_ConstructIraq_MIC_TRML4D",
    "Command_ConstructIraq_MIC_IRIST",
    "Command_ConstructIraq_MIC_US_AN_TPY2",
    "Command_ConstructIraq_MIC_THAAD",
)

DATA_EXTRA = r"Data\INI\CommandButton_ZZZZ_ZZZZConstructCameos.ini"

BTN_RE = re.compile(
    r"(?m)^CommandButton\s+(\S+)\s*\r?\n(.*?)(?=^CommandButton\s|\Z)",
    re.S,
)
CS_RE = re.compile(
    r"(?m)^CommandSet\s+(\S+)\s*\r?\n(.*?)(?=^CommandSet\s|\Z)",
    re.S,
)
MI_RE = re.compile(
    r"(?m)^MappedImage\s+(\S+)\s*\r?\n(.*?)(?=^MappedImage\s|\Z)",
    re.S,
)
OBJ_RE = re.compile(
    r"(?m)^Object\s+(\S+)\s*\r?\n(.*?)(?=^Object\s|\Z)",
    re.S,
)
WPN_RE = re.compile(
    r"(?m)^Weapon\s+(\S+)\s*\r?\n(.*?)(?=^Weapon\s|\Z)",
    re.S,
)
OCL_RE = re.compile(
    r"(?m)^ObjectCreationList\s+(\S+)\s*\r?\n(.*?)(?=^ObjectCreationList\s|\Z)",
    re.S,
)


def read_big(path: Path) -> tuple[list[tuple[str, int, int]], bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


def file_map_from_entries(entries, raw) -> dict[str, bytes]:
    return {name: raw[off : off + size] for name, off, size in entries}


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def last_wins(file_map: dict[str, bytes], kind_re: re.Pattern) -> dict[str, tuple[str, str]]:
    wins: dict[str, tuple[str, str]] = {}
    for path in sorted(file_map, key=lambda n: n.lower()):
        if not path.lower().endswith(".ini"):
            continue
        text = file_map[path].decode("latin1")
        for m in kind_re.finditer(text):
            wins[m.group(1)] = (path, m.group(0))
    return wins


def field(body: str | None, key: str) -> str | None:
    if not body:
        return None
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", body)
    return m.group(1) if m else None


def png_to_tga128(png: Path) -> bytes:
    im = Image.open(png).convert("RGBA")
    im = im.resize((128, 128), Image.Resampling.LANCZOS)
    raw = bytearray()
    pix = im.load()
    for y in range(127, -1, -1):
        for x in range(128):
            r, g, b, a = pix[x, y]
            raw.extend((b, g, r, a))
    header = bytes([0, 0, 2]) + b"\x00" * 9 + struct.pack("<HH", 128, 128) + bytes([32, 8])
    return header + bytes(raw) + TGA_FOOTER


def rewrite_buttonimage(block: str, new_image: str) -> str:
    out, n = re.subn(
        r"(?im)^(\s*ButtonImage\s*=\s*)\S+",
        rf"\1{new_image}",
        block,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"ButtonImage rewrite failed:\n{block[:200]}")
    return out


def native_lastwin_ini(buttons: dict[str, tuple[str, str]]) -> tuple[str, list[dict]]:
    chunks = [
        "; SPECTER last-win. Construct-button ButtonImage only.",
        "; Native AD/radar UNIT_BUILD buttons that still named old atlas cameos.",
        "; Does not edit SelectPortrait, CommandSet, cost, weapons, or GM shop names.",
        "; Sorts after CommandButton_ZZZZ_ZZZ92N6E.ini so 92N6E Object alias is kept.",
        "",
    ]
    changed = []
    for name in sorted(buttons):
        src, block = buttons[name]
        cmd = field(block, "Command")
        obj = field(block, "Object")
        img = field(block, "ButtonImage")
        if cmd != "UNIT_BUILD" or not obj:
            continue
        if obj.startswith("Iraq_MIC_"):
            continue
        target = OBJECT_BUTTONIMAGE.get(obj)
        if not target or img == target:
            continue
        new_block = rewrite_buttonimage(block.strip(), target)
        chunks.append(new_block)
        chunks.append("")
        changed.append(
            {
                "command_button": name,
                "object": obj,
                "old_buttonimage": img,
                "new_buttonimage": target,
                "prior_src": src,
            }
        )
    if not changed:
        raise SystemExit("no native CommandButton ButtonImage last-wins produced")
    return "\n".join(chunks).replace("\n", "\r\n"), changed


def art_name_map(file_map: dict[str, bytes]) -> dict[str, str]:
    return {n.replace("/", "\\").lower(): n for n in file_map}


def validate(
    data_map: dict[str, bytes],
    art_map: dict[str, bytes],
    packed_tga: dict[str, bytes],
) -> dict:
    buttons = last_wins(data_map, BTN_RE)
    sets = last_wins(data_map, CS_RE)
    mapped = last_wins(data_map, MI_RE)
    objects = last_wins(data_map, OBJ_RE)
    weapons = last_wins(data_map, WPN_RE)
    ocls = last_wins(data_map, OCL_RE)
    art_l = art_name_map(art_map)

    def art_has(tga: str) -> str | None:
        key = rf"art\textures\{tga}".lower()
        return art_l.get(key)

    report_rows = []

    # MappedImages for new cameos must last-win to the packed TGA names.
    for mi, tga in [
        ("specbtn_heron", "specbtn_heron.tga"),
        ("specbtn_mq4", "specbtn_mq4.tga"),
        ("specbtn_orlan10", "specbtn_orlan10.tga"),
        ("specbtn_shahedlnchr", "specbtn_shahedlnchr.tga"),
        ("specbtn_mic_arrow", "specbtn_mic_arrow.tga"),
        ("specbtn_mic_tpy2", "specbtn_mic_tpy2.tga"),
        ("specbtn_mic_92n6r", "specbtn_mic_92n6r.tga"),
        ("specbtn_mic_s400", "specbtn_mic_s400.tga"),
        ("specbtn_mic_pantsir", "specbtn_mic_pantsir.tga"),
        ("specbtn_mic_krasukha", "specbtn_mic_krasukha.tga"),
        ("specbtn_mic_96l6tsp", "specbtn_mic_96l6tsp.tga"),
        ("specbtn_mic_s500", "specbtn_mic_s500.tga"),
        ("specbtn_mic_hq9", "specbtn_mic_hq9.tga"),
        ("specbtn_mic_ht233", "specbtn_mic_ht233.tga"),
        ("specbtn_mic_trml4d", "specbtn_mic_trml4d.tga"),
        ("specbtn_mic_irist", "specbtn_mic_irist.tga"),
        ("specbtn_mic_ustpy2", "specbtn_mic_ustpy2.tga"),
        ("specbtn_mic_thaad", "specbtn_mic_thaad.tga"),
        ("Button_GlobalMarket", "Button_GlobalMarket.tga"),
    ]:
        rec = mapped.get(mi)
        if not rec:
            raise SystemExit(f"MappedImage {mi} missing")
        src, body = rec
        tex = field(body, "Texture")
        if not tex or tex.lower() != tga.lower():
            raise SystemExit(f"MappedImage {mi} Texture={tex} expected {tga} ({src})")
        packed_name = art_has(tga)
        if not packed_name:
            raise SystemExit(f"ART missing {tga}")
        blob = art_map[packed_name]
        if blob != packed_tga[tga]:
            raise SystemExit(f"ART {tga} bytes do not match converted PNG")

    # Four drones
    drone_sets = []
    for b, img in zip(
        DRONE_BUTTONS,
        ("specbtn_heron", "specbtn_mq4", "specbtn_orlan10", "specbtn_shahedlnchr"),
    ):
        rec = buttons.get(b)
        if not rec:
            raise SystemExit(f"missing {b}")
        src, body = rec
        if field(body, "ButtonImage") != img:
            raise SystemExit(f"{b} ButtonImage={field(body,'ButtonImage')} expected {img}")
        if field(body, "Command") != "UNIT_BUILD":
            raise SystemExit(f"{b} Command changed")
    for cs, (src, body) in sorted(sets.items()):
        used = [b for b in DRONE_BUTTONS if b in body]
        if used:
            drone_sets.append({"commandset": cs, "src": src, "buttons": used})
    if len(drone_sets) < 10:
        raise SystemExit(f"too few radar CommandSets with four drones: {len(drone_sets)}")

    # GM building construct: Button_GlobalMarket, not a shop specbtn
    gm_btns = []
    for name, (src, body) in sorted(buttons.items()):
        if name == "Command_ConstructIraq_MIC" or name.endswith("_GlobalStore"):
            img = field(body, "ButtonImage")
            if img != "Button_GlobalMarket":
                raise SystemExit(f"{name} ButtonImage={img} expected Button_GlobalMarket")
            if field(body, "Command") != "DOZER_CONSTRUCT":
                raise SystemExit(f"{name} Command changed")
            gm_btns.append(name)

    # GM shop products stay specbtn_mic_*
    expected_mic = {
        "Command_ConstructIraq_MIC_Arrow": "specbtn_mic_arrow",
        "Command_ConstructIraq_MIC_AN_TPY2": "specbtn_mic_tpy2",
        "Command_ConstructIraq_MIC_92N6R": "specbtn_mic_92n6r",
        "Command_ConstructIraq_MIC_S400": "specbtn_mic_s400",
        "Command_ConstructIraq_MIC_PantsirS1M": "specbtn_mic_pantsir",
        "Command_ConstructIraq_MIC_Krasukha4": "specbtn_mic_krasukha",
        "Command_ConstructIraq_MIC_96L6TSP": "specbtn_mic_96l6tsp",
        "Command_ConstructIraq_MIC_S500": "specbtn_mic_s500",
        "Command_ConstructIraq_MIC_HQ9": "specbtn_mic_hq9",
        "Command_ConstructIraq_MIC_HT233": "specbtn_mic_ht233",
        "Command_ConstructIraq_MIC_TRML4D": "specbtn_mic_trml4d",
        "Command_ConstructIraq_MIC_IRIST": "specbtn_mic_irist",
        "Command_ConstructIraq_MIC_US_AN_TPY2": "specbtn_mic_ustpy2",
        "Command_ConstructIraq_MIC_THAAD": "specbtn_mic_thaad",
    }
    for b, img in expected_mic.items():
        rec = buttons.get(b)
        if not rec:
            raise SystemExit(f"missing shop button {b}")
        src, body = rec
        if field(body, "ButtonImage") != img:
            raise SystemExit(f"shop {b} ButtonImage={field(body,'ButtonImage')} expected {img}")
        if "CommandSet" in src:
            raise SystemExit(f"shop button last-win path unexpected: {src}")

    # Native objects now point at dedicated specbtn images
    for obj, img in OBJECT_BUTTONIMAGE.items():
        hits = [
            (n, field(body, "ButtonImage"), src)
            for n, (src, body) in buttons.items()
            if field(body, "Command") == "UNIT_BUILD" and field(body, "Object") == obj
        ]
        if not hits:
            continue
        for n, got, src in hits:
            if got != img:
                raise SystemExit(f"{n} Object={obj} ButtonImage={got} expected {img} ({src})")

    # SelectPortrait of GM building / drones / MIC copies must stay atlas names
    portraits = {
        "Iraq_MIC": "irq_mic",
        "Germany_GlobalStore": "irq_mic",
        "SpecterRadar_Heron": "Nat_heron",
        "SpecterRadar_MQ4": "us_mq4",
        "SpecterRadar_Orlan10": "rus_orlan10",
        "SpecterRadar_ShahedLauncher": "irn_shahedlncher",
        "Iraq_MIC_S400": "rus_s400r",
        "Iraq_MIC_HQ9": "pla_hq9b",
        "RussiaVehicleS400": "rus_s400r",
        "ChinaVehicleHQ9": "pla_hq9b",
        "ChinaVehicleHT233": "pla_ht233",
        "Russia_92N6R": "rus_92n6r",
    }
    for obj, portrait in portraits.items():
        rec = objects.get(obj)
        if not rec:
            raise SystemExit(f"Object {obj} missing")
        got = field(rec[1], "SelectPortrait")
        if got != portrait:
            raise SystemExit(f"{obj} SelectPortrait={got} expected {portrait} (must not reuse specbtn)")

    # Prior radar / Iraq last-wins
    cs_src, cs = sets["Iraq_RadarStationCommandSet"]
    if "Command_SpySatelliteScan" in cs or "Command_SpecterSpySatelliteFee" in cs:
        raise SystemExit(f"Iraq radar CommandSet regained Spy Satellite ({cs_src})")
    if "Command_IraqiRadarSearch" not in cs:
        raise SystemExit("Iraq radar lost Command_IraqiRadarSearch")
    for b in DRONE_BUTTONS:
        if b not in cs:
            raise SystemExit(f"Iraq radar lost {b}")
    obj_src, obj = objects["Iraq_RadarStation"]
    if "SpecialPowerSpySatellite" in obj or "P30_Radar_Deploy_St" in obj:
        raise SystemExit(f"Iraq_RadarStation last-win broken ({obj_src})")
    if "RadarUpgrade" not in obj or "Upgrade_AmericaRadar" not in obj:
        raise SystemExit("Iraq_RadarStation radar grant/upgrade lost")
    _, dl = weapons["92N6R_FireControlDataLink"]
    if "DamageDealtAtSelfPosition = Yes" not in dl:
        raise SystemExit("92N6R_FireControlDataLink last-win lost")
    _, htdl = weapons["HT233_FireControlDataLink"]
    if "DamageDealtAtSelfPosition = Yes" not in htdl:
        raise SystemExit("HT233_FireControlDataLink last-win lost")
    _, hq = ocls["OCL_HQ9_Deployed"]
    if "HQ9_FireControlSystem" not in hq:
        raise SystemExit("OCL_HQ9_Deployed last-win lost")
    n6_src, n6 = buttons["Command_ConstructRussian_92N6E"]
    if field(n6, "Object") != "RussiaVehicle92N6R":
        raise SystemExit(f"92N6E construct Object alias lost ({n6_src})")
    if field(n6, "ButtonImage") != "specbtn_mic_92n6r":
        raise SystemExit("92N6E construct ButtonImage not updated")

    # Packed TGAs must be unique (one unit's image must not replace another)
    hashes = {n: hashlib.sha256(b).hexdigest() for n, b in packed_tga.items()}
    rev: dict[str, list[str]] = {}
    for n, h in hashes.items():
        rev.setdefault(h, []).append(n)
    dups = {h: v for h, v in rev.items() if len(v) > 1}
    if dups:
        raise SystemExit(f"duplicate packed button TGAs: {dups}")

    spy_btn = buttons.get("Command_SpySatelliteScan")
    if not spy_btn or "SpecialPowerSpySatellite" not in spy_btn[1]:
        raise SystemExit("Command_SpySatelliteScan must remain for other buildings")

    return {
        "drone_commandsets": drone_sets,
        "gm_construct_buttons": gm_btns,
        "mappedimages": {
            mi: {
                "src": mapped[mi][0],
                "texture": field(mapped[mi][1], "Texture"),
                "art_entry": art_has(field(mapped[mi][1], "Texture")),
            }
            for mi in (
                "Button_GlobalMarket",
                "specbtn_heron",
                "specbtn_mq4",
                "specbtn_orlan10",
                "specbtn_shahedlnchr",
            )
            + tuple(expected_mic.values())
        },
        "tga_sha256": hashes,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-data", type=Path, required=True)
    ap.add_argument("--src-art", type=Path, required=True)
    ap.add_argument("--patch-root", type=Path, default=Path("patch"))
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    data_entries, data_raw = read_big(args.src_data)
    data_map = file_map_from_entries(data_entries, data_raw)
    art_entries, art_raw = read_big(args.src_art)
    art_map = file_map_from_entries(art_entries, art_raw)
    del data_raw, art_raw

    buttons = last_wins(data_map, BTN_RE)
    extra_text, native_changed = native_lastwin_ini(buttons)
    if DATA_EXTRA in data_map:
        raise SystemExit(f"already present: {DATA_EXTRA}")
    data_map[DATA_EXTRA] = extra_text.encode("latin1")

    packed_tga: dict[str, bytes] = {}
    png_root = args.patch_root
    for png_name, tga_name in PNG_TO_TGA.items():
        png = png_root / png_name
        if not png.is_file():
            raise SystemExit(f"missing PNG {png}")
        packed_tga[tga_name] = png_to_tga128(png)
    gm_png = GM_BUILDING_PNG if GM_BUILDING_PNG.is_file() else png_root / "Art/Textures/Button_GlobalMarket.png"
    if not gm_png.is_file():
        raise SystemExit(f"missing {gm_png}")
    packed_tga[GM_BUILDING_TGA] = png_to_tga128(gm_png)

    art_l = art_name_map(art_map)
    replaced_art = []
    for tga_name, blob in packed_tga.items():
        key = rf"art\textures\{tga_name}".lower()
        if key in art_l:
            old = art_l[key]
            art_map.pop(old)
            replaced_art.append(old)
        art_map[rf"Art\Textures\{tga_name}"] = blob

    meta = validate(data_map, art_map, packed_tga)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_data = args.out_dir / "_SPEC_DATA_ONE.big"
    out_art = args.out_dir / "_SPEC_ART_ONE.big"
    data_bytes = build_big(data_map)
    art_bytes = build_big(art_map)
    out_data.write_bytes(data_bytes)
    out_art.write_bytes(art_bytes)

    # Re-read to confirm header size field
    for path in (out_data, out_art):
        rebuilt, rraw = read_big(path)
        hdr_size = struct.unpack(">I", rraw[4:8])[0]
        if hdr_size != len(rraw):
            raise SystemExit(f"{path.name} size field {hdr_size} != file {len(rraw)}")

    data_sha = sha256_file(out_data)
    art_sha = sha256_file(out_art)
    Path(str(out_data) + ".sha256").write_text(data_sha + "\n")
    Path(str(out_art) + ".sha256").write_text(art_sha + "\n")

    summary = {
        "src_data_size": args.src_data.stat().st_size,
        "src_art_size": args.src_art.stat().st_size,
        "out_data_size": out_data.stat().st_size,
        "out_art_size": out_art.stat().st_size,
        "out_data_sha256": data_sha,
        "out_art_sha256": art_sha,
        "data_extra": DATA_EXTRA,
        "native_buttonimage_lastwins": native_changed,
        "packed_tga": sorted(packed_tga),
        "replaced_art": replaced_art,
        "validation": meta,
    }
    (args.out_dir / "patch_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"DATA {out_data.stat().st_size} sha256={data_sha} extra={DATA_EXTRA}")
    print(f"ART  {out_art.stat().st_size} sha256={art_sha} tga={len(packed_tga)}")
    print(f"Native ButtonImage last-wins: {len(native_changed)}")
    for row in native_changed:
        print(f"  {row['command_button']}: {row['old_buttonimage']} -> {row['new_buttonimage']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
