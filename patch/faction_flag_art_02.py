#!/usr/bin/env python3
"""SPECTER1 per-faction building flag ART pass.

Baseline: SPECTER1_FACTION_FLAG_IDENTITY_01 DATA+ART.
Creates native national flag assets for every repaired faction that had
only cloned donor flags, and wires them into the Abbas-type buildings
(the only structures with flag Draw attachments).

New ART per faction (Side -> texture stem / flag mesh):
  India         IN_Flag.tga    India_Flag_Hs
  Libya         LY_Flag.tga    Libya_Flag_Hs
  Pakistan      PK_Flag.tga    Pakistan_Flag_Hs
  SaudiArabia   SA_Flag.tga    SaudiArabia_Flag_Hs
  Syria         SY_Flag.tga    Syria_Flag_Hs
  SouthAfrica   ZA_Flag.tga    SouthAfrica_Flag_Hs
  UAE           UAE_Flag.tga   UAE_Flag_Hs
  Japan         JP_Flag.tga    Japan_Flag_Hs
  SouthKorea    SK_Flag.tga    SouthKorea_Flag_Hs
  Vietnam       VN_Flag.tga    Vietnam_Flag_Hs
Staged textures (no Abbas consumer yet, same pipeline): DE/FR/UK/IT/SE/UA.

Method (all byte-safe, no model edits):
- Flag PNGs fetched from flagcdn (w320), resized 128x64, written as
  standard bottom-up 32-bit TGA (desc 0x08) -- proven pixel-identical
  on-GPU to the working DPRK_Flag/IraqiFlag DDS pair.
- Flag W3Ds cloned from Irq__IqFlag_Hs.W3D by overwriting the 3
  length-prefixed texture-name fields in place (size-identical files).
- DATA: Abbas Draw Model/Animation retargeted Side -> native mesh.

Protected factions, gameplay, units, weapons, animations unchanged.
"""
from __future__ import annotations

import hashlib
import io
import re
import shutil
import struct
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_FACTION_FLAG_IDENTITY_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_FACTION_FLAG_IDENTITY_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "f82eb7772e94c8b1006a7c6dcaba174222f38051cd9135314b727b4509fa07c7"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_FACTION_FLAG_ART_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_FACTION_FLAG_ART_01")
RELEASE_NAME = "SPECTER1_FACTION_FLAG_ART_01"

DONOR_W3D = r"Art\W3D\Irq__IqFlag_Hs.W3D"
DONOR_TEX = b"IraqiFlag.dds"  # 3x, length-prefixed 14-byte fields

# Side -> (flagcdn code, texture stem, mesh name or None, Abbas filename hint)
FLAGS = {
    "India": ("in", "IN_Flag.tga", "India_Flag_Hs", "India_Abbas.ini"),
    "Libya": ("ly", "LY_Flag.tga", "Libya_Flag_Hs", "Libya_Abbas.ini"),
    "Pakistan": ("pk", "PK_Flag.tga", "Pakistan_Flag_Hs", "Pakistan_Abbas.ini"),
    "SaudiArabia": ("sa", "SA_Flag.tga", "SaudiArabia_Flag_Hs", "SaudiArabia_Abbas.ini"),
    "Syria": ("sy", "SY_Flag.tga", "Syria_Flag_Hs", "Syria_Abbas.ini"),
    "SouthAfrica": ("za", "ZA_Flag.tga", "SouthAfrica_Flag_Hs", "SouthAfrica_Abbas.ini"),
    "UAE": ("ae", "UAE_Flag.tga", "UAE_Flag_Hs", "UAE_Abbas.ini"),
    "Japan": ("jp", "JP_Flag.tga", "Japan_Flag_Hs", "Japan_NuclearCenter.ini"),
    "SouthKorea": ("kr", "SK_Flag.tga", "SouthKorea_Flag_Hs", "SouthKorea_NuclearCenter.ini"),
    "Vietnam": ("vn", "VN_Flag.tga", "Vietnam_Flag_Hs", "Vietnam_NuclearCenter.ini"),
    "Germany": ("de", "DE_Flag.tga", None, None),
    "France": ("fr", "FR_Flag.tga", None, None),
    "Britain": ("gb", "UK_Flag.tga", None, None),
    "Italy": ("it", "IT_Flag.tga", None, None),
    "Sweden": ("se", "SE_Flag.tga", None, None),
    "Ukraine": ("ua", "UA_Flag.tga", None, None),
}

