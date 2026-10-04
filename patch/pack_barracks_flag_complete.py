#!/usr/bin/env python3
"""Complete ten-country Barracks flag fix on the live accepted DATA/ART pair.

DATA source: BARRACKS_FLAG_DEDUP (NATO radar + 8 HideSubObject barracks).
ART source: BUILDING_FLAG_COMPLETE_ROLLOUT (live ART, SHA 493c16d2...).

India/Pakistan: add accepted Flag_Hs poles (Irq__IqFlag_Hs clone + IN/PK_Flag.tga)
and hide irq_camp FLAG01-03. The eight already-patched barracks stay byte-identical.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/BARRACKS_FLAG_DEDUP/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/flag_audit/liveart/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "4f1b5d694739b6f0f1dea391fa13cd6faa5271e74a61c990f624ac1bca07e763"
EXPECTED_ART_SHA = "493c16d2a990cad70d459edbbb6eede963172f433a16f57b241688205a19f314"
RELEASE = Path("/workspace/patch/Release/BARRACKS_FLAG_COMPLETE")
PAYLOAD = RELEASE / "payload"

P_INDIA = r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_Barracks.ini"
P_PAKISTAN = r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_Barracks.ini"
P_DONOR = r"Art\W3D\Irq__IqFlag_Hs.W3D"
P_IN_W3D = r"Art\W3D\IN__INFlag_Hs.W3D"
P_PK_W3D = r"Art\W3D\PK__PKFlag_Hs.W3D"
P_IN_TGA = r"Art\Textures\IN_Flag.tga"
P_PK_TGA = r"Art\Textures\PK_Flag.tga"
P_IRQ_CAMP = r"Art\W3D\irq_camp.W3D"

EIGHT = [
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_Barracks.ini",
    r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_Barracks.ini",
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_Barracks.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_Barracks.ini",
    r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_Barracks.ini",
]

FROZEN = EIGHT + [
    r"Data\INI\Weapon.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\Upgrade.ini",
    r"Data\INI\SpecialPower.ini",
    r"Data\INI\Object\CivilianBuilding.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_Barracks.ini",
    r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_Barracks.ini",
    r"Data\INI\Object\Specter\United States Of America\Buildings\Camp.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_SoldierCommand.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_BarracksAndRifles.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_Class2.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_SAUAESYINPK.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\French Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\GM406.ini",
]

DONOR_NAME = b"IRQ__IQFLAG_HS"
DONOR_TEX = b"IraqiFlag.dds"
HIDE_LINE = "      HideSubObject = FLAG01 FLAG02 FLAG03"
DRAW01_RE = re.compile(r"(?i)^\s*Draw\s*=\s*W3DModelDraw\s+ModuleTag_01\s*$")
DRAW_RE = re.compile(r"(?i)^\s*Draw\s*=")
ANIM_LOOP_RE = re.compile(r"(?i)^\s*AnimationMode\s*=\s*LOOP\s*$")
OBJ_RE = re.compile(r"(?im)^Object\s+(\S+)")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


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
    encoded = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
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


def replace_w3d_names(donor: bytes, old: bytes, new: bytes) -> bytes:
    if len(new) > 15 or len(new) > len(old):
        raise SystemExit(f"bad container name {new!r}")
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


def make_flag_hs(donor: bytes, new_name: bytes, new_tex: bytes) -> bytes:
    named = replace_w3d_names(donor, DONOR_NAME, new_name)
    out = replace_w3d_texture(named, DONOR_TEX, new_tex)
    if len(out) != len(donor):
        raise SystemExit("W3D size changed")
    if DONOR_NAME in out or DONOR_TEX in out or b"IraqiFlag" in out:
        raise SystemExit("donor leaked into new W3D")
    expect = new_name + b"\x00" * (16 - len(new_name))
    if out[20:36] != expect:
        raise SystemExit(f"root container mismatch: {out[20:36]!r}")
    return out


def hide_irq_camp_flags(text: str) -> str:
    if "HideSubObject = FLAG01 FLAG02 FLAG03" in text:
        raise SystemExit("HideSubObject already present")
    lines = text.splitlines(keepends=True)
    out = []
    in_mod01 = False
    inserted = 0
    for line in lines:
        raw = line[:-1] if line.endswith("\n") else line
        if raw.endswith("\r"):
            raw = raw[:-1]
        if DRAW01_RE.match(raw):
            in_mod01 = True
        elif DRAW_RE.match(raw):
            in_mod01 = False
        out.append(line)
        if in_mod01 and ANIM_LOOP_RE.match(raw):
            nl = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
            out.append(HIDE_LINE + nl)
            inserted += 1
    if inserted != 6:
        raise SystemExit(f"expected 6 HideSubObject inserts, got {inserted}")
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


def patch_in_pk(text: str, model: str) -> str:
    if "ModuleTag_03" in text:
        raise SystemExit(f"{model}: already has ModuleTag_03")
    hidden = hide_irq_camp_flags(text)
    nl = "\r\n" if "\r\n" in hidden else "\n"
    m = re.search(r"(?im)^[ \t]*PlacementViewAngle\s*=", hidden)
    if not m:
        raise SystemExit(f"{model}: missing PlacementViewAngle")
    new = hidden[: m.start()] + flag_draw(model, nl) + hidden[m.start() :]
    if new.count("HideSubObject = FLAG01 FLAG02 FLAG03") != 6:
        raise SystemExit(f"{model}: hide count wrong")
    if new.count(model) != 9:
        raise SystemExit(f"{model}: Flag_Hs refs {new.count(model)}")
    if "HideSubObject" in new.split("ModuleTag_03", 1)[1]:
        raise SystemExit(f"{model}: hide leaked into Flag_Hs")
    return new


def last_objects(entries):
    last = {}
    for name, blob in entries:
        if not name.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        ms = list(OBJ_RE.finditer(text))
        for i, m in enumerate(ms):
            end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
            last[m.group(1)] = text[m.start() : end]
    return last


def main() -> int:
    if sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("DEDUP DATA SHA mismatch")
    if sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("live ART SHA mismatch")

    data = read_big(SRC_DATA)
    art = read_big(SRC_ART)
    orig_data = list(data)
    orig_art = list(art)
    orig_data_map = {norm(n).lower(): b for n, b in orig_data}
    orig_art_map = {norm(n).lower(): b for n, b in orig_art}

    donor = raw_of(art, P_DONOR)
    if len(donor) != 20341:
        raise SystemExit("donor Flag_Hs size unexpected")
    jp = raw_of(art, r"Art\W3D\JP__JPFlag_Hs.W3D")
    repro = make_flag_hs(donor, b"JP__JPFLAG_HS", b"JP_Flag.tga")
    if repro != jp:
        raise SystemExit("clone method no longer matches live JP Flag_Hs")

    for tga_path in (P_IN_TGA, P_PK_TGA):
        tga = raw_of(art, tga_path)
        if len(tga) < 18 or tga[2] != 2:
            raise SystemExit(f"{tga_path} is not uncompressed truecolor")

    in_w3d = make_flag_hs(donor, b"IN__INFLAG_HS", b"IN_Flag.tga")
    pk_w3d = make_flag_hs(donor, b"PK__PKFLAG_HS", b"PK_Flag.tga")
    if any(norm(n).lower() == norm(p).lower() for n, _ in art for p in (P_IN_W3D, P_PK_W3D)):
        raise SystemExit("IN/PK Flag_Hs already packed")
    art.append((P_IN_W3D, in_w3d))
    art.append((P_PK_W3D, pk_w3d))

    PAYLOAD.mkdir(parents=True, exist_ok=True)
    for packed, model in ((P_INDIA, "IN__INFlag_Hs"), (P_PAKISTAN, "PK__PKFlag_Hs")):
        idx = find_index(data, packed)
        old_name, old_blob = data[idx]
        new_text = patch_in_pk(old_blob.decode("latin1", errors="replace"), model)
        new_blob = new_text.encode("latin1")
        dest = PAYLOAD / packed.replace("\\", "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(new_blob)
        data[idx] = (old_name, new_blob)
        print(f"PATCHED {packed} {len(old_blob)} -> {len(new_blob)}")

    for p in FROZEN:
        idx = find_index(data, p)
        if data[idx][1] != orig_data_map[norm(p).lower()]:
            raise SystemExit(f"frozen DATA changed: {p}")

    if [n for n, _ in data] != [n for n, _ in orig_data]:
        raise SystemExit("DATA path set/order changed")
    changed = []
    for n, b in data:
        if orig_data_map[norm(n).lower()] != b:
            changed.append(n)
    if {norm(x).lower() for x in changed} != {norm(P_INDIA).lower(), norm(P_PAKISTAN).lower()}:
        raise SystemExit(f"unexpected DATA changes: {changed}")

    for n, b in orig_art:
        if raw_of(art, n) != b:
            raise SystemExit(f"existing ART modified: {n}")
    if raw_of(art, P_IRQ_CAMP) != orig_art_map[norm(P_IRQ_CAMP).lower()]:
        raise SystemExit("irq_camp.W3D modified")
    if raw_of(art, P_DONOR) != donor:
        raise SystemExit("donor Flag_Hs modified")
    if len(art) != len(orig_art) + 2:
        raise SystemExit("ART count unexpected")

    data_blob = build_big_ordered(data)
    art_blob = build_big_ordered(art)
    rebuilt_data = read_big_from_bytes(data_blob)
    rebuilt_art = read_big_from_bytes(art_blob)
    if [n for n, _ in rebuilt_data] != [n for n, _ in data]:
        raise SystemExit("DATA rebuild order drifted")
    if [n for n, _ in rebuilt_art] != [n for n, _ in art]:
        raise SystemExit("ART rebuild order drifted")

    last = last_objects(rebuilt_data)
    expect = {
        "Japan_Barracks": "JP__JPFlag_Hs",
        "SouthKorea_Barracks": "SK__SKFlag_Hs",
        "Vietnam_Barracks": "VN__VNFlag_Hs",
        "Libya_Barracks": "LY__LYFlag_Hs",
        "Syria_Barracks": "SY__SYFlag_Hs",
        "UAE_Barracks": "AE__AEFlag_Hs",
        "SaudiArabia_Barracks": "SA__SAFlag_Hs",
        "SouthAfrica_Barracks": "ZA__ZAFlag_Hs",
        "India_Barracks": "IN__INFlag_Hs",
        "Pakistan_Barracks": "PK__PKFlag_Hs",
    }
    for obj, flag in expect.items():
        body = last[obj]
        if body.count("HideSubObject = FLAG01 FLAG02 FLAG03") != 6:
            raise SystemExit(f"{obj}: hide count")
        if flag not in body or "ModuleTag_03" not in body:
            raise SystemExit(f"{obj}: missing Flag_Hs")
        if "HideSubObject" in body.split("ModuleTag_03", 1)[1]:
            raise SystemExit(f"{obj}: hide leaked")
        if body.count("irq_camp") < 1:
            raise SystemExit(f"{obj}: lost irq_camp")
    for obj in ("Iraq_Barracks", "Egypt_Barracks", "Israel_Barracks"):
        body = last[obj]
        if "HideSubObject" in body or "Flag_Hs" in body:
            raise SystemExit(f"{obj}: unexpectedly patched")

    art_names = {norm(n).lower() for n, _ in rebuilt_art}
    if norm(P_IN_W3D).lower() not in art_names or norm(P_PK_W3D).lower() not in art_names:
        raise SystemExit("packed ART missing IN/PK Flag_Hs")

    RELEASE.mkdir(parents=True, exist_ok=True)
    data_out = RELEASE / "_SPEC_DATA_ONE.big"
    art_out = RELEASE / "_SPEC_ART_ONE.big"
    data_out.write_bytes(data_blob)
    art_out.write_bytes(art_blob)
    data_sha = sha256_file(data_out)
    art_sha = sha256_file(art_out)

    audit = "\n".join(
        [
            "BARRACKS_FLAG_COMPLETE",
            "SOURCE_DATA = BARRACKS_FLAG_DEDUP / NATO_RADAR_USA_REFERENCE_FIX lineage",
            f"SOURCE_DATA_SHA = {EXPECTED_DATA_SHA}",
            f"SOURCE_ART_SHA = {EXPECTED_ART_SHA}",
            f"DATA_SHA256 = {data_sha}",
            f"ART_SHA256 = {art_sha}",
            "TEN_COUNTRY_FLAG_SOURCE = Flag_Hs ModuleTag_03 + HideSubObject FLAG01-03",
            "EIGHT_EXISTING_UNCHANGED = YES",
            "INDIA_PAKISTAN = IN__INFlag_Hs / PK__PKFlag_Hs added",
            "CLONE_METHOD = Irq__IqFlag_Hs container+texture remap (reproduces JP__JPFlag_Hs)",
            "EXISTING_W3D_MODIFIED = NO",
            "IRQ_CAMP_MODIFIED = NO",
            "OTHER_BUILDINGS_UNCHANGED = YES",
            "OIL_CAPTURE_UNCHANGED = YES",
            "FIGHTER_ROSTER_UNCHANGED = YES",
            "NATO_RADAR_UNCHANGED = YES",
            "INGAME_TESTED = NO",
            "STATIC_PACKED_AUDIT = PASS",
        ]
    )
    changelog = """BARRACKS_FLAG_COMPLETE

