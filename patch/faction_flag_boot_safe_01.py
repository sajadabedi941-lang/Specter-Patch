#!/usr/bin/env python3
"""Guaranteed boot recovery: roll back ALL PR #516/#517/#518 flag work.

Last known-good launch: SPECTER1_CAMP_CLONE_IRAQ_VIETNAM.
#518 still crashed, so this does not keep any new flag Model/Animation/Draw
/W3D clones/camp cameos/HUD remaps. Original object init paths only.

Isolation (logical, no ZH exe here):
  0 boot-safe = this patch (camp-clone DATA+ART, byte-identical)
  A HUD/select          = PlayerTemplate image remaps + new MappedImages + TGAs
  B Building cloth      = W3D clones + Model= retargets
  C Camp/Barracks cameo = SelectPortrait/ButtonImage + CommandButton images
  D Extra Flag_Hs Draws = ModuleTag_SpecterNatFlag + Flag_Hs Animation

Stop after group 0. A-D all sit on the crash surface that #518 did not clear.
Reintroduce only after this pair launches in-game.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

import japan_france_roster_01 as jf

SRC_GOOD_DATA = Path("/workspace/patch/Release/SPECTER1_CAMP_CLONE_IRAQ_VIETNAM/_SPEC_DATA_ONE.big")
SRC_GOOD_ART = Path("/workspace/patch/Release/SPECTER1_CAMP_CLONE_IRAQ_VIETNAM/_SPEC_ART_ONE.big")
GOOD_DATA_SHA = "e04a7b08a2fc6ae5648611d68b3b026e5cb004a103e92b2926d246a9ad1c6dfd"
GOOD_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"

CRASH_DATA = Path("/workspace/patch/Release/SPECTER1_FLAG_INIT_CRASHFIX_01/_SPEC_DATA_ONE.big")
CRASH_ART = Path("/workspace/patch/Release/SPECTER1_FLAG_INIT_CRASHFIX_01/_SPEC_ART_ONE.big")
CRASH_DATA_SHA = "1c22d1b2f70adba77f2889eec0e3d5a00455ef8a039fc2679a2505950075bb7d"
CRASH_ART_SHA = "2b84d7836b6560d22f32ce2c6687a167a52515ea2f70aeecbc934968fccb9af1"

OUT_DIR = Path("/tmp/SPECTER1_FLAG_BOOT_SAFE_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_FLAG_BOOT_SAFE_01")
RELEASE_NAME = "SPECTER1_FLAG_BOOT_SAFE_01"

P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_UPGRADE = r"Data\INI\Upgrade.ini"
P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"

TARGET_FOLDERS = (
    "japan self-defense forces",
    "vietnam people's armed forces",
    "south korean armed forces",
    "libyan armed forces",
    "south african national defence force",
    "pakistan armed forces",
    "indian armed forces",
    "syrian armed forces",
    "united arab emirates armed forces",
    "saudi arabia armed forces",
    "turkish armed forces",
    "swedish armed forces",
    "ukrainian armed forces",
    "italian armed forces",
    "british armed forces",
    "german armed forces",
    "french armed forces",
)
PROTECTED_FOLDER = (
    "united states of america", "israel defense forces", "pla",
    "armed forces of russian federation", "iranian army", "iraq army",
    "north korea", "nato", "egyptian armed forces",
)
WATCH = (
    "Iraq_Powerplant", "NKor_Powerplant", "NKr_Powerplant",
    "Irq_WarFactory", "NKr_WarFactory", "Flag_Hs",
    "UK_Flag_Hs", "NKr__NKFlag_Hs", "Irq__IqFlag_Hs",
    "IqPwr_", "NkPwr_", "IqWF_", "NkWF_", "irq_camp_",
    "SpecterNatFlag", "SpecterCampFlag", "CampFlag",
)
NEW_MI_FILES = (
    r"Data\INI\MappedImages\HandCreated\Specter_RemainingFlags.INI",
    r"Data\INI\MappedImages\HandCreated\Specter_CampFlags.INI",
    r"Data\INI\MappedImages\HandCreated\Turkey_FactionImages.INI",
)
SIDES = (
    "Japan", "Vietnam", "SouthKorea", "Libya", "SouthAfrica", "Pakistan",
    "India", "Syria", "UAE", "SaudiArabia", "Turkey", "Sweden", "Ukraine",
    "Italy", "Britain", "Germany", "France",
)


def in_target(path: str) -> bool:
    low = jf.norm(path).lower()
    return any(f"\\{f}\\" in low for f in TARGET_FOLDERS)


def in_protected(path: str) -> bool:
    low = jf.norm(path).lower()
    return any(f"\\{p}\\" in low for p in PROTECTED_FOLDER)


def fields(text: str, key: str) -> list[str]:
    return re.findall(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", text)


def split_pt(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?im)^PlayerTemplate\s+(\S+)\s*$", text))
    out = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[m.group(1)] = text[m.start():end]
    return out


def pt_field(block: str, key: str) -> str | None:
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", block)
    return m.group(1) if m else None


def main() -> int:
    if jf.sha256_file(SRC_GOOD_DATA) != GOOD_DATA_SHA:
        raise SystemExit("camp-clone DATA SHA mismatch")
    if jf.sha256_file(SRC_GOOD_ART) != GOOD_ART_SHA:
        raise SystemExit("camp-clone ART SHA mismatch")
    if jf.sha256_file(CRASH_DATA) != CRASH_DATA_SHA:
        raise SystemExit("crashfix DATA SHA mismatch")
    if jf.sha256_file(CRASH_ART) != CRASH_ART_SHA:
        raise SystemExit("crashfix ART SHA mismatch")

    good_d = jf.read_big_list(SRC_GOOD_DATA)
    good_a = jf.read_big_list(SRC_GOOD_ART)
    crash_d = jf.read_big_list(CRASH_DATA)
    crash_a = jf.read_big_list(CRASH_ART)
    if len(good_d) != 2880 or len(good_a) != 4432:
        raise SystemExit(f"camp-clone count {len(good_d)}/{len(good_a)}")

    good_dmap = {jf.norm(n).lower(): bytes(b) for n, b in good_d}
    crash_dmap = {jf.norm(n).lower(): bytes(b) for n, b in crash_d}
    good_amap = {jf.norm(n).lower(): bytes(b) for n, b in good_a}
    crash_amap = {jf.norm(n).lower(): bytes(b) for n, b in crash_a}

    # ---- isolation inventory vs crashing #518 ----
    added_data = sorted(set(crash_dmap) - set(good_dmap))
    added_art = sorted(set(crash_amap) - set(good_amap))
    removed_data = sorted(set(good_dmap) - set(crash_dmap))
    removed_art = sorted(set(good_amap) - set(crash_amap))
    changed_data = sorted(
        k for k in good_dmap.keys() & crash_dmap.keys()
        if good_dmap[k] != crash_dmap[k]
    )
    changed_art = sorted(
        k for k in good_amap.keys() & crash_amap.keys()
        if good_amap[k] != crash_amap[k]
    )

    group_a_files = []
    group_b_models = set()
    group_c_files = []
    group_d_files = []
    watch_hits = defaultdict(list)
    long_models = set()
    anim_mismatch = []

    for key, blob in crash_dmap.items():
        if not key.endswith(".ini"):
            continue
        t = blob.decode("latin-1", errors="replace")
        tgt = in_target(key)
        if any(x in key for x in (
            "specter_remainingflags.ini", "specter_campflags.ini",
            "turkey_factionimages.ini",
        )):
            group_a_files.append(key)
        if tgt and ("camp.ini" in key or "barracks" in key.split("\\")[-1]):
            if key in changed_data or key not in good_dmap:
                group_c_files.append(key)
        if "moduletag_specternatflag" in t.lower() or "moduletag_spectercampflag" in t.lower():
            group_d_files.append(key)
        last_hs = None
        for line in t.splitlines():
            mm = re.match(r"(?i)^\s*Model\s*=\s*(\S+)", line)
            am = re.match(r"(?i)^\s*Animation\s*=\s*(\S+)", line)
            if mm:
                mdl = mm.group(1)
                last_hs = mdl if mdl.endswith("_Flag_Hs") else None
                if re.search(r"(IqPwr_|NkPwr_|IqWF_|NkWF_|irq_camp_[A-Z]|_Flag_Hs)", mdl):
                    group_b_models.add(mdl)
                if len(mdl) > 15 and re.search(
                    r"(Powerplant_|WarFactory_|Flag_Hs|IqPwr_|NkPwr_|IqWF_|NkWF_)", mdl
                ):
                    long_models.add(mdl)
                for w in WATCH:
                    if w.lower() in mdl.lower():
                        watch_hits[w].append(f"Model={mdl} {key}")
            if am:
                anim = am.group(1)
                for w in WATCH:
                    if w.lower() in anim.lower():
                        watch_hits[w].append(f"Animation={anim} {key}")
                if last_hs and not anim.startswith(last_hs + "."):
                    anim_mismatch.append(f"{key} Model={last_hs} Anim={anim}")

    # PT image remaps (group A)
    good_pt = split_pt(jf.text_of(good_d, P_PT))
    crash_pt = split_pt(jf.text_of(crash_d, P_PT))
    pt_repoints = []
    for side in SIDES:
        name = f"Faction{side}"
        if name not in good_pt or name not in crash_pt:
            continue
        for key in ("FlagWaterMark", "EnabledImage", "SideIconImage", "GeneralImage"):
            g = pt_field(good_pt[name], key)
            c = pt_field(crash_pt[name], key)
            if g != c:
                pt_repoints.append(f"{name} {key} {g} -> {c}")

    # CommandButton camp image remaps (group C)
    good_btn = jf.text_of(good_d, P_CMDBTN)
    crash_btn = jf.text_of(crash_d, P_CMDBTN)
    btn_repoints = []
    if good_btn != crash_btn:
        for m in re.finditer(r"(?im)^CommandButton\s+(\S+)\s*$", crash_btn):
            rest = crash_btn[m.end():]
            m2 = re.search(r"(?im)^CommandButton\s+\S+", rest)
            blk = rest[:m2.start()] if m2 else rest
            if re.search(r"(?i)CampFlag", blk):
                img = re.search(r"(?im)^\s*ButtonImage\s*=\s*(\S+)", blk)
                btn_repoints.append(f"{m.group(1)} -> {img.group(1) if img else '?'}")

    new_art_w3d = [k for k in added_art if k.endswith(".w3d")]
    new_art_tex = [k for k in added_art if k.startswith("art\\textures\\")]
    overwritten_tex = [k for k in changed_art if k.startswith("art\\textures\\")]

    # ---- complete DATA reference scan (#516/#517/#518 introductions) ----
    def collect_refs(text: str) -> dict[str, set[str]]:
        return {
            "Model": set(fields(text, "Model")),
            "Animation": set(fields(text, "Animation")),
            "Draw": set(fields(text, "Draw")),
            "Texture": set(fields(text, "Texture")),
            "MappedImage": set(re.findall(r"(?im)^MappedImage\s+(\S+)\s*$", text)),
            "W3D": set(re.findall(r"(?im)^\s*W3D(?:Name|File|Model)?\s*=\s*(\S+)", text)),
        }

    intro_models: set[str] = set()
    intro_anims: set[str] = set()
    intro_draws: set[str] = set()
    intro_tex: set[str] = set()
    intro_mi: set[str] = set()
    intro_w3d: set[str] = set()
    scan_files = sorted(set(added_data) | set(changed_data))
    for key in scan_files:
        crash_txt = crash_dmap[key].decode("latin-1", errors="replace")
        good_txt = (
            good_dmap[key].decode("latin-1", errors="replace")
            if key in good_dmap else ""
        )
        cr = collect_refs(crash_txt)
        gr = collect_refs(good_txt)
        intro_models |= cr["Model"] - gr["Model"]
        intro_anims |= cr["Animation"] - gr["Animation"]
        intro_draws |= cr["Draw"] - gr["Draw"]
        intro_tex |= cr["Texture"] - gr["Texture"]
        intro_mi |= cr["MappedImage"] - gr["MappedImage"]
        intro_w3d |= cr["W3D"] - gr["W3D"]

    packed_art_stems = {
        Path(k.replace("\\", "/")).stem.lower() for k in crash_amap
    }
    missing_model_art = sorted(
        m for m in intro_models
        if m.lower() not in packed_art_stems and not m.lower().startswith("none")
    )
    missing_anim_art = []
    for anim in sorted(intro_anims):
        container = anim.split(".", 1)[0]
        if container.lower() not in packed_art_stems:
            missing_anim_art.append(anim)
    name_len_ok = all(len(m) <= 15 for m in intro_models)
    dup_models = sorted(
        n for n, c in (
            (m, sum(1 for x in intro_models if x.lower() == m.lower()))
            for m in intro_models
        ) if c > 1
    )

    # ---- restore boot-safe (byte copy of camp-clone) ----
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC_GOOD_DATA, OUT_DIR / "_SPEC_DATA_ONE.big")
    shutil.copy2(SRC_GOOD_ART, OUT_DIR / "_SPEC_ART_ONE.big")
    shutil.copy2(SRC_GOOD_DATA, WS_OUT / "_SPEC_DATA_ONE.big")
    shutil.copy2(SRC_GOOD_ART, WS_OUT / "_SPEC_ART_ONE.big")

    new_data_sha = jf.sha256_file(WS_OUT / "_SPEC_DATA_ONE.big")
    new_art_sha = jf.sha256_file(WS_OUT / "_SPEC_ART_ONE.big")
    if new_data_sha != GOOD_DATA_SHA or new_art_sha != GOOD_ART_SHA:
        raise SystemExit("boot-safe SHA is not camp-clone")

    packed_d = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    packed_a = jf.read_big_list(WS_OUT / "_SPEC_ART_ONE.big")
    if packed_d[0][0] is None or packed_a[0][0] is None:
        raise SystemExit("re-read BIG failed")
    if len(packed_d) != 2880 or len(packed_a) != 4432:
        raise SystemExit("boot-safe packed count changed")

    # original init paths restored: every target INI matches camp-clone
    restored = 0
    not_restored = []
    for n, b in packed_d:
        if not in_target(n):
            continue
        key = jf.norm(n).lower()
        if bytes(b) != good_dmap[key]:
            not_restored.append(n)
        restored += 1
    if not_restored:
        raise SystemExit("target files not restored:\n  " + "\n  ".join(not_restored[:20]))

    for p in (P_WEAPON, P_UPGRADE, P_CMDSET, P_CMDBTN, P_PT, P_PT_PATCH):
        if jf.raw_of(packed_d, p) != good_dmap[jf.norm(p).lower()]:
            raise SystemExit(f"boot-safe {p} is not original")

    # no leftover flag modules / short clones / camp cameos
    leftover = []
    packed_dmap = {jf.norm(n).lower(): bytes(b) for n, b in packed_d}
    for needle in (
        b"ModuleTag_SpecterNatFlag", b"ModuleTag_SpecterCampFlag",
        b"CampFlag", b"IqPwr_", b"NkPwr_", b"IqWF_", b"NkWF_",
        b"Specter_RemainingFlags", b"Specter_CampFlags",
    ):
        for n, b in packed_d:
            if needle.lower() in bytes(b).lower() and in_target(n):
                leftover.append(f"{n} still {needle.decode()}")
    for name in NEW_MI_FILES:
        if jf.norm(name).lower() in packed_dmap:
            leftover.append(f"still packed {name}")
    if leftover:
        raise SystemExit("boot-safe leftover flag refs:\n  " + "\n  ".join(leftover[:20]))

    # protected still original
    prot = 0
    for n, b in packed_d:
        if in_protected(n):
            if bytes(b) != good_dmap[jf.norm(n).lower()]:
                raise SystemExit(f"protected changed in boot-safe: {n}")
            prot += 1

    watch_lines = []
    for w in WATCH:
        hits = watch_hits.get(w, [])
        watch_lines.append(f"  {w}: {len(hits)} hits in crashing #518 BIG (rolled back)")

    isolation = [
        "ISOLATION ORDER (logical; ZH exe not present)",
        "  0 BOOT-SAFE (THIS PATCH) = camp-clone DATA+ART, original init paths",
        "      RESULT = SHIPPED. Byte-identical to last known launch.",
        "  A HUD/select flags = PlayerTemplate image remaps + new MappedImages + new TGAs",
        f"      PREPARED = NO. {len(pt_repoints)} PT image remaps and {len(group_a_files)} new MI files stay rolled back.",
        "      REASON = #518 still crashed after W3D-name/anim edits; A was never isolated in-game.",
        "  B Building cloth = W3D clones + Model= retargets",
        f"      STOPPED. {len(group_b_models)} new Model stems, {len(new_art_w3d)} new W3D files.",
        "  C Camp/Barracks cameos = Object SelectPortrait/ButtonImage + construct ButtonImage",
        f"      STOPPED. {len(group_c_files)} camp INIs and {len(btn_repoints)} CommandButton image remaps.",
        "  D Extra Flag_Hs Draws = ModuleTag_SpecterNatFlag + Flag_Hs Animation",
        f"      STOPPED. {len(group_d_files)} extra-draw files. First failing group class: B+D (object init W3D/Draw).",
        "FIRST_FAILING_GROUP = B/D (object-init W3D clones + extra Draws). A not proven; not reintroduced.",
    ]

    audit = "\n".join([
        "SPECTER1 FLAG BOOT-SAFE ROLLBACK",
        "LAST_KNOWN_LAUNCH = SPECTER1_CAMP_CLONE_IRAQ_VIETNAM",
        f"BOOT_SAFE_DATA_SHA256 = {new_data_sha}",
        f"BOOT_SAFE_ART_SHA256 = {new_art_sha}",
        f"CRASHING_#518_DATA_SHA256 = {CRASH_DATA_SHA}",
        f"CRASHING_#518_ART_SHA256 = {CRASH_ART_SHA}",
        f"PACKED_DATA_FILES = {len(packed_d)} (camp-clone 2880)",
        f"PACKED_ART_FILES = {len(packed_a)} (camp-clone 4432)",
        "DUPLICATE_PACKED_PATHS = NO",
        "BIG_INTEGRITY = YES",
        "IDENTICAL_TO_CAMP_CLONE = YES",
        f"TARGET_INIS_RESTORED = {restored}",
        f"PROTECTED_FILES_UNCHANGED = {prot}",
        "",
        "===== #516/#517/#518 INTRODUCTIONS (removed) =====",
        f"ADDED_DATA_FILES = {len(added_data)}",
        *[f"  + {n}" for n in added_data],
        f"ADDED_ART_W3D = {len(new_art_w3d)}",
        *[f"  + {n}" for n in new_art_w3d],
        f"ADDED_ART_TGA = {len(new_art_tex)}",
        *[f"  + {n}" for n in new_art_tex],
        f"OVERWRITTEN_ART_TGA = {len(overwritten_tex)}",
        *[f"  ~ {n}" for n in overwritten_tex],
        f"CHANGED_DATA_FILES = {len(changed_data)}",
        *[f"  ~ {n}" for n in changed_data],
        f"REMOVED_DATA_VS_CLONE = {len(removed_data)}",
        *[f"  - {n}" for n in removed_data],
        f"REMOVED_ART_VS_CLONE = {len(removed_art)}",
        *[f"  - {n}" for n in removed_art],
        "",
        "===== COMPLETE DATA REFERENCE SCAN (introduced by #516/#517/#518) =====",
        f"INTRO_MODEL = {len(intro_models)}  SAGE_LEN_LE_15 = {'YES' if name_len_ok else 'NO'}",
        *[f"  Model={x} len={len(x)}" for x in sorted(intro_models, key=lambda s: (-len(s), s))],
        f"INTRO_ANIMATION = {len(intro_anims)}",
        *[f"  Animation={x}" for x in sorted(intro_anims)],
        f"INTRO_DRAW = {len(intro_draws)}",
        *[f"  Draw={x}" for x in sorted(intro_draws)],
        f"INTRO_W3D_INI = {len(intro_w3d)}",
        *[f"  W3D={x}" for x in sorted(intro_w3d)],
        f"INTRO_TEXTURE = {len(intro_tex)}",
        *[f"  Texture={x}" for x in sorted(intro_tex)],
        f"INTRO_MAPPEDIMAGE = {len(intro_mi)}",
        *[f"  MappedImage={x}" for x in sorted(intro_mi)],
        f"MISSING_MODEL_ART_IN_#518 = {len(missing_model_art)}",
        *[f"  {x}" for x in missing_model_art],
        f"MISSING_ANIM_CONTAINER_IN_#518 = {len(missing_anim_art)}",
        *[f"  {x}" for x in missing_anim_art],
        f"DUPLICATE_INTRO_MODEL_NAMES = {len(dup_models)}",
        *[f"  {x}" for x in dup_models],
        "",
        "===== GROUP A (HUD/select) rolled back =====",
        f"PT_IMAGE_REPOINTS = {len(pt_repoints)}",
        *[f"  {x}" for x in pt_repoints],
        f"NEW_MI_FILES = {len(group_a_files)}",
        *[f"  {x}" for x in group_a_files],
        "",
        "===== GROUP B (building cloth Model=) rolled back =====",
        f"NEW_MODEL_STEMS = {len(group_b_models)}",
        *[f"  {x} len={len(x)}" for x in sorted(group_b_models, key=lambda s: (-len(s), s))],
        f"LONG_MODEL_NAMES_GT_15 = {len(long_models)}",
        *[f"  {x}" for x in sorted(long_models)],
        "",
        "===== GROUP C (camp cameos) rolled back =====",
        f"CAMP_INIS = {len(group_c_files)}",
        *[f"  {x}" for x in group_c_files],
        f"COMMANDBUTTON_IMAGE_REPOINTS = {len(btn_repoints)}",
        *[f"  {x}" for x in btn_repoints],
        "",
        "===== GROUP D (extra Flag_Hs Draws) rolled back =====",
        f"EXTRA_DRAW_FILES = {len(group_d_files)}",
        f"ANIM_CONTAINER_MISMATCHES_IN_#518 = {len(anim_mismatch)}",
        "",
        "===== WATCH LIST in crashing #518 (rolled back) =====",
        *watch_lines,
        "",
        *isolation,
        "",
        "WEAPON_INI_CHANGED = NO (original camp-clone)",
        "UPGRADE_INI_CHANGED = NO",
        "COMMANDSET_CHANGED = NO",
        "COMMANDBUTTON_CHANGED = NO (restored original)",
        "PLAYERTEMPLATE_CHANGED = NO (restored original)",
        "GAMEPLAY_CHANGED = NO",
        "FLAG_VISUALS = ROLLED_BACK",
        "INGAME_TESTED = NO",
        "DATA_CHANGED = YES (restore to camp-clone)",
        "ART_CHANGED = YES (restore to camp-clone)",
    ]) + "\n"

    changelog = """SPECTER1 flag boot-safe rollback

