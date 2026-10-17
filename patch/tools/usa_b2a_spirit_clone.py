#!/usr/bin/env python3
"""B-2A second bomber: clone working AmericaJetB2Spirit gameplay + donor AVB3bmbr visual.

- Freeze AmericaJetB2Spirit (Object + Slot 1 + CommandButton) completely
- Rewrite AmericaJetB2A as Spirit clone with B-2A identity + donor W3D family
- Slot 12 + Command_ConstructAmericaJetB2A
- CSF labels for visible name B-2A
"""
from __future__ import annotations

import hashlib
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
STAGE = MASTER / "_stage_usa_b2a_spirit_clone"
VERIFY = MASTER / "_extract_usa_b2a_spirit_clone_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_B2A_SPIRIT_CLONE.zip"
OUT_HASH = ROOT / "Release/DATA_USA_B2A_SPIRIT_CLONE_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_B2A_SPIRIT_CLONE_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_B2A_SPIRIT_CLONE_REPORT.txt"
SRC_DIR = ROOT / "Data/INI/Object/Specter/United States Of America"

OLD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"

SPIRIT_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"
)
B2A_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB2A.ini"
)
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"
CSF_KEY = "Data\\English\\generals.csf"
MI_KEY = "Data\\INI\\MappedImages\\HandCreated\\HandCreatedMappedImages.INI"
HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)

# Spirit CommandButton must stay exactly as currently packed (do not touch).
FREEZE_SPIRIT_BTN = "Command_ConstructAmericaJetB2Spirit"

