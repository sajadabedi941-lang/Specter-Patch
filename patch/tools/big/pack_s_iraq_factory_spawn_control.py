#!/usr/bin/env python3
"""Control build: restore PR #593 spawn-safe factory A-J; keep AlAbbas name fix.

Packed last-wins 593 vs 597 for factory A-J (complete object compare):
  KindOf / Draw / Body / Locomotor / Geometry / module tags: identical
  ONLY rearm add-ons differ:
    WeaponSet Conditions=PLAYER_UPGRADE
    CommandSet unique instead of Scud_B_CommandSet
    WeaponSetUpgrade TriggeredBy Upgrade_Rearm_*
    Weapon FireOCL OCL_Rearm_* and AutoReloadsClip=No (A/D)

PR #594/#595 contain/riders crashed spawn.
PR #596/#597 removed contain but kept those rearm add-ons; spawn still crashes.

This packer restores factory object bodies AND weapon blocks from PR #593.
Iraq_AlAbbasTELCommandSet remains defined so the building CommandSet is not
overwritten. Factory TELs use Scud_B_CommandSet again. Country TEL rearm
(Alabaas rider path) is unchanged. ART is PR #593.

Factory half-price rearm is NOT reintroduced until this control is spawn-safe
in Zero Hour.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_597 = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_COMMANDSET/_SPEC_DATA_ONE.big"
SRC_593 = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_TOP_MARKINGS/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_TOP_MARKINGS/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_SPAWN_CONTROL"

SHA_597 = "238d63e6cbe9e09a7b02d4b864fe3c9333fbf08d536460592a1cb4663579ea17"
SIZE_597 = 366616568
SHA_593 = "6af19c95f508a80752e26fd603d2745b5c2c51d446890a3f373816d329033f27"
SIZE_593 = 366515208
SHA_ART = "95a0737f7f6e7d0f15a2a1234b222d1cf9643d1199b00e28e7e87e7c89083ed4"
SIZE_ART = 1294467676

CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
WEAPON_A_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlFahd500.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
ABBAS_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini"
BLD_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_Abbas.ini"

FACTORY = [
    {"object": "Iraq_AlFahd500", "weapon": "Weapon_Iraq_AlFahd500",
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini", "wkey": WEAPON_A_KEY},
    {"object": "Iraq_AlHusseinII", "weapon": "Weapon_Iraq_AlHusseinII",
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlHusseinII.ini", "wkey": WEAPON_KEY},
    {"object": "Iraq_AlSamoudII", "weapon": "Weapon_Iraq_AlSamoudII",
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlSamoudII.ini", "wkey": WEAPON_KEY},
    {"object": "Iraq_AlAbbas", "weapon": "Weapon_Iraq_AlAbbas",
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini", "wkey": WEAPON_KEY},
    {"object": "Iraq_AlBasrah", "weapon": "Weapon_Iraq_AlBasrah",
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlBasrah.ini", "wkey": WEAPON_KEY},
    {"object": "Iraq_AlNasir", "weapon": "Weapon_Iraq_AlNasir",
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlNasir.ini", "wkey": WEAPON_KEY},
    {"object": "Iraq_AlMansour", "weapon": "Weapon_Iraq_AlMansour",
     "ini": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlMansour.ini", "wkey": WEAPON_KEY},
]

KIND_593 = "PRELOAD SELECTABLE CAN_ATTACK CAN_CAST_REFLECTIONS VEHICLE SCORE"


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


def replace_weapon_block(host: str, name: str, new_block: str) -> str:
    matches = list(re.finditer(rf"(?ms)^Weapon {re.escape(name)}\r?\n.*?^End", host))
    if not matches:
        raise SystemExit(f"weapon missing in host: {name}")
    last = matches[-1]
    return host[: last.start()] + new_block + host[last.end() :]


def cmdset_blocks(text: str, name: str) -> list[str]:
    return [m.group(0) for m in re.finditer(rf"(?ms)^CommandSet {re.escape(name)}\n.*?^End", text)]


def validate(data: dict[str, bytes], d593: dict[str, bytes], d597: dict[str, bytes]) -> list[str]:
    fails = []
    cs = decode(data[CS_KEY])
    cs593 = decode(d593[CS_KEY])
    bld_sets = cmdset_blocks(cs, "Iraq_AlAbbasCommandSet")
    if len(bld_sets) != 1:
        fails.append(f"Iraq_AlAbbasCommandSet count {len(bld_sets)}")
    else:
        orig = cmdset_blocks(cs593, "Iraq_AlAbbasCommandSet")[-1]
        if bld_sets[0].replace("\r", "") != orig.replace("\r", ""):
            fails.append("building Iraq_AlAbbasCommandSet != PR #593")
    if "CommandSet Iraq_AlAbbasTELCommandSet" not in cs:
        fails.append("Iraq_AlAbbasTELCommandSet unique-name reservation missing")
    lows = {}
    for m in re.finditer(r"^CommandSet (\S+)", cs, re.M):
        lows.setdefault(m.group(1).lower(), []).append(m.group(1))
    for low, names in lows.items():
        if len(names) > 1:
            fails.append(f"duplicate CommandSet {names}")
    bld = object_body(decode(data[BLD_KEY]), "Iraq_Abbas")
    if field(bld, "CommandSet") != "Iraq_AlAbbasCommandSet":
        fails.append(f"building CommandSet {field(bld,'CommandSet')}")
    if decode(data[R11_KEY]) != decode(d593[R11_KEY]):
        fails.append("9P117 mutated")
    abbas = object_body(decode(data[ABBAS_KEY]), "Iraq_Alhussaien")
    if "RiderChangeContain" not in (abbas or ""):
        fails.append("Iraq_Alhussaien rider path lost")
    for spec in FACTORY:
        body = object_body(decode(data[spec["ini"]]), spec["object"])
        b593 = object_body(decode(d593[spec["ini"]]), spec["object"])
        if body != b593:
            fails.append(f"{spec['object']} object body != PR #593")
            continue
        if field(body, "CommandSet") != "Scud_B_CommandSet":
            fails.append(f"{spec['object']} CommandSet {field(body,'CommandSet')}")
        if field(body, "KindOf") != KIND_593:
            fails.append(f"{spec['object']} KindOf changed")
        if "PLAYER_UPGRADE" in body or "TriggeredBy" in body:
            fails.append(f"{spec['object']} still has rearm object add-ons")
        if "RiderChangeContain" in body or "InitialPayload" in body:
            fails.append(f"{spec['object']} contain stack present")
        wkey = spec["wkey"]
        wtext = decode(data[wkey])
        w = last_block("Weapon", spec["weapon"], wtext)
        if wkey == WEAPON_A_KEY and not w:
            w = last_block("Weapon", spec["weapon"], decode(data[WEAPON_KEY]))
        orig_w = last_block("Weapon", spec["weapon"], decode(d593[wkey]))
        if spec["wkey"] == WEAPON_A_KEY and not orig_w:
            orig_w = last_block("Weapon", spec["weapon"], decode(d593[WEAPON_KEY]))
        if (w or "").replace("\r", "") != (orig_w or "").replace("\r", ""):
            fails.append(f"{spec['weapon']} != PR #593")
        if w and ("OCL_Rearm_" in w or "OCL_HussienMissileDisarm" in w):
            fails.append(f"{spec['weapon']} still has rearm FireOCL")
    return fails


def main() -> int:
    if sha256_path(SRC_597) != SHA_597 or SRC_597.stat().st_size != SIZE_597:
        raise SystemExit("PR #597 DATA mismatch")
    if sha256_path(SRC_593) != SHA_593 or SRC_593.stat().st_size != SIZE_593:
        raise SystemExit("PR #593 DATA mismatch")
    if sha256_path(SRC_ART) != SHA_ART or SRC_ART.stat().st_size != SIZE_ART:
        raise SystemExit("PR #593 ART mismatch")

    d597 = parse_big(SRC_597.read_bytes())
    d593 = parse_big(SRC_593.read_bytes())
    data = dict(d597)

    for spec in FACTORY:
        data[spec["ini"]] = d593[spec["ini"]]
        mapped = ROOT / "patch" / spec["ini"].replace("\\", "/")
        if mapped.exists():
            mapped.write_bytes(data[spec["ini"]])

    # Restore factory weapon blocks from PR #593.
    w597 = decode(data[WEAPON_KEY])
    w593 = decode(d593[WEAPON_KEY])
    for spec in FACTORY:
        if spec["wkey"] != WEAPON_KEY:
            continue
        orig = last_block("Weapon", spec["weapon"], w593)
        if not orig:
            raise SystemExit(f"593 missing {spec['weapon']}")
        w597 = replace_weapon_block(w597, spec["weapon"], orig)
    data[WEAPON_KEY] = to_crlf(w597)
    data[WEAPON_A_KEY] = d593[WEAPON_A_KEY]
    src_a = ROOT / "patch/Data/INI/Weapon/Weapon_Iraq_AlFahd500.ini"
    if src_a.exists():
        src_a.write_bytes(data[WEAPON_A_KEY])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    shutil.copy2(SRC_ART, OUT / "_SPEC_ART_ONE.big")
    extracted = parse_big(out_data.read_bytes())
    fails = validate(extracted, d593, d597)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    if sha256_path(OUT / "_SPEC_ART_ONE.big") != SHA_ART:
        fails.append("ART copy not byte-identical")

    changed_vs_597 = sorted(k for k in extracted if d597.get(k) != extracted.get(k))
    changed_vs_593 = sorted(k for k in extracted if d593.get(k) != extracted.get(k))
    data_sha = sha256_path(out_data)
    report = [
        "# SPECTER factory A-J spawn-safe CONTROL (rearm stripped)",
        "",
        "593 vs 597 factory object diffs were ONLY rearm add-ons:",
        "  PLAYER_UPGRADE WeaponSet, unique CommandSet, WeaponSetUpgrade TriggeredBy,",
        "  FireOCL OCL_Rearm_*, AutoReloadsClip=No on A/D.",
        "KindOf/Draw/Body/Locomotor/Geometry/module tags were already identical.",
        "Contain/riders were already absent in #597; spawn still crashed.",
        "",
        "CONTROL: restore PR #593 factory object bodies and weapon blocks.",
        "Keep Iraq_AlAbbasTELCommandSet so the building CommandSet is unique.",
        "Factory TELs use Scud_B_CommandSet again. Country TEL rearm unchanged.",
        "Factory half-price rearm is NOT present on A-J.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART size: {SIZE_ART}",
        f"- ART SHA256: {SHA_ART}",
        f"- Changed vs PR #597: {', '.join(changed_vs_597)}",
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
        "- Factory A-J object bodies byte-match PR #593",
        "- Factory A-J weapons byte-match PR #593 (no rearm FireOCL)",
        "- Scud_B_CommandSet restored; no PLAYER_UPGRADE / TriggeredBy on A-J",
        "- Iraq_AlAbbasCommandSet unique and identical to PR #593 building set",
        "- Iraq_AlAbbasTELCommandSet still reserved (startup collision fix)",
        "- Iraq_Alhussaien rider rearm and 9P117 unchanged; ART = PR #593",
        "",
        "Static validation completed; runtime game test not performed.",
        "Spawn crash is NOT claimed fixed. Unresolved: produce A-J in Zero Hour.",
        "Factory half-price rearm is withheld until this control is spawn-safe.",
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
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={SIZE_ART}\n"
        f"ART_SHA256={SHA_ART}\n"
        f"CHANGED_VS_597={', '.join(changed_vs_597)}\n"
        "CONTROL=PR593 factory objects+weapons; AlAbbasTELCommandSet reserved\n"
        "FACTORY_REARM=REMOVED from A-J until spawn is proven in-game\n"
        "BASELINE=PR #597 history + PR #593 factory bodies/ART\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n"
        "SPAWN_CRASH_CLAIMED_FIXED=NO\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: factory A-J spawn-safe CONTROL\n"
        "\n"
        "Restores PR #593 factory missile objects and weapons. Factory rearm\n"
        "is removed from A-J. Al-Abbas building CommandSet is unchanged.\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "  _SPEC_ART_ONE.big  (unchanged from PR #593)\n"
        "\n"
        "Static validation completed; runtime spawn test not performed.\n",
        encoding="utf-8",
    )
    (OUT / "DIFF_593_VS_597.txt").write_text(
        "Factory A-J packed last-wins differences (593 spawn-safe vs 597 crashing):\n"
        "\n"
        "UNCHANGED: KindOf, Draw=W3DTruckDraw, Body=ActiveBody, Locomotor,\n"
        "Geometry, DeployStyleAIUpdate, Physics, empty-then-TriggeredBy module\n"
        "tag ModuleTag_09h56u56j, death/FX modules, ProductionUpdate, costs.\n"
        "No RiderChangeContain / InitialPayload / GARRISONABLE in #597.\n"
        "\n"
        "CHANGED (all rearm add-ons introduced #594-#596):\n"
        "1. WeaponSet Conditions=PLAYER_UPGRADE (same primary weapon)\n"
        "2. CommandSet Scud_B_CommandSet -> unique Iraq_*CommandSet / TELCommandSet\n"
        "3. WeaponSetUpgrade TriggeredBy = Upgrade_Rearm_<object>\n"
        "4. Weapon FireOCL = OCL_Rearm_<object> (non-contained stripper)\n"
        "5. AutoReloadsClip=No on A (AlFahd500) and D (AlAbbas); B/C/H/I/J already No\n"
        "\n"
        "CONTROL restores 1-5 to PR #593. Country TEL rearm kept.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_SPAWN_CONTROL.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
        zf.write(OUT / "DIFF_593_VS_597.txt", "DIFF_593_VS_597.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
