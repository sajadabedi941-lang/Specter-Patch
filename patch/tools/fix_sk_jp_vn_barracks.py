#!/usr/bin/env python3
"""Repair South Korea / Japan / Vietnam Barracks chains from CURRENT NK Barracks.

READ-ONLY: North Korea and all other factions.
DATA-only. Rebuilds _SPEC_DATA_ONE.big, re-extracts, zips DATA only.

Fixes:
- Rebuild country Barracks Objects from NorthKorea_Barracks field-for-field
- Create missing *_BarracksCommandSet (reuse proven Iraq infantry buttons = NK working production)
- Retarget construct buttons to country Barracks (not Iraq_Barracks)
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
ZIP_PATH = ROOT / "Release/SPECTER_MASTER_DATA_SK_JP_VN_BARRACKS_FIX.zip"
NOTE = OUT_DIR / "DATA_SK_JP_VN_BARRACKS_FIX_HASHES.txt"
DL = OUT_DIR / "DATA_SK_JP_VN_BARRACKS_FIX_DOWNLOAD.txt"
EXTRACT = OUT_DIR / "_extract_sk_jp_vn_barracks_verify"

BASE_ART = "74a411b72c19fafaafcd48a45d2aa76731d8dbd13e919e4f73f8b989e90d4822"

FACTIONS = [
    {
        "prefix": "SouthKorea",
        "side": "SouthKorea",
        "folder": "South Korean Armed Forces",
        "header": "South Korean Armed Forces - Buildings",
    },
    {
        "prefix": "Japan",
        "side": "Japan",
        "folder": "Japan Self-Defense Forces",
        "header": "Japan Self-Defense Forces - Buildings",
    },
    {
        "prefix": "Vietnam",
        "side": "Vietnam",
        "folder": "Vietnam People's Armed Forces",
        "header": "Vietnam People's Armed Forces - Buildings",
    },
]

IRAQ_BARRACKS_CS = """CommandSet Iraq_BarracksCommandSet
  1 = Command_ConstructIraq_RepublicanGuard_AKMS
  2 = Command_ConstructIraq_RepublicanGuard_RPG7
  3 = Command_ConstructIraq_RepublicanGuardMortar
  4 = Command_ConstructIraq_RepublicanGuardKornet
  5 = Command_ConstructIraq_RepublicanGuard_Pkm
  6 = Command_ConstructIraq_RepublicanGuard_TBK14
  7 = Command_ConstructIraq_RepublicanGuard_Eng
  8 = Command_ConstructIraq_SpecialForces
  9 = Command_ConstructIraq_RepublicanGuardIgla
  11 = Command_UpgradeGLARebelCaptureBuilding
  12 = Command_Upgrade_RGD5
  13 = Command_Upgrade_Rpg29
  14 = Command_Sell
