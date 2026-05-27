# Open Source Games Index

Public, reviewable metadata for open-source games.

This repository is a public source of broader open-source game catalog that can also be consumed by tools like LANLauncherNG.

What this repository provides:

- human-authored game pages under `games/<gameid>/`
- machine-readable metadata for each game
- a generated GitHub Pages site for browsing the catalog
- a root `index.json` for tooling integrations

The repo can contain a Index of:

- LAN games
- online multiplayer games
- co-op or split-screen games
- single-player-only games

The `lan_supported` flag is what lets LLNG separate the LAN-relevant subset from the broader catalog.

The generated site visually marks LAN-capable titles with a badge and provides a simple filter for LAN-only browsing.

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
  payload.json
  media/
  screenshots/
```

The generated site also exposes a machine-readable `index.json` at the root.
