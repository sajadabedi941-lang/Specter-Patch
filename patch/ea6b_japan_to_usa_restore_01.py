#!/usr/bin/env python3
"""EA6B_JAPAN_TO_USA_RESTORE_STAGE_01.

Replace broken USA AmericaJetF18Prowler with the healthy JapanJetEA6B donor.
Object name / Side / DisplayName / CommandSet stay USA so production is unchanged.
Japan files, other aircraft, CommandSet, CommandButton, PlayerTemplate, ART
are not edited.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/BUILDING_FLAG_COMPLETE_ROLLOUT/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/BUILDING_FLAG_COMPLETE_ROLLOUT/_SPEC_ART_ONE.big")
SRC_DATA_SHA = "2a0e9b0d77ceb442376b5e67573a1af12057713884318f2858b6ce30de2d0345"
SRC_ART_SHA = "493c16d2a990cad70d459edbbb6eede963172f433a16f57b241688205a19f314"

RELEASE = "EA6B_JAPAN_TO_USA_RESTORE_STAGE_01"
WS = Path("/workspace/patch/Release") / RELEASE
TMP = Path("/tmp") / RELEASE

P_USA = r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaJetF18Prowler.ini"
P_JP = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetEA6B.ini"
P_JP_USA = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetEA6BUSA.ini"
P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"

USA_KEEP = {
    "object": "AmericaJetF18Prowler",
    "side": "America",
    "display": "OBJECT:AmericaJetF18Prowler",
    "commandset": "GenericTacticalBomberCommandSet",
}


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
    encoded_names: list[bytes] = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded_names.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded_names):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries: list[tuple[str, bytes]], target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 packed path, got {len(hits)}")
    return hits[0]


def text_of(entries: list[tuple[str, bytes]], target: str) -> str:
    return entries[find_index(entries, target)][1].decode("latin1", errors="replace")


def restore_usa_from_japan(japan: str) -> str:
    if "Object JapanJetEA6B" not in japan:
        raise SystemExit("Japan donor missing Object JapanJetEA6B")
    if "Model               = EA6" not in japan and "Model = EA6" not in japan:
        raise SystemExit("Japan donor missing Model EA6")
    if "Specter_Weapon_EA6B_JH7A2_Bomb" not in japan:
        raise SystemExit("Japan donor missing healthy bomb weapon")
    if "D30-F6_JetLocomotor" not in japan:
        raise SystemExit("Japan donor missing D30-F6_JetLocomotor")

    text = japan
    text = re.sub(r"(?m)^Object JapanJetEA6B\s*$", "Object AmericaJetF18Prowler", text)
    text = re.sub(r"(?m)^  DisplayName = OBJECT:JapanJetEA6B\s*$", "  DisplayName = OBJECT:AmericaJetF18Prowler", text)
    text = re.sub(r"(?m)^  Side = Japan\s*$", "  Side = America", text)
    text = re.sub(
        r"(?m)^  CommandSet = JapanEA6BBomberCommandSet\s*$",
        "  CommandSet = GenericTacticalBomberCommandSet",
        text,
    )
    if "Object AmericaJetF18Prowler" not in text:
        raise SystemExit("USA object name remap failed")
    if "Side = America" not in text:
        raise SystemExit("USA Side remap failed")
    if "GenericTacticalBomberCommandSet" not in text:
        raise SystemExit("USA CommandSet remap failed")
    if "JapanJetEA6B" in text or "Side = Japan" in text:
        raise SystemExit("Japan identity leaked into USA object")
    if "JapanEA6BBomberCommandSet" in text:
        raise SystemExit("Japan CommandSet leaked into USA object")
    # Keep donor model / weapon / locomotor / AI.
    for must in (
        "Model               = EA6",
        "HideSubObject       = HOOK",
        "Specter_Weapon_EA6B_JH7A2_Bomb",
        "D30-F6_JetLocomotor",
        "OutOfAmmoDamagePerSecond = 0%",
        "Mass = 50.0",
    ):
        if must not in text:
            raise SystemExit(f"donor field missing after remap: {must}")
    if not text.endswith("\n"):
        text += "\n"
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")


def main() -> int:
    if sha256_file(SRC_DATA) != SRC_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if sha256_file(SRC_ART) != SRC_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    data_orig = read_big(SRC_DATA)
    japan = text_of(data_orig, P_JP)
    usa_old = text_of(data_orig, P_USA)
    if "Object AmericaJetF18Prowler" not in usa_old:
        raise SystemExit("USA EA-6B missing")
    if "General_Electric_F414" not in usa_old:
        raise SystemExit("expected broken USA locomotor General_Electric_F414")
    if "OutOfAmmoDamagePerSecond = 10%" not in usa_old:
        raise SystemExit("expected broken USA OutOfAmmoDamagePerSecond 10%")

    usa_new = restore_usa_from_japan(japan)
    data = list(data_orig)
    i = find_index(data, P_USA)
    data[i] = (data[i][0], usa_new.encode("latin1"))

    # Frozen paths.
    for p in (P_JP, P_JP_USA, P_CMDSET, P_CMDBTN, P_PT, P_PT_PATCH):
        if data[find_index(data, p)][1] != data_orig[find_index(data_orig, p)][1]:
            raise SystemExit(f"frozen path changed: {p}")

    orig_names = [n for n, _ in data_orig]
    new_names = [n for n, _ in data]
    if orig_names != new_names:
        raise SystemExit("DATA packed path order changed")
    if len(data) != len(data_orig):
        raise SystemExit("DATA file count changed")

    changed = []
    for (n0, b0), (n1, b1) in zip(data_orig, data):
        if b0 != b1:
            changed.append(n1)
    if changed != [P_USA]:
        raise SystemExit(f"unexpected DATA changes: {changed}")

    # Other USA airforce objects untouched.
    for n, b in data:
        nl = n.lower()
        if "united states of america\\airforce\\" in nl and norm(n).lower() != norm(P_USA).lower():
            ob = data_orig[find_index(data_orig, n)][1]
            if b != ob:
                raise SystemExit(f"other USA aircraft changed: {n}")

    data_blob = build_big_ordered(data)
    rebuilt = read_big_from_bytes(data_blob)
    if [n for n, _ in rebuilt] != orig_names:
        raise SystemExit("rebuilt DATA path order drifted")
    if rebuilt[find_index(rebuilt, P_USA)][1] != usa_new.encode("latin1"):
        raise SystemExit("rebuilt USA object mismatch")
    if rebuilt[find_index(rebuilt, P_JP)][1] != data_orig[find_index(data_orig, P_JP)][1]:
        raise SystemExit("Japan donor drifted in rebuild")

    WS.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    data_path = WS / "_SPEC_DATA_ONE.big"
    art_path = WS / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_blob)
    shutil.copy2(SRC_ART, art_path)
    if sha256_file(art_path) != SRC_ART_SHA:
        raise SystemExit("ART copy drifted")

    data_sha = sha256_file(data_path)
    art_sha = sha256_file(art_path)
    zip_path = WS / f"{RELEASE}.zip"
    audit = f"""EA6B_JAPAN_TO_USA_RESTORE_STAGE_01
