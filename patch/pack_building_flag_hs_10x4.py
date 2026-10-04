#!/usr/bin/env python3
"""DATA-only Flag_Hs for Power/Supply/CC/WF on the 10 camp-flag countries.

Source: BARRACKS_FLAG_COMPLETE DATA/ART.
Reuses existing country Flag_Hs W3Ds. Does not touch Barracks or shared meshes.
Japan/SK/Vietnam PowerPlant live inside *_Systems.ini — only that object is patched.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/BARRACKS_FLAG_COMPLETE/_SPEC_DATA_ONE.big")
EXPECTED_DATA_SHA = "41064996aa6e3889719e45e5c1e1df687913a600102cc1429e8af6214a3db567"
RELEASE = Path("/workspace/patch/Release/BUILDING_FLAG_HS_10x4")
PAYLOAD = RELEASE / "payload"

FLAG = {
    "India": "IN__INFlag_Hs",
    "Pakistan": "PK__PKFlag_Hs",
    "SouthKorea": "SK__SKFlag_Hs",
    "Libya": "LY__LYFlag_Hs",
    "Syria": "SY__SYFlag_Hs",
    "UAE": "AE__AEFlag_Hs",
    "SaudiArabia": "SA__SAFlag_Hs",
    "SouthAfrica": "ZA__ZAFlag_Hs",
    "Japan": "JP__JPFlag_Hs",
    "Vietnam": "VN__VNFlag_Hs",
}

# (packed_path, object_name, country, hide_line or None, already_has_flag)
# hide_line None = US_Command (no FLAG cloth)
POWER_HIDE = "      HideSubObject = FLAG01 FLAG02 FLAG03 BOX08 BOX09"
CLOTH_HIDE = "      HideSubObject = FLAG01 FLAG02 FLAG03"

TARGETS = [
    # Power
    (r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_PowerPlant.ini", "India_PowerPlant", "India", POWER_HIDE, False),
    (r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_PowerPlant.ini", "Pakistan_PowerPlant", "Pakistan", POWER_HIDE, False),
    (r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_PowerPlant.ini", "Libya_PowerPlant", "Libya", POWER_HIDE, True),
    (r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_PowerPlant.ini", "Syria_PowerPlant", "Syria", POWER_HIDE, True),
    (r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_PowerPlant.ini", "UAE_PowerPlant", "UAE", POWER_HIDE, True),
    (r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_PowerPlant.ini", "SaudiArabia_PowerPlant", "SaudiArabia", POWER_HIDE, True),
    (r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_PowerPlant.ini", "SouthAfrica_PowerPlant", "SouthAfrica", POWER_HIDE, True),
    (r"Data\INI\Object\Specter\Japan Self-Defense Forces\Japan_Systems.ini", "Japan_PowerPlant", "Japan", POWER_HIDE, False),
    (r"Data\INI\Object\Specter\South Korean Armed Forces\SouthKorea_Systems.ini", "SouthKorea_PowerPlant", "SouthKorea", POWER_HIDE, True),
    (r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Vietnam_Systems.ini", "Vietnam_PowerPlant", "Vietnam", POWER_HIDE, False),
    # Supply
    (r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_SupplyCenter.ini", "India_SupplyCenter", "India", CLOTH_HIDE, False),
    (r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_SupplyCenter.ini", "Pakistan_SupplyCenter", "Pakistan", CLOTH_HIDE, False),
    (r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_SupplyCenter.ini", "Libya_SupplyCenter", "Libya", CLOTH_HIDE, True),
    (r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_SupplyCenter.ini", "Syria_SupplyCenter", "Syria", CLOTH_HIDE, True),
    (r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_SupplyCenter.ini", "UAE_SupplyCenter", "UAE", CLOTH_HIDE, True),
    (r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_SupplyCenter.ini", "SaudiArabia_SupplyCenter", "SaudiArabia", CLOTH_HIDE, True),
    (r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_SupplyCenter.ini", "SouthAfrica_SupplyCenter", "SouthAfrica", CLOTH_HIDE, True),
    (r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_SupplyCenter.ini", "Japan_SupplyCenter", "Japan", CLOTH_HIDE, False),
    (r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_SupplyCenter.ini", "SouthKorea_SupplyCenter", "SouthKorea", CLOTH_HIDE, True),
    (r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_SupplyCenter.ini", "Vietnam_SupplyCenter", "Vietnam", CLOTH_HIDE, False),
    # War Factory
    (r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_WarFactory.ini", "India_WarFactory_T", "India", CLOTH_HIDE, False),
    (r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_WarFactory.ini", "Pakistan_WarFactory_T", "Pakistan", CLOTH_HIDE, False),
    (r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_WarFactory.ini", "Libya_WarFactory_T", "Libya", CLOTH_HIDE, True),
    (r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_WarFactory.ini", "Syria_WarFactory_T", "Syria", CLOTH_HIDE, True),
    (r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_WarFactory.ini", "UAE_WarFactory_T", "UAE", CLOTH_HIDE, True),
    (r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_WarFactory.ini", "SaudiArabia_WarFactory_T", "SaudiArabia", CLOTH_HIDE, True),
    (r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_WarFactory.ini", "SouthAfrica_WarFactory_T", "SouthAfrica", CLOTH_HIDE, True),
    (r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_WarFactory.ini", "Japan_WarFactory", "Japan", CLOTH_HIDE, False),
    (r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_WarFactory.ini", "SouthKorea_WarFactory", "SouthKorea", CLOTH_HIDE, True),
    (r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_WarFactory.ini", "Vietnam_WarFactory", "Vietnam", CLOTH_HIDE, False),
    # Command Center
    (r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_CommandCenter.ini", "India_CommandCenter", "India", None, False),
    (r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_CommandCenter.ini", "Pakistan_CommandCenter", "Pakistan", None, False),
    (r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_CommandCenter.ini", "Libya_CommandCenter", "Libya", None, False),
    (r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_CommandCenter.ini", "Syria_CommandCenter", "Syria", None, False),
    (r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_CommandCenter.ini", "UAE_CommandCenter", "UAE", None, False),
    (r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_CommandCenter.ini", "SaudiArabia_CommandCenter", "SaudiArabia", None, False),
    (r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_CommandCenter.ini", "SouthAfrica_CommandCenter", "SouthAfrica", None, False),
    (r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_CommandCenter.ini", "Japan_CommandCenter", "Japan", CLOTH_HIDE, False),
    (r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_CommandCenter.ini", "SouthKorea_CommandCenter", "SouthKorea", CLOTH_HIDE, True),
    (r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_CommandCenter.ini", "Vietnam_CommandCenter", "Vietnam", CLOTH_HIDE, False),
]

BARRACKS_FROZEN = [
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_Barracks.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_Barracks.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_Barracks.ini",
    r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_Barracks.ini",
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_Barracks.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_Barracks.ini",
    r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_Barracks.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_Barracks.ini",
]

FROZEN_EXTRA = [
    r"Data\INI\Weapon.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\Upgrade.ini",
    r"Data\INI\SpecialPower.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_SoldierCommand.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_BarracksAndRifles.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_PowerPlant.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_SupplyCenter.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_CommandCenter.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory.ini",
]

OBJ_RE = re.compile(r"(?im)^Object\s+(\S+)")
DRAW_RE = re.compile(r"(?i)^\s*Draw\s*=")
ANIM_LOOP_RE = re.compile(r"(?i)^\s*AnimationMode\s*=\s*LOOP\s*$")


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
    return read_big_from_bytes(data)


def read_big_from_bytes(data: bytes):
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


def hide_first_draw(body: str, hide_line: str) -> str:
    if hide_line.split("=", 1)[1].strip() in body and "HideSubObject" in body:
        # already hidden with same tokens
        if hide_line.strip() in body.replace("\r\n", "\n"):
            return body
    lines = body.splitlines(keepends=True)
    out = []
    in_first = False
    seen_draw = False
    inserted = 0
    for line in lines:
        raw = line[:-1] if line.endswith("\n") else line
        if raw.endswith("\r"):
            raw = raw[:-1]
        if DRAW_RE.match(raw):
            if not seen_draw:
                in_first = True
                seen_draw = True
            else:
                in_first = False
        out.append(line)
        if in_first and ANIM_LOOP_RE.match(raw):
            nl = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
            out.append(hide_line + nl)
            inserted += 1
    if inserted < 1:
        raise SystemExit(f"no HideSubObject inserts (got {inserted})")
    return "".join(out)


def flag_draw(model: str, nl: str) -> str:
    block = f"""  ; ------------ Flag -----------------
  Draw                = W3DModelDraw ModuleTag_03
    ConditionState    = None
      Model           = {model}
      Animation       = {model}.{model}
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT
    AliasConditionState = SNOW
    AliasConditionState = NIGHT SNOW
    
    ConditionState    = DAMAGED
      Model           = {model}
      Animation       = {model}.{model}
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT DAMAGED
    AliasConditionState = SNOW DAMAGED
    AliasConditionState = NIGHT SNOW DAMAGED
    
    ConditionState    = REALLYDAMAGED RUBBLE
      Model           = {model}
      Animation       = {model}.{model}
      AnimationMode   = LOOP
    End
  End
