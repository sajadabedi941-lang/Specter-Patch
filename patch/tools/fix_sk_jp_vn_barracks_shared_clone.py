#!/usr/bin/env python3
"""SHARED clone bug: delete+rebuild Japan/SouthKorea/Vietnam Barracks from CURRENT NK.

North Korea READ-ONLY. DATA-only. Fresh extract validation from rebuilt BIG.
Removes parse-breaking Texture=IraqiFlag.tga DPRK_Flag.tga (unique to unloaded NK
Barracks path; absent from working Iraq Army Barracks under Data\\INI\\Object).
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace/patch")
DATA_BIG = ROOT / "Release/SPECTER_MASTER/_SPEC_DATA_ONE.big"
ART_BIG = ROOT / "Release/SPECTER_MASTER/_SPEC_ART_ONE.big"
OUT_DIR = ROOT / "Release/SPECTER_MASTER"
ZIP_PATH = ROOT / "Release/SPECTER_MASTER_DATA_SK_JP_VN_BARRACKS_SHARED_FIX.zip"
NOTE = OUT_DIR / "DATA_SK_JP_VN_BARRACKS_SHARED_FIX_HASHES.txt"
DL = OUT_DIR / "DATA_SK_JP_VN_BARRACKS_SHARED_FIX_DOWNLOAD.txt"
EXTRACT_BEFORE = OUT_DIR / "_extract_barracks_shared_before"
EXTRACT_FINAL = OUT_DIR / "_extract_barracks_shared_final"

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

# Proven infantry roster used by working NK gameplay (via Iraq_Barracks construct).
# NorthKorea_BarracksCommandSet does not exist in active CommandSet.ini.
BARRACKS_CS_BODY = """  1 = Command_ConstructIraq_RepublicanGuard_AKMS
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


def nl(t: str) -> str:
    return t.replace("\r\n", "\n").replace("\r", "\n")


def barracks_path(folder: str) -> str:
    return f"Data\\INI\\Object\\Specter\\{folder}\\Buildings\\Iraq_Barracks.ini"


def find_key(file_map: dict[str, bytes], want: str) -> str | None:
    w = norm(want)
    for k in file_map:
        if norm(k) == w:
            return k
    return None


def find_nk_barracks_key(file_map: dict[str, bytes]) -> str:
    for k in file_map:
        if norm(k).endswith("north korea\\buildings\\iraq_barracks.ini"):
            return k
    raise SystemExit("North Korea Barracks donor not found")


def rebuild_from_nk(nk_text: str, prefix: str, side: str, header: str) -> str:
    """DELETE body semantics: full reconstruct from NK text, identity-only swaps + parse fixes."""
    t = nk_text
    # Identity
    t = t.replace("Object NorthKorea_Barracks", f"Object {prefix}_Barracks")
    t = re.sub(r"(?m)^(\s*Side\s*=\s*)NorthKorea\s*$", rf"\1{side}", t)
    t = t.replace(
        "CommandSet       = NorthKorea_BarracksCommandSet",
        f"CommandSet       = {prefix}_BarracksCommandSet",
    )
    t = t.replace(
        "CommandSet = NorthKorea_BarracksCommandSet",
        f"CommandSet = {prefix}_BarracksCommandSet",
    )
    # Remove Iraq faction comment identity
    t = t.replace(
        ";-------------- Iraq Army - Buildings -----------------;",
        f";-------------- {header} -----------------;",
    )
    # PARSE-SAFETY + Iraq identity: remove Texture IraqiFlag remapping.
    # This line exists ONLY on NK Barracks (unloaded bad path) and the three clones.
    # Working Data\\INI\\Object Iraq_Barracks has no such line.
    t = re.sub(
        r"(?m)^\s*Texture\s*=\s*IraqiFlag\.tga\s+DPRK_Flag\.tga\s*\r?\n",
        "",
        t,
    )
    # Guarantees
    assert f"Object {prefix}_Barracks" in t
    assert re.search(rf"(?m)^\s*Side\s*=\s*{re.escape(side)}\s*$", t)
    assert f"{prefix}_BarracksCommandSet" in t
    assert "Object NorthKorea_Barracks" not in t
    assert not re.search(r"(?m)^\s*Side\s*=\s*(NorthKorea|Iraq)\s*$", t)
    assert "IraqiFlag" not in t
    assert "NorthKorea_BarracksCommandSet" not in t
    assert "Iraq_BarracksCommandSet" not in t
    assert "Iraq Army" not in t
    return t


