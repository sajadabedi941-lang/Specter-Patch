#!/usr/bin/env python3
"""Icon-only last-wins: Israel Jericho -> Button_Atom, China D30 -> Button_Artillery.

Baseline: packed SPECTER_ARABIC_ALLIANCE_UPGRADES (PR #654).

Packed last-wins audit:
  AirF_Command_ConstructAmericaParticleCannonUplink
    Object=AirF_AmericaParticleCannonUplink (Israel Jericho silo)
    CommandSet IsraelDozerCommandSet slot 6
    ButtonImage was isi_jericho
  Command_ConstructChinaBunker
    Object=ChinaBunker last-wins from PLA\\Buildings\\D30.ini
    CommandSet PLADozerCommandSet slot 7
    ButtonImage was rus_d30

Existing MappedImages (ART already packed):
  Button_Atom      Texture=Button_Atom.tga
  Button_Artillery Texture=Button_Artillery.tga

ART is copied unchanged. No new faction, unit, weapon, or texture.
"""
from __future__ import annotations

import hashlib
import shutil
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_ARABIC_ALLIANCE_UPGRADES/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_ARABIC_ALLIANCE_UPGRADES/_SPEC_ART_ONE.big"
SRC_ART_GZ = ROOT / "patch/Release/SPECTER_ARABIC_ALLIANCE_UPGRADES/_SPEC_ART_ONE.big.gz"
OUT = ROOT / "patch/Release/SPECTER_ISRAEL_JERICHO_CHINA_D30_ICONS"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "9f502c614f97e64566d1480da8e5f3596e3e81462a719d2c6f72c5f1d1ae499a"
SIZE_DATA_SRC = 370733139
SHA_ART_SRC = "de0e998813bb7f74ff634c4a5aefb901692334e1e0d2a52637d3699b1d8f1f8a"
SIZE_ART_SRC = 2451295403
SHA_ART_GZ_SRC = "c759a09f94ac407337691ec8cd86dbdc85bc3d6a00cd1766e55bf21b67d8bfaf"

CB_KEY = r"Data\INI\CommandButton_IsraelJerichoChinaD30Icons.ini"
JERICHO_BTN = "AirF_Command_ConstructAmericaParticleCannonUplink"
CHINA_BTN = "Command_ConstructChinaBunker"
ATOM = "Button_Atom"
ARTILLERY = "Button_Artillery"

FROZEN = [
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandSet_IsraelMissiles.ini",
    r"Data\INI\CommandSet_ChinaMissiles.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\Upgrade.ini",
    r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Jericho.ini",
    r"Data\INI\Object\Specter\PLA\Buildings\D30.ini",
    r"Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Israel_Jericho2.ini",
    r"Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Israel_Jericho3.ini",
]


def last_block(text: str, kind: str, name: str) -> str:
    import re
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
        block = last_block(blob.decode("latin1"), kind, name)
        if block:
            found = (key, block)
    return found


