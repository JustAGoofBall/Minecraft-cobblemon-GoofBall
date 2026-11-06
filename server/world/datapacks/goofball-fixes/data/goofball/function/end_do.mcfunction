# Second half of goofball:end_open (the chunks are loaded now).
execute if score #end goofball matches 1 run return 0
# Exit portal: the 20 air blocks inside the bedrock ring at y=58 (centre pillar and corners are bedrock and stay).
execute in minecraft:the_end run fill -2 58 -2 2 58 2 minecraft:end_portal replace minecraft:air
# The 20 vanilla gateway positions (radius 96, y 75). Better End Island places its own gateway design.
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed 96 75 0
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed 91 75 29
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed 77 75 56
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed 56 75 77
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed 29 75 91
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed 0 75 96
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed -30 75 91
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed -57 75 77
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed -78 75 56
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed -92 75 29
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed -96 75 0
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed -92 75 -30
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed -78 75 -57
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed -57 75 -78
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed -30 75 -92
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed -1 75 -96
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed 29 75 -92
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed 56 75 -78
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed 77 75 -57
execute in minecraft:the_end run place feature minecraft:end_gateway_delayed 91 75 -30
scoreboard players set #end goofball 1
execute in minecraft:the_end run forceload remove -24 -24 24 40
execute in minecraft:the_end run forceload remove 96 0
execute in minecraft:the_end run forceload remove 91 29
execute in minecraft:the_end run forceload remove 77 56
execute in minecraft:the_end run forceload remove 56 77
execute in minecraft:the_end run forceload remove 29 91
execute in minecraft:the_end run forceload remove 0 96
execute in minecraft:the_end run forceload remove -30 91
execute in minecraft:the_end run forceload remove -57 77
execute in minecraft:the_end run forceload remove -78 56
execute in minecraft:the_end run forceload remove -92 29
execute in minecraft:the_end run forceload remove -96 0
execute in minecraft:the_end run forceload remove -92 -30
execute in minecraft:the_end run forceload remove -78 -57
execute in minecraft:the_end run forceload remove -57 -78
execute in minecraft:the_end run forceload remove -30 -92
execute in minecraft:the_end run forceload remove -1 -96
execute in minecraft:the_end run forceload remove 29 -92
execute in minecraft:the_end run forceload remove 56 -78
execute in minecraft:the_end run forceload remove 77 -57
execute in minecraft:the_end run forceload remove 91 -30
tellraw @a {"text":"[GoofBall] Het End is open: het uitgangsportaal werkt en de gateways staan.","color":"gold"}
