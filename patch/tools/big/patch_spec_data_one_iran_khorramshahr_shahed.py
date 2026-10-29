#!/usr/bin/env python3
"""Iran-only live DATA patch: Khorramshahr start-game + Shahed-136 Fire/range.

Starts from the factory-complete DATA BIG (RS-24/DF-41 + prior last-wins).
Edits only:

- the live last-win IranVehicleKhormshar block inside
  Object_ZZZZ_ZzGlobalStoreFivePrereq.ini (no new Object overlay)
- Data\\INI\\Object\\Specter\\Iranian Army\\Wheeled\\ShahedLauncher.ini
- Data\\INI\\Object\\Specter\\Iranian Army\\Wheeled\\Iran_Khorram.ini BuildTime
- adds Data\\INI\\Weapon_ZZZZ_IranShahed136Launcher.ini (unique weapon name)
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path


SRC_SHA = "4d74a2f423914d31b4e5e58ff463929d3fc1bad965cc78e3743e950221346a52"

OV_PATH = r"Data\INI\Object_ZZZZ_ZzGlobalStoreFivePrereq.ini"
SH_PATH = r"Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini"
KH_PATH = r"Data\INI\Object\Specter\Iranian Army\Wheeled\Iran_Khorram.ini"
WPN_PATH = r"Data\INI\Weapon_ZZZZ_IranShahed136Launcher.ini"

CS_IRAQ = r"Data\INI\CommandSet_ZZZZ_ZZZIraqRadar.ini"
OBJ_IRAQ = r"Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini"
OBJ_SUPPLY = r"Data\INI\Object\zzzzz_SpecterSupplyCentreBuy"
WPN_TPY = r"Data\INI\Weapon_ZZZZ_ZZZZTpy2RadarCue.ini"
RS_PATH = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Wheeled\RS-24_Yars.ini"

OBJ_BLOCK = re.compile(
    r"(?ms)^(Object\s+IranVehicleKhormshar\b.*?)(?=^Object\s|\Z)"
)


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


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def _norm(path: str | None) -> str:
    return (path or "").replace("\\", "").replace("/", "").lower()


def patch_khormshar(block: str) -> str:
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
    block = re.sub(
        r"(?ms)^  Prerequisites\n    Object  = Iran_GlobalStore\n  End\n",
        "  Prerequisites\n  End\n",
        block,
        count=1,
    )
    block = re.sub(r"(?m)^  BuildTime       = 22\.0", "  BuildTime       = 10.0", block, count=1)
    block = re.sub(
        r"(?m)^  CommandSet             = Iraq_AlhussaienCommandSet",
        "  CommandSet             = Iraq_AlhussaienArmedCommandSet",
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
    if "Turret\n" not in block.replace("\r\n", "\n") and "Turret\r\n" not in block:
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


def patch_shahed(body: str) -> str:
    body = re.sub(
        r"(?ms)^  WeaponSet\n    Conditions = None \n    Weapon = PRIMARY   5x_Shahed136DroneSwarm\n  End\n",
        (
            "  WeaponSet\n"
            "    Conditions = None \n"
            "    Weapon = PRIMARY   Weapon_Iran_Shahed136Launcher\n"
            "  End\n"
        ),
        body,
        count=1,
    )
    body = re.sub(
        r"(?m)^  CommandSet    = AmericaTankCrusaderCommandSet",
        "  CommandSet    = Scud_B_CommandSet",
        body,
        count=1,
    )
    body = re.sub(r"(?m)^  VisionRange     = 600", "  VisionRange     = 3000", body, count=1)
    return body


def patch_khorram_time(body: str) -> str:
    return re.sub(r"(?m)^  BuildTime       = 54\.0", "  BuildTime       = 10.0", body, count=1)


def validate(file_map: dict[str, bytes]) -> None:
    ksrc, kbody = last_win_block(file_map, "Object", "IranVehicleKhormshar")
    _req(ksrc == OV_PATH, f"Khormshar live source {ksrc}")
    _req(field(kbody, "BuildTime").startswith("10"), f"Khormshar time {field(kbody, 'BuildTime')}")
    _req(field(kbody, "BuildCost") == "2500", "Khormshar cost")
    _req(field(kbody, "Side") == "Iran", "Khormshar Side")
    _req(field(kbody, "CommandSet") == "Iraq_AlhussaienArmedCommandSet", "Khormshar CS")
    _req("Iran_GlobalStore" not in (kbody or ""), "Khormshar still GlobalStore")
    _req("RiderChangeContain" not in (kbody or ""), "Khormshar rider remain")
    _req("ObjectCreationUpgrade" not in (kbody or ""), "Khormshar rearm remain")
    _req("Khormshar1_ICBM" in (kbody or ""), "Khormshar ICBM lost")
    _req(re.search(r"(?ms)WeaponSet\s+Conditions\s+=\s+None.*?Khormshar1_ICBM", (kbody or "").replace("\r\n", "\n")), "Khormshar None set")
    _req(field(kbody, "DisplayName") == "OBJECT:Khormshar", "Khormshar name")
    _req("Irn_Khormsh" in (kbody or ""), "Khormshar hull")

    defs = all_defs(file_map, "Object", "IranVehicleKhormshar")
    _req(OV_PATH in defs, "overlay lost Khormshar")

    ssrc, sbody = last_win_block(file_map, "Object", "IranVehicleShahedLauncher")
    _req(ssrc == SH_PATH, f"Shahed source {ssrc}")
    _req(field(sbody, "CommandSet") == "Scud_B_CommandSet", "Shahed CS")
    _req("Weapon_Iran_Shahed136Launcher" in (sbody or ""), "Shahed weapon")
    _req("5x_Shahed136DroneSwarm" not in (sbody or ""), "Shahed still swarm name")
    _req(field(sbody, "VisionRange") == "3000", "Shahed vision")
    _req(field(sbody, "BuildCost") == "1500", "Shahed cost")
    _req(field(sbody, "DisplayName") == "OBJECT:ShahedLauncher", "Shahed name")
    _req("Irn_ShhdLnchr" in (sbody or ""), "Shahed hull")
    _req(len(all_defs(file_map, "Object", "IranVehicleShahedLauncher")) == 1, "Shahed duplicate")

    wsrc, wbody = last_win_block(file_map, "Weapon", "Weapon_Iran_Shahed136Launcher")
    _req(wsrc == WPN_PATH, f"new weapon source {wsrc}")
    _req(field(wbody, "AttackRange") == "3000", "new weapon range")
    _req(field(wbody, "MinimumAttackRange").startswith("200"), "new weapon min")
    _req("AntiGround" in (wbody or "") and "Yes" in (wbody or ""), "new weapon AntiGround")
    _req("Shahed136_AI_Object" in (wbody or ""), "projectile")
    _req(field(wbody, "PrimaryDamage") == "1800", "damage changed")

    swarm_src, swarm = last_win_block(file_map, "Weapon", "5x_Shahed136DroneSwarm")
    _req(field(swarm, "AttackRange") == "1500", f"swarm range changed via {swarm_src}")

    rsrc, rbody = last_win_block(file_map, "Object", "Iran_Khorram")
    _req(rsrc == KH_PATH, f"Iran_Khorram source {rsrc}")
    _req(field(rbody, "BuildTime").startswith("10"), f"Iran_Khorram time {field(rbody, 'BuildTime')}")
    _req(field(rbody, "BuildCost") == "4980", "Iran_Khorram cost")
    _req("Weapon_Iran_Khorram" in (rbody or ""), "Iran_Khorram weapon")

    bsrc, bbody = last_win_block(file_map, "CommandButton", "Command_ConstructIranVehicleKhormshar")
    _req(re.search(r"(?im)^\s*Object\s+=\s+IranVehicleKhormshar", bbody or ""), "construct button moved")
    _req("NeededScience" not in (bbody or "") and "Upgrade" not in (bbody or ""), "construct button science")

    shb_src, shb = last_win_block(file_map, "CommandButton", "Command_ConstructIranVehicleShahedLauncher")
    _req(re.search(r"(?im)^\s*Object\s+=\s+IranVehicleShahedLauncher", shb or ""), "shahed button moved")

    cs_src, cs = last_win_block(file_map, "CommandSet", "IranWarfactoryCommandSet")
    _req("Command_ConstructIranVehicleKhormshar" in (cs or ""), "WF lost Khormshar")
    _req("Command_ConstructIranVehicleShahedLauncher" in (cs or ""), "WF lost Shahed")

    fire_src, fire = last_win_block(file_map, "CommandButton", "Command_FireMainWeapon")
    _req(fire_src and "FIRE_WEAPON" in (fire or ""), "FireMainWeapon missing")
    _req("NEED_SPECIAL_POWER_SCIENCE" not in (fire or ""), "FireMainWeapon science")

    armed_src, armed = last_win_block(file_map, "CommandSet", "Iraq_AlhussaienArmedCommandSet")
    _req("Command_IraqAlAbbasICBMFire" in (armed or ""), "armed CS fire")

    irq_src, _ = last_win_block(file_map, "Object", "Iraq_RadarStation")
    _req(irq_src == OBJ_IRAQ, f"Iraq radar last-win {irq_src}")
    am_src, _ = last_win_block(file_map, "Object", "AmericaSupplyCenter")
    _req(_norm(OBJ_SUPPLY) in _norm(am_src), f"Supply last-win {am_src}")
    wsrc, _ = last_win_block(file_map, "Weapon", "92N6R_FireControlDataLink")
    _req(wsrc == WPN_TPY, f"DataLink last-win {wsrc}")
    rs_src, rs_body = last_win_block(file_map, "Object", "RussiaVehicleRS24")
    _req(rs_src == RS_PATH, f"RS24 last-win {rs_src}")
    _req("RiderChangeContain" not in (rs_body or ""), "RS24 rider returned")

    fattah_src, fattah = last_win_block(file_map, "Object", "IranVehicleFattah")
    _req("Iran_GlobalStore" in (fattah or ""), "Fattah prereq stripped")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-big", type=Path, required=True)
    ap.add_argument("--out-big", type=Path, required=True)
    ap.add_argument(
        "--weapon",
        type=Path,
        default=Path("patch/Data/INI/Weapon_ZZZZ_IranShahed136Launcher.ini"),
    )
    args = ap.parse_args()

    digest_src = sha256(args.src_big)
    _req(digest_src == SRC_SHA, f"src BIG is not factory-complete ({digest_src})")

    fm = read_big(args.src_big)

    ov = fm[OV_PATH].decode("latin1")
    m = OBJ_BLOCK.search(ov.replace("\r\n", "\n"))
    _req(m is not None, "IranVehicleKhormshar missing from overlay")
    patched = patch_khormshar(m.group(1))
    ov_new = ov.replace("\r\n", "\n").replace(m.group(1), patched, 1)
    fm[OV_PATH] = crlf(ov_new)

    sh = fm[SH_PATH].decode("latin1")
    fm[SH_PATH] = crlf(patch_shahed(sh.replace("\r\n", "\n")))

    kh = fm[KH_PATH].decode("latin1")
    fm[KH_PATH] = crlf(patch_khorram_time(kh.replace("\r\n", "\n")))

    _req(args.weapon.is_file(), f"missing {args.weapon}")
    fm[WPN_PATH] = crlf(args.weapon.read_text(encoding="latin1"))

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
    print(f"  splice {OV_PATH} IranVehicleKhormshar")
    print(f"  replace {SH_PATH}")
    print(f"  replace {KH_PATH} BuildTime")
    print(f"  add {WPN_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
