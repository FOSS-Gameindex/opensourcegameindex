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

