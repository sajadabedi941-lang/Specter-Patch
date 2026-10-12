#!/usr/bin/env python3
"""UAE + Japan A-J accuracy / radar-stealth description correction.

Baseline: packed SPECTER_SAUDI_ACC_DESC (PR #644 on #643).

Packed last-wins already implement the accepted PR #634 / #630 ratings:
  ScatterRadius = 175 * (10 / Acc)           impact dispersion, not a hit %
  MaxHealth     = 400 * (CHL / 5)            interceptor toughness, not radar stealth
  PrimaryDamage / SecondaryDamage / death HACK follow 2000/100/2200 * (kg/400)

Player CSF captions/tooltips omitted Acc and Radar-Stealth (name/range/kg/time/price
only). This packer upserts those strings. Warhead/damage audit found no mismatch.

Weapon, projectile, warhead, object, command-set, button-image, range, mass,
damage, reload, cost, build time, and ART are unchanged.
Saudi #644 CSF stays frozen. No RadarPriority. No speed change.
"""
from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_sk_missiles_aj as sk  # noqa: E402
import pack_s_uae_missiles_aj as uae  # noqa: E402
import pack_s_japan_missiles_aj as jpn  # noqa: E402
import pack_s_saudi_acc_desc as sad  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_SAUDI_ACC_DESC/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_SAUDI_ACC_DESC/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_UAE_JAPAN_ACC_DESC"

SHA_DATA_SRC = "1133213de66987f5a48a0f9e6341c6f5254a279fbc305d358b7fc227b37070a4"
SIZE_DATA_SRC = 368528717
SHA_ART_SRC = "3c3872d21e09ad3f71960c11f88f0187ed21a9ff1942664e74846070bd2485bb"
SIZE_ART_SRC = 1830385382

UAE_EXPECTED = {
    "A": {"acc": 60, "chl": 30, "km": 1000, "kg": 400, "name": "Falcon"},
    "B": {"acc": 45, "chl": 40, "km": 1100, "kg": 800, "name": "Barq"},
    "C": {"acc": 75, "chl": 25, "km": 1300, "kg": 600, "name": "Liwa"},
    "D": {"acc": 35, "chl": 55, "km": 1500, "kg": 1500, "name": "Dhafra"},
    "E": {"acc": 65, "chl": 35, "km": 1800, "kg": 1200, "name": "Al Ain"},
    "F": {"acc": 30, "chl": 50, "km": 2100, "kg": 2500, "name": "Buraq"},
    "G": {"acc": 50, "chl": 70, "km": 2400, "kg": 1800, "name": "Siraj"},
    "H": {"acc": 25, "chl": 45, "km": 2800, "kg": 3500, "name": "Mezyad"},
    "I": {"acc": 70, "chl": 55, "km": 3400, "kg": 5000, "name": "Qamar"},
    "J": {"acc": 20, "chl": 30, "km": 4000, "kg": 7000, "name": "Al Watan"},
}

JPN_EXPECTED = {
    "A": {"acc": 85, "chl": 25, "km": 1000, "kg": 400, "name": "Type 12 Kai"},
    "B": {"acc": 70, "chl": 35, "km": 1100, "kg": 400, "name": "Type 88 Kai"},
    "C": {"acc": 45, "chl": 70, "km": 1400, "kg": 600, "name": "Kōryū"},
    "D": {"acc": 35, "chl": 45, "km": 2000, "kg": 1200, "name": "Raijin"},
    "E": {"acc": 80, "chl": 55, "km": 2200, "kg": 800, "name": "Hayate"},
    "F": {"acc": 25, "chl": 30, "km": 2800, "kg": 2500, "name": "Yamato"},
    "G": {"acc": 15, "chl": 20, "km": 3200, "kg": 3500, "name": "Kurogane"},
    "H": {"acc": 75, "chl": 40, "km": 1200, "kg": 400, "name": "Shiden"},
    "I": {"acc": 40, "chl": 65, "km": 1800, "kg": 1000, "name": "Fūjin"},
    "J": {"acc": 20, "chl": 25, "km": 3600, "kg": 4000, "name": "Tenrai"},
}

