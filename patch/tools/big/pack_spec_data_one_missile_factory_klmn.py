#!/usr/bin/env python3
"""Fill missile-factory slots K/L/N from live SPE DATA.

Source: PR #711 / iran-shahed-khormshar-fire _SPEC_DATA_ONE.big
(SHA 1cf73a202d68a9008dfc6bc2925d26b31da53f622ad5881e400f5ce74c3c7937).

Slot M (13 Varuaktori) is NOT in live DATA/CSF — not invented.

K = Iraq_Alhussaien (Iraq factory K, BuildCost 20000) reused as-is.
L = Factory_KhormsharOnce (copy of live IranVehicleKhormshar, cost 20000, one clip).
N = Factory_DF41Once (copy of live ChinaVehicleDF41, cost 30000, one clip, no China WF prereq).

CommandSet.ini is the ControlBar table (same bytes as PR #710 loose overlay).
Both the DATA copy and a new loose CommandSet.ini are written so LocalFileSystem
first-win still contains the four Iran fire sets plus factory K/L/N.
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


def patch_khormshar_vehicle(block: str) -> str:
    """Show MISSILE01 on a TEL copy; bind FireMainWeapon (PRIMARY) to that bone."""
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
        has_primary = bool(
            re.search(r"WeaponLaunchBone\s*=\s*PRIMARY\s+MISSILE01\b", joined, re.I)
        )
        result: list[str] = []
        for line in buf:
            if re.search(r"HideSubObject\s*=\s*MISSILE01\b", line, re.I):
                if is_rider1 or is_rubble:
                    result.append(line)
                else:
                    result.append(re.sub(r"HideSubObject", "ShowSubObject", line, count=1))
            elif re.search(r"WeaponLaunchBone\s*=\s*SECONDARY\s+MISSILE01\b", line, re.I):
                indent = line[: len(line) - len(line.lstrip())]
                if not has_primary:
                    result.append(f"{indent}WeaponLaunchBone  = PRIMARY   MISSILE01")
                    result.append(f"{indent}WeaponFireFXBone  = PRIMARY   WEAPONFX")
                    has_primary = True
                result.append(line)
            else:
                result.append(line)
        if not is_rider1 and not is_rubble:
            if not has_show and not any(
                re.search(r"ShowSubObject\s*=\s*MISSILE01\b", ln, re.I) for ln in result
            ):
                result.insert(-1, "      ShowSubObject     = MISSILE01")
            fire_state = (
                "DEFAULTCONDITIONSTATE" in flags
                or "DEPLOYED" in flags
                or "RIDER2" in flags
            )
            if fire_state and not has_primary:
                result.insert(-1, "      WeaponLaunchBone  = PRIMARY   MISSILE01")
                result.insert(-1, "      WeaponFireFXBone  = PRIMARY   WEAPONFX")
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

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/IRAN_SHAHED_KHORMSHAR_FIRE/_SPEC_DATA_ONE.big"
SRC_SHA = "1cf73a202d68a9008dfc6bc2925d26b31da53f622ad5881e400f5ce74c3c7937"
OUT_DIR = ROOT / "Release/MISSILE_FACTORY_KLMN"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
OUT_SHA = OUT_DIR / "_SPEC_DATA_ONE.big.sha256"
OUT_CS = OUT_DIR / "CommandSet.ini"
OUT_CS_SHA = OUT_DIR / "CommandSet.ini.sha256"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_KHOR = r"Data\INI\Object\Specter\Iranian Army\Wheeled\Khormshar.ini"
K_DF41 = r"Data\INI\Object\Specter\PLA\Wheeled\DF41.ini"
K_NEW_KHOR = r"Data\INI\Object\Specter\FactoryKLMN\Factory_KhormsharOnce.ini"
K_NEW_DF41 = r"Data\INI\Object\Specter\FactoryKLMN\Factory_DF41Once.ini"

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

NEW_BUTTONS = """
; Shared missile-factory K/L/N. Not Iraq A-M. Slot M (13 Varuaktori) not in live DATA.
CommandButton CB_FACTORY_SLOT_K
  Command       = UNIT_BUILD
  Object        = Iraq_Alhussaien
  TextLabel     = CONTROLBAR:SpecterMissileK
  ButtonImage   = specter_missile_k
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipSpecterMissileK
End

