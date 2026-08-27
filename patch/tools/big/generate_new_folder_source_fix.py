#!/usr/bin/env python3
"""New-folder/TEOD visual source correction. Preserves Specter gameplay."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_final_global_completion as g

ROOT = Path("/workspace/patch/Data")
INI = ROOT / "INI"
MAP = INI / "MappedImages/HandCreated"

# Existing objects: replace Draw models only.
VISUAL_PATCHES = [
    {
        "rel": "INI/Object/Specter/French Armed Forces/Airforce/FranceJetMirageF1CR.ini",
        "note": "France Mirage F1CR. New folder TEOD UVMirage. Gameplay unchanged.",
        "pairs": [("LSFFRF1d", "UVMirage_D"), ("LSFFRF1k", "UVMirage_E"), ("LSFFRF1", "UVMirage")],
    },
    {
        "rel": "INI/Object/Specter/Japan Self-Defense Forces/Airforce/JapanJetC130H.ini",
        "note": "JASDF C-130H. New folder TEOD AVCargoPln (AC-130/C-130 class). Gameplay unchanged.",
        "pairs": [("AVCargoPln_D1", "AVCargoPln_E")],
    },
    {
        "rel": "INI/Object/Specter/PLA/Airforce/ChinaJetJ35A.ini",
        "note": "PLA Shenyang J-35A. New folder TEOD NVJ31 (FC-31/J-31 family). Gameplay unchanged.",
        "pairs": [],
        "all_model": ("CHAJ31HXNew", "NVJ31", "NVJ31_D", "NVJ31_E"),
    },
    {
        "rel": "INI/Object/Specter/German Armed Forces/Airforce/GermanyJetFCASNGF.ini",
        "note": "Germany FCAS NGF Demonstrator. New folder TEOD NVJ31. Gameplay unchanged.",
        "pairs": [("LSFJ31d", "NVJ31_D"), ("LSFJ31k", "NVJ31_E"), ("LSFJ31", "NVJ31")],
    },
    {
        "rel": "INI/Object/Specter/Iranian Army/Airforce/IranJetMig21Bis.ini",
        "note": "Iran MiG-21bis. New folder TEOD UVMig-21. Gameplay unchanged.",
        "pairs": [("LSFIDMig21d", "UVMig-21_D"), ("LSFIDMig21", "UVMig-21")],
        "k_from_d": True,
        "model_k": "UVMig-21_E",
    },
    {
        "rel": "INI/Object/Specter/Iranian Army/Airforce/IranJetSu35S.ini",
        "note": "Iran Su-35. New folder TEOD SU-37 (SU-35.dds). Gameplay unchanged.",
        "pairs": [("LSFSU35d", "SU-37_D"), ("LSFSU35k", "SU-37_E"), ("LSFSU35", "SU-37")],
    },
    {
        "rel": "INI/Object/Specter/Pakistan Armed Forces/Airforce/PakistanJetJ10CE.ini",
        "note": "Pakistan J-10CE. New folder TEOD NVJ-10. Gameplay unchanged.",
        "pairs": [("CHI_J10C_D", "NVJ-10D"), ("CHI_J10C_R", "NVJ-10_D"), ("CHI_J10C", "NVJ-10")],
    },
    {
        "rel": "INI/Object/Specter/Italian Armed Forces/Airforce/ItalyJetGCAP.ini",
        "note": "Italy GCAP demonstrator. New folder TEOD PAK-FA. Gameplay unchanged.",
        "pairs": [("qsnt50", "PAK-FA")],
        "all_same_then_dk": ("PAK-FA", "PAK-FA_D", "PAK-FA_E"),
    },
    {
        "rel": "INI/Object/Specter/Turkey Armed Forces/Airforce/TurkeyJetF16C.ini",
        "note": "Turkey F-16C Block 50+. New folder TEOD AVF16. Gameplay unchanged.",
        "pairs": [("LSFF16Cd", "AVF16_D"), ("LSFF16Ck", "AVF16_E"), ("LSFF16C", "AVF16")],
    },
]


def patch_comment(text: str, note: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith(";"):
        lines[0] = f"; SPECTER - {note}"
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "\n")


def apply_all_model(text: str, old: str, model: str, model_d: str, model_k: str) -> str:
    """Replace a single shared model name with pristine/damaged/rubble variants by ConditionState."""
    out = []
    state = "default"
    for line in text.splitlines(True):
        s = line.strip()
        if s.startswith("DefaultConditionState"):
            state = "default"
        elif s.startswith("ConditionState") and "RUBBLE" in s:
            state = "rubble"
        elif s.startswith("ConditionState") and "REALLYDAMAGED" in s:
            state = "damaged"
        elif s.startswith("ConditionState"):
            state = "other"
        if re.match(r"\s*Model\s+=\s+" + re.escape(old) + r"\s*$", line):
            tgt = model if state in ("default", "other") else (model_k if state == "rubble" else model_d)
            line = re.sub(r"(Model\s+=\s+)\S+", r"\1" + tgt, line)
        out.append(line)
    return "".join(out)


def apply_after_same(text: str, model: str, model_d: str, model_k: str) -> str:
    return apply_all_model(text, model, model, model_d, model_k)


def patch_existing() -> list[Path]:
    written = []
    for spec in VISUAL_PATCHES:
        path = ROOT / spec["rel"]
        text = path.read_text(encoding="ascii")
        text = patch_comment(text, spec["note"])
        if spec.get("all_model"):
            old, m, md, mk = spec["all_model"]
            text = apply_all_model(text, old, m, md, mk)
        else:
            for a, b in spec["pairs"]:
                text = text.replace(a, b)
            if spec.get("all_same_then_dk"):
                m, md, mk = spec["all_same_then_dk"]
                text = apply_after_same(text, m, md, mk)
            if spec.get("model_k"):
                # rubble still has _D from d-pair; fix rubble to _E
                text = apply_all_model(text, spec["pairs"][0][1], spec["pairs"][-1][1], spec["pairs"][0][1], spec["model_k"])
        g.w(path, text)
        written.append(path)
        print("patched", spec["rel"])
    return written


WEAPONS = "\n".join(
    [
        "; SPECTER new-folder source-fix weapons for newly created units only.",
        g.cannon("Britain_Weapon_VampireFB5_Cannon", 24),
        g.rockets("Britain_Weapon_VampireFB5_Rocket", 8),
        g.a2g("Britain_Weapon_VampireFB5_Bomb", 480, 26, 520, 4, 550, g.FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation"),
        g.cannon("Britain_Weapon_VampireFB9_Cannon", 24),
        g.a2a("Britain_Weapon_VampireFB9_IR", 480, 380, 2, 800, g.AIM9),
        g.a2g("Britain_Weapon_VampireFB9_Bomb", 500, 28, 540, 2, 600, g.FAB, "B52BombDrop", "FX_AuroraBombLaunch", "FX_FreeFallBombsDetonation"),
    ]
)

NEW_AIRCRAFT = [
    dict(
        rel="INI/Object/Specter/United States Of America/Airforce/AmericaDroneRQ180.ini",
        kind="jet",
        obj="AmericaDroneRQ180",
        side="America",
        portrait="SPEC_AmericaRQ180",
        model="AV_RQ180",
        model_d="AV_RQ180_D",
        model_k="AV_RQ180_E",
        weapons="",
        cost=2400, time=20.0, hp=280, scale=0.80, vision=1100,
        commandset="C17GlobalMasterCommandSet", shroud=960.0,
        kindof="PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT",
        extras=g.STEALTH + g.DETECT.format(rate=1200, rng=2600),
        needs_runway="Yes", mass=120.0, geom=(16.0, 8.0, 3.0, "No"),
        locomotor="D30-F6_JetLocomotor",
        note="USA RQ-180 unarmed stealth HALE recon. New folder TEOD AV_RQ180. No offensive weapons.",
    ),
    dict(
        rel="INI/Object/Specter/British Armed Forces/Airforce/BritainJetVampireFB5.ini",
        kind="jet",
        obj="BritainJetVampireFB5",
        side="Britain",
        portrait="SPEC_BritainVampireFB5",
        model="UV_Turbo",
        model_d="UV_Turbo_D",
        model_k="UV_Turbo_D",
        weapons=g.wset(
            "Britain_Weapon_VampireFB5_Cannon",
            "Britain_Weapon_VampireFB5_Rocket",
            "Britain_Weapon_VampireFB5_Bomb",
            "AIRCRAFT VEHICLE",
            "VEHICLE STRUCTURE",
            "VEHICLE STRUCTURE",
        ),
        cost=600, time=7.0, hp=260, scale=0.78, vision=420,
        commandset=g.BOMBER_CS,
        note="RAF de Havilland Vampire FB.5. New folder TEOD UV_Turbo (Turbo Vampire). Legacy fighter-bomber.",
    ),
    dict(
        rel="INI/Object/Specter/British Armed Forces/Airforce/BritainJetVampireFB9.ini",
        kind="jet",
        obj="BritainJetVampireFB9",
        side="Britain",
        portrait="SPEC_BritainVampireFB9",
        model="UVVampire",
        model_d="UVVampire_D",
        model_k="UVVampire_E1",
        weapons=g.wset(
            "Britain_Weapon_VampireFB9_IR",
            "Britain_Weapon_VampireFB9_Cannon",
            "Britain_Weapon_VampireFB9_Bomb",
            "AIRCRAFT",
            "AIRCRAFT VEHICLE",
            "VEHICLE STRUCTURE",
        ),
        cost=650, time=7.5, hp=270, scale=0.80, vision=440,
        commandset=g.BOMBER_CS,
        note="RAF de Havilland Vampire FB.9. New folder TEOD UVVampire. Distinct from Turbo Vampire UV_Turbo.",
    ),
]

BUTTONS = [(s["obj"], s["portrait"]) for s in NEW_AIRCRAFT]
CSF_LABELS = {
    "CONTROLBAR:ConstructAmericaDroneRQ180": "RQ-180",
    "CONTROLBAR:ToolTipAmericaDroneRQ180": "American RQ-180 stealth reconnaissance UAV. Unarmed. Large radar and shroud coverage.",
    "OBJECT:AmericaDroneRQ180": "RQ-180",
    "CONTROLBAR:ConstructBritainJetVampireFB5": "Vampire FB.5",
    "CONTROLBAR:ToolTipBritainJetVampireFB5": "RAF de Havilland Vampire FB.5. Cannon, rockets, light bombs. Legacy fighter-bomber.",
    "OBJECT:BritainJetVampireFB5": "Vampire FB.5",
    "CONTROLBAR:ConstructBritainJetVampireFB9": "Vampire FB.9",
    "CONTROLBAR:ToolTipBritainJetVampireFB9": "RAF de Havilland Vampire FB.9. Distinct from FB.5. Cannon, short-range IR, bombs.",
    "OBJECT:BritainJetVampireFB9": "Vampire FB.9",
}
PORTRAITS = [p for _, p in BUTTONS]


def buttons_text() -> str:
    chunks = ["; SPECTER new-folder source-fix construct buttons."]
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
    chunks = ["; Unique Specter new-folder source-fix portraits."]
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
    patch_existing()
    g.w(INI / "Weapon_NewFolderSourceFix.ini", WEAPONS)
    g.w(INI / "CommandButton_NewFolderSourceFix.ini", buttons_text())
    g.w(MAP / "zNewFolderSourceFix_Portrait_Images.INI", mapped_text())
    for spec in NEW_AIRCRAFT:
        body = g.jet(
            spec["obj"], spec["side"], spec["portrait"],
            spec["model"], spec["model_d"], spec["model_k"],
            spec["weapons"], spec["cost"], spec["time"], spec["hp"],
            spec["scale"], spec["vision"], spec["note"],
            commandset=spec.get("commandset", g.FIGHTER_CS),
            shroud=spec.get("shroud", 220.0),
            kindof=spec.get("kindof", "PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT"),
            extras=spec.get("extras", ""),
            needs_runway=spec.get("needs_runway", ""),
            locomotor=spec.get("locomotor", "Snecma_M88_4E"),
            geom=spec.get("geom", (14.0, 7.0, 5.0, "Yes")),
            mass=spec.get("mass", 500.0),
        )
        g.w(ROOT / spec["rel"], body)
    print(f"patched visuals + wrote {len(NEW_AIRCRAFT)} new aircraft")


if __name__ == "__main__":
    main()
