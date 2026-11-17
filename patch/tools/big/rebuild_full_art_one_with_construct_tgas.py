#!/usr/bin/env python3
"""Rebuild full SPE ART ONE, replacing only accepted construct-button TGAs.

Source ART ONE is the unmodified SPE archive (2144972013 bytes / 2094699 KiB).
The 447MB split ART ONE is not the reference file and is not used as the base.
Only Art\\Textures\\specbtn_*.tga and Button_GlobalMarket.tga are replaced
with the 128x128 32-bit TGA blobs from the accepted construct-button pack.
ART TWO is not modified.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

REPLACE = {
    r"Art\Textures\Button_GlobalMarket.tga",
    r"Art\Textures\specbtn_heron.tga",
    r"Art\Textures\specbtn_mic_92n6r.tga",
    r"Art\Textures\specbtn_mic_96l6tsp.tga",
    r"Art\Textures\specbtn_mic_arrow.tga",
    r"Art\Textures\specbtn_mic_hq9.tga",
    r"Art\Textures\specbtn_mic_ht233.tga",
    r"Art\Textures\specbtn_mic_irist.tga",
    r"Art\Textures\specbtn_mic_krasukha.tga",
    r"Art\Textures\specbtn_mic_pantsir.tga",
    r"Art\Textures\specbtn_mic_s400.tga",
    r"Art\Textures\specbtn_mic_s500.tga",
    r"Art\Textures\specbtn_mic_thaad.tga",
    r"Art\Textures\specbtn_mic_tpy2.tga",
    r"Art\Textures\specbtn_mic_trml4d.tga",
    r"Art\Textures\specbtn_mic_ustpy2.tga",
    r"Art\Textures\specbtn_mq4.tga",
    r"Art\Textures\specbtn_orlan10.tga",
    r"Art\Textures\specbtn_shahedlnchr.tga",
}


def parse_index(path: Path) -> tuple[list[tuple[str, int, int]], int]:
    with path.open("rb") as f:
        hdr = f.read(16)
        if hdr[:4] != b"BIGF":
            raise ValueError(f"Not BIGF: {path}")
        count = struct.unpack(">I", hdr[8:12])[0]
        header_size = struct.unpack(">I", hdr[12:16])[0]
        idx = f.read(header_size - 16)
    pos = 0
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", idx[pos : pos + 8])
        pos += 8
        end = idx.index(b"\x00", pos)
        name = idx[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, off, size))
    return entries, header_size


def load_named(path: Path, wanted: set[str]) -> dict[str, bytes]:
    entries, _ = parse_index(path)
    out: dict[str, bytes] = {}
    with path.open("rb") as f:
        for name, off, size in entries:
            if name in wanted:
                f.seek(off)
                out[name] = f.read(size)
    missing = wanted - set(out)
    if missing:
        raise SystemExit(f"missing in {path}: {sorted(missing)}")
    return out


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    spe = Path("/tmp/art-one-extract/SPECTER FINAL (GeneralsMode.com)/_SPEC_ART_ONE.big")
    donor = Path("patch/Release/CONSTRUCT_BUTTON_IMAGES/_SPEC_ART_ONE.big")
    dst = Path("patch/Release/WORLD_WAR_III2027_FULL/_SPEC_ART_ONE.big")
    dst.parent.mkdir(parents=True, exist_ok=True)

    donor_blobs = load_named(donor, REPLACE)
    spe_entries, _ = parse_index(spe)
    spe_names = {n for n, _, _ in spe_entries}
    if set(REPLACE) - spe_names:
        raise SystemExit(f"SPE ART ONE missing {sorted(set(REPLACE) - spe_names)}")

    # Rebuild using SPE membership/order, lowercase sort (SAGE last-wins by filename).
    items: list[tuple[str, int, int | None, bytes | None]] = []
    # name, spe_off, spe_size, override_bytes
    for name, off, size in spe_entries:
        if name in REPLACE:
            items.append((name, 0, None, donor_blobs[name]))
        else:
            items.append((name, off, size, None))
    items.sort(key=lambda it: it[0].lower())

    header_size = 16
    for name, _, _, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1

    blobs_size = 0
    layout = []
    offset = header_size
    for name, spe_off, spe_size, override in items:
        size = len(override) if override is not None else int(spe_size)
        layout.append((name, offset, size, spe_off, spe_size, override))
        offset += size
        blobs_size += size
    total = header_size + blobs_size
    if total >= 2**32:
        raise SystemExit(f"BIG total {total} exceeds 32-bit BIGF size")

    tmp = dst.with_suffix(".big.tmp")
    with tmp.open("wb") as out, spe.open("rb") as src:
        out.write(b"BIGF")
        out.write(struct.pack(">I", total))
        out.write(struct.pack(">I", len(layout)))
        out.write(struct.pack(">I", header_size))
        for name, off, size, *_ in layout:
            out.write(struct.pack(">II", off, size))
            out.write(name.encode("latin1") + b"\x00")
        if out.tell() != header_size:
            raise SystemExit(f"header mismatch {out.tell()} != {header_size}")
        for name, off, size, spe_off, spe_size, override in layout:
            if override is not None:
                out.write(override)
            else:
                src.seek(spe_off)
                remaining = int(spe_size)
                while remaining:
                    chunk = src.read(min(remaining, 1 << 20))
                    if not chunk:
                        raise SystemExit(f"short read {name}")
                    out.write(chunk)
                    remaining -= len(chunk)
        if out.tell() != total:
            raise SystemExit(f"size mismatch {out.tell()} != {total}")
    tmp.replace(dst)

    digest = sha256_file(dst)
    (dst.parent / "_SPEC_ART_ONE.big.sha256").write_text(digest + "\n", encoding="ascii")
    print(
        {
            "dst": str(dst),
            "size": dst.stat().st_size,
            "sha256": digest,
            "entries": len(layout),
            "replaced": len(REPLACE),
            "spe_size": spe.stat().st_size,
        }
    )


if __name__ == "__main__":
    main()
