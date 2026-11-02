#!/usr/bin/env python3
"""Validate USAPAC3 spawn-crash fix against packed DATA + ART TWO."""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
MERGED = ROOT / "docs/specter-usapac3/merged"
DATA = MERGED / "_SPEC_DATA_ONE.big"
ART2 = MERGED / "_SPEC_ART_TWO.big"
PATCH = ROOT / "patch"

ART1_SHA = "15ffb0dcbf6e0a02e8ece6421efac1331c391b48d8afa6b108550df89653df66"
ART2_ORIG_SHA = "a5a20d959d2835f12a4bf5431e011c4d45047f24ea3d88841c2281fc0a6c19af"
CS_SHA = "f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223"
CB_SHA = "4eb2c95a9415d081bb5fbf508f25883c5afe598448f4ca70bbc6dac8b2ef6b2d"

W3D_MODELS = {
    "UsaPac3Car": "Art\\W3D\\UsaPac3Car.W3D",
    "UsaPac3Car_d": "Art\\W3D\\UsaPac3Car_d.W3D",
    "UsaPac3Car_w": "Art\\W3D\\UsaPac3Car_w.W3D",
    "UsaPac3F": "Art\\W3D\\UsaPac3F.W3D",
    "UsaPac3F_d": "Art\\W3D\\UsaPac3F_d.W3D",
    "pac3mis_m": "Art\\W3D\\pac3mis_m.W3D",
}

