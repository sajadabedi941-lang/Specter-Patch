#!/usr/bin/env python3
"""Rename the playable NATO faction's visible country name to Spain.

Patches packed Data\\English\\generals.csf so FactionNato's DisplayName,
in-game SIDE name, and country-selection bio/tooltip show Spanish Armed
Forces (English CSF convention, matching British/French/Italian Armed
Forces). Internal Side=Nato, FactionNato, objects, and ART are unchanged.

Writes first-wins overlay 0_SPECTER_NatoSpainDisplay.big containing only
the patched CSF. Win32BIGFileSystem overwrite=FALSE: 0_* registers before
_SPEC_DATA_ONE.big, so this named CSF wins at game start.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA = Path(
    "/tmp/sp_work/SPECTER FINAL (GeneralsMode.com)/_SPEC_DATA_ONE.big"
)
DEFAULT_OUT = Path(
    "/workspace/patch/tools/installer/0_SPECTER_NatoSpainDisplay.big"
)
DEFAULT_MANIFEST = Path(
    "/workspace/patch/tools/installer/NATO_SPAIN_DISPLAY_MANIFEST.json"
)

CSF_NAME = "Data\\English\\generals.csf"

# English CSF only in packed DATA. Peer convention is "X Armed Forces".
# Object kit already lives under Data\\INI\\Object\\Specter\\Spanish Armed Forces\\.
SPAIN_NAME = "Spanish Armed Forces"

REPLACEMENTS = {
    "INI:FactionNatoForces": (
        "NATO Armies",
        SPAIN_NAME,
    ),
    "SIDE:Nato": (
        "Nato Armies",
        SPAIN_NAME,
    ),
    "GUI:BioFeatures_Nato": (
        "all of europe armies in one, backed by USA\n\n\n "
        "Manpower : 1.800.000\n Budget      : 200B$\n",
        "Spanish Armed Forces\n\n\n "
        "Manpower : 1.800.000\n Budget      : 200B$\n",
    ),
    "TOOLTIP:BioStrategyLong_Nato": (
        "High Tech Weapons, AIR,LAND,SEA",
        "Spanish Armed Forces - High Tech Weapons, AIR,LAND,SEA",
    ),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
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


def parse_csf(blob: bytes) -> tuple[bytes, list[tuple[str, str]]]:
    if blob[:4] != b" FSC":
        raise ValueError("Not a CSF file")
    nlabels = struct.unpack_from("<I", blob, 8)[0]
    pos = 24
    recs: list[tuple[str, str]] = []
    for _ in range(nlabels):
        magic = blob[pos : pos + 4]
        pos += 4
        if magic != b" LBL":
            raise ValueError(f"expected LBL, got {magic!r}")
        nstr, llen = struct.unpack_from("<II", blob, pos)
        pos += 8
        label = blob[pos : pos + llen].decode("ascii", errors="replace")
        pos += llen
        text = ""
        for _s in range(nstr):
            sm = blob[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", blob, pos)[0]
            pos += 4
            raw = blob[pos : pos + slen * 2]
            pos += slen * 2
            text = bytes(b ^ 0xFF for b in raw).decode("utf-16-le", errors="replace")
            if sm == b"WRTS":
                elen = struct.unpack_from("<I", blob, pos)[0]
                pos += 4
                pos += elen
            elif sm not in (b" RTS",):
                raise ValueError(f"unknown CSF string magic {sm!r} on {label}")
        recs.append((label, text))
    if pos != len(blob):
        raise ValueError(f"CSF trailing bytes: pos={pos} size={len(blob)}")
    return blob[:24], recs


def write_csf(recs: list[tuple[str, str]]) -> bytes:
    out = bytearray()
    out += b" FSC"
    out += struct.pack("<IIIII", 3, len(recs), len(recs), 0, 0)
    for label, text in recs:
        raw = bytes(b ^ 0xFF for b in text.encode("utf-16-le"))
        chars = len(raw) // 2
        out += b" LBL"
        out += struct.pack("<II", 1, len(label))
        out += label.encode("ascii")
        out += b" RTS"
        out += struct.pack("<I", chars)
        out += raw
    return bytes(out)


def extract_csf(entries, raw) -> bytes:
    for name, off, size in entries:
        if name.replace("/", "\\").lower() == CSF_NAME.lower():
            return raw[off : off + size]
    raise SystemExit(f"{CSF_NAME} missing from DATA BIG")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-big", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = ap.parse_args()

    entries, raw = read_big(args.data_big)
    csf = extract_csf(entries, raw)
    header, recs = parse_csf(csf)
    by_label = {label: text for label, text in recs}
    changed = []
    for label, (old, new) in REPLACEMENTS.items():
        if label not in by_label:
            raise SystemExit(f"missing CSF label {label}")
        current = by_label[label]
        if current not in (old, new):
            raise SystemExit(
                f"{label}: unexpected current value {current!r} "
                f"(wanted {old!r} or already {new!r})"
            )
        if current != new:
            changed.append(
                {"label": label, "from": current, "to": new}
            )
            by_label[label] = new

    patched = [(label, by_label[label]) for label, _ in recs]
    # Unchanged labels must round-trip.
    for label, text in recs:
        if label not in REPLACEMENTS and by_label[label] != text:
            raise SystemExit(f"non-target label mutated: {label}")

    csf_out = write_csf(patched)
    _, verify = parse_csf(csf_out)
    verify_map = dict(verify)
    for label, (old, new) in REPLACEMENTS.items():
        if verify_map[label] != new:
            raise SystemExit(f"verify failed for {label}: {verify_map[label]!r}")
    if len(verify) != len(recs):
        raise SystemExit("label count changed")

    overlay = build_big({CSF_NAME: csf_out})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(overlay)

    ov_entries, ov_raw = read_big(args.out)
    ov_files = [n.replace("/", "\\") for n, _, _ in ov_entries]
    if ov_files != [CSF_NAME]:
        raise SystemExit(f"overlay contents unexpected: {ov_files}")

    manifest = {
        "overlay": args.out.name,
        "overlay_sha256": sha256_bytes(overlay),
        "overlay_bytes": len(overlay),
        "source_data_big": str(args.data_big),
        "source_data_sha256": sha256_bytes(raw),
        "csf_path": CSF_NAME,
        "csf_labels": len(recs),
        "display_name": SPAIN_NAME,
        "language_convention": (
            "Packed DATA ships English generals.csf only. "
            "Peer country names use 'X Armed Forces' "
            "(British/French/Italian). España is not used because there is "
            "no Spanish-language CSF pack."
        ),
        "internal_ids_preserved": [
            "PlayerTemplate FactionNato",
            "Side = Nato",
            "BaseSide = Nato",
            "DisplayName = INI:FactionNatoForces (key unchanged)",
            "Nato* objects, CommandSets, sciences, weapons",
        ],
        "identity_art": {
            "FlagWaterMark": "WatermarkUSA (unchanged; no WatermarkSpain / ES_Flag)",
            "EnabledImage": "SSObserverUSA (unchanged; no SSObserverSpain)",
            "LoadScreenImage": "SAFactionLogoPage_US (unchanged; no Spain load page)",
            "SideIconImage": "GameinfoAMRCA (unchanged; no GameinfoSpain)",
            "NT_Flag.tga": "present in ART but unused by PlayerTemplate",
        },
        "changed": changed,
        "already_applied": [
            {"label": label, "value": new}
            for label, (old, new) in REPLACEMENTS.items()
            if label not in {c["label"] for c in changed}
        ],
        "intentionally_retained_nato_country_names": [
            {
                "label": "GUI:BioNameEntry_Pos5",
                "value": by_label.get("GUI:BioNameEntry_Pos5"),
                "reason": "Challenge Laser General bio slot, not FactionNato",
            },
            {
                "label": "SIDE:AmericaLaserGeneral",
                "value": by_label.get("SIDE:AmericaLaserGeneral"),
                "reason": "USA Laser General side string, not FactionNato",
            },
            {
                "label": "SIDE:AmericaSuperWeaponGeneral",
                "value": by_label.get("SIDE:AmericaSuperWeaponGeneral"),
                "reason": "USA SuperWeapon General side string, not FactionNato",
            },
            {
                "label": "INI:FactionAmericaSuperWeaponGeneral",
                "value": by_label.get("INI:FactionAmericaSuperWeaponGeneral"),
                "reason": "USA SuperWeapon General display name, not FactionNato",
            },
        ],
        "load_order_note": (
            "Win32BIGFileSystem overwrite=FALSE; first registered duplicate "
            "internal path wins. 0_SPECTER_NatoSpainDisplay.big sorts before "
            "_SPEC_DATA_ONE.big and INIZH.big, so this CSF is used from new-game "
            "faction selection onward. Internal identifiers are unchanged."
        ),
    }
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {args.out} ({len(overlay)} bytes) sha256={manifest['overlay_sha256']}")
    print(f"changed {len(changed)} CSF labels; {len(recs)} total labels preserved")
    for item in changed:
        print(f"  {item['label']}: {item['from']!r} -> {item['to']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
