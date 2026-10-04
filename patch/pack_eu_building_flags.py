#!/usr/bin/env python3
"""EU building flags: 7 countries x 5 US-mesh buildings.

Source DATA: NK_POWERPLANT_FLAG
Source ART:  BUILDING_FLAG_SIZE_CC
Add-only Flag_Hs clones. Shared US_* W3Ds and prior Flag_Hs untouched.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/NK_POWERPLANT_FLAG/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/BUILDING_FLAG_SIZE_CC/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "c035a6c1dabe6dfd064cfa4462d55c7c06bc1691117a5a573e29fa05bc549cad"
EXPECTED_ART_SHA = "b40a8e686df17ffbb538be22ecb17c783a9b6913ab0d3af0d9ef3ed4ebdf7191"
RELEASE = Path("/workspace/patch/Release/EU_BUILDING_FLAGS")
PAYLOAD = RELEASE / "payload"

P_DONOR = r"Art\W3D\Irq__IqFlag_Hs.W3D"
DONOR_NAME = b"IRQ__IQFLAG_HS"
DONOR_TEX = b"IraqiFlag.dds"
PIVOTS = 0x00000102
HALF_POLE = 17.492

# FPOLE (or US_Supply LINE01) + half Flag_Hs pole, same method as Flag_HsCU.
LINE01 = {
    "CU": (61.513, -64.028, 0.767 + HALF_POLE),
    "CP": (-31.496, 4.983, -0.516 + HALF_POLE),
    "WF": (46.895, 13.418, 3.622 + HALF_POLE),
    "PP": (44.359, 14.828, 0.385 + HALF_POLE),
    "SC": (33.267, -28.765, 4.450 + HALF_POLE),
}

HIDE = {
    "CU": "      HideSubObject = F1 F2 F3 FPOLE HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06",
    "CP": "      HideSubObject = F1 F2 F3 FPOLE HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06",
    "WF": "      HideSubObject = F1 F2 F3 FPOLE HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06",
    "PP": "      HideSubObject = F1 F2 F3 FPOLE HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06",
    "SC": "      HideSubObject = F1 F2 F3 HOUSECOLOR01 HOUSECOLOR02 HOUSECOLOR03 LINE01",
}

COUNTRY = {
    "Turkey": ("TR", b"TR_Flag.tga"),
    "Italy": ("IT", b"IT_Flag.tga"),
    "Sweden": ("SE", b"SE_Flag.tga"),
    "Britain": ("UK", b"UK_Flag.tga"),
    "France": ("FR", b"FR_Flag.tga"),
    "Germany": ("DE", b"DE_Flag.tga"),
    "Ukraine": ("UA", b"UA_Flag.tga"),
}

# (packed_path, object_name, country, kind)
TARGETS = [
    (r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\CommandCenter.ini", "TurkeyCommandCenter", "Turkey", "CU"),
    (r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\Warfactory.ini", "TurkeyWarFactory", "Turkey", "WF"),
    (r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\Camp.ini", "TurkeyBootCamp", "Turkey", "CP"),
    (r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\PowerStation.ini", "TurkeyPowerStation", "Turkey", "PP"),
    (r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\SupplyCenter.ini", "TurkeySupplyCenter", "Turkey", "SC"),
    (r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\CommandCenter.ini", "ItalyCommandCenter", "Italy", "CU"),
    (r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\Warfactory.ini", "ItalyWarFactory", "Italy", "WF"),
    (r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\Camp.ini", "ItalyBootCamp", "Italy", "CP"),
    (r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\PowerStation.ini", "ItalyPowerStation", "Italy", "PP"),
    (r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\SupplyCenter.ini", "ItalySupplyCenter", "Italy", "SC"),
    (r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\CommandCenter.ini", "SwedenCommandCenter", "Sweden", "CU"),
    (r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\Warfactory.ini", "SwedenWarFactory", "Sweden", "WF"),
    (r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\Camp.ini", "SwedenBootCamp", "Sweden", "CP"),
    (r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\PowerStation.ini", "SwedenPowerStation", "Sweden", "PP"),
    (r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\SupplyCenter.ini", "SwedenSupplyCenter", "Sweden", "SC"),
    (r"Data\INI\Object\Specter\British Armed Forces\Buildings\CommandCenter.ini", "BritainCommandCenter", "Britain", "CU"),
    (r"Data\INI\Object\Specter\British Armed Forces\Buildings\Warfactory.ini", "BritainWarFactory", "Britain", "WF"),
    (r"Data\INI\Object\Specter\British Armed Forces\Buildings\Camp.ini", "BritainBootCamp", "Britain", "CP"),
    (r"Data\INI\Object\Specter\British Armed Forces\Buildings\PowerStation.ini", "BritainPowerStation", "Britain", "PP"),
    (r"Data\INI\Object\Specter\British Armed Forces\Buildings\SupplyCenter.ini", "BritainSupplyCenter", "Britain", "SC"),
    (r"Data\INI\Object\Specter\French Armed Forces\Buildings\CommandCenter.ini", "FranceCommandCenter", "France", "CU"),
    (r"Data\INI\Object\Specter\French Armed Forces\Buildings\Warfactory.ini", "FranceWarFactory", "France", "WF"),
    (r"Data\INI\Object\Specter\French Armed Forces\Buildings\Camp.ini", "FranceBootCamp", "France", "CP"),
    (r"Data\INI\Object\Specter\French Armed Forces\Buildings\PowerStation.ini", "FrancePowerStation", "France", "PP"),
    (r"Data\INI\Object\Specter\French Armed Forces\Buildings\SupplyCenter.ini", "FranceSupplyCenter", "France", "SC"),
    (r"Data\INI\Object\Specter\German Armed Forces\Buildings\CommandCenter.ini", "GermanyCommandCenter", "Germany", "CU"),
    (r"Data\INI\Object\Specter\German Armed Forces\Buildings\Warfactory.ini", "GermanyWarFactory", "Germany", "WF"),
    (r"Data\INI\Object\Specter\German Armed Forces\Buildings\Camp.ini", "GermanyBootCamp", "Germany", "CP"),
    (r"Data\INI\Object\Specter\German Armed Forces\Buildings\PowerStation.ini", "GermanyPowerStation", "Germany", "PP"),
    (r"Data\INI\Object\Specter\German Armed Forces\Buildings\SupplyCenter.ini", "GermanySupplyCenter", "Germany", "SC"),
    (r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\CommandCenter.ini", "UkraineCommandCenter", "Ukraine", "CU"),
    (r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\Warfactory.ini", "UkraineWarFactory", "Ukraine", "WF"),
    (r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\Camp.ini", "UkraineBootCamp", "Ukraine", "CP"),
    (r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\PowerStation.ini", "UkrainePowerStation", "Ukraine", "PP"),
    (r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\SupplyCenter.ini", "UkraineSupplyCenter", "Ukraine", "SC"),
]

FROZEN_DATA = [
    r"Data\INI\Weapon.ini",
    r"Data\INI\Armor.ini",
    r"Data\INI\Locomotor.ini",
    r"Data\INI\Science.ini",
    r"Data\INI\Upgrade.ini",
    r"Data\INI\SpecialPower.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_SoldierCommand.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_BarracksAndRifles.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\Object\Specter\North Korea\NorthKorea_Systems.ini",
    r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_SupplyCenter.ini",
    r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_CommandCenter.ini",
    r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_WarFactory.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_PowerPlant.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_SupplyCenter.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_CommandCenter.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_CommandCenter.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_Barracks.ini",
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_PowerPlant.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_CommandCenter.ini",
    r"Data\INI\Object\Specter\United States Of America\Buildings\CommandCenter.ini",
    r"Data\INI\Object\Specter\United States Of America\Buildings\Camp.ini",
    r"Data\INI\Object\Specter\United States Of America\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\United States Of America\Buildings\PowerPlant.ini",
    r"Data\INI\Object\Specter\United States Of America\Buildings\SupplyCenter.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Buildings\GM406.ini",
]

PROTECTED_ART = [
    r"Art\W3D\US_Command.W3D",
    r"Art\W3D\US_Camp.W3D",
    r"Art\W3D\US_WarFactory.W3D",
    r"Art\W3D\US_Powerplant.W3D",
    r"Art\W3D\US_PowerplantU.W3D",
    r"Art\W3D\US_Supply.W3D",
    r"Art\W3D\US_COM_Strb.W3D",
    r"Art\W3D\Irq__IqFlag_Hs.W3D",
    r"Art\W3D\IN__INFlag_Hs.W3D",
    r"Art\W3D\IN__INFlag_HsCU.W3D",
    r"Art\W3D\irq_camp.W3D",
    r"Art\W3D\Iraq_Powerplant.W3D",
    r"Art\W3D\NKor_Powerplant.W3D",
    r"Art\Textures\TR_Flag.tga",
    r"Art\Textures\IT_Flag.tga",
    r"Art\Textures\SE_Flag.tga",
    r"Art\Textures\UK_Flag.tga",
    r"Art\Textures\FR_Flag.tga",
    r"Art\Textures\DE_Flag.tga",
    r"Art\Textures\UA_Flag.tga",
]

FROZEN_OBJECTS = [
    "AmericaCommandCenter",
    "AmericaBarracks",
    "AmericaWarFactory",
    "AmericaWarFactory_T",
    "AmericaPowerPlant",
    "AmericaSupplyCenter",
    "India_CommandCenter",
    "India_Barracks",
    "India_PowerPlant",
    "Pakistan_CommandCenter",
    "Japan_CommandCenter",
    "SouthKorea_CommandCenter",
    "Vietnam_CommandCenter",
    "Libya_CommandCenter",
    "Syria_CommandCenter",
    "UAE_CommandCenter",
    "SaudiArabia_CommandCenter",
    "SouthAfrica_CommandCenter",
    "Iraq_PowerPlant",
    "Iraq_Barracks",
    "NorthKorea_PowerPlant",
    "NorthKorea_SupplyCenter",
    "NorthKorea_CommandCenter",
    "NorthKorea_WarFactory",
    "NatoCommandCenter",
    "NatoBootCamp",
    "NatoWarFactory",
    "NatoPowerStation",
    "NatoSupplyCenter",
]

OBJ_RE = re.compile(r"(?im)^Object\s+(\S+)")
DRAW_RE = re.compile(r"(?i)^\s*Draw\s*=")
ANIM_LOOP_RE = re.compile(r"(?i)^\s*AnimationMode\s*=\s*LOOP\s*$")
HIDE_RE = re.compile(r"(?i)^\s*HideSubObject\s*=")
END_RE = re.compile(r"(?i)^\s*End\s*$")


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


def raw_of(entries, target: str) -> bytes:
    return entries[find_index(entries, target)][1]


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


def replace_w3d_names(donor: bytes, old: bytes, new: bytes) -> bytes:
    out = bytearray(donor)
    start = 0
    count = 0
    while True:
        i = out.find(old, start)
        if i < 0:
            break
        nul = out.find(b"\x00", i)
        if nul < 0:
            raise SystemExit(f"unterminated name at {i}")
        cur = bytes(out[i:nul])
        if not cur.startswith(old):
            start = i + 1
            continue
        field_len = 32 if b"." in cur else 16
        old_field = cur + b"\x00" * (field_len - len(cur))
        if bytes(out[i : i + field_len]) != old_field:
            raise SystemExit(f"unexpected name field at {i}")
        replacement = new + cur[len(old) :]
        if len(replacement) + 1 > field_len:
            raise SystemExit(f"renamed field too long: {replacement!r}")
        padded = replacement + b"\x00" * (field_len - len(replacement))
        out[i : i + field_len] = padded
        count += 1
        start = i + field_len
    if count != 19:
        raise SystemExit(f"expected 19 container name fields, got {count}")
    if old in bytes(out) or bytes(out).count(new) != 19:
        raise SystemExit("container rename failed")
    return bytes(out)


def replace_w3d_texture(blob: bytes, old: bytes, new: bytes) -> bytes:
    field_len = len(old) + 1
    new_field = new + b"\x00"
    if len(new_field) > field_len:
        raise SystemExit(f"texture name too long: {new!r}")
    new_field += b"\x00" * (field_len - len(new_field))
    out = bytearray(blob)
    count = 0
    start = 0
    while True:
        i = out.find(old, start)
        if i < 0:
            break
        if i + len(old) < len(out) and out[i + len(old)] == 0:
            out[i : i + field_len] = new_field
            count += 1
            start = i + field_len
        else:
            start = i + 1
    if count != 3 or old in bytes(out) or bytes(out).count(new) != 3:
        raise SystemExit("texture rename failed")
    return bytes(out)


def walk_chunks(blob: bytes, start=0, end=None):
    if end is None:
        end = len(blob)
    pos = start
    while pos + 8 <= end:
        ctype, raw = struct.unpack_from("<II", blob, pos)
        size = raw & 0x7FFFFFFF
        has_sub = bool(raw & 0x80000000)
        ds = pos + 8
        de = min(ds + size, end)
        yield ctype, ds, de, has_sub
        if has_sub:
            yield from walk_chunks(blob, ds, de)
        pos = de


def set_line01(blob: bytes, xyz: tuple[float, float, float]) -> bytes:
    out = bytearray(blob)
    patched = 0
    for ctype, ds, de, has_sub in walk_chunks(out):
        if ctype != PIVOTS or has_sub:
            continue
        for i in range((de - ds) // 60):
            off = ds + i * 60
            name = bytes(out[off : off + 16]).split(b"\x00", 1)[0]
            if name == b"LINE01":
                struct.pack_into("<fff", out, off + 20, *xyz)
                patched += 1
    if patched != 1:
        raise SystemExit(f"LINE01 patch count {patched}")
    return bytes(out)


def read_line01(blob: bytes) -> tuple[float, float, float]:
    for ctype, ds, de, has_sub in walk_chunks(blob):
        if ctype != PIVOTS or has_sub:
            continue
        for i in range((de - ds) // 60):
            off = ds + i * 60
            name = blob[off : off + 16].split(b"\x00", 1)[0]
            if name == b"LINE01":
                return struct.unpack_from("<fff", blob, off + 20)
    raise SystemExit("LINE01 missing")


def make_flag_hs(donor: bytes, new_name: bytes, new_tex: bytes, xyz) -> bytes:
    named = replace_w3d_names(donor, DONOR_NAME, new_name)
    texed = replace_w3d_texture(named, DONOR_TEX, new_tex)
    out = set_line01(texed, xyz)
    if len(out) != len(donor):
        raise SystemExit("W3D size changed")
    if DONOR_NAME in out or DONOR_TEX in out or b"IraqiFlag" in out:
        raise SystemExit("donor leaked into new W3D")
    got = read_line01(out)
    if any(abs(a - b) > 1e-3 for a, b in zip(got, xyz)):
        raise SystemExit(f"LINE01 mismatch {got} vs {xyz}")
    return out


def model_name(country: str, kind: str) -> str:
    prefix = COUNTRY[country][0]
    return f"{prefix}__{prefix}Flag_Hs{kind}"


def hier_name(model: str) -> bytes:
    return model.upper().encode("ascii")


def raw_line(line: str) -> str:
    raw = line[:-1] if line.endswith("\n") else line
    if raw.endswith("\r"):
        raw = raw[:-1]
    return raw


def line_nl(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    return ""


def indent_of(raw: str) -> int:
    return len(raw) - len(raw.lstrip(" \t"))


def draw_spans(lines: list[str]):
    spans = []
    i = 0
    while i < len(lines):
        raw = raw_line(lines[i])
        if DRAW_RE.match(raw):
            indent = indent_of(raw)
            j = i + 1
            while j < len(lines):
                r = raw_line(lines[j])
                if END_RE.match(r) and indent_of(r) == indent:
                    spans.append((i, j))
                    i = j
                    break
                j += 1
            else:
                raise SystemExit("unterminated Draw")
        i += 1
    return spans


def apply_hide(body: str, hide_line: str) -> str:
    lines = body.splitlines(keepends=True)
    spans = draw_spans(lines)
    if not spans:
        raise SystemExit("no Draw to hide")
    first_s, first_e = spans[0]
    tokens = hide_line.split("=", 1)[1].strip()
    out = []
    replaced = 0
    inserted = 0
    for i, line in enumerate(lines):
        raw = raw_line(line)
        if first_s <= i <= first_e and HIDE_RE.match(raw):
            out.append(hide_line + line_nl(line))
            replaced += 1
            continue
        out.append(line)
        if first_s <= i <= first_e and ANIM_LOOP_RE.match(raw) and replaced == 0:
            out.append(hide_line + line_nl(line))
            inserted += 1
    if replaced + inserted < 1:
        raise SystemExit("no HideSubObject applied")
    text = "".join(out)
    if tokens not in text:
        raise SystemExit("hide tokens missing")
    return text


def flag_draw(model: str, nl: str) -> str:
    block = f"""  ; ------------ Flag -----------------
  Draw                = W3DModelDraw ModuleTag_Flag_Hs
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
    if "ModuleTag_Flag_Hs" in body:
        raise SystemExit("Flag_Hs already present")
    if model in body:
        raise SystemExit(f"{model} already in object")
    nl = "\r\n" if "\r\n" in body else "\n"
    lines = body.splitlines(keepends=True)
    spans = draw_spans(lines)
    if not spans:
        raise SystemExit("no Draw for flag insert")
    last_e = spans[-1][1]
    insert_at = last_e + 1
    block = nl + flag_draw(model, nl)
    out = lines[:insert_at] + [block] + lines[insert_at:]
    text = "".join(out)
    if text.count("ModuleTag_Flag_Hs") != 1:
        raise SystemExit("Flag_Hs tag count")
    if "HideSubObject" in text.split("ModuleTag_Flag_Hs", 1)[1]:
        raise SystemExit("HideSubObject leaked into Flag_Hs")
    return text


