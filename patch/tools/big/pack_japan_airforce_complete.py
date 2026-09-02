#!/usr/bin/env python3
"""Build the complete Japan Air Force replacement pack.

Starts from the last-stable full BIGs (v0.4.44) and:
  * keeps every existing ART/DATA file (other countries untouched)
  * adds Japan donor W3Ds
  * adds unique Japan_* fighter objects (no duplicate Object IDs)
  * retargets existing Japan airfield CommandButtons to those objects
  * replaces the F-15J slot with F-16AJ
  * does NOT pack CommandSet_Japan.ini (would duplicate Japan CommandSets)

Usage:
  python3 pack_japan_airforce_complete.py \\
    --data-big /path/_SPEC_DATA_ONE.big \\
    --art-big /path/_SPEC_ART_ONE.big \\
    --patch-root /path/to/patch \\
    --out-dir /path/out
"""

from __future__ import annotations

import argparse
import hashlib
import re
import struct
import zipfile
from pathlib import Path

AIRFIELD = """CommandSet Japan_AirfieldCommandSet
  1 = Command_ConstructJapan_F35A
  2 = Command_ConstructJapan_F35B
  3 = Command_ConstructJapan_F15JKai
  4 = Command_ConstructJapan_F15DJ
  5 = Command_ConstructJapan_F2A
  6 = Command_ConstructJapan_F2B
  7 = Command_ConstructJapan_X2Shinshin
  8 = Command_ConstructJapan_F3GCAP
  9 = Command_ConstructJapan_F4EJKai
  10 = Command_ConstructJapan_F3
  11 = Command_ConstructJapan_F16AJ
  12 = Command_ConstructJapan_F2Kai
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

AIRFIELD_USED = "Japan_JASDF_AirfieldCommandSet"

BUTTON_OBJECT = {
    "Command_ConstructJapanJetF35A": "Japan_F35A",
    "Command_ConstructJapanJetF35B": "Japan_F35B",
    "Command_ConstructJapanJetF15JKai": "Japan_F15JKai",
    "Command_ConstructJapanJetF15DJ": "Japan_F15DJ",
    "Command_ConstructJapanJetF2A": "Japan_F2A",
    "Command_ConstructJapanJetF2B": "Japan_F2B",
    "Command_ConstructJapanJetX2Shinshin": "Japan_X2Shinshin",
    "Command_ConstructJapanJetFX": "Japan_F3GCAP",
    "Command_ConstructJapanJetF4EJKai": "Japan_F4EJKai",
    "Command_ConstructJapanJetF3": "Japan_F3",
    "Command_ConstructJapanJetF15J": "Japan_F16AJ",
    "Command_ConstructJapanJetF2Kai": "Japan_F2Kai",
}

CSF_SET = {
    "CONTROLBAR:ConstructJapanJetF15J": "F-16AJ",
    "CONTROLBAR:ToolTipJapanJetF15J": "JASDF F-16AJ. AAM and Paveway loadout.",
    "OBJECT:JapanJetF15J": "F-16AJ",
    "OBJECT:Japan_F35A": "F-35A",
    "OBJECT:Japan_F35B": "F-35B",
    "OBJECT:Japan_F15JKai": "F-15J Kai",
    "OBJECT:Japan_F15DJ": "F-15DJ",
    "OBJECT:Japan_F2A": "F-2A",
    "OBJECT:Japan_F2B": "F-2B",
    "OBJECT:Japan_X2Shinshin": "X-2 Shinshin",
    "OBJECT:Japan_F3GCAP": "F-X",
    "OBJECT:Japan_F4EJKai": "F-4EJ Kai",
    "OBJECT:Japan_F3": "F-3 GCAP",
    "OBJECT:Japan_F16AJ": "F-16AJ",
    "OBJECT:Japan_F2Kai": "F-2 Kai",
    "CONTROLBAR:ConstructJapan_F35A": "F-35A",
    "CONTROLBAR:ConstructJapan_F35B": "F-35B",
    "CONTROLBAR:ConstructJapan_F15JKai": "F-15J Kai",
    "CONTROLBAR:ConstructJapan_F15DJ": "F-15DJ",
    "CONTROLBAR:ConstructJapan_F2A": "F-2A",
    "CONTROLBAR:ConstructJapan_F2B": "F-2B",
    "CONTROLBAR:ConstructJapan_X2Shinshin": "X-2 Shinshin",
    "CONTROLBAR:ConstructJapan_F3GCAP": "F-X GCAP",
    "CONTROLBAR:ConstructJapan_F4EJKai": "F-4EJ Kai",
    "CONTROLBAR:ConstructJapan_F3": "F-3",
    "CONTROLBAR:ConstructJapan_F16AJ": "F-16AJ",
    "CONTROLBAR:ConstructJapan_F2Kai": "F-2 Kai",
    "CONTROLBAR:ToolTipConstructJapan_F35A": "JASDF F-35A",
    "CONTROLBAR:ToolTipConstructJapan_F35B": "JASDF F-35B",
    "CONTROLBAR:ToolTipConstructJapan_F15JKai": "JASDF F-15J Kai",
    "CONTROLBAR:ToolTipConstructJapan_F15DJ": "JASDF F-15DJ",
    "CONTROLBAR:ToolTipConstructJapan_F2A": "JASDF F-2A",
    "CONTROLBAR:ToolTipConstructJapan_F2B": "JASDF F-2B",
    "CONTROLBAR:ToolTipConstructJapan_X2Shinshin": "JASDF X-2 Shinshin",
    "CONTROLBAR:ToolTipConstructJapan_F3GCAP": "JASDF GCAP F-X",
    "CONTROLBAR:ToolTipConstructJapan_F4EJKai": "JASDF F-4EJ Kai",
    "CONTROLBAR:ToolTipConstructJapan_F3": "JASDF F-3",
    "CONTROLBAR:ToolTipConstructJapan_F16AJ": "JASDF F-16AJ",
    "CONTROLBAR:ToolTipConstructJapan_F2Kai": "JASDF F-2 Kai",
}

JP_AIR = (
    "Data/INI/Object/Specter/Japan Self-Defense Forces/Airforce"
)

DATA_ADD = [
    f"{JP_AIR}/Japan_F35A.ini",
    f"{JP_AIR}/Japan_F35B.ini",
    f"{JP_AIR}/Japan_F15JKai.ini",
    f"{JP_AIR}/Japan_F15DJ.ini",
    f"{JP_AIR}/Japan_F2A.ini",
    f"{JP_AIR}/Japan_F2B.ini",
    f"{JP_AIR}/Japan_F2Kai.ini",
    f"{JP_AIR}/Japan_F3GCAP.ini",
    f"{JP_AIR}/Japan_F4EJKai.ini",
    f"{JP_AIR}/Japan_F3.ini",
    f"{JP_AIR}/Japan_F16DBlk52.ini",
    f"{JP_AIR}/Japan_X2Shinshin.ini",
    "Data/INI/Object/Specter/United States Of America/Airforce/F35C.ini",
    "Data/INI/Object/Specter/United States Of America/Airforce/F35C_AA.ini",
    "Data/INI/Weapon_Japan.ini",
    "Data/INI/CommandSet_zzz_JapanAirForce.ini",
    "Data/INI/CommandButton_Japan_AirForce.ini",
    "Data/INI/Object/Specter/Japan Self-Defense Forces/Buildings/Japan_Airfield.ini",
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


def decode_wcs(raw: bytes, n: int) -> str:
    chars = []
    for j in range(n):
        ch = struct.unpack_from("<H", raw, j * 2)[0] ^ 0xFFFF
        if ch:
            chars.append(chr(ch))
    return "".join(chars)


def encode_wcs(text: str) -> bytes:
    out = bytearray()
    for ch in text:
        out += struct.pack("<H", ord(ch) ^ 0xFFFF)
    return bytes(out)


def parse_csf(blob: bytes) -> tuple[tuple, list[tuple[str, str]]]:
    magic, ver, nlab, nstr, extra, lang = struct.unpack_from("<4sIIIII", blob)
    pos = 24
    labels: list[tuple[str, str]] = []
    for _ in range(nlab):
        lid, scount, nlen = struct.unpack_from("<4sII", blob, pos)
        pos += 12
        name = blob[pos : pos + nlen].decode("latin1", errors="replace")
        pos += nlen
        val = ""
        for _s in range(scount):
            sid = blob[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", blob, pos)[0]
            pos += 4
            raw = blob[pos : pos + slen * 2]
            pos += slen * 2
            val = decode_wcs(raw, slen)
            if sid == b"WRTS":
                elen = struct.unpack_from("<I", blob, pos)[0]
                pos += 4 + elen
        labels.append((name, val))
    return (magic, ver, extra, lang), labels


def build_csf(header: tuple, labels: list[tuple[str, str]]) -> bytes:
    magic, ver, extra, lang = header
    out = bytearray()
    out += struct.pack("<4sIIIII", magic, ver, len(labels), len(labels), extra, lang)
    for name, val in labels:
        nb = name.encode("latin1", errors="replace")
        wb = encode_wcs(val)
        out += struct.pack("<4sII", b" LBL", 1, len(nb))
        out += nb
        out += b" RTS"
        out += struct.pack("<I", len(val))
        out += wb
    return bytes(out)


def patch_csf(blob: bytes, updates: dict[str, str]) -> bytes:
    header, labels = parse_csf(blob)
    by_name = {k: i for i, (k, _) in enumerate(labels)}
    for key, val in updates.items():
        if key in by_name:
            i = by_name[key]
            labels[i] = (key, val)
        else:
            labels.append((key, val))
    return build_csf(header, labels)


def patch_commandset(text: str) -> str:
    def retarget(m: re.Match) -> str:
        block = m.group(0)
        name = m.group(1)
        new_obj = BUTTON_OBJECT[name]
        return re.sub(
            r"(?m)^(\s*Object\s*=\s*)\S+",
            rf"\1{new_obj}",
            block,
            count=1,
        )

    names = "|".join(re.escape(n) for n in BUTTON_OBJECT)
    text = re.sub(
        rf"(?ms)^CommandButton ({names})\n.*?^End\s*$",
        retarget,
        text,
    )
    # Buildings use Japan_JASDF_AirfieldCommandSet in CommandSet_zzz_*.ini.
    # A second Japan_AirfieldCommandSet here crashes ZH on parse.
    text = re.sub(
        r"(?ms)^CommandSet Japan_AirfieldCommandSet\b.*?^End\s*\n?",
        "",
        text,
    )
    return text


def put_map(amap: dict[str, tuple[str, bytes]], big_path: str, content: bytes) -> str:
    key = norm_key(big_path)
    display = big_path.replace("/", "\\")
    if key in amap:
        old_name, _old = amap[key]
        amap[key] = (old_name, content)
        return "updated"
    amap[key] = (display, content)
    return "added"


def finalize(order_keys: list[str], amap: dict[str, tuple[str, bytes]]) -> dict[str, bytes]:
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

    data_map: dict[str, tuple[str, bytes]] = {}
    data_keys: list[str] = []
    for name, off, size in data_entries:
        key = norm_key(name)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (name.replace("/", "\\"), data_raw[off : off + size])

    art_map: dict[str, tuple[str, bytes]] = {}
    art_keys: list[str] = []
    for name, off, size in art_entries:
        key = norm_key(name)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (name.replace("/", "\\"), art_raw[off : off + size])

    added = updated = 0
    for rel in DATA_ADD:
        src = args.patch_root / rel
        if not src.is_file():
            raise FileNotFoundError(src)
        status = put_map(data_map, rel, src.read_bytes())
        if status == "added":
            added += 1
        else:
            updated += 1

    cs_key = "data\\ini\\commandset.ini"
    cs_name, cs_blob = data_map[cs_key]
    data_map[cs_key] = (cs_name, patch_commandset(cs_blob.decode("latin1")).encode("latin1"))
    updated += 1

    lab_key = "data\\ini\\object\\specter\\japan self-defense forces\\buildings\\japan_largeairbase.ini"
    if lab_key in data_map:
        lab_name, lab_blob = data_map[lab_key]
        lab_txt = lab_blob.decode("latin1")
        lab_txt = re.sub(
            r"(?m)^(\s*CommandSet\s*=\s*)Japan_AirfieldCommandSet\s*$",
            rf"\1{AIRFIELD_USED}",
            lab_txt,
        )
        data_map[lab_key] = (lab_name, lab_txt.encode("latin1"))
        updated += 1

    csf_key = "data\\english\\generals.csf"
    csf_name, csf_blob = data_map[csf_key]
    data_map[csf_key] = (csf_name, patch_csf(csf_blob, CSF_SET))
    updated += 1

    art_added = art_updated = 0
    art_root = args.patch_root / "Art"
    for path in sorted(art_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(args.patch_root).as_posix()
        status = put_map(art_map, rel, path.read_bytes())
        if status == "added":
            art_added += 1
        else:
            art_updated += 1

    final_data = finalize(data_keys, data_map)
    final_art = finalize(art_keys, art_map)
    out_data = args.out_dir / "_SPEC_DATA_ONE.big"
    out_art = args.out_dir / "_SPEC_ART_ONE.big"
    data_bytes = build_big(final_data)
    art_bytes = build_big(final_art)
    out_data.write_bytes(data_bytes)
    out_art.write_bytes(art_bytes)

    zip_path = args.out_dir / "SPECTER_JAPAN_AIRFORCE.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(out_data, arcname="_SPEC_DATA_ONE.big")
        zf.write(out_art, arcname="_SPEC_ART_ONE.big")

    print(f"DATA: baseline={len(data_entries)} added={added} updated={updated} final={len(final_data)} bytes={len(data_bytes)} sha256={hashlib.sha256(data_bytes).hexdigest()}")
    print(f"ART:  baseline={len(art_entries)} added={art_added} updated={art_updated} final={len(final_art)} bytes={len(art_bytes)} sha256={hashlib.sha256(art_bytes).hexdigest()}")
    print(f"ZIP:  {zip_path} bytes={zip_path.stat().st_size} sha256={hashlib.sha256(zip_path.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
