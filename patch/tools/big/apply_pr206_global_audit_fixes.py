#!/usr/bin/env python3
"""Apply GLOBAL FINAL AUDIT fixes for PR #206.

Extracts actionable Object INIs + CommandButton.ini from the packed PR206 BIG,
applies stock/donor remaps, writes into patch/Data, and leaves packer to overlay.
ASCII-only output. Object names unchanged.
"""
from __future__ import annotations

import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_BIG = ROOT / "Release" / "SPECTER_PR206_TEST_BUILD" / "_SPEC_DATA_ONE.big"
DATA_SRC = ROOT / "Data"
REPORT = ROOT / "Release" / "SPECTER_PR206_TEST_BUILD" / "GLOBAL_FINAL_AUDIT_REPORT.json"

MODEL_REMAPS = {
    "CHI_DF41HL": "CHI_DF41",
    "CHI_DF41_WL": "CHI_DF41Camo",
    "CHI_DF41A": "CHI_DF41_A",
    "CHI_DF41_T": "CHI_DF41",
    "CHI_DF41_TD": "CHI_DF41D",
    "CHI_GJ11LR": "CHI_GJ11L",
    "MIG-25bm_IRQ": "Iraq_Mig-25bm",
    "Egypt_IL-76": "Iraq_IL-76",
    "India_IL-76": "Iraq_IL-76",
    "Libya_IL-76": "Iraq_IL-76",
    "Pakistan_IL-76": "Iraq_IL-76",
    "SaudiArabia_IL-76": "Iraq_IL-76",
    "SouthAfrica_IL-76": "Iraq_IL-76",
    "Syria_IL-76": "Iraq_IL-76",
    "Ukraine_IL-76": "Iraq_IL-76",
    "Vietnam_IL-76": "Iraq_IL-76",
    "Irn_SU22M2_D": "Irn_SU22M2",
    "Irq_SU22M3_D": "Irq_SU22M3",
    "Iraq_Shaheed": "Irn_Shahed136",
    "IRQ_WF1": "Irq_WarFactory",
    "Iraq_MIC": "MIC",
    "Iraq_Command": "Command",
    "Iraq_sam2": "Spec_SamSite2",
    "Iraq_T-72A": "Irq_T72M1",
    "Iraq_T-72B3": "Irq_T72M1B3",
    "Iraq_Bmp-1p": "Irq_BMP1P",
    "Iraq_ZSU-23-4": "Irq_ZSU23",
    "Irq_Sam6": "irq_sam6m",
    "ISR_PULSPHD": "PULSPH",
    "US_F-16Cblk52": "US_F16CJ_blk52",
    "US_TOW_TRTU": "US_TOW_TRT",
    "3": "AIRNGR_IDG",
}

FX_REMAPS = {
    "FX_NEWGenericMissileDeath": "FX_GenericMissileDeath",
    "FX_30mmAPFSDSHitEffect": "WeaponFX_GenericTankShellDetonation",
}

WEAPON_REMAPS = {
    "HE_Zulfighar_350kg": "HE_Zulfighar_450kg",
    "Egypt_R11_CH_Explosion": "R11_CH_Explosion",
    "India_R11_CH_Explosion": "R11_CH_Explosion",
    "Libya_R11_CH_Explosion": "R11_CH_Explosion",
    "Pakistan_R11_CH_Explosion": "R11_CH_Explosion",
    "SaudiArabia_R11_CH_Explosion": "R11_CH_Explosion",
    "SouthAfrica_R11_CH_Explosion": "R11_CH_Explosion",
    "Syria_R11_CH_Explosion": "R11_CH_Explosion",
    "Ukraine_R11_CH_Explosion": "R11_CH_Explosion",
    "Vietnam_R11_CH_Explosion": "R11_CH_Explosion",
    "F35C_AN/APG81_AESA_Radar_AAMode": "F35C_AN/APG81_AESA_Radar_AAMode-kk",
}

OCL_REMAPS = {
    "OCL_CrusaderTurretDeathEffect": "OCL_GenericTankDeathEffect",
}

CS_REMAPS = {
    "RussiaGattlingCannonCommandSet": "ChinaGattlingCannonCommandSet",
    "AmericaShipYardCommandSet": "BattleShipCommandSet",
}

