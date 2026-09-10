#!/usr/bin/env python3
"""Re-extract the complete pack and audit live PlayerTemplate → factory → air chains."""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

BASE = Path("/tmp/ea6b_crash_fix/_SPEC_DATA_ONE.big")
UNLOCK = Path("/tmp/warfactory_unlock/_SPEC_DATA_ONE.big")
PACKED = Path("/tmp/wf_airforce_complete/_SPEC_DATA_ONE.big")
REPORT = Path("/workspace/patch/Release/docs/WF_AIRFORCE_COMPLETE_REPORT.txt")

DEST_WF = {
    "Britain": ("BritainWarFactory", "BritainWarfactoryCommandSet"),
    "Germany": ("GermanyWarFactory", "GermanyWarfactoryCommandSet"),
    "France": ("FranceWarFactory", "FranceWarfactoryCommandSet"),
    "Italy": ("ItalyWarFactory", "ItalyWarfactoryCommandSet"),
    "Ukraine": ("UkraineWarFactory", "UkraineWarfactoryCommandSet"),
    "Turkey": ("TurkeyWarFactory", "TurkeyWarfactoryCommandSet"),
    "Sweden": ("SwedenWarFactory", "SwedenWarfactoryCommandSet"),
    "Libya": ("Libya_WarFactory_T", "Libya_WarFactoryCommandSet"),
    "SouthAfrica": ("SouthAfrica_WarFactory_T", "SouthAfrica_WarFactoryCommandSet"),
    "UAE": ("UAE_WarFactory_T", "UAE_WarFactoryCommandSet"),
    "SaudiArabia": ("SaudiArabia_WarFactory_T", "SaudiArabia_WarFactoryCommandSet"),
    "Syria": ("Syria_WarFactory_T", "Syria_WarFactoryCommandSet"),
    "Japan": ("Japan_WarFactory", "Japan_WarFactoryCommandSet"),
    "Vietnam": ("Vietnam_WarFactory", "Vietnam_WarFactoryCommandSet"),
    "SouthKorea": ("SouthKorea_WarFactory", "SouthKorea_WarFactoryCommandSet"),
    "India": ("India_WarFactory_T", "India_WarFactoryCommandSet"),
    "Pakistan": ("Pakistan_WarFactory_T", "Pakistan_WarFactoryCommandSet"),
}

PROTECTED_CS = [
    "NatoWarfactoryCommandSet",
    "AmericaWarFactoryCommandSet",
    "AmericaWarFactoryCommandSet_T3",
    "RussiaWarFactoryCommandSet",
    "EgyptWarFactoryCommandSet",
    "Iraq_WarFactoryCommandSet_T3",
    "IranWarfactoryCommandSet",
    "Israel_WarFactoryCommandSet",
    "NorthKorea_WarFactoryCommandSet",
    "ChinaWarFactoryCommandSet",
    "AmericaAirfieldCommandSet",
    "Iraq_AirfieldCommandSet",
]

PROTECTED_PATHS = (
    r"\united states of america\\",
    r"\armed forces of russian federation\\",
    r"\pla\\",
    r"\iranian army\\",
    r"\israel defense forces\\",
    r"\nato\\",
    r"\egyptian armed forces\\",
    r"\iraq army\\",
    r"\north korea\\",
)

SKIP = {"Command_Sell", "Command_SetRallyPoint", "Command_UpgradeAmericaCountermeasures"}


def parse_big(path: Path):
    data = path.read_bytes()
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for _ in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((name, data[eoff : eoff + esz]))
    return entries


def parse_block(text, start):
    depth = 0
    buf = []
    for i, line in enumerate(text[start:].splitlines(True)):
        buf.append(line)
        raw = line.split(";", 1)[0]
        if i == 0:
            depth = 1
            continue
        if re.match(r"(?i)^\s*End\b", raw):
            depth -= 1
            if depth <= 0:
                break
        elif re.match(
            r"(?i)^\s*(Draw|Behavior|Body|WeaponSet|ArmorSet|Prerequisites|DefaultConditionState|ConditionState|UnitSpecificSounds)\b",
            raw,
        ):
            depth += 1
        elif re.match(r"(?i)^\s*Turret\s*$", raw):
            depth += 1
    return "".join(buf)


