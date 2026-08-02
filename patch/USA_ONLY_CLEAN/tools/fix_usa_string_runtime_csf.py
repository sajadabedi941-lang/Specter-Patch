#!/usr/bin/env python3
"""Fix Specter USA String Manager runtime failure.

ROOT CAUSE (verified by binary CSF parse):
  Data/English/generals.csf in USA packs was corrupt. At labels such as
  INI:FactionTurkey the string magic was written as ASCII 'RTSW' instead of
  little-endian STRW ('WRTS') / STR (' RTS'). String Manager then fails with:
    ***FATAL*** String Manager failed to initialize properly

SECONDARY RISK:
  Data/English/*.txt overlays next to generals.csf are not CSF. Working packs
  ship CSF only under English/. USA strings belong inside generals.csf.

THIS SCRIPT:
  - Takes USA DATA big (aircraft content preserved)
  - Replaces generals.csf with a known-good CSF + appended USA OBJECT/CONTROLBAR keys
  - Removes Data/English/*.txt
  - Does NOT delete USA aircraft / AdvancedAirBase INIs
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path


def read_big(path: Path):
    data = path.read_bytes()
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    m = {}
    for _ in range(n):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        sz = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        m[name] = data[off : off + sz]
        pos = end + 1
    return m


def build_big(file_map: dict) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index, blobs, offset = [], [], header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for b in blobs:
        out += b
    return bytes(out)


def parse_csf(data: bytes) -> dict:
    ver, nlab, nstr, unused, lang = struct.unpack_from("<IIIII", data, 4)
    pos = 24
    labels = {}
    for i in range(nlab):
        if data[pos : pos + 4] != b" LBL":
            return {"ok": False, "at": i, "pos": pos, "parsed": len(labels)}
        pos += 4
        (ns,) = struct.unpack_from("<I", data, pos)
        pos += 4
        (nl,) = struct.unpack_from("<I", data, pos)
        pos += 4
        name = data[pos : pos + nl].decode("latin1", "replace")
        pos += nl
        vals = []
        for _ in range(ns):
            sm = data[pos : pos + 4]
            pos += 4
            (slen,) = struct.unpack_from("<I", data, pos)
            pos += 4
            if sm not in (b" RTS", b"WRTS"):
                return {"ok": False, "at": i, "name": name, "sm": sm}
            raw = data[pos : pos + slen * 2]
            pos += slen * 2
            text = bytes((~b) & 0xFF for b in raw).decode("utf-16-le", "replace")
            vals.append(text)
            if pos < len(data) and data[pos : pos + 4] not in (b" LBL", b" RTS", b"WRTS"):
                (elen,) = struct.unpack_from("<I", data, pos)
                pos += 4
                pos += elen
        labels[name] = vals
    return {
        "ok": True,
        "labels": labels,
        "nlab": nlab,
        "nstr": nstr,
        "remain": len(data) - pos,
        "ver": ver,
        "lang": lang,
        "unused": unused,
    }


def encode_u16_inv(s: str) -> bytes:
    return bytes((~b) & 0xFF for b in s.encode("utf-16-le"))


def append_labels(csf: bytes, new_labels: dict[str, str]) -> bytes:
    info = parse_csf(csf)
    if not info["ok"]:
        raise ValueError(f"base CSF invalid: {info}")
    existing = info["labels"]
    ver, nlab, nstr, unused, lang = struct.unpack_from("<IIIII", csf, 4)
    add = bytearray()
    added = 0
    for key, val in sorted(new_labels.items()):
        if key in existing:
            continue
        name = key.encode("latin1", errors="replace")
        payload = encode_u16_inv(val)
        chars = len(payload) // 2
        add += b" LBL"
        add += struct.pack("<I", 1)
        add += struct.pack("<I", len(name))
        add += name
        add += b" RTS"
        add += struct.pack("<I", chars)
        add += payload
        added += 1
    out = bytearray(b" FSC")
    out += struct.pack("<IIIII", ver, nlab + added, nstr + added, unused, lang)
    out += csf[24:]
    out += add
    return bytes(out)


def load_usa_strings(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="ascii").splitlines():
        s = line.strip()
        if not s or s.startswith(";") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-big", type=Path, required=True)
    ap.add_argument("--good-csf-big", type=Path, required=True, help="BIG containing valid generals.csf")
    ap.add_argument("--usa-strings", type=Path, required=True, help="ASCII KEY = VALUE list")
    ap.add_argument("--out-big", type=Path, required=True)
    args = ap.parse_args()

    data = read_big(args.data_big)
    good = read_big(args.good_csf_big)
    csf_key = [k for k in data if k.lower().endswith("generals.csf")][0]
    good_key = [k for k in good if k.lower().endswith("generals.csf")][0]
    before = parse_csf(data[csf_key])
    print("input CSF ok=", before.get("ok"), "detail=", {k: before[k] for k in before if k != "labels"})

    usa = load_usa_strings(args.usa_strings)
    new_csf = append_labels(good[good_key], usa)
    after = parse_csf(new_csf)
    if not after["ok"] or after["remain"] != 0:
        raise SystemExit(f"merged CSF invalid: {after}")
    print("merged CSF ok labels=", after["nlab"], "usa_keys=", len(usa))

    data[csf_key] = new_csf
    removed = []
    for k in list(data):
        low = k.lower().replace("/", "\\")
        if low.startswith("data\\english\\") and low.endswith(".txt"):
            removed.append(k)
            del data[k]
    print("removed English txt:", removed)

    args.out_big.parent.mkdir(parents=True, exist_ok=True)
    args.out_big.write_bytes(build_big(data))
    print("wrote", args.out_big)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
