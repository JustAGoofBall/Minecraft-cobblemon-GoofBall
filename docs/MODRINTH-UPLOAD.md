# Publishing the modpack on Modrinth

Once the pack is on Modrinth, players can find it in the Modrinth App (and Prism/ATLauncher), install
it in one click, and get a notification when there's an update.

Every mod, shader and resource pack in this pack is hosted on Modrinth itself, so the pack follows
Modrinth's modpack rules.

## Once: create the project
1. Go to <https://modrinth.com> and sign in (e.g. with your GitHub account).
2. Click **+** (top right) → **Create a project**.
   - **Project type:** Modpack
   - **Name:** `GoofBall Cobblemon`
   - **URL:** e.g. `goofball-cobblemon`
   - **Visibility:**
     - *Public*: anyone can find it.
     - *Unlisted*: only people with the link can find it (good for a friend group).
     - *Private*: only you (and members you add).
   - **Summary:** e.g. `Cobblemon 1.8 modpack with Mega Evolutions, Radical Red trainers, new biomes, structures, shaders and great server performance.`
3. Then fill in on the project page:
   - **Description:** what the pack is and how to join the server. You can reuse the mod list from
     the [README](../README.md).
   - **Icon:** a picture (e.g. a Poké Ball).
   - **Tags:** e.g. *Adventure*, *Multiplayer*, *Exploration*.
   - **License:** pick one for your pack (e.g. *MIT*). This covers your pack setup, not the mods.
   - **Environment:** *Client and server*.

## Uploading a version
1. Download the latest `GoofBall-Cobblemon-<version>.mrpack` from the
   [Releases](https://github.com/JustAGoofBall/Minecraft-cobblemon-GoofBall/releases).
2. On your Modrinth project page: **Versions** → **Create a version** (or *Upload a version*).
3. Drop in the `.mrpack` file. Modrinth fills in *Minecraft 1.21.1* and *Fabric* by itself.
   - **Version number:** same as the release, e.g. `2.0.0`
   - **Version title:** e.g. `GoofBall Cobblemon 2.0.0`
   - **Release channel:** *Release*
   - **Changelog:** what changed.
4. Click **Create** / **Publish**.

> Don't upload the **server zip** to Modrinth. It's only for Crafty and lives on GitHub.

## Review
The first time, click **Submit for review**. A Modrinth moderator checks the project, which can take a
few days. Make sure there's a clear description, an icon and a license, or it gets sent back. After
approval the pack can be found (unless it's *Private*).

## For every new version
1. Make a new GitHub Release (see [MAINTENANCE.md](MAINTENANCE.md)).
2. Upload the new `.mrpack` to Modrinth as a new version (steps above).
3. Update the server in Crafty (see [CRAFTY.md](CRAFTY.md)).
