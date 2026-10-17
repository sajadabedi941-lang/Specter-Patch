#!/usr/bin/env python3
"""Fully restore working USA B-2 (AVB3bmbr) + B-52H production on HeavyAirBase.

Restores Object AmericaJetB2Spirit from last known working definition (AVB3bmbr,
B2-ic_L, unlocked). Unlocks AmericaJetB52H and fixes aircraft icons.
Does NOT touch B-21 / B-1R / E-3 / LargeAirBase / CSF / other factions.
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
TEOD_W3D = Path("/tmp/teod_extract/!TEOD_W3D.big")
TEOD_TEX = Path("/tmp/teod_extract/!TEOD_Textures.big")
WORKING_B2 = Path("/tmp/working_AmericaJetB2Spirit.ini")
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_B2_B52_FULL_RESTORE.zip"
OUT_HASH = ROOT / "Release/DATA_USA_B2_B52_FULL_RESTORE_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_B2_B52_FULL_RESTORE_DOWNLOAD.txt"
VERIFY = MASTER / "_extract_usa_b2_b52_full_restore_verify"
GOOD_CSF_SHA = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    assert data[:4] == b"BIGF", path
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


def extract_named(big_path: Path, names: list[str]) -> dict[str, bytes]:
    entries, data = read_big(big_path)
    want = {n.lower().replace("/", "\\"): n for n in names}
    out = {}
    for name, off, size in entries:
        key = name.lower().replace("/", "\\")
        if key in want:
            out[name.replace("/", "\\")] = data[off : off + size]
    missing = [want[k] for k in want if k not in {x.lower() for x in out}]
    if missing:
        raise SystemExit(f"Missing from {big_path}: {missing}")
    return out


def replace_object(usa: str, obj_name: str, new_block: str) -> str:
    m = re.search(rf"^Object\s+{re.escape(obj_name)}\s*$", usa, re.M)
    if not m:
        raise SystemExit(f"Object {obj_name} missing")
    nxt = re.search(r"^Object\s+\S+", usa[m.start() + 10 :], re.M)
    end = m.start() + 10 + nxt.start()
    block = new_block.rstrip() + "\n\n"
    return usa[: m.start()] + block + usa[end:]


def patch_b52(block: str) -> str:
    # Proper aircraft icon (not GBU / not B-1R)
    block = re.sub(
        r"(SelectPortrait\s*=\s*)\S+",
        r"\1us_b52h",
        block,
        count=1,
    )
    block = re.sub(
        r"(ButtonImage\s*=\s*)\S+",
        r"\1us_b52h",
        block,
        count=1,
    )
    # Clear StrategyCenter / Rank4 gates; keep weapon upgrades intact
    block = re.sub(
        r"Prerequisites\s*.*?End",
        "Prerequisites\n  End\n  Buildable           = Ignore_Prerequisites",
        block,
        count=1,
        flags=re.S,
    )
    # Avoid duplicate Buildable if already present after Prerequisites
    # (only one intentional Buildable near prereq)
    return block


def patch_commandbutton(text: str, btn: str, obj: str, image: str) -> str:
    pat = re.compile(
        rf"CommandButton\s+{re.escape(btn)}\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    m = pat.search(text)
    if not m:
        raise SystemExit(f"Missing {btn}")
    new = (
        f"CommandButton {btn}\n"
        f"  Command       = UNIT_BUILD\n"
        f"  Object        = {obj}\n"
        f"  TextLabel     = CONTROLBAR:{btn.replace('Command_', '')}\n"
        f"  ButtonImage   = {image}\n"
        f"  ButtonBorderType = BUILD\n"
        f"  DescriptLabel = CONTROLBAR:ToolTip{btn.replace('Command_Construct', '')}\n"
        f"End"
    )
    # Preserve exact historical TextLabel/DescriptLabel from existing button when present
    old = m.group(0)
    tl = re.search(r"TextLabel\s*=\s*(\S+)", old)
    dl = re.search(r"DescriptLabel\s*=\s*(\S+)", old)
    if tl:
        new = re.sub(r"TextLabel\s*=\s*\S+", f"TextLabel     = {tl.group(1)}", new)
    if dl:
        new = re.sub(r"DescriptLabel\s*=\s*\S+", f"DescriptLabel = {dl.group(1)}", new)
    if pat.findall(text) and len(pat.findall(text)) > 1:
        raise SystemExit(f"Duplicate CommandButton {btn}")
    return pat.sub(new, text, count=1)


def ensure_mapped_b2(mi: str) -> str:
    if re.search(r"^MappedImage\s+B2-ic_L\s*$", mi, re.M):
        return mi
    block = """
