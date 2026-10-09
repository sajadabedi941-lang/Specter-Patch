#!/usr/bin/env python3
"""Fix startup crash: duplicate last-wins Iraq_AlAbbasCommandSet.

Packed last-wins (PR #596 vs #593):

  CommandSet.ini already defined Iraq_AlAbbasCommandSet for the Al-Abbas
  BUILDING (Iraq_Abbas / Iraq_Abbas_AI):

    1 = Command_AlAbbasGroundAttack
    14 = Command_Sell

  PR #596 appended a second CommandSet with the SAME name for the factory
  TEL Iraq_AlAbbas (FireMainWeapon / re-arm / Scud switch buttons).

  SAGE last-wins replaces the building command set. The crash dialog names
  Data/INI/CommandSet.ini / Iraq_AlabbasCommandSet (case-insensitive).

Fix: rename ONLY the appended TEL command set to Iraq_AlAbbasTELCommandSet
and point the factory TEL at it. Restore last-wins of the original building
set. ART unchanged. Rearm implementation otherwise unchanged.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_596 = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_ALABAAS_REARM/_SPEC_DATA_ONE.big"
SRC_593 = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_TOP_MARKINGS/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_TOP_MARKINGS/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_COMMANDSET"

SHA_596 = "2335a8e211c288547be629aa520995a91a120eba6e061b6a87943c1e2d08523a"
SIZE_596 = 366616562
SHA_593_DATA = "6af19c95f508a80752e26fd603d2745b5c2c51d446890a3f373816d329033f27"
SIZE_593_DATA = 366515208
SHA_ART = "95a0737f7f6e7d0f15a2a1234b222d1cf9643d1199b00e28e7e87e7c89083ed4"
SIZE_ART = 1294467676

CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
TEL_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini"
BLD_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_Abbas.ini"
BLD_AI_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_Abbas_AI.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"

OLD_SET = "Iraq_AlAbbasCommandSet"
NEW_SET = "Iraq_AlAbbasTELCommandSet"

BUILDING_SET = (
    "CommandSet Iraq_AlAbbasCommandSet\r\n"
    "  1 = Command_AlAbbasGroundAttack\r\n"
    "  14 = Command_Sell\r\n"
    "End"
)
TEL_SET_OLD = (
    "CommandSet Iraq_AlAbbasCommandSet\r\n"
    "  1 = Command_FireMainWeapon\r\n"
    "  5 = Command_Rearm_Iraq_AlAbbas\r\n"
    "  6 = Command_ScudSwitchToHE\r\n"
    "  8 = Command_ScudSwitchToHE_NI\r\n"
    "  10 = Command_ScudSwitchToHE_CH\r\n"
    "  12 = Command_AttackMove\r\n"
    "  13 = Command_Guard\r\n"
    "  14 = Command_Stop\r\n"
    "End"
)
TEL_SET_NEW = TEL_SET_OLD.replace(
    "CommandSet Iraq_AlAbbasCommandSet",
    "CommandSet Iraq_AlAbbasTELCommandSet",
    1,
)


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


def cmdset_blocks(text: str, name: str) -> list[str]:
    return [m.group(0) for m in re.finditer(rf"(?ms)^CommandSet {re.escape(name)}\n.*?^End", text)]


def patch_commandset(raw: bytes) -> bytes:
    # Operate on CRLF bytes so we only rename the appended TEL block.
    if raw.count(TEL_SET_OLD.encode("latin1")) != 1:
        raise SystemExit(
            f"expected exactly 1 appended TEL Iraq_AlAbbasCommandSet, "
            f"found {raw.count(TEL_SET_OLD.encode('latin1'))}"
        )
    if raw.count(BUILDING_SET.encode("latin1")) < 1:
        raise SystemExit("original building Iraq_AlAbbasCommandSet missing")
    out = raw.replace(TEL_SET_OLD.encode("latin1"), TEL_SET_NEW.encode("latin1"), 1)
    return out


def patch_tel_object(text: str) -> str:
    body = object_body(text, "Iraq_AlAbbas")
    if not body:
        raise SystemExit("Iraq_AlAbbas missing")
    if field(body, "CommandSet") != OLD_SET:
        raise SystemExit(f"TEL CommandSet is {field(body,'CommandSet')}")
    new = body.replace(f"CommandSet    = {OLD_SET}", f"CommandSet    = {NEW_SET}", 1)
    if NEW_SET not in new:
        raise SystemExit("TEL CommandSet rename failed")
    return text.replace(body, new, 1)


def validate(data: dict[str, bytes], d593: dict[str, bytes], d596: dict[str, bytes]) -> list[str]:
    fails = []
    cs = decode(data[CS_KEY])
    cs593 = decode(d593[CS_KEY])
    cb = decode(data[CB_KEY])
    blocks = cmdset_blocks(cs, OLD_SET)
    if len(blocks) != 1:
        fails.append(f"Iraq_AlAbbasCommandSet count {len(blocks)} != 1")
    else:
        orig = cmdset_blocks(cs593, OLD_SET)
        if not orig:
            fails.append("593 missing Iraq_AlAbbasCommandSet")
        elif blocks[0].replace("\r", "") != orig[-1].replace("\r", ""):
            fails.append("building Iraq_AlAbbasCommandSet last-wins != PR #593")
        if "Command_AlAbbasGroundAttack" not in blocks[0] or "Command_Sell" not in blocks[0]:
            fails.append("building set lost GroundAttack/Sell")
        if "Command_FireMainWeapon" in blocks[0] or "Command_Rearm_Iraq_AlAbbas" in blocks[0]:
            fails.append("building set still has TEL buttons")
    telset = last_block("CommandSet", NEW_SET, cs)
    if not telset:
        fails.append("missing Iraq_AlAbbasTELCommandSet")
    else:
        for btn in [
            "Command_FireMainWeapon",
            "Command_Rearm_Iraq_AlAbbas",
            "Command_ScudSwitchToHE",
            "Command_ScudSwitchToHE_NI",
            "Command_ScudSwitchToHE_CH",
            "Command_AttackMove",
            "Command_Guard",
            "Command_Stop",
        ]:
            if btn not in telset:
                fails.append(f"TEL set missing {btn}")
            if not re.search(rf"^CommandButton {re.escape(btn)}\s*$", cb, re.M):
                fails.append(f"missing CommandButton {btn}")
        if "Command_AlAbbasGroundAttack" in telset:
            fails.append("TEL set stole building buttons")
    # case-insensitive uniqueness
    lows = {}
    for m in re.finditer(r"^CommandSet (\S+)", cs, re.M):
        lows.setdefault(m.group(1).lower(), []).append(m.group(1))
    for low, names in lows.items():
        if len(names) > 1:
            fails.append(f"duplicate CommandSet last-wins {names}")
    tel = object_body(decode(data[TEL_KEY]), "Iraq_AlAbbas")
    if field(tel, "CommandSet") != NEW_SET:
        fails.append(f"TEL CommandSet {field(tel,'CommandSet')}")
    for key, obj in ((BLD_KEY, "Iraq_Abbas"), (BLD_AI_KEY, "Iraq_Abbas_AI")):
        body = object_body(decode(data[key]), obj)
        if field(body, "CommandSet") != OLD_SET:
            fails.append(f"{obj} CommandSet {field(body,'CommandSet')}")
        if data[key] != d596[key]:
            fails.append(f"{obj} file mutated")
    if decode(data[R11_KEY]) != decode(d593[R11_KEY]):
        fails.append("9P117 mutated")
    # factory TEL still spawn-safe
    if "RiderChangeContain" in (tel or "") or "InitialPayload" in (tel or ""):
        fails.append("TEL reintroduced contain")
    for btn in ["Command_AlAbbasGroundAttack", "Command_Sell"]:
        if not re.search(rf"^CommandButton {re.escape(btn)}\s*$", cb, re.M):
            fails.append(f"missing building button {btn}")
    changed = sorted(k for k in data if d596.get(k) != data.get(k))
    allowed = {CS_KEY, TEL_KEY}
    for k in changed:
        if k not in allowed:
            fails.append(f"unrelated path changed: {k}")
    return fails


def main() -> int:
    if sha256_path(SRC_596) != SHA_596 or SRC_596.stat().st_size != SIZE_596:
        raise SystemExit("PR #596 DATA mismatch")
    if sha256_path(SRC_593) != SHA_593_DATA or SRC_593.stat().st_size != SIZE_593_DATA:
        raise SystemExit("PR #593 DATA mismatch")
    if sha256_path(SRC_ART) != SHA_ART or SRC_ART.stat().st_size != SIZE_ART:
        raise SystemExit("PR #593 ART mismatch")

    d596 = parse_big(SRC_596.read_bytes())
    d593 = parse_big(SRC_593.read_bytes())
    data = dict(d596)
    data[CS_KEY] = patch_commandset(data[CS_KEY])
    data[TEL_KEY] = to_crlf(patch_tel_object(decode(data[TEL_KEY])))
    mapped = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlAbbas.ini"
    if mapped.exists():
        mapped.write_bytes(data[TEL_KEY])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    shutil.copy2(SRC_ART, OUT / "_SPEC_ART_ONE.big")
    extracted = parse_big(out_data.read_bytes())
    fails = validate(extracted, d593, d596)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    if sha256_path(OUT / "_SPEC_ART_ONE.big") != SHA_ART:
        fails.append("ART copy not byte-identical")

    changed = sorted(k for k in extracted if d596.get(k) != extracted.get(k))
    data_sha = sha256_path(out_data)
    report = [
        "# SPECTER startup crash fix: Iraq_AlAbbasCommandSet last-wins collision",
        "",
        "ROOT CAUSE: PR #596 appended CommandSet Iraq_AlAbbasCommandSet for the",
        "factory TEL. That name already belonged to the Al-Abbas BUILDING",
        "(Iraq_Abbas / Iraq_Abbas_AI): Command_AlAbbasGroundAttack + Command_Sell.",
        "Last-wins replaced the building set with vehicle FireMainWeapon/re-arm",
        "buttons. Crash dialog: Data/INI/CommandSet.ini / Iraq_AlabbasCommandSet.",
        "",
        "FIX: rename the TEL set to Iraq_AlAbbasTELCommandSet. Building set is",
        "again the unique last-wins definition, identical to PR #593.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART size: {SIZE_ART}",
        f"- ART SHA256: {SHA_ART}",
        f"- Changed vs PR #596: {', '.join(changed)}",
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
        "- Exactly one Iraq_AlAbbasCommandSet; last-wins == PR #593 building set",
        "- Factory TEL uses unique Iraq_AlAbbasTELCommandSet",
        "- Iraq_Abbas / Iraq_Abbas_AI still reference Iraq_AlAbbasCommandSet",
        "- All CommandButtons in both sets exist",
        "- No duplicate CommandSet names (case-insensitive)",
        "- ART byte-identical to PR #593; 9P117 unchanged",
        "",
        "Static validation completed; runtime game test not performed.",
        "Unresolved runtime step: launch Zero Hour past CommandSet.ini load.",
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
        f"CHANGED_VS_596={', '.join(changed)}\n"
        "ROOT_CAUSE=duplicate last-wins CommandSet Iraq_AlAbbasCommandSet (building vs factory TEL)\n"
        "FIX=rename TEL set to Iraq_AlAbbasTELCommandSet\n"
        "BASELINE=PR #596 DATA + PR #593 ART\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: startup crash fix for Iraq_AlAbbasCommandSet\n"
        "\n"
        "The factory TEL no longer overwrites the Al-Abbas building CommandSet.\n"
        "Place both complete replacement BIGs in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "  _SPEC_ART_ONE.big  (unchanged from PR #593)\n"
        "\n"
        "Static validation completed; runtime game test not performed.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_COMMANDSET.zip"
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