SOURCE_DATA = BUILDING_FLAG_COMPLETE_ROLLOUT/_SPEC_DATA_ONE.big
SOURCE_DATA_SHA = {SRC_DATA_SHA}
SOURCE_ART_SHA = {SRC_ART_SHA}
NEW_DATA_SHA256 = {data_sha}
NEW_DATA_BYTES = {data_path.stat().st_size}
NEW_DATA_FILE_COUNT = {len(data)}
NEW_ART_SHA256 = {art_sha}
NEW_ART_BYTES = {art_path.stat().st_size}
ART_CHANGED = NO

DONOR = JapanJetEA6B
DONOR_FILE = {P_JP}
USA_OBJECT = AmericaJetF18Prowler
USA_FILE = {P_USA}

REMOVED_BROKEN_USA =
  Locomotor General_Electric_F414
  OutOfAmmoDamagePerSecond 10%
  Mass 500.0
  Armor AirplaneArmor_P
  Upgrade_AmericaCountermeasures modules

KEPT_FROM_DONOR =
  Model EA6
  HideSubObject HOOK
  Weapon Specter_Weapon_EA6B_JH7A2_Bomb
  Locomotor D30-F6_JetLocomotor + BasicJetTaxiLocomotor
  JetAIUpdate OutOfAmmoDamagePerSecond 0% MinHeight 1
  Mass 50.0
  Scale 0.9
  Armor AirplaneArmor
  No Prerequisites

