#!/usr/bin/env python3
"""Russia Tu-95 only: donor ART visuals + B-52 gameplay references on healthy art_data baseline.

Baseline: patch/Release/SPECTER_MASTER/_SPEC_{DATA,ART}_ONE.big
  (extracted from uploaded art_data.part01-22.rar)

Does NOT modify USA B-52 Object / Weapon / OCL / CommandButton.
Does NOT touch Tu-160 / An-225 / A-50 / An-124 / IL76 / other factions.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
MASTER = PATCH / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
OUT = PATCH / "Release/SPECTER_MASTER_RUSSIA_TU95"
EXPECTED_DATA = "c7062a4ab12677a2e797d1a98324b14fcefd0a0cbdbbcec0a2e527553e377c05"
EXPECTED_ART = "bb5d15325e227bad247450dc379bbf85b8bbd620beacc9b2f8db89976b1989d7"

AF = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce"
CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
CSF_KEY = r"Data\English\generals.csf"

ART_REL = [
    "Art/W3D/CWCruTu95.W3D",
    "Art/W3D/CWCruTu95_d.W3D",
    "Art/W3D/CWCruTu95_k.W3D",
    "Art/Textures/CWCruTu95.dds",
    "Art/Textures/CWCruTu95_d.dds",
    "Art/Textures/CWCruTu95_k.dds",
    "Art/Textures/CWCruTU95.dds",
    "Art/Textures/CWCruTU95_d.dds",
    "Art/Textures/CWCruTU95_k.dds",
    "Art/Textures/CWCgenPropellor.dds",
    "Art/Textures/CWCgenPropellor.tga",
    "Art/Textures/CWCgenReflective.dds",
    "Art/Textures/CWCgenReflective.tga",
    "Art/Textures/Tu95.tga",
    "Art/Textures/Tu95TB.tga",
]

OBJ_PATH = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/RussiaJetTu95.ini"
)
MAP_PATH = PATCH / "Data/INI/MappedImages/HandCreated/Russia_Tu95_Images.INI"
STR_PATH = PATCH / "Data/English/SPECTER_RUSSIA_TU95_Strings.txt"

TU95_CS = """CommandSet RussiaJetTu95CommandSet
  1  = Command_AmericaB52CarpetStrike
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
"""

TU95_BTN = """CommandButton Command_ConstructRussiaJetTu95
  Command       = UNIT_BUILD
  Object        = RussiaJetTu95
  TextLabel     = CONTROLBAR:ConstructRussiaJetTu95
  ButtonImage   = Tu95
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetTu95
End
"""

CSF_STRINGS = {
    "OBJECT:RussiaJetTu95": "Tu-95 Bear",
    "CONTROLBAR:ConstructRussiaJetTu95": "Tu-95 Bear",
    "CONTROLBAR:ToolTipRussiaJetTu95": "Build Tu-95 strategic bomber (B-52 bomb system)",
}


def sha256(p: Path | bytes) -> str:
    return hashlib.sha256(p if isinstance(p, bytes) else Path(p).read_bytes()).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF", path
    n = struct.unpack(">I", data[8:12])[0]
    off = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        eo, sz = struct.unpack(">II", data[off : off + 8])
        i = off + 8
        while data[i]:
            i += 1
        name = data[off + 8 : i].decode("latin1")
        out[name] = data[eo : eo + sz]
        off = i + 1
    return out


def write_big(path: Path, entries: dict[str, bytes]) -> None:
    # Stable order: existing-ish alphabetical for determinism
    names = sorted(entries.keys(), key=lambda s: s.lower())
    # Header + TOC size estimate
    toc = bytearray()
    payload = bytearray()
    # Precompute header size: 16 + sum(8+len(name)+1)
    header_size = 16 + sum(8 + len(n.encode("latin1")) + 1 for n in names)
    # Align payloads after header
    cursor = header_size
    for name in names:
        blob = entries[name]
        toc += struct.pack(">II", cursor, len(blob))
        nb = name.encode("latin1") + b"\x00"
        toc += nb
        payload += blob
        cursor += len(blob)
    file_size = 16 + len(toc) + len(payload)
    header = b"BIGF" + struct.pack(">III", file_size, len(names), 16 + len(toc))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + toc + payload)


def art_key(rel: str) -> str:
    return rel.replace("/", "\\")


def upsert_commandset(cs: str, name: str, block: str) -> str:
    pat = re.compile(rf"(?ms)^CommandSet\s+{re.escape(name)}\s*\n.*?^End\s*\n")
    if pat.search(cs):
        return pat.sub(block.rstrip() + "\n\n", cs, count=1)
    return cs.rstrip() + "\n\n" + block.rstrip() + "\n"


def upsert_commandbutton(cb: str, name: str, block: str) -> str:
    pat = re.compile(rf"(?ms)^CommandButton\s+{re.escape(name)}\s*\n.*?^End\s*\n")
    if pat.search(cb):
        return pat.sub(block.rstrip() + "\n\n", cb, count=1)
    return cb.rstrip() + "\n\n" + block.rstrip() + "\n"


def patch_heavy_cs(cs: str) -> str:
    """Add Tu-95 construct to Russia Heavy AirBase without removing existing units."""
    m = re.search(r"(?ms)^CommandSet\s+Russia_HeavyAirBaseCommandSet\s*\n(.*?)^^End\s*$", cs)
    if not m:
        raise SystemExit("Russia_HeavyAirBaseCommandSet not found")
    body = m.group(1)
    if "Command_ConstructRussiaJetTu95" in body:
        return cs
    # Insert as slot 6 if free, else next free 1..12
    used = {int(x) for x in re.findall(r"(?m)^\s*(\d+)\s*=", body)}
    slot = 6 if 6 not in used else next(i for i in range(1, 15) if i not in used)
    lines = [ln for ln in body.splitlines() if ln.strip()]
    lines.append(f"  {slot} = Command_ConstructRussiaJetTu95")
    # Keep rally/sell at 13/14 if present; sort numeric slots
    def sk(ln: str) -> tuple[int, str]:
        mm = re.match(r"\s*(\d+)\s*=", ln)
        return (int(mm.group(1)), ln) if mm else (999, ln)

    lines = sorted(lines, key=sk)
    new_block = "CommandSet Russia_HeavyAirBaseCommandSet\n" + "\n".join(lines) + "\nEnd\n"
    return re.sub(
        r"(?ms)^CommandSet\s+Russia_HeavyAirBaseCommandSet\s*\n.*?^End\s*\n",
        new_block + "\n",
        cs,
        count=1,
    )


def encode_csf_string(text: str) -> bytes:
    out = bytearray()
    for ch in text:
        out += struct.pack("<H", ord(ch) ^ 0xFFFF)
    return bytes(out)


def upsert_csf(csf: bytes, pairs: dict[str, str]) -> bytes:
    data = bytearray(csf)
    assert data[:4] == b" FSC"
    num_labels = struct.unpack_from("<I", data, 8)[0]
    num_strings = struct.unpack_from("<I", data, 12)[0]
    # Build set of existing labels (ASCII search)
    existing = set()
    for key in pairs:
        if data.find(key.encode("ascii")) >= 0:
            existing.add(key)
    add = {k: v for k, v in pairs.items() if k not in existing}
    if not add:
        return bytes(data)
    for label, value in add.items():
        lb = label.encode("ascii")
        sb = encode_csf_string(value)
        entry = (
            b" LBL"
            + struct.pack("<I", 1)
            + struct.pack("<I", len(lb))
            + lb
            + b" RTS"
            + struct.pack("<I", len(value))
            + sb
        )
        data += entry
        num_labels += 1
        num_strings += 1
    struct.pack_into("<I", data, 8, num_labels)
    struct.pack_into("<I", data, 12, num_strings)
    return bytes(data)


def extract_object(text: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^Object\s+{re.escape(name)}\s*\n.*?^End\s*$", text)
    return m.group(0) if m else None


def main() -> None:
    assert DATA_BIG.exists() and ART_BIG.exists()
    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)
    assert data_sha == EXPECTED_DATA, f"DATA baseline mismatch {data_sha}"
    assert art_sha == EXPECTED_ART, f"ART baseline mismatch {art_sha}"

    data_entries = read_big(DATA_BIG)
    art_entries = read_big(ART_BIG)

    # Freeze USA B-52 chain hashes before edits
    usa_sys_key = r"Data\INI\Object\Specter\United States Of America\USA_System.ini"
    weapon_key = r"Data\INI\Weapon.ini"
    ocl_key = r"Data\INI\ObjectCreationList.ini"
    b52_before = extract_object(data_entries[usa_sys_key].decode("latin1", "replace"), "AmericaJetB52H")
    assert b52_before and "AmericaB52FifteenBombLineWeapon" in b52_before
    weapon_sha = sha256(data_entries[weapon_key])
    ocl_sha = sha256(data_entries[ocl_key])
    cb_before = data_entries[CB_KEY]
    assert b"Command_AmericaB52CarpetStrike" in cb_before
    carpet_btn = re.search(
        r"(?ms)^CommandButton\s+Command_AmericaB52CarpetStrike\s*\n.*?^End\s*$",
        cb_before.decode("latin1", "replace"),
    )
    assert carpet_btn, "B-52 carpet FIRE_WEAPON button missing in baseline"
    carpet_btn_text = carpet_btn.group(0)

    # --- ART merge (Tu-95 family only) ---
    missing_art = []
    for rel in ART_REL:
        src = PATCH / rel
        if not src.exists():
            missing_art.append(rel)
            continue
        art_entries[art_key(rel)] = src.read_bytes()
    assert not missing_art, f"Missing donor ART: {missing_art}"

    # --- DATA: Object ---
    obj_text = OBJ_PATH.read_text(encoding="utf-8")
    assert "AmericaB52FifteenBombLineWeapon" in obj_text
    assert "Object RussiaJetTu95" in obj_text
    data_entries[rf"{AF}\RussiaJetTu95.ini"] = obj_text.encode("utf-8")

    # MappedImage + strings txt
    data_entries[r"Data\INI\MappedImages\HandCreated\Russia_Tu95_Images.INI"] = MAP_PATH.read_bytes()
    data_entries[r"Data\English\SPECTER_RUSSIA_TU95_Strings.txt"] = STR_PATH.read_bytes()

    # CommandSet / CommandButton (Russia only)
    cs = data_entries[CS_KEY].decode("latin1", "replace")
    cb = data_entries[CB_KEY].decode("latin1", "replace")
    cs = upsert_commandset(cs, "RussiaJetTu95CommandSet", TU95_CS)
    cs = patch_heavy_cs(cs)
    cb = upsert_commandbutton(cb, "Command_ConstructRussiaJetTu95", TU95_BTN)
    # Ensure USA carpet button unchanged
    assert carpet_btn_text in cb
    data_entries[CS_KEY] = cs.encode("latin1", "replace")
    data_entries[CB_KEY] = cb.encode("latin1", "replace")

    # CSF strings
    data_entries[CSF_KEY] = upsert_csf(data_entries[CSF_KEY], CSF_STRINGS)

    # --- Write BIGs ---
    OUT.mkdir(parents=True, exist_ok=True)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    write_big(out_data, data_entries)
    write_big(out_art, art_entries)

    # --- Verify ---
    vdata = read_big(out_data)
    vart = read_big(out_art)
    checks: list[tuple[str, bool]] = []

    def ok(label: str, cond: bool) -> None:
        checks.append((label, cond))
        print(("PASS" if cond else "FAIL"), label)

    tu95 = vdata[rf"{AF}\RussiaJetTu95.ini"].decode("utf-8", "replace")
    ok("Tu-95 Object exists", "Object RussiaJetTu95" in tu95)
    ok("Tu-95 B52 weapon", "AmericaB52FifteenBombLineWeapon" in tu95)
    ok("Tu-95 CS", "RussiaJetTu95CommandSet" in tu95)
    ok("Tu-95 Side Russia", "Side                = Russia" in tu95 or "Side = Russia" in tu95)
    ok("Tu-95 visual CWCruTu95", "Model = CWCruTu95" in tu95)
    ok("Tu-95 damaged model", "CWCruTu95_d" in tu95)
    ok("Tu-95 rubble model", "CWCruTu95_k" in tu95)

    baseline_cs = read_big(DATA_BIG)[CS_KEY].decode("latin1", "replace")
    b52_cs_before = re.search(
        r"(?ms)^CommandSet\s+AmericaB52HCommandSet\s*\n.*?^End\s*$", baseline_cs
    ).group(0)
    vcs = vdata[CS_KEY].decode("latin1", "replace")
    ok("Heavy has Tu-95", "Command_ConstructRussiaJetTu95" in vcs)
    ok("Tu95 CommandSet carpet", "Command_AmericaB52CarpetStrike" in vcs)
    ok(
        "B52 CS unchanged",
        re.search(r"(?ms)^CommandSet\s+AmericaB52HCommandSet\s*\n.*?^End\s*$", vcs).group(0)
        == b52_cs_before,
    )

    # B52 object / weapon / ocl / carpet button unchanged vs baseline
    b52_after = extract_object(vdata[usa_sys_key].decode("latin1", "replace"), "AmericaJetB52H")
    ok("B52 Object unchanged", b52_after == b52_before)
    ok("Weapon.ini unchanged", sha256(vdata[weapon_key]) == weapon_sha)
    ok("OCL.ini unchanged", sha256(vdata[ocl_key]) == ocl_sha)
    vcb = vdata[CB_KEY].decode("latin1", "replace")
    mbtn = re.search(
        r"(?ms)^CommandButton\s+Command_AmericaB52CarpetStrike\s*\n.*?^End\s*$", vcb
    )
    ok("B52 CarpetStrike button unchanged", bool(mbtn) and mbtn.group(0) == carpet_btn_text)
    ok("Construct button present", "Command_ConstructRussiaJetTu95" in vcb)

    # No other Russia expansion aircraft Objects introduced
    for other in (
        "RussiaJetTU160Clean",
        "RussiaJetAn124Visual",
        "RussiaJetAn225Visual",
        "RussiaJetA50Visual",
        "RussiaJetAvionIL76Visual",
        "RussiaJetCargoIL76Visual",
        "RussiaJetTu95Visual",
    ):
        ok(f"no {other}", rf"{AF}\{other}.ini" not in vdata)

    for rel in ART_REL:
        ok(f"ART {art_key(rel)}", art_key(rel) in vart)

    # Weapon chain presence (reuse)
    w = vdata[weapon_key].decode("latin1", "replace")
    o = vdata[ocl_key].decode("latin1", "replace")
    ok("Weapon AmericaB52FifteenBombLineWeapon", "Weapon AmericaB52FifteenBombLineWeapon" in w)
    ok("OCL_AmericaB52FifteenBombLine", "ObjectCreationList OCL_AmericaB52FifteenBombLine" in o)
    ok("Bomb AmericaB52TenBombLineBomb", b"AmericaB52TenBombLineBomb" in vdata[
        r"Data\INI\Object\Specter\United States Of America\USA_WeaponObjects.ini"
    ])

    failed = [l for l, c in checks if not c]
    assert not failed, f"Verification failed: {failed}"

    zip_path = OUT / "Russia_Tu95_Final.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")

    dsha = sha256(out_data)
    asha = sha256(out_art)
    zsha = sha256(zip_path)

    report = f"""TU-95 INTEGRATION = READY FOR USER TEST

