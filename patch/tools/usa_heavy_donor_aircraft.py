#!/usr/bin/env python3
"""Add READY donor heavy aircraft to USA America_HeavyAirBase.

Adds:
  - AmericaJetAC130 (from prior Patch_America_AC130Spectre JetAI production object)
  - AmericaJetC17Globemaster (prior Patch_America_C17 + donor IUAC17HXNew mesh)

Does NOT invent Objects for ART-only donors (E737 / Osprey / E2avionHE).
Preserves B-2/B-21/B-52/B-1R/E-3 slots 1-5. Does NOT modify CSF.
"""
from __future__ import annotations

import hashlib
import re
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
DONOR = Path("/tmp/donor_art_extract/Art")
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_HEAVY_DONOR_AIRCRAFT.zip"
OUT_HASH = ROOT / "Release/DATA_USA_HEAVY_DONOR_AIRCRAFT_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_HEAVY_DONOR_AIRCRAFT_DOWNLOAD.txt"
VERIFY = MASTER / "_extract_usa_heavy_donor_aircraft_verify"
GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"

AC130 = Path("/tmp/AmericaJetAC130.ini")
C17 = Path("/tmp/AmericaJetC17Globemaster.ini")


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


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


def patch_commandset(cs: str) -> str:
    # Preserve slots 1-5; keep NuclearTip on 6; add new aircraft on 7-8.
    block = """CommandSet America_HeavyAirBaseCommandSet
  1  = Command_ConstructAmericaJetB2Spirit
  2  = Command_ConstructAmericaJetB21
  3  = Command_ConstructAmericaJetB52H
  4  = Command_ConstructAmericaJetB1R
  5  = Command_ConstructAmericaJetE3AWACS
  6  = Command_Upgrade_NuclearTipWarhead2
  7  = Command_ConstructAmericaJetAC130
  8  = Command_ConstructAmericaJetC17Globemaster
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""
    pat = re.compile(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    if not pat.search(cs):
        raise SystemExit("Heavy CS missing")
    return pat.sub(block.rstrip(), cs, count=1)


def ensure_buttons(cb: str) -> str:
    buttons = {
        "Command_ConstructAmericaJetAC130": """CommandButton Command_ConstructAmericaJetAC130
  Command       = UNIT_BUILD
  Object        = AmericaJetAC130
  TextLabel     = CONTROLBAR:ConstructAmericaJetAC130
  ButtonImage   = us_ac130
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipAmericaJetAC130
End
""",
        "Command_ConstructAmericaJetC17Globemaster": """CommandButton Command_ConstructAmericaJetC17Globemaster
  Command       = UNIT_BUILD
  Object        = AmericaJetC17Globemaster
  TextLabel     = CONTROLBAR:ConstructAmericaJetC17Globemaster
  ButtonImage   = C17GlobalMaster
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipAmericaJetC17Globemaster
End
""",
    }
    for name, block in buttons.items():
        if re.search(rf"^CommandButton\s+{re.escape(name)}\s*$", cb, re.M):
            cb = re.sub(
                rf"CommandButton\s+{re.escape(name)}\s*\n.*?^End\s*$",
                block.rstrip(),
                cb,
                count=1,
                flags=re.M | re.S,
            )
        else:
            # Insert after B52 button cluster
            anchor = re.search(
                r"CommandButton\s+Command_ConstructAmericaJetB52H\s*\n.*?^End\s*$",
                cb,
                re.M | re.S,
            )
            if not anchor:
                raise SystemExit("B52 button missing for anchor")
            cb = cb[: anchor.end()] + "\n\n" + block + cb[anchor.end() :]
    return cb


def ensure_mapped_c17(mi: str) -> str:
    if re.search(r"^MappedImage\s+C17GlobalMaster\s*$", mi, re.M):
        return mi
    block = """
