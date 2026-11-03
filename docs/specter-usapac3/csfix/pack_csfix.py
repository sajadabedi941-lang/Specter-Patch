#!/usr/bin/env python3
"""Register USAPAC3 CommandSets on the live Zero Hour ControlBar path.

Release 748 put USAPAC3CommandSet* only in Data\\INI\\CommandSet_USAPAC3.ini
inside DATA. Launch_Specter copies CommandSet.ini to loose Data\\INI, and
ControlBar first-wins that file. Live THAAD menus work because S400ECommandSet*
are inside CommandSet.ini. This stage appends the four PAC-3 sets to that
same file and removes the unique CommandSet file from packed DATA so the
names cannot collide if a unique CommandSet_*.ini is ever parsed.

Does not rewrite S400ECommandSet*, US_M1120.ini, Weapon.ini, CommandButton.ini,
OCL_THAAD_*, ART, Patriot, NASAMS, failed-impl, or abtest.
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
MERGED = ROOT / "docs/specter-usapac3/merged"
CSFIX = ROOT / "docs/specter-usapac3/csfix"
DATA = MERGED / "_SPEC_DATA_ONE.big"
ART2 = MERGED / "_SPEC_ART_TWO.big"
INSTALLER = ROOT / "patch/tools/installer"

BEFORE_DATA_SHA = "347f04b919edd733c519740919a48d493700fca6bc2f0ed5a224b64ed2f2ebbe"
BEFORE_CS_SHA = "f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223"
ART2_SHA = "2a65d89d60db9696a2b3a69df5a1c7cb173e10de027e7be6aedb6ba3cb47ae38"
THAAD_SHA = "b56d62cdb44d0d3e582df51aeee56fcb25a447397983e8ced5788a4520dae92f"
WEAPON_SHA = "a8eb8340aecd1bd04147e97b4b5ce218f91233464178c34c66ff2cc003c5d6b8"
CB_SHA = "1870f1118e20e64b9f4186c49dd561884296ddda9fb7b2caa90bd9f26e8eb65c"
OCL_SHA = "e284d55c2b96fcb8c6aa585d155ba94b9f6fbbe1810f30cde96e3ef6bc16cff5"
OCLZ_SHA = "ee88eb90ee1ac12d1127daaf19529f1477b21987582f1102ffbb2a60b3ad79ad"

S400E_SHA = {
    b"S400ECommandSet": "d705077266291cb18edabec56bf1696c011682cca1f191227dc81563a02d6143",
    b"S400E_MTS_CommandSet": "f695dce4f6c1800374abb6959c075433d2f965580fec153bb5f7c1d0fe8e5998",
    b"S400ECommandSet_Deployed": "94c34b1ee20f3673ef7367ddcb145d06dc3318a87f4873d0b402a288c9785307",
    b"S400ECommandSet_AA": "f5166929304af7750478939e33a186ef319115a6f076e4e9f9637e32e34f4559",
    b"S400ECommandSet_ABM": "f512e16d145e583d9b20670fd66f6153ec94b61431fccffe22173688f0bf98bd",
}
OVERLAY_S400E_SHA = {
    b"S400ECommandSet": "327d1e31c7c29fc1b9b8d26c7ef198751239e2890c45faf35e12beffe93f7b95",
    b"S400E_MTS_CommandSet": "ad52ed14c13b2c1d015cb8ba501229e8a06f9b104ce4a3f654195b0c5f362149",
    b"S400ECommandSet_Deployed": "4bd3ab4b7c41e341b4b9d075a2895b3715a35e9beec5e03e01a4f871304501b2",
    b"S400ECommandSet_AA": "dcaa14f6a272770d1a853e15f0db422aaa2c8d9d04b1020cbfbc653452538a11",
    b"S400ECommandSet_ABM": "a2e8f4fc0af392dc369301a2a41b31007aea47027deadb0afa1db100c4af1c4c",
}

CS_KEY = r"data\ini\commandset.ini"
CB_KEY = r"data\ini\commandbutton.ini"
THAAD_KEY = r"data\ini\object\specter\united states of america\airdefense\us_m1120.ini"
OBJ_KEY = r"data\ini\object\specter\united states of america\airdefense\usapac3.ini"
WPN_KEY = r"data\ini\weapon.ini"
OCL_KEY = r"data\ini\objectcreationlist.ini"
OCLZ_KEY = r"data\ini\objectcreationlist_zzzz_zzgmadabm.ini"
CSU_KEY = r"data\ini\commandset_usapac3.ini"
OCLU_KEY = r"data\ini\objectcreationlist_usapac3.ini"

CS_STORE = r"Data\INI\CommandSet_USAPAC3.ini"

LOOSE_CS = [
    MERGED / "CommandSet.ini",
    INSTALLER / "CommandSet.ini",
    ROOT / "patch/Data/INI/CommandSet.ini",
]

UNIQUE_SETS = (
    b"USAPAC3CommandSet",
    b"USAPAC3CommandSet_AA",
    b"USAPAC3CommandSet_ABM",
    b"USAPAC3CommandSet_Deployed",
)

CS_BODY = b"""\
; SPECTER PATCH - USAPAC3 CommandSets registered in live CommandSet.ini.
; ControlBar first-wins loose Data\\INI\\CommandSet.ini (Launch_Specter copies it).
; Does not redefine S400ECommandSet / S400ECommandSet_AA / _ABM / _Deployed.

