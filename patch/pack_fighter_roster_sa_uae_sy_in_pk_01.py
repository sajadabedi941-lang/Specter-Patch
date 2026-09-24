#!/usr/bin/env python3
"""Pack-only: validated fighter roster overlays onto the live DATA BIG.

Does not edit Objects/Weapons/CommandSets. Replaces existing packed object
paths with the already-validated INIs and appends the two last-win files.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/CAPTURE_BUILDING_FIX_STAGE_JAPAN_SOUTH_KOREA_VIETNAM/_SPEC_DATA_ONE.big")
EXPECTED_SRC_SHA = "fbe90ff915af2267d90a12532aff281d4a06e0f3a81a25ee07c4c380b50c74bc"
ROOT = Path("/workspace/patch")
INI = ROOT / "Data" / "INI"
RELEASE = ROOT / "Release" / "FIGHTER_ROSTER_SA_UAE_SYRIA_INDIA_PAKISTAN"

# Validated rebound objects (same packed path as live BIG). KEEP objects omitted.
REPLACE = [
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15C.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTyphoon.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15S.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF5E.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTornadoECR.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTornadoIDS.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15EX.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetF15SA.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTyphoonT3.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetLightning.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetHawk65.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetTornadoADV.ini",
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF16E.ini",
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage20005.ini",
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage2000DAD.ini",
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15EA.ini",
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15E.ini",
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF16F.ini",
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF16ECegy.ini",
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage20009.ini",
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetMirage20009E.ini",
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15SA.ini",
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetHawk102.ini",
    r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\Syria_Mig-29A.ini",
    r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig25.ini",
    r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\Syria_MirageF1-Bq.ini",
    r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetSu22.ini",
    r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetSu22M4.ini",
    r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetSu24.ini",
    r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetL39.ini",
    r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig23.ini",
    r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig21.ini",
    r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig21MF.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMig21Bison.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\India_Mig-29A.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetJaguarIS.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMig27.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetSu30MKI.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetRafaleEH.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetRafaleDH.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMirage2000H.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMirage2000I.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetTejas.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetAMCA.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetMig29K.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF16AMLU.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetMirage3.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF7P.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetA5C.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetJ10CE.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetJF17.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetJF17Blk3.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetMirage5.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetMirageROSE.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF16B.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF7PG.ini",
]

APPEND = [
    (r"Data\INI\CommandButton_ZZZZ_FighterRoster_SAUAESYINPK.ini", INI / "CommandButton_ZZZZ_FighterRoster_SAUAESYINPK.ini"),
    (r"Data\INI\CommandSet_ZZZZ_FighterRoster_SAUAESYINPK.ini", INI / "CommandSet_ZZZZ_FighterRoster_SAUAESYINPK.ini"),
]

FROZEN = [
    r"Data\INI\Weapon.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\CommandSet_Pakistan.ini",
    r"Data\INI\CommandSet_ZZZZ_AfricaPakistanSyria_AirExp.ini",
    r"Data\INI\CommandButton_ZZZZ_AfricaPakistanSyria_AirExp.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\F15C.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\F15E_229.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\F16CM_BLK50_AA.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\F16CJ_BLK52.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\J7.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\J10C.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\JF17.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\J16D.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\SU24M2.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su30SM2.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su35S.ini",
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Airforce\UAE_F16Blk52.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\Pakistan_F16Blk52.ini",
    r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetJ7.ini",
    r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\Syria_Su-25K.ini",
    r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\SyriaJetSu30SM2.ini",
    r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\SyriaJetJ16D.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetSu35S.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF15E.ini",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(name: str) -> str:
    return name.replace("/", "\\")


def read_big(path: Path) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def read_big_from_bytes(data: bytes) -> list[tuple[str, bytes]]:
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries, target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 path, got {len(hits)}")
    return hits[0]


def ws_path(packed: str) -> Path:
    rel = packed.replace("\\", "/")
    if rel.lower().startswith("data/ini/"):
        return INI / rel[len("Data/INI/") :]
    raise SystemExit(f"unexpected packed path {packed}")


def main() -> int:
    if sha256_file(SRC_DATA) != EXPECTED_SRC_SHA:
        raise SystemExit("live DATA SHA mismatch")

    entries = read_big(SRC_DATA)
    orig = list(entries)
    orig_map = {norm(n).lower(): (n, b) for n, b in orig}

    replaced = []
    for packed in REPLACE:
        src = ws_path(packed)
        if not src.is_file():
            raise SystemExit(f"missing overlay {src}")
        blob = src.read_bytes()
        # validated files already use CRLF
        idx = find_index(entries, packed)
        old_name, old_blob = entries[idx]
        if blob == old_blob:
            raise SystemExit(f"overlay identical to baseline (not the validated rebind): {packed}")
        entries[idx] = (old_name, blob)
        replaced.append(packed)

    for packed, src in APPEND:
        if any(norm(n).lower() == packed.lower() for n, _ in entries):
            raise SystemExit(f"already packed: {packed}")
        entries.append((packed, src.read_bytes()))

    for p in FROZEN:
        idx = find_index(entries, p)
        if entries[idx][1] != orig_map[norm(p).lower()][1]:
            raise SystemExit(f"frozen path changed: {p}")

    orig_names = [n for n, _ in orig]
    new_names = [n for n, _ in entries]
    if new_names[: len(orig_names)] != orig_names:
        raise SystemExit("packed path order prefix changed")
    added = new_names[len(orig_names) :]
    if [norm(x) for x in added] != [a[0] for a in APPEND]:
        raise SystemExit(f"unexpected added paths: {added}")

    replace_set = {norm(p).lower() for p in REPLACE}
    for n, b in entries[: len(orig)]:
        if norm(n).lower() in replace_set:
            continue
        if b != orig_map[norm(n).lower()][1]:
            raise SystemExit(f"unintended rewrite: {n}")

    data_blob = build_big_ordered(entries)
    rebuilt = read_big_from_bytes(data_blob)
    if [n for n, _ in rebuilt] != new_names:
        raise SystemExit("rebuild order drifted")

    RELEASE.mkdir(parents=True, exist_ok=True)
    out = RELEASE / "_SPEC_DATA_ONE.big"
    out.write_bytes(data_blob)
    sha = sha256_file(out)
    (RELEASE / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {sha}\n"
        f"SOURCE_DATA_SHA {EXPECTED_SRC_SHA}\n"
        f"ART unchanged (not packed)\n"
        f"FILE_COUNT {len(entries)}\n"
        f"BYTES {out.stat().st_size}\n",
        encoding="utf-8",
    )
    (RELEASE / "PACKED_FILES.txt").write_text(
        "REPLACED\n" + "\n".join(f"  {p}" for p in replaced) + "\nAPPENDED\n"
        + "\n".join(f"  {p}" for p, _ in APPEND) + "\nART_CHANGED = NO\n",
        encoding="utf-8",
    )
    print("PACKED", out, out.stat().st_size, sha, "files", len(entries))
    print("REPLACED", len(replaced), "APPENDED", len(APPEND))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
