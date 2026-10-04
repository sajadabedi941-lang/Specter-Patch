#!/usr/bin/env python3
"""Restore Iranian national Flag_Hs on six standard buildings.

JP/SK/VN Barracks are already correct (HideSubObject FLAG01-03 + country
Flag_Hs + JP/SK/VN_Flag.tga) and are not modified.

Iran has no IR_Flag texture, no Flag_Hs mesh, and no Draw attachment.
DATA is required: ART-only W3Ds cannot attach to buildings.

Source: EUROPEAN_BUILDING_FLAGS_FINAL DATA + ART.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import re
import struct
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/EUROPEAN_BUILDING_FLAGS_FINAL/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/EUROPEAN_BUILDING_FLAGS_FINAL/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "f5bfdefd1aef43ceb9b23327d0fa3bf72d9702e33900d4890e74163a8e387104"
EXPECTED_ART_SHA = "fce888aca990e511df7bdb74c302b51a253eb89b250a4b92f8733f3cb28b0702"
RELEASE = Path("/workspace/patch/Release/IRAN_BUILDING_FLAGS")
PAYLOAD = RELEASE / "payload"

P_DONOR = r"Art\W3D\Irq__IqFlag_Hs.W3D"
DONOR_NAME = b"IRQ__IQFLAG_HS"
DONOR_TEX = b"IraqiFlag.dds"
PIVOTS = 0x00000102
HALF_POLE = 17.492

# Per-building LINE01: Iran mesh attach point + half Flag_Hs pole.
LINE01 = {
    "CP": (40.929214, 15.818870, -0.690117 + HALF_POLE),  # Iran_Camp CYLINDER11
    "CU": (-64.593636, 46.108624, 28.039402 + HALF_POLE),  # Iran_Command BOX16
    "WF": (-40.438286, -27.859848, 22.942892 + HALF_POLE),  # Iran_WarFactory BOX05
    "PP": (20.491306, -9.029234, 0.340959 + HALF_POLE),  # Irn_Power FPOLE
    "SC": (-31.631107, 19.081333, 9.745492 + HALF_POLE),  # Iran_Supply BOX14
}

PP_HIDE = "      HideSubObject = FPOLE HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06"

# (packed INI, object, kind, hide_line or None)
TARGETS = [
    (r"Data\INI\Object\Specter\Iranian Army\Buildings\Camp.ini", "IranBarracks", "CP", None),
    (r"Data\INI\Object\Specter\Iranian Army\Buildings\Command.ini", "IranCommandCenter", "CU", None),
    (r"Data\INI\Object\Specter\Iranian Army\Buildings\Warfactory.ini", "IranWarFactory", "WF", None),
    (r"Data\INI\Object\Specter\Iranian Army\Buildings\Powerplant.ini", "IranPowerplant", "PP", PP_HIDE),
    (r"Data\INI\Object\Specter\Iranian Army\Buildings\SupplyCenter.ini", "IranSupplyCenter", "SC", None),
]

FROZEN_OBJECTS = [
    "Japan_Barracks",
    "SouthKorea_Barracks",
    "Vietnam_Barracks",
    "India_Barracks",
    "Pakistan_Barracks",
    "Libya_Barracks",
    "Iraq_Barracks",
    "BritainBootCamp",
    "TurkeyBootCamp",
]

OBJ_RE = re.compile(r"(?im)^Object\s+(\S+)")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_big(path: Path):
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


def build_big_ordered(entries):
    header_size = 16
    encoded = [n.encode("latin1", errors="replace") for n, _ in entries]
    for nb in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    out = bytearray(b"BIGF")
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded):
        content = bytes(content)
        index.append((offset, len(content), nb))
        blobs.append(content)
        offset += len(content)
    total = offset
    out += struct.pack(">I", total)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for off, size, nb in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries, packed: str) -> int:
    want = packed.replace("/", "\\").lower()
    for i, (n, _) in enumerate(entries):
        if n.replace("/", "\\").lower() == want:
            return i
    raise SystemExit(f"missing {packed}")


def walk_chunks(blob: bytes, start=0, end=None):
    if end is None:
        end = len(blob)
    pos = start
    while pos + 8 <= end:
        ctype, raw = struct.unpack_from("<II", blob, pos)
        size = raw & 0x7FFFFFFF
        has_sub = bool(raw & 0x80000000)
        ds = pos + 8
        de = min(ds + size, end)
        yield ctype, ds, de, has_sub
        if has_sub:
            yield from walk_chunks(blob, ds, de)
        pos = de


def replace_w3d_names(donor: bytes, old: bytes, new: bytes) -> bytes:
    out = bytearray(donor)
    start = 0
    count = 0
    while True:
        i = out.find(old, start)
        if i < 0:
            break
        nul = out.find(b"\x00", i)
        if nul < 0:
            raise SystemExit(f"unterminated name at {i}")
        cur = bytes(out[i:nul])
        if not cur.startswith(old):
            start = i + 1
            continue
        field_len = 32 if b"." in cur else 16
        old_field = cur + b"\x00" * (field_len - len(cur))
        if bytes(out[i : i + field_len]) != old_field:
            raise SystemExit(f"unexpected name field at {i}")
        replacement = new + cur[len(old) :]
        if len(replacement) + 1 > field_len:
            raise SystemExit(f"renamed field too long: {replacement!r}")
        padded = replacement + b"\x00" * (field_len - len(replacement))
        out[i : i + field_len] = padded
        count += 1
        start = i + field_len
    if count != 19:
        raise SystemExit(f"expected 19 container name fields, got {count}")
    if old in bytes(out) or bytes(out).count(new) != 19:
        raise SystemExit("container rename failed")
    return bytes(out)


def replace_w3d_texture(blob: bytes, old: bytes, new: bytes) -> bytes:
    field_len = len(old) + 1
    new_field = new + b"\x00"
    if len(new_field) > field_len:
        raise SystemExit(f"texture name too long: {new!r}")
    new_field += b"\x00" * (field_len - len(new_field))
    out = bytearray(blob)
    count = 0
    start = 0
    while True:
        i = out.find(old, start)
        if i < 0:
            break
        if i + len(old) < len(out) and out[i + len(old)] == 0:
            out[i : i + field_len] = new_field
            count += 1
            start = i + field_len
        else:
            start = i + 1
    if count != 3 or old in bytes(out) or bytes(out).count(new) != 3:
        raise SystemExit("texture rename failed")
    return bytes(out)


def set_line01(blob: bytes, xyz: tuple[float, float, float]) -> bytes:
    out = bytearray(blob)
    patched = 0
    for ctype, ds, de, has_sub in walk_chunks(out):
        if ctype != PIVOTS or has_sub:
            continue
        for i in range((de - ds) // 60):
            off = ds + i * 60
            name = bytes(out[off : off + 16]).split(b"\x00", 1)[0]
            if name == b"LINE01":
                struct.pack_into("<fff", out, off + 20, *xyz)
                patched += 1
    if patched != 1:
        raise SystemExit(f"LINE01 patch count {patched}")
    return bytes(out)


def read_line01(blob: bytes) -> tuple[float, float, float]:
    for ctype, ds, de, has_sub in walk_chunks(blob):
        if ctype != PIVOTS or has_sub:
            continue
        for i in range((de - ds) // 60):
            off = ds + i * 60
            name = blob[off : off + 16].split(b"\x00", 1)[0]
            if name == b"LINE01":
                return struct.unpack_from("<fff", blob, off + 20)
    raise SystemExit("LINE01 missing")


def make_flag_hs(donor: bytes, new_name: bytes, new_tex: bytes, xyz) -> bytes:
    named = replace_w3d_names(donor, DONOR_NAME, new_name)
    texed = replace_w3d_texture(named, DONOR_TEX, new_tex)
    out = set_line01(texed, xyz)
    if len(out) != len(donor):
        raise SystemExit("W3D size changed")
    if DONOR_NAME in out or DONOR_TEX in out or b"IraqiFlag" in out:
        raise SystemExit("donor leaked into new W3D")
    got = read_line01(out)
    if any(abs(a - b) > 1e-3 for a, b in zip(got, xyz)):
        raise SystemExit(f"LINE01 mismatch {got} vs {xyz}")
    return out


def model_name(kind: str) -> str:
    return f"IR__IRFlag_Hs{kind}"


def hier_name(model: str) -> bytes:
    return model.upper().encode("ascii")


def object_spans(text: str):
    ms = list(OBJ_RE.finditer(text))
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        out.append((m.group(1), m.start(), end))
    return out


def last_objects(entries):
    last = {}
    for name, blob in entries:
        if not name.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        for obj, start, end in object_spans(text):
            last[obj] = text[start:end]
    return last


def flag_draw(model: str, nl: str) -> str:
    block = f"""  ; ------------ Flag -----------------
  Draw                = W3DModelDraw ModuleTag_03
    ConditionState    = None
      Model           = {model}
      Animation       = {model}.{model}
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT
    AliasConditionState = SNOW
    AliasConditionState = NIGHT SNOW

    ConditionState    = DAMAGED
      Model           = {model}
      Animation       = {model}.{model}
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT DAMAGED
    AliasConditionState = SNOW DAMAGED
    AliasConditionState = NIGHT SNOW DAMAGED

    ConditionState    = REALLYDAMAGED RUBBLE
      Model           = {model}
      Animation       = {model}.{model}
      AnimationMode   = LOOP
    End
  End
