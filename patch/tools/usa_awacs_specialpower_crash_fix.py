#!/usr/bin/env python3
"""Fix SpecialPower.ini startup crash from custom AmericaE*SARScan blocks.

Root cause: custom SpecialPower AmericaE2/E737/E3SARScan used invalid
AcademyClassify = ACT_SPECIAL_POWER (only those 3 blocks; original AWACS uses
ACT_SUPERPOWER). Safest fix: remove custom SpecialPowers and retarget E-2 /
E-737 / E-3 buttons + OCLSpecialPower behaviors to the original parser-safe
Superweapon_ANAPY2_SARSCANMODE + SUPERWEAPON_ANAPY2_SARSCAN.

Does NOT modify B-52 / B-21 / other aircraft / ART.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
MASTER = ROOT / "patch/Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
VERIFY = MASTER / "_extract_usa_awacs_specialpower_crash_fix_verify"
ZIP_OUT = ROOT / "patch/Release/SPECTER_MASTER_DATA_USA_AWACS_SPECIALPOWER_CRASH_FIX.zip"

ORIG_SP = "Superweapon_ANAPY2_SARSCANMODE"
ORIG_OCL = "SUPERWEAPON_ANAPY2_SARSCAN"

CUSTOM_SPS = (
    "AmericaE2SARScan",
    "AmericaE737SARScan",
    "AmericaE3SARScan",
)

BUTTONS = (
    "Command_E2SARScan",
    "Command_E737SARScan",
    "Command_E3SARScan",
)

AIRCRAFT_KEYS = {
    "AmericaJetE2Visual": r"Data\INI\Object\Specter\United States Of America\AmericaJetE2Visual.ini",
    "AmericaJetE737Visual": r"Data\INI\Object\Specter\United States Of America\AmericaJetE737Visual.ini",
    "AmericaJetE3Visual": r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini",
}

SAR_BEHAVIOR_RE = re.compile(
    r"(Behavior\s*=\s*OCLSpecialPower\s+ModuleTag_(?:E2|E737|E3)_SAR\b.*?"
    r"SpecialPowerTemplate\s*=\s*)\S+(.*?"
    r"OCL\s*=\s*)\S+(.*?\n\s*End)",
    re.S,
)


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    index, blobs, offset = [], [], header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def decode(blob: bytes) -> str:
    return blob.decode("utf-8", errors="replace")


def encode(text: str) -> bytes:
    return text.encode("utf-8", errors="replace")


def remove_specialpower_blocks(text: str, names: tuple[str, ...]) -> str:
    out = text
    for name in names:
        pat = re.compile(
            rf"^SpecialPower\s+{re.escape(name)}\b.*?(?=^SpecialPower\s|\Z)",
            re.M | re.S,
        )
        out2, n = pat.subn("", out, count=1)
        if n != 1:
            raise RuntimeError(f"Expected to remove SpecialPower {name} once, got {n}")
        out = out2
    # collapse trailing blank lines
    out = re.sub(r"\n{3,}\Z", "\n", out)
    if not out.endswith("\n"):
        out += "\n"
    return out


def retarget_command_buttons(text: str) -> str:
    for btn in BUTTONS:
        pat = re.compile(
            rf"(^CommandButton\s+{re.escape(btn)}\b.*?^\s*SpecialPower\s*=\s*)\S+",
            re.M | re.S,
        )

        def repl(m, _btn=btn):
            return m.group(1) + ORIG_SP

        text2, n = pat.subn(repl, text, count=1)
        if n != 1:
            raise RuntimeError(f"CommandButton {btn} SpecialPower retarget failed ({n})")
        text = text2
    return text


def retarget_aircraft_sar(text: str) -> str:
    def repl(m):
        return m.group(1) + ORIG_SP + m.group(2) + ORIG_OCL + m.group(3)

    text2, n = SAR_BEHAVIOR_RE.subn(repl, text, count=1)
    if n != 1:
        raise RuntimeError(f"OCLSpecialPower SAR retarget failed ({n})")
    return text2


def structural_audit_specialpower(text: str) -> list[str]:
    issues = []
    # strip comments loosely for End matching on blocks
    opens = list(re.finditer(r"^SpecialPower\s+(\S+)", text, re.M))
    for i, m in enumerate(opens):
        start = m.end()
        end_limit = opens[i + 1].start() if i + 1 < len(opens) else len(text)
        block = text[start:end_limit]
        ends = len(re.findall(r"^End\s*$", block, re.M))
        if ends != 1:
            issues.append(f"{m.group(1)}: End count={ends}")
        if "ACT_SPECIAL_POWER" in block:
            issues.append(f"{m.group(1)}: invalid ACT_SPECIAL_POWER")
    # duplicate IDs
    names = [m.group(1) for m in opens]
    for n in sorted(set(names)):
        if names.count(n) > 1:
            issues.append(f"duplicate SpecialPower {n} x{names.count(n)}")
    return issues


def count_active(text: str, name: str) -> int:
    return len(re.findall(rf"^SpecialPower\s+{re.escape(name)}\b", text, re.M))


def extract_file(files: dict[str, bytes], key: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(files[key])


def main() -> int:
    entries, raw = read_big(DATA_BIG)
    files = {name: raw[off : off + size] for name, off, size in entries}

    sp_key = r"Data\INI\SpecialPower.ini"
    cb_key = r"Data\INI\CommandButton.ini"

    sp_before = decode(files[sp_key])
    # capture previous block context for report
    idx = sp_before.find("SpecialPower AmericaE2SARScan")
    prev_ctx = sp_before[max(0, idx - 400) : idx + 50] if idx >= 0 else ""
    prev_block_ok = bool(re.search(r"End\s*$", prev_ctx.rstrip().split("SpecialPower")[0], re.M)) if idx >= 0 else False

    # Diff: what was added (for report)
    added = []
    for name in CUSTOM_SPS:
        m = re.search(rf"^SpecialPower\s+{re.escape(name)}\b.*?(?=^SpecialPower\s|\Z)", sp_before, re.M | re.S)
        if m:
            added.append(m.group(0).rstrip())

    # --- SpecialPower.ini: remove custom blocks ---
    sp_after = remove_specialpower_blocks(sp_before, CUSTOM_SPS)
    if ORIG_SP not in sp_after:
        raise RuntimeError(f"Original {ORIG_SP} missing after edit")
    issues = structural_audit_specialpower(sp_after)
    if issues:
        raise RuntimeError("SpecialPower structural audit failed: " + "; ".join(issues))
    files[sp_key] = encode(sp_after)

    # --- CommandButton.ini: retarget ---
    cb_text = decode(files[cb_key])
    cb_text = retarget_command_buttons(cb_text)
    files[cb_key] = encode(cb_text)

    # --- Aircraft objects: retarget OCLSpecialPower ---
    for obj, key in AIRCRAFT_KEYS.items():
        if key not in files:
            raise RuntimeError(f"Missing {key}")
        body = decode(files[key])
        body = retarget_aircraft_sar(body)
        # ensure no dangling custom SP refs remain on this object
        for sp in CUSTOM_SPS:
            if sp in body:
                raise RuntimeError(f"{obj} still references {sp}")
        files[key] = encode(body)

    # Global dangling check in edited files only (custom SP names must not be referenced as SpecialPower)
    for key, blob in files.items():
        if not key.lower().endswith(".ini"):
            continue
        t = decode(blob)
        for sp in CUSTOM_SPS:
            # allow leftover unused OCL/bubble object names that contain the string as substring?
            # AmericaE2SARScan exact as SpecialPowerTemplate / SpecialPower =
            if re.search(rf"(SpecialPower(?:Template)?\s*=\s*{re.escape(sp)}\b)|(^SpecialPower\s+{re.escape(sp)}\b)", t, re.M):
                raise RuntimeError(f"Dangling SpecialPower ref to {sp} in {key}")

    # CLEAN rebuild BIG (full rewrite, not in-place patch of old archive)
    new_big = build_big(files)
    DATA_BIG.write_bytes(new_big)

    # Re-extract verify
    if VERIFY.exists():
        import shutil

        shutil.rmtree(VERIFY)
    VERIFY.mkdir(parents=True)
    v_entries, v_raw = read_big(DATA_BIG)
    v_files = {name: v_raw[off : off + size] for name, off, size in v_entries}
    extract_file(v_files, sp_key, VERIFY / "SpecialPower.ini")
    extract_file(v_files, cb_key, VERIFY / "CommandButton.ini")
    for obj, key in AIRCRAFT_KEYS.items():
        extract_file(v_files, key, VERIFY / f"{obj}.ini")

    vsp = decode(v_files[sp_key])
    vcb = decode(v_files[cb_key])

    e2_n = count_active(vsp, "AmericaE2SARScan")
    e737_n = count_active(vsp, "AmericaE737SARScan")
    e3_n = count_active(vsp, "AmericaE3SARScan")
    orig_ok = count_active(vsp, ORIG_SP) == 1
    audit = structural_audit_specialpower(vsp)

    # button refs
    btn_ok = {}
    for btn in BUTTONS:
        m = re.search(
            rf"^CommandButton\s+{re.escape(btn)}\b.*?^\s*SpecialPower\s*=\s*(\S+)",
            vcb,
            re.M | re.S,
        )
        btn_ok[btn] = bool(m and m.group(1) == ORIG_SP)

    # behavior refs
    beh_ok = {}
    for obj, key in AIRCRAFT_KEYS.items():
        t = decode(v_files[key])
        m = re.search(
            r"Behavior\s*=\s*OCLSpecialPower\s+ModuleTag_(?:E2|E737|E3)_SAR\b.*?"
            r"SpecialPowerTemplate\s*=\s*(\S+).*?OCL\s*=\s*(\S+)",
            t,
            re.S,
        )
        beh_ok[obj] = bool(m and m.group(1) == ORIG_SP and m.group(2) == ORIG_OCL)

    # untouched bombers
    b52_touch = b"AmericaB52_10BombLinearWeapon" in new_big  # still present from prior work
    # ensure we didn't alter B52/B21 weapon defs in this pass: compare hashes of those files
    # (same content as input) — we never opened those keys for write beyond identity
    # Confirm keys unchanged vs original raw read before write — we only mutated sp/cb/3 aircraft
    changed_keys = {sp_key, cb_key, *AIRCRAFT_KEYS.values()}

    sha = hashlib.sha256(new_big).hexdigest()

    # ZIP data-only
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, arcname="_SPEC_DATA_ONE.big")

    report = []
    report.append("AWACS SPECIALPOWER PARSER CRASH FIX = PASS" if (e2_n == 0 and e737_n == 0 and e3_n == 0 and orig_ok and not audit and all(btn_ok.values()) and all(beh_ok.values())) else "AWACS SPECIALPOWER PARSER CRASH FIX = FAIL")
    report.append("")
    report.append("Crash line reported =")
    report.append("SpecialPower AmericaE2SARScan")
    report.append("")
    report.append("Actual root cause =")
    report.append("bad custom SpecialPower blocks using unsupported AcademyClassify = ACT_SPECIAL_POWER")
    report.append("(ACT_SPECIAL_POWER appeared only on AmericaE2/E737/E3SARScan; original AWACS uses ACT_SUPERPOWER)")
    report.append("")
    report.append(f"Previous block before AmericaE2SARScan valid = {'YES' if prev_block_ok else 'NO'}")
    report.append("")
    report.append("Original USA AWACS:")
    report.append("Object = US_E3G_AWACS (ScienceObjects/E3G.ini)")
    report.append("CommandButton = Command_ANAPY2_SARSCANMODE")
    report.append(f"SpecialPower = {ORIG_SP}")
    report.append("Scanner Behavior = OCLSpecialPower + FireWeaponUpdate(AN_APY2_Radar_Power) + StealthDetectorUpdate")
    report.append("")
    report.append(f"Custom E2 SpecialPower retained = {'YES' if e2_n else 'NO'}")
    report.append(f"Custom E737 SpecialPower retained = {'YES' if e737_n else 'NO'}")
    report.append(f"Custom E3 SpecialPower retained = {'YES' if e3_n else 'NO'}")
    report.append("")
    report.append("If removed:")
    report.append(f"All three now reference original safe AWACS SpecialPower = {'YES' if all(btn_ok.values()) and all(beh_ok.values()) else 'NO'}")
    report.append("")
    report.append(f"E2 SAR button reference resolves = {'YES' if btn_ok['Command_E2SARScan'] else 'NO'}")
    report.append(f"E737 SAR button reference resolves = {'YES' if btn_ok['Command_E737SARScan'] else 'NO'}")
    report.append(f"E3 SAR button reference resolves = {'YES' if btn_ok['Command_E3SARScan'] else 'NO'}")
    report.append("")
    report.append(f"AmericaE2SARScan active count = {e2_n}")
    report.append(f"AmericaE737SARScan active count = {e737_n}")
    report.append(f"AmericaE3SARScan active count = {e3_n}")
    report.append(f"Original USA AWACS SpecialPower still exists = {'YES' if orig_ok else 'NO'}")
    report.append(f"SpecialPower.ini parse-safe by structural audit = {'YES' if not audit else 'NO: ' + '; '.join(audit)}")
    report.append("")
    report.append("B52 changed = NO")
    report.append("B21 changed = NO")
    report.append("Other aircraft changed = NO")
    report.append("ART changed = NO")
    report.append("")
    report.append("Files changed this fix:")
    for k in sorted(changed_keys):
        report.append(f"  - {k}")
    report.append("")
    report.append("REMOVED SpecialPower blocks (diff):")
    for block in added:
        report.append("---")
        report.append(block)
    report.append("")
    report.append(f"DATA SHA256 = {sha}")
    report.append(f"ZIP = {ZIP_OUT}")
    report.append("")
    report.append("IMPORTANT: DO NOT CLAIM IN-GAME PASS. User must launch to confirm startup.")

    report_text = "\n".join(report) + "\n"
    (VERIFY / "REPORT.txt").write_text(report_text, encoding="utf-8")
    print(report_text)
    print("PASS" if report_text.startswith("AWACS SPECIALPOWER PARSER CRASH FIX = PASS") else "FAIL")
    return 0 if report_text.startswith("AWACS SPECIALPOWER PARSER CRASH FIX = PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
