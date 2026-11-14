#!/usr/bin/env python3
"""SS2: give TurkeyVehicleDozerm America's tank-dozer W3D (Irq_VT72B).

Only member changed: Data\\INI\\Object\\Specter\\Turkish Armed Forces\\Wheleed\\Dozer.ini
TurkeyVehicleDozer is copied byte-for-byte from the original SS2 DATA BIG.
TurkeyVehicleDozerm is taken from the SS2 runtime definition; only Model and
Animation tokens are retargeted to Irq_VT72B. No ART BIG is rewritten because
AmericaVehicleDozer already loads Art\\W3D\\Irq_VT72B.W3D from _SPEC_ART_TWO.big
and T-72_IRQ / iraqi_tanktracks from _SPEC_ART_ONE.big.
"""
from __future__ import annotations

import argparse
import hashlib
import struct
import zipfile
from pathlib import Path

MEMBER = r"Data\INI\Object\Specter\Turkish Armed Forces\Wheleed\Dozer.ini"
USA_DOZER = r"Data\INI\Object\Specter\United States Of America\Wheeled\Dozer.ini"
LOOSE_TURKEY = Path(
    "/tmp/ss2/SPECTER FINAL (GeneralsMode.com)/Data/INI/Object/"
    "Specter/Turkish Armed Forces/Wheleed/Dozer.ini"
)

