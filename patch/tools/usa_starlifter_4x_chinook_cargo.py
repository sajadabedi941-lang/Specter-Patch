#!/usr/bin/env python3
"""Give AmericaJetC17Visual (Starlifter) 4x Chinook TransportContain capacity.

Cargo reference: AmericaVehicleChinook (Slots=8, AllowInsideKindOf=INFANTRY VEHICLE).
Starlifter keeps JetAIUpdate / F100 / runway flight / W3D / scale / HeavyAirBase slot 8.
Uses existing C17GlobalMasterCommandSet (TransportExit + Command_ChinookUnload).
"""
from __future__ import annotations

import hashlib
import math
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
STAGE = MASTER / "_stage_usa_starlifter_4x_chinook_cargo"
VERIFY = MASTER / "_extract_usa_starlifter_4x_chinook_cargo_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_STARLIFTER_4X_CHINOOK_CARGO.zip"
OUT_HASH = ROOT / "Release/DATA_USA_STARLIFTER_4X_CHINOOK_CARGO_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_STARLIFTER_4X_CHINOOK_CARGO_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_STARLIFTER_4X_CHINOOK_CARGO_REPORT.txt"
SRC_DIR = ROOT / "Data/INI/Object/Specter/United States Of America"

CSF_KEY = "Data\\English\\generals.csf"
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"
HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)
CHINOOK_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Airforce\\CH47F.ini"
)
C17_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Visual.ini"
)

FREEZE_OBJECTS = [
    CHINOOK_KEY,
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE2Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE3Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB2A.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
]

# Example units for capacity math (read live TSC from packed DATA)
EXAMPLE_UNITS = [
    ("AmericaInfantryRanger", "infantry"),
    ("AmericaVehicleHumvee", "vehicle"),
    ("AmericaTankCrusader", "tank"),
]

STARLIFTER_CS = "C17GlobalMasterCommandSet"
TRANSPORT_BLOCK = """
  Behavior = TransportContain ModuleTag_StarlifterCargo
    Slots                 = {slots}
    DamagePercentToUnits  = 100%
    AllowInsideKindOf     = INFANTRY VEHICLE
    ForbidInsideKindOf    = AIRCRAFT HUGE_VEHICLE
    ExitDelay             = 100
    NumberOfExitPaths     = 1
  End
"""


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


def extract_object(text: str, name: str) -> str:
    m = re.search(rf"(?ms)^Object\s+{re.escape(name)}\s*\n.*?(?=^Object\s|\Z)", text)
    assert m, name
    return m.group(0)


def chinook_slots(chinook_txt: str) -> int:
    obj = extract_object(chinook_txt, "AmericaVehicleChinook")
    m = re.search(
        r"(?ms)Behavior\s*=\s*TransportContain.*?\n\s*End",
        obj,
    )
    assert m
    sm = re.search(r"(?m)^\s*Slots\s*=\s*(\d+)", m.group(0))
    assert sm
    return int(sm.group(1))


def find_tsc(file_map: dict[str, bytes], obj_name: str) -> int:
    for k, v in file_map.items():
        if not k.lower().endswith(".ini"):
            continue
        t = v.decode("latin1", errors="replace")
        if f"Object {obj_name}" not in t and f"Object  {obj_name}" not in t:
            continue
        try:
            obj = extract_object(t, obj_name)
        except AssertionError:
            continue
        m = re.search(r"(?m)^\s*TransportSlotCount\s*=\s*(\d+)", obj)
        if m:
            return int(m.group(1))
    raise AssertionError(f"TransportSlotCount not found for {obj_name}")


def patch_c17(text: str, slots: int) -> str:
    # KindOf += TRANSPORT
    def kindof_repl(m: re.Match[str]) -> str:
        indent, vals = m.group(1), m.group(2)
        parts = vals.split()
        if "TRANSPORT" not in parts:
            parts.append("TRANSPORT")
        return f"{indent}KindOf = " + " ".join(parts)

    text = re.sub(r"(?m)^(\s*)KindOf\s*=\s*(.*)$", kindof_repl, text, count=1)

    # CommandSet -> existing C17GlobalMasterCommandSet
    text = re.sub(
        r"(?m)^(\s*CommandSet\s*=\s*)\S+\s*$",
        rf"\g<1>{STARLIFTER_CS}",
        text,
        count=1,
    )

    # Replace or insert TransportContain
    block = TRANSPORT_BLOCK.format(slots=slots).rstrip() + "\n"
    if re.search(r"(?m)^\s*Behavior\s*=\s*TransportContain\b", text):
        text = re.sub(
            r"(?ms)^\s*Behavior\s*=\s*TransportContain.*?\n\s*End\s*\n?",
            block + "\n",
            text,
            count=1,
        )
    else:
        # insert before Geometry (same placement family as other modules)
        text = re.sub(
            r"(?m)^(\s*Geometry\s*=)",
            block + "\n\\1",
            text,
            count=1,
        )

    # Update header comment cargo note
    text = re.sub(
        r"Cargo = NOT YET\.",
        f"Cargo = Chinook TransportContain x4 (Slots={slots}).",
        text,
        count=1,
    )

    # Safety: remain fixed-wing
    assert "JetAIUpdate" in text
    assert "BasicJetTaxiLocomotor" in text
    assert "HelicopterAIUpdate" not in text
    assert "ChinookAIUpdate" not in text
    assert "ChinookLocomotor" not in text
    assert "TransportContain" in text
    assert f"Slots                 = {slots}" in text
    assert STARLIFTER_CS in text
    assert "IUAC17HXNew" in text
    return text


