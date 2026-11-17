#!/usr/bin/env python3
"""Merge only USAPAC3 ART/DATA into stock SPECTER _SPEC_* BIGs.

Does not rewrite Weapon.ini / CommandButton.ini / CommandSet.ini / Armor.ini /
Locomotor.ini. Does not edit America_AD_THAAD, America_AD_Patriot, or
America_AD_NASAMS objects. Other-country CommandSets in
CommandSet_FactionExpansion_Armies.ini stay as they are; only America's
slot 6/12 were already set in the overlay source.
"""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
SRC_DATA = Path("/tmp/spec-audit/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/spec-audit/_SPEC_ART_ONE.big")
OUT_DIR = ROOT / "docs/specter-usapac3/merged"
BAK_DIR = ROOT / "docs/specter-usapac3/backup"

STOCK_SKIP = {
    "data\\ini\\weapon.ini",
    "data\\ini\\commandbutton.ini",
    "data\\ini\\commandset.ini",
    "data\\ini\\armor.ini",
    "data\\ini\\locomotor.ini",
}

ART_FILES = [
    "Art/W3D/UsaPac3Car.W3D",
    "Art/W3D/UsaPac3Car_d.W3D",
    "Art/W3D/UsaPac3Car_w.W3D",
    "Art/W3D/UsaPac3F.W3D",
    "Art/W3D/UsaPac3F_d.W3D",
    "Art/W3D/pac3mis_m.W3D",
    "Art/Textures/usaPAC3TRUCKmap.dds",
    "Art/Textures/usaPAC3TRUCKmap_d.dds",
    "Art/Textures/ampac3map.dds",
    "Art/Textures/ampac3map_d.dds",
    "Art/Textures/ampac3mapBaCK.dds",
    "Art/Textures/pac3missilemap.dds",
    "Art/Textures/ABNPatriot02.dds",
    "Art/Textures/ABNPatriot02_d.tga",
    "Art/Textures/USAPAC3.tga",
    "Art/Textures/USAPAC3TB.tga",
]

DATA_FILES = [
    "Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3.ini",
    "Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3_Projectile.ini",
    "Data/INI/Weapon_USAPAC3.ini",
    "Data/INI/CommandButton_USAPAC3.ini",
    "Data/INI/CommandSet_FactionExpansion_Armies.ini",
    "Data/INI/CommandSet_ZZZZ_USAPAC3.ini",
    "Data/INI/MappedImages/HandCreated/USAPAC3_Images.INI",
    "Data/English/FactionExpansion_USAPAC3_Strings.txt",
]