1. BASELINE
- Source: uploaded art_data.part01-22.rar
- DATA SHA256 (pre-change) = {EXPECTED_DATA}
- ART  SHA256 (pre-change) = {EXPECTED_ART}

2. OBJECT
- Object ID = RussiaJetTu95
- Side = Russia
- Heavy AirBase = Yes (Command_ConstructRussiaJetTu95)

3. GAMEPLAY DONOR
- AmericaJetB52H architecture (JetAI / locomotor / death / vision / build stats)
- Weapon PRIMARY = AmericaB52FifteenBombLineWeapon (FireOCL -> OCL_AmericaB52FifteenBombLine)
- Bomb object = AmericaB52TenBombLineBomb (unchanged USA)
- Detonation = AmericaB52LineBombDetonation (unchanged USA)
- Fire button = Command_AmericaB52CarpetStrike (FIRE_WEAPON PRIMARY) reused by reference

4. USA UNCHANGED
- AmericaJetB52H Object unchanged
- Weapon.ini / ObjectCreationList.ini unchanged
- Command_AmericaB52CarpetStrike unchanged

5. DONOR ART (visual only)
{chr(10).join('- ' + art_key(r) for r in ART_REL)}

6. MODIFIED DATA KEYS
- {AF}\\RussiaJetTu95.ini (new)
- Data\\INI\\CommandSet.ini (RussiaJetTu95CommandSet + Heavy slot)
- Data\\INI\\CommandButton.ini (ConstructRussiaJetTu95 only)
- Data\\INI\\MappedImages\\HandCreated\\Russia_Tu95_Images.INI (new)
- Data\\English\\SPECTER_RUSSIA_TU95_Strings.txt (new)
- Data\\English\\generals.csf (Tu-95 labels appended)

7. HASHES
_SPEC_DATA_ONE.big SHA256 = {dsha}
_SPEC_ART_ONE.big  SHA256 = {asha}
Russia_Tu95_Final.zip SHA256 = {zsha}
ZIP = {zip_path}

Only Tu-95 added/changed. No in-game PASS claimed.
"""
    (OUT / "REPORT.txt").write_text(report, encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big={dsha}\n_SPEC_ART_ONE.big={asha}\nZIP={zsha}\n",
        encoding="utf-8",
    )
    (PATCH / "Release/DATA_RUSSIA_TU95_HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big={dsha}\n_SPEC_ART_ONE.big={asha}\nZIP={zsha}\n",
        encoding="utf-8",
    )
    print(report)


if __name__ == "__main__":
    main()