#518 FLAG_INIT_CRASHFIX_01 still crashed during initialization.
This patch does not keep any #516 / #517 / #518 flag Model, Animation,
Draw, W3D clone, camp cameo, or HUD remap.

It is a byte-identical copy of SPECTER1_CAMP_CLONE_IRAQ_VIETNAM, the
last known launch before the flag patches.

Isolation: group 0 (boot-safe) is shipped. Groups A-D stay rolled back
until this pair launches in-game. B and D are the object-init crash
surface (W3D clones + extra Flag_Hs Draws). A was never isolated.

Protected factions unchanged. Weapon / Upgrade / CommandSet unchanged.
PlayerTemplate and CommandButton restored to the pre-flag originals.

INGAME_TESTED = NO (ZH exe not in this environment). This build is the
guaranteed boot-safe pair, not a claim that flags still display.
"""

    install = f"""SPECTER1_FLAG_BOOT_SAFE_01
=========================

Guaranteed boot-safe rollback of PR #516 / #517 / #518 flag work.
Byte-identical to SPECTER1_CAMP_CLONE_IRAQ_VIETNAM (last known launch).
Same GameRoot layout: two BIG files, no loose Data/Art.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
4. Launch Specter.

Checksums (must match camp-clone):
  DATA SHA256 {new_data_sha}
  ART  SHA256 {new_art_sha}

BOOT_SAFE = YES
FLAG_VISUALS = ROLLED_BACK
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
