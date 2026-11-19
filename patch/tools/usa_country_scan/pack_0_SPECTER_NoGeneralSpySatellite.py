#!/usr/bin/env python3
"""Patch 0_SPECTER_NoGeneralSpySatellite.big in place for SS2 USA Country Scan.

Do not ship a helper z_ BIG. The Country Scan overlay already owns the CC
module and the two defs, but SS2 loose SpecialPower.ini / ObjectCreationList.ini
shadow those exact archive paths. Stock game.dat still loads unique files
under Data\\INI\\Object via TheThingFactory directory glob.

This script copies every existing member byte-for-byte from the original 0_
BIG and adds one unused Object path containing the America-only defs already
present in that same BIG's SpecialPower.ini / ObjectCreationList.ini.
"""
from __future__ import annotations

import argparse
import hashlib
import struct
import zipfile
from pathlib import Path


NEW_MEMBER = r"Data\INI\Object\zzzz_SPECTER_AmericaCountryScanDefs.ini"

HEADER = (
    b"; SPECTER Object-glob. ThingFactory loads Data\\INI\\Object\\ "
    b"(stock game.dat dirpath).\r\n"
    b"; Bodies copied from this same BIG's SpecialPower.ini / ObjectCreationList.ini.\r\n"
    b"; Required on SS2 because loose SpecialPower.ini / ObjectCreationList.ini "
    b"shadow those exact paths.\r\n"
)


def iter_big_members(data: bytes):
    if data[:4] != b"BIGF":
        raise SystemExit("not BIGF")
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    for _ in range(nfiles):
        foff, fsize = struct.unpack(">II", data[off : off + 8])
        off += 8
        end = data.find(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        yield name, data[foff : foff + fsize]


def extract_named(file_map: dict[str, bytes], want: str) -> bytes:
    want_l = want.replace("\\", "/").lower()
    for name, blob in file_map.items():
        if name.replace("\\", "/").lower() == want_l:
            return blob
    raise SystemExit(f"missing {want}")


def slice_named_block(blob: bytes, header: bytes) -> bytes:
    start = blob.find(header)
    if start < 0:
        raise SystemExit(f"header not found: {header!r}")
    nl = b"\r\n" if b"\r\n" in blob[start : start + len(header) + 8] else b"\n"
    nxt_sp = blob.find(nl + b"SpecialPower ", start + len(header))
    nxt_ocl = blob.find(nl + b"ObjectCreationList ", start + len(header))
    ends = [i for i in (nxt_sp, nxt_ocl) if i >= 0]
    if ends:
        return blob[start : min(ends) + len(nl)]
    end_tag = nl + b"End" + nl
    last = blob.rfind(end_tag, start)
    if last < 0:
        raise SystemExit("block End not found")
    return blob[start : last + len(end_tag)]


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
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
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--source-big",
        type=Path,
        default=Path(
            "/tmp/ss2/SPECTER FINAL (GeneralsMode.com)/0_SPECTER_NoGeneralSpySatellite.big"
        ),
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("patch/Release/SPECTER_USA_COUNTRY_SCAN"),
    )
    args = ap.parse_args()

    original = args.source_big.read_bytes()
    file_map = {name: blob for name, blob in iter_big_members(original)}
    if NEW_MEMBER in file_map or NEW_MEMBER.lower() in {k.lower() for k in file_map}:
        raise SystemExit(f"{NEW_MEMBER} already present")

    sp = extract_named(file_map, "Data/INI/SpecialPower.ini")
    ocl = extract_named(file_map, "Data/INI/ObjectCreationList.ini")
    sp_block = slice_named_block(sp, b"SpecialPower SpecialPowerAmericaCountryScan")
    ocl_block = slice_named_block(ocl, b"ObjectCreationList SUPERWEAPON_AmericaCountryScan")
    if b"Israel" in sp_block or b"Israel" in ocl_block:
        raise SystemExit("refused: Israel leaked into America-only extract")
    if b"AmericaCommandCenter" in sp_block or b"AmericaCommandCenter" in ocl_block:
        raise SystemExit("refused: AmericaCommandCenter leaked into defs extract")

    body = HEADER + sp_block
    if not body.endswith(b"\r\n"):
        body += b"\r\n"
    body += b"\r\n" + ocl_block
    if not body.endswith(b"\r\n"):
        body += b"\r\n"
    file_map[NEW_MEMBER] = body

    big = build_big(file_map)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    big_path = out_dir / "0_SPECTER_NoGeneralSpySatellite.big"
    big_path.write_bytes(big)
    big_sha = hashlib.sha256(big).hexdigest()
    (out_dir / "0_SPECTER_NoGeneralSpySatellite.big.sha256").write_text(
        f"{big_sha}  0_SPECTER_NoGeneralSpySatellite.big\n"
    )

    zip_path = out_dir / "SPECTER_USA_COUNTRY_SCAN.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(big_path, arcname="0_SPECTER_NoGeneralSpySatellite.big")
    zip_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (out_dir / "SPECTER_USA_COUNTRY_SCAN.zip.sha256").write_text(
        f"{zip_sha}  SPECTER_USA_COUNTRY_SCAN.zip\n"
    )

    rebuilt = {name: blob for name, blob in iter_big_members(big)}
    for name, blob in {n: b for n, b in iter_big_members(original)}.items():
        if rebuilt.get(name) != blob:
            raise SystemExit(f"original member changed: {name}")
    if NEW_MEMBER not in rebuilt:
        raise SystemExit("new member missing after rebuild")

    print(f"source_sha256={hashlib.sha256(original).hexdigest()}")
    print(f"member={NEW_MEMBER} bytes={len(body)}")
    print(f"big={big_path} members={len(rebuilt)} bytes={len(big)} sha256={big_sha}")
    print(f"zip={zip_path} bytes={zip_path.stat().st_size} sha256={zip_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
