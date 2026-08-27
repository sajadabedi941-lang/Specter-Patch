#!/usr/bin/env python3
"""Overlay INI for unused unique DONOR_ART aircraft W3Ds. Visual donor only."""
from __future__ import annotations

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
w = g.w

METEOR = g.METEOR
AIM9 = g.AIM9
R77 = g.R77
GBU = g.GBU
FAB = g.FAB
CRUISE = g.CRUISE
KH31 = g.KH31
PAVE = g.PAVE

WEAPONS = "\n".join(
    [
        "; SPECTER unused-donor aircraft weapons. Wrappers over packed projectiles.",
        a2a("Pakistan_Weapon_AIM120_F16AMLU", 780, 1100, 4, 920, METEOR),
        a2a("Pakistan_Weapon_AIM9_F16AMLU", 640, 500, 2, 700, AIM9),
        a2g("Pakistan_Weapon_Bomb_F16AMLU", 700, 32, 720, 4, 800, FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation"),
        a2a("Japan_Weapon_AAM4B_F15J", 940, 1480, 8, 780, METEOR),
        a2a("Japan_Weapon_AAM5_F15JBase", 800, 600, 4, 620, AIM9),
        cannon("Japan_Weapon_Cannon_F15JBase", 40),
        a2a("Israel_Weapon_AMRAAM_F15C", 900, 1420, 6, 820, METEOR),
        a2a("Israel_Weapon_Python_F15C", 760, 560, 4, 640, AIM9),
        cannon("Israel_Weapon_Cannon_F15C", 32),
        a2a("France_Weapon_Meteor_FCAS", 980, 1520, 4, 900, METEOR),
        a2a("France_Weapon_MICA_FCAS", 800, 820, 2, 700, METEOR),
        a2g("France_Weapon_AASM_FCAS", 880, 30, 840, 2, 1600, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1800),
        a2a("Saudi_Weapon_AIM120_F15S", 860, 1280, 2, 950, METEOR),
        a2a("Saudi_Weapon_AIM9_F15S", 700, 520, 2, 720, AIM9),
        a2g("Saudi_Weapon_GBU_F15S", 980, 40, 900, 8, 700, GBU, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation", 1000),
        a2a("India_Weapon_R77_Su30MKI", 900, 1360, 6, 840, R77),
        a2a("India_Weapon_R73_Su30MKI", 760, 540, 2, 660, AIM9),
        a2g("India_Weapon_Kh59_Su30MKI", 1100, 50, 1280, 2, 2800, CRUISE, "Grad_launch", "FX_MediumMissileIgnition", "FX_HE_UnguidedMissileDetonation", 1800),
        a2a("Pakistan_Weapon_PL9_F7PG", 620, 480, 2, 750, AIM9),
        cannon("Pakistan_Weapon_Cannon_F7PG", 24),
        a2g("Pakistan_Weapon_Bomb_F7PG", 560, 28, 560, 2, 600, FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation"),
        a2a("Iran_Weapon_PL7_F7N", 600, 460, 2, 780, AIM9),
        cannon("Iran_Weapon_Cannon_F7N", 24),
        a2g("Iran_Weapon_Bomb_F7N", 540, 26, 540, 2, 650, FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation"),
    ]
)

AIRCRAFT = [
    dict(
        rel="INI/Object/Specter/Pakistan Armed Forces/Airforce/PakistanJetF16AMLU.ini",
        obj="PakistanJetF16AMLU",
        side="Pakistan",
        portrait="SPEC_PakistanF16AMLU",
        model="LSFF16C",
        model_d="LSFF16Cd",
        model_k="LSFF16Ck",
        weapons=wset(
            "Pakistan_Weapon_AIM120_F16AMLU",
            "Pakistan_Weapon_AIM9_F16AMLU",
            "Pakistan_Weapon_Bomb_F16AMLU",
            "AIRCRAFT",
            "AIRCRAFT",
            "VEHICLE STRUCTURE",
        ),
        cost=1600,
        time=12.0,
        hp=400,
        scale=0.90,
        vision=620,
        note="Pakistan F-16A MLU. Donor ART LSFF16C.W3D unused unique F-16. Distinct from Pakistan_F16Blk52.",
    ),
    dict(
        rel="INI/Object/Specter/Japan Self-Defense Forces/Airforce/JapanJetF15J.ini",
        obj="JapanJetF15J",
        side="Japan",
        portrait="SPEC_JapanF15J",
        model="LSFUSAF15C",
        model_d="LSFUSAF15Cd",
        model_k="LSFUSAF15Ck",
        weapons=wset(
            "Japan_Weapon_AAM4B_F15J",
            "Japan_Weapon_AAM5_F15JBase",
            "Japan_Weapon_Cannon_F15JBase",
            "AIRCRAFT",
            "AIRCRAFT",
            "AIRCRAFT VEHICLE",
        ),
        cost=2400,
        time=16.0,
        hp=520,
        scale=1.02,
        vision=740,
        note="JASDF F-15J. Donor ART LSFUSAF15C.W3D unused unique F-15C. Distinct from F-15J Kai.",
    ),
    dict(
        rel="INI/Object/Specter/Israel Defense Forces/Airforce/IsraelJetF15CBaz.ini",
        obj="IsraelJetF15CBaz",
        side="AmericaAirForceGeneral",
        portrait="SPEC_IsraelF15CBaz",
        model="US_F15C",
        model_d="US_F15C",
        model_k="US_F15C",
        weapons=wset(
            "Israel_Weapon_AMRAAM_F15C",
            "Israel_Weapon_Python_F15C",
            "Israel_Weapon_Cannon_F15C",
            "AIRCRAFT",
            "AIRCRAFT",
            "AIRCRAFT VEHICLE",
        ),
        cost=2300,
        time=15.5,
        hp=500,
        scale=1.00,
        vision=720,
        note="IAF F-15C Baz interceptor. Packed US_F15C.W3D unused after USA F-15E swap. No bombs.",
    ),
    dict(
        rel="INI/Object/Specter/French Armed Forces/Airforce/FranceJetFCASNGF.ini",
        obj="FranceJetFCASNGF",
        side="France",
        portrait="SPEC_FranceFCASNGF",
        model="LSFJ20",
        model_d="LSFJ20",
        model_k="LSFJ20",
        weapons=wset(
            "France_Weapon_Meteor_FCAS",
            "France_Weapon_MICA_FCAS",
            "France_Weapon_AASM_FCAS",
            "AIRCRAFT",
            "AIRCRAFT",
            "VEHICLE STRUCTURE",
        ),
        cost=3200,
        time=20.0,
        hp=560,
        scale=1.00,
        vision=760,
        note="France FCAS NGF demonstrator. Donor ART LSFJ20.W3D unused canard stealth stand-in. Distinct from Germany NVJ31 FCAS.",
    ),
    dict(
        rel="INI/Object/Specter/Saudi Arabia Armed Forces/Airforce/SaudiJetF15S.ini",
        obj="SaudiJetF15S",
        side="SaudiArabia",
        portrait="SPEC_SaudiF15S",
        model="LSFUSAF15E",
        model_d="LSFUSAF15Ed",
        model_k="LSFUSAF15Ek",
        weapons=wset(
            "Saudi_Weapon_AIM120_F15S",
            "Saudi_Weapon_AIM9_F15S",
            "Saudi_Weapon_GBU_F15S",
            "AIRCRAFT",
            "AIRCRAFT",
            "VEHICLE STRUCTURE",
        ),
        cost=2600,
        time=17.0,
        hp=540,
        scale=1.05,
        vision=700,
        note="RSAF F-15S strike eagle. Donor ART LSFUSAF15E.W3D unused unique. USA F-15E keeps US_F15E.",
    ),
    dict(
        rel="INI/Object/Specter/Indian Armed Forces/Airforce/IndiaJetSu30MKI.ini",
        obj="IndiaJetSu30MKI",
        side="India",
        portrait="SPEC_IndiaSu30MKI",
        model="RUSU30",
        model_d="RUSU30d",
        model_k="RUSU30d",
        weapons=wset(
            "India_Weapon_R77_Su30MKI",
            "India_Weapon_R73_Su30MKI",
            "India_Weapon_Kh59_Su30MKI",
            "AIRCRAFT",
            "AIRCRAFT",
            "VEHICLE STRUCTURE",
        ),
        cost=2500,
        time=16.5,
        hp=560,
        scale=0.92,
        vision=720,
        note="IAF Su-30MKI. Donor ART RUSU30.W3D unused unique. Russia Su-30SM2 keeps RUS_SU30SM2.",
    ),
    dict(
        rel="INI/Object/Specter/Pakistan Armed Forces/Airforce/PakistanJetF7PG.ini",
        obj="PakistanJetF7PG",
        side="Pakistan",
        portrait="SPEC_PakistanF7PG",
        model="LSFPKJ7",
        model_d="LSFPKJ7d",
        model_k="LSFPKJ7d",
        weapons=wset(
            "Pakistan_Weapon_PL9_F7PG",
            "Pakistan_Weapon_Cannon_F7PG",
            "Pakistan_Weapon_Bomb_F7PG",
            "AIRCRAFT",
            "AIRCRAFT VEHICLE",
            "VEHICLE STRUCTURE",
        ),
        cost=900,
        time=8.0,
        hp=280,
        scale=0.86,
        vision=480,
        note="PAF F-7PG. Donor ART LSFPKJ7.W3D Pakistan-skinned J-7, distinct hash from China LSFJ7.",
    ),
    dict(
        rel="INI/Object/Specter/Iranian Army/Airforce/IranJetF7N.ini",
        obj="IranJetF7N",
        side="Iran",
        portrait="SPEC_IranF7N",
        model="LSFIRJ7",
        model_d="LSFIRJ7d",
        model_k="LSFIRJ7d",
        weapons=wset(
            "Iran_Weapon_PL7_F7N",
            "Iran_Weapon_Cannon_F7N",
            "Iran_Weapon_Bomb_F7N",
            "AIRCRAFT",
            "AIRCRAFT VEHICLE",
            "VEHICLE STRUCTURE",
        ),
        cost=850,
        time=7.5,
        hp=270,
        scale=0.86,
        vision=470,
        note="IRIAF F-7N. Donor ART LSFIRJ7.W3D Iran-skinned J-7, distinct hash from China LSFJ7.",
    ),
]

BUTTONS = [(s["obj"], s["portrait"]) for s in AIRCRAFT]
PORTRAITS = [p for _, p in BUTTONS]

CSF_LABELS = {
    "CONTROLBAR:ConstructPakistanJetF16AMLU": "F-16A MLU",
    "CONTROLBAR:ToolTipPakistanJetF16AMLU": "Pakistani F-16A MLU. AMRAAM, Sidewinder, conventional bombs.",
    "OBJECT:PakistanJetF16AMLU": "F-16A MLU",
    "CONTROLBAR:ConstructJapanJetF15J": "F-15J",
    "CONTROLBAR:ToolTipJapanJetF15J": "JASDF F-15J air-superiority fighter. AAM-4B and AAM-5. No strike load.",
    "OBJECT:JapanJetF15J": "F-15J",
    "CONTROLBAR:ConstructIsraelJetF15CBaz": "F-15C Baz",
    "CONTROLBAR:ToolTipIsraelJetF15CBaz": "Israeli F-15C Baz interceptor. AMRAAM-class and Python missiles.",
    "OBJECT:IsraelJetF15CBaz": "F-15C Baz",
    "CONTROLBAR:ConstructFranceJetFCASNGF": "FCAS NGF",
    "CONTROLBAR:ToolTipFranceJetFCASNGF": "French FCAS next-generation fighter demonstrator. Meteor, MICA, limited AASM.",
    "OBJECT:FranceJetFCASNGF": "FCAS NGF",
    "CONTROLBAR:ConstructSaudiJetF15S": "F-15S",
    "CONTROLBAR:ToolTipSaudiJetF15S": "Saudi F-15S strike fighter. Defensive A2A and heavy GBU load.",
    "OBJECT:SaudiJetF15S": "F-15S",
    "CONTROLBAR:ConstructIndiaJetSu30MKI": "Su-30MKI",
    "CONTROLBAR:ToolTipIndiaJetSu30MKI": "Indian Su-30MKI multirole. R-77, R-73, Kh-59 strike.",
    "OBJECT:IndiaJetSu30MKI": "Su-30MKI",
    "CONTROLBAR:ConstructPakistanJetF7PG": "F-7PG",
    "CONTROLBAR:ToolTipPakistanJetF7PG": "Pakistani F-7PG legacy fighter. PL-9, cannon, light bombs.",
    "OBJECT:PakistanJetF7PG": "F-7PG",
    "CONTROLBAR:ConstructIranJetF7N": "F-7N",
    "CONTROLBAR:ToolTipIranJetF7N": "Iranian F-7N legacy interceptor. Short-range IR missiles, cannon, light bombs.",
    "OBJECT:IranJetF7N": "F-7N",
}

SLOT_ADDS = {
    "Pakistan_AirfieldCommandSet": {
        7: "Command_ConstructPakistanJetF16AMLU",
        8: "Command_ConstructPakistanJetF7PG",
    },
    "Japan_HeavyAirBaseCommandSet": {9: "Command_ConstructJapanJetF15J"},
    "Israel_HeavyAirBaseCommandSet": {3: "Command_ConstructIsraelJetF15CBaz"},
    "France_HeavyAirBaseCommandSet": {6: "Command_ConstructFranceJetFCASNGF"},
    "SaudiArabia_HeavyAirBaseCommandSet": {1: "Command_ConstructSaudiJetF15S"},
    "India_HeavyAirBaseCommandSet": {1: "Command_ConstructIndiaJetSu30MKI"},
    "Iran_HeavyAirBaseCommandSet": {4: "Command_ConstructIranJetF7N"},
}

PORTRAIT_SRC = {
    "SPEC_PakistanF16AMLU.tga": "LSFF16C.tga",
    "SPEC_JapanF15J.tga": "LSFUSAF15C.tga",
    "SPEC_IsraelF15CBaz.tga": "US_F15C.dds",
    "SPEC_FranceFCASNGF.tga": "LSFJ20.dds",
    "SPEC_SaudiF15S.tga": "LSFUSAF15E.dds",
    "SPEC_IndiaSu30MKI.tga": "RUSU30MKK.dds",
    "SPEC_PakistanF7PG.tga": "LSFPKJ7.dds",
    "SPEC_IranF7N.tga": "LSFIRJ7.dds",
}


def buttons_text() -> str:
    chunks = ["; SPECTER unused-donor construct buttons. Inlined into CommandSet.ini."]
    for obj, img in BUTTONS:
        chunks.append(
            f"CommandButton Command_Construct{obj}\n"
            f"  Command          = UNIT_BUILD\n"
            f"  Object           = {obj}\n"
            f"  TextLabel        = CONTROLBAR:Construct{obj}\n"
            f"  ButtonImage      = {img}\n"
            f"  ButtonBorderType = BUILD\n"
            f"  DescriptLabel    = CONTROLBAR:ToolTip{obj}\n"
            f"End\n"
        )
    return "\n".join(chunks)


def mapped_text() -> str:
    chunks = ["; Unique Specter unused-donor portraits."]
    for img in PORTRAITS:
        chunks.append(
            f"MappedImage {img}\n"
            f"  Texture = {img}.tga\n"
            f"  TextureWidth = 150\n"
            f"  TextureHeight = 113\n"
            f"  Coords = Left:0 Top:0 Right:150 Bottom:113\n"
            f"  Status = NONE\n"
            f"End\n"
        )
    return "\n".join(chunks)


def main() -> None:
    w(INI / "Weapon_DonorUnusedAircraft.ini", WEAPONS)
    w(INI / "CommandButton_DonorUnusedAircraft.ini", buttons_text())
    w(MAP / "zDonorUnused_AirbasePortrait_Images.INI", mapped_text())
    for spec in AIRCRAFT:
        body = fighter(
            spec["obj"],
            spec["side"],
            spec["portrait"],
            spec["model"],
            spec["model_d"],
            spec["model_k"],
            spec["weapons"],
            spec["cost"],
            spec["time"],
            spec["hp"],
            spec["scale"],
            spec["vision"],
            spec["note"],
        )
        w(ROOT / spec["rel"], body)
    print(f"wrote {len(AIRCRAFT)} unused-donor aircraft + weapons + buttons + portraits")


if __name__ == "__main__":
    main()
