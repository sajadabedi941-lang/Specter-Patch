#!/usr/bin/env python3
"""Isolated parser fix: Turkey_FactionImages.INI leading apostrophe.

STRIP_02 still crashed. Forensic audit found this file starts with `'`.
Only that character is removed. ART is copied byte-identical.
PlayerTemplate, CommandButton, the other two new MI files, Objects,
Weapon/Upgrade/CommandSet are frozen.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_FLAG_ART_CLONE_STRIP_02/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_FLAG_ART_CLONE_STRIP_02/_SPEC_ART_ONE.big")
SRC_DATA_SHA = "3e42c369fb30e229062fcbf29feafb15c9e59472dc16757d8e5f0c0092813221"
SRC_ART_SHA = "c16055702267e59770a7f657f843ea49840889b453a5c0611e8971045afe05b7"

WS_OUT = Path("/workspace/patch/Release/SPECTER1_FLAG_TURKEY_MI_PARSE_01")
RELEASE_NAME = "SPECTER1_FLAG_TURKEY_MI_PARSE_01"

P_TURKEY = r"Data\INI\MappedImages\HandCreated\Turkey_FactionImages.INI"
P_REMAIN = r"Data\INI\MappedImages\HandCreated\Specter_RemainingFlags.INI"
P_CAMP = r"Data\INI\MappedImages\HandCreated\Specter_CampFlags.INI"
P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_UPGRADE = r"Data\INI\Upgrade.ini"
P_CMDSET = r"Data\INI\CommandSet.ini"

KEEP_MI = (
    "WatermarkTurkey",
    "GameinfoTurkey",
    "Turkey_Logo",
    "SSObserverTurkey",
    "Turkey_Flag",
)
FROZEN = (P_PT, P_PT_PATCH, P_CMDBTN, P_REMAIN, P_CAMP, P_WEAPON, P_UPGRADE, P_CMDSET)


def main() -> int:
    if jf.sha256_file(SRC_DATA) != SRC_DATA_SHA:
        raise SystemExit("STRIP_02 DATA SHA mismatch")
    if jf.sha256_file(SRC_ART) != SRC_ART_SHA:
        raise SystemExit("STRIP_02 ART SHA mismatch")

    data = jf.read_big_list(SRC_DATA)
    if len(data) != 2883:
        raise SystemExit(f"DATA count {len(data)}")

    src_map = {jf.norm(n).lower(): bytes(b) for n, b in data}
    frozen_raw = {p: jf.raw_of(data, p) for p in FROZEN}

    raw = jf.raw_of(data, P_TURKEY)
    text = raw.decode("latin-1", errors="replace")
    if not text.startswith("'"):
        raise SystemExit("expected leading apostrophe on Turkey_FactionImages.INI")
    if not text[1:].lstrip().startswith(";"):
        raise SystemExit("expected comment after apostrophe")
    new_text = text[1:]
    if new_text.startswith("'"):
        raise SystemExit("leading apostrophe still present")
    if not new_text.startswith(";"):
        raise SystemExit("file must start with ; after fix")
    for name in KEEP_MI:
        if not re.search(rf"(?im)^MappedImage\s+{re.escape(name)}\s*$", new_text):
            raise SystemExit(f"missing MappedImage {name}")
    # blocks after the first line must be unchanged
    old_rest = text.splitlines(keepends=True)[1:]
    new_rest = new_text.splitlines(keepends=True)[1:]
    if old_rest != new_rest:
        raise SystemExit("MappedImage body changed")

    jf.set_text(data, P_TURKEY, new_text)

    # every other DATA file must still be the STRIP_02 bytes
    turkey_key = jf.norm(P_TURKEY).lower()
    changed = []
    for n, b in data:
        key = jf.norm(n).lower()
        if key == turkey_key:
            continue
        if bytes(b) != src_map[key]:
            changed.append(n)
    if changed:
        raise SystemExit("non-Turkey DATA changed:\n  " + "\n  ".join(changed[:20]))
    for p in FROZEN:
        if jf.raw_of(data, p) != frozen_raw[p]:
            raise SystemExit(f"frozen file changed: {p}")

    dnames = [jf.norm(n).lower() for n, _ in data]
    if len(dnames) != len(set(dnames)):
        raise SystemExit("duplicate DATA paths")
    if len(data) != 2883:
        raise SystemExit("DATA file count changed")

    packed_turkey = jf.text_of(data, P_TURKEY)
    if packed_turkey.startswith("'"):
        raise SystemExit("packed Turkey MI still starts with apostrophe")
    if not packed_turkey.startswith(";"):
        raise SystemExit("packed Turkey MI does not start with comment")

    WS_OUT.mkdir(parents=True, exist_ok=True)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(jf.build_big_ordered(data))
    shutil.copy2(SRC_ART, WS_OUT / "_SPEC_ART_ONE.big")

    new_data_sha = jf.sha256_file(WS_OUT / "_SPEC_DATA_ONE.big")
    new_art_sha = jf.sha256_file(WS_OUT / "_SPEC_ART_ONE.big")
    if new_art_sha != SRC_ART_SHA:
        raise SystemExit("ART must stay STRIP_02 bytes")
    if new_data_sha == SRC_DATA_SHA:
        raise SystemExit("DATA SHA unchanged; Turkey MI was not rewritten")

    packed_d = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    packed_a = jf.read_big_list(WS_OUT / "_SPEC_ART_ONE.big")
    if packed_d[0][0] is None or packed_a[0][0] is None:
        raise SystemExit("re-read BIG failed")
    if len(packed_d) != 2883 or len(packed_a) != 4449:
        raise SystemExit(f"packed count {len(packed_d)}/{len(packed_a)}")
    if jf.text_of(packed_d, P_TURKEY).startswith("'"):
        raise SystemExit("re-read Turkey MI still has apostrophe")
    for p in FROZEN:
        if jf.raw_of(packed_d, p) != frozen_raw[p]:
            raise SystemExit(f"re-read frozen changed: {p}")
    # confirm only one DATA file differs from source
    packed_map = {jf.norm(n).lower(): bytes(b) for n, b in packed_d}
    diffs = [k for k in packed_map if packed_map[k] != src_map[k]]
    if diffs != [turkey_key]:
        raise SystemExit(f"unexpected DATA diffs: {diffs}")

    boot_safe = (
        new_art_sha == SRC_ART_SHA
        and not jf.text_of(packed_d, P_TURKEY).startswith("'")
        and jf.text_of(packed_d, P_TURKEY).startswith(";")
        and diffs == [turkey_key]
    )

    first = jf.text_of(packed_d, P_TURKEY).splitlines()[0]
    audit = "\n".join([
        "SPECTER1 TURKEY MAPPEDIMAGE PARSER FIX",
        "BASELINE = SPECTER1_FLAG_ART_CLONE_STRIP_02",
        f"BASELINE_DATA_SHA256 = {SRC_DATA_SHA}",
        f"BASELINE_ART_SHA256 = {SRC_ART_SHA}",
        f"NEW_DATA_SHA256 = {new_data_sha}",
        f"NEW_ART_SHA256 = {new_art_sha}",
        f"PACKED_DATA_FILES = {len(packed_d)}",
        f"PACKED_ART_FILES = {len(packed_a)}",
        "DUPLICATE_PACKED_PATHS = NO",
        "BIG_INTEGRITY = YES",
        f"BOOT_SAFE = {'YES' if boot_safe else 'NO'}",
        "FIX_APPLIED = YES (Turkey_FactionImages parser fix)",
        "INGAME_TESTED = NO",
        "ART_CHANGED = NO",
        "DATA_CHANGED = YES (one file)",
        f"CHANGED_FILE = {P_TURKEY}",
        f"FIRST_LINE = {first}",
        "LEADING_APOSTROPHE = REMOVED",
        "MAPPEDIMAGE_BLOCKS_KEPT = WatermarkTurkey GameinfoTurkey Turkey_Logo SSObserverTurkey Turkey_Flag",
        "PLAYERTEMPLATE_CHANGED = NO",
        "COMMANDBUTTON_CHANGED = NO",
        "SPECTER_REMAININGFLAGS_CHANGED = NO",
        "SPECTER_CAMPFLAGS_CHANGED = NO",
        "WEAPON_INI_CHANGED = NO",
        "UPGRADE_INI_CHANGED = NO",
        "COMMANDSET_CHANGED = NO",
        "OBJECT_INI_CHANGED = NO",
        "FLAGS_RESTORED = NO",
        "CLOTH_RESTORED = NO",
        "EXTRA_DRAWS_RESTORED = NO",
    ]) + "\n"

    changelog = """SPECTER1 Turkey MappedImage parser fix

STRIP_02 still crashed at initialization. Forensic audit found
Data\\INI\\MappedImages\\HandCreated\\Turkey_FactionImages.INI starts
with a stray apostrophe before the comment.

This packer removes only that apostrophe. The five MappedImage blocks
are unchanged. ART is the STRIP_02 pair, byte-identical.

PlayerTemplate, CommandButton, Specter_RemainingFlags,
Specter_CampFlags, Objects, Weapon, Upgrade, CommandSet are frozen.

INGAME_TESTED = NO
"""

    install = f"""SPECTER1_FLAG_TURKEY_MI_PARSE_01
================================

Isolated parser fix for Turkey_FactionImages.INI.
ART is unchanged from SPECTER1_FLAG_ART_CLONE_STRIP_02.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
4. Launch Specter.

Checksums:
  DATA SHA256 {new_data_sha}
  ART  SHA256 {new_art_sha}

FIX_APPLIED = YES (Turkey_FactionImages parser fix)
INGAME_TESTED = NO
"""

    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "INSTALL.txt").write_text(install, encoding="utf-8")
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
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", new_data_sha)
    print("ART", new_art_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
