#!/usr/bin/env python3
"""Pack China heavy aircraft expansion into _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big.

Adds overlay INI + donor ART. Patches packed China_HeavyAirBaseCommandSet in place
(does not create a second CommandSet). Does not overwrite existing aircraft INI.
Does not patch China_LargeAirBaseCommandSet (fighters stay on the fighter airbase).
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
DONOR = Path("/tmp/donor_china_heavy")
BASE_DATA = Path("/tmp/china_fighter_expansion/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/china_fighter_expansion/_SPEC_ART_ONE.big")

CSF_LABELS = {
    "CONTROLBAR:ConstructChinaBomberH6K": "H-6K",
    "CONTROLBAR:ToolTipChinaBomberH6K": "PLA H-6K bomber. CJ-10 cruise missiles and heavy bombs.",
    "OBJECT:ChinaBomberH6K": "H-6K\r\n6x CJ-10 cruise\r\n8x bombs\r\nCarpet bombs",
    "CONTROLBAR:ConstructChinaJetY20": "Y-20",
    "CONTROLBAR:ToolTipChinaJetY20": "PLA Y-20 Kunpeng transport. Infantry and vehicle airlift.",
    "OBJECT:ChinaJetY20": "Y-20 Kunpeng\r\nTransport",
    "CONTROLBAR:ConstructChinaAircraftY20AEW": "Y-20 AEW",
    "CONTROLBAR:ToolTipChinaAircraftY20AEW": "PLA Y-20 AEW / KJ-3000. Airborne radar scan.",
    "OBJECT:ChinaAircraftY20AEW": "Y-20 AEW\r\nSAR scan",
}

NEW_COMMANDSET = """CommandSet China_HeavyAirBaseCommandSet
  1  = Command_ConstructChinaAircraftKJ500
  2  = Command_ConstructChinaJetJH7BHeavy
  3  = Command_ConstructChinaJetJH7A2
  4  = Command_ConstructChinaHelicopterZ18A
  5  = Command_ConstructChinaBomberH6K
  6  = Command_ConstructChinaJetY20
  7  = Command_ConstructChinaAircraftY20AEW
  8  = Command_ConstructChinaDroneCH5
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

ART_MAP = [
    ("Art/w3d/h6k.W3D", "Art\\W3D\\h6k.W3D"),
    ("Art/w3d/HXYun20HXNew.W3D", "Art\\W3D\\HXYun20HXNew.W3D"),
    ("Art/w3d/HXYun20YJ.W3D", "Art\\W3D\\HXYun20YJ.W3D"),
    ("Art/Textures/h6k.dds", "Art\\Textures\\h6k.dds"),
    ("Art/Textures/h6k.dds", "Art\\Textures\\h6k.tga"),
    ("Art/Textures/planeH.dds", "Art\\Textures\\planeH.dds"),
    ("Art/Textures/planeH.dds", "Art\\Textures\\planeH.tga"),
    ("Art/Textures/planeJZ.dds", "Art\\Textures\\planeJZ.dds"),
    ("Art/Textures/planeJZ.dds", "Art\\Textures\\planeJZ.tga"),
    ("Art/Textures/yujing1.dds", "Art\\Textures\\yujing1.dds"),
    ("Art/Textures/yujing1.dds", "Art\\Textures\\yujing1.tga"),
    ("Art/Textures/CHNH6KTB.tga", "Art\\Textures\\CHNH6KTB.tga"),
    ("Art/Textures/CHNY20TB.tga", "Art\\Textures\\CHNY20TB.tga"),
    ("Art/Textures/CHNKJ2000TB.tga", "Art\\Textures\\CHNKJ2000TB.tga"),
]

OVERLAY_OBJECT_FILES = {"H6K.ini", "Y20.ini", "Y20AEW.ini"}
OVERLAY_NAMED = {
    "Weapon_ChinaHeavyExpansion.ini",
    "CommandButton_ChinaHeavyExpansion.ini",
    "China_HeavyExpansion_Images.INI",
}


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
        labels.append((b" LBL", key, [(b" STR", value, b"")]))
        added += 1
    print(f"CSF added {added} labels (existing {len(have)})")
    return build_csf(version, unk, lang, labels)


