@echo off
rem Start de server zonder Crafty (Windows). Crafty gebruikt dit bestand niet.
cd /d "%~dp0"
java -Xms6G -Xmx6G -jar fabric-server-launch.jar nogui
pause
