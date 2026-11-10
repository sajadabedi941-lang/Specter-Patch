#!/usr/bin/env python3
"""Put Iran missile Fire CommandSets into CommandSet.ini.

Proven empty-bar cause in the #708 BIG (SHA bbbc60c7…):

- Every Iran missile Object.CommandSet is IranMissileFireCommandSet,
  IranKhorramshahrFireCommandSet, or IranShahed136FireCommandSet.
- Those names are absent from Data\\INI\\CommandSet.ini.
- They exist only in CommandSet_IranMissiles.ini and
  CommandSet_ZZZZ_ZzzIranMissileFire.ini.
- Buildings the player can actually use (IranWarFactory, Iran_MissileFactory,
  IranVehicleDozer) point at names that ARE in CommandSet.ini.

INIZH.big is not in this environment, so BIG-vs-INIZH overwrite of the
CommandSet.ini *path* cannot be dumped here. The in-game split (empty unit
bars vs working factory/dozer bars) matches CommandSet.ini membership, not
extra-file membership.

This pack appends the four unique Iran sets to CommandSet.ini and removes
those names from extra files so they cannot collide if extras are parsed.
Does not edit Scud_B_CommandSet / Smerch_CommandSet. No ART.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path


SRC_SHA = "bbbc60c7d39b37cef7c82e11b96e95f322e7b9fe7b2674660c02575f5584c81e"

CS_INI = r"Data\INI\CommandSet.ini"
CS_IRAN = r"Data\INI\CommandSet_IranMissiles.ini"
CS_ZZZZ = r"Data\INI\CommandSet_ZZZZ_ZzzIranMissileFire.ini"
KH_FIRST = r"Data\INI\Object\Specter\Iranian Army\Wheeled\Khormshar.ini"
SH_PATH = r"Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini"
MF_PATH = r"Data\INI\Object\Specter\Iranian Army\Buildings\Iran_MissileFactory.ini"
WPN_PATH = r"Data\INI\Weapon_ZZZZ_IranShahed136Launcher.ini"
PROJ_PATH = r"Data\INI\Object\Specter\Iranian Army\Iran_Shahed136_FireProjectile.ini"
RS_PATH = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Wheeled\RS-24_Yars.ini"
OBJ_IRAQ = r"Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini"
OBJ_SUPPLY = r"Data\INI\Object\zzzzz_SpecterSupplyCentreBuy"
WPN_TPY = r"Data\INI\Weapon_ZZZZ_ZZZZTpy2RadarCue.ini"

APPEND = """
CommandSet IranMissileFireCommandSet
  1  = Command_FireMainWeapon
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End

CommandSet IranMissileTELFireCommandSet
  1  = Command_FireMainWeapon
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End

CommandSet IranKhorramshahrFireCommandSet
  1  = Command_FireMainWeapon
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End

