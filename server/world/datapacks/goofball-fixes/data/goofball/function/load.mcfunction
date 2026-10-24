# No vanilla mobs: Pokémon, Cobblemon NPCs/trainers and villagers only.
# doMobSpawning off stops all natural spawning (also phantoms, patrols, wandering traders, cats).
# Cobblemon has its own rule (doPokemonSpawning), spawner blocks keep working.
gamerule doMobSpawning false
gamerule doPatrolSpawning false
gamerule doTraderSpawning false
gamerule doInsomnia false
# Performance: spawn chunks only tick when a player is near (vanilla keeps them loaded forever).
gamerule spawnChunkRadius 0
# Keep inventory stays off: the Gravestones mod stores your items in a grave when you die
# (it places no grave while keepInventory is on).
gamerule keepInventory false
schedule function goofball:remove_vanilla_mobs 100t replace
schedule function goofball:arena_place 200t replace
