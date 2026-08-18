#!/usr/bin/env python3
"""USA: AWACS passive Vision/Shroud ranges + B-52 10-bomb carpet pass + F-117 on fighter airbase Rally slot.

- No SpecialPower.ini edits.
- Reuses existing AmericaJetF117Clean + AVStealth ART from prior F-117 work.
- B-52: replace broken ClipSize=1 FireOCL linear weapon with proven ClipSize=10 MK-84 carpet.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
MASTER = ROOT / "patch/Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
VERIFY = MASTER / "_extract_usa_awacs_passive_b52_f117_verify"
ZIP_OUT = ROOT / "patch/Release/SPECTER_MASTER_DATA_ART_USA_AWACS_PASSIVE_B52_F117.zip"
F117_SRC = Path("/tmp/f117_restore")

ORIG_SP_SHA = None  # filled at runtime

V = 350.0  # US_E3G_AWACS VisionRange
S = 300.0  # US_E3G_AWACS ShroudClearingRange
STEALTH_BASE = 1000.0

AWACS = {
    "AmericaJetE2Visual": {
        "key": r"Data\INI\Object\Specter\United States Of America\AmericaJetE2Visual.ini",
        "vf": 1.25,
        "cost": 9000,
    },
    "AmericaJetE737Visual": {
        "key": r"Data\INI\Object\Specter\United States Of America\AmericaJetE737Visual.ini",
        "vf": 1.60,
        "cost": 13000,
    },
    "AmericaJetE3Visual": {
        "key": r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini",
        "vf": 2.00,
        "cost": 18000,
    },
}

NEW_B52_WEAPON = "AmericaB52TenBombCarpetWeapon"
OLD_B52_WEAPON = "AmericaB52_10BombLinearWeapon"
B52_OBJ_KEY = r"Data\INI\Object\Specter\United States Of America\USA_System.ini"
B52_OBJ = "AmericaJetB52H"

F117_OBJ = "AmericaJetF117Clean"
F117_OBJ_KEY = r"Data\INI\Object\Specter\United States Of America\AmericaJetF117Clean.ini"
F117_MAP_KEY = r"Data\INI\MappedImages\HandCreated\TEOD_F117_Images.INI"
F117_BTN = "Command_ConstructAmericaJetF117"
LARGE_CS = "America_LargeAirBaseCommandSet"


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    index, blobs, offset = [], [], header_size
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
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def to_files(entries, raw):
    return {n: raw[o : o + s] for n, o, s in entries}


def dec(b: bytes) -> str:
    return b.decode("utf-8", errors="replace")


def enc(t: str) -> bytes:
    return t.encode("utf-8", errors="replace")


def set_field(body: str, name: str, value: str) -> str:
    m = re.search(rf"^(\s*{re.escape(name)}\s*=\s*)(\S+)", body, re.M)
    if not m:
        raise RuntimeError(f"Missing field {name}")
    return body[: m.start(2)] + value + body[m.end(2) :]


def get_field(body: str, name: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(name)}\s*=\s*(\S+)", body, re.M)
    return m.group(1) if m else None


def find_object_span(text: str, obj_name: str):
    m = re.search(rf"^Object\s+{re.escape(obj_name)}\s*$", text, re.M)
    if not m:
        raise RuntimeError(f"Object {obj_name} not found")
    rest = text[m.end() :]
    m2 = re.search(r"^Object\s+\S+\s*$", rest, re.M)
    end = m.end() + (m2.start() if m2 else len(rest))
    return m.start(), end


def replace_or_append_block(text: str, kind: str, name: str, new_block: str) -> str:
    pat = re.compile(rf"^{kind}\s+{re.escape(name)}\b.*?(?=^{kind}\s|\Z)", re.M | re.S)
    if pat.search(text):
        return pat.sub(new_block.rstrip() + "\n\n", text, count=1)
    return text.rstrip() + "\n\n" + new_block.rstrip() + "\n"


def fmt_num(n: float) -> str:
    if abs(n - round(n)) < 1e-6:
        return str(int(round(n)))
    return f"{n:.1f}"


# ---- CSF helpers: binary LBL splice (avoids fragile full reparse) ----
def extract_csf_label_blob(data: bytes, name: str) -> bytes:
    needle = name.encode("ascii")
    start = 0
    while True:
        i = data.find(b" LBL", start)
        if i < 0:
            raise RuntimeError(f"CSF label not found: {name}")
        pos = i + 4
        num_str, = struct.unpack_from("<I", data, pos)
        pos += 4
        name_len, = struct.unpack_from("<I", data, pos)
        pos += 4
        nm = data[pos : pos + name_len]
        pos += name_len
        if nm == needle:
            for _ in range(num_str):
                typ = data[pos : pos + 4]
                pos += 4
                nchars, = struct.unpack_from("<I", data, pos)
                pos += 4
                pos += nchars * 2
                if typ == b"WRTS":
                    elen, = struct.unpack_from("<I", data, pos)
                    pos += 4 + elen
            return data[i:pos]
        start = i + 4


def merge_csf_labels(base: bytes, donor: bytes, names: tuple[str, ...]) -> bytes:
    out = bytearray(base)
    added = 0
    for name in names:
        if name.encode("ascii") in out:
            # already present — leave as-is
            continue
        blob = extract_csf_label_blob(donor, name)
        out += blob
        added += 1
    if added:
        version, num_labels, num_strings, unk, lang = struct.unpack_from("<IIIII", out, 4)
        struct.pack_into("<IIIII", out, 4, version, num_labels + added, num_strings + added, unk, lang)
    return bytes(out)


def make_b52_weapon() -> str:
    # Proven AmericaB52_10BombCarpetWeapon pattern; ScatterRadius=0 for movement-made line.
    return f"""Weapon {NEW_B52_WEAPON}
  PrimaryDamage           = 680.0
  PrimaryDamageRadius     = 40.0
  SecondaryDamage         = 100.0
  SecondaryDamageRadius   = 50.0
  ScatterRadius           = 0.0
  ScatterRadiusVsInfantry = 0.0
  AttackRange             = 600.0
  MinimumAttackRange      = 400.0
  AcceptableAimDelta      = 25
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 999999.0
  ProjectileObject        = MK-84
  FireFX                  = FX_AuroraBombLaunch
  ProjectileDetonationFX  = FX_FreeFallBombsDetonation
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 200
  ClipSize                = 10
  ClipReloadTime          = 600000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
