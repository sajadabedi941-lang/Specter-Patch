#!/usr/bin/env python3
"""Fix Russia RS-24 and China DF-41 War Factory complete-production crashes.

Previous Release rs24-df41-wf-crash (alias object + DF-41 Draw strip) was
installed in-game and did not stop the crash. This rebuild does not pack
that overlay.

Both live construct buttons already target existing objects. The crash is
at factory-complete / object create, not click or queue.

Source BIG must be the current healthy DATA (wf-restore-warfactory-buttons).
Does not edit CommandSet.ini / CommandButton.ini (INIZH first-wins those
paths). CommandSet blocks are not placed in Object\\.
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
OBJ_RADAR = r"Data\INI\Object\zzzzz_SpecterRadarTpy2Cue"
OBJ_SUPPLY = r"Data\INI\Object\zzzzz_SpecterSupplyCentreBuy"
OBJ_FIX = r"Data\INI\Object\zzzzz_SpecterRs24Df41Spawn"
OBJ_OLD = r"Data\INI\Object\zzzzz_SpecterRs24Df41Crash"
WPN_TPY = r"Data\INI\Weapon_ZZZZ_ZZZZTpy2RadarCue.ini"

CS_BLOCK = re.compile(r"(?m)^CommandSet\s+([A-Za-z_][A-Za-z0-9_]*)")
OBJ_CS = re.compile(r"(?im)^\s*CommandSet\s*=\s*(\S+)")
MODEL_PAT = re.compile(r"(?im)^\s*Model\s+=\s+(\S+)")
BTN_PAT = re.compile(r"(?m)^CommandButton\s+(\S+)\s*(.*?)(?=^CommandButton\s|\Z)", re.S)
KIND_PAT = re.compile(r"(?im)^\s*KindOf\s+=\s+(.+)$")
WS_NONE = re.compile(r"(?im)^\s*Conditions\s+=\s+None\s*$")
PAYLOAD = re.compile(r"(?im)^\s*InitialPayload\s+=")


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


def last_win_block(file_map: dict[str, bytes], kind: str, name: str) -> tuple[str | None, str | None]:
    pat = re.compile(
        rf"(?m)^{kind}\s+{re.escape(name)}\b.*?(?=^(?:Object|Weapon|Armor|CommandButton|CommandSet|ObjectCreationList|Upgrade|SpecialPower)\s|\Z)",
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


def button_object(file_map: dict[str, bytes], name: str) -> tuple[str | None, str | None]:
    src = obj = None
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        for m in BTN_PAT.finditer(raw.decode("latin1")):
            if m.group(1) != name:
                continue
            mo = re.search(r"(?im)^\s*Object\s+=\s+(\S+)", m.group(2))
            src, obj = path, (mo.group(1) if mo else None)
    return src, obj


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def _norm(path: str | None) -> str:
    return (path or "").replace("\\", "").replace("/", "").lower()


def field(body: str | None, key: str) -> str | None:
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s+=\s+(\S+)", body or "")
    return m.group(1) if m else None


def validate(file_map: dict[str, bytes]) -> None:
    old_paths = [p for p in file_map if _norm(OBJ_OLD) in _norm(p)]
    _req(not old_paths, f"old rs24-df41-wf-crash overlay still packed: {old_paths}")

    for path, raw in file_map.items():
        if _norm(OBJ_FIX) in _norm(path) and path.lower().endswith(".ini"):
            blocks = CS_BLOCK.findall(raw.decode("latin1"))
            _req(not blocks, f"Object folder has CommandSet blocks in {path}: {blocks}")

    btn_src, btn_obj = button_object(file_map, "Command_ConstructRussiaVehicleRS24")
    _req(btn_obj == "RussiaVehicleRS24", f"Russia main button Object is {btn_obj}")
    rsrc, rbody = last_win_block(file_map, "Object", "RussiaVehicleRS24")
    _req(_norm(OBJ_FIX) in _norm(rsrc), f"RussiaVehicleRS24 last-win not overlay ({rsrc})")
    _req(field(rbody, "Side") == "Russia", "RS24 Side changed")
    _req(field(rbody, "BuildCost") == "3500", f"RS24 BuildCost {field(rbody, 'BuildCost')}")
    _req((field(rbody, "BuildTime") or "").startswith("22"), f"RS24 BuildTime {field(rbody, 'BuildTime')}")
    _req("RS24_Yars_ICBM_1x_Warhead" in (rbody or ""), "RS24 lost 1x warhead")
    _req("RS24_Yars_ICBM_4x_Warhead" in (rbody or ""), "RS24 lost 4x warhead")
    _req("RiderChangeContain" in (rbody or ""), "RS24 lost RiderChangeContain")
    _req(field(rbody, "CommandSet") == "RussiaVehicleRS24_UnarmedRearmSet", "RS24 CommandSet not unarmed rearm")
    _req(
        re.search(r"(?is)WeaponSet\s+Conditions\s+=\s+None\s+.*?DeployHeavyWeapons", rbody or ""),
        "RS24 missing default unarmed WeaponSet",
    )
    _req(not PAYLOAD.search(rbody or ""), "RS24 still has InitialPayload")
    _req("RU_RS28" not in (rbody or ""), "RS24 still references RU_RS28")
    kind = (KIND_PAT.search(rbody or "") or re.match(r"$")).group(1) if KIND_PAT.search(rbody or "") else ""
    _req("GARRISONABLE" not in kind, f"RS24 KindOf still garrisonable: {kind}")
    _req("SALVAGER" not in kind, f"RS24 KindOf still salvager: {kind}")
    _req("HUGE_VEHICLE" not in kind, f"RS24 KindOf still huge: {kind}")
    _req("RUS_RS24" in MODEL_PAT.findall(rbody or ""), "RS24 lost hull model")

    ysrc, ybody = last_win_block(file_map, "Object", "Russia_RS24_Yars")
    _req(ybody is None, f"Russia_RS24_Yars alias returned ({ysrc})")

    dsrc, dbody = last_win_block(file_map, "Object", "ChinaVehicleDF41")
    _req(_norm(OBJ_FIX) in _norm(dsrc), f"DF41 last-win not overlay ({dsrc})")
    _req(field(dbody, "Side") == "China", "DF41 Side changed")
    _req(field(dbody, "BuildCost") == "3500", f"DF41 BuildCost {field(dbody, 'BuildCost')}")
    _req((field(dbody, "BuildTime") or "").startswith("22"), f"DF41 BuildTime {field(dbody, 'BuildTime')}")
    _req("ICBM_DF41_1x_300kt_Warhead" in (dbody or ""), "DF41 lost 1x warhead")
    _req("DF41_ICBM_6x_Warhead_Missile" in (dbody or ""), "DF41 lost 6x warhead")
    _req("RiderChangeContain" in (dbody or ""), "DF41 lost RiderChangeContain")
    _req(field(dbody, "CommandSet") == "ChinaVehicleDF41_UnarmedRearmSet", "DF41 CommandSet not unarmed rearm")
    _req(
        re.search(r"(?is)WeaponSet\s+Conditions\s+=\s+None\s+.*?DeployHeavyWeapons", dbody or ""),
        "DF41 missing default unarmed WeaponSet",
    )
    _req(not PAYLOAD.search(dbody or ""), "DF41 still has InitialPayload")
    dkind = KIND_PAT.search(dbody or "")
    dkind_s = dkind.group(1) if dkind else ""
    _req("GARRISONABLE" not in dkind_s, f"DF41 KindOf still garrisonable: {dkind_s}")
    _req("SALVAGER" not in dkind_s, f"DF41 KindOf still salvager: {dkind_s}")
    _req("HUGE_VEHICLE" not in dkind_s, f"DF41 KindOf still huge: {dkind_s}")
    models = set(MODEL_PAT.findall(dbody or ""))
    _req("CHI_DF41" in models and "DF41_Bones" in models, f"DF41 lost hull/bones {models}")
    # Draw strip is NOT this patch; original extra draws remain
    _req("CHI_DF41_WL" in models, "DF41 extra WL draw was stripped again")
    csrc, cbtn = button_object(file_map, "Command_ConstructChinaVehicleDF41")
    _req(cbtn == "ChinaVehicleDF41", f"DF41 button Object is {cbtn}")

    irq_src, _ = last_win_block(file_map, "Object", "Iraq_RadarStation")
    _req(irq_src == OBJ_IRAQ, f"Iraq radar object last-win moved to {irq_src}")
    cs_src, cs = last_win_block(file_map, "CommandSet", "Iraq_RadarStationCommandSet")
    _req(cs_src == CS_IRAQ, f"Iraq radar CS last-win moved to {cs_src}")
    am_src, _ = last_win_block(file_map, "Object", "AmericaSupplyCenter")
    _req(_norm(OBJ_SUPPLY) in _norm(am_src), f"America Supply last-win lost ({am_src})")
    sc_src, _ = last_win_block(file_map, "CommandSet", "AmericaSupplyCenterCommandSet")
    _req(sc_src == CS_SUPPLY, f"America Supply CS last-win moved to {sc_src}")
    wsrc, _ = last_win_block(file_map, "Weapon", "92N6R_FireControlDataLink")
    _req(wsrc == WPN_TPY, f"92N6R DataLink last-win moved to {wsrc}")

    for country in ("SaudiArabia", "India"):
        src, body = last_win_block(file_map, "Object", f"{country}_WarFactory_T")
        _req("zzzzz_SpecterWfRemoveSarab" not in _norm(src), f"{country} WF overlay returned ({src})")
        _req(f"{country}_WarFactoryCommandSet" in OBJ_CS.findall(body or ""), f"{country} WF CS changed")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    ap.add_argument(
        "--objects",
        type=Path,
        default=Path("patch/Data/INI/Object/zzzzz_SpecterRs24Df41Spawn"),
    )
    args = ap.parse_args()

    digest_src = sha256(args.src_big)
    _req(
        digest_src == "242a7c81da9c4552030d25620c1a93342cf6832988ed74639f26b0f8f72a511d",
        f"src BIG is not wf-restore healthy DATA ({digest_src})",
    )

    fm = read_big(args.src_big)
    extras: dict[str, bytes] = {}
    for ini in sorted(args.objects.glob("*.ini")):
        if ini.name.lower() == "commandsets.ini":
            raise SystemExit(f"do not pack CommandSet blocks from Object folder: {ini}")
        extras[rf"{OBJ_FIX}\{ini.name}"] = crlf(ini.read_text(encoding="latin1"))

    changed = []
    for name, body in extras.items():
        prev = fm.get(name)
        fm[name] = body
        changed.append(("update" if prev is not None else "add", name))

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
    for op, name in changed:
        print(f"  {op} {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