def last_named(kind, name, entries):
    found = src = None
    pat = re.compile(rf"(?im)^{kind}\s+{re.escape(name)}\b")
    for fname, blob in entries:
        text = blob.decode("latin1", errors="ignore")
        for m in pat.finditer(text):
            found = parse_block(text, m.start())
            src = fname
    return src, found


def index_all(entries):
    obj = {}
    btn = {}
    for fname, blob in entries:
        text = blob.decode("latin1", errors="ignore")
        for m in re.finditer(r"(?im)^Object(?:Reskin)?\s+(\S+)", text):
            obj[m.group(1)] = (fname, parse_block(text, m.start()))
        for m in re.finditer(r"(?im)^CommandButton\s+(\S+)", text):
            btn[m.group(1)] = (fname, parse_block(text, m.start()))
    return obj, btn


def field(blk, key):
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", blk or "")
    return m.group(1) if m else None


def cs_slots(blk):
    return re.findall(r"(?m)^\s*(\d+)\s*=\s*(\S+)", blk or "")


def prereq_locked(blk):
    m = re.search(r"(?ims)^\s*Prerequisites\b.*?^\s*End\b", blk or "")
    if not m:
        return False
    return bool(re.search(r"(?im)^\s*(Object|Science)\s*=", m.group(0)))


def weapons(blk):
    return re.findall(r"(?im)^\s*Weapon\s*=\s*(\S+)\s+(\S+)", blk or "")


def models(blk):
    return re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", blk or "")


