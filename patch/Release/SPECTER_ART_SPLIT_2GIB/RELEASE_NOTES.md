# SPECTER ART 2GiB split — restore building models

The packed ART from PR #650 onward is larger than 2,147,483,648 bytes. SAGE 32-bit BIG offsets cannot read W3Ds past that boundary, so buildings stay constructible (DATA) but render invisible/white/untextured.

This pack splits ART into `_SPEC_ART_ONE.big` (textures) and `_SPEC_ART_TWO.big` (W3Ds). Every original ART entry is preserved byte-for-byte. DATA is unchanged.

Zero Hour auto-loads every `*.big` next to `generals.exe`. Put all three files in the SPECTER folder and delete the old oversized ART_ONE.

Static validation only. The game was not launched.
