#!/usr/bin/env python3
"""Fix Japan_MQ9 + UAE_MQ9 inside _SPEC_DATA_ONE.big (USA MQ9 donor).

UAE has no separate CombatDrone.ini; UAE_MQ9 is the combat MQ9 role.
Same pattern as France/Germany/batch CombatDrone fixes.

Keep country identity (Object/Side/cost/time/primary weapon/AAB).
Remove non-ASCII, duplicate Shadow, SCIENCE_*StealthJet.
Preserve MQ9 art (Nat_mq9 / US_MQ9*).
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
SRC = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_COMBATDRONE_BATCH_FIXED" / "_SPEC_DATA_ONE.big"
ART = ROOT / "Release" / "SPECTER_BIG_MERGE" / "_SPEC_ART_ONE.big"
OUT = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_JAPAN_UAE_MQ9_FIXED"

USA_PATH = r"Data\INI\Object\Specter\United States Of America\Drones\Mq9.ini"

TARGETS = [
    {
        "label": "Japan_MQ9",
        "object": "Japan_MQ9",
        "side": "Japan",
        "path": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\Japan_MQ9.ini",
        "tree": "INI/Object/Specter/Japan Self-Defense Forces/Airforce/Japan_MQ9.ini",
        "weapon": "4x_AGM114N_Mq9",  # valid country loadout already on unit
        "aab": "Japan_AdvancedAirBase",
        "display": "OBJECT:Japan_MQ9",
        "bad_science": "SCIENCE_JapanStealthJet",
    },
    {
        "label": "UAE_MQ9",
        "object": "UAE_MQ9",
        "side": "UAE",  # faction Side token (UnitedArabEmirates unused in DATA)
        "path": r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAE_MQ9.ini",
        "tree": "INI/Object/Specter/United Arab Emirates/Airforce/UAE_MQ9.ini",
        "weapon": "UAE_Weapon_AAM_Short",
        "aab": "UAE_AdvancedAirBase",
        "display": "OBJECT:UAE_MQ9",
        "bad_science": "SCIENCE_UAEStealthJet",
    },
]

PRESERVE = {
    r"Data\INI\Object\Specter\French Armed Forces\Drones\France_CombatDrone.ini": (
        "7512cca46c234c6951a54d5a982184209d203668738c4e1336fdaab1e1ba8df2"
    ),
    r"Data\INI\Object\Specter\German Armed Forces\Drones\Germany_CombatDrone.ini": (
        "663b32b1de6111bd1496463bc042f642d204782a525f103c63440d92d380e8b2"
    ),
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Drones\Japan_CombatDrone.ini": (
        "33b349eb4b48ee01f105dc201671e1e1ca43fdb0325eeaee68cf2119d10aa53f"
    ),
    r"Data\INI\Object\Specter\Indian Armed Forces\Drones\India_CombatDrone.ini": (
        "943aa7ef3ac7ee5fdafcdf95c437b2662baea0c35a351272400c12cae436e73c"
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

STEALTH_SCI = re.compile(r"(?i)\bSCIENCE_\w*StealthJet\b|\bSCIENCE_UAE\b")


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
    return cats


def code_only(text: str) -> str:
    return "\n".join(line.split(";", 1)[0] for line in text.splitlines())


def validate_mq9(
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
        fails.append(f"{label}: AAB missing")
    if "Nat_mq9" not in text or "US_MQ9" not in text:
        fails.append(f"{label}: MQ9 art missing")
    if STEALTH_SCI.search(code_only(text)):
        fails.append(f"{label}: stealth science in code {STEALTH_SCI.findall(code_only(text))}")
    if "DRONE" not in text:
        fails.append(f"{label}: DRONE KindOf missing (combat drone role)")

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


def extract_cost_time(broken: str, label: str) -> tuple[str, str]:
    cost_m = re.search(r"(?m)^\s*BuildCost\s*=\s*(\S+)", broken)
    time_m = re.search(r"(?m)^\s*BuildTime\s*=\s*(\S+)", broken)
    if not cost_m or not time_m:
        raise SystemExit(f"{label}: missing BuildCost/Time")
    return cost_m.group(1), time_m.group(1)


def clone_usa_mq9(
    usa_text: str,
    *,
    object_name: str,
    side: str,
    display: str,
    weapon: str,
    aab: str,
    build_cost: str,
    build_time: str,
) -> str:
    text = usa_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    i = 0
    while i < len(lines) and (lines[i].strip() == "" or lines[i].lstrip().startswith(";")):
        i += 1
    text = "\n".join(lines[i:])
    if not text.startswith("Object AmericaDronesMq9"):
        raise SystemExit("unexpected USA MQ9 start")

    text = text.replace("Object AmericaDronesMq9", f"Object {object_name}", 1)
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
        lambda m: m.group(1) + weapon,
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(  BuildCost\s*=\s*)\S+",
        lambda m: m.group(1) + build_cost,
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(  BuildTime\s*=\s*)\S+",
        lambda m: m.group(1) + build_time,
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
        f"; SPECTER FIX - {object_name}\n"
        f"; Donor: USA AmericaDronesMq9 (France/Germany/USA MQ9 CombatDrone pattern)\n"
        f"; Keep: Object {object_name} / Side={side} / {aab} / {weapon}\n"
        f"; Cost/time preserved ({build_cost}/{build_time}); MQ9 art preserved\n"
        f"; Removed: non-ASCII, stealth-jet science, duplicate Shadow\n"
        f"\n"
    )
    text = header + text
    text = "".join(c if ord(c) < 128 else "?" for c in text)

    if f"Object {object_name}" not in text:
        raise SystemExit(f"{object_name}: object missing")
    if not re.search(rf"(?m)^  Side\s*=\s*{re.escape(side)}\s*$", text):
        raise SystemExit(f"{object_name}: side missing")
    if weapon not in text or "2x_GBU12II_Mq9" not in text:
        raise SystemExit(f"{object_name}: weapons missing")
    if aab not in text:
        raise SystemExit(f"{object_name}: AAB missing")
    if "Nat_mq9" not in text or "US_MQ9" not in text:
        raise SystemExit(f"{object_name}: MQ9 art missing")
    if STEALTH_SCI.search(code_only(text)):
        raise SystemExit(f"{object_name}: stealth science remain")
    if "Object AmericaDronesMq9" in text:
        raise SystemExit(f"{object_name}: donor name remain")
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
    if not re.search(r"(?m)^Object\s+AmericaDronesMq9\b", usa_text):
        raise SystemExit("USA MQ9 Object missing")
    ok_d, issues_d = full_block_check(usa_text)
    if not ok_d:
        print("DONOR BLOCK FAIL", issues_d)
        return 1
    print("PASS donor AmericaDronesMq9")

    repaired: dict[str, bytes] = {}
    identities: dict[str, tuple[str, str]] = {}

    for spec in TARGETS:
        path = spec["path"]
        if knorm(path) not in by:
            raise SystemExit(f"missing {path}")
        broken = by[knorm(path)][1].decode("utf-8", "replace")
        cost, btime = extract_cost_time(broken, spec["label"])
        identities[spec["label"]] = (cost, btime)
        issues = []
        if any(ord(c) > 127 for c in broken):
            issues.append("non-ASCII")
        if len(re.findall(r"(?m)^\s*Shadow\s*=", broken)) != 1:
            issues.append("dup Shadow")
        if spec["bad_science"] in code_only(broken):
            issues.append(spec["bad_science"])
        print(f"OLD {spec['label']}: {issues}")

        repl = clone_usa_mq9(
            usa_text,
            object_name=spec["object"],
            side=spec["side"],
            display=spec["display"],
            weapon=spec["weapon"],
            aab=spec["aab"],
            build_cost=cost,
            build_time=btime,
        )
        repaired[spec["label"]] = repl.encode("ascii")

    # pre-write validate
    tmp = list(entries)
    tmp_by = {knorm(n): i for i, (n, _) in enumerate(tmp)}
    for spec in TARGETS:
        idx = tmp_by[knorm(spec["path"])]
        tmp[idx] = (tmp[idx][0], repaired[spec["label"]])

    for spec in TARGETS:
        fails = validate_mq9(
            repaired[spec["label"]].decode("ascii"),
            expect_object=spec["object"],
            expect_side=spec["side"],
            expect_weapon=spec["weapon"],
            expect_aab=spec["aab"],
            entries=tmp,
            art_entries=art_entries,
            label=spec["label"],
        )
        if fails:
            print(f"PRE-WRITE FAIL {spec['label']}")
            for f in fails:
                print(" ", f)
            return 1
        print(f"PASS pre-write {spec['label']}")

    path_to_label = {knorm(s["path"]): s["label"] for s in TARGETS}
    new_entries: list[tuple[str, bytes]] = []
    for name, blob in entries:
        k = knorm(name)
        if k in path_to_label:
            new_entries.append((name, repaired[path_to_label[k]]))
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
        label = spec["label"]
        path = spec["path"]
        if knorm(path) not in rby:
            raise SystemExit(f"EXTRACT FAIL missing {path}")
        ename, ebytes = rby[knorm(path)]
        if ebytes != repaired[label]:
            raise SystemExit(f"EXTRACT FAIL bytes mismatch {label}")
        fails = validate_mq9(
            ebytes.decode("ascii"),
            expect_object=spec["object"],
            expect_side=spec["side"],
            expect_weapon=spec["weapon"],
            expect_aab=spec["aab"],
            entries=rebuilt,
            art_entries=art_entries,
            label=f"EXTRACTED_{label}",
        )
        if fails:
            out_big.unlink(missing_ok=True)
            print(f"EXTRACTED FAIL {label} - BIG deleted")
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
        (OUT / f"{label}.ini").write_bytes(ebytes)
        shas[label] = sha256_bytes(ebytes)
        print(f"PASS extract {label} sha={shas[label]}")

    for path, expect in PRESERVE.items():
        got = sha256_bytes(rby[knorm(path)][1])
        if got != expect:
            raise SystemExit(f"preserve lost {path}: {got}")

    old_by = {knorm(n): b for n, b in entries}
    changed = [n for n, b in rebuilt if old_by[knorm(n)] != b]
    expected = {knorm(s["path"]) for s in TARGETS}
    if {knorm(n) for n in changed} != expected:
        raise SystemExit(f"unexpected changed: {changed}")

    # Confirm no UAE_CombatDrone path exists (documented)
    if any("uae_combatdrone" in knorm(n) for n, _ in rebuilt):
        print("NOTE: UAE_CombatDrone.ini also present")
    else:
        print("NOTE: no UAE_CombatDrone.ini in BIG; UAE combat MQ9 role = UAE_MQ9.ini")

    big_sha = sha256_file(out_big)
    big_size = out_big.stat().st_size

    report = (
        "SPECTER JAPAN_MQ9 + UAE_MQ9 FIX - VERIFY REPORT\n"
        "==============================================\n"
        "VERDICT: PASS\n"
        "Patched INSIDE: _SPEC_DATA_ONE.big\n"
        "Donor: USA AmericaDronesMq9 (France/Germany CombatDrone pattern)\n"
        "Targets: Japan_MQ9.ini, UAE_MQ9.ini (UAE combat drone / MQ9 role)\n"
        "Side: Japan / UAE (faction token; UnitedArabEmirates unused in DATA)\n"
        "Removed: non-ASCII, duplicate Shadow, SCIENCE_*StealthJet\n"
        "Preserved MQ9 art: Nat_mq9 / US_MQ9 / US_MQ9D / US_MQ9R\n"
        f"\nBIG SHA256: {big_sha}\n"
        f"BIG SIZE:   {big_size}\n"
        f"Japan_MQ9 SHA256: {shas['Japan_MQ9']} cost/time={identities['Japan_MQ9']}\n"
        f"UAE_MQ9 SHA256:   {shas['UAE_MQ9']} cost/time={identities['UAE_MQ9']}\n"
        "\nValidation: pre-write PASS, extract-from-BIG PASS, byte match PASS\n"
        "Preserved: France/Germany/Japan CombatDrone batch + India EliteStrike/CC/MHQ\n"
        "FINAL: PASS\n"
    )
    (OUT / "VERIFY_REPORT.txt").write_text(report, encoding="ascii")
    (OUT / "EMBED_PROOF.txt").write_text(
        "EMBED + EXTRACT TEST\n"
        "====================\n"
        f"Japan_MQ9: embedded={shas['Japan_MQ9']} match=YES\n"
        f"UAE_MQ9: embedded={shas['UAE_MQ9']} match=YES\n"
        f"BIG_sha256={big_sha}\n"
        f"BIG_size={big_size}\n",
        encoding="ascii",
    )
    (OUT / "README_INSTALL.txt").write_text(
        "SPECTER JAPAN_MQ9 + UAE_MQ9 FIX\n"
        "===============================\n\n"
        "Patched INSIDE _SPEC_DATA_ONE.big:\n"
        "  Japan_MQ9.ini\n"
        "  UAE_MQ9.ini  (UAE combat MQ9 / CombatDrone role; no UAE_CombatDrone.ini exists)\n"
        "USA MQ9 donor pattern; MQ9 art preserved; stealth-jet science removed.\n\n"
        "Install: replace Data\\_SPEC_DATA_ONE.big; keep _SPEC_ART_ONE.big.\n",
        encoding="ascii",
    )
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big SHA256={big_sha} SIZE={big_size}\n"
        f"Japan_MQ9.ini SHA256={shas['Japan_MQ9']}\n"
        f"UAE_MQ9.ini SHA256={shas['UAE_MQ9']}\n",
        encoding="ascii",
    )

    for sync in [
        ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL",
        ROOT / "Release" / "SPECTER_FINAL_EGYPT_BRITAIN_FIXED",
    ]:
        if sync.is_dir():
            shutil.copy2(out_big, sync / "_SPEC_DATA_ONE.big")

    final_dir = ROOT / "Release" / "SPECTER_SPEC_DATA_ONE_FINAL"
    for name in ("HASHES.txt", "VERIFY_REPORT.txt", "README_INSTALL.txt", "EMBED_PROOF.txt"):
        shutil.copy2(OUT / name, final_dir / name)
    for label in shas:
        shutil.copy2(OUT / f"{label}.ini", final_dir / f"{label}.ini")

    zpath = OUT / "_SPEC_DATA_ONE_JAPAN_UAE_MQ9_FIXED.zip"
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_big, "_SPEC_DATA_ONE.big")
        for spec in TARGETS:
            label = spec["label"]
            zf.write(OUT / f"{label}.ini", f"{label}.ini")
            ename = rby[knorm(spec["path"])][0]
            rel = Path(*Path(ename.replace("\\", "/")).parts)
            zf.write(extract_root / rel, f"EXTRACT_VERIFY/{label}.ini")
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
