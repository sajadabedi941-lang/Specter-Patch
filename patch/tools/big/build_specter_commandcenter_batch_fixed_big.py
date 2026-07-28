#!/usr/bin/env python3
"""Batch-repair 9 CommandCenter INIs inside _SPEC_DATA_ONE.big.

Countries: Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, Turkey,
Israel, Ukraine, Vietnam.

Donor: AmericaCommandCenter (same method as Egypt_CC / India_CC).
Keep country Object/Side/DisplayName/CommandSet/cost/time.
Remove Irq/Iraq crash tokens, non-ASCII, duplicate Shadow.
Extract-verify every repaired file inside the BIG.
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
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_JAPAN_UAE_MQ9_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_COMMANDCENTER_BATCH_FIXED"

USA_PATH = r"Data\INI\Object\Specter\United States Of America\Buildings\CommandCenter.ini"

TARGETS: list[dict] = [
    {
        "country": "Libya",
        "side": "Libya",
        "path": r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_CommandCenter.ini",
        "tree": "INI/Object/Specter/Libyan Armed Forces/Buildings/Libya_CommandCenter.ini",
    },
    {
        "country": "Pakistan",
        "side": "Pakistan",
        "path": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_CommandCenter.ini",
        "tree": "INI/Object/Specter/Pakistan Armed Forces/Buildings/Pakistan_CommandCenter.ini",
    },
    {
        "country": "SaudiArabia",
        "side": "SaudiArabia",
        "path": r"Data\INI\Object\Specter\Saudi Arabian Armed Forces\Buildings\SaudiArabia_CommandCenter.ini",
        "tree": "INI/Object/Specter/Saudi Arabian Armed Forces/Buildings/SaudiArabia_CommandCenter.ini",
    },
    {
        "country": "SouthAfrica",
        "side": "SouthAfrica",
        "path": r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_CommandCenter.ini",
        "tree": "INI/Object/Specter/South African National Defence Force/Buildings/SouthAfrica_CommandCenter.ini",
    },
    {
        "country": "Syria",
        "side": "Syria",
        "path": r"Data\INI\Object\Specter\Syrian Arab Army\Buildings\Syria_CommandCenter.ini",
        "tree": "INI/Object/Specter/Syrian Arab Army/Buildings/Syria_CommandCenter.ini",
    },
    {
        "country": "Turkey",
        "side": "Turkey",
        "path": r"Data\INI\Object\Specter\Turkey Armed Forces\Buildings\Turkey_CommandCenter.ini",
        "tree": "INI/Object/Specter/Turkey Armed Forces/Buildings/Turkey_CommandCenter.ini",
    },
    {
        "country": "Israel",
        "side": "Israel",
        "path": r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_CommandCenter.ini",
        "tree": "INI/Object/Specter/Israel Defense Forces/Buildings/Israel_CommandCenter.ini",
    },
    {
        "country": "Ukraine",
        "side": "Ukraine",
        "path": r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\Ukraine_CommandCenter.ini",
        "tree": "INI/Object/Specter/Ukrainian Armed Forces/Buildings/Ukraine_CommandCenter.ini",
    },
    {
        "country": "Vietnam",
        "side": "Vietnam",
        "path": r"Data\INI\Object\Specter\Vietnam People's Army\Buildings\Vietnam_CommandCenter.ini",
        "tree": "INI/Object/Specter/Vietnam People's Army/Buildings/Vietnam_CommandCenter.ini",
    },
]

PRESERVE = {
    r"Data\INI\Object\Specter\French Armed Forces\Drones\France_CombatDrone.ini": (
        "7512cca46c234c6951a54d5a982184209d203668738c4e1336fdaab1e1ba8df2"
    ),
    r"Data\INI\Object\Specter\German Armed Forces\Drones\Germany_CombatDrone.ini": (
        "663b32b1de6111bd1496463bc042f642d204782a525f103c63440d92d380e8b2"
    ),
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_CommandCenter.ini": (
        "29d084b8c5fa23fe047961bf9cc3ce33714a64c4168f09bce275d00938f1b93b"
    ),
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_MilitaryHQ.ini": (
        "8ee8db3c9d91901bc6b60c4489429dd555664cf42b77482c99e5cedd15d4ec43"
    ),
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\Japan_MQ9.ini": (
        "34c8dcffc78caaeb559f8f8e5dbc5e64842fc10291b19bcef22efcdb7d4014cf"
    ),
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAE_MQ9.ini": (
        "6fe4ad1b0a98ac50b069f2b6d6e6082b81620bd24e998516ef4dc985d347fa09"
    ),
}

CRASH_TOKENS = re.compile(
    r"Irq_Command|irq_comndcntr|Iraq_Adnan1|SUPERWEAPON_Iraqi|SUPERWEAPON_Iraq|"
    r"Iraq_CommandCenter|Object Iraq_",
    re.I,
)

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
        cats["MappedImage"].update(re.findall(r"(?m)^MappedImage\s+(\S+)", t))
        cats["OCL"].update(re.findall(r"(?m)^ObjectCreationList\s+(\S+)", t))
        cats["SpecialPower"].update(re.findall(r"(?m)^SpecialPower\s+(\S+)", t))
    return cats


def validate_cc(
    text: str,
    *,
    expect_object: str,
    expect_side: str,
    expect_cmd: str,
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
    if expect_cmd not in text:
        fails.append(f"{label}: CommandSet missing {expect_cmd}")
    if not re.search(r"(?m)^\s*Draw\s*=\s*W3DModelDraw\b", text):
        fails.append(f"{label}: Draw missing")
    shadows = re.findall(r"(?m)^\s*Shadow\s*=\s*(\S+)", text)
    if len(shadows) != 1 or shadows[0] != "SHADOW_VOLUME":
        fails.append(f"{label}: Shadow={shadows}")
    tags = re.findall(r"ModuleTag_\S+", text)
    dups = [t for t, c in Counter(tags).items() if c > 1]
    if dups:
        fails.append(f"{label}: dup ModuleTags {dups}")
    if "Geometry" not in text or "GeometryMajorRadius" not in text:
        fails.append(f"{label}: Geometry missing")
    if "COMMANDCENTER" not in text:
        fails.append(f"{label}: KindOf COMMANDCENTER missing")
    if "US_Command" not in text or "us_commandcenter" not in text:
        fails.append(f"{label}: USA CC art missing")
    if CRASH_TOKENS.search(text):
        fails.append(f"{label}: crash tokens {CRASH_TOKENS.findall(text)}")

    def need(kind: str, vals: list[str]) -> None:
        for v in vals:
            if v in ("None", "NONE"):
                continue
            if v not in cats[kind] and v.encode() not in data_join:
                fails.append(f"{label}: missing {kind}={v}")

    need("CommandSet", re.findall(r"(?m)^\s*CommandSet\s*=\s*(\S+)", text))
    need("Armor", re.findall(r"(?m)^\s*Armor\s*=\s*(\S+)", text))
    need("Science", re.findall(r"(?m)^\s*(?:Science|GrantScience)\s*=\s*(\S+)", text))
    need("Object", re.findall(r"(?m)^\s*Object\s*=\s*(\S+)", text))
    need(
        "Upgrade",
        re.findall(r"(?m)^\s*(?:UpgradeCameo\d*|TriggeredBy|UpgradeToGrant)\s*=\s*(\S+)", text),
    )
    need("MappedImage", re.findall(r"(?m)^\s*(?:SelectPortrait|ButtonImage)\s*=\s*(\S+)", text))
    need("OCL", re.findall(r"(?m)^\s*(?:OCL|CreationList|UpgradeObject)\s*=\s*(\S+)", text))
    need("OCL", re.findall(r"(?m)^\s*UpgradeOCL\s*=\s*\S+\s+(\S+)", text))
    need("SpecialPower", re.findall(r"(?m)^\s*SpecialPowerTemplate\s*=\s*(\S+)", text))
    need("Object", re.findall(r"(?m)^\s*GunshipTemplateName\s*=\s*(\S+)", text))

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


def extract_identity(broken: str, country: str) -> dict:
    obj = f"{country}_CommandCenter"
    side_m = re.search(r"(?m)^\s*Side\s*=\s*(\S+)", broken)
    disp_m = re.search(r"(?m)^\s*DisplayName\s*=\s*(\S+)", broken)
    cmd_m = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", broken)
    cost_m = re.search(r"(?m)^\s*BuildCost\s*=\s*(\S+)", broken)
    time_m = re.search(r"(?m)^\s*BuildTime\s*=\s*(\S+)", broken)
    if not side_m or not cmd_m or not cost_m or not time_m:
        raise SystemExit(f"{country}: missing Side/CommandSet/cost/time")
    # Keep DisplayName if present; else OBJECT:Country_CommandCenter
    display = disp_m.group(1) if disp_m else f"OBJECT:{obj}"
    # Prefer country CommandSet naming
    cmd = cmd_m.group(1)
    expect_cmd = f"{country}_CommandCenterCommandSet"
    if cmd != expect_cmd:
        # still keep whatever was there if it exists naming-wise
        pass
    return {
        "object": obj,
        "side": side_m.group(1),
        "display": display,
        "commandset": cmd,
        "cost": cost_m.group(1),
        "time": time_m.group(1),
    }


def clone_usa_to_country(usa_text: str, ident: dict) -> str:
    obj = ident["object"]
    side = ident["side"]
    display = ident["display"]
    cmd = ident["commandset"]
    cost = ident["cost"]
    btime = ident["time"]

    text = usa_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    i = 0
    while i < len(lines) and (lines[i].strip() == "" or lines[i].lstrip().startswith(";")):
        i += 1
    text = "\n".join(lines[i:])
    if not text.startswith("Object AmericaCommandCenter"):
        raise SystemExit("unexpected USA CommandCenter start")

    text = text.replace("Object AmericaCommandCenter", f"Object {obj}", 1)
    text = re.sub(
        r"(?m)^(  Side\s*=\s*)America\s*$",
        lambda m: m.group(1) + side,
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(  DisplayName\s*=\s*)OBJECT:\S+\s*$",
        lambda m: m.group(1) + display,
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(  CommandSet\s*=\s*)AmericaCommandCenterCommandSet\s*$",
        lambda m: m.group(1) + cmd,
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(  BuildCost\s*=\s*)\S+",
        lambda m: m.group(1) + cost,
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(  BuildTime\s*=\s*)\S+",
        lambda m: m.group(1) + btime,
        text,
        count=1,
    )

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
        f"; Donor: AmericaCommandCenter (Egypt/India CommandCenter method)\n"
        f"; Keep: Object/Side={side}/{cmd}/DisplayName/cost-time\n"
        f"; Art: US_Command / us_commandcenter; no Irq/Adnan crash modules\n"
        f"; Full validation + embed-in-BIG extract verify\n"
        f"\n"
    )
    text = header + text
    text = "".join(c if ord(c) < 128 else "?" for c in text)

    if f"Object {obj}" not in text:
        raise SystemExit(f"{obj}: object missing")
    if not re.search(rf"(?m)^  Side\s*=\s*{re.escape(side)}\s*$", text):
        raise SystemExit(f"{obj}: side missing")
    if cmd not in text:
        raise SystemExit(f"{obj}: commandset missing")
    if CRASH_TOKENS.search(text):
        raise SystemExit(f"{obj}: crash tokens remain")
    if "US_Command" not in text or "us_commandcenter" not in text:
        raise SystemExit(f"{obj}: USA art missing")
    if "Object AmericaCommandCenter" in text:
        raise SystemExit(f"{obj}: donor name remain")
    return text.replace("\n", "\r\n")


def main() -> int:
    if not SRC.is_file():
        raise SystemExit(f"missing source BIG {SRC}")
    entries = parse_big(SRC)
    by = {knorm(n): (n, b) for n, b in entries}
    art_entries = parse_big(ART) if ART.is_file() else []
    if knorm(USA_PATH) not in by:
        raise SystemExit("USA CommandCenter missing")

    # Dynamic Egypt CC preserve hash
    eg_path = r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_CommandCenter.ini"
    PRESERVE[eg_path] = sha256_bytes(by[knorm(eg_path)][1])

    usa_text = by[knorm(USA_PATH)][1].decode("utf-8", "replace")
    ok_d, issues_d = full_block_check(usa_text)
    if not ok_d:
        print("DONOR BLOCK FAIL", issues_d)
        return 1
    if "US_Command" not in usa_text:
        raise SystemExit("USA CC art missing")
    print("PASS donor AmericaCommandCenter")

    repaired: dict[str, bytes] = {}
    idents: dict[str, dict] = {}

    for spec in TARGETS:
        country = spec["country"]
        path = spec["path"]
        if knorm(path) not in by:
            raise SystemExit(f"missing {path}")
        broken = by[knorm(path)][1].decode("utf-8", "replace")
        ident = extract_identity(broken, country)
        if ident["side"] != spec["side"]:
            raise SystemExit(f"{country}: Side mismatch {ident['side']} vs {spec['side']}")
        idents[country] = ident
        issues = []
        if any(ord(c) > 127 for c in broken):
            issues.append("non-ASCII")
        if CRASH_TOKENS.search(broken):
            issues.append("Irq/Iraq tokens")
        if len(re.findall(r"(?m)^\s*Shadow\s*=", broken)) != 1:
            issues.append("Shadow count")
        print(f"OLD {country}: {issues or ['flagged-clean']} cost={ident['cost']}/{ident['time']} CS={ident['commandset']}")

        repl = clone_usa_to_country(usa_text, ident)
        repaired[country] = repl.encode("ascii")

    # pre-write validate with temp entries
    tmp = list(entries)
    tmp_by = {knorm(n): i for i, (n, _) in enumerate(tmp)}
    for spec in TARGETS:
        idx = tmp_by[knorm(spec["path"])]
        tmp[idx] = (tmp[idx][0], repaired[spec["country"]])

    for spec in TARGETS:
        country = spec["country"]
        ident = idents[country]
        fails = validate_cc(
            repaired[country].decode("ascii"),
            expect_object=ident["object"],
            expect_side=ident["side"],
            expect_cmd=ident["commandset"],
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

    path_to_country = {knorm(s["path"]): s["country"] for s in TARGETS}
    new_entries: list[tuple[str, bytes]] = []
    for name, blob in entries:
        k = knorm(name)
        if k in path_to_country:
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
        ident = idents[country]
        if knorm(path) not in rby:
            raise SystemExit(f"EXTRACT FAIL missing {path}")
        ename, ebytes = rby[knorm(path)]
        if ebytes != repaired[country]:
            raise SystemExit(f"EXTRACT FAIL bytes mismatch {country}")
        fails = validate_cc(
            ebytes.decode("ascii"),
            expect_object=ident["object"],
            expect_side=ident["side"],
            expect_cmd=ident["commandset"],
            entries=rebuilt,
            art_entries=art_entries,
            label=f"EXTRACTED_{country}",
        )
        if fails:
            out_big.unlink(missing_ok=True)
            print(f"EXTRACTED FAIL {country} - BIG deleted")
            for f in fails:
                print(" ", f)
            return 1

        rel = Path(*Path(ename.replace("\\", "/")).parts)
        ep = extract_root / rel
        ep.parent.mkdir(parents=True, exist_ok=True)
        ep.write_bytes(ebytes)
        tree = ROOT / "Data" / Path(spec["tree"])
        tree.parent.mkdir(parents=True, exist_ok=True)
        tree.write_bytes(ebytes)
        (OUT / f"{country}_CommandCenter.ini").write_bytes(ebytes)
        shas[country] = sha256_bytes(ebytes)
        print(f"PASS extract {country} sha={shas[country]}")

    for path, expect in PRESERVE.items():
        if knorm(path) not in rby:
            raise SystemExit(f"preserve path missing {path}")
        got = sha256_bytes(rby[knorm(path)][1])
        if got != expect:
            raise SystemExit(f"preserve lost {path}: {got}")

    old_by = {knorm(n): b for n, b in entries}
    changed = [n for n, b in rebuilt if old_by[knorm(n)] != b]
    expected = {knorm(s["path"]) for s in TARGETS}
    if {knorm(n) for n in changed} != expected:
        raise SystemExit(f"unexpected changed: {changed}")

    if len(shas) != 9:
        raise SystemExit(f"expected 9 repaired CCs, got {len(shas)}")

    big_sha = sha256_file(out_big)
    big_size = out_big.stat().st_size

    report_lines = [
        "SPECTER COMMANDCENTER BATCH FIX (9 COUNTRIES) - VERIFY REPORT",
        "=============================================================",
        "VERDICT: PASS",
        "Patched INSIDE: _SPEC_DATA_ONE.big",
        "Donor: AmericaCommandCenter (Egypt/India CC method)",
        "Countries: Libya, Pakistan, SaudiArabia, SouthAfrica, Syria, Turkey, Israel, Ukraine, Vietnam",
        "Removed: Irq_Command/irq_comndcntr/Iraq_Adnan1/SUPERWEAPON_Iraqi*, non-ASCII, dup Shadow",
        "Kept: Object/Side/DisplayName/CommandSet/cost-time; art US_Command/us_commandcenter",
        "",
        f"BIG SHA256: {big_sha}",
        f"BIG SIZE:   {big_size}",
        "",
        "Per-country SHA256:",
    ]
    for spec in TARGETS:
        c = spec["country"]
        ident = idents[c]
        report_lines.append(
            f"  {c}_CommandCenter.ini {shas[c]} cost={ident['cost']} time={ident['time']} CS={ident['commandset']}"
        )
    report_lines += [
        "",
        "Validation: donor PASS, pre-write PASS x9, extract-from-BIG PASS x9",
        "Preserved: Egypt/India CC, France/Germany drones, Japan/UAE MQ9, India MHQ",
        "FINAL: PASS",
        "",
    ]
    report = "\n".join(report_lines)
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT TEST\n"
        "====================\n"
        + "\n".join(f"{c}: embedded={shas[c]} match=YES" for c in shas)
        + f"\nBIG_sha256={big_sha}\nBIG_size={big_size}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER COMMANDCENTER BATCH FIX (9)\n"
        "===================================\n\n"
        "Repaired INSIDE _SPEC_DATA_ONE.big:\n"
        "  Libya, Pakistan, SaudiArabia, SouthAfrica, Syria,\n"
        "  Turkey, Israel, Ukraine, Vietnam CommandCenter\n"
        "Donor: AmericaCommandCenter (Egypt/India method).\n"
        "Removed Irq/Iraq crash tokens + non-ASCII + dup Shadow.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )
    hash_lines = [f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}"]
    for spec in TARGETS:
        c = spec["country"]
        hash_lines.append(f"{c}_CommandCenter.ini SHA256={shas[c]}")
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
        shutil.copy2(OUT / f"{c}_CommandCenter.ini", final_dir / f"{c}_CommandCenter.ini")

    zpath = OUT / "_SPEC_DATA_ONE_COMMANDCENTER_BATCH_FIXED.zip"
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for spec in TARGETS:
            c = spec["country"]
            zf.write(OUT / f"{c}_CommandCenter.ini", f"{c}_CommandCenter.ini")
            ename = rby[knorm(spec["path"])][0]
            rel = Path(*Path(ename.replace("\\", "/")).parts)
            zf.write(extract_root / rel, f"EXTRACT_VERIFY/{c}_CommandCenter.ini")
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