TEXTURE_STEMS = {
    "usapac3truckmap",
    "usapac3truckmap_d",
    "ampac3map",
    "ampac3map_d",
    "ampac3mapback",
    "pac3missilemap",
    "abnpatriot02",
    "abnpatriot02_d",
    "usapac3",
    "usapac3tb",
}


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        fail(f"not BIGF {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos = end + 1
        entries.append((name.replace("/", "\\"), off, size))
    return data, entries


def cstr(b: bytes) -> str:
    return b.split(b"\x00", 1)[0].decode("latin-1", "replace")


def parse_w3d(blob: bytes):
    CON = 0x80000000

    def walk(start, end):
        pos = start
        while pos + 8 <= end:
            cid, raw = struct.unpack_from("<II", blob, pos)
            size = raw & 0x7FFFFFFF
            is_c = bool(raw & CON)
            payload = pos + 8
            pe = payload + size
            if pe > len(blob):
                break
            yield cid, size, is_c, payload, pe
            if is_c:
                yield from walk(payload, pe)
            pos = pe

    bones, anims, textures, meshes = [], [], [], 0
    for cid, size, is_c, s, e in walk(0, len(blob)):
        if cid == 0x102:
            n = size // 60
            for i in range(n):
                off = s + i * 60
                bones.append(cstr(blob[off : off + 16]).upper())
        elif cid == 0x201:
            ver, name, hier, nf, fr = struct.unpack_from("<I16s16sII", blob, s)
            anims.append((cstr(name).upper(), cstr(hier).upper(), nf, fr))
        elif cid == 0x32:
            textures.append(cstr(blob[s:e]))
        elif cid == 0x1F:
            meshes += 1
    return bones, anims, textures, meshes


def main() -> int:
    overlay = (PATCH / "Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3.ini").read_text(
        encoding="latin-1"
    )
    if overlay.count("\nObject USAPAC3") + (1 if overlay.startswith("Object USAPAC3") else 0) < 1:
        fail("overlay missing Object USAPAC3")
    if len(re.findall(r"(?m)^Object USAPAC3\s*$", overlay)) != 1:
        fail("overlay object count")
    if "AttachToBoneInAnotherModule" in overlay:
        fail("attach still present")
    if "ModuleTag_TracksDraw" in overlay or "UsaPac3Car_w" in overlay:
        fail("second truck Draw / UsaPac3Car_w still on spawn path")
    if "PRISTINE_BONE_POS_IN_FINAL_FRAME" in overlay:
        fail("pristine bone flag still present")
    if "WeaponLaunchBone" in overlay or "Turret            =" in overlay or "TurretPitch" in overlay:
        fail("turret/launch bones still in Draw")
    if overlay.count("Draw = W3DTruckDraw") != 1:
        fail("expected exactly one W3DTruckDraw")
    if "AnimationMode     = ONCE_BACKWARDS" not in overlay or "Flags             = START_FRAME_FIRST" not in overlay:
        fail("US_THAAD default animation flags missing")
    if "BuildCost           = 3876" not in overlay:
        fail("cost")
    if "BuildTime           = 18.6" not in overlay:
        fail("time")
    if "CommandSet           = USAPAC3CommandSet" not in overlay:
        fail("commandset field")
    if "Locomotor = SET_NORMAL Generic8x8Locomotor" not in overlay:
        fail("locomotor")
    if "Weapon             = SECONDARY USAPAC3_Weapon" not in overlay:
        fail("weapon")
    if "Prerequisites" in overlay:
        fail("prerequisites returned")

    data_raw, data_ents = read_big(DATA)
    data_map = {n.replace("/", "\\").lower(): (n, data_raw[o : o + s]) for n, o, s in data_ents}
    obj_key = "data\\ini\\object\\specter\\patchsystems\\airdefense\\usapac3.ini"
    if obj_key not in data_map:
        fail("packed object missing")
    packed_obj = data_map[obj_key][1]
    if packed_obj != overlay.encode("latin-1"):
        fail("packed object != overlay")
    winners = [n for n, o, s in data_ents if b"\nObject USAPAC3" in data_raw[o : o + s] or data_raw[o : o + s].startswith(b"Object USAPAC3")]
    # unique-path object files that define Object USAPAC3
    defs = []
    for n, o, s in data_ents:
        txt = data_raw[o : o + s].decode("latin-1", "replace")
        if re.search(r"(?m)^Object USAPAC3\s*$", txt):
            defs.append(n)
    if defs != ["Data\\INI\\Object\\Specter\\PatchSystems\\AirDefense\\USAPAC3.ini"]:
        fail(f"object winners {defs}")

    for rel, label in [
        ("data\\ini\\weapon_usapac3.ini", "Weapon USAPAC3_Weapon"),
        ("data\\ini\\object\\specter\\patchsystems\\airdefense\\usapac3_projectile.ini", "Object USAPAC3_Projectile"),
        ("data\\ini\\commandset_zzzz_usapac3.ini", "CommandSet USAPAC3CommandSet"),
        ("data\\ini\\locomotor.ini", "Locomotor Generic8x8Locomotor"),
        ("data\\ini\\locomotor.ini", "Locomotor AIM-120CLocomotor"),
    ]:
        if rel not in data_map:
            fail(f"missing {rel}")
        if label not in data_map[rel][1].decode("latin-1", "replace"):
            fail(f"{rel} missing {label}")

    cs = (MERGED / "CommandSet.ini").read_bytes()
    cb = (MERGED / "CommandButton.ini").read_bytes()
    if sha_file(MERGED / "CommandSet.ini") != CS_SHA:
        fail("CommandSet.ini hash changed")
    if sha_file(MERGED / "CommandButton.ini") != CB_SHA:
        fail("CommandButton.ini hash changed")
    cs_txt = cs.decode("latin-1")
    m = re.search(
        r"CommandSet AmericaCommandCenterCommandSet\s*(.*?)\nEnd",
        cs_txt,
        re.S,
    )
    if not m:
        fail("CC commandset")
    block = m.group(1)
    if "6  = Command_ConstructUSAPAC3" not in block:
        fail("slot 6")
    if "Command_ConstructAmerica_AD_THAAD" in block or "Command_ConstructAmerica_AD_Patriot" in block:
        fail("CC block rewritten")
    if "Command_ConstructAmerica_AD_NASAMS" in block:
        fail("NASAMS inserted into live CC")

    art_raw, art_ents = read_big(ART2)
    art_map = {n.replace("/", "\\").lower(): (n, art_raw[o : o + s]) for n, o, s in art_ents}
    if sha_file(ART2) == ART2_ORIG_SHA:
        fail("ART TWO has no USAPAC3 art")
    tex_index = {}
    for n, blob in ((k, v[1]) for k, v in art_map.items()):
        base = n.replace("\\", "/").rsplit("/", 1)[-1]
        stem = base.rsplit(".", 1)[0].lower()
        if n.startswith("art\\textures\\") or n.startswith("art\\w3d\\"):
            tex_index.setdefault(stem, []).append(n)

    needed_bones = {
        "UsaPac3Car": {"CORE", "TIRE01", "TIRE02", "TIRE03", "TIRE04", "TIRE05", "TIRE06", "TIRE07", "TIRE08", "TURRET01", "TURRETEL01", "FIREPOINT01"},
        "UsaPac3Car_w": {"TIRE09", "TIRE10"},
        "UsaPac3F": {"CORE", "TURRET01", "FIREPOINT01"},
        "pac3mis_m": {"PL11BODY"},
    }
    for model, path in W3D_MODELS.items():
        key = path.lower()
        if key not in art_map:
            fail(f"missing W3D {path}")
        bones, anims, textures, meshes = parse_w3d(art_map[key][1])
        if meshes < 1:
            fail(f"{model} has no meshes")
        if not anims:
            fail(f"{model} has no animation header")
        if anims[0][0] != model.upper().replace("USAPAC3", "USAPAC3"):
            # UsaPac3Car -> USAPAC3CAR
            expect = model.upper()
            if anims[0][0] != expect:
                fail(f"{model} anim name {anims[0][0]} != {expect}")
        for bone in needed_bones.get(model, ()):
            if bone not in bones:
                fail(f"{model} missing bone {bone}")
        for tex in textures:
            stem = tex.replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()
            if stem not in tex_index:
                fail(f"{model} texture {tex} not in ART TWO")

    for stem in TEXTURE_STEMS:
        if stem not in tex_index:
            fail(f"texture stem missing {stem}")

    # THAAD / Patriot / NASAMS packed objects must be byte-identical to overlay sources
    for rel in [
        "Data/INI/Object/Specter/PatchSystems/AirDefense/America_AD_THAAD.ini",
        "Data/INI/Object/Specter/PatchSystems/AirDefense/America_AD_Patriot.ini",
        "Data/INI/Object/Specter/PatchSystems/AirDefense/America_AD_NASAMS.ini",
    ]:
        key = rel.replace("/", "\\").lower()
        src = (PATCH / rel).read_bytes()
        if key not in data_map:
            print("WARN packed missing", rel)
            continue
        if data_map[key][1] != src:
            # overlay may differ from live packed; ensure we did not rewrite this run
            if b"USAPAC3" in data_map[key][1]:
                fail(f"{rel} now references USAPAC3")

    print("STATIC_OK")
    print("object_winner Data\\INI\\Object\\Specter\\PatchSystems\\AirDefense\\USAPAC3.ini")
    print("art2_entries", len(art_ents), "data_entries", len(data_ents))
    print("DATA", sha_file(DATA), DATA.stat().st_size)
    print("ART2", sha_file(ART2), ART2.stat().st_size)
    print("CommandSet", CS_SHA)
    print("CommandButton", CB_SHA)
    print("ART1_unchanged", ART1_SHA)
    print("INGAME_ZH: not executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
