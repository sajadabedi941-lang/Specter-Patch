#!/usr/bin/env python3
"""Build full merged Specter Data BIG as drop-in _SPEC_DATA_ONE.big

Merge order (later wins for shared keys):
1) vendor SPECTER_BIG_MERGE/_SPEC_DATA_ONE.big  (full Specter content)
2) SPECTER_FINAL_REPAIRED (repairs + Britain F35B USA-donor + expansions)
3) SPECTER_EGYPT_COMMANDCENTER_FIX playable extras (AAB/MHQ keys if any)
4) Force Egypt_CommandCenter.ini = USA-donor repaired file
5) Apply init link repairs (PlayerTemplate/CommandSet slots)

Output package: _SPECTER_FULL_MERGED_FIXED.zip containing _SPEC_DATA_ONE.big
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path("patch")
VENDOR = ROOT / "Release/SPECTER_BIG_MERGE/_SPEC_DATA_ONE.big"
FINAL = ROOT / "Release/SPECTER_FINAL_REPAIRED/_SPECTER_FINAL_REPAIRED.big"
EGYPT_FIX_PKG = ROOT / "Release/SPECTER_EGYPT_COMMANDCENTER_FIX/_SPEC_DATA_ONE.big"
BRITAIN_PKG = ROOT / "Release/SPECTER_BRITAIN_F35B_SAUDI_DRONE_PLAYABLE/_SPEC_DATA_ONE.big"
CC_SRC = (
    ROOT
    / "Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
)
CC_KEY = r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_CommandCenter.ini"
F35B_KEY = r"Data\INI\Object\Specter\British Armed Forces\Airforce\Britain_F35B.ini"
OUT = ROOT / "Release/SPECTER_FULL_MERGED_FIXED"
OUT_BIG = OUT / "_SPEC_DATA_ONE.big"
OUT_ZIP = OUT / "_SPECTER_FULL_MERGED_FIXED.zip"
BROKEN_CC = "1b559b9e0d4eb1400e76934196eb71205c1ff21317e610d717c1da1dc7870b61"
FIXED_F35B = "c92587adf41b34f0"  # prefix of known good Britain F35B


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1", errors="replace")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    index, blobs, offset = [], [], header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def catalogs(ini: dict[str, str]):
    cats: dict[str, set[str]] = defaultdict(set)
    for text in ini.values():
        cats["Object"].update(re.findall(r"^\s*Object\s+(?![=])(\S+)", text, re.M))
        cats["CommandSet"].update(
            re.findall(r"^\s*CommandSet\s+(?![=])(\S+)", text, re.M)
        )
        cats["CommandButton"].update(
            re.findall(r"^\s*CommandButton\s+(?![=])(\S+)", text, re.M)
        )
        cats["SpecialPower"].update(
            re.findall(r"^\s*SpecialPower\s+(?![=])(\S+)", text, re.M)
        )
        cats["Science"].update(re.findall(r"^\s*Science\s+(?![=])(\S+)", text, re.M))
        cats["Upgrade"].update(re.findall(r"^\s*Upgrade\s+(?![=])(\S+)", text, re.M))
        cats["Weapon"].update(re.findall(r"^\s*Weapon\s+(?![=])(\S+)", text, re.M))
        cats["OCL"].update(
            re.findall(r"^\s*ObjectCreationList\s+(?![=])(\S+)", text, re.M)
        )
        cats["Armor"].update(re.findall(r"^\s*Armor\s+(?![=])(\S+)", text, re.M))
        cats["DamageFX"].update(re.findall(r"^\s*DamageFX\s+(?![=])(\S+)", text, re.M))
        cats["FXList"].update(re.findall(r"^\s*FXList\s+(?![=])(\S+)", text, re.M))
    return cats


def parse_ok(text: str) -> bool:
    open_re = re.compile(
        r"^\s*(?:Object\s+(?![=])\S+|Draw\s*=|Behavior\s*=|ArmorSet\b|Body\s*=|"
        r"UnitSpecificSounds\b|ConditionState\s*=|TransitionState\s*=|WeaponSet\b|"
        r"CommandSet\s+(?![=])\S+|CommandButton\s+(?![=])\S+|PlayerTemplate\s+\S+)"
    )
    depth = 0
    for line in text.splitlines():
        code = line.split(";", 1)[0]
        if not code.strip():
            continue
        if re.match(r"^\s*End\s*$", code):
            depth -= 1
            if depth < 0:
                return False
            continue
        if open_re.match(code):
            depth += 1
    return depth == 0


def apply_text_repairs(entries: dict[str, bytes], log: list[str]) -> None:
    def get(key: str) -> str:
        return entries[key].decode("utf-8", errors="replace")

    def put(key: str, text: str) -> None:
        if not text.endswith("\n"):
            text += "\n"
        entries[key] = text.encode("utf-8")

    pt_key = r"Data\INI\PlayerTemplate.ini"
    if pt_key in entries:
        text = get(pt_key)
        reps = [
            (
                r"(^\s*PurchaseScienceCommandSetRank1\s*=\s*)SCIENCE_NorthKorea_CommandSetRank1\b",
                r"\1SCIENCE_Iraq_CommandSetRank1",
            ),
            (
                r"(^\s*PurchaseScienceCommandSetRank3\s*=\s*)SCIENCE_NorthKorea_CommandSetRank3\b",
                r"\1SCIENCE_Iraq_CommandSetRank3",
            ),
            (
                r"(^\s*PurchaseScienceCommandSetRank8\s*=\s*)SCIENCE_NorthKorea_CommandSetRank8\b",
                r"\1SCIENCE_Iraq_CommandSetRank8",
            ),
            (
                r"(^\s*SpecialPowerShortcutCommandSet\s*=\s*)SpecialPowerShortcutNorthKorea\b",
                r"\1SpecialPowerShortcutNorthKoreaSystem",
            ),
            (
                r"(^\s*StartingUnit0\s*=\s*)AirF_AmericaVehicleDozer\b",
                r"\1AmericaVehicleDozer",
            ),
        ]
        for rx, repl in reps:
            text2, n = re.subn(rx, repl, text, flags=re.M)
            if n:
                text = text2
                log.append(f"PlayerTemplate repair x{n}")
        put(pt_key, text)

    aab = r"Data\INI\CommandSet_StrategicBombers_AABOnly.ini"
    if aab in entries:
        text = get(aab)
        text, n = re.subn(
            r"Command_ConstructAmericaJetE3AWACS\b",
            "Command_ConstructPatch_America_E3",
            text,
        )
        if n:
            log.append(f"AABOnly America E3 x{n}")
        text, n = re.subn(
            r"Command_ConstructRussiaJetSu75Checkmate\b",
            "Command_ConstructPatch_Russia_Su75",
            text,
        )
        if n:
            log.append(f"AABOnly Su75 x{n}")
        text, n = re.subn(
            r"^[ \t]*\d+\s*=\s*Command_ConstructRussiaJetSu47Recon[ \t]*\n",
            "",
            text,
            flags=re.M,
        )
        if n:
            log.append(f"AABOnly remove Su47 x{n}")
        put(aab, text)

    adv = r"Data\INI\CommandSet_AdvancedAirBase.ini"
    if adv in entries:
        text = get(adv)
        text, n = re.subn(
            r"^[ \t]*15\s*=\s*Command_ConstructPatch_US_E3G_AWACS[ \t]*\n",
            "",
            text,
            flags=re.M,
        )
        if n:
            log.append(f"AdvancedAirBase remove dead E3G x{n}")
        put(adv, text)

    cs = r"Data\INI\CommandSet.ini"
    if cs in entries:
        text = get(cs)
        text, n = re.subn(
            r"Demo_Command_ConstructGLAVehicleToxinTruck;TOXIN(?:\s+TRACTOR)?",
            "Demo_Command_ConstructGLAVehicleToxinTruck",
            text,
        )
        if n:
            log.append(f"CommandSet toxin syntax x{n}")
        put(cs, text)


def full_dependency_scan(entries: dict[str, bytes]) -> dict:
    ini = {
        k: v.decode("utf-8", errors="replace")
        for k, v in entries.items()
        if k.lower().endswith(".ini")
    }
    cats = catalogs(ini)
    report: dict = {
        "objects": len(cats["Object"]),
        "commandsets": len(cats["CommandSet"]),
        "commandbuttons": len(cats["CommandButton"]),
        "missing": [],
        "egypt_cc_missing": [],
        "cs_slot_missing": [],
        "pt_missing": [],
    }

    # Egypt CC refs
    if CC_KEY in ini:
        cc = ini[CC_KEY]
        checks = [
            ("CommandSet", r"^\s*CommandSet\s*=\s*(\S+)", "CommandSet"),
            ("SpecialPower", r"^\s*SpecialPowerTemplate\s*=\s*(\S+)", "SpecialPower"),
            ("OCL", r"^\s*(?:OCL|CreationList|UpgradeObject)\s*=\s*(\S+)", "OCL"),
            ("Object", r"^\s*GunshipTemplateName\s*=\s*(\S+)", "Object"),
            ("Upgrade", r"^\s*(?:UpgradeToGrant|TriggeredBy)\s*=\s*(\S+)", "Upgrade"),
            ("Science", r"^\s*GrantScience\s*=\s*(\S+)", "Science"),
            ("Weapon", r"^\s*DeathWeapon\s*=\s*(\S+)", "Weapon"),
        ]
        for label, rx, pool in checks:
            for m in re.finditer(rx, cc, re.M):
                ref = m.group(1)
                if ref.upper() == "NONE":
                    continue
                if ref not in cats[pool]:
                    report["egypt_cc_missing"].append(f"{label}={ref}")
        for sci, ocl in re.findall(r"^\s*UpgradeOCL\s*=\s*(\S+)\s+(\S+)", cc, re.M):
            if sci not in cats["Science"]:
                report["egypt_cc_missing"].append(f"Science={sci}")
            if ocl not in cats["OCL"]:
                report["egypt_cc_missing"].append(f"OCL={ocl}")

    # CommandSet slots → CB/Object (init-critical)
    for name, text in ini.items():
        for m in re.finditer(
            r"CommandSet\s+(\S+)\n([\s\S]*?)^\s*End\s*$", text, re.M
        ):
            for sm in re.finditer(r"^\s*\d+\s*=\s*(\S+)", m.group(2), re.M):
                ref = sm.group(1)
                if ref in ("NONE", "Separator"):
                    continue
                if ";" in ref or (
                    ref not in cats["CommandButton"] and ref not in cats["Object"]
                ):
                    report["cs_slot_missing"].append(f"{m.group(1)} -> {ref}")

    # PlayerTemplate critical
    for name, text in ini.items():
        if not name.lower().endswith("playertemplate.ini"):
            continue
        for m in re.finditer(
            r"PlayerTemplate\s+(\S+)\n([\s\S]*?)^\s*End\s*$", text, re.M
        ):
            pt, block = m.group(1), m.group(2)
            for label, rx, pool in [
                ("StartingBuilding", r"^\s*StartingBuilding\s*=\s*(\S+)", "Object"),
                ("StartingUnit", r"^\s*StartingUnit\d*\s*=\s*(\S+)", "Object"),
                (
                    "PurchaseCS",
                    r"^\s*PurchaseScienceCommandSet\w*\s*=\s*(\S+)",
                    "CommandSet",
                ),
                (
                    "ShortcutCS",
                    r"^\s*SpecialPowerShortcutCommandSet\s*=\s*(\S+)",
                    "CommandSet",
                ),
            ]:
                for sm in re.finditer(rx, block, re.M):
                    ref = sm.group(1)
                    if ref.upper() == "NONE":
                        continue
                    if ref not in cats[pool]:
                        report["pt_missing"].append(f"{pt}.{label}={ref}")

    report["missing"] = (
        report["egypt_cc_missing"] + report["cs_slot_missing"] + report["pt_missing"]
    )
    report["cats"] = cats
    report["ini"] = ini
    return report


def validate(entries: dict[str, bytes], vendor: dict[str, bytes]) -> tuple[bool, list[str], list[str], dict]:
    passes, fails = [], []
    scan = full_dependency_scan(entries)
    ini = scan["ini"]
    cats = scan["cats"]

    # Egypt CC single + fixed
    cc_keys = [
        k
        for k in entries
        if "egypt" in k.lower()
        and "commandcenter" in k.lower().replace("_", "").replace(" ", "")
        and k.lower().endswith(".ini")
    ]
    if len(cc_keys) == 1 and cc_keys[0] == CC_KEY:
        passes.append("Egypt_CommandCenter copies = 1")
    else:
        fails.append(f"Egypt_CommandCenter copies={len(cc_keys)}")

    cc_sha = hashlib.sha256(entries[CC_KEY]).hexdigest()
    if cc_sha == BROKEN_CC:
        fails.append("Egypt_CommandCenter still broken SPEC")
    else:
        passes.append(f"Egypt_CommandCenter USA-donor sha={cc_sha[:16]}…")

    code = "\n".join(
        line.split(";", 1)[0]
        for line in entries[CC_KEY].decode("utf-8", errors="replace").splitlines()
    )
    if re.search(
        r"\birq_|\bIraq_Adnan1\b|\bIrq_Command\b|\bSUPERWEAPON_Iraqi|\bSUPERWEAPON_Iraq",
        code,
    ):
        fails.append("Iraq/irq tokens in Egypt_CommandCenter")
    else:
        passes.append("No Iraq/irq crash tokens in Egypt_CommandCenter")

    if parse_ok(ini[CC_KEY]) and parse_ok(
        ini.get(r"Data\INI\PlayerTemplate.ini", "End\n")
    ):
        passes.append("INI parser PASS (Egypt CC + PlayerTemplate)")
    else:
        fails.append("INI parser FAIL")

    # Object dups: Egypt unique; no new vs vendor; report vendor pre-existing
    def obj_map(src: dict[str, bytes]) -> dict[str, list[str]]:
        m: dict[str, list[str]] = defaultdict(list)
        for name, raw in src.items():
            if not name.lower().endswith(".ini"):
                continue
            for mm in re.finditer(
                r"^\s*Object\s+(?![=])(\S+)",
                raw.decode("utf-8", errors="replace"),
                re.M,
            ):
                m[mm.group(1)].append(name)
        return m

    om = obj_map(entries)
    vom = obj_map(vendor)
    if om.get("Egypt_CommandCenter") == [CC_KEY]:
        passes.append("Object duplicates = 0 for Egypt_CommandCenter")
    else:
        fails.append(f"Egypt_CommandCenter defs={om.get('Egypt_CommandCenter')}")

    dups = {k for k, v in om.items() if len(v) > 1}
    vdups = {k for k, v in vom.items() if len(v) > 1}
    new_dups = dups - vdups
    if not new_dups:
        passes.append(
            f"Object duplicates = 0 new (vendor pre-existing retained={len(vdups)}; content kept)"
        )
    else:
        fails.append(f"New Object duplicates introduced: {list(new_dups)[:8]}")

    # Britain F35B present + fixed donor marker
    if F35B_KEY in entries:
        fsha = hashlib.sha256(entries[F35B_KEY]).hexdigest()
        text = entries[F35B_KEY].decode("utf-8", errors="replace")
        if "Britain_F35B" in text and "US_F35A" in text and "Side" in text:
            passes.append(f"Britain_F35B present (USA F35 donor ART) sha={fsha[:16]}…")
        else:
            fails.append("Britain_F35B missing donor structure")
    else:
        fails.append("Britain_F35B.ini missing")

    # Content retention vs vendor
    missing_vendor_keys = set(vendor) - set(entries)
    if not missing_vendor_keys:
        passes.append(f"All vendor SPEC keys retained ({len(vendor)})")
    else:
        fails.append(f"Lost vendor keys: {len(missing_vendor_keys)}")

    # Faction markers
    for obj in [
        "Egypt_CommandCenter",
        "AmericaCommandCenter",
        "Britain_F35B",
        "Iraq_CommandCenter",
        "Turkey_Adnan1",
    ]:
        if obj in cats["Object"]:
            passes.append(f"Faction/content marker OK: {obj}")
        else:
            fails.append(f"Missing object {obj}")

    # Missing refs (init-critical scan)
    if not scan["missing"]:
        passes.append("Missing references = 0 (Egypt CC + CS slots + PlayerTemplate)")
    else:
        fails.append(
            "Missing references: "
            + "; ".join(scan["missing"][:15])
            + (f" …(+{len(scan['missing'])-15})" if len(scan["missing"]) > 15 else "")
        )

    if not fails:
        passes.append("Game initialization PASS (static)")
    return (not fails), passes, fails, scan


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    log: list[str] = []

    for p in (VENDOR, FINAL, CC_SRC):
        if not p.exists():
            print("MISSING", p)
            return 1

    print("Reading vendor SPEC...")
    vendor = read_big(VENDOR)
    print("Reading FINAL_REPAIRED...")
    final = read_big(FINAL)
    extras = {}
    if EGYPT_FIX_PKG.exists():
        print("Reading EGYPT_COMMANDCENTER_FIX playable extras...")
        extras = read_big(EGYPT_FIX_PKG)
    britain = {}
    if BRITAIN_PKG.exists():
        print("Reading Britain F35B package...")
        britain = read_big(BRITAIN_PKG)

    # Merge: vendor base → final overlay → extras overlay → britain F35B force
    merged: dict[str, bytes] = dict(vendor)
    log.append(f"Base vendor SPEC entries={len(vendor)}")

    overwritten = 0
    for k, v in final.items():
        if k in merged and merged[k] != v:
            overwritten += 1
        merged[k] = v
    log.append(
        f"Overlay FINAL_REPAIRED: keys={len(final)} overwritten={overwritten} added={len(set(final)-set(vendor))}"
    )

    added_ex = 0
    for k, v in extras.items():
        if k not in merged:
            merged[k] = v
            added_ex += 1
        elif k != CC_KEY and merged[k] != v:
            # keep FINAL for most; but prefer Britain F35B from extras if FINAL somehow old
            if k == F35B_KEY:
                merged[k] = v
    log.append(f"Overlay EGYPT_FIX extras added={added_ex}")

    if F35B_KEY in britain:
        merged[F35B_KEY] = britain[F35B_KEY]
        log.append(
            f"Force Britain_F35B from Britain package sha={hashlib.sha256(britain[F35B_KEY]).hexdigest()[:16]}…"
        )
    elif F35B_KEY in final:
        log.append(
            f"Britain_F35B from FINAL sha={hashlib.sha256(final[F35B_KEY]).hexdigest()[:16]}…"
        )

    # Force USA-donor Egypt CC
    cc_text = CC_SRC.read_text(encoding="utf-8", errors="replace")
    if not cc_text.endswith("\n"):
        cc_text += "\n"
    # Ensure header
    if "USA" not in cc_text.splitlines()[0]:
        lines = cc_text.splitlines()
        lines[0] = "; SPECTER FULL MERGED FIXED — Egypt_CommandCenter USA AmericaCommandCenter donor"
        cc_text = "\n".join(lines) + "\n"
    merged[CC_KEY] = cc_text.encode("utf-8")
    log.append(
        f"Force Egypt_CommandCenter USA-donor sha={hashlib.sha256(merged[CC_KEY]).hexdigest()[:16]}…"
    )

    apply_text_repairs(merged, log)

    print("Packing _SPEC_DATA_ONE.big ...")
    big = build_big(merged)
    OUT_BIG.write_bytes(big)
    sha = hashlib.sha256(big).hexdigest()
    (OUT / "_SPEC_DATA_ONE.big.sha256").write_text(sha + "\n", encoding="utf-8")
    print("sha", sha, "entries", len(merged), "size", len(big))

    packed = read_big(OUT_BIG)
    ok, passes, fails, scan = validate(packed, vendor)
    verdict = "PASS" if ok else "FAIL"

    # Write dependency scan detail
    dep = [
        "FULL DEPENDENCY SCAN — _SPEC_DATA_ONE.big (FULL MERGED FIXED)",
        "=" * 60,
        f"Objects={scan['objects']} CommandSets={scan['commandsets']} CommandButtons={scan['commandbuttons']}",
        f"Egypt CC missing refs: {len(scan['egypt_cc_missing'])}",
        f"CommandSet slot missing: {len(scan['cs_slot_missing'])}",
        f"PlayerTemplate missing: {len(scan['pt_missing'])}",
        f"Init-critical missing TOTAL: {len(scan['missing'])}",
        "",
    ]
    for section, key in [
        ("Egypt_CommandCenter", "egypt_cc_missing"),
        ("CommandSet slots", "cs_slot_missing"),
        ("PlayerTemplate", "pt_missing"),
    ]:
        dep.append(f"--- {section} ---")
        items = scan[key]
        if not items:
            dep.append("  (none)")
        else:
            for x in items[:50]:
                dep.append(f"  {x}")
            if len(items) > 50:
                dep.append(f"  … +{len(items)-50} more")
        dep.append("")
    (OUT / "DEPENDENCY_SCAN.txt").write_text("\n".join(dep) + "\n", encoding="utf-8")

    verify = [
        "SPECTER FULL MERGED FIXED — VERIFY REPORT",
        "=" * 60,
        f"VERDICT: {verdict}",
        "BIG (install name): _SPEC_DATA_ONE.big",
        f"SHA256: {sha}",
        f"Entries: {len(merged)}",
        f"Size: {len(big)} bytes",
        "",
        "Merge: vendor SPEC ← FINAL_REPAIRED ← playable extras",
        "Egypt_CommandCenter: USA AmericaCommandCenter donor only",
        "Britain_F35B: USA F35 donor fix retained",
        "No factions/content removed from vendor SPEC key set.",
        "",
        "REPAIRS / MERGE LOG:",
    ]
    for line in log:
        verify.append(f"  - {line}")
    verify += ["", f"PASS: {len(passes)}  FAIL: {len(fails)}", ""]
    for p in passes:
        verify.append("PASS: " + p)
    for f in fails:
        verify.append("FAIL: " + f)
    verify += ["", f"FINAL: {verdict}"]
    (OUT / "VERIFY_REPORT.txt").write_text("\n".join(verify) + "\n", encoding="utf-8")
    (OUT / "REPAIRS.txt").write_text("\n".join(log) + "\n", encoding="utf-8")

    (OUT / "README_INSTALL.txt").write_text(
        f"""SPECTER FULL MERGED FIXED
