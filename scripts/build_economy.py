#!/usr/bin/env python3
"""Generate the CobbleDollars shop and bank (sell) prices, and prove they can't be exploited.

Every item gets a value: raw materials from scripts/economy/values.json, crafted items from their
cheapest recipe (sum of the inputs / output count), so crafting never adds value. Then:
  - sell price <= value
  - sell price <= SELL_RATIO x the lowest price you can BUY the item for anywhere: our shop, the
    Casino Rocket merchants, villagers (worst case 1 emerald per trade) - see external_prices.json
  - auto-priced shop items cost BUY_MARKUP x value
  - for every recipe: sell(outputs) <= value(inputs), so buy -> craft -> sell never makes money
  - items villagers pay emeralds for cost at least an emerald in our shop (cured villager: 1 item = 1 emerald)
  - gachapons: expected sell value of the contents <= GACHA_RATIO x the price
The build fails (exit code 1) when any rule is broken.

Reads recipes, tags and item ids from the server's jars (vanilla + mods), read-only.

Usage:
  python3 -I scripts/build_economy.py /srv/minecraft/servers/<id>            # check + report
  python3 -I scripts/build_economy.py /srv/minecraft/servers/<id> --write    # also write configs
"""

import argparse
import io
import json
import math
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ECON_DIR = REPO_ROOT / "scripts" / "economy"
OUT_DIR = REPO_ROOT / "server" / "config" / "cobbledollars"
VANILLA_JAR = "versions/1.21.1/server-1.21.1.jar"

SELL_RATIO = 0.25  # sell price <= 25% of the cheapest buy price
BUY_MARKUP = 4  # auto shop price = 4 x value
GACHA_RATIO = 0.5  # expected sell value of a gacha pull <= 50% of its price
INF = math.inf

# Items that come back when crafting (bucket of milk -> empty bucket).
REMAINDERS = {
    "minecraft:milk_bucket": "minecraft:bucket",
    "minecraft:water_bucket": "minecraft:bucket",
    "minecraft:lava_bucket": "minecraft:bucket",
    "minecraft:powder_snow_bucket": "minecraft:bucket",
    "minecraft:honey_bottle": "minecraft:glass_bottle",
    "minecraft:dragon_breath": "minecraft:glass_bottle",
}
SHAPED = {"minecraft:crafting_shaped", "crafting_shaped", "cobblemon:cooking_pot"}
SHAPELESS = {"minecraft:crafting_shapeless", "crafting_shapeless", "cobblemon:cooking_pot_shapeless"}
COOKING = {"minecraft:smelting", "minecraft:blasting", "minecraft:smoking", "minecraft:campfire_cooking"}


# ---------------------------------------------------------------- reading the jars

def open_jars(server: Path):
    """Yield (name, ZipFile) for vanilla, every mod and every jar nested in a mod (load order)."""
    def walk(name, z):
        yield name, z
        for n in z.namelist():
            if n.startswith("META-INF/jars/") and n.endswith(".jar"):
                yield from walk(n, zipfile.ZipFile(io.BytesIO(z.read(n))))
    yield VANILLA_JAR, zipfile.ZipFile(server / VANILLA_JAR)
    for jar in sorted((server / "mods").glob("*.jar")):
        yield from walk(jar.name, zipfile.ZipFile(jar))


def read_json(z, n):
    try:
        return json.loads(z.read(n).decode("utf-8-sig"), strict=False)
    except (ValueError, UnicodeDecodeError):
        return None


