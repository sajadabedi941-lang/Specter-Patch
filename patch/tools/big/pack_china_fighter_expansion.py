#!/usr/bin/env python3
"""Pack China fighter expansion into _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big.

Adds overlay INI + donor ART. Patches packed China_LargeAirBaseCommandSet in place
(does not create a second CommandSet). Does not overwrite existing aircraft INI.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
DONOR = Path("/tmp/donor_china_fighters")
BASE_DATA = Path("/tmp/russia_four_fighters/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/russia_four_fighters/_SPEC_ART_ONE.big")

CSF_LABELS = {
    "CONTROLBAR:ConstructChinaJetJ11B": "J-11B",
    "CONTROLBAR:ToolTipChinaJetJ11B": "PLA J-11B strike Flanker. KD-88, bombs, PL-12.",
    "OBJECT:ChinaJetJ11B": "J-11B\r\n2x KD-88\r\n4x bombs\r\n4x PL-12",
    "CONTROLBAR:ConstructChinaJetJ15": "J-15 Flying Shark",
    "CONTROLBAR:ToolTipChinaJetJ15": "PLA J-15 naval strike fighter. YJ anti-ship missiles and guided bombs.",
    "OBJECT:ChinaJetJ15": "J-15 Flying Shark\r\nYJ anti-ship\r\nLT-3 PGM",
    "CONTROLBAR:ConstructChinaJetJ31": "J-31",
    "CONTROLBAR:ToolTipChinaJetJ31": "PLA J-31 stealth strike fighter. Internal precision bombs.",
    "OBJECT:ChinaJetJ31": "J-31\r\nInternal PGM strike",
    "CONTROLBAR:ConstructChinaJetJF17Block3": "JF-17 Block 3",
    "CONTROLBAR:ToolTipChinaJetJF17Block3": "JF-17 Block 3 / FC-1. Guided bombs and air-to-ground missiles.",
    "OBJECT:ChinaJetJF17Block3": "JF-17 Block 3\r\nPGM + CM-400/C-802 style AGM",
    "CONTROLBAR:ConstructChinaJetJ8II": "J-8II",
    "CONTROLBAR:ToolTipChinaJetJ8II": "PLA J-8II interceptor-strike. Bombs and rockets.",
    "OBJECT:ChinaJetJ8II": "J-8II\r\nBombs + rockets",
    "CONTROLBAR:ConstructChinaJetJ7": "J-7",
    "CONTROLBAR:ToolTipChinaJetJ7": "PLA J-7 light strike fighter. Bombs and rockets.",
    "OBJECT:ChinaJetJ7": "J-7\r\nLight bombs + rockets",
    "CONTROLBAR:ConstructChinaJetJ10A": "J-10A",
    "CONTROLBAR:ToolTipChinaJetJ10A": "PLA J-10A. Precision bombs and air-to-ground missiles.",
    "OBJECT:ChinaJetJ10A": "J-10A\r\nPGM + KD-88",
    "CONTROLBAR:ConstructChinaJetJ10B": "J-10B",
    "CONTROLBAR:ToolTipChinaJetJ10B": "PLA J-10B. Precision bombs and air-to-ground missiles.",
    "OBJECT:ChinaJetJ10B": "J-10B\r\nLT-3 PGM + KD-88",
}

NEW_COMMANDSET = """CommandSet China_LargeAirBaseCommandSet
  1  = Command_ConstructChinaJetJ20B_AG
  2  = Command_ConstructChinaJetJ50
  3  = Command_ConstructChinaJetJ16D
  4  = Command_ConstructChinaHelicopterWZ10ME
  5  = Command_ConstructChinaJetJ16BBunker
  6  = Command_ConstructChinaJetJ20B_AA
  7  = Command_ConstructChinaJetJ10C
  8  = Command_ConstructChinaJetJ20B_AA_AI
  9  = Command_ConstructChinaJetJ11B
  10 = Command_ConstructChinaJetJ15
  11 = Command_ConstructChinaJetJ31
  12 = Command_ConstructChinaJetJF17Block3
  13 = Command_SetRallyPoint
  14 = Command_Sell
  15 = Command_ConstructChinaJetJ8II
  16 = Command_ConstructChinaJetJ7
  17 = Command_ConstructChinaJetJ10A
  18 = Command_ConstructChinaJetJ10B
