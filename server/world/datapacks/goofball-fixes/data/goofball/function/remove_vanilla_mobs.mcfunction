# Mobs that were already there (or spawn with new chunks) are dropped into the void every 5 seconds,
# so they leave no drops. Not in the list: mobs from spawner blocks (zombie, skeleton, spider, blaze,
# ...: they despawn by themselves), villagers, golems, bosses. Tag a mob goofball_keep to keep it.
execute as @e[type=#goofball:removed_mobs,tag=!goofball_keep] at @s run tp @s ~ -400 ~
schedule function goofball:remove_vanilla_mobs 100t replace
