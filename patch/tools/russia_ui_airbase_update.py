#!/usr/bin/env python3
"""Russia UI icon restore + Su-47/Su-75 on Large fighter AirBase.

Baseline: Part 2 BIGs (Tu-95 + Part 2 aircraft). Does not modify aircraft Objects,
Weapon.ini, OCL, SpecialPower, or USA files.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
IN_DIR = PATCH / "Release/SPECTER_MASTER_RUSSIA_PART2"
DATA_BIG = IN_DIR / "_SPEC_DATA_ONE.big"
ART_BIG = IN_DIR / "_SPEC_ART_ONE.big"
OUT = PATCH / "Release/SPECTER_MASTER_RUSSIA_UI_AIRBASE"
EXPECTED_DATA = "de8c51bf45f79154019d470f6244b1fa0293ed8ed93e4374dc55c22820dd049d"
EXPECTED_ART = "c9ab76a9ad6c32444159453f184666e46c530cc9d39a9d677051fc0ac81b83de"

CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
MAP_KEY = r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI"

ART_REL = [
    "Art/Textures/SU34TB.tga",
    "Art/Textures/SU35TB.tga",
    "Art/Textures/T50TB.tga",
    "Art/Textures/SU47tb.tga",
    "Art/Textures/autreT50TB.tga",
    "Art/Textures/SU24TB.tga",
    "Art/Textures/SU24Strike1TB.tga",
    "Art/Textures/autreSU24TB.tga",
    "Art/Textures/KA52TB.tga",
    "Art/Textures/TU22M3TB.tga",
    "Art/Textures/TU160TB.tga",
    "Art/Textures/TU-160.tga",
    "Art/Textures/Tu95TB.tga",
    "Art/Textures/RussiaA50TB.tga",
    "Art/Textures/RussiaAN225TB.tga",
    "Art/Textures/AN124TB.tga",
    "Art/Textures/yier76.tga",
    "Art/Textures/yier76TB.tga",
    "Art/Textures/CargoIL76RussiaTB.tga",
]

RUS_REMAP = {
    "rus_su34": """MappedImage rus_su34
  Texture = SU34TB.tga
  TextureWidth = 150
  TextureHeight = 118
  Coords = Left:0 Top:0 Right:150 Bottom:118
  Status = NONE
End
""",
    "rus_su35s": """MappedImage rus_su35s
  Texture = SU35TB.tga
  TextureWidth = 120
  TextureHeight = 92
  Coords = Left:0 Top:0 Right:120 Bottom:92
  Status = NONE
End
""",
    "rus_su57": """MappedImage rus_su57
  Texture = T50TB.tga
  TextureWidth = 120
  TextureHeight = 93
  Coords = Left:0 Top:0 Right:120 Bottom:93
  Status = NONE
End
""",
    "rus_ka52": """MappedImage rus_ka52
  Texture = KA52TB.tga
  TextureWidth = 150
  TextureHeight = 108
  Coords = Left:0 Top:0 Right:150 Bottom:108
  Status = NONE
End
""",
    "rus_su24m2": """MappedImage rus_su24m2
  Texture = SU24TB.tga
  TextureWidth = 150
  TextureHeight = 110
  Coords = Left:0 Top:0 Right:150 Bottom:110
  Status = NONE
End
""",
    "rus_su24mp": """MappedImage rus_su24mp
  Texture = SU24Strike1TB.tga
  TextureWidth = 150
  TextureHeight = 110
  Coords = Left:0 Top:0 Right:150 Bottom:110
  Status = NONE
End
""",
    "rus_tu22m3m": """MappedImage rus_tu22m3m
  Texture = TU22M3TB.tga
  TextureWidth = 750
  TextureHeight = 422
  Coords = Left:0 Top:0 Right:750 Bottom:422
  Status = NONE
End
""",
    "rus_a50": """MappedImage rus_a50
  Texture = RussiaA50TB.tga
  TextureWidth = 640
  TextureHeight = 430
  Coords = Left:0 Top:0 Right:640 Bottom:430
  Status = NONE
