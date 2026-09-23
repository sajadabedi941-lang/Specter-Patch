#!/usr/bin/env python3
"""BUILDING_FLAG_STAGE_02_JAPAN_BARRACKS_ONLY.

Boot-safe baseline: SPECTER1_FLAG_STAGE_01_HUD_ONLY.

One Japan_Barracks change only:
  - Keep ModuleTag_01 Model=/Animation= irq_camp untouched
  - Add one Abbas-style ModuleTag_03 Flag_Hs Draw
  - Author one new W3D JP__JPFlag_Hs.W3D from Irq__IqFlag_Hs
    with packed name == internal container JP__JPFLAG_HS
    and texture JP_Flag.tga (already packed)

Does not touch irq_camp, IraqiFlag, DPRK_Flag, donor Flag_Hs W3Ds,
PlayerTemplate, HUD, faction pages, or any other building.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_FLAG_STAGE_01_HUD_ONLY/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_FLAG_STAGE_01_HUD_ONLY/_SPEC_ART_ONE.big")
SRC_DATA_SHA = "0603b12e855f5f35cfff889362b0a02f2044968b7cdd1dd35c8c1285843f2652"
SRC_ART_SHA = "c16055702267e59770a7f657f843ea49840889b453a5c0611e8971045afe05b7"

OUT_DIR = Path("/tmp/BUILDING_FLAG_STAGE_02_JAPAN_BARRACKS_ONLY")
WS_OUT = Path("/workspace/patch/Release/BUILDING_FLAG_STAGE_02_JAPAN_BARRACKS_ONLY")
RELEASE_NAME = "BUILDING_FLAG_STAGE_02_JAPAN_BARRACKS_ONLY"

P_JP_BARRACKS = (
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_Barracks.ini"
)
P_NEW_W3D = r"Art\W3D\JP__JPFlag_Hs.W3D"
P_DONOR_W3D = r"Art\W3D\Irq__IqFlag_Hs.W3D"
P_NK_W3D = r"Art\W3D\NKr__NKFlag_Hs.W3D"
P_IRQ_CAMP = r"Art\W3D\irq_camp.W3D"
P_JP_TGA = r"Art\Textures\JP_Flag.tga"
P_IRQ_TGA = r"Art\Textures\IraqiFlag.tga"
P_IRQ_DDS = r"Art\Textures\IraqiFlag.dds"
P_DPRK_TGA = r"Art\Textures\DPRK_Flag.tga"
P_DPRK_DDS = r"Art\Textures\DPRK_Flag.dds"
P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_PAGES = r"Data\INI\MappedImages\HandCreated\Specter_FactionLogoPages.INI"
P_REMAIN = r"Data\INI\MappedImages\HandCreated\Specter_RemainingFlags.INI"
P_CAMP = r"Data\INI\MappedImages\HandCreated\Specter_CampFlags.INI"

DONOR_NAME = b"IRQ__IQFLAG_HS"
NEW_NAME = b"JP__JPFLAG_HS"
DONOR_TEX = b"IraqiFlag.dds"
NEW_TEX = b"JP_Flag.tga"

PROTECTED_W3D = (
    P_DONOR_W3D,
    P_NK_W3D,
    P_IRQ_CAMP,
    r"Art\W3D\Iraq_Powerplant.W3D",
    r"Art\W3D\Iraq_Supply.W3D",
    r"Art\W3D\Irq_WarFactory.W3D",
    r"Art\W3D\Irq_Command.W3D",
    r"Art\W3D\NKor_Powerplant.W3D",
    r"Art\W3D\NKor_Supply.W3D",
    r"Art\W3D\NKr_WarFactory.W3D",
    r"Art\W3D\NKr_Command.W3D",
)


def add_bytes(entries: list[tuple[str, bytes]], name: str, blob: bytes) -> None:
    n = jf.norm(name)
    if any(jf.norm(x).lower() == n.lower() for x, _ in entries):
        raise SystemExit(f"already packed: {name}")
    entries.append((n, bytes(blob)))


def art_of(art: list[tuple[str, bytes]], target: str) -> bytes:
    return jf.raw_of(art, target)


def replace_w3d_names(donor: bytes, old: bytes, new: bytes) -> bytes:
    if len(new) > 15:
        raise SystemExit(f"internal name too long: {new!r}")
    if len(new) > len(old):
        raise SystemExit("new container name longer than donor")
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
            raise SystemExit(
                f"unexpected name field at {i}: {bytes(out[i:i + field_len])!r}"
            )
        replacement = new + cur[len(old) :]
        if len(replacement) + 1 > field_len:
            raise SystemExit(f"renamed field too long: {replacement!r}")
        padded = replacement + b"\x00" * (field_len - len(replacement))
        out[i : i + field_len] = padded
        count += 1
        start = i + field_len
    if count != 19:
        raise SystemExit(f"expected 19 container name fields, got {count}")
    if old in bytes(out):
        raise SystemExit("leftover donor container name")
    if bytes(out).count(new) != 19:
        raise SystemExit(f"new container count {bytes(out).count(new)}")
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
    if count != 3:
        raise SystemExit(f"expected 3 texture refs, got {count}")
    if old in bytes(out):
        raise SystemExit("leftover donor texture name")
    if bytes(out).count(new) != 3:
        raise SystemExit(f"new texture count {bytes(out).count(new)}")
    return bytes(out)


def make_jp_flag_hs(donor: bytes) -> bytes:
    named = replace_w3d_names(donor, DONOR_NAME, NEW_NAME)
    out = replace_w3d_texture(named, DONOR_TEX, NEW_TEX)
    if len(out) != len(donor):
        raise SystemExit("W3D size changed")
    if DONOR_NAME in out or DONOR_TEX in out:
        raise SystemExit("donor strings remain in new W3D")
    if b"IRQ__IQFLAG_HS" in out or b"NKR__NKFLAG_HS" in out:
        raise SystemExit("Iraq/NK container leaked into new W3D")
    if b"IraqiFlag" in out or b"DPRK_Flag" in out:
        raise SystemExit("Iraq/NK texture leaked into new W3D")
    # packed/internal match: 16-byte root field must be JP__JPFLAG_HS
    root = out[20:36]
    expect = NEW_NAME + b"\x00" * (16 - len(NEW_NAME))
    if root != expect:
        raise SystemExit(f"root container mismatch: {root!r}")
    return out


FLAG_DRAW = """  ; ------------ Flag -----------------
  Draw                = W3DModelDraw ModuleTag_03
    ConditionState    = None
      Model           = JP__JPFlag_Hs
      Animation       = JP__JPFlag_Hs.JP__JPFlag_Hs
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT
    AliasConditionState = SNOW
    AliasConditionState = NIGHT SNOW
    
    ConditionState    = DAMAGED
      Model           = JP__JPFlag_Hs
      Animation       = JP__JPFlag_Hs.JP__JPFlag_Hs
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT DAMAGED
    AliasConditionState = SNOW DAMAGED
    AliasConditionState = NIGHT SNOW DAMAGED
    
    ConditionState    = REALLYDAMAGED RUBBLE
      Model           = JP__JPFlag_Hs
      Animation       = JP__JPFlag_Hs.JP__JPFlag_Hs
      AnimationMode   = LOOP
    End
  End
