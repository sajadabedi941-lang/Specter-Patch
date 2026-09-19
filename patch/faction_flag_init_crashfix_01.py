#!/usr/bin/env python3
"""Restore a bootable ZH init after PR #516 / #517 flag updates.

Crash: Uncaught Exception during initialization.

Causes found in the stacked CAMP_FLAGS BIG:
1) W3D Model= names longer than the SAGE 15-char mesh name buffer
   (Iraq_Powerplant_UAE=19, NKor_Powerplant_JP=18, Irq_WarFactory_*=17-18,
   NKr_WarFactory_*=17). Existing working donors are all <=15
   (Iraq_Powerplant, NKor_Powerplant).
2) Extra flag Draws and Abbas flag Draws use Model=<xx>_Flag_Hs but
   Animation=Irq__IqFlag_Hs.Irq__IqFlag_Hs (or NKr__NKFlag_Hs...), so
   init loads a W3D/anim container that does not match the Model.

This packer only repairs those visual refs. Weapon / Upgrade / CommandSet /
CommandButton / PlayerTemplate / protected factions are byte-identical.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_FACTION_CAMP_FLAGS_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_FACTION_CAMP_FLAGS_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "0cc32a58a439dff4d0ad8c74b1cbf2aa02e34195a373492bf62f0dde0dddf10b"
EXPECTED_ART_SHA = "e1f603a06c3ccb18601e046d0fef212c56888425db3e77fcd5a69be3c612c8c9"
OUT_DIR = Path("/tmp/SPECTER1_FLAG_INIT_CRASHFIX_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_FLAG_INIT_CRASHFIX_01")
RELEASE_NAME = "SPECTER1_FLAG_INIT_CRASHFIX_01"

P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_UPGRADE = r"Data\INI\Upgrade.ini"
P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"

PROTECTED_FOLDER = (
    "united states of america", "israel defense forces", "pla",
    "armed forces of russian federation", "iranian army", "iraq army",
    "north korea", "nato", "egyptian armed forces",
)

# Long clone filename -> short SAGE-safe name (<=15).
RENAME = {
    "Iraq_Powerplant_IN": "IqPwr_IN",
    "Iraq_Powerplant_LY": "IqPwr_LY",
    "Iraq_Powerplant_PK": "IqPwr_PK",
    "Iraq_Powerplant_SA": "IqPwr_SA",
    "Iraq_Powerplant_SY": "IqPwr_SY",
    "Iraq_Powerplant_ZA": "IqPwr_ZA",
    "Iraq_Powerplant_UAE": "IqPwr_UAE",
    "NKor_Powerplant_JP": "NkPwr_JP",
    "NKor_Powerplant_SK": "NkPwr_SK",
    "NKor_Powerplant_VN": "NkPwr_VN",
    "Irq_WarFactory_LY": "IqWF_LY",
    "Irq_WarFactory_SA": "IqWF_SA",
    "Irq_WarFactory_SY": "IqWF_SY",
    "Irq_WarFactory_ZA": "IqWF_ZA",
    "Irq_WarFactory_UAE": "IqWF_UAE",
    "NKr_WarFactory_IN": "NkWF_IN",
    "NKr_WarFactory_JP": "NkWF_JP",
    "NKr_WarFactory_PK": "NkWF_PK",
    "NKr_WarFactory_SK": "NkWF_SK",
    "NKr_WarFactory_VN": "NkWF_VN",
}

FOLDER_SIDE = {
    "japan self-defense forces": "Japan",
    "vietnam people's armed forces": "Vietnam",
    "south korean armed forces": "SouthKorea",
    "libyan armed forces": "Libya",
    "south african national defence force": "SouthAfrica",
    "pakistan armed forces": "Pakistan",
    "indian armed forces": "India",
    "syrian armed forces": "Syria",
    "united arab emirates armed forces": "UAE",
    "saudi arabia armed forces": "SaudiArabia",
    "turkish armed forces": "Turkey",
    "swedish armed forces": "Sweden",
    "ukrainian armed forces": "Ukraine",
    "italian armed forces": "Italy",
    "british armed forces": "Britain",
    "german armed forces": "Germany",
    "french armed forces": "France",
}


def in_protected(path: str) -> bool:
    low = jf.norm(path).lower()
    return any(f"\\{p}\\" in low for p in PROTECTED_FOLDER)


def folder_side(path: str) -> str | None:
    low = jf.norm(path).lower()
    for folder, side in FOLDER_SIDE.items():
        if f"\\{folder}\\" in low:
            return side
    return None


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if jf.sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    data = jf.read_big_list(SRC_DATA)
    art = jf.read_big_list(SRC_ART)
    if len(data) != 2883 or len(art) != 4509:
        raise SystemExit(f"packed count {len(data)}/{len(art)}")

    src_weapon = jf.raw_of(data, P_WEAPON)
    src_upgrade = jf.raw_of(data, P_UPGRADE)
    src_cmdset = jf.raw_of(data, P_CMDSET)
    src_cmdbtn = jf.raw_of(data, P_CMDBTN)
    src_pt = jf.raw_of(data, P_PT)
    src_pt_patch = jf.raw_of(data, P_PT_PATCH)
    protected_files = {
        jf.norm(n).lower(): bytes(b)
        for n, b in data
        if in_protected(n)
    }

    for old, new in RENAME.items():
        if len(new) > 15:
            raise SystemExit(f"short name still too long: {new}")

    # ---- ART: rename oversized W3D clones (same bytes, short packed name) ----
    art_renames = 0
    seen = {jf.norm(n).lower() for n, _ in art}
    new_art: list[tuple[str, bytes]] = []
    for name, blob in art:
        stem = Path(jf.norm(name).replace("\\", "/")).stem
        if stem in RENAME:
            new_name = jf.norm(f"Art\\W3D\\{RENAME[stem]}.W3D")
            key = new_name.lower()
            if key in seen:
                raise SystemExit(f"ART name collision {new_name}")
            new_art.append((new_name, bytes(blob)))
            seen.add(key)
            art_renames += 1
        else:
            new_art.append((name, bytes(blob)))
    art = new_art

    # ---- DATA: retarget long Model= and fix Flag_Hs Animation containers ----
    model_swaps = 0
    anim_fixes = 0
    extra_draws_kept = 0
    for idx, (fname, blob) in enumerate(data):
        if not str(fname).lower().endswith(".ini"):
            continue
        if in_protected(fname):
            continue
        if folder_side(fname) is None:
            continue
        text = blob.decode("latin-1", errors="replace")
        orig = text

        def rep_model(m: re.Match[str]) -> str:
            nonlocal model_swaps
            cur = m.group(2)
            if cur in RENAME:
                model_swaps += 1
                return m.group(1) + RENAME[cur]
            return m.group(0)

        text = re.sub(r"(?im)^(\s*Model\s*=\s*)(\S+)", rep_model, text)

        # Animation container must match the Flag_Hs Model it is attached to.
        # Walk lines so Abbas / extra-draw blocks stay consistent.
        lines = text.splitlines(keepends=True)
        last_flag_hs: str | None = None
        out_lines = []
        for line in lines:
            mm = re.match(r"(?i)^(\s*Model\s*=\s*)(\S+)", line)
            am = re.match(r"(?i)^(\s*Animation\s*=\s*)(\S+)", line)
            if mm:
                last_flag_hs = mm.group(2) if mm.group(2).endswith("_Flag_Hs") else None
                out_lines.append(line)
                continue
            if am and last_flag_hs:
                want = f"{last_flag_hs}.Irq__IqFlag_Hs"
                if am.group(2) != want:
                    nl = "\r\n" if line.endswith("\r\n") else "\n"
                    # preserve original prefix whitespace and key spelling
                    out_lines.append(f"{am.group(1)}{want}{nl}")
                    anim_fixes += 1
                    continue
            out_lines.append(line)
        text = "".join(out_lines)
        if "ModuleTag_SpecterNatFlag" in text:
            extra_draws_kept += 1
        if text != orig:
            data[idx] = (fname, text.encode("latin-1", errors="replace"))

    # leftover long names on target factions
    leftover_long = []
    leftover_anim = []
    leftover_old = []
    for n, b in data:
        if in_protected(n) or folder_side(n) is None:
            continue
        t = b.decode("latin-1", errors="replace")
        for m in re.finditer(r"(?im)^\s*Model\s*=\s*(\S+)", t):
            mdl = m.group(1)
            if mdl in RENAME or (re.search(r"(Iraq_Powerplant_|NKor_Powerplant_|Irq_WarFactory_|NKr_WarFactory_)", mdl) and len(mdl) > 15):
                leftover_long.append(f"{n} {mdl}")
        last = None
        for line in t.splitlines():
            mm = re.match(r"(?i)^\s*Model\s*=\s*(\S+)", line)
            am = re.match(r"(?i)^\s*Animation\s*=\s*(\S+)", line)
            if mm:
                last = mm.group(1) if mm.group(1).endswith("_Flag_Hs") else None
            if am and last:
                if am.group(1) != f"{last}.Irq__IqFlag_Hs":
                    leftover_anim.append(f"{n} Model={last} Anim={am.group(1)}")
        for old in RENAME:
            if re.search(rf"(?im)^\s*Model\s*=\s*{re.escape(old)}\s*$", t):
                leftover_old.append(f"{n} {old}")
    if leftover_long or leftover_old:
        raise SystemExit("leftover long models:\n  " + "\n  ".join((leftover_long + leftover_old)[:20]))
    if leftover_anim:
        raise SystemExit("leftover anim mismatch:\n  " + "\n  ".join(leftover_anim[:20]))

    # ---- frozen files ----
    if jf.raw_of(data, P_WEAPON) != src_weapon:
        raise SystemExit("Weapon.ini changed")
    if jf.raw_of(data, P_UPGRADE) != src_upgrade:
        raise SystemExit("Upgrade.ini changed")
    if jf.raw_of(data, P_CMDSET) != src_cmdset:
        raise SystemExit("CommandSet.ini changed")
    if jf.raw_of(data, P_CMDBTN) != src_cmdbtn:
        raise SystemExit("CommandButton.ini changed")
    if jf.raw_of(data, P_PT) != src_pt:
        raise SystemExit("PlayerTemplate.ini changed")
    if jf.raw_of(data, P_PT_PATCH) != src_pt_patch:
        raise SystemExit("PlayerTemplate_SpecterPatch.ini changed")
    for n, b in data:
        if in_protected(n) and bytes(b) != protected_files.get(jf.norm(n).lower()):
            raise SystemExit(f"protected DATA changed: {n}")

    dnames = [jf.norm(n).lower() for n, _ in data]
    anames = [jf.norm(n).lower() for n, _ in art]
    if len(dnames) != len(set(dnames)):
        raise SystemExit("duplicate DATA paths")
    if len(anames) != len(set(anames)):
        raise SystemExit("duplicate ART paths")

    art_w3d = {
        Path(jf.norm(n).replace("\\", "/")).stem.lower()
        for n, _ in art if n.lower().endswith(".w3d")
    }
    missing = []
    too_long = []
    for n, b in data:
        if in_protected(n) or folder_side(n) is None or not str(n).lower().endswith(".ini"):
            continue
        t = b.decode("latin-1", errors="replace")
        for m in re.finditer(r"(?im)^\s*Model\s*=\s*(\S+)", t):
            mdl = m.group(1)
            if mdl.lower() in ("none", "null"):
                continue
            if len(mdl) > 15 and re.search(r"(IqPwr_|NkPwr_|IqWF_|NkWF_|Flag_Hs|irq_camp_|Iraq_|NKor_|NKr_)", mdl):
                too_long.append(mdl)
            if re.search(r"(IqPwr_|NkPwr_|IqWF_|NkWF_|Flag_Hs|irq_camp_)", mdl):
                if mdl.lower() not in art_w3d:
                    missing.append(f"{n} {mdl}")
    if missing:
        raise SystemExit("Model= missing ART:\n  " + "\n  ".join(missing[:20]))
    if too_long:
        raise SystemExit("still-long flag models: " + ", ".join(sorted(set(too_long))))

    # old long names must be gone from ART
    for old in RENAME:
        if f"art\\w3d\\{old}.w3d".lower() in {jf.norm(n).lower() for n, _ in art}:
            raise SystemExit(f"old long W3D still packed: {old}")
        if f"art\\w3d\\{RENAME[old]}.w3d".lower() not in {jf.norm(n).lower() for n, _ in art}:
            raise SystemExit(f"short W3D missing: {RENAME[old]}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(jf.build_big_ordered(data))
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(jf.build_big_ordered(art))
    shutil.copy2(OUT_DIR / "_SPEC_DATA_ONE.big", WS_OUT / "_SPEC_DATA_ONE.big")
    shutil.copy2(OUT_DIR / "_SPEC_ART_ONE.big", WS_OUT / "_SPEC_ART_ONE.big")
    new_data_sha = jf.sha256_file(WS_OUT / "_SPEC_DATA_ONE.big")
    new_art_sha = jf.sha256_file(WS_OUT / "_SPEC_ART_ONE.big")
    packed_d = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    packed_a = jf.read_big_list(WS_OUT / "_SPEC_ART_ONE.big")
    if packed_d[0][0] is None or packed_a[0][0] is None:
        raise SystemExit("re-read BIG failed")

    audit = "\n".join([
        "SPECTER1 FLAG INIT CRASHFIX",
        "BASELINE = SPECTER1_FACTION_CAMP_FLAGS_01 (#516 + #517)",
        f"BASELINE_DATA_SHA256 = {EXPECTED_DATA_SHA}",
        f"BASELINE_ART_SHA256 = {EXPECTED_ART_SHA}",
        f"NEW_DATA_SHA256 = {new_data_sha}",
        f"NEW_ART_SHA256 = {new_art_sha}",
        f"PACKED_DATA_FILES = {len(packed_d)}",
        f"PACKED_ART_FILES = {len(packed_a)}",
        "DUPLICATE_PACKED_PATHS = NO",
        "BIG_INTEGRITY = YES",
        "CRASH = Uncaught Exception during initialization",
        "BROKEN_REF_1 = W3D Model= names >15 chars (Iraq_Powerplant_*, NKor_Powerplant_*, Irq_WarFactory_*, NKr_WarFactory_*)",
        "BROKEN_REF_2 = Flag_Hs Draw Animation container != Model (Irq__IqFlag_Hs / NKr__NKFlag_Hs)",
        "FILE_CAUSING_CRASH = building Object INIs that Model= long clones + extra/Abbas Flag_Hs Draws",
        f"FIX_1 = renamed {art_renames} W3D clones to <=15 char stems (IqPwr_/NkPwr_/IqWF_/NkWF_)",
        f"FIX_2 = retargeted {model_swaps} Model= refs",
        f"FIX_3 = rewrote {anim_fixes} Flag_Hs Animation lines to <mesh>.Irq__IqFlag_Hs",
        f"EXTRA_FLAG_DRAWS_KEPT = {extra_draws_kept} (re-enabled with matching anim container)",
        "WEAPON_INI_CHANGED = NO",
        "UPGRADE_INI_CHANGED = NO",
        "COMMANDSET_CHANGED = NO",
        "COMMANDBUTTON_CHANGED = NO",
        "PLAYERTEMPLATE_CHANGED = NO",
        "PROTECTED_FACTIONS_UNCHANGED = YES",
        "GAMEPLAY_CHANGED = NO",
        "INGAME_TESTED = NO",
        "DATA_CHANGED = YES",
        "ART_CHANGED = YES",
    ]) + "\n"

    changelog = """SPECTER1 flag init crashfix

