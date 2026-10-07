#!/usr/bin/env python3
"""Fix B/C/D/H/I/J spawn crash on the PR #574 DATA baseline.

Starts from the packed PR #574 _SPEC_DATA_ONE.big (SHA 87ce408d...).
Does NOT import PR #575+ locomotor/alias/projectile experiments.
Does NOT modify Al-Fahd500 / MOTHER / 9P117 / ART.

Fix 1: remove ReplaceObjectUpgrade + OBJECT_UPGRADE rebuild buttons that
       reference Upgrade templates only defined in unloaded
       Data\\INI\\Upgrade_IraqFactoryMissiles.ini. TEL CommandSet becomes
       Scud_B_CommandSet (working A architecture).
Fix 2: move B/C/D/H/I/J primary + warhead weapons from the unloaded
       Data\\INI\\Weapon\\ sidecar into engine-loaded Data\\INI\\Weapon.ini.
       Stats are copied verbatim from the #574 sidecar.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_DATA_BCDHIJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_DATA_BCDHIJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_BCDHIJ_SPAWN_FIX"
SRC_DIR = ROOT / "patch/Data/INI"

BASE_DATA_SHA = "87ce408d2fa679b82f9fad22b515b10a9b993aa4453cc32175e2af093410a126"
BASE_DATA_SIZE = 366469264
BASE_ART_SHA = "e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4"
BASE_ART_SIZE = 1292294758

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
UNIT_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
PROJ_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini"
WEP_A_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlFahd500.ini"
WEP_SIDECAR_KEY = r"Data\INI\Weapon\Weapon_Iraq_FactoryMissiles.ini"
UPG_SIDECAR_KEY = r"Data\INI\Upgrade_IraqFactoryMissiles.ini"
LOCO_KEY = r"Data\INI\Locomotor.ini"
UPGRADE_KEY = r"Data\INI\Upgrade.ini"

MISSILES = [
    {
        "slot": "B",
        "object": "Iraq_AlHusseinII",
        "weapon": "Weapon_Iraq_AlHusseinII",
        "warhead": "Weapon_Iraq_AlHusseinII_Warhead",
        "projectile": "Projectile_Iraq_AlHusseinII",
        "model": "Irq_AlHussein2M",
        "tex": "Irq_AlHussein2P.tga",
        "cameo": "specter_missile_b",
        "price": 1800,
        "build": 25,
        "range": "2064.0",
        "damage": "4000.0",
        "scatter": "87.5",
        "death": "4400",
        "hier": b"IRQ_AH2_M",
    },
    {
        "slot": "C",
        "object": "Iraq_AlSamoudII",
        "weapon": "Weapon_Iraq_AlSamoudII",
        "warhead": "Weapon_Iraq_AlSamoudII_Warhead",
        "projectile": "Projectile_Iraq_AlSamoudII",
        "model": "Irq_AlSamoud2M",
        "tex": "Irq_AlSamoud2P.tga",
        "cameo": "specter_missile_c",
        "price": 1700,
        "build": 22,
        "range": "2408.0",
        "damage": "3000.0",
        "scatter": "43.75",
        "death": "3300",
        "hier": b"IRQ_AS2_M",
    },
    {
        "slot": "D",
        "object": "Iraq_AlAbbas",
        "weapon": "Weapon_Iraq_AlAbbas",
        "warhead": "Weapon_Iraq_AlAbbas_Warhead",
        "projectile": "Projectile_Iraq_AlAbbas",
        "model": "Irq_AlAbbas2M",
        "tex": "Irq_AlAbbas2P.tga",
        "cameo": "specter_missile_d",
        "price": 2600,
        "build": 35,
        "range": "2752.0",
        "damage": "6000.0",
        "scatter": "70",
        "death": "6600",
        "hier": b"IRQ_AAB_M",
    },
    {
        "slot": "H",
        "object": "Iraq_AlBasrah",
        "weapon": "Weapon_Iraq_AlBasrah",
        "warhead": "Weapon_Iraq_AlBasrah_Warhead",
        "projectile": "Projectile_Iraq_AlBasrah",
        "model": "Irq_AlBasrahM",
        "tex": "Irq_AlBasrahP.tga",
        "cameo": "specter_missile_h",
        "price": 5000,
        "build": 60,
        "range": "3956.0",
        "damage": "12000.0",
        "scatter": "87.5",
        "death": "13200",
        "hier": b"IRQ_ABS_M",
    },
    {
        "slot": "I",
        "object": "Iraq_AlNasir",
        "weapon": "Weapon_Iraq_AlNasir",
        "warhead": "Weapon_Iraq_AlNasir_Warhead",
        "projectile": "Projectile_Iraq_AlNasir",
        "model": "Irq_AlNasirM",
        "tex": "Irq_AlNasirP.tga",
        "cameo": "specter_missile_i",
        "price": 6500,
        "build": 75,
        "range": "4128.0",
        "damage": "16000.0",
        "scatter": "50",
        "death": "17600",
        "hier": b"IRQ_ANS_M",
    },
    {
        "slot": "J",
        "object": "Iraq_AlMansour",
        "weapon": "Weapon_Iraq_AlMansour",
        "warhead": "Weapon_Iraq_AlMansour_Warhead",
        "projectile": "Projectile_Iraq_AlMansour",
        "model": "Irq_AlMansourM",
        "tex": "Irq_AlMansourP.tga",
        "cameo": "specter_missile_j",
        "price": 8000,
        "build": 90,
        "range": "4300.0",
        "damage": "20000.0",
        "scatter": "35",
        "death": "22000",
        "hier": b"IRQ_AMN_M",
    },
]


def unit_key(obj: str) -> str:
    return rf"Data\INI\Object\Specter\Iraq Army\Wheeled\{obj}.ini"


def proj_key(obj: str) -> str:
    return rf"Data\INI\Object\Specter\Iraq Army\{obj}_Projectile.ini"


def tel_cs(obj: str) -> str:
    return f"{obj}_TELCommandSet"


def rebuild_btn(obj: str) -> str:
    return f"CB_{obj}_Rebuild"


def rebuild_upg(obj: str) -> str:
    return f"Upgrade_{obj}_Rebuild"


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes) -> dict[str, bytes]:
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


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


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    expected = header
    for name, off, size in sorted(files, key=lambda x: x[1]):
        if off != expected:
            issues.append(f"overlap/gap {name}")
            break
        expected = off + size
    if expected != len(blob):
        issues.append("trailing gap/overflow")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def command_block(text: str, kind: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text)
    return m.group(0) if m else None


def slot_map(block: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def last_weapon_block(data: dict[str, bytes], name: str) -> tuple[str, str] | None:
    blocks: list[tuple[str, str]] = []
    wep = data[WEAPON_KEY].decode("latin1")
    b = command_block(wep, "Weapon", name)
    if b:
        blocks.append((WEAPON_KEY, b))
    for k in sorted(data, key=lambda x: x.lower()):
        lk = k.replace("/", "\\").lower()
        if lk.startswith(r"data\ini\weapon" + "\\") and lk.endswith(".ini"):
            t = data[k].decode("latin1")
            blk = command_block(t, "Weapon", name)
            if blk:
                blocks.append((k, blk))
    return blocks[-1] if blocks else None


def weapon_def_count(data: dict[str, bytes], name: str) -> int:
    n = 0
    for k, v in data.items():
        if not k.lower().endswith(".ini"):
            continue
        n += len(re.findall(rf"^Weapon {re.escape(name)}\s*$".encode("ascii"), v, re.M))
    return n


def object_def_count(data: dict[str, bytes], name: str) -> int:
    n = 0
    for k, v in data.items():
        if not k.lower().endswith(".ini"):
            continue
        n += len(re.findall(rf"^Object {re.escape(name)}\s*$".encode("ascii"), v, re.M))
    return n


def strip_block(text: str, kind: str, name: str) -> tuple[str, int]:
    blk = command_block(text, kind, name)
    if not blk:
        return text, 0
    idx = text.find(blk)
    if idx < 0:
        return text, 0
    end = idx + len(blk)
    if text.startswith("\r\n", end):
        end += 2
    elif text.startswith("\n", end):
        end += 1
    if text.startswith("\r\n", end):
        end += 2
    elif text.startswith("\n", end):
        end += 1
    return text[:idx] + text[end:], 1


REBUILD_MODULE = re.compile(
    r"[ \t]*; After firing \(ClipSize 1, AutoReloadsClip No\) the missile is spent\.\r?\n"
    r"[ \t]*; OBJECT_UPGRADE.*\r?\n"
    r"[ \t]*; then ReplaceObjectUpgrade.*\r?\n"
    r"[ \t]*Behavior = ReplaceObjectUpgrade ModuleTag_Rebuild\r?\n"
    r"[ \t]*TriggeredBy[ \t]*=[ \t]*Upgrade_Iraq_\S+_Rebuild\r?\n"
    r"[ \t]*ReplaceObject[ \t]*=[ \t]*\S+\r?\n"
    r"[ \t]*End\r?\n",
    re.M,
)


def patch_unit(raw: bytes, obj: str) -> bytes:
    text = raw.decode("latin1")
    new, n = re.subn(
        rf"CommandSet[ \t]*=[ \t]*{re.escape(tel_cs(obj))}",
        "CommandSet    = Scud_B_CommandSet",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"{obj}: CommandSet replace failed ({n})")
    stripped, n2 = REBUILD_MODULE.subn("", new, count=1)
    if n2 != 1:
        raise SystemExit(f"{obj}: ReplaceObjectUpgrade strip failed ({n2})")
    if "ReplaceObjectUpgrade" in stripped or rebuild_upg(obj) in stripped:
        raise SystemExit(f"{obj}: rebuild residue remains")
    if "CommandSet    = Scud_B_CommandSet" not in stripped:
        raise SystemExit(f"{obj}: Scud_B_CommandSet not applied")
    return stripped.replace("\n", "\r\n").replace("\r\r\n", "\r\n").encode("latin1")


def sidecar_weapon_body(sidecar: str) -> str:
    """Keep exact Weapon ... End blocks from the #574 sidecar; rewrite header."""
    m = re.search(r"^Weapon ", sidecar, re.M)
    if not m:
        raise SystemExit("sidecar has no Weapon blocks")
    body = sidecar[m.start() :].strip() + "\n"
    header = (
        "; Iraq factory missiles B/C/D/H/I/J. Engine-loaded via Data\\INI\\Weapon.ini.\n"
        "; Stats copied verbatim from PR #574 Data\\INI\\Weapon\\Weapon_Iraq_FactoryMissiles.ini.\n"
        "; MOTHER SRBM_ALHIJARAH_HE / Iraq_AlFahd500 weapons are not modified.\n"
        "; TheWeaponStore loads Data\\INI\\Weapon.ini only. The old Weapon\\ sidecar is removed.\n"
        "\n"
    )
    return header + body


