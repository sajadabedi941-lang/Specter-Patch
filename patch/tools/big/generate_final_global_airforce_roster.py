#!/usr/bin/env python3
"""Final global air-force roster overlay. Visual donors only. No USA/RU/CN objects."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_global_donor_airforce as g

ROOT = Path("/workspace/patch/Data")
INI = ROOT / "INI"
MAP = INI / "MappedImages/HandCreated"

fighter = g.fighter
wset = g.wset
a2a = g.a2a
a2g = g.a2g
cannon = g.cannon
rockets = g.rockets
w = g.w

METEOR = g.METEOR
AIM9 = g.AIM9
R77 = g.R77
GBU = g.GBU
FAB = g.FAB
CRUISE = g.CRUISE
KH31 = g.KH31
PAVE = g.PAVE


def _h(s: str) -> int:
    return int(hashlib.md5(s.encode("ascii")).hexdigest()[:8], 16)


def loadout(obj: str, role: str) -> str:
    n = abs(_h(obj))
    v1 = 40 + (n % 30)
    v2 = 20 + ((n >> 3) % 24)
    d1 = 700 + (n % 400)
    d2 = 550 + ((n >> 5) % 250)
    d3 = 400 + ((n >> 7) % 500)
    if role == "a2a":
        return wset(
            f"{obj}_WpnRadar", f"{obj}_WpnIR", f"{obj}_WpnGun",
            "AIRCRAFT", "AIRCRAFT", "AIRCRAFT VEHICLE",
        ), "\n".join([
            a2a(f"{obj}_WpnRadar", 880 + v1, 1400 + v1, 6 + (n % 3), d1, METEOR if n % 2 == 0 else R77),
            a2a(f"{obj}_WpnIR", 720 + v2, 560 + v2, 2 + (n % 3), d2, AIM9),
            cannon(f"{obj}_WpnGun", 24 + (n % 16)),
        ])
    if role == "interceptor":
        return wset(
            f"{obj}_WpnRadar", f"{obj}_WpnIR", f"{obj}_WpnGun",
            "AIRCRAFT", "AIRCRAFT", "AIRCRAFT",
        ), "\n".join([
            a2a(f"{obj}_WpnRadar", 940 + v1, 1500 + v1, 8 + (n % 3), d1 - 80, R77 if n % 2 else METEOR),
            a2a(f"{obj}_WpnIR", 760 + v2, 600 + v2, 4, d2, AIM9),
            cannon(f"{obj}_WpnGun", 20 + (n % 12)),
        ])
    if role == "multirole":
        return wset(
            f"{obj}_WpnRadar", f"{obj}_WpnIR", f"{obj}_WpnStrike",
            "AIRCRAFT", "AIRCRAFT", "VEHICLE STRUCTURE",
        ), "\n".join([
            a2a(f"{obj}_WpnRadar", 820 + v1, 1200 + v1, 4 + (n % 3), d1, METEOR),
            a2a(f"{obj}_WpnIR", 680 + v2, 520 + v2, 2, d2, AIM9),
            a2g(f"{obj}_WpnStrike", 780 + v1, 30 + (n % 10), 780 + v2, 4 + (n % 3), 800 + d3 // 4, GBU if n % 2 else PAVE, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1000 + (n % 800)),
        ])
    if role == "strike":
        return wset(
            f"{obj}_WpnIR", f"{obj}_WpnBomb", f"{obj}_WpnStandoff",
            "AIRCRAFT", "VEHICLE STRUCTURE", "VEHICLE STRUCTURE",
        ), "\n".join([
            a2a(f"{obj}_WpnIR", 640 + v2, 500 + v2, 2, d2 + 80, AIM9),
            a2g(f"{obj}_WpnBomb", 860 + v1, 36 + (n % 12), 820 + v2, 6 + (n % 4), 600 + d3 // 5, GBU if n % 3 else FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 900 + (n % 700)),
            a2g(f"{obj}_WpnStandoff", 1100 + v1, 48 + (n % 10), 1200 + v1, 2, 2400 + (n % 800), CRUISE if n % 2 else KH31, "Grad_launch", "FX_MediumMissileIgnition", "FX_HE_UnguidedMissileDetonation", 1600 + (n % 600)),
        ])
    if role == "cas":
        return wset(
            f"{obj}_WpnGun", f"{obj}_WpnRkt", f"{obj}_WpnBomb",
            "VEHICLE INFANTRY", "VEHICLE STRUCTURE", "VEHICLE STRUCTURE",
        ), "\n".join([
            cannon(f"{obj}_WpnGun", 32 + (n % 16)),
            rockets(f"{obj}_WpnRkt", 8 + (n % 8)),
            a2g(f"{obj}_WpnBomb", 640 + v1, 28 + (n % 8), 560 + v2, 6, 400 + d3 // 6, FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation"),
        ])
    # legacy
    return wset(
        f"{obj}_WpnIR", f"{obj}_WpnGun", f"{obj}_WpnBomb",
        "AIRCRAFT", "AIRCRAFT VEHICLE", "VEHICLE STRUCTURE",
    ), "\n".join([
        a2a(f"{obj}_WpnIR", 600 + v2, 460 + v2, 2, d2 + 100, AIM9),
        cannon(f"{obj}_WpnGun", 20 + (n % 10)),
        a2g(f"{obj}_WpnBomb", 620 + v1, 30, 540 + v2, 4, 550, FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation"),
    ])


ROLE_STATS = {
    "a2a": (2400, 16.0, 520, 720),
    "interceptor": (2200, 14.5, 480, 780),
    "multirole": (1800, 13.0, 440, 640),
    "strike": (2000, 14.0, 460, 600),
    "cas": (1400, 11.0, 380, 520),
    "legacy": (1100, 9.0, 300, 480),
    "stealth": (3000, 19.0, 560, 760),
}


def jet(obj, side, folder, model, role, identity, source, note, scale=0.92, md=None, mk=None, portrait_src=None):
    cost, time, hp, vision = ROLE_STATS[role]
    if role == "stealth":
        cost, time, hp, vision = 3000, 19.0, 560, 760
    wpn_block, wpn_defs = loadout(obj, role if role != "stealth" else "a2a")
    if role == "stealth":
        wpn_block, wpn_defs = loadout(obj, "multirole")
    return dict(
        obj=obj,
        side=side,
        folder=folder,
        rel=f"INI/Object/Specter/{folder}/Airforce/{obj}.ini",
        model=model,
        model_d=md or model,
        model_k=mk or md or model,
        role=role if role != "stealth" else "a2a",
        role_label="stealth / air superiority" if role == "stealth" else role,
        identity=identity,
        source=source,
        note=note,
        scale=scale,
        cost=cost,
        time=time,
        hp=hp,
        vision=vision,
        portrait=f"SPEC_{obj}",
        portrait_src=portrait_src or (model + ".dds"),
        wpn_block=wpn_block,
        wpn_defs=wpn_defs,
    )


# folder, side
FR = ("French Armed Forces", "France")
DE = ("German Armed Forces", "Germany")
IT = ("Italian Armed Forces", "Italy")
UK = ("British Armed Forces", "Britain")
JP = ("Japan Self-Defense Forces", "Japan")
TR = ("Turkey Armed Forces", "Turkey")
IR = ("Iranian Army", "Iran")
PK = ("Pakistan Armed Forces", "Pakistan")
IN = ("Indian Armed Forces", "India")
IL = ("Israel Defense Forces", "AmericaAirForceGeneral")
SA = ("Saudi Arabia Armed Forces", "SaudiArabia")
NA = ("NATO", "Nato")
SE = ("Swedish Armed Forces", "Sweden")
UA = ("Ukrainian Armed Forces", "Ukraine")
AE = ("United Arab Emirates", "UAE")
LY = ("Libyan Armed Forces", "Libya")
SY = ("Syrian Arab Army", "Syria")
ZA = ("South African National Defence Force", "SouthAfrica")
SK = ("Republic of Korea Armed Forces", "SouthKorea")
NK = ("North Korea", "NorthKorea")
VN = ("Vietnam People's Army", "Vietnam")
IQ = ("Iraq Army", "Iraq")
GL = ("ArabicArmy", "GLA")

AIRCRAFT = [
    jet("GermanyJetTyphoonT1", DE[1], DE[0], "EVTyphoon", "a2a", "Typhoon T1", "DONOR_ART EVTyphoon.W3D unused unique", "Luftwaffe Typhoon Tranche 1. Distinct from T4 LSFEUEF2000.", 0.96, portrait_src="EVTyphoonSDTX04.tga"),
    jet("JapanJetF35A", JP[1], JP[0], "LSFUSAF35A", "stealth", "F-35A", "packed LSFUSAF35A", "JASDF F-35A. Meteor-class and JDAM.", 0.90, "LSFUSAF35Ad", "LSFUSAF35Ak", "LSFUSAF35A.W3D"),
    jet("JapanJetF35B", JP[1], JP[0], "ENF35A", "stealth", "F-35B", "packed ENF35A", "JASDF / JMSDF F-35B STOVL.", 0.88, portrait_src="ENF35A.W3D"),
    jet("JapanJetFX", JP[1], JP[0], "CHAJ31HXNew", "stealth", "F-X", "packed unused CHAJ31HXNew", "JASDF F-X next-generation fighter stand-in.", 0.94, portrait_src="CHAJ31HXNew.W3D"),
    jet("JapanJetF15DJ", JP[1], JP[0], "US_F15EX", "multirole", "F-15DJ", "packed US_F15EX", "JASDF two-seat F-15DJ.", 1.02, portrait_src="US_F15EX.W3D"),
    jet("JapanJetF3", JP[1], JP[0], "PAK-FA", "stealth", "F-3 GCAP", "packed PAK-FA", "JASDF F-3 / GCAP partner stand-in.", 0.96, "PAK-FA_D", "PAK-FA_E", "PAK-FA.W3D"),
    jet("TurkeyJetF35A", TR[1], TR[0], "LSFUSAF35A", "stealth", "F-35A", "packed LSFUSAF35A", "Turkish F-35A (ordered / Peace Onyx III).", 0.90, "LSFUSAF35Ad", "LSFUSAF35Ak"),
    jet("TurkeyJetHurjet", TR[1], TR[0], "AVHawk", "cas", "Hurjet", "packed AVHawk light-attack stand-in", "TAI Hurjet light combat trainer.", 0.82, "AVHawk_D", "AVHawk_D"),
    jet("TurkeyJetNF5", TR[1], TR[0], "AVHawk", "cas", "NF-5A", "packed AVHawk_D", "Turkish NF-5A Freedom Fighter.", 0.80, "AVHawk_D", "AVHawk_D1"),
    jet("TurkeyJetF4E", TR[1], TR[0], "JPF4", "legacy", "F-4E Phantom", "packed JPF4", "Turkish F-4E Phantom (pre-Terminator).", 0.98, "JPF4D", "JPF4K"),
    jet("TurkeyJetKAANBlk2", TR[1], TR[0], "NVJ31", "a2a", "KAAN Block 2", "packed NVJ31", "KAAN MMU Block 2 air-superiority.", 0.98, "NVJ31_D", "NVJ31_E"),
    jet("TurkeyJetF16Blk30", TR[1], TR[0], "LSFF16", "multirole", "F-16C Block 30", "packed LSFF16", "Turkish F-16C Block 30 Peace Onyx I.", 0.88, "LSFF16d", "LSFF16k"),
    jet("IranJetF14AM", IR[1], IR[0], "LSFIRF14A", "interceptor", "F-14AM", "DONOR_ART LSFIRF14A unused unique Tomcat", "IRIAF F-14AM. Distinct from live Iran_F14A.", 1.04, "LSFIRF14Ad", "LSFIRF14Ad", "LSFF14A.dds"),
    jet("PakistanJetJF17", PK[1], PK[0], "LSFPKJF17", "multirole", "JF-17 Thunder", "packed LSFPKJF17 unused by Pakistan", "PAF JF-17 Thunder Block II.", 0.88, "LSFPKJF17d", "LSFPKJF17k"),
    jet("PakistanJetJF17Blk3", PK[1], PK[0], "LSFPKJF17", "strike", "JF-17 Block III", "packed LSFPKJF17k", "PAF JF-17 Block III strike.", 0.90, "LSFPKJF17d", "LSFPKJF17k"),
    jet("PakistanJetMirage5", PK[1], PK[0], "LSFMirage5", "strike", "Mirage 5 PA", "packed LSFMirage5", "PAF Mirage 5 ROSE strike.", 0.90, "LSFMirage5d", "LSFMirage5k"),
    jet("PakistanJetMirage3", PK[1], PK[0], "LSFMirage3", "interceptor", "Mirage IIIEP", "packed LSFMirage3", "PAF Mirage IIIEP.", 0.88, "LSFMirage3d", "LSFMirage3k"),
    jet("PakistanJetA5C", PK[1], PK[0], "QIANG5", "cas", "A-5C Fantan", "packed QIANG5", "PAF A-5C Fantan CAS.", 0.92, "QIANG5d", "QIANG5k", "chq5m.dds"),
    jet("PakistanJetF16B", PK[1], PK[0], "LSFPKF16", "multirole", "F-16B", "DONOR_ART LSFPKF16 unused unique", "PAF F-16B two-seat.", 0.88, "LSFPKF16d", "LSFPKF16d", "LSFPKF16.dds"),
    jet("PakistanJetF7P", PK[1], PK[0], "LSFJ7", "legacy", "F-7P", "packed LSFJ7", "PAF F-7P Skybolt. Distinct from F-7PG.", 0.84, "LSFJ7d", "LSFJ7k"),
    jet("PakistanJetMirageROSE", PK[1], PK[0], "UVMirage", "strike", "Mirage ROSE III", "packed UVMirage", "PAF Mirage ROSE III.", 0.90, "UVMirage_D", "UVMirage_E"),
    jet("IndiaJetRafaleEH", IN[1], IN[0], "LSFIDRafale", "multirole", "Rafale EH", "packed LSFIDRafale India mesh", "IAF Rafale EH.", 0.94, "LSFIDRafaled", "LSFIDRafalek"),
    jet("IndiaJetRafaleDH", IN[1], IN[0], "LSFRafaleAS", "strike", "Rafale DH", "packed LSFRafaleAS", "IAF Rafale DH two-seat strike.", 0.94, "LSFRafaleASd", "LSFRafaleASd"),
    jet("IndiaJetMirage2000H", IN[1], IN[0], "LSFMirage2000", "a2a", "Mirage 2000H", "packed LSFMirage2000", "IAF Mirage 2000H.", 0.92, "LSFMirage2000d", "LSFMirage2000k"),
    jet("IndiaJetMirage2000I", IN[1], IN[0], "LSFMirage2KD", "strike", "Mirage 2000I", "packed LSFMirage2KD", "IAF Mirage 2000I strike.", 0.92, "LSFMirage2KDd", "LSFMirage2KDk"),
    jet("IndiaJetMig21Bison", IN[1], IN[0], "LSFIDMig21", "legacy", "MiG-21 Bison", "packed unused LSFIDMig21", "IAF MiG-21 Bison.", 0.84, "LSFIDMig21d", "LSFIDMig21d"),
    jet("IndiaJetJaguarIS", IN[1], IN[0], "LSFFRF1", "strike", "Jaguar IS", "packed LSFFRF1 Jaguar-class donor", "IAF Jaguar IS strike.", 0.90, "LSFFRF1d", "LSFFRF1k"),
    jet("IndiaJetMig27", IN[1], IN[0], "MiG-23bn_Irq", "cas", "MiG-27 Bahadur", "packed MiG-23bn_Irq", "IAF MiG-27 Bahadur.", 0.92),
    jet("IndiaJetMig29K", IN[1], IN[0], "RUS_Mig35", "multirole", "MiG-29K", "packed RUS_Mig35", "INAS MiG-29K naval fighter.", 0.90),
    jet("IndiaJetAMCA", IN[1], IN[0], "LSFJ31", "stealth", "AMCA", "packed LSFJ31 AMCA stand-in", "IAF AMCA stealth fighter stand-in.", 0.94, "LSFJ31d", "LSFJ31k"),
    jet("IndiaJetTejas", IN[1], IN[0], "NVJ31", "multirole", "Tejas Mk1A", "packed NVJ31 Tejas/AMCA-class stand-in", "IAF Tejas Mk1A. Closest packed canard-ish stealth light fighter.", 0.86, "NVJ31_D", "NVJ31_E"),
    jet("IsraelJetF16CBarak", IL[1], IL[0], "LSFISF16", "multirole", "F-16C Barak", "DONOR_ART LSFISF16 unused unique", "IAF F-16C Barak. Distinct from F-16I Sufa.", 0.88, "LSFISF16d", "LSFISF16d", "LSFF16I.dds"),
    jet("IsraelJetF15IRaamII", IL[1], IL[0], "LSFISF15E", "strike", "F-15I Ra'am", "DONOR_ART LSFISF15E unused unique", "IAF F-15I Ra'am strike mesh distinct from Isr_F15I.", 1.04, "LSFISF15Ed", "LSFISF15Ed", "LSFISF15E.dds"),
    jet("IsraelJetKfir", IL[1], IL[0], "LSFMirage5", "multirole", "Kfir C.10", "packed LSFMirage5 Kfir stand-in", "IAF Kfir C.10.", 0.88, "LSFMirage5d", "LSFMirage5k"),
    jet("IsraelJetF4E", IL[1], IL[0], "JPF4", "legacy", "F-4E Kurnass", "packed JPF4", "IAF F-4E Kurnass.", 0.98, "JPF4D", "JPF4K"),
    jet("IsraelJetNesher", IL[1], IL[0], "LSFMirage3", "legacy", "Nesher", "packed LSFMirage3", "IAF Nesher.", 0.86, "LSFMirage3d", "LSFMirage3k"),
    jet("SaudiJetF15SA", SA[1], SA[0], "Arb_F15SA", "strike", "F-15SA", "packed Arb_F15SA", "RSAF F-15SA.", 1.06),
    jet("SaudiJetF15C", SA[1], SA[0], "LSFUSAF15C", "a2a", "F-15C", "packed LSFUSAF15C", "RSAF F-15C.", 1.00, "LSFUSAF15Cd", "LSFUSAF15Ck", "LSFUSAF15C.tga"),
    jet("SaudiJetTyphoon", SA[1], SA[0], "LSFEUEF2000", "a2a", "Typhoon F.2", "packed LSFEUEF2000", "RSAF Typhoon F.2.", 0.96, "LSFEUEF2000d", "LSFEUEF2000k"),
    jet("SaudiJetTyphoonT3", SA[1], SA[0], "NAT_EF2000T4", "multirole", "Typhoon T3", "packed NAT_EF2000T4", "RSAF Typhoon T3.", 0.96),
    jet("SaudiJetTornadoIDS", SA[1], SA[0], "LSFTornado", "strike", "Tornado IDS", "packed LSFTornado", "RSAF Tornado IDS.", 1.00, "LSFTornadod", "LSFTornadok"),
    jet("SaudiJetTornadoADV", SA[1], SA[0], "LSFTornado", "interceptor", "Tornado ADV", "packed LSFTornado", "RSAF Tornado ADV.", 1.00, "LSFTornadod", "LSFTornadok"),
    jet("SaudiJetTornadoECR", SA[1], SA[0], "LSFTornado", "strike", "Tornado ECR", "packed LSFTornado", "RSAF Tornado ECR SEAD.", 1.00, "LSFTornadod", "LSFTornadok"),
    jet("SaudiJetHawk65", SA[1], SA[0], "AVHawk", "cas", "Hawk 65", "packed AVHawk", "RSAF Hawk 65.", 0.80, "AVHawk_D", "AVHawk_D"),
    jet("SaudiJetLightning", SA[1], SA[0], "AVLightn", "interceptor", "Lightning F.53", "packed AVLightn", "RSAF Lightning F.53.", 0.86, "AVLightn_D", "AVLightn_D"),
    jet("SaudiJetF15EX", SA[1], SA[0], "US_F15EX", "multirole", "F-15EX", "packed US_F15EX", "RSAF F-15EX / Advanced Eagle.", 1.05),
    jet("NatoJetF18A", NA[1], NA[0], "AmF18A", "multirole", "F/A-18A Hornet", "DONOR_ART AmF18A unused unique", "NATO F/A-18A Hornet.", 0.92, portrait_src="AmF18MA01.dds"),
    jet("NatoJetF18C", NA[1], NA[0], "AVF-18", "multirole", "F/A-18C Hornet", "packed unused AVF-18", "NATO F/A-18C Hornet.", 0.92, "AVF-18_D", "AVF-18_E"),
    jet("NatoJetF18E", NA[1], NA[0], "F18SEA", "strike", "F/A-18E Super Hornet", "DONOR_ART F18SEA unused unique", "NATO F/A-18E Super Hornet.", 0.96, portrait_src="F18SEA_1.tga"),
    jet("NatoJetF18F", NA[1], NA[0], "US_FA18F", "multirole", "F/A-18F Super Hornet", "packed US_FA18F", "NATO F/A-18F Super Hornet.", 0.96),
    jet("NatoJetF35B", NA[1], NA[0], "ENF35A", "stealth", "F-35B", "packed ENF35A", "NATO F-35B.", 0.88),
    jet("NatoJetTornadoIDS", NA[1], NA[0], "LSFTornado", "strike", "Tornado IDS", "packed LSFTornado", "NATO Tornado IDS.", 1.00, "LSFTornadod", "LSFTornadok"),
    jet("NatoJetF16C", NA[1], NA[0], "AVF16", "multirole", "F-16C", "packed AVF16", "NATO F-16C Fighting Falcon.", 0.88, "AVF16_D", "AVF16_E"),
    jet("SwedenJetGripenE", SE[1], SE[0], "LSFEUEF2000", "a2a", "JAS 39E Gripen", "packed LSFEUEF2000 Gripen-E canard stand-in", "Flygvapnet JAS 39E. Closest packed euro-canard.", 0.94, "LSFEUEF2000d", "LSFEUEF2000k"),
    jet("SwedenJetViggenJA37", SE[1], SE[0], "LSFMirage2000", "interceptor", "JA 37 Viggen", "packed LSFMirage2000 delta stand-in", "Flygvapnet JA 37 Viggen.", 0.92, "LSFMirage2000d", "LSFMirage2000k"),
    jet("SwedenJetViggenAJS37", SE[1], SE[0], "LSFMirage2KD", "strike", "AJS 37 Viggen", "packed LSFMirage2KD", "Flygvapnet AJS 37 Viggen strike.", 0.92, "LSFMirage2KDd", "LSFMirage2KDk"),
    jet("SwedenJetDrakenJ35", SE[1], SE[0], "LSFMirage3", "interceptor", "J 35 Draken", "packed LSFMirage3 double-delta stand-in", "Flygvapnet J 35 Draken.", 0.86, "LSFMirage3d", "LSFMirage3k"),
    jet("SwedenJetLansenJ32", SE[1], SE[0], "LSFFRF1", "strike", "J 32 Lansen", "packed LSFFRF1", "Flygvapnet J 32 Lansen.", 0.90, "LSFFRF1d", "LSFFRF1k"),
    jet("SwedenJetSK60", SE[1], SE[0], "AVHawk", "cas", "SK 60", "packed AVHawk", "Flygvapnet SK 60 light attack.", 0.78, "AVHawk_D", "AVHawk_D"),
    jet("SwedenJetViggenSH", SE[1], SE[0], "UVMirage", "strike", "SH 37 Viggen", "packed UVMirage", "Flygvapnet SH 37 Viggen.", 0.90, "UVMirage_D", "UVMirage_E"),
    jet("UkraineJetMig29", UA[1], UA[0], "LSFruMiG29", "a2a", "MiG-29", "packed LSFruMiG29", "Ukrainian MiG-29 Fulcrum.", 0.88, "LSFruMiG29d", "LSFruMiG29k"),
    jet("UkraineJetMig29MU1", UA[1], UA[0], "RUS_Mig35", "multirole", "MiG-29MU1", "packed RUS_Mig35", "Ukrainian MiG-29MU1.", 0.90),
    jet("UkraineJetSu27", UA[1], UA[0], "LSFRUSU27SK", "a2a", "Su-27", "packed LSFRUSU27SK", "Ukrainian Su-27 Flanker.", 0.98, "LSFRUSU27SKd", "LSFRUSU27SKk"),
    jet("UkraineJetSu27UB", UA[1], UA[0], "RUS_SU30SM2", "multirole", "Su-27UB", "packed RUS_SU30SM2", "Ukrainian Su-27UB.", 0.96),
    jet("UkraineJetSu24M", UA[1], UA[0], "RUS_SU24M2", "strike", "Su-24M", "packed RUS_SU24M2", "Ukrainian Su-24M.", 1.02),
    jet("UkraineJetSu24MR", UA[1], UA[0], "RUS_SU24MP", "strike", "Su-24MR", "packed RUS_SU24MP", "Ukrainian Su-24MR fighter-bomber.", 1.02),
    jet("UkraineJetSu25", UA[1], UA[0], "RUS_SU25T", "cas", "Su-25", "packed RUS_SU25T", "Ukrainian Su-25 Frogfoot.", 0.92),
    jet("UkraineJetSu25M1", UA[1], UA[0], "RUSU-25", "cas", "Su-25M1", "packed RUSU-25", "Ukrainian Su-25M1.", 0.92, "RUSU-25_D", "RUSU-25_E"),
    jet("UkraineJetF16AM", UA[1], UA[0], "US_F16CJ_blk52", "multirole", "F-16AM", "packed US_F16CJ_blk52", "Ukrainian F-16AM.", 0.88),
    jet("UkraineJetMirage2000", UA[1], UA[0], "LSFMirage2000", "multirole", "Mirage 2000", "packed LSFMirage2000", "Ukrainian Mirage 2000.", 0.90, "LSFMirage2000d", "LSFMirage2000k"),
    jet("UkraineJetMig21", UA[1], UA[0], "UVMig-21", "legacy", "MiG-21bis", "packed UVMig-21", "Ukrainian MiG-21bis.", 0.82, "UVMig-21_D", "UVMig-21_E"),
    jet("UAEJetF16E", AE[1], AE[0], "Arb_F16C_B60", "multirole", "F-16E Block 60", "packed Arb_F16C_B60", "UAE F-16E Desert Falcon.", 0.90),
    jet("UAEJetF16F", AE[1], AE[0], "Egy_F16C", "multirole", "F-16F Block 60", "packed Egy_F16C", "UAE F-16F two-seat.", 0.90, "Egy_F16C_D", "Egy_F16C_R"),
    jet("UAEJetF16ECegy", AE[1], AE[0], "LSFF16CEgy", "strike", "F-16E Desert Falcon", "DONOR_ART LSFF16CEgy unused unique", "UAE F-16E unique mesh.", 0.90, "LSFF16CEgyd", "LSFF16CEgyd", "ISFUSAF16.tga"),
    jet("UAEJetMirage20009", AE[1], AE[0], "LSFMirage2000", "a2a", "Mirage 2000-9", "packed LSFMirage2000", "UAE Mirage 2000-9.", 0.92, "LSFMirage2000d", "LSFMirage2000k"),
    jet("UAEJetMirage2000DAD", AE[1], AE[0], "LSFMirage2KD", "strike", "Mirage 2000DAD", "packed LSFMirage2KD", "UAE Mirage 2000DAD.", 0.92, "LSFMirage2KDd", "LSFMirage2KDk"),
    jet("UAEJetMirage20009E", AE[1], AE[0], "FraMirage2000", "multirole", "Mirage 2000-9E", "packed FraMirage2000", "UAE Mirage 2000-9E.", 0.92),
    jet("UAEJetF15EA", AE[1], AE[0], "US_F15EX", "strike", "F-15EA", "packed US_F15EX", "UAE F-15EA ordered Eagle.", 1.06),
    jet("UAEJetHawk102", AE[1], AE[0], "AVHawk", "cas", "Hawk 102", "packed AVHawk", "UAE Hawk 102.", 0.80, "AVHawk_D", "AVHawk_D"),
    jet("UAEJetF15E", AE[1], AE[0], "US_F15E", "strike", "F-15E", "packed US_F15E", "UAE F-15E-class strike eagle.", 1.04, "US_F15E_D", "US_F15E_R"),
    jet("UAEJetF15SA", AE[1], AE[0], "Arb_F15SA", "a2a", "F-15SA", "packed Arb_F15SA", "UAE Advanced Eagle.", 1.06),
    jet("LibyaJetSu22", LY[1], LY[0], "Irq_SU22M3", "strike", "Su-22M3", "packed Irq_SU22M3", "Libyan Su-22M3.", 0.90),
    jet("LibyaJetSu24", LY[1], LY[0], "Irq_Su24Mk", "strike", "Su-24MK", "packed Irq_Su24Mk", "Libyan Su-24MK.", 1.00),
    jet("LibyaJetMig23", LY[1], LY[0], "MiG-23bn_Irq", "multirole", "MiG-23ML", "packed MiG-23bn_Irq", "Libyan MiG-23ML.", 0.90),
    jet("LibyaJetMig25", LY[1], LY[0], "Iraq_Mig-25bm", "interceptor", "MiG-25PD", "packed Iraq_Mig-25bm", "Libyan MiG-25PD.", 1.08),
    jet("LibyaJetMig21", LY[1], LY[0], "UVMig-21", "legacy", "MiG-21bis", "packed UVMig-21", "Libyan MiG-21bis.", 0.82, "UVMig-21_D", "UVMig-21_E"),
    jet("LibyaJetJ7", LY[1], LY[0], "LSFJ7", "legacy", "J-7", "packed LSFJ7", "Libyan J-7.", 0.84, "LSFJ7d", "LSFJ7k"),
    jet("LibyaJetMirageF1BD", LY[1], LY[0], "UVMirage", "multirole", "Mirage F1BD", "packed UVMirage", "Libyan Mirage F1BD.", 0.90, "UVMirage_D", "UVMirage_E"),
    jet("LibyaJetSu22M4", LY[1], LY[0], "Irn_SU22M2", "cas", "Su-22M4", "packed Irn_SU22M2", "Libyan Su-22M4.", 0.90),
    jet("LibyaJetMig21MF", LY[1], LY[0], "UVMig-21", "legacy", "MiG-21MF", "packed UVMig-21", "Libyan MiG-21MF.", 0.80, "UVMig-21_D", "UVMig-21_E"),
    jet("SyriaJetSu22", SY[1], SY[0], "Irq_SU22M3", "strike", "Su-22M3", "packed Irq_SU22M3", "Syrian Su-22M3.", 0.90),
    jet("SyriaJetSu24", SY[1], SY[0], "Irq_Su24Mk", "strike", "Su-24MK", "packed Irq_Su24Mk", "Syrian Su-24MK.", 1.00),
    jet("SyriaJetMig23", SY[1], SY[0], "MiG-23bn_Irq", "multirole", "MiG-23ML", "packed MiG-23bn_Irq", "Syrian MiG-23ML.", 0.90),
    jet("SyriaJetMig25", SY[1], SY[0], "Iraq_Mig-25bm", "interceptor", "MiG-25PD", "packed Iraq_Mig-25bm", "Syrian MiG-25PD.", 1.08),
    jet("SyriaJetMig21", SY[1], SY[0], "UVMig-21", "legacy", "MiG-21bis", "packed UVMig-21", "Syrian MiG-21bis.", 0.82, "UVMig-21_D", "UVMig-21_E"),
    jet("SyriaJetJ7", SY[1], SY[0], "LSFJ7", "legacy", "J-7", "packed LSFJ7", "Syrian J-7.", 0.84, "LSFJ7d", "LSFJ7k"),
    jet("SyriaJetSu22M4", SY[1], SY[0], "Irn_SU22M2", "cas", "Su-22M4", "packed Irn_SU22M2", "Syrian Su-22M4.", 0.90),
    jet("SyriaJetL39", SY[1], SY[0], "AVHawk", "cas", "L-39ZA", "packed AVHawk", "Syrian L-39ZA Albatros.", 0.78, "AVHawk_D", "AVHawk_D"),
    jet("SyriaJetMig21MF", SY[1], SY[0], "UVMig-21", "legacy", "MiG-21MF", "packed UVMig-21", "Syrian MiG-21MF.", 0.80, "UVMig-21_D", "UVMig-21_E"),
    jet("SouthAfricaJetCheetahC", ZA[1], ZA[0], "LSFMirage3", "a2a", "Cheetah C", "packed LSFMirage3", "SAAF Cheetah C.", 0.88, "LSFMirage3d", "LSFMirage3k"),
    jet("SouthAfricaJetCheetahD", ZA[1], ZA[0], "LSFMirage5", "strike", "Cheetah D", "packed LSFMirage5", "SAAF Cheetah D.", 0.88, "LSFMirage5d", "LSFMirage5k"),
    jet("SouthAfricaJetGripenC", ZA[1], ZA[0], "NAT_EF2000T4", "multirole", "JAS 39C Gripen", "packed NAT_EF2000T4 Gripen stand-in", "SAAF Gripen C. Closest packed euro-canard.", 0.92),
    jet("SouthAfricaJetGripenD", ZA[1], ZA[0], "LSFEUEF2000", "multirole", "JAS 39D Gripen", "packed LSFEUEF2000", "SAAF Gripen D.", 0.92, "LSFEUEF2000d", "LSFEUEF2000k"),
    jet("SouthAfricaJetHawk120", ZA[1], ZA[0], "AVHawk", "cas", "Hawk 120", "packed AVHawk", "SAAF Hawk 120.", 0.80, "AVHawk_D", "AVHawk_D"),
    jet("SouthAfricaJetImpala", ZA[1], ZA[0], "AVHawk", "cas", "Impala Mk II", "packed AVHawk_D", "SAAF Impala Mk II.", 0.78, "AVHawk_D", "AVHawk_D1"),
    jet("SouthAfricaJetBuccaneer", ZA[1], ZA[0], "LSFTornado", "strike", "Buccaneer S.50", "packed LSFTornado swing-wing stand-in", "SAAF Buccaneer S.50.", 1.02, "LSFTornadod", "LSFTornadok"),
    jet("SouthAfricaJetMirageIIICZ", ZA[1], ZA[0], "UVMirage", "interceptor", "Mirage IIICZ", "packed UVMirage", "SAAF Mirage IIICZ.", 0.86, "UVMirage_D", "UVMirage_E"),
    jet("SouthAfricaJetCheetahE", ZA[1], ZA[0], "LSFMirage2000", "multirole", "Cheetah E", "packed LSFMirage2000", "SAAF Cheetah E.", 0.90, "LSFMirage2000d", "LSFMirage2000k"),
    jet("SouthAfricaJetGripenE", ZA[1], ZA[0], "NVJ31", "a2a", "JAS 39E Gripen", "packed NVJ31 Gripen-E stand-in", "SAAF Gripen E near-future.", 0.94, "NVJ31_D", "NVJ31_E"),
    jet("SouthKoreaJetF15K", SK[1], SK[0], "LSFF15K", "strike", "F-15K Slam Eagle", "DONOR_ART LSFF15K unused unique", "ROKAF F-15K.", 1.06, "LSFF15Kd", "LSFF15Kd", "LSFF15K.dds"),
    jet("SouthKoreaJetF16C", SK[1], SK[0], "US_F16CJ_blk52", "multirole", "F-16C", "packed US_F16CJ_blk52", "ROKAF F-16C.", 0.88),
    jet("SouthKoreaJetF16D", SK[1], SK[0], "US_F16D_B52", "multirole", "F-16D", "packed US_F16D_B52", "ROKAF F-16D.", 0.88),
    jet("SouthKoreaJetKF16", SK[1], SK[0], "LSFKF16", "strike", "KF-16", "packed LSFKF16", "ROKAF KF-16.", 0.88, "LSFKF16d", "LSFKF16d"),
    jet("SouthKoreaJetF35A", SK[1], SK[0], "LSFUSAF35A", "stealth", "F-35A", "packed LSFUSAF35A", "ROKAF F-35A.", 0.90, "LSFUSAF35Ad", "LSFUSAF35Ak"),
    jet("SouthKoreaJetKF21", SK[1], SK[0], "LSFJ31", "a2a", "KF-21 Boramae", "packed LSFJ31 KF-21 stand-in", "ROKAF KF-21 Boramae.", 0.94, "LSFJ31d", "LSFJ31k"),
    jet("SouthKoreaJetFA50", SK[1], SK[0], "AVHawk", "cas", "FA-50", "packed AVHawk FA-50 stand-in", "ROKAF FA-50 Fighting Eagle.", 0.82, "AVHawk_D", "AVHawk_D"),
    jet("SouthKoreaJetF4E", SK[1], SK[0], "JPF4", "legacy", "F-4E Phantom", "packed JPF4", "ROKAF F-4E.", 0.98, "JPF4D", "JPF4K"),
    jet("SouthKoreaJetF5E", SK[1], SK[0], "AVHawk", "cas", "F-5E Tiger II", "packed AVHawk_D", "ROKAF F-5E.", 0.78, "AVHawk_D", "AVHawk_D1"),
    jet("SouthKoreaJetKF21Blk2", SK[1], SK[0], "NVJ31", "stealth", "KF-21 Block 2", "packed NVJ31", "ROKAF KF-21 Block 2.", 0.96, "NVJ31_D", "NVJ31_E"),
    jet("SouthKoreaJetF15KSlam", SK[1], SK[0], "US_F15E", "strike", "F-15K", "packed US_F15E second F-15K mesh", "ROKAF F-15K Slam Eagle strike-configured.", 1.05, "US_F15E_D", "US_F15E_R"),
    jet("SouthKoreaJetT50", SK[1], SK[0], "AVHawk", "cas", "T-50 Golden Eagle", "packed AVHawk_P", "ROKAF T-50.", 0.80, "AVHawk_P", "AVHawk_D"),
    jet("NorthKoreaJetMig21", NK[1], NK[0], "UVMig-21", "legacy", "MiG-21bis", "packed UVMig-21", "KPAF MiG-21bis.", 0.82, "UVMig-21_D", "UVMig-21_E"),
    jet("NorthKoreaJetMig23", NK[1], NK[0], "MiG-23bn_Irq", "multirole", "MiG-23ML", "packed MiG-23bn_Irq", "KPAF MiG-23ML.", 0.90),
    jet("NorthKoreaJetJ7", NK[1], NK[0], "LSFJ7", "legacy", "J-7", "packed LSFJ7", "KPAF J-7.", 0.84, "LSFJ7d", "LSFJ7k"),
    jet("NorthKoreaJetSu22", NK[1], NK[0], "Irn_SU22M2", "strike", "Su-22", "packed Irn_SU22M2", "KPAF Su-22.", 0.90),
    jet("NorthKoreaJetMig21PF", NK[1], NK[0], "UVMig-21", "interceptor", "MiG-21PF", "packed UVMig-21", "KPAF MiG-21PF.", 0.80, "UVMig-21_D", "UVMig-21_E"),
    jet("NorthKoreaJetJ7B", NK[1], NK[0], "LSFJ7", "legacy", "J-7B", "packed LSFJ7", "KPAF J-7B.", 0.82, "LSFJ7d", "LSFJ7k"),
    jet("NorthKoreaJetSu25UB", NK[1], NK[0], "RUSU-25", "cas", "Su-25UB", "packed RUSU-25", "KPAF Su-25UB.", 0.90, "RUSU-25_D", "RUSU-25_E"),
    jet("NorthKoreaJetMig29UB", NK[1], NK[0], "LSFruMiG29", "a2a", "MiG-29UB", "packed LSFruMiG29", "KPAF MiG-29UB.", 0.88, "LSFruMiG29d", "LSFruMiG29k"),
    jet("NorthKoreaJetMig23BN", NK[1], NK[0], "MiG-23bn_Irq", "cas", "MiG-23BN", "packed MiG-23bn_Irq", "KPAF MiG-23BN.", 0.92),
    jet("NorthKoreaJetSu22M4", NK[1], NK[0], "Irq_SU22M3", "strike", "Su-22M4", "packed Irq_SU22M3", "KPAF Su-22M4.", 0.90),
    jet("VietnamJetMig21", VN[1], VN[0], "LSFIDMig21", "legacy", "MiG-21bis", "packed LSFIDMig21", "VPAF MiG-21bis.", 0.84, "LSFIDMig21d", "LSFIDMig21d"),
    jet("VietnamJetSu22", VN[1], VN[0], "Irq_SU22M3", "strike", "Su-22M3", "packed Irq_SU22M3", "VPAF Su-22M3.", 0.90),
    jet("VietnamJetSu27", VN[1], VN[0], "LSFRUSU27SK", "a2a", "Su-27SK", "packed LSFRUSU27SK", "VPAF Su-27SK.", 0.98, "LSFRUSU27SKd", "LSFRUSU27SKk"),
    jet("VietnamJetSu30", VN[1], VN[0], "RUS_SU30SM2", "multirole", "Su-30MK2", "packed RUS_SU30SM2", "VPAF Su-30MK2.", 0.96),
    jet("VietnamJetSu22M4", VN[1], VN[0], "Irn_SU22M2", "cas", "Su-22M4", "packed Irn_SU22M2", "VPAF Su-22M4.", 0.90),
    jet("VietnamJetYak130", VN[1], VN[0], "AVHawk", "cas", "Yak-130", "packed AVHawk", "VPAF Yak-130.", 0.82, "AVHawk_D", "AVHawk_D"),
    jet("VietnamJetMig21bis", VN[1], VN[0], "UVMig-21", "legacy", "MiG-21MF", "packed UVMig-21", "VPAF MiG-21MF.", 0.80, "UVMig-21_D", "UVMig-21_E"),
    jet("VietnamJetSu27UB", VN[1], VN[0], "LSFSU35", "a2a", "Su-27UBK", "packed LSFSU35", "VPAF Su-27UBK.", 0.98, "LSFSU35d", "LSFSU35k"),
    jet("VietnamJetSu30MK2", VN[1], VN[0], "RUSU30", "strike", "Su-30MK2V", "packed RUSU30", "VPAF Su-30MK2V.", 0.94, "RUSU30d", "RUSU30d", "RUSU30MKK.dds"),
    jet("VietnamJetL39", VN[1], VN[0], "AVHawk", "cas", "L-39", "packed AVHawk_D", "VPAF L-39.", 0.78, "AVHawk_D", "AVHawk_D1"),
    jet("VietnamJetF5E", VN[1], VN[0], "AVHawk", "cas", "F-5E", "packed AVHawk_P captured RVNAF F-5", "VPAF captured F-5E.", 0.80, "AVHawk_P", "AVHawk_D"),
    jet("IraqJetF16IQ", IQ[1], IQ[0], "US_F16CJ_blk52", "multirole", "F-16IQ", "packed US_F16CJ_blk52", "IQAF F-16IQ.", 0.88),
    jet("IraqJetMig21", IQ[1], IQ[0], "UVMig-21", "legacy", "MiG-21bis", "packed UVMig-21", "IQAF MiG-21bis.", 0.82, "UVMig-21_D", "UVMig-21_E"),
    jet("IraqJetL159", IQ[1], IQ[0], "AVHawk", "cas", "L-159 / Tucano-class", "packed AVHawk light attack", "IQAF light attack jet.", 0.80, "AVHawk_D", "AVHawk_D"),
    jet("IraqJetSu25UB", IQ[1], IQ[0], "RUSU-25", "cas", "Su-25UB", "packed RUSU-25", "IQAF Su-25UB.", 0.90, "RUSU-25_D", "RUSU-25_E"),
    jet("ArabJetMirage2000", GL[1], GL[0], "LSFMirage2000", "multirole", "Mirage 2000", "packed LSFMirage2000", "GLA coalition Mirage 2000.", 0.90, "LSFMirage2000d", "LSFMirage2000k"),
    jet("ArabJetMig29", GL[1], GL[0], "Irq_Mig29A", "a2a", "MiG-29", "packed Irq_Mig29A", "GLA coalition MiG-29.", 0.88),
    jet("ArabJetSu25", GL[1], GL[0], "Irq_Su25k", "cas", "Su-25", "packed Irq_Su25k", "GLA coalition Su-25.", 0.90),
    jet("ArabJetMirageF1", GL[1], GL[0], "Irq_MirageF1_Bq", "strike", "Mirage F1", "packed Irq_MirageF1_Bq", "GLA coalition Mirage F1.", 0.88),
    jet("TurkeyJetRF4E", TR[1], TR[0], "JPF4", "strike", "RF-4E Phantom", "packed JPF4", "Turkish RF-4E reconnaissance-strike Phantom.", 0.96, "JPF4D", "JPF4K"),
    jet("SwedenJetSK60B", SE[1], SE[0], "AVHawk", "cas", "SK 60B", "packed AVHawk_P", "Flygvapnet SK 60B.", 0.76, "AVHawk_P", "AVHawk_D"),
    jet("SwedenJetGripenA", SE[1], SE[0], "NAT_EF2000T4", "a2a", "JAS 39A Gripen", "packed NAT_EF2000T4 early Gripen family", "Flygvapnet JAS 39A. Same canard family as 39C, smaller scale.", 0.88),
    jet("SouthAfricaJetHawk127", ZA[1], ZA[0], "AVHawk", "cas", "Hawk 127", "packed AVHawk_P", "SAAF Hawk 127 lead-in fighter.", 0.80, "AVHawk_P", "AVHawk_D"),
    jet("SaudiJetF5E", SA[1], SA[0], "AVHawk", "cas", "F-5E Tiger II", "packed AVHawk_D", "RSAF F-5E Tiger II.", 0.78, "AVHawk_D", "AVHawk_D1"),
    jet("UAEJetMirage20005", AE[1], AE[0], "LSFMirage5", "multirole", "Mirage 2000-5", "packed LSFMirage5", "UAE Mirage 2000-5.", 0.90, "LSFMirage5d", "LSFMirage5k"),
]

assert len(AIRCRAFT) == len({a["obj"] for a in AIRCRAFT}), "duplicate new object"


WEAPONS = "; SPECTER final global airforce roster weapons. Wrappers over packed projectiles.\n" + "\n".join(a["wpn_defs"] for a in AIRCRAFT)

CSF_LABELS = {}
for a in AIRCRAFT:
    CSF_LABELS[f"CONTROLBAR:Construct{a['obj']}"] = a["identity"]
    CSF_LABELS[f"CONTROLBAR:ToolTip{a['obj']}"] = a["note"][:120]
    CSF_LABELS[f"OBJECT:{a['obj']}"] = a["identity"]

# Re-identify existing clone NATO names that become country-real on fighter pads.
CSF_RELABEL = {
    "CONTROLBAR:ConstructSwedenJetEF2000T4": "JAS 39C Gripen",
    "CONTROLBAR:ToolTipSwedenJetEF2000T4": "Swedish JAS 39C Gripen. Canard eurofighter stand-in mesh.",
    "OBJECT:SwedenJetEF2000T4": "JAS 39C Gripen",
    "CONTROLBAR:ConstructSwedenJetEF2000T4_AA": "JAS 39C MS20",
    "CONTROLBAR:ToolTipSwedenJetEF2000T4_AA": "Swedish JAS 39C MS20 air-superiority load.",
    "OBJECT:SwedenJetEF2000T4_AA": "JAS 39C MS20",
    "CONTROLBAR:ConstructSwedenJetEF2000T4_CAS": "JAS 39C CAS",
    "CONTROLBAR:ToolTipSwedenJetEF2000T4_CAS": "Swedish JAS 39C strike/CAS load.",
    "OBJECT:SwedenJetEF2000T4_CAS": "JAS 39C CAS",
    "CONTROLBAR:ConstructItalyJetEF2000T4": "Typhoon T1",
    "OBJECT:ItalyJetEF2000T4": "Typhoon T1",
    "CONTROLBAR:ToolTipItalyJetEF2000T4": "Italian Typhoon Tranche 1. Distinct NAT_EF2000T4 mesh.",
    "CONTROLBAR:ConstructNatoJetF35C": "F-35A",
    "OBJECT:NatoJetF35C": "F-35A",
    "CONTROLBAR:ToolTipNatoJetF35C": "NATO F-35A Lightning II.",
    "CONTROLBAR:ConstructIraq_Mig25RB": "MiG-25RB",
    "OBJECT:Iraq_Mig25RB": "MiG-25RB",
    "CONTROLBAR:ToolTipIraq_Mig25RB": "Iraqi MiG-25RB interceptor-reconnaissance Foxbat.",
    "CONTROLBAR:ConstructIraq_IL-76": "Il-76",
    "OBJECT:Iraq_IL-76": "Il-76",
    "CONTROLBAR:ToolTipIraq_IL-76": "Iraqi Il-76 transport.",
    "CONTROLBAR:ConstructLibya_L_170E_FakeRCS_Mig27": "MiG-23BN",
    "OBJECT:Libya_L_170E_FakeRCS_Mig27": "MiG-23BN",
}

CSF_LABELS.update(CSF_RELABEL)

PORTRAIT_SRC = {a["portrait"] + ".tga": a["portrait_src"] for a in AIRCRAFT}


def buttons_text() -> str:
    chunks = ["; SPECTER final global roster construct buttons. Inlined into CommandSet.ini."]
    for a in AIRCRAFT:
        chunks.append(
            f"CommandButton Command_Construct{a['obj']}\n"
            f"  Command          = UNIT_BUILD\n"
            f"  Object           = {a['obj']}\n"
            f"  TextLabel        = CONTROLBAR:Construct{a['obj']}\n"
            f"  ButtonImage      = {a['portrait']}\n"
            f"  ButtonBorderType = BUILD\n"
            f"  DescriptLabel    = CONTROLBAR:ToolTip{a['obj']}\n"
            f"End\n"
        )
    return "\n".join(chunks)


def mapped_text() -> str:
    chunks = ["; Unique Specter final-roster portraits."]
    for a in AIRCRAFT:
        chunks.append(
            f"MappedImage {a['portrait']}\n"
            f"  Texture = {a['portrait']}.tga\n"
            f"  TextureWidth = 150\n"
            f"  TextureHeight = 113\n"
            f"  Coords = Left:0 Top:0 Right:150 Bottom:113\n"
            f"  Status = NONE\n"
            f"End\n"
        )
    return "\n".join(chunks)


# Fighter menus: exactly 12 combat jets. Support types belong on Heavy.
FIGHTER_MENUS = {
    "FranceAirfieldCommandSet": [
        "FranceJetRafaleC", "FranceJetRafaleB", "FranceJetRafaleM", "FranceJetRafaleF4",
        "FranceJetRafaleF3", "FranceJetMirage20005F", "FranceJetMirage2000", "FranceJetMirage2000D",
        "FranceJetMirageF1CT", "FranceJetMirageIIIE", "FranceJetMirage5", "FranceJetFCASNGF",
    ],
    "GermanyAirfieldCommandSet": [
        "GermanyJetTyphoonT4", "GermanyJetTyphoonT1", "GermanyJetTyphoonECR", "GermanyJetTornadoADV",
        "GermanyJetF35A", "GermanyJetMiG29G", "GermanyJetTornadoIDS", "GermanyJetTornadoECR",
        "GermanyJetF4F", "GermanyJetAlphaJet", "GermanyJetMako", "GermanyJetFCASNGF",
    ],
    "ItalyAirfieldCommandSet": [
        "ItalyJetTyphoon", "ItalyJetEF2000T4", "ItalyJetF35A", "ItalyJetF35B",
        "ItalyJetTornadoIDS", "ItalyJetTornadoECR", "ItalyJetAMX", "ItalyJetHarrierII",
        "ItalyJetF16", "ItalyJetGCAP", "ItalyJetM346FA", "ItalyJetMB339",
    ],
    "BritainAirfieldCommandSet": [
        "BritainJetF35B", "BritainJetTyphoonFGR4", "BritainJetTyphoonT3", "BritainJetTempest",
        "BritainJetTornadoF3", "BritainJetTornadoGR4", "BritainJetHarrierGR9", "BritainJetSeaHarrierFA2",
        "BritainJetPhantomFG1", "BritainJetJaguarGR3", "BritainJetLightningF6", "BritainJetHawk200",
    ],
    "Japan_AirfieldCommandSet": [
        "JapanJetF15JKai", "JapanJetF15J", "JapanJetF15DJ", "JapanJetF2A",
        "JapanJetF2B", "JapanJetF2Kai", "JapanJetF4EJKai", "JapanJetX2Shinshin",
        "JapanJetF35A", "JapanJetF35B", "JapanJetFX", "JapanJetF3",
    ],
    "TurkeyAirfieldCommandSet": [
        "TurkeyJetKAAN", "TurkeyJetKAANBlk2", "TurkeyJetF16C", "TurkeyJetF16Ozgur",
        "TurkeyJetF16DBlk52", "TurkeyJetF16Blk30", "TurkeyJetF4ETerm", "TurkeyJetF4E",
        "TurkeyJetRF4E", "TurkeyJetF35A", "TurkeyJetHurjet", "TurkeyJetNF5",
    ],
    "IranExpandedAirfieldCommandSet": [
        "IranJetF14A", "IranJetF14AM", "IranJetF4E", "IranJetMig29A",
        "IranJetMig21Bis", "IranJetF7N", "IranJetSU22", "IranJetSU24M",
        "IranJetSU25K", "IranJetSu35S", "IranJetJ10CE", "IranJetSu57E",
    ],
    "Pakistan_AirfieldCommandSet": [
        "PakistanJetF16AMLU", "Pakistan_F16Blk52", "PakistanJetF16B", "PakistanJetJ10CE",
        "PakistanJetJF17", "PakistanJetJF17Blk3", "PakistanJetF7PG", "PakistanJetF7P",
        "PakistanJetMirage3", "PakistanJetMirage5", "PakistanJetMirageROSE", "PakistanJetA5C",
    ],
    "India_AirfieldCommandSet": [
        "IndiaJetSu30MKI", "India_Mig-29A", "IndiaJetMig29K", "IndiaJetRafaleEH",
        "IndiaJetRafaleDH", "IndiaJetMirage2000H", "IndiaJetMirage2000I", "IndiaJetMig21Bison",
        "IndiaJetJaguarIS", "IndiaJetMig27", "IndiaJetTejas", "IndiaJetAMCA",
    ],
    "Israel_LargeAirBaseCommandSet": [
        "IsraelJetF35I_AA", "IsraelJetF35IAdirPenetrator", "IsraelJetF16ISufaPrecision", "Israel_F16I_AG",
        "IsraelJetF16CBarak", "IsraelJetF15CBaz", "Israel_F15I_AA", "IsraelJetF15IRaamII",
        "IsraelJetKfir", "IsraelJetNesher", "IsraelJetF4E", "IsraelJetF15IRaamDeepStrike",
    ],
    "SaudiArabia_AirfieldCommandSet": [
        "SaudiJetF15S", "SaudiJetF15SA", "SaudiJetF15C", "SaudiJetF15EX",
        "SaudiJetTyphoon", "SaudiJetTyphoonT3", "SaudiJetTornadoIDS", "SaudiJetTornadoADV",
        "SaudiJetTornadoECR", "SaudiJetHawk65", "SaudiJetLightning", "SaudiJetF5E",
    ],
    "NatoAirfieldCommandSet": [
        "NatoJetF18A", "NatoJetF18C", "NatoJetF18E", "NatoJetF18F",
        "NatoJetEA18G", "NatoJetF35C", "NatoJetF35B", "NatoJetEF2000T4",
        "NatoJetF16C", "NatoJetF16DBlk52", "NatoJetRafaleF3", "NatoJetTornadoIDS",
    ],
    "SwedenAirfieldCommandSet": [
        "SwedenJetGripenA", "SwedenJetEF2000T4", "SwedenJetEF2000T4_AA", "SwedenJetGripenE",
        "SwedenJetEF2000T4_CAS", "SwedenJetViggenJA37", "SwedenJetViggenAJS37", "SwedenJetViggenSH",
        "SwedenJetDrakenJ35", "SwedenJetLansenJ32", "SwedenJetSK60", "SwedenJetSK60B",
    ],
    "UkraineAirfieldCommandSet": [
        "UkraineJetMig29", "UkraineJetMig29MU1", "UkraineJetSu27", "UkraineJetSu27UB",
        "UkraineJetF16AM", "UkraineJetF16DBlk52", "UkraineJetMirage2000", "UkraineJetSu24M",
        "UkraineJetSu24MR", "UkraineJetSu25", "UkraineJetSu25M1", "UkraineJetMig21",
    ],
    "UAE_AirfieldCommandSet": [
        "UAEJetF16E", "UAEJetF16ECegy", "UAE_F16Blk52", "UAEJetF16F",
        "UAEJetMirage20009", "UAEJetMirage20009E", "UAEJetMirage2000DAD", "UAEJetF15EA",
        "UAEJetF15E", "UAEJetF15SA", "UAEJetHawk102", "UAEJetMirage20005",
    ],
    "Libya_AirfieldCommandSet": [
        "Libya_Mig-29A", "Libya_MirageF1_Bq", "LibyaJetMirageF1BD", "LibyaJetMig23",
        "LibyaJetMig25", "LibyaJetMig21", "LibyaJetMig21MF", "LibyaJetJ7",
        "LibyaJetSu22", "LibyaJetSu22M4", "Libya_Su-25K", "LibyaJetSu24",
    ],
    "Syria_AirfieldCommandSet": [
        "Syria_Mig-29A", "Syria_MirageF1_Bq", "SyriaJetMig23", "SyriaJetMig25",
        "SyriaJetMig21", "SyriaJetMig21MF", "SyriaJetJ7", "SyriaJetSu22",
        "SyriaJetSu22M4", "Syria_Su-25K", "SyriaJetSu24", "SyriaJetL39",
    ],
    "SouthAfrica_AirfieldCommandSet": [
        "SouthAfrica_MirageF1_Bq", "SouthAfricaJetMirageIIICZ", "SouthAfricaJetCheetahC", "SouthAfricaJetCheetahD",
        "SouthAfricaJetCheetahE", "SouthAfricaJetGripenC", "SouthAfricaJetGripenD", "SouthAfricaJetGripenE",
        "SouthAfricaJetHawk120", "SouthAfricaJetHawk127", "SouthAfricaJetImpala", "SouthAfricaJetBuccaneer",
    ],
    "SouthKorea_AirfieldCommandSet": [
        "SouthKoreaJetF15K", "SouthKoreaJetF15KSlam", "SouthKoreaJetF16C", "SouthKoreaJetF16D",
        "SouthKoreaJetKF16", "SouthKoreaJetF35A", "SouthKoreaJetKF21", "SouthKoreaJetKF21Blk2",
        "SouthKoreaJetFA50", "SouthKoreaJetT50", "SouthKoreaJetF4E", "SouthKoreaJetF5E",
    ],
    "NorthKorea_AirfieldCommandSet": [
        "NorthKoreaJetMig29S", "NorthKoreaJetMig29UB", "NorthKoreaJetMig21", "NorthKoreaJetMig21PF",
        "NorthKoreaJetMig23", "NorthKoreaJetMig23BN", "NorthKoreaJetJ7", "NorthKoreaJetJ7B",
        "NorthKoreaJetSu22", "NorthKoreaJetSu22M4", "NorthKoreaJetSu25T", "NorthKoreaJetSu25UB",
    ],
    "Vietnam_AirfieldCommandSet": [
        "VietnamJetMig29S", "VietnamJetMig21", "VietnamJetMig21bis", "VietnamJetSu22",
        "VietnamJetSu22M4", "VietnamJetSu27", "VietnamJetSu27UB", "VietnamJetSu30",
        "VietnamJetSu30MK2", "VietnamJetYak130", "VietnamJetL39", "VietnamJetF5E",
    ],
    "Iraq_AirfieldCommandSet": [
        "IraqJetF16IQ", "Iraq_Mig-29A", "Iraq_Mig-25BM", "Iraq_Mig-23ML",
        "IraqJetMig21", "Iraq_MirageF1_Bq", "Iraq_Su-22M3", "Iraq_Su-24MK",
        "Iraq_Su-25K", "IraqJetSu25UB", "IraqJetL159", "Iraq_Mig25RB",
    ],
    "ArabicAirfieldCommandSet": [
        "ArabicArmy_F15SA", "ArabicArmy_F15SA_AA", "ArabicArmy_F16C_E", "ArabJetEF2000AA",
        "ArabicArmy_EF2000", "ArabicArmy_Su35", "ArabicArmy_Su30MKA", "ArabicArmy_Rafale_DM",
        "Arab_Su-24MK", "ArabicArmy_Su-24MR", "ArabJetMirage2000", "ArabJetMig29",
    ],
}

# Duplicate fighter menus onto Large copies and numbered upgrade copies.
FIGHTER_MENU_COPIES = {
    "FranceAirfieldCommandSet": ["France_LargeAirBaseCommandSet"],
    "GermanyAirfieldCommandSet": ["Germany_LargeAirBaseCommandSet"],
    "ItalyAirfieldCommandSet": ["Italy_LargeAirBaseCommandSet"],
    "BritainAirfieldCommandSet": ["Britain_LargeAirBaseCommandSet"],
    "Japan_AirfieldCommandSet": ["Japan_AirfieldCommandSet"],  # Large shares this set
    "TurkeyAirfieldCommandSet": ["Turkey_LargeAirBaseCommandSet"],
    "IranExpandedAirfieldCommandSet": ["IranExpandedAirfieldCommandSet"],  # Large shares
    "Pakistan_AirfieldCommandSet": ["Pakistan_AirfieldCommandSet1", "Pakistan_AirfieldCommandSet2", "Pakistan_AirfieldCommandSet3"],
    "India_AirfieldCommandSet": ["India_AirfieldCommandSet1", "India_AirfieldCommandSet2", "India_AirfieldCommandSet3"],
    "SaudiArabia_AirfieldCommandSet": ["SaudiArabia_AirfieldCommandSet1", "SaudiArabia_AirfieldCommandSet2", "SaudiArabia_AirfieldCommandSet3"],
    "NatoAirfieldCommandSet": ["Nato_LargeAirBaseCommandSet"],
    "SwedenAirfieldCommandSet": ["Sweden_LargeAirBaseCommandSet"],
    "UkraineAirfieldCommandSet": ["Ukraine_LargeAirBaseCommandSet"],
    "UAE_AirfieldCommandSet": ["UAE_AirfieldCommandSet1", "UAE_AirfieldCommandSet2", "UAE_AirfieldCommandSet3"],
    "Libya_AirfieldCommandSet": ["Libya_AirfieldCommandSet1", "Libya_AirfieldCommandSet2", "Libya_AirfieldCommandSet3"],
    "Syria_AirfieldCommandSet": ["Syria_AirfieldCommandSet1", "Syria_AirfieldCommandSet2", "Syria_AirfieldCommandSet3"],
    "SouthAfrica_AirfieldCommandSet": ["SouthAfrica_AirfieldCommandSet1", "SouthAfrica_AirfieldCommandSet2", "SouthAfrica_AirfieldCommandSet3"],
}

HEAVY_MENUS = {
    "France_HeavyAirBaseCommandSet": [
        "FranceJetC130", "FranceAircraftE3", "FranceUCAVNeuron", "FranceHelicopterTiger",
        "FranceHelicopterNH90", "FranceHelicopterCaracal", "FranceJetMirageF1CR",
    ],
    "Germany_HeavyAirBaseCommandSet": [
        "GermanyJetA400M", "GermanyJetC130J", "GermanyAircraftE3", "GermanyDroneHeronTP",
        "GermanyUAVEuroMALE", "GermanyHelicopterTigerUHT", "GermanyHelicopterNH90",
        "GermanyHelicopterCH53", "GermanyHelicopterH145M",
    ],
    "Italy_HeavyAirBaseCommandSet": [
        "ItalyJetC130J", "ItalyJetC27J", "ItalyAircraftG550CAEW", "ItalyDroneMQ9",
        "ItalyHelicopterAW249", "ItalyHelicopterA129", "ItalyHelicopterNH90",
        "ItalyHelicopterAW101", "ItalyHelicopterAW139",
    ],
    "Britain_HeavyAirBaseCommandSet": [
        "BritainJetA400M", "BritainJetC17", "BritainAircraftE7", "BritainDroneMQ9",
        "BritainBomberVulcan", "BritainHelicopterApache", "BritainHelicopterChinook",
        "BritainHelicopterMerlin", "BritainHelicopterWildcat", "BritainHelicopterPuma",
        "BritainJetPhantomFGR2", "BritainAircraftTornadoECR",
    ],
    "Japan_HeavyAirBaseCommandSet": [
        "JapanJetC130H", "JapanUAVRQ4",
    ],
    "Turkey_HeavyAirBaseCommandSet": [
        "TurkeyJetE3AAWACS", "TurkeyHelicopterAH64E", "TurkeyHelicopterUH60", "TurkeyHelicopterCH47F",
    ],
    "Iran_HeavyAirBaseCommandSet": [
        "IranHelicopterPanha2091", "IranHelicopterMi8", "IranJetSu47Berkut",
    ],
    "Pakistan_HeavyAirBaseCommandSet": [
        "Pakistan_Mi-8T", "Pakistan_IL-76",
    ],
    "India_HeavyAirBaseCommandSet": [
        "India_Mi-8T", "India_IL-76",
    ],
    "Israel_HeavyAirBaseCommandSet": [
        "IsraelJetF15BazHeavyBomber", "IsraelJetG550Eitam",
    ],
    "SaudiArabia_HeavyAirBaseCommandSet": [
        "SaudiArabia_Mi-8T", "SaudiArabia_IL-76",
    ],
    "Nato_HeavyAirBaseCommandSet": [
        "NatoJetE3AAWACS", "NatoHelicopterAH64E", "NatoHelicopterUH60", "NatoHelicopterCH47F",
    ],
    "Sweden_HeavyAirBaseCommandSet": [
        "SwedenJetE3AAWACS", "SwedenHelicopterCH47F", "SwedenHelicopterUH60", "SwedenHelicopterAH64E",
    ],
    "Ukraine_HeavyAirBaseCommandSet": [
        "UkraineJetE3AAWACS", "UkraineHelicopterCH47F", "UkraineHelicopterUH60", "UkraineHelicopterAH64E",
    ],
    "UAE_HeavyAirBaseCommandSet": [
        "UAE_IL-76", "UAE_Mi-8T",
    ],
    "Libya_HeavyAirBaseCommandSet": [
        "Libya_Mi-8T", "Libya_IL-76",
    ],
    "Syria_HeavyAirBaseCommandSet": [
        "Syria_Mi-8T", "Syria_IL-76",
    ],
    "SouthAfrica_HeavyAirBaseCommandSet": [
        "SouthAfrica_Mi-8T", "SouthAfrica_IL-76",
    ],
    "SouthKorea_HeavyAirBaseCommandSet": [
        "SouthKoreaHelicopterWZ10ME", "SouthKoreaHelicopterMi28N", "SouthKoreaHelicopterKa52M",
    ],
    "NorthKorea_HeavyAirBaseCommandSet": [
        "NorthKoreaHelicopterWZ10ME", "NorthKoreaHelicopterMi28N", "NorthKoreaHelicopterKa52M",
    ],
    "Vietnam_HeavyAirBaseCommandSet": [
        "VietnamHelicopterWZ10ME", "VietnamHelicopterMi28N", "VietnamHelicopterKa52M",
    ],
    "Iraq_HeavyAirBaseCommandSet": [
        "Iraq_Tu-22M3", "Iraq_Tu-22M3_AI", "Iraq_Su-24MR", "Iraq_Mi-35M3",
        "Iraq_Mi-28NE", "Iraq_Mi-8T", "Iraq_IL-76",
    ],
    "Iraq_LargeAirBaseCommandSet": [
        "IraqJetF16IQ", "Iraq_Mig-29A", "Iraq_Mig-25BM", "Iraq_Mig-23ML",
        "IraqJetMig21", "Iraq_MirageF1_Bq", "Iraq_Su-22M3", "Iraq_Su-24MK",
        "Iraq_Su-25K", "IraqJetSu25UB", "IraqJetL159", "Iraq_Mig25RB",
    ],
}

# Fix Turkey duplicate F16Blk30 x2 - replace 12th with ArabJetSu25? No that's GLA.
# Turkey slot 12 should be unique: use TurkeyJetNF5 only once. Slot 11 NF5 slot 12 need unique.
# I'll fix Turkey list: last should not duplicate Blk30. Use existing TurkeyJetF35C as 2nd F-35? Bad.
# 12th unique: keep Hurjet and NF5, drop second Blk30. Need another jet.
# Add TurkeyJetRF4 using JPF4 - 3rd F-4. Replace duplicate in post.

# Iran old AirfieldCommandSet - building uses Expanded; still rewrite both.
FIGHTER_MENU_COPIES["IranExpandedAirfieldCommandSet"] = ["IranAirfieldCommandSet"]

# GLA extra 4 jets: ArabJetSu25 not in 12. 12 uses ArabJetMig29 and ArabJetMirage2000. Good. ArabJetSu25 unused OK.

# Arabic remaining ArabJetSu25 not slotted - OK.

# Expand copies that Large shares same name: Japan Large uses Japan_AirfieldCommandSet - already the primary.
# Iran Large uses IranExpandedAirfieldCommandSet - primary.
# India Large uses India_AirfieldCommandSet - primary.
# Pakistan Large uses Pakistan_AirfieldCommandSet - primary.
# SK Large uses SouthKorea_AirfieldCommandSet - primary.
# etc.

# NorthKorea/Vietnam/SK Large share Airfield set - primary rewrite is enough.

FIGHTER_MENU_COPIES["Israel_LargeAirBaseCommandSet"] = ["Israel_AirfieldCommandSet"]
FIGHTER_MENU_COPIES["ArabicAirfieldCommandSet"] = [
    "ArabicAirfieldCommandSet_T", "ArabicAirfieldCommandSet_T1",
    "ArabicAirfieldCommandSet_T2", "ArabicAirfieldCommandSet_T3",
]


def main() -> None:
    w(INI / "Weapon_FinalGlobalAirforceRoster.ini", WEAPONS)
    w(INI / "CommandButton_FinalGlobalAirforceRoster.ini", buttons_text())
    w(MAP / "zFinalGlobal_AirbasePortrait_Images.INI", mapped_text())
    for spec in AIRCRAFT:
        body = fighter(
            spec["obj"], spec["side"], spec["portrait"], spec["model"], spec["model_d"], spec["model_k"],
            spec["wpn_block"], spec["cost"], spec["time"], spec["hp"], spec["scale"], spec["vision"], spec["note"],
        )
        w(ROOT / spec["rel"], body)
    print(f"wrote {len(AIRCRAFT)} roster aircraft")
    for name, objs in FIGHTER_MENUS.items():
        if len(objs) != 12:
            raise SystemExit(f"{name} has {len(objs)} fighters")
        if len(set(objs)) != 12:
            raise SystemExit(f"{name} duplicate fighters {objs}")
    print("fighter menus 12/12 unique PASS")


if __name__ == "__main__":
    main()
