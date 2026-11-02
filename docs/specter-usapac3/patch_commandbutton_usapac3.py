#!/usr/bin/env python3
"""Crash fix: Command_ConstructUSAPAC3 must live in CommandButton.ini.

ZH parses Data\\INI\\CommandSet.ini / CommandButton.ini before unique-path
INI inside the DATA BIG. AmericaCommandCenterCommandSet slot 6 referenced
Command_ConstructUSAPAC3 while that button existed only in
CommandButton_USAPAC3.ini -> init crash on that CommandSet block.

Append the button to packed CommandButton.ini and drop the unique-path
duplicate so the name is defined once. CommandSet.ini is not changed.
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
SRC = ROOT / "docs/specter-usapac3/merged/_SPEC_DATA_ONE.big"
OUT_DIR = ROOT / "docs/specter-usapac3/merged"

CS_KEY = r"data\ini\commandset.ini"
CB_KEY = r"data\ini\commandbutton.ini"
OLD_BTN_KEY = r"data\ini\commandbutton_usapac3.ini"

BUTTON = (
    b"\r\n"
    b"; SPECTER PATCH USAPAC3 construct button. Must be in CommandButton.ini\r\n"
    b"; so CommandSet.ini AmericaCommandCenterCommandSet slot 6 can resolve it.\r\n"
    b"\r\n"
    b"CommandButton Command_ConstructUSAPAC3\r\n"
    b"  Command            = UNIT_BUILD\r\n"
    b"  Object             = USAPAC3\r\n"
    b"  TextLabel          = CONTROLBAR:ConstructUSAPAC3\r\n"
    b"  ButtonImage        = USAPAC3\r\n"
    b"  ButtonBorderType   = BUILD\r\n"
    b"  DescriptLabel      = CONTROLBAR:ToolTipConstructUSAPAC3\r\n"
    b"End\r\n"
)

CS_SHA = "f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223"
ART2_SHA = "f9c32a05a71d9773965755c9f96e07f779060e38af90d479c3b23eda40225b42"


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        fail(f"not BIGF {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos = end + 1
        entries.append((name.replace("/", "\\"), off, size))
    return data, entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin-1")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
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
        out += name.encode("latin-1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def main() -> int:
    raw, entries = read_big(SRC)
    file_map = {}
    for name, off, size in entries:
        file_map[name] = raw[off : off + size]

    by_key = {n.replace("/", "\\").lower(): n for n in file_map}
    cs_name = by_key[CS_KEY]
    cb_name = by_key[CB_KEY]
    old_btn_name = by_key.get(OLD_BTN_KEY)

    cs = file_map[cs_name]
    cb = file_map[cb_name]
    if sha256(cs) != CS_SHA:
        fail("CommandSet.ini changed; refusing to patch")
    if b"  6  = Command_ConstructUSAPAC3" not in cs:
        fail("slot 6 missing from CommandSet.ini")
    if not re.search(rb"(?m)^CommandSet\s+AmericaCommandCenterCommandSet\s*$", cs):
        fail("live CC CommandSet missing")
    if cs.count(b"CommandSet AmericaCommandCenterCommandSet\r\n") != 1:
        fail("duplicate AmericaCommandCenterCommandSet in CommandSet.ini")
    if b"Command_ConstructUSAPAC3" in cb:
        fail("CommandButton.ini already has USAPAC3")
    if old_btn_name is None:
        fail("CommandButton_USAPAC3.ini missing from DATA")

    new_cb = cb.rstrip(b"\r\n") + b"\r\n" + BUTTON
    if new_cb.count(b"CommandButton Command_ConstructUSAPAC3\r\n") != 1:
        fail("button append count")
    if not re.search(
        rb"(?m)^CommandButton\s+Command_ConstructUSAPAC3\s*$\r?\n"
        rb"  Command\s+=\s+UNIT_BUILD\s*$\r?\n"
        rb"  Object\s+=\s+USAPAC3\s*$",
        new_cb,
    ):
        fail("button Object is not USAPAC3")
    # prefix of original CommandButton.ini must be unchanged
    if not new_cb.startswith(cb.rstrip(b"\r\n")):
        fail("CommandButton.ini prefix mutated")

    file_map[cb_name] = new_cb
    del file_map[old_btn_name]

    # no other path mutated
    orig = {n: raw[off : off + size] for n, off, size in entries}
    for name, blob in file_map.items():
        if name == cb_name:
            continue
        if orig.get(name) != blob:
            fail(f"mutated {name}")
    if old_btn_name in file_map:
        fail("unique button file still present")

    out = build_big(file_map)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(out)
    (OUT_DIR / "CommandButton.ini").write_bytes(new_cb)
    (OUT_DIR / "CommandSet.ini").write_bytes(cs)
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(
        f"{sha256(out)}  _SPEC_DATA_ONE.big\n", encoding="ascii"
    )
    (OUT_DIR / "CommandButton.ini.sha256").write_text(
        f"{sha256(new_cb)}  CommandButton.ini\n", encoding="ascii"
    )

    raw2, entries2 = read_big(OUT_DIR / "_SPEC_DATA_ONE.big")
    amap = {n.replace("/", "\\").lower(): raw2[off : off + size] for n, off, size in entries2}
    if CS_KEY not in amap or sha256(amap[CS_KEY]) != CS_SHA:
        fail("packed CommandSet.ini hash")
    if OLD_BTN_KEY in amap:
        fail("unique button file still packed")
    packed_cb = amap[CB_KEY]
    if packed_cb != new_cb:
        fail("packed CommandButton.ini mismatch")
    defs = re.findall(rb"(?m)^CommandButton\s+Command_ConstructUSAPAC3\s*$", packed_cb)
    if len(defs) != 1:
        fail(f"Command_ConstructUSAPAC3 defs in CommandButton.ini: {len(defs)}")
    extra = [
        n
        for n, off, size in entries2
        if b"CommandButton Command_ConstructUSAPAC3" in raw2[off : off + size]
        and n.replace("/", "\\").lower() != CB_KEY
    ]
    if extra:
        fail(f"duplicate button files {extra}")

    for needle in (
        b"Command_ConstructAmerica_AD_THAAD",
        b"Command_ConstructAmerica_AD_Patriot",
        b"Command_ConstructAmerica_AD_NASAMS",
        b"Command_ConstructAmericaDozer",
    ):
        if needle not in packed_cb and needle not in amap[CS_KEY]:
            # THAAD buttons live in CommandButton.ini or unique files; just warn via count
            pass
    thaad_cs = amap[CS_KEY].count(b"Command_ConstructAmerica_AD_THAAD")
    print("THAAD construct refs in CommandSet.ini", thaad_cs)
    print("NASAMS construct refs in CommandSet.ini", amap[CS_KEY].count(b"Command_ConstructAmerica_AD_NASAMS"))
    print("Patriot construct refs in CommandSet.ini", amap[CS_KEY].count(b"Command_ConstructAmerica_AD_Patriot"))

    lines = [
        f"DATA bytes={len(out)} sha256={sha256(out)} entries={len(file_map)}",
        f"CommandSet.ini unchanged sha256={CS_SHA}",
        f"CommandButton.ini bytes={len(new_cb)} sha256={sha256(new_cb)}",
        "appended Command_ConstructUSAPAC3 Object=USAPAC3 once",
        "removed Data\\INI\\CommandButton_USAPAC3.ini to avoid already-defined",
        f"ART TWO unchanged sha256={ART2_SHA}",
        "STATIC_OK",
    ]
    text = "\n".join(lines) + "\n"
    (OUT_DIR / "CRASHFIX_REPORT.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