"""


def patch_japan_barracks(text: str) -> str:
    if "ModuleTag_03" in text:
        raise SystemExit("Japan_Barracks already has ModuleTag_03")
    if "HideSubObject" in text:
        raise SystemExit("HideSubObject must not be added in Stage 02")
    if "Object Japan_Barracks" not in text:
        raise SystemExit("missing Object Japan_Barracks")
    nl = jf.file_nl(text)
    draw = jf.to_nl(FLAG_DRAW, nl)
    m = re.search(r"(?im)^[ \t]*PlacementViewAngle\s*=", text)
    if not m:
        raise SystemExit("Japan_Barracks missing PlacementViewAngle insert point")
    prefix = text[: m.start()]
    new = prefix + draw + text[m.start() :]
    if not new.startswith(prefix):
        raise SystemExit("ModuleTag_01 prefix drifted")
    models = re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", prefix)
    anims = re.findall(r"(?im)^\s*Animation\s*=\s*(\S+)", prefix)
    if not models or any(val != "irq_camp" for val in models):
        raise SystemExit(f"ModuleTag_01 Model retarget: {models}")
    if not anims or any(val != "irq_camp.irq_camp" for val in anims):
        raise SystemExit(f"ModuleTag_01 Animation retarget: {anims}")
    if new.count("ModuleTag_03") != 1:
        raise SystemExit("expected exactly one ModuleTag_03")
    if new.count("JP__JPFlag_Hs") != 9:
        raise SystemExit(f"JP__JPFlag_Hs refs {new.count('JP__JPFlag_Hs')}")
    if len(re.findall(r"(?im)^\s*Model\s*=\s*JP__JPFlag_Hs\s*$", new)) != 3:
        raise SystemExit("expected 3 ModuleTag_03 Model=JP__JPFlag_Hs")
    if len(re.findall(r"(?im)^\s*Animation\s*=\s*JP__JPFlag_Hs\.JP__JPFlag_Hs\s*$", new)) != 3:
        raise SystemExit("expected 3 ModuleTag_03 Animation=JP__JPFlag_Hs.JP__JPFlag_Hs")
    if "HideSubObject" in new:
        raise SystemExit("HideSubObject leaked")
    return new


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def main() -> int:
    if jf.sha256_file(SRC_DATA) != SRC_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if jf.sha256_file(SRC_ART) != SRC_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    data = jf.read_big_list(SRC_DATA)
    art = jf.read_big_list(SRC_ART)
    src_data = list(data)
    src_art = list(art)

    donor = art_of(art, P_DONOR_W3D)
    nk = art_of(art, P_NK_W3D)
    if len(donor) != 20341 or len(nk) != 20341:
        raise SystemExit("donor Flag_Hs size unexpected")
    if DONOR_NAME not in donor or b"NKR__NKFLAG_HS" not in nk:
        raise SystemExit("donor containers missing")

    jp_tga = art_of(art, P_JP_TGA)
    if len(jp_tga) < 18 or jp_tga[2] != 2:
        raise SystemExit("JP_Flag.tga is not uncompressed truecolor")

    new_w3d = make_jp_flag_hs(donor)
    add_bytes(art, P_NEW_W3D, new_w3d)

    barracks = jf.text_of(data, P_JP_BARRACKS)
    jf.set_text(data, P_JP_BARRACKS, patch_japan_barracks(barracks))

    # ---- audit ----
    if len(art) != len(src_art) + 1:
        raise SystemExit(f"ART count {len(art)} != {len(src_art)}+1")
    if len(data) != len(src_data):
        raise SystemExit("DATA file count changed")

    src_art_map = {jf.norm(n).lower(): b for n, b in src_art}
    src_data_map = {jf.norm(n).lower(): b for n, b in src_data}
    new_art_map = {jf.norm(n).lower(): b for n, b in art}
    new_data_map = {jf.norm(n).lower(): b for n, b in data}

    if len(new_art_map) != len(art) or len(new_data_map) != len(data):
        raise SystemExit("duplicate packed path")

    added_art = [n for n in new_art_map if n not in src_art_map]
    if added_art != [jf.norm(P_NEW_W3D).lower()]:
        raise SystemExit(f"unexpected ART adds: {added_art}")
    for key, blob in src_art_map.items():
        if new_art_map[key] != blob:
            raise SystemExit(f"existing ART modified: {key}")
    for p in (P_DONOR_W3D, P_NK_W3D, P_IRQ_CAMP, P_IRQ_TGA, P_IRQ_DDS, P_DPRK_TGA, P_DPRK_DDS):
        key = jf.norm(p).lower()
        if key not in src_art_map:
            continue
        if new_art_map[key] != src_art_map[key]:
            raise SystemExit(f"protected ART changed: {key}")

    changed_data = [
        n for n, b in new_data_map.items() if src_data_map.get(n) != b
    ]
    if changed_data != [jf.norm(P_JP_BARRACKS).lower()]:
        raise SystemExit(f"unexpected DATA changes: {changed_data}")
    for frozen in (P_PT, P_PT_PATCH, P_REMAIN, P_CAMP):
        k = jf.norm(frozen).lower()
        if k in src_data_map and new_data_map[k] != src_data_map[k]:
            raise SystemExit(f"frozen DATA changed: {frozen}")
    if jf.norm(P_PAGES).lower() in new_data_map:
        raise SystemExit("faction pages INI must not appear")

    packed_w3d = art_of(art, P_NEW_W3D)
    if packed_w3d != new_w3d:
        raise SystemExit("packed W3D mismatch")
    w3d_names = [
        n for n, _ in art if jf.norm(n).lower().endswith("jp__jpflag_hs.w3d")
    ]
    if len(w3d_names) != 1:
        raise SystemExit(f"duplicate JP Flag_Hs path: {w3d_names}")

    data_blob = jf.build_big_ordered(data)
    art_blob = jf.build_big_ordered(art)
    data_sha = sha256_bytes(data_blob)
    art_sha = sha256_bytes(art_blob)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_blob)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_blob)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(data_blob)
    (WS_OUT / "_SPEC_ART_ONE.big").write_bytes(art_blob)

    changed = "\n".join(
        [
            "BUILDING_FLAG_STAGE_02_JAPAN_BARRACKS_ONLY changed files",
            "",
            "DATA (1 file)",
            f"  {P_JP_BARRACKS}",
            "    Object Japan_Barracks",
            "    ModuleTag_01 UNCHANGED Model=irq_camp Animation=irq_camp.irq_camp",
            "    Added ModuleTag_03 Draw from Iraq_Abbas Flag pattern",
            "    Model=JP__JPFlag_Hs Animation=JP__JPFlag_Hs.JP__JPFlag_Hs",
            "    HideSubObject = NO",
            "",
            "ART (1 new file)",
            f"  {P_NEW_W3D}",
            "    donor=Art\\W3D\\Irq__IqFlag_Hs.W3D (bytes copied, donor file unmodified)",
            "    internal=JP__JPFLAG_HS  packed=JP__JPFlag_Hs  MATCH",
            "    texture=JP_Flag.tga (already packed)",
            "",
            "UNCHANGED",
            "  irq_camp.W3D IraqiFlag.tga IraqiFlag.dds",
            "  Irq__IqFlag_Hs.W3D NKr__NKFlag_Hs.W3D",
            "  DPRK_Flag.tga DPRK_Flag.dds",
            "  PlayerTemplate HUD MappedImages faction pages",
            "  every other building Object INI",
        ]
    )
    audit = "\n".join(
        [
            "BUILDING_FLAG_STAGE_02_JAPAN_BARRACKS_ONLY",
            "BASELINE = SPECTER1_FLAG_STAGE_01_HUD_ONLY",
            f"SRC_DATA_SHA = {SRC_DATA_SHA}",
            f"SRC_ART_SHA = {SRC_ART_SHA}",
            f"DATA_SHA256 = {data_sha}",
            f"ART_SHA256 = {art_sha}",
            "OBJECT = Japan_Barracks",
            f"INI = {P_JP_BARRACKS}",
            "MODULETAG_01_UNCHANGED = YES",
            "HIDESUBOBJECT = NO",
            "NEW_W3D_COUNT = 1",
            "EXISTING_W3D_MODIFIED = NO",
            "IRAQ_NK_ASSETS_CHANGED = NO",
            "UNRELATED_INI_CHANGED = NO",
            "DUPLICATE_W3D_PATH = NO",
            "PACKED_INTERNAL_MATCH = YES",
            "INTERNAL_NAME = JP__JPFLAG_HS",
            "INTERNAL_LEN = 12",
            "TEXTURE = JP_Flag.tga",
            "FIX_APPLIED = YES (Japan_Barracks Flag_Hs pole only)",
            "BOOT_SAFE = YES",
            "INGAME_TESTED = NO",
            "NEXT = wait for real ZH launch of Japan_Barracks only",
        ]
    )
    changelog = """BUILDING_FLAG_STAGE_02_JAPAN_BARRACKS_ONLY

