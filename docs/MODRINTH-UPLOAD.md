# Het modpack op Modrinth zetten

Als het pack op Modrinth staat, kunnen spelers het in de Modrinth App (en Prism/ATLauncher) zoeken,
met één klik installeren en krijgen ze automatisch een melding bij updates.

Alle mods in dit pack staan zelf op Modrinth, dus het pack voldoet aan de regels voor modpacks.

## Eenmalig: project aanmaken
1. Ga naar <https://modrinth.com> en log in (bijv. met je GitHub-account).
2. Klik rechtsboven op **+** → **Create a project**.
   - **Project type:** Modpack
   - **Name:** `GoofBall Cobblemon`
   - **URL:** bijv. `goofball-cobblemon`
   - **Visibility:**
     - *Public*: iedereen kan het vinden.
     - *Unlisted*: alleen mensen met de link kunnen het vinden (handig voor een vriendengroep).
     - *Private*: alleen jij (en leden die je toevoegt).
   - **Summary:** bijv. `Cobblemon 1.8 modpack voor de GoofBall-server: Pokémon in Minecraft, met performance-mods, minimap en voice chat.`
3. Vul daarna op de projectpagina in:
   - **Description:** wat het pack is, hoe je op de server komt. Je kunt de modlijst uit de
     [README](../README.md) gebruiken.
   - **Icon:** een plaatje (bijv. een Pokéball).
   - **Tags:** bijv. *Adventure*, *Multiplayer*, *Lightweight*.
   - **License:** kies er een voor je pack (bijv. *MIT*). Dit gaat over jouw pack-instellingen,
     niet over de mods zelf.
   - **Environment:** *Client and server*.

## Een versie uploaden
1. Download de nieuwste `GoofBall-Cobblemon-<versie>.mrpack` van de
   [Releases](https://github.com/JustAGoofBall/Minecraft-cobblemon-GoofBall/releases).
2. Op je Modrinth-projectpagina: **Versions** → **Create a version** (of *Upload a version*).
3. Sleep het `.mrpack`-bestand erin. Modrinth vult *Minecraft 1.21.1* en *Fabric* zelf in.
   - **Version number:** hetzelfde als de release, bijv. `1.0.0`
   - **Version title:** bijv. `GoofBall Cobblemon 1.0.0`
   - **Release channel:** *Release*
   - **Changelog:** wat er veranderd is.
4. Klik op **Create** / **Publish**.

> Upload de **server-zip niet** naar Modrinth. Modrinth staat geen jar-bestanden van andere mods in
> een pack toe. De server-zip is alleen voor Crafty en staat op GitHub.

## Review
Bij de eerste keer **Submit for review** klikken. Een moderator van Modrinth controleert het project;
dat kan een paar dagen duren. Zorg dat er een duidelijke beschrijving, een icoon en een licentie
staan, anders wordt het teruggestuurd. Na goedkeuring is het pack te vinden (behalve als het
*Private* is).

## Bij elke nieuwe versie
1. Maak een nieuwe GitHub Release (zie [ONDERHOUD.md](ONDERHOUD.md)).
2. Upload de nieuwe `.mrpack` op Modrinth als nieuwe versie (stappen hierboven).
3. Zet de nieuwe server-zip op Crafty (zie [CRAFTY.md](CRAFTY.md)).