"""
    return block.replace("\n", nl)


def insert_flag(body: str, model: str) -> str:
    if "ModuleTag_03" in body and model in body:
        return body
    if model in body and "ModuleTag_03" in body:
        return body
    nl = "\r\n" if "\r\n" in body else "\n"
    m = re.search(r"(?im)^[ \t]*PlacementViewAngle\s*=", body)
    if not m:
        raise SystemExit(f"missing PlacementViewAngle for {model}")
    return body[: m.start()] + flag_draw(model, nl) + body[m.start() :]


def patch_object(body: str, model: str, hide_line: str | None, already_has_flag: bool) -> str:
    if hide_line:
        body = hide_first_draw(body, hide_line)
    if not already_has_flag:
        body = insert_flag(body, model)
    elif model not in body:
        raise SystemExit(f"expected existing Flag_Hs {model}")
    if model not in body:
        raise SystemExit(f"Flag_Hs missing after patch: {model}")
    if hide_line and hide_line.split("=", 1)[1].strip() not in body:
        raise SystemExit("hide tokens missing after patch")
    if hide_line and "HideSubObject" in body.split("ModuleTag_03", 1)[-1]:
        # Flag_Hs draw must not contain hide
        flag_part = body.split("Draw                = W3DModelDraw ModuleTag_03", 1)
        if len(flag_part) == 2 and "HideSubObject" in flag_part[1].split("PlacementViewAngle", 1)[0]:
            raise SystemExit("HideSubObject leaked into Flag_Hs")
    return body


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

    entries = read_big(SRC_DATA)
    orig = list(entries)
    orig_map = {norm(n).lower(): (n, b) for n, b in orig}

    # apply per unique file
    by_file: dict[str, list] = {}
    for packed, obj, country, hide, has_flag in TARGETS:
        by_file.setdefault(packed, []).append((obj, country, hide, has_flag))

    PAYLOAD.mkdir(parents=True, exist_ok=True)
    changed_paths = []
    for packed, jobs in by_file.items():
        idx = find_index(entries, packed)
        old_name, old_blob = entries[idx]
        text = old_blob.decode("latin1", errors="replace")
        spans = object_spans(text)
        names = [n for n, _, _ in spans]
        new_text = text
        # patch from the end so offsets stay valid if we rebuild from original spans
        rebuilt = []
        cursor = 0
        for obj, start, end in spans:
            rebuilt.append(text[cursor:start])
            body = text[start:end]
            job = next((j for j in jobs if j[0] == obj), None)
            if job:
                _obj, country, hide, has_flag = job
                body = patch_object(body, FLAG[country], hide, has_flag)
            rebuilt.append(body)
            cursor = end
        rebuilt.append(text[cursor:])
        new_text = "".join(rebuilt)
        # non-target objects in this file must be unchanged
        new_spans = object_spans(new_text)
        if [n for n, _, _ in new_spans] != names:
            raise SystemExit(f"object list drifted: {packed}")
        old_map = {n: text[s:e] for n, s, e in spans}
        new_map = {n: new_text[s:e] for n, s, e in new_spans}
        for n in names:
            if n not in {j[0] for j in jobs} and old_map[n] != new_map[n]:
                raise SystemExit(f"non-target object changed: {n} in {packed}")
        new_blob = new_text.encode("latin1")
        dest = PAYLOAD / packed.replace("\\", "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(new_blob)
        entries[idx] = (old_name, new_blob)
        changed_paths.append(packed)
        print(f"PATCHED {packed} {len(old_blob)} -> {len(new_blob)} objs={[j[0] for j in jobs]}")

    if [n for n, _ in entries] != [n for n, _ in orig]:
        raise SystemExit("DATA path order changed")

    change_set = {norm(p).lower() for p in changed_paths}
    for n, b in entries:
        key = norm(n).lower()
        if key in change_set:
            continue
        if b != orig_map[key][1]:
            raise SystemExit(f"unintended rewrite: {n}")

    for p in BARRACKS_FROZEN + FROZEN_EXTRA:
        idx = find_index(entries, p)
        if entries[idx][1] != orig_map[norm(p).lower()][1]:
            raise SystemExit(f"frozen changed: {p}")

    data_blob = build_big_ordered(entries)
    rebuilt = read_big_from_bytes(data_blob)
    last = last_objects(rebuilt)

    expect_objs = {
        "India_PowerPlant": ("IN__INFlag_Hs", True),
        "Pakistan_PowerPlant": ("PK__PKFlag_Hs", True),
        "Libya_PowerPlant": ("LY__LYFlag_Hs", True),
        "Syria_PowerPlant": ("SY__SYFlag_Hs", True),
        "UAE_PowerPlant": ("AE__AEFlag_Hs", True),
        "SaudiArabia_PowerPlant": ("SA__SAFlag_Hs", True),
        "SouthAfrica_PowerPlant": ("ZA__ZAFlag_Hs", True),
        "Japan_PowerPlant": ("JP__JPFlag_Hs", True),
        "SouthKorea_PowerPlant": ("SK__SKFlag_Hs", True),
        "Vietnam_PowerPlant": ("VN__VNFlag_Hs", True),
        "India_SupplyCenter": ("IN__INFlag_Hs", True),
        "Pakistan_SupplyCenter": ("PK__PKFlag_Hs", True),
        "Libya_SupplyCenter": ("LY__LYFlag_Hs", True),
        "Syria_SupplyCenter": ("SY__SYFlag_Hs", True),
        "UAE_SupplyCenter": ("AE__AEFlag_Hs", True),
        "SaudiArabia_SupplyCenter": ("SA__SAFlag_Hs", True),
        "SouthAfrica_SupplyCenter": ("ZA__ZAFlag_Hs", True),
        "Japan_SupplyCenter": ("JP__JPFlag_Hs", True),
        "SouthKorea_SupplyCenter": ("SK__SKFlag_Hs", True),
        "Vietnam_SupplyCenter": ("VN__VNFlag_Hs", True),
        "India_WarFactory_T": ("IN__INFlag_Hs", True),
        "Pakistan_WarFactory_T": ("PK__PKFlag_Hs", True),
        "Libya_WarFactory_T": ("LY__LYFlag_Hs", True),
        "Syria_WarFactory_T": ("SY__SYFlag_Hs", True),
        "UAE_WarFactory_T": ("AE__AEFlag_Hs", True),
        "SaudiArabia_WarFactory_T": ("SA__SAFlag_Hs", True),
        "SouthAfrica_WarFactory_T": ("ZA__ZAFlag_Hs", True),
        "Japan_WarFactory": ("JP__JPFlag_Hs", True),
        "SouthKorea_WarFactory": ("SK__SKFlag_Hs", True),
        "Vietnam_WarFactory": ("VN__VNFlag_Hs", True),
        "India_CommandCenter": ("IN__INFlag_Hs", False),
        "Pakistan_CommandCenter": ("PK__PKFlag_Hs", False),
        "Libya_CommandCenter": ("LY__LYFlag_Hs", False),
        "Syria_CommandCenter": ("SY__SYFlag_Hs", False),
        "UAE_CommandCenter": ("AE__AEFlag_Hs", False),
        "SaudiArabia_CommandCenter": ("SA__SAFlag_Hs", False),
        "SouthAfrica_CommandCenter": ("ZA__ZAFlag_Hs", False),
        "Japan_CommandCenter": ("JP__JPFlag_Hs", True),
        "SouthKorea_CommandCenter": ("SK__SKFlag_Hs", True),
        "Vietnam_CommandCenter": ("VN__VNFlag_Hs", True),
    }
    for obj, (flag, expect_hide) in expect_objs.items():
        body = last.get(obj)
        if not body:
            raise SystemExit(f"missing last-win {obj}")
        if flag not in body or "ModuleTag_03" not in body:
            raise SystemExit(f"{obj}: missing Flag_Hs {flag}")
        hides = body.count("HideSubObject")
        if expect_hide and hides < 1:
            raise SystemExit(f"{obj}: missing HideSubObject")
        if not expect_hide and hides != 0:
            raise SystemExit(f"{obj}: unexpected HideSubObject")

    for obj in (
        "India_Barracks",
        "Pakistan_Barracks",
        "Japan_Barracks",
        "Iraq_Barracks",
        "Iraq_PowerPlant",
        "Iraq_CommandCenter",
    ):
        if last[obj] != last_objects(orig)[obj] and obj.startswith("Iraq"):
            raise SystemExit(f"{obj} changed")
    orig_last = last_objects(orig)
    for obj in (
        "India_Barracks",
        "Pakistan_Barracks",
        "Japan_Barracks",
        "SouthKorea_Barracks",
        "Vietnam_Barracks",
        "Libya_Barracks",
        "Syria_Barracks",
        "UAE_Barracks",
        "SaudiArabia_Barracks",
        "SouthAfrica_Barracks",
    ):
        if last[obj] != orig_last[obj]:
            raise SystemExit(f"barracks changed: {obj}")

    RELEASE.mkdir(parents=True, exist_ok=True)
    out = RELEASE / "_SPEC_DATA_ONE.big"
    out.write_bytes(data_blob)
    sha = sha256_file(out)
    audit = "\n".join(
        [
            "BUILDING_FLAG_HS_10x4",
            f"SOURCE_DATA_SHA {EXPECTED_DATA_SHA}",
            f"DATA_SHA256 {sha}",
            f"BYTES {out.stat().st_size}",
            f"FILE_COUNT {len(entries)}",
            "ART_CHANGED = NO",
            "BARRACKS_UNCHANGED = YES",
            "SHARED_W3D_UNCHANGED = YES",
            "NEW_W3D_COUNT = 0",
            "COUNTRIES = India Pakistan SouthKorea Libya Syria UAE SaudiArabia SouthAfrica Japan Vietnam",
            "BUILDINGS = PowerPlant SupplyCenter CommandCenter WarFactory",
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
        "REPLACED\n" + "\n".join(f"  {p}" for p in changed_paths) + "\nART_CHANGED = NO\n",
        encoding="utf-8",
    )
    (RELEASE / "changelog.txt").write_text(
        """BUILDING_FLAG_HS_10x4

Applies the accepted Barracks Flag_Hs method to Power Plant, Supply
Centre, Command Center, and War Factory for the same 10 countries.

Reuses existing country Flag_Hs W3Ds. No new ART clones.
Hides baked FLAG01-03 (and Power Plant BOX08-09) on shared meshes
via country-object HideSubObject only. irq_camp and Barracks unchanged.

US_Command CCs have no FLAG cloth; a Flag_Hs pole is added the same
way as SouthKorea_CommandCenter. FPOLE is not hidden.
""",
        encoding="utf-8",
    )
    (RELEASE / "INSTALL.txt").write_text(
        f"""BUILDING_FLAG_HS_10x4

Copy _SPEC_DATA_ONE.big over GameRoot. ART BIG is unchanged.

DATA SHA256 {sha}
INGAME_TESTED = NO
""",
        encoding="utf-8",
    )
    print("PACKED", out, out.stat().st_size, sha)
    print(audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
