#!/usr/bin/env python3
"""SPECTER1_FLAG_FACTION_PAGE_ONLY — Stage 01B LoadScreenImage pages.

Baseline is FLAG_STAGE_01_HUD_ONLY (confirmed boot). Only LoadScreenImage
for 17 remaining countries is remapped onto unique FactionLogoPage
MappedImages and 1024x1024 TGA pages. Stock USA/GLA/China pages are not
reused. Buildings, W3D, ExtraDraw, cloth, and gameplay INI stay frozen.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_FLAG_STAGE_01_HUD_ONLY/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_FLAG_STAGE_01_HUD_ONLY/_SPEC_ART_ONE.big")
SRC_DATA_SHA = "0603b12e855f5f35cfff889362b0a02f2044968b7cdd1dd35c8c1285843f2652"
SRC_ART_SHA = "c16055702267e59770a7f657f843ea49840889b453a5c0611e8971045afe05b7"

WS_OUT = Path("/workspace/patch/Release/SPECTER1_FLAG_FACTION_PAGE_ONLY")
RELEASE_NAME = "SPECTER1_FLAG_FACTION_PAGE_ONLY"

P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_UPGRADE = r"Data\INI\Upgrade.ini"
P_CMDSET = r"Data\INI\CommandSet.ini"
P_REMAIN = r"Data\INI\MappedImages\HandCreated\Specter_RemainingFlags.INI"
P_TURKEY = r"Data\INI\MappedImages\HandCreated\Turkey_FactionImages.INI"
P_CAMP = r"Data\INI\MappedImages\HandCreated\Specter_CampFlags.INI"
P_PAGES = r"Data\INI\MappedImages\HandCreated\Specter_FactionLogoPages.INI"

FROZEN_DATA = (P_PT_PATCH, P_CMDBTN, P_WEAPON, P_UPGRADE, P_CMDSET, P_REMAIN, P_TURKEY, P_CAMP)

# template suffix -> (MappedImage/page stem, existing 128x64 flag TGA stem)
SIDES = {
    "Japan": ("JapanFactionLogoPage", "JP_Flag"),
    "Vietnam": ("VietnamFactionLogoPage", "VN_Flag"),
    "SouthKorea": ("SouthKoreaFactionLogoPage", "SK_Flag"),
    "Libya": ("LibyaFactionLogoPage", "LY_Flag"),
    "SouthAfrica": ("SouthAfricaFactionLogoPage", "ZA_Flag"),
    "Pakistan": ("PakistanFactionLogoPage", "PK_Flag"),
    "India": ("IndiaFactionLogoPage", "IN_Flag"),
    "Syria": ("SyriaFactionLogoPage", "SY_Flag"),
    "UAE": ("UAEFactionLogoPage", "UAE_Flag"),
    "SaudiArabia": ("SaudiArabiaFactionLogoPage", "SA_Flag"),
    "Turkey": ("TurkeyFactionLogoPage", "TR_Flag"),
    "Sweden": ("SwedenFactionLogoPage", "SE_Flag"),
    "Ukraine": ("UkraineFactionLogoPage", "UA_Flag"),
    "Italy": ("ItalyFactionLogoPage", "IT_Flag"),
    "Britain": ("BritainFactionLogoPage", "UK_Flag"),
    "Germany": ("GermanyFactionLogoPage", "DE_Flag"),
    "France": ("FranceFactionLogoPage", "FR_Flag"),
}
PROTECTED = (
    "FactionAmerica",
    "FactionAmericaAirForceGeneral",
    "FactionIran",
    "FactionIsrael",
    "FactionChina",
    "FactionRussia",
    "FactionNato",
    "FactionEgypt",
    "FactionNorthKorea",
    "FactionIraq",
)
STOCK_PAGES = (
    "SAFactionLogoPage_US",
    "SUFactionLogoPage_GLA",
    "SNFactionLogoPage_China",
)
TGA_FOOTER = bytes.fromhex("000000000000000054525545564953494f4e2d5846494c452e00")
VIS_W, VIS_H = 799, 599
PAGE_W = PAGE_H = 1024


def add_bytes(entries: list[tuple[str, bytes]], name: str, blob: bytes) -> None:
    n = jf.norm(name)
    if any(jf.norm(x).lower() == n.lower() for x, _ in entries):
        raise SystemExit(f"already packed: {name}")
    entries.append((n, bytes(blob)))


def art_tex(art: list[tuple[str, bytes]], stem: str) -> bytes:
    hits = [
        b
        for n, b in art
        if Path(n.replace("\\", "/")).stem.lower() == stem.lower()
        and n.lower().endswith(".tga")
    ]
    if len(hits) != 1:
        raise SystemExit(f"expected 1 ART TGA {stem}, got {len(hits)}")
    return hits[0]


def decode_tga_rgb(raw: bytes) -> tuple[int, int, list[tuple[int, int, int]]]:
    idlen, imgtype = raw[0], raw[2]
    w, h = struct.unpack_from("<HH", raw, 12)
    bpp, desc = raw[16], raw[17]
    if imgtype != 2:
        raise SystemExit("flag TGA must be uncompressed truecolor")
    off = 18 + idlen
    step = bpp // 8
    top_down = bool(desc & 0x20)
    out: list[tuple[int, int, int]] = []
    for y in range(h):
        row = y if top_down else (h - 1 - y)
        for x in range(w):
            i = off + (row * w + x) * step
            out.append((raw[i + 2], raw[i + 1], raw[i]))
    return w, h, out


def scale_nn(
    sw: int, sh: int, src: list[tuple[int, int, int]], dw: int, dh: int
) -> list[tuple[int, int, int]]:
    out: list[tuple[int, int, int]] = []
    for y in range(dh):
        sy = min(sh - 1, y * sh // dh)
        for x in range(dw):
            sx = min(sw - 1, x * sw // dw)
            out.append(src[sy * sw + sx])
    return out


def make_faction_page(flag_raw: bytes) -> bytes:
    sw, sh, src = decode_tga_rgb(flag_raw)
    aspect = sw / sh
    dw, dh = VIS_W, int(round(VIS_W / aspect))
    if dh > VIS_H:
        dh = VIS_H
        dw = int(round(VIS_H * aspect))
    scaled = scale_nn(sw, sh, src, dw, dh)
    ox = (VIS_W - dw) // 2
    oy = (VIS_H - dh) // 2
    # 24-bit BGR bottom-up canvas, dark fill. Visible page is top-left 799x599.
    pixels = bytearray([8, 8, 8] * (PAGE_W * PAGE_H))

    def put(x: int, y_top: int, rgb: tuple[int, int, int]) -> None:
        row = PAGE_H - 1 - y_top
        i = (row * PAGE_W + x) * 3
        r, g, b = rgb
        pixels[i] = b
        pixels[i + 1] = g
        pixels[i + 2] = r

    for y in range(dh):
        for x in range(dw):
            put(ox + x, oy + y, scaled[y * dw + x])
    out = bytearray()
    out += bytes([0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    out += struct.pack("<HH", PAGE_W, PAGE_H)
    out += bytes([24, 0])
    out += pixels
    out += TGA_FOOTER
    if len(out) != 18 + PAGE_W * PAGE_H * 3 + 26:
        raise SystemExit(f"page size {len(out)}")
    return bytes(out)


def faction_block(pt: str, name: str) -> str:
    m = re.search(
        rf"(?ims)^PlayerTemplate\s+{re.escape(name)}\s*$.*?(?=^PlayerTemplate\s|\Z)",
        pt,
    )
    if not m:
        raise SystemExit(f"missing PlayerTemplate {name}")
    return m.group(0)


def set_load_screen(pt: str, name: str, image: str) -> str:
    block = faction_block(pt, name)
    new_block, n = re.subn(
        r"(?im)^(\s*LoadScreenImage\s*=\s*)\S+",
        rf"\g<1>{image}",
        block,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"{name}: LoadScreenImage replace n={n}")
    old_rest = re.sub(r"(?im)^(\s*LoadScreenImage\s*=\s*)\S+", r"\1", block)
    new_rest = re.sub(r"(?im)^(\s*LoadScreenImage\s*=\s*)\S+", r"\1", new_block)
    if old_rest != new_rest:
        raise SystemExit(f"{name}: non-LoadScreenImage edit")
    return pt.replace(block, new_block, 1)


def load_screen_of(block: str) -> str:
    m = re.search(r"(?im)^\s*LoadScreenImage\s*=\s*(\S+)", block)
    if not m:
        raise SystemExit("missing LoadScreenImage")
    return m.group(1)


def mi_names(text: str) -> list[str]:
    return re.findall(r"(?im)^MappedImage\s+(\S+)\s*$", text)


def main() -> int:
    if jf.sha256_file(SRC_DATA) != SRC_DATA_SHA:
        raise SystemExit("STAGE_01 DATA SHA mismatch")
    if jf.sha256_file(SRC_ART) != SRC_ART_SHA:
        raise SystemExit("STAGE_01 ART SHA mismatch")

    data = jf.read_big_list(SRC_DATA)
    art = jf.read_big_list(SRC_ART)
    if len(data) != 2883 or len(art) != 4449:
        raise SystemExit(f"baseline count {len(data)}/{len(art)}")

    src_data_map = {jf.norm(n).lower(): bytes(b) for n, b in data}
    src_art_map = {jf.norm(n).lower(): bytes(b) for n, b in art}
    frozen_raw = {p: jf.raw_of(data, p) for p in FROZEN_DATA}
    src_pt = jf.text_of(data, P_PT)
    src_pt_raw = jf.raw_of(data, P_PT)
    src_protected = {name: faction_block(src_pt, name) for name in PROTECTED if f"PlayerTemplate {name}" in src_pt}

    pt = src_pt
    rows = []
    for side, (page, flag_stem) in SIDES.items():
        tmpl = f"Faction{side}"
        old = load_screen_of(faction_block(pt, tmpl))
        if old not in STOCK_PAGES:
            raise SystemExit(f"{tmpl} LoadScreenImage already {old}")
        pt = set_load_screen(pt, tmpl, page)
        rows.append(f"{tmpl}  {old} -> {page}  flag={flag_stem}.tga")
    if pt == src_pt:
        raise SystemExit("PlayerTemplate LoadScreenImage unchanged")
    if src_pt.count("LoadScreenImage") != pt.count("LoadScreenImage"):
        raise SystemExit("LoadScreenImage count changed")
    for name, block in src_protected.items():
        if faction_block(pt, name) != block:
            raise SystemExit(f"protected template changed: {name}")
    for side in SIDES:
        tmpl = f"Faction{side}"
        old_b = faction_block(src_pt, tmpl)
        new_b = faction_block(pt, tmpl)
        old_stripped = re.sub(r"(?im)^(\s*LoadScreenImage\s*=\s*)\S+", r"\1", old_b)
        new_stripped = re.sub(r"(?im)^(\s*LoadScreenImage\s*=\s*)\S+", r"\1", new_b)
        if old_stripped != new_stripped:
            raise SystemExit(f"{tmpl} non-LoadScreenImage drift")

    pages_ini = ["; SPECTER STAGE 01B - unique faction logo pages (select / load)"]
    new_art_names = []
    for side, (page, flag_stem) in SIDES.items():
        if page in STOCK_PAGES:
            raise SystemExit(f"refuses to reuse stock page name {page}")
        flag = art_tex(art, flag_stem)
        tga = make_faction_page(flag)
        hdr_w, hdr_h = struct.unpack_from("<HH", tga, 12)
        if tga[2] != 2 or hdr_w != 1024 or hdr_h != 1024 or tga[16] != 24:
            raise SystemExit(f"{page} TGA header invalid")
        tex_name = f"{page}.tga"
        add_bytes(art, rf"Art\Textures\{tex_name}", tga)
        new_art_names.append(rf"Art\Textures\{tex_name}")
        pages_ini += [
            "",
            f"MappedImage {page}",
            f"  Texture = {tex_name}",
            "  TextureWidth = 1024",
            "  TextureHeight = 1024",
            "  Coords = Left:0 Top:0 Right:799 Bottom:599",
            "  Status = NONE",
            "End",
        ]
    pages_text = "\n".join(pages_ini) + "\n"
    if pages_text.startswith("'") or not pages_text.startswith(";"):
        raise SystemExit("pages INI must start with comment")
    got = mi_names(pages_text)
    want = [page for page, _ in SIDES.values()]
    if got != want:
        raise SystemExit(f"pages MappedImage set {got}")
    for stock in STOCK_PAGES:
        if stock in pages_text:
            raise SystemExit(f"stock page name leaked into new INI: {stock}")

    jf.set_text(data, P_PT, pt)
    jf.add_file(data, P_PAGES, pages_text)

    turkey_key = jf.norm(P_PT).lower()
    pages_key = jf.norm(P_PAGES).lower()
    changed = []
    for n, b in data:
        key = jf.norm(n).lower()
        if key in (turkey_key, pages_key):
            continue
        if key not in src_data_map or bytes(b) != src_data_map[key]:
            changed.append(n)
    if changed:
        raise SystemExit("unexpected DATA change:\n  " + "\n  ".join(changed[:20]))
    for p in FROZEN_DATA:
        if jf.raw_of(data, p) != frozen_raw[p]:
            raise SystemExit(f"frozen DATA changed: {p}")
    if jf.raw_of(data, P_PT) == src_pt_raw:
        raise SystemExit("PlayerTemplate not rewritten")

    new_art_keys = {jf.norm(p).lower() for p in new_art_names}
    art_changed = []
    for n, b in art:
        key = jf.norm(n).lower()
        if key in new_art_keys:
            if not n.lower().endswith(".tga"):
                raise SystemExit(f"non-TGA added: {n}")
            continue
        if key not in src_art_map or bytes(b) != src_art_map[key]:
            art_changed.append(n)
    if art_changed:
        raise SystemExit("unexpected ART change:\n  " + "\n  ".join(art_changed[:20]))
    w3d_new = [n for n, _ in art if n.lower().endswith(".w3d") and jf.norm(n).lower() not in src_art_map]
    if w3d_new:
        raise SystemExit("W3D added")
    if len(data) != 2884:
        raise SystemExit(f"DATA count {len(data)}")
    if len(art) != 4466:
        raise SystemExit(f"ART count {len(art)}")

    WS_OUT.mkdir(parents=True, exist_ok=True)
    dst_data = WS_OUT / "_SPEC_DATA_ONE.big"
    dst_art = WS_OUT / "_SPEC_ART_ONE.big"
    dst_data.write_bytes(jf.build_big_ordered(data))
    dst_art.write_bytes(jf.build_big_ordered(art))

    new_data_sha = jf.sha256_file(dst_data)
    new_art_sha = jf.sha256_file(dst_art)
    if new_data_sha == SRC_DATA_SHA or new_art_sha == SRC_ART_SHA:
        raise SystemExit("packed SHA unchanged")

    packed_d = jf.read_big_list(dst_data)
    packed_a = jf.read_big_list(dst_art)
    if len(packed_d) != 2884 or len(packed_a) != 4466:
        raise SystemExit("re-read count mismatch")
    packed_pt = jf.text_of(packed_d, P_PT)
    packed_pages = jf.text_of(packed_d, P_PAGES)
    if packed_pages.startswith("'") or not packed_pages.startswith(";"):
        raise SystemExit("packed pages INI parser prefix bad")
    packed_mi = set(mi_names(packed_pages))
    packed_art_stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in packed_a
        if n.lower().endswith(".tga")
    }
    for side, (page, _) in SIDES.items():
        val = load_screen_of(faction_block(packed_pt, f"Faction{side}"))
        if val != page:
            raise SystemExit(f"packed {side} LoadScreenImage={val}")
        if page not in packed_mi:
            raise SystemExit(f"packed missing MappedImage {page}")
        if page.lower() not in packed_art_stems:
            raise SystemExit(f"packed missing ART {page}.tga")
    for name, block in src_protected.items():
        if faction_block(packed_pt, name) != block:
            raise SystemExit(f"re-read protected changed: {name}")
    for p in FROZEN_DATA:
        if jf.raw_of(packed_d, p) != frozen_raw[p]:
            raise SystemExit(f"re-read frozen changed: {p}")
    for stock in STOCK_PAGES:
        if stock in packed_pages:
            raise SystemExit("packed pages INI reuses stock name")

    boot_safe = (
        not packed_pages.startswith("'")
        and packed_pages.startswith(";")
        and packed_mi == set(want)
        and len(packed_d) == 2884
        and len(packed_a) == 4466
        and all(jf.raw_of(packed_d, p) == frozen_raw[p] for p in FROZEN_DATA)
    )

    changed_files = "\n".join([
        "SPECTER1_FLAG_FACTION_PAGE_ONLY changed files",
        "",
        "DATA CHANGED",
        f"  {P_PT}",
        "    LoadScreenImage only, 17 remaining factions",
        *[f"    {row}" for row in rows],
        "",
        "DATA ADDED",
        f"  {P_PAGES}",
        "    17 MappedImage blocks, unique names, 1024x1024 / 799x599",
        *[f"    MappedImage {page}" for page, _ in SIDES.values()],
        "",
        "ART ADDED (17 faction logo pages only)",
        *[f"  {n}" for n in new_art_names],
        "",
        "NOT CHANGED",
        "  PlayerTemplate fields other than LoadScreenImage",
        "  FlagWaterMark EnabledImage SideIconImage GeneralImage",
        "  ScoreScreenImage Medallion*",
        "  CommandButton.ini Weapon.ini Upgrade.ini CommandSet.ini",
        "  Specter_RemainingFlags.INI Turkey_FactionImages.INI Specter_CampFlags.INI",
        "  building Object INIs",
        "  W3D / Flag_Hs / ExtraDraw / cloth / Model= / Animation=",
        "  stock SAFactionLogoPage_US SUFactionLogoPage_GLA SNFactionLogoPage_China",
        "  protected USA Iran Israel China Russia NATO Egypt NorthKorea Iraq",
    ]) + "\n"

    audit = "\n".join([
        "SPECTER1 FLAG FACTION PAGE ONLY",
        "STAGE = 01B LoadScreenImage / FactionLogoPage only",
        "BASELINE = SPECTER1_FLAG_STAGE_01_HUD_ONLY",
        f"BASELINE_DATA_SHA256 = {SRC_DATA_SHA}",
        f"BASELINE_ART_SHA256 = {SRC_ART_SHA}",
        f"NEW_DATA_SHA256 = {new_data_sha}",
        f"NEW_ART_SHA256 = {new_art_sha}",
        f"PACKED_DATA_FILES = {len(packed_d)}",
        f"PACKED_ART_FILES = {len(packed_a)}",
        "DUPLICATE_PACKED_PATHS = NO",
        "BIG_INTEGRITY = YES",
        f"BOOT_SAFE = {'YES' if boot_safe else 'NO'}",
        "FIX_APPLIED = YES (Stage 01B unique FactionLogoPage)",
        "INGAME_TESTED = NO",
        "STAGE_02_STARTED = NO",
        "LOADSCREENIMAGE_SIDES = 17",
        "MAPPEDIMAGE_PAGES = 17",
        "ART_PAGES_ADDED = 17",
        "PAGE_LAYOUT = 1024x1024 visible 799x599",
        "STOCK_PAGES_REUSED = NO",
        "TEXTURE_RESOLVE = YES",
        "LOADSCREENIMAGE_RESOLVE = YES",
        "PROTECTED_UNCHANGED = YES",
        "PLAYERTEMPLATE_OTHER_FIELDS = UNCHANGED",
        "COMMANDBUTTON_CHANGED = NO",
        "WEAPON_INI_CHANGED = NO",
        "UPGRADE_INI_CHANGED = NO",
        "COMMANDSET_CHANGED = NO",
        "OBJECT_INI_CHANGED = NO",
        "W3D_ADDED = NO",
        "FLAG_HS_ADDED = NO",
        "EXTRADRAW_ADDED = NO",
        "CLOTH_RESTORED = NO",
        "MODEL_CHANGED = NO",
        "ANIMATION_CHANGED = NO",
    ]) + "\n"

    changelog = """SPECTER1 FLAG_FACTION_PAGE_ONLY