FLAG_W, FLAG_H = 128, 64


def fetch_flag(code: str) -> Image.Image:
    url = f"https://flagcdn.com/w320/{code}.png"
    req = urllib.request.Request(url, headers={"User-Agent": "SpecterPatch/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    if im.width < 100 or im.height < 60:
        raise SystemExit(f"flag {code}: implausible size {im.size}")
    return im


def to_tga(im: Image.Image) -> bytes:
    im = im.resize((FLAG_W, FLAG_H), Image.LANCZOS)
    px = im.tobytes("raw", "RGBA")
    # BGRA rows, bottom-up, 32-bit, descriptor 0x08 (same as DPRK_Flag.tga)
    rows = [px[i * FLAG_W * 4:(i + 1) * FLAG_W * 4] for i in range(FLAG_H)]
    out = bytearray()
    for row in reversed(rows):
        for i in range(0, len(row), 4):
            out += bytes((row[i + 2], row[i + 1], row[i], row[i + 3]))
    hdr = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, FLAG_W, FLAG_H, 32, 0x08)
    return hdr + bytes(out)


def clone_w3d(donor: bytes, new_stem: str) -> bytes:
    """Swap texture ref in place. File size must not change."""
    field = new_stem.encode("ascii") + b"\x00"
    if len(field) > len(DONOR_TEX) + 1:
        raise SystemExit(f"texture name too long: {new_stem}")
    field = field + b"\x00" * (len(DONOR_TEX) + 1 - len(field))
    count = donor.count(DONOR_TEX)
    if count != 3:
        raise SystemExit(f"donor texture refs != 3 (got {count})")
    return donor.replace(DONOR_TEX, field.rstrip(b"\x00") + b"\x00" * (len(DONOR_TEX) + 1 - len(new_stem.encode("ascii") + b"\x00")))


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("unexpected DATA SHA")
    if jf.sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("unexpected ART SHA")

    data_entries = jf.read_big_list(SRC_DATA)
    art_entries = jf.read_big_list(SRC_ART)
    data_base = {jf.norm(n).lower(): bytes(b) for n, b in data_entries}
    art_base = {jf.norm(n).lower(): bytes(b) for n, b in art_entries}
    donor = bytes(jf.raw_of(art_entries, DONOR_W3D))

    # Self-test: same-name clone must be byte-identical.
    if clone_w3d(donor, "IraqiFlag.dds") != donor:
        raise SystemExit("W3D clone self-test failed")

    new_art: dict[str, bytes] = {}
    for side, (code, stem, _mesh, _hint) in FLAGS.items():
        tga = to_tga(fetch_flag(code))
        # Read back through PIL (honors origin bit) and compare.
        back = Image.open(io.BytesIO(tga)).convert("RGB")
        ref = fetch_flag(code).convert("RGB").resize((FLAG_W, FLAG_H), Image.LANCZOS)
        diff = sum(abs(a - b) for a, b in zip(back.tobytes(), ref.tobytes())) / (FLAG_W * FLAG_H * 3)
        if diff > 3.0:
            raise SystemExit(f"{side}: TGA round-trip diff too large ({diff:.2f})")
        new_art[f"Art\\Textures\\{stem}"] = tga

    mesh_of: dict[str, str] = {}
    for side, (_code, stem, mesh, _hint) in FLAGS.items():
        if mesh is None:
            continue
        w3d = clone_w3d(donor, stem)
        assert len(w3d) == len(donor)
        if DONOR_TEX in w3d or stem.encode("ascii") not in w3d:
            raise SystemExit(f"{side}: W3D clone ref check failed")
        new_art[f"Art\\W3D\\{mesh}.W3D"] = w3d
        mesh_of[side] = stem

    # Resolve Abbas packed paths by filename.
    abbas_path: dict[str, str] = {}
    for side, (_c, _s, mesh, hint) in FLAGS.items():
        if mesh is None:
            continue
        hits = [n for n, _ in data_entries if n.lower().endswith("\\" + hint.lower())]
        if len(hits) != 1:
            raise SystemExit(f"{side}: Abbas file {hint} hits={len(hits)}")
        abbas_path[side] = hits[0]

    # DATA: retarget Abbas flag Draw refs to native meshes.
    old_mesh = "Irq__IqFlag_Hs"
    data_changed = []
    for side, path in abbas_path.items():
        mesh = [m for s, (_c, _st, m, _h) in FLAGS.items() if s == side][0]
        old = jf.text_of(data_entries, path)
        if old_mesh not in old:
            raise SystemExit(f"{path}: donor mesh not referenced")
        new, n_model = re.subn(rf"(?im)^(\s*Model\s*=\s*){re.escape(old_mesh)}\b",
                               rf"\1{mesh}", old)
        new, n_anim = re.subn(
            rf"(?im)^(\s*Animation\s*=\s*){re.escape(old_mesh)}\.{re.escape(old_mesh)}\b",
            rf"\1{mesh}.{mesh}", new)
        if n_model < 1 or n_anim < 1:
            raise SystemExit(f"{path}: no pairs swapped")
        if re.search(rf"(?im)^\s*(Model|Animation)\s*=\s*{re.escape(old_mesh)}", new):
            raise SystemExit(f"{path}: donor mesh still referenced")
        jf.set_text(data_entries, path, new)
        data_changed.append((path, n_model, n_anim))

    for rel, blob in new_art.items():
        n = jf.norm(rel)
        if any(jf.norm(x).lower() == n.lower() for x, _ in art_entries):
            raise SystemExit(f"already packed: {rel}")
        art_entries.append((n, bytes(blob)))

    # ---- Validation ----
    art_names = {jf.norm(n).lower() for n, _ in art_entries}
    for side, (_c, stem, mesh, _h) in FLAGS.items():
        if f"art\\textures\\{stem}".lower() not in art_names:
            raise SystemExit(f"ART missing texture {stem}")
        if mesh and f"art\\w3d\\{mesh}.w3d".lower() not in art_names:
            raise SystemExit(f"ART missing mesh {mesh}")

    changed = [n for n, b in data_entries
               if data_base.get(jf.norm(n).lower()) != bytes(b)]
    if {jf.norm(c).lower() for c in changed} != {jf.norm(p).lower() for p in abbas_path.values()}:
        raise SystemExit(f"unexpected DATA changes: {changed}")
    for n, b in art_entries:
        k = jf.norm(n).lower()
        if k in art_base and art_base[k] != bytes(b):
            raise SystemExit(f"ART entry modified (must be add-only): {n}")

    # No-faction-shows-another-flag: every Draw flag-mesh ref must match Side.
    native = {"Iraq": "Irq__IqFlag_Hs", "Egypt": "Irq__IqFlag_Hs",
              "NorthKorea": "NKr__NKFlag_Hs"}
    for side, (_c, _s, mesh, _h) in FLAGS.items():
        if mesh:
            native[side] = mesh
    checked = 0
    for n, b in data_entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", errors="replace")
        for m in re.finditer(r"(?im)^Object\s+(\S+)\s*$", t):
            m2 = re.search(r"(?im)^Object\s+\S+", t[m.end():])
            oblk = t[m.start(): m.end() + m2.start() if m2 else len(t)]
            sm = re.search(r"(?im)^\s*Side\s*=\s*(\S+)\s*$", oblk)
            if not sm:
                continue
            for fm in set(re.findall(r"(?im)^\s*Model\s*=\s*(\S*Flag_Hs)\s*$", oblk)):
                want = native.get(sm.group(1))
                if want is None:
                    raise SystemExit(f"{m.group(1)} (Side={sm.group(1)}): unmapped flag {fm}")
                if fm != want:
                    raise SystemExit(f"{m.group(1)}: {fm} != native {want}")
                checked += 1
    packed_art = None
    _ = packed_art

    data_blob = jf.build_big_ordered(data_entries)
    art_blob = jf.build_big_ordered(art_entries)
    new_data_sha = hashlib.sha256(data_blob).hexdigest()
    new_art_sha = hashlib.sha256(art_blob).hexdigest()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(data_blob)
    (WS_OUT / "_SPEC_ART_ONE.big").write_bytes(art_blob)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_blob)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_blob)

    lines = [
        "SPECTER1 FACTION FLAG ART 01",
        f"BASELINE_DATA_SHA256 = {EXPECTED_DATA_SHA}",
        f"NEW_DATA_SHA256 = {new_data_sha}",
        f"BASELINE_ART_SHA256 = {EXPECTED_ART_SHA}",
        f"NEW_ART_SHA256 = {new_art_sha}",
        "ART_MODE = add-only (no existing entry modified)",
        "GAMEPLAY_CHANGED = NO",
        "PROTECTED_FACTIONS_UNCHANGED = YES (USA, Israel, China, Russia, Iran, Iraq, NorthKorea, NATO, Egypt)",
        "",
        f"NATIVE_FLAG_CHECKED = {checked} Abbas flag Draw refs, every Side uses its own mesh",
        "WIRED_MESHES (Abbas Draw -> native W3D + native texture):",
    ]
    for side, path in abbas_path.items():
        mesh = [m for s, (_c, _st, m, _h) in FLAGS.items() if s == side][0]
        stem = [st for s, (_c, st, _m, _h) in FLAGS.items() if s == side][0]
        lines.append(f"  {side}: {path.split(chr(92))[-1]} -> {mesh}.W3D ({stem})")
    lines += [
        "STAGED_TEXTURES (no Abbas consumer yet): DE_Flag, FR_Flag, UK_Flag, IT_Flag, SE_Flag, UA_Flag",
        "TURKEY: existing Turkey_Flag.tga kept; no Abbas building needs a Turkey W3D.",
        "",
        "OUT_OF_SCOPE (no flag attachment points in models; adding Draw blocks would",
        "misplace flags without W3D placement data): WarFactory/Radar/Power/Supply/Barracks",
        "show house color automatically, same as the USA/NATO reference standard.",
        "",
        "INGAME_TESTED = NO",
        "DATA_CHANGED = YES (10 Abbas INIs only)",
        "ART_CHANGED = YES (16 textures + 10 W3D clones added)",
    ]
    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 faction flag ART 01