# CommandButton Object= remaps (missing -> existing)
CB_OBJECT_REMAPS = {
    "ChinaJetMIG": "Infa_ChinaJetMIG",
    "ChinaVehicleHelix": "Infa_ChinaVehicleHelix",
    "Russia_Mi-28NE": "Turkey_Mi-28NE",
    "Russia_Mig-31K": "RussiaJetMig31K",
    "Russia_Su-24M2": "RussiaJetSU24M2",
    "Russia_Su-24MP": "RussiaJetSU24MP",
    "Russia_Su-25T": "RussiaJetSU25T",
    "Russia_Su34": "RussiaJetSu34",
    "Russia_Su35S": "RussiaJetSu35S",
    "Russia_Su35S_TS": "RussiaJetSu35S",
    "Russia_Su57": "Patch_Russia_Su57",
    "Russia_Su57_AA": "Patch_Russia_Su57",
    "Russia_Tu-22M3M": "RussiaJetTu22M3M",
    "ChinaVehicleListeningOutpost": "Infa_ChinaVehicleListeningOutpost",
    "ChinaVehicleTroopCrawler": "Infa_ChinaVehicleTroopCrawler",
    "ChinaTankECM": "Infa_ChinaTankECM",
    "ChinaVehicleInfernoCannon": "Infa_ChinaVehicleInfernoCannon",
    "ChinaVehicleNukeLauncher": "Infa_ChinaVehicleNukeLauncher",
    "RussiaTankT72B3": "RussiaTankT72B3M",
    "Russia_92N6R": "RussiaVehicle92N6R",
    "Russia_Bm30": "RussiaVehicleBm30",
    "Russia_Krasukha-4": "ChinaVehicleKrasukha4",
    "Russia_PantsirS1M": "RussiaVehiclePantsirS1M",
    "Russia_S400_Real": "RussiaS400Deployed",
    "Russia_TOR_M2U": "RussiaVehiclePantsirS1M",
    "Russia_TOS-1A": "RussiaTankTos1A",
    "Russian_T15": "RussianTankT15",
    "ChinaNuclearMissileLauncher": "Infa_ChinaNuclearMissileLauncher",
    "ChinaTankOverlord": "ChinaTankOverlordGattlingCannon",
    "EgyptInfantryRifleman": "EgyptInfantryMachinegunner",
    "Slth_GLATankScorpion": "Slth_GLATankScorpion2",
    "Russia_92N6R_AI": "RussiaRadar92N6RAI",
    "Russia_S400_AI": "RussiaS400Deployed",
}

WORKER_CS = {
    "Egypt_Worker": "Egypt_WorkerCommandSet",
    "India_Worker": "India_WorkerCommandSet",
    "Iraq_Worker": "Iraq_WorkerCommandSet",
    "Libya_Worker": "Libya_WorkerCommandSet",
    "Pakistan_Worker": "Pakistan_WorkerCommandSet",
    "SaudiArabia_Worker": "SaudiArabia_WorkerCommandSet",
    "SouthAfrica_Worker": "SouthAfrica_WorkerCommandSet",
    "Syria_Worker": "Syria_WorkerCommandSet",
    "Ukraine_Worker": "Ukraine_WorkerCommandSet",
    "Vietnam_Worker": "Vietnam_WorkerCommandSet",
}

POWERPLANT_CS = {
    "Iraq_PowerPlant": "AmericaPowerPlantCommandSet",
    "NorthKorea_PowerPlant": "ChinaPowerPlantCommandSet",
    "Slth_GLAStingerSite": "ChinaGattlingCannonCommandSet",
}


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    n = struct.unpack(">I", data[8:12])[0]
    off = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        fo, fl = struct.unpack(">II", data[off : off + 8])
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin-1").replace("\\", "/")
        off = end + 1
        out[name] = data[fo : fo + fl]
    return out


def to_ascii(text: str) -> str:
    return text.encode("ascii", "replace").decode("ascii")


def replace_token(text: str, old: str, new: str) -> str:
    # Word-ish token replace for INI values (preserve surrounding spacing)
    return re.sub(rf"(?<![A-Za-z0-9_/]){re.escape(old)}(?![A-Za-z0-9_/])", new, text)


def fix_worker(text: str, worker_obj: str) -> str:
    cs = WORKER_CS[worker_obj]
    # Fix CommandSetUpgrade that still points at missing GLAWorkerCommandSet
    text = re.sub(
        r"(?m)^(\s*CommandSet\s*=\s*)GLAWorkerCommandSet\s*$",
        rf"\1{cs}",
        text,
    )
    return text