Stage 01 HUD remaps booted but did not change country-select pages.
This pair remaps only PlayerTemplate LoadScreenImage for 17 remaining
countries onto unique <Country>FactionLogoPage MappedImages and
1024x1024 TGA pages (visible 799x599). Stock USA/GLA/China pages
are not reused.

Buildings, W3D, ExtraDraw, cloth, CommandButton, Weapon, Upgrade,
and CommandSet are frozen.

INGAME_TESTED = NO
STAGE_02_STARTED = NO
"""

    install = f"""SPECTER1_FLAG_FACTION_PAGE_ONLY
================================

Stage 01B = country select / load-screen faction pages only.
Baseline is the launching FLAG_STAGE_01_HUD_ONLY pair.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
4. Launch Specter.
5. Open country / faction select and check the 17 remaining sides.

Checksums:
  DATA SHA256 {new_data_sha}
  ART  SHA256 {new_art_sha}

BOOT_SAFE = {'YES' if boot_safe else 'NO'}
INGAME_TESTED = NO
STAGE_02_STARTED = NO
"""

    next_prompt = """You are continuing Specter flag restoration.

Stage 01B SPECTER1_FLAG_FACTION_PAGE_ONLY remaps only
PlayerTemplate LoadScreenImage onto unique FactionLogoPage
MappedImages and 1024x1024 TGA pages for 17 remaining countries.

