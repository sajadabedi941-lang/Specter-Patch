#!/usr/bin/env python3
"""Restore Iran missile Fire buttons using stock Command_FireMainWeapon.

Starts from the unlock BIG (PR #707). That pack pointed Khormshar/Shahed at
unique CommandSets whose slot-1 buttons (Command_IranFirePrimary/Secondary)
existed only in an extra CommandButton file. Live ControlBar uses buttons
from CommandButton.ini (INIZH first-wins that stock path). Unique extra
button names do not appear. Other Iran TELs still used Scud_B_CommandSet /
Smerch_CommandSet, which live only in CommandSet.ini (also INIZH-first-win).

This pack:
- rewrites unique Iran CommandSets to Command_FireMainWeapon (stock)
- also defines those sets in CommandSet_IranMissiles.ini (known Iran extra)
- retargets every Iran missile Object off Scud_B / Smerch
- moves Khormshar ICBM to PRIMARY so FireMainWeapon can fire it
- keeps unlocks, BuildTime 10, Shahed range 3000, no ART
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path


SRC_SHA = "b9b7317ea6e346bc45544287c3fbcc5b96693a2c82019500d72044cd024eb915"

OV_PATH = r"Data\INI\Object_ZZZZ_ZzGlobalStoreFivePrereq.ini"
CS_EXTRA = r"Data\INI\CommandSet_ZZZZ_ZzzIranMissileFire.ini"
CS_IRAN = r"Data\INI\CommandSet_IranMissiles.ini"
KH_FIRST = r"Data\INI\Object\Specter\Iranian Army\Wheeled\Khormshar.ini"
SH_PATH = r"Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini"
SYS_PATH = r"Data\INI\Object\Specter\Iranian Army\Iran_System.ini"
WPN_PATH = r"Data\INI\Weapon_ZZZZ_IranShahed136Launcher.ini"
PROJ_PATH = r"Data\INI\Object\Specter\Iranian Army\Iran_Shahed136_FireProjectile.ini"
MF_PATH = r"Data\INI\Object\Specter\Iranian Army\Buildings\Iran_MissileFactory.ini"

OBJ_IRAQ = r"Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini"
OBJ_SUPPLY = r"Data\INI\Object\zzzzz_SpecterSupplyCentreBuy"
WPN_TPY = r"Data\INI\Weapon_ZZZZ_ZZZZTpy2RadarCue.ini"
RS_PATH = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Wheeled\RS-24_Yars.ini"

# first-win Object path -> (object name, old CS substring, new CS)
WHEELED = {
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\Fateh313.ini": (
        "IranVehicleFateh313",
        "CommandSet    = Scud_B_CommandSet",
        "CommandSet    = IranMissileFireCommandSet",
    ),
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\Fattah.ini": (
        "IranVehicleFattah",
        "CommandSet    = Scud_B_CommandSet",
        "CommandSet    = IranMissileFireCommandSet",
    ),
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\Iran_Hormuz.ini": (
        "Iran_Hormuz",
        "CommandSet    = Scud_B_CommandSet",
        "CommandSet    = IranMissileFireCommandSet",
    ),
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\Iran_Qader.ini": (
        "Iran_Qader",
        "CommandSet    = Scud_B_CommandSet",
        "CommandSet    = IranMissileFireCommandSet",
    ),
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\Iran_Qiam.ini": (
        "Iran_Qiam",
        "CommandSet    = Scud_B_CommandSet",
        "CommandSet    = IranMissileFireCommandSet",
    ),
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\Iran_Emad.ini": (
        "Iran_Emad",
        "CommandSet    = Scud_B_CommandSet",
        "CommandSet    = IranMissileFireCommandSet",
    ),
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\Iran_Khalij.ini": (
        "Iran_Khalij",
        "CommandSet    = Scud_B_CommandSet",
        "CommandSet    = IranMissileFireCommandSet",
    ),
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\Iran_Dezful.ini": (
        "Iran_Dezful",
        "CommandSet    = Scud_B_CommandSet",
        "CommandSet    = IranMissileFireCommandSet",
    ),
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\Iran_Khorram.ini": (
        "Iran_Khorram",
        "CommandSet    = Scud_B_CommandSet",
        "CommandSet    = IranMissileFireCommandSet",
    ),
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\Iran_Kheibar.ini": (
        "Iran_Kheibar",
        "CommandSet    = Scud_B_CommandSet",
        "CommandSet    = IranMissileFireCommandSet",
    ),
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\Iran_Ghadr.ini": (
        "Iran_Ghadr",
        "CommandSet    = Scud_B_CommandSet",
        "CommandSet    = IranMissileFireCommandSet",
    ),
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\Iran_Simorgh.ini": (
        "Iran_Simorgh",
        "CommandSet    = Scud_B_CommandSet",
        "CommandSet    = IranMissileFireCommandSet",
    ),
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\BM21.ini": (
        "IranVehicleBM21",
        "CommandSet            = Smerch_CommandSet",
        "CommandSet            = IranMissileFireCommandSet",
    ),
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\Hovyz.ini": (
        "IranVehicleHoveyzeh",
        "CommandSet            = Smerch_CommandSet",
        "CommandSet            = IranMissileFireCommandSet",
    ),
}

SYS_UNITS = [
    "IranVehicleFattah2",
    "IranVehicleZolfagharM",
    "IranVehicleDezfulPenetrator",
]
OV_SCUD = [
    "IranVehicleFattah",
    "IranVehicleFattah2",
    "IranVehicleZolfagharM",
    "IranVehicleDezfulPenetrator",
]

IRAN_CS_APPEND = """
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


