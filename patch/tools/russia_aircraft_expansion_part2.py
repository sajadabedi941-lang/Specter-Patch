#!/usr/bin/env python3
"""Russia Aircraft Expansion Part 2 on the successful Tu-95 runtime.

Input: patch/Release/SPECTER_MASTER_RUSSIA_TU95/_SPEC_{DATA,ART}_ONE.big
  (Tu-95 on uploaded art_data healthy baseline — Tu-95 must remain unchanged)

Adds: Tu-160, An-225, A-50, An-124, avionIL76, cargoIL76
Donor ART visual only. USA B-2A / E-3 / E-737 / Chinook unchanged.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
IN_DIR = PATCH / "Release/SPECTER_MASTER_RUSSIA_TU95"
DATA_BIG = IN_DIR / "_SPEC_DATA_ONE.big"
ART_BIG = IN_DIR / "_SPEC_ART_ONE.big"
OUT = PATCH / "Release/SPECTER_MASTER_RUSSIA_PART2"

EXPECTED_DATA = "5fa4b2b3e19e6947cb07c1bb685ac43470f2dd524cba9cc25897d3acacd4fd92"
EXPECTED_ART = "74b6c949240ebc38c71273edc90a7a7e4512c22ea36a544e953a1e834d7b6834"

AF = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce"
CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
CSF_KEY = r"Data\English\generals.csf"
AF_DIR = PATCH / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"

ART_REL = [
    "Art/W3D/LSFRussiaTu160.W3D",
    "Art/W3D/LSFRussiaTu160d.W3D",
    "Art/W3D/LSFRussiaTu160k.W3D",
    "Art/Textures/LSFRussiaTU160.dds",
    "Art/Textures/LSFRussiaTU160d.dds",
    "Art/Textures/LSFRussiaTU160k.dds",
    "Art/Textures/TU-160.tga",
    "Art/Textures/TU160TB.tga",
    "Art/W3D/A_AN225_100.W3D",
    "Art/W3D/A_E-3_100.W3D",
    "Art/Textures/A_AN225_100.tga",
    "Art/Textures/A_E-3_100.tga",
    "Art/Textures/RussiaAN225.tga",
    "Art/Textures/RussiaAN225TB.tga",
    "Art/W3D/CWCruA50.W3D",
    "Art/Textures/CWCruA50.dds",
    "Art/Textures/CWCruA50.tga",
    "Art/Textures/RussiaA50.tga",
    "Art/Textures/RussiaA50TB.tga",
    "Art/W3D/CWCruAn124.W3D",
    "Art/W3D/CWCruAn124_b.W3D",
    "Art/Textures/CWCruAn124.dds",
    "Art/Textures/CWCruAn124Nav.dds",
    "Art/Textures/CWCruAn124NavL.dds",
    "Art/Textures/CWCruAn124NavR.dds",
    "Art/Textures/AN124.tga",
    "Art/Textures/AN124TB.tga",
    "Art/W3D/Yier76.W3D",
    "Art/Textures/yier76.tga",
    "Art/Textures/yier76TB.tga",
    "Art/Textures/yujing1.dds",
    "Art/Textures/yujing1.tga",
    "Art/W3D/LSFRussiaYR76.W3D",
    "Art/W3D/LSFRussiaYR76d.W3D",
    "Art/W3D/LSFRussiaYR76k.W3D",
    "Art/Textures/LSFRussiaYR76.tga",
    "Art/Textures/LSFRussiaYR76d.tga",
    "Art/Textures/LSFRussiaYR76k.tga",
    "Art/Textures/CargoIL76Russia.tga",
    "Art/Textures/CargoIL76RussiaTB.tga",
]

OBJECTS = {
    "RussiaJetTU160": AF_DIR / "RussiaJetTU160.ini",
    "RussiaJetAn225": AF_DIR / "RussiaJetAn225.ini",
    "RussiaJetA50": AF_DIR / "RussiaJetA50.ini",
    "RussiaJetAn124": AF_DIR / "RussiaJetAn124.ini",
    "RussiaJetAvionIL76": AF_DIR / "RussiaJetAvionIL76.ini",
    "RussiaJetCargoIL76": AF_DIR / "RussiaJetCargoIL76.ini",
}

NEW_CS = {
    "RussiaJetAn225CommandSet": """CommandSet RussiaJetAn225CommandSet
  1  = Command_E3SARScan
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
""",
    "RussiaJetA50CommandSet": """CommandSet RussiaJetA50CommandSet
  1  = Command_E737SARScan
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
""",
}

NEW_BTNS = {
    "Command_ConstructRussiaJetTU160": """CommandButton Command_ConstructRussiaJetTU160
  Command       = UNIT_BUILD
  Object        = RussiaJetTU160
  TextLabel     = CONTROLBAR:ConstructRussiaJetTU160
  ButtonImage   = TU160
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetTU160
End
""",
    "Command_ConstructRussiaJetAn225": """CommandButton Command_ConstructRussiaJetAn225
  Command       = UNIT_BUILD
  Object        = RussiaJetAn225
  TextLabel     = CONTROLBAR:ConstructRussiaJetAn225
  ButtonImage   = RussiaAN225
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetAn225
End
""",
    "Command_ConstructRussiaJetA50": """CommandButton Command_ConstructRussiaJetA50
  Command       = UNIT_BUILD
  Object        = RussiaJetA50
  TextLabel     = CONTROLBAR:ConstructRussiaJetA50
  ButtonImage   = RussiaA50
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetA50
End
""",
    "Command_ConstructRussiaJetAn124": """CommandButton Command_ConstructRussiaJetAn124
  Command       = UNIT_BUILD
  Object        = RussiaJetAn124
  TextLabel     = CONTROLBAR:ConstructRussiaJetAn124
  ButtonImage   = AN124
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetAn124
End
""",
    "Command_ConstructRussiaJetAvionIL76": """CommandButton Command_ConstructRussiaJetAvionIL76
  Command       = UNIT_BUILD
  Object        = RussiaJetAvionIL76
  TextLabel     = CONTROLBAR:ConstructRussiaJetAvionIL76
  ButtonImage   = yier76
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetAvionIL76
End
""",
    "Command_ConstructRussiaJetCargoIL76": """CommandButton Command_ConstructRussiaJetCargoIL76
  Command       = UNIT_BUILD
  Object        = RussiaJetCargoIL76
  TextLabel     = CONTROLBAR:ConstructRussiaJetCargoIL76
  ButtonImage   = CargoIL76Russia
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetCargoIL76
End
""",
}

HEAVY_ADD = [
    (7, "Command_ConstructRussiaJetTU160"),
    (8, "Command_ConstructRussiaJetAn225"),
    (9, "Command_ConstructRussiaJetA50"),
    (10, "Command_ConstructRussiaJetAn124"),
    (11, "Command_ConstructRussiaJetAvionIL76"),
    (12, "Command_ConstructRussiaJetCargoIL76"),
]

CSF_STRINGS = {
    "OBJECT:RussiaJetTU160": "Tu-160 Blackjack",
    "CONTROLBAR:ConstructRussiaJetTU160": "Tu-160 Blackjack",
    "CONTROLBAR:ToolTipRussiaJetTU160": "Build Tu-160 (B-2A bomb system)",
    "OBJECT:RussiaJetAn225": "An-225 Mriya",
    "CONTROLBAR:ConstructRussiaJetAn225": "An-225 Mriya",
    "CONTROLBAR:ToolTipRussiaJetAn225": "Build An-225 (E-3 SAR scan)",
    "OBJECT:RussiaJetA50": "A-50 Mainstay",
    "CONTROLBAR:ConstructRussiaJetA50": "A-50 Mainstay",
    "CONTROLBAR:ToolTipRussiaJetA50": "Build A-50 (E-737 SAR scan)",
    "OBJECT:RussiaJetAn124": "An-124 Ruslan",
    "CONTROLBAR:ConstructRussiaJetAn124": "An-124 Ruslan",
    "CONTROLBAR:ToolTipRussiaJetAn124": "Build An-124 transport (8x Chinook capacity)",
    "OBJECT:RussiaJetAvionIL76": "IL-76",
    "CONTROLBAR:ConstructRussiaJetAvionIL76": "IL-76",
    "CONTROLBAR:ToolTipRussiaJetAvionIL76": "Build IL-76 transport (4x Chinook capacity)",
    "OBJECT:RussiaJetCargoIL76": "IL-76 Cargo",
    "CONTROLBAR:ConstructRussiaJetCargoIL76": "IL-76 Cargo",
    "CONTROLBAR:ToolTipRussiaJetCargoIL76": "Build IL-76 cargo transport (6x Chinook capacity)",
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
    names = sorted(entries.keys(), key=lambda s: s.lower())
    toc = bytearray()
    payload = bytearray()
    header_size = 16 + sum(8 + len(n.encode("latin1")) + 1 for n in names)
    cursor = header_size
    for name in names:
        blob = entries[name]
        toc += struct.pack(">II", cursor, len(blob))
        toc += name.encode("latin1") + b"\x00"
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
    m = re.search(r"(?ms)^CommandSet\s+Russia_HeavyAirBaseCommandSet\s*\n(.*?)^^End\s*$", cs)
    if not m:
        raise SystemExit("Russia_HeavyAirBaseCommandSet not found")
    body = m.group(1)
    if "Command_ConstructRussiaJetTu95" not in body:
        raise SystemExit("Tu-95 missing from Heavy AirBase — abort")
    lines = [ln for ln in body.splitlines() if ln.strip()]
    used = {int(x) for x in re.findall(r"(?m)^\s*(\d+)\s*=", body)}
    for slot, cmd in HEAVY_ADD:
        if cmd in body:
            continue
        use = slot if slot not in used else next(i for i in range(1, 15) if i not in used)
        lines.append(f"  {use} = {cmd}")
        used.add(use)

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
    add = {k: v for k, v in pairs.items() if data.find(k.encode("ascii")) < 0}
    for label, value in add.items():
        lb = label.encode("ascii")
        entry = (
            b" LBL"
            + struct.pack("<I", 1)
            + struct.pack("<I", len(lb))
            + lb
            + b" RTS"
            + struct.pack("<I", len(value))
            + encode_csf_string(value)
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
    assert sha256(DATA_BIG) == EXPECTED_DATA, "Tu-95 DATA baseline mismatch — abort"
    assert sha256(ART_BIG) == EXPECTED_ART, "Tu-95 ART baseline mismatch — abort"

    data_entries = read_big(DATA_BIG)
    art_entries = read_big(ART_BIG)

    tu95_key = rf"{AF}\RussiaJetTu95.ini"
    tu95_before = data_entries[tu95_key]
    usa_b2a_key = r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini"
    usa_e3_key = r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini"
    usa_e737_key = r"Data\INI\Object\Specter\United States Of America\AmericaJetE737Visual.ini"
    usa_ch47_key = r"Data\INI\Object\Specter\United States Of America\Airforce\CH47F.ini"
    usa_sys_key = r"Data\INI\Object\Specter\United States Of America\USA_System.ini"
    weapon_key = r"Data\INI\Weapon.ini"
    ocl_key = r"Data\INI\ObjectCreationList.ini"
    sp_key = r"Data\INI\SpecialPower.ini"

    freeze = {
        "Tu95": tu95_before,
        "B2A": data_entries[usa_b2a_key],
        "E3": data_entries[usa_e3_key],
        "E737": data_entries[usa_e737_key],
        "CH47": data_entries[usa_ch47_key],
        "Weapon": data_entries[weapon_key],
        "OCL": data_entries[ocl_key],
        "SP": data_entries[sp_key],
        "B52": extract_object(data_entries[usa_sys_key].decode("latin1", "replace"), "AmericaJetB52H"),
    }
    cb_before = data_entries[CB_KEY].decode("latin1", "replace")
    for btn in (
        "Command_AmericaB52CarpetStrike",
        "Command_E3SARScan",
        "Command_E737SARScan",
        "Command_FireMainWeapon",
        "Command_ChinookUnload",
    ):
        assert re.search(rf"(?ms)^CommandButton\s+{btn}\s*\n.*?^End\s*$", cb_before), btn
    carpet = re.search(
        r"(?ms)^CommandButton\s+Command_AmericaB52CarpetStrike\s*\n.*?^End\s*$", cb_before
    ).group(0)
    e3btn = re.search(r"(?ms)^CommandButton\s+Command_E3SARScan\s*\n.*?^End\s*$", cb_before).group(0)
    e737btn = re.search(
        r"(?ms)^CommandButton\s+Command_E737SARScan\s*\n.*?^End\s*$", cb_before
    ).group(0)

    missing_art = [rel for rel in ART_REL if not (PATCH / rel).exists()]
    assert not missing_art, f"Missing donor ART: {missing_art}"
    for rel in ART_REL:
        art_entries[art_key(rel)] = (PATCH / rel).read_bytes()

    for obj_id, src in OBJECTS.items():
        text = src.read_text(encoding="utf-8")
        assert f"Object {obj_id}" in text
        data_entries[rf"{AF}\{obj_id}.ini"] = text.encode("utf-8")

    data_entries[r"Data\INI\MappedImages\HandCreated\Russia_Part2_Aircraft_Images.INI"] = (
        PATCH / "Data/INI/MappedImages/HandCreated/Russia_Part2_Aircraft_Images.INI"
    ).read_bytes()
    data_entries[r"Data\English\SPECTER_RUSSIA_PART2_Strings.txt"] = (
        PATCH / "Data/English/SPECTER_RUSSIA_PART2_Strings.txt"
    ).read_bytes()

    cs = data_entries[CS_KEY].decode("latin1", "replace")
    cb = data_entries[CB_KEY].decode("latin1", "replace")
    for name, block in NEW_CS.items():
        cs = upsert_commandset(cs, name, block)
    cs = patch_heavy_cs(cs)
    for name, block in NEW_BTNS.items():
        cb = upsert_commandbutton(cb, name, block)
    assert carpet in cb and e3btn in cb and e737btn in cb
    data_entries[CS_KEY] = cs.encode("latin1", "replace")
    data_entries[CB_KEY] = cb.encode("latin1", "replace")
    data_entries[CSF_KEY] = upsert_csf(data_entries[CSF_KEY], CSF_STRINGS)

    # Tu-95 object bytes must be identical
    assert data_entries[tu95_key] == freeze["Tu95"]

    OUT.mkdir(parents=True, exist_ok=True)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    write_big(out_data, data_entries)
    write_big(out_art, art_entries)

    vdata = read_big(out_data)
    vart = read_big(out_art)
    checks: list[tuple[str, bool]] = []

    def ok(label: str, cond: bool) -> None:
        checks.append((label, cond))
        print(("PASS" if cond else "FAIL"), label)

    ok("Tu-95 unchanged", vdata[tu95_key] == freeze["Tu95"])
    ok("B2A unchanged", vdata[usa_b2a_key] == freeze["B2A"])
    ok("E3 unchanged", vdata[usa_e3_key] == freeze["E3"])
    ok("E737 unchanged", vdata[usa_e737_key] == freeze["E737"])
    ok("Chinook unchanged", vdata[usa_ch47_key] == freeze["CH47"])
    ok("Weapon.ini unchanged", vdata[weapon_key] == freeze["Weapon"])
    ok("OCL.ini unchanged", vdata[ocl_key] == freeze["OCL"])
    ok("SpecialPower.ini unchanged", vdata[sp_key] == freeze["SP"])
    ok(
        "B52 unchanged",
        extract_object(vdata[usa_sys_key].decode("latin1", "replace"), "AmericaJetB52H")
        == freeze["B52"],
    )

    tu160 = vdata[rf"{AF}\RussiaJetTU160.ini"].decode("utf-8")
    ok("Tu-160 exists", "Object RussiaJetTU160" in tu160)
    ok("Tu-160 B2A weapon", "AmericaB2A10TonBombWeapon" in tu160)
    ok("Tu-160 visual", "LSFRussiaTu160" in tu160)

    an225 = vdata[rf"{AF}\RussiaJetAn225.ini"].decode("utf-8")
    ok("An-225 exists", "Object RussiaJetAn225" in an225)
    ok("An-225 E3 SP", "AmericaE3TargetedSARScan" in an225)
    ok("An-225 E3 OCL", "OCL_AmericaE3TargetedSARScan" in an225)
    ok("An-225 vision 1200", re.search(r"VisionRange\s*=\s*1200", an225) is not None)
    ok("An-225 shroud 1200", re.search(r"ShroudClearingRange\s*=\s*1200", an225) is not None)
    ok("An-225 stealth 4000", "DetectionRange = 4000" in an225)

    a50 = vdata[rf"{AF}\RussiaJetA50.ini"].decode("utf-8")
    ok("A-50 exists", "Object RussiaJetA50" in a50)
    ok("A-50 E737 SP", "AmericaE737TargetedSARScan" in a50)
    ok("A-50 E737 OCL", "OCL_AmericaE737TargetedSARScan" in a50)
    ok("A-50 vision 810", re.search(r"VisionRange\s*=\s*810", a50) is not None)
    ok("A-50 stealth 2700", "DetectionRange = 2700" in a50)

    an124 = vdata[rf"{AF}\RussiaJetAn124.ini"].decode("utf-8")
    ok("An-124 exists", "Object RussiaJetAn124" in an124)
    ok("An-124 slots 64", "Slots                 = 64" in an124)
    ok("An-124 TRANSPORT", "TRANSPORT" in an124)
    ok("An-124 no WeaponSet", not re.search(r"(?m)^\\s*WeaponSet\\b", an124))

    avion = vdata[rf"{AF}\RussiaJetAvionIL76.ini"].decode("utf-8")
    ok("avionIL76 exists", "Object RussiaJetAvionIL76" in avion)
    ok("avion slots 32", "Slots                 = 32" in avion)

    cargo = vdata[rf"{AF}\RussiaJetCargoIL76.ini"].decode("utf-8")
    ok("cargoIL76 exists", "Object RussiaJetCargoIL76" in cargo)
    ok("cargo slots 48", "Slots                 = 48" in cargo)
    ok("avion != cargo", avion != cargo)

    vcs = vdata[CS_KEY].decode("latin1", "replace")
    ok("Heavy Tu-95 kept", "Command_ConstructRussiaJetTu95" in vcs)
    for cmd in (
        "Command_ConstructRussiaJetTU160",
        "Command_ConstructRussiaJetAn225",
        "Command_ConstructRussiaJetA50",
        "Command_ConstructRussiaJetAn124",
        "Command_ConstructRussiaJetAvionIL76",
        "Command_ConstructRussiaJetCargoIL76",
    ):
        ok(f"Heavy {cmd}", cmd in vcs)

    ours = list(OBJECTS) + ["RussiaJetTu95"]
    seen: dict[str, list[str]] = {}
    for k, blob in vdata.items():
        if not k.endswith(".ini"):
            continue
        for oid in re.findall(r"(?m)^Object\s+(\S+)", blob.decode("latin1", "replace")):
            if oid in ours:
                seen.setdefault(oid, []).append(k)
    dup = {i: p for i, p in seen.items() if len(p) > 1}
    ok("no duplicate Object IDs", not dup)

    for rel in ART_REL:
        ok(f"ART {art_key(rel)}", art_key(rel) in vart)

    failed = [l for l, c in checks if not c]
    assert not failed, f"Verification failed: {failed}"

    zip_path = OUT / "Russia_Aircraft_Expansion_Part2.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")

    dsha, asha, zsha = sha256(out_data), sha256(out_art), sha256(zip_path)
    report = f"""RUSSIA AIRCRAFT EXPANSION PART 2 = READY FOR USER TEST

