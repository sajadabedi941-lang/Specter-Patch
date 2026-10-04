#!/usr/bin/env python3
"""Fix JP/SK/VN Power Plant NK flags and 3x approved Flag_Hs meshes.

DATA: neutralize duplicate Buildings\\Iraq_PowerPlant.ini objects that still
use NKor_Powerplant. Replace those objects with the same country's Systems.ini
Power Plant (Iraq_Powerplant + hide + country Flag_HsPP).

ART: uniformly enlarge country-specific Flag_Hs clones by 3x (cloth width/height
and pole length from the pole base). Do not scale Irq__IqFlag_Hs or NKr__NKFlag_Hs.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/CC_START_BUILD_MATCH/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/IRAN_BUILDING_FLAGS/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "03526c0ea0c7b2b1d87528284cf01f933a47953a21d9c4e73e84cfc6fa1f8a89"
EXPECTED_ART_SHA = "ec4f5bdcc8f9e9171a8d9fb0d9523cffa41089eded03b330f0f1738aaf555760"
RELEASE = Path("/workspace/patch/Release/PP_FLAG_SIZE_3X")
PAYLOAD = RELEASE / "payload"
SCALE = 3.0

PP_DUPES = [
    {
        "id": "Japan",
        "obj": "Japan_PowerPlant",
        "dupe": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_PowerPlant.ini",
        "canon": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Japan_Systems.ini",
        "flag": "JP__JPFlag_HsPP",
        "tex": b"JP_Flag.tga",
    },
    {
        "id": "SouthKorea",
        "obj": "SouthKorea_PowerPlant",
        "dupe": r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\Iraq_PowerPlant.ini",
        "canon": r"Data\INI\Object\Specter\South Korean Armed Forces\SouthKorea_Systems.ini",
        "flag": "SK__SKFlag_HsPP",
        "tex": b"SK_Flag.tga",
    },
    {
        "id": "Vietnam",
        "obj": "Vietnam_PowerPlant",
        "dupe": r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_PowerPlant.ini",
        "canon": r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Vietnam_Systems.ini",
        "flag": "VN__VNFlag_HsPP",
        "tex": b"VN_Flag.tga",
    },
]

SCALE_PREFIXES = (
    "jp__",
    "sk__",
    "vn__",
    "in__",
    "pk__",
    "ly__",
    "sy__",
    "ae__",
    "sa__",
    "za__",
    "tr__",
    "it__",
    "se__",
    "uk__",
    "fr__",
    "de__",
    "ua__",
    "ir__",
)
SKIP_FLAG_HS = ("irq__", "nkr__")

FROZEN_OBJECTS = [
    "NorthKorea_PowerPlant",
    "Iraq_PowerPlant",
    "India_PowerPlant",
    "Japan_Barracks",
    "SouthKorea_Barracks",
    "Vietnam_Barracks",
    "IranCommandCenter",
    "SaudiArabia_CommandCenter",
]

FROZEN_ART = [
    r"Art\W3D\Irq__IqFlag_Hs.W3D",
    r"Art\W3D\NKr__NKFlag_Hs.W3D",
    r"Art\W3D\NKor_Powerplant.W3D",
    r"Art\W3D\Iraq_Powerplant.W3D",
    r"Art\Textures\DPRK_Flag.tga",
]

FROZEN_FILES = [
    r"Data\INI\CommandSet_ZZZZ_OilCapture_SoldierCommand.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\CommandSet_ZZZZ_CommandCenterMatchStart.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\Object\Specter\North Korea\NorthKorea_Systems.ini",
]

OBJ_RE = re.compile(r"(?im)^Object\s+(\S+)")
PIVOTS = 0x00000102
MESH = 0x00000000
VERTS = 0x00000002
MESH_HEADER3 = 0x0000001F


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


def object_spans(text: str):
    ms = list(OBJ_RE.finditer(text))
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        out.append((m.group(1), m.start(), end))
    return out


def extract_object(text: str, obj: str) -> str:
    for name, start, end in object_spans(text):
        if name == obj:
            return text[start:end]
    raise SystemExit(f"object {obj} missing")


def replace_object(text: str, obj: str, new_body: str) -> str:
    for name, start, end in object_spans(text):
        if name == obj:
            return text[:start] + new_body + text[end:]
    raise SystemExit(f"object {obj} missing in dupe file")


def last_objects(entries):
    last = {}
    last_src = {}
    for name, blob in entries:
        if not name.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        for obj, start, end in object_spans(text):
            last[obj] = text[start:end]
            last_src[obj] = name
    return last, last_src


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


def mesh_bounds(blob: bytes):
    out = {}
    pos = 0
    while pos + 8 <= len(blob):
        ctype, raw = struct.unpack_from("<II", blob, pos)
        size = raw & 0x7FFFFFFF
        has_sub = bool(raw & 0x80000000)
        ds, de = pos + 8, min(pos + 8 + size, len(blob))
        if ctype == MESH and has_sub:
            mesh = None
            verts = []
            for c2, s2, e2, h2 in walk_chunks(blob, ds, de):
                if c2 == MESH_HEADER3 and not h2:
                    mesh = blob[s2 + 8 : s2 + 24].split(b"\x00", 1)[0].decode("latin1")
                if c2 == VERTS and not h2:
                    n = (e2 - s2) // 12
                    for i in range(n):
                        verts.append(struct.unpack_from("<fff", blob, s2 + i * 12))
            if mesh and verts:
                ys = [v[1] for v in verts]
                xs = [v[0] for v in verts]
                zs = [v[2] for v in verts]
                out[mesh] = {
                    "n": len(verts),
                    "xmin": min(xs),
                    "xmax": max(xs),
                    "ymin": min(ys),
                    "ymax": max(ys),
                    "zmin": min(zs),
                    "zmax": max(zs),
                }
        pos = de
    return out


def read_line01_pivot(blob: bytes):
    for ctype, ds, de, has_sub in walk_chunks(blob):
        if ctype != PIVOTS or has_sub:
            continue
        for i in range((de - ds) // 60):
            off = ds + i * 60
            name = bytes(blob[off : off + 16]).split(b"\x00", 1)[0]
            if name == b"LINE01":
                return struct.unpack_from("<fff", blob, off + 20)
    raise SystemExit("LINE01 pivot missing")


def scale_flag_hs(blob: bytes, factor: float = SCALE) -> bytes:
    bounds = mesh_bounds(blob)
    if "LINE01" not in bounds or "FLAG03" not in bounds:
        raise SystemExit("Flag_Hs missing LINE01/FLAG03")
    ybase = bounds["LINE01"]["ymin"]
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
    for ctype, ds, de, has_sub in walk_chunks(out):
        if ctype != PIVOTS or has_sub:
            continue
        for i in range((de - ds) // 60):
            off = ds + i * 60
            name = bytes(out[off : off + 16]).split(b"\x00", 1)[0]
            if name in (b"FLAG01", b"FLAG02", b"FLAG03", b"HOUSECOLOR01", b"HOUSECOLOR02", b"HOUSECOLOR03"):
                x, y, z = struct.unpack_from("<fff", out, off + 20)
                y = (y - ybase) * factor + ybase
                struct.pack_into("<fff", out, off + 20, x, y, z)
    if len(out) != len(blob):
        raise SystemExit("W3D size changed")
    return bytes(out)


def should_scale(name: str) -> bool:
    ln = name.replace("/", "\\").lower()
    if not ln.startswith("art\\w3d\\") or "flag_hs" not in ln:
        return False
    base = ln.split("\\")[-1]
    if any(base.startswith(p) for p in SKIP_FLAG_HS):
        return False
    return any(base.startswith(p) for p in SCALE_PREFIXES)


def write_payload(repl: dict[str, bytes]) -> None:
    if PAYLOAD.exists():
        for p in PAYLOAD.rglob("*"):
            if p.is_file():
                p.unlink()
    for name, blob in repl.items():
        dest = PAYLOAD / name.replace("\\", "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)


def validate(orig_art, orig_data, new_art, new_data) -> None:
    orig_last, _ = last_objects(orig_data)
    new_last, new_src = last_objects(new_data)
    for obj in FROZEN_OBJECTS:
        if obj in ("Japan_Barracks", "SouthKorea_Barracks", "Vietnam_Barracks", "IranCommandCenter", "SaudiArabia_CommandCenter"):
            if new_last[obj] != orig_last[obj]:
                raise SystemExit(f"frozen object changed: {obj}")
        if obj == "NorthKorea_PowerPlant":
            if "NKor_Powerplant" not in new_last[obj]:
                raise SystemExit("NK Power Plant lost NKor_Powerplant")
            if new_last[obj] != orig_last[obj]:
                raise SystemExit("NorthKorea_PowerPlant changed")
        if obj == "Iraq_PowerPlant" and new_last[obj] != orig_last[obj]:
            raise SystemExit("Iraq_PowerPlant changed")

    orig_data_map = {n.replace("/", "\\").lower(): b for n, b in orig_data}
    new_data_map = {n.replace("/", "\\").lower(): b for n, b in new_data}
    for packed in FROZEN_FILES:
        key = packed.replace("/", "\\").lower()
        if orig_data_map[key] != new_data_map[key]:
            raise SystemExit(f"frozen DATA file changed: {packed}")

    orig_art_map = {n.replace("/", "\\").lower(): b for n, b in orig_art}
    new_art_map = {n.replace("/", "\\").lower(): (n, b) for n, b in new_art}
    for packed in FROZEN_ART:
        key = packed.replace("/", "\\").lower()
        if orig_art_map[key] != new_art_map[key][1]:
            raise SystemExit(f"frozen ART changed: {packed}")

    for c in PP_DUPES:
        body = new_last[c["obj"]]
        if "NKor_Powerplant" in body or "DPRK_Flag" in body or "NKr__NKFlag" in body:
            raise SystemExit(f"{c['obj']} still references NK flag assets")
        if c["flag"] not in body or "Iraq_Powerplant" not in body:
            raise SystemExit(f"{c['obj']} missing correct Flag_HsPP/Iraq mesh")
        if "HideSubObject" not in body or "FLAG01" not in body:
            raise SystemExit(f"{c['obj']} missing hide")
        # both definitions must be clean
        for packed in (c["dupe"], c["canon"]):
            text = new_data_map[packed.replace("/", "\\").lower()].decode("latin1", errors="replace")
            obj_body = extract_object(text, c["obj"])
            if "NKor_Powerplant" in obj_body:
                raise SystemExit(f"{packed} still has NKor_Powerplant")
            if c["flag"] not in obj_body:
                raise SystemExit(f"{packed} missing {c['flag']}")
        w3d_key = f"art\\w3d\\{c['flag'].lower()}.w3d"
        if c["tex"] not in new_art_map[w3d_key][1]:
            raise SystemExit(f"{c['flag']} lost {c['tex']}")

    scaled = 0
    for n, b in new_art:
        if not should_scale(n):
            continue
        scaled += 1
        old = orig_art_map[n.replace("/", "\\").lower()]
        if read_line01_pivot(old) != read_line01_pivot(b):
            raise SystemExit(f"{n}: LINE01 pivot changed")
        if len(old) != len(b):
            raise SystemExit(f"{n}: size changed")
        if b"IraqiFlag" in b or b"DPRK_Flag" in b:
            raise SystemExit(f"{n}: wrong flag texture leak")
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
    if scaled < 80:
        raise SystemExit(f"expected >=80 scaled Flag_Hs, got {scaled}")

    print("STATIC VALIDATION: PASS")
    print(f"  JP/SK/VN Power Plant dupe objects neutralized ({len(PP_DUPES)})")
    print("  NorthKorea_PowerPlant unchanged")
    print(f"  Flag_Hs meshes scaled {SCALE}x: {scaled}")
    print("  LINE01 attachment pivots unchanged; flag proportions preserved")


def write_docs(data_sha: str, art_sha: str, scaled: int) -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)
    (RELEASE / "AUDIT.txt").write_text(
        "PP_FLAG_SIZE_3X\n"
        f"SOURCE_DATA_SHA = {EXPECTED_DATA_SHA}\n"
        f"SOURCE_ART_SHA = {EXPECTED_ART_SHA}\n"
        "PP_ROOT_CAUSE = duplicate Object in Buildings\\Iraq_PowerPlant.ini uses NKor_Powerplant "
        "with no HideSubObject (SK also attached barracks SK__SKFlag_Hs).\n"
        "PP_FIX = copy each country's Systems.ini Power Plant object over the dupe file.\n"
        "SIZE = Flag_Hs cloth XYZ * 3; pole length * 3 from LINE01 ymin; LINE01 pivot unchanged.\n"
        f"SCALED_W3D = {scaled}\n"
        "SKIP = Irq__IqFlag_Hs NKr__NKFlag_Hs NKor_Powerplant Iraq_Powerplant\n"
        "INGAME_TESTED = NO\n",
        encoding="utf-8",
    )
    (RELEASE / "CHANGED_FILES.txt").write_text(
        "DATA replaced\n"
        + "\n".join(f"  {c['dupe']}" for c in PP_DUPES)
        + "\nART replaced\n  country-specific *Flag_Hs*.W3D (3x scale, same filenames)\n"
        "ART skipped\n  Irq__IqFlag_Hs.W3D  NKr__NKFlag_Hs.W3D  building meshes\n",
        encoding="utf-8",
    )
    (RELEASE / "CHANGELOG.txt").write_text(
        "PP_FLAG_SIZE_3X\n\n"
        "Japan/South Korea/Vietnam Power Plants no longer last-win (or first-win) to\n"
        "NKor_Powerplant. Both Object definitions now use Iraq_Powerplant + hide + Flag_HsPP.\n"
        "Approved country Flag_Hs meshes are 3x larger (cloth and pole). Attachment pivots\n"
        "and textures are unchanged. North Korea Power Plant is unchanged.\n"
        "In-game test: NOT PERFORMED.\n",
        encoding="utf-8",
    )
    if data_sha and art_sha:
        (RELEASE / "SHA256.txt").write_text(
            f"_SPEC_DATA_ONE.big {data_sha}\n"
            f"_SPEC_ART_ONE.big  {art_sha}\n",
            encoding="utf-8",
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", action="store_true")
    args = ap.parse_args()
    if sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    art_entries = read_big(SRC_ART)
    data_entries = read_big(SRC_DATA)
    data_work = list(data_entries)
    art_work = list(art_entries)
    repl: dict[str, bytes] = {}

    for c in PP_DUPES:
        canon_i = find_index(data_work, c["canon"])
        dupe_i = find_index(data_work, c["dupe"])
        canon_text = data_work[canon_i][1].decode("latin1", errors="replace")
        dupe_text = data_work[dupe_i][1].decode("latin1", errors="replace")
        canon_obj = extract_object(canon_text, c["obj"])
        if c["flag"] not in canon_obj:
            raise SystemExit(f"{c['id']} Systems.ini missing {c['flag']}")
        new_dupe = replace_object(dupe_text, c["obj"], canon_obj)
        blob = new_dupe.encode("latin1", errors="replace")
        data_work[dupe_i] = (data_work[dupe_i][0], blob)
        repl[data_work[dupe_i][0]] = blob
        print("DATA", c["id"], data_work[dupe_i][0])

    scaled = 0
    for i, (name, blob) in enumerate(art_work):
        if not should_scale(name):
            continue
        new_blob = scale_flag_hs(blob)
        art_work[i] = (name, new_blob)
        repl[name] = new_blob
        scaled += 1
    print(f"ART scaled Flag_Hs: {scaled}")

    write_payload(repl)
    validate(art_entries, data_entries, art_work, data_work)
    write_docs("", "", scaled)

    if args.pack:
        data_out = RELEASE / "_SPEC_DATA_ONE.big"
        art_out = RELEASE / "_SPEC_ART_ONE.big"
        data_out.write_bytes(build_big_ordered(data_work))
        art_out.write_bytes(build_big_ordered(art_work))
        dsha = sha256_file(data_out)
        asha = sha256_file(art_out)
        print("PACKED", data_out, dsha, data_out.stat().st_size)
        print("PACKED", art_out, asha, art_out.stat().st_size)
        write_docs(dsha, asha, scaled)

        packed_d = {n.replace("/", "\\").lower(): b for n, b in read_big(data_out)}
        src_d = {n.replace("/", "\\").lower(): b for n, b in data_entries}
        changed_d = sorted(k for k in src_d if packed_d[k] != src_d[k])
        expect_d = {c["dupe"].replace("/", "\\").lower() for c in PP_DUPES}
        if set(changed_d) != expect_d or set(packed_d) != set(src_d):
            raise SystemExit(f"DATA scope fail {changed_d}")
        packed_a = {n.replace("/", "\\").lower(): b for n, b in read_big(art_out)}
        src_a = {n.replace("/", "\\").lower(): b for n, b in art_entries}
        name_by_key = {n.replace("/", "\\").lower(): n for n, _ in art_entries}
        changed_a = [k for k in src_a if packed_a[k] != src_a[k]]
        if set(packed_a) != set(src_a):
            raise SystemExit("ART keys changed")
        bad = [k for k in changed_a if not should_scale(name_by_key[k])]
        if bad:
            raise SystemExit(f"unexpected ART changes {bad}")
        print(f"POST-PACK SCOPE: PASS (3 DATA INIs, {len(changed_a)} Flag_Hs W3Ds)")
    else:
        print("Payload written; BIGs not packed (pass --pack after validation).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