End"""


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


def barracks_path(folder: str) -> str:
    return f"Data\\INI\\Object\\Specter\\{folder}\\Buildings\\Iraq_Barracks.ini"


def clone_barracks_from_nk(nk_text: str, prefix: str, side: str, header: str) -> str:
    """Field-for-field clone of NorthKorea_Barracks with country identity only."""
    text = nk_text
    text = text.replace("Object NorthKorea_Barracks", f"Object {prefix}_Barracks")
    text = re.sub(
        r"(?m)^(\s*Side\s*=\s*)NorthKorea\s*$",
        rf"\1{side}",
        text,
    )
    text = text.replace(
        "CommandSet       = NorthKorea_BarracksCommandSet",
        f"CommandSet       = {prefix}_BarracksCommandSet",
    )
    text = text.replace(
        "CommandSet = NorthKorea_BarracksCommandSet",
        f"CommandSet = {prefix}_BarracksCommandSet",
    )
    # Comment header Iraq identity → country (content identity leak cleanup)
    text = text.replace(
        ";-------------- Iraq Army - Buildings -----------------;",
        f";-------------- {header} -----------------;",
    )
    # Safety: no leftover NK Side / CommandSet / Object name
    assert f"Object {prefix}_Barracks" in text
    assert re.search(rf"(?m)^\s*Side\s*=\s*{re.escape(side)}\s*$", text)
    assert f"{prefix}_BarracksCommandSet" in text
    assert "Object NorthKorea_Barracks" not in text
    assert not re.search(r"(?m)^\s*Side\s*=\s*NorthKorea\s*$", text)
    assert not re.search(r"(?m)^\s*Side\s*=\s*Iraq\s*$", text)
    assert "NorthKorea_BarracksCommandSet" not in text
    assert "Iraq_BarracksCommandSet" not in text
    return text


def make_barracks_commandset(prefix: str) -> str:
    return IRAQ_BARRACKS_CS.replace(
        "CommandSet Iraq_BarracksCommandSet",
        f"CommandSet {prefix}_BarracksCommandSet",
    )


def ensure_commandsets(cs_text: str) -> str:
    out = cs_text
    for fac in FACTIONS:
        name = f"{fac['prefix']}_BarracksCommandSet"
        if out.count(f"CommandSet {name}") == 0:
            block = make_barracks_commandset(fac["prefix"])
            # Insert after Iraq_BarracksCommandSet if present, else append
            anchor = "CommandSet Iraq_BarracksCommandSet"
            i = out.find(anchor)
            if i >= 0:
                j = out.find("\nEnd", i)
                if j < 0:
                    raise SystemExit("Iraq_BarracksCommandSet End not found")
                j = j + len("\nEnd")
                out = out[:j] + "\n\n" + block + out[j:]
            else:
                out = out.rstrip() + "\n\n" + block + "\n"
        elif out.count(f"CommandSet {name}") > 1:
            raise SystemExit(f"duplicate CommandSet {name}")
    return out


def fix_construct_buttons(cb_text: str) -> str:
    out = cb_text
    for fac in FACTIONS:
        prefix = fac["prefix"]
        # Match SAFE (and plain) construct buttons for this country only
        pattern = re.compile(
            rf"(CommandButton Command_Construct{prefix}_Barracks(?:_SAFE)?\n"
            rf".*?Object\s*=\s*)Iraq_Barracks(\r?\n)",
            re.S,
        )
        out, n = pattern.subn(rf"\1{prefix}_Barracks\2", out)
        if n == 0:
            # Also allow already-fixed or alternate Object lines
            if f"Command_Construct{prefix}_Barracks" not in out:
                raise SystemExit(f"missing construct button for {prefix}")
        # Must not still point at Iraq for these buttons
        for m in re.finditer(
            rf"CommandButton Command_Construct{prefix}_Barracks\w*\n(.*?)End",
            out,
            re.S,
        ):
            block = m.group(0)
            obj = re.search(r"Object\s*=\s*(\S+)", block)
            if not obj or obj.group(1) != f"{prefix}_Barracks":
                raise SystemExit(f"construct button still wrong for {prefix}: {block}")
    # NK must remain untouched (still Iraq_Barracks per current NK chain)
    nk = re.search(
        r"CommandButton Command_ConstructNorthKorea_Barracks_SAFE\n(.*?)End",
        out,
        re.S,
    )
    if not nk or "Object           = Iraq_Barracks" not in nk.group(0):
        raise SystemExit("North Korea construct button was altered unexpectedly")
    return out


def parse_validate_barracks(text: str, prefix: str, side: str) -> list[str]:
    errs = []
    if text.startswith("\ufeff") or text[:3] == "\ufeff":
        errs.append("BOM")
    raw = text.encode("latin-1")
    if raw.startswith(b"\xef\xbb\xbf"):
        errs.append("UTF8_BOM")
    norm_t = text.replace("\r\n", "\n").replace("\r", "\n")
    objs = re.findall(r"(?m)^Object\s+(\S+)", norm_t)
    if objs != [f"{prefix}_Barracks"]:
        errs.append(f"objects={objs}")
    if not norm_t.rstrip().endswith("End"):
        errs.append("missing_trailing_End")
    if "<<<<<<" in text or ">>>>>>" in text:
        errs.append("merge_marker")
    if re.search(r"(?m)^\s*Side\s*=\s*Iraq\s*$", norm_t):
        errs.append("side_iraq")
    if re.search(r"(?m)^\s*Side\s*=\s*NorthKorea\s*$", norm_t):
        errs.append("side_nk")
    if not re.search(rf"(?m)^\s*Side\s*=\s*{re.escape(side)}\s*$", norm_t):
        errs.append("side_missing")
    if f"CommandSet       = {prefix}_BarracksCommandSet" not in text and (
        f"CommandSet = {prefix}_BarracksCommandSet" not in text
    ):
        # tolerate whitespace variants
        if not re.search(
            rf"(?m)^\s*CommandSet\s*=\s*{re.escape(prefix)}_BarracksCommandSet\s*$",
            norm_t,
        ):
            errs.append("commandset_missing")
    # nested Object: more than one Object header already caught
    return errs


def extract_file(entries, data, want: str) -> bytes:
    w = norm(want)
    for name, off, size in entries:
        if norm(name) == w:
            return data[off : off + size]
    raise KeyError(want)


def main() -> None:
    entries, data = read_big(DATA_BIG)
    file_map = {name: data[off : off + size] for name, off, size in entries}

    # Canonical NK Barracks source (current content; path may lack Data\INI prefix)
    nk_key = None
    for name in file_map:
        if norm(name).endswith("north korea\\buildings\\iraq_barracks.ini"):
            nk_key = name
            break
    if not nk_key:
        raise SystemExit("North Korea Barracks source not found")
    nk_bytes = file_map[nk_key]
    nk_text = nk_bytes.decode("latin-1")
    if "Object NorthKorea_Barracks" not in nk_text:
        raise SystemExit("NK source missing Object NorthKorea_Barracks")

    changed = []

    # 1) Rebuild three Barracks from NK
    for fac in FACTIONS:
        path = barracks_path(fac["folder"])
        # Preserve existing key casing if present
        existing = None
        for name in file_map:
            if norm(name) == norm(path):
                existing = name
                break
        key = existing or path
        new_text = clone_barracks_from_nk(
            nk_text, fac["prefix"], fac["side"], fac["header"]
        )
        # Preserve NK encoding: CRLF if source uses CRLF
        if b"\r\n" in nk_bytes and "\r\n" not in new_text:
            new_text = new_text.replace("\n", "\r\n")
        # If clone introduced \n-only from replace on mixed, normalize to NK line endings
        if b"\r\n" in nk_bytes:
            new_text = new_text.replace("\r\n", "\n").replace("\n", "\r\n")
        errs = parse_validate_barracks(new_text, fac["prefix"], fac["side"])
        if errs:
            raise SystemExit(f"{fac['prefix']} barracks validate failed: {errs}")
        new_bytes = new_text.encode("latin-1")
        if file_map.get(key) != new_bytes:
            file_map[key] = new_bytes
            changed.append(key)

    # 2) CommandSet.ini — add country Barracks CommandSets
    cs_key = None
    for name in file_map:
        if norm(name) == norm("Data\\INI\\CommandSet.ini"):
            cs_key = name
            break
    if not cs_key:
        raise SystemExit("CommandSet.ini missing")
    cs_old = file_map[cs_key].decode("latin-1")
    cs_new = ensure_commandsets(cs_old)
    if cs_new != cs_old:
        # keep original newline style
        if b"\r\n" in file_map[cs_key]:
            cs_new = cs_new.replace("\r\n", "\n").replace("\n", "\r\n")
        file_map[cs_key] = cs_new.encode("latin-1")
        changed.append(cs_key)

    # 3) CommandButton.ini — retarget construct Object
    cb_key = None
    for name in file_map:
        if norm(name) == norm("Data\\INI\\CommandButton.ini"):
            cb_key = name
            break
    if not cb_key:
        raise SystemExit("CommandButton.ini missing")
    cb_old = file_map[cb_key].decode("latin-1")
    cb_new = fix_construct_buttons(cb_old)
    if cb_new != cb_old:
        if b"\r\n" in file_map[cb_key]:
            cb_new = cb_new.replace("\r\n", "\n").replace("\n", "\r\n")
        file_map[cb_key] = cb_new.encode("latin-1")
        changed.append(cb_key)

    # Rebuild BIG
    new_big = build_big(file_map)
    DATA_BIG.write_bytes(new_big)
    data_sha = sha256(new_big)
    art_sha = sha256(ART_BIG)

    # Re-extract verify
    EXTRACT.mkdir(parents=True, exist_ok=True)
    entries2, data2 = read_big(DATA_BIG)
    report = []
    overall = "PASS"

    def get(path_end: str) -> tuple[str, bytes]:
        for name, off, size in entries2:
            if norm(name).endswith(norm(path_end)):
                return name, data2[off : off + size]
        raise KeyError(path_end)

    cs_name, cs_bytes = get("Data\\INI\\CommandSet.ini")
    cb_name, cb_bytes = get("Data\\INI\\CommandButton.ini")
    cs_t = cs_bytes.decode("latin-1")
    cb_t = cb_bytes.decode("latin-1")

    for fac in FACTIONS:
        prefix = fac["prefix"]
        side = fac["side"]
        path = barracks_path(fac["folder"])
        name, blob = None, None
        for n, off, size in entries2:
            if norm(n) == norm(path):
                name, blob = n, data2[off : off + size]
                break
        if name is None:
            overall = "FAIL"
            report.append(f"{prefix}: MISSING FILE {path}")
            continue
        text = blob.decode("latin-1")
        errs = parse_validate_barracks(text, prefix, side)
        bom = blob.startswith(b"\xef\xbb\xbf")
        obj_count = sum(
            1
            for n, off, size in entries2
            if n.lower().endswith(".ini")
            and re.search(
                rf"(?m)^Object\s+{re.escape(prefix)}_Barracks\s*$",
                data2[off : off + size].decode("latin-1", "replace"),
            )
        )
        cs_count = cs_t.count(f"CommandSet {prefix}_BarracksCommandSet")
        # construct button
        m = re.search(
            rf"CommandButton Command_Construct{prefix}_Barracks_SAFE\n(.*?)End",
            cb_t,
            re.S,
        )
        construct_obj = None
        if m:
            om = re.search(r"Object\s*=\s*(\S+)", m.group(1))
            construct_obj = om.group(1) if om else None
        # Iraq Side leak
        iraq_side = bool(re.search(r"(?m)^\s*Side\s*=\s*Iraq\s*$", text))
        # CS buttons exist
        missing_btns = []
        if cs_count == 1:
            i = cs_t.find(f"CommandSet {prefix}_BarracksCommandSet")
            block = cs_t[i : cs_t.find("\nEnd", i) + 4]
            for btn in re.findall(r"=\s*(Command_\S+)", block):
                if cb_t.count(f"CommandButton {btn}") < 1:
                    missing_btns.append(btn)
        parse_ok = not errs and obj_count == 1 and cs_count == 1 and not missing_btns
        parse_ok = parse_ok and construct_obj == f"{prefix}_Barracks" and not iraq_side and not bom
        if not parse_ok:
            overall = "FAIL"
        report.append(
            f"""
{prefix}:
  Crash file = {name}
  Object = {prefix}_Barracks
  Side = {side}
  CommandSet = {prefix}_BarracksCommandSet (count={cs_count})
  Construct Button = Command_Construct{prefix}_Barracks_SAFE -> {construct_obj}
  Object count = {obj_count}
  Encoding/BOM issue = {'YES' if bom else 'NO'}
  Iraq identity leak (Side) = {'YES' if iraq_side else 'NO'}
  Parse errs = {errs or 'none'}
  Missing CS buttons = {missing_btns or 'none'}
  Parse validation = {'PASS' if parse_ok else 'FAIL'}
