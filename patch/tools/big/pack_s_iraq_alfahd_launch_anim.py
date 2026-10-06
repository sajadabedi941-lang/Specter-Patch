#!/usr/bin/env python3
"""Restore Al-Fahd500 9P117 raise/unpack animation lookup (DATA only).

Live DATA baseline: FIRE_FLAG / s-iraq-alfahd-9p117-freeze.
ART is not rebuilt. Keep the flag-text _SPEC_ART_ONE.big.

Root cause:
  ZH HRawAnimClass registers the clip as HierarchyName.AnimName
  (strcpy(Name, hier); strcat("."); strcat(anim)).
  Original 9P117 INI Irq_9P117.Irq_9P117 matches IRQ_9P117.IRQ_9P117.
  Al-Fahd INI used Irq_AlFahd500.IRQ_AF500, but the W3D clip is
  IRQ_AF500.IRQ_AF500, so Get_HAnim missed it and the ramp stayed packed.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD_FIRE_FLAG/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD_FLAG_TEXT/_SPEC_ART_ONE.big"
UNIT_SRC = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlFahd500.ini"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD_LAUNCH_ANIM"

BASE_DATA_SHA = "aed109b44177bcf6c03cff56b42106f985115404f0ace80811ae262e999b9cc0"
BASE_DATA_SIZE = 366368616
BASE_ART_SHA = "b242265f79404e0d07f2f1f52599becb0eb73e28a741e9b79f0ba67a6078bb34"
BASE_ART_SIZE = 1266477100

UNIT_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
WEAPON_INI_KEY = r"Data\INI\Weapon.ini"
PROJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"

LAUNCHER_W3D = r"Art\W3D\Irq_AlFahd500.W3D"
LAUNCHERD_W3D = r"Art\W3D\Irq_AlFahd500D.W3D"
ORIG_W3D = r"Art\W3D\Irq_9P117.W3D"
ORIGD_W3D = r"Art\W3D\Irq_9P117D.W3D"
PROJ_TEX = r"Art\Textures\Irq_AlFahd500P.tga"
FLAG_TEX = r"Art\Textures\IraqiFlag.dds"
GENERIC = r"Art\Textures\GENERIC-MISSILES.dds"


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


def to_crlf(data: bytes) -> bytes:
    text = data.decode("latin1").replace("\r\n", "\n").replace("\n", "\r\n")
    return text.encode("latin1")


def walk(blob: bytes):
    def rec(data: bytes, start: int, stop: int):
        p = start
        while p + 8 <= stop:
            cid, raw = struct.unpack_from("<II", data, p)
            sz = raw & 0x7FFFFFFF
            cont = bool(raw & 0x80000000)
            cs, ce = p + 8, p + 8 + sz
            if ce > stop:
                break
            yield cid, cont, cs, ce
            if cont:
                yield from rec(data, cs, ce)
            p = ce

    yield from rec(blob, 0, len(blob))


def anim_registered_name(blob: bytes) -> str | None:
    for cid, _c, cs, ce in walk(blob):
        if cid == 0x201 and ce - cs >= 36:
            name = blob[cs + 4 : cs + 20].split(b"\x00", 1)[0].decode("latin1")
            hier = blob[cs + 20 : cs + 36].split(b"\x00", 1)[0].decode("latin1")
            frames, rate = struct.unpack_from("<II", blob, cs + 36)
            return f"{hier}.{name} frames={frames} rate={rate}"
    return None


def commandset_block(text: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^CommandSet {re.escape(name)}\r?\n.*?^End", text)
    return m.group(0) if m else None


def slot_map(block: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


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


def validate(data: dict[str, bytes], src_data: dict[str, bytes], art: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    unit = data[UNIT_KEY].decode("latin1")
    r11 = data[R11_KEY].decode("latin1")

    if "Animation       = IRQ_AF500.IRQ_AF500" not in unit:
        fails.append("Al-Fahd missing IRQ_AF500.IRQ_AF500")
    if "Animation       = IRQ_AF500D.IRQ_AF500D" not in unit:
        fails.append("Al-Fahd missing IRQ_AF500D.IRQ_AF500D")
    if "Irq_AlFahd500.IRQ_AF500" in unit or "Irq_AlFahd500D.IRQ_AF500D" in unit:
        fails.append("Al-Fahd still uses filename.anim lookup")
    if unit.count("IRQ_AF500.IRQ_AF500") < 4:
        fails.append(f"too few IRQ_AF500.IRQ_AF500 refs {unit.count('IRQ_AF500.IRQ_AF500')}")
    if "ConditionState    = UNPACKING" not in unit:
        fails.append("UNPACKING state missing")
    if "UnpackTime = 6555" not in unit or "PackTime = 6555" not in unit:
        fails.append("unpack/pack time mismatch vs 9P117")
    if "ManualDeployAnimations = Yes" not in unit:
        fails.append("ManualDeployAnimations missing")
    if "DeployStyleAIUpdate" not in unit:
        fails.append("DeployStyleAIUpdate missing")
    if "Weapon = PRIMARY   Weapon_Iraq_AlFahd500" not in unit:
        fails.append("weapon retargeted")
    if "BuildCost       = 3000" not in unit:
        fails.append("cost changed")
    if "CommandSet    = Scud_B_CommandSet" not in unit:
        fails.append("commandset changed")

    if "Animation       = Irq_9P117.Irq_9P117" not in r11:
        fails.append("original 9P117 animation lost")
    if data[R11_KEY] != src_data[R11_KEY]:
        fails.append("9P117 INI mutated")
    if "Object Iraq_R11ScudB" not in r11:
        fails.append("Iraq_R11ScudB object lost")
    if "UnpackTime = 6555" not in r11:
        fails.append("9P117 UnpackTime changed")

    wep = data[WEAPON_INI_KEY]
    if wep != src_data[WEAPON_INI_KEY]:
        fails.append("Weapon.ini mutated")
    if b"Weapon Weapon_Iraq_AlFahd500" not in wep:
        fails.append("Al-Fahd weapon missing")
    if data[PROJ_KEY] != src_data[PROJ_KEY]:
        fails.append("projectile INI mutated")
    if data[FACTORY_KEY] != src_data[FACTORY_KEY]:
        fails.append("factory INI mutated")
    if data[r"Data\INI\CommandSet.ini"] != src_data[r"Data\INI\CommandSet.ini"]:
        fails.append("CommandSet.ini mutated")

    cs = data[r"Data\INI\CommandSet.ini"].decode("latin1")
    scud = commandset_block(cs, "Scud_B_CommandSet") or ""
    slots = slot_map(scud)
    if slots.get(1) != "Command_FireMainWeapon":
        fails.append("FireMainWeapon not slot 1")
    vt = commandset_block(cs, "Iraq_VT72BCommandSet") or ""
    if slot_map(vt).get(14) != "Command_ConstructIraq_AlFahdMissileFactory":
        fails.append("factory button lost")

    changed = sorted(k for k in set(data) | set(src_data) if data.get(k) != src_data.get(k))
    if changed != [UNIT_KEY]:
        fails.append(f"unexpected DATA changes {changed}")

    # ART frozen (read-only audit of the live flag-text ART).
    a9 = anim_registered_name(art[ORIG_W3D])
    aa = anim_registered_name(art[LAUNCHER_W3D])
    ad = anim_registered_name(art[LAUNCHERD_W3D])
    if a9 != "IRQ_9P117.IRQ_9P117 frames=200 rate=30":
        fails.append(f"original 9P117 anim {a9}")
    if aa != "IRQ_AF500.IRQ_AF500 frames=200 rate=30":
        fails.append(f"Al-Fahd anim {aa}")
    if ad != "IRQ_AF500D.IRQ_AF500D frames=200 rate=30":
        fails.append(f"Al-Fahd damaged anim {ad}")
    if FLAG_TEX not in art or GENERIC not in art:
        fails.append("flag/generic texture missing from live ART")
    if PROJ_TEX not in art:
        fails.append("Al-Fahd dedicated missile texture missing from live ART")
    else:
        tga = art[PROJ_TEX]
        if tga[16] != 32 or (tga[17] & 0x0F) != 8:
            fails.append("flag-text missile TGA profile lost")
    if b"IRQ_AF500" not in art[LAUNCHER_W3D] or b"IRQ_9P117" in art[LAUNCHER_W3D]:
        fails.append("Al-Fahd W3D identity contamination")
    if b"IRQ_9P117" not in art[ORIG_W3D]:
        fails.append("original 9P117 identity lost in live ART")
    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("live DATA baseline mismatch")
    if SRC_ART.stat().st_size != BASE_ART_SIZE or sha256_path(SRC_ART) != BASE_ART_SHA:
        raise SystemExit("live ART baseline mismatch (flag-text ART required)")

    src_data = parse_big(SRC_DATA.read_bytes())
    art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    data[UNIT_KEY] = to_crlf(UNIT_SRC.read_bytes())

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    extracted = parse_big(packed)
    fails = validate(extracted, src_data, art)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))

    data_sha = sha256_path(out_data)
    report = [
        "# Iraq_AlFahd500 launch-prep animation restore",
        "",
        "DATA-only. Keep flag-text _SPEC_ART_ONE.big.",
        "",
        "## Audit",
        "Original object Iraq_R11ScudB uses Irq_9P117.W3D clip IRQ_9P117.IRQ_9P117",
        "(200 frames @ 30 fps) on UNPACKING / PACKING / DEPLOYED via DeployStyleAIUpdate",
        "UnpackTime=6555. Al-Fahd cloned that Draw/AI but looked up Irq_AlFahd500.IRQ_AF500.",
        "ZH registers the clip as IRQ_AF500.IRQ_AF500, so the raise never played.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART unchanged SHA256: {BASE_ART_SHA}",
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
        "## VALIDATION PASS (static)",
        "- Al-Fahd Animation now IRQ_AF500.IRQ_AF500 / IRQ_AF500D.IRQ_AF500D",
        "- Matches W3D HRawAnim registration HierarchyName.AnimName",
        "- UNPACKING/PACKING/DEPLOYED + UnpackTime=6555 identical to Iraq_R11ScudB",
        "- Weapon/projectile/factory/commandsets/9P117 INI unchanged",
        "- Live ART still has 200-frame raise clip + Iraqi flag / AL-FAHD500 skin",
        "",
        "RUNTIME_TEST=NOT RUN",
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
        f"ART_FILE=_SPEC_ART_ONE.big (keep s-iraq-alfahd-flag-text)\n"
        f"ART_SHA256={BASE_ART_SHA}\n"
        "OBJECT_ORIGINAL=Iraq_R11ScudB\n"
        "OBJECT_ALFAHD=Iraq_AlFahd500\n"
        "ANIM_ORIGINAL=Irq_9P117.Irq_9P117 (W3D IRQ_9P117.IRQ_9P117, 200 frames @ 30)\n"
        "ANIM_ALFAHD=IRQ_AF500.IRQ_AF500 (same 200-frame raise clip, dedicated identity)\n"
        "UNPACK_TIME=6555 (matches original 9P117)\n"
        "ROOT_CAUSE=INI looked up Irq_AlFahd500.IRQ_AF500; engine hash is IRQ_AF500.IRQ_AF500\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Iraq Al-Fahd 500 launch-prep animation restore\n"
        "DATA-only complete replacement. Place in the game folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "Keep the flag-text ART file (_SPEC_ART_ONE.big from s-iraq-alfahd-flag-text).\n"
        "Al-Fahd now plays IRQ_AF500.IRQ_AF500 (the cloned 9P117 raise clip) on unpack.\n"
        "Iraqi flag + AL-FAHD500 skin are unchanged.\n"
        "Do not use a partial INI patch.\n",
        encoding="utf-8",
    )
    print("\n".join(report))
    print("PACK OK", data_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
