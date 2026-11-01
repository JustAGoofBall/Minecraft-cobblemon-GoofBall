# The Ender Dragon is gone on this server (MobsBeGone), so the End never got finished:
# no active exit portal and no gateways to the outer islands. Run this ONCE as an op: /function goofball:end_open
# It loads the needed chunks, waits, then goofball:end_do places everything. Safe to run twice (flag #end).
scoreboard objectives add goofball dummy
execute if score #end goofball matches 1 run return 0
execute in minecraft:the_end run forceload add -24 -24 24 40
execute in minecraft:the_end run forceload add 96 0
execute in minecraft:the_end run forceload add 91 29
execute in minecraft:the_end run forceload add 77 56
execute in minecraft:the_end run forceload add 56 77
execute in minecraft:the_end run forceload add 29 91
execute in minecraft:the_end run forceload add 0 96
execute in minecraft:the_end run forceload add -30 91
execute in minecraft:the_end run forceload add -57 77
execute in minecraft:the_end run forceload add -78 56
execute in minecraft:the_end run forceload add -92 29
execute in minecraft:the_end run forceload add -96 0
execute in minecraft:the_end run forceload add -92 -30
execute in minecraft:the_end run forceload add -78 -57
execute in minecraft:the_end run forceload add -57 -78
execute in minecraft:the_end run forceload add -30 -92
execute in minecraft:the_end run forceload add -1 -96
execute in minecraft:the_end run forceload add 29 -92
execute in minecraft:the_end run forceload add 56 -78
execute in minecraft:the_end run forceload add 77 -57
execute in minecraft:the_end run forceload add 91 -30
schedule function goofball:end_do 100t replace
tellraw @a {"text":"[GoofBall] Het End wordt geopend...","color":"gold"}
