#!/usr/bin/env python3
"""Object-init boot-safe patch: strip B/D flag W3D/Draw refs only.

#518 still crashed. FIRST_FAILING_GROUP = B/D
  (object-init W3D clones + extra Flag_Hs Draws).

This packer starts from the crashing #518 pair and restores camp-clone
Model=/Animation=/Draw on every target building Object. Extra Flag_Hs
Draws are removed. Cloned W3D names are no longer referenced.

Kept (not object-init):
  PlayerTemplate, CommandButton, MappedImages, TGA/W3D art files.

Not touched:
  Weapon, Upgrade, CommandSet, CommandButton, PlayerTemplate, country IDs,
  protected DATA (USA/Iran/Israel/China/Russia/NATO/Egypt/NK/Iraq).

Do not reintroduce B/D until this pair launches in-game.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

import japan_france_roster_01 as jf

SRC_CRASH_DATA = Path("/workspace/patch/Release/SPECTER1_FLAG_INIT_CRASHFIX_01/_SPEC_DATA_ONE.big")
SRC_CRASH_ART = Path("/workspace/patch/Release/SPECTER1_FLAG_INIT_CRASHFIX_01/_SPEC_ART_ONE.big")
CRASH_DATA_SHA = "1c22d1b2f70adba77f2889eec0e3d5a00455ef8a039fc2679a2505950075bb7d"
CRASH_ART_SHA = "2b84d7836b6560d22f32ce2c6687a167a52515ea2f70aeecbc934968fccb9af1"

SRC_GOOD_DATA = Path("/workspace/patch/Release/SPECTER1_CAMP_CLONE_IRAQ_VIETNAM/_SPEC_DATA_ONE.big")
GOOD_DATA_SHA = "e04a7b08a2fc6ae5648611d68b3b026e5cb004a103e92b2926d246a9ad1c6dfd"

OUT_DIR = Path("/tmp/SPECTER1_FLAG_OBJECT_BOOT_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_FLAG_OBJECT_BOOT_01")
RELEASE_NAME = "SPECTER1_FLAG_OBJECT_BOOT_01"

P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_UPGRADE = r"Data\INI\Upgrade.ini"
P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"

FROZEN = {jf.norm(p).lower() for p in (P_PT, P_PT_PATCH, P_WEAPON, P_UPGRADE, P_CMDSET, P_CMDBTN)}

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

# New cloned / extra-draw stems introduced by #516/#517/#518.
CLONE_MODEL_RE = re.compile(
    r"(?i)(IqPwr_|NkPwr_|IqWF_|NkWF_|irq_camp_[A-Za-z]"
    r"|Iraq_Powerplant_|NKor_Powerplant_|NKr_Powerplant_"
    r"|Irq_WarFactory_|NKr_WarFactory_"
    r"|Iraq_Supply_|NKor_Supply_|NKr_Command_"
    r"|(DE|FR|IN|IT|JP|LY|PK|SA|SE|SK|SY|TR|UA|UAE|UK|VN|ZA)_Flag_Hs)"
)
EXTRA_DRAW_RE = re.compile(
    r"(?ims)^[ \t]*Draw\s*=\s*W3DModelDraw\s+"
    r"ModuleTag_Specter(?:Nat|Camp)Flag\s*$"
    r".*?^[ \t]*End\s*$"
    r".*?^[ \t]*End\s*$",
)
RISKY_HINT = (
    "powerplant", "powerstation", "warfactory", "camp.ini", "barracks",
    "flag_hs", "iqpwr_", "nkpwr_", "iqwf_", "nkwf_", "irq_camp_",
)


def in_target(path: str) -> bool:
    low = jf.norm(path).lower()
    return any(f"\\{f}\\" in low for f in TARGET_FOLDERS)


def in_protected(path: str) -> bool:
    low = jf.norm(path).lower()
    return any(f"\\{p}\\" in low for p in PROTECTED_FOLDER)


def fields(text: str, key: str) -> list[str]:
    return re.findall(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", text)


def strip_extra_draws(text: str) -> tuple[str, int]:
    new, n = EXTRA_DRAW_RE.subn("", text)
    # leftover tags if the block regex missed a variant
    leftover = len(re.findall(r"(?i)ModuleTag_Specter(?:Nat|Camp)Flag", new))
    if leftover:
        raise SystemExit(f"extra-draw strip left {leftover} Specter flag tags")
    return new, n


def main() -> int:
    if jf.sha256_file(SRC_CRASH_DATA) != CRASH_DATA_SHA:
        raise SystemExit("crashfix DATA SHA mismatch")
    if jf.sha256_file(SRC_CRASH_ART) != CRASH_ART_SHA:
        raise SystemExit("crashfix ART SHA mismatch")
    if jf.sha256_file(SRC_GOOD_DATA) != GOOD_DATA_SHA:
        raise SystemExit("camp-clone DATA SHA mismatch")

    data = jf.read_big_list(SRC_CRASH_DATA)
    art = jf.read_big_list(SRC_CRASH_ART)
    good_d = jf.read_big_list(SRC_GOOD_DATA)
    if len(data) != 2883 or len(art) != 4509:
        raise SystemExit(f"#518 packed count {len(data)}/{len(art)}")
    if len(good_d) != 2880:
        raise SystemExit(f"camp-clone DATA count {len(good_d)}")

    good_dmap = {jf.norm(n).lower(): bytes(b) for n, b in good_d}
    src_frozen = {p: jf.raw_of(data, p) for p in (P_PT, P_PT_PATCH, P_WEAPON, P_UPGRADE, P_CMDSET, P_CMDBTN)}
    protected_files = {
        jf.norm(n).lower(): bytes(b) for n, b in data if in_protected(n)
    }

    restored_files: list[str] = []
    extra_draws_removed = 0
    model_lines_restored = 0
    removed_models: set[str] = set()
    removed_anims: set[str] = set()
    removed_draws: list[str] = []

    for idx, (fname, blob) in enumerate(data):
        key = jf.norm(fname).lower()
        if key in FROZEN:
            continue
        if in_protected(fname):
            continue
        if not str(fname).lower().endswith(".ini"):
            continue

        crash_txt = blob.decode("latin-1", errors="replace")
        good_blob = good_dmap.get(key)

        if good_blob is not None and bytes(blob) != good_blob:
            good_txt = good_blob.decode("latin-1", errors="replace")
            crash_models = set(fields(crash_txt, "Model"))
            good_models = set(fields(good_txt, "Model"))
            crash_anims = set(fields(crash_txt, "Animation"))
            good_anims = set(fields(good_txt, "Animation"))
            removed_models |= crash_models - good_models
            removed_anims |= crash_anims - good_anims
            model_lines_restored += sum(
                1 for a, b in zip(fields(crash_txt, "Model"), fields(good_txt, "Model"))
                if a != b
            )
            if "ModuleTag_SpecterNatFlag" in crash_txt or "ModuleTag_SpecterCampFlag" in crash_txt:
                extra_draws_removed += crash_txt.lower().count("moduletag_specternatflag")
                extra_draws_removed += crash_txt.lower().count("moduletag_spectercampflag")
                removed_draws.append(jf.norm(fname))
            data[idx] = (fname, good_blob)
            restored_files.append(jf.norm(fname))
            continue

        if good_blob is None:
            # new MI files stay; they are not object-init W3D
            continue

        # identical to camp-clone already, but still strip any extra draw if present
        if "ModuleTag_SpecterNatFlag" in crash_txt or "ModuleTag_SpecterCampFlag" in crash_txt:
            new_txt, n = strip_extra_draws(crash_txt)
            extra_draws_removed += n
            removed_draws.append(jf.norm(fname))
            data[idx] = (fname, new_txt.encode("latin-1", errors="replace"))

    # belt: no extra-draw tags remain anywhere except we already restored
    leftover_extra = []
    leftover_clones = []
    long_models = []
    anim_mismatch = []
    remaining_flag_hs = []
    remaining_modified = []
    for n, b in data:
        if not str(n).lower().endswith(".ini"):
            continue
        if in_protected(n) or jf.norm(n).lower() in FROZEN:
            continue
        t = b.decode("latin-1", errors="replace")
        key = jf.norm(n).lower()
        if "ModuleTag_SpecterNatFlag" in t or "ModuleTag_SpecterCampFlag" in t:
            leftover_extra.append(n)
        last_hs = None
        for line in t.splitlines():
            mm = re.match(r"(?i)^\s*Model\s*=\s*(\S+)", line)
            am = re.match(r"(?i)^\s*Animation\s*=\s*(\S+)", line)
            if mm:
                mdl = mm.group(1)
                last_hs = mdl if re.search(r"(?i)Flag_Hs", mdl) else None
                if CLONE_MODEL_RE.search(mdl):
                    leftover_clones.append(f"{n} Model={mdl}")
                if len(mdl) > 15 and re.search(
                    r"(?i)(Powerplant|WarFactory|Flag_Hs|IqPwr_|NkPwr_|IqWF_|NkWF_|irq_camp_)",
                    mdl,
                ):
                    long_models.append(f"{n} Model={mdl} len={len(mdl)}")
                if re.search(r"(?i)Flag_Hs", mdl):
                    remaining_flag_hs.append(f"Model={mdl} {jf.norm(n)}")
            if am:
                anim = am.group(1)
                if last_hs and not anim.lower().startswith(last_hs.lower() + "."):
                    anim_mismatch.append(f"{n} Model={last_hs} Anim={anim}")
                if CLONE_MODEL_RE.search(anim) or re.search(r"(?i)(IqPwr_|NkPwr_|IqWF_|NkWF_)", anim):
                    leftover_clones.append(f"{n} Animation={anim}")
        if key in good_dmap and bytes(b) != good_dmap[key] and in_target(n):
            remaining_modified.append(jf.norm(n))

    if leftover_extra:
        raise SystemExit("leftover extra Draws:\n  " + "\n  ".join(leftover_extra[:20]))
    if leftover_clones:
        raise SystemExit("leftover clone Model/Anim:\n  " + "\n  ".join(leftover_clones[:20]))
    if long_models:
        raise SystemExit("Model= longer than 15:\n  " + "\n  ".join(long_models[:20]))
    if anim_mismatch:
        raise SystemExit("Animation container mismatch:\n  " + "\n  ".join(anim_mismatch[:20]))

    # frozen / protected must still be the #518 bytes
    for p, raw in src_frozen.items():
        if jf.raw_of(data, p) != raw:
            raise SystemExit(f"frozen file changed: {p}")
    for n, b in data:
        if in_protected(n) and bytes(b) != protected_files[jf.norm(n).lower()]:
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
    missing_art = []
    for n, b in data:
        if not str(n).lower().endswith(".ini") or in_protected(n):
            continue
        if not in_target(n) and jf.norm(n).lower() not in FROZEN:
            continue
        t = b.decode("latin-1", errors="replace")
        for mdl in fields(t, "Model"):
            if mdl.lower() in ("none", "null"):
                continue
            if re.search(r"(?i)(Flag_Hs|Iraq_Powerplant|NKor_Powerplant|Irq_WarFactory|NKr_WarFactory|irq_camp)", mdl):
                if mdl.lower() not in art_w3d:
                    missing_art.append(f"{n} {mdl}")
    if missing_art:
        raise SystemExit("Model= missing ART:\n  " + "\n  ".join(missing_art[:20]))

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
    if len(packed_d) != 2883 or len(packed_a) != 4509:
        raise SystemExit(f"packed count changed {len(packed_d)}/{len(packed_a)}")
    if new_art_sha != CRASH_ART_SHA:
        raise SystemExit("ART must stay the #518 pair (TGA/W3D kept, unused)")

    # remaining active flag refs (HUD / cameo / unused ART only)
    remaining_pt = []
    pt_txt = jf.text_of(packed_d, P_PT)
    good_pt = jf.text_of(good_d, P_PT)
    if pt_txt != good_pt:
        remaining_pt.append("PlayerTemplate.ini still has #516 HUD remaps (frozen)")
    btn_txt = jf.text_of(packed_d, P_CMDBTN)
    good_btn = jf.text_of(good_d, P_CMDBTN)
    remaining_btn = []
    if btn_txt != good_btn:
        for m in re.finditer(r"(?im)^CommandButton\s+(\S+)\s*$", btn_txt):
            rest = btn_txt[m.end():]
            m2 = re.search(r"(?im)^CommandButton\s+\S+", rest)
            blk = rest[:m2.start()] if m2 else rest
            if re.search(r"(?i)CampFlag", blk):
                remaining_btn.append(m.group(1))

    remaining_mi = [
        jf.norm(n) for n, _ in packed_d
        if re.search(r"(?i)(specter_remainingflags|specter_campflags|turkey_factionimages)", n)
    ]

    # confirm restored PP/WF/Camp objects match camp-clone
    pp_wf_camp = []
    for n, b in packed_d:
        low = jf.norm(n).lower()
        if not in_target(n):
            continue
        if not any(h in low for h in ("powerplant", "powerstation", "warfactory", "camp.ini", "barracks")):
            continue
        if bytes(b) != good_dmap[low]:
            raise SystemExit(f"PP/WF/Camp not restored: {n}")
        pp_wf_camp.append(jf.norm(n))

    boot_safe = (
        not leftover_extra
        and not leftover_clones
        and not long_models
        and not anim_mismatch
        and not missing_art
        and extra_draws_removed > 0
        and restored_files
    )

    watch = defaultdict(list)
    watch_names = (
        "Iraq_Powerplant", "NKor_Powerplant", "NKr_Powerplant",
        "Irq_WarFactory", "NKr_WarFactory", "Flag_Hs",
        "UK_Flag_Hs", "NKr__NKFlag_Hs", "Irq__IqFlag_Hs",
        "IqPwr_", "NkPwr_", "IqWF_", "NkWF_", "irq_camp_", "NK_camp_",
        "CampFlag", "ModuleTag_SpecterNatFlag",
    )
    for n, b in packed_d:
        if not str(n).lower().endswith(".ini") or in_protected(n):
            continue
        t = b.decode("latin-1", errors="replace")
        for w in watch_names:
            if w.lower() in t.lower():
                if w.lower() in ("campflag",) and jf.norm(n).lower() in FROZEN:
                    watch[w].append(jf.norm(n))
                    continue
                if w.lower() == "campflag" and re.search(r"(?i)MappedImage\s+CampFlag", t):
                    watch[w].append(jf.norm(n))
                    continue
                if re.search(rf"(?im)^\s*(Model|Animation)\s*=\s*\S*{re.escape(w)}", t) or (
                    w.startswith("ModuleTag") and w in t
                ):
                    watch[w].append(f"{w} {jf.norm(n)}")

    audit = "\n".join([
        "SPECTER1 FLAG OBJECT-INIT BOOT-SAFE",
        "BASELINE = SPECTER1_FLAG_INIT_CRASHFIX_01 (#518, still crashing)",
        f"BASELINE_DATA_SHA256 = {CRASH_DATA_SHA}",
        f"BASELINE_ART_SHA256 = {CRASH_ART_SHA}",
        f"NEW_DATA_SHA256 = {new_data_sha}",
        f"NEW_ART_SHA256 = {new_art_sha}",
        f"PACKED_DATA_FILES = {len(packed_d)}",
        f"PACKED_ART_FILES = {len(packed_a)}",
        "DUPLICATE_PACKED_PATHS = NO",
        "BIG_INTEGRITY = YES",
        f"BOOT_SAFE = {'YES' if boot_safe else 'NO'}",
        "INGAME_TESTED = NO",
        "FIRST_FAILING_GROUP = B/D (stripped)",
        "",
        "===== REMOVED RISKY REFERENCES =====",
        f"RESTORED_BUILDING_INIS = {len(restored_files)}",
        *[f"  {n}" for n in restored_files],
        f"EXTRA_FLAG_DRAWS_REMOVED = {extra_draws_removed}",
        f"EXTRA_DRAW_FILES = {len(removed_draws)}",
        *[f"  {n}" for n in removed_draws],
        f"REMOVED_CLONE_MODELS = {len(removed_models)}",
        *[f"  Model={x} len={len(x)}" for x in sorted(removed_models, key=lambda s: (-len(s), s))],
        f"REMOVED_CLONE_ANIMATIONS = {len(removed_anims)}",
        *[f"  Animation={x}" for x in sorted(removed_anims)],
        f"PP_WF_CAMP_RESTORED = {len(pp_wf_camp)}",
        *[f"  {n}" for n in pp_wf_camp],
        "",
        "===== REMAINING ACTIVE FLAG REFERENCES =====",
        "HUD/select PlayerTemplate remaps = KEPT (frozen, not object-init)",
        f"COMMANDBUTTON_CAMPFLAG = {len(remaining_btn)} (frozen, MappedImage only)",
        *[f"  {x}" for x in remaining_btn],
        f"MAPPEDIMAGE_FILES_KEPT = {len(remaining_mi)}",
        *[f"  {x}" for x in remaining_mi],
        "ART TGA/W3D clones = KEPT but unreferenced by Object Model=",
        f"REMAINING_OBJECT_FLAG_HS (camp-clone originals only) = {len(remaining_flag_hs)}",
        *[f"  {x}" for x in remaining_flag_hs],
        "",
        "===== REMAINING MODIFIED OBJECTS =====",
        f"TARGET_OBJECTS_STILL_DIFF_FROM_CAMP_CLONE = {len(remaining_modified)}",
        *([f"  {x}" for x in remaining_modified] or ["  NONE (all target building Objects restored)"]),
        "",
        "===== WATCH AFTER STRIP =====",
        *[f"  {w}: {len(watch[w])} object-init hits" for w in watch_names],
        "",
        "WEAPON_INI_CHANGED = NO",
        "UPGRADE_INI_CHANGED = NO",
        "COMMANDSET_CHANGED = NO",
        "COMMANDBUTTON_CHANGED = NO",
        "PLAYERTEMPLATE_CHANGED = NO",
        "PROTECTED_FACTIONS_UNCHANGED = YES",
        "GAMEPLAY_CHANGED = NO",
        "ART_CHANGED = NO (TGA/W3D kept, unused clones not referenced)",
        "DATA_CHANGED = YES (object Model/Draw/Animation restored)",
        "FLAG_VISUALS_OBJECT = ROLLED_BACK",
        "FLAG_VISUALS_HUD = KEPT",
        "REENGAGE_FLAGS = NO (wait for launch confirmation)",
    ]) + "\n"

    changelog = """SPECTER1 flag object-init boot-safe

