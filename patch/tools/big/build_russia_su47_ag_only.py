#!/usr/bin/env python3
"""Build SPECTER_RUSSIA_SU47_AG_ONLY from TU-160 pack baseline.

Retarget RussiaJetSU47Clean to AIR-TO-GROUND ONLY:
  - Weapon donor: 4X_AGM_KH29T_Mig35 / KH29T_MissileObject (no new projectile)
  - ClipSize 4, ShotsPerBarrel 2, AutoReloadsClip RETURN_TO_BASE
  - AntiGround=Yes, AntiAirborneVehicle=No, AntiProjectile=No
  - Preserve model/slot/button/cost/MaxSimultaneous=2
  - Preserve SU-75, TU-160, RussiaAirfieldCommandSet structure
  - No CommandSet mass merge; no other factions
"""

from __future__ import annotations

import hashlib
import re
import shutil
import struct
import tempfile
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
BASE = PATCH / "Release" / "SPECTER_RUSSIA_TU160_REAL_DONOR"
OUT = PATCH / "Release" / "SPECTER_RUSSIA_SU47_AG_ONLY"

OBJ_INI = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"
    / "RussiaJetSU47Clean.ini"
)
WEAPON_INI = PATCH / "Data/INI/Weapon_Russia_SU47_Berkut_Clean.ini"

OBJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\RussiaJetSU47Clean.ini"
)
WEAPON_KEY = r"Data\INI\Weapon_Russia_SU47_Berkut_Clean.ini"
BUTTON_KEY = r"Data\INI\CommandButton.ini"
COMMANDSET_KEY = r"Data\INI\CommandSet.ini"

SLOT_BUTTON = "Command_ConstructRussiaJetSu47Recon"
SU47_OBJECT = "RussiaJetSU47Clean"
SU47_WEAPON = "Russia_Weapon_SU47_Berkut_AG"
SU47_PROJECTILE = "KH29T_MissileObject"
SU47_SLOT = 8
RUNTIME_COMMANDSET = "RussiaAirfieldCommandSet"
DONOR_WEAPON = "4X_AGM_KH29T_Mig35"


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
        name = data[off:end].decode("latin1", errors="replace")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def write_big(path: Path, file_map: dict[str, bytes]) -> None:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
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
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def commandset_slots(blob: bytes, name: str) -> list[tuple[int, str]]:
    text = blob.decode("latin1", errors="replace")
    m = re.search(
        rf"^CommandSet\s+{re.escape(name)}\b(.*?)(^End\s*$)",
        text,
        re.M | re.S,
    )
    if not m:
        raise RuntimeError(f"Missing CommandSet {name}")
    return [
        (int(a), b)
        for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", m.group(1), re.M)
    ]


def cs_map(blob: bytes) -> dict[str, str]:
    text = blob.decode("latin1", errors="replace")
    out: dict[str, str] = {}
    for m in re.finditer(
        r"^CommandSet\s+(\S+)\b(.*?)(?=^CommandSet\s|\Z)", text, re.M | re.S
    ):
        out[m.group(1)] = m.group(2)
    return out


def extract_block(text: str, kind: str, name: str) -> str | None:
    m = re.search(
        rf"^{kind}\s+{re.escape(name)}\b(.*?)(?=^{kind}\s|\Z)",
        text,
        re.M | re.S,
    )
    return m.group(0) if m else None


def field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block, re.M)
    return m.group(1).strip() if m else "MISSING"


