# AGENTS.md

Repo-specific guidance for agents working in this repository.

## Project shape

- This repository is a public catalog of open-source games.
- The source of truth is under `games/<gameid>/`.
- The generated site and root `index.json` are build artifacts, not hand-edited content.

## Directory conventions

- Each game entry should live in `games/<gameid>/`.
- Required files:
  - `README.md`
  - `metadata.json`
- Optional files:
  - `links.json`
  - `payload.json`
  - `media/`
  - `screenshots/`

## Content rules

- Keep `games/<gameid>/README.md` short and human-readable.
- Keep `metadata.json` machine-readable and deterministic.
- Ensure `metadata.json.game_id` matches the folder name exactly.
- Keep `links` as a list of objects with valid `http` or `https` URLs.
- Only add media when the license and provenance are clear.
- Prefer stable links that do not depend on personal accounts.
- Treat `lan_supported` as the flag for LAN-relevant catalog filtering.
- Use `runtime_support` consistently; the site normalizes `native`, `wine`, `proton`, `proton-ge`, and `windows`.

## Build and validation

- Validate repository content with `python3 tools/validate_repo.py`.
- Build the static site with `python3 tools/build_site.py --root . --output site`.
- Generated output lands in `site/` and should not be edited manually.
- If you need to verify a change, run validation before build output checks.

## Adding games

- Search online for actively maintained open-source multiplayer games that are suitable for LAN parties.
- Exclude any title already present under `games/` and any source or official page already listed in `crawled_urls.json`.
- Verify current maintenance from official sources before adding an entry.
- Create `games/<gameid>/README.md` and `games/<gameid>/metadata.json` in the same format as the existing entries.
- Keep `README.md` short and human-readable, and keep `metadata.json` deterministic with a matching `game_id`, stable URLs, the correct `lan_supported` flag, and one image plus one YouTube video in `media` when available.
- After researching a game, add every external URL you inspected to `crawled_urls.json` so future searches avoid repeating the same crawl.
- Run `python3 tools/validate_repo.py` after adding or changing entries.

### Sample metadata

Use existing games under `games/` as the primary reference. This example shows the full structure the repo expects:

```json
{
  "game_id": "example-game",
  "title": "Example Game",
  "description": "An open-source multiplayer game with LAN support.",
  "publisher": "Example Project",
  "release_year": 2024,
  "genre": "First-person shooter",
  "lan_supported": true,
  "max_players": "16",
  "runtime_support": ["native", "wine"],
  "website_url": "https://example.org/",
  "community_url": "https://example.org/community/",
  "discord_url": "https://discord.gg/example",
  "download_url": "https://example.org/download/",
  "page_url": "https://example.org/game/",
  "media": {
    "image_url": "https://example.org/media/screenshot.jpg",
    "image_source_url": "https://example.org/",
    "video_url": "https://www.youtube.com/watch?v=example",
    "video_title": "Example Game trailer"
  },
  "links": [
    {
      "label": "Website",
      "url": "https://example.org/"
    },
    {
      "label": "Community",
      "url": "https://example.org/community/"
    },
    {
      "label": "Download",
      "url": "https://example.org/download/"
    },
    {
      "label": "Source",
      "url": "https://github.com/example/example-game"
    }
  ],
  "syncthing_folder": "example-game",
  "syncthing_seed_device_ids": [
    "EXAMPLEDEVICEID1234567890"
  ],
  "category": "Shooter"
}
```

## Working practice

- Check `git status` before editing; the worktree may already contain unrelated user changes.
- Do not overwrite or revert changes you did not make unless the user asks.
- Prefer small, scoped edits that touch one game or one metadata concern at a time.
- When adding or changing game content, confirm the schema and validation rules in `docs/schema.md` and `tools/validate_repo.py`.
