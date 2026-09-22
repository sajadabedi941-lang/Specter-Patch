#!/usr/bin/env python3
"""ART-only strip of unused #516/#517/#518 flag W3D clones.

DATA stays byte-identical to SPECTER1_FLAG_OBJECT_BOOT_01.
ART is rebuilt from last-known-launch camp-clone ART, plus HUD TGAs
required by the frozen MappedImages. No Object/Draw/Model/Animation edits.

Release: SPECTER1_FLAG_ART_CLONE_STRIP_02
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/tmp/flag_audit/current/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/flag_audit/current/_SPEC_ART_ONE.big")
GOOD_ART = Path("/tmp/flag_audit/campclone/_SPEC_ART_ONE.big")

SRC_DATA_SHA = "3e42c369fb30e229062fcbf29feafb15c9e59472dc16757d8e5f0c0092813221"
SRC_ART_SHA = "2b84d7836b6560d22f32ce2c6687a167a52515ea2f70aeecbc934968fccb9af1"
GOOD_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"

WS_OUT = Path("/workspace/patch/Release/SPECTER1_FLAG_ART_CLONE_STRIP_02")
RELEASE_NAME = "SPECTER1_FLAG_ART_CLONE_STRIP_02"

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

# Packed W3D stems introduced by #516/#517/#518. Ban these from the new ART.
BANNED_W3D_STEM = re.compile(
    r"(?i)^("
    r"IqPwr_.+"
    r"|NkPwr_.+"
    r"|IqWF_.+"
    r"|NkWF_.+"
    r"|irq_camp_.+"
    r"|Iraq_Supply_.+"
    r"|NKor_Supply_.+"
    r"|NKr_Command_.+"
    r"|(DE|FR|IN|IT|JP|LY|PK|SA|SE|SK|SY|TR|UA|UAE|UK|VN|ZA)_Flag_Hs"
    r")$"
)
KEEP_ORIGINAL_HS = {"irq__iqflag_hs", "nkr__nkflag_hs", "flag_hs"}

KEEP_TEX_STEMS = {
    "de_flag", "fr_flag", "in_flag", "it_flag", "jp_flag",
    "ly_flag", "pk_flag", "sa_flag", "se_flag", "sk_flag",
    "sy_flag", "tr_flag", "ua_flag", "uae_flag", "uk_flag",
    "vn_flag", "za_flag",
    "gameinfoturkey", "ssobserverturkey", "turkey_flag",
    "turkey_logo", "watermarkturkey",
}

CLONE_MODEL_RE = re.compile(
    r"(?i)(IqPwr_|NkPwr_|IqWF_|NkWF_|irq_camp_[A-Za-z]"
    r"|Iraq_Powerplant_|NKor_Powerplant_|NKr_Powerplant_"
    r"|Irq_WarFactory_|NKr_WarFactory_|Iraq_Supply_|NKor_Supply_|NKr_Command_"
    r"|(DE|FR|IN|IT|JP|LY|PK|SA|SE|SK|SY|TR|UA|UAE|UK|VN|ZA)_Flag_Hs)"
)
COUNTRY_FLAG_ANIM_RE = re.compile(
    r"(?i)(DE|FR|IN|IT|JP|LY|PK|SA|SE|SK|SY|TR|UA|UAE|UK|VN|ZA)_Flag_Hs"
)


def in_protected(path: str) -> bool:
    low = jf.norm(path).lower()
    return any(f"\\{p}\\" in low for p in PROTECTED_FOLDER)


def stem_of(path: str) -> str:
    return Path(jf.norm(path).replace("\\", "/")).stem


def is_banned_w3d(path: str) -> bool:
    if not path.lower().endswith(".w3d"):
        return False
    return bool(BANNED_W3D_STEM.match(stem_of(path)))


def main() -> int:
    if jf.sha256_file(SRC_DATA) != SRC_DATA_SHA:
        raise SystemExit("OBJECT_BOOT DATA SHA mismatch")
    if jf.sha256_file(SRC_ART) != SRC_ART_SHA:
        raise SystemExit("OBJECT_BOOT ART SHA mismatch")
    if jf.sha256_file(GOOD_ART) != GOOD_ART_SHA:
        raise SystemExit("camp-clone ART SHA mismatch")

    src_data = jf.read_big_list(SRC_DATA)
    src_art = jf.read_big_list(SRC_ART)
    good_art = jf.read_big_list(GOOD_ART)
    if len(src_data) != 2883:
        raise SystemExit(f"OBJECT_BOOT DATA count {len(src_data)}")
    if len(src_art) != 4509:
        raise SystemExit(f"OBJECT_BOOT ART count {len(src_art)}")
    if len(good_art) != 4432:
        raise SystemExit(f"camp-clone ART count {len(good_art)}")

    frozen = {p: jf.raw_of(src_data, p) for p in (P_PT, P_PT_PATCH, P_WEAPON, P_UPGRADE, P_CMDSET, P_CMDBTN)}
    protected = {jf.norm(n).lower(): bytes(b) for n, b in src_data if in_protected(n)}

    # PASS 1: DATA must not reference clone Model=/Animation=
    data_clone_hits = []
    extra_draws = []
    remaining_hs = []
    for n, b in src_data:
        if not str(n).lower().endswith(".ini"):
            continue
        t = b.decode("latin-1", errors="replace")
        if "ModuleTag_SpecterNatFlag" in t or "ModuleTag_SpecterCampFlag" in t:
            extra_draws.append(jf.norm(n))
        for mdl in re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", t):
            if CLONE_MODEL_RE.search(mdl):
                data_clone_hits.append(f"{n} Model={mdl}")
            if re.search(r"(?i)(Irq__IqFlag_Hs|NKr__NKFlag_Hs)$", mdl):
                remaining_hs.append(f"Model={mdl} {jf.norm(n)}")
        for anim in re.findall(r"(?im)^\s*Animation\s*=\s*(\S+)", t):
            if CLONE_MODEL_RE.search(anim) or COUNTRY_FLAG_ANIM_RE.search(anim):
                data_clone_hits.append(f"{n} Animation={anim}")
    if extra_draws:
        raise SystemExit("DATA still has extra flag Draws:\n  " + "\n  ".join(extra_draws[:20]))
    if data_clone_hits:
        raise SystemExit("DATA still references clone Model/Anim:\n  " + "\n  ".join(data_clone_hits[:20]))

    src_art_map = {jf.norm(n).lower(): (n, bytes(b)) for n, b in src_art}
    good_art_map = {jf.norm(n).lower(): (n, bytes(b)) for n, b in good_art}

    banned_in_src = sorted(
        jf.norm(n) for n, _ in src_art if is_banned_w3d(n)
    )
    banned_in_good = [jf.norm(n) for n, _ in good_art if is_banned_w3d(n)]
    if banned_in_good:
        raise SystemExit("camp-clone ART already has banned clones:\n  " + "\n  ".join(banned_in_good[:20]))

    # ART = camp-clone, then overlay required HUD TGAs from current ART
    new_art: list[tuple[str, bytes]] = [(n, bytes(b)) for n, b in good_art]
    new_map = {jf.norm(n).lower(): i for i, (n, _) in enumerate(new_art)}
    added_tex: list[str] = []
    replaced_tex: list[str] = []
    missing_keep_tex: list[str] = []

    for key, (name, blob) in src_art_map.items():
        if not key.startswith("art\\textures\\"):
            continue
        if stem_of(key).lower() not in KEEP_TEX_STEMS:
            continue
        if key in new_map:
            new_art[new_map[key]] = (new_art[new_map[key]][0], blob)
            replaced_tex.append(jf.norm(name))
        else:
            new_art.append((name, blob))
            new_map[key] = len(new_art) - 1
            added_tex.append(jf.norm(name))

    for stem in sorted(KEEP_TEX_STEMS):
        hits = [k for k in src_art_map if k.startswith("art\\textures\\") and stem_of(k).lower() == stem]
        if not hits:
            missing_keep_tex.append(stem)
    if missing_keep_tex:
        raise SystemExit("required HUD texture missing from current ART: " + ", ".join(missing_keep_tex))

    # never carry banned W3Ds
    leftover_ban = [jf.norm(n) for n, _ in new_art if is_banned_w3d(n)]
    if leftover_ban:
        raise SystemExit("banned W3D leaked into new ART:\n  " + "\n  ".join(leftover_ban[:20]))

    # keep original HS containers
    for keep in ("art\\w3d\\irq__iqflag_hs.w3d", "art\\w3d\\nkr__nkflag_hs.w3d"):
        if keep not in {jf.norm(n).lower() for n, _ in new_art}:
            raise SystemExit(f"original HS missing from new ART: {keep}")

    anames = [jf.norm(n).lower() for n, _ in new_art]
    if len(anames) != len(set(anames)):
        raise SystemExit("duplicate ART paths")

    art_tex_stems = {
        stem_of(n).lower()
        for n, _ in new_art
        if jf.norm(n).lower().startswith("art\\textures\\")
    }
    unresolved_mi = []
    for n, b in src_data:
        low = jf.norm(n).lower()
        if "mappedimage" not in low:
            continue
        t = b.decode("latin-1", errors="replace")
        if not re.search(r"(?i)(specter_remainingflags|specter_campflags|turkey_factionimages)", n):
            continue
        for tex in re.findall(r"(?im)^\s*Texture\s*=\s*(\S+)", t):
            stem = tex.split(".")[0].lower()
            if stem not in art_tex_stems:
                unresolved_mi.append(f"{n} Texture={tex}")
    if unresolved_mi:
        raise SystemExit("MappedImage texture missing in new ART:\n  " + "\n  ".join(unresolved_mi[:20]))

    WS_OUT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC_DATA, WS_OUT / "_SPEC_DATA_ONE.big")
    (WS_OUT / "_SPEC_ART_ONE.big").write_bytes(jf.build_big_ordered(new_art))

    new_data_sha = jf.sha256_file(WS_OUT / "_SPEC_DATA_ONE.big")
    new_art_sha = jf.sha256_file(WS_OUT / "_SPEC_ART_ONE.big")
    if new_data_sha != SRC_DATA_SHA:
        raise SystemExit("DATA is not byte-identical to OBJECT_BOOT")
    if new_art_sha == SRC_ART_SHA:
        raise SystemExit("ART SHA unchanged; clones were not stripped")
    if new_art_sha == GOOD_ART_SHA:
        raise SystemExit("ART SHA is camp-clone; HUD TGAs were not added")

    packed_d = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    packed_a = jf.read_big_list(WS_OUT / "_SPEC_ART_ONE.big")
    if packed_d[0][0] is None or packed_a[0][0] is None:
        raise SystemExit("re-read BIG failed")
    if len(packed_d) != 2883:
        raise SystemExit(f"DATA count changed {len(packed_d)}")
    if bytes((WS_OUT / "_SPEC_DATA_ONE.big").read_bytes()) != SRC_DATA.read_bytes():
        raise SystemExit("DATA bytes differ from OBJECT_BOOT")

    for p, raw in frozen.items():
        if jf.raw_of(packed_d, p) != raw:
            raise SystemExit(f"frozen INI changed: {p}")
    for n, b in packed_d:
        if in_protected(n) and bytes(b) != protected[jf.norm(n).lower()]:
            raise SystemExit(f"protected DATA changed: {n}")

    packed_ban = [jf.norm(n) for n, _ in packed_a if is_banned_w3d(n)]
    if packed_ban:
        raise SystemExit("packed ART still has banned W3D:\n  " + "\n  ".join(packed_ban[:20]))
    packed_anames = [jf.norm(n).lower() for n, _ in packed_a]
    if len(packed_anames) != len(set(packed_anames)):
        raise SystemExit("packed ART duplicate paths")

    # remaining active flag refs (DATA unchanged, so same as OBJECT_BOOT)
    remaining_btn = []
    btn = jf.text_of(packed_d, P_CMDBTN)
    for m in re.finditer(r"(?im)^CommandButton\s+(\S+)\s*$", btn):
        rest = btn[m.end():]
        m2 = re.search(r"(?im)^CommandButton\s+\S+", rest)
        blk = rest[:m2.start()] if m2 else rest
        if re.search(r"(?i)CampFlag", blk):
            remaining_btn.append(m.group(1))
    remaining_mi = [
        jf.norm(n) for n, _ in packed_d
        if re.search(r"(?i)(specter_remainingflags|specter_campflags|turkey_factionimages)", n)
    ]

    boot_safe = (
        new_data_sha == SRC_DATA_SHA
        and not data_clone_hits
        and not extra_draws
        and not packed_ban
        and not unresolved_mi
        and not leftover_ban
        and len(packed_anames) == len(set(packed_anames))
        and added_tex
    )

    audit = "\n".join([
        "SPECTER1 FLAG ART CLONE STRIP 02",
        "BASELINE_DATA = SPECTER1_FLAG_OBJECT_BOOT_01 (frozen)",
        f"BASELINE_DATA_SHA256 = {SRC_DATA_SHA}",
        f"BASELINE_ART_SHA256 = {SRC_ART_SHA}",
        f"CAMP_CLONE_ART_SHA256 = {GOOD_ART_SHA}",
        f"NEW_DATA_SHA256 = {new_data_sha}",
        f"NEW_ART_SHA256 = {new_art_sha}",
        f"PACKED_DATA_FILES = {len(packed_d)}",
        f"PACKED_ART_FILES = {len(packed_a)} (camp-clone 4432 + {len(added_tex)} new TGA)",
        "DUPLICATE_DATA_PATHS = 0",
        "DUPLICATE_ART_PATHS = 0",
        "BIG_INTEGRITY = YES",
        f"BOOT_SAFE = {'YES' if boot_safe else 'NO'}",
        "FIX_APPLIED = YES (ART only)",
        "INGAME_TESTED = NO",
        "DATA_BYTE_IDENTICAL_TO_OBJECT_BOOT = YES",
        "",
        "===== REMOVED W3D CLONES =====",
        f"REMOVED_W3D_COUNT = {len(banned_in_src)}",
        *[f"  - {n}" for n in banned_in_src],
        "",
        "===== HUD TEXTURES KEPT/ADDED =====",
        f"ADDED_TGA_FROM_OBJECT_BOOT = {len(added_tex)}",
        *[f"  + {n}" for n in added_tex],
        f"REPLACED_TGA_OVER_CAMP_CLONE = {len(replaced_tex)}",
        *[f"  ~ {n}" for n in replaced_tex],
        "",
        "===== PASS SCANS =====",
        "PASS1_DATA_NO_CLONE_MODEL_ANIM = YES",
        "PASS1_DATA_NO_EXTRA_DRAWS = YES",
        "PASS2_ART_NO_BANNED_W3D = YES",
        "PASS3_DATA_FROZEN = YES",
        "PASS4_NO_DUPLICATE_ART = YES",
        "PASS5_MAPPEDIMAGE_TEXTURES_RESOLVE = YES",
        "",
        "===== REMAINING ACTIVE FLAG REFERENCES =====",
        "PlayerTemplate HUD remaps = KEPT (DATA frozen)",
        f"COMMANDBUTTON_CAMPFLAG = {len(remaining_btn)} (DATA frozen)",
        *[f"  {x}" for x in remaining_btn],
        f"MAPPEDIMAGE_FILES = {len(remaining_mi)}",
        *[f"  {x}" for x in remaining_mi],
        "Original Abbas/NuclearCenter Flag_Hs = KEPT",
        *[f"  {x}" for x in remaining_hs],
        "Irq__IqFlag_Hs / NKr__NKFlag_Hs W3D = KEPT",
        "Building cloth / extra Draws / Model retargets = NOT RESTORED",
        "",
        "===== REMAINING MODIFIED OBJECTS vs OBJECT_BOOT DATA =====",
        "NONE (DATA byte-identical)",
        "",
        "WEAPON_INI_CHANGED = NO",
        "UPGRADE_INI_CHANGED = NO",
        "COMMANDSET_CHANGED = NO",
        "COMMANDBUTTON_CHANGED = NO",
        "PLAYERTEMPLATE_CHANGED = NO",
        "PROTECTED_FACTIONS_UNCHANGED = YES",
        "GAMEPLAY_CHANGED = NO",
        "ART_CHANGED = YES (unused flag W3D clones removed; HUD TGA kept)",
        "DATA_CHANGED = NO",
        "REENGAGE_FLAGS = NO",
    ]) + "\n"

    changelog = """SPECTER1 flag ART clone strip 02

