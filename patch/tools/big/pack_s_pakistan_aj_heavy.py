#!/usr/bin/env python3
"""Pakistan A-J gameplay-balance correction: heavier late-roster warheads.

Baseline: packed SPECTER_PAKISTAN_MISSILES_AJ (PR #640).

DATA-only. Factory, builders, buttons, ART, Acc/CHL/range, A-F payloads,
India A-J, and every other accepted country stay frozen.

Ghauri / Shaheen-II / Ababeel / Shaheen-III receive SPECTER-heavy payloads
so Pakistan has several late-roster strategic options. Acc and interceptor
toughness are unchanged. Babur and Ra'ad stay precision/CHL cruise analogues.

Public real-world payload claims are not used as caps. Values are game balance.
Iran has no accepted A-J factory roster and is not created here.
"""
from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_sk_missiles_aj as sk  # noqa: E402
import pack_s_india_missiles_aj as ind  # noqa: E402
import pack_s_pakistan_missiles_aj as pak  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_PAKISTAN_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_PAKISTAN_MISSILES_AJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_PAKISTAN_AJ_HEAVY"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_PAK = "0b49d68d484531fe76e9b4b14bd29c054e34ee51472e48f9b7f63efebeb782cb"
SIZE_DATA_PAK = 368354874
SHA_ART_PAK = "a7375becdf29e23c8a5e926a3329167561194bfee09dfe4d714ea30573edd24f"
SIZE_ART_PAK = 1782622889

# SPECTER-heavy late roster. Acc/CHL/km unchanged. A-F unchanged.
NEW_LATE = {
    "G": {
        "kg": 2400, "rebuild": 50, "price": 4600,
        "role": (
            "Liquid MRBM analogue (Ghauri/Hatf-V; SPECTER heavy warhead, "
            "modest Acc vs India Agni-I)"
        ),
    },
    "H": {
        "kg": 2000, "rebuild": 56, "price": 5400,
        "role": (
            "Solid MRBM analogue (Shaheen-II/Hatf-VI; SPECTER heavy regional "
            "strike, more precise than Ghauri)"
        ),
    },
    "I": {
        "kg": 2800, "rebuild": 68, "price": 7200,
        "role": (
            "MIRV-class heavy analogue (Ababeel; developmental/uncertain; "
            "high CHL, not longer-ranged than Shaheen-III)"
        ),
    },
    "J": {
        "kg": 3600, "rebuild": 80, "price": 8600,
        "role": (
            "Long MRBM heavy analogue (Shaheen-III; SPECTER payload above "
            "India Agni-V, range below Agni-V 4000 km cap)"
        ),
    },
}


def rebuild_one(old: dict) -> dict:
    raw = {
        "slot": old["slot"], "object": old["object"], "name": old["name"],
        "model": old["model"], "modeld": old["modeld"], "proj_model": old["proj_model"],
        "hier": old["hier"], "hierd": old["hierd"], "proj_hier": old["proj_hier"],
        "tex": old["tex"], "body": old["body"], "nose": old["nose"],
        "expect": old["expect"], "km": old["km"], "acc": old["acc"],
        "stealth": old["stealth"],
    }
    if old["slot"] in NEW_LATE:
        raw.update(NEW_LATE[old["slot"]])
    else:
        raw["kg"] = old["kg"]
        raw["rebuild"] = old["rebuild"]
        raw["price"] = old["price"]
        raw["role"] = old["role"]
    return pak.derived(raw)


OLD_DERIVED = list(pak.DERIVED)
NEW_DERIVED = [rebuild_one(m) for m in OLD_DERIVED]
OLD_BY = {m["slot"]: m for m in OLD_DERIVED}
NEW_BY = {m["slot"]: m for m in NEW_DERIVED}
CHANGED = [m for m in NEW_DERIVED if m["slot"] in NEW_LATE]

for _m in NEW_DERIVED:
    assert 1000 <= _m["km"] <= 4000 and 400 <= _m["kg"] <= 10000
    assert _m["acc"] == OLD_BY[_m["slot"]]["acc"]
    assert _m["stealth"] == OLD_BY[_m["slot"]]["stealth"]
    assert _m["km"] == OLD_BY[_m["slot"]]["km"]
    assert _m["object"] == OLD_BY[_m["slot"]]["object"]


def patch_unit_text(text: str, m: dict) -> str:
    text = re.sub(r"(BuildCost\s+=\s+)\d+", rf"\g<1>{m['price']}", text, count=1)
    text = re.sub(
        r"(BuildTime\s+=\s+)[\d.]+",
        rf"\g<1>{m['rebuild']}.0",
        text,
        count=1,
    )
    return text


