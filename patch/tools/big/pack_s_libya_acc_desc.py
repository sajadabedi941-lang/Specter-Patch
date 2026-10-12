#!/usr/bin/env python3
"""Libya A-J accuracy / radar-evasion description correction on PR #635.

Gameplay fields already packed in s-libya-missiles-aj are preserved:
  ScatterRadius = 175 * (10 / Acc)           impact dispersion, not a hit %
  MaxHealth     = 400 * (CHL / 5)            interceptor toughness, not radar stealth

This packer updates player-visible CSF button captions and tooltips only.
Weapon, projectile, warhead, object, command-set, button-image, range, mass,
damage, reload, cost, build time, and ART are unchanged.
No RadarPriority. No speed change. No other countries.
"""
from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_sk_missiles_aj as sk  # noqa: E402
import pack_s_libya_missiles_aj as lby  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_LIBYA_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_LIBYA_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_LIBYA_ACC_DESC"

SHA_DATA_LBY = "c2e30f89c7ab543a99436f000d1a9cb033341f24bababfde6d847baa26b76b10"
SIZE_DATA_LBY = 367678570
SHA_ART_LBY = "52701d0c089144a4201cdb8946fc8f70f5e5b0a42b45f051c8dca1938ca3fa79"
SIZE_ART_LBY = 1591573341

EXPECTED = {
    "A": {"acc": 55, "chl": 35, "km": 1000, "kg": 400, "name": "Fajr"},
    "B": {"acc": 45, "chl": 30, "km": 1100, "kg": 700, "name": "Sahra"},
    "C": {"acc": 75, "chl": 25, "km": 1250, "kg": 500, "name": "Waha"},
    "D": {"acc": 35, "chl": 50, "km": 1450, "kg": 1400, "name": "Jamahiriya"},
    "E": {"acc": 65, "chl": 40, "km": 1700, "kg": 1100, "name": "Murzuq"},
    "F": {"acc": 30, "chl": 45, "km": 2000, "kg": 2200, "name": "Akhdar"},
    "G": {"acc": 50, "chl": 70, "km": 2300, "kg": 1800, "name": "Sirt"},
    "H": {"acc": 25, "chl": 40, "km": 2700, "kg": 3200, "name": "Fezzan"},
    "I": {"acc": 70, "chl": 55, "km": 3300, "kg": 5500, "name": "Orouba"},
    "J": {"acc": 20, "chl": 30, "km": 3900, "kg": 8000, "name": "Great Man-Made River"},
}


def mapping_report() -> list[str]:
    lines = [
        "ENGINE IMPLEMENTATION (unchanged from PR #635 packed last-wins):",
        "  Accuracy rating -> ScatterRadius = 175 * (10 / Acc).",
        "    SAGE ScatterRadius is impact dispersion around the aimed point.",
        "    It is not a hit-chance percentage. No Accuracy=N% field exists.",
        "  Radar-evasion rating -> projectile MaxHealth = 400 * (CHL / 5).",
        "    SPECTER interceptors with AntiProjectile / AntiBallisticMissile deal",
        "    damage to KindOf PROJECTILE BALLISTIC_MISSILE bodies. Higher MaxHealth",
        "    takes more interceptor hits to destroy. This is intercept toughness,",
        "    not radar stealth, not an evade-percentage, and not RadarPriority.",
        "  WeaponSpeed remains 280 on every Libya A-J PRIMARY weapon.",
        "  No RadarPriority on projectiles.",
        "",
        "SLOT  NAME                    KM   KG   ACC  CHL  SCATTER  HP     ENGINE ACC           ENGINE EVADE",
    ]
    for m in lby.DERIVED:
        lines.append(
            f"  {m['slot']}    {m['name']:<22} {m['km']:<4} {m['kg']:<4} "
            f"{m['acc']:<4} {m['stealth']:<4} {sk.fmt_stat(m['scatter']):<7} {sk.fmt_stat(m['hp']):<6} "
            f"ScatterRadius         MaxHealth"
        )
    return lines


