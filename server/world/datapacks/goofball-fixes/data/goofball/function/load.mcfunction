# No vanilla mobs: Pokémon, Cobblemon NPCs/trainers and villagers only.
# doMobSpawning off stops all natural spawning (also phantoms, patrols, wandering traders, cats).
# Cobblemon has its own rule (doPokemonSpawning), spawner blocks keep working.
gamerule doMobSpawning false
gamerule doPatrolSpawning false
gamerule doTraderSpawning false
gamerule doInsomnia false
schedule function goofball:remove_vanilla_mobs 100t replace