Built on successful Tu-95 runtime (art_data healthy baseline + Tu-95).
Tu-95 / B-2A / E-3 / E-737 / Chinook / Weapon / OCL / SpecialPower unchanged.

AIRCRAFT
- RussiaJetTU160  visual LSFRussiaTu160  gameplay B-2A (AmericaB2A10TonBombWeapon)
- RussiaJetAn225  visual A_AN225_100     gameplay E-3 SAR (AmericaE3TargetedSARScan)
- RussiaJetA50    visual CWCruA50        gameplay E-737 SAR (AmericaE737TargetedSARScan)
- RussiaJetAn124  visual CWCruAn124      Chinook TransportContain Slots=64
- RussiaJetAvionIL76 visual Yier76       Chinook TransportContain Slots=32
- RussiaJetCargoIL76 visual LSFRussiaYR76 Chinook TransportContain Slots=48
- RussiaJetTu95   UNCHANGED

HASHES
_SPEC_DATA_ONE.big = {dsha}
_SPEC_ART_ONE.big  = {asha}
ZIP = {zsha}
PATH = {zip_path}

No in-game PASS claimed.
"""
    (OUT / "REPORT.txt").write_text(report, encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big={dsha}\n_SPEC_ART_ONE.big={asha}\nZIP={zsha}\n", encoding="utf-8"
    )
    (PATCH / "Release/DATA_RUSSIA_PART2_HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big={dsha}\n_SPEC_ART_ONE.big={asha}\nZIP={zsha}\n", encoding="utf-8"
    )
    print(report)


if __name__ == "__main__":
    main()
