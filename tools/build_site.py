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


def load_optional_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return load_json(path)
    except (OSError, ValueError):
        return {}


def localize_text(raw: object, locale: str) -> str:
    if isinstance(raw, dict):
        preferred = str(raw.get(locale, "")).strip()
        if preferred:
            return preferred
        fallback = str(raw.get("en", "")).strip() or str(raw.get("de", "")).strip()
        return fallback
    return str(raw or "").strip()


def parse_player_count(raw: object) -> int | None:
    text = str(raw or "").strip()
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def player_bucket(player_count: int | None) -> str:
    if player_count is None:
        return "unknown"
    if player_count <= 2:
        return "1-2"
    if player_count <= 4:
        return "3-4"
    if player_count <= 8:
        return "5-8"
    return "9+"


def normalize_runtime_support(raw: object) -> list[str]:
    if isinstance(raw, list):
        values = [str(item).strip().lower() for item in raw if str(item).strip()]
    else:
        values = [part.strip().lower() for part in str(raw or "").split(",")]
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in {"native", "wine", "proton", "proton-ge", "windows"} and value not in seen:
            cleaned.append(value)
            seen.add(value)
    return cleaned


def runtime_bucket(values: list[str]) -> str:
    if not values:
        return "unknown"
    if len(values) > 1:
        return "mixed"
    return values[0]


def normalize_category(raw: object, genre: str, title: str) -> str:
    text = str(raw or "").strip()
    if text:
        return text
    genre_text = genre.strip().lower()
    if not genre_text:
        genre_text = title.strip().lower()
    if any(token in genre_text for token in ("shooter", "fps", "quake", "heretic", "hexen", "doom")):
        return "Shooter"
    if any(token in genre_text for token in ("strategy", "tactics", "tower defense", "simulation", "transport")):
        return "Strategy"
    if any(token in genre_text for token in ("racing", "kart")):
        return "Racing"
    if any(token in genre_text for token in ("puzzle", "match", "arcade")):
        return "Puzzle"
    if any(token in genre_text for token in ("rpg", "role", "open-world")):
        return "RPG"
    if any(token in genre_text for token in ("platform",)):
        return "Platformer"
    if any(token in genre_text for token in ("fighting", "combat")):
        return "Fighting"
    if any(token in genre_text for token in ("sandbox",)):
        return "Sandbox"
    if any(token in genre_text for token in ("server", "mmo")):
        return "Server"
    if any(token in genre_text for token in ("party",)):
        return "Party"
    if any(token in genre_text for token in ("engine",)):
        return "Engine"
    return "Action"


