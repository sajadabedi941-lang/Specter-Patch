#!/usr/bin/env python3
"""Batch-repair nine MilitaryHQ objects inside _SPEC_DATA_ONE.big.

Donor: AmericaCommandCenter, the same stable structure used by verified
Egypt_MilitaryHQ and India_MilitaryHQ. Only country identity fields are kept:
Object, Side, DisplayName and country-specific CommandSet.
"""
from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

import build_specter_commandcenter_batch_fixed_big as common

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_COMMANDCENTER_BATCH_TEN_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_MILITARYHQ_BATCH_FIXED"
USA_PATH = r"Data\INI\Object\Specter\United States Of America\Buildings\CommandCenter.ini"

TARGETS = [
    {
        "country": "Israel",
        "side": "Israel",
        "path": r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_MilitaryHQ.ini",
        "tree": "INI/Object/Specter/Israel Defense Forces/Buildings/Israel_MilitaryHQ.ini",
    },
    {
        "country": "Libya",
        "side": "Libya",
        "path": r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_MilitaryHQ.ini",
        "tree": "INI/Object/Specter/Libyan Armed Forces/Buildings/Libya_MilitaryHQ.ini",
    },
    {
        "country": "Pakistan",
        "side": "Pakistan",
        "path": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_MilitaryHQ.ini",
        "tree": "INI/Object/Specter/Pakistan Armed Forces/Buildings/Pakistan_MilitaryHQ.ini",
    },
    {
        "country": "SaudiArabia",
        "side": "SaudiArabia",
        "path": r"Data\INI\Object\Specter\Saudi Arabian Armed Forces\Buildings\SaudiArabia_MilitaryHQ.ini",
        "tree": "INI/Object/Specter/Saudi Arabian Armed Forces/Buildings/SaudiArabia_MilitaryHQ.ini",
    },
    {
        "country": "SouthAfrica",
        "side": "SouthAfrica",
        "path": r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_MilitaryHQ.ini",
        "tree": "INI/Object/Specter/South African National Defence Force/Buildings/SouthAfrica_MilitaryHQ.ini",
    },
    {
        "country": "Syria",
        "side": "Syria",
        "path": r"Data\INI\Object\Specter\Syrian Arab Army\Buildings\Syria_MilitaryHQ.ini",
        "tree": "INI/Object/Specter/Syrian Arab Army/Buildings/Syria_MilitaryHQ.ini",
    },
    {
        "country": "Turkey",
        "side": "Turkey",
        "path": r"Data\INI\Object\Specter\Turkey Armed Forces\Buildings\Turkey_MilitaryHQ.ini",
        "tree": "INI/Object/Specter/Turkey Armed Forces/Buildings/Turkey_MilitaryHQ.ini",
    },
    {
        "country": "Ukraine",
        "side": "Ukraine",
        "path": r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\Ukraine_MilitaryHQ.ini",
        "tree": "INI/Object/Specter/Ukrainian Armed Forces/Buildings/Ukraine_MilitaryHQ.ini",
    },
    {
        "country": "Vietnam",
        "side": "Vietnam",
        "path": r"Data\INI\Object\Specter\Vietnam People's Army\Buildings\Vietnam_MilitaryHQ.ini",
        "tree": "INI/Object/Specter/Vietnam People's Army/Buildings/Vietnam_MilitaryHQ.ini",
    },
]


