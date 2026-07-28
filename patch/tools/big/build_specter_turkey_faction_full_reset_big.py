#!/usr/bin/env python3
"""FULL Turkey faction reset — stop patching individual files.

1. Backup every Turkey Armed Forces INI from _SPEC_DATA_ONE.big
2. DELETE Turkey custom Projectiles / WeaponObjects / Shells
3. Rebuild Turkey aircraft/drones from validated USA/China/Russia donors
4. Retarget ALL Turkey weapon files' ProjectileObject lines to existing
   stock USA/Russia missiles (NO new weapon objects created)
5. Remap missing Turkey W3D models to existing ART; ASCII-sanitize
6. Full Turkey validation; pack BIG+ZIP
"""
from __future__ import annotations

import re
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

import build_specter_aircraft_aab_global_fixed_big as base
import build_specter_turkey_aircraft_roster_fixed_big as roster
import build_specter_turkey_faction_ini_batch_fixed_big as turkey_batch
import build_specter_turkey_weaponobjects_crash_fix_big as turkey_wo

ROOT = Path(__file__).resolve().parents[2]
SRC = (
    ROOT
    / "Release"
    / "SPECTER_SPEC_DATA_ONE_TURKEY_WEAPONOBJECTS_FULL_REBUILD"
    / "_SPEC_DATA_ONE.big"
)
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_TURKEY_FACTION_FULL_RESET"
BACKUP = OUT / "_BACKUP_TURKEY_INIS"

USA = r"Data\INI\Object\Specter\United States Of America"
RUS = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
AAB = r"Data\INI\Object\Specter\PatchSystems\AdvancedAirBase\Aircraft_AAB_Global.ini"
TUR = r"Data\INI\Object\Specter\Turkey Armed Forces"
CYR_M = "\u041c"

