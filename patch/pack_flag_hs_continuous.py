#!/usr/bin/env python3
"""Keep 3x Flag_Hs size but restore FLAG01/02/03 chain continuity.

Root cause: FLAG01/02/03 (and HOUSECOLOR*) are a parented cloth bone chain.
The first 3x pass scaled every pivot Y as if it lived in LINE01 mesh space
((y - pole_ymin)*3 + pole_ymin). That is correct only for LINE01's direct
children (FLAG03 / HOUSECOLOR03). Grandchild local translations exploded,
stacking the three cloth sections up the pole.

Fix: re-scale from the unscaled IRAN ART.
  - LINE01 verts: Y from ymin * 3 (base planted). LINE01 pivot unchanged.
  - FLAG/HOUSECOLOR verts: XYZ * 3 (same large cloth).
  - LINE01 children: Tx/Tz * 3, Ty pole-stretched (stay at top of tall pole).
  - Deeper FLAG/HOUSECOLOR bones: local T * 3 (preserve rest-pose joins).
Animation is rotation-only and is left untouched.
"""
from __future__ import annotations

import argparse
import struct
import zipfile
from pathlib import Path

from pack_iran_building_flags import replace_w3d_names
from pack_pp_flag_size_3x import (
    MESH,
    MESH_HEADER3,
    PIVOTS,
    VERTS,
    build_big_ordered,
    find_index,
    mesh_bounds,
    read_big,
    read_line01_pivot,
    sha256_file,
    walk_chunks,
)

SRC_ART = Path("/workspace/patch/Release/IRAN_BUILDING_FLAGS/_SPEC_ART_ONE.big")
EXPECTED_ART_SHA = "ec4f5bdcc8f9e9171a8d9fb0d9523cffa41089eded03b330f0f1738aaf555760"
RELEASE = Path("/workspace/patch/Release/FLAG_HS_CONTINUOUS")
PAYLOAD = RELEASE / "payload"
SCALE = 3.0

SCALE_PREFIXES = (
    "jp__", "sk__", "vn__", "in__", "pk__", "ly__", "sy__", "ae__", "sa__",
    "za__", "tr__", "it__", "se__", "uk__", "fr__", "de__", "ua__", "ir__",
    "iq__", "nk__",
)
SKIP_FLAG_HS = ("irq__", "nkr__")

NEW_FLAGS = [
    ("IQ__IQFlag_HsCU", b"IRQ__IQFLAG_HS", r"Art\W3D\Irq__IqFlag_Hs.W3D", b"IraqiFlag.dds"),
    ("IQ__IQFlag_HsWF", b"IRQ__IQFLAG_HS", r"Art\W3D\Irq__IqFlag_Hs.W3D", b"IraqiFlag.dds"),
    ("IQ__IQFlag_HsCP", b"IRQ__IQFLAG_HS", r"Art\W3D\Irq__IqFlag_Hs.W3D", b"IraqiFlag.dds"),
    ("IQ__IQFlag_HsPP", b"IRQ__IQFLAG_HS", r"Art\W3D\Irq__IqFlag_Hs.W3D", b"IraqiFlag.dds"),
    ("IQ__IQFlag_HsSC", b"IRQ__IQFLAG_HS", r"Art\W3D\Irq__IqFlag_Hs.W3D", b"IraqiFlag.dds"),
    ("NK__NKFlag_HsCU", b"NKR__NKFLAG_HS", r"Art\W3D\NKr__NKFlag_Hs.W3D", b"DPRK_Flag.dds"),
    ("NK__NKFlag_HsWF", b"NKR__NKFLAG_HS", r"Art\W3D\NKr__NKFlag_Hs.W3D", b"DPRK_Flag.dds"),
    ("NK__NKFlag_HsCP", b"NKR__NKFLAG_HS", r"Art\W3D\NKr__NKFlag_Hs.W3D", b"DPRK_Flag.dds"),
    ("NK__NKFlag_HsPP", b"NKR__NKFLAG_HS", r"Art\W3D\NKr__NKFlag_Hs.W3D", b"DPRK_Flag.dds"),
    ("NK__NKFlag_HsSC", b"NKR__NKFLAG_HS", r"Art\W3D\NKr__NKFlag_Hs.W3D", b"DPRK_Flag.dds"),
]