def field(block: str, key: str) -> str:
    import re
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block or "", re.M)
    return m.group(1).strip() if m else ""


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
    original = dict(files)

    overlay = sk.to_crlf(
        (LOOSE / "CommandButton_IsraelJerichoChinaD30Icons.ini").read_text(
            encoding="latin1"
        )
    )
    files[CB_KEY] = overlay
    if CB_KEY not in order:
        order.append(CB_KEY)

    for key in FROZEN:
        if key not in files:
            raise SystemExit(f"missing frozen {key}")
        if files[key] != original[key]:
            raise SystemExit(f"frozen mutated before pack: {key}")

    data_big = sk.build_big(files)
    fails = sk.big_structure_ok(data_big)
    if fails:
        raise SystemExit("big_structure_ok: " + "; ".join(fails))

    packed, packed_order = sk.parse_big_ordered(data_big)

    src_j, blk_j = last_from(packed_order, packed, "CommandButton", JERICHO_BTN)
    src_c, blk_c = last_from(packed_order, packed, "CommandButton", CHINA_BTN)
    if src_j != CB_KEY:
        raise SystemExit(f"Jericho button last-wins {src_j}")
    if src_c != CB_KEY:
        raise SystemExit(f"China D30 button last-wins {src_c}")
    if field(blk_j, "ButtonImage") != ATOM:
        raise SystemExit(f"Jericho icon {field(blk_j, 'ButtonImage')}")
    if field(blk_c, "ButtonImage") != ARTILLERY:
        raise SystemExit(f"China D30 icon {field(blk_c, 'ButtonImage')}")
    if field(blk_j, "Object") != "AirF_AmericaParticleCannonUplink":
        raise SystemExit("Jericho object changed")
    if field(blk_c, "Object") != "ChinaBunker":
        raise SystemExit("China D30 object changed")
    if field(blk_j, "Command") != "DOZER_CONSTRUCT":
        raise SystemExit("Jericho command changed")
    if field(blk_c, "Command") != "DOZER_CONSTRUCT":
        raise SystemExit("China D30 command changed")
    if field(blk_j, "TextLabel") != "CONTROLBAR:Constructisijerichoiii":
        raise SystemExit("Jericho label changed")
    if field(blk_c, "TextLabel") != "CONTROLBAR:ConstructRussiaD30":
        raise SystemExit("China D30 label changed")

    src_a, mi_a = last_from(packed_order, packed, "MappedImage", ATOM)
    src_r, mi_r = last_from(packed_order, packed, "MappedImage", ARTILLERY)
    if field(mi_a, "Texture") != "Button_Atom.tga":
        raise SystemExit("Button_Atom texture missing")
    if field(mi_r, "Texture") != "Button_Artillery.tga":
        raise SystemExit("Button_Artillery texture missing")

    src_cs, cs = last_from(packed_order, packed, "CommandSet", "IsraelDozerCommandSet")
    if "6  = AirF_Command_ConstructAmericaParticleCannonUplink" not in cs.replace("\r\n", "\n"):
        # allow spacing variants
        if "AirF_Command_ConstructAmericaParticleCannonUplink" not in cs:
            raise SystemExit("Israel dozer lost Jericho construct")
    src_pla, pla = last_from(packed_order, packed, "CommandSet", "PLADozerCommandSet")
    if "Command_ConstructChinaBunker" not in pla:
        raise SystemExit("PLA dozer lost China D30 construct")

    src_obj, jericho_obj = last_from(
        packed_order, packed, "Object", "AirF_AmericaParticleCannonUplink"
    )
    if "Israel" not in field(jericho_obj, "Side") and field(jericho_obj, "Side") != "Israel":
        raise SystemExit(f"Jericho object Side={field(jericho_obj, 'Side')}")
    src_d30, d30_obj = last_from(packed_order, packed, "Object", "ChinaBunker")
    if field(d30_obj, "Side") != "China":
        raise SystemExit(f"ChinaBunker Side={field(d30_obj, 'Side')}")

    src_h, h = last_from(packed_order, packed, "CommandButton", "CB_ISRAEL_MISSILE_H")
    src_i, i = last_from(packed_order, packed, "CommandButton", "CB_ISRAEL_MISSILE_I")
    if field(h, "Object") != "Israel_Jericho2" or field(h, "ButtonImage") != "specter_missile_h":
        raise SystemExit("factory Jericho2 button mutated")
    if field(i, "Object") != "Israel_Jericho3" or field(i, "ButtonImage") != "specter_missile_i":
        raise SystemExit("factory Jericho3 button mutated")

    if packed[r"Data\INI\CommandSet_IsraelMissiles.ini"] != original[r"Data\INI\CommandSet_IsraelMissiles.ini"]:
        raise SystemExit("Israel CommandSet mutated")
    if packed[r"Data\INI\CommandSet_ChinaMissiles.ini"] != original[r"Data\INI\CommandSet_ChinaMissiles.ini"]:
        raise SystemExit("China CommandSet mutated")
    if packed[r"Data\INI\PlayerTemplate.ini"] != original[r"Data\INI\PlayerTemplate.ini"]:
        raise SystemExit("PlayerTemplate mutated")

    allowed = {CB_KEY}
    for key in original:
        if key in allowed:
            continue
        if packed.get(key) != original[key]:
            raise SystemExit(f"unrelated key changed: {key}")
    for key in packed:
        if key not in original and key != CB_KEY:
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
    (ext / "CommandButton_IsraelJerichoChinaD30Icons.ini").write_bytes(overlay)

    data_sha = sk.sha256_path(data_path)
    art_sha = sk.sha256_path(art_path)
    art_gz_sha = sk.sha256_path(art_gz_path)
    if art_sha != SHA_ART_SRC:
        raise SystemExit("copied ART hash mismatch")
    if art_gz_sha != SHA_ART_GZ_SRC:
        raise SystemExit("copied ART.gz hash mismatch")

    zip_path = ROOT / "patch/Release/SPECTER_ISRAEL_JERICHO_CHINA_D30_ICONS.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)
    tag = "s-israel-jericho-china-d30-icons"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/"
        + tag
    )

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #654 s-arabic-alliance-upgrades",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        f"ART_GZ_SIZE={art_gz_path.stat().st_size}",
        f"ART_GZ_SHA256={art_gz_sha}",
        "ART_CHANGED=NO",
        "ART_NEW_TEXTURE=NO",
        f"JERICHO_BUTTON={JERICHO_BTN}",
        "JERICHO_OBJECT=AirF_AmericaParticleCannonUplink",
        f"JERICHO_ICON_WAS=isi_jericho",
        f"JERICHO_ICON_NOW={ATOM}",
        "JERICHO_TEXTURE=Button_Atom.tga",
        "JERICHO_COMMANDSET=IsraelDozerCommandSet slot 6 (unchanged)",
        f"CHINA_D30_BUTTON={CHINA_BTN}",
        "CHINA_D30_OBJECT=ChinaBunker (PLA D30.ini last-wins)",
        "CHINA_D30_ICON_WAS=rus_d30",
        f"CHINA_D30_ICON_NOW={ARTILLERY}",
        "CHINA_D30_TEXTURE=Button_Artillery.tga",
        "CHINA_D30_COMMANDSET=PLADozerCommandSet slot 7 (unchanged)",
        "FACTORY_JERICHO2_UNCHANGED=CB_ISRAEL_MISSILE_H specter_missile_h",
        "FACTORY_JERICHO3_UNCHANGED=CB_ISRAEL_MISSILE_I specter_missile_i",
        "LABELS_UNCHANGED=YES",
        "COMMANDSETS_UNCHANGED=YES",
        "NO_NEW_FACTION=YES",
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
            "ZIP_FILE=SPECTER_ISRAEL_JERICHO_CHINA_D30_ICONS.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #654",
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
                "ART is unchanged from PR #654 / #653. Gzipped for GitHub's 2 GiB limit.",
                "ART is also inside the ZIP as uncompressed _SPEC_ART_ONE.big (same SHA).",
                "",
                "ZIP (complete uncompressed DATA + ART BIGs):",
                f"  {rel_base}/SPECTER_ISRAEL_JERICHO_CHINA_D30_ICONS.zip",
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
        "Israel Jericho construct button uses existing Button_Atom.\n"
        "China D30 construct button uses existing Button_Artillery.\n"
        "Gameplay, objects, labels, and CommandSets are unchanged. ART unchanged.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Israel Jericho Atom icon + China D30 Artillery icon\n\n"
        "- Israel Jericho dozer button `AirF_Command_ConstructAmericaParticleCannonUplink`\n"
        "  ButtonImage `isi_jericho` -> existing `Button_Atom` (`Button_Atom.tga`).\n"
        "- China D30 dozer button `Command_ConstructChinaBunker`\n"
        "  ButtonImage `rus_d30` -> existing `Button_Artillery` (`Button_Artillery.tga`).\n"
        "- Objects, command IDs, labels, CommandSet slots, and gameplay unchanged.\n"
        "- ART is the unchanged PR #654 BIG. Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "CommandButton_IsraelJerichoChinaD30Icons.ini last-wins\n"
        "AirF_Command_ConstructAmericaParticleCannonUplink and Command_ConstructChinaBunker.\n"
        "CommandButton.ini, CommandSets, objects, factory Jericho2/3 buttons, and ART are frozen.\n"
        "AirF_AmericaDozerCommandSet still references the same Jericho construct command ID\n"
        "(packed object last-wins as Israel's Jericho silo).\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report))


if __name__ == "__main__":
    main()