def fix_powerplant_commented_cs(text: str, obj: str) -> str:
    cs = POWERPLANT_CS[obj]
    # CommandSet = ;Something  -> real CS (crash: no valid CommandSet)
    text = re.sub(
        rf"(?ms)(Object\s+{re.escape(obj)}\b.*?^\s*CommandSet\s*=\s*);[^\n]*",
        rf"\1{cs}",
        text,
        count=1,
    )
    return text


def fix_usa_fake_air(text: str) -> str:
    # Invalid CommandSet = none on USA_FakeAirTargets
    text = re.sub(
        r"(?ms)(Object\s+USA_FakeAirTargets\b.*?^\s*)CommandSet\s*=\s*none\s*$",
        r"\1; CommandSet omitted (was none) PR206 global audit",
        text,
        count=1,
    )
    return text


def fix_upgrade_heroic(text: str) -> str:
    # Missing Upgrade_Veterancy_HEROIC -> comment TriggeredBy to avoid init hazard
    text = re.sub(
        r"(?m)^(\s*)TriggeredBy\s*=\s*Upgrade_Veterancy_HEROIC\s*$",
        r"\1; TriggeredBy = Upgrade_Veterancy_HEROIC ; PR206 missing upgrade removed",
        text,
    )
    return text


def apply_common(text: str) -> str:
    for old, new in MODEL_REMAPS.items():
        text = re.sub(
            rf"(?m)^(\s*Model\s*=\s*){re.escape(old)}(\s*(?:;.*)?)?$",
            rf"\1{new}\2",
            text,
        )
    for old, new in FX_REMAPS.items():
        text = replace_token(text, old, new)
    for old, new in WEAPON_REMAPS.items():
        text = replace_token(text, old, new)
    for old, new in OCL_REMAPS.items():
        text = replace_token(text, old, new)
    for old, new in CS_REMAPS.items():
        text = re.sub(
            rf"(?m)^(\s*CommandSet\s*=\s*){re.escape(old)}(\s*(?:;.*)?)?$",
            rf"\1{new}\2",
            text,
        )
    return text


def fix_command_button(text: str) -> str:
    for old, new in CB_OBJECT_REMAPS.items():
        text = re.sub(
            rf"(?m)^(\s*Object\s*=\s*){re.escape(old)}(\s*(?:;.*)?)?$",
            rf"\1{new}\2",
            text,
        )
    return text


def main() -> None:
    import json

    report = json.loads(
        (ROOT / "Release/SPECTER_PR206_TEST_BUILD/GLOBAL_FINAL_AUDIT_REPORT.json").read_text()
    )
    paths = sorted({i["path"] for i in report["actionable_issues"]})
    paths.append("Data/INI/CommandButton.ini")

    big = read_big(DATA_BIG)
    changed: list[str] = []
    for rel in paths:
        if rel not in big:
            print("MISSING_IN_BIG", rel)
            continue
        raw = big[rel]
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        orig = text

        text = apply_common(text)
        text = fix_usa_fake_air(text)
        text = fix_upgrade_heroic(text)

        # per-object worker / powerplant
        for worker in WORKER_CS:
            if re.search(rf"(?m)^Object\s+{re.escape(worker)}\b", text):
                text = fix_worker(text, worker)
        for obj in POWERPLANT_CS:
            if re.search(rf"(?m)^Object\s+{re.escape(obj)}\b", text):
                text = fix_powerplant_commented_cs(text, obj)

        if rel.endswith("CommandButton.ini"):
            text = fix_command_button(text)

        text = to_ascii(text)
        if text == orig.encode("ascii", "replace").decode("ascii") and text == orig:
            # still write if content changed via ascii only
            pass
        if text != orig:
            changed.append(rel)

        out = DATA_SRC / rel.removeprefix("Data/")
        # paths are Data/INI/... so DATA_SRC/INI/...
        if rel.startswith("Data/"):
            out = DATA_SRC / rel[len("Data/") :]
        else:
            out = DATA_SRC / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="ascii", newline="\n")
        print("WROTE", out.relative_to(ROOT))

    manifest = ROOT / "Release" / "SPECTER_PR206_TEST_BUILD" / "GLOBAL_AUDIT_FIXED_MANIFEST.txt"
    manifest.write_text(
        "\n".join(paths) + f"\n\ncount={len(paths)}\nchanged={len(changed)}\n",
        encoding="ascii",
    )
    print("MANIFEST", manifest)
    print("CHANGED", len(changed))
    for p in changed:
        print(" ", p)


if __name__ == "__main__":
    main()
