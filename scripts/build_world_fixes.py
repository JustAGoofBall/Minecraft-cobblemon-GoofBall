#!/usr/bin/env python3
"""Generate worldgen / loot fixes and the spawn arena for the goofball-fixes datapack.

Reads the mod jars of a server dir (read-only) and writes into
server/world/datapacks/goofball-fixes/. Re-run after a mod update:

  python3 -I scripts/build_world_fixes.py /srv/minecraft/servers/<id>

What it does
  1. Legendary Monuments dojo-tower loot tables: replaces item ids that do not exist in
     Cobblemon 1.8.1 (black/blue_apricorn_sprout -> *_seed, tomato_berry -> tamato_berry) and
     points the three reward tables at chests/tower_vault* (the original path is missing).
  2. Caps the spacing of far-away legendary structures (Legendary Monuments, Pokémon Stadium)
     so each one exists inside a normal pregenerated area.
  3. Radical Gyms Structures: widens the biome tags so Terralith biomes count (the mod lists
     only vanilla biome ids, so most gyms were extremely rare).
  4. Pokémon Stadium biomes: land biome tags instead of an explicit vanilla list.
  5. A battle arena (structure NBT) that is placed once at world spawn by a function.
"""
import gzip
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DP = REPO / "server/world/datapacks/goofball-fixes"
MAX_SPACING = 150      # chunks (16 blocks); 150 -> ~99 % chance that a 4000x4000 area has one
MAX_SEPARATION = 100

LM_JAR = "legendarymonuments-fabric-1.21.1-8.2-Keep-Fighting.jar"
OPP_JAR = "cobblemonopponents-fabric-1.8.0.jar"

ITEM_FIXES = {
    "cobblemon:black_apricorn_sprout": "cobblemon:black_apricorn_seed",
    "cobblemon:blue_apricorn_sprout": "cobblemon:blue_apricorn_seed",
    "cobblemon:tomato_berry": "cobblemon:tamato_berry",
}
LM_LOOT = [
    "chests/tower_spawner_dark", "chests/tower_spawner_water",
    "spawners/dojo/dark_tower_spawner", "spawners/dojo/water_tower_spawner",
]
# reward tables whose "dojo_towers_vaults/tower_reward" reference does not exist
LM_VAULT_REFS = {
    "chests/dojo_towers/water_tower_reward": "chests/tower_vault_water",
    "chests/dojo_towers/dark_tower_reward": "chests/tower_vault_dark",
    "npc_rewards/mustard_rewards": "chests/tower_vault",
}

RGS_BIOMES = {  # only overworld gyms; blackthorn/kanto_league (End) and cinnabar (Nether) stay
    "celadon_gym": ["#minecraft:is_forest"],
    "cerulean_gym": ["#minecraft:is_beach", "minecraft:swamp", "minecraft:mangrove_swamp",
                     "minecraft:stony_shore", "minecraft:lukewarm_ocean", "minecraft:warm_ocean"],
    "fuchsia_gym": ["#minecraft:is_jungle"],
    "pewter_gym": ["#minecraft:is_mountain", "#minecraft:is_hill"],
    "saffron_gym": ["minecraft:dark_forest", "minecraft:cherry_grove", "#minecraft:is_taiga"],
    "vermilion_gym": ["#minecraft:is_badlands", "#minecraft:is_savanna"],
}
STADIUM_BIOMES = ["#minecraft:is_forest", "#minecraft:is_taiga", "#minecraft:is_jungle",
                  "#minecraft:is_badlands", "#minecraft:is_savanna", "#minecraft:is_mountain",
                  "#minecraft:is_hill", "#cobblemon:is_plains", "#cobblemon:is_desert"]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def fix_items(node):
    if isinstance(node, dict):
        return {k: (ITEM_FIXES.get(v, v) if k == "name" and isinstance(v, str) else fix_items(v))
                for k, v in node.items()}
    if isinstance(node, list):
        return [fix_items(v) for v in node]
    return node


def build_loot(lm):
    for t in LM_LOOT:
        d = fix_items(json.loads(lm.read(f"data/legendarymonuments/loot_table/{t}.json")))
        write_json(DP / f"data/legendarymonuments/loot_table/{t}.json", d)
    for t, target in LM_VAULT_REFS.items():
        raw = lm.read(f"data/legendarymonuments/loot_table/{t}.json").decode()
        raw = raw.replace("legendarymonuments:chests/dojo_towers_vaults/tower_reward",
                          f"legendarymonuments:{target}")
        write_json(DP / f"data/legendarymonuments/loot_table/{t}.json", json.loads(raw))