Completes Barracks national-flag de-dup for all ten target countries.

Eight countries already had Flag_Hs poles + HideSubObject FLAG01-03
from BARRACKS_FLAG_DEDUP. Those eight INIs are byte-identical here.

India and Pakistan had only shared irq_camp (Iraqi FLAG01-03 cloth)
and no Flag_Hs W3D in live ART. irq_camp_IN / irq_camp_PK were stripped
from ART. Safe fix uses the accepted Flag_Hs system:

  - New add-only W3Ds IN__INFlag_Hs / PK__PKFlag_Hs
  - Donor Irq__IqFlag_Hs (unmodified), texture IN_Flag.tga / PK_Flag.tga
  - Clone method byte-reproduces live JP__JPFlag_Hs
  - HideSubObject FLAG01 FLAG02 FLAG03 on irq_camp ConditionStates

Shared irq_camp.W3D, other buildings, oil capture, fighter rosters,
and NATO radar overlays are unchanged.
"""
    changed = """BARRACKS_FLAG_COMPLETE changed files

DATA (2 files)
  Data\\INI\\Object\\Specter\\Indian Armed Forces\\Buildings\\India_Barracks.ini
  Data\\INI\\Object\\Specter\\Pakistan Armed Forces\\Buildings\\Pakistan_Barracks.ini

