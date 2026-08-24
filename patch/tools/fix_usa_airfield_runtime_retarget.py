#!/usr/bin/env python3
"""BUGFIX: USA fighter airbase — retarget ACTIVE Airfield construct buttons.

Root cause: AmericaDozerCommandSet slot 13 still used
Command_ConstructAmericaAirfield_T → AmericaAirfield_T (old US_AirField).
Slot 18 had a NEW unused-style button while the old Airfield_T path remained.

Fix (Nato-style):
  Command_ConstructAmericaAirfield   Object = America_LargeAirBase
  Command_ConstructAmericaAirfield_T Object = America_LargeAirBase
  Dozer slot 18 = Command_ConstructAmericaAirfield (existing button name)
  Dozer slot 13 stays Command_ConstructAmericaAirfield_T (now also LargeAirBase)
  HeavyAirBase slot 4 UNCHANGED

DATA-only. Pakistan/other factions frozen.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace/patch")
DATA_BIG = ROOT / "Release/SPECTER_MASTER/_SPEC_DATA_ONE.big"
ART_BIG = ROOT / "Release/SPECTER_MASTER/_SPEC_ART_ONE.big"
OUT_DIR = ROOT / "Release/SPECTER_MASTER"
ZIP_PATH = ROOT / "Release/SPECTER_MASTER_DATA_USA_AIRFIELD_RUNTIME_FIX.zip"
NOTE = OUT_DIR / "DATA_USA_AIRFIELD_RUNTIME_FIX_HASHES.txt"
DL = OUT_DIR / "DATA_USA_AIRFIELD_RUNTIME_FIX_DOWNLOAD.txt"

# Pre-fix sha (AmericaAirfield_T still on slot 13). Post-fix:
# 575d9010b7ab138db8592ac1ba85faad3ec0f107497cbd8acb86cfc2890f452f
BASE_DATA = "bf0dae5838e465ce6d9ee643941f97484a3f56470b39ceef0292465858403db2"
BASE_ART = "74a411b72c19fafaafcd48a45d2aa76731d8dbd13e919e4f73f8b989e90d4822"


def sha256(p: Path | bytes) -> str:
    b = p if isinstance(p, bytes) else Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
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
    return n.replace("/", "\\").lower()


def upsert_commandbutton(cb_text: str, name: str, block: str) -> str:
    m = re.search(rf"^CommandButton\s+{re.escape(name)}\b.*?^End\s*$", cb_text, re.M | re.S)
    assert m, name
    return cb_text[: m.start()] + block.rstrip() + "\n" + cb_text[m.end() :]


def object_exists(fmap: dict[str, bytes], obj: str) -> bool:
    for b in fmap.values():
        if re.search(rf"^Object\s+{re.escape(obj)}\b", b.decode("latin1", errors="replace"), re.M):
            return True
    return False


def main() -> None:
    assert sha256(DATA_BIG) == BASE_DATA, sha256(DATA_BIG)
    assert sha256(ART_BIG) == BASE_ART

    entries, raw = read_big(DATA_BIG)
    fmap: dict[str, bytes] = {}
    disp: dict[str, str] = {}
    for name, off, size in entries:
        k = norm(name)
        if k not in fmap:
            disp[k] = name.replace("/", "\\")
        fmap[k] = raw[off : off + size]

    freeze_paths = {
        "pak_lab": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_LargeAirBase.ini",
        "pak_hab": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_HeavyAirBase.ini",
        "usa_hab": r"Data\INI\Object\Specter\United States Of America\Buildings\America_HeavyAirBase.ini",
        "usa_lab": r"Data\INI\Object\Specter\United States Of America\Buildings\America_LargeAirBase.ini",
    }
    freeze = {k: fmap[norm(p)] for k, p in freeze_paths.items()}

    # Verify America_LargeAirBase already correct (from prior patch)
    lab = freeze["usa_lab"].decode("latin1")
    assert re.search(r"^Object\s+America_LargeAirBase\b", lab, re.M)
    assert "Side             = America" in lab
    assert "Model              = TheAirPort" in lab
    assert "NumRows                 = 4" in lab
    assert "NumCols                 = 4" in lab
    assert "CommandSet          = America_LargeAirBaseCommandSet" in lab
    assert "AmericaSupplyCenter" in lab
    assert "Pakistan" not in re.search(r"Side\s*=\s*\S+", lab).group(0)

    # HeavyAirBase must remain
    hab = freeze["usa_hab"].decode("latin1")
    assert re.search(r"^Object\s+America_HeavyAirBase\b", hab, re.M)
    assert "HXUSABigAirPort" in hab

    cs_path = norm(r"Data\INI\CommandSet.ini")
    cb_path = norm(r"Data\INI\CommandButton.ini")
    pt_path = norm(r"Data\INI\PlayerTemplate.ini")
    pt_before = fmap[pt_path]
    cs_text = fmap[cs_path].decode("latin1")
    cb_text = fmap[cb_path].decode("latin1")

    dozer_before = re.search(
        r"^CommandSet\s+AmericaDozerCommandSet\b.*?^End\s*$", cs_text, re.M | re.S
    ).group(0)
    assert re.search(r"13\s*=\s*Command_ConstructAmericaAirfield_T\b", dozer_before)
    assert re.search(r"4\s*=\s*Command_ConstructAmerica_HeavyAirBase\b", dozer_before)
    # BEFORE: slot 13 builds old AmericaAirfield_T
    air_t_before = re.search(
        r"^CommandButton\s+Command_ConstructAmericaAirfield_T\b.*?^End\s*$",
        cb_text,
        re.M | re.S,
    ).group(0)
    assert "Object        = AmericaAirfield_T" in air_t_before
    air_before = re.search(
        r"^CommandButton\s+Command_ConstructAmericaAirfield\b.*?^End\s*$",
        cb_text,
        re.M | re.S,
    ).group(0)
    assert "Object        = AmericaAirfield" in air_before

    # --- Retarget EXISTING buttons (Nato-style) ---
    air_btn = """CommandButton Command_ConstructAmericaAirfield
  Command       = DOZER_CONSTRUCT
  Object        = America_LargeAirBase
  TextLabel     = CONTROLBAR:ConstructAmericaAirfield
  ButtonImage   = us_airfield
  ButtonBorderType        = BUILD ; Identifier for the User as to what kind of button this is
  DescriptLabel           = CONTROLBAR:ToolTipUSABuildAirField
