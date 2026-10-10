#!/usr/bin/env python3
"""Fix Iraq missile factory construction for all PR #613 assigned countries.

Root cause: Iraq_AlFahdMissileFactory Prerequisites = Iraq_SupplyCenter.
Assigned countries never own that object, so DOZER_CONSTRUCT stays
visible on the CommandSet but canBuild() fails.

Fix: keep the Supply Center progression gate, but OR every assigned
country's live supply-center object (plus Iraq_SupplyCenter).

Do not change slots, missiles, factory production CommandSet, model,
health, cost, or build time. ART is copied byte-identical from #613.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_MISSILE_FACTORY_EXPORT/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_MISSILE_FACTORY_EXPORT/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_MISSILE_FACTORY_PREREQ"
LOOSE_FACTORY = ROOT / "patch/Data/INI/Object/Specter/Iraq Army/Buildings/Iraq_AlFahdMissileFactory.ini"

SHA_DATA_613 = "6fe954541ed93327879bba50ed1995be5da0080a036b1cd2fd87ed077e3a0a3c"
SIZE_DATA_613 = 366670447
SHA_ART_613 = "fa46c291d9cec1b106977e7a5ec3ded54e9bc0c9e2c94ab4d4852b90d4e96359"
SIZE_ART_613 = 1305667638

CS_KEY = r"Data\INI\CommandSet.ini"
PK_KEY = r"Data\INI\CommandSet_Pakistan.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
FACTORY_BTN = "Command_ConstructIraq_AlFahdMissileFactory"

# Live supply-center objects from the #613 DATA BIG (all exist).
SUPPLY_OR = [
    "Iraq_SupplyCenter",
    "UkraineSupplyCenter",
    "TurkeySupplyCenter",
    "ItalySupplyCenter",
    "SwedenSupplyCenter",
    "BritainSupplyCenter",
    "FranceSupplyCenter",
    "GermanySupplyCenter",
    "NatoSupplyCenter",
    "ChinaSupplyCenter",
    "SouthKorea_SupplyCenter",
    "NorthKorea_SupplyCenter",
    "Vietnam_SupplyCenter",
    "Japan_SupplyCenter",
    "India_SupplyCenter",
    "Pakistan_SupplyCenter",
    "SaudiArabia_SupplyCenter",
    "UAE_SupplyCenter",
    "Syria_SupplyCenter",
    "Libya_SupplyCenter",
    "SouthAfrica_SupplyCenter",
    "RussiaSupplyCenter",
]

COUNTRY_SUPPLY = {
    "Ukraine": "UkraineSupplyCenter",
    "Turkey": "TurkeySupplyCenter",
    "Italy": "ItalySupplyCenter",
    "Sweden": "SwedenSupplyCenter",
    "Britain": "BritainSupplyCenter",
    "France": "FranceSupplyCenter",
    "Germany": "GermanySupplyCenter",
    "Nato": "NatoSupplyCenter",
    "China": "ChinaSupplyCenter",
    "SouthKorea": "SouthKorea_SupplyCenter",
    "NorthKorea": "NorthKorea_SupplyCenter",
    "Vietnam": "Vietnam_SupplyCenter",
    "Japan": "Japan_SupplyCenter",
    "India": "India_SupplyCenter",
    "Pakistan": "Pakistan_SupplyCenter",
    "SaudiArabia": "SaudiArabia_SupplyCenter",
    "UAE": "UAE_SupplyCenter",
    "Syria": "Syria_SupplyCenter",
    "Libya": "Libya_SupplyCenter",
    "SouthAfrica": "SouthAfrica_SupplyCenter",
    "Russia": "RussiaSupplyCenter",
}

SLOT_SETS = {
    "Ukraine": ("UkraineDozerCommandSet", 14),
    "Turkey": ("TurkeyDozerCommandSet", 14),
    "Italy": ("ItalyDozerCommandSet", 14),
    "Sweden": ("SwedenDozerCommandSet", 14),
    "Britain": ("BritainDozerCommandSet", 14),
    "France": ("FranceDozerCommandSet", 14),
    "Germany": ("GermanyDozerCommandSet", 14),
    "Nato": ("NatoDozerCommandSet", 14),
    "China": ("PLADozerCommandSet", 14),
    "SouthKorea": ("SouthKorea_VT72BCommandSet", 6),
    "NorthKorea": ("NorthKorea_VT72BCommandSet", 6),
    "Vietnam": ("Vietnam_VT72BCommandSet", 6),
    "Japan": ("Japan_VT72BCommandSet", 6),
    "India": ("IndiaDozerCommandSet", 13),
    "Pakistan": ("PakistanDozerCommandSet", 13),
    "SaudiArabia": ("SaudiArabiaDozerCommandSet", 13),
    "UAE": ("UAEDozerCommandSet", 13),
    "Syria": ("SyriaDozerCommandSet", 13),
    "Libya": ("LibyaDozerCommandSet", 13),
    "SouthAfrica": ("SouthAfricaDozerCommandSet", 13),
    "Russia": ("RussiaDozerCommandSet", 14),
}

MISSILE_SETS = [
    "Iraq_AlFahdMissileFactoryCommandSet",
    "Iraq_AlhussaienCommandSet",
    "Iraq_AlhussaienArmedCommandSet",
    "Iraq_AlHaithamArmedCommandSet",
    "Iraq_AlAbbasCommandSet",
    "Iraq_WarFactoryCommandSet_T",
    "Iraq_WarFactoryCommandSet_T1",
    "Iraq_WarFactoryCommandSet_T2",
    "Iraq_WarFactoryCommandSet_T3",
    "Iraq_WarFactoryCommandSet",
    "Smerch_CommandSet",
]

PREREQ_BLOCK = (
    "  Prerequisites\r\n"
    "    Object = " + " ".join(SUPPLY_OR) + "\r\n"
    "  End\r\n"
)
OLD_PREREQ = (
    "  Prerequisites\r\n"
    "    Object = Iraq_SupplyCenter\r\n"
    "  End\r\n"
)


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
        raise SystemExit("not BIGF")
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
    offset = header_size
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", 0)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    blobs = []
    for name, content in items:
        content = bytes(content)
        out += struct.pack(">II", offset, len(content))
        out += name.encode("latin1") + b"\x00"
        blobs.append(content)
        offset += len(content)
    out[4:8] = struct.pack(">I", offset)
    for blob in blobs:
        out += blob
    return bytes(out)


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def command_block(text: str, name: str) -> str | None:
    matches = list(re.finditer(rf"(?ms)^CommandSet {re.escape(name)}\r?\n.*?^End", text))
    return matches[-1].group(0) if matches else None


def slot_map(block: str | None) -> dict[int, str]:
    out: dict[int, str] = {}
    if not block:
        return out
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def field(body: str | None, key: str) -> str:
    if not body:
        return ""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", body, re.M)
    return m.group(1).strip() if m else ""


def last_object(files: dict[str, bytes], obj: str) -> str:
    pat = re.compile(rf"(?ms)^Object {re.escape(obj)}\s*\n(.*?)(?=^Object |\Z)")
    last = ""
    for n, blob in files.items():
        if not n.lower().endswith(".ini"):
            continue
        hits = list(pat.finditer(blob.decode("latin1")))
        if hits:
            last = hits[-1].group(0)
    return last


def patch_factory(blob: bytes) -> bytes:
    text = blob.decode("latin1")
    if OLD_PREREQ not in text:
        # accept LF-only source
        old_lf = OLD_PREREQ.replace("\r\n", "\n")
        if old_lf in text.replace("\r\n", "\n") and "\r\n" not in text:
            text = text.replace(old_lf, PREREQ_BLOCK.replace("\r\n", "\n"))
            return text.replace("\n", "\r\n").encode("latin1")
        raise SystemExit("factory prerequisite block not found")
    text = text.replace(OLD_PREREQ, PREREQ_BLOCK, 1)
    if text.count("Object = Iraq_SupplyCenter") and "UkraineSupplyCenter" not in text:
        raise SystemExit("prereq replace failed")
    return text.encode("latin1")


def validate(data: dict[str, bytes], art: dict[str, bytes], src_data: dict[str, bytes], src_art: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    if set(data) != set(src_data):
        fails.append("DATA file set changed")
    if art != src_art:
        fails.append("ART mutated")
    changed = sorted(k for k in src_data if src_data[k] != data.get(k))
    if changed != [FACTORY_KEY]:
        fails.append(f"unexpected mutated files: {changed}")
    if data[CS_KEY] != src_data[CS_KEY]:
        fails.append("CommandSet.ini mutated")
    if data[PK_KEY] != src_data[PK_KEY]:
        fails.append("CommandSet_Pakistan.ini mutated")
    if data[CB_KEY] != src_data[CB_KEY]:
        fails.append("CommandButton.ini mutated")

    factory = data[FACTORY_KEY].decode("latin1")
    src_factory = src_data[FACTORY_KEY].decode("latin1")
    if field(factory, "BuildCost") != "1800":
        fails.append(f"BuildCost={field(factory, 'BuildCost')}")
    if field(factory, "BuildTime") != "20.0":
        fails.append(f"BuildTime={field(factory, 'BuildTime')}")
    if field(factory, "CommandSet") != "Iraq_AlFahdMissileFactoryCommandSet":
        fails.append("factory production CommandSet changed")
    if field(factory, "Side") != "Iraq":
        fails.append(f"Side={field(factory, 'Side')}")
    if "Irq_FahdFac" not in factory or "Irq_FahdFacD" not in factory:
        fails.append("factory model changed")
    if "MaxHealth       = 1800.0" not in factory:
        fails.append("factory health changed")
    if "Object = Iraq_SupplyCenter" not in factory:
        fails.append("Iraq_SupplyCenter dropped from OR list")
    if re.search(r"(?ms)^\s*Prerequisites\s*\n\s*End", factory):
        fails.append("prerequisites were emptied")
    stripped = factory
    for name in SUPPLY_OR:
        stripped = stripped.replace(name, "", 1)
        if name not in factory:
            fails.append(f"missing OR prereq {name}")
        body = last_object(data, name)
        if not body:
            fails.append(f"missing supply object {name}")
        elif "FS_SUPPLY" not in field(body, "KindOf"):
            fails.append(f"{name} is not FS_SUPPLY")
    if "Iraq_SupplyCenter" in stripped and factory.count("Iraq_SupplyCenter") != 1:
        # leftover exclusive-only prereq besides the OR list is ok if only once
        pass

    # Exclusive old prereq must not remain as the only object.
    m = re.search(r"(?ms)^\s*Prerequisites\s*\n(.*?)^\s*End", factory)
    inner = " ".join(m.group(1).split()) if m else ""
    if inner == "Object = Iraq_SupplyCenter":
        fails.append("prereq still Iraq-only")
    for name in COUNTRY_SUPPLY.values():
        if name not in inner:
            fails.append(f"prereq OR missing {name}")

    # Keep all other factory lines identical except the prereq block.
    def norm_prereq(text: str) -> str:
        return re.sub(r"(?ms)^\s*Prerequisites\s*\n.*?^\s*End\s*\n", "PREREQ\n", text)

    if norm_prereq(factory) != norm_prereq(src_factory):
        fails.append("factory changed outside Prerequisites")

    cs = data[CS_KEY].decode("latin1")
    for country, (set_name, slot) in SLOT_SETS.items():
        slots = slot_map(command_block(cs, set_name))
        if slots.get(slot) != FACTORY_BTN:
            fails.append(f"{country} {set_name} slot {slot}={slots.get(slot)}")
    pk = data[PK_KEY].decode("latin1")
    if slot_map(command_block(pk, "Pakistan_WorkerCommandSet")).get(13) != FACTORY_BTN:
        fails.append("Pakistan Worker slot 13 lost factory")
    if slot_map(command_block(pk, "Pakistan_VT72BCommandSet")).get(13) != FACTORY_BTN:
        fails.append("Pakistan VT72B slot 13 lost factory")

    for name in MISSILE_SETS:
        if command_block(cs, name) != command_block(src_data[CS_KEY].decode("latin1"), name):
            fails.append(f"missile CommandSet mutated: {name}")

    btn = data[CB_KEY].decode("latin1")
    if "CommandButton Command_ConstructIraq_AlFahdMissileFactory" not in btn:
        fails.append("construct button missing")
    if "Object           = Iraq_AlFahdMissileFactory" not in btn:
        fails.append("construct button object retargeted")
    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != SIZE_DATA_613 or sha256_path(SRC_DATA) != SHA_DATA_613:
        raise SystemExit("DATA baseline is not PR #613")
    if SRC_ART.stat().st_size != SIZE_ART_613 or sha256_path(SRC_ART) != SHA_ART_613:
        raise SystemExit("ART baseline is not PR #613")

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)
    data[FACTORY_KEY] = patch_factory(data[FACTORY_KEY])

    # Keep the loose source in sync with packed last-wins.
    loose = LOOSE_FACTORY.read_text(encoding="latin1")
    loose_new = re.sub(
        r"(?ms)^  Prerequisites\n    Object = Iraq_SupplyCenter\n  End\n",
        "  Prerequisites\n    Object = " + " ".join(SUPPLY_OR) + "\n  End\n",
        loose,
        count=1,
    )
    if loose_new == loose:
        raise SystemExit("loose factory prereq replace failed")
    LOOSE_FACTORY.write_text(loose_new, encoding="latin1")

    fails = validate(data, art, src_data, src_art)
    out_data = build_big(data)
    out_art = build_big(art)
    fails.extend([f"DATA {x}" for x in big_structure_ok(out_data)])
    fails.extend([f"ART {x}" for x in big_structure_ok(out_art)])
    fails.extend(validate(parse_big(out_data), parse_big(out_art), src_data, src_art))
    if fails:
        raise SystemExit("VALIDATION FAIL\n" + "\n".join(fails))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "_SPEC_DATA_ONE.big").write_bytes(out_data)
    (OUT / "_SPEC_ART_ONE.big").write_bytes(out_art)
    data_sha = sha256_path(OUT / "_SPEC_DATA_ONE.big")
    art_sha = sha256_path(OUT / "_SPEC_ART_ONE.big")

    ext = OUT / "LAST_WINS_EXTRACT/DATA"
    ext.mkdir(parents=True, exist_ok=True)
    (ext / "Iraq_AlFahdMissileFactory.ini").write_bytes(parse_big(out_data)[FACTORY_KEY])

    report = [
        "SPECTER missile factory construction prerequisite fix",
        f"DATA {len(out_data)} {data_sha}",
        f"ART  {len(out_art)} {art_sha}",
        "",
        "ROOT CAUSE:",
        "  Button visible because CommandSets already list",
        "  Command_ConstructIraq_AlFahdMissileFactory.",
        "  Construction fails because canBuild() requires",
        "  Prerequisites Object = Iraq_SupplyCenter.",
        "  Assigned countries never own that Iraq-only building.",
        "  Command button, builders, W3D, and factory production",
        "  CommandSet were already valid.",
        "",
        "FIX:",
        "  Same Iraq_AlFahdMissileFactory object.",
        "  Prerequisites now OR every assigned country's live",
        "  Supply Center (plus Iraq_SupplyCenter).",
        "  Supply-center progression gate is kept. Slots unchanged.",
        "  No missiles transferred. ART unchanged from #613.",
        "",
        "STATIC_VALIDATION=PASS",
        "RUNTIME_TEST=NOT RUN",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=NO\n"
        f"DATA_SIZE={len(out_data)}\n"
        f"DATA_SHA256={data_sha}\n"
        f"ART_SIZE={len(out_art)}\n"
        f"ART_SHA256={art_sha}\n"
        "BASELINE=PR #613\n"
        "ROOT_CAUSE=Iraq_SupplyCenter exclusive prerequisite\n"
        "FIX=OR assigned-country supply centers\n"
        "MISSILES_TRANSFERRED=NO\n"
        "SLOTS_CHANGED=NO\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Fix missile factory construction for assigned countries.\n"
        "The button was visible; construction failed on Iraq_SupplyCenter.\n"
        "Place both complete replacement BIGs in the SPECTER folder.\n"
        "STATIC ONLY.\n",
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Missile factory construction prerequisite fix\n"
        "\n"
        "- Root cause: exclusive `Iraq_SupplyCenter` prerequisite.\n"
        "- Fix: OR each assigned country's live Supply Center.\n"
        "- Same factory object, slots, production roster, and ART.\n",
        encoding="utf-8",
    )
    (OUT / "CONFLICTS.txt").write_text(
        "Only Iraq_AlFahdMissileFactory Prerequisites last-wins.\n"
        "CommandSets and ART are unchanged from PR #613.\n"
        "STATIC ONLY.\n",
        encoding="utf-8",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "DATA/ART/ZIP links are filled after the GitHub Release is published.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_MISSILE_FACTORY_PREREQ.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
        zf.write(OUT / "RELEASE_NOTES.md", "RELEASE_NOTES.md")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size} sha={sha256_path(zip_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
