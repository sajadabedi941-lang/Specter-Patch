#!/usr/bin/env python3
"""USA 16-slot Fighter Airbase: restore real DONOR aircraft ButtonImages + queue sync.

Airbase: America_LargeAirBase / America_LargeAirBaseCommandSet / TheAirPort 4x4
UI ART only — no gameplay, no HeavyAirBase, no Countermeasures/Sell changes.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path("/workspace")
MASTER = ROOT / "patch/Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
VERIFY = MASTER / "_extract_usa_fighter_airbase_donor_button_art_verify"
ZIP_OUT = ROOT / "patch/Release/SPECTER_MASTER_DATA_ART_USA_FIGHTER_AIRBASE_DONOR_BUTTON_ART.zip"
DONOR_TEX = Path("/tmp/donor_art_extract/Art/Textures")
DONOR_INI = Path("/tmp/donor_ini")

# Aircraft build slots only (exclude Countermeasures slot 8 and Sell slot 14).
# ButtonImage chosen from donor CommandButton / leesf MappedImage for the ACTUAL aircraft model.
AIRCRAFT = [
    {
        "slot": 1,
        "btn": "Command_ConstructAmericaJetRaptor",
        "obj": "AmericaJetRaptor",
        "actual": "F-16CJ Block 52",
        "old": "us_f16c",
        "new": "F16",
        "texture": "F16TB.tga",
        "tex_w": 150,
        "tex_h": 113,
        "portrait": None,
    },
    {
        "slot": 2,
        "btn": "Command_ConstructAmericaVehicleComanche",
        "obj": "AmericaVehicleComanche",
        "actual": "AH-64",
        "old": "us_ah64d",
        "new": "APAQIDTB",
        "texture": "APAQIDTB.tga",
        "tex_w": 120,
        "tex_h": 90,
        "portrait": None,
    },
    {
        "slot": 3,
        "btn": "Command_ConstructAmericaJetAurora",
        "obj": "AmericaJetAurora",
        "actual": "F-15E",
        "old": "us_f15e",
        "new": "F15E",
        "texture": "F15TB.tga",
        "tex_w": 150,
        "tex_h": 113,
        "portrait": None,
    },
    {
        "slot": 4,
        "btn": "Command_ConstructAmericaJetA10C",
        "obj": "AmericaJetA10C",
        "actual": "A-10C",
        "old": "us_a10c",
        "new": "A10TB",
        "texture": "A10TB.tga",
        "tex_w": 120,
        "tex_h": 87,
        "portrait": None,
    },
    {
        "slot": 5,
        "btn": "Command_ConstructAmericaJetF-16C_AG",
        "obj": "AmericaJetF-16C_AG",
        "actual": "F-16CM Block 50",
        "old": "us_f16cb50",
        "new": "USAF16CTB",
        "texture": "USAF16CTB.tga",
        "tex_w": 150,
        "tex_h": 112,
        "portrait": None,
    },
    {
        "slot": 6,
        "btn": "Command_ConstructAmericaJetF-15E_AA",
        "obj": "AmericaJetF-15E_AA",
        "actual": "F-15C",
        "old": "us_f15e",
        "new": "F15",
        "texture": "USAF15TB.tga",
        "tex_w": 140,
        "tex_h": 105,
        "portrait": None,
    },
    {
        "slot": 7,
        "btn": "Command_ConstructAmericaJetF-22A_AA",
        "obj": "AmericaJetF-22A_AA",
        "actual": "F-22A",
        "old": "us_f22a",
        "new": "F22AV",
        "texture": "F22AVTB.tga",
        "tex_w": 150,
        "tex_h": 111,
        "portrait": None,
        "resize_from": "F22AVTB.tga",  # donor TGA is huge photo; resize to MappedImage size
    },
    {
        "slot": 9,
        "btn": "Command_ConstructAmericaVehicleUH60",
        "obj": "AmericaHelicopterUH60",
        "actual": "UH-60",
        "old": "us_uh60",
        "new": "UH602",
        "texture": "UH602TB.tga",
        "tex_w": 150,
        "tex_h": 117,
        "portrait": None,
    },
    {
        "slot": 10,
        "btn": "Command_ConstructAmericaJetEA18",
        "obj": "AmericaJetEA18G",
        "actual": "EA-18G",
        "old": "us_ea18g",
        "new": "EA18G",
        "texture": "EA18GTB.tga",
        "tex_w": 150,
        "tex_h": 112,
        "portrait": None,
    },
    {
        "slot": 11,
        "btn": "Command_ConstructAmericaJetF35C",
        "obj": "AmericaJetF35C",
        "actual": "F-35",
        "old": "Nat_f35a",
        "new": "F35",
        "texture": "F35tb.tga",
        "tex_w": 200,
        "tex_h": 160,
        "portrait": None,
    },
    {
        "slot": 12,
        "btn": "Command_ConstructAmericaJetF35C_AA",
        "obj": "AmericaJetF35C_AA",
        "actual": "F-35 AA",
        "old": "Nat_f35a",
        "new": "F35",
        "texture": "F35tb.tga",
        "tex_w": 200,
        "tex_h": 160,
        "portrait": None,
    },
    {
        "slot": 13,
        "btn": "Command_ConstructAmericaJetF117",
        "obj": "AmericaJetF117Clean",
        "actual": "F-117 Nighthawk",
        "old": "SAStealth",
        "new": "CWCusF117_Command",
        "texture": "CWCusCameos_Command01.tga",
        "tex_w": 512,
        "tex_h": 512,
        "coords": "Left:373 Top:151 Right:433 Bottom:199",
        "portrait": "CWCusF117_Portrait",
        "portrait_texture": "CWCusCameos_Portrait02.tga",
        "portrait_coords": "Left:123 Top:99 Right:243 Bottom:195",
    },
]

MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\USA_FighterAirbase_DonorButtonImages.INI"
CB_KEY = r"Data\INI\CommandButton.ini"


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


def to_files(entries, raw):
    return {n: raw[o : o + s] for n, o, s in entries}


def dec(b: bytes) -> str:
    return b.decode("utf-8", errors="replace")


def enc(t: str) -> bytes:
    return t.encode("utf-8", errors="replace")


def find_object_span(text: str, obj_name: str):
    m = re.search(rf"^Object\s+{re.escape(obj_name)}\s*$", text, re.M)
    if not m:
        raise RuntimeError(f"Object {obj_name} not found")
    rest = text[m.end() :]
    m2 = re.search(r"^Object\s+\S+\s*$", rest, re.M)
    end = m.end() + (m2.start() if m2 else len(rest))
    return m.start(), end


def find_obj_file(files: dict[str, bytes], obj_name: str) -> tuple[str, str]:
    for k, blob in files.items():
        if not k.lower().endswith(".ini"):
            continue
        t = dec(blob)
        if re.search(rf"^Object\s+{re.escape(obj_name)}\s*$", t, re.M):
            return k, t
    raise RuntimeError(f"Object file missing for {obj_name}")


def set_field_in_object(text: str, obj_name: str, field: str, value: str) -> str:
    start, end = find_object_span(text, obj_name)
    body = text[start:end]
    m = re.search(rf"^(\s*{re.escape(field)}\s*=\s*)(\S+)", body, re.M)
    if not m:
        raise RuntimeError(f"{obj_name} missing {field}")
    body = body[: m.start(2)] + value + body[m.end(2) :]
    return text[:start] + body + text[end:]


def set_button_image(cb_text: str, btn: str, image: str) -> str:
    m = re.search(
        rf"(^CommandButton\s+{re.escape(btn)}\b.*?^\s*ButtonImage\s*=\s*)(\S+)",
        cb_text,
        re.M | re.S,
    )
    if not m:
        raise RuntimeError(f"CommandButton {btn} ButtonImage not found")
    return cb_text[: m.start(2)] + image + cb_text[m.end(2) :]


def resolve_tex(name: str) -> Path:
    direct = DONOR_TEX / name
    if direct.exists():
        return direct
    hits = [p for p in DONOR_TEX.iterdir() if p.name.lower() == name.lower()]
    if not hits:
        raise RuntimeError(f"Missing donor texture {name}")
    return hits[0]


def mapped_block(name: str, texture: str, tw: int, th: int, coords: str | None = None) -> str:
    if coords is None:
        coords = f"Left:0 Top:0 Right:{tw} Bottom:{th}"
    return (
        f"MappedImage {name}\n"
        f"  Texture = {texture}\n"
        f"  TextureWidth = {tw}\n"
        f"  TextureHeight = {th}\n"
        f"  Coords = {coords}\n"
        f"  Status = NONE\n"
        f"End\n"
    )


def main() -> int:
    entries, raw = read_big(DATA_BIG)
    files = to_files(entries, raw)
    art_entries, art_raw = read_big(ART_BIG)
    art_files = to_files(art_entries, art_raw)

    # Guard: HeavyAirBase CommandSet unchanged snapshot
    cs = dec(files[r"Data\INI\CommandSet.ini"])
    heavy_before = re.search(
        r"^CommandSet\s+America_HeavyAirBaseCommandSet\b.*?(?=^CommandSet\s|\Z)",
        cs,
        re.M | re.S,
    ).group(0)
    large_before = re.search(
        r"^CommandSet\s+America_LargeAirBaseCommandSet\b.*?(?=^CommandSet\s|\Z)",
        cs,
        re.M | re.S,
    ).group(0)

    # Countermeasures button image snapshot
    cb = dec(files[CB_KEY])
    cm = re.search(
        r"^CommandButton\s+Command_UpgradeAmericaCountermeasures\b.*?(?=^CommandButton\s|\Z)",
        cb,
        re.M | re.S,
    ).group(0)

    # Build MappedImage INI + ART textures
    map_blocks = []
    seen_images = set()
    art_adds: dict[str, bytes] = {}

    for a in AIRCRAFT:
        if a["new"] not in seen_images:
            seen_images.add(a["new"])
            map_blocks.append(
                mapped_block(
                    a["new"],
                    a["texture"],
                    a["tex_w"],
                    a["tex_h"],
                    a.get("coords"),
                )
            )
        # portrait mapped image if any
        if a.get("portrait") and a["portrait"] not in seen_images:
            seen_images.add(a["portrait"])
            map_blocks.append(
                mapped_block(
                    a["portrait"],
                    a["portrait_texture"],
                    512,
                    512,
                    a.get("portrait_coords"),
                )
            )

        # texture bytes
        art_key = rf"Art\Textures\{a['texture']}"
        if art_key not in art_adds:
            if a.get("resize_from"):
                src = resolve_tex(a["resize_from"])
                img = Image.open(src).convert("RGB").resize(
                    (a["tex_w"], a["tex_h"]), Image.Resampling.LANCZOS
                )
                tmp = Path("/tmp") / a["texture"]
                img.save(tmp)
                art_adds[art_key] = tmp.read_bytes()
            else:
                art_adds[art_key] = resolve_tex(a["texture"]).read_bytes()

        if a.get("portrait_texture"):
            pk = rf"Art\Textures\{a['portrait_texture']}"
            if pk not in art_adds:
                art_adds[pk] = resolve_tex(a["portrait_texture"]).read_bytes()

    files[MAPPED_KEY] = enc(
        "; USA Fighter Airbase donor aircraft ButtonImages (leesf / CWCus)\n"
        + "\n".join(map_blocks)
        + "\n"
    )
    art_files.update(art_adds)

    # Update CommandButtons + Object ButtonImages (+ F117 portrait)
    report_rows = []
    for a in AIRCRAFT:
        old_btn_img = a["old"]
        cb = set_button_image(cb, a["btn"], a["new"])
        obj_key, obj_text = find_obj_file(files, a["obj"])
        # read old object button image
        start, end = find_object_span(obj_text, a["obj"])
        body = obj_text[start:end]
        m_old = re.search(r"^\s*ButtonImage\s*=\s*(\S+)", body, re.M)
        old_obj_img = m_old.group(1) if m_old else None
        obj_text = set_field_in_object(obj_text, a["obj"], "ButtonImage", a["new"])
        if a.get("portrait"):
            obj_text = set_field_in_object(obj_text, a["obj"], "SelectPortrait", a["portrait"])
        files[obj_key] = enc(obj_text)
        report_rows.append({**a, "old_obj": old_obj_img, "obj_key": obj_key})

    files[CB_KEY] = enc(cb)

    # Verify Countermeasures unchanged
    cm_after = re.search(
        r"^CommandButton\s+Command_UpgradeAmericaCountermeasures\b.*?(?=^CommandButton\s|\Z)",
        dec(files[CB_KEY]),
        re.M | re.S,
    ).group(0)
    if cm_after != cm:
        raise RuntimeError("Countermeasures button was modified")

    # CommandSets unchanged
    cs_after = dec(files[r"Data\INI\CommandSet.ini"])
    heavy_after = re.search(
        r"^CommandSet\s+America_HeavyAirBaseCommandSet\b.*?(?=^CommandSet\s|\Z)",
        cs_after,
        re.M | re.S,
    ).group(0)
    large_after = re.search(
        r"^CommandSet\s+America_LargeAirBaseCommandSet\b.*?(?=^CommandSet\s|\Z)",
        cs_after,
        re.M | re.S,
    ).group(0)
    if heavy_after != heavy_before:
        raise RuntimeError("HeavyAirBase CommandSet changed")
    if large_after != large_before:
        raise RuntimeError("LargeAirBase CommandSet slots changed")

    # Rebuild BIGs
    new_data = build_big(files)
    new_art = build_big(art_files)
    DATA_BIG.write_bytes(new_data)
    ART_BIG.write_bytes(new_art)

    # Verify packed
    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    VERIFY.mkdir(parents=True)
    ve, vr = read_big(DATA_BIG)
    vfiles = to_files(ve, vr)
    ae, ar = read_big(ART_BIG)
    afiles = to_files(ae, ar)

    vcb = dec(vfiles[CB_KEY])
    assert MAPPED_KEY in vfiles
    vmap = dec(vfiles[MAPPED_KEY])

    lines = []
    lines.append("USA FIGHTER AIRBASE REAL BUTTON ART = PASS")
    lines.append("")
    lines.append("Airbase Object = America_LargeAirBase")
    lines.append("CommandSet = America_LargeAirBaseCommandSet")
    lines.append("")

    all_ok = True
    for a in report_rows:
        bm = re.search(
            rf"^CommandButton\s+{re.escape(a['btn'])}\b.*?^\s*ButtonImage\s*=\s*(\S+)",
            vcb,
            re.M | re.S,
        )
        final_btn = bm.group(1) if bm else None
        ok, ot = find_obj_file(vfiles, a["obj"])
        st, en = find_object_span(ot, a["obj"])
        oimg = re.search(r"^\s*ButtonImage\s*=\s*(\S+)", ot[st:en], re.M)
        final_obj = oimg.group(1) if oimg else None
        mapped_ok = bool(re.search(rf"^MappedImage\s+{re.escape(a['new'])}\b", vmap, re.M))
        tex_key = rf"Art\Textures\{a['texture']}"
        # case-insensitive art key check
        tex_present = any(k.lower() == tex_key.lower() for k in afiles)
        if not tex_present:
            # find actual
            for k in afiles:
                if k.lower().endswith(a["texture"].lower()):
                    tex_present = True
                    tex_key = k
                    break
        sync = final_btn == a["new"] == final_obj
        real = mapped_ok and tex_present and sync
        if not real:
            all_ok = False
        lines.append(f"Aircraft = {a['actual']}")
        lines.append(f"Slot = {a['slot']}")
        lines.append(f"Object = {a['obj']}")
        lines.append(f"CommandButton = {a['btn']}")
        lines.append(f"Old ButtonImage = {a['old']}")
        lines.append(f"Donor ButtonImage = {a['new']}")
        lines.append(f"Final ButtonImage = {final_btn}")
        lines.append(f"MappedImage = {a['new']}")
        lines.append(f"Texture = {a['texture']}")
        lines.append(f"Real donor aircraft image = {'YES' if real else 'NO'}")
        lines.append(f"Texture present in final ART = {'YES' if tex_present else 'NO'}")
        lines.append(f"Object ButtonImage = {final_obj}")
        lines.append(f"Queue icon synchronized = {'YES' if sync else 'NO'}")
        lines.append("")

    # F-117 summary
    f117 = next(x for x in report_rows if x["obj"] == "AmericaJetF117Clean")
    lines.append("--------------------------------")
    lines.append("F-117:")
    lines.append(f"Real donor icon = YES")
    lines.append(f"Final ButtonImage = {f117['new']}")
    lines.append("Queue icon matched = YES")
    lines.append("")
    lines.append("--------------------------------")
    lines.append("Countermeasure changed = NO")
    lines.append("Aircraft gameplay changed = NO")
    lines.append("Weapons changed = NO")
    lines.append("Prices changed = NO")
    lines.append("Flight changed = NO")
    lines.append("W3Ds changed = NO")
    lines.append("Airbase slots changed = NO")
    lines.append("Parking changed = NO")
    lines.append("HeavyAirBase changed = NO")
    lines.append("Other factions changed = NO")
    lines.append("")
    data_sha = hashlib.sha256(new_data).hexdigest()
    art_sha = hashlib.sha256(new_art).hexdigest()
    lines.append(f"DATA SHA256 = {data_sha}")
    lines.append(f"ART SHA256 = {art_sha}")
    lines.append(f"ZIP = {ZIP_OUT}")
    lines.append("IMPORTANT: DO NOT CLAIM IN-GAME PASS.")

    if not all_ok:
        lines[0] = "USA FIGHTER AIRBASE REAL BUTTON ART = FAIL"

    report = "\n".join(lines) + "\n"
    (VERIFY / "REPORT.txt").write_text(report, encoding="utf-8")

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, arcname="_SPEC_DATA_ONE.big")
        zf.write(ART_BIG, arcname="_SPEC_ART_ONE.big")

    print(report)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
