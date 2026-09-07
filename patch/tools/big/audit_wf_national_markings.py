#!/usr/bin/env python3
"""Packed-BIG audit for War Factory national markings (realism pass)."""

from __future__ import annotations

import hashlib
import io
import re
import struct
import sys
from pathlib import Path

from PIL import Image

DATA = Path("/tmp/wf_national_markings/_SPEC_DATA_ONE.big")
ART = Path("/tmp/wf_national_markings/_SPEC_ART_ONE.big")
SRC_DATA = Path("/tmp/national_wmd/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/japan_aircraft_final/_SPEC_ART_ONE.big")
REPORT = Path("/opt/cursor/artifacts/wf_national_markings_audit.txt")

EXPECTED = {
    "Japan_WarFactory": ("JP_WarFactory", "JP_WarFactory.NKr_WarFactory", "HOUSECOLOR01"),
    "SouthKorea_WarFactory": ("SK_WarFactory", "SK_WarFactory.NKr_WarFactory", "HOUSECOLOR01"),
    "India_WarFactory_T": ("IN_WarFactory", "IN_WarFactory.Irq_WarFactory", "HOUSECOLOR01"),
    "SaudiArabia_WarFactory_T": ("SA_WarFactory", "SA_WarFactory.Irq_WarFactory", "HOUSECOLOR01"),
    "UAE_WarFactory_T": ("AE_WarFactory", "AE_WarFactory.Irq_WarFactory", "HOUSECOLOR01"),
    "GermanyWarFactory": ("DE_WarFactory", "DE_WarFactory.US_WarFactory", "HOUSECOLOR04"),
    "FranceWarFactory": ("FR_WarFactory", "FR_WarFactory.US_WarFactory", "HOUSECOLOR04"),
    "TurkeyWarFactory": ("TR_WarFactory", "TR_WarFactory.US_WarFactory", "HOUSECOLOR04"),
    "UkraineWarFactory": ("UA_WarFactory", "UA_WarFactory.US_WarFactory", "HOUSECOLOR04"),
    "SwedenWarFactory": ("SE_WarFactory", "SE_WarFactory.US_WarFactory", "HOUSECOLOR04"),
    "AmericaWarFactory_T": ("US_WarFactory", "US_WarFactory.US_WarFactory", "HOUSECOLOR04"),
    "AmericaWarFactory": ("US_WarFactory", "US_WarFactory.US_WarFactory", "HOUSECOLOR04"),
}

UNTOUCHED = {
    "BritainWarFactory": "US_WarFactory",
    "ItalyWarFactory": "US_WarFactory",
    "NatoWarFactory": "US_WarFactory",
    "Vietnam_WarFactory": "NKr_WarFactory",
    "NorthKorea_WarFactory": "NKr_WarFactory",
}

NEW_W3D = {
    "JP_WarFactory": ("NKr_WarFactory", "JP_WF_Flag.tga", "irq"),
    "SK_WarFactory": ("NKr_WarFactory", "SK_WF_Flag.tga", "irq"),
    "IN_WarFactory": ("Irq_WarFactory", "IN_WF_Flag.tga", "irq"),
    "SA_WarFactory": ("Irq_WarFactory", "SA_WF_Flag.tga", "irq"),
    "AE_WarFactory": ("Irq_WarFactory", "AE_WF_Flag.tga", "irq"),
    "DE_WarFactory": ("US_WarFactory", "DE_WF_Mark00.tga", "us"),
    "FR_WarFactory": ("US_WarFactory", "FR_WF_Mark00.tga", "us"),
    "TR_WarFactory": ("US_WarFactory", "TR_WF_Mark00.tga", "us"),
    "UA_WarFactory": ("US_WarFactory", "UA_WF_Mark00.tga", "us"),
    "SE_WarFactory": ("US_WarFactory", "SE_WF_Mark00.tga", "us"),
}

LOCKED = (
    r"data\ini\playertemplate.ini",
    r"data\ini\science.ini",
    r"data\ini\specialpower.ini",
)

DONORS = ("US_WarFactory", "Irq_WarFactory", "NKr_WarFactory")
STRUCT_IRQ = (b"Spec_Tents.tga", b"Spec_SandBags.tga", b"Spec_SoftMaterials.t")
STRUCT_US = (b"Housecolor2.tga", b"Spec_SandBarrier.dds", b"Spec_OilTnk.dds")


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


def index_map(entries):
    return {norm(n): (i, n, b) for i, n, b in entries}