CommandSet USAPAC3CommandSet
  1 = Command_ADS_MTS_SWITCH
  3 = Command_AADS_AA_Mode
  5 = Command_AADS_ABM_Mode
  14 = Command_Stop
End

CommandSet USAPAC3CommandSet_AA
  6  = Command_ADSCombatMode
  14 = Command_Stop
End

CommandSet USAPAC3CommandSet_ABM
  6  = Command_ADS_ABM_CombatMode
  14 = Command_Stop
End

CommandSet USAPAC3CommandSet_Deployed
  13 = Command_FireControlPack
  14 = Command_Stop
End
""".replace(b"\n", b"\r\n")


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def key(name: str) -> str:
    return name.replace("/", "\\").lower()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        fail(f"not BIGF {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos = end + 1
        entries.append((name, off, size))
    return data, entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin-1")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin-1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def extract_top_level(blob: bytes, kind: bytes, name: bytes) -> bytes:
    pat = re.compile(rb"(?m)^" + re.escape(kind) + rb"\s+" + re.escape(name) + rb"\s*$")
    matches = list(pat.finditer(blob))
    if len(matches) != 1:
        fail(f"expected 1 {kind.decode()} {name.decode()}, got {len(matches)}")
    lines = blob[matches[0].start() :].splitlines(True)
    acc = [lines[0]]
    for line in lines[1:]:
        acc.append(line)
        if line.strip() == b"End" and line[:1] not in b" \t":
            break
    return b"".join(acc)


def count_headers(blob: bytes, kind: bytes, name: bytes) -> int:
    return len(re.findall(rb"(?m)^" + re.escape(kind) + rb"\s+" + re.escape(name) + rb"\s*$", blob))


def append_cs(blob: bytes) -> bytes:
    for name in UNIQUE_SETS:
        if count_headers(blob, b"CommandSet", name):
            fail(f"{name.decode()} already present")
    if not blob.endswith(b"\n"):
        fail("CommandSet.ini missing trailing newline")
    extra = CS_BODY if CS_BODY.endswith(b"\n") else CS_BODY + b"\r\n"
    return blob + b"\r\n" + extra


def assert_s400e(blob: bytes, expected: dict[bytes, str], label: str) -> None:
    for name, digest in expected.items():
        got = sha256(extract_top_level(blob, b"CommandSet", name))
        if got != digest:
            fail(f"{label} {name.decode()} sha {got} != {digest}")


def main() -> int:
    if sha_file(DATA) != BEFORE_DATA_SHA:
        fail("input DATA is not specter-usapac3-independent packed BIG")
    if sha_file(ART2) != ART2_SHA:
        fail("ART TWO changed")

    raw, entries = read_big(DATA)
    file_map = {n: raw[o : o + s] for n, o, s in entries}
    by = {key(n): n for n in file_map}

    for k, expected in (
        (THAAD_KEY, THAAD_SHA),
        (WPN_KEY, WEAPON_SHA),
        (CS_KEY, BEFORE_CS_SHA),
        (CB_KEY, CB_SHA),
        (OCL_KEY, OCL_SHA),
        (OCLZ_KEY, OCLZ_SHA),
    ):
        got = sha256(file_map[by[k]])
        if got != expected:
            fail(f"protected {k} sha {got} != {expected}")

    if CSU_KEY not in by:
        fail("748 unique CommandSet_USAPAC3.ini missing from input DATA")
    if OCLU_KEY not in by:
        fail("unique ObjectCreationList_USAPAC3.ini missing")

    old_cs = file_map[by[CS_KEY]]
    assert_s400e(old_cs, S400E_SHA, "packed-before")
    new_cs = append_cs(old_cs)
    if not new_cs.startswith(old_cs):
        fail("CommandSet.ini append was not prefix-preserving")
    assert_s400e(new_cs, S400E_SHA, "packed-after")
    for name in UNIQUE_SETS:
        if count_headers(new_cs, b"CommandSet", name) != 1:
            fail(f"append missing {name.decode()}")

    obj = file_map[by[OBJ_KEY]]
    if b"CommandSet           = USAPAC3CommandSet\r\n" not in obj:
        fail("Object USAPAC3 lost unique CommandSet")
    if b"S400ECommandSet" in obj:
        fail("Object USAPAC3 still names S400E")

    file_map[by[CS_KEY]] = new_cs
    del file_map[by[CSU_KEY]]

    if sha256(file_map[by[THAAD_KEY]]) != THAAD_SHA:
        fail("US_M1120.ini mutated")
    if sha256(file_map[by[WPN_KEY]]) != WEAPON_SHA:
        fail("Weapon.ini mutated")
    if sha256(file_map[by[CB_KEY]]) != CB_SHA:
        fail("CommandButton.ini mutated")
    if sha256(file_map[by[OCL_KEY]]) != OCL_SHA:
        fail("ObjectCreationList.ini mutated")
    if key(CS_STORE) in {key(n) for n in file_map}:
        fail("unique CommandSet_USAPAC3.ini still packed")

    out = build_big(file_map)
    DATA.write_bytes(out)

    live_written = []
    for path in LOOSE_CS:
        old = path.read_bytes()
        if path.name == "CommandSet.ini" and path.parent.name == "INI":
            assert_s400e(old, OVERLAY_S400E_SHA, f"{path}-before")
            updated = append_cs(old)
            if not updated.startswith(old):
                fail(f"{path} append was not prefix-preserving")
            assert_s400e(updated, OVERLAY_S400E_SHA, f"{path}-after")
        else:
            if old != old_cs:
                fail(f"{path} was not the live 748 CommandSet.ini")
            updated = new_cs
        path.write_bytes(updated)
        live_written.append(path)

    installer_cs = (INSTALLER / "CommandSet.ini").read_bytes()
    merged_cs = (MERGED / "CommandSet.ini").read_bytes()
    if installer_cs != new_cs or merged_cs != new_cs:
        fail("installer/merged CommandSet.ini != packed")

    CSFIX.mkdir(parents=True, exist_ok=True)
    (CSFIX / "_SPEC_DATA_ONE.big").write_bytes(out)
    (MERGED / "_SPEC_DATA_ONE.big.sha256").write_text(f"{sha256(out)}  _SPEC_DATA_ONE.big\n", encoding="ascii")
    (CSFIX / "CommandSet.ini").write_bytes(new_cs)

    print("packed", sha256(out), "bytes", len(out), "entries", len(file_map))
    print("CommandSet.ini", sha256(new_cs), "bytes", len(new_cs))
    print("THAAD file unchanged", THAAD_SHA)
    print("ART TWO unchanged", ART2_SHA)
    print("unique CommandSet_USAPAC3.ini removed from DATA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
