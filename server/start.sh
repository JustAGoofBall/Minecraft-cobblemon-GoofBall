#!/usr/bin/env sh
# Start the server without Crafty (Linux/macOS). Crafty does not use this file.
# goofball-server.jar downloads/updates the mods, then starts Fabric.
# Use a different amount of memory: MEMORY=10G ./start.sh
cd "$(dirname "$0")" || exit 1
MEMORY="${MEMORY:-8G}"
# Aikar's G1GC flags (https://mcflags.emc.gs): fewer lag spikes from garbage collection.
exec java -Xms"$MEMORY" -Xmx"$MEMORY" -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Daikars.new.flags=true -Dusing.aikars.flags=https://mcflags.emc.gs -jar goofball-server.jar nogui
