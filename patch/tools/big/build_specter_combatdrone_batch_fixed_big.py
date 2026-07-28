#!/usr/bin/env python3
"""Batch-repair CombatDrone INIs inside _SPEC_DATA_ONE.big.

Targets: India, Sweden, SouthKorea, SaudiArabia, Japan, Italy
Pattern: France/Germany CombatDrone fix (USA AmericaDronesMq9 donor).

For each country:
  - Clone USA MQ9 structure
  - Keep Object Country_CombatDrone / Side / DisplayName
  - Keep Country_Weapon_ATGM + 2x_GBU12II_Mq9
  - Prerequisites: Country_AdvancedAirBase + SCIENCE_Rank3 only
  - Keep country BuildCost/BuildTime
  - Remove non-ASCII, SCIENCE_UAEStealthJet, duplicate Shadow

Writes repaired files INTO the DATA BIG; extract-verifies every drone.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_INDIA_MHQ_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_COMBATDRONE_BATCH_FIXED"

USA_PATH = r"Data\INI\Object\Specter\United States Of America\Drones\Mq9.ini"

# country -> (BIG path, Side, expected Object, tree relative under patch/Data/...)
TARGETS: list[dict] = [
    {
        "country": "India",
        "side": "India",
        "path": r"Data\INI\Object\Specter\Indian Armed Forces\Drones\India_CombatDrone.ini",
        "tree": "INI/Object/Specter/Indian Armed Forces/Drones/India_CombatDrone.ini",
    },
    {
        "country": "Sweden",
        "side": "Sweden",
        "path": r"Data\INI\Object\Specter\Swedish Armed Forces\Drones\Sweden_CombatDrone.ini",
        "tree": "INI/Object/Specter/Swedish Armed Forces/Drones/Sweden_CombatDrone.ini",
    },
    {
        "country": "SouthKorea",
        "side": "SouthKorea",
        "path": r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Drones\SouthKorea_CombatDrone.ini",
        "tree": "INI/Object/Specter/Republic of Korea Armed Forces/Drones/SouthKorea_CombatDrone.ini",
    },
    {
        "country": "SaudiArabia",
        "side": "SaudiArabia",
        "path": r"Data\INI\Object\Specter\Saudi Arabian Armed Forces\Drones\SaudiArabia_CombatDrone.ini",
        "tree": "INI/Object/Specter/Saudi Arabian Armed Forces/Drones/SaudiArabia_CombatDrone.ini",
    },
    {
        "country": "Japan",
        "side": "Japan",
        "path": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Drones\Japan_CombatDrone.ini",
        "tree": "INI/Object/Specter/Japan Self-Defense Forces/Drones/Japan_CombatDrone.ini",
    },
    {
        "country": "Italy",
        "side": "Italy",
        "path": r"Data\INI\Object\Specter\Italian Armed Forces\Drones\Italy_CombatDrone.ini",
        "tree": "INI/Object/Specter/Italian Armed Forces/Drones/Italy_CombatDrone.ini",
    },
]

PRESERVE = {
    r"Data\INI\Object\Specter\French Armed Forces\Drones\France_CombatDrone.ini": (
        "7512cca46c234c6951a54d5a982184209d203668738c4e1336fdaab1e1ba8df2"
    ),
    r"Data\INI\Object\Specter\German Armed Forces\Drones\Germany_CombatDrone.ini": (
        "663b32b1de6111bd1496463bc042f642d204782a525f103c63440d92d380e8b2"
    ),
    r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\India_EliteStrike.ini": (
        "0f9af6019f0976cd219d393f94fda3e17bb6d74eeb933513a0f48aa13b665533"
    ),
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_CommandCenter.ini": (
        "29d084b8c5fa23fe047961bf9cc3ce33714a64c4168f09bce275d00938f1b93b"
    ),
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_MilitaryHQ.ini": (
        "8ee8db3c9d91901bc6b60c4489429dd555664cf42b77482c99e5cedd15d4ec43"
    ),
}

OPENERS = [
    (re.compile(r"^\s*Object\s+(?![=])\S+"), "Object"),
    (re.compile(r"^\s*Draw\s*="), "Draw"),
    (re.compile(r"^\s*Behavior\s*="), "Behavior"),
    (re.compile(r"^\s*Body\s*="), "Body"),
    (re.compile(r"^\s*ArmorSet\b"), "ArmorSet"),
    (re.compile(r"^\s*WeaponSet\b"), "WeaponSet"),
    (re.compile(r"^\s*Prerequisites\b"), "Prerequisites"),
    (re.compile(r"^\s*UnitSpecificSounds\b"), "UnitSpecificSounds"),
    (re.compile(r"^\s*DefaultConditionState\b"), "DefaultConditionState"),
    (re.compile(r"^\s*ConditionState\s*="), "ConditionState"),
    (re.compile(r"^\s*TransitionState\s*="), "TransitionState"),
]

UAE_CODE = re.compile(r"(?i)\bSCIENCE_UAE|\bUAEAirfield\b|\bUAEStealth")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def knorm(name: str) -> str:
    return name.lower().replace("/", "\\")


def parse_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    entries = []
    pos = 16
    for _ in range(count):
        offset, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos = end + 1
        entries.append((name, data[offset : offset + size]))
    return entries


def write_big(path: Path, entries) -> None:
    header_size = 16
    for name, _ in entries:
        header_size += 8 + len(name.encode("latin-1")) + 1
    while header_size % 4:
        header_size += 1
    blobs, index, cursor = [], [], header_size
    for name, raw in entries:
        blobs.append(raw)
        index.append((name, cursor, len(raw)))
        cursor += len(raw)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", cursor)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for name, offset, size in index:
        out += struct.pack(">II", offset, size)
        out += name.encode("latin-1") + b"\x00"
    while len(out) < header_size:
        out += b"\x00"
    for blob in blobs:
        out += blob
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))


def full_block_check(text: str) -> tuple[bool, list[str]]:
    issues: list[str] = []
    stack: list[tuple[str, int]] = []
    for i, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0]
        if not code.strip():
            continue
        if re.match(r"^\s*End\s*$", code):
            if not stack:
                issues.append(f"EXTRA End @{i}")
            else:
                stack.pop()
            continue
        for rx, kind in OPENERS:
            if rx.match(code):
                stack.append((kind, i))
                break
    if stack:
        issues.append("UNCLOSED " + ",".join(f"{k}@{i}" for k, i in stack))
    return (not issues), issues


def catalog(entries):
    cats: dict[str, set[str]] = defaultdict(set)
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("utf-8", "replace")
        cats["Object"].update(re.findall(r"(?m)^Object\s+(?![=])(\S+)", t))
        cats["CommandSet"].update(re.findall(r"(?m)^CommandSet\s+(\S+)", t))
        cats["Weapon"].update(re.findall(r"(?m)^Weapon\s+(\S+)", t))
        cats["Science"].update(re.findall(r"(?m)^Science\s+(\S+)", t))
        cats["Upgrade"].update(re.findall(r"(?m)^Upgrade\s+(\S+)", t))
        cats["Armor"].update(re.findall(r"(?m)^Armor\s+(\S+)", t))
        cats["Locomotor"].update(re.findall(r"(?m)^Locomotor\s+(\S+)", t))
        cats["MappedImage"].update(re.findall(r"(?m)^MappedImage\s+(\S+)", t))
        cats["OCL"].update(re.findall(r"(?m)^ObjectCreationList\s+(\S+)", t))
    return cats


def code_only(text: str) -> str:
    return "\n".join(line.split(";", 1)[0] for line in text.splitlines())


def validate_drone(
    text: str,
    *,
    expect_object: str,
    expect_side: str,
    expect_weapon: str,
    expect_aab: str,
    entries,
    art_entries,
    label: str,
) -> list[str]:
    fails: list[str] = []
    cats = catalog(entries)
    data_join = b"\n".join(b for _, b in entries)

    if any(ord(c) > 127 for c in text):
        fails.append(f"{label}: non-ASCII")
    ok, issues = full_block_check(text)
    if not ok:
        fails.append(f"{label}: block {issues}")
    objs = re.findall(r"(?m)^Object\s+(\S+)", text)
    if objs != [expect_object]:
        fails.append(f"{label}: Object={objs}")
    if not re.search(rf"(?m)^  Side\s*=\s*{re.escape(expect_side)}\s*$", text):
        fails.append(f"{label}: Side!={expect_side}")
    if not re.search(r"(?m)^\s*Draw\s*=\s*W3DModelDraw\b", text):
        fails.append(f"{label}: Draw missing")
    shadows = re.findall(r"(?m)^\s*Shadow\s*=\s*(\S+)", text)
    if len(shadows) != 1 or shadows[0] != "SHADOW_VOLUME":
        fails.append(f"{label}: Shadow={shadows}")
    tags = re.findall(r"ModuleTag_\S+", text)
    dups = [t for t, c in Counter(tags).items() if c > 1]
    if dups:
        fails.append(f"{label}: dup ModuleTags {dups}")
    if "Geometry" not in text:
        fails.append(f"{label}: Geometry missing")
    if expect_weapon not in text:
        fails.append(f"{label}: weapon missing {expect_weapon}")
    if "2x_GBU12II_Mq9" not in text:
        fails.append(f"{label}: secondary GBU missing")
    if expect_aab not in text:
        fails.append(f"{label}: AAB prereq missing")
    if UAE_CODE.search(code_only(text)):
        fails.append(f"{label}: UAE tokens in code {UAE_CODE.findall(code_only(text))}")
    if "SCIENCE_UAEStealthJet" in code_only(text):
        fails.append(f"{label}: SCIENCE_UAEStealthJet in code")

    def need(kind: str, vals: list[str]) -> None:
        for v in vals:
            if v in ("None", "NONE"):
                continue
            if v not in cats[kind] and v.encode() not in data_join:
                fails.append(f"{label}: missing {kind}={v}")

    need("CommandSet", re.findall(r"(?m)^\s*CommandSet\s*=\s*(\S+)", text))
    need("Weapon", re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", text))
    need("Armor", re.findall(r"(?m)^\s*Armor\s*=\s*(\S+)", text))
    need("Science", re.findall(r"(?m)^\s*Science\s*=\s*(\S+)", text))
    need("Object", re.findall(r"(?m)^\s*Object\s*=\s*(\S+)", text))
    need(
        "Upgrade",
        re.findall(r"(?m)^\s*(?:UpgradeCameo\d*|TriggeredBy|UpgradeToGrant)\s*=\s*(\S+)", text),
    )
    need("MappedImage", re.findall(r"(?m)^\s*(?:SelectPortrait|ButtonImage)\s*=\s*(\S+)", text))
    need("Locomotor", re.findall(r"(?m)^\s*Locomotor\s*=\s*\S+\s+(\S+)", text))

    for m in set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)):
        if m in ("None", "NONE"):
            continue
        w3d = [
            n
            for n, _ in art_entries
            if m.lower() in knorm(n) and n.lower().endswith(".w3d")
        ]
        if not w3d:
            fails.append(f"{label}: ModelW3D missing {m}")
    return fails


def extract_identity(broken: str, country: str) -> tuple[str, str]:
    cost_m = re.search(r"(?m)^\s*BuildCost\s*=\s*(\S+)", broken)
    time_m = re.search(r"(?m)^\s*BuildTime\s*=\s*(\S+)", broken)
    if not cost_m or not time_m:
        raise SystemExit(f"{country}: missing BuildCost/Time")
    return cost_m.group(1), time_m.group(1)


def clone_usa_to_country(
    usa_text: str,
    *,
    country: str,
    side: str,
    build_cost: str,
    build_time: str,
) -> str:
    obj = f"{country}_CombatDrone"
    weapon = f"{country}_Weapon_ATGM"
    aab = f"{country}_AdvancedAirBase"

    text = usa_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    i = 0
    while i < len(lines) and (lines[i].strip() == "" or lines[i].lstrip().startswith(";")):
        i += 1
    text = "\n".join(lines[i:])
    if not text.startswith("Object AmericaDronesMq9"):
        raise SystemExit("unexpected USA MQ9 start")

    text = text.replace("Object AmericaDronesMq9", f"Object {obj}", 1)
    text = re.sub(r"(?m)^(  Side\s*=\s*)America\s*$", rf"\1{side}", text, count=1)
    text = re.sub(
        r"(?m)^(  DisplayName\s*=\s*)OBJECT:\S+\s*$",
        rf"\1OBJECT:{obj}",
        text,
        count=1,
    )
    text = re.sub(
        r"(?ms)^  Prerequisites\n.*?^  End",
        "  Prerequisites\n"
        f"    Object = {aab}\n"
        "    Science = SCIENCE_Rank3\n"
        "  End",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(    Weapon\s*=\s*PRIMARY\s+)\S+\s*$",
        rf"\1{weapon}",
        text,
        count=1,
    )
    text = re.sub(r"(?m)^(  BuildCost\s*=\s*)\S+", rf"\g<1>{build_cost}", text, count=1)
    text = re.sub(r"(?m)^(  BuildTime\s*=\s*)\S+", rf"\g<1>{build_time}", text, count=1)

    seen_shadow = False
    out_lines: list[str] = []
    for line in text.split("\n"):
        if re.match(r"^\s*Shadow\s*=\s*SHADOW_VOLUME\s*$", line):
            if seen_shadow:
                continue
            seen_shadow = True
        out_lines.append(line)
    text = "\n".join(out_lines)

    header = (
        f"; SPECTER FIX - {obj}\n"
        f"; Donor: USA AmericaDronesMq9 (Mq9.ini) - France/Germany CombatDrone pattern\n"
        f"; Keep: Object {obj} / Side={side} / {aab} / {weapon}\n"
        f"; Cost/time preserved from country balance ({build_cost}/{build_time})\n"
        f"; Removed: non-ASCII, SCIENCE_UAEStealthJet, duplicate Shadow\n"
        f"\n"
    )
    text = header + text
    text = "".join(c if ord(c) < 128 else "?" for c in text)

    if f"Object {obj}" not in text:
        raise SystemExit(f"{country}: object missing")
    if not re.search(rf"(?m)^  Side\s*=\s*{re.escape(side)}\s*$", text):
        raise SystemExit(f"{country}: side missing")
    if weapon not in text or "2x_GBU12II_Mq9" not in text:
        raise SystemExit(f"{country}: weapons missing")
    if aab not in text:
        raise SystemExit(f"{country}: AAB missing")
    if UAE_CODE.search(code_only(text)):
        raise SystemExit(f"{country}: UAE leftovers in code")
    if "Object AmericaDronesMq9" in text:
        raise SystemExit(f"{country}: donor name remain")
    return text.replace("\n", "\r\n")


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG {SRC}")
    entries = parse_big(SRC)
    by = {knorm(n): (n, b) for n, b in entries}
    art_entries = parse_big(ART) if ART.is_file() else []
    if knorm(USA_PATH) not in by:
        raise SystemExit("USA Mq9.ini missing")

    usa_text = by[knorm(USA_PATH)][1].decode("utf-8", "replace")
    # Donor may carry duplicate Shadow (clone step de-dupes). Validate structure lightly.
    if not re.search(r"(?m)^Object\s+AmericaDronesMq9\b", usa_text):
        raise SystemExit("USA MQ9 Object missing")
    if not re.search(r"(?m)^\s*Draw\s*=\s*W3DModelDraw\b", usa_text):
        raise SystemExit("USA MQ9 Draw missing")
    if "US_MQ9" not in usa_text or "Nat_mq9" not in usa_text:
        raise SystemExit("USA MQ9 art missing")
    if "2x_GBU12II_Mq9" not in usa_text:
        raise SystemExit("USA MQ9 secondary weapon missing")
    ok_d, issues_d = full_block_check(usa_text)
    if not ok_d:
        print("DONOR BLOCK FAIL", issues_d)
        return 1
    print("PASS donor AmericaDronesMq9 (clone will de-dupe Shadow)")

    repaired: dict[str, bytes] = {}
    identities: dict[str, tuple[str, str]] = {}

    for spec in TARGETS:
        country = spec["country"]
        path = spec["path"]
        if knorm(path) not in by:
            raise SystemExit(f"missing {path}")
        broken = by[knorm(path)][1].decode("utf-8", "replace")
        cost, btime = extract_identity(broken, country)
        identities[country] = (cost, btime)
        old_issues = []
        if any(ord(c) > 127 for c in broken):
            old_issues.append("non-ASCII")
        if len(re.findall(r"(?m)^\s*Shadow\s*=", broken)) != 1:
            old_issues.append("dup/missing Shadow")
        if "SCIENCE_UAEStealthJet" in code_only(broken):
            old_issues.append("SCIENCE_UAEStealthJet")
        print(f"OLD {country}: {old_issues or ['clean?']}")

        repl = clone_usa_to_country(
            usa_text,
            country=country,
            side=spec["side"],
            build_cost=cost,
            build_time=btime,
        )
        repaired[country] = repl.encode("ascii")

    # Pre-write validate with temp entry list
    tmp = [(n, b) for n, b in entries]
    tmp_by = {knorm(n): i for i, (n, _) in enumerate(tmp)}
    for spec in TARGETS:
        country = spec["country"]
        path = spec["path"]
        idx = tmp_by[knorm(path)]
        tmp[idx] = (tmp[idx][0], repaired[country])

    for spec in TARGETS:
        country = spec["country"]
        obj = f"{country}_CombatDrone"
        weapon = f"{country}_Weapon_ATGM"
        aab = f"{country}_AdvancedAirBase"
        text = repaired[country].decode("ascii")
        fails = validate_drone(
            text,
            expect_object=obj,
            expect_side=spec["side"],
            expect_weapon=weapon,
            expect_aab=aab,
            entries=tmp,
            art_entries=art_entries,
            label=country,
        )
        if fails:
            print(f"PRE-WRITE FAIL {country}")
            for f in fails:
                print(" ", f)
            return 1
        print(f"PASS pre-write {country}")

    # Build new entries
    path_set = {knorm(s["path"]) for s in TARGETS}
    path_to_country = {knorm(s["path"]): s["country"] for s in TARGETS}
    new_entries: list[tuple[str, bytes]] = []
    for name, blob in entries:
        k = knorm(name)
        if k in path_set:
            new_entries.append((name, repaired[path_to_country[k]]))
        else:
            new_entries.append((name, blob))

    OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT / "_SPEC_DATA_ONE.big"
    if out_big.exists():
        out_big.unlink()
    write_big(out_big, new_entries)

    rebuilt = parse_big(out_big)
    rby = {knorm(n): (n, b) for n, b in rebuilt}

    extract_root = OUT / "_EXTRACT_VERIFY"
    shas: dict[str, str] = {}

    for spec in TARGETS:
        country = spec["country"]
        path = spec["path"]
        if knorm(path) not in rby:
            raise SystemExit(f"EXTRACT FAIL missing {path}")
        ename, ebytes = rby[knorm(path)]
        if ebytes != repaired[country]:
            raise SystemExit(f"EXTRACT FAIL bytes mismatch {country}")
        etext = ebytes.decode("ascii")
        fails = validate_drone(
            etext,
            expect_object=f"{country}_CombatDrone",
            expect_side=spec["side"],
            expect_weapon=f"{country}_Weapon_ATGM",
            expect_aab=f"{country}_AdvancedAirBase",
            entries=rebuilt,
            art_entries=art_entries,
            label=f"EXTRACTED_{country}",
        )
        if fails:
            out_big.unlink(missing_ok=True)
            print(f"EXTRACTED VALIDATION FAILED {country} - BIG deleted")
            for f in fails:
                print(" ", f)
            return 1

        # write extract path mirroring BIG
        rel = Path(*Path(ename.replace("\\", "/")).parts)
        ep = extract_root / rel
        ep.parent.mkdir(parents=True, exist_ok=True)
        ep.write_bytes(ebytes)
        if ep.read_bytes() != repaired[country]:
            raise SystemExit(f"disk extract mismatch {country}")

        # tree sync
        tree = ROOT / "Data" / Path(spec["tree"])
        tree.parent.mkdir(parents=True, exist_ok=True)
        tree.write_bytes(ebytes)
        (OUT / f"{country}_CombatDrone.ini").write_bytes(ebytes)
        shas[country] = sha256_bytes(ebytes)
        print(f"PASS extract {country} sha={shas[country]}")

    for path, expect in PRESERVE.items():
        got = sha256_bytes(rby[knorm(path)][1])
        if got != expect:
            raise SystemExit(f"preserve lost {path}: {got}")

    # Only the 6 drone paths should change
    old_by = {knorm(n): b for n, b in entries}
    changed = [n for n, b in rebuilt if old_by[knorm(n)] != b]
    expected_changed = {knorm(s["path"]) for s in TARGETS}
    if {knorm(n) for n in changed} != expected_changed:
        raise SystemExit(f"unexpected changed entries: {changed}")

    big_sha = sha256_file(out_big)
    big_size = out_big.stat().st_size

    report_lines = [
        "SPECTER COMBATDRONE BATCH FIX - VERIFY REPORT",
        "============================================",
        "VERDICT: PASS",
        "Patched INSIDE: _SPEC_DATA_ONE.big",
        "Donor: USA AmericaDronesMq9 (France/Germany pattern)",
        "Countries: India, Sweden, SouthKorea, SaudiArabia, Japan, Italy",
        "Removed per file: non-ASCII, SCIENCE_UAEStealthJet, duplicate Shadow",
        "Kept: Object/Side/Country_Weapon_ATGM/Country_AdvancedAirBase/cost-time",
        f"",
        f"BIG SHA256: {big_sha}",
        f"BIG SIZE:   {big_size}",
        "",
        "Per-country SHA256:",
    ]
    for spec in TARGETS:
        c = spec["country"]
        cost, btime = identities[c]
        report_lines.append(f"  {c}_CombatDrone.ini {shas[c]} cost={cost} time={btime}")
    report_lines += [
        "",
        "Validation: donor PASS, pre-write PASS, extract-from-BIG PASS (all 6)",
        "Preserved: France/Germany CombatDrone, India EliteStrike/CC/MHQ",
        "FINAL: PASS",
        "",
    ]
    report = "\n".join(report_lines)
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT TEST\n"
        "====================\n"
        + "\n".join(
            f"{c}: embedded={shas[c]} extracted_match=YES"
            for c in [s["country"] for s in TARGETS]
        )
        + f"\nBIG_sha256={big_sha}\nBIG_size={big_size}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER COMBATDRONE BATCH FIX\n"
        "=============================\n\n"
        "Repaired inside _SPEC_DATA_ONE.big:\n"
        "  India, Sweden, SouthKorea, SaudiArabia, Japan, Italy CombatDrone\n"
        "Pattern: USA MQ9 donor (same as France/Germany).\n"
        "Removed: non-ASCII, SCIENCE_UAEStealthJet, duplicate Shadow.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )
    hash_lines = [f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}"]
    for spec in TARGETS:
        c = spec["country"]
        hash_lines.append(f"{c}_CombatDrone.ini SHA256={shas[c]}")
    (OUT / "HASHES.txt").write_text("\n".join(hash_lines) + "\n", encoding="ascii")

    for sync in [
        ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL",
        ROOT / "Release" / "SPECTER_FINAL_EGYPT_BRITAIN_FIXED",
    ]:
        if sync.is_dir():
            shutil.copy2(out_big, sync / "_SPEC_DATA_ONE.big")

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    for name in ("HASHES.txt", "VERIFY_REPORT.txt", "README_INSTALL.txt", "EMBED_PROOF.txt"):
        shutil.copy2(OUT / name, final_dir / name)
    for spec in TARGETS:
        c = spec["country"]
        shutil.copy2(OUT / f"{c}_CombatDrone.ini", final_dir / f"{c}_CombatDrone.ini")

    zpath = OUT / "_SPEC_DATA_ONE_COMBATDRONE_BATCH_FIXED.zip"
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for spec in TARGETS:
            c = spec["country"]
            zf.write(OUT / f"{c}_CombatDrone.ini", f"{c}_CombatDrone.ini")
            # extract proof
            ename = rby[knorm(spec["path"])][0]
            rel = Path(*Path(ename.replace("\\", "/")).parts)
            zf.write(extract_root / rel, f"EXTRACT_VERIFY/{c}_CombatDrone.ini")
        zf.write(OUT / "VERIFY_REPORT.txt", "VERIFY_REPORT.txt")
        zf.write(OUT / "EMBED_PROOF.txt", "EMBED_PROOF.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "README_INSTALL.txt", "README_INSTALL.txt")

    final_zip = final_dir / "_SPEC_DATA_ONE_FINAL.zip"
    if final_zip.exists():
        final_zip.unlink()
    shutil.copy2(zpath, final_zip)

    print(report)
    print("BIG", out_big, big_sha, big_size)
    print("ZIP", zpath, sha256_file(zpath))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
