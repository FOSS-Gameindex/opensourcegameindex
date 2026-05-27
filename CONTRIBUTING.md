# Contributing

## Branch flow

- Open pull requests against `main`.
- Keep changes scoped to one game or one metadata concern whenever possible.
- Core maintainers merge reviewed pull requests into `main`.
- Release promotion happens by merging `main` into `release`.

## Content rules

- Keep `games/<gameid>/README.md` human readable and short.
- Keep `games/<gameid>/metadata.json` machine readable and deterministic.
- Prefer stable links that do not depend on personal accounts.
- Add media files only when the license and provenance are clear.

## Required checks

- JSON schema validation.
- Link validation.
- File existence checks for declared media.
- Site generation smoke test.

