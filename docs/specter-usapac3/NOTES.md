# USAPAC3 merged into main SPECTER BIGs

Zero Hour was not run. In-game Command Center clicks were not tested.

Independent `_SPECTER_USAPAC3.big` is not the install method.

## Why the sidecar never showed up

`Launch_Specter.bat` only copies `_SPEC_DATA_ONE.big` and `_SPEC_ART_ONE.big`
next to `generals.exe`. America HQ CommandSet is
`Data\INI\CommandSet_FactionExpansion_Armies.ini`. A separate overlay BIG
was not on that load path.

## What this merge does

Adds USAPAC3 ART to `_SPEC_ART_ONE.big` (`Art\W3D\`, `Art\Textures\`).
Adds USAPAC3 DATA to `_SPEC_DATA_ONE.big` and writes America HQ slots on
the original CommandSet path:

- slot 6 = USAPAC3
- slot 12 = NASAMS (moved, not deleted)
- slots 1–5, 7–11, 13–14 unchanged

CSF strings were appended to the packed `Data\English\generals.csf`
(8151 → 8155 labels). Overlay CSF was not used as a replacement.

America_AD_THAAD, America_AD_Patriot, America_AD_NASAMS objects were not
edited. Stock Weapon.ini / CommandSet.ini / CommandButton.ini were not
replaced.

## Rollback

Original stock BIGs were not overwritten in place. Hashes:

- DATA `c7062a4ab12677a2e797d1a98324b14fcefd0a0cbdbbcec0a2e527553e377c05`
- ART  `bb5d15325e227bad247450dc379bbf85b8bbd620beacc9b2f8db89976b1989d7`

Copies: `/tmp/usapac3-original-backup/`