def object_block(text: str, name: str) -> re.Match[str] | None:
    return re.search(rf"(?ms)^(Object\s+{re.escape(name)}\b.*?)(?=^Object\s|\Z)", text)


def splice_named(text: str, name: str, mutator) -> str:
    m = object_block(text, name)
    _req(m is not None, f"{name} missing")
    patched = mutator(m.group(1))
    return text[: m.start(1)] + patched + text[m.end(1) :]


def retarget_scud(block: str) -> str:
    new, n = re.subn(
        r"(?m)^  CommandSet    = Scud_B_CommandSet",
        "  CommandSet    = IranMissileFireCommandSet",
        block,
        count=1,
    )
    _req(n == 1, f"scud retarget missed: {block[block.find('CommandSet'):block.find('CommandSet')+60] if 'CommandSet' in block else block[:80]!r}")
    return new


def patch_khormshar_primary(block: str) -> str:
    new, n = re.subn(
        r"(?ms)^  WeaponSet\n    Conditions = None\n    Weapon            = SECONDARY  Khormshar1_ICBM\n    AutoChooseSources = SECONDARY  NONE\n",
        (
            "  WeaponSet\n"
            "    Conditions = None\n"
            "    Weapon            = PRIMARY    Khormshar1_ICBM\n"
            "    AutoChooseSources = PRIMARY    NONE\n"
        ),
        block,
        count=1,
    )
    _req(n == 1, "Khormshar PRIMARY splice missed")
    return new


def cs_has_stock_fire(body: str | None) -> bool:
    return bool(body) and "Command_FireMainWeapon" in body and "Command_IranFire" not in body


def unlocked(body: str | None) -> bool:
    inner = prereq_inner(body)
    return not any(
        x in inner
        for x in ("IranIndustrialComplex", "Iran_GlobalStore", "IranRadarStation", "IranWarFactory")
    )


