#!/usr/bin/env python3
"""Replace the first-registered RS-24 / DF-41 Object files.

Four overlay Releases added later zzzzz Object blocks. Those did not
change in-game behavior. CommandSet extra files of existing names are
already known not to replace the first-loaded bar. Iraq radar map was
already in the original Object file; Spy Satellite stayed on the first
CommandSet. The live construct objects are the original Specter\\ paths.

This rebuild starts from wf-restore and overwrites those original paths
in place so the first-registered definition is the patched one. No
second Object block is added.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path


CS_IRAQ = r"Data\INI\CommandSet_ZZZZ_ZZZIraqRadar.ini"
CS_SUPPLY = r"Data\INI\CommandSet_ZZZZ_ZZZZZSupplyCentreBuyButtons.ini"
OBJ_IRAQ = r"Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini"
OBJ_SUPPLY = r"Data\INI\Object\zzzzz_SpecterSupplyCentreBuy"
WPN_TPY = r"Data\INI\Weapon_ZZZZ_ZZZZTpy2RadarCue.ini"

RS_PATH = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Wheeled\RS-24_Yars.ini"
CH_PATH = r"Data\INI\Object\Specter\PLA\Wheeled\DF41.ini"

CS_BLOCK = re.compile(r"(?m)^CommandSet\s+([A-Za-z_][A-Za-z0-9_]*)")
OBJ_CS = re.compile(r"(?im)^\s*CommandSet\s*=\s*(\S+)")
BTN_PAT = re.compile(r"(?m)^CommandButton\s+(\S+)\s*(.*?)(?=^CommandButton\s|\Z)", re.S)
LOCO_PAT = re.compile(r"(?im)^\s*Locomotor\s+=\s+SET_NORMAL\s+(\S+)")
PAYLOAD = re.compile(r"(?im)^\s*InitialPayload\s+=")
OBJ_PAT = re.compile(r"(?m)^Object\s+(\S+)")


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    fm: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        fm[name] = data[off : off + size]
    return fm


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    index, blobs, offset = [], [], header_size
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
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def crlf(body: str) -> bytes:
    return body.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def all_defs(file_map: dict[str, bytes], name: str) -> list[str]:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(name)}\b")
    hits = []
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        if pat.search(raw.decode("latin1")):
            hits.append(path)
    return hits


def last_win_block(file_map: dict[str, bytes], kind: str, name: str) -> tuple[str | None, str | None]:
    pat = re.compile(
        rf"(?m)^{kind}\s+{re.escape(name)}\b.*?(?=^(?:Object|Weapon|Armor|CommandButton|CommandSet|ObjectCreationList|Upgrade|SpecialPower|Locomotor)\s|\Z)",
        re.S,
    )
    last = None
    src = None
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        for m in pat.finditer(raw.decode("latin1")):
            last = m.group(0)
            src = path
    return src, last


def button_object(file_map: dict[str, bytes], name: str) -> str | None:
    obj = None
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        for m in BTN_PAT.finditer(raw.decode("latin1")):
            if m.group(1) != name:
                continue
            mo = re.search(r"(?im)^\s*Object\s+=\s+(\S+)", m.group(2))
            obj = mo.group(1) if mo else None
    return obj


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def _norm(path: str | None) -> str:
    return (path or "").replace("\\", "").replace("/", "").lower()


def field(body: str | None, key: str) -> str | None:
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s+=\s+(\S+)", body or "")
    return m.group(1) if m else None


def loco(body: str | None) -> str | None:
    m = LOCO_PAT.search(body or "")
    return m.group(1) if m else None


def validate(file_map: dict[str, bytes]) -> None:
    for old in (
        r"Data\INI\Object\zzzzz_SpecterRs24Df41Crash",
        r"Data\INI\Object\zzzzz_SpecterRs24Df41Spawn",
        r"Data\INI\Object\zzzzz_SpecterRs24Df41Loco",
    ):
        leftover = [p for p in file_map if _norm(old) in _norm(p)]
        _req(not leftover, f"overlay leftover packed: {leftover}")

    r_defs = all_defs(file_map, "RussiaVehicleRS24")
    _req(r_defs == [RS_PATH], f"RussiaVehicleRS24 not single original path: {r_defs}")
    d_defs = all_defs(file_map, "ChinaVehicleDF41")
    _req(d_defs == [CH_PATH], f"ChinaVehicleDF41 not single original path: {d_defs}")

    for path in (RS_PATH, CH_PATH):
        blocks = CS_BLOCK.findall(file_map[path].decode("latin1"))
        _req(not blocks, f"CommandSet block in {path}: {blocks}")

    _req(button_object(file_map, "Command_ConstructRussiaVehicleRS24") == "RussiaVehicleRS24", "Russia button moved")
    _req(button_object(file_map, "Command_ConstructChinaVehicleDF41") == "ChinaVehicleDF41", "China button moved")

    rsrc, rbody = last_win_block(file_map, "Object", "RussiaVehicleRS24")
    _req(rsrc == RS_PATH, f"RS24 source {rsrc}")
    _req(field(rbody, "Side") == "Russia", "RS24 Side")
    _req(field(rbody, "BuildCost") == "3500", "RS24 cost")
    _req((field(rbody, "BuildTime") or "").startswith("22"), "RS24 time")
    _req("RS24_Yars_ICBM_1x_Warhead" in (rbody or ""), "RS24 1x")
    _req("RS24_Yars_ICBM_4x_Warhead" in (rbody or ""), "RS24 4x")
    _req("RiderChangeContain" in (rbody or ""), "RS24 rider")
    _req("RussiaRS24Hulk" in OBJ_PAT.findall(file_map[RS_PATH].decode("latin1")), "hulk lost")
    _req(loco(rbody) == "Generic8x8Locomotor", f"RS24 loco {loco(rbody)}")
    _req("Generic8x8Locomotor_H" not in (rbody or ""), "RS24 still _H")
    _req(not PAYLOAD.search(rbody or ""), "RS24 still InitialPayload")
    _req("RU_RS28" not in (rbody or ""), "RS24 still RU_RS28")
    _req(field(rbody, "CommandSet") == "RussiaVehicleRS24_UnarmedRearmSet", "RS24 CS")
    _req("GARRISONABLE" not in (rbody or "").split("KindOf", 1)[-1].split("\n", 1)[0], "RS24 KindOf")

    dsrc, dbody = last_win_block(file_map, "Object", "ChinaVehicleDF41")
    _req(dsrc == CH_PATH, f"DF41 source {dsrc}")
    _req(field(dbody, "Side") == "China", "DF41 Side")
    _req(field(dbody, "BuildCost") == "3500", "DF41 cost")
    _req((field(dbody, "BuildTime") or "").startswith("22"), "DF41 time")
    _req("ICBM_DF41_1x_300kt_Warhead" in (dbody or ""), "DF41 1x")
    _req("DF41_ICBM_6x_Warhead_Missile" in (dbody or ""), "DF41 6x")
    _req("CHI_DF41" in (dbody or "") and "DF41_Bones" in (dbody or ""), "DF41 hull")
    _req("CHI_DF41_WL" not in (dbody or "") and "CHI_DF41HL" not in (dbody or ""), "DF41 missing W3Ds remain")
    _req("Model                = None" not in (dbody or ""), "DF41 Model=None")
    _req(loco(dbody) == "Generic8x8Locomotor", f"DF41 loco {loco(dbody)}")
    _req(not PAYLOAD.search(dbody or ""), "DF41 still InitialPayload")
    _req(field(dbody, "CommandSet") == "ChinaVehicleDF41_UnarmedRearmSet", "DF41 CS")

    ysrc, ybody = last_win_block(file_map, "Object", "Russia_RS24_Yars")
    _req(ybody is None, f"Yars alias returned {ysrc}")

    irq_src, _ = last_win_block(file_map, "Object", "Iraq_RadarStation")
    _req(irq_src == OBJ_IRAQ, f"Iraq radar last-win {irq_src}")
    am_src, _ = last_win_block(file_map, "Object", "AmericaSupplyCenter")
    _req(_norm(OBJ_SUPPLY) in _norm(am_src), f"Supply last-win {am_src}")
    wsrc, _ = last_win_block(file_map, "Weapon", "92N6R_FireControlDataLink")
    _req(wsrc == WPN_TPY, f"DataLink last-win {wsrc}")
    cs_src, _ = last_win_block(file_map, "CommandSet", "Iraq_RadarStationCommandSet")
    _req(cs_src == CS_IRAQ, f"Iraq CS last-win {cs_src}")

    for country in ("SaudiArabia", "India"):
        src, body = last_win_block(file_map, "Object", f"{country}_WarFactory_T")
        _req("zzzzz_SpecterWfRemoveSarab" not in _norm(src), f"{country} WF overlay")
        _req(f"{country}_WarFactoryCommandSet" in OBJ_CS.findall(body or ""), f"{country} WF CS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    ap.add_argument(
        "--objects",
        type=Path,
        default=Path("patch/Data/INI/Object/SpecterFirstWinRs24Df41"),
    )
    args = ap.parse_args()

    digest_src = sha256(args.src_big)
    _req(
        digest_src == "242a7c81da9c4552030d25620c1a93342cf6832988ed74639f26b0f8f72a511d",
        f"src BIG is not wf-restore ({digest_src})",
    )

    fm = read_big(args.src_big)
    mapping = {
        RS_PATH: args.objects / "RS-24_Yars.ini",
        CH_PATH: args.objects / "DF41.ini",
    }
    changed = []
    for dest, src in mapping.items():
        _req(dest in fm, f"missing original path {dest}")
        _req(src.is_file(), f"missing patch {src}")
        fm[dest] = crlf(src.read_text(encoding="latin1"))
        changed.append(dest)

    validate(fm)

    args.out_big.parent.mkdir(parents=True, exist_ok=True)
    blob = build_big(fm)
    args.out_big.write_bytes(blob)
    hdr = struct.unpack(">I", blob[4:8])[0]
    if hdr != len(blob):
        raise SystemExit(f"BIG size field {hdr} != file {len(blob)}")
    digest = sha256(args.out_big)
    Path(str(args.out_big) + ".sha256").write_text(digest + "\n")
    print(f"SRC  size={args.src_big.stat().st_size} sha256={digest_src}")
    print(f"OUT  size={args.out_big.stat().st_size} sha256={digest} entries={len(fm)}")
    for name in changed:
        print(f"  replace {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
