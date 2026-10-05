# GoofBall Cobblemon

Een Fabric-modpack met **Cobblemon** (Pokémon in Minecraft) voor de GoofBall-server, met
performance-mods, een minimap, recepten-overzicht en voice chat.

| | |
|---|---|
| Minecraft | **1.21.1** |
| Modloader | **Fabric** 0.19.5 |
| Cobblemon | **1.8.1** |
| Java (server) | **21** |

## Downloaden
Bij elke [Release](https://github.com/JustAGoofBall/Minecraft-cobblemon-GoofBall/releases/latest) horen twee bestanden:

| Bestand | Voor wie | Handleiding |
|---|---|---|
| `GoofBall-Cobblemon-<versie>.mrpack` | **Spelers**: importeren in Modrinth App, Prism Launcher of ATLauncher | [docs/SPELERS.md](docs/SPELERS.md) |
| `GoofBall-Cobblemon-Server-<versie>.zip` | **Server**: importeren in Crafty Controller | [docs/CRAFTY.md](docs/CRAFTY.md) |

Spelers en server moeten altijd **dezelfde versie** gebruiken.

## Mods
| Mod | Spelers | Server | Waarvoor |
|---|:-:|:-:|---|
| [Cobblemon](https://modrinth.com/mod/cobblemon) | ✅ | ✅ | Pokémon! |
| [Fabric API](https://modrinth.com/mod/fabric-api) | ✅ | ✅ | Nodig voor bijna alle Fabric-mods |
| [Lithium](https://modrinth.com/mod/lithium) | ✅ | ✅ | Snellere game-logica |
| [FerriteCore](https://modrinth.com/mod/ferrite-core) | ✅ | ✅ | Minder RAM-gebruik |
| [ModernFix](https://modrinth.com/mod/modernfix) | ✅ | ✅ | Sneller opstarten, minder RAM |
| [Krypton](https://modrinth.com/mod/krypton) | ✅ | ✅ | Efficiënter netwerkverkeer |
| [Simple Voice Chat](https://modrinth.com/mod/simple-voice-chat) | ✅ | ✅ | Voice chat in de game |
| [Jade](https://modrinth.com/mod/jade) | ✅ | ✅ | Laat zien naar welk blok of welke entity je kijkt |
| [AppleSkin](https://modrinth.com/mod/appleskin) | ✅ | ✅ | Honger en verzadiging zichtbaar |
| [Sodium](https://modrinth.com/mod/sodium) | ✅ | | Veel meer FPS |
| [Entity Culling](https://modrinth.com/mod/entityculling) | ✅ | | Meer FPS (verborgen entities niet tekenen) |
| [ImmediatelyFast](https://modrinth.com/mod/immediatelyfast) | ✅ | | Meer FPS (sneller tekenen van GUI, tekst enz.) |
| [Xaero's Minimap](https://modrinth.com/mod/xaeros-minimap) | ✅ | | Minimap |
| [Xaero's World Map](https://modrinth.com/mod/xaeros-world-map) | ✅ | | Wereldkaart (toets **M**) |
| [EMI](https://modrinth.com/mod/emi) | ✅ | | Recepten opzoeken |
| [Mod Menu](https://modrinth.com/mod/modmenu) | ✅ | | Mod-instellingen in het menu |
| [Mouse Tweaks](https://modrinth.com/mod/mouse-tweaks) | ✅ | | Makkelijker items verplaatsen |
| [Chunky](https://modrinth.com/mod/chunky) | | ✅ | Wereld vooraf genereren |
| [spark](https://modrinth.com/mod/spark) | | ✅ | Lag onderzoeken |

(Plus libraries die automatisch meekomen, zoals Text Placeholder API voor Mod Menu.)

## Handleidingen
- [docs/SPELERS.md](docs/SPELERS.md): modpack installeren en met de server verbinden
- [docs/CRAFTY.md](docs/CRAFTY.md): server opzetten en updaten in Crafty Controller
- [docs/MODRINTH-UPLOAD.md](docs/MODRINTH-UPLOAD.md): het pack op Modrinth publiceren
- [docs/ONDERHOUD.md](docs/ONDERHOUD.md): mods toevoegen/updaten en een nieuwe release maken

## Hoe deze repo werkt
```
pack/                      Het modpack (packwiz): per mod een klein .pw.toml-bestand
server/                    Extra bestanden voor de server-zip (server.properties, start-scripts)
scripts/build_server.py    Maakt de server-zip uit de .mrpack
.github/workflows/         Bouwt automatisch de .mrpack en server-zip bij elke push en release
docs/                      Handleidingen
```

Er staan geen jar-bestanden in de repo. GitHub Actions downloadt de mods van Modrinth (met
hash-controle) als de release wordt gebouwd.

## Licenties
De mods zijn van hun eigen makers en vallen onder hun eigen licentie (zie de links hierboven).
De server-zip bevat de server-mods zelf, zodat Crafty hem direct kan importeren.
Let op: Simple Voice Chat is *All Rights Reserved*. Die jar staat dus in de server-zip voor gebruik
op je eigen server; zet de server-zip niet op andere sites.
