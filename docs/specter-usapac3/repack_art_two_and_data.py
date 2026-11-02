#!/usr/bin/env python3
"""Put USAPAC3 art in canonical _SPEC_ART_TWO.big; keep ART ONE unchanged.

Canonical ART ONE is 2,145,283,309 bytes (2,200,339 bytes under GitHub/2GiB).
The 16 USAPAC3 art files are 5,723,261 bytes and do not fit in ART ONE.
ART TWO is the W3D archive (Art\\W3D\\ only) and has room. Textures overflow
here too so ART ONE stays byte-identical.

DATA source is the live unified _SPEC_DATA_ONE.big (374,075,482 bytes).
"""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
SRC_ART2 = Path("/tmp/spec-art-live/_SPEC_ART_TWO.big")
SRC_DATA = Path("/tmp/spec-art-live/_SPEC_DATA_ONE.unified.big")
OUT_DIR = ROOT / "docs/specter-usapac3/merged"
BAK_DIR = ROOT / "docs/specter-usapac3/backup"

ART1_SIZE = 2145283309
ART1_SHA = "15ffb0dcbf6e0a02e8ece6421efac1331c391b48d8afa6b108550df89653df66"
ART2_SHA = "a5a20d959d2835f12a4bf5431e011c4d45047f24ea3d88841c2281fc0a6c19af"
DATA_SHA = "c775c5cc5ae7ca1a4cb717b061c387ad044a737a19989b15496b88f6172da8ac"
GIB = 2147483648

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


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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
        pos = end + 1
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
        fail(f"csf trailing {len(buf) - i}")
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
    print(f"CSF appended {added} -> {nlab + added}")
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


def main() -> int:
    if sha_file(SRC_ART2) != ART2_SHA:
        fail("ART TWO source hash mismatch")
    if sha_file(SRC_DATA) != DATA_SHA:
        fail("unified DATA source hash mismatch")

    art_total = 0
    for rel in ART_FILES:
        p = PATCH / rel
        if not p.exists():
            fail(f"missing {rel}")
        art_total += p.stat().st_size
    room = GIB - ART1_SIZE
    print(f"ART ONE size={ART1_SIZE} 2GiB_room={room} USAPAC3_art={art_total} fits={art_total <= room}")
    if art_total <= room:
        fail("expected USAPAC3 art to overflow ART ONE; check sizes")

    fe = (PATCH / "Data/INI/CommandSet_FactionExpansion_Armies.ini").read_text(encoding="latin-1")
    if "6 = Command_ConstructUSAPAC3" not in fe or "12 = Command_ConstructAmerica_AD_NASAMS" not in fe:
        fail("HQ slots wrong")

    BAK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (BAK_DIR / "_SPEC_ART_ONE.original.sha256").write_text(f"{ART1_SHA}  _SPEC_ART_ONE.big\n", encoding="ascii")
    (BAK_DIR / "_SPEC_ART_TWO.original.sha256").write_text(f"{ART2_SHA}  _SPEC_ART_TWO.big\n", encoding="ascii")
    (BAK_DIR / "_SPEC_DATA_ONE.original.sha256").write_text(f"{DATA_SHA}  _SPEC_DATA_ONE.big\n", encoding="ascii")

    art_raw, art_entries = read_big(SRC_ART2)
    orig_art_names = {norm(n) for n, _, _ in art_entries}
    art_order, art_map = to_map(art_raw, art_entries)
    art_added = []
    for rel in ART_FILES:
        key = norm(rel)
        if key in orig_art_names:
            fail(f"would overwrite existing ART TWO entry {rel}")
        display = rel.replace("/", "\\")
        art_map[key] = (display, (PATCH / rel).read_bytes())
        art_added.append(display)
    final_art = finalize(art_order, art_map)
    if len(final_art) != len(art_entries) + 16:
        fail(f"ART TWO entry count {len(final_art)} != {len(art_entries)+16}")
    out_art = build_big(final_art)
    if any(norm(n) in orig_art_names and False for n in []):
        pass
    # no original ART TWO path removed
    if len(art_entries) != 2684:
        print("WARN original ART TWO count", len(art_entries))

    data_raw, data_entries = read_big(SRC_DATA)
    data_order, data_map = to_map(data_raw, data_entries)
    added, updated = [], []
    for rel in DATA_FILES:
        path = PATCH / rel
        if not path.exists():
            fail(f"missing {rel}")
        key = norm(rel)
        if key in STOCK_SKIP:
            fail(f"refusing stock overwrite {rel}")
        display = rel.replace("/", "\\")
        content = path.read_bytes()
        if key in data_map:
            old_name, old = data_map[key]
            if old != content:
                data_map[key] = (old_name, content)
                updated.append(display)
        else:
            data_map[key] = (display, content)
            added.append(display)
    csf_key = "data\\english\\generals.csf"
    csf_name, csf_blob = data_map[csf_key]
    new_csf = append_csf(csf_blob, CSF_LABELS)
    if new_csf != csf_blob:
        data_map[csf_key] = (csf_name, new_csf)
        updated.append(csf_name)
    final_data = finalize(data_order, data_map)
    out_data = build_big(final_data)

    hq = final_data["Data\\INI\\CommandSet_FactionExpansion_Armies.ini"].decode("latin-1")
    if "6 = Command_ConstructUSAPAC3" not in hq:
        fail("packed HQ slot 6")
    if "Art\\W3D\\UsaPac3Car.W3D" not in final_art or "Art\\Textures\\USAPAC3TB.tga" not in final_art:
        fail("packed art paths")

    ap = OUT_DIR / "_SPEC_ART_TWO.big"
    dp = OUT_DIR / "_SPEC_DATA_ONE.big"
    ap.write_bytes(out_art)
    dp.write_bytes(out_data)
    (OUT_DIR / "_SPEC_ART_TWO.big.sha256").write_text(f"{sha256(out_art)}  _SPEC_ART_TWO.big\n", encoding="ascii")
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(f"{sha256(out_data)}  _SPEC_DATA_ONE.big\n", encoding="ascii")
    (OUT_DIR / "_SPEC_ART_ONE.unchanged.sha256").write_text(f"{ART1_SHA}  _SPEC_ART_ONE.big\n", encoding="ascii")

    lines = [
        f"ART_ONE unchanged bytes={ART1_SIZE} sha256={ART1_SHA}",
        f"ART_ONE 2GiB remaining={GIB-ART1_SIZE} USAPAC3_art={art_total} -> all 16 files in ART_TWO",
        f"ART_TWO original entries={len(art_entries)} bytes={len(art_raw)} sha256={ART2_SHA}",
        f"ART_TWO merged   entries={len(final_art)} bytes={len(out_art)} sha256={sha256(out_art)}",
        "ART_TWO added (none overwritten):",
        *[f"  + {n}" for n in art_added],
        f"DATA original entries={len(data_entries)} bytes={len(data_raw)} sha256={DATA_SHA}",
        f"DATA merged   entries={len(final_data)} bytes={len(out_data)} sha256={sha256(out_data)}",
        "DATA added:",
        *[f"  + {n}" for n in added],
        "DATA updated:",
        *[f"  ~ {n}" for n in updated],
        "STATIC_OK",
        "INGAME_ZH: not executed",
    ]
    text = "\n".join(lines) + "\n"
    (OUT_DIR / "MERGE_REPORT.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
