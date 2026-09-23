#!/usr/bin/env python3
"""AIRCRAFT_ROSTER_EXPANSION_AFRICA_PAKISTAN_SYRIA_STAGE_01.

Add 2 imported jets + 1 helicopter to South Africa, Pakistan, and Syria.
Clones only. Does not modify donor USA/Russia/China objects, existing
aircraft, CommandSet.ini, CommandButton.ini, HUD, or PlayerTemplate.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/EA6B_JAPAN_TO_USA_RESTORE_STAGE_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/EA6B_JAPAN_TO_USA_RESTORE_STAGE_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "eb58e8e6a4212cedfed7d4007800be5cc28833f6a359c9bbc593987990b784e7"
EXPECTED_ART_SHA = "493c16d2a990cad70d459edbbb6eede963172f433a16f57b241688205a19f314"

RELEASE = "AIRCRAFT_ROSTER_EXPANSION_AFRICA_PAKISTAN_SYRIA_STAGE_01"
WS = Path("/workspace/patch/Release") / RELEASE

P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_CS_NEW = r"Data\INI\CommandSet_ZZZZ_AfricaPakistanSyria_AirExp.ini"
P_BTN_NEW = r"Data\INI\CommandButton_ZZZZ_AfricaPakistanSyria_AirExp.ini"

HIGH_JET = 5500
HIGH_HELI = 4200

# (faction, role, new_object, new_path, donor_path, donor_object, donor_side, button_image, cost)
JOBS = [
    (
        "SouthAfrica", "jet", "SouthAfricaJetF15E",
        r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetF15E.ini",
        r"Data\INI\Object\Specter\United States Of America\Airforce\F15E_229.ini",
        "AmericaJetAurora", "America", "F15E", HIGH_JET,
    ),
    (
        "SouthAfrica", "jet", "SouthAfricaJetJ10C",
        r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetJ10C.ini",
        r"Data\INI\Object\Specter\PLA\Airforce\J10C.ini",
        "ChinaJetJ10C", "China", "pla_j10c", HIGH_JET,
    ),
    (
        "SouthAfrica", "heli", "SouthAfricaHelicopterAH64E",
        r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaHelicopterAH64E.ini",
        r"Data\INI\Object\Specter\United States Of America\Airforce\AH64E.ini",
        "AmericaHelicopterAH64E", "America", "us_ah64d", HIGH_HELI,
    ),
    (
        "Pakistan", "jet", "PakistanJetSu35S",
        r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetSu35S.ini",
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su35S.ini",
        "RussiaJetSu35S", "Russia", "SU35", HIGH_JET,
    ),
    (
        "Pakistan", "jet", "PakistanJetF15E",
        r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanJetF15E.ini",
        r"Data\INI\Object\Specter\United States Of America\Airforce\F15E_229.ini",
        "AmericaJetAurora", "America", "F15E", HIGH_JET,
    ),
    (
        "Pakistan", "heli", "PakistanHelicopterWZ10",
        r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\PakistanHelicopterWZ10.ini",
        r"Data\INI\Object\Specter\PLA\Airforce\WZ10ME.ini",
        "ChinaHelicopterWZ10ME", "China", "pla_wz10me", HIGH_HELI,
    ),
    (
        "Syria", "jet", "SyriaJetSu30SM2",
        r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\SyriaJetSu30SM2.ini",
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su30SM2.ini",
        "RussiaJetSu30SM2", "Russia", "rus_su33mk3", HIGH_JET,
    ),
    (
        "Syria", "jet", "SyriaJetJ16D",
        r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\SyriaJetJ16D.ini",
        r"Data\INI\Object\Specter\PLA\Airforce\J16D.ini",
        "ChinaJetJ16D", "China", "pla_j16d", HIGH_JET,
    ),
    (
        "Syria", "heli", "SyriaHelicopterKA52",
        r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\SyriaHelicopterKA52.ini",
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\KA52M.ini",
        "RussiaHelicopterKA52", "Russia", "rus_ka52", HIGH_HELI,
    ),
]

HEAVY_CS = {
    "SouthAfrica_HeavyAirBaseCommandSet": [
        "  1 = Command_ConstructSouthAfrica_Mi-8T",
        "  2 = Command_ConstructSouthAfricaHelicopterRooivalk",
        "  3 = Command_ConstructSouthAfricaHelicopterOryx",
        "  4 = Command_ConstructSouthAfricaJetIL76",
        "  5 = Command_ConstructSouthAfricaJetF15E",
        "  6 = Command_ConstructSouthAfricaJetJ10C",
        "  7 = Command_ConstructSouthAfricaHelicopterAH64E",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ],
    "Pakistan_HeavyAirBaseCommandSet": [
        "  1 = Command_ConstructPakistan_Mi-8T",
        "  2 = Command_ConstructPakistan_IL-76",
        "  3 = Command_ConstructPakistanJetSu35S",
        "  4 = Command_ConstructPakistanJetF15E",
        "  5 = Command_ConstructPakistanHelicopterWZ10",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ],
    "Syria_HeavyAirBaseCommandSet": [
        "  1 = Command_ConstructSyria_Mi-8T",
        "  2 = Command_ConstructSyria_IL-76",
        "  3 = Command_ConstructSyriaBomberH6K",
        "  4 = Command_ConstructSyriaJetSu30SM2",
        "  5 = Command_ConstructSyriaJetJ16D",
        "  6 = Command_ConstructSyriaHelicopterKA52",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
    ],
}

DONOR_PATHS = sorted({j[4] for j in JOBS})
FROZEN = [
    P_CMDSET, P_CMDBTN, P_PT, P_PT_PATCH,
    r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaJetF18Prowler.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetEA6B.ini",
] + DONOR_PATHS


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(name: str) -> str:
    return name.replace("/", "\\")


def read_big(path: Path) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries: list[tuple[str, bytes]] = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries, target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 path, got {len(hits)}")
    return hits[0]


def text_of(entries, target: str) -> str:
    return entries[find_index(entries, target)][1].decode("latin1", errors="replace")


def add_file(entries, name: str, text: str) -> None:
    n = norm(name)
    if any(norm(x).lower() == n.lower() for x, _ in entries):
        raise SystemExit(f"already packed: {name}")
    entries.append((n, text.replace("\n", "\r\n").encode("latin1", errors="replace")))


def extract_object(text: str, name: str) -> str:
    m = re.search(rf"(?im)^Object\s+{re.escape(name)}\s*$", text)
    if not m:
        raise SystemExit(f"missing Object {name}")
    m2 = re.search(r"(?im)^Object\s+\S+", text[m.end() :])
    return text[m.start() : m.end() + m2.start() if m2 else len(text)]


def clone_object(src: str, old: str, new: str, old_side: str, new_side: str, header: str, cost: int) -> str:
    block = extract_object(src, old)
    t = block.replace(old, new)
    t2, c = re.subn(rf"(?im)^(\s*Side\s*=\s*){re.escape(old_side)}\b", rf"\1{new_side}", t)
    if c < 1:
        raise SystemExit(f"{new}: side remap failed")
    t = header + t2
    t, ncost = re.subn(r"(?im)^(\s*BuildCost\s*=\s*)\S+", rf"\g<1>{cost}", t, count=1)
    if ncost != 1:
        raise SystemExit(f"{new}: BuildCost replace failed")
    t = re.sub(r"(?im)^(\s*Buildable\s*=\s*)\S+", r"\1Yes", t, count=1)
    t = re.sub(r"(?im)^[ \t]*Science[ \t]*=[ \t]*.*\n", "", t)
    t = re.sub(r"(?im)^[ \t]*RequiredScience[ \t]*=[ \t]*.*\n", "", t)
    t = re.sub(r"(?im)^[ \t]*NeededUpgrade[ \t]*=[ \t]*.*\n", "", t)
    if f"Object {new}" not in t:
        raise SystemExit(f"{new}: object name missing")
    if f"Object {old}" in t:
        raise SystemExit(f"{new}: donor object name leaked")
    if f"Side                = {old_side}" in t or f"Side = {old_side}" in t:
        # allow leftover comments only
        for ln in t.splitlines():
            if re.match(rf"(?i)^\s*Side\s*=\s*{old_side}\b", ln):
                raise SystemExit(f"{new}: donor Side leaked")
    if f"BuildCost" in t and str(cost) not in t:
        raise SystemExit(f"{new}: high cost missing")
    return t


def unit_button(btn: str, obj: str, image: str) -> str:
    return (
        f"CommandButton {btn}\n"
        f"  Command          = UNIT_BUILD\n"
        f"  Object           = {obj}\n"
        f"  TextLabel        = CONTROLBAR:Construct{obj}\n"
        f"  ButtonImage      = {image}\n"
        f"  ButtonBorderType = BUILD\n"
        f"  DescriptLabel    = CONTROLBAR:ToolTip{obj}\n"
        f"End\n\n"
    )


def main() -> int:
    if sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("DATA SHA mismatch")
    if not SRC_ART.exists() or sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("ART SHA mismatch")

    entries = read_big(SRC_DATA)
    orig = list(entries)
    orig_map = {norm(n).lower(): b for n, b in orig}

    for job in JOBS:
        faction, role, obj, dest, donor_path, donor_obj, donor_side, image, cost = job
        donor = text_of(entries, donor_path)
        header = (
            f"; {RELEASE} clone. Donor {donor_obj} NOT modified. "
            f"High cost {cost}. Side {faction}.\n"
        )
        text = clone_object(donor, donor_obj, obj, donor_side, faction, header, cost)
        if "Model" not in text:
            raise SystemExit(f"{obj}: missing Model")
        add_file(entries, dest, text)

    btn_txt = f"; {RELEASE} construct buttons\n\n"
    for job in JOBS:
        faction, role, obj, dest, donor_path, donor_obj, donor_side, image, cost = job
        btn_txt += unit_button(f"Command_Construct{obj}", obj, image)
    add_file(entries, P_BTN_NEW, btn_txt)

    cs_txt = f"; {RELEASE} HeavyAirBase last-win\n\n"
    for name, lines in HEAVY_CS.items():
        cs_txt += f"CommandSet {name}\n"
        cs_txt += "\n".join(lines) + "\nEnd\n\n"
    add_file(entries, P_CS_NEW, cs_txt)

    # Frozen originals.
    for p in FROZEN:
        if entries[find_index(entries, p)][1] != orig_map[norm(p).lower()]:
            raise SystemExit(f"frozen path changed: {p}")

    orig_names = [n for n, _ in orig]
    new_names = [n for n, _ in entries]
    if new_names[: len(orig_names)] != orig_names:
        raise SystemExit("packed path order prefix changed")
    added = new_names[len(orig_names) :]
    expected_added = [j[3] for j in JOBS] + [P_BTN_NEW, P_CS_NEW]
    if [norm(x) for x in added] != expected_added:
        raise SystemExit(f"unexpected added paths: {added}")

    for n, b in entries[: len(orig)]:
        if b != orig_map[norm(n).lower()]:
            raise SystemExit(f"existing file rewritten: {n}")

    data_blob = build_big_ordered(entries)
    rebuilt = read_big_from_bytes(data_blob)
    if [n for n, _ in rebuilt] != new_names:
        raise SystemExit("rebuild order drifted")
    for job in JOBS:
        obj = job[2]
        dest = job[3]
        text = text_of(rebuilt, dest)
        if f"Object {obj}" not in text:
            raise SystemExit(f"packed missing {obj}")
        if f"BuildCost           = {job[8]}" not in text and f"BuildCost = {job[8]}" not in text:
            if str(job[8]) not in text:
                raise SystemExit(f"{obj} cost not packed")

    cs_live = text_of(rebuilt, P_CS_NEW)
    for name in HEAVY_CS:
        if f"CommandSet {name}" not in cs_live:
            raise SystemExit(f"missing last-win {name}")

    WS.mkdir(parents=True, exist_ok=True)
    data_path = WS / "_SPEC_DATA_ONE.big"
    data_path.write_bytes(data_blob)
    data_sha = sha256_file(data_path)

    added_list = "\n".join(f"  {p}" for p in expected_added)
    jobs_list = "\n".join(
        f"  {j[0]} | {j[1]} | {j[2]} | donor {j[5]} | cost {j[8]} | {j[3]}"
        for j in JOBS
    )
    audit = f"""AIRCRAFT_ROSTER_EXPANSION_AFRICA_PAKISTAN_SYRIA_STAGE_01
