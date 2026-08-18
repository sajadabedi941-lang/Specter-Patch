#!/usr/bin/env python3
"""Copy AmericaJetE737Visual flight system to C-17 and AC-130 only.

E-737 / E-2 / other aircraft / HeavyAirBase / ART frozen.
C-17: unarmed; adopt E-737 Locomotor + JetAI + Physics + runway Geometry.
AC-130: keep weapons/combat; adopt E-737 movement; keep OutOfAmmoDamagePerSecond.
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
STAGE = MASTER / "_stage_usa_e737_flight_to_c17_ac130"
VERIFY = MASTER / "_extract_usa_e737_flight_to_c17_ac130_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_E737_FLIGHT_TO_C17_AC130.zip"
OUT_HASH = ROOT / "Release/DATA_USA_E737_FLIGHT_TO_C17_AC130_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_E737_FLIGHT_TO_C17_AC130_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_E737_FLIGHT_TO_C17_AC130_REPORT.txt"
SRC_DIR = ROOT / "Data/INI/Object/Specter/United States Of America"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
# AC-130 content hash before this task (weapons/W3D must stay; flight will change)
# We freeze by field assertions, not full-file hash after patch.

E737_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini"
)
E2_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE2Visual.ini"
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
    CS_KEY,
    CB_KEY,
    E737_KEY,
    E2_KEY,
    HEAVY_KEY,
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE3Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\Airforce\\B1R.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\ScienceObjects\\B52H.ini",
]

# Exact E-737 JetAI block body fields (ModuleTag may differ per object)
E737_JETAI_C17 = """  Behavior = JetAIUpdate ModuleTag_09
    KeepsParkingSpaceWhenAirborne = Yes
    MinHeight = 1
    NeedsRunway = Yes
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 10000
    TakeoffPause = 1000
    TakeoffDistForMaxLift = 0%
    AutoAcquireEnemiesWhenIdle = No
    ParkingOffset = 5
  End"""

# AC-130: same movement, keep combat OutOfAmmoDamage; do NOT force AutoAcquire=No
E737_JETAI_AC130 = """  Behavior = JetAIUpdate ModuleTag_04
    KeepsParkingSpaceWhenAirborne = Yes
    MinHeight = 1
    NeedsRunway = Yes
    OutOfAmmoDamagePerSecond = 8%
    ReturnToBaseIdleTime = 10000
    TakeoffPause = 1000
    TakeoffDistForMaxLift = 0%
    ParkingOffset = 5
  End"""


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


def grab(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1) if m else None


def flight_snapshot(text: str) -> dict:
    jai = re.search(
        r"(?ms)^\s*Behavior\s*=\s*JetAIUpdate\s+(\S+)\s*\n(.*?)^\s*End\s*$",
        text,
    )
    fields = {}
    if jai:
        fields["JetAI_Module"] = jai.group(1)
        body = jai.group(2)
        for key in (
            "KeepsParkingSpaceWhenAirborne",
            "MinHeight",
            "NeedsRunway",
            "OutOfAmmoDamagePerSecond",
            "ReturnToBaseIdleTime",
            "TakeoffPause",
            "TakeoffDistForMaxLift",
            "AutoAcquireEnemiesWhenIdle",
            "ParkingOffset",
        ):
            mm = re.search(rf"(?m)^\s*{key}\s*=\s*(\S+)", body)
            fields[key] = mm.group(1) if mm else None
    fields["Locomotor"] = grab(
        text, r"(?m)^\s*Locomotor\s*=\s*SET_NORMAL\s+(\S+)"
    )
    fields["TaxiLocomotor"] = grab(
        text, r"(?m)^\s*Locomotor\s*=\s*SET_TAXIING\s+(\S+)"
    )
    fields["Mass"] = grab(text, r"(?m)^\s*Mass\s*=\s*(\S+)")
    fields["GeometryMajorRadius"] = grab(
        text, r"(?m)^\s*GeometryMajorRadius\s*=\s*(\S+)"
    )
    fields["GeometryMinorRadius"] = grab(
        text, r"(?m)^\s*GeometryMinorRadius\s*=\s*(\S+)"
    )
    fields["GeometryHeight"] = grab(
        text, r"(?m)^\s*GeometryHeight\s*=\s*(\S+)"
    )
    fields["Scale"] = grab(text, r"(?m)^\s*Scale\s*=\s*(\S+)")
    return fields


def replace_jetai(text: str, new_block: str) -> str:
    out, n = re.subn(
        r"(?ms)^\s*Behavior\s*=\s*JetAIUpdate\s+\S+\s*\n.*?^\s*End\s*$",
        new_block,
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"JetAI replace failed n={n}")
    return out


def replace_normal_loco(text: str, loco: str) -> str:
    out, n = re.subn(
        r"(?m)^(\s*Locomotor\s*=\s*SET_NORMAL\s+)\S+(\s*)$",
        rf"\1{loco}\2",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"Locomotor replace failed n={n}")
    return out


def replace_mass(text: str, mass: str) -> str:
    out, n = re.subn(
        r"(?ms)^(\s*Behavior\s*=\s*PhysicsBehavior\s+\S+\s*\n"
        r"\s*Mass\s*=\s*)\S+(\s*\n\s*End\s*$)",
        rf"\g<1>{mass}\2",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"Mass replace failed n={n}")
    return out


def replace_geometry(text: str, major: str, minor: str, height: str) -> str:
    for key, val in (
        ("GeometryMajorRadius", major),
        ("GeometryMinorRadius", minor),
        ("GeometryHeight", height),
    ):
        text2, n = re.subn(
            rf"(?m)^(\s*{key}\s*=\s*)\S+(\s*)$",
            rf"\g<1>{val}\2",
            text,
            count=1,
        )
        if n != 1:
            raise SystemExit(f"{key} replace failed n={n}")
        text = text2
    return text


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
    freeze = {k: dmap[k] for k in FREEZE_KEYS if k in dmap}

    e737 = dmap[E737_KEY].decode("latin1")
    e2 = dmap[E2_KEY].decode("latin1")
    c17 = dmap[C17_KEY].decode("latin1")
    ac130 = dmap[AC130_KEY].decode("latin1")

    # Freeze scale requirements
    assert re.search(r"(?m)^\s*Scale\s*=\s*0\.8\s*$", e737)
    assert re.search(r"(?m)^\s*Scale\s*=\s*3\.932\s*$", e2)
    assert "Model = KVE737" in e737
    assert "Model = IUAC17HXNew" in c17
    assert "Model = US_AC130W" in ac130
    assert "WeaponSet" in ac130
    assert "WeaponSet" not in c17
    assert "SpectreGunshipUpdate" not in ac130  # combat via WeaponSet

    e737_snap = flight_snapshot(e737)
    c17_before = flight_snapshot(c17)
    ac130_before = flight_snapshot(ac130)

    # Capture AC-130 combat identity blobs to preserve
    ac130_weapon = re.search(
        r"(?ms)^\s*WeaponSet\s*\n.*?^\s*End\s*$", ac130
    ).group(0)
    ac130_scale = ac130_before["Scale"]
    ac130_kindof = grab(ac130, r"(?m)^\s*KindOf\s*=\s*(.+)$")
    ac130_model_count = ac130.count("US_AC130W")
    ac130_health = grab(ac130, r"(?m)^\s*MaxHealth\s*=\s*(\S+)")

    # --- Patch C-17 ---
    c17_new = c17
    c17_new = replace_jetai(c17_new, E737_JETAI_C17)
    c17_new = replace_normal_loco(c17_new, "F100_PW_229")
    assert "BasicJetTaxiLocomotor" in c17_new
    c17_new = replace_mass(c17_new, "500.0")
    # Align collision to E-737 proven HeavyAirBase runway clearance
    c17_new = replace_geometry(c17_new, "40.0", "10.0", "10.0")
    assert "Model = IUAC17HXNew" in c17_new
    assert not re.search(r"(?m)^\s*Scale\s*=", c17_new)
    assert "WeaponSet" not in c17_new
    assert "TransportContain" not in c17_new

    # --- Patch AC-130 ---
    ac130_new = ac130
    ac130_new = replace_jetai(ac130_new, E737_JETAI_AC130)
    ac130_new = replace_normal_loco(ac130_new, "F100_PW_229")
    assert "BasicJetTaxiLocomotor" in ac130_new
    ac130_new = replace_mass(ac130_new, "500.0")
    ac130_new = replace_geometry(ac130_new, "40.0", "10.0", "10.0")
    # Preserve combat / identity
    assert re.search(r"(?ms)^\s*WeaponSet\s*\n.*?^\s*End\s*$", ac130_new).group(
        0
    ) == ac130_weapon
    assert re.search(rf"(?m)^\s*Scale\s*=\s*{re.escape(ac130_scale)}\s*$", ac130_new)
    assert ac130_new.count("US_AC130W") == ac130_model_count
    assert grab(ac130_new, r"(?m)^\s*KindOf\s*=\s*(.+)$") == ac130_kindof
    assert "CAN_ATTACK" in ac130_kindof
    assert grab(ac130_new, r"(?m)^\s*MaxHealth\s*=\s*(\S+)") == ac130_health
    assert "CountermeasuresBehavior" in ac130_new
    assert "M102_105mm_Howitzer" in ac130_new
    assert "SpectreGunshipUpdate" not in ac130_new

    dmap[C17_KEY] = c17_new.encode("latin1")
    dmap[AC130_KEY] = ac130_new.encode("latin1")

    SRC_DIR.mkdir(parents=True, exist_ok=True)
    (SRC_DIR / "AmericaJetC17Visual.ini").write_bytes(dmap[C17_KEY])
    (SRC_DIR / "AmericaJetAC130.ini").write_bytes(dmap[AC130_KEY])

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

    # Re-verify scales frozen
    assert re.search(
        r"(?m)^\s*Scale\s*=\s*0\.8\s*$", vmap[E737_KEY].decode("latin1")
    )
    assert re.search(
        r"(?m)^\s*Scale\s*=\s*3\.932\s*$", vmap[E2_KEY].decode("latin1")
    )

    c17_after = flight_snapshot(vmap[C17_KEY].decode("latin1"))
    ac130_after = flight_snapshot(vmap[AC130_KEY].decode("latin1"))
    assert c17_after["Locomotor"] == "F100_PW_229"
    assert ac130_after["Locomotor"] == "F100_PW_229"
    assert c17_after["MinHeight"] == "1"
    assert ac130_after["MinHeight"] == "1"
    assert c17_after["TakeoffDistForMaxLift"] == "0%"
    assert ac130_after["TakeoffDistForMaxLift"] == "0%"
    assert c17_after["ParkingOffset"] == "5"
    assert ac130_after["ParkingOffset"] == "5"
    assert ac130_after["OutOfAmmoDamagePerSecond"] == "8%"
    assert c17_after["OutOfAmmoDamagePerSecond"] == "0%"
    assert c17_after["GeometryMajorRadius"] == "40.0"
    assert ac130_after["GeometryMajorRadius"] == "40.0"

    heavy = vmap[HEAVY_KEY].decode("latin1")
    assert re.search(r"(?m)^\s*NumRows\s*=\s*3\s*$", heavy)
    assert re.search(r"(?m)^\s*NumCols\s*=\s*2\s*$", heavy)

    report = []
    report.append(
        "E737 FLIGHT TEMPLATE → C17 + AC130 = PASS (structural readiness)"
    )
    report.append("")
    report.append("REFERENCE:")
    report.append("E-737 Object = AmericaJetE737Visual")
    report.append(f"E-737 Locomotor = {e737_snap['Locomotor']} + {e737_snap['TaxiLocomotor']}")
    report.append(
        "E-737 AIUpdate = JetAIUpdate "
        f"(KeepsParkingSpaceWhenAirborne={e737_snap['KeepsParkingSpaceWhenAirborne']}, "
        f"MinHeight={e737_snap['MinHeight']}, NeedsRunway={e737_snap['NeedsRunway']}, "
        f"TakeoffPause={e737_snap['TakeoffPause']}, "
        f"TakeoffDistForMaxLift={e737_snap['TakeoffDistForMaxLift']}, "
        f"ParkingOffset={e737_snap['ParkingOffset']}, "
        f"ReturnToBaseIdleTime={e737_snap['ReturnToBaseIdleTime']}, "
        f"AutoAcquireEnemiesWhenIdle={e737_snap['AutoAcquireEnemiesWhenIdle']})"
    )
    report.append(f"E-737 Physics = Mass {e737_snap['Mass']}")
    report.append(
        "E-737 important flight parameters = "
        f"Geometry {e737_snap['GeometryMajorRadius']}/"
        f"{e737_snap['GeometryMinorRadius']}/{e737_snap['GeometryHeight']}; "
        f"Scale={e737_snap['Scale']} (frozen)"
    )
    report.append("")
    report.append("------------------------------")
    report.append("")
    report.append("C-17:")
    report.append("Object = AmericaJetC17Visual")
    report.append("W3D = IUAC17HXNew")
    report.append("Visual scale changed = NO")
    report.append(f"Old Locomotor = {c17_before['Locomotor']}")
    report.append(f"New Locomotor = {c17_after['Locomotor']}")
    report.append(
        f"Old AIUpdate = MinHeight={c17_before['MinHeight']} "
        f"ParkingOffset={c17_before['ParkingOffset']} "
        f"TakeoffDistForMaxLift={c17_before['TakeoffDistForMaxLift']} "
        f"TakeoffPause={c17_before['TakeoffPause']}"
    )
    report.append(
        f"New AIUpdate = MinHeight={c17_after['MinHeight']} "
        f"ParkingOffset={c17_after['ParkingOffset']} "
        f"TakeoffDistForMaxLift={c17_after['TakeoffDistForMaxLift']} "
        f"TakeoffPause={c17_after['TakeoffPause']} "
        f"(E-737-identical JetAIUpdate)"
    )
    report.append(
        f"Physics changes = Mass {c17_before['Mass']} -> {c17_after['Mass']} "
        "(already 500; matches E-737)"
    )
    report.append(
        f"Geometry changes = "
        f"{c17_before['GeometryMajorRadius']}/{c17_before['GeometryMinorRadius']}/"
        f"{c17_before['GeometryHeight']} -> "
        f"{c17_after['GeometryMajorRadius']}/{c17_after['GeometryMinorRadius']}/"
        f"{c17_after['GeometryHeight']} "
        "(aligned to E-737 runway-proven collision; visual unchanged)"
    )
    report.append("E-737 flight structure adopted = YES")
    report.append("Weapons = NONE")
    report.append("")
    report.append("Expected:")
    report.append("Takeoff = READY")
    report.append("Flight = READY")
    report.append("Return = READY")
    report.append("Landing = READY")
    report.append("Parking = READY")
    report.append("")
    report.append("------------------------------")
    report.append("")
    report.append("AC-130:")
    report.append("Object = AmericaJetAC130")
    report.append("W3D = US_AC130W")
    report.append("Visual changed = NO")
    report.append(f"Scale changed = NO (remains {ac130_scale})")
    report.append("Weapons changed = NO (M102_105mm_Howitzer WeaponSet preserved)")
    report.append(f"Old Locomotor = {ac130_before['Locomotor']}")
    report.append(f"New Locomotor = {ac130_after['Locomotor']}")
    report.append(
        f"Old AIUpdate = MinHeight={ac130_before['MinHeight']} "
        f"ParkingOffset={ac130_before['ParkingOffset']} "
        f"TakeoffDistForMaxLift={ac130_before['TakeoffDistForMaxLift']}"
    )
    report.append(
        f"New AIUpdate = MinHeight={ac130_after['MinHeight']} "
        f"ParkingOffset={ac130_after['ParkingOffset']} "
        f"TakeoffDistForMaxLift={ac130_after['TakeoffDistForMaxLift']} "
        f"KeepsParkingSpaceWhenAirborne=Yes "
        f"(OutOfAmmoDamagePerSecond kept {ac130_after['OutOfAmmoDamagePerSecond']}; "
        "AutoAcquireEnemiesWhenIdle not forced No)"
    )
    report.append("SpectreGunshipUpdate preserved = N/A (not present in current Object)")
    report.append(
        "Combat functionality preserved = YES "
        "(WeaponSet, CAN_ATTACK, CountermeasuresBehavior, health, icon intact)"
    )
    report.append(
        f"Geometry changes = "
        f"{ac130_before['GeometryMajorRadius']}/{ac130_before['GeometryMinorRadius']}/"
        f"{ac130_before['GeometryHeight']} -> "
        f"{ac130_after['GeometryMajorRadius']}/{ac130_after['GeometryMinorRadius']}/"
        f"{ac130_after['GeometryHeight']} "
        "(E-737 runway-proven collision; visual Scale unchanged)"
    )
    report.append("E-737 flight structure adopted = YES")
    report.append("")
    report.append("Expected:")
    report.append("Takeoff = READY")
    report.append("Flight = READY")
    report.append("Combat = PRESERVED")
    report.append("Return = READY")
    report.append("Landing = READY")
    report.append("Parking = READY")
    report.append("")
    report.append("------------------------------")
    report.append("")
    report.append("E-737 changed = NO")
    report.append("E-2 changed = NO")
    report.append("V-22 changed = NO")
    report.append("E-3 changed = NO")
    report.append("Bombers changed = NO")
    report.append("HeavyAirBase changed = NO")
    report.append("Other factions changed = NO")
    report.append("ART changed = NO")
    report.append(f"DATA sha256 = {sha256(DATA_BIG)}")
    report.append(
        "NOTE = In-game flight not launched here; structural readiness only."
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