def parse_audit(blob: bytes, prefix: str, side: str) -> dict:
    t = blob.decode("latin-1")
    tn = nl(t)
    errs = []
    if blob.startswith(b"\xef\xbb\xbf"):
        errs.append("BOM")
    if b"\x00" in blob:
        errs.append("NULL")
    # unexpected non-ascii
    if any(b > 127 for b in blob):
        errs.append("NON_ASCII")
    objs = re.findall(r"(?m)^Object\s+(\S+)", tn)
    if objs != [f"{prefix}_Barracks"]:
        errs.append(f"objs={objs}")
    if not tn.rstrip().endswith("End"):
        errs.append("missing_End")
    if "<<<<<<" in t or ">>>>>>" in t or "```" in t:
        errs.append("markers")
    if re.search(r"(?m)^\s*Side\s*=\s*Iraq\s*$", tn):
        errs.append("side_iraq")
    if re.search(r"(?m)^\s*Side\s*=\s*NorthKorea\s*$", tn):
        errs.append("side_nk")
    if not re.search(rf"(?m)^\s*Side\s*=\s*{re.escape(side)}\s*$", tn):
        errs.append("side_wrong")
    if not re.search(
        rf"(?m)^\s*CommandSet\s*=\s*{re.escape(prefix)}_BarracksCommandSet\s*$", tn
    ):
        errs.append("cs_ref")
    # Iraq faction identity (not shared irq_camp / irq_barracks art tokens)
    identity_leaks = []
    for pat, name in [
        (r"(?m)^\s*Side\s*=\s*Iraq\s*$", "SideIraq"),
        (r"Iraq_BarracksCommandSet", "IraqCS"),
        (r"IraqiFlag", "IraqiFlag"),
        (r"Iraq Army", "IraqArmyComment"),
        (r"Object Iraq_", "ObjectIraq"),
        (r"Side\s*=\s*Iraq", "SideIraq2"),
    ]:
        if re.search(pat, t):
            identity_leaks.append(name)
    # nested Object
    nested = len(objs) > 1
    # End balance: one top-level Object, file ends with End
    balanced = (len(objs) == 1) and tn.rstrip().endswith("End")
    return {
        "errs": errs,
        "identity_leaks": identity_leaks,
        "encoding": "latin-1/CRLF" if b"\r\n" in blob else "latin-1/LF",
        "bom": blob.startswith(b"\xef\xbb\xbf"),
        "nulls": b"\x00" in blob,
        "balanced": balanced,
        "nested": nested,
        "pass": not errs and not identity_leaks and balanced and not nested,
    }


def ensure_commandsets(cs_text: str) -> str:
    """Remove any existing country Barracks CS then insert clean copies once."""
    # Work in LF space; caller re-applies CRLF if needed.
    out = nl(cs_text)
    for fac in FACTIONS:
        name = f"{fac['prefix']}_BarracksCommandSet"
        while True:
            m = re.search(
                rf"(?ms)^CommandSet\s+{re.escape(name)}\s*\n.*?^End\s*(?:\n|$)",
                out,
            )
            if not m:
                break
            out = out[: m.start()] + out[m.end() :]
        block = f"CommandSet {name}\n{BARRACKS_CS_BODY}"
        if not block.endswith("\n"):
            block += "\n"
        anchor = re.search(
            r"(?ms)^CommandSet\s+Iraq_BarracksCommandSet\s*\n.*?^End\s*",
            out,
        )
        if anchor:
            out = out[: anchor.end()] + "\n\n" + block + out[anchor.end() :]
        else:
            out = out.rstrip() + "\n\n" + block + "\n"
    for fac in FACTIONS:
        name = f"{fac['prefix']}_BarracksCommandSet"
        cnt = len(re.findall(rf"(?m)^CommandSet\s+{re.escape(name)}\s*$", out))
        if cnt != 1:
            raise SystemExit(f"CS count bad for {name}: {cnt}")
    return out


