#!/usr/bin/env python3
"""Fix Aircraft_AAB_Global.ini identity mismatches using Specter donor art."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AAB = ROOT / "Data/INI/Object/Specter/PatchSystems/AdvancedAirBase/Aircraft_AAB_Global.ini"
BTN = ROOT / "Data/INI/CommandButton_AdvancedAirBase_Aircraft.ini"


def jet_draw(model: str, bone: str = "WeaponA", engines: int = 2) -> str:
    """AAB-friendly Draw copied from Specter USA jet donors (F35/F22/F15 style)."""
    engine_lines_default = "\n".join(
        f"      ParticleSysBone     = Engine{i:02d} JetLenzflare" for i in range(1, engines + 1)
    )
    engine_lines_dmg = "\n".join(
        f"      ParticleSysBone     = Engine{i:02d} JetLenzflare" for i in range(1, engines + 1)
    )
    return f"""  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model               = {model}
      HideSubObject       = BurnerFX01 BurnerFX02
      WeaponLaunchBone = PRIMARY {bone}
    End
    ConditionState        = JETEXHAUST
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End
    ConditionState        = JETEXHAUST JETAFTERBURNER
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
      ShowSubObject       = BurnerFX01 BurnerFX02
{engine_lines_default}
    End
    ConditionState        = REALLYDAMAGED
      Model               = {model}
      ParticleSysBone     = Smoke01 JetSmoke
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
    End
    ConditionState        = REALLYDAMAGED JETEXHAUST
      Model               = {model}
      ParticleSysBone     = Smoke01 JetSmoke
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End
    ConditionState        = REALLYDAMAGED JETEXHAUST JETAFTERBURNER
      Model               = {model}
      ParticleSysBone     = Smoke01 JetSmoke
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
      ShowSubObject       = BurnerFX01 BurnerFX02
{engine_lines_dmg}
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End
    ConditionState        = RUBBLE
      Model               = {model}
      HideSubObject       = None
      ShowSubObject       = None
    End
    OkToChangeModelColor = Yes
  End