CSF_LABELS = {
    "OBJECT:USAPAC3": "PAC-3 Patriot",
    "OBJECT:USAPAC3_Projectile": "PAC-3 Missile",
    "CONTROLBAR:ConstructUSAPAC3": "PAC-3 Patriot",
    "CONTROLBAR:ToolTipConstructUSAPAC3": (
        "Mobile Patriot PAC-3 battery. THAAD-class intercept vs aircraft and ballistic missiles.\n"
        "\nStrong vs. aircraft, ballistic missiles\nWeak vs. tanks, infantry"
    ),
}


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        fail(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos += len(name) + 1
        entries.append((name.replace("/", "\\"), off, size))
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
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin-1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def parse_csf_names(buf: bytes) -> set[str]:
    i = 24
    names = set()
    nlab = struct.unpack_from("<I", buf, 8)[0]
    for _ in range(nlab):
        if buf[i : i + 4] != b" LBL":
            fail("csf parse error")
        i += 4
        scount = struct.unpack_from("<I", buf, i)[0]
        i += 4
        nlen = struct.unpack_from("<I", buf, i)[0]
        i += 4
        name = buf[i : i + nlen].decode("latin-1")
        i += nlen
        names.add(name)
        for _s in range(scount):
            st = buf[i : i + 4]
            i += 4
            vlen = struct.unpack_from("<I", buf, i)[0]
            i += 4
            i += vlen * 2
            if st in (b"WRTS", b"RTSW"):
                elen = struct.unpack_from("<I", buf, i)[0]
                i += 4
                i += elen
    if i != len(buf):
        fail(f"csf trailing bytes {len(buf) - i}")
    return names


def append_csf(buf: bytes, new: dict[str, str]) -> bytes:
    existing = parse_csf_names(buf)
    data = bytearray(buf)
    nlab, nstr = struct.unpack_from("<II", buf, 8)
    added = 0
    for key, val in new.items():
        if key in existing:
            continue
        enc = val.encode("utf-16-le")
        nchars = len(enc) // 2
        xored = bytearray(enc)
        for i in range(0, len(xored), 2):
            c = xored[i] | (xored[i + 1] << 8)
            c ^= 0xFFFF
            xored[i] = c & 0xFF
            xored[i + 1] = (c >> 8) & 0xFF
        name_b = key.encode("latin-1")
        rec = bytearray()
        rec += b" LBL"
        rec += struct.pack("<I", 1)
        rec += struct.pack("<I", len(name_b))
        rec += name_b
        rec += b" RTS"
        rec += struct.pack("<I", nchars)
        rec += bytes(xored)
        data += rec
        added += 1
    struct.pack_into("<I", data, 8, nlab + added)
    struct.pack_into("<I", data, 12, nstr + added)
    parse_csf_names(bytes(data))
    print(f"CSF appended {added} labels -> {nlab + added}")
    return bytes(data)


def to_map(raw: bytes, entries):
    order = []
    amap = {}
    for name, off, size in entries:
        key = norm(name)
        if key not in amap:
            order.append(key)
        amap[key] = (name, raw[off : off + size])
    return order, amap


def finalize(order, amap):
    final = {}
    seen = set()
    for key in order:
        name, content = amap[key]
        final[name] = content
        seen.add(key)
    for key, (name, content) in sorted(amap.items(), key=lambda kv: kv[0]):
        if key not in seen:
            final[name] = content
    return final


def put_data(amap, rel: str, content: bytes, added, updated, skipped):
    key = norm(rel)
    if key in STOCK_SKIP:
        skipped.append(rel)
        return
    display = rel.replace("/", "\\")
    if key in amap:
        old_name, old = amap[key]
        if old == content:
            return
        amap[key] = (old_name, content)
        updated.append(display)
    else:
        amap[key] = (display, content)
        added.append(display)


def main() -> int:
    if not SRC_DATA.exists() or not SRC_ART.exists():
        fail("source SPEC BIGs missing under /tmp/spec-audit")

    fe = (PATCH / "Data/INI/CommandSet_FactionExpansion_Armies.ini").read_text(encoding="latin-1")
    if "6 = Command_ConstructUSAPAC3" not in fe:
        fail("FactionExpansion slot 6 is not USAPAC3")
    if "12 = Command_ConstructAmerica_AD_NASAMS" not in fe:
        fail("NASAMS not on slot 12")
    if "5 = Command_ConstructAmerica_AD_THAAD" not in fe or "4 = Command_ConstructAmerica_AD_Patriot" not in fe:
        fail("Patriot/THAAD HQ slots changed")
    for banned in (
        "Object America_AD_THAAD",
        "Object America_AD_Patriot",
        "Object America_AD_NASAMS",
    ):
        if banned in (PATCH / "Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3.ini").read_text(encoding="latin-1"):
            fail(banned)

    BAK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    src_data = SRC_DATA.read_bytes()
    src_art = SRC_ART.read_bytes()
    (BAK_DIR / "_SPEC_DATA_ONE.original.sha256").write_text(
        f"{sha256(src_data)}  _SPEC_DATA_ONE.big\n", encoding="ascii"
    )
    (BAK_DIR / "_SPEC_ART_ONE.original.sha256").write_text(
        f"{sha256(src_art)}  _SPEC_ART_ONE.big\n", encoding="ascii"
    )
    print("backup hashes written (original BIGs kept at", SRC_DATA, SRC_ART, ")")

    data_raw, data_entries = read_big(SRC_DATA)
    art_raw, art_entries = read_big(SRC_ART)
    data_order, data_map = to_map(data_raw, data_entries)
    art_order, art_map = to_map(art_raw, art_entries)

    added, updated, skipped = [], [], []
    for rel in DATA_FILES:
        path = PATCH / rel
        if not path.exists():
            fail(f"missing {rel}")
        put_data(data_map, rel, path.read_bytes(), added, updated, skipped)

    csf_key = "data\\english\\generals.csf"
    if csf_key not in data_map:
        fail("packed CSF missing")
    csf_name, csf_blob = data_map[csf_key]
    new_csf = append_csf(csf_blob, CSF_LABELS)
    if new_csf != csf_blob:
        data_map[csf_key] = (csf_name, new_csf)
        updated.append(csf_name)

    art_added, art_updated = [], []
    for rel in ART_FILES:
        path = PATCH / rel
        if not path.exists():
            fail(f"missing art {rel}")
        key = norm(rel)
        content = path.read_bytes()
        display = rel.replace("/", "\\")
        if key in art_map:
            old_name, old = art_map[key]
            if old != content:
                art_map[key] = (old_name, content)
                art_updated.append(display)
        else:
            art_map[key] = (display, content)
            art_added.append(display)

    final_data = finalize(data_order, data_map)
    final_art = finalize(art_order, art_map)
    out_data = build_big(final_data)
    out_art = build_big(final_art)

    # verify packed HQ set
    hq = final_data["Data\\INI\\CommandSet_FactionExpansion_Armies.ini"].decode("latin-1")
    if "6 = Command_ConstructUSAPAC3" not in hq or "12 = Command_ConstructAmerica_AD_NASAMS" not in hq:
        fail("packed HQ CommandSet slots wrong")
    if b"Object USAPAC3" not in final_data["Data\\INI\\Object\\Specter\\PatchSystems\\AirDefense\\USAPAC3.ini"]:
        fail("packed object missing")
    if "Art\\W3D\\UsaPac3Car.W3D" not in final_art:
        fail("packed W3D missing")

    dp = OUT_DIR / "_SPEC_DATA_ONE.big"
    ap = OUT_DIR / "_SPEC_ART_ONE.big"
    dp.write_bytes(out_data)
    ap.write_bytes(out_art)
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(f"{sha256(out_data)}  _SPEC_DATA_ONE.big\n", encoding="ascii")
    (OUT_DIR / "_SPEC_ART_ONE.big.sha256").write_text(f"{sha256(out_art)}  _SPEC_ART_ONE.big\n", encoding="ascii")

    report = []
    report.append(f"DATA original entries={len(data_entries)} bytes={len(src_data)} sha256={sha256(src_data)}")
    report.append(f"DATA merged   entries={len(final_data)} bytes={len(out_data)} sha256={sha256(out_data)}")
    report.append("DATA added:")
    report.extend(f"  + {n}" for n in added)
    report.append("DATA updated:")
    report.extend(f"  ~ {n}" for n in updated)
    if skipped:
        report.append("DATA skipped stock:")
        report.extend(f"  ! {n}" for n in skipped)
    report.append(f"ART original entries={len(art_entries)} bytes={len(src_art)} sha256={sha256(src_art)}")
    report.append(f"ART merged   entries={len(final_art)} bytes={len(out_art)} sha256={sha256(out_art)}")
    report.append("ART added:")
    report.extend(f"  + {n}" for n in art_added)
    report.append("ART updated:")
    report.extend(f"  ~ {n}" for n in art_updated)
    report.append("STATIC_OK")
    report.append("INGAME_ZH: not executed")
    text = "\n".join(report) + "\n"
    (OUT_DIR / "MERGE_REPORT.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
