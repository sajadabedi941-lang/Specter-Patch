# Russia Aircraft Visual Dependency Manifests (Phase 1)

Donor source: `DONOR_Art.part001.rar` … `DONOR_Art.part069.rar`  
Policy: DONOR ART = YES, DONOR GAMEPLAY DATA = NO  
Baseline required: PR #370 complete `_SPEC_DATA_ONE.big` + `_SPEC_ART_ONE.big`  
Expected DATA SHA256: `c7062a4ab12677a2e797d1a98324b14fcefd0a0cbdbbcec0a2e527553e377c05`

## Tu-160 (Blackjack)

| Role | Asset |
|------|-------|
| Primary W3D | `Art/W3D/LSFRussiaTu160.W3D` |
| Damaged | `Art/W3D/LSFRussiaTu160d.W3D` |
| ReallyDamaged | `Art/W3D/LSFRussiaTu160k.W3D` |
| Animation | embedded `LSFRussiaTu160.LSFRussiaTu160` (DOOR_1 sweep) |
| Textures | `LSFRussiaTU160.dds` / `d` / `k` |
| Button art | `TU-160.tga`, `TU160TB.tga` |
| Object skeleton | `RussiaJetTU160Clean` |

## Tu-95 (Bear)

| Role | Asset |
|------|-------|
| Primary W3D | `Art/W3D/CWCruTu95.W3D` |
| Damaged | `Art/W3D/CWCruTu95_d.W3D` |
| ReallyDamaged | `Art/W3D/CWCruTu95_k.W3D` |
| Animation | `CWCruTu95.CWCruTu95` LOOP (prop bones) |
| Textures | `CWCruTu95.dds` (+ casing alias `CWCruTU95.dds`), `CWCgenPropellor.*`, `CWCgenReflective.*` |
| Button art | `Tu95.tga`, `Tu95TB.tga` |
| Object skeleton | `RussiaJetTu95Visual` |

## An-124 (Ruslan)

| Role | Asset |
|------|-------|
| Primary W3D | `Art/W3D/CWCruAn124.W3D` |
| Subobject | `Art/W3D/CWCruAn124_b.W3D` |
| Textures | `CWCruAn124.dds`, `CWCruAn124Nav.dds`, `NavL`, `NavR` |
| Button art | `AN124.tga`, `AN124TB.tga` |
| Object skeleton | `RussiaJetAn124Visual` |

## An-225 (Mriya)

| Role | Asset |
|------|-------|
| Primary W3D | `Art/W3D/A_AN225_100.W3D` |
| Mesh texture deps | `A_AN225_100.tga`, **`A_E-3_100.tga`** (required by mesh) |
| Related W3D | `A_E-3_100.W3D` (texture family companion) |
| Button art | `RussiaAN225.tga`, `RussiaAN225TB.tga` |
| Object skeleton | `RussiaJetAn225Visual` |

## A-50 (Mainstay)

| Role | Asset |
|------|-------|
| Primary W3D | `Art/W3D/CWCruA50.W3D` |
| Rotodome anim | `CWCruA50.CWCruA50` LOOP (DOME / DISH hierarchy) |
| Textures | `CWCruA50.dds`/`.tga`, `CWCruAn124NavL/R.dds`, `CWCgenReflective.*` |
| Button art | `RussiaA50.tga`, `RussiaA50TB.tga` |
| Object skeleton | `RussiaJetA50Visual` |

## avionIL76

| Role | Asset |
|------|-------|
| Primary W3D | `Art/W3D/Yier76.W3D` |
| Required texture | **`yujing1.dds`/`.tga`** (missing = pink/broken) |
| Hull texture | `yier76.tga` |
| Button art | `yier76.tga`, `yier76TB.tga` |
| Object skeleton | `RussiaJetAvionIL76Visual` |

## cargoIL76

| Role | Asset |
|------|-------|
| Primary W3D | `Art/W3D/LSFRussiaYR76.W3D` |
| Damaged | `LSFRussiaYR76d.W3D` |
| ReallyDamaged | `LSFRussiaYR76k.W3D` |
| Textures | `LSFRussiaYR76.tga` / `d` / `k` |
| Button art | `CargoIL76Russia.tga`, `CargoIL76RussiaTB.tga` |
| Object skeleton | `RussiaJetCargoIL76Visual` |

## Staging note

Phase 1 donor ART extracted into `patch/Art/W3D` and `patch/Art/Textures`.  
**PACKING BLOCKED** until PR #370 complete BIG pair is provided (gofile premium-locked from this agent).