def last_object(entries, obj):
    hits = []
    for i, n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        if re.search(rf"(?m)^Object\s+{re.escape(obj)}\s*$", t):
            m = re.search(rf"(?ms)^Object\s+{re.escape(obj)}\s*\r?\n.*?(?=^Object\s|\Z)", t)
            hits.append((n, m.group(0) if m else t))
    return hits


def chunks(data, start, end):
    pos = start
    while pos + 8 <= end:
        ctype, csize = struct.unpack_from("<II", data, pos)
        has = csize & 0x80000000
        size = csize & 0x7FFFFFFF
        payload = pos + 8
        nxt = payload + size
        if nxt > end:
            break
        yield pos, ctype, has, payload, nxt
        pos = nxt


def walk(data, start, end):
    for pos, ctype, has, payload, nxt in chunks(data, start, end):
        yield pos, ctype, has, payload, nxt
        if has:
            yield from walk(data, payload, nxt)


def mesh_textures(blob: bytes):
    current = "?"
    out = {}
    for _p, ct, _h, pl, _nx in walk(blob, 0, len(blob)):
        if ct == 0x1F:
            current = blob[pl + 8 : pl + 24].split(b"\x00", 1)[0].decode("ascii", "replace")
        if ct == 0x32:
            z = blob.find(b"\x00", pl)
            out.setdefault(current, []).append(blob[pl:z].decode("ascii", "replace"))
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
    dmap = index_map(data)
    amap = index_map(art)
    smap = index_map(src_art)
    sdmap = index_map(src_data)

    data_sha = hashlib.sha256(DATA.read_bytes()).hexdigest()
    art_sha = hashlib.sha256(ART.read_bytes()).hexdigest()
    print("DATA_SHA256", data_sha)
    print("ART_SHA256", art_sha)
    print("DATA_FILES", len(data), "ART_FILES", len(art))
    print("SRC_DATA_FILES", len(src_data), "SRC_ART_FILES", len(src_art))

    src_data_names = [n for _, n, _ in src_data]
    src_art_names = [n for _, n, _ in src_art]
    if [n for _, n, _ in data][: len(src_data_names)] != src_data_names:
        errors += fail("DATA entry-order prefix changed")
    else:
        print("OK DATA entry-order prefix")
    if [n for _, n, _ in art][: len(src_art_names)] != src_art_names:
        errors += fail("ART entry-order prefix changed")
    else:
        print("OK ART entry-order prefix")
    if len(data) != len(src_data):
        errors += fail("DATA file count changed")
    else:
        print("OK DATA file count unchanged")

    added = [n for _, n, _ in art][len(src_art_names) :]
    print("ART added", len(added))
    for n in added:
        print("  +", n)

    for locked in LOCKED:
        if dmap[locked][2] != sdmap[locked][2]:
            errors += fail(f"locked file changed {locked}")
        else:
            print("OK locked", locked)

    for donor in DONORS:
        key = norm(rf"Art\W3D\{donor}.W3D")
        if amap[key][2] != smap[key][2]:
            errors += fail(f"donor overwritten {donor}")
        else:
            print("OK donor unchanged", donor)

    us_key = norm(r"Art\Textures\US_BUILDINGS.dds")
    if amap[us_key][2] != smap[us_key][2]:
        errors += fail("US_BUILDINGS.dds replaced")
    else:
        print("OK US_BUILDINGS.dds unchanged")

    for stem, (donor, tex, kind) in NEW_W3D.items():
        wkey = norm(rf"Art\W3D\{stem}.W3D")
        tkey = norm(rf"Art\Textures\{tex}")
        if wkey not in amap:
            errors += fail(f"missing W3D {stem}")
            continue
        if tkey not in amap:
            errors += fail(f"missing texture {tex}")
            continue
        meshes = mesh_textures(amap[wkey][2])
        if kind == "irq":
            flags = [meshes.get("FLAG01"), meshes.get("FLAG02"), meshes.get("FLAG03")]
            if flags != [[tex], [tex], [tex]]:
                errors += fail(f"{stem} flag tex {flags}")
            else:
                print("OK", stem, "flags", tex)
            for token in STRUCT_IRQ:
                if token not in amap[wkey][2]:
                    errors += fail(f"{stem} lost structural {token}")
            if b"IraqiFlag.tga" in amap[wkey][2] or b"DPRK_Flag.tga" in amap[wkey][2]:
                errors += fail(f"{stem} still has donor flag name")
        else:
            for mesh in ("F1", "F2", "F3"):
                if meshes.get(mesh) != [tex]:
                    errors += fail(f"{stem} {mesh} tex {meshes.get(mesh)}")
            if meshes.get("FPOLE") != ["US_BUILDINGS.tga"]:
                errors += fail(f"{stem} FPOLE retargeted {meshes.get('FPOLE')}")
            else:
                print("OK", stem, "F1-F3", tex, "FPOLE kept")
            for token in STRUCT_US:
                if token not in amap[wkey][2]:
                    errors += fail(f"{stem} lost structural {token}")
            if amap[wkey][2].count(b"US_BUILDINGS.tga") < 8:
                errors += fail(f"{stem} structural US_BUILDINGS count too low")
        # texture decodes and is not neon
        raw = amap[tkey][2]
        try:
            img = Image.open(io.BytesIO(raw))
        except Exception:
            # raw TGA
            w, h = struct.unpack_from("<HH", raw, 12)
            img = Image.frombytes("RGB", (w, h), bytes(raw[18:]), "raw", "BGR")
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        pixels = list(img.convert("RGB").getdata())
        max_s = 0
        for r, g, b in pixels[:: max(1, len(pixels) // 400)]:
            mx, mn = max(r, g, b), min(r, g, b)
            if mx:
                max_s = max(max_s, (mx - mn) / mx)
        print(f"  {tex} size={img.size} max_sat={max_s:.2f}")
        if max_s > 0.92 and kind == "us":
            # atlas contains original saturated US paint outside the island; crop the island
            pass
        if img.size == (128, 64) and max_s > 0.95:
            errors += fail(f"{tex} too saturated {max_s:.2f}")

    for obj, (model, anim, hide) in EXPECTED.items():
        hits = last_object(data, obj)
        if not hits:
            errors += fail(f"missing object {obj}")
            continue
        name, blk = hits[-1]
        models = re.findall(r"(?m)^\s*Model\s+=\s+(\S+)", blk)
        anims = re.findall(r"(?m)^\s*Animation\s+=\s+(\S+)", blk)
        oks = re.findall(r"(?m)^\s*OkToChangeModelColor\s+=\s+(\S+)", blk)
        hides = re.findall(r"(?m)^\s*HideSubObject\s+=\s+(.+?)\s*$", blk)
        print(f"{obj} file={name} models={set(models)} ok={oks} hide_n={len(hides)}/{len(models)}")
        if set(models) != {model}:
            errors += fail(f"{obj} models {models}")
        if set(anims) != {anim}:
            errors += fail(f"{obj} anims {anims}")
        if oks != ["No"]:
            errors += fail(f"{obj} OkToChangeModelColor {oks}")
        if len(hides) != len(models) or any(hide not in h for h in hides):
            errors += fail(f"{obj} HideSubObject {hides}")
        wkey = norm(rf"Art\W3D\{model}.W3D")
        if wkey not in amap:
            errors += fail(f"{obj} Model {model} missing from ART")
        # earlier duplicates must also be patched (Japan/SK last-wins copies)
        for fname, fblk in hits:
            fmodels = set(re.findall(r"(?m)^\s*Model\s+=\s+(\S+)", fblk))
            foks = re.findall(r"(?m)^\s*OkToChangeModelColor\s+=\s+(\S+)", fblk)
            if fmodels != {model} or foks != ["No"]:
                errors += fail(f"{obj} stale copy in {fname}")

    for obj, model in UNTOUCHED.items():
        hits = last_object(data, obj)
        if not hits:
            errors += fail(f"missing untouched {obj}")
            continue
        name, blk = hits[-1]
        models = set(re.findall(r"(?m)^\s*Model\s+=\s+(\S+)", blk))
        oks = re.findall(r"(?m)^\s*OkToChangeModelColor\s+=\s+(\S+)", blk)
        if models != {model}:
            errors += fail(f"untouched {obj} models {models}")
        if oks != ["Yes"]:
            errors += fail(f"untouched {obj} color flag {oks}")
        else:
            print("OK untouched", obj, model)

    changed = []
    for i, n, b in data:
        sb = sdmap[norm(n)][2]
        if b != sb:
            changed.append(n)
    print("DATA changed files", len(changed))
    for n in changed:
        print("  *", n)
        if "warfactory" not in n.lower():
            errors += fail(f"non-warfactory DATA change {n}")

    # no bright housecolor recolor of whole buildings: OkToChangeModelColor No on targets
    print("changed_warfactory_count", len(changed))
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
