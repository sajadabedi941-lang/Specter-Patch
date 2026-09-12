#!/usr/bin/env python3
"""DATA-only Iraq unlock + air pass on the SPECTER1 working baseline.

Starts from /tmp/specter1_clean_copy/_SPEC_DATA_ONE.big
(SHA256 9629b6a092aaffb606a01af70e29b88d6c38c8dfc0958fe2d4c3a32c8d1da635).

Does not rebuild ART. Does not write CommandSet_ZZZZ files.
Does not start from PR #473 / #474 packs.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/specter1_clean_copy/_SPEC_DATA_ONE.big")
EXPECTED_DATA_SHA = "9629b6a092aaffb606a01af70e29b88d6c38c8dfc0958fe2d4c3a32c8d1da635"
OUT_DIR = Path("/tmp/specter1_iraq_work")
REPO_OVERLAY = Path("/workspace/patch/Data/INI/Object/Specter/IraqUnlockSpecter1")

CS_INI = r"data\ini\commandset.ini"
WPN_INI = r"data\ini\weapon.ini"
RUS_TU22 = r"data\ini\object\specter\armed forces of russian federation\airforce\tu22m3m.ini"
IRQ_TU22 = r"data\ini\object\specter\iraq army\airforce\iraq_tu-22m3.ini"
IRQ_MIG21 = r"data\ini\object\specter\iraq army\airforce\iraqjetmig21.ini"
IRQ_WF = r"data\ini\object\specter\iraq army\buildings\iraq_warfactory.ini"
IRQ_MIC = r"data\ini\object\specter\iraq army\buildings\iraq_mic.ini"

UNIT_UNLOCK_KEYS = {
    r"data\ini\object\specter\iraq army\airforce\iraq_miragef1-bq.ini",
    r"data\ini\object\specter\iraq army\airforce\iraq_su-24mk.ini",
    r"data\ini\object\specter\iraq army\airforce\iraq_su-24mr.ini",
    r"data\ini\object\specter\iraq army\airforce\iraq_su-22m3.ini",
    r"data\ini\object\specter\iraq army\airforce\iraq_mi-8.ini",
    r"data\ini\object\specter\iraq army\tracked\2s1.ini",
    r"data\ini\object\specter\iraq army\apc\btr90.ini",
    r"data\ini\object\specter\iraq army\airdefense\9k33.ini",
    r"data\ini\object\specter\iraq army\tracked\assadbabel2.ini",
    r"data\ini\object\specter\iraq army\wheeled\alnida.ini",
    r"data\ini\object\specter\iraq army\wheeled\abbaslauncher.ini",
    r"data\ini\object\specter\iraq army\wheeled\9p117.ini",
    r"data\ini\object\specter\iraq army\wheeled\karrar-2.ini",
    r"data\ini\object\specter\iraq army\wheeled\lamiaa.ini",
    r"data\ini\object\specter\iraq army\airdefense\b340.ini",
    r"data\ini\object\specter\iraq army\airdefense\fahad3.ini",
    r"data\ini\object\specter\iraq army\infantry\mortarteam.ini",
    r"data\ini\object\specter\iraq army\infantry\kornetteam.ini",
    r"data\ini\object\specter\iraq army\infantry\heavysniper.ini",
    r"data\ini\object\specter\iraq army\infantry\enginer.ini",
    r"data\ini\object\specter\iraq army\infantry\specialforces.ini",
    r"data\ini\object\specter\iraq army\infantry\airborne.ini",
    r"data\ini\object\specter\iraq army\drones\sarab3.ini",
    r"data\ini\object\specter\iraq army\drones\ababil200.ini",
    r"data\ini\object\specter\iraq army\drones\ababil200r.ini",
}

PROTECTED_MUST_NOT_CHANGE = (
    r"\united states of america\\",
    r"\pla\\",
    r"\iranian army\\",
    r"\israel defense forces\\",
    r"\nato\\",
    r"\egyptian armed forces\\",
    r"\north korea\\",
    r"\japan self-defense",
    r"\south korean",
    r"\vietnam",
    r"\saudi",
    r"\united arab emirates",
    r"\indian armed",
    r"\pakistan",
    r"\german",
    r"\french",
    r"\british",
    r"\italian",
    r"\turkish",
    r"\swedish",
    r"\ukrain",
    r"\libyan",
    r"\south african",
    r"\syrian",
)

L159_WEAPON = """Weapon IraqJetL159_WpnBomb
  PrimaryDamage           = 1750.0
  PrimaryDamageRadius     = 30.0
  SecondaryDamage         = 800.0
  SecondaryDamageRadius   = 10.0
  AttackRange             = 960.0
  MinimumAttackRange      = 500.0
  AcceptableAimDelta      = 12
  DamageType              = ARMOR_PIERCING
  DeathType               = EXPLODED
  WeaponSpeed             = 9999
  ProjectileObject        = GBU24_GuidedBombObject
  FireFX                  = FX_AuroraBombLaunch
  ProjectileDetonationFX  = Mirv_HE_Explosion
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 1350
  ClipSize                = 3
  ClipReloadTime          = 13000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
  AntiAirborneVehicle     = No
  AntiGround              = Yes