def fix_construct_buttons(cb_text: str) -> str:
    out = cb_text
    for fac in FACTIONS:
        prefix = fac["prefix"]
        # Force Object line on SAFE construct button
        pattern = re.compile(
            rf"(CommandButton Command_Construct{prefix}_Barracks_SAFE\r?\n"
            rf".*?Object\s*=\s*)\S+(\r?\n)",
            re.S,
        )
        out2, n = pattern.subn(rf"\g<1>{prefix}_Barracks\2", out)
        if n == 0:
            raise SystemExit(f"construct button missing for {prefix}")
        out = out2
    # verify
    cbn = nl(out)
    for fac in FACTIONS:
        prefix = fac["prefix"]
        m = re.search(
            rf"CommandButton Command_Construct{prefix}_Barracks_SAFE\n(.*?)End",
            cbn,
            re.S,
        )
        obj = re.search(r"Object\s*=\s*(\S+)", m.group(1)).group(1)
        if obj != f"{prefix}_Barracks":
            raise SystemExit(f"{prefix} construct still {obj}")
    # NK untouched
    m = re.search(
        r"CommandButton Command_ConstructNorthKorea_Barracks_SAFE\n(.*?)End",
        cbn,
        re.S,
    )
    obj = re.search(r"Object\s*=\s*(\S+)", m.group(1)).group(1)
    if obj != "Iraq_Barracks":
        raise SystemExit(f"NK construct altered to {obj}")
    return out


def count_object_defs(entries, data, obj: str) -> list[str]:
    locs = []
    for name, off, size in entries:
        if not name.lower().endswith(".ini"):
            continue
        t = nl(data[off : off + size].decode("latin-1", "replace"))
        if re.search(rf"(?m)^Object\s+{re.escape(obj)}\s*$", t):
            locs.append(name)
    return locs