End
""",
}

BTN_IMAGE = {
    "Command_ConstructRussiaJetSu34": "SU34",
    "Command_ConstructRussiaJetSu35S": "SU35",
    "Command_ConstructRussiaJetSu35AG": "SU35",
    "Command_ConstructRussiaJetSu57": "T50",
    "Command_ConstructRussiaJetSu57AA": "T50",
    "Command_ConstructRussiaJetSu47Recon": "SU47",
    "Command_ConstructRussiaJetSu75Checkmate": "SU75",
    "Command_ConstructRussiaJetSU24M2": "SU24",
    "Command_ConstructRussiaJetSU24MP": "rus_su24mp",
    "Command_ConstructRussiaJetTu22M3M": "TU22M3",
    "Command_ConstructRussiaHelicopterKA52": "KA52",
    "Command_ConstructRussiaJetTU160": "TU160",
    "Command_ConstructRussiaJetTu95": "Tu95",
    "Command_ConstructRussiaJetA50": "RussiaA50",
    "Command_ConstructRussiaJetAn225": "RussiaAN225",
    "Command_ConstructRussiaJetAn124": "AN124",
    "Command_ConstructRussiaJetAvionIL76": "yier76",
    "Command_ConstructRussiaJetCargoIL76": "CargoIL76Russia",
}

SIZE_FIX_FILES = {
    r"Data\INI\MappedImages\HandCreated\Russia_Tu95_Images.INI": """; Tu-95 donor button (full TGA frame)
MappedImage Tu95
  Texture = Tu95TB.tga
  TextureWidth = 1363
  TextureHeight = 751
  Coords = Left:0 Top:0 Right:1363 Bottom:751
  Status = NONE
End
""",
    r"Data\INI\MappedImages\HandCreated\Russia_Part2_Aircraft_Images.INI": """; Part-2 aircraft buttons (full TGA frames)

MappedImage TU160
  Texture = TU160TB.tga
  TextureWidth = 150
  TextureHeight = 110
  Coords = Left:0 Top:0 Right:150 Bottom:110
  Status = NONE
End

MappedImage AN124
  Texture = AN124TB.tga
  TextureWidth = 1280
  TextureHeight = 720
  Coords = Left:0 Top:0 Right:1280 Bottom:720
  Status = NONE
End

MappedImage RussiaAN225
  Texture = RussiaAN225TB.tga
  TextureWidth = 600
  TextureHeight = 380
  Coords = Left:0 Top:0 Right:600 Bottom:380
  Status = NONE
End

MappedImage RussiaA50
  Texture = RussiaA50TB.tga
  TextureWidth = 640
  TextureHeight = 430
  Coords = Left:0 Top:0 Right:640 Bottom:430
  Status = NONE
End

MappedImage yier76
  Texture = yier76.tga
  TextureWidth = 1194
  TextureHeight = 719
  Coords = Left:0 Top:0 Right:1194 Bottom:719
  Status = NONE
End

MappedImage CargoIL76Russia
  Texture = CargoIL76RussiaTB.tga
  TextureWidth = 550
  TextureHeight = 335
  Coords = Left:0 Top:0 Right:550 Bottom:335
  Status = NONE