AIR_MAP: list[tuple[str, str, str, str]] = [
    (rf"{TUR}\Airforce\Turkey_F16Block70.ini", "Turkey_F16Block70", rf"{USA}\Airforce\F16CM_BLK50_DB52.ini", "AmericaJetF-16C_AG"),
    (rf"{TUR}\Airforce\Turkey_Hurjet.ini", "Turkey_Hurjet", rf"{USA}\Airforce\F15C.ini", "AmericaJetF-15E_AA"),
    (rf"{TUR}\Airforce\Turkey_KAAN.ini", "Turkey_KAAN", rf"{USA}\Airforce\F22A_AA.ini", "AmericaJetF-22A_AA"),
    (rf"{TUR}\Airforce\Turkey_Anka3.ini", "Turkey_Anka3", rf"{USA}\Airforce\F35C.ini", "AmericaJetF35C"),
    (rf"{TUR}\Airforce\Turkey_B2.ini", "Turkey_B2", AAB, "Patch_America_B2"),
    (rf"{TUR}\Airforce\Turkey_B52.ini", "Turkey_B52", rf"{USA}\ScienceObjects\B52H.ini", "AmericaJetB52"),
    (rf"{TUR}\Airforce\Turkey_AWACS.ini", "Turkey_AWACS", rf"{USA}\ScienceObjects\E3G.ini", "US_E3G_AWACS"),
    (rf"{TUR}\Airforce\Turkey_Akinci.ini", "Turkey_Akinci", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Airforce\Turkey_TB2.ini", "Turkey_TB2", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Airforce\Turkey_Tanker.ini", "Turkey_Tanker", AAB, "Patch_Turkey_KC135R"),
    (rf"{TUR}\Airforce\Turkey_Transport.ini", "Turkey_Transport", AAB, "Patch_Turkey_A400M"),
    (rf"{TUR}\Airforce\Turkey_Tu-22M3.ini", "Turkey_Tu-22M3", rf"{RUS}\Airforce\TU22M3M.ini", "RussiaJetTu22M3M"),
    (rf"{TUR}\Airforce\Turkey_Tu-22M3_AI.ini", "Turkey_Tu-22M3_AI", rf"{RUS}\Airforce\TU22M3M.ini", "RussiaJetTu22M3M"),
    (rf"{TUR}\Airforce\Turkey_Mig-29A.ini", "Turkey_Mig-29A", rf"{RUS}\Airforce\Mig35.ini", "RussiaJetMig35"),
    (rf"{TUR}\Airforce\Turkey_Mig-25BM.ini", "Turkey_Mig-25BM", rf"{RUS}\Airforce\MIG31K.ini", "RussiaJetMig31K"),
    (rf"{TUR}\Airforce\Turkey_Su-22M3.ini", "Turkey_Su-22M3", rf"{RUS}\Airforce\SU34M.ini", "RussiaJetSu34"),
    (rf"{TUR}\Airforce\Turkey_Su-24MK.ini", "Turkey_Su-24MK", rf"{RUS}\Airforce\Su35S_TS.ini", "RussiaJetSu35AG"),
    (rf"{TUR}\Airforce\Turkey_Su-25K.ini", "Turkey_Su-25K", rf"{RUS}\Airforce\SU57.ini", "RussiaJetSu57"),
    (rf"{TUR}\Airforce\Turkey_Su-24MR.ini", "Turkey_Su-24MR", AAB, "Patch_China_J16"),
    (rf"{TUR}\Airforce\Turkey_Mig-23BN.ini", "Turkey_Mig-23ML", AAB, "Patch_China_J10"),
    (rf"{TUR}\Airforce\Turkey_MirageF1-Bq.ini", "Turkey_MirageF1_Bq", AAB, "Patch_China_J20"),
    (rf"{TUR}\Airforce\Turkey_Mi-28NE.ini", "Turkey_Mi-28NE", rf"{USA}\Airforce\AH64D.ini", "AmericaVehicleComanche"),
    (rf"{TUR}\Airforce\Turkey_Mi-35M3.ini", "Turkey_Mi-35M3", rf"{USA}\Airforce\AH64E.ini", "AmericaHelicopterAH64E"),
    (rf"{TUR}\Airforce\Turkey_Mi-8.ini", "Turkey_Mi-8T", rf"{USA}\Airforce\AH64E - Bk.ini", "AmericaHelicopterAH64E-BK"),
    (rf"{TUR}\Airforce\Turkey_T129.ini", "Turkey_T129", rf"{USA}\Airforce\AH64E.ini", "AmericaHelicopterAH64E"),
    (rf"{TUR}\Drones\Turkey_Kizilelma.ini", "Turkey_Kizilelma", rf"{USA}\Airforce\F22A_AG.ini", "AmericaJetStealthFighter"),
    (rf"{TUR}\Drones\Turkey_HeavyUAV.ini", "Turkey_HeavyUAV", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Turkey_StealthUAV.ini", "Turkey_StealthUAV", rf"{USA}\Airforce\F22A_AG.ini", "AmericaJetStealthFighter"),
    (rf"{TUR}\Drones\Ababil200.ini", "Turkey_Ababil200", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Ababil200R.ini", "TurkeyDronesAbabil200Recon", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Quds5.ini", "Turkey_Quds5", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Quds5_AI.ini", "TurkeyDroneQuds5_AI", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
    (rf"{TUR}\Drones\Sarab3.ini", "Turkey_Sarab3", rf"{USA}\Drones\Mq9.ini", "AmericaDronesMq9"),
]

F16V_PATH = rf"{TUR}\Airforce\Turkey_F16V.ini"
F16V_DONOR = rf"{USA}\Airforce\F16CM_BLK50_DB52.ini"
F16V_RENAME = {
    "AmericaJetF-16C_AG": "Turkey_F16V",
    "AmericaJetF16CMB50_Mixed": "Turkey_F16V_Mixed",
    "AmericaJetF16CMB50_AGM": "Turkey_F16V_AGM",
    "AmericaJetF16CMB50_GBU24": "Turkey_F16V_GBU24",
}

# Explicit ProjectileObject retargets -> existing stock objects only
WEAPON_PROJECTILE_RETARGET = {
    "Turkey_9M14_MissileObject": "ComancheAntiTankMissile",
    "Turkey_Projectile_AIM120C_F16V": "RaptorJetMissile",
    "Turkey_Projectile_F16Blk70_AIM120": "RaptorJetMissile",
    "Turkey_Projectile_Goktug_KAAN": "RaptorJetMissile",
    "Turkey_Projectile_ADSAM": "PatriotMissile",
    "Turkey_Projectile_SAM": "PatriotMissile",
    "Turkey_Projectile_SHORAD": "StingerMissile",
    "Turkey_Projectile_AntiDrone": "StingerMissile",
    "Turkey_Projectile_MD": "PatriotMissile",
    "Turkey_Projectile_ATGM": "ComancheAntiTankMissile",
    "Turkey_Projectile_Altay_ATGM": "ComancheAntiTankMissile",
    "Turkey_Projectile_Tank": "HumveeMissile",
    "Turkey_Projectile_Cruise": "TomahawkMissile",
    "Turkey_Projectile_MLRSShort": "StingerMissile",
    "Turkey_Goktug_Projectile": "RaptorJetMissile",
    "Turkey_SOM_Cruise_Projectile": "TomahawkMissile",
    "Turkey_SOM_Projectile": "TomahawkMissile",
    "Turkey_Tayfun_Projectile": "ScudStormMissile",
    "Turkey_TRG122_Projectile": "StingerMissile",
    "Turkey_Fab-100": "AuroraBomb",
    "Turkey_Fab-250": "AuroraBomb",
    "Turkey_Fab-500FF": "AuroraBomb",
    "Turkey_Kab500": "AuroraBomb",
    "Turkey_AlAbidMissile": "ScudStormMissile",
    "Turkey_HussieanMissile": "ScudStormMissile",
    "Turkey_AlAbidWarheadReentryProjectile": "NeutronMissile",
    "Turkey_HussieanWarheadReentryProjectile": "NeutronMissile",
    # Turkey weapons previously pointed at other-faction projectiles — force USA/Russia stock
    "Ukraine_IRIS_T_Projectile": "PatriotMissile",
    "Ukraine_Grad_Projectile": "ScudStormMissile",
    "9M14_AT-3A": "ComancheAntiTankMissile",
}

# Heuristic fallback when a Turkey_* projectile remains
def fallback_projectile(name: str) -> str:
    n = name.lower()
    if any(k in n for k in ("aim", "aam", "goktug", "r27", "r40", "kh25", "kh29", "kh58")):
        return "RaptorJetMissile"
    if any(k in n for k in ("sam", "adsam", "md", "patriot", "s125", "s75", "buk")):
        return "PatriotMissile"
    if any(k in n for k in ("stinger", "shorad", "antidrone", "rpg", "grad", "mlrs", "trg", "s8")):
        return "StingerMissile"
    if any(k in n for k in ("atgm", "kornet", "tank", "altay", "9m14", "fgm")):
        return "ComancheAntiTankMissile"
    if any(k in n for k in ("cruise", "tomahawk", "som", "kh22", "kh55", "kh101")):
        return "TomahawkMissile"
    if any(k in n for k in ("scud", "tayfun", "abbas", "huss", "ballistic", "alabid", "srbm", "mrbm", "icbm")):
        return "ScudStormMissile"
    if any(k in n for k in ("fab", "kab", "bomb", "gbu", "warhead")):
        return "AuroraBomb"
    return "RaptorJetMissile"


MODEL_REMAP = {
    "AIRngr_F_SKN": "AIRNGR_IDG",
    "Turkey_Irg-Ak": "AIRNGR_RN2",
    "Turkey_Irg-Pk": "AIRNGR_RN2",
    "Turkey_Irg-Rpg": "AIRNGR_AT2",
    "Turkey_Irg-Rpg29": "AIRNGR_ATM",
    "Turkey_Irg-AT": "AIRNGR_ATM",
    "Turkey_Irg-mrt": "US_Mortar",
    "UIWRKR_SKN": "AIRNGR_IDG",
    "MIG-25bm_IRQ": "RUS_MIG31K",
    "Turkey_Mig-25bm": "RUS_MIG31K",
    "Turkey_100Cannon": "Iraq_100Cannon",
    "Turkey_D30": "Iraq_D30",
    "Turkey_Powerplant": "US_PowerPlant",
    "Turkey_Supply": "US_Supply",
    "Turkey_Adnan1": "Iraq_Adnan1",
    "Turkey_IL-76": "RUS_IL76MD90A",
    "Turkey_Tu22m3": "RUS_TU22M3M",
    "Turkey_Bm21": "Iraq_BM21",
    "Turkey_Bm21D": "Iraq_BM21D",
    "Turkey_Bm21R": "Iraq_BM21R",
    "UBArmDeal_DNS": "US_WarFactory",
    "Turkey_BMP1M3": "Irq_BMP1P",
    "Turkey_BMP-2M2": "Iraq_BMP-2M2",
    "Turkey_2S1": "Irq_T72M1",
    "NULL": "AIM-120",
}

def basename(name: str) -> str:
    return Path(name.replace("\\", "/")).name.lower()


def is_turkey_ini(name: str) -> bool:
    return "Turkey Armed Forces" in name.replace("/", "\\") and name.lower().endswith(".ini")


def is_turkey_custom_weapon_file(name: str) -> bool:
    ln = name.replace("/", "\\")
    if "Turkey Armed Forces" not in ln:
        return False
    if "\\Projectiles\\" in ln:
        return True
    return basename(name) in {"turkey_weaponobjects.ini", "turkey_shells.ini"}


def is_weapon_definition_file(name: str) -> bool:
    """All Weapon*.ini definitions (never WeaponObjects)."""
    bn = basename(name)
    if not bn.endswith(".ini"):
        return False
    if "weaponobject" in bn:
        return False
    return bn == "weapon.ini" or bn.startswith("weapon_")


def ascii_sanitize(text: str) -> str:
    text = text.replace(CYR_M, "M")
    for old, new in turkey_batch.ASCII_MAP.items():
        text = text.replace(old, new)
    if any(ord(c) > 127 for c in text):
        text = "".join(c if ord(c) < 128 else "?" for c in text)
    # never leave 9?317 style corruption from Cyrillic M
    text = re.sub(r"9\?317", "9M317", text)
    return text


def backup_turkey(entries, backup_root: Path) -> int:
    if backup_root.exists():
        shutil.rmtree(backup_root)
    backup_root.mkdir(parents=True, exist_ok=True)
    n = 0
    for name, raw in entries:
        if not is_turkey_ini(name):
            continue
        rel = Path(*Path(name.replace("\\", "/")).parts)
        parts = list(rel.parts)
        if "Turkey Armed Forces" in parts:
            idx = parts.index("Turkey Armed Forces")
            rel = Path(*parts[idx:])
        dest = backup_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        n += 1
    (backup_root / "BACKUP_MANIFEST.txt").write_text(
        f"Turkey INI backup count={n}\n", encoding="ascii"
    )
    return n


def clone_multi_f16v(donor_text: str, old_turkey_text: str) -> str:
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Object\s+(\S+)", donor_text)]
    blocks: list[str] = []
    for i, (start, name) in enumerate(starts):
        if name not in F16V_RENAME:
            continue
        end = starts[i + 1][0] if i + 1 < len(starts) else len(donor_text)
        block = donor_text[start:end]
        turkey_name = F16V_RENAME[name]
        identity = roster.extract_identity(old_turkey_text, turkey_name)
        identity.setdefault("display", f"OBJECT:{turkey_name}")
        fixed = roster.clone_to_turkey(
            block,
            donor_object=name,
            turkey_object=turkey_name,
            identity=identity,
            donor_label="F16CM_BLK50_DB52.ini",
        )
        fixed = re.sub(
            r"(?m)^; SPECTER TURKEY AIRCRAFT ROSTER FIX",
            "; SPECTER TURKEY FACTION FULL RESET",
            fixed,
            count=1,
        )
        blocks.append(fixed.rstrip() + "\n")
    if len(blocks) != 4:
        raise SystemExit(f"F16V expected 4 objects got {len(blocks)}")
    header = (
        "; SPECTER TURKEY FACTION FULL RESET - Turkey_F16V.ini\n"
        "; Full USA F-16C weapon system (no Turkey custom weapons)\n\n"
    )
    return header + "\n".join(blocks)


def retarget_weapon_file(
    text: str,
    known_objects: set[str],
    *,
    mode: str = "turkey_only",
) -> tuple[str, int]:
    """Replace ProjectileObject values for Turkey reset.

    mode:
      - turkey_only: retarget Turkey_* / explicit remap keys only (safe for shared Weapon.ini)
      - turkey_file: full Turkey weapon file retarget including cross-faction→stock maps
      - skip: no-op
    """
    if mode == "skip":
        return text, 0
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    n = 0
    cross_faction = {
        "Ukraine_IRIS_T_Projectile",
        "Ukraine_Grad_Projectile",
        "9M14_AT-3A",
    }

    def repl_block(wname: str, body: str) -> str:
        nonlocal n
        is_turkey_weapon = wname.startswith("Turkey") or "Turkey" in wname

        def repl(m: re.Match[str]) -> str:
            nonlocal n
            prefix, proj = m.group(1), m.group(2)
            if proj in ("None", "NONE"):
                return m.group(0)

            good = WEAPON_PROJECTILE_RETARGET.get(proj)

            if mode == "turkey_only":
                # Shared files: only touch Turkey_* projectiles or Turkey weapon blocks'
                # explicit cross-faction remaps. Never rewrite other factions' missing refs.
                if proj.startswith("Turkey"):
                    if good is None:
                        good = fallback_projectile(proj)
                elif is_turkey_weapon and proj in cross_faction:
                    pass  # keep good from remap table
                elif good and proj.startswith("Turkey"):
                    pass
                else:
                    # Drop non-Turkey remaps (e.g. do not rewrite Ukraine_* in Weapon.ini
                    # unless it is a Turkey weapon using that projectile).
                    if not (is_turkey_weapon and proj in cross_faction and good):
                        return m.group(0)
            else:
                # turkey_file mode
                if good and proj in cross_faction and not is_turkey_weapon:
                    # Shouldn't happen in turkey files, but be safe
                    if not is_turkey_weapon:
                        return m.group(0)
                if good is None and proj.startswith("Turkey"):
                    good = fallback_projectile(proj)
                # Also retarget missing Turkey-named leftovers
                if good is None and is_turkey_weapon and (
                    proj.startswith("Ukraine_")
                    or proj.startswith("Iraq_")
                    or ("Projectile" in proj and proj not in known_objects)
                ):
                    good = fallback_projectile(proj)

            if good and good != proj:
                n += 1
                return f"{prefix}{good}"
            return m.group(0)

        return re.sub(r"(?m)^(\s*ProjectileObject\s*=\s*)(\S+)\s*$", repl, body)

    parts = re.split(r"(?m)(?=^Weapon\s+\S+)", text)
    out: list[str] = []
    for part in parts:
        wm = re.match(r"(?ms)^(Weapon\s+(\S+)\s*\n)(.*)", part)
        if not wm:
            out.append(part)
            continue
        out.append(wm.group(1) + repl_block(wm.group(2), wm.group(3)))
    return "".join(out), n


def remap_models_in_text(text: str, stems: set[str]) -> tuple[str, list[str]]:
    notes: list[str] = []
    out = text
    for bad, good in MODEL_REMAP.items():
        if good.lower() not in stems:
            continue
        pattern = rf"(?m)^(\s*Model\s*=\s*){re.escape(bad)}(\s*(?:;.*)?)$"
        out2, c = re.subn(pattern, rf"\g<1>{good}\g<2>", out)
        if c:
            out = out2
            notes.append(f"{bad}->{good}x{c}")
    # Any remaining Model= that is missing from ART -> AIM-120 / Irq_255mm_Round heuristic
    def model_fix(m: re.Match[str]) -> str:
        prefix, model = m.group(1), m.group(2)
        if model in ("None", "NONE"):
            return m.group(0)
        if model.lower() in stems:
            return m.group(0)
        # choose safe fallback
        fb = "Irq_255mm_Round" if any(k in model.lower() for k in ("shell", "tank", "cannon", "d30", "bm21")) else "AIM-120"
        if "inf" in model.lower() or "irg" in model.lower() or "worker" in model.lower() or "skn" in model.lower():
            fb = "AIRNGR_IDG"
        if "power" in model.lower():
            fb = "US_PowerPlant"
        if "supply" in model.lower():
            fb = "US_Supply"
        if "warfactory" in model.lower() or "armdeal" in model.lower():
            fb = "US_WarFactory"
        if fb.lower() not in stems:
            fb = "AIM-120"
        notes.append(f"{model}->{fb}(auto)")
        return f"{prefix}{fb}"

    out = re.sub(r"(?m)^(\s*Model\s*=\s*)(\S+)", model_fix, out)
    return out, notes


def validate_turkey_all(entries, art_entries) -> tuple[list[str], list[str]]:
    fails: list[str] = []
    warns: list[str] = []
    cats = turkey_wo.catalog(entries)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }

    for n, _ in entries:
        if is_turkey_custom_weapon_file(n):
            fails.append(f"custom Turkey weapon file still present: {n}")

    w2p: dict[str, list[str]] = {}
    for n, r in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = r.decode("utf-8", "replace")
        for m in re.finditer(r"(?ms)^Weapon\s+(\S+)\s*$.*?(?=^Weapon\s|\Z)", t):
            w2p[m.group(1)] = re.findall(
                r"(?m)^\s*ProjectileObject\s*=\s*(\S+)", m.group(0)
            )

    for n, r in entries:
        if not is_turkey_ini(n):
            continue
        bn = Path(n.replace("\\", "/")).name
        t = r.decode("utf-8", "replace")
        if any(ord(c) > 127 for c in t):
            fails.append(f"{bn}: non-ASCII")
        for w in re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", t):
            if w.startswith(";") or w in ("None", "NONE", "End"):
                continue
            if w.startswith("Exclusive") or w == "InitialDelay":
                continue
            if w not in cats["Weapon"]:
                fails.append(f"{bn}: missing Weapon {w}")
                continue
            for p in w2p.get(w, []):
                if p in ("None", "NONE"):
                    continue
                if p not in cats["Object"]:
                    fails.append(f"{bn}: weapon {w} missing ProjectileObject {p}")
                elif p.startswith("Turkey_") and (
                    "Projectile" in p or p.endswith("MissileObject") or p.startswith("Turkey_Fab")
                ):
                    # Should have been retargeted away from deleted custom objects
                    # Allow if object still exists elsewhere (not deleted)
                    pass
        for model in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", t)):
            if model in ("None", "NONE"):
                continue
            if model.lower() not in stems:
                fails.append(f"{bn}: missing W3D Model={model}")
        for m in re.finditer(r"(?m)^\s*BuildVariations\s*=\s*(.+)$", t):
            miss = [v for v in m.group(1).split(";")[0].split() if v not in cats["Object"]]
            if miss:
                fails.append(f"{bn}: missing BV {miss}")
        for fx in set(re.findall(r"(?m)^\s*FXList\s*=\s*(\S+)", t)):
            if fx not in ("None", "NONE") and fx not in cats["FXList"]:
                fails.append(f"{bn}: missing FXList {fx}")
        for ocl in set(re.findall(r"(?m)^\s*(?:FireOCL|OCL)\s*=\s*(\S+)", t)):
            # Generals uses: OCL = FINAL OCL_Name  (token FINAL/INITIAL is a timing keyword)
            if ocl in ("None", "NONE", "FINAL", "INITIAL", "ALL", "MIDPOINT"):
                continue
            if ocl not in cats["OCL"] and ocl not in cats["Object"]:
                warns.append(f"{bn}: possible missing OCL {ocl}")

    objs = cats["Object"]
    for need in (
        "Turkey_F16Block70",
        "Turkey_F16V",
        "Turkey_Kizilelma",
        "Turkey_TB2",
        "Turkey_Akinci",
        "Turkey_Tu-22M3",
    ):
        if need not in objs:
            fails.append(f"missing critical Object {need}")

    # Any ProjectileObject still pointing at missing / deleted Turkey customs
    for w, ps in w2p.items():
        for p in ps:
            if p in ("None", "NONE"):
                continue
            if p not in objs:
                # Only fail when the weapon name is Turkey-related or projectile is Turkey_*
                if w.startswith("Turkey") or "Turkey" in w or p.startswith("Turkey"):
                    fails.append(f"weapon {w} missing ProjectileObject {p}")
            elif p.startswith("Turkey_") and (
                "Projectile" in p
                or p.endswith("MissileObject")
                or p.startswith("Turkey_Fab")
                or "Goktug" in p
                or "SOM" in p
                or "Tayfun" in p
            ):
                fails.append(f"weapon {w} still uses custom Turkey projectile {p}")
    return fails, warns


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing SRC {SRC}")
    entries = base.parse_big(SRC)
    art_entries = base.parse_big(ART)
    stems = {
        Path(n.replace("\\", "/")).stem.lower()
        for n, _ in art_entries
        if n.lower().endswith(".w3d")
    }
    by = {base.knorm(n): (n, r) for n, r in entries}
    cats0 = turkey_wo.catalog(entries)
    known_objects = set(cats0["Object"])

    OUT.mkdir(parents=True, exist_ok=True)
    n_bak = backup_turkey(entries, BACKUP)
    print(f"BACKUP Turkey INIs: {n_bak} -> {BACKUP}")

    for good in set(MODEL_REMAP.values()):
        if good.lower() not in stems:
            print(f"WARNING remap target missing ART: {good}")

    patched: dict[str, bytes] = {}
    notes: list[str] = []

    # --- Aircraft clones ---
    for target, turkey_object, donor_path, donor_object in AIR_MAP:
        if base.knorm(target) not in by:
            raise SystemExit(f"missing target {target}")
        if base.knorm(donor_path) not in by:
            raise SystemExit(f"missing donor {donor_path}")
        t_name, t_raw = by[base.knorm(target)]
        d_name, d_raw = by[base.knorm(donor_path)]
        old_text = t_raw.decode("utf-8", "replace")
        donor_text = d_raw.decode("utf-8", "replace")
        identity = roster.extract_identity(old_text, turkey_object)
        identity.setdefault("display", f"OBJECT:{turkey_object}")
        donor_block = roster.extract_object(donor_text, donor_object)
        fixed = roster.clone_to_turkey(
            donor_block,
            donor_object=donor_object,
            turkey_object=turkey_object,
            identity=identity,
            donor_label=Path(d_name.replace("\\", "/")).name,
        )
        fixed = re.sub(
            r"(?m)^; SPECTER TURKEY AIRCRAFT ROSTER FIX",
            "; SPECTER TURKEY FACTION FULL RESET",
            fixed,
            count=1,
        )
        fixed = ascii_sanitize(fixed)
        patched[base.knorm(target)] = fixed.encode("ascii")
        notes.append(f"AIR {turkey_object} <= {donor_object}")
        print(f"CLONED {turkey_object} from {donor_object}")

    # --- F16V multi-object ---
    f16v = clone_multi_f16v(
        by[base.knorm(F16V_DONOR)][1].decode("utf-8", "replace"),
        by[base.knorm(F16V_PATH)][1].decode("utf-8", "replace"),
    )
    f16v = ascii_sanitize(f16v)
    patched[base.knorm(F16V_PATH)] = f16v.encode("ascii")
    notes.append("AIR Turkey_F16V set <= USA F16CM_BLK50_DB52")
    print("CLONED Turkey_F16V multi-object set from USA F-16")

    # --- Retarget weapon definition files (Turkey-scoped; do not rewrite other factions) ---
    total_retargets = 0
    for name, raw in entries:
        if not is_weapon_definition_file(name):
            continue
        bn = basename(name)
        if bn.startswith("weapon_turkey") or bn.startswith("weapon_phasei_turkey"):
            mode = "turkey_file"
        elif bn in {"weapon.ini", "weapon_verificationfixes.ini"}:
            mode = "turkey_only"
        else:
            # Leave India/Ukraine/etc weapon files completely untouched
            mode = "skip"
        text = raw.decode("utf-8", "replace")
        text2, nfix = retarget_weapon_file(text, known_objects, mode=mode)
        # Only ASCII-sanitize files we actually retarget (avoid touching other factions)
        if mode != "skip":
            text2 = ascii_sanitize(text2)
        if nfix or (mode != "skip" and text2 != text):
            patched[base.knorm(name)] = text2.encode("ascii")
            total_retargets += nfix
            notes.append(f"WEAPON {bn} retargets={nfix}")
            print(f"WEAPON {bn} retargets={nfix}")
    print(f"TOTAL weapon ProjectileObject retargets={total_retargets}")

    # --- Remap models + ASCII sanitize all remaining Turkey INIs ---
    model_files = 0
    for name, raw in entries:
        if not is_turkey_ini(name):
            continue
        if is_turkey_custom_weapon_file(name):
            continue
        kn = base.knorm(name)
        text = patched[kn].decode("ascii") if kn in patched else raw.decode("utf-8", "replace")
        text2, mnotes = remap_models_in_text(text, stems)
        text2 = re.sub(r"(?m)^(\s*Side\s*=\s*)(?!Turkey\b)\S+", r"\1Turkey", text2)
        text2 = ascii_sanitize(text2)
        if mnotes or kn in patched or text2 != text:
            patched[kn] = text2.encode("ascii")
            if mnotes:
                model_files += 1
                notes.append(f"MODEL {basename(name)}: {','.join(mnotes[:8])}")
    print(f"Model remapped files={model_files}")

    # --- Rebuild BIG entries ---
    rebuilt: list[tuple[str, bytes]] = []
    deleted = 0
    for name, raw in entries:
        if is_turkey_custom_weapon_file(name):
            deleted += 1
            print(f"DELETE {name}")
            continue
        kn = base.knorm(name)
        rebuilt.append((name, patched[kn]) if kn in patched else (name, raw))
    print(f"DELETED custom Turkey weapon/projectile files: {deleted}")
    if deleted < 18:
        raise SystemExit(f"expected to delete >=18 custom weapon files, got {deleted}")

    # Sync tree
    for kn, raw in patched.items():
        for name, _ in entries:
            if base.knorm(name) != kn:
                continue
            if is_turkey_ini(name):
                tp = roster.tree_path_for(name)
                tp.parent.mkdir(parents=True, exist_ok=True)
                tp.write_bytes(raw)
            elif is_weapon_definition_file(name):
                # write under patch/Data/INI/<basename>
                dest = ROOT / "Data" / "INI" / Path(name.replace("\\", "/")).name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(raw)
            break
    for name, _ in entries:
        if is_turkey_custom_weapon_file(name):
            tp = roster.tree_path_for(name)
            if tp.is_file():
                tp.unlink()

    counts: dict[str, int] = defaultdict(int)
    for n, _ in rebuilt:
        counts[base.knorm(n)] += 1
    dups = [k for k, v in counts.items() if v > 1]
    if dups:
        raise SystemExit(f"duplicate paths {dups[:10]}")

    failures, warns = validate_turkey_all(rebuilt, art_entries)
    if failures:
        print("PRE-WRITE FAILED")
        for f in failures[:150]:
            print(" ", f)
        return 1
    print(f"PASS pre-write (soft-warns={len(warns)})")

    out_big = OUT / "_SPEC_DATA_ONE.big"
    base.write_big(out_big, rebuilt)
    final_entries = base.parse_big(out_big)
    post, post_warns = validate_turkey_all(final_entries, art_entries)
    if post:
        out_big.unlink(missing_ok=True)
        print("POST-WRITE FAILED")
        for f in post[:150]:
            print(" ", f)
        return 1
    print(f"PASS post-write (soft-warns={len(post_warns)})")

    left = [n for n, _ in final_entries if is_turkey_custom_weapon_file(n)]
    if left:
        raise SystemExit(f"custom weapon files remain: {left}")

    big_sha = base.sha256_file(out_big)
    big_size = out_big.stat().st_size
    (OUT / "RESET_NOTES.txt").write_text(
        "TURKEY FACTION FULL RESET\n"
        "========================\n"
        f"backup_inis={n_bak}\n"
        f"deleted_custom_weapon_files={deleted}\n"
        f"air_clones={len(AIR_MAP)+1}\n"
        f"weapon_projectile_retargets={total_retargets}\n"
        + "\n".join(notes[:300])
        + "\n",
        encoding="ascii",
    )
    verify = (
        "SPECTER TURKEY FACTION FULL RESET - VERIFY REPORT\n"
        "================================================\n"
        "VERDICT: PASS\n"
        "Goal: Turkey faction loads without crash\n"
        "Actions:\n"
        "- Backed up all Turkey INIs\n"
        "- Deleted Turkey Projectiles/WeaponObjects/Shells (no new weapon objects)\n"
        "- Rebuilt F-16/Kizilelma/TB2/AKINCI/Tu-22M3 (+ roster) from USA/China/Russia donors\n"
        "- Retargeted Turkey weapons to existing USA/Russia stock projectiles\n"
        "- Remapped missing W3D models; ASCII-sanitized Turkey INIs\n"
        f"BIG SHA256: {big_sha}\n"
        f"BIG SIZE: {big_size}\n"
        f"Soft warns: {len(post_warns)}\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(verify, encoding="ascii")
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER TURKEY FACTION FULL RESET\n"
        "================================\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n"
        "Turkey aircraft use USA/China/Russia donor systems.\n"
        "Custom Turkey weapon object files were removed.\n"
        "Weapon_Turkey*.ini / Weapon.ini point at stock missiles.\n",
        encoding="ascii",
    )
    (OUT / "TURKEY_SOFT_WARNINGS.txt").write_text(
        "\n".join(post_warns[:500]) + "\n", encoding="ascii", errors="replace"
    )

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in ("VERIFY_REPORT.txt", "README_INSTALL.txt", "RESET_NOTES.txt"):
            shutil.copy2(OUT / name, final_dir / name)

    zip_path = OUT / "_SPEC_DATA_ONE_TURKEY_FACTION_FULL_RESET.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for name in (
            "VERIFY_REPORT.txt",
            "README_INSTALL.txt",
            "RESET_NOTES.txt",
            "TURKEY_SOFT_WARNINGS.txt",
        ):
            zf.write(OUT / name, name)
    zip_sha = base.sha256_file(zip_path)
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"_SPEC_DATA_ONE_TURKEY_FACTION_FULL_RESET.zip SHA256={zip_sha}\n",
        encoding="ascii",
    )
    if final_dir.is_dir():
        shutil.copy2(OUT / "HASHES.txt", final_dir / "HASHES.txt")
    print(f"BIG SHA256={big_sha}")
    print(f"ZIP SHA256={zip_sha}")
    print("FINAL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
