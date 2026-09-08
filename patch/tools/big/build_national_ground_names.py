#!/usr/bin/env python3
"""DATA-only national ground naming pass.

Updates DisplayName, CommandButton TextLabel/DescriptLabel, and CSF strings.
Does not change ART, models, weapons, armor, locomotor, cost, time, or CommandSets.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_national_ground_forces import (
    LOCKED_BIG_PATHS,
    build_big_ordered,
    last_named,
    norm,
    parse_big,
    xor_csf_utf16,
)
from national_ground_names import NAMES
from national_ground_roster import all_units

SRC_DATA = Path("/tmp/national_ground_visual/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/national_ground_visual/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/national_ground_names")


def parse_csf(blob: bytes):
    if blob[:4] != b" FSC":
        raise SystemExit("generals.csf is not CSF")
    version, nlabels, nstrings, unused, lang = struct.unpack_from("<IIIII", blob, 4)
    pos = 24
    labels = []
    for _ in range(nlabels):
        if blob[pos : pos + 4] != b" LBL":
            raise SystemExit(f"bad LBL at {pos}")
        nstr, namelen = struct.unpack_from("<II", blob, pos + 4)
        pos += 12
        name = blob[pos : pos + namelen].decode("latin1")
        pos += namelen
        strs = []
        for _s in range(nstr):
            mag = blob[pos : pos + 4]
            slen = struct.unpack_from("<I", blob, pos + 4)[0]
            pos += 8
            raw = blob[pos : pos + slen * 2]
            pos += slen * 2
            val = bytes(x ^ 0xFF for x in raw).decode("utf-16-le")
            extra = b""
            if mag == b"WRTS":
                elen = struct.unpack_from("<I", blob, pos)[0]
                pos += 4
                extra = blob[pos : pos + elen]
                pos += elen
            strs.append((mag, val, extra))
        labels.append((name, strs))
    if pos != len(blob):
        trailing = blob[pos:]
    else:
        trailing = b""
    if len(labels) != nlabels:
        raise SystemExit("CSF label count mismatch")
    return version, unused, lang, labels, trailing


def build_csf(version: int, unused: int, lang: int, labels, trailing: bytes = b"") -> bytes:
    out = bytearray()
    out += b" FSC"
    nlabels = len(labels)
    nstrings = sum(len(strs) for _n, strs in labels)
    out += struct.pack("<IIIII", version, nlabels, nstrings, unused, lang)
    for name, strs in labels:
        key = name.encode("latin1")
        out += b" LBL"
        out += struct.pack("<II", len(strs), len(key))
        out += key
        for mag, val, extra in strs:
            out += mag
            out += struct.pack("<I", len(val))
            out += xor_csf_utf16(val)
            if mag == b"WRTS":
                out += struct.pack("<I", len(extra))
                out += extra
    out += trailing
    return bytes(out)


def upsert_csf(blob: bytes, updates: dict[str, str]) -> bytes:
    version, unused, lang, labels, trailing = parse_csf(blob)
    seen = {name.upper() for name, _s in labels}
    changed = 0
    new_labels = []
    for name, strs in labels:
        if name in updates:
            new_val = updates[name]
            new_strs = []
            for mag, val, extra in strs:
                if val != new_val:
                    changed += 1
                new_strs.append((mag, new_val, extra))
            new_labels.append((name, new_strs))
        else:
            new_labels.append((name, strs))
    for name, value in updates.items():
        if name.upper() in seen:
            continue
        new_labels.append((name, [(b" RTS", value, b"")]))
        changed += 1
    print("csf labels updated/added", changed, "requested", len(updates))
    return build_csf(version, unused, lang, new_labels, trailing)


def index_last_named(entries, kinds: tuple[str, ...]):
    found = {kind: {} for kind in kinds}
    texts = {}
    for i, (n, blob) in enumerate(entries):
        if not n.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1")
        texts[i] = text
        for kind in kinds:
            for m in re.finditer(rf"(?m)^{kind}\s+(\S+)\s*$", text):
                found[kind][m.group(1)] = (i, n)
    return found, texts


def patch_object_display(entries, texts, loc, obj: str, display_key: str) -> None:
    if obj not in loc:
        raise SystemExit(f"missing object {obj}")
    i, fname = loc[obj]
    if norm(fname) in {norm(p) for p in LOCKED_BIG_PATHS}:
        raise SystemExit(f"refusing locked object file {fname}")
    text = texts[i]
    m = last_named(text, "Object", obj)
    if not m:
        raise SystemExit(f"no block {obj} in {fname}")
    blk = m.group(0)
    new_blk, n = re.subn(
        r"(?m)^(\s*DisplayName\s+=\s+)\S+",
        rf"\1{display_key}",
        blk,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"DisplayName missing on {obj} in {fname}")
    if new_blk == blk:
        return
    if re.sub(r"(?m)^\s*DisplayName\s+=\s+\S+", "", blk) != re.sub(r"(?m)^\s*DisplayName\s+=\s+\S+", "", new_blk):
        raise SystemExit(f"non-display change on {obj}")
    texts[i] = text[: m.start()] + new_blk + text[m.end() :]
    entries[i] = (entries[i][0], texts[i].encode("latin1"))
    print("display", obj, "->", display_key, "in", fname)


def patch_button_labels(entries, texts, loc, btn: str, text_key: str, tip_key: str) -> None:
    if btn not in loc:
        raise SystemExit(f"missing button {btn}")
    i, fname = loc[btn]
    text = texts[i]
    m = last_named(text, "CommandButton", btn)
    if not m:
        raise SystemExit(f"no button {btn} in {fname}")
    blk = m.group(0)
    new_blk, n1 = re.subn(r"(?m)^(\s*TextLabel\s+=\s+)\S+", rf"\1{text_key}", blk, count=1)
    new_blk, n2 = re.subn(r"(?m)^(\s*DescriptLabel\s+=\s+)\S+", rf"\1{tip_key}", new_blk, count=1)
    if n1 != 1 or n2 != 1:
        raise SystemExit(f"button labels missing on {btn} in {fname}")
    if new_blk == blk:
        return
    stripped_old = re.sub(r"(?m)^\s*(TextLabel|DescriptLabel)\s+=\s+\S+", "", blk)
    stripped_new = re.sub(r"(?m)^\s*(TextLabel|DescriptLabel)\s+=\s+\S+", "", new_blk)
    if stripped_old != stripped_new:
        raise SystemExit(f"non-label change on {btn}")
    texts[i] = text[: m.start()] + new_blk + text[m.end() :]
    entries[i] = (entries[i][0], texts[i].encode("latin1"))
    print("button", btn, "->", text_key, "in", fname)


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing visual source BIG", file=sys.stderr)
        return 1
    if hashlib.sha256(SRC_ART.read_bytes()).hexdigest() != (
        "0778d63b6d08ac92d025a4fcbd70003fbdeed968de18941eeb2b3059d9a8b353"
    ):
        print("WARNING ART SHA is not the visual-upgrade ART")

    data_entries = parse_big(SRC_DATA)
    src_data_names = [n for n, _ in data_entries]
    data_index = {norm(n): i for i, (n, _) in enumerate(data_entries)}

    wanted = {u.obj for _c, u in all_units()}
    if set(NAMES) != wanted:
        raise SystemExit(f"name map mismatch extra={set(NAMES)-wanted} missing={wanted-set(NAMES)}")

    found, texts = index_last_named(data_entries, ("Object", "CommandButton"))
    csf_updates = {}
    for _country, unit in all_units():
        display, tooltip = NAMES[unit.obj]
        obj_key = f"OBJECT:{unit.obj}"
        text_key = f"CONTROLBAR:Construct{unit.obj}"
        tip_key = f"CONTROLBAR:ToolTip{unit.obj}"
        csf_updates[obj_key] = display
        csf_updates[text_key] = display
        csf_updates[tip_key] = tooltip
        patch_object_display(data_entries, texts, found["Object"], unit.obj, obj_key)
        patch_button_labels(
            data_entries,
            texts,
            found["CommandButton"],
            f"Command_Construct{unit.obj}",
            text_key,
            tip_key,
        )

    csf_key = None
    for n, _b in data_entries:
        if n.lower().endswith("generals.csf"):
            csf_key = n
            break
    if not csf_key:
        raise SystemExit("generals.csf missing")
    i = data_index[norm(csf_key)]
    name, blob = data_entries[i]
    new_csf = upsert_csf(blob, csf_updates)
    data_entries[i] = (name, new_csf)
    print("patched CSF", csf_key, "delta", len(new_csf) - len(blob))

    locked = {norm(p) for p in LOCKED_BIG_PATHS}
    src_map = {norm(n): b for n, b in parse_big(SRC_DATA)}
    for n, b in data_entries:
        if norm(n) in locked and src_map.get(norm(n)) != b:
            raise SystemExit(f"locked file changed {n}")

    if [n for n, _ in data_entries] != src_data_names:
        raise SystemExit("DATA entry names/order changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(data_entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    shutil.copy2(SRC_ART, OUT_DIR / "_SPEC_ART_ONE.big")
    print("DATA_SHA256", hashlib.sha256(data_big).hexdigest())
    print("ART_SHA256", hashlib.sha256((OUT_DIR / "_SPEC_ART_ONE.big").read_bytes()).hexdigest())
    print("DATA_BYTES", len(data_big), "FILES", len(data_entries))
    print("ART copied unchanged from visual pack")
    return 0


if __name__ == "__main__":
    sys.exit(main())
