Specter Patch — Country Balance / Economy tools
===============================================

CENTRAL CONFIG (edit this only):
  patch/Data/INI/CountryBalance.ini

Apply (deterministic bake for multiplayer):
  python3 patch/tools/economy/apply_country_balance.py
  python3 patch/tools/economy/apply_country_balance.py --side Turkey
  python3 patch/tools/economy/apply_country_balance.py --dry-run --report /tmp/out.csv

Preview (no writes):
  python3 patch/tools/economy/preview_price.py \
    --side America --base-cost 2000 --origin Imported \
    --tech Gen5Fighter --category Aircraft

apply_dynamic_pricing.py is a thin alias of apply_country_balance.py.

Sync audit:
  python3 patch/tools/economy/sync_audit.py
  See patch/SYNC_CHECKLIST.md
