# Onderhoud: mods toevoegen, updaten en een nieuwe versie uitbrengen

Het modpack staat in de map [`pack/`](../pack) en wordt beheerd met
[packwiz](https://packwiz.infra.link). In die map staan alleen kleine tekstbestanden: per mod één
`.pw.toml` met de downloadlink en hash. Er staan geen jar-bestanden in de repo.

## Nieuwe versie uitbrengen (zonder iets te installeren)
Dit kan helemaal via de GitHub-website:

1. Ga naar **Releases** → **Draft a new release**.
2. **Choose a tag** → typ een nieuw versienummer, bijv. `v1.0.1` → *Create new tag*.
   (Vanaf `main`.)
3. Titel bijv. `GoofBall Cobblemon 1.0.1`, schrijf wat er veranderd is → **Publish release**.
4. Wacht een paar minuten. GitHub Actions bouwt het pack en zet deze bestanden bij de release:
   - `GoofBall-Cobblemon-1.0.1.mrpack`: voor spelers en voor Modrinth
   - `GoofBall-Cobblemon-Server-1.0.1.zip`: voor Crafty

Het versienummer van de tag (zonder `v`) wordt automatisch de versie van het pack.
De voortgang zie je onder het tabblad **Actions**.

## packwiz installeren (voor mods toevoegen/updaten)
Je hebt [Go](https://go.dev/dl/) nodig, daarna:

```sh
go install github.com/packwiz/packwiz@latest
```

Of download een kant-en-klare versie: open de nieuwste geslaagde run op
<https://github.com/packwiz/packwiz/actions> en download het bestand voor je systeem onder *Artifacts*.

Alle commando's hieronder voer je uit **in de map `pack/`**.

## Mod toevoegen
```sh
packwiz modrinth add <naam-of-link>      # bijv. packwiz modrinth add waystones
```
Zoek de naam op <https://modrinth.com/mods> (het stuk achter `/mod/` in de link).
Controleer daarna in het nieuwe `mods/<naam>.pw.toml` de regel `side`:

| `side` | Betekenis |
|---|---|
| `"both"` | Spelers én server hebben de mod nodig (bijv. mods die blokken, items of Pokémon toevoegen) |
| `"client"` | Alleen spelers (graphics, minimap, GUI-mods). Komt niet in de server-zip. |
| `"server"` | Alleen de server (beheer-tools zoals Chunky). Komt niet in de `.mrpack` voor spelers. |

Heb je `side` met de hand aangepast, draai dan `packwiz refresh`.

## Mod verwijderen
```sh
packwiz remove <naam>
```

## Mods updaten
```sh
packwiz update --all      # alles
packwiz update cobblemon  # één mod
```
Let op: update alleen naar versies voor **Minecraft 1.21.1**. Een nieuwe Minecraft-versie
(`packwiz migrate minecraft <versie>`) werkt pas als **alle** mods (vooral Cobblemon) die versie
ondersteunen. Een bestaande wereld kan je niet terugzetten naar een oudere versie: maak altijd
eerst een backup.

## Lokaal testen (optioneel)
```sh
mkdir -p dist
cd pack
packwiz modrinth export -o ../dist/GoofBall-Cobblemon-test.mrpack
cd ..
python3 scripts/build_server.py dist/GoofBall-Cobblemon-test.mrpack
```
Dan staan de `.mrpack` en de server-zip in `dist/` (die map wordt niet meegecommit).

## Wijzigingen opslaan
Commit de veranderde bestanden in `pack/` (inclusief `index.toml` en `pack.toml`) en push naar
`main`. GitHub Actions controleert bij elke push of het pack nog klopt en bouwt een testversie
(te downloaden onder **Actions** → de run → *Artifacts*). Maak daarna een nieuwe release (zie boven).

## Configs meeleveren (optioneel)
Bestanden die je in het pack wilt meesturen, zoals standaard-configs, zet je in `pack/` op dezelfde
plek als in de Minecraft-map (bijv. `pack/config/jade/…`). Draai daarna `packwiz refresh`.
Die bestanden gaan naar spelers **en** naar de server.