def build_index(root: Path) -> dict:
    source_config = load_optional_json(root / "source.json")
    source_seed_device_ids: list[str] = []
    if isinstance(source_config.get("seed_device_ids"), list):
        for value in source_config.get("seed_device_ids", []):
            text = str(value).strip()
            if text and text not in source_seed_device_ids:
                source_seed_device_ids.append(text)
    games = []
    for game_dir in sorted(p for p in (root / "games").iterdir() if p.is_dir()):
        metadata = load_json(game_dir / "metadata.json")
        payload = load_optional_json(game_dir / "payload.json")
        links = metadata.get("links", [])
        lan_supported = metadata.get("lan_supported")
        player_count = parse_player_count(metadata.get("max_players"))
        runtime_support = normalize_runtime_support(
            metadata.get("runtime_support", metadata.get("supported_runtimes"))
        )
        category = normalize_category(metadata.get("category"), str(metadata.get("genre", "")), str(metadata.get("title", "")))
        game_seed_device_ids: list[str] = []
        if isinstance(payload.get("syncthing_seed_device_ids"), list):
            for value in payload.get("syncthing_seed_device_ids", []):
                text = str(value).strip()
                if text and text not in game_seed_device_ids:
                    game_seed_device_ids.append(text)
        if not game_seed_device_ids:
            game_seed_device_ids = list(source_seed_device_ids)
        games.append(
            {
                "game_id": metadata.get("game_id", game_dir.name),
                "title": metadata.get("title", ""),
                "description": metadata.get("description", ""),
                "publisher": metadata.get("publisher", ""),
                "release_year": metadata.get("release_year", ""),
                "genre": metadata.get("genre", ""),
                "category": category,
                "lan_supported": lan_supported,
                "max_players": metadata.get("max_players", ""),
                "player_count": player_count,
                "player_bucket": player_bucket(player_count),
                "runtime_support": runtime_support,
                "runtime_bucket": runtime_bucket(runtime_support),
                "syncthing_folder": str(
                    payload.get("syncthing_folder", metadata.get("syncthing_folder", ""))
                ).strip(),
                "syncthing_seed_device_ids": game_seed_device_ids,
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
            "folder_id": str(source_config.get("folder_id", "")).strip(),
            "seed_device_ids": source_seed_device_ids,
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


def render_field_list(items: list[tuple[str, str]]) -> str:
    rows = []
    for label, value in items:
        if not value:
            continue
        rows.append(
            f"<dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd>"
        )
    if not rows:
        return "<p class=\"muted\">No structured metadata available.</p>"
    return f"<dl class=\"meta-list\">{''.join(rows)}</dl>"


def youtube_embed_url(raw: str) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    if "youtube.com/embed/" in text:
        return text
    if "youtu.be/" in text:
        video_id = text.rsplit("/", 1)[-1].split("?")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    if "watch?v=" in text:
        video_id = text.split("watch?v=", 1)[1].split("&", 1)[0]
        return f"https://www.youtube.com/embed/{video_id}"
    if "youtube.com/watch" in text:
        video_id = text.split("v=", 1)[-1].split("&", 1)[0]
        return f"https://www.youtube.com/embed/{video_id}"
    return text


def render_media(entry: dict, game_dir: Path, title: str) -> str:
    media = entry.get("media", {})
    if not isinstance(media, dict):
        media = {}
    image_url = str(media.get("image_url", "") or media.get("image", "")).strip()
    image_alt = str(media.get("image_alt", "")).strip() or title
    image_source = str(media.get("image_source_url", "")).strip()
    video_url = str(media.get("video_url", "") or media.get("youtube_url", "")).strip()
    video_title = str(media.get("video_title", "")).strip()
    video_source = str(media.get("video_source_url", "")).strip()
    parts = []
    if image_url:
        resolved_image = html.escape(image_url, quote=True)
        parts.append(
            f'<img class="game-hero" src="{resolved_image}" alt="{html.escape(image_alt, quote=True)}">'
        )
        if image_source:
            parts.append(
                f'<p class="muted meta-caption">Image source: <a href="{html.escape(image_source, quote=True)}">{html.escape(image_source)}</a></p>'
            )
    if video_url:
        embed_url = youtube_embed_url(video_url)
        label = video_title or "Video"
        parts.append(
            f'<div class="video-frame"><iframe src="{html.escape(embed_url, quote=True)}" title="{html.escape(label, quote=True)}" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>'
        )
        if video_source and video_source != video_url:
            parts.append(
                f'<p class="muted meta-caption">Video source: <a href="{html.escape(video_source, quote=True)}">{html.escape(video_source)}</a></p>'
            )
    return "".join(parts)


def render_metadata_summary(entry: dict, locale: str) -> str:
    title = localize_text(entry.get("title"), locale)
    description = localize_text(entry.get("description"), locale)
    publisher = localize_text(entry.get("publisher"), locale)
    release_year = localize_text(entry.get("release_year"), locale)
    genre = localize_text(entry.get("genre"), locale)
    category = localize_text(entry.get("category"), locale)
    lan_supported = "Yes" if entry.get("lan_supported") is True else "No"
    max_players = str(entry.get("max_players", "")).strip()
    runtime_support = ", ".join(normalize_runtime_support(entry.get("runtime_support", entry.get("supported_runtimes"))))
    website_url = str(entry.get("website_url", "")).strip()
    community_url = str(entry.get("community_url", "")).strip()
    discord_url = str(entry.get("discord_url", "")).strip()
    download_url = str(entry.get("download_url", "")).strip()
    links_count = str(len(entry.get("links", [])) if isinstance(entry.get("links"), list) else 0)
    media = entry.get("media", {})
    if not isinstance(media, dict):
        media = {}
    video_url = str(media.get("video_url", "") or media.get("youtube_url", "")).strip()
    image_url = str(media.get("image_url", "") or media.get("image", "")).strip()
    return render_field_list(
        [
            ("Title", title),
            ("Description", description),
            ("Publisher", publisher),
            ("Release year", release_year),
            ("Genre", genre),
            ("Category", category),
            ("LAN supported", lan_supported),
            ("Max players", max_players),
            ("Runtime support", runtime_support),
            ("Website", website_url),
            ("Community", community_url),
            ("Discord", discord_url),
            ("Download", download_url),
            ("Image URL", image_url),
            ("Video URL", video_url),
            ("Links", links_count),
        ]
    )


def render_page(title: str, body: str, body_class: str = "") -> str:
    body_attr = f' class="{html.escape(body_class)}"' if body_class else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 0; background: #0f1722; color: #e7edf5; }}
    body.site-index header, body.site-index main {{ max-width: none; }}
    header, main {{ max-width: 1100px; margin: 0 auto; padding: 1.2rem; }}
    body.site-index main {{ padding-inline: 1rem; }}
    .card {{ background: #182435; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 1rem; }}
    .grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}
    .game-grid {{ grid-template-columns: repeat(auto-fit, minmax(260px, 320px)); grid-auto-rows: 280px; align-items: stretch; justify-content: start; }}
    a {{ color: #8fd3ff; }}
    .muted {{ color: #a8b5c6; }}
    .link-list {{ padding-left: 1.2rem; }}
    .game-hero {{ width: 100%; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); }}
    .video-frame {{ position: relative; aspect-ratio: 16 / 9; border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); margin-top: 0.8rem; }}
    .video-frame iframe {{ width: 100%; height: 100%; border: 0; display: block; }}
    .badge-row {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.6rem 0 0.4rem; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.3rem 0.6rem; border-radius: 999px; font-size: 0.82rem; border: 1px solid transparent; }}
    .badge-lan {{ background: rgba(68, 173, 92, 0.16); color: #9af0aa; border-color: rgba(68, 173, 92, 0.35); }}
    .badge-no-lan {{ background: rgba(255, 255, 255, 0.06); color: #c4cedb; border-color: rgba(255, 255, 255, 0.1); }}
    .badge-category {{ background: rgba(143, 211, 255, 0.12); color: #d1f0ff; border-color: rgba(143, 211, 255, 0.28); }}
    .meta-list {{ display: grid; grid-template-columns: minmax(140px, 180px) 1fr; gap: 0.4rem 0.8rem; margin: 0; }}
    .meta-list dt {{ color: #a8b5c6; font-size: 0.9rem; }}
    .meta-list dd {{ margin: 0; word-break: break-word; }}
    .meta-caption {{ margin: 0.5rem 0 0; }}
    .filter-toolbar {{ display: flex; flex-wrap: wrap; gap: 0.9rem; align-items: end; margin: 0.75rem 0 1.25rem; }}
    .filter-field {{ display: flex; flex-direction: column; gap: 0.35rem; min-width: 180px; flex: 1 1 180px; }}
    .filter-label {{ display: block; color: #a8b5c6; font-size: 0.9rem; }}
    .filter-input {{ width: 100%; box-sizing: border-box; border: 1px solid rgba(255,255,255,0.14); background: rgba(10, 15, 24, 0.72); color: #e7edf5; border-radius: 12px; padding: 0.65rem 0.8rem; }}
    .filter-input:focus {{ outline: 2px solid rgba(143, 211, 255, 0.45); outline-offset: 1px; }}
    .filter-btn {{ appearance: none; border: 1px solid rgba(255,255,255,0.12); background: rgba(255,255,255,0.05); color: #e7edf5; border-radius: 999px; padding: 0.45rem 0.8rem; cursor: pointer; }}
    .filter-btn[aria-pressed="true"] {{ background: rgba(143, 211, 255, 0.16); border-color: rgba(143, 211, 255, 0.36); }}
    .cards-empty {{ color: #a8b5c6; padding: 1rem 0.25rem; }}
    .is-hidden {{ display: none !important; }}
    .game-card {{ position: relative; overflow: hidden; padding: 0; display: flex; align-items: stretch; background-color: #101722; background-image: linear-gradient(180deg, rgba(10, 14, 20, 0.08), rgba(10, 14, 20, 0.88)), var(--card-bg, linear-gradient(135deg, rgba(38,56,84,0.9), rgba(18,24,36,0.95))); background-size: cover; background-position: center; }}
    .game-card-link {{ position: absolute; inset: 0; z-index: 1; }}
    .game-card-overlay {{ position: relative; z-index: 0; display: grid; grid-template-rows: auto auto 1fr auto; gap: 0.45rem; width: 100%; min-height: 100%; padding: 1rem; background: linear-gradient(180deg, rgba(3, 8, 14, 0.08), rgba(3, 8, 14, 0.72)); }}
    .game-card-overlay h2 {{ margin: 0; font-size: 1.35rem; text-wrap: balance; }}
    .game-card-overlay .category-line {{ margin: 0; font-weight: 700; letter-spacing: 0.02em; }}
    .game-card-overlay .description-line {{ margin: 0; align-self: end; transform: translateY(-20px); }}
    .game-card-overlay .badge-row {{ margin-top: 0; transform: translateY(-20px); }}
    .game-card-overlay .badge {{ backdrop-filter: blur(6px); }}
    .table-wrap {{ overflow-x: auto; }}
    .game-table {{ width: 100%; border-collapse: collapse; }}
    .game-table th, .game-table td {{ text-align: left; padding: 0.7rem 0.6rem; border-bottom: 1px solid rgba(255,255,255,0.08); vertical-align: top; }}
    .game-table th {{ position: sticky; top: 0; background: #182435; z-index: 1; }}
    .sort-btn {{ appearance: none; border: 0; background: transparent; color: inherit; font: inherit; cursor: pointer; padding: 0; }}
    .table-panel {{ margin-top: 1rem; }}
    .view-toggle {{ display: flex; gap: 0.5rem; }}
    .view-active-grid #games-table-panel {{ display: none; }}
    .view-active-table #games-grid {{ display: none; }}
    .view-active-table #games-table-panel {{ display: block; }}
  </style>
</head>
<body{body_attr}>
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
    lan_count = sum(1 for entry in index["games"] if entry.get("lan_supported") is True)
    game_count = len(index["games"])
    categories = sorted({str(entry.get("category", "")).strip() for entry in index["games"] if str(entry.get("category", "")).strip()})
    games_html = []
    for entry in index["games"]:
        game_id = str(entry["game_id"])
        game_dir = root / "games" / game_id
        locale = "en"
        title = localize_text(entry.get("title"), locale) or game_id
        description = localize_text(entry.get("description"), locale)
        category = str(entry.get("category", "")).strip() or "Action"
        detail_html = render_links(entry.get("links", []), locale)
        metadata_html = render_metadata_summary(entry, locale)
        media_html = render_media(entry, game_dir, title)
        lan_supported = entry.get("lan_supported") is True
        max_players = str(entry.get("max_players", "")).strip()
        player_bucket_value = str(entry.get("player_bucket", "unknown"))
        runtime_bucket_value = str(entry.get("runtime_bucket", "unknown"))
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
        lan_badge = ""
        if lan_supported:
            player_text = f"{html.escape(max_players)} players" if max_players else "LAN"
            lan_badge = (
                '<span class="badge badge-lan">'
                f'LAN supported{f" · {player_text}" if max_players else ""}'
                '</span>'
            )
        else:
            lan_badge = '<span class="badge badge-no-lan">No LAN mode</span>'
        background_url = str((entry.get("media", {}) or {}).get("image_url", "")).strip()
        style_attr = f' style="--card-bg: url(&quot;{html.escape(background_url, quote=True)}&quot;)"' if background_url else ""
        page = render_page(
            title,
            f"""
<header>
  <p class="muted"><a href="../..">Back to index</a></p>
  <h1>{html.escape(title)}</h1>
  <p class="muted">{html.escape(description)}</p>
  <div class="badge-row">
    <span class="badge badge-category">{html.escape(category)}</span>
    {lan_badge}
  </div>
</header>
<main class="grid">
  <section class="card">
    {media_html}
    <h2>Metadata</h2>
    {metadata_html}
    <p><a href="metadata.json" download>Download machine-readable metadata.json</a></p>
    <details>
      <summary>Raw metadata</summary>
      <pre>{html.escape(json.dumps(entry, indent=2, ensure_ascii=False))}</pre>
    </details>
  </section>
  <section class="card">
    <h2>Links</h2>
    {detail_html}
    <p class="muted">Source files: <code>games/{html.escape(game_id)}</code></p>
    <p><a href="metadata.json" download>Download metadata.json</a></p>
  </section>
</main>
""",
            body_class="site-game",
        )
        (game_output / "index.html").write_text(page, encoding="utf-8")
        games_html.append(
            f"""
<article class="card game-card" data-title="{html.escape(title.lower(), quote=True)}" data-category="{html.escape(category.lower(), quote=True)}" data-genre="{html.escape(str(entry.get('genre', '')), quote=True)}" data-lan-supported="{1 if lan_supported else 0}" data-player-bucket="{html.escape(player_bucket_value)}" data-runtime-bucket="{html.escape(runtime_bucket_value)}" data-sort-title="{html.escape(title.lower(), quote=True)}" data-sort-category="{html.escape(category.lower(), quote=True)}" data-sort-genre="{html.escape(str(entry.get('genre', '')).lower(), quote=True)}" data-sort-players="{entry.get('player_count') if entry.get('player_count') is not None else -1}" data-sort-runtime="{html.escape(runtime_bucket_value.lower(), quote=True)}"{style_attr}>
  <a class="game-card-link" href="games/{html.escape(game_id)}/index.html" aria-label="{html.escape(title)}"></a>
  <div class="game-card-overlay">
    <h2>{html.escape(title)}</h2>
    <p class="muted category-line">{html.escape(category)}</p>
    <div></div>
    <p class="muted description-line">{html.escape(description)}</p>
    <div class="badge-row">
      <span class="badge {'badge-lan' if lan_supported else 'badge-no-lan'}">
        {'LAN supported' if lan_supported else 'No LAN mode'}
        {f' · {html.escape(max_players)} players' if lan_supported and max_players else ''}
      </span>
    </div>
  </div>
</article>
"""
        )
    index_page = render_page(
        "Open Source Games Index",
        f"""
<header>
  <h1>Open Source Games Index</h1>
  <p class="muted">Public metadata and navigation for open-source games.</p>
  <p class="muted">LAN-capable games: {lan_count} of {game_count}</p>
</header>
<main>
  <div class="filter-toolbar">
    <label class="filter-field">
      <span class="filter-label">Search titles</span>
      <input id="search-box" class="filter-input" type="search" placeholder="Type to filter by title">
    </label>
    <label class="filter-field">
      <span class="filter-label">Category</span>
      <select id="category-filter" class="filter-input">
        <option value="all">All categories</option>
        {''.join(f'<option value="{html.escape(category.lower(), quote=True)}">{html.escape(category)}</option>' for category in categories)}
      </select>
    </label>
    <label class="filter-field">
      <span class="filter-label">Catalog filter</span>
      <select id="lan-filter" class="filter-input">
        <option value="all">All games</option>
        <option value="lan">LAN supported</option>
        <option value="nonlan">No LAN mode</option>
      </select>
    </label>
    <label class="filter-field">
      <span class="filter-label">Player count</span>
      <select id="player-filter" class="filter-input">
        <option value="all">Any count</option>
        <option value="1-2">1-2</option>
        <option value="3-4">3-4</option>
        <option value="5-8">5-8</option>
        <option value="9+">9+</option>
        <option value="unknown">Unknown</option>
      </select>
    </label>
    <label class="filter-field">
      <span class="filter-label">Runtime support</span>
      <select id="runtime-filter" class="filter-input">
        <option value="all">Any runtime</option>
        <option value="native">Native</option>
        <option value="wine">Wine</option>
        <option value="proton">Proton</option>
        <option value="proton-ge">Proton-GE</option>
        <option value="mixed">Mixed</option>
        <option value="unknown">Unknown</option>
      </select>
    </label>
    <div class="filter-field view-toggle-field">
      <span class="filter-label">View</span>
      <div class="view-toggle" role="tablist" aria-label="View toggle">
        <button class="filter-btn" type="button" data-view="grid" aria-pressed="true">Grid</button>
        <button class="filter-btn" type="button" data-view="table" aria-pressed="false">Table</button>
      </div>
    </div>
  </div>
  <section class="grid game-grid" id="games-grid">
    {''.join(games_html)}
  </section>
  <section class="card table-panel" id="games-table-panel" hidden>
    <div class="table-wrap">
      <table class="game-table">
        <thead>
          <tr>
            <th><button type="button" class="sort-btn" data-sort-key="title" aria-sort="ascending">Title</button></th>
            <th><button type="button" class="sort-btn" data-sort-key="category">Category</button></th>
            <th><button type="button" class="sort-btn" data-sort-key="genre">Genre</button></th>
            <th><button type="button" class="sort-btn" data-sort-key="lan">LAN</button></th>
            <th><button type="button" class="sort-btn" data-sort-key="players">Players</button></th>
            <th><button type="button" class="sort-btn" data-sort-key="runtime">Runtime</button></th>
          </tr>
        </thead>
        <tbody id="games-table-body">
          {''.join(
              f'<tr class="table-row" data-title="{html.escape(str(entry.get("title", "")).lower(), quote=True)}" data-category="{html.escape(str(entry.get("category", "")).lower(), quote=True)}" data-genre="{html.escape(str(entry.get("genre", "")).lower(), quote=True)}" data-lan-supported="{1 if entry.get("lan_supported") is True else 0}" data-player-bucket="{html.escape(str(entry.get("player_bucket", "unknown")), quote=True)}" data-runtime-bucket="{html.escape(str(entry.get("runtime_bucket", "unknown")), quote=True)}" data-sort-title="{html.escape(str(entry.get("title", "")).lower(), quote=True)}" data-sort-category="{html.escape(str(entry.get("category", "")).lower(), quote=True)}" data-sort-genre="{html.escape(str(entry.get("genre", "")).lower(), quote=True)}" data-sort-lan="{1 if entry.get("lan_supported") is True else 0}" data-sort-players="{entry.get("player_count") if entry.get("player_count") is not None else -1}" data-sort-runtime="{html.escape(str(entry.get("runtime_bucket", "unknown")).lower(), quote=True)}"><td><a href="games/{html.escape(str(entry.get("game_id", "")))}/index.html">{html.escape(str(entry.get("title", "")))}</a></td><td>{html.escape(str(entry.get("category", "")))}</td><td>{html.escape(str(entry.get("genre", "")))}</td><td>{"Yes" if entry.get("lan_supported") is True else "No"}</td><td>{html.escape(str(entry.get("max_players", "")))}</td><td>{html.escape(", ".join(normalize_runtime_support(entry.get("runtime_support", entry.get("supported_runtimes")))))}</td></tr>'
              for entry in index["games"]
          )}
        </tbody>
      </table>
    </div>
  </section>
  <p class="cards-empty" id="games-empty" hidden>No games match the selected filter.</p>
  <script>
  (function () {{
    const searchBox = document.getElementById('search-box');
    const categoryFilter = document.getElementById('category-filter');
    const lanFilter = document.getElementById('lan-filter');
    const playerFilter = document.getElementById('player-filter');
    const runtimeFilter = document.getElementById('runtime-filter');
    const viewButtons = Array.from(document.querySelectorAll('[data-view]'));
    const cards = Array.from(document.querySelectorAll('#games-grid .card'));
    const tablePanel = document.getElementById('games-table-panel');
    const tableBody = document.getElementById('games-table-body');
    const tableRows = Array.from(document.querySelectorAll('#games-table-body .table-row'));
    const sortButtons = Array.from(document.querySelectorAll('.sort-btn'));
    const empty = document.getElementById('games-empty');
    const state = {{
      search: '',
      category: 'all',
      lan: 'all',
      players: 'all',
      runtime: 'all',
      view: 'grid',
      sortKey: 'title',
      sortDir: 'asc',
    }};

    function setView(view) {{
      state.view = view;
      document.body.dataset.view = view;
      const gridVisible = view === 'grid';
      document.body.classList.toggle('view-active-grid', gridVisible);
      document.body.classList.toggle('view-active-table', !gridVisible);
      document.getElementById('games-grid').hidden = !gridVisible;
      tablePanel.hidden = gridVisible;
      for (const button of viewButtons) {{
        button.setAttribute('aria-pressed', button.dataset.view === view ? 'true' : 'false');
      }}
    }}

    function matchesSearch(row, search) {{
      if (!search) return true;
      return (row.dataset.title || '').includes(search);
    }}

    function matchesCategory(row, value) {{
      return value === 'all' || (row.dataset.category || '') === value;
    }}

    function matchesPlayerFilter(card, mode) {{
      const bucket = card.dataset.playerBucket || 'unknown';
      return mode === 'all' || bucket === mode;
    }}

    function matchesLanFilter(card, mode) {{
      const lanSupported = card.dataset.lanSupported === '1';
      return mode === 'all' || (mode === 'lan' && lanSupported) || (mode === 'nonlan' && !lanSupported);
    }}

    function matchesRuntimeFilter(card, mode) {{
      const bucket = card.dataset.runtimeBucket || 'unknown';
      return mode === 'all' || bucket === mode;
    }}

    function matchesLanFilterRow(row, mode) {{
      const lanSupported = row.dataset.lanSupported === '1';
      return mode === 'all' || (mode === 'lan' && lanSupported) || (mode === 'nonlan' && !lanSupported);
    }}

    function matchesPlayerFilterRow(row, mode) {{
      const bucket = row.dataset.playerBucket || 'unknown';
      return mode === 'all' || bucket === mode;
    }}

    function matchesRuntimeFilterRow(row, mode) {{
      const bucket = row.dataset.runtimeBucket || 'unknown';
      return mode === 'all' || bucket === mode;
    }}

    function compareRows(a, b, key, dir) {{
      const left = a.dataset['sort' + key[0].toUpperCase() + key.slice(1)] || '';
      const right = b.dataset['sort' + key[0].toUpperCase() + key.slice(1)] || '';
      let result = 0;
      if (key === 'players' || key === 'lan') {{
        result = Number(left) - Number(right);
      }} else {{
        result = String(left).localeCompare(String(right));
      }}
      return dir === 'asc' ? result : -result;
    }}

    function applySort() {{
      const rows = [...tableRows].sort((a, b) => compareRows(a, b, state.sortKey, state.sortDir));
      for (const row of rows) {{
        tableBody.appendChild(row);
      }}
      for (const button of sortButtons) {{
        const active = button.dataset.sortKey === state.sortKey;
        button.setAttribute('aria-sort', active ? (state.sortDir === 'asc' ? 'ascending' : 'descending') : 'none');
      }}
    }}

    function applyFilters() {{
      let visible = 0;
      for (const card of cards) {{
        const show =
          matchesSearch(card, state.search) &&
          matchesCategory(card, state.category) &&
          matchesLanFilter(card, state.lan) &&
          matchesPlayerFilter(card, state.players) &&
          matchesRuntimeFilter(card, state.runtime);
        card.classList.toggle('is-hidden', !show);
        if (show) {{
          visible += 1;
        }}
      }}
      for (const row of tableRows) {{
        const show =
          matchesSearch(row, state.search) &&
          matchesCategory(row, state.category) &&
          matchesLanFilterRow(row, state.lan) &&
          matchesPlayerFilterRow(row, state.players) &&
          matchesRuntimeFilterRow(row, state.runtime);
        row.classList.toggle('is-hidden', !show);
        if (show) {{
          visible += 1;
        }}
      }}
      if (empty) {{
        empty.hidden = visible !== 0;
      }}
    }}

    searchBox.addEventListener('input', () => {{
      state.search = searchBox.value.trim().toLowerCase();
      applyFilters();
    }});
    categoryFilter.addEventListener('change', () => {{
      state.category = categoryFilter.value;
      applyFilters();
    }});
    lanFilter.addEventListener('change', () => {{
      state.lan = lanFilter.value;
      applyFilters();
    }});
    playerFilter.addEventListener('change', () => {{
      state.players = playerFilter.value;
      applyFilters();
    }});
    runtimeFilter.addEventListener('change', () => {{
      state.runtime = runtimeFilter.value;
      applyFilters();
    }});
    for (const button of viewButtons) {{
      button.addEventListener('click', () => setView(button.dataset.view || 'grid'));
    }}
    for (const button of sortButtons) {{
      button.addEventListener('click', () => {{
        const key = button.dataset.sortKey || 'title';
        if (state.sortKey === key) {{
          state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
        }} else {{
          state.sortKey = key;
          state.sortDir = 'asc';
        }}
        applySort();
        applyFilters();
      }});
    }}
    setView('grid');
    applySort();
    applyFilters();
  }})();
  </script>
</main>
""",
        body_class="site-index",
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