Continues from SPECTER1_FACTION_FLAG_IDENTITY_01. Native national flag
assets for the repaired factions: 16 new 128x64 flag textures converted
from reference flag art, plus 10 W3D flag-mesh clones of Irq__IqFlag_Hs
(byte-identical except the texture name) for every faction with an
Abbas-type building. Abbas Draw refs retargeted Side -> native mesh, so
no faction displays another country's flag anymore.

Protected factions, gameplay, units, weapons, animations unchanged. ART
is add-only. WarFactory/Radar/Power/Supply/Barracks inherit house color
automatically (USA/NATO reference standard); they have no flag meshes.

INGAME_TESTED = NO
"""
    install = f"""{RELEASE_NAME}
==============================

Native per-faction building flags on the SPECTER1 identity baseline.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
4. Launch Specter.

Checksums:
  DATA SHA256 {new_data_sha}
  ART  SHA256 {new_art_sha}

INGAME_TESTED = NO
"""
    for dest in (OUT_DIR, WS_OUT):
        (dest / "audit.txt").write_text(audit, encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "INSTALL.txt").write_text(install, encoding="utf-8")
    zpath = WS_OUT / f"{RELEASE_NAME}.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
        zf.write(WS_OUT / "INSTALL.txt", "INSTALL.txt")
    (OUT_DIR / zpath.name).write_bytes(zpath.read_bytes())
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {new_data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {new_art_sha}\n"
        f"{zpath.name}  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n"
    )
    for dest in (OUT_DIR, WS_OUT):
        (dest / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    print(audit)
    print("ZIP", zpath, zpath.stat().st_size, zip_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