End
"""
    air_t_btn = """CommandButton Command_ConstructAmericaAirfield_T
  Command       = DOZER_CONSTRUCT
  Object        = America_LargeAirBase
  TextLabel     = CONTROLBAR:ConstructAmericaAirfield
  ButtonImage   = us_airfield
  ButtonBorderType        = BUILD ; Identifier for the User as to what kind of button this is
  DescriptLabel           = CONTROLBAR:ToolTipUSABuildAirField
End
"""
    cb_text = upsert_commandbutton(cb_text, "Command_ConstructAmericaAirfield", air_btn)
    cb_text = upsert_commandbutton(cb_text, "Command_ConstructAmericaAirfield_T", air_t_btn)

    # Exactly one definition each
    assert len(re.findall(r"^CommandButton\s+Command_ConstructAmericaAirfield\b", cb_text, re.M)) == 1
    assert len(re.findall(r"^CommandButton\s+Command_ConstructAmericaAirfield_T\b", cb_text, re.M)) == 1

    # Slot 18: use EXISTING Airfield button name (not the extra LargeAirBase button)
    def repl_dozer(m: re.Match) -> str:
        block = m.group(0)
        block = re.sub(
            r"(18\s*=\s*)Command_ConstructAmerica_LargeAirBase\b",
            r"\1Command_ConstructAmericaAirfield",
            block,
        )
        # If somehow still old AmericaAirfield button name without Large already handled
        block = re.sub(
            r"(18\s*=\s*)Command_ConstructAmericaAirfield\b",
            r"\1Command_ConstructAmericaAirfield",
            block,
        )
        return block

    cs_text2, nsub = re.subn(
        r"^CommandSet\s+AmericaDozerCommandSet\b.*?^End\s*$",
        repl_dozer,
        cs_text,
        count=1,
        flags=re.M | re.S,
    )
    assert nsub == 1
    dozer_after = re.search(
        r"^CommandSet\s+AmericaDozerCommandSet\b.*?^End\s*$", cs_text2, re.M | re.S
    ).group(0)

    # Heavy preserved
    assert re.search(r"4\s*=\s*Command_ConstructAmerica_HeavyAirBase\b", dozer_after)
    # Slot 13 still Airfield_T name (now retargeted)
    assert re.search(r"13\s*=\s*Command_ConstructAmericaAirfield_T\b", dozer_after)
    # Slot 18 uses existing Airfield button
    assert re.search(r"18\s*=\s*Command_ConstructAmericaAirfield\b", dozer_after)
    assert "Command_ConstructAmerica_LargeAirBase" not in dozer_after
    # Unrelated slots preserved
    assert "Command_ConstructAmerica_MIM104F" in dozer_after
    assert "Command_ConstructAmericaWarFactory" in dozer_after
    assert "Command_ConstructAmericaBarracks" in dozer_after

    fmap[cs_path] = cs_text2.encode("latin1")
    fmap[cb_path] = cb_text.encode("latin1")

    # Freeze: Pakistan + HeavyAirBase + LargeAirBase object file unchanged this pass
    # (LargeAirBase object already correct; we only retarget buttons)
    for k in ("pak_lab", "pak_hab", "usa_hab", "usa_lab"):
        assert fmap[norm(freeze_paths[k])] == freeze[k], k
    assert fmap[pt_path] == pt_before

    DATA_BIG.write_bytes(build_big({disp[k]: v for k, v in fmap.items()}))
    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)
    assert art_sha == BASE_ART

    # -------- RE-EXTRACT FINAL BIG AND PROVE --------
    e2, r2 = read_big(DATA_BIG)
    f2 = {norm(n): r2[o : o + s] for n, o, s in e2}
    cs2 = f2[cs_path].decode("latin1")
    cb2 = f2[cb_path].decode("latin1")

    # Dozer object
    dozer_obj_file = None
    for n, b in ((disp.get(k, k), v) for k, v in f2.items()):
        t = b.decode("latin1", errors="replace")
        if re.search(r"^Object\s+AmericaVehicleDozer\b", t, re.M):
            dozer_obj_file = n
            assert "CommandSet          = AmericaDozerCommandSet" in t
            break
    assert dozer_obj_file

    vt = re.search(r"^CommandSet\s+AmericaDozerCommandSet\b.*?^End\s*$", cs2, re.M | re.S).group(0)
    assert re.search(r"13\s*=\s*Command_ConstructAmericaAirfield_T\b", vt)
    assert re.search(r"18\s*=\s*Command_ConstructAmericaAirfield\b", vt)
    assert re.search(r"4\s*=\s*Command_ConstructAmerica_HeavyAirBase\b", vt)

    # Active buttons from dozer airfield slots
    for btn_name in ("Command_ConstructAmericaAirfield", "Command_ConstructAmericaAirfield_T"):
        assert len(re.findall(rf"^CommandButton\s+{re.escape(btn_name)}\b", cb2, re.M)) == 1
        bb = re.search(rf"^CommandButton\s+{re.escape(btn_name)}\b.*?^End\s*$", cb2, re.M | re.S).group(0)
        obj = re.search(r"Object\s*=\s*(\S+)", bb).group(1)
        assert obj == "America_LargeAirBase", (btn_name, obj, bb)

    # No dozer path to old airfield objects
    for btn_ref in re.findall(r"=\s*(Command_Construct\S+)", vt):
        if "Airfield" in btn_ref or "LargeAirBase" in btn_ref:
            bb = re.search(
                rf"^CommandButton\s+{re.escape(btn_ref)}\b.*?^End\s*$", cb2, re.M | re.S
            ).group(0)
            obj = re.search(r"Object\s*=\s*(\S+)", bb).group(1)
            assert obj == "America_LargeAirBase", (btn_ref, obj)

    # America_LargeAirBase object
    assert (
        sum(
            1
            for b in f2.values()
            if re.search(r"^Object\s+America_LargeAirBase\b", b.decode("latin1", errors="replace"), re.M)
        )
        == 1
    )
    lab2 = next(
        b.decode("latin1", errors="replace")
        for b in f2.values()
        if re.search(r"^Object\s+America_LargeAirBase\b", b.decode("latin1", errors="replace"), re.M)
    )
    assert "Model              = TheAirPort" in lab2
    assert "NumRows                 = 4" in lab2
    assert "NumCols                 = 4" in lab2
    assert "America_LargeAirBaseCommandSet" in lab2
    # Fighter roster preserved on LargeAirBase CommandSet
    lcs = re.search(
        r"^CommandSet\s+America_LargeAirBaseCommandSet\b.*?^End\s*$", cs2, re.M | re.S
    ).group(0)
    for need in (
        "Command_ConstructAmericaJetRaptor",
        "Command_ConstructAmericaJetF-16C_AG",
        "Command_ConstructAmericaJetF-22A_AA",
        "Command_ConstructAmericaJetF35C",
    ):
        assert need in lcs
    assert "Command_ConstructAmericaJetB2Spirit" not in lcs  # heavy stays elsewhere

    # Heavy preserved
    assert object_exists(f2, "America_HeavyAirBase")
    hcs = re.search(
        r"^CommandSet\s+America_HeavyAirBaseCommandSet\b.*?^End\s*$", cs2, re.M | re.S
    ).group(0)
    assert "Command_ConstructAmericaJetB2Spirit" in hcs
    assert re.search(r"4\s*=\s*Command_ConstructAmerica_HeavyAirBase\b", vt)
    hbtn = re.search(
        r"^CommandButton\s+Command_ConstructAmerica_HeavyAirBase\b.*?^End\s*$", cb2, re.M | re.S
    ).group(0)
    assert "Object        = America_HeavyAirBase" in hbtn

    # Old objects still exist (not deleted)
    assert object_exists(f2, "AmericaAirfield")
    assert object_exists(f2, "AmericaAirfield_T")
    assert object_exists(f2, "America_MIM104F")

    # Pakistan frozen
    assert f2[norm(freeze_paths["pak_lab"])] == freeze["pak_lab"]
    assert f2[norm(freeze_paths["pak_hab"])] == freeze["pak_hab"]
    assert f2[pt_path] == pt_before

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    report = f"""USA 16-SLOT AIRFIELD RUNTIME FIX = PASS

