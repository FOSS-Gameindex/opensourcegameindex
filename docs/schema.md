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
- `website_url`
- `community_url`
- `discord_url`
- `download_url`
- `page_url`
- `links`
- `media`

## `links`

Each link item should include:

- `label`
- `url`

`label` can be either a plain string or a locale map with `en` and `de`.

`lan_supported` should be set to `true` for titles that include a LAN mode and are therefore relevant to LAN-oriented clients such as LLNG. Single-player-only titles can stay in the public catalog, but they should set `lan_supported` to `false` or omit it when not applicable.
