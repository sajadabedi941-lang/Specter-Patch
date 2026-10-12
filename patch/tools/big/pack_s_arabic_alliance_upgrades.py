#!/usr/bin/env python3
"""Unlock existing Arabic Alliance upgrades for testing (PR stacked on #653).

Arabic Alliance is packed FactionGLA (CSF INI:FactionGLA). Egypt and UAE stay
separate PlayerTemplates. This pack does not create a country or faction.

Baseline: packed SPECTER_IRAN_US_ISRAEL_MISSILES_AJ (PR #653).

Changes (AA only):
  - Drop SCIENCE_Rank2/3 from Command_Arb_Tier1 / Command_Arb_Tier3.
  - Expose Tier1/2/3 together on Industry Planet T/T1/T2 CommandSets.
  - Drop SCIENCE_Rank* from AA/GLA-only sciences (not EmergencyRepair*).
  - Put Rank3/Rank8 AA general-power purchase buttons on Rank1 commandset.
  - Last-win missing CommandSet GLAWorkerCommandSet (dozer already names it).
  - Strip SCIENCE_RankN from AA-folder unit Prerequisites (keep science-named
    locks: ScudLauncher / MarauderTank / AlgeriaAirForce / ArabDrones).

ART is copied unchanged from #653. No new faction, dozer, factory, or unit.
"""
from __future__ import annotations

import gzip
import hashlib
import re
import shutil
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_IRAN_US_ISRAEL_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAN_US_ISRAEL_MISSILES_AJ/_SPEC_ART_ONE.big"
SRC_ART_GZ = ROOT / "patch/Release/SPECTER_IRAN_US_ISRAEL_MISSILES_AJ/_SPEC_ART_ONE.big.gz"
OUT = ROOT / "patch/Release/SPECTER_ARABIC_ALLIANCE_UPGRADES"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "99a695f81c5adfa5d412f397d1df2951c40bfe7ebfbb7c26f3633cb5e67d6695"
SIZE_DATA_SRC = 370725498
SHA_ART_SRC = "de0e998813bb7f74ff634c4a5aefb901692334e1e0d2a52637d3699b1d8f1f8a"
SIZE_ART_SRC = 2451295403
SHA_ART_GZ_SRC = "c759a09f94ac407337691ec8cd86dbdc85bc3d6a00cd1766e55bf21b67d8bfaf"

CB_KEY = r"Data\INI\CommandButton_ArabicAllianceUnlock.ini"
CS_KEY = r"Data\INI\CommandSet_ArabicAllianceUnlock.ini"
SCI_KEY = r"Data\INI\Science_ArabicAllianceUnlock.ini"

AA_RANK_KEYS = [
    r"Data\INI\Object\Specter\Arabic Alliance\AirDefense\Arb_30N6E.ini",
    r"Data\INI\Object\Specter\Arabic Alliance\AirDefense\Arb_S300.ini",
    r"Data\INI\Object\Specter\Arabic Alliance\AirDefense\Tor1M.ini",
    r"Data\INI\Object\Specter\Arabic Alliance\Airforce\Su24MR.ini",
    r"Data\INI\Object\Specter\Arabic Alliance\Tracked\M109A6.ini",
    r"Data\INI\Object\Specter\Arabic Alliance\Wheeled\Arb_9K729M.ini",
    r"Data\INI\Object\Specter\Arabic Alliance\Wheeled\Arb_9K729M_AI.ini",
    r"Data\INI\Object\Specter\Arabic Alliance\Wheeled\Arb_9K729MV.ini",
]

FROZEN_KEYS = [
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\PlayerTemplate_SpecterPatch.ini",
    r"Data\INI\Upgrade.ini",
    r"Data\INI\Upgrade_Egypt.ini",
    r"Data\INI\Upgrade_UAE.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\Science.ini",
]


def last_block(text: str, kind: str, name: str) -> str:
    ms = list(
        re.finditer(
            rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?(?:^End|^END)\s*$",
            text,
        )
    )
    return ms[-1].group(0) if ms else ""


