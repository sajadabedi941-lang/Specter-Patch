#!/usr/bin/env python3
"""Pack z_SPECTER_AmericaCountryScan.big for SS2 USA Country Scan defs.

SPECTER ships stock ZH game.dat (2005). That binary loads:

  TheSpecialPowerStore:
    Data\\INI\\Default\\SpecialPower.ini
    Data\\INI\\SpecialPower.ini
  TheObjectCreationListStore:
    Data\\INI\\Default\\ObjectCreationList.ini
    Data\\INI\\ObjectCreationList.ini
  TheThingFactory:
    Data\\INI\\Default\\Object.ini
    Data\\INI\\Object          (directory glob, recursive)

SS2 loose SpecialPower.ini / ObjectCreationList.ini equal _SPEC_DATA_ONE
and shadow 0_SPECTER_NoGeneralSpySatellite.big of those exact paths.
A BIG cannot beat those loose files.

ThingFactory's Data\\INI\\Object glob does load unique archive members.
SPECTER already defines top-level ObjectCreationList blocks in Object INIs
(USAPAC3.ini, ABM_FCS.ini). The INI token table is global, so SpecialPower
blocks in the same Object glob are parsed the same way.

This overlay therefore uses one unused Object path, not SpecialPower_*.ini.
"""
from __future__ import annotations

import argparse
import hashlib
import struct
import zipfile
from pathlib import Path


MEMBER = r"Data\INI\Object\zzzz_SPECTER_AmericaCountryScanDefs.ini"

HEADER = (
    b"; SPECTER Object-glob last-win. ThingFactory loads Data\\INI\\Object\\ "
    b"(stock game.dat dirpath).\r\n"
    b"; Bodies copied from 0_SPECTER_NoGeneralSpySatellite.big.\r\n"
    b"; Do not put these defs in Data\\INI\\SpecialPower_*.ini; that path is not loaded.\r\n"
)


def extract_big_member(big_path: Path, want: str) -> bytes:
    data = big_path.read_bytes()
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    want_l = want.replace("\\", "/").lower()
    for _ in range(nfiles):
        foff, fsize = struct.unpack(">II", data[off : off + 8])
        off += 8
        end = data.find(b"\x00", off)
        name = data[off:end].decode("latin1").replace("\\", "/")
        off = end + 1
        if name.lower() == want_l:
            return data[foff : foff + fsize]
    raise SystemExit(f"missing {want} in {big_path}")


def slice_named_block(blob: bytes, header: bytes) -> bytes:
    start = blob.find(header)
    if start < 0:
        raise SystemExit(f"header not found: {header!r}")
    nl = b"\r\n" if b"\r\n" in blob[start : start + len(header) + 8] else b"\n"
    nxt_sp = blob.find(nl + b"SpecialPower ", start + len(header))
    nxt_ocl = blob.find(nl + b"ObjectCreationList ", start + len(header))
    ends = [i for i in (nxt_sp, nxt_ocl) if i >= 0]
    if ends:
        # include the CRLF that terminates this block, before the next header
        end = min(ends) + len(nl)
        return blob[start:end]
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
        default=Path("/tmp/ss2/SPECTER FINAL (GeneralsMode.com)/0_SPECTER_NoGeneralSpySatellite.big"),
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("patch/Release/SPECTER_USA_COUNTRY_SCAN"),
    )
    args = ap.parse_args()

    sp = extract_big_member(args.source_big, "Data/INI/SpecialPower.ini")
    ocl = extract_big_member(args.source_big, "Data/INI/ObjectCreationList.ini")
    sp_block = slice_named_block(sp, b"SpecialPower SpecialPowerAmericaCountryScan")
    ocl_block = slice_named_block(ocl, b"ObjectCreationList SUPERWEAPON_AmericaCountryScan")
    if b"Israel" in sp_block or b"Israel" in ocl_block:
        raise SystemExit("refused: Israel leaked into America-only extract")
    if b"AmericaCommandCenter" in sp_block or b"AmericaCommandCenter" in ocl_block:
        raise SystemExit("refused: AmericaCommandCenter leaked into defs extract")

    body = HEADER + sp_block
    if not body.endswith(b"\r\n"):
        body += b"\r\n"
    body += b"\r\n"
    body += ocl_block
    if not body.endswith(b"\r\n"):
        body += b"\r\n"

    big = build_big({MEMBER: body})
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    big_path = out_dir / "z_SPECTER_AmericaCountryScan.big"
    big_path.write_bytes(big)
    big_sha = hashlib.sha256(big).hexdigest()
    (out_dir / "z_SPECTER_AmericaCountryScan.big.sha256").write_text(
        f"{big_sha}  z_SPECTER_AmericaCountryScan.big\n"
    )

    zip_path = out_dir / "SPECTER_USA_COUNTRY_SCAN.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(big_path, arcname="z_SPECTER_AmericaCountryScan.big")
    zip_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (out_dir / "SPECTER_USA_COUNTRY_SCAN.zip.sha256").write_text(
        f"{zip_sha}  SPECTER_USA_COUNTRY_SCAN.zip\n"
    )

    print(f"member={MEMBER}")
    print(f"big={big_path} bytes={len(big)} sha256={big_sha}")
    print(f"zip={zip_path} bytes={zip_path.stat().st_size} sha256={zip_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
