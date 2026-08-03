SPECTER COMMANDSET DOZER SYNTAX FIX
====================================

Fixes the GameRoot BIG crash:
  Data\INI\CommandSet.ini parsing error at CommandSet AmericaDozerCommandSet

What changed
------------
- Started from verified stock _SPEC_DATA_ONE.big SHA256:
  846a6a363af8c5c7c953ba2e4292f1aa72d807e22b5ce5b49365e59770fbebb7
- Patched the existing Data\INI\CommandSet.ini BIG entry only.
- Kept exactly one CommandSet AmericaDozerCommandSet definition.
- Removed USA Strategy Center commands from the dozer CommandSet and put the Advanced Airfield button in those slots.
- Wrote CommandSet.ini with LF line endings only (CR bytes = 0).
- Kept AmericaVehicleDozer using stock CommandSet = AmericaDozerCommandSet.
- Kept America Command Center CommandSet untouched.
- Restored the correct six-aircraft America Advanced Airfield roster from advanced-airfield-six / usa-build-palette-restore lineage.

America Advanced Airfield roster
--------------------------------
1. B-2  -> Patch_America_B2
2. B-21 -> Patch_America_B21
3. B-52 -> Patch_America_B52
4. C-5  -> Patch_America_C17
5. F-117 -> AmericaJetStealthFighter (science gate cleared)
6. E-3  -> Patch_America_E3

America_AdvancedAirBase settings
--------------------------------
- Prerequisites: empty
- Scale: 2.00
- Geometry: 224.0 x 148.0 x 50.0
- Model/art: US_AirField

Verification
------------
- AmericaDozerCommandSet definitions: 1
- CommandSet.ini CR bytes: 0
- CommandSet.ini SHA256: b50dfb1b1445d18b1c6ff1f979494fc453010f3de7fddd20304cf066497a914b
- DATA BIG SHA256: bbb247809bfb6bde10aca03a9bf9bad802f50b2ce6a5c25aa6f538487a148f08
- ART BIG SHA256: bf7ca6982fe38c51260be7b0a2ba25eef17c7c50ce2e9b20119001fcac8b0a73
- Russia 9M317 PRELOAD: False

Files
-----
- CommandSet.ini: extracted patched BIG entry for audit/reference only.
- VERIFY.json: exact verification from rebuilt BIG.

Warning
-------
Do not install a loose Data\INI\CommandSet.ini over this release. A loose override
can take precedence over the BIG entry and reintroduce stale commandsets or mixed
line endings.

Download
--------
https://filebin.net/specter-commandset-aab-corrected-66a9/SPECTER_FINAL_RELEASE.zip
ZIP SHA256: 9bcf8ba305c265e8218292728f17208b3659840d2ec9744ab3e648378b8ae9a8
