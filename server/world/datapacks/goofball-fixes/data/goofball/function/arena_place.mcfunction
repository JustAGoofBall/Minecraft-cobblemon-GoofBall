# Place the battle arena once, at the world spawn area (0,0). Needs the chunks loaded.
scoreboard objectives add goofball dummy
execute if score #arena goofball matches 1 run return 0
forceload add -32 -32 32 32
schedule function goofball:arena_do 100t replace
