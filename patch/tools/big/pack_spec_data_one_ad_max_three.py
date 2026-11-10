#!/usr/bin/env python3
"""Cap every buildable SPECTER Air Defence type at 3 per player.

Engine field (already used in this project): MaxSimultaneousOfType.
That count is per-player, includes live + under-construction objects, and
drops on sell/destroy. MaxSimultaneousLinkKey = Patch_AirDefense currently
pools many AD types into one shared 10. That key is removed so the cap is
3 of each type, not 3 AD total.

Source: df41-factory-ballistic _SPEC_DATA_ONE.big
(SHA 5b7ee5c6b8a57506c9cc82083e8366bfcdb50f1c585fba2d842504bfaa2d2312).

Does not change weapons, range, cost, upgrades, or intercept behavior.
CommandSet.ini / CommandButton.ini are copied unchanged (#714 overlay).
"""
from __future__ import annotations

import hashlib
import re
import struct
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/DF41_FACTORY_BALLISTIC/_SPEC_DATA_ONE.big"
SRC_SHA = "5b7ee5c6b8a57506c9cc82083e8366bfcdb50f1c585fba2d842504bfaa2d2312"
OUT_DIR = ROOT / "Release/AD_MAX_THREE"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_WPN = r"Data\INI\Weapon.ini"

EXCLUDE_NAME = re.compile(
    r"(Jet|Bomber|UAV|Hawk1|Hawk2|F16|Vulcan|GlobalHawk|Tomahawk|Nasr$|Pakistan_Raad|"
    r"RSA3|BattleMaster|Krasukha|M777|D30|Howitzer|100mmCannon|Falaq|2A65|"
    r"TunnelNetwork|FireBase|Bunker|SpeakerTower|WarFactory|MissileFactory|"
    r"GlobalStore|ScudStorm|StormShadow|HelixGattling|OverlordGattling|SpectreGunship|"
    r"Damaged|FireControl|LockControl|_Missile\d|_CombatMode|_PackMode|Pongae6)",
    re.I,
)
NAMED = re.compile(
    r"(S400|S500|S300|HQ9|Hq9|Pantsir|Avenger|Patriot|THAAD|Arrow|"
    r"IronDome|Barak8|HISAR|SIPER|Korkut|Sungur|Roland|Igla|Stinger|SAM8|SA-6|"
    r"9K317|Fahad3|B340|Majid|RaadBaran|RaadM2|RaadSPG|Bavar|Meraj|Cortale|"
    r"Crotale|IRIST|PGZ04|QuadCannon|M1126_M1_Shorad|MIM104|AD_SAM|AD_MD|"
    r"AD_SHORAD|AD_Anti|Sam2|ZSU|Sam8|SamSite|Mantis|CRAM|Gattling|Stormer|"
    r"TPY2|92N6|96L6|55K6|30N6|HT233|TRML|9S19|SAMPT|NASAMS|TorM2|Tor1M|_Tor)",
    re.I,
)
SITE = re.compile(
    r"(Patriot|StingerSite|SamSite|Sam2|IRISTSam|Hq9_Site|CRAM|Mantis|"
    r"Fahad3Sam|DefenseSite|GattlingCannon|MIM104|BavarSite|S400Site|"
    r"S400_Site|SAMPT|NASAMS|S300PMU)",
    re.I,
)


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
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
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def object_files(entries: dict[str, bytes]) -> list[tuple[str, str]]:
    return sorted(
        (
            (k, v.decode("latin1"))
            for k, v in entries.items()
            if k.lower().startswith(r"data\ini\object") and k.lower().endswith(".ini")
        ),
        key=lambda kv: kv[0].lower(),
    )


def iter_objects(text: str):
    for m in re.finditer(r"^Object (\S+)\s*\r?\n", text, re.M):
        n2 = re.search(r"^Object ", text[m.end() :], re.M)
        end = m.end() + n2.start() if n2 else len(text)
        yield m.group(1), m.start(), end, text[m.start() : end]


def field(block: str, name: str) -> str | None:
    m = re.search(rf"^[ \t]*{name}[ \t]*=[ \t]*(\S+)", block, re.M)
    return m.group(1) if m else None


def kindof(block: str) -> str:
    m = re.search(r"^[ \t]*KindOf[ \t]*=[ \t]*(.+)$", block, re.M)
    return (m.group(1) if m else "").strip()


