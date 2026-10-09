#!/usr/bin/env python3
"""Isolated lever 1: unique CommandSet on Iraq_AlFahd500 only.

Spawn-crash evidence (packed last-wins):

  PR #594  Scud_B_CommandSet + RiderChangeContain + InitialPayload
           + weapon FireOCL/AutoReloadsClip=No  -> CTD at spawn
  PR #595  same riders + GARRISONABLE            -> CTD at spawn
  PR #597  NO riders; unique CS + PLAYER_UPGRADE WeaponSet
           + WeaponSetUpgrade TriggeredBy + FireOCL/AutoNo -> CTD at spawn

Shared crash ingredients were riders (#594/#595) or TriggeredBy/PLAYER_UPGRADE
(#597), plus FireOCL/AutoNo on the weapon in both families. Unique CommandSet
was NOT in #594 (still crashed), so it is not sufficient to explain #594.

This experiment changes ONE spawn-time object field:

  CommandSet = Iraq_AlFahd500CommandSet
    (already in PR #599 DATA: FireMainWeapon + Command_Rearm_Iraq_AlFahd500
     $1100 + Scud switch / move / guard / stop)

Not changed: KindOf, riders, WeaponSet, WeaponSetUpgrade, weapon, FireOCL,
B-J, country TELs, MOTHER/9P117, factory production button, ART.

This does NOT complete paid rearm. Clip still auto-reloads (ClipReloadTime
95000). The $1100 button can be clicked if spawn succeeds; nothing restores
or strips clip. Next lever only after in-game spawn is confirmed.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MAGENTA_WAVES/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MAGENTA_WAVES/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD500_CMDSET"

SHA_DATA_599 = "ec066f71382d3d1d732d4a9cdde54ffee86258eb0362aa0c8087155bc5e7f4d8"
SIZE_DATA_599 = 366615017
SHA_ART_599 = "9c1dc445c17b024f8a4c1c55e699371a94d4991d1dff1eb377f3976a6c54545e"
SIZE_ART_599 = 1295713019

OBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
FAC_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
W_A_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlFahd500.ini"
ABBAS_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini"

OTHER_FACTORY = [
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHusseinII.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlSamoudII.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlBasrah.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNasir.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlMansour.ini",
]

NEW_SET = "Iraq_AlFahd500CommandSet"
OLD_SET = "Scud_B_CommandSet"


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
        raise SystemExit("not BIGF")
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
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def decode(blob: bytes) -> str:
    return blob.decode("latin1").replace("\r\n", "\n")


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def object_body(text: str, name: str) -> str | None:
    found = [(m.group(1), m.start()) for m in re.finditer(r"^Object\s+(\S+)\s*$", text, re.M)]
    for i, (n, start) in enumerate(found):
        if n == name:
            end = found[i + 1][1] if i + 1 < len(found) else len(text)
            return text[start:end]
    return None


def field(body: str | None, key: str) -> str:
    if not body:
        return ""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", body, re.M)
    return m.group(1).strip() if m else ""


def last_block(kind: str, name: str, text: str) -> str | None:
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text))
    return matches[-1].group(0) if matches else None


def patch_object(text: str) -> str:
    body = object_body(text, "Iraq_AlFahd500")
    if not body:
        raise SystemExit("Iraq_AlFahd500 missing")
    if field(body, "CommandSet") != OLD_SET:
        raise SystemExit(f"expected {OLD_SET}, got {field(body, 'CommandSet')}")
    new_body = re.sub(
        rf"^(\s*CommandSet\s*=\s*){re.escape(OLD_SET)}\s*$",
        rf"\1{NEW_SET}",
        body,
        count=1,
        flags=re.M,
    )
    if new_body == body:
        raise SystemExit("CommandSet replace failed")
    return text[: text.find(body)] + new_body + text[text.find(body) + len(body) :]


def validate(data: dict[str, bytes], baseline: dict[str, bytes]) -> list[str]:
    fails = []
    changed = sorted(k for k in data if baseline.get(k) != data.get(k))
    if changed != [OBJ_KEY]:
        fails.append(f"changed paths {changed} (expected only {OBJ_KEY})")
    body = object_body(decode(data[OBJ_KEY]), "Iraq_AlFahd500")
    base = object_body(decode(baseline[OBJ_KEY]), "Iraq_AlFahd500")
    if field(body, "CommandSet") != NEW_SET:
        fails.append(f"CommandSet {field(body, 'CommandSet')}")
    if field(body, "KindOf") != field(base, "KindOf"):
        fails.append("KindOf mutated")
    if "RiderChangeContain" in (body or "") or "InitialPayload" in (body or ""):
        fails.append("riders present")
    if "PLAYER_UPGRADE" in (body or "") or "TriggeredBy" in (body or ""):
        fails.append("597 WeaponSetUpgrade levers present")
    if field(body, "BuildCost") != "2200":
        fails.append("BuildCost mutated")
    cs = decode(data[CS_KEY])
    cb = decode(data[CB_KEY])
    telset = last_block("CommandSet", NEW_SET, cs) or ""
    for btn in [
        "Command_FireMainWeapon",
        "Command_Rearm_Iraq_AlFahd500",
        "Command_ScudSwitchToHE",
        "Command_AttackMove",
        "Command_Guard",
        "Command_Stop",
    ]:
        if btn not in telset:
            fails.append(f"unique set missing {btn}")
        if not re.search(rf"^CommandButton {re.escape(btn)}\s*$", cb, re.M):
            fails.append(f"missing CommandButton {btn}")
    btn_a = last_block("CommandButton", "CB_MISSILE_A", cb) or ""
    if "Object        = Iraq_AlFahd500" not in btn_a and "Object = Iraq_AlFahd500" not in btn_a:
        fails.append("CB_MISSILE_A no longer builds Iraq_AlFahd500")
    fac = object_body(decode(data[FAC_KEY]), "Iraq_AlFahdMissileFactory")
    if field(fac, "CommandSet") != "Iraq_AlFahdMissileFactoryCommandSet":
        fails.append("factory CommandSet mutated")
    r11 = object_body(decode(data[R11_KEY]), "Iraq_R11ScudB")
    if field(r11, "CommandSet") != OLD_SET:
        fails.append("MOTHER CommandSet mutated")
    if data[R11_KEY] != baseline[R11_KEY]:
        fails.append("9P117 file mutated")
    if data[W_A_KEY] != baseline[W_A_KEY]:
        fails.append("Weapon_Iraq_AlFahd500 mutated")
    if data[CS_KEY] != baseline[CS_KEY]:
        fails.append("CommandSet.ini mutated")
    if data[ABBAS_KEY] != baseline[ABBAS_KEY]:
        fails.append("Iraq_Alhussaien file mutated")
    for key in OTHER_FACTORY:
        if data[key] != baseline[key]:
            fails.append(f"factory sibling mutated: {key}")
    lows = {}
    for m in re.finditer(r"^CommandSet (\S+)", cs, re.M):
        lows.setdefault(m.group(1).lower(), []).append(m.group(1))
    for names in lows.values():
        if len(names) > 1:
            fails.append(f"duplicate CommandSet {names}")
    return fails


def main() -> int:
    if sha256_path(SRC_DATA) != SHA_DATA_599 or SRC_DATA.stat().st_size != SIZE_DATA_599:
        raise SystemExit("PR #599 DATA mismatch")
    if sha256_path(SRC_ART) != SHA_ART_599 or SRC_ART.stat().st_size != SIZE_ART_599:
        raise SystemExit("PR #599 ART mismatch")

    baseline = parse_big(SRC_DATA.read_bytes())
    data = dict(baseline)
    data[OBJ_KEY] = to_crlf(patch_object(decode(data[OBJ_KEY])))
    mapped = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlFahd500.ini"
    if mapped.exists():
        mapped.write_bytes(data[OBJ_KEY])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    shutil.copy2(SRC_ART, OUT / "_SPEC_ART_ONE.big")
    extracted = parse_big(out_data.read_bytes())
    fails = validate(extracted, baseline)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    if sha256_path(OUT / "_SPEC_ART_ONE.big") != SHA_ART_599:
        fails.append("ART copy not byte-identical to PR #599")

    data_sha = sha256_path(out_data)
    changed = sorted(k for k in extracted if baseline.get(k) != extracted.get(k))
    report = [
        "# SPECTER isolated lever 1: Iraq_AlFahd500 unique CommandSet",
        "",
        "ONE spawn-time object field: CommandSet Scud_B -> Iraq_AlFahd500CommandSet.",
        "No riders, no GARRISONABLE, no PLAYER_UPGRADE, no TriggeredBy, no FireOCL.",
        "Factory CB_MISSILE_A still UNIT_BUILDs Iraq_AlFahd500. MOTHER keeps Scud_B.",
        "Paid rearm LOOP is NOT complete. Clip still auto-reloads in 95s.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART size: {SIZE_ART_599}",
        f"- ART SHA256: {SHA_ART_599}",
        f"- Changed vs PR #599: {', '.join(changed)}",
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
        "- Only Iraq_AlFahd500.ini changed; B-J, 9P117, Alhussaien, weapons, CommandSet.ini unchanged",
        "- Unique set buttons resolve; no duplicate CommandSet names",
        "- CB_MISSILE_A still builds Iraq_AlFahd500",
        "- ART byte-identical to PR #599",
        "",
        "Static validation completed; runtime game test not performed.",
        "Spawn CTD is NOT claimed fixed. Unresolved: produce A in Zero Hour.",
        "Do not add TriggeredBy/FireOCL/riders until this lever is spawn-safe in-game.",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=NO\n"
        "LEVER=CommandSet only (Iraq_AlFahd500 -> Iraq_AlFahd500CommandSet)\n"
        "PAID_REARM_LOOP_COMPLETE=NO\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted)}\n"
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={SIZE_ART_599}\n"
        f"ART_SHA256={SHA_ART_599}\n"
        "ART_BYTE_IDENTICAL_TO_PR599=YES\n"
        f"CHANGED_VS_599={', '.join(changed)}\n"
        "BASELINE=PR #599\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n"
        "SPAWN_CTD_CLAIMED_FIXED=NO\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Iraq_AlFahd500 isolated CommandSet lever\n"
        "\n"
        "Missile A uses Iraq_AlFahd500CommandSet (includes $1100 rearm button).\n"
        "No riders / WeaponSetUpgrade TriggeredBy / FireOCL. Clip still auto-reloads.\n"
        "Place both BIGs in the SPECTER folder. Runtime spawn test not performed.\n"
        "Paid rearm LOOP is NOT complete. Do not treat the $1100 button as a clip restore.\n",
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "\n".join(
            [
                "# Isolated lever 1: unique CommandSet on Iraq_AlFahd500",
                "",
                "Preserves PR #599 baseline. One packed path changed:",
                "`Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlFahd500.ini`",
                "CommandSet `Scud_B_CommandSet` -> existing leftover `Iraq_AlFahd500CommandSet`.",
                "",
                "## Packed last-wins inspected (PR #599 DATA)",
                "",
                "- Factory `Iraq_AlFahdMissileFactoryCommandSet` slot 1 = `CB_MISSILE_A` UNIT_BUILD Object=`Iraq_AlFahd500`.",
                "- `Iraq_AlFahd500`: KindOf vehicle (no GARRISONABLE), WeaponSet Conditions=None, Weapon=`Weapon_Iraq_AlFahd500`, empty `WeaponSetUpgrade ModuleTag_09h56u56j` (no TriggeredBy), ProductionUpdate, CommandSet was `Scud_B_CommandSet`, BuildCost=2200.",
                "- `Weapon_Iraq_AlFahd500`: ClipSize=1, ClipReloadTime=95000, no FireOCL, AutoReloadsClip omitted (default Yes).",
                "- `Iraq_Alhussaien`: GARRISONABLE_UNTIL_DESTROYED + RiderChangeContain + InitialPayload rider2 + ObjectCreationUpgrade TriggeredBy=`Upgrade_Rearm_Iraq_Alhussaien` + unique armed/unarmed CommandSets. That machine is not copied.",
                "- Leftover (unreferenced by AlFahd500 body): `Iraq_AlFahd500CommandSet` (FireMainWeapon + Command_Rearm_Iraq_AlFahd500 + Scud switches), `Command_Rearm_Iraq_AlFahd500` OBJECT_UPGRADE, `Upgrade_Rearm_Iraq_AlFahd500` Type=OBJECT BuildCost=1100, `Iraq_AlFahd500_UnarmedRearmSet`, `RearmStrip_Iraq_AlFahd500`.",
                "- `Scud_B_CommandSet` unchanged; MOTHER `Iraq_R11ScudB` still uses it.",
                "",
                "## Spawn-CTD split (#594-#597)",
                "",
                "- #594/#595: RiderChangeContain + InitialPayload (+ GARRISONABLE in #595) + weapon FireOCL/AutoReloadsClip=No. Unique CS was NOT required for #594 (kept Scud_B, still CTD).",
                "- #596: startup CTD from duplicate `Iraq_AlAbbasCommandSet` (building vs TEL).",
                "- #597: no riders; PLAYER_UPGRADE WeaponSet + unique CS + WeaponSetUpgrade TriggeredBy + FireOCL OCL_Rearm_* + AutoReloadsClip=No on A/D. Spawn still CTD.",
                "- Shared crash ingredients: riders or TriggeredBy/PLAYER_UPGRADE plus FireOCL/AutoNo. Isolated unique CS was never tested.",
                "",
                "## This lever",
                "",
                "Assign the leftover unique CommandSet only. No KindOf, rider, WeaponSet, TriggeredBy, FireOCL, or weapon edits. B-J / country TELs / MOTHER / factory button unchanged.",
                "",
                "Paid rearm is NOT complete: clip still auto-reloads in 95s. The leftover $1100 OBJECT_UPGRADE button can charge money with no clip restore because no module listens to `Upgrade_Rearm_Iraq_AlFahd500`.",
                "",
                "Static validation is not runtime safety. Game executable is not in this environment.",
                "",
                "Do not proceed to missile B. Do not add TriggeredBy/FireOCL/riders until this lever is spawn-safe in Zero Hour.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD500_CMDSET.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
