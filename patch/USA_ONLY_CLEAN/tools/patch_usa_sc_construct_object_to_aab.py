#!/usr/bin/env python3
"""Patch ONLY USA stock SC construct buttons' Object= to America_AdvancedAirBase inside a DATA BIG.

Does not modify CommandSet.ini, Art, Draw, or Geometry.
Does not touch AirF_/Lazr_/SupW_ Strategy Center buttons.
"""
from __future__ import annotations
import argparse, re, struct, hashlib
from pathlib import Path

BUTTONS = (
    "Command_ConstructAmericaStrategyCenter_T",
    "Command_ConstructAmericaStrategyCenter",
)

def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"not BIGF: {path}")
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(n):
        off = struct.unpack(">I", data[pos:pos+4])[0]
        sz = struct.unpack(">I", data[pos+4:pos+8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, off, sz))
    return data, entries

def build_big(file_map: dict[str, bytes]) -> bytes:
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

def patch_button(text: str, button_name: str, new_object: str) -> str:
    pat = re.compile(rf"(CommandButton\s+{re.escape(button_name)}\s*\r?\n)(.*?)(\r?\nEnd)", re.S)
    m = pat.search(text)
    if not m:
        raise SystemExit(f"missing button {button_name}")
    head, body, end = m.group(1), m.group(2), m.group(3)
    body2, n = re.subn(r"(?m)^(\s*Object\s*=\s*)\S+", rf"\g<1>{new_object}", body, count=1)
    if n != 1:
        raise SystemExit(f"Object not patched in {button_name}")
    return text[: m.start()] + head + body2 + end + text[m.end() :]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    args = ap.parse_args()
    raw, entries = read_big(args.data_big)
    file_map = {name: raw[off:off+sz] for name, off, sz in entries}
    cb_key = next(k for k in file_map if k.replace("/", "\\").lower() == "data\\ini\\commandbutton.ini")
    cs_key = next(k for k in file_map if k.replace("/", "\\").lower() == "data\\ini\\commandset.ini")
    cs_before = file_map[cs_key]
    text = file_map[cb_key].decode("latin1")
    for bn in BUTTONS:
        text = patch_button(text, bn, "America_AdvancedAirBase")
    file_map[cb_key] = text.encode("latin1")
    assert file_map[cs_key] == cs_before, "CommandSet.ini must remain untouched"
    out = build_big(file_map)
    args.out_big.parent.mkdir(parents=True, exist_ok=True)
    args.out_big.write_bytes(out)
    print(hashlib.sha256(out).hexdigest(), args.out_big, len(out))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
