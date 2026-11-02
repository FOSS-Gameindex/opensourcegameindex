# Open Source Game Index

Public, reviewable metadata for open-source games.

This repository is a public source for a broader open-source game catalog that can also be consumed by tools like LANLauncherNG.

What this repository provides:

- human-authored game pages under `games/<gameid>/`
- machine-readable metadata for each game
- a generated GitHub Pages site for browsing the catalog
- a root `index.json` for tooling integrations
- optional `source.json` metadata for the public index mirror, including its monotonically increasing index revision

The repo can contain a mix of:

- LAN games
- online multiplayer games
- co-op or split-screen games
- single-player-only games

The `lan_supported` flag is what lets LLNG separate the LAN-relevant subset from the broader catalog.

The generated site visually marks LAN-capable titles with a badge and provides filters for LAN-only browsing, player-count ranges, and runtime support.

The generated index uses schema version 2. Increase `source.json.index_revision` for every catalog release; LLNG rejects rollback and different content reusing an accepted revision. The generated index is an unsigned candidate. Before distributing it through LLNG, sign it with an authorized offline publisher key using the LLNG `sign_ogsi_document.py` workflow.

Every game's `metadata.json` contains blank LLNG distribution templates for convenient editing. Leave them empty for catalog-only games. Ouisync-published games fill in the read token, repository `info_hash`, editable files, archive path/format/SHA-256, embedded `version.ini` path, and game `version`. The generator omits untouched templates from `index.json`, but includes completed LLNG distribution data plus optional `runner`/`installer_tasks` recommendations. `runner` can select `wine`, `proton`, or `proton-ge`; `installer_tasks` can record proven `winetricks`/`protontricks` dependencies.

## Workflow

1. Contributors open pull requests against `main`.
2. Maintainers review and merge into `main`.
3. A release branch is promoted from `main` when the index should be published.
4. CI generates the static site and deploys it to GitHub Pages.

## Repository layout

```text
games/<gameid>/
  README.md
  metadata.json
  links.json
  media/
  screenshots/
```

The generated site also exposes a machine-readable `index.json` at the root.