def ad_path(path: str) -> bool:
    p = path.lower()
    return "airdefense" in p or "airdefence" in p


def buildable_maps(entries: dict[str, bytes]) -> tuple[set[str], set[str], set[str]]:
    cb = entries[K_CB].decode("latin1")
    unit_btn: dict[str, str] = {}
    dozer_btn: dict[str, str] = {}
    for m in re.finditer(
        r"^CommandButton (\S+)\s*\r?\n(.*?)(?=^CommandButton |\Z)", cb, re.M | re.S
    ):
        cm = re.search(r"Command\s*=\s*(\S+)", m.group(2))
        om = re.search(r"Object\s*=\s*(\S+)", m.group(2))
        if not cm or not om:
            continue
        if cm.group(1) == "UNIT_BUILD":
            unit_btn[m.group(1)] = om.group(1)
        elif cm.group(1) == "DOZER_CONSTRUCT":
            dozer_btn[m.group(1)] = om.group(1)
    has_btn = set(unit_btn.values())
    dozer_objs = set(dozer_btn.values())
    cs = entries[K_CS].decode("latin1")
    reachable: set[str] = set()
    for m in re.finditer(
        r"^CommandSet (\S+)\s*\r?\n(.*?)(?=^CommandSet |\Z)", cs, re.M | re.S
    ):
        for b in re.findall(r"^\s*\d+\s*=\s*(\S+)", m.group(2), re.M):
            if b in unit_btn:
                reachable.add(unit_btn[b])
            if b in dozer_btn:
                reachable.add(dozer_btn[b])
    return reachable, has_btn, dozer_objs


def select_ad(entries: dict[str, bytes]) -> dict[str, dict]:
    reachable, has_btn, dozer_objs = buildable_maps(entries)
    first: dict[str, dict] = {}
    for path, text in object_files(entries):
        for name, _s, _e, block in iter_objects(text):
            rec = {
                "path": path,
                "max": field(block, "MaxSimultaneousOfType"),
                "link": field(block, "MaxSimultaneousLinkKey"),
                "kind": kindof(block),
                "cost": field(block, "BuildCost"),
                "side": field(block, "Side"),
            }
            first.setdefault(name, rec)
    selected: dict[str, dict] = {}
    for name, d in first.items():
        if EXCLUDE_NAME.search(name):
            continue
        buildable = name in reachable or name in has_btn or name in dozer_objs
        if d["link"] == "Patch_AirDefense":
            selected[name] = d
        elif ad_path(d["path"]) and d["cost"] and buildable:
            selected[name] = d
        elif NAMED.search(name) and d["cost"] and buildable:
            selected[name] = d
        elif "FS_BASE_DEFENSE" in d["kind"] and SITE.search(name) and (
            d["cost"] or name in dozer_objs
        ):
            selected[name] = d
    return selected


def patch_block(block: str) -> str:
    nl = "\r\n" if "\r\n" in block else "\n"
    block = re.sub(
        r"^([ \t]*MaxSimultaneousLinkKey\s*=\s*Patch_AirDefense[^\r\n]*\r?\n)",
        "",
        block,
        flags=re.M,
    )
    if re.search(r"^([ \t]*MaxSimultaneousOfType\s*=\s*)\S+", block, re.M):
        return re.sub(
            r"^([ \t]*MaxSimultaneousOfType\s*=\s*)\S+",
            r"\g<1>3",
            block,
            count=1,
            flags=re.M,
        )
    lines = block.splitlines()
    out: list[str] = []
    inserted = False
    for line in lines:
        out.append(line)
        if (not inserted) and re.match(r"^\s*Side\s*=", line):
            out.append("  MaxSimultaneousOfType = 3")
            inserted = True
        elif (not inserted) and re.match(r"^\s*BuildCost\s*=", line):
            out.append("  MaxSimultaneousOfType = 3")
            inserted = True
    if not inserted:
        raise RuntimeError("could not insert MaxSimultaneousOfType")
    text = nl.join(out)
    if not text.endswith(nl):
        text += nl
    return text