USA_IDENTITY_KEPT =
  Object AmericaJetF18Prowler
  Side America
  DisplayName OBJECT:AmericaJetF18Prowler
  CommandSet GenericTacticalBomberCommandSet

ART_DEPENDENCIES (unchanged, already packed)
  Art\\W3D\\EA6.W3D
  Art\\Textures\\EA6.tga
  Art\\Textures\\USAEA6Prowler.tga
  Art\\Textures\\USAEA6ProwlerTB.tga
  MappedImage EA6Prowler

WEAPON_OK = Specter_Weapon_EA6B_JH7A2_Bomb present in Weapon.ini
LOCOMOTOR_OK = D30-F6_JetLocomotor present in Locomotor.ini
UPGRADE_LINKS_REMOVED_FROM_USA_OBJECT = Upgrade_AmericaCountermeasures Upgrade_MTS Upgrade_AmericaAdvancedTraining
PREREQUISITES = none (donor)

UNTOUCHED
  JapanJetEA6B.ini
  JapanJetEA6BUSA.ini
  other USA aircraft
  CommandSet.ini CommandButton.ini
  PlayerTemplate.ini PlayerTemplate_SpecterPatch.ini
  faction pages HUD unrelated DATA ART

CHANGED_DATA_PATHS =
  {P_USA}

BOOT_SAFE = YES
INGAME_TESTED = NO
"""
    changelog = """EA6B_JAPAN_TO_USA_RESTORE_STAGE_01

Replace the broken USA EA-6B (AmericaJetF18Prowler) with the healthy
JapanJetEA6B donor. One DATA object path only.

USA production button still builds AmericaJetF18Prowler.
CommandSet / CommandButton / PlayerTemplate / HUD / other aircraft unchanged.
ART unchanged (shared EA6.W3D already packed).

Japan files are not edited.
"""
    install = f"""EA6B_JAPAN_TO_USA_RESTORE_STAGE_01

1. Copy _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big over the live Specter pair.
2. Play USA only.
3. Confirm EA-6B builds and flies using the Japan donor locomotor/weapon.
4. Do not use this pair to test other aircraft changes.

DATA SHA256 {data_sha}
ART  SHA256 {art_sha}
"""
    (WS / "audit.txt").write_text(audit, encoding="utf-8")
    (WS / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS / "INSTALL.txt").write_text(install, encoding="utf-8")
    (WS / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {art_sha}\n"
        f"{RELEASE}.zip  SHA256 PLACEHOLDER\n",
        encoding="utf-8",
    )
    (WS / "CHANGED_FILES.txt").write_text(
        "CHANGED_DATA_PATHS\n"
        f"  {P_USA}\n"
        "ART_CHANGED = NO\n",
        encoding="utf-8",
    )

    print("Writing ZIP...")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
        zf.write(WS / "audit.txt", "audit.txt")
        zf.write(WS / "changelog.txt", "changelog.txt")
        zf.write(WS / "SHA256.txt", "SHA256.txt")
        zf.write(WS / "INSTALL.txt", "INSTALL.txt")
    zip_sha = sha256_file(zip_path)
    (WS / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {art_sha}\n"
        f"{RELEASE}.zip  SHA256 {zip_sha}  {zip_path.stat().st_size} bytes\n",
        encoding="utf-8",
    )
    print(audit)
    print("ZIP", zip_path, zip_path.stat().st_size, zip_sha)
    return 0


def read_big_from_bytes(data: bytes) -> list[tuple[str, bytes]]:
    if data[:4] != b"BIGF":
        raise SystemExit("rebuilt blob is not BIGF")
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


if __name__ == "__main__":
    raise SystemExit(main())