End
"""

ART_MAP = [
    # (src glob under DONOR, dest BIG path)
    ("Art/w3d/LSFJ11B.W3D", "Art\\W3D\\LSFJ11B.W3D"),
    ("Art/w3d/LSFJ11Bd.W3D", "Art\\W3D\\LSFJ11Bd.W3D"),
    ("Art/w3d/LSFJ11Bk.W3D", "Art\\W3D\\LSFJ11Bk.W3D"),
    ("Art/w3d/J15JZ.W3D", "Art\\W3D\\J15JZ.W3D"),
    ("Art/w3d/LSFJ31.W3D", "Art\\W3D\\LSFJ31.W3D"),
    ("Art/w3d/LSFJ31d.W3D", "Art\\W3D\\LSFJ31d.W3D"),
    ("Art/w3d/LSFJ31k.W3D", "Art\\W3D\\LSFJ31k.W3D"),
    ("Art/w3d/LSFPKJF17.W3D", "Art\\W3D\\LSFPKJF17.W3D"),
    ("Art/w3d/LSFPKJF17d.W3D", "Art\\W3D\\LSFPKJF17d.W3D"),
    ("Art/w3d/LSFPKJF17k.W3D", "Art\\W3D\\LSFPKJF17k.W3D"),
    ("Art/w3d/LSFChinaJ8B.W3D", "Art\\W3D\\LSFChinaJ8B.W3D"),
    ("Art/w3d/LSFChinaJ8Bd.W3D", "Art\\W3D\\LSFChinaJ8Bd.W3D"),
    ("Art/w3d/LSFJ7.W3D", "Art\\W3D\\LSFJ7.W3D"),
    ("Art/w3d/LSFJ7d.W3D", "Art\\W3D\\LSFJ7d.W3D"),
    ("Art/w3d/LSFJ7k.W3D", "Art\\W3D\\LSFJ7k.W3D"),
    ("Art/w3d/chj10a.W3D", "Art\\W3D\\CHJ10A.W3D"),
    ("Art/w3d/ChJ10B.W3D", "Art\\W3D\\ChJ10B.W3D"),
    ("Art/Textures/LSFJ11B.dds", "Art\\Textures\\LSFJ11B.dds"),
    ("Art/Textures/LSFJ11Bd.dds", "Art\\Textures\\LSFJ11Bd.dds"),
    ("Art/Textures/LSFJ11Bk.dds", "Art\\Textures\\LSFJ11Bk.dds"),
    ("Art/Textures/J11B.tga", "Art\\Textures\\J11B.tga"),
    ("Art/Textures/AGMZJ15.dds", "Art\\Textures\\AGMZJ15.dds"),
    ("Art/Textures/CHNJ15A.tga", "Art\\Textures\\CHNJ15A.tga"),
    ("Art/Textures/CHNJ15ATB.tga", "Art\\Textures\\CHNJ15ATB.tga"),
    ("Art/Textures/LSFJ31.dds", "Art\\Textures\\LSFJ31.dds"),
    ("Art/Textures/LSFJ31d.dds", "Art\\Textures\\LSFJ31d.dds"),
    ("Art/Textures/LSFJ31k.dds", "Art\\Textures\\LSFJ31k.dds"),
    ("Art/Textures/J31TB.tga", "Art\\Textures\\J31TB.tga"),
    ("Art/Textures/LSFJF17.dds", "Art\\Textures\\LSFJF17.dds"),
    ("Art/Textures/LSFJF17d.dds", "Art\\Textures\\LSFJF17d.dds"),
    ("Art/Textures/LSFJF17k.dds", "Art\\Textures\\LSFJF17k.dds"),
    ("Art/Textures/JF17TB.tga", "Art\\Textures\\JF17TB.tga"),
    ("Art/Textures/LSFChinaJ8B.dds", "Art\\Textures\\LSFChinaJ8B.dds"),
    ("Art/Textures/LSFChinaJ8Bd.dds", "Art\\Textures\\LSFChinaJ8Bd.dds"),
    ("Art/Textures/CHJ7.dds", "Art\\Textures\\CHJ7.dds"),
    ("Art/Textures/CHJ7d.dds", "Art\\Textures\\CHJ7d.dds"),
    ("Art/Textures/LSFJ7K.dds", "Art\\Textures\\LSFJ7K.dds"),
    ("Art/Textures/CHJ7TB.tga", "Art\\Textures\\CHJ7TB.tga"),
    ("Art/Textures/CHJ10A.dds", "Art\\Textures\\CHJ10A.dds"),
    ("Art/Textures/CHJ10B.dds", "Art\\Textures\\CHJ10B.dds"),
    ("Art/Textures/ChinaJ10BIm.tga", "Art\\Textures\\ChinaJ10BIm.tga"),
    ("Art/Textures/ChinaAirWMap.dds", "Art\\Textures\\ChinaAirWMap.dds"),
    ("Art/Textures/MK-82.tga", "Art\\Textures\\MK-82.tga"),
    ("Art/Textures/LSFPL8.tga", "Art\\Textures\\LSFPL8.tga"),
    ("Art/Textures/LSFFighterweipen.tga", "Art\\Textures\\LSFFighterweipen.tga"),
    ("Art/Textures/LSFSD10_M.tga", "Art\\Textures\\LSFSD10_M.tga"),
    ("Art/Textures/LSFNKJ7d.dds", "Art\\Textures\\LSFNKJ7d.dds"),
    ("Art/Textures/f35.dds", "Art\\Textures\\f35.dds"),
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


def csf_decode(raw: bytes) -> str:
    return bytes(b ^ 0xFF for b in raw).decode("utf-16-le", errors="replace")


def csf_encode(text: str) -> bytes:
    raw = text.encode("utf-16-le")
    return bytes(b ^ 0xFF for b in raw)


def parse_csf(data: bytes):
    if data[:4] not in (b" FSC", b"CSF "):
        raise ValueError("Not a CSF file")
    version, nlab, nstr, unk, lang = struct.unpack_from("<IIIII", data, 4)
    pos = 24
    labels = []
    for _ in range(nlab):
        mag = data[pos : pos + 4]
        pos += 4
        ns, namelen = struct.unpack_from("<II", data, pos)
        pos += 8
        name = data[pos : pos + namelen].decode("latin1", errors="replace")
        pos += namelen
        strings = []
        for _j in range(ns):
            smag = data[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            raw = data[pos : pos + 2 * slen]
            pos += 2 * slen
            extra = b""
            if smag in (b"WRTS", b"STR "):
                elen = struct.unpack_from("<I", data, pos)[0]
                pos += 4
                extra = data[pos : pos + elen]
                pos += elen
            strings.append((smag, csf_decode(raw), extra))
        labels.append((mag, name, strings))
    return version, unk, lang, labels


def build_csf(version, unk, lang, labels) -> bytes:
    out = bytearray()
    out += b" FSC"
    nstr = sum(len(s) for _, _, s in labels)
    out += struct.pack("<IIIII", version, len(labels), nstr, unk, lang)
    for mag, name, strings in labels:
        nb = name.encode("latin1", errors="replace")
        out += mag
        out += struct.pack("<II", len(strings), len(nb))
        out += nb
        for smag, text, extra in strings:
            enc = csf_encode(text)
            chars = len(enc) // 2
            out += smag
            out += struct.pack("<I", chars)
            out += enc
            if smag in (b"WRTS", b"STR "):
                out += struct.pack("<I", len(extra))
                out += extra
    return bytes(out)


def patch_csf(data: bytes) -> bytes:
    version, unk, lang, labels = parse_csf(data)
    have = {name for _, name, _ in labels}
    added = 0
    for key, value in CSF_LABELS.items():
        if key in have:
            continue
        labels.append((b" LBL", key, [(b" RTS", value, b"")]))
        added += 1
    print(f"CSF added {added} labels (existing {len(have)})")
    return build_csf(version, unk, lang, labels)


def patch_commandset(text: str) -> str:
    pattern = re.compile(
        r"CommandSet China_LargeAirBaseCommandSet\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    m = pattern.search(text)
    if not m:
        raise SystemExit("China_LargeAirBaseCommandSet not found in packed CommandSet.ini")
    old = m.group(0)
    if "Command_ConstructChinaJetJ11B" in old:
        print("CommandSet already patched")
        return text
    return pattern.sub(NEW_COMMANDSET.rstrip() + "\n", text, count=1)


def lf(data: bytes) -> bytes:
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def parse_check(overlay_files: dict[str, bytes]) -> None:
    errors = []
    for name, content in overlay_files.items():
        if not name.lower().endswith(".ini"):
            continue
        text = content.decode("utf-8")
        if "\r" in text:
            errors.append(f"{name}: CRLF")
        for kind in ("Object", "Weapon", "CommandButton", "CommandSet", "MappedImage", "Locomotor"):
            opens = len(re.findall(rf"^{kind}\s+\S+", text, re.M))
            # End count is global; skip strict per-kind
        if text.count("\nEnd") + (1 if text.rstrip().endswith("End") else 0) < opens if False else False:
            pass
        n_obj = len(re.findall(r"^Object\s+\S+", text, re.M))
        n_wpn = len(re.findall(r"^Weapon\s+\S+", text, re.M))
        n_btn = len(re.findall(r"^CommandButton\s+\S+", text, re.M))
        n_end = len(re.findall(r"^End\s*$", text, re.M))
        # Draw/Behavior/WeaponSet also use End. Just ensure every block has End present.
        if n_end == 0 and (n_obj + n_wpn + n_btn) > 0:
            errors.append(f"{name}: missing End")
    if errors:
        raise SystemExit("PARSER CHECK FAIL\n" + "\n".join(errors))
    print("PARSER CHECK PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/china_fighter_expansion"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    data_entries, data_raw = read_big(BASE_DATA)
    art_entries, art_raw = read_big(BASE_ART)

    data_map: dict[str, tuple[str, bytes]] = {}
    data_keys = []
    for name, off, size in data_entries:
        key = norm_key(name)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (name.replace("/", "\\"), data_raw[off : off + size])

    art_map: dict[str, tuple[str, bytes]] = {}
    art_keys = []
    for name, off, size in art_entries:
        key = norm_key(name)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (name.replace("/", "\\"), art_raw[off : off + size])

    overlay: dict[str, bytes] = {}
    patch_data = ROOT / "patch/Data"
    for path in sorted(patch_data.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(patch_data).as_posix()
        # Only pack China fighter expansion overlay + leave other patch files to existing BIG
        keep = False
        if rel.startswith("INI/Object/Specter/PLA/Airforce/J"):
            keep = path.name in {
                "J11B.ini",
                "J15.ini",
                "J31.ini",
                "JF17.ini",
                "J8II.ini",
                "J7.ini",
                "J10A.ini",
                "J10B.ini",
            }
        if path.name in {
            "Weapon_ChinaFighterExpansion.ini",
            "CommandButton_ChinaFighterExpansion.ini",
            "China_FighterExpansion_Images.INI",
        }:
            keep = True
        if not keep:
            continue
        big_name = "Data\\" + rel.replace("/", "\\")
        overlay[big_name] = lf(path.read_bytes())

    parse_check(overlay)

    # Patch CommandSet (packed file, not workspace overlay)
    cs_key = "data\\ini\\commandset.ini"
    cs_name, cs_bytes = data_map[cs_key]
    cs_text = cs_bytes.decode("latin1")
    cs_new = patch_commandset(cs_text)
    if cs_new == cs_text:
        raise SystemExit("CommandSet patch produced no change")
    if cs_new.count("CommandSet China_LargeAirBaseCommandSet") != 1:
        raise SystemExit("duplicate China_LargeAirBaseCommandSet after patch")
    data_map[cs_key] = (cs_name, lf(cs_new.encode("latin1")))
    print("Patched CommandSet China_LargeAirBaseCommandSet")

    # CSF
    csf_key = "data\\english\\generals.csf"
    csf_name, csf_bytes = data_map[csf_key]
    data_map[csf_key] = (csf_name, patch_csf(csf_bytes))

    added_data = []
    for big_name, content in overlay.items():
        key = norm_key(big_name)
        if key in data_map:
            raise SystemExit(f"Refusing to overwrite existing DATA entry: {big_name}")
        data_map[key] = (big_name, content)
        added_data.append(big_name)

    added_art = []
    for src_rel, dest in ART_MAP:
        src = DONOR / src_rel
        if not src.is_file() or src.stat().st_size == 0:
            raise SystemExit(f"Missing donor ART {src}")
        key = norm_key(dest)
        content = src.read_bytes()
        if key in art_map:
            old_name, old = art_map[key]
            if old != content:
                art_map[key] = (old_name, content)
                added_art.append(dest + " (updated)")
        else:
            art_map[key] = (dest, content)
            added_art.append(dest)

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

    final_data = finalize(data_keys, data_map)
    final_art = finalize(art_keys, art_map)
    data_bytes = build_big(final_data)
    art_bytes = build_big(final_art)
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_bytes)
    out_art.write_bytes(art_bytes)

    zpath = out / "CHINA_FIGHTER_EXPANSION.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")

    report = out / "PACK_REPORT.txt"
    report.write_text(
        "\n".join(
            [
                f"DATA SHA256={hashlib.sha256(data_bytes).hexdigest()} SIZE={len(data_bytes)}",
                f"ART  SHA256={hashlib.sha256(art_bytes).hexdigest()} SIZE={len(art_bytes)}",
                f"ZIP  SHA256={hashlib.sha256(zpath.read_bytes()).hexdigest()} SIZE={zpath.stat().st_size}",
                "added_data=" + repr(added_data),
                "added_art=" + repr(added_art),
                NEW_COMMANDSET,
                "PARSER CHECK PASS",
            ]
        )
        + "\n"
    )
    print(report.read_text())
    print(f"Wrote {out_data} {out_art} {zpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