class Data:
    def __init__(self, server: Path):
        self.mods = {"minecraft", "c", "fabric", "java"}
        self.items = set((ECON_DIR / "vanilla_items_1.21.1.txt").read_text().split())
        raw_tags = defaultdict(list)  # tag -> [(replace, values)] in load order
        self.recipes = {}  # recipe id -> json (later jars override earlier ones)
        for _name, z in open_jars(server):
            names = z.namelist()
            if "fabric.mod.json" in names:
                meta = read_json(z, "fabric.mod.json") or {}
                self.mods.add(meta.get("id", ""))
                self.mods.update(meta.get("provides", []))
            for n in names:
                if not n.endswith(".json") or not n.startswith(("data/", "assets/")):
                    continue
                parts = n[:-5].split("/")
                if len(parts) >= 5 and parts[0] == "assets" and parts[2:4] == ["models", "item"]:
                    self.items.add(f"{parts[1]}:{'/'.join(parts[4:])}")
                elif len(parts) >= 4 and parts[0] == "data" and parts[2] in ("recipe", "recipes"):
                    d = read_json(z, n)
                    if isinstance(d, dict):
                        self.recipes[f"{parts[1]}:{'/'.join(parts[3:])}"] = d
                elif len(parts) >= 5 and parts[0] == "data" and parts[2] == "tags" and parts[3] in ("item", "items"):
                    d = read_json(z, n)
                    if isinstance(d, dict):
                        raw_tags[f"{parts[1]}:{'/'.join(parts[4:])}"].append((d.get("replace", False), d.get("values", [])))
        self.tags = {}
        self._raw_tags = raw_tags
        for t in raw_tags:
            self.tag(t)

    def tag(self, t, seen=()):
        if t in self.tags:
            return self.tags[t]
        out = set()
        for replace, values in self._raw_tags.get(t, []):
            if replace:
                out = set()
            for v in values:
                v = v.get("id") if isinstance(v, dict) else v
                if not isinstance(v, str):
                    continue
                if v.startswith("#"):
                    if v[1:] not in seen:
                        out |= self.tag(v[1:], seen + (t,))
                elif v in self.items:
                    out.add(v)
        self.tags[t] = out
        return out

    def conditions_ok(self, d):
        return all(self._cond(c) for c in d.get("fabric:load_conditions", []))

    def _cond(self, c):
        kind = c.get("condition", "")
        if kind == "fabric:all_mods_loaded":
            return all(m in self.mods for m in c.get("values", []))
        if kind == "fabric:any_mods_loaded":
            return any(m in self.mods for m in c.get("values", []))
        if kind == "fabric:not":
            return not self._cond(c.get("value", {}))
        if kind == "fabric:and":
            return all(self._cond(x) for x in c.get("values", []))
        if kind == "fabric:or":
            return any(self._cond(x) for x in c.get("values", []))
        if kind in ("fabric:true", "fabric:tags_populated", "fabric:registry_contains", "fabric:feature_flags_enabled"):
            return True
        return False


# ---------------------------------------------------------------- recipes

def ingredient(data, ing):
    """Ingredient JSON -> set of item ids that fit, or None if the format is unknown."""
    if isinstance(ing, list):
        out = set()
        for x in ing:
            alt = ingredient(data, x)
            if alt is None:
                return None
            out |= alt
        return out
    if isinstance(ing, str):
        return data.tag(ing[1:]) if ing.startswith("#") else {ing}
    if not isinstance(ing, dict):
        return None
    if "item" in ing and isinstance(ing["item"], str):
        return {ing["item"]}
    if "id" in ing and isinstance(ing["id"], str):
        return {ing["id"]}
    if "tag" in ing:
        return data.tag(ing["tag"])
    if "base" in ing:  # fabric:components / fabric:difference: at least the base item
        return ingredient(data, ing["base"])
    if "ingredients" in ing:  # fabric:any / fabric:all
        return ingredient(data, ing["ingredients"])
    return None


def result(r):
    """Result JSON -> (item, count) or None."""
    if isinstance(r, str):
        return r, 1
    if isinstance(r, dict):
        if isinstance(r.get("item"), dict):  # farmersdelight: {"item": {"id", "count"}}
            return result(r["item"])
        item = r.get("id") or r.get("item")
        if isinstance(item, str):
            return item, r.get("count", 1)
    return None


def parse_recipe(data, d):
    """Recipe JSON -> (inputs [(alternatives, qty)], outputs [(item, count)]) or None."""
    t = d.get("type", "")
    inputs, outputs = [], []
    if t in SHAPED:
        counts = defaultdict(int)
        for row in d.get("pattern", []):
            for ch in row:
                if ch != " ":
                    counts[ch] += 1
        for ch, n in counts.items():
            inputs.append((ingredient(data, d.get("key", {}).get(ch)), n))
        outputs.append(result(d.get("result")))
    elif t in SHAPELESS or t == "farmersdelight:cooking":
        for ing in d.get("ingredients", []):
            inputs.append((ingredient(data, ing), 1))
        if t == "farmersdelight:cooking" and d.get("container"):
            inputs.append((ingredient(data, d["container"]), 1))
        outputs.append(result(d.get("result")))
    elif t in COOKING or t == "minecraft:stonecutting":
        inputs.append((ingredient(data, d.get("ingredient")), 1))
        outputs.append(result(d.get("result")))
    elif t == "minecraft:smithing_transform":
        for k in ("template", "base", "addition"):
            inputs.append((ingredient(data, d.get(k)), 1))
        outputs.append(result(d.get("result")))
    elif t == "cobblefurnies:furni_crafting":
        for m in d.get("materials", []):
            inputs.append((ingredient(data, m), m.get("count", 1)))
        outputs.append(result(d.get("result")))
    elif t == "cobblemon:brewing_stand":  # 1 input brews 3 bottles
        inputs.append((ingredient(data, d.get("bottle")), 1))
        inputs.append((ingredient(data, d.get("input")), 1 / 3))
        outputs.append(result(d.get("result")))
    elif t == "farmersdelight:cutting":  # knife isn't used up
        inputs.append((ingredient(data, d.get("ingredients", [None])[0]), 1))
        for r in d.get("result", []):
            if r.get("chance", 1) >= 1:
                outputs.append(result(r))
    else:
        return None
    if not outputs or None in outputs:
        return None
    return inputs, outputs


