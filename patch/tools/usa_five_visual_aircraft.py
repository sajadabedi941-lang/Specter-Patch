#!/usr/bin/env python3
"""USA HeavyAirBase: five donor-visual base aircraft (B-21 method).

Specter-safe Objects + donor ART only. No donor gameplay DATA.
Slots: 5=E3, 8=C17, 9=E737, 10=E2, 11=V22.
DATA-only if ART already has assets.
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
OBJ_DIR = ROOT / "Data/INI/Object/Specter/United States Of America"
STAGE = MASTER / "_stage_usa_five_visual_aircraft"
VERIFY = MASTER / "_extract_usa_five_visual_aircraft_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_FIVE_VISUAL_AIRCRAFT.zip"
OUT_HASH = ROOT / "Release/DATA_USA_FIVE_VISUAL_AIRCRAFT_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_FIVE_VISUAL_AIRCRAFT_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_FIVE_VISUAL_AIRCRAFT_REPORT.txt"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"

AIRCRAFT = [
    {
        "obj": "AmericaJetE3Visual",
        "file": "AmericaJetE3Visual.ini",
        "btn": "Command_ConstructAmericaJetE3Visual",
        "slot": 5,
        "w3d": "E3",
        "icon": "E3USA",
        "label": "E-3",
        "role": "AWACS",
    },
    {
        "obj": "AmericaJetC17Visual",
        "file": "AmericaJetC17Visual.ini",
        "btn": "Command_ConstructAmericaJetC17Visual",
        "slot": 8,
        "w3d": "IUAC17HXNew",
        "icon": "C17GlobalMaster",
        "label": "C-17",
        "role": "Transport",
    },
    {
        "obj": "AmericaJetE737Visual",
        "file": "AmericaJetE737Visual.ini",
        "btn": "Command_ConstructAmericaJetE737Visual",
        "slot": 9,
        "w3d": "KVE737",
        "icon": "avionE737",
        "label": "E-737",
        "role": "AEW",
    },
    {
        "obj": "AmericaJetE2Visual",
        "file": "AmericaJetE2Visual.ini",
        "btn": "Command_ConstructAmericaJetE2Visual",
        "slot": 10,
        "w3d": "AVHawk",
        "icon": "E2avionHE",
        "label": "E2",
        "role": "Radar",
    },
    {
        "obj": "AmericaJetV22Visual",
        "file": "AmericaJetV22Visual.ini",
        "btn": "Command_ConstructAmericaJetV22Visual",
        "slot": 11,
        "w3d": "AVOsprey",
        "icon": "V22",
        "label": "V-22",
        "role": "Transport",
    },
]

FORBIDDEN_OBJECTS = [
    "AmericaJetE3AWACS",
    "USAE3",
    "AmericaJetE737AEW",
    "avionE737",
    "AmericaJetC17Globemaster",
    "USAC17GlobalMaster",
    "E2avionHE",
    "USAHelixV22",
    "AmericaJetV22",
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


def count_obj(file_map: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(name)}\s*$".encode())
    return sum(len(pat.findall(b)) for b in file_map.values())


def structure_ok(blob: bytes, obj: str, w3d: str) -> None:
    assert all(c < 128 for c in blob), f"{obj} non-ASCII"
    assert b"\x00" not in blob
    assert not blob.startswith(b"\xef\xbb\xbf")
    text = blob.decode("ascii")
    assert len(re.findall(r"(?m)^Object\s+\S+", text)) == 1
    assert re.search(rf"(?m)^Object\s+{re.escape(obj)}\s*$", text)
    assert w3d in text
    assert not re.search(r"(?m)^\s*WeaponSet\b", text)
    assert "SpectreGunship" not in text
    assert "TransportContain" not in text
    stack: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(";"):
            continue
        if s.startswith("Object "):
            stack = ["Object"]
        elif re.match(
            r"^(Draw|Behavior|ArmorSet|WeaponSet|Body|UnitSpecificSounds|"
            r"Prerequisites|DefaultConditionState|ConditionState|TransitionState)\b",
            s,
        ):
            stack.append(s.split()[0])
        elif s == "End":
            assert stack, f"{obj} extra End"
            stack.pop()
    assert stack == [], f"{obj} unclosed {stack}"


def upsert_button(cb: str, btn: str, obj: str, icon: str, text_label: str) -> str:
    block = (
        f"CommandButton {btn}\n"
        f"  Command       = UNIT_BUILD\n"
        f"  Object        = {obj}\n"
        f"  TextLabel     = {text_label}\n"
        f"  ButtonImage   = {icon}\n"
        f"  ButtonBorderType = BUILD\n"
        f"  DescriptLabel = {text_label}if\n"
        f"End\n"
    )
    if re.search(rf"(?m)^CommandButton\s+{re.escape(btn)}\s*$", cb):
        cb, n = re.subn(
            rf"CommandButton\s+{re.escape(btn)}\s*\n.*?^End\s*$",
            block.rstrip(),
            cb,
            count=1,
            flags=re.M | re.S,
        )
        assert n == 1
        return cb
    # insert before America_HeavyAirBase-related area: after last America construct jet button near end of USA section
    anchor = "CommandButton Command_ConstructAmericaJetAC130"
    if anchor not in cb:
        raise SystemExit("AC130 button missing; refuse to insert")
    # append after AC130 button End
    m = re.search(
        rf"CommandButton\s+Command_ConstructAmericaJetAC130\s*\n.*?^End\s*$",
        cb,
        flags=re.M | re.S,
    )
    assert m
    insert_at = m.end()
    return cb[:insert_at] + "\n\n" + block + cb[insert_at:]


def patch_heavy_airbase(cs: str) -> str:
    def repl(m: re.Match[str]) -> str:
        body = (
            "  1  = Command_ConstructAmericaJetB2Spirit\n"
            "  2  = Command_ConstructAmericaJetB21\n"
            "  3  = Command_ConstructAmericaJetB52H\n"
            "  4  = Command_ConstructAmericaJetB1R\n"
            "  5  = Command_ConstructAmericaJetE3Visual\n"
            "  6  = Command_Upgrade_NuclearTipWarhead2\n"
            "  7  = Command_ConstructAmericaJetAC130\n"
            "  8  = Command_ConstructAmericaJetC17Visual\n"
            "  9  = Command_ConstructAmericaJetE737Visual\n"
            "  10 = Command_ConstructAmericaJetE2Visual\n"
            "  11 = Command_ConstructAmericaJetV22Visual\n"
            "  13 = Command_SetRallyPoint\n"
            "  14 = Command_Sell\n"
        )
        return f"CommandSet America_HeavyAirBaseCommandSet\n{body}End"

    out, n = re.subn(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)End",
        repl,
        cs,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("HeavyAirBase CommandSet not patched")
    return out


def main() -> None:
    dmap = read_big(DATA_BIG)
    amap = read_big(ART_BIG)
    assert sha256(dmap["Data\\English\\generals.csf"]) == GOOD_CSF
    freeze = {k: dmap[k] for k in FREEZE_KEYS}
    assert sha256(freeze[FREEZE_KEYS[0]]) == AC130_SHA
    art_sha = sha256(ART_BIG)

    # ART dependencies
    required_art = {
        "E3": [r"Art\\W3D\\E3\.W3D$"],
        "KVE737": [r"Art\\W3D\\KVE737\.W3D$"],
        "IUAC17HXNew": [r"Art\\W3D\\IUAC17HXNew\.W3D$"],
        "AVHawk": [r"Art\\W3D\\AVHawk\.W3D$"],
        "AVOsprey": [r"Art\\W3D\\AVOsprey\.W3D$"],
    }
    for label, pats in required_art.items():
        for pat in pats:
            if not any(re.search(pat, k, re.I) for k in amap):
                raise SystemExit(f"missing ART {label} / {pat}")

    # Remove any leftover forbidden object files if present
    for key in list(dmap):
        base = key.rsplit("\\", 1)[-1].lower()
        if base in {
            "americajete3awacs.ini",
            "americajete737aew.ini",
            "avione737.ini",
            "americajetc17globemaster.ini",
            "e2avionhe.ini",
            "usahelixv22.ini",
        }:
            del dmap[key]

    cb = dmap["Data\\INI\\CommandButton.ini"].decode("latin1")
    cs = dmap["Data\\INI\\CommandSet.ini"].decode("latin1")

    for ac in AIRCRAFT:
        src = OBJ_DIR / ac["file"]
        blob = src.read_bytes()
        # normalize to LF ASCII
        text = blob.decode("utf-8")
        assert all(ord(c) < 128 for c in text)
        blob = text.replace("\r\n", "\n").encode("ascii")
        structure_ok(blob, ac["obj"], ac["w3d"])
        key = f"Data\\INI\\Object\\Specter\\United States Of America\\{ac['file']}"
        dmap[key] = blob
        label = f"CONTROLBAR:{ac['obj']}"
        cb = upsert_button(cb, ac["btn"], ac["obj"], ac["icon"], label)

    cs = patch_heavy_airbase(cs)
    dmap["Data\\INI\\CommandButton.ini"] = cb.encode("latin1")
    dmap["Data\\INI\\CommandSet.ini"] = cs.encode("latin1")

    for name in FORBIDDEN_OBJECTS:
        if count_obj(dmap, name) != 0:
            raise SystemExit(f"forbidden object still active: {name}")

    for ac in AIRCRAFT:
        assert count_obj(dmap, ac["obj"]) == 1

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
    assert sha256(ART_BIG) == art_sha

    for name in FORBIDDEN_OBJECTS:
        assert count_obj(vmap, name) == 0
    for ac in AIRCRAFT:
        assert count_obj(vmap, ac["obj"]) == 1
        key = f"Data\\INI\\Object\\Specter\\United States Of America\\{ac['file']}"
        structure_ok(vmap[key], ac["obj"], ac["w3d"])

    cb = vmap["Data\\INI\\CommandButton.ini"].decode("latin1")
    cs = vmap["Data\\INI\\CommandSet.ini"].decode("latin1")
    heavy = re.search(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)End", cs, re.S
    )
    assert heavy
    body = heavy.group(1)
    expected_slots = {
        1: "Command_ConstructAmericaJetB2Spirit",
        2: "Command_ConstructAmericaJetB21",
        3: "Command_ConstructAmericaJetB52H",
        4: "Command_ConstructAmericaJetB1R",
        5: "Command_ConstructAmericaJetE3Visual",
        6: "Command_Upgrade_NuclearTipWarhead2",
        7: "Command_ConstructAmericaJetAC130",
        8: "Command_ConstructAmericaJetC17Visual",
        9: "Command_ConstructAmericaJetE737Visual",
        10: "Command_ConstructAmericaJetE2Visual",
        11: "Command_ConstructAmericaJetV22Visual",
        13: "Command_SetRallyPoint",
        14: "Command_Sell",
    }
    for slot, cmd in expected_slots.items():
        assert re.search(rf"(?m)^\s*{slot}\s*=\s*{re.escape(cmd)}\s*$", body), (
            slot,
            cmd,
        )

    for ac in AIRCRAFT:
        m = re.search(
            rf"CommandButton\s+{re.escape(ac['btn'])}\s*\n(.*?)End", cb, re.S
        )
        assert m
        assert "UNIT_BUILD" in m.group(0)
        assert re.search(rf"(?m)^\s*Object\s*=\s*{re.escape(ac['obj'])}\s*$", m.group(0))

    # working aircraft object counts
    assert count_obj(vmap, "AmericaJetAC130") == 1
    assert count_obj(vmap, "AmericaJetB21Clean") == 1
    assert count_obj(vmap, "AmericaJetB2Spirit") == 1
    assert count_obj(vmap, "AmericaJetB52H") == 1
    assert count_obj(vmap, "AmericaJetB1R") == 1

    report = []
    report.append("FIVE DONOR-VISUAL AIRCRAFT BASE BUILD = PASS")
    report.append("")
    report.append("METHOD:")
    report.append("Donor DATA used = NO")
    report.append("Donor ART used = YES")
    report.append("Specter-compatible Object structure used = YES")
    report.append("B-21 integration method followed = YES")
    report.append("Skeleton = Specter JetAI/F100 (jets) + heli JetAI/T700 (V-22)")
    report.append("BASE AIRCRAFT BUILDS/SPAWNS STRUCTURALLY READY")
    report.append("GAME BOOT / ROLE FUNCTION CLAIMED = NO")
    report.append("")

    details = [
        ("E-3", "AmericaJetE3Visual", "E3", 5, "AWACS functionality = NOT YET"),
        ("C-17", "AmericaJetC17Visual", "IUAC17HXNew", 8, "Transport functionality = NOT YET"),
        ("E-737", "AmericaJetE737Visual", "KVE737", 9, "AEW functionality = NOT YET"),
        ("E2", "AmericaJetE2Visual", "AVHawk", 10, "Radar functionality = NOT YET"),
        ("V-22", "AmericaJetV22Visual", "AVOsprey", 11, "Transport functionality = NOT YET"),
    ]
    for label, obj, w3d, slot, note in details:
        report.append(f"{label}:")
        report.append(f"Final Object = {obj}")
        report.append(f"Visual W3D = {w3d}")
        report.append("Donor ART = YES")
        report.append("Donor DATA = NO")
        report.append(f"HeavyAirBase slot = {slot}")
        report.append(note)
        report.append("Weapons = NONE")
        report.append("")

    report.append("AC-130 changed = NO")
    report.append("B-2/B-21/B-52/B-1R changed = NO")
    report.append("Other factions changed = NO")
    report.append("ART rebuilt = NO")
    report.append(f"ART sha256 = {art_sha}")
    report.append(f"DATA sha256 = {sha256(DATA_BIG)}")

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