def patch_file(text: str, names: set[str]) -> tuple[str, int]:
    pieces: list[str] = []
    last = 0
    n_changed = 0
    for name, start, end, block in iter_objects(text):
        pieces.append(text[last:start])
        if name in names:
            new_block = patch_block(block)
            pieces.append(new_block)
            n_changed += 1
            last = end
        else:
            pieces.append(block)
            last = end
    pieces.append(text[last:])
    return "".join(pieces), n_changed


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("VALIDATE FAIL: " + msg)


def validate(orig: dict[str, bytes], new: dict[str, bytes], names: set[str]) -> list[str]:
    require(orig[K_CS] == new[K_CS], "CommandSet.ini changed")
    require(orig[K_CB] == new[K_CB], "CommandButton.ini changed")
    require(orig[K_WPN] == new[K_WPN], "Weapon.ini changed")
    rs = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Wheeled\RS-24_Yars.ini"
    require(orig[rs] == new[rs], "unrelated RS-24 object changed")
    first_new: dict[str, dict] = {}
    for path, text in object_files(new):
        for name, _s, _e, block in iter_objects(text):
            if name not in first_new:
                first_new[name] = {
                    "max": field(block, "MaxSimultaneousOfType"),
                    "link": field(block, "MaxSimultaneousLinkKey"),
                    "cost": field(block, "BuildCost"),
                    "kind": kindof(block),
                }
    for name in names:
        require(name in first_new, f"lost object {name}")
        require(first_new[name]["max"] == "3", f"{name} cap is {first_new[name]['max']}")
        require(
            first_new[name]["link"] != "Patch_AirDefense",
            f"{name} still pooled on Patch_AirDefense",
        )
    # cost/kind of a sample must match orig first-win
    first_old: dict[str, dict] = {}
    for path, text in object_files(orig):
        for name, _s, _e, block in iter_objects(text):
            if name not in first_old:
                first_old[name] = {
                    "cost": field(block, "BuildCost"),
                    "kind": kindof(block),
                    "wpn": "WeaponSet" in block,
                }
    for name in names:
        require(first_old[name]["cost"] == first_new[name]["cost"], f"{name} cost changed")
        require(first_old[name]["kind"] == first_new[name]["kind"], f"{name} KindOf changed")
    notes = [f"objects={len(names)}"]
    return notes


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    blob = SRC_BIG.read_bytes()
    if hashlib.sha256(blob).hexdigest() != SRC_SHA:
        raise SystemExit("source BIG sha mismatch")
    orig = read_big(SRC_BIG)
    selected = select_ad(orig)
    names = set(selected)
    if len(names) < 50:
        raise SystemExit(f"AD set too small: {len(names)}")
    new = dict(orig)
    files_changed = 0
    blocks_changed = 0
    for path, text in object_files(orig):
        patched, n = patch_file(text, names)
        if n:
            new[path] = patched.encode("latin1")
            files_changed += 1
            blocks_changed += n
    notes = validate(orig, new, names)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_blob = build_big(new)
    digest = hashlib.sha256(out_blob).hexdigest()
    OUT_BIG.write_bytes(out_blob)
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(digest + "\n", encoding="ascii")
    for name, key in (("CommandSet.ini", K_CS), ("CommandButton.ini", K_CB)):
        (OUT_DIR / name).write_bytes(new[key])
        (OUT_DIR / f"{name}.sha256").write_text(
            hashlib.sha256(new[key]).hexdigest() + "\n", encoding="ascii"
        )
    inv_lines = ["side\tname\told_max\told_link\tcost\tpath"]
    for name, d in sorted(selected.items(), key=lambda kv: ((kv[1]["side"] or ""), kv[0])):
        inv_lines.append(
            "\t".join(
                [
                    d["side"] or "?",
                    name,
                    d["max"] or "-",
                    d["link"] or "-",
                    d["cost"] or "-",
                    d["path"],
                ]
            )
        )
    (OUT_DIR / "AD_MAX_THREE_INVENTORY.tsv").write_text(
        "\n".join(inv_lines) + "\n", encoding="utf-8"
    )
    print("wrote", OUT_BIG, "bytes", len(out_blob), "sha256", digest)
    print("files", files_changed, "blocks", blocks_changed, "objects", len(names))
    for n in notes:
        print(" ", n)
    sides = defaultdict(int)
    for d in selected.values():
        sides[d["side"] or "?"] += 1
    print(" sides", len(sides))


if __name__ == "__main__":
    main()
