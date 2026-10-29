#!/usr/bin/env python3
"""Fill missile-factory slot M from the live RS24Yars TEL.

Source: PR #712 / missile-factory-klmn _SPEC_DATA_ONE.big
(SHA ad4ded5faf0a83a4886f4cc55f42b63a7b53bdd26cf2bea31e005fdbba852e16).

Live DATA has no Object named RS_24Yars. The real RS24Yars TEL is
Object RussiaVehicleRS24 in Data\\INI\\Object\\Specter\\Armed Forces Of
Russian Federation\\Wheeled\\RS-24_Yars.ini. Weapon.ini labels that
chain "; ----------- Russia RS24Yars --------------". The construct
button is Command_ConstructRussiaVehicleRS24 (Object=RussiaVehicleRS24,
image rus_rs24). Projectile is RS24_Yars_Object.

A factory-only copy is required (same reason as #712 L/N):
  * live BuildCost is 3500, required factory price is 27000
  * live Prerequisites = RussiaWarFactory (would lock every other country)
  * live CommandSet is Iraq_AlhussaienArmedCommandSet (rider ICBM, not Fire)
  * live weapon RS24_Yars_ICBM_1x_Warhead reloads (no AutoReloadsClip=No)
  * changing any of those on the original would last-win Russia's WF TEL

K/L/N from #712 stay. Only ControlBar slot 13 (M) is rewritten.
Iraq A-J and CB_MISSILE_K stay; Iraq slot M (was CB_MISSILE_M / BM-21)
is replaced by the shared RS24 button. Iraq A-M buttons are not copied
onto other countries.

Egypt and Arabic Alliance have no missile-factory CommandSet in live DATA.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
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
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def dec(blob: bytes) -> str:
    return blob.decode("latin1")


def enc(text: str) -> bytes:
    return text.encode("latin1")


def nl_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def crlf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").strip("\r\n") + "\r\n"


ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/MISSILE_FACTORY_KLMN/_SPEC_DATA_ONE.big"
SRC_SHA = "ad4ded5faf0a83a4886f4cc55f42b63a7b53bdd26cf2bea31e005fdbba852e16"
OUT_DIR = ROOT / "Release/MISSILE_FACTORY_M_RS24"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
OUT_SHA = OUT_DIR / "_SPEC_DATA_ONE.big.sha256"
OUT_CS = OUT_DIR / "CommandSet.ini"
OUT_CS_SHA = OUT_DIR / "CommandSet.ini.sha256"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_RS24 = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Wheeled\RS-24_Yars.ini"
K_KHOR = r"Data\INI\Object\Specter\Iranian Army\Wheeled\Khormshar.ini"
K_DF41 = r"Data\INI\Object\Specter\PLA\Wheeled\DF41.ini"
K_NEW_KHOR = r"Data\INI\Object\Specter\FactoryKLMN\Factory_KhormsharOnce.ini"
K_NEW_DF41 = r"Data\INI\Object\Specter\FactoryKLMN\Factory_DF41Once.ini"
K_NEW_RS24 = r"Data\INI\Object\Specter\FactoryKLMN\Factory_RS24YarsOnce.ini"
K_ABBAS = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini"

IRAQ_K_OBJECT = "Iraq_Alhussaien"
IRAQ_K_COST = "20000"

FACTORY_SETS = [
    "America_MissileFactoryCommandSet",
    "Britain_MissileFactoryCommandSet",
    "China_MissileFactoryCommandSet",
    "France_MissileFactoryCommandSet",
    "Germany_MissileFactoryCommandSet",
    "India_MissileFactoryCommandSet",
    "Iran_MissileFactoryCommandSet",
    "Israel_MissileFactoryCommandSet",
    "Italy_MissileFactoryCommandSet",
    "Japan_MissileFactoryCommandSet",
    "Libya_MissileFactoryCommandSet",
    "NorthKorea_MissileFactoryCommandSet",
    "Pakistan_MissileFactoryCommandSet",
    "Russia_MissileFactoryCommandSet",
    "SaudiArabia_MissileFactoryCommandSet",
    "SouthAfrica_MissileFactoryCommandSet",
    "SouthKorea_MissileFactoryCommandSet",
    "Spain_MissileFactoryCommandSet",
    "Sweden_MissileFactoryCommandSet",
    "Syria_MissileFactoryCommandSet",
    "Turkey_MissileFactoryCommandSet",
    "UAE_MissileFactoryCommandSet",
    "Ukraine_MissileFactoryCommandSet",
    "Vietnam_MissileFactoryCommandSet",
]
IRAQ_FACTORY_SET = "Iraq_AlFahdMissileFactoryCommandSet"
IRAQ_BUILDING_SET = "Iraq_AlFahdMissileFactoryBuildingCommandSet"

# Labels / image taken from live Command_ConstructRussiaVehicleRS24.
NEW_BUTTON = """
; Shared missile-factory slot M. Live RS24Yars TEL is RussiaVehicleRS24.
; Factory copy only: price 27000 / one-clip / no RussiaWarFactory.
CommandButton CB_FACTORY_SLOT_M
  Command       = UNIT_BUILD
  Object        = Factory_RS24YarsOnce
  TextLabel     = CONTROLBAR:ConstructRussiaVehicleRS24
  ButtonImage   = rus_rs24
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaVehicleRS24
End
"""

# Live RS24_Yars_ICBM_1x_Warhead fields + AutoReloadsClip=No + AntiGround.
# Does not last-win the original weapon name.
RS24_WEAPON = """
; One-clip factory RS24Yars. Does not last-win RS24_Yars_ICBM_1x_Warhead.
; Live source: Weapon.ini "; ----------- Russia RS24Yars --------------"
Weapon Weapon_Factory_RS24YarsOnce
  PrimaryDamage               = 1
  PrimaryDamageRadius         = 0
  AttackRange                 = 2500
  MinimumAttackRange          = 1500
  PreAttackDelay              = 3600
  PreAttackType               = PER_SHOT
  DamageType                  = FLAME
  FireFX                      = FX_ICBM_LaunchSteam
  FireOCL                     = OCL_HussienMissileDisarm
  ProjectileObject            = RS24_Yars_Object
  AntiGround                  = Yes
  RadiusDamageAffects         = ALLIES ENEMIES NEUTRALS
  DelayBetweenShots           = 1
  ClipSize                    = 1
  ClipReloadTime              = 4000
  AutoReloadsClip             = No
  AcceptableAimDelta          = 360
  ShowsAmmoPips               = Yes
