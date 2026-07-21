Specter Patch — Economy / Dynamic Pricing tools
===============================================

apply_dynamic_pricing.py
  Reads patch/Data/INI/Economy/* tables and rewrites BuildCost / BuildTime
  on Object and Upgrade INIs under patch/. Preserves bases via PatchBaseCost.

  python3 patch/tools/economy/apply_dynamic_pricing.py
  python3 patch/tools/economy/apply_dynamic_pricing.py --side Turkey
  python3 patch/tools/economy/apply_dynamic_pricing.py --dry-run --report /tmp/out.csv

preview_price.py
  What-if calculator (no file writes).

  python3 patch/tools/economy/preview_price.py \
    --side Turkey --base-cost 2000 --origin Imported \
    --tech Gen5Fighter --category Aircraft

Contract: patch/Data/INI/Economy/DYNAMIC_PRICING.txt