# ---------------------------------------------------------------- rules / pricing

def matcher(data, pattern):
    if pattern.startswith("#"):
        members = data.tag(pattern[1:])
        return lambda i: i in members
    if pattern.startswith("re:"):
        rx = re.compile(pattern[3:])
        return lambda i: rx.fullmatch(i) is not None
    return lambda i: i == pattern


def nice(n):
    """Round a shop price up to 2 significant digits (1234 -> 1300)."""
    if n <= 100:
        return max(1, math.ceil(n))
    step = 10 ** (len(str(int(n))) - 2)
    return math.ceil(n / step) * step


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("server", type=Path, help="server folder (with mods/ and versions/)")
    ap.add_argument("--write", action="store_true", help="write server/config/cobbledollars/*.json")
    ap.add_argument("--explain", action="append", default=[], help="print how an item got its price")
    args = ap.parse_args()

    data = Data(args.server)
    values_cfg = json.loads((ECON_DIR / "values.json").read_text())
    shops_cfg = json.loads((ECON_DIR / "shops.json").read_text())
    ext_cfg = json.loads((ECON_DIR / "external_prices.json").read_text())
    errors, warnings = [], []

    rules = []
    for r in values_cfg["rules"]:
        rules.append((matcher(data, r["match"]), r))
        if not r["match"].startswith(("#", "re:")) and r["match"] not in data.items:
            errors.append(f"values.json: unknown item {r['match']}")
        if r["match"].startswith("#") and not data.tag(r["match"][1:]):
            warnings.append(f"values.json: empty tag {r['match']}")
    never = [matcher(data, p) for p in values_cfg["never_sell"]]
    ignore_unpriced = [matcher(data, p) for p in values_cfg.get("ignore_unpriced", [])]

    def rule_for(item):
        for m, r in rules:
            if m(item):
                return r
        return None

    # Base values (scaled), "value": 0 = worthless, null/missing = derive from recipes.
    scale = values_cfg.get("scale", 1)
    fixed = set(values_cfg.get("unscaled", []))
    value = defaultdict(lambda: INF)
    category = {}
    for item in sorted(data.items):
        r = rule_for(item)
        if r is None:
            continue
        if r.get("value") is not None:
            v = r["value"] if item in fixed or r["match"] in fixed else r["value"] * scale
            value[item] = int(v)
        if r.get("bank"):
            category[item] = r["bank"]

    # Buy prices elsewhere -> cap on the value.
    caps = {}  # item -> (cap, why)

    def add_cap(item, cap, why):
        cap = int(cap)
        if item not in caps or cap < caps[item][0]:
            caps[item] = (cap, why)

    for shop, offers in ext_cfg["casino_rocket"].items():
        for item, price in offers.items():
            add_cap(item, price * SELL_RATIO, f"Casino Rocket {shop} sells it for {price}")
    emerald = value["minecraft:emerald"]
    for item, per_emerald in ext_cfg["villager_sells_per_emerald"].items():
        add_cap(item, emerald / per_emerald, f"villagers sell {per_emerald} for 1 emerald ({emerald})")
    for cat in shops_cfg["categories"]:
        for o in cat["offers"]:
            if "price" in o:
                add_cap(o["item"], o["price"] * SELL_RATIO, f"our shop sells it for {o['price']}")

    # Recipes.
    recipes, skipped = [], defaultdict(int)
    for rid, d in data.recipes.items():
        if not data.conditions_ok(d):
            continue
        p = parse_recipe(data, d)
        if p is None:
            skipped[d.get("type", "?")] += 1
            continue
        recipes.append((rid, *p))
    groups = []  # chipped: anything in a group turns into anything else in it
    for rid, d in data.recipes.items():
        if d.get("type") == "chipped:workbench" and data.conditions_ok(d):
            for ing in d.get("ingredients", []):
                g = ingredient(data, ing)
                if g and len(g) > 1:
                    groups.append(sorted(g))

    def input_cost(inputs):
        total = 0
        for alts, qty in inputs:
            if not alts:
                return INF
            best = min(value[a] - (value[REMAINDERS[a]] if a in REMAINDERS and value[REMAINDERS[a]] < INF else 0)
                       for a in alts)
            total += best * qty
        return total

    # Fixpoint: lower values until no recipe, cap or chipped group can lower them any more.
    # A cap only lowers a value, it never gives an item without a value one.
    why = {}
    for _ in range(100):
        changed = False
        for item, (cap, reason) in caps.items():
            if cap < value[item] < INF:
                value[item], why[item], changed = cap, reason, True
        for rid, inputs, outputs in recipes:
            if len(outputs) != 1:
                continue
            out, count = outputs[0]
            cost = input_cost(inputs)
            if cost < INF:
                v = max(0, math.floor(cost / count))
                if v < value[out]:
                    value[out], why[out], changed = v, rid, True
        for g in groups:
            lo = min(value[i] for i in g)
            for i in g:
                if lo < value[i]:
                    value[i], why[i], changed = lo, "chipped workbench", True
        if not changed:
            break
    else:
        errors.append("values did not settle after 100 rounds")

    # Bank: items with a bank category, a value >= 1, not on the never-sell list.
    bank = {}
    for item, cat in category.items():
        if any(m(item) for m in never):
            continue
        v = value[item]
        if v == INF:
            warnings.append(f"bank: no value for {item} (no rule value and no usable recipe)")
        elif v >= 1:
            bank[item] = v

    # Shop.
    shop_out = []
    for cat in shops_cfg["categories"]:
        offers = []
        for o in cat["offers"]:
            item = o["item"]
            if item not in data.items:
                errors.append(f"shops.json: unknown item {item}")
                continue
            price = o.get("price")
            if price is None:
                v = value[item]
                price = nice(max(BUY_MARKUP * v, o.get("min_price", 0))) if v < INF else 0
                if price < 1 or v < 1 and "min_price" not in o:
                    errors.append(f"shops.json: {item} has no price and no value")
                    continue
            offers.append({"item": item, "price": str(price)})
            if item in bank and bank[item] > price * SELL_RATIO:
                errors.append(f"{item}: sells for {bank[item]} but the shop sells it for {price}")
        shop_out.append({"name": cat["name"], "offers": offers})
    villager_buys = set(ext_cfg["villager_buys"])
    for cat in shop_out:
        for o in cat["offers"]:
            if o["item"] in villager_buys and int(o["price"]) < bank.get("minecraft:emerald", 0):
                errors.append(f"{o['item']}: shop price {o['price']} < emerald {bank['minecraft:emerald']} "
                              "(cured villagers trade 1 for 1 emerald)")

    # Check every recipe: what you can sell the outputs for <= what the inputs are worth.
    unpriced_inputs = defaultdict(set)
    for rid, inputs, outputs in recipes:
        gain = sum(bank.get(o, 0) * c for o, c in outputs)
        if gain == 0:
            continue
        cost = input_cost(inputs)
        if cost == INF:
            for alts, _ in inputs:
                for a in alts or ():
                    if value[a] == INF and not any(m(a) for m in ignore_unpriced):
                        unpriced_inputs[a].add(rid)
        elif gain > cost + 1e-9:
            errors.append(f"recipe {rid}: outputs sell for {gain} > inputs worth {cost:g}")
    for item in bank:
        if item in caps and bank[item] > caps[item][0]:
            errors.append(f"{item}: sells for {bank[item]} but {caps[item][1]}")

    # Gachapons.
    gacha = gacha_check(args.server, ext_cfg, bank, errors)

    # Item ids must exist.
    for item in bank:
        if item not in data.items:
            errors.append(f"bank: unknown item {item}")

    # ------------------------------------------------------------ report
    order = values_cfg["bank_categories"]
    for c in set(category[i] for i in bank) - set(order):
        errors.append(f"bank category {c!r} missing from bank_categories")
    bank_sorted = sorted(bank, key=lambda i: (order.index(category[i]) if category[i] in order else 99, i))
    print(f"Recipes: {len(recipes)} used, skipped types: {dict(sorted(skipped.items(), key=lambda x: -x[1]))}")
    print(f"Bank: {len(bank)} items   Shop: {sum(len(c['offers']) for c in shop_out)} offers in {len(shop_out)} tabs")
    for c in order:
        items = sorted((i for i in bank if category[i] == c), key=lambda i: -bank[i])
        if items:
            top = ", ".join(f"{i.split(':')[1]} {bank[i]}" for i in items[:12])
            print(f"  {c} ({len(items)}): {top}")
    for line in gacha:
        print(line)
    for item in args.explain:
        print(f"explain {item}: value {value[item]}, sell {bank.get(item, '-')}, "
              f"cap {caps.get(item)}, lowered by {why.get(item, '-')}, rule {rule_for(item)}")
    if unpriced_inputs:
        print(f"Unpriced recipe inputs for sellable items ({len(unpriced_inputs)}), check they aren't free:")
        print("  " + ", ".join(sorted(unpriced_inputs)))
    for w in sorted(set(warnings)):
        print("warning:", w)
    for e in errors:
        print("ERROR:", e)
    if errors:
        print(f"{len(errors)} errors, nothing written.")
        return 1

    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "default_bank.json").write_text(
            json.dumps([{"item": i, "price": str(bank[i])} for i in bank_sorted], indent=2) + "\n")
        (OUT_DIR / "default_shop.json").write_text(json.dumps(shop_out, indent=2, ensure_ascii=False) + "\n")
        (OUT_DIR / "common.json").write_text(json.dumps(values_cfg["common"], indent=2) + "\n")
        print(f"Written to {OUT_DIR.relative_to(REPO_ROOT)}/")
    return 0