def validate(data, art, src_data, src_art, order) -> list[str]:
    fails: list[str] = []
    if art != src_art:
        # Compare key-by-key for a useful message.
        only_new = set(art) - set(src_art)
        only_old = set(src_art) - set(art)
        changed = [k for k in art if k in src_art and art[k] != src_art[k]]
        if only_new:
            fails.append(f"ART added {list(only_new)[:5]}")
        if only_old:
            fails.append(f"ART removed {list(only_old)[:5]}")
        if changed:
            fails.append(f"ART mutated {changed[:5]}")

    for key in data:
        if key == sk.CSF_KEY:
            continue
        if data.get(key) != src_data.get(key):
            fails.append(f"DATA mutated {key}")
    for key in src_data:
        if key == sk.CSF_KEY:
            continue
        if key not in data:
            fails.append(f"DATA dropped {key}")

    csf = data[sk.CSF_KEY]
    src_csf = src_data[sk.CSF_KEY]
    wep_sat = data[lby.LBY_WEP_KEY].decode("latin1")
    src_wep_sat = src_data[lby.LBY_WEP_KEY].decode("latin1")
    if wep_sat != src_wep_sat:
        fails.append("Libya weapon satellite mutated")

    for frozen_cs in (
        "UAE_MissileFactoryCommandSet",
        "SaudiArabia_MissileFactoryCommandSet",
        "Libya_MissileFactoryCommandSet",
        "LibyaDozerCommandSet",
    ):
        new_b = sk.last_block(data[sk.CS_KEY].decode("latin1"), "CommandSet", frozen_cs)
        old_b = sk.last_block(src_data[sk.CS_KEY].decode("latin1"), "CommandSet", frozen_cs)
        if new_b != old_b:
            fails.append(f"{frozen_cs} mutated")

    for m in lby.DERIVED:
        exp = EXPECTED[m["slot"]]
        if m["acc"] != exp["acc"] or m["stealth"] != exp["chl"]:
            fails.append(f"{m['slot']} rating mismatch packer vs table")
        if m["km"] != exp["km"] or m["kg"] != exp["kg"] or m["name"] != exp["name"]:
            fails.append(f"{m['slot']} identity mismatch vs accepted table")

        w = sk.last_block(wep_sat, "Weapon", m["weapon"])
        if sk.field(w, "ScatterRadius") != sk.fmt_stat(m["scatter"]):
            fails.append(f"{m['slot']} scatter changed")
        if sk.field(w, "AttackRange") != sk.fmt_stat(m["range"]):
            fails.append(f"{m['slot']} range changed")
        if sk.field(w, "PrimaryDamage") != sk.fmt_stat(m["damage"]):
            fails.append(f"{m['slot']} PD changed")
        if sk.field(w, "SecondaryDamage") != sk.fmt_stat(m["secondary"]):
            fails.append(f"{m['slot']} SD changed")
        if sk.field(w, "ClipReloadTime") != "300000":
            fails.append(f"{m['slot']} reload changed")
        if sk.field(w, "WeaponSpeed") != "280":
            fails.append(f"{m['slot']} speed changed")
        if "RadarPriority" in w:
            fails.append(f"{m['slot']} weapon RadarPriority")

        proj = sk.last_block(data[m["proj_key"]].decode("latin1"), "Object", m["projectile"])
        if sk.field(proj, "MaxHealth") != sk.fmt_stat(m["hp"]):
            fails.append(f"{m['slot']} HP changed")
        if sk.field(proj, "RadarPriority"):
            fails.append(f"{m['slot']} projectile RadarPriority")

        caption = f"{m['slot']} {m['name']}"
        tip = lby.player_tooltip(m)
        if sk.csf_get(csf, f"CONTROLBAR:LibyaMissile{m['slot']}") != caption:
            fails.append(f"{m['slot']} CSF caption")
        got = sk.csf_get(csf, f"CONTROLBAR:ToolTipLibyaMissile{m['slot']}")
        if got != tip:
            fails.append(f"{m['slot']} CSF tooltip {got!r}")
        if f"{m['km']} km" not in (got or ""):
            fails.append(f"{m['slot']} tooltip missing range")
        if f"{m['kg']} kg" not in (got or ""):
            fails.append(f"{m['slot']} tooltip missing mass")
        if f"{m['acc']}/100" not in (got or ""):
            fails.append(f"{m['slot']} tooltip missing acc")
        if f"{m['stealth']}/100" not in (got or ""):
            fails.append(f"{m['slot']} tooltip missing chl")
        if "hit %" in (got or "").lower() and "not a hit" not in (got or "").lower():
            fails.append(f"{m['slot']} tooltip claims hit %")
        if "stealth" in (got or "").lower() and "not stealth" not in (got or "").lower():
            fails.append(f"{m['slot']} tooltip claims stealth")
        if sk.csf_get(src_csf, f"CONTROLBAR:ToolTipLibyaMissile{m['slot']}") == got:
            fails.append(f"{m['slot']} tooltip unchanged from baseline")

        bblock = sk.last_block(data[sk.CB_KEY].decode("latin1"), "CommandButton", m["button"])
        if sk.field(bblock, "ButtonImage") != m["cameo"]:
            fails.append(f"{m['slot']} button image")
        if sk.field(bblock, "Object") != m["object"]:
            fails.append(f"{m['slot']} button object")

        if len(tip) > 400:
            fails.append(f"{m['slot']} tooltip long {len(tip)}")

    # Other-country CSF captions stay put.
    if sk.csf_get(csf, "CONTROLBAR:UAEMissileA") != sk.csf_get(src_csf, "CONTROLBAR:UAEMissileA"):
        fails.append("UAE A CSF mutated")
    if sk.csf_get(csf, "CONTROLBAR:SaudiArabiaMissileA") != sk.csf_get(
        src_csf, "CONTROLBAR:SaudiArabiaMissileA"
    ):
        fails.append("Saudi A CSF mutated")
    return fails


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_LBY or SRC_DATA.stat().st_size != SIZE_DATA_LBY:
        raise SystemExit("DATA baseline is not SPECTER_LIBYA_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_LBY or SRC_ART.stat().st_size != SIZE_ART_LBY:
        raise SystemExit("ART baseline is not SPECTER_LIBYA_MISSILES_AJ")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art_bytes = SRC_ART.read_bytes()
    src_art = sk.parse_big(src_art_bytes)
    data = dict(src_data)
    data[sk.CSF_KEY] = sk.csf_upsert(src_data[sk.CSF_KEY], lby.csf_map())

    data_big = sk.build_big(data)
    packed_data, order = sk.parse_big_ordered(data_big)
    packed_art = sk.parse_big(src_art_bytes)
    fails = validate(packed_data, packed_art, src_data, src_art, order)
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))
    fails.extend(f"ART {x}" for x in sk.big_structure_ok(src_art_bytes))
    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_big)
    shutil.copyfile(SRC_ART, art_path)

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    tips = []
    for m in lby.DERIVED:
        tips.append(f"CONTROLBAR:LibyaMissile{m['slot']}={m['slot']} {m['name']}")
        tips.append(f"CONTROLBAR:ToolTipLibyaMissile{m['slot']}=")
        tips.append(lby.player_tooltip(m))
        tips.append("")
    (ext / "LIBYA_TOOLTIPS.txt").write_text("\n".join(tips), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    data_sha = sk.sha256_path(data_path)
    art_sha = sk.sha256_path(art_path)
    if art_sha != SHA_ART_LBY:
        raise SystemExit("ART copy is not byte-identical to PR #635 ART")
    zip_path = ROOT / "patch/Release/SPECTER_LIBYA_ACC_DESC.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #635 s-libya-missiles-aj",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "ART_UNCHANGED=YES",
        "WEAPONS_UNCHANGED=YES",
        "PROJECTILES_UNCHANGED=YES",
        "SCATTER_UNCHANGED=YES",
        "MAXHEALTH_UNCHANGED=YES",
        "NO_RADARPRIORITY=YES",
        "NO_SPEED_CHANGE=YES",
        "CSF_TOOLTIPS_UPDATED=YES",
        "",
        *map_lines,
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    hashes = "\n".join(
        [
            "DATA_CHANGED=YES",
            "ART_CHANGED=NO",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_SIZE={art_path.stat().st_size}",
            f"ART_SHA256={art_sha}",
            "ZIP_FILE=SPECTER_LIBYA_ACC_DESC.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #635",
            "STATIC_VALIDATION=PASS",
            "RUNTIME_TEST=NOT RUN",
            "",
        ]
    )
    (OUT / "HASHES.txt").write_text(hashes)
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA replacement:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-libya-aj-acc-desc/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement (unchanged from s-libya-missiles-aj):",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-libya-aj-acc-desc/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-libya-aj-acc-desc/SPECTER_LIBYA_ACC_DESC.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-libya-aj-acc-desc",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-libya-aj-acc-desc",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Libya A-J accuracy and radar-evasion description correction.\n"
        "ScatterRadius and projectile MaxHealth from PR #635 are unchanged.\n"
        "Player tooltips now show Acc/100 and radar-evasion/100 as design indexes\n"
        "with explicit caveats. ART is byte-identical to s-libya-missiles-aj.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Libya A-J accuracy / radar-evasion descriptions\n\n"
        "- Packed ScatterRadius and projectile MaxHealth from PR #635 are unchanged.\n"
        "- Accuracy rating maps to ScatterRadius (impact dispersion, not a hit %).\n"
        "- Radar-evasion rating maps to projectile MaxHealth (interceptor toughness, not stealth).\n"
        "- Production button captions and tooltips now include letter, range, mass, Acc/100, and CHL/100 with caveats.\n"
        "- ART unchanged. No RadarPriority. No speed change. Other countries unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "Only Data\\English\\generals.csf Libya missile caption/tooltip labels changed.\n"
        "Weapon_Libya_Missiles.ini, factory command sets, objects, and ART are unchanged.\n"
        "UAE, Saudi, Japan, SK, Vietnam, Iraq, and 9P117 packed definitions are unchanged.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:40]))


if __name__ == "__main__":
    main()