DATA is the frozen OBJECT_BOOT pair. No Object, Draw, Model, or
Animation was edited.

ART is rebuilt from SPECTER1_CAMP_CLONE_IRAQ_VIETNAM plus the HUD
TGA files required by the frozen MappedImages. All unused #516/#517/#518
flag W3D clones are gone (IqPwr_/NkPwr_/IqWF_/NkWF_/irq_camp_*/
country *_Flag_Hs / Iraq_Supply_* / NKor_Supply_* / NKr_Command_*).

Original Irq__IqFlag_Hs and NKr__NKFlag_Hs stay. Extra Draws and
building-cloth retargets are not restored.

INGAME_TESTED = NO
"""

    install = f"""SPECTER1_FLAG_ART_CLONE_STRIP_02
================================

ART-only strip of unused flag W3D clones. DATA is unchanged from
SPECTER1_FLAG_OBJECT_BOOT_01.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
4. Launch Specter.

Checksums:
  DATA SHA256 {new_data_sha}
  ART  SHA256 {new_art_sha}

BOOT_SAFE = {'YES' if boot_safe else 'NO'}
FIX_APPLIED = YES (ART only)
INGAME_TESTED = NO
"""

    for dest in (WS_OUT,):
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "audit.txt").write_text(audit, encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "INSTALL.txt").write_text(install, encoding="utf-8")
        (dest / "SHA256.txt").write_text(
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
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {new_data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {new_art_sha}\n"
        f"{RELEASE_NAME}.zip  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n"
    )
    (WS_OUT / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", new_data_sha)
    print("ART", new_art_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    print("REMOVED_W3D", len(banned_in_src))
    print("BOOT_SAFE", "YES" if boot_safe else "NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
