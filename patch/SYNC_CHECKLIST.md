# Specter Patch — Multiplayer Sync Checklist

**Status:** PASS — Iraq realistic playable faction completion  
**Last audit:** `sync_audit.py` errors=0 (vendor Data.zip warn only)  
**Package:** `SYNC_MANIFEST.sha256` present

---

## Iraq playable gate (this drop)

| System | Status |
|--------|--------|
| Faction identity | Iraqi roster; FOAB/Tu-22/Mi-28/S-400-clones removed from player path |
| Buildings / tech tree | CC→Power→Supply→WF/AAB→Radar→MIC; Worker parity |
| Infantry / vehicles / tanks | RG infantry, T-72, BMP, BTR, Assad Babel |
| Artillery / missiles | D-30, 2S1, BM-21, Scud/Al-Hussein (conventional) |
| Air force | Su-25/22/24, Mirage, MiG-23/25/29 (no Tu-22M3) |
| Helicopter assault / transport | Mi-35 + Mi-8 on Airfield/AAB |
| Air defense | Roland, SA-6, Sam8, ZSU-23-4, Sam2/DefenseSite |
| General Star | AirPower / AirAssault / Artillery |
| Economy | CountryBalance Iraq Low + PatchBaseCost bake |
| AI | Existing Iraq AI buildings retained; player CS no `*_AI` constructs |
| MP | Lifetime pinned; LinkKeys; no dual costs |

Turkey / North Korea trees were not modified in this drop.

---

## Automated checks

```bash
python3 patch/tools/economy/sync_audit.py
python3 patch/tools/economy/generate_sync_manifest.py --check
```

- [x] `sync_audit.py` exits 0  
- [x] No Specter archive modifications  
- [ ] Lobby clients install same patch package — host responsibility  

---

## Non-negotiable rules

1. Deterministic data only; Lifetime Min==Max.  
2. Never modify `Data.zip` / `Specter_Data*` / `_SPEC_*` / `.big` / `payload.rar`.  
3. Unique IDs; player production ≠ AI-only variants.  
4. Faction-tree `Side` matches folder (`Iraq Army` → `Iraq`).
