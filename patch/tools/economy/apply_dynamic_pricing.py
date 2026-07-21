#!/usr/bin/env python3
"""Specter Patch — Dynamic Pricing applicator.

FinalCost = BaseCost × Economy × Origin × Tech × Asymmetric × Domestic

Preserves BaseCost in `; PatchBaseCost = N` so re-runs do not compound.
Reads tables from patch/Data/INI/Economy/.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # patch/
ECONOMY = ROOT / "Data" / "INI" / "Economy"
OBJECT_ROOT = ROOT / "Data" / "INI" / "Object"
UPGRADE_GLOB = list((ROOT / "Data" / "INI").glob("Upgrade_*.ini"))


def parse_blocks(text: str, keyword: str) -> list[tuple[str, dict[str, str]]]:
    """Parse `Keyword Name\\n  Key = Val\\nEnd` blocks."""
    blocks: list[tuple[str, dict[str, str]]] = []
    pattern = re.compile(
        rf"^{keyword}\s+(\S+)\s*\n(.*?)(?=^End\s*$)",
        re.M | re.S,
    )
    for m in pattern.finditer(text):
        name = m.group(1)
        body = m.group(2)
        fields: dict[str, str] = {}
        for line in body.splitlines():
            line = line.split(";", 1)[0].strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            fields[k.strip()] = v.strip()
        blocks.append((name, fields))
    return blocks


def load_map(path: Path, keyword: str) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    return {n: f for n, f in parse_blocks(path.read_text(errors="replace"), keyword)}


def fnum(d: dict[str, str], key: str, default: float = 1.0) -> float:
    if key not in d:
        return default
    raw = d[key].replace("%", "").strip()
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass
class PricingTables:
    factions: dict[str, dict[str, str]] = field(default_factory=dict)
    origins: dict[str, dict[str, str]] = field(default_factory=dict)
    tech: dict[str, dict[str, str]] = field(default_factory=dict)
    domestic: dict[str, str] = field(default_factory=dict)
    asymmetric: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    defaults: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    registry: dict[str, dict[str, str]] = field(default_factory=dict)
    resource: dict[str, dict[str, str]] = field(default_factory=dict)


def load_tables() -> PricingTables:
    t = PricingTables()
    t.factions = load_map(ECONOMY / "FactionEconomy.ini", "FactionEconomy")
    t.origins = load_map(ECONOMY / "EquipmentOrigin.ini", "EquipmentOrigin")
    t.tech = load_map(ECONOMY / "TechnologyClass.ini", "TechnologyClass")
    dom = load_map(ECONOMY / "DomesticProduction.ini", "DomesticProduction")
    t.domestic = dom.get("Bonus", {"CostMult": "0.95", "TimeMult": "0.90", "UpgradeCostMult": "0.90"})
    t.asymmetric = parse_blocks(
        (ECONOMY / "AsymmetricBalance.ini").read_text(errors="replace"), "AsymmetricRule"
    )
    t.defaults = parse_blocks(
        (ECONOMY / "PricingDefaults.ini").read_text(errors="replace"), "PricingDefault"
    )
    t.registry = load_map(ECONOMY / "UnitPricingRegistry.ini", "PricingEntry")
    t.resource = load_map(ECONOMY / "ResourceIncome.ini", "ResourceIncome")
    return t


def glob_match(pattern: str, path_norm: str) -> bool:
    """Minimal glob: * matches any substring."""
    rx = re.escape(pattern).replace(r"\*", ".*")
    return re.search(rx, path_norm) is not None


def match_default(obj_name: str, rel_path: str, tables: PricingTables) -> dict[str, str]:
    path_norm = rel_path.replace("\\", "/")
    for _name, fields in tables.defaults:
        mp = fields.get("MatchPath")
        mr = fields.get("MatchNameRegex")
        path_ok = True if not mp else glob_match(mp, path_norm)
        name_ok = True if not mr else re.search(mr, obj_name, re.I) is not None
        if mp and mr:
            if path_ok and name_ok:
                return fields
        elif mp:
            if path_ok:
                return fields
        elif mr:
            if name_ok:
                return fields
    return {}


def registry_lookup(name: str, tables: PricingTables) -> dict[str, str]:
    """Exact PricingEntry, else longest registered prefix (for loadout variants)."""
    if name in tables.registry:
        return dict(tables.registry[name])
    best = ""
    for key in tables.registry:
        if name.startswith(key) and len(key) > len(best):
            best = key
    return dict(tables.registry[best]) if best else {}


def resolve_meta(
    obj_name: str,
    side: str,
    rel_path: str,
    is_upgrade: bool,
    tables: PricingTables,
) -> dict[str, str]:
    meta: dict[str, str] = {}
    dflt = match_default(obj_name, rel_path, tables)
    if "Category" in dflt:
        meta["Category"] = dflt["Category"]
    if "DefaultOrigin" in dflt:
        meta["Origin"] = dflt["DefaultOrigin"]
    if "DefaultTechClass" in dflt:
        meta["TechClass"] = dflt["DefaultTechClass"]

    # Registry (exact or longest prefix) overrides defaults
    reg = registry_lookup(obj_name, tables)
    for k, v in reg.items():
        if k in ("BaseCost", "BaseTime"):
            continue
        meta[k] = v

    if is_upgrade:
        meta.setdefault("Category", "Upgrade")

    origin = meta.get("Origin", "Licensed")
    if origin == "OwnerDomestic":
        origin = "Domestic"
    meta["Origin"] = origin
    meta.setdefault("TechClass", "Standard")
    meta.setdefault("Category", "Vehicle" if not is_upgrade else "Upgrade")
    meta["Side"] = side
    return meta


def asymmetric_mults(category: str, economy_rating: str, tables: PricingTables) -> tuple[float, float]:
    cost_m, time_m = 1.0, 1.0
    for _name, fields in tables.asymmetric:
        if fields.get("Category") != category:
            continue
        ratings = fields.get("MatchEconomyRating", "").split()
        if economy_rating not in ratings:
            continue
        cost_m *= fnum(fields, "CostMult", 1.0)
        time_m *= fnum(fields, "TimeMult", 1.0)
    return cost_m, time_m


def compute(
    base_cost: float,
    base_time: float,
    side: str,
    meta: dict[str, str],
    tables: PricingTables,
    is_upgrade: bool,
) -> tuple[int, float, dict]:
    fac = tables.factions.get(side)
    if not fac:
        # Unknown side: neutral
        fac = {
            "EconomyRating": "Medium",
            "PurchaseCostMult": "1.0",
            "UpgradeCostMult": "1.0",
        }
    rating = fac.get("EconomyRating", "Medium")
    eco_cost = fnum(fac, "UpgradeCostMult" if is_upgrade else "PurchaseCostMult", 1.0)

    origin = meta.get("Origin", "Licensed")
    org = tables.origins.get(origin, {"CostMult": "1", "TimeMult": "1", "UpgradeCostMult": "1"})
    org_cost = fnum(org, "UpgradeCostMult" if is_upgrade else "CostMult", 1.0)
    org_time = fnum(org, "TimeMult", 1.0)

    tech = tables.tech.get(meta.get("TechClass", "Standard"), {"CostMult": "1", "TimeMult": "1"})
    tech_cost = fnum(tech, "CostMult", 1.0)
    tech_time = fnum(tech, "TimeMult", 1.0)

    asym_cost, asym_time = asymmetric_mults(meta.get("Category", "Vehicle"), rating, tables)

    dom_cost = dom_time = dom_up = 1.0
    if origin == "Domestic":
        dom_cost = fnum(tables.domestic, "CostMult", 0.95)
        dom_time = fnum(tables.domestic, "TimeMult", 0.90)
        dom_up = fnum(tables.domestic, "UpgradeCostMult", 0.90)

    if is_upgrade:
        cost_m = eco_cost * org_cost * tech_cost * asym_cost * (dom_up if origin == "Domestic" else 1.0)
    else:
        cost_m = eco_cost * org_cost * tech_cost * asym_cost * (dom_cost if origin == "Domestic" else 1.0)
    time_m = org_time * tech_time * asym_time * (dom_time if origin == "Domestic" else 1.0)

    final_cost = max(1, int(round(base_cost * cost_m)))
    final_time = max(0.1, round(base_time * time_m, 1))
    detail = {
        "rating": rating,
        "origin": origin,
        "tech": meta.get("TechClass"),
        "category": meta.get("Category"),
        "cost_m": round(cost_m, 4),
        "time_m": round(time_m, 4),
        "eco": eco_cost,
        "org": org_cost,
        "tech_m": tech_cost,
        "asym": asym_cost,
        "dom": dom_cost if not is_upgrade else dom_up,
    }
    return final_cost, final_time, detail


OBJ_RE = re.compile(r"^Object\s+(\S+)\s*$", re.M)
UPG_RE = re.compile(r"^Upgrade\s+(\S+)\s*$", re.M)
SIDE_RE = re.compile(r"^\s*Side\s*=\s*(\S+)", re.M)
COST_RE = re.compile(r"^(\s*)BuildCost\s*=\s*([0-9]+)", re.M)
TIME_RE = re.compile(r"^(\s*)BuildTime\s*=\s*([0-9.]+)", re.M)
BASE_COST_RE = re.compile(r";\s*PatchBaseCost\s*=\s*([0-9.]+)")
BASE_TIME_RE = re.compile(r";\s*PatchBaseTime\s*=\s*([0-9.]+)")
APPLIED_RE = re.compile(r";\s*PatchPricing\s+.*\n")


def split_object_blocks(text: str, kind: str) -> list[tuple[int, int, str, str]]:
    """Return list of (start, end, name, block_text) for Object or Upgrade blocks."""
    rx = OBJ_RE if kind == "Object" else UPG_RE
    matches = list(rx.finditer(text))
    out = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        # trim to End of this object roughly — keep until next Object/Upgrade
        out.append((start, end, m.group(1), text[start:end]))
    return out


SKIP_NAME_RE = re.compile(
    r"(Damaged|Debris|Hulk|Lock|Projectile|WeaponObject|Explosion|Cloud|BombObject|Crashed)",
    re.I,
)


def registry_lookup(name: str, tables: PricingTables) -> dict[str, str]:
    """Exact PricingEntry, else longest registered prefix (for loadout variants)."""
    if name in tables.registry:
        return dict(tables.registry[name])
    best = ""
    for key in tables.registry:
        if name.startswith(key) and len(key) > len(best):
            best = key
    return dict(tables.registry[best]) if best else {}


def process_file(
    path: Path,
    tables: PricingTables,
    side_filter: str | None,
    dry_run: bool,
    kind: str,
) -> list[dict]:
    text = path.read_text(errors="replace")
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    reports = []
    blocks = split_object_blocks(text, kind)
    if not blocks:
        return reports

    new_text = text
    # Process from end to start so offsets stay valid
    for start, end, name, block in reversed(blocks):
        is_upgrade = kind == "Upgrade"
        if SKIP_NAME_RE.search(name):
            continue
        sm = SIDE_RE.search(block)
        side = sm.group(1) if sm else None
        if is_upgrade:
            # Upgrade_Turkey_* → Turkey
            mside = re.match(r"Upgrade_([A-Za-z]+)_", name)
            side = mside.group(1) if mside else side_filter or "Turkey"
            # AmericaAirForceGeneral won't match simple — OK
        if not side:
            continue
        if side_filter and side != side_filter:
            continue

        cm = COST_RE.search(block)
        if not cm:
            continue
        tm = TIME_RE.search(block)

        bcm = BASE_COST_RE.search(block)
        btm = BASE_TIME_RE.search(block)
        cur_cost = float(cm.group(2))
        cur_time = float(tm.group(2)) if tm else 10.0
        base_cost = float(bcm.group(1)) if bcm else cur_cost
        base_time = float(btm.group(1)) if btm else cur_time

        # Registry may override base (exact or prefix variant)
        reg = registry_lookup(name, tables)
        meta = resolve_meta(name, side, rel, is_upgrade, tables)
        if "BaseCost" in reg:
            base_cost = fnum(reg, "BaseCost", base_cost)
        if "BaseTime" in reg:
            base_time = fnum(reg, "BaseTime", base_time)

        final_cost, final_time, detail = compute(
            base_cost, base_time, side, meta, tables, is_upgrade
        )

        new_block = block
        # Strip old PatchPricing lines
        new_block = APPLIED_RE.sub("", new_block)
        # Ensure base markers after Object/Upgrade line
        header_end = new_block.find("\n") + 1
        # Remove existing base markers
        new_block = BASE_COST_RE.sub("", new_block)
        new_block = BASE_TIME_RE.sub("", new_block)
        # clean double blank from removals lightly
        marker = (
            f"; PatchBaseCost = {int(base_cost) if base_cost == int(base_cost) else base_cost}\n"
            f"; PatchBaseTime = {base_time}\n"
            f"; PatchPricing side={side} origin={detail['origin']} tech={detail['tech']} "
            f"cat={detail['category']} rating={detail['rating']} "
            f"cost×{detail['cost_m']} time×{detail['time_m']} "
            f"=> {final_cost} / {final_time}s\n"
        )
        new_block = new_block[:header_end] + marker + new_block[header_end:]

        def repl_cost(m):
            return f"{m.group(1)}BuildCost           = {final_cost}"

        def repl_time(m):
            # keep trailing comment if any on original — TIME_RE doesn't capture comment
            return f"{m.group(1)}BuildTime           = {final_time}"

        new_block, ncost = COST_RE.subn(repl_cost, new_block, count=1)
        if tm:
            new_block, ntime = TIME_RE.subn(repl_time, new_block, count=1)
        else:
            ntime = 0

        new_text = new_text[:start] + new_block + new_text[end:]
        reports.append(
            {
                "file": rel,
                "name": name,
                "side": side,
                "base_cost": base_cost,
                "final_cost": final_cost,
                "base_time": base_time,
                "final_time": final_time,
                **detail,
            }
        )

    if reports and not dry_run and new_text != text:
        path.write_text(new_text)
    return reports


def apply_supply_income(tables: PricingTables, side_filter: str | None, dry_run: bool) -> list[str]:
    """Inject/update ModuleTag_PatchResourceIncome on SupplyCenter buildings only."""
    notes = []
    base_deposit = 20
    for path in OBJECT_ROOT.rglob("*.ini"):
        if "SupplyCenter" not in path.name and "SupplyStash" not in path.name:
            continue
        text = path.read_text(errors="replace")
        changed = False
        blocks = split_object_blocks(text, "Object")
        new_text = text
        for start, end, name, block in reversed(blocks):
            if "SupplyCenter" not in name and "SupplyStash" not in name:
                continue
            sm = SIDE_RE.search(block)
            if not sm:
                continue
            side = sm.group(1)
            if side_filter and side != side_filter:
                continue
            fac = tables.factions.get(side)
            if not fac:
                continue
            rating = fac.get("EconomyRating", "Medium")
            res = tables.resource.get(rating, {})
            mult = fnum(res, "PortTradeMult", 1.0)
            deposit = max(1, int(round(base_deposit * mult)))
            module = (
                f"  Behavior = AutoDepositUpdate ModuleTag_PatchResourceIncome\n"
                f"    DepositTiming       = 15000\n"
                f"    DepositAmount       = {deposit}\n"
                f"    InitialCaptureBonus = 0\n"
                f"  End\n"
            )
            if "ModuleTag_PatchResourceIncome" in block:
                nb = re.sub(
                    r"(Behavior = AutoDepositUpdate ModuleTag_PatchResourceIncome\n"
                    r".*?DepositAmount\s*=\s*)([0-9]+)",
                    rf"\g<1>{deposit}",
                    block,
                    count=1,
                    flags=re.S,
                )
            else:
                # Place with other Behaviors when possible
                beh = re.search(r"^(\s*Behavior\s*=)", block, re.M)
                if beh:
                    nb = block[: beh.start()] + module + block[beh.start() :]
                elif COST_RE.search(block):
                    nb = COST_RE.sub(lambda m: m.group(0) + "\n" + module.rstrip("\n"), block, count=1)
                else:
                    nb = block + "\n" + module
            if nb != block:
                new_text = new_text[:start] + nb + new_text[end:]
                changed = True
            notes.append(f"{name} ({side}/{rating}): DepositAmount={deposit}")
        if changed and not dry_run:
            path.write_text(new_text)
    return notes


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Specter Patch dynamic pricing")
    ap.add_argument("--side", help="Only process this Side (e.g. Turkey)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-income", action="store_true", help="Skip supply income overlays")
    ap.add_argument("--report", type=Path, help="Write CSV report path")
    args = ap.parse_args()

    tables = load_tables()
    reports: list[dict] = []

    # Objects
    for path in OBJECT_ROOT.rglob("*.ini"):
        reports.extend(process_file(path, tables, args.side, args.dry_run, "Object"))

    # Upgrades
    for path in (ROOT / "Data" / "INI").glob("Upgrade_*.ini"):
        reports.extend(process_file(path, tables, args.side, args.dry_run, "Upgrade"))

    income_notes = []
    if not args.no_income:
        income_notes = apply_supply_income(tables, args.side, args.dry_run)

    print(f"Priced entries: {len(reports)}  dry_run={args.dry_run}")
    # Show sample
    for r in reports[:15]:
        print(
            f"  {r['name']}: {r['base_cost']} -> {r['final_cost']} "
            f"({r['origin']}/{r['tech']}/{r['category']}) ×{r['cost_m']}"
        )
    if len(reports) > 15:
        print(f"  ... +{len(reports) - 15} more")
    for n in income_notes[:10]:
        print("  income:", n)

    if args.report:
        import csv

        args.report.parent.mkdir(parents=True, exist_ok=True)
        keys = [
            "name",
            "side",
            "file",
            "base_cost",
            "final_cost",
            "base_time",
            "final_time",
            "rating",
            "origin",
            "tech",
            "category",
            "cost_m",
            "time_m",
        ]
        with args.report.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(reports)
        print("wrote", args.report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
