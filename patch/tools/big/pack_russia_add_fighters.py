#!/usr/bin/env python3
"""Add-only packer: Su-47 Berkut + Su-57 T-50 on the PR #385 DATA/ART baseline.

Exact previous successful method:
  - new standalone object INIs
  - extra CommandButton_*.ini (does not replace stock CommandButton.ini)
  - extra English strings + CSF append
  - donor W3D/textures only
  - surgical add of empty Large Air Base slots 11-12 (no reorder of 1-10/13-14)

Does not modify existing aircraft objects, Weapon.ini, CommandButton.ini,
Russia_System.ini, Su-35S, Ka-52, Su-75, or other factions.
Su-75 Checkmate is already on the #385 Large Air Base and is left untouched.
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
OUT = Path("/tmp/russia_add_fighters")

OLD_LARGE = (
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
NEW_LARGE = (
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

FROZEN = (
    r"data\ini\commandbutton.ini",
    r"data\ini\weapon.ini",
    r"data\ini\upgrade.ini",
    r"data\ini\object\specter\armed forces of russian federation\russia_system.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su35s.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\ka52m.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su57_aa.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su35s_ts.ini",
)


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
    if OLD_LARGE not in text:
        raise SystemExit("Russia_LargeAirBaseCommandSet baseline block not found — abort")
    if text.count(OLD_LARGE) != 1:
        raise SystemExit("Large Air Base block matched more than once — abort")
    patched = text.replace(OLD_LARGE, NEW_LARGE, 1)
    if patched.replace(NEW_LARGE, OLD_LARGE, 1) != text:
        raise SystemExit("CommandSet rewrite was not a pure slot 11-12 add")
    return patched.encode("latin1")


def csf_encode_u16(s: str) -> bytes:
    raw = s.encode("utf-16-le")
    return bytes((~b) & 0xFF for b in raw)


def csf_append(blob: bytes, pairs: dict[str, str]) -> bytes:
    if blob[:4] != b" FSC":
        raise SystemExit(f"unexpected CSF magic {blob[:4]!r}")
    ver, nlab, nstr, unk, lang = struct.unpack_from("<IIIII", blob, 4)
    p = 24
    existing = set()
    for _ in range(nlab):
        tag = blob[p : p + 4]
        p += 4
        if tag != b" LBL":
            raise SystemExit(f"bad label tag {tag!r}")
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


def grab_cs(text: str, name: str) -> str | None:
    m = re.search(rf"CommandSet {re.escape(name)}\n(.*?)(?:\nEnd)", text, re.S)
    return m.group(0) if m else None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    data_entries = read_big(DATA_SRC)
    art_entries = read_big(ART_SRC)
    data_ops: dict[str, str] = {}
    art_ops: dict[str, str] = {}

    new_data = {
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su47Berkut.ini": (
            PATCH / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/Su47Berkut.ini"
        ),
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su57T50.ini": (
            PATCH / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/Su57T50.ini"
        ),
        r"Data\INI\CommandButton_RussiaSu47T50.ini": PATCH / "Data/INI/CommandButton_RussiaSu47T50.ini",
        r"Data\English\SPECTER_RUSSIA_SU47_T50_Strings.txt": PATCH
        / "Data/English/SPECTER_RUSSIA_SU47_T50_Strings.txt",
    }
    for name, path in new_data.items():
        data_ops[name] = upsert(data_entries, name, path.read_bytes())
        if data_ops[name] != "added":
            raise SystemExit(f"expected new DATA file, already existed: {name}")

    cs_name = cs_raw = None
    for n, b in data_entries:
        if n.replace("/", "\\").lower() == r"data\ini\commandset.ini":
            cs_name, cs_raw = n, b
            break
    if cs_raw is None:
        raise SystemExit("CommandSet.ini missing")
    upsert(data_entries, cs_name, patch_commandset(cs_raw))
    data_ops["CommandSet.ini"] = "added-slots-11-12-only"

    strings = {
        "OBJECT:RussiaSu47Berkut": "Su-47 Berkut",
        "CONTROLBAR:ConstructRussiaJetSu47Berkut": "Su-47 Berkut",
        "CONTROLBAR:ToolTipRussiaJetSu47Berkut": (
            "Build Su-47 Berkut air-superiority fighter (R-77 / R-73 / KAB-500)"
        ),
        "OBJECT:RussiaSu57T50": "Su-57 T-50 PAK FA",
        "CONTROLBAR:ConstructRussiaJetSu57T50": "Su-57 T-50 PAK FA",
        "CONTROLBAR:ToolTipRussiaJetSu57T50": (
            "Build Su-57 T-50 PAK FA multirole fighter (K-77M / R-73 / KAB-500)"
        ),
    }
    for n, b in data_entries:
        if n.replace("/", "\\").lower() == r"data\english\generals.csf":
            upsert(data_entries, n, csf_append(b, strings))
            data_ops["generals.csf"] = "appended-new-labels"
            break
    else:
        raise SystemExit("generals.csf missing")

    art_src = {
        r"Art\W3D\RUSU-47.W3D": PATCH / "Art/W3D/RUSU-47.W3D",
        r"Art\W3D\RUSU-47_D.W3D": PATCH / "Art/W3D/RUSU-47_D.W3D",
        r"Art\W3D\RUSU-47_E.W3D": PATCH / "Art/W3D/RUSU-47_E.W3D",
        r"Art\W3D\LSFT50.W3D": PATCH / "Art/W3D/LSFT50.W3D",
        r"Art\W3D\LSFT50d.W3D": PATCH / "Art/W3D/LSFT50d.W3D",
        r"Art\W3D\LSFT50k.W3D": PATCH / "Art/W3D/LSFT50k.W3D",
        r"Art\Textures\RUSU-47mainskin.tga": PATCH / "Art/Textures/RUSU-47mainskin.tga",
        r"Art\Textures\RUSU-47mainskin_D.tga": PATCH / "Art/Textures/RUSU-47mainskin_D.tga",
        r"Art\Textures\RUSU-47mainskin_E.tga": PATCH / "Art/Textures/RUSU-47mainskin_E.tga",
        r"Art\Textures\RUSU47MAP.dds": PATCH / "Art/Textures/RUSU47MAP.dds",
        r"Art\Textures\LSFT50.dds": PATCH / "Art/Textures/LSFT50.dds",
        r"Art\Textures\LSFT50d.dds": PATCH / "Art/Textures/LSFT50d.dds",
        r"Art\Textures\LSFT50k.dds": PATCH / "Art/Textures/LSFT50k.dds",
    }
    for name, path in art_src.items():
        art_ops[name] = upsert(art_entries, name, path.read_bytes())

    data_bytes = write_big(data_entries)
    art_bytes = write_big(art_entries)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_bytes)
    out_art.write_bytes(art_bytes)

    src_data = {n.replace("/", "\\").lower(): b for n, b in read_big(DATA_SRC)}
    new_data_map = {n.replace("/", "\\").lower(): b for n, b in read_big(out_data)}
    allowed = {
        r"data\ini\commandset.ini",
        r"data\english\generals.csf",
        r"data\ini\object\specter\armed forces of russian federation\airforce\su47berkut.ini",
        r"data\ini\object\specter\armed forces of russian federation\airforce\su57t50.ini",
        r"data\ini\commandbutton_russiasu47t50.ini",
        r"data\english\specter_russia_su47_t50_strings.txt",
    }
    unexpected = [k for k in new_data_map if k not in allowed and src_data.get(k) != new_data_map[k]]
    if unexpected:
        raise SystemExit(f"existing DATA changed: {unexpected[:20]}")
    for key in FROZEN:
        if src_data[key] != new_data_map[key]:
            raise SystemExit(f"frozen existing file changed: {key}")
    if any("su75checkmate.ini" in k for k in new_data_map):
        raise SystemExit("must not add a second Su-75 object file")

    src_cs = src_data[r"data\ini\commandset.ini"].decode("latin1")
    new_cs = new_data_map[r"data\ini\commandset.ini"].decode("latin1")
    if grab_cs(new_cs, "Russia_LargeAirBaseCommandSet") != NEW_LARGE.replace("\nEnd", "\nEnd"):
        # tolerate CRLF in grab; compare via replace check already done
        pass
    if OLD_LARGE not in src_cs or NEW_LARGE not in new_cs:
        raise SystemExit("Large Air Base slot add failed")
    for name in (
        "Nato_LargeAirBaseCommandSet",
        "America_LargeAirBaseCommandSet",
        "China_LargeAirBaseCommandSet",
        "Russia_HeavyAirBaseCommandSet",
        "RussiaAirfieldCommandSet",
    ):
        if grab_cs(src_cs, name) != grab_cs(new_cs, name):
            raise SystemExit(f"existing menu changed: {name}")

    # existing Su-75 object still present and unchanged
    sys_src = src_data[r"data\ini\object\specter\armed forces of russian federation\russia_system.ini"]
    sys_new = new_data_map[r"data\ini\object\specter\armed forces of russian federation\russia_system.ini"]
    if sys_src != sys_new:
        raise SystemExit("Russia_System.ini changed")
    if b"Object RussiaJetSu75Checkmate" not in sys_new:
        raise SystemExit("existing Su-75 missing")

    data_sha = hashlib.sha256(data_bytes).hexdigest()
    art_sha = hashlib.sha256(art_bytes).hexdigest()
    zpath = OUT / "RUSSIA_ADD_SU47_T50.zip"
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
        f"Baseline: PR #385 pack. Added Su-47 Berkut + Su-57 T-50 only.\n"
        f"Existing Su-75 / Su-35S / Ka-52 / menus 1-10+13-14 untouched.\n",
        encoding="utf-8",
    )
    print(report.read_text())
    print("ZIP", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
