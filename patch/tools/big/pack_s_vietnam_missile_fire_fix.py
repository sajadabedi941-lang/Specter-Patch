#!/usr/bin/env python3
"""Fix inactive Vietnam A-H fire buttons by loading weapons into Weapon.ini.

ROOT CAUSE (PR #627 / packed last-wins):
  Vietnam TELs A-H last-wins as:
    CommandSet = Scud_B_CommandSet
    WeaponSet PRIMARY = Weapon_Vietnam_*
  Scud_B_CommandSet slot 1 = Command_FireMainWeapon (FIRE_WEAPON / PRIMARY).

  That is the same fire path as working 9P117 (Iraq_R11ScudB) and Iraq_AlFahd500.
  Command_FireMainWeapon is inactive when PRIMARY does not resolve.

  Weapon_Iraq_AlFahd500 last-wins inside Data\\INI\\Weapon.ini (PR that made
  Al-Fahd fire). Weapon_Vietnam_* existed ONLY in
  Data\\INI\\Weapon\\Weapon_Vietnam_Missiles.ini — the same unloaded class of
  satellite that left Al-Fahd PRIMARY empty.

  The satellite also contains illegal floats SecondaryDamage = 62.5.0 (VCM-02)
  and 87.5.0 (Cửu Long), which abort SAGE INI parse if that file is read.

FIX:
  Sanitize those two floats to 62.5 / 87.5 (intended 5% secondary).
  Append the 16 Vietnam weapon/warhead blocks to Data\\INI\\Weapon.ini.
  Keep the satellite file with the same cleaned text.
  Do not touch CommandSet.ini, CommandButton.ini, factory objects, ART,
  9P117, Iraq A-M, names, colors, markings, range, damage, cost, or build time.
  No rearm. No ZZZZ. No dedicated fake Fire buttons.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_VIETNAM_FACTORY_MENU_FIX/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_VIETNAM_FACTORY_MENU_FIX/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_VIETNAM_MISSILE_FIRE_FIX"
LOOSE_WEP = ROOT / "patch/Data/INI/Weapon/Weapon_Vietnam_Missiles.ini"

SHA_DATA_627 = "7667eeff006b9afc7a46e3f710e4797d8052d98fd12787f9d7e3c1983ab85ebd"
SIZE_DATA_627 = 366803309
SHA_ART_627 = "3030c68abc11b801121feeac44a21af4407ffa9be385fba0f979d01fd7e4ab44"
SIZE_ART_627 = 1343628546

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
SAT_WEP = r"Data\INI\Weapon\Weapon_Vietnam_Missiles.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
BUILDING_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactoryBuilding.ini"
FAC_KEY = (
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces"
    r"\Buildings\Vietnam_MissileFactory.ini"
)
ALFAHD_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"

MARKER = (
    "; ===== Vietnam missiles A-H "
    "(Weapon.ini load path for Command_FireMainWeapon) ====="
)

MISSILES = [
    {
        "slot": "A",
        "btn": "CB_VIETNAM_MISSILE_A",
        "object": "Vietnam_VCM01",
        "weapon": "Weapon_Vietnam_VCM01",
        "warhead": "Weapon_Vietnam_VCM01_Warhead",
        "projectile": "Projectile_Vietnam_VCM01",
        "range": "860.0",
        "damage": "5000.0",
        "secondary": "250.0",
        "cost": "800",
        "time": "15.0",
    },
    {
        "slot": "B",
        "btn": "CB_VIETNAM_MISSILE_B",
        "object": "Vietnam_VCM02",
        "weapon": "Weapon_Vietnam_VCM02",
        "warhead": "Weapon_Vietnam_VCM02_Warhead",
        "projectile": "Projectile_Vietnam_VCM02",
        "range": "1204.0",
        "damage": "1250.0",
        "secondary": "62.5",
        "cost": "1200",
        "time": "20.0",
    },
    {
        "slot": "C",
        "btn": "CB_VIETNAM_MISSILE_C",
        "object": "Vietnam_SongHong",
        "weapon": "Weapon_Vietnam_SongHong",
        "warhead": "Weapon_Vietnam_SongHong_Warhead",
        "projectile": "Projectile_Vietnam_SongHong",
        "range": "1376.0",
        "damage": "2000.0",
        "secondary": "100.0",
        "cost": "1600",
        "time": "25.0",
    },
    {
        "slot": "D",
        "btn": "CB_VIETNAM_MISSILE_D",
        "object": "Vietnam_HongHa",
        "weapon": "Weapon_Vietnam_HongHa",
        "warhead": "Weapon_Vietnam_HongHa_Warhead",
        "projectile": "Projectile_Vietnam_HongHa",
        "range": "1548.0",
        "damage": "9000.0",
        "secondary": "450.0",
        "cost": "2000",
        "time": "30.0",
    },
    {
        "slot": "E",
        "btn": "CB_VIETNAM_MISSILE_E",
        "object": "Vietnam_CuuLong",
        "weapon": "Weapon_Vietnam_CuuLong",
        "warhead": "Weapon_Vietnam_CuuLong_Warhead",
        "projectile": "Projectile_Vietnam_CuuLong",
        "range": "1720.0",
        "damage": "1750.0",
        "secondary": "87.5",
        "cost": "2500",
        "time": "35.0",
    },
    {
        "slot": "F",
        "btn": "CB_VIETNAM_MISSILE_F",
        "object": "Vietnam_TruongSon",
        "weapon": "Weapon_Vietnam_TruongSon",
        "warhead": "Weapon_Vietnam_TruongSon_Warhead",
        "projectile": "Projectile_Vietnam_TruongSon",
        "range": "1892.0",
        "damage": "3000.0",
        "secondary": "150.0",
        "cost": "3000",
        "time": "40.0",
    },
    {
        "slot": "G",
        "btn": "CB_VIETNAM_MISSILE_G",
        "object": "Vietnam_BachDang",
        "weapon": "Weapon_Vietnam_BachDang",
        "warhead": "Weapon_Vietnam_BachDang_Warhead",
        "projectile": "Projectile_Vietnam_BachDang",
        "range": "2236.0",
        "damage": "2500.0",
        "secondary": "125.0",
        "cost": "4000",
        "time": "50.0",
    },
    {
        "slot": "H",
        "btn": "CB_VIETNAM_MISSILE_H",
        "object": "Vietnam_ThangLong",
        "weapon": "Weapon_Vietnam_ThangLong",
        "warhead": "Weapon_Vietnam_ThangLong_Warhead",
        "projectile": "Projectile_Vietnam_ThangLong",
        "range": "2580.0",
        "damage": "6000.0",
        "secondary": "300.0",
        "cost": "5000",
        "time": "60.0",
    },
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


def last_block_from_files(order: list[str], files: dict[str, bytes], kind: str, name: str) -> tuple[str, str]:
    found = ("", "")
    needle = f"{kind} {name}".encode("ascii")
    for key in order:
        blob = files[key]
        if needle not in blob:
            continue
        block = last_block(blob.decode("latin1"), kind, name)
        if block:
            found = (key, block)
    return found


def field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block or "", re.M)
    return m.group(1).strip() if m else ""


def slot_map(block: str) -> dict[int, str]:
    out = {}
    for m in re.finditer(r"(?m)^\s*(\d+)\s*=\s*(\S+)", block or ""):
        out[int(m.group(1))] = m.group(2)
    return out


def to_crlf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\n", "\r\n")


def sanitize_weapon_text(text: str) -> str:
    # fmt_num(62.5) + ".0" emitted illegal 62.5.0 / 87.5.0 floats.
    return re.sub(r"(=\s*)(\d+\.\d+)\.0\b", r"\1\2", text)


def extract_weapon_blocks(text: str) -> str:
    blocks = []
    for m in MISSILES:
        for name in (m["weapon"], m["warhead"]):
            block = last_block(text, "Weapon", name)
            if not block:
                raise SystemExit(f"satellite missing {name}")
            blocks.append(block.rstrip() + "\r\n")
    return "\r\n".join(blocks)


def append_vietnam_weapons(weapon_ini: str, satellite: str) -> str:
    if last_block(weapon_ini, "Weapon", "Weapon_Vietnam_VCM01"):
        raise SystemExit("Weapon.ini already has Vietnam weapons; inspect before splicing")
    cleaned = sanitize_weapon_text(satellite)
    body = extract_weapon_blocks(to_crlf(cleaned))
    return weapon_ini.rstrip("\r\n") + "\r\n\r\n" + MARKER + "\r\n" + body + "\r\n"


def validate(data: dict[str, bytes], src: dict[str, bytes], order: list[str]) -> list[str]:
    fails: list[str] = []

    for key in (CS_KEY, CB_KEY, R11_KEY, FACTORY_KEY, BUILDING_KEY, FAC_KEY, ALFAHD_KEY):
        if data.get(key) != src.get(key):
            fails.append(f"frozen mutated {key}")

    src_w = src[WEAPON_KEY].decode("latin1")
    new_w = data[WEAPON_KEY].decode("latin1")
    if not new_w.startswith(src_w.rstrip("\r\n")):
        fails.append("Weapon.ini prefix (existing weapons) mutated")
    if MARKER not in new_w:
        fails.append("Weapon.ini missing Vietnam marker")
    if last_block(src_w, "Weapon", "SRBM_ALHIJARAH_HE") != last_block(new_w, "Weapon", "SRBM_ALHIJARAH_HE"):
        fails.append("SRBM_ALHIJARAH_HE mutated")
    if last_block(src_w, "Weapon", "Weapon_Iraq_AlFahd500") != last_block(new_w, "Weapon", "Weapon_Iraq_AlFahd500"):
        fails.append("Weapon_Iraq_AlFahd500 mutated")
    if last_block(src_w, "Weapon", "Weapon_Iraq_AlMansour") != last_block(new_w, "Weapon", "Weapon_Iraq_AlMansour"):
        fails.append("Weapon_Iraq_AlMansour mutated")

    sat = data[SAT_WEP].decode("latin1")
    if re.search(r"=\s*\d+\.\d+\.0\b", sat) or re.search(r"=\s*\d+\.\d+\.0\b", new_w):
        fails.append("illegal float still present (x.y.0)")

    fire_file, fire = last_block_from_files(order, data, "CommandButton", "Command_FireMainWeapon")
    if field(fire, "Command") != "FIRE_WEAPON":
        fails.append("Command_FireMainWeapon Command")
    if field(fire, "WeaponSlot") != "PRIMARY":
        fails.append("Command_FireMainWeapon WeaponSlot")
    if "NEED_TARGET_POS" not in field(fire, "Options"):
        fails.append("Command_FireMainWeapon Options")
    if field(fire, "Disabled") or field(fire, "Science") or field(fire, "Upgrade"):
        fails.append("Command_FireMainWeapon locked")

    cs_file, scud = last_block_from_files(order, data, "CommandSet", "Scud_B_CommandSet")
    slots = slot_map(scud)
    if slots.get(1) != "Command_FireMainWeapon":
        fails.append("Scud_B_CommandSet slot 1")
    if cs_file != CS_KEY:
        fails.append(f"Scud_B_CommandSet last-wins in {cs_file}")

    _fac_file, fac_cs = last_block_from_files(order, data, "CommandSet", "Vietnam_MissileFactoryCommandSet")
    if not fac_cs:
        fails.append("missing Vietnam_MissileFactoryCommandSet")
    for m in MISSILES:
        if m["btn"] not in fac_cs:
            fails.append(f"factory missing {m['btn']}")
    if last_block(data[CS_KEY].decode("latin1"), "CommandSet", "Vietnam_MissileFactoryCommandSet") == "":
        fails.append("CommandSet.ini lost Vietnam_MissileFactoryCommandSet")

    for m in MISSILES:
        unit_file, unit = last_block_from_files(order, data, "Object", m["object"])
        if not unit:
            fails.append(f"missing object {m['object']}")
            continue
        if field(unit, "CommandSet") != "Scud_B_CommandSet":
            fails.append(f"{m['object']} CommandSet={field(unit, 'CommandSet')}")
        if f"Weapon = PRIMARY   {m['weapon']}" not in unit:
            fails.append(f"{m['object']} PRIMARY")
        if "CAN_ATTACK" not in field(unit, "KindOf"):
            fails.append(f"{m['object']} KindOf")
        if field(unit, "BuildCost") != m["cost"]:
            fails.append(f"{m['object']} BuildCost")
        if field(unit, "BuildTime") != m["time"]:
            fails.append(f"{m['object']} BuildTime")
        if field(unit, "Side") != "Vietnam":
            fails.append(f"{m['object']} Side")

        wblock = last_block(new_w, "Weapon", m["weapon"])
        if not wblock:
            fails.append(f"Weapon.ini missing {m['weapon']}")
            continue
        if field(wblock, "AttackRange") != m["range"]:
            fails.append(f"{m['weapon']} AttackRange={field(wblock, 'AttackRange')}")
        if field(wblock, "PrimaryDamage") != m["damage"]:
            fails.append(f"{m['weapon']} PrimaryDamage={field(wblock, 'PrimaryDamage')}")
        if field(wblock, "SecondaryDamage") != m["secondary"]:
            fails.append(f"{m['weapon']} SecondaryDamage={field(wblock, 'SecondaryDamage')}")
        if field(wblock, "MinimumAttackRange") != "800.0":
            fails.append(f"{m['weapon']} MinimumAttackRange")
        if field(wblock, "ProjectileObject") != m["projectile"]:
            fails.append(f"{m['weapon']} ProjectileObject")
        if field(wblock, "AntiGround") != "Yes":
            fails.append(f"{m['weapon']} AntiGround")
        if field(wblock, "ClipSize") != "1":
            fails.append(f"{m['weapon']} ClipSize")
        sat_w = last_block(sat, "Weapon", m["weapon"])
        if not sat_w:
            fails.append(f"satellite missing {m['weapon']}")
        elif sat_w.rstrip() != wblock.rstrip():
            fails.append(f"satellite/Weapon.ini mismatch {m['weapon']}")

        war = last_block(new_w, "Weapon", m["warhead"])
        if not war:
            fails.append(f"Weapon.ini missing {m['warhead']}")
        elif not last_block(sat, "Weapon", m["warhead"]):
            fails.append(f"satellite missing {m['warhead']}")

        _pfile, proj = last_block_from_files(order, data, "Object", m["projectile"])
        if not proj:
            fails.append(f"missing projectile {m['projectile']}")
        elif "MissileAIUpdate" not in proj:
            fails.append(f"{m['projectile']} MissileAIUpdate")

        _bfile, btn = last_block_from_files(order, data, "CommandButton", m["btn"])
        if field(btn, "Command") != "UNIT_BUILD" or field(btn, "Object") != m["object"]:
            fails.append(f"{m['btn']} production chain")

    r11_file, r11 = last_block_from_files(order, data, "Object", "Iraq_R11ScudB")
    if field(r11, "CommandSet") != "Scud_B_CommandSet":
        fails.append("9P117 CommandSet")
    if "Weapon = PRIMARY   SRBM_ALHIJARAH_HE" not in r11:
        fails.append("9P117 PRIMARY")
    if r11_file != R11_KEY:
        fails.append("9P117 last-wins file")

    _af_file, alfahd = last_block_from_files(order, data, "Object", "Iraq_AlFahd500")
    if field(alfahd, "CommandSet") != "Scud_B_CommandSet":
        fails.append("AlFahd CommandSet")
    if "Weapon = PRIMARY   Weapon_Iraq_AlFahd500" not in alfahd:
        fails.append("AlFahd PRIMARY")

    all_ini = b"".join(v for k, v in data.items() if k.lower().endswith(".ini"))
    if b"ZZZZ" in all_ini and b"Weapon_Vietnam_" in all_ini:
        for k, v in data.items():
            if "zzzz" in k.lower() and b"Weapon_Vietnam_" in v:
                fails.append(f"ZZZZ shortcut {k}")
    return fails


def write_release_docs(data_path: Path, art_path: Path, zip_path: Path, packed: dict[str, bytes]) -> str:
    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    zip_sha = sha256_path(zip_path)

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    wini = packed[WEAPON_KEY].decode("latin1")
    sat = packed[SAT_WEP].decode("latin1")
    (ext / "Weapon.ini.Vietnam.txt").write_text(
        MARKER + "\r\n" + extract_weapon_blocks(wini),
        encoding="utf-8",
    )
    (ext / "Weapon_Vietnam_Missiles.ini").write_text(sat, encoding="utf-8")

    chain_lines = [
        "LIVE FIRE CHAIN (packed last-wins)",
        "",
        "Vietnam_MissileFactoryCommandSet last-wins in CommandSet.ini",
        "  CB_VIETNAM_MISSILE_A-H (UNIT_BUILD) last-wins in CommandButton.ini",
        "    Object Vietnam_* last-wins in Vietnam Wheeled INI",
        "      CommandSet = Scud_B_CommandSet",
        "      Scud_B_CommandSet slot 1 = Command_FireMainWeapon",
        "        Command_FireMainWeapon = FIRE_WEAPON / PRIMARY / NEED_TARGET_POS",
        "      WeaponSet PRIMARY = Weapon_Vietnam_*",
        "        last-wins now in Data\\INI\\Weapon.ini (was satellite-only)",
        "        ProjectileObject = Projectile_Vietnam_*",
        "",
    ]
    for m in MISSILES:
        chain_lines.append(
            f"{m['slot']} {m['object']}: {m['btn']} -> {m['object']} -> "
            f"Scud_B_CommandSet / Command_FireMainWeapon -> {m['weapon']} -> {m['projectile']}"
        )
        chain_lines.append(
            f"    AttackRange={m['range']} Min=800.0 PrimaryDamage={m['damage']} "
            f"SecondaryDamage={m['secondary']} BuildCost={m['cost']} BuildTime={m['time']}"
        )
    (ext / "CHAIN.txt").write_text("\n".join(chain_lines) + "\n", encoding="utf-8")

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #627 s-vietnam-factory-menu-fix",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "ART_UNCHANGED=YES",
        "FACTORY_MENU_UNCHANGED=YES",
        "IRAQ_FACTORY_ROSTER_UNCHANGED=YES",
        "NINE_P117_UNCHANGED=YES",
        "KASHTAN_FALAQ_RETAINED=YES",
        "IRAQ_ABBAS_BIO_RETAINED=YES",
        "NO_REARM=YES",
        "NO_ZZZZ=YES",
        "",
        "ROOT CAUSE: Weapon_Vietnam_* lived only in Data\\INI\\Weapon\\Weapon_Vietnam_Missiles.ini.",
        "Command_FireMainWeapon is FIRE_WEAPON / PRIMARY. PRIMARY was empty at runtime,",
        "same class of bug as Al-Fahd before it was spliced into Weapon.ini.",
        "Satellite also had illegal SecondaryDamage 62.5.0 / 87.5.0 (VCM-02 / Cửu Long).",
        "FIX: sanitize those floats; append A-H weapons+warheads to Weapon.ini last-wins.",
        "CommandSet.ini / CommandButton.ini / factory / ART / 9P117 / Iraq A-M untouched.",
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
            "ZIP_FILE=SPECTER_VIETNAM_MISSILE_FIRE_FIX.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #627",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-vietnam-missile-fire-fix/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-vietnam-missile-fire-fix/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-vietnam-missile-fire-fix/SPECTER_VIETNAM_MISSILE_FIRE_FIX.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-vietnam-missile-fire-fix",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-vietnam-missile-fire-fix",
                "BASELINE=PR #627",
                "STATIC VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN — the game was not launched.",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Vietnam missile A-H fire-button fix.\n"
        "Splices Weapon_Vietnam_* into Data\\INI\\Weapon.ini so Command_FireMainWeapon\n"
        "resolves PRIMARY. Factory menu, ART, names, markings, and stats unchanged\n"
        "except illegal 62.5.0 / 87.5.0 floats become 62.5 / 87.5.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Vietnam missile A-H fire-button fix\n\n"
        "- Root cause: Vietnam A-H weapons were only in a satellite Weapon file, so "
        "`Command_FireMainWeapon` (FIRE_WEAPON / PRIMARY) stayed inactive. Same class "
        "of bug as Al-Fahd before it was spliced into `Weapon.ini`.\n"
        "- Satellite `SecondaryDamage = 62.5.0` / `87.5.0` (VCM-02 / Cửu Long) was also illegal.\n"
        "- Fix: sanitize those floats and append the 16 weapon/warhead blocks to `Weapon.ini`.\n"
        "- Factory menu, production buttons, 9P117, Iraq A-M, ART, names, colors, "
        "dorsal flags, range, damage, cost, and build time are unchanged.\n"
        "- Static validation only. The game was not launched.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "Weapon.ini now last-wins Weapon_Vietnam_* and *_Warhead after the existing catalog.\n"
        "Data\\INI\\Weapon\\Weapon_Vietnam_Missiles.ini kept with the same cleaned blocks.\n"
        "CommandSet.ini / CommandButton.ini / Vietnam factory objects are unchanged from PR #627.\n"
        "9P117 SRBM_ALHIJARAH_HE and Iraq factory weapons are unchanged.\n"
    )
    return hashes


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_627 or SRC_DATA.stat().st_size != SIZE_DATA_627:
        raise SystemExit("DATA baseline is not PR #627 SPECTER_VIETNAM_FACTORY_MENU_FIX")
    if sha256_path(SRC_ART) != SHA_ART_627 or SRC_ART.stat().st_size != SIZE_ART_627:
        raise SystemExit("ART baseline is not PR #627 SPECTER_VIETNAM_FACTORY_MENU_FIX")

    src_data, _ = parse_big_ordered(SRC_DATA.read_bytes())
    data = dict(src_data)

    sat = sanitize_weapon_text(src_data[SAT_WEP].decode("latin1"))
    sat = to_crlf(sat)
    if "62.5.0" in sat or "87.5.0" in sat:
        raise SystemExit("sanitize failed")
    data[SAT_WEP] = sat.encode("latin1")
    data[WEAPON_KEY] = append_vietnam_weapons(
        src_data[WEAPON_KEY].decode("latin1"), sat
    ).encode("latin1")

    if LOOSE_WEP.exists():
        LOOSE_WEP.write_bytes(data[SAT_WEP])

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

    zip_path = ROOT / "patch/Release/SPECTER_VIETNAM_MISSILE_FIRE_FIX.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")

    hashes = write_release_docs(data_path, art_path, zip_path, packed)
    print("PACKED")
    print(hashes)


if __name__ == "__main__":
    main()