INGAME_TESTED = NO
STAGE_02_STARTED = NO

Do not start Stage 02 until the user confirms a real Zero Hour
launch of this pair AND the large country-select pages.

Do not add cloth, Flag_Hs, W3D, ExtraDraw, or building Objects.
Do not modify Weapon / Upgrade / CommandSet / CommandButton.
Keep protected factions unchanged.
"""

    (WS_OUT / "CHANGED_FILES.txt").write_text(changed_files, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "INSTALL.txt").write_text(install, encoding="utf-8")
    (WS_OUT / "NEXT_AGENT_PROMPT.md").write_text(next_prompt, encoding="utf-8")
    (WS_OUT / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {new_data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {new_art_sha}\n",
        encoding="utf-8",
    )
    zpath = WS_OUT / f"{RELEASE_NAME}.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "INSTALL.txt",
            "changelog.txt",
            "audit.txt",
            "SHA256.txt",
            "CHANGED_FILES.txt",
        ):
            zf.write(WS_OUT / name, name)
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()
    (WS_OUT / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {new_data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {new_art_sha}\n"
        f"{RELEASE_NAME}.zip  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n",
        encoding="utf-8",
    )
    print(audit)
    print(changed_files)
    print("WROTE", dst_data, new_data_sha)
    print("ART", new_art_sha)
    print("ZIP", zpath, zpath.stat().st_size, zip_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
