#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return raw


def localize_text(raw: object, locale: str) -> str:
    if isinstance(raw, dict):
        preferred = str(raw.get(locale, "")).strip()
        if preferred:
            return preferred
        fallback = str(raw.get("en", "")).strip() or str(raw.get("de", "")).strip()
        return fallback
    return str(raw or "").strip()


def build_index(root: Path) -> dict:
    games = []
    for game_dir in sorted(p for p in (root / "games").iterdir() if p.is_dir()):
        metadata = load_json(game_dir / "metadata.json")
        links = metadata.get("links", [])
        games.append(
            {
                "game_id": metadata.get("game_id", game_dir.name),
                "title": metadata.get("title", ""),
                "description": metadata.get("description", ""),
                "publisher": metadata.get("publisher", ""),
                "release_year": metadata.get("release_year", ""),
                "genre": metadata.get("genre", ""),
                "page_url": f"games/{game_dir.name}/index.html",
                "website_url": metadata.get("website_url", ""),
                "community_url": metadata.get("community_url", ""),
                "discord_url": metadata.get("discord_url", ""),
                "download_url": metadata.get("download_url", ""),
                "media": metadata.get("media", {}),
                "links": links if isinstance(links, list) else [],
            }
        )
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "repo_url": "",
            "branch": "",
            "commit_sha": "",
        },
        "games": games,
    }


def render_links(links: list[dict], locale: str) -> str:
    if not links:
        return "<p class=\"muted\">No external links available.</p>"
    items = []
    for entry in links:
        label = localize_text(entry.get("label"), locale)
        url = html.escape(str(entry.get("url", "")).strip(), quote=True)
        if not url:
            continue
        items.append(f'<li><a href="{url}">{html.escape(label)}</a></li>')
    if not items:
        return "<p class=\"muted\">No external links available.</p>"
    return f"<ul class=\"link-list\">{''.join(items)}</ul>"


def render_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 0; background: #0f1722; color: #e7edf5; }}
    header, main {{ max-width: 1100px; margin: 0 auto; padding: 1.2rem; }}
    .card {{ background: #182435; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 1rem; }}
    .grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}
    a {{ color: #8fd3ff; }}
    .muted {{ color: #a8b5c6; }}
    .link-list {{ padding-left: 1.2rem; }}
    .game-hero {{ width: 100%; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


def build_site(root: Path, output: Path) -> None:
    index = build_index(root)
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    games_html = []
    for entry in index["games"]:
        game_id = str(entry["game_id"])
        game_dir = root / "games" / game_id
        locale = "en"
        title = localize_text(entry.get("title"), locale) or game_id
        description = localize_text(entry.get("description"), locale)
        media = entry.get("media", {})
        image_rel = str(media.get("image", "")).strip()
        detail_html = render_links(entry.get("links", []), locale)
        game_output = output / "games" / game_id
        game_output.mkdir(parents=True, exist_ok=True)
        for filename in ("README.md", "metadata.json", "links.json", "payload.json"):
            source = game_dir / filename
            if source.is_file():
                shutil.copy2(source, game_output / filename)
        for folder_name in ("media", "screenshots"):
            source_dir = game_dir / folder_name
            if source_dir.is_dir():
                shutil.copytree(
                    source_dir,
                    game_output / folder_name,
                    dirs_exist_ok=True,
                )
        image_html = ""
        if image_rel:
            image_html = (
                f'<img class="game-hero" src="{html.escape(image_rel, quote=True)}" '
                f'alt="{html.escape(title)}">'
            )
        page = render_page(
            title,
            f"""
<header>
  <p class="muted"><a href="../..">Back to index</a></p>
  <h1>{html.escape(title)}</h1>
  <p class="muted">{html.escape(description)}</p>
</header>
<main class="grid">
  <section class="card">
    {image_html}
    <h2>Metadata</h2>
    <pre>{html.escape(json.dumps(entry, indent=2, ensure_ascii=False))}</pre>
  </section>
  <section class="card">
    <h2>Links</h2>
    {detail_html}
    <p class="muted">Source files: <code>games/{html.escape(game_id)}</code></p>
  </section>
</main>
""",
        )
        (game_output / "index.html").write_text(page, encoding="utf-8")
        games_html.append(
            f"""
<article class="card">
  <h2><a href="games/{html.escape(game_id)}/index.html">{html.escape(title)}</a></h2>
  <p class="muted">{html.escape(description)}</p>
  <p><a href="games/{html.escape(game_id)}/index.html">Open game page</a></p>
</article>
"""
        )
    index_page = render_page(
        "Open Source Games Index",
        f"""
<header>
  <h1>Open Source Games Index</h1>
  <p class="muted">Public metadata and navigation for LANLauncherNG.</p>
</header>
<main>
  <section class="grid">
    {''.join(games_html)}
  </section>
</main>
""",
    )
    (output / "index.html").write_text(index_page, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="site")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    build_site(root, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
