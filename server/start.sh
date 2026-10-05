#!/usr/bin/env sh
# Start de server zonder Crafty (Linux/macOS). Crafty gebruikt dit bestand niet.
# Ander geheugen gebruiken: MEMORY=8G ./start.sh
cd "$(dirname "$0")" || exit 1
MEMORY="${MEMORY:-6G}"
exec java -Xms"$MEMORY" -Xmx"$MEMORY" -jar fabric-server-launch.jar nogui