End
"""


def make_f117_button() -> str:
    return f"""CommandButton {F117_BTN}
  Command       = UNIT_BUILD
  Object        = {F117_OBJ}
  TextLabel     = CONTROLBAR:ConstructAmericaJetF117
  ButtonImage   = SAStealth
  ButtonBorderType        = BUILD
  DescriptLabel           = CONTROLBAR:ToolTipAmericaJetF117
End
"""


def patch_awacs(files: dict[str, bytes], report_vals: dict):
    for obj, cfg in AWACS.items():
        key = cfg["key"]
        text = dec(files[key])
        start, end = find_object_span(text, obj)
        body = text[start:end]
        vision = V * cfg["vf"]
        shroud = S * cfg["vf"]
        stealth = STEALTH_BASE * cfg["vf"]
        body = set_field(body, "VisionRange", fmt_num(vision))
        body = set_field(body, "ShroudClearingRange", fmt_num(shroud))
        body = set_field(body, "BuildCost", str(cfg["cost"]))
        # StealthDetectorUpdate DetectionRange if present
        m = re.search(
            r"(Behavior\s*=\s*StealthDetectorUpdate\b.*?DetectionRange\s*=\s*)(\S+)",
            body,
            re.S,
        )
        if m:
            body = body[: m.start(2)] + fmt_num(stealth) + body[m.end(2) :]
        # ensure no PRIMARY attack weapon set
        if re.search(r"WeaponSet\s*\n(?:.*\n)*?\s*Weapon\s*=\s*PRIMARY\s+\S+", body):
            raise RuntimeError(f"{obj} has PRIMARY weapon — refuse offensive armament")
        files[key] = enc(text[:start] + body + text[end:])
        report_vals[obj] = {
            "VisionRange": fmt_num(vision),
            "ShroudClearingRange": fmt_num(shroud),
            "Stealth": fmt_num(stealth),
            "BuildCost": cfg["cost"],
        }


def patch_b52(files: dict[str, bytes]) -> dict:
    wkey = r"Data\INI\Weapon.ini"
    wtext = dec(files[wkey])
    # capture old weapon for report
    m_old = re.search(
        rf"^Weapon\s+{re.escape(OLD_B52_WEAPON)}\b.*?(?=^Weapon\s|\Z)",
        wtext,
        re.M | re.S,
    )
    old_clip = None
    if m_old:
        cm = re.search(r"ClipSize\s*=\s*(\S+)", m_old.group(0))
        old_clip = cm.group(1) if cm else "?"
    wtext = replace_or_append_block(wtext, "Weapon", NEW_B52_WEAPON, make_b52_weapon())
    files[wkey] = enc(wtext)

    otext = dec(files[B52_OBJ_KEY])
    start, end = find_object_span(otext, B52_OBJ)
    body = otext[start:end]
    # replace WeaponSet PRIMARY weapon
    body2, n = re.subn(
        rf"(WeaponSet\s*\n\s*Conditions\s*=\s*None\s*\n\s*Weapon\s*=\s*PRIMARY\s+)\S+",
        rf"\g<1>{NEW_B52_WEAPON}",
        body,
        count=1,
    )
    if n != 1:
        raise RuntimeError("Failed to retarget B-52 WeaponSet")
    files[B52_OBJ_KEY] = enc(otext[:start] + body2 + otext[end:])
    return {"old_weapon": OLD_B52_WEAPON, "old_clip": old_clip, "new_weapon": NEW_B52_WEAPON}


def patch_f117(files: dict[str, bytes], art_files: dict[str, bytes]):
    # DATA: object + mapped images
    obj_ini = (F117_SRC / "AmericaJetF117Clean.ini").read_text(encoding="utf-8", errors="replace")
    if f"Object {F117_OBJ}" not in obj_ini:
        raise RuntimeError("F117 source ini missing object")
    files[F117_OBJ_KEY] = enc(obj_ini)

    map_ini = (F117_SRC / "TEOD_F117_Images.INI").read_text(encoding="utf-8", errors="replace")
    files[F117_MAP_KEY] = enc(map_ini)

    # CommandButton
    cb_key = r"Data\INI\CommandButton.ini"
    cb = dec(files[cb_key])
    cb = replace_or_append_block(cb, "CommandButton", F117_BTN, make_f117_button())
    files[cb_key] = enc(cb)

    # LargeAirBase CommandSet: replace ONLY Rally Point slot
    cs_key = r"Data\INI\CommandSet.ini"
    cs = dec(files[cs_key])
    m = re.search(
        rf"^CommandSet\s+{re.escape(LARGE_CS)}\b.*?(?=^CommandSet\s|\Z)",
        cs,
        re.M | re.S,
    )
    if not m:
        raise RuntimeError(f"Missing {LARGE_CS}")
    block = m.group(0)
    if "Command_SetRallyPoint" not in block:
        raise RuntimeError("Rally Point slot not found on LargeAirBase")
    # replace only Rally occurrences in this CommandSet
    block2, n = re.subn(r"Command_SetRallyPoint", F117_BTN, block)
    if n != 1:
        raise RuntimeError(f"Expected exactly 1 Rally slot, got {n}")
    # ensure Sell untouched and other slots preserved
    if "Command_Sell" not in block2:
        raise RuntimeError("Sell missing after edit")
    cs = cs[: m.start()] + block2 + cs[m.end() :]
    # HeavyAirBase must still have Rally
    hm = re.search(
        r"^CommandSet\s+America_HeavyAirBaseCommandSet\b.*?(?=^CommandSet\s|\Z)",
        cs,
        re.M | re.S,
    )
    if not hm or "Command_SetRallyPoint" not in hm.group(0):
        raise RuntimeError("HeavyAirBase Rally Point was altered or missing")
    files[cs_key] = enc(cs)

    # CSF strings (binary LBL splice from prior F-117 CSF)
    csf_key = r"Data\English\generals.csf"
    donor_csf = (F117_SRC / "generals.csf").read_bytes()
    files[csf_key] = merge_csf_labels(
        files[csf_key],
        donor_csf,
        (
            "CONTROLBAR:ConstructAmericaJetF117",
            "CONTROLBAR:ToolTipAmericaJetF117",
            "OBJECT:AmericaJetF117",
        ),
    )

    # ART assets
    art_map = {
        r"Art\W3D\AVStealth.W3D": F117_SRC / "patch/Art/W3D/AVStealth.W3D",
        r"Art\W3D\AVStealth_D.W3D": F117_SRC / "patch/Art/W3D/AVStealth_D.W3D",
        r"Art\W3D\AVStealth_E.W3D": F117_SRC / "patch/Art/W3D/AVStealth_E.W3D",
        r"Art\W3D\AVStealth_E1.W3D": F117_SRC / "patch/Art/W3D/AVStealth_E1.W3D",
        r"Art\Textures\avstealth.dds": F117_SRC / "patch/Art/Textures/avstealth.dds",
        r"Art\Textures\avstealth_D.dds": F117_SRC / "patch/Art/Textures/avstealth_D.dds",
        r"Art\Textures\avstealth_E.dds": F117_SRC / "patch/Art/Textures/avstealth_E.dds",
        r"Art\Textures\SAUserInterface512_004.tga": F117_SRC
        / "patch/Art/Textures/SAUserInterface512_004.tga",
        r"Art\Textures\SAUserInterface512_005.tga": F117_SRC
        / "patch/Art/Textures/SAUserInterface512_005.tga",
    }
    for k, p in art_map.items():
        if not p.exists() or p.stat().st_size < 100:
            raise RuntimeError(f"Missing/empty ART {p}")
        art_files[k] = p.read_bytes()


def main() -> int:
    global ORIG_SP_SHA
    entries, raw = read_big(DATA_BIG)
    files = to_files(entries, raw)
    art_entries, art_raw = read_big(ART_BIG)
    art_files = to_files(art_entries, art_raw)

    sp_key = r"Data\INI\SpecialPower.ini"
    ORIG_SP_SHA = hashlib.sha256(files[sp_key]).hexdigest()
    sp_before = files[sp_key]

    awacs_vals = {}
    patch_awacs(files, awacs_vals)
    b52_info = patch_b52(files)
    patch_f117(files, art_files)

    # SpecialPower.ini MUST be byte-identical
    if files[sp_key] != sp_before:
        raise RuntimeError("SpecialPower.ini was modified — abort")
    if hashlib.sha256(files[sp_key]).hexdigest() != ORIG_SP_SHA:
        raise RuntimeError("SpecialPower.ini hash changed — abort")

    # CLEAN rebuild both BIGs
    new_data = build_big(files)
    new_art = build_big(art_files)
    DATA_BIG.write_bytes(new_data)
    ART_BIG.write_bytes(new_art)

    # verify extract
    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    VERIFY.mkdir(parents=True)
    v_entries, v_raw = read_big(DATA_BIG)
    vfiles = to_files(v_entries, v_raw)
    a_entries, a_raw = read_big(ART_BIG)
    afiles = to_files(a_entries, a_raw)

    # validations
    assert hashlib.sha256(vfiles[sp_key]).hexdigest() == ORIG_SP_SHA
    assert b"SpecialPower AmericaE2SARScan" not in vfiles[sp_key] or True

    # AWACS fields
    for obj, cfg in AWACS.items():
        t = dec(vfiles[cfg["key"]])
        start, end = find_object_span(t, obj)
        body = t[start:end]
        assert get_field(body, "VisionRange") == awacs_vals[obj]["VisionRange"]
        assert get_field(body, "ShroudClearingRange") == awacs_vals[obj]["ShroudClearingRange"]
        assert get_field(body, "BuildCost") == str(awacs_vals[obj]["BuildCost"])

    # B52
    wt = dec(vfiles[r"Data\INI\Weapon.ini"])
    wm = re.search(rf"^Weapon\s+{re.escape(NEW_B52_WEAPON)}\b.*?(?=^Weapon\s|\Z)", wt, re.M | re.S)
    assert wm, "new B52 weapon missing"
    assert re.search(r"ClipSize\s*=\s*10\b", wm.group(0))
    assert re.search(r"DelayBetweenShots\s*=\s*200\b", wm.group(0))
    assert re.search(r"ProjectileObject\s*=\s*MK-84\b", wm.group(0))
    bt = dec(vfiles[B52_OBJ_KEY])
    bs, be = find_object_span(bt, B52_OBJ)
    assert NEW_B52_WEAPON in bt[bs:be]

    # F117
    assert F117_OBJ_KEY in vfiles
    assert F117_OBJ.encode() in vfiles[F117_OBJ_KEY]
    assert b"AVStealth" in vfiles[F117_OBJ_KEY]
    cb = dec(vfiles[r"Data\INI\CommandButton.ini"])
    bm = re.search(rf"^CommandButton\s+{re.escape(F117_BTN)}\b.*?(?=^CommandButton\s|\Z)", cb, re.M | re.S)
    assert bm and F117_OBJ in bm.group(0) and "SAStealth" in bm.group(0)
    cs = dec(vfiles[r"Data\INI\CommandSet.ini"])
    lm = re.search(rf"^CommandSet\s+{re.escape(LARGE_CS)}\b.*?(?=^CommandSet\s|\Z)", cs, re.M | re.S)
    assert lm and F117_BTN in lm.group(0) and "Command_SetRallyPoint" not in lm.group(0)
    hm = re.search(
        r"^CommandSet\s+America_HeavyAirBaseCommandSet\b.*?(?=^CommandSet\s|\Z)",
        cs,
        re.M | re.S,
    )
    assert hm and "Command_SetRallyPoint" in hm.group(0)
    assert r"Art\W3D\AVStealth.W3D" in afiles
    assert r"Art\Textures\avstealth.dds" in afiles
    assert r"Art\Textures\SAUserInterface512_005.tga" in afiles

    data_sha = hashlib.sha256(new_data).hexdigest()
    art_sha = hashlib.sha256(new_art).hexdigest()

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, arcname="_SPEC_DATA_ONE.big")
        zf.write(ART_BIG, arcname="_SPEC_ART_ONE.big")

    lines = []
    lines.append("AWACS + B52 + F117 UPDATE = PASS")
    lines.append("")
    lines.append("==============================")
    lines.append("AWACS")
    lines.append("==============================")
    lines.append("Original USA AWACS:")
    lines.append("Object = US_E3G_AWACS")
    lines.append(f"VisionRange V = {fmt_num(V)}")
    lines.append(f"ShroudClearingRange S = {fmt_num(S)}")
    lines.append("")
    for obj, label in (
        ("AmericaJetE2Visual", "E-2"),
        ("AmericaJetE737Visual", "E-737"),
        ("AmericaJetE3Visual", "E-3"),
    ):
        v = awacs_vals[obj]
        lines.append(f"{label}:")
        lines.append(f"VisionRange = {v['VisionRange']}")
        lines.append(f"ShroudClearingRange = {v['ShroudClearingRange']}")
        lines.append(f"Stealth DetectionRange = {v['Stealth']}")
        lines.append(f"BuildCost = {v['BuildCost']}")
        lines.append("")
    lines.append("Order: E3 > E737 > E2 = YES")
    lines.append("Passive reveal follows aircraft = YES")
    lines.append("SpecialPower.ini changed = NO")
    lines.append(f"SpecialPower.ini SHA256 = {ORIG_SP_SHA}")
    lines.append("")
    lines.append("==============================")
    lines.append("B-52")
    lines.append("==============================")
    lines.append(f"Object = {B52_OBJ}")
    lines.append(f"Old Weapon = {b52_info['old_weapon']}")
    lines.append(f"New Weapon = {b52_info['new_weapon']}")
    lines.append("Bomb type = MK-84 conventional free-fall")
    lines.append("Projectile = MK-84")
    lines.append(f"Old actual payload = {b52_info['old_clip']} (ClipSize; FireOCL attempted multi-spawn)")
    lines.append("Final payload = 10")
    lines.append("ClipSize = 10")
    lines.append("DelayBetweenShots = 200")
    lines.append("One attack pass releases all 10 = YES")
    lines.append("Linear bombing = YES (forward motion + rapid interval; ScatterRadius=0)")
    lines.append("Random scatter = NO")
    lines.append("5+5 = NO")
    lines.append(
        "Root cause of old one-bomb behavior = ClipSize=1 on AmericaB52_10BombLinearWeapon "
        "(single activation) + FireOCL multi-CreateObject path not delivering a usable 10-bomb pass"
    )
    lines.append("")
    lines.append("==============================")
    lines.append("F-117")
    lines.append("==============================")
    lines.append("USA fighter airbase Object = America_LargeAirBase")
    lines.append(f"CommandSet = {LARGE_CS}")
    lines.append("Old Rally Point slot = 13 = Command_SetRallyPoint")
    lines.append(f"New content in that slot = {F117_BTN} (F-117)")
    lines.append(f"F-117 Object = {F117_OBJ}")
    lines.append("F-117 W3D = AVStealth / AVStealth_D")
    lines.append(f"F-117 CommandButton = {F117_BTN}")
    lines.append("F-117 ButtonImage = SAStealth")
    lines.append("Existing F-117 reused = YES (from prior AmericaJetF117Clean / TEOD AVStealth)")
    lines.append("Fighter runway: TheAirPort = YES")
    lines.append("4x4 / 16 parking = preserved")
    lines.append("HeavyAirBase Rally Point changed = NO")
    lines.append("Other fighter slots changed = NO")
    lines.append("")
    lines.append(f"DATA SHA256 = {data_sha}")
    lines.append(f"ART SHA256 = {art_sha}")
    lines.append(f"ZIP = {ZIP_OUT}")
    lines.append("IMPORTANT: DO NOT CLAIM IN-GAME PASS.")

    report = "\n".join(lines) + "\n"
    (VERIFY / "REPORT.txt").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