def build_spacing(jar, ns, only=None):
    done = []
    for n in sorted(jar.namelist()):
        m = re.match(rf"data/{ns}/worldgen/structure_set/(.+)\.json$", n)
        if not m or (only and m.group(1) not in only):
            continue
        d = json.loads(jar.read(n))
        p = d["placement"]
        if p.get("spacing", 0) > MAX_SPACING:
            old = (p["spacing"], p["separation"])
            p["spacing"] = MAX_SPACING
            p["separation"] = min(p["separation"], MAX_SEPARATION)
            write_json(DP / f"data/{ns}/worldgen/structure_set/{m.group(1)}.json", d)
            done.append((m.group(1), old, (p["spacing"], p["separation"])))
    return done


def build_biomes(opp):
    for name, biomes in RGS_BIOMES.items():
        write_json(DP / f"data/rgs/tags/worldgen/biome/{name}.json",
                   {"replace": True, "values": biomes})
    for n in sorted(opp.namelist()):
        m = re.match(r"data/([^/]+)/worldgen/structure/(pokemon_stadium_.+)\.json$", n)
        if m:
            d = json.loads(opp.read(n))
            # a HolderSet is either one "#tag" or a list of plain ids: tags in a list are invalid
            d["biomes"] = "#cobblemonopponents:pokemon_stadium_biomes"
            write_json(DP / f"data/{m.group(1)}/worldgen/structure/{m.group(2)}.json", d)
    write_json(DP / "data/cobblemonopponents/tags/worldgen/biome/pokemon_stadium_biomes.json",
               {"values": STADIUM_BIOMES})


# ---------------------------------------------------------------- arena (structure NBT)
class NBT:
    @staticmethod
    def string(s):
        b = s.encode()
        return struct.pack(">H", len(b)) + b

    @classmethod
    def named(cls, tag_id, name, payload):
        return bytes([tag_id]) + cls.string(name) + payload

    @classmethod
    def int_(cls, v):
        return struct.pack(">i", v)

    @classmethod
    def list_(cls, elem_id, items):
        return bytes([elem_id]) + struct.pack(">i", len(items)) + b"".join(items)

    @classmethod
    def compound(cls, fields):  # fields: list of (tag_id, name, payload)
        return b"".join(cls.named(t, n, p) for t, n, p in fields) + b"\x00"


def arena_blocks():
    """Return (size, {(x,y,z): (name, props)}). Origin corner; floor level is y=4."""
    X, Z, H, F = 45, 45, 11, 4
    b = {}

    def put(x, y, z, name, **props):
        b[(x, y, z)] = (name, props)

    for x in range(X):
        for z in range(Z):
            for y in range(F):
                put(x, y, z, "minecraft:stone_bricks")
            put(x, F, z, "minecraft:polished_andesite")
    # border trim
    for i in range(X):
        for (x, z) in ((i, 0), (i, Z - 1), (0, i), (X - 1, i)):
            put(x, F, z, "minecraft:polished_deepslate")
    # battlefield 15 x 25, checkerboard
    fx0, fx1, fz0, fz1 = 15, 29, 10, 34
    for x in range(fx0, fx1 + 1):
        for z in range(fz0, fz1 + 1):
            put(x, F, z, "minecraft:white_concrete" if (x + z) % 2 == 0
                else "minecraft:light_gray_concrete")
    for x in range(fx0, fx1 + 1):          # center line
        put(x, F, 22, "minecraft:black_concrete")
    for x in range(21, 24):                # trainer boxes
        for z in range(12, 15):
            put(x, F, z, "minecraft:blue_concrete")
        for z in range(30, 33):
            put(x, F, z, "minecraft:red_concrete")
    # low wall around the field
    for x in range(fx0 - 1, fx1 + 2):
        for z in (fz0 - 1, fz1 + 1):
            put(x, F + 1, z, "minecraft:polished_blackstone_brick_wall")
    for z in range(fz0 - 1, fz1 + 2):
        for x in (fx0 - 1, fx1 + 1):
            put(x, F + 1, z, "minecraft:polished_blackstone_brick_wall")
    # stands on both long sides: 3 rows of stairs rising outward
    for row in range(3):
        for z in range(fz0 - 1, fz1 + 2):
            for dx in range(3 - row):  # fill below the stair so it is solid
                pass
            wx = fx0 - 3 - row         # west side: 11, 10, 9
            ex = fx1 + 3 + row         # east side: 33, 34, 35
            for y in range(F + 1, F + 1 + row):
                put(wx, y, z, "minecraft:polished_andesite")
                put(ex, y, z, "minecraft:polished_andesite")
            put(wx, F + 1 + row, z, "minecraft:quartz_stairs", facing="east", half="bottom",
                shape="straight")
            put(ex, F + 1 + row, z, "minecraft:quartz_stairs", facing="west", half="bottom",
                shape="straight")
    # corner pillars with lights
    for x in (8, 36):
        for z in (7, 37):
            for y in range(F + 1, F + 6):
                put(x, y, z, "minecraft:quartz_pillar", axis="y")
            put(x, F + 6, z, "minecraft:sea_lantern")
    # healing machines and PCs on both ends (natural=true: they do not drop when broken)
    for z, face in ((4, "south"), (40, "north")):
        for x in (19, 25):
            put(x, F + 1, z, "cobblemon:healing_machine", facing=face, natural="true", charge="0")
        put(22, F + 1, z, "cobblemon:pc", facing=face, part="bottom", on="false", natural="true")
        put(22, F + 2, z, "cobblemon:pc", facing=face, part="top", on="false", natural="true")
        for x in range(17, 28):            # planter strip under them
            put(x, F, z, "minecraft:polished_deepslate")
    return (X, H, Z), b