End
"""


def extract_object(text: str, obj_name: str) -> str:
    nl = nl_of(text)
    m = re.search(
        rf"^Object {re.escape(obj_name)}\s*{re.escape(nl)}(.*?)(?=^Object |\Z)",
        text,
        re.M | re.S,
    )
    if not m:
        raise RuntimeError(f"Object {obj_name} missing")
    return m.group(0)


def show_missile_except_disarmed(block: str) -> str:
    """Show MISSILE01 on the factory TEL; keep hide on RIDER1 (FireOCL) and rubble."""
    nl = nl_of(block)
    lines = block.splitlines()
    out: list[str] = []
    in_main = False
    cond = ""
    state_lines: list[str] = []
    injected_feedback = False

    def flush_state(buf: list[str], cond_flags: str) -> list[str]:
        if not buf:
            return buf
        flags = cond_flags.upper()
        is_rider1 = "RIDER1" in flags
        is_rubble = ("RUBBLE" in flags) and ("RIDER" not in flags)
        joined = nl.join(buf)
        has_show = bool(re.search(r"ShowSubObject\s*=\s*MISSILE01\b", joined, re.I))
        result: list[str] = []
        for line in buf:
            if re.search(r"HideSubObject\s*=\s*MISSILE01\b", line, re.I):
                if is_rider1 or is_rubble:
                    result.append(line)
                else:
                    result.append(re.sub(r"HideSubObject", "ShowSubObject", line, count=1))
            else:
                result.append(line)
        if not is_rider1 and not is_rubble:
            if not has_show and not any(
                re.search(r"ShowSubObject\s*=\s*MISSILE01\b", ln, re.I) for ln in result
            ):
                result.insert(-1, "      ShowSubObject     = MISSILE01")
        return result

    i = 0
    while i < len(lines):
        line = lines[i]
        if re.search(r"Draw\s*=\s*W3DTruckDraw\s+ModuleTag_01\b", line):
            in_main = True
            out.append(line)
            i += 1
            continue
        if in_main and (not injected_feedback) and "OkToChangeModelColor" in line:
            out.append(line)
            out.append("    ProjectileBoneFeedbackEnabledSlots = PRIMARY SECONDARY")
            injected_feedback = True
            i += 1
            continue
        if in_main and re.match(r"\s*TrackMarks\s*=", line):
            if state_lines:
                out.extend(flush_state(state_lines, cond))
                state_lines = []
            in_main = False
            out.append(line)
            i += 1
            continue
        if in_main:
            if re.match(r"\s*DefaultConditionState\b", line) or re.match(
                r"\s*ConditionState\b", line
            ):
                if state_lines:
                    out.extend(flush_state(state_lines, cond))
                    state_lines = []
                cond = line.split(";", 1)[0]
                state_lines = [line]
                i += 1
                continue
            if state_lines:
                state_lines.append(line)
                if re.match(r"\s*End\s*$", line.split(";", 1)[0]):
                    out.extend(flush_state(state_lines, cond))
                    state_lines = []
                    cond = ""
                i += 1
                continue
        out.append(line)
        i += 1
    if state_lines:
        out.extend(flush_state(state_lines, cond))
    text = nl.join(out)
    if not text.endswith(nl):
        text += nl
    if "ProjectileBoneFeedbackEnabledSlots" not in text:
        raise RuntimeError("failed to inject ProjectileBoneFeedbackEnabledSlots")
    if not re.search(r"ShowSubObject\s*=\s*MISSILE01", text):
        raise RuntimeError("failed to show MISSILE01")
    return text


def upsert_slots(body: str, slots: dict[int, str]) -> str:
    nl = nl_of(body)
    lines = body.splitlines()
    have: set[int] = set()
    out: list[str] = []
    for line in lines:
        m = re.match(r"^(\s*)(\d+)\s*=\s*(\S+)", line)
        if m:
            num = int(m.group(2))
            if num in slots:
                out.append(f"{m.group(1)}{num} = {slots[num]}")
                have.add(num)
                continue
        if re.match(r"^\s*End\s*$", line.split(";", 1)[0]):
            indent = "  "
            for num in sorted(slots):
                if num not in have:
                    out.append(f"{indent}{num} = {slots[num]}")
                    have.add(num)
        out.append(line)
    missing = set(slots) - have
    if missing:
        raise RuntimeError(f"failed to write slots {missing}")
    text = nl.join(out)
    if not text.endswith(nl):
        text += nl
    return text


def patch_commandset(text: str) -> str:
    nl = nl_of(text)
    m_slots = {13: "CB_FACTORY_SLOT_M"}

    def one(name: str) -> None:
        nonlocal text
        m = re.search(
            rf"(^CommandSet {re.escape(name)}\s*{re.escape(nl)})(.*?)(?=^CommandSet |\Z)",
            text,
            re.M | re.S,
        )
        if not m:
            raise RuntimeError(f"CommandSet {name} missing from CommandSet.ini")
        new_body = upsert_slots(m.group(2), m_slots)
        text = text[: m.start()] + m.group(1) + new_body + text[m.end() :]

    for name in FACTORY_SETS:
        one(name)
    one(IRAQ_FACTORY_SET)
    return text


def patch_commandbutton(text: str) -> str:
    nl = nl_of(text)
    if "CommandButton CB_FACTORY_SLOT_M" in text:
        raise RuntimeError("factory M button already present")
    if "CommandButton CB_FACTORY_SLOT_K" not in text:
        raise RuntimeError("#712 K button missing from source")
    if not text.endswith(nl):
        text += nl
    return text + nl + crlf(NEW_BUTTON).replace("\r\n", nl)


def patch_weapon_ini(text: str) -> str:
    nl = nl_of(text)
    if "Weapon Weapon_Factory_RS24YarsOnce" in text:
        raise RuntimeError("factory RS24 weapon already present")
    if "Weapon Weapon_Factory_KhormsharOnce" not in text:
        raise RuntimeError("#712 L weapon missing from source")
    if not text.endswith(nl):
        text += nl
    return text + nl + crlf(RS24_WEAPON).replace("\r\n", nl)


def make_rs24_once(src: str) -> str:
    block = extract_object(src, "RussiaVehicleRS24")
    header = (
        "; SPECTER factory-only copy of live Object RussiaVehicleRS24\r\n"
        "; (Weapon.ini name: Russia RS24Yars). Unique path so ThingFactory\r\n"
        "; first-win does not replace the War Factory TEL.\r\n"
        "; Why a copy: BuildCost 27000 vs live 3500; no RussiaWarFactory;\r\n"
        "; FactoryOnceFireCommandSet instead of Iraq_AlhussaienArmedCommandSet;\r\n"
        "; one-clip Weapon_Factory_RS24YarsOnce; Show MISSILE01.\r\n"
        "; Live file RS-24_Yars.ini is not modified.\r\n"
        "\r\n"
    )
    block = block.replace("Object RussiaVehicleRS24", "Object Factory_RS24YarsOnce", 1)
    block = re.sub(r"BuildCost\s*=\s*\S+", "BuildCost       = 27000", block, count=1)
    block = re.sub(
        r"Prerequisites\s*\r?\n\s*Object\s*=\s*RussiaWarFactory\s*\r?\n\s*End",
        "Prerequisites\r\n  End",
        block,
        count=1,
    )
    block = block.replace(
        "CommandSet             = Iraq_AlhussaienArmedCommandSet",
        "CommandSet             = FactoryOnceFireCommandSet",
    )
    block = block.replace("RS24_Yars_ICBM_1x_Warhead", "Weapon_Factory_RS24YarsOnce")
    block = re.sub(
        r"Weapon\s+=\s+SECONDARY\s+RS24_Yars_ICBM_4x_Warhead",
        "Weapon            = SECONDARY  NONE",
        block,
    )
    block = show_missile_except_disarmed(block)
    if "BuildCost       = 27000" not in block:
        raise RuntimeError("RS24 once cost not set")
    if "RussiaWarFactory" in block:
        raise RuntimeError("RS24 once still requires RussiaWarFactory")
    if "FactoryOnceFireCommandSet" not in block:
        raise RuntimeError("RS24 once CommandSet not set")
    if "Iraq_AlhussaienArmedCommandSet" in block:
        raise RuntimeError("RS24 once still uses Iraq ICBM CommandSet")
    if "Weapon_Factory_RS24YarsOnce" not in block:
        raise RuntimeError("RS24 once PRIMARY not set")
    if "RS24_Yars_ICBM_1x_Warhead" in block:
        raise RuntimeError("RS24 once still points at live reload weapon")
    return header + block


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("VALIDATE FAIL: " + msg)


def slots_of(cs_text: str, name: str) -> dict[int, str]:
    m = re.search(
        rf"^CommandSet {re.escape(name)}\s*\r?\n(.*?)(?=^CommandSet |\Z)",
        cs_text,
        re.M | re.S,
    )
    require(m is not None, f"missing CS {name}")
    return {int(a): b for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", m.group(1), re.M)}


def weapon_block(text: str, name: str) -> str | None:
    m = re.search(rf"^Weapon {re.escape(name)}\s*\r?\n.*?^End\s*$", text, re.M | re.S)
    return m.group(0) if m else None


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> list[str]:
    notes: list[str] = []
    require(K_NEW_RS24 in new, "new RS24 object file missing")
    require(K_NEW_KHOR in new and K_NEW_DF41 in new, "#712 L/N object files missing")
    require(orig[K_RS24] == new[K_RS24], "live RS-24_Yars.ini must stay identical")
    require(orig[K_KHOR] == new[K_KHOR], "live Khormshar.ini must stay identical")
    require(orig[K_DF41] == new[K_DF41], "live DF41.ini must stay identical")
    require(orig[K_NEW_KHOR] == new[K_NEW_KHOR], "#712 Khormshar once changed")
    require(orig[K_NEW_DF41] == new[K_NEW_DF41], "#712 DF41 once changed")
    require(orig[K_ABBAS] == new[K_ABBAS], "Iraq AbbasLauncher.ini changed")

    cs = dec(new[K_CS])
    cb = dec(new[K_CB])
    w = dec(new[K_WPN])
    require("CommandButton CB_FACTORY_SLOT_K" in cb, "lost #712 K button")
    require("Object        = Iraq_Alhussaien" in cb, "K button object wrong")
    require("CommandButton CB_FACTORY_SLOT_L" in cb, "lost #712 L button")
    require("Object        = Factory_KhormsharOnce" in cb, "L button object wrong")
    require("CommandButton CB_FACTORY_SLOT_M" in cb, "M button missing")
    require("Object        = Factory_RS24YarsOnce" in cb, "M button object wrong")
    require("ButtonImage   = rus_rs24" in cb, "M button image not live rus_rs24")
    require("CommandButton CB_FACTORY_SLOT_N" in cb, "lost #712 N button")
    require("Object        = Factory_DF41Once" in cb, "N button object wrong")
    require("CommandSet FactoryOnceFireCommandSet" in cs, "once fire CS missing")
    require("CommandSet IranKhorramshahrFireCommandSet" in cs, "lost #710 Khormshar fire CS")
    require("CommandSet IranShahed136FireCommandSet" in cs, "lost #710 Shahed fire CS")
    require("Weapon Weapon_Factory_KhormsharOnce" in w, "lost #712 L weapon")
    require("Weapon Weapon_Factory_DF41Once" in w, "lost #712 N weapon")
    require("Weapon Weapon_Factory_RS24YarsOnce" in w, "RS24 once weapon missing")
    require("ProjectileObject            = RS24_Yars_Object" in w, "RS24 projectile lost")
    rs_w = weapon_block(w, "Weapon_Factory_RS24YarsOnce")
    require(rs_w is not None, "RS24 once weapon block missing")
    require("AutoReloadsClip             = No" in rs_w, "RS24 once not one-clip")
    require("ClipSize                    = 1" in rs_w, "RS24 once ClipSize")
    require("FireOCL                     = OCL_HussienMissileDisarm" in rs_w, "RS24 FireOCL")

    for name in (
        "Khormshar1_ICBM",
        "ICBM_DF41_1x_300kt_Warhead",
        "RS24_Yars_ICBM_1x_Warhead",
        "RS24_Yars_ICBM_4x_Warhead",
        "Weapon_Factory_KhormsharOnce",
        "Weapon_Factory_DF41Once",
    ):
        o = weapon_block(dec(orig[K_WPN]), name)
        require(o is not None and o in w, f"{name} changed")

    rs = dec(new[K_NEW_RS24])
    require(re.search(r"^Object Factory_RS24YarsOnce\b", rs, re.M), "RS24 once object name")
    require(not re.search(r"^Object RussiaVehicleRS24\b", rs, re.M), "copy still named RussiaVehicleRS24")
    require("BuildCost       = 27000" in rs, "RS24 once price")
    require("Weapon_Factory_RS24YarsOnce" in rs, "RS24 once PRIMARY")
    require("FactoryOnceFireCommandSet" in rs, "RS24 once fire CS")
    require(
        not re.search(r"Object\s*=\s*RussiaWarFactory\b", rs),
        "RS24 once still gated",
    )
    require("ShowSubObject     = MISSILE01" in rs, "RS24 once missile hidden")
    require("WeaponLaunchBone  = PRIMARY   WeaponA" in rs, "live PRIMARY bone lost")

    # A-J / K / L / N unchanged; only slot 13 rewritten
    old_ru = slots_of(dec(orig[K_CS]), "Russia_MissileFactoryCommandSet")
    new_ru = slots_of(cs, "Russia_MissileFactoryCommandSet")
    for i in range(1, 11):
        require(old_ru[i] == new_ru[i], f"Russia slot {i} changed")
    require(new_ru[11] == "CB_FACTORY_SLOT_K", "Russia K")
    require(new_ru[12] == "CB_FACTORY_SLOT_L", "Russia L")
    require(new_ru[13] == "CB_FACTORY_SLOT_M", "Russia M")
    require(new_ru[14] == "CB_FACTORY_SLOT_N", "Russia N")
    require(old_ru[13] == "Command_SetRallyPoint", "source Russia M was not Rally")

    old_iq = slots_of(dec(orig[K_CS]), IRAQ_FACTORY_SET)
    new_iq = slots_of(cs, IRAQ_FACTORY_SET)
    for i in range(1, 11):
        require(old_iq[i] == new_iq[i], f"Iraq slot {i} A-J changed")
    require(new_iq[11] == "CB_MISSILE_K", "Iraq K must stay CB_MISSILE_K")
    require(new_iq[12] == "CB_FACTORY_SLOT_L", "Iraq L")
    require(new_iq[13] == "CB_FACTORY_SLOT_M", "Iraq M")
    require(new_iq[14] == "CB_FACTORY_SLOT_N", "Iraq N")
    require(old_iq[13] == "CB_MISSILE_M", "source Iraq M was not CB_MISSILE_M")

    old_bldg = slots_of(dec(orig[K_CS]), IRAQ_BUILDING_SET)
    new_bldg = slots_of(cs, IRAQ_BUILDING_SET)
    require(old_bldg == new_bldg, "Iraq factory-building CS changed")

    for name in FACTORY_SETS:
        sl = slots_of(cs, name)
        for i in range(1, 11):
            require(not sl[i].startswith("CB_MISSILE_"), f"{name} slot {i} got Iraq button")
        require(sl[11] == "CB_FACTORY_SLOT_K", f"{name} K")
        require(sl[12] == "CB_FACTORY_SLOT_L", f"{name} L")
        require(sl[13] == "CB_FACTORY_SLOT_M", f"{name} M")
        require(sl[14] == "CB_FACTORY_SLOT_N", f"{name} N")
        require("CB_MISSILE_A" not in sl.values(), f"{name} imported Iraq A")
        require("CB_MISSILE_M" not in sl.values(), f"{name} imported Iraq M")

    # No invented RS_24Yars Object; Egypt / Arabic Alliance have no factory CS
    require("Object RS_24Yars" not in rs, "invented Object RS_24Yars")
    require("CommandSet Egypt_MissileFactoryCommandSet" not in cs, "invented Egypt factory")
    require(
        "CommandSet ArabicAlliance_MissileFactoryCommandSet" not in cs,
        "invented Arabic Alliance factory",
    )

    al = extract_object(dec(new[K_ABBAS]), IRAQ_K_OBJECT)
    require(re.search(rf"BuildCost\s*=\s*{IRAQ_K_COST}\b", al) is not None, "Iraq K cost changed")

    live = extract_object(dec(new[K_RS24]), "RussiaVehicleRS24")
    require(re.search(r"BuildCost\s*=\s*3500\b", live) is not None, "live RS24 cost changed")
    require("RussiaWarFactory" in live, "live RS24 prereq lost")

    notes.append(f"factory_sets={len(FACTORY_SETS)+1}")
    notes.append("live_rs24yars=RussiaVehicleRS24")
    notes.append("factory_copy=Factory_RS24YarsOnce")
    notes.append("slot_m=13")
    notes.append("iraq_A_J_preserved=yes")
    notes.append("egypt_arabic_no_factory=yes")
    return notes


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    src_sha = hashlib.sha256(SRC_BIG.read_bytes()).hexdigest()
    if src_sha != SRC_SHA:
        raise SystemExit(f"source BIG sha mismatch: {src_sha}")
    orig = read_big(SRC_BIG)
    new = dict(orig)
    new[K_CS] = enc(patch_commandset(dec(orig[K_CS])))
    new[K_CB] = enc(patch_commandbutton(dec(orig[K_CB])))
    new[K_WPN] = enc(patch_weapon_ini(dec(orig[K_WPN])))
    new[K_NEW_RS24] = enc(make_rs24_once(dec(orig[K_RS24])))
    notes = validate(orig, new)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    blob = build_big(new)
    OUT_BIG.write_bytes(blob)
    digest = hashlib.sha256(blob).hexdigest()
    OUT_SHA.write_text(digest + "\n", encoding="ascii")
    OUT_CS.write_bytes(new[K_CS])
    OUT_CS_SHA.write_text(hashlib.sha256(new[K_CS]).hexdigest() + "\n", encoding="ascii")
    print("wrote", OUT_BIG, "bytes", len(blob), "sha256", digest, "entries", len(new))
    print("wrote", OUT_CS, "bytes", len(new[K_CS]), "sha256", hashlib.sha256(new[K_CS]).hexdigest())
    for n in notes:
        print(" ", n)


if __name__ == "__main__":
    main()
