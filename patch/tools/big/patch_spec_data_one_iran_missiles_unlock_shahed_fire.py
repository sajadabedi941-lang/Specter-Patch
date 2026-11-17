#!/usr/bin/env python3
"""Unlock live Iran missiles and give Shahed-136 a fireable ballistic shot.

Starts from the #706 DATA BIG. PR #706 last-won only the Khormshar overlay and
left Shahed pointing at Scud_B_CommandSet + Shahed136_AI_Object. In-game ZH
still had Iran missiles locked and Shahed Fire dead.

Object names in this pack are first-win (same lesson as RS-24/DF-41):
Khormshar.ini / Fattah.ini / Iran_System.ini are the defs the game reads.
CommandSet.ini / CommandButton.ini are stock paths and can be first-won by
INIZH, so Fire uses unique extra-file names the Objects point at.

Edits only Iran missile / factory / Shahed fire paths. No ART.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path


SRC_SHA = "592b49746f14425213309be1cabc5343a1b98aefe9dd977cb27f3cb8e82a1eb4"

OV_PATH = r"Data\INI\Object_ZZZZ_ZzGlobalStoreFivePrereq.ini"
KH_FIRST = r"Data\INI\Object\Specter\Iranian Army\Wheeled\Khormshar.ini"
FA_FIRST = r"Data\INI\Object\Specter\Iranian Army\Wheeled\Fattah.ini"
SYS_PATH = r"Data\INI\Object\Specter\Iranian Army\Iran_System.ini"
SH_PATH = r"Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini"
MF_PATH = r"Data\INI\Object\Specter\Iranian Army\Buildings\Iran_MissileFactory.ini"
KH_TEL = r"Data\INI\Object\Specter\Iranian Army\Wheeled\Iran_Khorram.ini"
WPN_PATH = r"Data\INI\Weapon_ZZZZ_IranShahed136Launcher.ini"
BTN_PATH = r"Data\INI\CommandButton_ZZZZ_ZzzIranMissileFire.ini"
CS_PATH = r"Data\INI\CommandSet_ZZZZ_ZzzIranMissileFire.ini"
PROJ_PATH = r"Data\INI\Object\Specter\Iranian Army\Iran_Shahed136_FireProjectile.ini"

CS_IRAQ = r"Data\INI\CommandSet_ZZZZ_ZZZIraqRadar.ini"
OBJ_IRAQ = r"Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini"
OBJ_SUPPLY = r"Data\INI\Object\zzzzz_SpecterSupplyCentreBuy"
WPN_TPY = r"Data\INI\Weapon_ZZZZ_ZZZZTpy2RadarCue.ini"
RS_PATH = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Wheeled\RS-24_Yars.ini"
FATEH_PATH = r"Data\INI\Object\Specter\Iranian Army\Wheeled\Fateh313.ini"

IRAN_OV = [
    "IranVehicleKhormshar",
    "IranVehicleFattah",
    "IranVehicleFattah2",
    "IranVehicleZolfagharM",
    "IranVehicleDezfulPenetrator",
]
SYS_UNITS = [
    "IranVehicleFattah2",
    "IranVehicleZolfagharM",
    "IranVehicleDezfulPenetrator",
]


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


def all_defs(file_map: dict[str, bytes], kind: str, name: str) -> list[str]:
    pat = re.compile(rf"(?m)^{kind}\s+{re.escape(name)}\b")
    hits = []
    for path, raw in sorted(file_map.items(), key=lambda kv: kv[0].lower()):
        if not path.lower().endswith(".ini"):
            continue
        if pat.search(raw.decode("latin1")):
            hits.append(path)
    return hits


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
    return re.search(
        rf"(?ms)^(Object\s+{re.escape(name)}\b.*?)(?=^Object\s|\Z)",
        text,
    )


def empty_prereq(block: str) -> str:
    new, n = re.subn(
        r"(?ms)^  Prerequisites\n(?:    Object[^\n]*\n)+  End\n",
        "  Prerequisites\n  End\n",
        block,
        count=1,
    )
    _req(n == 1, f"prereq splice missed in block starting {block[:60]!r}")
    return new


def patch_khormshar_first(block: str) -> str:
    block = re.sub(
        r"(?ms)^  WeaponSet\n    Conditions = WEAPON_RIDER1\n.*?^  End\n",
        (
            "  WeaponSet\n"
            "    Conditions = None\n"
            "    Weapon            = SECONDARY  Khormshar1_ICBM\n"
            "    AutoChooseSources = SECONDARY  NONE\n"
            "    Weapon            = TERTIARY   DeployHeavyWeapons\n"
            "    AutoChooseSources = TERTIARY   NONE\n"
            "  End\n"
            "  WeaponSet\n"
            "    Conditions = WEAPON_RIDER1\n"
            "    Weapon            = SECONDARY  NONE\n"
            "    AutoChooseSources = SECONDARY  NONE\n"
            "    Weapon            = TERTIARY   DeployHeavyWeapons\n"
            "    AutoChooseSources = TERTIARY   NONE\n"
            "  End\n"
        ),
        block,
        count=1,
    )
    block = empty_prereq(block)
    block = re.sub(r"(?m)^  BuildTime       = 22\.0", "  BuildTime       = 10.0", block, count=1)
    block = re.sub(
        r"(?m)^  CommandSet             = Iraq_AlhussaienCommandSet",
        "  CommandSet             = IranKhorramshahrFireCommandSet",
        block,
        count=1,
    )
    block = re.sub(
        r"(?ms)^  Behavior = RiderChangeContain ModuleTag_WarheadRider\n.*?^  End\n",
        "",
        block,
        count=1,
    )
    block = re.sub(
        r"(?ms)^  Behavior = ObjectCreationUpgrade ModuleTag_Rearm\n.*?^  End\n",
        "",
        block,
        count=1,
    )
    if "Turret\n" not in block.replace("\r\n", "\n"):
        block = block.replace(
            "  Behavior = DeployStyleAIUpdate ModuleTag_JG704\n"
            "    AutoAcquireEnemiesWhenIdle = No\n",
            "  Behavior = DeployStyleAIUpdate ModuleTag_JG704\n"
            "    Turret\n"
            "      TurretTurnRate        = 0\n"
            "      TurretPitchRate       = 0\n"
            "      ControlledWeaponSlots = PRIMARY SECONDARY TERTIARY\n"
            "      NaturalTurretAngle    = 0\n"
            "      InitiallyDisabled     = Yes\n"
            "    End\n"
            "    AutoAcquireEnemiesWhenIdle = No\n",
            1,
        )
    return block


def patch_khormshar_overlay(block: str) -> str:
    block = re.sub(
        r"(?m)^  CommandSet             = Iraq_AlhussaienArmedCommandSet",
        "  CommandSet             = IranKhorramshahrFireCommandSet",
        block,
        count=1,
    )
    if "IranIndustrialComplex" in block or "Iran_GlobalStore" in prereq_inner(block):
        block = empty_prereq(block)
    return block


def patch_factory(body: str) -> str:
    new, n = re.subn(
        r"(?m)^    Object = IranSupplyCenter SouthKorea_SupplyCenter .+$",
        "    Object = IranSupplyCenter",
        body,
        count=1,
    )
    _req(n == 1, "missile factory prereq line missing")
    return new


def patch_shahed(body: str) -> str:
    new, n = re.subn(
        r"(?m)^  CommandSet    = Scud_B_CommandSet",
        "  CommandSet    = IranShahed136FireCommandSet",
        body,
        count=1,
    )
    _req(n == 1, "shahed CommandSet splice missed")
    return new


def splice_named(text: str, name: str, mutator) -> str:
    m = object_block(text, name)
    _req(m is not None, f"{name} missing")
    patched = mutator(m.group(1))
    return text[: m.start(1)] + patched + text[m.end(1) :]


def unlocked_prereq(body: str | None) -> bool:
    inner = prereq_inner(body)
    if not inner:
        return True
    banned = (
        "IranIndustrialComplex",
        "Iran_GlobalStore",
        "IranRadarStation",
        "IranWarFactory",
    )
    return not any(x in inner for x in banned)


def validate(file_map: dict[str, bytes]) -> None:
    ksrc, kfirst = first_win_block(file_map, "Object", "IranVehicleKhormshar")
    _req(ksrc == KH_FIRST, f"Khormshar first-win {ksrc}")
    _req(field(kfirst, "BuildTime").startswith("10"), f"Khormshar first time {field(kfirst, 'BuildTime')}")
    _req(field(kfirst, "BuildCost") == "2500", "Khormshar cost")
    _req(field(kfirst, "CommandSet") == "IranKhorramshahrFireCommandSet", "Khormshar first CS")
    _req(unlocked_prereq(kfirst), f"Khormshar first prereq {prereq_inner(kfirst)}")
    _req("RiderChangeContain" not in (kfirst or ""), "Khormshar first rider remain")
    _req("ObjectCreationUpgrade" not in (kfirst or ""), "Khormshar first rearm remain")
    _req(
        re.search(
            r"(?ms)WeaponSet\s+Conditions\s+=\s+None.*?Khormshar1_ICBM",
            (kfirst or "").replace("\r\n", "\n"),
        ),
        "Khormshar first None set",
    )
    _req("Irn_Khormsh" in (kfirst or ""), "Khormshar hull")
    _req(field(kfirst, "DisplayName") == "OBJECT:Khormshar", "Khormshar name")

    klast_src, klast = last_win_block(file_map, "Object", "IranVehicleKhormshar")
    _req(klast_src == OV_PATH, f"Khormshar last {klast_src}")
    _req(field(klast, "CommandSet") == "IranKhorramshahrFireCommandSet", "Khormshar last CS")
    _req(field(klast, "BuildTime").startswith("10"), "Khormshar last time")
    _req(unlocked_prereq(klast), f"Khormshar last prereq {prereq_inner(klast)}")

    for name, first_path in [
        ("IranVehicleFattah", FA_FIRST),
        ("IranVehicleFattah2", SYS_PATH),
        ("IranVehicleZolfagharM", SYS_PATH),
        ("IranVehicleDezfulPenetrator", SYS_PATH),
    ]:
        fsrc, fbody = first_win_block(file_map, "Object", name)
        lsrc, lbody = last_win_block(file_map, "Object", name)
        _req(fsrc == first_path, f"{name} first {fsrc}")
        _req(lsrc == OV_PATH, f"{name} last {lsrc}")
        _req(unlocked_prereq(fbody), f"{name} first prereq {prereq_inner(fbody)}")
        _req(unlocked_prereq(lbody), f"{name} last prereq {prereq_inner(lbody)}")
        _req(field(fbody, "CommandSet") == "Scud_B_CommandSet", f"{name} CS changed")

    msrc, mbody = first_win_block(file_map, "Object", "Iran_MissileFactory")
    _req(msrc == MF_PATH, f"factory source {msrc}")
    _req(len(all_defs(file_map, "Object", "Iran_MissileFactory")) == 1, "factory duplicate")
    _req(prereq_inner(mbody) == "Object = IranSupplyCenter", f"factory prereq {prereq_inner(mbody)}")
    _req("SouthKorea_SupplyCenter" not in (mbody or ""), "factory still AND-locked")

    ssrc, sbody = first_win_block(file_map, "Object", "IranVehicleShahedLauncher")
    _req(ssrc == SH_PATH, f"Shahed first {ssrc}")
    _req(len(all_defs(file_map, "Object", "IranVehicleShahedLauncher")) == 1, "Shahed duplicate")
    _req(field(sbody, "CommandSet") == "IranShahed136FireCommandSet", "Shahed CS")
    _req("Weapon_Iran_Shahed136Launcher" in (sbody or ""), "Shahed weapon")
    _req(field(sbody, "VisionRange") == "3000", "Shahed vision")
    _req(field(sbody, "BuildCost") == "1500", "Shahed cost")
    _req("Irn_ShhdLnchr" in (sbody or ""), "Shahed hull")

    wsrc, wbody = last_win_block(file_map, "Weapon", "Weapon_Iran_Shahed136Launcher")
    _req(wsrc == WPN_PATH, f"weapon source {wsrc}")
    _req(field(wbody, "AttackRange") == "3000", "weapon range")
    _req(field(wbody, "MinimumAttackRange").startswith("200"), "weapon min")
    _req("AntiGround" in (wbody or "") and "Yes" in (wbody or ""), "weapon AntiGround")
    _req("Iran_Shahed136_FireProjectile" in (wbody or ""), "ballistic projectile")
    _req("Shahed136_AI_Object" not in (wbody or ""), "swarm projectile remain")
    _req(field(wbody, "PrimaryDamage") == "1800", "damage changed")

    psrc, pbody = first_win_block(file_map, "Object", "Iran_Shahed136_FireProjectile")
    _req(psrc == PROJ_PATH, f"projectile source {psrc}")
    _req("DumbProjectileBehavior" in (pbody or ""), "projectile not dumb")
    _req("PROJECTILE" in (pbody or "") and "BALLISTIC_MISSILE" in (pbody or ""), "projectile kind")
    _req("SELECTABLE" not in (pbody or "") and "CAN_ATTACK" not in (pbody or ""), "projectile still unit")
    _req("Irn_Shahed136" in (pbody or ""), "projectile model")

    bsrc, bbody = first_win_block(file_map, "CommandButton", "Command_IranFirePrimary")
    _req(bsrc == BTN_PATH, f"fire button source {bsrc}")
    _req("FIRE_WEAPON" in (bbody or "") and "PRIMARY" in (bbody or ""), "fire button")
    _req("NEED_SPECIAL_POWER_SCIENCE" not in (bbody or ""), "fire button science")

    cssrc, csbody = first_win_block(file_map, "CommandSet", "IranShahed136FireCommandSet")
    _req(cssrc == CS_PATH, f"shahed CS source {cssrc}")
    _req("Command_IranFirePrimary" in (csbody or ""), "shahed CS fire")

    kcssrc, kcs = first_win_block(file_map, "CommandSet", "IranKhorramshahrFireCommandSet")
    _req(kcssrc == CS_PATH, f"khorm CS source {kcssrc}")
    _req("Command_IranFireSecondary" in (kcs or ""), "khorm CS fire")

    swarm_src, swarm = last_win_block(file_map, "Weapon", "5x_Shahed136DroneSwarm")
    _req(field(swarm, "AttackRange") == "1500", f"swarm range changed via {swarm_src}")

    rsrc, rbody = last_win_block(file_map, "Object", "Iran_Khorram")
    _req(rsrc == KH_TEL, f"Iran_Khorram source {rsrc}")
    _req(field(rbody, "BuildTime").startswith("10"), f"Iran_Khorram time {field(rbody, 'BuildTime')}")
    _req(unlocked_prereq(rbody), "Iran_Khorram prereq")

    ftsrc, ftbody = first_win_block(file_map, "Object", "IranVehicleFateh313")
    _req(ftsrc == FATEH_PATH, f"Fateh source {ftsrc}")
    _req(field(ftbody, "CommandSet") == "Scud_B_CommandSet", "Fateh CS changed")
    _req("2x_SRBM_Fateh313_HE" in (ftbody or ""), "Fateh weapon")

    silo_src, silo = first_win_block(file_map, "Object", "IranSejjilSilo")
    _req("IranIndustrialComplex" in prereq_inner(silo) or "Iran_GlobalStore" in prereq_inner(silo), "Sejjil unlocked by mistake")

    canary_src, canary = last_win_block(file_map, "Object", "RussiaVehicle96L6TSP")
    _req(canary_src == OV_PATH, f"96L6 last {canary_src}")
    _req("Russia_GlobalStore" in prereq_inner(canary), "non-Iran GlobalStore stripped")

    irq_src, _ = last_win_block(file_map, "Object", "Iraq_RadarStation")
    _req(irq_src == OBJ_IRAQ, f"Iraq radar last-win {irq_src}")
    am_src, _ = last_win_block(file_map, "Object", "AmericaSupplyCenter")
    _req(_norm(OBJ_SUPPLY) in _norm(am_src), f"Supply last-win {am_src}")
    wsrc, _ = last_win_block(file_map, "Weapon", "92N6R_FireControlDataLink")
    _req(wsrc == WPN_TPY, f"DataLink last-win {wsrc}")
    rs_src, rs_body = last_win_block(file_map, "Object", "RussiaVehicleRS24")
    _req(rs_src == RS_PATH, f"RS24 last-win {rs_src}")
    _req("RiderChangeContain" not in (rs_body or ""), "RS24 rider returned")

    wf_src, wf = last_win_block(file_map, "CommandSet", "IranWarfactoryCommandSet")
    _req("Command_ConstructIranVehicleKhormshar" in (wf or ""), "WF lost Khormshar")
    _req("Command_ConstructIranVehicleShahedLauncher" in (wf or ""), "WF lost Shahed")
    _req("Command_ConstructIranVehicleFattah" in (wf or ""), "WF lost Fattah")
    _req("Command_ConstructIranVehicleFateh313" in (wf or ""), "WF lost Fateh")

    mfcs_src, mfcs = last_win_block(file_map, "CommandSet", "Iran_MissileFactoryCommandSet")
    _req("CB_IRAN_MISSILE_A" in (mfcs or "") and "CB_IRAN_MISSILE_G" in (mfcs or ""), "MF roster")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    ap.add_argument("--weapon", type=Path, default=Path("patch/Data/INI/Weapon_ZZZZ_IranShahed136Launcher.ini"))
    ap.add_argument("--button", type=Path, default=Path("patch/Data/INI/CommandButton_ZZZZ_ZzzIranMissileFire.ini"))
    ap.add_argument("--commandset", type=Path, default=Path("patch/Data/INI/CommandSet_ZZZZ_ZzzIranMissileFire.ini"))
    ap.add_argument(
        "--projectile",
        type=Path,
        default=Path("patch/Data/INI/Object/Specter/Iranian Army/Iran_Shahed136_FireProjectile.ini"),
    )
    args = ap.parse_args()

    digest_src = sha256(args.src_big)
    _req(digest_src == SRC_SHA, f"src BIG is not #706 ({digest_src})")

    for extra in (args.weapon, args.button, args.commandset, args.projectile):
        _req(extra.is_file(), f"missing {extra}")

    fm = read_big(args.src_big)

    kh = fm[KH_FIRST].decode("latin1").replace("\r\n", "\n")
    fm[KH_FIRST] = crlf(splice_named(kh, "IranVehicleKhormshar", patch_khormshar_first))

    fa = fm[FA_FIRST].decode("latin1").replace("\r\n", "\n")
    fm[FA_FIRST] = crlf(splice_named(fa, "IranVehicleFattah", empty_prereq))

    sys_txt = fm[SYS_PATH].decode("latin1").replace("\r\n", "\n")
    for name in SYS_UNITS:
        sys_txt = splice_named(sys_txt, name, empty_prereq)
    fm[SYS_PATH] = crlf(sys_txt)

    ov = fm[OV_PATH].decode("latin1").replace("\r\n", "\n")
    ov = splice_named(ov, "IranVehicleKhormshar", patch_khormshar_overlay)
    for name in IRAN_OV:
        if name == "IranVehicleKhormshar":
            continue
        ov = splice_named(ov, name, empty_prereq)
    fm[OV_PATH] = crlf(ov)

    fm[MF_PATH] = crlf(patch_factory(fm[MF_PATH].decode("latin1").replace("\r\n", "\n")))
    fm[SH_PATH] = crlf(patch_shahed(fm[SH_PATH].decode("latin1").replace("\r\n", "\n")))

    fm[WPN_PATH] = crlf(args.weapon.read_text(encoding="latin1"))
    fm[BTN_PATH] = crlf(args.button.read_text(encoding="latin1"))
    fm[CS_PATH] = crlf(args.commandset.read_text(encoding="latin1"))
    fm[PROJ_PATH] = crlf(args.projectile.read_text(encoding="latin1"))

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
    print(f"  first-win {KH_FIRST}")
    print(f"  first-win {FA_FIRST}")
    print(f"  first-win {SYS_PATH} {SYS_UNITS}")
    print(f"  overlay {OV_PATH} {IRAN_OV}")
    print(f"  factory {MF_PATH}")
    print(f"  shahed  {SH_PATH}")
    print(f"  add {BTN_PATH}")
    print(f"  add {CS_PATH}")
    print(f"  add {PROJ_PATH}")
    print(f"  replace {WPN_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
