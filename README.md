# Open Source Games Index

Public, reviewable game metadata for LANLauncherNG.

This repository is split into two layers:

- `games/<gameid>/` contains the human-authored source material for one game.
- GitHub Pages is generated from that source by CI and provides a browsable site.

LANLauncherNG consumes the generated `index.json` and the published game pages for:

- metadata
- artwork and screenshots
- project website links
- community board links
- Discord links
- download references

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

