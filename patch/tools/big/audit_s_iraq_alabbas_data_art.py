#!/usr/bin/env python3
"""Re-audit the current Al-Abbas DATA + baseline ART pair. Does not rebuild."""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

ROOT = Path("/workspace")
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_DATA_ART"
DATA_BIG = OUT / "_SPEC_DATA_ONE.big"
ART_BIG = OUT / "_SPEC_ART_ONE.big"
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_BUILDTIME/_SPEC_DATA_ONE.big"
SRC_ART_A = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_DATA_BCDHIJ/_SPEC_ART_ONE.big"
SRC_ART_B = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_SKINS_BCDHIJ/_SPEC_ART_ONE.big"

EXPECTED_DATA_SHA = "d57a6f7451c0032ab774ce352d736715ddea1b20ae6176393a1967bbc659c30c"
EXPECTED_DATA_SIZE = 366473321
EXPECTED_ART_SHA = "e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4"
EXPECTED_ART_SIZE = 1292294758
EXPECTED_DATA_FILES = 2930
EXPECTED_ART_FILES = 4628

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
UPG_KEY = r"Data\INI\Upgrade_IraqFactoryMissiles.ini"
UNIT_D_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini"
PROJ_D_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlAbbas_Projectile.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"

REQUIRED_ART = [
    r"Art\W3D\Irq_AlAbbas2M.W3D",
    r"Art\W3D\Irq_AlFahd500.W3D",
    r"Art\W3D\Irq_AlFahd500D.W3D",
    r"Art\W3D\Irq_9P117.W3D",
    r"Art\W3D\Irq_9P117D.W3D",
    r"Art\W3D\Irq_AlHussein2M.W3D",
    r"Art\W3D\Irq_AlSamoud2M.W3D",
    r"Art\W3D\Irq_AlBasrahM.W3D",
    r"Art\W3D\Irq_AlNasirM.W3D",
    r"Art\W3D\Irq_AlMansourM.W3D",
    r"Art\Textures\Irq_AlAbbas2P.tga",
    r"Art\Textures\Irq_AlFahd500P.tga",
    r"Art\Textures\Irq_9P117.dds",
    r"Art\Textures\specter_missile_a.tga",
    r"Art\Textures\specter_missile_d.tga",
    r"Art\Textures\Irq_AlHussein2P.tga",
    r"Art\Textures\Irq_AlSamoud2P.tga",
    r"Art\Textures\Irq_AlBasrahP.tga",
    r"Art\Textures\Irq_AlNasirP.tga",
    r"Art\Textures\Irq_AlMansourP.tga",
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
    weapon_dir = [
        k
        for k in data
        if k.replace("/", "\\").lower().startswith(r"data\ini\weapon" + "\\") and k.lower().endswith(".ini")
    ]
    for k in sorted(weapon_dir, key=lambda x: x.lower()):
        t = data[k].decode("utf-8")
        b = command_block(t, "Weapon", name)
        if b:
            blocks.append((k, b))
    return blocks[-1] if blocks else None


def main() -> int:
    fails: list[str] = []
    if not DATA_BIG.is_file() or not ART_BIG.is_file():
        raise SystemExit("combined BIG pair missing")

    data_size = DATA_BIG.stat().st_size
    art_size = ART_BIG.stat().st_size
    data_sha = sha256_path(DATA_BIG)
    art_sha = sha256_path(ART_BIG)

    if data_size != EXPECTED_DATA_SIZE or data_sha != EXPECTED_DATA_SHA:
        fails.append(f"DATA identity drift size={data_size} sha={data_sha}")
    if art_size != EXPECTED_ART_SIZE or art_sha != EXPECTED_ART_SHA:
        fails.append(f"ART identity drift size={art_size} sha={art_sha}")
    if SRC_DATA.is_file() and sha256_path(SRC_DATA) != data_sha:
        fails.append("DATA is not the live Al-Abbas BuildTime package")
    for src_art in (SRC_ART_A, SRC_ART_B):
        if src_art.is_file() and sha256_path(src_art) != art_sha:
            fails.append(f"ART is not the current baseline {src_art}")

    data_blob = DATA_BIG.read_bytes()
    art_blob = ART_BIG.read_bytes()
    if data_blob[:4] != b"BIGF":
        fails.append("DATA not BIGF")
    if art_blob[:4] != b"BIGF":
        fails.append("ART not BIGF")
    fails.extend(f"DATA {x}" for x in big_structure_ok(data_blob))
    fails.extend(f"ART {x}" for x in big_structure_ok(art_blob))

    extracted = parse_big(data_blob)
    art_files = parse_big(art_blob)
    if len(extracted) != EXPECTED_DATA_FILES:
        fails.append(f"DATA file count {len(extracted)}")
    if len(art_files) != EXPECTED_ART_FILES:
        fails.append(f"ART file count {len(art_files)} — content may have been removed")

    n = len(
        re.findall(
            rb"^Object Iraq_AlAbbas\s*$",
            b"".join(v for k, v in extracted.items() if k.lower().endswith(".ini")),
            re.M,
        )
    )
    if n != 1:
        fails.append(f"Iraq_AlAbbas definition count {n}")

    unit = extracted[UNIT_D_KEY].decode("utf-8")
    if "BuildTime       = 30.0" not in unit:
        fails.append("BuildTime not 30.0")
    if "BuildTime       = 35.0" in unit:
        fails.append("old production BuildTime 35.0 still present")
    if "BuildCost       = 2600" not in unit:
        fails.append("price changed")
    if "CommandSet    = Iraq_AlAbbas_TELCommandSet" not in unit:
        fails.append("commandset")
    if "Weapon = PRIMARY   Weapon_Iraq_AlAbbas" not in unit:
        fails.append("weapon")
    if "ReplaceObject = Iraq_AlAbbas" not in unit or "TriggeredBy   = Upgrade_Iraq_AlAbbas_Rebuild" not in unit:
        fails.append("rebuild ReplaceObjectUpgrade")

    upg = command_block(extracted[UPG_KEY].decode("utf-8"), "Upgrade", "Upgrade_Iraq_AlAbbas_Rebuild") or ""
    if "BuildCost        = 1300" not in upg or "BuildTime        = 35.0" not in upg:
        fails.append("rebuild upgrade cost/time changed")

    wep = last_weapon_block(extracted, "Weapon_Iraq_AlAbbas")
    if not wep:
        fails.append("weapon missing")
    else:
        if "AutoReloadsClip             = No" not in wep[1] or "ClipSize                    = 1" not in wep[1]:
            fails.append("clip/rebuild weapon flags")

    fire = command_block(extracted[CB_KEY].decode("latin1"), "CommandButton", "Command_FireMainWeapon") or ""
    if "Command           = FIRE_WEAPON" not in fire or "WeaponSlot        = PRIMARY" not in fire:
        fails.append("Fire CommandButton")
    if "NEED_SPECIAL_POWER_SCIENCE" in fire or re.search(r"^\s*Science\s*=", fire, re.M):
        fails.append("Fire still science-gated")
    if "Upgrade" in fire:
        fails.append("Fire has Upgrade field")

    tel = command_block(extracted[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlAbbas_TELCommandSet") or ""
    slots = slot_map(tel)
    if slots.get(1) != "Command_FireMainWeapon" or slots.get(2) != "CB_Iraq_AlAbbas_Rebuild":
        fails.append(f"TEL CommandSet {slots}")

    r11 = extracted[R11_KEY].decode("utf-8", errors="replace")
    if "Object Iraq_R11ScudB" not in r11:
        fails.append("MOTHER object missing")
    if "BuildTime       = 17.0" not in r11:
        fails.append("MOTHER BuildTime changed")
    if "CommandSet    = Scud_B_CommandSet" not in r11:
        fails.append("MOTHER CommandSet changed")
    if SRC_DATA.is_file():
        src = parse_big(SRC_DATA.read_bytes())
        if extracted[R11_KEY] != src[R11_KEY]:
            fails.append("MOTHER 9P117 mutated vs live DATA")
        if extracted[UNIT_D_KEY] != src[UNIT_D_KEY]:
            fails.append("Al-Abbas unit mutated vs live DATA")

    missing_art = [k for k in REQUIRED_ART if k not in art_files]
    if missing_art:
        fails.append(f"required ART missing {missing_art}")

    stage = OUT / "LAST_WINS_EXTRACT"
    if stage.exists():
        for leftover in stage.rglob("*"):
            if leftover.is_file() and leftover.suffix.lower() in {".w3d", ".tga", ".dds", ".big"}:
                leftover.unlink()
    (stage / "DATA").mkdir(parents=True, exist_ok=True)
    (stage / "ART").mkdir(parents=True, exist_ok=True)
    for rel in [UNIT_D_KEY, UPG_KEY, R11_KEY, PROJ_D_KEY]:
        if rel in extracted:
            p = stage / "DATA" / rel.replace("\\", "/")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(extracted[rel])
    (stage / "ART" / "ART_FILELIST.txt").write_text(
        f"ART_FILES={len(art_files)}\n" + "\n".join(sorted(art_files, key=str.lower)) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Combined DATA+ART release audit",
        "",
        f"DATA size: {data_size}",
        f"DATA SHA256: {data_sha}",
        f"DATA files: {len(extracted)}",
        f"ART size: {art_size}",
        f"ART SHA256: {art_sha}",
        f"ART files: {len(art_files)}",
        "ART rebuilt: NO (identity copy of current baseline ART BIG)",
        "",
        "Al-Abbas Object Iraq_AlAbbas BuildTime=30.0",
        "Fire Command_FireMainWeapon no Science/Upgrade",
        "Rebuild $1300 / 35.0s preserved",
        "MOTHER 9P117 unchanged",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        report.append("")
        report.append("RUNTIME TEST: NOT PERFORMED")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static)",
        "- both BIGs are complete replacement packages",
        "- DATA is the current Al-Abbas 30s package",
        "- ART is the current dedicated-skin baseline (4628 files), not rebuilt",
        "- required missile/9P117/Al-Fahd/cameo ART present",
        "- Fire available from the start; rebuild mechanic unchanged",
        "- MOTHER / 9P117 unchanged",
        "",
        "RUNTIME TEST: NOT PERFORMED",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=NO (current Al-Abbas 30s DATA reused)\n"
        "ART_CHANGED=NO (current baseline ART reused, not rebuilt)\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={data_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted)}\n"
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={art_size}\n"
        f"ART_SHA256={art_sha}\n"
        f"ART_FILES={len(art_files)}\n"
        "OBJECT=Iraq_AlAbbas\n"
        "BUILDTIME=30.0\n"
        "FIRE=Command_FireMainWeapon unlocked\n"
        "MOTHER_UNCHANGED=YES\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT PERFORMED\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER current DATA + ART pair\n"
        "Place BOTH complete replacement files in the game folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "  _SPEC_ART_ONE.big\n"
        "DATA includes Iraq_AlAbbas BuildTime 30.0. ART is the current baseline skins package.\n",
        encoding="utf-8",
    )
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
