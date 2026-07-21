# Specter Patch — Multiplayer Sync Checklist

**Status:** PASS — Phase 4 Turkey AD/MLRS complete (incl. TRG-230)  
**Last audit:** `sync_audit.py` errors=0 (vendor Data.zip warn only)  
**Package:** `SYNC_MANIFEST.sha256` present

---

## Phase 4 unit gate (this drop)

| Unit | Object ID | LinkKey | Button | Baked cost |
|------|-----------|---------|--------|------------|
| TRG-230 | `Turkey_TRG230` | Patch_StrategicLauncher | ConstructTurkey_TRG230 | 1197 / 13.0s |
| TRG-300 Kaplan | `Turkey_TRG300` | Patch_StrategicLauncher | ConstructTurkey_TRG300 | baked |
| TRLG-230 | `Turkey_TRLG230` | Patch_StrategicLauncher | ConstructTurkey_TRLG230 | baked |
| Bora | `Turkey_Bora` | Patch_StrategicLauncher | ConstructTurkey_Bora | baked |
| HISAR-A+ | `Turkey_HISAR_A` | Patch_AirDefense | ConstructTurkey_HISAR_A | baked |
| HISAR-O+ | `Turkey_HISAR_O` | Patch_AirDefense | ConstructTurkey_HISAR_O | baked |
| SIPER | `Turkey_SIPER` | Patch_AirDefense | ConstructTurkey_SIPER | baked |
| Korkut | `Turkey_Korkut` | Patch_AirDefense | ConstructTurkey_Korkut | baked |

Weapons overlay: `Weapon_Turkey_Phase4.ini`  
Upgrades: `Upgrade_Turkey_HisarNetwork`, `Upgrade_Turkey_BoraGuidance`  
Production: WarFactory T–T3 + MIC + AI WF (player Object IDs)

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
