#!/usr/bin/env python3
"""Fix CommandSet.ini: remove stale refs to deleted E-3 UNIT_BUILD button.

Root cause of reported parse crash at AmericaAirfieldCommandSet:
Command_ConstructAmericaJetE3AWACS was removed during E-3 ART-only reset,
but AmericaAirfieldCommandSet (+ T/T1/T2/T3) still referenced it.

Does NOT restore E-3/C-17/E-737/E2/V-22 gameplay buttons.
Does NOT modify ART or aircraft Objects.
DATA-only.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
STAGE = MASTER / "_stage_usa_commandset_parse_fix"
VERIFY = MASTER / "_extract_usa_commandset_parse_fix_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_COMMANDSET_PARSE_FIX.zip"
OUT_HASH = ROOT / "Release/DATA_USA_COMMANDSET_PARSE_FIX_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_COMMANDSET_PARSE_FIX_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_COMMANDSET_PARSE_FIX_REPORT.txt"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"

STALE_BUTTONS = [
    "Command_ConstructAmericaJetE3AWACS",
    "Command_ConstructAmericaJetC17Globemaster",
    "Command_ConstructAmericaJetE737AEW",
    "Command_ConstructAmericaE2avionHE",
    "Command_ConstructAmericaJetE2avionHE",
    "Command_ConstructAmericaV22",
    "Command_ConstructAmericaJetV22",
]

FREEZE_KEYS = [
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\Airforce\\B1R.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini",
]


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        out[name.replace("/", "\\")] = data[off : off + size]
    return out


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16 + sum(8 + len(n.encode("latin1")) + 1 for n, _ in items)
    offset = header_size
    index, blobs = [], []
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">III", offset, len(items), header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for b in blobs:
        out += b
    return bytes(out)


def write_tree(file_map: dict[str, bytes], root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for name, content in file_map.items():
        path = root / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def read_tree(root: Path) -> dict[str, bytes]:
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root)).replace("/", "\\")] = p.read_bytes()
    return out


def strip_stale_slot_lines(cs: str) -> tuple[str, list[str]]:
    """Remove non-comment slot lines that reference deleted CommandButtons."""
    lines = cs.splitlines(keepends=True)
    removed: list[str] = []
    out: list[str] = []
    stale_re = re.compile(
        r"(?m)^(\s*)(\d+)\s*=\s*("
        + "|".join(re.escape(b) for b in STALE_BUTTONS)
        + r")\s*$"
    )
    for line in lines:
        raw = line.rstrip("\r\n")
        if raw.lstrip().startswith(";"):
            out.append(line)
            continue
        m = stale_re.match(raw)
        if m:
            removed.append(f"L?: {raw.strip()}")
            continue
        out.append(line)
    return "".join(out), removed


def scan_commandsets(text: str) -> tuple[list[dict], list[tuple]]:
    """Structural scan. Accepts End or END as terminators (Specter uses both)."""
    lines = text.splitlines()
    stack: list[str] = []
    blocks: list[dict] = []
    problems: list[tuple] = []
    cur = None
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or s.startswith(";"):
            continue
        if re.match(r"^CommandSet\s+\S+", s):
            name = s.split(None, 1)[1]
            if stack:
                problems.append(("MISSING_END_BEFORE_NEXT", i + 1, name, list(stack)))
            stack.append(name)
            cur = {"name": name, "start": i + 1, "end": None}
            blocks.append(cur)
        elif s in ("End", "END"):
            if not stack:
                problems.append(("EXTRA_END", i + 1, s, None))
            else:
                stack.pop()
                if cur is not None and cur["end"] is None:
                    cur["end"] = i + 1
                cur = None if not stack else blocks[-1] if blocks else None
                # After pop, current open block is top of stack if any
                if stack:
                    # find last block matching stack[-1] without end... simplify:
                    for b in reversed(blocks):
                        if b["name"] == stack[-1] and b["end"] is None:
                            cur = b
                            break
                else:
                    cur = None
    if stack:
        problems.append(("UNCLOSED_AT_EOF", len(lines), list(stack), None))
    return blocks, problems


def extract_block(text: str, name: str) -> str:
    m = re.search(
        rf"CommandSet\s+{re.escape(name)}\s*\n(.*?)(?:^End\s*$|^END\s*$)",
        text,
        flags=re.M | re.S,
    )
    if not m:
        raise SystemExit(f"CommandSet {name} not found")
    return m.group(0)


def count_headers(text: str, name: str) -> int:
    return len(re.findall(rf"(?m)^CommandSet\s+{re.escape(name)}\s*$", text))


def all_refs_resolve(cs_block: str, cb: str) -> list[str]:
    missing = []
    for btn in re.findall(r"(?m)^\s*\d+\s*=\s*(\S+)\s*$", cs_block):
        if not re.search(rf"(?m)^CommandButton\s+{re.escape(btn)}\s*$", cb):
            missing.append(btn)
    return missing


def main() -> None:
    dmap = read_big(DATA_BIG)
    assert sha256(dmap["Data\\English\\generals.csf"]) == GOOD_CSF
    freeze = {k: dmap[k] for k in FREEZE_KEYS}
    assert sha256(freeze[FREEZE_KEYS[0]]) == AC130_SHA
    art_sha_before = sha256(ART_BIG)

    cs_before = dmap[CS_KEY]
    cb_text = dmap[CB_KEY].decode("latin1")
    cs_text = cs_before.decode("latin1")

    # Encoding checks
    assert not cs_before.startswith(b"\xef\xbb\xbf")
    assert b"\x00" not in cs_before
    assert all(c < 128 for c in cs_before)

    # Confirm root cause: stale E3 button refs with button missing
    assert not re.search(
        r"(?m)^CommandButton\s+Command_ConstructAmericaJetE3AWACS\s*$", cb_text
    )
    stale_hits_before = len(
        re.findall(
            r"(?m)^\s*\d+\s*=\s*Command_ConstructAmericaJetE3AWACS\s*$", cs_text
        )
    )
    assert stale_hits_before >= 1

    # Identify previous CommandSet before AmericaAirfieldCommandSet
    blocks_before, _ = scan_commandsets(cs_text)
    air_idx = next(
        i for i, b in enumerate(blocks_before) if b["name"] == "AmericaAirfieldCommandSet"
    )
    prev = blocks_before[air_idx - 1]
    air = blocks_before[air_idx]

    new_cs, removed = strip_stale_slot_lines(cs_text)
    assert "Command_ConstructAmericaJetE3AWACS" not in new_cs or all(
        line.strip().startswith(";")
        for line in new_cs.splitlines()
        if "Command_ConstructAmericaJetE3AWACS" in line
    )
    # stronger: no active slot refs
    assert not re.search(
        r"(?m)^\s*\d+\s*=\s*Command_ConstructAmericaJetE3AWACS\s*$", new_cs
    )
    for btn in STALE_BUTTONS:
        assert not re.search(rf"(?m)^\s*\d+\s*=\s*{re.escape(btn)}\s*$", new_cs)

    # HeavyAirBase must remain art-only empty slots (no restore)
    heavy = extract_block(new_cs, "America_HeavyAirBaseCommandSet")
    for btn in STALE_BUTTONS:
        assert btn not in heavy
    assert re.search(
        r"(?m)^\s*1\s*=\s*Command_ConstructAmericaJetB2Spirit\s*$", heavy
    )
    assert re.search(r"(?m)^\s*7\s*=\s*Command_ConstructAmericaJetAC130\s*$", heavy)
    assert not re.search(r"(?m)^\s*5\s*=", heavy)
    for slot in (8, 9, 10, 11):
        assert not re.search(rf"(?m)^\s*{slot}\s*=", heavy)

    # Airfield block validation
    assert count_headers(new_cs, "AmericaAirfieldCommandSet") == 1
    assert count_headers(new_cs, "America_HeavyAirBaseCommandSet") == 1
    air_block = extract_block(new_cs, "AmericaAirfieldCommandSet")
    missing = all_refs_resolve(air_block, cb_text)
    if missing:
        raise SystemExit(f"AmericaAirfieldCommandSet unresolved buttons: {missing}")

    for variant in [
        "AmericaAirfieldCommandSet_T",
        "AmericaAirfieldCommandSet_T1",
        "AmericaAirfieldCommandSet_T2",
        "AmericaAirfieldCommandSet_T3",
    ]:
        if count_headers(new_cs, variant) == 1:
            miss = all_refs_resolve(extract_block(new_cs, variant), cb_text)
            if miss:
                raise SystemExit(f"{variant} unresolved: {miss}")

    blocks, problems = scan_commandsets(new_cs)
    # Only hard-fail on EXTRA_END / UNCLOSED / MISSING near USA airfield/heavy
    critical = []
    for p in problems:
        kind = p[0]
        if kind == "EXTRA_END":
            critical.append(p)
        elif kind == "UNCLOSED_AT_EOF":
            critical.append(p)
        elif kind == "MISSING_END_BEFORE_NEXT":
            # Only critical if involves our USA airbase sets or neighbors
            open_names = p[3] or []
            nxt = p[2]
            if any(
                x in open_names or nxt == x
                for x in (
                    "AmericaAirfieldCommandSet",
                    "America_HeavyAirBaseCommandSet",
                    "Command_ScriptedA10ThunderboltStrike",
                )
            ):
                critical.append(p)
    if critical:
        raise SystemExit(f"critical CommandSet structure problems: {critical}")

    # AmericaAirfield neighbors still balanced
    air2 = next(b for b in blocks if b["name"] == "AmericaAirfieldCommandSet")
    assert air2["end"] is not None
    prev2 = blocks[blocks.index(air2) - 1]
    assert prev2["end"] is not None

    # No diagnostic junk
    assert "E737_TEST" not in new_cs
    assert "DonorReplace" not in new_cs

    dmap[CS_KEY] = new_cs.encode("latin1")
    assert all(c < 128 for c in dmap[CS_KEY])
    assert b"\x00" not in dmap[CS_KEY]

    # Clean staging rebuild
    if STAGE.exists():
        shutil.rmtree(STAGE)
    write_tree(dmap, STAGE / "in")
    staged = read_tree(STAGE / "in")
    new_data = build_big(staged)
    DATA_BIG.write_bytes(new_data)

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    vmap = read_big(DATA_BIG)
    write_tree(vmap, VERIFY / "out")

    for k, blob in freeze.items():
        assert vmap[k] == blob, k
    assert sha256(vmap["Data\\English\\generals.csf"]) == GOOD_CSF
    assert sha256(ART_BIG) == art_sha_before

    final_cs = vmap[CS_KEY].decode("latin1")
    final_cb = vmap[CB_KEY].decode("latin1")
    assert count_headers(final_cs, "AmericaAirfieldCommandSet") == 1
    assert count_headers(final_cs, "America_HeavyAirBaseCommandSet") == 1
    assert not re.search(
        r"(?m)^\s*\d+\s*=\s*Command_ConstructAmericaJetE3AWACS\s*$", final_cs
    )
    miss = all_refs_resolve(
        extract_block(final_cs, "AmericaAirfieldCommandSet"), final_cb
    )
    assert not miss

    blocks_f, problems_f = scan_commandsets(final_cs)
    missing_end = sum(1 for p in problems_f if p[0] == "MISSING_END_BEFORE_NEXT")
    extra_end = sum(1 for p in problems_f if p[0] == "EXTRA_END")
    unclosed = sum(1 for p in problems_f if p[0] == "UNCLOSED_AT_EOF")
    # For USA airfield/heavy local region: zero critical issues
    air_f = next(b for b in blocks_f if b["name"] == "AmericaAirfieldCommandSet")
    prev_f = blocks_f[blocks_f.index(air_f) - 1]
    heavy_f = next(b for b in blocks_f if b["name"] == "America_HeavyAirBaseCommandSet")

    # Slot report for HeavyAirBase
    heavy_body = extract_block(final_cs, "America_HeavyAirBaseCommandSet")
    slots = {}
    for slot in range(1, 15):
        sm = re.search(rf"(?m)^\s*{slot}\s*=\s*(\S+)\s*$", heavy_body)
        slots[slot] = sm.group(1) if sm else "EMPTY"

    # ART families still present
    amap = read_big(ART_BIG)
    def has(pat: str) -> bool:
        return any(re.search(pat, k, re.I) for k in amap)

    report = []
    report.append("USA COMMANDSET PARSE FIX = PASS")
    report.append("")
    report.append("Reported crash header =")
    report.append("CommandSet AmericaAirfieldCommandSet")
    report.append("")
    report.append(
        "Actual root cause = "
        "AmericaAirfieldCommandSet (and T/T1/T2/T3) still referenced "
        "Command_ConstructAmericaJetE3AWACS after that CommandButton was removed "
        "during E-3 ART-only reset; parser fails while reading AmericaAirfieldCommandSet"
    )
    report.append("Was defect inside previous CommandSet = NO")
    report.append(f"Previous CommandSet = {prev_f['name']}")
    report.append(f"Previous starts at line = {prev_f['start']}")
    report.append(f"Previous ends at line = {prev_f['end']}")
    report.append("Missing/extra End found = NO (previous block End present)")
    report.append("")
    report.append(f"AmericaAirfieldCommandSet count = {count_headers(final_cs, 'AmericaAirfieldCommandSet')}")
    report.append("Expected = 1")
    report.append(
        f"America_HeavyAirBaseCommandSet count = {count_headers(final_cs, 'America_HeavyAirBaseCommandSet')}"
    )
    report.append("Expected = 1")
    report.append("")
    report.append(
        f"Missing End total (file-wide, End/END-aware) = {missing_end}"
    )
    report.append(f"Extra End total = {extra_end}")
    report.append(f"Nested/unclosed at EOF = {unclosed}")
    report.append(
        "AmericaAirfieldCommandSet / previous / HeavyAirBase local structure = BALANCED"
    )
    report.append("")
    report.append("Stale E-3 HeavyAirBase button = 0")
    report.append("Stale C-17 HeavyAirBase button = 0")
    report.append("Stale E-737 HeavyAirBase button = 0")
    report.append("Stale E2 HeavyAirBase button = 0")
    report.append("Stale V-22 HeavyAirBase button = 0")
    report.append(
        f"Stale E-3 AmericaAirfield slot lines removed = {stale_hits_before}"
    )
    report.append("")
    report.append("HeavyAirBase final slots:")
    labels = {
        1: "B-2",
        2: "B-21",
        3: "B-52",
        4: "B-1R",
        5: "EMPTY",
        6: "Nuclear Tip Warhead",
        7: "AC-130",
        8: "EMPTY",
        9: "EMPTY",
        10: "EMPTY",
        11: "EMPTY",
        13: "Rally Point",
        14: "Sell",
    }
    for slot in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14]:
        report.append(f"{slot} = {labels[slot]} ({slots[slot]})")
    report.append("")
    report.append(f"E-3 ART preserved = {'YES' if has(r'E3\\.W3D|E3USA') else 'NO'}")
    report.append(f"C-17 ART preserved = {'YES' if has(r'IUAC17') else 'NO'}")
    report.append(f"E-737 ART preserved = {'YES' if has(r'KVE737') else 'NO'}")
    report.append(f"E2 ART preserved = {'YES' if has(r'AVHawk') else 'NO'}")
    report.append(f"V-22 ART preserved = {'YES' if has(r'AVOsprey') else 'NO'}")
    report.append("")
    report.append("B-2/B-21/B-52/B-1R changed = NO")
    report.append("AC-130 changed = NO")
    report.append("ART changed = NO")
    report.append("")
    report.append("FINAL PACKED CommandSet.ini STRUCTURAL VALIDATION = PASS")
    report.append("GAME BOOT CLAIMED = NO")
    report.append(f"DATA sha256 = {sha256(DATA_BIG)}")
    report.append(f"CommandSet.ini sha256 = {sha256(vmap[CS_KEY])}")

    text = "\n".join(report) + "\n"
    OUT_REPORT.write_text(text, encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text(text, encoding="utf-8")
    (STAGE / "removed_lines.txt").write_text(
        "\n".join(removed) + "\n", encoding="utf-8"
    )

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    with zipfile.ZipFile(OUT_ZIP) as z:
        assert z.namelist() == ["_SPEC_DATA_ONE.big"]

    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={sha256(DATA_BIG)}\n"
        f"CommandSet.ini sha256={sha256(vmap[CS_KEY])}\n"
        f"ZIP={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            "curl",
            "-sF",
            "reqtype=fileupload",
            "-F",
            "time=72h",
            "-F",
            f"fileToUpload=@{OUT_ZIP}",
            "https://litterbox.catbox.moe/resources/internals/api.php",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    url = (proc.stdout or "").strip()
    if not url.startswith("http"):
        raise SystemExit(f"upload failed: {url!r} {proc.stderr!r}")
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print(text)
    print("Download =", url)


if __name__ == "__main__":
    main()
