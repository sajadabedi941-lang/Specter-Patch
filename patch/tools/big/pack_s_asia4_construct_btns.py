#!/usr/bin/env python3
"""Audit NK / SK / Japan / Vietnam construction buttons for four required images.

Baseline: PR #618 SPECTER_EU8_CONSTRUCT_BTNS
  DATA 366676852 SHA bae544986974b2c4b96e9071024091f96833b686796dd6bdf0d233003a4603ee
  ART  1306947794 SHA 2a89dd356f1b3938fc9f34b6f63572e758c5f96f2486dfe578daab737b2cc8a7

Required mappings, only where those construction buttons actually exist:
  LGM30G        -> Button_Atom
  M777          -> Button_Artillery
  IRIS-T SLX    -> Button_AirDefense
  Strategy Center -> Button_GlobalMarket

Packed last-wins audit found none of those four construct buttons on
North Korea, South Korea, Japan, or Vietnam. No CommandButton, CommandSet,
or ART mutation is performed. Archives are identical to PR #618.
Static validation only.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_EU8_CONSTRUCT_BTNS/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_EU8_CONSTRUCT_BTNS/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_ASIA4_CONSTRUCT_BTNS"

SHA_DATA_618 = "bae544986974b2c4b96e9071024091f96833b686796dd6bdf0d233003a4603ee"
SIZE_DATA_618 = 366676852
SHA_ART_618 = "2a89dd356f1b3938fc9f34b6f63572e758c5f96f2486dfe578daab737b2cc8a7"
SIZE_ART_618 = 1306947794

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"

COUNTRIES = [
    ("North Korea", "NorthKorea", "NorthKorea_VT72BCommandSet"),
    ("South Korea", "SouthKorea", "SouthKorea_VT72BCommandSet"),
    ("Japan", "Japan", "Japan_VT72BCommandSet"),
    ("Vietnam", "Vietnam", "Vietnam_VT72BCommandSet"),
]

REQUIRED = [
    ("LGM30G", ("lgm30", "lgm-30"), "Button_Atom"),
    ("M777", ("m777",), "Button_Artillery"),
    ("IRIS-T SLX", ("irist", "iris-t", "iris_t"), "Button_AirDefense"),
    ("Strategy Center", ("strategycenter", "strategy_center"), "Button_GlobalMarket"),
]


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes) -> dict[str, bytes]:
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


def last_blocks(blob: bytes, header: bytes) -> dict[str, str]:
    last = {}
    lines = blob.splitlines(True)
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith(header):
            name = ln.split(None, 1)[-1].strip().decode("latin1", "replace")
            start = i
            i += 1
            while i < len(lines):
                if lines[i] in (b"End\r\n", b"End\n", b"End", b"END\r\n", b"END\n", b"END"):
                    last[name] = b"".join(lines[start : i + 1]).decode("latin1")
                    i += 1
                    break
                i += 1
            else:
                break
        else:
            i += 1
    return last


def field(body: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(\S+)", body, re.M)
    return m.group(1) if m else ""


def art_has(art: dict[str, bytes], stem: str) -> bool:
    return rf"Art\Textures\{stem}.tga".lower() in {k.lower() for k in art}


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_618 or SRC_DATA.stat().st_size != SIZE_DATA_618:
        raise SystemExit("DATA baseline mismatch vs PR #618")
    if sha256_path(SRC_ART) != SHA_ART_618 or SRC_ART.stat().st_size != SIZE_ART_618:
        raise SystemExit("ART baseline mismatch vs PR #618")

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    buttons = last_blocks(src_data[CB_KEY], b"CommandButton ")
    sets = last_blocks(src_data[CS_KEY], b"CommandSet ")

    fails = []
    for _, _, cs_name in COUNTRIES:
        if cs_name not in sets:
            fails.append(f"missing CommandSet {cs_name}")
    for stem in ("Button_Atom", "Button_Artillery", "Button_AirDefense", "Button_GlobalMarket"):
        if not art_has(src_art, stem):
            fails.append(f"missing packed TGA {stem}")

    inventory = []
    found_required = []
    for country, prefix, cs_name in COUNTRIES:
        body = sets[cs_name]
        inventory.append(f"## {country}  CommandSet={cs_name}")
        for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", body, re.M):
            slot, btn = m.group(1), m.group(2)
            block = buttons.get(btn, "")
            inventory.append(
                f"  slot {slot:>2} | {btn} | {field(block, 'Object') or '-'} | "
                f"{field(block, 'Command') or '?'} | {field(block, 'ButtonImage') or '?'}"
            )
        inventory.append("")
        inventory.append(f"  Required-mapping status for {country}:")
        for label, needles, want in REQUIRED:
            hits = []
            for name, block in buttons.items():
                if field(block, "Command") != "DOZER_CONSTRUCT":
                    continue
                blob = (name + " " + field(block, "Object")).lower()
                if prefix.lower() not in name.lower() and prefix.lower() not in field(block, "Object").lower():
                    continue
                if any(n in blob.replace("-", "").replace("_", "") or n in blob for n in needles):
                    hits.append((name, field(block, "Object"), field(block, "ButtonImage")))
            # also accept shared America LGM30 if this dozer references it
            if label == "LGM30G":
                if "Command_ConstructAmericaLgm30" in body:
                    block = buttons["Command_ConstructAmericaLgm30"]
                    hits.append(
                        (
                            "Command_ConstructAmericaLgm30",
                            field(block, "Object"),
                            field(block, "ButtonImage"),
                        )
                    )
            if hits:
                for name, obj, img in hits:
                    found_required.append((country, label, name, obj, img, want))
                    ok = img == want
                    inventory.append(
                        f"    {label}: {name} Object={obj} ButtonImage={img} "
                        f"want {want} | {'OK' if ok else 'NEEDS CHANGE'}"
                    )
                    if not ok:
                        fails.append(f"{country} {label} is {img} want {want}")
            else:
                inventory.append(
                    f"    {label}: DOES NOT EXIST — no {label} DOZER_CONSTRUCT button "
                    f"on {cs_name} or as a {prefix} construct CommandButton"
                )
        inventory.append("")

    if found_required:
        fails.append(f"unexpected required-button hits: {found_required}")

    # No mutations allowed for this audit-only pack.
    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    shutil.copy2(SRC_DATA, data_path)
    shutil.copy2(SRC_ART, art_path)

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    for _, _, cs_name in COUNTRIES:
        (ext / f"{cs_name}.ini").write_text(sets[cs_name] + "\n")
    (ext / "INVENTORY.txt").write_text("\n".join(inventory) + "\n")

    data_sha = sha256_path(data_path)
    art_sha = sha256_path(art_path)
    if data_sha != SHA_DATA_618 or art_sha != SHA_ART_618:
        raise SystemExit("copied archives drifted from PR #618")

    zip_path = ROOT / "patch/Release/SPECTER_ASIA4_CONSTRUCT_BTNS.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sha256_path(zip_path)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #618 s-eu8-construct-btns",
        "DATA_CHANGED=NO",
        "ART_CHANGED=NO",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "COMMANDSET_UNCHANGED=YES",
        "COMMANDBUTTON_UNCHANGED=YES",
        "",
        "REQUIRED MAPPINGS — NONE EXIST FOR THESE FOUR COUNTRIES:",
        "  LGM30G          — no construct button / object",
        "  M777            — no construct button / object",
        "  IRIS-T SLX      — no construct button / object",
        "  Strategy Center — no construct button / object",
        "",
        "Closest existing construct options (NOT remapped; different buildings):",
        "  NuclearCenter -> {Country}_Abbas  (Abbas superweapon, not LGM30G)",
        "  D30_SAFE      -> {Country}_D30_Howitzer  (D-30, not M777)",
        "  Hq9_Site      -> {Country}_Hq9_Site  (HQ-9, not IRIS-T SLX)",
        "  Sam2_SAFE     -> {Country}_Sam2  (S-125, not on current VT72B slots except unused buttons)",
        "  No Strategy Center object or construct button",
        "",
        "No CommandButtons invented. No CommandSets changed. Archives identical to PR #618.",
        "",
        "COMPLETE BUILDER INVENTORY:",
        *inventory,
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n")
    (OUT / "INVENTORY.txt").write_text("\n".join(inventory) + "\n")
    hashes = "\n".join(
        [
            "DATA_CHANGED=NO",
            "ART_CHANGED=NO",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_SIZE={art_path.stat().st_size}",
            f"ART_SHA256={art_sha}",
            "ZIP_FILE=SPECTER_ASIA4_CONSTRUCT_BTNS.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #618",
            "STATIC_VALIDATION=PASS",
            "RUNTIME_TEST=NOT RUN",
            "",
        ]
    )
    (OUT / "HASHES.txt").write_text(hashes)
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA replacement (identical to PR #618):",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-asia4-construct-btns/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement (identical to PR #618):",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-asia4-construct-btns/_SPEC_ART_ONE.big",
                f"  SIZE={art_path.stat().st_size}",
                f"  SHA256={art_sha}",
                "",
                "ZIP:",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-asia4-construct-btns/SPECTER_ASIA4_CONSTRUCT_BTNS.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both BIGs in the SPECTER folder.",
                "TAG=s-asia4-construct-btns",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-asia4-construct-btns",
                "BASELINE=PR #618",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Audit of North Korea, South Korea, Japan, and Vietnam construction buttons.\n"
        "LGM30G, M777, IRIS-T SLX, and Strategy Center construct buttons do not exist.\n"
        "No DATA/ART mutation. Archives identical to PR #618. Static validation only.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Asia-4 construction-button audit (NK / SK / Japan / Vietnam)\n\n"
        "- Packed last-wins audit of each country's VT72B construction CommandSet.\n"
        "- LGM30G, M777, IRIS-T SLX, and Strategy Center construction buttons do not exist for these countries.\n"
        "- No CommandButtons invented. No CommandSets or gameplay changed.\n"
        "- Replacement BIGs are identical to PR #618.\n"
        "- Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "No DATA or ART mutations. No last-wins conflicts.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report[:40]))


if __name__ == "__main__":
    main()
