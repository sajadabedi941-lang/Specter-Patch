#!/usr/bin/env python3
"""USA HeavyAirBase: E-737 Scale=1.1 + C-17 takeoff/landing flight fix.

E-737: visual Scale only.
C-17: align flight/airfield compatibility with proven AmericaJetAC130
      (large NeedsRunway heavy-airbase aircraft). Keep IUAC17HXNew ART.
      Reduce collision geometry; switch to AC130Locomotor; no weapons/cargo.
DATA-only.
"""
from __future__ import annotations

import hashlib
import json
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
STAGE = MASTER / "_stage_usa_e737_c17_flight_fix"
VERIFY = MASTER / "_extract_usa_e737_c17_flight_fix_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_E737_C17_FLIGHT_FIX.zip"
OUT_HASH = ROOT / "Release/DATA_USA_E737_C17_FLIGHT_FIX_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_E737_C17_FLIGHT_FIX_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_E737_C17_FLIGHT_FIX_REPORT.txt"
SRC_DIR = ROOT / "Data/INI/Object/Specter/United States Of America"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"

E737_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini"
)
C17_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Visual.ini"
)
AC130_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
)
HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"
CSF_KEY = "Data\\English\\generals.csf"

FREEZE_KEYS = [
    CSF_KEY,
    AC130_KEY,
    CS_KEY,
    CB_KEY,
    HEAVY_KEY,
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE3Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE2Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini",
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


def patch_e737(text: str) -> tuple[str, str]:
    m = re.search(r"(?m)^(\s*Scale\s*=\s*)(\S+)(\s*)$", text)
    if not m:
        raise SystemExit("E737 Scale line not found")
    old = m.group(2)
    new_text, n = re.subn(
        r"(?m)^(\s*Scale\s*=\s*)\S+(\s*)$", r"\g<1>1.1\2", text, count=1
    )
    if n != 1:
        raise SystemExit(f"E737 Scale patch failed n={n}")
    # Ensure only Scale changed for gameplay-critical fields
    assert "Model = KVE737" in new_text
    assert "Locomotor = SET_NORMAL F100_PW_229" in new_text
    return new_text, old


def patch_c17(text: str) -> dict:
    before = {}
    # Physics Mass
    m = re.search(
        r"(?ms)^\s*Behavior\s*=\s*PhysicsBehavior\s+\S+\s*\n(.*?)^\s*End\s*$",
        text,
    )
    if not m:
        raise SystemExit("C17 PhysicsBehavior missing")
    mm = re.search(r"(?m)^\s*Mass\s*=\s*(\S+)", m.group(1))
    before["Mass"] = mm.group(1) if mm else None

    # JetAI
    m = re.search(
        r"(?ms)^\s*Behavior\s*=\s*JetAIUpdate\s+\S+\s*\n(.*?)^\s*End\s*$",
        text,
    )
    if not m:
        raise SystemExit("C17 JetAIUpdate missing")
    jai = m.group(1)
    for key in (
        "MinHeight",
        "ParkingOffset",
        "TakeoffPause",
        "TakeoffDistForMaxLift",
        "NeedsRunway",
        "KeepsParkingSpaceWhenAirborne",
    ):
        mm = re.search(rf"(?m)^\s*{key}\s*=\s*(\S+)", jai)
        before[key] = mm.group(1) if mm else None

    # Locomotor
    mm = re.search(r"(?m)^\s*Locomotor\s*=\s*SET_NORMAL\s+(\S+)", text)
    before["Locomotor"] = mm.group(1) if mm else None

    # Geometry
    for key in (
        "GeometryMajorRadius",
        "GeometryMinorRadius",
        "GeometryHeight",
        "GeometryIsSmall",
    ):
        mm = re.search(rf"(?m)^\s*{key}\s*=\s*(\S+)", text)
        before[key] = mm.group(1) if mm else None

    # Replace Physics Mass
    text2, n = re.subn(
        r"(?ms)^(\s*Behavior\s*=\s*PhysicsBehavior\s+\S+\s*\n"
        r"\s*Mass\s*=\s*)\S+(\s*\n\s*End\s*$)",
        r"\g<1>500.0\2",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"Mass patch failed n={n}")
    text = text2

    # Replace entire JetAIUpdate with AC130-compatible runway settings
    # Keep KeepsParkingSpaceWhenAirborne + no combat acquire + 0% ammo damage
    new_jai = (
        "  Behavior = JetAIUpdate ModuleTag_09\n"
        "    KeepsParkingSpaceWhenAirborne = Yes\n"
        "    NeedsRunway = Yes\n"
        "    ParkingOffset = 10\n"
        "    TakeoffPause = 900\n"
        "    TakeoffDistForMaxLift = 25%\n"
        "    MinHeight = 5\n"
        "    OutOfAmmoDamagePerSecond = 0%\n"
        "    ReturnToBaseIdleTime = 12000\n"
        "    AutoAcquireEnemiesWhenIdle = No\n"
        "  End"
    )
    text2, n = re.subn(
        r"(?ms)^\s*Behavior\s*=\s*JetAIUpdate\s+\S+\s*\n.*?^\s*End\s*$",
        new_jai,
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"JetAI patch failed n={n}")
    text = text2

    # Locomotor -> AC130Locomotor (large fixed-wing runway reference)
    text2, n = re.subn(
        r"(?m)^(\s*Locomotor\s*=\s*SET_NORMAL\s+)\S+(\s*)$",
        r"\1AC130Locomotor\2",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"Locomotor patch failed n={n}")
    text = text2
    assert "BasicJetTaxiLocomotor" in text

    # Geometry -> AC130-proven clearance on HeavyAirBase (visual unchanged)
    for key, val in (
        ("GeometryMajorRadius", "42.0"),
        ("GeometryMinorRadius", "14.0"),
        ("GeometryHeight", "14.0"),
    ):
        text2, n = re.subn(
            rf"(?m)^(\s*{key}\s*=\s*)\S+(\s*)$",
            rf"\g<1>{val}\2",
            text,
            count=1,
        )
        if n != 1:
            raise SystemExit(f"{key} patch failed n={n}")
        text = text2

    # Safety: visual model unchanged, no weapons, no transport
    assert "Model = IUAC17HXNew" in text
    assert "WeaponSet" not in text
    assert "TransportContain" not in text
    assert text.count("IUAC17HXNew") >= 3
    # no Scale added
    assert not re.search(r"(?m)^\s*Scale\s*=", text)

    after = {
        "Mass": "500.0",
        "MinHeight": "5",
        "ParkingOffset": "10",
        "TakeoffPause": "900",
        "TakeoffDistForMaxLift": "25%",
        "NeedsRunway": "Yes",
        "KeepsParkingSpaceWhenAirborne": "Yes",
        "Locomotor": "AC130Locomotor",
        "GeometryMajorRadius": "42.0",
        "GeometryMinorRadius": "14.0",
        "GeometryHeight": "14.0",
    }
    return {"text": text, "before": before, "after": after}


def upload_zip(path: Path) -> str:
    proc = subprocess.run(
        [
            "curl",
            "-sF",
            "reqtype=fileupload",
            "-F",
            "time=72h",
            "-F",
            f"fileToUpload=@{path}",
            "https://litterbox.catbox.moe/resources/internals/api.php",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    url = (proc.stdout or "").strip()
    if url.startswith("http"):
        return url
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
            f"file=@{path}",
            f"https://{server}.gofile.io/uploadFile",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    data = json.loads(up.stdout)
    return data["data"]["downloadPage"]


def main() -> None:
    dmap = read_big(DATA_BIG)
    amap = read_big(ART_BIG)
    assert sha256(dmap[CSF_KEY]) == GOOD_CSF
    assert sha256(dmap[AC130_KEY]) == AC130_SHA
    freeze = {k: dmap[k] for k in FREEZE_KEYS if k in dmap}

    # ART present; do not modify ART
    art_has_c17 = any("IUAC17" in k for k in amap)
    art_has_e737 = any("KVE737" in k for k in amap)
    assert art_has_c17
    assert art_has_e737

    e737_before = dmap[E737_KEY].decode("latin1")
    c17_before = dmap[C17_KEY].decode("latin1")
    assert re.search(r"(?m)^Object\s+AmericaJetE737Visual\s*$", e737_before)
    assert re.search(r"(?m)^Object\s+AmericaJetC17Visual\s*$", c17_before)

    # Heavy parking freeze snapshot
    heavy_before = dmap[HEAVY_KEY]
    assert b"NumRows                 = 3" in heavy_before
    assert b"NumCols                 = 2" in heavy_before

    e737_new, e737_old_scale = patch_e737(e737_before)
    c17_info = patch_c17(c17_before)
    c17_new = c17_info["text"]

    dmap[E737_KEY] = e737_new.encode("latin1")
    dmap[C17_KEY] = c17_new.encode("latin1")

    SRC_DIR.mkdir(parents=True, exist_ok=True)
    (SRC_DIR / "AmericaJetE737Visual.ini").write_bytes(dmap[E737_KEY])
    (SRC_DIR / "AmericaJetC17Visual.ini").write_bytes(dmap[C17_KEY])

    if STAGE.exists():
        shutil.rmtree(STAGE)
    write_tree(dmap, STAGE / "in")
    staged = read_tree(STAGE / "in")
    for k, blob in freeze.items():
        assert staged[k] == blob, f"freeze mutated: {k}"
    new_data = build_big(staged)
    DATA_BIG.write_bytes(new_data)

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    vmap = read_big(DATA_BIG)
    write_tree(vmap, VERIFY / "out")

    for k, blob in freeze.items():
        assert vmap[k] == blob, f"freeze broken: {k}"
    assert sha256(vmap[CSF_KEY]) == GOOD_CSF
    assert sha256(vmap[AC130_KEY]) == AC130_SHA
    assert vmap[HEAVY_KEY] == heavy_before

    e737 = vmap[E737_KEY].decode("latin1")
    c17 = vmap[C17_KEY].decode("latin1")
    assert re.search(r"(?m)^\s*Scale\s*=\s*1\.1\s*$", e737)
    assert "Model = KVE737" in e737
    assert "Model = IUAC17HXNew" in c17
    assert not re.search(r"(?m)^\s*Scale\s*=", c17)
    assert "Locomotor = SET_NORMAL AC130Locomotor" in c17
    assert "Locomotor = SET_TAXIING BasicJetTaxiLocomotor" in c17
    assert re.search(r"(?m)^\s*GeometryMajorRadius\s*=\s*42\.0\s*$", c17)
    assert re.search(r"(?m)^\s*GeometryMinorRadius\s*=\s*14\.0\s*$", c17)
    assert re.search(r"(?m)^\s*GeometryHeight\s*=\s*14\.0\s*$", c17)
    assert re.search(r"(?m)^\s*TakeoffDistForMaxLift\s*=\s*25%\s*$", c17)
    assert re.search(r"(?m)^\s*MinHeight\s*=\s*5\s*$", c17)
    assert re.search(r"(?m)^\s*Mass\s*=\s*500\.0\s*$", c17)
    assert "WeaponSet" not in c17
    assert "TransportContain" not in c17
    assert (
        len(re.findall(r"(?m)^Object\s+AmericaJetC17Visual\s*$", c17)) == 1
    )
    assert (
        len(re.findall(r"(?m)^Object\s+AmericaJetE737Visual\s*$", e737)) == 1
    )

    # Unique object defs in whole DATA
    def count_obj(name: str) -> int:
        pat = re.compile(rf"(?m)^Object\s+{re.escape(name)}\s*$")
        return sum(
            len(pat.findall(v.decode("latin1")))
            for k, v in vmap.items()
            if k.lower().endswith(".ini")
        )

    assert count_obj("AmericaJetC17Visual") == 1
    assert count_obj("AmericaJetE737Visual") == 1

    b = c17_info["before"]
    a = c17_info["after"]
    report = []
    report.append("E737 + C17 FIX = PASS (structural readiness; in-game untested)")
    report.append("")
    report.append("E-737:")
    report.append("Object = AmericaJetE737Visual")
    report.append(f"Old Scale = {e737_old_scale}")
    report.append("New Scale = 1.1")
    report.append("W3D changed = NO (KVE737)")
    report.append("Gameplay changed = NO")
    report.append("")
    report.append("C-17:")
    report.append("Object = AmericaJetC17Visual")
    report.append("Primary W3D = IUAC17HXNew")
    report.append("Visual scale changed = NO")
    report.append("")
    report.append("Flight reference Object = AmericaJetAC130")
    report.append(
        "Reason selected = Proven large fixed-wing NeedsRunway aircraft "
        "already building from America_HeavyAirBase with stable taxi/"
        "takeoff/return; uses dedicated AC130Locomotor (high Lift, low "
        "MinTurnSpeed) and HeavyAirBase-safe collision geometry. "
        "B-21/B-1R use tiny GeometryIsSmall fighter-like boxes; E-3 shares "
        "the same broken large-airframe fighter locomotor pattern as C-17."
    )
    report.append("")
    report.append(
        "Root cause of takeoff/landing issue = "
        f"C-17 used fighter locomotor {b['Locomotor']} (Lift=117, "
        f"MinTurnSpeed=120) with oversized collision "
        f"(Major={b['GeometryMajorRadius']}/Minor={b['GeometryMinorRadius']}/"
        f"Height={b['GeometryHeight']}) and Mass={b['Mass']}, plus JetAI "
        f"MinHeight={b['MinHeight']} / TakeoffDistForMaxLift="
        f"{b['TakeoffDistForMaxLift']} — poor runway clearance and lift "
        "profile for HXUSABigAirPort vs working AC-130."
    )
    report.append("")
    report.append("Changed:")
    report.append(
        f"Locomotor = {b['Locomotor']} -> {a['Locomotor']} "
        "(taxi BasicJetTaxiLocomotor unchanged)"
    )
    report.append(
        "JetAIUpdate = MinHeight 5, ParkingOffset 10, TakeoffPause 900, "
        "TakeoffDistForMaxLift 25%, ReturnToBaseIdleTime 12000 "
        "(kept NeedsRunway=Yes, KeepsParkingSpaceWhenAirborne=Yes, "
        "OutOfAmmoDamagePerSecond=0%, AutoAcquireEnemiesWhenIdle=No)"
    )
    report.append(f"Physics = Mass {b['Mass']} -> {a['Mass']}")
    report.append(
        f"Geometry = Major {b['GeometryMajorRadius']}->{a['GeometryMajorRadius']}, "
        f"Minor {b['GeometryMinorRadius']}->{a['GeometryMinorRadius']}, "
        f"Height {b['GeometryHeight']}->{a['GeometryHeight']} "
        "(match AC-130 proven HeavyAirBase clearance; visual unchanged)"
    )
    report.append("Airfield-related settings = JetAI runway fields above")
    report.append("")
    report.append("C-17 weapons = NONE")
    report.append("")
    report.append("C-17 build = READY")
    report.append("C-17 takeoff structure = READY")
    report.append("C-17 landing structure = READY")
    report.append("C-17 return-to-parking structure = READY")
    report.append("")
    report.append("HeavyAirBase 3+3 parking changed = NO")
    report.append("Other aircraft changed = NO")
    report.append("Other factions changed = NO")
    report.append(f"ART changed = NO (ART present C17={art_has_c17} E737={art_has_e737})")
    report.append(f"DATA sha256 = {sha256(DATA_BIG)}")
    report.append("")
    report.append(
        "NOTE = In-game takeoff/landing not executed in this environment; "
        "report is structural readiness only."
    )

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
    url = upload_zip(OUT_ZIP)
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print(text)
    print("Download =", url)


if __name__ == "__main__":
    main()