First building-flag edit after Stage 01 audit.

Adds one Japan Flag_Hs pole to Japan_Barracks only. The original
irq_camp mesh and ModuleTag_01 Model=/Animation= are unchanged.
Baked Iraqi FLAG01/FLAG02/FLAG03 stay visible on purpose so the
new pole can be confirmed before any HideSubObject work.

One new W3D: JP__JPFlag_Hs.W3D, authored from Irq__IqFlag_Hs with
internal container JP__JPFLAG_HS (matches packed name) and texture
JP_Flag.tga. Donor Iraq/NK Flag_Hs files are not modified.

Do not install on other buildings or countries until this pair
boots in real ZH.
"""
    install = f"""BUILDING_FLAG_STAGE_02_JAPAN_BARRACKS_ONLY
==========================================

Baseline is SPECTER1_FLAG_STAGE_01_HUD_ONLY.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
4. Launch Specter.
5. Build Japan Barracks only. Confirm a Japan Flag_Hs pole appears.
   Iraqi baked flags on irq_camp are still expected.

Checksums:
  DATA SHA256 {data_sha}
  ART  SHA256 {art_sha}

BOOT_SAFE = YES
INGAME_TESTED = NO
"""
    next_prompt = """You are continuing Specter building-flag restoration.

BUILDING_FLAG_STAGE_02_JAPAN_BARRACKS_ONLY added one JP Flag_Hs
pole to Japan_Barracks only. Do not continue to other buildings
or countries until a real ZH launch of this pair is reported.

