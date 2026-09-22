You are continuing the Specter Zero Hour init-crash repair.

Do not restore flags, cloth, or extra Draws.
Do not retarget Model= or Animation=.
Do not touch Weapon / Upgrade / CommandSet / protected DATA / building Object INIs.

Read first:
- patch/Release/SPECTER1_FLAG_STRIP02_FORENSIC_01/FORENSIC_SUMMARY.txt
- patch/Release/SPECTER1_FLAG_STRIP02_FORENSIC_01/audit.txt

Proven:
- STRIP_02 still crashes in-game.
- Unused clone W3D preload is not the cause.
- Remaining diffs vs last known launch are Group A only (3 new MappedImage INIs, PlayerTemplate, CommandButton, 17 Flag TGAs, 5 Turkey TGA format swaps).

Exact offending file found:
  Data\INI\MappedImages\HandCreated\Turkey_FactionImages.INI
  starts with ASCII apostrophe `'` before `; SPECTER PATCH...`

Required isolated repair (one DATA file only):
1. Branch cursor/flag-turkey-mi-parse-7da3 from cursor/flag-art-clone-strip-7da3.
2. Source DATA = STRIP_02 / OBJECT_BOOT (SHA 3e42c369fb30e229062fcbf29feafb15c9e59472dc16757d8e5f0c0092813221).
   Source ART = STRIP_02 (SHA c16055702267e59770a7f657f843ea49840889b453a5c0611e8971045afe05b7). Copy ART bytes; do not rebuild ART.
3. Rewrite ONLY Turkey_FactionImages.INI: remove the leading `'`. Keep the five MappedImage blocks. Use CRLF. Do not change image names.
4. Leave PlayerTemplate, CommandButton, Specter_RemainingFlags, Specter_CampFlags, all Object INIs, Weapon/Upgrade/CommandSet untouched.
5. Scan before ZIP: file must start with `;` or `MappedImage`; no `'`; five MappedImages still present; DATA otherwise byte-identical except that one file; ART SHA unchanged.
6. Full pair ZIP SPECTER1_FLAG_TURKEY_MI_PARSE_01. BOOT_SAFE only if scans pass. INGAME_TESTED = NO.
7. Do not claim in-game fixed.

If that pair still crashes, stop and isolate the other two new MI files + PlayerTemplate next. Do not add cloth.