B2A_BUTTON = """CommandButton Command_ConstructAmericaJetB2A
  Command       = UNIT_BUILD
  Object        = AmericaJetB2A
  TextLabel     = CONTROLBAR:AmericaJetB2A
  ButtonImage   = B2A
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipAmericaJetB2A
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


def count_obj(dmap: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(name)}\s*$")
    return sum(
        len(pat.findall(v.decode("latin1")))
        for k, v in dmap.items()
        if k.lower().endswith(".ini")
    )


def count_btn(dmap: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^CommandButton\s+{re.escape(name)}\s*$")
    return sum(
        len(pat.findall(v.decode("latin1")))
        for k, v in dmap.items()
        if k.lower().endswith(".ini")
    )


def extract_spirit(usa_system: bytes) -> str:
    t = usa_system.decode("latin1")
    m = re.search(
        r"(?ms)^Object\s+AmericaJetB2Spirit\s*\n.*?(?=^Object\s|\Z)", t
    )
    assert m, "AmericaJetB2Spirit missing"
    # trim trailing section comments after End of object
    block = m.group(0)
    # keep through final End of the object (last End before next Object)
    # The regex already stops at next Object; strip trailing blank/comment lines
    # after the object's closing End — find last standalone End at col 0? Spirit ends with "End\n\n\n;"
    lines = block.splitlines(True)
    # find last line that is exactly 'End' at object level - use first complete parse
    return block


def spirit_to_b2a(spirit_block: str) -> str:
    """Clone Spirit gameplay; retarget identity + portraits to B2A. Keep AVB3bmbr visual."""
    # Cut trailing commentary after the object's final End
    # Spirit block may include following comment banners — keep only through first top-level End after Object
    text = spirit_block
    # Normalize name
    text = re.sub(
        r"(?m)^Object\s+AmericaJetB2Spirit\s*$",
        "Object AmericaJetB2A",
        text,
        count=1,
    )
    text = text.replace("OBJECT:AmericaJetB2Spirit", "OBJECT:AmericaJetB2A")
    text = re.sub(
        r"(?m)^(\s*SelectPortrait\s*=\s*).*$",
        r"\1B2A",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(\s*ButtonImage\s*=\s*).*$",
        r"\1B2A",
        text,
        count=1,
    )
    # Header comment
    header = (
        ";==============================================================================\n"
        "; AmericaJetB2A - second B-2 variant (DISPLAY: B-2A)\n"
        "; Gameplay/syntax cloned from working AmericaJetB2Spirit\n"
        "; Visual = donor USAB2 family AVB3bmbr / AVB3bmbr_D / AVB3bmbr_D1\n"
        "; Donor gameplay DATA = NOT IMPORTED\n"
        ";==============================================================================\n\n"
    )
    # Ensure primary models remain donor AVB3bmbr family
    assert "AVB3bmbr" in text
    assert not re.search(r"(?m)^\s*Model\s*=\s*US_B1R\b", text)
    assert not re.search(r"(?m)^\s*Model\s*=\s*AVB21\b", text)
    # Strip any trailing content after final object End that isn't part of object
    # Find the End that closes Object: count nesting from Object line
    lines = text.splitlines()
    out_lines: list[str] = []
    stack: list[str] = []
    started = False
    for line in lines:
        s = line.strip()
        if not started:
            if s.startswith("Object "):
                started = True
                stack = ["Object"]
                out_lines.append(line)
            continue
        out_lines.append(line)
        if not s or s.startswith(";"):
            continue
        if re.match(
            r"^(Draw|Behavior|ArmorSet|WeaponSet|Body|UnitSpecificSounds|"
            r"Prerequisites|DefaultConditionState|ConditionState|"
            r"TransitionState|AliasConditionState)\b",
            s,
        ):
            stack.append(s.split()[0])
        elif s == "End":
            if not stack:
                break
            stack.pop()
            if not stack:
                break
    body = "\n".join(out_lines).rstrip() + "\n"
    assert "Object AmericaJetB2A" in body
    assert "Weapon = PRIMARY USA_B2_Spirit_BunkerBuster" in body
    assert "D30-F6_JetLocomotor" in body
    assert "Model               = AVB3bmbr" in body or "Model = AVB3bmbr" in body
    return header + body


def csf_encode_str(s: str) -> bytes:
    out = bytearray()
    for ch in s:
        out += struct.pack("<H", (~ord(ch)) & 0xFFFF)
    return bytes(out)


def csf_add_labels(csf: bytes, entries: list[tuple[str, str]]) -> bytes:
    """Append labels using same markers as packed generals.csf ( LBL /  RTS)."""
    assert csf[0:4] in (b" CSF", b" FSC")
    # packed file uses little-endian fourcc showing as ' FSC' for 'CSF '
    magic = csf[0:4]
    version, nlab, nstr, reserved = struct.unpack_from("<IIII", csf, 4)
    blob = bytearray(csf)
    for label, value in entries:
        # skip if already present
        if label.encode("ascii") in csf:
            # replace not needed if present
            continue
        lab = label.encode("ascii")
        val = csf_encode_str(value)
        # markers match existing file: b' LBL' and b' RTS'
        entry = bytearray()
        entry += b" LBL"
        entry += struct.pack("<II", 1, len(lab))
        entry += lab
        entry += b" RTS"
        entry += struct.pack("<I", len(value))
        entry += val
        blob += entry
        nlab += 1
        nstr += 1
    struct.pack_into("<IIII", blob, 4, version, nlab, nstr, reserved)
    # keep magic
    blob[0:4] = magic
    return bytes(blob)


def upsert_button(cb: str) -> str:
    block = B2A_BUTTON.rstrip()
    if re.search(r"(?m)^CommandButton\s+Command_ConstructAmericaJetB2A\s*$", cb):
        cb2, n = re.subn(
            r"(?ms)^CommandButton\s+Command_ConstructAmericaJetB2A\s*\n.*?^End\s*$",
            block,
            cb,
            count=1,
        )
        assert n == 1
        return cb2
    m = re.search(
        r"(?ms)^CommandButton\s+Command_ConstructAmericaJetB2Spirit\s*\n.*?^End\s*$",
        cb,
    )
    assert m
    return cb[: m.end()] + "\n\n" + block + "\n" + cb[m.end() :]


def ensure_slot12(cs: str) -> str:
    def repl(m: re.Match[str]) -> str:
        body = m.group(0)
        if re.search(r"(?m)^\s*12\s*=", body):
            body2, n = re.subn(
                r"(?m)^(\s*12\s*=\s*).*$",
                r"\1Command_ConstructAmericaJetB2A",
                body,
                count=1,
            )
            assert n == 1
        else:
            body2, n = re.subn(
                r"(?m)^(\s*13\s*=\s*Command_SetRallyPoint\s*)$",
                "  12 = Command_ConstructAmericaJetB2A\n\\1",
                body,
                count=1,
            )
            assert n == 1
        assert re.search(
            r"(?m)^\s*1\s*=\s*Command_ConstructAmericaJetB2Spirit\s*$", body2
        )
        assert re.search(
            r"(?m)^\s*12\s*=\s*Command_ConstructAmericaJetB2A\s*$", body2
        )
        return body2

    cs2, n = re.subn(
        r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?^End\s*$",
        repl,
        cs,
        count=1,
    )
    assert n == 1
    return cs2


def get_btn_block(cb: str, name: str) -> str:
    m = re.search(
        rf"(?ms)^CommandButton\s+{re.escape(name)}\s*\n.*?^End\s*$", cb
    )
    assert m, name
    return m.group(0)


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
    art = read_big(ART_BIG)
    assert sha256(data[CSF_KEY]) == OLD_CSF

    # Donor / ART visual family present
    for k in (
        "Art\\W3D\\AVB3bmbr.W3D",
        "Art\\W3D\\AVB3bmbr_D.W3D",
        "Art\\W3D\\AVB3bmbr_D1.W3D",
        "Art\\Textures\\avb3bmbr.dds",
        "Art\\Textures\\B2ATB.tga",
        "Art\\Textures\\B2A.tga",
    ):
        assert k in art, f"missing ART {k}"

    spirit_file_before = data[SPIRIT_KEY]
    spirit_btn_before = get_btn_block(
        data[CB_KEY].decode("latin1"), FREEZE_SPIRIT_BTN
    )
    heavy_before = data[HEAVY_KEY]

    spirit_block = extract_spirit(spirit_file_before)
    b2a_text = spirit_to_b2a(spirit_block)
    b2a_blob = b2a_text.encode("latin1")

    cb = data[CB_KEY].decode("latin1")
    cs = data[CS_KEY].decode("latin1")
    mi = data[MI_KEY].decode("latin1")
    assert re.search(r"(?m)^MappedImage\s+B2A\s*$", mi), "MappedImage B2A required"

    cb2 = upsert_button(cb)
    # Spirit button frozen
    assert get_btn_block(cb2, FREEZE_SPIRIT_BTN) == spirit_btn_before
    cs2 = ensure_slot12(cs)

    csf2 = csf_add_labels(
        data[CSF_KEY],
        [
            ("OBJECT:AmericaJetB2A", "B-2A"),
            ("CONTROLBAR:AmericaJetB2A", "B-2A"),
            ("CONTROLBAR:ToolTipAmericaJetB2A", "B-2A stealth bomber"),
        ],
    )
    assert sha256(csf2) != OLD_CSF
    assert b"CONTROLBAR:AmericaJetB2A" in csf2
    assert b"OBJECT:AmericaJetB2A" in csf2

    data2 = dict(data)
    data2[B2A_KEY] = b2a_blob
    data2[CB_KEY] = cb2.replace("\r\n", "\n").encode("latin1")
    data2[CS_KEY] = cs2.replace("\r\n", "\n").encode("latin1")
    data2[CSF_KEY] = csf2
    # hard freeze Spirit object file + heavy airbase building
    data2[SPIRIT_KEY] = spirit_file_before
    data2[HEAVY_KEY] = heavy_before

    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    write_tree(data2, STAGE / "in")

    # ART unchanged this pass
    art_sha_before = sha256(ART_BIG)
    DATA_BIG.write_bytes(build_big(data2))

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    dv = read_big(DATA_BIG)
    write_tree(dv, VERIFY / "out")

    assert dv[SPIRIT_KEY] == spirit_file_before
    assert dv[HEAVY_KEY] == heavy_before
    assert get_btn_block(dv[CB_KEY].decode("latin1"), FREEZE_SPIRIT_BTN) == spirit_btn_before
    assert count_obj(dv, "AmericaJetB2Spirit") == 1
    assert count_obj(dv, "AmericaJetB2A") == 1
    assert count_btn(dv, "Command_ConstructAmericaJetB2A") == 1
    assert count_btn(dv, "Command_ConstructAmericaJetB2Spirit") == 1

    b2a = dv[B2A_KEY].decode("latin1")
    assert "Object AmericaJetB2A" in b2a
    assert "OBJECT:AmericaJetB2A" in b2a
    assert "SelectPortrait         = B2A" in b2a or "SelectPortrait = B2A" in b2a
    assert "ButtonImage            = B2A" in b2a or "ButtonImage = B2A" in b2a
    assert "AVB3bmbr" in b2a
    assert "USA_B2_Spirit_BunkerBuster" in b2a
    assert "D30-F6_JetLocomotor" in b2a
    assert "JetAIUpdate" in b2a

    hab = re.search(
        r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?^End\s*$",
        dv[CS_KEY].decode("latin1"),
    ).group(0)
    assert re.search(r"(?m)^\s*1\s*=\s*Command_ConstructAmericaJetB2Spirit\s*$", hab)
    assert re.search(r"(?m)^\s*12\s*=\s*Command_ConstructAmericaJetB2A\s*$", hab)

    btn = get_btn_block(dv[CB_KEY].decode("latin1"), "Command_ConstructAmericaJetB2A")
    assert "Object        = AmericaJetB2A" in btn
    assert "ButtonImage   = B2A" in btn

    assert b"CONTROLBAR:AmericaJetB2A" in dv[CSF_KEY]
    assert sha256(ART_BIG) == art_sha_before

    SRC_DIR.mkdir(parents=True, exist_ok=True)
    (SRC_DIR / "AmericaJetB2A.ini").write_bytes(b2a_blob)

    data_sha = sha256(DATA_BIG)
    art_sha = art_sha_before
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    url = upload(OUT_ZIP)
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={data_sha}\n"
        f"_SPEC_ART_ONE.big sha256={art_sha} (unchanged)\n"
        f"CSF changed for B-2A labels; prior CSF={OLD_CSF}\n"
        f"zip={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    report = f"""B-2A SECOND BOMBER INTEGRATION = PASS

