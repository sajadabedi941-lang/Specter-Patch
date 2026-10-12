#!/usr/bin/env python3
"""India A-J gameplay-balance correction: SPECTER-heavy strategic warheads.

Baseline: packed SPECTER_PAKISTAN_AJ_HEAVY (PR #641 on PR #640 / #639).

DATA-only. Factory, builders, buttons, ART, Acc/CHL/range stay frozen.
Pakistan #641 G-J heavies stay frozen. A-E stay light/precision.
F gets a modest cruise-payload review. G-J become heavy strategic options.
Agni-V is a 4000 km / 7000 kg SPECTER endgame, not a 1800 kg real-world cap.

Public payload claims are not used as limits. 10000 kg is the global max,
not a target for every late missile. Iran has no accepted A-J roster.
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
import pack_s_pakistan_aj_heavy as pakh  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_PAKISTAN_AJ_HEAVY/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_PAKISTAN_AJ_HEAVY/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_INDIA_AJ_HEAVY"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "99520c9cd6bf41f65d09ad291f81beff030effc8b7f3f2546f7848816d8f8442"
SIZE_DATA_SRC = 368355036
SHA_ART_SRC = "a7375becdf29e23c8a5e926a3329167561194bfee09dfe4d714ea30573edd24f"
SIZE_ART_SRC = 1782622889

# Acc/CHL/km frozen. A-E payloads frozen. F modest cruise review. G-J heavy.
NEW_STATS = {
    "F": {
        "kg": 650, "rebuild": 40, "price": 3400,
        "role": (
            "Subsonic cruise analogue (Nirbhay; longer than BrahMos, "
            "modest SPECTER payload, lower CHL)"
        ),
    },
    "G": {
        "kg": 2000, "rebuild": 52, "price": 5200,
        "role": (
            "SRBM/MRBM analogue (Agni-I; SPECTER heavy warhead, more precise "
            "and lighter than Pakistan Ghauri 2400 kg)"
        ),
    },
    "H": {
        "kg": 1800, "rebuild": 56, "price": 5800,
        "role": (
            "Canister MRBM analogue (Agni Prime; lighter/more precise than "
            "Agni-I, longer than Shaheen-II)"
        ),
    },
    "I": {
        "kg": 4000, "rebuild": 70, "price": 8600,
        "role": (
            "IRBM analogue (Agni-III; SPECTER heavy regional/strategic, "
            "longer than Ababeel, below Agni-V payload)"
        ),
    },
    "J": {
        "kg": 7000, "rebuild": 92, "price": 10800,
        "role": (
            "ICBM-class analogue at SPECTER 4000 km (Agni-V; SPECTER endgame "
            "payload, not the old 1800 kg real-world-inspired cap)"
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
    if old["slot"] in NEW_STATS:
        raw.update(NEW_STATS[old["slot"]])
    else:
        raw["kg"] = old["kg"]
        raw["rebuild"] = old["rebuild"]
        raw["price"] = old["price"]
        raw["role"] = old["role"]
    return ind.derived(raw)


OLD_DERIVED = list(ind.DERIVED)
NEW_DERIVED = [rebuild_one(m) for m in OLD_DERIVED]
OLD_BY = {m["slot"]: m for m in OLD_DERIVED}
NEW_BY = {m["slot"]: m for m in NEW_DERIVED}
CHANGED = [m for m in NEW_DERIVED if m["slot"] in NEW_STATS]

for _m in NEW_DERIVED:
    assert 1000 <= _m["km"] <= 4000 and 400 <= _m["kg"] <= 10000
    assert _m["acc"] == OLD_BY[_m["slot"]]["acc"]
    assert _m["stealth"] == OLD_BY[_m["slot"]]["stealth"]
    assert _m["km"] == OLD_BY[_m["slot"]]["km"]
    assert _m["object"] == OLD_BY[_m["slot"]]["object"]
assert NEW_BY["J"]["km"] == 4000
assert NEW_BY["H"]["kg"] < NEW_BY["G"]["kg"]
assert NEW_BY["J"]["kg"] < 10000
assert NEW_BY["J"]["kg"] > pakh.NEW_BY["J"]["kg"]


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
    full = ind.weapon_file([m])
    fire = sk.last_block(full, "Weapon", m["weapon"])
    death = sk.last_block(full, "Weapon", m["warhead"])
    if not fire or not death:
        raise SystemExit(f"missing weapon pair for {m['slot']}")
    return fire + "\n\n" + death


def player_tooltip(m: dict) -> str:
    return ind.player_tooltip(m)


def csf_changed() -> dict[str, str]:
    return {
        f"CONTROLBAR:ToolTipIndiaMissile{m['slot']}": player_tooltip(m)
        for m in CHANGED
    }


def mapping_report() -> list[str]:
    lines = [
        "INDIA A-J HEAVY STRATEGIC REBALANCE (DATA only)",
        "",
        "Baseline: PR #641 Pakistan heavy + PR #640 + PR #639.",
        "Unchanged: names, objects, factory, builders, buttons, ART, Acc, CHL, km.",
        "Unchanged: A-E payload / damage / cost / time.",
        "Changed: F modest cruise review; G-J warhead / PD / SD / HACK / cost / time / CSF.",
        "Pakistan #641 G-J frozen. Iran A-J roster absent.",
        "",
        "ENGINE (verified packed, unchanged mapping):",
        "  AttackRange 1720 = 1000 km.",
        "  PrimaryDamage = 2000 * (kg / 400).",
        "  SecondaryDamage = 100 * (kg / 400).",
        "  Death HACK = 2200 * (kg / 400). NOT folded into PrimaryDamage.",
        "  ScatterRadius 175 = Acc 10/100. Dispersion, not hit %.",
        "  Projectile MaxHealth 400 = CHL 5/100. Interceptor toughness, not stealth.",
        "  ClipSize=1 AutoReloadsClip=Yes ClipReloadTime=300000.",
        "",
        "OLD vs NEW (SPECTER game values, not verified specs):",
        "SLOT  NAME         KM   ACC CHL  OLD_KG NEW_KG  OLD_PD   NEW_PD   OLD_SD  NEW_SD  OLD_HACK NEW_HACK OLD$   NEW$   OLDT NEWT",
    ]
    for slot in "ABCDEFGHIJ":
        o, n = OLD_BY[slot], NEW_BY[slot]
        lines.append(
            f"  {slot}    {n['name']:<12} {n['km']:<4} {n['acc']:<3} {n['stealth']:<3} "
            f"{o['kg']:<6} {n['kg']:<6} "
            f"{sk.fmt_stat(o['damage']):<8} {sk.fmt_stat(n['damage']):<8} "
            f"{sk.fmt_stat(o['secondary']):<7} {sk.fmt_stat(n['secondary']):<7} "
            f"{o['death']:<8} {n['death']:<8} "
            f"{o['price']:<6} {n['price']:<6} {o['rebuild']:<4} {n['rebuild']}"
        )
    lines.extend(
        [
            "",
            "COUNTRY BALANCE vs Pakistan #641 (packed inspected, not runtime):",
            "  India J Agni-V 4000 km / 7000 kg Acc 58 $10800 t92.",
            "  Pakistan J Shaheen-III 3000 km / 3600 kg Acc 56 $8600 t80.",
            "    India keeps reach and takes the heavier SPECTER endgame.",
            "  India I Agni-III 3300/4000 Acc 52 vs Pakistan I Ababeel 2500/2800 CHL 58.",
            "    India IRBM reach + payload. Pakistan keeps the CHL outlier.",
            "  India G Agni-I 1900/2000 Acc 50 vs Pakistan G Ghauri 1900/2400 Acc 36.",
            "    Same range band: Pakistan heavier, India more precise.",
            "  India H Agni-P 2500/1800 Acc 68 vs Pakistan H Shaheen-II 2200/2000 Acc 54.",
            "    Pakistan slightly heavier; India longer and more precise.",
            "  A-E stay tactical/precision. F Nirbhay 650 kg cruise, not a BM.",
            "  Libya J 3900/8000 Acc 20. UAE J 4000/7000 Acc 20. Saudi J 4000/4000 Acc 20.",
            "  India J matches UAE-class mass with Acc 58 and 4000 km, at high cost/time.",
            "  Iran has no accepted A-J factory roster; not created or modified.",
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
        sk.CSF_KEY, sk.WEAPON_KEY, ind.IND_WEP_KEY,
        *[NEW_BY[s]["unit_key"] for s in NEW_STATS],
    }
    for key in src_data:
        if key in allowed_data:
            continue
        if data.get(key) != src_data.get(key):
            fails.append(f"DATA mutated {key}")
    for key in data:
        if key not in src_data:
            fails.append(f"DATA added {key}")

    if data[sk.CS_KEY] != src_data[sk.CS_KEY]:
        fails.append("CommandSet.ini mutated")
    if data[sk.CB_KEY] != src_data[sk.CB_KEY]:
        fails.append("CommandButton.ini mutated")
    if data[ind.IND_FAC_KEY] != src_data[ind.IND_FAC_KEY]:
        fails.append("India factory object mutated")
    if data[ind.IND_CB_KEY] != src_data[ind.IND_CB_KEY]:
        fails.append("India buttons mutated")
    if data[ind.IND_CS_KEY] != src_data[ind.IND_CS_KEY]:
        fails.append("India command satellite mutated")
    if data[pakh.pak.PAK_FAC_KEY] != src_data[pakh.pak.PAK_FAC_KEY]:
        fails.append("Pakistan factory mutated")
    if data[pakh.pak.PAK_WEP_KEY] != src_data[pakh.pak.PAK_WEP_KEY]:
        fails.append("Pakistan weapon satellite mutated")

    wep_text = data[sk.WEAPON_KEY].decode("latin1")
    src_wep = src_data[sk.WEAPON_KEY].decode("latin1")
    wep_sat = data[ind.IND_WEP_KEY].decode("latin1")
    if sk.illegal_floats(wep_text) or sk.illegal_floats(wep_sat):
        fails.append(
            f"illegal floats {sk.illegal_floats(wep_text) + sk.illegal_floats(wep_sat)}"
        )

    for slot in "ABCDE":
        o = OLD_BY[slot]
        if sk.last_block(wep_text, "Weapon", o["weapon"]) != sk.last_block(
            src_wep, "Weapon", o["weapon"]
        ):
            fails.append(f"{slot} Weapon.ini fire mutated")
        if data[o["unit_key"]] != src_data[o["unit_key"]]:
            fails.append(f"{slot} unit mutated")
        if data[o["proj_key"]] != src_data[o["proj_key"]]:
            fails.append(f"{slot} projectile mutated")

    for m in pakh.CHANGED:
        if data[m["unit_key"]] != src_data[m["unit_key"]]:
            fails.append(f"Pakistan {m['slot']} unit mutated")
        if sk.last_block(wep_text, "Weapon", m["weapon"]) != sk.last_block(
            src_wep, "Weapon", m["weapon"]
        ):
            fails.append(f"Pakistan {m['slot']} weapon mutated")

    if sk.last_block(wep_text, "Weapon", "Weapon_Pakistan_Shaheen3") != sk.last_block(
        src_wep, "Weapon", "Weapon_Pakistan_Shaheen3"
    ):
        fails.append("Pakistan Shaheen-III weapon mutated")
    if sk.last_block(data[sk.R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB") != (
        sk.last_block(src_data[sk.R11_KEY].decode("latin1"), "Object", "Iraq_R11ScudB")
    ):
        fails.append("9P117 mutated")

    csf = data[sk.CSF_KEY]
    for m in NEW_DERIVED:
        unit = sk.last_block(data[m["unit_key"]].decode("latin1"), "Object", m["object"])
        if sk.field(unit, "BuildCost") != str(m["price"]):
            fails.append(f"{m['slot']} BuildCost")
        if not sk.field(unit, "BuildTime").startswith(f"{m['rebuild']}.0"):
            fails.append(f"{m['slot']} BuildTime")
        if sk.field(unit, "Side") != "India":
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

        btn = sk.last_block(data[sk.CB_KEY].decode("latin1"), "CommandButton", m["button"])
        if sk.field(btn, "Object") != m["object"]:
            fails.append(f"{m['slot']} button object")
        if sk.csf_get(csf, f"CONTROLBAR:IndiaMissile{m['slot']}") != f"{m['slot']} {m['name']}":
            fails.append(f"{m['slot']} CSF name")
        if sk.csf_get(csf, f"CONTROLBAR:ToolTipIndiaMissile{m['slot']}") != player_tooltip(m):
            fails.append(f"{m['slot']} CSF tooltip")

    if NEW_BY["J"]["kg"] <= 1800:
        fails.append("Agni-V still at old 1800 kg")
    if NEW_BY["J"]["kg"] > 10000:
        fails.append("Agni-V over global max")
    if NEW_BY["G"]["kg"] <= OLD_BY["G"]["kg"]:
        fails.append("Agni-I payload not increased")
    if NEW_BY["I"]["kg"] <= OLD_BY["I"]["kg"]:
        fails.append("Agni-III payload not increased")
    return fails


def write_loose() -> None:
    wheel = LOOSE / "Object/Specter/Indian Armed Forces/Wheeled"
    wep = LOOSE / "Weapon/Weapon_India_Missiles.ini"
    for m in CHANGED:
        path = wheel / f"{m['object']}.ini"
        path.write_text(patch_unit_text(path.read_text(encoding="utf-8"), m), encoding="utf-8")
    wep.write_text(ind.weapon_file(NEW_DERIVED), encoding="utf-8")


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_PAKISTAN_AJ_HEAVY")
    if sk.sha256_path(SRC_ART) != SHA_ART_SRC or SRC_ART.stat().st_size != SIZE_ART_SRC:
        raise SystemExit("ART baseline is not SPECTER_PAKISTAN_AJ_HEAVY")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    src_art = sk.parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    for m in CHANGED:
        data[m["unit_key"]] = sk.to_crlf(
            patch_unit_text(src_data[m["unit_key"]].decode("latin1"), m)
        )

    wep = src_data[sk.WEAPON_KEY].decode("latin1")
    sat = src_data[ind.IND_WEP_KEY].decode("latin1")
    for m in CHANGED:
        pair = weapon_pair(m).replace("\r\n", "\n")
        fire = sk.last_block(pair, "Weapon", m["weapon"]).replace("\n", "\r\n")
        death = sk.last_block(pair, "Weapon", m["warhead"]).replace("\n", "\r\n")
        wep = sk.replace_last(wep, "Weapon", m["weapon"], fire)
        wep = sk.replace_last(wep, "Weapon", m["warhead"], death)
        sat = sk.replace_last(sat, "Weapon", m["weapon"], fire)
        sat = sk.replace_last(sat, "Weapon", m["warhead"], death)
    data[sk.WEAPON_KEY] = wep.encode("latin1")
    data[ind.IND_WEP_KEY] = sat.encode("latin1")
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
    (ext / "Weapon.ini.IndiaHeavy.txt").write_text(ind.weapon_file(NEW_DERIVED), encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")
    for m in CHANGED:
        (ext / f"{m['object']}.ini").write_text(
            packed_data[m["unit_key"]].decode("latin1"), encoding="utf-8"
        )

    data_sha = sk.sha256_path(data_path)
    art_sha = sk.sha256_path(art_path)
    zip_path = ROOT / "patch/Release/SPECTER_INDIA_AJ_HEAVY.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)
    if art_sha != SHA_ART_SRC:
        raise SystemExit(f"ART hash drifted {art_sha}")

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #641 s-pakistan-aj-heavy + PR #640 + PR #639",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "ART_UNCHANGED=YES",
        "FACTORY_UNCHANGED=YES",
        "BUTTONS_UNCHANGED=YES",
        "A_E_UNCHANGED=YES",
        "ACC_CHL_KM_UNCHANGED=YES",
        "PAKISTAN_641_UNCHANGED=YES",
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
            "ZIP_FILE=SPECTER_INDIA_AJ_HEAVY.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #641",
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
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-india-aj-heavy/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement (byte-identical to s-pakistan-aj-heavy / s-pakistan-missiles-aj):",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-india-aj-heavy/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-india-aj-heavy/SPECTER_INDIA_AJ_HEAVY.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-india-aj-heavy",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-india-aj-heavy",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "India A-J heavy strategic rebalance. DATA only.\n"
        "Nirbhay 650 kg. Agni-I 2000 kg. Agni-P 1800 kg. Agni-III 4000 kg. Agni-V 7000 kg / 4000 km.\n"
        "A-E, Acc/CHL/range, factory, buttons, ART, and Pakistan #641 unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# India A-J heavy strategic rebalance\n\n"
        "- DATA-only. ART hash identical to s-pakistan-aj-heavy.\n"
        "- Agni-I 900→2000 kg. Agni-P 700→1800 kg. Agni-III 1200→4000 kg. Agni-V 1800→7000 kg.\n"
        "- Nirbhay 550→650 kg cruise review. A-E unchanged.\n"
        "- Acc, CHL, range, factory, buttons, Pakistan #641 unchanged.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "INVENTORY.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")
    (OUT / "CONFLICTS.txt").write_text(
        "Weapon.ini and Weapon\\Weapon_India_Missiles.ini last-win F/G/H/I/J fire/warhead pairs.\n"
        "India_Nirbhay / Agni1 / AgniP / Agni3 / Agni5 BuildCost/BuildTime updated.\n"
        "CSF tooltips for F-J updated to the new packed kg/time/cost.\n"
        "Factory, builders, buttons, ART, A-E, Acc/CHL/km, and Pakistan #641 unchanged.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:70]))


if __name__ == "__main__":
    main()
