#!/usr/bin/env python3
"""Aircraft-only global + Iraq/NK/Iran pass. Source: prior donor-update BIGs.

Does not touch PlayerTemplate, Science, War Factory, or ground CommandSets.
Does not modify China J-7 / China CH-5/Z-18A/slots (already correct).
Does not change Iranian weapons.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/aircraft_donor_update/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/aircraft_donor_update/_SPEC_ART_ONE.big")
DONOR = Path("/tmp/new_donor_extract/New folder")
OUT_DIR = Path("/tmp/aircraft_global_update")

LOCKED_PATHS = {
    r"data\ini\playertemplate.ini",
    r"data\ini\science.ini",
}

DONOR_ART = {
    "00PMBeta999.big": [
        r"Art\Textures\F14TB.tga",
        r"Art\Textures\LSFF14A.dds",
        r"Art\Textures\LSFF14Ad.dds",
        r"Art\w3d\LSFIRF14A.W3D",
        r"Art\w3d\LSFIRF14Ad.W3D",
    ],
}

# Existing working bomb chains — different per aircraft, no new Weapon blocks.
BOMB_SWAPS = {
    "VietnamJetMig21bis": ("VietnamJetMig21bis_WpnBomb", "China_Weapon_Bomb_Q5"),
    "IndiaJetMig21Bison": ("IndiaJetMig21Bison_WpnBomb", "2x_ODAB_500_PMV_SU24_LR"),
    "LibyaJetJ7": ("LibyaJetJ7_WpnBomb", "China_Weapon_FAB_J7"),
    "NorthKoreaJetJ7": ("NorthKoreaJetJ7_WpnBomb", "Kab500_LeaserGuidedBomb"),
    "NorthKoreaJetJ7B": ("NorthKoreaJetJ7B_WpnBomb", "China_Weapon_Bomb_Q5"),
    "SyriaJetJ7": ("SyriaJetJ7_WpnBomb", "2x_ODAB_500_PMV_SU24_LR"),
    "PakistanJetF7P": ("PakistanJetF7P_WpnBomb", "China_Weapon_FAB2_J7"),
    "PakistanJetF7PG": ("Pakistan_Weapon_Bomb_F7PG", "3x_ODAB_500_PMV_SU24"),
}

SCALE_ONLY = {
    "IranJetMig21Bis": 0.10,
    "IranJetF7N": 0.10,
    "NorthKoreaJetMig21PF": 0.10,
    "IraqJetF16IQ": 0.10,
    "VietnamJetMig21bis": 0.10,
    "IndiaJetMig21Bison": 0.10,
    "LibyaJetJ7": 0.10,
    "NorthKoreaJetJ7": 0.10,
    "NorthKoreaJetJ7B": 0.10,
    "SyriaJetJ7": 0.10,
    "PakistanJetF7P": 0.10,
    "PakistanJetF7PG": 0.10,
    "NorthKoreaJetMig29UB": 0.10,
}

CSF_LABELS = {
    "CONTROLBAR:ConstructIraqJetF16IQ": "F-16IQ",
    "CONTROLBAR:ToolTipIraqJetF16IQ": "Iraqi F-16IQ.",
    "CONTROLBAR:ConstructIraqJetMig21": "MiG-21",
    "CONTROLBAR:ToolTipIraqJetMig21": "Iraqi MiG-21.",
    "CONTROLBAR:ConstructIraqJetSu25UB": "Su-25UB",
    "CONTROLBAR:ToolTipIraqJetSu25UB": "Iraqi Su-25UB.",
    "CONTROLBAR:ConstructIraqJetL159": "L-159",
    "CONTROLBAR:ToolTipIraqJetL159": "Iraqi L-159.",
    "CONTROLBAR:ConstructIraqJetF14Tomcat": "F-14 Tomcat",
    "CONTROLBAR:ToolTipIraqJetF14Tomcat": "F-14 Tomcat. JH-7A2 bombs.",
    "OBJECT:IraqJetF14Tomcat": "F-14 Tomcat",
    "CONTROLBAR:ConstructIranJetF14AM": "F-14AM",
    "CONTROLBAR:ToolTipIranJetF14AM": "Iranian F-14AM.",
    "CONTROLBAR:ConstructIranJetF4E": "F-4E Phantom",
    "CONTROLBAR:ToolTipIranJetF4E": "Iranian F-4E.",
    "CONTROLBAR:ConstructIranJetMig21Bis": "MiG-21bis",
    "CONTROLBAR:ToolTipIranJetMig21Bis": "Iranian MiG-21bis.",
    "CONTROLBAR:ConstructIranJetF7N": "F-7N",
    "CONTROLBAR:ToolTipIranJetF7N": "Iranian F-7N.",
    "CONTROLBAR:ConstructIranJetSu35S": "Su-35S",
    "CONTROLBAR:ToolTipIranJetSu35S": "Iranian Su-35S.",
    "CONTROLBAR:ConstructNorthKoreaJetMig21": "MiG-21",
    "CONTROLBAR:ToolTipNorthKoreaJetMig21": "North Korean MiG-21.",
    "CONTROLBAR:ConstructNorthKoreaJetMig21PF": "MiG-21PF",
    "CONTROLBAR:ToolTipNorthKoreaJetMig21PF": "North Korean MiG-21PF.",
    "CONTROLBAR:ConstructNorthKoreaJetJ7": "J-7",
    "CONTROLBAR:ToolTipNorthKoreaJetJ7": "North Korean J-7.",
    "CONTROLBAR:ConstructNorthKoreaJetJ7B": "J-7B",
    "CONTROLBAR:ToolTipNorthKoreaJetJ7B": "North Korean J-7B.",
    "CONTROLBAR:ConstructNorthKoreaJetMig29UB": "MiG-29UB",
    "CONTROLBAR:ToolTipNorthKoreaJetMig29UB": "North Korean MiG-29UB.",
    "CONTROLBAR:ConstructNorthKoreaBomberIl28": "Il-28",
    "CONTROLBAR:ToolTipNorthKoreaBomberIl28": "Il-28 heavy bomber. Six SU-34 guided bombs.",
    "OBJECT:NorthKoreaBomberIl28": "Il-28",
    "CONTROLBAR:ConstructNorthKoreaJetIL76": "Il-76",
    "CONTROLBAR:ToolTipNorthKoreaJetIL76": "North Korean Il-76 transport.",
    "OBJECT:NorthKoreaJetIL76": "Il-76",
    "CONTROLBAR:ConstructNorthKoreaUAVSaetbyol": "Saetbyol",
    "CONTROLBAR:ToolTipNorthKoreaUAVSaetbyol": "Saetbyol recon UAV. No weapons.",
    "OBJECT:NorthKoreaUAVSaetbyol": "Saetbyol",
}

NEW_BUTTONS = {
    "Command_ConstructIraqJetF16IQ": ("IraqJetF16IQ", "SPEC_IraqJetF16IQ", "CONTROLBAR:ConstructIraqJetF16IQ", "CONTROLBAR:ToolTipIraqJetF16IQ"),
    "Command_ConstructIraqJetMig21": ("IraqJetMig21", "SPEC_IraqJetMig21", "CONTROLBAR:ConstructIraqJetMig21", "CONTROLBAR:ToolTipIraqJetMig21"),
    "Command_ConstructIraqJetSu25UB": ("IraqJetSu25UB", "SPEC_IraqJetSu25UB", "CONTROLBAR:ConstructIraqJetSu25UB", "CONTROLBAR:ToolTipIraqJetSu25UB"),
    "Command_ConstructIraqJetL159": ("IraqJetL159", "SPEC_IraqJetL159", "CONTROLBAR:ConstructIraqJetL159", "CONTROLBAR:ToolTipIraqJetL159"),
    "Command_ConstructIraqJetF14Tomcat": ("IraqJetF14Tomcat", "F14", "CONTROLBAR:ConstructIraqJetF14Tomcat", "CONTROLBAR:ToolTipIraqJetF14Tomcat"),
    "Command_ConstructIranJetF14AM": ("IranJetF14AM", "SPEC_IranJetF14AM", "CONTROLBAR:ConstructIranJetF14AM", "CONTROLBAR:ToolTipIranJetF14AM"),
    "Command_ConstructIranJetF4E": ("IranJetF4E", "SPEC_IranF4E", "CONTROLBAR:ConstructIranJetF4E", "CONTROLBAR:ToolTipIranJetF4E"),
    "Command_ConstructIranJetMig21Bis": ("IranJetMig21Bis", "SPEC_IranMig21Bis", "CONTROLBAR:ConstructIranJetMig21Bis", "CONTROLBAR:ToolTipIranJetMig21Bis"),
    "Command_ConstructIranJetF7N": ("IranJetF7N", "SPEC_IranF7N", "CONTROLBAR:ConstructIranJetF7N", "CONTROLBAR:ToolTipIranJetF7N"),
    "Command_ConstructIranJetSu35S": ("IranJetSu35S", "SPEC_IranSu35S", "CONTROLBAR:ConstructIranJetSu35S", "CONTROLBAR:ToolTipIranJetSu35S"),
    "Command_ConstructNorthKoreaJetMig21": ("NorthKoreaJetMig21", "SPEC_NorthKoreaJetMig21", "CONTROLBAR:ConstructNorthKoreaJetMig21", "CONTROLBAR:ToolTipNorthKoreaJetMig21"),
    "Command_ConstructNorthKoreaJetMig21PF": ("NorthKoreaJetMig21PF", "SPEC_NorthKoreaJetMig21PF", "CONTROLBAR:ConstructNorthKoreaJetMig21PF", "CONTROLBAR:ToolTipNorthKoreaJetMig21PF"),
    "Command_ConstructNorthKoreaJetJ7": ("NorthKoreaJetJ7", "SPEC_NorthKoreaJetJ7", "CONTROLBAR:ConstructNorthKoreaJetJ7", "CONTROLBAR:ToolTipNorthKoreaJetJ7"),
    "Command_ConstructNorthKoreaJetJ7B": ("NorthKoreaJetJ7B", "SPEC_NorthKoreaJetJ7B", "CONTROLBAR:ConstructNorthKoreaJetJ7B", "CONTROLBAR:ToolTipNorthKoreaJetJ7B"),
    "Command_ConstructNorthKoreaJetMig29UB": ("NorthKoreaJetMig29UB", "SPEC_NorthKoreaJetMig29UB", "CONTROLBAR:ConstructNorthKoreaJetMig29UB", "CONTROLBAR:ToolTipNorthKoreaJetMig29UB"),
    "Command_ConstructNorthKoreaBomberIl28": ("NorthKoreaBomberIl28", "rus_tu22m3m", "CONTROLBAR:ConstructNorthKoreaBomberIl28", "CONTROLBAR:ToolTipNorthKoreaBomberIl28"),
    "Command_ConstructNorthKoreaJetIL76": ("NorthKoreaJetIL76", "CargoIL76Russia", "CONTROLBAR:ConstructNorthKoreaJetIL76", "CONTROLBAR:ToolTipNorthKoreaJetIL76"),
    "Command_ConstructNorthKoreaUAVSaetbyol": ("NorthKoreaUAVSaetbyol", "Dozor600", "CONTROLBAR:ConstructNorthKoreaUAVSaetbyol", "CONTROLBAR:ToolTipNorthKoreaUAVSaetbyol"),
}

MAPPED_IMAGES = """MappedImage F14
  Texture = F14TB.tga
  TextureWidth = 128
  TextureHeight = 128
  Coords = Left:0 Top:0 Right:128 Bottom:128
  Status = NONE
