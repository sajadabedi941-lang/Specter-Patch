#!/usr/bin/env python3
"""DATA-only: retarget NorthKorea_PowerPlant to existing NKor_Powerplant.W3D.

Source: BUILDING_FLAG_SIZE_CC. Does not edit ART, Iraq PP, or other countries.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/BUILDING_FLAG_SIZE_CC/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/BUILDING_FLAG_SIZE_CC/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "b72ebb16303553b6fabeb901ba646da0d73aa5f8400e0600fca9a0aa101140d9"
EXPECTED_ART_SHA = "b40a8e686df17ffbb538be22ecb17c783a9b6913ab0d3af0d9ef3ed4ebdf7191"
RELEASE = Path("/workspace/patch/Release/NK_POWERPLANT_FLAG")
PAYLOAD = RELEASE / "payload"

P_FILE = r"Data\INI\Object\Specter\North Korea\NorthKorea_Systems.ini"
OBJ = "NorthKorea_PowerPlant"
OLD = "Iraq_Powerplant"
NEW = "NKor_Powerplant"

FROZEN = [
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_PowerPlant.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_PowerPlant.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_PowerPlant.ini",
    r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_PowerPlant.ini",
    r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_PowerPlant.ini",
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_PowerPlant.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_PowerPlant.ini",
    r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_PowerPlant.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Japan_Systems.ini",
    r"Data\INI\Object\Specter\South Korean Armed Forces\SouthKorea_Systems.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Vietnam_Systems.ini",
    r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_SupplyCenter.ini",
    r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_CommandCenter.ini",
    r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_WarFactory.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_Barracks.ini",
    r"Data\INI\Weapon.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
]

OBJ_RE = re.compile(r"(?im)^Object\s+(\S+)")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(name: str) -> str:
    return name.replace("/", "\\")


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries):
    header_size = 16
    encoded = [n.encode("latin1", errors="replace") for n, _ in entries]
    for nb in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    out = bytearray(b"BIGF")
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries, target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 path, got {len(hits)}")
    return hits[0]


def object_spans(text: str):
    ms = list(OBJ_RE.finditer(text))
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        out.append((m.group(1), m.start(), end))
    return out


def last_objects(entries):
    last = {}
    for name, blob in entries:
        if not name.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        for obj, start, end in object_spans(text):
            last[obj] = text[start:end]
    return last


def main() -> int:
    if sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    data = read_big(SRC_DATA)
    orig = list(data)
    orig_map = {norm(n).lower(): b for n, b in orig}
    orig_last = last_objects(orig)

    idx = find_index(data, P_FILE)
    old_name, old_blob = data[idx]
    text = old_blob.decode("latin1", errors="replace")
    spans = object_spans(text)
    names = [n for n, _, _ in spans]
    if names.count(OBJ) != 1:
        raise SystemExit(f"{OBJ} count {names.count(OBJ)}")

    rebuilt = []
    cursor = 0
    for obj, start, end in spans:
        rebuilt.append(text[cursor:start])
        body = text[start:end]
        if obj == OBJ:
            # 3 Model + 3 Animation "Name.Name" = 9 token occurrences
            if body.count(OLD) != 9:
                raise SystemExit(f"{OBJ}: expected 9 {OLD} refs, got {body.count(OLD)}")
            if NEW in body:
                raise SystemExit(f"{OBJ}: already retargeted")
            body = body.replace(OLD, NEW)
            if body.count(NEW) != 9 or OLD in body:
                raise SystemExit("retarget failed")
        rebuilt.append(body)
        cursor = end
    rebuilt.append(text[cursor:])
    new_text = "".join(rebuilt)
    new_spans = object_spans(new_text)
    if [n for n, _, _ in new_spans] != names:
        raise SystemExit("object list drifted")
    old_map_obj = {n: text[s:e] for n, s, e in spans}
    new_map_obj = {n: new_text[s:e] for n, s, e in new_spans}
    for n in names:
        if n != OBJ and old_map_obj[n] != new_map_obj[n]:
            raise SystemExit(f"non-target object changed: {n}")

    new_blob = new_text.encode("latin1")
    PAYLOAD.mkdir(parents=True, exist_ok=True)
    dest = PAYLOAD / P_FILE.replace("\\", "/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(new_blob)
    data[idx] = (old_name, new_blob)

    if [n for n, _ in data] != [n for n, _ in orig]:
        raise SystemExit("DATA path order changed")
    for n, b in data:
        key = norm(n).lower()
        if key == norm(P_FILE).lower():
            continue
        if b != orig_map[key]:
            raise SystemExit(f"unintended rewrite: {n}")
    for p in FROZEN:
        if data[find_index(data, p)][1] != orig_map[norm(p).lower()]:
            raise SystemExit(f"frozen changed: {p}")

    last = last_objects(data)
    body = last[OBJ]
    if body.count(NEW) != 9 or OLD in body:
        raise SystemExit("last-win retarget failed")
    if last["Iraq_PowerPlant"] != orig_last["Iraq_PowerPlant"]:
        raise SystemExit("Iraq_PowerPlant changed")
    for obj in (
        "India_PowerPlant",
        "Pakistan_PowerPlant",
        "Japan_PowerPlant",
        "SouthKorea_PowerPlant",
        "Vietnam_PowerPlant",
        "Libya_PowerPlant",
        "Syria_PowerPlant",
        "UAE_PowerPlant",
        "SaudiArabia_PowerPlant",
        "SouthAfrica_PowerPlant",
        "NorthKorea_SupplyCenter",
        "NorthKorea_CommandCenter",
        "NorthKorea_WarFactory",
        "India_Barracks",
    ):
        if last[obj] != orig_last[obj]:
            raise SystemExit(f"frozen object changed: {obj}")

    # ART must still contain NKor_Powerplant and must not be packed
    art = read_big(SRC_ART)
    art_names = {norm(n).lower() for n, _ in art}
    if r"art\w3d\nkor_powerplant.w3d" not in art_names:
        raise SystemExit("NKor_Powerplant.W3D missing from live ART")

    RELEASE.mkdir(parents=True, exist_ok=True)
    out = RELEASE / "_SPEC_DATA_ONE.big"
    blob = build_big_ordered(data)
    out.write_bytes(blob)
    sha = sha256_file(out)
    audit = "\n".join(
        [
            "NK_POWERPLANT_FLAG",
            f"SOURCE_DATA_SHA {EXPECTED_DATA_SHA}",
            f"DATA_SHA256 {sha}",
            f"BYTES {out.stat().st_size}",
            f"FILE_COUNT {len(data)}",
            "ART_CHANGED = NO",
            "RETARGET = NorthKorea_PowerPlant Iraq_Powerplant -> NKor_Powerplant (9 tokens)",
            "IRAQ_POWERPLANT_UNCHANGED = YES",
            "OTHER_NINE_POWERPLANTS_UNCHANGED = YES",
            "NK_SUPPLY_CC_WF_UNCHANGED = YES",
            "INGAME_TESTED = NO",
            "STATIC_PACKED_AUDIT = PASS",
        ]
    )
    (RELEASE / "audit.txt").write_text(audit + "\n", encoding="utf-8")
    (RELEASE / "POST_PACK_VALIDATION.txt").write_text(audit + "\n", encoding="utf-8")
    (RELEASE / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {sha}\n"
        f"SOURCE_DATA_SHA {EXPECTED_DATA_SHA}\n"
        f"ART unchanged\n"
        f"BYTES {out.stat().st_size}\n",
        encoding="utf-8",
    )
    (RELEASE / "PACKED_FILES.txt").write_text(
        f"REPLACED\n  {P_FILE}\n  object {OBJ} only\nART_CHANGED = NO\n",
        encoding="utf-8",
    )
    (RELEASE / "CHANGED_FILES.txt").write_text(
        "NK_POWERPLANT_FLAG changed files\n\n"
        f"DATA (1 file, 1 object slice)\n  {P_FILE}  Object {OBJ}\n"
        "    Model/Animation Iraq_Powerplant -> NKor_Powerplant (9 tokens / 6 lines)\n\n"
        "ART\n  none (NKor_Powerplant.W3D already in live ART with DPRK_Flag.tga)\n\n"
        "UNCHANGED\n  Iraq_PowerPlant and the other nine country Power Plants\n"
        "  NorthKorea Supply/CommandCenter/WarFactory\n"
        "  Barracks Flag_Hs, shared W3Ds, oil/radar/rosters\n",
        encoding="utf-8",
    )
    (RELEASE / "changelog.txt").write_text(
        """NK_POWERPLANT_FLAG

