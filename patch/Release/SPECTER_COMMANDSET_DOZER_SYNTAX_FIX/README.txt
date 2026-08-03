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
- Replaced only the USA dozer stock strategy-center command:
  Command_ConstructAmericaStrategyCenter -> Command_ConstructAmerica_AdvancedAirBase
- Wrote CommandSet.ini with LF line endings only (CR bytes = 0).
- Kept AmericaVehicleDozer using stock CommandSet = AmericaDozerCommandSet.
- Kept America Command Center CommandSet untouched.
- Kept AAB six-aircraft roster, early unlock, approximately 2x size, and Russia 9M317_MissileObject without PRELOAD.

Verification
------------
- AmericaDozerCommandSet definitions: 1
- CommandSet.ini CommandSet blocks checked: 738
- CommandSet.ini CR bytes: 0
- CommandSet.ini SHA256: 80634329b63f25ac8180c4bd49f55d8b3a6899d9dc3c3cdeecf8a308e08a0bc0
- DATA BIG SHA256: 2fcc582e767001ac3e44e319a4f95f781dd112ebd7f612e6d216f1ea2be87f5c
- ART BIG SHA256: bf7ca6982fe38c51260be7b0a2ba25eef17c7c50ce2e9b20119001fcac8b0a73

Files
-----
- CommandSet.ini: extracted patched BIG entry for audit/reference only.
- The installable GameRoot BIGs are packaged in /opt/cursor/artifacts/SPECTER_FINAL_RELEASE.zip.

Warning
-------
Do not install a loose Data\INI\CommandSet.ini over this release. A loose override
can take precedence over the BIG entry and reintroduce stale commandsets or mixed
line endings.

Download
--------
https://filebin.net/specter-commandset-dozer-syntax-fix-66a9/SPECTER_FINAL_RELEASE.zip
ZIP SHA256: ab75510c1346b9865014f223f3498487c7cdcad972926b0c6fd4028cbbe29d00