CommandButton CB_FACTORY_SLOT_L
  Command       = UNIT_BUILD
  Object        = Factory_KhormsharOnce
  TextLabel     = CONTROLBAR:ConstructIranVehicleKhormshar
  ButtonImage   = irn_khormshar
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipBuildIranVehicleKhormshar
End

CommandButton CB_FACTORY_SLOT_N
  Command       = UNIT_BUILD
  Object        = Factory_DF41Once
  TextLabel     = CONTROLBAR:ConstructChinaVehicleDF41
  ButtonImage   = pla_df41
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipChinaVehicleDF41
End
"""

NEW_CS_FIRE = """
CommandSet FactoryOnceFireCommandSet
  1  = Command_FireMainWeapon
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
"""

KHOR_WEAPON = """
; One-clip factory Khorramshahr. Does not last-win Khormshar1_ICBM.
Weapon Weapon_Factory_KhormsharOnce
  PrimaryDamage               = 1
  PrimaryDamageRadius         = 0
  AttackRange                 = 2000
  MinimumAttackRange          = 1000
  PreAttackDelay              = 3600
  PreAttackType               = PER_SHOT
  DamageType                  = FLAME
  FireFX                      = FX_IskanderFiringEffects
  FireOCL                     = OCL_HussienMissileDisarm
  ProjectileObject            = Khormshar1_Object
  ProjectileDetonationFX      = FX_HeavyWarheadCruiseMissileExplosion
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