End
""",
}


def sha256(p: Path | bytes) -> str:
    return hashlib.sha256(p if isinstance(p, bytes) else Path(p).read_bytes()).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
    n = struct.unpack(">I", data[8:12])[0]
    off = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        eo, sz = struct.unpack(">II", data[off : off + 8])
        i = off + 8
        while data[i]:
            i += 1
        out[data[off + 8 : i].decode("latin1")] = data[eo : eo + sz]
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


def replace_mapped(text: str, name: str, block: str) -> str:
    pat = re.compile(rf"(?ms)^MappedImage\s+{re.escape(name)}\s*\n.*?^End\s*\n")
    if not pat.search(text):
        raise SystemExit(f"MappedImage {name} not found")
    return pat.sub(block.rstrip() + "\n\n", text, count=1)


def set_button_image(cb: str, btn: str, image: str) -> str:
    pat = re.compile(rf"(?ms)^(CommandButton\s+{re.escape(btn)}\s*\n.*?^End\s*)$")
    m = pat.search(cb)
    if not m:
        raise SystemExit(f"missing {btn}")
    block = m.group(1)
    if not re.search(r"(?m)^\s*ButtonImage\s*=", block):
        raise SystemExit(f"no ButtonImage on {btn}")
    block = re.sub(r"(?m)^(\s*ButtonImage\s*=\s*)\S+", rf"\1{image}", block, count=1)
    return pat.sub(block, cb, count=1)


def patch_large(cs: str) -> str:
    m = re.search(r"(?ms)^CommandSet\s+Russia_LargeAirBaseCommandSet\s*\n(.*?)^^End\s*$", cs)
    if not m:
        raise SystemExit("Large CS missing")
    body = m.group(1)
    if "Command_ConstructRussiaJetSu75Checkmate" not in body:
        raise SystemExit("Su-75 missing from Large")
    if "Command_ConstructRussiaJetSu47Recon" in body:
        return cs
    used = {int(x) for x in re.findall(r"(?m)^\s*(\d+)\s*=", body)}
    slot = next(i for i in range(1, 13) if i not in used)
    lines = [ln for ln in body.splitlines() if ln.strip()]
    lines.append(f"  {slot} = Command_ConstructRussiaJetSu47Recon")

    def sk(ln: str) -> tuple[int, str]:
        mm = re.match(r"\s*(\d+)\s*=", ln)
        return (int(mm.group(1)), ln) if mm else (999, ln)

    lines = sorted(lines, key=sk)
    new_block = "CommandSet Russia_LargeAirBaseCommandSet\n" + "\n".join(lines) + "\nEnd\n"
    return re.sub(
        r"(?ms)^CommandSet\s+Russia_LargeAirBaseCommandSet\s*\n.*?^End\s*\n",
        new_block + "\n",
        cs,
        count=1,
    )


def patch_heavy(cs: str) -> str:
    """Keep heavies; remove Su-47 from Heavy so it lives on Large only."""
    m = re.search(r"(?ms)^CommandSet\s+Russia_HeavyAirBaseCommandSet\s*\n(.*?)^^End\s*$", cs)
    if not m:
        raise SystemExit("Heavy CS missing")
    body = m.group(1)
    for must in (
        "Command_ConstructRussiaJetTU160",
        "Command_ConstructRussiaJetTu95",
        "Command_ConstructRussiaJetA50",
        "Command_ConstructRussiaJetAn225",
        "Command_ConstructRussiaJetAn124",
        "Command_ConstructRussiaJetAvionIL76",
        "Command_ConstructRussiaJetCargoIL76",
    ):
        if must not in body:
            raise SystemExit(f"Heavy missing {must}")
    lines = [
        ln
        for ln in body.splitlines()
        if ln.strip() and "Command_ConstructRussiaJetSu47Recon" not in ln
    ]

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


def extract_object(text: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^Object\s+{re.escape(name)}\s*\n.*?^End\s*$", text)
    return m.group(0) if m else None


def main() -> None:
    assert sha256(DATA_BIG) == EXPECTED_DATA
    assert sha256(ART_BIG) == EXPECTED_ART
    data_entries = read_big(DATA_BIG)
    art_entries = read_big(ART_BIG)

    freeze_keys = [
        r"Data\INI\Weapon.ini",
        r"Data\INI\ObjectCreationList.ini",
        r"Data\INI\SpecialPower.ini",
        r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini",
        r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini",
        r"Data\INI\Object\Specter\United States Of America\AmericaJetE737Visual.ini",
        r"Data\INI\Object\Specter\United States Of America\Airforce\CH47F.ini",
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\RussiaJetTu95.ini",
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\RussiaJetTU160.ini",
    ]
    frozen = {k: data_entries[k] for k in freeze_keys}

    missing = [rel for rel in ART_REL if not (PATCH / rel).exists()]
    assert not missing, missing
    for rel in ART_REL:
        art_entries[art_key(rel)] = (PATCH / rel).read_bytes()

    mapped = data_entries[MAP_KEY].decode("latin1", "replace")
    for name, block in RUS_REMAP.items():
        mapped = replace_mapped(mapped, name, block)
    data_entries[MAP_KEY] = mapped.encode("latin1", "replace")

    for key, text in SIZE_FIX_FILES.items():
        data_entries[key] = text.encode("utf-8")
    data_entries[r"Data\INI\MappedImages\HandCreated\Russia_UI_AircraftIcons.INI"] = (
        PATCH / "Data/INI/MappedImages/HandCreated/Russia_UI_AircraftIcons.INI"
    ).read_bytes()

    cb = data_entries[CB_KEY].decode("latin1", "replace")
    for btn, image in BTN_IMAGE.items():
        cb = set_button_image(cb, btn, image)
    data_entries[CB_KEY] = cb.encode("latin1", "replace")

    cs = data_entries[CS_KEY].decode("latin1", "replace")
    cs = patch_large(cs)
    cs = patch_heavy(cs)
    data_entries[CS_KEY] = cs.encode("latin1", "replace")

    for k, blob in frozen.items():
        assert data_entries[k] == blob, f"frozen changed {k}"

    OUT.mkdir(parents=True, exist_ok=True)
    out_data, out_art = OUT / "_SPEC_DATA_ONE.big", OUT / "_SPEC_ART_ONE.big"
    write_big(out_data, data_entries)
    write_big(out_art, art_entries)

    vdata = read_big(out_data)
    vart = read_big(out_art)
    checks: list[tuple[str, bool]] = []

    def ok(label: str, cond: bool) -> None:
        checks.append((label, cond))
        print(("PASS" if cond else "FAIL"), label)

    vcs = vdata[CS_KEY].decode("latin1", "replace")
    vcb = vdata[CB_KEY].decode("latin1", "replace")
    vmap = vdata[MAP_KEY].decode("latin1", "replace")
    ok("Large Su-75", "Command_ConstructRussiaJetSu75Checkmate" in vcs)
    ok("Large Su-47", "Command_ConstructRussiaJetSu47Recon" in vcs)
    ok("Heavy Tu-160", "Command_ConstructRussiaJetTU160" in vcs)
    ok("Heavy Tu-95", "Command_ConstructRussiaJetTu95" in vcs)
    ok("Heavy no Su-47", "Command_ConstructRussiaJetSu47Recon" not in re.search(
        r"(?ms)^CommandSet Russia_HeavyAirBaseCommandSet\s*\n.*?^End\s*$", vcs
    ).group(0))
    ok("Su47 ButtonImage SU47", "ButtonImage   = SU47" in vcb or "ButtonImage = SU47" in vcb)
    ok("Su75 ButtonImage SU75", re.search(
        r"(?ms)^CommandButton Command_ConstructRussiaJetSu75Checkmate\s*\n.*?ButtonImage\s*=\s*SU75",
        vcb,
    ) is not None)
    ok("rus_su34 uses SU34TB", "Texture = SU34TB.tga" in vmap)
    ok("ART SU34TB", art_key("Art/Textures/SU34TB.tga") in vart)
    ok("ART SU47tb", art_key("Art/Textures/SU47tb.tga") in vart)
    ok("ART T50TB", art_key("Art/Textures/T50TB.tga") in vart)
    ok("ART KA52TB", art_key("Art/Textures/KA52TB.tga") in vart)
    ok("Weapon unchanged", vdata[r"Data\INI\Weapon.ini"] == frozen[r"Data\INI\Weapon.ini"])
    ok("OCL unchanged", vdata[r"Data\INI\ObjectCreationList.ini"] == frozen[r"Data\INI\ObjectCreationList.ini"])
    ok("Tu95 object unchanged", vdata[freeze_keys[7]] == frozen[freeze_keys[7]])
    ok("Tu160 object unchanged", vdata[freeze_keys[8]] == frozen[freeze_keys[8]])
    ok("B2A unchanged", vdata[freeze_keys[3]] == frozen[freeze_keys[3]])

    failed = [l for l, c in checks if not c]
    assert not failed, failed

    zip_path = OUT / "Russia_UI_Airbase_Update.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
    dsha, asha, zsha = sha256(out_data), sha256(out_art), sha256(zip_path)
    report = f"""RUSSIA UI AIRBASE UPDATE

Icons remapped to donor ART TGAs (native sizes). Su-47 + Su-75 on Large AirBase.
Aircraft Objects / weapons / OCL unchanged.

DATA SHA256 = {dsha}
ART  SHA256 = {asha}
ZIP SHA256  = {zsha}
PATH = {zip_path}
"""
    (OUT / "REPORT.txt").write_text(report, encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big={dsha}\n_SPEC_ART_ONE.big={asha}\nZIP={zsha}\n", encoding="utf-8"
    )
    print(report)


if __name__ == "__main__":
    main()