def write_arena():
    size, blocks = arena_blocks()
    palette, index = [], {}
    for _, st in blocks.items():
        key = (st[0], tuple(sorted(st[1].items())))
        if key not in index:
            index[key] = len(palette)
            props = [(8, k, NBT.string(v)) for k, v in sorted(st[1].items())]
            fields = [(8, "Name", NBT.string(st[0]))]
            if props:
                fields.append((10, "Properties", NBT.compound(props)))
            palette.append(NBT.compound(fields))
    blk = []
    for (x, y, z), st in sorted(blocks.items()):
        key = (st[0], tuple(sorted(st[1].items())))
        blk.append(NBT.compound([
            (3, "state", NBT.int_(index[key])),
            (9, "pos", NBT.list_(3, [NBT.int_(x), NBT.int_(y), NBT.int_(z)]))]))
    root = NBT.compound([
        (3, "DataVersion", NBT.int_(3955)),
        (9, "size", NBT.list_(3, [NBT.int_(s) for s in size])),
        (9, "palette", NBT.list_(10, palette)),
        (9, "blocks", NBT.list_(10, blk)),
        (9, "entities", NBT.list_(0, []))])
    out = DP / "data/goofball/structure/arena.nbt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(gzip.compress(NBT.named(10, "", root), mtime=0))
    return size, len(blocks), len(palette)


FUNCTIONS = {
    "arena_place.mcfunction": """# Place the battle arena once, at the world spawn area (0,0). Needs the chunks loaded.
scoreboard objectives add goofball dummy
execute if score #arena goofball matches 1 run return 0
forceload add -32 -32 32 32
schedule function goofball:arena_do 100t replace
""",
    "arena_do.mcfunction": """execute if score #arena goofball matches 1 run return 0
execute in minecraft:overworld positioned 0 0 0 positioned over motion_blocking_no_leaves run place template goofball:arena ~-22 ~-4 ~-22
execute in minecraft:overworld positioned 0 0 0 positioned over motion_blocking_no_leaves run setworldspawn ~ ~ ~-26
scoreboard players set #arena goofball 1
forceload remove -32 -32 32 32
tellraw @a {"text":"[GoofBall] De battle arena is geplaatst bij spawn.","color":"gold"}
""",
}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    mods = Path(sys.argv[1]) / "mods"
    lm = zipfile.ZipFile(mods / LM_JAR)
    opp = zipfile.ZipFile(mods / OPP_JAR)
    build_loot(lm)
    changed = build_spacing(lm, "legendarymonuments")
    changed += build_spacing(opp, "cobblemonopponents", only={"pokemon_stadium"})
    build_biomes(opp)
    size, nblocks, npal = write_arena()
    for name, text in FUNCTIONS.items():
        (DP / "data/goofball/function" / name).write_text(text)
    load = DP / "data/goofball/function/load.mcfunction"
    t = load.read_text()
    if "arena_place" not in t:
        load.write_text(t.rstrip("\n") + "\nschedule function goofball:arena_place 200t replace\n")
    for n, old, new in changed:
        print(f"spacing {n}: {old} -> {new}")
    print(f"arena {size}, {nblocks} blocks, palette {npal}")


if __name__ == "__main__":
    main()