def patch_object(body: str, country: str, kind: str) -> str:
    model = model_name(country, kind)
    body = apply_hide(body, HIDE[kind])
    body = insert_flag(body, model)
    if model not in body or "ModuleTag_Flag_Hs" not in body:
        raise SystemExit(f"{model} missing after patch")
    tokens = HIDE[kind].split("=", 1)[1].strip()
    if tokens not in body:
        raise SystemExit("hide tokens missing after patch")
    if body.count(model) < 6:
        raise SystemExit(f"{model} ref count {body.count(model)}")
    return body


def main() -> int:
    if sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    data = read_big(SRC_DATA)
    art = read_big(SRC_ART)
    orig_data = list(data)
    orig_art = list(art)
    orig_data_map = {norm(n).lower(): b for n, b in orig_data}
    orig_art_map = {norm(n).lower(): b for n, b in orig_art}
    orig_last = last_objects(orig_data)

    donor = raw_of(art, P_DONOR)
    if len(donor) != 20341:
        raise SystemExit("donor size unexpected")
    cu = raw_of(art, r"Art\W3D\IN__INFlag_HsCU.W3D")
    repro = make_flag_hs(donor, b"IN__INFLAG_HSCU", b"IN_Flag.tga", LINE01["CU"])
    if repro != cu:
        raise SystemExit("clone method no longer matches live IN Flag_HsCU")

    for prefix, tex in COUNTRY.values():
        tpath = rf"Art\Textures\{tex.decode('ascii')}"
        raw_of(art, tpath)

    PAYLOAD.mkdir(parents=True, exist_ok=True)
    new_art_paths = []
    built = {}
    for packed, obj, country, kind in TARGETS:
        prefix, tex = COUNTRY[country]
        model = model_name(country, kind)
        hier = hier_name(model)
        art_path = rf"Art\W3D\{model}.W3D"
        key = norm(art_path).lower()
        if key not in built:
            xyz = LINE01[kind]
            blob = make_flag_hs(donor, hier, tex, xyz)
            built[key] = (art_path, blob)
            dest = PAYLOAD / art_path.replace("\\", "/")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(blob)
            new_art_paths.append(art_path)
            print(f"ART {art_path} LINE01={xyz}")

    if len(built) != 35:
        raise SystemExit(f"expected 35 W3Ds, got {len(built)}")
    for key in built:
        if any(norm(n).lower() == key for n, _ in art):
            raise SystemExit(f"ART name collision: {key}")
    for art_path, blob in built.values():
        art.append((art_path, blob))

    by_file: dict[str, list] = {}
    for packed, obj, country, kind in TARGETS:
        by_file.setdefault(packed, []).append((obj, country, kind))

    changed_paths = []
    for packed, jobs in by_file.items():
        idx = find_index(data, packed)
        old_name, old_blob = data[idx]
        text = old_blob.decode("latin1", errors="replace")
        spans = object_spans(text)
        names = [n for n, _, _ in spans]
        rebuilt = []
        cursor = 0
        for obj, start, end in spans:
            rebuilt.append(text[cursor:start])
            body = text[start:end]
            job = next((j for j in jobs if j[0] == obj), None)
            if job:
                _obj, country, kind = job
                if names.count(obj) != 1:
                    raise SystemExit(f"duplicate object in file: {obj}")
                body = patch_object(body, country, kind)
            rebuilt.append(body)
            cursor = end
        rebuilt.append(text[cursor:])
        new_text = "".join(rebuilt)
        new_spans = object_spans(new_text)
        if [n for n, _, _ in new_spans] != names:
            raise SystemExit(f"object list drifted: {packed}")
        old_map = {n: text[s:e] for n, s, e in spans}
        new_map = {n: new_text[s:e] for n, s, e in new_spans}
        job_names = {j[0] for j in jobs}
        for n in names:
            if n not in job_names and old_map[n] != new_map[n]:
                raise SystemExit(f"non-target object changed: {n} in {packed}")
        new_blob = new_text.encode("latin1")
        dest = PAYLOAD / packed.replace("\\", "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(new_blob)
        data[idx] = (old_name, new_blob)
        changed_paths.append(packed)
        print(f"PATCHED {packed} objs={[j[0] for j in jobs]}")

    if [n for n, _ in data] != [n for n, _ in orig_data]:
        raise SystemExit("DATA path order changed")
    change_set = {norm(p).lower() for p in changed_paths}
    for n, b in data:
        key = norm(n).lower()
        if key in change_set:
            continue
        if b != orig_data_map[key]:
            raise SystemExit(f"unintended DATA rewrite: {n}")
    for p in FROZEN_DATA:
        try:
            idx = find_index(data, p)
        except SystemExit:
            continue
        if data[idx][1] != orig_data_map[norm(p).lower()]:
            raise SystemExit(f"frozen DATA changed: {p}")

    if [n for n, _ in art][: len(orig_art)] != [n for n, _ in orig_art]:
        raise SystemExit("existing ART order changed")
    for n, b in orig_art:
        if raw_of(art, n) != orig_art_map[norm(n).lower()]:
            raise SystemExit(f"existing ART modified: {n}")
    for p in PROTECTED_ART:
        if raw_of(art, p) != orig_art_map[norm(p).lower()]:
            raise SystemExit(f"protected ART changed: {p}")

    last = last_objects(data)
    for packed, obj, country, kind in TARGETS:
        body = last[obj]
        model = model_name(country, kind)
        if body.count("ModuleTag_Flag_Hs") != 1:
            raise SystemExit(f"{obj}: Flag_Hs tag count")
        if model not in body:
            raise SystemExit(f"{obj}: missing {model}")
        tokens = HIDE[kind].split("=", 1)[1].strip()
        if tokens not in body:
            raise SystemExit(f"{obj}: missing hide")
        if "HideSubObject" in body.split("ModuleTag_Flag_Hs", 1)[1]:
            raise SystemExit(f"{obj}: hide leaked into Flag_Hs")
        if not body.strip().endswith("End"):
            raise SystemExit(f"{obj}: missing End")
    for obj in FROZEN_OBJECTS:
        if obj in last and last[obj] != orig_last[obj]:
            raise SystemExit(f"frozen object changed: {obj}")

    RELEASE.mkdir(parents=True, exist_ok=True)
    data_blob = build_big_ordered(data)
    art_blob = build_big_ordered(art)
    data_out = RELEASE / "_SPEC_DATA_ONE.big"
    art_out = RELEASE / "_SPEC_ART_ONE.big"
    data_out.write_bytes(data_blob)
    art_out.write_bytes(art_blob)
    dsha = sha256_file(data_out)
    asha = sha256_file(art_out)

    rows = []
    for packed, obj, country, kind in TARGETS:
        model = model_name(country, kind)
        tex = COUNTRY[country][1].decode("ascii")
        building = {
            "CU": "Command Center",
            "WF": "War Factory",
            "CP": "Camp",
            "PP": "Power Plant",
            "SC": "Supply Center",
        }[kind]
        mesh = {
            "CU": "US_Command",
            "WF": "US_WarFactory",
            "CP": "US_Camp",
            "PP": "US_Powerplant",
            "SC": "US_Supply",
        }[kind]
        rows.append(
            f"{country:8s} | {building:14s} | {obj:24s} | {mesh:14s} | "
            f"US F1/F2/F3 | {model:18s} | {tex:11s} | YES | YES | NO | PASS"
        )

    audit = "\n".join(
        [
            "EU_BUILDING_FLAGS",
            f"SOURCE_DATA_SHA {EXPECTED_DATA_SHA}",
            f"SOURCE_ART_SHA {EXPECTED_ART_SHA}",
            f"DATA_SHA256 {dsha}",
            f"ART_SHA256 {asha}",
            f"DATA_BYTES {data_out.stat().st_size}",
            f"ART_BYTES {art_out.stat().st_size}",
            f"DATA_FILE_COUNT {len(data)}",
            f"ART_FILE_COUNT {len(art)}",
            f"NEW_W3D_COUNT {len(built)}",
            "TARGETS = 35",
            "FIXED = 35",
            "UNRELATED_FILES_CHANGED = NO",
            "USA_UNCHANGED = YES",
            "PRIOR_10_COUNTRY_FLAGS_UNCHANGED = YES",
            "NK_POWERPLANT_UNCHANGED = YES",
            "INGAME_TESTED = NO",
            "STATIC_PACKED_AUDIT = PASS",
        ]
    )
    table = (
        "COUNTRY | BUILDING | OBJECT | BUILDING MODEL | OLD FLAG | NEW FLAG W3D | "
        "FLAG TEXTURE | HIDES US FLAG | NATIONAL FLAG PRESENT | DUPLICATE FLAG | STATUS\n"
        + "\n".join(rows)
    )
    (RELEASE / "audit.txt").write_text(audit + "\n", encoding="utf-8")
    (RELEASE / "POST_PACK_VALIDATION.txt").write_text(audit + "\n\n" + table + "\n", encoding="utf-8")
    (RELEASE / "VALIDATION_TABLE.txt").write_text(table + "\n", encoding="utf-8")
    (RELEASE / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {dsha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {asha}\n"
        f"SOURCE_DATA_SHA {EXPECTED_DATA_SHA}\n"
        f"SOURCE_ART_SHA {EXPECTED_ART_SHA}\n"
        f"DATA_BYTES {data_out.stat().st_size}\n"
        f"ART_BYTES {art_out.stat().st_size}\n",
        encoding="utf-8",
    )
    (RELEASE / "PACKED_FILES.txt").write_text(
        "REPLACED DATA\n"
        + "\n".join(f"  {p}" for p in changed_paths)
        + "\nADDED ART\n"
        + "\n".join(f"  {p}" for p in new_art_paths)
        + "\n",
        encoding="utf-8",
    )
    (RELEASE / "CHANGED_FILES.txt").write_text(
        "EU_BUILDING_FLAGS changed files\n\n"
        "DATA (35 last-win Object files)\n"
        + "\n".join(f"  {p}" for p in changed_paths)
        + "\n\nART (35 add-only Flag_Hs clones; existing ART untouched)\n"
        + "\n".join(f"  {p}" for p in new_art_paths)
        + "\n\nUNCHANGED\n"
        "  USA / Iraq / prior 10-country Flag_Hs / NK Power Plant\n"
        "  Shared US_* W3Ds, Weapon/CommandSet/Upgrade, oil/radar/rosters\n",
        encoding="utf-8",
    )
    (RELEASE / "changelog.txt").write_text(
        """EU_BUILDING_FLAGS

Turkey, Italy, Sweden, Britain, France, Germany, and Ukraine Command
Center / War Factory / Camp / Power Plant / Supply Center last-wins
all used shared US_* meshes (F1/F2/F3 US flag cloth) with no Flag_Hs.

Add-only per-building Flag_Hs clones (Iraq-donor remap + LINE01 on
each US FPOLE / Supply LINE01 + half-pole). Hide F1 F2 F3 FPOLE
HOUSECOLOR04-06 on CU/CP/WF/PP. Hide F1 F2 F3 HOUSECOLOR01-03 LINE01
on Supply. Shared US meshes and prior country Flag_Hs are unchanged.
""",
        encoding="utf-8",
    )
    (RELEASE / "INSTALL.txt").write_text(
        f"""EU_BUILDING_FLAGS

Copy BOTH _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big over GameRoot.

DATA SHA256 {dsha}
ART  SHA256 {asha}
INGAME_TESTED = NO
""",
        encoding="utf-8",
    )
    (RELEASE / "AUDIT_PRE.txt").write_text(
        """EU_BUILDING_FLAGS AUDIT (before edits)

All 35 last-wins share USA meshes and show US F1/F2/F3 cloth.
No TR/IT/SE/UK/FR/DE/UA Flag_Hs W3Ds existed.
Country TGAs already present and visually correct.
ART-only remap of US_* would break USA. DATA Draw + hide required.
""",
        encoding="utf-8",
    )
    print(audit)
    print("PACKED", data_out, art_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