ART (2 new files)
  Art\\W3D\\IN__INFlag_Hs.W3D
  Art\\W3D\\PK__PKFlag_Hs.W3D

UNCHANGED
  Eight previously patched Barracks INIs
  irq_camp.W3D Irq__IqFlag_Hs.W3D all existing Flag_Hs W3Ds
  Iraq/Egypt/Israel/USA Barracks
  War Factory / Supply / Power / Command Center / Airfield
  Oil-capture, fighter-roster, NATO radar overlays
"""
    install = f"""BARRACKS_FLAG_COMPLETE

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG.
4. Launch Specter.

This ZIP is a complete replacement pair, not an INI-only overlay.

DATA SHA256 {data_sha}
ART  SHA256 {art_sha}

INGAME_TESTED = NO
"""
    (RELEASE / "audit.txt").write_text(audit + "\n", encoding="utf-8")
    (RELEASE / "changelog.txt").write_text(changelog, encoding="utf-8")
    (RELEASE / "CHANGED_FILES.txt").write_text(changed, encoding="utf-8")
    (RELEASE / "INSTALL.txt").write_text(install, encoding="utf-8")
    (RELEASE / "POST_PACK_VALIDATION.txt").write_text(audit + "\n", encoding="utf-8")

    zip_path = RELEASE / "BARRACKS_FLAG_COMPLETE.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_out, "_SPEC_DATA_ONE.big")
        zf.write(art_out, "_SPEC_ART_ONE.big")
        zf.write(RELEASE / "audit.txt", "audit.txt")
        zf.write(RELEASE / "changelog.txt", "changelog.txt")
        zf.write(RELEASE / "INSTALL.txt", "INSTALL.txt")
        zf.write(RELEASE / "CHANGED_FILES.txt", "CHANGED_FILES.txt")
    zip_sha = sha256_file(zip_path)
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}  {data_out.stat().st_size} bytes\n"
        f"_SPEC_ART_ONE.big   SHA256 {art_sha}  {art_out.stat().st_size} bytes\n"
        f"BARRACKS_FLAG_COMPLETE.zip  SHA256 {zip_sha}  {zip_path.stat().st_size} bytes\n"
        f"SOURCE_DATA_SHA {EXPECTED_DATA_SHA}\n"
        f"SOURCE_ART_SHA {EXPECTED_ART_SHA}\n"
    )
    (RELEASE / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    # rewrite zip with SHA256 inside
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_out, "_SPEC_DATA_ONE.big")
        zf.write(art_out, "_SPEC_ART_ONE.big")
        zf.write(RELEASE / "audit.txt", "audit.txt")
        zf.write(RELEASE / "changelog.txt", "changelog.txt")
        zf.write(RELEASE / "INSTALL.txt", "INSTALL.txt")
        zf.write(RELEASE / "CHANGED_FILES.txt", "CHANGED_FILES.txt")
        zf.write(RELEASE / "SHA256.txt", "SHA256.txt")
    zip_sha = sha256_file(zip_path)
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}  {data_out.stat().st_size} bytes\n"
        f"_SPEC_ART_ONE.big   SHA256 {art_sha}  {art_out.stat().st_size} bytes\n"
        f"BARRACKS_FLAG_COMPLETE.zip  SHA256 {zip_sha}  {zip_path.stat().st_size} bytes\n"
        f"SOURCE_DATA_SHA {EXPECTED_DATA_SHA}\n"
        f"SOURCE_ART_SHA {EXPECTED_ART_SHA}\n"
    )
    (RELEASE / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    print("PACKED DATA", data_out.stat().st_size, data_sha)
    print("PACKED ART", art_out.stat().st_size, art_sha)
    print("ZIP", zip_path.stat().st_size, zip_sha)
    print(audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