def weapon_pair(m: dict) -> str:
    full = pak.weapon_file([m])
    fire = sk.last_block(full, "Weapon", m["weapon"])
    death = sk.last_block(full, "Weapon", m["warhead"])
    if not fire or not death:
        raise SystemExit(f"missing weapon pair for {m['slot']}")
    return fire + "\r\n\r\n" + death


def player_tooltip(m: dict) -> str:
    return pak.player_tooltip(m)


def csf_changed() -> dict[str, str]:
    mapping = {}
    for m in CHANGED:
        mapping[f"CONTROLBAR:ToolTipPakistanMissile{m['slot']}"] = player_tooltip(m)
    return mapping


def mapping_report() -> list[str]:
    lines = [
        "PAKISTAN A-J HEAVY STRATEGIC REBALANCE (DATA only)",
        "",
        "Unchanged: names, objects, factory, builders, buttons, ART, Acc, CHL, km.",
        "Unchanged: A-F payload / damage / cost / time.",
        "Changed: G-J warhead mass, Primary/Secondary/HACK damage, cost, time, CSF.",
        "",
        "ENGINE (unchanged mapping):",
        "  AttackRange 1720 = 1000 km.",
        "  PrimaryDamage 2000 = 400 kg. Formula: 2000 * (kg / 400).",
        "  SecondaryDamage 100 = 400 kg. Formula: 100 * (kg / 400).",
        "  Death HACK 2200 = 400 kg extra. NOT folded into PrimaryDamage.",
        "  ScatterRadius 175 = Acc 10/100. Dispersion, not hit %.",
        "  Projectile MaxHealth 400 = CHL 5/100. Interceptor toughness, not stealth.",
        "  ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000.",
        "",
        "OLD vs NEW (SPECTER game values, not verified specs):",
        "SLOT  NAME         OLD_KG NEW_KG  OLD_PD  NEW_PD  OLD_SD NEW_SD  OLD$  NEW$  OLDT NEWT  KM   ACC CHL",
    ]
    for slot in "ABCDEFGHIJ":
        o, n = OLD_BY[slot], NEW_BY[slot]
        lines.append(
            f"  {slot}    {n['name']:<12} {o['kg']:<6} {n['kg']:<6} "
            f"{sk.fmt_stat(o['damage']):<7} {sk.fmt_stat(n['damage']):<7} "
            f"{sk.fmt_stat(o['secondary']):<6} {sk.fmt_stat(n['secondary']):<6} "
            f"{o['price']:<5} {n['price']:<5} {o['rebuild']:<4} {n['rebuild']:<4} "
            f"{n['km']:<4} {n['acc']:<3} {n['stealth']}"
        )
    lines.extend(
        [
            "",
            "COUNTRY BALANCE (packed inspected, not runtime):",
            "  India J Agni-V 4000 km / 1800 kg Acc 58 $7200 t75.",
            "  Pakistan J Shaheen-III 3000 km / 3600 kg Acc 56 $8600 t80.",
            "    India keeps reach. Pakistan J is the heavier SPECTER strike.",
            "  India I Agni-III 3300/1200 Acc 52. Pakistan I Ababeel 2500/2800 Acc 46 CHL 58.",
            "    India keeps IRBM reach. Ababeel is the heavier MIRV-class option.",
            "  Ghauri 1900/2400 Acc 36 vs Agni-I 1900/900 Acc 50: heavier, less precise.",
            "  Shaheen-II 2200/2000 Acc 54: heavy regional, not a Ghauri clone.",
            "  Babur/Ra'ad stay 450/400 kg cruise analogues (Acc/CHL, not heavy BM).",
            "  Syria J 2200/1500. SA J 2400/1200. Saudi J 4000/4000. Libya J 3900/8000.",
            "  Iran has no accepted A-J factory roster; not created or modified.",
            "  USA/EU strategic systems remain on other production paths.",
            "",
        ]
    )
    return lines


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

    allowed_data = {
        sk.CSF_KEY, sk.WEAPON_KEY, pak.PAK_WEP_KEY,
        *[NEW_BY[s]["unit_key"] for s in NEW_LATE],
    }
    for key in src_data:
        if key in allowed_data:
            continue
        if data.get(key) != src_data.get(key):
            fails.append(f"DATA mutated {key}")
    for key in data:
        if key not in src_data:
            fails.append(f"DATA added {key}")

    for frozen_cs in (
        "PakistanDozerCommandSet",
        "Pakistan_WorkerCommandSet",
        "Pakistan_VT72BCommandSet",
        "Pakistan_MissileFactoryCommandSet",
        "India_MissileFactoryCommandSet",
        "IndiaDozerCommandSet",
        "SouthAfrica_MissileFactoryCommandSet",
        "Syria_MissileFactoryCommandSet",
        "Libya_MissileFactoryCommandSet",
        "Iraq_AlFahdMissileFactoryCommandSet",
    ):
        _k, new_b = sk.last_block_from_files(order, data, "CommandSet", frozen_cs)
        _o, old_b = sk.last_block_from_files(
            list(src_data), src_data, "CommandSet", frozen_cs
        )
        if new_b != old_b:
            fails.append(f"{frozen_cs} mutated")

    if data[pak.PAK_FAC_KEY] != src_data[pak.PAK_FAC_KEY]:
        fails.append("factory object mutated")
    if data[pak.PAK_CB_KEY] != src_data[pak.PAK_CB_KEY]:
        fails.append("Pakistan buttons mutated")
    if data[pak.PAK_CS_KEY] != src_data[pak.PAK_CS_KEY]:
        fails.append("Pakistan command satellite mutated")
    if data[sk.CS_KEY] != src_data[sk.CS_KEY]:
        fails.append("CommandSet.ini mutated")
    if data[sk.CB_KEY] != src_data[sk.CB_KEY]:
        fails.append("CommandButton.ini mutated")

    wep_text = data[sk.WEAPON_KEY].decode("latin1")
    src_wep = src_data[sk.WEAPON_KEY].decode("latin1")
    wep_sat = data[pak.PAK_WEP_KEY].decode("latin1")
    if sk.illegal_floats(wep_text) or sk.illegal_floats(wep_sat):
        fails.append(f"illegal floats {sk.illegal_floats(wep_text) + sk.illegal_floats(wep_sat)}")

    for slot in "ABCDEF":
        o = OLD_BY[slot]
        if sk.last_block(wep_text, "Weapon", o["weapon"]) != sk.last_block(
            src_wep, "Weapon", o["weapon"]
        ):
            fails.append(f"{slot} Weapon.ini fire mutated")
        if data[o["unit_key"]] != src_data[o["unit_key"]]:
            fails.append(f"{slot} unit mutated")
        if data[o["proj_key"]] != src_data[o["proj_key"]]:
            fails.append(f"{slot} projectile mutated")

    if sk.last_block(wep_text, "Weapon", "Weapon_India_Prahaar") != sk.last_block(
        src_wep, "Weapon", "Weapon_India_Prahaar"
    ):
        fails.append("India Prahaar weapon mutated")
    if sk.last_block(wep_text, "Weapon", "Weapon_India_Agni5") != sk.last_block(
        src_wep, "Weapon", "Weapon_India_Agni5"
    ):
        fails.append("India Agni-V weapon mutated")
    if sk.last_block(data[sk.R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB") != (
        sk.last_block(src_data[sk.R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB")
    ):
        fails.append("9P117 mutated")

    fac = sk.last_block(
        data[pak.PAK_FAC_KEY].decode("latin1"), "Object", "Pakistan_MissileFactory"
    )
    if sk.field(fac, "CommandSet") != "Pakistan_MissileFactoryCommandSet":
        fails.append("factory CommandSet")

    csf = data[sk.CSF_KEY]
    for m in NEW_DERIVED:
        unit = sk.last_block(data[m["unit_key"]].decode("latin1"), "Object", m["object"])
        if sk.field(unit, "BuildCost") != str(m["price"]):
            fails.append(f"{m['slot']} BuildCost")
        if not sk.field(unit, "BuildTime").startswith(f"{m['rebuild']}.0"):
            fails.append(f"{m['slot']} BuildTime")
        if sk.field(unit, "Side") != "Pakistan":
            fails.append(f"{m['slot']} Side")
        if m["weapon"] not in unit:
            fails.append(f"{m['slot']} weapon bind")
        if "Rearm" in unit or "RiderChangeContain" in unit:
            fails.append(f"{m['slot']} rearm")

        proj = sk.last_block(data[m["proj_key"]].decode("latin1"), "Object", m["projectile"])
        if sk.field(proj, "MaxHealth") != sk.fmt_stat(m["hp"]):
            fails.append(f"{m['slot']} HP")
        if sk.field(proj, "RadarPriority"):
            fails.append(f"{m['slot']} RadarPriority")
        if data[m["proj_key"]] != src_data[m["proj_key"]]:
            fails.append(f"{m['slot']} projectile file changed")

        for blob, label in (
            (sk.last_block(wep_text, "Weapon", m["weapon"]), "Weapon.ini"),
            (sk.last_block(wep_sat, "Weapon", m["weapon"]), "sat"),
        ):
            if sk.field(blob, "AttackRange") != sk.fmt_stat(m["range"]):
                fails.append(f"{m['slot']} {label} range")
            if sk.field(blob, "PrimaryDamage") != sk.fmt_stat(m["damage"]):
                fails.append(f"{m['slot']} {label} PD")
            if sk.field(blob, "SecondaryDamage") != sk.fmt_stat(m["secondary"]):
                fails.append(f"{m['slot']} {label} SD")
            if sk.field(blob, "ScatterRadius") != sk.fmt_stat(m["scatter"]):
                fails.append(f"{m['slot']} {label} scatter")
            if sk.field(blob, "ClipSize") != "1" or sk.field(blob, "AutoReloadsClip") != "Yes":
                fails.append(f"{m['slot']} {label} clip")
            if sk.field(blob, "ClipReloadTime") != "300000":
                fails.append(f"{m['slot']} {label} reload")
            if sk.field(blob, "ProjectileObject") != m["projectile"]:
                fails.append(f"{m['slot']} {label} projectile")
            if sk.field(blob, "WeaponSpeed") != "280":
                fails.append(f"{m['slot']} {label} speed")
        death = sk.last_block(wep_sat, "Weapon", m["warhead"])
        if sk.field(death, "DamageType") != "HACK":
            fails.append(f"{m['slot']} death type")
        if sk.field(death, "PrimaryDamage") != str(m["death"]):
            fails.append(f"{m['slot']} death PD")
        fire = sk.last_block(wep_text, "Weapon", m["weapon"])
        if "HACK" in fire:
            fails.append(f"{m['slot']} HACK folded into PRIMARY")

        btn = sk.last_block(
            data[sk.CB_KEY].decode("latin1"), "CommandButton", m["button"]
        )
        if sk.field(btn, "Object") != m["object"]:
            fails.append(f"{m['slot']} button object")
        if sk.field(btn, "ButtonImage") != m["cameo"]:
            fails.append(f"{m['slot']} button image")
        if sk.csf_get(csf, f"CONTROLBAR:PakistanMissile{m['slot']}") != f"{m['slot']} {m['name']}":
            fails.append(f"{m['slot']} CSF name")
        if sk.csf_get(csf, f"CONTROLBAR:ToolTipPakistanMissile{m['slot']}") != player_tooltip(m):
            fails.append(f"{m['slot']} CSF tooltip")

    if NEW_BY["J"]["kg"] <= OLD_BY["J"]["kg"]:
        fails.append("J payload not increased")
    if NEW_BY["G"]["kg"] <= OLD_BY["G"]["kg"]:
        fails.append("G payload not increased")
    if NEW_BY["I"]["kg"] <= NEW_BY["H"]["kg"] and NEW_BY["I"]["kg"] <= NEW_BY["G"]["kg"]:
        fails.append("I not a distinct heavy option")
    if len({NEW_BY[s]["kg"] for s in "GHIJ"}) < 4:
        fails.append("late payloads not differentiated")
    if NEW_BY["J"]["km"] >= 4000:
        fails.append("J must stay below India Agni-V range cap")
    return fails


def write_loose() -> None:
    wheel = LOOSE / "Object/Specter/Pakistan Armed Forces/Wheeled"
    wep = LOOSE / "Weapon/Weapon_Pakistan_Missiles.ini"
    for m in CHANGED:
        path = wheel / f"{m['object']}.ini"
        path.write_text(patch_unit_text(path.read_text(encoding="utf-8"), m), encoding="utf-8")
    wep.write_text(pak.weapon_file(NEW_DERIVED), encoding="utf-8")


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_PAK or SRC_DATA.stat().st_size != SIZE_DATA_PAK:
        raise SystemExit("DATA baseline is not SPECTER_PAKISTAN_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_PAK or SRC_ART.stat().st_size != SIZE_ART_PAK:
        raise SystemExit("ART baseline is not SPECTER_PAKISTAN_MISSILES_AJ")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art = sk.parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    for m in CHANGED:
        data[m["unit_key"]] = sk.to_crlf(
            patch_unit_text(src_data[m["unit_key"]].decode("latin1"), m)
        )

    wep = src_data[sk.WEAPON_KEY].decode("latin1")
    sat = src_data[pak.PAK_WEP_KEY].decode("latin1")
    for m in CHANGED:
        pair = weapon_pair(m).replace("\r\n", "\n")
        fire = sk.last_block(pair, "Weapon", m["weapon"]).replace("\n", "\r\n")
        death = sk.last_block(pair, "Weapon", m["warhead"]).replace("\n", "\r\n")
        wep = sk.replace_last(wep, "Weapon", m["weapon"], fire)
        wep = sk.replace_last(wep, "Weapon", m["warhead"], death)
        sat = sk.replace_last(sat, "Weapon", m["weapon"], fire)
        sat = sk.replace_last(sat, "Weapon", m["warhead"], death)
    data[sk.WEAPON_KEY] = wep.encode("latin1")
    data[pak.PAK_WEP_KEY] = sat.encode("latin1")
    data[sk.CSF_KEY] = sk.csf_upsert(src_data[sk.CSF_KEY], csf_changed())

    write_loose()

    data_big = sk.build_big(data)
    art_big = SRC_ART.read_bytes()
    packed_data, order = sk.parse_big_ordered(data_big)
    packed_art = sk.parse_big(art_big)
    fails = validate(packed_data, packed_art, src_data, src_art, order)
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))
    fails.extend(f"ART {x}" for x in sk.big_structure_ok(art_big))
    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_big)
    art_path.write_bytes(art_big)

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "Weapon.ini.PakistanHeavy.txt").write_text(pak.weapon_file(NEW_DERIVED), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")
    for m in CHANGED:
        (ext / f"{m['object']}.ini").write_text(
            packed_data[m["unit_key"]].decode("latin1"), encoding="utf-8"
        )

    data_sha = sk.sha256_path(data_path)
    art_sha = sk.sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_PAKISTAN_AJ_HEAVY.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)

    if art_sha != SHA_ART_PAK:
        raise SystemExit(f"ART hash drifted {art_sha}")

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #640 s-pakistan-missiles-aj",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "ART_UNCHANGED=YES",
        "FACTORY_UNCHANGED=YES",
        "BUTTONS_UNCHANGED=YES",
        "A_F_UNCHANGED=YES",
        "ACC_CHL_KM_UNCHANGED=YES",
        "INDIA_AJ_UNCHANGED=YES",
        "IRAN_ROSTER_ABSENT=YES",
        "NO_REARM=YES",
        "NO_RADARPRIORITY=YES",
        "",
        *map_lines,
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
            "ZIP_FILE=SPECTER_PAKISTAN_AJ_HEAVY.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #640",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-pakistan-aj-heavy/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement (byte-identical to s-pakistan-missiles-aj):",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-pakistan-aj-heavy/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-pakistan-aj-heavy/SPECTER_PAKISTAN_AJ_HEAVY.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-pakistan-aj-heavy",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-pakistan-aj-heavy",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Pakistan A-J heavy strategic rebalance. DATA only.\n"
        "Ghauri 2400 kg, Shaheen-II 2000 kg, Ababeel 2800 kg, Shaheen-III 3600 kg.\n"
        "A-F, Acc/CHL/range, factory, buttons, and ART unchanged.\n"
        "India A-J and all other accepted countries unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Pakistan A-J heavy strategic rebalance\n\n"
        "- DATA-only. ART hash identical to s-pakistan-missiles-aj.\n"
        "- Ghauri 1200→2400 kg. Shaheen-II 850→2000 kg. Ababeel 800→2800 kg. Shaheen-III 1100→3600 kg.\n"
        "- Primary/Secondary/HACK damage and CSF tooltips follow the accepted 400 kg scale.\n"
        "- Acc, CHL, range, factory, buttons, A-F, India A-J unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")
    (OUT / "CONFLICTS.txt").write_text(
        "Weapon.ini and Weapon\\Weapon_Pakistan_Missiles.ini last-win G-J fire/warhead pairs.\n"
        "Pakistan_Ghauri / Shaheen2 / AbabeelMRV / Shaheen3 BuildCost/BuildTime updated.\n"
        "CSF tooltips for G-J updated to the new packed kg/PD/SD/time/cost.\n"
        "Factory, builders, buttons, ART, A-F, Acc/CHL/km, India, and other countries unchanged.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:60]))


if __name__ == "__main__":
    main()