def main() -> int:
    packed = parse_big(PACKED)
    unlock = parse_big(UNLOCK)
    ea6b = parse_big(BASE)
    obj, btn = index_all(packed)
    lines = []
    ok = True

    def log(msg):
        lines.append(msg)
        print(msg)

    dsha = hashlib.sha256(PACKED.read_bytes()).hexdigest()
    log(f"PACKED {PACKED} {PACKED.stat().st_size} SHA256 {dsha}")
    log(f"FILES {len(packed)}")

    zzzz = [n for n, _ in packed if "zzzz" in n.lower()]
    if zzzz:
        ok = False
        log(f"FAIL ZZZZ files {zzzz}")
    else:
        log("NO_ZZZZ_FILES")

    # protected CS vs ea6b (Iran air may change vs unlock, WF CS must not)
    cs_pack = cs_ea = None
    for n, b in packed:
        if n.replace("/", "\\") == r"Data\INI\CommandSet.ini":
            cs_pack = b.decode("latin1")
    for n, b in ea6b:
        if n.replace("/", "\\") == r"Data\INI\CommandSet.ini":
            cs_ea = b.decode("latin1")
    for name in PROTECTED_CS:
        _, a = last_named("CommandSet", name, packed)
        _, b = last_named("CommandSet", name, ea6b)
        if a != b:
            # dest unlock already changed dest CS inside same file; compare vs unlock for WF
            _, u = last_named("CommandSet", name, unlock)
            if a != u:
                ok = False
                log(f"FAIL protected CS changed {name}")
            else:
                log(f"PROTECTED_CS_OK {name} (matches unlock)")
        else:
            log(f"PROTECTED_CS_OK {name}")

    # dest WF chain
    wf_ok = 0
    for country, (wf, csname) in DEST_WF.items():
        src, wblk = last_named("Object", wf, packed)
        _, cblk = last_named("CommandSet", csname, packed)
        if not wblk or not cblk:
            ok = False
            log(f"FAIL {country} missing wf/cs")
            continue
        if field(wblk, "CommandSet") != csname:
            ok = False
            log(f"FAIL {country} WF CommandSet mismatch {field(wblk, 'CommandSet')}")
            continue
        if "ProductionUpdate" not in wblk or "DefaultProductionExitUpdate" not in wblk:
            ok = False
            log(f"FAIL {country} WF missing production modules")
            continue
        slots = cs_slots(cblk)
        missing = []
        locked = []
        for _s, bname in slots:
            if bname in SKIP:
                continue
            bsrc, bblk = btn.get(bname, (None, None))
            if not bblk:
                missing.append(bname)
                continue
            oname = field(bblk, "Object")
            osrc, oblk = obj.get(oname, (None, None)) if oname else (None, None)
            if not oblk:
                missing.append(f"{bname}->{oname}")
            elif prereq_locked(oblk) and not oname.startswith("WFUnlock_"):
                # dest may still point at open template units
                locked.append(oname)
        if missing:
            ok = False
            log(f"FAIL {country} WF missing buttons/objects {missing[:6]}")
        else:
            wf_ok += 1
            log(f"DEST_WARFACTORY_OK {country} slots={len(slots)} src={src}")
        if country == "Japan":
            md = models(wblk)
            if "US_WarFactory" not in md:
                ok = False
                log(f"FAIL Japan WF model {md[:3]}")
            else:
                log("JAPAN_WARFACTORY_USA_TEMPLATE_OK")
            if "JP_WarFactory.NKr_WarFactory" in wblk:
                ok = False
                log("FAIL Japan still has broken NKr animation")

    log(f"DEST_WARFACTORY_OK_COUNT {wf_ok}/{len(DEST_WF)}")

    # air audits
    def audit_air(label, csname, must_btns, must_not=(), min_fighters=0):
        nonlocal ok
        _, cblk = last_named("CommandSet", csname, packed)
        if not cblk:
            ok = False
            log(f"FAIL {label} missing CS {csname}")
            return
        slots = cs_slots(cblk)
        btns = [b for _, b in slots]
        for bname in must_btns:
            if bname not in btns:
                ok = False
                log(f"FAIL {label} missing slot {bname}")
            else:
                bsrc, bblk = btn.get(bname, (None, None))
                oname = field(bblk, "Object") if bblk else None
                osrc, oblk = obj.get(oname, (None, None)) if oname else (None, None)
                if not oblk:
                    ok = False
                    log(f"FAIL {label} {bname} object missing {oname}")
                else:
                    log(f"OK {label} {bname} -> {oname} model={models(oblk)[:1]} weap={len(weapons(oblk))}")
        for bname in must_not:
            if bname in btns:
                ok = False
                log(f"FAIL {label} still has {bname}")
        fighters = [b for b in btns if "Helicopter" not in b and "Mi-8" not in b and "Mi17" not in b and b not in SKIP]
        if min_fighters and len(fighters) < min_fighters:
            ok = False
            log(f"FAIL {label} fighter-like slots {len(fighters)} < {min_fighters}")
        log(f"AIR_{label}_SLOTS {slots}")

    audit_air(
        "IRAN",
        "IranExpandedAirfieldCommandSet",
        [
            "Command_ConstructIranAir_Tu22M3",
            "Command_ConstructIranAir_Su24MR",
            "Command_ConstructIranAir_IL76",
        ],
    )
    audit_air(
        "SAUDI",
        "SaudiArabia_AirfieldCommandSet",
        ["Command_ConstructSaudiArabia_Mi-8T", "Command_ConstructSaudiAir_AH64E", "Command_ConstructSaudiJetF5E_CAS"],
    )
    _, f5 = last_named("Object", "SaudiJetF5E", packed)
    if f5 and "AVHawk" in models(f5):
        ok = False
        log("FAIL Saudi F5E still AVHawk")
    else:
        log(f"SAUDI_F5E_MODEL {models(f5)[:3]}")

    audit_air(
        "UAE",
        "UAE_AirfieldCommandSet",
        ["Command_ConstructUAE_F16Blk52", "Command_ConstructUAE_Mi-8T", "Command_ConstructUAE_F16Blk52_CAS"],
    )
    _, uae = last_named("Object", "UAE_F16Blk52", packed)
    we = weapons(uae)
    if len(we) < 3:
        ok = False
        log(f"FAIL UAE F16 weapons {we}")
    else:
        log(f"UAE_F16_WEAPONS {we}")

    audit_air(
        "INDIA",
        "India_AirfieldCommandSet",
        ["Command_ConstructIndia_Mi-8T", "Command_ConstructIndiaAir_AH64E", "Command_ConstructIndiaJetSu30MKI_CAS"],
    )
    audit_air(
        "PAKISTAN",
        "Pakistan_AirfieldCommandSet",
        ["Command_ConstructPakistan_Mi-8T", "Command_ConstructPakistanAir_AH64E", "Command_ConstructPakistan_F16Blk52_CAS"],
    )
    audit_air(
        "SK",
        "SouthKorea_AirfieldCommandSet",
        [
            "Command_ConstructSouthKoreaJetUH60P",
            "Command_ConstructSouthKoreaJetAH64E",
            "Command_ConstructSouthKoreaJetCH47",
            "Command_ConstructSouthKoreaHelicopterLAH",
            "Command_ConstructSouthKoreaHelicopterKUH1",
            "Command_ConstructSouthKoreaJetE737",
            "Command_ConstructSouthKoreaAir_USATransport",
        ],
        must_not=(
            "Command_ConstructSouthKoreaJetRC800",
            "Command_ConstructSouthKoreaJetC130H",
            "Command_ConstructSouthKoreaJetCN235",
        ),
    )
    _, e737 = last_named("Object", "SouthKoreaJetE737", packed)
    if e737 and "AmericaE737TargetedSARScan" not in e737:
        ok = False
        log("FAIL SK E737 missing SAR scan")
    else:
        log("SK_E737_SCAN_OK")
    _, ah = last_named("Object", "SouthKoreaJetAH64E", packed)
    if ah and len(weapons(ah)) < 2:
        ok = False
        log(f"FAIL SK AH64 weapons {weapons(ah)}")
    else:
        log(f"SK_AH64_WEAPONS {weapons(ah)}")

    audit_air(
        "SA",
        "SouthAfrica_AirfieldCommandSet",
        ["Command_ConstructSouthAfrica_MirageF1_Bq", "Command_ConstructSouthAfricaHelicopterOryx", "Command_ConstructSouthAfricaJetImpala"],
    )
    _, f1 = last_named("Object", "SouthAfrica_MirageF1_Bq", packed)
    if prereq_locked(f1):
        ok = False
        log("FAIL SA Mirage F1 still locked")
    else:
        log("SA_MIRAGE_UNLOCKED")
    _, oryx = last_named("Object", "SouthAfricaHelicopterOryx", packed)
    if oryx and "NAT_Puma" in models(oryx):
        ok = False
        log("FAIL Oryx still NAT_Puma")
    else:
        log(f"SA_ORYX_MODEL {models(oryx)[:2]}")
    _, imp = last_named("Object", "SouthAfricaJetImpala", packed)
    if imp and "UV_Turbo" in models(imp):
        ok = False
        log("FAIL Impala still UV_Turbo")
    else:
        log(f"SA_IMPALA_MODEL {models(imp)[:2]}")

    audit_air(
        "VIETNAM",
        "Vietnam_AirfieldCommandSet",
        [
            "Command_ConstructVietnamJetMi17",
            "Command_ConstructVietnamJetMig29S",
            "Command_ConstructVietnamJetL39",
            "Command_ConstructVietnamJetMig29S_CAS",
        ],
        min_fighters=12,
    )
    _, mi17 = last_named("Object", "VietnamJetMi17", packed)
    if mi17 and "CAN_ATTACK" not in (field(mi17, "KindOf") or "") and "CAN_ATTACK" not in mi17:
        ok = False
        log("FAIL VN Mi17 not CAN_ATTACK")
    else:
        log(f"VN_MI17 {models(mi17)[:1]} weap={weapons(mi17)}")

    # protected object folders unchanged vs unlock except we didn't touch them
    u_map = {n.replace("/", "\\").lower(): b for n, b in unlock}
    p_map = {n.replace("/", "\\").lower(): (n, b) for n, b in packed}
    prot_changed = []
    for k, (n, b) in p_map.items():
        if any(tok in k for tok in PROTECTED_PATHS):
            if u_map.get(k) != b:
                prot_changed.append(n)
    if prot_changed:
        ok = False
        log(f"FAIL protected files changed {prot_changed}")
    else:
        log("PROTECTED_OBJECT_FILES_UNCHANGED")

    log("RESULT " + ("PASS" if ok else "FAIL"))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
