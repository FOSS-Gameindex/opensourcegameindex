# Metadata Schema

Each game lives under `games/<gameid>/`.

Required files:

- `README.md`
- `metadata.json`

Optional files:

- `links.json`
- `payload.json`
- `media/*`
- `screenshots/*`

## `metadata.json`

Required top-level fields:

- `game_id`
- `title`

Recommended fields:

- `description`
- `publisher`
- `release_year`
- `genre`
- `lan_supported`
- `max_players`
- `runtime_support`
- `website_url`
- `community_url`
- `discord_url`
- `download_url`
- `page_url`
- `links`
- `media`
- `syncthing_folder`
- `syncthing_seed_device_ids`

## `links`

Each link item should include:

- `label`
- `url`

`label` can be either a plain string or a locale map with `en` and `de`.

`lan_supported` should be set to `true` for titles that include a LAN mode and are therefore relevant to LAN-oriented clients such as LLNG. Single-player-only titles can stay in the public catalog, but they should set `lan_supported` to `false` or omit it when not applicable.

`runtime_support` is a convenience field for the generated site. Use it to describe the supported launch/runtime families as a comma-separated string or list, for example `native`, `wine`, `proton`, `proton-ge`, or combinations like `native,wine`. The site uses it to filter by runtime support without changing the game content model.

`syncthing_folder` and `syncthing_seed_device_ids` are transport hints for offline peer-to-peer sync. The launcher can use them to bootstrap or refresh the Syncthing peer graph for a game or for the public index mirror itself.