""".rstrip()
        )

    # NK unchanged check: NK barracks bytes identical, NK construct still Iraq
    nk_name, nk_blob = None, None
    for n, off, size in entries2:
        if norm(n).endswith("north korea\\buildings\\iraq_barracks.ini"):
            nk_name, nk_blob = n, data2[off : off + size]
            break
    nk_same = nk_blob == nk_bytes
    nk_btn = re.search(
        r"CommandButton Command_ConstructNorthKorea_Barracks_SAFE\n(.*?)End",
        cb_t,
        re.S,
    )
    nk_obj = re.search(r"Object\s*=\s*(\S+)", nk_btn.group(1)).group(1) if nk_btn else None

    NOTE.write_text(
        f"_SPEC_DATA_ONE.big sha256={data_sha}\n"
        f"_SPEC_ART_ONE.big sha256={art_sha} (UNCHANGED expected {BASE_ART})\n"
        f"ART match = {art_sha == BASE_ART}\n"
        f"NK barracks bytes unchanged = {nk_same}\n"
        f"NK construct Object = {nk_obj}\n"
        f"Files changed:\n"
        + "\n".join(f"  {c}" for c in changed)
        + f"\nOVERALL = {overall}\n"
        + "\n".join(report)
        + "\n"
    )

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    print("CHANGED:")
    for c in changed:
        print(" ", c)
    print("DATA sha", data_sha)
    print("ART sha", art_sha, "unchanged", art_sha == BASE_ART)
    print("NK barracks unchanged", nk_same, "NK construct", nk_obj)
    print("OVERALL", overall)
    print(NOTE.read_text())
    print("ZIP", ZIP_PATH, ZIP_PATH.stat().st_size)


if __name__ == "__main__":
    main()
