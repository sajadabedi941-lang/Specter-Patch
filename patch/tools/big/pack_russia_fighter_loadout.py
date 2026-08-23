#!/usr/bin/env python3
"""Finalize Su-47 / T-50 loadouts on the PR #386 fighter DATA pack.

Isolation rules (stable launch first):
  - Do not edit stock/global CommandSet.ini, CommandButton.ini, Weapon.ini,
    Upgrade.ini, or packed Russia_System.ini.
  - New aircraft live in isolated overlay object files.
  - New buttons live in CommandButton_RussiaSu47T50.ini (already in #386).
  - Do not redefine Russia_LargeAirBaseCommandSet. ZH replaces a CommandSet
    wholesale, so a partial override would wipe slots 1-10.
  - Su-75 stays on the packed #386 object. Changing it requires editing
    Russia_System.ini (multi-object global) or a duplicate Object overlay.

This packer only:
  - updates overlay Su47Berkut.ini / Su57T50.ini
  - refreshes extra English strings + CSF tooltips we already own
  - copies ART bytes unchanged from the #386 fighter pack
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

DATA_SRC = Path("/tmp/russia_su47_t50/_SPEC_DATA_ONE.big")
ART_SRC = Path("/tmp/russia_su47_t50/_SPEC_ART_ONE.big")
PATCH = Path("/workspace/patch")
OUT = Path("/tmp/russia_fighter_loadout")

SU47_OVERLAY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su47Berkut.ini"
)
SU57_OVERLAY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su57T50.ini"
)
STRINGS = r"Data\English\SPECTER_RUSSIA_SU47_T50_Strings.txt"
RUSSIA_SYSTEM = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Russia_System.ini"
)

STOCK_GLOBAL = (
    r"data\ini\commandset.ini",
    r"data\ini\commandbutton.ini",
    r"data\ini\weapon.ini",
    r"data\ini\upgrade.ini",
    r"data\ini\armor.ini",
    r"data\ini\locomotor.ini",
    RUSSIA_SYSTEM.replace("/", "\\").lower(),
)

LOCK_RE = re.compile(
    r"\b(Prerequisites|START_LOCK|SCIENCE_Rank|NeededUpgrade)\b", re.I
)
USA_WEAPON_RE = re.compile(
    r"\b(AASM250kg|GBU-|GBU_|Mk82|Spice250|AIM-120|AIM120|AGM-65|AGM65|JSOW|JDAM)\b"
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


def by_name(entries):
    return {n.replace("/", "\\").lower(): (n, b) for n, b in entries}


def csf_decode_u16(buf: bytes) -> str:
    return bytes((~b) & 0xFF for b in buf).decode("utf-16-le", errors="replace")


def csf_encode_u16(s: str) -> bytes:
    raw = s.encode("utf-16-le")
    return bytes((~b) & 0xFF for b in raw)


def csf_upsert(blob: bytes, pairs: dict[str, str]) -> bytes:
    if blob[:4] != b" FSC":
        raise SystemExit(f"unexpected CSF magic {blob[:4]!r}")
    ver, nlab, nstr, unk, lang = struct.unpack_from("<IIIII", blob, 4)
    p = 24
    labels = []
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
        strs = []
        for _j in range(nsl):
            stag = blob[p : p + 4]
            p += 4
            slen = struct.unpack_from("<I", blob, p)[0]
            p += 4
            raw = blob[p : p + slen * 2]
            p += slen * 2
            extra = None
            if stag == b"WRTS":
                elen = struct.unpack_from("<I", blob, p)[0]
                p += 4
                extra = blob[p : p + elen]
                p += elen
            strs.append((stag, csf_decode_u16(raw), extra))
        labels.append((key, strs))
    if p != len(blob):
        raise SystemExit(f"CSF parse leftover {len(blob) - p} bytes")

    wanted = {k.upper(): (k, v) for k, v in pairs.items()}
    seen = set()
    out_labels = []
    for key, strs in labels:
        uk = key.upper()
        if uk in wanted:
            seen.add(uk)
            new_val = wanted[uk][1]
            if strs:
                stag, _old, extra = strs[0]
                strs = [(stag, new_val, extra)] + strs[1:]
            else:
                strs = [(b" RTS", new_val, None)]
        out_labels.append((key, strs))
    for uk, (key, val) in wanted.items():
        if uk in seen:
            continue
        out_labels.append((key, [(b" RTS", val, None)]))

    out = bytearray()
    out += b" FSC"
    nstr_new = sum(len(s) for _, s in out_labels)
    out += struct.pack("<IIIII", ver, len(out_labels), nstr_new, unk, lang)
    for key, strs in out_labels:
        out += b" LBL"
        out += struct.pack("<I", len(strs))
        kb = key.encode("ascii")
        out += struct.pack("<I", len(kb))
        out += kb
        for stag, val, extra in strs:
            enc = csf_encode_u16(val)
            if extra is not None:
                out += b"WRTS"
                out += struct.pack("<I", len(enc) // 2)
                out += enc
                out += struct.pack("<I", len(extra))
                out += extra
            else:
                out += b" RTS"
                out += struct.pack("<I", len(enc) // 2)
                out += enc
    return bytes(out)


def weapon_names(ini_text: str) -> set[str]:
    return set(
        re.findall(
            r"^\s*Weapon\s+=\s+(?:PRIMARY|SECONDARY|TERTIARY)\s+(\S+)",
            ini_text,
            re.M,
        )
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    src_entries = read_big(DATA_SRC)
    data_entries = list(src_entries)
    src_by = by_name(src_entries)
    data_ops: dict[str, str] = {}

    overlays = {
        SU47_OVERLAY: PATCH
        / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/Su47Berkut.ini",
        SU57_OVERLAY: PATCH
        / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/Su57T50.ini",
        STRINGS: PATCH / "Data/English/SPECTER_RUSSIA_SU47_T50_Strings.txt",
    }
    for name, path in overlays.items():
        data_ops[name] = upsert(data_entries, name, path.read_bytes())

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
    csf_name, csf_raw = src_by[r"data\english\generals.csf"]
    upsert(data_entries, csf_name, csf_upsert(csf_raw, strings))
    data_ops["generals.csf"] = "upsert-owned-tooltips"

    data_bytes = write_big(data_entries)
    art_bytes = ART_SRC.read_bytes()
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_bytes)
    out_art.write_bytes(art_bytes)

    packed = read_big(out_data)
    by = by_name(packed)
    src_map = {k: v[1] for k, v in src_by.items()}
    new_map = {k: v[1] for k, v in by.items()}

    allowed_changed = {
        SU47_OVERLAY.replace("/", "\\").lower(),
        SU57_OVERLAY.replace("/", "\\").lower(),
        STRINGS.replace("/", "\\").lower(),
        r"data\english\generals.csf",
    }
    unexpected = [k for k in new_map if k not in allowed_changed and src_map.get(k) != new_map[k]]
    if unexpected:
        raise SystemExit(f"unexpected DATA changes: {unexpected[:20]}")
    extra = sorted(set(new_map) - set(src_map))
    if extra:
        raise SystemExit(f"unexpected added DATA files: {extra}")

    for frozen in STOCK_GLOBAL + (r"data\ini\commandbutton_russiasu47t50.ini",):
        if src_map[frozen] != new_map[frozen]:
            raise SystemExit(f"stock/global file changed: {frozen}")

    # #386 airbase menu must remain byte-identical
    if src_map[r"data\ini\commandset.ini"] != new_map[r"data\ini\commandset.ini"]:
        raise SystemExit("CommandSet.ini changed; #386 baseline must stay frozen")
    cs = new_map[r"data\ini\commandset.ini"].decode("latin1")
    m = re.search(r"CommandSet Russia_LargeAirBaseCommandSet\n(.*?)(?:\nEnd)", cs, re.S)
    if not m:
        raise SystemExit("large commandset missing")
    block = m.group(0)
    for btn in (
        "Command_ConstructRussiaJetSu75Checkmate",
        "Command_ConstructRussiaJetSu47Berkut",
        "Command_ConstructRussiaJetSu57T50",
        "Command_ConstructRussiaJetSu35S",
    ):
        if btn not in block:
            raise SystemExit(f"missing large-airbase button {btn}")

    # packed Su-75 must still live in Russia_System.ini (no extract / no duplicate)
    sys_txt = new_map[RUSSIA_SYSTEM.replace("/", "\\").lower()].decode("latin1")
    if sys_txt.count("Object RussiaJetSu75Checkmate") != 1:
        raise SystemExit("Su-75 object count in Russia_System.ini is not 1")
    if "Object RussiaJetSu47Recon" not in sys_txt:
        raise SystemExit("Su-47 Recon missing from Russia_System.ini")
    su75_overlay = (
        r"data\ini\object\specter\armed forces of russian federation\airforce\su75checkmate.ini"
    )
    if su75_overlay in new_map:
        raise SystemExit("Su75Checkmate.ini must not be packed (duplicate Object risk)")

    checks = {
        SU47_OVERLAY.replace("/", "\\").lower(): {
            "cost": "BuildCost           = 2800",
            "time": "BuildTime           = 20.0",
            "weapons": {
                "6x_R77_MRBVR_SU35S",
                "R73_HOBS_SRAAM_SU35",
                "Kab500_LeaserGuidedBomb",
            },
        },
        SU57_OVERLAY.replace("/", "\\").lower(): {
            "cost": "BuildCost           = 3900",
            "time": "BuildTime           = 24.0",
            "weapons": {
                "6x_MRAAM_K77M_SU57",
                "R73_HOBS_SRAAM_SU35",
                "Kab500_LeaserGuidedBomb",
            },
        },
    }
    for key, expect in checks.items():
        text = new_map[key].decode("latin1")
        if expect["cost"] not in text or expect["time"] not in text:
            raise SystemExit(f"cost/time changed: {key}")
        if LOCK_RE.search(text):
            raise SystemExit(f"lock token found in {key}")
        if USA_WEAPON_RE.search(text):
            raise SystemExit(f"USA/NATO weapon imported in {key}")
        if "Kab2500" in text:
            raise SystemExit(f"bomber-class KAB-2500 still present in {key}")
        got = weapon_names(text)
        if got != expect["weapons"]:
            raise SystemExit(f"weapon mismatch in {key}: {got}")

    # packed Su-75 loadout stays on the #386 baseline (K-77M only)
    su75 = re.search(
        r"Object RussiaJetSu75Checkmate\r\n.*?^End\r\n", sys_txt, re.M | re.S
    )
    if not su75:
        raise SystemExit("Su-75 block missing")
    if weapon_names(su75.group(0)) != {"6x_MRAAM_K77M_SU57"}:
        raise SystemExit(f"Su-75 packed weapons drifted: {weapon_names(su75.group(0))}")
    if "BuildCost           = 3500" not in su75.group(0):
        raise SystemExit("Su-75 cost drifted")

    data_sha = hashlib.sha256(data_bytes).hexdigest()
    art_sha = hashlib.sha256(art_bytes).hexdigest()
    src_art_sha = hashlib.sha256(ART_SRC.read_bytes()).hexdigest()
    if art_sha != src_art_sha:
        raise SystemExit("ART was rewritten; this pack must keep previous ART bytes")

    zpath = OUT / "RUSSIA_FIGHTER_LOADOUT.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()

    report = OUT / "PACK_REPORT.txt"
    report.write_text(
        f"DATA SHA256={data_sha} SIZE={len(data_bytes)}\n"
        f"ART  SHA256={art_sha} SIZE={len(art_bytes)} (unchanged from #386)\n"
        f"ZIP  SHA256={zip_sha} SIZE={zpath.stat().st_size}\n"
        f"DATA ops={data_ops}\n"
        f"Su-47 overlay: R-77 + R-73 + KAB-500\n"
        f"T-50 overlay: K-77M + R-73 + KAB-500\n"
        f"Su-75 packed #386 baseline unchanged (no Russia_System.ini edit)\n"
        f"CommandSet.ini / CommandButton.ini / Russia_System.ini frozen\n",
        encoding="utf-8",
    )
    print(report.read_text())
    print("ZIP", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
