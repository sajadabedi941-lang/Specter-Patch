You are continuing the Specter (C&C Generals Zero Hour) flag-init crash repair.

Do not start random fixes. Read this whole prompt. Audit before you edit. Do not claim fixed unless every required scan passes.

## Project rules

GameRoot is only:
- generals.exe
- `_SPEC_DATA_ONE.big`
- `_SPEC_ART_ONE.big`

INI/ART live inside those two BIG files. No loose Data/Art. No new BIG names.

Never touch:
- Weapon.ini
- Upgrade.ini
- CommandSet.ini
- CommandButton.ini
- PlayerTemplate.ini
- PlayerTemplate_SpecterPatch.ini
- Country IDs
- Protected DATA folders: USA, Iran, Israel, China, Russia, NATO, Egypt, North Korea, Iraq

Do not modify the working Russia baseline.
Do not reintroduce flag visuals.
Do not add flags back in one batch.
Do not create a partial ZIP.

Priority:
1. Zero Hour launches.
2. Gameplay untouched.
3. Flag cloth stays off until launch is confirmed.

## What already happened (do not repeat)

- PR #516 / #517 added flag TGA, W3D clones, building Model= retargets, extra Flag_Hs Draws, HUD remaps, camp cameos.
- Crash: Uncaught Exception during initialization. No last error. No stack.
- PR #518 shortened packed names to IqPwr_/NkPwr_/IqWF_/NkWF_ and rewrote Animation= to `<file>.Irq__IqFlag_Hs`. Extra Draws were kept. Game still crashed.
- PR #519 is a byte-copy of SPECTER1_CAMP_CLONE_IRAQ_VIETNAM (last known launch).
- PR #520 (current latest release SPECTER1_FLAG_OBJECT_BOOT_01) restored 118 building Object INIs to camp-clone and removed extra Draws. ART is still the #518 ART.

## Audit already completed (re-verify, then act)

Read:
- `patch/Release/SPECTER1_FLAG_REMAIN_AUDIT_01/FLAG_ONLY_AUDIT.txt`
- `patch/flag_remain_init_audit.py`

Current pair:
- DATA SHA256 `3e42c369fb30e229062fcbf29feafb15c9e59472dc16757d8e5f0c0092813221`
- ART  SHA256 `2b84d7836b6560d22f32ce2c6687a167a52515ea2f70aeecbc934968fccb9af1`

Last known launch:
- SPECTER1_CAMP_CLONE_IRAQ_VIETNAM
- DATA `e04a7b08a2fc6ae5648611d68b3b026e5cb004a103e92b2926d246a9ad1c6dfd`
- ART  `15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a`

Confirmed broken chain class that #518 missed:

`clone_w3d()` only swapped the texture string. Internal mesh/animation container stayed the donor name.

Examples you must re-dump from ART before editing:
- `UK_Flag_Hs.W3D` packed name UK_Flag_Hs, internal IRQ__IQFLAG_HS, texture UK_Flag.tga
- `IqPwr_UAE.W3D` packed name IqPwr_UAE, internal IRAQ_POWERPLANT, texture UAE_Flag.tga
- `irq_camp_JP.W3D` packed name irq_camp_JP, internal IRQ_CAMP, texture JP_Flag.tga
- `NkWF_JP.W3D` packed name NkWF_JP, internal NKR_WARFACTORY, texture JP_Flag.tga

On the current DATA pair, no Object `Model=` points at those clones. Extra Draws are gone. Remaining Object Flag_Hs are only camp-clone Abbas / NuclearCenter (`Irq__IqFlag_Hs` / `NKr__NKFlag_Hs`) and those containers match.

Residual crash risk: the 60 unused clone W3Ds are still packed in ART. If ZH indexes every W3D in `_SPEC_ART_ONE.big` at init, filename != internal mesh can still throw Uncaught Exception during initialization.

Vanilla Model= meshes that live in INIZH.big / game ART and are missing from `_SPEC_ART_ONE.big` are overlay-expected. Do not treat them as flag bugs. Do not rename NationalGround IRIST / M2A3 long names.

## Required work

Create branch `cursor/flag-art-clone-strip-7da3` from `cursor/flag-object-boot-7da3`.

Inspect, then rebuild one complete pair:

1. Re-read current OBJECT_BOOT DATA+ART and camp-clone ART. Verify the SHAs above.
2. Confirm again: zero `ModuleTag_SpecterNatFlag` / `SpecterCampFlag`, zero `Model=` / `Animation=` of IqPwr_/NkPwr_/IqWF_/NkWF_/irq_camp_*/country `*_Flag_Hs`.
3. Rebuild `_SPEC_ART_ONE.big` from camp-clone ART, then copy only these textures from current ART (do not copy any of the 60 clone W3Ds):
   - `Art\Textures\DE_Flag.tga` and the other 16 country `*_Flag.tga`
   - the 5 already-overwritten Turkey HUD textures if they exist in current ART (`GameinfoTurkey.tga`, `SSObserverTurkey.tga`, `Turkey_Flag.tga`, `Turkey_Logo.tga`, `WatermarkTurkey.tga`)
4. Leave `_SPEC_DATA_ONE.big` as the current OBJECT_BOOT DATA bytes. Do not rewrite PlayerTemplate, CommandButton, Weapon, Upgrade, CommandSet, or any building Object INI.
5. Do not add extra Draws. Do not retarget Model=. Do not rename internals. Do not reintroduce cloned W3Ds.

## Required scans before you may write the ZIP

After packing, scan the new pair and fail the packer if any check fails:

- Every `Model=` / `Animation=` / `Draw=` that matches Flag_Hs, IqPwr_, NkPwr_, IqWF_, NkWF_, irq_camp_, UK_Flag_Hs, Irq__IqFlag_Hs, NKr__NKFlag_Hs
- Object -> Draw -> Model -> Animation -> W3D for those only
- Model and Animation container must be the same W3D stem
- That W3D must exist in the new ART
- Internal mesh/anim container dumped from the W3D must match the Model/Animation stem (case-insensitive)
- No packed W3D filename that is a #516-518 clone (IqPwr_, NkPwr_, IqWF_, NkWF_, irq_camp_XX, country *_Flag_Hs)
- No duplicate DATA or ART paths
- No Model= of a removed clone name
- Frozen INIs byte-identical to OBJECT_BOOT
- Protected DATA byte-identical to OBJECT_BOOT
- MappedImage Texture= for the kept flag/Turkey images still resolve in the new ART

## Output

One complete GameRoot pair, not a partial patch:

- `_SPEC_DATA_ONE.big`
- `_SPEC_ART_ONE.big`
- INSTALL.txt
- changelog.txt
- audit.txt with BOOT_SAFE = YES/NO
- SHA256.txt
- one ZIP containing those files only

Release name: `SPECTER1_FLAG_ART_CLONE_STRIP_01`

Audit must list:
- Removed unused W3D clones
- Remaining active flag references (PT / CommandButton / MappedImage / original Abbas Flag_Hs only)
- Remaining modified objects (should be none vs OBJECT_BOOT DATA)

Commit the packer and the small docs. Do not commit the BIG/ZIP. Push. Open a draft PR against `cursor/flag-object-boot-7da3`. Create the GitHub Release with the ZIP.

## Success condition

You may not say "fixed".
You may say BOOT_SAFE = YES only if every scan above passed.
INGAME_TESTED = NO unless a real Zero Hour launch was performed.
Do not restore building cloth or extra Draws after the pack. Wait for launch confirmation.
