#!/usr/bin/env python3
"""Pack Russia Su-47 Berkut + Su-57 T-50 into the latest working DATA/ART BIGs.

Preserves original BIG entry order. Edits only:
  - Data\\INI\\CommandSet.ini  (Russia_LargeAirBaseCommandSet slots 11-12)
  - Data\\English\\generals.csf (new display strings)
  - new object / button / string files
  - new ART w3d + textures

Does not rewrite stock CommandButton.ini (extra CommandButton_*.ini is loaded).
Does not touch Heavy Air Base or other factions.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

DATA_SRC = Path("/tmp/russia_su35s_ka52/_SPEC_DATA_ONE.big")
ART_SRC = Path("/tmp/radar_pkg/_SPEC_ART_ONE.big")
PATCH = Path("/workspace/patch")
ART_DONOR = Path("/tmp/rus_new_art")
OUT = Path("/tmp/russia_su47_t50")


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def write_big(entries: list[tuple[str, bytes]]) -> bytes:
    header = 16
    encoded = []
    for name, blob in entries:
        raw = name.replace("/", "\\").encode("latin1")
        encoded.append((raw, blob))
        header += 8 + len(raw) + 1
    offset = header
    out = bytearray()
    total = header + sum(len(b) for _, b in encoded)
    out += b"BIGF"
    out += struct.pack(">I", total)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header)
    for raw, blob in encoded:
        out += struct.pack(">II", offset, len(blob))
        out += raw + b"\x00"
        offset += len(blob)
    for _, blob in encoded:
        out += blob
    return bytes(out)


def upsert(entries: list[tuple[str, bytes]], name: str, content: bytes) -> str:
    key = name.replace("/", "\\").lower()
    for i, (n, _) in enumerate(entries):
        if n.replace("/", "\\").lower() == key:
            entries[i] = (n, content)
            return "updated"
    entries.append((name.replace("/", "\\"), content))
    return "added"


def patch_commandset(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    old = (
        "CommandSet Russia_LargeAirBaseCommandSet\n"
        "  1  = Command_ConstructRussiaJetSu75Checkmate\n"
        "  2  = Command_ConstructRussiaJetSu35S\n"
        "  3  = Command_ConstructRussiaJetSu30SM2\n"
        "  4  = Command_ConstructRussiaJetSU25T\n"
        "  5  = Command_ConstructRussiaJetSu35AG\n"
        "  6  = Command_ConstructRussiaJetMig31K\n"
        "  7  = Command_ConstructRussiaHelicopterMi28N\n"
        "  8  = Command_ConstructRussiaHelicopterKA52\n"
        "  9  = Command_ConstructRussiaJetSu57AA\n"
        "  10 = Command_ConstructRussiaJetSu47Recon\n"
        "  13 = Command_SetRallyPoint\n"
        "  14 = Command_Sell\n"
        "End"
    )
    new = (
        "CommandSet Russia_LargeAirBaseCommandSet\n"
        "  1  = Command_ConstructRussiaJetSu75Checkmate\n"
        "  2  = Command_ConstructRussiaJetSu35S\n"
        "  3  = Command_ConstructRussiaJetSu30SM2\n"
        "  4  = Command_ConstructRussiaJetSU25T\n"
        "  5  = Command_ConstructRussiaJetSu35AG\n"
        "  6  = Command_ConstructRussiaJetMig31K\n"
        "  7  = Command_ConstructRussiaHelicopterMi28N\n"
        "  8  = Command_ConstructRussiaHelicopterKA52\n"
        "  9  = Command_ConstructRussiaJetSu57AA\n"
        "  10 = Command_ConstructRussiaJetSu47Recon\n"
        "  11 = Command_ConstructRussiaJetSu47Berkut\n"
        "  12 = Command_ConstructRussiaJetSu57T50\n"
        "  13 = Command_SetRallyPoint\n"
        "  14 = Command_Sell\n"
        "End"
    )
    if old not in text:
        raise SystemExit("Russia_LargeAirBaseCommandSet block not found exactly — abort")
    if text.count(old) != 1:
        raise SystemExit("Russia_LargeAirBaseCommandSet matched more than once — abort")
    patched = text.replace(old, new, 1)
    # safety: no other faction Large menus changed
    if patched.replace(new, old, 1) != text:
        raise SystemExit("unexpected commandset rewrite")
    return patched.encode("latin1")


def csf_decode_u16(buf: bytes) -> str:
    return bytes((~b) & 0xFF for b in buf).decode("utf-16-le", errors="replace")


def csf_encode_u16(s: str) -> bytes:
    raw = s.encode("utf-16-le")
    return bytes((~b) & 0xFF for b in raw)


def csf_append(blob: bytes, pairs: dict[str, str]) -> bytes:
    if blob[:4] != b" FSC":
        raise SystemExit(f"unexpected CSF magic {blob[:4]!r}")
    ver, nlab, nstr, unk, lang = struct.unpack_from("<IIIII", blob, 4)
    # collect existing keys
    p = 24
    existing = set()
    for _ in range(nlab):
        tag = blob[p : p + 4]
        p += 4
        if tag != b" LBL":
            raise SystemExit(f"bad label tag {tag!r} at {p}")
        nsl = struct.unpack_from("<I", blob, p)[0]
        p += 4
        nlen = struct.unpack_from("<I", blob, p)[0]
        p += 4
        key = blob[p : p + nlen].decode("ascii", "replace")
        p += nlen
        existing.add(key.upper())
        for _j in range(nsl):
            stag = blob[p : p + 4]
            p += 4
            slen = struct.unpack_from("<I", blob, p)[0]
            p += 4
            p += slen * 2
            if stag == b"WRTS":
                elen = struct.unpack_from("<I", blob, p)[0]
                p += 4 + elen
    extra = bytearray()
    added = 0
    for key, val in pairs.items():
        if key.upper() in existing:
            continue
        extra += b" LBL"
        extra += struct.pack("<I", 1)
        kb = key.encode("ascii")
        extra += struct.pack("<I", len(kb))
        extra += kb
        extra += b" RTS"
        enc = csf_encode_u16(val)
        extra += struct.pack("<I", len(enc) // 2)
        extra += enc
        added += 1
    header = bytearray(blob[:24])
    struct.pack_into("<I", header, 8, nlab + added)
    struct.pack_into("<I", header, 12, nstr + added)
    return bytes(header) + blob[24:] + extra


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    data_entries = read_big(DATA_SRC)
    art_entries = read_big(ART_SRC)

    # --- DATA new files ---
    new_data = {
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su47Berkut.ini": (
            PATCH / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/Su47Berkut.ini"
        ),
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su57T50.ini": (
            PATCH / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/Su57T50.ini"
        ),
        r"Data\INI\CommandButton_RussiaSu47T50.ini": PATCH / "Data/INI/CommandButton_RussiaSu47T50.ini",
        r"Data\English\SPECTER_RUSSIA_SU47_T50_Strings.txt": PATCH / "Data/English/SPECTER_RUSSIA_SU47_T50_Strings.txt",
    }
    data_ops = {}
    for name, path in new_data.items():
        data_ops[name] = upsert(data_entries, name, path.read_bytes())

    # --- CommandSet surgical ---
    cs_name = None
    cs_raw = None
    for n, b in data_entries:
        if n.replace("/", "\\").lower() == r"data\ini\commandset.ini":
            cs_name, cs_raw = n, b
            break
    if cs_raw is None:
        raise SystemExit("CommandSet.ini missing")
    cs_new = patch_commandset(cs_raw)
    upsert(data_entries, cs_name, cs_new)
    data_ops["CommandSet.ini"] = "patched-large-only"

    # --- CSF ---
    strings = {
        "OBJECT:RussiaSu47Berkut": "Su-47 Berkut",
        "CONTROLBAR:ConstructRussiaJetSu47Berkut": "Su-47 Berkut",
        "CONTROLBAR:ToolTipRussiaJetSu47Berkut": "Build Su-47 Berkut air-superiority fighter (R-77 / R-73)",
        "OBJECT:RussiaSu57T50": "Su-57 T-50 PAK FA",
        "CONTROLBAR:ConstructRussiaJetSu57T50": "Su-57 T-50 PAK FA",
        "CONTROLBAR:ToolTipRussiaJetSu57T50": "Build Su-57 T-50 PAK FA multirole fighter (R-77 / R-73 / KAB-2500)",
    }
    for n, b in data_entries:
        if n.replace("/", "\\").lower() == r"data\english\generals.csf":
            upsert(data_entries, n, csf_append(b, strings))
            data_ops["generals.csf"] = "appended"
            break
    else:
        raise SystemExit("generals.csf missing")

    # --- ART ---
    art_src = {
        r"Art\W3D\RUSU-47.W3D": ART_DONOR / "Art/w3d/RUSU-47.W3D",
        r"Art\W3D\RUSU-47_D.W3D": ART_DONOR / "Art/w3d/RUSU-47_D.W3D",
        r"Art\W3D\RUSU-47_E.W3D": ART_DONOR / "Art/w3d/RUSU-47_E.W3D",
        r"Art\W3D\LSFT50.W3D": ART_DONOR / "Art/w3d/LSFT50.W3D",
        r"Art\W3D\LSFT50d.W3D": ART_DONOR / "Art/w3d/LSFT50d.W3D",
        r"Art\W3D\LSFT50k.W3D": ART_DONOR / "Art/w3d/LSFT50k.W3D",
        r"Art\Textures\RUSU-47mainskin.tga": ART_DONOR / "Art/Textures/RUSU-47mainskin.tga",
        r"Art\Textures\RUSU-47mainskin_D.tga": ART_DONOR / "Art/Textures/RUSU-47mainskin_D.tga",
        r"Art\Textures\RUSU-47mainskin_E.tga": ART_DONOR / "Art/Textures/RUSU-47mainskin_E.tga",
        r"Art\Textures\RUSU47MAP.dds": ART_DONOR / "Art/Textures/RUSU47MAP.dds",
        r"Art\Textures\LSFT50.dds": ART_DONOR / "Art/Textures/LSFT50.dds",
        r"Art\Textures\LSFT50d.dds": ART_DONOR / "Art/Textures/LSFT50d.dds",
        r"Art\Textures\LSFT50k.dds": ART_DONOR / "Art/Textures/LSFT50k.dds",
    }
    art_ops = {}
    for name, path in art_src.items():
        art_ops[name] = upsert(art_entries, name, path.read_bytes())

    data_bytes = write_big(data_entries)
    art_bytes = write_big(art_entries)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_bytes)
    out_art.write_bytes(art_bytes)

    # validate packed commandset
    val = read_big(out_data)
    by = {n.replace("/", "\\").lower(): b for n, b in val}
    cs = by[r"data\ini\commandset.ini"].decode("latin1")
    m = re.search(r"CommandSet Russia_LargeAirBaseCommandSet\n(.*?)(?:\nEnd)", cs, re.S)
    assert m, "large commandset missing after pack"
    block = m.group(0)
    assert "Command_ConstructRussiaJetSu47Berkut" in block
    assert "Command_ConstructRussiaJetSu57T50" in block
    assert "Command_ConstructRussiaJetSu75Checkmate" in block
    assert "Command_ConstructRussiaJetSu35S" in block
    heavy = re.search(r"CommandSet Russia_HeavyAirBaseCommandSet\n(.*?)(?:\nEnd)", cs, re.S).group(0)
    assert "Su47Berkut" not in heavy and "Su57T50" not in heavy
    # other factions unchanged vs source commandset for Nato_Large
    src_cs = dict((n.replace("/", "\\").lower(), b) for n, b in read_big(DATA_SRC))[r"data\ini\commandset.ini"]
    src_text = src_cs.decode("latin1")
    for name in [
        "Nato_LargeAirBaseCommandSet",
        "America_LargeAirBaseCommandSet",
        "China_LargeAirBaseCommandSet",
        "IranExpandedAirfieldCommandSet",
        "Russia_HeavyAirBaseCommandSet",
    ]:
        def grab(t, n=name):
            mm = re.search(rf"CommandSet {n}\n(.*?)(?:\nEnd)", t, re.S)
            return mm.group(0) if mm else None
        if grab(src_text) != grab(cs):
            raise SystemExit(f"faction commandset changed unexpectedly: {name}")

    data_sha = hashlib.sha256(data_bytes).hexdigest()
    art_sha = hashlib.sha256(art_bytes).hexdigest()
    zpath = OUT / "RUSSIA_SU47_T50_SU75.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()

    report = OUT / "PACK_REPORT.txt"
    report.write_text(
        f"DATA SHA256={data_sha} SIZE={len(data_bytes)}\n"
        f"ART  SHA256={art_sha} SIZE={len(art_bytes)}\n"
        f"ZIP  SHA256={zip_sha} SIZE={zpath.stat().st_size}\n"
        f"DATA ops={data_ops}\n"
        f"ART ops={art_ops}\n"
        f"Large menu now includes Su-75 (existing) + Su-47 Berkut + Su-57 T-50\n"
        f"Heavy menu unchanged\n",
        encoding="utf-8",
    )
    print(report.read_text())
    print("ZIP", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
