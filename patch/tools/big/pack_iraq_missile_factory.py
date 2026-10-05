#!/usr/bin/env python3
"""Pack SPECTER Iraq Missile Factory ART+DATA replacement BIGs.

Base: SPECTER FINAL _SPEC_DATA_ONE.big + _SPEC_ART_ONE.big
Merge: patch/ overlay (stock cores skipped)
Surgical: Iraq_VT72BCommandSet slot 14 only, plus CSF labels.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
import zipfile
from pathlib import Path

STOCK_SKIP = {
    "data\\ini\\weapon.ini",
    "data\\ini\\commandbutton.ini",
    "data\\ini\\commandset.ini",
    "data\\ini\\armor.ini",
    "data\\ini\\locomotor.ini",
}

FORBIDDEN_ART_OVERWRITE = {
    "art\\w3d\\irq_warfactory.w3d",
    "art\\textures\\abarfrccmd.dds",
    "art\\textures\\abarfrccmd_d.dds",
}

REQUIRED_ART = [
    "Art\\W3D\\LSFIQMCheChang.W3D",
    "Art\\W3D\\LSFIQMCheChangd.W3D",
    "Art\\W3D\\LSFIQMCheChange.W3D",
    "Art\\W3D\\LSFMCheChangCB.W3D",
    "Art\\Textures\\LSFDaoDanTBO.tga",
    "Art\\Textures\\LSFDF11M.tga",
    "Art\\Textures\\LSFDF11Md.tga",
    "Art\\Textures\\LSFDustPaoDao.tga",
    "Art\\Textures\\LSFDustPaoDaod.tga",
    "Art\\Textures\\LSFDustPaoDaoe.tga",
    "Art\\Textures\\LSFChinaBase.tga",
    "Art\\Textures\\LSFChinaBased.tga",
    "Art\\Textures\\LSFChinaBasee.tga",
    "Art\\Textures\\Camo net.tga",
    "Art\\Textures\\Camo netd.tga",
    "Art\\Textures\\Camo netk.tga",
    "Art\\Textures\\YILAKE.tga",
    "Art\\Textures\\YILAKEd.tga",
]

CSF_LABELS = [
    ("OBJECT:Iraq_MissileFactory", "Iraq Missile Factory"),
    ("CONTROLBAR:ConstructIraq_MissileFactory", "Missile Factory"),
    ("CONTROLBAR:ToolTipIraqBuildMissileFactory", "Builds the Iraqi Missile Factory. Produces missile vehicles."),
]


def norm_key(name: str) -> str:
    return name.replace("/", "\\").lower()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not a BIGF archive: {path}")
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


def to_map(entries, raw):
    amap: dict[str, tuple[str, bytes]] = {}
    order: list[str] = []
    for name, off, size in entries:
        key = norm_key(name)
        if key not in amap:
            order.append(key)
        amap[key] = (name.replace("/", "\\"), raw[off : off + size])
    return amap, order


def finalize(order_keys, amap):
    final = {}
    seen = set()
    for key in order_keys:
        name, content = amap[key]
        final[name] = content
        seen.add(key)
    for key, (name, content) in sorted(amap.items(), key=lambda kv: kv[0]):
        if key not in seen:
            final[name] = content
    return final


def patch_iraq_vt72b_slot14(content: bytes) -> bytes:
    text = content.decode("latin1", errors="replace")
    start = text.find("CommandSet Iraq_VT72BCommandSet")
    if start < 0:
        raise RuntimeError("Iraq_VT72BCommandSet not found in packed CommandSet.ini")
    end = text.find("\nEnd", start)
    if end < 0:
        raise RuntimeError("Iraq_VT72BCommandSet End not found")
    end += len("\nEnd")
    block = text[start:end]
    if "14 = Command_DisarmMinesAtPosition" not in block and "14  = Command_DisarmMinesAtPosition" not in block:
        if "Command_ConstructIraq_MissileFactory" in block:
            return content
        raise RuntimeError("Iraq_VT72BCommandSet slot 14 is not Clear Mines")
    new_block = block.replace(
        "14 = Command_DisarmMinesAtPosition",
        "14 = Command_ConstructIraq_MissileFactory",
    ).replace(
        "14  = Command_DisarmMinesAtPosition",
        "14  = Command_ConstructIraq_MissileFactory",
    )
    if new_block == block:
        raise RuntimeError("Failed to substitute Iraq_VT72BCommandSet slot 14")
    # safety: other slots must remain
    for token in (
        "Command_ConstructIraq_WarFactory_T",
        "Command_ConstructIraq_HeavyAirBase",
        "Command_ConstructIraq_PowerPlant",
        "Command_Stop",
    ):
        if token not in new_block:
            raise RuntimeError(f"Slot-14 patch would drop {token}")
    if "Command_DisarmMinesAtPosition" in new_block:
        raise RuntimeError("Clear Mines still present on Iraq_VT72BCommandSet")
    patched = text[:start] + new_block + text[end:]
    return patched.encode("latin1", errors="replace")


def xor_csf_bytes(s: str) -> bytes:
    raw = s.encode("utf-16-le")
    return bytes(b ^ 0xFF for b in raw)


def patch_csf(content: bytes, labels: list[tuple[str, str]]) -> bytes:
    if content[:4] not in (b" CSF", b"CSF ", b" FSC", b"FSC "):
        raise RuntimeError(f"Unrecognized CSF magic {content[:4]!r}")
    magic = content[:4]
    version, nlab, nstr, unk, lang = struct.unpack_from("<IIIII", content, 4)
    pos = 24
    existing = set()
    # walk labels
    for _ in range(nlab):
        tag = content[pos : pos + 4]
        if tag != b" LBL":
            raise RuntimeError(f"Bad CSF label tag {tag!r} at {pos}")
        str_count, name_len = struct.unpack_from("<II", content, pos + 4)
        pos += 12
        name = content[pos : pos + name_len].decode("ascii", errors="replace")
        pos += name_len
        existing.add(name)
        for _s in range(str_count):
            stag = content[pos : pos + 4]
            slen = struct.unpack_from("<I", content, pos + 4)[0]
            pos += 8 + slen * 2
            if stag == b"WRTS":  # extra value
                vlen = struct.unpack_from("<I", content, pos)[0]
                pos += 4 + vlen
    extra = bytearray()
    added = 0
    for name, value in labels:
        if name in existing:
            continue
        extra += b" LBL"
        extra += struct.pack("<II", 1, len(name))
        extra += name.encode("ascii")
        extra += b" RTS"
        encoded = xor_csf_bytes(value)
        extra += struct.pack("<I", len(encoded) // 2)
        extra += encoded
        added += 1
    if added == 0:
        return content
    header = magic + struct.pack("<IIIII", version, nlab + added, nstr + added, unk, lang)
    return header + content[24:] + bytes(extra)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-big", type=Path, required=True)
    ap.add_argument("--art-big", type=Path, required=True)
    ap.add_argument("--patch-root", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    data_entries, data_raw = read_big(args.data_big)
    art_entries, art_raw = read_big(args.art_big)
    data_map, data_keys = to_map(data_entries, data_raw)
    art_map, art_keys = to_map(art_entries, art_raw)

    added = updated = skipped_stock = 0
    art_added = art_updated = 0
    forbidden_hits = []

    def merge_data(big_path: str, content: bytes) -> None:
        nonlocal added, updated, skipped_stock
        key = norm_key(big_path)
        if key in STOCK_SKIP:
            skipped_stock += 1
            return
        display = big_path.replace("/", "\\")
        if key in data_map:
            old_name, old = data_map[key]
            if old == content or old.rstrip(b"\x00") == content.rstrip(b"\x00"):
                return
            data_map[key] = (old_name, content)
            updated += 1
        else:
            data_map[key] = (display, content)
            added += 1

    patch_data = args.patch_root / "Data"
    for path in sorted(patch_data.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(patch_data).as_posix()
        merge_data("Data\\" + rel.replace("/", "\\"), path.read_bytes())

    patch_art = args.patch_root / "Art"
    if patch_art.exists():
        for path in sorted(patch_art.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(args.patch_root).as_posix()
            big_path = rel.replace("/", "\\")
            key = norm_key(big_path)
            if key in FORBIDDEN_ART_OVERWRITE:
                forbidden_hits.append(big_path)
                continue
            content = path.read_bytes()
            if key in art_map:
                old_name, old = art_map[key]
                if old != content and old.rstrip(b"\x00") != content.rstrip(b"\x00"):
                    art_map[key] = (old_name, content)
                    art_updated += 1
            else:
                art_map[key] = (big_path, content)
                art_added += 1

    if forbidden_hits:
        raise RuntimeError("Refusing forbidden ART overwrite: " + ", ".join(forbidden_hits))

    cs_key = "data\\ini\\commandset.ini"
    if cs_key not in data_map:
        raise RuntimeError("packed CommandSet.ini missing")
    cs_name, cs_content = data_map[cs_key]
    data_map[cs_key] = (cs_name, patch_iraq_vt72b_slot14(cs_content))

    csf_key = "data\\english\\generals.csf"
    if csf_key in data_map:
        csf_name, csf_content = data_map[csf_key]
        data_map[csf_key] = (csf_name, patch_csf(csf_content, CSF_LABELS))

    final_data = finalize(data_keys, data_map)
    final_art = finalize(art_keys, art_map)

    # validations
    missing_art = [p for p in REQUIRED_ART if norm_key(p) not in {norm_key(k) for k in final_art}]
    if missing_art:
        raise RuntimeError("Missing required ART in output: " + ", ".join(missing_art))
    if norm_key("Art\\Textures\\abarfrccmd.dds") in {norm_key(p) for p in REQUIRED_ART}:
        raise RuntimeError("abarfrccmd must not be in required import set")
    irq_wf = next((n for n in final_art if norm_key(n) == "art\\w3d\\irq_warfactory.w3d"), None)
    if irq_wf:
        old = dict((norm_key(n), (n, c)) for n, c in [(n, art_raw[o:o+s]) for n,o,s in art_entries])
        # compare against original ART big if present
        orig = {norm_key(n): raw[off:off+sz] for n, off, sz in art_entries}
        if "art\\w3d\\irq_warfactory.w3d" in orig:
            if final_art[irq_wf] != orig["art\\w3d\\irq_warfactory.w3d"]:
                raise RuntimeError("Irq_WarFactory.W3D was modified")

    cs_out = next(v for k, v in ((norm_key(n), c) for n, c in final_data.items()) if k == "data\\ini\\commandset.ini")
    cs_text = cs_out.decode("latin1", errors="replace")
    i = cs_text.find("CommandSet Iraq_VT72BCommandSet")
    j = cs_text.find("\nEnd", i)
    block = cs_text[i : j + 4]
    assert "14 = Command_ConstructIraq_MissileFactory" in block or "14  = Command_ConstructIraq_MissileFactory" in block
    assert "Command_DisarmMinesAtPosition" not in block
    assert "Command_ConstructIraq_WarFactory_T" in block
    assert "Command_ConstructIraq_HeavyAirBase" in block

    obj_hits = [n for n, c in final_data.items() if b"Object Iraq_MissileFactory" in c]
    if len(obj_hits) != 1:
        raise RuntimeError(f"Iraq_MissileFactory object definition count={len(obj_hits)} {obj_hits}")

    out_data = args.out_dir / "_SPEC_DATA_ONE.big"
    out_art = args.out_dir / "_SPEC_ART_ONE.big"
    data_bytes = build_big(final_data)
    art_bytes = build_big(final_art)
    out_data.write_bytes(data_bytes)
    out_art.write_bytes(art_bytes)

    hashes = (
        f"_SPEC_DATA_ONE.big  {len(data_bytes)}  SHA256={sha256(data_bytes)}\n"
        f"_SPEC_ART_ONE.big   {len(art_bytes)}  SHA256={sha256(art_bytes)}\n"
    )
    (args.out_dir / "HASHES.txt").write_text(hashes, encoding="utf-8")
    print(f"DATA: preserved={len(data_entries)} added={added} updated={updated} skipped_stock={skipped_stock} final={len(final_data)}")
    print(f"ART:  preserved={len(art_entries)} added={art_added} updated={art_updated} final={len(final_art)}")
    print(hashes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