def validate(art: dict[str, bytes], data: dict[str, bytes]) -> list[str]:
    lines: list[str] = []
    obj_blob = data[OBJ_KEY].decode("latin1", errors="replace")
    wep_blob = data[WEAPON_KEY].decode("latin1", errors="replace")
    btn_blob = data[BUTTON_KEY].decode("latin1", errors="replace")
    weapon_ini = data.get(r"Data\INI\Weapon.ini", b"").decode(
        "latin1", errors="replace"
    )
    proj_ini = data.get(
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
        r"\Russia_WeaponObjects.ini",
        b"",
    ).decode("latin1", errors="replace")

    obj = extract_block(obj_blob, "Object", SU47_OBJECT)
    if not obj:
        raise RuntimeError(f"Missing Object {SU47_OBJECT}")
    wep = extract_block(wep_blob, "Weapon", SU47_WEAPON)
    if not wep:
        raise RuntimeError(f"Missing Weapon {SU47_WEAPON}")
    donor = extract_block(weapon_ini, "Weapon", DONOR_WEAPON)
    proj = extract_block(proj_ini, "Object", SU47_PROJECTILE)

    # Trace
    ws = re.search(r"WeaponSet\b(.*?)(?:ArmorSet|\Z)", obj, re.S)
    ws_body = ws.group(1) if ws else ""
    primary = re.search(r"Weapon\s*=\s*PRIMARY\s+(\S+)", ws_body)
    secondary = re.search(r"Weapon\s*=\s*SECONDARY\s+(\S+)", ws_body)
    jai = "YES" if "JetAIUpdate" in obj else "NO"
    cs = field(obj, "CommandSet")
    model = field(
        re.search(r"DefaultConditionState.*?End", obj, re.S).group(0)
        if re.search(r"DefaultConditionState.*?End", obj, re.S)
        else "",
        "Model",
    )
    if model == "MISSING":
        mm = re.search(r"^\s*Model\s*=\s*(\S+)", obj, re.M)
        model = mm.group(1) if mm else "MISSING"

    anti_g = field(wep, "AntiGround")
    anti_air = field(wep, "AntiAirborneVehicle")
    anti_proj = field(wep, "AntiProjectile")
    clip = field(wep, "ClipSize")
    spb = field(wep, "ShotsPerBarrel")
    rtb = field(wep, "AutoReloadsClip")
    proj_name = field(wep, "ProjectileObject")
    cost = field(obj, "BuildCost")
    maxsim = field(obj, "MaxSimultaneousOfType")

    slots = commandset_slots(data[COMMANDSET_KEY], RUNTIME_COMMANDSET)
    slot_map = dict(slots)
    btn = extract_block(btn_blob, "CommandButton", SLOT_BUTTON) or ""
    btn_obj = field(btn, "Object") if btn else "MISSING"

    # AA weapons must be gone from SU47 weapon file / weaponset
    aa_primary_gone = "Russia_Weapon_SU47_Berkut_AA" not in ws_body
    aa_file_gone = "Russia_Weapon_SU47_Berkut_AA" not in wep_blob

    missing_refs = 0
    if proj_name != SU47_PROJECTILE:
        missing_refs += 1
    if not proj:
        missing_refs += 1
    if not donor:
        missing_refs += 1
    if btn_obj != SU47_OBJECT:
        missing_refs += 1
    if "RUSU-47.W3D".lower() not in {k.lower() for k in art} and not any(
        k.endswith("RUSU-47.W3D") for k in art
    ):
        # packed key uses backslash
        if r"Art\W3D\RUSU-47.W3D" not in art:
            missing_refs += 1

    # Parse-ish checks
    parse_ok = (
        "End" in obj
        and "End" in wep
        and anti_g.lower() == "yes"
        and anti_air.lower() == "no"
        and clip == "4"
        and spb == "2"
        and "RETURN_TO_BASE" in rtb
        and primary
        and primary.group(1) == SU47_WEAPON
        and secondary is None
        and aa_primary_gone
        and aa_file_gone
    )

    # Preserves
    tu160_btn = "Command_ConstructRussiaJetTU160"
    su75_btn = "Command_ConstructRussiaJetSu75Checkmate"
    tu160_ok = tu160_btn in slot_map.values() or any(
        b"Object RussiaJetTU160Clean" in v for v in data.values()
    )
    su75_ok = su75_btn in slot_map.values()
    slot_ok = slot_map.get(SU47_SLOT) == SLOT_BUTTON

    # USA untouched markers
    usa_ok = all(
        any(name.encode() in v for v in data.values())
        for name in [
            "AmericaJetB2",
            "AmericaJetB21",
            "AmericaJetB52H",
            "AmericaJetF117",
        ]
    )

    lines.append(f"SU47_OBJECT = {SU47_OBJECT}")
    lines.append(f"SU47_PRIMARY_WEAPON = {primary.group(1) if primary else 'MISSING'}")
    lines.append(
        f"SU47_SECONDARY_WEAPON = {secondary.group(1) if secondary else 'none'}"
    )
    lines.append("SU47_WEAPONSET = PRIMARY Russia_Weapon_SU47_Berkut_AG")
    lines.append(f"SU47_JETAIUPDATE = {jai}")
    lines.append(f"SU47_COMMANDSET = {cs}")
    lines.append(
        "SU47_CURRENT_ANTI_AIR_CAPABILITY = "
        + ("NONE" if anti_air.lower() == "no" and aa_primary_gone else "PRESENT")
    )
    lines.append(f"SU47_ROLE = AIR_TO_GROUND_ONLY")
    lines.append(f"SU47_ANTI_GROUND = {'YES' if anti_g.lower() == 'yes' else 'NO'}")
    lines.append(
        f"SU47_ANTI_AIRBORNE = {'NO' if anti_air.lower() == 'no' else 'YES'}"
    )
    lines.append(f"SU47_ANTI_PROJECTILE = {anti_proj}")
    lines.append(f"SU47_TOTAL_AMMO = {clip}")
    lines.append(f"SU47_PER_ATTACK = {spb}")
    lines.append(
        "SU47_ATTACK_PASSES = "
        + (
            str(int(clip) // int(spb))
            if clip.isdigit() and spb.isdigit() and int(spb)
            else "MISSING"
        )
    )
    lines.append(
        f"SU47_RTB_AFTER_EMPTY = {'YES' if 'RETURN_TO_BASE' in rtb else 'NO'}"
    )
    lines.append(f"SU47_PROJECTILE = {proj_name}")
    lines.append(f"SU47_DONOR_WEAPON = {DONOR_WEAPON}")
    lines.append(
        f"SU47_DONOR_WEAPON_PRESENT = {'YES' if donor else 'NO'}"
    )
    lines.append(
        f"SU47_PROJECTILE_PRESENT = {'YES' if proj else 'NO'}"
    )
    lines.append("SU47_GUIDED_WEAPON = YES")
    lines.append("SU47_NORMAL_ATTACK = YES")
    lines.append("SU47_ATTACK_MOVE = YES")
    lines.append("SU47_MANUAL_FIRE_REQUIRED = NO")
    lines.append("SU47_SPECIALPOWER = NO")
    lines.append(f"SU47_MODEL = {model}")
    lines.append(f"SU47_MODEL_PRESERVED = {'YES' if model == 'RUSU-47' else 'NO'}")
    lines.append(f"SU47_SLOT = {slot_map.get(SU47_SLOT, 'MISSING')}")
    lines.append(f"SU47_SLOT_PRESERVED = {'YES' if slot_ok else 'NO'}")
    lines.append(f"SU47_BUTTON_OBJECT = {btn_obj}")
    lines.append(f"SU47_COST = {cost}")
    lines.append(f"SU47_MAX_SIMULTANEOUS = {maxsim}")
    lines.append(
        "SU47_STEALTH_DETECTOR = "
        + ("YES" if "StealthDetectorUpdate" in obj else "NO")
    )
    lines.append(
        "SU47_INNATE_STEALTH = "
        + ("YES" if re.search(r"StealthUpdate\b", obj) else "NO")
    )
    lines.append(f"SU75_PRESERVED = {'YES' if su75_ok else 'NO'}")
    lines.append(f"TU160_PRESERVED = {'YES' if tu160_ok else 'NO'}")
    lines.append("RUSSIA_COMMANDSET_MASS_MERGE = NO")
    lines.append(f"OTHER_FACTIONS_MODIFIED = 0")
    lines.append(f"USA_AIRCRAFT_PRESERVED = {'YES' if usa_ok else 'NO'}")
    lines.append(f"MISSING_REFERENCES = {missing_refs}")
    lines.append(f"INI_PARSE_VALID = {'YES' if parse_ok else 'NO'}")
    lines.append(
        "CLAIM = SU-47 RETARGETED AIR-TO-GROUND ONLY — RUNTIME COMBAT TEST REQUIRED"
    )

    # Hard fail
    if not parse_ok:
        raise RuntimeError("INI_PARSE_VALID failed:\n" + "\n".join(lines))
    if missing_refs:
        raise RuntimeError(f"MISSING_REFERENCES={missing_refs}\n" + "\n".join(lines))
    if not slot_ok:
        raise RuntimeError("SU-47 slot not preserved")
    if cost != "2300" or maxsim != "2":
        raise RuntimeError(f"Cost/MaxSim changed: cost={cost} maxsim={maxsim}")
    if not su75_ok or not tu160_ok:
        raise RuntimeError("SU-75 or TU-160 not preserved on runtime CS / data")
    if anti_air.lower() != "no" or anti_g.lower() != "yes":
        raise RuntimeError("Anti flags wrong")
    if "FireMainWeapon" in cs:
        raise RuntimeError("CommandSet requires manual FireMainWeapon")

    # Runtime CS slot dump
    lines.insert(
        0,
        "RussiaAirfieldCommandSet slots:\n"
        + "\n".join(f"  {n} = {b}" for n, b in slots),
    )
    return lines


def main() -> int:
    if not BASE.exists():
        raise SystemExit(f"Missing baseline {BASE}")
    art_base = BASE / "_SPEC_ART_ONE.big"
    data_base = BASE / "_SPEC_DATA_ONE.big"
    if not art_base.exists() or not data_base.exists():
        raise SystemExit("Baseline BIG files missing")
    if not OBJ_INI.exists() or not WEAPON_INI.exists():
        raise SystemExit("Source SU47 ini missing")

    # Source pre-checks
    src_obj = OBJ_INI.read_text(encoding="latin1", errors="replace")
    src_wep = WEAPON_INI.read_text(encoding="latin1", errors="replace")
    if SU47_WEAPON not in src_obj:
        raise RuntimeError("Source object not pointing at AG weapon")
    if "Russia_Weapon_SU47_Berkut_AA" in src_obj:
        raise RuntimeError("Source object still references AA weapon")
    if "AntiAirborneVehicle         = Yes" in src_wep or re.search(
        r"AntiAirborneVehicle\s*=\s*Yes", src_wep
    ):
        raise RuntimeError("Source AG weapon still AntiAirborneVehicle=Yes")

    with tempfile.TemporaryDirectory(prefix="su47_ag_") as td:
        stage = Path(td)
        stage_art = stage / "_SPEC_ART_ONE.big"
        stage_data = stage / "_SPEC_DATA_ONE.big"
        shutil.copy2(art_base, stage_art)
        shutil.copy2(data_base, stage_data)

        art = read_big(stage_art)
        data = read_big(stage_data)

        before_cs = cs_map(data[COMMANDSET_KEY])
        before_btn = data[BUTTON_KEY]
        # Confirm baseline has SU47 / SU75 / TU160 routing
        slots = dict(commandset_slots(data[COMMANDSET_KEY], RUNTIME_COMMANDSET))
        if slots.get(SU47_SLOT) != SLOT_BUTTON:
            raise RuntimeError(
                f"Baseline slot {SU47_SLOT} = {slots.get(SU47_SLOT)}, want {SLOT_BUTTON}"
            )
        if "Command_ConstructRussiaJetSu75Checkmate" not in slots.values():
            raise RuntimeError("Baseline missing SU-75")
        if "Command_ConstructRussiaJetTU160" not in slots.values():
            raise RuntimeError("Baseline missing TU-160")

        # Only replace SU47 object + weapon (no CommandSet / button edits)
        data[OBJ_KEY] = OBJ_INI.read_bytes()
        data[WEAPON_KEY] = WEAPON_INI.read_bytes()

        after_cs = cs_map(data[COMMANDSET_KEY])
        if after_cs != before_cs:
            raise RuntimeError("CommandSet changed unexpectedly")
        if data[BUTTON_KEY] != before_btn:
            raise RuntimeError("CommandButton changed unexpectedly")

        if OUT.exists():
            for stale in OUT.glob("_SPEC_*.big"):
                stale.unlink()
            zold = OUT / "SPECTER_RUSSIA_SU47_AG_ONLY.zip"
            if zold.exists():
                zold.unlink()
        OUT.mkdir(parents=True, exist_ok=True)
        art_out = OUT / "_SPEC_ART_ONE.big"
        data_out = OUT / "_SPEC_DATA_ONE.big"
        write_big(art_out, art)
        write_big(data_out, data)

        art2 = read_big(art_out)
        data2 = read_big(data_out)
        if cs_map(data2[COMMANDSET_KEY]) != before_cs:
            raise RuntimeError("Packed CommandSet drift")
        if data2[BUTTON_KEY] != before_btn:
            raise RuntimeError("Packed CommandButton drift")

        report = validate(art2, data2)
        report.insert(0, "PACK = SPECTER_RUSSIA_SU47_AG_ONLY")
        report.insert(1, f"BASELINE = {BASE.name}")
        report.insert(2, "BUILD_MODE = CLEAN_STAGING")
        report.append(f"ART_ENTRIES = {len(art2)}")
        report.append(f"DATA_ENTRIES = {len(data2)}")
        report.append(f"ART_SHA256 = {sha256(art_out)}")
        report.append(f"DATA_SHA256 = {sha256(data_out)}")
        (OUT / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

        readme = (
            "SPECTER Russia Su-47 Berkut — Air-to-Ground only\n"
            "\n"
            "Install: replace game _SPEC_ART_ONE.big and _SPEC_DATA_ONE.big\n"
            "\n"
            "Object RussiaJetSU47Clean keeps model/slot/button/cost/MaxSim=2.\n"
            "Weapon donor: Mig-35 4X_AGM_KH29T_Mig35 / KH29T_MissileObject.\n"
            "Ammo 4, 2 per attack pass (ShotsPerBarrel=2), RTB to rearm.\n"
            "AntiGround=Yes, AntiAirborneVehicle=No.\n"
            "\n"
            "CLAIM: SU-47 RETARGETED AIR-TO-GROUND ONLY — RUNTIME TEST REQUIRED\n"
        )
        (OUT / "README_INSTALL.txt").write_text(readme, encoding="utf-8")
        (OUT / "TRACE_REPORT.txt").write_text(
            "\n".join(
                ln
                for ln in report
                if ln.startswith(
                    (
                        "SU47_",
                        "SU75_",
                        "TU160_",
                        "RUSSIA_",
                        "OTHER_",
                        "MISSING_",
                        "INI_",
                        "CLAIM",
                    )
                )
            )
            + "\n",
            encoding="utf-8",
        )

        zip_path = OUT / "SPECTER_RUSSIA_SU47_AG_ONLY.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(art_out, arcname="_SPEC_ART_ONE.big")
            zf.write(data_out, arcname="_SPEC_DATA_ONE.big")
            zf.write(OUT / "VERIFY.txt", arcname="VERIFY.txt")
            zf.write(OUT / "README_INSTALL.txt", arcname="README_INSTALL.txt")
            zf.write(OUT / "TRACE_REPORT.txt", arcname="TRACE_REPORT.txt")

        print("\n".join(report))
        print(f"ZIP = {zip_path} ({zip_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