def last_from(order, files, kind, name):
    found = ("", "")
    needle = f"{kind} {name}".encode("ascii")
    for key in order:
        blob = files[key]
        if needle not in blob:
            continue
        try:
            text = blob.decode("latin1")
        except Exception:
            continue
        block = last_block(text, kind, name)
        if block:
            found = (key, block)
    return found


def field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block or "", re.M)
    return m.group(1).strip() if m else ""


def strip_rank_prereqs(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        block = m.group(0)
        return re.sub(
            r"(?m)^[ \t]*Science[ \t]*=[ \t]*SCIENCE_Rank\d+[^\n]*\r?\n",
            "",
            block,
        )

    return re.sub(r"(?ms)^  Prerequisites\r?\n.*?^  End", repl, text)


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_SRC:
        raise SystemExit("baseline DATA hash mismatch")
    if SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("baseline DATA size mismatch")
    if sk.sha256_path(SRC_ART) != SHA_ART_SRC:
        raise SystemExit("baseline ART hash mismatch")
    if SRC_ART.stat().st_size != SIZE_ART_SRC:
        raise SystemExit("baseline ART size mismatch")

    raw = SRC_DATA.read_bytes()
    files, order = sk.parse_big_ordered(raw)
    original = {k: files[k] for k in files}

    overlays = {
        CB_KEY: sk.to_crlf( (LOOSE / "CommandButton_ArabicAllianceUnlock.ini").read_text(encoding="latin1") ),
        CS_KEY: sk.to_crlf( (LOOSE / "CommandSet_ArabicAllianceUnlock.ini").read_text(encoding="latin1") ),
        SCI_KEY: sk.to_crlf( (LOOSE / "Science_ArabicAllianceUnlock.ini").read_text(encoding="latin1") ),
    }
    for key, blob in overlays.items():
        files[key] = blob
        if key not in order:
            order.append(key)

    stripped = []
    for key in AA_RANK_KEYS:
        if key not in files:
            raise SystemExit(f"missing AA object {key}")
        text = files[key].decode("latin1")
        new = strip_rank_prereqs(text)
        if new == text:
            raise SystemExit(f"no SCIENCE_Rank strip in {key}")
        if re.search(r"Science\s*=\s*SCIENCE_Rank", new):
            raise SystemExit(f"SCIENCE_Rank remains in {key}")
        files[key] = new.encode("latin1")
        stripped.append(key)

    # Frozen baseline files must stay byte-identical.
    for key in FROZEN_KEYS:
        if files[key] != original[key]:
            raise SystemExit(f"frozen key mutated: {key}")

    data_big = sk.build_big(files)
    fails = sk.big_structure_ok(data_big)
    if fails:
        raise SystemExit("big_structure_ok: " + "; ".join(fails))

    packed, packed_order = sk.parse_big_ordered(data_big)

    def req(kind, name, pred, msg):
        src, blk = last_from(packed_order, packed, kind, name)
        if not blk:
            raise SystemExit(f"missing last-wins {kind} {name}")
        if not pred(src, blk):
            raise SystemExit(f"{msg}: {kind} {name} from {src}\n{blk}")
        return src, blk

    req(
        "CommandButton",
        "Command_Arb_Tier1",
        lambda s, b: s == CB_KEY and "Science" not in b and "Upgrade_Arb_Tier1" in b,
        "Tier1 still rank-locked",
    )
    req(
        "CommandButton",
        "Command_Arb_Tier3",
        lambda s, b: s == CB_KEY and "Science" not in b and "Upgrade_Arb_Tier3" in b,
        "Tier3 still rank-locked",
    )
    req(
        "CommandSet",
        "SCIENCE_GLA_CommandSetRank1",
        lambda s, b: s == CS_KEY
        and "Command_PurchaseScienceArabicParaDrop" in b
        and "Command_PurchaseScienceArabDrones" in b
        and "Command_PurchaseScienceAnthraxBomb" in b,
        "Rank1 CS missing AA powers",
    )
    req(
        "CommandSet",
        "ArabicIndustryPlanetCommandSet_T",
        lambda s, b: s == CS_KEY
        and "Command_Arb_Tier1" in b
        and "Command_Arb_Tier2" in b
        and "Command_Arb_Tier3" in b,
        "Industry T missing a tier button",
    )
    req(
        "CommandSet",
        "GLAWorkerCommandSet",
        lambda s, b: s == CS_KEY and "Command_ConstructArabicArmy_IndustryPlanet" in b,
        "worker CS missing Industry Planet",
    )
    req(
        "Science",
        "SCIENCE_ArabicParadrop",
        lambda s, b: s == SCI_KEY and "SCIENCE_Rank" not in b and "SCIENCE_GLA" in field(b, "PrerequisiteSciences"),
        "Paradrop still rank-locked",
    )
    req(
        "Science",
        "SCIENCE_Arabic155mm2",
        lambda s, b: s == SCI_KEY and "SCIENCE_Rank" not in b and "SCIENCE_Arabic155mm1" in field(b, "PrerequisiteSciences"),
        "155mm2 chain/rank wrong",
    )
    req(
        "Science",
        "SCIENCE_AnthraxBomb",
        lambda s, b: s == SCI_KEY and "SCIENCE_Rank" not in b,
        "AnthraxBomb still rank-locked",
    )
    req(
        "Science",
        "SCIENCE_EmergencyRepair1",
        lambda s, b: s.endswith("Science.ini") and "SCIENCE_Rank3" in field(b, "PrerequisiteSciences"),
        "EmergencyRepair1 must stay shared/rank-locked",
    )
    src, blk = last_from(packed_order, packed, "PlayerTemplate", "FactionGLA")
    if src != r"Data\INI\PlayerTemplate.ini":
        raise SystemExit(f"FactionGLA last-wins moved to {src}")
    if field(blk, "Side") != "GLA" or field(blk, "StartingBuilding") != "GLACommandCenter":
        raise SystemExit("FactionGLA identity changed")
    if last_from(packed_order, packed, "PlayerTemplate", "FactionArabicAlliance")[1]:
        raise SystemExit("created FactionArabicAlliance")
    if last_from(packed_order, packed, "PlayerTemplate", "FactionAlgeria")[1]:
        raise SystemExit("created FactionAlgeria")
    src_eg, eg = last_from(packed_order, packed, "PlayerTemplate", "FactionEgypt")
    src_uae, uae = last_from(packed_order, packed, "PlayerTemplate", "FactionUAE")
    if field(eg, "Side") != "Egypt" or field(uae, "Side") != "UAE":
        raise SystemExit("Egypt/UAE identity changed")
    if packed[r"Data\INI\PlayerTemplate.ini"] != original[r"Data\INI\PlayerTemplate.ini"]:
        raise SystemExit("PlayerTemplate.ini mutated")
    if packed[r"Data\INI\Upgrade.ini"] != original[r"Data\INI\Upgrade.ini"]:
        raise SystemExit("Upgrade.ini mutated")

    # No SCIENCE_Rank left on the patched AA objects.
    for key in AA_RANK_KEYS:
        text = packed[key].decode("latin1")
        if re.search(r"Science\s*=\s*SCIENCE_Rank", text):
            raise SystemExit(f"packed {key} still has SCIENCE_Rank")
    m1 = packed[r"Data\INI\Object\Specter\Arabic Alliance\Tracked\M1A2SA.ini"]
    if m1 != original[r"Data\INI\Object\Specter\Arabic Alliance\Tracked\M1A2SA.ini"]:
        raise SystemExit("M1A2SA (SCIENCE_MarauderTank) must stay frozen")
    khalid = packed[r"Data\INI\Object\Specter\Arabic Alliance\Wheeled\Arab_Khalid.ini"]
    if khalid != original[r"Data\INI\Object\Specter\Arabic Alliance\Wheeled\Arab_Khalid.ini"]:
        raise SystemExit("Arab_Khalid (SCIENCE_ScudLauncher) must stay frozen")
    su30 = packed[r"Data\INI\Object\Specter\Arabic Alliance\Airforce\Su30MKA.ini"]
    if su30 != original[r"Data\INI\Object\Specter\Arabic Alliance\Airforce\Su30MKA.ini"]:
        raise SystemExit("Su30MKA (SCIENCE_AlegeriaAirForce) must stay frozen")
    ch4 = packed[r"Data\INI\Object\Specter\Arabic Alliance\UAV\CH4B.ini"]
    if ch4 != original[r"Data\INI\Object\Specter\Arabic Alliance\UAV\CH4B.ini"]:
        raise SystemExit("CH4B (SCIENCE_ArabDrones) must stay frozen")

    # Only new overlay keys + AA rank object keys may differ.
    allowed = set(overlays) | set(AA_RANK_KEYS)
    changed = []
    for key in original:
        if key in allowed:
            if key in original and packed.get(key) != original[key]:
                changed.append(key)
            continue
        if packed.get(key) != original[key]:
            raise SystemExit(f"unrelated key changed: {key}")
    for key in packed:
        if key not in original and key not in overlays:
            raise SystemExit(f"unexpected new key: {key}")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_big)
    shutil.copy2(SRC_ART, art_path)
    art_gz_path = OUT / "_SPEC_ART_ONE.big.gz"
    shutil.copy2(SRC_ART_GZ, art_gz_path)

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "CommandButton_ArabicAllianceUnlock.ini").write_bytes(overlays[CB_KEY])
    (ext / "CommandSet_ArabicAllianceUnlock.ini").write_bytes(overlays[CS_KEY])
    (ext / "Science_ArabicAllianceUnlock.ini").write_bytes(overlays[SCI_KEY])
    for key in AA_RANK_KEYS:
        dest = ext / Path(key.replace("\\", "/")).name
        dest.write_bytes(packed[key])

    data_sha = sk.sha256_path(data_path)
    art_sha = sk.sha256_path(art_path)
    art_gz_sha = sk.sha256_path(art_gz_path)
    if art_sha != SHA_ART_SRC:
        raise SystemExit("copied ART hash mismatch")
    if art_gz_sha != SHA_ART_GZ_SRC:
        raise SystemExit("copied ART.gz hash mismatch")

    zip_path = ROOT / "patch/Release/SPECTER_ARABIC_ALLIANCE_UPGRADES.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)
    tag = "s-arabic-alliance-upgrades"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/"
        + tag
    )

    unlocked = [
        "Upgrade_Arb_Tier1 (PLAYER_UPGRADE; Rank2 removed; Industry Planet T/T1/T2)",
        "Upgrade_Arb_Tier2 (already had no rank; now on Industry Planet T/T1 as well as T1)",
        "Upgrade_Arb_Tier3 (PLAYER_UPGRADE; Rank3 removed; Industry Planet T/T1/T2)",
        "Upgrade_EgyptArmy (already on GLACommandCenter; Science commented; unchanged)",
        "Upgrade_GLAFortifiedStructure (Industry Planet / Palace; no rank; unchanged)",
        "Upgrade_GLACamouflage (Industry Planet / Palace; no rank; unchanged)",
        "Upgrade_GLAToxinShells (GLAPalaceCommandSet; no rank; unchanged)",
        "Upgrade_GLAAnthraxBeta (GLAPalaceCommandSet; no rank; unchanged)",
        "Upgrade_MTS (Industry Planet / Palace; aircraft TriggeredBy; no rank; unchanged)",
        "Upgrade_NuclearReactor (Industry Planet / Palace; no rank; unchanged)",
        "Upgrade_AmericaCountermeasures (ArabicAirfieldCommandSet_T*; no rank; unchanged)",
        "Upgrade_GLAInfantryRebelBoobyTrapAttack (GLABarracksCommandSet; no rank; unchanged)",
        "Upgrade_InfantryCaptureBuilding (GLABarracksCommandSet; no rank; unchanged)",
        "Upgrade_AmericaRadar (granted by ArabicArmy59N6E GrantUpgradeCreate; unchanged)",
        "Upgrade_Rearm_Arab_Khalid (existing Khalid rearm; unchanged)",
        "SCIENCE_ArabicAWACS (Rank dropped; Rank1 purchase row)",
        "SCIENCE_ArabicParadrop (Rank3 dropped; moved to Rank1 row)",
        "SCIENCE_ArabicAroumredParadrop (Rank3 dropped; moved to Rank1 row)",
        "SCIENCE_ArabDrones (Rank3 dropped; moved to Rank1 row; CH4B still requires this science)",
        "SCIENCE_Arabic155mm1/2/3 (Rank3 dropped; 1-2-3 chain kept; Rank1 row)",
        "SCIENCE_AlegeriaAirForce (already Rank1; Su30MKA still requires this science)",
        "SCIENCE_ScudLauncher (already Rank1; Arab_Khalid still requires this science)",
        "SCIENCE_MarauderTank (already Rank1; GLATankMarauder still requires this science)",
        "SCIENCE_RebelAmbush1/2/3 (Rank3 dropped; 1-2-3 chain kept; Rank1 row)",
        "SCIENCE_AnthraxBomb (Rank5 dropped; Rank1 row)",
        "SCIENCE_GPSScrambler (Rank5 dropped; Rank1 row)",
    ]
    remaining = [
        "SCIENCE_EmergencyRepair1/2/3: shared with USA/China; still SCIENCE_Rank3. Changing it would unlock other factions.",
        "SCIENCE_ArabicAWACSSCAN: definition unlocked (Rank dropped) but no PURCHASE_SCIENCE button exists; likely AWACS scan mode, not a separately purchasable upgrade.",
        "Upgrade_AmericaCompositeArmor / Upgrade_AmericaAdvancedTraining / Upgrade_AmericaChemicalSuits: AA units TriggeredBy them, but no AA CommandSet carries the purchase buttons (America Strategy Center path). Not fabricating AA buttons.",
        "Upgrade_Kab-2500: Arab_Su-24MK TriggeredBy it; Command_UpgradeKab-2500 exists but is not on any Arabic Alliance CommandSet. Not adding a cosmetic button.",
        "Upgrade_Egypt_* and Upgrade_UAE_*: packed as FactionEgypt / FactionUAE, not FactionGLA (Arabic Alliance). Not wired onto AA.",
        "Upgrade_ChaffUpgrade: cost 0 auto/object upgrade, not a player purchase.",
        "Upgrade_AADS_AA_Mode / Upgrade_AADS_ABM_Mode: object-mode toggles on S-300, not player research.",
        "Upgrade_ICBM_BoosterKiller: granted by radar GrantUpgradeCreate, not purchased.",
    ]
    unit_rank = [
        "Arb_30N6E / Arabic_S300PMU2: SCIENCE_Rank4 stripped (keep building CS unlock via Tier2/3)",
        "Arab_Tor1M: SCIENCE_Rank5 stripped; still requires GLAPalace + ArabicArmy_IndustryPlanet",
        "ArabicArmy_Su-24MR: SCIENCE_Rank6 stripped",
        "GLAVehicleRocketBuggy (M109A6): SCIENCE_Rank3 stripped; still requires GLAPalace + Industry Planet",
        "Arb_9K720SV1 / Arb_9K720M_AI / GLAVehicleScudLauncher: SCIENCE_Rank6 stripped; still require GLAPalace + Industry Planet",
    ]

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #653 s-iran-us-israel-missiles-aj",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        f"ART_GZ_SIZE={art_gz_path.stat().st_size}",
        f"ART_GZ_SHA256={art_gz_sha}",
        "ART_CHANGED=NO",
        "FACTION_CREATED=NO",
        "FACTIONGLA_REMAINS_ARABIC_ALLIANCE=YES",
        "EGYPT_UAE_UNCHANGED=YES",
        "OTHER_FACTIONS_UNCHANGED=YES",
        f"OVERLAY_KEYS={CB_KEY} | {CS_KEY} | {SCI_KEY}",
        f"AA_OBJECT_RANK_STRIP={len(stripped)}",
        "GLAWORKERCOMMANDSET_LASTWINS=YES",
        "",
        "UNLOCKED:",
        *[f"  - {x}" for x in unlocked],
        "",
        "UNIT_SCIENCE_RANK_STRIPPED (production access after existing building/science locks):",
        *[f"  - {x}" for x in unit_rank],
        "",
        "REMAINS UNAVAILABLE:",
        *[f"  - {x}" for x in remaining],
        "",
        "CHANGED_KEYS:",
        *[f"  {k}" for k in sorted(allowed) if packed.get(k) != original.get(k) or k in overlays],
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
            f"ART_GZ_SIZE={art_gz_path.stat().st_size}",
            f"ART_GZ_SHA256={art_gz_sha}",
            "ZIP_FILE=SPECTER_ARABIC_ALLIANCE_UPGRADES.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #653",
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
                f"  {rel_base}/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement (complete BIG, gzipped for GitHub's 2 GiB asset limit):",
                f"  {rel_base}/_SPEC_ART_ONE.big.gz",
                f"  GZ_SIZE={art_gz_path.stat().st_size}",
                f"  GZ_SHA256={art_gz_sha}",
                f"  UNCOMPRESSED_SIZE={art_path.stat().st_size}",
                f"  UNCOMPRESSED_SHA256={art_sha}",
                "  gunzip -k _SPEC_ART_ONE.big.gz",
                "  Do not install the .gz file as the game BIG.",
                "",
                "ART is also inside the ZIP as uncompressed _SPEC_ART_ONE.big (same SHA).",
                "GitHub rejects raw files >= 2147483648 bytes. ART is unchanged from PR #653.",
                "",
                "ZIP (complete uncompressed DATA + ART BIGs):",
                f"  {rel_base}/SPECTER_ARABIC_ALLIANCE_UPGRADES.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both uncompressed BIGs in the SPECTER folder.",
                f"TAG={tag}",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/"
                + tag,
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "ARABIC ALLIANCE — ALL EXISTING UPGRADES UNLOCKED — TEST BUILD\n"
        "FactionGLA (display name Arabic Alliance) only. No new country or faction.\n"
        "Existing Upgrade_Arb_Tier1/2/3 and AA/GLA-only general powers are rank-unlocked.\n"
        "Upgrade definitions and effects are unchanged. ART is unchanged from PR #653.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# ARABIC ALLIANCE — ALL EXISTING UPGRADES UNLOCKED — TEST BUILD\n\n"
        "- Arabic Alliance is the existing FactionGLA. No new faction or country.\n"
        "- Upgrade_Arb_Tier1/2/3 are purchasable without Rank 2/3.\n"
        "- Industry Planet shows all three tier buttons on the starting CommandSet.\n"
        "- AA general powers (AWACS, paradrop, drones, 155mm, Algeria AF, Ambush,\n"
        "  Anthrax Bomb, GPS Scrambler) sit on the 1-star purchase row.\n"
        "- SCIENCE_Rank stripped from AA-folder unit Prerequisites; named sciences kept.\n"
        "- GLAWorkerCommandSet last-wins the AA build list the worker already referenced.\n"
        "- Egypt and UAE PlayerTemplates and all other factions are unchanged.\n"
        "- ART is the unchanged PR #653 BIG. Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "CommandButton_ArabicAllianceUnlock.ini last-wins Command_Arb_Tier1 and Command_Arb_Tier3.\n"
        "CommandSet_ArabicAllianceUnlock.ini last-wins SCIENCE_GLA_CommandSetRank1,\n"
        "ArabicIndustryPlanetCommandSet_T/T1/T2, and GLAWorkerCommandSet.\n"
        "Science_ArabicAllianceUnlock.ini last-wins AA/GLA-only sciences (not EmergencyRepair).\n"
        "Eight Arabic Alliance object INIs last-win with SCIENCE_Rank stripped from Prerequisites.\n"
        "PlayerTemplate.ini, Upgrade.ini, CommandButton.ini, CommandSet.ini, Science.ini,\n"
        "Upgrade_Egypt.ini, Upgrade_UAE.ini, and all non-AA objects are frozen.\n"
        "ART is copied unchanged from PR #653.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:40]))


if __name__ == "__main__":
    main()