FROZEN_ART = [
    r"Art\W3D\Irq__IqFlag_Hs.W3D",
    r"Art\W3D\NKr__NKFlag_Hs.W3D",
    r"Art\W3D\NKor_Powerplant.W3D",
    r"Art\W3D\Iraq_Powerplant.W3D",
    r"Art\W3D\Irq_Command.W3D",
    r"Art\W3D\irq_camp.W3D",
]


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def should_scale(name: str) -> bool:
    ln = norm(name)
    if not ln.startswith("art\\w3d\\") or "flag_hs" not in ln:
        return False
    base = ln.split("\\")[-1]
    if any(base.startswith(p) for p in SKIP_FLAG_HS):
        return False
    return any(base.startswith(p) for p in SCALE_PREFIXES)


def read_pivots(blob: bytes):
    for ctype, ds, de, has_sub in walk_chunks(blob):
        if ctype != PIVOTS or has_sub:
            continue
        rows = []
        for i in range((de - ds) // 60):
            off = ds + i * 60
            name = bytes(blob[off : off + 16]).split(b"\x00", 1)[0].decode("latin1")
            parent = struct.unpack_from("<I", blob, off + 16)[0]
            tx, ty, tz = struct.unpack_from("<fff", blob, off + 20)
            rows.append({"i": i, "name": name, "parent": parent, "t": (tx, ty, tz), "off": off})
        return rows
    raise SystemExit("PIVOTS missing")


def scale_flag_hs_continuous(blob: bytes, factor: float = SCALE) -> bytes:
    bounds = mesh_bounds(blob)
    if "LINE01" not in bounds or "FLAG03" not in bounds:
        raise SystemExit("Flag_Hs missing LINE01/FLAG03")
    ybase = bounds["LINE01"]["ymin"]
    pivots = read_pivots(blob)
    line01_i = next(p["i"] for p in pivots if p["name"] == "LINE01")
    out = bytearray(blob)

    pos = 0
    while pos + 8 <= len(out):
        ctype, raw = struct.unpack_from("<II", out, pos)
        size = raw & 0x7FFFFFFF
        has_sub = bool(raw & 0x80000000)
        ds, de = pos + 8, min(pos + 8 + size, len(out))
        if ctype == MESH and has_sub:
            mesh = None
            for c2, s2, e2, h2 in walk_chunks(out, ds, de):
                if c2 == MESH_HEADER3 and not h2:
                    mesh = bytes(out[s2 + 8 : s2 + 24]).split(b"\x00", 1)[0].decode("latin1")
            if mesh:
                for c2, s2, e2, h2 in walk_chunks(out, ds, de):
                    if c2 == VERTS and not h2:
                        n = (e2 - s2) // 12
                        for i in range(n):
                            off = s2 + i * 12
                            x, y, z = struct.unpack_from("<fff", out, off)
                            if mesh == "LINE01":
                                y = (y - ybase) * factor + ybase
                            elif mesh.startswith("FLAG") or mesh.startswith("HOUSECOLOR"):
                                x *= factor
                                y *= factor
                                z *= factor
                            struct.pack_into("<fff", out, off, x, y, z)
        pos = de

    for p in read_pivots(out):
        if p["name"] in ("ROOTTRANSFORM", "LINE01"):
            continue
        if not (p["name"].startswith("FLAG") or p["name"].startswith("HOUSECOLOR")):
            continue
        tx, ty, tz = struct.unpack_from("<fff", out, p["off"] + 20)
        if p["parent"] == line01_i:
            tx *= factor
            tz *= factor
            ty = (ty - ybase) * factor + ybase
        else:
            tx *= factor
            ty *= factor
            tz *= factor
        struct.pack_into("<fff", out, p["off"] + 20, tx, ty, tz)

    if len(out) != len(blob):
        raise SystemExit("W3D size changed")
    return bytes(out)


def clone_scaled(donor: bytes, old_name: bytes, model: str, tex: bytes) -> bytes:
    new_name = model.upper().encode("ascii")
    blob = replace_w3d_names(donor, old_name, new_name)
    blob = scale_flag_hs_continuous(blob)
    if tex not in blob:
        raise SystemExit(f"{model} lost {tex}")
    return blob


def write_payload(repl: dict[str, bytes]) -> None:
    if PAYLOAD.exists():
        for p in PAYLOAD.rglob("*"):
            if p.is_file():
                p.unlink()
    for name, blob in repl.items():
        dest = PAYLOAD / name.replace("\\", "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)


def validate(orig_art, new_art) -> None:
    orig_m = {norm(n): (n, b) for n, b in orig_art}
    new_m = {norm(n): (n, b) for n, b in new_art}
    for packed in FROZEN_ART:
        if orig_m[norm(packed)][1] != new_m[norm(packed)][1]:
            raise SystemExit(f"frozen ART changed: {packed}")

    scaled = 0
    for n, b in new_art:
        if not should_scale(n):
            continue
        scaled += 1
        key = norm(n)
        # originals for the 90 live in IRAN under the same name; IQ/NK are new
        if key in orig_m:
            old = orig_m[key][1]
        else:
            donor_key = "art\\w3d\\irq__iqflag_hs.w3d" if key.startswith("art\\w3d\\iq__") else "art\\w3d\\nkr__nkflag_hs.w3d"
            old = orig_m[donor_key][1]
        if read_line01_pivot(old) != read_line01_pivot(b):
            raise SystemExit(f"{n}: LINE01 pivot changed")
        if len(old) != len(b):
            raise SystemExit(f"{n}: size changed")
        ob = mesh_bounds(old)
        nb = mesh_bounds(b)
        old_flag = ob["FLAG03"]["ymax"] - ob["FLAG03"]["ymin"]
        new_flag = nb["FLAG03"]["ymax"] - nb["FLAG03"]["ymin"]
        if abs(new_flag / old_flag - SCALE) > 0.05:
            raise SystemExit(f"{n}: FLAG03 scale {new_flag / old_flag}")
        old_pole = ob["LINE01"]["ymax"] - ob["LINE01"]["ymin"]
        new_pole = nb["LINE01"]["ymax"] - nb["LINE01"]["ymin"]
        if abs(new_pole / old_pole - SCALE) > 0.05:
            raise SystemExit(f"{n}: LINE01 scale {new_pole / old_pole}")
        if abs(nb["LINE01"]["ymin"] - ob["LINE01"]["ymin"]) > 0.05:
            raise SystemExit(f"{n}: pole base moved")

        op = read_pivots(old)
        np_ = read_pivots(b)
        ybase = ob["LINE01"]["ymin"]
        line01_i = next(p["i"] for p in op if p["name"] == "LINE01")
        for a, c in zip(op, np_):
            if a["name"] != c["name"] or a["parent"] != c["parent"]:
                raise SystemExit(f"{n}: pivot hierarchy drifted")
            if a["name"] in ("ROOTTRANSFORM", "LINE01"):
                if max(abs(x - y) for x, y in zip(a["t"], c["t"])) > 0.001:
                    raise SystemExit(f"{n}: {a['name']} pivot moved")
                continue
            ox, oy, oz = a["t"]
            nx, ny, nz = c["t"]
            if a["parent"] == line01_i:
                ex, ey, ez = ox * SCALE, (oy - ybase) * SCALE + ybase, oz * SCALE
            else:
                ex, ey, ez = ox * SCALE, oy * SCALE, oz * SCALE
            if max(abs(nx - ex), abs(ny - ey), abs(nz - ez)) > 0.05:
                raise SystemExit(f"{n}: {a['name']} T {c['t']} != expected {(ex, ey, ez)}")

    if scaled < 90:
        raise SystemExit(f"expected >=90 scaled Flag_Hs, got {scaled}")
    print("STATIC VALIDATION: PASS")
    print(f"  Flag_Hs meshes re-scaled 3x with hierarchical pivots: {scaled}")
    print("  LINE01 attach pivot unchanged; grandchild local T * 3")
    print("  FLAG03/HOUSECOLOR03 stay at pole-top (Y pole-stretched)")


def write_docs(art_sha: str, scaled: int) -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)
    (RELEASE / "AUDIT.txt").write_text(
        "FLAG_HS_CONTINUOUS\n"
        f"SOURCE_ART_SHA = {EXPECTED_ART_SHA}\n"
        "ROOT_CAUSE = FLAG01/02/03 are a parented cloth chain. First 3x pass "
        "pole-stretched every pivot Y, exploding grandchild offsets.\n"
        "FIX = verts still *3; LINE01 children Y pole-stretched; deeper bones T*3.\n"
        "SIZE = unchanged 3.000x FLAG03 / LINE01\n"
        f"SCALED_W3D = {scaled}\n"
        "DATA = unchanged (use FLAG_SIZE_EVERYWHERE DATA BIG)\n"
        "INGAME_TESTED = NO\n",
        encoding="utf-8",
    )
    (RELEASE / "CHANGELOG.txt").write_text(
        "FLAG_HS_CONTINUOUS\n\n"
        "Keeps the approved 3x national flag size. Restores FLAG01/02/03 as one\n"
        "continuous cloth chain (plus HOUSECOLOR) by scaling child-bone translations\n"
        "in their local parent space instead of pole-mesh space.\n"
        "ART-only. DATA from FLAG_SIZE_EVERYWHERE is unchanged.\n"
        "In-game test: NOT PERFORMED.\n",
        encoding="utf-8",
    )
    (RELEASE / "CHANGED_FILES.txt").write_text(
        "ART replaced: all country *Flag_Hs*.W3D (90 prior + 10 IQ/NK clones)\n"
        "ART skipped: Irq__IqFlag_Hs NKr__NKFlag_Hs building meshes\n"
        "DATA: none (unchanged)\n",
        encoding="utf-8",
    )
    if art_sha:
        (RELEASE / "SHA256.txt").write_text(f"_SPEC_ART_ONE.big  {art_sha}\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", action="store_true")
    args = ap.parse_args()
    if sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    art_work = list(read_big(SRC_ART))
    orig_art = list(art_work)
    repl: dict[str, bytes] = {}

    scaled = 0
    for i, (name, blob) in enumerate(art_work):
        if not should_scale(name):
            continue
        new_blob = scale_flag_hs_continuous(blob)
        art_work[i] = (name, new_blob)
        repl[name] = new_blob
        scaled += 1
    print(f"ART re-scaled existing Flag_Hs: {scaled}")

    for model, old_name, donor_path, tex in NEW_FLAGS:
        donor = orig_art[find_index(orig_art, donor_path)][1]
        blob = clone_scaled(donor, old_name, model, tex)
        packed = rf"Art\W3D\{model}.W3D"
        art_work.append((packed, blob))
        repl[packed] = blob
        scaled += 1
        print("ART NEW", packed)

    write_payload(repl)
    validate(orig_art, art_work)
    write_docs("", scaled)

    if args.pack:
        art_out = RELEASE / "_SPEC_ART_ONE.big"
        art_out.write_bytes(build_big_ordered(art_work))
        asha = sha256_file(art_out)
        print("PACKED", art_out, asha, art_out.stat().st_size)
        write_docs(asha, scaled)
        packed_a = {norm(n): b for n, b in read_big(art_out)}
        src_a = {norm(n): b for n, b in orig_art}
        extra = set(packed_a) - set(src_a)
        expect = {norm(rf"Art\W3D\{m}.W3D") for m, *_ in NEW_FLAGS}
        if extra != expect:
            raise SystemExit(f"unexpected ART extras {extra}")
        print(f"POST-PACK SCOPE: PASS ({scaled} Flag_Hs, {len(extra)} new IQ/NK)")
        zpath = RELEASE / "FLAG_HS_CONTINUOUS.zip"
        with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_STORED) as zf:
            zf.write(art_out, "_SPEC_ART_ONE.big")
            zf.write(RELEASE / "SHA256.txt", "SHA256.txt")
            zf.write(RELEASE / "CHANGELOG.txt", "CHANGELOG.txt")
        print("ZIP", zpath, sha256_file(zpath), zpath.stat().st_size)
    else:
        print("Payload written; BIG not packed (pass --pack after validation).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