SOURCE_DATA_SHA = {EXPECTED_DATA_SHA}
SOURCE_ART_SHA = {EXPECTED_ART_SHA}
NEW_DATA_SHA256 = {data_sha}
NEW_DATA_BYTES = {data_path.stat().st_size}
NEW_DATA_FILE_COUNT = {len(entries)}
ART_CHANGED = NO
ART_INCLUDED = NO (use existing ART SHA {EXPECTED_ART_SHA})

EXISTING_ROSTER
  SouthAfrica Airfield 12/12 full (Mirage/Cheetah/Gripen/Hawk/Impala/Buccaneer)
  SouthAfrica Heavy Mi-8 Rooivalk Oryx IL76
  Pakistan Airfield 12/12 full (F-16/J-10CE/JF-17/F-7/Mirage/A-5)
  Pakistan Heavy Mi-8 IL76
  Syria Airfield 12/12 full (MiG/Su/J-7/L-39)
  Syria Heavy Mi-8 IL76 H-6K

ADDED
{jobs_list}

PLACED_ON = *_HeavyAirBaseCommandSet last-win (airfields full)
PREREQUISITES = none (science locks stripped on clones)
DONOR_OBJECTS_MODIFIED = NO
EXISTING_AIRCRAFT_MODIFIED = NO
PLAYERTEMPLATE_MODIFIED = NO
HUD_MODIFIED = NO
COMMANDSET_INI_MODIFIED = NO
COMMANDBUTTON_INI_MODIFIED = NO