MappedImage C17GlobalMaster
  Texture = C17GlobalMaster.tga
  TextureWidth = 1040
  TextureHeight = 752
  Coords = Left:0 Top:0 Right:1040 Bottom:752
  Status = NONE
End
"""
    return mi.rstrip() + "\n" + block


def main() -> None:
    dentries, dblob = read_big(DATA_BIG)
    aentries, ablob = read_big(ART_BIG)
    dmap = {n.replace("/", "\\"): dblob[o : o + s] for n, o, s in dentries}
    amap = {n.replace("/", "\\"): ablob[o : o + s] for n, o, s in aentries}

    if sha256(dmap["Data\\English\\generals.csf"]) != GOOD_CSF:
        raise SystemExit("CSF is not known-good — abort to protect String Manager")

    # Snapshot preserved aircraft
    usa = dmap[
        "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"
    ].decode("latin1")
    for must in ["AmericaJetB2Spirit", "AmericaJetB52H", "AmericaJetE3AWACS"]:
        assert re.search(rf"^Object\s+{must}\s*$", usa, re.M), must
    b21 = dmap[
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini"
    ]
    b1r_key = next(k for k in dmap if k.lower().endswith("airforce\\b1r.ini"))
    b1r = dmap[b1r_key]
    large_cs = re.search(
        r"CommandSet\s+America_LargeAirBaseCommandSet\s*\n(.*?)End",
        dmap["Data\\INI\\CommandSet.ini"].decode("latin1"),
        re.S,
    ).group(1)

    # Objects
    dmap[
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
    ] = AC130.read_bytes()
    dmap[
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Globemaster.ini"
    ] = C17.read_bytes()

    # CommandSet / Button / MappedImage
    cs = dmap["Data\\INI\\CommandSet.ini"].decode("latin1")
    cs2 = patch_commandset(cs)
    # Large unchanged
    large2 = re.search(
        r"CommandSet\s+America_LargeAirBaseCommandSet\s*\n(.*?)End", cs2, re.S
    ).group(1)
    assert large2 == large_cs
    dmap["Data\\INI\\CommandSet.ini"] = cs2.encode("latin1")

    cb = dmap["Data\\INI\\CommandButton.ini"].decode("latin1")
    # Preserve existing bomber buttons
    for btn in [
        "Command_ConstructAmericaJetB2Spirit",
        "Command_ConstructAmericaJetB21",
        "Command_ConstructAmericaJetB52H",
        "Command_ConstructAmericaJetB1R",
        "Command_ConstructAmericaJetE3AWACS",
    ]:
        assert re.search(rf"^CommandButton\s+{btn}\s*$", cb, re.M), btn
    dmap["Data\\INI\\CommandButton.ini"] = ensure_buttons(cb).encode("latin1")

    mi_key = "Data\\INI\\MappedImages\\HandCreated\\HandCreatedMappedImages.INI"
    dmap[mi_key] = ensure_mapped_c17(dmap[mi_key].decode("latin1")).encode("latin1")

    # ART imports for C-17 only (AC-130 already in ART)
    art_files = {
        "Art\\W3D\\IUAC17HXNew.W3D": DONOR / "w3d" / "IUAC17HXNew.W3D",
        "Art\\Textures\\IUCC17THXNew.dds": DONOR / "Textures" / "IUCC17THXNew.dds",
        "Art\\Textures\\C17GlobalMaster.tga": DONOR / "Textures" / "C17GlobalMaster.tga",
    }
    added = []
    for dest, src in art_files.items():
        if not src.exists():
            raise SystemExit(f"Missing donor ART {src}")
        if dest.lower() not in {k.lower() for k in amap}:
            amap[dest] = src.read_bytes()
            added.append(dest)

    # Required existing AC-130 ART
    for need in ["Art\\W3D\\US_AC130W.W3D", "Art\\Textures\\US_AC130W.dds"]:
        if need.lower() not in {k.lower() for k in amap}:
            raise SystemExit(f"AC-130 ART missing: {need}")

    new_data = build_big(dmap)
    new_art = build_big(amap)
    DATA_BIG.write_bytes(new_data)
    ART_BIG.write_bytes(new_art)

    # Re-extract verify
    import shutil

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    VERIFY.mkdir(parents=True)
    ve, vb = read_big(DATA_BIG)
    vmap = {n.replace("/", "\\"): vb[o : o + s] for n, o, s in ve}
    ae, ab = read_big(ART_BIG)
    anames = {n.lower().replace("/", "\\") for n, _, _ in ae}

    assert sha256(vmap["Data\\English\\generals.csf"]) == GOOD_CSF
    assert (
        vmap[
            "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini"
        ]
        == b21
    )
    assert vmap[b1r_key] == b1r

    vcs = vmap["Data\\INI\\CommandSet.ini"].decode("latin1")
    hm = re.search(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)End", vcs, re.S
    )
    body = hm.group(1)
    assert "Command_ConstructAmericaJetB2Spirit" in body
    assert "Command_ConstructAmericaJetB21" in body
    assert "Command_ConstructAmericaJetB52H" in body
    assert "Command_ConstructAmericaJetB1R" in body
    assert "Command_ConstructAmericaJetE3AWACS" in body
    assert "Command_ConstructAmericaJetAC130" in body
    assert "Command_ConstructAmericaJetC17Globemaster" in body
    assert not re.search(
        r"B2Spirit|B21|B52H|AC130|C17",
        re.search(
            r"CommandSet\s+America_LargeAirBaseCommandSet\s*\n(.*?)End", vcs, re.S
        ).group(1),
    )

    vcb = vmap["Data\\INI\\CommandButton.ini"].decode("latin1")
    for btn, obj in [
        ("Command_ConstructAmericaJetAC130", "AmericaJetAC130"),
        ("Command_ConstructAmericaJetC17Globemaster", "AmericaJetC17Globemaster"),
        ("Command_ConstructAmericaJetE3AWACS", "AmericaJetE3AWACS"),
    ]:
        m = re.search(rf"CommandButton\s+{btn}\s*\n(.*?)End", vcb, re.S)
        assert m and "UNIT_BUILD" in m.group(0) and obj in m.group(0), btn

    for key, needle in [
        (
            "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini",
            b"Object AmericaJetAC130",
        ),
        (
            "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Globemaster.ini",
            b"Object AmericaJetC17Globemaster",
        ),
    ]:
        blob = vmap[key]
        assert needle in blob
        assert b"Ignore_Prerequisites" in blob
        assert b"JetAIUpdate" in blob
        assert b"AmericaStrategyCenter" not in blob
        assert b"SCIENCE_Rank4" not in blob

    ac = vmap[
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
    ].decode("latin1")
    assert "US_AC130W" in ac and "M102_105mm_Howitzer" in ac
    c17 = vmap[
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Globemaster.ini"
    ].decode("latin1")
    assert "IUAC17HXNew" in c17 and "US_C130H" not in c17

    for need in [
        "art\\w3d\\us_ac130w.w3d",
        "art\\textures\\us_ac130w.dds",
        "art\\w3d\\iuac17hxnew.w3d",
        "art\\textures\\iucc17thxnew.dds",
        "art\\textures\\c17globalmaster.tga",
    ]:
        assert need in anames, need

    report = hm.group(0) + f"\nART added={added}\nCSF ok\n"
    (VERIFY / "VERIFY.txt").write_text(report, encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
        z.write(ART_BIG, "_SPEC_ART_ONE.big")

    dsha, asha = sha256(DATA_BIG), sha256(ART_BIG)
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={dsha}\n_SPEC_ART_ONE.big sha256={asha}\n"
        f"ART added={added}\nZIP={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
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
        timeout=300,
    )
    url = (proc.stdout or "").strip()
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print("DATA", dsha)
    print("ART", asha)
    print("URL", url)
    print(report)


if __name__ == "__main__":
    main()
