#!/usr/bin/env python3
"""Al-Fahd500 final stats vs immutable 9P117 MOTHER baseline.

Live DATA baseline: SPECTER_IRAQ_MISSILE_QUEUE_SLOTS
ART is unchanged (keep previous complete ART BIG).

MOTHER (do not modify Iraq_R11ScudB / SRBM_ALHIJARAH_HE / HE_9M729_450kg):
  range scale 1000 km -> AttackRange 1720
  400 kg warhead -> PrimaryDamage 2000 + death HE_9M729_450kg 2200
  accuracy 10/100 -> ScatterRadius 175
  radar stealth 5/100 -> projectile on radar, MaxHealth 400
  production listed 20s / actual packed BuildTime 17s / BuildCost 1200

Al-Fahd500:
  range equal (1720)
  1600 kg = 4x damage (8000 + dedicated death 8800)
  accuracy equal (175)
  stealth 20/100 -> RadarPriority LOCAL_UNIT_ONLY + MaxHealth 1600
  BuildTime 30s / BuildCost 2200
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_QUEUE_SLOTS/_SPEC_DATA_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD500_STATS"
UNIT_SRC = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlFahd500.ini"
PROJ_SRC = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Iraq_AlFahd500_Projectile.ini"
WEP_SRC = ROOT / "patch/Data/INI/Weapon/Weapon_Iraq_AlFahd500.ini"

BASE_DATA_SHA = "a794a57a028aae4ec2e6adcb7a96030f34e21935181c0c02962923fea9dd0cd1"
BASE_DATA_SIZE = 366376372

CB_KEY = r"Data\INI\CommandButton.ini"
CS_KEY = r"Data\INI\CommandSet.ini"
CSF_KEY = r"Data\English\generals.csf"
UNIT_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
PROJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Iraq_AlFahd500_Projectile.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
WEP_OVERRIDE_KEY = r"Data\INI\Weapon\Weapon_Iraq_AlFahd500.ini"

TOOLTIP = (
    "Al-Fahd500\n"
    "برد: 1000 کیلومتر\n"
    "سرجنگی: 1600 کیلوگرم\n"
    "دقت نقطه‌زنی: 10/100\n"
    "رادارگریزی: 20/100\n"
    "زمان بازسازی: 30 ثانیه\n"
    "قیمت: 2200 دلار"
)

CSF_LABELS = {
    "OBJECT:Iraq_AlFahd500": "Al-Fahd500",
    "CONTROLBAR:ToolTipSpecterMissileA": TOOLTIP,
}


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes) -> dict[str, bytes]:
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


def parse_index(data: bytes):
    archive_size = struct.unpack(">I", data[4:8])[0]
    count = struct.unpack(">I", data[8:12])[0]
    header_size = struct.unpack(">I", data[12:16])[0]
    pos = 16
    files = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files.append((name, off, size))
    return archive_size, count, header_size, pos, files


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index = []
    blobs = []
    offset = header_size
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
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")


def command_block(text: str, kind: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text)
    return m.group(0) if m else None


def slot_map(block: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    expected = header
    for name, off, size in sorted(files, key=lambda x: x[1]):
        if off != expected:
            issues.append(f"overlap/gap {name}")
            break
        expected = off + size
    if expected != len(blob):
        issues.append("trailing gap/overflow")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def csf_parse(csf: bytes):
    if csf[:4] != b" FSC":
        raise SystemExit(f"unexpected CSF magic {csf[:4]!r}")
    magic, ver, nlab, nstr, unused, lang = struct.unpack_from("<4sIIIII", csf, 0)
    labels = []
    pos = 24
    while pos < len(csf):
        if csf[pos : pos + 4] != b" LBL":
            break
        pos += 4
        cnt, nlen = struct.unpack_from("<II", csf, pos)
        pos += 8
        name = csf[pos : pos + nlen].decode("latin1")
        pos += nlen
        strs = []
        for _ in range(cnt):
            smag = csf[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4
            raw = csf[pos : pos + slen * 2]
            pos += slen * 2
            val = bytes(x ^ 0xFF for x in raw).decode("utf-16le")
            extra = None
            if smag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4
                extra = csf[pos : pos + elen]
                pos += elen
            strs.append((smag, val, extra))
        labels.append((name, strs))
    return magic, ver, unused, lang, labels


def csf_build(magic, ver, unused, lang, labels) -> bytes:
    body = bytearray()
    nstr = 0
    for name, strs in labels:
        body += b" LBL"
        body += struct.pack("<II", len(strs), len(name))
        body += name.encode("latin1")
        for smag, val, extra in strs:
            encoded = val.encode("utf-16le")
            xored = bytes(x ^ 0xFF for x in encoded)
            tag = smag if smag in (b" RTS", b"WRTS") else b" RTS"
            body += tag
            body += struct.pack("<I", len(val))
            body += xored
            nstr += 1
            if tag == b"WRTS" and extra is not None:
                body += struct.pack("<I", len(extra))
                body += extra
    header = bytearray()
    header += magic
    header += struct.pack("<IIIII", ver, len(labels), nstr, unused, lang)
    return bytes(header + body)


def csf_upsert(csf: bytes, mapping: dict[str, str]) -> bytes:
    magic, ver, unused, lang, labels = csf_parse(csf)
    by_name = {n: i for i, (n, _) in enumerate(labels)}
    for key, value in mapping.items():
        if key in by_name:
            i = by_name[key]
            name, strs = labels[i]
            if strs:
                smag, _old, extra = strs[0]
                strs[0] = (smag, value, extra)
            else:
                strs.append((b" RTS", value, None))
            labels[i] = (name, strs)
        else:
            labels.append((key, [(b" RTS", value, None)]))
    return csf_build(magic, ver, unused, lang, labels)


def csf_get(csf: bytes, key: str) -> str | None:
    _m, _v, _u, _l, labels = csf_parse(csf)
    for name, strs in labels:
        if name == key and strs:
            return strs[0][1]
    return None


def last_weapon_block(data: dict[str, bytes], name: str) -> tuple[str, str] | None:
    blocks: list[tuple[str, str]] = []
    wep = data[WEAPON_KEY].decode("latin1")
    b = command_block(wep, "Weapon", name)
    if b:
        blocks.append((WEAPON_KEY, b))
    weapon_dir = []
    for k in data:
        lk = k.replace("/", "\\").lower()
        if lk.startswith(r"data\ini\weapon" + "\\") and lk.endswith(".ini"):
            weapon_dir.append(k)
    for k in sorted(weapon_dir, key=lambda x: x.lower()):
        t = data[k].decode("utf-8")
        b = command_block(t, "Weapon", name)
        if b:
            blocks.append((k, b))
    return blocks[-1] if blocks else None


def validate(data: dict[str, bytes], src_data: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    all_ini = b"".join(v for k, v in data.items() if k.lower().endswith(".ini"))

    if data[R11_KEY] != src_data[R11_KEY]:
        fails.append("9P117.ini mutated")
    if data[WEAPON_KEY] != src_data[WEAPON_KEY]:
        fails.append("Weapon.ini mutated (MOTHER weapons must stay byte-identical)")
    if data[FACTORY_KEY] != src_data[FACTORY_KEY]:
        fails.append("factory object mutated")
    if data[CB_KEY] != src_data[CB_KEY]:
        fails.append("CommandButton.ini mutated")
    if data[CS_KEY] != src_data[CS_KEY]:
        fails.append("CommandSet.ini mutated")

    r11 = data[R11_KEY].decode("latin1")
    if "BuildCost       = 1200" not in r11 or "Weapon = PRIMARY   SRBM_ALHIJARAH_HE" not in r11:
        fails.append("MOTHER Iraq_R11ScudB cost/weapon changed")
    if "SelectPortrait         = irq_9p117" not in r11:
        fails.append("9P117 cameo retargeted")

    mother = command_block(data[WEAPON_KEY].decode("latin1"), "Weapon", "SRBM_ALHIJARAH_HE") or ""
    if "PrimaryDamage               = 2000.0" not in mother:
        fails.append("MOTHER SRBM_ALHIJARAH_HE damage changed")
    if "AttackRange                 = 1720.0" not in mother:
        fails.append("MOTHER range changed")
    if "ScatterRadius               = 175" not in mother:
        fails.append("MOTHER scatter changed")
    he = command_block(data[WEAPON_KEY].decode("latin1"), "Weapon", "HE_9M729_450kg") or ""
    if "PrimaryDamage           = 2200" not in he:
        fails.append("MOTHER death warhead HE_9M729_450kg changed")

    last = last_weapon_block(data, "Weapon_Iraq_AlFahd500")
    if not last:
        fails.append("Weapon_Iraq_AlFahd500 missing")
    else:
        _k, blk = last
        if "PrimaryDamage               = 8000.0" not in blk:
            fails.append(f"Al-Fahd last-wins damage not 4x MOTHER: {_k}")
        if "AttackRange                 = 1720.0" not in blk:
            fails.append("Al-Fahd range not equal to MOTHER 1720")
        if "ScatterRadius               = 175" not in blk:
            fails.append("Al-Fahd accuracy scatter changed")
        if "MinimumAttackRange          = 800.0" not in blk:
            fails.append("Al-Fahd min range changed")
        if "ProjectileObject            = Projectile_Iraq_AlFahd500" not in blk:
            fails.append("Al-Fahd projectile retargeted")
        if last[0].replace("/", "\\").lower() != WEP_OVERRIDE_KEY.lower():
            fails.append(f"Al-Fahd weapon last-wins file {last[0]}")

    war = last_weapon_block(data, "Weapon_Iraq_AlFahd500_Warhead")
    if not war or "PrimaryDamage           = 8800" not in war[1]:
        fails.append("Al-Fahd dedicated warhead not 4x HE_9M729_450kg")

    unit = data[UNIT_KEY].decode("utf-8")
    if "SelectPortrait         = specter_missile_a" not in unit:
        fails.append("queue SelectPortrait lost")
    if "ButtonImage            = specter_missile_a" not in unit:
        fails.append("queue ButtonImage lost")
    if "BuildCost       = 2200" not in unit:
        fails.append("price not 2200")
    if "BuildTime       = 30.0" not in unit:
        fails.append("production time not 30s")
    if "Weapon = PRIMARY   Weapon_Iraq_AlFahd500" not in unit:
        fails.append("Al-Fahd weapon link")
    if "IRQ_AF500.IRQ_AF500" not in unit or "UnpackTime = 6555" not in unit:
        fails.append("launch animation lost")
    if "Model                           = Irq_AlFahd500" not in unit:
        fails.append("launcher model lost")
    if re.search(r"^\s*(SelectPortrait|ButtonImage)\s*=\s*irq_9p117", unit, re.M):
        fails.append("irq_9p117 reintroduced on Al-Fahd")

    proj = data[PROJ_KEY].decode("utf-8")
    if "RadarPriority = LOCAL_UNIT_ONLY" not in proj:
        fails.append("projectile radar stealth missing")
    if "MaxHealth       = 1600.0" not in proj:
        fails.append("projectile intercept HP not 4x MOTHER")
    if "DeathWeapon   = Weapon_Iraq_AlFahd500_Warhead" not in proj:
        fails.append("projectile still shares MOTHER death weapon")
    if "HE_9M729_450kg" in proj:
        fails.append("projectile still references shared 9P117 warhead")
    if "Model = Irq_AlFahd500M" not in proj or "R11SRBMLocomotor" not in proj:
        fails.append("projectile visual/locomotor lost")
    if "KindOf = PROJECTILE BALLISTIC_MISSILE" not in proj:
        fails.append("projectile KindOf lost")

    btn = command_block(data[CB_KEY].decode("latin1"), "CommandButton", "CB_MISSILE_A") or ""
    if "Object        = Iraq_AlFahd500" not in btn or "ButtonImage   = specter_missile_a" not in btn:
        fails.append("CB_MISSILE_A mapping/artwork")
    fac = command_block(data[CS_KEY].decode("latin1"), "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet") or ""
    slots = slot_map(fac)
    if slots.get(1) != "CB_MISSILE_A" or slots.get(13) != "Command_SetRallyPoint" or slots.get(14) != "Command_Sell":
        fails.append(f"factory CommandSet slots {slots}")
    for i in range(2, 13):
        if i in slots:
            fails.append(f"B-L slot {i} wired")

    for ch in "BCDEFGHIJKL":
        n = all_ini.count(f"CommandButton CB_MISSILE_{ch}".encode("ascii"))
        if n != 1:
            fails.append(f"CB_MISSILE_{ch} count {n}")

    zzzz = [
        k
        for k, v in data.items()
        if "zzzz" in k.lower() and (b"Weapon_Iraq_AlFahd500" in v or b"Iraq_AlFahd500" in v)
    ]
    if zzzz:
        fails.append(f"ZZZZ override {zzzz[:4]}")

    name = csf_get(data[CSF_KEY], "OBJECT:Iraq_AlFahd500")
    if name != "Al-Fahd500":
        fails.append(f"DisplayName {name!r}")
    tip = csf_get(data[CSF_KEY], "CONTROLBAR:ToolTipSpecterMissileA")
    if tip != TOOLTIP:
        fails.append("tooltip not Persian Al-Fahd500 stat block")
    if "Damage" in (tip or "") or "آسیب" in (tip or ""):
        fails.append("tooltip still has a separate Damage stat")

    changed = sorted(k for k in set(data) | set(src_data) if data.get(k) != src_data.get(k))
    allowed = {UNIT_KEY, PROJ_KEY, CSF_KEY, WEP_OVERRIDE_KEY}
    unexpected = [k for k in changed if k not in allowed]
    if unexpected:
        fails.append(f"unexpected DATA changes {unexpected[:8]}")
    if WEP_OVERRIDE_KEY not in data:
        fails.append("missing Weapon last-wins file")
    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("live DATA baseline mismatch")

    src_data = parse_big(SRC_DATA.read_bytes())
    data = dict(src_data)
    data[UNIT_KEY] = to_crlf(UNIT_SRC.read_text(encoding="utf-8"))
    data[PROJ_KEY] = to_crlf(PROJ_SRC.read_text(encoding="utf-8"))
    data[WEP_OVERRIDE_KEY] = to_crlf(WEP_SRC.read_text(encoding="utf-8"))
    data[CSF_KEY] = csf_upsert(data[CSF_KEY], CSF_LABELS)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    packed = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed)
    extracted = parse_big(packed)

    stage = OUT / "LAST_WINS_EXTRACT"
    (stage / "DATA").mkdir(parents=True)
    for rel in [UNIT_KEY, PROJ_KEY, WEP_OVERRIDE_KEY, R11_KEY]:
        p = stage / "DATA" / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])
    mother = command_block(extracted[WEAPON_KEY].decode("latin1"), "Weapon", "SRBM_ALHIJARAH_HE") or ""
    last = last_weapon_block(extracted, "Weapon_Iraq_AlFahd500")
    war = last_weapon_block(extracted, "Weapon_Iraq_AlFahd500_Warhead")
    (stage / "WEAPONS.txt").write_text(
        "=== MOTHER SRBM_ALHIJARAH_HE (Weapon.ini, unchanged) ===\n"
        + mother
        + "\n\n=== LAST-WINS Weapon_Iraq_AlFahd500 ===\n"
        + (last[1] if last else "MISSING")
        + "\n\n=== LAST-WINS Weapon_Iraq_AlFahd500_Warhead ===\n"
        + (war[1] if war else "MISSING")
        + "\n",
        encoding="utf-8",
    )

    fails = validate(extracted, src_data)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    data_sha = sha256_path(out_data)
    report = [
        "# SPECTER Al-Fahd500 final stats (Missile A)",
        "",
        "MOTHER = Iraq_R11ScudB / SRBM_ALHIJARAH_HE — NOT MODIFIED",
        "Al-Fahd500 warhead 4x, range/accuracy equal, stealth 20 vs 5, $2200 / 30s",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        "- ART changed: NO (keep previous _SPEC_ART_ONE.big)",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        report.append("RUNTIME_TEST=NOT RUN")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static)",
        "- CB_MISSILE_A -> Iraq_AlFahd500, ButtonImage specter_missile_a",
        "- Queue/countdown Object ButtonImage+SelectPortrait = specter_missile_a",
        "- Range AttackRange 1720 = MOTHER (1000 km scale)",
        "- Damage 8000 + warhead 8800 = 4x MOTHER 2000+2200",
        "- ScatterRadius 175 = MOTHER accuracy 10/100",
        "- Projectile RadarPriority LOCAL_UNIT_ONLY, MaxHealth 1600 (4x 400)",
        "- BuildCost 2200, BuildTime 30.0",
        "- 9P117 / Weapon.ini / factory CommandSet / CB_MISSILE_B-L unchanged",
        "",
        "RUNTIME_TEST=NOT RUN",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=NO\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted)}\n"
        "ART_FILE=unchanged previous _SPEC_ART_ONE.big\n"
        "ART_SHA256=5fdc19145769b81bce2cddaeeb91701d6c9ce0f4e288e0d55baa03cbfdb33ea9\n"
        "QUEUE_ICON=specter_missile_a\n"
        "MAPPING=موشک A -> Iraq_AlFahd500\n"
        "PRICE=2200\n"
        "BUILDTIME=30\n"
        "DAMAGE_SCALE=4x MOTHER\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER Al-Fahd500 final stats (Missile A)\n"
        "Place this complete replacement DATA BIG in the game folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "Keep the previous complete ART BIG (_SPEC_ART_ONE.big); ART did not change.\n"
        "9P117 / MOTHER is unmodified.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD500_STATS.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
