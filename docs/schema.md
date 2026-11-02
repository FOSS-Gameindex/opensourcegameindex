# Metadata Schema

Each game lives under `games/<gameid>/`.

Required files:

- `README.md`
- `metadata.json`

Optional files:

- `links.json`
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

Every game metadata file includes the LLNG fields as empty templates. Leave them empty for catalog-only entries. Games distributed through LLNG need `version`, `game_provider_type: "ouisync"`, `distribution.archive` (archive path, format, SHA-256, and its internal `version.ini` path), and `llng.distribution` (Ouisync read token, repository info hash, and `editable_files`). Repository validation requires these fields together for Ouisync-published entries, and the index generator omits the untouched templates from the generated index.

## `links`

Each link item should include:

- `label`
- `url`

`label` can be either a plain string or a locale map with `en` and `de`.

`lan_supported` should be set to `true` for titles that include a LAN mode and are therefore relevant to LAN-oriented clients such as LLNG. Single-player-only titles can stay in the public catalog, but they should set `lan_supported` to `false` or omit it when not applicable.

`runtime_support` is a convenience field for the generated site. Use it to describe the supported launch/runtime families as a comma-separated string or list, for example `native`, `wine`, `proton`, `proton-ge`, or combinations like `native,wine`. The site uses it to filter by runtime support without changing the game content model. LLNG can use `runner` as the per-game Linux runtime default and `installer_tasks` to distribute tested `winetricks` or `protontricks` dependencies.

`source.json.index_revision` is a positive integer; increase it for each catalog release that will be signed and distributed. The site generator emits an unsigned schema-v2 index candidate. LLNG accepts it only after an authorized publisher signs the candidate; keep signing keys offline and outside this repository.
