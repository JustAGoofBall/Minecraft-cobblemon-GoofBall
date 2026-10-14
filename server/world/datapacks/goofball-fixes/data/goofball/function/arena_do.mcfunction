execute if score #arena goofball matches 1 run return 0
execute in minecraft:overworld positioned 0 0 0 positioned over motion_blocking_no_leaves run place template goofball:arena ~-22 ~-4 ~-22
execute in minecraft:overworld positioned 0 0 0 positioned over motion_blocking_no_leaves run setworldspawn ~ ~ ~-26
scoreboard players set #arena goofball 1
forceload remove -32 -32 32 32
tellraw @a {"text":"[GoofBall] De battle arena is geplaatst bij spawn.","color":"gold"}
