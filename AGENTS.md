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

## Working practice

- Check `git status` before editing; the worktree may already contain unrelated user changes.
- Do not overwrite or revert changes you did not make unless the user asks.
- Prefer small, scoped edits that touch one game or one metadata concern at a time.
- When adding or changing game content, confirm the schema and validation rules in `docs/schema.md` and `tools/validate_repo.py`.