CommandSet IranShahed136FireCommandSet
  1  = Command_FireMainWeapon
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
"""

IRAN_UNITS = {
    "IranVehicleFateh313": "IranMissileFireCommandSet",
    "IranVehicleFattah": "IranMissileFireCommandSet",
    "IranVehicleFattah2": "IranMissileFireCommandSet",
    "IranVehicleZolfagharM": "IranMissileFireCommandSet",
    "IranVehicleDezfulPenetrator": "IranMissileFireCommandSet",
    "IranVehicleBM21": "IranMissileFireCommandSet",
    "IranVehicleHoveyzeh": "IranMissileFireCommandSet",
    "Iran_Hormuz": "IranMissileFireCommandSet",
    "Iran_Qader": "IranMissileFireCommandSet",
    "Iran_Qiam": "IranMissileFireCommandSet",
    "Iran_Emad": "IranMissileFireCommandSet",
    "Iran_Khalij": "IranMissileFireCommandSet",
    "Iran_Dezful": "IranMissileFireCommandSet",
    "Iran_Khorram": "IranMissileFireCommandSet",
    "Iran_Kheibar": "IranMissileFireCommandSet",
    "Iran_Ghadr": "IranMissileFireCommandSet",
    "Iran_Simorgh": "IranMissileFireCommandSet",
    "IranVehicleKhormshar": "IranKhorramshahrFireCommandSet",
    "IranVehicleShahedLauncher": "IranShahed136FireCommandSet",
}


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


def first_win_block(file_map: dict[str, bytes], kind: str, name: str) -> tuple[str | None, str | None]:
    pat = re.compile(
        rf"(?m)^{kind}\s+{re.escape(name)}\b.*?(?=^(?:Object|Weapon|Armor|CommandButton|CommandSet|ObjectCreationList|Upgrade|SpecialPower|Locomotor)\s|\Z)",
        re.S,
    )
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        m = pat.search(raw.decode("latin1"))
        if m:
            return path, m.group(0)
    return None, None


def field(body: str | None, key: str) -> str | None:
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s+=\s+(\S+)", body or "")
    return m.group(1) if m else None


def prereq_inner(body: str | None) -> str:
    m = re.search(r"(?ms)^\s*Prerequisites\s*\n(.*?)^\s*End", body or "")
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip()


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def _norm(path: str | None) -> str:
    return (path or "").replace("\\", "").replace("/", "").lower()


def all_cs_defs(file_map: dict[str, bytes], name: str) -> list[str]:
    pat = re.compile(rf"(?m)^CommandSet\s+{re.escape(name)}\b")
    hits = []
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        if pat.search(raw.decode("latin1")):
            hits.append(path)
    return hits


def validate(file_map: dict[str, bytes]) -> None:
    bsrc, bbody = first_win_block(file_map, "CommandButton", "Command_FireMainWeapon")
    _req(bsrc == r"Data\INI\CommandButton.ini", f"FireMainWeapon {bsrc}")
    _req("FIRE_WEAPON" in (bbody or "") and "PRIMARY" in (bbody or ""), "FireMainWeapon slot")

    for cs_name in (
        "IranMissileFireCommandSet",
        "IranMissileTELFireCommandSet",
        "IranKhorramshahrFireCommandSet",
        "IranShahed136FireCommandSet",
    ):
        defs = all_cs_defs(file_map, cs_name)
        _req(defs == [CS_INI], f"{cs_name} defs {defs}")
        src, body = first_win_block(file_map, "CommandSet", cs_name)
        _req(src == CS_INI, f"{cs_name} first {src}")
        _req("Command_FireMainWeapon" in (body or ""), f"{cs_name} no Fire")
        _req("Command_Guard" in (body or "") and "Command_Stop" in (body or ""), f"{cs_name} bar")
        for slot, btn in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", body or ""):
            _req(1 <= int(slot) <= 14, f"{cs_name} slot {slot} off ControlBar")
            bsrc2, _ = first_win_block(file_map, "CommandButton", btn)
            _req(bsrc2 == r"Data\INI\CommandButton.ini", f"{cs_name} {btn} not in CommandButton.ini ({bsrc2})")

    for name, expected in IRAN_UNITS.items():
        _, body = first_win_block(file_map, "Object", name)
        _req(field(body, "CommandSet") == expected, f"{name} CS {field(body, 'CommandSet')}")
        inner = prereq_inner(body)
        _req(
            not any(x in inner for x in ("IranIndustrialComplex", "Iran_GlobalStore", "IranRadarStation")),
            f"{name} relocked {inner}",
        )

    _, kbody = first_win_block(file_map, "Object", "IranVehicleKhormshar")
    _req(field(kbody, "BuildTime").startswith("10"), "Khormshar time")
    _req(field(kbody, "BuildCost") == "2500", "Khormshar cost")
    _req(
        re.search(
            r"(?ms)WeaponSet\s+Conditions\s+=\s+None.*?PRIMARY\s+Khormshar1_ICBM",
            (kbody or "").replace("\r\n", "\n"),
        ),
        "Khormshar ICBM not PRIMARY",
    )

    _, sbody = first_win_block(file_map, "Object", "IranVehicleShahedLauncher")
    _req(field(sbody, "BuildCost") == "1500", "Shahed cost")
    _req(field(sbody, "VisionRange") == "3000", "Shahed vision")
    _, wbody = last_win_block(file_map, "Weapon", "Weapon_Iran_Shahed136Launcher")
    _req(field(wbody, "AttackRange") == "3000", "Shahed range")
    _req("Iran_Shahed136_FireProjectile" in (wbody or ""), "Shahed projectile")

    _, mbody = first_win_block(file_map, "Object", "Iran_MissileFactory")
    _req(prereq_inner(mbody) == "Object = IranSupplyCenter", f"factory {prereq_inner(mbody)}")
    _, rkh = last_win_block(file_map, "Object", "Iran_Khorram")
    _req(field(rkh, "BuildTime").startswith("10"), "Iran_Khorram time")

    _, isk = first_win_block(file_map, "Object", "Russia_Iskander")
    _req(field(isk, "CommandSet") == "Scud_B_CommandSet", "Iskander CS changed")
    scud_defs = all_cs_defs(file_map, "Scud_B_CommandSet")
    _req(scud_defs == [CS_INI], f"Scud_B defs {scud_defs}")

    irq_src, _ = last_win_block(file_map, "Object", "Iraq_RadarStation")
    _req(irq_src == OBJ_IRAQ, f"Iraq radar {irq_src}")
    am_src, _ = last_win_block(file_map, "Object", "AmericaSupplyCenter")
    _req(_norm(OBJ_SUPPLY) in _norm(am_src), f"Supply {am_src}")
    wsrc, _ = last_win_block(file_map, "Weapon", "92N6R_FireControlDataLink")
    _req(wsrc == WPN_TPY, f"DataLink {wsrc}")
    rs_src, rs_body = last_win_block(file_map, "Object", "RussiaVehicleRS24")
    _req(rs_src == RS_PATH, f"RS24 {rs_src}")
    _req("RiderChangeContain" not in (rs_body or ""), "RS24 rider")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    ap.add_argument("--iran-missiles-cs", type=Path, default=Path("patch/Data/INI/CommandSet_IranMissiles.ini"))
    ap.add_argument("--zzzz-cs", type=Path, default=Path("patch/Data/INI/CommandSet_ZZZZ_ZzzIranMissileFire.ini"))
    args = ap.parse_args()

    digest_src = sha256(args.src_big)
    _req(digest_src == SRC_SHA, f"src BIG is not #708 ({digest_src})")
    _req(args.iran_missiles_cs.is_file() and args.zzzz_cs.is_file(), "missing extra CS sources")

    fm = read_big(args.src_big)
    cs = fm[CS_INI].decode("latin1").replace("\r\n", "\n")
    _req("CommandSet IranWarfactoryCommandSet" in cs, "CommandSet.ini missing Iran WF set")
    _req("CommandSet IranMissileFireCommandSet" not in cs, "already appended")
    fm[CS_INI] = crlf(cs.rstrip() + "\n" + APPEND)

    iran_txt = args.iran_missiles_cs.read_text(encoding="latin1")
    _req("IranMissileFireCommandSet" not in iran_txt, "loose IranMissiles still has unique CS")
    fm[CS_IRAN] = crlf(iran_txt)
    fm[CS_ZZZZ] = crlf(args.zzzz_cs.read_text(encoding="latin1"))

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
    print(f"  append 4 CommandSets to {CS_INI}")
    print(f"  restore {CS_IRAN}")
    print(f"  comment-only {CS_ZZZZ}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