MODEL_SWAPS = (
    (b"AVCONSTDOZ_A.AVCONSTDOZ_A", b"Irq_VT72B.Irq_VT72B"),
    (b"AVCONSTDOZ_AD.AVCONSTDOZ_AD", b"Irq_VT72B.Irq_VT72B"),
    (b"AVCONSTDOZ_AD", b"Irq_VT72B"),
    (b"AVCONSTDOZ_A", b"Irq_VT72B"),
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


def extract_object(blob: bytes, name: str) -> bytes:
    header = f"Object {name}".encode("ascii")
    start = blob.find(header)
    if start < 0:
        raise SystemExit(f"missing Object {name}")
    nxt = blob.find(b"\nObject ", start + len(header))
    chunk = blob[start:] if nxt < 0 else blob[start:nxt]
    return chunk.rstrip(b"\r\n") + b"\r\n"


def only_model_swaps(block: bytes) -> bytes:
    out = block
    for old, new in MODEL_SWAPS:
        out = out.replace(old, new)
    if b"AVCONSTDOZ" in out:
        raise SystemExit("leftover AVCONSTDOZ after model swap")
    if out.count(b"Irq_VT72B") < 1:
        raise SystemExit("Irq_VT72B was not applied")
    return out


def non_model_lines(block: bytes) -> list[str]:
    lines = []
    for line in block.decode("latin1").splitlines():
        stripped = line.strip()
        if stripped.startswith("Model") or stripped.startswith("Animation"):
            continue
        lines.append(line)
    return lines


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--data-big",
        type=Path,
        default=Path("/tmp/ss2/SPECTER FINAL (GeneralsMode.com)/_SPEC_DATA_ONE.big"),
    )
    ap.add_argument(
        "--loose-turkey",
        type=Path,
        default=LOOSE_TURKEY,
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("patch/Release/SPECTER_SS2_TURKEY_DOZERM_VT72B"),
    )
    args = ap.parse_args()

    original = args.data_big.read_bytes()
    items = list(iter_big_members(original))
    orig_map = {name: blob for name, blob in items}
    if MEMBER not in orig_map:
        raise SystemExit(f"missing {MEMBER}")
    orig_dozer = orig_map[MEMBER]
    orig_turkey = extract_object(orig_dozer, "TurkeyVehicleDozer")
    if b"Object TurkeyVehicleDozerm" in orig_dozer:
        raise SystemExit("original BIG already has TurkeyVehicleDozerm")

    usa = extract_object(orig_map[USA_DOZER], "AmericaVehicleDozer")
    if b"Model             = Irq_VT72B" not in usa:
        raise SystemExit("AmericaVehicleDozer is not the tank W3D Irq_VT72B")

    loose = args.loose_turkey.read_bytes()
    loose_regular = extract_object(loose, "TurkeyVehicleDozer")
    if loose_regular.rstrip(b"\r\n") != orig_turkey.rstrip(b"\r\n"):
        raise SystemExit("loose TurkeyVehicleDozer differs from BIG; refusing to patch")
    dozerm = extract_object(loose, "TurkeyVehicleDozerm")
    patched_dozerm = only_model_swaps(dozerm)
    if non_model_lines(dozerm) != non_model_lines(patched_dozerm):
        raise SystemExit("non-model lines of TurkeyVehicleDozerm changed")

    new_member = orig_turkey.rstrip(b"\r\n") + b"\r\n\r\n" + patched_dozerm
    if extract_object(new_member, "TurkeyVehicleDozer").rstrip(b"\r\n") != orig_turkey.rstrip(
        b"\r\n"
    ):
        raise SystemExit("TurkeyVehicleDozer mutated")

    new_items = []
    changed = 0
    for name, blob in items:
        if name == MEMBER:
            new_items.append((name, new_member))
            changed += 1
        else:
            new_items.append((name, blob))
    if changed != 1:
        raise SystemExit(f"expected 1 changed member, got {changed}")

    rebuilt = build_big_ordered(new_items)
    rebuilt_map = {name: blob for name, blob in iter_big_members(rebuilt)}
    if set(rebuilt_map) != set(orig_map):
        raise SystemExit("member set changed")
    for name, blob in orig_map.items():
        if name == MEMBER:
            continue
        if rebuilt_map[name] != blob:
            raise SystemExit(f"unrelated member mutated: {name}")
    if rebuilt_map[MEMBER] != new_member:
        raise SystemExit("written Dozer.ini mismatch")
    if b"Object TurkeyVehicleDozer\r\n" not in rebuilt_map[MEMBER]:
        raise SystemExit("regular TurkeyVehicleDozer missing after rebuild")
    if b"Object TurkeyVehicleDozerm\r\n" not in rebuilt_map[MEMBER]:
        raise SystemExit("TurkeyVehicleDozerm missing after rebuild")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    big_path = args.out_dir / "_SPEC_DATA_ONE.big"
    big_path.write_bytes(rebuilt)
    zip_path = args.out_dir / "SPECTER_SS2_TURKEY_DOZERM_VT72B.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(big_path, arcname="_SPEC_DATA_ONE.big")
        if zf.namelist() != ["_SPEC_DATA_ONE.big"]:
            raise SystemExit("ZIP must contain only _SPEC_DATA_ONE.big")

    big_sha = sha256_file(big_path)
    zip_sha = sha256_file(zip_path)
    (args.out_dir / "_SPEC_DATA_ONE.big.sha256").write_text(f"{big_sha}  _SPEC_DATA_ONE.big\n")
    (args.out_dir / "SPECTER_SS2_TURKEY_DOZERM_VT72B.zip.sha256").write_text(
        f"{zip_sha}  SPECTER_SS2_TURKEY_DOZERM_VT72B.zip\n"
    )
    report = args.out_dir / "COMPARE.txt"
    report.write_text(
        "SS2 Turkey second dozer 3D swap\n"
        f"Member: {MEMBER}\n"
        "Regular Object TurkeyVehicleDozer: byte-identical to original BIG\n"
        "Second Object TurkeyVehicleDozerm: Model/Animation only -> Irq_VT72B\n"
        "AmericaVehicleDozer destination W3D: Irq_VT72B (already in _SPEC_ART_TWO.big)\n"
        "ART BIGs not modified.\n"
        f"_SPEC_DATA_ONE.big  {big_path.stat().st_size}  {big_sha}\n"
        f"SPECTER_SS2_TURKEY_DOZERM_VT72B.zip  {zip_path.stat().st_size}  {zip_sha}\n"
    )
    print(f"wrote {big_path} {big_path.stat().st_size} {big_sha}")
    print(f"wrote {zip_path} {zip_path.stat().st_size} {zip_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