DF41_WEAPON = """
; One-clip factory DF-41. Does not last-win ICBM_DF41_1x_300kt_Warhead.
Weapon Weapon_Factory_DF41Once
  PrimaryDamage               = 1
  PrimaryDamageRadius         = 0
  AttackRange                 = 2300
  MinimumAttackRange          = 500
  PreAttackDelay              = 3600
  PreAttackType               = PER_SHOT
  DamageType                  = FLAME
  FireFX                      = FX_IskanderFiringEffects
  FireOCL                     = OCL_HussienMissileDisarm
  ProjectileObject            = DF41_ICBM_Sgl_Object
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


def crlf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").strip("\r\n") + "\r\n"


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
    other_slots = {
        11: "CB_FACTORY_SLOT_K",
        12: "CB_FACTORY_SLOT_L",
        14: "CB_FACTORY_SLOT_N",
    }
    iraq_slots = {
        11: "CB_MISSILE_K",
        12: "CB_FACTORY_SLOT_L",
        14: "CB_FACTORY_SLOT_N",
    }

    def one(name: str, slots: dict[int, str]) -> None:
        nonlocal text
        m = re.search(
            rf"(^CommandSet {re.escape(name)}\s*{re.escape(nl)})(.*?)(?=^CommandSet |\Z)",
            text,
            re.M | re.S,
        )
        if not m:
            raise RuntimeError(f"CommandSet {name} missing from CommandSet.ini")
        new_body = upsert_slots(m.group(2), slots)
        text = text[: m.start()] + m.group(1) + new_body + text[m.end() :]

    for name in FACTORY_SETS:
        one(name, other_slots)
    one(IRAQ_FACTORY_SET, iraq_slots)
    if "CommandSet FactoryOnceFireCommandSet" not in text:
        if not text.endswith(nl):
            text += nl
        text += nl + crlf(NEW_CS_FIRE).replace("\r\n", nl)
    return text


def patch_commandbutton(text: str) -> str:
    nl = nl_of(text)
    if "CommandButton CB_FACTORY_SLOT_K" in text:
        raise RuntimeError("factory buttons already present")
    if not text.endswith(nl):
        text += nl
    return text + nl + crlf(NEW_BUTTONS).replace("\r\n", nl)


def patch_weapon_ini(text: str) -> str:
    nl = nl_of(text)
    if "Weapon Weapon_Factory_KhormsharOnce" in text:
        raise RuntimeError("factory weapons already present")
    if not text.endswith(nl):
        text += nl
    return (
        text
        + nl
        + crlf(KHOR_WEAPON).replace("\r\n", nl)
        + nl
        + crlf(DF41_WEAPON).replace("\r\n", nl)
    )


def make_khormshar_once(src: str) -> str:
    block = extract_object(src, "IranVehicleKhormshar")
    block = block.replace("Object IranVehicleKhormshar", "Object Factory_KhormsharOnce", 1)
    block = re.sub(r"BuildCost\s*=\s*\S+", "BuildCost       = 20000", block, count=1)
    block = block.replace("Khormshar1_ICBM", "Weapon_Factory_KhormsharOnce")
    if "BuildCost       = 20000" not in block:
        raise RuntimeError("Khormshar once cost not set")
    if "Weapon_Factory_KhormsharOnce" not in block:
        raise RuntimeError("Khormshar once weapon not set")
    if "IranKhorramshahrFireCommandSet" not in block:
        raise RuntimeError("Khormshar fire CommandSet lost")
    return block


def make_df41_once(src: str) -> str:
    block = extract_object(src, "ChinaVehicleDF41")
    block = block.replace("Object ChinaVehicleDF41", "Object Factory_DF41Once", 1)
    block = re.sub(r"BuildCost\s*=\s*\S+", "BuildCost       = 30000", block, count=1)
    block = re.sub(
        r"Prerequisites\s*\r?\n\s*Object\s*=\s*ChinaWarFactory\s*\r?\n\s*End",
        "Prerequisites\r\n  End",
        block,
        count=1,
    )
    block = block.replace(
        "CommandSet             = Iraq_AlhussaienArmedCommandSet",
        "CommandSet             = FactoryOnceFireCommandSet",
    )
    block = block.replace("ICBM_DF41_1x_300kt_Warhead", "Weapon_Factory_DF41Once")
    block = re.sub(
        r"Weapon\s+=\s+SECONDARY\s+DF41_ICBM_6x_Warhead_Missile",
        "Weapon            = SECONDARY  NONE",
        block,
    )
    block = patch_khormshar_vehicle(block)
    if "BuildCost       = 30000" not in block:
        raise RuntimeError("DF-41 once cost not set")
    if "ChinaWarFactory" in block:
        raise RuntimeError("DF-41 once still requires ChinaWarFactory")
    if "FactoryOnceFireCommandSet" not in block:
        raise RuntimeError("DF-41 once CommandSet not set")
    if "Iraq_AlhussaienArmedCommandSet" in block:
        raise RuntimeError("DF-41 once still uses Iraq ICBM CommandSet")
    return block


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


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> list[str]:
    notes: list[str] = []
    require(K_NEW_KHOR in new and K_NEW_DF41 in new, "new object files missing")
    require(orig[K_KHOR] == new[K_KHOR], "live Khormshar.ini must stay identical")
    require(orig[K_DF41] == new[K_DF41], "live DF41.ini must stay identical")

    cs = dec(new[K_CS])
    cb = dec(new[K_CB])
    w = dec(new[K_WPN])
    require("CommandButton CB_FACTORY_SLOT_K" in cb, "K button missing")
    require("Object        = Iraq_Alhussaien" in cb, "K button object wrong")
    require("CommandButton CB_FACTORY_SLOT_L" in cb, "L button missing")
    require("Object        = Factory_KhormsharOnce" in cb, "L button object wrong")
    require("CommandButton CB_FACTORY_SLOT_N" in cb, "N button missing")
    require("Object        = Factory_DF41Once" in cb, "N button object wrong")
    require("CB_FACTORY_SLOT_M" not in cb, "invented M button")
    require("CommandSet FactoryOnceFireCommandSet" in cs, "once fire CS missing")
    require("CommandSet IranKhorramshahrFireCommandSet" in cs, "lost #710 Khormshar fire CS")
    require("CommandSet IranShahed136FireCommandSet" in cs, "lost #710 Shahed fire CS")
    require("Weapon Weapon_Factory_KhormsharOnce" in w, "khormshar once weapon missing")
    require("Weapon Weapon_Factory_DF41Once" in w, "df41 once weapon missing")
    require("AutoReloadsClip             = No" in w, "one-shot AutoReloadsClip missing")
    # original weapons unchanged
    for name in ("Khormshar1_ICBM", "ICBM_DF41_1x_300kt_Warhead", "AlAbidMissileWeapon"):
        o = re.search(rf"^Weapon {name}\s*\r?\n(.*?)^End\s*$", dec(orig[K_WPN]), re.M | re.S)
        n = re.search(rf"^Weapon {name}\s*\r?\n(.*?)^End\s*$", w, re.M | re.S)
        require(o is not None and n is not None and o.group(0) == n.group(0), f"{name} changed")

    kh = dec(new[K_NEW_KHOR])
    require("Object Factory_KhormsharOnce" in kh, "khormshar once object name")
    require("BuildCost       = 20000" in kh, "khormshar once price")
    require("Weapon_Factory_KhormsharOnce" in kh, "khormshar once PRIMARY")
    require("IranKhorramshahrFireCommandSet" in kh, "khormshar once fire CS")

    df = dec(new[K_NEW_DF41])
    require("Object Factory_DF41Once" in df, "df41 once object name")
    require("BuildCost       = 30000" in df, "df41 once price")
    require("Weapon_Factory_DF41Once" in df, "df41 once PRIMARY")
    require("FactoryOnceFireCommandSet" in df, "df41 once fire CS")
    require("ChinaWarFactory" not in df, "df41 once still gated")
    require("ShowSubObject     = MISSILE01" in df, "df41 once missile hidden")

    # A-J unchanged for a sample country
    old_ru = slots_of(dec(orig[K_CS]), "Russia_MissileFactoryCommandSet")
    new_ru = slots_of(cs, "Russia_MissileFactoryCommandSet")
    for i in range(1, 11):
        require(old_ru[i] == new_ru[i], f"Russia slot {i} changed")
    require(new_ru[11] == "CB_FACTORY_SLOT_K", "Russia K")
    require(new_ru[12] == "CB_FACTORY_SLOT_L", "Russia L")
    require(new_ru[13] == old_ru[13], "Russia M/Rally changed without Varuaktori")
    require(new_ru[14] == "CB_FACTORY_SLOT_N", "Russia N")

    old_iq = slots_of(dec(orig[K_CS]), IRAQ_FACTORY_SET)
    new_iq = slots_of(cs, IRAQ_FACTORY_SET)
    for i in range(1, 11):
        require(old_iq[i] == new_iq[i], f"Iraq slot {i} A-J changed")
    require(new_iq[11] == "CB_MISSILE_K", "Iraq K must stay CB_MISSILE_K")
    require(new_iq[12] == "CB_FACTORY_SLOT_L", "Iraq L")
    require(new_iq[13] == old_iq[13], "Iraq M replaced without Varuaktori")
    require(new_iq[14] == "CB_FACTORY_SLOT_N", "Iraq N")
    # Iraq A-M buttons must not be copied onto other countries
    for name in FACTORY_SETS:
        sl = slots_of(cs, name)
        for i in range(1, 11):
            require(not sl[i].startswith("CB_MISSILE_"), f"{name} slot {i} got Iraq button")
        require(sl[11] == "CB_FACTORY_SLOT_K", f"{name} K")
        require(sl[12] == "CB_FACTORY_SLOT_L", f"{name} L")
        require(sl[14] == "CB_FACTORY_SLOT_N", f"{name} N")
        require("CB_MISSILE_A" not in sl.values(), f"{name} imported Iraq A")

    # Iraq Alhussaien cost still 20000
    abbas = dec(new[r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini"])
    al = extract_object(abbas, IRAQ_K_OBJECT)
    require(re.search(rf"BuildCost\s*=\s*{IRAQ_K_COST}\b", al) is not None, "Iraq K cost changed")

    notes.append(f"factory_sets={len(FACTORY_SETS)+1}")
    notes.append("varuaktori=NOT_IN_LIVE_DATA")
    notes.append("iraq_A_J_preserved=yes")
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
    new[K_NEW_KHOR] = enc(make_khormshar_once(dec(orig[K_KHOR])))
    new[K_NEW_DF41] = enc(make_df41_once(dec(orig[K_DF41])))
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
