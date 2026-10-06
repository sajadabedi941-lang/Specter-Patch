#!/usr/bin/env python3
"""Fix invisible Iraqi strategic TELs by renaming cloned W3D HLod names.

Authority ART: SPECTER_IRAQ_COMPLETE/_SPEC_ART_ONE.big (current live s ART).
Authority DATA: SPECTER_IRAQ_FACTORY_COMMANDSET/_SPEC_DATA_ONE.big (not modified).

Root cause: cloned IQ_* W3D files were registered under donor HLod names
(IRQ_9P117, IRQ_SARAB7, ...). INI Model= IQ_*TEL looks up that exact HLod
name, misses, and the drawable is empty.

Patch HLod header Name to the filename stem when the stem fits in the
16-byte W3D name field (15 chars + NUL). HierarchyName and animations
stay on the donor names so existing Animation= lines keep working.

Does not modify DATA, shared donor W3Ds, or shared atlases.
Static validation only. Not an in-game runtime test.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

ROOT = Path("/workspace")
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_COMPLETE/_SPEC_ART_ONE.big"
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_COMMANDSET/_SPEC_DATA_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_TEL_VISIBLE"

HLOD_HEADER = 0x00000701
W3D_NAME_LEN = 16

DEFAULT_TELS = [
    "IQ_AlHusseinTEL",
    "IQ_AlHijarahTEL",
    "IQ_AlAbbasTEL",
    "IQ_Badr2000TEL",
    "IQ_AlSamoudTEL",
    "IQ_Ababil100TEL",
    "IQ_Tammuz1TEL",
    "IQ_AlAbidTEL",
]
DEFAULT_MSL = [
    "IQ_AlHusseinMSL",
    "IQ_AlHijarahMSL",
    "IQ_AlAbbasMSL",
    "IQ_Badr2000MSL",
    "IQ_AlSamoudMSL",
    "IQ_Ababil100MSL",
    "IQ_Tammuz1MSL",
    "IQ_AlAbidMSL",
]


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes):
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
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


def walk_chunks(blob: bytes, start: int = 0, end: int | None = None):
    if end is None:
        end = len(blob)
    pos = start
    while pos + 8 <= end:
        cid, raw = struct.unpack_from("<II", blob, pos)
        sz = raw & 0x7FFFFFFF
        cont = bool(raw & 0x80000000)
        cs, ce = pos + 8, pos + 8 + sz
        if ce > end + 8:
            break
        yield cid, cont, pos, cs, min(ce, len(blob))
        if cont:
            yield from walk_chunks(blob, cs, min(ce, end))
        pos = ce


def zstr(buf: bytes) -> str:
    return buf.split(b"\x00", 1)[0].decode("latin1", errors="replace")


def hlod_name(blob: bytes) -> str | None:
    for cid, _cont, _pos, cs, ce in walk_chunks(blob):
        if cid == HLOD_HEADER and ce - cs >= 40:
            return zstr(blob[cs + 8 : cs + 24])
    return None


def patch_hlod_name(blob: bytes, new_name: str) -> tuple[bytes, bool]:
    if len(new_name) >= W3D_NAME_LEN:
        return blob, False
    padded = new_name.encode("ascii") + b"\x00" * (W3D_NAME_LEN - len(new_name))
    out = bytearray(blob)
    changed = False
    for cid, _cont, _pos, cs, ce in walk_chunks(blob):
        if cid == HLOD_HEADER and ce - cs >= 40:
            if bytes(out[cs + 8 : cs + 24]) != padded:
                out[cs + 8 : cs + 24] = padded
                changed = True
    return bytes(out), changed


def w3d_key(stem: str) -> str:
    return f"Art\\W3D\\{stem}.W3D"


def find_ci(files: dict[str, bytes], key: str) -> str | None:
    lk = key.replace("/", "\\").lower()
    for k in files:
        if k.replace("/", "\\").lower() == lk:
            return k
    return None


def validate(art: dict[str, bytes], src_art: dict[str, bytes], data: dict[str, bytes]) -> list[str]:
    fails = []
    patched = []
    skipped_long = []
    for k, blob in art.items():
        lk = k.replace("/", "\\").lower()
        if not lk.startswith("art\\w3d\\iq_") or not lk.endswith(".w3d"):
            continue
        stem = Path(k.replace("\\", "/")).stem
        name = hlod_name(blob)
        if len(stem) >= W3D_NAME_LEN:
            skipped_long.append((stem, name))
            continue
        if name != stem:
            fails.append(f"HLod {name!r} != stem {stem}")
        else:
            patched.append(stem)
        texes = set()
        for cid, _c, _p, cs, ce in walk_chunks(blob):
            if cid == 0x00000032:
                texes.add(zstr(blob[cs:ce]))
        for tex in texes:
            tkey = find_ci(art, f"Art\\Textures\\{tex}")
            if tkey is None:
                # engine also accepts .dds for .tga
                alt = tex[:-4] + ".dds" if tex.lower().endswith(".tga") else tex[:-4] + ".tga"
                if find_ci(art, f"Art\\Textures\\{alt}") is None:
                    fails.append(f"{stem} missing texture {tex}")

    for stem in DEFAULT_TELS + DEFAULT_MSL:
        if find_ci(art, w3d_key(stem)) is None:
            fails.append(f"missing required W3D {stem}")
        else:
            key = find_ci(art, w3d_key(stem))
            if hlod_name(art[key]) != stem:
                fails.append(f"{stem} HLod not renamed")

    # donor W3Ds must remain byte-identical
    for donor in [
        "Irq_9P117",
        "Irq_9P117D",
        "Irq_R11_M",
        "Irq_Abbas_L",
        "RUS_9K720K",
        "Irq_Sarab7",
        "Irq_Lamiaa",
        "Iraq_Alhusain_L",
        "RUS_RS24",
        "GENERIC-MISSILES.dds",
        "AAM-GENTEX.dds",
        "KH-GENTEX.dds",
    ]:
        if donor.endswith(".dds"):
            sk = find_ci(src_art, f"Art\\Textures\\{donor}")
            dk = find_ci(art, f"Art\\Textures\\{donor}")
        else:
            sk = find_ci(src_art, w3d_key(donor))
            dk = find_ci(art, w3d_key(donor))
        if sk is None or dk is None:
            fails.append(f"donor missing {donor}")
        elif src_art[sk] != art[dk]:
            fails.append(f"donor mutated {donor}")

    # IQ files: only W3D HLod bytes may change; textures identical; no extras
    extra = [k for k in art if k not in src_art]
    missing = [k for k in src_art if k not in art]
    if extra:
        fails.append(f"extra ART files {extra[:5]}")
    if missing:
        fails.append(f"missing ART files {missing[:5]}")

    # DATA must be the locked factory+parse baseline and unused here
    proj = data[r"Data\INI\Object\Specter\Iraq Army\Iraq_StrategicMissile_Projectiles.ini"]
    if proj.count(b"MissileAIUpdate") != 8:
        fails.append("DATA parse fix lost")
    core = data[r"Data\INI\CommandSet.ini"].decode("latin1")
    if core.count("CommandSet Iraq_MissileFactoryCommandSet") != 1:
        fails.append("factory CommandSet not in core")
    if "1  = Command_ConstructIraq_Ababil100_New" not in core:
        fails.append("factory slot 1 lost")

    later = []
    seen = set()
    for name in sorted(art, key=lambda n: n.lower()):
        ln = name.replace("/", "\\").lower()
        if ln.startswith("art\\w3d\\iq_") and ln.endswith(".w3d"):
            stem = Path(name.replace("\\", "/")).stem.lower()
            if stem in seen:
                later.append(name)
            seen.add(stem)
    if later:
        fails.append(f"duplicate IQ W3D last-wins {later}")

    return fails, patched, skipped_long


def main() -> int:
    if not SRC_ART.is_file():
        raise SystemExit(f"missing current s ART {SRC_ART}")
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing current s DATA {SRC_DATA}")

    src_art = parse_big(SRC_ART.read_bytes())
    art = dict(src_art)
    data = parse_big(SRC_DATA.read_bytes())

    notes = []
    for k, blob in list(art.items()):
        lk = k.replace("/", "\\").lower()
        if not lk.startswith("art\\w3d\\iq_") or not lk.endswith(".w3d"):
            continue
        stem = Path(k.replace("\\", "/")).stem
        if len(stem) >= W3D_NAME_LEN:
            notes.append(f"SKIP long stem {stem} (W3D name field is 15 chars)")
            continue
        old = hlod_name(blob)
        patched, changed = patch_hlod_name(blob, stem)
        if changed:
            art[k] = patched
            notes.append(f"HLod {old} -> {stem} in {k}")
        elif old != stem:
            notes.append(f"FAILED {k} still {old}")

    packed = build_big(art)
    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_ART_ONE.big"
    out_big.write_bytes(packed)

    extracted = parse_big(packed)
    fails, patched, skipped = validate(extracted, src_art, data)

    report = [
        "# Iraq strategic TEL visibility ART fix",
        "",
        "Static validation only. The game was not launched.",
        "",
        "## Exact root cause",
        "",
        "All 8 constructed TEL Objects use `Model = IQ_<Name>TEL`.",
        "Those W3D files existed in the live ART BIG, but their HLod",
        "prototype names were still the donor names (IRQ_9P117, IRQ_ABBAS_L,",
        "RUS_9K720K, IRQ_SARAB7, IRQ_LAMIAA, IRAQ_ALHUSAIN_L, RUS_RS24).",
        "WW3D `Create_Render_Obj(Model)` looks up the HLod by that string,",
        "not the filename. The lookup misses, the drawable is empty, and the",
        "unit is invisible. All 8 units were affected. Draw modules and",
        "donor Animation= lines were already structurally valid.",
        "",
        "## Fix",
        "",
        "Patched only the HLod header Name inside each cloned IQ_* W3D whose",
        "filename stem is <= 15 characters so it matches `Model=`.",
        "HierarchyName / animation names stay on the donor so INI",
        "Animation=Irq_9P117.Irq_9P117 etc. still resolve.",
        "Shared donor W3Ds and shared atlases were not modified.",
        "DATA was not modified (parse fix + factory CommandSet intact).",
        "",
        "## Pack",
        "",
        f"- ART path: `{out_big}`",
        f"- ART size: {out_big.stat().st_size}",
        f"- ART SHA256: {sha256_path(out_big)}",
        f"- files: {len(art)}",
        "- DATA: unchanged (s-iraq-factory-commandset)",
        "",
        "## HLod patches",
        "",
    ]
    report.extend(f"- {n}" for n in notes)
    report.append("")
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
        print("\n".join(report))
        return 1
    report += [
        "## VALIDATION PASS",
        f"- patched HLod names: {len(patched)}",
        f"- long stems left on donor HLod (16-char TELD/TELR): {len(skipped)}",
        "- all 8 default TEL W3Ds exist and HLod==Model stem",
        "- all 8 projectile MSL W3Ds exist and HLod==Model stem",
        "- cloned W3D textures resolve",
        "- donor W3Ds / shared atlases byte-identical",
        "- no extra/missing ART paths; no IQ W3D last-wins dupes",
        "- DATA parse fix MissileAIUpdate x8 unchanged",
        "- DATA factory CommandSet in core CommandSet.ini unchanged",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
    (OUT / "README.txt").write_text(
        "SPECTER Iraq strategic TEL visibility ART fix\n"
        "\n"
        "Install this _SPEC_ART_ONE.big over current live s ART.\n"
        "Keep the current live s DATA (s-iraq-factory-commandset).\n"
        "Do not replace DATA.\n"
        "\n"
        "Static validation only. The game was not launched in this environment.\n",
        encoding="ascii",
    )
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
