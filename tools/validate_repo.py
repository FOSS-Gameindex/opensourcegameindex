#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


GAME_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def load_json(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return raw


def valid_url(raw: str) -> bool:
    parsed = urlparse(raw)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_game(game_dir: Path) -> list[str]:
    errors: list[str] = []
    metadata_path = game_dir / "metadata.json"
    readme_path = game_dir / "README.md"
    if not metadata_path.is_file():
        errors.append(f"{game_dir}: missing metadata.json")
        return errors
    if not readme_path.is_file():
        errors.append(f"{game_dir}: missing README.md")

    try:
        metadata = load_json(metadata_path)
    except Exception as exc:  # noqa: BLE001
        return [f"{metadata_path}: {exc}"]

    game_id = str(metadata.get("game_id", "")).strip()
    if not GAME_ID_RE.match(game_id):
        errors.append(f"{metadata_path}: invalid game_id")
    elif game_id != game_dir.name:
        errors.append(f"{metadata_path}: game_id does not match folder name")

    links = metadata.get("links", [])
    if isinstance(links, list):
        for entry in links:
            if not isinstance(entry, dict):
                errors.append(f"{metadata_path}: link entry must be an object")
                continue
            url = str(entry.get("url", "")).strip()
            if not valid_url(url):
                errors.append(f"{metadata_path}: invalid link url {url!r}")
    else:
        errors.append(f"{metadata_path}: links must be a list")

    media = metadata.get("media", {})
    if isinstance(media, dict):
        for key in ("image", "video"):
            rel = str(media.get(key, "")).strip()
            if not rel:
                continue
            resolved = (game_dir / rel).resolve(strict=False)
            if not resolved.exists():
                errors.append(f"{metadata_path}: missing media file {rel!r}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    games_root = root / "games"
    for game_dir in sorted(p for p in games_root.iterdir() if p.is_dir()):
        errors.extend(validate_game(game_dir))
    for line in errors:
        print(line, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

