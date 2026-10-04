#!/usr/bin/env python3
"""Surgical barracks flag de-dup: hide irq_camp FLAG01-03 on 8 dual-Draw barracks.

Source of truth: live NATO_RADAR_USA_REFERENCE_FIX _SPEC_DATA_ONE.big.
Replaces only the eight packed barracks INIs that already have a country
Flag_Hs ModuleTag_03. Adds HideSubObject FLAG01 FLAG02 FLAG03 to every
irq_camp ConditionState so the baked Iraq cloth is hidden and the newer
national pole remains.

India_Barracks and Pakistan_Barracks are not patched: live last-win has
no Flag_Hs Draw, so hiding FLAG01-03 would remove their only 3D flag.
Iraq_Barracks and all non-barracks buildings are frozen.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/flag_audit/_SPEC_DATA_ONE.big")
EXPECTED_SRC_SHA = "11fcfb872b8fd6e8ba8389fcf5cb9b06357ef1392c6af98c364e18f810e79858"
EXPECTED_SRC_SIZE = 366169284
ROOT = Path("/workspace/patch")
PAYLOAD = ROOT / "Release" / "BARRACKS_FLAG_DEDUP" / "payload"
RELEASE = ROOT / "Release" / "BARRACKS_FLAG_DEDUP"

REPLACE = [
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_Barracks.ini",
    r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_Barracks.ini",
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_Barracks.ini",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_Barracks.ini",
    r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_Barracks.ini",
]

UNCHANGED_TARGETS = [
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_Barracks.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_Barracks.ini",
]

FROZEN = [
    r"Data\INI\Weapon.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\Upgrade.ini",
    r"Data\INI\SpecialPower.ini",
    r"Data\INI\Object\CivilianBuilding.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_Barracks.ini",
    r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_Barracks.ini",
    r"Data\INI\Object\Specter\United States Of America\Buildings\Camp.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_SoldierCommand.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_BarracksAndRifles.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_Class2.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_SAUAESYINPK.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\French Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\GM406.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\GM406.ini",
] + UNCHANGED_TARGETS

FLAG_HS = {
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_Barracks.ini": "JP__JPFlag_Hs",
    r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\Iraq_Barracks.ini": "SK__SKFlag_Hs",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_Barracks.ini": "VN__VNFlag_Hs",
    r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_Barracks.ini": "LY__LYFlag_Hs",
    r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_Barracks.ini": "SY__SYFlag_Hs",
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_Barracks.ini": "AE__AEFlag_Hs",
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_Barracks.ini": "SA__SAFlag_Hs",
    r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_Barracks.ini": "ZA__ZAFlag_Hs",
}

HIDE_LINE = "      HideSubObject = FLAG01 FLAG02 FLAG03"
DRAW01_RE = re.compile(r"(?i)^\s*Draw\s*=\s*W3DModelDraw\s+ModuleTag_01\s*$")
DRAW_RE = re.compile(r"(?i)^\s*Draw\s*=")
ANIM_LOOP_RE = re.compile(r"(?i)^\s*AnimationMode\s*=\s*LOOP\s*$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def norm(name: str) -> str:
    return name.replace("/", "\\")


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    return read_big_from_bytes(data)


def read_big_from_bytes(data: bytes):
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries):
    header_size = 16
    encoded = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries, target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 path, got {len(hits)}")
    return hits[0]


def hide_irq_camp_flags(text: str) -> str:
    if "HideSubObject = FLAG01 FLAG02 FLAG03" in text:
        raise SystemExit("payload already contains HideSubObject FLAG01-03")
    lines = text.splitlines(keepends=True)
    out = []
    in_mod01 = False
    inserted = 0
    for line in lines:
        raw = line[:-1] if line.endswith("\n") else line
        if raw.endswith("\r"):
            raw = raw[:-1]
        if DRAW01_RE.match(raw):
            in_mod01 = True
        elif DRAW_RE.match(raw):
            in_mod01 = False
        out.append(line)
        if in_mod01 and ANIM_LOOP_RE.match(raw):
            nl = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
            out.append(HIDE_LINE + nl)
            inserted += 1
    if inserted != 6:
        raise SystemExit(f"expected 6 HideSubObject inserts in ModuleTag_01, got {inserted}")
    return "".join(out)


def validate_payload(packed: str, blob: bytes) -> None:
    text = blob.decode("latin1", errors="replace")
    flag = FLAG_HS[packed]
    if text.count("HideSubObject = FLAG01 FLAG02 FLAG03") != 6:
        raise SystemExit(f"{packed}: expected 6 HideSubObject lines")
    if "Draw = W3DModelDraw ModuleTag_01" not in text and "Draw = W3DModelDraw ModuleTag_01" not in text.replace("\r\n", "\n"):
        raise SystemExit(f"{packed}: missing ModuleTag_01")
    if f"Model           = {flag}" not in text and f"Model = {flag}" not in text:
        if flag not in text:
            raise SystemExit(f"{packed}: missing preserved Flag_Hs {flag}")
    if "ModuleTag_03" not in text:
        raise SystemExit(f"{packed}: missing Flag_Hs ModuleTag_03")
    # Hide must not appear inside the Flag_Hs draw
    flag_draw = text.split("Draw                = W3DModelDraw ModuleTag_03", 1)
    if len(flag_draw) != 2:
        raise SystemExit(f"{packed}: cannot isolate ModuleTag_03")
    if "HideSubObject" in flag_draw[1]:
        raise SystemExit(f"{packed}: HideSubObject leaked into Flag_Hs draw")


def payload_path(packed: str) -> Path:
    return PAYLOAD / packed.replace("\\", "/")


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing source BIG {SRC_DATA}")
    if sha256_file(SRC_DATA) != EXPECTED_SRC_SHA:
        raise SystemExit("NATO radar DATA SHA mismatch")
    if SRC_DATA.stat().st_size != EXPECTED_SRC_SIZE:
        raise SystemExit("NATO radar DATA size mismatch")

    entries = read_big(SRC_DATA)
    orig = list(entries)
    orig_map = {norm(n).lower(): (n, b) for n, b in orig}

    PAYLOAD.mkdir(parents=True, exist_ok=True)
    replaced = []
    for packed in REPLACE:
        idx = find_index(entries, packed)
        old_name, old_blob = entries[idx]
        old_text = old_blob.decode("latin1", errors="replace")
        if FLAG_HS[packed] not in old_text:
            raise SystemExit(f"baseline missing Flag_Hs {FLAG_HS[packed]}: {packed}")
        if "HideSubObject" in old_text:
            raise SystemExit(f"baseline already has HideSubObject: {packed}")
        new_text = hide_irq_camp_flags(old_text)
        # preserve original newline style of the file
        if old_blob.endswith(b"\r\n") or b"\r\n" in old_blob:
            new_blob = new_text.encode("latin1")
        else:
            new_blob = new_text.encode("latin1")
        validate_payload(packed, new_blob)
        dest = payload_path(packed)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(new_blob)
        entries[idx] = (old_name, new_blob)
        replaced.append(packed)
        print(f"PATCHED {packed} {len(old_blob)} -> {len(new_blob)}")

    for p in FROZEN:
        idx = find_index(entries, p)
        if entries[idx][1] != orig_map[norm(p).lower()][1]:
            raise SystemExit(f"frozen path changed: {p}")

    orig_names = [n for n, _ in orig]
    new_names = [n for n, _ in entries]
    if new_names != orig_names:
        raise SystemExit("packed path set/order changed")

    replace_set = {norm(p).lower() for p in REPLACE}
    for n, b in entries:
        if norm(n).lower() in replace_set:
            continue
        if b != orig_map[norm(n).lower()][1]:
            raise SystemExit(f"unintended rewrite: {n}")

    data_blob = build_big_ordered(entries)
    rebuilt = read_big_from_bytes(data_blob)
    if [n for n, _ in rebuilt] != new_names:
        raise SystemExit("rebuild order drifted")

    # Post-pack object-level checks
    last = {}
    obj_re = re.compile(r"(?im)^Object\s+(\S+)")
    for name, blob in rebuilt:
        if not name.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        matches = list(obj_re.finditer(text))
        for i, m in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            last[m.group(1)] = text[m.start() : end]

    checks = {
        "Japan_Barracks": ("JP__JPFlag_Hs", True),
        "SouthKorea_Barracks": ("SK__SKFlag_Hs", True),
        "Vietnam_Barracks": ("VN__VNFlag_Hs", True),
        "Libya_Barracks": ("LY__LYFlag_Hs", True),
        "Syria_Barracks": ("SY__SYFlag_Hs", True),
        "UAE_Barracks": ("AE__AEFlag_Hs", True),
        "SaudiArabia_Barracks": ("SA__SAFlag_Hs", True),
        "SouthAfrica_Barracks": ("ZA__ZAFlag_Hs", True),
        "India_Barracks": (None, False),
        "Pakistan_Barracks": (None, False),
        "Iraq_Barracks": (None, False),
        "Egypt_Barracks": (None, False),
        "Israel_Barracks": (None, False),
    }
    for obj, (flag, expect_hide) in checks.items():
        body = last.get(obj)
        if not body:
            raise SystemExit(f"missing last-win object {obj}")
        hides = body.count("HideSubObject = FLAG01 FLAG02 FLAG03")
        if expect_hide:
            if hides != 6:
                raise SystemExit(f"{obj}: expected 6 hides, got {hides}")
            if flag not in body:
                raise SystemExit(f"{obj}: lost Flag_Hs {flag}")
            if "ModuleTag_03" not in body:
                raise SystemExit(f"{obj}: lost ModuleTag_03")
        else:
            if hides != 0:
                raise SystemExit(f"{obj}: unexpected HideSubObject")
            if "Flag_Hs" in body:
                raise SystemExit(f"{obj}: unexpected Flag_Hs")

    RELEASE.mkdir(parents=True, exist_ok=True)
    out = RELEASE / "_SPEC_DATA_ONE.big"
    out.write_bytes(data_blob)
    sha = sha256_file(out)
    validation = [
        "STATIC_VALIDATION = PASS",
        "INGAME_TESTED = NO",
        f"SOURCE_DATA_SHA {EXPECTED_SRC_SHA}",
        f"PACKED_DATA_SHA {sha}",
        f"FILE_COUNT {len(entries)}",
        f"BYTES {out.stat().st_size}",
        "REPLACED_BARRACKS = Japan SouthKorea Vietnam Libya Syria UAE SaudiArabia SouthAfrica",
        "UNCHANGED_BARRACKS = India Pakistan Iraq Egypt Israel USA",
        "FLAG_HS_PRESERVED = YES",
        "IRQ_CAMP_MESH_UNCHANGED = YES",
        "ART_CHANGED = NO",
        "OIL_CAPTURE_UNCHANGED = YES",
        "FIGHTER_ROSTER_UNCHANGED = YES",
        "NATO_RADAR_UNCHANGED = YES",
        "OTHER_BUILDINGS_UNCHANGED = YES",
    ]
    (RELEASE / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {sha}\n"
        f"SOURCE_DATA_SHA {EXPECTED_SRC_SHA}\n"
        f"ART unchanged (not packed)\n"
        f"FILE_COUNT {len(entries)}\n"
        f"BYTES {out.stat().st_size}\n",
        encoding="utf-8",
    )
    (RELEASE / "PACKED_FILES.txt").write_text(
        "REPLACED\n"
        + "\n".join(f"  {p}" for p in replaced)
        + "\nAPPENDED\n  NONE\n"
        + "ART_CHANGED = NO\n"
        + "INDIA_PAKISTAN_CHANGED = NO\n"
        + "IRAQ_BARRACKS_CHANGED = NO\n",
        encoding="utf-8",
    )
    (RELEASE / "POST_PACK_VALIDATION.txt").write_text("\n".join(validation) + "\n", encoding="utf-8")
    print("PACKED", out, out.stat().st_size, sha, "files", len(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
