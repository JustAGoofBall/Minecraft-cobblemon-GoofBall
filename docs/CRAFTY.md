# Server draaien op Crafty Controller

Je hebt één bestand nodig: **`GoofBall-Cobblemon-Server-<versie>.zip`**.
Download het bij de nieuwste [Release](https://github.com/JustAGoofBall/Minecraft-cobblemon-GoofBall/releases/latest) (onder *Assets*).

In de zip zit alles wat de server nodig heeft:

| Bestand / map | Wat |
|---|---|
| `fabric-server-launch.jar` | De server-jar (Minecraft 1.21.1 + Fabric). Downloadt bij de eerste start zelf de Minecraft-server. |
| `mods/` | Cobblemon + alle server-mods (geen client-mods zoals Sodium of de minimap). |
| `server.properties` | Standaardinstellingen (moeilijkheid, view distance, MOTD). |
| `start.sh` / `start.bat` | Alleen nodig als je de server **zonder** Crafty draait. |

## Wat de server nodig heeft
- **Java 21**. Draait Crafty in Docker? De officiële Crafty-image heeft Java 21 al.
  Draait Crafty direct op Linux/Windows? Installeer dan Java 21 (bijv. `openjdk-21-jre-headless` of
  [Adoptium Temurin 21](https://adoptium.net)).
- **RAM:** minimaal **4 GB** voor de server, **6 GB** aanbevolen (meer bij veel spelers).
- **Poorten:**
  - `25565` **TCP**: Minecraft (of de poort die je in Crafty kiest).
  - `24454` **UDP**: Simple Voice Chat. Zonder deze poort werkt alles behalve voice chat.

## Eerste keer installeren
1. Log in op Crafty en klik op **Create New Server** (➕).
2. Kies **Minecraft Java** en dan de optie om een **zip-bestand te importeren/uploaden**
   (*Import Server* → *Upload Zip*).
3. Upload `GoofBall-Cobblemon-Server-<versie>.zip`.
   - Vraagt Crafty naar de map met de server? Kies de **bovenste map** (de bestanden staan direct in
     de zip, niet in een submap).
4. Vul in:
   - **Server name:** bijv. `GoofBall Cobblemon`
   - **Server JAR / executable:** `fabric-server-launch.jar`
   - **Min memory:** `4` GB, **Max memory:** `6` GB
   - **Port:** `25565` (of een vrije poort naar keuze)
5. Klik op **Import Server** / **Create**.
6. Open de server en ga naar **Config**:
   - Controleer of het **Server Execution Command** ongeveer zo is:
     `java -Xms4096M -Xmx6144M -jar fabric-server-launch.jar nogui`
   - Kies bij **Java** (als je Crafty-versie die optie heeft) een **Java 21**-installatie.
   - Sla op.
7. Klik op **Start**. Crafty vraagt of je akkoord gaat met de
   [Minecraft EULA](https://aka.ms/MinecraftEULA) → **Ja**.
8. De eerste start duurt even (Minecraft en libraries worden gedownload, Cobblemon laadt 1000+
   Pokémon). Klaar is de server als je in de **Terminal** dit ziet:
   `Done (…)! For help, type "help"`
9. Maak jezelf beheerder via de Terminal: `op <jouw-minecraftnaam>`

### Docker: extra UDP-poort voor voice chat
De standaard Crafty `docker-compose.yml` zet meestal alleen TCP-poorten open. Voeg voor voice chat
een UDP-poort toe en herstart de container:

```yaml
    ports:
      - "8443:8443"
      - "25565:25565"
      - "24454:24454/udp"   # Simple Voice Chat
```

Draai je meerdere servers of wil je een andere poort? Pas dan na de eerste start
`config/voicechat/voicechat-server.properties` aan (`port=…`) via het **Files**-tabblad.

## Handige commando's (in de Crafty Terminal)
| Commando | Wat het doet |
|---|---|
| `op <naam>` | Speler beheerder maken |
| `whitelist on` / `whitelist add <naam>` | Alleen vrienden toelaten |
| `chunky radius 3000` en dan `chunky start` | Wereld vooraf genereren rond spawn (minder lag later). Doe dit als er niemand online is. |
| `spark tps` / `spark profiler start` | Lag onderzoeken |

## Updaten naar een nieuwe versie van het modpack
Je wereld en instellingen blijven bewaard; je vervangt alleen de mods.

1. **Backup:** tabblad **Backups** → maak een backup.
2. **Stop** de server.
3. Pak de nieuwe `GoofBall-Cobblemon-Server-<versie>.zip` uit op je eigen computer.
4. In Crafty → **Files**:
   - Verwijder de map `mods`.
   - Maak een nieuwe map `mods` en upload daarin alle `.jar`-bestanden uit de map `mods` van de nieuwe zip.
   - Upload ook `fabric-server-launch.jar` opnieuw (overschrijven), voor het geval de Fabric-versie veranderd is.
   - **Niet** `server.properties` overschrijven, anders ben je je instellingen kwijt.
5. **Start** de server.

Laat spelers daarna ook de nieuwe `.mrpack` gebruiken (zie [SPELERS.md](SPELERS.md)): client en
server moeten dezelfde versie hebben.

## Problemen?
- **"Unsupported class file major version" / Java-fout:** de server draait niet op Java 21.
- **Server stopt met "OutOfMemoryError":** verhoog *Max memory* in Crafty.
- **Speler krijgt "Mod rejections" / "mismatched mod":** de speler heeft een andere modpack-versie dan de server.
- **Voice chat werkt niet:** UDP-poort 24454 staat niet open (router, firewall of Docker).
