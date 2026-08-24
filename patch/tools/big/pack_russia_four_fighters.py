#!/usr/bin/env python3
"""PR #385 baseline + isolated four fighters on the live Large Air Base menu.

Stock CommandButton.ini / Weapon.ini / Russia_System.ini / CSF / existing
aircraft stay untouched.

CommandSet.ini is the one live file that is surgically updated:
  Russia_LargeAirBaseCommandSet keeps slots 1-10 and 13-14 from #385
  and gains slots 11 / 12 / 15 / 16. No overlay CommandSet file.
  No second Russia_LargeAirBaseCommandSet definition.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

DATA_SRC = Path("/tmp/russia_su35s_ka52/_SPEC_DATA_ONE.big")
ART_SRC = Path("/tmp/radar_pkg/_SPEC_ART_ONE.big")
PATCH = Path("/workspace/patch")
OUT = Path("/tmp/russia_four_fighters")

CS_KEY = r"data\ini\commandset.ini"
LARGE_NAME = "Russia_LargeAirBaseCommandSet"

OLD_LARGE = (
    "CommandSet Russia_LargeAirBaseCommandSet\n"
    "  1  = Command_ConstructRussiaJetSu75Checkmate\n"
    "  2  = Command_ConstructRussiaJetSu35S\n"
    "  3  = Command_ConstructRussiaJetSu30SM2\n"
    "  4  = Command_ConstructRussiaJetSU25T\n"
    "  5  = Command_ConstructRussiaJetSu35AG\n"
    "  6  = Command_ConstructRussiaJetMig31K\n"
    "  7  = Command_ConstructRussiaHelicopterMi28N\n"
    "  8  = Command_ConstructRussiaHelicopterKA52\n"
    "  9  = Command_ConstructRussiaJetSu57AA\n"
    "  10 = Command_ConstructRussiaJetSu47Recon\n"
    "  13 = Command_SetRallyPoint\n"
    "  14 = Command_Sell\n"
    "End"
)
NEW_LARGE = (
    "CommandSet Russia_LargeAirBaseCommandSet\n"
    "  1  = Command_ConstructRussiaJetSu75Checkmate\n"
    "  2  = Command_ConstructRussiaJetSu35S\n"
    "  3  = Command_ConstructRussiaJetSu30SM2\n"
    "  4  = Command_ConstructRussiaJetSU25T\n"
    "  5  = Command_ConstructRussiaJetSu35AG\n"
    "  6  = Command_ConstructRussiaJetMig31K\n"
    "  7  = Command_ConstructRussiaHelicopterMi28N\n"
    "  8  = Command_ConstructRussiaHelicopterKA52\n"
    "  9  = Command_ConstructRussiaJetSu57AA\n"
    "  10 = Command_ConstructRussiaJetSu47Recon\n"
    "  11 = Command_ConstructRussiaJetSu47Berkut\n"
    "  12 = Command_ConstructRussiaJetSu57T50\n"
    "  13 = Command_SetRallyPoint\n"
    "  14 = Command_Sell\n"
    "  15 = Command_ConstructRussiaJetSu75\n"
    "  16 = Command_ConstructRussiaJetSu39\n"
    "End"
)

EXPECTED_SLOTS = {
    1: "Command_ConstructRussiaJetSu75Checkmate",
    2: "Command_ConstructRussiaJetSu35S",
    3: "Command_ConstructRussiaJetSu30SM2",
    4: "Command_ConstructRussiaJetSU25T",
    5: "Command_ConstructRussiaJetSu35AG",
    6: "Command_ConstructRussiaJetMig31K",
    7: "Command_ConstructRussiaHelicopterMi28N",
    8: "Command_ConstructRussiaHelicopterKA52",
    9: "Command_ConstructRussiaJetSu57AA",
    10: "Command_ConstructRussiaJetSu47Recon",
    11: "Command_ConstructRussiaJetSu47Berkut",
    12: "Command_ConstructRussiaJetSu57T50",
    13: "Command_SetRallyPoint",
    14: "Command_Sell",
    15: "Command_ConstructRussiaJetSu75",
    16: "Command_ConstructRussiaJetSu39",
}

AIRFORCE = PATCH / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"

NEW_DATA = {
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su47Berkut.ini": AIRFORCE
    / "Su47Berkut.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su57T50.ini": AIRFORCE
    / "Su57T50.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su75Checkmate.ini": AIRFORCE
    / "Su75Checkmate.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su39.ini": AIRFORCE / "Su39.ini",
    r"Data\INI\CommandButton_Russia_Su47.ini": PATCH / "Data/INI/CommandButton_Russia_Su47.ini",
    r"Data\INI\CommandButton_Russia_Su57T50.ini": PATCH / "Data/INI/CommandButton_Russia_Su57T50.ini",
    r"Data\INI\CommandButton_Russia_Su75.ini": PATCH / "Data/INI/CommandButton_Russia_Su75.ini",
    r"Data\INI\CommandButton_Russia_Su39.ini": PATCH / "Data/INI/CommandButton_Russia_Su39.ini",
}

NEW_ART = {
    r"Art\W3D\RUSU-47.W3D": PATCH / "Art/W3D/RUSU-47.W3D",
    r"Art\W3D\RUSU-47_D.W3D": PATCH / "Art/W3D/RUSU-47_D.W3D",
    r"Art\W3D\RUSU-47_E.W3D": PATCH / "Art/W3D/RUSU-47_E.W3D",
    r"Art\Textures\RUSU-47mainskin.tga": PATCH / "Art/Textures/RUSU-47mainskin.tga",
    r"Art\Textures\RUSU-47mainskin_D.tga": PATCH / "Art/Textures/RUSU-47mainskin_D.tga",
    r"Art\Textures\RUSU-47mainskin_E.tga": PATCH / "Art/Textures/RUSU-47mainskin_E.tga",
    r"Art\Textures\RUSU47MAP.dds": PATCH / "Art/Textures/RUSU47MAP.dds",
    r"Art\W3D\LSFT50.W3D": PATCH / "Art/W3D/LSFT50.W3D",
    r"Art\W3D\LSFT50d.W3D": PATCH / "Art/W3D/LSFT50d.W3D",
    r"Art\W3D\LSFT50k.W3D": PATCH / "Art/W3D/LSFT50k.W3D",
    r"Art\Textures\LSFT50.dds": PATCH / "Art/Textures/LSFT50.dds",
    r"Art\Textures\LSFT50d.dds": PATCH / "Art/Textures/LSFT50d.dds",
    r"Art\Textures\LSFT50k.dds": PATCH / "Art/Textures/LSFT50k.dds",
    r"Art\W3D\RUSU75.W3D": PATCH / "Art/W3D/RUSU75.W3D",
    r"Art\W3D\RUSU75_D.W3D": PATCH / "Art/W3D/RUSU75_D.W3D",
    r"Art\W3D\RUSU75_E.W3D": PATCH / "Art/W3D/RUSU75_E.W3D",
    r"Art\W3D\RUSU75_E1.W3D": PATCH / "Art/W3D/RUSU75_E1.W3D",
    r"Art\W3D\RUSU75_E2.W3D": PATCH / "Art/W3D/RUSU75_E2.W3D",
    r"Art\Textures\SU-75.dds": PATCH / "Art/Textures/SU-75.dds",
    r"Art\Textures\SU-75_D.dds": PATCH / "Art/Textures/SU-75_D.dds",
    r"Art\Textures\SU-75_E.dds": PATCH / "Art/Textures/SU-75_E.dds",
}

FROZEN = (
    r"data\ini\commandbutton.ini",
    r"data\ini\weapon.ini",
    r"data\ini\upgrade.ini",
    r"data\english\generals.csf",
    r"data\ini\object\specter\armed forces of russian federation\russia_system.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su35s.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\ka52m.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su57.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su57_aa.ini",
    r"data\ini\object\specter\armed forces of russian federation\airforce\su25t_su39.ini",
    r"data\ini\object\specter\armed forces of russian federation\buildings\russia_largeairbase.ini",
)

REQUIRED_OBJECTS = {
    "RussiaJetSu47Berkut": "RUSU-47",
    "RussiaJetSu57T50": "LSFT50",
    "RussiaJetSu75": "RUSU75",
    "RussiaJetSu39": "RUS_SU39",
}

FORBIDDEN_REUSED_OBJECTS = (
    "RussiaJetSu75Checkmate",
    "RussiaJetSU25T",
    "RussiaJetSU25T_UCAS",
    "RussiaJetSu47Recon",
    "RussiaJetSu57",
    "RussiaJetSu57AA",
    "RussiaJetSu35S",
    "RussiaJetSu34",
    "RussiaHelicopterKA52",
)


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def write_big(entries: list[tuple[str, bytes]]) -> bytes:
    header = 16
    encoded = []
    for name, blob in entries:
        raw = name.replace("/", "\\").encode("latin1")
        encoded.append((raw, blob))
        header += 8 + len(raw) + 1
    offset = header
    out = bytearray()
    total = header + sum(len(b) for _, b in encoded)
    out += b"BIGF"
    out += struct.pack(">I", total)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header)
    for raw, blob in encoded:
        out += struct.pack(">II", offset, len(blob))
        out += raw + b"\x00"
        offset += len(blob)
    for _, blob in encoded:
        out += blob
    return bytes(out)


def upsert_new_only(entries: list[tuple[str, bytes]], name: str, content: bytes) -> None:
    key = name.replace("/", "\\").lower()
    for n, _ in entries:
        if n.replace("/", "\\").lower() == key:
            raise SystemExit(f"refusing to replace existing file: {n}")
    entries.append((name.replace("/", "\\"), content))


def replace_existing(entries: list[tuple[str, bytes]], name: str, content: bytes) -> None:
    key = name.replace("/", "\\").lower()
    for i, (n, _) in enumerate(entries):
        if n.replace("/", "\\").lower() == key:
            entries[i] = (n, content)
            return
    raise SystemExit(f"missing existing file to replace: {name}")


def parse_commandset_block(text: str, name: str, max_slot: int = 16) -> dict:
    matches = list(re.finditer(rf"^CommandSet {re.escape(name)}\s*$", text, re.M))
    if len(matches) != 1:
        raise SystemExit(f"parser FAIL: {name} defined {len(matches)} time(s)")
    start = matches[0].start()
    rest = text[start:]
    m = re.match(
        rf"CommandSet {re.escape(name)}\n(?P<body>.*?)(?:\nEnd)(?=\n|$)",
        rest,
        re.S,
    )
    if not m:
        raise SystemExit(f"parser FAIL: {name} missing well-formed End")
    slots = {}
    for lineno, line in enumerate(m.group("body").splitlines(), 1):
        raw = line.split(";", 1)[0].rstrip()
        if not raw.strip():
            continue
        sm = re.match(r"^  (\d+)\s*=\s*(\S+)\s*$", raw)
        if not sm:
            raise SystemExit(f"parser FAIL: {name} bad line {lineno}: {raw!r}")
        slot = int(sm.group(1))
        if slot in slots:
            raise SystemExit(f"parser FAIL: {name} duplicate slot {slot}")
        if slot < 1 or slot > max_slot:
            raise SystemExit(f"parser FAIL: {name} slot {slot} out of range")
        slots[slot] = sm.group(2)
    return {"block": rest[: m.end()], "slots": slots}


def check_ini_bytes(raw: bytes, label: str) -> str:
    if raw[:2] == b"\xff\xfe" or raw[:3] == b"\xef\xbb\xbf":
        raise SystemExit(f"parser FAIL: {label} has a BOM")
    if b"\r\n" in raw:
        raise SystemExit(f"parser FAIL: {label} has CRLF")
    text = raw.decode("latin1")
    if text.count("End") < 1:
        raise SystemExit(f"parser FAIL: {label} has no End")
    return text


def patch_commandset(raw: bytes) -> bytes:
    text = check_ini_bytes(raw, "source CommandSet.ini")
    if text.count("CommandSet Russia_LargeAirBaseCommandSet") != 1:
        raise SystemExit("parser FAIL: source CommandSet.ini Large set is not unique")
    if OLD_LARGE not in text:
        raise SystemExit("parser FAIL: #385 Russia_LargeAirBaseCommandSet block not found")
    if text.count(OLD_LARGE) != 1:
        raise SystemExit("parser FAIL: #385 Large block matched more than once")
    patched = text.replace(OLD_LARGE, NEW_LARGE, 1)
    if patched.replace(NEW_LARGE, OLD_LARGE, 1) != text:
        raise SystemExit("parser FAIL: CommandSet rewrite was not a pure slot add")
    out = patched.encode("latin1")
    if b"\r\n" in out:
        raise SystemExit("parser FAIL: patched CommandSet.ini gained CRLF")
    return out


def parser_check_live_commandset(raw: bytes) -> None:
    text = check_ini_bytes(raw, "CommandSet.ini")
    if text.count("CommandSet Russia_LargeAirBaseCommandSet") != 1:
        raise SystemExit("parser FAIL: duplicated Russia_LargeAirBaseCommandSet in CommandSet.ini")
    parsed = parse_commandset_block(text, LARGE_NAME, max_slot=16)
    if parsed["block"] != NEW_LARGE:
        raise SystemExit("parser FAIL: live Russia_LargeAirBaseCommandSet body mismatch")
    if parsed["slots"] != EXPECTED_SLOTS:
        raise SystemExit(f"parser FAIL: live Large slots {parsed['slots']}")
    for slot in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14):
        if parsed["slots"][slot] != EXPECTED_SLOTS[slot]:
            raise SystemExit(f"parser FAIL: existing slot {slot} changed")
    print("PARSER CHECK PASS: live CommandSet.ini has unique Large set + slots 11/12/15/16")


def assert_no_duplicate_large(entries: list[tuple[str, bytes]]) -> None:
    hits = []
    for n, b in entries:
        if b"CommandSet Russia_LargeAirBaseCommandSet" in b:
            hits.append(n)
        key = n.replace("/", "\\").lower()
        if "commandset_zzzz" in key or key.endswith(r"commandset_zzzz_russia_largeairbase.ini"):
            raise SystemExit(f"parser FAIL: overlay CommandSet file still packed: {n}")
    if hits != [next(n for n, _ in entries if n.replace("/", "\\").lower() == CS_KEY)]:
        raise SystemExit(f"parser FAIL: Russia_LargeAirBaseCommandSet files={hits}")
    print("PARSER CHECK PASS: no duplicate Russia_LargeAirBaseCommandSet, no overlay file")


def collect_objects(entries: list[tuple[str, bytes]]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        text = b.decode("latin1", "replace")
        for obj in re.findall(r"^Object (\S+)", text, re.M):
            found.setdefault(obj, []).append(n)
    return found


def collect_buttons(entries: list[tuple[str, bytes]]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for n, b in entries:
        nl = n.replace("/", "\\").lower()
        if "commandbutton" not in nl:
            continue
        text = b.decode("latin1", "replace")
        for btn in re.findall(r"^CommandButton (\S+)", text, re.M):
            found.setdefault(btn, []).append(n)
    return found


def verify_new_object_file(path: Path, obj: str, model: str) -> None:
    raw = path.read_bytes()
    text = check_ini_bytes(raw, path.name)
    objs = re.findall(r"^Object (\S+)", text, re.M)
    if objs != [obj]:
        raise SystemExit(f"parser FAIL: {path.name} objects {objs} != [{obj}]")
    if not re.search(rf"Model\s+=\s+{re.escape(model)}\s*$", text, re.M):
        raise SystemExit(f"parser FAIL: {path.name} missing Model={model}")
    for banned in FORBIDDEN_REUSED_OBJECTS:
        if re.search(rf"^Object {re.escape(banned)}\s*$", text, re.M):
            raise SystemExit(f"parser FAIL: {path.name} redefines packed {banned}")
    print(f"PARSER CHECK PASS: {path.name} Object {obj} Model {model}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    overlay = PATCH / "Data/INI/CommandSet_ZZZZ_Russia_LargeAirBase.ini"
    if overlay.exists():
        raise SystemExit("refusing to pack: overlay CommandSet_ZZZZ_Russia_LargeAirBase.ini still exists")

    for obj, model, fname in (
        ("RussiaJetSu47Berkut", "RUSU-47", "Su47Berkut.ini"),
        ("RussiaJetSu57T50", "LSFT50", "Su57T50.ini"),
        ("RussiaJetSu75", "RUSU75", "Su75Checkmate.ini"),
        ("RussiaJetSu39", "RUS_SU39", "Su39.ini"),
    ):
        verify_new_object_file(AIRFORCE / fname, obj, model)

    src_entries = read_big(DATA_SRC)
    src_map = {n.replace("/", "\\").lower(): b for n, b in src_entries}
    baseline_cs = src_map[CS_KEY]
    baseline_text = check_ini_bytes(baseline_cs, "PR #385 CommandSet.ini")
    if parse_commandset_block(baseline_text, LARGE_NAME, max_slot=14)["block"] != OLD_LARGE:
        raise SystemExit("parser FAIL: source CommandSet.ini is not the #385 Large block")

    patched_cs = patch_commandset(baseline_cs)
    parser_check_live_commandset(patched_cs)

    data_entries = list(src_entries)
    replace_existing(data_entries, r"Data\INI\CommandSet.ini", patched_cs)
    added = {r"Data\INI\CommandSet.ini": "slots 11/12/15/16 added"}
    for name, path in NEW_DATA.items():
        upsert_new_only(data_entries, name, path.read_bytes())
        added[name] = "added"

    new_map = {n.replace("/", "\\").lower(): b for n, b in data_entries}
    if new_map[CS_KEY] == src_map[CS_KEY]:
        raise SystemExit("parser FAIL: CommandSet.ini was not updated")
    for key in FROZEN:
        if src_map[key] != new_map[key]:
            raise SystemExit(f"existing file replaced: {key}")

    extra = sorted(set(new_map) - set(src_map))
    expected_extra = {k.replace("/", "\\").lower() for k in NEW_DATA}
    if set(extra) != expected_extra:
        raise SystemExit(f"unexpected added DATA files: {sorted(set(extra) ^ expected_extra)}")

    assert_no_duplicate_large(data_entries)
    parser_check_live_commandset(new_map[CS_KEY])

    objects = collect_objects(data_entries)
    for obj in REQUIRED_OBJECTS:
        files = objects.get(obj, [])
        if len(files) != 1:
            raise SystemExit(f"parser FAIL: Object {obj} files={files}")
        print(f"OBJECT UNIQUE PASS: {obj} -> {files[0]}")
    for banned in FORBIDDEN_REUSED_OBJECTS:
        if banned not in objects:
            raise SystemExit(f"parser FAIL: expected packed object missing: {banned}")

    buttons = collect_buttons(data_entries)
    required_buttons = {
        "Command_ConstructRussiaJetSu47Berkut": "RussiaJetSu47Berkut",
        "Command_ConstructRussiaJetSu57T50": "RussiaJetSu57T50",
        "Command_ConstructRussiaJetSu75": "RussiaJetSu75",
        "Command_ConstructRussiaJetSu39": "RussiaJetSu39",
    }
    for btn in required_buttons:
        if btn not in buttons:
            raise SystemExit(f"parser FAIL: missing CommandButton {btn}")
        if len(buttons[btn]) != 1:
            raise SystemExit(f"parser FAIL: CommandButton {btn} duplicated in {buttons[btn]}")

    art_entries = read_big(ART_SRC)
    art_src_map = {n.replace("/", "\\").lower(): b for n, b in art_entries}
    art_added = {}
    for name, path in NEW_ART.items():
        upsert_new_only(art_entries, name, path.read_bytes())
        art_added[name] = "added"
    art_new_map = {n.replace("/", "\\").lower(): b for n, b in art_entries}
    extra_art = sorted(set(art_new_map) - set(art_src_map))
    expected_art = {k.replace("/", "\\").lower() for k in NEW_ART}
    if set(extra_art) != expected_art:
        raise SystemExit(f"unexpected added ART files: {sorted(set(extra_art) ^ expected_art)}")
    for banned in (
        r"art\w3d\rus_su57.w3d",
        r"art\w3d\rus_su39.w3d",
        r"art\textures\rus_su39.dds",
    ):
        if banned in art_src_map and art_src_map[banned] != art_new_map[banned]:
            raise SystemExit(f"existing ART replaced: {banned}")

    data_bytes = write_big(data_entries)
    art_bytes = write_big(art_entries)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_bytes)
    out_art.write_bytes(art_bytes)

    written_entries = read_big(out_data)
    written = {n.replace("/", "\\").lower(): b for n, b in written_entries}
    parser_check_live_commandset(written[CS_KEY])
    assert_no_duplicate_large(written_entries)
    if r"data\ini\commandset_zzzz_russia_largeairbase.ini" in written:
        raise SystemExit("parser FAIL: overlay CommandSet packed in final DATA BIG")

    zpath = OUT / "RUSSIA_FOUR_FIGHTERS.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")

    report = OUT / "PACK_REPORT.txt"
    report.write_text(
        f"DATA SHA256={hashlib.sha256(data_bytes).hexdigest()} SIZE={len(data_bytes)}\n"
        f"ART  SHA256={hashlib.sha256(art_bytes).hexdigest()} SIZE={len(art_bytes)}\n"
        f"ZIP  SHA256={hashlib.sha256(zpath.read_bytes()).hexdigest()} SIZE={zpath.stat().st_size}\n"
        f"CommandSet.ini SHA256={hashlib.sha256(written[CS_KEY]).hexdigest()} (live #385 + slots 11/12/15/16)\n"
        f"added_data={added}\n"
        f"added_art={art_added}\n"
        f"objects={ {k: objects[k] for k in REQUIRED_OBJECTS} }\n"
        f"PARSER CHECK PASS\n",
        encoding="utf-8",
    )
    print(report.read_text())
    print("ZIP", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