End
"""


def parse_big(path: Path):
    data = path.read_bytes()
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for _ in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((name, data[eoff : eoff + esz]))
    return entries


def build_big_ordered(entries):
    header_size = 16
    encoded = [(n.encode("latin1"), b) for n, b in entries]
    for nb, _blob in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for nb, blob in encoded:
        index.append((nb, offset, len(blob)))
        blobs.append(blob)
        offset += len(blob)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def decode(blob: bytes) -> str:
    if blob[:2] == b"\xff\xfe":
        return blob.decode("utf-16-le")
    return blob.decode("latin1")


def encode(text: str, orig: bytes) -> bytes:
    if orig[:2] == b"\xff\xfe":
        return orig[:2] + text.encode("utf-16-le")
    return text.encode("latin1")


def patch_named_object(text: str, objname: str, fn) -> str:
    parts = re.split(r"(?m)(?=^Object(?:Reskin)?\s+\S+)", text)
    out = []
    for p in parts:
        if re.match(rf"(?m)^Object(?:Reskin)?\s+{re.escape(objname)}\b", p):
            p = fn(p)
        out.append(p)
    return "".join(out)


def bump_scale(part: str, delta: float) -> str:
    def sub(m):
        try:
            v = float(m.group(2))
        except ValueError:
            return m.group(0)
        return f"{m.group(1)}{v + delta:.2f}"

    new = re.sub(r"(?im)^(\s*Scale\s*=\s*)([0-9.]+)", sub, part)
    if new != part:
        return new
    n = nl(part)
    if re.search(r"(?im)^\s*DefaultConditionState\b", part):
        return re.sub(
            r"(?im)^(\s*DefaultConditionState\s*)$",
            rf"\1{n}      Scale = {1.0 + delta:.2f}",
            part,
            count=1,
        )
    return part


def replace_first_weaponset_primary(text: str, weapon: str) -> str:
    n = nl(text)
    pat = re.compile(
        r"(?ms)^(\s*WeaponSet\s*\n\s*Conditions\s*=\s*None\s*\n).*?^(\s*End\s*)$",
    )
    block = (
        f"  WeaponSet{n}"
        f"    Conditions = None{n}"
        f"    Weapon = PRIMARY {weapon}{n}"
        f"    PreferredAgainst = PRIMARY STRUCTURE VEHICLE{n}"
        f"    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI{n}"
        f"  End"
    )
    if pat.search(text):
        return pat.sub(block, text, count=1)
    return text


def strip_iraq_airfield_tiers(part: str) -> str:
    part = re.sub(
        r"(?im)^(\s*CommandSet\s*=\s*)Iraq_AirfieldCommandSet_T\b",
        r"\1Iraq_AirfieldCommandSet",
        part,
    )
    part = re.sub(
        r"(?ms)^\s*Behavior\s*=\s*CommandSetUpgrade ModuleTag_Tier[123]\s*\n.*?^\s*End\s*\n",
        "",
        part,
    )
    return part


def patch_object_file(name: str, blob: bytes) -> bytes:
    key = name.replace("/", "\\").lower()
    text = decode(blob)
    orig = text

    # Iraq airfield unlock (player builds Iraq_Airfield_T)
    if "iraq" in key and "airfield" in key and "\\object\\" in key:
        for obj in ("Iraq_Airfield_T", "Iraq_Airfield", "Iraq_Airfield_AI"):
            text = patch_named_object(text, obj, strip_iraq_airfield_tiers)

    targets = set(SCALE_ONLY) | set(BOMB_SWAPS) | {"NorthKoreaJetMig29UB"}
    for obj in targets:
        if obj not in text:
            continue

        def apply(part, obj=obj):
            if obj in SCALE_ONLY:
                part = bump_scale(part, SCALE_ONLY[obj])
            if obj in BOMB_SWAPS:
                old, new = BOMB_SWAPS[obj]
                part = part.replace(old, new)
            if obj == "NorthKoreaJetMig29UB":
                part = part.replace(
                    "NorthKoreaJetMig29UB_WpnGun",
                    "Kab500_LeaserGuidedBomb",
                )
            return part

        text = patch_named_object(text, obj, apply)

    if text == orig:
        return blob
    return encode(text, blob)


def button_block(name: str, obj: str, image: str, label: str, tip: str) -> str:
    return (
        f"CommandButton {name}\n"
        f"  Command       = UNIT_BUILD\n"
        f"  Object        = {obj}\n"
        f"  TextLabel     = {label}\n"
        f"  ButtonImage   = {image}\n"
        f"  ButtonBorderType = BUILD\n"
        f"  DescriptLabel = {tip}\n"
        f"End\n"
    )


def patch_commandbutton(blob: bytes, key: str) -> bytes:
    if key.replace("/", "\\").lower() != r"data\ini\commandbutton.ini":
        return blob
    text = decode(blob)
    n = nl(text)
    orig = text
    for name, (obj, image, label, tip) in NEW_BUTTONS.items():
        if re.search(rf"(?m)^CommandButton {re.escape(name)}\b", text):
            continue
        if not text.endswith(n):
            text += n
        text += n + button_block(name, obj, image, label, tip).replace("\n", n)
    if text == orig:
        return blob
    return encode(text, blob)


def set_slots(cs_name: str, slots: dict[int, str], src: str) -> str:
    m = re.search(
        rf"(?ms)^(CommandSet {re.escape(cs_name)}\s*\n)(.*?)(^End\s*$)",
        src,
    )
    if not m:
        print(f"  CommandSet missing {cs_name}")
        return src
    body = m.group(2)
    n = nl(src)
    for slot, btn in slots.items():
        if btn is None:
            body = re.sub(rf"(?im)^\s*{slot}\s*=\s*\S+\s*\n", "", body)
            continue
        if re.search(rf"(?im)^\s*{slot}\s*=\s*\S+", body):
            body = re.sub(
                rf"(?im)^(\s*{slot}\s*=\s*)\S+",
                rf"\1{btn}",
                body,
                count=1,
            )
        else:
            body = body.rstrip() + n + f"  {slot} = {btn}" + n
    return src[: m.start()] + m.group(1) + body + m.group(3) + src[m.end() :]


def patch_commandset(blob: bytes) -> bytes:
    text = decode(blob)
    orig = text
    # Iraq fighter bars: fix Mig25RB name, drop Tu-22 AI, put Su-24MR on 15
    for cs in ("Iraq_AirfieldCommandSet", "Iraq_LargeAirBaseCommandSet"):
        text = set_slots(
            cs,
            {
                12: "Command_ConstructIraqJetMig25RB",
                15: "Command_ConstructIraq_Su-24MR",
            },
            text,
        )
    # Iraq heavy: remove Tu-22, keep Su-24MR, add Tomcat
    text = set_slots(
        "Iraq_HeavyAirBaseCommandSet",
        {
            1: "Command_ConstructIraqJetF14Tomcat",
            2: "Command_ConstructIraq_Su-24MR",
            3: None,
            7: "Command_ConstructIraqJetIL76",
        },
        text,
    )
    # Iraq T3 leftover: drop Tu-22 if the T sets remain on any leftover building
    text = set_slots("Iraq_AirfieldCommandSet_T3", {8: "Command_ConstructIraq_Su-24MR"}, text)
    # NK heavy: Il-28, Il-76, Saetbyol
    text = set_slots(
        "NorthKorea_HeavyAirBaseCommandSet",
        {
            4: "Command_ConstructNorthKoreaBomberIl28",
            5: "Command_ConstructNorthKoreaJetIL76",
            6: "Command_ConstructNorthKoreaUAVSaetbyol",
        },
        text,
    )
    if text == orig:
        return blob
    return encode(text, blob)


def patch_mapped(blob: bytes) -> bytes:
    text = decode(blob)
    if re.search(r"(?m)^MappedImage F14\b", text):
        return blob
    # Attach F14 cameo next to the existing Iran F-14AM image file.
    if not re.search(r"(?m)^MappedImage SPEC_IranJetF14AM\b", text):
        return blob
    n = nl(text)
    if not text.endswith(n):
        text += n
    return encode(text + n + MAPPED_IMAGES.replace("\n", n), blob)


def csf_upsert(blob: bytes, labels: dict[str, str]) -> bytes:
    if blob[:4] != b" FSC":
        return blob
    version, nlab, nstr, extra = struct.unpack_from("<IIII", blob, 4)
    lang = struct.unpack_from("<I", blob, 20)[0]
    pos = 24
    existing = {}
    order = []
    for _ in range(nlab):
        magic = blob[pos : pos + 4]
        if magic != b" LBL":
            print("CSF parse abort", pos)
            return blob
        pos += 4
        nvals, namelen = struct.unpack_from("<II", blob, pos)
        pos += 8
        name = blob[pos : pos + namelen].decode("ascii", "replace")
        pos += namelen
        vals = []
        extras = []
        for _v in range(nvals):
            sm = blob[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", blob, pos)[0]
            pos += 4
            raw = blob[pos : pos + slen * 2]
            pos += slen * 2
            val = bytes(b ^ 0xFF for b in raw).decode("utf-16-le", "replace")
            extra_s = ""
            if sm == b"WRTS":
                elen = struct.unpack_from("<I", blob, pos)[0]
                pos += 4
                extra_s = blob[pos : pos + elen].decode("latin1", "replace")
                pos += elen
            vals.append(val)
            extras.append((sm, extra_s))
        existing[name] = (magic, vals, extras)
        order.append(name)
    for k, v in labels.items():
        if k in existing:
            magic, vals, extras = existing[k]
            if vals:
                vals[0] = v
            else:
                vals = [v]
                extras = [(b" RTS", "")]
            existing[k] = (magic, vals, extras)
        else:
            order.append(k)
            existing[k] = (b" LBL", [v], [(b" RTS", "")])
    out = bytearray()
    out += b" FSC"
    out += struct.pack("<IIIII", version, len(order), len(order), extra, lang)
    for name in order:
        magic, vals, extras = existing[name]
        nb = name.encode("ascii")
        out += magic
        out += struct.pack("<II", len(vals), len(nb))
        out += nb
        for val, (sm, extra_s) in zip(vals, extras):
            enc = val.encode("utf-16-le")
            xored = bytes(b ^ 0xFF for b in enc)
            out += sm
            out += struct.pack("<I", len(enc) // 2)
            out += xored
            if sm == b"WRTS":
                eb = extra_s.encode("latin1")
                out += struct.pack("<I", len(eb))
                out += eb
    return bytes(out)


def import_donor_art(art_map: dict[str, bytes]) -> list[str]:
    imported = []
    lower_index = {n.replace("/", "\\").lower(): n for n in art_map}
    for big_name, names in DONOR_ART.items():
        entries = parse_big(DONOR / big_name)
        idx = {n.replace("/", "\\").lower(): (n, b) for n, b in entries}
        for want in names:
            key = want.replace("/", "\\").lower()
            if key not in idx:
                print(f"  DONOR MISSING {want}")
                continue
            orig, blob = idx[key]
            if key in lower_index:
                art_map[lower_index[key]] = blob
                imported.append(lower_index[key] + " (overwrite)")
            else:
                art_map[orig] = blob
                lower_index[key] = orig
                imported.append(orig)
    return imported


def find_entry(data_map, suffix: str):
    suffix = suffix.replace("/", "\\").lower()
    for n, b in data_map.items():
        if n.replace("/", "\\").lower().endswith(suffix):
            return n, b
    return None, None


def last_object(text: str, name: str):
    hit = None
    for p in re.split(r"(?m)(?=^Object(?:Reskin)?\s+\S+)", text):
        if re.match(rf"(?m)^Object(?:Reskin)?\s+{re.escape(name)}\b", p):
            hit = p
    return hit


def clone_object(src_text: str, old: str, new: str, portrait: str, display: str) -> str:
    text = src_text.replace(f"Object {old}", f"Object {new}", 1)
    text = re.sub(r"(?im)^(\s*SelectPortrait\s*=\s*)\S+", rf"\1{portrait}", text, count=1)
    text = re.sub(r"(?im)^(\s*ButtonImage\s*=\s*)\S+", rf"\1{portrait}", text, count=1)
    text = re.sub(r"(?im)^(\s*DisplayName\s*=\s*)\S+", rf"\1{display}", text, count=1)
    return text


def make_il28(src: str) -> str:
    text = clone_object(src, "RussiaJetTu22M3M", "NorthKoreaBomberIl28", "rus_tu22m3m", "OBJECT:NorthKoreaBomberIl28")
    text = replace_first_weaponset_primary(text, "Specter_Weapon_SU34MF_Bomb6")
    for leftover in (
        "KH101_CruiseMissile_TU22M3M",
        "SVP-24-22_TU22M3M",
        "3x_FAB500_TU22M3M_CRF",
        "3x_FAB500_TU22M3M_CRB",
        "2x_FAB500_TU22M3M_WR",
    ):
        text = re.sub(rf"(?im)^\s*Weapon\s*=\s*\S+\s+{re.escape(leftover)}\s*\n", "", text)
    text = re.sub(r"(?im)^(\s*OkToChangeModelColor\s*=\s*)\S+", r"\1Yes", text)
    return text


def make_il76(src: str) -> str:
    return clone_object(src, "RussiaJetCargoIL76", "NorthKoreaJetIL76", "CargoIL76Russia", "OBJECT:NorthKoreaJetIL76")


def make_saetbyol(src: str) -> str:
    """Kept for history; Saetbyol is now a standalone INI (see build_saetbyol_crash_fix.py).

    Do not clone France E3 with \\11100 replacements — that wrote I00/J00 and
    attached ENGINE01-04 bones to AVReaper, which crashes on produce.
    """
    raise RuntimeError("use build_saetbyol_crash_fix.py")


def make_iraq_tomcat(src: str) -> str:
    text = clone_object(src, "JapanJetF14Tomcat", "IraqJetF14Tomcat", "F14", "OBJECT:IraqJetF14Tomcat")
    text = replace_first_weaponset_primary(text, "Specter_Weapon_JH7A2_Bomb6")
    return text


def main() -> int:
    print("Loading packed BIGs...", flush=True)
    data_entries = parse_big(SRC_DATA)
    art_entries = parse_big(SRC_ART)
    data_map = {n: b for n, b in data_entries}
    art_map = {n: b for n, b in art_entries}
    data_order = [n for n, _ in data_entries]
    art_order = [n for n, _ in art_entries]

    print("Importing donor ART...", flush=True)
    imported = import_donor_art(art_map)
    print(f"  {len(imported)} ART files")
    for n in imported:
        print("   ", n)

    patched = []
    for name, blob in list(data_entries):
        key = name.replace("/", "\\").lower()
        if key in LOCKED_PATHS:
            continue
        new = blob
        if key == r"data\ini\commandbutton.ini":
            new = patch_commandbutton(blob, key)
        elif key.endswith("\\commandset.ini"):
            new = patch_commandset(blob)
        elif "mappedimage" in key and key.endswith(".ini"):
            new = patch_mapped(blob)
        elif key.endswith("generals.csf"):
            new = csf_upsert(blob, CSF_LABELS)
        elif "\\object\\" in key and key.endswith(".ini"):
            new = patch_object_file(name, blob)
        if new != blob:
            data_map[name] = new
            patched.append(name)

    clones = []
    _, f14_blob = find_entry(data_map, r"\japanjetf14tomcat.ini")
    _, tu_blob = find_entry(data_map, r"\tu22m3m.ini")
    _, il_blob = find_entry(data_map, r"\russiajetcargoil76.ini")
    _, e3_blob = find_entry(data_map, r"\franceaircrafte3.ini")

    if f14_blob:
        t = make_iraq_tomcat(last_object(decode(f14_blob), "JapanJetF14Tomcat") or decode(f14_blob))
        new_name = r"Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetF14Tomcat.ini"
        data_map[new_name] = encode(t if t.startswith("Object ") else t, f14_blob)
        clones.append(new_name)
    if tu_blob:
        src = last_object(decode(tu_blob), "RussiaJetTu22M3M") or decode(tu_blob)
        t = make_il28(src)
        new_name = r"Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaBomberIl28.ini"
        data_map[new_name] = encode(t, tu_blob)
        clones.append(new_name)
    if il_blob:
        src = last_object(decode(il_blob), "RussiaJetCargoIL76") or decode(il_blob)
        t = make_il76(src)
        new_name = r"Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetIL76.ini"
        data_map[new_name] = encode(t, il_blob)
        clones.append(new_name)
    # Saetbyol is a standalone recon UAV. Do not clone FranceAircraftE3 —
    # that path wrote I00/J00 and invalid AVReaper ENGINE bones.
    # See patch/tools/big/build_saetbyol_crash_fix.py.
    if e3_blob:
        print("SKIP FranceAircraftE3 -> Saetbyol clone (build_saetbyol_crash_fix.py)")

    print("Patched DATA:", len(patched))
    for n in patched:
        print(" ", n)
    print("New objects:", clones)

    data_out = [(n, data_map[n]) for n in data_order]
    known = set(data_order)
    for n in clones:
        if n not in known:
            data_out.append((n, data_map[n]))
            known.add(n)
    art_out = [(n, art_map[n]) for n in art_order]
    known_a = set(art_order)
    for n, b in art_map.items():
        if n not in known_a:
            art_out.append((n, b))
            known_a.add(n)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(data_out)
    art_big = build_big_ordered(art_out)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_big)
    dsha = hashlib.sha256(data_big).hexdigest()
    asha = hashlib.sha256(art_big).hexdigest()
    print("DATA", dsha, len(data_big))
    print("ART ", asha, len(art_big))
    (OUT_DIR / "SHA256.txt").write_text(f"DATA {dsha}\nART  {asha}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