EXISTING B-2:
Object = AmericaJetB2Spirit
Changed = NO
HeavyAirBase Slot = 1

NEW B-2A:
Object = AmericaJetB2A
DisplayName = B-2A

Gameplay structure source = AmericaJetB2Spirit (full clone)

Donor primary W3D = AVB3bmbr
Donor textures = avb3bmbr.dds / avb3bmbr_D.dds / avb3bmbr_E.dds (+ AVB2A*.tga family present)
Donor animations = (embedded in AVB3bmbr W3D family)
Donor ButtonImage = B2A (MappedImage -> B2ATB.tga; distinct from Spirit B2DropBombTB)

Donor ART used = YES
Donor gameplay DATA used = NO

CommandButton = Command_ConstructAmericaJetB2A
Command = UNIT_BUILD
Object target = AmericaJetB2A
HeavyAirBase Slot = 12

Takeoff structure = JetAIUpdate + D30-F6_JetLocomotor (from Spirit)
Landing structure = BasicJetTaxiLocomotor + JetAIUpdate (from Spirit)
Parking structure = KeepsParking via JetAIUpdate / HeavyAirBase HXUSABigAirPort 3x2 unchanged

Existing B-2 preserved = YES
AmericaJetB2Spirit count = 1
AmericaJetB2A count = 1

DATA sha256 = {data_sha}
ART sha256 = {art_sha} (unchanged)
ZIP = {OUT_ZIP.name}
URL = {url}
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