def patch_commandset(text: str) -> str:
    pattern = re.compile(
        r"CommandSet China_HeavyAirBaseCommandSet\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    m = pattern.search(text)
    if not m:
        raise SystemExit("China_HeavyAirBaseCommandSet not found in packed CommandSet.ini")
    old = m.group(0)
    if "Command_ConstructChinaBomberH6K" in old:
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
        n_obj = len(re.findall(r"^Object\s+\S+", text, re.M))
        n_wpn = len(re.findall(r"^Weapon\s+\S+", text, re.M))
        n_btn = len(re.findall(r"^CommandButton\s+\S+", text, re.M))
        n_end = len(re.findall(r"^End\s*$", text, re.M))
        if n_end == 0 and (n_obj + n_wpn + n_btn) > 0:
            errors.append(f"{name}: missing End")
    if errors:
        raise SystemExit("PARSER CHECK FAIL\n" + "\n".join(errors))
    print("PARSER CHECK PASS")


def blob_from_map(amap, key_substr: str) -> bytes:
    key_substr = key_substr.lower()
    for key, (_name, content) in amap.items():
        if key_substr in key:
            return content
    raise SystemExit(f"missing packed entry matching {key_substr}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/china_heavy_aircraft"))
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

    # Baseline hashes of existing China aircraft that must stay byte-identical.
    protect = {
        "j10c.ini": hashlib.sha256(blob_from_map(data_map, "pla\\airforce\\j10c.ini")).hexdigest(),
        "h6m.ini": hashlib.sha256(blob_from_map(data_map, "science objects\\h6m.ini")).hexdigest(),
        "ch5.ini": hashlib.sha256(blob_from_map(data_map, "pla\\drones\\ch5.ini")).hexdigest(),
        "china_system.ini": hashlib.sha256(blob_from_map(data_map, "pla\\china_system.ini")).hexdigest(),
        "j11b.ini": hashlib.sha256(blob_from_map(data_map, "pla\\airforce\\j11b.ini")).hexdigest(),
    }

    overlay: dict[str, bytes] = {}
    patch_data = ROOT / "patch/Data"
    for path in sorted(patch_data.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(patch_data).as_posix()
        keep = False
        if rel.startswith("INI/Object/Specter/PLA/Airforce/") and path.name in OVERLAY_OBJECT_FILES:
            keep = True
        if path.name in OVERLAY_NAMED:
            keep = True
        if not keep:
            continue
        big_name = "Data\\" + rel.replace("/", "\\")
        overlay[big_name] = lf(path.read_bytes())

    parse_check(overlay)

    cs_key = "data\\ini\\commandset.ini"
    cs_name, cs_bytes = data_map[cs_key]
    cs_text = cs_bytes.decode("latin1")
    large_before = re.search(
        r"CommandSet China_LargeAirBaseCommandSet\s*\n.*?^End\s*$",
        cs_text,
        re.M | re.S,
    )
    if not large_before:
        raise SystemExit("China_LargeAirBaseCommandSet missing before patch")
    large_text = large_before.group(0)
    cs_new = patch_commandset(cs_text)
    if cs_new == cs_text:
        raise SystemExit("CommandSet patch produced no change")
    if cs_new.count("CommandSet China_HeavyAirBaseCommandSet") != 1:
        raise SystemExit("duplicate China_HeavyAirBaseCommandSet after patch")
    if cs_new.count("CommandSet China_LargeAirBaseCommandSet") != 1:
        raise SystemExit("duplicate China_LargeAirBaseCommandSet after patch")
    large_after = re.search(
        r"CommandSet China_LargeAirBaseCommandSet\s*\n.*?^End\s*$",
        cs_new,
        re.M | re.S,
    ).group(0)
    if large_after != large_text:
        raise SystemExit("China_LargeAirBaseCommandSet was modified; abort")
    if "Command_ConstructChinaJetJ11B" not in large_after:
        raise SystemExit("fighter CommandSet lost J-11B")
    data_map[cs_key] = (cs_name, lf(cs_new.encode("latin1")))
    print("Patched CommandSet China_HeavyAirBaseCommandSet")

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
                added_art.append(dest + " (unchanged)")
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

    zpath = out / "CHINA_HEAVY_AIRCRAFT.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")

    # Post-pack verify from written BIG.
    v_entries, v_raw = read_big(out_data)
    v_map = {}
    for name, off, size in v_entries:
        v_map[norm_key(name)] = v_raw[off : off + size]
    a_entries, a_raw = read_big(out_art)
    a_names = {norm_key(n) for n, _o, _s in a_entries}

    def must_hash(key_substr, expected):
        blob = None
        for k, b in v_map.items():
            if key_substr in k:
                blob = b
                break
        if blob is None:
            raise SystemExit(f"verify missing {key_substr}")
        got = hashlib.sha256(blob).hexdigest()
        if got != expected:
            raise SystemExit(f"protected file changed: {key_substr}")

    must_hash("pla\\airforce\\j10c.ini", protect["j10c.ini"])
    must_hash("science objects\\h6m.ini", protect["h6m.ini"])
    must_hash("pla\\drones\\ch5.ini", protect["ch5.ini"])
    must_hash("pla\\china_system.ini", protect["china_system.ini"])
    must_hash("pla\\airforce\\j11b.ini", protect["j11b.ini"])

    cs = v_map["data\\ini\\commandset.ini"].decode("latin1")
    if "Command_ConstructChinaBomberH6K" not in cs:
        raise SystemExit("H-6K button missing from CommandSet")
    if "Command_ConstructChinaJetY20" not in cs:
        raise SystemExit("Y-20 button missing from CommandSet")
    if "Command_ConstructChinaAircraftY20AEW" not in cs:
        raise SystemExit("Y-20 AEW button missing from CommandSet")
    if "Command_ConstructChinaDroneCH5" not in cs:
        raise SystemExit("CH-5 button missing from CommandSet")
    if cs.count("CommandSet China_HeavyAirBaseCommandSet") != 1:
        raise SystemExit("duplicate heavy CommandSet")
    if "Command_ConstructChinaJetJ11B" not in cs:
        raise SystemExit("fighter J-11B missing after heavy pack")

    for req in (
        "data\\ini\\object\\specter\\pla\\airforce\\h6k.ini",
        "data\\ini\\object\\specter\\pla\\airforce\\y20.ini",
        "data\\ini\\object\\specter\\pla\\airforce\\y20aew.ini",
        "data\\ini\\weapon_chinaheavyexpansion.ini",
        "data\\ini\\commandbutton_chinaheavyexpansion.ini",
        "data\\ini\\mappedimages\\handcreated\\china_heavyexpansion_images.ini",
    ):
        if req not in v_map:
            raise SystemExit(f"overlay missing from DATA BIG: {req}")

    for req in (
        "art\\w3d\\h6k.w3d",
        "art\\w3d\\hxyun20hxnew.w3d",
        "art\\w3d\\hxyun20yj.w3d",
        "art\\textures\\h6k.dds",
        "art\\textures\\planeh.dds",
        "art\\textures\\planejz.dds",
        "art\\textures\\chnh6ktb.tga",
        "art\\textures\\chny20tb.tga",
        "art\\textures\\chnkj2000tb.tga",
    ):
        if req not in a_names:
            raise SystemExit(f"ART missing {req}")

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
                "PROTECTED EXISTING AIRCRAFT HASHES UNCHANGED",
                "FIGHTER LARGE AIRBASE UNCHANGED",
            ]
        )
        + "\n"
    )
    print(report.read_text())
    print(f"Wrote {out_data} {out_art} {zpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