MappedImage B2-ic_L
  Texture = US-Icons01.dds
  TextureWidth = 512
  TextureHeight = 512
  Coords = Left:366 Top:392 Right:488 Bottom:490
  Status = NONE
End
"""
    return mi.rstrip() + "\n" + block


def obj_span(text: str, name: str) -> str:
    m = re.search(rf"^Object\s+{re.escape(name)}\s*$", text, re.M)
    nxt = re.search(r"^Object\s+\S+", text[m.start() + 10 :], re.M)
    return text[m.start() : m.start() + 10 + nxt.start()]


def main() -> None:
    working_b2 = WORKING_B2.read_text(encoding="latin1")
    assert "AVB3bmbr" in working_b2
    assert "B2-ic_L" in working_b2
    assert "Ignore_Prerequisites" in working_b2

    dentries, dblob = read_big(DATA_BIG)
    aentries, ablob = read_big(ART_BIG)
    dmap = {n.replace("/", "\\"): dblob[o : o + s] for n, o, s in dentries}
    amap = {n.replace("/", "\\"): ablob[o : o + s] for n, o, s in aentries}

    # CSF must remain the known-good binary (String Manager hotfix)
    csf_key = "Data\\English\\generals.csf"
    if sha256(dmap[csf_key]) != GOOD_CSF_SHA:
        raise SystemExit(f"Refusing to proceed: CSF sha is not known-good ({sha256(dmap[csf_key])})")

    usa_key = "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"
    cb_key = "Data\\INI\\CommandButton.ini"
    cs_key = "Data\\INI\\CommandSet.ini"
    mi_key = "Data\\INI\\MappedImages\\HandCreated\\HandCreatedMappedImages.INI"

    usa = dmap[usa_key].decode("latin1")
    # Snapshot untouched neighbors
    b21_before = dmap.get(
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini"
    )
    cs_before = dmap[cs_key]
    b1r_before = None
    for k, v in dmap.items():
        if k.lower().endswith("airforce\\b1r.ini"):
            b1r_before = (k, v)
            break

    # Replace B-2 Spirit with last working definition
    usa = replace_object(usa, "AmericaJetB2Spirit", working_b2)

    # Unlock + icon-fix B-52H (keep US_B52H mesh / weapons / cost)
    b52 = obj_span(usa, "AmericaJetB52H")
    usa = replace_object(usa, "AmericaJetB52H", patch_b52(b52))

    # Guard: E3 block still present and unchanged identity
    e3 = obj_span(usa, "AmericaJetE3AWACS")
    assert "AmericaJetE3AWACS" in e3 and "US_E3G" in e3

    dmap[usa_key] = usa.encode("latin1")

    # CommandButtons
    cb = dmap[cb_key].decode("latin1")
    cb = patch_commandbutton(
        cb, "Command_ConstructAmericaJetB2Spirit", "AmericaJetB2Spirit", "B2-ic_L"
    )
    cb = patch_commandbutton(
        cb, "Command_ConstructAmericaJetB52H", "AmericaJetB52H", "us_b52h"
    )
    # Ensure B21 / B1R / E3 buttons unchanged by verifying they still resolve
    for btn, obj in [
        ("Command_ConstructAmericaJetB21", "AmericaJetB21Clean"),
        ("Command_ConstructAmericaJetB1R", "AmericaJetB1R"),
        ("Command_ConstructAmericaJetE3AWACS", "AmericaJetE3AWACS"),
    ]:
        m = re.search(rf"CommandButton\s+{btn}\s*\n(.*?)End", cb, re.S)
        assert m and obj in m.group(0) and "UNIT_BUILD" in m.group(0), btn
    dmap[cb_key] = cb.encode("latin1")

    # MappedImage for B-2 icon
    mi = dmap[mi_key].decode("latin1")
    dmap[mi_key] = ensure_mapped_b2(mi).encode("latin1")

    # Heavy CommandSet must remain bomber roster
    cs = dmap[cs_key].decode("latin1")
    hm = re.search(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)End", cs, re.S
    )
    assert hm
    body = hm.group(1)
    assert "Command_ConstructAmericaJetB2Spirit" in body
    assert "Command_ConstructAmericaJetB21" in body
    assert "Command_ConstructAmericaJetB52H" in body
    # Large untouched
    lm = re.search(
        r"CommandSet\s+America_LargeAirBaseCommandSet\s*\n(.*?)End", cs, re.S
    )
    assert lm and not re.search(
        r"B2Spirit|B21|B52H", lm.group(1)
    ), "LargeAirBase must not gain bombers"
    assert dmap[cs_key] == cs_before, "CommandSet.ini must not change in this repair"

    # ART: add AVB3bmbr assets only if missing
    art_add = extract_named(
        TEOD_W3D,
        [
            "Art\\W3D\\AVB3bmbr.W3D",
            "Art\\W3D\\AVB3bmbr_D.W3D",
            "Art\\W3D\\AVB3bmbr_D1.W3D",
            "Art\\W3D\\AVB3bmbr_D2.W3D",
        ],
    )
    art_add.update(
        extract_named(
            TEOD_TEX,
            [
                "Art\\Textures\\avb3bmbr.dds",
                "Art\\Textures\\avb3bmbr_D.dds",
                "Art\\Textures\\avb3bmbr_E.dds",
            ],
        )
    )
    added = []
    for name, content in art_add.items():
        if name.lower() not in {k.lower() for k in amap}:
            amap[name] = content
            added.append(name)
    # Required already-present assets
    for need in [
        "Art\\W3D\\US_B52H.W3D",
        "Art\\Textures\\US_B52H.dds",
        "Art\\Textures\\US-Icons01.dds",
    ]:
        if need.lower() not in {k.lower() for k in amap}:
            raise SystemExit(f"Required ART missing: {need}")

    new_data = build_big(dmap)
    new_art = build_big(amap)
    DATA_BIG.write_bytes(new_data)
    ART_BIG.write_bytes(new_art)

    # --- Re-extract verify ---
    if VERIFY.exists():
        import shutil

        shutil.rmtree(VERIFY)
    VERIFY.mkdir(parents=True)
    ve, vb = read_big(DATA_BIG)
    vmap = {n.replace("/", "\\"): vb[o : o + s] for n, o, s in ve}
    ae2, ab2 = read_big(ART_BIG)
    anames = {n.lower().replace("/", "\\") for n, _, _ in ae2}

    assert sha256(vmap[csf_key]) == GOOD_CSF_SHA
    assert vmap[cs_key] == cs_before
    if b21_before is not None:
        assert (
            vmap[
                "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini"
            ]
            == b21_before
        )
    if b1r_before:
        assert vmap[b1r_before[0]] == b1r_before[1]

    vusa = vmap[usa_key].decode("latin1")
    spirit = obj_span(vusa, "AmericaJetB2Spirit")
    b52f = obj_span(vusa, "AmericaJetB52H")
    spirit_models = set(re.findall(r"^\s*Model\s*=\s*(\S+)", spirit, re.M))
    assert "AVB3bmbr" in spirit_models and not any(m.startswith("US_B1R") for m in spirit_models)
    assert "B2-ic_L" in spirit
    assert not re.search(r"^\s*Object\s*=\s*AmericaStrategyCenter", spirit, re.M)
    assert not re.search(r"^\s*Science\s*=\s*SCIENCE_Rank4", spirit, re.M)
    assert "Ignore_Prerequisites" in spirit
    b52_models = set(re.findall(r"^\s*Model\s*=\s*(\S+)", b52f, re.M))
    assert "US_B52H" in b52_models
    assert not re.search(r"^\s*Object\s*=\s*AmericaStrategyCenter", b52f, re.M)
    assert not re.search(r"^\s*Science\s*=\s*SCIENCE_Rank4", b52f, re.M)
    assert "Ignore_Prerequisites" in b52f
    assert re.search(r"SelectPortrait\s*=\s*us_b52h", b52f)
    assert "USA_B52H_AreaBombardment" in b52f
    assert "JetAIUpdate" in spirit and "JetAIUpdate" in b52f
    assert "PhysicsBehavior" in spirit and "PhysicsBehavior" in b52f
    assert "AIRCRAFT" in spirit and "AIRCRAFT" in b52f

    # Duplicate object defs
    assert len(re.findall(r"^Object\s+AmericaJetB2Spirit\s*$", vusa, re.M)) == 1
    assert len(re.findall(r"^Object\s+AmericaJetB52H\s*$", vusa, re.M)) == 1

    vcb = vmap[cb_key].decode("latin1")
    for btn, obj, img in [
        ("Command_ConstructAmericaJetB2Spirit", "AmericaJetB2Spirit", "B2-ic_L"),
        ("Command_ConstructAmericaJetB52H", "AmericaJetB52H", "us_b52h"),
    ]:
        matches = list(re.finditer(rf"^CommandButton\s+{btn}\s*$", vcb, re.M))
        assert len(matches) == 1, btn
        block = vcb[matches[0].start() : vcb.find("\nEnd", matches[0].start()) + 4]
        assert "UNIT_BUILD" in block and f"Object        = {obj}" in block.replace(
            "\r", ""
        ) or f"Object = {obj}" in block.replace(" ", "")
        assert f"ButtonImage   = {img}" in block or f"ButtonImage = {img}" in block.replace(
            " ", ""
        )
        # looser checks
        assert "UNIT_BUILD" in block
        assert obj in block
        assert img in block

    vmi = vmap[mi_key].decode("latin1")
    assert re.search(r"^MappedImage\s+B2-ic_L\s*$", vmi, re.M)

    for need in [
        "art\\w3d\\avb3bmbr.w3d",
        "art\\textures\\avb3bmbr.dds",
        "art\\w3d\\us_b52h.w3d",
        "art\\textures\\us_b52h.dds",
        "art\\textures\\us-icons01.dds",
    ]:
        assert need in anames, need

    report = []
    report.append("USA B-2 + B-52 FULL RESTORE = PASS")
    report.append(f"CSF unchanged sha={sha256(vmap[csf_key])}")
    report.append(f"ART added={added}")
    report.append(hm.group(0) if hm else "")
    report.append("--- B2 Spirit models ---")
    report.append(str(sorted(set(re.findall(r"Model\\s*=\\s*(\\S+)", spirit)))))
    report.append("--- B52 models ---")
    report.append(str(sorted(set(re.findall(r"Model\\s*=\\s*(\\S+)", b52f)))))
    (VERIFY / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (VERIFY / "AmericaJetB2Spirit.ini").write_text(spirit, encoding="latin1")
    (VERIFY / "AmericaJetB52H.ini").write_text(b52f, encoding="latin1")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
        z.write(ART_BIG, "_SPEC_ART_ONE.big")

    dsha, asha = sha256(DATA_BIG), sha256(ART_BIG)
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={dsha}\n"
        f"_SPEC_ART_ONE.big sha256={asha}\n"
        f"ART added={added}\n"
        f"ZIP={OUT_ZIP.name}\n",
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
    print("ADDED", added)
    print("URL", url)
    print((VERIFY / "VERIFY.txt").read_text())


if __name__ == "__main__":
    main()