def validate(file_map: dict[str, bytes]) -> None:
    bsrc, bbody = first_win_block(file_map, "CommandButton", "Command_FireMainWeapon")
    _req(bsrc == r"Data\INI\CommandButton.ini", f"FireMainWeapon source {bsrc}")
    _req("FIRE_WEAPON" in (bbody or "") and "PRIMARY" in (bbody or ""), "FireMainWeapon not PRIMARY FIRE")
    _req("NEED_SPECIAL_POWER_SCIENCE" not in (bbody or ""), "FireMainWeapon science")

    for cs_name in (
        "IranMissileFireCommandSet",
        "IranMissileTELFireCommandSet",
        "IranKhorramshahrFireCommandSet",
        "IranShahed136FireCommandSet",
    ):
        src, body = last_win_block(file_map, "CommandSet", cs_name)
        _req(src in (CS_EXTRA, CS_IRAN), f"{cs_name} last {src}")
        _req(cs_has_stock_fire(body), f"{cs_name} still unique buttons")
        _req("Command_Guard" in (body or "") and "Command_Stop" in (body or ""), f"{cs_name} missing move bar")
        first_src, first_body = first_win_block(file_map, "CommandSet", cs_name)
        _req(cs_has_stock_fire(first_body), f"{cs_name} first still unique")

    ksrc, kbody = first_win_block(file_map, "Object", "IranVehicleKhormshar")
    _req(ksrc == KH_FIRST, f"Khormshar first {ksrc}")
    _req(field(kbody, "CommandSet") == "IranKhorramshahrFireCommandSet", "Khormshar CS")
    _req(field(kbody, "BuildTime").startswith("10"), "Khormshar time")
    _req(field(kbody, "BuildCost") == "2500", "Khormshar cost")
    _req(unlocked(kbody), f"Khormshar prereq {prereq_inner(kbody)}")
    _req(
        re.search(
            r"(?ms)WeaponSet\s+Conditions\s+=\s+None.*?PRIMARY\s+Khormshar1_ICBM",
            (kbody or "").replace("\r\n", "\n"),
        ),
        "Khormshar ICBM not PRIMARY",
    )
    _, klast = last_win_block(file_map, "Object", "IranVehicleKhormshar")
    _req(field(klast, "CommandSet") == "IranKhorramshahrFireCommandSet", "Khormshar last CS")
    _req(
        re.search(
            r"(?ms)WeaponSet\s+Conditions\s+=\s+None.*?PRIMARY\s+Khormshar1_ICBM",
            (klast or "").replace("\r\n", "\n"),
        ),
        "Khormshar last ICBM not PRIMARY",
    )

    ssrc, sbody = first_win_block(file_map, "Object", "IranVehicleShahedLauncher")
    _req(ssrc == SH_PATH, f"Shahed {ssrc}")
    _req(field(sbody, "CommandSet") == "IranShahed136FireCommandSet", "Shahed CS")
    _req("Weapon_Iran_Shahed136Launcher" in (sbody or ""), "Shahed weapon")
    _req(field(sbody, "VisionRange") == "3000", "Shahed vision")
    _req(field(sbody, "BuildCost") == "1500", "Shahed cost")

    wsrc, wbody = last_win_block(file_map, "Weapon", "Weapon_Iran_Shahed136Launcher")
    _req(wsrc == WPN_PATH, f"shahed weapon {wsrc}")
    _req(field(wbody, "AttackRange") == "3000", "shahed range")
    _req("Iran_Shahed136_FireProjectile" in (wbody or ""), "shahed projectile")
    _req("AntiGround" in (wbody or ""), "shahed AntiGround")

    psrc, pbody = first_win_block(file_map, "Object", "Iran_Shahed136_FireProjectile")
    _req(psrc == PROJ_PATH, f"proj {psrc}")
    _req("DumbProjectileBehavior" in (pbody or ""), "proj not dumb")

    for name, expected_cs in [
        ("IranVehicleFateh313", "IranMissileFireCommandSet"),
        ("IranVehicleFattah", "IranMissileFireCommandSet"),
        ("IranVehicleFattah2", "IranMissileFireCommandSet"),
        ("IranVehicleZolfagharM", "IranMissileFireCommandSet"),
        ("IranVehicleDezfulPenetrator", "IranMissileFireCommandSet"),
        ("IranVehicleBM21", "IranMissileFireCommandSet"),
        ("IranVehicleHoveyzeh", "IranMissileFireCommandSet"),
        ("Iran_Hormuz", "IranMissileFireCommandSet"),
        ("Iran_Qader", "IranMissileFireCommandSet"),
        ("Iran_Qiam", "IranMissileFireCommandSet"),
        ("Iran_Emad", "IranMissileFireCommandSet"),
        ("Iran_Khalij", "IranMissileFireCommandSet"),
        ("Iran_Dezful", "IranMissileFireCommandSet"),
        ("Iran_Khorram", "IranMissileFireCommandSet"),
        ("Iran_Kheibar", "IranMissileFireCommandSet"),
        ("Iran_Ghadr", "IranMissileFireCommandSet"),
        ("Iran_Simorgh", "IranMissileFireCommandSet"),
    ]:
        fsrc, fbody = first_win_block(file_map, "Object", name)
        _req(field(fbody, "CommandSet") == expected_cs, f"{name} CS {field(fbody, 'CommandSet')}")
        _req(unlocked(fbody), f"{name} relocked {prereq_inner(fbody)}")
        _req("Scud_B_CommandSet" not in (fbody or ""), f"{name} still Scud_B")
        _req("Smerch_CommandSet" not in (fbody or ""), f"{name} still Smerch")

    # other-country Scud_B units untouched
    _, isk = first_win_block(file_map, "Object", "Russia_Iskander")
    _req(field(isk, "CommandSet") == "Scud_B_CommandSet", "Iskander CS changed")
    _, abb = first_win_block(file_map, "Object", "Iraq_AlAbbas")
    _req(field(abb, "CommandSet") == "Scud_B_CommandSet", "AlAbbas CS changed")

    msrc, mbody = first_win_block(file_map, "Object", "Iran_MissileFactory")
    _req(msrc == MF_PATH, f"factory {msrc}")
    _req(prereq_inner(mbody) == "Object = IranSupplyCenter", f"factory prereq {prereq_inner(mbody)}")

    _, rkh = last_win_block(file_map, "Object", "Iran_Khorram")
    _req(field(rkh, "BuildTime").startswith("10"), "Iran_Khorram time")

    canary_src, canary = last_win_block(file_map, "Object", "RussiaVehicle96L6TSP")
    _req(canary_src == OV_PATH, f"96L6 {canary_src}")
    _req("Russia_GlobalStore" in prereq_inner(canary), "non-Iran GlobalStore stripped")

    irq_src, _ = last_win_block(file_map, "Object", "Iraq_RadarStation")
    _req(irq_src == OBJ_IRAQ, f"Iraq radar {irq_src}")
    am_src, _ = last_win_block(file_map, "Object", "AmericaSupplyCenter")
    _req(_norm(OBJ_SUPPLY) in _norm(am_src), f"Supply {am_src}")
    wsrc, _ = last_win_block(file_map, "Weapon", "92N6R_FireControlDataLink")
    _req(wsrc == WPN_TPY, f"DataLink {wsrc}")
    rs_src, rs_body = last_win_block(file_map, "Object", "RussiaVehicleRS24")
    _req(rs_src == RS_PATH, f"RS24 {rs_src}")
    _req("RiderChangeContain" not in (rs_body or ""), "RS24 rider returned")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    ap.add_argument(
        "--commandset",
        type=Path,
        default=Path("patch/Data/INI/CommandSet_ZZZZ_ZzzIranMissileFire.ini"),
    )
    args = ap.parse_args()

    digest_src = sha256(args.src_big)
    _req(digest_src == SRC_SHA, f"src BIG is not unlock pack ({digest_src})")
    _req(args.commandset.is_file(), f"missing {args.commandset}")

    fm = read_big(args.src_big)

    fm[CS_EXTRA] = crlf(args.commandset.read_text(encoding="latin1"))

    iran_cs = fm[CS_IRAN].decode("latin1").replace("\r\n", "\n")
    if "CommandSet IranMissileFireCommandSet" not in iran_cs:
        iran_cs = iran_cs.rstrip() + "\n" + IRAN_CS_APPEND
    fm[CS_IRAN] = crlf(iran_cs)

    for path, (_name, old, new) in WHEELED.items():
        text = fm[path].decode("latin1").replace("\r\n", "\n")
        _req(old in text, f"{path} missing {old!r}")
        fm[path] = crlf(text.replace(old, new, 1))

    sys_txt = fm[SYS_PATH].decode("latin1").replace("\r\n", "\n")
    for name in SYS_UNITS:
        sys_txt = splice_named(sys_txt, name, retarget_scud)
    fm[SYS_PATH] = crlf(sys_txt)

    ov = fm[OV_PATH].decode("latin1").replace("\r\n", "\n")
    ov = splice_named(ov, "IranVehicleKhormshar", patch_khormshar_primary)
    for name in OV_SCUD:
        ov = splice_named(ov, name, retarget_scud)
    fm[OV_PATH] = crlf(ov)

    kh = fm[KH_FIRST].decode("latin1").replace("\r\n", "\n")
    fm[KH_FIRST] = crlf(splice_named(kh, "IranVehicleKhormshar", patch_khormshar_primary))

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
