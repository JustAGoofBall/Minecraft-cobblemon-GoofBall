#!/usr/bin/env python3
"""Generate the Cobblemon Pokestops loot-table overrides (goofball-fixes datapack).

Each stop gives 1-2 items from a weighted common pool, plus small independent
chances (random_chance) at a TM and at a mega stone. Mega stones are on the
economy never_sell list and TMs are not in the bank, so none of it can be sold.
"""
import json, pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / (
    "server/world/datapacks/goofball-fixes/data/cobblemon_pokestops/loot_table/gameplay")

TMS = """flamethrower thunderbolt icebeam earthquake psychic shadowball surf hydropump
energyball darkpulse dragonpulse closecombat flashcannon focusblast bugbuzz airslash
gigadrain calmmind swordsdance bulkup dragondance protect substitute roost thunderwave
willowisp stealthrock toxic uturn voltswitch icepunch firepunch thunderpunch scald
waterfall crunch xscissor stoneedge rockslide ironhead outrage sludgebomb poisonjab
aurasphere hypervoice playrough knockoff taunt trickroom""".split()

MEGA = """abomasite absolite aerodactylite aggronite alakazite altarianite ampharosite
audinite banettite beedrillite blastoisinite blazikenite cameruptite charizardite_x
charizardite_y diancite galladite garchompite gardevoirite gengarite glalitite
gyaradosite heracronite houndoominite kangaskhanite latiasite latiosite lopunnite
lucarionite manectite mawilite medichamite metagrossite mewtwonite_x mewtwonite_y
pidgeotite pinsirite sableye_placeholder salamencite sceptilite scizorite sharpedonite
slowbronite steelixite swampertite tyranitarite venusaurite""".split()
MEGA = [m for m in MEGA if "placeholder" not in m]

def item(name, weight, lo=1, hi=1):
    e = {"type": "minecraft:item", "name": name, "weight": weight}
    if (lo, hi) != (1, 1):
        e["functions"] = [{"function": "minecraft:set_count",
                           "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}]
    return e

def table(common, tm_chance, mega_chance):
    tm_entries = [{"type": "minecraft:item", "name": "cobblemon:technical_machine",
                   "functions": [{"function": "minecraft:set_components",
                                  "components": {"cobblemon:tm_move": {"move": m}}}]}
                  for m in TMS]
    mega_entries = [{"type": "minecraft:item", "name": f"mega_showdown:{m}"} for m in MEGA]
    chance = lambda c: [{"condition": "minecraft:random_chance", "chance": c}]
    return {"type": "minecraft:chest", "pools": [
        {"rolls": 1, "bonus_rolls": 0.6, "entries": common},
        {"rolls": 1, "conditions": chance(tm_chance), "entries": tm_entries},
        {"rolls": 1, "conditions": chance(mega_chance), "entries": mega_entries}]}

C = lambda n: f"cobblemon:{n}"
heals = [item(C(n), 25) for n in ("antidote", "paralyze_heal", "awakening", "burn_heal", "ice_heal")]
berries = [item(C("oran_berry"), 40, 1, 3)] + [item(C(n), 25, 1, 2)
           for n in ("razz_berry", "pinap_berry", "nanab_berry", "pecha_berry", "cheri_berry")]
potions = [item(C("potion"), 50), item(C("super_potion"), 30), item(C("hyper_potion"), 8)]

TABLES = {
    # general stop: balls, medicine, berries, a little candy
    "pokestop_loot": table(
        [item(C("poke_ball"), 50, 1, 3), item(C("great_ball"), 30), item(C("ultra_ball"), 8),
         *potions, *heals, *berries, item(C("revive"), 10), item(C("exp_candy_xs"), 20),
         item(C("pp_up"), 5), item(C("exp_candy_s"), 4)], 0.04, 0.004),
    # winged stop: ancient balls and berries, slightly better TM chance
    "wingedstop_loot": table(
        [item(C("ancient_poke_ball"), 50, 1, 2), item(C("ancient_great_ball"), 25),
         item(C("ancient_ultra_ball"), 8), *potions, *berries, item(C("revive"), 10),
         item(C("exp_candy_xs"), 20), item(C("exp_candy_s"), 4)], 0.06, 0.004),
    # pokeball stop: ball variety (no Master Ball)
    "pokeballstop_loot": table(
        [item(C("poke_ball"), 40, 1, 3),
         *[item(C(n), 25) for n in ("azure_ball", "citrine_ball", "roseate_ball", "verdant_ball")],
         *[item(C(n), 20) for n in ("friend_ball", "dive_ball", "lure_ball", "nest_ball")],
         *[item(C(n), 8) for n in ("heavy_ball", "quick_ball", "dusk_ball", "premier_ball",
                                    "ultra_ball", "timer_ball", "luxury_ball", "level_ball",
                                    "sport_ball", "fast_ball", "park_ball")]], 0.03, 0.003),
}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, t in TABLES.items():
        (OUT / f"{name}.json").write_text(json.dumps(t, indent=2) + "\n")
        print("wrote", name, sum(e.get("weight", 0) for p in t["pools"][:1] for e in p["entries"]))