End
"""

RUS_BOMB_OLD = """  WeaponSet
    Conditions            = None 
    Weapon                = PRIMARY    3x_FAB500_TU22M3M_CRF
    Weapon                = SECONDARY  3x_FAB500_TU22M3M_CRB
    Weapon                = TERTIARY   2x_FAB500_TU22M3M_WR
  End"""

RUS_BOMB_NEW = """  WeaponSet
    Conditions            = None 
    Weapon                = PRIMARY    Kab2500_LeaserGuidedBomb
    PreferredAgainst      = PRIMARY    STRUCTURE VEHICLE
    AutoChooseSources     = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI
  End"""


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


def build_big_ordered(entries):
    header_size = 16
    encoded = [(n.encode("latin1"), b) for n, b in entries]
    for nb, _blob in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for nb, blob in encoded:
        index.append((nb, offset, len(blob)))
        blobs.append(blob)
        offset += len(blob)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def nl_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def decode(b: bytes) -> str:
    return b.decode("latin1")


def encode(text: str) -> bytes:
    return text.encode("latin1")


def empty_prereqs(text: str) -> tuple[str, int]:
    nl = nl_of(text)
    n = 0

    def repl(m: re.Match) -> str:
        nonlocal n
        n += 1
        indent = m.group(1)
        return f"{indent}Prerequisites{nl}{indent}End{nl}"

    new = re.sub(
        r"(?im)^([ \t]*)Prerequisites\b[^\r\n]*\r?\n(?:(?!^[ \t]*End\s*$).*\r?\n)*[ \t]*End\s*\r?\n",
        repl,
        text,
    )
    return new, n


SCIENCE_REQ = re.compile(
    r"(?im)^[ \t]*Science\s*=\s*(SCIENCE_Tu-22|SCIENCE_Alhussien|SCIENCE_Rank[0-9]+|SCIENCE_IraqReconnaissance)\s*\r?\n"
)


def strip_object_science_req(text: str) -> tuple[str, int]:
    n = len(SCIENCE_REQ.findall(text))
    return SCIENCE_REQ.sub("", text), n


def remove_commandset_upgrades(text: str) -> str:
    text = re.sub(
        r"(?im)^[ \t]*Behavior\s*=\s*CommandSetUpgrade\b[\s\S]*?^[ \t]*End\s*\r?\n",
        "",
        text,
    )
    text = re.sub(
        r"(?im)^;---------------- Tire Upgrades[\s\S]*?;----------------- End Of Tier Upgrades\s*\r?\n",
        "",
        text,
    )
    return text


def set_first_commandset(text: str, new_cs: str) -> str:
    return re.sub(
        r"(?im)^([ \t]*)CommandSet\s*=\s*\S+",
        rf"\1CommandSet       = {new_cs}",
        text,
        count=1,
    )


def insert_cs_slot(cs_text: str, cs_name: str, slot: str, button: str) -> str:
    nl = "\r\n" if "\r\n" in cs_text else "\n"
    pat = re.compile(
        rf"(?im)^(CommandSet {re.escape(cs_name)}\s*\r?\n)(.*?)(^End\s*\r?\n)",
        re.S,
    )
    m = pat.search(cs_text)
    if not m:
        raise SystemExit(f"missing CommandSet {cs_name}")
    body = m.group(2)
    if re.search(rf"(?im)^\s*{re.escape(slot)}\s*=", body):
        body = re.sub(
            rf"(?im)^(\s*{re.escape(slot)}\s*=\s*)\S+",
            rf"\g<1>{button}",
            body,
        )
    else:
        prev = str(int(slot) - 1)
        prev_m = re.search(rf"(?im)^(\s*{re.escape(prev)}\s*=\s*\S+\s*\r?\n)", body)
        line = f"  {slot} = {button}{nl}"
        if prev_m:
            body = body[: prev_m.end()] + line + body[prev_m.end() :]
        else:
            body = line + body
    return cs_text[: m.start()] + m.group(1) + body + m.group(3) + cs_text[m.end() :]


def make_iraq_tu22(rus_text: str) -> str:
    nl = nl_of(rus_text)
    text = rus_text
    text = re.sub(r"(?im)^Object RussiaJetTu22M3M\s*$", "Object Iraq_Tu-22M3", text)
    text = re.sub(r"(?im)^(  Side\s*=\s*)Russia\s*$", r"\1Iraq", text)
    text = re.sub(r"(?im)^(  DisplayName\s*=\s*)OBJECT:Tu22M3M\s*$", r"\1OBJECT:Tu-22M3", text)
    text = re.sub(r"(?im)^(  SelectPortrait\s*=\s*)rus_tu22m3m\s*$", r"\1irq_tu22", text)
    text = re.sub(r"(?im)^(  ButtonImage\s*=\s*)rus_tu22m3m\s*$", r"\1irq_tu22", text)
    bomb_old = RUS_BOMB_OLD.replace("\n", nl)
    bomb_new = RUS_BOMB_NEW.replace("\n", nl)
    if bomb_old not in text:
        raise SystemExit("Iraq Tu-22 clone: could not rewrite Russian bomb WeaponSet")
    text = text.replace(bomb_old, bomb_new, 1)
    if not re.search(r"(?im)^[ \t]*Prerequisites\b", text):
        text = re.sub(
            r"(?im)^(  Side\s*=\s*Iraq\s*\r?\n)",
            rf"\1{nl}  Prerequisites{nl}  End{nl}",
            text,
            count=1,
        )
    text, _ = empty_prereqs(text)
    text, _ = strip_object_science_req(text)
    return text


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing SPECTER1 DATA BIG {SRC_DATA}")
    src_bytes = SRC_DATA.read_bytes()
    src_sha = hashlib.sha256(src_bytes).hexdigest()
    if src_sha != EXPECTED_DATA_SHA:
        raise SystemExit(f"BASELINE HASH MISMATCH {src_sha} != {EXPECTED_DATA_SHA}")

    src = parse_big(SRC_DATA)
    by_key = {n.replace("/", "\\").lower(): (n, b) for n, b in src}
    stats = {"prereq_files": 0, "prereq_blocks": 0, "science_lines": 0}

    rus_name, rus_blob = by_key[RUS_TU22]
    rus_text = decode(rus_blob)
    rus_nl = nl_of(rus_text)
    bomb_old = RUS_BOMB_OLD.replace("\n", rus_nl)
    bomb_new = RUS_BOMB_NEW.replace("\n", rus_nl)
    if bomb_old not in rus_text:
        raise SystemExit("Russia Tu-22M3M default WeaponSet not found as expected")
    rus_text = rus_text.replace(bomb_old, bomb_new, 1)
    if "RUS_TU22M3M" not in rus_text or "Kab2500_LeaserGuidedBomb" not in rus_text:
        raise SystemExit("Russia Tu-22 visual/bomb rewrite failed")
    if rus_text.count("Object RussiaJetTu22M3M") != 1:
        raise SystemExit("Russia object header mutated")

    irq_tu_text = make_iraq_tu22(decode(rus_blob))
    if "RUS_TU22M3M" not in irq_tu_text or "Object Iraq_Tu-22M3" not in irq_tu_text:
        raise SystemExit("Iraq Tu-22 clone failed")
    if "Iraq_Tu22m3" in irq_tu_text:
        raise SystemExit("Iraq Tu-22 still references old Iraq W3D")

    out = []
    changed = []
    for name, blob in src:
        key = name.replace("/", "\\").lower()
        text = decode(blob)
        new = text

        if key == CS_INI:
            new = insert_cs_slot(new, "Iraq_HeavyAirBaseCommandSet", "3", "Command_ConstructIraq_Tu-22M3")
            new = insert_cs_slot(new, "Iraq_LargeAirBaseCommandSet", "16", "Command_ConstructIraq_Tu-22M3")
            new = insert_cs_slot(new, "Iraq_MICCommandSet3", "2", "Command_ConstructIraq_Karrar2")
            if "SaudiArabia_AirfieldCommandSet" not in new or "Japan_WarFactoryCommandSet" not in new:
                raise SystemExit("CommandSet.ini lost protected blocks")

        elif key == WPN_INI:
            nl = nl_of(new)
            block = L159_WEAPON.replace("\n", nl)
            new = new.rstrip() + nl + nl + block

        elif key == RUS_TU22:
            new = rus_text

        elif key == IRQ_TU22:
            new = irq_tu_text

        elif key == IRQ_MIG21:
            new = re.sub(r"(?im)^(Scale\s*=\s*)0\.82\s*$", r"\g<1>0.90", new, count=1)

        elif key == IRQ_WF:
            new = set_first_commandset(new, "Iraq_WarFactoryCommandSet_T3")
            new = remove_commandset_upgrades(new)

        elif key == IRQ_MIC:
            new = set_first_commandset(new, "Iraq_MICCommandSet3")
            new = remove_commandset_upgrades(new)

        elif key in UNIT_UNLOCK_KEYS:
            new, pn = empty_prereqs(new)
            new, sn = strip_object_science_req(new)
            if pn or sn:
                stats["prereq_files"] += 1
                stats["prereq_blocks"] += pn
                stats["science_lines"] += sn

        if new != text:
            changed.append(name)
            out.append((name, encode(new)))
        else:
            out.append((name, blob))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(out)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    dsha = hashlib.sha256(data_big).hexdigest()
    print("DATA", dsha, len(data_big), "files", len(out))
    print("CHANGED")
    for n in changed:
        print(" ", n)
        low = n.replace("/", "\\").lower()
        if any(tok in low for tok in PROTECTED_MUST_NOT_CHANGE):
            if "iraq army" not in low:
                raise SystemExit(f"protected path changed: {n}")
    print("STATS", stats)

    REPO_OVERLAY.mkdir(parents=True, exist_ok=True)
    (REPO_OVERLAY / "Iraq_Tu-22M3.ini").write_bytes(encode(irq_tu_text))
    (REPO_OVERLAY / "IraqJetL159_WpnBomb.ini").write_text(
        L159_WEAPON.replace("\n", "\r\n"), encoding="latin1"
    )
    (OUT_DIR / "SHA256.txt").write_text(
        "DATA  _SPEC_DATA_ONE.big\n"
        f"SHA256 {dsha}\n"
        "ART    unchanged SPECTER1 working baseline\n"
        "SHA256 2eb2ff5bc4a762aa44702ecfbd67c7e21f9986c0026fcc3fccb85ea62a8bb761\n"
    )
    print("PACK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