def gacha_check(server, ext_cfg, bank, errors):
    """Expected sell value of one gacha pull vs. its price, per coin/capsule type."""
    cfg_dir = server / "config" / "casinorocket"
    try:
        machines = json.loads((cfg_dir / "gacha_machines.json").read_text())
        pools = json.loads((cfg_dir / "item_gachapon.json").read_text())["pools"]
    except (OSError, ValueError, KeyError) as e:
        errors.append(f"gacha: can't read Casino Rocket config: {e}")
        return []
    pool_ev, top = {}, {}
    for rarity, entries in pools.items():
        total = sum(e.get("weight", 0) for e in entries)
        parts = {e.get("itemId"): e.get("weight", 0) / total * e.get("count", 1) * bank.get(e.get("itemId"), 0)
                 for e in entries} if total else {}
        pool_ev[rarity] = sum(parts.values())
        top[rarity] = sorted(parts.items(), key=lambda x: -x[1])[:3]
    base = machines["rarity_base_weights"]
    lines = []
    for kind, price_key in ext_cfg["gacha_prices"].items():
        coin = kind.split(":")[0]
        mult = machines["coin_multipliers"][coin]
        w = {r: base[r] * mult.get(r, 1) for r in base}
        total = sum(w.values())
        p = {r: w[r] / total for r in w}
        pity = machines.get("pity", {}).get(coin, {})
        if pity.get("usesToMax"):  # worst case: pity maxed out
            leg = max(p["legendary"], pity.get("maxLegendaryChance", 0))
            rest = (1 - leg) / (1 - p["legendary"])
            p = {r: (leg if r == "legendary" else p[r] * rest) for r in p}
        ev = sum(p[r] * pool_ev.get(r, 0) for r in p)
        bonus = machines.get("premier_bonus", {})
        if bonus.get("enable"):
            ev += pool_ev.get("bonus", 0) / bonus.get("coinsToBonus", 10)
        price = dig(machines["gacha_store"], price_key)
        biggest = max(p, key=lambda r: p[r] * pool_ev.get(r, 0))
        lines.append(f"Gacha {kind}: expected sell value {ev:.0f} for price {price} (mostly {biggest}: "
                     + ", ".join(f"{i.split(':')[1]} {v:.0f}" for i, v in top.get(biggest, [])) + ")")
        if ev > GACHA_RATIO * price:
            errors.append(f"gacha {kind}: expected sell value {ev:.0f} > {GACHA_RATIO:.0%} of {price}")
    return lines


def dig(d, path):
    for k in path.split("."):
        d = d[k]
    return d


if __name__ == "__main__":
    sys.exit(main())
