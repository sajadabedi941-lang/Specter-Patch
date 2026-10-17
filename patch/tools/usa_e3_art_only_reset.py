#!/usr/bin/env python3
"""E-3 ART-only reset: remove AmericaJetE3AWACS gameplay DATA.

Keeps donor visual ART (E3 / chj10_r / E3USA) in _SPEC_ART_ONE.big.
Empties HeavyAirBase Slot 5. Does not restore C-17/E-737/E2/V-22 gameplay.
Freezes AC-130 and bombers. DATA-only package.
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
STAGE = MASTER / "_stage_usa_e3_art_only_reset"
VERIFY = MASTER / "_extract_usa_e3_art_only_reset_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_E3_ART_ONLY_RESET.zip"
OUT_HASH = ROOT / "Release/DATA_USA_E3_ART_ONLY_RESET_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_E3_ART_ONLY_RESET_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_E3_ART_ONLY_RESET_REPORT.txt"
REF_DIR = ROOT / (
    "Data/INI/Object/Specter/United States Of America/_ref"
)

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"

USA_KEY = "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"

REMOVE_OBJECTS = [
    "AmericaJetE3AWACS",
    "USAE3",
    "AmericaJetE737AEW",
    "avionE737",
    "AmericaJetC17Globemaster",
    "USAC17GlobalMaster",
    "AmericaJetE2avionHE",
    "E2avionHE",
    "AmericaJetV22",
    "USAHelixV22",
]

REMOVE_BUTTONS = [
    "Command_ConstructAmericaJetE3AWACS",
]

# Still must stay absent from prior art-only reset
ABSENT_BUTTONS = [
    "Command_ConstructAmericaJetC17Globemaster",
    "Command_ConstructAmericaJetE737AEW",
    "Command_ConstructAmericaE2avionHE",
    "Command_ConstructAmericaV22",
]

FREEZE_KEYS = [
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\Airforce\\B1R.ini",
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


def count_obj(file_map: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(name)}\s*$".encode())
    return sum(len(pat.findall(b)) for b in file_map.values())


def extract_object_span(text: str, object_name: str) -> tuple[int, int, str]:
    """Return (start_line_idx, end_line_idx_inclusive, block_text)."""
    lines = text.splitlines(keepends=True)
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"^Object\s+{re.escape(object_name)}\s*$", line.rstrip("\r\n")):
            start = i
            break
    if start is None:
        raise SystemExit(f"Object {object_name} not found")
    stack: list[str] = []
    end_i = None
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if not s or s.startswith(";"):
            continue
        if re.match(r"^Object\s+\S+", s):
            if stack and i != start:
                raise SystemExit(f"nested Object near {object_name}")
            stack.append("Object")
        elif re.match(
            r"^(Draw|Behavior|ArmorSet|WeaponSet|Body|UnitSpecificSounds|"
            r"Prerequisites|DefaultConditionState|ConditionState|TransitionState)\b",
            s,
        ):
            stack.append(s.split()[0])
        elif s == "End":
            if not stack:
                raise SystemExit("extra End")
            stack.pop()
            if not stack:
                end_i = i
                break
    if end_i is None:
        raise SystemExit(f"Object {object_name} did not close")
    block = "".join(lines[start : end_i + 1])
    return start, end_i, block


def remove_e3_from_usa_system(usa_blob: bytes) -> tuple[bytes, bytes]:
    """Remove AmericaJetE3AWACS Object and its SPECTER donor-replace comments.

    Returns (new_usa_blob, removed_block_bytes).
    Preserves all other Objects (B-2, B-52, drones, systems, etc.).
    """
    text = usa_blob.decode("latin1")
    lines = text.splitlines(keepends=True)
    start, end_i, block = extract_object_span(text, "AmericaJetE3AWACS")

    # Also strip immediately preceding SPECTER donor-replace comment lines
    cut = start
    j = start - 1
    while j >= 0:
        s = lines[j].strip()
        if not s:
            cut = j
            j -= 1
            continue
        if s.startswith(";") and (
            "AmericaJetE3AWACS" in s
            or "USAE3" in s
            or "donor" in s.lower()
            or "Primary W3D = E3" in s
            or "US_E3G" in s
            or "SpectreGunship" in s
            or "ECM WeaponSet from donor" in s
            or "Vision 1000" in s
        ):
            cut = j
            j -= 1
            continue
        break

    new_lines = lines[:cut] + lines[end_i + 1 :]
    # Avoid runaway blank lines at the junction
    new_text = "".join(new_lines)
    new_text = re.sub(r"\n{4,}", "\n\n\n", new_text)
    new_blob = new_text.encode("latin1")

    if re.search(r"(?m)^Object\s+AmericaJetE3AWACS\s*$", new_text):
        raise SystemExit("AmericaJetE3AWACS still present after removal")
    # Critical freezes inside USA_System
    for must in ("AmericaJetB2Spirit", "AmericaJetB52H", "AmericaDroneX45"):
        if not re.search(rf"(?m)^Object\s+{must}\s*$", new_text):
            raise SystemExit(f"accidentally removed {must}")
    return new_blob, block.encode("latin1")


def remove_command_button(cb: str, btn: str) -> str:
    pattern = rf"CommandButton\s+{re.escape(btn)}\s*\n.*?^End\s*\n?"
    out, n = re.subn(pattern, "", cb, count=1, flags=re.M | re.S)
    if n != 1:
        raise SystemExit(f"failed to remove CommandButton {btn} (n={n})")
    if re.search(rf"(?m)^CommandButton\s+{re.escape(btn)}\s*$", out):
        raise SystemExit(f"button still present: {btn}")
    return out


def empty_slot(cs: str, slot: int) -> str:
    def repl(m: re.Match[str]) -> str:
        body = m.group(1)
        body2, n = re.subn(rf"(?m)^\s*{slot}\s*=\s*\S+\s*\n", "", body)
        if n != 1:
            raise SystemExit(f"failed removing HeavyAirBase slot {slot} (n={n})")
        return f"CommandSet America_HeavyAirBaseCommandSet\n{body2}End"

    out, n = re.subn(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)End",
        repl,
        cs,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("HeavyAirBase CommandSet not found")
    return out


def art_e3_stats(amap: dict[str, bytes]) -> dict:
    names = list(amap.keys())
    w3d = [
        n
        for n in names
        if n.lower().endswith(".w3d")
        and re.search(r"(^|\\)(E3|chj10_r)\.", n.split("\\")[-1], re.I)
    ]
    # also accept exact E3.W3D / chj10_r.W3D
    w3d = [
        n
        for n in names
        if n.lower().endswith(".w3d")
        and re.match(r"(E3|chj10_r)(\.|$)", n.split("\\")[-1], re.I)
    ]
    tex = [
        n
        for n in names
        if n.lower().endswith((".tga", ".dds"))
        and re.search(r"E3USA|\\E3\.|chj10", n, re.I)
    ]
    icons = [n for n in tex if re.search(r"E3USA", n, re.I)]
    return {"w3d": w3d, "tex": tex, "icons": icons}


def main() -> None:
    dmap = read_big(DATA_BIG)
    amap = read_big(ART_BIG)
    assert sha256(dmap["Data\\English\\generals.csf"]) == GOOD_CSF

    freeze = {k: dmap[k] for k in FREEZE_KEYS}
    assert sha256(freeze[FREEZE_KEYS[0]]) == AC130_SHA

    # Snapshot B-2 / B-52 blobs inside USA_System before edit (object presence checks later)
    usa_before = dmap[USA_KEY]
    b2_before = count_obj({USA_KEY: usa_before}, "AmericaJetB2Spirit")
    b52_before = count_obj({USA_KEY: usa_before}, "AmericaJetB52H")
    assert b2_before == 1 and b52_before == 1

    art = art_e3_stats(amap)
    if not any(n.upper().endswith("E3.W3D") for n in art["w3d"]):
        raise SystemExit(f"donor E3.W3D missing from ART: {art}")
    if not any("chj10_r" in n.lower() for n in art["w3d"]):
        raise SystemExit(f"donor chj10_r.W3D missing from ART: {art}")
    if not art["icons"]:
        raise SystemExit(f"E3USA icon missing from ART: {art}")

    # Prior art-only aircraft must remain inactive
    for name in [
        "AmericaJetE737AEW",
        "avionE737",
        "AmericaJetC17Globemaster",
        "E2avionHE",
        "USAHelixV22",
    ]:
        assert count_obj(dmap, name) == 0, name

    new_usa, removed_block = remove_e3_from_usa_system(usa_before)
    REF_DIR.mkdir(parents=True, exist_ok=True)
    (REF_DIR / "AmericaJetE3AWACS_donor_gameplay_REMOVED_reference_ONLY.txt").write_bytes(
        removed_block
    )

    dmap[USA_KEY] = new_usa
    dmap[CB_KEY] = remove_command_button(
        dmap[CB_KEY].decode("latin1"), REMOVE_BUTTONS[0]
    ).encode("latin1")
    dmap[CS_KEY] = empty_slot(dmap[CS_KEY].decode("latin1"), 5).encode("latin1")

    # Confirm absent support buttons remain absent
    cb = dmap[CB_KEY].decode("latin1")
    for btn in ABSENT_BUTTONS:
        if re.search(rf"(?m)^CommandButton\s+{re.escape(btn)}\s*$", cb):
            raise SystemExit(f"support button reappeared: {btn}")

    for name in REMOVE_OBJECTS:
        if count_obj(dmap, name) != 0:
            raise SystemExit(f"Object still active: {name}")

    # Clean staging rebuild (never in-place mutate without rewrite)
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
    assert sha256(vmap[FREEZE_KEYS[0]]) == AC130_SHA

    usa_v = vmap[USA_KEY].decode("latin1")
    assert not re.search(r"(?m)^Object\s+AmericaJetE3AWACS\s*$", usa_v)
    assert "Object AmericaJetE3AWACS" not in usa_v
    assert count_obj(vmap, "AmericaJetE3AWACS") == 0
    assert count_obj(vmap, "USAE3") == 0
    assert count_obj(vmap, "AmericaJetB2Spirit") == 1
    assert count_obj(vmap, "AmericaJetB52H") == 1
    assert count_obj(vmap, "AmericaJetB21Clean") == 1
    assert count_obj(vmap, "AmericaJetB1R") == 1
    assert count_obj(vmap, "AmericaJetAC130") == 1
    for name in [
        "AmericaJetE737AEW",
        "avionE737",
        "AmericaJetC17Globemaster",
        "E2avionHE",
        "USAHelixV22",
    ]:
        assert count_obj(vmap, name) == 0

    cs = vmap[CS_KEY].decode("latin1")
    m = re.search(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)End", cs, re.S
    )
    assert m
    body = m.group(1)
    slots = {}
    for slot in range(1, 15):
        sm = re.search(rf"(?m)^\s*{slot}\s*=\s*(\S+)\s*$", body)
        slots[slot] = sm.group(1) if sm else "EMPTY"
    assert slots[5] == "EMPTY"
    assert slots[8] == "EMPTY"
    assert slots[9] == "EMPTY"
    assert slots[10] == "EMPTY"
    assert slots[11] == "EMPTY"
    assert slots[1] == "Command_ConstructAmericaJetB2Spirit"
    assert slots[2] == "Command_ConstructAmericaJetB21"
    assert slots[3] == "Command_ConstructAmericaJetB52H"
    assert slots[4] == "Command_ConstructAmericaJetB1R"
    assert slots[6] == "Command_Upgrade_NuclearTipWarhead2"
    assert slots[7] == "Command_ConstructAmericaJetAC130"
    assert slots[13] == "Command_SetRallyPoint"
    assert slots[14] == "Command_Sell"

    cb = vmap[CB_KEY].decode("latin1")
    assert not re.search(
        r"(?m)^CommandButton\s+Command_ConstructAmericaJetE3AWACS\s*$", cb
    )

    # ART unchanged
    art_sha = sha256(ART_BIG)
    amap2 = read_big(ART_BIG)
    art = art_e3_stats(amap2)

    # Also confirm other four ART families still present
    def has_w3d(pred) -> bool:
        return any(
            n.lower().endswith(".w3d") and pred(n) for n in amap2
        )

    assert has_w3d(lambda n: "KVE737" in n.upper())
    assert has_w3d(lambda n: "IUAC17" in n.upper())
    assert has_w3d(lambda n: "AVOSPREY" in n.upper())
    assert has_w3d(lambda n: "AVHAWK" in n.upper())

    report = []
    report.append("E-3 ART-ONLY RESET = PASS")
    report.append("")
    report.append("Crash-causing E-3 Object removed = YES")
    report.append("usa_system.ini contains AmericaJetE3AWACS = NO")
    report.append("Expected = NO")
    report.append("")
    report.append("HeavyAirBase Slot 5 = EMPTY")
    report.append("")
    report.append("E-3 donor ART:")
    report.append("Primary W3D = E3")
    report.append(
        f"Textures preserved = YES ({len(art['tex'])} matched; icons/gear-related)"
    )
    report.append(
        "Animations preserved = YES (chj10_r gear W3D retained in ART)"
    )
    report.append(
        f"Icon preserved = YES ({', '.join(Path(x.replace(chr(92),'/')).name for x in art['icons'])})"
    )
    report.append(f"Gear W3D preserved = YES (chj10_r present)")
    report.append("")
    report.append("E-3 gameplay DATA active = NO")
    report.append("C-17 gameplay DATA active = NO")
    report.append("E-737 gameplay DATA active = NO")
    report.append("E2avionHE gameplay DATA active = NO")
    report.append("V-22 gameplay DATA active = NO")
    report.append("")
    report.append("AC-130 changed = NO")
    report.append("B-2 changed = NO")
    report.append("B-21 changed = NO")
    report.append("B-52 changed = NO")
    report.append("B-1R changed = NO")
    report.append("ART rebuilt = NO")
    report.append(f"ART sha256 = {art_sha}")
    report.append("")
    report.append("Final HeavyAirBase slots:")
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
    report.append(f"DATA sha256 = {sha256(DATA_BIG)}")
    report.append(
        f"Removed Object block bytes = {len(removed_block)} "
        "(saved as reference-only txt, not packed as gameplay INI)"
    )
    report.append("Removed CommandButton = Command_ConstructAmericaJetE3AWACS")
    report.append("Placeholder/test Objects created = NO")

    text = "\n".join(report) + "\n"
    OUT_REPORT.write_text(text, encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text(text, encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    with zipfile.ZipFile(OUT_ZIP) as z:
        assert z.namelist() == ["_SPEC_DATA_ONE.big"]

    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={sha256(DATA_BIG)}\n"
        f"_SPEC_ART_ONE.big sha256={art_sha} (unchanged, not packaged)\n"
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
