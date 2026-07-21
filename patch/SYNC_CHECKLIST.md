# Specter Patch — Multiplayer Sync Checklist

**Status:** PASS — Turkey full audit completion (playable finished faction)  
**Last audit:** `sync_audit.py` errors=0 (vendor Data.zip warn only)  
**Package:** `SYNC_MANIFEST.sha256` present

---

## Turkey playable gate

| System | Status |
|--------|--------|
| PlayerTemplate PlayableSide | Yes |
| Building tree (Power→Supply→WF/AAB→Radar→MIC) | PowerPlant CS fixed; Worker=VT72B parity |
| Ground army (WF T–T3 + MIC) | AD + MLRS/Bora + armor/IFV + T72B3 |
| Air defense | HISAR/SIPER/Korkut/Sungur + HisarNetwork; Sam2/DefenseSite/Fahad3 site |
| Missile/artillery | TRG-230/300, TRLG-230, Bora + BoraGuidance |
| Helicopter assault | T129, Mi-28NE, Mi-35M3 (player AAB + AI Airfield T3) |
| Transport helicopter | Mi-8T; Mi-35 TRANSPORT |
| Advanced Air Base | 6-pad + heavies + Tu-22M3 + assault/transport |
| General Star | AirPower / AirAssault / Strategic + MIC AirAssault upgrade (science-gated) |
| Trainable Worker | Barracks slot 10 |
| Dead upgrades closed | AAMissile, Camouflage, T72B3, Precision/Radar extended |

---

## Automated checks

```bash
python3 patch/tools/economy/sync_audit.py
# expect: PASS, errors=0
python3 patch/tools/economy/generate_sync_manifest.py --check
```

- [x] `sync_audit.py` exits 0  
- [x] No duplicate Object / CommandSet / CommandButton / Weapon / Upgrade IDs  
- [x] No dual BuildCost/BuildTime  
- [x] No player CommandSet `*_AI` constructs  
- [x] LinkKeys on AD / strategic launchers  
- [x] CountryBalance bake + PatchBaseCost markers  
- [x] No Specter archive modifications  
- [ ] Lobby clients install same patch package — host responsibility  

---

## Non-negotiable rules

1. Deterministic data only; Lifetime Min==Max; no gameplay Random* assignments.  
2. Never modify `Data.zip` / `Specter_Data*` / `_SPEC_*` / `.big` / `payload.rar`.  
3. One identical patch package for the lobby (`SYNC_MANIFEST.sha256`).  
4. Unique IDs; player production ≠ AI-only variants.  
5. Faction-tree `Side` ownership matches folder.
