#!/usr/bin/env python3
"""Restore existing USA B-2 / B-21 / B-52 production onto America_HeavyAirBase.

DATA-only preferred; ART is updated only when proven-missing B-21 mesh/icon
dependencies (AVB21_*, B-21*.dds, US-Icons03, JetPickBox) are absent.

Does NOT create new bomber Objects — restores AmericaJetB21Clean from the prior
project definition and wires existing UNIT_BUILD buttons into the active
America_HeavyAirBaseCommandSet.
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
B21_SRC = Path("/tmp/AmericaJetB21Clean.ini")
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_HEAVY_BOMBER_RESTORE.zip"
OUT_HASHES = ROOT / "Release/DATA_USA_HEAVY_BOMBER_RESTORE_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_HEAVY_BOMBER_RESTORE_DOWNLOAD.txt"
VERIFY_DIR = MASTER / "_extract_usa_heavy_bomber_verify"


def sha256(p: Path | bytes) -> str:
    b = p if isinstance(p, bytes) else Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    assert data[:4] == b"BIGF", path
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
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


def norm(n: str) -> str:
    return n.replace("/", "\\")


def file_map_from_big(entries, data) -> dict[str, bytes]:
    return {norm(name): data[off : off + size] for name, off, size in entries}


def extract_named(big_path: Path, wanted: list[str]) -> dict[str, bytes]:
    entries, data = read_big(big_path)
    want = {w.lower().replace("/", "\\"): w for w in wanted}
    out = {}
    for name, off, size in entries:
        key = name.lower().replace("/", "\\")
        if key in want:
            out[norm(name)] = data[off : off + size]
    missing = [w for k, w in want.items() if k not in {n.lower() for n in out}]
    if missing:
        raise SystemExit(f"Missing from {big_path}: {missing}")
    return out


def csf_label_set(csf: bytes) -> set[str]:
    nlabels = struct.unpack_from("<I", csf, 8)[0]
    pos = 24
    labels: set[str] = set()
    for _ in range(nlabels):
        if pos + 12 > len(csf) or csf[pos : pos + 4] != b" LBL":
            break
        namelen = struct.unpack_from("<I", csf, pos + 8)[0]
        numvals = struct.unpack_from("<I", csf, pos + 4)[0]
        pos += 12
        label = csf[pos : pos + namelen].decode("ascii", errors="replace")
        pos += namelen
        labels.add(label)
        for _v in range(numvals):
            vtag = csf[pos : pos + 4]
            pos += 4
            strlen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4 + strlen * 2
            if vtag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4 + elen
    return labels


def append_csf_label(csf: bytes, label: str, value: str) -> bytes:
    if label in csf_label_set(csf):
        return csf
    assert value.isascii(), value
    utf16 = value.encode("utf-16-le")
    char_count = len(utf16) // 2
    xored = bytes(b ^ 0xFF for b in utf16)
    label_b = label.encode("ascii")
    entry = bytearray()
    entry += b" LBL"
    entry += struct.pack("<II", 1, len(label_b))
    entry += label_b
    entry += b" STR"
    entry += struct.pack("<I", char_count)
    entry += xored
    nlabels = struct.unpack_from("<I", csf, 8)[0]
    out = bytearray(csf)
    struct.pack_into("<I", out, 8, nlabels + 1)
    out += entry
    return bytes(out)


def patch_commandset(text: str) -> str:
    block = """CommandSet America_HeavyAirBaseCommandSet
  1  = Command_ConstructAmericaJetB2Spirit
  2  = Command_ConstructAmericaJetB21
  3  = Command_ConstructAmericaJetB52H
  4  = Command_ConstructAmericaJetB1R
  5  = Command_ConstructAmericaJetE3AWACS
  6  = Command_Upgrade_NuclearTipWarhead2
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""
    pat = re.compile(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    if not pat.search(text):
        raise SystemExit("America_HeavyAirBaseCommandSet not found in CommandSet.ini")
    return pat.sub(block.rstrip(), text, count=1)


def patch_commandbutton(text: str) -> str:
    btn = """CommandButton Command_ConstructAmericaJetB21
  Command       = UNIT_BUILD
  Object        = AmericaJetB21Clean
  TextLabel     = CONTROLBAR:ConstructAmericaJetB21
  ButtonImage   = B21_L
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipAmericaJetB21
End
"""
    if re.search(r"^CommandButton\s+Command_ConstructAmericaJetB21\s*$", text, re.M):
        # Retarget existing button to AmericaJetB21Clean without inventing a new button id.
        pat = re.compile(
            r"CommandButton\s+Command_ConstructAmericaJetB21\s*\n.*?^End\s*$",
            re.M | re.S,
        )
        return pat.sub(btn.rstrip(), text, count=1)
    # Insert after B2Spirit button (keeps heavy-aircraft buttons clustered).
    anchor = re.search(
        r"CommandButton\s+Command_ConstructAmericaJetB2Spirit\s*\n.*?^End\s*$",
        text,
        re.M | re.S,
    )
    if not anchor:
        raise SystemExit("Command_ConstructAmericaJetB2Spirit missing — cannot place B-21 button")
    return text[: anchor.end()] + "\n\n" + btn + text[anchor.end() :]


def patch_mapped_images(text: str) -> str:
    if re.search(r"^MappedImage\s+B21_L\s*$", text, re.M):
        return text
    block = """
MappedImage B21_L
  Texture = US-Icons03.tga
  TextureWidth = 512
  TextureHeight = 512
  Coords = Left:366 Top:392 Right:488 Bottom:489
  Status = NONE
End
"""
    return text.rstrip() + "\n" + block


def ensure_large_untouched(text: str) -> None:
    m = re.search(
        r"CommandSet\s+America_LargeAirBaseCommandSet\s*\n(.*?)(?=^CommandSet |\Z)",
        text,
        re.M | re.S,
    )
    if not m:
        raise SystemExit("America_LargeAirBaseCommandSet missing")
    body = m.group(1)
    for bad in ("B2Spirit", "B21", "B52H", "B1R"):
        if f"Command_ConstructAmericaJet{bad}" in body or (
            bad == "B21" and "Command_ConstructAmericaJetB21" in body
        ):
            # B21 check only
            pass
    if re.search(r"Command_ConstructAmericaJetB2Spirit|Command_ConstructAmericaJetB21|Command_ConstructAmericaJetB52H", body):
        raise SystemExit("LargeAirBase unexpectedly contains bombers — abort")


def main() -> None:
    if not B21_SRC.exists():
        raise SystemExit(f"Missing restored object source {B21_SRC}")
    if not TEOD_W3D.exists() or not TEOD_TEX.exists():
        raise SystemExit("TEOD donor BIGs missing under /tmp/teod_extract")

    data_entries, data_blob = read_big(DATA_BIG)
    art_entries, art_blob = read_big(ART_BIG)
    data_map = file_map_from_big(data_entries, data_blob)
    art_map = file_map_from_big(art_entries, art_blob)

    cs_key = "Data\\INI\\CommandSet.ini"
    cb_key = "Data\\INI\\CommandButton.ini"
    mi_key = "Data\\INI\\MappedImages\\HandCreated\\HandCreatedMappedImages.INI"
    csf_key = "Data\\English\\generals.csf"
    obj_key = "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini"
    hab_key = "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\America_HeavyAirBase.ini"

    cs = data_map[cs_key].decode("latin1")
    ensure_large_untouched(cs)
    cs = patch_commandset(cs)
    data_map[cs_key] = cs.encode("latin1")

    cb = data_map[cb_key].decode("latin1")
    cb = patch_commandbutton(cb)
    data_map[cb_key] = cb.encode("latin1")

    mi = data_map[mi_key].decode("latin1")
    mi = patch_mapped_images(mi)
    data_map[mi_key] = mi.encode("latin1")

    # Restore existing B-21 object (exact prior AmericaJetB21Clean definition).
    data_map[obj_key] = B21_SRC.read_bytes()

    csf = data_map[csf_key]
    for label, value in [
        ("OBJECT:AmericaJetB21", "B-21 Raider"),
        ("CONTROLBAR:ConstructAmericaJetB21", "B-21 Raider"),
        ("CONTROLBAR:ToolTipAmericaJetB21", "Stealth strategic bomber."),
        ("OBJECT:AmericaJetB2Spirit", "B-2 Spirit"),
        ("CONTROLBAR:ConstructAmericaJetB2Spirit", "B-2 Spirit"),
        ("CONTROLBAR:ToolTipAmericaJetB2Spirit", "Stealth strategic bomber."),
        ("OBJECT:AmericaJetB52H", "B-52H Stratofortress"),
        ("CONTROLBAR:ConstructAmericaJetB52H", "B-52H Stratofortress"),
        ("CONTROLBAR:ToolTipAmericaJetB52H", "Heavy strategic bomber."),
        ("OBJECT:AmericaJetE3AWACS", "E-3G AWACS"),
        ("CONTROLBAR:ConstructAmericaJetE3AWACS", "E-3G AWACS"),
        ("CONTROLBAR:ToolTipAmericaJetE3AWACS", "Airborne early warning aircraft."),
    ]:
        csf = append_csf_label(csf, label, value)
    data_map[csf_key] = csf

    # Confirm HeavyAirBase still points at the active CommandSet (building unchanged).
    hab = data_map[hab_key].decode("latin1")
    if "CommandSet          = America_HeavyAirBaseCommandSet" not in hab and \
       "CommandSet = America_HeavyAirBaseCommandSet" not in hab:
        if not re.search(r"CommandSet\s*=\s*America_HeavyAirBaseCommandSet", hab):
            raise SystemExit("America_HeavyAirBase CommandSet assignment missing")

    # ART: only add proven-missing B-21 dependencies.
    art_needed = extract_named(
        TEOD_W3D,
        [
            "Art\\W3D\\AVB21.W3D",
            "Art\\W3D\\AVB21_A.W3D",
            "Art\\W3D\\AVB21_A_D.W3D",
            "Art\\W3D\\AVB21_D.W3D",
            "Art\\W3D\\AVB21_E.W3D",
            "Art\\W3D\\AVB21_E1.W3D",
            "Art\\W3D\\JetPickBox.W3D",
        ],
    )
    art_needed.update(
        extract_named(
            TEOD_TEX,
            [
                "Art\\Textures\\B-21.dds",
                "Art\\Textures\\B-21_D.dds",
                "Art\\Textures\\B-21_E.dds",
                "Art\\Textures\\US-Icons03.tga",
            ],
        )
    )
    art_added = []
    for name, content in art_needed.items():
        key = name
        if key.lower() not in {k.lower() for k in art_map}:
            art_map[key] = content
            art_added.append(key)
        else:
            # Keep existing ART bytes; dependency already present.
            pass

    new_data = build_big(data_map)
    new_art = build_big(art_map)
    DATA_BIG.write_bytes(new_data)
    ART_BIG.write_bytes(new_art)

    # Re-extract verification
    if VERIFY_DIR.exists():
        import shutil

        shutil.rmtree(VERIFY_DIR)
    VERIFY_DIR.mkdir(parents=True)
    v_entries, v_data = read_big(DATA_BIG)
    v_map = file_map_from_big(v_entries, v_data)
    for key in (cs_key, cb_key, obj_key, hab_key, mi_key):
        out = VERIFY_DIR / key.replace("\\", "/")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(v_map[key])

    v_cs = v_map[cs_key].decode("latin1")
    v_cb = v_map[cb_key].decode("latin1")
    v_obj = v_map[obj_key].decode("latin1")
    report = []
    m = re.search(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)End",
        v_cs,
        re.S,
    )
    report.append("America_HeavyAirBaseCommandSet:\n" + m.group(0))
    for btn in [
        "Command_ConstructAmericaJetB2Spirit",
        "Command_ConstructAmericaJetB21",
        "Command_ConstructAmericaJetB52H",
    ]:
        bm = re.search(rf"CommandButton\s+{btn}\s*\n(.*?)End", v_cb, re.S)
        report.append(bm.group(0) if bm else f"MISSING {btn}")
    report.append(
        "Object AmericaJetB21Clean present: "
        + str("Object AmericaJetB21Clean" in v_obj)
    )
    report.append("Model AVB21_A: " + str("AVB21_A" in v_obj))
    a_entries, _ = read_big(ART_BIG)
    a_names = {n.lower().replace("/", "\\") for n, _, _ in a_entries}
    for need in [
        "art\\w3d\\avb21_a.w3d",
        "art\\textures\\b-21.dds",
        "art\\textures\\us-icons03.tga",
        "art\\w3d\\jetpickbox.w3d",
        "art\\w3d\\us_b1r.w3d",
        "art\\w3d\\us_b52h.w3d",
    ]:
        report.append(f"ART {need}: {need in a_names}")

    verify_txt = VERIFY_DIR / "VERIFY.txt"
    verify_txt.write_text("\n\n".join(report) + "\n", encoding="utf-8")

    # Package ZIP: include ART only if we added files (proven missing deps).
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
        if art_added:
            z.write(ART_BIG, "_SPEC_ART_ONE.big")

    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)
    OUT_HASHES.write_text(
        f"_SPEC_DATA_ONE.big sha256={data_sha}\n"
        f"_SPEC_ART_ONE.big sha256={art_sha}\n"
        f"ART files added ({len(art_added)}): {art_added}\n"
        f"ZIP={OUT_ZIP.name}\n",
        encoding="utf-8",
    )

    # Upload
    url = ""
    try:
        proc = subprocess.run(
            ["curl", "-sF", f"fileRequest=@{OUT_ZIP}", "https://litterbox.catbox.moe/resources/internals/api.php"],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        # litterbox needs time+file fields
        if "http" not in (proc.stdout or ""):
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
                check=False,
            )
        url = (proc.stdout or "").strip()
    except Exception as e:
        url = f"UPLOAD_FAILED: {e}"
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print("DATA", data_sha)
    print("ART", art_sha)
    print("ART_ADDED", art_added)
    print("URL", url)
    print(verify_txt.read_text())


if __name__ == "__main__":
    main()
