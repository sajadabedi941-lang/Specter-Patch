#!/usr/bin/env python3
"""Finalize Su-47 / T-50 / Su-75 loadouts on the current fighter DATA pack.

Surgical DATA only:
  - replace overlay Su47Berkut.ini / Su57T50.ini
  - add overlay Su75Checkmate.ini
  - strip Object RussiaJetSu75Checkmate from packed Russia_System.ini
    (prevents duplicate Object; other objects in that file stay byte-identical)
  - refresh extra English strings + CSF tooltips we already own

Does not touch CommandSet.ini, CommandButton.ini, costs, other factions, or ART.
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

SU75_PACKED = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Russia_System.ini"
)
SU75_OVERLAY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su75Checkmate.ini"
)
SU47_OVERLAY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su47Berkut.ini"
)
SU57_OVERLAY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su57T50.ini"
)
STRINGS = r"Data\English\SPECTER_RUSSIA_SU47_T50_Strings.txt"

SU75_STUB = (
    "; RussiaJetSu75Checkmate moved to Airforce/Su75Checkmate.ini "
    "(fighter loadout finalization)\r\n"
)

LOCK_RE = re.compile(
    r"\b(Prerequisites|START_LOCK|SCIENCE_Rank|NeededUpgrade)\b", re.I
)
USA_WEAPON_RE = re.compile(
    r"\b(AASM250kg|GBU-|GBU_|Mk82|Spice250|AIM-120|AIM120|AGM-65|AGM65|JSOW|JDAM)\b"
)
RU_WEAPONS_OK = {
    "6x_R77_MRBVR_SU35S",
    "R73_HOBS_SRAAM_SU35",
    "Kab500_LeaserGuidedBomb",
    "6x_MRAAM_K77M_SU57",
    "Kab500_LeaserGuidedBomb_Mig29k",
}


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


def strip_su75_from_russia_system(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    m = re.search(r"Object RussiaJetSu75Checkmate\r\n.*?^End\r\n", text, re.M | re.S)
    if not m:
        raise SystemExit("RussiaJetSu75Checkmate block not found in packed Russia_System.ini")
    if text.count("Object RussiaJetSu75Checkmate") != 1:
        raise SystemExit("unexpected extra Su-75 object markers")
    # keep neighboring objects intact
    before = text[: m.start()]
    after = text[m.end() :]
    if "Object RussiaJetSu47Recon" not in after:
        raise SystemExit("Su-47 Recon missing after Su-75 strip — abort")
    if "Object RUSSU75X_RussiaSystemK77MTargetLock" not in after:
        raise SystemExit("Su-75 K77M lock dummy missing after strip — abort")
    patched = before + SU75_STUB + after
    # only the Su-75 object may change
    if patched.replace(SU75_STUB, m.group(0), 1) != text:
        raise SystemExit("Russia_System.ini rewrite was not a pure Su-75 swap")
    return patched.encode("latin1")


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
    added = 0
    for uk, (key, val) in wanted.items():
        if uk in seen:
            continue
        out_labels.append((key, [(b" RTS", val, None)]))
        added += 1

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
        SU75_OVERLAY: PATCH
        / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/Su75Checkmate.ini",
        STRINGS: PATCH / "Data/English/SPECTER_RUSSIA_SU47_T50_Strings.txt",
    }
    for name, path in overlays.items():
        data_ops[name] = upsert(data_entries, name, path.read_bytes())

    sys_name, sys_raw = src_by[SU75_PACKED.replace("/", "\\").lower()]
    sys_new = strip_su75_from_russia_system(sys_raw)
    upsert(data_entries, sys_name, sys_new)
    data_ops[SU75_PACKED] = "stripped-su75-object-only"

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

    # --- pack ---
    data_bytes = write_big(data_entries)
    art_bytes = ART_SRC.read_bytes()
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_bytes)
    out_art.write_bytes(art_bytes)

    # --- validate ---
    packed = read_big(out_data)
    by = by_name(packed)
    src_map = {k: v[1] for k, v in src_by.items()}
    new_map = {k: v[1] for k, v in by.items()}

    allowed_changed = {
        SU47_OVERLAY.replace("/", "\\").lower(),
        SU57_OVERLAY.replace("/", "\\").lower(),
        SU75_OVERLAY.replace("/", "\\").lower(),
        STRINGS.replace("/", "\\").lower(),
        SU75_PACKED.replace("/", "\\").lower(),
        r"data\english\generals.csf",
    }
    unexpected = []
    for key, blob in new_map.items():
        if key in allowed_changed:
            continue
        if src_map.get(key) != blob:
            unexpected.append(key)
    if unexpected:
        raise SystemExit(f"unexpected DATA changes: {unexpected[:20]}")

    # CommandSet / CommandButton frozen vs previous fighter pack
    for frozen in (
        r"data\ini\commandset.ini",
        r"data\ini\commandbutton.ini",
        r"data\ini\commandbutton_russiasu47t50.ini",
        r"data\ini\weapon.ini",
        r"data\ini\upgrade.ini",
    ):
        if src_map[frozen] != new_map[frozen]:
            raise SystemExit(f"frozen file changed: {frozen}")

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

    # loadout objects
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
        SU75_OVERLAY.replace("/", "\\").lower(): {
            "cost": "BuildCost           = 3500",
            "time": "BuildTime           = 55.0",
            "weapons": {
                "6x_MRAAM_K77M_SU57",
                "R73_HOBS_SRAAM_SU35",
                "Kab500_LeaserGuidedBomb_Mig29k",
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

    # packed Russia_System.ini must no longer define the jet
    sys_txt = new_map[SU75_PACKED.replace("/", "\\").lower()].decode("latin1")
    if "Object RussiaJetSu75Checkmate" in sys_txt:
        raise SystemExit("Su-75 still defined in packed Russia_System.ini")
    if "Object RussiaJetSu47Recon" not in sys_txt:
        raise SystemExit("Su-47 Recon missing from Russia_System.ini")

    # other Russian aircraft files unchanged
    for key, blob in new_map.items():
        if key in allowed_changed:
            continue
        if "armed forces of russian federation" in key and src_map.get(key) != blob:
            raise SystemExit(f"other Russia file changed: {key}")

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
        f"ART  SHA256={art_sha} SIZE={len(art_bytes)} (unchanged from fighter baseline)\n"
        f"ZIP  SHA256={zip_sha} SIZE={zpath.stat().st_size}\n"
        f"DATA ops={data_ops}\n"
        f"Su-47: R-77 + R-73 + KAB-500\n"
        f"T-50: K-77M + R-73 + KAB-500 (removed KAB-2500OD)\n"
        f"Su-75: K-77M + R-73 + light KAB-500; model still RUS_SU57 (no Su-75 W3D)\n"
        f"CommandSet.ini / CommandButton.ini / costs / other factions frozen\n",
        encoding="utf-8",
    )
    print(report.read_text())
    print("ZIP", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