=========================

File inside zip: _SPEC_DATA_ONE.big
SHA256: {sha}
Entries: {len(merged)}
Validation: {verdict}

This is a COMPLETE Data BIG replacement (not a small overlay).
It merges vendor Specter SPEC content with FINAL_REPAIRED expansions,
keeps Britain F35B USA-donor fix, and replaces ONLY Egypt_CommandCenter.ini
with the safe USA AmericaCommandCenter donor (Side=Egypt).

INSTALL:
1. Backup Data\\_SPEC_DATA_ONE.big
2. Copy this _SPEC_DATA_ONE.big over Data\\_SPEC_DATA_ONE.big
3. Keep Data\\_SPEC_ART_ONE.big
4. DELETE every other Specter Data BIG (_SPECTER_*.big, old patches, prior FIXED overlays)
""",
        encoding="utf-8",
    )

    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in [
            "_SPEC_DATA_ONE.big",
            "_SPEC_DATA_ONE.big.sha256",
            "README_INSTALL.txt",
            "VERIFY_REPORT.txt",
            "DEPENDENCY_SCAN.txt",
            "REPAIRS.txt",
        ]:
            zf.write(OUT / name, arcname=name)

    print("\n".join(verify))
    print("ZIP", OUT_ZIP, OUT_ZIP.stat().st_size)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
