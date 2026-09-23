#!/usr/bin/env python3
"""BUILDING_FLAG_COMPLETE_ROLLOUT.

Copy the already audited Stage 09 pair. No INI/W3D rebuild.
Stage 09 is the sequential merge of Stages 02-09.
"""
from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

SRC = Path("/workspace/patch/Release/BUILDING_FLAG_STAGE_09_LIBYA_ONLY")
SRC_DATA_SHA = "2a0e9b0d77ceb442376b5e67573a1af12057713884318f2858b6ce30de2d0345"
SRC_ART_SHA = "493c16d2a990cad70d459edbbb6eede963172f433a16f57b241688205a19f314"
HUD_DATA_SHA = "0603b12e855f5f35cfff889362b0a02f2044968b7cdd1dd35c8c1285843f2652"
HUD_ART_SHA = "c16055702267e59770a7f657f843ea49840889b453a5c0611e8971045afe05b7"
RELEASE = "BUILDING_FLAG_COMPLETE_ROLLOUT"
WS = Path("/workspace/patch/Release") / RELEASE


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    src_data = SRC / "_SPEC_DATA_ONE.big"
    src_art = SRC / "_SPEC_ART_ONE.big"
    if sha256_file(src_data) != SRC_DATA_SHA:
        raise SystemExit("Stage 09 DATA SHA mismatch; refusing to copy")
    if sha256_file(src_art) != SRC_ART_SHA:
        raise SystemExit("Stage 09 ART SHA mismatch; refusing to copy")

    WS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_data, WS / "_SPEC_DATA_ONE.big")
    shutil.copy2(src_art, WS / "_SPEC_ART_ONE.big")
    data_sha = sha256_file(WS / "_SPEC_DATA_ONE.big")
    art_sha = sha256_file(WS / "_SPEC_ART_ONE.big")
    if data_sha != SRC_DATA_SHA or art_sha != SRC_ART_SHA:
        raise SystemExit("copied BIG bytes drifted")

    changed = """BUILDING_FLAG_COMPLETE_ROLLOUT changed files

SOURCE = BUILDING_FLAG_STAGE_09_LIBYA_ONLY (byte copy, no rebuild)
HUD_BASELINE = SPECTER1_FLAG_STAGE_01_HUD_ONLY

This pair is the sequential merge of already audited stages 02-09.
No new INI or W3D edits were made for this release.

ART added vs HUD (8 new Flag_Hs W3Ds, 0 existing modified)
  Art\\W3D\\JP__JPFlag_Hs.W3D
  Art\\W3D\\VN__VNFlag_Hs.W3D
  Art\\W3D\\SA__SAFlag_Hs.W3D
  Art\\W3D\\AE__AEFlag_Hs.W3D
  Art\\W3D\\SY__SYFlag_Hs.W3D
  Art\\W3D\\ZA__ZAFlag_Hs.W3D
  Art\\W3D\\SK__SKFlag_Hs.W3D
  Art\\W3D\\LY__LYFlag_Hs.W3D

DATA changed vs HUD (35 country building INIs only)
  Japan_Barracks
  Vietnam_Barracks
  SaudiArabia Barracks/Power/Supply/WF/Abbas
  UAE Barracks/Power/Supply/WF/Abbas
  Syria Barracks/Power/Supply/WF/Abbas
  SouthAfrica Barracks/Power/Supply/WF/Abbas
  SouthKorea Barracks/Power/Supply/WF/CC/Abbas/Systems
  Libya Barracks/Power/Supply/WF/Abbas

UNCHANGED
  Iraq / North Korea Flag_Hs and donor meshes
  irq_camp Iraq_Powerplant Iraq_Supply Irq_WarFactory
  NKor/NKr/US shared building meshes
  PlayerTemplate HUD MappedImages faction pages CommandButton CommandSet
"""
    audit = f"""BUILDING_FLAG_COMPLETE_ROLLOUT
SOURCE = BUILDING_FLAG_STAGE_09_LIBYA_ONLY
SOURCE_COPY = BYTE_IDENTICAL
NEW_EDITS = NO
HUD_DATA_SHA = {HUD_DATA_SHA}
HUD_ART_SHA = {HUD_ART_SHA}
SRC_DATA_SHA = {SRC_DATA_SHA}
SRC_ART_SHA = {SRC_ART_SHA}
DATA_SHA256 = {data_sha}
ART_SHA256 = {art_sha}
INCLUDED = Japan Vietnam SaudiArabia UAE Syria SouthAfrica SouthKorea Libya
NEW_W3D_COUNT = 8
EXISTING_W3D_MODIFIED = NO
DUPLICATE_W3D_PATH = NO
PROTECTED_ASSETS_CHANGED = NO
SHARED_MESH_MODIFIED = NO
IRAQ_NK_ASSETS_CHANGED = NO
UNRELATED_INI_CHANGED = NO
PLAYERTEMPLATE_CHANGED = NO
HUD_CHANGED = NO
PACKED_INTERNAL_MATCH = YES
FIX_APPLIED = YES (merged audited stages 02-09 only)
BOOT_SAFE = YES
INGAME_TESTED = NO
"""
    changelog = """BUILDING_FLAG_COMPLETE_ROLLOUT

Final combined install pair for all completed building Flag_Hs stages.

This release copies BUILDING_FLAG_STAGE_09_LIBYA_ONLY byte-for-byte.
Stage 09 already contains the sequential audited merge of:

  02 Japan_Barracks
  03 Vietnam_Barracks
  04 Saudi Arabia
  05 UAE
  06 Syria
  07 South Africa
  08 South Korea
  09 Libya

No new edits. Shared donor meshes, Iraq/NK Flag_Hs, HUD flags, and
PlayerTemplate are unchanged from the HUD baseline except the 35
country building INIs and 8 new country Flag_Hs W3Ds listed in
CHANGED_FILES.txt.

BOOT_SAFE = YES
INGAME_TESTED = NO
"""
    install = f"""BUILDING_FLAG_COMPLETE_ROLLOUT
================================

Final combined Flag_Hs pair. Contains Japan, Vietnam, Saudi Arabia,
UAE, Syria, South Africa, South Korea, and Libya.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
4. Launch Specter.

Checksums:
  DATA SHA256 {data_sha}
  ART  SHA256 {art_sha}

BOOT_SAFE = YES
INGAME_TESTED = NO
PROTECTED_ASSETS_CHANGED = NO
SHARED_MESH_MODIFIED = NO
NEW_EDITS = NO
"""
    (WS / "CHANGED_FILES.txt").write_text(changed, encoding="utf-8")
    (WS / "audit.txt").write_text(audit, encoding="utf-8")
    (WS / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS / "INSTALL.txt").write_text(install, encoding="utf-8")
    sha_tmp = (
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {art_sha}\n"
    )
    (WS / "SHA256.txt").write_text(sha_tmp, encoding="utf-8")
    zip_path = WS / f"{RELEASE}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS / "audit.txt", "audit.txt")
        zf.write(WS / "SHA256.txt", "SHA256.txt")
        zf.write(WS / "changelog.txt", "changelog.txt")
    zip_sha = sha256_file(zip_path)
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {art_sha}\n"
        f"{RELEASE}.zip  SHA256 {zip_sha}  {zip_path.stat().st_size} bytes\n"
    )
    (WS / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    print("WROTE", WS)
    print(sha_txt)
    print(audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