def identity(old_text: str, country: str) -> dict[str, str]:
    values: dict[str, str] = {}
    patterns = {
        "object": r"(?m)^Object\s+(\S+)",
        "side": r"(?m)^\s*Side\s*=\s*(\S+)",
        "display": r"(?m)^\s*DisplayName\s*=\s*(\S+)",
        "commandset": r"(?m)^\s*CommandSet\s*=\s*(\S+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, old_text)
        if not match:
            raise SystemExit(f"{country}: identity field missing: {key}")
        values[key] = match.group(1)

    expected_object = f"{country}_MilitaryHQ"
    expected_commandset = f"{country}_MilitaryHQCommandSet"
    if values["object"] != expected_object:
        raise SystemExit(f"{country}: unexpected Object {values['object']}")
    if values["commandset"] != expected_commandset:
        raise SystemExit(f"{country}: unexpected CommandSet {values['commandset']}")
    return values


def clone_donor(usa_text: str, ident: dict[str, str]) -> str:
    text = usa_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    while lines and (not lines[0].strip() or lines[0].lstrip().startswith(";")):
        lines.pop(0)
    text = "\n".join(lines)
    if not text.startswith("Object AmericaCommandCenter"):
        raise SystemExit("unexpected AmericaCommandCenter donor")

    text = text.replace(
        "Object AmericaCommandCenter",
        f"Object {ident['object']}",
        1,
    )
    text = re.sub(
        r"(?m)^(  Side\s*=\s*)America\s*$",
        lambda m: m.group(1) + ident["side"],
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(  DisplayName\s*=\s*)OBJECT:\S+\s*$",
        lambda m: m.group(1) + ident["display"],
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(  CommandSet\s*=\s*)AmericaCommandCenterCommandSet\s*$",
        lambda m: m.group(1) + ident["commandset"],
        text,
        count=1,
    )

    # Defensive de-duplication even though the donor currently has one Shadow.
    shadow_seen = False
    clean_lines: list[str] = []
    for line in text.splitlines():
        if re.match(r"^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", line):
            if shadow_seen:
                continue
            shadow_seen = True
        clean_lines.append(line)
    text = "\n".join(clean_lines) + "\n"

    header = (
        f"; SPECTER FIX - {ident['object']}\n"
        "; Donor: AmericaCommandCenter (verified Egypt/India MilitaryHQ method)\n"
        f"; Identity retained: Object / Side={ident['side']} / DisplayName / {ident['commandset']}\n"
        "; All other structure uses the validated donor; no Irq/Adnan clone modules\n"
        "; Patched and extract-verified inside _SPEC_DATA_ONE.big\n\n"
    )
    text = header + text
    text = "".join(c if ord(c) < 128 else "?" for c in text)

    if common.CRASH_TOKENS.search(text):
        raise SystemExit(f"{ident['object']}: wrong-faction crash token remains")
    if "US_Command" not in text or "us_commandcenter" not in text:
        raise SystemExit(f"{ident['object']}: donor art missing")
    return text.replace("\n", "\r\n")


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing current DATA BIG: {SRC}")

    entries = common.parse_big(SRC)
    by = {common.knorm(n): (n, raw) for n, raw in entries}
    art_entries = common.parse_big(ART)
    usa_text = by[common.knorm(USA_PATH)][1].decode("utf-8", "replace")
    donor_ok, donor_issues = common.full_block_check(usa_text)
    if not donor_ok:
        raise SystemExit(f"donor block validation failed: {donor_issues}")
    print("PASS AmericaCommandCenter donor")

    repaired: dict[str, bytes] = {}
    identities: dict[str, dict[str, str]] = {}
    for spec in TARGETS:
        country = spec["country"]
        old = by[common.knorm(spec["path"])][1].decode("utf-8", "replace")
        ident = identity(old, country)
        if ident["side"] != spec["side"]:
            raise SystemExit(f"{country}: Side mismatch {ident['side']}")
        identities[country] = ident
        print(
            f"OLD {country}: nonASCII={sum(ord(c) > 127 for c in old)} "
            f"wrongFaction={bool(common.CRASH_TOKENS.search(old))}"
        )
        repaired[country] = clone_donor(usa_text, ident).encode("ascii")

    path_to_country = {common.knorm(s["path"]): s["country"] for s in TARGETS}
    candidate = [
        (name, repaired[path_to_country[common.knorm(name)]])
        if common.knorm(name) in path_to_country
        else (name, raw)
        for name, raw in entries
    ]

    # Pre-write full validation.
    for spec in TARGETS:
        country = spec["country"]
        ident = identities[country]
        failures = common.validate_cc(
            repaired[country].decode("ascii"),
            expect_object=ident["object"],
            expect_side=ident["side"],
            expect_cmd=ident["commandset"],
            entries=candidate,
            art_entries=art_entries,
            label=f"PREWRITE_{country}",
        )
        if failures:
            print(f"PRE-WRITE FAILED: {country}")
            for failure in failures:
                print(" ", failure)
            return 1
        print(f"PASS pre-write {country}")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    common.write_big(out_big, candidate)
    rebuilt = common.parse_big(out_big)
    rby = {common.knorm(n): (n, raw) for n, raw in rebuilt}

    extract_root = OUT / "_EXTRACT_VERIFY"
    shas: dict[str, str] = {}
    for spec in TARGETS:
        country = spec["country"]
        ident = identities[country]
        entry_name, embedded = rby[common.knorm(spec["path"])]
        if embedded != repaired[country]:
            raise SystemExit(f"{country}: embedded bytes differ from repaired source")
        failures = common.validate_cc(
            embedded.decode("ascii"),
            expect_object=ident["object"],
            expect_side=ident["side"],
            expect_cmd=ident["commandset"],
            entries=rebuilt,
            art_entries=art_entries,
            label=f"EXTRACTED_{country}",
        )
        if failures:
            out_big.unlink(missing_ok=True)
            print(f"EXTRACTED VALIDATION FAILED: {country}")
            for failure in failures:
                print(" ", failure)
            return 1

        rel = Path(*Path(entry_name.replace("\\", "/")).parts)
        extracted = extract_root / rel
        extracted.parent.mkdir(parents=True, exist_ok=True)
        extracted.write_bytes(embedded)
        if extracted.read_bytes() != repaired[country]:
            raise SystemExit(f"{country}: disk extract bytes differ")

        tree = ROOT / "Data" / Path(spec["tree"])
        tree.parent.mkdir(parents=True, exist_ok=True)
        tree.write_bytes(embedded)
        (OUT / f"{country}_MilitaryHQ.ini").write_bytes(embedded)
        shas[country] = common.sha256_bytes(embedded)
        print(f"PASS extract + byte match {country} sha={shas[country]}")

    # Prove no unrelated BIG entry changed.
    old_by = {common.knorm(n): raw for n, raw in entries}
    changed = {
        common.knorm(name)
        for name, raw in rebuilt
        if raw != old_by[common.knorm(name)]
    }
    expected = {common.knorm(s["path"]) for s in TARGETS}
    if changed != expected:
        raise SystemExit(f"unrelated BIG entries changed: {changed ^ expected}")
    if len(shas) != 9:
        raise SystemExit(f"expected 9 repaired MilitaryHQ objects, got {len(shas)}")

    big_sha = common.sha256_file(out_big)
    big_size = out_big.stat().st_size
    report_lines = [
        "SPECTER MILITARYHQ BATCH FIX (9 COUNTRIES) - VERIFY REPORT",
        "==========================================================",
        "VERDICT: PASS",
        "Patched INSIDE: _SPEC_DATA_ONE.big",
        "Donor: AmericaCommandCenter (verified Egypt/India MilitaryHQ method)",
        "Countries: Israel, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, Turkey, Ukraine, Vietnam",
        "Identity retained only: Object, Side, DisplayName, country CommandSet",
        "Removed: Irq/Iraq/Adnan tokens, non-ASCII, duplicate Shadow",
        "Art: US_Command / US_COM_Strb / us_commandcenter",
        "Donor cost/time and modules retained as requested",
        "",
        f"BIG SHA256: {big_sha}",
        f"BIG SIZE:   {big_size}",
        "",
        "Per-country SHA256:",
    ]
    report_lines += [
        f"  {country}_MilitaryHQ.ini {shas[country]}"
        for country in shas
    ]
    report_lines += [
        "",
        "Full Object/Draw/Shadow/ModuleTag/End/W3D/ref validation: PASS x9",
        "Extract-from-BIG byte match: PASS x9",
        "Unrelated BIG entries changed: 0",
        "FINAL: PASS",
        "",
    ]
    report = "\n".join(report_lines)
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT TEST\n"
        "====================\n"
        + "\n".join(
            f"{country}: embedded={shas[country]} match=YES validation=PASS"
            for country in shas
        )
        + f"\nBIG_sha256={big_sha}\nBIG_size={big_size}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER MILITARYHQ BATCH FIX (9)\n"
        "================================\n\n"
        "Repaired inside _SPEC_DATA_ONE.big:\n"
        "Israel, Libya, Pakistan, SaudiArabia, SouthAfrica, Syria,\n"
        "Turkey, Ukraine, Vietnam MilitaryHQ.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        "\n".join(
            [f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}"]
            + [f"{country}_MilitaryHQ.ini SHA256={shas[country]}" for country in shas]
        )
        + "\n",
        encoding="ascii",
    )

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    if final_dir.is_dir():
        shutil.copy2(out_big, final_dir / "_SPEC_DATA_ONE.big")
        for name in ("HASHES.txt", "VERIFY_REPORT.txt", "README_INSTALL.txt", "EMBED_PROOF.txt"):
            shutil.copy2(OUT / name, final_dir / name)
        for country in shas:
            shutil.copy2(
                OUT / f"{country}_MilitaryHQ.ini",
                final_dir / f"{country}_MilitaryHQ.ini",
            )

    zip_path = OUT / "_SPEC_DATA_ONE_MILITARYHQ_BATCH_FIXED.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for spec in TARGETS:
            country = spec["country"]
            zf.write(OUT / f"{country}_MilitaryHQ.ini", f"{country}_MilitaryHQ.ini")
            entry_name = rby[common.knorm(spec["path"])][0]
            rel = Path(*Path(entry_name.replace("\\", "/")).parts)
            zf.write(extract_root / rel, f"EXTRACT_VERIFY/{country}_MilitaryHQ.ini")
        for name in ("VERIFY_REPORT.txt", "EMBED_PROOF.txt", "HASHES.txt", "README_INSTALL.txt"):
            zf.write(OUT / name, name)

    if final_dir.is_dir():
        shutil.copy2(zip_path, final_dir / "_SPEC_DATA_ONE_FINAL.zip")

    print(report)
    print("BIG", out_big, big_sha, big_size)
    print("ZIP", zip_path, common.sha256_file(zip_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