COUNTRIES = (
    ("UAE", uae.DERIVED, UAE_EXPECTED, "UAE", uae.UAE_WEP_KEY),
    ("Japan", jpn.DERIVED, JPN_EXPECTED, "Japan", jpn.NEW_WEP_KEY),
)


def player_tooltip(m: dict) -> str:
    return (
        f"{m['slot']} {m['name']}\n"
        f"Range: {m['km']} km\n"
        f"Warhead: {m['kg']} kg\n"
        f"Accuracy: {m['acc']}/100\n"
        f"Radar Stealth: {m['stealth']}/100\n"
        f"Accuracy is impact scatter, not a hit %.\n"
        f"Radar Stealth is a rating for interceptor toughness, not stealth "
        f"and not a penetration %.\n"
        f"Build Time: {m['rebuild']} sec\n"
        f"Price: ${m['price']}"
    )


def csf_map() -> dict[str, str]:
    mapping = {}
    for _country, missiles, _exp, prefix, _wep in COUNTRIES:
        for m in missiles:
            mapping[f"CONTROLBAR:{prefix}Missile{m['slot']}"] = f"{m['slot']} {m['name']}"
            mapping[f"CONTROLBAR:ToolTip{prefix}Missile{m['slot']}"] = player_tooltip(m)
    return mapping


def mapping_report() -> list[str]:
    lines = [
        "UAE + JAPAN A-J ACCURACY / RADAR-STEALTH DESCRIPTION CORRECTION",
        "",
        "Baseline packed last-wins: SPECTER_SAUDI_ACC_DESC (PR #644 on #643).",
        "Accepted ratings: UAE PR #634, Japan PR #630. Reused, not redesigned.",
        "Problem: CSF tooltips showed name/range/kg/time/price only. Acc/CHL omitted.",
        "Warhead audit: all 20 packed PD/SD/HACK values already match 2000/100/2200*(kg/400).",
        "No warhead or gameplay field was changed.",
        "",
        "ENGINE IMPLEMENTATION (unchanged from packed last-wins):",
        "  Accuracy rating -> ScatterRadius = 175 * (10 / Acc).",
        "    SAGE ScatterRadius is impact dispersion around the aimed point.",
        "    It is not a hit-chance percentage. No Accuracy=N% field exists.",
        "  Radar-Stealth rating -> projectile MaxHealth = 400 * (CHL / 5).",
        "    SPECTER interceptors with AntiProjectile / AntiBallisticMissile deal",
        "    damage to KindOf PROJECTILE BALLISTIC_MISSILE bodies. Higher MaxHealth",
        "    takes more interceptor hits to destroy. This is intercept toughness,",
        "    not radar stealth, not an evade-percentage, and not RadarPriority.",
        "    SAGE has no RadarStealth field. The tooltip label is the design rating.",
        "  WeaponSpeed remains 280. ClipReloadTime remains 300000.",
        "",
        "CTRY  SLOT NAME            KM   KG   ACC  CHL  SCATTER  HP     PD      SD     HACK  TIP",
    ]
    for country, missiles, _exp, _prefix, _wep in COUNTRIES:
        for m in missiles:
            lines.append(
                f"  {country:<4} {m['slot']}    {m['name']:<14} {m['km']:<4} {m['kg']:<4} "
                f"{m['acc']:<4} {m['stealth']:<4} {sk.fmt_stat(m['scatter']):<7} {sk.fmt_stat(m['hp']):<6} "
                f"{sk.fmt_stat(m['damage']):<7} {sk.fmt_stat(m['secondary']):<6} {m['death']:<5} "
                f"CSF_UPDATED"
            )
    return lines


