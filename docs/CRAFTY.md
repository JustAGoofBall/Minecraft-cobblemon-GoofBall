# Running the server on Crafty Controller

You need one file: **`GoofBall-Cobblemon-Server-<version>.zip`** (about 0.2 MB).
Download it from the latest [Release](https://github.com/JustAGoofBall/Minecraft-cobblemon-GoofBall/releases/latest)
(under *Assets*).

| File | What it is |
|---|---|
| `goofball-server.jar` | **The jar Crafty starts.** On every start it downloads/updates the mods from Modrinth (each file is hash-checked), then starts the Fabric server. |
| `fabric-server-launch.jar` | Fabric's server launcher for Minecraft 1.21.1. Downloads Minecraft + Fabric on the first start. |
| `server.properties` | Default settings (difficulty, view distance, MOTD). |
| `start.sh` / `start.bat` | Only needed if you run the server **without** Crafty. |

The mods are not inside the zip: many mod authors don't allow re-uploading their files. The launcher
downloads them from Modrinth, just like the players' launchers do.

## Requirements
- **Java 21**. If Crafty runs in Docker, the official Crafty image already has Java 21. If Crafty runs
  directly on Linux/Windows, install Java 21 (for example `openjdk-21-jre-headless` or
  [Adoptium Temurin 21](https://adoptium.net)).
- **RAM:** at least **8 GB** for the server, **10 GB** recommended with 5+ players.
- **Internet access** to `cdn.modrinth.com`, `meta.fabricmc.net` and Mojang's servers (for the first
  download and for updates).
- **Disk:** about 1 GB for the server files, plus the world.
- **Ports:**
  - `25565` **TCP**: Minecraft (or the port you choose in Crafty).
  - `24454` **UDP**: Simple Voice Chat. Without it everything works except voice chat.

## First install
1. Log in to Crafty and click **Create New Server** (➕).
2. Choose **Minecraft Java** and the option to **import/upload a zip file**
   (*Import Server* → *Upload Zip*).
3. Upload `GoofBall-Cobblemon-Server-<version>.zip`.
   - If Crafty asks for the server folder inside the zip, pick the **top folder** (the files are
     directly in the zip, not in a subfolder).
4. Fill in:
   - **Server name:** e.g. `GoofBall Cobblemon`
   - **Server JAR / executable:** `goofball-server.jar`
   - **Min memory:** `8` GB, **Max memory:** `8` GB (or 10/10)
   - **Port:** `25565` (or any free port)
5. Click **Import Server** / **Create**.
6. Open the server and go to **Config**:
   - Set the **Server Execution Command** to (change `8G` if you picked a different amount):
     ```
     java -Xms8G -Xmx8G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Daikars.new.flags=true -Dusing.aikars.flags=https://mcflags.emc.gs -jar goofball-server.jar nogui
     ```
     These are [Aikar's flags](https://mcflags.emc.gs): they reduce lag spikes from Java's garbage
     collector. A plain `java -Xms8G -Xmx8G -jar goofball-server.jar nogui` also works.
   - If your Crafty version has a **Java** option, pick a **Java 21** installation.
   - Save.
7. Click **Start**. Crafty asks whether you accept the
   [Minecraft EULA](https://aka.ms/MinecraftEULA): **Yes**.
8. The first start takes a few minutes. You'll see `[GoofBall] Downloading … files from Modrinth`,
   then Minecraft/Fabric downloading, then Cobblemon loading 1000+ Pokémon. The server is ready when
   the **Terminal** shows:
   `Done (…)! For help, type "help"`
9. Make yourself an operator in the Terminal: `op <your-minecraft-name>`

### Pre-generate the world (strongly recommended)
Generating new terrain (Terralith + Tectonic + all the structure mods) is the heaviest thing the
server does. Generate the area around spawn before players explore, when nobody is online:
```
chunky radius 3000
chunky start
```
This takes a while (watch the progress in the Terminal). `chunky pause` / `chunky continue` work too.

### Docker: extra UDP port for voice chat
The default Crafty `docker-compose.yml` usually only opens TCP ports. Add a UDP port for voice chat
and restart the container:

```yaml
    ports:
      - "8443:8443"
      - "25565:25565"
      - "24454:24454/udp"   # Simple Voice Chat
```

If you run several servers or need another port, change `port=` in
`config/voicechat/voicechat-server.properties` (**Files** tab, after the first start).

## Updating to a new pack version
1. **Backup:** **Backups** tab → create a backup.
2. **Stop** the server.
3. In **Files**, upload `goofball-server.jar` from the new zip and overwrite the old one.
4. **Start** the server. The launcher removes mods that were dropped from the pack, downloads
   new/updated ones, and leaves your world, configs and any mods you added yourself alone.

Then make sure the players also use the new `.mrpack` (see [PLAYERS.md](PLAYERS.md)).

### Upgrading from 1.x to 2.0
Version 2.0 changes world generation (Terralith + Tectonic + many structures), so **start a new world**.
Old chunks keep the old terrain and you'd get ugly borders. Also delete the old `mods` folder once
(the 1.x mods weren't installed by the launcher, so it can't clean them up).

## Handy commands (in the Crafty Terminal)
| Command | What it does |
|---|---|
| `op <name>` | Make a player an operator |
| `whitelist on` / `whitelist add <name>` | Only allow your friends |
| `chunky radius 3000` then `chunky start` | Pre-generate the world around spawn |
| `spark tps` / `spark profiler start` | Find the cause of lag |

## Server performance mods (already included)
Lithium, FerriteCore, ModernFix, Krypton, ScalableLux, Noisium, ServerCore, Alternate Current,
Structure Layout Optimizer, Clumps, plus Chunky (pre-generation) and spark (profiling).
`server.properties` uses view-distance 8 and simulation-distance 6. You can raise these if your CPU
has room (check `spark tps`: it should stay at 20).

## Troubleshooting
- **`[GoofBall] ERROR: could not download …`**: the server can't reach `cdn.modrinth.com`. Check its
  internet/DNS and start again. To start once without checking mods, add `-Dgoofball.skipSync=true`
  before `-jar` in the execution command.
- **"Unsupported class file major version" / Java error**: the server isn't running on Java 21.
- **`OutOfMemoryError`**: raise the memory (both `-Xms` and `-Xmx`) in the execution command.
- **Player gets "mod rejections" / "mismatched mod"**: the player's pack version differs from the server's.
- **Voice chat doesn't work**: UDP port 24454 isn't open (router, firewall or Docker).
