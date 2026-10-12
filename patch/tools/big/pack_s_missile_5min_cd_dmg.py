#!/usr/bin/env python3
"""Global 5-minute missile re-fire cooldown + verified-kg warhead damage scale.

Baseline: PR #628 SPECTER_VIETNAM_MISSILE_FIRE_FIX.

GOAL 1 — native post-shot cooldown
  SAGE FIRE_WEAPON is gray while the clip is empty. With ClipSize=1,
  AutoReloadsClip=Yes, ClipReloadTime=300000 (milliseconds) the Fire action
  becomes available again 300 seconds after the shot. That is the engine
  reload, not a production queue, rebuild, or fake disabled button.

GOAL 2 — warhead mass vs 9P117 400 kg
  Mother actual impact damage is SRBM_ALHIJARAH_HE PrimaryDamage 2000
  ARMOR_PIERCING (plus SecondaryDamage 100 splash). Projectile
  FireWeaponWhenDead HE_9M729_450kg is DamageType=HACK radius 20 and is
  NOT folded into the AP total (would double-count if treated as the same
  explosion). Formula: PrimaryDamage = 2000 * (kg/400),
  SecondaryDamage = 100 * (kg/400). Mother 2000/100 is frozen.
  Death HACK extras already follow 2200*(kg/400) and stay as-is.

Not changed (shared or unverified):
  122mm Grad weapons (Iraq_BM-21 shares Iran BM21 / Israel PULS / AirF Tomahawk).
  Vanilla SCUDLauncherGun* (Stealth GLA Scud).
  Units with no documented warhead kg (Shaheen, TLAM, DF-21, Fateh, Iskander,
  Sarab7, Najm, Haitham/Alhussaien launch dummies).
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_VIETNAM_MISSILE_FIRE_FIX/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_VIETNAM_MISSILE_FIRE_FIX/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_MISSILE_5MIN_CD_DMG"
LOOSE_VN = ROOT / "patch/Data/INI/Weapon/Weapon_Vietnam_Missiles.ini"
LOOSE_AF = ROOT / "patch/Data/INI/Weapon/Weapon_Iraq_AlFahd500.ini"

SHA_DATA_628 = "06bdaafb04b3001af2b3cf8beead296c2132dc1326c0305a5e78e3c9dd8dd316"
SIZE_DATA_628 = 366815742
SHA_ART_628 = "3030c68abc11b801121feeac44a21af4407ffa9be385fba0f979d01fd7e4ab44"
SIZE_ART_628 = 1343628546

WEAPON_KEY = r"Data\INI\Weapon.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
SAT_VN = r"Data\INI\Weapon\Weapon_Vietnam_Missiles.ini"
SAT_AF = r"Data\INI\Weapon\Weapon_Iraq_AlFahd500.ini"
SAT_HN = r"Data\INI\Weapon\Weapon_Iraq_AlHaithamNajm.ini"

RELOAD_MS = "300000"

# ClipSize=1 + 300s + auto-reload. ClipSize forced to 1 where the live clip was 2
# so the next Fire action cannot fire a second round before the 300s clock.
COOLDOWN = [
    # Iraq factory A-J + mother G + Vietnam A-H
    "Weapon_Iraq_AlFahd500",
    "Weapon_Iraq_AlHusseinII",
    "Weapon_Iraq_AlSamoudII",
    "Weapon_Iraq_AlAbbas",
    "Weapon_Iraq_AlBasrah",
    "Weapon_Iraq_AlNasir",
    "Weapon_Iraq_AlMansour",
    "SRBM_ALHIJARAH_HE",
    "Weapon_Vietnam_VCM01",
    "Weapon_Vietnam_VCM02",
    "Weapon_Vietnam_SongHong",
    "Weapon_Vietnam_HongHa",
    "Weapon_Vietnam_CuuLong",
    "Weapon_Vietnam_TruongSon",
    "Weapon_Vietnam_BachDang",
    "Weapon_Vietnam_ThangLong",
    # Iraq factory E/F/K/L launch weapons
    "2x_MRPGM_Raad2",
    "Weapon_Iraq_AlNajm",
    "AlAbidMissileWeapon",
    "HussieanMissileWeapon",
    "Weapon_Iraq_AlHaitham_AlAbid",
    "Weapon_Iraq_AlHaitham_Hussiean",
    # other produceable SPECTER TELs (exclusive or missile-only shared)
    "2x_BGM109E_GL_TLAM_Block_IV",
    "9K720M_ST_Missile_Arb",
    "2x_9K723K1_SRBM_GPS",
    "2x_9M729_GLCM",
    "MRBM_DF21C",
    "2x_SRBM_Fateh313_HE",
    "1x_MRBM_Hwasong7_HE",
    "NK_Hwasong5_SRBM",
    "NK_Hwasong7_MRBM",
    "NK_Hwasong15_BunkerBuster",
    "India_Weapon_Shaheen",
    "Libya_Weapon_Shaheen",
    "Pakistan_Weapon_Shaheen",
    "Pakistan_Weapon_Ababeel",
    "SaudiArabia_Weapon_Shaheen",
    "SouthAfrica_Weapon_Shaheen",
    "Syria_Weapon_Shaheen",
    "UAE_Weapon_Shaheen",
]

FORCE_CLIP1 = {
    "2x_MRPGM_Raad2",
    "Weapon_Iraq_AlNajm",
    "2x_BGM109E_GL_TLAM_Block_IV",
    "2x_9K723K1_SRBM_GPS",
    "2x_9M729_GLCM",
    "2x_SRBM_Fateh313_HE",
}

# Verified kg from packed comments / prior accepted inventories. Mother frozen.
MOTHER_PD = "2000.0"
MOTHER_SD = "100.0"
DAMAGE = {
    "Weapon_Iraq_AlFahd500": {"PrimaryDamage": "8000.0", "SecondaryDamage": "400.0"},  # 1600 kg
    "Weapon_Iraq_AlHusseinII": {"SecondaryDamage": "200.0"},  # 800 kg, PD already 4000
    "Weapon_Iraq_AlSamoudII": {"SecondaryDamage": "150.0"},  # 600 kg, PD already 3000
    "Weapon_Iraq_AlAbbas": {"SecondaryDamage": "300.0"},  # 1200 kg, PD already 6000
    "Weapon_Iraq_AlBasrah": {"SecondaryDamage": "600.0"},  # 2400 kg, PD already 12000
    "Weapon_Iraq_AlNasir": {"SecondaryDamage": "800.0"},  # 3200 kg, PD already 16000
    "Weapon_Iraq_AlMansour": {"SecondaryDamage": "1000.0"},  # 4000 kg, PD already 20000
}

VERIFIED = [
    ("Iraq_R11ScudB", "SRBM_ALHIJARAH_HE", 400, "2000.0", "100.0", True),
    ("Iraq_AlFahd500", "Weapon_Iraq_AlFahd500", 1600, "8000.0", "400.0", False),
    ("Iraq_AlHusseinII", "Weapon_Iraq_AlHusseinII", 800, "4000.0", "200.0", False),
    ("Iraq_AlSamoudII", "Weapon_Iraq_AlSamoudII", 600, "3000.0", "150.0", False),
    ("Iraq_AlAbbas", "Weapon_Iraq_AlAbbas", 1200, "6000.0", "300.0", False),
    ("Iraq_AlBasrah", "Weapon_Iraq_AlBasrah", 2400, "12000.0", "600.0", False),
    ("Iraq_AlNasir", "Weapon_Iraq_AlNasir", 3200, "16000.0", "800.0", False),
    ("Iraq_AlMansour", "Weapon_Iraq_AlMansour", 4000, "20000.0", "1000.0", False),
    ("Vietnam_VCM01", "Weapon_Vietnam_VCM01", 1000, "5000.0", "250.0", False),
    ("Vietnam_VCM02", "Weapon_Vietnam_VCM02", 250, "1250.0", "62.5", False),
    ("Vietnam_SongHong", "Weapon_Vietnam_SongHong", 400, "2000.0", "100.0", False),
    ("Vietnam_HongHa", "Weapon_Vietnam_HongHa", 1800, "9000.0", "450.0", False),
    ("Vietnam_CuuLong", "Weapon_Vietnam_CuuLong", 350, "1750.0", "87.5", False),
    ("Vietnam_TruongSon", "Weapon_Vietnam_TruongSon", 600, "3000.0", "150.0", False),
    ("Vietnam_BachDang", "Weapon_Vietnam_BachDang", 500, "2500.0", "125.0", False),
    ("Vietnam_ThangLong", "Weapon_Vietnam_ThangLong", 1200, "6000.0", "300.0", False),
]

ALFAHD_WARHEAD = (
    "Weapon Weapon_Iraq_AlFahd500_Warhead\r\n"
    "  PrimaryDamage           = 8800\r\n"
    "  PrimaryDamageRadius     = 20.0\r\n"
    "  AttackRange             = 1\r\n"
    "  DamageType              = HACK\r\n"
    "  DeathType               = EXPLODED\r\n"
    "  WeaponSpeed             = 9999999999\r\n"
    "  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR\r\n"
    "  ClipSize                = 1\r\n"
    "  ProjectileCollidesWith  = STRUCTURES\r\n"
    "End"
)

FROZEN_OBJ = [
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini",
    (
        r"Data\INI\Object\Specter\Vietnam People's Armed Forces"
        r"\Buildings\Vietnam_MissileFactory.ini"
    ),
]


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big_ordered(data: bytes):
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files = {}
    order = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        key = name.replace("/", "\\")
        files[key] = data[off : off + size]
        order.append(key)
    return files, order


def parse_index(data: bytes):
    archive_size = struct.unpack(">I", data[4:8])[0]
    count = struct.unpack(">I", data[8:12])[0]
    header_size = struct.unpack(">I", data[12:16])[0]
    pos = 16
    files = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files.append((name, off, size))
    return archive_size, count, header_size, pos, files


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


def big_structure_ok(data: bytes) -> list[str]:
    fails = []
    archive_size, count, header_size, hdr_end, files = parse_index(data)
    if archive_size != len(data):
        fails.append(f"archive size {archive_size} != {len(data)}")
    if count != len(files):
        fails.append("count mismatch")
    if header_size != hdr_end:
        fails.append("header size mismatch")
    seen = set()
    for name, off, size in files:
        key = name.replace("/", "\\").lower()
        if key in seen:
            fails.append(f"dup {name}")
        seen.add(key)
        if off < header_size or off + size > len(data):
            fails.append(f"range {name}")
    return fails


def last_spans(text: str, kind: str, name: str):
    return list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text))


def last_block(text: str, kind: str, name: str) -> str:
    ms = last_spans(text, kind, name)
    return ms[-1].group(0) if ms else ""


def last_from_files(order, files, kind, name):
    found = ("", "")
    needle = f"{kind} {name}".encode("ascii")
    for key in order:
        if needle not in files[key]:
            continue
        block = last_block(files[key].decode("latin1"), kind, name)
        if block:
            found = (key, block)
    return found


def field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*([^;\r\n]+)", block or "", re.M)
    return m.group(1).strip() if m else ""


def replace_last(text: str, kind: str, name: str, new_block: str) -> str:
    ms = last_spans(text, kind, name)
    if not ms:
        raise SystemExit(f"missing {kind} {name}")
    m = ms[-1]
    return text[: m.start()] + new_block + text[m.end() :]


def set_field(block: str, key: str, value: str) -> str:
    pat = rf"(?m)^(\s*{re.escape(key)}\s*=\s*)[^;\r\n]+"
    if re.search(pat, block):
        return re.sub(pat, rf"\g<1>{value}", block, count=1)
    return re.sub(r"(?m)^End\s*$", f"  {key}                 = {value}\r\nEnd", block, count=1)


def apply_cooldown(block: str, name: str) -> str:
    block = set_field(block, "ClipReloadTime", RELOAD_MS)
    block = set_field(block, "AutoReloadsClip", "Yes")
    if name in FORCE_CLIP1 or field(block, "ClipSize") in {"1", "2"}:
        if name in FORCE_CLIP1 or field(block, "ClipSize") == "2":
            block = set_field(block, "ClipSize", "1")
    return block


def patch_text(text: str, names: set[str]) -> tuple[str, list[str]]:
    changed = []
    for name in names:
        block = last_block(text, "Weapon", name)
        if not block:
            continue
        new = apply_cooldown(block, name)
        if name in DAMAGE:
            for k, v in DAMAGE[name].items():
                new = set_field(new, k, v)
        if new != block:
            text = replace_last(text, "Weapon", name, new)
            changed.append(name)
    return text, changed


def ensure_in_weapon_ini(wini: str, source_text: str, name: str) -> str:
    src = last_block(source_text, "Weapon", name)
    if not src:
        return wini
    src = apply_cooldown(src, name)
    if name in DAMAGE:
        for k, v in DAMAGE[name].items():
            src = set_field(src, k, v)
    if last_block(wini, "Weapon", name):
        return replace_last(wini, "Weapon", name, src)
    return wini.rstrip("\r\n") + "\r\n\r\n" + src + "\r\n"


def validate(data: dict[str, bytes], src: dict[str, bytes], order: list[str]) -> list[str]:
    fails: list[str] = []
    for key in FROZEN_OBJ:
        if data.get(key) != src.get(key):
            fails.append(f"frozen mutated {key}")

    wini = data[WEAPON_KEY].decode("latin1")
    mother = last_block(wini, "Weapon", "SRBM_ALHIJARAH_HE")
    if field(mother, "PrimaryDamage") != MOTHER_PD:
        fails.append(f"mother PrimaryDamage {field(mother, 'PrimaryDamage')}")
    if field(mother, "SecondaryDamage") != MOTHER_SD:
        fails.append(f"mother SecondaryDamage {field(mother, 'SecondaryDamage')}")
    if field(mother, "AttackRange") != "1720.0":
        fails.append("mother range")
    if field(mother, "ClipReloadTime") != RELOAD_MS:
        fails.append("mother reload")

    death = last_from_files(order, data, "Weapon", "HE_9M729_450kg")[1]
    if field(death, "PrimaryDamage") != "2200" or field(death, "DamageType") != "HACK":
        fails.append("mother death HACK mutated")

    for name in COOLDOWN:
        key, block = last_from_files(order, data, "Weapon", name)
        if not block:
            fails.append(f"missing {name}")
            continue
        if field(block, "ClipReloadTime") != RELOAD_MS:
            fails.append(f"{name} ClipReloadTime={field(block, 'ClipReloadTime')}")
        if field(block, "AutoReloadsClip") != "Yes":
            fails.append(f"{name} AutoReloadsClip={field(block, 'AutoReloadsClip')}")
        if field(block, "ClipSize") != "1":
            fails.append(f"{name} ClipSize={field(block, 'ClipSize')}")
        wini_b = last_block(wini, "Weapon", name)
        if not wini_b:
            fails.append(f"Weapon.ini missing {name}")
        elif field(wini_b, "ClipReloadTime") != RELOAD_MS:
            fails.append(f"Weapon.ini {name} reload")

    for _obj, wname, kg, pd, sd, frozen in VERIFIED:
        block = last_block(wini, "Weapon", wname)
        if field(block, "PrimaryDamage") != pd:
            fails.append(f"{wname} PD {field(block, 'PrimaryDamage')} != {pd}")
        if field(block, "SecondaryDamage") != sd:
            fails.append(f"{wname} SD {field(block, 'SecondaryDamage')} != {sd}")
        expect = 2000.0 * (kg / 400.0)
        got = float(field(block, "PrimaryDamage"))
        if abs(got - expect) > 0.01:
            fails.append(f"{wname} PD scale {got} != {expect}")

    # Vietnam fire chain still live
    for obj, wname, _kg, _pd, _sd, _fr in VERIFIED:
        if not obj.startswith("Vietnam_"):
            continue
        _k, unit = last_from_files(order, data, "Object", obj)
        if field(unit, "CommandSet") != "Scud_B_CommandSet":
            fails.append(f"{obj} CommandSet")
        if f"Weapon = PRIMARY   {wname}" not in (unit or ""):
            fails.append(f"{obj} PRIMARY")

    _k, scud = last_from_files(order, data, "CommandSet", "Scud_B_CommandSet")
    if "Command_FireMainWeapon" not in scud:
        fails.append("Scud_B lost FireMainWeapon")
    _k, fire = last_from_files(order, data, "CommandButton", "Command_FireMainWeapon")
    if field(fire, "Command") != "FIRE_WEAPON" or field(fire, "WeaponSlot") != "PRIMARY":
        fails.append("FireMainWeapon")

    _k, fac = last_from_files(order, data, "CommandSet", "Vietnam_MissileFactoryCommandSet")
    if "CB_VIETNAM_MISSILE_A" not in fac or "CB_VIETNAM_MISSILE_H" not in fac:
        fails.append("Vietnam factory menu")
    _k, irq = last_from_files(order, data, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet")
    if "CB_MISSILE_A" not in irq or "CB_MISSILE_M" not in irq:
        fails.append("Iraq factory menu")

    # shared Grad / vanilla Scud guns untouched
    src_w = src[WEAPON_KEY].decode("latin1")
    for name in ("122mm_M21OF_Grad_Semi", "122mm_M21OF_Grad_Salvo", "SCUDLauncherGunExplosive"):
        if last_block(wini, "Weapon", name) != last_block(src_w, "Weapon", name):
            fails.append(f"shared {name} mutated")

    if b"ZZZZ" in b"".join(v for k, v in data.items() if "zzzz" in k.lower()):
        fails.append("ZZZZ")
    return fails


def write_docs(data_path: Path, art_path: Path, zip_path: Path, packed, order) -> str:
    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_sha = sha256_path(zip_path)
    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    wini = packed[WEAPON_KEY].decode("latin1")
    lines = [
        "STATIC INVENTORY + EFFECTIVE LAST-WINS",
        "Mother 9P117 / Iraq_R11ScudB / SRBM_ALHIJARAH_HE: 400 kg.",
        "Actual impact damage = PrimaryDamage 2000 ARMOR_PIERCING + splash SecondaryDamage 100.",
        "Death HE_9M729_450kg = 2200 HACK r=20 (not added into AP total).",
        "Formula: PD = 2000 * (kg/400); SD = 100 * (kg/400).",
        "Cooldown: ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000 ms after the shot.",
        "",
        "REPRESENTATIVE SCALE",
        "  200 kg -> PD 1000 / SD 50   (no current factory missile at exactly 200 kg; VCM-02 is 250 kg = 1250)",
        "  400 kg -> PD 2000 / SD 100  (mother, Sông Hồng)",
        "  800 kg -> PD 4000 / SD 200  (Al-Hussein II)",
        " 1200 kg -> PD 6000 / SD 300  (Al-Abbas, Thăng Long)",
        " 1600 kg -> PD 8000 / SD 400  (Al-Fahd 500; was 4000/100 in Weapon.ini)",
        "",
    ]
    for obj, wname, kg, pd, sd, frozen in VERIFIED:
        block = last_block(wini, "Weapon", wname)
        lines.append(
            f"{obj:22} {kg:5}kg {wname:28} PD={field(block,'PrimaryDamage'):8} "
            f"SD={field(block,'SecondaryDamage'):6} RL={field(block,'ClipReloadTime')} "
            f"{'MOTHER-FROZEN-DMG' if frozen else ''}"
        )
    lines += [
        "",
        "LIMITATIONS",
        "- Iraq_BM-21 uses shared 122mm Grad weapons also used by Iran BM21, Israel PULS,",
        "  AirF Tomahawk. Those weapons were not changed.",
        "- Vanilla SCUDLauncherGun* (Stealth GLA Scud) not changed.",
        "- Haitham / Alhussaien have two warhead slots; each clip is 300s independently.",
        "  Switching to the other slot can fire immediately (no shared-across-slots reload).",
        "- Missiles with no documented kg kept their existing PrimaryDamage.",
        "- ClipSize 2->1 on 2x_* launchers so the second round cannot bypass the 300s clock.",
        "- RUNTIME TEST: NOT RUN. Game was not launched.",
        "",
    ]
    (ext / "INVENTORY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ext / "Weapon.ini.Changed.txt").write_text(
        "\n\n".join(last_block(wini, "Weapon", n) for n in COOLDOWN if last_block(wini, "Weapon", n)),
        encoding="utf-8",
    )

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #628 s-vietnam-missile-fire-fix",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "ART_UNCHANGED=YES",
        "MOTHER_DAMAGE_FROZEN=YES",
        "VIETNAM_FIRE_CHAIN_PRESERVED=YES",
        "NO_REARM=YES",
        "NO_ZZZZ=YES",
        "",
        "COOLDOWN: ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000 on in-scope weapons.",
        "DAMAGE: Al-Fahd 1600kg 4000->8000; Iraq B-J splash scaled to 100*(kg/400);",
        "Vietnam A-H already matched the formula. Mother 2000/100 unchanged.",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n")
    hashes = "\n".join(
        [
            "DATA_CHANGED=YES",
            "ART_CHANGED=NO",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_SIZE={art_path.stat().st_size}",
            f"ART_SHA256={art_sha}",
            "ZIP_FILE=SPECTER_MISSILE_5MIN_CD_DMG.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #628",
            "STATIC_VALIDATION=PASS",
            "RUNTIME_TEST=NOT RUN",
            "",
        ]
    )
    (OUT / "HASHES.txt").write_text(hashes)
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-missile-5min-cd-dmg/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-missile-5min-cd-dmg/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-missile-5min-cd-dmg/SPECTER_MISSILE_5MIN_CD_DMG.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "TAG=s-missile-5min-cd-dmg",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-missile-5min-cd-dmg",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN — the game was not launched. No 5-minute in-game test.",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Global 5-minute missile re-fire cooldown and verified-kg damage scale.\n"
        "Native ClipReloadTime=300000 after the shot. Mother 400 kg damage frozen.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Global 5-minute missile cooldown + warhead damage scale\n\n"
        "- Native SAGE reload: `ClipSize=1`, `AutoReloadsClip=Yes`, `ClipReloadTime=300000` "
        "on produceable SPECTER missile weapons. Clock starts after the shot.\n"
        "- Damage formula vs 9P117 400 kg / PrimaryDamage 2000: "
        "`PD = 2000 * (kg/400)`, splash `SD = 100 * (kg/400)`.\n"
        "- Al-Fahd 1600 kg was 4000 in Weapon.ini; now 8000. Iraq B–J splash scaled. "
        "Vietnam A–H already matched. Mother 2000/100 not changed.\n"
        "- Death HACK extras are not added into the AP total (avoids double-count).\n"
        "- Shared Grad weapons and vanilla GLA Scud guns were not changed.\n"
        "- Static validation only. The game was not launched.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "Weapon.ini last-wins many missile ClipReloadTime values at 300000.\n"
        "Satellite Weapon_Vietnam_Missiles.ini / Weapon_Iraq_AlFahd500.ini / "
        "Weapon_Iraq_AlHaithamNajm.ini and country Weapon_*.ini match.\n"
        "CommandSet.ini, CommandButton.ini, factory objects, 9P117 object, ART unchanged.\n"
        "122mm Grad and SCUDLauncherGun* left frozen because they are shared.\n"
    )
    return hashes


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_628 or SRC_DATA.stat().st_size != SIZE_DATA_628:
        raise SystemExit("DATA baseline is not PR #628 SPECTER_VIETNAM_MISSILE_FIRE_FIX")
    if sha256_path(SRC_ART) != SHA_ART_628 or SRC_ART.stat().st_size != SIZE_ART_628:
        raise SystemExit("ART baseline is not PR #628")

    src_data, _ = parse_big_ordered(SRC_DATA.read_bytes())
    data = dict(src_data)
    names = set(COOLDOWN)

    # Patch every INI that already defines one of these weapons.
    for key, blob in list(data.items()):
        if not key.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1")
        if not any(f"Weapon {n}" in text for n in names):
            continue
        new, changed = patch_text(text, names)
        if changed:
            data[key] = new.encode("latin1")

    # Guarantee Weapon.ini last-wins for every cooldown weapon (load-path lesson from Al-Fahd / Vietnam).
    wini = data[WEAPON_KEY].decode("latin1")
    for name in COOLDOWN:
        source = ""
        for key, blob in data.items():
            if not key.lower().endswith(".ini"):
                continue
            blk = last_block(blob.decode("latin1"), "Weapon", name)
            if blk:
                source = blob.decode("latin1")
        if not source:
            raise SystemExit(f"no source block for {name}")
        wini = ensure_in_weapon_ini(wini, source, name)
    if not last_block(wini, "Weapon", "Weapon_Iraq_AlFahd500_Warhead"):
        wini = wini.rstrip("\r\n") + "\r\n\r\n" + ALFAHD_WARHEAD + "\r\n"
    data[WEAPON_KEY] = wini.encode("latin1")

    if LOOSE_VN.exists() and SAT_VN in data:
        LOOSE_VN.write_bytes(data[SAT_VN])
    if LOOSE_AF.exists() and SAT_AF in data:
        LOOSE_AF.write_bytes(data[SAT_AF])

    data_big = build_big(data)
    packed, order = parse_big_ordered(data_big)
    fails = validate(packed, src_data, order)
    fails.extend(f"DATA {x}" for x in big_structure_ok(data_big))
    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_big)
    shutil.copy2(SRC_ART, art_path)

    zip_path = ROOT / "patch/Release/SPECTER_MISSILE_5MIN_CD_DMG.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")

    hashes = write_docs(data_path, art_path, zip_path, packed, order)
    print("PACKED")
    print(hashes)


if __name__ == "__main__":
    main()