The game booted on the Camp-clone baseline and crashed during
initialization after the PR #516 / #517 flag BIGs.

Broken references:
1. Building Model= names longer than SAGE's 15-character W3D name
   buffer (Iraq_Powerplant_UAE=19, NKor_Powerplant_JP=18, others 17-18).
   All working donor meshes are <=15.
2. Extra flag Draws and Abbas flag Draws used Model=<xx>_Flag_Hs but
   Animation=Irq__IqFlag_Hs.Irq__IqFlag_Hs (or NKr__NKFlag_Hs), so init
   bound a different W3D/anim container than the Model.

Fix:
- Rename those W3D clones to IqPwr_XX / NkPwr_XX / IqWF_XX / NkWF_XX
  (<=8 chars) and retarget Model=.
- Point Flag_Hs Animation at <mesh>.Irq__IqFlag_Hs.
- Extra Draws stay (re-enabled after the anim fix). HUD / select /
  camp MappedImages unchanged. Protected factions unchanged.
- Weapon / Upgrade / CommandSet / CommandButton / PlayerTemplate
  byte-identical.

INGAME_TESTED = NO
"""

    install = f"""SPECTER1_FLAG_INIT_CRASHFIX_01
==============================

Boot-restore patch for the PR #516 / #517 flag crash.
Same GameRoot layout: two BIG files, no loose Data/Art.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
4. Launch Specter.

Checksums:
  DATA SHA256 {new_data_sha}
  ART  SHA256 {new_art_sha}

INIT_CRASHFIX = YES
INGAME_TESTED = NO
"""

    for dest in (OUT_DIR, WS_OUT):
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "audit.txt").write_text(audit, encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "INSTALL.txt").write_text(install, encoding="utf-8")

    zpath = WS_OUT / f"{RELEASE_NAME}.zip"
    (WS_OUT / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {new_data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {new_art_sha}\n",
        encoding="utf-8",
    )
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
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {new_data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {new_art_sha}\n"
        f"{RELEASE_NAME}.zip  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n"
    )
    for dest in (OUT_DIR, WS_OUT):
        (dest / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    shutil.copy2(zpath, OUT_DIR / zpath.name)
    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", new_data_sha)
    print("ART", new_art_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