"""
    return block.replace("\n", nl)


def insert_flag(body: str, model: str) -> str:
    if "ModuleTag_03" in body and model in body:
        return body
    nl = "\r\n" if "\r\n" in body else "\n"
    m = re.search(r"(?im)^[ \t]*PlacementViewAngle\s*=", body)
    if not m:
        raise SystemExit(f"missing PlacementViewAngle for {model}")
    return body[: m.start()] + flag_draw(model, nl) + body[m.start() :]


def apply_power_hide(body: str) -> str:
    nl = "\r\n" if "\r\n" in body else "\n"
    hide = PP_HIDE + nl
    lines = body.splitlines(keepends=True)
    out = []
    inserted = 0
    for i, line in enumerate(lines):
        out.append(line)
        if re.match(r"(?i)^\s*Model\s*=\s*Irn_Power\s*$", line.strip("\r\n")):
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if "HideSubObject" not in nxt:
                out.append(hide)
                inserted += 1
    if inserted < 1:
        raise SystemExit("Power HideSubObject not inserted")
    return "".join(out)


def write_iran_flag_tga() -> bytes:
    """128x64 32bpp BGRA TGA matching existing XX_Flag.tga header."""
    w, h = 128, 64
    green = (0x40, 0x9F, 0x23, 255)  # BGRA official-ish
    white = (255, 255, 255, 255)
    red = (0x00, 0x00, 0xDA, 255)
    band = h // 3
    cx, cy = w // 2, h // 2
    # stored coordinates (y=0 bottom)
    stored = []
    for y in range(h):  # y=0 bottom
        visual_y = h - 1 - y
        if visual_y < band:
            row_c = green
        elif visual_y < 2 * band:
            row_c = white
        else:
            row_c = red
        for x in range(w):
            stored.append(row_c)
    # simplified red tulip emblem in the white band
    for y in range(h):
        visual_y = h - 1 - y
        for x in range(w):
            dx = x - cx
            dy = visual_y - cy
            hit = False
            # four upward petals
            for ang in (-0.70, -0.23, 0.23, 0.70):
                px = math.sin(ang) * 7.0
                py = -math.cos(ang) * 7.5
                if (dx - px) ** 2 / 6.0 + (dy - py) ** 2 / 10.0 <= 1.0 and dy <= 8:
                    hit = True
            # center blade / sword
            if abs(dx) <= 1.2 and -9 <= dy <= 8:
                hit = True
            # small base bar
            if abs(dx) <= 5 and -10 <= dy <= -8:
                hit = True
            if hit and band <= visual_y < 2 * band:
                stored[y * w + x] = red
    raw = bytearray()
    for b, g, r, a in stored:
        raw += bytes((b, g, r, a))
    header = bytes([0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 128, 0, 64, 0, 32, 8])
    blob = header + bytes(raw)
    if len(blob) != 32786:
        raise SystemExit(f"IR_Flag.tga size {len(blob)}")
    return blob


def patch_file(text: str, jobs) -> str:
    spans = object_spans(text)
    pieces = []
    last = 0
    by_obj = {obj: (kind, hide) for obj, kind, hide in jobs}
    for obj, start, end in spans:
        pieces.append(text[last:start])
        body = text[start:end]
        if obj in by_obj:
            kind, hide = by_obj[obj]
            model = model_name(kind)
            if hide:
                body = apply_power_hide(body)
            body = insert_flag(body, model)
            if model not in body or "ModuleTag_03" not in body:
                raise SystemExit(f"{obj}: Flag_Hs missing after patch")
            if hide and "FPOLE" not in body:
                raise SystemExit(f"{obj}: hide missing")
        pieces.append(body)
        last = end
    pieces.append(text[last:])
    return "".join(pieces)


def write_payload(art_add: dict[str, bytes], data_repl: dict[str, bytes]) -> None:
    if PAYLOAD.exists():
        for p in PAYLOAD.rglob("*"):
            if p.is_file():
                p.unlink()
    for name, blob in {**art_add, **data_repl}.items():
        dest = PAYLOAD / name.replace("\\", "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)


def validate(art_entries, data_entries, art_add, data_repl) -> None:
    art_map = {n.replace("/", "\\").lower(): (n, b) for n, b in art_entries}
    data_map = {n.replace("/", "\\").lower(): (n, b) for n, b in data_entries}
    # merge adds
    for n, b in art_add.items():
        art_map[n.replace("/", "\\").lower()] = (n, b)
    for n, b in data_repl.items():
        data_map[n.replace("/", "\\").lower()] = (n, b)

    merged_data = list(data_entries)
    for n, b in data_repl.items():
        i = find_index(merged_data, n)
        merged_data[i] = (merged_data[i][0], b)
    last = last_objects(merged_data)
    orig_last = last_objects(data_entries)

    for obj in FROZEN_OBJECTS:
        if last[obj] != orig_last[obj]:
            raise SystemExit(f"frozen object changed: {obj}")

    # JP/SK/VN barracks chain
    expect_barracks = {
        "Japan_Barracks": "JP__JPFlag_Hs",
        "SouthKorea_Barracks": "SK__SKFlag_Hs",
        "Vietnam_Barracks": "VN__VNFlag_Hs",
    }
    for obj, flag in expect_barracks.items():
        body = last[obj]
        if flag not in body or "HideSubObject" not in body or "irq_camp" not in body:
            raise SystemExit(f"{obj} barracks chain broken")
        tex = { "JP__JPFlag_Hs": b"JP_Flag.tga", "SK__SKFlag_Hs": b"SK_Flag.tga", "VN__VNFlag_Hs": b"VN_Flag.tga"}[flag]
        w3d_key = f"art\\w3d\\{flag.lower()}.w3d"
        if w3d_key not in art_map:
            raise SystemExit(f"missing {flag} W3D")
        if tex not in art_map[w3d_key][1]:
            raise SystemExit(f"{flag} missing texture {tex}")

    # Iran
    tga_key = r"art\textures\ir_flag.tga"
    if tga_key not in art_map:
        raise SystemExit("missing IR_Flag.tga")
    tga = art_map[tga_key][1]
    if len(tga) != 32786 or tga[12:16] != bytes([128, 0, 64, 0]):
        raise SystemExit("IR_Flag.tga header/size mismatch")

    for packed, obj, kind, hide in TARGETS:
        model = model_name(kind)
        body = last[obj]
        if model not in body or "ModuleTag_03" not in body:
            raise SystemExit(f"{obj}: missing {model}")
        if hide and "FPOLE" not in body:
            raise SystemExit(f"{obj}: missing FPOLE hide")
        if obj != "IranPowerplant" and "FPOLE" in body:
            raise SystemExit(f"{obj}: unexpected FPOLE hide")
        w3d_key = f"art\\w3d\\{model.lower()}.w3d"
        if w3d_key not in art_map:
            raise SystemExit(f"missing {model}.W3D")
        blob = art_map[w3d_key][1]
        if len(blob) != 20341:
            raise SystemExit(f"{model} size {len(blob)}")
        if b"IR_Flag.tga" not in blob or b"IraqiFlag" in blob:
            raise SystemExit(f"{model} texture wrong")
        got = read_line01(blob)
        exp = LINE01[kind]
        if any(abs(a - b) > 1e-3 for a, b in zip(got, exp)):
            raise SystemExit(f"{model} LINE01 {got} != {exp}")

    # no duplicate art names
    names = [n.replace("/", "\\").lower() for n, _ in art_entries]
    names += [n.replace("/", "\\").lower() for n in art_add]
    if len(names) != len(set(names)):
        raise SystemExit("duplicate ART names")

    print("STATIC VALIDATION: PASS")
    print("  JP/SK/VN Barracks unchanged and still correct")
    print("  Iran 5 objects (Barracks/Camp same) + 5 Flag_Hs + IR_Flag.tga")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", action="store_true", help="write complete replacement BIGs after payload")
    args = ap.parse_args()

    if sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    art_entries = read_big(SRC_ART)
    data_entries = read_big(SRC_DATA)
    donor = art_entries[find_index(art_entries, P_DONOR)][1]
    if len(donor) != 20341:
        raise SystemExit(f"donor size {len(donor)}")

    ir_flag = write_iran_flag_tga()
    art_add = {r"Art\Textures\IR_Flag.tga": ir_flag}
    for kind, xyz in LINE01.items():
        model = model_name(kind)
        blob = make_flag_hs(donor, hier_name(model), b"IR_Flag.tga", xyz)
        art_add[rf"Art\W3D\{model}.W3D"] = blob
        print(f"ART {model}.W3D LINE01={xyz}")

    # patch DATA files
    by_file: dict[str, list] = {}
    for packed, obj, kind, hide in TARGETS:
        by_file.setdefault(packed, []).append((obj, kind, hide))

    data_repl = {}
    data_work = list(data_entries)
    for packed, jobs in by_file.items():
        idx = find_index(data_work, packed)
        old_name, old_blob = data_work[idx]
        text = old_blob.decode("latin1", errors="replace")
        new_text = patch_file(text, jobs)
        new_blob = new_text.encode("latin1", errors="replace")
        data_work[idx] = (old_name, new_blob)
        data_repl[old_name] = new_blob
        print(f"DATA {old_name}")

    write_payload(art_add, data_repl)
    validate(art_entries, data_entries, art_add, data_repl)

    RELEASE.mkdir(parents=True, exist_ok=True)
    (RELEASE / "AUDIT.txt").write_text(
        "IRAN_BUILDING_FLAGS\n"
        f"SOURCE_DATA_SHA = {EXPECTED_DATA_SHA}\n"
        f"SOURCE_ART_SHA = {EXPECTED_ART_SHA}\n"
        "JP_SK_VN_BARRACKS = UNCHANGED (already correct Flag_Hs + national TGA)\n"
        "IRAN_ROOT_CAUSE = missing IR_Flag.tga, missing Flag_Hs W3Ds, missing Draw ModuleTag_03\n"
        "IRAN_TEXTURE = Art\\Textures\\IR_Flag.tga (128x64 32bpp, same header as JP/SK/VN_Flag)\n"
        "IRAN_MESHES = IR__IRFlag_Hs{CP,CU,WF,PP,SC} cloned from Irq__IqFlag_Hs\n"
        "IRAN_OBJECTS = IranBarracks (Camp+Barracks), IranCommandCenter, IranWarFactory, IranPowerplant, IranSupplyCenter\n"
        "DATA_REQUIRED = YES (buildings had no flag Draw)\n"
        "INGAME_TESTED = NO\n",
        encoding="utf-8",
    )

    if args.pack:
        # ART: append new files (do not replace existing)
        packed_art = list(art_entries) + [(n, b) for n, b in art_add.items()]
        packed_data = data_work
        art_out = RELEASE / "_SPEC_ART_ONE.big"
        data_out = RELEASE / "_SPEC_DATA_ONE.big"
        art_out.write_bytes(build_big_ordered(packed_art))
        data_out.write_bytes(build_big_ordered(packed_data))
        print("PACKED", art_out, sha256_file(art_out), "bytes", art_out.stat().st_size)
        print("PACKED", data_out, sha256_file(data_out), "bytes", data_out.stat().st_size)
        (RELEASE / "SHA256.txt").write_text(
            f"_SPEC_ART_ONE.big  {sha256_file(art_out)}\n"
            f"_SPEC_DATA_ONE.big {sha256_file(data_out)}\n",
            encoding="utf-8",
        )
    else:
        print("Payload written; BIGs not packed (pass --pack after validation).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