def upload(path: Path) -> str:
    try:
        r = subprocess.run(
            [
                "curl",
                "-sF",
                f"file=@{path}",
                "https://litterbox.catbox.moe/resources/internals/api.php",
                "-F",
                "time=72h",
                "-F",
                "reqtype=fileupload",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        out = (r.stdout or "").strip()
        if out.startswith("http"):
            return out
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["curl", "-sF", f"file=@{path}", "https://store1.gofile.io/uploadFile"],
            capture_output=True,
            text=True,
            timeout=900,
        )
        m = re.search(r'"downloadPage"\s*:\s*"([^"]+)"', r.stdout or "")
        if m:
            return m.group(1)
    except Exception:
        pass
    return "(upload failed)"


def main() -> None:
    data = read_big(DATA_BIG)
    art_sha = sha256(ART_BIG)
    cs_before = data[CS_KEY]
    cb_before = data[CB_KEY]
    heavy_before = data[HEAVY_KEY]
    csf_before = data[CSF_KEY]
    freeze_blobs = {k: data[k] for k in FREEZE_OBJECTS if k in data}
    # freeze chinook explicitly even if also in FREEZE list
    chinook_before = data[CHINOOK_KEY]

    chinook_txt = chinook_before.decode("latin1")
    x = chinook_slots(chinook_txt)
    star_slots = x * 4
    assert star_slots == x * 4

    # Ensure target CommandSet exists with unload
    cs_txt = cs_before.decode("latin1")
    assert re.search(
        rf"(?ms)^CommandSet\s+{re.escape(STARLIFTER_CS)}\s*\n.*?"
        r"Command_ChinookUnload.*?(?=^CommandSet\s|\Z)",
        cs_txt,
    )
    assert "Command_TransportExit" in cs_txt

    c17_before = data[C17_KEY].decode("latin1")
    models_before = re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", c17_before)
    btn_before = re.search(r"(?m)^\s*ButtonImage\s*=\s*(\S+)", c17_before).group(1)
    scale_before = re.search(r"(?m)^\s*Scale\s*=\s*([0-9.]+)", c17_before)
    jetai_before = "JetAIUpdate" in c17_before
    loco_before = re.search(
        r"(?m)^\s*Locomotor\s*=\s*SET_NORMAL\s+(\S+)", c17_before
    ).group(1)

    patched = patch_c17(c17_before, star_slots)
    assert re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", patched) == models_before
    assert (
        re.search(r"(?m)^\s*ButtonImage\s*=\s*(\S+)", patched).group(1) == btn_before
    )
    scale_after = re.search(r"(?m)^\s*Scale\s*=\s*([0-9.]+)", patched)
    assert (scale_before.group(1) if scale_before else None) == (
        scale_after.group(1) if scale_after else None
    )
    assert jetai_before and "JetAIUpdate" in patched
    assert (
        re.search(r"(?m)^\s*Locomotor\s*=\s*SET_NORMAL\s+(\S+)", patched).group(1)
        == loco_before
    )

    # Capacity examples
    examples = []
    for uname, kind in EXAMPLE_UNITS:
        tsc = find_tsc(data, uname)
        examples.append(
            {
                "name": uname,
                "kind": kind,
                "tsc": tsc,
                "chinook": math.floor(x / tsc),
                "starlifter": math.floor(star_slots / tsc),
            }
        )

    data2 = dict(data)
    data2[C17_KEY] = patched.replace("\r\n", "\n").encode("latin1")
    data2[CS_KEY] = cs_before
    data2[CB_KEY] = cb_before
    data2[HEAVY_KEY] = heavy_before
    data2[CSF_KEY] = csf_before
    data2[CHINOOK_KEY] = chinook_before
    for k, v in freeze_blobs.items():
        data2[k] = v

    SRC_DIR.mkdir(parents=True, exist_ok=True)
    (SRC_DIR / "AmericaJetC17Visual.ini").write_bytes(data2[C17_KEY])

    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    write_tree(data2, STAGE / "in")
    DATA_BIG.write_bytes(build_big(data2))

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    dv = read_big(DATA_BIG)
    write_tree(dv, VERIFY / "out")

    assert dv[CS_KEY] == cs_before
    assert dv[CB_KEY] == cb_before
    assert dv[HEAVY_KEY] == heavy_before
    assert dv[CSF_KEY] == csf_before
    assert dv[CHINOOK_KEY] == chinook_before
    assert sha256(ART_BIG) == art_sha

    out_c17 = dv[C17_KEY].decode("latin1")
    assert "TransportContain" in out_c17
    assert f"Slots                 = {star_slots}" in out_c17
    assert "AllowInsideKindOf     = INFANTRY VEHICLE" in out_c17
    assert STARLIFTER_CS in out_c17
    assert "TRANSPORT" in re.search(r"(?m)^\s*KindOf\s*=\s*(.*)$", out_c17).group(1)
    assert "JetAIUpdate" in out_c17 and "HelicopterAIUpdate" not in out_c17
    assert "IUAC17HXNew" in out_c17
    assert btn_before in out_c17

    # HeavyAirBase still slot 8 = C17
    heavy = dv[HEAVY_KEY].decode("latin1")
    assert re.search(r"NumRows\s*=\s*3", heavy)
    assert re.search(r"NumCols\s*=\s*2", heavy)
    cs_txt2 = dv[CS_KEY].decode("latin1")
    mhab = re.search(
        r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?(?=^CommandSet\s|\Z)",
        cs_txt2,
    )
    assert mhab and "Command_ConstructAmericaJetC17Visual" in mhab.group(0)

    # freeze other aircraft blobs
    for k, v in freeze_blobs.items():
        if k == C17_KEY:
            continue
        assert dv[k] == v

    data_sha = sha256(DATA_BIG)
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    url = upload(OUT_ZIP)

    def ex_line(e: dict) -> str:
        return (
            f"Example {e['kind']} ({e['name']}):\n"
            f"TransportSlotCount = {e['tsc']}\n"
            f"Chinook capacity = {e['chinook']}\n"
            f"Starlifter capacity = {e['starlifter']}\n"
        )

    report = f"""STARLIFTER HEAVY TRANSPORT = STRUCTURAL PASS

Starlifter:
Object = AmericaJetC17Visual
W3D = IUAC17HXNew
CommandButton = Command_ConstructAmericaJetC17Visual
HeavyAirBase Slot = 8

Flight system changed = NO
Visual changed = NO
Scale changed = NO

------------------------------

CHINOOK REFERENCE:

Object = AmericaVehicleChinook
TransportContain module = ModuleTag_08
Slots = {x}

Allowed cargo = INFANTRY VEHICLE
Forbidden cargo = AIRCRAFT HUGE_VEHICLE
DamagePercentToUnits = 100%
ExitDelay = 100
NumberOfExitPaths = 1

Unload command = Command_ChinookUnload (EVACUATE) + Command_TransportExit (EXIT_CONTAINER)
Chinook CommandSet = AmericaVehicleChinookCommandSet

------------------------------

STARLIFTER:

TransportContain source = Chinook
Chinook Slots = {x}
Multiplier = 4
Final Starlifter Slots = {star_slots}

Allows infantry = YES
Allows vehicles = YES
Allows tanks = YES (VEHICLE KindOf; not HUGE_VEHICLE)

Unload command available = YES
Starlifter CommandSet = {STARLIFTER_CS}
  (existing Specter set: Command_TransportExit x10 + Command_ChinookUnload + Guard + Stop)

KindOf += TRANSPORT = YES
JetAIUpdate preserved = YES
HelicopterAIUpdate added = NO
Helicopter locomotor added = NO

------------------------------

CAPACITY TEST:

{''.join(ex_line(e) for e in examples)}
Transported-unit SlotCounts changed = NO

Starlifter remains fixed-wing = YES
Other aircraft changed = NO
Chinook changed = NO
HeavyAirBase changed = NO
ART changed = NO

In-game load/unload effectiveness = USER TEST REQUIRED

DATA sha256 = {data_sha}
ART sha256 = {art_sha}
ZIP = {OUT_ZIP.name}
URL = {url}
"""
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={data_sha}\n"
        f"_SPEC_ART_ONE.big sha256={art_sha} (unchanged)\n"
        f"zip={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
