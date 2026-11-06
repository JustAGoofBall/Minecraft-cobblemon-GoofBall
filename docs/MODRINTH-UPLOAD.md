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

## Uploading a version (automatic)
Publishing a GitHub Release uploads the `.mrpack` to Modrinth by itself (CI step *Publish to Modrinth* in
`.github/workflows/build.yml`, project id `aDvJFIvn`, secret `MODRINTH_TOKEN` with the scope *Create versions*).
- **Version number:** the tag without `v` (e.g. `2.8.0`)
- **Version title:** the release title
- **Changelog:** the release description
- **Channel:** *Release*, or *Beta* if the GitHub release is marked as pre-release

Check on the project's **Versions** page that the new version shows up. If the step fails (for example
the token expired), upload the `.mrpack` from the release by hand: **Versions** → **Create a version**.

> Don't upload the **server zip** to Modrinth. It's only for Crafty and lives on GitHub.

## Files that are not from Modrinth
The only non-Modrinth content in the `.mrpack` is the pack's own configuration (`overrides/config`,
`overrides/defaultconfigs`) and `overrides/resourcepacks/GoofBall-Trainer-Skins.zip`. That zip holds the skins of
the two NPC trainers, made by the project owner (JustAGoofBall) for this pack. `ballajustgoof.png` is built on
the default Minecraft skin (Steve), so say that if Modrinth asks; the other skin, `justagoofball.png`, is a
separate design. If Modrinth does not accept it, remove the zip from `pack/resourcepacks/` and `packwiz refresh`.

## Review
The first time, click **Submit for review**. A Modrinth moderator checks the project, which can take a
few days. Make sure there's a clear description, an icon and a license, or it gets sent back. After
approval the pack can be found (unless it's *Private*).

## For every new version
1. Make a new GitHub Release (see [MAINTENANCE.md](MAINTENANCE.md)). Modrinth follows automatically.
2. Update the server in Crafty (see [CRAFTY.md](CRAFTY.md)).