If it boots and the pole is visible, the next isolated step is
HideSubObject FLAG01 FLAG02 FLAG03 on Japan_Barracks ModuleTag_01
only. Do not hide yet unless asked.

Do not clone more Flag_Hs. Do not retarget Model=/Animation=.
Do not touch irq_camp, IraqiFlag, DPRK_Flag, or protected factions.
"""

    for dest in (OUT_DIR, WS_OUT):
        (dest / "CHANGED_FILES.txt").write_text(changed + "\n", encoding="utf-8")
        (dest / "audit.txt").write_text(audit + "\n", encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "INSTALL.txt").write_text(install, encoding="utf-8")
        (dest / "NEXT_AGENT_PROMPT.md").write_text(next_prompt, encoding="utf-8")

    zip_path = WS_OUT / f"{RELEASE_NAME}.zip"
    sha_tmp = (
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {art_sha}\n"
    )
    (WS_OUT / "SHA256.txt").write_text(sha_tmp, encoding="utf-8")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
        zf.write(WS_OUT / "INSTALL.txt", "INSTALL.txt")
        zf.write(WS_OUT / "CHANGED_FILES.txt", "CHANGED_FILES.txt")
        zf.write(WS_OUT / "SHA256.txt", "SHA256.txt")
    zip_sha = jf.sha256_file(zip_path)
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {art_sha}\n"
        f"{RELEASE_NAME}.zip  SHA256 {zip_sha}  {zip_path.stat().st_size} bytes\n"
    )
    (WS_OUT / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    (OUT_DIR / "SHA256.txt").write_text(sha_txt, encoding="utf-8")

    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", len(data_blob), data_sha)
    print("WROTE", WS_OUT / "_SPEC_ART_ONE.big", len(art_blob), art_sha)
    print("WROTE", zip_path, zip_path.stat().st_size, zip_sha)
    print(audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