def check_missile(fails, country, m, exp, prefix, wep_sat, wep_ini, csf, src_csf, cb_text, data):
    if m["acc"] != exp["acc"] or m["stealth"] != exp["chl"]:
        fails.append(f"{country} {m['slot']} rating mismatch packer vs table")
    if m["km"] != exp["km"] or m["kg"] != exp["kg"] or m["name"] != exp["name"]:
        fails.append(f"{country} {m['slot']} identity mismatch vs accepted table")

    w = sk.last_block(wep_sat, "Weapon", m["weapon"]) or sk.last_block(wep_ini, "Weapon", m["weapon"])
    death = sk.last_block(wep_sat, "Weapon", m["warhead"]) or sk.last_block(wep_ini, "Weapon", m["warhead"])
    if sk.field(w, "ScatterRadius") != sk.fmt_stat(m["scatter"]):
        fails.append(f"{country} {m['slot']} scatter changed")
    if sk.field(w, "AttackRange") != sk.fmt_stat(m["range"]):
        fails.append(f"{country} {m['slot']} range changed")
    if sk.field(w, "PrimaryDamage") != sk.fmt_stat(m["damage"]):
        fails.append(f"{country} {m['slot']} PD changed")
    if sk.field(w, "SecondaryDamage") != sk.fmt_stat(m["secondary"]):
        fails.append(f"{country} {m['slot']} SD changed")
    if sk.field(w, "ClipReloadTime") != "300000":
        fails.append(f"{country} {m['slot']} reload changed")
    if sk.field(w, "WeaponSpeed") != "280":
        fails.append(f"{country} {m['slot']} speed changed")
    if "RadarPriority" in w:
        fails.append(f"{country} {m['slot']} weapon RadarPriority")
    if "HACK" in w:
        fails.append(f"{country} {m['slot']} HACK folded into PRIMARY")
    if sk.field(death, "DamageType") != "HACK":
        fails.append(f"{country} {m['slot']} death type")
    if sk.field(death, "PrimaryDamage") != str(m["death"]):
        fails.append(f"{country} {m['slot']} death PD")

    proj = sk.last_block(data[m["proj_key"]].decode("latin1"), "Object", m["projectile"])
    if sk.field(proj, "MaxHealth") != sk.fmt_stat(m["hp"]):
        fails.append(f"{country} {m['slot']} HP changed")
    if sk.field(proj, "RadarPriority"):
        fails.append(f"{country} {m['slot']} projectile RadarPriority")

    caption = f"{m['slot']} {m['name']}"
    tip = player_tooltip(m)
    if sk.csf_get(csf, f"CONTROLBAR:{prefix}Missile{m['slot']}") != caption:
        fails.append(f"{country} {m['slot']} CSF caption")
    got = sk.csf_get(csf, f"CONTROLBAR:ToolTip{prefix}Missile{m['slot']}")
    if got != tip:
        fails.append(f"{country} {m['slot']} CSF tooltip {got!r}")
    if f"{m['km']} km" not in (got or ""):
        fails.append(f"{country} {m['slot']} tooltip missing range")
    if f"{m['kg']} kg" not in (got or ""):
        fails.append(f"{country} {m['slot']} tooltip missing mass")
    if f"Accuracy: {m['acc']}/100" not in (got or ""):
        fails.append(f"{country} {m['slot']} tooltip missing acc")
    if f"Radar Stealth: {m['stealth']}/100" not in (got or ""):
        fails.append(f"{country} {m['slot']} tooltip missing radar stealth")
    if "not a hit %" not in (got or ""):
        fails.append(f"{country} {m['slot']} tooltip missing acc caveat")
    if "not stealth" not in (got or ""):
        fails.append(f"{country} {m['slot']} tooltip missing stealth caveat")
    if sk.csf_get(src_csf, f"CONTROLBAR:ToolTip{prefix}Missile{m['slot']}") == got:
        fails.append(f"{country} {m['slot']} tooltip unchanged from baseline")

    bblock = sk.last_block(cb_text, "CommandButton", m["button"])
    if sk.field(bblock, "ButtonImage") != m["cameo"]:
        fails.append(f"{country} {m['slot']} button image")
    if sk.field(bblock, "Object") != m["object"]:
        fails.append(f"{country} {m['slot']} button object")
    if sk.field(bblock, "DescriptLabel") != f"CONTROLBAR:ToolTip{prefix}Missile{m['slot']}":
        fails.append(f"{country} {m['slot']} DescriptLabel")
    if sk.field(bblock, "TextLabel") != f"CONTROLBAR:{prefix}Missile{m['slot']}":
        fails.append(f"{country} {m['slot']} TextLabel")
    if len(tip) > 400:
        fails.append(f"{country} {m['slot']} tooltip long {len(tip)}")