def to_crlf_bytes(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def write_workspace(data: dict[str, bytes]) -> None:
    """Keep git sources in sync with packed last-wins for the files we own.

    Do not dump the entire packed CommandButton.ini / CommandSet.ini / Weapon.ini
    over the repo copies (those packed files are last-wins supersets).
    """
    for m in MISSILES:
        unit_path = SRC_DIR / "Object/Specter/Iraq Army/Wheeled" / f"{m['object']}.ini"
        unit_path.parent.mkdir(parents=True, exist_ok=True)
        unit_path.write_bytes(data[unit_key(m["object"])].replace(b"\r\n", b"\n"))
    wep_path = SRC_DIR / "Weapon.ini"
    wep_text = wep_path.read_text(encoding="latin1")
    if "Weapon Weapon_Iraq_AlHusseinII" not in wep_text:
        body = data[WEAPON_KEY].decode("latin1")
        start = body.find("; Iraq factory missiles B/C/D/H/I/J. Engine-loaded")
        if start < 0:
            raise SystemExit("packed Weapon.ini missing B-J appendix")
        appendix = body[start:].replace("\r\n", "\n")
        if not wep_text.endswith("\n"):
            wep_text += "\n"
        wep_path.write_text(wep_text + "\n" + appendix, encoding="latin1")
    sidecar = SRC_DIR / "Weapon/Weapon_Iraq_FactoryMissiles.ini"
    upgrade = SRC_DIR / "Upgrade_IraqFactoryMissiles.ini"
    if sidecar.exists():
        sidecar.unlink()
    if upgrade.exists():
        upgrade.unlink()


def validate(data: dict[str, bytes], src: dict[str, bytes], art: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    all_ini = b"".join(v for k, v in data.items() if k.lower().endswith(".ini"))

    for key, label in [
        (R11_KEY, "9P117.ini"),
        (FACTORY_KEY, "factory object"),
        (UNIT_A_KEY, "Iraq_AlFahd500.ini"),
        (PROJ_A_KEY, "Al-Fahd projectile"),
        (WEP_A_KEY, "Al-Fahd weapon sidecar"),
        (LOCO_KEY, "Locomotor.ini"),
        (UPGRADE_KEY, "Upgrade.ini"),
    ]:
        if data.get(key) != src.get(key):
            fails.append(f"{label} mutated vs PR #574")

    wep_src = src[WEAPON_KEY]
    wep_new = data[WEAPON_KEY]
    if not wep_new.startswith(wep_src):
        fails.append("Weapon.ini prefix (including Al-Fahd500 block) mutated")
    if wep_new == wep_src:
        fails.append("Weapon.ini was not extended with B-J weapons")

    r11 = data[R11_KEY].decode("latin1")
    if "BuildCost       = 1200" not in r11 or "Weapon = PRIMARY   SRBM_ALHIJARAH_HE" not in r11:
        fails.append("MOTHER Iraq_R11ScudB cost/weapon changed")

    unit_a = data[UNIT_A_KEY].decode("latin1")
    if "CommandSet    = Scud_B_CommandSet" not in unit_a:
        fails.append("Al-Fahd CommandSet changed")
    if "Weapon = PRIMARY   Weapon_Iraq_AlFahd500" not in unit_a:
        fails.append("Al-Fahd weapon link")
    if "ReplaceObjectUpgrade" in unit_a:
        fails.append("Al-Fahd unexpectedly gained ReplaceObjectUpgrade")

    last_a = last_weapon_block(data, "Weapon_Iraq_AlFahd500")
    if not last_a or "PrimaryDamage               = 8000.0" not in last_a[1]:
        fails.append("Al-Fahd last-wins damage")
    if last_a and last_a[0].replace("/", "\\").lower() != WEP_A_KEY.lower():
        fails.append(f"Al-Fahd weapon last-wins file {last_a[0]}")

    if WEP_SIDECAR_KEY in data:
        fails.append("unloaded Weapon\\ sidecar still packed")
    if UPG_SIDECAR_KEY in data:
        fails.append("unloaded Upgrade_IraqFactoryMissiles.ini still packed")

    if b"ReplaceObjectUpgrade ModuleTag_Rebuild" in all_ini:
        fails.append("ReplaceObjectUpgrade ModuleTag_Rebuild still present")
    if re.search(rb"Upgrade_Iraq_Al\w+_Rebuild", all_ini):
        fails.append("Upgrade_Iraq_*_Rebuild reference still present")
    if re.search(rb"CB_Iraq_Al\w+_Rebuild", all_ini):
        fails.append("rebuild CommandButton still present")
    if re.search(rb"_TELCommandSet", all_ini):
        fails.append("TEL CommandSet still present")

    loc = data[LOCO_KEY].decode("latin1")
    if not command_block(loc, "Locomotor", "R11SRBMLocomotor"):
        fails.append("R11SRBMLocomotor missing from Locomotor.ini")
    if not command_block(loc, "Locomotor", "Generic8x8Locomotor"):
        fails.append("Generic8x8Locomotor missing from Locomotor.ini")
    if re.search(r"^Locomotor Iraq_Al(HusseinII|SamoudII|Abbas|Basrah|Nasir|Mansour)_Locomotor", loc, re.M):
        fails.append("later dedicated missile locos leaked into Locomotor.ini")

    fac = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet") or ""
    slots = slot_map(fac)
    expect = {
        1: "CB_MISSILE_A",
        2: "CB_MISSILE_B",
        3: "CB_MISSILE_C",
        4: "CB_MISSILE_D",
        8: "CB_MISSILE_H",
        9: "CB_MISSILE_I",
        10: "CB_MISSILE_J",
        13: "Command_SetRallyPoint",
        14: "Command_Sell",
    }
    for k, v in expect.items():
        if slots.get(k) != v:
            fails.append(f"factory slot {k}={slots.get(k)} expected {v}")

    scud = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Scud_B_CommandSet") or ""
    scud_slots = slot_map(scud)
    if scud_slots.get(1) != "Command_FireMainWeapon":
        fails.append("Scud_B_CommandSet lost FireMainWeapon")

    for m in MISSILES:
        uk = unit_key(m["object"])
        pk = proj_key(m["object"])
        if object_def_count(data, m["object"]) != 1:
            fails.append(f"{m['object']} definition count {object_def_count(data, m['object'])}")
        if object_def_count(data, m["projectile"]) != 1:
            fails.append(f"{m['projectile']} definition count {object_def_count(data, m['projectile'])}")
        unit = data[uk].decode("latin1")
        if f"SelectPortrait         = {m['cameo']}" not in unit:
            fails.append(f"{m['object']} SelectPortrait")
        if f"ButtonImage            = {m['cameo']}" not in unit:
            fails.append(f"{m['object']} ButtonImage")
        if f"BuildCost       = {m['price']}" not in unit:
            fails.append(f"{m['object']} price")
        if f"BuildTime       = {m['build']}.0" not in unit:
            fails.append(f"{m['object']} build time")
        if f"Weapon = PRIMARY   {m['weapon']}" not in unit:
            fails.append(f"{m['object']} weapon")
        if "CommandSet    = Scud_B_CommandSet" not in unit:
            fails.append(f"{m['object']} CommandSet")
        if "ReplaceObjectUpgrade" in unit:
            fails.append(f"{m['object']} still has ReplaceObjectUpgrade")
        if "Model                           = Irq_AlFahd500" not in unit:
            fails.append(f"{m['object']} launcher model")
        if "IRQ_AF500.IRQ_AF500" not in unit:
            fails.append(f"{m['object']} launch anim")
        if "Locomotor = SET_NORMAL Generic8x8Locomotor" not in unit:
            fails.append(f"{m['object']} unit locomotor")

        if data[pk] != src[pk]:
            fails.append(f"{m['object']} projectile mutated vs PR #574")
        proj = data[pk].decode("latin1")
        if f"Model = {m['model']}" not in proj:
            fails.append(f"{m['object']} projectile Model")
        if f"DeathWeapon   = {m['warhead']}" not in proj:
            fails.append(f"{m['object']} death weapon")
        if "Locomotor = SET_NORMAL R11SRBMLocomotor" not in proj:
            fails.append(f"{m['object']} projectile locomotor")

        if weapon_def_count(data, m["weapon"]) != 1:
            fails.append(f"{m['weapon']} definition count {weapon_def_count(data, m['weapon'])}")
        if weapon_def_count(data, m["warhead"]) != 1:
            fails.append(f"{m['warhead']} definition count {weapon_def_count(data, m['warhead'])}")
        wep = last_weapon_block(data, m["weapon"])
        if not wep:
            fails.append(f"missing weapon {m['weapon']}")
        else:
            if wep[0].replace("/", "\\") != WEAPON_KEY:
                fails.append(f"{m['weapon']} last-wins {wep[0]} (must be Weapon.ini)")
            if f"AttackRange                 = {m['range']}" not in wep[1]:
                fails.append(f"{m['weapon']} range")
            if f"PrimaryDamage               = {m['damage']}" not in wep[1]:
                fails.append(f"{m['weapon']} damage")
            if f"ScatterRadius               = {m['scatter']}" not in wep[1]:
                fails.append(f"{m['weapon']} scatter")
            if f"ProjectileObject            = {m['projectile']}" not in wep[1]:
                fails.append(f"{m['weapon']} projectile")
            if "FireFX                      = FX_IskanderFiringEffects" not in wep[1]:
                fails.append(f"{m['weapon']} FireFX")
        war = last_weapon_block(data, m["warhead"])
        if not war or war[0].replace("/", "\\") != WEAPON_KEY:
            fails.append(f"{m['warhead']} not in Weapon.ini")
        elif f"PrimaryDamage           = {m['death']}" not in war[1]:
            fails.append(f"{m['warhead']} death damage")

        btn = command_block(data[CB_KEY].decode("latin1"), "CommandButton", f"CB_MISSILE_{m['slot']}") or ""
        if f"Object        = {m['object']}" not in btn:
            fails.append(f"CB_MISSILE_{m['slot']} Object")
        if f"ButtonImage   = {m['cameo']}" not in btn:
            fails.append(f"CB_MISSILE_{m['slot']} art")

        w3d = rf"Art\W3D\{m['model']}.W3D"
        tex = rf"Art\Textures\{m['tex']}"
        if w3d not in art:
            fails.append(f"ART missing {w3d}")
        elif m["hier"] not in art[w3d]:
            fails.append(f"{m['model']} hierarchy missing")
        if tex not in art:
            fails.append(f"ART missing {tex}")

    zzzz = [
        k
        for k, v in data.items()
        if "zzzz" in k.lower()
        and any(m["object"].encode("ascii") in v for m in MISSILES)
    ]
    if zzzz:
        fails.append(f"ZZZZ override {zzzz[:4]}")

    # No PR #575+ hyphenated Specter-path aliases.
    for k in data:
        lk = k.replace("/", "\\").lower()
        if "iraq-al" in lk and "specter" in lk:
            fails.append(f"hyphenated Specter alias leaked {k}")

    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("PR #574 DATA baseline mismatch")
    if SRC_ART.stat().st_size != BASE_ART_SIZE or sha256_path(SRC_ART) != BASE_ART_SHA:
        raise SystemExit("PR #574 ART baseline mismatch")

    src = parse_big(SRC_DATA.read_bytes())
    art = parse_big(SRC_ART.read_bytes())
    data = dict(src)

    sidecar_text = data[WEP_SIDECAR_KEY].decode("latin1")
    append = sidecar_weapon_body(sidecar_text)
    wep = data[WEAPON_KEY]
    if not wep.endswith(b"\r\n"):
        wep += b"\r\n"
    if not wep.endswith(b"\r\n\r\n"):
        wep += b"\r\n"
    data[WEAPON_KEY] = wep + to_crlf_bytes(append)

    cb = data[CB_KEY].decode("latin1")
    cs = data[CS_KEY].decode("latin1")
    for m in MISSILES:
        data[unit_key(m["object"])] = patch_unit(data[unit_key(m["object"])], m["object"])
        cb, n_btn = strip_block(cb, "CommandButton", rebuild_btn(m["object"]))
        if n_btn != 1:
            raise SystemExit(f"strip {rebuild_btn(m['object'])} failed ({n_btn})")
        cs, n_cs = strip_block(cs, "CommandSet", tel_cs(m["object"]))
        if n_cs != 1:
            raise SystemExit(f"strip {tel_cs(m['object'])} failed ({n_cs})")
    data[CB_KEY] = cb.encode("latin1")
    data[CS_KEY] = cs.encode("latin1")

    del data[WEP_SIDECAR_KEY]
    del data[UPG_SIDECAR_KEY]

    write_workspace(data)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    packed_data = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed_data)

    extracted = parse_big(out_data.read_bytes())
    stage = OUT / "LAST_WINS_EXTRACT/DATA"
    dump_keys = [CB_KEY, CS_KEY, WEAPON_KEY, UNIT_A_KEY, R11_KEY, FACTORY_KEY]
    dump_keys += [unit_key(m["object"]) for m in MISSILES]
    dump_keys += [proj_key(m["object"]) for m in MISSILES]
    for rel in dump_keys:
        p = stage / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])

    fails = validate(extracted, src, art)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed_data))
    if WEP_SIDECAR_KEY in extracted or UPG_SIDECAR_KEY in extracted:
        fails.append("sidecar still in re-extracted BIG")

    data_sha = sha256_path(out_data)
    report = [
        "# SPECTER Iraq B/C/D/H/I/J spawn-crash + Weapon.ini load fix",
        "",
        "Baseline: PR #574 DATA+ART (inclusive). PR #575+ NOT imported.",
        "MOTHER / Iraq_R11ScudB / 9P117 — NOT MODIFIED",
        "Al-Fahd500 object / CommandSet / weapon / projectile / ART — NOT MODIFIED",
        "ART — NOT REBUILT (use PR #574 _SPEC_ART_ONE.big)",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART SHA256 (unchanged): {BASE_ART_SHA}",
        f"- ART size (unchanged): {BASE_ART_SIZE}",
        f"- ART files (unchanged): {len(art)}",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        report.append("RUNTIME_TEST=NOT RUN")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static / packed last-wins)",
        "- B/C/D/H/I/J: ReplaceObjectUpgrade removed",
        "- B/C/D/H/I/J: CommandSet = Scud_B_CommandSet (same as working A)",
        "- rebuild OBJECT_UPGRADE buttons removed",
        "- Upgrade_IraqFactoryMissiles.ini removed from packed DATA",
        "- Weapon\\Weapon_Iraq_FactoryMissiles.ini removed from packed DATA",
        "- primary + warhead weapons now defined once in Data\\INI\\Weapon.ini",
        "- PR #574 damage/range/scatter/warhead stats preserved",
        "- projectile Objects / W3D / TGA / R11SRBMLocomotor unchanged",
        "- Al-Fahd500 / MOTHER / factory CommandSet / ART unchanged",
        "- no dedicated locos, no hyphenated aliases, no ZZZZ overrides",
        "",
        "Static validation completed; runtime game test not performed.",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=NO\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted)}\n"
        "ART_FILE=PR574 _SPEC_ART_ONE.big (not rebuilt)\n"
        f"ART_SIZE={BASE_ART_SIZE}\n"
        f"ART_SHA256={BASE_ART_SHA}\n"
        f"ART_FILES={len(art)}\n"
        "OBJECTS=Iraq_AlHusseinII,Iraq_AlSamoudII,Iraq_AlAbbas,Iraq_AlBasrah,Iraq_AlNasir,Iraq_AlMansour\n"
        "COMMANDSET_TEL=Scud_B_CommandSet\n"
        "REBUILD=REMOVED (unloaded Upgrade_Iraq_*_Rebuild)\n"
        "WEAPONS=Data\\INI\\Weapon.ini (engine-loaded)\n"
        "BASELINE=PR #574 inclusive\n"
        "PR575PLUS=NOT IMPORTED\n"
        "ALFAHD_GAMEPLAY=UNCHANGED\n"
        "MOTHER_GAMEPLAY=UNCHANGED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq B/C/D/H/I/J spawn-crash fix (PR #574 baseline)\n"
        "\n"
        "Place this complete replacement DATA BIG in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "\n"
        "Keep the existing PR #574 ART BIG (do not replace ART):\n"
        "  _SPEC_ART_ONE.big\n"
        f"  SHA256={BASE_ART_SHA}\n"
        "\n"
        "Fixes:\n"
        "- B/C/D/H/I/J no longer reference unloaded rebuild Upgrades at spawn\n"
        "- B/C/D/H/I/J weapons now live in engine-loaded Weapon.ini\n"
        "- PR #574 missile stats and projectile artwork preserved\n"
        "- Al-Fahd500 / A unchanged\n"
        "- Does NOT include PR #575+ locomotor/alias experiments\n"
        "\n"
        "Static validation completed; runtime game test not performed.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_BCDHIJ_SPAWN_FIX.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
