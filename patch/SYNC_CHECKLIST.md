# Specter Patch — Multiplayer Sync Checklist

**Status:** PASS — North Korea full playable faction added (Turkey remains complete)  
**Last audit:** `sync_audit.py` errors=0 (vendor Data.zip warn only)  
**Package:** `SYNC_MANIFEST.sha256` present

---

## North Korea playable gate

| System | Status |
|--------|--------|
| PlayerTemplate PlayableSide | Yes (`FactionNorthKorea`) |
| Object tree | `Object/Specter/North Korea/` Side=NorthKorea |
| Overlays | CommandButton/Set, Science, SpecialPower, Upgrade, OCL, Weapon |
| Buildings | CC→Power→Supply→WF/AAB→Radar→MIC; Worker/VT72B |
| Ground / AD / missiles | WF T–T3 + MIC; Patch_AirDefense / Patch_StrategicLauncher |
| Helicopter assault + transport | AAB + AI Airfield T3 |
| Advanced Air Base | 6-pad + heavies + Tu-22; unique CS |
| General Star | AirPower / AirAssault / Strategic |
| Economy | CountryBalance NorthKorea Low bake |
| AI | Side=NorthKorea; matching player CS |
| MP IDs | Unique vs Turkey (no shared CommandButton/OCL/SP/Object) |

## Turkey playable gate

Still green (unchanged intent). See prior checklist history.

---

## Automated checks

```bash
python3 patch/tools/economy/sync_audit.py
python3 patch/tools/economy/generate_sync_manifest.py --check
```

- [x] `sync_audit.py` exits 0  
- [x] No duplicate Object / CommandSet / CommandButton / Weapon / Upgrade / Science IDs  
- [x] Unique OCL namespaces per faction overlay  
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
5. Faction-tree `Side` ownership matches folder (`North Korea` → `NorthKorea`).
