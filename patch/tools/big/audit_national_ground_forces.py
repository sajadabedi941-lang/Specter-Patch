#!/usr/bin/env python3
"""Packed-BIG audit for National Ground Forces (17 countries x 14 units)."""

from __future__ import annotations

import hashlib
import io
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from national_ground_roster import COUNTRIES, LOCKED_BIG_PATHS, PROTECTED_COMMANDSETS, all_units

DATA = Path("/tmp/national_ground_forces/_SPEC_DATA_ONE.big")
ART = Path("/tmp/national_ground_forces/_SPEC_ART_ONE.big")
SRC_DATA = Path("/tmp/wf_national_markings/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/wf_national_markings/_SPEC_ART_ONE.big")
REPORT = Path("/opt/cursor/artifacts/national_ground_forces_audit.txt")


def parse_big(path: Path):
    data = path.read_bytes()
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for i in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((i, name, data[eoff : eoff + esz]))
    return entries


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def basename(name: str) -> str:
    return name.replace("\\", "/").split("/")[-1].lower()


def last_named(text, kind, name):
    hits = list(re.finditer(rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?(?=^{kind}\s|\Z)", text))
    return hits[-1].group(0) if hits else None


def last_named_any(entries, kind, name):
    hits = []
    for i, n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        blk = last_named(t, kind, name)
        if blk:
            hits.append((n, blk))
    return hits[-1] if hits else None


def last_object_any(entries, obj):
    return last_named_any(entries, "Object", obj)


def walk_csf(blob):
    pos = 24
    nlab = struct.unpack_from("<I", blob, 8)[0]
    out = {}
    for _ in range(nlab):
        if blob[pos : pos + 4] != b" LBL":
            break
        nstr, namelen = struct.unpack_from("<II", blob, pos + 4)
        pos += 12
        name = blob[pos : pos + namelen].decode("latin1", "replace")
        pos += namelen
        vals = []
        for _s in range(nstr):
            mag = blob[pos : pos + 4]
            slen = struct.unpack_from("<I", blob, pos + 4)[0]
            pos += 8
            raw = blob[pos : pos + slen * 2]
            pos += slen * 2
            val = bytes(x ^ 0xFF for x in raw).decode("utf-16-le", "replace")
            if mag == b"WRTS":
                elen = struct.unpack_from("<I", blob, pos)[0]
                pos += 4 + elen
            vals.append(val)
        out[name] = vals[0] if vals else ""
    return out


def fail(msg):
    print("FAIL", msg)
    return 1


def _run() -> int:
    errors = 0
    if not DATA.is_file() or not ART.is_file():
        return fail("missing packed BIG")
    data = parse_big(DATA)
    art = parse_big(ART)
    src_data = parse_big(SRC_DATA)
    src_art = parse_big(SRC_ART)
    dmap = {norm(n): (i, n, b) for i, n, b in data}
    amap = {norm(n): (i, n, b) for i, n, b in art}
    smap = {norm(n): b for i, n, b in src_data}
    art_bases = {basename(n): n for i, n, b in art}

    print("DATA_SHA256", hashlib.sha256(DATA.read_bytes()).hexdigest())
    print("ART_SHA256", hashlib.sha256(ART.read_bytes()).hexdigest())
    print("DATA_FILES", len(data), "ART_FILES", len(art))
    if [n for _, n, _ in data][: len(src_data)] != [n for _, n, _ in src_data]:
        errors += fail("DATA entry-order prefix changed")
    else:
        print("OK DATA entry-order prefix")
    if [n for _, n, _ in art][: len(src_art)] != [n for _, n, _ in src_art]:
        errors += fail("ART entry-order prefix changed")
    else:
        print("OK ART entry-order prefix")

    for locked in LOCKED_BIG_PATHS:
        if norm(locked) in smap and dmap.get(norm(locked), (None, None, None))[2] != smap[norm(locked)]:
            errors += fail(f"locked changed {locked}")
        elif norm(locked) in smap:
            print("OK locked", locked)

    csf_blob = None
    for i, n, b in data:
        if n.lower().endswith("generals.csf"):
            csf_blob = b
    if not csf_blob:
        return fail("missing generals.csf")
    csf = walk_csf(csf_blob)

    defined_weapons = set()
    defined_armor = set()
    defined_loco = set()
    for i, n, b in data:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        defined_weapons.update(re.findall(r"(?m)^Weapon\s+(\S+)", t))
        defined_armor.update(re.findall(r"(?m)^Armor\s+(\S+)", t))
        defined_loco.update(re.findall(r"(?m)^Locomotor\s+(\S+)", t))

    for pcs in PROTECTED_COMMANDSETS:
        src_hit = last_named_any(src_data, "CommandSet", pcs)
        dst_hit = last_named_any(data, "CommandSet", pcs)
        if src_hit and dst_hit and src_hit[1] != dst_hit[1]:
            errors += fail(f"protected CommandSet changed {pcs}")

    unit_count = 0
    for country in COUNTRIES:
        hit = last_named_any(data, "CommandSet", country.cs)
        if not hit:
            errors += fail(f"missing CS {country.cs}")
            continue
        _csfile, blk = hit
        slots = {int(a): b for a, b in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", blk)}
        if len(slots) != 14 or set(slots) != set(range(1, 15)):
            errors += fail(f"{country.key} last-wins {_csfile} slots {sorted(slots)}")
            continue
        print(f"OK {country.key} {country.cs} last-wins {_csfile} 14 slots")
        for extra in (country.cs + "1", country.cs + "2", country.cs + "3"):
            ehit = last_named_any(data, "CommandSet", extra)
            if not ehit:
                continue
            eslots = {int(a): b for a, b in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", ehit[1])}
            if set(eslots.values()) != set(slots.values()):
                errors += fail(f"{extra} last-wins {ehit[0]} does not match 14-slot roster")
        for idx, unit in enumerate(country.units, 1):
            unit_count += 1
            btn = f"Command_Construct{unit.obj}"
            if slots.get(idx) != btn:
                errors += fail(f"{country.key} slot {idx} {slots.get(idx)} != {btn}")
            bhit = last_named_any(data, "CommandButton", btn)
            if not bhit:
                errors += fail(f"missing button {btn}")
                continue
            _bf, bblk = bhit
            obj = re.search(r"(?m)^\s*Object\s+=\s+(\S+)", bblk)
            if not obj or obj.group(1) != unit.obj:
                errors += fail(f"{btn} Object {obj.group(1) if obj else None}")
            ohit = last_object_any(data, unit.obj)
            if not ohit:
                errors += fail(f"missing object {unit.obj}")
                continue
            _fn, oblk = ohit
            model = re.search(r"(?m)^\s*Model\s+=\s+(\S+)", oblk)
            if not model:
                errors += fail(f"{unit.obj} no Model")
                continue
            stem = model.group(1)
            if stem.lower() + ".w3d" not in art_bases:
                errors += fail(f"{unit.obj} Model {stem} missing from ART")
            for key in (f"OBJECT:{unit.obj}", f"CONTROLBAR:Construct{unit.obj}", f"CONTROLBAR:ToolTip{unit.obj}"):
                if key not in csf:
                    errors += fail(f"missing CSF {key}")
            weap = re.findall(r"(?m)^\s*Weapon\s+=\s+(?:PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", oblk)
            if not weap:
                weap = [w for w in re.findall(r"(?m)^\s*Weapon\s+=\s+(\S+)", oblk) if w not in {"PRIMARY", "SECONDARY", "TERTIARY"}]
            if not weap:
                errors += fail(f"{unit.obj} no Weapon")
            for w in weap:
                if w not in defined_weapons:
                    errors += fail(f"{unit.obj} Weapon {w} missing")
            armors = re.findall(r"(?m)^\s*Armor\s+=\s+(\S+)", oblk)
            if not armors:
                errors += fail(f"{unit.obj} no Armor")
            for a in armors:
                if a not in defined_armor:
                    errors += fail(f"{unit.obj} Armor {a} missing")
            locos = re.findall(r"(?m)^\s*Locomotor\s+=\s+SET_\S+\s+(\S+)", oblk)
            if not locos:
                errors += fail(f"{unit.obj} no Locomotor")
            for loc in locos:
                if loc not in defined_loco:
                    errors += fail(f"{unit.obj} Locomotor {loc} missing")
            print(f"  {idx:2d} {unit.obj} model={stem} file={Path(_fn.replace(chr(92), '/')).name} weap={len(weap)} csf=OK")

    print("UNIT_COUNT", unit_count)
    if unit_count != 17 * 14:
        errors += fail(f"expected 238 units, got {unit_count}")

    if errors:
        print("AUDIT_FAIL", errors)
        return 1
    print("AUDIT_OK")
    return 0


def main() -> int:
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        code = _run()
    finally:
        sys.stdout = old
    text = buf.getvalue()
    print(text, end="")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text)
    print("wrote", REPORT)
    return code


if __name__ == "__main__":
    sys.exit(main())