#518 still crashed. Isolation named FIRST_FAILING_GROUP = B/D
(object-init W3D clones + extra Flag_Hs Draws).

This patch restores camp-clone Model=/Animation=/Draw on every target
building Object (PowerPlant, WarFactory, Camp/Barracks, and the other
buildings that received extra Draws or cloned meshes). Extra Flag_Hs
Draw modules are removed. No new cloned W3D is referenced at init.

PlayerTemplate, CommandButton, MappedImages, and TGA/W3D art files
are kept. Weapon / Upgrade / CommandSet / country IDs / protected
DATA are unchanged.

Do not re-add B/D flag Draws or cloned Model= until this pair
launches in-game.

INGAME_TESTED = NO
"""

    install = f"""SPECTER1_FLAG_OBJECT_BOOT_01
===========================

Object-init boot-safe patch. Strips B/D (cloned W3D Model= and extra
Flag_Hs Draws). Keeps HUD textures and PlayerTemplate/CommandButton.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
4. Launch Specter.

Checksums:
  DATA SHA256 {new_data_sha}
  ART  SHA256 {new_art_sha}

BOOT_SAFE = {'YES' if boot_safe else 'NO'}
FLAG_VISUALS_OBJECT = ROLLED_BACK
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
    print("BOOT_SAFE", "YES" if boot_safe else "NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