ADDED_DATA_PATHS
{added_list}

BOOT_SAFE = YES
INGAME_TESTED = NO
"""
    changelog = """AIRCRAFT_ROSTER_EXPANSION_AFRICA_PAKISTAN_SYRIA_STAGE_01

South Africa: USA F-15E + China J-10C + USA AH-64E (5500/5500/4200)
Pakistan: Russia Su-35S + USA F-15E + China WZ-10 (5500/5500/4200)
Syria: Russia Su-30SM2 + China J-16D + Russia Ka-52 (5500/5500/4200)

Clones only. Donors, existing aircraft, HUD, PlayerTemplate unchanged.
Placed on HeavyAirBase because airfield bars are already full.
ART unchanged.
"""
    install = f"""AIRCRAFT_ROSTER_EXPANSION_AFRICA_PAKISTAN_SYRIA_STAGE_01

1. Copy _SPEC_DATA_ONE.big over the live Specter DATA pair.
2. Keep the existing ART pair (SHA {EXPECTED_ART_SHA}).
3. Play South Africa / Pakistan / Syria. Build Heavy Air Base.
4. Confirm the 2 imported jets and 1 helicopter appear at high cost.

DATA SHA256 {data_sha}
"""
    (WS / "audit.txt").write_text(audit, encoding="utf-8")
    (WS / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS / "INSTALL.txt").write_text(install, encoding="utf-8")
    (WS / "CHANGED_FILES.txt").write_text("ADDED_DATA_PATHS\n" + added_list + "\nART_CHANGED = NO\n", encoding="utf-8")
    (WS / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"ART unchanged SHA256 {EXPECTED_ART_SHA}\n",
        encoding="utf-8",
    )

    zip_path = WS / f"{RELEASE}.zip"
    print("Writing ZIP...")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(WS / "audit.txt", "audit.txt")
        zf.write(WS / "changelog.txt", "changelog.txt")
        zf.write(WS / "SHA256.txt", "SHA256.txt")
        zf.write(WS / "INSTALL.txt", "INSTALL.txt")
        zf.write(WS / "CHANGED_FILES.txt", "CHANGED_FILES.txt")
    zip_sha = sha256_file(zip_path)
    (WS / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"ART unchanged SHA256 {EXPECTED_ART_SHA}\n"
        f"{RELEASE}.zip  SHA256 {zip_sha}  {zip_path.stat().st_size} bytes\n",
        encoding="utf-8",
    )
    print(audit)
    print("ZIP", zip_path, zip_path.stat().st_size, zip_sha)
    return 0


def read_big_from_bytes(data: bytes) -> list[tuple[str, bytes]]:
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


if __name__ == "__main__":
    raise SystemExit(main())
