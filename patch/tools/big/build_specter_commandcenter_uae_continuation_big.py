#!/usr/bin/env python3
"""Add the remaining UAE CommandCenter repair to the completed 9-country BIG.

This continuation does not rebuild the previous nine repairs. It opens their
validated output BIG, replaces only UAE_CommandCenter.ini, then validates and
extract-verifies all ten repaired CommandCenters.
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import build_specter_commandcenter_batch_fixed_big as batch

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_COMMANDCENTER_BATCH_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_COMMANDCENTER_BATCH_TEN_FIXED"

USA_PATH = r"Data\INI\Object\Specter\United States Of America\Buildings\CommandCenter.ini"
UAE = {
    "country": "UAE",
    "side": "UAE",
    "path": r"Data\INI\Object\Specter\United Arab Emirates\Buildings\UAE_CommandCenter.ini",
    "tree": "INI/Object/Specter/United Arab Emirates/Buildings/UAE_CommandCenter.ini",
}

PREVIOUS = batch.TARGETS
ALL_TARGETS = PREVIOUS + [UAE]

PREVIOUS_SHAS = {
    "Libya": "2d1268d8632d435f0174edb1692fa3b21af3cd9f7c934bef48da2c1cc5c7b75a",
    "Pakistan": "f569c8ffb5822d39e2f334cd077e9d24a4900ab0b41e1cd47875d54bdebf2e6e",
    "SaudiArabia": "026ad6416fa7c02a8fb19399b6b691fa4f2b3f8e4d34d825927e34d47a758764",
    "SouthAfrica": "96b286aa669bf1c146a209bd9b27e6e4250826e58469e5cf3aa383982ac8d5b8",
    "Syria": "86f5b1f44c83fa6baabd2a9b64f8ea2b57205f52cb3ac9df61571429dc9a7976",
    "Turkey": "51d934aa00a4e96f0b94d224e84fc48963b5349f037e1ef329e39249e71f9c63",
    "Israel": "ffceba90e9d764faa7a10d308f6b094d2bbaa5a0818abfba680f6995fbd73e31",
    "Ukraine": "9606f25bafb6400bc13f1aa061389213c5a76ddfb3439a59c8b4c89cad83c4f0",
    "Vietnam": "a7cb4c7127f95f68853b597eeae80c1bf3ae20ecff951858122d99c765603084",
}


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing completed 9-country BIG: {SRC}")

    entries = batch.parse_big(SRC)
    by = {batch.knorm(n): (n, raw) for n, raw in entries}
    art_entries = batch.parse_big(ART)

    # Prove the prior nine are exactly the completed repairs before continuing.
    for spec in PREVIOUS:
        country = spec["country"]
        got = batch.sha256_bytes(by[batch.knorm(spec["path"])][1])
        if got != PREVIOUS_SHAS[country]:
            raise SystemExit(f"prior repair changed: {country} {got}")
    print("PASS preserved completed 9-country BIG")

    old_name, old_raw = by[batch.knorm(UAE["path"])]
    old_text = old_raw.decode("utf-8", "replace")
    ident = batch.extract_identity(old_text, "UAE")
    if ident["side"] != "UAE":
        raise SystemExit(f"unexpected UAE Side token: {ident['side']}")
    print(
        "OLD UAE issues:",
        "non-ASCII" if any(ord(c) > 127 for c in old_text) else "",
        "Irq/Iraq" if batch.CRASH_TOKENS.search(old_text) else "",
    )

    usa_text = by[batch.knorm(USA_PATH)][1].decode("utf-8", "replace")
    repaired_text = batch.clone_usa_to_country(usa_text, ident)
    repaired = repaired_text.encode("ascii")

    tmp_entries = [
        (name, repaired if batch.knorm(name) == batch.knorm(UAE["path"]) else raw)
        for name, raw in entries
    ]
    fails = batch.validate_cc(
        repaired_text,
        expect_object="UAE_CommandCenter",
        expect_side="UAE",
        expect_cmd="UAE_CommandCenterCommandSet",
        entries=tmp_entries,
        art_entries=art_entries,
        label="UAE_PREWRITE",
    )
    if fails:
        print("UAE PRE-WRITE VALIDATION FAILED")
        for failure in fails:
            print(" ", failure)
        return 1
    print("PASS UAE pre-write validation")

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    batch.write_big(out_big, tmp_entries)

    rebuilt = batch.parse_big(out_big)
    rby = {batch.knorm(n): (n, raw) for n, raw in rebuilt}
    extract_root = OUT / "_EXTRACT_VERIFY"
    identities: dict[str, dict] = {}
    shas: dict[str, str] = {}

    # Validate and extract all ten; the first nine compare to their existing
    # repaired source bytes, UAE compares to the new replacement.
    for spec in ALL_TARGETS:
        country = spec["country"]
        entry_name, embedded = rby[batch.knorm(spec["path"])]
        expected = repaired if country == "UAE" else by[batch.knorm(spec["path"])][1]
        if embedded != expected:
            raise SystemExit(f"embedded byte mismatch: {country}")

        text = embedded.decode("ascii")
        country_ident = batch.extract_identity(text, country)
        identities[country] = country_ident
        failures = batch.validate_cc(
            text,
            expect_object=country_ident["object"],
            expect_side=country_ident["side"],
            expect_cmd=country_ident["commandset"],
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
        extract_path = extract_root / rel
        extract_path.parent.mkdir(parents=True, exist_ok=True)
        extract_path.write_bytes(embedded)
        if extract_path.read_bytes() != expected:
            raise SystemExit(f"disk extract byte mismatch: {country}")

        tree_path = ROOT / "Data" / Path(spec["tree"])
        tree_path.parent.mkdir(parents=True, exist_ok=True)
        tree_path.write_bytes(embedded)
        (OUT / f"{country}_CommandCenter.ini").write_bytes(embedded)
        shas[country] = batch.sha256_bytes(embedded)
        print(f"PASS extract + full validation {country} sha={shas[country]}")

    if len(shas) != 10:
        raise SystemExit(f"expected 10 validated CommandCenters, got {len(shas)}")

    # Continuation must alter only UAE relative to the completed nine-country BIG.
    changed = [
        name
        for name, raw in rebuilt
        if raw != by[batch.knorm(name)][1]
    ]
    if changed != [old_name]:
        raise SystemExit(f"continuation changed files other than UAE: {changed}")

    # Preserve earlier cumulative repairs.
    for path, expected in batch.PRESERVE.items():
        if "Egypt_CommandCenter" in path:
            continue
        got = batch.sha256_bytes(rby[batch.knorm(path)][1])
        if got != expected:
            raise SystemExit(f"cumulative repair lost: {path} {got}")

    big_sha = batch.sha256_file(out_big)
    big_size = out_big.stat().st_size
    report_lines = [
        "SPECTER COMMANDCENTER BATCH FIX (10 COUNTRIES) - VERIFY REPORT",
        "==============================================================",
        "VERDICT: PASS",
        "Continuation source: validated 9-country CommandCenter BIG",
        "Continuation change: UAE_CommandCenter.ini ONLY",
        "Patched INSIDE: _SPEC_DATA_ONE.big",
        "Donor: AmericaCommandCenter (Egypt/India CC method)",
        "Countries: Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, Turkey, Israel, Ukraine, Vietnam, UAE",
        "Removed: Irq/Iraq donor tokens, non-ASCII, duplicate Shadow",
        "Kept: Object/Side/DisplayName/CommandSet/cost-time",
        "Art: US_Command / US_COM_Strb / us_commandcenter",
        "",
        f"BIG SHA256: {big_sha}",
        f"BIG SIZE:   {big_size}",
        "",
        "Per-country SHA256:",
    ]
    for spec in ALL_TARGETS:
        country = spec["country"]
        country_ident = identities[country]
        report_lines.append(
            f"  {country}_CommandCenter.ini {shas[country]} "
            f"cost={country_ident['cost']} time={country_ident['time']} "
            f"CS={country_ident['commandset']}"
        )
    report_lines += [
        "",
        "Validation: full parse/Object/Draw/Shadow/ModuleTag/End/W3D/art PASS x10",
        "Extract-from-BIG byte match: PASS x10",
        "Only UAE changed relative to completed 9-country BIG: PASS",
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
        "SPECTER COMMANDCENTER BATCH FIX (10)\n"
        "====================================\n\n"
        "Repaired inside _SPEC_DATA_ONE.big:\n"
        "Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, Turkey,\n"
        "Israel, Ukraine, Vietnam, UAE CommandCenter.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        "\n".join(
            [f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}"]
            + [f"{country}_CommandCenter.ini SHA256={shas[country]}" for country in shas]
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
                OUT / f"{country}_CommandCenter.ini",
                final_dir / f"{country}_CommandCenter.ini",
            )

    zip_path = OUT / "_SPEC_DATA_ONE_COMMANDCENTER_BATCH_TEN_FIXED.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for spec in ALL_TARGETS:
            country = spec["country"]
            zf.write(
                OUT / f"{country}_CommandCenter.ini",
                f"{country}_CommandCenter.ini",
            )
            entry_name = rby[batch.knorm(spec["path"])][0]
            rel = Path(*Path(entry_name.replace("\\", "/")).parts)
            zf.write(
                extract_root / rel,
                f"EXTRACT_VERIFY/{country}_CommandCenter.ini",
            )
        for name in ("VERIFY_REPORT.txt", "EMBED_PROOF.txt", "HASHES.txt", "README_INSTALL.txt"):
            zf.write(OUT / name, name)

    final_zip = final_dir / "_SPEC_DATA_ONE_FINAL.zip"
    if final_dir.is_dir():
        shutil.copy2(zip_path, final_zip)

    print(report)
    print("BIG", out_big, big_sha, big_size)
    print("ZIP", zip_path, batch.sha256_file(zip_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
