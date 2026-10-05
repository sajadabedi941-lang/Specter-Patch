#!/usr/bin/env python3
"""Pack Iraqi Missile Factory into the live s-baseline SPEC BIGs.

Reads the current s _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big (does not rebuild
from old PRs). Adds only the missile-factory DATA/ART. Does not import
abarfrccmd* and does not replace Irq_WarFactory.W3D.

Do NOT mutate Data\\INI\\CommandSet.ini. Live s CommandSet.ini never
references a CommandButton that exists only in an extra CommandButton_*.ini;
doing so leaves Iraq_VT72BCommandSet slot 14 unresolved and crashes the
command bar. Slot 14 is last-won by CommandSet_Iraq_MissileFactory.ini after
CommandButton_Iraq_MissileFactory.ini is loaded.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
S_DATA = Path("/tmp/s-bigs/_SPEC_DATA_ONE.big")
S_ART = Path("/tmp/s-bigs/_SPEC_ART_ONE.big")
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_FACTORY_FIX_FINAL"
DONOR_W3D = Path("/tmp/iqmiss-donor")
DONOR_TEX = Path("/tmp/iqmiss-donor/textures")
PATCH_DATA = ROOT / "patch/Data"

CSF_LABELS = {
    "CONTROLBAR:ConstructIraqMissileFactory": "Missile Factory",
    "CONTROLBAR:ToolTipIraqBuildMissileFactory": "Build Missile Factory. Produces R-11 Scud, SA-6, BM-21 and Al-Hussin.",
    "OBJECT:IraqMissileFactory": "Missile Factory",
}

ART_IMPORTS = [
    ("Art\\W3D\\LSFIQMCheChang.W3D", DONOR_W3D / "LSFIQMCheChang.W3D"),
    ("Art\\W3D\\LSFIQMCheChangd.W3D", DONOR_W3D / "LSFIQMCheChangd.W3D"),
    ("Art\\W3D\\LSFIQMCheChange.W3D", DONOR_W3D / "LSFIQMCheChange.W3D"),
    ("Art\\W3D\\LSFMCheChangCB.W3D", DONOR_W3D / "LSFMCheChangCB.W3D"),
    ("Art\\Textures\\Camo net.tga", DONOR_TEX / "Camo net.tga"),
    ("Art\\Textures\\Camo netd.tga", DONOR_TEX / "Camo netd.tga"),
    ("Art\\Textures\\Camo netk.tga", DONOR_TEX / "Camo netk.tga"),
    ("Art\\Textures\\LSFChinaBase.tga", DONOR_TEX / "LSFChinaBase.tga"),
    ("Art\\Textures\\LSFChinaBased.tga", DONOR_TEX / "LSFChinaBased.tga"),
    ("Art\\Textures\\LSFChinaBasee.tga", DONOR_TEX / "LSFChinaBasee.tga"),
    ("Art\\Textures\\LSFDF11M.tga", DONOR_TEX / "LSFDF11M.tga"),
    ("Art\\Textures\\LSFDF11Md.tga", DONOR_TEX / "LSFDF11Md.tga"),
    ("Art\\Textures\\LSFDustPaoDao.tga", DONOR_TEX / "LSFDustPaoDao.tga"),
    ("Art\\Textures\\LSFDustPaoDaod.tga", DONOR_TEX / "LSFDustPaoDaod.tga"),
    ("Art\\Textures\\LSFDustPaoDaoe.tga", DONOR_TEX / "LSFDustPaoDaoe.tga"),
    ("Art\\Textures\\YILAKE.tga", DONOR_TEX / "YILAKE.tga"),
    ("Art\\Textures\\YILAKEd.tga", DONOR_TEX / "YILAKEd.tga"),
]


def sha256(path: Path) -> str:
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


def csf_append(csf: bytes, labels: dict[str, str]) -> bytes:
    if csf[:4] != b" FSC":
        raise SystemExit(f"unexpected CSF magic {csf[:4]!r}")
    magic, ver, nlab, nstr, unused, lang = struct.unpack_from("<4sIIIII", csf, 0)
    existing = set()
    pos = 24
    while pos < len(csf):
        if csf[pos : pos + 4] != b" LBL":
            break
        pos += 4
        cnt, nlen = struct.unpack_from("<II", csf, pos)
        pos += 8
        name = csf[pos : pos + nlen].decode("latin1")
        pos += nlen
        existing.add(name)
        for _ in range(cnt):
            smag = csf[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4 + slen * 2
            if smag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4 + elen
    extra = bytearray()
    added = 0
    for key, value in labels.items():
        if key in existing:
            continue
        encoded = value.encode("utf-16le")
        xored = bytes(x ^ 0xFF for x in encoded)
        extra += b" LBL"
        extra += struct.pack("<II", 1, len(key))
        extra += key.encode("latin1")
        extra += b" RTS"
        extra += struct.pack("<I", len(value))
        extra += xored
        added += 1
    if not added:
        return csf
    hdr = struct.pack("<4sIIIII", magic, ver, nlab + added, nstr + added, unused, lang)
    return hdr + csf[24:] + extra


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    data_map = parse_big(S_DATA.read_bytes())
    art_map = parse_big(S_ART.read_bytes())

    irq_wf = None
    for k in art_map:
        if k.replace("/", "\\").lower() == "art\\w3d\\irq_warfactory.w3d":
            irq_wf = art_map[k]
            break
    if irq_wf is None:
        raise SystemExit("Irq_WarFactory.W3D missing from s ART baseline")
    irq_wf_hash = hashlib.sha256(irq_wf).hexdigest()

    # DATA inserts
    obj = (PATCH_DATA / "INI/Object/Specter/Iraq Army/Buildings/Iraq_MissileFactory.ini").read_bytes()
    btn = (PATCH_DATA / "INI/CommandButton_Iraq_MissileFactory.ini").read_bytes()
    cset = (PATCH_DATA / "INI/CommandSet_Iraq_MissileFactory.ini").read_bytes()
    data_map["Data\\INI\\Object\\Specter\\Iraq Army\\Buildings\\Iraq_MissileFactory.ini"] = obj
    data_map["Data\\INI\\CommandButton_Iraq_MissileFactory.ini"] = btn
    data_map["Data\\INI\\CommandSet_Iraq_MissileFactory.ini"] = cset

    cs_key = "Data\\INI\\CommandSet.ini"
    if cs_key not in data_map:
        raise SystemExit("CommandSet.ini missing")
    # Crash fix: leave CommandSet.ini byte-identical to s. Slot 14 of
    # Iraq_VT72BCommandSet must stay Command_DisarmMinesAtPosition here.
    cs_text = data_map[cs_key].decode("latin1")
    vt = re.search(r"CommandSet Iraq_VT72BCommandSet\r?\n.*?^End", cs_text, re.M | re.S)
    if not vt:
        raise SystemExit("Iraq_VT72BCommandSet missing from s CommandSet.ini")
    if "  14 = Command_ConstructIraq_MissileFactory" in vt.group(0):
        raise SystemExit("CommandSet.ini must not reference extra-only MissileFactory button")
    if "  14 = Command_DisarmMinesAtPosition" not in vt.group(0):
        raise SystemExit("s Iraq_VT72BCommandSet slot 14 is not DisarmMines")
    wk = re.search(r"CommandSet Iraq_WorkerCommandSet\r?\n.*?^End", cs_text, re.M | re.S)
    if not wk or "  14 = Command_DisarmMinesAtPosition" not in wk.group(0):
        raise SystemExit("Iraq_WorkerCommandSet Clear Mines missing")

    csf_key = "Data\\English\\generals.csf"
    if csf_key not in data_map:
        raise SystemExit("generals.csf missing")
    data_map[csf_key] = csf_append(data_map[csf_key], CSF_LABELS)

    # ART inserts — skip if already present; never write abarfrccmd
    for dest, src in ART_IMPORTS:
        if "abarfrccmd" in dest.lower():
            raise SystemExit("refusing abarfrccmd import")
        if not src.is_file():
            raise SystemExit(f"missing donor file {src}")
        # do not overwrite existing SPECTER assets
        existing = None
        for k in art_map:
            if k.replace("/", "\\").lower() == dest.lower():
                existing = k
                break
        if existing:
            print("KEEP existing ART", existing)
            continue
        art_map[dest] = src.read_bytes()
        print("ADD ART", dest, src.stat().st_size)

    # restore Irq_WarFactory unchanged
    for k, v in list(art_map.items()):
        if k.replace("/", "\\").lower() == "art\\w3d\\irq_warfactory.w3d":
            if hashlib.sha256(v).hexdigest() != irq_wf_hash:
                raise SystemExit("Irq_WarFactory.W3D was modified")
            art_map[k] = irq_wf

    data_big = build_big(data_map)
    art_big = build_big(art_map)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_big)
    art_path.write_bytes(art_big)

    zip_path = OUT / "SPECTER_IRAQ_MISSILE_FACTORY_FIX_FINAL.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        zf.write(data_path, arcname="_SPEC_DATA_ONE.big")
        zf.write(art_path, arcname="_SPEC_ART_ONE.big")

    dhash, ahash, zhash = sha256(data_path), sha256(art_path), sha256(zip_path)
    (OUT / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  {data_path.stat().st_size}  SHA256={dhash}\n"
        f"_SPEC_ART_ONE.big  {art_path.stat().st_size}  SHA256={ahash}\n"
        f"SPECTER_IRAQ_MISSILE_FACTORY_FIX_FINAL.zip  {zip_path.stat().st_size}  SHA256={zhash}\n",
        encoding="ascii",
    )
    print("DATA", data_path, data_path.stat().st_size, dhash)
    print("ART", art_path, art_path.stat().st_size, ahash)
    print("ZIP", zip_path, zip_path.stat().st_size, zhash)
    print("Irq_WarFactory.W3D sha256", irq_wf_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