"""


# object -> (model, portrait, commandset, locomotor, bone, engines)
FIXES: dict[str, tuple[str, str, str, str, str, int]] = {
    # America priority fixes
    "Patch_America_F35": (
        "US_F35A",
        "Nat_f35a",
        "GenericMultiRoleFighter_AG_CommandSet",
        "Pratt_Whitney_F135",
        "WeaponA",
        1,  # F35 single engine; donor lists Engine01/02 FX but model has ENGINE01
    ),
    "Patch_America_F15E": (
        "US_F15E",
        "us_f15e",
        "GenericMultiRoleFighter_AG_CommandSet",
        "Pratt_Whitney_F100",
        "Weapon01",
        2,
    ),
    "Patch_America_F15EX": (
        "US_F15EX",
        "us_f15e",
        "GenericMultiRoleFighter_AG_CommandSet",
        "Pratt_Whitney_F100",
        "Weapon01",
        2,
    ),
    "Patch_America_A10": (
        "US_A10C",
        "us_a10c",
        "GenericTacticalBomberCommandSet",
        "TF34_GE_100",
        "WeaponA",
        2,
    ),
    "Patch_America_EA18G": (
        "US_EA18G",
        "us_ea18g",
        "EA18G_CommandSet",
        "General_Electric_F414",
        "WeaponA01",
        2,
    ),
    # Allied F-35s (Specter donors all use US_F35A + Nat_f35a)
    "Patch_Japan_F35J": (
        "US_F35A",
        "Nat_f35a",
        "GenericMultiRoleFighter_AG_CommandSet",
        "Pratt_Whitney_F135",
        "WeaponA",
        1,
    ),
    "Patch_UAE_F35": (
        "US_F35A",
        "Nat_f35a",
        "GenericMultiRoleFighter_AG_CommandSet",
        "Pratt_Whitney_F135",
        "WeaponA",
        1,
    ),
    "Patch_Nato_F35": (
        "US_F35A",
        "Nat_f35a",
        "GenericMultiRoleFighter_AG_CommandSet",
        "Pratt_Whitney_F135",
        "WeaponA",
        1,
    ),
    "Patch_Britain_F35B": (
        "US_F35A",
        "Nat_f35a",
        "GenericMultiRoleFighter_AG_CommandSet",
        "Pratt_Whitney_F135",
        "WeaponA",
        1,
    ),
    "Patch_Italy_F35A": (
        "US_F35A",
        "Nat_f35a",
        "GenericMultiRoleFighter_AG_CommandSet",
        "Pratt_Whitney_F135",
        "WeaponA",
        1,
    ),
    "Patch_SouthKorea_F35A": (
        "US_F35A",
        "Nat_f35a",
        "GenericMultiRoleFighter_AG_CommandSet",
        "Pratt_Whitney_F135",
        "WeaponA",
        1,
    ),
    "Patch_UN_F35": (
        "US_F35A",
        "Nat_f35a",
        "GenericMultiRoleFighter_AG_CommandSet",
        "Pratt_Whitney_F135",
        "WeaponA",
        1,
    ),
    # F-15 family
    "Patch_Japan_F15J": (
        "US_F15E",
        "us_f15e",
        "GenericMultiRoleFighter_AG_CommandSet",
        "Pratt_Whitney_F100",
        "Weapon01",
        2,
    ),
    "Patch_Saudi_F15SA": (
        "Arb_F15SA",
        "arb_f15sa",
        "GenericTacticalBomberCommandSet",
        "Pratt_Whitney_F100",
        "Weapon01",
        2,
    ),
    "Patch_SouthKorea_F15K": (
        "Arb_F15SA",
        "arb_f15sa",
        "GenericTacticalBomberCommandSet",
        "Pratt_Whitney_F100",
        "Weapon01",
        2,
    ),
}

# CommandButton image overrides (construct buttons)
BTN_IMAGES = {
    "Command_ConstructPatch_America_F35": "Nat_f35a",
    "Command_ConstructPatch_America_F15E": "us_f15e",
    "Command_ConstructPatch_America_F15EX": "us_f15e",
    "Command_ConstructPatch_America_A10": "us_a10c",
    "Command_ConstructPatch_America_EA18G": "us_ea18g",
    "Command_ConstructPatch_Japan_F35J": "Nat_f35a",
    "Command_ConstructPatch_UAE_F35": "Nat_f35a",
    "Command_ConstructPatch_Nato_F35": "Nat_f35a",
    "Command_ConstructPatch_Britain_F35B": "Nat_f35a",
    "Command_ConstructPatch_Italy_F35A": "Nat_f35a",
    "Command_ConstructPatch_SouthKorea_F35A": "Nat_f35a",
    "Command_ConstructPatch_UN_F35": "Nat_f35a",
    "Command_ConstructPatch_Japan_F15J": "us_f15e",
    "Command_ConstructPatch_Saudi_F15SA": "arb_f15sa",
    "Command_ConstructPatch_SouthKorea_F15K": "arb_f15sa",
}


def patch_object(block: str, obj: str, model: str, portrait: str, cmd: str, loco: str, bone: str, engines: int) -> str:
    # Replace SelectPortrait / ButtonImage
    block = re.sub(r"(^\s*SelectPortrait\s*=\s*)\S+", rf"\g<1>{portrait}", block, count=1, flags=re.M)
    block = re.sub(r"(^\s*ButtonImage\s*=\s*)\S+", rf"\g<1>{portrait}", block, count=1, flags=re.M)
    # Replace Draw module
    draw = jet_draw(model, bone, engines)
    block2, n = re.subn(
        r"^\s*Draw\s*=\s*W3DModelDraw[\s\S]*?^\s*OkToChangeModelColor\s*=\s*Yes\s*\n\s*End",
        draw.rstrip(),
        block,
        count=1,
        flags=re.M,
    )
    if n != 1:
        # fallback: Draw ... End that contains DefaultConditionState
        block2, n = re.subn(
            r"^\s*Draw\s*=\s*W3DModelDraw ModuleTag_01\n[\s\S]*?^\s*End\n(?=\s*DisplayName|\s*; \*\*\*)",
            draw,
            block,
            count=1,
            flags=re.M,
        )
    if n != 1:
        raise RuntimeError(f"Failed to replace Draw for {obj} (n={n})")
    block = block2
    # CommandSet + Locomotor
    block = re.sub(r"(^\s*CommandSet\s*=\s*)\S+", rf"\g<1>{cmd}", block, count=1, flags=re.M)
    block = re.sub(
        r"(^\s*Locomotor\s*=\s*SET_NORMAL\s+)\S+",
        rf"\g<1>{loco}",
        block,
        count=1,
        flags=re.M,
    )
    # Identity comment
    if "SPECTER IDENTITY FIX" not in block:
        block = block.replace(
            f"Object {obj}\n",
            f"Object {obj}\n; SPECTER IDENTITY FIX - Draw/Model/CommandSet from Specter donor ({model})\n",
            1,
        )
    return block


def main() -> int:
    text = AAB.read_text("latin-1")
    for obj, (model, portrait, cmd, loco, bone, engines) in FIXES.items():
        s = text.find(f"Object {obj}")
        if s < 0:
            print("MISSING", obj)
            continue
        n = text.find("\nObject ", s + 10)
        if n < 0:
            n = len(text)
        old = text[s:n]
        new = patch_object(old, obj, model, portrait, cmd, loco, bone, engines)
        text = text[:s] + new + text[n:]
        print("FIXED", obj, "->", model, portrait, cmd)

    # ASCII-scrub only the fixed object header comments that we may have introduced is enough;
    # leave rest of file. Validate no non-ascii in our SPECTER IDENTITY FIX lines.
    AAB.write_text(text, encoding="latin-1")

    # Buttons
    btn = BTN.read_text("latin-1")
    for cmd, img in BTN_IMAGES.items():
        pat = re.compile(
            rf"(CommandButton {re.escape(cmd)}\n[\s\S]*?ButtonImage\s*=\s*)\S+",
            re.M,
        )
        btn2, n = pat.subn(rf"\g<1>{img}", btn, count=1)
        if n:
            btn = btn2
            print("BTN", cmd, "->", img)
        else:
            print("BTN skip (not present)", cmd)
    BTN.write_text(btn, encoding="latin-1")

    # Verify
    text = AAB.read_text("latin-1")
    for obj, (model, portrait, cmd, loco, bone, engines) in FIXES.items():
        s = text.find(f"Object {obj}")
        n = text.find("\nObject ", s + 10)
        b = text[s:n]
        assert f"Model               = {model}" in b or f"Model = {model}" in b or f"Model               = {model}" in b
        assert f"SelectPortrait" in b and portrait in b
        assert f"CommandSet = {cmd}" in b or f"CommandSet = {cmd}" in b.replace("  ", " ")
        assert re.search(rf"CommandSet\s*=\s*{re.escape(cmd)}", b)
        assert re.search(rf"Locomotor\s*=\s*SET_NORMAL\s+{re.escape(loco)}", b)
        assert f"Model               = {model}" in b or re.search(rf"Model\s*=\s*{re.escape(model)}", b)
        # ensure placeholder gone for F35
        if "F35" in obj:
            assert "US_F16CMB50" not in b
            assert "F16C_AG_CommandSet" not in b
        print("VERIFY OK", obj)
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
