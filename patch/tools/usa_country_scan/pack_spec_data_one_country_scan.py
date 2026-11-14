#!/usr/bin/env python3
"""Add America Country Scan defs to SS2 _SPEC_DATA_ONE.big.

Inserts Data\\INI\\Object\\zzzy_SPECTER_AmericaCountryScanDefs.ini, which sorts
before zzzz_SPECTER_CountryScans.ini so SpecialPower/OCL pointers bind at parse.
Existing members are copied byte-for-byte and keep their original index order.
"""
from __future__ import annotations

import argparse
import hashlib
import struct
import zipfile
from pathlib import Path

NEW_MEMBER = r"Data\INI\Object\zzzy_SPECTER_AmericaCountryScanDefs.ini"
COUNTRY_SCANS = r"Data\INI\Object\zzzz_SPECTER_CountryScans.ini"

HEADER = (
    b"; SPECTER Object-glob. ThingFactory loads Data\\INI\\Object\\ before "
    b"zzzz_SPECTER_CountryScans.ini.\r\n"
    b"; Bodies copied from 0_SPECTER_NoGeneralSpySatellite.big.\r\n"
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


def build_big_ordered(items: list[tuple[str, bytes]]) -> bytes:
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
        "--data-big",
        type=Path,
        default=Path("/tmp/ss2/SPECTER FINAL (GeneralsMode.com)/_SPEC_DATA_ONE.big"),
    )
    ap.add_argument(
        "--source-overlay",
        type=Path,
        default=Path(
            "/tmp/ss2/SPECTER FINAL (GeneralsMode.com)/0_SPECTER_NoGeneralSpySatellite.big"
        ),
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("patch/Release/SPECTER_SS2_USA_COUNTRY_SCAN_FIX"),
    )
    args = ap.parse_args()

    original = args.data_big.read_bytes()
    items = list(iter_big_members(original))
    orig_map = {name: blob for name, blob in items}
    orig_n = len(items)
    if any(name.replace("\\", "/").lower() == NEW_MEMBER.replace("\\", "/").lower() for name, _ in items):
        raise SystemExit(f"{NEW_MEMBER} already present")

    if not (NEW_MEMBER.lower() < COUNTRY_SCANS.lower()):
        raise SystemExit("load-order guarantee failed: zzzy_ must sort before zzzz_CountryScans")

    overlay = {name: blob for name, blob in iter_big_members(args.source_overlay.read_bytes())}
    sp = extract_named(overlay, "Data/INI/SpecialPower.ini")
    ocl = extract_named(overlay, "Data/INI/ObjectCreationList.ini")
    sp_block = slice_named_block(sp, b"SpecialPower SpecialPowerAmericaCountryScan")
    ocl_block = slice_named_block(ocl, b"ObjectCreationList SUPERWEAPON_AmericaCountryScan")
    if b"Israel" in sp_block or b"Israel" in ocl_block:
        raise SystemExit("refused: Israel leaked into America-only extract")
    if b"AmericaCommandCenter" in sp_block or b"AmericaCommandCenter" in ocl_block:
        raise SystemExit("refused: AmericaCommandCenter leaked into defs extract")
    if b"AmericaCountryScanPing" not in ocl_block:
        raise SystemExit("OCL missing AmericaCountryScanPing")

    ping_src = None
    country = orig_map.get(COUNTRY_SCANS)
    if country is None:
        country = overlay.get(COUNTRY_SCANS)
        ping_src = "0_ overlay"
    else:
        ping_src = "DATA BIG"
    if country is None or b"Object AmericaCountryScanPing" not in country:
        # SS2 DATA does not contain CountryScans; ping lives in overlay/loose
        overlay_cs = overlay.get(COUNTRY_SCANS) or overlay.get(
            r"Data\INI\Object\zzzz_SPECTER_CountryScans.ini"
        )
        if overlay_cs is None or b"Object AmericaCountryScanPing" not in overlay_cs:
            raise SystemExit("AmericaCountryScanPing object not found")
        ping_src = "0_ overlay CountryScans.ini"

    body = HEADER + sp_block
    if not body.endswith(b"\r\n"):
        body += b"\r\n"
    body += b"\r\n" + ocl_block
    if not body.endswith(b"\r\n"):
        body += b"\r\n"

    items.append((NEW_MEMBER, body))
    big = build_big_ordered(items)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    big_path = out_dir / "_SPEC_DATA_ONE.big"
    big_path.write_bytes(big)
    big_sha = hashlib.sha256(big).hexdigest()
    (out_dir / "_SPEC_DATA_ONE.big.sha256").write_text(f"{big_sha}  _SPEC_DATA_ONE.big\n")

    zip_path = out_dir / "SPECTER_SS2_USA_COUNTRY_SCAN_FIX.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(big_path, arcname="_SPEC_DATA_ONE.big")
    zip_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (out_dir / "SPECTER_SS2_USA_COUNTRY_SCAN_FIX.zip.sha256").write_text(
        f"{zip_sha}  SPECTER_SS2_USA_COUNTRY_SCAN_FIX.zip\n"
    )

    rebuilt = list(iter_big_members(big))
    rebuilt_map = {name: blob for name, blob in rebuilt}
    if len(rebuilt) != orig_n + 1:
        raise SystemExit(f"member count {len(rebuilt)} != {orig_n}+1")
    for name, blob in orig_map.items():
        if rebuilt_map.get(name) != blob:
            raise SystemExit(f"original member changed: {name}")
    if rebuilt[-1][0] != NEW_MEMBER:
        raise SystemExit("new member was not appended")

    print(f"source_data_sha256={hashlib.sha256(original).hexdigest()}")
    print(f"orig_members={orig_n} new_members={len(rebuilt)}")
    print(f"ping_object={ping_src}")
    print(f"sort_before_countryscans={NEW_MEMBER.lower() < COUNTRY_SCANS.lower()}")
    print(f"member={NEW_MEMBER} bytes={len(body)}")
    print(f"big={big_path} bytes={len(big)} sha256={big_sha}")
    print(f"zip={zip_path} bytes={zip_path.stat().st_size} sha256={zip_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
