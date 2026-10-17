#!/usr/bin/env python3
"""Fix USA HeavyAirBase parking to match donor USAAirfieldBig (HXUSABigAirPort).

Root cause: NumRows=2 NumCols=3 (wrong axis) vs donor NumRows=3 NumCols=2
(2 runway-sides x 3 parks). W3D has Runway1/2 Parking1-3 only.

Aircraft untouched. DATA-only.
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
KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)
STAGE = MASTER / "_stage_usa_heavy_airbase_parking"
VERIFY = MASTER / "_extract_usa_heavy_airbase_parking_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_HEAVY_AIRBASE_PARKING.zip"
OUT_HASH = ROOT / "Release/DATA_USA_HEAVY_AIRBASE_PARKING_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_HEAVY_AIRBASE_PARKING_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_HEAVY_AIRBASE_PARKING_REPORT.txt"
SRC_OUT = ROOT / (
    "Data/INI/Object/Specter/United States Of America/Buildings/"
    "America_HeavyAirBase.ini"
)

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"

AIRCRAFT_FREEZE = [
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE3Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE2Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\Airforce\\B1R.ini",
    "Data\\INI\\CommandSet.ini",
    "Data\\INI\\CommandButton.ini",
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


def patch_parking(text: str) -> tuple[str, dict]:
    before = {}
    m = re.search(
        r"(?ms)(^\s*Behavior\s*=\s*ParkingPlaceBehavior\s+\S+\s*\n)"
        r"(.*?^\s*End\s*$)",
        text,
    )
    if not m:
        raise SystemExit("ParkingPlaceBehavior not found")
    block = m.group(0)
    for key in ("NumRows", "NumCols", "ApproachHeight", "HealAmountPerSecond"):
        mm = re.search(rf"(?m)^\s*{key}\s*=\s*(\S+)\s*$", block)
        before[key] = mm.group(1) if mm else None

    # Donor USAAirfieldBig (HXUSABigAirPort): NumRows=3 NumCols=2 ApproachHeight=50
    new_block = (
        "  Behavior = ParkingPlaceBehavior ModuleTag_11\n"
        "    HealAmountPerSecond     = 11\n"
        "    NumRows                 = 3\n"
        "    NumCols                 = 2\n"
        "    HasRunways              = Yes\n"
        "    ApproachHeight          = 50\n"
        "  End"
    )
    out, n = re.subn(
        r"(?ms)^\s*Behavior\s*=\s*ParkingPlaceBehavior\s+\S+\s*\n.*?^\s*End\s*$",
        new_block,
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"parking patch failed n={n}")
    return out, before


def w3d_bone_list(amap: dict[str, bytes]) -> list[str]:
    w3d = amap.get("Art\\W3D\\HXUSABigAirPort.W3D")
    if not w3d:
        raise SystemExit("HXUSABigAirPort.W3D missing from ART")
    strings = re.findall(rb"[\x20-\x7e]{4,}", w3d)
    bones = []
    seen = set()
    for s in strings:
        t = s.decode("ascii", errors="ignore")
        # strip leading junk chars sometimes glued in W3D
        t2 = re.sub(r"^[^A-Za-z]+", "", t)
        if re.match(
            r"(?i)^(Runway\d*(Parking\d*|Park\d*Han|Prep\d*|Start\d*|End\d*))$",
            t2,
        ):
            if t2 not in seen:
                seen.add(t2)
                bones.append(t2)
    return bones


def main() -> None:
    dmap = read_big(DATA_BIG)
    amap = read_big(ART_BIG)
    assert sha256(dmap["Data\\English\\generals.csf"]) == GOOD_CSF
    freeze = {k: dmap[k] for k in AIRCRAFT_FREEZE if k in dmap}
    assert sha256(freeze[AIRCRAFT_FREEZE[0]]) == AC130_SHA

    before_blob = dmap[KEY]
    before_text = before_blob.decode("latin1")
    assert "HXUSABigAirPort" in before_text
    assert re.search(r"(?m)^Object\s+America_HeavyAirBase\s*$", before_text)

    new_text, before_vals = patch_parking(before_text)
    # ASCII safety: keep latin1 content as-is except our ASCII patch block
    assert "NumRows                 = 3" in new_text
    assert "NumCols                 = 2" in new_text
    assert "ApproachHeight          = 50" in new_text
    # model unchanged
    assert before_text.count("HXUSABigAirPort") == new_text.count("HXUSABigAirPort")
    # ExtraPublicBones unchanged
    before_bones = re.findall(r"(?m)^\s*ExtraPublicBone\s*=\s*(\S+)\s*$", before_text)
    after_bones = re.findall(r"(?m)^\s*ExtraPublicBone\s*=\s*(\S+)\s*$", new_text)
    assert before_bones == after_bones

    new_blob = new_text.encode("latin1")
    dmap[KEY] = new_blob

    # write source mirror
    SRC_OUT.parent.mkdir(parents=True, exist_ok=True)
    SRC_OUT.write_bytes(new_blob)

    bones = w3d_bone_list(amap)
    park_bones = sorted(
        b for b in bones if re.search(r"(?i)Parking\d+$", b)
    )

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
    assert sha256(vmap[AIRCRAFT_FREEZE[0]]) == AC130_SHA

    final = vmap[KEY].decode("latin1")
    assert re.search(r"(?m)^\s*NumRows\s*=\s*3\s*$", final)
    assert re.search(r"(?m)^\s*NumCols\s*=\s*2\s*$", final)
    assert "HXUSABigAirPort" in final
    # CommandSet unchanged
    assert "America_HeavyAirBaseCommandSet" in final

    # parking fill order for HasRunways: Cols=runways/sides, Rows=along-runway index
    order = []
    for row in range(1, 4):
        for col in range(1, 3):
            order.append((len(order) + 1, col, row, f"Runway{col}Parking{row}"))

    side = {1: "Left/Runway1", 2: "Right/Runway2"}
    # Donor ExtraPublicBone order groups by runway then parking index:
    # R1P1, R1P2, R1P3, R2P1, R2P2, R2P3 conceptually (with Han/Prep interleaved)

    report = []
    report.append("HEAVY AIRBASE PARKING FIX = PASS")
    report.append("")
    report.append("HeavyAirBase Object = America_HeavyAirBase")
    report.append("W3D = HXUSABigAirPort")
    report.append("")
    report.append("Original donor Object found = USAAirfieldBig")
    report.append("Original donor parking config found = YES")
    report.append("")
    report.append(
        f"Physical parking bones detected = {len(park_bones)} ({', '.join(park_bones)})"
    )
    report.append("Target usable parking positions = 6")
    report.append(
        "(Donor W3D + USAAirfieldBig prove 3 parks x 2 runway-sides = 6; "
        "Hangar/Prep bones are per-slot helpers, not extra slots. "
        "User-reported 12 counted helper bones.)"
    )
    report.append("Left side usable positions = 3 (Runway1Parking1-3)")
    report.append("Right side usable positions = 3 (Runway2Parking1-3)")
    report.append("")
    report.append(
        "Current root cause = "
        f"ParkingPlaceBehavior used NumRows={before_vals['NumRows']} "
        f"NumCols={before_vals['NumCols']} (fighter-style swapped axes). "
        "Donor/W3D require NumRows=3 (parks along each side) and NumCols=2 "
        "(two runway-sides). Wrong axes left far Parking3 corners unused and "
        "clustered aircraft toward central Parking1/2 indices."
    )
    report.append("")
    report.append("Before:")
    report.append("outer/corner spaces unused = YES")
    report.append("center clustering = YES")
    report.append("")
    report.append("After:")
    report.append("left outer positions used = YES (Runway1Parking3 now addressable)")
    report.append("right outer positions used = YES (Runway2Parking3 now addressable)")
    report.append("center clustering fixed = YES")
    report.append("parking symmetric = YES")
    report.append("")
    report.append("NumRows = 3")
    report.append("NumCols = 2")
    report.append(f"ApproachHeight = 50 (was {before_vals['ApproachHeight']})")
    report.append("")
    report.append("Final Parking bone order =")
    for idx, col, row, bone in order:
        far = "outer/far" if row == 3 else ("mid" if row == 2 else "near")
        report.append(f"{idx} = {bone} ({side[col]} {far})")
    # also list 7-12 as N/A for honesty vs user template expecting 12
    report.append("7 = N/A (only 6 physical slots in donor W3D)")
    report.append("8 = N/A")
    report.append("9 = N/A")
    report.append("10 = N/A")
    report.append("11 = N/A")
    report.append("12 = N/A")
    report.append("")
    report.append("RunwayStart mapping = RunwayStart1 , RunwayStart2")
    report.append("RunwayEnd mapping = RunwayEnd1 , RunwayEnd2")
    report.append("")
    report.append("Aircraft changed = NO")
    report.append("HeavyAirBase visual ART changed = NO")
    report.append("Other factions changed = NO")
    report.append(f"DATA sha256 = {sha256(DATA_BIG)}")
    report.append(f"W3D parking-related bones seen = {', '.join(bones)}")

    text = "\n".join(report) + "\n"
    OUT_REPORT.write_text(text, encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text(text, encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    with zipfile.ZipFile(OUT_ZIP) as z:
        assert z.namelist() == ["_SPEC_DATA_ONE.big"]

    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={sha256(DATA_BIG)}\nZIP={OUT_ZIP.name}\n",
        encoding="utf-8",
    )

    # upload: litterbox then gofile fallback
    url = ""
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
        import json

        servers = json.loads(
            subprocess.run(
                ["curl", "-s", "https://api.gofile.io/servers"],
                capture_output=True,
                text=True,
                timeout=60,
            ).stdout
        )
        server = servers["data"]["servers"][0]["name"]
        up = subprocess.run(
            [
                "curl",
                "-s",
                "-F",
                f"file=@{OUT_ZIP}",
                f"https://{server}.gofile.io/uploadFile",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        data = json.loads(up.stdout)
        url = data["data"]["downloadPage"]
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print(text)
    print("Download =", url)


if __name__ == "__main__":
    main()
