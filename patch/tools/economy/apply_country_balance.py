#!/usr/bin/env python3
"""Specter Patch — Country Balance System applicator.

Reads ONE central config: patch/Data/INI/CountryBalance.ini

FinalCost = Base
  × Country.(Unit|Aircraft|Weapon|Upgrade)CostMult
  × Origin × TechClass × Category × Asymmetric × Domestic

Deterministic for multiplayer: same INI + same BaseCost ⇒ same finals.
No per-unit hardcoded overrides (UseUnitRegistry = No).
Preserves BaseCost via `; PatchBaseCost` markers.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # patch/
CENTRAL = ROOT / "Data" / "INI" / "CountryBalance.ini"
OBJECT_ROOT = ROOT / "Data" / "INI" / "Object"


def parse_blocks(text: str, keyword: str) -> list[tuple[str, dict[str, str]]]:
    blocks: list[tuple[str, dict[str, str]]] = []
    pattern = re.compile(
        rf"^{keyword}\s+(\S+)\s*\n(.*?)(?=^End\s*$)",
        re.M | re.S,
    )
    for m in pattern.finditer(text):
        fields: dict[str, str] = {}
        for line in m.group(2).splitlines():
            line = line.split(";", 1)[0].strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            fields[k.strip()] = v.strip()
        blocks.append((m.group(1), fields))
    return blocks


def load_map(text: str, keyword: str) -> dict[str, dict[str, str]]:
    return {n: f for n, f in parse_blocks(text, keyword)}


def fnum(d: dict[str, str], key: str, default: float = 1.0) -> float:
    if key not in d:
        return default
    try:
        return float(d[key].replace("%", "").strip())
    except ValueError:
        return default


def glob_match(pattern: str, path_norm: str) -> bool:
    rx = re.escape(pattern).replace(r"\*", ".*")
    return re.search(rx, path_norm) is not None


@dataclass
class BalanceTables:
    system: dict[str, str] = field(default_factory=dict)
    countries: dict[str, dict[str, str]] = field(default_factory=dict)
    origins: dict[str, dict[str, str]] = field(default_factory=dict)
    tech: dict[str, dict[str, str]] = field(default_factory=dict)
    categories: dict[str, dict[str, str]] = field(default_factory=dict)
    domestic: dict[str, str] = field(default_factory=dict)
    asymmetric: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    rules: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    resource_tiers: dict[str, dict[str, str]] = field(default_factory=dict)


def load_central(path: Path = CENTRAL) -> BalanceTables:
    if not path.exists():
        raise SystemExit(f"Missing central config: {path}")
    text = path.read_text(errors="replace")
    t = BalanceTables()
    sys_map = load_map(text, "CountryBalanceSystem")
    t.system = sys_map.get("System", next(iter(sys_map.values()), {})) if sys_map else {}
    # CountryBalanceSystem has no name in our file — keyword is CountryBalanceSystem with name missing
    # Our blocks are `CountryBalanceSystem` then fields then End — parse specially
    m = re.search(
        r"^CountryBalanceSystem\s*\n(.*?)(?=^End\s*$)",
        text,
        re.M | re.S,
    )
    if m:
        fields: dict[str, str] = {}
        for line in m.group(1).splitlines():
            line = line.split(";", 1)[0].strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            fields[k.strip()] = v.strip()
        t.system = fields
    t.countries = load_map(text, "Country")
    t.origins = load_map(text, "Origin")
    t.tech = load_map(text, "TechClass")
    t.categories = load_map(text, "Category")
    dom = load_map(text, "DomesticProduction")
    t.domestic = dom.get("Bonus", {"CostMult": "0.95", "TimeMult": "0.90", "UpgradeCostMult": "0.90"})
    t.asymmetric = parse_blocks(text, "AsymmetricRule")
    t.rules = parse_blocks(text, "CategoryRule")
    t.resource_tiers = load_map(text, "ResourceTier")
    return t


def match_rule(obj_name: str, rel_path: str, tables: BalanceTables) -> dict[str, str]:
    path_norm = rel_path.replace("\\", "/")
    for _name, fields in tables.rules:
        mp = fields.get("MatchPath")
        mr = fields.get("MatchNameRegex")
        path_ok = True if not mp else glob_match(mp, path_norm)
        name_ok = True if not mr else re.search(mr, obj_name, re.I) is not None
        if mp and mr:
            if path_ok and name_ok:
                return fields
        elif mp and path_ok:
            return fields
        elif mr and name_ok:
            return fields
    return {}


def resolve_meta(
    obj_name: str, side: str, rel_path: str, is_upgrade: bool, tables: BalanceTables
) -> dict[str, str]:
    meta: dict[str, str] = {}
    rule = match_rule(obj_name, rel_path, tables)
    if "Category" in rule:
        meta["Category"] = rule["Category"]
    if "DefaultOrigin" in rule:
        meta["Origin"] = rule["DefaultOrigin"]
    if "DefaultTechClass" in rule:
        meta["TechClass"] = rule["DefaultTechClass"]
    if is_upgrade:
        meta["Category"] = "Upgrade"
    origin = meta.get("Origin", tables.system.get("DefaultOrigin", "Licensed"))
    if origin == "OwnerDomestic":
        origin = "Domestic"
    meta["Origin"] = origin
    meta.setdefault("TechClass", tables.system.get("DefaultTechClass", "Standard"))
    meta.setdefault("Category", "Vehicle" if not is_upgrade else "Upgrade")
    meta["Side"] = side
    return meta


def asymmetric_mults(category: str, rating: str, tables: BalanceTables) -> tuple[float, float]:
    cost_m = time_m = 1.0
    for _n, fields in tables.asymmetric:
        if fields.get("Category") != category:
            continue
        if rating not in fields.get("MatchEconomyRating", "").split():
            continue
        cost_m *= fnum(fields, "CostMult", 1.0)
        time_m *= fnum(fields, "TimeMult", 1.0)
    return cost_m, time_m


def country_cost_key(category: str, tables: BalanceTables) -> str:
    cat = tables.categories.get(category, {})
    return cat.get("CountryCostKey", "UnitCostMult")


def compute(
    base_cost: float,
    base_time: float,
    side: str,
    meta: dict[str, str],
    tables: BalanceTables,
    is_upgrade: bool,
) -> tuple[int, float, dict]:
    country = tables.countries.get(side)
    if not country:
        country = {
            "EconomyRating": "Medium",
            "UnitCostMult": "1",
            "AircraftCostMult": "1",
            "WeaponCostMult": "1",
            "UpgradeCostMult": "1",
            "BuildTimeMult": "1",
        }
    rating = country.get("EconomyRating", "Medium")
    category = meta.get("Category", "Vehicle")
    key = "UpgradeCostMult" if is_upgrade else country_cost_key(category, tables)
    # WeaponCostMult also when TechClass is HighTechMissile
    if not is_upgrade and meta.get("TechClass") == "HighTechMissile" and category != "Missile":
        key = "WeaponCostMult"
    eco = fnum(country, key, 1.0)
    build_time_country = fnum(country, "BuildTimeMult", 1.0)

    origin = meta.get("Origin", "Licensed")
    org = tables.origins.get(origin, {})
    org_cost = fnum(org, "UpgradeCostMult" if is_upgrade else "CostMult", 1.0)
    org_time = fnum(org, "TimeMult", 1.0)

    tech = tables.tech.get(meta.get("TechClass", "Standard"), {})
    tech_cost = fnum(tech, "CostMult", 1.0)
    tech_time = fnum(tech, "TimeMult", 1.0)

    cat = tables.categories.get(category, {})
    cat_cost = fnum(cat, "CostMult", 1.0)
    cat_time = fnum(cat, "TimeMult", 1.0)

    asym_c, asym_t = asymmetric_mults(category, rating, tables)

    dom_c = dom_t = dom_u = 1.0
    if origin == "Domestic":
        dom_c = fnum(tables.domestic, "CostMult", 0.95)
        dom_t = fnum(tables.domestic, "TimeMult", 0.90)
        dom_u = fnum(tables.domestic, "UpgradeCostMult", 0.90)

    if is_upgrade:
        cost_m = eco * org_cost * tech_cost * cat_cost * asym_c * (dom_u if origin == "Domestic" else 1.0)
    else:
        cost_m = eco * org_cost * tech_cost * cat_cost * asym_c * (dom_c if origin == "Domestic" else 1.0)
    time_m = org_time * tech_time * cat_time * asym_t * build_time_country
    if origin == "Domestic":
        time_m *= dom_t

    final_cost = max(1, int(round(base_cost * cost_m)))
    final_time = max(0.1, round(base_time * time_m, 1))
    detail = {
        "rating": rating,
        "origin": origin,
        "tech": meta.get("TechClass"),
        "category": category,
        "cost_key": key,
        "cost_m": round(cost_m, 4),
        "time_m": round(time_m, 4),
        "eco": eco,
    }
    return final_cost, final_time, detail


OBJ_RE = re.compile(r"^Object\s+(\S+)\s*$", re.M)
UPG_RE = re.compile(r"^Upgrade\s+(\S+)\s*$", re.M)
SIDE_RE = re.compile(r"^\s*Side\s*=\s*(\S+)", re.M)
COST_RE = re.compile(r"^(\s*)BuildCost\s*=\s*([0-9]+)", re.M)
TIME_RE = re.compile(r"^(\s*)BuildTime\s*=\s*([0-9.]+)", re.M)
BASE_COST_RE = re.compile(r";\s*PatchBaseCost\s*=\s*([0-9.]+)")
BASE_TIME_RE = re.compile(r";\s*PatchBaseTime\s*=\s*([0-9.]+)")
APPLIED_RE = re.compile(r";\s*PatchPricing\s+.*\n|; \s*CountryBalance\s+.*\n")
SKIP_NAME_RE = re.compile(
    r"(Damaged|Debris|Hulk|Lock|Projectile|WeaponObject|Explosion|Cloud|BombObject|Crashed)",
    re.I,
)


def split_blocks(text: str, kind: str) -> list[tuple[int, int, str, str]]:
    rx = OBJ_RE if kind == "Object" else UPG_RE
    matches = list(rx.finditer(text))
    out = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((start, end, m.group(1), text[start:end]))
    return out


def process_file(
    path: Path,
    tables: BalanceTables,
    side_filter: str | None,
    dry_run: bool,
    kind: str,
) -> list[dict]:
    text = path.read_text(errors="replace")
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    reports: list[dict] = []
    blocks = split_blocks(text, kind)
    if not blocks:
        return reports
    new_text = text
    for start, end, name, block in reversed(blocks):
        is_upgrade = kind == "Upgrade"
        if SKIP_NAME_RE.search(name):
            continue
        sm = SIDE_RE.search(block)
        side = sm.group(1) if sm else None
        if is_upgrade:
            mside = re.match(r"Upgrade_([A-Za-z]+)_", name)
            side = mside.group(1) if mside else side_filter
        if not side:
            continue
        if side_filter and side != side_filter:
            continue
        cm = COST_RE.search(block)
        if not cm:
            continue
        tm = TIME_RE.search(block)
        cur_cost = float(cm.group(2))
        cur_time = float(tm.group(2)) if tm else 10.0
        bcm = BASE_COST_RE.search(block)
        btm = BASE_TIME_RE.search(block)
        base_cost = float(bcm.group(1)) if bcm else cur_cost
        base_time = float(btm.group(1)) if btm else cur_time

        meta = resolve_meta(name, side, rel, is_upgrade, tables)
        final_cost, final_time, detail = compute(
            base_cost, base_time, side, meta, tables, is_upgrade
        )

        new_block = APPLIED_RE.sub("", block)
        new_block = BASE_COST_RE.sub("", new_block)
        new_block = BASE_TIME_RE.sub("", new_block)
        header_end = new_block.find("\n") + 1
        marker = (
            f"; PatchBaseCost = {int(base_cost) if base_cost == int(base_cost) else base_cost}\n"
            f"; PatchBaseTime = {base_time}\n"
            f"; CountryBalance side={side} origin={detail['origin']} tech={detail['tech']} "
            f"cat={detail['category']} key={detail['cost_key']} rating={detail['rating']} "
            f"cost×{detail['cost_m']} time×{detail['time_m']} => {final_cost} / {final_time}s\n"
        )
        new_block = new_block[:header_end] + marker + new_block[header_end:]
        new_block, _ = COST_RE.subn(
            lambda m: f"{m.group(1)}BuildCost           = {final_cost}", new_block, count=1
        )
        if tm:
            new_block, _ = TIME_RE.subn(
                lambda m: f"{m.group(1)}BuildTime           = {final_time}", new_block, count=1
            )
        new_text = new_text[:start] + new_block + new_text[end:]
        reports.append(
            {
                "name": name,
                "side": side,
                "file": rel,
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


def apply_income(tables: BalanceTables, side_filter: str | None, dry_run: bool) -> list[str]:
    notes = []
    base_deposit = int(fnum(tables.system, "SupplyDepositBase", 20))
    timing = int(fnum(tables.system, "SupplyDepositTimingMS", 15000))
    for path in OBJECT_ROOT.rglob("*.ini"):
        if "SupplyCenter" not in path.name and "SupplyStash" not in path.name:
            continue
        text = path.read_text(errors="replace")
        changed = False
        new_text = text
        for start, end, name, block in reversed(split_blocks(text, "Object")):
            if "SupplyCenter" not in name and "SupplyStash" not in name:
                continue
            sm = SIDE_RE.search(block)
            if not sm:
                continue
            side = sm.group(1)
            if side_filter and side != side_filter:
                continue
            country = tables.countries.get(side)
            if not country:
                continue
            # Prefer TradeIncomeMult for passive supply-center income; Port for ports later
            mult = fnum(country, "TradeIncomeMult", fnum(country, "SupplyIncomeMult", 1.0))
            deposit = max(1, int(round(base_deposit * mult)))
            module = (
                f"  Behavior = AutoDepositUpdate ModuleTag_PatchResourceIncome\n"
                f"    DepositTiming       = {timing}\n"
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
                nb = re.sub(
                    r"(ModuleTag_PatchResourceIncome\n\s*DepositTiming\s*=\s*)([0-9]+)",
                    rf"\g<1>{timing}",
                    nb,
                    count=1,
                )
            else:
                beh = re.search(r"^(\s*Behavior\s*=)", block, re.M)
                if beh:
                    nb = block[: beh.start()] + module + block[beh.start() :]
                else:
                    nb = block + "\n" + module
            if nb != block:
                new_text = new_text[:start] + nb + new_text[end:]
                changed = True
            notes.append(
                f"{name} ({side}/{country.get('EconomyRating')}): "
                f"DepositAmount={deposit} Trade×{mult}"
            )
        if changed and not dry_run:
            path.write_text(new_text)
    return notes


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Country Balance System from central INI")
    ap.add_argument("--config", type=Path, default=CENTRAL)
    ap.add_argument("--side")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-income", action="store_true")
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    tables = load_central(args.config)
    if tables.system.get("Deterministic", "Yes").lower() not in ("yes", "true", "1"):
        print("WARNING: Deterministic != Yes in CountryBalance.ini")

    reports: list[dict] = []
    for path in OBJECT_ROOT.rglob("*.ini"):
        reports.extend(process_file(path, tables, args.side, args.dry_run, "Object"))
    for path in (ROOT / "Data" / "INI").glob("Upgrade_*.ini"):
        reports.extend(process_file(path, tables, args.side, args.dry_run, "Upgrade"))

    income = []
    if not args.no_income:
        income = apply_income(tables, args.side, args.dry_run)

    print(f"CountryBalance: {args.config}")
    print(f"Priced entries: {len(reports)}  dry_run={args.dry_run}  countries={len(tables.countries)}")
    for r in reports[:12]:
        print(
            f"  {r['name']}: {r['base_cost']} -> {r['final_cost']} "
            f"({r['side']}/{r['category']}/{r['cost_key']}) ×{r['cost_m']}"
        )
    if len(reports) > 12:
        print(f"  ... +{len(reports) - 12} more")
    for n in income[:8]:
        print("  income:", n)

    if args.report:
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
            "cost_key",
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
