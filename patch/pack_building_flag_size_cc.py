#!/usr/bin/env python3
"""Reposition Flag_Hs onto each building pole and hide leftover CC flags.

Source DATA: BUILDING_FLAG_HS_10x4
Source ART:  BARRACKS_FLAG_COMPLETE
Does not modify existing *Flag_Hs.W3D (Barracks) or shared building meshes.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/BUILDING_FLAG_HS_10x4/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/BARRACKS_FLAG_COMPLETE/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "acd4b18d2bd9ab5f42e883dcc50982711ac0f7c80a5cdf9cefab7444336da222"
EXPECTED_ART_SHA = "de5f1e93a20f117a8244a6c1d7ad467b43671628ba05d350fc82ccc446b9d4d3"
RELEASE = Path("/workspace/patch/Release/BUILDING_FLAG_SIZE_CC")
PAYLOAD = RELEASE / "payload"

P_DONOR = r"Art\W3D\Irq__IqFlag_Hs.W3D"
DONOR_NAME = b"IRQ__IQFLAG_HS"
DONOR_TEX = b"IraqiFlag.dds"
PIVOTS = 0x00000102
HALF_POLE = 17.492  # half of Flag_Hs LINE01 mesh (34.984)

# Building-type LINE01 for Flag_Hs clones. Base-pivoted poles get +HALF_POLE Z.
LINE01 = {
    "PP": (-14.342, -32.269, 36.448),
    "SC": (56.662, 29.918, 8.617 + HALF_POLE),
    "WF": (53.595, 36.922, 5.945 + HALF_POLE),
    "CU": (61.513, -64.028, 0.767 + HALF_POLE),  # US_Command FPOLE + half pole
    "CK": (14.259, -10.538, 19.156),  # NKr_Command, same euler as Flag_Hs
}

COUNTRY = {
    "India": ("IN", b"IN_Flag.tga"),
    "Pakistan": ("PK", b"PK_Flag.tga"),
    "SouthKorea": ("SK", b"SK_Flag.tga"),
    "Libya": ("LY", b"LY_Flag.tga"),
    "Syria": ("SY", b"SY_Flag.tga"),
    "UAE": ("AE", b"UAE_Flag.tga"),
    "SaudiArabia": ("SA", b"SA_Flag.tga"),
    "SouthAfrica": ("ZA", b"ZA_Flag.tga"),
    "Japan": ("JP", b"JP_Flag.tga"),
    "Vietnam": ("VN", b"VN_Flag.tga"),
}

HIDE = {
    "PP": "      HideSubObject = FLAG01 FLAG02 FLAG03 BOX08 BOX09 LINE01",
    "SC": "      HideSubObject = FLAG01 FLAG02 FLAG03 LINE01",
    "WF": "      HideSubObject = FLAG01 FLAG02 FLAG03 LINE01",
    "CU": "      HideSubObject = F1 F2 F3 FPOLE HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06",
    "CK": "      HideSubObject = FLAG01 FLAG02 FLAG03 LINE01",
}

# (packed_path, object_name, country, kind)
TARGETS = [
    (r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_PowerPlant.ini", "India_PowerPlant", "India", "PP"),
    (r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_PowerPlant.ini", "Pakistan_PowerPlant", "Pakistan", "PP"),
    (r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_PowerPlant.ini", "Libya_PowerPlant", "Libya", "PP"),
    (r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_PowerPlant.ini", "Syria_PowerPlant", "Syria", "PP"),
    (r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_PowerPlant.ini", "UAE_PowerPlant", "UAE", "PP"),
    (r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_PowerPlant.ini", "SaudiArabia_PowerPlant", "SaudiArabia", "PP"),
    (r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_PowerPlant.ini", "SouthAfrica_PowerPlant", "SouthAfrica", "PP"),
    (r"Data\INI\Object\Specter\Japan Self-Defense Forces\Japan_Systems.ini", "Japan_PowerPlant", "Japan", "PP"),
    (r"Data\INI\Object\Specter\South Korean Armed Forces\SouthKorea_Systems.ini", "SouthKorea_PowerPlant", "SouthKorea", "PP"),
    (r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Vietnam_Systems.ini", "Vietnam_PowerPlant", "Vietnam", "PP"),
    (r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_SupplyCenter.ini", "India_SupplyCenter", "India", "SC"),
    (r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_SupplyCenter.ini", "Pakistan_SupplyCenter", "Pakistan", "SC"),
    (r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_SupplyCenter.ini", "Libya_SupplyCenter", "Libya", "SC"),
    (r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_SupplyCenter.ini", "Syria_SupplyCenter", "Syria", "SC"),
    (r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_SupplyCenter.ini", "UAE_SupplyCenter", "UAE", "SC"),
    (r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_SupplyCenter.ini", "SaudiArabia_SupplyCenter", "SaudiArabia", "SC"),
    (r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_SupplyCenter.ini", "SouthAfrica_SupplyCenter", "SouthAfrica", "SC"),
    (r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_SupplyCenter.ini", "Japan_SupplyCenter", "Japan", "SC"),
    (r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_SupplyCenter.ini", "SouthKorea_SupplyCenter", "SouthKorea", "SC"),
    (r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_SupplyCenter.ini", "Vietnam_SupplyCenter", "Vietnam", "SC"),
    (r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_WarFactory.ini", "India_WarFactory_T", "India", "WF"),
    (r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_WarFactory.ini", "Pakistan_WarFactory_T", "Pakistan", "WF"),
    (r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_WarFactory.ini", "Libya_WarFactory_T", "Libya", "WF"),
    (r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_WarFactory.ini", "Syria_WarFactory_T", "Syria", "WF"),
    (r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_WarFactory.ini", "UAE_WarFactory_T", "UAE", "WF"),
    (r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_WarFactory.ini", "SaudiArabia_WarFactory_T", "SaudiArabia", "WF"),
    (r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_WarFactory.ini", "SouthAfrica_WarFactory_T", "SouthAfrica", "WF"),
    (r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_WarFactory.ini", "Japan_WarFactory", "Japan", "WF"),
    (r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_WarFactory.ini", "SouthKorea_WarFactory", "SouthKorea", "WF"),
    (r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_WarFactory.ini", "Vietnam_WarFactory", "Vietnam", "WF"),
    (r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_CommandCenter.ini", "India_CommandCenter", "India", "CU"),
    (r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_CommandCenter.ini", "Pakistan_CommandCenter", "Pakistan", "CU"),
    (r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_CommandCenter.ini", "Libya_CommandCenter", "Libya", "CU"),
    (r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_CommandCenter.ini", "Syria_CommandCenter", "Syria", "CU"),
    (r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_CommandCenter.ini", "UAE_CommandCenter", "UAE", "CU"),
    (r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_CommandCenter.ini", "SaudiArabia_CommandCenter", "SaudiArabia", "CU"),
    (r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_CommandCenter.ini", "SouthAfrica_CommandCenter", "SouthAfrica", "CU"),
    (r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_CommandCenter.ini", "Japan_CommandCenter", "Japan", "CK"),
    (r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_CommandCenter.ini", "SouthKorea_CommandCenter", "SouthKorea", "CK"),
    (r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_CommandCenter.ini", "Vietnam_CommandCenter", "Vietnam", "CK"),
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

EXISTING_FLAG_HS = [
    r"Art\W3D\Irq__IqFlag_Hs.W3D",
    r"Art\W3D\IN__INFlag_Hs.W3D",
    r"Art\W3D\PK__PKFlag_Hs.W3D",
    r"Art\W3D\SK__SKFlag_Hs.W3D",
    r"Art\W3D\LY__LYFlag_Hs.W3D",
    r"Art\W3D\SY__SYFlag_Hs.W3D",
    r"Art\W3D\AE__AEFlag_Hs.W3D",
    r"Art\W3D\SA__SAFlag_Hs.W3D",
    r"Art\W3D\ZA__ZAFlag_Hs.W3D",
    r"Art\W3D\JP__JPFlag_Hs.W3D",
    r"Art\W3D\VN__VNFlag_Hs.W3D",
    r"Art\W3D\irq_camp.W3D",
    r"Art\W3D\Iraq_Powerplant.W3D",
    r"Art\W3D\Iraq_Supply.W3D",
    r"Art\W3D\NKor_Supply.W3D",
    r"Art\W3D\Irq_WarFactory.W3D",
    r"Art\W3D\NKr_WarFactory.W3D",
    r"Art\W3D\US_Command.W3D",
    r"Art\W3D\NKr_Command.W3D",
]

OBJ_RE = re.compile(r"(?im)^Object\s+(\S+)")
DRAW_RE = re.compile(r"(?i)^\s*Draw\s*=")
ANIM_LOOP_RE = re.compile(r"(?i)^\s*AnimationMode\s*=\s*LOOP\s*$")
HIDE_RE = re.compile(r"(?i)^(\s*)HideSubObject\s*=\s*.+$")


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


def apply_hide(body: str, hide_line: str) -> str:
    lines = body.splitlines(keepends=True)
    out = []
    in_first = False
    seen_draw = False
    replaced = 0
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
        if in_first and HIDE_RE.match(raw):
            nl = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
            out.append(hide_line + nl)
            replaced += 1
            continue
        out.append(line)
        if in_first and ANIM_LOOP_RE.match(raw) and replaced == 0:
            # insert only when this draw has no HideSubObject yet; if some
            # LOOP states already have hide, the replace branch handles them.
            pass
    text = "".join(out)
    if replaced == 0:
        # insert after every LOOP in first draw
        lines = text.splitlines(keepends=True)
        out = []
        in_first = False
        seen_draw = False
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
        text = "".join(out)
    if replaced + inserted < 1:
        raise SystemExit("no HideSubObject applied")
    tokens = hide_line.split("=", 1)[1].strip()
    if tokens not in text:
        raise SystemExit("hide tokens missing")
    return text


def retarget_flag(body: str, old_model: str, new_model: str) -> str:
    if old_model not in body:
        raise SystemExit(f"missing old Flag_Hs {old_model}")
    if "ModuleTag_03" not in body:
        raise SystemExit("missing ModuleTag_03")
    # old camp name is a prefix of the new building name; replace whole tokens only
    token = re.compile(rf"(?<![A-Za-z0-9]){re.escape(old_model)}(?![A-Za-z0-9])")
    old_count = len(token.findall(body))
    if old_count < 1:
        raise SystemExit(f"no standalone Flag_Hs token {old_model}")
    new = token.sub(new_model, body)
    if new.count(new_model) != old_count:
        raise SystemExit("retarget count mismatch")
    if token.search(new):
        raise SystemExit("old Flag_Hs remains")
    return new


def patch_object(body: str, country: str, kind: str) -> str:
    prefix = COUNTRY[country][0]
    old = f"{prefix}__{prefix}Flag_Hs"
    new = model_name(country, kind)
    body = retarget_flag(body, old, new)
    body = apply_hide(body, HIDE[kind])
    if new not in body or "ModuleTag_03" not in body:
        raise SystemExit(f"{new} missing after patch")
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

    donor = raw_of(art, P_DONOR)
    if len(donor) != 20341:
        raise SystemExit("donor size unexpected")
    jp = raw_of(art, r"Art\W3D\JP__JPFlag_Hs.W3D")
    repro = replace_w3d_texture(
        replace_w3d_names(donor, DONOR_NAME, b"JP__JPFLAG_HS"),
        DONOR_TEX,
        b"JP_Flag.tga",
    )
    if repro != jp:
        raise SystemExit("clone method no longer matches live JP Flag_Hs")

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
        for n in names:
            if n not in {j[0] for j in jobs} and old_map[n] != new_map[n]:
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
    for p in BARRACKS_FROZEN + FROZEN_EXTRA:
        if data[find_index(data, p)][1] != orig_data_map[norm(p).lower()]:
            raise SystemExit(f"frozen DATA changed: {p}")

    if [n for n, _ in art][: len(orig_art)] != [n for n, _ in orig_art]:
        raise SystemExit("existing ART order changed")
    for n, b in orig_art:
        if raw_of(art, n) != orig_art_map[norm(n).lower()]:
            raise SystemExit(f"existing ART modified: {n}")
    for p in EXISTING_FLAG_HS:
        if raw_of(art, p) != orig_art_map[norm(p).lower()]:
            raise SystemExit(f"protected ART changed: {p}")

    last = last_objects(data)
    orig_last = last_objects(orig_data)
    for packed, obj, country, kind in TARGETS:
        body = last[obj]
        model = model_name(country, kind)
        if model not in body or "ModuleTag_03" not in body:
            raise SystemExit(f"{obj}: missing {model}")
        tokens = HIDE[kind].split("=", 1)[1].strip()
        if tokens not in body:
            raise SystemExit(f"{obj}: missing hide {tokens}")
        prefix = COUNTRY[country][0]
        camp = f"{prefix}__{prefix}Flag_Hs"
        # camp name is a prefix of the new name; require the new suffix present
        if kind in ("CU",):
            if "F1 F2 F3" not in body:
                raise SystemExit(f"{obj}: US_Command F1-F3 not hidden")
        if obj.endswith("_Barracks"):
            raise SystemExit("barracks in targets")
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
        "Iraq_Barracks",
        "Iraq_PowerPlant",
        "Iraq_CommandCenter",
    ):
        if last[obj] != orig_last[obj]:
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

    audit = "\n".join(
        [
            "BUILDING_FLAG_SIZE_CC",
            f"SOURCE_DATA_SHA {EXPECTED_DATA_SHA}",
            f"SOURCE_ART_SHA {EXPECTED_ART_SHA}",
            f"DATA_SHA256 {dsha}",
            f"ART_SHA256 {asha}",
            f"DATA_BYTES {data_out.stat().st_size}",
            f"ART_BYTES {art_out.stat().st_size}",
            f"DATA_FILE_COUNT {len(data)}",
            f"ART_FILE_COUNT {len(art)}",
            f"NEW_W3D_COUNT {len(built)}",
            "BARRACKS_UNCHANGED = YES",
            "EXISTING_FLAG_HS_UNCHANGED = YES",
            "SHARED_W3D_UNCHANGED = YES",
            "COUNTRIES = India Pakistan SouthKorea Libya Syria UAE SaudiArabia SouthAfrica Japan Vietnam",
            "BUILDINGS = PowerPlant SupplyCenter CommandCenter WarFactory",
            "INGAME_TESTED = NO",
            "STATIC_PACKED_AUDIT = PASS",
        ]
    )
    (RELEASE / "audit.txt").write_text(audit + "\n", encoding="utf-8")
    (RELEASE / "POST_PACK_VALIDATION.txt").write_text(audit + "\n", encoding="utf-8")
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
        "BUILDING_FLAG_SIZE_CC changed files\n\n"
        "DATA (40 last-win files; JP/SK/VN PowerPlant are object-slices)\n"
        + "\n".join(f"  {p}" for p in changed_paths)
        + "\n\nART (40 add-only Flag_Hs clones; existing Flag_Hs untouched)\n"
        + "\n".join(f"  {p}" for p in new_art_paths)
        + "\n\nUNCHANGED\n"
        "  All 10 Barracks last-wins and existing *Flag_Hs.W3D / irq_camp.W3D\n"
        "  Shared building meshes, Iraq/Egypt/Israel/USA, oil/radar/rosters\n",
        encoding="utf-8",
    )
    (RELEASE / "changelog.txt").write_text(
        """BUILDING_FLAG_SIZE_CC

Repositions the accepted Flag_Hs pole onto each building's native flag
location and removes leftover Command Center flags.

Root cause (size): all country Flag_Hs W3Ds are identical camp-sized
clones attached at origin, so they appear at the irq_camp offset instead
of the Power/Supply/CC/WF pole.

Root cause (old CC flags): US_Command cloth is F1/F2/F3 (not FLAG01-03)
and was never hidden. NKr_Command FLAG01-03 were hidden but the native
LINE01 pole and camp-offset Flag_Hs remained.

Fix: add-only per-building Flag_Hs clones (Iraq-donor remap + LINE01
move). Hide F1 F2 F3 FPOLE HOUSECOLOR04-06 on US_Command CCs. Hide
native LINE01 with the previous FLAG cloth hides on the other buildings.
Existing Barracks Flag_Hs W3Ds are not modified.
""",
        encoding="utf-8",
    )
    (RELEASE / "INSTALL.txt").write_text(
        f"""BUILDING_FLAG_SIZE_CC

Copy BOTH _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big over GameRoot.

DATA SHA256 {dsha}
ART  SHA256 {asha}
INGAME_TESTED = NO
""",
        encoding="utf-8",
    )
    print(audit)
    print("PACKED", data_out, art_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