Active USA Dozer = AmericaVehicleDozer
Active Dozer CommandSet = AmericaDozerCommandSet

Airfield slot = 13 (Command_ConstructAmericaAirfield_T) AND 18 (Command_ConstructAmericaAirfield)
Active Airfield ConstructButton = Command_ConstructAmericaAirfield / Command_ConstructAmericaAirfield_T

BEFORE target Object =
  Command_ConstructAmericaAirfield   -> AmericaAirfield
  Command_ConstructAmericaAirfield_T -> AmericaAirfield_T
  (slot 18 had Command_ConstructAmerica_LargeAirBase; slot 13 still built OLD AmericaAirfield_T)

AFTER target Object =
  Command_ConstructAmericaAirfield   -> America_LargeAirBase
  Command_ConstructAmericaAirfield_T -> America_LargeAirBase

Expected AFTER:
America_LargeAirBase

America_LargeAirBase exists = YES
Primary W3D = TheAirPort.W3D
Capacity = 16
NumRows = 4
NumCols = 4

Old USA Airfield still constructed by Dozer = NO
Expected = NO

USA fighter roster preserved = YES (America_LargeAirBaseCommandSet)
USA HeavyAirBase preserved = YES
Patriot-slot HeavyAirBase preserved = YES (slot 4)

Pakistan changed = NO
Other factions changed = NO
ART changed = NO

ACTIVE FILES CHANGED:
- Data\\INI\\CommandButton.ini  (retarget Airfield + Airfield_T -> America_LargeAirBase)
- Data\\INI\\CommandSet.ini      (slot 18 -> Command_ConstructAmericaAirfield)

DATA sha256 = {data_sha}
ART sha256  = {art_sha} (UNCHANGED)
ZIP sha256  = {sha256(ZIP_PATH)}
ZIP path    = {ZIP_PATH}
ZIP size    = {ZIP_PATH.stat().st_size}
"""
    NOTE.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