NorthKorea_PowerPlant last-win pointed at Iraq_Powerplant, whose
FLAG01-03 and BOX08-09 use IraqiFlag.tga. The country clone
NKor_Powerplant.W3D (DPRK_Flag.tga, same geometry) already exists
and is how NK Supply/CC/WF get their flags.

Retargeted the six Model/Animation lines (9 tokens) on
NorthKorea_PowerPlant only. Iraq Power Plant and the other nine
Power Plants unchanged.
""",
        encoding="utf-8",
    )
    (RELEASE / "INSTALL.txt").write_text(
        f"""NK_POWERPLANT_FLAG

Copy _SPEC_DATA_ONE.big over GameRoot. ART BIG is unchanged.

DATA SHA256 {sha}
INGAME_TESTED = NO
""",
        encoding="utf-8",
    )
    (RELEASE / "AUDIT_PRE.txt").write_text(
        """NK_POWERPLANT_FLAG AUDIT (before edits)

Last-win: Data\\INI\\Object\\Specter\\North Korea\\NorthKorea_Systems.ini
  Object NorthKorea_PowerPlant
  Model/Animation = Iraq_Powerplant (3 condition states)
  No HideSubObject, no Flag_Hs

Iraq_Powerplant.W3D: FLAG01-03 + BOX08-09 = IraqiFlag.tga
NKor_Powerplant.W3D: same 62852-byte clone, 189 byte diffs,
  FLAG textures remapped to DPRK_Flag.tga (already in live ART)

NK Supply  = NKor_Supply   (DPRK baked)  — correct
NK CC      = NKr_Command   (DPRK baked)  — correct
NK WF      = NKr_WarFactory(DPRK baked)  — correct
NK PP      = Iraq_Powerplant (Iraqi baked) — BUG

NKr__NKFlag_Hs exists (camp pole). Not used here: NKor_Powerplant
already carries the correct pole + wall flags. Adding Flag_Hs on
Iraq_Powerplant would hide BOX08-09 wall flags and/or duplicate.

Single last-win. Japan/SK/VN Systems.ini do not redefine this object.
""",
        encoding="utf-8",
    )
    print(audit)
    print("PACKED", out, out.stat().st_size, sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
