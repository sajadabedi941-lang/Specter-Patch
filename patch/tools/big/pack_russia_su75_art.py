#!/usr/bin/env python3
"""ART-only Su-75 Checkmate visual fix on the PR #388 add-fighters pack.

Adds real TEOD RUSU75 W3D + SU-75 textures from patch ART sources.
Retargets ONLY RussiaJetSu75Checkmate Model= lines (required so the new
W3D is used). Does not replace shared RUS_SU57.W3D (Su-57 / Su-57AA / decoy).

Does not touch CommandSet.ini, CommandButton.ini, Weapon.ini, costs, weapons,
or any other aircraft object.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

DATA_SRC = Path("/tmp/russia_add_fighters/_SPEC_DATA_ONE.big")
ART_SRC = Path("/tmp/russia_add_fighters/_SPEC_ART_ONE.big")
PATCH = Path("/workspace/patch")
OUT = Path("/tmp/russia_su75_art")

RUSSIA_SYSTEM = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Russia_System.ini"
)

FROZEN = (
    r"data\ini\commandset.ini",
    r"data\ini\commandbutton.ini",
    r"data\ini\commandbutton_russiasu47t50.ini",
    r"data\ini\weapon.ini",
    r"data\ini\upgrade.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su35s.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\ka52m.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su57.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su57_aa.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su47berkut.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su57t50.ini",
)


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def write_big(entries: list[tuple[str, bytes]]) -> bytes:
    header = 16
    encoded = []
    for name, blob in entries:
        raw = name.replace("/", "\\").encode("latin1")
        encoded.append((raw, blob))
        header += 8 + len(raw) + 1
    offset = header
    out = bytearray()
    total = header + sum(len(b) for _, b in encoded)
    out += b"BIGF"
    out += struct.pack(">I", total)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header)
    for raw, blob in encoded:
        out += struct.pack(">II", offset, len(blob))
        out += raw + b"\x00"
        offset += len(blob)
    for _, blob in encoded:
        out += blob
    return bytes(out)


def upsert(entries: list[tuple[str, bytes]], name: str, content: bytes) -> str:
    key = name.replace("/", "\\").lower()
    for i, (n, _) in enumerate(entries):
        if n.replace("/", "\\").lower() == key:
            entries[i] = (n, content)
            return "updated"
    entries.append((name.replace("/", "\\"), content))
    return "added"


def retarget_su75_models(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    m = re.search(r"Object RussiaJetSu75Checkmate\r\n.*?^End\r\n", text, re.M | re.S)
    if not m:
        raise SystemExit("Su-75 object block not found")
    block = m.group(0)
    if block.count("Model               = RUS_SU57") != 6:
        raise SystemExit(f"unexpected Su-75 Model count: {block.count('Model               = RUS_SU57')}")
    new_block = block
    # default + inherited exhaust
    new_block = new_block.replace(
        "    DefaultConditionState\r\n      Model               = RUS_SU57\r\n",
        "    DefaultConditionState\r\n      Model               = RUSU75\r\n",
        1,
    )
    new_block = new_block.replace(
        "    ConditionState        = REALLYDAMAGED\r\n      Model               = RUS_SU57\r\n",
        "    ConditionState        = REALLYDAMAGED\r\n      Model               = RUSU75_D\r\n",
        1,
    )
    new_block = new_block.replace(
        "    ConditionState        = REALLYDAMAGED JETEXHAUST\r\n      Model               = RUS_SU57\r\n",
        "    ConditionState        = REALLYDAMAGED JETEXHAUST\r\n      Model               = RUSU75_D\r\n",
        1,
    )
    new_block = new_block.replace(
        "    ConditionState        = REALLYDAMAGED JETEXHAUST JETAFTERBURNER\r\n      Model               = RUS_SU57\r\n",
        "    ConditionState        = REALLYDAMAGED JETEXHAUST JETAFTERBURNER\r\n      Model               = RUSU75_D\r\n",
        1,
    )
    new_block = new_block.replace(
        "    ConditionState        = RUBBLE\r\n      Model               = RUS_SU57\r\n",
        "    ConditionState        = RUBBLE\r\n      Model               = RUSU75_E\r\n",
        1,
    )
    new_block = new_block.replace(
        "    ConditionState        = RUBBLE JETEXHAUST JETAFTERBURNER\r\n      Model               = RUS_SU57\r\n",
        "    ConditionState        = RUBBLE JETEXHAUST JETAFTERBURNER\r\n      Model               = RUSU75_E\r\n",
        1,
    )
    if "RUS_SU57" in new_block:
        raise SystemExit("Su-75 still references RUS_SU57")
    if new_block.count("RUSU75") < 3:
        raise SystemExit("Su-75 RUSU75 retarget failed")
    # gameplay fields must stay
    for token in (
        "BuildCost           = 3500",
        "BuildTime           = 55.0",
        "6x_MRAAM_K77M_SU57",
        "CommandSet        = F22A_AA_CommandSet",
        "Object RussiaJetSu75Checkmate",
    ):
        if token not in new_block:
            raise SystemExit(f"gameplay field lost: {token}")
    patched = text[: m.start()] + new_block + text[m.end() :]
    if patched.replace(new_block, block, 1) != text:
        raise SystemExit("Russia_System.ini change was not Su-75-block-only")
    # decoy / other RUS_SU57 must remain
    if patched.count("Model = RUS_SU57") + patched.count("Model               = RUS_SU57") != 1:
        raise SystemExit("shared RUS_SU57 references were disturbed")
    return patched.encode("latin1")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    data_entries = read_big(DATA_SRC)
    art_entries = read_big(ART_SRC)
    data_ops: dict[str, str] = {}
    art_ops: dict[str, str] = {}

    sys_name = None
    sys_raw = None
    for n, b in data_entries:
        if n.replace("/", "\\").lower() == RUSSIA_SYSTEM.replace("/", "\\").lower():
            sys_name, sys_raw = n, b
            break
    if sys_raw is None:
        raise SystemExit("Russia_System.ini missing")
    upsert(data_entries, sys_name, retarget_su75_models(sys_raw))
    data_ops[RUSSIA_SYSTEM] = "su75-model-lines-only"

    art_src = {
        r"Art\W3D\RUSU75.W3D": PATCH / "Art/W3D/RUSU75.W3D",
        r"Art\W3D\RUSU75_D.W3D": PATCH / "Art/W3D/RUSU75_D.W3D",
        r"Art\W3D\RUSU75_E.W3D": PATCH / "Art/W3D/RUSU75_E.W3D",
        r"Art\W3D\RUSU75_E1.W3D": PATCH / "Art/W3D/RUSU75_E1.W3D",
        r"Art\W3D\RUSU75_E2.W3D": PATCH / "Art/W3D/RUSU75_E2.W3D",
        r"Art\Textures\SU-75.dds": PATCH / "Art/Textures/SU-75.dds",
        r"Art\Textures\SU-75_D.dds": PATCH / "Art/Textures/SU-75_D.dds",
        r"Art\Textures\SU-75_E.dds": PATCH / "Art/Textures/SU-75_E.dds",
    }
    for name, path in art_src.items():
        art_ops[name] = upsert(art_entries, name, path.read_bytes())

    data_bytes = write_big(data_entries)
    art_bytes = write_big(art_entries)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_bytes)
    out_art.write_bytes(art_bytes)

    src_data = {n.replace("/", "\\").lower(): b for n, b in read_big(DATA_SRC)}
    new_data = {n.replace("/", "\\").lower(): b for n, b in read_big(out_data)}
    src_art = {n.replace("/", "\\").lower(): b for n, b in read_big(ART_SRC)}
    new_art = {n.replace("/", "\\").lower(): b for n, b in read_big(out_art)}

    changed_data = [k for k in new_data if src_data.get(k) != new_data[k]]
    if changed_data != [RUSSIA_SYSTEM.replace("/", "\\").lower()]:
        raise SystemExit(f"unexpected DATA changes: {changed_data}")
    for key in FROZEN:
        if src_data[key] != new_data[key]:
            raise SystemExit(f"frozen file changed: {key}")

    # ART: only additions, existing RUS_SU57 untouched
    art_changed = [k for k in new_art if src_art.get(k) != new_art[k]]
    expected_art = {name.replace("/", "\\").lower() for name in art_src}
    if set(art_changed) != expected_art:
        raise SystemExit(f"unexpected ART changes: {art_changed}")
    if src_art.get(r"art\w3d\rus_su57.w3d") != new_art.get(r"art\w3d\rus_su57.w3d"):
        raise SystemExit("shared RUS_SU57.W3D was replaced")
    for name in art_src:
        key = name.replace("/", "\\").lower()
        if key not in new_art:
            raise SystemExit(f"missing ART {name}")

    data_sha = hashlib.sha256(data_bytes).hexdigest()
    art_sha = hashlib.sha256(art_bytes).hexdigest()
    zpath = OUT / "RUSSIA_SU75_ART.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()
    report = OUT / "PACK_REPORT.txt"
    report.write_text(
        f"DATA SHA256={data_sha} SIZE={len(data_bytes)}\n"
        f"ART  SHA256={art_sha} SIZE={len(art_bytes)}\n"
        f"ZIP  SHA256={zip_sha} SIZE={zpath.stat().st_size}\n"
        f"DATA ops={data_ops}\n"
        f"ART ops={art_ops}\n"
        f"Su-75 Model retarget RUS_SU57 -> RUSU75/_D/_E only. Shared Su-57 ART kept.\n",
        encoding="utf-8",
    )
    print(report.read_text())
    print("ZIP", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