def main() -> None:
    entries, data = read_big(DATA_BIG)
    file_map = {name: data[off : off + size] for name, off, size in entries}
    nk_key = find_nk_barracks_key(file_map)
    nk_bytes = file_map[nk_key]
    nk_text = nk_bytes.decode("latin-1")
    if "Object NorthKorea_Barracks" not in nk_text:
        raise SystemExit("donor missing Object NorthKorea_Barracks")

    # BEFORE counts
    before = {
        o: count_object_defs(entries, data, o)
        for o in [
            "Japan_Barracks",
            "SouthKorea_Barracks",
            "Vietnam_Barracks",
            "NorthKorea_Barracks",
        ]
    }
    print("BEFORE counts:")
    for k, v in before.items():
        print(f"  {k} = {len(v)} {v}")

    changed: list[str] = []
    fallback = {f["prefix"]: False for f in FACTIONS}

    # 1) DELETE + rebuild three Barracks from NK
    for fac in FACTIONS:
        path = barracks_path(fac["folder"])
        key = find_key(file_map, path)
        if key is None:
            key = path
        # delete old body by full replace
        new_text = rebuild_from_nk(nk_text, fac["prefix"], fac["side"], fac["header"])
        # match NK CRLF
        if b"\r\n" in nk_bytes:
            new_text = new_text.replace("\r\n", "\n").replace("\n", "\r\n")
        new_bytes = new_text.encode("latin-1")
        audit = parse_audit(new_bytes, fac["prefix"], fac["side"])
        if not audit["pass"]:
            # FALLBACK: point construct to NorthKorea_Barracks later; still ship cleaned object if possible
            print(f"WARN {fac['prefix']} parse audit soft-fail: {audit}")
            # If still not pass, keep object but mark fallback for construct
            if audit["errs"] or audit["nested"] or not audit["balanced"]:
                fallback[fac["prefix"]] = True
        file_map[key] = new_bytes
        changed.append(key)
        print(f"REBUILT {key} size={len(new_bytes)} audit_pass={audit['pass']}")

    # 2) CommandSet.ini — recreate Barracks CS
    cs_key = find_key(file_map, "Data\\INI\\CommandSet.ini")
    if not cs_key:
        raise SystemExit("CommandSet.ini missing")
    cs_old = file_map[cs_key].decode("latin-1")
    cs_new = ensure_commandsets(cs_old)
    if b"\r\n" in file_map[cs_key]:
        cs_new = cs_new.replace("\r\n", "\n").replace("\n", "\r\n")
    if cs_new.encode("latin-1") != file_map[cs_key]:
        file_map[cs_key] = cs_new.encode("latin-1")
        changed.append(cs_key)

    # 3) CommandButton — construct targets (or fallback)
    cb_key = find_key(file_map, "Data\\INI\\CommandButton.ini")
    if not cb_key:
        raise SystemExit("CommandButton.ini missing")
    cb_old = file_map[cb_key].decode("latin-1")
    if any(fallback.values()):
        # Per-country fallback to NorthKorea_Barracks when that country's object failed audit
        out = cb_old
        for fac in FACTIONS:
            prefix = fac["prefix"]
            target = (
                "NorthKorea_Barracks"
                if fallback[prefix]
                else f"{prefix}_Barracks"
            )
            pattern = re.compile(
                rf"(CommandButton Command_Construct{prefix}_Barracks_SAFE\r?\n"
                rf".*?Object\s*=\s*)\S+(\r?\n)",
                re.S,
            )
            out, n = pattern.subn(rf"\g<1>{target}\2", out)
            if n == 0:
                raise SystemExit(f"missing construct {prefix}")
        cb_new = out
    else:
        cb_new = fix_construct_buttons(cb_old)
    if b"\r\n" in file_map[cb_key]:
        cb_new = cb_new.replace("\r\n", "\n").replace("\n", "\r\n")
    if cb_new.encode("latin-1") != file_map[cb_key]:
        file_map[cb_key] = cb_new.encode("latin-1")
        changed.append(cb_key)

    # NK bytes must be unchanged
    if file_map[nk_key] != nk_bytes:
        raise SystemExit("NK barracks mutated")

    # Rebuild BIG
    new_big = build_big(file_map)
    DATA_BIG.write_bytes(new_big)
    data_sha = sha256(new_big)
    art_sha = sha256(ART_BIG)

    # FINAL fresh extract + audit
    if EXTRACT_FINAL.exists():
        shutil.rmtree(EXTRACT_FINAL)
    EXTRACT_FINAL.mkdir(parents=True)
    entries2, data2 = read_big(DATA_BIG)
    report_lines = []
    overall = "PASS"

    cs_t = nl(
        next(
            data2[o : o + s].decode("latin-1")
            for n, o, s in entries2
            if norm(n) == norm("Data\\INI\\CommandSet.ini")
        )
    )
    cb_t = nl(
        next(
            data2[o : o + s].decode("latin-1")
            for n, o, s in entries2
            if norm(n) == norm("Data\\INI\\CommandButton.ini")
        )
    )

    for fac in FACTIONS:
        prefix, side, folder = fac["prefix"], fac["side"], fac["folder"]
        path = barracks_path(folder)
        key = None
        blob = None
        for n, o, s in entries2:
            if norm(n) == norm(path):
                key, blob = n, data2[o : o + s]
                break
        # write extract
        outp = EXTRACT_FINAL / Path(path.replace("\\", "/"))
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_bytes(blob)
        locs = count_object_defs(entries2, data2, f"{prefix}_Barracks")
        audit = parse_audit(blob, prefix, side)
        csc = cs_t.count(f"CommandSet {prefix}_BarracksCommandSet")
        # CS buttons
        i = cs_t.find(f"CommandSet {prefix}_BarracksCommandSet")
        block = cs_t[i : cs_t.find("\nEnd", i) + 4] if i >= 0 else ""
        miss_btns = [
            b
            for b in re.findall(r"=\s*(Command_\S+)", block)
            if f"CommandButton {b}" not in cb_t
        ]
        m = re.search(
            rf"CommandButton Command_Construct{prefix}_Barracks_SAFE\n(.*?)End",
            cb_t,
            re.S,
        )
        cobj = re.search(r"Object\s*=\s*(\S+)", m.group(1)).group(1) if m else None
        # infantry objects
        miss_units = []
        for btn in re.findall(r"=\s*(Command_Construct\S+)", block):
            bm = re.search(rf"CommandButton {re.escape(btn)}\n(.*?)End", cb_t, re.S)
            if not bm:
                continue
            u = re.search(r"Object\s*=\s*(\S+)", bm.group(1))
            if not u:
                continue
            unit = u.group(1)
            udefs = count_object_defs(entries2, data2, unit)
            if not udefs:
                miss_units.append(unit)
        ok = (
            audit["pass"]
            and len(locs) == 1
            and csc == 1
            and not miss_btns
            and not miss_units
            and cobj
            in (f"{prefix}_Barracks", "NorthKorea_Barracks")
        )
        if not ok:
            overall = "FAIL"
        report_lines.append(
            f"""
{prefix}:
  Final file = {key}
  Object count in FINAL BIG = {len(locs)}
  Side = {side}
  CommandSet = {prefix}_BarracksCommandSet (count={csc})
  Construct button = Command_Construct{prefix}_Barracks_SAFE -> {cobj}
  Rebuilt from North Korea = YES
  Iraq content removed = {'YES' if not audit['identity_leaks'] else 'NO ' + str(audit['identity_leaks'])}
  Encoding = {audit['encoding']}
  BOM = {audit['bom']}
  Null bytes = {audit['nulls']}
  Balanced Object/End = {'YES' if audit['balanced'] else 'NO'}
  Nested Object = {'YES' if audit['nested'] else 'NO'}
  Duplicate Object = {'YES' if len(locs) != 1 else 'NO'}
  Iraq identity leak = {'YES' if audit['identity_leaks'] else 'NO'}
  Correct Side = {'YES' if not any(x.startswith('side') for x in audit['errs']) else 'NO'}
  CommandSet resolves = {'YES' if csc == 1 else 'NO'}
  Missing buttons = {miss_btns or 'none'}
  Missing units = {miss_units or 'none'}
  Parse audit = {'PASS' if ok else 'FAIL'} {audit['errs']}
  Fallback used = {'YES' if fallback[prefix] else 'NO'}
""".rstrip()
        )

    # NK unchanged check
    nk_blob2 = next(
        data2[o : o + s]
        for n, o, s in entries2
        if norm(n) == norm(nk_key)
    )
    nk_same = nk_blob2 == nk_bytes

    NOTE.write_text(
        f"DATA sha256={data_sha}\n"
        f"ART sha256={art_sha} unchanged={art_sha == BASE_ART}\n"
        f"NK barracks unchanged={nk_same}\n"
        f"OVERALL={overall}\n"
        f"Changed:\n"
        + "\n".join(f"  {c}" for c in changed)
        + "\n"
        + "\n".join(report_lines)
        + "\n"
    )
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    print("OVERALL", overall)
    print("DATA", data_sha)
    print("ART", art_sha, art_sha == BASE_ART)
    print("NK same", nk_same)
    print("fallback", fallback)
    print(NOTE.read_text())
    print("ZIP", ZIP_PATH, ZIP_PATH.stat().st_size)


if __name__ == "__main__":
    main()