def validate(data, art, src_data, src_art, order) -> list[str]:
    fails: list[str] = []
    if art != src_art:
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
    wep_ini = data[sk.WEAPON_KEY].decode("latin1")
    cb_text = data[sk.CB_KEY].decode("latin1")
    if data[sk.WEAPON_KEY] != src_data[sk.WEAPON_KEY]:
        fails.append("Weapon.ini mutated")
    if data[sk.CS_KEY] != src_data[sk.CS_KEY]:
        fails.append("CommandSet.ini mutated")
    if data[sk.CB_KEY] != src_data[sk.CB_KEY]:
        fails.append("CommandButton.ini mutated")

    for frozen_cs in (
        "UAE_MissileFactoryCommandSet",
        "Japan_MissileFactoryCommandSet",
        "SaudiArabia_MissileFactoryCommandSet",
        "NorthKorea_MissileFactoryCommandSet",
        "India_MissileFactoryCommandSet",
        "Iraq_AlFahdMissileFactoryCommandSet",
    ):
        new_b = sk.last_block(data[sk.CS_KEY].decode("latin1"), "CommandSet", frozen_cs)
        old_b = sk.last_block(src_data[sk.CS_KEY].decode("latin1"), "CommandSet", frozen_cs)
        if new_b != old_b:
            fails.append(f"{frozen_cs} mutated")

    for country, missiles, expected, prefix, wep_key in COUNTRIES:
        wep_sat = data[wep_key].decode("latin1")
        if wep_sat != src_data[wep_key].decode("latin1"):
            fails.append(f"{country} weapon satellite mutated")
        for m in missiles:
            check_missile(
                fails, country, m, expected[m["slot"]], prefix,
                wep_sat, wep_ini, csf, src_csf, cb_text, data,
            )

    for key, label in (
        ("CONTROLBAR:ToolTipSaudiArabiaMissileA", "Saudi A"),
        ("CONTROLBAR:ToolTipSaudiArabiaMissileJ", "Saudi J"),
        ("CONTROLBAR:ToolTipNorthKoreaMissileA", "NK A"),
        ("CONTROLBAR:ToolTipIndiaMissileJ", "India J"),
        ("CONTROLBAR:ToolTipPakistanMissileJ", "Pakistan J"),
        ("CONTROLBAR:ToolTipLibyaMissileA", "Libya A"),
        ("CONTROLBAR:ToolTipSouthKoreaMissileA", "SK A"),
        ("CONTROLBAR:ToolTipVietnamMissileA", "Vietnam A"),
        ("CONTROLBAR:ToolTipSyriaMissileA", "Syria A"),
    ):
        if sk.csf_get(csf, key) != sk.csf_get(src_csf, key):
            fails.append(f"{label} CSF mutated")

    saudi_a = sk.csf_get(csf, "CONTROLBAR:ToolTipSaudiArabiaMissileA")
    if not saudi_a or "Accuracy: 55/100" not in saudi_a:
        fails.append("Saudi A Acc tooltip lost")
    return fails


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_SAUDI_ACC_DESC")
    if sk.sha256_path(SRC_ART) != SHA_ART_SRC or SRC_ART.stat().st_size != SIZE_ART_SRC:
        raise SystemExit("ART baseline is not SPECTER_SAUDI_ACC_DESC")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art_bytes = SRC_ART.read_bytes()
    src_art = sk.parse_big(src_art_bytes)
    data = dict(src_data)
    data[sk.CSF_KEY] = sk.csf_upsert(src_data[sk.CSF_KEY], csf_map())

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
    for country, missiles, _exp, prefix, _wep in COUNTRIES:
        tips.append(f"===== {country} =====")
        for m in missiles:
            tips.append(f"CONTROLBAR:{prefix}Missile{m['slot']}={m['slot']} {m['name']}")
            tips.append(f"CONTROLBAR:ToolTip{prefix}Missile{m['slot']}=")
            tips.append(player_tooltip(m))
            tips.append("")
    (ext / "UAE_JAPAN_TOOLTIPS.txt").write_text("\n".join(tips), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    data_sha = sk.sha256_path(data_path)
    art_sha = sk.sha256_path(art_path)
    if art_sha != SHA_ART_SRC:
        raise SystemExit("ART copy is not byte-identical to SPECTER_SAUDI_ACC_DESC ART")
    zip_path = ROOT / "patch/Release/SPECTER_UAE_JAPAN_ACC_DESC.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #644 s-saudi-aj-acc-desc + PR #643 + #642 + #634 + #630",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "ART_UNCHANGED=YES",
        "WEAPONS_UNCHANGED=YES",
        "PROJECTILES_UNCHANGED=YES",
        "WARHEAD_DAMAGE_UNCHANGED=YES",
        "SCATTER_UNCHANGED=YES",
        "MAXHEALTH_UNCHANGED=YES",
        "NO_RADARPRIORITY=YES",
        "NO_SPEED_CHANGE=YES",
        "CSF_TOOLTIPS_UPDATED=YES",
        "SAUDI_AJ_ACC_DESC_KEPT=YES",
        "NORTHKOREA_AJ_UNCHANGED=YES",
        "INDIA_AJ_HEAVY_UNCHANGED=YES",
        "PAKISTAN_AJ_HEAVY_UNCHANGED=YES",
        "IRAQ_AM_UNCHANGED=YES",
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
            "ZIP_FILE=SPECTER_UAE_JAPAN_ACC_DESC.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #644",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-uae-japan-aj-acc-desc/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement (unchanged from s-saudi-aj-acc-desc / s-northkorea-missiles-aj):",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-uae-japan-aj-acc-desc/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-uae-japan-aj-acc-desc/SPECTER_UAE_JAPAN_ACC_DESC.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-uae-japan-aj-acc-desc",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-uae-japan-aj-acc-desc",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "UAE + Japan A-J accuracy and radar-stealth description correction.\n"
        "ScatterRadius, MaxHealth, and warhead damage from PR #634 / #630 are unchanged.\n"
        "Player tooltips now show Acc/100 and Radar Stealth/100 as design indexes\n"
        "with explicit caveats. ART is byte-identical to s-saudi-aj-acc-desc.\n"
        "Saudi #644 descriptions are preserved. Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# UAE + Japan A-J accuracy / radar-stealth descriptions\n\n"
        "- Packed ScatterRadius, MaxHealth, and warhead damage from PR #634 / #630 are unchanged.\n"
        "- Accuracy rating maps to ScatterRadius (impact dispersion, not a hit %).\n"
        "- Radar Stealth rating maps to projectile MaxHealth (interceptor toughness, not stealth).\n"
        "- Production button captions and tooltips now include letter, range, mass, Acc/100, and Radar Stealth/100 with caveats.\n"
        "- Warhead audit: all 20 missiles already matched 2000/100/2200 * (kg/400). No damage edits.\n"
        "- ART unchanged. Saudi #644 CSF kept. No RadarPriority. No speed change.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "Only Data\\English\\generals.csf UAE and Japan missile caption/tooltip labels changed.\n"
        "Weapon satellites, factory command sets, objects, warheads, and ART are unchanged.\n"
        "Saudi #644, North Korea, India, Pakistan, Libya, SK, Vietnam, Syria, Iraq, and 9P117 stay frozen.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:60]))


if __name__ == "__main__":
    main()
